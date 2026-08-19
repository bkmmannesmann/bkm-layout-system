#!/usr/bin/env python3
"""Baut ein BKM-Technisches Datenblatt als PDF.

Beispiele:
  python3 scripts/build_tds.py --content content/tds/content.json
  python3 scripts/build_tds.py --content content/tds/content.json --release
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from weasyprint import HTML

from validate_tds import validate_data

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = ROOT_DIR / "templates" / "tds"
ICON_DIR = TEMPLATE_DIR / "icons"
OUTPUT_DIR = ROOT_DIR / "output"
ICON_COLOR_PATTERN = re.compile(r"--tds-lime:\s*(#[0-9a-fA-F]{3,8})")


def icon_color() -> str:
    """Liest die Icon-Farbe aus der zentralen Markenvariable in template.css."""
    match = ICON_COLOR_PATTERN.search((TEMPLATE_DIR / "template.css").read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("FEHLER: --tds-lime ist in templates/tds/template.css nicht definiert.")
    return match.group(1)


def make_icon_renderer(color: str):
    """Bindet ein Abschnittsicon mit gesetzter Füllfarbe ein.

    WeasyPrint rendert eingebettete SVG mit einer eigenen Engine; die CSS des
    Dokuments und damit auch `currentColor` erreichen den SVG-Baum nicht. Ohne
    gesetztes fill-Attribut zeichnet WeasyPrint die Phosphor-Glyphen schwarz.
    Die Farbe wird deshalb beim Rendern eingesetzt, damit die Icon-Dateien
    unverändert dem Stand aus BRAND-SOURCE.md entsprechen.
    """

    def render_icon(name: str) -> Markup:
        source = ICON_DIR / f"{name}.svg"
        if not source.is_file():
            return Markup("")
        svg = source.read_text(encoding="utf-8")
        return Markup(svg.replace('fill="currentColor"', f'fill="{color}"', 1))

    return render_icon


def page_count(pdf_path: Path) -> int | None:
    """Liest die Seitenanzahl mit dem vorhandenen Poppler-Werkzeug aus."""
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Erstellt ein BKM-Technisches Datenblatt als PDF.")
    parser.add_argument("--content", required=True, help="Pfad zu content.json, relativ zum Repository oder absolut")
    parser.add_argument("--output", help="Ausgabepfad für PDF, relativ zum Repository oder absolut")
    parser.add_argument("--release", action="store_true", help="Erzeugt nur ein freigabefähiges, markerfreies PDF")
    args = parser.parse_args()

    content_path = Path(args.content)
    if not content_path.is_absolute():
        content_path = ROOT_DIR / content_path
    if not content_path.is_file():
        print(f"FEHLER: Content-Datei nicht gefunden: {content_path}")
        return 2

    try:
        data = json.loads(content_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FEHLER: Ungültiges JSON: {error}")
        return 2

    errors, warnings = validate_data(data, release=args.release)
    for warning in warnings:
        print(f"WARNUNG: {warning}")
    if errors:
        for error in errors:
            print(f"FEHLER: {error}")
        print("PDF wurde nicht erzeugt.")
        return 1

    output_path = Path(args.output) if args.output else OUTPUT_DIR / f"{content_path.parent.name}.pdf"
    if not output_path.is_absolute():
        output_path = ROOT_DIR / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(("html", "xml")),
    )
    environment.globals["icon"] = make_icon_renderer(icon_color())
    html = environment.get_template("template.html").render(**data)
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(output_path))

    expected_pages = int(data["page_count"]) + (0 if args.release or not data.get("review") else 1)
    actual_pages = page_count(output_path)
    if actual_pages is None:
        print("WARNUNG: Die Seitenzahl konnte nicht automatisch aus dem PDF gelesen werden.")
    elif actual_pages != expected_pages:
        print(
            f"FEHLER: PDF hat {actual_pages} Seiten; erwartet werden {expected_pages}. "
            "Inhalte oder Umbruch vor der Freigabe prüfen."
        )
        return 3

    mode = "Release" if args.release else "Entwurf"
    print(f"TDS-PDF erstellt ({mode}): {output_path}")
    if actual_pages is not None:
        print(f"Seitenzahl geprüft: {actual_pages}/{expected_pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
