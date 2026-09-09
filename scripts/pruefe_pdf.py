#!/usr/bin/env python3
"""Prueft ein fertiges PDF gegen den Layoutvertrag - gleich, wer es gebaut hat.

Der Bau im Repo prueft, was er selbst erzeugt. Der Weg ueber Claude Design
geht daran vorbei: am 03.09.2026 kam eine Broschuere zurueck, in der die
Blattbeschriftung des Canvas mitgedruckt war, dreizehn Seiten Text unter
dem Fusssteg trugen und auf einer Seite Woerter mitten durchbrachen -
'Technologi/emarke'. Jeder dieser Fehler waere im Repo-Bau gemeldet
worden. Er lief nur nicht.

Diese Pruefung nimmt darum ein beliebiges PDF:

    python3 scripts/pruefe_pdf.py broschuere.pdf
    python3 scripts/pruefe_pdf.py anleitung.pdf --art anleitung

Sie aendert nichts. Sie misst und meldet.
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

try:
    import pyphen
except ImportError:                                   # pragma: no cover
    pyphen = None

ROOT_DIR = Path(__file__).parent.parent.resolve()
MM = 72 / 25.4

# Satzspiegel je Dokumentart. Die Broschuerenwerte stehen in
# templates/pages/pages-spec.css als die vier Eingaben des Rasters, die
# der Anleitung in brand.json unter grid.anleitung.
GEOMETRIE = {
    "broschuere": {"links": 18.0, "rechts": 192.0, "oben": 26.7, "unten": 273.5},
    # Der Innenteil aus dem Canvas seit dem 07.09.2026: Beiwerk steht unten,
    # oben ist kein Kopfsteg mehr fuer Kolumnentitel noetig. Der Druckweg
    # unter 'broschuere' faehrt weiter 26,7 und 273,5 - wer ein PDF aus
    # scripts/build_pages.py prueft, nimmt jenen Schluessel.
    "innenteil":  {"links": 18.0, "rechts": 192.0, "oben": 18.0, "unten": 276.0},
    "anleitung":  {"links": 18.0, "rechts": 192.0, "oben": 18.0, "unten": 277.0},
}
BLATT_HOEHE = 297.0
BLATT_BREITE = 210.0

# Rundung beim Umrechnen von Punkt in Millimeter und der Ueberhang
# justierter Zeilen. Darunter ist es keine Abweichung, darueber schon.
TOLERANZ = 0.6

# Am Kopfsteg braucht es mehr: der Blockrahmen einer Zeile umfasst die
# ganze Zeilenbox, nicht die Grundlinie. Eine Unbounded-Rubrik, die
# vertragsgemaess bei 18 mm beginnt, misst darum 17,4 mm. 1,5 mm deckt
# das ab und laesst eine echte Abweichung von 2 mm noch auffallen.
TOLERANZ_OBEN = 1.5

# An der rechten Fluchtlinie ebenso, aus einem anderen Grund: der
# Blockrahmen der Textextraktion umfasst den Vorschub des letzten
# Glyphen, nicht seine Schwaerze. Am 03.09.2026 nachgemessen - die
# Extraktion meldete 192,80 mm, die rechteste dunkle Bildspalte lag bei
# 191,96 mm, also genau auf der Linie. Ueber alle acht Anleitungen war
# der groesste solche Ueberhang 0,90 mm. Ab 1,0 mm steht wirklich Tinte
# im Rand.
TOLERANZ_RECHTS = 1.0

# Wortabstand im Blocksatz. Ein Setzer laesst den Zwischenraum zwischen
# vier Fuenfteln und vier Dritteln seiner natuerlichen Breite laufen;
# InDesign hat 80/100/133 Prozent als Vorgabe. Darueber sieht man die
# Luecke, ab dem Doppelten reisst sie ein Loch in die Spalte. Gemessen
# wird gegen die Breite, die die eingebettete Schrift selbst fuer das
# Leerzeichen angibt - nicht gegen einen Mittelwert aus dem Dokument,
# denn wenn die Haelfte aller Zeilen gedehnt ist, waere der Mittelwert
# schon mitgedehnt und die Messung schoenrechnend.
ABSTAND_AUFFAELLIG = 1.33
ABSTAND_LOCH = 2.0

# Kurze Zeilen sind Ueberschriften, Bildunterschriften und Tabellenzellen.
# Fuer eine Aussage ueber den Blocksatz braucht es eine gefuellte Zeile.
ABSTAND_MIN_ZEICHEN = 20
ABSTAND_MIN_LUECKEN = 3

# Blattbeschriftungen aus Canvas-Werkzeugen. U2 bis U4 sind die
# Umschlagseiten - als Satzbegriff richtig, auf dem Blatt nicht.
# Das Impressum. Steht in allen drei Dokumentarten im Fusssteg und ist
# dort richtig.
# Erstelldatum steht seit dem 09.09.2026 in den Verarbeitungsanleitungen,
# vorher stand dort Ausgegeben am. Beides bleibt erkannt, damit aeltere
# Ausgaben nicht ploetzlich als impressumlos gelten.
IMPRESSUM = re.compile(r"Copyright|Erstelldatum|Ausgegeben am|All rights reserved",
                       re.IGNORECASE)

MARKER = re.compile(r"(?:^|\s)(U[234]|Artboard\s*\d*|Screen\s*\d+|Frame\s*\d+)(?:\s|$)")


def seiten_geometrie(doc, art):
    geo = dict(GEOMETRIE[art])
    return geo


def check_blattformat(doc):
    fehler = []
    for i, p in enumerate(doc, 1):
        b, h = p.rect.width / MM, p.rect.height / MM
        if abs(b - BLATT_BREITE) > 1 or abs(h - BLATT_HOEHE) > 1:
            fehler.append(f"Seite {i}: {b:.0f} x {h:.0f} mm statt DIN A4.")
    return fehler


def check_canvas_marker(doc):
    """Blattbeschriftung eines Canvas-Werkzeugs im Druck.

    'U2' stand am 03.09.2026 oben rechts auf der ersten Innenseite. Es
    stand weder in der content.json noch im Template - der Canvas hat
    sein eigenes Geruest mitgedruckt, dieselbe Sorte wie die Labelleiste,
    die aus I-Anleitung.dc.html entfernt wurde.
    """
    fehler = []
    for i, p in enumerate(doc, 1):
        for treffer in set(m.group(1) for m in MARKER.finditer(p.get_text())):
            fehler.append(f"Seite {i}: Blattbeschriftung {treffer!r} steht im Dokument.")
    return fehler


def check_satzspiegel(doc, geo):
    """Text ausserhalb des Satzspiegels.

    Der Fusssteg ist keine Empfehlung: er ist das, was die Seite atmen
    laesst, und er haelt den Text vom Beschnitt weg.

    Seitenbeiwerk - Folio und Kolumnentitel - sitzt planmaessig darunter.
    Ein PDF allein sagt nicht, was Beiwerk ist und was Fliesstext.
    Unterschieden wird darum daran, dass Beiwerk sich wiederholt: was auf
    drei oder mehr Seiten an derselben Hoehe steht, ist die Fusszeile und
    wird einmal zusammengefasst statt seitenweise gemeldet. Ein einzelner
    Absatz, der dort unten landet, ist keine Fusszeile und wird gemeldet.
    """
    unter = []
    for i, p in enumerate(doc, 1):
        for b in p.get_text("blocks"):
            if not b[4].strip():
                continue
            text = re.sub(r"\s+", " ", b[4]).strip()
            if b[3] / MM > geo["unten"] + TOLERANZ:
                unter.append((i, round(b[3] / MM, 1), text))

    # Hoehen, die sich ueber mehrere Seiten wiederholen: Fusszeile.
    haeufig = {}
    for _, y, _ in unter:
        haeufig[round(y)] = haeufig.get(round(y), 0) + 1
    beiwerk = {y for y, n in haeufig.items() if n >= 3}

    fehler, hinweise = [], []
    for i, y, text in unter:
        if round(y) in beiwerk:
            continue
        # Das Impressum sitzt vertragsgemaess im Fusssteg. Erkannt wird
        # es an seinem Inhalt, nicht an seiner Position: seit die
        # Anleitungen ein Prueftprotokoll hinter dem Dokument tragen, ist
        # die Impressumsseite nicht mehr die letzte. Als Hinweis, nicht
        # als Beanstandung - sonst meldet jedes eigene Dokument dauerhaft
        # einen Fehler, den niemand beheben will, und die Meldung
        # verliert ihre Kraft.
        ist_impressum = bool(IMPRESSUM.search(text))
        ziel = hinweise if ist_impressum else fehler
        ziel.append(f"Seite {i}: Text bis {y:.1f} mm, Fusssteg endet bei "
                    f"{geo['unten']:.1f} mm: {text[:46]!r}")
    if beiwerk:
        hoehen = ", ".join(f"{y} mm" for y in sorted(beiwerk))
        hinweise.append(f"Seitenbeiwerk auf {hoehen} unter dem Satzspiegel - "
                        f"wiederholt sich ueber mehrere Seiten, vermutlich "
                        f"Folio und Kolumnentitel.")

    for i, p in enumerate(doc, 1):
        for b in p.get_text("blocks"):
            if not b[4].strip():
                continue
            text = re.sub(r"\s+", " ", b[4]).strip()[:46]
            if b[1] / MM < geo["oben"] - TOLERANZ_OBEN:
                fehler.append(f"Seite {i}: Text ab {b[1]/MM:.1f} mm, "
                              f"Kopfsteg beginnt bei {geo['oben']:.1f} mm: {text!r}")
            if b[2] / MM > geo["rechts"] + TOLERANZ_RECHTS:
                fehler.append(f"Seite {i}: Satz bis {b[2]/MM:.1f} mm, "
                              f"rechte Fluchtlinie bei {geo['rechts']:.1f} mm: {text!r}")
    return fehler, hinweise


def check_blattkante(doc):
    """Text, der ueber die Blattkante hinauslaeuft - im Druck weg."""
    fehler = []
    for i, p in enumerate(doc, 1):
        for b in p.get_text("blocks"):
            if b[4].strip() and b[3] / MM > BLATT_HOEHE:
                text = re.sub(r"\s+", " ", b[4]).strip()[:46]
                fehler.append(f"Seite {i}: Text bis {b[3]/MM:.1f} mm auf einem "
                              f"{BLATT_HOEHE:.0f}-mm-Blatt - wird beschnitten: {text!r}")
    return fehler


def check_schriften(doc):
    """Fremdschriften und Type-3-Schriften im Dokument.

    Eine benannte Fremdschrift ist immer ein Fehler: eine Datei wurde
    nicht gefunden und still ersetzt. Bei Type 3 haengt es am Erzeuger -
    im Repo-Bau ist es dieselbe stille Ersetzung, in einem Canvas-Export
    sind es oft gezeichnete Glyphen ohne Namen. Darum werden beide
    getrennt gemeldet und die namenlosen nur einmal, mit Seitenliste.
    """
    # Ein Erzeuger bettet die Schrift unter ihrem Klarnamen ein - mit
    # Leerzeichen statt Bindestrichen. 'TT Norms Pro Bold' wurde dadurch
    # als Fremdschrift gemeldet, obwohl es die Hausschrift ist. Verglichen
    # wird deshalb ohne Trennzeichen.
    erlaubt = ("TTNorms", "Unbounded", "LiberationSans", "BKM")
    fehler, gesehen, type3 = [], set(), []
    for i, p in enumerate(doc, 1):
        for f in p.get_fonts(full=True):
            kurz = (f[3] or "").split("+")[-1]
            nackt = kurz.replace("-", "").replace(" ", "").replace("_", "")
            if f[2] == "Type3" and not kurz:
                if i not in type3:
                    type3.append(i)
                continue
            if kurz in gesehen:
                continue
            gesehen.add(kurz)
            if f[2] == "Type3":
                fehler.append(f"Seite {i}: Type-3-Schrift {kurz!r} - eine "
                              f"Schriftdatei wurde nicht gefunden und still ersetzt.")
            elif not any(e.lower() in nackt.lower() for e in erlaubt):
                fehler.append(f"Seite {i}: Fremdschrift {kurz!r} im Dokument.")
    if type3:
        seiten = ", ".join(str(s) for s in type3[:8])
        mehr = f" und {len(type3)-8} weitere" if len(type3) > 8 else ""
        fehler.append(f"Type-3-Schriften ohne Namen auf Seite {seiten}{mehr}. "
                      f"Aus einem Canvas-Export sind das meist gezeichnete "
                      f"Glyphen; aus dem Repo-Bau waere es eine stille "
                      f"Ersetzung. Herkunft pruefen.")
    return fehler


def check_wortbruch(doc):
    """Woerter, die ohne Trennstrich mitten durchbrechen.

    Entsteht, wenn eine Spalte schmaler ist als das laengste Wort darin
    und die CSS auf break-word steht. Am 03.09.2026 stand auf einer Seite
    'Technologi / emarke' und 'Partnernet / zwerk'.

    Erkannt wird es daran, dass das letzte Wort einer Zeile und das erste
    der naechsten zusammengesetzt ein Wort ergeben, das anderswo im
    Dokument als ein Wort steht. Ohne diesen zweiten Beleg waere jeder
    normale Umbruch ein Treffer.
    """
    voll = " ".join(p.get_text() for p in doc)
    woerter = set(w.lower() for w in re.findall(r"[A-Za-zÄÖÜäöüß-]{4,}", voll))
    fehler = []
    for i, p in enumerate(doc, 1):
        for blk in p.get_text("dict")["blocks"]:
            zeilen = [" ".join(s["text"] for s in l["spans"]).strip()
                      for l in blk.get("lines", [])]
            for a, b in zip(zeilen, zeilen[1:]):
                if not a or not b or a[-1] in "-–—":
                    continue
                links = re.search(r"([A-Za-zÄÖÜäöüß]+)$", a)
                rechts = re.match(r"([a-zäöüß]+)", b)
                if not links or not rechts:
                    continue
                ganz = (links.group(1) + rechts.group(1)).lower()
                if len(ganz) > 7 and ganz in woerter:
                    fehler.append(f"Seite {i}: {links.group(1)!r} / "
                                  f"{rechts.group(1)!r} - {ganz!r} bricht ohne "
                                  f"Trennstrich mitten durch.")
    return fehler


# Die eingebetteten Schriften, zum Nachmessen einer Silbe.
SCHRIFTEN = {}

Zeile = collections.namedtuple(
    "Zeile", "faktor seite breite text folgt frei schrift groesse")


def leerzeichenbreiten(doc):
    """Wie breit jede eingebettete Schrift ihr Leerzeichen setzt, in em.

    Aus der Schriftdatei im PDF, nicht aus dem Satz. Damit gilt die
    Messung auch fuer ein PDF, das nicht aus diesem Repository kommt.
    """
    import pymupdf
    breiten, _schriften = {}, {}
    for seite in doc:
        for xref, _, _, basename, *_ in seite.get_fonts(full=True):
            # get_fonts liefert 'DJXTCH+TT-Norms-Pro', der Satz meldet
            # 'TT-Norms-Pro'. Das Praefix ist die Untergruppenkennung des
            # PDF; ohne sie abzuschneiden findet keine Zeile ihre Schrift,
            # und die Pruefung bleibt stumm, ohne es zu sagen.
            name = basename.split("+")[-1]
            if name in breiten:
                continue
            try:
                puffer = doc.extract_font(xref)[3]
                if puffer:
                    schrift = pymupdf.Font(fontbuffer=puffer)
                    breiten[name] = schrift.glyph_advance(32)
                    _schriften[name] = schrift
                else:
                    breiten[name] = None
            except Exception:
                breiten[name] = None
    SCHRIFTEN.update(_schriften)
    return breiten


def zeilenabstaende(doc):
    """Je Zeile: Faktor des Wortabstands, Seite, Zeilenbreite, Text.

    Gemessen wird der Vorschub des Leerzeichens - der Abstand vom Anfang
    des Leerzeichens zum Anfang des naechsten Buchstabens. Genommen wird
    der Mittelwert der Zeile in der Mitte, nicht der groesste Abstand:
    ein einzelner grosser Zwischenraum kann ein geschuetztes Leerzeichen
    oder ein Einzug sein, eine durchgehend gedehnte Zeile ist das Loch.
    """
    import statistics
    breiten = leerzeichenbreiten(doc)
    zeilen = []
    for nr, seite in enumerate(doc, 1):
        for block in seite.get_text("rawdict")["blocks"]:
            reihe = block.get("lines", [])
            for lfd, zeile in enumerate(reihe):
                zeichen, natur, schrift, groesse = [], [], None, 9.0
                for span in zeile["spans"]:
                    name = span["font"].split("+")[-1]
                    em = breiten.get(name)
                    if em is None:
                        continue
                    zeichen += span["chars"]
                    natur.append(em * span["size"] / MM)
                    if schrift is None:
                        schrift, groesse = name, span["size"]
                if len(zeichen) < ABSTAND_MIN_ZEICHEN or not natur:
                    continue
                luecken = [(b["bbox"][0] - a["bbox"][0]) / MM
                           for a, b in zip(zeichen, zeichen[1:])
                           if a["c"] == " "]
                if len(luecken) < ABSTAND_MIN_LUECKEN:
                    continue
                normal = statistics.median(natur)
                if normal <= 0:
                    continue
                text = "".join(c["c"] for c in zeichen).strip()
                # Das erste Wort der naechsten Zeile ist das, was nicht
                # mehr gepasst hat. Es zu nennen macht aus einer Meldung
                # eine Handlungsanweisung.
                folgt = ""
                if lfd + 1 < len(reihe):
                    weiter = "".join(c["c"] for sp in reihe[lfd+1]["spans"]
                                     for c in sp.get("chars", ())).strip()
                    if weiter:
                        folgt = weiter.split()[0].strip(".,;:()\u201e\u201c")
                faktor = statistics.median(luecken) / normal
                # So viel Platz gaebe die Zeile her, wenn ihre
                # Zwischenraeume wieder auf Normalmass zurueckgingen.
                frei = (faktor - 1) * normal * len(luecken)
                zeilen.append(Zeile(faktor, nr,
                                    (zeichen[-1]["bbox"][2]
                                     - zeichen[0]["bbox"][0]) / MM,
                                    text, folgt, frei, schrift, groesse))
    return zeilen


def check_wortabstand(doc):
    """Zeilen, deren Wortzwischenraum ein Loch in die Spalte reisst.

    Blocksatz dehnt den Zwischenraum, bis die Zeile die Spalte fuellt.
    Passt das naechste Wort nicht mehr und laesst es sich nicht trennen,
    wird die Zeile auseinandergezogen. Bei 55 mm Spaltenbreite und 9 pt
    traegt eine Zeile sechsunddreissig Zeichen; da geraet das schnell
    ausser Rand und Band.

    Gemeldet wird ab dem Doppelten, und zwar unter den Hinweisen: ein
    Loch ist haesslich, aber es bricht keine Zusage. Das Auffaellige
    darunter steht nur in der Kennzahl - es einzeln zu melden hiesse,
    vierzig Prozent einer Broschuere zu melden, und eine Pruefung, die
    das tut, liest niemand zu Ende.

    Zur Abhilfe wird das Wort am Anfang der naechsten Zeile genannt. Ein
    weiches Trennzeichen darin hilft - aber nicht, indem seine erste
    Silbe die Luecke fuellt. Das war die erste Vermutung, und sie war
    falsch: gemessen passt die Silbe so gut wie nie hinein, denn genau
    dann haette Pango von sich aus getrennt. Es hilft, weil es den
    Umbruch der ganzen Zeile verschiebt. Deshalb ist das Ergebnis nicht
    vorherzusagen - man setzt es, baut neu und misst nach.
    """
    loecher = []
    for z in zeilenabstaende(doc):
        if z.faktor <= ABSTAND_LOCH:
            continue
        meldung = (f"Seite {z.seite}: Wortabstand {z.faktor:.1f}-fach in einer "
                   f"Spalte von {z.breite:.0f} mm: {z.text[:48]!r}")
        if len(z.folgt) >= 6:
            meldung += (f" - es haengt an {z.folgt!r}; ein weiches "
                        f"Trennzeichen darin verschiebt den Umbruch")
        loecher.append(meldung)
    return loecher


def wortabstand_kennzahl(doc):
    """Eine Zeile Bilanz zum Blocksatz, auch wenn nichts zu melden ist.

    Die Meldung nennt nur die Loecher. Der Zustand dazwischen - laeuft
    der Satz ruhig oder steht die Haelfte aller Zeilen gedehnt - steht
    in keiner Meldung und ist doch das, was man auf dem Blatt sieht.
    """
    import statistics
    werte = sorted(z.faktor for z in zeilenabstaende(doc))
    if not werte:
        return None
    return {
        "zeilen": len(werte),
        "median": statistics.median(werte),
        "auffaellig": sum(x > ABSTAND_AUFFAELLIG for x in werte)/len(werte)*100,
        "max": werte[-1],
    }


def fuellgrad(doc, geo):
    zeilen = []
    for i, p in enumerate(doc, 1):
        unten = max((b[3] / MM for b in p.get_text("blocks") if b[4].strip()),
                    default=geo["oben"])
        unten = min(unten, geo["unten"])
        anteil = (unten - geo["oben"]) / (geo["unten"] - geo["oben"]) * 100
        zeilen.append((i, max(0, anteil)))
    return zeilen


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("pdf")
    p.add_argument("--art", choices=sorted(GEOMETRIE), default="broschuere",
                   help="Satzspiegel, gegen den geprueft wird.")
    p.add_argument("--blocksatz", action="store_true",
                   help="Wortabstaende auch ausserhalb der Broschuere messen.")
    p.add_argument("--fuellgrad", action="store_true",
                   help="Zusaetzlich ausgeben, wie voll jede Seite steht.")
    a = p.parse_args()

    if not Path(a.pdf).is_file():
        print(f"Nicht gefunden: {a.pdf}")
        return 2
    try:
        import pymupdf
    except ImportError:
        print("pymupdf fehlt.")
        return 2

    doc = pymupdf.open(a.pdf)
    geo = seiten_geometrie(doc, a.art)

    satz, hinweise = check_satzspiegel(doc, geo)

    # Der Blocksatz ist ein Broschuerenthema. Er entstand an der
    # dreispaltigen Anlage des Innenteils - 55 mm, sechsunddreissig
    # Zeichen je Zeile. Die Verarbeitungsanleitungen und die
    # Datenblaetter setzen ihren Text 76 bis 114 mm breit und liegen
    # gemessen bei 1,00-fachem Wortabstand; dort gibt es nichts zu
    # holen, und vier Randbefunde ueber acht Anleitungen wuerden nur
    # den Bericht zustellen. Mit --blocksatz laeuft die Messung
    # trotzdem, wenn jemand nachsehen will.
    blocksatz = a.blocksatz or a.art == "broschuere"
    # Ein Loch misst Satzqualitaet, nicht Vertragstreue: haesslich, aber
    # keine gebrochene Zusage - anders als Text ueber der Blattkante
    # oder eine fehlende Schrift. Es laeuft darum unter den Hinweisen
    # und beeinflusst den Rueckgabewert nicht.
    if blocksatz:
        hinweise = hinweise + check_wortabstand(doc)
    gruppen = [
        ("Blattbeschriftung aus dem Canvas", check_canvas_marker(doc)),
        ("Text ueber der Blattkante",        check_blattkante(doc)),
        ("Text ausserhalb des Satzspiegels", satz),
        ("Wortbrueche ohne Trennstrich",     check_wortbruch(doc)),
        ("Schriften",                        check_schriften(doc)),
        ("Blattformat",                      check_blattformat(doc)),
    ]

    print(f"  {Path(a.pdf).name}: {len(doc)} Seiten, geprueft als {a.art}")
    print(f"  Satzspiegel {geo['links']:.0f}-{geo['rechts']:.0f} mm waagerecht, "
          f"{geo['oben']:.1f}-{geo['unten']:.1f} mm senkrecht")
    print()
    gesamt = 0
    for name, fehler in gruppen:
        if fehler:
            gesamt += len(fehler)
            print(f"  {name} ({len(fehler)}):")
            for f in fehler[:12]:
                print(f"    - {f}")
            if len(fehler) > 12:
                print(f"    … und {len(fehler)-12} weitere")
        else:
            print(f"  {name}: nichts zu beanstanden.")
    kennzahl = wortabstand_kennzahl(doc) if blocksatz else None
    if kennzahl:
        print()
        print(f"  Blocksatz: {kennzahl['zeilen']} Fliesstextzeilen gemessen, "
              f"Wortabstand im Mittel {kennzahl['median']:.2f}-fach, "
              f"{kennzahl['auffaellig']:.0f}% ueber der Setzergrenze von "
              f"{ABSTAND_AUFFAELLIG:.2f}, weiteste Zeile {kennzahl['max']:.1f}-fach.")

    if hinweise:
        print()
        print("  Hinweise - gesehen, aber nicht als Fehler gewertet:")
        for h in hinweise:
            print(f"    · {h}")
    if a.fuellgrad:
        print()
        print("  Fuellgrad je Seite:")
        for i, v in fuellgrad(doc, geo):
            leer = "  <- sehr leer" if v < 40 else ""
            print(f"    S{i:3}  {v:3.0f}%{leer}")
    print()
    print(f"  {gesamt} Beanstandung(en).")
    return 1 if gesamt else 0


if __name__ == "__main__":
    sys.exit(main())
