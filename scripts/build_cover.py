#!/usr/bin/env python3
"""
BKM Cover Builder v2.0 – Generiert Titelblätter in allen 5 Varianten.

Grundprinzip:
    - 16:9 Farbkasten (oberer Bereich, 118.1mm hoch)
    - Key Visual + Logo = 1/5 Formatbreite (42mm)
    - Headline immer 2-zeilig, Versalien, Zeile 1 kürzer als Zeile 2
    - Text Weiß auf dunklem BG, Stone Grey auf weißem BG
    - Key Visual als vorgerenderte Bilddatei (NIEMALS Code!)

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

ROOT_DIR = Path(__file__).parent.parent.resolve()
from jinja2 import Environment, FileSystemLoader

# Projekt-Root ermitteln
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "templates" / "cover"
OUTPUT_DIR = PROJECT_ROOT / "output" / "covers"
ASSETS_DIR = PROJECT_ROOT / "assets"

# ============================================================================
# VARIANTEN-DEFINITION
# 
# Jede Variante definiert:
# - Hintergrundfarbe des 16:9-Farbkastens
# - Logo-Variante (Kontrast-Regel)
# - Key Visual Variante (on-dark / on-light)
# - Textfarben (Headline, Subheadline, Fließtext)
# ============================================================================

VARIANTS = {
    "mannesmann": {
        "variant_class": "cover--mannesmann",
        "label": "BKM Mannesmann AG",
        "color_box_bg": "#1c4b42",
        "color_box_name": "Deep Green",
        "logo_file": "bkm-logo-white-puregreen.svg",
        "keyvisual_file": "keyvisual-on-light.png",
        "headline_color": "#ffffff",
        "subheadline_color": "#b4e717",
        "intro_color": "#ffffff",
    },
    "fachbetriebe": {
        "variant_class": "cover--fachbetriebe",
        "label": "Fachbetriebe",
        "color_box_bg": "#287d4b",
        "color_box_name": "Transition Green",
        "logo_file": "bkm-logo-white-puregreen.svg",
        "keyvisual_file": "keyvisual-on-light.png",
        "headline_color": "#ffffff",
        "subheadline_color": "#b4e717",  # Pure Green
        "intro_color": "#ffffff",
        "text_shadow": True,  # Leichter Schatten
    },
    "homeline": {
        "variant_class": "cover--homeline",
        "label": "BKM Home Line",
        "color_box_bg": "#4daf46",
        "color_box_name": "Pure Green",
        "logo_file": "bkm-logo-white.svg",
        "keyvisual_file": "keyvisual-on-light.png",
        "headline_color": "#ffffff",
        "subheadline_color": "#1c4b42",
        "intro_color": "#ffffff",
    },
    "proline": {
        "variant_class": "cover--proline",
        "label": "BKM Pro Line",
        "color_box_bg": "#494949",
        "color_box_name": "Stone Grey",
        "logo_file": "bkm-logo-white-puregreen.svg",
        "keyvisual_file": "keyvisual-on-light.png",
        "headline_color": "#ffffff",
        "subheadline_color": "#4daf46",  # Pure Green
        "intro_color": "#ffffff",
    },
    "anleitung": {
        "variant_class": "cover--anleitung",
        "label": "Verarbeitungsanleitung",
        "color_box_bg": "#ffffff",
        "color_box_name": "Weiß",
        "logo_file": "bkm-logo-stonegrey-puregreen.svg",
        "keyvisual_file": "keyvisual-on-light.png",
        "headline_color": "#494949",
        "subheadline_color": "#4daf46",
        "intro_color": "#494949",
    },
}


def build_cover(variant_key: str, content: dict):
    """Generiert ein Cover-PDF für eine bestimmte Variante."""
    
    variant = VARIANTS[variant_key]
    
    # Jinja2 Template laden
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("cover.html")
    
    # Asset-Pfade relativ zum Template
    # assets/logos/ traegt die schlanken Fassungen: gleiche viewBox, gleiche
    # zwoelf Pfade, byteweise identische Pfaddaten - aber 9 KB statt 517 KB.
    # Der Unterschied war ein metadata-Block mit Illustrators
    # Bearbeitungsspur, fuer die Darstellung wirkungslos.
    logo_path = f"../../assets/logos/{variant['logo_file']}"
    keyvisual_path = f"../../assets/images/{variant['keyvisual_file']}"
    
    # Badge-Pfad (nur für Home Line und Pro Line Produktbroschüren)
    badge_path = ""
    badge_alt = ""
    if variant_key == "homeline":
        badge_path = "../../assets/images/badge-homeline.png"
        badge_alt = "HOME LINE"
    elif variant_key == "proline":
        badge_path = "../../assets/images/badge-proline.png"
        badge_alt = "PRO LINE"
    
    # Template-Variablen zusammenführen
    template_vars = {
        "variant_class": variant["variant_class"],
        "logo_path": logo_path,
        "keyvisual_path": keyvisual_path,
        # Nur die Fachbetriebe-Variante traegt das runde Systempartner-Siegel.
        # Es ersetzt optisch das Logo; das Logo bleibt im Fluss und unsichtbar,
        # damit der Abstand zur Headline unveraendert bleibt.
        "seal_path": ("../../uploads/signatur-bkm-systempartner-logo.png"
                      if variant_key == "fachbetriebe" else ""),
        "badge_path": badge_path,
        "badge_alt": badge_alt,
        "headline": content.get("headline", "HEADLINE HIER\nZWEITE ZEILE"),
        "subheadline": content.get("subheadline", "Subheadline hier"),
        "intro_text": content.get("intro_text", "Einleitungstext hier."),
        "hero_image_path": content.get("hero_image_path", "../../uploads/cover-hero-standard.jpg"),
        "hero_image_alt": content.get("hero_image_alt", "Hero-Bild"),
        "title": content.get("title", f"BKM Cover – {variant['label']}"),
    }
    
    # HTML rendern
    html_content = template.render(**template_vars)
    
    # Inline-CSS für varianten-spezifische Farben injizieren
    # (WeasyPrint unterstützt CSS-Variablen nicht zuverlässig in allen Kontexten)
    # Text-Shadow fuer Fachbetriebe
    shadow_css = ""
    if variant.get("text_shadow"):
        shadow_css = """
      .cover__headline, .cover__subheadline, .cover__intro {
        text-shadow: 0 1px 3px rgba(0,0,0,0.3);
      }
"""
    
    color_overrides = f"""
    <style>
      .cover__color-box {{ background-color: {variant['color_box_bg']}; }}
      .cover__headline {{ color: {variant['headline_color']}; }}
      .cover__subheadline {{ color: {variant['subheadline_color']}; }}
      .cover__intro {{ color: {variant['intro_color']}; }}
      {shadow_css}
    </style>
    """
    html_content = html_content.replace("</head>", f"{color_overrides}\n</head>")
    
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

    fehler = check_output(html_content, pdf_path if "pdf_path" in dir() else None)
    if fehler:
        for f in fehler:
            print(f"  ✗ {f}")
        return None

    return html_path


def check_output(html_content, pdf_path):
    """Prueft das erzeugte Cover auf zwei stille Fehler.

    Erstens tote Bildverweise. Findet WeasyPrint eine Datei nicht, bricht es
    nicht ab, sondern setzt den Alt-Text an ihre Stelle - in einer
    Serifenschrift, die es selbst mitbringt. Genau so liefen alle fuenf Cover
    monatelang: die Vorgabe zeigte auf assets/images/placeholder/hero.jpg,
    einen Ordner, den es nie gab.

    Zweitens die Schriften. Verweist ein Stylesheet auf eine Schriftdatei, die
    fehlt, wird still ersetzt. Dasselbe Muster.

    Die Pfade werden hier geprueft, nicht per Textsuche im Quelltext: sie
    entstehen zur Laufzeit aus variant['logo_file'], eine Suche nach dem
    woertlichen Pfad findet sie nicht.
    """
    import re
    fehler = []

    for ref in sorted(set(re.findall(r'src="\.\./\.\./([^"]+)"', html_content))):
        if not (ROOT_DIR / ref).is_file():
            fehler.append(f"Bildverweis zeigt ins Leere: {ref}")

    if pdf_path and pdf_path.is_file():
        try:
            from pdf_checks import check_fonts
            from pypdf import PdfReader
            fehler.extend(check_fonts(PdfReader(str(pdf_path))))
        except ImportError:
            pass

    return fehler


def main():
    # Argument: Variante
    variant_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    # Variantenspezifischer Content
    VARIANT_CONTENT = {
        "mannesmann": {
            "headline": "IHR ZUHAUSE IN<br>SICHEREN HÄNDEN",
            "subheadline": "Feuchte Wände \u00b7 Ihr Keller wird unbrauchbar?",
            "intro_text": "Mit einem zertifizierten BKM Fachbetrieb erhalten Sie eine fachkundige Einschätzung und Sicherheit für Ihr Zuhause.",
            "hero_image_alt": "BKM Mannesmann AG",
        },
        "fachbetriebe": {
            "headline": "IHR ZUHAUSE IN<br>SICHEREN HÄNDEN",
            "subheadline": "Feuchte Wände \u00b7 Ihr Keller wird unbrauchbar?",
            "intro_text": "Mit einem zertifizierten BKM Fachbetrieb erhalten Sie eine fachkundige Einschätzung und Sicherheit für Ihr Zuhause.",
            "hero_image_alt": "BKM Fachbetrieb Beratung",
        },
        "homeline": {
            "headline": "BKM HOME LINE<br>SELBST SANIEREN",
            "subheadline": "Feuchtigkeitsschutz mit System",
            "intro_text": "F\u00fcr die einfache Anwendung im Heimwerkerbereich optimiert. BKM Systemqualit\u00e4t vom Hersteller \u2013 Made in Germany.",
            "hero_image_alt": "BKM Home Line Produkte",
        },
        "proline": {
            "headline": "BKM PRO LINE<br>FACHGERECHT SANIEREN",
            "subheadline": "Feuchtigkeitsschutz mit System",
            "intro_text": "F\u00fcr professionelle Verarbeitung und komplexe Anwendungen optimiert. BKM Systemqualit\u00e4t vom Hersteller. \u2013 Made in Germany.",
            "hero_image_alt": "BKM Pro Line Produkte",
        },
        "anleitung": {
            "headline": "VERARBEITUNGS-<br>ANLEITUNG",
            "subheadline": "Schritt f\u00fcr Schritt zum Ergebnis",
            "intro_text": "Detaillierte Anweisungen f\u00fcr die fachgerechte Verarbeitung unserer Produkte.",
            "hero_image_alt": "BKM Verarbeitungsanleitung",
        },
    }
    
    # Content laden (falls vorhanden)
    content_path = PROJECT_ROOT / "content" / "cover" / "content.json"
    if content_path.exists():
        with open(content_path, "r", encoding="utf-8") as f:
            content = json.load(f)
    else:
        content = {}
    
    print("=" * 60)
    print("BKM COVER BUILDER v2.0")
    print("=" * 60)
    print(f"Grundraster: 16:9 Farbkasten (118.1mm) + Hero-Bild (178.9mm)")
    print(f"Key Visual + Logo: 1/5 Formatbreite = 42mm")
    print(f"Linker Rand: 18mm")
    print("-" * 60)
    
    if variant_arg == "all":
        for key in VARIANTS:
            v = VARIANTS[key]
            # Variantenspezifischer Content hat Vorrang, dann JSON, dann Fallback
            variant_content = VARIANT_CONTENT.get(key, {})
            merged_content = {**variant_content, **content}  # JSON überschreibt Defaults
            print(f"\n→ {v['label']} ({key}) – BG: {v['color_box_name']}")
            build_cover(key, merged_content)
    elif variant_arg in VARIANTS:
        v = VARIANTS[variant_arg]
        variant_content = VARIANT_CONTENT.get(variant_arg, {})
        merged_content = {**variant_content, **content}
        print(f"\n→ {v['label']} ({variant_arg}) – BG: {v['color_box_name']}")
        build_cover(variant_arg, merged_content)
    else:
        print(f"Unbekannte Variante: {variant_arg}")
        print(f"Verfügbar: {', '.join(VARIANTS.keys())}, all")
        sys.exit(1)
    
    print(f"\n{'=' * 60}")
    print(f"Fertig! Output in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
