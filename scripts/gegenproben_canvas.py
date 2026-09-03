#!/usr/bin/env python3
"""Gegenproben fuer die Pruefungen in build_anleitung_canvas.py.

Eine Pruefung, die nie greift, ist keine Pruefung. Jede der vier
Funktionen bekommt hier einen Fehler vorgesetzt, den sie melden muss -
und einen unveraenderten Lauf, bei dem sie still bleiben muss. Die
Fehler sind nicht erfunden: es sind die drei, die am 01.09.2026 im
Dokument standen, plus die naheliegenden Nachbarn.

    python3 scripts/gegenproben_canvas.py

Setzt voraus, dass templates/brochure/I-Anleitung.dc.html gebaut ist.
"""

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import build_anleitung_canvas as bac  # noqa: E402

ZIEL = ROOT_DIR / "templates" / "brochure" / "I-Anleitung.dc.html"


def faelle(h, blaetter):
    """(Name, Pruefung, praepariertes Dokument, soll_greifen)."""
    def chrome(x):
        return bac.check_chrome(x, blaetter)

    return [
        ("unveraendert - alle drei Pruefungen bleiben still",
         lambda x: chrome(x) + bac.check_seitenrahmen(x) + bac.check_fotolage(x),
         h, False),

        ("Link auf eine andere Canvas-Gruppe", chrome,
         h.replace("<section style=",
                   '<a href="A-Titelblaetter.dc.html">A</a><section style=', 1), True),

        ("Kopfblock: <h1> ausserhalb der Blaetter", chrome,
         h.replace("<section style=",
                   '<h1 style="font-size:44px">Verarbeitungsanleitung</h1>'
                   '<section style=', 1), True),

        ("Labelleiste ueber dem Blatt", chrome,
         h.replace('<div id="anleitung-titel"',
                   '<div style="border-bottom:2px solid #1c4b42">Titelblatt</div>'
                   '<div id="anleitung-titel"', 1), True),

        ("ein Blatt fehlt", chrome,
         re.sub(r'<div id="anleitung-nacharbeit" data-screen-label="[^"]*"'
                r' style="width:210mm;height:297mm',
                '<div style="width:0mm;height:0mm', h), True),

        ("zwei Blaetter mit derselben Kennung", chrome,
         h.replace('id="anleitung-anleitung-2"', 'id="anleitung-anleitung-1"', 1), True),

        ("html/body aus cover-spec.css durchgelassen", bac.check_seitenrahmen,
         h.replace("<style>", "<style>\nhtml, body { width: 210mm; height: 297mm; }",
                   1), True),

        ("die alte vollflaechige Fotolage gewinnt zuletzt", bac.check_fotolage,
         h.replace("</style>",
                   ".cover__hero { position: relative; width: 100%;"
                   " min-height: 150mm; }\n</style>", 1), True),

        ("cover-spec.css gar nicht eingebunden", bac.check_fotolage,
         re.sub(r"\.cover__hero\s*\{[^}]*\}", "", h), True),

        ("Variantenklasse am Titelblatt weggeschnitten", bac.check_fotolage,
         h.replace('class="cover cover--anleitung"', 'class="huelle"', 1), True),

        ("Titelfoto um 1 mm verrutscht", bac.check_fotolage,
         h.replace("top: 117.46mm", "top: 118.46mm", 1), True),
    ]


def main():
    if not ZIEL.is_file():
        print(f"Nicht gefunden: {ZIEL.relative_to(ROOT_DIR)} - erst bauen.")
        return 2
    h = ZIEL.read_text(encoding="utf-8")
    blaetter = len(re.findall(r'style="width:210mm;height:297mm', h))

    schlecht = 0
    for name, pruefung, doc, soll in faelle(h, blaetter):
        gefunden = pruefung(doc)
        gut = bool(gefunden) == soll
        schlecht += not gut
        zeichen = "greift " if gefunden else "still  "
        print(f"  {zeichen} {name:48s} {'ok' if gut else 'FEHLSCHLAG'}")
        for f in gefunden:
            print(f"          {f}")

    print()
    gesamt = len(faelle(h, blaetter))
    print(f"  {gesamt - schlecht} von {gesamt} Gegenproben wie erwartet.")
    return 1 if schlecht else 0


if __name__ == "__main__":
    sys.exit(main())
