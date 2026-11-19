# Nepal Shipping & Sourcing — company website

A static, multi-page corporate website for **Nepal Shipping & Sourcing Pvt. Ltd.**:
international shipping, freight coordination and product sourcing from Nepal.

Plain HTML, CSS and vanilla JavaScript, with no runtime dependencies, no framework and no tracking.
It is deployed as static files on **Cloudflare Pages** from a GitHub repository.

> **Before launch:** work through [`COMPANY-CONTENT-CHECKLIST.md`](COMPANY-CONTENT-CHECKLIST.md).
> The 🔴 items include the phone country code, WhatsApp and service confirmation.

---

## Pages

| URL | Source | Purpose |
|-----|--------|---------|
| `/` | `src/pages/index.html` | Home: hero route map, introduction, services, sourcing, commitments, process, product categories, call to action |
| `/about/` | `src/pages/about.html` | Overview, mission, vision, values, approach, customer service commitment |
| `/services/` | `src/pages/services.html` | Seven freight services, each with an inquiry button |
| `/sourcing/` | `src/pages/sourcing.html` | Eight-step sourcing process, eight product categories, what to send us |
| `/contact/` | `src/pages/contact.html` | Contact details and the inquiry form (mailto-based) |
| `/404.html` | `src/pages/404.html` | Not-found page (served automatically by Cloudflare Pages) |

## Project structure

```
Nepal Shipping/
├── NSS_logo.png                 original logo — untouched
├── favicon.zip                  original favicon pack — untouched (extracted into site/)
├── site.config.json             ← company details + domain (single source of truth)
├── src/                         ← edit content here
│   ├── partials/                layout, <head>, header, footer; hero-map.html is generated
│   ├── pages/                   one file per page (body content + <!--meta {...}--> block)
│   └── assets/images/           illustrations + map artwork (copied to site/assets/images/)
│       └── photos/              Wikimedia Commons photos (WebP) + credits.json
├── site/                        ← the published website (Cloudflare Pages output directory)
│   ├── index.html, about/, services/, sourcing/, contact/, 404.html   (generated)
│   ├── sitemap.xml, robots.txt                                       (generated)
│   ├── _headers                 Cloudflare security + cache headers
│   ├── favicon.*, apple-touch-icon.png, site.webmanifest, web-app-manifest-*.png
│   └── assets/
│       ├── css/main.css         all styles (edit directly)
│       ├── js/main.js           menu, inquiry form, ?review mode (edit directly)
│       ├── fonts/               Archivo variable font (self-hosted, SIL Open Font Licence)
│       ├── images/              (generated copy of src/assets/images/; do not edit here)
│       └── img/                 NSS_logo.png (copy), icons.svg, og-image.png
├── tools/
│   ├── build.py                 assembles src/ → site/ (Python 3 standard library only)
│   ├── serve.py                 local preview server that applies _headers like Cloudflare
│   ├── build_hero_map.py        hero map, route overlay, contact banner (from tools/data/)
│   ├── build_illustrations.py   all other editorial illustrations (also photo fallbacks)
│   ├── fetch_photos.py          downloads + crops freely licensed photos (dev-only: Pillow)
│   ├── verify_assets.py         checks every image/icon in site/ resolves (run before deploy)
│   ├── data/nepal-adm0.geojson  Nepal boundary (geoBoundaries / Open Data Nepal, CC BY 4.0)
│   ├── qa_check.py              automated browser QA (optional, needs Playwright)
│   └── og/                      source + renderer for the social share image
├── README.md  SECURITY.md  COMPANY-CONTENT-CHECKLIST.md  TESTING-REPORT.md
```

**What is generated and what is hand-edited:** HTML pages, `sitemap.xml` and `robots.txt` are generated
by `tools/build.py`, so edit `src/` and rebuild. CSS, JS, images and `_headers` live directly in `site/`.

The generated `site/` folder is committed to Git, so Cloudflare Pages needs **no build step**.

## Editing

Requirements: Python 3.8+ (pre-installed on macOS). Nothing else.

```bash
# 1. Edit content in src/pages/*.html, shared parts in src/partials/*.html,
#    or company details in site.config.json
# 2. Rebuild the HTML
python3 tools/build.py
# 3. Preview locally with production headers (CSP etc.)
python3 tools/serve.py 8080          # → http://127.0.0.1:8080/
# 4. Commit and push; Cloudflare Pages redeploys automatically
```

### Business email

The business email is set in `site.config.json` (`"email"`) and used everywhere: the contact page,
footer, call-to-action bands, the inquiry form's `mailto:` target and Schema.org data. To change it,
edit that value and run `python3 tools/build.py`. If it is ever left empty, the build falls back to
the test address `inquiries@example.com` and prints a warning.

### Change the domain

Edit `site_url` in `site.config.json` and rebuild. This updates canonical tags, Open Graph URLs,
Schema.org data, `sitemap.xml` and `robots.txt` together.

### Content review mode

Add `?review` to any page URL to highlight every placeholder that still needs confirming.

### Photos and image credits

Photos come from Wikimedia Commons or Openverse under CC0, public domain, CC BY or CC BY-SA licences,
plus the company's own photos (`about_us1.JPG`, `about_us2.JPG` in the project root; the 20 MB originals
are git-ignored and only optimised WebP copies are committed), via `tools/fetch_photos.py` (dev-only
dependency: Pillow). Every photo is cropped to its slot, lightly tone-matched to the palette and saved
as WebP. Each slot in its `PHOTOS` list maps to a
`{{PHOTO:slot|alt text}}` marker in the page sources. If a slot has no photo, the build uses a designed
fallback (the matching illustration, or an icon tile), so a slot is never empty or broken.

CC BY and CC BY-SA require attribution. The `/credits/` page, generated from
`src/assets/images/photos/credits.json` and linked in the footer, provides it, so keep it published.
To replace a photo with your own, save it as `src/assets/images/photos/<slot>.webp` at the slot's size,
remove that slot from `credits.json`, re-run `fetch_photos.py` to refresh the credits table, then rebuild.

Every `/assets/` URL in the built HTML carries a content-hash `?v=` parameter, so browsers always get the
latest version of changed files (this is what fixes icons appearing blank after an update).

### Adding photography

The design works without photos. To add one, save an optimised image (WebP, about 1600px wide,
under 250 KB) in `site/assets/img/`, then reference it with explicit dimensions:

```html
<img src="/assets/img/felt-workshop.webp" width="1600" height="1067"
     alt="Artisans shaping felt balls in a workshop in Kathmandu" loading="lazy" decoding="async">
```

Images must be same-origin: the Content Security Policy blocks images from other domains.
Use `loading="lazy"` for anything below the first screen. Never hotlink stock images.

### Add or remove a service

1. Edit the `<article class="service">` block in `src/pages/services.html` and its "On this page" link.
2. Update the home-page list (`src/pages/index.html`) and the footer (`src/partials/footer.html`).
3. Update the `<select id="f-topic">` options in `src/pages/contact.html` **and** the `TOPICS`
   allowlist in `site/assets/js/main.js` (keys must match).
4. Run `python3 tools/build.py`.

## The inquiry form

The form sends inquiries **in the background** to the business inbox through
[FormSubmit](https://formsubmit.co). After validation, `main.js` POSTs JSON (`Content-Type` and `Accept:
application/json`) to `https://formsubmit.co/ajax/<business email>`, with name, email, company, country,
topic, message, `_subject` ("New Inquiry — Nepal Shipping & Sourcing"), `_replyto` (the visitor's
email) and the `_honey` honeypot. The button shows "Sending...", then the page confirms "Message sent!"
and resets the form. No tab, Gmail window or mail app opens. If the request fails, the visitor sees an
error and a "Copy message" fallback.

- **One-time activation (required):** the first submission to a new address makes FormSubmit send an
  "Activate Form" email to the business Gmail inbox. Click the link once. Until then, submissions are
  not delivered.
- The endpoint is built from `email` in `site.config.json`. The CSP allows `https://formsubmit.co` in
  `connect-src` and `form-action`.
- Without JavaScript, the form posts to FormSubmit's standard endpoint and shows its thank-you page.
- Inquiries pass through FormSubmit's servers on their way to the inbox (see SECURITY.md).

---

## Deployment: GitHub + Cloudflare Pages

> Nothing has been deployed and no DNS has been changed. These steps are for the site owner.

### 1. Put the project on GitHub

```bash
cd "Nepal Shipping"
git init
git add .
git commit -m "Initial website"
# Create an empty private repository on github.com, then:
git branch -M main
git remote add origin git@github.com:<your-account>/<repo-name>.git
git push -u origin main
```

`.gitignore` already excludes macOS `.DS_Store` files and Python caches.

### 2. Create the Cloudflare Pages project

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Select the repository.
3. Build settings:

   | Setting | Value |
   |---|---|
   | Framework preset | **None** |
   | Build command | *(leave empty)* |
   | Build output directory | **`site`** |
   | Root directory | *(leave empty)* |

4. **Save and Deploy.** You will get a `*.pages.dev` preview URL. Test it before adding the domain.

Cloudflare Pages automatically serves `about/index.html` at `/about/`, serves `404.html` for unknown
paths, and applies `site/_headers`.

### 3. Connect the custom domain

2. Pages project → **Custom domains** → **Set up a custom domain** → enter the apex domain
   (`nepalshippingandsourcing.com`).
3. If the domain's DNS is already on Cloudflare, the record is created for you. Otherwise follow the
   prompt: either move the nameservers to Cloudflare (recommended, required for an apex domain) or add
   the CNAME it shows at your current DNS provider.
4. Add `www.<domain>` as a second custom domain, then create a **Redirect Rule** (Rules → Redirect
   Rules) sending `www.<domain>/*` to `https://<domain>/${1}` with a 301 status, so there is one
   canonical host.
5. SSL/TLS → set the mode to **Full (strict)**, and turn on **Always Use HTTPS**.
6. Optional, once everything works: enable HSTS in the Cloudflare dashboard. The `_headers` file
   already sends `Strict-Transport-Security` for one year (without `preload`; see SECURITY.md).

### 4. After launch

- Check `https://<domain>/`, `/about/`, `/services/`, `/sourcing/`, `/contact/` and an unknown URL (should show the 404 page).
- Check the headers: `curl -sI https://<domain>/ | grep -iE "content-security|x-frame|referrer|x-content"`.
- Run Lighthouse (Chrome DevTools → Lighthouse) or [PageSpeed Insights](https://pagespeed.web.dev/).
- Submit `https://<domain>/sitemap.xml` in Google Search Console.
- Test the share preview with a social media link inspector.

## Testing locally

```bash
python3 tools/serve.py 8080
# optional automated QA (development only, never deployed):
python3 -m venv .venv && .venv/bin/pip install playwright && .venv/bin/playwright install chromium
.venv/bin/python tools/qa_check.py --browsers chromium
```

See [`TESTING-REPORT.md`](TESTING-REPORT.md) for the results from the final QA pass.

## Credits and licences

- Logo and favicons: supplied by the company.
- Font: [Archivo](https://fonts.google.com/specimen/Archivo) by Omnibus-Type, SIL Open Font Licence 1.1, self-hosted.
- Nepal boundary: [geoBoundaries](https://www.geoboundaries.org/) gbOpen NPL ADM0, sourced from
  Open Data Nepal, CC BY 4.0. It includes Nepal's official 2020 boundary (Kalapani, Lipulekh,
  Limpiyadhura). Attribution appears under the home-page map.
- Photographs: Wikimedia Commons contributors; see `/credits/` for each author and licence.
- Contour terrain (stylised, not survey data), illustrations, icons and all copy: created for this project.
  Regenerate with `python3 tools/build_hero_map.py` and `python3 tools/build_illustrations.py`,
  then `python3 tools/build.py`.
