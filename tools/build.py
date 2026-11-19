#!/usr/bin/env python3
"""Assemble the static site from src/ into site/.

    python3 tools/build.py

- site.config.json     company contact details + domain (single source of truth)
- src/partials/*.html  shared layout, head, header and footer; any partial can be
                       pulled into a page with {{INCLUDE:name}}
- src/pages/*.html     page bodies, each starting with a <!--meta {...} --> JSON block
- src/assets/          images etc., copied to site/assets/ (src/assets/images/ is
                       mirrored exactly, so deleted source images are removed too)
- Writes site/<path>/index.html, site/404.html, site/sitemap.xml, site/robots.txt

Standard library only. Cloudflare Pages serves the committed site/ folder
directly, so no build step is needed at deploy time; run this locally after
editing anything in src/ or site.config.json, then commit site/.
"""
import hashlib
import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "site"
CONFIG = ROOT / "site.config.json"

TEST_EMAIL = "inquiries@example.com"  # used only when no email is configured

NAV = [
    ("home", "/", "Home"),
    ("about", "/about/", "About us"),
    ("services", "/services/", "Services"),
    ("sourcing", "/sourcing/", "Products & sourcing"),
    ("contact", "/contact/", "Contact us"),
]

META_RE = re.compile(r"\A\s*<!--meta\s*(\{.*?\})\s*-->\s*", re.S)


def load_config():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not cfg.get("email"):
        print(
            "\n  WARNING: site.config.json has no \"email\" value.\n"
            f"  Building with the test address {TEST_EMAIL}.\n"
            "  Set the business email in site.config.json and rebuild before launch.\n",
            file=sys.stderr,
        )
        cfg["email"] = TEST_EMAIL
    cfg["site_url"] = cfg["site_url"].rstrip("/")
    return cfg


def dump(data):
    return json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")


def postal_address(c):
    a = c["address"]
    addr = {"@type": "PostalAddress"}
    if a.get("street"):
        addr["streetAddress"] = a["street"]
    addr["addressLocality"] = a["locality"]
    if a.get("postal_code"):
        addr["postalCode"] = a["postal_code"]
    addr["addressCountry"] = a["country_code"]
    return addr


def organization_jsonld(c):
    # Only information supplied by the client. Social profiles and founding
    # date are deliberately omitted until verified (see checklist).
    return dump({
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": c["site_url"] + "/#organization",
        "name": c["site_name"],
        "legalName": c["legal_name"],
        "url": c["site_url"] + "/",
        "logo": c["site_url"] + "/assets/img/NSS_logo.png",
        "email": c["email"],
        "telephone": [c["landline_e164"], c["phone_e164"]],
        "address": postal_address(c),
        "contactPoint": [
            {"@type": "ContactPoint", "contactType": "customer service", "email": c["email"],
             "telephone": c["landline_e164"], "name": "Office landline"},
            {"@type": "ContactPoint", "contactType": "customer service", "email": c["email"],
             "telephone": c["phone_e164"], "name": "Mobile and WhatsApp"},
        ],
    })


def website_jsonld(c):
    return dump({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": c["site_url"] + "/#website",
        "url": c["site_url"] + "/",
        "name": c["site_name"],
        "publisher": {"@id": c["site_url"] + "/#organization"},
    })


def breadcrumb_jsonld(c, meta):
    return dump({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": c["site_url"] + "/"},
            {"@type": "ListItem", "position": 2, "name": meta["crumb"], "item": c["site_url"] + meta["path"]},
        ],
    })


def render_nav(current):
    items = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return "\n            ".join(items)


# ---------- photos ----------
# {{PHOTO:slot|alt text}} -> <img> for src/assets/images/photos/<slot>.webp (see
# tools/fetch_photos.py). If the photo is missing, a designed fallback is used so a
# slot is never empty: the matching illustration, or an icon tile for product items.
PHOTO_DIR = SRC / "assets" / "images" / "photos"
PHOTO_SIZES = {"cat": (800, 600), "item": (480, 360), "banner": (1600, 720), "feature": (1200, 800), "svc": (720, 480), "about": (1200, 800)}
FALLBACK_ICONS = {
    "cat-handicrafts-felt": "bowl", "cat-herbs-spices": "leaf", "cat-agriculture": "tea",
    "cat-food": "jar", "cat-textiles": "textile", "cat-home-decor": "lamp", "cat-custom": "plus",
    "item-felt-balls": "felt", "item-felt-rugs": "felt", "item-felt-slippers": "felt", "item-felt-toys": "felt",
    "item-pet-products": "felt", "item-hemp": "textile", "item-knitwear": "textile", "item-pashmina": "textile",
    "item-dhaka": "textile", "item-lokta": "docs", "item-carpets": "textile", "item-cushions": "textile",
    "item-lamps": "lamp",
}
_credits_file = PHOTO_DIR / "credits.json"
PHOTO_CREDITS = json.loads(_credits_file.read_text()) if _credits_file.is_file() else {}
PHOTO_RE = re.compile(r"\{\{PHOTO:([a-z0-9-]+)\|([^}]*)\}\}")


def photo_html(slot, alt):
    kind = slot.split("-", 1)[0]
    w, h = PHOTO_SIZES[kind]
    eager = kind == "banner"
    loading = 'decoding="async" fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    alt_attr = html.escape(alt, quote=True)
    if (PHOTO_DIR / f"{slot}.webp").is_file():
        meta = PHOTO_CREDITS.get(slot, {})
        w, h = meta.get("w", w), meta.get("h", h)
        # Smaller copies (<slot>-<width>.webp) become a srcset so phones don't download desktop files.
        variants = sorted((int(f.stem.rsplit("-", 1)[1]), f.name) for f in PHOTO_DIR.glob(f"{slot}-*.webp")
                          if f.stem.rsplit("-", 1)[1].isdigit())
        srcset = ""
        if variants:
            entries = [f"/assets/images/photos/{name} {vw}w" for vw, name in variants]
            entries.append(f"/assets/images/photos/{slot}.webp {w}w")
            srcset = f' srcset="{", ".join(entries)}" sizes="(min-width: 78rem) 1240px, calc(100vw - 2.5rem)"'
        return (f'<img class="photo photo--{kind}" src="/assets/images/photos/{slot}.webp"{srcset} width="{w}" height="{h}" '
                f'{loading} alt="{alt_attr}">')
    # Fallbacks
    name = slot.split("-", 1)[1]
    svg = {"banner": f"banner-{name}.svg", "feature": f"feature-{name}.svg", "svc": f"spot-{name}.svg"}.get(kind)
    if svg and (SRC / "assets" / "images" / svg).is_file():
        sw, sh = {"banner": (1600, 720), "feature": (1200, 800), "svc": (480, 320)}[kind]
        return (f'<img class="photo photo--{kind}" src="/assets/images/{svg}" width="{sw}" height="{sh}" '
                f'{loading} alt="{alt_attr}">')
    icon = FALLBACK_ICONS.get(slot, "box")
    label = f' role="img" aria-label="{alt_attr}"' if alt else ' aria-hidden="true"'
    return (f'<span class="photo-fallback photo-fallback--{kind}"{label}>'
            f'<svg aria-hidden="true"><use href="/assets/img/icons.svg#i-{icon}"/></svg></span>')


_hashes = {}


def asset_version(url_path):
    """Short content hash for a file under site/, used as a cache-busting ?v= value."""
    if url_path not in _hashes:
        f = OUT / url_path.lstrip("/")
        _hashes[url_path] = hashlib.sha256(f.read_bytes()).hexdigest()[:10] if f.is_file() else None
    return _hashes[url_path]


ASSET_REF = re.compile(r'((?:src|href|srcset)=")(/assets/[^"#?\s]+)((?:#[^"]*)?")')
SRCSET = re.compile(r'srcset="([^"]*,[^"]*)"')


def version_assets(doc):
    """Append ?v=<hash> to every /assets/ reference so changed files always get a new URL.
    (Browsers otherwise keep serving cached copies, e.g. an old icon sprite missing new icons.)"""
    def sub(m):
        v = asset_version(m.group(2))
        return f"{m.group(1)}{m.group(2)}?v={v}{m.group(3)}" if v else m.group(0)
    doc = ASSET_REF.sub(sub, doc)

    def sub_srcset(m):  # multi-entry srcset: version every URL in the list
        parts = []
        for entry in m.group(1).split(","):
            url, *desc = entry.strip().split()
            v = asset_version(url) if url.startswith("/assets/") else None
            parts.append(" ".join([f"{url}?v={v}" if v else url] + desc))
        return f'srcset="{", ".join(parts)}"'
    return SRCSET.sub(sub_srcset, doc)


def build_page(path, partials, c):
    raw = path.read_text(encoding="utf-8")
    m = META_RE.match(raw)
    if not m:
        sys.exit(f"{path}: missing <!--meta {{...}} --> block")
    meta = json.loads(m.group(1))
    body = raw[m.end():]

    url_path = meta["path"]
    canonical = c["site_url"] + url_path
    jsonld = []
    if meta.get("organization"):
        jsonld += [organization_jsonld(c), website_jsonld(c)]
    if meta.get("crumb"):
        jsonld.append(breadcrumb_jsonld(c, meta))
    jsonld_html = "\n".join(f'<script type="application/ld+json">\n{j}\n</script>' for j in jsonld)

    noindex = meta.get("noindex", False)
    vars_ = {
        "TITLE": html.escape(meta["title"]),
        "DESCRIPTION": html.escape(meta["description"]),
        "CANONICAL_TAG": "" if noindex else f'<link rel="canonical" href="{canonical}">',
        "CANONICAL": canonical,
        "ROBOTS": "noindex, follow" if noindex else "index, follow",
        "OG_IMAGE": c["site_url"] + c["og_image"],
        "SITE_NAME": html.escape(c["site_name"]),
        "LEGAL_NAME": html.escape(c["legal_name"]),
        "JSONLD": jsonld_html,
        "PRELOAD": meta.get("preload", ""),
        "NAV": render_nav(meta.get("nav", "")),
        "EMAIL": html.escape(c["email"]),
        "GMAIL_COMPOSE": "https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=" + html.escape(c["email"]),
        # Display form with a line-break opportunity before "@" so long addresses wrap cleanly.
        "EMAIL_TEXT": html.escape(c["email"]).replace("@", "<wbr>@", 1),
        "PHONE_E164": c["phone_e164"],
        "PHONE_DISPLAY": html.escape(c["phone_display"]),
        # FormSubmit endpoints use the private alias token, so the inbox address is not in the form URL.
        "FORM_ENDPOINT": "https://formsubmit.co/ajax/" + c.get("form_token", c["email"]),
        "FORM_ACTION": "https://formsubmit.co/" + c.get("form_token", c["email"]),
        "LANDLINE_E164": c["landline_e164"],
        "LANDLINE_DISPLAY": html.escape(c["landline_display"]),
        "LANDLINE_LOCAL": html.escape(c["landline_local"]),
        "WHATSAPP_URL": c["whatsapp_url"],
        "ADDRESS": html.escape(c["address"]["display"]),
        "YEAR": str(date.today().year),
        "PAGE": meta.get("nav", "page"),
    }

    doc = (partials["layout"]
           .replace("{{HEAD}}", partials["head"])
           .replace("{{HEADER}}", partials["header"])
           .replace("{{MAIN}}", body)
           .replace("{{FOOTER}}", partials["footer"]))
    doc = re.sub(r"\{\{INCLUDE:([a-z0-9-]+)\}\}", lambda m: partials[m.group(1)], doc)
    doc = PHOTO_RE.sub(lambda m: photo_html(m.group(1), m.group(2)), doc)
    for k, v in vars_.items():
        doc = doc.replace("{{" + k + "}}", v)
    doc = version_assets(doc)
    leftover = set(re.findall(r"\{\{[A-Z_]+\}\}", doc))
    if leftover:
        sys.exit(f"{path}: unresolved template variables {leftover}")

    dest = OUT / meta["output"] if meta.get("output") else OUT / url_path.strip("/") / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    return meta, dest


def copy_assets():
    src = SRC / "assets"
    if not src.exists():
        return
    for d in src.iterdir():
        if not d.is_dir():
            continue
        dest = OUT / "assets" / d.name
        if d.name == "images" and dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(d, dest, dirs_exist_ok=True)
        print(f"copied src/assets/{d.name}/ -> site/assets/{d.name}/")


def main():
    c = load_config()
    copy_assets()
    partials = {p.stem: p.read_text(encoding="utf-8") for p in (SRC / "partials").glob("*.html")}
    pages = []
    for p in sorted((SRC / "pages").glob("*.html")):
        meta, dest = build_page(p, partials, c)
        pages.append(meta)
        print(f"built {dest.relative_to(ROOT)}")

    today = date.today().isoformat()
    entries = [
        f"  <url>\n    <loc>{c['site_url']}{m['path']}</loc>\n    <lastmod>{today}</lastmod>\n  </url>"
        for m in sorted(pages, key=lambda m: m.get("order", 99)) if not m.get("noindex")
    ]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries) + "\n</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {c['site_url']}/sitemap.xml\n", encoding="utf-8")
    print("built site/sitemap.xml, site/robots.txt")


if __name__ == "__main__":
    main()
