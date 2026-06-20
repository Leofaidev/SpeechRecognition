"""
Helper: focus the Hotkeys Start Recording entry and inject Ctrl+C.
Run from command line: python inject_ctrlc.py
"""
import ctypes
import time
import sys

user32 = ctypes.windll.user32

# Known HWNDs from current app session
APP_HWND   = 459172
INNER_ENTRY = 71880   # visible inner tkinter.Entry for Start Recording

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202

def makelparam(x, y):
    return (y & 0xFFFF) << 16 | (x & 0xFFFF)

# Bring app forward
user32.SetForegroundWindow(APP_HWND)
time.sleep(0.2)

# Click on inner entry (sends WM_LBUTTONDOWN/UP via SendMessage)
lp = makelparam(100, 10)
user32.SendMessageW(INNER_ENTRY, WM_LBUTTONDOWN, 0x0001, lp)
user32.SendMessageW(INNER_ENTRY, WM_LBUTTONUP,   0x0000, lp)
time.sleep(0.05)  # minimal wait for FocusIn

# Use keyboard library to send ctrl+c (updates GetAsyncKeyState properly)
try:
    import keyboard
    # keyboard.send sends the key combo to the focused window
    keyboard.send('ctrl+c')
    print("keyboard.send('ctrl+c') done")
    time.sleep(0.5)
except ImportError:
    print("keyboard lib not found, using VkKeyScan approach")
    # Fallback: keybd_event
    VK_CONTROL = 0x11
    VK_C = 0x43
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_C, 0, 0, 0)
    time.sleep(0.3)
    ctypes.windll.user32.keybd_event(VK_C, 0, 2, 0)
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 2, 0)
    time.sleep(0.3)

print("Done")
