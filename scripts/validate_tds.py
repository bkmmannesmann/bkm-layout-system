#!/usr/bin/env python3
"""Validiert TDS-Content gegen den BKM-Redaktionsstandard.

Ohne --release werden Entwurfsdaten geprüft. Mit --release blockieren offene
Marker, interne Prüfblöcke, fehlende Produktionsassets und fehlende
Markenschriften die PDF-Erzeugung.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = ROOT_DIR / "templates" / "tds"
FONT_DIR = ROOT_DIR / "assets" / "fonts"
MARKER_PATTERN = re.compile(r"\[(?:ANGABE FEHLT|ZU PRÜFEN):[^\]]+\]")
REQUIRED_FONTS = ("TT_Norms_Pro_Regular.ttf", "TT_Norms_Pro_Bold.ttf", "Unbounded-Black.ttf")
LEGACY_FIELDS = ("revision", "issue_date", "packaging_image")
REQUIRED_FIELDS = (
    "title", "product_name", "product_subtitle", "product_short", "product_line",
    "created_date", "page_count", "logo", "keyvisual", "line_badge",
    "product_image", "description", "advantages", "properties",
    "technical_data_page1", "technical_data_page2", "applications",
    "manual_reference", "notes", "sds_reference", "packaging", "storage",
    "disposal", "legal", "final_note",
)
REQUIRED_ASSETS = ("logo", "keyvisual", "line_badge", "product_image")
EXPECTED_BADGES = {
    "HOME LINE": "badge-homeline.png",
    "PRO LINE": "badge-proline.png",
}


def walk_strings(value: Any) -> list[str]:
    """Liefert rekursiv alle Textwerte eines JSON-Objekts."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in walk_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in walk_strings(item)]
    return []


def asset_path(asset_reference: str) -> Path:
    """Löst einen im TDS-HTML verwendeten relativen Asset-Pfad auf."""
    return (TEMPLATE_DIR / asset_reference).resolve()


def validate_data(data: dict[str, Any], release: bool = False) -> tuple[list[str], list[str]]:
    """Prüft Content und gibt (Fehler, Warnungen) zurück."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in data or data[field] in (None, ""):
            errors.append(f"Pflichtfeld fehlt oder ist leer: {field}")

    for legacy_field in LEGACY_FIELDS:
        if legacy_field in data:
            errors.append(
                f"{legacy_field} ist kein Feld des TDS-Datenvertrags; bitte entfernen. "
                "Das Datum im Kopf ist created_date, eine Revisionsnummer wird nicht geführt."
            )

    if errors:
        return errors, warnings

    if data["product_line"] not in EXPECTED_BADGES:
        errors.append("product_line muss exakt 'HOME LINE' oder 'PRO LINE' sein.")
    else:
        expected_badge = EXPECTED_BADGES[data["product_line"]]
        if not str(data["line_badge"]).endswith(expected_badge):
            errors.append(
                f"line_badge passt nicht zu {data['product_line']}; erwartet wird {expected_badge}."
            )
        if "novu" in str(data["product_name"]).lower() and data["product_line"] != "HOME LINE":
            errors.append("Produkte mit dem Namensbestandteil Novu gehören zur HOME LINE.")

    if not isinstance(data["page_count"], int) or not 2 <= data["page_count"] <= 6:
        errors.append(
            "page_count muss die Zahl der veroeffentlichten Seiten nennen (2 bis 6). "
            "Drei ist der Regelfall; der interne Pruefteil zaehlt nicht mit."
        )

    try:
        datetime.strptime(str(data["created_date"]), "%d.%m.%Y")
    except ValueError:
        errors.append("created_date muss das Format TT.MM.JJJJ haben.")

    if len(str(data["description"])) > 360:
        errors.append("description überschreitet die zulässigen 360 Zeichen.")

    if "notes_on_page3" in data and not isinstance(data["notes_on_page3"], bool):
        errors.append("notes_on_page3 muss true oder false sein.")

    for field, lower, upper in (("advantages", 5, 7), ("properties", 5, 7)):
        values = data[field]
        if not isinstance(values, list) or not lower <= len(values) <= upper:
            errors.append(f"{field} muss zwischen {lower} und {upper} Einträge enthalten.")
        elif any(not isinstance(item, str) or not item.strip() for item in values):
            errors.append(f"{field} darf keine leeren Einträge enthalten.")

    for table_name in ("technical_data_page1", "technical_data_page2"):
        rows = data[table_name]
        if not isinstance(rows, list) or not rows:
            errors.append(f"{table_name} muss mindestens eine Datenzeile enthalten.")
            continue
        for position, row in enumerate(rows, start=1):
            if not isinstance(row, dict) or not str(row.get("parameter", "")).strip() or not str(row.get("value", "")).strip():
                errors.append(f"{table_name}, Zeile {position}: parameter und value sind Pflicht.")

    for table_name in ("matrix", "format_table"):
        table = data.get(table_name)
        if table:
            if not isinstance(table, dict) or not table.get("title") or not table.get("columns") or not table.get("rows"):
                errors.append(f"{table_name} muss title, columns und rows enthalten.")
            elif any(not isinstance(row, list) or len(row) != len(table["columns"]) for row in table["rows"]):
                errors.append(f"Jede Zeile von {table_name} muss genau so viele Werte wie columns enthalten.")

    if not isinstance(data["packaging"], list):
        errors.append("packaging muss eine Liste sein; bei fehlenden Gebinden nutze eine leere Liste.")
    system_components = data.get("system_components")
    if not data["packaging"] and not system_components:
        errors.append("Mindestens packaging oder system_components muss einen Eintrag enthalten.")
    for position, unit in enumerate(data["packaging"], start=1):
        if not isinstance(unit, dict) or not str(unit.get("size", "")).strip() or not str(unit.get("article_number", "")).strip():
            errors.append(f"packaging, Eintrag {position}: size und article_number sind Pflicht.")
    if system_components:
        if isinstance(system_components, list):
            for position, unit in enumerate(system_components, start=1):
                if not isinstance(unit, dict) or not str(unit.get("size", "")).strip() or not str(unit.get("article_number", "")).strip():
                    errors.append(f"system_components, Eintrag {position}: size und article_number sind Pflicht.")
        elif isinstance(system_components, dict):
            items = system_components.get("items")
            if not str(system_components.get("title", "")).strip() or not isinstance(items, list) or not items:
                errors.append("system_components als Gruppe muss title und mindestens einen Eintrag unter items enthalten.")
            else:
                for position, component in enumerate(items, start=1):
                    if not isinstance(component, dict) or not str(component.get("name", "")).strip() or not str(component.get("role", "")).strip():
                        errors.append(f"system_components, Eintrag {position}: name und role sind Pflicht.")
        else:
            errors.append("system_components muss eine Liste oder eine Gruppe mit title und items sein.")

    if not isinstance(data["legal"], list) or len(data["legal"]) < 1:
        errors.append("legal muss mindestens einen juristisch freigegebenen Absatz enthalten.")

    for field in REQUIRED_ASSETS:
        reference = data[field]
        if not isinstance(reference, str) or not reference.strip():
            errors.append(f"{field} muss einen relativen Asset-Pfad enthalten.")
            continue
        resolved = asset_path(reference)
        if not resolved.is_file():
            message = f"Asset fehlt: {field} → {reference}"
            if release:
                errors.append(message)
            else:
                warnings.append(message)
        elif field == "product_image":
            if resolved.suffix.lower() != ".png":
                errors.append("product_image muss ein PNG mit transparentem Hintergrund sein.")
            else:
                try:
                    from PIL import Image
                    with Image.open(resolved) as image:
                        if image.mode not in {"RGBA", "LA"}:
                            errors.append("product_image muss Transparenz enthalten (RGBA oder LA).")
                except ImportError:
                    warnings.append("Transparenz des Produktbilds konnte nicht geprüft werden: Pillow fehlt.")

    markers = MARKER_PATTERN.findall("\\n".join(walk_strings(data)))
    if markers:
        message = f"{len(markers)} offene Marker gefunden."
        if release:
            errors.append(message + " Ein Veröffentlichungs-Build ist damit gesperrt.")
        else:
            warnings.append(message + " Der Entwurf darf nicht veröffentlicht werden.")

    review = data.get("review")
    review_page_count = data.get("review_page_count", 1)
    if "review_page_count" in data and (not isinstance(review_page_count, int) or review_page_count < 1):
        errors.append("review_page_count muss eine positive ganze Zahl sein.")
    if review and "review_page_count" not in data:
        review_page_count = 1
    if not review and "review_page_count" in data:
        errors.append("review_page_count ist nur zusammen mit review zulässig.")
    if review:
        continuation_after = review.get("continuation_after")
        if continuation_after is not None:
            changes = review.get("changes", [])
            if not isinstance(continuation_after, int) or not 1 <= continuation_after < len(changes):
                errors.append("review.continuation_after muss zwischen dem ersten und letzten Änderungspunkt liegen.")
            if review_page_count != 2:
                errors.append("Ein geteilter Prüfteil benötigt review_page_count: 2.")
        elif review_page_count != 1:
            errors.append("review_page_count größer als 1 benötigt review.continuation_after.")
    if release and review:
        errors.append("review darf im Veröffentlichungs-Build nicht enthalten sein.")
    if not release and not review and markers:
        warnings.append("Marker ohne review-Block: offene Punkte und Prüfprotokoll dokumentieren.")

    missing_fonts = [name for name in REQUIRED_FONTS if not (FONT_DIR / name).is_file()]
    if missing_fonts:
        message = (
            "Markenschriften fehlen unter assets/fonts/: "
            + ", ".join(missing_fonts)
            + ". Sie sind im Repository versioniert - bitte nicht loeschen. Ohne sie setzt "
            "WeasyPrint Ersatzschriften; Laufweite und Umbruch weichen ab."
        )
        if release:
            errors.append(message)
        else:
            warnings.append(message)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validiert einen BKM-TDS-Content-Datensatz.")
    parser.add_argument("content", type=Path, help="Pfad zur content.json; relativ zum Repository oder absolut")
    parser.add_argument("--release", action="store_true", help="Aktiviert Sperren für die Veröffentlichung")
    args = parser.parse_args()

    path = args.content if args.content.is_absolute() else ROOT_DIR / args.content
    if not path.is_file():
        print(f"FEHLER: Content-Datei nicht gefunden: {path}")
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FEHLER: Ungültiges JSON: {error}")
        return 2

    errors, warnings = validate_data(data, release=args.release)
    for warning in warnings:
        print(f"WARNUNG: {warning}")
    for error in errors:
        print(f"FEHLER: {error}")

    if errors:
        print(f"TDS-Validierung fehlgeschlagen: {len(errors)} Fehler, {len(warnings)} Warnungen.")
        return 1

    mode = "Release" if args.release else "Entwurf"
    print(f"TDS-Validierung bestanden ({mode}): {len(warnings)} Warnungen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
