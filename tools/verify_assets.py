#!/usr/bin/env python3
"""Static check that every graphic referenced by the built site resolves.

    python3 tools/verify_assets.py

For every HTML file in site/:
  - every <img src>, <image href>, <link href> and <script src> under /assets/
    or the site root points to an existing, non-empty file;
  - every <img> has width and height attributes (prevents layout shift / 0x0 slots);
  - every icon <use href="...icons.svg#id"> names a <symbol id> that exists in the sprite;
  - every .photo-fallback tile contains a graphic;
  - no unresolved {{TEMPLATE}} / {{PHOTO:...}} markers remain.
Exit code 1 on any problem. Standard library only.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
SPRITE = SITE / "assets" / "img" / "icons.svg"
SYMBOLS = set(re.findall(r'<symbol id="([^"]+)"', SPRITE.read_text()))


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.imgs, self.uses, self.fallbacks = [], [], [], []
        self._fallback_depth = None
        self._fallback_has_graphic = False
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.depth += 1
        if tag == "img":
            self.imgs.append(a)
            self.refs.append(a.get("src", ""))
        elif tag in ("image", "use"):
            href = a.get("href", "")
            (self.uses if tag == "use" else self.refs).append(href)
            if self._fallback_depth is not None:
                self._fallback_has_graphic = True
        elif tag == "link" and a.get("rel") in ("stylesheet", "preload", "icon", "shortcut icon", "apple-touch-icon", "manifest"):
            self.refs.append(a.get("href", ""))
        elif tag == "source" and a.get("srcset"):
            self.refs.append(a["srcset"].split()[0])
        elif tag == "script" and a.get("src"):
            self.refs.append(a["src"])
        if "photo-fallback" in (a.get("class") or "").split():
            self._fallback_depth, self._fallback_has_graphic = self.depth, False

    def handle_endtag(self, tag):
        if self._fallback_depth is not None and self.depth == self._fallback_depth:
            self.fallbacks.append(self._fallback_has_graphic)
            self._fallback_depth = None
        self.depth -= 1


def local_path(url):
    if not url.startswith("/") or url.startswith("//"):
        return None
    return SITE / url.split("#")[0].split("?")[0].lstrip("/")


def main():
    problems, counts = [], {"pages": 0, "img": 0, "use": 0, "refs": 0, "fallbacks": 0}
    for page in sorted(SITE.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(SITE)
        counts["pages"] += 1
        if re.search(r"\{\{[A-Z_]+(:[^}]*)?\}\}", text):
            problems.append(f"{rel}: unresolved template marker")
        c = Collector()
        c.feed(text)
        for img in c.imgs:
            counts["img"] += 1
            if not img.get("width") or not img.get("height"):
                problems.append(f"{rel}: <img src={img.get('src')}> missing width/height")
            if "alt" not in img:
                problems.append(f"{rel}: <img src={img.get('src')}> missing alt")
        for url in c.refs:
            p = local_path(url)
            if p is None:
                continue
            counts["refs"] += 1
            if not p.is_file() or p.stat().st_size == 0:
                problems.append(f"{rel}: missing or empty asset {url}")
        for href in c.uses:
            counts["use"] += 1
            m = re.search(r"icons\.svg(?:\?[^#]*)?#([\w-]+)$", href)
            if not m:
                problems.append(f"{rel}: unexpected <use href={href}>")
            elif m.group(1) not in SYMBOLS:
                problems.append(f"{rel}: icon #{m.group(1)} is not defined in icons.svg")
            else:
                p = local_path(href)
                if not p.is_file():
                    problems.append(f"{rel}: sprite file missing for {href}")
        for ok in c.fallbacks:
            counts["fallbacks"] += 1
            if not ok:
                problems.append(f"{rel}: empty .photo-fallback tile")
    print(f"Checked {counts['pages']} pages: {counts['img']} images, {counts['use']} icons, "
          f"{counts['refs']} asset references, {counts['fallbacks']} fallback tiles.")
    for p in problems:
        print("  PROBLEM:", p)
    print("OK: every graphic resolves." if not problems else f"{len(problems)} problem(s) found.")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
