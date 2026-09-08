#!/usr/bin/env python3
"""Gegenproben zur Innenteil-Geometrie im Canvas, geprueft in validate_brochure.py.

Am 07.09.2026 wurde der Innenteil umgestellt: Kopfsteg 18 mm, Fusssteg 21 mm,
Kolumnentitel und Seitenzahl nicht mehr oben, sondern unten auf 284,6 mm. Damit
das Beiwerk dort absolut sitzen kann, bekamen die Seiten ein vorangestelltes
position:relative.

Danach lief die Layoutpruefung weiter durch und meldete zwei Verstoesse - beide
falsch. Was wirklich passiert war: die Seitenregex verlangte style="width:210mm
am Anfang der Stilangabe und verlor durch das vorangestellte position:relative
59 von 85 Seiten-Containern. Und die Seitenzahl wurde im oberen Viertel der
Seite gesucht, wo seit der Umstellung keine mehr steht - gefunden wurden
stattdessen Zeilen aus dem Inhaltsverzeichnis.

Eine Pruefung, die nichts mehr findet, ist gefaehrlicher als eine, die
fehlschlaegt: sie meldet Erfolg. Deshalb steht hier nicht nur, was greifen und
was still bleiben muss, sondern auch, wie viel die Pruefung ueberhaupt sieht.

    python3 scripts/gegenproben_innenteil.py
"""

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(WURZEL / "scripts"))

import validate_brochure as V                                # noqa: E402

# Untergrenzen, keine Sollwerte. Seiten kommen und gehen; was nicht passieren
# darf, ist ein stiller Absturz der Reichweite auf einen Bruchteil.
MINDESTENS_SEITEN = 70
MINDESTENS_ZIFFERN = 40


def seiten_und_ziffern():
    seiten = ziffern = 0
    for datei in sorted(V.CANVAS_DIR.glob("*.dc.html")):
        if datei.name in V.CANVAS_AUSGENOMMEN:
            continue
        for _, block in V.canvas_pages(datei.read_text(encoding="utf-8")):
            seiten += 1
            ziffern += V.canvas_folio(block) is not None
    return seiten, ziffern


def mit_datei(name: str, inhalt: str):
    """Laesst check_canvas_footers gegen ein einzelnes praepariertes Blatt laufen."""
    ordner = Path(tempfile.mkdtemp(prefix="innenteil-"))
    (ordner / name).write_text(inhalt, encoding="utf-8")
    echt = V.CANVAS_DIR
    try:
        V.CANVAS_DIR = ordner
        return V.check_canvas_footers()
    finally:
        V.CANVAS_DIR = echt
        shutil.rmtree(ordner, ignore_errors=True)


def blatt(stil: str, beiwerk: str = "", vorspann: str = "") -> str:
    return (f'<div {vorspann}style="{stil}">'
            f'<p>Satz</p>{beiwerk}</div>')


def beiwerkzeile(ziffer: str = "07", lage: str = "284.6") -> str:
    return (f'<div style="position:absolute;left:18mm;top:{lage}mm;width:174mm;'
            f'display:flex;justify-content:space-between;align-items:baseline">'
            f'<span>Kapitel</span><span>{ziffer}</span></div>')


REGEL = "width:210mm;height:297mm;box-sizing:border-box;padding:18mm 18mm 21mm"
RELATIV = "position:relative;" + REGEL


def main():
    gut = gesamt = 0

    def probe(bedingung, text, zusatz=""):
        nonlocal gut, gesamt
        gesamt += 1
        gut += bool(bedingung)
        print(f"  [{'ok' if bedingung else 'XX'}] {text}")
        if zusatz:
            print(f"        {zusatz}")

    print("Wie weit reicht die Pruefung")
    print("-" * 66)

    seiten, ziffern = seiten_und_ziffern()
    probe(seiten >= MINDESTENS_SEITEN,
          "die Seitenerkennung erfasst den Bestand",
          f"{seiten} Seiten erkannt, Untergrenze {MINDESTENS_SEITEN}")
    probe(ziffern >= MINDESTENS_ZIFFERN,
          "die Seitenzahlen werden im Beiwerk gefunden",
          f"{ziffern} Seitenzahlen erkannt, Untergrenze {MINDESTENS_ZIFFERN}")

    # Jede Beiwerkzeile im Bestand muss einer erkannten Seite zugeordnet sein,
    # bis auf die Umschlagseiten U2 und U3, die statt einer Ziffer ihr Kuerzel
    # tragen. Sonst zaehlt die Pruefung Seiten, deren Fuss sie nie ansieht.
    offen = []
    for datei in sorted(V.CANVAS_DIR.glob("*.dc.html")):
        if datei.name in V.CANVAS_AUSGENOMMEN:
            continue
        text = datei.read_text(encoding="utf-8")
        zeilen = len(re.findall(r"top:" + re.escape(V.CANVAS_BEIWERK[:-2]) + r"mm;width:174mm", text))
        umschlag = len(re.findall(r"<span>U[234]</span>", text))
        erkannt = sum(1 for _, b in V.canvas_pages(text) if V.canvas_folio(b))
        if zeilen - umschlag != erkannt:
            offen.append(f"{datei.name}: {zeilen} Zeilen, {umschlag} Umschlag, {erkannt} erkannt")
    probe(not offen, "jede Beiwerkzeile gehoert zu einer erkannten Seite",
          "; ".join(offen) if offen else "Umschlagseiten U2/U3 tragen kein Folio und bleiben aussen vor")

    probe(not V.check_canvas_footers(), "der Bestand ist sauber",
          "check_canvas_footers meldet nichts")

    print("\nDie Seite muss erkannt werden, egal wie das Tag geschrieben ist")
    print("-" * 66)

    for name, stil, vorspann in (
            ("Stilangabe beginnt mit width", REGEL, ""),
            ("position:relative vorangestellt", RELATIV, ""),
            ("position:relative hinten angehaengt", REGEL + ";position:relative", ""),
            ("id und data-Attribut vor dem style", REGEL, 'id="s1" data-screen-label="Seite 1" '),
    ):
        n = len(list(V.canvas_pages(blatt(stil, vorspann=vorspann))))
        probe(n == 1, f"{name} - als Seite erkannt", f"{n} Container gefunden")

    print("\nDie Seitenzahl muss an ihrer Lage erkannt werden, nicht an ihrer Form")
    print("-" * 66)

    b = blatt(RELATIV, beiwerkzeile("07"))
    _, block = next(iter(V.canvas_pages(b)))
    probe(V.canvas_folio(block) == "07", "Ziffer im Beiwerk auf 284,6 mm gilt als Seitenzahl",
          f"gefunden: {V.canvas_folio(block)}")

    # Genau der Fall, der die Pruefung in die Irre fuehrte: eine Flexzeile mit
    # Ziffer im Inhaltsverzeichnis, weit oben auf der Seite.
    ihv = ('<div style="display:flex;justify-content:space-between">'
           '<span>03 · Zwei Wege. Ein Ziel.</span><span>17</span></div>')
    _, block = next(iter(V.canvas_pages(blatt(RELATIV, ihv))))
    probe(V.canvas_folio(block) is None,
          "eine Zeile aus dem Inhaltsverzeichnis gilt nicht als Seitenzahl",
          f"gefunden: {V.canvas_folio(block)}")

    _, block = next(iter(V.canvas_pages(blatt(RELATIV, beiwerkzeile("07", "270")))))
    probe(V.canvas_folio(block) is None,
          "eine Beiwerkzeile auf falscher Lage gilt nicht als Seitenzahl",
          f"auf 270 mm statt {V.CANVAS_BEIWERK}, gefunden: {V.canvas_folio(block)}")

    _, block = next(iter(V.canvas_pages(blatt(RELATIV, beiwerkzeile("U2")))))
    probe(V.canvas_folio(block) is None,
          "die Umschlagkennung U2 gilt nicht als Seitenzahl",
          f"gefunden: {V.canvas_folio(block)}")

    print("\nDer Fusssteg")
    print("-" * 66)

    ok = mit_datei("X.dc.html", blatt(RELATIV, beiwerkzeile()))
    probe(not ok, "regelrechter Fusssteg mit Seitenzahl bleibt still",
          f"21 mm, Meldungen: {len(ok)}")

    falsch = RELATIV.replace("18mm 18mm 21mm", "18mm 18mm 23.5mm")
    m = mit_datei("X.dc.html", blatt(falsch, beiwerkzeile()))
    probe(len(m) == 1, "abweichender Fusssteg mit Seitenzahl wird gemeldet",
          m[0] if m else "keine Meldung")

    m = mit_datei("X.dc.html", blatt(falsch))
    probe(not m, "abweichender Fusssteg ohne Seitenzahl bleibt still",
          "randabfallende Strecken und Rueckseiten sind nicht gebunden")

    m = mit_datei(V.CANVAS_AUSGENOMMEN[0], blatt(falsch, beiwerkzeile()))
    probe(not m, f"{V.CANVAS_AUSGENOMMEN[0]} bleibt ausgenommen",
          "der Umschlag ist anders aufgebaut")

    print("\nDie Werte kommen aus brand.json")
    print("-" * 66)

    innen = json.loads((WURZEL / "brand.json").read_text(encoding="utf-8"))
    innen = innen["grid"]["interior"]["innenteil_canvas"]
    probe(V.CANVAS_FOOT == f"{innen['margin_bottom_mm']:g}mm",
          "der gepruefte Fusssteg stammt aus brand.json",
          f"{V.CANVAS_FOOT} = innenteil_canvas.margin_bottom_mm")
    probe(V.CANVAS_BEIWERK == f"{innen['beiwerk']['oberkante_mm']:g}mm",
          "die gepruefte Beiwerklage stammt aus brand.json",
          f"{V.CANVAS_BEIWERK} = innenteil_canvas.beiwerk.oberkante_mm")

    print("-" * 66)
    print(f"  {gut} von {gesamt} wie erwartet")
    return 0 if gut == gesamt else 1


if __name__ == "__main__":
    sys.exit(main())
