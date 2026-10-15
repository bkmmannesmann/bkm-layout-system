#!/usr/bin/env python3
"""Rendert Instagram-Karussells aus Claude-Design-HTML zu verlustfreien PNGs.

Der Entwurf entsteht in Claude Design und kommt unverändert hierher. Gesetzt
wird er von Chromium, demselben Browser, in dem Claude Design ihn zeigt —
deshalb sieht das PNG aus wie der Entwurf und nicht wie eine Nachbildung.

    python3 scripts/build_instagram.py social/instagram/<post>/
    python3 scripts/build_instagram.py social/instagram/<post>/index.html
    python3 scripts/build_instagram.py ~/Downloads/<projekt>.zip --slug <post>
    python3 scripts/build_instagram.py --alle

Angenommen werden beide Exportwege aus Claude Design:

  Project archive   ZIP mit HTML und allen Dateien. Wird nach
                    social/instagram/<slug>/ entpackt und von dort gebaut.
  Standalone HTML   Eine Datei, alle Bilder und Schriften eingebettet.

Welche Elemente Folien sind, wird in dieser Reihenfolge gesucht:

  1. --selector, wenn angegeben
  2. Elemente mit data-slide              (eigene Konvention)
  3. Elemente mit data-screen-label       (Artboards in Claude Design)
  4. die äußersten Elemente im Seitenverhältnis des Zielformats

Jede Folie wird so skaliert, dass sie genau im Zielformat herauskommt
(Standard 1080 × 1350, Instagram-Hochformat 4:5). Ein Artboard, das im
Entwurf 540 px breit ist, wird mit doppelter Pixeldichte gerendert, nicht
hochgerechnet.

Ausgabe: output/instagram/<slug>/<slug>-01.png … sowie <slug>.zip mit allen
Folien. PNG, RGB ohne Alphakanal, sRGB — direkt für den Upload.

Abbruch (Exit-Code 1), wenn eine Schrift oder ein Bild nicht lädt, eine
Folie nicht ins Format passt oder die Folienzahl außerhalb von 7 bis 10
liegt (--min/--max). Fehlende Schriften ersetzt Chromium sonst still.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
SOCIAL_DIR = ROOT_DIR / "social" / "instagram"
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
  return {schriften, bilder, verlangt: [...verlangt]};
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
    drift_pruefen(html)
    ok = True

    with sync_playwright() as pw:
        exe = chromium_pfad()
        browser = pw.chromium.launch(**({"executable_path": exe} if exe else {}))

        def laden(dsf: float):
            ctx = browser.new_context(viewport={"width": 1600, "height": 1200},
                                      device_scale_factor=dsf)
            seite = ctx.new_page()
            seite.goto(html.resolve().as_uri(), wait_until="networkidle", timeout=120_000)
            seite.wait_for_timeout(args.warten)
            # Animationen und Übergänge stehen im Endzustand.
            seite.add_style_tag(content="*,*::before,*::after{animation-duration:0s!important;"
                                        "animation-delay:0s!important;transition:none!important;"
                                        "caret-color:transparent!important}")
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
        for b in pruefung["bilder"]:
            if not b["ok"]:
                fehler(f"Bild lädt nicht: {b['src']}")
                ok = False
        ctx.close()

        # Rendern: je Folienbreite die Pixeldichte, die genau das Zielformat ergibt.
        dateien = []
        for f in folien:
            dsf = breite / f["breite"]
            ctx, seite, _ = laden(dsf)
            el = seite.locator(f'[data-ig-folie="{f["index"]}"]')
            png = el.screenshot(type="png", animations="disabled")
            ctx.close()
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
        browser.close()

    with zipfile.ZipFile(ausgabe / f"{slug}.zip", "w", zipfile.ZIP_STORED) as z:
        for d in dateien:
            z.write(d, d.name)
    print(f"  {(ausgabe / (slug + '.zip')).relative_to(ROOT_DIR)}")
    print("  OK" if ok else "  MIT FEHLERN — PNGs liegen vor, sind aber nicht freigegeben.")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("quelle", nargs="?", help="Ordner, HTML-Datei oder ZIP aus Claude Design")
    ap.add_argument("--alle", action="store_true", help="jeden Ordner unter social/instagram/ bauen")
    ap.add_argument("--slug", help="Name des Posts (Ordner und Dateinamen)")
    ap.add_argument("--datei", help="HTML-Datei im Ordner, falls es mehrere gibt")
    ap.add_argument("--selector", help="CSS-Selektor für die Folien")
    ap.add_argument("--format", choices=FORMATE, default="4:5", help="Standard 4:5 (1080 × 1350)")
    ap.add_argument("--min", type=int, default=7, help="Mindestzahl Folien (Standard 7)")
    ap.add_argument("--max", type=int, default=10, help="Höchstzahl Folien (Standard 10)")
    ap.add_argument("--warten", type=int, default=800, help="ms nach dem Laden (Standard 800)")
    args = ap.parse_args()

    auftraege: list[tuple[Path, str]] = []
    if args.alle:
        for ordner in sorted(p for p in SOCIAL_DIR.iterdir() if p.is_dir()):
            auftraege.append((html_finden(ordner, None), ordner.name))
    elif args.quelle:
        quelle = Path(args.quelle).expanduser().resolve()
        if not quelle.exists():
            sys.exit(f"Nicht gefunden: {quelle}")
        if quelle.suffix.lower() == ".zip" and quelle.parent.parent != SOCIAL_DIR:
            slug = args.slug or slug_aus(quelle.stem)
            ziel = SOCIAL_DIR / slug
            entpacken(quelle, ziel)
            auftraege.append((html_finden(ziel, args.datei), slug))
        else:
            if quelle.suffix.lower() == ".zip":
                quelle = quelle.parent
            ordner = quelle if quelle.is_dir() else quelle.parent
            slug = args.slug or slug_aus(ordner.name if quelle.is_dir() or ordner != SOCIAL_DIR
                                         else quelle.stem)
            auftraege.append((html_finden(quelle, args.datei), slug))
    else:
        ap.print_help()
        return 2

    ergebnisse = [bauen(html, slug, args) for html, slug in auftraege]
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
