#!/usr/bin/env python3
"""Prueft eine content.json der Verarbeitungsanleitung, bevor gebaut wird.

Der Datenvertrag steht in docs/anleitung-content.schema.json. Geprueft wird
hier von Hand, nicht ueber jsonschema: das Paket liegt nicht im Bestand, und
das Datenblatt prueft aus demselben Grund ebenso. Das Schema bleibt trotzdem
die maschinenlesbare Referenz - danach richten sich Werkzeuge, die aus einem
Textdokument eine Anleitung bauen.

Diese Pruefung liest den Inhalt. Die Pruefungen in build_anleitung.py lesen
das Ergebnis. Beide sind noetig: was hier zaehlbar ist, faellt dort nicht auf,
und umgekehrt faellt ein abgeschnittener Absatz nur im PDF auf.

    python3 scripts/validate_anleitung.py content/anleitung-hz250pro/content.json
    python3 scripts/validate_anleitung.py <datei> --release
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = ROOT_DIR / "templates" / "anleitung"
ICON_DIR = TEMPLATE_DIR / "icons"

PFLICHT = ("title", "product_name", "product_line", "document_rubrik",
           "issued", "page_number_start", "page_total", "pages")
# product_image und line_badge standen hier bis 31.08.2026 als Pflicht,
# wurden aber weder im Innenteil noch im Titelblatt gesetzt. Ein Kollege
# haette sie liefern muessen, ohne dass sie irgendwo erscheinen.
LINIEN = ("PRO LINE", "HOME LINE")
DATUM = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

# Gemessen am 31.08.2026: 68 Zeichen laufen zwei Zeilen, 82 laufen drei.
# Die Grenze steht als max_lines in brand.json; hier die Zeichenzahl, die
# sich daraus ergibt.
SUB_MAX = 70
ABB_MAX = 4          # rechte Spalte, siehe ABB_JE_SEITE in build_anleitung.py
VORTEIL_MAX = 4      # mehr passen nicht auf Blatt 2


def pruefe(daten):
    fehler = []

    for feld in PFLICHT:
        if feld not in daten:
            fehler.append(f"Pflichtfeld fehlt: {feld}")
    if fehler:
        return fehler

    if daten["document_rubrik"] != "Verarbeitungsanleitung":
        fehler.append("document_rubrik muss 'Verarbeitungsanleitung' lauten.")
    if daten["product_line"] not in LINIEN:
        fehler.append(f"product_line ist {daten['product_line']!r}, "
                      f"zugelassen sind {' und '.join(LINIEN)}.")
    # Produkte mit dem Namensbestandteil Novu gehoeren zur Home Line, alle
    # uebrigen zur Pro Line. Die Zuordnung ist fest, siehe
    # badges.assignment in brand.json.
    erwartet = "HOME LINE" if "novu" in daten["product_name"].lower() else "PRO LINE"
    if daten["product_line"] != erwartet:
        fehler.append(
            f"product_line ist {daten['product_line']}, erwartet {erwartet}: "
            f"Produkte mit dem Namensbestandteil Novu gehoeren zur Home Line, "
            f"alle uebrigen zur Pro Line.")
    if not DATUM.match(str(daten["issued"])):
        fehler.append(f"issued ist {daten['issued']!r}, erwartet TT.MM.JJJJ.")

    # Seitenzaehlung: das Titelblatt ist Blatt 1 und zaehlt mit.
    if daten["page_number_start"] != 2:
        fehler.append(f"page_number_start ist {daten['page_number_start']}, "
                      f"muss 2 sein - das Titelblatt ist Blatt 1.")
    seiten = daten["pages"]
    if daten["page_total"] != len(seiten) + 1:
        fehler.append(f"page_total ist {daten['page_total']}, der Innenteil hat "
                      f"aber {len(seiten)} Seiten. Mit dem Titelblatt sind das "
                      f"{len(seiten) + 1}.")

    fehler.extend(pruefe_folge(seiten))
    fehler.extend(pruefe_cover(daten.get("cover")))
    fehler.extend(pruefe_seiten(seiten))
    fehler.extend(pruefe_verweise(daten))
    return fehler


def pruefe_folge(seiten):
    """Die Rubrikenfolge ist abgelesen, nicht entworfen - und fest.

    Sieben freigegebene Fassungen tragen sie gleich, unabhaengig von Produkt
    und Linie: erst Vorteile und Vorbereitung, dann ein bis vier
    Anleitungsseiten, zuletzt die Nacharbeit.
    """
    arten = [s.get("type") for s in seiten]
    fehler = []
    unbekannt = [a for a in arten
                 if a not in ("vorbereitung", "anleitung", "nacharbeit")]
    if unbekannt:
        fehler.append(f"Unbekannter Seitentyp: {', '.join(map(str, unbekannt))}. "
                      f"Zugelassen sind vorbereitung, anleitung, nacharbeit.")
        return fehler
    if arten[0] != "vorbereitung":
        fehler.append("Die erste Seite des Innenteils muss vom Typ "
                      "vorbereitung sein.")
    if arten[-1] != "nacharbeit":
        fehler.append("Die letzte Seite muss vom Typ nacharbeit sein.")
    if arten.count("vorbereitung") != 1:
        fehler.append(f"{arten.count('vorbereitung')}x vorbereitung, erwartet 1.")
    if arten.count("nacharbeit") != 1:
        fehler.append(f"{arten.count('nacharbeit')}x nacharbeit, erwartet 1.")
    n = arten.count("anleitung")
    if not 1 <= n <= 4:
        fehler.append(f"{n} Anleitungsseiten, erwartet 1 bis 4.")
    if arten.count("anleitung") and any(
            a == "anleitung" for a in arten[arten.index("nacharbeit"):]):
        fehler.append("Nach der Nacharbeit folgt keine Anleitungsseite mehr.")

    mit_tipp = [i for i, s in enumerate(seiten) if s.get("tip")]
    letzte = max((i for i, a in enumerate(arten) if a == "anleitung"), default=None)
    if letzte is not None and mit_tipp and mit_tipp != [letzte]:
        fehler.append("Der Profi-Tipp steht auf der letzten Anleitungsseite, "
                      "sonst nirgends.")
    return fehler


def pruefe_cover(cover):
    if cover is None:
        return []          # zulaessig: dann entsteht nur der Innenteil
    fehler = []
    for feld in ("headline", "subheadline", "intro_text"):
        if not cover.get(feld):
            fehler.append(f"cover.{feld} fehlt.")
    sub = cover.get("subheadline", "")
    if len(sub) > SUB_MAX:
        fehler.append(
            f"cover.subheadline hat {len(sub)} Zeichen, hoechstens {SUB_MAX} "
            f"passen in zwei Zeilen. Text kuerzen, nicht die Spalte "
            f"verbreitern - type_scale.cover.subheadline.max_lines.")
    return fehler


def pruefe_seiten(seiten):
    fehler = []
    for i, s in enumerate(seiten, 2):
        art = s.get("type")
        if art == "vorbereitung":
            v = s.get("advantages", [])
            if not 2 <= len(v) <= VORTEIL_MAX:
                fehler.append(f"Seite {i}: {len(v)} Vorteile, erwartet 2 bis "
                              f"{VORTEIL_MAX}. Mehr passen nicht auf das Blatt.")
            for feld in ("scope", "workplace", "tools", "safety"):
                if feld not in s:
                    fehler.append(f"Seite {i}: {feld} fehlt.")
        elif art == "anleitung":
            if not s.get("sections"):
                fehler.append(f"Seite {i}: keine Abschnitte.")
            n = len(s.get("figures", []))
            if n > ABB_MAX:
                fehler.append(f"Seite {i}: {n} Abbildungen, in die Spalte "
                              f"passen {ABB_MAX}.")
            for a in s.get("sections", []):
                if not a.get("title"):
                    fehler.append(f"Seite {i}: Abschnitt ohne Titel.")
                if not (a.get("body") or a.get("bullets") or a.get("formulas")):
                    fehler.append(f"Seite {i}: Abschnitt {a.get('title')!r} "
                                  f"hat weder Text noch Liste noch Formel.")
        elif art == "nacharbeit":
            for feld in ("headline", "steps", "issued", "copyright"):
                if not s.get(feld):
                    fehler.append(f"Seite {i}: {feld} fehlt.")
    return fehler


def pruefe_verweise(daten):
    """Bild- und Iconverweise am Dateisystem, nicht per Textsuche.

    Findet WeasyPrint eine Bilddatei nicht, setzt es still den Alt-Text an
    ihre Stelle. Ein falscher Iconname laesst den Kasten still leer, weil
    das Template mit 'ignore missing' einbindet.
    """
    fehler, gesehen = [], set()

    def geh(knoten):
        if isinstance(knoten, dict):
            for k, w in knoten.items():
                if k == "icon" and isinstance(w, str) and w:
                    if w not in gesehen:
                        gesehen.add(w)
                        if not (ICON_DIR / f"{w}.svg").is_file():
                            fehler.append(
                                f"Icon gibt es nicht: {w}.svg fehlt in "
                                f"templates/anleitung/icons/")
                elif k == "image" and isinstance(w, str):
                    if w and w not in gesehen:
                        gesehen.add(w)
                        if not (TEMPLATE_DIR / w).resolve().is_file():
                            fehler.append(f"Bildverweis zeigt ins Leere: {w}")
                else:
                    geh(w)
        elif isinstance(knoten, list):
            for e in knoten:
                geh(e)

    geh(daten)
    return fehler


def offene_angaben(daten):
    treffer = []

    def geh(k):
        if isinstance(k, str):
            if "[ANGABE FEHLT" in k or "[ZU PRÜFEN" in k:
                treffer.append(k.strip()[:110])
        elif isinstance(k, dict):
            for w in k.values():
                geh(w)
        elif isinstance(k, list):
            for e in k:
                geh(e)

    geh(daten.get("pages", []))
    return treffer


def main():
    p = argparse.ArgumentParser(
        description="Prueft eine content.json der Verarbeitungsanleitung.")
    p.add_argument("content")
    p.add_argument("--release", action="store_true",
                   help="Offene Angaben blockieren die Freigabe.")
    a = p.parse_args()

    pfad = Path(a.content)
    if not pfad.is_file():
        print(f"Nicht gefunden: {pfad}")
        return 2
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Kein gueltiges JSON: {e}")
        return 2

    fehler = pruefe(daten)
    offen = offene_angaben(daten)

    if fehler:
        print(f"Inhaltspruefung {pfad}: {len(fehler)} Verstoss(e)\n")
        for f in fehler:
            print(f"  - {f}")
        print("\nDer Datenvertrag steht in docs/anleitung-content.schema.json, "
              "die Layoutregeln in docs/ANLEITUNG-LAYOUT.md.")
        return 1

    if offen:
        wort = "Release" if a.release else "Entwurf"
        print(f"Offene Angaben ({len(offen)}), im {wort}:")
        for e in offen:
            print(f"  - {e}")
        if a.release:
            print("\nEine Release-Fassung darf keine offenen Angaben tragen.")
            return 1
        print()

    print(f"Inhaltspruefung {pfad} bestanden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
