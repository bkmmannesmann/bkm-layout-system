# Workflow für technische Datenblätter

Dieses Dokument beschreibt den verbindlichen Ablauf zur Erstellung eines **BKM technischen Datenblatts (TDS)**. Es ergänzt den [Redaktionsstandard](REDAKTIONSSTANDARD.md) um die praktische Arbeit im Repository. Das Ziel ist ein nachvollziehbarer Weg von belegten Produktinformationen zu einer druckfähigen PDF-Ausgabe, ohne dass Redaktion oder Anwendungstechnik Layout-Dateien bearbeiten müssen.

> **Grundsatz:** Ein TDS ist eine technische Auskunft, kein Verkaufstext. Unbelegte Angaben bleiben sichtbar markiert und blockieren die Veröffentlichung.

## Rollen und Freigaben

| Rolle | Verantwortung | Ergebnis |
|---|---|---|
| Redaktion | Strukturiert Quellinformationen, formuliert in BKM-Sprache und dokumentiert Änderungen. | Vollständiger Entwurf mit `review`-Block. |
| Anwendungstechnik | Prüft Kennwerte, Verarbeitung, Verbrauch und Plausibilität. | Abgezeichnetes Prüfprotokoll. |
| Qualitätsmanagement | Prüft Normen, Prüfzeugnisse und Nachweise. | Nachweisprüfung ohne offene Marker. |
| Leitung Technik | Erteilt die fachliche Freigabe. | Freigabe mit Datum, dokumentiert im Freigaberegister. |
| Satz und Versionierung | Führt den Release-Build aus und prüft die PDF-Ausgabe. | Veröffentlichungsfähige PDF. |

## Verzeichnis- und Dateikonventionen

Neue Datenblätter erhalten einen eigenen Ordner im Muster `content/tds-<produkt-slug>/`. Der Produkt-Slug wird kleingeschrieben und nutzt Bindestriche, beispielsweise `content/tds-novutop-primer/`. Die Datei heißt immer `content.json`. Produktbilder liegen ausschließlich unter `assets/images/products/` und werden nicht in den Content-Ordner kopiert.

| Artefakt | Verbindlicher Ort | Regel |
|---|---|---|
| TDS-Layout | `templates/tds/` | Nur durch berechtigte Layoutpflege ändern. |
| Inhalt eines Produkts | `content/tds-<produkt-slug>/content.json` | Eine Datei pro Produkt. |
| Produktbild | `assets/images/products/<produkt-slug>.png` | Freigestelltes PNG mit transparentem Hintergrund. |
| Freigaberegeln | `docs/REDAKTIONSSTANDARD.md` | Fachlich verbindliche Quelle. |
| Datenvertrag | `docs/tds-content.schema.json` | Maschinenlesbare Strukturreferenz. |
| Generierte PDFs | `output/` | Nie committen. |

Die fünf vorhandenen Referenzen decken die wesentlichen Fälle ab: `tds` für den kurzen Standardfall, `tds-hz250pro` für lineare Formelzeilen, `tds-hzc` für eine Verbrauchsmatrix, `tds-ks` für Formattabelle und Systemkomponenten sowie `tds-novusan` für die Home Line.

## Neuer Entwurf

Kopiere zunächst die strukturell passendste Referenz in einen neuen Produktordner. Verwende den kurzen Standardfall, wenn keine Matrix oder Systemkomponenten erforderlich sind. Für nichtlineare Verbrauchswerte ist `tds-hzc` die Referenz, bei Formaten und Systemteilen `tds-ks`. Ersetze anschließend ausschließlich die Werte in `content.json`; HTML und CSS bleiben unverändert. Setze `created_date` auf das Datum, an dem du die Datei erzeugst.

```bash
cp -R content/tds content/tds-neues-produkt
# Das freigestellte, freigegebene Produktbild nach assets/images/products/neues-produkt.png legen.
python3 scripts/validate_tds.py content/tds-neues-produkt/content.json
python3 scripts/build_tds.py --content content/tds-neues-produkt/content.json
```

Für einen Entwurf sind offene Punkte zulässig, sofern sie sichtbar als `[ANGABE FEHLT: …]` oder `[ZU PRÜFEN: …]` markiert und im `review`-Block vollständig erläutert werden. Der Entwurfs-Build erzeugt dann eine zusätzliche interne Prüfseite ohne Seitenzahl. Eine fehlende Produktgrafik oder lokal nicht installierte Lizenzschrift wird im Entwurf als Warnung angezeigt, damit die technische Inhaltsprüfung nicht stillschweigend zur Layoutfreigabe wird.

## Pflichtangaben und Markenregeln

Das Feld `created_date` ist für jeden Entwurf Pflicht und trägt das **Erstelldatum** im Format `TT.MM.JJJJ` — den Tag, an dem die Datei erzeugt wird, nie das Ausgabedatum eines älteren Quellblatts. Eine Revisionsnummer wird nicht geführt; Änderungen sind über den Commit-Verlauf und das Freigaberegister nachvollziehbar. Das Feld `product_line` ist exakt `HOME LINE` oder `PRO LINE`; der zugehörige Badge wird automatisch gegengeprüft. Produkte mit dem Namensbestandteil **Novu** gehören zur Home Line.

Die Produktbeschreibung darf maximal 360 Zeichen enthalten. Vorteile und Eigenschaften umfassen jeweils fünf bis sieben Einträge. Das Template erzwingt die BKM-Grundachse von 18 mm, die Bildfläche von 230 × 312 Pixel und die zentral gepflegten BKM-Farben. Aus diesem Grund dürfen keine individuellen CSS-Änderungen in einzelnen Produktordnern angelegt werden.

Lange Hinweise bleiben grundsätzlich auf Seite 2. Reicht der Platz trotz präziser, fachlich vollständiger Formulierung nicht aus, setzt die Redaktion `"notes_on_page3": true`. Das Template verlagert dann den vollständigen Hinweisblock kontrolliert auf Seite 3. Der Text wird dabei nicht kleiner gesetzt. Diese Ausnahme ist nur nach Sichtprüfung der PDF zulässig; der HZ-C-Referenzfall demonstriert sie.

## Von der Fachprüfung zum Release

Nach der technischen Prüfung übernimmst du die bestätigten Kennwerte. Unbelegte Angaben werden nicht geschätzt. Entferne erst dann alle Marker und den gesamten `review`-Block aus der Release-Fassung. Halte die Freigabe selbst im Pull Request, im Qualitätsmanagementsystem oder in einem anderen vorgesehenen Freigaberegister fest; sie gehört nicht in die veröffentlichte PDF.

| Prüfschritt | Entwurf | Release |
|---|---:|---:|
| JSON-Struktur vollständig | Pflicht | Pflicht |
| Produktbild vorhanden und transparent | Warnung | Sperre |
| Markenschriften unter `assets/fonts/` | Warnung | Sperre |
| Offene Marker | Erlaubt, mit `review` | Sperre |
| Interner Prüfteil `review` | Pflicht bei offenen Punkten | Sperre |
| Seitenzahl | 4 Seiten bei Review, sonst 3 | Exakt 3 Seiten |
| Erstelldatum `created_date` | Pflicht | Pflicht |

Der Release-Build stoppt bei fehlenden Produktassets, fehlenden Markenschriften, offenen Markern, einem noch enthaltenen `review`-Block oder falscher Seitenzahl. Das schützt davor, einen internen Entwurf als produktives Datenblatt zu publizieren.

```bash
python3 scripts/validate_tds.py content/tds-neues-produkt/content.json --release
python3 scripts/build_tds.py \
  --content content/tds-neues-produkt/content.json \
  --output output/tds-neues-produkt.pdf \
  --release
```

## Visuelle Schlussprüfung

Nach einem erfolgreichen Release-Build öffnet die verantwortliche Person die PDF und prüft mindestens Produktbild, Umbruch, Tabellenzeilen, Markenbadge, Abschnittsicons, Erstelldatum und Seitenzählung. Die lizenzierten Schriften müssen lokal unter `assets/fonts/` verfügbar sein. Dieser Ordner ist absichtlich nicht versioniert; ohne die Schriften setzt WeasyPrint Ersatzschriften, wodurch Laufweite und Umbruch abweichen — der Release-Build bricht deshalb ab.

## Änderungen am System

Änderungen an `templates/tds/`, zentralen Markenvariablen oder dem Redaktionsstandard müssen über einen Pull Request erfolgen. Der Pull Request verwendet die Checkliste in `.github/pull_request_template.md`. Einzelne Produktinhalte dürfen nur dann als Release gemergt werden, wenn der Release-Build fehlerfrei durchläuft und die fachliche Freigabe dokumentiert ist.
