"""T-11: Generate three UI wireframe PDFs for the Speech Recognition App.

Variants:
  v1 — Minimalist  (flat, white/grey, blue accent, maximum whitespace)
  v2 — Full-Featured (rich colour, rounded cards, gradients implied, modern)
  v3 — Dark Studio  (DAW-inspired dark mode, teal/cyan accents, compact)

Each PDF contains 11 pages:
  Cover, Main Window (Regular), Main Window (Short Session / Amendment),
  Settings, Voice Profile Management, Substitution Dictionary, Batch Queue,
  Output Content Configuration, Hotkey Configuration,
  Speaker Labelling Prompt, Session History, Backup & Restore.

Output: docs/wireframes/wireframe_v{1,2,3}_*.pdf
"""

from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from pathlib import Path
from dataclasses import dataclass

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "wireframes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Coordinate system ─────────────────────────────────────────────────────────
# Page : xlim=(0,100)  ylim=(0,70)   figure 17×11.9 in  (landscape)
# Window box  : x 2–97  y 8–69
#   title bar : y 65–69 (4 units)
#   nav/toolbar: y 59–65 (6 units)
#   content   : y 8–59 (51 units)
# Legend strip: y 0–7

PW, PH = 100, 70
FW, FH = 17, 11.9
WX0, WY0, WX1, WY1 = 2, 8, 97, 69
TBH = 4    # title bar height
NAVH = 6   # nav/toolbar height
CY0 = WY0          # content start y
CY1 = WY1 - TBH - NAVH  # content end y  (= WY0 + 51 = 59)


# ── Style ─────────────────────────────────────────────────────────────────────

@dataclass
class S:
    name: str; slug: str; subtitle: str
    # backgrounds
    bg: str; win: str; tb: str; nav: str; panel: str; sidebar: str
    # brand / state colours
    pri: str; pri_t: str; sec: str; acc: str; ok: str; warn: str
    # text / border
    fg: str; fg2: str; bdr: str; inp: str; li: str; ls: str; tb_t: str; ann: str
    # geometry
    rad: float; lw: float
    # fonts
    fs_h: float; fs_b: float; fs_s: float; fs_xs: float


V1 = S(
    name="Minimalist", slug="v1_minimalist",
    subtitle="Clean, flat, maximum whitespace — content leads, chrome follows",
    bg="#F9F9F9", win="#FFFFFF", tb="#3D3D3D", nav="#F2F2F2", panel="#FFFFFF", sidebar="#F7F7F7",
    pri="#2980B9", pri_t="#FFFFFF", sec="#888888", acc="#C0392B", ok="#27AE60", warn="#E67E22",
    fg="#2C2C2C", fg2="#AAAAAA", bdr="#DEDEDE", inp="#FFFFFF", li="#F5F5F5", ls="#D6EAF8",
    tb_t="#FFFFFF", ann="#C0392B",
    rad=0.0, lw=0.65,
    fs_h=9.0, fs_b=7.2, fs_s=6.0, fs_xs=5.2,
)

V2 = S(
    name="Full-Featured", slug="v2_full",
    subtitle="Rich colour, card elevation, icon hints, modern CustomTkinter palette",
    bg="#E8EDF5", win="#FFFFFF", tb="#1E3A5F", nav="#2563EB", panel="#FFFFFF", sidebar="#F0F4FA",
    pri="#2563EB", pri_t="#FFFFFF", sec="#64748B", acc="#EF4444", ok="#10B981", warn="#F59E0B",
    fg="#1E293B", fg2="#94A3B8", bdr="#CBD5E1", inp="#F8FAFC", li="#F1F5F9", ls="#DBEAFE",
    tb_t="#FFFFFF", ann="#B91C1C",
    rad=2.5, lw=0.5,
    fs_h=9.5, fs_b=7.5, fs_s=6.2, fs_xs=5.4,
)

V3 = S(
    name="Dark Studio", slug="v3_dark_studio",
    subtitle="DAW-inspired dark mode — professional, compact, high-contrast",
    bg="#0D1117", win="#161B22", tb="#090D13", nav="#1C2128", panel="#21262D", sidebar="#161B22",
    pri="#00D4AA", pri_t="#0D1117", sec="#8B949E", acc="#FF6B6B", ok="#3FB950", warn="#E3B341",
    fg="#C9D1D9", fg2="#6E7681", bdr="#30363D", inp="#0D1117", li="#21262D", ls="#1F4C3A",
    tb_t="#C9D1D9", ann="#FF6B6B",
    rad=1.5, lw=0.7,
    fs_h=9.0, fs_b=7.2, fs_s=6.0, fs_xs=5.2,
)

ALL = [V1, V2, V3]


# ── Drawing primitives ────────────────────────────────────────────────────────

def _rrect(ax, x, y, w, h, fc, ec, lw, r):
    """Draw a rectangle (rounded if r > 0)."""
    if r > 0:
        pad = r
        p = FancyBboxPatch(
            (x + pad, y + pad), max(w - 2 * pad, 0.01), max(h - 2 * pad, 0.01),
            boxstyle=f"round,pad={pad}",
            facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2,
        )
    else:
        p = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2)
    ax.add_patch(p)


def box(ax, s: S, x, y, w, h, fc=None, ec=None, lw=None, r=None):
    _rrect(ax, x, y, w, h,
           fc=fc or s.panel, ec=ec or s.bdr,
           lw=lw if lw is not None else s.lw,
           r=r if r is not None else s.rad)


def txt(ax, s: S, x, y, text, fc=None, fs=None, ha="left", va="center",
        bold=False, mono=False, clip=True):
    ax.text(x, y, text, color=fc or s.fg, fontsize=fs or s.fs_b,
            ha=ha, va=va, fontweight="bold" if bold else "normal",
            fontfamily="monospace" if mono else "sans-serif",
            clip_on=clip, zorder=5)


def btn(ax, s: S, x, y, w, h, label, kind="pri"):
    colours = {
        "pri": (s.pri, s.pri_t),
        "sec": (s.panel, s.fg),
        "danger": (s.acc, "#FFFFFF"),
        "ok": (s.ok, "#FFFFFF"),
        "ghost": ("none", s.pri),
    }
    fc, ft = colours.get(kind, colours["pri"])
    ec = s.bdr if kind in ("sec", "ghost") else "none"
    box(ax, s, x, y, w, h, fc=fc, ec=ec, lw=s.lw)
    txt(ax, s, x + w / 2, y + h / 2, label, fc=ft, ha="center", bold=True)


def inp(ax, s: S, x, y, w, h, placeholder="", value=""):
    box(ax, s, x, y, w, h, fc=s.inp, ec=s.bdr)
    disp = value if value else placeholder
    fc = s.fg if value else s.fg2
    txt(ax, s, x + 1.2, y + h / 2, disp, fc=fc, fs=s.fs_s)


def ddl(ax, s: S, x, y, w, h, value="Select…"):
    box(ax, s, x, y, w, h, fc=s.inp, ec=s.bdr)
    txt(ax, s, x + 1.2, y + h / 2, value, fs=s.fs_s)
    # chevron
    cx, cy = x + w - 2.2, y + h / 2
    ax.annotate("▾", (cx, cy), color=s.fg2, fontsize=s.fs_s, ha="center", va="center",
                zorder=5)


def chk(ax, s: S, x, y, checked, label):
    size = 2.0
    fc = s.pri if checked else s.inp
    box(ax, s, x, y, size, size, fc=fc, ec=s.bdr if not checked else s.pri)
    if checked:
        txt(ax, s, x + size / 2, y + size / 2, "✓", fc=s.pri_t, fs=s.fs_s, ha="center", bold=True)
    txt(ax, s, x + size + 1.0, y + size / 2, label, fs=s.fs_s)


def tog(ax, s: S, x, y, on, label):
    tw, th = 5.0, 2.2
    fc = s.pri if on else s.sec
    _rrect(ax, x, y, tw, th, fc=fc, ec="none", lw=0, r=th / 2)
    cx = (x + tw - th / 2 - 0.3) if on else (x + th / 2 + 0.3)
    c = Circle((cx, y + th / 2), th / 2 - 0.3, color="#FFFFFF", zorder=5)
    ax.add_patch(c)
    txt(ax, s, x + tw + 1.2, y + th / 2, label, fs=s.fs_s)


def lstbox(ax, s: S, x, y, w, h, items, sel=None):
    box(ax, s, x, y, w, h, fc=s.inp, ec=s.bdr)
    row_h = min(3.5, h / max(len(items), 1))
    for i, item in enumerate(items):
        ry = y + h - (i + 1) * row_h
        if ry < y:
            break
        fc = s.ls if i == sel else ("none" if i % 2 == 0 else s.li)
        if fc != "none":
            ax.add_patch(Rectangle((x, ry), w, row_h, facecolor=fc, edgecolor="none", zorder=3))
        txt(ax, s, x + 1.5, ry + row_h / 2, item, fs=s.fs_s)
        if i > 0:
            ax.add_line(Line2D([x, x + w], [ry + row_h, ry + row_h],
                               color=s.bdr, linewidth=0.3, zorder=4))


def prog(ax, s: S, x, y, w, h, val, label=""):
    box(ax, s, x, y, w, h, fc=s.inp, ec=s.bdr)
    if val > 0:
        ax.add_patch(Rectangle((x, y), w * val, h, facecolor=s.pri, edgecolor="none", zorder=3))
    if label:
        txt(ax, s, x + w / 2, y + h / 2, label, fc=s.pri_t if val > 0.5 else s.fg, ha="center", fs=s.fs_xs)


def tag(ax, s: S, x, y, n):
    """Draw a numbered callout circle for element labelling."""
    c = Circle((x, y), 1.1, color=s.ann, zorder=10)
    ax.add_patch(c)
    txt(ax, s, x, y, str(n), fc="#FFFFFF", fs=s.fs_xs, ha="center", va="center", bold=True)


def hline(ax, s: S, y, x0=None, x1=None):
    x0 = x0 if x0 is not None else WX0
    x1 = x1 if x1 is not None else WX1
    ax.add_line(Line2D([x0, x1], [y, y], color=s.bdr, linewidth=s.lw, zorder=4))


def vline(ax, s: S, x, y0=None, y1=None):
    y0 = y0 if y0 is not None else CY0
    y1 = y1 if y1 is not None else CY1
    ax.add_line(Line2D([x, x], [y0, y1], color=s.bdr, linewidth=s.lw, zorder=4))


def signal_meter(ax, s: S, x, y, w, h, bars=12):
    bw = w / (bars * 1.4)
    for i in range(bars):
        bx = x + i * (w / bars)
        bh = h * (0.3 + 0.7 * i / bars)
        fc = s.ok if i < bars * 0.6 else (s.warn if i < bars * 0.85 else s.acc)
        ax.add_patch(Rectangle((bx, y), bw, bh, facecolor=fc, edgecolor="none", zorder=4))


def section_header(ax, s: S, x, y, w, h, title):
    box(ax, s, x, y, w, h, fc=s.sidebar, ec="none")
    txt(ax, s, x + 1.5, y + h / 2, title, fs=s.fs_s, bold=True, fc=s.sec)


def card(ax, s: S, x, y, w, h, title=None):
    box(ax, s, x, y, w, h, fc=s.panel, ec=s.bdr)
    if title:
        txt(ax, s, x + 1.5, y + h - 2.0, title, bold=True, fs=s.fs_s, fc=s.sec)


def legend_row(ax, s: S, elements):
    """Draw element legend strip at bottom of page y 0-7."""
    ax.add_patch(Rectangle((WX0, 0), WX1 - WX0, 7.5, facecolor=s.panel, edgecolor=s.bdr,
                            linewidth=s.lw * 0.6, zorder=1))
    txt(ax, s, WX0 + 1, 6.8, "Elements:", fc=s.sec, fs=s.fs_xs, bold=True)
    col_w = (WX1 - WX0 - 2) / 5
    for i, (n, name) in enumerate(elements[:15]):
        col = i % 5
        row = i // 5
        bx = WX0 + 1 + col * col_w
        by = 5.2 - row * 2.4
        tag(ax, s, bx + 0.7, by + 0.6, n)
        txt(ax, s, bx + 2.3, by + 0.6, name, fs=s.fs_xs, fc=s.fg2)


# ── Window frame ──────────────────────────────────────────────────────────────

def window_frame(ax, s: S, panel_name: str):
    """Draw outer window + title bar + nav strip; return content top y."""
    # window box
    box(ax, s, WX0, WY0, WX1 - WX0, WY1 - WY0, fc=s.win, ec=s.bdr, lw=s.lw * 1.5)
    # title bar
    tby = WY1 - TBH
    ax.add_patch(Rectangle((WX0, tby), WX1 - WX0, TBH, facecolor=s.tb, zorder=3))
    txt(ax, s, WX0 + 3, tby + TBH / 2, "Speech Recognition Program", fc=s.tb_t,
        bold=True, fs=s.fs_b)
    # window controls
    for i, (col, sym) in enumerate([(s.ok, ""), (s.warn, ""), (s.acc, "")]):
        cx = WX1 - 2.5 - i * 3.5
        c = Circle((cx, tby + TBH / 2), 1.0, color=col, zorder=5)
        ax.add_patch(c)
    # nav bar (coloured for V2, grey otherwise)
    navfc = s.nav
    navy = tby - NAVH
    ax.add_patch(Rectangle((WX0, navy), WX1 - WX0, NAVH, facecolor=navfc, zorder=3))
    # panel name breadcrumb
    txt(ax, s, WX0 + 3, navy + NAVH / 2, f"◀  {panel_name}", fc=s.tb_t, fs=s.fs_s, bold=True)
    # horizontal rule below nav
    hline(ax, s, navy, WX0, WX1)
    return navy   # return y of content top


# ── Page setup ────────────────────────────────────────────────────────────────

def new_page(s: S, panel_title: str):
    fig, ax = plt.subplots(figsize=(FW, FH))
    ax.set_xlim(0, PW)
    ax.set_ylim(0, PH)
    ax.set_aspect("auto")
    ax.axis("off")
    fig.patch.set_facecolor(s.bg)
    ax.set_facecolor(s.bg)
    # panel title above window
    txt(ax, s, WX0, WY1 + 0.6, panel_title.upper(),
        fc=s.pri, fs=s.fs_b, bold=True)
    window_frame(ax, s, panel_title)
    return fig, ax


# ── Panels ────────────────────────────────────────────────────────────────────

def panel_cover(s: S):
    fig, ax = plt.subplots(figsize=(FW, FH))
    ax.set_xlim(0, PW); ax.set_ylim(0, PH)
    ax.axis("off")
    fig.patch.set_facecolor(s.bg); ax.set_facecolor(s.bg)
    # large title block
    box(ax, s, 15, 30, 70, 30, fc=s.tb, ec="none")
    txt(ax, s, 50, 53, "Speech Recognition Program", fc=s.tb_t, fs=16, ha="center", bold=True)
    txt(ax, s, 50, 48, "UI Wireframes — Design Option", fc=s.tb_t, fs=11, ha="center")
    box(ax, s, 15, 26, 70, 4, fc=s.pri, ec="none")
    txt(ax, s, 50, 28, f"Variant {s.slug[1]}: {s.name}", fc=s.pri_t, fs=13, ha="center", bold=True)
    txt(ax, s, 50, 22, s.subtitle, fc=s.fg, fs=s.fs_b, ha="center")
    txt(ax, s, 50, 18, "Covers all 9 GUI panels  +  Session History  +  Short Session Amendment",
        fc=s.fg2, fs=s.fs_s, ha="center")
    txt(ax, s, 50, 14, "Spec Sections 12.4  ·  12.6.d  ·  12.8", fc=s.fg2, fs=s.fs_s, ha="center")
    txt(ax, s, 50, 8, "T-11  ·  CHK-04  ·  Phase 0 Design Artefact", fc=s.ann, fs=s.fs_xs, ha="center")
    return fig


def panel_main_regular(s: S):
    fig, ax = new_page(s, "Main Window — Regular Mode")
    cy1 = WY1 - TBH - NAVH   # top of content = 59

    # ── Toolbar row 1 (device + meter + rec + mode)  y: cy1-5 to cy1
    row1y = cy1 - 5
    txt(ax, s, WX0 + 2, cy1 - 2.5, "Input:", fc=s.fg2, fs=s.fs_s)
    ddl(ax, s, WX0 + 8, row1y + 0.5, 22, 3.5, "Microphone (Realtek HD)")
    tag(ax, s, WX0 + 8 + 11 - 1, row1y + 0.5 + 1.75 + 1.3, 1)
    # signal meter
    signal_meter(ax, s, WX0 + 32, row1y + 1.0, 12, 2.5)
    tag(ax, s, WX0 + 32 + 6, row1y + 1.0 + 2.5 + 1.2, 2)
    # recording indicator
    c = Circle((WX0 + 50, row1y + 2.25), 1.5, color=s.acc, zorder=5)
    ax.add_patch(c)
    txt(ax, s, WX0 + 52.5, row1y + 2.25, "REC", fc=s.acc, fs=s.fs_s, bold=True)
    tag(ax, s, WX0 + 50, row1y + 2.25 + 2.8, 3)
    # mode toggle
    txt(ax, s, WX0 + 58, row1y + 2.25, "Mode:", fc=s.fg2, fs=s.fs_s)
    btn(ax, s, WX0 + 64, row1y + 0.5, 10, 3.5, "● Regular", "pri")
    btn(ax, s, WX0 + 75, row1y + 0.5, 14, 3.5, "Short Session", "sec")
    tag(ax, s, WX0 + 74, row1y + 0.5 + 1.75 + 1.3, 4)
    hline(ax, s, row1y)

    # ── Toolbar row 2 (group selector)  y: row1y-4 to row1y
    row2y = row1y - 4
    txt(ax, s, WX0 + 2, row2y + 2, "Speaker Group:", fc=s.fg2, fs=s.fs_s)
    ddl(ax, s, WX0 + 18, row2y + 0.4, 22, 3.0, "Group 1")
    tag(ax, s, WX0 + 18 + 11, row2y + 0.4 + 1.5 + 1.2, 5)
    hline(ax, s, row2y)

    # ── Progress bars  y: row2y-6 to row2y
    row3y = row2y - 6
    txt(ax, s, WX0 + 2, row3y + 5, "File:", fc=s.fg2, fs=s.fs_s)
    prog(ax, s, WX0 + 8, row3y + 3.5, 60, 2.8, 0.45, "45%")
    tag(ax, s, WX0 + 38 + 4, row3y + 3.5 + 1.4 + 1.2, 6)
    txt(ax, s, WX0 + 2, row3y + 1.5, "Queue:", fc=s.fg2, fs=s.fs_s)
    prog(ax, s, WX0 + 8, row3y + 0.2, 60, 2.0, 0.2, "1 / 5 files")
    tag(ax, s, WX0 + 38 + 4, row3y + 0.2 + 1.0 + 1.2, 7)
    hline(ax, s, row3y)

    # ── Transcript area  y: CY0+6 to row3y
    ta_y0 = CY0 + 6
    ta_h = row3y - ta_y0
    box(ax, s, WX0 + 1, ta_y0, WX1 - WX0 - 2, ta_h, fc=s.inp, ec=s.bdr)
    tag(ax, s, WX0 + 1 + (WX1 - WX0 - 2) / 2, ta_y0 + ta_h - 2, 8)
    # sample segments
    segs = [
        ("Speaker 1", "00:00:01,500 – 00:00:05,200", "Hello, my name is John Smith. How are you today?"),
        ("Speaker 2", "00:00:06,000 – 00:00:09,800", "I'm doing well, thank you. Let's discuss the agenda."),
        ("Speaker 1", "00:00:10,500 – 00:00:14,000", "Sure. First item: project status update…"),
    ]
    for i, (spk, ts, line) in enumerate(segs):
        sy = ta_y0 + ta_h - 4 - i * 6
        if sy < ta_y0 + 1:
            break
        txt(ax, s, WX0 + 2.5, sy + 1.8, spk, fc=s.pri, fs=s.fs_s, bold=True)
        txt(ax, s, WX0 + 2.5, sy - 0.2, ts, fc=s.fg2, fs=s.fs_xs)
        txt(ax, s, WX0 + 2.5, sy - 2.2, line, fc=s.fg, fs=s.fs_s)
        if i < len(segs) - 1:
            hline(ax, s, sy - 3.5, WX0 + 1, WX1 - 1)

    # ── Playback bar  y: CY0 to CY0+5.5
    pb_y = CY0
    hline(ax, s, pb_y + 5.5)
    btn(ax, s, WX0 + 2, pb_y + 1, 6, 3.5, "▶ Play", "sec")
    tag(ax, s, WX0 + 5, pb_y + 1 + 1.75 + 1.2, 9)
    # seek bar
    box(ax, s, WX0 + 10, pb_y + 2.2, 65, 1.2, fc=s.li, ec=s.bdr, r=0)
    ax.add_patch(Rectangle((WX0 + 10, pb_y + 2.2), 30, 1.2, facecolor=s.pri, edgecolor="none", zorder=3))
    c2 = Circle((WX0 + 40, pb_y + 2.8), 0.9, color=s.pri, zorder=6)
    ax.add_patch(c2)
    tag(ax, s, WX0 + 42, pb_y + 2.8 + 2.0, 10)
    txt(ax, s, WX0 + 77, pb_y + 2.8, "01:23 / 05:47", fc=s.fg2, fs=s.fs_s)
    tag(ax, s, WX0 + 84, pb_y + 2.8 + 1.8, 11)

    legend_row(ax, s, [
        (1, "Device Dropdown"), (2, "Signal Meter"), (3, "Record Indicator"),
        (4, "Mode Toggle"), (5, "Group Selector"), (6, "File Progress"),
        (7, "Queue Progress"), (8, "Transcript Area"), (9, "Playback Control"),
        (10, "Seek Slider"), (11, "Timestamp"),
    ])
    return fig


def panel_main_short(s: S):
    fig, ax = new_page(s, "Main Window — Short Session Mode (Amendment)")
    cy1 = WY1 - TBH - NAVH

    # Same toolbars as regular (compact)
    row1y = cy1 - 4.5
    txt(ax, s, WX0 + 2, row1y + 2, "Input:", fc=s.fg2, fs=s.fs_s)
    ddl(ax, s, WX0 + 8, row1y + 0.3, 22, 3.5, "Microphone (Realtek HD)")
    signal_meter(ax, s, WX0 + 32, row1y + 0.8, 10, 2.0)
    c = Circle((WX0 + 47, row1y + 2), 1.5, color=s.ok, zorder=5)
    ax.add_patch(c)
    txt(ax, s, WX0 + 50, row1y + 2, "READY", fc=s.ok, fs=s.fs_s, bold=True)
    btn(ax, s, WX0 + 64, row1y + 0.3, 10, 3.5, "Regular", "sec")
    btn(ax, s, WX0 + 75, row1y + 0.3, 14, 3.5, "● Short Session", "pri")
    tag(ax, s, WX0 + 82, row1y + 0.3 + 1.75 + 1.2, 1)
    hline(ax, s, row1y)
    row2y = row1y - 4
    txt(ax, s, WX0 + 2, row2y + 2, "Speaker Group:", fc=s.fg2, fs=s.fs_s)
    ddl(ax, s, WX0 + 18, row2y + 0.4, 22, 3.0, "Group 1")
    hline(ax, s, row2y)

    # ── Two-field form  ────────────────────────────────────────────────────────
    form_top = row2y - 1.5
    form_bot = CY0 + 1.5
    field_h = (form_top - form_bot - 4) / 2  # ~2 equal fields with gap

    # Field 1 — Transcription
    f1y = form_top - field_h
    txt(ax, s, WX0 + 2, form_top - 1, "Transcription", fc=s.sec, fs=s.fs_s, bold=True)
    box(ax, s, WX0 + 1, f1y, WX1 - WX0 - 16, field_h, fc=s.inp, ec=s.bdr)
    tag(ax, s, WX0 + 1 + (WX1 - WX0 - 16) / 2, f1y + field_h - 1.5, 2)
    sample_t = "Hello, this is the transcribed speech text.\nIt appears here after recording completes."
    txt(ax, s, WX0 + 2.5, f1y + field_h - 2.5, sample_t, fc=s.fg, fs=s.fs_s)
    # Translate & copy button
    btn(ax, s, WX1 - 14, f1y + field_h / 2 - 2, 13, 4.0, "Translate &\nCopy", "pri")
    tag(ax, s, WX1 - 14 + 6.5, f1y + field_h / 2 - 2 + 4.0 + 1.2, 3)

    gap_y = f1y - 2
    hline(ax, s, gap_y, WX0 + 1, WX1 - 1)

    # Field 2 — Translation
    f2y = form_bot
    txt(ax, s, WX0 + 2, f2y + field_h + 0.5, "Translation", fc=s.sec, fs=s.fs_s, bold=True)
    box(ax, s, WX0 + 1, f2y, WX1 - WX0 - 16, field_h, fc=s.inp, ec=s.bdr)
    tag(ax, s, WX0 + 1 + (WX1 - WX0 - 16) / 2, f2y + field_h - 1.5, 4)
    sample_tr = "Tässä on käännetty teksti.\nSe näkyy tässä käännöksen jälkeen."
    txt(ax, s, WX0 + 2.5, f2y + field_h - 2.5, sample_tr, fc=s.fg, fs=s.fs_s)
    btn(ax, s, WX1 - 14, f2y + field_h / 2 - 1.5, 13, 3.5, "Save to\nClipboard", "sec")
    tag(ax, s, WX1 - 14 + 6.5, f2y + field_h / 2 - 1.5 + 3.5 + 1.2, 5)

    # Disabled-translation note
    txt(ax, s, WX0 + 2, form_bot - 0.8,
        "⚠  When translation is disabled: field 2 and its button are hidden; field 1 expands; button label changes to \"Copy to clipboard\"",
        fc=s.warn, fs=s.fs_xs)

    legend_row(ax, s, [
        (1, "Mode Toggle (Short Session)"), (2, "Transcription Field"),
        (3, "Translate & Copy Button"), (4, "Translation Field"),
        (5, "Save to Clipboard Button"),
    ])
    return fig


def panel_settings(s: S):
    fig, ax = new_page(s, "Settings")
    cy1 = WY1 - TBH - NAVH

    # Sidebar
    sb_w = 20
    box(ax, s, WX0, CY0, sb_w, cy1 - CY0, fc=s.sidebar, ec=s.bdr)
    cats = ["Audio & Input", "Transcription", "Translation", "Output", "Advanced", "About"]
    for i, c in enumerate(cats):
        ry = cy1 - 4 - i * 5
        if i == 1:  # selected
            ax.add_patch(Rectangle((WX0, ry), sb_w, 4.5, facecolor=s.ls, edgecolor="none", zorder=3))
        txt(ax, s, WX0 + 3, ry + 2.2, c, fc=s.pri if i == 1 else s.fg, fs=s.fs_s,
            bold=(i == 1))
    vline(ax, s, WX0 + sb_w, CY0, cy1)

    # Content area
    cx = WX0 + sb_w + 2
    cw = WX1 - cx - 1

    txt(ax, s, cx, cy1 - 3, "Transcription", fc=s.fg, fs=s.fs_h, bold=True)
    hline(ax, s, cy1 - 4.5, cx, WX1 - 1)

    rows = [
        ("Source Language", "ddl", "Finnish"),
        ("Target Language", "ddl", "English"),
        ("Whisper Model", "ddl", "Medium (recommended)"),
        ("Bad Audio Threshold", "slider", "0.6"),
        ("Min Voice Profile Samples", "inp", "10"),
    ]
    for i, (lbl, kind, val) in enumerate(rows):
        ry = cy1 - 7 - i * 6
        txt(ax, s, cx, ry + 2, lbl, fc=s.fg2, fs=s.fs_s)
        tag(ax, s, cx + cw / 2 - 1, ry + 2 + 1.2, i + 1)
        if kind == "ddl":
            ddl(ax, s, cx + cw * 0.42, ry + 0.3, cw * 0.56, 3.5, val)
        elif kind == "slider":
            box(ax, s, cx + cw * 0.42, ry + 1.2, cw * 0.56, 1.5, fc=s.li, ec=s.bdr, r=0)
            ax.add_patch(Rectangle((cx + cw * 0.42, ry + 1.2), cw * 0.56 * 0.6, 1.5,
                                   facecolor=s.pri, edgecolor="none", zorder=3))
            c = Circle((cx + cw * 0.42 + cw * 0.56 * 0.6, ry + 1.95), 0.8, color=s.pri, zorder=6)
            ax.add_patch(c)
            txt(ax, s, cx + cw * 0.42 + cw * 0.56 + 1, ry + 1.95, val, fc=s.fg, fs=s.fs_s)
        else:
            inp(ax, s, cx + cw * 0.42, ry + 0.3, cw * 0.56, 3.5, val, val)

    # toggles section
    ty = cy1 - 7 - len(rows) * 6 - 2
    txt(ax, s, cx, ty, "Options", fc=s.fg, fs=s.fs_h, bold=True)
    hline(ax, s, ty - 1.2, cx, WX1 - 1)
    tog(ax, s, cx, ty - 5.5, True, "Enable translation by default")
    tag(ax, s, cx + 5 + 1.0, ty - 5.5 + 2.2 + 1.2, 6)
    tog(ax, s, cx + 40, ty - 5.5, False, "Auto-start with Windows")
    tag(ax, s, cx + 40 + 5 + 1.0, ty - 5.5 + 2.2 + 1.2, 7)

    # HF licence
    hy = ty - 11
    box(ax, s, cx, hy, cw - 1, 6.5, fc=s.li, ec=s.bdr)
    txt(ax, s, cx + 1.5, hy + 5, "HuggingFace Licence", fc=s.fg, fs=s.fs_s, bold=True)
    txt(ax, s, cx + 1.5, hy + 3, "pyannote.audio requires licence acceptance for speaker diarization.",
        fc=s.fg2, fs=s.fs_xs)
    txt(ax, s, cx + 1.5, hy + 1.5, "Status: ✗ Not accepted", fc=s.acc, fs=s.fs_xs, bold=True)
    btn(ax, s, cx + cw - 20, hy + 0.8, 18, 3.0, "Open HuggingFace Licence", "ghost")
    tag(ax, s, cx + cw - 20 + 9, hy + 0.8 + 1.5 + 1.2, 8)

    # output folder
    oy = hy - 7
    txt(ax, s, cx, oy + 3, "Output Folder:", fc=s.fg2, fs=s.fs_s)
    inp(ax, s, cx + cw * 0.32, oy + 0.8, cw * 0.45, 3.0, "", "C:\\Users\\Leo1\\Documents\\Output")
    btn(ax, s, cx + cw * 0.32 + cw * 0.45 + 0.5, oy + 0.8, 8, 3.0, "Browse…", "sec")
    tag(ax, s, cx + cw * 0.32 + cw * 0.45 / 2, oy + 0.8 + 1.5 + 1.2, 9)

    legend_row(ax, s, [
        (1, "Source Language"), (2, "Target Language"), (3, "Whisper Model"),
        (4, "Bad Audio Threshold"), (5, "Min Profile Samples"), (6, "Translation Toggle"),
        (7, "Auto-Start Toggle"), (8, "HuggingFace Licence"), (9, "Output Folder"),
    ])
    return fig


def panel_voice_profiles(s: S):
    fig, ax = new_page(s, "Voice Profile Management")
    cy1 = WY1 - TBH - NAVH
    ch = cy1 - CY0

    # Left: speaker list (35% width)
    lw = (WX1 - WX0) * 0.35
    txt(ax, s, WX0 + 2, cy1 - 2, "Speakers", fc=s.fg, fs=s.fs_b, bold=True)
    tag(ax, s, WX0 + 2 + 7, cy1 - 2 + 1.2, 1)
    speakers = ["Jane Doe", "John Smith", "Unknown Speaker #001",
                "Maria Garcia", "Tanaka Hiroshi"]
    lstbox(ax, s, WX0 + 1, CY0 + 10, lw - 2, ch - 14, speakers, sel=1)
    # action buttons under list
    btn(ax, s, WX0 + 1, CY0 + 6.5, (lw - 2) / 3 - 0.5, 3.2, "+ Add", "pri")
    btn(ax, s, WX0 + 1 + (lw - 2) / 3, CY0 + 6.5, (lw - 2) / 3 - 0.5, 3.2, "Rename", "sec")
    btn(ax, s, WX0 + 1 + (lw - 2) * 2 / 3, CY0 + 6.5, (lw - 2) / 3 - 0.5, 3.2, "Delete", "danger")
    tag(ax, s, WX0 + 1 + (lw - 2) / 6, CY0 + 6.5 + 1.6 + 1.2, 2)
    btn(ax, s, WX0 + 1, CY0 + 1.5, (lw - 2) / 2 - 0.5, 3.2, "Import", "sec")
    btn(ax, s, WX0 + 1 + (lw - 2) / 2, CY0 + 1.5, (lw - 2) / 2 - 0.5, 3.2, "Export", "sec")
    tag(ax, s, WX0 + 1 + (lw - 2) / 4, CY0 + 1.5 + 1.6 + 1.2, 3)
    vline(ax, s, WX0 + lw, CY0, cy1)

    # Middle: groups (30% width)
    mw = (WX1 - WX0) * 0.30
    mx = WX0 + lw + 1
    txt(ax, s, mx + 1, cy1 - 2, "Groups", fc=s.fg, fs=s.fs_b, bold=True)
    tag(ax, s, mx + 1 + 5.5, cy1 - 2 + 1.2, 4)
    groups = ["Group 1 (All)", "Interview Set A", "Meeting Participants", "Personal"]
    lstbox(ax, s, mx, CY0 + 10, mw - 2, ch - 14, groups, sel=2)
    btn(ax, s, mx, CY0 + 6.5, (mw - 2) / 2 - 0.5, 3.2, "+ Add Group", "pri")
    btn(ax, s, mx + (mw - 2) / 2, CY0 + 6.5, (mw - 2) / 2 - 0.5, 3.2, "Rename", "sec")
    tag(ax, s, mx + (mw - 2) / 4, CY0 + 6.5 + 1.6 + 1.2, 5)
    vline(ax, s, mx + mw - 1, CY0, cy1)

    # Right: speaker detail (35% width)
    rx = mx + mw
    rw = WX1 - rx - 1
    txt(ax, s, rx + 1, cy1 - 2, "John Smith", fc=s.pri, fs=s.fs_b, bold=True)
    # avatar placeholder
    c = Circle((rx + rw / 2, cy1 - 9), 5, facecolor=s.li, edgecolor=s.bdr, linewidth=s.lw, zorder=3)
    ax.add_patch(c)
    txt(ax, s, rx + rw / 2, cy1 - 9, "JS", fc=s.sec, fs=12, ha="center", bold=True)
    tag(ax, s, rx + rw / 2, cy1 - 9 + 5 + 1.2, 6)
    fields = [("First Name", "John"), ("Last Name", "Smith"), ("Organisation", "Acme Corp"),
              ("Position", "Engineer"), ("Note", "")]
    for i, (lbl, val) in enumerate(fields):
        fy = cy1 - 20 - i * 5.5
        txt(ax, s, rx + 1, fy + 1.8, lbl, fc=s.fg2, fs=s.fs_xs)
        inp(ax, s, rx + 1, fy - 1.0, rw - 2, 2.8, lbl, val)
        tag(ax, s, rx + 1 + rw / 2, fy - 1.0 + 1.4 + 1.2, 7 + i)
    # group membership
    gy = cy1 - 50
    txt(ax, s, rx + 1, gy, "Member of:", fc=s.fg2, fs=s.fs_xs, bold=True)
    for j, g in enumerate(["Group 1 (All)", "Interview Set A"]):
        box(ax, s, rx + 1, gy - 4 - j * 4, rw - 2, 3.0, fc=s.ls, ec=s.pri)
        txt(ax, s, rx + 2, gy - 4 + 1.5 - j * 4, g, fc=s.pri, fs=s.fs_xs)
    txt(ax, s, rx + 1, CY0 + 1, "Drag speaker onto group to assign membership",
        fc=s.fg2, fs=s.fs_xs)

    legend_row(ax, s, [
        (1, "Speaker List"), (2, "Speaker Actions"), (3, "Import / Export"),
        (4, "Group List"), (5, "Group Actions"), (6, "Speaker Avatar"),
        (7, "First Name"), (8, "Last Name"), (9, "Organisation"), (10, "Group Membership"),
    ])
    return fig


def panel_dictionary(s: S):
    fig, ax = new_page(s, "Substitution Dictionary")
    cy1 = WY1 - TBH - NAVH

    # Toolbar
    toolbar_y = cy1 - 5.5
    btn(ax, s, WX0 + 2, toolbar_y + 0.5, 10, 4.0, "+ Add Row", "pri")
    tag(ax, s, WX0 + 7, toolbar_y + 0.5 + 2 + 1.2, 1)
    btn(ax, s, WX0 + 14, toolbar_y + 0.5, 10, 4.0, "Edit", "sec")
    tag(ax, s, WX0 + 19, toolbar_y + 0.5 + 2 + 1.2, 2)
    btn(ax, s, WX0 + 26, toolbar_y + 0.5, 10, 4.0, "Delete", "danger")
    tag(ax, s, WX0 + 31, toolbar_y + 0.5 + 2 + 1.2, 3)
    inp(ax, s, WX0 + 45, toolbar_y + 0.7, 25, 3.5, "[Search...]")
    tag(ax, s, WX0 + 57.5, toolbar_y + 0.7 + 1.75 + 1.2, 4)
    btn(ax, s, WX0 + 72, toolbar_y + 0.5, 10, 4.0, "Import CSV", "sec")
    tag(ax, s, WX0 + 77, toolbar_y + 0.5 + 2 + 1.2, 5)
    btn(ax, s, WX0 + 84, toolbar_y + 0.5, 10, 4.0, "Export CSV", "sec")
    tag(ax, s, WX0 + 89, toolbar_y + 0.5 + 2 + 1.2, 6)
    hline(ax, s, toolbar_y)

    # Undo/redo
    ur_y = toolbar_y - 5
    btn(ax, s, WX0 + 2, ur_y + 0.5, 8, 3.5, "↩ Undo", "ghost")
    btn(ax, s, WX0 + 12, ur_y + 0.5, 8, 3.5, "↪ Redo", "ghost")
    tag(ax, s, WX0 + 6, ur_y + 0.5 + 1.75 + 1.2, 7)
    hline(ax, s, ur_y)

    # Table
    tbl_y = ur_y
    tbl_w = WX1 - WX0 - 2
    col_w = [tbl_w * 0.08, tbl_w * 0.40, tbl_w * 0.40, tbl_w * 0.12]
    headers = ["#", "Source Term", "Replacement", "Flags"]
    # header row
    hdr_h = 4
    box(ax, s, WX0 + 1, tbl_y - hdr_h, tbl_w, hdr_h, fc=s.sidebar, ec=s.bdr)
    cx_off = WX0 + 1
    for i, (h, cw) in enumerate(zip(headers, col_w)):
        txt(ax, s, cx_off + 1, tbl_y - hdr_h + 2, h, fc=s.fg, fs=s.fs_s, bold=True)
        tag(ax, s, cx_off + 1 + cw / 2 - 1, tbl_y - hdr_h + 4 + 1.2, 8 + i)
        cx_off += cw
        if i < len(col_w) - 1:
            vline(ax, s, cx_off, tbl_y - hdr_h, tbl_y)
    rows_data = [
        ("1", "recognise", "recognize", "case-insensitive"),
        ("2", "colour", "color", "whole-word"),
        ("3", "tech*", "technology", "wildcard"),
        ("4", "Dr.", "Doctor", ""),
    ]
    row_h = 4.5
    for j, row in enumerate(rows_data):
        ry = tbl_y - hdr_h - (j + 1) * row_h
        fc = s.ls if j == 1 else (s.li if j % 2 == 1 else "none")
        if fc != "none":
            ax.add_patch(Rectangle((WX0 + 1, ry), tbl_w, row_h, facecolor=fc, edgecolor="none", zorder=2))
        cx_off = WX0 + 1
        for k, (cell, cw) in enumerate(zip(row, col_w)):
            txt(ax, s, cx_off + 1, ry + row_h / 2, cell, fc=s.fg if k > 0 else s.fg2, fs=s.fs_s)
            cx_off += cw
        hline(ax, s, ry, WX0 + 1, WX1 - 1)
        if j == 1:
            tag(ax, s, WX0 + 1 + tbl_w / 2, ry + row_h / 2 + 2.0, 12)

    legend_row(ax, s, [
        (1, "Add Row"), (2, "Edit Row"), (3, "Delete Row"), (4, "Search Box"),
        (5, "Import CSV"), (6, "Export CSV"), (7, "Undo / Redo"),
        (8, "Row Number Col"), (9, "Source Term Col"), (10, "Replacement Col"), (12, "Selected Row"),
    ])
    return fig


def panel_batch(s: S):
    fig, ax = new_page(s, "Batch Queue")
    cy1 = WY1 - TBH - NAVH

    # Left: file list (65%)
    lw = (WX1 - WX0) * 0.65
    txt(ax, s, WX0 + 2, cy1 - 2, "Queue", fc=s.fg, fs=s.fs_b, bold=True)
    # column headers
    hdr_y = cy1 - 6
    cols = [("File Name", 0.40), ("Duration", 0.12), ("Status", 0.15), ("Progress", 0.33)]
    cx_off = WX0 + 1
    box(ax, s, WX0 + 1, hdr_y - 3.5, lw - 2, 3.5, fc=s.sidebar, ec=s.bdr)
    for hdr, cw_frac in cols:
        cw = (lw - 3) * cw_frac
        txt(ax, s, cx_off + 1, hdr_y - 1.8, hdr, fc=s.fg2, fs=s.fs_s, bold=True)
        cx_off += cw
    # file rows
    files = [
        ("interview_2026_05.mp3", "12:34", "Processing", 0.45),
        ("meeting_notes.wav", "08:20", "Pending", 0.0),
        ("lecture_pt1.mp4", "45:02", "Done", 1.0),
        ("lecture_pt2.mp4", "38:17", "Error", 0.0),
        ("Q1_review.mp3", "22:45", "Pending", 0.0),
    ]
    status_col = {"Processing": s.warn, "Pending": s.fg2, "Done": s.ok, "Error": s.acc}
    row_h = 4.5
    for j, (name, dur, status, pval) in enumerate(files):
        ry = hdr_y - 3.5 - (j + 1) * row_h
        if ry < CY0 + 6:
            break
        fc = s.ls if j == 0 else (s.li if j % 2 == 1 else "none")
        if fc != "none":
            ax.add_patch(Rectangle((WX0 + 1, ry), lw - 2, row_h, facecolor=fc, edgecolor="none", zorder=2))
        cx_off = WX0 + 1
        for cell, cw_frac in zip([name, dur, status, ""], cols):
            cw = (lw - 3) * cw_frac[1]
            if cell == status:
                txt(ax, s, cx_off + 1, ry + row_h / 2, cell, fc=status_col.get(status, s.fg), fs=s.fs_s, bold=True)
            elif cell == "":
                if pval > 0:
                    prog(ax, s, cx_off + 0.5, ry + row_h / 2 - 0.7, cw - 2, 1.8, pval)
                    tag(ax, s, cx_off + 0.5 + cw / 2, ry + row_h / 2 + 1.5 + 1.0, 4)
            else:
                txt(ax, s, cx_off + 1, ry + row_h / 2, cell, fc=s.fg, fs=s.fs_s)
            cx_off += cw
        if j == 1:
            tag(ax, s, WX0 + 1 + lw / 2, ry + row_h / 2 + 2.0, 1)
        hline(ax, s, ry, WX0 + 1, WX0 + lw - 1)
    tag(ax, s, WX0 + 1 + lw / 4, cy1 - 6, 2)
    vline(ax, s, WX0 + lw, CY0, cy1)

    # Right: controls
    rx = WX0 + lw + 1
    rw = WX1 - rx - 1
    txt(ax, s, rx + 1, cy1 - 2, "Actions", fc=s.fg, fs=s.fs_b, bold=True)
    actions = [("Add Files…", "pri"), ("Remove Selected", "sec"), ("Clear Queue", "sec"),
               ("▶ Start", "ok"), ("■ Stop", "danger")]
    for i, (lbl, kind) in enumerate(actions):
        btn(ax, s, rx + 1, cy1 - 7 - i * 6, rw - 2, 4.5, lbl, kind)
        tag(ax, s, rx + 1 + (rw - 2) / 2, cy1 - 7 - i * 6 + 4.5 + 1.2, 5 + i)

    legend_row(ax, s, [
        (1, "Queue Row"), (2, "Column Headers"), (3, "Status Indicator"),
        (4, "Per-file Progress"), (5, "Add Files"), (6, "Remove Selected"),
        (7, "Clear Queue"), (8, "Start Processing"), (9, "Stop Processing"),
    ])
    return fig


def panel_output_config(s: S):
    fig, ax = new_page(s, "Output Content Configuration")
    cy1 = WY1 - TBH - NAVH

    mid = (WX0 + WX1) / 2
    col_w = (WX1 - WX0 - 4) / 2

    # Left column: field toggles
    txt(ax, s, WX0 + 2, cy1 - 2, "Include in output", fc=s.fg, fs=s.fs_b, bold=True)
    hline(ax, s, cy1 - 4, WX0 + 1, mid - 1)
    toggles = [
        ("Speaker Name", True), ("Timestamps", True), ("Transcription Confidence", False),
        ("Language Label", False), ("Translated Text", True), ("Bad Audio Marker", True),
    ]
    for i, (lbl, on) in enumerate(toggles):
        ty = cy1 - 8 - i * 6.5
        tog(ax, s, WX0 + 4, ty, on, lbl)
        tag(ax, s, WX0 + 4 + 5 + 1, ty + 2.2 + 1.2, i + 1)

    # Right column: format checkboxes
    txt(ax, s, mid + 1, cy1 - 2, "Output formats", fc=s.fg, fs=s.fs_b, bold=True)
    hline(ax, s, cy1 - 4, mid, WX1 - 1)
    formats = [
        ("TXT — Plain text file", True), ("DOCX — Word document", False),
        ("SRT — Subtitle file", False), ("JSON — Machine-readable", True),
        ("Display — On screen", True), ("Clipboard — Auto-copy", False),
    ]
    for i, (lbl, checked) in enumerate(formats):
        cy = cy1 - 8 - i * 6.5
        chk(ax, s, mid + 4, cy, checked, lbl)
        tag(ax, s, mid + 4 + 3 + 1, cy + 1 + 1.2, 7 + i)

    vline(ax, s, mid, CY0 + 15, cy1)

    # Output folder picker
    fp_y = CY0 + 4
    hline(ax, s, fp_y + 9, WX0 + 1, WX1 - 1)
    txt(ax, s, WX0 + 2, fp_y + 7, "Output Folder:", fc=s.fg2, fs=s.fs_s, bold=True)
    inp(ax, s, WX0 + 2, fp_y + 3, (WX1 - WX0 - 14), 3.5, "", "C:\\Users\\Leo1\\Documents\\Output")
    tag(ax, s, WX0 + 2 + (WX1 - WX0 - 14) / 2, fp_y + 3 + 1.75 + 1.2, 13)
    btn(ax, s, WX1 - 11, fp_y + 3, 10, 3.5, "Browse…", "sec")

    legend_row(ax, s, [
        (1, "Speaker Name Toggle"), (2, "Timestamps Toggle"), (3, "Confidence Toggle"),
        (4, "Language Label Toggle"), (5, "Translation Toggle"), (6, "Bad Audio Toggle"),
        (7, "TXT Format"), (8, "DOCX Format"), (9, "SRT Format"), (10, "JSON Format"),
        (11, "Display Format"), (12, "Clipboard Format"), (13, "Output Folder"),
    ])
    return fig


def panel_hotkeys(s: S):
    fig, ax = new_page(s, "Hotkey Configuration")
    cy1 = WY1 - TBH - NAVH

    txt(ax, s, WX0 + 3, cy1 - 2, "Global Hotkeys", fc=s.fg, fs=s.fs_b, bold=True)
    txt(ax, s, WX0 + 3, cy1 - 5,
        "Click a key binding field, then press the desired key combination. ⚠ conflicts are highlighted.",
        fc=s.fg2, fs=s.fs_s)
    hline(ax, s, cy1 - 7)

    actions = [
        ("Start Recording", "Ctrl + Shift + S", False),
        ("Stop Recording", "Ctrl + Shift + X", False),
        ("Push-to-Talk (hold)", "F9", False),
        ("Cancel Recording", "Ctrl + Shift + C", False),
        ("Open / Show Window", "Ctrl + Shift + W", True),
        ("Short Session Start", "Ctrl + Shift + Q", False),
    ]
    row_h = 6.5
    # headers
    hdr_y = cy1 - 9
    txt(ax, s, WX0 + 3, hdr_y, "Action", fc=s.sec, fs=s.fs_s, bold=True)
    txt(ax, s, WX0 + 52, hdr_y, "Key Binding", fc=s.sec, fs=s.fs_s, bold=True)
    txt(ax, s, WX0 + 80, hdr_y, "Status", fc=s.sec, fs=s.fs_s, bold=True)
    hline(ax, s, hdr_y - 1.5)
    for i, (action, key, conflict) in enumerate(actions):
        ry = hdr_y - 1.5 - (i + 1) * row_h
        if i % 2 == 1:
            ax.add_patch(Rectangle((WX0 + 1, ry), WX1 - WX0 - 2, row_h, facecolor=s.li, edgecolor="none", zorder=2))
        txt(ax, s, WX0 + 3, ry + row_h / 2, action, fc=s.fg, fs=s.fs_s)
        # key capture field
        bfc = "#FFF3CD" if conflict else s.inp  # yellow if conflict
        bec = s.warn if conflict else s.bdr
        box(ax, s, WX0 + 50, ry + 1, 28, 4.2, fc=bfc, ec=bec)
        txt(ax, s, WX0 + 64, ry + 3.1, key, fc=s.fg, fs=s.fs_s, ha="center", mono=True)
        tag(ax, s, WX0 + 50 + 14, ry + 1 + 2.1 + 1.2, i + 1)
        if conflict:
            txt(ax, s, WX0 + 80, ry + row_h / 2, "⚠ Conflict", fc=s.warn, fs=s.fs_s, bold=True)
            tag(ax, s, WX0 + 90, ry + row_h / 2 + 1.5, 7)
        else:
            txt(ax, s, WX0 + 80, ry + row_h / 2, "✓ OK", fc=s.ok, fs=s.fs_s)
        hline(ax, s, ry, WX0 + 1, WX1 - 1)

    # Save / Reset
    save_y = hdr_y - 1.5 - len(actions) * row_h - 3
    btn(ax, s, WX0 + 3, save_y, 15, 4.5, "Save Changes", "pri")
    btn(ax, s, WX0 + 20, save_y, 15, 4.5, "Reset Defaults", "sec")
    tag(ax, s, WX0 + 10, save_y + 4.5 + 1.2, 8)

    legend_row(ax, s, [
        (1, "Start Recording Key"), (2, "Stop Recording Key"), (3, "Push-to-Talk Key"),
        (4, "Cancel Recording Key"), (5, "Open Window Key"), (6, "Short Session Key"),
        (7, "Conflict Warning"), (8, "Save / Reset"),
    ])
    return fig


def panel_labelling(s: S):
    fig, ax = new_page(s, "Speaker Labelling Prompt")
    cy1 = WY1 - TBH - NAVH

    txt(ax, s, WX0 + 3, cy1 - 2,
        "Identify this speaker — or Skip to label later", fc=s.fg, fs=s.fs_b, bold=True)
    hline(ax, s, cy1 - 4)

    # Waveform + player (top 30%)
    wave_y = cy1 - 4 - 16
    box(ax, s, WX0 + 2, wave_y, WX1 - WX0 - 4, 14, fc=s.inp, ec=s.bdr)
    tag(ax, s, (WX0 + WX1) / 2, wave_y + 14 + 1.2, 1)
    # fake waveform
    np.random.seed(3)
    xs = np.linspace(WX0 + 4, WX1 - 4, 200)
    ys = wave_y + 7 + np.random.randn(200) * 3.0
    ax.plot(xs, ys, color=s.pri, linewidth=0.5, zorder=4)
    # start/end markers
    for mx, label, n in [(WX0 + 20, "▼ Start (5.0s)", 2), (WX0 + 60, "▼ End (15.0s)", 3)]:
        ax.add_line(Line2D([mx, mx], [wave_y, wave_y + 14], color=s.acc, linewidth=1.0, linestyle="--", zorder=5))
        txt(ax, s, mx, wave_y + 14.5, label, fc=s.acc, fs=s.fs_xs, ha="center")
        tag(ax, s, mx, wave_y - 1.5, n)
    # player controls
    pc_y = wave_y - 5.5
    btn(ax, s, WX0 + 2, pc_y, 14, 3.5, "▶ Play Fragment", "pri")
    tag(ax, s, WX0 + 9, pc_y + 3.5 + 1.2, 4)
    prog(ax, s, WX0 + 18, pc_y + 1.0, 50, 1.5, 0.38, "")
    txt(ax, s, WX0 + 70, pc_y + 1.75, "03.8s / 10.0s", fc=s.fg2, fs=s.fs_xs)

    # Metadata form (below player)
    form_y = pc_y - 2
    form_fields = [
        ("Last Name *", "Smith"), ("First Name *", "John"), ("Middle Name", ""),
        ("Nickname", ""), ("Organisation", "Acme Corp"), ("Position", "Engineer"),
        ("Note", ""),
    ]
    cols = 2
    fld_w = (WX1 - WX0 - 6) / cols
    for i, (lbl, val) in enumerate(form_fields):
        col = i % cols
        row = i // cols
        fx = WX0 + 3 + col * fld_w
        fy = form_y - row * 7
        txt(ax, s, fx, fy, lbl, fc=s.fg2, fs=s.fs_xs)
        inp(ax, s, fx, fy - 3.2, fld_w - 2, 3.0, lbl.replace(" *", ""), val)
        tag(ax, s, fx + fld_w / 2, fy - 3.2 + 1.5 + 1.2, 5 + i)

    # Buttons
    btn_y = CY0 + 1
    btn(ax, s, WX0 + 3, btn_y, 15, 4.5, "✓  Save Profile", "pri")
    tag(ax, s, WX0 + 10, btn_y + 4.5 + 1.2, 12)
    btn(ax, s, WX0 + 20, btn_y, 10, 4.5, "Skip →", "sec")
    tag(ax, s, WX0 + 25, btn_y + 4.5 + 1.2, 13)
    btn(ax, s, WX0 + 32, btn_y, 8, 4.5, "↩", "ghost")
    btn(ax, s, WX0 + 42, btn_y, 8, 4.5, "↪", "ghost")
    tag(ax, s, WX0 + 36, btn_y + 4.5 + 1.2, 14)

    legend_row(ax, s, [
        (1, "Waveform Display"), (2, "Start Marker"), (3, "End Marker"),
        (4, "Play Fragment"), (5, "Last Name"), (6, "First Name"), (7, "Middle Name"),
        (8, "Nickname"), (9, "Organisation"), (10, "Position"), (11, "Note"),
        (12, "Save Profile"), (13, "Skip"), (14, "Undo / Redo"),
    ])
    return fig


def panel_history(s: S):
    fig, ax = new_page(s, "Session History")
    cy1 = WY1 - TBH - NAVH
    lw = (WX1 - WX0) * 0.42

    # Left: session list
    txt(ax, s, WX0 + 2, cy1 - 2, "Sessions", fc=s.fg, fs=s.fs_b, bold=True)
    inp(ax, s, WX0 + 2, cy1 - 6.5, lw - 4, 3.5, "[Filter sessions...]")
    tag(ax, s, WX0 + 2 + (lw - 4) / 2, cy1 - 6.5 + 1.75 + 1.2, 1)
    sessions = [
        ("2026-05-19  14:32", "File", "05:47", "⚠ Outdated"),
        ("2026-05-18  09:15", "Batch", "22:10", ""),
        ("2026-05-17  16:44", "Mic", "01:23", ""),
        ("2026-05-16  11:00", "File", "08:30", ""),
        ("2026-05-14  13:20", "Batch", "45:00", ""),
    ]
    row_h = 5.5
    hdr_y = cy1 - 11
    for i, (date, src, dur, warn) in enumerate(sessions):
        ry = hdr_y - i * row_h
        fc = s.ls if i == 0 else (s.li if i % 2 else "none")
        if fc != "none":
            ax.add_patch(Rectangle((WX0 + 1, ry - row_h), lw - 2, row_h, facecolor=fc, edgecolor="none", zorder=2))
        txt(ax, s, WX0 + 2.5, ry - 1.5, date, fc=s.fg, fs=s.fs_s, bold=(i == 0))
        txt(ax, s, WX0 + 2.5, ry - 3.5, f"{src}  ·  {dur}", fc=s.fg2, fs=s.fs_xs)
        if warn:
            txt(ax, s, WX0 + lw - 18, ry - 2.5, warn, fc=s.warn, fs=s.fs_xs, bold=True)
            tag(ax, s, WX0 + lw - 9, ry - 2.5 + 1.5, 2)
        if i == 0:
            tag(ax, s, WX0 + 2.5 + (lw - 4) / 2, ry - 1.5 + 1.5, 3)
        hline(ax, s, ry - row_h, WX0 + 1, WX0 + lw - 1)
    vline(ax, s, WX0 + lw, CY0, cy1)

    # Right: detail panel
    rx = WX0 + lw + 2
    rw = WX1 - rx - 1
    txt(ax, s, rx, cy1 - 2, "Session Detail", fc=s.fg, fs=s.fs_b, bold=True)
    hline(ax, s, cy1 - 4, rx, WX1 - 1)

    detail_items = [
        ("Session ID", "3f2a1b4c-5d6e-7f8a…"),
        ("Created", "2026-05-19  14:32:00 UTC"),
        ("Source Type", "File"),
        ("Source Path", "C:\\…\\interview.mp3"),
        ("Speaker Group", "Group 1"),
        ("Segments", "47"),
    ]
    for i, (lbl, val) in enumerate(detail_items):
        dy = cy1 - 7 - i * 5.5
        txt(ax, s, rx, dy + 1, lbl + ":", fc=s.fg2, fs=s.fs_xs, bold=True)
        txt(ax, s, rx, dy - 1, val, fc=s.fg, fs=s.fs_s)
        tag(ax, s, rx + rw / 2, dy + 1 + 1.2, 4 + i)

    # Output files
    of_y = cy1 - 43
    txt(ax, s, rx, of_y, "Output Files:", fc=s.fg2, fs=s.fs_xs, bold=True)
    for j, f in enumerate(["interview_WSP.txt", "interview_WSP.json"]):
        txt(ax, s, rx, of_y - 3 - j * 3.5, f"[f] {f}", fc=s.fg, fs=s.fs_xs)
    tag(ax, s, rx + rw / 2, of_y + 1.2, 10)

    # Action buttons
    btn(ax, s, rx, CY0 + 9, rw - 1, 4.5, "Regenerate Output", "pri")
    tag(ax, s, rx + (rw - 1) / 2, CY0 + 9 + 4.5 + 1.2, 11)
    btn(ax, s, rx, CY0 + 3, rw - 1, 4.5, "Delete Session", "danger")
    tag(ax, s, rx + (rw - 1) / 2, CY0 + 3 + 4.5 + 1.2, 12)

    legend_row(ax, s, [
        (1, "Session Filter"), (2, "Outdated Indicator"), (3, "Selected Session"),
        (4, "Session ID"), (5, "Created Timestamp"), (6, "Source Type"),
        (7, "Source Path"), (8, "Speaker Group"), (9, "Segment Count"),
        (10, "Output Files"), (11, "Regenerate Output"), (12, "Delete Session"),
    ])
    return fig


def panel_backup(s: S):
    fig, ax = new_page(s, "Backup and Restore")
    cy1 = WY1 - TBH - NAVH
    mid = (WX0 + WX1) / 2

    for section_x, section_w, title, n_offset in [
        (WX0 + 1, mid - WX0 - 2, "Create Backup", 0),
        (mid + 1, WX1 - mid - 2, "Restore from Backup", 5),
    ]:
        box(ax, s, section_x, CY0 + 1, section_w, cy1 - CY0 - 2, fc=s.panel, ec=s.bdr)
        section_header(ax, s, section_x, cy1 - 5, section_w, 4, title)
        if n_offset == 0:
            # Backup section
            txt(ax, s, section_x + 2, cy1 - 9, "Estimated backup size:", fc=s.fg2, fs=s.fs_s)
            txt(ax, s, section_x + 2, cy1 - 13, "3.4 GB", fc=s.pri, fs=12, bold=True)
            tag(ax, s, section_x + 10, cy1 - 13 + 2, 1)
            txt(ax, s, section_x + 2, cy1 - 16.5, "Includes: voice profiles, config, session history, dictionary",
                fc=s.fg2, fs=s.fs_xs)
            # destination picker
            txt(ax, s, section_x + 2, cy1 - 21, "Destination:", fc=s.fg2, fs=s.fs_s)
            inp(ax, s, section_x + 2, cy1 - 25, section_w - 12, 3.5, "", "C:\\Users\\Leo1\\Backups")
            tag(ax, s, section_x + 2 + (section_w - 12) / 2, cy1 - 25 + 1.75 + 1.2, 2)
            btn(ax, s, section_x + section_w - 10, cy1 - 25, 8, 3.5, "Browse…", "sec")
            # inside-folder warning
            warn_y = cy1 - 32
            box(ax, s, section_x + 2, warn_y, section_w - 4, 6, fc="#FFF9C4" if s.bg != s.win else s.li, ec=s.warn)
            txt(ax, s, section_x + 3, warn_y + 4, "⚠  Warning", fc=s.warn, fs=s.fs_s, bold=True)
            txt(ax, s, section_x + 3, warn_y + 2, "Backup folder is inside the installation folder.", fc=s.fg, fs=s.fs_xs)
            txt(ax, s, section_x + 3, warn_y + 0.5, "Uninstalling the app will delete this backup.", fc=s.fg, fs=s.fs_xs)
            tag(ax, s, section_x + section_w / 2, warn_y + 6 + 1.2, 3)
            btn(ax, s, section_x + 2, CY0 + 3, section_w - 4, 5, "Create Backup Now", "pri")
            tag(ax, s, section_x + section_w / 2, CY0 + 3 + 5 + 1.2, 4)
        else:
            # Restore section
            txt(ax, s, section_x + 2, cy1 - 9, "Select backup file:", fc=s.fg2, fs=s.fs_s)
            inp(ax, s, section_x + 2, cy1 - 13.5, section_w - 12, 3.5, "No file selected...")
            tag(ax, s, section_x + 2 + (section_w - 12) / 2, cy1 - 13.5 + 1.75 + 1.2, 5)
            btn(ax, s, section_x + section_w - 10, cy1 - 13.5, 8, 3.5, "Browse…", "sec")
            # pre-restore warning
            pwr_y = cy1 - 32
            box(ax, s, section_x + 2, pwr_y, section_w - 4, 10, fc=s.li, ec=s.bdr)
            txt(ax, s, section_x + 3, pwr_y + 8, "ℹ  Before restoring:", fc=s.pri, fs=s.fs_s, bold=True)
            for k, line in enumerate([
                "A safety backup of current data",
                "will be created automatically",
                "before the restore proceeds.",
            ]):
                txt(ax, s, section_x + 3, pwr_y + 5.5 - k * 2, line, fc=s.fg, fs=s.fs_xs)
            tag(ax, s, section_x + section_w / 2, pwr_y + 10 + 1.2, 6)
            btn(ax, s, section_x + 2, CY0 + 9, section_w - 4, 5, "Restore from Backup", "pri")
            tag(ax, s, section_x + section_w / 2, CY0 + 9 + 5 + 1.2, 7)
            txt(ax, s, section_x + 2, CY0 + 4,
                "Current data will be replaced. This cannot be undone.",
                fc=s.acc, fs=s.fs_xs)
            tag(ax, s, section_x + section_w / 2, CY0 + 4 + 1.5, 8)

    vline(ax, s, mid, CY0 + 1, cy1 - 1)

    legend_row(ax, s, [
        (1, "Estimated Backup Size"), (2, "Backup Destination"), (3, "Folder Warning"),
        (4, "Create Backup Button"), (5, "Restore File Picker"), (6, "Pre-restore Notice"),
        (7, "Restore Button"), (8, "Irreversibility Warning"),
    ])
    return fig


# ── PDF generation ────────────────────────────────────────────────────────────

PANELS = [
    ("cover", panel_cover),
    ("01_main_regular", panel_main_regular),
    ("02_main_short_session", panel_main_short),
    ("03_settings", panel_settings),
    ("04_voice_profiles", panel_voice_profiles),
    ("05_dictionary", panel_dictionary),
    ("06_batch", panel_batch),
    ("07_output_config", panel_output_config),
    ("08_hotkeys", panel_hotkeys),
    ("09_labelling", panel_labelling),
    ("10_history", panel_history),
    ("11_backup", panel_backup),
]


def generate_pdf(s: S):
    out = OUTPUT_DIR / f"wireframe_{s.slug}.pdf"
    with PdfPages(str(out)) as pdf:
        for name, fn in PANELS:
            fig = fn(s)
            pdf.savefig(fig, bbox_inches="tight", dpi=120, facecolor=s.bg)
            plt.close(fig)
            print(f"  [{s.name}] {name}")
    print(f"  -> {out}")


def main():
    for s in ALL:
        print(f"\nGenerating {s.name}...")
        generate_pdf(s)
    print("\nDone.")


if __name__ == "__main__":
    main()
