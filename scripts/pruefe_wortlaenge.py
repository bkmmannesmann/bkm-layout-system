#!/usr/bin/env python3
"""Zu lange Woerter finden, bevor daraus ein Wortbruch wird.

Am 03.09.2026 stand in einer gerenderten Broschuere 'Technologi / emarke'
und 'Partnernet / zwerk'. Das entsteht, wenn ein Wort breiter ist als die
Spalte, in der es steht. Was dann passiert, entscheidet das Stylesheet:

  overflow-wrap: break-word   -> das Wort wird mitten durchgehackt
  (nichts davon)              -> das Wort steht ueber die Spaltenkante

Beides ist derselbe Fehler in zwei Gestalten, und beide werden erst im
fertigen PDF sichtbar. scripts/pruefe_pdf.py findet sie dort - aber dann
ist gebaut. Diese Pruefung setzt eine Stufe frueher an, am ausgelegten
Satz, und beantwortet die Frage, die von der Wahl des Renderers
unabhaengig ist: passt das laengste Wort in seine Spalte?

Gemessen wird, nicht geschaetzt. Jedes Wort wird mit seinem eigenen Stil
- Schrift, Schnitt, Groesse, Laufweite - noch einmal ausgelegt, und die
Breite, die dabei herauskommt, geht gegen die Innenbreite des Kastens,
in dem es steht. Zeichen mal Durchschnittsbreite waere geraten; das 'W'
ist in TT Norms Pro dreimal so breit wie das 'i'.

Zwei Dinge sind ausdruecklich kein Fehler:

  hyphens: auto   Dann darf das Wort brechen, mit Trennstrich. Gemessen
                  wird dann nicht das ganze Wort, sondern seine laengste
                  Silbe - nur die muss am Stueck passen. Ohne diese
                  Unterscheidung waere jeder deutsche Fliesstext voller
                  Falschmeldungen.

  Bindestriche    'Feuchte-Check' darf nach dem Strich umbrechen. Das
                  Wort zerfaellt in seine Teile, jeder wird einzeln
                  gemessen.

Wo die Pruefung nichts findet, und warum das richtig ist: eine
Tabellenspalte ohne feste Breite waechst mit ihrem Inhalt. Dort entsteht
kein Wortbruch, sondern eine zu breite Tabelle - ein anderer Fehler, den
scripts/pruefe_pdf.py an der Blattkante findet. Diese Pruefung greift,
wo die Breite feststeht, und das ist im Satzspiegel die Regel.

Aufruf:

    python3 scripts/pruefe_wortlaenge.py <datei.html> [--basis <ordner>]

Rueckgabe 0, wenn jedes Wort in seine Spalte passt, sonst 1.

Die Bauwege rufen sie selbst auf - scripts/build_pages.py und
scripts/build_anleitung.py legen den Satz ohnehin aus, bevor sie
schreiben, und reichen das ausgelegte Dokument hier herein. Ein zu
langes Wort steht dann unter den Beanstandungen des Baus.

Die Pruefung laeuft auch gegen HTML, das nicht aus diesem Repository
stammt - etwa gegen einen Canvas-Export. Sie braucht nur die Datei und
den Ordner, aus dem deren Schriften und Bilder kommen.
"""

import argparse
import re
import sys
from pathlib import Path

from weasyprint import HTML
from weasyprint.text.line_break import split_first_line

try:
    import pyphen
except ImportError:                                   # pragma: no cover
    pyphen = None

PX_JE_MM = 96 / 25.4

# Stellen, an denen ein Wort ohne Zutun des Stylesheets umbrechen darf.
# Getrennt wird nach dem Zeichen, nicht davor - so haelt es CSS.
TRENNZEICHEN = "-‐–—/­"

# Unter dieser Breite lohnt keine Meldung: Kaesten, die im Satz nur ein
# paar Millimeter halten, sind Striche, Marken oder leere Huellen.
MINDESTBREITE_MM = 5.0

_woerterbuecher = {}


def in_mm(px):
    return px / PX_JE_MM


def woerterbuch(sprache):
    """Trennwoerterbuch fuer eine Sprache, einmal geladen."""
    if sprache in _woerterbuecher:
        return _woerterbuecher[sprache]
    buch = None
    if pyphen is not None:
        for versuch in (sprache, sprache.split("-")[0], "de_DE"):
            try:
                buch = pyphen.Pyphen(lang=versuch)
                break
            except Exception:
                continue
    _woerterbuecher[sprache] = buch
    return buch


def stuecke(wort, style):
    """Das Wort in die Teile zerlegen, die am Stueck stehen muessen.

    Erst an den Trennzeichen, die jedes Stylesheet erlaubt. Steht das
    Wort unter hyphens:auto, danach zusaetzlich an den Silbenfugen -
    dann muss nur die laengste Silbe passen, nicht das ganze Wort.
    """
    teile = [t for t in re.split(f"(?<=[{re.escape(TRENNZEICHEN)}])", wort) if t]
    # Das weiche Trennzeichen ist unsichtbar, bis dort umbrochen wird -
    # dann steht da ein Strich. Gemessen wird der Zustand nach dem
    # Umbruch, sonst faellt das Stueck um die Strichbreite zu schmal aus.
    teile = [t[:-1] + "-" if t.endswith("\u00ad") else t for t in teile]

    if style["hyphens"] != "auto":
        return teile

    buch = woerterbuch((style["lang"] or "de").lower())
    if buch is None:
        return teile

    fein = []
    for teil in teile:
        silben = buch.inserted(teil, hyphen="\x00").split("\x00")
        # Die Silbe traegt den Trennstrich mit, der bei einem Umbruch
        # gesetzt wird - sonst faellt die Messung um dessen Breite zu
        # schmal aus.
        fein.extend(s + "-" for s in silben[:-1])
        fein.append(silben[-1])
    return fein


def breite(text, style):
    """Wie breit dieses Stueck ausgelegt wirklich ist, in Pixeln."""
    return split_first_line(text, style, None, None, 0)[3]


def textkaesten(box, kasten=None, seite=None):
    """Jede Textbox mit dem Kasten, dessen Zeilen sie fuellt.

    Der Kasten ist der Block, an dem die Zeilenbox haengt - genau der
    gibt die Breite vor, in die umbrochen wird. Er kann tiefer liegen
    als die Spalte: eine Tabellenzelle in einer Spalte zaehlt als
    Zelle, nicht als Spalte.
    """
    art = type(box).__name__
    if art == "LineBox":
        for kind in box.children:
            yield from textkaesten(kind, kasten, seite)
        return
    for kind in getattr(box, "children", ()):
        if type(kind).__name__ == "LineBox":
            yield from textkaesten(kind, box, seite)
        else:
            yield from textkaesten(kind, kasten, seite)
    if art == "TextBox" and kasten is not None:
        yield seite, kasten, box


def weich_getrennt(quelle):
    """Woerter, die in der Quelle ein weiches Trennzeichen tragen.

    WeasyPrint wirft U+00AD beim Auslegen weg - im Boxbaum steht
    'Technologiemarke', nicht 'Technologie\u00admarke'. Die erlaubte
    Bruchstelle ist damit unsichtbar, und ohne diese Liste wuerde die
    Pruefung ausgerechnet das Wort anmahnen, an dem der Setzer die
    Trennung schon von Hand gesetzt hat.

    Geliefert wird eine Zuordnung: nacktes Wort -> Fassung mit Fugen.
    """
    if not quelle:
        return {}
    return {w.replace("\u00ad", ""): w
            for w in re.findall(r"[^\s<>]*\u00ad[^\s<>]*", quelle)}


def pruefe(html, basis=None, stylesheets=None):
    """Aus HTML: auslegen und messen. Liefert eine Liste von Befunden."""
    dokument = HTML(string=html, base_url=basis).render(
        stylesheets=stylesheets)
    return pruefe_dokument(dokument, quelle=html)


def pruefe_dokument(dokument, quelle=None):
    """Ein bereits ausgelegtes Dokument messen.

    Der Bauweg legt ohnehin aus, bevor er schreibt. Er reicht sein
    Dokument hier herein, statt es fuer die Pruefung ein zweites Mal
    auszulegen - bei neunundvierzig Seiten sind das mehrere Sekunden.
    Die Quelle kommt mit, weil im Boxbaum die weichen Trennzeichen
    fehlen.
    """
    fugen = weich_getrennt(quelle)
    befunde = {}
    for nr, seite in enumerate(dokument.pages, 1):
        for _, kasten, tb in textkaesten(seite._page_box, seite=nr):
            verfuegbar = kasten.width
            if not isinstance(verfuegbar, (int, float)):
                continue
            if in_mm(verfuegbar) < MINDESTBREITE_MM:
                continue
            for wort in tb.text.split():
                if len(wort) < 6:
                    continue
                for teil in stuecke(fugen.get(wort, wort), tb.style):
                    gemessen = breite(teil, tb.style)
                    if gemessen <= verfuegbar:
                        continue
                    schluessel = (wort, teil, round(in_mm(verfuegbar), 1))
                    treffer = befunde.setdefault(schluessel, {
                        "wort": wort, "teil": teil,
                        "breit": in_mm(gemessen),
                        "kasten": in_mm(verfuegbar),
                        "tag": kasten.element_tag or "?",
                        "seiten": set(),
                    })
                    treffer["seiten"].add(nr)

    reihe = sorted(befunde.values(), key=lambda b: (-(b["breit"] - b["kasten"])))
    return reihe


def bericht(befunde, quelle):
    print(f"  Wortlaengen: {quelle}")
    if not befunde:
        print("  Jedes Wort passt in seine Spalte.")
        return 0
    if len(befunde) == 1:
        print("  Eine Stelle, an der ein Wort breiter ist als sein Kasten:")
    else:
        print(f"  {len(befunde)} Stellen, an denen ein Wort breiter ist "
              f"als sein Kasten:")
    for b in befunde:
        seiten = ", ".join(str(s) for s in sorted(b["seiten"])[:6])
        stueck = "" if b["teil"] == b["wort"] else f" (Stueck {b['teil']!r})"
        print(f"    - {b['wort']!r}{stueck} misst {b['breit']:.1f} mm, "
              f"<{b['tag']}> haelt {b['kasten']:.1f} mm - Seite {seiten}")
    print()
    print("  Was das im Satz heisst: mit overflow-wrap:break-word wird das")
    print("  Wort mitten durchgehackt, ohne es steht es ueber die Kante.")
    print("  Abhilfe: kuerzeres Wort, weiches Trennzeichen U+00AD an der")
    print("  richtigen Fuge, hyphens:auto fuer den Kasten, oder mehr Breite.")
    return 1


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("html", help="Die zu pruefende HTML-Datei")
    p.add_argument("--basis", help="Ordner fuer Schriften und Bilder "
                                   "(voreingestellt: der der Datei)")
    a = p.parse_args()

    pfad = Path(a.html)
    if not pfad.exists():
        print(f"  Datei nicht gefunden: {pfad}")
        return 2
    basis = a.basis or str(pfad.parent)
    return bericht(pruefe(pfad.read_text(encoding="utf-8"), basis), pfad.name)


if __name__ == "__main__":
    sys.exit(main())
