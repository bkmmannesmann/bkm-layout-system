#!/usr/bin/env python3
"""
BKM Layout System - Innenseiten Build-Skript
=============================================
Generiert PDF-Broschüren aus JSON-Content-Dateien.
Das Template-System arbeitet mit konkreten Seitentypen:
  - opener: Doppelgeteilte Seite (Farbe oben + Farbe unten)
  - content: Headline + Leadline + Spaltentext (weiß)
  - feature: Bild-Text-Kombination (verschiedene Layouts)
  - process: Nummerierte Prozess-Schritte
  - list: Aufzählung mit Titel/Body-Paaren
  - toc: Inhaltsverzeichnis (1- oder 2-spaltig)
  - backcover: Rückseite mit CTA + Kontakt
"""

import json
import os
import re
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pypdf import PdfReader

from pdf_checks import check_completeness, check_fonts, collect_strings

# Pfadschluessel des Innenteils. Sie stehen als Pfad im Content und nicht als
# Text im PDF.
PAGE_SKIP_KEYS = ("image", "badge", "logo", "keyvisual")

# Rueckgabewert fuer Ordner, die zu einem anderen Template gehoeren:
# kein Fehler, aber auch kein gebautes PDF.
SKIPPED = object()

# Pfade
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "pages"
CONTENT_DIR = PROJECT_ROOT / "content"
OUTPUT_DIR = PROJECT_ROOT / "output" / "pages"
ASSETS_DIR = PROJECT_ROOT / "assets"




def check_output(pdf_path, content_data):
    """Prueft das erzeugte PDF gegen zwei Fehler, die sonst still durchgehen.

    Erstens die eingebetteten Schriften: verweist ein Stylesheet auf eine
    Schriftdatei, die es nicht gibt, meldet WeasyPrint das nicht, sondern
    setzt eine Ersatzschrift. Der Innenteil lief so zeitweise in DejaVu Sans.

    Zweitens die Vollstaendigkeit: laeuft ein Text ueber seinen Bereich
    hinaus, schneidet ihn overflow:hidden ab. Das PDF sieht heil aus, es
    fehlt nur der Schluss des Absatzes.
    """
    reader = PdfReader(str(pdf_path))
    errors = check_fonts(reader)

    # Nur die Seiten: der Dokumenttitel steht im <title> und damit nicht im
    # sichtbaren Text, page_number_start ist eine Zahl.
    errors.extend(check_completeness(
        reader, collect_strings(content_data.get("pages", []), skip_keys=PAGE_SKIP_KEYS)))

    errors.extend(_check_type_area(reader))
    errors.extend(_check_right_edge(pdf_path))
    return errors


# Satzspiegel in mm, aus docs/BROSCHUERE-LAYOUT.md. Ausserhalb dieser Grenzen
# darf keine Grundlinie liegen - dort schneidet der Beschnitt, oder der Text
# laeuft in die Fusszeile.
MARGIN_X = 18.0
PAGE_W = 210.0
PAGE_H = 297.0
FOOTER_ZONE = 23.5                    # Fusssteg, siehe --brochure-footer-zone
CONTENT_BOTTOM = PAGE_H - FOOTER_ZONE # 272.0mm, tiefste Grundlinie fuer Satz
FOOTER_BASELINE = PAGE_H - MARGIN_X   # 279.0mm, Grundlinie der Seitenzahl
TOLERANCE = 0.6                       # Rundung der Textmatrix
FOOTER_TOLERANCE = 1.5                # Spielraum um die Fusszeilen-Grundlinie
BLEED_SAFE = 285.0                    # Grenze auf Seiten ohne Fusszeile
# Hauptheadline. Der Layoutvertrag nennt 30pt; im PDF steht die Groesse in
# CSS-Pixeln, weil WeasyPrint so rechnet - 30 * 96/72 = 40.
HEADLINE_SIZE = 30.0 * 96 / 72
BODY_PT = 9.0                         # Fliesstext und Leadline, in Punkt
# Spielraum fuer den Glyphenueberhang. Die Textbox eines Spans reicht ueber die
# Satzkante hinaus, weil sie die Vorschubbreite misst und nicht die Schwaerze.
# Gemessen an beiden Broschueren: bei sauberem Raster enden die Woerter zwischen
# 192.00 und 192.38mm, beim frueheren 0.8mm-Fehler zwischen 192.26 und 193.12mm.
# 0.5mm trennt die beiden Faelle; enger gefasst meldet die Pruefung den Ueberhang
# als Fehler, weiter gefasst laesst sie den Rasterfehler durch.
EDGE_TOLERANCE = 0.5


def _check_right_edge(pdf_path):
    """Prueft die rechte Satzkante.

    _check_type_area unten sieht nur, wo eine Zeile anfaengt - deshalb ist ihr
    entgangen, dass die dritte Spalte 0.8mm ueber die rechte Fluchtlinie
    stand. Dafuer braucht es die Breite jeder Textbox, und die liefert pypdf
    nicht. pymupdf ist eine reine Pruefabhaengigkeit; fehlt es, wird die
    Pruefung uebersprungen statt den Build zu blockieren.
    """
    try:
        import pymupdf
    except ImportError:
        return []

    errors = []
    pt_per_mm = 72 / 25.4
    right = PAGE_W - MARGIN_X

    with pymupdf.open(str(pdf_path)) as doc:
        for index, page in enumerate(doc, start=1):
            weitest = None
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        # Nur Fliesstext und Leadline; Headlines duerfen
                        # gestalterisch anders stehen.
                        if abs(span["size"] - BODY_PT) > 0.3:
                            continue
                        x1 = span["bbox"][2] / pt_per_mm
                        if weitest is None or x1 > weitest[0]:
                            weitest = (x1, span["text"].strip()[:40])
            if weitest and weitest[0] > right + EDGE_TOLERANCE:
                errors.append(
                    f"Seite {index}: Satz endet bei {weitest[0]:.2f}mm, die rechte "
                    f"Fluchtlinie liegt bei {right:.0f}mm: {weitest[1]!r}"
                )
    return errors


def _check_type_area(reader):
    """Prueft, dass keine Grundlinie ausserhalb des Satzspiegels liegt.

    Der Vollstaendigkeitsvergleich oben findet abgeschnittenen Text nicht:
    overflow:hidden beschneidet nur die Darstellung, im Textlayer steht der
    Absatz weiterhin vollstaendig. Sichtbar wird der Fehler erst an der
    Position - Text unterhalb der Fusszeilen-Grundlinie oder jenseits der
    seitlichen Fluchtlinie ist im gedruckten Heft weg oder unleserlich.
    """
    errors = []
    for index, page in enumerate(reader.pages, start=1):
        lines = []
        sized = []

        def visit(text, cm, tm, font_dict, font_size):
            if not text.strip():
                return
            # Die Textmatrix allein ist nicht die Seitenposition; sie gilt im
            # Raum, den die aktuelle Transformationsmatrix aufspannt. Beide
            # multiplizieren, sonst kommen Werte wie x=251mm auf einem
            # 210mm breiten Blatt heraus.
            x_pt = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y_pt = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            x_mm = x_pt / 72 * 25.4
            y_mm = PAGE_H - y_pt / 72 * 25.4
            lines.append((x_mm, y_mm, text.strip()[:40]))
            # font_size kommt in Textraumeinheiten; die Skalierung der
            # Textmatrix macht daraus die gesetzte Groesse in pt.
            sized.append((x_mm, y_mm, font_size * abs(tm[3] or 1), text.strip()[:40]))

        page.extract_text(visitor_text=visit)

        # Traegt die Seite eine Fusszeile, gehoert ihr der Fusssteg allein und
        # der Satz endet bei CONTENT_BOTTOM. Rueckseite und Inhaltsverzeichnis
        # tragen keine Ziffer; dort ist nur der Beschnitt die Grenze - das
        # Impressum steht laut Vermessung tiefer als jeder Fusssteg.
        has_footer = any(abs(y - FOOTER_BASELINE) <= FOOTER_TOLERANCE
                         for _, y, _ in lines)
        bottom = CONTENT_BOTTOM if has_footer else BLEED_SAFE

        outside = []
        for x_mm, y_mm, snippet in lines:
            in_footer = has_footer and abs(y_mm - FOOTER_BASELINE) <= FOOTER_TOLERANCE
            if y_mm > bottom + TOLERANCE and not in_footer:
                outside.append((snippet, f"Grundlinie {y_mm:.1f}mm, "
                                         f"erlaubt bis {bottom:.0f}mm"))
            elif x_mm < MARGIN_X - TOLERANCE or x_mm > PAGE_W - MARGIN_X + TOLERANCE:
                outside.append((snippet, f"x={x_mm:.1f}mm"))

        for snippet, where in outside[:3]:
            errors.append(
                f"Seite {index}: Text ausserhalb des Satzspiegels ({where}): {snippet!r}"
            )
        if len(outside) > 3:
            errors.append(f"Seite {index}: {len(outside) - 3} weitere Stellen")

        # Die Hauptheadline steht in 30pt und darf hoechstens zwei Zeilen
        # laufen - dieselbe Regel wie auf dem Titelblatt. Drei Zeilen
        # drueckt den Text darunter aus dem Raster.
        baselines = {round(y, 1) for x, y, size, _ in sized
                     if abs(size - HEADLINE_SIZE) < 0.5}
        if len(baselines) > 2:
            errors.append(
                f"Seite {index}: Hauptheadline laeuft {len(baselines)}-zeilig, "
                f"erlaubt sind hoechstens zwei Zeilen"
            )

    return errors


def build_brochure(content_data, output_name):
    """Generiert eine PDF-Broschüre aus Content-Daten."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False
    )
    template = env.get_template("page-template.html")

    html_content = template.render(**content_data)

    output_path = OUTPUT_DIR / f"{output_name}.pdf"
    HTML(
        string=html_content,
        base_url=str(TEMPLATES_DIR)
    ).write_pdf(str(output_path))

    errors = check_output(output_path, content_data)
    if errors:
        print(f"  [FEHLER] {output_path}")
        for error in errors:
            print(f"    - {error}")
        print("    Die Regeln stehen in docs/BROSCHUERE-LAYOUT.md.")
        return None

    print(f"  [OK] {output_path}")
    return output_path


def build_demo():
    """Generiert eine Demo-Broschüre basierend auf dem Fachbetrieb-Prospekt."""

    content = {
        "title": "BKM Fachbetrieb - Demo Broschüre",
        "sender": "fachbetrieb",
        "page_number_start": 1,
        "pages": [
            # --- SEITE 2: OPENER ---
            {
                "type": "opener",
                "running_head": "Ihr Zuhause verdient Schutz",
                "upper_surface": "stone",
                "headline": "IHR ZUHAUSE VERDIENT SCHUTZ.",
                "section_headline": "Für Eigentümer, die ihr Haus langfristig schützen wollen.",
                "upper_cols": 3,
                "upper_text": "Wenn im eigenen Keller Feuchtigkeit auftritt, stehen viele Eigentümer vor einer schwierigen Entscheidung. Was tun? Wen fragen? Und wie erkennt man, ob eine Maßnahme wirklich sinnvoll ist? Hochwertige Materialien sind wichtig. Aber bei Feuchtigkeitsschäden entscheidet nicht allein das Material über das Ergebnis. Entscheidend ist, ob die Ursache richtig eingeordnet, die passende Systemlösung gewählt und die Maßnahme fachgerecht umgesetzt wird.",
                "lower_surface": "transition",
                "lower_headline": "Was einen BKM Fachbetrieb auszeichnet",
                "lower_leadline": "Prüfen. Erklären. Empfehlen. Fachgerecht umsetzen. Vorbeugen.",
                "lower_cols": 2,
                "lower_text": "Ein BKM Fachbetrieb arbeitet nach einem klaren Prinzip: Zuerst wird die Ursache geprüft. Dann wird erklärt, was hinter dem Schaden steckt. Auf dieser Grundlage wird eine passende Lösung empfohlen und fachgerecht umgesetzt. Dieser Ablauf sorgt dafür, dass keine wichtigen Schritte übersprungen werden. Und dass Sie als Eigentümer jederzeit nachvollziehen können, warum eine bestimmte Maßnahme empfohlen wird."
            },

            # --- SEITE 3: CONTENT (3-Spalten, 2 Sektionen) ---
            {
                "type": "content",
                "running_head": "Ursachen verstehen",
                "headline_section": "Was Sie sehen, ist selten die Ursache",
                "columns": 3,
                "col_content": [
                    "Viele Eigentümer bemerken das Problem erst, wenn es sichtbar wird: feuchte Wände, Schimmel, abblätternde Farbe. Doch was an der Oberfläche erscheint, hat meist tiefere Ursachen.",
                    "Wer nur die sichtbaren Folgen behandelt, riskiert, dass der Schaden zurückkehrt. Ein spezialisierter BKM Fachbetrieb arbeitet deshalb systematisch.",
                    "Die Analyse beginnt nicht an der Wand, sondern am Gebäude: Wie ist es gebaut? Welche Wasserbelastung wirkt ein? Erst dann lässt sich eine passende Lösung finden."
                ],
                "section2": {
                    "headline": "Warum spezialisierte BKM Fachbetriebe anders arbeiten",
                    "leadline": "Feuchteschäden sind keine Standardbaustelle.",
                    "columns": 3,
                    "col_content": [
                        "Bei Feuchtigkeitsschäden reicht es nicht, einfach irgendeine Maßnahme anzubieten. Entscheidend ist, ob diese Maßnahme zur Ursache, zum Schadensbild und zum Gebäude passt.",
                        "Ein spezialisierter BKM Fachbetrieb arbeitet deshalb systematisch: Erst prüfen, dann erklären, dann empfehlen. So entsteht aus Unsicherheit ein nachvollziehbarer Sanierungsprozess.",
                        "Sie investieren in Klarheit, Werterhalt und eine fachgerecht geplante Lösung. Nicht in eine pauschale Maßnahme, die vielleicht gar nicht zum Problem passt."
                    ]
                }
            },

            # --- SEITE 4: FEATURE (Bild oben + grüner Block unten) ---
            {
                "type": "feature",
                "running_head": "Der Sanierungsprozess",
                "layout": "top-image",
                "image_height": "110.0mm",
                "headline": "Der Ablauf einer BKM Fachbetrieb-Sanierung",
                "leadline": "Von der Analyse bis zur fertigen Abdichtung.",
                "columns": 3,
                "text": "Ein klarer Ablauf schafft Sicherheit. Vom ersten Kontakt bis zur fertigen Abdichtung folgt jeder Schritt einem durchdachten Prozess. Sie erhalten eine verständliche Erklärung, was hinter dem Schaden steckt und welche Maßnahmen sinnvoll erscheinen. Dabei geht es nicht um eine pauschale Lösung, sondern um eine Empfehlung passend zu Ihrem Gebäude.",
                "lower_section": {
                    "headline": "Woran Sie ein fachlich sauberes Angebot erkennen",
                    "columns": 3,
                    "text": "Bei Feuchtigkeitsschäden reicht eine pauschale Position wie Kellerabdichtung oft nicht aus. Für Eigentümer ist entscheidend, ob nachvollziehbar wird, warum eine bestimmte Maßnahme empfohlen wird. Ein fachlich sauberes Angebot sollte deshalb nicht nur beschreiben, was gemacht wird, sondern auch, worauf diese Empfehlung basiert."
                },
                "lower_surface": "transition"
            },

            # --- SEITE 5: CONTENT (Große HL + 3-Spalten) ---
            {
                "type": "content",
                "running_head": "Der Weg zur richtigen Lösung",
                "headline_large": "DER WEG ZUR RICHTIGEN LÖSUNG",
                "headline_section": "Ein klarer Ablauf schafft Sicherheit.",
                "leadline": "Fünf Schritte für eine nachhaltige Sanierung.",
                "columns": 3,
                "col_content": [
                    "Schritt 1: Erstgespräch und Bestandsaufnahme. Sie schildern das Problem, wir hören zu. Gemeinsam verschaffen wir uns einen ersten Überblick über die Situation an Ihrem Gebäude.",
                    "Schritt 2: Fachkundige Analyse vor Ort. Ein spezialisierter Techniker prüft das Gebäude systematisch. Dabei werden Schadensbilder dokumentiert und mögliche Ursachen eingegrenzt.",
                    "Schritt 3: Individuelle Empfehlung. Auf Basis der Analyse erhalten Sie eine verständliche Erklärung und eine passende Systemlösung für Ihr Gebäude."
                ]
            },

            # --- SEITE 6: OPENER (Dunkel + Hell) ---
            {
                "type": "opener",
                "running_head": "Die richtige Entscheidung",
                "upper_surface": "stone",
                "headline": "ERST PRÜFEN DANN RICHTIG ENTSCHEIDEN.",
                "section_headline": "Die richtige Lösung beginnt am Gebäude.",
                "upper_cols": 3,
                "upper_text": "Feuchtigkeit am Haus sollte nicht ignoriert werden. Gleichzeitig ist vorschnelles Handeln selten der beste Weg. Der sinnvollste erste Schritt ist eine fachkundige Einschätzung. Ihr BKM Fachbetrieb hilft Ihnen dabei, den Schaden zu verstehen, mögliche Ursachen einzuordnen und eine passende Lösung für Ihr Gebäude zu finden.",
                "lower_surface": "white",
                "lower_headline": "Was Sie beim Fachbetrieb zusätzlich erhalten",
                "lower_leadline": "Der größte Mehrwert liegt in der Sicherheit Ihrer Entscheidung.",
                "lower_cols": 3,
                "lower_text": "Ein qualitätsbewusster Hausbesitzer möchte nicht einfach irgendetwas machen lassen. Er möchte verstehen, was sinnvoll ist, wofür er investiert und warum eine bestimmte Maßnahme empfohlen wird. Genau dafür ist der Fachbetrieb da. Sie müssen die Ursache nicht selbst erraten. Wir setzen auf Lösungen, die zum Gebäude passen."
            },

            # --- INHALTSVERZEICHNIS ---
            {
                "type": "toc",
                "no_folio": True,
                "title": "Inhalt",
                "two_columns": False,
                "entries": [
                    {"is_chapter": True, "title": "Ihr Zuhause verdient Schutz", "page": "01"},
                    {"is_chapter": False, "title": "Was einen BKM Fachbetrieb auszeichnet", "page": "01"},
                    {"is_chapter": True, "title": "Ursachen verstehen", "page": "02"},
                    {"is_chapter": False, "title": "Was Sie sehen, ist selten die Ursache", "page": "02"},
                    {"is_chapter": False, "title": "Warum spezialisierte Fachbetriebe anders arbeiten", "page": "02"},
                    {"is_chapter": True, "title": "Der Sanierungsprozess", "page": "03"},
                    {"is_chapter": False, "title": "Ablauf einer BKM Fachbetrieb-Sanierung", "page": "03"},
                    {"is_chapter": False, "title": "Woran Sie ein sauberes Angebot erkennen", "page": "03"},
                    {"is_chapter": True, "title": "Die richtige Entscheidung", "page": "04"},
                    {"is_chapter": False, "title": "Erst prüfen, dann entscheiden", "page": "05"},
                    {"is_chapter": False, "title": "Was Sie zusätzlich erhalten", "page": "05"}
                ]
            },

            # --- RÜCKSEITE ---
            {
                "type": "backcover",
                "no_folio": True,
                "cta_headline": "Der sicherste erste Schritt \u2013 Ihre kostenlose Schadensanalyse",
                "cta_body": "Das größte Risiko bei Feuchtigkeitsschäden ist, nichts zu tun. Jeder Tag des Zögerns kann den Schaden vergrößern und die Kosten in die Höhe treiben. Machen Sie den ersten, sicheren Schritt in eine trockene Zukunft für Ihr Zuhause.",
                "cta_action": "Fordern Sie jetzt Ihre kostenlose und unverbindliche Schadensanalyse durch einen zertifizierten Fachpartner in Ihrer Nähe an.",
                "contact": {
                    "company": "BKM Mannesmann AG",
                    "street": "Wideystraße 23",
                    "city": "59174 Kamen (Germany)",
                    "web": "www.bkm-mannesmann.de",
                    "email": "info@bkm-mannesmann.de",
                    "phone": "+49 (0) 2307-99034-0"
                },
                "imprint": "Ausgegeben am 06/2026 - All rights reserved."
            }
        ]
    }

    # Content als JSON speichern
    demo_content_path = CONTENT_DIR / "demo" / "content.json"
    demo_content_path.parent.mkdir(parents=True, exist_ok=True)
    with open(demo_content_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print("Generiere Demo-Broschüre (seitentyp-basiert)...")
    result = build_brochure(content, "demo-broschuere")
    print("\nFertig!" if result else "\nAbgebrochen: die Ausgabepruefung hat Verstoesse gemeldet.")
    return result


def build_from_json(content_name):
    """Generiert eine Broschüre aus einer JSON-Content-Datei."""
    content_path = CONTENT_DIR / content_name / "content.json"
    if not content_path.exists():
        print(f"[FEHLER] Content-Datei nicht gefunden: {content_path}")
        sys.exit(1)

    with open(content_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    # Die Datenblatt-Ordner fuehren keine 'pages' - fuer sie ist build_tds.py
    # zustaendig.
    if "pages" not in content:
        print(f"  [UEBERSPRUNGEN] {content_name}: kein Innenteil-Content "
              f"(Datenblatt? dann build_tds.py)")
        return SKIPPED

    return build_brochure(content, content_name)


def main():
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python3 build_pages.py demo              - Demo-Broschüre generieren")
        print("  python3 build_pages.py <content-name>    - Broschüre aus content/<name>/content.json")
        print("  python3 build_pages.py all               - Alle Content-Ordner generieren")
        sys.exit(1)

    target = sys.argv[1]

    # Ein Verstoss in der Ausgabepruefung muss sich im Exit-Code zeigen, sonst
    # laeuft die CI gruen ueber ein fehlerhaftes PDF hinweg.
    ok = True
    if target == "demo":
        ok = build_demo() is not None
    elif target == "all":
        ok = build_demo() is not None
        if CONTENT_DIR.exists():
            for folder in sorted(CONTENT_DIR.iterdir()):
                if not folder.is_dir() or folder.name == "demo":
                    continue
                if folder.name.startswith("tds"):
                    continue  # Datenblaetter baut build_tds.py
                if (folder / "content.json").exists():
                    print(f"Generiere: {folder.name}...")
                    result = build_from_json(folder.name)
                    ok = (result is not None) and ok
    else:
        ok = build_from_json(target) is not None

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
