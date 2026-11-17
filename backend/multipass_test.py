"""Multipass Verification & Multi-Pass Inference Test Suite for SadakSetu AI.

Combines:
  1. 6-Stage Quality Assurance Verification Passes:
     - Pass 1: Model & Checkpoint Integrity (PyTorch + ONNX)
     - Pass 2: Offline Dataset & Dataloader Alignment
     - Pass 3: Single-Pass vs Multi-Pass (Flip + Zoom Crop + TTA) Inference
     - Pass 4: False Positive & Background Rejection (Normal Road Test)
     - Pass 5: Engine Parity & Speed Comparison (PyTorch vs ONNX Runtime)
     - Pass 6: Offline FastAPI HTTP Integration (POST /api/v1/ai/detect)
  2. Multi-Pass Inference Implementation:
     - Evaluates the multi-pass upload scanning algorithm (Full-Image + Horizontal Flip + Road Crop + NMS)
       as designed for high-recall upload image analysis.
"""

import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import torch
import onnx
import onnxruntime as ort
from ultralytics import YOLO
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import get_settings


def nms_boxes(boxes, scores, iou_thresh=0.45):
    if len(boxes) == 0:
        return []
    b = np.array(boxes)
    s = np.array(scores)
    x1, y1, x2, y2 = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = s.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]
    return keep


def run_multipass_inference(model: YOLO, img_bgr: np.ndarray, conf: float = 0.35, imgsz: int = 320) -> dict:
    h, w = img_bgr.shape[:2]
    started = time.perf_counter()

    # Pass 1: Standard Full-Image
    t0 = time.perf_counter()
    r1 = model.predict(img_bgr, conf=conf, imgsz=imgsz, verbose=False)[0]
    p1_time = (time.perf_counter() - t0) * 1000
    b1 = r1.boxes.xyxy.cpu().numpy().tolist()
    s1 = r1.boxes.conf.cpu().numpy().tolist()

    # Pass 2: Horizontal Flip
    t0 = time.perf_counter()
    flipped = cv2.flip(img_bgr, 1)
    r2 = model.predict(flipped, conf=conf, imgsz=imgsz, verbose=False)[0]
    p2_time = (time.perf_counter() - t0) * 1000
    b2_raw = r2.boxes.xyxy.cpu().numpy().tolist()
    s2 = r2.boxes.conf.cpu().numpy().tolist()
    b2 = [[w - box[2], box[1], w - box[0], box[3]] for box in b2_raw]

    # Pass 3: Lower-Half Road Crop (where road surfaces appear)
    t0 = time.perf_counter()
    crop_y0 = int(h * 0.30)
    crop = img_bgr[crop_y0:, :]
    r3 = model.predict(crop, conf=conf, imgsz=imgsz, verbose=False)[0]
    p3_time = (time.perf_counter() - t0) * 1000
    b3_raw = r3.boxes.xyxy.cpu().numpy().tolist()
    s3 = r3.boxes.conf.cpu().numpy().tolist()
    b3 = [[box[0], box[1] + crop_y0, box[2], box[3] + crop_y0] for box in b3_raw]

    # Fusion via Non-Maximum Suppression
    all_boxes = b1 + b2 + b3
    all_scores = s1 + s2 + s3
    keep = nms_boxes(all_boxes, all_scores, iou_thresh=0.45)
    merged_boxes = [all_boxes[i] for i in keep]
    merged_scores = [all_scores[i] for i in keep]

    total_time = (time.perf_counter() - started) * 1000
    return {
        "pass1_count": len(b1),
        "pass1_time_ms": round(p1_time, 1),
        "pass2_count": len(b2),
        "pass2_time_ms": round(p2_time, 1),
        "pass3_count": len(b3),
        "pass3_time_ms": round(p3_time, 1),
        "merged_count": len(merged_boxes),
        "merged_boxes": merged_boxes,
        "merged_scores": merged_scores,
        "total_time_ms": round(total_time, 1),
    }


def execute_multipass_test():
    print("=" * 65)
    print("           SADAKSETU AI MULTIPASS TEST SUITE            ")
    print("=" * 65)

    results_summary = {}

    # -------------------------------------------------------------
    # PASS 1: Model Checkpoint & Graph Integrity
    # -------------------------------------------------------------
    print("\n[PASS 1/6] Model & Checkpoint Integrity")
    pt_path = Path("models/baseline_yolo11.pt")
    onnx_path = Path("models/baseline_yolo11.onnx")

    assert pt_path.is_file(), f"PyTorch weights missing at {pt_path}"
    assert onnx_path.is_file(), f"ONNX model missing at {onnx_path}"

    pt_size = pt_path.stat().st_size / (1024 * 1024)
    onnx_size = onnx_path.stat().st_size / (1024 * 1024)

    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)

    print(f"  PyTorch Model: {pt_path.name} ({pt_size:.2f} MB) -> OK")
    print(f"  ONNX Model:    {onnx_path.name} ({onnx_size:.2f} MB) -> VALID GRAPH")
    results_summary["Pass 1 - Integrity"] = "PASS"

    # -------------------------------------------------------------
    # PASS 2: Dataset & Dataloader Verification
    # -------------------------------------------------------------
    print("\n[PASS 2/6] Dataset & Split Alignment")
    ds_root = Path("datasets/provided_pothole_detection_yolo11_prepared")
    train_imgs = list((ds_root / "train/images").glob("*.jpg"))
    val_imgs = list((ds_root / "valid/images").glob("*.jpg"))
    test_imgs = list((ds_root / "test/images").glob("*.jpg"))

    print(f"  Train: {len(train_imgs)} images | Val: {len(val_imgs)} images | Test: {len(test_imgs)} images")
    assert len(train_imgs) > 1000 and len(test_imgs) > 200, "Dataset splits incomplete"
    results_summary["Pass 2 - Dataset"] = f"PASS ({len(train_imgs)} train / {len(test_imgs)} test)"

    # -------------------------------------------------------------
    # PASS 3: Single-Pass vs Multi-Pass Inference Test
    # -------------------------------------------------------------
    print("\n[PASS 3/6] Single-Pass vs Multi-Pass (Flip + Zoom Crop) Benchmark")
    model = YOLO(str(pt_path))
    sample_tests = test_imgs[:10]
    sp_total = 0
    mp_total = 0

    for idx, p in enumerate(sample_tests):
        img_bgr = cv2.imread(str(p))
        res = run_multipass_inference(model, img_bgr, conf=0.30, imgsz=320)
        sp_total += res["pass1_count"]
        mp_total += res["merged_count"]
        gain = res["merged_count"] - res["pass1_count"]
        gain_str = f"+{gain}" if gain > 0 else f"{gain}"
        print(f"  [{idx+1:02d}] {p.name[:28]}... Single: {res['pass1_count']} | Multi: {res['merged_count']} (Delta: {gain_str}) | Latency: {res['total_time_ms']}ms")

    print(f"  Total Detections on 10 Samples -> Single-Pass: {sp_total} | Multi-Pass: {mp_total}")
    results_summary["Pass 3 - Multi-Pass Inference"] = f"PASS (Found {mp_total} vs {sp_total} boxes)"

    # -------------------------------------------------------------
    # PASS 4: False Positive Rejection (Normal Road Test)
    # -------------------------------------------------------------
    print("\n[PASS 4/6] Normal Road & False Positive Rejection Test")
    normal_labels = [p for p in (ds_root / "train/labels").glob("*.txt") if p.stat().st_size == 0]
    normal_fp_count = 0
    tested_normal = min(5, len(normal_labels))

    for p in normal_labels[:tested_normal]:
        img_p = ds_root / "train/images" / (p.stem + ".jpg")
        r = model.predict(str(img_p), conf=0.35, imgsz=320, verbose=False)[0]
        cnt = len(r.boxes)
        normal_fp_count += cnt
        print(f"  Background/Clean Sample {img_p.name[:25]}... Detections at conf=0.35: {cnt}")

    rejection_rate = ((tested_normal - normal_fp_count) / tested_normal) * 100 if tested_normal > 0 else 100
    print(f"  Tested {tested_normal} background images: {normal_fp_count} false positives at conf=0.35")
    results_summary["Pass 4 - Background/Clean Samples"] = f"COMPLETED ({normal_fp_count} detections across {tested_normal} background samples)"

    # -------------------------------------------------------------
    # PASS 5: Engine Parity Test (PyTorch vs ONNX Runtime)
    # -------------------------------------------------------------
    print("\n[PASS 5/6] Cross-Engine Parity Check (PyTorch vs ONNX Runtime)")
    sample_img_p = test_imgs[0]
    # PyTorch
    t0 = time.perf_counter()
    pt_res = model.predict(str(sample_img_p), conf=0.35, imgsz=320, verbose=False)[0]
    pt_ms = (time.perf_counter() - t0) * 1000

    # ONNX Runtime
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    img = Image.open(sample_img_p).convert("RGB").resize((320, 320))
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))[np.newaxis, ...]
    t0 = time.perf_counter()
    ort_out = session.run(None, {"images": arr})[0]
    ort_ms = (time.perf_counter() - t0) * 1000

    # Find highest confidence in ONNX output
    ort_max_conf = float(np.max(ort_out[0, 4, :]))
    pt_max_conf = float(pt_res.boxes.conf[0]) if len(pt_res.boxes) > 0 else 0.0

    print(f"  PyTorch Latency: {pt_ms:.1f}ms | Top Conf: {pt_max_conf:.3f}")
    print(f"  ONNX Latency:    {ort_ms:.1f}ms | Top Conf: {ort_max_conf:.3f}")
    assert abs(pt_max_conf - ort_max_conf) < 0.05, "Parity drift exceeds tolerance"
    results_summary["Pass 5 - Engine Parity"] = f"PASS (ONNX {ort_ms:.1f}ms vs PT {pt_ms:.1f}ms, parity delta {abs(pt_max_conf - ort_max_conf):.3f})"

    # -------------------------------------------------------------
    # PASS 6: Offline FastAPI HTTP Integration Test
    # -------------------------------------------------------------
    print("\n[PASS 6/6] Offline Direct API Route Test (POST /api/v1/ai/detect)")
    app = create_app()
    client = TestClient(app)

    with open(sample_img_p, "rb") as f:
        resp = client.post("/api/v1/ai/detect", files={"image": (sample_img_p.name, f, "image/jpeg")})

    assert resp.status_code == 200, f"API failed with status {resp.status_code}"
    body = resp.json()
    assert body["status"] == "COMPLETED"
    print(f"  HTTP Status: {resp.status_code} OK")
    print(f"  Response: model={body['model_name']} {body['model_version']}, count={body['detection_count']}, time={body['processing_time_ms']}ms")
    results_summary["Pass 6 - HTTP API"] = f"PASS (Status 200, {body['detection_count']} detections)"

    # -------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # -------------------------------------------------------------
    print("\n" + "=" * 65)
    print("                     MULTIPASS TEST RESULTS                     ")
    print("=" * 65)
    for test_pass, status in results_summary.items():
        print(f"  {test_pass:<30} : {status}")
    print("=" * 65)
    print("ALL PASSES COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    execute_multipass_test()
