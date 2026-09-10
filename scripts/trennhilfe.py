#!/usr/bin/env python3
"""Weiche Trennzeichen setzen, damit lange Woerter ueberall brechen duerfen.

Am 07.09.2026 gemessen: der Chromium dieses Rechners trennt deutschen
Text bei hyphens:auto nicht. hyphens:none und hyphens:auto liefern Zeile
fuer Zeile dasselbe - mit und ohne lang-Attribut. Browser tun das nur,
wenn sie ein Trennwoerterbuch fuer die Sprache mitbringen; darauf ist
kein Verlass. WeasyPrint hat eines und trennt gut, deshalb sah das
gebaute PDF sauber aus und die Vorschau in Claude Design nicht.

Ohne Trennung ist eine schmale Spalte in beiden Satzarten unbrauchbar:

    55-mm-Spalte, 9 pt      Flatterrand    Blocksatz
    ohne Trennzeichen        31,0 %        reisst auf
    mit weichen Fugen        17,6 %        1,9 %

Ein weiches Trennzeichen U+00AD braucht kein Woerterbuch. Es steht im
Text, ist unsichtbar, und wo umbrochen wird, setzt der Renderer den
Trennstrich. Das wirkt in jedem Browser und in WeasyPrint gleich.

Die Fugen kommen aus brand.json unter typography.trennfugen. Was dort
nicht steht, wird nach Silben getrennt - mit mindestens drei Zeichen zu
jeder Seite, sonst entstehen Trennungen wie 'Mau-e-r-werk'.

    python3 scripts/trennhilfe.py content/<name>/content.json
    python3 scripts/trennhilfe.py content/<name>/content.json --schreiben
    python3 scripts/trennhilfe.py --wort Bauwerksabdichtung
    python3 scripts/trennhilfe.py --pruefe-liste

Ohne --schreiben wird nur gezeigt, was sich aendern wuerde.

Angefasst werden nur Fliesstextfelder. Ueberschriften, Kolumnentitel,
Verzeichniseintraege und Pfade bleiben, wie sie sind: ein Trennzeichen
gehoert in den Satz, nicht in eine Zeile, die nie umbricht. Ein globaler
Textersatz ueber die ganze content.json trifft sie alle - das war beim
ersten Versuch der Fehler, und eine Ueberschrift mit unsichtbarem
Zeichen faellt niemandem auf, bis sie an falscher Stelle bricht.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pyphen
except ImportError:                                   # pragma: no cover
    pyphen = None

WURZEL = Path(__file__).resolve().parent.parent
WEICH = "­"

# Felder, die Fliesstext tragen. Alles andere bleibt unberuehrt.
FLIESSTEXT = {"body", "text", "lower_text", "upper_text", "intro_text",
              "leadline", "footer_text", "cta_body", "col_content",
              "quote", "content"}

# Ab hier lohnt eine Trennstelle. Kuerzere Woerter passen in jede Spalte,
# die im Satzspiegel vorkommt, und eine Trennung in einem Achtbuchstaber
# sieht nach Not aus.
MINDESTLAENGE = 12

# Mindestens so viele Zeichen bleiben links und rechts der Fuge stehen.
# Der Duden erlaubt zwei; drei liest sich besser und schneidet die
# Einzelbuchstaben weg, die pyphen an Fremdwoertern absetzt.
RAND = 3

_buch = None


def woerterbuch():
    global _buch
    if _buch is None and pyphen is not None:
        for sprache in ("de_DE", "de"):
            try:
                _buch = pyphen.Pyphen(lang=sprache)
                break
            except Exception:
                continue
    return _buch


def fugenliste():
    """Die geprueften Wortfugen aus brand.json."""
    marke = json.loads((WURZEL / "brand.json").read_text(encoding="utf-8"))
    roh = marke.get("typography", {}).get("trennfugen", {}).get("fugen", {})
    return {wort: teile.split("|") for wort, teile in roh.items()}


def zerlegen(wort, fugen):
    """Das Wort in die Stuecke zerlegen, zwischen denen getrennt werden darf."""
    if wort in fugen:
        return fugen[wort]
    buch = woerterbuch()
    if buch is None:
        return [wort]
    silben = buch.inserted(wort, hyphen="\x00").split("\x00")
    aus, puffer, rest = [], "", len(wort)
    for silbe in silben[:-1]:
        puffer += silbe
        rest -= len(silbe)
        if len(puffer) >= RAND and rest >= RAND:
            aus.append(puffer)
            puffer = ""
    aus.append(puffer + silben[-1])
    return aus


def trennen(wort, fugen):
    """Ein Wort mit weichen Trennzeichen versehen."""
    if WEICH in wort or len(wort) < MINDESTLAENGE:
        return wort
    stuecke = zerlegen(wort, fugen)
    return WEICH.join(stuecke) if len(stuecke) > 1 else wort


def satz(text, fugen):
    """Jedes lange Wort eines Textes mit Fugen versehen."""
    return re.sub(r"[A-Za-zÄÖÜäöüß]{%d,}" % MINDESTLAENGE,
                  lambda m: trennen(m.group(), fugen), text)


def gehe(knoten, fugen, feld=None, treffer=None):
    if isinstance(knoten, dict):
        return {k: gehe(v, fugen, k, treffer) for k, v in knoten.items()}
    if isinstance(knoten, list):
        return [gehe(v, fugen, feld, treffer) for v in knoten]
    if isinstance(knoten, str) and feld in FLIESSTEXT:
        neu = satz(knoten, fugen)
        if neu != knoten and treffer is not None:
            for a, b in zip(re.findall(r"[A-Za-zÄÖÜäöüß]{%d,}" % MINDESTLAENGE, knoten),
                            re.findall(r"[A-Za-zÄÖÜäöüß%s]{%d,}" % (WEICH, MINDESTLAENGE), neu)):
                if WEICH in b:
                    treffer[a] = b.replace(WEICH, "|")
        return neu
    return knoten


def pruefe_liste(fugen):
    """Stimmen die Fugen der Liste mit dem Wort ueberein?

    Ein Tippfehler in brand.json faellt sonst erst im Druck auf - als
    fehlender oder doppelter Buchstabe mitten im Wort.
    """
    fehler = []
    for wort, teile in fugen.items():
        wieder = "".join(teile)
        if wieder != wort:
            fehler.append(f"{wort!r}: die Fugen ergeben {wieder!r}")
        for t in teile:
            if len(t) < RAND:
                fehler.append(f"{wort!r}: Stueck {t!r} ist kuerzer als "
                              f"{RAND} Zeichen")
    return fehler


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("content", nargs="?", help="Pfad zu content.json")
    p.add_argument("--schreiben", action="store_true",
                   help="Die Datei aendern statt nur zu zeigen.")
    p.add_argument("--wort", help="Ein einzelnes Wort trennen und zeigen.")
    p.add_argument("--pruefe-liste", action="store_true",
                   help="Die Fugenliste in brand.json gegen sich selbst pruefen.")
    a = p.parse_args()

    fugen = fugenliste()

    if a.pruefe_liste:
        fehler = pruefe_liste(fugen)
        print(f"  Fugenliste: {len(fugen)} Woerter")
        for f in fehler:
            print(f"    - {f}")
        print("  Alle Fugen ergeben ihr Wort." if not fehler
              else f"  {len(fehler)} Beanstandung(en).")
        return 1 if fehler else 0

    if a.wort:
        stuecke = zerlegen(a.wort, fugen)
        quelle = "brand.json" if a.wort in fugen else "Silbentrennung"
        print(f"  {a.wort}  ->  {'|'.join(stuecke)}   ({quelle})")
        return 0

    if not a.content:
        p.print_help()
        return 2

    pfad = Path(a.content)
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    treffer = {}
    neu = gehe(daten, fugen, treffer=treffer)

    print(f"  {pfad}")
    print(f"  {len(treffer)} verschiedene Woerter bekommen Fugen:\n")
    aus_liste = sum(1 for w in treffer if w in fugen)
    for wort in sorted(treffer):
        quelle = "*" if wort in fugen else " "
        print(f"    {quelle} {wort:30} {treffer[wort]}")
    print(f"\n  {aus_liste} davon aus der Fugenliste (*), "
          f"{len(treffer)-aus_liste} nach Silben.")

    if a.schreiben:
        pfad.write_text(json.dumps(neu, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"  Geschrieben. Jetzt neu bauen und mit "
              f"scripts/pruefe_pdf.py nachmessen.")
    else:
        print("  Nichts geaendert. Mit --schreiben uebernehmen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
