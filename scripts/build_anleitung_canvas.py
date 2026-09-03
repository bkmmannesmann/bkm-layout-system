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

Ausgegeben werden nur die A4-Blaetter - keine Gruppen-Navigation, kein
Kopfblock, keine Labelleiste. Die acht Vorlagengruppen A bis H tragen das
zu Recht, weil aus ihnen ausgewaehlt wird; die Anleitung ist ein Dokument
und wird als Blattfolge gelesen.

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

STYLESHEETS = [
    ROOT_DIR / "design-system" / "variables.css",
    ROOT_DIR / "design-system" / "base.css",
    ROOT_DIR / "components" / "components.css",
    TEMPLATE_DIR / "anleitung-spec.css",
    COVER_DIR / "cover-spec.css",
]

# Aus cover-spec.css duerfen nur die .cover-Regeln in den Canvas. Die
# Datei ist fuer eine Seite geschrieben, die allein im Browser steht:
# html und body auf 210x297 mm zu nageln reisst die Arbeitsflaeche
# auseinander, @page traegt dort nichts, und jeder @font-face bietet im
# Canvas einen Schnitt zur Auswahl an, den es im Haus nicht gibt - so ist
# in die Bestandsanleitungen Unbounded SemiBold geraten.
COVER_GLOBAL = (
    r"@page\s*\{[^}]*\}",
    r"(?m)^\*\s*\{[^}]*\}",
    r"(?m)^html,\s*body\s*\{[^}]*\}",
    r"@font-face\s*\{[^}]*\}",
)


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
    css = re.sub(r"@import\s+[^;]+;", "", css)
    if pfad == COVER_DIR / "cover-spec.css":
        for muster in COVER_GLOBAL:
            css = re.sub(muster, "", css)
    return css


def fontfaces_ausduennen(css):
    """Duennt die @font-face-Bloecke auf das aus, was gesetzt werden darf.

    Zwei Gruende, einen Block wegzuwerfen: die Datei fehlt, oder der
    Schnitt steht nicht in brand.json.

    design-system/base.css deklariert Schnitte, die im Bestand fehlen -
    Unbounded Regular bis ExtraBold, TT Norms Light, Medium, DemiBold und
    die Kursiven. Zwoelf tote Verweise. Im PDF ist das folgenlos, weil sie
    nie gesetzt werden; im Canvas nicht: dort bietet ein deklarierter
    Schnitt sich zur Auswahl an, und genau so ist in die Bestandsfassungen
    der Anleitungen Unbounded SemiBold geraten. Zugelassen sind nur
    Unbounded Black und TT Norms 400 und 700, siehe typography in
    brand.json.
    """
    marke = json.loads((ROOT_DIR / "brand.json").read_text(encoding="utf-8"))
    typo = marke.get("typography", {})
    erlaubt = {eintrag["family"]: {str(w) for w in eintrag.get("weights", [])}
               for rolle in ("display", "body")
               for eintrag in [typo.get(rolle, {})] if eintrag.get("family")}

    def behalten(block):
        roh = block.group(0)
        dateien = re.findall(r"url\(['\"]?([^'\")]+)", roh)
        if not all((ROOT_DIR / d).is_file() for d in dateien):
            return ""
        familie = re.search(r"font-family:\s*['\"]?([^;'\"]+)", roh)
        gewicht = re.search(r"font-weight:\s*(\d+)", roh)
        if familie and gewicht:
            name = familie.group(1).strip()
            # BKM PDF Sans steht bewusst nicht in brand.json: das ist die
            # eingebettete Druckfassung nach AGENTS.md, Regel 11. Nur die
            # beiden Hausfamilien werden auf ihre Schnitte begrenzt.
            if name in erlaubt and gewicht.group(1) not in erlaubt[name]:
                return ""
        return roh
    return re.sub(r"@font-face\s*\{[^}]*\}", behalten, css)


def seiten_zerlegen(html):
    """Zerlegt den Innenteil in seine Seiten.

    Gesucht wird <section class="anl-page"> ... </section> auf oberster
    Ebene. Verschachtelte section-Elemente gibt es in dieser Vorlage nicht.
    """
    return re.findall(r'(<section class="anl-page">.*?</section>)', html, re.S)


def kopf(titel):
    """Rahmen der Canvas-Datei: Helmet, Stylesheet, Blattcontainer.

    Ohne Chrome. Die acht Vorlagengruppen A bis H tragen Navigation,
    Kopfblock und Labelleiste zu Recht - sie sind Sammlungen, aus denen
    ausgewaehlt wird. Die Anleitung ist das nicht: sie ist ein Dokument,
    das als Blattfolge gelesen und weitergegeben wird. Links auf die
    anderen Gruppen sind darin tote Fracht, und der Kopfblock ist Text
    ueber die Datei, nicht Inhalt der Anleitung.

    Der Titel steht nur noch im <title> - er benennt den Reiter, ohne auf
    der Flaeche zu erscheinen.
    """
    css = fontfaces_ausduennen(
        wurzelpfade("\n".join(stylesheet_einlesen(p) for p in STYLESHEETS)))
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel}</title>
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

/* base.css und components.css setzen text-align:justify fuer die
   Broschuerenstrecken. In der Produktion sieht das Titelblatt diese
   beiden Dateien nie - es wird allein aus cover-spec.css gesetzt und
   steht linksbuendig. Im Canvas liegen alle Stylesheets im selben
   Dokument, und ohne diese Zeile stuenden Headline, Subheadline und
   Intro im Blocksatz. cover-spec.css setzt selbst nirgends text-align,
   links ist dort also der Zustand. */
.cover, .cover * {{ text-align: left; }}
</style>
</helmet>

<section style="padding:60px 60px 120px;display:flex;flex-direction:column;gap:48px">

<div style="display:flex;flex-wrap:wrap;align-items:flex-start;gap:60px">
"""


def artboard(kennung, label, inhalt):
    """Ein A4-Blatt, sonst nichts.

    Die Kennung sitzt jetzt am Blatt selbst - #anleitung-titel bleibt
    damit anspringbar, obwohl die Leiste darueber weg ist.
    data-screen-label traegt den Seitennamen fuer Kommentare, ohne
    sichtbar zu sein. Der Farbname stand bis 01.09.2026 in der Leiste; er
    lautete auf allen Blaettern "Weiss" und trug nichts.
    """
    return f"""
<div id="{kennung}" data-screen-label="{label}" style="width:210mm;height:297mm;position:relative;overflow:hidden;background:#fff;box-shadow:0 18px 50px rgba(28,75,66,.18)">
{inhalt}
</div>
"""



def _stilblock(html):
    """Der Inhalt des <style>-Blocks im Helmet."""
    a = html.find("<style>")
    b = html.find("</style>")
    return html[a:b] if a >= 0 and b > a else ""


def check_chrome(html, seiten_soll):
    """Die Anleitung wird ohne Chrome ausgegeben.

    Keine Gruppen-Navigation, kein Kopfblock, keine Labelleiste - sie ist
    ein Dokument, keine Vorlagensammlung. Der Bau hat das dreimal wieder
    eingezogen, weil die Funktionen aus der Bibliothek stammen; darum
    steht es hier als Pruefung und nicht nur im Layoutvertrag.
    """
    fehler = []
    if re.search(r'href="[^"]*\.dc\.html"', html):
        fehler.append("Links auf andere Canvas-Gruppen im Dokument.")

    blaetter = re.findall(r'<div id="([^"]+)" data-screen-label="([^"]+)"'
                          r' style="width:210mm;height:297mm', html)
    if len(blaetter) != seiten_soll:
        fehler.append(f"{len(blaetter)} A4-Blaetter, erwartet {seiten_soll}.")

    aussen = len(re.findall(r"<h1 style=", html))
    if aussen:
        fehler.append(f"{aussen} <h1> ausserhalb der Blaetter - Kopfblock.")

    if "border-bottom:2px solid #1c4b42" in html:
        fehler.append("Labelleiste ueber den Blaettern.")

    if len(set(k for k, _ in blaetter)) != len(blaetter):
        fehler.append("Zwei Blaetter tragen dieselbe Kennung.")
    return fehler


def check_seitenrahmen(html):
    """cover-spec.css ist fuer eine Seite geschrieben, die allein steht.

    html und body auf 210x297 mm zu nageln reisst die Arbeitsflaeche
    auseinander: der Canvas traegt mehrere Blaetter nebeneinander. Die
    Regel darf im Dokument nicht ankommen.
    """
    css = _stilblock(html)
    if re.search(r"(?m)^html,\s*body\s*\{[^}]*210mm", css):
        fehler = "html/body auf Blattmass festgenagelt - aus cover-spec.css."
        return [fehler]
    return []


def check_fotolage(html):
    """Wo das Titelfoto liegt, steht in brand.json - nicht in der CSS.

    Der Canvas zog seine Regel bis 01.09.2026 aus components.css, wo die
    alte vollflaechige Fassung steht. Gemessen wird darum am Ergebnis
    gegen brand.json, und geprueft wird zusaetzlich, ob die Regel auch
    zuletzt kommt: eine spaetere gleichrangige Regel gewaenne still.
    """
    geo = json.loads((ROOT_DIR / "brand.json").read_text(encoding="utf-8"))
    foto = geo.get("cover_geometry", {}).get("photo", {})
    soll_top, soll_hoehe = foto.get("top_mm"), foto.get("height_mm")
    if soll_top is None:
        return []

    css = _stilblock(html)
    regeln = list(re.finditer(r"\.cover__hero\s*\{([^}]*)\}", css))
    if not regeln:
        return ["Keine Regel fuer .cover__hero - cover-spec.css fehlt."]

    letzte = regeln[-1].group(1)
    top = re.search(r"top:\s*([\d.]+)mm", letzte)
    # (?<![-\w]) haelt min-height und max-height heraus - sonst meldet die
    # Pruefung die 150 mm der alten Regel als Hoehe des Fotos.
    hoehe = re.search(r"(?<![-\w])height:\s*([\d.]+)mm", letzte)
    fehler = []
    if not top or abs(float(top.group(1)) - soll_top) > 0.05:
        fehler.append(
            f"Titelfoto beginnt bei {top.group(1) + ' mm' if top else 'unbestimmt'}, "
            f"brand.json sagt {soll_top} mm.")
    if soll_hoehe is not None and (
            not hoehe or abs(float(hoehe.group(1)) - soll_hoehe) > 0.05):
        fehler.append(
            f"Titelfoto ist {hoehe.group(1) + ' mm' if hoehe else 'unbestimmt'} hoch, "
            f"brand.json sagt {soll_hoehe} mm.")
    if 'class="cover cover--' not in html:
        fehler.append("Variantenklasse am Titelblatt fehlt - die "
                      "Variantenregeln greifen dann nicht.")
    return fehler


def check_schriftangebot(html):
    """Was der Canvas an Schnitten anbietet, kann jemand auswaehlen.

    Im PDF ist ein ungenutzter @font-face folgenlos. Hier nicht: ein
    deklarierter Schnitt steht in der Auswahl, und genau so ist in die
    Bestandsanleitungen Unbounded SemiBold geraten. Gemeldet, nicht
    abgebrochen - BKM PDF Sans ist die eingebettete Druckfassung aus
    AGENTS.md und gehoert dorthin.
    """
    marke = json.loads((ROOT_DIR / "brand.json").read_text(encoding="utf-8"))
    typo = marke.get("typography", {})
    erlaubt = {}
    for rolle in ("display", "body"):
        eintrag = typo.get(rolle, {})
        if eintrag.get("family"):
            erlaubt[eintrag["family"]] = {str(w) for w in eintrag.get("weights", [])}

    angeboten = {}
    for block in re.finditer(r"@font-face\s*\{([^}]*)\}", _stilblock(html)):
        b = block.group(1)
        fam = re.search(r"font-family:\s*['\"]?([^;'\"]+)", b)
        gew = re.search(r"font-weight:\s*(\d+)", b)
        if fam:
            angeboten.setdefault(fam.group(1).strip(), set()).add(
                gew.group(1) if gew else "?")

    hinweise = []
    for fam, gewichte in sorted(angeboten.items()):
        if fam not in erlaubt:
            continue
        ueber = sorted(gewichte - erlaubt[fam], key=int)
        if ueber:
            hinweise.append(f"{fam}: {', '.join(ueber)} angeboten, "
                            f"brand.json laesst {', '.join(sorted(erlaubt[fam]))} zu.")
    return hinweise

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

    teile = [kopf(f"Verarbeitungsanleitung {content['product_name']}")]

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
        # Der Wrapper bleibt drin. Ohne ihn fehlt .cover--anleitung, und
        # damit greifen die Variantenregeln nicht - Headline und Intro
        # stuenden in der Vorgabefarbe statt in Deep Green.
        m = re.search(r'(<div class="cover [^"]*">.*?</div>)\s*</body>', roh, re.S)
        if m:
            teile.append(artboard("anleitung-titel", "Titelblatt", m.group(1)))

    ARTEN = {"vorbereitung": "Vorteile · Vorbereitung",
             "anleitung": "Anleitung",
             "nacharbeit": "Nacharbeit"}
    zaehler = {}
    for seite, quelle in zip(seiten, content["pages"]):
        art = quelle["type"]
        zaehler[art] = zaehler.get(art, 0) + 1
        label = ARTEN[art]
        if art == "anleitung":
            label = f"Anleitung {zaehler[art]}"
        kennung = f"anleitung-{art}" + (f"-{zaehler[art]}" if art == "anleitung" else "")
        teile.append(artboard(kennung, label, seite))

    teile.append("\n</div>\n</section>\n</x-dc>\n</body>\n</html>\n")
    ZIEL.write_text("".join(teile), encoding="utf-8")
    print(f"  {ZIEL.relative_to(ROOT_DIR)}  "
          f"{ZIEL.stat().st_size // 1024} KB, {len(seiten) + 1} Artboards")

    fertig = ZIEL.read_text(encoding="utf-8")
    fehler = (check_chrome(fertig, len(seiten) + 1)
              + check_seitenrahmen(fertig)
              + check_fotolage(fertig))
    if fehler:
        print()
        for f in fehler:
            print(f"    {f}")
        return 1

    hinweise = check_schriftangebot(fertig)
    if hinweise:
        print()
        print("    Schnitte, die der Canvas zur Auswahl stellt:")
        for h in hinweise:
            print(f"      {h}")
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
