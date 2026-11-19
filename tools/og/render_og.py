#!/usr/bin/env python3
"""Render tools/og/og-image.html to site/assets/img/og-image.png (needs Playwright)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / "site" / "assets" / "img" / "og-image.png"

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1200, "height": 630})
    page.goto((HERE / "og-image.html").as_uri(), wait_until="networkidle")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT))
    b.close()
print("wrote", OUT)
