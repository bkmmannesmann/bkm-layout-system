# Instagram-Karussells

Gilt **nur für Instagram**. Broschüre, Datenblatt und Anleitung haben eigene Regeln und greifen
nicht auf diese Vorlage zu, und umgekehrt.

| | |
|:---|:---|
| Format | 1080 × 1350 px (4:5), PNG verlustfrei, RGB, sRGB |
| Folien | 7 bis 10 je Post |
| Referenz | `templates/instagram/referenz/` — Claude Design, Runde 4 · Version 2 |
| Vorlage | `templates/instagram/karussell.html.j2` + `templates/instagram/dateien/` |
| Inhalt | `content/instagram/<post>/content.json` |
| Plan | `content/instagram/plan.csv` |
| Ausgabe | `output/instagram/<post>/` (nicht im Git; auf GitHub als Artefakt) |

## Wie es zusammenhängt

```
Referenz (Claude Design)  →  Folientypen und Blöcke  →  content.json je Post  →  PNG
   wird nicht gepostet         karussell.html.j2          aus dem Content-Plan     Chromium
```

Die **Referenz** ist das freigegebene Design. Aus ihr ist die Vorlage abgeleitet; die
Inline-Styles stehen dort wörtlich. Die **Gegenprobe** baut die drei Referenz-Karussells aus
`content.json` nach und vergleicht sie pixelweise mit dem Export — so fällt jede Abweichung
der Vorlage vom Design auf:

```bash
python3 scripts/build_instagram.py --gegenprobe
```

Ändert sich das Design, entsteht in Claude Design eine neue Runde. Sie ersetzt
`templates/instagram/referenz/`, danach wird die Vorlage nachgezogen, bis die Gegenprobe wieder
besteht. Die Vorlage wird nicht ohne neue Referenz verändert.

## Content-Plan

`content/instagram/plan.csv`, Semikolon-getrennt, öffnet sich in Excel und Google Sheets.

| Spalte | Inhalt |
|:---|:---|
| `nr` | `IG-001` … — steht auch als `"plan"` in der `content.json` |
| `termin` | geplantes Veröffentlichungsdatum, `2026-11-03` |
| `ordner` | Ordnername unter `content/instagram/`, ab Status `entwurf` Pflicht |
| `thema` | worum es geht, ein Satz |
| `zielgruppe` | Selbermacher, Machen lassen, Fachbetriebe, alle … |
| `status` | `idee` → `entwurf` → `freigegeben` → `gepostet` |
| `notiz` | Quelle, Rückfragen, Freigabe durch wen |

Abgearbeitet wird von oben: die nächste Zeile mit `idee` bekommt einen Ordner und eine
`content.json` und geht auf `entwurf`. Freigegeben wird erst, wenn kein Marker mehr offen ist.

```bash
python3 scripts/build_instagram.py --plan
```

meldet für jede Zeile, ob der Post existiert, gültig ist, die richtige Nummer trägt und noch
`[ANGABE FEHLT: …]` oder `[ZU PRÜFEN: …]` enthält. Ein Post ohne Planzeile ist ein Fehler.

## Ein Post: `content.json`

```json
{
  "titel": "Zwei Wege · Der DIY-Weg",
  "plan": "IG-001",
  "caption": "Text unter dem Post",
  "hashtags": ["feuchterkeller", "bautenschutz"],
  "folien": [ { … }, { … } ]
}
```

Vollständige Beispiele: die drei Referenzposts `content/instagram/wege-*/`.

### Auszeichnung im Text

| Schreibweise | Ergebnis |
|:---|:---|
| `*Wort*` | Akzentfarbe — Lime auf dunkler, Transition Green auf heller Fläche |
| `**Wort**` | fett |
| `***Wort***` | fett in Akzentfarbe |

Farbwerte gibt es im Inhalt nicht. Eine Folie ist `"flaeche": "dunkel"` oder `"hell"`, daraus
folgen Grund, Logo, Schrift- und Akzentfarbe. Felder auf `_bg`, `_color`, `farbe` oder ein
Hex-Wert im Text weist die Prüfung ab.

### Rahmen einer Folie

Kopf (Logo, `03 / 07`), ab Folie 2 das Maßband mit Kapitel und „Du bist hier“-Marke, auf der
letzten Folie das Maßband ohne Marke. Das setzt die Vorlage selbst.

| Feld | Werte | Vorgabe |
|:---|:---|:---|
| `typ` | `standard`, `cover-hell`, `cover-wege`, `wege-vergleich`, `schluss-wege` | `standard` |
| `flaeche` | `dunkel`, `hell` | `dunkel` |
| `kapitel` | Wort im Maßband, ab Folie 2 Pflicht (außer letzte) | — |
| `textur` | `deep-1` … `deep-3`, `hell-1` … `hell-3` | dunkel rotierend, hell `hell-2` |
| `ausrichtung` | `oben`, `mitte`, `unten` | `mitte` |
| `abstand` | px zwischen den Blöcken | 44 |
| `hintergrund.foto_box` | `{bild, oben, hoehe, fokus}` — Foto im oberen Teil (Cover, Ergebnis) | — |
| `hintergrund.foto_flaeche` | `{bild, fokus, verlauf}` — Vollbild mit Abdunklung `leicht`/`mittel`/`kraeftig` | — |
| `chevrons` | `true` — Pfeilgrafik rechts (Schlussfolie) | `false` |
| `cta` | Text des Lime-Buttons auf der letzten Folie | — |
| `ziel` | Text der Lime-Pille unten (Zwei-Wege-Folien) | — |

Dunkle Schlussfolie ohne `textur` steht auf glattem Deep Green, wie in der Referenz.

### Blöcke (`bloecke`, in Lesereihenfolge)

| `typ` | Felder | Referenz |
|:---|:---|:---|
| `rubrik` | `text`, `akzent` (Lime statt grau, nur dunkel) — auf hell automatisch als Pille | alle |
| `headline` | `text`, `groesse` (64), `versal`, `max_breite`, `zeilenhoehe`, `produkt` (Bild rechts daneben) | alle |
| `text` | `text`, `groesse` (30), `max_breite` (820) | alle |
| `punkte` | `punkte: [{titel, text?}]`, `icon`: `check`/`warnung`, `abstand` (26) | 4a-02, 4a-05 |
| `zeilen` | `punkte: ["…"]` — Häkchenzeilen mit Trennlinien | 4c-04 |
| `schritte` | `schritte: [{titel, text?}]` — nummeriert 01, 02 … | 4a-04, 4c-03 |
| `karten` | `karten: [{icon, titel, zeilen: [], bild?}]` — zwei Glaskarten | 4a-03 |
| `ursachen` | `zeilen: [{bild, zeichen, ursache, fokus?}]` — Anzeichen → Ursache | 4b-04 |
| `hinweis` | `text` — dunkle Box mit Info-Icon | 4b-03 |
| `gegenueber` | `links/rechts: {titel, punkte: []}` — warten vs. handeln | 4b-06 |
| `vorteile` | `vorteile: [{icon | portrait, titel, text?}]` | 4c-05 |
| `bild` | `bild`, `hoehe` (460), `fokus` — Foto im Textfluss | 4c-06 |
| `badge` | — Home-Line-Plakette | 4a-07 |

Icons: `check`, `check-circle`, `warning`, `clock`, `package`, `certificate`, `clipboard-text`,
`info`, `arrow-right`, `arrow-left` (Phosphor, aus der Referenz).

### Sondertypen

| `typ` | Zweck | Felder | Referenz |
|:---|:---|:---|:---|
| `cover-hell` | Cover mit Foto oben, Chevrons | `foto: {bild, fokus}` + Blöcke | 4c-01 |
| `cover-wege` | Cover der Zwei-Wege-Serie | `foto`, `ziel`, `links`, `rechts`, `textur_links/rechts` + Blöcke | 4b-01 |
| `wege-vergleich` | zwei Wege nebeneinander | `links/rechts: {rubrik, portrait, titel, punkte, fazit}` | 4b-05 |
| `schluss-wege` | Schluss der Zwei-Wege-Serie | `foto`, `ziel`, `links/rechts: {titel, text}` + Blöcke | 4b-07 |

### Bilder

Ein Dateiname ohne Pfad liegt in `templates/instagram/dateien/`; alles andere relativ zur
Repo-Wurzel, z. B. `uploads/feuchte-waende-selbst-sanieren.webp`. Fehlt eine Datei, bricht die
Prüfung ab. Motive mit dem Vermerk „AI GENERATED“ behalten ihn sichtbar (AGENTS.md, Regel 7) —
mit `fokus` so verschieben, dass er im Bild bleibt.

## KI-Kennzeichnung

Ein Karussell gilt als Ganzes als KI-erzeugt. **Jede Folie trägt das Label „AI GENERATED“
im Kopf, links neben dem Zähler** — fester Teil des Designs wie Logo und Seitenzahl, nicht
auf einem Foto. So ist es auf jeder Folie beim ersten Blick sichtbar (EU-KI-Verordnung,
Art. 50 Abs. 4), egal wie groß ein Bild steht oder wo es beschnitten wird.

| | |
|:---|:---|
| Label | `assets/kennzeichnung/bkm-ai-generated-lime.svg` (Lime-Pille) und `-deep.svg` (Deep-Green-Pille) |
| Wahl | dunkle Folie → Lime-Pille, helle Folie → Deep-Green-Pille; beim hellen Cover mit Foto im Kasten des Zählers |
| Größe | 28 px hoch, Abstand 20 px zum Zähler |
| Abschalten | `"ki": false` in der `content.json` — nur für Posts nachweislich ohne KI-Inhalt |

**Zusätzlich beim Posten** in Instagram unter *Erweiterte Einstellungen* die KI-Kennzeichnung
einschalten. Der Export schreibt die PNGs neu; Metadaten, an denen Meta KI-Bilder automatisch
erkennt, gehen dabei verloren. Die Plattformkennzeichnung ersetzt das Label nicht: die Pflicht
liegt bei dem, der veröffentlicht.

Die Gegenprobe läuft ohne Label: verglichen wird die Vorlage mit dem Design.

## Bauen

**Auf GitHub:** Jeder Push unter `content/instagram/` startet die Action *Instagram* und baut
die geänderten Posts; ändert sich die Vorlage, alle Posts plus Gegenprobe. Die PNGs liegen im
Lauf unten unter **Artifacts → instagram-png**, zusammen mit der Caption als Textdatei.

**Lokal:**

```bash
pip install -r requirements.txt && playwright install chromium   # einmalig
python3 scripts/build_instagram.py content/instagram/<post>/
python3 scripts/build_instagram.py --alle
```

## Was geprüft wird

| Prüfung | Folge |
|:---|:---|
| unbekannter Folientyp, Block, Icon, Textur, Verlauf; Farbwert im Inhalt; Bild fehlt | Fehler vor dem Bau |
| Folienzahl außerhalb 7–10 | Fehler |
| Text ragt unter den Satzspiegel (ins Maßband) oder über den rechten Rand | Fehler mit Folie und Pixelzahl |
| eine Datei, Schrift oder ein Bild lädt nicht | Fehler — Chromium ersetzt sonst still |
| Folie nicht 4:5 | Fehler, Folie wird nicht gespeichert |
| Vorlage weicht von der Referenz ab (`--gegenprobe`) | Fehler |
| offene Marker in einem freigegebenen Post (`--plan`) | Fehler |

Bei Fehlern entstehen die PNGs trotzdem zum Ansehen; der Lauf endet mit Exit-Code 1.

## Direktexport ohne Content-Plan

Ein fertiges Karussell als HTML aus Claude Design lässt sich auch unmittelbar rendern — für
Einzelstücke, die nicht in den Plan gehören. **Project archive** wählen; Standalone HTML geht
auch, ist aber größer. Ablage `incoming/instagram/`.

```bash
python3 scripts/build_instagram.py ~/Downloads/<projekt>.zip --slug <name>
python3 scripts/build_instagram.py <export>.html --slug <name>
```
