#!/usr/bin/env python3
"""KI-Kennzeichnung: rendern, im Motiv suchen, aufbringen.

Nach EU-KI-Verordnung trägt jedes KI-generierte Motiv den Vermerk „AI GENERATED“
im Bild selbst. Dieses Modul findet einen vorhandenen Vermerk und setzt ihn,
wo er fehlt. Die Maße stehen in brand.json unter ai_generated_images.marke.

Der Suchweg ist eine normierte Kreuzkorrelation (NCC) der Bildhelligkeit gegen
die Deckungsmaske des Logos, über mehrere Maßstäbe und die vier Bildecken.
NCC ist unempfindlich gegen Helligkeit und Kontrast des Grundes — deshalb findet
sie den weissen Vermerk sowohl auf dunklem Keller- als auch auf heller Wandfläche.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

WURZEL = Path(__file__).resolve().parent.parent
SVG = WURZEL / "assets" / "kennzeichnung" / "bkm-ai-generated.svg"

# Seitenverhaeltnis des Logos aus der viewBox: 195,131 : 47,307
SEITENVERHAELTNIS = 195.131 / 47.307

# Mindeststreuung eines Suchfensters in Graustufen. Darunter ist die Fläche zu
# gleichförmig, um den Vermerk zu enthalten — und die NCC dort nicht belastbar.
# Die Zeile „AI GENERATED“ nimmt diesen Anteil der Logohöhe ein, ihre Versalien
# wiederum diesen Anteil der Zeile. Aus beidem folgt, wie klein die Kennzeichnung
# bei einer gegebenen Logobreite wird — die eigentliche Lesbarkeitsfrage.
ZEILE_ANTEIL = 11.336 / 47.307
VERSAL_ANTEIL = 0.98

MIN_STREUUNG = 6.0

# Unter dieser Musterbreite ist die Zeile „AI GENERATED“ nicht mehr lesbar — ein
# so kleiner Fund wäre ohnehin keine gültige Kennzeichnung. Zugleich korrelieren
# winzige Muster leicht zufällig mit beliebiger Bildstruktur; die Grenze hält
# diese Scheinfunde aus der Suche heraus.
MIN_MUSTER_PX = 40

# Trennwert. Echte Vermerke messen 0,94 aufwärts, strukturähnliche Bildstellen
# bleiben unter 0,58 (gemessen an 15 Motiven des Repos, 6 davon gekennzeichnet).
SCHWELLE = 0.75

# Arbeitsbreite der Suche. Der Vermerk ist relativ zur Bildbreite bemessen, seine
# Erkennbarkeit haengt also nicht an der Aufloesung des Motivs. Ein Druckbild mit
# 2480 px wird fuer die Korrelation heruntergerechnet und der Fund zurueckgerechnet;
# das kostet nichts an Trennschaerfe und spart den Grossteil der Rechenzeit.
ARBEITSBREITE = 1400


def regeln() -> dict:
    """Maße aus brand.json. Fallback, damit das Modul auch einzeln läuft."""
    vorgabe = {
        "breite_anteil": 0.083,
        "rand_anteil": 0.028,
        "mindestbreite_px": 90,
        "mindestbreite_mm": 15.0,
        "farbe": "#ffffff",
        "ecken": ["unten_rechts", "unten_links"],
        "ecken_zulaessig": ["unten_rechts", "unten_links", "oben_rechts", "oben_links"],
    }
    try:
        marke = json.loads((WURZEL / "brand.json").read_text(encoding="utf-8"))
        marke = marke.get("ai_generated_images", {}).get("marke", {})
        for k in vorgabe:
            if k in marke:
                vorgabe[k] = marke[k]
    except Exception:
        pass
    return vorgabe


def logo_raster(breite_px: int, farbe: str = "#ffffff") -> Image.Image:
    """Das Logo in der gewünschten Pixelbreite, als RGBA mit weichen Kanten."""
    if breite_px < 8:
        raise ValueError("Logobreite unter 8 px ergibt keine lesbare Kennzeichnung")
    quelle = SVG.read_text(encoding="utf-8")
    if farbe.lower() not in ("#ffffff", "#fff"):
        quelle = quelle.replace('fill="#ffffff"', 'fill="%s"' % farbe)
    dok = pymupdf.open(stream=quelle.encode("utf-8"), filetype="svg")
    faktor = breite_px / dok[0].rect.width
    pix = dok[0].get_pixmap(matrix=pymupdf.Matrix(faktor, faktor), alpha=True)
    bild = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    dok.close()
    return bild


def _ncc(feld: np.ndarray, muster: np.ndarray) -> np.ndarray:
    """Normierte Kreuzkorrelation von muster über feld, gültige Lagen.

    Zähler über FFT, lokale Summen und Quadratsummen über Integralbilder.
    Ergebnis in [-1, 1], Form (feld.h - muster.h + 1, feld.w - muster.w + 1).
    """
    fh, fw = feld.shape
    mh, mw = muster.shape
    if fh < mh or fw < mw:
        return np.zeros((0, 0))

    m_zentriert = muster - muster.mean()
    m_norm = math.sqrt(float((m_zentriert ** 2).sum()))
    if m_norm < 1e-9:
        return np.zeros((fh - mh + 1, fw - mw + 1))

    # Zaehler: Korrelation feld * zentriertes Muster
    gh, gw = fh + mh - 1, fw + mw - 1
    gh, gw = 1 << (gh - 1).bit_length(), 1 << (gw - 1).bit_length()
    F = np.fft.rfft2(feld, s=(gh, gw))
    M = np.fft.rfft2(m_zentriert[::-1, ::-1], s=(gh, gw))
    voll = np.fft.irfft2(F * M, s=(gh, gw))
    zaehler = voll[mh - 1: mh - 1 + fh - mh + 1, mw - 1: mw - 1 + fw - mw + 1]

    # Nenner: lokale Standardabweichung des Feldes
    ii = np.zeros((fh + 1, fw + 1), dtype=np.float64)
    ii2 = np.zeros((fh + 1, fw + 1), dtype=np.float64)
    ii[1:, 1:] = feld.cumsum(0).cumsum(1)
    ii2[1:, 1:] = (feld.astype(np.float64) ** 2).cumsum(0).cumsum(1)

    def fenster(tab):
        return (tab[mh:, mw:] - tab[:-mh, mw:] - tab[mh:, :-mw] + tab[:-mh, :-mw])

    n = mh * mw
    summe = fenster(ii)
    summe2 = fenster(ii2)
    varianz = np.maximum(summe2 - summe ** 2 / n, 0.0)
    nenner = np.sqrt(varianz) * m_norm

    # Auf einer nahezu gleichförmigen Fläche geht der Nenner gegen null und der
    # Quotient explodiert zu einer Scheingüte von 1,0. Eine solche Fläche kann den
    # Vermerk aber gar nicht tragen: weisse Glyphen auf beliebigem Grund erzeugen
    # zwangsläufig Streuung. Deshalb wird nach der lokalen Standardabweichung
    # gefiltert, nicht nach einem absoluten Epsilon.
    std_lokal = np.sqrt(varianz / n)
    ergebnis = np.zeros_like(zaehler)
    gut = std_lokal >= MIN_STREUUNG
    ergebnis[gut] = zaehler[gut] / nenner[gut]
    return np.clip(ergebnis, -1.0, 1.0)


ECKEN = ("unten_rechts", "unten_links", "oben_rechts", "oben_links")


def _suchfenster(w: int, h: int, ecke: str, anteil_x=0.48, anteil_y=0.34):
    bw, bh = max(1, int(w * anteil_x)), max(1, int(h * anteil_y))
    x0 = w - bw if "rechts" in ecke else 0
    y0 = h - bh if "unten" in ecke else 0
    return x0, y0, bw, bh


_MUSTER: dict[int, np.ndarray] = {}


def _muster(breite_px: int) -> np.ndarray:
    """Deckungsmaske des Logos in Pixelbreite, gemerkt — die Skalensuche
    fragt dieselben Breiten für jede Ecke erneut ab."""
    if breite_px not in _MUSTER:
        _MUSTER[breite_px] = np.asarray(
            logo_raster(breite_px).split()[3], dtype=np.float32) / 255.0
    return _MUSTER[breite_px]


def _durchlauf(grau, w, h, ecken, breiten, bestes):
    for ecke in ecken:
        x0, y0, bw, bh = _suchfenster(w, h, ecke)
        feld = grau[y0:y0 + bh, x0:x0 + bw]
        for tb in breiten:
            th = int(round(tb / SEITENVERHAELTNIS))
            if tb < MIN_MUSTER_PX or tb > bw or th > bh:
                continue
            muster = _muster(tb)
            karte = _ncc(feld, muster)
            if karte.size == 0:
                continue
            i = int(np.argmax(karte))
            gy, gx = divmod(i, karte.shape[1])
            guete = float(karte[gy, gx])
            if guete > bestes["guete"]:
                bestes.update(guete=guete, ecke=ecke, breite_anteil=tb / w,
                              kasten=(x0 + gx, y0 + gy, muster.shape[1], muster.shape[0]))
    return bestes


def finde(pfad, schwelle: float = SCHWELLE, breiten_anteile=None, fein: bool = True) -> dict:
    """Sucht die Kennzeichnung in allen vier Ecken über mehrere Maßstäbe.

    Liefert das beste Ergebnis: {gefunden, guete, ecke, kasten, breite_anteil, …}.
    kasten ist (x, y, breite, hoehe) in Pixeln des Originalbildes.

    Erst ein grobes Skalenraster über alle vier Ecken, dann — wenn fein — ein
    enges Raster um die Siegerskala in der Siegerecke. Ohne diesen zweiten
    Durchgang ist die gemessene Größe nur so genau wie das grobe Raster, und
    daraus lässt sich keine Maßregel ableiten.
    """
    bild = Image.open(pfad).convert("L")
    w0, h0 = bild.size
    faktor = 1.0
    if w0 > ARBEITSBREITE:
        faktor = ARBEITSBREITE / w0
        bild = bild.resize((ARBEITSBREITE, max(1, round(h0 * faktor))), Image.LANCZOS)
    w, h = bild.size
    grau = np.asarray(bild, dtype=np.float32)

    if breiten_anteile is None:
        # 5 % bis 45 % der Bildbreite. Die Obergrenze ist nicht willkuerlich: wird
        # die Marke nach dem Druckmindestmass von 20 mm gesetzt, misst sie auf einem
        # 85 mm breiten Motiv 24 % und auf einem 55 mm breiten 36 % der Bildbreite.
        # Der Bereich endete zuerst bei 21 % - der Sucher fand damit genau die
        # Marken nicht, die das Repository selbst druckgerecht aufbringt.
        breiten_anteile = [0.05 * (1.1226 ** i) for i in range(20)]

    bestes = {"gefunden": False, "guete": -1.0, "ecke": None, "kasten": None,
              "breite_anteil": None, "datei": str(pfad), "bild": (w0, h0)}

    grob = sorted({int(round(w * a)) for a in breiten_anteile})
    bestes = _durchlauf(grau, w, h, ECKEN, grob, bestes)

    if fein and bestes["ecke"]:
        mitte = bestes["kasten"][2]
        spanne = sorted({max(MIN_MUSTER_PX, mitte + d) for d in range(-14, 15)})
        bestes = _durchlauf(grau, w, h, [bestes["ecke"]], spanne, bestes)

    if bestes["kasten"] and faktor != 1.0:
        bestes["kasten"] = tuple(int(round(v / faktor)) for v in bestes["kasten"])
    bestes["gefunden"] = bestes["guete"] >= schwelle
    return bestes


def raender(treffer: dict) -> tuple[float, float]:
    """Abstand des Treffers zur nächsten waagerechten und senkrechten Bildkante,
    als Anteil der Bildbreite."""
    if not treffer.get("kasten"):
        return (float("nan"), float("nan"))
    w, h = treffer["bild"]
    x, y, tb, th = treffer["kasten"]
    dx = min(x, w - (x + tb)) / w
    dy = min(y, h - (y + th)) / w
    return dx, dy


def _dunkelheit(grau: np.ndarray) -> float:
    """Wie gut trägt eine Fläche einen weissen Vermerk? 0 = gar nicht, 1 = ideal.

    Bewertet wird der Abstand der Fläche zu Weiss, gedämpft durch ihre Unruhe:
    eine ruhige dunkle Fläche schlägt eine ebenso dunkle, aber stark strukturierte.
    """
    mittel = float(grau.mean()) / 255.0
    unruhe = float(grau.std()) / 255.0
    return max(0.0, (1.0 - mittel)) * (1.0 - min(unruhe * 1.4, 0.6))


def marke_breite(bildbreite_px: int, regel: dict, druckbreite_mm: float | None = None) -> int:
    """Die Pixelbreite, in der die Marke ins Motiv gebrannt wird.

    Ohne druckbreite_mm gilt der Anteil an der Bildbreite, nach unten begrenzt
    durch das Mindestmaß in Pixeln. Das ist die Bildschirmrechnung.

    Mit druckbreite_mm kommt die Rechnung für den Druck dazu: die Marke wird
    mitskaliert, wenn das Motiv ins Layout gesetzt wird, und ihre gedruckte
    Größe hängt deshalb nicht an der Auflösung des Motivs, sondern allein an
    der Breite, in der es steht. Ein Skript, das das Motiv stempelt, ohne diese
    Breite zu kennen, kann das Mindestmaß in Millimetern nicht einhalten — es
    weiß nicht, wie gross das Bild am Ende wird.
    """
    breite = max(int(regel["mindestbreite_px"]), int(round(bildbreite_px * regel["breite_anteil"])))
    if druckbreite_mm:
        px_je_mm = bildbreite_px / float(druckbreite_mm)
        breite = max(breite, int(round(float(regel["mindestbreite_mm"]) * px_je_mm)))
    return min(breite, bildbreite_px)


def beste_ecke(pfad, regel: dict | None = None, druckbreite_mm: float | None = None) -> list[dict]:
    """Bewertet die zugelassenen Ecken nach Kontrast — dunkelste zuerst."""
    regel = regel or regeln()
    bild = Image.open(pfad).convert("L")
    w, h = bild.size
    grau = np.asarray(bild, dtype=np.float32)
    tb = marke_breite(w, regel, druckbreite_mm)
    th = int(round(tb / SEITENVERHAELTNIS))
    rand = int(round(w * regel["rand_anteil"]))
    luft = int(round(th * 0.45))  # etwas Umfeld mitbewerten

    ergebnis = []
    for ecke in regel["ecken"]:
        x = w - rand - tb if "rechts" in ecke else rand
        y = h - rand - th if "unten" in ecke else rand
        aus = grau[max(0, y - luft):y + th + luft, max(0, x - luft):x + tb + luft]
        ergebnis.append({"ecke": ecke, "eignung": _dunkelheit(aus),
                         "kasten": (x, y, tb, th),
                         "mittel": float(aus.mean()), "unruhe": float(aus.std())})
    ergebnis.sort(key=lambda e: -e["eignung"])
    return ergebnis


def stemple(pfad_ein, pfad_aus, ecke: str | None = None, regel: dict | None = None,
            druckbreite_mm: float | None = None) -> dict:
    """Setzt den Vermerk in die angegebene (oder kontraststärkste) Ecke.

    druckbreite_mm ist die Breite, in der das Motiv im Layout stehen wird. Nur
    mit ihr lässt sich das Mindestmaß für den Druck einhalten.
    """
    regel = regel or regeln()
    rang = beste_ecke(pfad_ein, regel, druckbreite_mm)
    gewaehlt = next((e for e in rang if e["ecke"] == ecke), rang[0])

    quelle = Image.open(pfad_ein)
    modus = quelle.mode
    bild = quelle.convert("RGBA")
    x, y, tb, th = gewaehlt["kasten"]
    bild.alpha_composite(logo_raster(tb, regel["farbe"]), (x, y))

    ziel = Path(pfad_aus)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if ziel.suffix.lower() in (".jpg", ".jpeg") or modus == "RGB":
        bild.convert("RGB").save(ziel, quality=95)
    else:
        bild.save(ziel)
    ergebnis = {"ecke": gewaehlt["ecke"], "kasten": gewaehlt["kasten"],
                "eignung": gewaehlt["eignung"], "ziel": str(ziel)}
    if druckbreite_mm:
        ergebnis["marke_mm"] = x_mm = tb_mm(gewaehlt["kasten"][2], bild.width, druckbreite_mm)
        ergebnis["versalhoehe_mm"] = x_mm / SEITENVERHAELTNIS * ZEILE_ANTEIL * VERSAL_ANTEIL
    return ergebnis


def tb_mm(marke_px: int, bild_px: int, druckbreite_mm: float) -> float:
    """Gedruckte Breite der Marke in Millimetern."""
    return marke_px / bild_px * float(druckbreite_mm)
