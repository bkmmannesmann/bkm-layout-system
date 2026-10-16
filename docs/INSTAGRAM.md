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
| `kennzahl` | `zahlen: [{zahl, einheit?, text?}]` — eine bis drei große Zahlen, Größe nach Anzahl | — (16.10.2026) |
| `skizze` | `art`: `bohrbild` oder `schnitt45`, dazu Maße als Text — technische Zeichnung, siehe unten | — (16.10.2026) |

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
unten rechts im Maßband-Streifen, links neben dem Pfeil** — klein, an derselben Stelle auf
jeder Folie, nie auf einem Foto. So ist es beim ersten Blick sichtbar (EU-KI-Verordnung,
Art. 50 Abs. 4), ohne ins Bild oder in den Kopf zu greifen.

| | |
|:---|:---|
| Label | `assets/kennzeichnung/bkm-ai-generated-lime.svg` (Lime-Pille) und `-deep.svg` (Deep-Green-Pille) |
| Lage | `right:158px; top:1297px` — mittig in der unteren Zeile des Maßbands |
| Größe | 20 px hoch, deutlich kleiner als das Logo |
| Wahl | im Maßband immer Lime; auf Covers ohne Maßband nach dem Grund dort (hell → Deep Green) |
| Abschalten | `"ki": false` in der `content.json` — nur für Posts nachweislich ohne KI-Inhalt |

**Zusätzlich beim Posten** in Instagram unter *Erweiterte Einstellungen* die KI-Kennzeichnung
einschalten. Der Export schreibt die PNGs neu; Metadaten, an denen Meta KI-Bilder automatisch
erkennt, gehen dabei verloren. Die Plattformkennzeichnung ersetzt das Label nicht: die Pflicht
liegt bei dem, der veröffentlicht.

Die Gegenprobe läuft ohne Label: verglichen wird die Vorlage mit dem Design.

## Gestaltungsregeln über die Referenz hinaus

Entscheidungen, die nach der Referenz getroffen wurden. Die Gegenprobe nimmt die betroffenen
Bereiche aus (`ABWEICHUNGEN` in `scripts/build_instagram.py`).

1. **Kein Logo und kein Zähler in einem weißen Kasten.** Auf einem Foto stehen das weiß-grüne
   Logo und der Zähler in Weiß; lesbar macht sie ein Deep-Green-Verlauf über dem oberen
   Bildrand, wie bei den Vollbild-Folien. (15.10.2026, Cover hell / 4c-01)
2. **Nichts liegt auf Gesichtern.** Kennzeichnungen, Labels und Bedienelemente gehören in die
   Rahmenzonen — Kopf, Maßband —, nicht ins Motiv.
3. **Neue Blöcke statt Einzellösungen.** Fehlt für ein Thema eine Form, entsteht ein neuer
   Blocktyp im bestehenden Rahmen (Fläche, Schrift, Akzentfarbe, Maßband unverändert), wird als
   Testbild abgenommen und erst danach hier und in der Vorlage ergänzt. Die Gegenprobe muss
   weiter bestehen — neue Blöcke kommen in der Referenz nicht vor und verändern sie nicht.
   `kennzahl` und `skizze` sind so entstanden. (16.10.2026)

### Skizzen

Vektorzeichnung, 864 × 440 px; Strich, Wandfläche und Akzent folgen der Folienfläche. Die
Maße stehen als Text im Inhalt und werden **wörtlich aus der Quelle** übernommen — die Zeichnung
zeigt das Prinzip, sie ist nicht maßstäblich und ersetzt nicht die Verarbeitungsanleitung.
`unterschrift` setzt eine graue Zeile darunter.

| `art` | Felder |
|:---|:---|
| `bohrbild` | `reihen: [{hoehe, versetzt?}]` (Höhe in cm über Boden; erste Reihe Ecke, 10, 30 … cm, versetzte Reihe 20, 40 … cm), `masse: {ecke, raster, boden, reihe?, versatz?}` |
| `schnitt45` | `wand_cm`, `tiefe_cm`, `masse: {wand, tiefe, bohrlaenge, winkel, drittel}` — Wandschnitt mit 45°-Bohrung und Injektionsflasche |

```json
{"typ": "skizze", "art": "bohrbild", "reihen": [{"hoehe": 10}, {"hoehe": 23.5, "versetzt": true}],
 "masse": {"ecke": "10 cm", "raster": "20 cm", "boden": "5–15 cm", "reihe": "12–15 cm", "versatz": "mittig versetzt"},
 "unterschrift": "Bohrlochmuster Horizontalsperre · über 50 cm Wandstärke"}
```

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
