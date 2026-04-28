import subprocess
import time
import pyautogui
import win32gui


def get_sticky_windows():
    results = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)
        if not title.strip():
            return

        if "Sticky Notes" in title:
            rect = win32gui.GetWindowRect(hwnd)
            results.append((hwnd, title, rect))

    win32gui.EnumWindows(callback, None)
    return results


def makeNote():
    # Open Sticky Notes
    subprocess.Popen(
        'explorer shell:AppsFolder\\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe!App'
    )

    time.sleep(3)

    before = get_sticky_windows()
    before_handles = {hwnd for hwnd, _, _ in before}

    if not before:
        print("No Sticky Notes window found")
        return

    old_hwnd, _, old_rect = before[0]

    # bring old note forward
    win32gui.ShowWindow(old_hwnd, 9)
    win32gui.SetForegroundWindow(old_hwnd)
    time.sleep(0.5)

    left, top, right, bottom = old_rect

    # click title area first so text box is not active
    pyautogui.click(left + 120, top + 20)
    time.sleep(0.2)

    # click the + button in the upper-left to create a new note
    pyautogui.click(left + 25, top + 20)
    time.sleep(1.5)

    after = get_sticky_windows()
    after_handles = {hwnd for hwnd, _, _ in after}
    new_handles = after_handles - before_handles

    if new_handles:
        new_hwnd = list(new_handles)[0]
    else:
        new_hwnd = win32gui.GetForegroundWindow()

    # move and resize only the new note
    win32gui.ShowWindow(new_hwnd, 9)
    win32gui.MoveWindow(new_hwnd, 0, 0, 500, 400, True)
    win32gui.SetForegroundWindow(new_hwnd)

    left, top, right, bottom = win32gui.GetWindowRect(new_hwnd)

    # menu button
    print("Menu click in 3 seconds...")

    pyautogui.click(left + 440, top + 35)

    time.sleep(0.5)

    # color option
    print("Color click in 3 seconds...")
    pyautogui.click(left + 350, top + 50)

    print("Moved new note")
    return new_hwnd



def writeNote(hwnd, text):
    win32gui.ShowWindow(hwnd, 9)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)

    # click inside the note body, below the title/menu area
    pyautogui.click(left + 40, top + 90)
    time.sleep(0.2)

    pyautogui.write(text, interval=0.01)