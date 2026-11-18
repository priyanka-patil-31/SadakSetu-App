import subprocess
import time
import xml.etree.ElementTree as ET

adb = r"C:\Users\HP\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run(cmd):
    return subprocess.run(f'"{adb}" {cmd}', shell=True, capture_output=True, text=True)

print("1. Tapping Team Members tab...")
run("shell input tap 800 2270")
time.sleep(1.5)

run("shell screencap -p /sdcard/screen_members_view.png")
run(r'pull /sdcard/screen_members_view.png "C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_members_initial.png"')

print("2. Dumping UI to find FAB button...")
run("shell uiautomator dump /sdcard/view_team.xml")
run(r'pull /sdcard/view_team.xml "C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_team.xml"')

tree = ET.parse(r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_team.xml")
fab_point = (936, 1980) # default FAB position
for node in tree.iter('node'):
    desc = node.attrib.get('content-desc', '')
    if 'Add' in desc or 'member' in desc.lower():
        b = node.attrib.get('bounds')
        print(f"Found node: desc={desc}, bounds={b}")
        pts = b.replace('][', ',').replace('[', '').replace(']', '').split(',')
        fab_point = ((int(pts[0]) + int(pts[2])) // 2, (int(pts[1]) + int(pts[3])) // 2)

print(f"3. Tapping FAB at {fab_point}...")
run(f"shell input tap {fab_point[0]} {fab_point[1]}")
time.sleep(1.5)

run("shell screencap -p /sdcard/screen_add_dialog.png")
run(r'pull /sdcard/screen_add_dialog.png "C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_add_member_dialog.png"')

print("4. Dumping Add Member dialog UI...")
run("shell uiautomator dump /sdcard/view_add_member.xml")
run(r'pull /sdcard/view_add_member.xml "C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_add_member.xml"')

tree2 = ET.parse(r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_add_member.xml")
edit_texts = []
for node in tree2.iter('node'):
    if node.attrib.get('class') == 'android.widget.EditText':
        edit_texts.append(node.attrib.get('bounds'))

print(f"Found {len(edit_texts)} input fields in Add Member dialog: {edit_texts}")

if len(edit_texts) >= 4:
    # 1. Full Name
    p1 = edit_texts[0].replace('][', ',').replace('[', '').replace(']', '').split(',')
    run(f"shell input tap {(int(p1[0]) + int(p1[2])) // 2} {(int(p1[1]) + int(p1[3])) // 2}")
    time.sleep(0.3)
    run("shell input text Sunil%sYadav")
    time.sleep(0.3)

    # 2. Employee ID
    p2 = edit_texts[1].replace('][', ',').replace('[', '').replace(']', '').split(',')
    run(f"shell input tap {(int(p2[0]) + int(p2[2])) // 2} {(int(p2[1]) + int(p2[3])) // 2}")
    time.sleep(0.3)
    run("shell input text EMP-SY-501")
    time.sleep(0.3)

    # 3. Phone
    p3 = edit_texts[2].replace('][', ',').replace('[', '').replace(']', '').split(',')
    run(f"shell input tap {(int(p3[0]) + int(p3[2])) // 2} {(int(p3[1]) + int(p3[3])) // 2}")
    time.sleep(0.3)
    run("shell input text 9876512345")
    time.sleep(0.3)

    # 4. Skills
    p4 = edit_texts[3].replace('][', ',').replace('[', '').replace(']', '').split(',')
    run(f"shell input tap {(int(p4[0]) + int(p4[2])) // 2} {(int(p4[1]) + int(p4[3])) // 2}")
    time.sleep(0.3)
    run("shell input text Asphalt,Roller")
    time.sleep(0.3)

    # Dismiss keyboard
    run("shell input keyevent 111")
    time.sleep(0.5)

    # Find Add Member button bounds
    run("shell uiautomator dump /sdcard/view_add_member_btn.xml")
    run(r'pull /sdcard/view_add_member_btn.xml "C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_add_member_btn.xml"')
    tree3 = ET.parse(r"C:\Users\HP\Downloads\SadakSetu project\SadakSetu--main\scratch\view_add_member_btn.xml")
    add_btn_pt = None
    for parent in tree3.iter():
        for child in parent:
            if 'Add Member' in child.attrib.get('text', ''):
                b = parent.attrib.get('bounds')
                pts = b.replace('][', ',').replace('[', '').replace(']', '').split(',')
                add_btn_pt = ((int(pts[0]) + int(pts[2])) // 2, (int(pts[1]) + int(pts[3])) // 2)
                break

    if add_btn_pt:
        print(f"5. Tapping Add Member at {add_btn_pt}...")
        run(f"shell input tap {add_btn_pt[0]} {add_btn_pt[1]}")
        time.sleep(2.0)

print("6. Pulling final screenshot...")
run("shell screencap -p /sdcard/screen_worker_added.png")
run(r'pull /sdcard/screen_worker_added.png "C:\Users\HP\.gemini\antigravity\brain\42618525-399e-40d1-8f73-7b43c2e5d09e\phone_screen_worker_created_success.png"')
print("Done!")
