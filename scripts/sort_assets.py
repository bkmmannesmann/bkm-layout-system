#!/usr/bin/env python3
"""Sortiert hochgeladene Dateien an ihren Platz im Repository.

Gedacht fuer den Weg ueber die GitHub-Weboberflaeche: dort laesst sich kein ZIP
entpacken, und pro Vorgang gehen hoechstens 100 Dateien mit je 25 MB. Alles
landet deshalb erst in einem Eingang und wird von hier aus verteilt.

    python3 scripts/sort_assets.py            # nur berichten
    python3 scripts/sort_assets.py --write    # verschieben

Der Eingang ist uploads/_inbox/. Ein anderer Ordner geht als erstes Argument.

Einsortiert wird nach Dateityp und - bei Bildern - nach dem gemessenen
Seitenverhaeltnis, nicht nach dem Dateinamen. Der Name sagt, was gemeint war;
das Verhaeltnis sagt, was die Datei ist. Weichen beide voneinander ab, wird das
gemeldet und die Datei bleibt liegen.

Warum das noetig ist: ein Titelblatt-Hintergrund im Format 16:9 endet bei
118,125 mm - genau dort, wo die Eckerweiterung anfaengt. Er kann sie nicht
mitbringen, und im Export schaut an dieser Stelle das Foto durch. Die
Hero-Grafik ist deshalb 210 x 125 mm, also 1,680 statt 1,778.

Pillow wird nur zum Messen gebraucht. Fehlt es, wird nach Typ und Name
sortiert und jedes Bild zur Sichtpruefung gemeldet.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
INBOX = ROOT_DIR / "uploads" / "_inbox"

try:
    from PIL import Image
except ImportError:
    Image = None

# Bildformate der Marke. Das Verhaeltnis ist Breite durch Hoehe.
# Siehe brand.json, cover_geometry und textures.
FORMATE = [
    # (Name, Verhaeltnis, Toleranz, Zielordner, Bemerkung)
    ("Hero-Grafik 210 x 125 mm", 210 / 125,      0.01, "uploads",
     "traegt die Eckerweiterung unterhalb der 16:9-Kante"),
    ("A4-Flaeche 210 x 297 mm",  210 / 297,      0.01, "uploads",
     "ganzseitige Textur"),
    ("16:9 210 x 118,125 mm",    16 / 9,         0.01, None,
     "endet auf der 16:9-Kante und kann die Eckerweiterung NICHT tragen"),
    ("Badge",                    720 / 174,      0.02, "assets/images",
     None),
    ("Keyvisual hochkant",       1046 / 2480,    0.02, "assets/keyvisual",
     None),
]

# Nicht-Bilder gehen nach Endung und Name.
NACH_ENDUNG = {
    ".woff2": "assets/fonts",
    ".ttf":   "assets/fonts",
    ".otf":   "assets/fonts",
}

NACH_NAME = [
    ("keyvisual", "assets/keyvisual"),
    ("logo",      "assets/logos"),
    ("signatur",  "uploads"),
]

BILDENDUNGEN = {".png", ".jpg", ".jpeg", ".webp"}


def ziel_fuer_svg(name: str) -> str:
    for teil, ordner in NACH_NAME:
        if teil in name.lower():
            return ordner
    return "assets/icons/phosphor/bold"


def messen(pfad: Path):
    """Groesse, Verhaeltnis und Alphakanal - oder None ohne Pillow."""
    if Image is None:
        return None
    with Image.open(pfad) as im:
        breite, hoehe = im.size
        alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    return breite, hoehe, breite / hoehe, alpha


def einordnen(pfad: Path):
    """Liefert (Zielordner oder None, Meldungen)."""
    endung = pfad.suffix.lower()
    meldungen = []

    if endung == ".svg":
        return ziel_fuer_svg(pfad.name), meldungen
    if endung in NACH_ENDUNG:
        return NACH_ENDUNG[endung], meldungen
    if endung not in BILDENDUNGEN:
        return None, [f"unbekannte Endung {endung}"]

    mass = messen(pfad)
    if mass is None:
        return None, ["Pillow fehlt - Bild von Hand einordnen"]
    breite, hoehe, verhaeltnis, alpha = mass

    for name, soll, toleranz, ordner, bemerkung in FORMATE:
        if abs(verhaeltnis - soll) > toleranz:
            continue
        if ordner is None:
            meldungen.append(f"{name}: {bemerkung}")
            return None, meldungen
        # Die Hero-Grafik braucht Transparenz: unterhalb der 16:9-Kante ist
        # nur der Eckzipfel deckend, der Rest gibt das Foto darunter frei.
        if soll == 210 / 125 and not alpha:
            meldungen.append(
                "Hero-Format, aber ohne Alphakanal - unterhalb der "
                "16:9-Kante muss alles ausser dem Eckzipfel durchsichtig sein")
            return None, meldungen
        return ordner, meldungen

    # Kein bekanntes Format: ein Foto. Die gehoeren nach uploads/.
    if "titel-hero" in pfad.name.lower():
        meldungen.append(
            f"heisst wie eine Hero-Grafik, misst aber {verhaeltnis:.4f} "
            f"statt {210/125:.4f} (210 x 125 mm)")
        return None, meldungen
    return "uploads", meldungen


def main() -> int:
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    schreiben = "--write" in sys.argv[1:]
    eingang = Path(argumente[0]) if argumente else INBOX
    if not eingang.is_absolute():
        eingang = ROOT_DIR / eingang

    if not eingang.is_dir():
        print(f"Eingang fehlt: {eingang.relative_to(ROOT_DIR)}")
        print("Dort hochladen, dann dieses Skript laufen lassen.")
        return 2

    dateien = [f for f in sorted(eingang.rglob("*"))
               if f.is_file() and f.name not in ("README.md", ".gitkeep")]
    if not dateien:
        print(f"{eingang.relative_to(ROOT_DIR)} ist leer.")
        return 0

    if Image is None:
        print("Hinweis: Pillow fehlt, Bilder werden nicht gemessen.\n")

    zuzuordnen, offen = [], []
    for datei in dateien:
        ordner, meldungen = einordnen(datei)
        if ordner is None:
            offen.append((datei, meldungen))
        else:
            ziel = ROOT_DIR / ordner / datei.name
            zuzuordnen.append((datei, ziel, meldungen))

    print(f"{len(dateien)} Datei(en) im Eingang\n")
    if zuzuordnen:
        print(f"{len(zuzuordnen)} zugeordnet:")
        for datei, ziel, meldungen in zuzuordnen:
            vorhanden = "  (ueberschreibt)" if ziel.exists() else ""
            print(f"  {datei.name:52s} -> {ziel.parent.relative_to(ROOT_DIR)}/{vorhanden}")
            for m in meldungen:
                print(f"      {m}")
    if offen:
        print(f"\n{len(offen)} bleiben liegen:")
        for datei, meldungen in offen:
            print(f"  {datei.name}")
            for m in meldungen:
                print(f"      {m}")

    if not schreiben:
        print("\nMit --write verschieben.")
        return 1 if offen else 0

    for datei, ziel, _ in zuzuordnen:
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(datei), str(ziel))
    print(f"\n{len(zuzuordnen)} verschoben, {len(offen)} liegengeblieben.")
    print("Danach docs/ASSET-MANIFEST.md nachziehen.")
    return 1 if offen else 0


if __name__ == "__main__":
    sys.exit(main())
