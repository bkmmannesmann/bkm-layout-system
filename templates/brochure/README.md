# BKM Broschüren-Templates

A4-Vorlagen für Imagebroschüren, Produktlinien- und Katalogbroschüren,
Fachbetriebsprospekte und Verarbeitungsanleitungen.
30 Vorlagen in acht Gruppen. Jede Datei öffnet direkt im Browser.

Verbindlich ist `docs/BROSCHUERE-CONTRACT.md` — Maße, Typografie, Farben,
Icon- und Texturregeln sowie die begründeten Abweichungen zum TDS-Vertrag.

## Ablage im Repo

```
templates/brochure/            9 .dc.html + support.js
docs/BROSCHUERE-CONTRACT.md    Layoutvertrag
assets/                        Logos, Keyvisual, Icons, Schriften
uploads/                       Hero-Grafiken, Fotos, Texturen
```

## Einstieg

`Bibliothek.dc.html` öffnen — der Index listet alle 30 Vorlagen nach Gruppe und
verlinkt sie.

| Datei | Gruppe | Vorlagen |
|:---|:---|:---|
| `A-Titelblaetter.dc.html` | Titelblätter | 6 |
| `B-Rahmenseiten.dc.html` | Rahmenseiten | 7 |
| `C-Navigation.dc.html` | Navigation | 3 |
| `D-Textstrecken.dc.html` | Textstrecken | 4 |
| `E-Strecken.dc.html` | Komplette Strecken | 3 |
| `F-Verfahren.dc.html` | Verfahren | 2 |
| `G-Produktseiten.dc.html` | Produktseiten | 3 |
| `H-Fachbetrieb.dc.html` | Fachbetrieb | 2 |

## Eine Broschüre bauen

1. Titelblatt aus Gruppe A wählen — je Absender eine Variante
   (AG, Fachbetrieb, Home Line, Pro Line, Verarbeitungsanleitung)
2. Rahmenseiten aus B ergänzen: U2 mit Impressum, Einstieg, Glossar, U3/U4
3. Navigation aus C, wenn die Broschüre mehr als zwölf Seiten hat
4. Inhalt aus D, F, G oder H, je nach Thema
5. Farbwelt setzen: AG in Deep Green, Fachbetriebsprospekte in Transition Green

Gruppe E zeigt drei fertige Strecken als Referenz für Rhythmus und Bildanteil.

## Abgrenzung zum TDS

Technische Datenblätter entstehen über `scripts/build_tds.py` aus
`content/<ordner>/content.json` und folgen `docs/LAYOUT-CONTRACT.md`.
Broschüren sind ein eigener Dokumenttyp mit eigenem Vertrag — sie werden nicht
über die TDS-Pipeline gebaut und teilen mit ihr nur Achse, Farbwerte, Haarlinie
und die Phosphor-Bold-Icons.

Drei Werte weichen bewusst ab: Radius 5 px statt 3 px, Keyvisual 42 mm statt
10 % der Blattbreite, offenes Icon-Set statt der neun festen Dateien.
Begründung im Vertrag, Abschnitt „Verhältnis zum TDS-Vertrag".

## Korrekturen an cover-spec.css

Drei Werte in `templates/cover/cover-spec.css` v2.0 und `cover-layout.json`
sind zu korrigieren — eigener Pull Request, weil sie die bestehenden Cover ändern:

| Wert | Ist | Soll |
|:---|:---|:---|
| Keyvisual `y_top_mm` | `102,3` | `102,416` |
| Farbkasten Höhe | `118,1 mm` | `118,125 mm` |
| Eckerweiterung | `8 × 8 mm` bei `118,125 mm` | `10 × 10 mm` bei `117,6 mm` |

Die JSON nennt zusätzlich `−0,025 em` Laufweite auf Headline und Subheadline,
das CSS nennt `0`. Maßgeblich ist das CSS.

## Offen

- Echte Shop-Kategorie-Icons fehlen; `C-Navigation.dc.html` nutzt Phosphor-Platzhalter
- Preise für Mehrfach-Gebinde in `G-Produktseiten.dc.html` stehen als „auf Anfrage"
- Haftungstext in `rahmen-glossar` rechtlich prüfen lassen
