# Testing report

Final QA pass on the local build, served by `tools/serve.py`, which applies the production
`site/_headers` (including the Content Security Policy) the way Cloudflare Pages would.

**Date:** 19 November 2026 · **Build:** `python3 tools/build.py`, with the corrected domain and the business email. The full QA suite was re-run after that change: 222 passed, 0 failed.

## Summary

| Area | Result |
|---|---|
| Automated QA suite (`tools/qa_check.py`, Chromium) | **222 passed, 0 failed** |
| Accessibility: axe-core 4.10.2, WCAG 2.0/2.1/2.2 A + AA + best practice | **0 violations** on all 5 pages at 375px and 1440px |
| Console errors / CSP violations | **None** on any page, at any viewport |
| Horizontal scrolling | **None** at 375, 768 or 1440px on any page |
| Broken internal links / anchors | **None** (all internal URLs return 200; all `#anchors` exist) |
| Favicon files | All 7 return **HTTP 200** with correct content types |
| Security headers | All present; the CSP contains no `'unsafe-inline'` |
| Core Web Vitals (lab, Chromium) | LCP 0.9–1.7 s and CLS ≤ 0.06 on throttled mobile; "good" range |
| Lighthouse | **Not run.** See "What could not be tested" |

## Environment and tools

- macOS, Python 3.9 (standard library) for the build and preview server.
- **Playwright for Python + Chromium**, installed in a temporary virtual environment outside the
  project, for automated checks, interaction tests, performance measurement and screenshots.
- **System Firefox (headless)** for visual rendering checks at 375, 768 and 1440px.
- **axe-core 4.10.2** injected into each page for accessibility auditing. CSP was bypassed only to
  inject the test library; every other check ran under the real CSP.

## What was tested

### Pages × viewports
Home, About, Services, Products & Sourcing, Contact and the 404 page, at **375×812, 768×1024 and
1440×900**. For each combination:

- no console errors, JavaScript exceptions or CSP violations
- no failed network requests
- no horizontal overflow
- every image loaded (after scrolling, to trigger lazy loading)

At 1440px, also: exactly one `<h1>`, a unique title and meta description, the correct canonical URL,
Open Graph and Twitter card tags, all 5 favicon/manifest `<link>` tags, `lang="en"`, `alt` on every
image, no skipped heading levels, and `rel="noopener"` on every `target="_blank"` link.

### Static files and headers
- `/favicon-96x96.png`, `/favicon.svg`, `/favicon.ico`, `/apple-touch-icon.png`, `/site.webmanifest`
  and both manifest icons: **200**.
- `/robots.txt`, `/sitemap.xml`, `/assets/img/og-image.png`: **200**.
- An unknown path returns **404** with the custom 404 page. `/_headers` is not publicly served.
- Headers present: Content-Security-Policy (`frame-ancestors 'none'`, no `'unsafe-inline'`),
  X-Content-Type-Options, Referrer-Policy, X-Frame-Options, Permissions-Policy,
  Strict-Transport-Security.

### Navigation and buttons
- Every internal link and in-page anchor across all pages was collected and requested.
- Home CTAs: "Explore our services" → `/services/`; "Contact our team" → `/contact/`.
- Every service "Ask about …" button links to `/contact/?topic=…#inquiry`, which preselects the topic.
- Mobile menu: hidden at load; opens with `aria-expanded="true"`; closes with Escape; its links navigate.
- Keyboard: the first Tab focuses "Skip to main content".

### Inquiry form
- Submitting empty shows an error summary with 4 linked errors, inline messages and `aria-invalid`.
- An invalid email on its own is flagged as the only error.
- A valid submission generates a `mailto:` URL (captured through the Chrome DevTools Protocol) with the
  correct subject (`Website inquiry: Product sourcing (Test Buyer)`), and a body that carries
  user-typed markup (`<b>12</b>`) as inert plain text.
- After submitting, the status panel appears with the "Copy message" fallback.
- `?topic=sea-freight` preselects the topic. A `<script>` payload in `?topic=` is ignored.
- `?review` mode highlights placeholders.

### Visual review
Full-page screenshots were reviewed at all three widths. The final set is in `docs/screenshots/`
(5 pages × 3 widths, plus the open mobile menu and the form's validation state).

### Performance (Chromium lab measurement, cold load)

| Page | Mobile LCP* | Mobile CLS* | Desktop LCP | Requests | Transfer** |
|---|---|---|---|---|---|
| Home | 1.69 s | 0.032 | 0.06 s | 7 | 284 KB |
| About | 0.90 s | 0.057 | 0.06 s | 6 | 273 KB |
| Services | 0.92 s | 0.000 | 0.06 s | 7 | 283 KB |
| Sourcing | 0.90 s | 0.002 | 0.06 s | 6 | 273 KB |
| Contact | 0.91 s | 0.022 | 0.06 s | 8 | 362 KB |

\* Throttled to roughly "Slow 4G" (150 ms latency, 1.6 Mbps) with 4× CPU slowdown.
\** Uncompressed local transfer. Cloudflare compresses HTML, CSS, JS and SVG with Brotli, so production
sizes will be noticeably smaller. The contour map SVG (117 KB raw) compresses especially well.

### Security scan of shipped files
- No `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` or `new Function`.
- No inline `style=""` attributes or inline event handlers. The only executable inline script is the
  hash-allowlisted one-liner.
- No API keys, tokens or secrets.
- The only third-party URL is the WhatsApp link (`noopener noreferrer`).
- No third-party runtime dependencies, so there is nothing to audit for known vulnerabilities.

### Asset integrity
- `NSS_logo.png` is unchanged, and its copy in `site/assets/img/` is byte-identical.
- `favicon.zip` is unchanged and passes an integrity test. Every extracted favicon file is
  byte-identical to the zip. Only `site.webmanifest` was edited, to replace "MyWebSite".

## Visual update (accurate map, page banners, illustrations)

After the hero map was rebuilt from real boundary data, the cropped subpage strips were replaced with
full banners, and illustrations and icons were added across the pages, the full suite was re-run:
**222 passed, 0 failed**, with zero axe violations at 375px and 1440px. New layouts were checked
visually at 375px and 1440px: the hero map, the four page banners, the service illustrations (heading
first on mobile), the sourcing pipeline (4×2 grid on mobile, single row on desktop) and the category
and value icons. The screenshots in `docs/screenshots/` predate this update.

## Photos, icons and asset verification update

- **Blank icon slots** (process step 4, About values, sourcing Sample and Monitor) were caused by browsers
  caching the old 12-icon sprite for 7 days; every icon was present in the current sprite. Fixed with
  content-hash `?v=` URLs on every `/assets/` reference, which also allows one-year immutable caching.
- 41 freely licensed photos added from Wikimedia Commons. Each automated pick was reviewed visually:
  11 were rejected (billiards, a concert, a damaged ship, military aircraft, third-party branding, a
  duplicate and others).
- `tools/verify_assets.py`: 7 pages, 99 images, 58 icons, 157 asset references and 7 fallback tiles,
  all resolving.
- The QA suite gained a browser render check (every visible icon and image draws at non-zero size) and
  the new `/credits/` page.
- Final run: **269 passed, 0 failed**, with zero axe violations on all 6 pages at 375px and 1440px. One
  issue was found and fixed along the way: on mobile, screen-reader-only text inside the credits table
  caused sideways scrolling.

## Content and photo update (merged category, new services, labelled contact banner)

- Merged Handicrafts and Handmade felt into one category; added Branding and packaging (home), plus
  Quality check and inspection and Cargo handling, packaging and branding (services, form topics).
- Office address now reads "Kathmandu 44600, Nepal" everywhere, including Schema.org (`postalCode`).
- The Contact banner has Email, Phone and Message labels. A separate mobile composition keeps them
  legible at 375px, served with `<picture>`.
- Every product slot now has a real photo, with 0 fallback tiles: 50 photos, 4 of them from the
  company's own felt photos. All are tone-matched to the palette.
- `verify_assets.py`: 117 images, 50 icons and 176 asset references, all resolving. QA: **273 passed,
  0 failed**, with zero axe violations.

## Landline and sharper About banner

- Landline +977 1-5918009 (01-5918009 within Nepal) added beside Mobile / WhatsApp +977 974-031-8224 on
  the Contact page, the Contact banner, the footer and the call-to-action bands, and to Schema.org (a
  `telephone` array plus one `ContactPoint` per number). Phone links no longer wrap mid-number.
- The About banner was blurry because it was saved at 1600 px but shown about 1240 CSS px wide, which
  needs about 2480 device px on Retina screens. It is now Boudhanath Stupa (original 8224 × 5140), saved
  at 2400 × 1080 WebP, quality 88, with a 1200 px copy served via `srcset`. Checked: a 2× desktop loads
  the 2400 px file and a 2× phone loads the 1200 px file.
- `verify_assets.py`: OK. QA: **273 passed, 0 failed**, with zero axe violations.

## Services, form, map and photo update

- The hero map now has corridor badges (air, sea, road), a Kathmandu hub ring and gateway labels (shown
  on desktop; on phones the legend carries them). There are no overlaps at 375px or 1440px, and the
  legend reads "Nepal's routes to global market".
- "Your gateway to Nepal" appears under the company name in the header and footer.
- Services: Product Sourcing first, Quality Check and Control last, with Title Case names in every list.
- The contact form opens Gmail's compose window, with an instant confirmation and fallbacks. QA covers
  the Gmail URL (recipient, subject, body) and the fallback `mailto:` link.
- Address "Kathmandu, 44600, Nepal"; the reply note reads "We reply in all languages."
- The sourcing chain has 10 steps, with Sample approve and Feedback added.
- New photos: Patan Durbar Square and Annapurna (About gallery), Bhaktapur pots (home sourcing section)
  and a Thamel felt-goods shop (Product Sourcing). All were cropped from sources large enough that
  nothing is upscaled.

## Global-markets hero map

- Nepal is centred, with arrowed routes from Kathmandu to US, CAN, UK, EU, AUS and NZ. There are two
  compositions: wide with full country names (768px and up), and a taller phone version with large
  codes, so nothing is cropped. Checked at 375px (3×), 768px (2×) and 1440px: no text or arrow overlaps,
  and nothing is clipped.
- `verify_assets.py`: OK. QA: **275 passed, 0 failed**, with zero axe violations.

## Background form submission and Toys crop

- The form POSTs JSON to FormSubmit's AJAX endpoint. QA intercepts the request and checks the URL,
  JSON headers, payload (name, email, `_replyto`, topic, message, `_subject`, `_honey`), that no
  tab or popup opens, the confirmation, the form reset, and the failure path (error plus copy fallback,
  message kept). A real delivery test needs the one-time FormSubmit activation (see README).
- Fixed: `.btn-row` overrode the `hidden` attribute, so the copy fallback showed after a successful send.
  A global `[hidden]` rule now wins.
- The Toys photo is a tight crop on two reindeer: 2644×1983 source region downscaled to 480×360.
- QA: **281 passed, 0 failed**, with zero axe violations.

## Form delivery hardening

- The AJAX request now sends `FormData` (multipart, no preflight) with `Accept: application/json`. On a
  non-success reply or a network error, a hidden standard POST is sent into a hidden iframe, so the page
  never navigates. QA covers the success path, the activation-pending fallback, the network-failure
  fallback and the payload fields, all under the real CSP (with `frame-src https://formsubmit.co` added).
- QA: **288 passed, 0 failed**, with zero axe violations.

## Issues found during QA and fixed

| Issue | Fix |
|---|---|
| **Form button sometimes ignored the click.** Re-validating on blur removed an error line, the layout shifted between mouse-down and mouse-up, and the click was lost. | Errors are now added only on submit and cleared while typing (`input`/`change`), so nothing moves under the pointer. |
| The logo PNG's opaque white square showed as a box on ivory. | Display-only `border-radius: 50%` hides the white corners. The file is unchanged (checklist item 17). |
| The footer loaded the 291 KB original logo on every page. | Uses the identical 85 KB 512px version from the favicon pack. |
| Product tags were invisible: tint on a tint background. | Tags now use ivory. |
| The hero headline broke into 4 short lines at 1440px, leaving a gap. | Widened the headline column. |
| Sparse contours, and the map frame cut off southern Nepal. | Regenerated the map with denser contours and a corrected frame. |
| `upgrade-insecure-requests` was redundant and broke local HTTP testing. | Removed. HSTS and "Always Use HTTPS" cover it. |
| The deprecated `interest-cohort` Permissions-Policy entry causes a console warning in Chrome. | Removed. |
| Subheadings in About → "Our approach" were `<h2>` under an `<h2>`. | Changed to `<h3>`. |

## What could not be tested here (do these after deployment)

1. **Lighthouse was not run.** It needs Node.js, which is not installed in this environment, and
   downloading a portable Node was not permitted during this session. No Lighthouse scores are claimed.
   Run it after deploying:
   - Chrome → DevTools → **Lighthouse** → Mobile and Desktop, on each page; or
   - https://pagespeed.web.dev/ with the live URL; or
   - `npx lighthouse https://<domain>/ --view` on a machine with Node.js.

   Given the measured LCP/CLS, zero axe violations, zero console errors and complete metadata, strong
   scores are expected, but that is an expectation, not a result.
2. **Firefox via Playwright** could not start inside this sandbox (a macOS restriction on its helper
   process), so the automated suite ran in **Chromium only**. Firefox was checked visually with the
   system Firefox in headless mode; layouts matched Chromium.
3. **Safari / iOS / real devices** were not tested. Check on a real iPhone and Android phone after
   deploying, especially the mobile menu, the form, and `tel:` / WhatsApp links.
4. **A real email app** opening the `mailto:` link was not tested (headless browsers cannot open one).
   The generated URL was verified. Send one test inquiry from a desktop and a phone after launch.
5. **Cloudflare's own header handling:** `_headers` was tested with a local emulation. After the first
   deploy, confirm with `curl -sI https://<domain>/`.
6. **A real test inquiry** should be sent to the business email after launch, from both a desktop and a
   phone, to confirm delivery end to end.

## Re-running the tests

```bash
python3 tools/serve.py 8080 &
python3 -m venv .venv && .venv/bin/pip install playwright && .venv/bin/playwright install chromium
.venv/bin/python tools/qa_check.py --browsers chromium            # add --axe path/to/axe.min.js for the accessibility scan
```
