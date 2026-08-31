#!/usr/bin/env python3
"""Erzeugt die Canvas-Fassung der Verarbeitungsanleitung.

Die Datei wird nicht von Hand geschrieben, sondern aus derselben
content.json erzeugt wie das PDF. Das ist der Punkt: Canvas und Produktion
sind sonst zwei Wege zu demselben Blatt, und die laufen auseinander. In
diesem Projekt ist das dreimal passiert - bei der Hero-Grafik, bei der
Fotolage und beim Keyvisual, das im Cover als PNG und im Canvas als SVG
stand.

    python3 scripts/build_anleitung_canvas.py content/anleitung-hz250pro/content.json

Ergebnis: templates/brochure/I-Anleitung.dc.html

Immer dieselbe Datei: die Canvas-Gruppe ist eine Arbeitsflaeche fuer ein
Dokument, nicht ein Archiv fuer alle sieben. Wer eine andere Anleitung
darauf legt, ueberschreibt die vorherige - das ist gewollt, denn was
bleiben soll, gehoert ohnehin in den Content zurueck.

Die Pfade werden dabei von ../../ auf die Wurzel umgestellt: die
Canvas-Dateien liegen in templates/brochure/, verweisen aber auf assets/
und uploads/ ohne Praefix - Claude Design loest sie aus der Repo-Wurzel
auf. Dieselbe Konvention wie in den acht bestehenden Gruppen.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = ROOT_DIR / "templates" / "anleitung"
COVER_DIR = ROOT_DIR / "templates" / "cover"
ZIEL = ROOT_DIR / "templates" / "brochure" / "I-Anleitung.dc.html"

GRUPPEN = [
    ("Bibliothek.dc.html", "Bibliothek"),
    ("A-Titelblaetter.dc.html", "A · Titelblätter"),
    ("B-Rahmenseiten.dc.html", "B · Rahmenseiten"),
    ("C-Navigation.dc.html", "C · Navigation"),
    ("D-Textstrecken.dc.html", "D · Textstrecken"),
    ("E-Strecken.dc.html", "E · Strecken"),
    ("F-Verfahren.dc.html", "F · Verfahren"),
    ("G-Produktseiten.dc.html", "G · Produktseiten"),
    ("H-Fachbetrieb.dc.html", "H · Fachbetrieb"),
    ("I-Anleitung.dc.html", "I · Anleitung"),
]

STYLESHEETS = [
    ROOT_DIR / "design-system" / "variables.css",
    ROOT_DIR / "design-system" / "base.css",
    ROOT_DIR / "components" / "components.css",
    TEMPLATE_DIR / "anleitung-spec.css",
]


def wurzelpfade(text):
    """Stellt jeden relativen Verweis auf die Repo-Wurzel um.

    Drei Herkuenfte, drei Tiefen:
      templates/anleitung/  verweist mit ../../  (Bilder im Content)
      design-system/        verweist mit ../     (Schriftdateien)
      templates/cover/      verweist mit ../../  (Logo, Keyvisual, Hero)

    Die Canvas-Datei liegt in templates/brochure/ und verweist ohne
    Praefix; Claude Design loest aus der Repo-Wurzel auf, so wie in den
    acht bestehenden Gruppen. Der erste Durchgang muss ../../ vor ../
    treffen, sonst bliebe ein ../ stehen.
    """
    for auf, ab in (('src="../../', 'src="'), ("url('../../", "url('"),
                    ('url("../../', 'url("'),
                    ('src="../', 'src="'), ("url('../", "url('"),
                    ('url("../', 'url("')):
        text = text.replace(auf, ab)
    return text


def stylesheet_einlesen(pfad):
    """Liest ein Stylesheet und loest @import auf.

    base.css importiert variables.css. Der Import bliebe im Canvas stehen
    und liefe ins Leere, weil die Datei dort nicht neben der HTML liegt -
    die Farben waeren still weg. Beide Dateien werden ohnehin einzeln
    eingebunden, der Import kann also entfallen.
    """
    css = pfad.read_text(encoding="utf-8")
    return re.sub(r"@import\s+[^;]+;", "", css)


def fontfaces_ausduennen(css):
    """Wirft @font-face-Bloecke weg, deren Datei es nicht gibt.

    design-system/base.css deklariert Schnitte, die im Bestand fehlen -
    Unbounded Regular bis ExtraBold, TT Norms Light, Medium, DemiBold und
    die Kursiven. Zwoelf tote Verweise. Im PDF ist das folgenlos, weil sie
    nie gesetzt werden; im Canvas nicht: dort bietet ein deklarierter
    Schnitt sich zur Auswahl an, und genau so ist in die Bestandsfassungen
    der Anleitungen Unbounded SemiBold geraten. Zugelassen sind nur
    Unbounded Black und TT Norms 400 und 700, siehe typography in
    brand.json.
    """
    def behalten(block):
        dateien = re.findall(r"url\(['\"]?([^'\")]+)", block.group(0))
        return block.group(0) if all((ROOT_DIR / d).is_file() for d in dateien) else ""
    return re.sub(r"@font-face\s*\{[^}]*\}", behalten, css)


def seiten_zerlegen(html):
    """Zerlegt den Innenteil in seine Seiten.

    Gesucht wird <section class="anl-page"> ... </section> auf oberster
    Ebene. Verschachtelte section-Elemente gibt es in dieser Vorlage nicht.
    """
    return re.findall(r'(<section class="anl-page">.*?</section>)', html, re.S)


def kopf(titel, untertitel):
    css = fontfaces_ausduennen(
        wurzelpfade("\n".join(stylesheet_einlesen(p) for p in STYLESHEETS)))
    nav = "\n".join(
        f'<a href="{datei}" style="font-family:\'TT Norms Pro\',sans-serif;'
        f'font-size:13px;font-weight:700;padding:6px 12px;border-radius:5px;'
        f'text-decoration:none;'
        + ("background:#1c4b42;color:#b4e717" if datei.startswith("I-")
           else "background:#fff;color:#1c4b42")
        + f'">{name}</a>'
        for datei, name in GRUPPEN)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<meta name="design_doc_mode" content="canvas">
<style>
@font-face{{font-family:'Unbounded';src:url('assets/fonts/Unbounded_900.woff2') format('woff2');font-weight:900;font-display:swap}}
@font-face{{font-family:'TT Norms Pro';src:url('assets/fonts/TT_Norms_Pro_Compact_Regular.woff2') format('woff2');font-weight:400;font-display:swap}}
@font-face{{font-family:'TT Norms Pro';src:url('assets/fonts/TT_Norms_Pro_Bold.woff2') format('woff2');font-weight:700;font-display:swap}}
html,body{{margin:0;padding:0;background:#e9e7e1}}
body{{font-family:'TT Norms Pro',system-ui,sans-serif;color:#494949;-webkit-font-smoothing:antialiased}}
a{{color:#287d4b;text-decoration:none}}
a:hover{{color:#1c4b42;text-decoration:underline}}

/* Erzeugt aus templates/anleitung/. Nicht hier aendern - die Datei wird
   von scripts/build_anleitung_canvas.py neu geschrieben. */
{css}
</style>
</helmet>

<div style="padding:28px 60px 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center">
{nav}
</div>

<section style="padding:60px 60px 120px;display:flex;flex-direction:column;gap:48px">

<div style="max-width:900px;display:flex;flex-direction:column;gap:14px">
<div style="font-family:'TT Norms Pro',sans-serif;font-weight:700;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#4daf46">I · Anleitung</div>
<h1 style="font-family:'Unbounded',sans-serif;font-weight:900;text-transform:uppercase;font-size:44px;line-height:1.05;letter-spacing:-0.02em;color:#1c4b42;margin:0">{titel}</h1>
<p style="margin:0;font-size:17px;line-height:1.6;max-width:70ch">{untertitel}</p>
</div>

<div style="display:flex;flex-wrap:wrap;align-items:flex-start;gap:60px">
"""


def artboard(kennung, label, farbe, inhalt):
    return f"""
<div id="{kennung}" style="display:flex;flex-direction:column;gap:20px">
<div style="display:flex;align-items:baseline;gap:14px;padding-bottom:12px;border-bottom:2px solid #1c4b42">
<span style="font-family:'TT Norms Pro',sans-serif;font-size:13px;font-weight:700;background:#1c4b42;color:#b4e717;padding:5px 10px">{kennung}</span>
<span style="font-family:'Unbounded',sans-serif;font-weight:900;text-transform:uppercase;font-size:20px;letter-spacing:-0.01em;color:#1c4b42">{label}</span>
<span style="font-size:14px;color:#8a8a8a">{farbe}</span>
</div>
<div data-screen-label="{label}" style="width:210mm;height:297mm;position:relative;overflow:hidden;background:#fff;box-shadow:0 18px 50px rgba(28,75,66,.18)">
{inhalt}
</div>
</div>
"""


def baue(content_path):
    from jinja2 import Environment, FileSystemLoader

    content = json.loads(Path(content_path).read_text(encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    innen = env.get_template("template.html").render(**content)
    seiten = seiten_zerlegen(wurzelpfade(innen))

    if len(seiten) != len(content["pages"]):
        print(f"  Zerlegt: {len(seiten)} Seiten, content.json beschreibt "
              f"{len(content['pages'])}. Abbruch.")
        return 1

    teile = [kopf(f"Verarbeitungsanleitung {content['product_name']}",
                  "Erzeugt aus content/anleitung-" +
                  Path(content_path).parent.name.replace("anleitung-", "") +
                  "/content.json. Aenderungen gehoeren in den Content oder in "
                  "templates/anleitung/, nicht in diese Datei — sie wird von "
                  "scripts/build_anleitung_canvas.py neu geschrieben.")]

    # Titelblatt: aus dem Cover-Bauweg, aber selbst gebaut. Vorher wurde
    # gelesen, was gerade in output/covers/ lag - das war der letzte
    # Bauablauf, nicht dieses Produkt. Der Canvas trug damit das
    # Titelblatt eines anderen Dokuments oder den produktneutralen
    # Vorgabetext, je nachdem, was zuletzt gebaut worden war. Aufgefallen
    # am 31.08.2026 an einer Datei, die sich ohne Aenderung am Inhalt
    # unterschied.
    titel_html = ROOT_DIR / "output" / "covers" / "cover_anleitung.html"
    if content.get("cover"):
        sys.path.insert(0, str(ROOT_DIR / "scripts"))
        import build_cover
        titel = dict(content["cover"])
        titel.setdefault("title", content.get("title", ""))
        build_cover.build_cover("anleitung", titel)
    if titel_html.is_file():
        roh = wurzelpfade(titel_html.read_text(encoding="utf-8"))
        m = re.search(r'<div class="cover [^"]*">(.*?)</div>\s*</body>', roh, re.S)
        if m:
            teile.append(artboard("anleitung-titel", "Titelblatt", "Weiß",
                                  m.group(1)))

    ARTEN = {"vorbereitung": ("Vorteile · Vorbereitung", "Weiß"),
             "anleitung": ("Anleitung", "Weiß"),
             "nacharbeit": ("Nacharbeit", "Weiß")}
    zaehler = {}
    for seite, quelle in zip(seiten, content["pages"]):
        art = quelle["type"]
        zaehler[art] = zaehler.get(art, 0) + 1
        label, farbe = ARTEN[art]
        if art == "anleitung":
            label = f"Anleitung {zaehler[art]}"
        kennung = f"anleitung-{art}" + (f"-{zaehler[art]}" if art == "anleitung" else "")
        teile.append(artboard(kennung, label, farbe, seite))

    teile.append("\n</div>\n</section>\n</x-dc>\n</body>\n</html>\n")
    ZIEL.write_text("".join(teile), encoding="utf-8")
    print(f"  {ZIEL.relative_to(ROOT_DIR)}  "
          f"{ZIEL.stat().st_size // 1024} KB, {len(seiten) + 1} Artboards")
    return 0


def main():
    p = argparse.ArgumentParser(description="Erzeugt die Canvas-Fassung.")
    p.add_argument("content")
    a = p.parse_args()
    if not Path(a.content).is_file():
        print(f"Nicht gefunden: {a.content}")
        return 2
    return baue(a.content)


if __name__ == "__main__":
    sys.exit(main())
