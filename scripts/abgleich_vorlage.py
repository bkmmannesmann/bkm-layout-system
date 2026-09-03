#!/usr/bin/env python3
"""Vergleicht eine content.json Satz fuer Satz mit ihrer freigegebenen Vorlage.

Der Anspruch an eine Verarbeitungsanleitung ist Vollstaendigkeit, nicht
Aehnlichkeit. Am 03.09.2026 stellte sich heraus, dass die sieben aus den
PDFs gebauten Fassungen verdichtet waren: zwischen 10 und 38 Prozent der
Saetze fehlten, darunter Verarbeitungswissen wie die versetzten
Bohrreihen bei Novusan oder das Bohrtiefen-Beispiel im 45-Grad-Winkel.
Aufgefallen ist es erst, als jeder Satz maschinell gegengeprueft wurde.

Kriterium: ein Satz der Vorlage gilt als uebernommen, wenn irgendein
Acht-Wort-Fenster daraus in der content.json steht. Streng genug, um
Umbrueche, Bindestriche und Ziffer-Buchstabe-Grenzen zu ueberstehen -
und streng genug, um Weglassungen zu zeigen.

    python3 scripts/abgleich_vorlage.py content/anleitung-novusan/content.json vorlage.pdf

Was gemeldet wird, ist nicht automatisch ein Fehler: die Textextraktion
zieht Ueberschrift und Satz zusammen und liest Werkzeuglisten in
Spaltenreihenfolge. Jeder Befund gehoert einzeln nachgeschlagen.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

BOILER = ("copyright", "reproduction", "wideystra", "www bkm", "phone",
          "all rights")


def norm(s):
    """Vergleichsform: ohne Auszeichnung, ohne Diakritika, ohne Interpunktion.

    ß wird zu ss, weil Versalien im Layout so gesetzt werden. Zwischen
    Ziffer und Buchstabe kommt ein Leerzeichen, sonst gilt 600ml als
    etwas anderes als 600-ml-.
    """
    s = re.sub(r"<[^>]+>", " ", s).replace("­", "").replace(" ", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("ß", "ss")
    s = re.sub(r"(?<=\d)(?=[a-zäöü])", " ", s)
    s = re.sub(r"(?<=[a-zäöü])(?=\d)", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9äöü]+", " ", s)).strip()


def saetze(pdf):
    import pymupdf
    t = "\n".join(p.get_text() for p in pymupdf.open(str(pdf)))
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t).replace("\n", " ")
    out = []
    for s in re.split(r"(?<=[.!?])\s+|\s•\s|\t", t):
        s = re.sub(r"\s+", " ", s).strip(" •\t")
        if len(s) >= 30 and not any(b in s.lower() for b in BOILER):
            out.append(s)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("content")
    p.add_argument("vorlage")
    a = p.parse_args()

    heu = norm(Path(a.content).read_text(encoding="utf-8"))
    treffer, fehlend = 0, []
    for s in saetze(a.vorlage):
        w = norm(s).split()
        if len(w) < 8:
            continue
        if any(" ".join(w[i:i + 8]) in heu for i in range(len(w) - 7)):
            treffer += 1
        else:
            fehlend.append(s)

    gesamt = treffer + len(fehlend)
    print(f"  {Path(a.content).parent.name}: {treffer} von {gesamt} Saetzen "
          f"der Vorlage wiedergefunden.")
    for s in fehlend:
        print(f"    - {s[:150]}")
    return 1 if fehlend else 0


if __name__ == "__main__":
    sys.exit(main())
