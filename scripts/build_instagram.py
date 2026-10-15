#!/usr/bin/env python3
"""Baut Instagram-Karussells als verlustfreie PNGs (1080 × 1350).

Der Regelweg: ein Post ist content/instagram/<post>/content.json. Daraus setzt
templates/instagram/karussell.html.j2 die Folien, und Chromium — derselbe
Browser, in dem Claude Design die Referenz zeigt — rendert sie zu PNG.

    python3 scripts/build_instagram.py content/instagram/<post>/
    python3 scripts/build_instagram.py --alle          # jeder Post im Ordner
    python3 scripts/build_instagram.py --plan          # Content-Plan prüfen
    python3 scripts/build_instagram.py --gegenprobe    # Vorlage gegen Referenz

Daneben nimmt es auch fertiges HTML aus Claude Design (Ordner, Datei, ZIP oder
Standalone-Export). Ein ZIP wird nach incoming/instagram/<slug>/ entpackt:

    python3 scripts/build_instagram.py templates/instagram/referenz/ --min 1 --max 100
    python3 scripts/build_instagram.py ~/Downloads/<projekt>.zip --slug <name>

Folien sind Elemente mit data-slide (eigene Vorlage) oder data-screen-label
(Artboards in Claude Design), sonst die äußersten Elemente im Zielformat.
Jede Folie wird mit der Pixeldichte gerendert, die genau das Zielformat ergibt.

Ausgabe: output/instagram/<post>/<post>-01.png …, <post>.zip mit allen Folien
und <post>-caption.txt. PNG, RGB ohne Alphakanal, sRGB.

Die Dateien kommen über einen lokalen Webserver, nicht über file:// — dort lädt
Chromium CSS-Masken nicht, und die Icons fehlten still. Abbruch (Exit-Code 1),
wenn eine Datei, Schrift oder ein Bild nicht lädt, Text über den Satzspiegel
läuft, eine Folie nicht ins Format passt oder die Folienzahl außerhalb von
7 bis 10 liegt (--min/--max).
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

ROOT_DIR = Path(__file__).parent.parent.resolve()
SOCIAL_DIR = ROOT_DIR / "incoming" / "instagram"   # Direktexporte aus Claude Design
CONTENT_DIR = ROOT_DIR / "content" / "instagram"
REFERENZ_DIR = ROOT_DIR / "templates" / "instagram" / "referenz"
# Gegenprobe: diese Posts bauen die Referenz (Runde 4) aus content.json nach.
GEGENPROBE = {"wege-diy": "4a", "wege-feuchte-check": "4b", "wege-fachbetrieb": "4c"}
OUTPUT_DIR = ROOT_DIR / "output" / "instagram"

FORMATE = {
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
    "9:16": (1080, 1920),
}

# Toleranz für das Seitenverhältnis einer Folie. Rundung im Canvas ja,
# ein anderes Format nein.
VERHAELTNIS_TOLERANZ = 0.01

# Im Cloud-Container liegt Chromium hier; lokal findet Playwright seinen
# eigenen (nach `playwright install chromium`). BKM_CHROMIUM überschreibt.
CHROMIUM_KANDIDATEN = [
    os.environ.get("BKM_CHROMIUM", ""),
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
]

FOLIEN_JS = r"""
([selector, zielVerhaeltnis, toleranz]) => {
  const sichtbar = el => {
    const r = el.getBoundingClientRect();
    return r.width > 50 && r.height > 50;
  };
  let quelle, els;
  if (selector) {
    quelle = 'selector';
    els = [...document.querySelectorAll(selector)];
  } else if (document.querySelector('[data-slide]')) {
    quelle = 'data-slide';
    els = [...document.querySelectorAll('[data-slide]')];
  } else if (document.querySelector('[data-screen-label]')) {
    quelle = 'data-screen-label';
    els = [...document.querySelectorAll('[data-screen-label]')];
  } else {
    quelle = 'seitenverhaeltnis';
    const passt = el => {
      const r = el.getBoundingClientRect();
      return r.width >= 200 && Math.abs(r.width / r.height - zielVerhaeltnis) / zielVerhaeltnis < toleranz;
    };
    const alle = [...document.body.querySelectorAll('*')].filter(passt);
    // nur die äußersten: kein Vorfahr passt ebenfalls
    els = alle.filter(el => {
      for (let p = el.parentElement; p; p = p.parentElement) if (alle.includes(p)) return false;
      return true;
    });
  }
  els = els.filter(sichtbar);
  els.forEach((el, i) => el.setAttribute('data-ig-folie', String(i)));
  return {
    quelle,
    folien: els.map((el, i) => {
      const r = el.getBoundingClientRect();
      return {
        index: i,
        label: el.getAttribute('data-slide') || el.getAttribute('data-screen-label') || '',
        breite: r.width,
        hoehe: r.height,
      };
    }),
  };
}
"""

PRUEF_JS = r"""
async () => {
  await document.fonts.ready;
  const schriften = [...document.fonts].map(f => ({
    familie: f.family.replace(/["']/g, ''), gewicht: f.weight, status: f.status,
  }));
  const bilder = [...document.images]
    .filter(img => img.closest('[data-ig-folie]'))
    .map(img => ({src: (img.currentSrc || img.src).slice(0, 120),
                  ok: img.complete && img.naturalWidth > 0}));
  // Welche Familien werden in den Folien tatsächlich verlangt?
  const verlangt = new Set();
  for (const el of document.querySelectorAll('[data-ig-folie], [data-ig-folie] *')) {
    if (!el.childNodes.length) continue;
    const hatText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hatText) continue;
    const cs = getComputedStyle(el);
    const erste = cs.fontFamily.split(',')[0].trim().replace(/["']/g, '');
    verlangt.add(erste + '|' + cs.fontWeight);
  }
  // Text, der über den Satzspiegel hinausläuft, liegt sonst unter dem Maßband
  // oder wird an der Folienkante abgeschnitten.
  const ueberlauf = [];
  for (const inhalt of document.querySelectorAll('[data-ig-folie] [data-ig-inhalt]')) {
    const folie = inhalt.closest('[data-ig-folie]');
    const r = folie.getBoundingClientRect(), cs = getComputedStyle(folie);
    const masstab = r.width / folie.offsetWidth;
    const unten = r.bottom - parseFloat(cs.paddingBottom) * masstab;
    const rechts = r.right - parseFloat(cs.paddingRight) * masstab;
    let tief = 0, breit = 0;
    for (const el of inhalt.querySelectorAll('*')) {
      const e = el.getBoundingClientRect();
      if (!e.width || !e.height) continue;
      tief = Math.max(tief, e.bottom - unten);
      breit = Math.max(breit, e.right - rechts);
    }
    if (tief > 2 || breit > 2)
      ueberlauf.push({folie: Number(folie.dataset.igFolie) + 1,
                      hoehe: Math.round(tief / masstab), breite: Math.round(breit / masstab)});
  }
  return {schriften, bilder, verlangt: [...verlangt], ueberlauf};
}
"""


def fehler(text: str) -> None:
    print(f"  FEHLER   {text}")


def hinweis(text: str) -> None:
    print(f"  HINWEIS  {text}")


def slug_aus(name: str) -> str:
    s = name.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "post"


def entpacken(archiv: Path, ziel: Path) -> None:
    """Entpackt das Project archive. Pfade außerhalb des Ziels werden abgewiesen."""
    if ziel.exists() and any(ziel.iterdir()):
        sys.exit(f"{ziel.relative_to(ROOT_DIR)} ist nicht leer. Anderen --slug wählen "
                 f"oder den Ordner vorher entfernen.")
    ziel.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archiv) as z:
        namen = [n for n in z.namelist() if not n.startswith("__MACOSX/")]
        # Liegt alles in einem gemeinsamen Oberordner, wird er weggelassen.
        teile = {n.split("/", 1)[0] for n in namen}
        praefix = ""
        if len(teile) == 1 and all("/" in n for n in namen):
            praefix = teile.pop() + "/"
        for n in namen:
            rel = n[len(praefix):]
            if not rel or rel.endswith("/"):
                continue
            pfad = (ziel / rel).resolve()
            if ziel.resolve() not in pfad.parents:
                sys.exit(f"Unsicherer Pfad im Archiv: {n}")
            pfad.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as quelle, open(pfad, "wb") as aus:
                shutil.copyfileobj(quelle, aus)
    print(f"Entpackt nach {ziel.relative_to(ROOT_DIR)}/")


def html_finden(pfad: Path, datei: str | None) -> Path:
    if pfad.is_file():
        return pfad
    if datei:
        return pfad / datei
    kandidaten = sorted(p for p in pfad.rglob("*.html") if "node_modules" not in p.parts)
    if not kandidaten:
        # Liegt nur das Project archive im Ordner (über die GitHub-Weboberfläche
        # hochgeladen), wird es daneben entpackt. Der Ordner _entpackt/ ist
        # ignoriert und entsteht bei jedem Bau neu.
        archive = sorted(pfad.glob("*.zip"))
        if len(archive) == 1:
            ziel = pfad / "_entpackt"
            shutil.rmtree(ziel, ignore_errors=True)
            entpacken(archive[0], ziel)
            return html_finden(ziel, datei)
        sys.exit(f"Keine HTML-Datei in {pfad}.")
    if len(kandidaten) == 1:
        return kandidaten[0]
    for name in ("index.html", "carousel.html", "karussell.html"):
        for k in kandidaten:
            if k.name == name and k.parent == pfad:
                return k
    liste = "\n".join(f"    {k.relative_to(pfad)}" for k in kandidaten)
    sys.exit(f"Mehrere HTML-Dateien in {pfad}, bitte mit --datei wählen:\n{liste}")


def chromium_pfad() -> str | None:
    for k in CHROMIUM_KANDIDATEN:
        if k and Path(k).exists():
            return k
    return None


def drift_pruefen(html: Path) -> None:
    """Markenprüfung des Entwurfs. Meldet, bricht aber nicht ab."""
    skript = ROOT_DIR / "scripts" / "check_brand_drift.py"
    if not skript.exists() or html.stat().st_size > 5_000_000:
        # Standalone-Exporte tragen alles base64-kodiert; die Prüfung sähe
        # dort nur Rauschen.
        return
    erg = subprocess.run([sys.executable, str(skript), str(html)],
                         capture_output=True, text=True)
    if erg.returncode:
        hinweis("Markenprüfung meldet Abweichungen (check_brand_drift.py):")
        for zeile in erg.stdout.strip().splitlines()[-12:]:
            print("           " + zeile)


class _StillerHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def webserver(wurzel: Path) -> ThreadingHTTPServer:
    """Liefert die Dateien über http://127.0.0.1 aus.

    Über file:// lädt Chromium CSS-Masken (mask: url(...)) nicht — sie gelten
    dort als fremder Ursprung. Die Icons der Referenz sind so gesetzt und
    fehlten im PNG, ohne dass eine Meldung kam.
    """
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(_StillerHandler, directory=str(wurzel)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def bauen(html: Path, slug: str, args) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright fehlt:  pip install playwright && playwright install chromium")
    from PIL import Image

    breite, hoehe = FORMATE[args.format]
    ziel_verhaeltnis = breite / hoehe
    ausgabe = OUTPUT_DIR / slug
    if ausgabe.exists():
        shutil.rmtree(ausgabe)
    ausgabe.mkdir(parents=True)

    print(f"\n{slug}: {html.relative_to(ROOT_DIR) if ROOT_DIR in html.parents else html}")
    if not html.is_relative_to(OUTPUT_DIR):
        # Aus content.json gesetzte Posts prüft die Gegenprobe gegen die Referenz;
        # die Markenprüfung meldete dort nur die Töne des freigegebenen Designs.
        drift_pruefen(html)
    ok = True

    html = html.resolve()
    wurzel = ROOT_DIR if ROOT_DIR in html.parents else html.parent
    httpd = webserver(wurzel)
    adresse = (f"http://127.0.0.1:{httpd.server_address[1]}/"
               + quote(html.relative_to(wurzel).as_posix()))
    fehlgeschlagen: list[str] = []

    def mitschreiben(seite) -> None:
        def antwort(r):
            if r.status >= 400:
                fehlgeschlagen.append(f"{r.status} {r.url}")
        seite.on("response", antwort)
        seite.on("requestfailed", lambda r: fehlgeschlagen.append(
            f"{r.failure or 'abgebrochen'} {r.url}"))

    with sync_playwright() as pw:
        exe = chromium_pfad()
        browser = pw.chromium.launch(**({"executable_path": exe} if exe else {}))

        def laden(dsf: float):
            ctx = browser.new_context(viewport={"width": 1600, "height": 1200},
                                      device_scale_factor=dsf)
            seite = ctx.new_page()
            mitschreiben(seite)
            seite.goto(adresse, wait_until="networkidle", timeout=120_000)
            seite.wait_for_timeout(args.warten)
            # Animationen und Übergänge stehen im Endzustand.
            seite.add_style_tag(content="*,*::before,*::after{animation-duration:0s!important;"
                                        "animation-delay:0s!important;transition:none!important;"
                                        "caret-color:transparent!important}"
                                        # Badge, das Claude Design in Exporte setzt
                                        "#__claude_design_branding,#__bundler_loading"
                                        "{display:none!important}")
            info = seite.evaluate(FOLIEN_JS, [args.selector, ziel_verhaeltnis,
                                              VERHAELTNIS_TOLERANZ])
            # Der Viewport muss alle Folien fassen, sonst schneidet ein
            # Canvas mit overflow:hidden die hinteren ab.
            masse = seite.evaluate("() => [document.documentElement.scrollWidth,"
                                   " document.documentElement.scrollHeight]")
            seite.set_viewport_size({"width": min(max(1600, masse[0]), 16000),
                                     "height": min(max(1200, masse[1]), 16000)})
            seite.wait_for_timeout(200)
            return ctx, seite, info

        ctx, seite, info = laden(1.0)
        folien = info["folien"]
        print(f"  {len(folien)} Folien gefunden (über {info['quelle']})")
        if not folien:
            fehler("Keine Folie gefunden. Folien mit data-slide markieren oder --selector angeben.")
            browser.close()
            return False

        for f in folien:
            v = f["breite"] / f["hoehe"]
            if abs(v - ziel_verhaeltnis) / ziel_verhaeltnis > VERHAELTNIS_TOLERANZ:
                fehler(f"Folie {f['index'] + 1} {f['label']!r}: {f['breite']:.0f} × {f['hoehe']:.0f} px "
                       f"passt nicht zu {args.format} ({breite} × {hoehe}).")
                ok = False
        if not args.min <= len(folien) <= args.max:
            fehler(f"{len(folien)} Folien — erwartet {args.min} bis {args.max}.")
            ok = False

        pruefung = seite.evaluate(PRUEF_JS)
        geladen = {(s["familie"], str(s["gewicht"])) for s in pruefung["schriften"]
                   if s["status"] == "loaded"}
        for s in pruefung["schriften"]:
            if s["status"] == "error":
                fehler(f"Schrift lädt nicht: {s['familie']} {s['gewicht']}")
                ok = False
        definiert = {s["familie"] for s in pruefung["schriften"]}
        for eintrag in pruefung["verlangt"]:
            familie, gewicht = eintrag.split("|")
            if familie in definiert and not any(f == familie for f, _ in geladen):
                fehler(f"Schrift {familie} {gewicht} wird verwendet, aber nicht geladen "
                       f"— Chromium setzt eine Ersatzschrift.")
                ok = False
            elif familie not in definiert and familie.lower() not in ("sans-serif", "serif"):
                hinweis(f"Schrift {familie} hat kein @font-face — es greift die Systemschrift.")
        for f in sorted(set(fehlgeschlagen)):
            if f.split(" ", 1)[-1].startswith(("data:", "blob:")):
                continue
            fehler(f"Datei lädt nicht: {f[:160]}")
            ok = False
        for u in pruefung["ueberlauf"]:
            fehler(f"Folie {u['folie']}: Inhalt läuft über ({u['hoehe']} px zu hoch, "
                   f"{u['breite']} px zu breit) — Text kürzen oder Schrift kleiner setzen.")
            ok = False
        for b in pruefung["bilder"]:
            if not b["ok"]:
                fehler(f"Bild lädt nicht: {b['src']}")
                ok = False
        ctx.close()

        # Rendern: je Folienbreite die Pixeldichte, die genau das Zielformat ergibt.
        # Folien gleicher Breite teilen sich einen Ladevorgang.
        dateien = []
        offen: dict[float, tuple] = {}
        for f in folien:
            dsf = round(breite / f["breite"], 4)
            if dsf not in offen:
                for alt in offen.values():
                    alt[0].close()
                offen = {dsf: laden(dsf)}
            seite = offen[dsf][1]
            el = seite.locator(f'[data-ig-folie="{f["index"]}"]')
            png = el.screenshot(type="png", animations="disabled")
            bild = Image.open(io.BytesIO(png))
            if bild.size != (breite, hoehe):
                if max(abs(bild.size[0] - breite), abs(bild.size[1] - hoehe)) > 3:
                    fehler(f"Folie {f['index'] + 1}: gerendert {bild.size}, erwartet {(breite, hoehe)} "
                           f"— nicht gespeichert.")
                    ok = False
                    continue
                bild = bild.resize((breite, hoehe), Image.LANCZOS)
            if bild.mode != "RGB":
                grund = Image.new("RGB", bild.size, (255, 255, 255))
                grund.paste(bild, mask=bild.getchannel("A") if "A" in bild.getbands() else None)
                bild = grund
            name = ausgabe / f"{slug}-{f['index'] + 1:02d}.png"
            bild.save(name, "PNG", optimize=True)
            dateien.append(name)
            label = f"  {f['label']}" if f["label"] else ""
            print(f"  {name.relative_to(ROOT_DIR)}  {bild.size[0]} × {bild.size[1]}{label}")
        for alt in offen.values():
            alt[0].close()
        browser.close()
    httpd.shutdown()

    with zipfile.ZipFile(ausgabe / f"{slug}.zip", "w", zipfile.ZIP_STORED) as z:
        for d in dateien:
            z.write(d, d.name)
    print(f"  {(ausgabe / (slug + '.zip')).relative_to(ROOT_DIR)}")
    print("  OK" if ok else "  MIT FEHLERN — PNGs liegen vor, sind aber nicht freigegeben.")
    return ok


def inhalt_setzen(datei: Path, args, kennzeichnen: bool = True) -> Path:
    """content.json → HTML unter output/instagram/_html/<slug>.html."""
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    import instagram_inhalt
    try:
        post = instagram_inhalt.laden(datei, args.min, args.max)
    except instagram_inhalt.InhaltsFehler as e:
        print(f"\n{datei.parent.name}: {datei.relative_to(ROOT_DIR)}")
        for z in str(e).splitlines():
            fehler(z)
        return None
    if not kennzeichnen:
        post["ki"] = False
    ziel = OUTPUT_DIR / "_html" / f"{datei.parent.name}.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(instagram_inhalt.html_setzen(post), encoding="utf-8")
    return ziel


def caption_schreiben(datei: Path, slug: str) -> None:
    post = json.loads(datei.read_text(encoding="utf-8"))
    tags = " ".join("#" + t.lstrip("#") for t in post.get("hashtags", []))
    text = (post.get("caption", "").strip() + ("\n\n" + tags if tags else "")).strip()
    if text:
        (OUTPUT_DIR / slug / f"{slug}-caption.txt").write_text(text + "\n", encoding="utf-8")


def _graustufen(datei: Path):
    """Für den Vergleich: weichgezeichnet und ohne 3 px Rand.

    Im Claude-Design-Canvas liegen die Artboards auf halben Pixeln. Dadurch
    sitzen im Export einzelne Kanten 1 px versetzt, und am Rand scheint der
    Canvas-Grund durch. Beides ist Rundung, kein Layoutfehler; eine falsche
    Schriftgröße oder ein verrutschter Block liegt weit über der Schwelle.
    """
    import numpy as np
    from PIL import Image, ImageFilter
    bild = Image.open(datei).convert("L").filter(ImageFilter.GaussianBlur(2))
    return np.asarray(bild, dtype=int)[3:-3, 3:-3]


def gegenprobe(args) -> int:
    """Baut die Referenz-Posts aus content.json und vergleicht pixelweise mit dem Export."""
    ref_args = argparse.Namespace(**{**vars(args), "min": 1, "max": 100, "selector": None})
    if not bauen(html_finden(REFERENZ_DIR, None), "referenz", ref_args):
        return 1
    status = 0
    for slug, runde in GEGENPROBE.items():
        # Ohne KI-Label: verglichen wird die Vorlage mit dem Design, und die
        # Referenz trägt das Label im Kopf noch nicht.
        html = inhalt_setzen(CONTENT_DIR / slug / "content.json", args, kennzeichnen=False)
        if not html or not bauen(html, slug, args):
            status = 1
            continue
        start = {"4a": 1, "4b": 8, "4c": 15}[runde]
        for i in range(7):
            soll = _graustufen(OUTPUT_DIR / "referenz" / f"referenz-{start + i:02d}.png")
            ist = _graustufen(OUTPUT_DIR / slug / f"{slug}-{i + 1:02d}.png")
            anteil = float((abs(soll - ist) > 40).mean())
            gleich = anteil <= 0.0005
            print(f"  {runde}-{i + 1:02d}: {'gleich' if gleich else 'WEICHT AB'}"
                  f" ({anteil:.3%} der Fläche über der Schwelle)")
            status |= not gleich
    print("\nGegenprobe", "bestanden" if status == 0 else "NICHT bestanden")
    return status


PLAN = CONTENT_DIR / "plan.csv"
PLAN_STATUS = ("idee", "entwurf", "freigegeben", "gepostet")
MARKER = re.compile(r"\[(ANGABE FEHLT|ZU PRÜFEN)[^\]]*\]")


def plan_lesen() -> list[dict]:
    import csv
    with PLAN.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def plan_pruefen(args) -> int:
    """Übersicht über den Content-Plan und seine Widersprüche."""
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    import instagram_inhalt
    zeilen = plan_lesen()
    status = 0
    zaehler: dict[str, int] = {}
    gesehen: set[str] = set()
    print(f"{'Nr':<8}{'Termin':<12}{'Status':<13}{'Ordner':<26}Befund")
    for z in zeilen:
        nr, ordner, st = z["nr"].strip(), z["ordner"].strip(), z["status"].strip()
        zaehler[st] = zaehler.get(st, 0) + 1
        befund = []
        if st not in PLAN_STATUS:
            befund.append(f"Status {st!r} unbekannt ({', '.join(PLAN_STATUS)})")
        if nr in gesehen:
            befund.append("Nummer doppelt")
        gesehen.add(nr)
        datei = CONTENT_DIR / ordner / "content.json" if ordner else None
        if st != "idee":
            if not datei or not datei.is_file():
                befund.append("content.json fehlt")
            else:
                text = datei.read_text(encoding="utf-8")
                post = json.loads(text)
                if post.get("plan") != nr:
                    befund.append(f"content.json trägt plan={post.get('plan')!r}")
                try:
                    instagram_inhalt.vorbereiten(post, args.min, args.max)
                except instagram_inhalt.InhaltsFehler as e:
                    befund.append(f"{len(str(e).splitlines())} Inhaltsfehler")
                offen = MARKER.findall(text)
                if offen and st in ("freigegeben", "gepostet"):
                    befund.append(f"{len(offen)} offene Marker, aber {st}")
                elif offen:
                    befund.append(f"{len(offen)} offene Marker")
        hart = [b for b in befund if not b.endswith("offene Marker")]
        status |= bool(hart)
        print(f"{nr:<8}{z['termin'].strip():<12}{st:<13}{ordner:<26}{'; '.join(befund) or 'ok'}")
    ohne_plan = sorted(p.parent.name for p in CONTENT_DIR.glob("*/content.json")
                       if p.parent.name not in {z["ordner"].strip() for z in zeilen})
    for o in ohne_plan:
        print(f"{'—':<8}{'':<12}{'':<13}{o:<26}nicht im Plan")
        status = 1
    print("\n" + ", ".join(f"{k}: {v}" for k, v in zaehler.items()))
    return status


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("quelle", nargs="?",
                    help="content.json, Post-Ordner, HTML-Datei oder ZIP aus Claude Design")
    ap.add_argument("--alle", action="store_true", help="jeden Post unter content/instagram/ bauen")
    ap.add_argument("--gegenprobe", action="store_true",
                    help="Referenz-Posts aus content.json nachbauen und mit dem Export vergleichen")
    ap.add_argument("--plan", action="store_true",
                    help="Content-Plan (content/instagram/plan.csv) gegen die Posts prüfen")
    ap.add_argument("--slug", help="Name des Posts (Ordner und Dateinamen)")
    ap.add_argument("--datei", help="HTML-Datei im Ordner, falls es mehrere gibt")
    ap.add_argument("--selector", help="CSS-Selektor für die Folien")
    ap.add_argument("--format", choices=FORMATE, default="4:5", help="Standard 4:5 (1080 × 1350)")
    ap.add_argument("--min", type=int, default=7, help="Mindestzahl Folien (Standard 7)")
    ap.add_argument("--max", type=int, default=10, help="Höchstzahl Folien (Standard 10)")
    ap.add_argument("--warten", type=int, default=800, help="ms nach dem Laden (Standard 800)")
    args = ap.parse_args()

    if args.gegenprobe:
        return gegenprobe(args)
    if args.plan:
        return plan_pruefen(args)

    auftraege: list[tuple[Path | None, str, Path | None]] = []
    if args.alle:
        for datei in sorted(CONTENT_DIR.glob("*/content.json")):
            auftraege.append((inhalt_setzen(datei, args), datei.parent.name, datei))
    elif args.quelle:
        quelle = Path(args.quelle).expanduser().resolve()
        if not quelle.exists():
            sys.exit(f"Nicht gefunden: {quelle}")
        if quelle.is_dir() and (quelle / "content.json").is_file():
            quelle = quelle / "content.json"
        if quelle.name == "content.json":
            slug = args.slug or quelle.parent.name
            auftraege.append((inhalt_setzen(quelle, args), slug, quelle))
        elif quelle.suffix.lower() == ".zip" and quelle.parent.parent != SOCIAL_DIR:
            slug = args.slug or slug_aus(quelle.stem)
            ziel = SOCIAL_DIR / slug
            entpacken(quelle, ziel)
            auftraege.append((html_finden(ziel, args.datei), slug, None))
        else:
            if quelle.suffix.lower() == ".zip":
                quelle = quelle.parent
            ordner = quelle if quelle.is_dir() else quelle.parent
            slug = args.slug or slug_aus(ordner.name if quelle.is_dir() or ordner != SOCIAL_DIR
                                         else quelle.stem)
            auftraege.append((html_finden(quelle, args.datei), slug, None))
    else:
        ap.print_help()
        return 2

    ergebnisse = []
    for html, slug, inhalt in auftraege:
        if html is None:
            ergebnisse.append(False)
            continue
        ergebnisse.append(bauen(html, slug, args))
        if inhalt:
            caption_schreiben(inhalt, slug)
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
