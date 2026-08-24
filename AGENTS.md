# Arbeiten an diesem Repository

Gilt für alle Beitragenden, **einschließlich KI-Assistenten** (Claude, Manus, Codex und andere),
unabhängig vom Account. Bitte vor der ersten Änderung vollständig lesen.

## Die drei verbindlichen Dokumente

| Datei | Regelt |
|:---|:---|
| `docs/LAYOUT-CONTRACT.md` | Maße, Typografie, Farben, Icons, Metadaten. Maschinell geprüft. |
| `docs/REDAKTIONSSTANDARD.md` | Inhalt, Blockreihenfolge, Sprache, Pflichtkennwerte, Marker, Freigabe. |
| `docs/TDS-WORKFLOW.md` | Ablauf von der Quellinformation bis zum Release-Build. |
| `docs/BROSCHUERE-LAYOUT.md` | Dasselbe für den Broschüren-Innenteil: Raster, Typografie, Farben, Flächen, Seitentypen. Maschinell geprüft. |

Bei Widerspruch zwischen Code und diesen Dokumenten gewinnen die Dokumente. Wer eine Regel ändern
will, ändert **erst** das Dokument, im selben Pull Request wie den Code.

## Feste Regeln, die häufig verletzt wurden

1. **Erstelldatum, keine Revision.** Das Datum im Kopf ist `created_date` und immer der Tag, an
   dem die Datei erzeugt wird — nie das „Ausgegeben am" eines alten Quellblatts. Die Felder
   `revision` und `issue_date` existieren nicht; der Validator weist sie ab.
2. **Produktlinie ohne Rückfrage.** Produkte mit dem Namensbestandteil **Novu** gehören zur
   **Home Line** (`badge-homeline.png`), alle übrigen zur **Pro Line**.
3. **Seitenzählung** nur über veröffentlichte Seiten. `page_count` ist die tatsächliche Zahl —
   drei im Regelfall, bei umfangreichen Produkten mehr. Der interne Prüfteil trägt keine Nummer
   und darf über mehrere Seiten laufen.
4. **Grundschrift 12 px auf allen Seiten.** Kein seitenbezogenes Verkleinern, um Inhalt
   unterzubringen.
5. **Icons: Phosphor Bold, lokale SVGs, sonst nichts.** `.tds-icon svg` nutzt `fill`, nicht
   `stroke`. Keine Icon-Webfont, kein CDN, keine `class="ph …"`-Klassen und **keine andere
   Strichstärke als Bold** — Regular verschwindet in der 20-px-Kachel. Neues Icon: auf
   phosphoricons.com Weight **Bold**, `width`/`height` entfernen, nach `templates/tds/icons/`,
   dann `python3 scripts/validate_layout.py`. Die Zuordnung Block → Icon ist fest und steht in
   `docs/LAYOUT-CONTRACT.md`; die Dateien sind nach dem Block benannt (`vorteile.svg`,
   `eigenschaften.svg`, `daten.svg` …), werden nicht produktbezogen umbelegt und über einen
   Geometrie-Hash gegen das Manifest im Prüfskript verglichen. Jede Datei trägt
   `style="fill:#b4e717"` am `svg`-Element — WeasyPrint stylt SVG-Kinder nicht über das
   Dokument-Stylesheet, ohne Inline-Füllung druckt der Glyph schwarz. Im Verzeichnis liegen genau
   diese neun Dateien.
6. **Fixbausteine sind unveränderlich.** Rechtliche Hinweise, Entsorgung und Schluss-Hinweis
   werden wörtlich übernommen — auch nicht in die Du-Form umgeschrieben.
7. **Kennzeichnung KI-generierter Produktbilder nicht entfernen.** Trägt ein Produktbild den
   Vermerk „AI GENERATED", bleibt er sichtbar im Bild — Vorgabe nach EU-KI-Verordnung. Nicht
   wegretuschieren, nicht beschneiden, nicht überdecken.
8. **Inhalt wird übernommen, nicht umformuliert.** Der Wortlaut der angelieferten Vorlage bleibt
   stehen. Was kritisch, unbelegt oder widersprüchlich ist, wird mit `[ANGABE FEHLT: …]` oder
   `[ZU PRÜFEN: …]` markiert und im `review`-Block erklärt — nicht besser geschrieben. Die
   einzige Ausnahme sind die juristischen Fixbausteine, die umgekehrt **nie** angepasst werden.
9. **Bedingungszeilen nur aus der Quelle.** Die kleine graue Zeile unter einem Parameternamen ist
   nur zulässig, wenn die Bedingung wörtlich in der Vorlage steht. Nie zur fachlichen Ergänzung
   hinzufügen — stattdessen markieren.
10. **Layoutänderungen gelten für alle Blätter**, nicht nur für das gerade offene.
11. **Gespeicherte TDS-PDFs bleiben vollständig von TT Norms Pro entkoppelt.** Im Druckmodus setzt `design-system/base.css` den gesamten Fließtext auf die lokal eingebettete Familie `BKM PDF Sans` (Liberation Sans), weil externe PDF-Viewer und Druckertreiber die derzeitigen TT-Norms-Glyphen auch nach dem Speichern fehlerhaft ersetzen können. Diese Regel erst nach reproduzierbar fehlerfreiem Speichern und anschließendem Drucken mit geprüften Vollversionen entfernen.

## Ablauf für eine Änderung

```bash
python3 scripts/validate_layout.py
python3 scripts/validate_tds.py content/<ordner>/content.json
python3 scripts/build_tds.py --content content/<ordner>/content.json
```

Die PDF danach ansehen: Icons sichtbar, Schriftgröße auf allen Seiten gleich, Erstelldatum im
Kopf, Fußzeile ohne Datum, Prüfteil ohne Seitenzahl sowie Ä/Ö/Ü/ä/ö/ü/ß/ẞ lesbar.

Für einen Release zusätzlich das freigestellte Produkt-PNG unter
`assets/images/products/<slug>.png` ablegen. Die Markenschriften liegen im Repository.

## Was ohne Rückfrage nicht geändert wird

`templates/tds/`, `templates/pages/`, `design-system/`, `components/`, die vier Regeldokumente
und `scripts/validate_*.py`. Das sind Systemdateien. Inhaltliche Arbeit findet in
`content/<ordner>/content.json` statt.

## Broschüren

Für den Innenteil gilt `docs/BROSCHUERE-LAYOUT.md` mit denselben Grundsätzen wie beim
Datenblatt. Zwei davon werden erfahrungsgemäß verletzt:

1. **Keine Farbwerte im Inhalt.** Eine `content.json` wählt eine der sechs benannten Flächen
   (`deep`, `transition`, `pure`, `stone`, `sand`, `white`). Der Name legt Grundton, Textfarbe,
   Headline- und Akzentfarbe gemeinsam fest. Felder auf `_bg` oder `_color` weist der Validator ab.
2. **Fehlende Schriftdateien fallen nicht auf.** Verweist ein Stylesheet auf eine Datei, die es
   nicht gibt, meldet WeasyPrint das nicht, sondern setzt still eine Ersatzschrift. Genau so lief
   der Innenteil zeitweise vollständig in DejaVu Sans. `validate_brochure.py` prüft die Pfade,
   `build_pages.py` liest die eingebetteten Schriften des fertigen PDFs.

```bash
python3 scripts/validate_brochure.py
python3 scripts/validate_brochure.py content/<ordner>/content.json
python3 scripts/build_pages.py <ordner>
```
