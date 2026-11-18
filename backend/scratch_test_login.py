import urllib.request
import json

test_accounts = [
    ("vikram.lead@example.com", "Leader123"),
    ("ramesh.lead@gmail.com", "Leader123"),
    ("suresh.lead@example.com", "Leader123"),
    ("rohan.citizen@example.com", "User123"),
    ("aarav.citizen@gmail.com", "Citizen123"),
]

for email, pwd in test_accounts:
    req = urllib.request.Request(
        "http://127.0.0.1:8001/api/v1/auth/login",
        data=json.dumps({"email": email, "password": pwd}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            role = data.get("user", {}).get("role")
            print(f"Login SUCCESS: {email} -> role={role}")
    except urllib.error.HTTPError as e:
        print(f"Login FAILED: {email} -> {e.code} {e.read().decode()}")
