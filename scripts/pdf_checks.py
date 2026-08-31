#!/usr/bin/env python3
"""Prueft ein erzeugtes PDF gegen Fehler, die sonst still durchgehen.

Zwei Fehler sieht man dem fertigen PDF nicht an:

Die Schrift. Verweist ein Stylesheet auf eine Datei, die es nicht gibt, meldet
WeasyPrint das nicht, sondern setzt eine Ersatzschrift. Der Innenteil lief so
zeitweise in DejaVu Sans.

Der Beschnitt. Die Seiten haben eine feste Hoehe und overflow:hidden. Was nicht
draufpasst, wird abgeschnitten - lautlos. Die Seitenzahl bleibt dabei richtig,
weil kein Umbruch entsteht; deshalb kann eine Seitenzahlpruefung das nicht
finden. In einem Datenblatt mit 25 zusaetzlichen Tabellenzeilen verschwanden so
22 davon, ohne Fehler und ohne Warnung.

Gemeinsam genutzt von build_pages.py (Broschuere) und build_tds.py (Datenblatt).
"""

from __future__ import annotations

import re

# Schriften, die im PDF stehen duerfen. Alles andere ist eine stille Ersetzung.
# BKM-PDF-Sans ist die Druckfamilie aus design-system/base.css: im Druckmodus
# wird Liberation Sans eingebettet, weil die vorliegenden TT-Norms-Pro-Dateien
# Trial-Fassungen sind und in externen Druckpfaden einen Hinweis ausgeben.
ALLOWED_FONTS = ("Unbounded", "TT-Norms-Pro", "TTNormsPro", "Liberation",
                 "BKM-PDF-Sans")

# Schluessel, deren Werte Pfade sind und nicht als Text im PDF stehen.
PATH_KEYS = ("image", "product_image", "badge", "line_badge", "logo", "keyvisual")

# Zusaetzlich im Datenblatt: der Dokumenttitel steht im <title> und damit nicht
# im sichtbaren Text, und die Produktlinie wird als Badge-Grafik gesetzt - beide
# fehlen zu Recht im PDF-Text.
TDS_SKIP_KEYS = PATH_KEYS + ("title", "product_line")


def letters(text: str) -> str:
    """Reduziert auf Buchstaben und Ziffern.

    Der Blocksatz bricht Woerter um und setzt Trennstriche; im extrahierten
    Text stehen dadurch Leerzeichen und Bindestriche an Stellen, die es in
    der Quelle nicht gibt. Ohne sie ist der Vergleich stabil.

    ß wird zu ss. Deutscher Versalsatz loest das ß auf: aus "Bohrlöcher
    verschließen" wird ueber text-transform:uppercase ein "BOHRLÖCHER
    VERSCHLIESSEN", und im PDF steht das doppelte s. Ohne diese Zeile
    meldet die Vollstaendigkeitspruefung heil gesetzte Ueberschriften als
    fehlenden Text - aufgefallen an den Abschnittstiteln der
    Verarbeitungsanleitung.
    """
    return re.sub(r"[^0-9a-zäöü]", "", text.lower().replace("ß", "ss"))


def collect_strings(node, out=None, *, min_length=40, skip_keys=PATH_KEYS):
    """Sammelt Textwerte aus der Content-Struktur ein.

    min_length steuert, ab welcher Laenge ein Text verglichen wird. Die
    Broschuere setzt sie hoch: ihr Fliesstext ist lang, kurze Felder wie
    Ueberschriften vergleichen sich nach dem Umbruch nicht verlaesslich. Das
    Datenblatt setzt sie niedrig, weil sein Inhalt gerade in kurzen
    Tabellenzeilen steckt - genau die, die beim Beschnitt verschwinden.
    """
    if out is None:
        out = []
    if isinstance(node, str):
        if len(node.strip()) >= min_length:
            out.append(node)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in skip_keys:
                continue
            collect_strings(value, out, min_length=min_length, skip_keys=skip_keys)
    elif isinstance(node, list):
        for item in node:
            collect_strings(item, out, min_length=min_length, skip_keys=skip_keys)
    return out


def check_fonts(reader) -> list[str]:
    """Meldet Schriften im PDF, die nicht zu den Markenschriften gehoeren."""
    errors = []
    fonts = set()
    for page in reader.pages:
        resources = page.get("/Resources", {}) or {}
        for value in (resources.get("/Font", {}) or {}).values():
            base = str(value.get_object().get("/BaseFont", ""))
            fonts.add(base.split("+")[-1].lstrip("/"))
    for font in sorted(fonts):
        if not any(font.startswith(prefix) for prefix in ALLOWED_FONTS):
            errors.append(
                f"Fremdschrift im PDF: {font} - eine Schriftdatei wurde nicht "
                f"gefunden und still ersetzt"
            )
    return errors


def check_completeness(reader, strings) -> list[str]:
    """Meldet Texte aus dem Inhalt, die im PDF fehlen.

    Verglichen wird gegen das ganze Dokument, nicht Seite gegen Seite: wo ein
    Text steht, entscheidet die Vorlage.
    """
    rendered = letters(" ".join(page.extract_text() or "" for page in reader.pages))
    errors = []
    for text in strings:
        if letters(text) and letters(text) not in rendered:
            errors.append(
                f"Text aus dem Inhalt steht nicht im PDF: ...{text.strip()[-60:]!r}"
            )
    return errors
