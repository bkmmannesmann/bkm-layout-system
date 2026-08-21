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
# Verzeichnis assets/bold/<name>-bold.svg.
#
# Geprueft wird die GEOMETRIE, nicht die Datei: der Hash laeuft ueber die
# aneinandergehaengten d-Attribute. Damit ist das Motiv und ueber das Motiv auch
# die Strichstaerke festgenagelt (am Pfad selbst ist sie nicht ablesbar, Bold-Pfade
# enthalten legitim a4,4 oder a16,16) - waehrend Farb- und Groessenangaben frei
# bleiben. Genau die muessen anpassbar sein: WeasyPrint wendet das Stylesheet des
# Dokuments nicht auf die Kinder eines inline eingebetteten SVG an, deshalb braucht
# jede Datei ihre Lime-Fuellung selbst.
ICON_SOURCE = "phosphor-icons/core, assets/bold/"
LIME = "#b4e717"
ICON_MANIFEST = {
    "vorteile.svg":      ("seal-check",          "a93e8a92c74e9aae2860edae9fd0ce24a7dda3421361e6027d102bfd1d4040fd"),
    "eigenschaften.svg": ("atom",                "dd8ed878d3db10bb2dbaf5b59bc1d53a87333c7be5f93946939a14888ee72bc6"),
    "daten.svg":         ("table",               "1af543527d932353fb082c6486d75ee4a283ddcbfd0658ef2c6fc69659c4f034"),
    "anwendung.svg":     ("house-line",          "c180f7a7a7e952fa744f0e662da1047d39e2f18b716763038dc14b2a45cba38a"),
    "hinweise.svg":      ("warning",             "fe869c06f45132ac4b5d88842d9e977956d2b76ab57e4f656e286deffa7e6794"),
    "gebinde.svg":       ("package",             "ea374c61e84389b3e740de5555c21d185c4736bd179899dc5af5d57efd5b4151"),
    "lagerung.svg":      ("thermometer-simple",  "bac5de5bc99e4ee6481857c1ef1d1d2f2f0dff32d880d613c130b76cfaf9b968"),
    "entsorgung.svg":    ("recycle",             "37e035e6d7bce2b35be9eb4f8635ac2162d37ff2eddda19bd4687460fe8ac95d"),
    "recht.svg":         ("scales",              "f68f32519970482ceb68a648175fe422e933c629a714a3108ba74cdc33eeba20"),
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

            body = path.read_text(encoding="utf-8")

            geometry = "|".join(re.findall(r'\bd="([^"]+)"', body))
            if not geometry:
                errors.append(f"icons/{name}: kein Pfad gefunden.")
                continue
            actual_sha = hashlib.sha256(geometry.encode("utf-8")).hexdigest()
            if actual_sha != expected_sha:
                errors.append(
                    f"icons/{name} zeigt ein anderes Motiv als vereinbart. Erwartet wird "
                    f"{upstream}-bold.svg aus {ICON_SOURCE} (Geometrie {expected_sha[:12]}…), "
                    f"gefunden {actual_sha[:12]}…. Icon neu aus dem Bold-Set holen oder, wenn der "
                    "Wechsel gewollt ist, Manifest und docs/LAYOUT-CONTRACT.md gemeinsam aendern."
                )

            if LIME.lower() not in body.lower():
                errors.append(
                    f"icons/{name}: keine Lime-Fuellung in der Datei. WeasyPrint wendet das "
                    f"Stylesheet nicht auf SVG-Kinder an, deshalb braucht jedes Icon "
                    f'style="fill:{LIME}" am svg-Element - sonst druckt der Glyph schwarz.'
                )
            if "stroke=" in body:
                errors.append(f"icons/{name}: Kontur-Icon, erwartet wird ein Flaechenglyph.")
            if 'viewBox="0 0 256 256"' not in body:
                errors.append(f"icons/{name}: viewBox muss 0 0 256 256 sein (Phosphor-Raster).")
            if re.search(r"<svg[^>]*\b(width|height)=", body):
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
