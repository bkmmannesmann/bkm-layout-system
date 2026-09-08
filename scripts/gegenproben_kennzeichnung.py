#!/usr/bin/env python3
"""Gegenproben zur KI-Kennzeichnung in scripts/kennzeichnung.py.

Gesucht wird der Vermerk „AI GENERATED“ ueber eine normierte Kreuzkorrelation
gegen die Deckungsmaske des Logos. Ein solcher Sucher hat zwei Arten zu irren:
er uebersieht einen vorhandenen Vermerk, oder er meldet einen, wo keiner ist.
Das zweite ist das gefaehrlichere - eine Pruefung, die auf Bildrauschen
anspringt, gibt ein Motiv als gekennzeichnet frei, das es nicht ist.

Hier steht deshalb beides: Faelle, in denen der Sucher anschlagen muss, und
Faelle, in denen er stumm zu bleiben hat. Die stummen sind in der Ueberzahl.

Gerechnet wird auf echten Motiven des Repositories, wo es sie gibt, und sonst
auf erzeugten Bildern - Verlauf, Rauschen, einfarbige Flaeche. Ein erzeugtes
Bild taugt fuer die Frage "springt der Sucher auf Struktur an", nicht fuer die
Frage "findet er einen echten Vermerk". Dafuer sind die sechs bereits
gekennzeichneten Motive in uploads/ da.

    python3 scripts/gegenproben_kennzeichnung.py
"""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

WURZEL = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(WURZEL / "scripts"))

import kennzeichnung as K                                    # noqa: E402
import pruefe_kennzeichnung as P                             # noqa: E402


def verlauf(w, h, von=40, bis=90):
    """Ein ruhiger Grund, wie ihn eine Kellerwand im Halbschatten abgibt."""
    zeile = np.linspace(von, bis, w, dtype=np.float32)
    feld = np.tile(zeile, (h, 1)) + np.linspace(0, 25, h, dtype=np.float32)[:, None]
    return Image.fromarray(np.clip(feld, 0, 255).astype(np.uint8)).convert("RGB")


def rauschen(w, h, mittel=110, streuung=45, saat=7):
    """Struktur ohne Vermerk - der haerteste Fall fuer einen Falschfund."""
    r = np.random.default_rng(saat)
    feld = r.normal(mittel, streuung, (h, w))
    return Image.fromarray(np.clip(feld, 0, 255).astype(np.uint8)).convert("RGB")


def mit_vermerk(bild, ecke="unten_rechts", breite_anteil=0.095, rand_anteil=0.010):
    """Setzt den Vermerk von Hand - unabhaengig von stemple(), damit die
    Gegenprobe nicht denselben Weg prueft, den sie beweisen soll."""
    bild = bild.convert("RGBA")
    w, h = bild.size
    tb = max(8, int(round(w * breite_anteil)))
    th = int(round(tb / K.SEITENVERHAELTNIS))
    rand = int(round(w * rand_anteil))
    x = w - rand - tb if "rechts" in ecke else rand
    y = h - rand - th if "unten" in ecke else rand
    bild.alpha_composite(K.logo_raster(tb), (x, y))
    return bild.convert("RGB")


def als_datei(bild, ordner, name):
    p = Path(ordner) / name
    bild.save(p, quality=95) if p.suffix.lower() in (".jpg", ".jpeg") else bild.save(p)
    return p


REGISTER = json.loads((WURZEL / "assets" / "kennzeichnung" / "register.json")
                      .read_text(encoding="utf-8"))
GEKENNZEICHNET = [WURZEL / r for r in REGISTER["ki_motive"]]
UNGEKENNZEICHNET = [WURZEL / r for r in [
    "uploads/a4-texture-white.jpg",
    "uploads/a4-texture-deep-green.jpg",
    "uploads/cover-hero-standard.jpg",
    "uploads/druckwasser-abplazender-putz-feuchte-waende.jpg",
    "uploads/magnific_nano-banana-2-halbnah-san_3GXw9NsREY.jpg",
    "uploads/fachbetrieb-partner-standard.webp",
    "assets/images/keyvisual-on-light.png",
    "assets/images/products/novusan.png",
]]


def main():
    gut = gesamt = 0

    def probe(bedingung, text, zusatz=""):
        nonlocal gut, gesamt
        gesamt += 1
        gut += bool(bedingung)
        print(f"  [{'ok' if bedingung else 'XX'}] {text}")
        if zusatz:
            print(f"        {zusatz}")

    tmp = tempfile.mkdtemp(prefix="kennzeichnung-")
    regel = K.regeln()

    print("Der Sucher muss anschlagen")
    print("-" * 64)

    # Die sechs Motive, an denen die Schwelle kalibriert wurde. Sie sind der
    # Bezugspunkt: was hier durchfaellt, macht jede Zahl in brand.json ungueltig.
    werte = []
    for p in GEKENNZEICHNET:
        if not p.exists():
            probe(False, f"{p.name} - fehlt im Repository")
            continue
        t = K.finde(p)
        werte.append(t["guete"])
        probe(t["gefunden"] and t["ecke"] == "unten_rechts",
              f"{p.name[:48]} - Vermerk gefunden",
              f"Guete {t['guete']:.3f}, {t['ecke']}, {t['kasten'][2]} px")
    if werte:
        probe(min(werte) >= 0.90,
              "die gekennzeichneten Motive liegen deutlich ueber der Schwelle",
              f"schwaechster Fund {min(werte):.3f}, Schwelle {K.SCHWELLE:.2f}")

    # In jeder zugelassenen Ecke, damit die Suche nicht nur unten rechts kann.
    for ecke in K.ECKEN:
        p = als_datei(mit_vermerk(verlauf(1200, 675), ecke), tmp, f"ecke-{ecke}.png")
        t = K.finde(p)
        probe(t["gefunden"] and t["ecke"] == ecke,
              f"Vermerk in Ecke {ecke} gefunden",
              f"Guete {t['guete']:.3f}, erkannt als {t['ecke']}")

    # Ein Motiv, das durch die JPEG-Kompression gegangen ist. Praxisfall: die
    # Bilder liegen nicht als PNG im Repository.
    p = als_datei(mit_vermerk(rauschen(1200, 675, 70, 30)), tmp, "gepresst.jpg")
    Image.open(p).save(Path(tmp) / "gepresst-60.jpg", quality=60)
    t = K.finde(Path(tmp) / "gepresst-60.jpg")
    probe(t["gefunden"], "Vermerk ueberlebt starke JPEG-Kompression",
          f"Guete {t['guete']:.3f} bei Qualitaet 60")

    # Was stemple() setzt, muss finde() wiederfinden - sonst prueft das Repository
    # etwas anderes, als es aufbringt.
    quelle = als_datei(verlauf(1600, 900, 30, 70), tmp, "roh.png")
    erg = K.stemple(quelle, Path(tmp) / "gestempelt.png")
    t = K.finde(Path(tmp) / "gestempelt.png")
    probe(t["gefunden"] and t["ecke"] == erg["ecke"],
          "was stemple() setzt, findet finde() wieder",
          f"gesetzt {erg['ecke']}, gefunden {t['ecke']}, Guete {t['guete']:.3f}")

    print("\nDer Sucher muss stumm bleiben")
    print("-" * 64)

    for p in UNGEKENNZEICHNET:
        if not p.exists():
            continue
        t = K.finde(p)
        probe(not t["gefunden"], f"{p.name[:48]} - kein Vermerk gemeldet",
              f"Guete {t['guete']:.3f}")

    # Reines Rauschen ist die haerteste Probe: irgendwo in einer 1200x675-Flaeche
    # findet sich immer eine Stelle, die dem Muster aehnelt. Sie darf die Schwelle
    # nicht erreichen.
    hoechste = 0.0
    for saat in (1, 2, 3, 4, 5):
        t = K.finde(als_datei(rauschen(1200, 675, 128, 60, saat), tmp, f"rausch{saat}.png"))
        hoechste = max(hoechste, t["guete"])
    probe(hoechste < K.SCHWELLE, "reines Rauschen erzeugt keinen Fund",
          f"hoechster Wert aus fuenf Durchgaengen {hoechste:.3f}")

    # Eine einfarbige Flaeche liess die Korrelation frueher auf 1,0 laufen: der
    # Nenner ging gegen null. MIN_STREUUNG haelt sie heraus.
    p = als_datei(Image.new("RGB", (1200, 675), (128, 132, 130)), tmp, "einfarbig.png")
    t = K.finde(p)
    probe(not t["gefunden"], "einfarbige Flaeche erzeugt keine Scheinguete von 1,0",
          f"Guete {t['guete']:.3f}")

    # Ein Bild kleiner als das kleinste Muster darf nicht abstuerzen.
    p = als_datei(verlauf(60, 40), tmp, "winzig.png")
    try:
        t = K.finde(p)
        probe(not t["gefunden"], "Bild kleiner als das Muster - kein Fund, kein Absturz",
              f"Guete {t['guete']:.3f} bei 60x40 px")
    except Exception as e:
        probe(False, "Bild kleiner als das Muster", f"{type(e).__name__}: {e}")

    print("\nMasse und Maengel")
    print("-" * 64)

    # Zu klein gesetzt: der Vermerk ist da, aber unlesbar. Die Pruefung muss ihn
    # finden und trotzdem beanstanden - nicht schweigen, weil etwas da ist.
    p = als_datei(mit_vermerk(verlauf(1200, 675), breite_anteil=0.05), tmp, "zu-klein.png")
    b = P.bewerte(p, regel)
    probe(b["gefunden"] and any("klein" in m for m in b["maengel"]),
          "zu klein gesetzter Vermerk wird beanstandet",
          f"gefunden {b['gefunden']}, {b['kasten'][2]} px, Maengel: {b['maengel'] or 'keine'}")

    # Randbuendig: verstoesst gegen den geforderten Abstand und faellt beim
    # Beschnitt als Erstes weg.
    p = als_datei(mit_vermerk(verlauf(1200, 675), rand_anteil=0.0), tmp, "randbuendig.png")
    b = P.bewerte(p, regel)
    probe(b["gefunden"] and any("Abstand" in m for m in b["maengel"]),
          "randbuendiger Vermerk wird beanstandet",
          f"Rand {100 * b.get('rand_x', 0):.2f} %, Maengel: {b['maengel'] or 'keine'}")

    # Regelmaessig gesetzt: keine Beanstandung. Sonst meldet die Pruefung bei
    # jedem korrekten Motiv und wird nach zwei Wochen nicht mehr gelesen.
    p = als_datei(mit_vermerk(verlauf(1200, 675)), tmp, "regelrecht.png")
    b = P.bewerte(p, regel)
    probe(b["gefunden"] and not b["maengel"], "regelrecht gesetzter Vermerk gilt als sauber",
          f"{b['kasten'][2]} px, Rand {100 * b['rand_x']:.2f} % / {100 * b['rand_y']:.2f} %")

    # Die Ecke entscheidet sich am Kontrast: auf einem Grund, der links dunkel und
    # rechts hell ist, muss die Wahl nach links fallen.
    feld = np.tile(np.linspace(20, 235, 1200, dtype=np.float32), (675, 1))
    p = als_datei(Image.fromarray(feld.astype(np.uint8)).convert("RGB"), tmp, "halb.png")
    rang = K.beste_ecke(p, regel)
    probe(rang[0]["ecke"] == "unten_links",
          "die Ecke wird nach dem Kontrast gewaehlt, nicht nach Gewohnheit",
          ", ".join(f"{e['ecke']} {e['eignung']:.2f}" for e in rang))

    # Das Logo darf nicht verzerrt aufgebracht werden. Gemessen wird gegen die
    # Sollhoehe, nicht gegen das Verhaeltnis: eine Rasterflaeche hat ganze Pixel,
    # und bei 200 px Breite liegt die Sollhoehe bei 48,5 - jede Rundung davon
    # verschiebt das Verhaeltnis um ein Prozent, ohne dass etwas verzerrt waere.
    # Ueber mehrere Groessen hinweg faellt eine echte Verzerrung trotzdem auf.
    schief = []
    for tb in (60, 114, 200, 400, 940):
        r = K.logo_raster(tb)
        soll = tb / K.SEITENVERHAELTNIS
        if abs(r.height - soll) > 1.0 or r.width != tb:
            schief.append(f"{tb} px -> {r.width}x{r.height}, Soll {soll:.1f}")
    probe(not schief, "das Logo behaelt ueber alle Groessen sein Seitenverhaeltnis",
          "; ".join(schief) if schief else
          "60, 114, 200, 400, 940 px - Hoehe jeweils innerhalb eines Rasterpixels")

    # Stempeln darf weder Bildgroesse noch Farbmodell veraendern.
    quelle = WURZEL / "uploads" / "cover-hero-standard.jpg"
    if quelle.exists():
        vorher = Image.open(quelle)
        K.stemple(quelle, Path(tmp) / "erhalt.jpg")
        nachher = Image.open(Path(tmp) / "erhalt.jpg")
        probe(vorher.size == nachher.size and vorher.mode == nachher.mode,
              "Stempeln aendert Bildgroesse und Farbmodell nicht",
              f"{vorher.size} {vorher.mode} -> {nachher.size} {nachher.mode}")

    print("\nRegister und Regelwerk")
    print("-" * 64)

    marke = json.loads((WURZEL / "brand.json").read_text(encoding="utf-8"))
    marke = marke["ai_generated_images"]["marke"]
    probe(Path(WURZEL / marke["datei"]).exists(),
          "brand.json verweist auf eine vorhandene Logodatei", marke["datei"])
    probe(abs(marke["seitenverhaeltnis"] - K.SEITENVERHAELTNIS) < 0.01,
          "das Seitenverhaeltnis in brand.json stimmt mit der Datei ueberein",
          f"brand.json {marke['seitenverhaeltnis']}, Datei {K.SEITENVERHAELTNIS:.3f}")

    doppelt = set(REGISTER["ki_motive"]) & set(REGISTER["keine_ki"])
    probe(not doppelt, "kein Motiv steht in beiden Listen des Registers",
          ", ".join(sorted(doppelt)) if doppelt else "")
    fehlend = [r for r in REGISTER["ki_motive"] + REGISTER["keine_ki"]
               if not (WURZEL / r).exists()]
    probe(not fehlend, "jeder Registereintrag zeigt auf eine vorhandene Datei",
          ", ".join(fehlend) if fehlend else "")

    print("-" * 64)
    print(f"  {gut} von {gesamt} wie erwartet")
    return 0 if gut == gesamt else 1


if __name__ == "__main__":
    sys.exit(main())
