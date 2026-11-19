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
| 2 | ✅ **Phone numbers** | **Resolved.** Landline **+977 1-5918009** (01-5918009 within Nepal, `tel:+97715918009`) and Mobile / WhatsApp **+977 974-031-8224** (`tel:+9779740318224`), confirmed by the company. Shown on the Contact page, the Contact banner, the footer and the call-to-action bands, and in Schema.org as a `telephone` array with one `ContactPoint` per number. | `site.config.json` → `landline_*`, `phone_*` | None. |
| 3 | ✅ **WhatsApp** | **Resolved.** The company confirmed +977 974-031-8224 as its Mobile / WhatsApp number. It links to `https://wa.me/9779740318224`. | `site.config.json` → `whatsapp_url` | None. |
| 4 | ✅ **Office address** | **Resolved.** Shown as "Kathmandu, 44600, Nepal" on the Contact page and in the footer, and included in Schema.org as a `PostalAddress` (locality Kathmandu, postal code 44600, country `NP`). | `site.config.json` → `address` | None. |
| 5 | 🟠 **Business hours** | The Contact page says "We reply in all languages. Times are Nepal Time (UTC+5:45)." No office hours are listed yet. | Contact page | Add office hours if you want them shown. |
| 14 | ✅ **Business email in the build** | **Resolved.** The business email from the brief is set in `site.config.json` and built into every page and the inquiry form. | `site.config.json` → `email` | None. |
| 15 | 🟢 **Social media accounts** | None shown. None were supplied and none have been invented. | — | Supply official profile URLs if you want them linked (footer + Schema.org `sameAs`). |
| 16 | 🟢 **Company registration details** | Not shown. | Footer | Optional: company registration number, PAN/VAT number, if you want them displayed. |

## Company story and claims

| # | Item | Current state | Where | Action |
|---|------|---------------|-------|--------|
| 6 | 🟠 **Founding year** | "Established in 2018" — taken from the logo text "Estd. 2018AD". Not included in Schema.org. | About page | Confirm the year. If correct, it can also be added as `foundingDate` in Schema.org. |
| 7 | 🟠 **Overview, mission, vision, values** | Original copy written for this site; no history, team or achievements invented. | About page | Approve or edit the wording. Add real history, leadership or team details if you want them shown. |
| 12 | 🟠 **Client commitments** | Home page "How we work with clients": one accountable contact, written itemised quotes, milestone updates, straight answers. The same commitments appear on the About page. | Home, About | Confirm the company can keep these promises on every job, or edit them. |
| 20 | 🟠 **Home map** | Nepal is drawn from real boundary data (geoBoundaries / Open Data Nepal, CC BY 4.0), including the official 2020 boundary through Kalapani, Lipulekh and Limpiyadhura, which India disputes. Arrowed routes run from the Kathmandu hub to US, CAN, UK, EU, AUS and NZ. Destinations are schematic (direction, not distance), and the legend says so. | Home hero; `tools/build_hero_map.py` (`MARKETS`) | Confirm these are your target markets. Add or remove entries in `MARKETS` and rebuild. |

## Services (all must be confirmed)

| # | Item | Current state | Action |
|---|------|---------------|--------|
| 8 | 🔴 **Each listed service** | In order: Product Sourcing, Air Freight, Sea Freight, Land Transport, Freight Forwarding, Import and Export Assistance, Customs Coordination, Cargo Handling, Packaging and Branding, Quality Check and Control (pre-shipment inspection with photo/video reports). All are described as coordination, with no claims of owned fleets, warehouses, licences or partnerships. | Confirm each service. To remove one, also delete it from the home-page list, the footer, the contact form topics (`src/pages/contact.html`) and `TOPICS` in `site/assets/js/main.js`. |
| 9 | 🔴 **Door-to-door shipping** | **Not published.** Left out on purpose because it was unconfirmed. A commented-out note marks where it would go in `src/pages/services.html`. | If confirmed, add the block, the "On this page" entry and a form topic. |

## Sourcing

| # | Item | Current state | Action |
|---|------|---------------|--------|
| 10 | 🔴 **Sourcing steps** | Ten steps on `/sourcing/`: identify, verify, quote, sample, sample approve, monitor, inspect, pack, ship, feedback. A seven-item summary on the home page includes Branding and packaging. | Confirm each step, especially workshop visits, photo inspection reports and post-delivery feedback. |
| 11 | 🔴 **Product categories and examples** | Seven categories: **Handicrafts & handmade felt** (merged), herbs and spices, agricultural products, food and beverages, apparel and textiles, home decor, other custom requirements. Example items are shown with photos. The **Pet products** photo is a close crop of a felt dog figure from the company's own photo `about_us2.JPG`, not an actual pet product such as a felt cat cave. | Confirm which categories and items you source. Replace the Pet products photo with a photo of real felt pet products if you have one. |
| 21 | 🟠 **Compliance note** | States that food, herbs and plant materials may need permits, certificates or tests, and that the company will advise. | Confirm the company gives this advice. |

## Imagery and brand assets

| # | Item | Current state | Action |
|---|------|---------------|--------|
| 13 | 🟠 **Photography** | 50 photos. 46 are freely licensed Wikimedia Commons / Openverse photos, credited on `/credits/`; they show products and freight in general, not the company's own premises, vehicles or partners. 4 come from the company's own felt photos (`about_us1.JPG`, `about_us2.JPG`), used on the About gallery, the Handicrafts & handmade felt card, and the Toys and Pet products items. All photos were cropped and lightly tone-matched to the site palette. No icon placeholders remain. | Confirm the company owns the rights to `about_us1.JPG` / `about_us2.JPG` and that the felt figures shown are products you source. Replace stock photos with your own over time. |
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
