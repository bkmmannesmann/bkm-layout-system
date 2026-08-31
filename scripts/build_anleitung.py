#!/usr/bin/env python3
"""Baut eine BKM Verarbeitungsanleitung aus content.json.

Die Anleitung ist ein eigenstaendiges Dokument, produktbezogen, fuer Pro
Line wie Home Line. Sie traegt kein Titelblatt - das ist ein eigenes
Dokument (scripts/build_cover.py, Variante "anleitung"). Die erste Seite
in pages[] traegt darum die Ziffer 1, dieselbe Regel wie im Innenteil der
Broschuere (pagination.production in brand.json).

    python3 scripts/build_anleitung.py content/anleitung-hz250pro/content.json

Was hier geprueft wird, ist nicht dasselbe wie im Validator: der Validator
liest den Inhalt, diese Pruefung liest das Ergebnis. Beide Wege sind noetig,
weil die haeufigsten Fehler erst beim Setzen entstehen - eine fehlende
Schriftdatei wird still ersetzt, ein zu langer Text still abgeschnitten.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pdf_checks import check_completeness, check_fonts, collect_strings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "templates" / "anleitung"
OUTPUT_DIR = PROJECT_ROOT / "output" / "anleitung"

# Pfadfelder tragen keinen Lesetext; sie im Vollstaendigkeitstest zu suchen
# ergaebe nur Rauschen. product_line steht als Alt-Text am Badge und landet
# nicht im sichtbaren Text.
SKIP_KEYS = (
    "image", "icon", "product_image", "line_badge", "logo", "keyvisual",
    "type", "product_line", "number",
)


def seiten_soll(content):
    """Zaehlt, wie viele Seiten das PDF haben muss.

    Jeder Eintrag in pages[] ergibt genau eine Seite. Weicht das PDF davon
    ab, ist eine Seite umgebrochen - fast immer, weil ein Bereich mehr
    Inhalt bekommen hat, als er fasst.
    """
    return len(content.get("pages", []))


def check_output(pdf_path, content):
    """Prueft das erzeugte PDF auf vier stille Fehler."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    fehler = check_fonts(reader)

    # min_length=3, nicht die voreingestellten 40: die kuerzesten Eintraege
    # dieses Dokuments sind die Sicherheitsangaben - "Schutzbrille" hat elf
    # Zeichen, "Gehörschutz" elf. Mit der Voreinstellung fiel die komplette
    # PSA-Liste vom Blatt, ohne dass die Pruefung etwas meldete. Das
    # Datenblatt prueft aus demselben Grund ab 3.
    fehler.extend(check_completeness(
        reader, collect_strings(content.get("pages", []),
                                min_length=3, skip_keys=SKIP_KEYS)))

    soll = seiten_soll(content)
    ist = len(reader.pages)
    if ist != soll:
        fehler.append(
            f"Das PDF hat {ist} Seiten, content.json beschreibt {soll}. "
            f"Ein Bereich fasst seinen Inhalt nicht - siehe .anl-page__body, "
            f"dort steht overflow:hidden.")

    fehler.extend(check_bildverweise(content))
    fehler.extend(check_paginierung(content))
    fehler.extend(check_abbildungen(content))
    return fehler


# Eine Abbildung braucht in der rechten Spalte 46 mm Bildhoehe, rund 4 mm
# Unterschrift und 5 mm Abstand. Bei 259 mm Satzhoehe abzueglich der
# Rubrik bleiben rund 245 mm - also vier Abbildungen. Die fuenfte wird von
# overflow:hidden abgeschnitten; die Seite sieht heil aus.
ABB_JE_SEITE = 4


def check_abbildungen(content):
    """Prueft, ob eine Seite mehr Abbildungen traegt, als in die Spalte passen.

    Der Vollstaendigkeitstest faengt das zwar auch, aber erst ueber den
    fehlenden Text der Platzhalterbeschriftung - und nur, solange es eine
    gibt. Steht dort ein echtes Bild, faellt es ersatzlos weg.
    """
    fehler = []
    for i, seite in enumerate(content.get("pages", []), 2):
        n = len(seite.get("figures", []))
        if n > ABB_JE_SEITE:
            fehler.append(
                f"Seite {i} traegt {n} Abbildungen, in die Spalte passen "
                f"{ABB_JE_SEITE}. Die uebrigen werden abgeschnitten.")
    return fehler


def check_paginierung(content):
    """Prueft die Seitenzaehlung gegen den Umfang.

    Die Anleitung zaehlt anders als die Broschuere: die sieben
    freigegebenen Fassungen tragen auf dem zweiten Blatt 2/5 oder 2/4, das
    Titelblatt ist also Blatt 1 und wird mitgezaehlt. Der Innenteil beginnt
    darum bei 2 und muss die Gesamtzahl kennen. Steht dort eine Zahl, die
    nicht zum Umfang passt, faellt das im PDF nicht auf - die Fusszeile
    sieht heil aus und nennt nur den falschen Nenner.
    """
    fehler = []
    start = content.get("page_number_start")
    gesamt = content.get("page_total")
    seiten = len(content.get("pages", []))

    if start != 2:
        fehler.append(
            f"page_number_start ist {start}, muss 2 sein: das Titelblatt "
            f"ist Blatt 1 und wird mitgezaehlt.")
    if gesamt is None:
        fehler.append("page_total fehlt - ohne die Zahl steht in der Fusszeile n/None.")
    elif gesamt != seiten + 1:
        fehler.append(
            f"page_total ist {gesamt}, der Innenteil hat aber {seiten} Seiten. "
            f"Mit dem Titelblatt sind das {seiten + 1}.")
    return fehler


def check_bildverweise(content):
    """Prueft jeden Bildpfad am Dateisystem.

    Findet WeasyPrint eine Datei nicht, bricht es nicht ab, sondern setzt
    den Alt-Text an ihre Stelle - in einer Serifenschrift, die es selbst
    mitbringt. Genau so liefen die Titelblaetter monatelang.
    """
    fehler = []
    gesehen = set()

    def geh(knoten):
        if isinstance(knoten, dict):
            for schluessel, wert in knoten.items():
                if schluessel in ("image", "icon", "product_image", "line_badge",
                                  "logo", "keyvisual") and isinstance(wert, str):
                    if wert and wert not in gesehen:
                        gesehen.add(wert)
                        pfad = (TEMPLATE_DIR / wert).resolve()
                        if not pfad.is_file():
                            fehler.append(f"Bildverweis zeigt ins Leere: {wert}")
                else:
                    geh(wert)
        elif isinstance(knoten, list):
            for eintrag in knoten:
                geh(eintrag)

    geh(content)
    return fehler


def check_offene_angaben(content):
    """Sammelt sichtbar markierte Luecken.

    Ein Entwurf darf sie haben, eine Release-Fassung nicht. Dieselbe Regel
    wie im Datenblatt, siehe docs/REDAKTIONSSTANDARD.md.
    """
    treffer = []

    def geh(knoten):
        if isinstance(knoten, str):
            if "[ANGABE FEHLT" in knoten or "[ZU PRÜFEN" in knoten:
                treffer.append(knoten.strip()[:110])
        elif isinstance(knoten, dict):
            for wert in knoten.values():
                geh(wert)
        elif isinstance(knoten, list):
            for eintrag in knoten:
                geh(eintrag)

    geh(content.get("pages", []))
    return treffer


def baue(content_path, release=False):
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML

    content = json.loads(Path(content_path).read_text(encoding="utf-8"))
    content.setdefault("page_number_start", 1)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    html = env.get_template("template.html").render(**content)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    name = Path(content_path).parent.name
    html_path = OUTPUT_DIR / f"{name}.html"
    pdf_path = OUTPUT_DIR / f"{name}.pdf"
    html_path.write_text(html, encoding="utf-8")
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(pdf_path))

    print(f"  HTML: {html_path}")
    print(f"  PDF:  {pdf_path}")

    offen = check_offene_angaben(content)
    if offen:
        wort = "Release" if release else "Entwurf"
        print(f"\n  Offene Angaben ({len(offen)}), im {wort}:")
        for eintrag in offen:
            print(f"    - {eintrag}")

    fehler = check_output(pdf_path, content)
    if fehler:
        print(f"\n  Beanstandet ({len(fehler)}):")
        for eintrag in fehler:
            print(f"    ✗ {eintrag}")

    if release and offen:
        print("\n  Eine Release-Fassung darf keine offenen Angaben tragen.")
        return 1
    return 1 if fehler else 0


def main():
    p = argparse.ArgumentParser(description="Baut eine BKM Verarbeitungsanleitung.")
    p.add_argument("content", help="Pfad zu content.json")
    p.add_argument("--release", action="store_true",
                   help="Offene Angaben blockieren die Ausgabe.")
    a = p.parse_args()

    if not Path(a.content).is_file():
        print(f"Nicht gefunden: {a.content}")
        return 1

    print("=" * 60)
    print("BKM VERARBEITUNGSANLEITUNG")
    print("=" * 60)
    return baue(a.content, release=a.release)


if __name__ == "__main__":
    sys.exit(main())
