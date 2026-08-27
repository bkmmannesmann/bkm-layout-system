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
| Fußsteg | `23,5 mm` | Innenseiten. Seiten ohne Seitenzahl sind nicht daran gebunden, siehe unten. |
| Textbreite | `174 mm` | 210 − 2 × 18 |
| Dreispaltig | `55 mm` Spalte, `4,6 mm` Steg | Fließtextseiten |
| Marginalspalte | `38 mm`, Steg `6 mm` | Textstrecken, Verfahren, Produktseiten |
| Radius | `5 px` | Abweichung, siehe unten |
| Haarlinie | `#e3e1dc` | Wie TDS |

### Ausnahme: Seiten ohne Seitenzahl

Der Fußsteg von `23,5 mm` begrenzt den Satzspiegel nach unten. **Wo die Seitenzahl steht,
unterscheiden sich die beiden Ebenen:** der Produktionspfad setzt sie über `.page__footer`
in den Fußsteg (Grundlinie `279 mm`, unterdrückbar über `no_folio`), der Canvas setzt sie in
den Kolumnentitel am Kopf — eine Zeile mit Rubrik links, Ziffer rechts, Unterlinie. Der
Fußsteg bleibt im Canvas leer; er hält beide Ebenen auf demselben Satzspiegel.

Eine Seite ohne Seitenzahl — Rückseite (U4) und randabfallende Strecken — ist daran nicht
gebunden; dort ist nur der Beschnitt die Grenze. `scripts/build_pages.py` prüft solche Seiten
gegen `BLEED_SAFE = 285 mm` statt gegen die `272 mm` einer Satzseite; die Fallunterscheidung
steht dort in `_check_type_area`.

Genutzt wird das aktuell an einer Stelle: `B-Rahmenseiten.dc.html`, Seite 10 (U4) steht auf
`padding: 26.7mm 18mm 18mm`. Der Impressumsblock endet dort bei `279,0 mm`. Der
Produktionspfad setzt dieselbe Seite über `.backcover-imprint { top: 271.0mm }` — also
ebenfalls tiefer, als der Fußsteg einer Satzseite zuließe.

Die Ausnahme ist eine **Erlaubnis, kein Gebot**: Seiten ohne Ziffer dürfen auf `23,5 mm`
stehenbleiben, wenn sie den Raum nicht brauchen — die meisten tun das. Über alle 74
Seiten-Container hinweg gilt: **alle 44 Seiten mit Ziffer stehen auf `23,5 mm`**, und alle
drei mit abweichendem Fuß tragen keine. `scripts/validate_brochure.py` prüft genau das; ein
abweichender Fuß auf einer Seite mit Ziffer wird gemeldet.

## Titelblatt

| Element | Wert |
|:---|:---|
| Hero-Grafik | `210 × 125 mm` — 118,125 mm für den 16:9-Teil, darunter 6,875 mm Eckerweiterung unten rechts |
| Keyvisual | `42 mm` breit, rechts angeschnitten, `top: 102,416 mm`, **`keyvisual-on-light.svg`** (dreifarbig) |
| Foto | ab `117,46 mm` bis Seitenunterkante, `210 × 179,54 mm`, `object-fit: cover` |
| Logo | `42 mm`, Kopfsteg `18 mm` |
| Siegel (Fachbetriebs-Titel) | `28,16 mm` rund, Kopfsteg `12 mm`, ersetzt das Logo |
| Headline | Unbounded 900, `30 pt`, Zeilenhöhe `1,25`, Laufweite `0` |
| Subheadline | Unbounded 900, `12 pt`, Zeilenhöhe `1,3`, Laufweite `0` |
| Fließtext | TT Norms Pro 400, `12 pt`, Zeilenhöhe `1,25`, Laufweite `−0,015 em`, max. 2 Zeilen |

### Die Seite braucht eine feste Höhe und absolute Kinder

```css
.seite   { width: 210mm; height: 297mm; position: relative; overflow: hidden; }
.element { position: absolute; }
```

Ohne das stimmen die Maße oben zwar, aber die Seite bricht um. Hero-Grafik und Foto
**überlappen sich um 7,54 mm**: die Grafik ist `125 mm` hoch, das Foto beginnt schon bei
`117,46 mm`. Absolut positioniert endet das Foto exakt bei `297 mm`. Stehen beide im Fluss
untereinander, addieren sie sich auf `304,54 mm` — und das Foto rutscht auf die nächste Seite.

`height: 297mm`, nicht `min-height` und nicht `auto`: eine Seite mit automatischer Höhe wächst
mit ihrem Inhalt. `overflow: hidden`, damit randabfallende Elemente abgeschnitten statt
umgebrochen werden.

**Im Vorschaufenster fällt das nicht auf.** Dort gibt es keinen Seitenumbruch, der Container
scrollt einfach weiter. Sichtbar wird es erst beim Export nach PDF. Wer eine Titelseite baut,
prüft sie deshalb im PDF, nicht in der Vorschau.

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

**Damit hängt die Fassung an der Position.** Auf dem Titelblatt gilt immer
`keyvisual-on-light.svg`, die dreifarbige — die weiße Fassung hat keinen
Pure-Green-Chevron, und die Zahl verliert ihre Begründung. `on-dark` gehört auf
durchgehend dunkle Flächen wie die Rückseite, `lime` ist Akzentfarbe.
`scripts/validate_brochure.py` prüft das für `A-Titelblaetter.dc.html`.

### Blitzerschutz

Die Eckerweiterung ist `10 × 10 mm` bei `top: 117,6 mm` — sie ragt also 0,5 mm in
die Hero-Fläche hinein. Zusätzlich beginnt das Foto bei `117,46 mm`, überlappt die
Hero-Grafik damit um 7,54 mm. Zwei Überlappungen, weil an dieser Kante drei Ebenen
zusammentreffen.

Der TDS löst dasselbe Problem über `.tds-band` mit `margin-top: -10px`. Beide Wege
sind gültig; der Broschüren-Weg ist nötig, weil das Hero eine Grafikdatei ist und
kein CSS-Balken.

## Paginierung

**Titel und Rückseite zählen nicht mit.** Die erste Seite danach trägt die Ziffer `1` —
auch dann, wenn sie keine anzeigt.

Eine Seite darf ihre Ziffer unterdrücken: Editorial, Inhaltsverzeichnis, Rückseite. Sie
**zählt trotzdem mit**, die Folge läuft danach ohne Sprung weiter. Liegt das Titelblatt im
selben Dokument, steht auf Blatt `N` damit immer die Ziffer `N−1`.

Genau daran ist ein Fehler aufgefallen: Blatt 3 trug die `03` statt der `02`, weil das
Titelblatt mitgezählt wurde. Der Versatz zog sich durch das ganze Dokument.

`scripts/check_export.py` rechnet das nach und meldet den Versatz einmal, nicht auf jeder
Seite — er zieht sich ohnehin durch.

Ändert sich die Zählung, **wandern die Verweise im Inhaltsverzeichnis mit**.

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

Kasten mit `5 px` Radius, Glyph immer in Lime Green. Die Kastenfarbe hängt am Absender
und am Untergrund:

| | auf hellem Grund | auf dunklem Grund |
|:---|:---|:---|
| BKM Mannesmann AG | Deep Green | Transition Green |
| Fachbetrieb | **Transition Green** | Transition Green |

Im Fachbetrieb-Kontext trägt der Kasten auch auf hellem Grund Transition Green, weil Deep Green
der AG vorbehalten bleibt. Damit ist der Lime-Glyph über alle Kontexte gleich — bei Pure Green als
Kasten hätte auch der Glyph wechseln müssen, und aus einer Regel wären zwei geworden.
Entscheidung vom 25.08.2026.

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

## Export prüfen

Jeder Export aus dem Canvas lässt sich gegen `brand.json` prüfen:

```bash
python3 scripts/check_export.py <datei.pdf>
```

Geprüft werden Schriften, Blattmaß, Satzspiegel gegen Kopf- und Fußsteg, Textfarben
gegen die Palette, Bildauflösung und Bildbeschnitt.

**Der Anlass war ein Fehler, den fünf Runden lang niemand bemerkt hat.** In einem Export
standen rund 4.000 von 4.200 Textstellen in `.SF NS`, der Systemschrift von macOS, statt
in TT Norms Pro — eine `font-family` in der `<doc-page>`-Hülle hatte die Body-Regel
überschrieben. Die Headlines waren korrekt, das PDF sah heil aus. Chrome kann San
Francisco nicht regulär einbetten und legt sie als **Type3** ab; daran ist es messbar.

Die Prüfung meldet zwei Klassen getrennt:

- **Verstöße** — Fremdschrift, falsches Blattmaß, Satz außerhalb des Satzspiegels,
  Farbe nicht in der Palette. Exitcode 1.
- **Hinweise** — niedrige Bildauflösung, Bilder über die Blattkante hinaus, Blattmaß
  minimal knapp. Sie brauchen ein Urteil, keinen Reflex.

Seiten ohne Seitenzahl werden gegen `285 mm` geprüft statt gegen `273,5` — dieselbe
Ausnahme wie oben, derselbe Wert wie `BLEED_SAFE` in `build_pages.py`.

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

Ein KI-generiertes Motiv trägt den Vermerk **„AI GENERATED"** als kleines Symbol
**im Bild selbst** — nicht als Bildunterschrift, nicht als Text im Layout. Nach
EU-KI-Verordnung erforderlich.

**Eine Sammelangabe im Impressum ersetzt ihn nicht.** Beides zugleich ist zulässig, der
Vermerk am Bild bleibt Pflicht. Nicht wegretuschieren, nicht überdecken, nicht
beschneiden.

In welcher Ecke er sitzt, entscheidet sich am einzelnen Motiv — oben oder unten, links
oder rechts. Eine feste Ecke gibt es nicht.

### Beschnitt: das Motiv gewinnt

`object-fit: cover` auf einem Kasten mit abweichendem Seitenverhältnis schneidet an den
Rändern weg. **Die Bildkomposition hat dennoch Vorrang.** Ein Motiv wird nicht in ein
anderes Format gepresst, nur damit der Vermerk sichtbar bleibt — weder durch Anpassen des
Kastens noch durch Verzicht auf den Beschnitt.

Stattdessen: prüfen, welche Ecken der Beschnitt übriglässt, und den Vermerk dorthin
setzen. Reicht keine Ecke, wird das Motiv **neu ausgerichtet** — der Bildausschnitt
wandert, nicht der Kasten.

`scripts/check_export.py` meldet zu jedem beschnittenen Bild, welche Ecken sichtbar
bleiben und welche verdeckt sind, etwa:

```
Seite 10: Bild beschnitten (links 4 mm). Für den KI-Vermerk nutzbar:
          oben rechts, unten rechts — verdeckt: oben links, unten links.
```

Das ist ein **Hinweis, kein Verstoß**: die Entscheidung liegt bei der Bildredaktion.

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

## Raster: keine Differenz mehr

Seit dem 25.08.2026 gibt es keine. Kopfsteg `26,7 mm`, Fußsteg `23,5 mm` und Spaltensteg
`4,6 mm` stammen aus `docs/print-anwendungen.md` des Design-System-Repositories und sind in
`templates/pages/` umgesetzt. Für die früheren `20,4 mm` und `4,3 mm` fand die Herkunftsprüfung
keine Quelle: der Wert stand nur in `pages-spec.css`, das Original-PDF der Vermessung war nie im
Repository, und der anlegende Commit führte keine Begründung.

Beim Umstellen fiel auf, dass die `feature`-Seite der Demo mit einer Bildhöhe von `131,2 mm` im
engeren Raster nicht mehr aufgeht — der Satz lief 19 mm über den Fußsteg. Die Ausgabeprüfung hat
das gemeldet, die Bildhöhe steht jetzt auf `110 mm`. Wer eine bestehende Broschüre auf dieses
Raster zieht, prüft die `feature`-Seiten zuerst.

## Offen

- Echte Shop-Kategorie-Icons fehlen; `C-Navigation.dc.html` nutzt Phosphor-Platzhalter
- Preise für Mehrfach-Gebinde in `G-Produktseiten.dc.html` stehen als „auf Anfrage"
- Haftungstext in `rahmen-glossar` rechtlich prüfen lassen
- Kein Validator-Skript für Broschüren; die Prüfung liegt bei Redaktion und Review
