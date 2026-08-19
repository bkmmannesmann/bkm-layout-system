#!/usr/bin/env python3
"""Holt die Markenschriften aus dem zentralen BKM-Design-System.

Die Schriftdateien sind lizenziert und werden in diesem Repository bewusst nicht
versioniert. Verbindliche Quelle ist das in BRAND-SOURCE.md gepinnte Design-System.
Dieses Skript lädt genau diese Revision und legt die Dateien unter assets/fonts/ ab.

  python3 scripts/sync_fonts.py
  python3 scripts/sync_fonts.py --check
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
BRAND_SOURCE = ROOT_DIR / "BRAND-SOURCE.md"
FONT_DIR = ROOT_DIR / "assets" / "fonts"
DESIGN_SYSTEM_URL = "https://github.com/bkmmannesmann/bkm-design-system"
SOURCE_SUBDIR = "assets/fonts"
REVISION_PATTERN = re.compile(r"bkm-design-system/commit/([0-9a-f]{40})")
WOFF2_MAGIC = b"wOF2"
REQUIRED_FONTS = (
    "Unbounded_400.woff2",
    "Unbounded_700.woff2",
    "Unbounded_900.woff2",
    "TT_Norms_Pro_Compact_Regular.woff2",
    "TT_Norms_Pro_Bold.woff2",
)


def pinned_revision() -> str:
    """Liest die festgelegte Design-System-Revision aus BRAND-SOURCE.md."""
    match = REVISION_PATTERN.search(BRAND_SOURCE.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(
            "FEHLER: In BRAND-SOURCE.md ist keine vollständige Design-System-Revision hinterlegt."
        )
    return match.group(1)


def run_git(*arguments: str) -> None:
    """Führt ein Git-Kommando aus und bricht mit klarer Meldung ab."""
    result = subprocess.run(["git", *arguments], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"FEHLER: git {' '.join(arguments)}\n{result.stderr.strip()}")


def fetch_fonts(revision: str, target: Path) -> None:
    """Holt assets/fonts der angegebenen Revision in ein Arbeitsverzeichnis."""
    run_git("init", "-q", str(target))
    run_git("-C", str(target), "remote", "add", "origin", DESIGN_SYSTEM_URL)
    run_git("-C", str(target), "fetch", "-q", "--depth", "1", "origin", revision)
    run_git("-C", str(target), "checkout", "-q", "FETCH_HEAD", "--", SOURCE_SUBDIR)


def verify(path: Path) -> list[str]:
    """Prüft, ob alle Pflichtschriften vorhanden und echte woff2-Dateien sind."""
    problems = []
    for name in REQUIRED_FONTS:
        candidate = path / name
        if not candidate.is_file():
            problems.append(f"fehlt: {name}")
        elif candidate.read_bytes()[:4] != WOFF2_MAGIC:
            problems.append(f"kein woff2: {name}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronisiert die BKM-Markenschriften.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Prüft nur den lokalen Bestand, ohne etwas zu laden",
    )
    arguments = parser.parse_args()

    if arguments.check:
        problems = verify(FONT_DIR)
        for problem in problems:
            print(f"FEHLER: {problem}")
        if problems:
            print("Markenschriften unvollständig. Abhilfe: python3 scripts/sync_fonts.py")
            return 1
        print(f"Markenschriften vollständig: {len(REQUIRED_FONTS)} Dateien in {FONT_DIR}.")
        return 0

    revision = pinned_revision()
    print(f"Design-System-Revision laut BRAND-SOURCE.md: {revision[:7]}")

    with tempfile.TemporaryDirectory() as workspace:
        checkout = Path(workspace) / "design-system"
        fetch_fonts(revision, checkout)
        source = checkout / SOURCE_SUBDIR
        problems = verify(source)
        if problems:
            for problem in problems:
                print(f"FEHLER: {problem}")
            print(f"Die Revision {revision[:7]} liefert nicht alle Pflichtschriften.")
            return 1
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        for name in REQUIRED_FONTS:
            shutil.copy2(source / name, FONT_DIR / name)
            print(f"  {name}")

    print(f"{len(REQUIRED_FONTS)} Markenschriften nach {FONT_DIR} übernommen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
