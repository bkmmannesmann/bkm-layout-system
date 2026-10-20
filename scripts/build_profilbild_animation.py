#!/usr/bin/env python3
"""Animiertes Profilbild: ein Tropfen fällt und zerfließt zum BKM-Logo.

Hintergrund Lime Green, Tropfen und Logo vollflächig Deep Green (Farbwerte aus
brand.json). Das Logo kommt aus assets/logos/ und wird nicht nachgezeichnet;
die Morphose rechnet auf vorzeichenbehafteten Distanzfeldern (SDF), dadurch
wirkt der Übergang wie Flüssigkeit statt wie eine Überblendung.

Ablauf einer Schleife (25 fps):
  Logo steht -> zerfließt zum Tropfen -> Tropfen fällt aus dem Bild ->
  neuer Tropfen fällt von oben -> Aufprall mit Welle -> zerfließt zum Logo.
Das erste Bild zeigt das fertige Logo, damit Plattformen, die nur das erste
Bild eines GIFs anzeigen, trotzdem das Logo zeigen.

    python3 scripts/build_profilbild_animation.py
    python3 scripts/build_profilbild_animation.py --groesse 640 --ausgabe ordner/

Benötigt pymupdf, numpy, pillow, scipy und ffmpeg (nur für MP4).
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets/logos/bkm-logo-deepgreen-puregreen.svg"
FPS = 25
SS = 2  # Überabtastung für saubere Kanten

# Dauer der Abschnitte in Bildern
HALTEN, SCHMELZEN, FALLEN_RAUS, FALLEN_REIN, AUFPRALL, FORMEN = 50, 18, 10, 14, 5, 26


def farben() -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    c = json.loads((ROOT / "brand.json").read_text())["colors"]
    hex_ = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    return hex_(c["lime-green"]["hex"]), hex_(c["deep-green"]["hex"]), c["deep-green"]["hex"]


def ease_in(t): return t * t
def ease_out(t): return 1 - (1 - t) ** 3
def ease_io(t): return 3 * t * t - 2 * t * t * t


def sdf(maske: np.ndarray) -> np.ndarray:
    """Vorzeichenbehaftete Distanz: innen negativ, außen positiv (Pixel)."""
    return distance_transform_edt(~maske) - distance_transform_edt(maske)


def logo_maske(n: int, breite: float, deep_hex: str) -> np.ndarray:
    """Logo vollständig in Deep Green, mittig auf n x n, als Deckung 0..1."""
    svg = LOGO.read_text().replace("#4daf46", deep_hex)
    doc = pymupdf.open(stream=svg.encode(), filetype="svg")
    seite = doc[0]
    zoom = breite / seite.rect.width
    pix = seite.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
    a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 4)[..., 3]
    m = np.zeros((n, n), np.float32)
    y0, x0 = (n - pix.height) // 2, (n - pix.width) // 2
    m[y0:y0 + pix.height, x0:x0 + pix.width] = a / 255
    return m


def tropfen_poly(cx, cy, r, sx=1.0, sy=1.0, k=64):
    """Tropfenform: Kreis unten, Spitze oben. (cx, cy) = Kreismittelpunkt."""
    pts = []
    for i in range(k):
        t = 2 * math.pi * i / k
        x = math.sin(t) * math.sin(t / 2) ** 1.0
        y = -math.cos(t)  # t=0 -> Spitze oben
        pts.append((cx + x * r * 1.05 * sx, cy + (y * 1.45 * r - 0.25 * r) * sy))
    return pts


def form_maske(n, zeichnen) -> np.ndarray:
    img = Image.new("L", (n, n), 0)
    zeichnen(ImageDraw.Draw(img))
    return np.asarray(img) > 127


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--groesse", type=int, default=800, help="Kantenlänge in px")
    ap.add_argument("--ausgabe", type=Path, default=ROOT / "assets/animation/profilbild")
    args = ap.parse_args()

    lime, deep, deep_hex = farben()
    N = args.groesse
    n = N * SS
    lime_a, deep_a = np.array(lime, np.float32), np.array(deep, np.float32)

    # Logo: 74 % der Breite, passt mit Rand in den runden Profilausschnitt.
    logo = logo_maske(n, 0.74 * n, deep_hex)
    L = sdf(logo > 0.5)

    r = 0.085 * n  # Tropfenradius
    mitte = n / 2
    boden = mitte + 0.08 * n  # Unterkante des Tropfens beim Aufprall

    def tropfen(cy, sx=1.0, sy=1.0):
        return form_maske(n, lambda d: d.polygon(tropfen_poly(mitte, cy, r, sx, sy), fill=255))

    # Gestauchter Tropfen nach dem Aufprall: flache Kuppe auf dem Boden
    pw, ph = 2.0 * r, 0.42 * r
    py = boden - ph
    E = sdf(form_maske(n, lambda d: d.ellipse(
        (mitte - pw, py - ph, mitte + pw, py + ph), fill=255)))
    D = sdf(tropfen(mitte))

    def aus_sdf(s):
        return np.clip(0.5 - s, 0, 1)

    def morph(a, b, e, quell=0.06 * n):
        # Lineare SDF-Mischung plus Anschwellen in der Mitte hält die Form
        # zusammenhängend wie ein Tropfen Flüssigkeit.
        return aus_sdf((1 - e) * a + e * b - quell * math.sin(math.pi * e))

    bilder: list[np.ndarray] = []

    def bild(deckung, extra=None):
        d = deckung if extra is None else np.maximum(deckung, extra)
        bilder.append(d)

    # 1. Logo steht
    for _ in range(HALTEN):
        bild(logo)
    # 2. Logo zerfließt zum Tropfen in der Mitte
    for i in range(1, SCHMELZEN + 1):
        bild(morph(L, D, ease_io(i / SCHMELZEN)))
    # 3. Tropfen fällt unten aus dem Bild
    for i in range(1, FALLEN_RAUS + 1):
        t = ease_in(i / FALLEN_RAUS)
        cy = mitte + t * (0.7 * n)
        bild(tropfen(cy, 1 - 0.12 * t, 1 + 0.25 * t).astype(np.float32))
    # 4. Neuer Tropfen fällt von oben bis zum Aufprall
    start = -0.25 * n
    ziel = boden - 1.2 * r
    for i in range(FALLEN_REIN):
        t = ease_in(i / (FALLEN_REIN - 1))
        cy = start + t * (ziel - start)
        bild(tropfen(cy, 1 - 0.15 * t, 1 + 0.3 * t).astype(np.float32))
    # 5. Aufprall: der Tropfen staucht sich zur flachen Kuppe
    T = sdf(tropfen(ziel))
    for i in range(1, AUFPRALL + 1):
        bild(morph(T, E, ease_out(i / AUFPRALL), quell=0))
    # 6. Kuppe breitet sich aus und formt das Logo; eine Welle läuft nach außen
    for i in range(1, FORMEN + 1):
        t = i / FORMEN
        e = ease_out(t)
        d = morph(E, L, e)
        # Welle: Ellipsenring, wird größer und blasser
        w = ease_out(min(1, t * 1.6))
        rx, ry = pw * (1.2 + 3.2 * w), ph * (1.4 + 3.2 * w)
        yy, xx = np.ogrid[:n, :n]
        rho = np.sqrt(((xx - mitte) / rx) ** 2 + ((yy - py) / ry) ** 2)
        dicke = 0.006 * n * (1 - w)
        ring = np.clip(1 - np.abs(rho - 1) * min(rx, ry) / max(dicke, 1e-3), 0, 1)
        bild(d, ring * (1 - w) * 0.55)
    # Das letzte Morphbild ist nahe am Logo, das Halten oben schließt die Schleife.

    args.ausgabe.mkdir(parents=True, exist_ok=True)
    frames = []
    for d in bilder:
        rgb = lime_a + (deep_a - lime_a) * d[..., None]
        img = Image.fromarray(rgb.astype(np.uint8)).resize((N, N), Image.LANCZOS)
        frames.append(img)

    frames[0].save(args.ausgabe / "bkm-profilbild-standbild.png")
    # GIF: gemeinsame Palette aus Lime/Deep-Mischtönen, keine Rasterung (Dither)
    pal = frames[HALTEN + SCHMELZEN // 2].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    gif = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    gif[0].save(args.ausgabe / "bkm-profilbild.gif", save_all=True, append_images=gif[1:],
                duration=1000 // FPS, loop=0, optimize=True, disposal=1)

    if shutil.which("ffmpeg"):
        tmp = args.ausgabe / "_frames"
        tmp.mkdir(exist_ok=True)
        for i, f in enumerate(frames):
            f.save(tmp / f"{i:04d}.png")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS),
                        "-i", str(tmp / "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "16", "-movflags", "+faststart",
                        str(args.ausgabe / "bkm-profilbild.mp4")], check=True)
        shutil.rmtree(tmp)
    print(f"{len(frames)} Bilder, {len(frames) / FPS:.1f} s -> {args.ausgabe}")


if __name__ == "__main__":
    main()
