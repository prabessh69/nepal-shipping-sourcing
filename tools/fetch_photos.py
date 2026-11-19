#!/usr/bin/env python3
"""Download freely licensed photos from Wikimedia Commons for the website.

    .venv/bin/python tools/fetch_photos.py            # fetch missing photos
    .venv/bin/python tools/fetch_photos.py --refresh  # re-pick every unpinned photo

Dev-only dependency: Pillow (pip install pillow). Not deployed.

For each slot in PHOTOS the script searches Commons (or uses a pinned file title),
accepts only CC0 / public domain / CC BY / CC BY-SA images, downloads a sized copy
(never hotlinked), crops it to the slot's aspect ratio with Pillow and saves WebP to
src/assets/images/photos/<slot>.webp.

Attribution data for every photo is written to src/assets/images/photos/credits.json,
and src/partials/photo-credits.html is generated for the /credits/ page. CC BY and
CC BY-SA licences require that credit, so keep the credits page published.
Pin a specific file by setting "title" on its slot after reviewing results.
"""
import argparse
import html
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "assets" / "images" / "photos"
CREDITS = OUT / "credits.json"
PARTIAL = ROOT / "src" / "partials" / "photo-credits.html"
API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1/images/"
UA = "NSSWebsiteImageFetcher/1.0 (static website build script; python-urllib)"

# slot: (search query or None, output size (w, h), pinned title or None)
PHOTOS = {
    # Home page product categories (4:3)
    "cat-herbs-spices": ("spices market Kathmandu", (800, 600), None),
    "cat-agriculture": ("Ilam tea garden", (800, 600), None),
    "cat-food": ("Nepal grocery shop", (800, 600), None),
    "cat-textiles": ("pashmina shawls", (800, 600), None),
    "cat-home-decor": ("handicraft shop Kathmandu", (800, 600), None),
    "cat-custom": ("Asan bazaar Kathmandu", (800, 600), None),
    # Products & Sourcing item thumbnails (4:3)
    "item-singing-bowls": ("Nepalese singing bowl", (480, 360), None),
    "item-metal-statues": ("Buddha statues shop Kathmandu", (480, 360), None),
    "item-wood-carvings": ("Bhaktapur wood carving window", (480, 360), None),
    "item-pottery": ("Bhaktapur potter", (480, 360), None),
    "item-thangka": ("thangka painting Nepal", (480, 360), None),
    "item-felt-balls": (None, (480, 360), "File:Felted balls.jpg"),
    "item-felt-rugs": ("felt rug", (480, 360), None),
    "item-felt-slippers": ("felt slippers", (480, 360), None),
    "item-timur": ("Zanthoxylum armatum", (480, 360), None),
    "item-turmeric": ("turmeric powder", (480, 360), None),
    "item-dried-herbs": ("dried herbs market", (480, 360), None),
    "item-botanicals": ("medicinal plants Nepal", (480, 360), None),
    "item-orthodox-tea": ("black tea leaves", (480, 360), None),
    "item-coffee": ("coffee beans", (480, 360), None),
    "item-cardamom": ("black cardamom", (480, 360), None),
    "item-ginger": ("fresh ginger", (480, 360), None),
    "item-honey": ("honey in glass jar", (480, 360), None),
    "item-snacks": ("beaten rice chiura", (480, 360), None),
    "item-pickles": ("achar pickle jar", (480, 360), None),
    "item-packaged-tea": ("tea packaging", (480, 360), None),
    "item-pashmina": ("pashmina", (480, 360), None),
    "item-hemp": (None, (480, 360), "File:Hemp Hats in Nepal 01.jpg"),
    "item-knitwear": ("wool sweater knitting", (480, 360), None),
    "item-dhaka": ("Dhaka topi", (480, 360), None),
    "item-lokta": ("lokta paper", (480, 360), None),
    "item-carpets": ("hand knotted carpet", (480, 360), None),
    "item-cushions": ("embroidered cushion", (480, 360), None),
    "item-lamps": ("paper lanterns", (480, 360), None),
    # Page banners (20:9) and home feature images (3:2)
    "banner-about": (None, (2400, 1080), "File:Boudhanath Stupa-IMG 7048.jpg"),
    "banner-services": ("container ship at sea", (1600, 720), None),
    "banner-sourcing": ("Thamel shop", (1600, 720), None),
    # About gallery (3:2, sharp enough for 2x screens at ~600 CSS px)
    "about-1": (None, (1200, 800), "File:Patan Durbar Square-2644.jpg"),
    "about-2": (None, (1200, 800), "File:The Annapurna range from Pokhara.jpg"),
    # Home "Sourcing in Nepal" section (3:2)
    "feature-sourcing": (None, (1200, 800), "File:Pot rows.jpg"),
    # Services cards (3:2)
    "svc-product-sourcing": ("handicraft shop Nepal", (720, 480), None),
    "svc-air-freight": ("cargo aircraft loading", (720, 480), None),
    "svc-sea-freight": ("container ship port", (720, 480), None),
    "svc-land-transport": ("Nepal truck", (720, 480), None),
    "svc-freight-forwarding": ("container terminal cranes", (720, 480), None),
    "svc-import-export": ("shipping containers", (720, 480), None),
    "svc-customs": ("Birgunj border", (720, 480), None),
    "svc-cargo-handling": ("pallets warehouse", (720, 480), None),
    "svc-quality-inspection": ("quality control inspection", (720, 480), None),
}

# Photos supplied by the company (originals kept locally, git-ignored; only WebP copies are committed).
# slot: (file in project root, output size, crop centering (x, y))
LOCAL = {
    "cat-handicrafts-felt": ("about_us1.JPG", (800, 600), (0.5, 0.5)),
    # Tight 4:3 crop on the two reindeer on the left (source region 2644x1983 px, downscaled, never upscaled).
    "item-felt-toys": ("about_us2.JPG", (480, 360), (0.5, 0.5), (0.0388, 0.18, 0.501, 0.70)),
    # Close crop on the felt dog. VERIFY with the company (checklist #11): a felt figure, not a cat cave.
    "item-pet-products": ("about_us2.JPG", (480, 360), (0.5, 0.5), (0.60, 0.50, 0.92, 0.95)),
}
COMPANY_CREDIT = {"author": "Nepal Shipping & Sourcing", "license": "Company photograph", "license_url": "", "source": ""}

# Per-slot overrides. Full-width banners are rendered ~1240 CSS px wide, i.e. ~2480 device px on
# Retina screens, so they are saved at 2400 px (quality 88) with a 1200 px variant for phones.
HIRES = {
    "banner-about": {"quality": 88, "centering": (0.5, 0.3), "variants": [1200]},
    "about-1": {"quality": 85, "fetch_width": 2400},
    "about-2": {"quality": 85, "centering": (0.5, 0.45), "fetch_width": 2400},
    "feature-sourcing": {"quality": 85, "fetch_width": 2400},
}

OK_LICENSE = re.compile(r"^(cc0|public domain|pd\b|cc[- ]by(-sa)?[- ]\d(\.\d)?)", re.I)
BAD_TITLE = re.compile(r"\b(map|logo|diagram|chart|flag|coat of arms|seal|stamp|icon|svg|audio|recording|scan|document|text|poster|"
                       r"pool|billiards?|concert|band|menu|beer|military|army|air force|usaf|soldiers?|protest|damaged|wreck|fire|accident|tennis|plastic)\b", re.I)


class FetchFailed(Exception):
    pass


def fetch(url, attempts=3):
    """GET with light pacing and a short backoff (2-3 s, never longer) on 429 / 5xx / timeouts.
    Raises FetchFailed so the caller can skip the slot; build.py then uses its fallback asset."""
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read()
            time.sleep(0.8)
            return body
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise FetchFailed(f"HTTP {e.code}")
            reason = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            reason = f"network: {e}"
        if i < attempts - 1:
            time.sleep(2 + i)  # 2 s, then 3 s
    raise FetchFailed(reason)


def api(params):
    params = {**params, "format": "json"}
    return json.loads(fetch(API + "?" + urllib.parse.urlencode(params)))


def candidates(query, width, title=None):
    base = {"action": "query", "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(width)}
    if title:
        data = api({**base, "titles": title})
    else:
        data = api({**base, "generator": "search", "gsrnamespace": "6", "gsrlimit": "20", "gsrsearch": query})
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    return pages


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def acceptable(page, size, pinned):
    ii = (page.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata", {})
    lic = strip_html(meta.get("LicenseShortName", {}).get("value", ""))
    if not OK_LICENSE.match(lic):
        return None, f"license {lic!r}"
    if ii.get("mime") not in ("image/jpeg", "image/png"):
        return None, "mime"
    if not pinned and BAD_TITLE.search(page["title"]):
        return None, "title"
    w, h = ii.get("width", 0), ii.get("height", 0)
    if w < size[0] * 0.9 or h < size[1] * 0.9:
        return None, "too small"
    target, ratio = size[0] / size[1], w / h
    if not pinned and not (target / 1.6 <= ratio <= target * 1.9):
        return None, "aspect"
    return {
        "title": page["title"],
        "source": ii.get("descriptionurl"),
        "thumb": ii.get("thumburl") or ii.get("url"),
        "author": strip_html(meta.get("Artist", {}).get("value", "")) or "Unknown author",
        "license": lic,
        "license_url": meta.get("LicenseUrl", {}).get("value", ""),
    }, None


def download(url):
    return fetch(url)


IVORY = (250, 247, 242)


def tone(img):
    """Subtle palette match: a little more contrast, slightly gentler saturation and a
    faint warm-ivory wash so photos sit comfortably on the site's warm surfaces."""
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(0.94)
    return Image.blend(img, Image.new("RGB", img.size, IVORY), 0.04)


def process(raw, size, dest, centering=(0.5, 0.5), quality=80, variants=()):
    img = raw if isinstance(raw, Image.Image) else Image.open(io.BytesIO(raw) if isinstance(raw, bytes) else raw)
    img = ImageOps.exif_transpose(img).convert("RGB")
    if img.width < size[0] or img.height < size[1]:
        print(f"    note: source {img.width}x{img.height} is smaller than {size[0]}x{size[1]} and will be upscaled", file=sys.stderr)
    img = tone(ImageOps.fit(img, size, method=Image.LANCZOS, centering=centering))
    img.save(dest, "WEBP", quality=quality, method=6)
    for w in variants:  # smaller copies for srcset, e.g. <slot>-1200.webp
        h = round(size[1] * w / size[0])
        img.resize((w, h), Image.LANCZOS).save(dest.with_name(f"{dest.stem}-{w}.webp"), "WEBP", quality=quality - 4, method=6)


def openverse(query, size):
    """Second source: Openverse (CC-licensed images from Flickr, Wikimedia and others)."""
    q = urllib.parse.urlencode({"q": query, "license": "cc0,pdm,by,by-sa", "page_size": "20", "mature": "false"})
    data = json.loads(fetch(f"{OPENVERSE}?{q}"))
    for r in data.get("results", []):
        w, h = r.get("width") or 0, r.get("height") or 0
        if w and h and (w < size[0] * 0.9 or h < size[1] * 0.9):
            continue
        if (r.get("filetype") or "jpg").lower() not in ("jpg", "jpeg", "png"):
            continue
        if BAD_TITLE.search(r.get("title") or ""):
            continue
        lic = r["license"].upper()
        lic = "CC0" if lic == "CC0" else ("Public domain" if lic == "PDM" else f"CC {lic.replace('-', ' ').replace(' ', '-')} {r.get('license_version', '')}".strip())
        yield {"title": r.get("title") or "Untitled", "source": r.get("foreign_landing_url"), "thumb": r["url"],
               "author": r.get("creator") or "Unknown author", "license": lic, "license_url": r.get("license_url", ""),
               "provider": r.get("source", "openverse")}


def write_partial(credits):
    rows = []
    for slot in list(LOCAL) + list(PHOTOS):
        c = credits.get(slot)
        if not c or "license" not in c or not (OUT / f"{slot}.webp").exists():
            continue
        lic = html.escape(c["license"])
        if c.get("license_url"):
            lic = (f'<a href="{html.escape(c["license_url"])}" rel="license noopener noreferrer" target="_blank">{lic}'
                   f'<span class="visually-hidden"> (opens in a new tab)</span></a>')
        name = html.escape(c["title"].removeprefix("File:"))
        if c.get("source"):
            name = (f'<a href="{html.escape(c["source"])}" target="_blank" rel="noopener noreferrer">{name}'
                    f'<span class="visually-hidden"> (opens in a new tab)</span></a>')
        rows.append(
            "          <tr>\n"
            f'            <td><img src="/assets/images/photos/{slot}.webp" width="{c["w"]}" height="{c["h"]}" loading="lazy" decoding="async" alt=""></td>\n'
            f"            <td>{name}</td>\n"
            f'            <td>{html.escape(c["author"])}</td>\n'
            f"            <td>{lic}</td>\n"
            "          </tr>")
    PARTIAL.write_text("<!-- Generated by tools/fetch_photos.py; do not edit by hand. -->\n" + "\n".join(rows) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--retone", action="store_true", help="apply the palette tone once to photos saved before toning existed")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    credits = json.loads(CREDITS.read_text()) if CREDITS.exists() else {}
    failed = []
    for slot, (fname, size, centering, *box) in LOCAL.items():
        src, dest = ROOT / fname, OUT / f"{slot}.webp"
        if not src.exists():
            if not dest.exists():
                print(f"  - {slot}: source {fname} not found", file=sys.stderr)
            continue
        if dest.exists() and slot in credits and not args.refresh:
            continue
        img = ImageOps.exif_transpose(Image.open(src))
        if box:
            l, t, r, b = box[0]
            img = img.crop((int(l * img.width), int(t * img.height), int(r * img.width), int(b * img.height)))
        process(img, size, dest, centering)
        credits[slot] = {**COMPANY_CREDIT, "title": fname, "w": size[0], "h": size[1], "toned": True}
        print(f"  {slot}: company photo {fname} {dest.stat().st_size // 1024} KB")
    if args.retone:
        for slot, c in credits.items():
            dest = OUT / f"{slot}.webp"
            if dest.exists() and "license" in c and not c.get("toned"):
                tone(Image.open(dest).convert("RGB")).save(dest, "WEBP", quality=82, method=6)
                c["toned"] = True
        print("  re-toned existing photos")
    for slot, (query, size, title) in PHOTOS.items():
        if args.only and slot not in args.only:
            continue
        dest = OUT / f"{slot}.webp"
        prev = credits.get(slot)
        if dest.exists() and prev and not args.refresh and not (title and prev["title"] != title):
            continue
        skip = set(prev.get("rejected", [])) if prev else set()
        skip |= {c["title"] for k, c in credits.items() if k != slot and "title" in c}  # no duplicates across slots
        chosen, reasons = None, []
        try:
            for page in candidates(query, HIRES.get(slot, {}).get("fetch_width", max(size[0], 800)), title):
                if page["title"] in skip:
                    continue
                info, why = acceptable(page, size, bool(title))
                if info:
                    chosen = info
                    break
                reasons.append(f"{page['title'][:50]}: {why}")
            if not chosen:
                for cand in openverse(query, size):
                    if cand["title"] not in skip and cand["source"] not in skip:
                        chosen = cand
                        break
            if not chosen:
                raise FetchFailed(f"no acceptable result on Commons ({len(reasons)} rejected) or Openverse")
            opts = HIRES.get(slot, {})
            process(download(chosen["thumb"]), size, dest, opts.get("centering", (0.5, 0.5)),
                    opts.get("quality", 80), opts.get("variants", ()))
        except FetchFailed as e:
            failed.append(slot)
            print(f"  - {slot}: skipped ({e}); build.py will use the fallback asset", file=sys.stderr)
            continue
        chosen.update({"w": size[0], "h": size[1], "query": query, "toned": True})
        if prev and prev.get("rejected"):
            chosen["rejected"] = prev["rejected"]
        chosen.pop("thumb")
        credits[slot] = chosen
        print(f"  {slot}: {chosen['title'][:70]} [{chosen['license']}] {dest.stat().st_size // 1024} KB")
        CREDITS.write_text(json.dumps(credits, indent=2, ensure_ascii=False))
    write_partial(credits)
    print(f"{sum('license' in c for c in credits.values())} photos recorded; credits partial written."
          + (f" {len(failed)} slot(s) use fallbacks: {', '.join(failed)}" if failed else ""))


if __name__ == "__main__":
    main()
