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
               f"C{bir[0]+40:.0f} {bir[1]+50:.0f} {bir[0]+230:.0f} {H-20} {bir[0]+330:.0f} {H+30}",
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
            <circle class="route-map__origin" cx="{kx:.0f}" cy="{ky:.0f}" r="10"/>
            <text class="route-map__label" x="{kx+22:.0f}" y="{ky-14:.0f}">Kathmandu</text>
          </svg>
'''
    PARTIAL.write_text("<!-- Generated by tools/build_hero_map.py; do not edit by hand. -->\n" + partial)
    return proj


def contact_banner():
    W, H = 1600, 720
    proj = Projection(W, H, scale=118, lon_c=84.13, lat_c=28.41)
    outline = outline_path(proj)
    inner, _ = terrain_groups(proj, 7, 16, 0.10, 0.075)
    kx, ky = proj(*KATHMANDU)
    # Contact channels around the map (mail, phone, chat), joined to Kathmandu.
    nodes = [(170, 150, "mail"), (1430, 150, "phone"), (1430, 600, "chat")]
    icon = {
        "mail": '<rect x="-22" y="-15" width="44" height="30" rx="2"/><path d="M-21 -13l21 15 21-15"/>',
        "phone": '<path d="M-14 -20h8l4 11-5 4a26 26 0 0 0 15 15l4-5 11 4v8a4 4 0 0 1-4 4A38 38 0 0 1-18 -16a4 4 0 0 1 4-4z"/>',
        "chat": '<path d="M-22 -16h44v26H-4l-14 10v-10h-4z"/><path d="M-12 -5h24M-12 3h14"/>',
    }
    links, badges = [], []
    for x, y, name in nodes:
        mx, my = (kx + x) / 2, min(ky, y) - 120
        links.append(f'<path d="M{kx:.0f} {ky:.0f}Q{mx:.0f} {my:.0f} {x} {y}"/>')
        badges.append(f'<g transform="translate({x} {y})"><circle r="46" fill="{IVORY}"/>'
                      f'<g fill="none" stroke="{FOREST}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round">{icon[name]}</g></g>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<!-- Boundary: geoBoundaries / Open Data Nepal (CC BY 4.0). Generated by tools/build_hero_map.py -->
<defs><clipPath id="np"><path d="{outline}"/></clipPath></defs>
<rect width="{W}" height="{H}" fill="{FOREST}"/>
<path d="{outline}" fill="{FOREST_RAISED}"/>
<g clip-path="url(#np)" fill="none" stroke="{MIST}" opacity=".8">{inner}</g>
<path d="{outline}" fill="none" stroke="{ROSE}" stroke-width="2.4" stroke-linejoin="round"/>
<g fill="none" stroke="{ROSE}" stroke-width="3" stroke-dasharray="2 10" stroke-linecap="round">{''.join(links)}</g>
{''.join(badges)}
<circle cx="{kx:.0f}" cy="{ky:.0f}" r="64" fill="{CRIMSON}" opacity=".16"/>
<circle cx="{kx:.0f}" cy="{ky:.0f}" r="36" fill="{CRIMSON}" opacity=".3"/>
<path d="M{kx:.0f} {ky:.0f}c-6-14-24-28-24-46a24 24 0 0 1 48 0c0 18-18 32-24 46z" fill="{CRIMSON}" stroke="{IVORY}" stroke-width="3" transform="translate(0 -4)"/>
<circle cx="{kx:.0f}" cy="{ky-54:.0f}" r="8.5" fill="{IVORY}"/>
</svg>
'''
    (IMG / "banner-contact.svg").write_text(svg)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    proj = hero()
    contact_banner()
    for name in ("hero-terrain.svg", "banner-contact.svg"):
        print(f"wrote src/assets/images/{name} ({(IMG / name).stat().st_size / 1024:.0f} KB)")
    print("wrote src/partials/hero-map.html")
    print("Kathmandu at", tuple(round(v) for v in proj(*KATHMANDU)))


if __name__ == "__main__":
    main()
