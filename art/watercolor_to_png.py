"""Turns a photo/scan of a painting on white paper into a transparent PNG.

  python art/watercolor_to_png.py photo.jpg out.png [--size 300x480] [--anchor bottom|center]

Steps: (1) even out uneven lighting using the paper itself, (2) "colour to alpha": white paper becomes
transparent, and thin watercolor washes become partly transparent instead of getting a white halo,
(3) trim, and optionally fit into an exact canvas size.
Paint white highlights as untouched paper only if you want them see-through.
"""
import argparse
import numpy as np
from PIL import Image, ImageFilter


def paper_map(rgb):
    """Estimate how bright the blank paper is in every spot (handles shadows and uneven light)."""
    h, w = rgb.shape[:2]
    small = Image.fromarray((rgb * 255).astype(np.uint8)).resize((max(16, w // 16), max(16, h // 16)), Image.BILINEAR)
    small = small.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(6))
    big = small.resize((w, h), Image.BICUBIC)
    return np.maximum(np.asarray(big, dtype=np.float32) / 255.0, 0.2)


def to_rgba(img, floor=0.05):
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    flat = np.clip(rgb / paper_map(rgb), 0, 1)                 # paper becomes pure white everywhere
    alpha = 1.0 - flat.min(axis=2)                              # the darker/more saturated, the more opaque
    alpha[alpha < floor] = 0.0                                  # drop paper grain and sensor noise
    a = np.maximum(alpha, 1e-4)[..., None]
    color = np.clip(1.0 - (1.0 - flat) / a, 0, 1)               # un-mix the colour from the white paper
    out = np.dstack([color, alpha])
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def trim(img, pad=4):
    # Ignore specks of dust/noise: only count areas that survive a small erode-then-grow pass.
    solid = img.getchannel("A").point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9))
    box = solid.getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


def fit(img, size, anchor="center", margin=0.04):
    W, H = size
    s = min(W * (1 - 2 * margin) / img.width, H * (1 - 2 * margin) / img.height)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - img.width) // 2
    y = H - img.height - round(H * margin / 2) if anchor == "bottom" else (H - img.height) // 2
    canvas.alpha_composite(img, (x, y))
    return canvas


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--size", help="WxH canvas, e.g. 300x480")
    ap.add_argument("--anchor", default="center", choices=["center", "bottom"])
    a = ap.parse_args()
    result = trim(to_rgba(Image.open(a.src)))
    if a.size:
        result = fit(result, tuple(int(v) for v in a.size.lower().split("x")), a.anchor)
    result.save(a.dst, optimize=True)
    print("saved", a.dst, result.size)
