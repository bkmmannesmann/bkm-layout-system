# Broschüren-Canvas

**Zuständigkeit:** Dieses Dokument regelt die **Design- und Abstimmungsebene** —
die 30 Seitentypen in `templates/brochure/`, aus denen Layouts ausgewählt und
freigegeben werden. Die **Produktionsebene** regelt
[`BROSCHUERE-LAYOUT.md`](BROSCHUERE-LAYOUT.md): dort entstehen aus
`content/*/content.json` über Jinja und WeasyPrint die druckfertigen PDFs.

Ein Layout wandert erst in die Pipeline, wenn es hier freigegeben ist. Beide
Dokumente stehen nebeneinander; keines gewinnt über das andere. Wo ihre Maße
auseinanderlaufen, steht das unter „Maßdifferenz zur Pipeline".

Gilt für A4-Broschüren: Imagebroschüren der BKM MANNESMANN AG, Produktlinien- und
Katalogbroschüren, Fachbetriebsprospekte und Verarbeitungsanleitungen.

Dieser Vertrag steht **neben** `LAYOUT-CONTRACT.md`, nicht darüber. Der TDS-Vertrag
regelt technische Datenblätter, die aus der Technik heraus über
`scripts/build_tds.py` erzeugt werden. Broschüren sind ein eigener Dokumenttyp mit
eigener Aufgabe: nicht Kennwerte auf drei Seiten, sondern Argumentation, Bildführung
und Navigation über zwanzig und mehr Seiten.

> **Die Zahlen in diesem Dokument stehen verbindlich in [`brand.json`](../brand.json).**
> Was hier steht, ist die Begründung dazu — warum ein Wert so ist und was passiert,
> wenn man ihn ändert. Bei Abweichung gewinnt `brand.json`.
> `scripts/check_brand_drift.py` prüft den Bestand dagegen.

## Dateien

30 Vorlagen in acht Gruppen, je eine Datei pro Gruppe. Jede öffnet direkt im Browser.

| Datei | Gruppe | Vorlagen |
|:---|:---|:---|
| `Bibliothek.dc.html` | Index | Übersicht, verlinkt alle Gruppen |
| `A-Titelblaetter.dc.html` | Titelblätter | 6 |
| `B-Rahmenseiten.dc.html` | Rahmenseiten | 7 |
| `C-Navigation.dc.html` | Navigation | 3 |
| `D-Textstrecken.dc.html` | Textstrecken | 4 |
| `E-Strecken.dc.html` | Komplette Strecken | 3 |
| `F-Verfahren.dc.html` | Verfahren | 2 |
| `G-Produktseiten.dc.html` | Produktseiten | 3 |
| `H-Fachbetrieb.dc.html` | Fachbetrieb | 2 |

## Maße und Raster

| Invariante | Wert | Grund |
|:---|:---|:---|
| Seitenformat | `210 × 297 mm` | A4, doppelseitig gesetzt |
| Achse außen und innen | `18 mm` | Wie TDS: die eine Fluchtlinie |
| Kopfsteg Innenseiten | `26,7 mm` | — |
| Kopfsteg Titelblatt mit Logo | `18 mm` | Das Logo steht auf der Achse, der Kopfsteg entspricht ihr. |
| Kopfsteg Titelblatt mit Siegel | `12 mm` | Das runde Siegel ersetzt das Logo und braucht mehr Luft nach unten, deshalb steht es höher. |
| Fußsteg | `23,5 mm` | Innenseiten |
| Textbreite | `174 mm` | 210 − 2 × 18 |
| Dreispaltig | `55 mm` Spalte, `4,6 mm` Steg | Fließtextseiten |
| Marginalspalte | `38 mm`, Steg `6 mm` | Textstrecken, Verfahren, Produktseiten |
| Radius | `5 px` | Abweichung, siehe unten |
| Haarlinie | `#e3e1dc` | Wie TDS |

## Titelblatt

| Element | Wert |
|:---|:---|
| Hero-Grafik | `210 × 125 mm` — 118,125 mm für den 16:9-Teil, darunter 6,875 mm Eckerweiterung unten rechts |
| Keyvisual | `42 mm` breit, rechts angeschnitten, `top: 102,416 mm`, dreifarbig |
| Foto | ab `117,46 mm` bis Seitenunterkante, `210 × 179,54 mm`, `object-fit: cover` |
| Logo | `42 mm`, Kopfsteg `18 mm` |
| Siegel (Fachbetriebs-Titel) | `28,16 mm` rund, Kopfsteg `12 mm`, ersetzt das Logo |
| Headline | Unbounded 900, `30 pt`, Zeilenhöhe `1,25`, Laufweite `0` |
| Subheadline | Unbounded 900, `12 pt`, Zeilenhöhe `1,3`, Laufweite `0` |
| Fließtext | TT Norms Pro 400, `12 pt`, Zeilenhöhe `1,25`, Laufweite `−0,015 em`, max. 2 Zeilen |

### Abstände optisch, nicht auf Kastenmaß

Alle drei Textblöcke tragen `text-box: trim-both cap alphabetic`. Die Werte gelten
von Versalhöhe zu Grundlinie, nicht von Kastenkante zu Kastenkante:

- Logo-Unterkante → Versalhöhe Headline: `18 mm`
- Headline-Grundlinie → Versalhöhe Subheadline: `7,87 mm` (95 px bei 300 dpi)
- Subheadline-Grundlinie → Versalhöhe Fließtext: `2,37 mm`

Grund: Ein Kastenabstand trägt den unsichtbaren Vorschub der Schrift mit. Ändert
jemand die Schriftgröße, verschiebt sich der sichtbare Abstand — die Zahl im Code
bedeutet dann nichts mehr. Optisch gemessen ist `18 mm` im Code `18 mm` auf dem Papier.

### Keyvisual-Position

`102,416 mm` ist kein gerundeter Wert. Die linke Oberkante des Pure-Green-Chevrons
liegt bei 73,33 von 464,8 SVG-Einheiten, bei 42 mm Breite also 15,709 mm unter der
Bildoberkante. Nur bei `102,416 mm` trifft sie die Unterkante des 16:9-Bereichs exakt.

### Blitzerschutz

Die Eckerweiterung ist `10 × 10 mm` bei `top: 117,6 mm` — sie ragt also 0,5 mm in
die Hero-Fläche hinein. Zusätzlich beginnt das Foto bei `117,46 mm`, überlappt die
Hero-Grafik damit um 7,54 mm. Zwei Überlappungen, weil an dieser Kante drei Ebenen
zusammentreffen.

Der TDS löst dasselbe Problem über `.tds-band` mit `margin-top: -10px`. Beide Wege
sind gültig; der Broschüren-Weg ist nötig, weil das Hero eine Grafikdatei ist und
kein CSS-Balken.

## Farbflächen

| Rolle | Hex |
|:---|:---|
| Deep Green | `#1c4b42` |
| Transition Green | `#287d4b` |
| Pure Green | `#4daf46` |
| Lime Green | `#b4e717` |
| Sand White | `#f6f5f2` |
| Stone Grey | `#494949` |
| Haarlinie | `#e3e1dc` |

Seitenflächen sind Clean White. **Sand White nur als Element, nie als Seitenfläche** —
im Druck wirkt eine vollflächige Sand-White-Seite schmutzig, am Bildschirm nicht.

**Fachbetriebsbroschüren, die an Endkunden des Betriebs gehen, ersetzen Deep Green
durch Transition Green.** Deep Green bleibt der AG vorbehalten.

**Lime ist im Fachbetrieb-Kontext zugelassen**, wo es sinnvoll ist — Entscheidung des
Markeninhabers vom 25.08.2026. Die Hauptfarbe der Fachbetriebe bleibt Transition Green.
Das weicht bewusst von `DESIGN.md` im Design-System ab, das Lime dort an fünf Stellen
ausschließt; eine Ausnahme kannte es bereits selbst. Die Abweichung gehört im
Design-System nachgezogen, sonst laufen die Repositories auseinander.

Maximal zwei Flächenfarben je Broschüre.

## Icons

Deep-Green-Kasten mit `5 px` Radius, Glyph in Lime Green. Auf dunklem Grund wird
der Kasten Transition Green, damit er sichtbar bleibt.

| Einsatz | Kasten | Glyph |
|:---|:---|:---|
| Kategorie-Opener | `12 mm` | `7,5 mm` |
| Im Text (Merksatz, Profi-Tipp, Linien) | `9,5 mm` | `6 mm` |
| Kontakt- und Impressumblöcke | `6,5 mm` | `3,8 mm` |

Quelle: Phosphor **Bold**, lokale SVGs, als CSS-Maske auf der Glyph-Fläche.
Keine Webfont, kein CDN.

**Abweichung zum TDS:** Dort steht der Glyph frei in einer 20-px-Kachel und trägt
seine Lime-Füllung inline, weil WeasyPrint das Dokument-Stylesheet nicht auf
SVG-Kinder anwendet. Broschüren rendern im Browser, nicht über WeasyPrint — dort
funktioniert die Maske. Die Neun-Dateien-Regel aus `templates/tds/icons/` gilt
für Broschüren nicht; sie brauchen ein größeres Set (Kategorien, Verfahren,
Partnerstufen).

## Texturen

`uploads/a4-texture-*.png`, je `2480 × 3508 px` — 210 × 297 mm bei 300 dpi.
Varianten in Deep Green, Transition Green, Pure Green und Weiß.

**Als `background` der Seite setzen, nicht als absolut positioniertes Bild.** Ein
absolut positioniertes Bild liegt über statisch positioniertem Inhalt, sobald die
Seite kein eigener Stacking Context ist — dann verschwinden Blöcke, die kein
`z-index` tragen.

Abschwächen über eine Farbebene, nicht über `opacity`:

```css
background: linear-gradient(rgba(255,255,255,.8), rgba(255,255,255,.8)),
            #fff url('…') center/cover no-repeat;
```

## Schrift

Unbounded 900 für Headlines, Versalien. TT Norms Pro 400/700 für Fließtext,
Auszeichnungen, Zahlen und Preise.

**Keine Monospace.** Auszeichnungszeilen mit Tracking laufen in TT Norms Pro Bold,
eine halbe Punktgröße größer als der Fließtext — Monospace trägt optisch mehr und
sah im Satz technisch statt redaktionell aus.

## Verhältnis zum TDS-Vertrag

Drei Werte weichen bewusst ab. Sie werden **nicht** angeglichen:

| Punkt | TDS | Broschüre | Grund |
|:---|:---|:---|:---|
| Radius | `3 px` | `5 px` | 3 px sind auf 20-px-Icon-Kacheln und dichte Datentabellen gerechnet. Bei 34-mm-Bildkästen und ganzseitigen Farbfeldern verschwindet der Radius optisch; 5 px sind die Entsprechung im größeren Maßstab. |
| Keyvisual | `10 %` der Blattbreite | `42 mm` = 20 % | Das Titelblatt setzt das Keyvisual als Bildelement, nicht als Randmarke. 42 mm entsprechen der Logobreite und damit einem Fünftel — dieselbe Proportion, in der Logo und Keyvisual zueinander stehen. |
| Icon-Set | genau 9 Dateien | offen | Broschüren decken Kategorien, Verfahren und Partnerstufen ab; ein festes Neuner-Set reicht nicht. |

Übernommen wurden: Achse `18 mm`, Farbwerte, Haarlinie `#e3e1dc`, Phosphor Bold als
lokale SVGs, Grundschriftgröße ohne seitenbezogene Verkleinerung.

## Zwei Druckwege

| Weg | Womit | Wofür |
|:---|:---|:---|
| **Canvas → Browser-PDF** | Vorlage im Browser öffnen, drucken | Abstimmung und Freigabe. Schnell, zeigt sofort das Layout. |
| **Pipeline → PDF/X** | `scripts/build_pages.py` über WeasyPrint | Druck. Eingebettete Markenschriften, Beschnittzugabe, Passermarken. |

Ein Browser-PDF geht **nicht** in die Druckerei. Ob die Markenschriften eingebettet
werden, hängt am Browser; Beschnittzugabe und Passermarken kann er nicht setzen. Bei
unseren Titelblättern laufen Hero-Grafik, Keyvisual und Foto randabfallend — ohne
Zugabe ist das nicht druckbar. Die Pipeline setzt dafür
`@page { bleed: 3mm; marks: crop cross; }`.

**Die CMYK-Konvertierung ist nachgelagert.** WeasyPrint schreibt RGB. Die Umwandlung
nach PDF/X-4 mit dem Farbprofil der Druckerei erfolgt danach — über Ghostscript oder
durch die Druckerei selbst. Ein PDF aus der Pipeline ist also noch **kein**
druckfertiges PDF/X, sondern die Vorstufe dazu.

## Icons für die Pipeline aufbereiten

Im Canvas liegen die Icons als **CSS-Maske** auf einer eingefärbten Fläche — die Datei
selbst braucht dort keine Füllung, nur ihre Form. Die Pipeline bettet dieselben Dateien
**inline** ein, und WeasyPrint wendet das Dokument-Stylesheet nicht auf die Kinder eines
inline eingebetteten SVG an. Ohne Füllung am `svg`-Element druckt der Glyph schwarz.

Jede Datei in `assets/icons/phosphor/bold/` trägt deshalb `style="fill:#b4e717"` am
`svg`-Element — dieselbe Regel, die `LAYOUT-CONTRACT.md` für die Datenblatt-Icons
aufstellt. Die Maske im Browser bleibt davon unberührt: sie wertet nur den Alphakanal aus.

```bash
python3 scripts/prepare_brochure_icons.py          # prüft und meldet
python3 scripts/prepare_brochure_icons.py --write  # schreibt die Füllung
```

Das Skript fasst `templates/tds/icons/` nicht an und prüft nach dem Schreiben, dass
dort nichts verändert wurde.

## Fotos: Kennzeichnung KI-generierter Bilder

Trägt ein Foto den Vermerk **„AI GENERATED"** — bei den gelieferten Motiven unten
rechts —, bleibt er **sichtbar im Bild**. Er ist nach EU-KI-Verordnung erforderlich.

Nicht wegretuschieren, nicht überdecken und **nicht beschneiden**. Das betrifft besonders
`object-fit: cover` auf einem Bildkasten, dessen Seitenverhältnis vom Motiv abweicht:
dort schneidet der Browser stillschweigend an den Rändern weg — und unten rechts liegt
genau der Vermerk. Wo ein Motiv mit Vermerk in einen abweichenden Kasten läuft, wird der
Kasten angepasst, nicht das Bild.

Dieselbe Regel gilt im Datenblatt für Produktbilder, siehe `AGENTS.md`, Punkt 7.

## Icons, die es doppelt gibt

Sechs der Broschüren-Icons sind motivgleich mit Icons aus dem TDS-Set. Sie liegen dort
unter dem **Blocknamen**, hier unter dem **Motivnamen**:

| Motiv | TDS | Canvas |
|:---|:---|:---|
| `atom` | `templates/tds/icons/eigenschaften.svg` | `assets/icons/phosphor/bold/atom.svg` |
| `package` | `templates/tds/icons/gebinde.svg` | `assets/icons/phosphor/bold/package.svg` |
| `scales` | `templates/tds/icons/recht.svg` | `assets/icons/phosphor/bold/scales.svg` |
| `seal-check` | `templates/tds/icons/vorteile.svg` | `assets/icons/phosphor/bold/seal-check.svg` |
| `table` | `templates/tds/icons/daten.svg` | `assets/icons/phosphor/bold/table.svg` |
| `warning` | `templates/tds/icons/hinweise.svg` | `assets/icons/phosphor/bold/warning.svg` |

`house` gehört **nicht** dazu: die Vorlagen referenzieren `house.svg`, das Datenblatt
nutzt `house-line` (`anwendung.svg`). Das sind zwei verschiedene Phosphor-Motive.

Das ist **kein Fehler**, sondern folgt aus zwei verschiedenen Benennungslogiken: Der
TDS-Vertrag benennt nach dem Inhaltsblock, damit kein Blatt versehentlich ein anderes
Symbol bekommt und die neun Dateien über einen Geometrie-Hash festgenagelt sind. Der
Canvas braucht ein offenes Set über Kategorien, Verfahren und Partnerstufen und benennt
deshalb nach dem Motiv.

Die Doppelung hat eine Folge, die bekannt sein muss: **Ein Motiv, das sich im zentralen
Design-System ändert, muss an zwei Stellen nachgezogen werden** — und im TDS-Fall
zusätzlich der Hash im `ICON_MANIFEST` von `scripts/validate_layout.py`. Die übrigen
26 Broschüren-Motive gibt es im TDS-Set nicht.

## Maßdifferenz zur Pipeline

| Wert | Pipeline (`pages-spec.css`) | Canvas (`templates/brochure/`) |
|:---|:---|:---|
| Achse außen und innen | `18,0 mm` | `18 mm` — gleich |
| Textbreite | `174,0 mm` | `174 mm` — gleich |
| Kopfsteg | `20,4 mm` | `26,7 mm` |
| Fußsteg | `25,0 mm` | `23,5 mm` |
| Spaltenbreite | `55,4 mm` | `55 mm` |
| Spaltensteg | `4,3 mm` | `4,6 mm` |
| Marginalspalte | gibt es nicht | `38 mm`, Steg `6 mm` |
| Radius | nicht geregelt | `5 px` |
| Headline-Zeilenhöhe | `1,13` | `1,25` |
| Sand White als Seitenfläche | zugelassen (`surface--sand`) | verboten |

### Was die Herkunftsprüfung ergeben hat

**`18 mm` ist belegt** und in beiden Systemen gleich: `--tds-axis: 18mm` in
`templates/tds/template.css`, festgeschrieben in `LAYOUT-CONTRACT.md` als „die eine Achse".
Kein Streitpunkt.

**Der Kopfsteg des Titelblatts ist kein Teil dieses Konflikts.** Dort gelten `18 mm` bei
Logo und `12 mm` bei rundem Siegel — zwei Werte für zwei Absenderzeichen, nicht zwei Werte
für dieselbe Sache. Das steht seit dieser Fassung getrennt im Vertrag und in `brand.json`
unter `grid.cover.margin_top_mm`.

**Der Innenseiten-Kopfsteg ist entschieden.** `docs/print-anwendungen.md` im Repository
`bkmmannesmann/bkm-design-system` führt Kopfsteg `26,7 mm`, Fußsteg `23,5 mm` und ein
Dreispaltenraster mit `55 mm` Spalte und `4,6 mm` Steg, Startpositionen
`18,0 / 77,6 / 137,2 mm`. Für `20,4 mm` fand die Herkunftsprüfung keine Quelle.
`templates/pages/` ist noch nicht nachgezogen — das ändert bestehende Broschüren und
braucht eine eigene Sichtprüfung.

**`20,4 mm` ist nicht belegt.** Der Wert steht ausschließlich in `pages-spec.css` und den
davon abgeleiteten Dateien. Der Dateikopf nennt als Quelle eine Vermessung des Original-PDFs
mit PyMuPDF — dieses PDF war nie im Repository, weder im Arbeitsbaum noch in der
Git-Historie. Der anlegende Commit `94b81a8` führt keine Begründung. Eine rechnerische
Herleitung gibt es nicht: `20,4 / 18 = 1,133` ergibt keine Proportion des Formats.
Der Canvas-Wert `26,7 mm` stammt aus `docs/print-anwendungen.md` des Design-System-Repos
und hat damit eine benennbare Quelle.

**Die Spaltenrechnung der Pipeline geht nicht auf.** `3 × 55,4 + 2 × 4,3 = 174,8 mm`,
deklariert sind `174,0 mm` — eine Differenz von `0,8 mm`. Im erzeugten PDF nachgemessen:
Die Spalten starten bei `18,0 | 77,7 | 137,4 mm`, die dritte endet also bei `192,8 mm`,
während der Satzspiegel bei `192,0 mm` endet. **Die dritte Spalte ragt 0,8 mm über den
rechten Rand.** Die Canvas-Rechnung `3 × 55 + 2 × 4,6 = 174,2 mm` liegt mit `0,2 mm`
deutlich näher; exakt wäre bei `174 mm` Textbreite und `4,6 mm` Steg eine Spalte von
`54,933 mm`.

**Behoben, ohne die Maßfrage vorwegzunehmen.** Spalten- und Satzbreite werden nicht mehr
gesetzt, sondern aus Achse und Steg gerechnet. Damit geht das Raster mit `4,3mm` Steg
genauso auf wie mit `4,6mm` — die Entscheidung unten bleibt offen, der Überstand ist weg.
Die rechte Satzkante liegt jetzt bei `192,00mm`; die verbleibenden `0,26` bis `0,38mm`
in der Messung sind Glyphenüberhang, nicht Raster.

Die Ausgabeprüfung sah nur, wo eine Zeile **anfängt** — deshalb ist ihr der Überstand
entgangen. Sie prüft jetzt auch die rechte Kante, mit `0,5mm` Toleranz für den
Glyphenüberhang. Gegengeprobt: mit den alten Werten meldet sie den Fehler.

### Stand

Die Differenz ist **nicht aufgelöst**. Beide Systeme bleiben unverändert, bis darüber
entschieden ist. Nach dem Rechercheergebnis spricht weiterhin für die Canvas-Maße, dass
`18 mm` ohnehin identisch ist und `20,4 mm` keine auffindbare Quelle hat. Die fehlerhafte
Spaltenrechnung ist kein Argument mehr — sie ist behoben, und zwar so, dass beide
Stegwerte tragen.


## Offen

- Echte Shop-Kategorie-Icons fehlen; `C-Navigation.dc.html` nutzt Phosphor-Platzhalter
- Preise für Mehrfach-Gebinde in `G-Produktseiten.dc.html` stehen als „auf Anfrage"
- Haftungstext in `rahmen-glossar` rechtlich prüfen lassen
- Kein Validator-Skript für Broschüren; die Prüfung liegt bei Redaktion und Review
