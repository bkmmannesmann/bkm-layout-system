#!/usr/bin/env python3
"""Liest content/instagram/<post>/content.json und setzt daraus das Karussell-HTML.

Wird von scripts/build_instagram.py benutzt; allein aufgerufen prüft es nur:

    python3 scripts/instagram_inhalt.py content/instagram/<post>/content.json

Die Folientypen und Blöcke stammen aus der Referenz in templates/instagram/referenz/
und sind in docs/INSTAGRAM.md beschrieben. Farbwerte gibt es im Inhalt nicht: eine
Folie ist „dunkel" oder „hell", daraus folgen Grund, Schrift- und Akzentfarbe.

Auszeichnung im Text:  *Wort*  → Akzentfarbe (Lime auf dunkel, Transition Green auf hell)
                       **Wort** → fett
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = ROOT_DIR / "templates" / "instagram"
DATEIEN = TEMPLATE_DIR / "dateien"

LIME, TRANS = "#b4e717", "#287d4b"

FOLIENTYPEN = {"standard", "cover-hell", "cover-wege", "wege-vergleich", "schluss-wege"}
BLOCKTYPEN = {"rubrik", "headline", "text", "punkte", "zeilen", "schritte", "karten",
              "ursachen", "hinweis", "gegenueber", "vorteile", "bild", "badge"}
TEXTUREN = {"deep-1", "deep-2", "deep-3", "hell-1", "hell-2", "hell-3"}
ICONS = {"check", "check-circle", "warning", "clock", "package", "certificate",
         "clipboard-text", "info", "arrow-right", "arrow-left"}
VERLAEUFE = {
    "leicht": "linear-gradient(180deg,rgba(15,38,32,0.35) 0%,rgba(15,38,32,0.82) 45%,rgba(15,38,32,0.96) 75%)",
    "mittel": "linear-gradient(180deg,rgba(15,38,32,0.7) 0%,rgba(15,38,32,0.9) 50%,rgba(15,38,32,0.97) 100%)",
    "kraeftig": "linear-gradient(180deg,rgba(15,38,32,0.72) 0%,rgba(15,38,32,0.9) 45%,rgba(15,38,32,0.97) 100%)",
}

BLOCK_VORGABEN = {
    "headline": {"groesse": 64, "versal": False, "max_breite": None, "zeilenhoehe": None},
    "text": {"groesse": 30, "max_breite": 820},
    "punkte": {"icon": "check", "abstand": 26},
    "bild": {"hoehe": 460, "fokus": "50% 50%"},
}


class InhaltsFehler(Exception):
    pass


# ── Filter für die Vorlage ────────────────────────────────────────────────

def auszeichnen(text: str, akzent: str) -> str:
    t = html.escape(str(text), quote=False)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", rf'<b style="color:{akzent}">\1</b>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", rf'<span style="color:{akzent}">\1</span>', t)
    return t


def pfad(name: str) -> str:
    """Bild aus templates/instagram/dateien/ (nur Dateiname) oder relativ zur Repo-Wurzel."""
    return "/templates/instagram/dateien/" + name if "/" not in name else "/" + name.lstrip("/")


def pfad_datei(name: str) -> Path:
    return DATEIEN / name if "/" not in name else ROOT_DIR / name.lstrip("/")


def icon_datei(name: str) -> str:
    return f"icon-{name}.svg"


# ── Vorgaben und Prüfung ──────────────────────────────────────────────────

def _bilder(obj, gefunden: list[str]) -> None:
    """Sammelt alle Bildangaben (Schlüssel bild, portrait, produkt)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("bild", "portrait", "produkt") and isinstance(v, str):
                gefunden.append(v)
            else:
                _bilder(v, gefunden)
    elif isinstance(obj, list):
        for v in obj:
            _bilder(v, gefunden)


def _farbfelder(obj, weg: str, fehler: list[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith(("_bg", "_color", "farbe")) or (isinstance(v, str) and re.search(r"#[0-9a-fA-F]{3,6}\b", v)):
                fehler.append(f"{weg}.{k}: keine Farbwerte im Inhalt — Fläche über 'flaeche' wählen")
            _farbfelder(v, f"{weg}.{k}", fehler)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _farbfelder(v, f"{weg}[{i}]", fehler)


def vorbereiten(post: dict, min_folien: int = 7, max_folien: int = 10) -> dict:
    fehler: list[str] = []
    folien = post.get("folien") or []
    if not min_folien <= len(folien) <= max_folien:
        fehler.append(f"{len(folien)} Folien — erwartet {min_folien} bis {max_folien}")
    _farbfelder(folien, "folien", fehler)

    for n, f in enumerate(folien, 1):
        wo = f"Folie {n}"
        typ = f.setdefault("typ", "standard")
        if typ not in FOLIENTYPEN:
            fehler.append(f"{wo}: unbekannter Typ {typ!r} ({', '.join(sorted(FOLIENTYPEN))})")
            continue
        flaeche = f.setdefault("flaeche", "hell" if typ == "cover-hell" else "dunkel")
        if flaeche not in ("dunkel", "hell"):
            fehler.append(f"{wo}: flaeche ist 'dunkel' oder 'hell', nicht {flaeche!r}")
        f["dunkel"] = flaeche == "dunkel"
        f["akzent"] = LIME if f["dunkel"] else TRANS
        f["schluss"] = n == len(folien)
        f["textur_gesetzt"] = "textur" in f
        f.setdefault("textur", (f"deep-{(n - 1) % 3 + 1}" if f["dunkel"] else "hell-2"))
        for k in ("textur", "textur_links", "textur_rechts"):
            if k in f and f[k] not in TEXTUREN:
                fehler.append(f"{wo}: {k} {f[k]!r} unbekannt ({', '.join(sorted(TEXTUREN))})")
        f.setdefault("textur_links", "deep-2")
        f.setdefault("textur_rechts", "hell-2")
        f.setdefault("padding", "96px 108px 340px" if f["schluss"] and f.get("cta") else "96px 108px 300px")
        f.setdefault("ausrichtung", "center")
        f["ausrichtung"] = {"oben": "flex-start", "mitte": "center", "unten": "flex-end"}.get(
            f["ausrichtung"], f["ausrichtung"])
        f.setdefault("abstand", 44)
        f.setdefault("chevrons", False)
        f.setdefault("hintergrund", {})
        if n > 1 and not f["schluss"] and not f.get("kapitel") and typ != "cover-hell":
            fehler.append(f"{wo}: 'kapitel' fehlt — steht im Maßband (z. B. 'Kurz-Check')")
        ff = f["hintergrund"].get("foto_flaeche")
        if ff:
            ff.setdefault("fokus", "50% 50%")
            ff.setdefault("verlauf", "mittel")
            if ff["verlauf"] not in VERLAEUFE:
                fehler.append(f"{wo}: verlauf {ff['verlauf']!r} unbekannt ({', '.join(VERLAEUFE)})")
        fb = f["hintergrund"].get("foto_box")
        if fb:
            fb.setdefault("oben", 200)
            fb.setdefault("hoehe", 486)
            fb.setdefault("fokus", "50% 40%")
        if "foto" in f:
            f["foto"].setdefault("fokus", "50% 50%")

        for b in f.setdefault("bloecke", []):
            bt = b.get("typ")
            if bt not in BLOCKTYPEN:
                fehler.append(f"{wo}: unbekannter Block {bt!r} ({', '.join(sorted(BLOCKTYPEN))})")
                continue
            for k, v in BLOCK_VORGABEN.get(bt, {}).items():
                b.setdefault(k, v)
            for k in ("karten", "vorteile"):
                for e in b.get(k, []):
                    if e.get("icon") and e["icon"] not in ICONS:
                        fehler.append(f"{wo}: Icon {e['icon']!r} unbekannt ({', '.join(sorted(ICONS))})")

    bilder: list[str] = []
    _bilder(folien, bilder)
    for b in bilder:
        if not pfad_datei(b).is_file():
            fehler.append(f"Bild fehlt: {b}")
    if fehler:
        raise InhaltsFehler("\n".join(fehler))
    return post


# ── KI-Kennzeichnung ──────────────────────────────────────────────────────
#
# Für Instagram gilt: jedes Foto bekommt den Vermerk „AI GENERATED" als eigenes
# Element über dem Bildkasten — außer es steht im Register unter keine_ki. Die
# Bilder kommen ohne Vermerk aus der Erzeugung; das Setzen ist Aufgabe des Baus.
# Größe und Abstand nach brand.json (ai_generated_images.marke), gemessen am
# Kasten, nicht an der Datei. Die Ecke nach dem Kontrast des sichtbaren
# Ausschnitts. Trägt das Motiv bereits einen eingebrannten Vermerk, wird dessen
# Ecke genommen, damit nicht zwei nebeneinander stehen.

REGISTER = ROOT_DIR / "assets" / "kennzeichnung" / "register.json"
# Zwei Fassungen desselben Labels, nach dem Grund unter dem Label gewählt:
# Lime-Pille auf dunklem Grund, Deep-Green-Pille auf hellem. Benannt nach der
# Farbe der Pille. Die Pille trägt ihren Kontrast selbst; die Wahl sorgt nur
# dafür, dass sie sich vom Grund absetzt und nicht darin aufgeht.
VERMERK_SVG = {"dunkel": "/assets/kennzeichnung/bkm-ai-generated-lime.svg",
               "hell": "/assets/kennzeichnung/bkm-ai-generated-deep.svg"}
VERMERK_VERHAELTNIS = 1384.24 / 266.41
HELL_AB = 0.55   # mittlere Helligkeit unter dem Label, ab der der Grund als hell gilt
KLEINSTER_KASTEN = 300   # darunter wäre die Marke (mind. 90 px) ein Drittel des Bildes


def _fokus(text: str) -> tuple[float, float]:
    teile = [float(t.rstrip("%")) / 100 for t in str(text).split()]
    return (teile + [0.5, 0.5])[:2] if len(teile) == 1 else tuple(teile[:2])


def _sichtbar(datei: Path, w: int, h: int, fokus: str, sicht_h: int | None = None):
    """Der Ausschnitt, den object-fit:cover im Kasten zeigt, auf Kastengröße gerechnet."""
    from PIL import Image
    bild = Image.open(datei).convert("L")
    bw, bh = bild.size
    s = max(w / bw, h / bh)
    fx, fy = _fokus(fokus)
    x0 = (bw * s - w) * fx / s
    y0 = (bh * s - h) * fy / s
    ausschnitt = bild.crop((round(x0), round(y0), round(x0 + w / s), round(y0 + h / s)))
    ausschnitt = ausschnitt.resize((w, h))
    if sicht_h:
        ausschnitt = ausschnitt.crop((0, 0, w, sicht_h))
    return ausschnitt, (x0, y0, s, bw, bh)


_eingebrannt_cache: dict[str, dict] = {}


def _eingebrannt(datei: Path) -> dict:
    schluessel = str(datei)
    if schluessel not in _eingebrannt_cache:
        sys.path.insert(0, str(ROOT_DIR / "scripts"))
        import kennzeichnung as K
        _eingebrannt_cache[schluessel] = K.finde(datei)
    return _eingebrannt_cache[schluessel]


def _keine_ki() -> set[str]:
    if not REGISTER.exists():
        return set()
    return set(json.loads(REGISTER.read_text(encoding="utf-8")).get("keine_ki", []))


def _vermerk(name: str, kasten: tuple[int, int, int, int], fokus: str, wo: str,
             meldungen: list[str], sicht_h: int | None = None,
             abgedunkelt: bool = False) -> dict | None:
    """Lage des Vermerks im Kasten (links, top, breite, hoehe der Box; ecke, marke, rand)."""
    import numpy as np
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    import kennzeichnung as K
    rel = str(pfad_datei(name).relative_to(ROOT_DIR))
    if rel in _keine_ki():
        return None
    kx, ky, w, h = kasten
    if w < KLEINSTER_KASTEN:
        meldungen.append(f"{wo}: {name} steht nur {w} px breit — kein Platz für den Vermerk. "
                         f"Ist es kein KI-Bild, unter keine_ki in {REGISTER.relative_to(ROOT_DIR)} eintragen.")
        return None
    regel = K.regeln()
    marke = max(int(regel["mindestbreite_px"]), round(w * regel["breite_anteil"]))
    mh = round(marke / VERMERK_VERHAELTNIS)
    rand = round(w * regel["rand_anteil"])
    sicht, (x0, y0, s, bw, bh) = _sichtbar(pfad_datei(name), w, h, fokus, sicht_h)
    hh = sicht.size[1]
    grau = np.asarray(sicht, dtype=np.float32)
    luft = round(mh * 0.45)

    def eignung(ecke):
        x = w - rand - marke if "rechts" in ecke else rand
        y = hh - rand - mh
        return K._dunkelheit(grau[max(0, y - luft):y + mh + luft, max(0, x - luft):x + marke + luft])

    rang = sorted(regel["ecken"], key=eignung, reverse=True)
    ecke = rang[0]
    x = w - rand - marke if "rechts" in ecke else rand
    y = hh - rand - mh
    alt = _eingebrannt(pfad_datei(name))
    if alt.get("gefunden"):
        # Ein alter, weißer Vermerk ist eingebrannt. Die deckende Pille legt sich
        # mittig darüber und ersetzt ihn sichtbar — sonst stünden zwei Marken da.
        ax, ay, aw, ah = alt["kasten"]
        ox, oy, ow, oh = (ax - x0) * s, (ay - y0) * s, aw * s, ah * s
        if ox < w and oy < hh and ox + ow > 0 and oy + oh > 0:
            marke = max(marke, round(ow) + 8, round((oh + 6) * VERMERK_VERHAELTNIS))
            mh = round(marke / VERMERK_VERHAELTNIS)
            x = min(max(rand, round(ox + ow / 2 - marke / 2)), w - marke - rand)
            y = min(max(rand, round(oy + oh / 2 - mh / 2)), hh - mh - rand)
    grund = grau[max(0, y - luft):y + mh + luft, max(0, x - luft):x + marke + luft]
    hell = not abgedunkelt and float(grund.mean()) / 255 >= HELL_AB
    return {"links": kx, "oben": ky, "breite": w, "hoehe": hh, "x": x, "y": y,
            "marke": marke, "svg": VERMERK_SVG["hell" if hell else "dunkel"]}


def vermerke_setzen(post: dict) -> list[str]:
    """Hängt an jede Fotoplatzierung die Lage ihres Vermerks. Liefert Hinweise."""
    meldungen: list[str] = []
    for n, f in enumerate(post["folien"], 1):
        wo = f"Folie {n}"
        massband = n > 1
        h = f.get("hintergrund", {})
        if h.get("foto_box"):
            fb = h["foto_box"]
            fb["vermerk"] = _vermerk(fb["bild"], (108, fb["oben"], 864, fb["hoehe"]), fb["fokus"], wo, meldungen)
        if h.get("foto_flaeche"):
            ff = h["foto_flaeche"]
            ff["vermerk"] = _vermerk(ff["bild"], (0, 0, 1080, 1350), ff["fokus"], wo, meldungen,
                                     sicht_h=1200 if massband else None, abgedunkelt=True)
        if f.get("foto"):
            hoehe = {"cover-hell": 608, "cover-wege": 900, "schluss-wege": 700}.get(f["typ"])
            if hoehe:
                f["foto"]["vermerk"] = _vermerk(f["foto"]["bild"], (0, 0, 1080, hoehe),
                                                f["foto"]["fokus"], wo, meldungen,
                                                abgedunkelt=f["typ"] != "cover-hell")
        for b in f.get("bloecke", []):
            if b.get("typ") == "bild":
                b["vermerk"] = _vermerk(b["bild"], (0, 0, 864, b["hoehe"]), b["fokus"], wo, meldungen)
            for u in b.get("zeilen", []) if b.get("typ") == "ursachen" else []:
                _vermerk(u["bild"], (0, 0, 120, 120), u.get("fokus", "62% 55%"), wo, meldungen)
            for v in b.get("vorteile", []):
                if v.get("portrait"):
                    _vermerk(v["portrait"], (0, 0, 64, 64), "50% 20%", wo, meldungen)
        if f.get("typ") == "wege-vergleich":
            for seite in ("links", "rechts"):
                _vermerk(f[seite]["portrait"], (0, 0, 140, 140), "50% 18%", wo, meldungen)
    return meldungen


def html_setzen(post: dict) -> str:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined  # noqa: F401
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False,
                      trim_blocks=False, lstrip_blocks=False)
    env.filters.update(auszeichnen=auszeichnen, pfad=pfad, icon_datei=icon_datei,
                       verlauf=lambda name: VERLAEUFE[name])
    return env.get_template("karussell.html.j2").render(post=post)


def laden(datei: Path, min_folien: int = 7, max_folien: int = 10) -> dict:
    post = json.loads(datei.read_text(encoding="utf-8"))
    return vorbereiten(post, min_folien, max_folien)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        post = laden(Path(sys.argv[1]))
    except InhaltsFehler as e:
        for z in str(e).splitlines():
            print("  FEHLER  ", z)
        return 1
    print(f"OK — {len(post['folien'])} Folien")
    return 0


if __name__ == "__main__":
    sys.exit(main())
