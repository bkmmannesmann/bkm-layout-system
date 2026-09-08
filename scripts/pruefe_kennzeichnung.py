#!/usr/bin/env python3
"""Prüft, ob KI-Motive den Vermerk „AI GENERATED“ tragen — und bringt ihn auf Wunsch auf.

    python3 scripts/pruefe_kennzeichnung.py                 # Bestand prüfen
    python3 scripts/pruefe_kennzeichnung.py uploads/foo.webp
    python3 scripts/pruefe_kennzeichnung.py --alle          # auch nicht registrierte Bilder
    python3 scripts/pruefe_kennzeichnung.py --stempeln uploads/foo.webp

Welche Motive KI-generiert sind, kann kein Bildvergleich entscheiden. Das steht in
assets/kennzeichnung/register.json und wird von Hand gepflegt. Nur ein dort als
KI eingetragenes Motiv ohne Vermerk ist ein Fehler; alles andere ist ein Hinweis.

Aufgebracht wird nur mit --stempeln. Ein Vermerk, den ein Skript ungefragt an die
falsche Stelle setzt, ist schlechter als ein gemeldeter fehlender.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kennzeichnung as K  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent
REGISTER = WURZEL / "assets" / "kennzeichnung" / "register.json"
ENDUNGEN = (".png", ".jpg", ".jpeg", ".webp")
SUCHORTE = ("uploads", "assets/images")

# Ein Vermerk, der die Bildkante berührt, verstösst gegen „leichter Abstand zu den
# Bildkanten“ und fällt beim Beschnitt als Erstes weg.
RAND_MINDESTENS = 0.003


def register() -> dict:
    if REGISTER.exists():
        return json.loads(REGISTER.read_text(encoding="utf-8"))
    return {"ki_motive": [], "keine_ki": []}


def einordnung(rel: str, reg: dict) -> str:
    if rel in reg.get("ki_motive", []):
        return "ki"
    if rel in reg.get("keine_ki", []):
        return "keine_ki"
    return "unbekannt"


def sammle(argumente, alle: bool, reg: dict) -> list[Path]:
    if argumente:
        pfade = []
        for a in argumente:
            p = Path(a)
            if p.is_dir():
                pfade += [q for q in sorted(p.rglob("*")) if q.suffix.lower() in ENDUNGEN]
            elif p.exists():
                pfade.append(p)
            else:
                print("  nicht gefunden: %s" % a)
        return pfade
    if alle:
        pfade = []
        for ort in SUCHORTE:
            d = WURZEL / ort
            if d.is_dir():
                pfade += [q for q in sorted(d.rglob("*")) if q.suffix.lower() in ENDUNGEN]
        return pfade
    return [WURZEL / r for r in reg.get("ki_motive", []) if (WURZEL / r).exists()]


def bewerte(pfad: Path, regel: dict) -> dict:
    treffer = K.finde(pfad)
    w, h = treffer["bild"]
    befund = dict(treffer)
    befund["maengel"] = []
    if treffer["gefunden"]:
        breite = treffer["kasten"][2]
        dx, dy = K.raender(treffer)
        befund["rand_x"], befund["rand_y"] = dx, dy
        soll = max(regel["mindestbreite_px"], int(round(w * regel["breite_anteil"])))
        if breite < regel["mindestbreite_px"]:
            befund["maengel"].append(
                "zu klein: %d px, Mindestmaß %d px" % (breite, regel["mindestbreite_px"]))
        elif breite < soll * 0.75:
            befund["maengel"].append(
                "kleiner als vorgesehen: %d px statt %d px (%.1f %% der Bildbreite)"
                % (breite, soll, 100 * breite / w))
        if min(dx, dy) < RAND_MINDESTENS:
            befund["maengel"].append(
                "ohne Abstand zur Bildkante (%.2f %% / %.2f %%)" % (100 * dx, 100 * dy))
    return befund


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pfade", nargs="*", help="Bilder oder Ordner; ohne Angabe das Register")
    ap.add_argument("--alle", action="store_true", help="alle Bilder in uploads/ und assets/images/")
    ap.add_argument("--stempeln", action="store_true", help="fehlenden Vermerk aufbringen")
    ap.add_argument("--ecke", choices=K.ECKEN, help="Ecke erzwingen statt nach Kontrast wählen")
    ap.add_argument("--ausgabe", help="Zielordner beim Stempeln (Vorgabe: an Ort und Stelle)")
    ap.add_argument("--druckbreite", type=float, metavar="MM",
                    help="Breite in mm, in der das Motiv im Layout stehen wird. Nur damit "
                         "laesst sich das Mindestmass fuer den Druck einhalten: die Marke wird "
                         "ins Pixelbild gebrannt und skaliert mit der Platzierung mit.")
    args = ap.parse_args()

    regel = K.regeln()
    reg = register()
    pfade = sammle(args.pfade, args.alle, reg)
    if not pfade:
        print("Keine Bilder zu prüfen. Register leer? %s" % REGISTER)
        return 0

    print("KI-Kennzeichnung — %d Motiv(e), Schwelle %.2f\n" % (len(pfade), K.SCHWELLE))
    fehler, hinweise, gestempelt = [], [], []

    for p in pfade:
        rel = str(p.relative_to(WURZEL)) if p.is_absolute() else str(p)
        art = einordnung(rel, reg)
        b = bewerte(p, regel)

        if b["gefunden"]:
            print("  ✓ %-52s %s, %d px, Güte %.3f"
                  % (rel[:52], b["ecke"], b["kasten"][2], b["guete"]))
            for m in b["maengel"]:
                print("      ! %s" % m)
                # Ein Mangel am registrierten KI-Motiv ist ein Fehler, sonst ein Hinweis.
                (fehler if art == "ki" else hinweise).append("%s: %s" % (rel, m))
            continue

        if art == "keine_ki":
            print("  – %-52s kein KI-Motiv, kein Vermerk nötig" % rel[:52])
            continue

        rang = K.beste_ecke(p, regel, args.druckbreite)
        vorschlag = rang[0]
        marke = "✗" if art == "ki" else "?"
        wort = "Vermerk fehlt" if art == "ki" else "kein Vermerk, nicht im Register"
        print("  %s %-52s %s (beste Ecke: %s, Eignung %.2f)"
              % (marke, rel[:52], wort, vorschlag["ecke"], vorschlag["eignung"]))

        if args.stempeln:
            ziel = Path(args.ausgabe) / p.name if args.ausgabe else p
            erg = K.stemple(p, ziel, args.ecke, regel, args.druckbreite)
            masse = ""
            if "marke_mm" in erg:
                masse = ", %.1f mm bei %.0f mm Bildbreite (Versalhöhe %.2f mm)" % (
                    erg["marke_mm"], args.druckbreite, erg["versalhoehe_mm"])
            print("      → gesetzt %s, %d px%s → %s"
                  % (erg["ecke"], erg["kasten"][2], masse, erg["ziel"]))
            gestempelt.append(rel)
        elif art == "ki":
            fehler.append("%s: Vermerk fehlt" % rel)
        else:
            hinweise.append("%s: kein Vermerk, nicht im Register" % rel)

    print()
    if gestempelt:
        print("%d Motiv(e) gestempelt." % len(gestempelt))
    if hinweise:
        print("%d Hinweis(e):" % len(hinweise))
        for h in hinweise:
            print("   · %s" % h)
    if fehler:
        print("%d Fehler:" % len(fehler))
        for f in fehler:
            print("   · %s" % f)
        print("\nEin im Register als KI geführtes Motiv ohne gültigen Vermerk verstösst"
              "\ngegen die EU-KI-Verordnung. Aufbringen mit --stempeln.")
        return 1
    if not hinweise:
        print("Alle geprüften Motive tragen den Vermerk regelgerecht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
