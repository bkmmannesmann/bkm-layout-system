# TDS-Template: technische Referenz

Das Verzeichnis `templates/tds/` enthält die zentrale Layoutvorlage für **BKM technische Datenblätter** im DIN-A4-Format. Es wird gemeinsam mit den JSON-Inhalten unter `content/` und dem Build-Befehl `scripts/build_tds.py` verwendet. Die redaktionellen Anforderungen stehen im [Redaktionsstandard](REDAKTIONSSTANDARD.md), der praktische Ablauf im [TDS-Workflow](TDS-WORKFLOW.md).

> **Zielbild:** Kolleginnen und Kollegen pflegen Produktdaten in JSON ein. Das Template erzeugt daraus ein einheitliches Datenblatt, ohne individuelle Layoutanpassungen pro Produkt.

## Architektur

| Baustein | Pfad | Aufgabe |
|---|---|---|
| Jinja2-Template | `templates/tds/template.html` | Seitenstruktur, Inhaltsreihenfolge und Metadaten. |
| TDS-CSS | `templates/tds/template.css` | Drucklayout, Raster, Tabellen, Farben und interne Prüfseite. |
| Icons | `templates/tds/icons/` | Einheitliche Symbolik für Inhaltsabschnitte. |
| Zentraler Markenrahmen | `design-system/variables.css`, `design-system/base.css` | BKM-Farben, Typografie und grundsätzliche Druckeinstellungen. |
| Content | `content/tds-<produkt-slug>/content.json` | Produktbezogene Daten. |
| Prüfung und Build | `scripts/validate_tds.py`, `scripts/build_tds.py` | Strukturprüfung, Freigabesperren und PDF-Erzeugung. |

## Festes Layout

Das veröffentlichte TDS besteht immer aus drei Seiten. Seite 1 enthält den Kopfbereich im Verhältnis 16:9, Vorteile, Eigenschaften und den Beginn der technischen Daten. Seite 2 enthält den Rest der technischen Daten, eine optionale Verbrauchs- oder Formattabelle sowie Anwendungsgebiete und Hinweise. Seite 3 enthält Gebinde und Systemkomponenten, Lagerung, Entsorgung, Rechtliches und den Schluss-Hinweis.

Alle wesentlichen Elemente orientieren sich an einer **18-mm-Achse**. Das Logo ist 42 mm breit, das Key Visual nimmt ein Zehntel der Blattbreite ein. Produktbilder werden in einer Fläche von 230 × 312 Pixel als freigestelltes PNG platziert. Für Home Line und Pro Line wird ausschließlich der zugehörige Badge verwendet; Produkte mit dem Namensbestandteil **Novu** tragen das Home-Line-Badge, alle übrigen Pro Line.

| Token | Wert | Verwendung |
|---|---:|---|
| `--tds-axis` | 18 mm | Gemeinsame linke Ausrichtungsachse. |
| `--tds-logo-w` | 42 mm | Breite des Logos im Kopf. |
| `--tds-keyvisual-w` | 10 % | Breite des Key Visuals. |
| Produktbildfläche | 230 × 312 px | Freigestelltes Produktbild im Kopf. |
| `--tds-radius` | 3 px | Einheitlicher Radius für Farbflächen. |

Die Grundschrift steht auf allen Seiten auf derselben Größe. Läuft eine Seite über, wandert der letzte Block nach hinten — Text wird nicht kleiner gesetzt. Seitenbezogene Dichteregeln sind im CSS nicht zulässig.

Die TDS-spezifischen Farbwerte sind absichtlich lokal im Template definiert, weil sie zusätzlich neutrale Druckfarben und die Markerfläche abbilden. Die primären Markenwerte sind parallel zentral in `design-system/variables.css` gepflegt. Produktordner dürfen keine eigenen Stylesheets oder Farbwerte enthalten.

## Datenmodell

Das vollständige Datenmodell ist in [`tds-content.schema.json`](tds-content.schema.json) beschrieben. Pflichtfelder sind unter anderem Produktname, Produktlinie, Erstelldatum, Asset-Pfade, Beschreibung, Vorteile, Eigenschaften, technische Daten sowie die rechtlichen Fixbausteine.

Die technischen Daten unterstützen exakt drei Zeilentypen: eine Standardzeile, eine Bedingungszeile mit zusätzlicher Kontextinformation und eine Formelzeile für linear geltende Berechnungen. Nichtlineare Verbrauchswerte werden als `matrix` gepflegt. Maßvarianten wie Plattenformate verwenden die gleich strukturierte `format_table`; beide Tabellen tragen Titel, Spalten, Zeilen und einen Hinweis. Gebinde bleiben eine Liste. Systemkomponenten können entweder als Liste mit Gebindegröße und Artikelnummer oder als Gruppe mit `title`, `items` (`name`, `role`) und optionalem `note` gepflegt werden. Ein optionaler `review`-Block erzeugt ausschließlich im Entwurf eine interne Prüfseite; für nachweislich umfangreiche Prüfprotokolle setzt `review_page_count` die erwartete Zahl interner Prüfseiten, standardmäßig `1`. Der aktuelle Datenvertrag unterstützt eine zweite Prüfseite über `review.continuation_after`; der Wert legt fest, nach wie vielen Änderungslistenpunkten die Fortsetzung samt Prüfprotokoll beginnt. Für nachweislich lange, fachlich notwendige Hinweise erlaubt `notes_on_page3: true` die kontrollierte Verlagerung des gesamten Hinweisblocks auf Seite 3.

Das Feld `created_date` trägt das **Erstelldatum** im Format `TT.MM.JJJJ` und erscheint im Kopf der ersten Seite sowie in der Kopfzeile der Folgeseiten. Es ist immer das Datum, an dem die Datei erzeugt wird, nie das Ausgabedatum eines älteren Quellblatts. Die Felder `revision` und `issue_date` sind **nicht** Teil des TDS-Datenvertrags; die Fußzeile führt kein Datum.

## Asset-Regeln

| Asset | Pfad | Freigaberegel |
|---|---|---|
| Logo | `assets/images/logos/logo-deepgreen-green.png` | Nur die freigegebene Wortmarke verwenden. |
| Key Visual | `assets/images/keyvisual-on-light.png` | Nicht nachbauen oder produktspezifisch ersetzen. |
| Line-Badge | `assets/images/badge-homeline.png` oder `assets/images/badge-proline.png` | Muss zur Produktlinie passen. |
| Produktbild | `assets/images/products/<produkt-slug>.png` | PNG mit transparentem Hintergrund; im Release Pflicht. |
| Schriften | `assets/fonts/` | Lokal bereitstellen; aufgrund der Lizenz nicht versioniert. Im Release Pflicht. |
| Abschnittsicons | `templates/tds/icons/` | Kuratierte lokale Phosphor-Icons im Gewicht Bold. **Flächenglyphen:** `.tds-icon svg` setzt `fill`, nicht `stroke`. |

## Entwurf und Veröffentlichung

Ein Entwurf darf offene Punkte enthalten, wenn jede Lücke den Marker `[ANGABE FEHLT: …]` oder `[ZU PRÜFEN: …]` trägt und der `review`-Block die offene Frage, Änderungen gegenüber dem Quell-Input und das Prüfprotokoll dokumentiert. Der Entwurf erhält dadurch eine vierte, klar als intern gekennzeichnete Seite ohne Seitenzahl.

Eine veröffentlichte Fassung darf keine Marker und keinen `review`-Block mehr enthalten. Der Release-Build prüft dies automatisch, ebenso die Pflichtassets, die Markenschriften und die Seitenzahl. Details stehen im [TDS-Workflow](TDS-WORKFLOW.md).

```bash
python3 scripts/validate_tds.py content/tds-neues-produkt/content.json --release
python3 scripts/build_tds.py --content content/tds-neues-produkt/content.json --release
```

## Änderungen an dieser Vorlage

Änderungen an Template, CSS, zentralen Markenvariablen oder Validierungslogik sind Systemänderungen. Sie müssen über einen Pull Request mit technischer und visueller Prüfung erfolgen. Änderungen dürfen nicht in einzelnen Produktordnern dupliziert werden; ansonsten würde die Vergleichbarkeit und Wartbarkeit der Datenblätter verloren gehen. Die Erweiterung um `format_table` und strukturierte `system_components` ist aus der freigegebenen Referenz BKM KS abgeleitet und gilt für alle künftigen TDS.
