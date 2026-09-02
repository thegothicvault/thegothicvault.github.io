# -*- coding: utf-8 -*-
"""
build_site.py — inject approved heel products into index.html.

Reads data/approved_catalog.json (written by taste_engine.record_approval when
you press the Telegram OK button) and renders product cards between the
<!-- HEELS:START --> / <!-- HEELS:END --> markers in index.html.

Image priority per product:
  1. A generated variation in GELEM/<slug>/  → copied into img/heels/<slug>.jpg
     and referenced locally (served by GitHub Pages after push).
  2. The catalog image_url (a hosted CDN URL) → referenced directly.

Usage:
    python build_site.py           # rebuild index.html (no push)
    python build_site.py --push    # rebuild + git commit + push live
    python build_site.py --limit 12
"""
import sys, os, re, json, shutil, subprocess, argparse
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8") if sys.stdout else None
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import space_runner   # single source of truth for slugify (AliExpress /item ids)

ROOT         = Path(__file__).resolve().parent.parent      # E:\PROJECTS\thegothicvault
CATALOG_FILE = ROOT / "data" / "approved_catalog.json"
INDEX_FILE   = ROOT / "index.html"
GELEM_DIR    = ROOT / "GELEM"
IMG_DIR      = ROOT / "img" / "heels"

START_MARK = "<!-- HEELS:START -->"
END_MARK   = "<!-- HEELS:END -->"

IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")


# ── Helpers ───────────────────────────────────────────────────────────

def load_catalog():
    if not CATALOG_FILE.exists():
        return []
    with open(CATALOG_FILE, encoding="utf-8-sig") as f:  # tolerate a stray BOM
        return json.load(f)


def save_catalog(catalog):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)


# Reuse space_runner.slugify so each AliExpress heel gets a UNIQUE slug (it
# appends the /item id). The old Shopify-only version collapsed every generic
# "Stiletto Heels" to one slug → all shared a single image on the site.
slugify = space_runner.slugify


def find_variation_image(slug):
    """Return the first generated image in GELEM/<slug>/, if any."""
    folder = GELEM_DIR / slug
    if not folder.is_dir():
        # also try a loose match (folders sometimes carry a suffix)
        matches = [d for d in GELEM_DIR.glob(f"{slug}*") if d.is_dir()] if GELEM_DIR.is_dir() else []
        folder = matches[0] if matches else folder
    if folder.is_dir():
        imgs = sorted(p for p in folder.iterdir()
                      if p.suffix.lower() in IMG_EXTS)
        if imgs:
            return imgs[0]
    return None


def resolve_image(item, slug):
    """
    Decide the <img src> for a product.
    Copies a local variation into img/heels/ when available; otherwise uses the
    hosted catalog image_url. Returns a src string or "".
    """
    var = find_variation_image(slug)
    if var:
        IMG_DIR.mkdir(parents=True, exist_ok=True)
        dest = IMG_DIR / f"{slug}.jpg"
        try:
            shutil.copyfile(var, dest)
            return f"img/heels/{slug}.jpg"
        except Exception as e:
            print(f"  ! copy failed for {slug}: {e}")
    return item.get("image_url", "") or ""


def esc(s):
    return (s or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def short_name(title, n=26):
    t = (title or "").strip()
    return t if len(t) <= n else t[:n - 1].rstrip() + "…"


def card_html(item, slug):
    src   = resolve_image(item, slug)
    name  = esc(short_name(item.get("title", "")))
    href  = esc(item.get("aff_link") or item.get("url", ""))
    price = esc(item.get("price", "") or "Shop")
    alt   = esc(item.get("title", ""))
    return (
        '      <a class="product-card" href="{href}" target="_blank" rel="noopener">\n'
        '        <img src="{src}" alt="{alt}" loading="lazy">\n'
        '        <div class="card-info">\n'
        '          <span class="card-name">{name}</span>\n'
        '          <span class="card-price">{price}</span>\n'
        '        </div>\n'
        '      </a>'
    ).format(href=href, src=esc(src), alt=alt, name=name, price=price)


def build_cards(items):
    """Render items in 2-up pair-grids, trailing odd item as single-grid."""
    blocks = []
    i = 0
    while i < len(items):
        pair = items[i:i + 2]
        cards = "\n".join(card_html(it, slugify(it)) for it in pair)
        if len(pair) == 2:
            blocks.append(f'    <div class="pair-grid">\n{cards}\n    </div>')
        else:
            blocks.append(f'    <div class="single-grid">\n{cards}\n    </div>')
        i += 2
    # separators between rows, matching the site style
    return "\n    <div class=\"pair-sep\">· · ·</div>\n".join(blocks)


# ── Main build ────────────────────────────────────────────────────────

def rebuild(limit):
    catalog = load_catalog()
    if not catalog:
        print("Catalog is empty — nothing to inject.")
        return False

    # newest first, cap
    items = sorted(catalog, key=lambda x: x.get("date", ""), reverse=True)
    # skip items with no usable link
    items = [it for it in items if (it.get("aff_link") or it.get("url"))][:limit]

    inner = build_cards(items)
    injection = f"{START_MARK}\n{inner}\n    {END_MARK}"

    html = INDEX_FILE.read_text(encoding="utf-8")
    if START_MARK not in html or END_MARK not in html:
        print("ERROR: markers not found in index.html — aborting.")
        return False

    # function replacement → no backslash/group-ref interpretation on the HTML
    new_html = re.sub(
        re.escape(START_MARK) + r".*?" + re.escape(END_MARK),
        lambda _m: injection,
        html,
        flags=re.DOTALL,
    )
    INDEX_FILE.write_text(new_html, encoding="utf-8")
    print(f"✅ Injected {len(items)} heel cards into index.html")

    # mark on_site
    on_urls = {it.get("url") for it in items}
    for it in catalog:
        if it.get("url") in on_urls:
            it["on_site"] = True
    save_catalog(catalog)
    return True


def git_push():
    cmds = [
        ["git", "-C", str(ROOT), "add", "index.html", "img"],
        ["git", "-C", str(ROOT), "commit", "-m",
         f"site: heel drops {datetime.now():%Y-%m-%d}"],
        ["git", "-C", str(ROOT), "push", "origin", "main"],
    ]
    for c in cmds:
        r = subprocess.run(c, capture_output=True, text=True)
        print(f"$ {' '.join(c[3:])}\n{(r.stdout or '').strip()}{(r.stderr or '').strip()}")
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print("  (git step non-zero — stopping push)")
            return
    print("✅ Pushed live")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="git commit + push after build")
    ap.add_argument("--limit", type=int, default=12, help="max cards to show")
    args = ap.parse_args()

    if rebuild(args.limit) and args.push:
        git_push()
