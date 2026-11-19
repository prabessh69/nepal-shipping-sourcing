#!/usr/bin/env python3
"""Automated QA for the static site (development tool — not deployed).

Requires Playwright (pip install playwright && playwright install chromium firefox)
and a running preview server:  python3 tools/serve.py 8080

    python3 tools/qa_check.py [--base http://127.0.0.1:8080] [--axe path/to/axe.min.js]
            [--shots DIR]

Checks, per page x browser x viewport (375 / 768 / 1440):
  console errors and CSP violations, failed requests, horizontal overflow,
  broken images, one <h1>, title / description / canonical / OG tags.
Then: internal link status, favicon files, mobile menu, inquiry form validation
and the generated mailto: URL, ?topic allowlist, ?review mode, skip link,
security headers, and (optionally) axe-core WCAG 2.2 AA scan.
Exit code 1 if any check fails.
"""
import argparse
import json
import sys
import urllib.request
from urllib.parse import urljoin, urlparse, parse_qs, unquote

from playwright.sync_api import sync_playwright

PAGES = ["/", "/about/", "/services/", "/sourcing/", "/contact/", "/credits/", "/this-page-does-not-exist"]
VIEWPORTS = [(375, 812), (768, 1024), (1440, 900)]
FAVICONS = ["/favicon-96x96.png", "/favicon.svg", "/favicon.ico", "/apple-touch-icon.png",
            "/site.webmanifest", "/web-app-manifest-192x192.png", "/web-app-manifest-512x512.png"]
REQUIRED_HEADERS = ["content-security-policy", "x-content-type-options", "referrer-policy",
                    "x-frame-options", "permissions-policy", "strict-transport-security"]

failures, passes = [], []


def check(ok, label):
    (passes if ok else failures).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label)


def http_status(url):
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers)


def scroll_through(page):
    page.evaluate("""async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
        await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; })));
        window.scrollTo(0, 0);
    }""")
    page.wait_for_timeout(200)


def page_checks(browser_name, page, base, path, vw, links):
    errors = []
    expect_404 = "does-not-exist" in path
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and not (expect_404 and "404" in m.text) else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    bad = []
    page.on("response", lambda r: bad.append(f"{r.status} {r.url}") if r.status >= 400 and not r.url.endswith("this-page-does-not-exist") else None)
    page.goto(base + path, wait_until="networkidle")
    scroll_through(page)
    tag = f"[{browser_name} {vw}px {path}]"

    check(not errors, f"{tag} no console errors / CSP violations {errors[:3] if errors else ''}")
    check(not bad, f"{tag} no failed requests {bad[:3] if bad else ''}")
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check(overflow <= 0, f"{tag} no horizontal scroll (overflow {overflow}px)")
    broken = page.evaluate("[...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)")
    check(not broken, f"{tag} all images loaded {broken}")
    blank = page.evaluate("""() => {
        const visible = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
        const out = [];
        document.querySelectorAll('svg use').forEach(u => {
            const svg = u.closest('svg');
            if (!visible(svg)) return;               // e.g. icons inside a closed mobile menu
            let b; try { b = u.getBBox(); } catch (e) { b = {width: 0, height: 0}; }
            if (!(b.width > 0 && b.height > 0)) out.push('icon ' + u.getAttribute('href').split('#')[1]);
        });
        document.querySelectorAll('img').forEach(i => { if (visible(i) && i.naturalWidth === 0) out.push('img ' + i.src); });
        document.querySelectorAll('.photo-fallback').forEach(f => { if (!f.querySelector('svg use')) out.push('empty fallback'); });
        return out;
    }""")
    check(not blank, f"{tag} every visible icon/image renders with non-zero size {blank[:4]}")
    if vw == 1440:
        meta = page.evaluate("""() => ({
            h1: document.querySelectorAll('h1').length,
            title: document.title,
            desc: document.querySelector('meta[name=description]')?.content || '',
            canonical: document.querySelector('link[rel=canonical]')?.href || '',
            og: !!document.querySelector('meta[property="og:image"]') && !!document.querySelector('meta[name="twitter:card"]'),
            icons: document.querySelectorAll('link[rel~=icon], link[rel=apple-touch-icon], link[rel=manifest]').length,
            lang: document.documentElement.lang,
            altMissing: [...document.images].filter(i => !i.hasAttribute('alt')).length,
            headingSkip: (() => { let last = 0, bad = []; document.querySelectorAll('h1,h2,h3,h4').forEach(h => { const l = +h.tagName[1]; if (last && l > last + 1) bad.push(h.textContent.trim()); last = l; }); return bad; })(),
            links: [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')),
            blank: [...document.querySelectorAll('a[target=_blank]')].filter(a => !/noopener/.test(a.rel)).length,
        })""")
        check(meta["h1"] == 1, f"{tag} exactly one h1 ({meta['h1']})")
        check(bool(meta["title"]) and bool(meta["desc"]), f"{tag} title + meta description")
        if "does-not-exist" not in path:
            check(meta["canonical"].endswith(path), f"{tag} canonical {meta['canonical']}")
        check(meta["og"], f"{tag} Open Graph + Twitter card")
        check(meta["icons"] == 5, f"{tag} 5 favicon/manifest links ({meta['icons']})")
        check(meta["lang"] == "en", f"{tag} html lang")
        check(meta["altMissing"] == 0, f"{tag} every img has alt")
        check(not meta["headingSkip"], f"{tag} no skipped heading levels {meta['headingSkip']}")
        check(meta["blank"] == 0, f"{tag} target=_blank links have rel=noopener")
        if not expect_404:
            links.update(urljoin(base + path, h) for h in meta["links"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--axe")
    ap.add_argument("--shots")
    ap.add_argument("--browsers", default="chromium,firefox", help="comma list: chromium,firefox,webkit")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    print("\n== Static files and headers")
    for f in FAVICONS:
        st, _ = http_status(base + f)
        check(st == 200, f"{f} -> {st}")
    for f in ["/robots.txt", "/sitemap.xml", "/assets/img/og-image.png"]:
        st, _ = http_status(base + f)
        check(st == 200, f"{f} -> {st}")
    st, h = http_status(base + "/")
    lower = {k.lower(): v for k, v in h.items()}
    for name in REQUIRED_HEADERS:
        check(name in lower, f"header {name}")
    check("frame-ancestors 'none'" in lower.get("content-security-policy", ""), "CSP frame-ancestors 'none'")
    check("unsafe-inline" not in lower.get("content-security-policy", ""), "CSP has no 'unsafe-inline'")
    st, _ = http_status(base + "/this-page-does-not-exist")
    check(st == 404, f"unknown path returns 404 ({st})")

    links = set()
    with sync_playwright() as p:
        for bname in args.browsers.split(","):
            print(f"\n== Pages in {bname}")
            browser = getattr(p, bname).launch()
            for vw, vh in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": vw, "height": vh})
                for path in PAGES:
                    page = ctx.new_page()
                    page_checks(bname, page, base, path, vw, links)
                    if args.shots and bname == "chromium":
                        name = (path.strip("/") or "home").replace("/", "_")
                        page.screenshot(path=f"{args.shots}/{name}-{vw}.png", full_page=True)
                    page.close()
                ctx.close()
            browser.close()

        print("\n== Internal links")
        internal = sorted(l for l in links if l.startswith(base))
        for url in internal:
            clean = url.split("#")[0]
            st, _ = http_status(clean)
            check(st == 200, f"{url[len(base):]} -> {st}")
            frag = urlparse(url).fragment
            if frag:
                links_page = urllib.request.urlopen(clean).read().decode()
                check(f'id="{frag}"' in links_page, f"anchor #{frag} exists on {urlparse(clean).path}")
        external = sorted(l for l in links if not l.startswith(base))
        print("  external/protocol links (not fetched):", external)

        print("\n== Interactions (chromium)")
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 375, "height": 812})
        page = ctx.new_page()
        page.goto(base + "/")
        toggle = page.locator(".nav-toggle")
        check(not page.locator("#site-nav").is_visible(), "mobile nav hidden initially")
        toggle.click()
        check(page.locator("#site-nav").is_visible() and toggle.get_attribute("aria-expanded") == "true", "mobile nav opens, aria-expanded=true")
        page.keyboard.press("Escape")
        check(not page.locator("#site-nav").is_visible() and toggle.get_attribute("aria-expanded") == "false", "Escape closes mobile nav")
        toggle.click()
        page.locator("#site-nav a", has_text="Services").click()
        page.wait_for_url("**/services/")
        check(page.url.endswith("/services/"), "mobile nav link navigates")
        page.keyboard.press("Tab")
        check(page.evaluate("document.activeElement.classList.contains('skip-link')"), "first Tab focuses skip link")

        # CTA buttons on the home page all lead somewhere real.
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(base + "/")
        for label, expect in [("Explore our services", "/services/"), ("Contact our team", "/contact/")]:
            page.goto(base + "/")
            page.get_by_role("link", name=label).first.click()
            page.wait_for_load_state()
            check(page.url.startswith(base + expect), f"CTA '{label}' -> {page.url[len(base):]}")

        # Form validation + mailto generation (capture navigation via CDP).
        page.goto(base + "/contact/?topic=sea-freight")
        check(page.locator("#f-topic").input_value() == "sea-freight", "?topic=sea-freight preselects topic")
        page.goto(base + "/contact/?topic=%3Cscript%3Ealert(1)%3C/script%3E")
        check(page.locator("#f-topic").input_value() == "", "?topic with unknown/malicious value is ignored")
        page.get_by_role("button", name="Send Message").click()
        n_err = page.locator("#form-errors li").count()
        check(n_err == 4 and page.locator("#form-errors").is_visible(), f"empty submit shows error summary ({n_err} errors)")
        check(page.locator("#f-email").get_attribute("aria-invalid") == "true", "invalid field gets aria-invalid")
        page.fill("#f-name", "Test Buyer")
        page.fill("#f-email", "not-an-email")
        page.select_option("#f-topic", "sourcing")
        page.fill("#f-message", "We need 2,000 felt balls in 12 colours, shipped to Hamburg.")
        page.get_by_role("button", name="Send Message").click()
        errs = page.locator("#form-errors li").all_text_contents()
        check(len(errs) == 1 and "email" in errs[0].lower(), f"bad email alone is flagged {errs}")
        page.fill("#f-email", "buyer@example.org")
        page.fill("#f-message", "We need 2,000 felt balls & <b>12</b> colours\nshipped to Hamburg.")

        # Submitting POSTs JSON to FormSubmit in the background (intercepted here; nothing leaves the machine).
        posted = []
        def fake_formsubmit(route):
            posted.append(route.request)
            route.fulfill(status=200, content_type="application/json", body='{"success":"true","message":"ok"}')
        ctx.route("https://formsubmit.co/**", fake_formsubmit)
        popups = []
        ctx.on("page", lambda p: popups.append(p))
        page.get_by_role("button", name="Send Message").click()
        page.wait_for_timeout(800)
        check(len(posted) == 1, f"submit sends one background POST ({len(posted)})")
        if posted:
            req = posted[0]
            body = json.loads(req.post_data or "{}")
            check(req.method == "POST" and req.url.startswith("https://formsubmit.co/ajax/"), "POST goes to the FormSubmit AJAX endpoint")
            check(req.headers.get("content-type") == "application/json" and req.headers.get("accept") == "application/json", "JSON Content-Type and Accept headers")
            check(body.get("name") == "Test Buyer" and body.get("email") == "buyer@example.org" and body.get("_replyto") == "buyer@example.org", "payload has name, email and _replyto")
            check(body.get("topic") == "Product Sourcing" and "<b>12</b>" in body.get("message", ""), "payload has topic and verbatim message")
            check(body.get("_subject") == "New Inquiry \u2014 Nepal Shipping & Sourcing" and body.get("_honey") == "", "payload has _subject and empty _honey")
        check(not popups, "no new tab or mail app is opened")
        check("Message sent!" in page.locator("#form-status").inner_text(), "on-page confirmation shown")
        check(page.locator("#f-name").input_value() == "" and page.locator("#f-message").input_value() == "", "form is reset after sending")
        check(page.locator("#form-fallback").is_hidden(), "copy fallback hidden on success")

        # Network failure path: error message plus the copy-message fallback.
        ctx.unroute("https://formsubmit.co/**")
        ctx.route("https://formsubmit.co/**", lambda route: route.abort())
        page.fill("#f-name", "Test Buyer"); page.fill("#f-email", "buyer@example.org")
        page.select_option("#f-topic", "sourcing"); page.fill("#f-message", "Second message to test the failure path, please ignore.")
        page.get_by_role("button", name="Send Message").click()
        page.wait_for_timeout(800)
        check("could not be sent" in page.locator("#form-status").inner_text() and page.locator("#copy-message").is_visible(), "failure shows error and copy fallback")
        check(page.locator("#f-message").input_value() != "", "form keeps the message when sending fails")

        page.goto(base + "/contact/?review")
        check(page.locator(".review-banner").is_visible(), "?review mode highlights placeholders")
        ctx.close()

        if args.axe:
            print("\n== axe-core WCAG 2.2 AA (chromium, CSP bypassed for injection only)")
            axe_src = open(args.axe).read()
            for vw in (375, 1440):
                ctx = browser.new_context(viewport={"width": vw, "height": 900}, bypass_csp=True)
                for path in PAGES[:-1]:
                    page = ctx.new_page()
                    page.goto(base + path, wait_until="networkidle")
                    page.add_script_tag(content=axe_src)
                    res = page.evaluate("""async () => {
                        const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice'] } });
                        return r.violations.map(v => ({id: v.id, impact: v.impact, n: v.nodes.length, t: v.nodes.slice(0,2).map(n => n.target.join(' '))}));
                    }""")
                    check(not res, f"[axe {vw}px {path}] {json.dumps(res) if res else 'no violations'}")
                    page.close()
                ctx.close()
        browser.close()

    print(f"\n{len(passes)} passed, {len(failures)} failed")
    for f in failures:
        print("  FAILED:", f)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
