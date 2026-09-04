#!/usr/bin/env python3
"""Gegenproben fuer scripts/pruefe_pdf.py.

Eine Pruefung, die nie greift, ist keine Pruefung. Jede der sechs
Funktionen bekommt hier ein praepariertes PDF vorgesetzt, das genau
ihren Fehler traegt - und ein sauberes, bei dem sie still bleiben muss.

Die Fehler sind nicht erfunden. Es sind die, die am 03.09.2026 in einer
aus Claude Design exportierten Broschuere standen: die Blattbeschriftung
'U2' im Druck, Text bis 299,6 mm auf einem 297-mm-Blatt, dreizehn Seiten
unter dem Fusssteg und 'Technologi/emarke' ohne Trennstrich.

    python3 scripts/gegenproben_pdf.py
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import pruefe_pdf as pp  # noqa: E402

MM = 72 / 25.4


def blatt(zeilen):
    """Baut ein A4-Blatt mit Text an genau vorgegebenen Stellen.

    zeilen: (x_mm, y_mm, text). Gesetzt wird in Helvetica - fuer die
    Geometrie- und Textpruefungen ist die Schrift ohne Belang, die
    Schriftpruefung wird getrennt geprueft.
    """
    import pymupdf
    d = pymupdf.open()
    s = d.new_page(width=210 * MM, height=297 * MM)
    for x, y, t in zeilen:
        s.insert_text((x * MM, y * MM), t, fontsize=9, fontname="helv")
    return d


SAUBER = [(20, 40, "Ein ganz gewoehnlicher Satz im Satzspiegel."),
          (20, 60, "Noch einer, damit die Seite nicht leer ist.")]


def faelle():
    import pymupdf
    geo = pp.GEOMETRIE["broschuere"]

    # Wortbruch: die zerrissene Form UND das ganze Wort im selben
    # Dokument - ohne den zweiten Beleg darf die Pruefung nicht greifen.
    d_bruch = pymupdf.open()
    s = d_bruch.new_page(width=210 * MM, height=297 * MM)
    s.insert_text((20 * MM, 40 * MM), "Die Technologi", fontsize=9, fontname="helv")
    s.insert_text((20 * MM, 44 * MM), "emarke absichern", fontsize=9, fontname="helv")
    s.insert_text((20 * MM, 60 * MM), "Technologiemarke im Fliesstext.",
                  fontsize=9, fontname="helv")

    # Derselbe Umbruch, aber ohne Beleg: zwei Woerter, die nur zufaellig
    # aneinanderpassen. Hier muss die Pruefung still bleiben.
    d_normal = blatt([(20, 40, "Wir bauen kein Publikum"),
                      (20, 44, "auf, sondern ein Netzwerk.")])

    return [
        ("unveraendert - alle Pruefungen still",
         lambda d: (pp.check_canvas_marker(d) + pp.check_blattkante(d)
                    + pp.check_satzspiegel(d, geo)[0] + pp.check_wortbruch(d)
                    + pp.check_blattformat(d)),
         blatt(SAUBER), False),

        ("Blattbeschriftung 'U2' im Druck", pp.check_canvas_marker,
         blatt(SAUBER + [(170, 30, "U2")]), True),

        ("Blattbeschriftung 'Artboard 3'", pp.check_canvas_marker,
         blatt(SAUBER + [(150, 30, "Artboard 3")]), True),

        # 299 mm, nicht 296: insert_text setzt die Grundlinie, der Block
        # reicht nur rund 1 mm tiefer. Bei 296 blieb er unter 297 und die
        # Pruefung schwieg zu Recht - der Prueffall war zu zahm, nicht die
        # Pruefung zu stumpf. Die echte Fassung stand bei 299,6 mm.
        ("Text ueber der Blattkante", pp.check_blattkante,
         blatt(SAUBER + [(20, 299, "Diese Zeile wird beschnitten.")]), True),

        ("Text unter dem Fusssteg", lambda d: pp.check_satzspiegel(d, geo)[0],
         blatt(SAUBER + [(20, 280, "Diese Zeile steht unter dem Fusssteg.")]), True),

        ("Text ueber dem Kopfsteg", lambda d: pp.check_satzspiegel(d, geo)[0],
         blatt(SAUBER + [(20, 20, "Diese Zeile steht zu hoch.")]), True),

        ("Satz hinter der rechten Fluchtlinie", lambda d: pp.check_satzspiegel(d, geo)[0],
         blatt(SAUBER + [(180, 100, "weit nach rechts hinaus")]), True),

        # Das Impressum steht vertragsgemaess im Fusssteg: es muss als
        # Hinweis erscheinen, nicht als Beanstandung. Geprueft wird beides -
        # dass die Beanstandungsliste leer bleibt und die Hinweisliste nicht.
        ("Impressum im Fusssteg - keine Beanstandung",
         lambda d: pp.check_satzspiegel(d, geo)[0],
         blatt(SAUBER + [(20, 280, "Copyright BKM.MANNESMANN AG - "
                                   "All rights reserved.")]), False),

        ("Impressum im Fusssteg - aber als Hinweis",
         lambda d: pp.check_satzspiegel(d, geo)[1],
         blatt(SAUBER + [(20, 280, "Copyright BKM.MANNESMANN AG - "
                                   "All rights reserved.")]), True),

        ("Wortbruch ohne Trennstrich", pp.check_wortbruch, d_bruch, True),

        ("gewoehnlicher Umbruch - kein Wortbruch", pp.check_wortbruch,
         d_normal, False),

        ("falsches Blattformat", pp.check_blattformat,
         (lambda: (lambda d: (d.new_page(width=148 * MM, height=210 * MM), d)[1])(
             __import__("pymupdf").open()))(), True),
    ]


def main():
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        print("pymupdf fehlt.")
        return 2

    schlecht = 0
    proben = faelle()
    for name, pruefung, doc, soll in proben:
        gefunden = pruefung(doc)
        gut = bool(gefunden) == soll
        schlecht += not gut
        zeichen = "greift " if gefunden else "still  "
        print(f"  {zeichen} {name:44s} {'ok' if gut else 'FEHLSCHLAG'}")
        for f in gefunden[:2]:
            print(f"          {f}")
    print()
    print(f"  {len(proben)-schlecht} von {len(proben)} Gegenproben wie erwartet.")
    return 1 if schlecht else 0


if __name__ == "__main__":
    sys.exit(main())
