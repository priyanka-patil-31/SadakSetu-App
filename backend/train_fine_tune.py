"""YOLO11 Pothole Detection Fine-Tuning & Evaluation Pipeline.

Automates dataset validation, starting checkpoint fine-tuning with GPU/CPU support,
evaluation against baseline, confusion matrix generation, and safe checkpoint promotion.
"""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO


def check_dataset(data_yaml_path: Path) -> dict:
    if not data_yaml_path.is_file():
        raise FileNotFoundError(f"Dataset YAML not found at: {data_yaml_path}")

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data_cfg = yaml.safe_load(f)

    root = Path(data_cfg.get("path", data_yaml_path.parent))
    train_dir = root / data_cfg.get("train", "train/images")
    val_dir = root / data_cfg.get("val", "valid/images")

    if not train_dir.exists():
        raise FileNotFoundError(f"Training images directory not found: {train_dir}")
    if not val_dir.exists():
        raise FileNotFoundError(f"Validation images directory not found: {val_dir}")

    train_count = len(list(train_dir.glob("*.jpg")) + list(train_dir.glob("*.png")))
    val_count = len(list(val_dir.glob("*.jpg")) + list(val_dir.glob("*.png")))
    names = data_cfg.get("names", [])

    return {
        "root": str(root),
        "train_count": train_count,
        "val_count": val_count,
        "classes": names,
        "nc": data_cfg.get("nc", len(names)),
    }


def evaluate_checkpoint(model_path: Path, data_yaml: Path, conf: float = 0.35, imgsz: int = 320, device: str = "cpu") -> dict:
    model = YOLO(str(model_path))
    metrics = model.val(
        data=str(data_yaml),
        split="test",
        conf=conf,
        iou=0.5,
        imgsz=imgsz,
        device=device,
        verbose=False,
    )
    p = float(metrics.results_dict.get("metrics/precision(B)", 0.0))
    r = float(metrics.results_dict.get("metrics/recall(B)", 0.0))
    map50 = float(metrics.results_dict.get("metrics/mAP50(B)", 0.0))
    map5095 = float(metrics.results_dict.get("metrics/mAP50-95(B)", 0.0))
    f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
    return {
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1": round(f1, 4),
        "map50": round(map50, 4),
        "map50_95": round(map5095, 4),
    }


def run_pipeline():
    parser = argparse.ArgumentParser(description="Fine-tune YOLO11 on Pothole Dataset")
    parser.add_argument("--epochs", type=int, default=5, help="Number of fine-tuning epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=320, help="Image size")
    parser.add_argument("--freeze", type=int, default=10, help="Backbone layers to freeze for fast CPU transfer learning")
    parser.add_argument("--fraction", type=float, default=1.0, help="Fraction of dataset to train on")
    parser.add_argument("--baseline", type=str, default="models/baseline_yolo11.pt", help="Baseline model path")
    parser.add_argument("--data", type=str, default="datasets/provided_pothole_detection_yolo11_prepared/data.yaml", help="Path to data.yaml")
    parser.add_argument("--conf", type=float, default=0.35, help="Evaluation confidence threshold")
    args = parser.parse_args()

    data_yaml = Path(args.data).resolve()
    baseline_path = Path(args.baseline).resolve()

    print("==================================================")
    print("      YOLO11 POTHOLE DETECTION FINE-TUNING       ")
    print("==================================================")

    # 1. Dataset verification
    print("\n[1/5] Verifying Dataset...")
    ds_info = check_dataset(data_yaml)
    print(f"  Dataset Root: {ds_info['root']}")
    print(f"  Train Images: {ds_info['train_count']}")
    print(f"  Val Images:   {ds_info['val_count']}")
    print(f"  Classes:      {ds_info['classes']} (nc={ds_info['nc']})")

    # 2. Hardware check
    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"\n[2/5] Hardware Check: Using device '{device}' (CUDA available: {torch.cuda.is_available()})")
    if device == "cpu":
        torch.set_num_threads(min(4, os.cpu_count() or 4))
        print(f"  Configured PyTorch CPU threads: {torch.get_num_threads()}")

    # 3. Baseline evaluation
    print(f"\n[3/5] Evaluating Baseline Checkpoint ({baseline_path.name})...")
    baseline_metrics = evaluate_checkpoint(baseline_path, data_yaml, conf=args.conf, imgsz=args.imgsz, device=device)
    print("  Baseline Metrics on Test Set:")
    for k, v in baseline_metrics.items():
        print(f"    {k}: {v}")

    # 4. Training
    output_dir = Path("runs/fine_tune")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[4/5] Starting Fine-Tuning for {args.epochs} epochs (imgsz={args.imgsz}, batch={args.batch}, freeze={args.freeze})...")

    model = YOLO(str(baseline_path))
    t0 = time.time()
    train_results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        freeze=args.freeze,
        fraction=args.fraction,
        device=device,
        workers=0,
        project=str(output_dir),
        name="yolo11n_pothole_finetuned",
        exist_ok=True,
        verbose=True,
    )
    training_time = time.time() - t0
    print(f"\n  Training completed in {training_time / 60:.2f} minutes.")

    # Locate saved weights
    save_dir = Path(train_results.save_dir) if hasattr(train_results, "save_dir") else output_dir / "yolo11n_pothole_finetuned"
    best_ckpt = save_dir / "weights" / "best.pt"
    last_ckpt = save_dir / "weights" / "last.pt"

    dest_models_dir = Path("models/fine_tuned")
    dest_models_dir.mkdir(parents=True, exist_ok=True)
    if best_ckpt.exists():
        shutil.copy2(best_ckpt, dest_models_dir / "best.pt")
    if last_ckpt.exists():
        shutil.copy2(last_ckpt, dest_models_dir / "last.pt")

    target_eval_ckpt = best_ckpt if best_ckpt.exists() else last_ckpt

    # 5. Fine-tuned evaluation and comparison
    print(f"\n[5/5] Evaluating Fine-Tuned Checkpoint ({target_eval_ckpt.name})...")
    ft_metrics = evaluate_checkpoint(target_eval_ckpt, data_yaml, conf=args.conf, imgsz=args.imgsz, device=device)

    print("\n==================================================")
    print("               FINAL COMPARISON REPORT            ")
    print("==================================================")
    print(f"{'Metric':<15} | {'Baseline':<12} | {'Fine-Tuned':<12} | {'Delta':<10}")
    print("-" * 55)
    for k in ["precision", "recall", "f1", "map50", "map50_95"]:
        b_val = baseline_metrics[k]
        f_val = ft_metrics[k]
        delta = f_val - b_val
        sign = "+" if delta >= 0 else ""
        print(f"{k:<15} | {b_val:<12} | {f_val:<12} | {sign}{delta:.4f}")

    # Check promotion condition
    promoted = False
    if ft_metrics["map50"] >= baseline_metrics["map50"]:
        print("\n[PROMOTION] Fine-tuned model achieved equal or higher mAP@50.")
        promoted_path = Path("models/best_fine_tuned.pt")
        shutil.copy2(target_eval_ckpt, promoted_path)
        print(f"  Saved promoted model to: {promoted_path}")
        promoted = True
    else:
        print("\n[INFO] Baseline model retains higher mAP@50. Preserving baseline as default.")
        print(f"  Fine-tuned weights preserved in: {dest_models_dir / 'best.pt'}")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": {"device": device, "cuda": torch.cuda.is_available()},
        "training": {
            "epochs": args.epochs,
            "batch": args.batch,
            "imgsz": args.imgsz,
            "freeze": args.freeze,
            "training_time_seconds": round(training_time, 2),
        },
        "baseline_metrics": baseline_metrics,
        "finetuned_metrics": ft_metrics,
        "promoted": promoted,
    }

    report_path = Path("models/fine_tuning_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report written to: {report_path}")


if __name__ == "__main__":
    run_pipeline()
