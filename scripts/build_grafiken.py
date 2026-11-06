#!/usr/bin/env python3
"""Erzeugt die Strichgrafiken unter grafiken/ als eigenstaendige HTML-Seiten.

Die Zeichnungen folgen der Bildsprache der Claude-Design-Blaetter
"BKM Leistungsbilder" und "BKM Schadensbilder": duenne Kontur in Deep Green,
helle Flaechen, Schraffuren fuer Schnitt und Erdreich, Lime nur als Akzent
(Abdichtung, Lupe). Es werden ausschliesslich Palettentoene aus brand.json
verwendet; Abstufungen entstehen ueber Deckkraft, nicht ueber neue Farben.

    python3 scripts/build_grafiken.py            # beide Grafiken
    python3 scripts/build_grafiken.py tor        # nur eine

Ausgabe: grafiken/<name>.html (Inline-SVG, Schriften relativ aus assets/fonts).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "grafiken"

# Palette (brand.json) -------------------------------------------------------
DEEP = "#1c4b42"
TRANS = "#287d4b"
LIME = "#b4e717"
STONE = "#494949"
MUTED = "#8a8a8a"
SAND = "#f6f5f2"
WHITE = "#ffffff"
HAIR = "#e3e1dc"
RULE = "#d9d7d3"


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pts(p) -> str:
    return " ".join(f"{f(x)},{f(y)}" for x, y in p)


def poly(p, fill="none", stroke=DEEP, sw=1.0, extra="") -> str:
    return (f'<polygon points="{pts(p)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linejoin="round" {extra}/>')


def line(a, b, stroke=DEEP, sw=1.0, extra="") -> str:
    return (f'<line x1="{f(a[0])}" y1="{f(a[1])}" x2="{f(b[0])}" y2="{f(b[1])}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" {extra}/>')


def pline(p, stroke=DEEP, sw=1.0, extra="") -> str:
    return (f'<polyline points="{pts(p)}" fill="none" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round" {extra}/>')


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def quad_lines(q, n, axis="u", stroke=DEEP, sw=0.8, extra="", t0=0.0, t1=1.0):
    """n Linien in einem Viereck q=(a,b,c,d), a-b oben, d-c unten.

    axis "u": Linien von oben nach unten (verlaufen parallel zu a-d),
    axis "v": Linien von links nach rechts (parallel zu a-b)."""
    a, b, c, d = q
    out = []
    for i in range(1, n):
        t = t0 + (t1 - t0) * i / n
        if axis == "u":
            out.append(line(lerp(a, b, t), lerp(d, c, t), stroke, sw, extra))
        else:
            out.append(line(lerp(a, d, t), lerp(b, c, t), stroke, sw, extra))
    return "".join(out)


FONTS = """
@font-face{font-family:"Unbounded";font-weight:900;src:url("../assets/fonts/Unbounded-Black.ttf") format("truetype")}
@font-face{font-family:"TT Norms Pro";font-weight:400;src:url("../assets/fonts/TT_Norms_Pro_Regular.ttf") format("truetype")}
@font-face{font-family:"TT Norms Pro";font-weight:700;src:url("../assets/fonts/TT_Norms_Pro_Bold.ttf") format("truetype")}
"""


def page(title: str, sub: str, svg: str, w: int, h: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<!-- Erzeugt mit scripts/build_grafiken.py. Nicht von Hand bearbeiten. -->
<style>{FONTS}
*{{box-sizing:border-box}}
html,body{{margin:0;background:{WHITE};font-family:"TT Norms Pro",sans-serif;color:{STONE}}}
.blatt{{max-width:{w}px;margin:0 auto;padding:32px 24px 40px}}
.kopf{{display:flex;align-items:baseline;gap:14px;border-bottom:1px solid {DEEP};padding-bottom:10px;margin-bottom:18px}}
.kopf h1{{font-family:"Unbounded",sans-serif;font-weight:900;font-size:22px;color:{DEEP};margin:0;letter-spacing:.01em}}
.kopf p{{margin:0;font-size:13px;color:{STONE}}}
figure{{margin:0;background:{SAND}}}
svg{{display:block;width:100%;height:auto}}
svg text{{font-family:"TT Norms Pro",sans-serif}}
svg .h{{font-family:"Unbounded",sans-serif;font-weight:900}}
svg .b{{font-weight:700}}
</style>
</head>
<body>
<main class="blatt">
<header class="kopf"><h1>{title}</h1><p>{sub}</p></header>
<figure>
<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">
{svg}
</svg>
</figure>
</main>
</body>
</html>
"""


# ===========================================================================
# 1. Einfahrt mit Doppelfluegeltor, Pfeilern und Lamellenzaun
# ===========================================================================

def hatch_defs() -> str:
    return f"""<defs>
<pattern id="hDiag" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">
  <line x1="0" y1="0" x2="0" y2="9" stroke="{DEEP}" stroke-width="0.9" stroke-opacity="0.75"/></pattern>
<pattern id="hDiagFine" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-28)">
  <line x1="0" y1="0" x2="0" y2="6" stroke="{DEEP}" stroke-width="0.7" stroke-opacity="0.55"/></pattern>
<pattern id="hVert" width="7" height="10" patternUnits="userSpaceOnUse">
  <line x1="0.5" y1="0" x2="0.5" y2="10" stroke="{DEEP}" stroke-width="0.8" stroke-opacity="0.7"/></pattern>
<pattern id="hVertWide" width="12" height="10" patternUnits="userSpaceOnUse">
  <line x1="0.5" y1="0" x2="0.5" y2="10" stroke="{DEEP}" stroke-width="0.7" stroke-opacity="0.45"/></pattern>
<pattern id="hGround" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(-62)">
  <line x1="0" y1="0" x2="0" y2="6" stroke="{DEEP}" stroke-width="0.8" stroke-opacity="0.55"/></pattern>
<pattern id="pSoil" width="18" height="18" patternUnits="userSpaceOnUse">
  <circle cx="5" cy="5" r="1.5" fill="{DEEP}" fill-opacity="0.18"/><circle cx="13" cy="12" r="1.2" fill="{DEEP}" fill-opacity="0.14"/></pattern>
<pattern id="pConc" width="22" height="22" patternUnits="userSpaceOnUse">
  <rect width="22" height="22" fill="{RULE}"/><circle cx="6" cy="7" r="1.6" fill="{DEEP}" fill-opacity="0.18"/><circle cx="16" cy="16" r="1.3" fill="{DEEP}" fill-opacity="0.14"/></pattern>
<pattern id="sCut" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="7" height="7" fill="{WHITE}"/><line x1="0" y1="0" x2="0" y2="7" stroke="{DEEP}" stroke-width="0.8" stroke-opacity="0.55"/></pattern>
<linearGradient id="gShadeR" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{DEEP}" stop-opacity="0"/><stop offset="1" stop-color="{DEEP}" stop-opacity="0.12"/></linearGradient>
<linearGradient id="gShadeL" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{DEEP}" stop-opacity="0.16"/><stop offset="1" stop-color="{DEEP}" stop-opacity="0"/></linearGradient>
<linearGradient id="gShadeDown" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{DEEP}" stop-opacity="0.14"/><stop offset="1" stop-color="{DEEP}" stop-opacity="0"/></linearGradient>
<linearGradient id="gFade" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{DEEP}" stop-opacity="0"/><stop offset="0.35" stop-color="{DEEP}" stop-opacity="1"/></linearGradient>
<radialGradient id="gWet" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="{DEEP}" stop-opacity="0.32"/><stop offset="1" stop-color="{DEEP}" stop-opacity="0"/></radialGradient>
</defs>"""


def pillar(x0, x1, top, bottom, cap_h=26, cap_over=10, depth=24, plaque=None, joints=()):
    """Gemauerter Torpfeiler mit Abdeckplatte, leicht von links gesehen."""
    s = []
    # Seitenflaeche (links, verkuerzt) mit Schraffur
    side = [(x0 - depth * 0.0, top), (x0, bottom)]
    # Koerper
    s.append(poly([(x0, top), (x1, top), (x1, bottom), (x0, bottom)], fill=WHITE, sw=2.2))
    # verkuerzte Seitenflaeche rechts als Streifen mit Senkrechtlinien
    sx = x0 + (x1 - x0) * 0.22
    s.append(poly([(x0, top), (sx, top), (sx, bottom), (x0, bottom)], fill="url(#hVert)", sw=0))
    s.append(poly([(x0, top), (sx, top), (sx, bottom), (x0, bottom)], fill="url(#gShadeL)", sw=0, stroke="none"))
    s.append(line((sx, top), (sx, bottom), sw=1.4))
    # Fugen
    for j in joints:
        y = top + (bottom - top) * j
        s.append(line((x0, y), (x1, y), sw=1.0, extra='stroke-opacity="0.6"'))
    # Abdeckplatte
    s.append(poly([(x0 - cap_over, top - cap_h), (x1 + cap_over * 0.6, top - cap_h),
                   (x1 + cap_over * 0.6, top), (x0 - cap_over, top)], fill=WHITE, sw=2.2))
    s.append(poly([(x0 - cap_over + 4, top - cap_h - 7), (x1 + cap_over * 0.6 - 4, top - cap_h - 7),
                   (x1 + cap_over * 0.6, top - cap_h), (x0 - cap_over, top - cap_h)], fill=WHITE, sw=1.6))
    s.append(poly([(x0 - cap_over, top - cap_h), (sx - 2, top - cap_h), (sx - 2, top), (x0 - cap_over, top)],
                  fill="url(#hVert)", sw=0, stroke="none"))
    # Hausnummernschild / Leuchte
    if plaque:
        px, py, pw, ph = plaque
        s.append(poly([(px, py), (px + pw, py), (px + pw, py + ph), (px, py + ph)], fill=WHITE, sw=1.8))
    return "".join(s)


def tor_scene() -> tuple[str, int, int]:
    W, H = 1932, 1932
    s = [hatch_defs()]
    s.append(f'<rect width="{W}" height="{H}" fill="{SAND}"/>')

    # ---------------- Haus im Hintergrund ----------------
    # linke Seitenflaeche des Hauptkubus (flach angeschnitten)
    s.append(poly([(170, 570), (525, 452), (535, 465), (535, 860), (497, 860), (497, 612), (170, 570)],
                  fill=WHITE, sw=0))
    s.append(poly([(178, 568), (525, 455), (530, 465), (530, 610), (178, 572)], fill="url(#hVert)", sw=0, stroke="none"))
    # Vordach-Volumen links
    s.append(poly([(170, 568), (497, 608), (497, 860), (170, 860)], fill=WHITE, sw=0))
    s.append(poly([(435, 615), (497, 612), (497, 860), (435, 860)], fill="url(#hVert)", sw=0, stroke="none"))
    s.append(poly([(435, 615), (497, 612), (497, 860), (435, 860)], fill="url(#gShadeR)", sw=0, stroke="none"))
    s.append(line((75, 560), (497, 607), sw=2.0))
    s.append(line((75, 572), (497, 619), sw=1.6))
    s.append(line((497, 607), (497, 860), sw=2.0))
    s.append(line((170, 570), (170, 860), sw=1.6))
    s.append(line((435, 618), (435, 860), sw=1.0))
    s.append(line((170, 568), (525, 452), sw=2.0))
    # Hauptkubus Front
    front = [(535, 465), (1347, 590), (1347, 905), (535, 905)]
    s.append(poly(front, fill=WHITE, sw=0))
    s.append(poly([(1347, 590), (1350, 585), (1350, 905), (1347, 905)], fill=WHITE, sw=1.6))
    # Attika
    s.append(pline([(525, 452), (1350, 580), (1350, 592), (535, 466), (525, 452)], sw=2.2))
    s.append(line((535, 466), (535, 860), sw=2.2))
    s.append(line((1347, 592), (1347, 905), sw=2.2))
    # Plattenfugen der Fassade
    for x in (720, 900, 1060, 1210):
        ytop = 466 + (x - 535) * (125 / 812)
        s.append(line((x, ytop), (x, 712 if 718 < x < 1296 else 905), sw=1.0, extra='stroke-opacity="0.7"'))
    # Wandleuchte
    s.append(poly([(636, 742), (650, 740), (650, 778), (636, 780)], fill=WHITE, sw=1.6))
    s.append(poly([(650, 740), (672, 737), (672, 772), (650, 778)], fill=WHITE, sw=1.8))
    s.append(quad_lines([(637, 744), (649, 742), (649, 777), (637, 779)], 4, "u", sw=0.8))
    # Durchfahrt / Carport-Nische
    s.append(poly([(718, 710), (1296, 767), (1296, 905), (718, 905)], fill=WHITE, sw=2.2))
    # Decke (Untersicht) diagonal schraffiert
    ceil = [(722, 714), (1292, 771), (1130, 788), (725, 790)]
    s.append(poly(ceil, fill="url(#hDiag)", sw=0, stroke="none"))
    s.append(poly(ceil, fill="url(#gShadeDown)", sw=0, stroke="none"))
    s.append(line((725, 790), (1130, 788), sw=1.4))
    s.append(line((1130, 788), (1292, 771), sw=1.4))
    # rechte Laibung senkrecht schraffiert
    lai = [(1130, 788), (1292, 771), (1292, 905), (1130, 905)]
    s.append(poly(lai, fill="url(#hVert)", sw=0, stroke="none"))
    s.append(line((1130, 788), (1130, 905), sw=1.4))
    # Rueckwand-Oeffnung (dunkel)
    s.append(poly([(858, 812), (1085, 812), (1085, 900), (858, 900)], fill=DEEP, sw=2.0))
    s.append(poly([(866, 820), (1077, 820), (1077, 900), (866, 900)], fill="none", stroke=WHITE, sw=1.2,
                  extra='stroke-opacity="0.35"'))

    # ---------------- Lamellenzaun links ----------------
    s.append(poly([(0, 812), (300, 828), (300, 1335), (0, 1340)], fill=WHITE, sw=0))
    x = 2
    while x < 280:
        s.append(poly([(x, 814 + x * 0.05), (x + 22, 815 + x * 0.05), (x + 22, 1336), (x, 1337)],
                      fill=WHITE, sw=1.4))
        s.append(poly([(x + 22, 815 + x * 0.05), (x + 33, 816 + x * 0.05), (x + 33, 1336), (x + 22, 1336)],
                      fill=DEEP, sw=0, stroke="none"))
        s.append(line((x + 3, 1300), (x + 19, 1300), sw=0.9, extra='stroke-opacity="0.6"'))
        x += 41
    # Sockel unter dem Zaun
    s.append(poly([(-4, 1330), (310, 1330), (312, 1352), (-4, 1355)], fill=WHITE, sw=2.0))
    s.append(poly([(-4, 1355), (312, 1352), (312, 1405), (-4, 1408)], fill="url(#hVertWide)", sw=0, stroke="none"))
    s.append(line((-4, 1408), (312, 1404), sw=2.0))

    # ---------------- Tor ----------------
    # Rahmen oben / unten (leicht fluchtend)
    top_l, top_r = 856, 892
    bot_l, bot_r = 1340, 1300
    s.append(poly([(487, top_l), (1440, top_r), (1440, bot_r), (487, bot_l)], fill=WHITE, sw=0))
    # festes Seitenfeld links mit senkrechten Staeben
    s.append(poly([(487, top_l), (580, top_l + 4), (580, bot_l - 4), (487, bot_l)], fill=WHITE, sw=2.2))
    for xx in (507, 527, 545, 562):
        s.append(poly([(xx, top_l + 2), (xx + 7, top_l + 2), (xx + 7, bot_l - 3), (xx, bot_l - 3)], fill=DEEP, sw=0,
                      stroke="none", extra='fill-opacity="0.85"'))
    s.append(line((487, top_l), (1440, top_r), sw=2.4))

    def wing(a, b, c, d, n):
        out = [poly([a, b, c, d], fill=WHITE, sw=2.4)]
        ia, ib = lerp(a, c, 0.012), lerp(b, d, 0.012)
        ic, id_ = lerp(c, a, 0.012), lerp(d, b, 0.012)
        out.append(poly([ia, ib, ic, id_], fill="none", sw=1.2))
        out.append(quad_lines([ia, ib, ic, id_], n, "v", sw=1.2))
        return "".join(out)

    lw = [(583, 880), (997, 888), (997, 1322), (583, 1334)]
    rw = [(1018, 888), (1352, 895), (1352, 1302), (1018, 1320)]
    s.append(wing(*lw, 18))
    s.append(wing(*rw, 18))
    # Mittelpfosten
    s.append(poly([(1000, 886), (1015, 887), (1015, 1334), (1000, 1334)], fill=WHITE, sw=2.0))
    s.append(line((1007, 1334), (1007, 1348), sw=4))
    # Griffe
    s.append(poly([(966, 1038), (980, 1037), (980, 1176), (966, 1177)], fill=WHITE, sw=2.0))
    s.append(poly([(970, 1046), (976, 1046), (976, 1168), (970, 1168)], fill=DEEP, sw=0, stroke="none"))
    s.append(poly([(1024, 1080), (1032, 1080), (1032, 1124), (1024, 1124)], fill=WHITE, sw=1.8))
    # rechtes Seitenfeld (in Fluchtung, dicht schraffiert)
    rs = [(1352, 895), (1440, 892), (1440, 1300), (1352, 1302)]
    s.append(poly(rs, fill=WHITE, sw=2.0))
    s.append(poly(rs, fill="url(#hVert)", sw=0, stroke="none"))
    s.append(poly(rs, fill="url(#gShadeR)", sw=0, stroke="none"))
    for xx in (1414, 1428):
        s.append(line((xx, 905), (xx, 1298), sw=2.6))
    # Bodenschiene + Schattenschraffur
    s.append(line((487, bot_l), (1440, bot_r), sw=2.4))
    sh = [(487, bot_l), (1440, bot_r), (1500, bot_r + 22), (560, bot_l + 30)]
    s.append(poly(sh, fill="url(#hGround)", sw=0, stroke="none"))
    s.append(line((560, 1360), (590, 1372), sw=1.4))

    # ---------------- Pfeiler ----------------
    s.append(pillar(272, 488, 800, 1396, cap_h=24, cap_over=6, plaque=(385, 876, 60, 68), joints=(0.5,)))
    s.append(pillar(1416, 1584, 876, 1322, cap_h=20, cap_over=6, plaque=(1522, 935, 38, 46), joints=(0.52,)))

    # kleine Pforte rechts
    pf = [(1584, 940), (1652, 944), (1652, 1300), (1584, 1302)]
    s.append(poly(pf, fill=WHITE, sw=2.0))
    s.append(poly([(1584, 922), (1690, 925), (1690, 945), (1584, 942)], fill=WHITE, sw=1.6))
    s.append(quad_lines(pf, 16, "v", sw=1.0))
    s.append(poly([(1640, 1040), (1648, 1040), (1648, 1120), (1640, 1120)], fill=DEEP, sw=0, stroke="none"))
    s.append(line((1680, 925), (1680, 1300), sw=3.0))
    s.append(pillar(1652, 1815, 890, 1300, cap_h=20, cap_over=6, plaque=(1764, 945, 26, 50), joints=(0.52,)))

    # ---------------- Boden ----------------
    # Gehweg links mit Bordstein
    walk = [(100, 1505), (650, 1462), (688, 1440), (690, 1418), (560, 1388), (310, 1402), (100, 1430)]
    s.append(poly(walk, fill=WHITE, sw=0))
    # Pflasterraster
    for i, yy in enumerate((1418, 1434, 1452, 1470, 1488)):
        s.append(line((130, yy + 6), (640, yy - 30 + i * 2), sw=0.8, extra='stroke-opacity="0.45"'))
    for xx in range(170, 640, 70):
        s.append(line((xx, 1405), (xx - 18, 1495), sw=0.8, extra='stroke-opacity="0.35"'))
    s.append(pline([(100, 1490), (640, 1446), (676, 1430), (684, 1416)], sw=2.0))
    s.append(pline([(100, 1506), (650, 1462), (688, 1440), (692, 1418)], sw=2.0))
    s.append(line((460, 1470), (462, 1485), sw=1.2))
    # Fahrbahnkante rechts
    s.append(pline([(1440, 1300), (1520, 1326), (1890, 1336)], sw=1.6))
    s.append(poly([(1500, 1324), (1890, 1334), (1890, 1342), (1500, 1334)], fill="url(#hGround)", sw=0, stroke="none"))
    s.append(line((1530, 1340), (1880, 1350), sw=1.0, extra='stroke-opacity="0.6"'))
    s.append(line((300, 1530), (60, 1545), sw=1.0, extra='stroke-opacity="0.5"'))
    return "\n".join(s), W, H


# ===========================================================================
# 2. Planblatt Holzhaus: Isometrie, Tragwerk, Schnitte, Grundriss, Tabellen
# ===========================================================================

C30, S30 = math.cos(math.radians(30)), 0.5


class Iso:
    """Isometrische Projektion: x nach rechts unten, y nach links unten, z nach oben."""

    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def __call__(self, x, y, z=0.0):
        return (self.ox + (x - y) * C30 * self.s, self.oy + (x + y) * S30 * self.s - z * self.s)

    def P(self, *p3):
        return [self(*q) for q in p3]


def text(x, y, t, size=12, cls="", fill=STONE, anchor="start", extra=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}"{c} {extra}>{t}</text>')


def para(x, y, lines, size=10.5, lh=14.5, fill=STONE):
    return "".join(text(x, y + i * lh, t, size, fill=fill) for i, t in enumerate(lines))


def house(iso, *, W=8.0, L=10.0, H=3.0, R=2.6, porch=2.2, deck=True, clad=True, roof=True,
          seams=True, detail=1.0, frame_only_half=False, shadow=True, sock_lime=True):
    """Holzhaus mit Satteldach (First entlang y), offener Veranda an der Giebelseite y=L."""
    o = 0.45            # Dachueberstand
    s = []
    P = iso.P
    Lc = L - porch      # geschlossener Teil
    sw_main = 1.1 * detail
    sw_fine = 0.55 * detail
    # Schlagschatten
    if shadow:
        s.append(poly([iso(W + 1.1, -0.6, -0.9), iso(W + 1.1, L + 1.7, -0.9), iso(-2.6, L + 3.6, -0.9),
                       iso(-2.6, 1.0, -0.9)], fill=DEEP, stroke="none", sw=0, extra='fill-opacity="0.13"'))
    # Terrasse auf Pfaehlen
    if deck:
        dx0, dx1, dy0, dy1, dz = -1.2, W + 1.1, -0.6, L + 1.7, 0.0
        for px in (dx0 + 0.2, (dx0 + dx1) / 2, dx1 - 0.2):
            for py in (dy1 - 0.2, (dy0 + dy1) / 2, dy0 + 0.6):
                if px > W - 0.5 and py < 1.0:
                    continue
                s.append(poly(P((px, py, -0.9), (px + 0.18, py, -0.9), (px + 0.18, py, -0.15), (px, py, -0.15)),
                              fill=WHITE, sw=sw_fine))
                s.append(poly(P((px, py, -0.9), (px, py + 0.18, -0.9), (px, py + 0.18, -0.15), (px, py, -0.15)),
                              fill=WHITE, sw=sw_fine))
        top = P((dx0, dy0, dz), (dx1, dy0, dz), (dx1, dy1, dz), (dx0, dy1, dz))
        s.append(poly(top, fill=WHITE, sw=sw_main))
        # Dielen (entlang x)
        n = int((dy1 - dy0) / 0.16)
        for i in range(1, n):
            yy = dy0 + (dy1 - dy0) * i / n
            s.append(line(iso(dx0, yy), iso(dx1, yy), sw=sw_fine * 0.7, extra='stroke-opacity="0.55"'))
        s.append(poly(P((dx0, dy1, 0), (dx1, dy1, 0), (dx1, dy1, -0.18), (dx0, dy1, -0.18)), fill=WHITE, sw=sw_main))
        s.append(poly(P((dx1, dy0, 0), (dx1, dy1, 0), (dx1, dy1, -0.18), (dx1, dy0, -0.18)), fill=WHITE, sw=sw_main))
        # Stufen vor der Veranda
        for k in range(3):
            z = -0.18 - k * 0.2
            yy = dy1 + 0.3 * (k + 1)
            s.append(poly(P((1.6, dy1, z + 0.18), (3.6, dy1, z + 0.18), (3.6, yy, z + 0.18), (1.6, yy, z + 0.18)),
                          fill=WHITE, sw=sw_fine))
            s.append(poly(P((1.6, yy, z + 0.18), (3.6, yy, z + 0.18), (3.6, yy, z), (1.6, yy, z)), fill=WHITE, sw=sw_fine))
    # Sockelabdichtung (Lime): Streifen am Wandfuss
    if sock_lime:
        s.append(poly(P((W, 0, 0), (W, Lc, 0), (W, Lc, 0.22), (W, 0, 0.22)), fill=LIME, stroke=DEEP, sw=sw_fine))
    # Seitenwand x=W (geschlossener Teil)
    side = P((W, 0, 0.22 if sock_lime else 0), (W, Lc, 0.22 if sock_lime else 0), (W, Lc, H), (W, 0, H))
    s.append(poly(side, fill=WHITE, sw=sw_main))
    s.append(poly(side, fill=DEEP, stroke="none", sw=0, extra='fill-opacity="0.05"'))
    if clad:
        n = int(Lc / 0.14)
        for i in range(1, n):
            yy = Lc * i / n
            s.append(line(iso(W, yy, 0.24), iso(W, yy, H), sw=sw_fine * 0.75, extra='stroke-opacity="0.6"'))
    # Fenster in der Seitenwand
    for (y0, y1, z0, z1) in ((1.0, 2.4, 1.0, 2.2), (4.6, 5.6, 0.9, 2.3)):
        if y1 > Lc:
            continue
        s.append(poly(P((W, y0, z0), (W, y1, z0), (W, y1, z1), (W, y0, z1)), fill=WHITE, sw=sw_main))
        s.append(poly(P((W, y0 + 0.08, z0 + 0.08), (W, y1 - 0.08, z0 + 0.08), (W, y1 - 0.08, z1 - 0.08),
                        (W, y0 + 0.08, z1 - 0.08)), fill=DEEP, stroke=DEEP, sw=sw_fine, extra='fill-opacity="0.12"'))
    # Rueckversetzte Giebelwand (Veranda)
    back = P((0, Lc, 0), (W, Lc, 0), (W, Lc, H), (0, Lc, H))
    s.append(poly(back, fill=WHITE, sw=sw_main))
    s.append(poly(back, fill=DEEP, stroke="none", sw=0, extra='fill-opacity="0.09"'))
    if clad:
        n = int(W / 0.14)
        for i in range(1, n):
            xx = W * i / n
            s.append(line(iso(xx, Lc, 0), iso(xx, Lc, H), sw=sw_fine * 0.7, extra='stroke-opacity="0.45"'))
    # Tuer + Fenster in der Verandawand
    s.append(poly(P((1.2, Lc, 0), (2.2, Lc, 0), (2.2, Lc, 2.2), (1.2, Lc, 2.2)), fill=WHITE, sw=sw_main))
    s.append(poly(P((4.4, Lc, 0.9), (6.6, Lc, 0.9), (6.6, Lc, 2.3), (4.4, Lc, 2.3)), fill=WHITE, sw=sw_main))
    s.append(poly(P((4.5, Lc, 1.0), (6.5, Lc, 1.0), (6.5, Lc, 2.2), (4.5, Lc, 2.2)), fill=DEEP, sw=sw_fine,
                  extra='fill-opacity="0.18"'))
    s.append(line(iso(5.5, Lc, 1.0), iso(5.5, Lc, 2.2), sw=sw_fine))
    # Verandaseite x=W: oberer Riegel + Stuetzen
    for (px, py) in ((W - 0.2, L - 0.2), (0.0, L - 0.2), (W / 2 - 0.1, L - 0.2)):
        s.append(poly(P((px, py + 0.2, 0), (px + 0.2, py + 0.2, 0), (px + 0.2, py + 0.2, H), (px, py + 0.2, H)),
                      fill=WHITE, sw=sw_main))
        s.append(poly(P((px + 0.2, py, 0), (px + 0.2, py + 0.2, 0), (px + 0.2, py + 0.2, H), (px + 0.2, py, H)),
                      fill=WHITE, sw=sw_main, extra=''))
    s.append(poly(P((W, Lc, H - 0.3), (W, L, H - 0.3), (W, L, H), (W, Lc, H)), fill=WHITE, sw=sw_main))
    # Giebeldreieck vorn (y=L), schwebend auf Riegel
    gab = P((0, L, H - 0.3), (W, L, H - 0.3), (W, L, H), (W / 2, L, H + R), (0, L, H))
    s.append(poly(gab, fill=WHITE, sw=sw_main))
    if clad:
        n = int(W / 0.14)
        for i in range(1, n):
            xx = W * i / n
            ztop = H + R * (1 - abs(xx - W / 2) / (W / 2))
            s.append(line(iso(xx, L, H), iso(xx, L, ztop), sw=sw_fine * 0.75, extra='stroke-opacity="0.6"'))
    s.append(line(iso(0, L, H), iso(W, L, H), sw=sw_main))
    # Giebelfenster
    s.append(poly(P((W / 2 - 0.5, L, H + 0.5), (W / 2 + 0.5, L, H + 0.5), (W / 2 + 0.5, L, H + 1.5),
                    (W / 2 - 0.5, L, H + 1.5)), fill=WHITE, sw=sw_main))
    s.append(poly(P((W / 2 - 0.42, L, H + 0.58), (W / 2 + 0.42, L, H + 0.58), (W / 2 + 0.42, L, H + 1.42),
                    (W / 2 - 0.42, L, H + 1.42)), fill=DEEP, sw=sw_fine, extra='fill-opacity="0.14"'))
    if not roof:
        return "".join(s)
    # Dachflaechen
    ez = H - o * R / (W / 2)
    rb = P((-o, -o, ez), (W / 2, -o, H + R), (W / 2, L + o, H + R), (-o, L + o, ez))
    rf = P((W / 2, -o, H + R), (W + o, -o, ez), (W + o, L + o, ez), (W / 2, L + o, H + R))
    s.append(poly(rb, fill=WHITE, sw=sw_main))
    s.append(poly(rb, fill=RULE, stroke="none", sw=0, extra='fill-opacity="0.55"'))
    s.append(poly(rf, fill=WHITE, sw=sw_main))
    if seams:
        n = int((L + 2 * o) / 0.32)
        for i in range(1, n):
            yy = -o + (L + 2 * o) * i / n
            s.append(line(iso(W / 2, yy, H + R), iso(W + o, yy, ez), sw=sw_fine * 0.8, extra='stroke-opacity="0.7"'))
            s.append(line(iso(W / 2, yy, H + R), iso(-o, yy, ez), sw=sw_fine * 0.7, extra='stroke-opacity="0.45"'))
    # Dachrand vorn (Stirnbrett)
    t = 0.14
    s.append(poly(P((-o, L + o, ez), (W / 2, L + o, H + R), (W / 2, L + o, H + R - t), (-o, L + o, ez - t)),
                  fill=WHITE, sw=sw_main))
    s.append(poly(P((W / 2, L + o, H + R), (W + o, L + o, ez), (W + o, L + o, ez - t), (W / 2, L + o, H + R - t)),
                  fill=WHITE, sw=sw_main))
    s.append(poly(P((W + o, -o, ez), (W + o, L + o, ez), (W + o, L + o, ez - t), (W + o, -o, ez - t)),
                  fill=WHITE, sw=sw_main))
    # Schornstein
    cx, cy = W / 2 - 1.1, 2.2
    zr = H + R - (W / 2 - (cx + 0.55)) * R / (W / 2)
    zb = H + R - (W / 2 - cx) * R / (W / 2)
    s.append(poly(P((cx, cy + 0.55, zb), (cx + 0.55, cy + 0.55, zr), (cx + 0.55, cy + 0.55, H + R + 0.9),
                    (cx, cy + 0.55, H + R + 0.9)), fill=WHITE, sw=sw_main))
    s.append(poly(P((cx + 0.55, cy, zr), (cx + 0.55, cy + 0.55, zr), (cx + 0.55, cy + 0.55, H + R + 0.9),
                    (cx + 0.55, cy, H + R + 0.9)), fill=WHITE, sw=sw_main, extra=''))
    s.append(poly(P((cx + 0.55, cy, zr), (cx + 0.55, cy + 0.55, zr), (cx + 0.55, cy + 0.55, H + R + 0.9),
                    (cx + 0.55, cy, H + R + 0.9)), fill=DEEP, stroke="none", sw=0, extra='fill-opacity="0.08"'))
    s.append(poly(P((cx - 0.05, cy - 0.05, H + R + 0.9), (cx + 0.6, cy - 0.05, H + R + 0.9),
                    (cx + 0.6, cy + 0.6, H + R + 0.9), (cx - 0.05, cy + 0.6, H + R + 0.9)), fill=WHITE, sw=sw_main))
    # Dachfenster in der vorderen Flaeche
    yy0, yy1 = 3.2, 4.0
    a0, a1 = 0.45, 0.62
    def onroof(t, yy):
        x = W / 2 + t * (W / 2 + o)
        return iso(x, yy, H + R - t * (R + o * R / (W / 2)))
    s.append(poly([onroof(a0, yy0), onroof(a1, yy0), onroof(a1, yy1), onroof(a0, yy1)], fill=WHITE, sw=sw_main))
    s.append(poly([onroof(a0 + .02, yy0 + .08), onroof(a1 - .02, yy0 + .08), onroof(a1 - .02, yy1 - .08),
                   onroof(a0 + .02, yy1 - .08)], fill=DEEP, sw=sw_fine, extra='fill-opacity="0.15"'))
    return "".join(s)


def frame(iso, *, W=8.0, L=10.0, H=3.0, R=2.6, sw=0.9, clad_part=False, lime=False):
    """Tragwerk (Staender, Pfetten, Sparren) als Drahtmodell, optional teilweise beplankt."""
    s = []
    P = iso.P
    o = 0.45
    ez = H - o * R / (W / 2)
    # Fundamentbalken / Schwelle
    for (a, b) in (((0, 0), (W, 0)), ((W, 0), (W, L)), ((W, L), (0, L)), ((0, L), (0, 0))):
        s.append(line(iso(*a, 0), iso(*b, 0), sw=sw * 1.4))
    if lime:
        s.append(pline([iso(0, L, 0.05), iso(W, L, 0.05), iso(W, 0, 0.05)], stroke=LIME, sw=sw * 4.5))
        s.append(pline([iso(0, L, 0), iso(W, L, 0), iso(W, 0, 0)], sw=sw * 1.2))
    # Staender
    xs = [0, W / 3, 2 * W / 3, W]
    ys = [0, L / 4, L / 2, 3 * L / 4, L]
    for x in xs:
        for y in (0, L):
            s.append(line(iso(x, y, 0), iso(x, y, H), sw=sw))
    for y in ys:
        for x in (0, W):
            s.append(line(iso(x, y, 0), iso(x, y, H), sw=sw))
    # Rahm / Riegel
    for z in (H, H / 2):
        for (a, b) in (((0, 0), (W, 0)), ((W, 0), (W, L)), ((W, L), (0, L)), ((0, L), (0, 0))):
            s.append(line(iso(*a, z), iso(*b, z), sw=sw if z == H else sw * 0.6))
    # Streben (Andreaskreuze) in der Seitenwand
    for i in range(len(ys) - 1):
        s.append(line(iso(W, ys[i], 0), iso(W, ys[i + 1], H), sw=sw * 0.6, extra='stroke-opacity="0.7"'))
    # Sparren + First
    for y in [L * i / 8 for i in range(9)]:
        s.append(pline([iso(-o, y, ez), iso(W / 2, y, H + R), iso(W + o, y, ez)], sw=sw))
    s.append(line(iso(W / 2, -o, H + R), iso(W / 2, L + o, H + R), sw=sw * 1.4))
    for (x, z) in ((-o, ez), (W + o, ez), (W / 4, H + R / 2), (3 * W / 4, H + R / 2)):
        s.append(line(iso(x, -o, z), iso(x, L + o, z), sw=sw * 0.8))
    if clad_part:
        # Dachdeckung zu ca. 60 % (Stehfalz) und Bekleidung der Rueckwand
        yc = L * 0.55
        rf = P((W / 2, -o, H + R), (W + o, -o, ez), (W + o, yc, ez), (W / 2, yc, H + R))
        rb = P((-o, -o, ez), (W / 2, -o, H + R), (W / 2, yc, H + R), (-o, yc, ez))
        s.insert(0, poly(rb, fill=WHITE, sw=sw, extra='fill-opacity="0.92"'))
        n = int((yc + o) / 0.3)
        roof = [poly(rf, fill=WHITE, sw=sw)]
        for i in range(1, n):
            yy = -o + (yc + o) * i / n
            roof.append(line(iso(W / 2, yy, H + R), iso(W + o, yy, ez), sw=sw * 0.5, extra='stroke-opacity="0.75"'))
        roof.append(poly(P((W + o, -o, ez), (W + o, yc, ez), (W + o, yc, ez - 0.14), (W + o, -o, ez - 0.14)),
                         fill=WHITE, sw=sw))
        # Seitenwand zu 40 % beplankt
        yw = L * 0.38
        side = P((W, 0, 0), (W, yw, 0), (W, yw, H), (W, 0, H))
        roof.insert(0, poly(side, fill=WHITE, sw=sw))
        n = int(yw / 0.14)
        for i in range(1, n):
            yy = yw * i / n
            roof.insert(1, line(iso(W, yy, 0), iso(W, yy, H), sw=sw * 0.45, extra='stroke-opacity="0.6"'))
        roof.insert(1, poly(P((W, 0.7, 1.0), (W, 2.1, 1.0), (W, 2.1, 2.2), (W, 0.7, 2.2)), fill=WHITE, sw=sw))
        s.extend(roof)
    return "".join(s)


def leader(a, b, label=None, size=9, anchor="start", dot=True):
    out = [line(a, b, sw=0.7)]
    if dot:
        out.append(f'<circle cx="{f(a[0])}" cy="{f(a[1])}" r="2" fill="{DEEP}"/>')
    if label:
        dx = 4 if anchor == "start" else -4
        out.append(text(b[0] + dx, b[1] + 3, label, size, fill=DEEP, anchor=anchor))
    return "".join(out)


def dim_h(x0, x1, y, label, size=8.5):
    t = 4
    return (line((x0, y), (x1, y), sw=0.6) + line((x0 - t, y + t), (x0 + t, y - t), sw=0.9)
            + line((x1 - t, y + t), (x1 + t, y - t), sw=0.9)
            + line((x0, y - 8), (x0, y + 8), sw=0.5) + line((x1, y - 8), (x1, y + 8), sw=0.5)
            + text((x0 + x1) / 2, y - 4, label, size, fill=DEEP, anchor="middle"))


def grid_axes(xs, ys, x0, x1, y0, y1, labels_x="ABCDEF", labels_y="123456"):
    s = []
    for i, x in enumerate(xs):
        s.append(line((x, y0 - 18), (x, y1 + 18), sw=0.5, extra='stroke-dasharray="6 3 1.5 3" stroke-opacity="0.6"'))
        s.append(f'<circle cx="{f(x)}" cy="{f(y0 - 28)}" r="9" fill="{WHITE}" stroke="{DEEP}" stroke-width="0.8"/>')
        s.append(text(x, y0 - 25, labels_x[i], 8.5, "b", DEEP, "middle"))
    for i, y in enumerate(ys):
        s.append(line((x0 - 18, y), (x1 + 18, y), sw=0.5, extra='stroke-dasharray="6 3 1.5 3" stroke-opacity="0.6"'))
        s.append(f'<circle cx="{f(x0 - 28)}" cy="{f(y)}" r="9" fill="{WHITE}" stroke="{DEEP}" stroke-width="0.8"/>')
        s.append(text(x0 - 28, y + 3, labels_y[i], 8.5, "b", DEEP, "middle"))
    return "".join(s)


def floor_plan(x0, y0, sc=27):
    """Grundriss EG 8 x 10 m mit Wandstaerke, Treppe, Kueche, Bad, Veranda."""
    s = []
    W, L, t = 8 * sc, 10 * sc, 0.3 * sc
    xs = [x0, x0 + W / 2, x0 + W]
    ys = [y0, y0 + L * 0.35, y0 + L * 0.78, y0 + L]
    s.append(grid_axes(xs, ys, x0, x0 + W, y0, y0 + L))
    # Aussenwaende (geschnitten = schraffiert)
    outer = [(x0, y0), (x0 + W, y0), (x0 + W, y0 + L * 0.78), (x0, y0 + L * 0.78)]
    inner = [(x0 + t, y0 + t), (x0 + W - t, y0 + t), (x0 + W - t, y0 + L * 0.78 - t), (x0 + t, y0 + L * 0.78 - t)]
    s.append(f'<path d="M{pts(outer).replace(" ", " L")} Z M{pts(inner[::-1]).replace(" ", " L")} Z" '
             f'fill="url(#sCut)" fill-rule="evenodd" stroke="{DEEP}" stroke-width="1.2"/>')
    s.append(poly(inner, fill=WHITE, sw=0.6))
    # Veranda
    s.append(poly([(x0, y0 + L * 0.78), (x0 + W, y0 + L * 0.78), (x0 + W, y0 + L), (x0, y0 + L)], fill=WHITE, sw=0.7,
                  extra='stroke-dasharray="4 3"'))
    for i in range(1, 12):
        yy = y0 + L * 0.78 + (L * 0.22) * i / 12
        s.append(line((x0, yy), (x0 + W, yy), sw=0.4, extra='stroke-opacity="0.45"'))
    for px in (x0, x0 + W / 2 - 3, x0 + W - 6):
        s.append(poly([(px, y0 + L - 6), (px + 6, y0 + L - 6), (px + 6, y0 + L), (px, y0 + L)], fill=DEEP, sw=0))
    # Innenwaende
    iw = 0.12 * sc
    for r in ([(x0 + W / 2 - iw / 2, y0 + t), (x0 + W / 2 + iw / 2, y0 + t),
               (x0 + W / 2 + iw / 2, y0 + L * 0.35), (x0 + W / 2 - iw / 2, y0 + L * 0.35)],
              [(x0 + t, y0 + L * 0.35 - iw / 2), (x0 + W * 0.62, y0 + L * 0.35 - iw / 2),
               (x0 + W * 0.62, y0 + L * 0.35 + iw / 2), (x0 + t, y0 + L * 0.35 + iw / 2)],
              [(x0 + W * 0.62 - iw, y0 + L * 0.35), (x0 + W * 0.62, y0 + L * 0.35),
               (x0 + W * 0.62, y0 + L * 0.55), (x0 + W * 0.62 - iw, y0 + L * 0.55)]):
        s.append(poly(r, fill=DEEP, sw=0.6))
    # Treppe
    tx, ty, tw, tl = x0 + t + 4, y0 + L * 0.37, W * 0.2, L * 0.36
    s.append(poly([(tx, ty), (tx + tw, ty), (tx + tw, ty + tl), (tx, ty + tl)], fill=WHITE, sw=0.8))
    for i in range(1, 13):
        s.append(line((tx, ty + tl * i / 13), (tx + tw, ty + tl * i / 13), sw=0.5))
    s.append(pline([(tx + tw / 2, ty + tl - 6), (tx + tw / 2, ty + 10)], sw=0.7))
    s.append(poly([(tx + tw / 2 - 3, ty + 14), (tx + tw / 2 + 3, ty + 14), (tx + tw / 2, ty + 8)], fill=DEEP, sw=0.5))
    # Kueche (Zeile oben rechts) + Bad (oben links)
    s.append(poly([(x0 + W / 2 + 6, y0 + t), (x0 + W - t, y0 + t), (x0 + W - t, y0 + t + 16), (x0 + W / 2 + 6, y0 + t + 16)],
                  fill=WHITE, sw=0.7))
    for k in range(1, 5):
        xx = x0 + W / 2 + 6 + (W / 2 - t - 6) * k / 5
        s.append(line((xx, y0 + t), (xx, y0 + t + 16), sw=0.5))
    s.append(f'<circle cx="{f(x0 + W * 0.85)}" cy="{f(y0 + t + 8)}" r="4.5" fill="none" stroke="{DEEP}" stroke-width="0.6"/>')
    s.append(poly([(x0 + t + 6, y0 + t + 6), (x0 + t + 30, y0 + t + 6), (x0 + t + 30, y0 + t + 50), (x0 + t + 6, y0 + t + 50)],
                  fill=WHITE, sw=0.7, extra='rx="6"'))
    s.append(f'<rect x="{f(x0 + W / 2 - 40)}" y="{f(y0 + t + 6)}" width="22" height="16" rx="6" fill="none" '
             f'stroke="{DEEP}" stroke-width="0.6"/>')
    # Tisch
    s.append(f'<rect x="{f(x0 + W * 0.66)}" y="{f(y0 + L * 0.47)}" width="34" height="50" fill="none" stroke="{DEEP}" stroke-width="0.7"/>')
    for (dx, dy) in ((-8, 8), (-8, 30), (36, 8), (36, 30)):
        s.append(f'<rect x="{f(x0 + W * 0.66 + dx)}" y="{f(y0 + L * 0.47 + dy)}" width="6" height="10" fill="none" '
                 f'stroke="{DEEP}" stroke-width="0.5"/>')
    # Tueroeffnung + Aufschlag
    dxp = x0 + W * 0.2
    dy_ = y0 + L * 0.78
    s.append(f'<rect x="{f(dxp)}" y="{f(dy_ - t - 1)}" width="{f(0.95 * sc)}" height="{f(t + 2)}" fill="{WHITE}"/>')
    s.append(f'<path d="M{f(dxp)},{f(dy_ - t)} l0,{f(-0.95 * sc)} a{f(0.95 * sc)},{f(0.95 * sc)} 0 0 1 {f(0.95 * sc)},{f(0.95 * sc)}" '
             f'fill="none" stroke="{DEEP}" stroke-width="0.6"/>')
    # Fenster in Aussenwand
    for (fx, fy, fw, fh) in ((x0 + W - t - 1, y0 + L * 0.1, t + 2, 1.4 * sc), (x0 + W - t - 1, y0 + L * 0.48, t + 2, sc),
                             (x0 + W * 0.58, y0 + L * 0.78 - t - 1, 2.2 * sc, t + 2)):
        s.append(f'<rect x="{f(fx)}" y="{f(fy)}" width="{f(fw)}" height="{f(fh)}" fill="{WHITE}" stroke="{DEEP}" stroke-width="0.7"/>')
    # Massketten
    s.append(dim_h(x0, x0 + W, y0 + L + 40, "8,00"))
    s.append(dim_h(x0, x0 + W / 2, y0 + L + 58, "4,00"))
    s.append(dim_h(x0 + W / 2, x0 + W, y0 + L + 58, "4,00"))
    # Nordpfeil
    nx, ny = x0 + W + 110, y0 + L + 30
    s.append(f'<circle cx="{f(nx)}" cy="{f(ny)}" r="16" fill="none" stroke="{DEEP}" stroke-width="0.9"/>')
    s.append(f'<path d="M{f(nx)},{f(ny - 16)} L{f(nx)},{f(ny)} L{f(nx + 16)},{f(ny)}" fill="none" stroke="{DEEP}" stroke-width="0.9"/>')
    s.append(text(nx, ny - 21, "N", 8.5, "b", DEEP, "middle"))
    # Raumbezeichnungen
    for (tx_, ty_, t_) in ((x0 + W * 0.75, y0 + L * 0.2, "Wohnen / Kochen"), (x0 + W * 0.25, y0 + L * 0.2, "Bad"),
                           (x0 + W * 0.8, y0 + L * 0.66, "Essen"), (x0 + W * 0.5, y0 + L * 0.9, "Veranda")):
        s.append(text(tx_, ty_, t_, 8, fill=DEEP, anchor="middle"))
    return "".join(s)


def section(x0, y0, sc, kind="giebel"):
    """Schnitt / Ansicht. giebel: Querschnitt mit Treppe. laengs: Laengsschnitt."""
    s = []
    if kind == "giebel":
        W, H, R = 6.2 * sc, 3.0 * sc, 2.4 * sc
        b = y0
        # Gelaende + Fundament (Lime = Abdichtung erdberuehrt)
        s.append(line((x0 - 40, b + 0.5 * sc), (x0 + W + 1.6 * sc + 40, b + 0.5 * sc), sw=0.8))
        s.append(poly([(x0 - 40, b + 0.5 * sc), (x0 + W + 1.6 * sc + 40, b + 0.5 * sc),
                       (x0 + W + 1.6 * sc + 40, b + 0.9 * sc), (x0 - 40, b + 0.9 * sc)], fill="url(#pSoil)", sw=0, stroke="none"))
        for fx in (x0, x0 + W - 0.3 * sc):
            s.append(poly([(fx, b), (fx + 0.3 * sc, b), (fx + 0.3 * sc, b + 0.9 * sc), (fx, b + 0.9 * sc)], fill="url(#sCut)", sw=0.9))
            s.append(line((fx - 2, b + 0.1 * sc), (fx - 2, b + 0.9 * sc), stroke=LIME, sw=3))
        # Bodenplatte
        s.append(poly([(x0, b - 0.25 * sc), (x0 + W, b - 0.25 * sc), (x0 + W, b), (x0, b)], fill="url(#sCut)", sw=0.9))
        # Waende
        for fx in (x0, x0 + W - 0.3 * sc):
            s.append(poly([(fx, b - 0.25 * sc), (fx + 0.3 * sc, b - 0.25 * sc), (fx + 0.3 * sc, b - H), (fx, b - H)],
                          fill="url(#sCut)", sw=1.1))
        # Dach
        rp = [(x0 - 0.4 * sc, b - H + 0.3 * sc), (x0 + W / 2, b - H - R), (x0 + W + 0.4 * sc, b - H + 0.3 * sc)]
        s.append(pline(rp, sw=2.2))
        s.append(pline([(p[0], p[1] + 9) for p in rp], sw=0.8))
        # Decke + Galerie
        s.append(poly([(x0 + 0.3 * sc, b - H + 0.1 * sc), (x0 + W * 0.45, b - H + 0.1 * sc),
                       (x0 + W * 0.45, b - H + 0.3 * sc), (x0 + 0.3 * sc, b - H + 0.3 * sc)], fill="url(#sCut)", sw=0.8))
        # Treppe
        n = 10
        sx0, sy0 = x0 + W * 0.42, b - 0.25 * sc
        stw, sth = (W * 0.2) / n, (H - 0.45 * sc) / n
        pts_ = [(sx0, sy0)]
        for i in range(n):
            pts_ += [(sx0 - i * stw, sy0 - (i + 1) * sth), (sx0 - (i + 1) * stw, sy0 - (i + 1) * sth)]
        s.append(pline(pts_, sw=0.8))
        s.append(line((sx0, sy0), (sx0 - n * stw, sy0 - n * sth), sw=0.6))
        # Anbau rechts (Pultdach)
        ax = x0 + W
        s.append(pline([(ax, b - H * 0.75), (ax + 1.6 * sc, b - H * 0.55), (ax + 1.6 * sc, b), (ax, b)], sw=1.4))
        s.append(poly([(ax + 1.6 * sc - 6, b - H * 0.55), (ax + 1.6 * sc, b - H * 0.55), (ax + 1.6 * sc, b), (ax + 1.6 * sc - 6, b)],
                      fill="url(#sCut)", sw=0.8))
        # Tuer, Fenster
        s.append(poly([(ax + 0.4 * sc, b), (ax + 0.4 * sc, b - 2.0 * sc), (ax + 1.0 * sc, b - 2.0 * sc), (ax + 1.0 * sc, b)], sw=0.8))
        s.append(poly([(x0 + W * 0.6, b - 1.0 * sc), (x0 + W * 0.85, b - 1.0 * sc), (x0 + W * 0.85, b - 2.0 * sc),
                       (x0 + W * 0.6, b - 2.0 * sc)], sw=0.8))
        s.append(poly([(x0 + W * 0.48, b - H - 0.4 * sc), (x0 + W * 0.56, b - H - 0.4 * sc), (x0 + W * 0.56, b - H - 1.2 * sc),
                       (x0 + W * 0.48, b - H - 1.2 * sc)], sw=0.7))
        # Schornstein
        s.append(poly([(x0 + W * 0.66, b - H - R * 0.66), (x0 + W * 0.66, b - H - R - 0.4 * sc), (x0 + W * 0.72, b - H - R - 0.4 * sc),
                       (x0 + W * 0.72, b - H - R * 0.54)], fill=WHITE, sw=1.0))
        # Moebel angedeutet
        s.append(poly([(x0 + W * 0.65, b - 0.25 * sc), (x0 + W * 0.65, b - 0.7 * sc), (x0 + W * 0.85, b - 0.7 * sc),
                       (x0 + W * 0.85, b - 0.25 * sc)], sw=0.6))
        # Stufen aussen
        for k in range(3):
            s.append(pline([(x0 - 0.3 * sc * (k + 1), b - 0.25 * sc + k * 0.12 * sc),
                            (x0 - 0.3 * sc * k, b - 0.25 * sc + k * 0.12 * sc)], sw=0.8))
        s.append(f'<circle cx="{f(x0 - 1.2 * sc)}" cy="{f(b - H - 0.2 * sc)}" r="9" fill="{WHITE}" stroke="{DEEP}" stroke-width="0.8"/>')
        s.append(text(x0 - 1.2 * sc, b - H - 0.2 * sc + 3, "1", 8.5, "b", DEEP, "middle"))
        return "".join(s)
    # Laengsschnitt
    Lw, H, R = 11 * sc, 3.0 * sc, 1.7 * sc
    b = y0
    s.append(line((x0 - 30, b), (x0 + Lw + 30, b), sw=0.8))
    # Stufenpodest links
    for k in range(4):
        s.append(pline([(x0 - 10 - k * 9, b - 0.3 * sc + k * 0.1 * sc), (x0 - 1 - k * 9, b - 0.3 * sc + k * 0.1 * sc),
                        (x0 - 1 - k * 9, b - 0.2 * sc + k * 0.1 * sc)], sw=0.7))
    s.append(poly([(x0, b - 0.3 * sc), (x0 + Lw, b - 0.3 * sc), (x0 + Lw, b), (x0, b)], fill="url(#sCut)", sw=0.9))
    s.append(line((x0, b + 3), (x0 + Lw, b + 3), stroke=LIME, sw=2.6))
    # Dachlinie
    rp = [(x0 - 0.3 * sc, b - H), (x0 + Lw * 0.42, b - H - R), (x0 + Lw + 0.3 * sc, b - H)]
    s.append(pline(rp, sw=2.0))
    s.append(pline([(p[0], p[1] + 7) for p in rp], sw=0.7))
    # Waende
    for wx in (x0, x0 + Lw - 0.25 * sc):
        s.append(poly([(wx, b - 0.3 * sc), (wx + 0.25 * sc, b - 0.3 * sc), (wx + 0.25 * sc, b - H), (wx, b - H)],
                      fill="url(#sCut)", sw=0.9))
    # Treppe Mitte
    n = 9
    sx0, sy0 = x0 + Lw * 0.5, b - 0.3 * sc
    stw, sth = 0.22 * sc, (H - 0.4 * sc) / n
    st = [(sx0, sy0)]
    for i in range(n):
        st += [(sx0 + i * stw, sy0 - (i + 1) * sth), (sx0 + (i + 1) * stw, sy0 - (i + 1) * sth)]
    s.append(pline(st, sw=0.7))
    s.append(poly([(sx0 - 0.2 * sc, b - H + 0.1 * sc), (sx0 - 0.2 * sc, b - 0.3 * sc), (sx0 - 0.05 * sc, b - 0.3 * sc),
                   (sx0 - 0.05 * sc, b - H + 0.1 * sc)], fill="url(#hVert)", sw=0.6))
    # Fenster / Moebel
    s.append(poly([(x0 + Lw * 0.6, b - 1.0 * sc), (x0 + Lw * 0.75, b - 1.0 * sc), (x0 + Lw * 0.75, b - 2.2 * sc),
                   (x0 + Lw * 0.6, b - 2.2 * sc)], sw=0.8))
    s.append(line((x0 + Lw * 0.675, b - 1.0 * sc), (x0 + Lw * 0.675, b - 2.2 * sc), sw=0.5))
    s.append(poly([(x0 + Lw * 0.1, b - 0.3 * sc), (x0 + Lw * 0.1, b - 0.75 * sc), (x0 + Lw * 0.32, b - 0.75 * sc),
                   (x0 + Lw * 0.32, b - 0.3 * sc)], sw=0.6))
    s.append(poly([(x0 + Lw * 0.38, b - 0.3 * sc), (x0 + Lw * 0.38, b - 2.2 * sc), (x0 + Lw * 0.45, b - 2.2 * sc),
                   (x0 + Lw * 0.45, b - 0.3 * sc)], sw=0.6))
    s.append(poly([(x0 + Lw * 0.82, b - 0.3 * sc), (x0 + Lw * 0.82, b - 1.0 * sc), (x0 + Lw * 0.93, b - 1.0 * sc),
                   (x0 + Lw * 0.93, b - 0.3 * sc)], sw=0.6))
    # Achsen unten
    for k in range(7):
        xx = x0 + Lw * k / 6
        s.append(line((xx, b + 8), (xx, b + 22), sw=0.5, extra='stroke-dasharray="3 2"'))
        s.append(f'<circle cx="{f(xx)}" cy="{f(b + 30)}" r="6.5" fill="{WHITE}" stroke="{DEEP}" stroke-width="0.7"/>')
        s.append(text(xx, b + 32.5, str(k + 1), 7, "b", DEEP, "middle"))
    return "".join(s)


def lupe(cx, cy, r, anchor, content, cid):
    """Lupenkreis wie in den Schadensbildern: Lime-Ring, Fuehrungslinie, Fokuspunkt."""
    ax, ay = anchor
    ang = math.atan2(ay - cy, ax - cx)
    ex, ey = cx + r * math.cos(ang), cy + r * math.sin(ang)
    return (f'<clipPath id="{cid}"><circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}"/></clipPath>'
            + line((ax, ay), (ex, ey), sw=1.6)
            + f'<ellipse cx="{f(ax)}" cy="{f(ay)}" rx="34" ry="20" fill="none" stroke="{LIME}" stroke-width="2.4" stroke-dasharray="2.5 4" stroke-linecap="round"/>'
            + f'<circle cx="{f(ax)}" cy="{f(ay)}" r="6" fill="{LIME}" stroke="{DEEP}" stroke-width="1.4"/>'
            + f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{WHITE}"/>'
            + f'<g clip-path="url(#{cid})">{content}</g>'
            + f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="none" stroke="{LIME}" stroke-width="9"/>'
            + f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r + 4.5)}" fill="none" stroke="{DEEP}" stroke-width="1.4"/>')


def table(x, y, rows, widths, rh=16.5, head=None, size=8.5):
    s = []
    wsum = sum(widths)
    yy = y
    if head:
        s.append(text(x, yy, head[0], 9.5, "h", DEEP))
        if len(head) > 1:
            s.append(text(x + wsum, yy, head[1], 9.5, "b", DEEP, "end"))
        yy += 8
        s.append(line((x, yy), (x + wsum, yy), sw=1.4))
    for r in rows:
        cx = x
        for i, (c, w) in enumerate(zip(r, widths)):
            anchor = "end" if i == len(r) - 1 else "start"
            tx = cx + w - 2 if anchor == "end" else cx + 2
            s.append(text(tx, yy + rh - 5, c, size, "b" if i == 0 else "", DEEP if i == 0 else STONE, anchor))
            cx += w
        yy += rh
        s.append(line((x, yy), (x + wsum, yy), sw=0.5, extra='stroke-opacity="0.6"'))
    return "".join(s), yy


def plan_scene() -> tuple[str, int, int]:
    W, H = 2000, 1120
    s = [hatch_defs()]
    s.append(f'<rect width="{W}" height="{H}" fill="{SAND}"/>')

    # ---------- Spalte 1: Titel + Text ----------
    s.append(text(140, 106, "HAUS", 30, "h", DEEP))
    s.append(text(140, 140, "ARCHITEKTUR", 11, "h", DEEP, extra='letter-spacing="0.06em"'))
    s.append(para(140, 162, [
        "Eingeschossiger Holzrahmenbau",
        "mit ausgebautem Dachgeschoss,",
        "Satteldach 32° in Stehfalzdeckung.",
        "Boden-Deckel-Schalung, offene",
        "Veranda an der Giebelseite.",
    ], 9.5, 13))
    s.append(para(140, 238, [
        "Sockel und erdberührte Bauteile",
        "mit Abdichtung (Lime markiert).",
    ], 9.5, 13))
    s.append(para(350, 96, [
        "Tragwerk: Ständer 6/16, Rähm",
        "und Schwelle 8/16, Sparren 8/20,",
        "e = 1,25 m. Aussteifung über",
        "Streben in den Längswänden.",
        "",
        "Gebäude 8,00 × 10,00 m,",
        "davon 2,20 m Veranda.",
        "Traufe +3,00 · First +5,60",
    ], 9.5, 13))

    # ---------- Tragwerk (Drahtmodell) mit Beschriftungen ----------
    iso_f = Iso(355, 350, 15)
    s.append(frame(iso_f, sw=0.8))
    for (p3, lbl, side) in (((0, 0, 3.0), "RÄHM 8/16", "l"), ((0, 2.5, 1.5), "STÄNDER 6/16", "l"),
                            ((0, 5.0, 0), "SCHWELLE 8/16", "l"), ((8, 0, 3.0), "SPARREN 8/20", "r"),
                            ((8, 5, 1.5), "STREBE 6/12", "r"), ((4, -0.45, 5.6), "FIRSTPFETTE", "r")):
        a = iso_f(*p3)
        if side == "l":
            s.append(leader(a, (215, a[1] - 10), None))
            s.append(text(140, a[1] - 7, lbl, 8.5, "b", DEEP))
        else:
            s.append(leader(a, (500, a[1] - 6), lbl, 8.5))
    s.append(text(140, 540, "TRAGWERK", 12, "h", DEEP))
    s.append(line((140, 550), (330, 550), sw=0.8))
    s.append(text(140, 565, "Isometrie, ohne Bekleidung · M 1:200", 8.5, fill=STONE))

    # ---------- kleine Iso oben Mitte mit Massketten ----------
    iso_s = Iso(690, 92, 8.5)
    s.append(house(iso_s, deck=False, clad=True, seams=True, detail=0.75, shadow=False, sock_lime=True))
    for (p3, lbl, ly) in (((4, 10, 4.5), "GIEBEL", 160), ((6.4, 3, 4.3), "STEHFALZ", 182),
                          ((8, 1.7, 1.6), "FENSTER", 204), ((8, 5, 0.1), "SOCKEL", 232)):
        a = iso_s(*p3)
        s.append(leader(a, (575, ly), lbl, 8, anchor="end"))
    for (p3, lbl) in (((4, -0.45, 5.6), "FIRST +5,60"), ((8.45, -0.45, 2.75), "TRAUFE +3,00"), ((8, 7.8, 0), "± 0,00")):
        a = iso_s(*p3)
        s.append(leader(a, (790, a[1] - 4), lbl, 8))
    s.append(text(575, 330, "AXONOMETRIE NORD-OST · M 1:250", 8.5, "b", DEEP))

    # ---------- Tabelle oben ----------
    rows = [("01", "Stehfalzdeckung Alu 0,7", "0,7"), ("02", "Lattung / Konterlattung", "30"),
            ("03", "Unterdeckbahn diffusionsoffen", "—"), ("04", "Holzfaserplatte", "60"),
            ("05", "Sparren / Zellulose", "200"), ("06", "Dampfbremse", "—"), ("07", "Installationsebene", "40"),
            ("08", "Gipsfaserplatte", "15"), ("09", "Schalung Lärche 24/146", "24"), ("10", "Sockelabdichtung", "—"),
            ]
    rows = rows[:9] + [("", "Gesamt Dach", "≈ 370")]
    tb, ty_end = table(870, 96, rows, [22, 122, 30], head=("DACHAUFBAU", "mm"))
    s.append(tb)

    # ---------- Querschnitt (Mitte) ----------
    s.append(text(575, 395, "QUERSCHNITT A–A", 12, "h", DEEP))
    s.append(text(575, 412, "Schnitt durch Treppe und Anbau", 8.5))
    s.append(para(575, 432, ["Dachaufbau gemäß Tabelle, Bodenplatte", "auf Perimeterdämmung, Abdichtung", "erdberührter Bauteile umlaufend."], 8.5, 12))
    s.append(f'<g>{section(650, 635, 22, "giebel")}</g>')
    s.append(dim_h(650, 650 + 6.2 * 22, 668, "6,20"))
    # Legende links neben Schnitt

    # ---------- Laengsschnitte (links unten) ----------
    s.append(f'<g>{section(170, 712, 30, "laengs")}</g>')
    s.append(text(140, 772, "LÄNGSSCHNITT B–B", 12, "h", DEEP))
    s.append(line((140, 782), (520, 782), sw=0.8))
    s.append(f'<g>{section(170, 1005, 30, "laengs")}</g>')
    s.append(text(140, 1065, "ANSICHT SÜD", 12, "h", DEEP))
    s.append(line((140, 1075), (520, 1075), sw=0.8))

    # ---------- Grundriss (Mitte unten) ----------
    s.append(f'<g>{floor_plan(660, 760, 27)}</g>')
    s.append(text(600, 1060, "GRUNDRISS ERDGESCHOSS", 12, "h", DEEP, extra='transform="rotate(-90 600 1060)"'))
    s.append(para(925, 920, ["Wohnfläche EG  58,4 m²", "Veranda  17,6 m²", "Treppe  2,1 m²", "Bad  6,8 m²",
                             "Essen  14,2 m²", "Wohnen  27,5 m²", "", "Raumhöhe  2,60 m", "Brüstung  0,90 m",
                             "Sturz  2,20 m"], 7.5, 11))

    # ---------- Hauptansicht (rechts oben) ----------
    iso_h = Iso(1305, 170, 29)
    s.append(house(iso_h, detail=1.15))
    # Lupe Stehfalz
    pt = iso_h(6.4, 6.6, 4.27)
    lz = []
    for i in range(-4, 10):
        x = 1650 + i * 22
        lz.append(poly([(x, 120), (x + 14, 120), (x + 14 - 90, 300), (x - 90, 300)], fill=WHITE, sw=0, stroke="none"))
        lz.append(line((x + 14, 120), (x + 14 - 90, 300), sw=2.0))
        lz.append(line((x + 17, 120), (x + 17 - 90, 300), sw=0.8, extra='stroke-opacity="0.6"'))
    lz.append(poly([(1560, 120), (1820, 120), (1820, 300), (1560, 300)], fill=DEEP, stroke="none", sw=0, extra='fill-opacity="0.04"'))
    s.append(lupe(1700, 200, 72, pt, "".join(lz), "cLupe"))
    s.append(text(1700, 296, "Stehfalz, Falzhöhe 25 mm", 8.5, "b", DEEP, "middle"))

    # ---------- kleine Iso rechts ----------
    iso_t = Iso(1735, 360, 6.0)
    s.append(house(iso_t, detail=0.6, sock_lime=False))
    s.append(text(1655, 440, "KLEINANSICHT · M 1:500", 8, "b", DEEP))

    # ---------- Textspalte rechts ----------
    s.append(text(1830, 90, "STEHFALZDACH", 12, "h", DEEP))
    s.append(para(1830, 110, ["Doppelstehfalz, Scharenbreite", "500 mm, auf Vollschalung mit", "Trennlage. Firstentlüftung", "durchgehend, Traufe mit", "Insektenschutzgitter.", "", "Anschluss Kamin mit", "Kehlblech und Kappleiste."], 8.5, 12.5))

    # ---------- Tragwerk mit Teilbekleidung (rechts unten) ----------
    iso_e = Iso(1340, 598, 28)
    # Achsraster gestrichelt
    for gx in (-1, 3, 7, 11):
        s.append(line(iso_e(gx, -2, 0), iso_e(gx, 12, 0), sw=0.6, extra='stroke-dasharray="5 5" stroke-opacity="0.55"'))
        s.append(line(iso_e(gx, 12, 0), iso_e(gx, 12, 7.5), sw=0.6, extra='stroke-dasharray="5 5" stroke-opacity="0.35"'))
    for gy in (-1, 3, 7, 11):
        s.append(line(iso_e(-2, gy, 0), iso_e(10, gy, 0), sw=0.6, extra='stroke-dasharray="5 5" stroke-opacity="0.55"'))
        s.append(line(iso_e(10, gy, 0), iso_e(10, gy, 7.5), sw=0.6, extra='stroke-dasharray="5 5" stroke-opacity="0.35"'))
    s.append(frame(iso_e, sw=1.3, clad_part=True, lime=True))
    s.append(lupe(1110, 1005, 66, iso_e(8, 10, 0.05),
                  poly([(1030, 1020), (1190, 1020), (1190, 1080), (1030, 1080)], fill="url(#pConc)", sw=0, stroke="none")
                  + poly([(1030, 930), (1190, 930), (1190, 1004), (1030, 1004)], fill="url(#sCut)", sw=0, stroke="none")
                  + poly([(1030, 1004), (1190, 1004), (1190, 1020), (1030, 1020)], fill=LIME, stroke=DEEP, sw=1.4)
                  + line((1030, 955), (1190, 955), sw=1.2) + line((1030, 1004), (1190, 1004), sw=2.2),
                  "cLupe2"))
    s.append(text(1110, 1094, "Schwelle auf Sockelabdichtung", 8.5, "b", DEEP, "middle"))

    # ---------- Rechte Spalte: Ansicht + Positionsliste + Schriftfeld ----------
    s.append(text(1665, 575, "SEITENANSICHT", 12, "h", DEEP))
    items = [("Schwelle", "1"), ("Ständer", "1"), ("Rähm", "1"), ("", ""),
             ("Sparren 8/20", "9"), ("Firstpfette", "1"), ("Mittelpfette", "2"),
             ("1. Fußpfette", "2"), ("2. Streben 6/12", "6"), ("3. Riegel", "8"),
             ("4. Schalung Lärche", "18"), ("5. Stehfalzbahnen", "24"), ("6. Kappleiste", "2"),
             ("7. Kehlblech Kamin", "1"), ("8. Sockelabdichtung", "1"), ("9. Fensterbank", "3"),
             ("10. Insektenschutz", "2"), ("11. Firstentlüftung", "1")]
    yy = 600
    for (a, b) in items:
        if a:
            s.append(text(1670, yy, a, 8, fill=STONE))
            s.append(text(1860, yy, b, 8, "b", DEEP, "end"))
        yy += 13

    # Schriftfeld
    x0, y0 = 1665, 872
    s.append(text(x0, y0, "GRUNDRISS", 10, "h", DEEP))
    s.append(text(1860, y0, "HOLZHAUS", 10, "h", DEEP, "end"))
    s.append(para(x0 + 75, y0 + 16, ["Eingeschossig", "mit Galerie"], 7.5, 10))
    s.append(line((x0, y0 + 40), (1860, y0 + 40), sw=1.2))
    s.append(para(x0, y0 + 56, ["Bauherr", "Objekt"], 7.5, 11))
    s.append(para(x0 + 80, y0 + 56, ["—", "Holzhaus Typ H8"], 7.5, 11))
    s.append(text(x0, y0 + 92, "M 1:100", 9, "b", DEEP))
    s.append(text(1860, y0 + 92, "A3", 9, "b", DEEP, "end"))
    s.append(line((x0, y0 + 102), (1860, y0 + 102), sw=0.8))
    cols = [x0, x0 + 50, x0 + 100, x0 + 150, 1860]
    for k in range(2):
        yb = y0 + 102 + k * 52
        for cx in cols[1:-1]:
            s.append(line((cx, yb), (cx, yb + 52), sw=0.5))
        s.append(line((x0, yb + 52), (1860, yb + 52), sw=0.8))
        labels = (("Plan", "Index", "Datum", "Gez."), ("Phase", "Blatt", "Format", "Gepr."))[k]
        vals = (("A-101", "a", "11/2026", "BKM"), ("LP 3", "01", "A3", "—"))[k]
        for i, (lab, val) in enumerate(zip(labels, vals)):
            s.append(text(cols[i] + 4, yb + 16, lab, 7, fill=MUTED))
            s.append(text(cols[i] + 4, yb + 34, val, 8.5, "b", DEEP))
    return "\n".join(s), W, H


# ===========================================================================
# Ausgabe
# ===========================================================================

SZENEN = {
    "tor": ("Einfahrt mit Doppelflügeltor", "Torpfeiler, Lamellenzaun und Pforte · Strichzeichnung", tor_scene),
    "planblatt": ("Planblatt Holzhaus", "Isometrie, Tragwerk, Schnitte und Grundriss · Abdichtung in Lime", plan_scene),
}


def main(argv: list[str]) -> int:
    namen = argv or list(SZENEN)
    OUT.mkdir(exist_ok=True)
    for name in namen:
        if name not in SZENEN:
            print(f"Unbekannte Grafik: {name} (bekannt: {', '.join(SZENEN)})")
            return 2
        titel, sub, fn = SZENEN[name]
        svg, w, h = fn()
        ziel = OUT / f"{name}.html"
        ziel.write_text(page(titel, sub, svg, w, h), encoding="utf-8")
        print(f"geschrieben: {ziel.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
