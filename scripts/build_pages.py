#!/usr/bin/env python3
"""
BKM Layout System – Innenseiten Build-Skript
=============================================
Generiert PDF-Broschüren aus HTML-Templates + JSON-Content.
Nutzt Jinja2 für Template-Rendering und WeasyPrint für PDF-Erzeugung.

Verwendung:
    python3 scripts/build_pages.py [template_name]
    python3 scripts/build_pages.py demo          # Generiert eine Demo-Broschüre
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


def build_pages(template_name="page-template", content_file=None, output_name=None):
    """Generiere PDF aus Template + Content."""
    
    # Output-Verzeichnis erstellen
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Jinja2 Environment
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False
    )
    
    template = env.get_template(f"{template_name}.html")
    
    # Content laden (falls vorhanden)
    context = {}
    if content_file and Path(content_file).exists():
        with open(content_file, 'r', encoding='utf-8') as f:
            context = json.load(f)
    
    # Template rendern
    html_content = template.render(**context)
    
    # PDF generieren
    if not output_name:
        output_name = template_name
    
    output_path = OUTPUT_DIR / f"{output_name}.pdf"
    
    HTML(
        string=html_content,
        base_url=str(TEMPLATES_DIR)
    ).write_pdf(str(output_path))
    
    print(f"  ✓ {output_path}")
    return output_path


def build_demo():
    """Generiere eine Demo-Broschüre mit Beispiel-Content."""
    
    demo_content = {
        "title": "BKM Fachbetrieb – Demo-Broschüre",
        
        # Seite 1: Einleitung
        "headline_large": "IHR ZUHAUSE<br>VERDIENT SCHUTZ.",
        "leadline": "Für Eigentümer, die ihr Haus langfristig schützen wollen.",
        "body_text_3col": (
            "Wenn im eigenen Keller Feuchtigkeit auftritt, stehen viele Eigentümer "
            "vor einer schwierigen Entscheidung. Was tun? Wen fragen? Und wie erkennt "
            "man, ob eine Maßnahme wirklich sinnvoll ist? "
            "Hochwertige Materialien sind wichtig. Aber bei Feuchtigkeitsschäden "
            "entscheidet nicht allein das Material über das Ergebnis. Entscheidend ist, "
            "ob die Ursache richtig eingeordnet, die passende Systemlösung gewählt und "
            "die Maßnahme fachgerecht umgesetzt wird. "
            "So entsteht aus Unsicherheit ein nachvollziehbarer Sanierungsprozess. "
            "Sie investieren also nicht nur in eine Abdichtungsmaßnahme. Sie investieren "
            "in Klarheit, Werterhalt und eine fachgerecht geplante Lösung."
        ),
        "quote_text": "Prüfen. Erklären. Empfehlen. Fachgerecht umsetzen. Vorbeugen.",
        
        # Seite 2: Bild-Text-Split
        "split_headline": "Was Sie sehen, ist selten die Ursache",
        "split_lead": "Sichtbare Schäden sind selten das eigentliche Problem.",
        "split_body": (
            "Viele Eigentümer bemerken das Problem erst, wenn es sichtbar wird: "
            "feuchte Wände, Schimmel, abblätternde Farbe. Doch was an der Oberfläche "
            "erscheint, hat meist tiefere Ursachen. Wer nur die sichtbaren Folgen "
            "behandelt, riskiert, dass der Schaden zurückkehrt."
        ),
        "split_headline_2": "Warum spezialisierte BKM Fachbetriebe anders arbeiten",
        "split_lead_2": "Feuchteschäden sind keine Standardbaustelle.",
        "split_body_2": (
            "Bei Feuchtigkeitsschäden reicht es nicht, einfach irgendeine Maßnahme "
            "anzubieten. Entscheidend ist, ob diese Maßnahme zur Ursache, zum "
            "Schadensbild und zum Gebäude passt. Ein spezialisierter BKM Fachbetrieb "
            "arbeitet deshalb systematisch."
        ),
        
        # Seite 3: Prozess + Kontrast
        "process_headline": "DER WEG ZUR<br>RICHTIGEN LÖSUNG",
        "process_lead": "Ein klarer Ablauf schafft Sicherheit.",
        "process_steps": [
            {
                "number": "1",
                "title": "Vor-Ort-Analyse",
                "text": "Der Fachbetrieb nimmt das Schadensbild auf und prüft, welche Ursachen infrage kommen."
            },
            {
                "number": "2",
                "title": "Einschätzung und Empfehlung",
                "text": "Sie erhalten eine verständliche Erklärung, was hinter dem Schaden steckt und welche Maßnahmen sinnvoll erscheinen."
            },
            {
                "number": "3",
                "title": "Fachgerechte Umsetzung",
                "text": "Die ausgewählte Lösung wird passend zum Gebäude umgesetzt. Dabei kommen professionelle BKM Pro Line Systeme zum Einsatz."
            }
        ],
        "process_benefit": {
            "title": "Ihr Vorteil",
            "text": "Sie behalten die Kontrolle, ohne selbst Sanierungsexperte werden zu müssen."
        },
        "contrast_headline": "Woran Sie ein fachlich sauberes Angebot erkennen",
        "contrast_lead": "Ein gutes Angebot erklärt die Entscheidung.",
        "contrast_body": (
            "Bei Feuchtigkeitsschäden reicht eine pauschale Position wie "
            "'Kellerabdichtung' oft nicht aus. Für Eigentümer ist entscheidend, "
            "ob nachvollziehbar wird, warum eine bestimmte Maßnahme empfohlen wird. "
            "Ein fachlich sauberes Angebot sollte deshalb nicht nur beschreiben, "
            "was gemacht wird, sondern auch, worauf diese Empfehlung basiert. "
            "Ihr Fachbetrieb systematisch prüft, Feuchte- oder Wasserbelastung "
            "auf das Gebäude einwirkt. Fachleute sprechen hier von "
            "Wassereinwirkungsklassen."
        ),
        
        # Seite 4: Inhaltsverzeichnis
        "toc_title": "Inhalt",
        "toc_items": [
            {"title": "Ihr Zuhause verdient Schutz", "page": "02", "is_chapter": True},
            {"title": "Was Sie sehen, ist selten die Ursache", "page": "03", "is_chapter": False},
            {"title": "Warum spezialisierte Fachbetriebe anders arbeiten", "page": "04", "is_chapter": False},
            {"title": "Der Weg zur richtigen Lösung", "page": "05", "is_chapter": True},
            {"title": "Woran Sie ein sauberes Angebot erkennen", "page": "06", "is_chapter": False},
            {"title": "Erst prüfen, dann richtig entscheiden", "page": "07", "is_chapter": True},
            {"title": "Was Sie beim Fachbetrieb zusätzlich erhalten", "page": "08", "is_chapter": False},
            {"title": "Ihre kostenlose Schadensanalyse", "page": "09", "is_chapter": False},
        ],
        
        # Seite 5: Rückseite
        "back_headline": "Der sicherste erste Schritt –<br>Ihre kostenlose Schadensanalyse",
        "back_text": (
            "Das größte Risiko bei Feuchtigkeitsschäden ist, nichts zu tun. "
            "Jeder Tag des Zögerns kann den Schaden vergrößern und die Kosten in "
            "die Höhe treiben. Machen Sie den ersten, sicheren Schritt in eine "
            "trockene Zukunft für Ihr Zuhause."
        ),
        "back_cta": "Fordern Sie jetzt Ihre kostenlose und unverbindliche Schadensanalyse durch einen zertifizierten Fachpartner in Ihrer Nähe an.",
        "contact_company": "BKM Mauertrocknungs GmbH",
        "contact_address": "Wideystraße 23<br>59174 Kamen (Germany)",
        "contact_web": "www.bkm-mannesmann.de",
        "contact_email": "info@bkm-mannesmann.de",
        "contact_phone": "+49 (0) 2307-99034-0",
        "imprint": "Ausgegeben am 06/2026 - All rights reserved. Reproduction only with our permission."
    }
    
    # Content als JSON speichern
    demo_content_path = CONTENT_DIR / "demo" / "content.json"
    demo_content_path.parent.mkdir(parents=True, exist_ok=True)
    with open(demo_content_path, 'w', encoding='utf-8') as f:
        json.dump(demo_content, f, ensure_ascii=False, indent=2)
    
    print("Generiere Demo-Broschüre (Innenseiten)...")
    build_pages("page-template", str(demo_content_path), "demo-broschuere")
    print("\nFertig!")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "demo":
            build_demo()
        else:
            # Versuche Content-Datei zu finden
            content_path = CONTENT_DIR / arg / "content.json"
            if content_path.exists():
                print(f"Generiere Broschüre: {arg}...")
                build_pages("page-template", str(content_path), arg)
            else:
                print(f"Fehler: Content-Datei nicht gefunden: {content_path}")
                sys.exit(1)
    else:
        build_demo()


if __name__ == "__main__":
    main()
