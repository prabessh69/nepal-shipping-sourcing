# Company content checklist — verify before launch

Everything on this list is either an assumption, a placeholder, or a claim the company must
confirm. Item numbers match the `<!-- PLACEHOLDER/VERIFY/REVIEW (… #N) -->` comments in `src/`.

**Tip:** open any page with `?review` added to the address (e.g. `http://127.0.0.1:8080/contact/?review`)
to highlight every on-page placeholder in yellow.

Legend: 🔴 must resolve before launch · 🟠 should confirm before launch · 🟢 recommended improvement · ✅ resolved

## Identity and contact details

| # | Item | Current state | Where | Action |
|---|------|---------------|-------|--------|
| 1 | ✅ **Domain** | **Resolved.** Corrected to `nepalshippingandsourcing.com` and used in canonical tags, sitemap, robots.txt, Open Graph and Schema.org. | `site.config.json` → `site_url` | None. To change it again, edit `site_url` and run `python3 tools/build.py`. |
| 2 | 🔴 **Phone number format** | Supplied as `9740318224`. Displayed as `+977 974-031-8224`, dialled as `tel:+9779740318224` (Nepal country code assumed). | `site.config.json` → `phone_e164`, `phone_display` | Confirm the country code and preferred display format. |
| 3 | 🔴 **WhatsApp** | Links to `https://wa.me/9779740318224` (same number, assumed). | `site.config.json` → `whatsapp_url`; Contact page; footer | Confirm the number is active on WhatsApp, or remove the WhatsApp rows. |
| 4 | 🔴 **Office address** | Shows "Nepal" and "Full office address shared on request". Not included in Schema.org. | Contact page; footer | Provide the registered office address (street, city, district, postal code). Add it to the page and, once verified, to `organization_jsonld()` in `tools/build.py` as a `PostalAddress`. |
| 5 | 🟠 **Business hours and language** | Says "We reply to inquiries in English. Times are Nepal Time (UTC+5:45)." No hours listed. | Contact page | Confirm reply language(s) and add office hours if desired. |
| 14 | ✅ **Business email in the build** | **Resolved.** The business email from the brief is set in `site.config.json` and built into every page and the inquiry form. | `site.config.json` → `email` | None. |
| 15 | 🟢 **Social media accounts** | None shown. None were supplied and none have been invented. | — | Supply official profile URLs if you want them linked (footer + Schema.org `sameAs`). |
| 16 | 🟢 **Company registration details** | Not shown. | Footer | Optional: company registration number, PAN/VAT number, if you want them displayed. |

## Company story and claims

| # | Item | Current state | Where | Action |
|---|------|---------------|-------|--------|
| 6 | 🟠 **Founding year** | "Established in 2018" — taken from the logo text "Estd. 2018AD". Not included in Schema.org. | About page | Confirm the year. If correct, it can also be added as `foundingDate` in Schema.org. |
| 7 | 🟠 **Overview, mission, vision, values** | Original copy written for this site; no history, team or achievements invented. | About page | Approve or edit the wording. Add real history, leadership or team details if you want them shown. |
| 12 | 🟠 **Client commitments** | Home page "How we work with clients": one accountable contact, written itemised quotes, milestone updates, straight answers. The same commitments appear on the About page. | Home, About | Confirm the company can keep these promises on every job, or edit them. |
| 20 | 🟢 **Route map** | The hero map is an original illustration: an approximate outline of Nepal with generated contour lines, plus indicative air, sea and road routes (Kathmandu air cargo, Indian seaports, southern border crossings). Labelled "Illustration, not to scale". | Home hero; `tools/build_hero_map.py` | Confirm you are comfortable with the indicative routes, which describe how Nepal's trade generally moves rather than specific company routes. |

## Services (all must be confirmed)

| # | Item | Current state | Action |
|---|------|---------------|--------|
| 8 | 🔴 **Each listed service** | Air freight, sea freight (FCL/LCL via Indian seaports), land transport (including cross-border), freight forwarding, import and export assistance, customs coordination (through licensed agents), cargo handling and packing. Each is described as *coordination*, with no claims of owned fleets, warehouses, licences or partnerships. | Confirm each service and its bullet points on `/services/`. Remove or edit any that are not offered. If one is removed, also delete it from the home-page service list, the footer, the contact form topics (`src/pages/contact.html`) and `TOPICS` in `site/assets/js/main.js`. |
| 9 | 🔴 **Door-to-door shipping** | **Not published.** Left out on purpose because it was unconfirmed. A commented-out note marks where it would go in `src/pages/services.html`. | If confirmed, add the block, the "On this page" entry and a form topic. |

## Sourcing

| # | Item | Current state | Action |
|---|------|---------------|--------|
| 10 | 🔴 **Sourcing capabilities** | Eight steps on `/sourcing/`: supplier identification, supplier verification (registration and capacity checks, "wherever possible" workshop visits), product sourcing, sample coordination, production monitoring, quality inspection (with photos), packaging coordination, export and shipping. A six-item summary appears on the home page. | Confirm each step, especially workshop visits and photo inspection reports. |
| 11 | 🔴 **Product categories and examples** | Handicrafts, handmade felt, herbs and spices, agricultural products, food and beverages, apparel and textiles, home decor, other custom requirements. Example items include singing bowls, thangka, felt balls, timur pepper, orthodox tea, large cardamom, pashmina, hemp, dhaka, lokta paper and others. | Confirm which categories you actually source, and remove any item the company cannot supply (for example regulated herbs). |
| 21 | 🟠 **Compliance note** | States that food, herbs and plant materials may need permits, certificates or tests, and that the company will advise. | Confirm the company gives this advice. |

## Imagery and brand assets

| # | Item | Current state | Action |
|---|------|---------------|--------|
| 13 | 🟠 **Commercial photography** | No photographs are used. The project folder had none, and no stock photos were downloaded. Visuals are the original contour-map illustration, line icons and typography. | Commission or license real photos (see the list below), then add them as described under "Adding photography" in README.md. |
| 17 | 🟢 **Logo presentation** | `NSS_logo.png` is unmodified (byte-identical copy in `site/assets/img/`). The header and footer use the 192px and 512px versions that came in `favicon.zip`. Because the PNG has an opaque white square background, CSS `border-radius: 50%` hides the white corners on ivory; the artwork's outer ring sits inside that circle, so nothing is cut. | Approve, or supply a transparent-background PNG/SVG version of the logo (preferred), then remove the radius rule in `main.css`. |
| 18 | 🟢 **Social share image** | `site/assets/img/og-image.png` (1200×630): logo plus contour plate plus company name. Source file: `tools/og/og-image.html`. | Approve, or replace with a branded photo. |
| 19 | 🟢 **Favicon / web app manifest** | Files extracted from `favicon.zip` unchanged, except `site.webmanifest`: its generator defaults ("MyWebSite", white theme colour) were replaced with the company name and ivory brand colour. | None required. |

### Photography wanted (priority order)

All photos should be the company's own, or properly licensed for commercial use. Avoid images that suggest facilities, vehicles or partnerships the company does not have.

1. **Home hero, optional photographic alternative to the map:** cargo being loaded or cartons staged for export in Nepal.
2. **About page:** the team or the office (only if real).
3. **Services, one per service:** an air cargo pallet at Tribhuvan International Airport; container loading or trucks at a border point; export cartons being packed and marked; documentation work.
4. **Sourcing, one per category:** a felt workshop, metalwork or singing bowls, a tea garden, spices drying, pashmina or hemp weaving, lokta paper making.
5. **Sourcing process:** a supplier visit, quality inspection against a sample, packing.

## Recommended additions (not blockers)

- 🟢 **Privacy notice page:** the site sets no cookies and has no analytics or server-side form storage, but a short privacy notice is good practice for an inquiry form.
- 🟢 **Google Search Console / Bing Webmaster Tools:** verify the domain after launch and submit `sitemap.xml`.
- 🟢 **Real Lighthouse run:** after deployment, run Lighthouse against the live URL (see TESTING-REPORT.md).
