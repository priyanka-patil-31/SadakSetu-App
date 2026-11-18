import subprocess
import time

adb = r"C:\Users\HP\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run(cmd):
    return subprocess.run(f'"{adb}" {cmd}', shell=True, capture_output=True, text=True)

print("1. Focusing email field...")
run("shell input tap 540 1372")
time.sleep(0.5)

print("2. Typing email...")
run("shell input text ramesh.lead@gmail.com")
time.sleep(0.5)

print("3. Tabbing to password field...")
run("shell input keyevent 61")
time.sleep(0.5)

print("4. Typing password...")
run("shell input text LeaderPass123")
time.sleep(0.5)

print("5. Dismissing keyboard...")
run("shell input keyevent 4")
time.sleep(0.8)

print("6. Tapping Sign in...")
run("shell input tap 540 1957")
time.sleep(3.0)

run("shell screencap -p /sdcard/screen_clean_logged.png")
run(r'pull /sdcard/screen_clean_logged.png "C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_clean_logged.png"')
print("Done clean login!")
