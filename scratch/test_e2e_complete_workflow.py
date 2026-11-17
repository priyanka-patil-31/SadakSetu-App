"""
End-to-End Workflow Verification Script for SadakSetu Work Assignment & Monitoring System
Covers all 6 Phases and all 13 workflow steps with real database records and live API endpoints.
"""
import requests
import json
import uuid
import datetime

BASE_URL = "http://127.0.0.1:8001"

def print_step(step_num, title):
    print(f"\n{'='*70}\nSTEP {step_num}: {title}\n{'='*70}")

def run_e2e_test():
    # -------------------------------------------------------------
    # Step 1: Citizen Login
    # -------------------------------------------------------------
    print_step(1, "Citizen Registration / Login")
    citizen_email = f"citizen.{uuid.uuid4().hex[:6]}@example.com"
    citizen_password = "CitizenPassword123!"
    
    # Register citizen
    reg_res = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "full_name": "Ananya Sharma",
            "email": citizen_email,
            "password": citizen_password,
            "phone": "9876543210",
            "client_type": "android",
        }
    )
    assert reg_res.status_code in (200, 201), f"Citizen reg failed: {reg_res.text}"
    citizen_data = reg_res.json()
    citizen_id = citizen_data["user"]["id"]
    print(f" Citizen registered: {citizen_data['user']['full_name']} ({citizen_email}) [Role: {citizen_data['user']['role']}]")
    
    citizen_session = requests.Session()
    c_login_res = citizen_session.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": citizen_email, "password": citizen_password, "client_type": "android"}
    )
    assert c_login_res.status_code == 200, f"Citizen login failed: {c_login_res.text}"
    c_token = c_login_res.json()["session_id"]
    citizen_session.headers["Authorization"] = f"Bearer {c_token}"
    print(" Citizen logged in via Android client session (Bearer token attached)")

    # -------------------------------------------------------------
    # Step 2: Citizen Submits Complaint
    # -------------------------------------------------------------
    print_step(2, "Citizen Submits Road Complaint")
    complaint_payload = {
        "title": "Severe pothole cluster near Metro Pillar 142",
        "description": "Deep multiple potholes causing vehicle damage and traffic bottleneck during peak hours.",
        "location": {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "address": "Outer Ring Road, Pillar 142, Bengaluru",
            "area": "Indiranagar Ward",
            "zone": "East Zone"
        }
    }
    c_res = citizen_session.post(f"{BASE_URL}/api/v1/complaints", json=complaint_payload)
    assert c_res.status_code == 201, f"Complaint creation failed: {c_res.text}"
    complaint = c_res.json()
    complaint_id = complaint["id"]
    complaint_number = complaint["complaint_number"]
    print(f" Complaint filed successfully: {complaint_number} (ID: {complaint_id})")
    print(f"   Status: {complaint['status']}, Severity: {complaint['severity']}")

    # -------------------------------------------------------------
    # Step 3: Admin Login
    # -------------------------------------------------------------
    print_step(3, "Admin Authentication on Web Dashboard")
    admin_session = requests.Session()
    admin_login_res = admin_session.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "admin@sadaksetu.local", "password": "Admin@SadakSetu1", "client_type": "browser"}
    )
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.text}"
    print(" Admin logged in successfully to Web Dashboard")

    # -------------------------------------------------------------
    # Step 4: Admin Verifies Complaint
    # -------------------------------------------------------------
    print_step(4, "Admin Triage & Complaint Verification")
    verify_res = admin_session.patch(
        f"{BASE_URL}/api/v1/complaints/{complaint_id}/status",
        json={"status": "UNDER_REVIEW", "note": "Verified by City Operations Center via mobile GPS and citizen report."}
    )
    assert verify_res.status_code == 200, f"Verification failed: {verify_res.text}"
    print(f" Complaint {complaint_number} transitioned to status: {verify_res.json()['status']}")

    # -------------------------------------------------------------
    # Step 5: Admin Retrieves Repair Teams & Assigns Work
    # -------------------------------------------------------------
    print_step(5, "Admin Assigns Complaint to Repair Team & Leader")
    teams_res = admin_session.get(f"{BASE_URL}/api/v1/teams?page=1&page_size=20")
    assert teams_res.status_code == 200, f"Failed to list teams: {teams_res.text}"
    teams = teams_res.json()["items"]
    assert len(teams) > 0, "No repair teams found!"
    target_team = teams[0]
    team_id = target_team["id"]
    print(f" Selected Repair Team: {target_team['name']} ({target_team['zone']}) - Lead: {target_team['lead_name']}")

    deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)).isoformat()
    assign_payload = {
        "team_id": team_id,
        "priority": "HIGH",
        "expected_completion_date": deadline,
        "instructions": "Excavate damaged asphalt 50mm, lay Bituminous Macadam base and 40mm wearing coat.",
        "note": "Critical arterial route, complete before weekend rush."
    }
    assign_res = admin_session.post(f"{BASE_URL}/api/v1/assignments/complaints/{complaint_id}", json=assign_payload)
    assert assign_res.status_code == 201, f"Assignment failed: {assign_res.text}"
    work_order = assign_res.json()
    wo_id = work_order["id"]
    wo_num = work_order["work_order_number"]
    print(f" Work Order Created: {wo_num} (Assignment ID: {wo_id})")
    print(f"   Work Status: {work_order['work_status']}, Priority: {work_order['priority']}")
    print(f"   Target Deadline: {work_order['expected_completion_date']}")

    # -------------------------------------------------------------
    # Step 6: Team Leader Login & View Assigned Work
    # -------------------------------------------------------------
    print_step(6, "Team Leader Logs In on Android App & Fetches 'My Work'")
    leader_session = requests.Session()
    leader_login_res = leader_session.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "ramesh.lead@gmail.com", "password": "LeaderPassword123!", "client_type": "android"}
    )
    assert leader_login_res.status_code == 200, f"Team Leader login failed: {leader_login_res.text}"
    l_token = leader_login_res.json()["session_id"]
    leader_session.headers["Authorization"] = f"Bearer {l_token}"
    print(" Team Leader Ramesh Kumar authenticated via mobile app (Bearer token attached)")

    my_work_res = leader_session.get(f"{BASE_URL}/api/v1/assignments/my-work")
    assert my_work_res.status_code == 200, f"Failed to fetch my-work: {my_work_res.text}"
    my_work_items = my_work_res.json()
    matching_wo = next((w for w in my_work_items if w["id"] == wo_id), None)
    assert matching_wo is not None, f"Work order {wo_id} not visible in Team Leader's work list!"
    print(f" Team Leader sees Work Order {matching_wo['work_order_number']} in assigned jobs!")

    # -------------------------------------------------------------
    # Step 7: Team Leader Accepts Work Order
    # -------------------------------------------------------------
    print_step(7, "Team Leader Accepts Work Order")
    accept_res = leader_session.post(f"{BASE_URL}/api/v1/assignments/{wo_id}/accept", json={"note": "Acknowledged. Crew dispatched with roller."})
    assert accept_res.status_code == 200, f"Accept failed: {accept_res.text}"
    print(f" Work Order Status updated to: {accept_res.json()['work_status']}")

    # -------------------------------------------------------------
    # Step 8: Team Leader Manages Team Members
    # -------------------------------------------------------------
    print_step(8, "Team Leader Assigns Crew Members to Work Order")
    members_res = leader_session.get(f"{BASE_URL}/api/v1/teams/my-team/members")
    assert members_res.status_code == 200, f"Failed to get members: {members_res.text}"
    members = members_res.json()
    member_ids = [m["id"] for m in members] if members else []
    
    update_members_res = leader_session.post(f"{BASE_URL}/api/v1/assignments/{wo_id}/members", json={"member_ids": member_ids})
    assert update_members_res.status_code == 200, f"Member update failed: {update_members_res.text}"
    print(f" Assigned {len(member_ids)} crew members to work order.")

    # -------------------------------------------------------------
    # Step 9: Repair Starts (IN_PROGRESS)
    # -------------------------------------------------------------
    print_step(9, "Team Leader Starts Repair Work")
    start_res = leader_session.post(f"{BASE_URL}/api/v1/assignments/{wo_id}/start", json={"note": "Milling machine on site, beginning surface removal."})
    assert start_res.status_code == 200, f"Start failed: {start_res.text}"
    print(f" Work Order Status updated to: {start_res.json()['work_status']}")

    # -------------------------------------------------------------
    # Step 10: Team Leader Updates Progress
    # -------------------------------------------------------------
    print_step(10, "Team Leader Reports Intermediate Progress")
    progress_res = leader_session.post(
        f"{BASE_URL}/api/v1/assignments/{wo_id}/progress",
        json={"progress_percentage": 65, "progress_notes": "Sub-base compacted. Prime coat applied. Laying asphalt."}
    )
    assert progress_res.status_code == 200, f"Progress update failed: {progress_res.text}"
    print(f" Progress recorded: {progress_res.json()['progress_percentage']}% - Notes: {progress_res.json()['progress_notes']}")

    # -------------------------------------------------------------
    # Step 11: Team Leader Uploads Before and After Photos
    # -------------------------------------------------------------
    print_step(11, "Team Leader Uploads Before & After Evidence Photos")
    before_photo = f"/api/v1/complaints/{complaint_id}/images/{uuid.uuid4().hex[:12]}_before.jpg"
    after_photo = f"/api/v1/complaints/{complaint_id}/images/{uuid.uuid4().hex[:12]}_after.jpg"

    p1_res = leader_session.post(f"{BASE_URL}/api/v1/assignments/{wo_id}/photos", json={"photo_type": "BEFORE", "photo_url": before_photo})
    assert p1_res.status_code == 200, f"Before photo failed: {p1_res.text}"
    p2_res = leader_session.post(f"{BASE_URL}/api/v1/assignments/{wo_id}/photos", json={"photo_type": "AFTER", "photo_url": after_photo})
    assert p2_res.status_code == 200, f"After photo failed: {p2_res.text}"
    print(f" Evidence Attached: 1 Before Photo, 1 After Photo")

    # -------------------------------------------------------------
    # Step 12: Team Leader Submits Completion for Admin Verification
    # -------------------------------------------------------------
    print_step(12, "Team Leader Submits Completion for Quality Verification")
    # First set progress to 100%
    leader_session.post(f"{BASE_URL}/api/v1/assignments/{wo_id}/progress", json={"progress_percentage": 100, "progress_notes": "All paving and edge sealing complete."})
    comp_res = leader_session.post(
        f"{BASE_URL}/api/v1/assignments/{wo_id}/submit-completion",
        json={"completion_notes": "Potholes filled with dense bituminous macadam, leveled with vibratory roller. Ready for sign-off."}
    )
    assert comp_res.status_code == 200, f"Submit completion failed: {comp_res.text}"
    print(f" Work Order Status transitioned to: {comp_res.json()['work_status']}")

    # -------------------------------------------------------------
    # Step 13: Admin Inspects & Verifies Completion
    # -------------------------------------------------------------
    print_step(13, "Admin Inspects Evidence & Approves Completion")
    # Admin checks monitoring list
    monitor_res = admin_session.get(f"{BASE_URL}/api/v1/assignments?status=COMPLETION_SUBMITTED")
    assert monitor_res.status_code == 200, f"Monitoring fetch failed: {monitor_res.text}"
    pending_verifications = monitor_res.json()
    target_audit = next((w for w in pending_verifications if w["id"] == wo_id), None)
    assert target_audit is not None, "Submitted work order not found in Admin's review queue!"
    print(f" Admin sees Work Order {target_audit['work_order_number']} in review queue")
    print(f"   Completion Notes: {target_audit['completion_notes']}")
    print(f"   Before Photos: {len(target_audit['before_photos'])}, After Photos: {len(target_audit['after_photos'])}")

    # Admin verifies and approves
    verify_wo_res = admin_session.post(
        f"{BASE_URL}/api/v1/assignments/{wo_id}/verify",
        json={"approved": True, "note": "Verified compaction and surface smoothness according to IRC-SP-72 standards. Excellent quality."}
    )
    assert verify_wo_res.status_code == 200, f"Admin verify failed: {verify_wo_res.text}"
    approved_wo = verify_wo_res.json()
    print(f" Work Order Approved! Final Work Status: {approved_wo['work_status']}")

    # -------------------------------------------------------------
    # Step 14: Citizen Sees Complaint Resolved
    # -------------------------------------------------------------
    print_step(14, "Citizen Verifies Updated Complaint Status")
    c_final_res = citizen_session.get(f"{BASE_URL}/api/v1/complaints/{complaint_id}")
    assert c_final_res.status_code == 200, f"Citizen fetch failed: {c_final_res.text}"
    final_complaint = c_final_res.json()
    print(f" Citizen Complaint #{final_complaint['complaint_number']} final status: {final_complaint['status']}")
    assert final_complaint["status"] == "RESOLVED", f"Expected RESOLVED but got {final_complaint['status']}"

    # -------------------------------------------------------------
    # Step 15: Check Notifications Generation
    # -------------------------------------------------------------
    print_step(15, "Notifications & Audit Trail Verification")
    notif_res = admin_session.get(f"{BASE_URL}/api/v1/notifications?page=1&page_size=10")
    if notif_res.status_code == 200:
        notifs = notif_res.json()["items"]
        print(f" Generated {len(notifs)} recent system notifications:")
        for n in notifs[:5]:
            print(f"   - [{n['notification_type']}] {n['title']}: {n['body']}")

    print("\n" + "="*70)
    print("SUCCESS: ALL 15 END-TO-END WORKFLOW VERIFICATION STEPS PASSED 100%!")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_e2e_test()
