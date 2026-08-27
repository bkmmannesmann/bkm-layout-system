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

import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Die geltende Palette kommt aus brand.json - der einzigen verbindlichen
# Markenquelle des Repositories. Frueher stand sie hier fest im Code und
# konnte still von der Dokumentation abweichen; jetzt kann sie das nicht mehr.
# --------------------------------------------------------------------------

BRAND_PATH = Path(__file__).parent.parent / "brand.json"


def lade_marke() -> dict:
    """Liest brand.json. Ohne sie laeuft nichts - sie ist die Quelle."""
    if not BRAND_PATH.exists():
        print(f"brand.json fehlt: {BRAND_PATH}")
        print("Sie ist die verbindliche Markenquelle; ohne sie kann nicht geprueft werden.")
        raise SystemExit(2)
    try:
        return json.loads(BRAND_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as fehler:
        print(f"brand.json ist kein gueltiges JSON: {fehler}")
        raise SystemExit(2)


def pruefe_marke(marke: dict) -> list[str]:
    """Prueft brand.json gegen sich selbst.

    Ohne diesen Schritt haette die Datei ein Loch: wer einen gesperrten Altwert
    als Palettenfarbe eintraegt, macht ihn damit zur Regel, und die Pruefung
    meldet ihn nirgends mehr. Die Quelle muss in sich stimmen, sonst prueft sie
    nur noch sich selbst.
    """
    fehler = []
    gesperrt = {w.lower() for w in marke["forbidden_colors"]["values"]}
    normiert = {a.lower() for a in marke.get("normalised_colors", {}) if not a.startswith("$")}

    for name, eintrag in marke["colors"].items():
        if not isinstance(eintrag, dict):
            continue
        hexwert = eintrag["hex"].lower()
        if hexwert in gesperrt:
            fehler.append(f"colors.{name} traegt {hexwert} - das steht unter forbidden_colors")
        if hexwert in normiert:
            fehler.append(f"colors.{name} traegt {hexwert} - das ist ein normierter Altwert")

    for rolle in ("display", "body"):
        familie = marke["typography"][rolle]
        for schnitt in familie["weights"]:
            if str(schnitt) not in familie.get("files", {}):
                fehler.append(f"typography.{rolle}: Schnitt {schnitt} ist gefuehrt, "
                              f"aber keine Datei dafuer hinterlegt")

    for name, flaeche in marke["surfaces"].items():
        if not isinstance(flaeche, dict) or name == "rules":
            continue
        for rolle, farbe in flaeche.items():
            # "sender:..." verweist auf sender_context statt auf eine feste Farbe.
            if isinstance(farbe, str) and farbe.startswith("sender:"):
                feld = farbe.split(":", 1)[1]
                for absender, eintrag in marke["sender_context"].items():
                    if absender.startswith("$"):
                        continue
                    if feld not in eintrag:
                        fehler.append(f"surfaces.{name}.{rolle} verweist auf "
                                      f"sender:{feld}, das sender_context.{absender} "
                                      f"nicht fuehrt")
                    elif eintrag[feld] not in marke["colors"]:
                        fehler.append(f"sender_context.{absender}.{feld} nennt "
                                      f"'{eintrag[feld]}', das keine Farbe in colors ist")
                continue
            if farbe not in marke["colors"]:
                fehler.append(f"surfaces.{name}.{rolle} nennt '{farbe}', "
                              f"das keine Farbe in colors ist")
    return fehler


MARKE = lade_marke()

_selbstpruefung = pruefe_marke(MARKE)
if _selbstpruefung:
    print("brand.json widerspricht sich selbst:")
    for _zeile in _selbstpruefung:
        print(f"  - {_zeile}")
    raise SystemExit(2)

PALETTE = {
    eintrag["hex"].lower(): name.replace("-", " ").title()
    for name, eintrag in MARKE["colors"].items()
    if isinstance(eintrag, dict) and "hex" in eintrag
}
# Zwei Toene, die brand.json nicht als Rolle fuehrt, im Bestand aber vorkommen:
# Schwarz und die Markerflaeche des Datenblatts.
PALETTE.setdefault("#000000", "Schwarz")
PALETTE.setdefault("#f0fad4", "Markerflaeche")

FORBIDDEN = {
    wert.lower(): "gesperrter Altwert"
    for wert in MARKE["forbidden_colors"]["values"]
}

# Toene, die auf einen Palettenwert normiert wurden und nicht zurueckkommen duerfen.
NORMALISED = {
    alt.lower(): neu.lower()
    for alt, neu in MARKE.get("normalised_colors", {}).items()
    if not alt.startswith("$")
}

# Markenschriften aus brand.json, dazu die Fallback-Familie des Druckmodus.
FONTS_OK = tuple(sorted({
    MARKE["typography"]["display"]["family"].lower(),
    MARKE["typography"]["body"]["family"].lower(),
    MARKE["typography"]["print_fallback"]["family"].lower(),
    "liberation sans",
}))

# Erlaubte Schnitte je Familie. Ein Verweis auf einen nicht gefuehrten Schnitt
# ist Drift: die Datei liegt vielleicht im Repository, eingesetzt wird sie nicht.
FONT_WEIGHTS = {
    MARKE["typography"]["display"]["family"].lower(): set(MARKE["typography"]["display"]["weights"]),
    MARKE["typography"]["body"]["family"].lower(): set(MARKE["typography"]["body"]["weights"]),
}

# Schriftdateien, die brand.json fuehrt. Ein url() auf eine andere Datei unter
# assets/fonts/ ist Drift.
FONT_FILES = set()
for _familie in ("display", "body"):
    for _schnitt in MARKE["typography"][_familie].get("files", {}).values():
        FONT_FILES.update(v for v in _schnitt.values())
FONT_FILES.add(MARKE["typography"]["print_fallback"]["file"])
FONT_FILES.update(MARKE["typography"]["print_fallback"].get("files", {}).values())

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
        elif colour in NORMALISED:
            findings.append(
                f"NORMIERT  {colour}  wurde auf {NORMALISED[colour]} normiert "
                f"und darf nicht zurueckkommen"
            )
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
        if low.startswith("courier") and "tds-marker" in text:
            continue      # in brand.json als Ausnahme gefuehrt, siehe no_monospace
        findings.append(f"SCHRIFT   {family!r} ist keine Markenschrift")

    # Verweise auf Schriftdateien: brand.json fuehrt, welche eingesetzt werden.
    # Unbounded_400 und _700 liegen im Repository, sind aber nicht zugelassen -
    # ein url() darauf ist Drift, auch wenn die Datei existiert.
    for ref in re.findall(r"url\(['\"]?([^'\")]*assets/fonts/[^'\")]+)", text):
        datei = ref.split("/")[-1]
        if not any(erlaubt.endswith(datei) for erlaubt in FONT_FILES):
            findings.append(
                f"SCHRIFT   {datei} ist in brand.json nicht als Schnitt gefuehrt"
            )

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
        for familie, schnitte in sorted(FONT_WEIGHTS.items()):
            print(f"  {familie}: nur {', '.join(str(w) for w in sorted(schnitte))}")
        print("\nZugelassene Schriftdateien:")
        for datei in sorted(FONT_FILES):
            print(f"  {datei}")
        print(f"\nQuelle: brand.json {MARKE['version']}, Stand {MARKE['updated']}")
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
