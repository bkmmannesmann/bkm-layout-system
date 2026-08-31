# Layoutvertrag Verarbeitungsanleitung

Verbindlich für `templates/anleitung/` und jede Datei unter
`content/anleitung-<produkt-slug>/content.json`. Die Verarbeitungsanleitung
ist ein eigenständiges, **produktbezogenes** Dokument für Pro Line wie Home
Line. Sie ersetzt weder das technische Datenblatt noch das
Sicherheitsdatenblatt; beide bleiben die verbindliche Quelle.

## Herkunft dieses Vertrags

Struktur und Rubrikenfolge sind an sieben freigegebenen Anleitungen
abgelesen, nicht entworfen: HZ 250 Pro, HZC Creme, SP Express, RD
ReparaturDicht, Novusan, NovuSticks, NovuProtect. Alle sieben tragen
dieselbe Folge, unabhängig von Produkt und Linie.

## Aufbau

| Blatt | Inhalt |
|---|---|
| 1 | Titelblatt. Eigenes Dokument (`scripts/build_cover.py`, Variante `anleitung`), zählt aber mit. |
| 2 | Rubriken **Vorteile** und **Vorbereitung**: Anwendungsbereich, Vorteile, Arbeitsplatz, Werkzeug, Sicherheit. |
| 3 … n−1 | Rubrik **Anleitung**. Ein bis vier Seiten, je nach Umfang. Die letzte trägt den Profi-Tipp. |
| n | Rubrik **Nacharbeit** mit Impressum und Ausgabedatum. |

Der Seitentyp im Content heißt `vorbereitung`, `anleitung` oder
`nacharbeit`. Andere Werte werden nicht gesetzt.

## Seitenzählung

Anders als die Broschüre: **das Titelblatt zählt mit.** Die sieben
freigegebenen Fassungen tragen auf dem zweiten Blatt `2/5` beziehungsweise
`2/4`. Darum gilt im Content

```
"page_number_start": 2,
"page_total": 1 + Anzahl der Innenseiten
```

`check_paginierung()` in `scripts/build_anleitung.py` prüft beides. Steht
dort eine Zahl, die nicht zum Umfang passt, sieht die Fußzeile heil aus und
nennt nur den falschen Nenner — deshalb wird gerechnet, nicht geglaubt.

## Satzspiegel

| | Wert | Quelle |
|---|---|---|
| Achse | 18 mm | `grid.axis_mm`, markenweit, nicht verhandelbar |
| Kopfsteg | 18 mm | dieses Dokument |
| Fußsteg | 20 mm | dieses Dokument |
| Satzbreite | 174 mm | `grid.interior.text_width_mm` |
| Spalten | 2 × 84,7 mm, Steg 4,6 mm | gerechnet: (174 − 4,6) / 2 |

Kopf- und Fußsteg weichen bewusst von `grid.interior` ab. 26,7 und 23,5 mm
sind Broschürenmaße; sie existieren dort, weil Kolumnentitel und Folio in
den Steg laufen. Ein technisches Dokument hat beides nicht. Das Datenblatt,
der nächste Verwandte, setzt aus demselben Grund von 6,0 bis 291,4 mm
(gemessen an `output/tds-hz250pro.pdf`); die freigegebenen Anleitungen
laufen von 12,6 bis 290,2 mm. Ohne diese Abweichung bräuchte dieselbe
Anleitung eine Seite mehr.

Der zweispaltige Satz ist keine Gestaltungsidee, sondern abgelesen: die
Vorlagen setzen den Text in einer 86-mm-Spalte und stellen Abbildungen
rechts daneben. Über die volle Satzbreite gelaufen ergäben sich bei 9 pt
mehr als 110 Zeichen je Zeile; lesbar sind 45 bis 75.

## Icons und Radius

Beides kommt aus `brand.json`, nicht aus dieser Vorlage.

**Radius** `radius.value_px` = 5, auf jeder Fläche, die nicht randabfallend
ist. Randabfallende Flächen bleiben kantig — ein Radius an der Blattkante
wird beim Beschnitt abgeschnitten und wirkt wie ein Fehler. Der Innenteil
setzte bis 31.08.2026 überall eckig; das war ein Übertragungsfehler, keine
Entscheidung.

**Icons** Phosphor Bold aus `templates/anleitung/icons/`, Glyph immer Lime
Green. Der Kasten hängt am Absender: Die Verarbeitungsanleitung ist ein
Dokument der AG, also Deep Green auf hellem Grund (`sender_context.ag`).
Auf dunklem Grund — im Profi-Tipp — trägt der Kasten Transition Green,
damit Deep nicht auf Deep steht. Der Glyph bleibt Lime; das ist eine Regel,
kein Sonderfall.

| Stelle | Größe | Quelle |
|---|---|---|
| Rubrik | Kasten 12 mm, Glyph 7,5 mm | `icons.sizes_mm.category_opener` |
| Abschnitt, Kasten | Kasten 9,5 mm, Glyph 6 mm | `icons.sizes_mm.inline` |

Die Dateien werden **inline eingebettet**, nicht als `<img>`: WeasyPrint
wendet das Dokument-Stylesheet nicht auf SVG-Kinder an, und ohne Füllung am
`svg`-Element druckt der Glyph schwarz. Jede Datei trägt sie selbst, gesetzt
von `scripts/prepare_brochure_icons.py`. Ein Icon-Webfont kommt nicht in
Frage — über Font-Klassen wäre die Strichstärke frei wählbar.

Das Motiv steht im Content als `icon` neben dem Titel, ohne Pfad und ohne
Endung. Das Template bindet es mit `ignore missing` ein — ein Tippfehler
ließe den Kasten still leer, deshalb prüft `check_bildverweise()`, ob die
Datei existiert.

## Bewusste Abweichungen von den Bestandsfassungen

Die sieben PDFs stammen aus der Zeit vor dem Markensystem. Übernommen wurde
die Struktur, nicht das Erscheinungsbild:

| | Bestandsfassung | hier |
|---|---|---|
| Rubrikfarbe | `#054f42` | Deep Green `#1c4b42` |
| Profi-Tipp | `#afca13` | Lime Green `#b4e717` |
| Titel-Headline | `#484848` | Stone Grey `#494949` |
| Schriftschnitt | Unbounded SemiBold | nur Black, siehe `typography.display` |
| Fremdschrift | Myriad Pro (4 Stellen) | keine |
| Achse | 15,0 mm | 18 mm |

## Was geprüft wird

`scripts/build_anleitung.py` liest das **Ergebnis**, nicht die Vorlage:

- **Schriften.** Fehlt eine Schriftdatei, ersetzt WeasyPrint sie still.
- **Vollständigkeit, ab 3 Zeichen.** Nicht ab 40 wie in der Broschüre: die
  kürzesten Einträge sind die Sicherheitsangaben. Mit der Voreinstellung
  fiel die komplette PSA-Liste vom Blatt, ohne dass etwas gemeldet wurde.
- **Seitenzahl.** Jeder Eintrag in `pages[]` ergibt genau eine Seite.
- **Bildverweise.** Am Dateisystem, nicht per Textsuche.
- **Paginierung.** `page_total` gegen den Umfang.
- **Offene Angaben.** `[ANGABE FEHLT: …]` und `[ZU PRÜFEN: …]` sind im
  Entwurf zulässig und blockieren `--release`.

## Fehlende Motive

Ein fehlendes Bild wird **nicht weggelassen**, sondern als gestreifte
Fläche mit Beschriftung gesetzt (`image_needed`). Ein toter Bildverweis
führt sonst dazu, dass WeasyPrint den Alt-Text in einer Serifenschrift an
die Stelle setzt — auf einer Anleitung fällt das erst im Druck auf.

## Neue Anleitung anlegen

```bash
cp -R content/anleitung-hz250pro content/anleitung-neues-produkt
# Werte gegen das Datenblatt des Produkts prüfen, nicht abschreiben.
python3 scripts/build_anleitung.py content/anleitung-neues-produkt/content.json
```

Der Umbruch ist Handarbeit: Jede Seite in `pages[]` muss ihren Inhalt
fassen. Läuft eine über, meldet der Bau es — dann wandert der letzte
Abschnitt eine Seite weiter. Seite 2 der HZ-250-Fassung hat nur noch
1,1 mm Luft; wächst dort etwas, klemmt sie.
