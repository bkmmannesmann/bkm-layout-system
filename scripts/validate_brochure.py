#!/usr/bin/env python3
"""Prueft, dass der Broschuereninnenteil dem Layoutvertrag entspricht.

Zwei Betriebsarten, wie beim Datenblatt getrennt nach Form und Inhalt:

    python3 scripts/validate_brochure.py                          # Layout
    python3 scripts/validate_brochure.py content/<ordner>/content.json  # Inhalt

Die Layoutpruefung schuetzt das Design: sie liest templates/pages/pages-spec.css
und page-template.html und schlaegt an, wenn eine Invariante aus
docs/BROSCHUERE-LAYOUT.md verletzt oder ein bekanntes Antimuster eingebaut
wurde. Die Inhaltspruefung liest eine content.json und prueft Struktur,
Flaechennamen und die Seitenverweise im Inhaltsverzeichnis.

Beide laufen ohne Abhaengigkeiten und sind fuer die CI gedacht. Die Pruefung
des erzeugten PDFs - eingebettete Schriften und Vollstaendigkeit des Textes -
sitzt in build_pages.py, weil sie das gerenderte Dokument braucht.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
CSS_PATH = ROOT_DIR / "templates" / "pages" / "pages-spec.css"
HTML_PATH = ROOT_DIR / "templates" / "pages" / "page-template.html"
VARIABLES_PATH = ROOT_DIR / "design-system" / "variables.css"
FONT_DIR = ROOT_DIR / "assets" / "fonts"

# --------------------------------------------------------------------------
# Vertragswerte. Jede Zeile hier entspricht einer Zeile in
# docs/BROSCHUERE-LAYOUT.md. Wer eine aendert, aendert beide.
# --------------------------------------------------------------------------

# Eingaben: feste Werte, die von Hand gesetzt werden.
RASTER = {
    "--brochure-margin-x": "18.0mm",
    "--brochure-margin-top": "20.4mm",
    "--brochure-gutter": "4.3mm",
    "--brochure-footer-zone": "25.0mm",
}

# Abgeleitete Groessen. Sie duerfen keine eigene Zahl tragen, sondern muessen
# aus den Eingaben gerechnet werden. Frueher standen hier 55.4mm und 174.0mm
# nebeneinander und widersprachen sich: 3 x 55.4 + 2 x 4.3 sind 174.8mm. Der
# Satz stand dadurch 0.8mm ueber der rechten Fluchtlinie. Geprueft wird deshalb
# die Konstruktion, nicht der Zahlenwert - so geht das Raster auch dann auf,
# wenn der Steg spaeter ein anderer ist.
#
# Jede rechnet direkt aus den Eingaben: WeasyPrint loest ein calc() nicht auf,
# wenn darin eine Variable steht, die selbst ein calc() ist - das Ergebnis wird
# 0, die Breite faellt auf auto und der Satz laeuft ueber die volle Blattbreite.
ABGELEITET = {
    "--brochure-col-3": ("--brochure-margin-x",),
    "--brochure-col":   ("--brochure-margin-x", "--brochure-gutter"),
    "--brochure-col-2": ("--brochure-margin-x", "--brochure-gutter"),
}

# Eine abgeleitete Groesse darf nicht auf einer anderen abgeleiteten aufbauen.
VERSCHACHTELUNG_VERBOTEN = set(ABGELEITET)

# Schriftgroessen je Bauteil, in pt.
TYPO = {
    "headline-large": "30pt",
    "headline-section": "18pt",
    "leadline": "9pt",
    "body-text": "9pt",
    "page__footer": "8pt",
    "backcover-imprint": "6pt",
}

# Die sechs benannten Flaechen. Ohne sie kann der Content keine Flaeche waehlen.
SURFACES = ("deep", "transition", "pure", "stone", "sand", "white")

# Aus docs/LAYOUT-CONTRACT.md uebernommen: dieselbe Sperrliste wie beim
# Datenblatt, damit nicht ueber die Broschuere ein Altwert zurueckkommt.
FORBIDDEN_COLOURS = ("#009245", "#006837", "#00a99d", "#8cc63f")

# Toene, die die Vermessung ergeben hat und die auf das Corporate Design
# normiert wurden. Sie duerfen nicht zurueckkommen.
NORMALISED_COLOURS = {
    "#484848": "#494949 (Stone Grey)",
    "#277c4b": "#287d4b (Transition Green)",
    "#d8d8d9": "var(--bkm-rule) (Bildplatzhalter)",
    "#e0e0e0": "var(--bkm-hairline) (Trennlinie)",
}

PAGE_TYPES = ("opener", "content", "feature", "process", "list", "toc", "backcover")
FEATURE_LAYOUTS = ("top-image", "left-image", "right-image")


def strip_css_comments(text: str) -> str:
    """Entfernt /* ... */ - der Dateikopf fuehrt Messwerte als Nachweis."""
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def strip_jinja_comments(text: str) -> str:
    return re.sub(r"\{#.*?#\}", "", text, flags=re.DOTALL)


# --------------------------------------------------------------------------
# Layoutpruefung
# --------------------------------------------------------------------------

def check_layout() -> list[str]:
    errors: list[str] = []

    for path in (CSS_PATH, HTML_PATH, VARIABLES_PATH):
        if not path.exists():
            errors.append(f"Datei fehlt: {path.relative_to(ROOT_DIR)}")
    if errors:
        return errors

    css_raw = CSS_PATH.read_text(encoding="utf-8")
    css = strip_css_comments(css_raw)
    html_raw = HTML_PATH.read_text(encoding="utf-8")
    html = strip_jinja_comments(html_raw)

    # --- Schriftdateien ----------------------------------------------------
    # Der Anlass fuer diese Pruefung: pages-spec.css verwies auf .woff2-Dateien,
    # die es nicht gibt. WeasyPrint meldet das nicht, sondern setzt still eine
    # Ersatzschrift - der Innenteil lief in DejaVu Sans, ohne dass es auffiel.
    referenced = re.findall(r"url\(['\"]([^'\"]+)['\"]\)", css)
    for ref in referenced:
        if ref.endswith(".css"):
            continue
        target = (CSS_PATH.parent / ref).resolve()
        if not target.exists():
            errors.append(
                f"Schriftdatei fehlt: {ref} - WeasyPrint faellt dann still auf "
                f"eine Ersatzschrift zurueck"
            )

    if "@import" not in css or "variables.css" not in css:
        errors.append(
            "pages-spec.css importiert design-system/variables.css nicht - "
            "ohne den Import sind die Farbvariablen nicht definiert"
        )

    # --- Farben ------------------------------------------------------------
    for source, label in ((css, "pages-spec.css"), (html, "page-template.html")):
        for hexv in re.findall(r"#[0-9a-fA-F]{6}", source):
            low = hexv.lower()
            if low in FORBIDDEN_COLOURS:
                errors.append(f"{label}: verbotener Altwert {hexv}")
            elif low in NORMALISED_COLOURS:
                errors.append(
                    f"{label}: {hexv} ist auf {NORMALISED_COLOURS[low]} normiert "
                    f"und darf nicht zurueckkommen"
                )
            else:
                errors.append(
                    f"{label}: Hex-Wert {hexv} - Farben laufen ueber var(--bkm-*)"
                )

    # --- Palette in variables.css -----------------------------------------
    variables = VARIABLES_PATH.read_text(encoding="utf-8")
    for name, value in (
        ("--bkm-deep-green", "#1c4b42"), ("--bkm-transition-green", "#287d4b"),
        ("--bkm-pure-green", "#4daf46"), ("--bkm-lime-green", "#b4e717"),
        ("--bkm-stone-grey", "#494949"), ("--bkm-sand-white", "#f6f5f2"),
        ("--bkm-hairline", "#e3e1dc"), ("--bkm-rule", "#d9d7d3"),
    ):
        if not re.search(rf"{re.escape(name)}\s*:\s*{value}\s*;", variables, re.I):
            errors.append(f"variables.css: {name} ist nicht {value}")

    # --- Raster ------------------------------------------------------------
    for name, value in RASTER.items():
        if not re.search(rf"{re.escape(name)}\s*:\s*{re.escape(value)}\s*;", css):
            errors.append(f"Rastervariable {name} ist nicht {value}")

    for name, zutaten in ABGELEITET.items():
        block = re.search(rf"{re.escape(name)}\s*:\s*([^;]+);", css)
        if block is None:
            errors.append(f"Abgeleitete Groesse {name} fehlt")
            continue
        ausdruck = block.group(1)
        if "calc(" not in ausdruck:
            errors.append(
                f"{name} traegt eine feste Zahl ({ausdruck.strip()}) statt einer "
                f"Rechnung - Spalten- und Satzbreite ergeben sich aus Achse und "
                f"Steg und werden nicht daneben nochmal gesetzt"
            )
            continue
        for zutat in zutaten:
            if zutat not in ausdruck:
                errors.append(f"{name} rechnet nicht mit {zutat}")
        for andere in VERSCHACHTELUNG_VERBOTEN - {name}:
            if andere in ausdruck:
                errors.append(
                    f"{name} rechnet mit {andere}, das selbst ein calc() ist - "
                    f"WeasyPrint loest das nicht auf, die Breite wird 0 und der "
                    f"Satz laeuft ueber die volle Blattbreite"
                )

    # --- Typografie --------------------------------------------------------
    for selector, size in TYPO.items():
        # Am Zeilenanfang verankert, sonst trifft der Ausdruck eine
        # Nachfahrenregel wie ".surface > .page__footer".
        block = re.search(rf"^\.{re.escape(selector)}\s*\{{(.*?)\}}", css,
                          re.DOTALL | re.MULTILINE)
        if block is None:
            errors.append(f"Regel .{selector} fehlt")
        elif f"font-size: {size}" not in block.group(1):
            errors.append(f".{selector}: Schriftgroesse ist nicht {size}")

    if 'hyphenate-character: "-"' not in css:
        errors.append(
            "body-text setzt kein hyphenate-character - TT Norms Pro enthaelt "
            "kein U+2010 und druckt an jeder Trennstelle ein schwarzes Kaestchen"
        )

    # --- Flaechen ----------------------------------------------------------
    for name in SURFACES:
        # Auf die oeffnende Klammer pruefen: ohne sie wuerde ".surface--sand"
        # auch in ".surface--sandstein" treffen und eine geloeschte Regel
        # unbemerkt durchgehen.
        if not re.search(rf"\.surface--{re.escape(name)}\s*\{{", css):
            errors.append(f"Flaechenklasse .surface--{name} fehlt")
    for prop in ("--surface-text", "--surface-hl-large",
                 "--surface-hl-section", "--surface-accent"):
        if css.count(prop) < len(SURFACES):
            errors.append(
                f"{prop} ist nicht in allen sechs Flaechen gesetzt - "
                f"eine Flaeche legt alle vier Rollen fest"
            )

    # --- Antimuster --------------------------------------------------------
    if "lower_top" in html:
        errors.append(
            "page-template.html nutzt lower_top - Baender stehen im Fluss, "
            "eine frei gewaehlte Oberkante hat den Text darueber verdeckt"
        )
    if "feature-band--tail" not in css:
        errors.append(
            "feature-band--tail fehlt - ohne das durchlaufende Band bricht die "
            "Farbflaeche auf halber Hoehe ab und die Fusszeile steht frei"
        )
    if re.search(r"font-size:\s*\d+(\.\d+)?(pt|px)", html):
        errors.append(
            "page-template.html setzt eine Schriftgroesse - Typografie steht "
            "im Stylesheet, nicht im Template"
        )
    for antipattern, reason in (
        ("@import url('https", "Externe Ressource - der Build laeuft offline"),
        ("cdn.", "CDN-Referenz - der Build laeuft offline"),
        ("class=\"ph ", "Icon-Webfont - nur lokale SVGs, siehe LAYOUT-CONTRACT.md"),
    ):
        if antipattern in css or antipattern in html:
            errors.append(f"{antipattern!r}: {reason}")

    # --- Fusszeile ---------------------------------------------------------
    for selector in (".page__footer--verso", ".page__footer--recto",
                     ".page__folio", ".page__runninghead"):
        if selector not in css:
            errors.append(f"Fusszeilenregel {selector} fehlt")
    if "'%02d' % no" not in html_raw:
        errors.append("Seitenzahl ist nicht zweistellig formatiert")

    return errors


# --------------------------------------------------------------------------
# Inhaltspruefung
# --------------------------------------------------------------------------

def check_content(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.name} ist kein gueltiges JSON: {exc}"]

    # Ein Ordner des Innenteil-Systems fuehrt seine Seiten unter 'pages'.
    # content/prospekt-fachbetrieb/ nutzt ein eigenes Template mit eigenem
    # Schema und wird von scripts/build.py gebaut - der gehoert hier nicht
    # geprueft, aber auch nicht stillschweigend uebergangen.
    if "pages" not in data:
        other = (data.get("meta") or {}).get("template")
        print(f"{path} uebersprungen: kein Innenteil-Content"
              + (f" (Template '{other}', zustaendig ist scripts/build.py)" if other else ""))
        raise SystemExit(0)

    if not isinstance(data.get("pages"), list) or not data["pages"]:
        return [f"{path.name}: 'pages' ist leer"]

    start = data.get("page_number_start")
    if start is None:
        errors.append(
            "page_number_start fehlt - ohne den Startwert beginnt die Zaehlung "
            "bei 2, was nur stimmt, wenn das Titelblatt genau eine Seite hat"
        )
    elif not isinstance(start, int) or start < 1:
        errors.append(f"page_number_start ist {start!r}, erwartet eine Zahl ab 1")

    # Kein Farbwert und keine Positionsangabe im Inhalt.
    raw = path.read_text(encoding="utf-8")
    for hexv in set(re.findall(r"#[0-9a-fA-F]{6}", raw)):
        errors.append(
            f"Farbwert {hexv} im Inhalt - Flaechen werden ueber ihren Namen "
            f"gewaehlt: {', '.join(SURFACES)}"
        )
    for field in re.findall(r'"(\w*(?:_bg|_color))"\s*:', raw):
        errors.append(
            f"Feld {field!r} im Inhalt - Farben bestimmt die Flaeche, "
            f"nicht der Inhalt"
        )
    if "lower_top" in raw:
        errors.append("Feld 'lower_top' im Inhalt - Baender stehen im Fluss")
    if re.search(r'"style"\s*:', raw):
        errors.append("Feld 'style' im Inhalt - kein CSS im Content-Ordner")

    # Seitenweise Pruefung; nebenbei die Zuordnung Nummer -> Seite aufbauen,
    # um die Verweise im Inhaltsverzeichnis gegenzupruefen.
    numbers: list[int | None] = []
    for index, page in enumerate(data["pages"]):
        where = f"Seite {index + 1}"
        ptype = page.get("type")
        if ptype not in PAGE_TYPES:
            errors.append(f"{where}: unbekannter Typ {ptype!r}, erlaubt: "
                          f"{', '.join(PAGE_TYPES)}")

        for field in ("upper_surface", "lower_surface", "quote_surface"):
            value = page.get(field)
            if value is not None and value not in SURFACES:
                errors.append(f"{where}: {field}={value!r} ist keine benannte "
                              f"Flaeche ({', '.join(SURFACES)})")

        if ptype == "feature":
            layout = page.get("layout", "top-image")
            if layout not in FEATURE_LAYOUTS:
                errors.append(f"{where}: layout={layout!r}, erlaubt: "
                              f"{', '.join(FEATURE_LAYOUTS)}")

        if ptype == "opener":
            for field in ("headline", "section_headline", "upper_text",
                          "lower_headline", "lower_text"):
                if not page.get(field):
                    errors.append(f"{where}: opener ohne {field}")

        if ptype == "backcover" and not page.get("contact"):
            errors.append(f"{where}: backcover ohne Kontaktblock")

        for field in ("upper_cols", "lower_cols", "columns"):
            value = page.get(field)
            if value is not None and value not in (1, 2, 3):
                errors.append(f"{where}: {field}={value!r}, erlaubt sind 1, 2 oder 3")

        base = start if isinstance(start, int) else 2
        numbers.append(None if page.get("no_folio") else base + index)

    # Verweise im Inhaltsverzeichnis gegen die tatsaechliche Zaehlung pruefen.
    printed = {n for n in numbers if n is not None}
    for index, page in enumerate(data["pages"]):
        if page.get("type") != "toc":
            continue
        for entry in page.get("entries", []):
            raw_page = str(entry.get("page", "")).strip()
            if not raw_page.isdigit():
                errors.append(f"Inhaltsverzeichnis: Eintrag {entry.get('title')!r} "
                              f"hat keine Seitenzahl")
                continue
            if int(raw_page) not in printed:
                errors.append(
                    f"Inhaltsverzeichnis: {entry.get('title')!r} verweist auf "
                    f"Seite {raw_page}, die es nicht gibt oder die keine Ziffer "
                    f"traegt (vorhanden: {min(printed, default=0)}-"
                    f"{max(printed, default=0)})"
                )

    return errors


# --------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if not target.exists():
            print(f"Datei nicht gefunden: {target}")
            return 2
        errors = check_content(target)
        label = f"Inhaltspruefung {target}"
    else:
        errors = check_layout()
        label = "Layoutpruefung Broschuere"

    if errors:
        print(f"{label}: {len(errors)} Verstoss(e)\n")
        for error in errors:
            print(f"  - {error}")
        print(f"\nDie Regeln stehen in docs/BROSCHUERE-LAYOUT.md.")
        return 1

    print(f"{label} bestanden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
