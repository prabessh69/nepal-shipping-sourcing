#!/usr/bin/env python3
"""Generate the hero terrain plate (site/assets/img/hero-terrain.svg).

An original, stylised illustration: an approximate outline of Nepal filled with
procedurally generated contour lines (elevation rises toward the northern,
Himalayan border). It is decorative and NOT a survey-accurate map.

Run from the project root:  python3 tools/build_hero_map.py
Pure standard library — no dependencies.
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "site" / "assets" / "img" / "hero-terrain.svg"

# ViewBox shared with the inline route overlay in index.html
W, H = 1600, 760
LON0, LON1 = 78.2, 90.0   # frame (equirectangular, cos-lat corrected)
LAT_C = 28.0
KX = math.cos(math.radians(LAT_C))
SCALE = W / ((LON1 - LON0) * KX)
LAT_TOP = 31.05


def proj(lon, lat):
    return ((lon - LON0) * KX * SCALE, (LAT_TOP - lat) * SCALE)


# Approximate outline of Nepal (lon, lat), clockwise from the far west.
NEPAL = [
    (80.06, 28.84), (80.25, 29.15), (80.37, 29.75), (80.62, 30.02), (80.90, 30.22),
    (81.25, 30.43), (81.53, 30.42), (82.10, 30.33), (82.33, 30.12), (82.80, 29.75),
    (83.34, 29.46), (83.90, 29.32), (84.23, 28.84), (84.62, 28.70), (85.01, 28.64),
    (85.32, 28.76), (85.62, 28.45), (85.90, 28.30), (86.00, 27.98), (86.30, 28.05),
    (86.58, 28.10), (87.10, 27.85), (87.45, 27.88), (87.80, 27.90), (88.12, 27.88),
    (88.17, 27.40), (88.19, 27.00), (88.10, 26.70), (88.04, 26.42), (87.70, 26.40),
    (87.30, 26.38), (86.80, 26.45), (86.30, 26.60), (86.00, 26.65), (85.60, 26.84),
    (85.20, 26.75), (84.88, 27.00), (84.65, 27.25), (84.10, 27.50), (83.70, 27.45),
    (83.30, 27.35), (83.00, 27.45), (82.70, 27.50), (82.30, 27.68), (81.90, 27.85),
    (81.40, 28.15), (81.00, 28.40), (80.55, 28.65), (80.25, 28.75),
]

rng = random.Random(2018)
GRID = 64
PERM = [[rng.random() for _ in range(GRID)] for _ in range(GRID)]


def smooth(t):
    return t * t * (3 - 2 * t)


def vnoise(x, y):
    xi, yi = int(math.floor(x)), int(math.floor(y))
    xf, yf = x - xi, y - yi
    a = PERM[yi % GRID][xi % GRID]
    b = PERM[yi % GRID][(xi + 1) % GRID]
    c = PERM[(yi + 1) % GRID][xi % GRID]
    d = PERM[(yi + 1) % GRID][(xi + 1) % GRID]
    u, v = smooth(xf), smooth(yf)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def fbm(x, y):
    total, amp, freq = 0.0, 0.5, 1.0
    for _ in range(5):
        total += amp * vnoise(x * freq, y * freq)
        amp *= 0.5
        freq *= 2.03
    return total


def elevation(px, py):
    lon = px / (KX * SCALE) + LON0
    lat = LAT_TOP - py / SCALE
    south = 26.4 + 0.30 * (88.1 - lon)      # rough southern edge of the country
    t = (lat - south) / 2.15
    base = max(0.0, min(1.25, t)) ** 1.35
    n = fbm(px / 115.0, py / 115.0)
    ridges = 1 - abs(2 * fbm(px / 70.0 + 9, py / 70.0 + 3) - 1)
    return base * 0.85 + n * 0.35 + ridges * base * 0.25


def march(step, levels):
    cols, rows = int(W / step) + 2, int(H / step) + 2
    f = [[elevation(i * step, j * step) for i in range(cols)] for j in range(rows)]
    out = {}
    for lv in levels:
        segs = []
        for j in range(rows - 1):
            for i in range(cols - 1):
                v = (f[j][i], f[j][i + 1], f[j + 1][i + 1], f[j + 1][i])
                idx = sum(1 << k for k in range(4) if v[k] > lv)
                if idx in (0, 15):
                    continue
                x0, y0 = i * step, j * step
                corners = [(x0, y0), (x0 + step, y0), (x0 + step, y0 + step), (x0, y0 + step)]

                def edge(e):
                    a, b = e, (e + 1) % 4
                    va, vb = v[a], v[b]
                    t = 0.5 if vb == va else (lv - va) / (vb - va)
                    (ax, ay), (bx, by) = corners[a], corners[b]
                    return (round(ax + (bx - ax) * t, 1), round(ay + (by - ay) * t, 1))

                crossing = [e for e in range(4) if (v[e] > lv) != (v[(e + 1) % 4] > lv)]
                if len(crossing) == 2:
                    segs.append((edge(crossing[0]), edge(crossing[1])))
                elif len(crossing) == 4:
                    segs.append((edge(0), edge(1)))
                    segs.append((edge(2), edge(3)))
        out[lv] = join(segs)
    return out


def join(segs):
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    used = set()
    lines = []
    for a, b in segs:
        key = (a, b) if a < b else (b, a)
        if key in used:
            continue
        used.add(key)
        line = [a, b]
        for direction in (0, 1):
            while True:
                end = line[-1] if direction == 0 else line[0]
                nxt = None
                for c in adj.get(end, []):
                    k = (end, c) if end < c else (c, end)
                    if k not in used:
                        used.add(k)
                        nxt = c
                        break
                if nxt is None:
                    break
                if direction == 0:
                    line.append(nxt)
                else:
                    line.insert(0, nxt)
        if len(line) >= 4:
            lines.append(line[::2] + ([line[-1]] if len(line) % 2 == 0 else []))
    return lines


def path_d(lines):
    parts = []
    for ln in lines:
        x, y = ln[0]
        s = f"M{x:g} {y:g}" + "".join(f"L{px:g} {py:g}" for px, py in ln[1:])
        parts.append(s)
    return "".join(parts)


def main():
    pts = [proj(lon, lat) for lon, lat in NEPAL]
    outline = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
    levels = [round(0.14 + k * 0.036, 3) for k in range(30)]
    contours = march(5, levels)

    inner, outer = [], []
    for k, lv in enumerate(levels):
        d = path_d(contours[lv])
        if not d:
            continue
        major = k % 5 == 0
        inner.append(f'<path d="{d}" stroke-width="{1.3 if major else 0.7}" opacity="{0.9 if major else 0.55}"/>')
        if k < 14 and k % 2 == 0:
            outer.append(f'<path d="{d}" stroke-width="0.6"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs><clipPath id="np"><path d="{outline}"/></clipPath></defs>
<rect width="{W}" height="{H}" fill="#16221C"/>
<g fill="none" stroke="#6E8577" opacity="0.22">{''.join(outer)}</g>
<path d="{outline}" fill="#1D2E25"/>
<g clip-path="url(#np)" fill="none" stroke="#A9C2B2">{''.join(inner)}</g>
<path d="{outline}" fill="none" stroke="#F2A7B4" stroke-width="2" stroke-linejoin="round"/>
</svg>
'''
    OUT.write_text(svg)
    print(f"wrote {OUT} ({len(svg)/1024:.1f} KB)")
    for name, (lon, lat) in {
        "kathmandu": (85.32, 27.71), "birgunj": (84.88, 27.01), "biratnagar": (87.28, 26.45),
        "bhairahawa": (83.45, 27.50), "nepalgunj": (81.62, 28.05),
    }.items():
        x, y = proj(lon, lat)
        print(f"{name}: {x:.0f},{y:.0f}")


if __name__ == "__main__":
    main()
