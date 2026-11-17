import subprocess
import time

adb = r"C:\Users\HP\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run_adb(args):
    subprocess.run([adb] + args, check=True)

print("1. Focusing Email field...")
run_adb(["shell", "input", "tap", "900", "1078"])
time.sleep(0.4)
run_adb(["shell", "input", "keyevent", "123"]) # MOVE_END
for _ in range(30):
    run_adb(["shell", "input", "keyevent", "67"]) # DEL
time.sleep(0.2)
run_adb(["shell", "input", "text", "aarav.citizen@gmail.com"])
time.sleep(0.5)

print("2. Focusing Password field...")
run_adb(["shell", "input", "tap", "900", "1298"])
time.sleep(0.4)
run_adb(["shell", "input", "keyevent", "123"]) # MOVE_END
for _ in range(30):
    run_adb(["shell", "input", "keyevent", "67"]) # DEL
time.sleep(0.2)
run_adb(["shell", "input", "text", "CitizenPass123"])
time.sleep(0.5)

print("3. Dismissing keyboard...")
run_adb(["shell", "input", "keyevent", "111"])
time.sleep(0.6)

print("4. Tapping Sign In...")
run_adb(["shell", "input", "tap", "540", "1663"])
time.sleep(2.5)

print("5. Pulling screenshot...")
run_adb(["shell", "screencap", "-p", "/sdcard/screen_citizen_logged_live.png"])
run_adb(["pull", "/sdcard/screen_citizen_logged_live.png", r"C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_citizen_logged_live.png"])
print("Done!")
