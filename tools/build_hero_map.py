#!/usr/bin/env python3
"""Generate the map artwork from real boundary data.

    python3 tools/build_hero_map.py

Inputs
  tools/data/nepal-adm0.geojson   Nepal national boundary (geoBoundaries / Open Data
                                  Nepal, CC BY 4.0). Includes Nepal's official 2020
                                  boundary through Kalapani, Lipulekh and Limpiyadhura.
Outputs
  src/assets/images/hero-terrain.svg    terrain plate: outline + contour lines
  src/partials/hero-map.html            inline SVG overlay: routes, markers, labels
  src/assets/images/banner-contact.svg  Contact page banner

The outline and city positions are geographically accurate (equirectangular
projection, cos-latitude corrected). The contour lines are a stylised terrain
model shaped by the real border (flat southern plains rising to the northern
Himalaya, with a dip at the Kathmandu valley). They are not survey elevation
data. Standard library only.
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data" / "nepal-adm0.geojson"
IMG = ROOT / "src" / "assets" / "images"
PARTIAL = ROOT / "src" / "partials" / "hero-map.html"

RING = json.loads(DATA.read_text())["features"][0]["geometry"]["coordinates"][0]

# Real-world positions (lon, lat)
KATHMANDU = (85.3240, 27.7172)
BIRGUNJ = (84.8770, 27.0120)      # Birgunj–Raxaul: main road + rail customs point
BHAIRAHAWA = (83.4480, 27.5050)   # Bhairahawa–Sunauli
BIRATNAGAR = (87.2718, 26.4525)   # Biratnagar–Jogbani

# Colours
FOREST, FOREST_RAISED, IVORY, ROSE, CRIMSON, MIST = "#16221C", "#1D2E25", "#FAF7F2", "#F2A7B4", "#C8102E", "#A9C2B2"


class Projection:
    def __init__(self, width, height, scale, lon_c, lat_c, ref_lat=28.2):
        self.w, self.h, self.s = width, height, scale
        self.k = math.cos(math.radians(ref_lat))
        self.lon0 = lon_c - width / 2 / (scale * self.k)
        self.lat_top = lat_c + height / 2 / scale

    def __call__(self, lon, lat):
        return ((lon - self.lon0) * self.k * self.s, (self.lat_top - lat) * self.s)

    def inverse(self, x, y):
        return (x / (self.k * self.s) + self.lon0, self.lat_top - y / self.s)


def outline_path(proj, ring=RING):
    pts = [proj(lon, lat) for lon, lat in ring]
    return "M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in pts) + "Z"


# ---------- terrain model ----------
rng = random.Random(2018)
G = 64
PERM = [[rng.random() for _ in range(G)] for _ in range(G)]


def vnoise(x, y):
    xi, yi = math.floor(x), math.floor(y)
    xf, yf = x - xi, y - yi
    a, b = PERM[yi % G][xi % G], PERM[yi % G][(xi + 1) % G]
    c, d = PERM[(yi + 1) % G][xi % G], PERM[(yi + 1) % G][(xi + 1) % G]
    u, v = xf * xf * (3 - 2 * xf), yf * yf * (3 - 2 * yf)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def fbm(x, y, octaves=5):
    t, amp, f = 0.0, 0.5, 1.0
    for _ in range(octaves):
        t += amp * vnoise(x * f, y * f)
        amp *= 0.5
        f *= 2.03
    return t


def border_span(lon):
    """South and north latitude of Nepal's border along a meridian."""
    ys = []
    n = len(RING)
    for i in range(n - 1):
        (x1, y1), (x2, y2) = RING[i], RING[i + 1]
        if (x1 <= lon < x2) or (x2 <= lon < x1):
            ys.append(y1 + (lon - x1) * (y2 - y1) / (x2 - x1))
    if len(ys) < 2:
        return None
    return min(ys), max(ys)


# Border span per 0.01° of longitude, then smoothed (±0.3°) so sharp notches in
# the border don't create vertical cliffs in the terrain model.
RAW = [border_span(79.6 + k * 0.01) for k in range(900)]
known = [k for k, v in enumerate(RAW) if v]
for k in range(900):
    if RAW[k] is None:
        RAW[k] = RAW[min(known, key=lambda kk: abs(kk - k))]
SPANS = []
for k in range(900):
    win = RAW[max(0, k - 30):k + 31]
    SPANS.append((sum(v[0] for v in win) / len(win), sum(v[1] for v in win) / len(win)))


def span_for(lon):
    return SPANS[max(0, min(899, round((lon - 79.6) / 0.01)))]


def elevation(lon, lat):
    south, north = span_for(lon)
    t = (lat - south) / max(0.6, north - south)          # 0 at southern border, 1 at northern
    base = 0.04 if t < 0.12 else (min(t, 1.15) - 0.12) ** 1.45 * 1.05   # flat Terai, steep north
    n = fbm(lon * 2.2, lat * 2.2)
    ridges = 1 - abs(2 * fbm(lon * 3.6 + 9, lat * 3.6 + 3) - 1)
    e = base + n * 0.28 + ridges * max(0, t) * 0.32
    # Kathmandu valley: a bowl inside the hills
    dk = ((lon - KATHMANDU[0]) * 1.4) ** 2 + (lat - KATHMANDU[1]) ** 2
    e -= 0.32 * math.exp(-dk / 0.018)
    return e


def noise_elevation(lon, lat):
    """Plain noise field for the faint terrain outside Nepal."""
    return fbm(lon * 1.6 + 40, lat * 1.6 + 11)


def contours(proj, step, levels, fn=None):
    fn = fn or elevation
    cols, rows = int(proj.w / step) + 2, int(proj.h / step) + 2
    field = []
    for j in range(rows):
        row = []
        for i in range(cols):
            lon, lat = proj.inverse(i * step, j * step)
            row.append(fn(lon, lat))
        field.append(row)
    out = {}
    for lv in levels:
        segs = []
        for j in range(rows - 1):
            for i in range(cols - 1):
                v = (field[j][i], field[j][i + 1], field[j + 1][i + 1], field[j + 1][i])
                inside = [val > lv for val in v]
                if all(inside) or not any(inside):
                    continue
                x0, y0 = i * step, j * step
                corners = [(x0, y0), (x0 + step, y0), (x0 + step, y0 + step), (x0, y0 + step)]

                def edge(e):
                    a, b = e, (e + 1) % 4
                    t = 0.5 if v[b] == v[a] else (lv - v[a]) / (v[b] - v[a])
                    (ax, ay), (bx, by) = corners[a], corners[b]
                    return (round(ax + (bx - ax) * t), round(ay + (by - ay) * t))

                cross = [e for e in range(4) if inside[e] != inside[(e + 1) % 4]]
                if len(cross) == 2:
                    segs.append((edge(cross[0]), edge(cross[1])))
                else:
                    segs += [(edge(0), edge(1)), (edge(2), edge(3))]
        out[lv] = join(segs)
    return out


def join(segs):
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    used, lines = set(), []
    key = lambda p, q: (p, q) if p < q else (q, p)
    for a, b in segs:
        if key(a, b) in used:
            continue
        used.add(key(a, b))
        line = [a, b]
        for forward in (True, False):
            while True:
                end = line[-1] if forward else line[0]
                nxt = next((c for c in adj.get(end, []) if key(end, c) not in used), None)
                if nxt is None:
                    break
                used.add(key(end, nxt))
                line.append(nxt) if forward else line.insert(0, nxt)
        if len(line) >= 5:
            lines.append(line[::2] + ([line[-1]] if len(line) % 2 == 0 else []))
    return lines


def path_d(lines):
    return "".join("M" + "L".join(f"{x:g} {y:g}" for x, y in ln) for ln in lines)


def terrain_groups(proj, step, n_levels, start, gap, outer_levels=0):
    levels = [round(start + k * gap, 3) for k in range(n_levels)]
    cs = contours(proj, step, levels)
    inner = []
    for k, lv in enumerate(levels):
        d = path_d(cs[lv])
        if d:
            major = k % 5 == 0
            inner.append(f'<path d="{d}" stroke-width="{1.3 if major else 0.7}" opacity="{0.95 if major else 0.55}"/>')
    outer = []
    if outer_levels:
        olv = [round(0.3 + k * 0.05, 3) for k in range(outer_levels)]
        ocs = contours(proj, step * 2, olv, noise_elevation)
        outer = [f'<path d="{path_d(ocs[lv])}"/>' for lv in olv if ocs[lv]]
    return "".join(inner), "".join(outer)


# ---------- route geometry helpers ----------
def _sample(d, t):
    """Point and unit direction at fraction t (by length) along an M/C/L path string."""
    import re as _re
    toks = _re.findall(r"[MCL]|-?\d+(?:\.\d+)?", d)
    pts, i, cur, cmd = [], 0, None, None
    while i < len(toks):
        if toks[i] in "MCL":
            cmd = toks[i]; i += 1; continue
        if cmd == "M":
            cur = (float(toks[i]), float(toks[i + 1])); pts.append(cur); i += 2
        elif cmd == "L":
            cur = (float(toks[i]), float(toks[i + 1])); pts.append(cur); i += 2
        elif cmd == "C":
            c1 = (float(toks[i]), float(toks[i + 1])); c2 = (float(toks[i + 2]), float(toks[i + 3]))
            end = (float(toks[i + 4]), float(toks[i + 5])); i += 6
            for k in range(1, 41):
                u = k / 40
                pts.append(tuple((1 - u) ** 3 * cur[j] + 3 * (1 - u) ** 2 * u * c1[j] + 3 * (1 - u) * u * u * c2[j] + u ** 3 * end[j] for j in (0, 1)))
            cur = end
    seg = [math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1)]
    target, acc = sum(seg) * t, 0.0
    for k, L in enumerate(seg):
        if acc + L >= target:
            f = (target - acc) / L if L else 0
            (x1, y1), (x2, y2) = pts[k], pts[k + 1]
            return (x1 + (x2 - x1) * f, y1 + (y2 - y1) * f), ((x2 - x1) / (L or 1), (y2 - y1) / (L or 1))
        acc += L
    return pts[-1], (0, 1)


def _at_y(d, y_target):
    """First point along the path whose y reaches y_target (used to keep badges inside the frame)."""
    for k in range(1, 400):
        pt, _ = _sample(d, k / 400)
        if pt[1] >= y_target:
            return pt
    return _sample(d, 0.8)[0]


MODE_GLYPH = {  # drawn in a 24-unit box centred on 0,0
    "air": '<path d="M0-10c1 0 1.6 1 1.6 2v4.6l8 4.4v2.2l-8-2.4v4.8l2.3 1.7v1.6L0 18l-3.9 1v-1.6l2.3-1.7V10.8l-8 2.4V11l8-4.4V-8c0-1 .6-2 1.6-2z" transform="translate(0 -4)"/>',
    "sea": '<path d="M-11 3h22l-3 6.5h-16z"/><path d="M-7 3v-5h4v5M-1.5 3v-8h4v8M4 3v-5h4v5"/>',
    "road": '<path d="M-11-6h12v11h-12zM1-2h5l4 4v3H1z"/><circle cx="-6" cy="7" r="2.2"/><circle cx="5" cy="7" r="2.2"/>',
}


def corridor_badge(pt, mode, label=None, anchor="start", dx=34, dy=7):
    x, y = pt
    out = (f'<g class="route-map__badge route-map__badge--{mode}" transform="translate({x:.0f} {y:.0f})">'
           f'<circle r="25"/><g class="route-map__glyph" transform="scale(1.25)">{MODE_GLYPH[mode]}</g></g>')
    if label:
        out += f'<text class="route-map__corridor" x="{x + dx:.0f}" y="{y + dy:.0f}" text-anchor="{anchor}">{label}</text>'
    return out


# ---------- outputs ----------
def hero():
    W, H = 1600, 760
    proj = Projection(W, H, scale=138, lon_c=84.13, lat_c=28.41)
    outline = outline_path(proj)
    inner, outer = terrain_groups(proj, 6, 28, 0.10, 0.045, outer_levels=5)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<!-- Boundary: geoBoundaries / Open Data Nepal (CC BY 4.0). Contours: stylised, generated by tools/build_hero_map.py -->
<defs><clipPath id="np"><path d="{outline}"/></clipPath></defs>
<rect width="{W}" height="{H}" fill="{FOREST}"/>
<g fill="none" stroke="#6E8577" stroke-width="0.8" opacity="0.2">{outer}</g>
<path d="{outline}" fill="{FOREST_RAISED}"/>
<g clip-path="url(#np)" fill="none" stroke="{MIST}">{inner}</g>
<path d="{outline}" fill="none" stroke="{ROSE}" stroke-width="2.2" stroke-linejoin="round"/>
</svg>
'''
    (IMG / "hero-terrain.svg").write_text(svg)

    ktm, bir, bhr, brt = proj(*KATHMANDU), proj(*BIRGUNJ), proj(*BHAIRAHAWA), proj(*BIRATNAGAR)
    f = lambda p: f"{p[0]:.0f} {p[1]:.0f}"
    kx, ky = ktm
    routes = {
        # Air: Tribhuvan International Airport, Kathmandu, out to the world
        "air-w": f"M{f(ktm)}C{kx-30:.0f} {ky-330:.0f} {kx-420:.0f} {ky-500:.0f} -20 {ky-430:.0f}",
        "air-e": f"M{f(ktm)}C{kx+110:.0f} {ky-250:.0f} {kx+380:.0f} {ky-420:.0f} 1620 {ky-460:.0f}",
        # Ocean freight: Kathmandu -> Birgunj/Raxaul -> south to Kolkata/Haldia
        "sea": f"M{f(ktm)}C{kx-10:.0f} {ky+40:.0f} {bir[0]+20:.0f} {bir[1]-50:.0f} {f(bir)}"
               f"C{bir[0]+30:.0f} {bir[1]+50:.0f} {bir[0]+120:.0f} {H-30} {bir[0]+175:.0f} {H+30}",
        # Road and rail: Kathmandu -> Bhairahawa/Sunauli and -> Biratnagar/Jogbani
        "road-w": f"M{f(ktm)}C{kx-90:.0f} {ky+50:.0f} {bhr[0]+90:.0f} {bhr[1]-30:.0f} {f(bhr)}L{bhr[0]-10:.0f} {H+30}",
        "road-e": f"M{f(ktm)}C{kx+110:.0f} {ky+40:.0f} {brt[0]-120:.0f} {brt[1]-70:.0f} {f(brt)}L{brt[0]+10:.0f} {H+30}",
    }
    order = [("air-w", "air"), ("air-e", "air"), ("sea", "sea"), ("road-w", "road"), ("road-e", "road")]
    masks = "\n".join(
        f'              <mask id="m{i}" maskUnits="userSpaceOnUse"><path class="reveal reveal--{i}" pathLength="1" d="{routes[k]}"/></mask>'
        for i, (k, _) in enumerate(order, 1))
    paths = "\n".join(
        f'            <g class="route route--{kind}"><path mask="url(#m{i})" d="{routes[k]}"/></g>'
        for i, (k, kind) in enumerate(order, 1))

    badges = "".join([
        corridor_badge(_sample(routes["air-w"], 0.58)[0], "air", "Global air hubs", "end", -34),
        corridor_badge(_sample(routes["air-e"], 0.6)[0], "air"),
        corridor_badge(_at_y(routes["sea"], 680), "sea", "Kolkata &amp; Haldia", "end", -34),
        corridor_badge(_at_y(routes["road-w"], 680), "road"),
        corridor_badge(_at_y(routes["road-e"], 690), "road", "India road &amp; rail"),
    ])

    def town(p, name, dx, anchor="start"):
        return (f'<circle cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="6"/>'
                f'<text class="route-map__town" x="{p[0]+dx:.0f}" y="{p[1]+6:.0f}" text-anchor="{anchor}">{name}</text>')

    partial = f'''          <svg class="route-map" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" role="img" aria-labelledby="map-title map-desc">
            <title id="map-title">Contour map of Nepal with outbound freight routes</title>
            <desc id="map-desc">Map of Nepal drawn from official boundary data, including Kalapani, Lipulekh and Limpiyadhura in the northwest. Dotted air routes leave Kathmandu to the west and east. A long-dash ocean-freight route runs from Kathmandu to the Birgunj border crossing and south toward the Indian seaports. Short-dash road and rail routes run from Kathmandu to the Bhairahawa and Biratnagar border crossings.</desc>
            <image href="/assets/images/hero-terrain.svg" width="{W}" height="{H}"/>
            <defs>
{masks}
            </defs>
{paths}
            <g class="route-map__points">{town(bir, "Birgunj", 14)}{town(bhr, "Bhairahawa", -14, "end")}{town(brt, "Biratnagar", 14)}</g>
            <g class="route-map__badges">{badges}</g>
            <circle class="route-map__hub" cx="{kx:.0f}" cy="{ky:.0f}" r="22"/>
            <circle class="route-map__origin" cx="{kx:.0f}" cy="{ky:.0f}" r="10"/>
            <text class="route-map__label" x="{kx+22:.0f}" y="{ky-14:.0f}">Kathmandu</text>
          </svg>
'''
    PARTIAL.write_text("<!-- Generated by tools/build_hero_map.py; do not edit by hand. -->\n" + partial)
    return proj


CONFIG = json.loads((ROOT / "site.config.json").read_text())
LABEL_FONT = 'font-family="Arial, Helvetica, sans-serif"'
BADGE_ICON = {
    "mail": '<rect x="-22" y="-15" width="44" height="30" rx="2"/><path d="M-21 -13l21 15 21-15"/>',
    "phone": '<path d="M-14 -20h8l4 11-5 4a26 26 0 0 0 15 15l4-5 11 4v8a4 4 0 0 1-4 4A38 38 0 0 1-18 -16a4 4 0 0 1 4-4z"/>',
    "chat": '<path d="M-22 -16h44v26H-4l-14 10v-10h-4z"/><path d="M-12 -5h24M-12 3h14"/>',
}


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


def _badge(x, y, name, r=46):
    return (f'<g transform="translate({x} {y})"><circle r="{r}" fill="{IVORY}"/>'
            f'<g fill="none" stroke="{FOREST}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round">{BADGE_ICON[name]}</g></g>')


def _label(x, y, lines, anchor="start", sizes=(30, 22)):
    """Title line in ivory, detail lines in rose; both high-contrast on forest green."""
    out = []
    for i, text in enumerate(lines):
        size = sizes[0] if i == 0 else sizes[1]
        colour, weight = (IVORY, 700) if i == 0 else (ROSE, 400)
        dy = 0 if i == 0 else sizes[0] * 0.25 + (sizes[1] * 1.35) * i
        out.append(f'<text x="{x}" y="{y + dy:.0f}" text-anchor="{anchor}" {LABEL_FONT} font-size="{size}" '
                   f'font-weight="{weight}" fill="{colour}">{_esc(text)}</text>')
    return "".join(out)


def _pin(kx, ky):
    return (f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="64" fill="{CRIMSON}" opacity=".16"/>'
            f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="36" fill="{CRIMSON}" opacity=".3"/>'
            f'<path d="M{kx:.0f} {ky:.0f}c-6-14-24-28-24-46a24 24 0 0 1 48 0c0 18-18 32-24 46z" fill="{CRIMSON}" stroke="{IVORY}" stroke-width="3" transform="translate(0 -4)"/>'
            f'<circle cx="{kx:.0f}" cy="{ky - 54:.0f}" r="8.5" fill="{IVORY}"/>')


def _map_layer(proj, W, H, step, levels):
    outline = outline_path(proj)
    inner, _ = terrain_groups(proj, step, levels, 0.10, 1.2 / levels)
    return (f'<defs><clipPath id="np"><path d="{outline}"/></clipPath></defs>'
            f'<rect width="{W}" height="{H}" fill="{FOREST}"/>'
            f'<path d="{outline}" fill="{FOREST_RAISED}"/>'
            f'<g clip-path="url(#np)" fill="none" stroke="{MIST}" opacity=".8">{inner}</g>'
            f'<path d="{outline}" fill="none" stroke="{ROSE}" stroke-width="2.4" stroke-linejoin="round"/>')


def contact_banner():
    email, phone, landline = CONFIG.get("email") or "Email", CONFIG["phone_display"], CONFIG["landline_display"]
    user, _, domain = email.partition("@")

    # Desktop / tablet: 1600 x 720. Badges sit in the corners, labels clear of the map.
    W, H = 1600, 720
    proj = Projection(W, H, scale=104, lon_c=84.35, lat_c=28.35)
    kx, ky = proj(*KATHMANDU)
    nodes = [(150, 120, "mail"), (150, 540, "phone"), (1450, 540, "chat")]
    links = "".join(f'<path d="M{kx:.0f} {ky:.0f}Q{(kx + x) / 2:.0f} {min(ky, y) - 120:.0f} {x} {y}"/>' for x, y, _ in nodes)
    labels = (_label(104, 206, ["Email", user, "@" + domain]) +
              _label(104, 610, ["Phone", landline, phone]) +
              _label(1496, 610, ["Message", "WhatsApp / chat"], anchor="end"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
           '<!-- Boundary: geoBoundaries / Open Data Nepal (CC BY 4.0). Generated by tools/build_hero_map.py -->'
           + _map_layer(proj, W, H, 7, 16)
           + f'<g fill="none" stroke="{ROSE}" stroke-width="3" stroke-dasharray="2 10" stroke-linecap="round">{links}</g>'
           + "".join(_badge(x, y, n) for x, y, n in nodes) + labels + _pin(kx, ky) + "</svg>\n")
    (IMG / "banner-contact.svg").write_text(svg)

    # Mobile: 800 x 710. Map on top, three labelled badges in a row underneath.
    W, H = 800, 710
    proj = Projection(W, 430, scale=88, lon_c=84.13, lat_c=28.4)
    kx, ky = proj(*KATHMANDU)
    ky += 40
    proj.lat_top += 40 / proj.s
    nodes = [(140, 560, "mail"), (400, 560, "phone"), (660, 560, "chat")]
    links = "".join(f'<path d="M{kx:.0f} {ky:.0f}Q{(kx + x) / 2:.0f} {(ky + y) / 2 - 40:.0f} {x} {y - 52}"/>' for x, y, _ in nodes)
    labels = (_label(140, 662, ["Email"], "middle", (36, 26)) + _label(400, 662, ["Phone"], "middle", (36, 26)) +
              _label(660, 662, ["Message"], "middle", (36, 26)))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
           '<!-- Boundary: geoBoundaries / Open Data Nepal (CC BY 4.0). Generated by tools/build_hero_map.py -->'
           + _map_layer(proj, W, H, 5, 14)
           + f'<g fill="none" stroke="{ROSE}" stroke-width="3" stroke-dasharray="2 10" stroke-linecap="round">{links}</g>'
           + "".join(_badge(x, y, n, 52) for x, y, n in nodes) + labels + _pin(kx, ky) + "</svg>\n")
    (IMG / "banner-contact-mobile.svg").write_text(svg)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    proj = hero()
    contact_banner()
    for name in ("hero-terrain.svg", "banner-contact.svg", "banner-contact-mobile.svg"):
        print(f"wrote src/assets/images/{name} ({(IMG / name).stat().st_size / 1024:.0f} KB)")
    print("wrote src/partials/hero-map.html")
    print("Kathmandu at", tuple(round(v) for v in proj(*KATHMANDU)))


if __name__ == "__main__":
    main()
