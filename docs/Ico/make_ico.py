"""Generate WSP.ico from the SVG icon design using Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw


def bezier_pts(p0, p1, p2, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        pts.append((x, y))
    return pts


def draw_icon(size: int) -> Image.Image:
    OVER = 4       # oversample factor for anti-aliasing
    S = size * OVER
    B = 256.0      # SVG coordinate space width/height

    sc = S / B

    def sp(x, y):
        return (x * sc, y * sc)

    def sr(v):
        return v * sc

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")

    def rr(x, y, w, h, rx, fill):
        d.rounded_rectangle([sp(x, y), sp(x + w, y + h)],
                             radius=sr(rx), fill=fill)

    # Background
    rr(0, 0, 256, 256, 52, (55, 48, 163, 255))

    # Mic body
    rr(102, 38, 52, 94, 26, (224, 231, 255, 255))
    # Mic inner shading (50% opacity)
    rr(112, 48, 10, 74, 5, (199, 210, 254, 128))

    # Stand arc: M72 122 Q72 178 128 178 Q184 178 184 122
    arc = (bezier_pts((72, 122), (72, 178), (128, 178))
           + bezier_pts((128, 178), (184, 178), (184, 122)))
    arc_sc = [sp(x, y) for x, y in arc]
    sw = max(2, int(sr(9)))
    for i in range(len(arc_sc) - 1):
        d.line([arc_sc[i], arc_sc[i + 1]], fill=(199, 210, 254, 255), width=sw)

    # Stand pole
    d.line([sp(128, 178), sp(128, 202)], fill=(199, 210, 254, 255), width=sw)
    # Base bar
    d.line([sp(96, 202), sp(160, 202)], fill=(199, 210, 254, 255), width=sw)

    # Base end dots
    for cx, cy in [(96, 202), (160, 202)]:
        cr = sr(4.5)
        bx, by = sp(cx, cy)
        d.ellipse([bx - cr, by - cr, bx + cr, by + cr], fill=(199, 210, 254, 255))

    # Waveform bars (visible at >= 32 px)
    if size >= 32:
        rr(196, 92, 10, 28, 5, (129, 140, 248, 255))
        rr(210, 76, 10, 60, 5, (165, 180, 252, 255))
        rr(224, 84, 10, 44, 5, (99, 102, 241, 255))
        rr(238, 96, 10, 20, 5, (129, 140, 248, 255))

    # Text-line pills (visible at >= 48 px)
    if size >= 48:
        rr(36, 222, 120, 10, 5, (67, 56, 202, 255))
        rr(36, 236, 88, 10, 5, (67, 56, 202, 255))

    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    sizes = [256, 128, 64, 48, 32, 24, 16]
    imgs = [draw_icon(s) for s in sizes]

    out = Path(__file__).parent / "WSP.ico"
    imgs[0].save(str(out), format="ICO",
                 append_images=imgs[1:],
                 sizes=[(s, s) for s in sizes])
    print(f"Saved {out}  ({out.stat().st_size:,} bytes)")
