#!/usr/bin/env python3
"""Prueft ein aus dem Design-Canvas exportiertes PDF gegen brand.json.

    python3 scripts/check_export.py <datei.pdf>
    python3 scripts/check_export.py <datei.pdf> --leise    # nur Fehler

Gedacht fuer die Abstimmungsfassung: das PDF, das der Browser beim Export
erzeugt. Es findet, was man dem fertigen Dokument nicht ansieht.

Der Anlass: In einem Export standen rund 4000 von 4200 Textstellen in der
macOS-Systemschrift statt in TT Norms Pro. Chrome kann San Francisco nicht
reglaer einbetten und legt sie als Type3 ab. Am Bildschirm faellt das kaum auf,
die Headlines waren korrekt, und fuenf Runden lang hat es niemand bemerkt.

Die Sollwerte stammen aus brand.json, nicht aus diesem Skript. Wer eine Regel
aendert, aendert sie dort.

Braucht pymupdf. Das ist eine reine Pruefabhaengigkeit; die Bauskripte
kommen ohne aus.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
BRAND_PATH = ROOT_DIR / "brand.json"

# Schriftfamilien, die im Export stehen duerfen. Alles andere heisst, dass der
# Browser eine Datei nicht laden konnte und still ersetzt hat.
MARKENSCHRIFTEN = ("Unbounded", "TTNormsPro", "TT-Norms", "TT_Norms", "Liberation",
                   "BKM-PDF-Sans")

# Toleranzen in mm.
KANTE = 0.6        # Rundung in der Textmatrix
BLATT = 0.5        # Browser drucken 209,89 statt 210 - das ist kein Fehler
DPI_MIN = 220      # darunter wird es im Druck sichtbar
BLEED_SAFE = 285.0 # tiefste Grundlinie auf einer Seite ohne Seitenzahl

# Toene, ueber die noch nicht entschieden ist. Leer, solange die Palette
# vollstaendig ist - ein unbekannter Ton ist dann ein Fehler.
UNGEKLAERTE_TOENE: dict[str, str] = {}


def mm(punkte: float) -> float:
    return punkte / 72 * 25.4


def lade_brand() -> dict:
    return json.loads(BRAND_PATH.read_text(encoding="utf-8"))


def spans(seite):
    """Alle Textstellen einer Seite."""
    for block in seite.get_text("dict")["blocks"]:
        for zeile in block.get("lines", []):
            for span in zeile["spans"]:
                if span["text"].strip():
                    yield span


def hat_folio(seite) -> str | None:
    """Die Seitenzahl aus dem Kolumnentitel, falls die Seite eine traegt.

    Der Canvas setzt sie oben - eine Zeile mit Rubrik und Ziffer, auf Recto
    rechts, auf Verso links. Gesucht wird deshalb nur im oberen Bereich; eine
    Ziffer weiter unten ist ein Verweis im Inhaltsverzeichnis oder eine
    Telefonnummer.

    Der Produktionspfad setzt die Ziffer dagegen in den Fusssteg. Dieses Skript
    prueft Canvas-Exporte; fuer den Innenteil aus build_pages.py findet es
    deshalb keine Ziffer und laesst die Paginierung ungeprueft. Dort deckt
    validate_brochure.py den Fall ueber page_number_start ab.
    """
    for span in spans(seite):
        text = span["text"].strip()
        if text.isdigit() and len(text) <= 3 and mm(span["origin"][1]) < 40:
            return text
    return None


def pruefe(pfad: Path, brand: dict) -> tuple[list[str], list[str]]:
    import pymupdf

    fehler, hinweise = [], []
    doc = pymupdf.open(str(pfad))

    raster = brand["grid"]["interior"]
    achse = float(raster["margin_x_mm"])
    kopf = float(raster["margin_top_mm"])
    fuss = float(raster["margin_bottom_mm"])
    breite_soll, hoehe_soll = 210.0, 297.0
    satz_unten = hoehe_soll - fuss                      # mit Ziffer: der Fusssteg
    # Ohne Ziffer greift die Ausnahme aus docs/BROSCHUERE-CANVAS.md: dort ist
    # nur der Beschnitt die Grenze. Derselbe Wert wie BLEED_SAFE in
    # build_pages.py, damit Canvas und Produktion gleich streng sind.
    satz_unten_frei = BLEED_SAFE

    palette = {v["hex"].lower(): k for k, v in brand["colors"].items()
               if isinstance(v, dict) and "hex" in v}

    # --- Blattmass ---------------------------------------------------------
    for i, seite in enumerate(doc, 1):
        b, h = mm(seite.rect.width), mm(seite.rect.height)
        if abs(b - breite_soll) > BLATT or abs(h - hoehe_soll) > BLATT:
            fehler.append(f"Seite {i}: Blattmass {b:.2f} x {h:.2f} mm statt 210 x 297")
    erste = doc[0]
    if abs(mm(erste.rect.width) - breite_soll) > 0.05:
        hinweise.append(
            f"Blattmass {mm(erste.rect.width):.2f} x {mm(erste.rect.height):.2f} mm - "
            f"Browser drucken minimal knapp. Fuer den Druck laeuft der Weg ueber "
            f"WeasyPrint mit Beschnittzugabe.")

    # --- Schriften ---------------------------------------------------------
    # Type3 wird zusammengefasst: der Browser legt jede Schnittvariante als
    # eigenes Objekt ab, das ergaebe vierzig Zeilen fuer einen Befund.
    fremd, type3_spans, type3_seiten, echte = {}, 0, set(), 0
    ersatzname = None
    for i, seite in enumerate(doc, 1):
        for f in seite.get_fonts(full=True):
            if f[2] == "Type3":
                type3_seiten.add(i)
                if ersatzname is None:
                    besch = doc.xref_object(f[0])
                    import re as _re
                    m = _re.search(r"/FontDescriptor (\d+) 0 R", besch)
                    if m:
                        fam = _re.search(r"/FontFamily \(([^)]*)\)",
                                         doc.xref_object(int(m.group(1))))
                        if fam:
                            ersatzname = fam.group(1)
        for span in spans(seite):
            name = span["font"]
            if any(name.startswith(x) for x in MARKENSCHRIFTEN):
                echte += 1
            elif name.startswith("Type3"):
                type3_spans += 1
            else:
                fremd.setdefault(name, [0, i])
                fremd[name][0] += 1
    if type3_spans:
        woher = f" Die Ersatzschrift ist {ersatzname!r}." if ersatzname else ""
        fehler.append(
            f"{type3_spans} Textstelle(n) auf {len(type3_seiten)} Seite(n) stehen in "
            f"einer Type3-Schrift, nur {echte} in einer Markenschrift. So legt der "
            f"Browser eine Schrift ab, die er nicht regulaer einbetten kann - in aller "
            f"Regel die Systemschrift als Ersatz fuer eine Markenschrift, die nicht "
            f"geladen wurde.{woher}")
    for name, (anzahl, erste_seite) in sorted(fremd.items(), key=lambda kv: -kv[1][0]):
        fehler.append(
            f"Fremdschrift {name!r}: {anzahl} Textstelle(n), zuerst auf Seite "
            f"{erste_seite}")

    # --- Satzspiegel -------------------------------------------------------
    for i, seite in enumerate(doc, 1):
        folio = hat_folio(seite)
        grenze = satz_unten if folio else satz_unten_frei
        links = rechts = None
        tiefste = None
        for span in spans(seite):
            x0, x1 = mm(span["bbox"][0]), mm(span["bbox"][2])
            y = mm(span["origin"][1])
            links = x0 if links is None else min(links, x0)
            rechts = x1 if rechts is None else max(rechts, x1)
            if tiefste is None or y > tiefste[0]:
                tiefste = (y, span["text"].strip()[:44])
        if links is None:
            continue
        if links < achse - KANTE:
            fehler.append(f"Seite {i}: Satz beginnt bei {links:.2f} mm, Achse ist {achse}")
        if rechts > breite_soll - achse + KANTE:
            fehler.append(f"Seite {i}: Satz endet bei {rechts:.2f} mm, erlaubt bis "
                          f"{breite_soll - achse}")
        if tiefste and tiefste[0] > grenze + KANTE:
            wo = f"Fusssteg {fuss} mm" if folio else "Beschnitt"
            fehler.append(
                f"Seite {i}: Grundlinie {tiefste[0]:.2f} mm, erlaubt bis {grenze:.1f} "
                f"({wo}, Seitenzahl: {folio or 'keine'}): {tiefste[1]!r}")

    # --- Paginierung -------------------------------------------------------
    # Titel und Rueckseite zaehlen nicht mit. Das erste Blatt nach dem Titel
    # traegt damit Ziffer 1, und auf Blatt N steht N-1 - auch dann, wenn eine
    # der vorderen Seiten ihre Ziffer ueber no_folio unterdrueckt. Genau hier
    # lag der Fehler: das Titelblatt wurde mitgezaehlt, deshalb stand auf
    # Blatt 3 die 03 statt der 02.
    folios = [(i, hat_folio(seite)) for i, seite in enumerate(doc, 1)]
    beziffert = [(i, f) for i, f in folios if f]
    for blatt, ziffer in beziffert:
        soll = blatt - 1
        if int(ziffer) != soll:
            fehler.append(
                f"Seite {blatt} traegt die Ziffer {ziffer}, erwartet {soll:02d}. "
                f"Titel und Rueckseite zaehlen nicht mit, deshalb ist die Ziffer "
                f"immer die Blattnummer minus eins.")
            break        # ein Versatz zieht sich durch, eine Meldung genuegt
    if beziffert:
        luecken = [b for b, _ in beziffert]
        fehlend = [b for b in range(min(luecken), max(luecken) + 1) if b not in luecken]
        if fehlend:
            hinweise.append(
                f"Ohne Ziffer zwischen den bezifferten Seiten: Blatt "
                f"{', '.join(map(str, fehlend))}. Zulaessig, wenn sie still "
                f"mitzaehlen - dann muss die Folge danach weiterlaufen.")

    # --- Farben ------------------------------------------------------------
    gesehen = {}
    for i, seite in enumerate(doc, 1):
        for span in spans(seite):
            h = f"#{span['color']:06x}"
            gesehen.setdefault(h, [0, i])
            gesehen[h][0] += 1
    for h, (anzahl, erste_seite) in sorted(gesehen.items(), key=lambda kv: -kv[1][0]):
        if h in palette:
            continue
        if h in UNGEKLAERTE_TOENE:
            hinweise.append(f"Textfarbe {h}: {anzahl} Stelle(n) - {UNGEKLAERTE_TOENE[h]}")
        else:
            fehler.append(f"Textfarbe {h} steht nicht in der Palette: {anzahl} "
                          f"Stelle(n), zuerst auf Seite {erste_seite}")

    # --- Bilder ------------------------------------------------------------
    for i, seite in enumerate(doc, 1):
        blatt_b, blatt_h = mm(seite.rect.width), mm(seite.rect.height)
        for info in seite.get_image_info(xrefs=True):
            x0, y0, x1, y1 = (mm(v) for v in info["bbox"])
            b, h = x1 - x0, y1 - y0
            if b < 20 or h < 20:      # Icons und Siegel
                continue
            dpi = info["width"] / (b / 25.4) if b else 0
            if dpi < DPI_MIN:
                hinweise.append(
                    f"Seite {i}: Bild {info['width']}x{info['height']} px auf "
                    f"{b:.0f}x{h:.0f} mm = {dpi:.0f} dpi")
            # Welcher Teil des Bildes bleibt sichtbar? Der KI-Vermerk steckt im
            # Bild selbst; welche Ecke ihn tragen kann, haengt an dieser Lage.
            # Das Bild wird dafuer nicht ins Format gepresst - es wird
            # ausgerichtet oder der Vermerk woanders gesetzt.
            weg_l, weg_r = max(0.0, -x0), max(0.0, x1 - blatt_b)
            weg_o, weg_u = max(0.0, -y0), max(0.0, y1 - blatt_h)
            if max(weg_l, weg_r, weg_o, weg_u) > 0.5:
                ecken = []
                for name, dx, dy in (("oben links", weg_l, weg_o),
                                     ("oben rechts", weg_r, weg_o),
                                     ("unten links", weg_l, weg_u),
                                     ("unten rechts", weg_r, weg_u)):
                    ecken.append((name, dx <= 0.5 and dy <= 0.5))
                sichtbar = [n for n, ok in ecken if ok]
                verloren = [n for n, ok in ecken if not ok]
                kanten = ", ".join(
                    f"{s} {v:.0f} mm" for v, s in
                    ((weg_l, "links"), (weg_r, "rechts"), (weg_o, "oben"), (weg_u, "unten"))
                    if v > 0.5)
                hinweise.append(
                    f"Seite {i}: Bild beschnitten ({kanten}). Fuer den KI-Vermerk "
                    f"nutzbar: {', '.join(sichtbar) if sichtbar else 'keine Ecke'}"
                    f"{' — verdeckt: ' + ', '.join(verloren) if verloren else ''}.")

    # --- KI-Vermerk --------------------------------------------------------
    volltext = " ".join(seite.get_text() for seite in doc).lower()
    if "ki-generiert" in volltext or "ai generated" in volltext:
        hinweise.append(
            "Ein KI-Vermerk steht im Text. Beschlossen ist der Vermerk im Bild "
            "selbst, nicht als Sammelangabe - pruefe, ob beides gemeint ist.")

    doc.close()
    return fehler, hinweise


def main() -> int:
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    leise = "--leise" in sys.argv[1:]
    if not argumente:
        print(__doc__.strip().split("\n\n")[1])
        return 2
    pfad = Path(argumente[0])
    if not pfad.is_file():
        print(f"Datei nicht gefunden: {pfad}")
        return 2

    try:
        import pymupdf  # noqa: F401
    except ImportError:
        print("pymupdf fehlt:  pip install pymupdf")
        return 2

    fehler, hinweise = pruefe(pfad, lade_brand())

    print(f"{pfad.name}")
    if fehler:
        print(f"\n{len(fehler)} Verstoss(e):")
        for f in fehler:
            print(f"  - {f}")
    if hinweise and not leise:
        print(f"\n{len(hinweise)} Hinweis(e):")
        for h in hinweise:
            print(f"  - {h}")
    if not fehler:
        print("\nKeine Verstoesse. Die Sollwerte stehen in brand.json.")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
