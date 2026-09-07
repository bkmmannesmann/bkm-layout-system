#!/usr/bin/env python3
"""Gegenproben zur Blocksatzpruefung in scripts/pruefe_pdf.py.

Blocksatz dehnt den Wortzwischenraum, bis die Zeile die Spalte fuellt.
Wie weit, misst check_wortabstand - gegen die Breite, die die
eingebettete Schrift selbst fuer das Leerzeichen angibt.

Hier steht beides: Faelle, in denen die Pruefung anschlagen muss, und
Faelle, in denen sie still zu bleiben hat. Die stillen sind die
wichtigeren. Eine Pruefung, die bei jedem gewoehnlichen Absatz meldet,
liest nach zwei Wochen niemand mehr.

Gebaut wird mit WeasyPrint, nicht mit den eingebauten Standardschriften
von PyMuPDF: die Messung braucht eine Schriftdatei im PDF, aus der sich
die natuerliche Breite des Leerzeichens lesen laesst. Genau das prueft
auch einer der Faelle - ein PDF ohne eingebettete Schrift darf die
Pruefung nicht zum Raten verleiten, sondern muss sie stumm lassen.

    python3 scripts/gegenproben_wortabstand.py
"""

import io
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import pruefe_pdf as pp                                    # noqa: E402

MM = 72 / 25.4


def loecher(doc):
    return pp.check_wortabstand(doc)

# Ein Text wie aus einer Broschuere: ueberwiegend kurze Woerter, dazwischen
# ein langes Kompositum, das am Zeilenende nicht mehr passt. Ein Text aus
# lauter Komposita waere untauglich - dann hat eine schmale Zeile zwei
# Woerter und einen Zwischenraum, und es gibt nichts zu messen.
TEXT = ("Die Wand wird von innen abgedichtet, ohne sie von aussen "
        "aufzugraben. Erst wenn das Wasser gestoppt ist, wird der Aufbau "
        "dauerhaft dicht. Wer das nicht beachtet, riskiert eine neue "
        "Bauwerksabdichtung. Am Ende zaehlt, dass das Haus trocken "
        "bleibt und es so bleibt. ") * 3


def blatt(breite_mm, ausrichtung="justify", text=None):
    """Ein A4-Blatt mit einem Textkasten fester Breite."""
    from weasyprint import HTML
    html = (f'<html lang="de"><style>@page{{size:A4;margin:20mm}}'
            f'body{{font-family:"TT Norms Pro",sans-serif;font-size:9pt}}'
            f'@font-face{{font-family:"TT Norms Pro";'
            f'src:url("assets/fonts/TT_Norms_Pro_Regular.ttf")}}'
            f'p{{width:{breite_mm}mm;text-align:{ausrichtung};'
            f'hyphens:auto;hyphenate-character:"-"}}</style>'
            f'<p>{text or TEXT}</p></html>')
    puffer = io.BytesIO()
    HTML(string=html, base_url=str(ROOT_DIR)).write_pdf(puffer)
    import pymupdf
    return pymupdf.open(stream=puffer.getvalue(), filetype="pdf")


def ohne_schrift():
    """Ein PDF mit einer Standardschrift, die nicht eingebettet wird."""
    import pymupdf
    d = pymupdf.open()
    s = d.new_page(width=210 * MM, height=297 * MM)
    s.insert_text((20 * MM, 40 * MM),
                  "Ein Satz mit reichlich Woertern darin zum Messen.",
                  fontsize=9, fontname="helv")
    return d


def gebaut(name):
    p = ROOT_DIR / "output" / "anleitung" / f"{name}.pdf"
    if not p.is_file():
        return None
    import pymupdf
    return pymupdf.open(p)


FAELLE = [
    # --- muss anschlagen -------------------------------------------
    ("Blocksatz in 40 mm Spalte - Loecher",
     lambda: loecher(blatt(40)), "greift"),

    ("Blocksatz in 55 mm Spalte - Loecher",
     lambda: loecher(blatt(55)), "greift"),

    # --- muss still bleiben ----------------------------------------
    ("Derselbe Text linksbuendig - kein Befund",
     lambda: loecher(blatt(40, "left")), "still"),

    ("Derselbe Text in 90 mm Spalte - kein Befund",
     lambda: loecher(blatt(90)), "still"),

    ("Derselbe Text in 120 mm Spalte - kein Befund",
     lambda: loecher(blatt(120)), "still"),

    ("Zeile mit zwei Woertern - zu wenig zum Messen",
     lambda: loecher(
         blatt(34, text="Bauwerksabdichtung Gebaeudebestand")), "still"),

    ("Schrift nicht eingebettet - die Pruefung raet nicht",
     lambda: loecher(ohne_schrift()), "still"),

    # Die Meldung muss das Wort nennen, an dem es haengt - ohne das ist
    # sie eine Feststellung und keine Handreichung.
    ("Die Meldung nennt das Wort der naechsten Zeile",
     lambda: [x for x in loecher(blatt(40)) if " - es haengt an " in x],
     "greift"),
]


def kennzahl_faelle():
    """Die Kennzahl muss auch dann etwas sagen, wenn nichts zu melden ist."""
    aus = []
    k = pp.wortabstand_kennzahl(blatt(90))
    aus.append(("Kennzahl bei breiter Spalte nahe 1,00",
                k is not None and k["median"] < 1.15, k))
    k = pp.wortabstand_kennzahl(blatt(40))
    aus.append(("Kennzahl bei schmaler Spalte deutlich darueber",
                k is not None and k["median"] > 1.40, k))
    k = pp.wortabstand_kennzahl(ohne_schrift())
    aus.append(("Kennzahl ohne eingebettete Schrift ist leer",
                k is None, k))
    return aus


def main():
    print("=" * 64)
    print("  Gegenproben Blocksatz")
    print("=" * 64)
    gut = gesamt = 0
    for name, f, soll in FAELLE:
        befunde = f()
        ok = bool(befunde) == (soll == "greift")
        gut += ok
        gesamt += 1
        print(f"  [{'ok' if ok else 'XX'}] {name}")
        print(f"        erwartet {soll}, gefunden {len(befunde)}")
        if befunde and (not ok or soll == "greift"):
            print(f"          {befunde[0][:96]}")

    for name, ok, k in kennzahl_faelle():
        gut += ok
        gesamt += 1
        wert = "-" if k is None else f"{k['median']:.2f}x ueber {k['zeilen']} Zeilen"
        print(f"  [{'ok' if ok else 'XX'}] {name}")
        print(f"        {wert}")

    # Gegen den echten Bestand. Nicht "kein Loch": vier Zeilen ueber acht
    # Anleitungen stehen bekanntermassen darueber, und sie mit weichen
    # Trennzeichen zu schliessen hat den Satz an der rechten Fluchtlinie
    # aufgerissen. Geprueft wird, was zaehlt - dass der Satz im Mittel
    # auf Normalmass laeuft und nicht stillschweigend abrutscht.
    for name in ("anleitung-novusan", "anleitung-hz250pro",
                 "anleitung-sp-express"):
        doc = gebaut(name)
        if doc is None:
            print(f"  [ - ] {name} - uebersprungen, nicht gebaut")
            continue
        k = pp.wortabstand_kennzahl(doc)
        befunde = loecher(doc)
        ok = (k is not None and k["median"] <= 1.05
              and k["auffaellig"] < 10 and len(befunde) <= 1)
        gut += ok
        gesamt += 1
        print(f"  [{'ok' if ok else 'XX'}] {name} - Satz laeuft auf Normalmass")
        print(f"        Mittel {k['median']:.2f}x, {k['auffaellig']:.0f}% ueber "
              f"der Setzergrenze, {len(befunde)} Loch/Loecher")

    print("-" * 64)
    print(f"  {gut} von {gesamt} wie erwartet")
    return 0 if gut == gesamt else 1


if __name__ == "__main__":
    sys.exit(main())
