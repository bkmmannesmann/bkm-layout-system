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
# Feste Zuordnung Inhaltsblock -> Icon. Quelle ist phosphor-icons/core,
# Verzeichnis assets/bold/<name>-bold.svg. Die Pruefsumme sichert die Identitaet
# der Datei; die Strichstaerke laesst sich am Pfad selbst NICHT ablesen (Bold-Pfade
# enthalten legitim a4,4 oder a16,16), deshalb wird sie nicht geraten.
ICON_SOURCE = "phosphor-icons/core, assets/bold/"
ICON_MANIFEST = {
    "vorteile.svg":      ("seal-check",          "f29d05b2145f5e01686493632a33c2d306df0c932f57cf9c34e1e7942fa55716"),
    "eigenschaften.svg": ("atom",                "50b215004b364200416bea5a7d952a841dc9b801c65359410c32209c45a6f709"),
    "daten.svg":         ("table",               "f0809a3a92d47d85f178324edd5d3b495750809e0d05ebbcf4a44eeae3405b5f"),
    "anwendung.svg":     ("house-line",          "c8cdf780da2882b25d5530155047b7c519a6cc2bbed476f5313cf95517308656"),
    "hinweise.svg":      ("warning",             "c2b1af21bbb1b92808c46f5ec01ade9169bd5cff30f8090c42da85e6e95d7558"),
    "gebinde.svg":       ("package",             "d8edc6001426d6ef610a7a60425357eb300ff2b0abf8a700eb89792c6c5a40d8"),
    "lagerung.svg":      ("thermometer-simple",  "2e833e800fcb84960d8bd4d39acb2af8b2c1b4df60f20766decd190dd962ac35"),
    "entsorgung.svg":    ("recycle",             "a46175ae6673793626fa076feb9143f95b7f5ee5563a75471d2af975c5f09caa"),
    "recht.svg":         ("scales",              "05da65086b033c0604d8f12d6ea0b51b1b47f698e3f5e396af9d2929ce859dae"),
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
