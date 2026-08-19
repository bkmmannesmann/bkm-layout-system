#!/usr/bin/env python3
"""Validiert TDS-Content gegen den BKM-Redaktionsstandard.

Ohne --release werden Entwurfsdaten geprüft. Mit --release blockieren offene
Marker, interne Prüfblöcke und fehlende Produktionsassets die PDF-Erzeugung.
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
MARKER_PATTERN = re.compile(r"\[(?:ANGABE FEHLT|ZU PRÜFEN):[^\]]+\]")
REVISION_PATTERN = re.compile(r"^\d+\.\d+$")
REQUIRED_FIELDS = (
    "title", "product_name", "product_subtitle", "product_short", "product_line",
    "revision", "issue_date", "page_count", "logo", "keyvisual", "line_badge",
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

    if data["page_count"] != 3:
        errors.append("page_count muss für das aktuelle TDS-Template 3 sein.")

    if not REVISION_PATTERN.fullmatch(str(data["revision"])):
        errors.append("revision muss dem Format n.n entsprechen, zum Beispiel '1.0'.")

    try:
        datetime.strptime(str(data["issue_date"]), "%d.%m.%Y")
    except ValueError:
        errors.append("issue_date muss das Format TT.MM.JJJJ haben.")

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

    matrix = data.get("matrix")
    if matrix:
        if not isinstance(matrix, dict) or not matrix.get("title") or not matrix.get("columns") or not matrix.get("rows"):
            errors.append("matrix muss title, columns und rows enthalten.")
        elif any(len(row) != len(matrix["columns"]) for row in matrix["rows"]):
            errors.append("Jede Zeile der matrix muss genau so viele Werte wie columns enthalten.")

    if not isinstance(data["packaging"], list):
        errors.append("packaging muss eine Liste sein; bei fehlenden Gebinden nutze eine leere Liste.")
    if not data["packaging"] and not data.get("system_components"):
        errors.append("Mindestens packaging oder system_components muss einen Eintrag enthalten.")
    for group_name in ("packaging", "system_components"):
        for position, unit in enumerate(data.get(group_name, []), start=1):
            if not isinstance(unit, dict) or not str(unit.get("size", "")).strip() or not str(unit.get("article_number", "")).strip():
                errors.append(f"{group_name}, Eintrag {position}: size und article_number sind Pflicht.")

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

    markers = MARKER_PATTERN.findall("\n".join(walk_strings(data)))
    if markers:
        message = f"{len(markers)} offene Marker gefunden."
        if release:
            errors.append(message + " Ein Veröffentlichungs-Build ist damit gesperrt.")
        else:
            warnings.append(message + " Der Entwurf darf nicht veröffentlicht werden.")

    review = data.get("review")
    if release and review:
        errors.append("review darf im Veröffentlichungs-Build nicht enthalten sein.")
    if not release and not review and markers:
        warnings.append("Marker ohne review-Block: offene Punkte und Prüfprotokoll dokumentieren.")

    if not (ROOT_DIR / "assets" / "fonts").is_dir() or not list((ROOT_DIR / "assets" / "fonts").glob("*")):
        warnings.append("Lizenzierte Schriften liegen nicht im lokalen assets/fonts/-Ordner; die PDF-Ansicht kann Ersatzschriften verwenden.")

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
