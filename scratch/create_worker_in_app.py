import subprocess
import time
import xml.etree.ElementTree as ET

adb = r"C:\Users\HP\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run_adb(args):
    return subprocess.run([adb] + args, capture_output=True, text=True, check=True)

def tap(x, y):
    run_adb(["shell", "input", "tap", str(x), str(y)])

def send_key(code):
    run_adb(["shell", "input", "keyevent", str(code)])

def type_text(text):
    run_adb(["shell", "input", "text", text])

print("Step 1: Check screen...")
# Focus email field
tap(540, 1372)
time.sleep(0.3)
run_adb(["shell", "input", "keycombination", "113", "29"]) # Ctrl+A
send_key(67) # Del
type_text("ramesh.lead@gmail.com")
time.sleep(0.3)

# Focus password field
tap(540, 1592)
time.sleep(0.3)
run_adb(["shell", "input", "keycombination", "113", "29"]) # Ctrl+A
send_key(67) # Del
type_text("LeaderPass123")
time.sleep(0.3)

# Dismiss keyboard
send_key(111)
time.sleep(0.5)

# Tap Sign in
print("Step 2: Tapping Sign in...")
tap(540, 1957)
time.sleep(2.5)

# Tap Team Members tab (bottom right)
print("Step 3: Tapping Team Members bottom tab...")
tap(800, 2270)
time.sleep(1.5)

# Dump UI to locate FAB button
run_adb(["shell", "uiautomator", "dump", "/sdcard/view_members.xml"])
run_adb(["pull", "/sdcard/view_members.xml", r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_members.xml"])

tree = ET.parse(r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_members.xml")
fab_bounds = None
for node in tree.iter('node'):
    desc = node.attrib.get('content-desc', '')
    if 'Add' in desc or 'member' in desc.lower():
        print(f"Found node: desc={desc}, bounds={node.attrib.get('bounds')}")
        fab_bounds = node.attrib.get('bounds')

# If found, tap FAB, otherwise tap standard bottom right FAB position (930, 1980)
if fab_bounds:
    # parse bounds "[x1,y1][x2,y2]"
    parts = fab_bounds.replace('][', ',').replace('[', '').replace(']', '').split(',')
    fx = (int(parts[0]) + int(parts[2])) // 2
    fy = (int(parts[1]) + int(parts[3])) // 2
    print(f"Tapping FAB at ({fx}, {fy})...")
    tap(fx, fy)
else:
    print("Tapping default FAB at (936, 1980)...")
    tap(936, 1980)

time.sleep(1.5)

# Dump UI to find input fields in the dialog
run_adb(["shell", "uiautomator", "dump", "/sdcard/view_dialog.xml"])
run_adb(["pull", "/sdcard/view_dialog.xml", r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_dialog.xml"])

tree = ET.parse(r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_dialog.xml")
edit_texts = []
add_btn_bounds = None
for node in tree.iter('node'):
    if node.attrib.get('class') == 'android.widget.EditText':
        edit_texts.append(node.attrib.get('bounds'))
    text = node.attrib.get('text', '')
    if text == 'Add Member':
        add_btn_bounds = node.attrib.get('bounds')

print(f"Found {len(edit_texts)} input fields in Add Member dialog: {edit_texts}")

if len(edit_texts) >= 4:
    # 1. Full Name
    p1 = edit_texts[0].replace('][', ',').replace('[', '').replace(']', '').split(',')
    tap((int(p1[0]) + int(p1[2])) // 2, (int(p1[1]) + int(p1[3])) // 2)
    time.sleep(0.3)
    type_text("Dinesh%sVerma")
    time.sleep(0.3)

    # 2. Employee ID
    p2 = edit_texts[1].replace('][', ',').replace('[', '').replace(']', '').split(',')
    tap((int(p2[0]) + int(p2[2])) // 2, (int(p2[1]) + int(p2[3])) // 2)
    time.sleep(0.3)
    type_text("EMP-RO-102")
    time.sleep(0.3)

    # 3. Phone
    p3 = edit_texts[2].replace('][', ',').replace('[', '').replace(']', '').split(',')
    tap((int(p3[0]) + int(p3[2])) // 2, (int(p3[1]) + int(p3[3])) // 2)
    time.sleep(0.3)
    type_text("9876543210")
    time.sleep(0.3)

    # 4. Skills
    p4 = edit_texts[3].replace('][', ',').replace('[', '').replace(']', '').split(',')
    tap((int(p4[0]) + int(p4[2])) // 2, (int(p4[1]) + int(p4[3])) // 2)
    time.sleep(0.3)
    type_text("Asphalt,Roller%sOperator")
    time.sleep(0.3)

    # Dismiss keyboard
    send_key(111)
    time.sleep(0.5)

    # Dump again to get Add Member button position
    run_adb(["shell", "uiautomator", "dump", "/sdcard/view_dialog2.xml"])
    run_adb(["pull", "/sdcard/view_dialog2.xml", r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_dialog2.xml"])
    tree2 = ET.parse(r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_dialog2.xml")
    for parent in tree2.iter():
        for child in parent:
            if 'Add Member' in child.attrib.get('text', ''):
                add_btn_bounds = parent.attrib.get('bounds')
                break

    if add_btn_bounds:
        ab = add_btn_bounds.replace('][', ',').replace('[', '').replace(']', '').split(',')
        bx = (int(ab[0]) + int(ab[2])) // 2
        by = (int(ab[1]) + int(ab[3])) // 2
        print(f"Clicking Add Member button at ({bx}, {by})...")
        tap(bx, by)
        time.sleep(2)

print("Taking final screenshot of Team Members...")
run_adb(["shell", "screencap", "-p", "/sdcard/screen_member_created.png"])
run_adb(["pull", "/sdcard/screen_member_created.png", r"C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_member_created.png"])
print("COMPLETE!")
