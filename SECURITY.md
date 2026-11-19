# Security

This document covers the security measures in the Nepal Shipping & Sourcing website, the external
services it touches, the hosting configuration it relies on, and its known limitations.

No website is completely secure. This one is designed to have a **very small attack surface**:
it is static files only, with no server code, database, login, cookies, analytics or third-party scripts.

## Measures implemented

### Architecture
- **Static site only.** HTML, CSS, one first-party JavaScript file, fonts and images. No server-side
  code runs, so there is no injection, authentication or session attack surface on the server.
- **No runtime dependencies.** No npm packages, frameworks, CDNs or tag managers. Everything shipped
  is first-party and served from the site's own origin.
- **Build tooling is standard-library Python** (`tools/build.py`, `tools/serve.py`,
  `tools/build_hero_map.py`), with no third-party packages. Playwright is used only for optional local
  QA (`tools/qa_check.py`, `tools/og/render_og.py`); it is never deployed.
- **No secrets.** There are no API keys, tokens or passwords anywhere in the project. The only contact
  details (business email and phone) are public by design and set in `site.config.json`.

### JavaScript (`site/assets/js/main.js`)
- No `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` or `new Function`.
  All dynamic text is set with `textContent`, and new elements are built with `createElement`.
- **URL parameters are allowlisted.** `?topic=` is accepted only if it matches a known key in the
  `TOPICS` object; anything else is ignored. `?review` only toggles a CSS class.
- **Form input is validated and sanitised:** fields are trimmed, control characters stripped, lengths
  capped (name 100, email 160, message 1,500 characters), the email format checked, and the topic
  checked against the allowlist. Values are placed in the `mailto:` URL only through
  `encodeURIComponent`, so they cannot inject extra headers or recipients.
- **Spam awareness:** a hidden honeypot field (`website`) silently drops automated submissions.
  Form data is sent only as JSON to the FormSubmit endpoint over HTTPS; the CSP allows no other destination.

### Personal data
- The form collects only what a reply needs: name, email and message are required; company and
  country are optional. Nothing is stored or transmitted by the website itself. The visitor's own
  email app sends the message.
- The form text asks visitors not to include passwords, card numbers or other sensitive data.
- No cookies, analytics, fingerprinting or third-party embeds (no maps, social widgets or video).
  `localStorage` is not used.

### Links
- The only off-site link is WhatsApp (`https://wa.me/…`). It opens in a new tab with
  `rel="noopener noreferrer"` and tells screen-reader users that it does.
- `mailto:` and `tel:` links are user-initiated.

## HTTP security headers (`site/_headers`)

Cloudflare Pages applies these to every response:

| Header | Value | Purpose |
|---|---|---|
| `Content-Security-Policy` | `default-src 'none'; script-src 'self' 'sha256-…'; style-src 'self'; img-src 'self'; font-src 'self'; manifest-src 'self'; connect-src 'self' https://formsubmit.co; form-action 'self' https://formsubmit.co; base-uri 'self'; frame-ancestors 'none'; object-src 'none'` | Only first-party resources can load. Blocks injected scripts, styles and plug-ins, and stops the site being framed. |
| `X-Content-Type-Options` | `nosniff` | Stops MIME sniffing. |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Sends only the origin to other sites. |
| `X-Frame-Options` | `DENY` | Clickjacking protection for older browsers (CSP `frame-ancestors` covers modern ones). |
| `Permissions-Policy` | camera, microphone, geolocation, payment, USB and sensors disabled | Denies powerful browser features the site never needs. |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isolates the browsing context from cross-origin pop-ups. |
| `Cross-Origin-Resource-Policy` | `same-origin` | Stops other sites embedding this site's assets. |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Forces HTTPS for a year after the first visit. |

**Notes on the CSP**
- **No `'unsafe-inline'`.** The one inline script (`document.documentElement.className="js"` in
  `src/partials/head.html`, which prevents the mobile menu flashing open on load) is allowed by its
  SHA-256 hash. If you change that line, recompute the hash (command in `_headers`) or the menu will
  briefly flash open on mobile.
- JSON-LD blocks (`<script type="application/ld+json">`) are data, not executable script, so the CSP
  does not block them.
- If you add a hosted form service, analytics, maps or any external resource, you **must** add its
  origin to the matching directive, or the browser will block it.
- `upgrade-insecure-requests` is deliberately left out: every resource is same-origin, and HSTS plus
  Cloudflare's "Always Use HTTPS" already enforce HTTPS.

**HSTS:** `includeSubDomains` assumes every subdomain will be HTTPS. `preload` is deliberately **not**
set. Only add it, and submit to hstspreload.org, once you are sure, because it is hard to undo.

## External services

| Service | Used for | Data shared |
|---|---|---|
| Cloudflare Pages | Hosting, TLS, CDN | Standard request logs held by Cloudflare |
| GitHub | Source repository | Site source code (keep the repository private if preferred) |
| WhatsApp (`wa.me`) | Optional contact link, only if the visitor clicks | Whatever the visitor chooses to send |
| FormSubmit (formsubmit.co) | Delivering inquiry-form messages to the business inbox | Name, email, company, country, topic and message the visitor submits |

No other third-party services are loaded. Fonts are self-hosted, so there are no Google Fonts requests.

## Dependency audit

- **Shipped site:** zero third-party dependencies, so there is nothing to audit for known vulnerabilities.
- **Build tools:** Python standard library only.
- **Optional QA tools (not deployed):** Playwright for Python. Keep it current with
  `pip install -U playwright` if you use it.
- **Font:** the Archivo variable font (SIL OFL) is a static WOFF2 file served from the site's own origin.

## Known limitations

- **Form delivery depends on FormSubmit:** messages pass through a third-party service, which must be activated once from the business inbox. If it is unavailable, visitors get an error and a copy-message fallback. The honeypot reduces, but does not eliminate, spam.
- **Public contact details:** the email and phone are shown in plain text and will attract some spam.
  That is the trade-off for a site with no backend. A hosted form service with spam filtering is the
  upgrade path (see README).
- **Header enforcement depends on hosting:** `_headers` is a Cloudflare Pages feature. If the site is
  ever hosted elsewhere, the same headers must be configured there.
- **Browser support:** the CSP hash and `frame-ancestors` need a modern browser. Older browsers get the
  `X-Frame-Options` fallback but less protection overall.
- **Account security is outside the code:** the biggest real risks are the GitHub, Cloudflare and
  domain-registrar accounts and the business inbox. See the checklist below.

## Deployment security checklist

- [ ] GitHub, Cloudflare, the domain registrar and the business email account all use strong unique
      passwords and **two-factor authentication**.
- [ ] Repository access is limited to people who need it. Branch protection is on for `main` if
      several people edit.
- [ ] The Cloudflare Pages project builds from `main` with output directory `site` and no build command.
- [ ] After the first deploy, `curl -sI https://<domain>/` shows the CSP, `X-Content-Type-Options`,
      `Referrer-Policy`, `X-Frame-Options` and `Strict-Transport-Security` headers.
- [ ] SSL/TLS mode is **Full (strict)**, and **Always Use HTTPS** is on.
- [ ] `www` redirects to the apex domain (or the other way round), so there is one canonical host.
- [ ] The browser console on each page shows no CSP violations.
- [ ] Domain auto-renewal and registrar lock are enabled. Registrar contact details are current.
- [ ] Optional: a DNS CAA record limiting certificate issuance to Cloudflare's certificate authorities.
- [ ] Optional: SPF, DKIM and DMARC records if the domain will send email.
- [ ] Re-run `tools/qa_check.py` (or at least check the console) after any change to `_headers`,
      `main.js` or the inline script.
