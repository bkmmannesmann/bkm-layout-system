#!/usr/bin/env python3
"""Prüft, dass das TDS-Layout unverändert dem Layoutvertrag entspricht.

Inhalt ist Sache von validate_tds.py. Dieses Skript schützt das Design:
es liest templates/tds/template.html und template.css und schlägt an, wenn eine
der festgelegten Invarianten verletzt oder ein bekanntes Antimuster eingebaut
wurde. Es läuft ohne Abhängigkeiten und ist für die CI gedacht.

    python3 scripts/validate_layout.py
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
CSS_PATH = ROOT_DIR / "templates" / "tds" / "template.css"
HTML_PATH = ROOT_DIR / "templates" / "tds" / "template.html"
ICON_DIR = ROOT_DIR / "templates" / "tds" / "icons"
# Feste Zuordnung Inhaltsblock -> Icon. Die Bold-Pfade stammen aus phosphor-icons/core,
# assets/bold/<name>-bold.svg; der SVG-Wurzelknoten trägt zusätzlich die feste CI-Farbe
# #b4e717, weil WeasyPrint CSS-Variablen in Inline-SVG nicht auflöst. Die Prüfsumme
# sichert die gesamte freigegebene Datei; die Strichstärke lässt sich am Pfad selbst
# nicht ablesen, deshalb wird sie nicht geraten.
ICON_SOURCE = "phosphor-icons/core, assets/bold/ + BKM-Lime-Füllung"
ICON_MANIFEST = {
    "vorteile.svg":      ("seal-check",          "0532d9d0116c98814550429510da80b10a499ba1e026a693a104c8633e7a2b35"),
    "eigenschaften.svg": ("atom",                "b4a6e5d5040b2dedda12ddf7158f4f58a5b56dcec96aefeead2bab8f757cf65f"),
    "daten.svg":         ("table",               "ff0b3a8a669d166f8de63472c3ece9e100937f1082ab7e924f5737462d2bc4b1"),
    "anwendung.svg":     ("house-line",          "067819a7ac3832b3e5ec7bfc80c63cbfc9671b3ceafb3391fbe60594e7e861c8"),
    "hinweise.svg":      ("warning",             "0a7dde69e5d924541e57e3b690175498bd15de0ac9e37a9b834a765423c80da4"),
    "gebinde.svg":       ("package",             "18ee52061a25dbf9c47d0c7dcb530b6e438c5d40d2efac72580ef3b0051c5ade"),
    "lagerung.svg":      ("thermometer-simple",  "4997534fd31142cebabebfe609bcf68f36cbdaeb0b7875c71554c1537f5ab9a0"),
    "entsorgung.svg":    ("recycle",             "649a31bc251911d05bf130790de3b1a909a9aa33462a6e1fcfcfa6165a18c0c0"),
    "recht.svg":         ("scales",              "cf214b60261f3f8ddcd030493860530cdcb1f39280d85ea8c48fd5aa7a1c3a28"),
}

# (Beschreibung, Regex, muss_vorkommen)
CSS_RULES = [
    ("Achse 18 mm", r"--tds-axis:\s*18mm", True),
    ("Logobreite 42 mm", r"--tds-logo-w:\s*42mm", True),
    ("Keyvisual 10 %", r"--tds-keyvisual-w:\s*10%", True),
    ("Radius 3 px", r"--tds-radius:\s*3px", True),
    ("Kopfbereich 16:9 = 118.1mm", r"height:\s*118\.1mm", True),
    ("Balken 30 px hoch", r"\.tds-band[^}]*height:\s*30px", True),
    ("Balken überlappt um 10 px", r"\.tds-band[^}]*margin-top:\s*-10px", True),
    ("Produktbild 230 x 312 px", r"width:\s*230px;\s*height:\s*312px", True),
    ("Line-Badge 44 x 182 px", r"\.tds-badge[^}]*height:\s*44px", True),
    ("Icons als Flaeche gefuellt", r"\.tds-icon svg[^}]*fill:\s*var\(--tds-lime\)", True),
    ("Icons ohne fill:none", r"\.tds-icon svg[^}]*fill:\s*none", False),
    ("Icons ohne stroke-width", r"\.tds-icon svg[^}]*stroke-width", False),
    ("keine seitenbezogene Satzdichte", r"\.tds-page:nth-of-type", False),
    ("kein Zebra in der Datentabelle", r"\.tds-table[^}]*nth-child", False),
    ("keine Pill-Radien", r"border-radius:\s*(?:9999px|50%|999px)", False),
    ("kein falsches Pure Green", r"#009245", False),
    ("kein falsches Deep Green", r"#006837", False),
    ("kein falsches Transition Green", r"#00A99D", False),
    ("kein falsches Lime", r"#8CC63F", False),
    ("keine Icon-Webfont im Druck-CSS", r"phosphor-icons", False),
]

HTML_RULES = [
    ("Erstelldatum im Kopf", r"tds-head__meta[^<]*>Erstelldatum:\s*{{\s*created_date\s*}}", True),
    ("Erstelldatum in den Laufkoepfen", r"tds-runhead__meta", True),
    ("keine Revisionsnummer", r"{{\s*revision\s*}}", False),
    ("kein Ausgabedatum", r"{{\s*issue_date\s*}}", False),
    ("Seitenzahl gegen page_count", r"tds-foot__page[^<]*>\d+/{{\s*page_count\s*}}", True),
    ("Pruefteil hinter {% if review %}", r"{%\s*if review\s*%}", True),
    ("Kein Stylesheet im Produktordner", r"content/", False),
    ("keine Icon-Webfont im Template", r"phosphor-icons", False),
    ("keine Icon-Klassen statt SVG", r"class=\"ph[ -]", False),
]



def check(label: str, text: str, rules) -> list[str]:
    errors: list[str] = []
    for description, pattern, must_exist in rules:
        found = re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None
        if must_exist and not found:
            errors.append(f"{label}: {description} — Regel fehlt oder wurde geaendert.")
        if not must_exist and found:
            errors.append(f"{label}: {description} — verbotenes Muster gefunden.")
    return errors


def main() -> int:
    errors: list[str] = []

    for path in (CSS_PATH, HTML_PATH):
        if not path.is_file():
            print(f"FEHLER: Datei fehlt: {path.relative_to(ROOT_DIR)}")
            return 2

    css = CSS_PATH.read_text(encoding="utf-8")
    html = HTML_PATH.read_text(encoding="utf-8")

    errors += check("template.css", css, CSS_RULES)
    errors += check("template.html", html, HTML_RULES)

    footers = re.findall(r"tds-foot__(?:meta|page)", html)
    if len(re.findall(r"class=\"tds-foot\"", html)) < 2:
        errors.append("template.html: jede Seite braucht eine Fusszeile, der Pruefteil eingeschlossen.")
    if re.search(r"tds-foot[^}]*created_date", html):
        errors.append("template.html: die Fusszeile darf kein Datum tragen.")

    if not ICON_DIR.is_dir():
        errors.append("templates/tds/icons/ fehlt.")
    else:
        present = {path.name for path in ICON_DIR.glob("*.svg")}

        for extra in sorted(present - set(ICON_MANIFEST)):
            errors.append(
                f"icons/{extra} steht nicht im Layoutvertrag. Das Verzeichnis enthaelt genau die "
                "neun benannten Blockdateien; Altbestaende bitte loeschen."
            )

        for name, (upstream, expected_sha) in ICON_MANIFEST.items():
            path = ICON_DIR / name
            if not path.is_file():
                errors.append(
                    f"icons/{name} fehlt (erwartet: {upstream}-bold.svg aus {ICON_SOURCE}). "
                    "Die Blockzuordnung ist fest; siehe docs/LAYOUT-CONTRACT.md."
                )
                continue

            raw = path.read_bytes()
            actual_sha = hashlib.sha256(raw).hexdigest()
            if actual_sha != expected_sha:
                errors.append(
                    f"icons/{name} weicht vom freigegebenen Stand ab. Erwartet wird "
                    f"{upstream}-bold.svg aus {ICON_SOURCE} (sha256 {expected_sha[:12]}…), "
                    f"gefunden {actual_sha[:12]}…. Icon neu aus dem Bold-Set holen oder, wenn die "
                    "Aenderung gewollt ist, die Pruefsumme im Manifest aktualisieren."
                )

            body = raw.decode("utf-8")
            if 'fill="currentColor"' not in body:
                errors.append(f"icons/{name}: fill=\"currentColor\" fehlt; die Farbe setzt das CSS.")
            if "stroke=" in body:
                errors.append(f"icons/{name}: Kontur-Icon, erwartet wird ein Flaechenglyph.")
            if 'viewBox="0 0 256 256"' not in body:
                errors.append(f"icons/{name}: viewBox muss 0 0 256 256 sein (Phosphor-Raster).")
            if "width=" in body or "height=" in body:
                errors.append(f"icons/{name}: feste Groesse im SVG; die Groesse setzt das CSS.")

    for error in errors:
        print(f"FEHLER: {error}")

    if errors:
        print(f"Layoutpruefung fehlgeschlagen: {len(errors)} Abweichungen vom Layoutvertrag.")
        print("Regeln: docs/LAYOUT-CONTRACT.md")
        return 1

    print(
        f"Layoutpruefung bestanden. {len(footers)} Fusszeilen-Elemente und "
        f"{len(ICON_MANIFEST)} Icons geprueft."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
