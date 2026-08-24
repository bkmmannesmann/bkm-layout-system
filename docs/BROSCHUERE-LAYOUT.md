# Layoutvertrag Broschüre

Regelt die Form des **Innenteils** von Produkt- und Unternehmensbroschüren. Für technische
Datenblätter gilt stattdessen `LAYOUT-CONTRACT.md`; das Titelblatt regelt der Cover-Abschnitt
in `README.md`.

Diese Datei ist die **verbindliche Liste der Layout-Invarianten**. `scripts/validate_brochure.py`
prüft sie maschinell. Wer eine Zeile hier ändert, ändert das Layout aller Broschüren — das geht
nur über einen Pull Request mit Sichtprüfung.

Warum es diese Datei gibt: dieselbe Begründung wie beim Datenblatt. An dem Repository arbeiten
mehrere Personen und mehrere KI-Assistenten aus verschiedenen Accounts. Ohne maschinell geprüfte
Invarianten driftet das Layout mit jedem Beitrag, und die Abweichung fällt erst im gedruckten
Heft auf.

Bei Widerspruch zwischen diesem Dokument und dem Code gewinnt das Dokument.

## Herkunft der Maße

Die Werte stammen aus einer Vermessung der bestehenden Broschüre mit PyMuPDF. Der Messwertblock
im Kopf von `templates/pages/pages-spec.css` bleibt als Herkunftsnachweis stehen, ist aber **nicht**
die geltende Quelle — geltend sind die Variablen. Wo Messung und Corporate Design auseinanderliefen,
gewinnt das Corporate Design; die drei betroffenen Fälle stehen unter „Farben".

## Maße und Raster

Format DIN A4, 210mm × 297mm, randlos (`@page { margin: 0 }`). Die Seitengröße wird nicht
seitenweise variiert.

| Invariante | Wert | Grund |
|:---|:---|:---|
| `--brochure-margin-x` | `18.0mm` | Die eine senkrechte Fluchtlinie, links wie rechts. Headlines, Fließtext, Fußzeile, Impressum und Badge stehen darauf. Es gibt keine zweite. |
| `--brochure-margin-top` | `20.4mm` | Oberkante der ersten Headline, zugleich Innenabstand jedes Bandes. |
| `--brochure-footer-zone` | `25.0mm` | Fußsteg. Kein Satz läuft hinein — er ist für Seitenzahl und Kolumnentitel reserviert. |
| `--brochure-col` | `55.4mm` | Eine Spalte. |
| `--brochure-gutter` | `4.3mm` | Spaltenabstand. |
| `--brochure-col-2` | `115.1mm` | Zwei Spalten: 2×55.4 + 1×4.3. |
| `--brochure-col-3` | `174.0mm` | Drei Spalten: 3×55.4 + 2×4.3. Zugleich die Satzspiegelbreite. |

Spalten-Startpositionen: `18.0mm | 77.7mm | 137.3mm`. Ein- und zweispaltige Sätze stehen auf
denselben Kanten, sie erfinden keine eigenen.

Diese Variablen stehen im `:root`-Block von `templates/pages/pages-spec.css` und **nicht** in
`design-system/variables.css`. Grund: die generischen `--margin-*` und `--column-gap` dort führen
15mm und 5mm und beschreiben ein anderes Raster. Die beiden Sätze gehören zusammengeführt; bis
dahin ist das Broschürenraster ausdrücklich das hier definierte.

## Typografie

Die Grundschrift ist **9pt auf allen Seiten**. Seitenbezogenes Verkleinern, um Inhalt
unterzubringen, ist verboten — dieselbe Regel wie beim Datenblatt. Läuft eine Seite über, wird
der Text gekürzt oder ein Block wandert auf die nächste Seite.

| Element | Schrift | Größe | Farbe | Besonderheit |
|:---|:---|:---|:---|:---|
| Hauptheadline | Unbounded Black | 30pt | Pure Green | Versalien, Zeilenhöhe 1.13, **höchstens zwei Zeilen** |
| Sektions-Headline | Unbounded Black | 18pt | Transition Green | keine Versalien, Zeilenhöhe 1.25 |
| Leadline | Unbounded Black | 9pt | Pure Green | einzeilige Merksatzzeile über dem Fließtext |
| Fließtext | TT Norms Pro Regular | 9pt | Stone Grey | Blocksatz, Silbentrennung an, Zeilenhöhe 1.42 |
| Fließtext hervorgehoben | TT Norms Pro Bold | 9pt | Stone Grey | — |
| CTA-Headline (Rückseite) | TT Norms Pro Bold | 16pt | Deep Green | — |
| Seitenzahl | TT Norms Pro Bold | 8pt | siehe Fußzeile | Laufweite 0.02em |
| Kolumnentitel | TT Norms Pro Regular | 8pt | siehe Fußzeile | ohne Transparenz, siehe unten |
| Impressum (Rückseite) | TT Norms Pro Regular | 6pt | Schwarz | — |

Die Hauptheadline läuft **höchstens zwei Zeilen** — dieselbe Regel wie auf dem Titelblatt. Eine
dritte Zeile drückt alles darunter aus dem Raster. Die Ausgabeprüfung zählt die Grundlinien in
30pt und bricht ab drei ab.

Der Fließtext setzt `hyphenate-character: "-"`. Ohne diese Zeile stellt WeasyPrint an jeder
Trennstelle `.notdef` als schwarzes Kästchen dar, weil TT Norms Pro den Trennstrich U+2010 nicht
enthält. Die Zeile wird nicht entfernt.

Die Markenschriften liegen unter `assets/fonts/`. Vorhanden sind von Unbounded **nur** der
Black-Schnitt und von TT Norms Pro Regular und Bold; weitere Schnitte anzusprechen ist wirkungslos.
Von TT Norms Pro beziehen Ä, Ö, Ü, ß, ä, ö, ü und ẞ eine lokale Sans-Serif, weil einige externe
PDF-Renderer sonst einen Trial-Hinweis einsetzen — dieselbe Absicherung wie in
`design-system/base.css`.

Verweist ein Stylesheet auf eine Schriftdatei, die nicht existiert, meldet WeasyPrint das **nicht**,
sondern setzt still eine Ersatzschrift. Genau so lief der Innenteil zeitweise in DejaVu Sans. Die
Prüfung liest deshalb die eingebetteten Schriften des erzeugten PDFs.

## Vertikale Abstände

| Von → Nach | Abstand |
|:---|:---|
| Hauptheadline → Sektions-Headline | 3.0mm |
| Sektions-Headline → Fließtext | 4.4mm |
| Sektions-Headline → Leadline | 9.7mm |
| Leadline → Fließtext | 5.4mm |
| Zwischen zwei Sektionen | 28.2mm |

## Farben

Nur die Werte aus dem Design-System, bezogen über `design-system/variables.css`:
Deep Green `#1c4b42`, Transition Green `#287d4b`, Pure Green `#4daf46`, Lime `#b4e717`,
Stone Grey `#494949`, Sand White `#f6f5f2`, Haarlinie `#e3e1dc`, Rule `#d9d7d3`.

Die Altwerte `#009245`, `#006837`, `#00A99D` und `#8CC63F` sind verboten und werden geprüft —
dieselbe Liste wie im TDS-Vertrag.

Drei gemessene Töne wichen um einen Rasterschritt vom Corporate Design ab und sind darauf
normiert worden. Sie dürfen nicht zurückgeändert werden:

| gemessen | gilt | Ton |
|:---|:---|:---|
| `#484848` | `#494949` | Stone Grey |
| `#277c4b` | `#287d4b` | Transition Green |
| `#8cc63f` | `#b4e717` | Lime — der Altwert ist ausdrücklich verboten |

Zwei weitere Werte waren Eigenbau und zeigen jetzt auf die Palette: Bildplatzhalter `#d8d8d9`
auf Rule `#d9d7d3`, Trennlinie im Inhaltsverzeichnis `#e0e0e0` auf Haarlinie `#e3e1dc`.

**Im Stylesheet und im Template steht kein Hex-Wert.** Farben werden ausschließlich über
`var(--bkm-*)` angesprochen. Die beiden Ausnahmen sind die Rollenvariablen
`--brochure-placeholder-bg` und `--brochure-rule`, die selbst wieder auf Palettenwerte zeigen.

## Flächen

Farbflächen werden über **benannte Flächen** angesprochen, nicht über Hex-Werte. Der Name
bestimmt Fläche, Textfarbe und Akzentfarbe gemeinsam — dadurch kann keine Kombination entstehen,
die im Druck nicht trägt:

| Name | Fläche | Text | Hauptheadline | Sektions-Headline | Akzent (Leadline) |
|:---|:---|:---|:---|:---|:---|
| `deep` | Deep Green `#1c4b42` | Weiß | Lime | Weiß | Lime |
| `transition` | Transition Green `#287d4b` | Weiß | Lime | Weiß | Lime |
| `pure` | Pure Green `#4daf46` | Weiß | Deep Green | Weiß | Deep Green |
| `stone` | Stone Grey `#494949` | Weiß | Pure Green | Weiß | Lime |
| `sand` | Sand White `#f6f5f2` | Stone Grey | Pure Green | Transition Green | Pure Green |
| `white` | Weiß `#ffffff` | Stone Grey | Pure Green | Transition Green | Pure Green |

Der Akzent ist auf allen dunklen Flächen **Lime**, nicht Pure Green. Grund ist der gemessene
Kontrast: Pure Green auf Transition Green ergibt 1.8:1 und ist als 9-pt-Leadline nicht lesbar.
Lime bringt auf Transition Green 3.5:1, auf Deep Green 6.7:1 und auf Stone Grey 6.2:1. Das weicht
bewusst vom Titelblatt-Schema ab, wo die Subheadline in 12pt steht und Pure Green trägt.

Die Hauptheadline behält den Ton der vermessenen Vorlage: Pure Green auf Stone Grey und auf hellem
Grund, Deep Green auf Pure Green, Lime auf den beiden dunklen Grüntönen.

Andere Kombinationen sind nicht zugelassen.

## Seitentypen

Der Innenteil kennt sieben Typen. Ein Seitentyp legt fest, wie eine Seite aufgebaut ist; er wird
im Content über `type` gewählt.

| Typ | Aufbau |
|:---|:---|
| `opener` | Kapitelöffner. Obere Blatthälfte (131.2mm) mit Hauptheadline, untere (165.8mm) mit Sektions-Headline, Leadline und Spaltentext. Beide Hälften tragen eine benannte Fläche. |
| `content` | Textseite auf weißem Grund. Optionale Hauptheadline, Sektions-Headline, Leadline, ein- bis dreispaltiger Satz, optional eine zweite Sektion. |
| `feature` | Bild-Text-Kombination in drei Ausprägungen: `top-image`, `left-image`, `right-image`. Optional ein unteres Band mit eigener Fläche. |
| `process` | Nummerierte Schritte mit Titel und Fließtext, optional ein Vorteilsblock. |
| `list` | Aufzählung aus Titel-/Textpaaren. |
| `toc` | Inhaltsverzeichnis, ein- oder zweispaltig, Kapitel fett und Unterpunkte mager. |
| `backcover` | Rückseite mit CTA-Block, Kontaktdaten, Impressum und optionalem Line-Badge. |

**Bänder stehen im Fluss, nicht absolut.** Auf der `feature`-Seite laufen Bild- und Textbänder
über die volle Blattbreite untereinander weg. Ein absolut gesetztes Band, dessen Oberkante frei
gewählt wird, hat den Text darüber verdeckt, ohne dass der Build etwas gemeldet hat. Das Feld
`lower_top` existiert deshalb nicht mehr.

**Das letzte Band einer Seite läuft bis zur Blattunterkante durch.** Sonst bricht die Farbfläche
auf halber Höhe ab und die Fußzeile steht auf unbestimmtem Grund.

## Seitenzahl und Kolumnentitel

Die Fußzeile sitzt auf der Grundlinie **18mm über der Blattunterkante**, also im selben Abstand
wie der seitliche Satzspiegelrand.

Die Ziffer steht außen, der Kolumnentitel innen: bei gerader Nummer — linke Seite im Bund —
die Ziffer links, bei ungerader die Ziffer rechts. Die Ziffer ist immer zweistellig (`02`,
nicht `2`).

**Gezählt wird über alle Seiten des Dokuments**, auch über die ohne sichtbare Ziffer. Sonst
stimmen die Verweise im Inhaltsverzeichnis nicht mehr. `page_number_start` gibt die Nummer der
ersten Innenseite an und ist **2**, weil das Titelblatt ein eigenes PDF ist und Seite 1 trägt.
`no_folio` unterdrückt die Ziffer auf einer Seite, ohne die Zählung anzuhalten; Inhaltsverzeichnis
und Rückseite tragen keine.

Die Farbe richtet sich nach dem letzten Band der Seite: auf farbigem Grund Weiß, auf hellem
Grund Stone Grey. `folio_color` übersteuert das für Ausnahmen.

Ziffer und Kolumnentitel unterscheiden sich im **Schnitt**, nicht in der Deckkraft: die Ziffer
steht Bold, der Kolumnentitel Regular. `opacity` ist hier verboten — WeasyPrint legt transparente
Elemente in eine eigene Transparenzgruppe, die im Druck rastert statt sauber zu separieren. Die
Ausgabeprüfung kann die Position solcher Elemente außerdem nicht mehr auflösen, weil ihre
Koordinaten dann im lokalen Raum des XObjects stehen.

## Bilder

Fehlt eine Bilddatei, rendert WeasyPrint den Alt-Text in einer Ersatzschrift statt das Bild — im
PDF sieht das aus wie ein Satzfehler, nicht wie eine fehlende Datei. Bilder liegen unter
`assets/images/`; der Release-Build bricht ab, wenn eine referenzierte Datei fehlt.

Trägt ein Produktbild den Vermerk „AI GENERATED", bleibt er sichtbar im Bild. Er ist nach
EU-KI-Verordnung erforderlich und wird nicht wegretuschiert, beschnitten oder überdeckt —
dieselbe Regel wie beim Datenblatt.

## Was Content-Ordner nicht dürfen

Kein eigenes Stylesheet, **keine Hex-Farbwerte**, keine `style`-Attribute, keine Millimeterangaben
zur Positionierung, keine broschürenspezifische Kopie von Template oder CSS. Ein Content-Ordner
enthält `content.json` und sonst nichts.

Flächen werden über die Namen aus „Flächen" gewählt, nicht über Farbwerte. Das ist derselbe
Grundsatz wie beim Datenblatt: der Inhalt bestimmt, *was* auf der Seite steht, das Layoutsystem
bestimmt, *wie* es aussieht.

## Prüfung

```bash
python3 scripts/validate_brochure.py                              # Design
python3 scripts/validate_brochure.py content/<ordner>/content.json  # Inhalt
python3 scripts/build_pages.py <ordner>                           # Bau
```

Beide Prüfungen laufen in der CI bei jedem Pull Request.
