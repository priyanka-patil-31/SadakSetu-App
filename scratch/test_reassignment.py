import requests
import datetime
import uuid

BASE = "http://127.0.0.1:8001"

def test_reassignment():
    # Citizen files complaint
    c_session = requests.Session()
    c_email = f"reassign.{uuid.uuid4().hex[:6]}@example.com"
    c_reg = c_session.post(f"{BASE}/api/v1/auth/register", json={
        "full_name": "Test Citizen Reassign",
        "email": c_email,
        "password": "Password123!",
        "phone": "9123456780",
        "client_type": "android"
    })
    assert c_reg.status_code in (200, 201)
    c_log = c_session.post(f"{BASE}/api/v1/auth/login", json={
        "email": c_email,
        "password": "Password123!",
        "client_type": "android"
    })
    c_token = c_log.json()["session_id"]
    c_session.headers["Authorization"] = f"Bearer {c_token}"

    comp = c_session.post(f"{BASE}/api/v1/complaints", json={
        "title": "Major road crack on East highway",
        "description": "Longitudinal crack extending 15 meters along the inner lane.",
        "location": {"latitude": 12.98, "longitude": 77.60, "address": "East Highway", "area": "Indiranagar", "zone": "East Zone"}
    }).json()
    complaint_id = comp["id"]
    print("Created complaint:", comp["complaint_number"])

    # Admin login
    admin_session = requests.Session()
    admin_session.post(f"{BASE}/api/v1/auth/login", json={"email":"admin@sadaksetu.local","password":"Admin@SadakSetu1","client_type":"browser"})

    # Admin gets teams
    teams = admin_session.get(f"{BASE}/api/v1/teams").json()["items"]
    t1 = next(t for t in teams if "Phase 1" in t["name"])
    t2 = next(t for t in teams if "Rapid Response Unit 2" in t["name"])

    # Assign to Team 1
    deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).isoformat()
    wo1_res = admin_session.post(f"{BASE}/api/v1/assignments/complaints/{complaint_id}", json={
        "team_id": t1["id"],
        "priority": "HIGH",
        "expected_completion_date": deadline,
        "instructions": "Initial inspection and seal."
    })
    assert wo1_res.status_code == 201, f"Initial assign failed: {wo1_res.text}"
    wo1 = wo1_res.json()
    print(f"Assigned to Team 1 ({t1['name']}) -> WO: {wo1['work_order_number']}, Status: {wo1['work_status']}")

    # Reassign to Team 2
    reassign_res = admin_session.post(f"{BASE}/api/v1/assignments/complaints/{complaint_id}/reassign", json={
        "team_id": t2["id"],
        "reason": "Team 1 diverted to priority highway flood emergency; reallocating to Unit 2.",
        "priority": "CRITICAL",
        "instructions": "Urgent: deploy sealing crew immediately."
    })
    assert reassign_res.status_code in (200, 201), f"Reassign failed: {reassign_res.text}"
    wo2 = reassign_res.json()
    print(f"Reassigned to Team 2 ({t2['name']}) -> WO: {wo2['work_order_number']}, Status: {wo2['work_status']}, Priority: {wo2['priority']}")

    # Check Team 2 Leader (Suresh Patel) sees it
    suresh_session = requests.Session()
    suresh_log = suresh_session.post(f"{BASE}/api/v1/auth/login", json={
        "email": "suresh.lead@example.com",
        "password": "LeaderPassword123!",
        "client_type": "android"
    })
    assert suresh_log.status_code == 200, f"Suresh login failed: {suresh_log.text}"
    s_token = suresh_log.json()["session_id"]
    suresh_session.headers["Authorization"] = f"Bearer {s_token}"

    suresh_work = suresh_session.get(f"{BASE}/api/v1/assignments/my-work").json()
    suresh_found = any(w["id"] == wo2["id"] for w in suresh_work)
    print(f"Team Leader Suresh sees reassigned work order in mobile app: {suresh_found}")
    assert suresh_found, "Suresh did not see reassigned work order!"
    print("\nSUCCESS: REASSIGNMENT VERIFICATION PASSED 100%!")

if __name__ == "__main__":
    test_reassignment()
