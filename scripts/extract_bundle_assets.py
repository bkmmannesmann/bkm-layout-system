#!/usr/bin/env python3
"""Holt die Bilder, Schriften und Bibliotheken aus den gebuendelten Canvas-Exporten.

Claude Design exportiert eine Vorlage als eine einzelne HTML-Datei, in der alle
Dateien mitreisen: gzip-gepackt, base64-kodiert, in einem
<script type="__bundler/manifest">. Die urspruenglichen Pfade stehen dort nicht -
im Dokument sind sie durch UUIDs ersetzt.

Rekonstruiert wird die Zuordnung ueber die Vorlage im Repository, die dieselbe
Struktur mit den echten Pfaden traegt: die n-te Referenz im Bundle gehoert zur
n-ten Referenz im Original. Der MIME-Typ aus dem Manifest muss zur Dateiendung
des Pfades passen, sonst wird der Eintrag nicht geschrieben, sondern gemeldet.

    python3 scripts/extract_bundle_assets.py <verzeichnis-mit-exporten>
    python3 scripts/extract_bundle_assets.py <verzeichnis> --write

Ohne --write wird nur berichtet. Geschrieben wird nach assets/ und uploads/;
vorhandene Dateien werden nicht ueberschrieben, ausser mit --force.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = ROOT_DIR / "templates" / "brochure"

# Der Stand, in dem die Vorlagen noch die urspruenglichen Schriftpfade tragen.
# Danach wurden sie auf die im Repository vorhandenen TTF gezogen, wodurch sich
# die Reihenfolge der Referenzen verschiebt.
BASELINE = "567c94c"

MIME_ENDUNG = {
    "image/svg+xml": {".svg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/jpeg": {".jpg", ".jpeg"},
    "font/woff2": {".woff2"},
    "font/ttf": {".ttf"},
    "text/javascript": {".js"},
    "application/javascript": {".js"},
}

UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def bundle_teile(pfad: Path) -> tuple[dict, str] | None:
    """Liest Manifest und Dokumentvorlage aus einem Export."""
    text = pfad.read_text(encoding="utf-8", errors="replace")
    manifest = re.search(
        r'<script type="__bundler/manifest">\s*(\{.*?\})\s*</script>', text, re.DOTALL)
    template = re.search(
        r'<script type="__bundler/template">\s*(.*?)\s*</script>', text, re.DOTALL)
    if not manifest or not template:
        return None
    roh = template.group(1).strip()
    if roh.startswith('"'):
        roh = json.loads(roh)
    return json.loads(manifest.group(1)), roh


def referenzen(text: str) -> list[str]:
    """Alle src- und url-Werte in Dokumentreihenfolge."""
    return re.findall(r'(?:src|url)\s*=?\s*[("\'\\]+\s*([^"\')\\]+)', text)


def original(name: str) -> str | None:
    """Die Repository-Vorlage im Baseline-Stand."""
    result = subprocess.run(
        ["git", "show", f"{BASELINE}:templates/brochure/{name}"],
        cwd=ROOT_DIR, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def entpacken(eintrag: dict) -> bytes:
    roh = base64.b64decode(eintrag["data"])
    if eintrag.get("compressed"):
        return gzip.decompress(roh)
    return roh


def partner(export: Path) -> str | None:
    """Die Repository-Vorlage, die zu diesem Export gehoert.

    Die Exporte heissen etwa '8fe3a890-A_Titelblaetter.html', die Vorlagen
    'A-Titelblaetter.dc.html'.
    """
    stamm = export.stem.split("-", 1)[-1].replace("_", "-")
    for kandidat in TEMPLATE_DIR.glob("*.dc.html"):
        if kandidat.name.split(".")[0].lower() == stamm.lower():
            return kandidat.name
    return None


def main() -> int:
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    schreiben = "--write" in sys.argv[1:]
    ueberschreiben = "--force" in sys.argv[1:]

    if not argumente:
        print(__doc__.strip().split("\n\n")[-2])
        return 2

    quelle = Path(argumente[0])
    exporte = sorted(quelle.glob("*.html")) if quelle.is_dir() else [quelle]
    if not exporte:
        print(f"Keine HTML-Exporte in {quelle}")
        return 2

    gefunden: dict[str, bytes] = {}
    unklar: list[str] = []

    for export in exporte:
        teile = bundle_teile(export)
        if teile is None:
            print(f"  uebersprungen: {export.name} - kein Bundle")
            continue
        manifest, template = teile

        vorlage = partner(export)
        if vorlage is None:
            unklar.append(f"{export.name}: keine passende Vorlage in templates/brochure/")
            continue
        quelltext = original(vorlage)
        if quelltext is None:
            unklar.append(f"{vorlage}: nicht im Stand {BASELINE}")
            continue

        # Beide Dokumente tragen dieselben Referenzen in derselben Reihenfolge,
        # das Bundle nur mit UUIDs statt Pfaden. Zugeordnet wird deshalb strikt
        # Position gegen Position - ueber ALLE Referenzen, nicht nur die unter
        # assets/ und uploads/. Sonst verschiebt schon das <script src="./support.js">
        # im Kopf die ganze Liste um eins.
        ids = referenzen(template)
        pfade = referenzen(quelltext)

        if len(ids) != len(pfade):
            unklar.append(
                f"{vorlage}: {len(ids)} Referenzen im Bundle, {len(pfade)} im "
                f"Original - Zuordnung uebersprungen")
            continue

        zugeordnet = 0
        for roh, ziel in zip(ids, pfade):
            # Die Kennung steht teils HTML-maskiert da, etwa in
            # mask:url(&quot;<uuid>&quot;) - deshalb suchen statt vergleichen.
            treffer = UUID.search(roh)
            if treffer is None:
                continue
            kennung = treffer.group(0)
            if not ziel.startswith(("assets/", "uploads/")):
                continue
            eintrag = manifest.get(kennung)
            if eintrag is None:
                continue
            # Der MIME aus dem Bundle ist der tatsaechliche Inhalt, die Endung im
            # Pfad nur der Name - etwa ein JPEG, das .png heisst. Abweichungen
            # werden gemeldet, nicht korrigiert: der Pfad steht in den Vorlagen.
            erwartet = MIME_ENDUNG.get(eintrag.get("mime"), set())
            endung = Path(ziel).suffix.lower()
            if erwartet and endung not in erwartet:
                unklar.append(
                    f"{ziel}: Inhalt ist {eintrag.get('mime')}, die Endung sagt {endung}")
            try:
                inhalt = entpacken(eintrag)
            except Exception as fehler:
                unklar.append(f"{ziel}: {type(fehler).__name__}")
                continue
            if ziel in gefunden and gefunden[ziel] != inhalt:
                unklar.append(f"{ziel}: zwei verschiedene Fassungen in den Exporten")
            gefunden[ziel] = inhalt
            zugeordnet += 1

        print(f"  {export.name:34s} {zugeordnet:2d} von {len(ids)} Kennungen zugeordnet")

    print(f"\n{len(gefunden)} Datei(en) rekonstruiert:")
    nach_ordner: dict[str, list[str]] = {}
    for ziel in sorted(gefunden):
        nach_ordner.setdefault(str(Path(ziel).parent), []).append(Path(ziel).name)
    for ordner in sorted(nach_ordner):
        namen = nach_ordner[ordner]
        print(f"  {ordner}/  ({len(namen)})")
        for name in namen:
            groesse = len(gefunden[f'{ordner}/{name}']) / 1024
            print(f"      {name:56s} {groesse:8.1f} KB")

    if unklar:
        print(f"\n{len(unklar)} offene Punkte:")
        for zeile in unklar:
            print(f"  - {zeile}")

    if not schreiben:
        print("\nMit --write schreiben.")
        return 0

    neu = uebersprungen = 0
    for ziel, inhalt in sorted(gefunden.items()):
        pfad = ROOT_DIR / ziel
        if pfad.exists() and not ueberschreiben:
            uebersprungen += 1
            continue
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_bytes(inhalt)
        neu += 1
    print(f"\n{neu} geschrieben, {uebersprungen} uebersprungen (schon vorhanden).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
