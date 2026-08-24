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
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# Pfade
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "pages"
CONTENT_DIR = PROJECT_ROOT / "content"
OUTPUT_DIR = PROJECT_ROOT / "output" / "pages"
ASSETS_DIR = PROJECT_ROOT / "assets"


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

    print(f"  [OK] {output_path}")
    return output_path


def build_demo():
    """Generiert eine Demo-Broschüre basierend auf dem Fachbetrieb-Prospekt."""

    content = {
        "title": "BKM Fachbetrieb - Demo Broschüre",
        "page_number_start": 2,
        "pages": [
            # --- SEITE 2: OPENER ---
            {
                "type": "opener",
                "running_head": "Ihr Zuhause verdient Schutz",
                "upper_bg": "#494949",
                "headline": "IHR ZUHAUSE VERDIENT SCHUTZ.",
                "headline_color": "#4daf46",
                "section_headline": "Für Eigentümer, die ihr Haus langfristig schützen wollen.",
                "section_hl_color": "#ffffff",
                "upper_cols": 3,
                "upper_text": "Wenn im eigenen Keller Feuchtigkeit auftritt, stehen viele Eigentümer vor einer schwierigen Entscheidung. Was tun? Wen fragen? Und wie erkennt man, ob eine Maßnahme wirklich sinnvoll ist? Hochwertige Materialien sind wichtig. Aber bei Feuchtigkeitsschäden entscheidet nicht allein das Material über das Ergebnis. Entscheidend ist, ob die Ursache richtig eingeordnet, die passende Systemlösung gewählt und die Maßnahme fachgerecht umgesetzt wird.",
                "upper_text_color": "#ffffff",
                "lower_bg": "#287d4b",
                "lower_headline": "Was einen BKM Fachbetrieb auszeichnet",
                "lower_hl_color": "#ffffff",
                "lower_leadline": "Prüfen. Erklären. Empfehlen. Fachgerecht umsetzen. Vorbeugen.",
                "lower_lead_color": "#ffffff",
                "lower_cols": 2,
                "lower_text": "Ein BKM Fachbetrieb arbeitet nach einem klaren Prinzip: Zuerst wird die Ursache geprüft. Dann wird erklärt, was hinter dem Schaden steckt. Auf dieser Grundlage wird eine passende Lösung empfohlen und fachgerecht umgesetzt. Dieser Ablauf sorgt dafür, dass keine wichtigen Schritte übersprungen werden. Und dass Sie als Eigentümer jederzeit nachvollziehen können, warum eine bestimmte Maßnahme empfohlen wird.",
                "lower_text_color": "#ffffff"
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
                "image_height": "131.2mm",
                "headline": "Der Ablauf einer BKM Fachbetrieb-Sanierung",
                "leadline": "Von der Analyse bis zur fertigen Abdichtung.",
                "columns": 3,
                "text": "Ein klarer Ablauf schafft Sicherheit. Vom ersten Kontakt bis zur fertigen Abdichtung folgt jeder Schritt einem durchdachten Prozess. Sie erhalten eine verständliche Erklärung, was hinter dem Schaden steckt und welche Maßnahmen sinnvoll erscheinen. Dabei geht es nicht um eine pauschale Lösung, sondern um eine Empfehlung passend zu Ihrem Gebäude.",
                "lower_section": {
                    "headline": "Woran Sie ein fachlich sauberes Angebot erkennen",
                    "columns": 3,
                    "text": "Bei Feuchtigkeitsschäden reicht eine pauschale Position wie Kellerabdichtung oft nicht aus. Für Eigentümer ist entscheidend, ob nachvollziehbar wird, warum eine bestimmte Maßnahme empfohlen wird. Ein fachlich sauberes Angebot sollte deshalb nicht nur beschreiben, was gemacht wird, sondern auch, worauf diese Empfehlung basiert."
                },
                "lower_top": "131.2mm",
                "lower_bg": "#287d4b"
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
                "upper_bg": "#494949",
                "headline": "ERST PRÜFEN DANN RICHTIG ENTSCHEIDEN.",
                "headline_color": "#4daf46",
                "section_headline": "Die richtige Lösung beginnt am Gebäude.",
                "section_hl_color": "#ffffff",
                "upper_cols": 3,
                "upper_text": "Feuchtigkeit am Haus sollte nicht ignoriert werden. Gleichzeitig ist vorschnelles Handeln selten der beste Weg. Der sinnvollste erste Schritt ist eine fachkundige Einschätzung. Ihr BKM Fachbetrieb hilft Ihnen dabei, den Schaden zu verstehen, mögliche Ursachen einzuordnen und eine passende Lösung für Ihr Gebäude zu finden.",
                "upper_text_color": "#ffffff",
                "lower_bg": "#ffffff",
                "lower_headline": "Was Sie beim Fachbetrieb zusätzlich erhalten",
                "lower_hl_color": "#1c4b42",
                "lower_leadline": "Der größte Mehrwert liegt in der Sicherheit Ihrer Entscheidung.",
                "lower_lead_color": "#4daf46",
                "lower_cols": 3,
                "lower_text": "Ein qualitätsbewusster Hausbesitzer möchte nicht einfach irgendetwas machen lassen. Er möchte verstehen, was sinnvoll ist, wofür er investiert und warum eine bestimmte Maßnahme empfohlen wird. Genau dafür ist der Fachbetrieb da. Sie müssen die Ursache nicht selbst erraten. Wir setzen auf Lösungen, die zum Gebäude passen.",
                "lower_text_color": "#494949"
            },

            # --- INHALTSVERZEICHNIS ---
            {
                "type": "toc",
                "no_folio": True,
                "title": "Inhalt",
                "two_columns": False,
                "entries": [
                    {"is_chapter": True, "title": "Ihr Zuhause verdient Schutz", "page": "02"},
                    {"is_chapter": False, "title": "Was einen BKM Fachbetrieb auszeichnet", "page": "02"},
                    {"is_chapter": True, "title": "Ursachen verstehen", "page": "03"},
                    {"is_chapter": False, "title": "Was Sie sehen, ist selten die Ursache", "page": "03"},
                    {"is_chapter": False, "title": "Warum spezialisierte Fachbetriebe anders arbeiten", "page": "03"},
                    {"is_chapter": True, "title": "Der Sanierungsprozess", "page": "04"},
                    {"is_chapter": False, "title": "Ablauf einer BKM Fachbetrieb-Sanierung", "page": "04"},
                    {"is_chapter": False, "title": "Woran Sie ein sauberes Angebot erkennen", "page": "04"},
                    {"is_chapter": True, "title": "Die richtige Entscheidung", "page": "05"},
                    {"is_chapter": False, "title": "Erst prüfen, dann entscheiden", "page": "06"},
                    {"is_chapter": False, "title": "Was Sie zusätzlich erhalten", "page": "06"}
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
    build_brochure(content, "demo-broschuere")
    print("\nFertig!")


def build_from_json(content_name):
    """Generiert eine Broschüre aus einer JSON-Content-Datei."""
    content_path = CONTENT_DIR / content_name / "content.json"
    if not content_path.exists():
        print(f"[FEHLER] Content-Datei nicht gefunden: {content_path}")
        sys.exit(1)

    with open(content_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    return build_brochure(content, content_name)


def main():
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python3 build_pages.py demo              - Demo-Broschüre generieren")
        print("  python3 build_pages.py <content-name>    - Broschüre aus content/<name>/content.json")
        print("  python3 build_pages.py all               - Alle Content-Ordner generieren")
        sys.exit(1)

    target = sys.argv[1]

    if target == "demo":
        build_demo()
    elif target == "all":
        build_demo()
        if CONTENT_DIR.exists():
            for folder in sorted(CONTENT_DIR.iterdir()):
                if folder.is_dir() and (folder / "content.json").exists() and folder.name != "demo":
                    print(f"Generiere: {folder.name}...")
                    build_from_json(folder.name)
    else:
        build_from_json(target)


if __name__ == "__main__":
    main()
