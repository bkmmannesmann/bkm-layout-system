#!/usr/bin/env python3
"""Prueft beliebige Dateien gegen die geltende BKM-Markenpalette.

Gedacht fuer alles, was ausserhalb der geprueften Templates entsteht und
trotzdem im Corporate Design stehen soll: Entwuerfe aus Claude Design
(.dc.html), Dateien aus anderen Repositories, exportiertes HTML, SVGs,
Stylesheets. validate_brochure.py und validate_layout.py schuetzen den
Innenteil und das Datenblatt; dieses Skript nimmt sich alles andere vor.

    python3 scripts/check_brand_drift.py <datei-oder-verzeichnis> [...]
    python3 scripts/check_brand_drift.py --list           # Palette ausgeben
    python3 scripts/check_brand_drift.py --include-docs .  # auch Markdown

Kommentare werden vor der Pruefung entfernt und Markdown standardmaessig
uebersprungen: die Layoutvertraege nennen die gesperrten Altwerte
ausdruecklich, und der Kopf von pages-spec.css fuehrt die alten Messwerte
als Herkunftsnachweis. Beides ist Dokumentation, kein Drift.

Gemeldet wird in drei Stufen:

  VERBOTEN   Ein Altwert, den docs/LAYOUT-CONTRACT.md ausdruecklich sperrt.
  NORMIERT   Ein Ton, der einem Palettenwert sehr nahe liegt, ihn aber
             knapp verfehlt - typischerweise ein alter Messwert.
  FREMD      Ein Farbwert, der zu keinem Palettenton passt. Kann Absicht
             sein (Fotos, Fremdlogos), gehoert aber angesehen.

Ohne Abhaengigkeiten, damit es in jeder Umgebung laeuft.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Die geltende Palette. Quelle: docs/LAYOUT-CONTRACT.md und
# design-system/variables.css. Wer hier etwas aendert, aendert beide mit.
# --------------------------------------------------------------------------

PALETTE = {
    "#1c4b42": "Deep Green",
    "#287d4b": "Transition Green",
    "#4daf46": "Pure Green",
    "#b4e717": "Lime",
    "#494949": "Stone Grey",
    "#f6f5f2": "Sand White",
    "#e3e1dc": "Haarlinie",
    "#d9d7d3": "Rule",
    "#f0fad4": "Markerflaeche",
    "#ffffff": "Weiss",
    "#000000": "Schwarz",
}

# Ausdruecklich gesperrt, siehe docs/LAYOUT-CONTRACT.md, Abschnitt Farben.
FORBIDDEN = {
    "#009245": "Altwert Gruen",
    "#006837": "Altwert Dunkelgruen",
    "#00a99d": "Altwert Tuerkis",
    "#8cc63f": "Altwert Hellgruen - heute Lime #b4e717",
}

# Markenschriften. Alles andere ist entweder ein Fallback oder Drift.
FONTS_OK = ("unbounded", "tt norms pro", "bkm pdf sans", "liberation sans")
FONTS_NEUTRAL = ("sans-serif", "serif", "monospace", "inherit", "initial",
                 "system-ui", "ui-sans-serif", "arial", "helvetica")

SUFFIXES = {".html", ".htm", ".css", ".svg", ".json", ".js", ".xml"}

# Dokumentation nennt Farbwerte, sie verwendet sie nicht: die Layoutvertraege
# fuehren die gesperrten Altwerte ausdruecklich auf. Markdown wird deshalb nur
# mit --include-docs geprueft.
DOC_SUFFIXES = {".md", ".markdown", ".txt"}

# Wie weit ein Ton von einem Palettenwert abweichen darf, um noch als
# "verfehlter Palettenton" statt als fremde Farbe zu gelten. Gemessen als
# Summe der Kanalabstaende; 24 entspricht rund 8 Stufen je Kanal.
NEAR_MISS = 24


def parse_hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def distance(a: str, b: str) -> int:
    return sum(abs(x - y) for x, y in zip(parse_hex(a), parse_hex(b)))


def nearest(colour: str) -> tuple[str, str, int]:
    best = min(PALETTE, key=lambda p: distance(colour, p))
    return best, PALETTE[best], distance(colour, best)


def find_colours(text: str) -> set[str]:
    """Sammelt Hex- und rgb()-Farben ein und normalisiert sie auf #rrggbb."""
    found = set()
    for raw in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", text):
        found.add("#%02x%02x%02x" % parse_hex(raw))
    for r, g, b in re.findall(
        r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", text
    ):
        found.add("#%02x%02x%02x" % (int(r), int(g), int(b)))
    return found


def find_fonts(text: str) -> set[str]:
    families = set()
    # Bis zum naechsten ; } oder " lesen, nicht bis zum ersten Apostroph:
    # in style="font-family:'Inter',sans-serif" steht der Name in Apostrophen.
    for decl in re.findall(r"font-family\s*:\s*([^;{}\"]+)", text, re.I):
        for name in decl.split(","):
            name = name.strip().strip("'\"")
            if name:
                families.add(name)
    return families


def strip_comments(text: str, suffix: str) -> str:
    """Entfernt Kommentare.

    Ein Wert in einem Kommentar ist ein Nachweis, keine Verwendung: der Kopf
    von pages-spec.css fuehrt die alten Messwerte als Herkunftsangabe. Ohne
    diesen Schritt meldet die Pruefung die eigene Dokumentation.
    """
    if suffix in (".css",):
        return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    if suffix in (".html", ".htm", ".svg", ".xml"):
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        return re.sub(r"\{#.*?#\}", "", text, flags=re.DOTALL)   # Jinja
    if suffix == ".js":
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        return re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return text


def check_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"nicht lesbar: {exc}"]

    text = strip_comments(text, path.suffix.lower())
    findings = []

    for colour in sorted(find_colours(text)):
        if colour in FORBIDDEN:
            findings.append(f"VERBOTEN  {colour}  {FORBIDDEN[colour]}")
        elif colour in PALETTE:
            continue
        else:
            name, label, dist = nearest(colour)
            if dist <= NEAR_MISS:
                findings.append(
                    f"NORMIERT  {colour}  verfehlt {label} {name} um {dist}"
                )
            else:
                findings.append(
                    f"FREMD     {colour}  kein Palettenton "
                    f"(naechster: {label} {name})"
                )

    for family in sorted(find_fonts(text)):
        low = family.lower()
        if any(low.startswith(ok) for ok in FONTS_OK):
            continue
        if low in FONTS_NEUTRAL or low.startswith("var("):
            continue
        findings.append(f"SCHRIFT   {family!r} ist keine Markenschrift")

    return findings


def collect(targets: list[str], include_docs: bool = False) -> list[Path]:
    wanted = SUFFIXES | DOC_SUFFIXES if include_docs else SUFFIXES
    files: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            files.extend(
                p for p in sorted(path.rglob("*"))
                if p.is_file() and p.suffix.lower() in wanted
                and ".git" not in p.parts and "node_modules" not in p.parts
            )
        elif path.is_file():
            files.append(path)
        else:
            print(f"nicht gefunden: {target}", file=sys.stderr)
    return files


def main() -> int:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    if args[0] == "--list":
        print("Geltende Palette:")
        for value, name in PALETTE.items():
            print(f"  {value}  {name}")
        print("\nGesperrte Altwerte:")
        for value, name in FORBIDDEN.items():
            print(f"  {value}  {name}")
        print("\nMarkenschriften: " + ", ".join(FONTS_OK))
        return 0

    include_docs = "--include-docs" in args
    args = [a for a in args if a != "--include-docs"]
    files = collect(args, include_docs)
    if not files:
        print("Keine passenden Dateien.")
        return 0

    total = {"VERBOTEN": 0, "NORMIERT": 0, "FREMD": 0, "SCHRIFT": 0}
    for path in files:
        findings = check_file(path)
        if not findings:
            continue
        print(f"\n{path}")
        for finding in findings:
            print(f"  {finding}")
            key = finding.split()[0]
            if key in total:
                total[key] += 1

    print(f"\n{len(files)} Datei(en) geprueft. "
          + ", ".join(f"{v}x {k}" for k, v in total.items() if v))

    # Nur gesperrte Altwerte und verfehlte Palettentoene sind harte Fehler.
    # Fremde Farben und Fremdschriften koennen Absicht sein.
    return 1 if total["VERBOTEN"] or total["NORMIERT"] else 0


if __name__ == "__main__":
    sys.exit(main())
