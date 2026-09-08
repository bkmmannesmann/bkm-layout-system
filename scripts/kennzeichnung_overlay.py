#!/usr/bin/env python3
"""Legt den Vermerk „AI GENERATED“ über den Bildkasten, statt ihn ins Motiv zu rechnen.

    python3 scripts/kennzeichnung_overlay.py                 # prüfen
    python3 scripts/kennzeichnung_overlay.py --setzen        # fehlende ergänzen
    python3 scripts/kennzeichnung_overlay.py --entfernen     # alle wieder herausnehmen

Warum überhaupt. Der Vermerk steht im Motiv, in einer Ecke mit rund einem Prozent
Randabstand. Ein Layoutkasten mit object-fit:cover schneidet zentral weg, was
übersteht — und trifft damit als Erstes diese Ecke. Im Bestand war der Vermerk
dadurch in allen einundzwanzig Platzierungen unsichtbar.

Ein Vermerk am Motiv, den der Kasten entfernt, erfüllt die Kennzeichnungspflicht
nicht: im Dokument ist er nicht da. Deshalb wird er zusätzlich als eigenes Element
über den Kasten gelegt. Beides zusammen: die Datei trägt ihn für den Fall, dass
das Motiv weitergereicht wird, das Dokument zeigt ihn unabhängig vom Beschnitt.

Grösse und Lage richten sich nach dem Kasten, nicht nach dem Motiv — der Kasten
ist das, was der Leser sieht. Die Ecke entscheidet der Kontrast des sichtbaren
Ausschnitts, nicht der des ganzen Bildes: über den weggeschnittenen Teil sagt eine
Kontrastmessung nichts aus, was für das Dokument gälte.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kennzeichnung as K  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent
CANVAS_DIR = WURZEL / "templates" / "brochure"
REGISTER = WURZEL / "assets" / "kennzeichnung" / "register.json"
SVG_REL = "assets/kennzeichnung/bkm-ai-generated.svg"

# Der Vermerk gehört über alles, was im Bildkasten liegen kann. Ein fester hoher
# Wert ist ehrlicher als ein aus dem Bild abgeleiteter: dort steht z-index:1, und
# darüber liegen im Titelblatt bereits Hero-Grafik und Logo.
Z_INDEX = 90

# Unterhalb dieses Werts traegt keine Ecke des sichtbaren Ausschnitts die weisse
# Marke mehr. Siehe brand.json, ai_generated_images.check.kontrast_skala.
KONTRAST_MIN = 0.45

BILD = re.compile(r'<img(?![^>]*\bdata-ki-vermerk)[^>]*\bsrc="([^"]+)"[^>]*\bstyle="([^"]*)"[^>]*>')
OVERLAY = re.compile(r'\s*<img data-ki-vermerk[^>]*>')


def _mm(stil: str, name: str):
    """Eine Laengenangabe in Millimetern, oder None.

    Die Vorlagen schreiben eine Null ohne Einheit — left:0 statt left:0mm.
    Andere Einheiten werden nicht umgerechnet, sondern verweigert: px oder
    Prozent haengen an Kontext, den diese Datei nicht hergibt, und ein
    geratener Wert saesse am Ende als Vermerk an der falschen Stelle.
    """
    m = re.search(r"\b" + name + r":\s*(-?[\d.]+)(mm|px|%)?(?=[;\"]|$)", stil)
    if not m:
        return None
    wert, einheit = float(m.group(1)), m.group(2)
    if einheit == "mm":
        return wert
    return 0.0 if wert == 0 else None


def register() -> set[str]:
    if not REGISTER.exists():
        return set()
    return set(json.loads(REGISTER.read_text(encoding="utf-8")).get("ki_motive", []))


def sichtbarer_ausschnitt(bild_v: float, kasten_v: float, cover: bool):
    """Anteil des Motivs, der im Kasten stehen bleibt: (x0, x1, y0, y1) in 0..1."""
    if not cover:
        return (0.0, 1.0, 0.0, 1.0)
    if bild_v > kasten_v:
        b, h = kasten_v / bild_v, 1.0
    else:
        b, h = 1.0, bild_v / kasten_v
    return ((1 - b) / 2, 1 - (1 - b) / 2, (1 - h) / 2, 1 - (1 - h) / 2)


def marke_im_kasten(kb_mm: float, regel: dict) -> tuple[float, float, float]:
    """Breite, Höhe und Randabstand der Marke im Kasten, in Millimetern."""
    breite = max(kb_mm * regel["breite_anteil"], float(regel["mindestbreite_mm"]))
    breite = min(breite, kb_mm * 0.9)
    return breite, breite / K.SEITENVERHAELTNIS, kb_mm * regel["rand_anteil"]


def ecke_im_ausschnitt(pfad: Path, ausschnitt, regel: dict) -> tuple[str, float]:
    """Welche Ecke des sichtbaren Ausschnitts trägt die weisse Marke am besten?"""
    im = Image.open(pfad).convert("L")
    w, h = im.size
    x0, x1, y0, y1 = ausschnitt
    teil = im.crop((int(x0 * w), int(y0 * h), max(1, int(x1 * w)), max(1, int(y1 * h))))
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        teil.save(f.name)
        rang = K.beste_ecke(f.name, regel)
    Path(f.name).unlink(missing_ok=True)
    return rang[0]["ecke"], rang[0]["eignung"]


# Eigenschaften, die das Bild im Elternlayout verankern. Sie muessen an den
# Rahmen wandern, sonst steht er dort anders als das Bild vorher.
UEBERNEHMEN = ("flex", "flex-grow", "flex-shrink", "flex-basis", "align-self",
               "justify-self", "order", "grid-area", "grid-column", "grid-row",
               "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
               "width", "height", "max-width", "max-height", "min-width", "min-height")


def overlay_absolut(kasten, ecke: str, regel: dict) -> str:
    """Der Vermerk als Geschwister eines absolut gesetzten Bildes.

    Das Bild kennt seine Lage auf der Seite in Millimetern, also laesst sich der
    Vermerk daneben stellen, ohne die Baumstruktur anzufassen. Der schonendste
    Weg — er aendert am Dokument nichts ausser einem zusaetzlichen Element.
    """
    left, top, kb, kh = kasten
    mb, mh, rand = marke_im_kasten(kb, regel)
    x = left + kb - rand - mb if "rechts" in ecke else left + rand
    y = top + kh - rand - mh if "unten" in ecke else top + rand
    return ('<img data-ki-vermerk="1" loading="lazy" decoding="async" src="%s" '
            'alt="AI GENERATED" style="position:absolute;left:%.2fmm;top:%.2fmm;'
            'width:%.2fmm;height:%.2fmm;z-index:%d;pointer-events:none;display:block">'
            % (SVG_REL, x, y, mb, mh, Z_INDEX))


def overlay_rahmen(bild_tag: str, bild_stil: str, ecke: str, regel: dict) -> str:
    """Der Vermerk in einem Rahmen um ein im Fluss stehendes Bild.

    Ein Bild mit width:100% oder calc(100% + 8mm) kennt seine Lage auf der Seite
    nicht — sie ergibt sich erst aus dem Elternelement. Ohne einen Bezugspunkt
    laesst sich nichts darueber legen, also bekommt es einen: einen Rahmen mit
    position:relative, in dem der Vermerk prozentual sitzt.

    Die Groessenregel steht dabei im CSS statt im Millimeterwert — width:9,5 %
    mit min-width auf dem Mindestmass ist genau „der groessere der beiden Werte“,
    und zwar bezogen auf den Kasten, in dem das Bild am Ende wirklich steht.
    """
    eigenschaften = []
    rest = bild_stil
    for name in UEBERNEHMEN:
        m = re.search(r"(?:^|;)\s*(" + re.escape(name) + r"\s*:[^;]+)", rest)
        if m:
            eigenschaften.append(m.group(1).strip())
            rest = rest[:m.start(1)] + rest[m.end(1):]
    innen = re.sub(r";\s*;", ";", rest).strip("; ")
    innen = "width:100%;height:100%;" + innen if innen else "width:100%;height:100%"

    rahmen = "position:relative;display:block;" + ";".join(eigenschaften)
    lage = ("right:%.2f%%;" % (100 * regel["rand_anteil"])) if "rechts" in ecke \
        else ("left:%.2f%%;" % (100 * regel["rand_anteil"]))
    lage += ("bottom:%.2f%%;" % (100 * regel["rand_anteil"] * K.SEITENVERHAELTNIS)) \
        if "unten" in ecke else ("top:%.2f%%;" % (100 * regel["rand_anteil"] * K.SEITENVERHAELTNIS))

    neues_bild = re.sub(r'\bstyle="[^"]*"', 'style="%s"' % innen, bild_tag, count=1)
    vermerk = ('<img data-ki-vermerk="1" loading="lazy" decoding="async" src="%s" '
               'alt="AI GENERATED" style="position:absolute;%swidth:%.1f%%;'
               'min-width:%gmm;height:auto;z-index:%d;pointer-events:none;display:block">'
               % (SVG_REL, lage, 100 * regel["breite_anteil"],
                  regel["mindestbreite_mm"], Z_INDEX))
    return ('<span data-ki-rahmen="1" style="%s">%s%s</span>'
            % (rahmen, neues_bild, vermerk))


# Ein bereits gesetzter Vermerk steht unmittelbar hinter seinem Bild — bei beiden
# Wegen: als Geschwister daneben, oder als zweites Kind im Rahmen.
SCHON_VERSEHEN = re.compile(r'\s*<img data-ki-vermerk')


def stellen(text: str, ki: set[str], regel: dict):
    """Alle Platzierungen von KI-Motiven, die noch keinen Vermerk tragen."""
    for m in BILD.finditer(text):
        if SCHON_VERSEHEN.match(text[m.end():m.end() + 40]):
            continue
        quelle, stil = m.group(1), m.group(2)
        if quelle not in ki or not (WURZEL / quelle).exists():
            continue
        cover = "object-fit:cover" in stil.replace(" ", "")
        left, top = _mm(stil, "left"), _mm(stil, "top")
        kb, kh = _mm(stil, "width"), _mm(stil, "height")
        absolut = ("position:absolute" in stil.replace(" ", "")
                   and None not in (left, top, kb, kh) and kb > 0 and kh > 0)
        yield m, quelle, (left, top, kb, kh) if absolut else None, cover, kb, kh


_LAGEN: dict[str, tuple] = {}


def vermerklage(pfad: Path):
    """Wo steht der ins Motiv gebrannte Vermerk? (x0, x1, y0, y1) in 0..1, oder None."""
    schluessel = str(pfad)
    if schluessel not in _LAGEN:
        t = K.finde(pfad)
        if not t["gefunden"]:
            _LAGEN[schluessel] = None
        else:
            bw, bh = t["bild"]
            x, y, tb, th = t["kasten"]
            _LAGEN[schluessel] = (x / bw, (x + tb) / bw, y / bh, (y + th) / bh)
    return _LAGEN[schluessel]


def beschnitt_zustand(lage, ausschnitt) -> str:
    """Was der Layoutkasten mit dem Vermerk im Motiv macht.

    Drei Faelle, und jeder verlangt etwas anderes. Steht er ganz im Bild, ist
    nichts zu tun. Ist er ganz weg, tritt der Vermerk ueber dem Kasten an seine
    Stelle. Ist er angeschnitten, bleibt ein Rest stehen, den kein Element
    darueber verdecken kann — es hat selbst Randabstand. Der Fall gehoert in die
    Bildredaktion und wird deshalb gemeldet, nicht stillschweigend uebermalt.
    """
    if lage is None:
        return "kein Vermerk im Motiv"
    vx0, vx1, vy0, vy1 = lage
    sx0, sx1, sy0, sy1 = ausschnitt
    if vx0 >= sx0 and vx1 <= sx1 and vy0 >= sy0 and vy1 <= sy1:
        return "ganz sichtbar"
    if vx1 <= sx0 or vx0 >= sx1 or vy1 <= sy0 or vy0 >= sy1:
        return "ganz weg"
    return "angeschnitten"


def bearbeite(datei: Path, ki: set[str], regel: dict, setzen: bool):
    """Prüft eine Canvas-Datei und ergänzt fehlende Vermerke, wenn setzen."""
    text = datei.read_text(encoding="utf-8")
    vorhanden = len(OVERLAY.findall(text))
    einfuegungen, berichte, offen = [], [], []

    for m, quelle, kasten, cover, kb, kh in stellen(text, ki, regel):
        im = Image.open(WURZEL / quelle)
        # Nur das Verhaeltnis des Kastens zaehlt fuer den Beschnitt. Steht es nicht
        # in Millimetern, ist wenigstens das Verhaeltnis oft ablesbar; sonst wird
        # der ganze Ausschnitt bewertet.
        bekannt = bool(kb and kh)
        kv = (kb / kh) if bekannt else im.width / im.height
        aus = sichtbarer_ausschnitt(im.width / im.height, kv, cover)

        # Was macht der Beschnitt mit dem Vermerk, der schon im Motiv steht?
        # Laesst er ihn ganz stehen, waere ein zweiter darueber eine Doppelung —
        # dann bleibt die Platzierung, wie sie ist.
        #
        # Steht die Kastengroesse nicht in Millimetern — width:100 %, calc(…) —,
        # ergibt sie sich erst aus dem Elternelement und der Beschnitt ist von hier
        # aus nicht zu berechnen. Dann wird der Vermerk gesetzt: eine Doppelung ist
        # ein Schoenheitsfehler, eine fehlende Kennzeichnung ein Rechtsverstoss.
        lage = vermerklage(WURZEL / quelle)
        zustand = beschnitt_zustand(lage, aus) if bekannt else "Beschnitt unbekannt"

        # Ein Vermerk ueber dem Kasten und einer im Motiv vertragen sich nicht.
        # An zwei Ecken lesen sie sich als zwei Kennzeichnungen; an derselben Ecke
        # ueberlagern sie sich versetzt zu einem unscharfen Doppelbild, denn ihre
        # Raender beziehen sich auf verschiedene Bezugsgroessen — der eine auf das
        # Motiv, der andere auf den Kasten. Gesetzt wird deshalb nur, wo der
        # gebrannte Vermerk sicher nicht im Bild steht.
        if zustand in ("ganz sichtbar", "angeschnitten") or (
                zustand == "Beschnitt unbekannt" and lage is not None):
            offen.append({"motiv": quelle, "vorlage": datei.name, "zustand": zustand})
            continue

        # Traegt das Motiv bereits einen Vermerk, uebernimmt der neue dessen Ecke.
        # Zwei Zeichen an zwei Ecken lesen sich als zwei Kennzeichnungen; an
        # derselben Ecke ueberlagern sie sich zu einer. Die Ecke ist ausserdem
        # schon nach Kontrast gewaehlt worden, als der Vermerk ins Motiv kam.
        ecke, eignung = ecke_im_ausschnitt(WURZEL / quelle, aus, regel)

        if kasten:
            mb, _, _ = marke_im_kasten(kasten[2], regel)
            einfuegungen.append(("nach", m.end(), overlay_absolut(kasten, ecke, regel)))
            weg, breite = "daneben", "%.1f mm" % mb
        else:
            einfuegungen.append(("ersetzen", (m.start(), m.end()),
                                 overlay_rahmen(m.group(0), m.group(2), ecke, regel)))
            weg, breite = "im Rahmen", "%.1f %% / min %g mm" % (
                100 * regel["breite_anteil"], regel["mindestbreite_mm"])
        berichte.append({"motiv": quelle, "kasten": (kb, kh), "ecke": ecke,
                         "eignung": eignung, "marke": breite, "weg": weg,
                         "zustand": zustand})

    if setzen and einfuegungen:
        neu = text
        # Von hinten nach vorn einsetzen, damit die frueheren Positionen gueltig bleiben.
        def anfang(eintrag):
            wo = eintrag[1]
            return wo[0] if isinstance(wo, tuple) else wo

        for art, wo, tag in sorted(einfuegungen, key=anfang, reverse=True):
            if art == "nach":
                neu = neu[:wo] + tag + neu[wo:]
            else:
                a, b = wo
                neu = neu[:a] + tag + neu[b:]
        datei.write_text(neu, encoding="utf-8")
    return berichte, vorhanden, offen


def entferne(datei: Path) -> int:
    text = datei.read_text(encoding="utf-8")
    neu, anzahl = OVERLAY.subn("", text)
    if anzahl:
        datei.write_text(neu, encoding="utf-8")
    return anzahl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dateien", nargs="*", help="Canvas-Dateien; ohne Angabe templates/brochure/*.dc.html")
    ap.add_argument("--setzen", action="store_true", help="fehlende Vermerke ergänzen")
    ap.add_argument("--entfernen", action="store_true", help="gesetzte Vermerke herausnehmen")
    args = ap.parse_args()

    dateien = [Path(d) for d in args.dateien] or sorted(CANVAS_DIR.glob("*.dc.html"))
    regel = K.regeln()
    ki = register()

    if args.entfernen:
        gesamt = sum(entferne(d) for d in dateien)
        print("%d Vermerk-Element(e) entfernt." % gesamt)
        return 0

    print("Vermerk über dem Bildkasten — %d Datei(en)\n" % len(dateien))
    gesamt = schon = 0
    offene = []
    for datei in dateien:
        berichte, vorhanden, offen = bearbeite(datei, ki, regel, args.setzen)
        offene.extend(offen)
        if not berichte and not vorhanden:
            continue
        print("  %s" % datei.name)
        for b in berichte:
            kb, kh = b["kasten"]
            masse = "%.0f × %.0f mm" % (kb, kh) if kb and kh else "im Fluss"
            warn = "  ← kein Kontrast" if b["eignung"] < KONTRAST_MIN else ""

            print("     %-46s %-12s %-9s Marke %-18s %s (%.2f)%s"
                  % (Path(b["motiv"]).name[:46], masse, b["weg"], b["marke"],
                     b["ecke"].replace("_", " "), b["eignung"], warn))
        if vorhanden:
            print("     %d Vermerk(e) bereits gesetzt" % vorhanden)
        gesamt += len(berichte)
        schon += vorhanden
        print()

    if offene:
        import collections
        nach_grund = collections.Counter(o["zustand"] for o in offene)
        print("%d Platzierung(en) bleiben unberuehrt, weil das Motiv den Vermerk selbst traegt:"
              % len(offene))
        for grund, n in nach_grund.most_common():
            print("   %2d × %s" % (n, grund))
        print("   Bei „ganz sichtbar\" ist nichts zu tun. Bei „angeschnitten\" bleibt ein Rest")
        print("   des gebrannten Vermerks stehen — diese Faelle brauchen einen anderen")
        print("   Bildausschnitt. Bei unbekanntem Beschnitt laesst sich von hier aus nicht")
        print("   entscheiden, ob eine Doppelung entstuende.\n")
    if args.setzen:
        print("%d Vermerk(e) gesetzt, %d waren schon da." % (gesamt, schon))
    elif gesamt:
        print("%d Platzierung(en) ohne Vermerk über dem Kasten, %d schon versehen." % (gesamt, schon))
        print("Setzen mit --setzen.")
    else:
        print("Alle %d Platzierungen tragen den Vermerk über dem Kasten." % schon)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
