#!/usr/bin/env python3
"""Misst die tatsaechliche Groesse der Bildkaesten in den Canvas-Vorlagen.

Ein Bild mit width:100 % oder calc(100 % + 8mm) kennt seine Groesse nicht — sie
ergibt sich erst aus dem Elternelement. Rechnerisch ist der Beschnitt damit von
aussen nicht zu bestimmen, und ohne ihn laesst sich nicht entscheiden, ob ein
Vermerk ueber dem Kasten noetig ist oder eine Doppelung erzeugen wuerde.

Gemessen wird deshalb dort, wo die Frage entschieden ist: im Browser. Jede Seite
wird einzeln gerendert, jedes KI-Motiv vorher markiert, und hinterher steht seine
Kastengroesse in Pixeln fest. Der Massstab kommt vom Seitencontainer selbst — er
ist 210 mm breit, das ist der einzige Bezug, den es braucht.

Braucht Playwright und das mitgelieferte Chromium. Fehlt eines von beidem, meldet
das Modul das und liefert nichts — geraten wird nicht.

    python3 scripts/kasten_messen.py            # alle Vorlagen
    python3 scripts/kasten_messen.py --json     # Ergebnis als JSON
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
CANVAS_DIR = WURZEL / "templates" / "brochure"
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

SEITE = re.compile(r'<div[^>]*\bstyle="[^"]*\bwidth:210mm;\s*height:297mm;')
BILD = re.compile(r'<img(?![^>]*\bdata-ki-vermerk)[^>]*\bsrc="([^"]+)"[^>]*>')


def _seiten(text: str):
    """Die Seitencontainer eines Canvas-Dokuments, als Textabschnitte."""
    starts = [m.start() for m in SEITE.finditer(text)] + [len(text)]
    for i in range(len(starts) - 1):
        yield text[starts[i]:starts[i + 1]]


def _messblatt(datei: Path, motive: set[str]) -> tuple[str, int]:
    """Baut aus einer Vorlage ein eigenstaendiges Blatt mit markierten Motiven."""
    text = datei.read_text(encoding="utf-8")
    stil = re.search(r"<style>.*?</style>", text, re.S)
    zaehler: dict[str, int] = {}

    def markiere(m):
        quelle = m.group(1)
        if quelle not in motive:
            return m.group(0)
        # Gezaehlt wird je Motiv, nicht fortlaufend ueber alle. So bleibt die
        # Zuordnung gueltig, auch wenn ein anderes Werkzeug die Bilder in
        # abweichender Reihenfolge durchgeht.
        n = zaehler.get(quelle, 0)
        zaehler[quelle] = n + 1
        return m.group(0)[:4] + (' data-mess="%s#%d"' % (quelle, n)) + m.group(0)[4:]

    koerper = "".join(BILD.sub(markiere, block) for block in _seiten(text))
    blatt = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
             + (stil.group(0) if stil else "")
             + "</head><body style='margin:0'>" + koerper + "</body></html>")
    return blatt, sum(zaehler.values())


def messen(dateien=None, motive: set[str] | None = None) -> dict | None:
    """{datei: [{index, quelle, breite_mm, hoehe_mm}, …]} oder None ohne Browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    if not Path(CHROMIUM).exists():
        return None

    if motive is None:
        reg = WURZEL / "assets" / "kennzeichnung" / "register.json"
        motive = set(json.loads(reg.read_text(encoding="utf-8")).get("ki_motive", []))
    dateien = dateien or sorted(CANVAS_DIR.glob("*.dc.html"))

    ergebnis = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROMIUM)
        for datei in dateien:
            blatt, anzahl = _messblatt(datei, motive)
            if not anzahl:
                continue
            # Die Bildpfade stehen relativ zur Wurzel des Repositories, also muss
            # das Messblatt dort liegen — sonst laedt kein Motiv und jeder Kasten
            # misst null.
            with tempfile.NamedTemporaryFile("w", dir=WURZEL, suffix=".html",
                                             prefix="_messung-", delete=False,
                                             encoding="utf-8") as f:
                f.write(blatt)
                pfad = Path(f.name)
            try:
                seite = browser.new_page(viewport={"width": 1200, "height": 900})
                seite.goto("file://" + str(pfad))
                seite.wait_for_timeout(900)
                werte = seite.evaluate("""() => {
                    const seiten = [...document.querySelectorAll('div')].filter(
                        d => (d.getAttribute('style')||'').includes('width:210mm'));
                    const massstab = seiten.length ? 210 / seiten[0].getBoundingClientRect().width : null;
                    return [...document.querySelectorAll('[data-mess]')].map(el => {
                        const r = el.getBoundingClientRect();
                        return {index: el.dataset.mess, src: el.getAttribute('src'),
                                w: r.width, h: r.height, massstab};
                    });
                }""")
                seite.close()
            finally:
                pfad.unlink(missing_ok=True)

            ergebnis[datei.name] = {
                w["index"]: {"quelle": w["src"],
                             "breite_mm": w["w"] * w["massstab"] if w["massstab"] else None,
                             "hoehe_mm": w["h"] * w["massstab"] if w["massstab"] else None}
                for w in werte
            }
        browser.close()
    return ergebnis


def main() -> int:
    erg = messen()
    if erg is None:
        print("Playwright oder Chromium fehlt — es wird nichts gemessen.")
        return 2
    if "--json" in sys.argv:
        print(json.dumps(erg, ensure_ascii=False, indent=1))
        return 0
    gesamt = 0
    for datei, eintraege in erg.items():
        print("  %s" % datei)
        for schluessel, e in sorted(eintraege.items()):
            gesamt += 1
            masse = ("%.1f × %.1f mm" % (e["breite_mm"], e["hoehe_mm"])
                     if e["breite_mm"] else "nicht messbar")
            print("     %-52s %s" % (Path(e["quelle"]).name[:52], masse))
    print("\n%d Bildkasten/-kaesten gemessen." % gesamt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
