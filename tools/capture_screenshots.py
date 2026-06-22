"""Capture fresh screenshots of all 11 WSP panels and compile into a PDF."""

import ctypes
import ctypes.wintypes
import time
import sys
from pathlib import Path
from PIL import Image, ImageGrab, ImageDraw, ImageFont

user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
GetWindowText = user32.GetWindowTextW
GetWindowTextLength = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowRect = user32.GetWindowRect
SetForegroundWindow = user32.SetForegroundWindow
ShowWindow = user32.ShowWindow
BringWindowToTop = user32.BringWindowToTop
SetCursorPos = user32.SetCursorPos
mouse_event = user32.mouse_event
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
SW_RESTORE = 9

OUT_DIR = Path(__file__).parent.parent / "screens" / "release"
OUT_PDF = Path(__file__).parent.parent / "docs" / "screenshots_v1.0.pdf"

PANELS = [
    ("Home",             "Главная"),
    ("Settings",         "Настройки"),
    ("Voice Profiles",   "Голосовые профили"),
    ("AI Config",        "Настройки ИИ"),
    ("Dictionary",       "Словарь замен"),
    ("Batch Queue",      "Пакетная очередь"),
    ("Output Config",    "Настройки вывода"),
    ("Hotkeys",          "Горячие клавиши"),
    ("Session History",  "История сессий"),
    ("Backup & Restore", "Резервное копирование"),
    ("About",            "О программе"),
]


def find_wsp_window():
    """Return HWND of the WSP main window, or None."""
    results = []

    def callback(hwnd, _):
        if not IsWindowVisible(hwnd):
            return True
        length = GetWindowTextLength(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buf, length + 1)
        title = buf.value
        # Match any window containing "WSP" in the title bar or the Russian title
        if "WSP" in title or "распознавания" in title or "Speech" in title:
            results.append(hwnd)
        return True

    EnumWindows(EnumWindowsProc(callback), 0)
    return results[0] if results else None


def click_at(x: int, y: int):
    SetCursorPos(x, y)
    time.sleep(0.05)
    mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def get_window_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def capture_window(hwnd) -> Image.Image:
    l, t, r, b = get_window_rect(hwnd)
    img = ImageGrab.grab(bbox=(l, t, r, b), all_screens=True)
    return img


def add_label(img: Image.Image, label: str) -> Image.Image:
    """Add a white label bar at the bottom of the image."""
    bar_h = 36
    new = Image.new("RGB", (img.width, img.height + bar_h), (30, 30, 30))
    new.paste(img, (0, 0))
    draw = ImageDraw.Draw(new)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    draw.text((img.width // 2, img.height + bar_h // 2), label,
              fill=(220, 220, 220), font=font, anchor="mm")
    return new


def build_pdf(images: list, labels: list):
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    # A4 landscape at 96 dpi: 1123 x 794 px
    PAGE_W, PAGE_H = 1123, 794
    MARGIN = 20
    TITLE_H = 50

    pages = []
    for img, label in zip(images, labels):
        page = Image.new("RGB", (PAGE_W, PAGE_H), (20, 20, 20))

        # Scale image to fit within page minus margins and title
        avail_w = PAGE_W - 2 * MARGIN
        avail_h = PAGE_H - 2 * MARGIN - TITLE_H
        ratio = min(avail_w / img.width, avail_h / img.height)
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)
        scaled = img.resize((new_w, new_h), Image.LANCZOS)

        x = (PAGE_W - new_w) // 2
        y = MARGIN + TITLE_H + (avail_h - new_h) // 2
        page.paste(scaled, (x, y))

        # Title bar
        draw = ImageDraw.Draw(page)
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
            small_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
        except Exception:
            title_font = ImageFont.load_default()
            small_font = title_font

        draw.text((PAGE_W // 2, MARGIN + TITLE_H // 2),
                  f"WSP v1.0  —  {label}",
                  fill=(255, 255, 255), font=title_font, anchor="mm")
        draw.text((PAGE_W - MARGIN, PAGE_H - 10),
                  "WSP Speech Recognition  ·  github.com/Leofaidev/SpeechRecognition",
                  fill=(120, 120, 120), font=small_font, anchor="rm")

        pages.append(page)

    # Cover page
    cover = Image.new("RGB", (PAGE_W, PAGE_H), (20, 20, 30))
    draw = ImageDraw.Draw(cover)
    try:
        big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 48)
        med = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 24)
        sml = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
    except Exception:
        big = med = sml = ImageFont.load_default()

    draw.text((PAGE_W // 2, PAGE_H // 2 - 80), "WSP",
              fill=(255, 255, 255), font=big, anchor="mm")
    draw.text((PAGE_W // 2, PAGE_H // 2 - 10), "Speech Recognition Program",
              fill=(180, 180, 200), font=med, anchor="mm")
    draw.text((PAGE_W // 2, PAGE_H // 2 + 40), "Version 1.0.001",
              fill=(100, 160, 255), font=med, anchor="mm")
    draw.text((PAGE_W // 2, PAGE_H // 2 + 90), "Application Screenshots",
              fill=(140, 140, 160), font=sml, anchor="mm")
    draw.text((PAGE_W // 2, PAGE_H - 30), "github.com/Leofaidev/SpeechRecognition",
              fill=(80, 80, 100), font=sml, anchor="mm")

    all_pages = [cover] + pages

    # Save as PDF
    all_pages[0].save(
        OUT_PDF, "PDF", resolution=96,
        save_all=True, append_images=all_pages[1:]
    )
    print(f"PDF saved: {OUT_PDF}  ({len(all_pages)} pages)")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    hwnd = find_wsp_window()
    if not hwnd:
        print("ERROR: WSP window not found. Launch the app first.", file=sys.stderr)
        sys.exit(1)

    print(f"Found WSP window: HWND={hwnd}")
    ShowWindow(hwnd, SW_RESTORE)
    BringWindowToTop(hwnd)
    SetForegroundWindow(hwnd)
    time.sleep(0.8)

    l, t, r, b = get_window_rect(hwnd)
    win_w = r - l
    win_h = b - t

    # Sidebar button positions (relative to window client area).
    # From visual inspection: x≈93, first button y≈97, step≈38px.
    # Title bar is ~30px, so absolute y = t + 30 + relative_y.
    BTN_X = l + 93
    BTN_Y_START = t + 97
    BTN_STEP = 38

    images = []
    labels = []

    for i, (label_en, _label_ru) in enumerate(PANELS):
        btn_y = BTN_Y_START + i * BTN_STEP
        print(f"  Clicking panel {i+1:02d}: {label_en}  (x={BTN_X}, y={btn_y})")
        click_at(BTN_X, btn_y)
        time.sleep(0.4)

        img = capture_window(hwnd)
        fname = OUT_DIR / f"panel_{i+1:02d}_{label_en.lower().replace(' ', '_').replace('&', 'and')}.png"
        img.save(fname)
        print(f"    Saved: {fname.name}  ({img.width}x{img.height})")

        images.append(img)
        labels.append(label_en)

    print("\nBuilding PDF...")
    build_pdf(images, labels)
    print("Done.")


if __name__ == "__main__":
    main()
