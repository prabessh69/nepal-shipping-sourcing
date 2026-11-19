#!/usr/bin/env python3
"""Generate the site's editorial illustrations into src/assets/images/.

    python3 tools/build_illustrations.py

Flat, geometric illustrations in the brand palette (warm ivory, deep forest
green, rhododendron red). Original artwork, no third-party assets. Standard
library only. Map-based artwork (hero terrain, contact banner) comes from
tools/build_hero_map.py instead.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "assets" / "images"

IVORY, TINT, TINT_DEEP, SAND = "#FAF7F2", "#F1ECE4", "#E7E0D5", "#D8CBB6"
FOREST, FOREST_RAISED, FOREST_3, FOREST_4 = "#16221C", "#1D2E25", "#2A4034", "#3B5546"
LEAF, LEAF_2, LEAF_3 = "#1E5631", "#2F6B44", "#4E8762"
CRIMSON, CRIMSON_DEEP, ROSE, ROSE_PALE = "#C8102E", "#A60D26", "#F2A7B4", "#F7D3D9"
MIST, MIST_2 = "#B9C2BC", "#D5DBD6"


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<!-- {title} | Nepal Shipping & Sourcing, original illustration -->\n{body}\n</svg>\n')


def poly(pts, fill, extra=""):
    return f'<path d="M{"L".join(f"{x:g} {y:g}" for x, y in pts)}Z" fill="{fill}"{extra}/>'


# ---------- motifs ----------
def range_with_snow(pts, fill, snow, peaks, depth=0.36):
    """Mountain silhouette with jagged snow caps on selected peak indices."""
    out = [poly(pts, fill)]
    for i in peaks:
        (lx, ly), (px, py), (rx, ry) = pts[i - 1], pts[i], pts[i + 1]
        a = (px + (lx - px) * depth, py + (ly - py) * depth)
        b = (px + (rx - px) * depth, py + (ry - py) * depth)
        jag = []
        for k in range(1, 5):
            t = k / 5
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t + (-8 if k % 2 else 6)
            jag.append((x, y))
        out.append(poly([a, (px, py), b] + jag[::-1], snow))
    return "".join(out)


def plane(x, y, s, rot, body=IVORY, accent=FOREST, stroke=None):
    st = f' stroke="{stroke}" stroke-width="{3 / s:.2f}" stroke-linejoin="round"' if stroke else ""
    windows = "".join(f'<circle cx="{wx}" cy="-4" r="2.6"/>' for wx in range(-125, 140, 15))
    return (f'<g transform="translate({x} {y}) rotate({rot}) scale({s})">'
            f'<path d="M-150 -13L-186 -82L-160 -82L-112 -13Z" fill="{body}"{st}/>'
            f'<path d="M-150 2L-206 15L-186 20L-118 7Z" fill="{body}"{st}/>'
            f'<path d="M-190 -14L150 -18Q200 -15 206 0Q201 11 150 15L-170 15Q-196 11 -201 -2Z" fill="{body}"{st}/>'
            f'<path d="M-12 6L-86 56L-58 58L52 9Z" fill="{body}"{st}/>'
            f'<rect x="-44" y="21" width="46" height="17" rx="8" fill="{accent}"/>'
            f'<path d="M168 -10L190 -9Q197 -6 199 -2L170 -2Z" fill="{accent}"/>'
            f'<g fill="{accent}">{windows}</g>'
            f'<path d="M-186 -82L-160 -82L-150 -60L-178 -60Z" fill="{CRIMSON}"/>'
            f'</g>')


def containers(x0, y_base, cols, rows, w=50, h=28, gap=3, palette=None, rib=FOREST):
    palette = palette or [CRIMSON, LEAF, ROSE, MIST, IVORY, CRIMSON_DEEP, LEAF_2, SAND]
    out = []
    for r in range(rows):
        for c in range(cols):
            if r == rows - 1 and c in (0, cols - 1):
                continue  # stepped top row
            col = palette[(c * 3 + r * 5) % len(palette)]
            x, y = x0 + c * (w + gap), y_base - (r + 1) * (h + gap)
            ribs = "".join(f'<path d="M{x + k * w / 6:g} {y + 4:g}v{h - 8}"/>' for k in range(1, 6))
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}"/>'
                       f'<g stroke="{rib}" stroke-opacity=".22" stroke-width="1.5">{ribs}</g>')
    return "".join(out)


def ship(x, y, s, hull=TINT_DEEP):
    return (f'<g transform="translate({x} {y}) scale({s})">'
            + containers(40, -60, 9, 3)
            + f'<path d="M0 -60L612 -60L572 22L34 22Z" fill="{hull}"/>'
            f'<path d="M10 -2L596 -2L572 22L34 22Z" fill="{CRIMSON}"/>'
            f'<path d="M0 -60L612 -60" stroke="{FOREST}" stroke-width="3"/>'
            f'<rect x="512" y="-158" width="64" height="98" fill="{IVORY}"/>'
            f'<rect x="506" y="-166" width="76" height="12" fill="{FOREST_3}"/>'
            + "".join(f'<rect x="{520 + k * 13}" y="-148" width="8" height="10" fill="{FOREST}"/>' for k in range(4))
            + f'<rect x="530" y="-196" width="26" height="30" fill="{CRIMSON}"/>'
            f'</g>')


def truck(x, y, s, trailer=LEAF, cab=CRIMSON):
    ribs = "".join(f'<path d="M{20 + k * 28} -104v78"/>' for k in range(10))
    wheels = "".join(f'<circle cx="{wx}" cy="-4" r="21" fill="{FOREST}"/><circle cx="{wx}" cy="-4" r="8" fill="{MIST}"/>'
                     for wx in (52, 100, 250, 352))
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<rect x="0" y="-112" width="300" height="92" rx="3" fill="{trailer}"/>'
            f'<g stroke="{IVORY}" stroke-opacity=".25" stroke-width="2">{ribs}</g>'
            f'<path d="M306 -96h52l34 34v42h-86z" fill="{cab}"/>'
            f'<path d="M318 -86h36l24 26h-60z" fill="{IVORY}"/>'
            f'<rect x="0" y="-26" width="392" height="10" fill="{FOREST_3}"/>'
            + wheels + '</g>')


def carton(x, y, w, h, fill=SAND, tape=TINT_DEEP, mark=True):
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
           f'<rect x="{x + w / 2 - 6:g}" y="{y}" width="12" height="{h}" fill="{tape}" opacity=".7"/>'
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{FOREST}" stroke-opacity=".25" stroke-width="2"/>')
    if mark and w > 60:
        mx, my = x + 14, y + 14
        out += (f'<g stroke="{FOREST}" stroke-width="2.4" fill="none" stroke-linecap="round" opacity=".7">'
                f'<path d="M{mx} {my + 16}v-14M{mx - 5} {my + 7}l5-6 5 6M{mx + 14} {my + 16}v-14M{mx + 9} {my + 7}l5-6 5 6"/></g>')
    return out


def document(x, y, w, h, rot=0, lines=5, fill=IVORY):
    ls = "".join(f'<rect x="{w * .14:g}" y="{h * .2 + k * h * .12:g}" width="{w * (0.72 if k % 3 else 0.5):g}" height="5" rx="2.5" fill="{MIST}"/>'
                 for k in range(lines))
    return (f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M0 0H{w * .78:g}L{w:g} {w * .22:g}V{h}H0Z" fill="{fill}" stroke="{FOREST}" stroke-opacity=".3" stroke-width="2"/>'
            f'<path d="M{w * .78:g} 0V{w * .22:g}H{w:g}" fill="none" stroke="{FOREST}" stroke-opacity=".3" stroke-width="2"/>'
            f'{ls}</g>')


def stamp(x, y, r, color=CRIMSON):
    return (f'<g transform="translate({x} {y}) rotate(-14)" fill="none" stroke="{color}" stroke-width="4">'
            f'<circle r="{r}"/><circle r="{r - 9}" stroke-width="2"/>'
            f'<path d="M{-r * .42:g} 0l{r * .28:g} {r * .3:g} {r * .5:g}-{r * .58:g}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>')


def felt_ball(x, y, r, fill, speck=IVORY):
    specks = "".join(f'<circle cx="{x + dx * r:g}" cy="{y + dy * r:g}" r="{r * .06:g}" fill="{speck}" opacity=".45"/>'
                     for dx, dy in ((-.4, -.3), (.2, -.5), (.45, .1), (-.1, .35), (-.5, .25), (.15, .05)))
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'
            f'<path d="M{x - r * .55:g} {y - r * .55:g}a{r:g} {r:g} 0 0 1 {r * .9:g}-{r * .25:g}" fill="none" stroke="{IVORY}" stroke-opacity=".35" stroke-width="{r * .12:g}" stroke-linecap="round"/>'
            + specks)


def dhaka_band(x, y, w, h, colors=(CRIMSON, IVORY, LEAF)):
    """Repeating diamond pattern inspired by hand-woven dhaka cloth."""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{colors[0]}"/>']
    d = h * .9
    k = 0
    cx = x + d / 2
    while cx < x + w:
        c = colors[1 + (k % (len(colors) - 1))]
        cy = y + h / 2
        out.append(poly([(cx, cy - d / 2), (cx + d / 2, cy), (cx, cy + d / 2), (cx - d / 2, cy)], c))
        out.append(poly([(cx, cy - d / 5), (cx + d / 5, cy), (cx, cy + d / 5), (cx - d / 5, cy)], colors[0]))
        cx += d
        k += 1
    return "".join(out)


def rhododendron(x, y, s=1.0):
    """Sprig of rhododendron, Nepal's national flower."""
    leaves = "".join(
        f'<ellipse cx="0" cy="-34" rx="11" ry="34" fill="{c}" transform="translate({x} {y}) scale({s}) rotate({a})"/>'
        for a, c in ((-70, LEAF), (-35, LEAF_2), (0, LEAF), (35, LEAF_2), (70, LEAF), (110, LEAF_2), (-110, LEAF_2)))
    petals = ""
    for dx, dy, r in ((0, -62, 22), (-26, -50, 19), (25, -48, 19), (-12, -80, 18), (14, -78, 18), (0, -40, 16)):
        petals += (f'<circle cx="{x + dx * s:g}" cy="{y + dy * s:g}" r="{r * s:g}" fill="{CRIMSON}"/>'
                   f'<circle cx="{x + dx * s:g}" cy="{y + dy * s:g}" r="{r * s * .38:g}" fill="{CRIMSON_DEEP}"/>')
    return leaves + petals


def pagoda(cx, by, s=1.0, roof=FOREST, body=CRIMSON_DEEP, plinth=TINT_DEEP):
    g = []
    y = by
    for w in (300, 252, 206, 164):            # stepped plinth
        g.append(f'<rect x="{-w / 2}" y="{y - 0 - 22}" width="{w}" height="22" fill="{plinth}"/>')
        g.append(f'<rect x="{-w / 2}" y="{y - 22}" width="{w}" height="3" fill="{FOREST}" opacity=".15"/>')
        y -= 22
    tiers = ((118, 70, 236), (86, 54, 184), (58, 46, 130))
    for i, (bw, bh, rw) in enumerate(tiers):
        g.append(f'<rect x="{-bw / 2}" y="{y - bh}" width="{bw}" height="{bh}" fill="{body}"/>')
        if i == 0:
            g += [f'<rect x="{-bw / 2 + 14 + k * 24}" y="{y - bh + 14}" width="12" height="{bh - 14}" fill="{FOREST}" opacity=".55"/>' for k in range(4)]
        y -= bh
        g.append(poly([(-rw / 2, y + 8), (-rw / 2 + 14, y - 2), (-bw / 2 + 4, y - 42), (bw / 2 - 4, y - 42), (rw / 2 - 14, y - 2), (rw / 2, y + 8)], roof))
        g.append(f'<rect x="{-rw / 2 + 10}" y="{y + 2}" width="{rw - 20}" height="5" fill="{CRIMSON}" opacity=".9"/>')
        y -= 42
    g.append(f'<rect x="-5" y="{y - 46}" width="10" height="46" fill="{SAND}"/>')
    for k, r in enumerate((14, 11, 8)):
        g.append(f'<circle cx="0" cy="{y - 12 - k * 15}" r="{r}" fill="{SAND}" stroke="{FOREST}" stroke-opacity=".25"/>')
    return f'<g transform="translate({cx} 0) scale({s} 1)">{"".join(g)}</g>'


def house(x, by, w, h, fill, roof=FOREST, windows=True):
    out = [f'<rect x="{x}" y="{by - h}" width="{w}" height="{h}" fill="{fill}"/>',
           poly([(x - 10, by - h + 2), (x + w + 10, by - h + 2), (x + w - 6, by - h - 22), (x + 6, by - h - 22)], roof)]
    if windows:
        cols = max(1, int(w // 34))
        for r in range(int((h - 30) // 46)):
            for c in range(cols):
                wx = x + (w - cols * 34) / 2 + c * 34 + 9
                out.append(f'<rect x="{wx:g}" y="{by - h + 22 + r * 46}" width="16" height="24" fill="{FOREST}" opacity=".7"/>'
                           f'<rect x="{wx - 3:g}" y="{by - h + 18 + r * 46}" width="22" height="5" fill="{SAND}"/>')
    return "".join(out)


# ---------- banners (1600 x 720) ----------
def banner_about():
    W, H = 1600, 720
    far = [(0, 470), (0, 330), (90, 296), (160, 320), (250, 214), (320, 262), (380, 200), (450, 252), (540, 160),
           (610, 228), (676, 206), (750, 268), (840, 184), (920, 242), (1000, 196), (1080, 256), (1160, 206),
           (1250, 276), (1340, 218), (1420, 270), (1500, 236), (1600, 296), (1600, 470)]
    hills1 = ("M0 470C140 420 260 452 380 430S640 392 780 420 1060 446 1200 412 1460 398 1600 430V720H0Z", LEAF_2)
    hills2 = ("M0 540C180 500 300 528 460 506S760 484 900 512 1180 534 1340 500 1520 492 1600 512V720H0Z", LEAF)
    ground = ("M0 600C260 582 520 596 800 588S1340 576 1600 592V720H0Z", FOREST)
    body = [f'<rect width="{W}" height="{H}" fill="{TINT}"/>',
            f'<circle cx="1210" cy="230" r="150" fill="{ROSE}" opacity=".55"/>',
            range_with_snow(far, MIST, IVORY, [4, 6, 8, 12, 14, 16, 18]),
            f'<path d="{hills1[0]}" fill="{hills1[1]}"/>', f'<path d="{hills2[0]}" fill="{hills2[1]}"/>']
    # Kathmandu roofscape and temple
    town = []
    for x, w, h, c in ((60, 96, 150, CRIMSON_DEEP), (170, 80, 120, "#8E1A2B"), (262, 104, 176, CRIMSON_DEEP),
                       (780, 92, 132, "#8E1A2B"), (884, 120, 168, CRIMSON_DEEP), (1016, 84, 118, "#8E1A2B"),
                       (1112, 100, 150, CRIMSON_DEEP), (1224, 78, 110, "#8E1A2B")):
        town.append(house(x, 640, w, h, c))
    body += town
    body.append(pagoda(560, 640, 1.0))
    body.append(f'<path d="{ground[0]}" fill="{ground[1]}"/>')
    # gateway route out of the valley
    body.append(f'<path d="M700 600C900 520 1080 470 1260 400S1500 300 1660 250" fill="none" stroke="{CRIMSON}" stroke-width="5" stroke-dasharray="3 14" stroke-linecap="round"/>')
    body.append(plane(1440, 300, .42, -16, IVORY, FOREST, FOREST))
    return svg(W, H, "".join(body), "About banner: Kathmandu valley beneath the Himalaya, with a route leaving for the world")


def banner_services():
    W, H = 1600, 720
    far = [(0, 470), (0, 360), (120, 300), (220, 340), (330, 250), (430, 300), (540, 230), (640, 290), (760, 240),
           (880, 310), (990, 250), (1100, 300), (1220, 236), (1340, 300), (1460, 260), (1600, 320), (1600, 470)]
    body = [f'<rect width="{W}" height="{H}" fill="{FOREST}"/>',
            range_with_snow(far, FOREST_RAISED, FOREST_4, [4, 6, 8, 10, 12], .3),
            f'<path d="M0 470H1600V720H0Z" fill="{FOREST_3}"/>',
            # sea on the left, quay and road on the right
            f'<path d="M0 520H900L860 720H0Z" fill="#20352B"/>',
            "".join(f'<path d="M{x} {y}q14-8 28 0t28 0" fill="none" stroke="{MIST}" stroke-opacity=".35" stroke-width="2.5" stroke-linecap="round"/>'
                    for x, y in ((60, 640), (220, 690), (420, 660), (640, 700), (120, 700), (760, 650))),
            ship(110, 585, .95),
            f'<path d="M900 520H1600V720H860Z" fill="{FOREST_4}"/>',
            f'<path d="M880 610H1600V680H866Z" fill="{FOREST_RAISED}"/>',
            f'<path d="M900 645H1600" stroke="{IVORY}" stroke-width="4" stroke-dasharray="26 22" opacity=".7"/>',
            truck(1110, 662, .95),
            # stacked containers on the quay
            containers(1440, 606, 3, 2, w=44, h=24),
            # aircraft climbing out with a dotted contrail
            f'<path d="M760 420C900 340 1020 270 1150 214" fill="none" stroke="{ROSE}" stroke-width="5" stroke-dasharray="2 14" stroke-linecap="round"/>',
            plane(1270, 168, .62, -18, IVORY, FOREST),
            f'<circle cx="1460" cy="104" r="44" fill="{ROSE}" opacity=".85"/>']
    return svg(W, H, "".join(body), "Services banner: container ship, cargo aircraft and truck")


def banner_sourcing():
    W, H = 1600, 720
    body = [f'<rect width="{W}" height="{H}" fill="{TINT}"/>',
            f'<path d="M0 0H1600V250C1300 236 1000 262 700 248S200 230 0 250Z" fill="{ROSE_PALE}" opacity=".55"/>',
            range_with_snow([(900, 250), (980, 170), (1040, 210), (1110, 130), (1190, 196), (1260, 150), (1350, 220), (1430, 180), (1520, 250)],
                            MIST_2, IVORY, [3, 5, 7], .4),
            # hanging textiles on a rod
            f'<rect x="90" y="86" width="560" height="10" rx="5" fill="{FOREST}"/>',
            "".join(dhaka_band(130, 96 + k * 41.25, 160, 41.25, pal) for k, pal in enumerate(
                [(CRIMSON, IVORY, LEAF_2), (LEAF, ROSE, IVORY), (CRIMSON_DEEP, IVORY, ROSE)] * 3) if k < 8),
            "".join(f'<path d="M{140 + k * 12} 426v26" stroke="{CRIMSON}" stroke-width="3"/>' for k in range(13)),
            f'<rect x="320" y="96" width="140" height="300" fill="{LEAF}"/>',
            "".join(f'<rect x="320" y="{120 + k * 46}" width="140" height="10" fill="{IVORY}" opacity=".85"/>' for k in range(6)),
            "".join(f'<path d="M{328 + k * 12} 396v24" stroke="{LEAF}" stroke-width="3"/>' for k in range(11)),
            f'<rect x="490" y="96" width="130" height="270" fill="{IVORY}"/>',
            "".join(f'<path d="M{490 + k * 26} 96v270" stroke="{ROSE}" stroke-width="3"/>' for k in range(1, 5)),
            # rhododendron on the wall
            rhododendron(1380, 360, 1.15),
            # table
            f'<rect y="470" width="{W}" height="250" fill="{TINT_DEEP}"/>',
            f'<rect y="470" width="{W}" height="10" fill="{SAND}"/>',
            '<g transform="translate(800 650) scale(1.2) translate(-800 -650)">',
            # spice mound with scoop
            f'<path d="M230 610Q315 470 410 610Z" fill="{CRIMSON}"/>',
            f'<path d="M270 610Q315 540 370 610Z" fill="{CRIMSON_DEEP}" opacity=".6"/>',
            f'<path d="M380 600l60-44" stroke="{SAND}" stroke-width="12" stroke-linecap="round"/>',
            # tea leaves
            "".join(f'<ellipse cx="{x}" cy="{y}" rx="26" ry="11" fill="{c}" transform="rotate({a} {x} {y})"/>'
                    for x, y, a, c in ((470, 600, -20, LEAF), (510, 590, 25, LEAF_2), (545, 604, -10, LEAF), (500, 612, 5, LEAF_3),
                                       (575, 592, 30, LEAF_2), (455, 584, 40, LEAF_3), (540, 580, -35, LEAF))),
            # singing bowl and mallet
            f'<ellipse cx="760" cy="636" rx="126" ry="16" fill="{FOREST}" opacity=".12"/>',
            f'<path d="M640 540H880Q874 640 760 640Q646 640 640 540Z" fill="{CRIMSON_DEEP}"/>',
            f'<ellipse cx="760" cy="540" rx="120" ry="22" fill="#8E1A2B"/>',
            f'<ellipse cx="760" cy="540" rx="104" ry="15" fill="{FOREST}" opacity=".55"/>',
            f'<path d="M660 570Q760 590 860 570" stroke="{ROSE}" stroke-width="3" fill="none" opacity=".6"/>',
            f'<path d="M880 636l120-30" stroke="{FOREST}" stroke-width="14" stroke-linecap="round"/>',
            f'<path d="M972 613l30-8" stroke="{CRIMSON}" stroke-width="16" stroke-linecap="round"/>',
            # felt balls
            felt_ball(1080, 610, 40, CRIMSON), felt_ball(1160, 618, 34, LEAF), felt_ball(1118, 556, 34, ROSE),
            felt_ball(1220, 606, 30, IVORY, MIST), felt_ball(1196, 552, 28, CRIMSON_DEEP), felt_ball(1040, 552, 26, LEAF_2),
            # lokta paper stack tied with string
            "".join(poly([(1200 + k * 4, 640 - k * 14), (1400 + k * 4, 640 - k * 14), (1396 + k * 4, 600 - k * 14), (1204 + k * 4, 600 - k * 14)],
                         c, f' stroke="{SAND}" stroke-width="2"') for k, c in enumerate((IVORY, ROSE_PALE, IVORY, "#EFE6D6"))),
            f'<path d="M1302 640V546" stroke="{CRIMSON}" stroke-width="5"/>',
            f'<path d="M1206 594H1406" stroke="{CRIMSON}" stroke-width="5"/>', '</g>']
    return svg(W, H, "".join(body), "Sourcing banner: Nepalese textiles, spices, tea, singing bowl, felt balls and lokta paper")


# ---------- feature images (1200 x 800) ----------
def feature_air_cargo():
    W, H = 1200, 800
    far = [(0, 470), (0, 330), (110, 270), (200, 310), (300, 200), (380, 250), (470, 180), (560, 240), (650, 200),
           (760, 270), (860, 210), (960, 260), (1060, 220), (1200, 290), (1200, 470)]
    body = [f'<rect width="{W}" height="{H}" fill="{TINT}"/>',
            f'<circle cx="960" cy="170" r="110" fill="{ROSE}" opacity=".5"/>',
            range_with_snow(far, MIST, IVORY, [4, 6, 8, 10, 12]),
            f'<path d="M0 470C200 440 400 460 600 446S1000 430 1200 450V800H0Z" fill="{LEAF_2}"/>',
            f'<rect y="540" width="{W}" height="260" fill="{TINT_DEEP}"/>',
            f'<path d="M0 700H1200" stroke="{IVORY}" stroke-width="6" stroke-dasharray="40 30"/>',
            f'<path d="M0 548H1200" stroke="{SAND}" stroke-width="6"/>',
            plane(560, 430, 1.55, 0, IVORY, FOREST, FOREST),
            # open cargo door
            f'<rect x="700" y="404" width="64" height="40" fill="{FOREST}"/>',
            f'<path d="M700 404l14-46h64l-14 46z" fill="{IVORY}" stroke="{FOREST}" stroke-width="3"/>',
            # loader ramp
            f'<path d="M720 444L820 600H900L800 444Z" fill="{FOREST_3}"/>']
    # ULD containers on dollies
    for x, c in ((150, CRIMSON), (300, LEAF), (450, MIST)):
        body.append(f'<path d="M{x} 640V560L{x + 26} 534H{x + 130}V640Z" fill="{c}"/>')
        body.append(f'<rect x="{x - 6}" y="640" width="142" height="12" fill="{FOREST}"/>')
        body.append(f'<circle cx="{x + 18}" cy="662" r="11" fill="{FOREST}"/><circle cx="{x + 112}" cy="662" r="11" fill="{FOREST}"/>')
    body.append(f'<path d="M136 646H880" stroke="{FOREST}" stroke-width="3" opacity=".5"/>')
    # cartons on a pallet
    for i, (dx, dy, w, h) in enumerate(((930, 600, 110, 60), (1050, 600, 100, 60), (950, 540, 100, 60), (1060, 540, 80, 60), (990, 480, 110, 60))):
        body.append(carton(dx, dy, w, h))
    body.append(f'<rect x="918" y="660" width="244" height="16" fill="{FOREST_4}"/>')
    body.append(f'<path d="M918 676h244" stroke="{FOREST}" stroke-width="4"/>')
    return svg(W, H, "".join(body), "Air cargo: aircraft loading ULD containers and cartons beneath the Himalaya")


def feature_textiles():
    W, H = 1200, 800
    body = [f'<rect width="{W}" height="{H}" fill="{TINT}"/>',
            f'<rect x="0" y="610" width="{W}" height="190" fill="{TINT_DEEP}"/>',
            # loom frame
            f'<rect x="170" y="70" width="22" height="560" fill="{FOREST}"/>',
            f'<rect x="770" y="70" width="22" height="560" fill="{FOREST}"/>',
            f'<rect x="150" y="70" width="662" height="24" fill="{FOREST}"/>',
            f'<rect x="150" y="470" width="662" height="20" fill="{FOREST_3}"/>',
            "".join(f'<path d="M{212 + k * 18} 94V330" stroke="{MIST}" stroke-width="2.5"/>' for k in range(31)),
            # woven cloth
            dhaka_band(204, 330, 560, 46, (CRIMSON, IVORY, LEAF_2, ROSE)),
            dhaka_band(204, 376, 560, 46, (LEAF, IVORY, CRIMSON)),
            dhaka_band(204, 422, 560, 46, (CRIMSON_DEEP, ROSE, IVORY)),
            f'<rect x="204" y="316" width="560" height="14" fill="{SAND}"/>',
            # shuttle
            f'<path d="M520 300h120l20 8-20 8H520l-20-8z" fill="{SAND}" stroke="{FOREST}" stroke-width="2"/>',
            # folded pashmina stack
            "".join(f'<rect x="{870 - k * 6}" y="{560 - k * 44}" width="250" height="44" rx="6" fill="{c}"/>'
                    f'<rect x="{870 - k * 6}" y="{560 - k * 44 + 30}" width="250" height="6" fill="{FOREST}" opacity=".12"/>'
                    for k, c in enumerate((CRIMSON, IVORY, LEAF, ROSE, CRIMSON_DEEP))),
            # basket of felt balls
            f'<path d="M140 640H520L490 760H170Z" fill="{SAND}"/>',
            "".join(f'<path d="M{150 + k * 32} 640L{180 + k * 26} 760" stroke="{TINT_DEEP}" stroke-width="3"/>' for k in range(12)),
            felt_ball(210, 626, 38, CRIMSON), felt_ball(282, 610, 40, LEAF), felt_ball(360, 622, 36, ROSE),
            felt_ball(436, 616, 36, IVORY, MIST), felt_ball(320, 570, 30, CRIMSON_DEEP), felt_ball(250, 572, 26, LEAF_2),
            rhododendron(1030, 280, .9)]
    return svg(W, H, "".join(body), "Handmade textiles: dhaka weaving on a loom, folded pashmina and a basket of felt balls")


# ---------- service spot illustrations (480 x 320) ----------
def spot(body, title):
    return svg(480, 320, f'<rect width="480" height="320" fill="{TINT}"/>' + body, title)


def spot_air():
    return spot(range_with_snow([(0, 260), (0, 210), (80, 170), (150, 200), (230, 140), (300, 190), (380, 150), (480, 210), (480, 260)],
                                MIST, IVORY, [4, 6]) +
                f'<rect y="260" width="480" height="60" fill="{TINT_DEEP}"/>'
                f'<path d="M30 300C140 280 230 210 300 160" fill="none" stroke="{CRIMSON}" stroke-width="4" stroke-dasharray="2 11" stroke-linecap="round"/>' +
                plane(350, 120, .6, -18, IVORY, FOREST, FOREST), "Air freight")


def spot_sea():
    return spot(f'<rect y="210" width="480" height="110" fill="{FOREST_3}"/>' +
                "".join(f'<path d="M{x} {y}q10-6 20 0t20 0" fill="none" stroke="{MIST}" stroke-width="2.5" stroke-linecap="round" opacity=".6"/>'
                        for x, y in ((40, 270), (180, 296), (330, 262), (400, 300), (110, 304))) +
                ship(40, 232, .64) + f'<circle cx="400" cy="70" r="34" fill="{ROSE}" opacity=".6"/>', "Sea freight")


def spot_land():
    return spot(range_with_snow([(0, 240), (0, 150), (90, 90), (170, 140), (260, 70), (340, 130), (420, 100), (480, 140), (480, 240)],
                                MIST, IVORY, [3, 5]) +
                f'<path d="M0 200C120 180 260 210 480 190V320H0Z" fill="{LEAF_2}"/>'
                f'<path d="M0 262C160 236 300 270 480 248V320H0Z" fill="{LEAF}"/>'
                f'<path d="M-10 300C120 272 260 300 490 270" fill="none" stroke="{FOREST}" stroke-width="30"/>'
                f'<path d="M-10 300C120 272 260 300 490 270" fill="none" stroke="{IVORY}" stroke-width="3" stroke-dasharray="14 12"/>' +
                truck(150, 290, .55), "Land transport")


def spot_forwarding():
    nodes = [(70, 220, "box"), (180, 120, "truck"), (310, 210, "ship"), (420, 100, "plane")]
    path = "M70 220C110 150 140 130 180 120S270 220 310 210 380 110 420 100"
    glyph = {
        "box": f'<path d="M-16 -8L0 -17 16 -8v17L0 18-16 9z M-16 -8L0 1 16 -8M0 1v17" fill="none" stroke="{FOREST}" stroke-width="3" stroke-linejoin="round"/>',
        "truck": f'<path d="M-20 -12h22v20h-22zM2 -5h9l8 8v5H2z" fill="none" stroke="{FOREST}" stroke-width="3" stroke-linejoin="round"/><circle cx="-12" cy="11" r="4" fill="{FOREST}"/><circle cx="10" cy="11" r="4" fill="{FOREST}"/>',
        "ship": f'<path d="M-20 4h40l-5 10h-30z M-13 4v-9h9v9 M-4 4v-15h9v15 M5 4v-9h9v9" fill="none" stroke="{FOREST}" stroke-width="3" stroke-linejoin="round"/>',
        "plane": f'<path d="M0 -20c2 0 3 2 3 4v9l15 8v4L3 1v8l4 3v3l-7-2-7 2v-3l4-3V1l-15 4v-4l15-8v-9c0-2 1-4 3-4z" fill="none" stroke="{FOREST}" stroke-width="2.6" stroke-linejoin="round"/>',
    }
    body = (f'<path d="{path}" fill="none" stroke="{CRIMSON}" stroke-width="4" stroke-dasharray="10 9" stroke-linecap="round"/>' +
            "".join(f'<g transform="translate({x} {y})"><circle r="40" fill="{IVORY}" stroke="{FOREST}" stroke-opacity=".2" stroke-width="2"/>{glyph[k]}</g>'
                    for x, y, k in nodes) +
            f'<circle cx="70" cy="290" r="7" fill="{LEAF}"/><path d="M70 290V262" stroke="{LEAF}" stroke-width="3"/>'
            f'<circle cx="420" cy="30" r="7" fill="{CRIMSON}"/><path d="M420 37V60" stroke="{CRIMSON}" stroke-width="3"/>')
    return spot(body, "Freight forwarding: one route through truck, ship and aircraft")


def spot_docs():
    return spot(document(110, 60, 170, 220, -8) + document(170, 44, 170, 220, 4) +
                stamp(330, 214, 46) +
                f'<path d="M380 80l18 18 34-40" fill="none" stroke="{LEAF}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>',
                "Import and export documents")


def spot_customs():
    stripes = "".join(f'<rect x="{150 + k * 40}" y="150" width="20" height="20" fill="{CRIMSON}"/>' for k in range(8))
    return spot(f'<rect y="240" width="480" height="80" fill="{TINT_DEEP}"/>'
                f'<rect x="40" y="100" width="100" height="140" fill="{FOREST_3}"/>'
                f'<rect x="54" y="118" width="72" height="44" fill="{MIST_2}"/>'
                f'<path d="M30 100h120l-10-20H40z" fill="{FOREST}"/>'
                f'<rect x="140" y="150" width="320" height="20" fill="{IVORY}" stroke="{FOREST}" stroke-width="2"/>' + stripes +
                f'<rect x="132" y="140" width="20" height="100" fill="{FOREST}"/>' +
                document(300, 190, 90, 110, 6, 4) + stamp(380, 270, 30), "Customs coordination: checkpoint barrier and stamped documents")


def spot_cargo():
    body = f'<rect y="250" width="480" height="70" fill="{TINT_DEEP}"/>'
    for dx, dy, w, h in ((100, 180, 120, 70), (230, 180, 110, 70), (120, 110, 100, 70), (230, 110, 120, 70), (170, 40, 110, 70)):
        body += carton(dx, dy, w, h)
    body += (f'<rect x="88" y="250" width="270" height="16" fill="{FOREST_4}"/>'
             f'<path d="M100 266v14M222 266v14M346 266v14" stroke="{FOREST_4}" stroke-width="10"/>'
             f'<path d="M160 40V250M290 40V250" stroke="{CRIMSON}" stroke-width="5"/>'
             f'<g transform="translate(400 120)" fill="none" stroke="{FOREST}" stroke-width="4" stroke-linecap="round">'
             f'<path d="M-16 -30h32l-4 26a12 12 0 0 1-24 0z M0 8v20 M-12 28h24"/></g>')
    return spot(body, "Cargo handling: export cartons strapped on a pallet")


FILES = {
    "banner-about.svg": banner_about,
    "banner-services.svg": banner_services,
    "banner-sourcing.svg": banner_sourcing,
    "feature-air-cargo.svg": feature_air_cargo,
    "feature-textiles.svg": feature_textiles,
    "spot-air-freight.svg": spot_air,
    "spot-sea-freight.svg": spot_sea,
    "spot-land-transport.svg": spot_land,
    "spot-freight-forwarding.svg": spot_forwarding,
    "spot-import-export.svg": spot_docs,
    "spot-customs.svg": spot_customs,
    "spot-cargo-handling.svg": spot_cargo,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FILES.items():
        data = fn()
        (OUT / name).write_text(data)
        print(f"wrote src/assets/images/{name} ({len(data) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
