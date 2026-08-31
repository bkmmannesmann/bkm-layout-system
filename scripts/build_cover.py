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
        "keyvisual_file": "keyvisual-on-light.svg",
    },
    "fachbetriebe": {
        "variant_class": "cover--fachbetriebe",
        "label": "Fachbetriebe",
        "color_box_bg": "#287d4b",
        "color_box_name": "Transition Green",
        "logo_file": "bkm-logo-white-puregreen.svg",
        "keyvisual_file": "keyvisual-on-light.svg",  # Pure Green
        "text_shadow": True,  # Leichter Schatten
    },
    "homeline": {
        "variant_class": "cover--homeline",
        "label": "BKM Home Line",
        "color_box_bg": "#4daf46",
        "color_box_name": "Pure Green",
        "logo_file": "bkm-logo-white.svg",
        "keyvisual_file": "keyvisual-on-light.svg",
    },
    "proline": {
        "variant_class": "cover--proline",
        "label": "BKM Pro Line",
        "color_box_bg": "#494949",
        "color_box_name": "Stone Grey",
        "logo_file": "bkm-logo-white-puregreen.svg",
        "keyvisual_file": "keyvisual-on-light.svg",  # Pure Green
    },
    "anleitung": {
        "variant_class": "cover--anleitung",
        "label": "Verarbeitungsanleitung",
        "color_box_bg": "#ffffff",
        "color_box_name": "Weiß",
        # Deep Green mit Pure-Green-M, dieselbe Kombination wie im
        # technischen Datenblatt. Seit 31.08.2026 ist das der Standard fuer
        # helle Untergruende: logos.on_light in brand.json. Die
        # Stone-Grey-Fassung ist unter logos.retired gefuehrt.
        "logo_file": "bkm-logo-deepgreen-puregreen.svg",
        "keyvisual_file": "keyvisual-on-light.svg",
    },
}


# Jede Variante traegt ihre eigene Hero-Grafik. Dieselben Dateien nutzt der
# Canvas in templates/brochure/A-Titelblaetter.dc.html.
HERO_GRAPHIC = {
    "mannesmann": "bkm-ag",
    "fachbetriebe": "fachbetrieb",
    "homeline": "home-line",
    "proline": "pro-line",
    "anleitung": "anleitung",
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
    # assets/keyvisual/, nicht assets/images/. Es gab drei Dateien fuer
    # dasselbe Zeichen: die schlanke SVG hier (649 Bytes, saubere Polygone,
    # in brand.json als keyvisual.on_light gefuehrt und im Canvas gesetzt),
    # eine 384-KB-Illustrator-SVG unter assets/images/ und die PNG, die das
    # Cover bis 31.08.2026 benutzte. Cover und Canvas liefen damit auf
    # zwei verschiedene Dateien - dasselbe Muster wie zuvor bei der
    # Hero-Grafik und der Fotolage.
    keyvisual_path = f"../../assets/keyvisual/{variant['keyvisual_file']}"
    
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
        # Die Hero-Grafik ersetzt den frueheren flachen Farbkasten; sie traegt
        # die Eckerweiterung im Alphakanal. Eine je Variante.
        "hero_graphic_path": f"../../uploads/titel-hero-{HERO_GRAPHIC[variant_key]}.png",
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
    
    # Die Textfarben stehen ausschliesslich in cover-spec.css, in den
    # .cover--<variante>-Regeln. Hier standen sie ein zweites Mal und wurden
    # still ueberstimmt: .cover--homeline .cover__subheadline hat die
    # Spezifitaet 0-2-0, die hier eingespeiste Regel nur 0-1-0. Wer den Wert
    # in diesem Skript aenderte, sah im PDF keine Wirkung.
    color_overrides = f"""
    <style>
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

    Drittens die Lage des Titelfotos. brand.json schreibt cover_geometry vor;
    die CSS wiederholt die Zahlen, und eine Abweichung faellt nicht auf, weil
    beide Fassungen fuer sich genommen sauber aussehen. Genau so lief das Foto
    ueber Monate vollflaechig (210 x 297 mm) statt ab 117,46 mm - derselbe
    Titel zeigte auf dem Canvas- und auf dem Produktionsweg einen anderen
    Ausschnitt desselben Motivs. Deshalb wird hier am Ergebnis nachgemessen,
    gegen brand.json, nicht gegen die CSS.

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
        fehler.extend(check_fotolage(pdf_path))
        fehler.extend(check_subheadline(pdf_path))

    return fehler


def check_subheadline(pdf_path):
    """Prueft, dass die Subheadline hoechstens zwei Zeilen laeuft.

    type_scale.cover.subheadline.max_lines in brand.json. Drei Zeilen
    drueckten den Textblock nach unten und liefen bei der
    Verarbeitungsanleitung in die Hero-Kante.

    Erkannt wird sie an 12 pt in Unbounded: der Fliesstext darunter steht
    in derselben Groesse, aber in TT Norms. Ueber die Farbe ginge es
    nicht - die wechselt je Variante.

    Wird die Grenze gerissen, ist der Text zu kuerzen. Nicht die Spalte
    zu verbreitern und nicht die Groesse zu senken: beides steht im
    Vertrag.
    """
    try:
        import pymupdf
    except ImportError:
        return []

    vertrag = json.loads((ROOT_DIR / "brand.json").read_text(encoding="utf-8"))
    grenze = (vertrag.get("type_scale", {}).get("cover", {})
              .get("subheadline", {}).get("max_lines"))
    soll_pt = (vertrag.get("type_scale", {}).get("cover", {})
               .get("subheadline", {}).get("size_pt"))
    if not grenze or not soll_pt:
        return []

    zeilen = []
    with pymupdf.open(str(pdf_path)) as doc:
        for block in doc[0].get_text("dict")["blocks"]:
            for zeile in block.get("lines", []):
                for teil in zeile["spans"]:
                    if (abs(teil["size"] - soll_pt) < 0.3
                            and "Unbounded" in teil["font"]):
                        zeilen.append("".join(x["text"] for x in zeile["spans"]).strip())
                        break

    if len(zeilen) <= grenze:
        return []
    return [f"Subheadline laeuft {len(zeilen)} Zeilen, erlaubt sind {grenze} "
            f"(type_scale.cover.subheadline.max_lines). Text kuerzen, nicht "
            f"die Spalte verbreitern: {zeilen[0][:44]!r} ..."]


def check_fotolage(pdf_path):
    """Misst im fertigen PDF nach, wo Titelfoto und Hero-Grafik sitzen.

    Verglichen wird gegen brand.json, nicht gegen die CSS - sonst prueft die
    Vorgabe sich selbst. Toleranz 0,3 mm: darunter liegt Rundung beim
    Umrechnen von Punkt in Millimeter, darueber ist es eine echte Abweichung.
    """
    try:
        import pymupdf
    except ImportError:
        return []

    geo = json.loads((ROOT_DIR / "brand.json").read_text(encoding="utf-8"))
    geo = geo.get("cover_geometry", {})
    soll_foto = geo.get("photo", {}).get("top_mm")
    soll_hero = geo.get("hero_graphic", {}).get("height_mm")
    if soll_foto is None and soll_hero is None:
        return []

    TOLERANZ = 0.3
    nach_mm = lambda pt: pt / 72 * 25.4
    fehler = []
    with pymupdf.open(str(pdf_path)) as doc:
        breit = [i for i in doc[0].get_image_info()
                 if nach_mm(i["bbox"][2] - i["bbox"][0]) > 100]

    # Die Hero-Grafik wird nicht beschnitten, ihr Rahmen steht so im PDF.
    # Das Foto liegt unter object-fit:cover, sein Rahmen ragt ueber den
    # Beschnitt hinaus - gemessen wird darum die Unterkante, die bei beiden
    # Wegen auf der Blattkante liegen muss.
    if soll_hero is not None:
        treffer = [i for i in breit
                   if abs(nach_mm(i["bbox"][3]) - soll_hero) < 1.0]
        if not treffer:
            unten = ", ".join(f"{nach_mm(i['bbox'][3]):.2f}" for i in breit) or "keine"
            fehler.append(
                f"Hero-Grafik endet nicht bei {soll_hero} mm laut brand.json "
                f"(gemessen: {unten} mm)")

    if soll_foto is not None:
        hoehe = 297.0 - soll_foto
        # Bei object-fit:cover skaliert das Motiv auf die groessere Kante;
        # der Rahmen im PDF ist deshalb um den Faktor Motivseite/Rahmenseite
        # groesser. Geprueft wird die Mitte - sie bleibt unter cover fest.
        mitte_soll = soll_foto + hoehe / 2
        treffer = [i for i in breit
                   if abs((nach_mm(i["bbox"][1]) + nach_mm(i["bbox"][3])) / 2
                          - mitte_soll) < TOLERANZ]
        if not treffer:
            gemessen = ", ".join(
                f"{(nach_mm(i['bbox'][1]) + nach_mm(i['bbox'][3])) / 2:.2f}"
                for i in breit) or "keine"
            fehler.append(
                f"Titelfoto sitzt nicht auf der Achse {mitte_soll:.2f} mm "
                f"(brand.json: ab {soll_foto} mm, {hoehe:.2f} mm hoch) - "
                f"gemessen: {gemessen} mm")

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
    print("Hero-Grafik 210 x 125 mm  |  Foto ab 117,46 mm, 179,54 mm hoch")
    print("Ueberlappung 7,54 mm (Blitzerschutz)  |  Keyvisual 42 mm ab 102,416 mm")
    print("Linker Rand 18 mm")
    print("-" * 60)
    
    # build_cover() gibt bei Beanstandung None zurueck. Das wurde hier nicht
    # ausgewertet: die Befunde standen auf dem Schirm, das Skript endete
    # trotzdem mit 0 und die CI lief durch. Eine Pruefung, die nicht
    # abbricht, ist keine.
    beanstandet = []

    if variant_arg == "all":
        for key in VARIANTS:
            v = VARIANTS[key]
            # Variantenspezifischer Content hat Vorrang, dann JSON, dann Fallback
            variant_content = VARIANT_CONTENT.get(key, {})
            merged_content = {**variant_content, **content}  # JSON überschreibt Defaults
            print(f"\n→ {v['label']} ({key}) – BG: {v['color_box_name']}")
            if build_cover(key, merged_content) is None:
                beanstandet.append(key)
    elif variant_arg in VARIANTS:
        v = VARIANTS[variant_arg]
        variant_content = VARIANT_CONTENT.get(variant_arg, {})
        merged_content = {**variant_content, **content}
        print(f"\n→ {v['label']} ({variant_arg}) – BG: {v['color_box_name']}")
        if build_cover(variant_arg, merged_content) is None:
            beanstandet.append(variant_arg)
    else:
        print(f"Unbekannte Variante: {variant_arg}")
        print(f"Verfügbar: {', '.join(VARIANTS.keys())}, all")
        sys.exit(1)
    
    print(f"\n{'=' * 60}")
    if beanstandet:
        print(f"Beanstandet: {', '.join(beanstandet)} - siehe ✗ oben")
        sys.exit(1)
    print(f"Fertig! Output in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
