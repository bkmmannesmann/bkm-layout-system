#!/usr/bin/env python3
"""
BKM Cover Builder – Generiert Titelblätter in allen 5 Varianten.

Verwendung:
    python3 scripts/build_cover.py [variante]
    
    Varianten: mannesmann, fachbetriebe, homeline, proline, anleitung, all
    
Beispiele:
    python3 scripts/build_cover.py fachbetriebe
    python3 scripts/build_cover.py all
"""

import json
import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Projekt-Root ermitteln
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "templates" / "cover"
OUTPUT_DIR = PROJECT_ROOT / "output" / "covers"

# Varianten-Mapping mit Farben
VARIANTS = {
    "mannesmann": {
        "variant_class": "cover--mannesmann",
        "label": "BKM Mannesmann AG",
        "header_bg": "#006837",
        "subline_color": "#8CC63F",
        "chevron_colors": ["#4dae45", "#277c4b", "#1c4b42"],
    },
    "fachbetriebe": {
        "variant_class": "cover--fachbetriebe",
        "label": "Fachbetriebe",
        "header_bg": "#009245",
        "subline_color": "#8CC63F",
        "chevron_colors": ["#4dae45", "#277c4b", "#1c4b42"],
    },
    "homeline": {
        "variant_class": "cover--homeline",
        "label": "BKM Home Line",
        "header_bg": "#006837",
        "subline_color": "#00A99D",
        "chevron_colors": ["#00A99D", "#006837", "#004d29"],
    },
    "proline": {
        "variant_class": "cover--proline",
        "label": "BKM Pro Line",
        "header_bg": "#1c4b42",
        "subline_color": "#4dae45",
        "chevron_colors": ["#009245", "#006837", "#1c4b42"],
    },
    "anleitung": {
        "variant_class": "cover--anleitung",
        "label": "Verarbeitungsanleitung",
        "header_bg": "#4A4A4A",
        "subline_color": "#009245",
        "chevron_colors": ["#009245", "#006837", "#4A4A4A"],
    },
}


def build_cover(variant_key: str, content: dict):
    """Generiert ein Cover-PDF für eine bestimmte Variante."""
    
    variant = VARIANTS[variant_key]
    
    # Jinja2 Template laden
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("cover.html")
    
    # Template-Variablen zusammenführen (inkl. Farben für SVG-Chevrons)
    chevron_colors = variant["chevron_colors"]
    template_vars = {
        "variant_class": variant["variant_class"],
        "header_bg": variant["header_bg"],
        "subline_color": variant["subline_color"],
        "chevron_1_color": chevron_colors[0],
        "chevron_2_color": chevron_colors[1],
        "chevron_3_color": chevron_colors[2],
        "logo_path": content.get("logo_path", "../../assets/images/logos/bkm_logo_white.svg"),
        "headline": content.get("headline", "HEADLINE HIER"),
        "subheadline": content.get("subheadline", "Subheadline hier"),
        "intro_text": content.get("intro_text", "Einleitungstext hier."),
        "hero_image_path": content.get("hero_image_path", "../../assets/images/placeholder/hero.jpg"),
        "hero_image_alt": content.get("hero_image_alt", "Hero-Bild"),
        "title": content.get("title", f"BKM Cover – {variant['label']}"),
    }
    
    # HTML rendern
    html_content = template.render(**template_vars)
    
    # Output-Verzeichnis erstellen
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # HTML speichern (für Preview)
    html_path = OUTPUT_DIR / f"cover_{variant_key}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # PDF generieren mit WeasyPrint
    try:
        from weasyprint import HTML
        pdf_path = OUTPUT_DIR / f"cover_{variant_key}.pdf"
        HTML(string=html_content, base_url=str(TEMPLATE_DIR)).write_pdf(str(pdf_path))
        print(f"  ✓ PDF: {pdf_path}")
    except ImportError:
        print(f"  ⚠ WeasyPrint nicht installiert – nur HTML generiert")
    except Exception as e:
        print(f"  ✗ PDF-Fehler: {e}")
    
    print(f"  ✓ HTML: {html_path}")
    return html_path


def main():
    # Argument: Variante
    variant_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    # Content laden (falls vorhanden)
    content_path = PROJECT_ROOT / "content" / "cover" / "content.json"
    if content_path.exists():
        with open(content_path, "r", encoding="utf-8") as f:
            content = json.load(f)
    else:
        # Standard-Content
        content = {
            "headline": "IHR ZUHAUSE IN SICHEREN HÄNDEN",
            "subheadline": "Feuchte Wände · Ihr Keller wird unbrauchbar?",
            "intro_text": "Mit einem zertifizierten BKM Fachbetrieb erhalten Sie eine fachkundige Einschätzung und Sicherheit für Ihr Zuhause.",
            "hero_image_alt": "BKM Fachbetrieb Beratung",
        }
    
    print("=" * 50)
    print("BKM COVER BUILDER")
    print("=" * 50)
    
    if variant_arg == "all":
        # Alle Varianten generieren
        for key in VARIANTS:
            print(f"\n→ Generiere: {VARIANTS[key]['label']} ({key})")
            build_cover(key, content)
    elif variant_arg in VARIANTS:
        print(f"\n→ Generiere: {VARIANTS[variant_arg]['label']} ({variant_arg})")
        build_cover(variant_arg, content)
    else:
        print(f"Unbekannte Variante: {variant_arg}")
        print(f"Verfügbar: {', '.join(VARIANTS.keys())}, all")
        sys.exit(1)
    
    print(f"\n{'=' * 50}")
    print(f"Fertig! Output in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
