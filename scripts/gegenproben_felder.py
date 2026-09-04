#!/usr/bin/env python3
"""Gegenproben fuer den Feldabgleich in beiden Pruefern.

Ein Feld, das der Content fuehrt und das Template nicht liest, faellt
still weg. Am 03.09.2026 kam eine 49-seitige Broschuere so zurueck:
fuenfzehn list-Seiten trugen ihre Eintraege unter 'items' und ihre
Ueberschrift unter 'headline_section' - das Template liest dort
'entries' und 'headline'. Die Seiten kamen fast leer heraus, und
validate_brochure.py lief gruen durch.

Geprueft wird beides: dass der Abgleich greift, wenn ein Feld nicht
gesetzt wird, und dass er bei den bestehenden Dokumenten still bleibt.

    python3 scripts/gegenproben_felder.py
"""

import copy
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import validate_brochure as vb   # noqa: E402
import validate_anleitung as va  # noqa: E402


def lade(pfad):
    return json.loads((ROOT_DIR / pfad).read_text(encoding="utf-8"))


def faelle():
    b = lade("content/broschuere-mannesmann/content.json")
    a = lade("content/anleitung-hzc/content.json")

    # Der echte Fehler: eine list-Seite mit items statt entries.
    b_items = copy.deepcopy(b)
    b_items["pages"].append({"type": "list", "headline_section": "Titel",
                             "items": [{"title": "a", "body": "b"}]})

    # Ein Feld, das es auf einem anderen Seitentyp gibt, hier aber nicht:
    # steps liest nur process, nicht list. Hier stand frueher
    # headline_large - das war ein gutes Beispiel, bis list und feature
    # dieselben Kopfzeilenfelder bekamen wie content und process. Seither
    # ist es dort erlaubt, und die Gegenprobe braucht ein Feld, das
    # wirklich nur einem einzigen Seitentyp gehoert.
    b_fremd = copy.deepcopy(b)
    b_fremd["pages"].append({"type": "list", "headline": "Titel",
                             "entries": [], "steps": []})

    a_fremd = copy.deepcopy(a)
    a_fremd["pages"][0]["erfundenes_feld"] = "steht nirgends im Template"

    return [
        ("Broschuere unveraendert - still", vb.check_felder, b, False),
        ("Anleitung unveraendert - still", va.pruefe_felder, a, False),
        ("list-Seite mit 'items' statt 'entries'", vb.check_felder, b_items, True),
        ("Feld vom falschen Seitentyp", vb.check_felder, b_fremd, True),
        ("erfundenes Feld in der Anleitung", va.pruefe_felder, a_fremd, True),
    ]


def main():
    schlecht = 0
    proben = faelle()
    for name, pruefung, daten, soll in proben:
        gefunden = pruefung(daten)
        gut = bool(gefunden) == soll
        schlecht += not gut
        zeichen = "greift " if gefunden else "still  "
        print(f"  {zeichen} {name:42s} {'ok' if gut else 'FEHLSCHLAG'}")
        for f in gefunden[:2]:
            print(f"          {f[:120]}")
    print()
    print(f"  {len(proben)-schlecht} von {len(proben)} Gegenproben wie erwartet.")
    return 1 if schlecht else 0


if __name__ == "__main__":
    sys.exit(main())
