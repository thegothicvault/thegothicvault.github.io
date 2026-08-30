# -*- coding: utf-8 -*-
"""
overlay.py - burn the REAL AliExpress deal onto a heel image's negative space.

The Magnific Space renders each ad with a clean negative-space zone (top third).
This takes the rendered image + the product's `deal` (real sale / was / discount /
rating / sold, pulled from the scout pool into approved_catalog by taste_engine)
and draws the on-screen price badge + social proof - the thing the Smart Heel
research says separates a "pretty" shot from one that SELLS.

Never invents data: any field missing from `deal` is simply skipped. If there is
no price at all, the image is left untouched.

Usage:
    py -3 overlay.py <slug-or-GELEM-folder>          # overlay every image for that heel
    py -3 overlay.py --image <path> --deal '<json>'  # one-off on a single file
"""
import os, sys, json, argparse, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT         = Path(__file__).resolve().parent.parent
CATALOG_FILE = ROOT / "data" / "approved_catalog.json"
GELEM_DIR    = ROOT / "GELEM"

_FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
_FONT_REG  = "C:/Windows/Fonts/arial.ttf"

# Palette
_INK    = (18, 18, 18, 255)
_WHITE  = (255, 255, 255, 255)
_NOW    = (255, 214, 10, 255)     # deal-yellow for the live price
_MUTED  = (200, 200, 200, 255)
_ACCENT = (214, 40, 40, 255)      # discount-badge red
_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
_DOT = "   \u00b7   "


def _font(size, bold=True):
    try:
        return ImageFont.truetype(_FONT_BOLD if bold else _FONT_REG, int(size))
    except Exception:
        return ImageFont.load_default()


def _money(v):
    try:
        return f"${float(v):.2f}"
    except Exception:
        return f"${v}" if v else ""


def _text_w(d, txt, font):
    return d.textbbox((0, 0), txt, font=font)[2]


def _draw_star(d, cx, cy, r, fill):
    """Vector 5-point star - font-independent, so ratings render on any machine."""
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill)


def apply_overlay(img_path, deal, out_path=None):
    """Burn the deal onto img_path. Returns out_path, or None if nothing was drawn."""
    deal = deal or {}
    sale, was, disc = deal.get("sale"), deal.get("was"), deal.get("discount")
    rating, sold = deal.get("rating"), deal.get("sold")
    if not sale and not was:
        return None  # no price -> nothing to sell with

    im = Image.open(img_path).convert("RGBA")
    W, H = im.size
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # --- semi-transparent banner across the top negative-space zone ---
    band_h = int(H * 0.24)
    d.rectangle([0, 0, W, band_h], fill=(0, 0, 0, 140))

    pad = int(W * 0.05)
    y = int(H * 0.045)

    # --- price line: big NOW price + struck-through WAS price ---
    now_txt = _money(sale or was)
    f_now = _font(W * 0.11, bold=True)
    d.text((pad, y), now_txt, font=f_now, fill=_NOW)
    now_w = _text_w(d, now_txt, f_now)
    now_h = d.textbbox((0, 0), now_txt, font=f_now)[3]

    if was and sale and str(was) != str(sale):
        was_txt = _money(was)
        f_was = _font(W * 0.05, bold=False)
        wx = pad + now_w + int(W * 0.03)
        wy = y + int(now_h * 0.30)
        d.text((wx, wy), was_txt, font=f_was, fill=_MUTED)
        ww = _text_w(d, was_txt, f_was)
        wh = d.textbbox((0, 0), was_txt, font=f_was)[3]
        d.line([wx, wy + wh * 0.62, wx + ww, wy + wh * 0.62], fill=_MUTED, width=max(2, int(W * 0.004)))

    # --- discount badge ---
    if disc:
        f_disc = _font(W * 0.045, bold=True)
        badge = f"{disc} OFF".upper()
        bw = _text_w(d, badge, f_disc)
        bh = d.textbbox((0, 0), badge, font=f_disc)[3]
        bx0 = W - pad - bw - int(W * 0.03)
        by0 = y + int(H * 0.01)
        d.rounded_rectangle([bx0, by0, bx0 + bw + int(W * 0.03), by0 + bh + int(H * 0.02)],
                            radius=int(H * 0.012), fill=_ACCENT)
        d.text((bx0 + int(W * 0.015), by0 + int(H * 0.008)), badge, font=f_disc, fill=_WHITE)

    # --- social proof line (only real fields; vector star for the rating) ---
    if rating or sold:
        f_pf = _font(W * 0.038, bold=True)
        px = pad
        py = int(band_h - H * 0.055)
        line_h = d.textbbox((0, 0), "0", font=f_pf)[3]
        if rating:
            sr = W * 0.020
            _draw_star(d, px + sr, py + line_h * 0.55, sr, _NOW)
            px += int(sr * 2 + W * 0.012)
        txt = _DOT.join([t for t in [str(rating) if rating else "", str(sold) if sold else ""] if t])
        d.text((px, py), txt, font=f_pf, fill=_WHITE)

    out = Image.alpha_composite(im, layer).convert("RGB")
    out_path = out_path or str(Path(img_path).with_name(Path(img_path).stem + "_deal.jpg"))
    out.save(out_path, quality=95)
    return out_path


def _deal_for_folder(folder_name):
    """Find the catalog item whose GELEM folder matches, return its deal."""
    catalog = json.loads(CATALOG_FILE.read_text(encoding="utf-8")) if CATALOG_FILE.exists() else []
    for item in catalog:
        la = (item.get("local_asset") or "")
        if folder_name in la or la.endswith(folder_name):
            return item.get("deal") or {}
    return {}


def overlay_heel(folder):
    """Overlay every image in GELEM/<folder> with that heel's deal."""
    fdir = GELEM_DIR / folder if not os.path.isabs(folder) else Path(folder)
    if not fdir.exists():
        print(f"no such folder: {fdir}"); return []
    deal = _deal_for_folder(fdir.name)
    if not deal:
        print(f"no deal found for {fdir.name} (approve it fresh so the pool deal attaches)"); return []
    done = []
    for p in sorted(fdir.iterdir()):
        if p.suffix.lower() in _IMG_EXT and not p.stem.endswith("_deal"):
            out = apply_overlay(str(p), deal)
            if out:
                done.append(out); print(f"  overlaid -> {Path(out).name}")
    print(f"done: {len(done)} images for {fdir.name}")
    return done


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", help="GELEM folder name or slug")
    ap.add_argument("--image", help="one-off: single image path")
    ap.add_argument("--deal", help="one-off: deal JSON (with --image)")
    ap.add_argument("--out", help="one-off: output path")
    a = ap.parse_args()
    if sys.stdout:
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    if a.image:
        deal = json.loads(a.deal) if a.deal else {}
        r = apply_overlay(a.image, deal, a.out)
        print(f"wrote {r}" if r else "no price in deal - nothing drawn")
    elif a.target:
        overlay_heel(a.target)
    else:
        ap.print_help()
