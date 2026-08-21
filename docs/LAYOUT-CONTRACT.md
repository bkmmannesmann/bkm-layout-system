# Layoutvertrag TDS

Gehört zu `REDAKTIONSSTANDARD.md` Version 1.1. Der Redaktionsstandard regelt den Inhalt,
dieser Vertrag die Form.

Diese Datei ist die **verbindliche Liste der Layout-Invarianten** für technische Datenblätter.
`scripts/validate_layout.py` prüft sie maschinell. Wer eine Zeile hier ändert, ändert das Design
aller Datenblätter — das geht nur über einen Pull Request mit Sichtprüfung.

Warum es diese Datei gibt: an dem Repository arbeiten mehrere Personen und mehrere KI-Assistenten
aus verschiedenen Accounts. Ohne maschinell geprüfte Invarianten driftet das Layout mit jedem
Beitrag, und die Abweichung fällt erst im gedruckten Blatt auf.

## Maße und Raster

| Invariante | Wert | Grund |
|:---|:---|:---|
| `--tds-axis` | `18mm` | Die **eine** Achse. Logo, Text, Balken, Abschnitte, Tabellen, Fußzeile stehen darauf. Es gibt keine zweite Fluchtlinie. |
| `--tds-logo-w` | `42mm` | Ein Fünftel der Blattbreite. |
| `--tds-keyvisual-w` | `10%` | Ein Zehntel der Blattbreite, bündig an der rechten Blattkante, nichts überlappt es. |
| `--tds-radius` | `3px` | Auf allen eckigen Farbflächen, ohne Ausnahme. Keine Pill-Radien. |
| `.tds-head` Höhe | `118.1mm` | 16:9 vom Blattrand bis Oberkante des Balkens. |
| `.tds-band` | `height: 30px`, `margin-top: -10px` | Randlos über die volle Breite, überlappt den Kopfbereich als Blitzerschutz im Druck. Ohne Text. |
| Produktbild | `230px × 312px` | Feste Fläche, freigestelltes PNG mit Alphakanal, `object-fit: contain`. Kein eingebrannter Schatten. Bei KI-generierten Produktbildern bleibt der Kennzeichnungsvermerk („AI GENERATED") im Bild — er ist nach EU-KI-Verordnung erforderlich und wird nicht wegretuschiert oder beschnitten. |
| Line-Badge | `44px × 182px`, linker Rand `-18mm` | Zwischen Subheadline und Fließtext, ragt bis an die Blattkante. |

## Typografie

Grundschrift **12 px auf allen Seiten**. Seitenbezogene Dichteregeln sind verboten —
`.tds-page:nth-of-type(n)` mit Schriftgrößen ist ein Fehler, nicht eine Lösung. Läuft eine Seite
über, wandert der letzte Block nach hinten (Redaktionsstandard 5.4) oder der Text wird gekürzt.

Headlines Unbounded Black in Versalien, Zeilenhöhe 125 %, Laufweite −0.025em. Subheadline
Unbounded Black, keine Versalien, Pure Green. Fließtext TT Norms Pro, Laufweite −0.015em.
Die Markenschriften liegen im Repository unter `assets/fonts/`; der Release-Build bricht ab, wenn eine Datei fehlt.

## Farben

Nur die Werte aus dem Design-System: Deep Green `#1c4b42`, Transition Green `#287d4b`,
Pure Green `#4daf46`, Lime `#b4e717`, Stone Grey `#494949`, Sand White `#f6f5f2`,
Haarlinie `#e3e1dc`, Markerfläche `#f0fad4`. Die Altwerte `#009245`, `#006837`, `#00A99D`
und `#8CC63F` sind verboten und werden geprüft.

## Icons

Die Abschnittsicons sind **Phosphor Bold als lokale SVG-Dateien** in `templates/tds/icons/`
(`fill="currentColor"`, viewBox `0 0 256 256`). `.tds-icon svg` setzt `fill`, niemals `stroke`
oder `fill: none` — sonst rendern die Icons unsichtbar. Die Größe setzt ausschließlich das CSS;
die SVGs tragen keine `width`/`height`.

**Nur Bold. Keine andere Strichstärke.** Regular, Light, Thin, Duotone und Fill sind nicht
zugelassen — im Datenblatt stehen die Icons in 20-px-Kacheln, alles unter Bold wirkt dünn und
verschwindet im Druck. Die Stärke lässt sich am Pfad **nicht** ablesen: Bold-Pfade enthalten
legitim `a4,4` oder `a16,16`, Regular-Pfade `a12,12`. Gesichert wird sie deshalb über das Motiv:
`scripts/validate_layout.py` bildet den sha256 über die aneinandergehängten `d`-Attribute und
vergleicht ihn mit dem Manifest im Skript. Quelle jeder Datei ist `phosphor-icons/core`,
Verzeichnis `assets/bold/<name>-bold.svg`.

**Jede Datei trägt ihre Lime-Füllung selbst:** `style="fill:#b4e717"` am `svg`-Element, zusätzlich
zu `fill="currentColor"`. Grund: WeasyPrint wendet das Stylesheet des Dokuments **nicht** auf die
Kinder eines inline eingebetteten SVG an — eine CSS-Regel wie `.tds-icon svg { fill: … }` greift im
Browser, im PDF aber nicht, und der Glyph druckt schwarz. Die Prüfung verlangt den Farbwert deshalb
in der Datei. Weil der Hash nur die Geometrie erfasst, bleiben Farb- und Größenangaben frei
änderbar, ohne das Manifest zu berühren.

**Keine Icon-Webfont, kein CDN.** Weder `template.html` noch `template.css` dürfen
`@phosphor-icons/web` laden oder `class="ph …"` verwenden. Gründe: WeasyPrint bekommt die Font
im Offline-Build nicht, und über die Font-Klassen ist die Strichstärke frei wählbar — genau so
entstehen Blätter mit Regular-Icons. Die Icons werden per `{% include 'icons/<name>.svg' %}`
eingebettet.

**Feste Zuordnung.** Jeder Inhaltsblock trägt immer dasselbe Icon, über alle Datenblätter hinweg.
Die Dateien sind nach dem Block benannt, nicht nach dem Motiv — damit kann kein Blatt versehentlich
ein anderes Symbol bekommen:

| Block | Datei | Phosphor-Icon (Bold) |
|:---|:---|:---|
| Vorteile | `icons/vorteile.svg` | `seal-check` |
| Eigenschaften | `icons/eigenschaften.svg` | `atom` |
| Technische Daten | `icons/daten.svg` | `table` |
| Anwendungsgebiete | `icons/anwendung.svg` | `house-line` |
| Hinweise | `icons/hinweise.svg` | `warning` |
| Verpackungseinheiten / Gebinde | `icons/gebinde.svg` | `package` |
| Lagerbedingungen | `icons/lagerung.svg` | `thermometer-simple` |
| Entsorgung | `icons/entsorgung.svg` | `recycle` |
| Rechtliche Hinweise | `icons/recht.svg` | `scales` |

Diese Zuordnung wird nicht produktbezogen geändert. Braucht ein neuer Block ein Icon, kommt eine
Zeile hinzu — eine bestehende wird nicht umbelegt. Das Verzeichnis enthält **genau diese neun
Dateien**; weitere SVGs lässt die Prüfung nicht zu, damit kein Altbestand versehentlich
wieder eingesetzt wird.

Ein neues Icon kommt so ins System: die Datei `assets/bold/<name>-bold.svg` aus
`phosphor-icons/core` übernehmen, `width`/`height` aus dem `svg`-Tag entfernen,
`fill="currentColor" style="fill:#b4e717"` setzen, unter dem Blocknamen in `templates/tds/icons/`
ablegen, Zeile samt Geometrie-Hash in `ICON_MANIFEST` ergänzen, dann
`python3 scripts/validate_layout.py`. Den Hash bewusst zu ändern ist erlaubt und sichtbar — ein
unbemerkter Motivwechsel nicht.

## Metadaten

**Die Seitenzahl ist nicht festgeschrieben.** Drei veröffentlichte Seiten sind der Regelfall,
umfangreiche Produkte dürfen vier oder fünf haben; der interne Prüfteil darf ebenfalls über
mehrere Seiten laufen. Die Fußzeile zählt gegen `page_count`, nicht gegen eine feste Drei.

Im Kopf der ersten Seite und in den Laufköpfen steht **`Erstelldatum: {{ created_date }}`**.
Eine Revisionsnummer und ein Ausgabedatum gibt es nicht. Die Fußzeile trägt Copyright, Anschrift
und Seitenzahl — **kein Datum**. Der interne Prüfteil trägt keine Seitenzahl, nur den Vermerk.

## Bedingungszeile

Die kleine graue Zeile unter einem Parameternamen (`<small>` im Template, `.tds-table th small`
im CSS) ist die **Bedingungszeile** nach Redaktionsstandard 5.1. Sie ist erlaubt, aber an eine
harte Bedingung gebunden:

> Eine Bedingungszeile darf nur stehen, wenn die Bedingung **wörtlich in der angelieferten
> Vorlage** steht. Sie wird nie hinzugefügt, um einen Kennwert zu erklären, zu präzisieren oder
> fachlich zu ergänzen.

Zulässig, weil aus der Quelle: `BOHRLOCHABSTAND` / „nach WTA-Vorgabe" — der Wert 12,5 cm ist
ohne die Bedingung nicht von den anderen Abstandszeilen zu unterscheiden.

Unzulässig: `VERARBEITUNGSTEMPERATUR` / „Umgebung und Untergrund", wenn die Vorlage nur
„mindestens +5 °C" nennt. Das ist eine fachliche Ergänzung. Fehlt die Unterscheidung wirklich,
wird sie als offener Punkt markiert — nicht stillschweigend eingesetzt.

Maschinell nicht prüfbar; die Prüfung liegt bei Redaktion und Review. Der Pull Request fragt sie
über die Checkliste ab. Der fachliche Hintergrund steht in `REDAKTIONSSTANDARD.md`, Abschnitt 5.1.

## Tabellen

Datentabelle: Haarlinien, kein Zebra — bewusst abweichend von der Website-Tabelle, damit das
gedruckte Blatt ruhiger läuft. Verbrauchs- und Formatmatrix: Zebra nach Design-System,
Deep-Green-Kopfzeile, 3 px Radius, Zahlenspalten rechtsbündig mit Tabellenziffern.

## Was Produktordner nicht dürfen

Kein eigenes Stylesheet, keine eigenen Farbwerte, keine `style`-Attribute im Content, keine
produktspezifische Kopie von Template oder CSS. Ein Produktordner enthält `content.json` und
sonst nichts.

## Prüfung

```bash
python3 scripts/validate_layout.py                        # Design
python3 scripts/validate_tds.py content/tds-x/content.json  # Inhalt
```

Beide Prüfungen laufen in der CI bei jedem Pull Request.
