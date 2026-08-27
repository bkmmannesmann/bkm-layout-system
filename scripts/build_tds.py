#!/usr/bin/env python3
"""Baut ein BKM-Technisches Datenblatt als PDF.

Beispiele:
  python3 scripts/build_tds.py --content content/tds/content.json
  python3 scripts/build_tds.py --content content/tds/content.json --release
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pypdf import PdfReader
from weasyprint import HTML

from pdf_checks import (
    TDS_SKIP_KEYS,
    check_completeness,
    check_fonts,
    collect_strings,
)
from validate_tds import validate_data

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = ROOT_DIR / "templates" / "tds"
OUTPUT_DIR = ROOT_DIR / "output"


# Der Inhalt wird ab dieser Laenge gegen das PDF verglichen. Niedrig, weil der
# Inhalt eines Datenblatts gerade in kurzen Tabellenzeilen steckt - genau die,
# die beim Beschnitt verschwinden. An allen vorliegenden Datenblaettern gibt es
# bis hinunter zu dieser Laenge keine Falschmeldung.
MIN_TEXT_LENGTH = 3


def check_output(pdf_path: Path, data: dict, release: bool) -> list[str]:
    """Prueft das erzeugte PDF auf stille Fehler.

    Die Seitenzahlpruefung unten findet abgeschnittenen Inhalt nicht: die Seiten
    haben eine feste Hoehe und overflow:hidden, ein zu langer Block erzeugt also
    keinen Umbruch, sondern verschwindet. Die Seitenzahl bleibt dabei richtig.
    """
    reader = PdfReader(str(pdf_path))
    # Im Release wird der Review-Block nicht gesetzt; seine Texte fehlen dann
    # zu Recht im PDF.
    skip = TDS_SKIP_KEYS + ("review",) if release else TDS_SKIP_KEYS
    strings = collect_strings(data, min_length=MIN_TEXT_LENGTH, skip_keys=skip)
    return check_fonts(reader) + check_completeness(reader, strings)


def page_count(pdf_path: Path) -> int | None:
    """Liest die Seitenanzahl aus dem PDF."""
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


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
    html = environment.get_template("template.html").render(**data)
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(output_path))

    output_errors = check_output(output_path, data, args.release)
    if output_errors:
        for error in output_errors:
            print(f"FEHLER: {error}")
        print("PDF wurde erzeugt, ist aber nicht freigabefaehig.")
        return 4

    review_pages = 0 if args.release or not data.get("review") else int(data.get("review_page_count", 1))
    expected_pages = int(data["page_count"]) + review_pages
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
