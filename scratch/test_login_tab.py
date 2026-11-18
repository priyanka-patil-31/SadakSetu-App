import subprocess
import time

adb = r"C:\Users\HP\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run(cmd):
    return subprocess.run(f'"{adb}" {cmd}', shell=True, capture_output=True, text=True)

print("1. Tapping email field...")
run("shell input tap 540 1372")
time.sleep(0.4)
run("shell input keycombination 113 29") # Ctrl+A
run("shell input keyevent 67") # Del
run("shell input text ramesh.lead@gmail.com")
time.sleep(0.4)

print("2. Moving to password via TAB...")
run("shell input keyevent 61") # TAB
time.sleep(0.4)
run("shell input keycombination 113 29") # Ctrl+A
run("shell input keyevent 67") # Del
run("shell input text LeaderPass123")
time.sleep(0.4)

print("3. Dismissing keyboard...")
run("shell input keyevent 4") # BACK dismisses keyboard
time.sleep(0.6)

print("4. Tapping Sign in button...")
run("shell input tap 540 1957")
time.sleep(3)

run("shell screencap -p /sdcard/screen_logged.png")
run(r'pull /sdcard/screen_logged.png "C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_logged_check.png"')
print("Done check!")
