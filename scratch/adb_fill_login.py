import subprocess
import time

adb = r"C:\Users\HP\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run_adb(cmd):
    return subprocess.run(f'"{adb}" {cmd}', shell=True, capture_output=True, text=True)

# Tap email field
run_adb("shell input tap 300 1380")
time.sleep(0.3)
# Select all and delete
for _ in range(50):
    run_adb("shell input keyevent 67") # KEYCODE_DEL
time.sleep(0.3)
run_adb("shell input text aarav.citizen@gmail.com")
time.sleep(0.3)

# Tap password field
run_adb("shell input tap 300 1600")
time.sleep(0.3)
for _ in range(50):
    run_adb("shell input keyevent 67")
time.sleep(0.3)
run_adb("shell input text CitizenPassword123!")
time.sleep(0.3)

# Tap Sign in
run_adb("shell input tap 540 1950")
time.sleep(2)

run_adb("shell screencap -p /sdcard/screen_citizen_login.png")
run_adb(r'pull /sdcard/screen_citizen_login.png "C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_citizen_login.png"')
print("Done")
