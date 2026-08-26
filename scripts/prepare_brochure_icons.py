#!/usr/bin/env python3
"""Bereitet die Broschueren-Icons fuer die WeasyPrint-Pipeline auf.

Im Canvas liegen die Icons als CSS-Maske auf einer eingefaerbten Flaeche - die
Datei selbst braucht dort keine Fuellung, nur ihre Form. Die Pipeline bettet
dieselben Dateien inline ein, und WeasyPrint wendet das Dokument-Stylesheet
nicht auf die Kinder eines inline eingebetteten SVG an. Ohne Fuellung am
svg-Element druckt der Glyph schwarz.

Dieses Skript setzt genau diese Fuellung - dieselbe Regel, die
docs/LAYOUT-CONTRACT.md fuer die Datenblatt-Icons aufstellt. Die Maske im
Browser bleibt davon unberuehrt: sie wertet nur den Alphakanal aus.

    python3 scripts/prepare_brochure_icons.py            # prueft und meldet
    python3 scripts/prepare_brochure_icons.py --write    # schreibt die Fuellung

templates/tds/icons/ wird nicht angefasst. Diese neun Dateien haengen am
Geometrie-Hash im Manifest von scripts/validate_layout.py; sechs Motive gibt es
in beiden Verzeichnissen, sie bleiben getrennt.

Ohne Abhaengigkeiten.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
ICON_DIR = ROOT_DIR / "assets" / "icons" / "phosphor" / "bold"
TDS_ICON_DIR = ROOT_DIR / "templates" / "tds" / "icons"

LIME = "#b4e717"

# Motive, die es in beiden Verzeichnissen gibt. Sie werden bewusst nicht
# zusammengelegt: der Datenblatt-Vertrag benennt nach Inhaltsblock und sichert
# die Geometrie ueber einen Hash, der Canvas benennt nach Motiv und braucht ein
# offenes Set. Ein Motivwechsel im Design-System ist an beiden Stellen
# nachzuziehen.
SHARED_MOTIFS = {
    "atom.svg":       "templates/tds/icons/eigenschaften.svg",
    "package.svg":    "templates/tds/icons/gebinde.svg",
    "scales.svg":     "templates/tds/icons/recht.svg",
    "seal-check.svg": "templates/tds/icons/vorteile.svg",
    "table.svg":      "templates/tds/icons/daten.svg",
    "warning.svg":    "templates/tds/icons/hinweise.svg",
    # Die Vorlagen referenzieren house.svg, das Datenblatt house-line -
    # zwei verschiedene Phosphor-Motive. Der Eintrag steht hier fuer den
    # Fall, dass spaeter doch house-line.svg mitgeliefert wird.
    "house-line.svg": "templates/tds/icons/anwendung.svg",
}


def needs_fill(svg: str) -> bool:
    """Traegt das svg-Element bereits eine Fuellung?"""
    opening = re.search(r"<svg\b[^>]*>", svg, re.IGNORECASE)
    if opening is None:
        return False
    tag = opening.group(0)
    return not re.search(r'style\s*=\s*["\'][^"\']*fill\s*:', tag, re.IGNORECASE)


def add_fill(svg: str) -> str:
    """Setzt style="fill:#b4e717" am svg-Element, ohne andere Attribute anzutasten."""
    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        existing = re.search(r'(style\s*=\s*["\'])([^"\']*)(["\'])', tag, re.IGNORECASE)
        if existing:
            value = existing.group(2).rstrip().rstrip(";")
            merged = f"{value};fill:{LIME}" if value else f"fill:{LIME}"
            return tag[:existing.start(2)] + merged + tag[existing.end(2):]
        return tag[:-1].rstrip() + f' style="fill:{LIME}">'
    return re.sub(r"<svg\b[^>]*>", repl, svg, count=1, flags=re.IGNORECASE)


def main() -> int:
    write = "--write" in sys.argv[1:]

    if not ICON_DIR.exists():
        print(f"Verzeichnis fehlt: {ICON_DIR.relative_to(ROOT_DIR)}")
        print("Die Broschueren-Icons sind noch nicht geliefert.")
        return 0

    icons = sorted(ICON_DIR.glob("*.svg"))
    if not icons:
        print(f"Keine SVG-Dateien in {ICON_DIR.relative_to(ROOT_DIR)}.")
        return 0

    offen, fertig = [], []
    for icon in icons:
        svg = icon.read_text(encoding="utf-8")
        if needs_fill(svg):
            offen.append(icon)
            if write:
                icon.write_text(add_fill(svg), encoding="utf-8")
        else:
            fertig.append(icon)

    print(f"{len(icons)} Icon(s) in {ICON_DIR.relative_to(ROOT_DIR)}")
    print(f"  {len(fertig)} tragen bereits eine Fuellung")
    if offen:
        verb = "ergaenzt" if write else "brauchen sie noch"
        print(f"  {len(offen)} {verb}:")
        for icon in offen[:8]:
            print(f"      {icon.name}")
        if len(offen) > 8:
            print(f"      ... und {len(offen) - 8} weitere")

    vorhanden = {i.name for i in icons} & set(SHARED_MOTIFS)
    if vorhanden:
        print(f"\n{len(vorhanden)} Motiv(e) gibt es auch im Datenblatt-Set. Getrennt "
              f"halten - die dortigen Dateien haengen am Geometrie-Hash:")
        for name in sorted(vorhanden):
            print(f"      {name:16s} <-> {SHARED_MOTIFS[name]}")

    if offen and not write:
        print("\nMit --write schreiben.")
        return 1

    # Gegenprobe: das Datenblatt-Set darf sich nicht veraendert haben.
    if write and TDS_ICON_DIR.exists():
        import subprocess
        result = subprocess.run(
            ["git", "status", "--porcelain", str(TDS_ICON_DIR)],
            cwd=ROOT_DIR, capture_output=True, text=True,
        )
        if result.stdout.strip():
            print("\nFEHLER: templates/tds/icons/ wurde veraendert:")
            print(result.stdout)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
