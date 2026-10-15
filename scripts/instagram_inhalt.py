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
    post.setdefault("ki", True)
    if not isinstance(post["ki"], bool):
        fehler.append("'ki' ist true oder false")
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
# Ein Karussell gilt als Ganzes als KI-erzeugt. Jede Folie trägt deshalb das
# Label „AI GENERATED" im Kopf, links neben dem Zähler — fest im Design, nicht
# auf einem Foto. Die Vorlage wählt die Fassung nach der Fläche der Folie.
# "ki": false in der content.json schaltet es für einen Post ab, der nachweislich
# ohne KI-Inhalte auskommt.

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
