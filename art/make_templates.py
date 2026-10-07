"""Builds the Sunny Garden art templates.

  - Sunny-Garden-paint-sheets.pdf : printable Letter pages (300 dpi) with boxes in the exact proportions
    of every piece, for painting by hand (watercolor on paper), then photographing/scanning.
  - templates/*.png               : exact-pixel-size guide layers for painting digitally (Procreate etc.).

Run:  python art/make_templates.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
OUT_TEMPLATES = HERE / "templates"
OUT_TEMPLATES.mkdir(exist_ok=True)

INK = (58, 26, 42)
SOFT = (120, 100, 110)
GUIDE = (92, 168, 214)          # light blue: easy to tell apart from the painting
PAPER = (255, 255, 255)
F_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\georgiai.ttf", 92)
F_H = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 46)
F_T = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 38)
F_S = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 31)

PAGE_W, PAGE_H = 2550, 3300     # US Letter at 300 dpi

# name, pixel size in the app (at 4x), what it is
PIECES = {
    "sunflower": (300, 480, "Sunflower"),
    "sun": (700, 700, "Sun with its glow"),
    "cloud": (300, 110, "Cloud"),
    "butterfly": (100, 80, "Butterfly"),
    "bee": (80, 60, "Bee"),
    "daisy": (60, 80, "Daisy"),
    "tuft": (60, 60, "Grass tuft"),
    "sky": (1360, 600, "Sky"),
    "hills-far": (1360, 300, "Far hills"),
    "hills-near": (1360, 300, "Closer hills"),
    "meadow": (1360, 1900, "Meadow / grass"),
}


def dashed_rect(d, box, color, width=4, dash=26, gap=16):
    x0, y0, x1, y1 = box
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        dashed_line(d, (ax, ay), (bx, by), color, width, dash, gap)


def dashed_line(d, a, b, color, width=4, dash=26, gap=16):
    (ax, ay), (bx, by) = a, b
    length = max(abs(bx - ax), abs(by - ay))
    if length == 0:
        return
    dx, dy = (bx - ax) / length, (by - ay) / length
    pos = 0
    while pos < length:
        end = min(pos + dash, length)
        d.line([(ax + dx * pos, ay + dy * pos), (ax + dx * end, ay + dy * end)], fill=color, width=width)
        pos += dash + gap


def dashed_circle(d, cx, cy, r, color, width=4, steps=72):
    import math
    for i in range(0, steps, 2):
        a0, a1 = 2 * math.pi * i / steps, 2 * math.pi * (i + 1) / steps
        d.line([(cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=color, width=width)


def draw_guides(d, key, x, y, w, h, s):
    """Guides inside a box at (x, y) with size (w, h) px on the canvas, where s = canvas px per template px."""
    dashed_rect(d, (x, y, x + w, y + h), GUIDE, width=max(3, int(s * 1.4)))
    if key == "sunflower":
        # centre line, head circle, stem base, leaf zone
        dashed_line(d, (x + w / 2, y), (x + w / 2, y + h), GUIDE, max(2, int(s * 0.8)), 10 * s, 14 * s)
        dashed_circle(d, x + w / 2, y + 150 * s, 105 * s, GUIDE, max(3, int(s * 1.2)))
        d.text((x + w / 2, y + 150 * s), "head\n200-220 px", font=F_S if s > 1.5 else None, fill=GUIDE, anchor="mm", align="center")
        base_y = y + h - 12 * s
        d.polygon([(x + w / 2, base_y), (x + w / 2 - 14 * s, base_y + 12 * s), (x + w / 2 + 14 * s, base_y + 12 * s)], fill=GUIDE)
        dashed_line(d, (x + 40 * s, y + 345 * s), (x + w - 40 * s, y + 345 * s), GUIDE, max(2, int(s * 0.8)), 8 * s, 12 * s)
        d.text((x + w / 2, y + 330 * s), "leaves around here", font=F_S if s > 1.5 else None, fill=GUIDE, anchor="mm")
        d.text((x + w / 2, y + h - 30 * s), "stem base touches here", font=F_S if s > 1.5 else None, fill=GUIDE, anchor="ms")
    elif key == "sun":
        dashed_circle(d, x + w / 2, y + h / 2, 76 * s, GUIDE, max(3, int(s * 1.2)))
        d.text((x + w / 2, y + h / 2), "sun disc", font=F_S if s > 1.0 else None, fill=GUIDE, anchor="mm")
        dashed_circle(d, x + w / 2, y + h / 2, 330 * s, GUIDE, max(2, int(s * 1.0)))
        d.text((x + w / 2, y + h / 2 + 330 * s - 30), "rays / glow fade out before this edge", font=F_S if s > 1.0 else None, fill=GUIDE, anchor="mm")
    elif key in ("hills-far", "hills-near"):
        d.text((x + 24 * s, y + 20 * s), "paint nothing above the hills: plain white paper becomes transparent", font=F_S if s > 0.8 else None, fill=GUIDE, anchor="la")
        dashed_line(d, (x, y + h * 0.35), (x + w, y + h * 0.35), GUIDE, max(2, int(s * 1.0)), 24 * s, 24 * s)
        d.text((x + w - 20 * s, y + h * 0.35 - 8), "highest hilltop around here", font=F_S if s > 0.8 else None, fill=GUIDE, anchor="rd")
    elif key == "meadow":
        d.text((x + 24 * s, y + 20 * s), "TOP: calm and light (flowers stand here)", font=F_S if s > 0.8 else None, fill=GUIDE, anchor="la")
        d.text((x + 24 * s, y + h - 20 * s), "BOTTOM: can be darker", font=F_S if s > 0.8 else None, fill=GUIDE, anchor="ld")
        for frac in (0.25, 0.5, 0.75):
            dashed_line(d, (x, y + h * frac), (x + 40 * s, y + h * frac), GUIDE, max(2, int(s)), 12 * s, 8 * s)
    elif key == "sky":
        d.text((x + 24 * s, y + h - 20 * s), "the sun, clouds and hills are placed on top of this", font=F_S if s > 0.8 else None, fill=GUIDE, anchor="ld")
    else:
        dashed_line(d, (x + w / 2, y), (x + w / 2, y + h), GUIDE, max(2, int(s * 0.8)), 6 * s, 8 * s)
        dashed_line(d, (x, y + h / 2), (x + w, y + h / 2), GUIDE, max(2, int(s * 0.8)), 6 * s, 8 * s)


# ---------- digital guide PNGs, exact pixel sizes ----------
for key, (w, h, title) in PIECES.items():
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = max(1.0, w / 300)
    d_guide = ImageDraw.Draw(img)
    draw_guides(d_guide, key, 0, 0, w - 1, h - 1, s if key not in ("sky", "hills-far", "hills-near", "meadow", "sun") else max(1.0, w / 700))
    # make the guide lines semi-transparent so they never fight with the painting
    a = img.getchannel("A").point(lambda v: 150 if v else 0)
    img.putalpha(a)
    img.save(OUT_TEMPLATES / f"{key}-{w}x{h}.png")

# ---------- printable pages ----------
pages = []


def new_page(title, subtitle):
    img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    d = ImageDraw.Draw(img)
    d.text((140, 110), "Sunny Garden", font=F_TITLE, fill=INK)
    d.text((140, 235), title, font=F_H, fill=INK)
    d.text((140, 295), subtitle, font=F_T, fill=SOFT)
    return img, d


def box(d, key, x, y, f, label, note=None):
    w, h, _ = PIECES[key]
    bw, bh = int(w * f), int(h * f)
    d.text((x, y - 18), label, font=F_T, fill=INK, anchor="ld")
    if note:
        d.text((x + bw, y - 18), note, font=F_S, fill=SOFT, anchor="rd")
    draw_guides(d, key, x, y, bw, bh, f)
    return bw, bh


FOOT = "Light blue lines are only a guide: paint inside them, any size you like as long as the shape (proportion) stays the same."

# page 1: sunflowers
img, d = new_page("Page 1 / 5 - The sunflower (the most important one!)", "Four colour versions: golden, pale yellow, orange, deep red-orange. Box is 300 x 480 px (5:8).")
f = 2.5
names = ["1. Golden", "2. Pale yellow", "3. Orange", "4. Deep red-orange"]
xs = [(PAGE_W - 2 * 750) // 3, (PAGE_W - 2 * 750) // 3 * 2 + 750]
for i in range(4):
    x = xs[i % 2]
    y = 440 + (i // 2) * 1300
    box(d, "sunflower", x, y, f, names[i], "5:8")
d.text((140, PAGE_H - 90), FOOT, font=F_S, fill=SOFT)
pages.append(img)

# page 2: sun + clouds
img, d = new_page("Page 2 / 5 - Sun and clouds", "Sun: 700 x 700 px (square). Clouds: 300 x 110 px (about 11:4). Soft edges are great: they get placed on the sky.")
box(d, "sun", (PAGE_W - 1750) // 2, 440, 2.5, "Sun with its glow", "1:1")
cw = int(300 * 2.5)
gap = (PAGE_W - 3 * cw) // 4
for i in range(3):
    box(d, "cloud", gap + i * (cw + gap), 2540, 2.5, f"Cloud {i + 1}", "300:110")
d.text((140, PAGE_H - 90), FOOT, font=F_S, fill=SOFT)
pages.append(img)

# page 3: small things
img, d = new_page("Page 3 / 5 - The little ones", "Shown 6x bigger than they appear in the app, so there's room for detail. Wings are the key: draw two poses of each.")
f = 6
bw = int(100 * f)
box(d, "butterfly", 300, 480, f, "Butterfly - wings OPEN", "5:4")
box(d, "butterfly", 300 + bw + 160, 480, f, "Butterfly - wings CLOSED", "5:4")
bw2 = int(80 * f)
box(d, "bee", 300, 1180, f, "Bee - wings UP", "4:3")
box(d, "bee", 300 + bw2 + 160, 1180, f, "Bee - wings DOWN", "4:3")
box(d, "daisy", 300, 1860, f, "Daisy", "3:4")
box(d, "tuft", 300 + int(60 * f) + 160, 1860, f, "Grass tuft", "1:1")
d.text((140, PAGE_H - 90), FOOT, font=F_S, fill=SOFT)
pages.append(img)

# page 4: sky + hills
img, d = new_page("Page 4 / 5 - Sky and hills", "All three are the full width of the garden. Sky 1360 x 600 px, each hills strip 1360 x 300 px.")
f = 1.5
box(d, "sky", 255, 460, f, "Sky", "1360:600")
box(d, "hills-far", 255, 460 + 900 + 130, f, "Far hills (softer, paler)", "1360:300")
box(d, "hills-near", 255, 460 + 900 + 130 + 450 + 130, f, "Closer hills", "1360:300")
d.text((140, PAGE_H - 90), FOOT, font=F_S, fill=SOFT)
pages.append(img)

# page 5: meadow
img, d = new_page("Page 5 / 5 - The meadow", "Tall on purpose: 1360 x 1900 px (about 5:7). It's cropped to fit, so avoid big details near the edges.")
f = 1.3
box(d, "meadow", (PAGE_W - int(1360 * f)) // 2, 440, f, "Meadow / grass", "1360:1900")
d.text((140, PAGE_H - 90), FOOT, font=F_S, fill=SOFT)
pages.append(img)

pages[0].save(HERE / "Sunny-Garden-paint-sheets.pdf", save_all=True, append_images=pages[1:], resolution=300.0)
for i, p in enumerate(pages, 1):
    p.resize((PAGE_W // 3, PAGE_H // 3)).save(HERE / f"preview-page-{i}.png")
print("done:", len(pages), "pages,", len(list(OUT_TEMPLATES.glob('*.png'))), "digital guide files")
