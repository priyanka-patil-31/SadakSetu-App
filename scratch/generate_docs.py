import os
import sys
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = r"c:\Users\HP\Downloads\SadakSetu project"
PDF_PATH = os.path.join(BASE_DIR, "SADAKSETU_WORKFLOW_DOCUMENTATION.pdf")
HTML_PATH = os.path.join(BASE_DIR, "SADAKSETU_WORKFLOW_DOCUMENTATION.html")
MD_PATH = os.path.join(BASE_DIR, "SADAKSETU_WORKFLOW_DOCUMENTATION.md")

# ==============================================================================
# 1. GENERATE MARKDOWN
# ==============================================================================
markdown_content = """# SadakSetu: Complete Work Assignment & Field Monitoring System
## End-to-End Operational Workflow & Technical Documentation

---

### Table of Contents
1. **System Overview & Objectives**
2. **Actor Roles & Responsibilities**
3. **The 13-Step Lifecycle Workflow**
4. **Reassignment Protocol**
5. **Database Architecture & Schema Extensions**
6. **API Endpoint Reference**
7. **Mobile Application Architecture (Android)**
8. **Admin Web Dashboard (Port 5174)**
9. **Automated Verification & Test Proofs**

---

## 1. System Overview & Objectives
**SadakSetu** ("Bridge for Roads") is a smart civic infrastructure governance platform designed to resolve road hazards (potholes, structural damage, waterlogging) through real-time collaboration between citizens, municipal administrators, and field repair teams.

### Core Architecture
- **Citizen Android App**: Citizen-facing interface for filing complaints with GPS, viewing nearby hazards, and tracking complaint status.
- **Team Leader Android App**: Integrated directly into the same APK with role-based routing; enables field leaders to accept work, dispatch crew workers, update progress sliders, report delays, capture before/after photos, and submit completions.
- **Admin Web Dashboard**: React + TypeScript portal providing complaint verification, team workload analysis, work order assignment/reassignment, and a dedicated **Work Monitoring & Field Audits** section.
- **Shared FastAPI Backend**: High-performance asynchronous REST backend connecting all clients to a shared PostgreSQL database.

---

## 2. Actor Roles & Responsibilities

| Role | Interface | Key Responsibilities |
| :--- | :--- | :--- |
| **Citizen** (`CITIZEN`) | Android Mobile App | • File geolocated road complaints with photos.<br>• Track status from `SUBMITTED` to `RESOLVED`.<br>• View nearby hazards on map. |
| **Admin** (`ADMIN`) | Web Dashboard (`:5174`) | • Triage and verify citizen complaints.<br>• Assign complaints to available repair teams.<br>• Set priority, SLA deadlines, and repair instructions.<br>• Monitor active, ongoing, delayed, and submitted repairs.<br>• Verify photo evidence and approve resolution or request rework. |
| **Team Leader** (`REPAIR_TEAM`) | Android Mobile App | • View assigned work orders.<br>• Accept work orders and navigate via Google Maps.<br>• Assign crew workers to job sites.<br>• Start repair work and update progress (0–100%).<br>• Report field bottlenecks/delays with reasons.<br>• Capture before-and-after photo evidence.<br>• Submit completed work for Admin audit. |
| **Crew Worker** (Non-Login) | Managed by Leader | • Field laborers and machine operators.<br>• Registered and allocated to work orders by the Team Leader.<br>• No mobile login credentials needed. |

---

## 3. The 13-Step Lifecycle Workflow

```
[ Citizen App ]            [ Admin Web Portal ]          [ Team Leader Mobile ]
       │                            │                              │
 1. Submits Complaint               │                              │
       │                            │                              │
       ▼                            ▼                              │
 2. System Triage ───► 3. Admin Verifies Complaint                 │
                                    │                              │
                                    ▼                              │
                       4. Assigns Work Order ────────────────► 5. Receives Alert
                                    │                              │
                                    │                              ▼
                                    │                     6. Accepts Assignment
                                    │                              │
                                    │                              ▼
                                    │                     7. Dispatches Crew
                                    │                              │
                                    │                              ▼
                                    │                     8. Starts Repair Work
                                    │                              │
                                    │                              ▼
                       10. Synchronizes Telemetry ◄────── 9. Updates Progress (0-100%)
                                    │                              │
                                    │                              ▼
                                    │                     11. Captures Photos (Before & After)
                                    │                              │
                                    │                              ▼
                       12. Review Queue ◄───────────────── 12. Submits Completion
                                    │
                                    ▼
                       13. Admin Audits & Approves
                                    │
                                    ▼
                       Work Order: COMPLETED
                       Complaint: RESOLVED
                                    │
                                    ▼
                       Citizen Notified
```

### Detailed Step-by-Step Breakdown:
1. **Citizen Submits Complaint**: Citizen captures pothole photo with smartphone camera, attaches GPS coordinates, and submits title/description. Status initialized to `SUBMITTED`.
2. **System Ingestion & Triage**: Backend stores validated media, generates a unique tracking code (`SS-YYYYMMDD-XXXXXXXX`), and sends an alert to Admin.
3. **Admin Verification**: Operations Center verifies the road issue and updates status to `UNDER_REVIEW`.
4. **Admin Assigns Work Order**:
   - Admin opens the verified complaint and selects **"Assign Work"**.
   - Admin reviews available Team Leaders with live workload figures (Active, Pending, Delayed).
   - Admin sets **Priority** (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), **Expected Completion Date**, and technical **Repair Instructions**.
   - A formal Work Order is generated (`WO-YYYYMMDD-XXXXXX`), linked to the complaint, and complaint transitions to `ASSIGNED`.
5. **Team Leader Notification**: Push notification and in-app alert dispatched to the assigned Team Leader.
6. **Team Leader Acceptance**: Leader logs into the Android app, navigates to "Pending Assignments", and taps **"Accept Assignment"**. Work Order transitions to `ACCEPTED`.
7. **Team Leader Dispatches Crew**: Leader opens the Work Order, clicks **"Assign Crew"**, and selects team members from the crew roster.
8. **Repair Begins**: Team arrives at the job site; Leader taps **"Start Repair"**. Work Order transitions to `IN_PROGRESS`.
9. **Intermediate Progress Reporting**: As excavation, base-course laying, and bitumen compaction proceed, Leader reports progress (e.g. 65%) with field notes.
10. **Delay Reporting (Exception Flow)**: If bad weather, equipment failure, or traffic causes stoppage, Leader taps **"Report Delay"**, entering a documented explanation. Admin dashboard immediately flags the work order.
11. **Photo Evidence Capture**: Leader uses the mobile camera to capture:
    - **Before Photos**: Initial excavated road condition.
    - **After Photos**: Finished, rolled, and sealed surface.
12. **Submit Completion**: Leader adjusts progress to 100%, writes final sign-off notes, and taps **"Submit Completion for Verification"**. Work Order transitions to `COMPLETION_SUBMITTED`.
13. **Admin Verification & Closure**:
    - Work order appears in Admin's **"Work Monitoring & Field Audits"** queue under *Completion Submitted*.
    - Admin reviews citizen initial photo, leader before/after evidence photos, timeline, and crew notes.
    - Admin clicks **"Approve & Mark Resolved"**.
    - Backend closes Work Order (`COMPLETED`), marks Citizen Complaint `RESOLVED`, and logs verification timestamp and admin user ID.
    - Citizen receives notification confirming the repair is finished.

---

## 4. Reassignment Protocol
If a team is blocked, experiences equipment breakdown, or must be diverted to an emergency:
1. Admin opens the Work Order in Complaint Management.
2. Admin clicks **"Reassign Work"**.
3. Admin selects the new repair team and provides a **mandatory reassign reason** (e.g., *"Team 1 diverted to priority highway flood emergency"*).
4. The previous assignment is archived (`RELEASED`), and an active assignment is generated for the new team.
5. The new Team Leader is immediately alerted and sees the work order in their mobile app with full transfer history.

---

## 5. Database Architecture

### Extended `team_assignments` (Work Orders)
```sql
ALTER TABLE team_assignments ADD COLUMN work_order_number VARCHAR(32);
ALTER TABLE team_assignments ADD COLUMN priority VARCHAR(20) DEFAULT 'MEDIUM';
ALTER TABLE team_assignments ADD COLUMN expected_completion_date TIMESTAMPTZ;
ALTER TABLE team_assignments ADD COLUMN instructions TEXT;
ALTER TABLE team_assignments ADD COLUMN work_status VARCHAR(30) DEFAULT 'PENDING';
ALTER TABLE team_assignments ADD COLUMN progress_percentage INT DEFAULT 0;
ALTER TABLE team_assignments ADD COLUMN progress_notes TEXT;
ALTER TABLE team_assignments ADD COLUMN delay_reason TEXT;
ALTER TABLE team_assignments ADD COLUMN before_photos JSONB DEFAULT '[]'::jsonb;
ALTER TABLE team_assignments ADD COLUMN after_photos JSONB DEFAULT '[]'::jsonb;
ALTER TABLE team_assignments ADD COLUMN assigned_member_ids JSONB DEFAULT '[]'::jsonb;
ALTER TABLE team_assignments ADD COLUMN completion_notes TEXT;
ALTER TABLE team_assignments ADD COLUMN completion_submitted_at TIMESTAMPTZ;
ALTER TABLE team_assignments ADD COLUMN verified_at TIMESTAMPTZ;
ALTER TABLE team_assignments ADD COLUMN verified_by_id UUID REFERENCES users(id);
ALTER TABLE team_assignments ADD COLUMN reassign_reason TEXT;
```

### New `team_members` (Field Crew Staff)
```sql
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES repair_teams(id) ON DELETE CASCADE,
    name VARCHAR(160) NOT NULL,
    employee_id VARCHAR(64) NOT NULL,
    phone VARCHAR(32),
    skills JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 6. REST API Reference

| Endpoint | Method | Role | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/assignments/complaints/{id}` | POST | Admin | Assign verified complaint to repair team. |
| `/api/v1/assignments/complaints/{id}/reassign` | POST | Admin | Reassign work order with mandatory reason. |
| `/api/v1/assignments/my-work` | GET | Leader | Fetch leader's assigned work orders. |
| `/api/v1/assignments/{id}/accept` | POST | Leader | Acknowledge assignment (`ACCEPTED`). |
| `/api/v1/assignments/{id}/start` | POST | Leader | Begin field repair (`IN_PROGRESS`). |
| `/api/v1/assignments/{id}/progress` | POST | Leader | Update progress percentage (0–100%) and notes. |
| `/api/v1/assignments/{id}/delay` | POST | Leader | Report delay with reason. |
| `/api/v1/assignments/{id}/photos` | POST | Leader | Attach before/after quality photos. |
| `/api/v1/assignments/{id}/members` | POST | Leader | Assign crew member IDs to work order. |
| `/api/v1/assignments/{id}/submit-completion` | POST | Leader | Submit work order for admin sign-off. |
| `/api/v1/assignments/{id}/verify` | POST | Admin | Approve resolution or request rework. |
| `/api/v1/assignments/stats` | GET | Admin | Aggregate telemetry statistics for dashboard. |
| `/api/v1/teams/{id}/leader` | POST | Admin | Provision login account for Team Leader. |
| `/api/v1/teams/my-team/members` | GET | Leader | List leader's team crew workers. |
| `/api/v1/teams/my-team/members` | POST | Leader | Add new field worker to team roster. |

---

## 7. Mobile Application Architecture (Android)
- **Role-Based App Entry**: Inside `AppNavHost.kt`, when user signs in:
  - Role `CITIZEN` $\rightarrow$ Renders `CitizenNavHost` with Home, Explore, Report, My Reports, Profile.
  - Role `REPAIR_TEAM` $\rightarrow$ Renders `TeamLeaderApp` with My Work, Crew Management, Detail Screen, and Dialogs.
- **Hardware Integration**: Tested and running on physical OnePlus Nord CE4 via `adb reverse tcp:8001 tcp:8001`.

---

## 8. Verification & Test Proofs
- **Automated E2E Script** (`scratch/test_e2e_complete_workflow.py`): 15 out of 15 operational steps passed with 100% compliance.
- **Reassignment Script** (`scratch/test_reassignment.py`): Reassignment with reason, audit trail, and multi-team visibility passed with 100% compliance.
- **TypeScript & Build Checks**: Zero errors in both root and dashboard frontends.
"""

# Write Markdown
with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(markdown_content)
print(f"Created Markdown: {MD_PATH}")

# ==============================================================================
# 2. GENERATE STANDALONE HTML WITH PRINT/PDF SUPPORT
# ==============================================================================
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SadakSetu - Work Assignment & Monitoring System Workflow</title>
<style>
  :root {{
    --primary: #1e3a8a;
    --primary-light: #3b82f6;
    --accent: #f59e0b;
    --success: #10b981;
    --danger: #ef4444;
    --dark: #0f172a;
    --light: #f8fafc;
    --border: #e2e8f0;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #334155;
    background: #f1f5f9;
    line-height: 1.6;
    padding: 30px 15px;
  }}
  .container {{
    max-width: 1000px;
    margin: 0 auto;
    background: #ffffff;
    padding: 45px;
    border-radius: 14px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  }}
  .header {{
    border-bottom: 3px solid var(--primary);
    padding-bottom: 25px;
    margin-bottom: 35px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
  }}
  .brand {{
    font-size: 32px;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.5px;
  }}
  .brand span {{ color: var(--accent); }}
  .tagline {{ font-size: 14px; color: #64748b; margin-top: 4px; }}
  .btn-print {{
    background: var(--primary);
    color: #fff;
    border: none;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.3);
    transition: all 0.2s;
  }}
  .btn-print:hover {{ background: #172554; transform: translateY(-1px); }}
  
  h1, h2, h3, h4 {{ color: var(--dark); font-weight: 700; margin-top: 28px; margin-bottom: 12px; }}
  h2 {{ font-size: 22px; border-left: 4px solid var(--primary-light); padding-left: 12px; margin-top: 35px; }}
  h3 {{ font-size: 17px; color: var(--primary); }}
  p {{ margin-bottom: 14px; font-size: 15px; }}
  
  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 18px 0 25px 0;
    font-size: 14px;
  }}
  th, td {{
    padding: 12px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  th {{
    background: #f8fafc;
    color: var(--dark);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 12px;
    letter-spacing: 0.5px;
  }}
  tr:hover {{ background: #f8fafc; }}
  
  /* Workflow Cards */
  .workflow-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin: 20px 0;
  }}
  .step-card {{
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    position: relative;
    border-top: 4px solid var(--primary-light);
  }}
  .step-number {{
    display: inline-block;
    width: 26px;
    height: 26px;
    line-height: 26px;
    background: var(--primary);
    color: #fff;
    border-radius: 50%;
    text-align: center;
    font-weight: 700;
    font-size: 12px;
    margin-right: 8px;
  }}
  .step-title {{
    font-size: 15px;
    font-weight: 700;
    color: var(--dark);
    display: inline-block;
    vertical-align: middle;
  }}
  .step-desc {{ font-size: 13px; color: #475569; margin-top: 8px; }}
  
  /* Badges */
  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
  }}
  .badge-pending {{ background: #fef3c7; color: #92400e; }}
  .badge-progress {{ background: #dbeafe; color: #1e40af; }}
  .badge-success {{ background: #d1fae5; color: #065f46; }}
  .badge-alert {{ background: #fee2e2; color: #991b1b; }}
  
  /* Code blocks */
  pre {{
    background: #0f172a;
    color: #f8fafc;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 13px;
    margin: 15px 0;
  }}
  code {{ font-family: "Courier New", Courier, monospace; }}
  
  /* Print Optimization */
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .container {{ box-shadow: none; padding: 0; max-width: 100%; }}
    .btn-print {{ display: none; }}
    .step-card {{ break-inside: avoid; }}
    table {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <div class="brand">Sadak<span>Setu</span></div>
      <div class="tagline">Work Assignment & Real-Time Field Monitoring System • Technical & Operational Manual</div>
    </div>
    <button class="btn-print" onclick="window.print()">Download as PDF / Print</button>
  </div>

  <h2>1. Executive Summary</h2>
  <p>SadakSetu provides an end-to-end connected municipal road maintenance pipeline. The system bridges citizen reporting with automated operations triage, work order assignment, real-time mobile field execution, quality auditing, and citizen feedback.</p>

  <h2>2. System Actors & Access Roles</h2>
  <table>
    <thead>
      <tr>
        <th>Role</th>
        <th>Client Platform</th>
        <th>Authentication</th>
        <th>Core Responsibilities</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Citizen</strong></td>
        <td>Android App</td>
        <td>Bearer Token / Android</td>
        <td>Reports potholes and hazards with GPS, tracks live resolution status.</td>
      </tr>
      <tr>
        <td><strong>Admin</strong></td>
        <td>Web Dashboard (:5174)</td>
        <td>HTTP-only Session Cookie</td>
        <td>Verifies complaints, dispatches repair teams, audits evidence photos, approves completions.</td>
      </tr>
      <tr>
        <td><strong>Team Leader</strong></td>
        <td>Android App (Leader Mode)</td>
        <td>Bearer Token / Android</td>
        <td>Accepts work orders, views road GPS on Google Maps, logs progress (0-100%), uploads photos, submits completions.</td>
      </tr>
      <tr>
        <td><strong>Crew Workers</strong></td>
        <td>Field Operations</td>
        <td>Managed by Leader</td>
        <td>Execution staff assigned to specific work orders. No mobile login required.</td>
      </tr>
    </tbody>
  </table>

  <h2>3. Complete 13-Step Operational Lifecycle</h2>
  <div class="workflow-grid">
    <div class="step-card">
      <span class="step-number">1</span>
      <span class="step-title">Citizen Submission</span>
      <p class="step-desc">Citizen captures photo & GPS coordinates on mobile app. System stores metadata and initializes status to <code>SUBMITTED</code>.</p>
    </div>
    <div class="step-card">
      <span class="step-number">2</span>
      <span class="step-title">Admin Triage</span>
      <p class="step-desc">City Operations Center reviews complaint location, severity, and photo. Status transitions to <code>UNDER_REVIEW</code>.</p>
    </div>
    <div class="step-card">
      <span class="step-number">3</span>
      <span class="step-title">Work Order Assignment</span>
      <p class="step-desc">Admin selects an available Team Leader, inspects workload, sets priority, SLA deadline, instructions, and confirms assignment.</p>
    </div>
    <div class="step-card">
      <span class="step-number">4</span>
      <span class="step-title">Leader Notification</span>
      <p class="step-desc">System dispatches push notification to Team Leader. Work order appears in mobile "Pending Assignments" tab.</p>
    </div>
    <div class="step-card">
      <span class="step-number">5</span>
      <span class="step-title">Work Acceptance</span>
      <p class="step-desc">Team Leader taps "Accept Assignment". Status transitions to <code>ACCEPTED</code> and Admin dashboard updates instantly.</p>
    </div>
    <div class="step-card">
      <span class="step-number">6</span>
      <span class="step-title">Crew Dispatch</span>
      <p class="step-desc">Leader selects team members from the crew roster to allocate skilled operators to the work order.</p>
    </div>
    <div class="step-card">
      <span class="step-number">7</span>
      <span class="step-title">Repair Starts</span>
      <p class="step-desc">Crew arrives on-site; Leader taps "Start Repair". Status becomes <code>IN_PROGRESS</code> and road is marked actively being fixed.</p>
    </div>
    <div class="step-card">
      <span class="step-number">8</span>
      <span class="step-title">Progress Updates</span>
      <p class="step-desc">Leader uses progress slider (0–100%) and notes to transmit real-time telemetry back to the operations center.</p>
    </div>
    <div class="step-card">
      <span class="step-number">9</span>
      <span class="step-title">Delay Reporting</span>
      <p class="step-desc">If materials, weather, or machinery issues cause stoppage, Leader reports delay reason; dashboard highlights alert.</p>
    </div>
    <div class="step-card">
      <span class="step-number">10</span>
      <span class="step-title">Before/After Photos</span>
      <p class="step-desc">Leader snaps verified before and after quality photos with the mobile camera, uploading them to the secure media store.</p>
    </div>
    <div class="step-card">
      <span class="step-number">11</span>
      <span class="step-title">Submit Completion</span>
      <p class="step-desc">With repairs 100% complete, Leader writes sign-off notes and submits. Status transitions to <code>COMPLETION_SUBMITTED</code>.</p>
    </div>
    <div class="step-card">
      <span class="step-number">12</span>
      <span class="step-title">Admin Quality Audit</span>
      <p class="step-desc">Admin opens work order in Work Monitoring tab, compares initial citizen photo with after photos, and inspects notes.</p>
    </div>
    <div class="step-card">
      <span class="step-number">13</span>
      <span class="step-title">Approval & Closure</span>
      <p class="step-desc">Admin clicks "Approve & Mark Resolved". Work order transitions to <code>COMPLETED</code> and Citizen complaint is set to <code>RESOLVED</code>.</p>
    </div>
  </div>

  <h2>4. Reassignment Workflow</h2>
  <p>When an emergency or workload bottleneck requires reallocating work:</p>
  <ol style="margin-left: 20px; font-size: 14px; margin-bottom: 20px;">
    <li>Admin clicks <strong>Reassign Work</strong> in the Complaint Management drawer.</li>
    <li>Admin selects the replacement repair team and enters a <strong>mandatory reassign reason</strong>.</li>
    <li>Previous team assignment is archived (<code>RELEASED</code>).</li>
    <li>New team receives the active assignment with updated priority, deadline, and instructions.</li>
  </ol>

  <h2>5. REST API Specifications</h2>
  <table>
    <thead>
      <tr>
        <th>Method</th>
        <th>Endpoint</th>
        <th>Authorized Role</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/complaints/{{id}}</code></td>
        <td><span class="badge badge-pending">ADMIN</span></td>
        <td>Create and link work order to complaint.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/complaints/{{id}}/reassign</code></td>
        <td><span class="badge badge-pending">ADMIN</span></td>
        <td>Reassign work order with reason.</td>
      </tr>
      <tr>
        <td><code>GET</code></td>
        <td><code>/api/v1/assignments/my-work</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Fetch team leader's assigned work orders.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/accept</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Accept assignment.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/start</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Begin repair work on-site.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/progress</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Transmit 0-100% progress and field notes.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/delay</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Report field delay with documented reason.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/photos</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Upload before & after evidence photos.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/members</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Assign crew worker IDs to work order.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/submit-completion</code></td>
        <td><span class="badge badge-progress">LEADER</span></td>
        <td>Submit finished job for verification.</td>
      </tr>
      <tr>
        <td><code>POST</code></td>
        <td><code>/api/v1/assignments/{{id}}/verify</code></td>
        <td><span class="badge badge-pending">ADMIN</span></td>
        <td>Approve completion or request rework.</td>
      </tr>
      <tr>
        <td><code>GET</code></td>
        <td><code>/api/v1/assignments/stats</code></td>
        <td><span class="badge badge-pending">ADMIN</span></td>
        <td>Aggregate field monitoring metrics.</td>
      </tr>
    </tbody>
  </table>

  <h2>6. Verification Proofs</h2>
  <p>The system was tested using automated test suites and real mobile device interactions:</p>
  <ul>
    <li><strong>End-to-End Workflow Verification:</strong> 15 of 15 steps passed (<code>scratch/test_e2e_complete_workflow.py</code>).</li>
    <li><strong>Reassignment Verification:</strong> Multi-team reassignment and audit trail passed (<code>scratch/test_reassignment.py</code>).</li>
    <li><strong>Android Device Verification:</strong> OnePlus Nord CE4 (<code>3c231d07</code>) tested for both Citizen and Team Leader roles.</li>
  </ul>
</div>
</body>
</html>
"""

# Write HTML
with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Created HTML: {HTML_PATH}")

# ==============================================================================
# 3. GENERATE PROFESSIONAL PDF VIA REPORTLAB
# ==============================================================================
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(A4[0] - 40, 30, f"Page {self._pageNumber} of {page_count}")
        self.drawString(40, 30, "SadakSetu • Work Assignment & Monitoring System Documentation")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 42, A4[0] - 40, 42)
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8,
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e40af"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # Title Banner
    story.append(Paragraph("SadakSetu: Work Assignment & Monitoring System", title_style))
    story.append(Paragraph("Complete Technical Architecture & End-to-End Operational Workflow", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e3a8a"), spaceAfter=14))

    # Section 1: Overview
    story.append(Paragraph("1. System Architecture & Objectives", h1_style))
    story.append(Paragraph(
        "<b>SadakSetu</b> is a unified smart civic infrastructure governance platform connecting three primary tiers: "
        "(1) <b>Citizen Mobile Application</b> for geo-tagged complaint submission, (2) <b>Admin Web Portal</b> "
        "for verification, crew dispatching, and field auditing, and (3) <b>Team Leader Android Field Suite</b> "
        "for on-site execution, crew management, telemetry, and evidence capture.",
        body_style
    ))

    # Section 2: Roles Table
    story.append(Paragraph("2. Actor Roles & Security Matrix", h1_style))
    role_data = [
        [Paragraph("Role", table_cell_bold), Paragraph("Interface", table_cell_bold), Paragraph("Auth Client", table_cell_bold), Paragraph("Responsibilities", table_cell_bold)],
        [Paragraph("<b>Citizen</b>", table_cell), Paragraph("Android App", table_cell), Paragraph("Bearer / Android", table_cell), Paragraph("Submit geotagged road complaints, track resolution timeline.", table_cell)],
        [Paragraph("<b>Admin</b>", table_cell), Paragraph("Web Portal (:5174)", table_cell), Paragraph("Session Cookie", table_cell), Paragraph("Verify complaints, dispatch repair teams, audit evidence, approve completions.", table_cell)],
        [Paragraph("<b>Team Leader</b>", table_cell), Paragraph("Android (Leader Mode)", table_cell), Paragraph("Bearer / Android", table_cell), Paragraph("Accept work orders, view GPS location, update progress (0-100%), upload photos, submit completion.", table_cell)],
        [Paragraph("<b>Crew Workers</b>", table_cell), Paragraph("Field Execution", table_cell), Paragraph("Managed by Leader", table_cell), Paragraph("Allocated to work orders by team lead. No individual login required.", table_cell)],
    ]
    role_table = Table(role_data, colWidths=[80, 100, 95, 235])
    role_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(role_table)
    story.append(Spacer(1, 10))

    # Section 3: 13-Step Workflow
    story.append(Paragraph("3. The 13-Step Operational Lifecycle", h1_style))
    steps_data = [
        [Paragraph("Step", table_cell_bold), Paragraph("Action", table_cell_bold), Paragraph("Actor", table_cell_bold), Paragraph("Operational Impact", table_cell_bold)],
        [Paragraph("1", table_cell), Paragraph("Submit Complaint", table_cell), Paragraph("Citizen", table_cell), Paragraph("GPS, photos, description submitted; status set to SUBMITTED.", table_cell)],
        [Paragraph("2", table_cell), Paragraph("Operations Triage", table_cell), Paragraph("Admin", table_cell), Paragraph("Complaint verified; status transitioned to UNDER_REVIEW.", table_cell)],
        [Paragraph("3", table_cell), Paragraph("Work Order Assignment", table_cell), Paragraph("Admin", table_cell), Paragraph("Team Leader selected, priority and deadline set; WO generated.", table_cell)],
        [Paragraph("4", table_cell), Paragraph("Mobile Alert", table_cell), Paragraph("System", table_cell), Paragraph("Push notification dispatched to assigned Team Leader.", table_cell)],
        [Paragraph("5", table_cell), Paragraph("Accept Assignment", table_cell), Paragraph("Team Leader", table_cell), Paragraph("Leader accepts work on mobile app; status set to ACCEPTED.", table_cell)],
        [Paragraph("6", table_cell), Paragraph("Crew Member Dispatch", table_cell), Paragraph("Team Leader", table_cell), Paragraph("Leader allocates crew members to job site roster.", table_cell)],
        [Paragraph("7", table_cell), Paragraph("Start Repair Work", table_cell), Paragraph("Team Leader", table_cell), Paragraph("Crew on-site; work starts; status set to IN_PROGRESS.", table_cell)],
        [Paragraph("8", table_cell), Paragraph("Progress Updates", table_cell), Paragraph("Team Leader", table_cell), Paragraph("Telemetry update (0-100% slider) synchronized to web.", table_cell)],
        [Paragraph("9", table_cell), Paragraph("Delay Reporting", table_cell), Paragraph("Team Leader", table_cell), Paragraph("Optional exception flow: delay reason flagged on dashboard.", table_cell)],
        [Paragraph("10", table_cell), Paragraph("Evidence Photos", table_cell), Paragraph("Team Leader", table_cell), Paragraph("Before and after photos captured via mobile camera.", table_cell)],
        [Paragraph("11", table_cell), Paragraph("Submit Completion", table_cell), Paragraph("Team Leader", table_cell), Paragraph("Final notes submitted; status set to COMPLETION_SUBMITTED.", table_cell)],
        [Paragraph("12", table_cell), Paragraph("Admin Audit", table_cell), Paragraph("Admin", table_cell), Paragraph("Admin inspects before/after photos & notes in Work Monitoring.", table_cell)],
        [Paragraph("13", table_cell), Paragraph("Approval & Closure", table_cell), Paragraph("Admin", table_cell), Paragraph("Work Order set to COMPLETED; Citizen complaint marked RESOLVED.", table_cell)],
    ]
    steps_table = Table(steps_data, colWidths=[35, 120, 80, 275])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(steps_table)
    story.append(Spacer(1, 10))

    # Page Break for Technical Reference
    story.append(PageBreak())

    # Section 4: Reassignment & API Reference
    story.append(Paragraph("4. Reassignment Protocol", h1_style))
    story.append(Paragraph(
        "If a crew is diverted to an emergency or faces equipment breakdown, Admin triggers <b>Reassign Work</b>. "
        "The system mandates a documented reason, archives the old assignment as <code>RELEASED</code>, and creates "
        "an active assignment for the new team. The new leader is immediately notified and receives full job context.",
        body_style
    ))

    story.append(Paragraph("5. REST API Endpoint Specifications", h1_style))
    api_data = [
        [Paragraph("Method", table_cell_bold), Paragraph("Endpoint Path", table_cell_bold), Paragraph("Role", table_cell_bold), Paragraph("Purpose", table_cell_bold)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/complaints/{id}", table_cell), Paragraph("ADMIN", table_cell), Paragraph("Assign complaint & generate work order.", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/complaints/{id}/reassign", table_cell), Paragraph("ADMIN", table_cell), Paragraph("Reassign work order with reason.", table_cell)],
        [Paragraph("GET", table_cell), Paragraph("/api/v1/assignments/my-work", table_cell), Paragraph("LEADER", table_cell), Paragraph("Fetch assigned work orders for mobile app.", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/accept", table_cell), Paragraph("LEADER", table_cell), Paragraph("Acknowledge assignment (ACCEPTED).", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/start", table_cell), Paragraph("LEADER", table_cell), Paragraph("Start field repair (IN_PROGRESS).", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/progress", table_cell), Paragraph("LEADER", table_cell), Paragraph("Update 0-100% progress and notes.", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/delay", table_cell), Paragraph("LEADER", table_cell), Paragraph("Report bottleneck/delay with reason.", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/photos", table_cell), Paragraph("LEADER", table_cell), Paragraph("Upload before/after evidence photos.", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/members", table_cell), Paragraph("LEADER", table_cell), Paragraph("Assign crew worker IDs to work order.", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/submit-completion", table_cell), Paragraph("LEADER", table_cell), Paragraph("Submit finished job for verification.", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/v1/assignments/{id}/verify", table_cell), Paragraph("ADMIN", table_cell), Paragraph("Approve completion or request rework.", table_cell)],
        [Paragraph("GET", table_cell), Paragraph("/api/v1/assignments/stats", table_cell), Paragraph("ADMIN", table_cell), Paragraph("Aggregate stats for monitoring dashboard.", table_cell)],
    ]
    api_table = Table(api_data, colWidths=[45, 205, 55, 205])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 10))

    # Section 6: Verification & QA Results
    story.append(Paragraph("6. Quality Assurance & Live Test Results", h1_style))
    story.append(Paragraph(
        "All workflows were systematically verified using live API endpoints, real PostgreSQL records, and physical hardware:<br/>"
        "• <b>15/15 Steps Passed</b> in automated workflow test (<code>scratch/test_e2e_complete_workflow.py</code>).<br/>"
        "• <b>Reassignment Protocol Passed</b> with full audit trail (<code>scratch/test_reassignment.py</code>).<br/>"
        "• <b>Mobile Device Verified</b> on OnePlus Nord CE4 (<code>3c231d07</code>) for both Citizen and Team Leader roles.<br/>"
        "• <b>Frontend Web App Verified</b> with zero TypeScript compiler errors on port 5174.",
        body_style
    ))

    # Build the PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Created PDF: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
