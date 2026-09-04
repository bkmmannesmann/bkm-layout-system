#!/usr/bin/env python3
"""Gegenproben zu scripts/pruefe_wortlaenge.py.

Eine Pruefung, von der niemand gesehen hat, dass sie anschlaegt, ist
keine Pruefung. Und eine, die bei jedem langen deutschen Wort anschlaegt,
ist schlimmer als keine - dann sieht sie irgendwann keiner mehr an.

Deshalb stehen hier beide Sorten: Faelle, die anschlagen muessen, und
Faelle, bei denen die Pruefung still zu bleiben hat. Die stillen sind
die wichtigeren. 'Feuchtigkeitsschutz' ist neunzehn Zeichen lang und
voellig in Ordnung, solange die Spalte breit genug ist oder das Wort
brechen darf.

Aufruf:  python3 scripts/gegenproben_wortlaenge.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pruefe_wortlaenge import pruefe                       # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent
KOPF = ("<style>@page{size:A4;margin:15mm}"
        "body{font-family:sans-serif;font-size:9pt}</style>")


def blatt(inneres):
    return f'<html lang="de">{KOPF}{inneres}</html>'


def kasten(text, breite_mm, trennung="none", groesse="9pt"):
    return blatt(f'<div style="width:{breite_mm}mm;hyphens:{trennung};'
                 f'font-size:{groesse}">{text}</div>')


def anleitung_html():
    p = WURZEL / "output/anleitung/anleitung-novusan.html"
    return p.read_text(encoding="utf-8") if p.is_file() else None


FAELLE = []


def fall(name, wie_viele):
    def nimm(f):
        FAELLE.append((name, wie_viele, f))
        return f
    return nimm


# --- Faelle, die anschlagen muessen ------------------------------------

@fall("Langes Wort in schmaler Spalte ohne Trennung", 1)
def _():
    return pruefe(kasten("Technologiemarke", 22))


@fall("Zwei lange Woerter, zwei Befunde", 2)
def _():
    return pruefe(kasten("Technologiemarke und Partnernetzwerk", 22))


@fall("Dasselbe Wort gross gesetzt sprengt die breite Spalte", 1)
def _():
    return pruefe(kasten("Partnernetzwerk", 55, groesse="32pt"))


@fall("Trennung an, aber das Wort hat keine Fuge", 1)
def _():
    # Eine Kennung ohne Silben: pyphen findet nichts zu trennen, also
    # muss sie am Stueck passen - und tut es nicht.
    return pruefe(kasten("XKQVWZBRTMFPGHDN", 18, trennung="auto"))


@fall("Auch der Teil hinter dem Bindestrich muss passen", 1)
def _():
    return pruefe(kasten("Fach-Feuchtigkeitsschutzsystem", 25))


# --- Faelle, bei denen die Pruefung still bleiben muss -----------------

@fall("Dasselbe Wort in breiter Spalte - kein Befund", 0)
def _():
    return pruefe(kasten("Technologiemarke", 60))


@fall("Schmale Spalte, aber Trennung erlaubt - kein Befund", 0)
def _():
    return pruefe(kasten("Technologiemarke Partnernetzwerk", 22,
                         trennung="auto"))


@fall("Bindestrichwort, dessen Teile einzeln passen - kein Befund", 0)
def _():
    return pruefe(kasten("Feuchte-Check", 20))


@fall("Weiches Trennzeichen an der Fuge loest den Befund auf", 0)
def _():
    return pruefe(kasten("Technologie­marke", 22))


@fall("Zierkasten unter fuenf Millimetern wird nicht gemessen", 0)
def _():
    return pruefe(kasten("Partnernetzwerk", 3))


@fall("Kurze Woerter bleiben aussen vor", 0)
def _():
    return pruefe(kasten("Wand Salz Putz Bohr", 6))


# --- Gegen den echten Bestand ------------------------------------------

@fall("Gebaute Anleitung Novusan - kein Befund", 0)
def _():
    html = anleitung_html()
    if html is None:
        return None
    return pruefe(html, str(WURZEL / "templates/anleitung"))


@fall("Dieselbe Anleitung mit einem zu langen Wort in der Werkzeugliste", None)
def _():
    """Der Beweis am eigenen Bestand.

    In der Werkzeugliste der Anleitung - sechsunddreissig Komma drei
    Millimeter, hyphens:none - wird 'Bohrmaschine' durch ein
    fuenfunddreissig Zeichen langes Wort ersetzt, das dort
    dreiundfuenfzig Millimeter braucht. Erwartet wird mindestens ein Befund; 'mindestens',
    weil die Ersetzung im HTML mehrfach greifen kann. Die Zahl ist
    nicht der Punkt, das Anschlagen ist es.

    Warum die Werkzeugliste und nicht die Tabelle daneben, die mit
    siebzehn Millimetern schmaler ist: eine Tabellenspalte ohne feste
    Breite waechst mit ihrem Inhalt. Dort entsteht kein Wortbruch,
    sondern eine zu breite Tabelle - ein anderer Fehler, den
    scripts/pruefe_pdf.py an der Blattkante findet. Diese Pruefung
    greift, wo die Breite feststeht.
    """
    html = anleitung_html()
    if html is None:
        return None
    ersetzt = html.replace("Bohrmaschine",
                           "Feuchtigkeitsschutzsystemkomponente")
    if ersetzt == html:
        return None
    return pruefe(ersetzt, str(WURZEL / "templates/anleitung"))


def main():
    print("=" * 62)
    print("  Gegenproben Wortlaenge")
    print("=" * 62)
    gut = uebersprungen = 0
    for name, erwartet, f in FAELLE:
        befunde = f()
        if befunde is None:
            print(f"  [ - ] {name}")
            print("        uebersprungen: gebaute Anleitung fehlt")
            uebersprungen += 1
            continue
        if erwartet is None:
            ok = len(befunde) >= 1
            soll = "mindestens 1"
        else:
            ok = len(befunde) == erwartet
            soll = str(erwartet)
        gut += ok
        print(f"  [{'ok' if ok else 'XX'}] {name}")
        print(f"        erwartet {soll}, gefunden {len(befunde)}")
        if not ok:
            for b in befunde[:4]:
                print(f"          {b['wort']!r} {b['breit']:.1f} mm "
                      f"in {b['kasten']:.1f} mm")
    gesamt = len(FAELLE) - uebersprungen
    print("-" * 62)
    print(f"  {gut} von {gesamt} wie erwartet"
          + (f", {uebersprungen} uebersprungen" if uebersprungen else ""))
    return 0 if gut == gesamt else 1


if __name__ == "__main__":
    sys.exit(main())
