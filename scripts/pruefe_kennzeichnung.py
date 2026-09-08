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
import re
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


# Ein Bild in einer Canvas-Vorlage: Quelle und Stilangabe.
CANVAS_BILD = re.compile(r'<img[^>]*\bsrc="([^"]+)"[^>]*\bstyle="([^"]*)"')
CANVAS_DIR = WURZEL / "templates" / "brochure"


def _mm(stil: str, name: str):
    m = re.search(r"\b" + name + r":\s*([\d.]+)mm", stil)
    return float(m.group(1)) if m else None


def sichtbarer_ausschnitt(bild_v: float, kasten_v: float, cover: bool):
    """Welcher Teil des Motivs bleibt im Kasten stehen, als Anteil 0..1.

    object-fit:cover fuellt den Kasten und schneidet zentral weg, was ueber
    steht — waagerecht, wenn das Bild breiter ist als der Kasten, sonst senkrecht.
    """
    if not cover:
        return (0.0, 1.0, 0.0, 1.0)
    if bild_v > kasten_v:
        breite, hoehe = kasten_v / bild_v, 1.0
    else:
        breite, hoehe = 1.0, bild_v / kasten_v
    return ((1 - breite) / 2, 1 - (1 - breite) / 2,
            (1 - hoehe) / 2, 1 - (1 - hoehe) / 2)


def pruefe_platzierung(reg: dict) -> list[dict]:
    """Ueberlebt der Vermerk den Beschnitt, mit dem das Motiv platziert ist?

    Ein Vermerk, der im Bild steht, aber vom Layoutkasten weggeschnitten wird,
    erfuellt die Kennzeichnungspflicht nicht — im Dokument ist er nicht da.
    Geprueft werden die Canvas-Vorlagen, nicht ein Export: was hier steht, geht
    in jede daraus gebaute Broschuere ein.
    """
    ki = set(reg.get("ki_motive", []))
    lagen: dict[str, dict] = {}
    befunde = []
    if not CANVAS_DIR.is_dir():
        return befunde

    for datei in sorted(CANVAS_DIR.glob("*.dc.html")):
        for m in CANVAS_BILD.finditer(datei.read_text(encoding="utf-8")):
            quelle, stil = m.group(1), m.group(2)
            if quelle not in ki or not (WURZEL / quelle).exists():
                continue
            kb, kh = _mm(stil, "width"), _mm(stil, "height")
            if not kb or not kh:
                continue
            if quelle not in lagen:
                t = K.finde(WURZEL / quelle)
                if not t["gefunden"]:
                    continue
                bw, bh = t["bild"]
                x, y, tb, th = t["kasten"]
                lagen[quelle] = {"v": bw / bh,
                                 "x0": x / bw, "x1": (x + tb) / bw,
                                 "y0": y / bh, "y1": (y + th) / bh}
            lage = lagen[quelle]
            sx0, sx1, sy0, sy1 = sichtbarer_ausschnitt(
                lage["v"], kb / kh, "object-fit:cover" in stil.replace(" ", ""))
            if not (lage["x0"] >= sx0 and lage["x1"] <= sx1
                    and lage["y0"] >= sy0 and lage["y1"] <= sy1):
                befunde.append({
                    "vorlage": datei.name, "motiv": quelle,
                    "kasten": (kb, kh),
                    "sichtbar": (sx0, sx1, sy0, sy1),
                    "vermerk": (lage["x0"], lage["x1"], lage["y0"], lage["y1"]),
                })
    return befunde


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pfade", nargs="*", help="Bilder oder Ordner; ohne Angabe das Register")
    ap.add_argument("--alle", action="store_true", help="alle Bilder in uploads/ und assets/images/")
    ap.add_argument("--platzierung", action="store_true",
                    help="prueft die Canvas-Vorlagen: ueberlebt der Vermerk den Beschnitt, "
                         "mit dem das Motiv dort platziert ist?")
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

    if args.platzierung:
        befunde = pruefe_platzierung(reg)
        print("Platzierung der KI-Motive in %s\n" % CANVAS_DIR.relative_to(WURZEL))
        if not befunde:
            print("Der Vermerk ueberlebt in allen Platzierungen den Beschnitt.")
            return 0
        for b in befunde:
            sx0, sx1, sy0, sy1 = b["sichtbar"]
            vx0, vx1, vy0, vy1 = b["vermerk"]
            print("  ✗ %-24s %s" % (b["vorlage"], Path(b["motiv"]).name))
            print("      Kasten %.0f × %.0f mm — sichtbar x %.1f–%.1f %%, y %.1f–%.1f %%"
                  % (b["kasten"][0], b["kasten"][1], 100*sx0, 100*sx1, 100*sy0, 100*sy1))
            print("      Vermerk liegt bei x %.1f–%.1f %%, y %.1f–%.1f %% — weggeschnitten"
                  % (100*vx0, 100*vx1, 100*vy0, 100*vy1))
        print("\n%d Platzierung(en) schneiden den Vermerk weg." % len(befunde))
        print("Ein Vermerk, den der Kasten entfernt, erfuellt die Kennzeichnungspflicht nicht.")
        print("Abhilfe nach brand.json, ai_generated_images.cropping: der Bildausschnitt")
        print("wandert, nicht der Kasten — also eine eigene, zugeschnittene und dann")
        print("gestempelte Fassung je Platzierung.")
        return 0

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
