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
    # Traegt keinen Lesetext: $comment erklaert die Datei, hero_image_alt
    # steht als Alt-Text am Titelfoto und erscheint nur, wenn das Bild
    # fehlt - dann meldet check_bildverweise es ohnehin.
    "$comment", "hero_image_alt",
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
    zu_pruefen = list(content.get("pages", []))
    if content.get("cover"):
        zu_pruefen.append(content["cover"])
    fehler.extend(check_completeness(
        reader, collect_strings(zu_pruefen, min_length=3, skip_keys=SKIP_KEYS)))

    # Das Titelblatt liegt im selben PDF und zaehlt mit, sofern es gebaut
    # wurde. Ohne cover-Block enthaelt die Datei nur den Innenteil.
    soll = seiten_soll(content) + (1 if content.get("cover") else 0)
    ist = len(reader.pages)
    if ist != soll:
        fehler.append(
            f"Das PDF hat {ist} Seiten, erwartet sind {soll}. "
            f"Faellt eine Seite aus, fasst ein Bereich seinen Inhalt nicht - "
            f"siehe .anl-page__body, dort steht overflow:hidden.")

    fehler.extend(check_bildverweise(content))
    fehler.extend(check_paginierung(content))
    fehler.extend(check_abbildungen(content))
    fehler.extend(check_typoskala(pdf_path))
    return fehler


def check_typoskala(pdf_path):
    """Misst die Display-Groessen im fertigen PDF gegen brand.json.

    Die Stufen standen bis 31.08.2026 nur in der CSS und waren damit bei
    jedem neuen Produkt frei waehlbar - eine Vorgabe, die niemand prueft,
    ist keine. Geprueft wird nur Unbounded: die Brotschrift traegt zu
    viele berechtigte Abstufungen, die Auszeichnungsschrift nicht.

    Das Titelblatt bleibt aussen vor; fuer das gilt type_scale.cover.
    """
    try:
        import pymupdf
    except ImportError:
        return []

    skala = json.loads((ROOT := PROJECT_ROOT / "brand.json").read_text(encoding="utf-8"))
    skala = skala.get("type_scale", {}).get("anleitung", {})
    erlaubt = skala.get("display_sizes_pt")
    if not erlaubt:
        return []

    gefunden = {}
    with pymupdf.open(str(pdf_path)) as doc:
        for nummer, seite in enumerate(doc):
            if nummer == 0:            # Titelblatt, eigene Skala
                continue
            for block in seite.get_text("dict")["blocks"]:
                for zeile in block.get("lines", []):
                    for teil in zeile["spans"]:
                        if "Unbounded" not in teil["font"] or not teil["text"].strip():
                            continue
                        groesse = round(teil["size"], 1)
                        if groesse not in erlaubt:
                            gefunden.setdefault(groesse, teil["text"].strip()[:34])

    return [f"Unbekannte Display-Groesse {g} pt bei {t!r} - zugelassen sind "
            f"{', '.join(str(x) for x in erlaubt)} pt laut "
            f"type_scale.anleitung in brand.json"
            for g, t in sorted(gefunden.items())]


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
                if schluessel == "icon" and isinstance(wert, str) and wert:
                    # icon traegt keinen Pfad, sondern einen Namen. Das
                    # Template bindet ihn mit 'ignore missing' ein - ein
                    # Tippfehler laesst den Kasten still leer.
                    if wert not in gesehen:
                        gesehen.add(wert)
                        if not (TEMPLATE_DIR / "icons" / f"{wert}.svg").is_file():
                            fehler.append(
                                f"Icon gibt es nicht: {wert}.svg fehlt in "
                                f"templates/anleitung/icons/")
                elif schluessel in ("image", "product_image", "line_badge",
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


def baue_titelblatt(content):
    """Baut das Titelblatt der Anleitung ueber den Cover-Bauweg.

    Das Titelblatt ist Blatt 1 des Dokuments - so steht es in allen sieben
    freigegebenen Fassungen, deren zweites Blatt 2/n traegt. Es entsteht
    trotzdem nicht hier, sondern in templates/cover/: dieselbe Vorlage
    traegt die Titel der Broschueren, und zwei Wege zu derselben Seite
    laufen auseinander. Belegt am Titelfoto, das monatelang auf beiden
    Wegen einen anderen Ausschnitt zeigte.

    Der Inhalt kommt aus dem cover-Block der Anleitung, nicht aus den
    Vorgaben in build_cover.py: die stehen dort produktneutral
    ("Schritt fuer Schritt zum Ergebnis"), die freigegebenen Anleitungen
    nennen auf dem Titel ihr Produkt.
    """
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import build_cover

    titel = dict(content.get("cover") or {})
    if not titel:
        return None
    titel.setdefault("title", content.get("title", ""))
    ergebnis = build_cover.build_cover("anleitung", titel)
    if ergebnis is None:
        return None
    return build_cover.OUTPUT_DIR / "cover_anleitung.pdf"


def fuege_zusammen(titel_pdf, innen_pdf, ziel):
    """Legt Titelblatt und Innenteil in eine Datei."""
    from pypdf import PdfWriter

    w = PdfWriter()
    for teil in (titel_pdf, innen_pdf):
        w.append(str(teil))
    with open(ziel, "wb") as f:
        w.write(f)


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
    innen_pdf = OUTPUT_DIR / f"{name}-innenteil.pdf"
    pdf_path = OUTPUT_DIR / f"{name}.pdf"
    html_path.write_text(html, encoding="utf-8")
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(innen_pdf))

    titel_pdf = baue_titelblatt(content)
    if titel_pdf and titel_pdf.is_file():
        fuege_zusammen(titel_pdf, innen_pdf, pdf_path)
        print(f"  Titelblatt und Innenteil zusammengefuehrt")
    else:
        innen_pdf.replace(pdf_path)
        print(f"  Ohne Titelblatt: kein cover-Block in content.json")

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
