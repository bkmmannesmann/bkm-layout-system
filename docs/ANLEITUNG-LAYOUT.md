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
| 1 | Titelblatt. Gebaut über `templates/cover/`, Variante `anleitung`, und im selben PDF. |
| 2 | Rubriken **Vorteile** und **Vorbereitung**: Anwendungsbereich, Vorteile, Arbeitsplatz, Werkzeug, Sicherheit. |
| 3 … n−1 | Rubrik **Anleitung**. Ein bis vier Seiten, je nach Umfang. Die letzte trägt den Profi-Tipp. |
| n | Rubrik **Nacharbeit** mit Impressum und Ausgabedatum. |

Der Seitentyp im Content heißt `vorbereitung`, `anleitung` oder
`nacharbeit`. Andere Werte werden nicht gesetzt.

## Satz über die volle Breite

Zwei Dinge laufen über die ganze Satzbreite, nicht in einer Spalte:

- **Die Vorteile**, direkt unter ihrer Rubrik. Sie sind die Aussage der
  Seite, und eine Aussage steht nicht am Rand.
- **Die nummerierten Handlungsschritte** — Arbeitsplatz vorbereiten wie
  Abschluss und Reinigung. Beide Listen folgen derselben Form.

Zweispaltig bleiben nur die Stellen, an denen zwei Dinge nebeneinander
gehören: geeignete gegen nicht geeignete Untergründe, Werkzeug gegen
Sicherheit, Text gegen Abbildung.

## Titelblatt

Das Titelblatt liegt im selben PDF wie der Innenteil — so wie in allen
sieben freigegebenen Fassungen. Es entsteht trotzdem nicht in
`templates/anleitung/`, sondern über den Cover-Bauweg: Dieselbe Vorlage
trägt die Titel der Broschüren, und zwei Wege zu derselben Seite laufen
auseinander. Belegt am Titelfoto, das monatelang auf beiden Wegen einen
anderen Ausschnitt zeigte.

Der Wortlaut kommt aus dem `cover`-Block der Anleitung, nicht aus den
Vorgaben in `build_cover.py`: Die stehen dort produktneutral („Schritt für
Schritt zum Ergebnis"), die freigegebenen Anleitungen nennen auf dem Titel
ihr Produkt.

```json
"cover": {
  "headline":    "VERARBEITUNGS-<br>ANLEITUNG",
  "subheadline": "Zur Injektion in mineralisches Mauerwerk …",
  "intro_text":  "BKM HZ 250 Pro – Dauerhafte Kapillarsperre …"
}
```

Fehlt der Block, entsteht nur der Innenteil, und der Bau sagt das.

**Die Subheadline läuft höchstens zwei Zeilen** (`type_scale.cover.
subheadline.max_lines`). Wird die Grenze gerissen, ist der Text zu kürzen —
nicht die Spalte zu verbreitern und nicht die Größe zu senken. Gemessen
liegt die Grenze bei rund 70 Zeichen: 68 passen, 82 nicht.
`check_subheadline()` in `scripts/build_cover.py` misst es am fertigen PDF
und blockiert den Zusammenbau, wenn es reißt.

**Farben auf dem Titelblatt der Anleitung.** Logo, Headline und Fließtext
stehen in Deep Green, nicht in Stone Grey: Die Anleitung ist ein Dokument
der AG, und deren Farbe auf hellem Grund ist Deep Green
(`sender_context.ag.text_on_light`). Das Logo ist
`bkm-logo-deepgreen-puregreen.svg` — dieselbe Kombination wie im
technischen Datenblatt, an dessen Pixeln geprüft: `#1c4b42` und `#4daf46`.
Die Datei ist bis auf die elf Farbwerte identisch mit der Stone-Grey-
Fassung; Pfadgeometrie und viewBox sind unverändert.

`logos.on_light` in `brand.json` zeigt weiter auf die Stone-Grey-Fassung.
Sie steht an acht Stellen im Canvas. Ob die ebenfalls wechseln, ist offen.

Die Subheadline bleibt Pure Green — benannte Kontrastausnahme mit 2,79,
siehe `contrast.accepted_exceptions.pure-green_on_white`.

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

**Die Rubriken tragen kein Icon.** Vorteile, Vorbereitung, Anleitung und
Nacharbeit tragen ihr Gewicht über Größe und Farbe. Alles darunter trägt
eines.

| Stelle | Größe | Quelle |
|---|---|---|
| Vorteil | Kasten 9,5 mm, Glyph 6 mm | `icons.sizes_mm.inline` |
| Subheadline, Kasten, Labelzeile, Profi-Tipp | Kasten 6,5 mm, Glyph 3,8 mm | `icons.sizes_mm.contact` |

Beim Vorteil steht der Kasten **neben beiden Zeilen** und trifft ihre Höhe:
Behauptung 9,5 pt auf 1,35 und Begründung 8,5 pt auf 1,4 ergeben zusammen
rund 9,5 mm — genau das Maß der Stufe `inline`.

## Aufzählungen

Der Punkt steht in **Deep Green** — dieselbe Farbe wie die Icon-Kästen auf
hellem Grund, nicht Transition Green. Auf dunkler Fläche wechselt er auf
Lime Green, sonst stünde Deep auf Deep. Heute trägt kein dunkler Kasten
eine Punktliste; die Regel hält den Fall ab, sobald einer eine bekommt.

Der gesetzte Punkt trägt nur dort, wo eine Liste als Aufzählung gelesen
werden muss. In den Untergrundlisten sowie in Werkzeug und Sicherheit ist
er weggelassen (`anl-bullets--nackt`): die Zeilen sind kurz und stehen
ohnehin untereinander. Angekündigt wird die Liste stattdessen über eine
Labelzeile mit Icon — `check-circle` vor *Geeignet für*, `warning` vor
*Nicht geeignet für*.

**Handlungsschritte tragen weder Ziffer noch Punkt.** Die Reihenfolge steht
im Text — „Lege zuerst fest", „Trage vor dem Aufbringen auf" —, und eine
zweite Ordnung daneben trägt nichts. Gilt für *Arbeitsplatz vorbereiten*
wie für *Abschluss und Reinigung*.

## Typografische Stufen

Verbindlich in `brand.json` unter `type_scale.anleitung`. Nur Unbounded ist
dort abschließend geregelt — die Brotschrift trägt zu viele berechtigte
Abstufungen, die Auszeichnungsschrift nicht.

| Stufe | Größe |
|---|---|
| Rubrik | 18 pt |
| Subheadline | 10 pt |
| Profi-Tipp | 9,5 pt |
| Kastentitel | 9 pt |

`check_typoskala()` misst das am fertigen PDF nach. Jede andere Größe in
Unbounded ist im Innenteil ein Fehler. Das Titelblatt bleibt außen vor;
dafür gilt `type_scale.cover`.

## Aufbau der Vorbereitungsseite

Von oben nach unten — erst wofür, dann wie, dann womit:

1. Rubrik **Vorteile**, darunter die Vorteile über die volle Satzbreite.
   **Das ist eine Entscheidung, keine Ablesung.** In allen sieben Vorlagen
   steht der Anwendungsbereich links oben und wird zuerst gelesen, die
   Rubrik VORTEILE sitzt darunter. Wir drehen das: Der Prüfbericht vom
   31.08.2026 hat die Stelle zu Recht beanstandet, weil hier bis dahin
   „abgelesen" stand, während die Herleitung dieses Vertrags sonst
   ausdrücklich Ablesung ist. Entscheidung des Markeninhabers, die Folge
   beizubehalten.
2. Absatz — die beiden Rubriken sind zwei Kapitel auf einem Blatt, nicht
   zwei Überschriften hintereinander.
3. Rubrik **Vorbereitung**.
4. **Anwendungsbereich** über die ganze Breite, darunter *Geeignet für*
   links und *Nicht geeignet für* rechts. **Fehlt die Ausschlussliste,
   läuft die Eignungsliste über die volle Breite**, zweispaltig gesetzt.
   SP Express führt keine — vorher stand die rechte Hälfte leer und riss
   ein Loch von rund 85 mm in die Seite.
5. **Arbeitsplatz vorbereiten** über die ganze Breite.
6. **Für die Anwendung brauchst du** links, **Für deine eigene Sicherheit**
   rechts.

Der Sicherheitskasten steht auf der benannten Fläche `deep` aus
`brand.json`: Grund Deep Green, Text Clean White, Titel Lime Green. Nicht
selbst zusammengestellt — der Name legt alle Werte gemeinsam fest, damit
keine Kombination entsteht, die im Druck nicht trägt. Der Icon-Kasten
wechselt darauf auf Transition Green, sonst stünde Deep auf Deep; der Glyph
bleibt Lime.

## Blocksatz nur im Fließtext

`design-system/base.css` setzt `text-align: justify` und `hyphens: auto`
für das ganze Dokument. Für den Fließtext ist das richtig. Jede kurze Zeile
in einer 84,7-mm-Spalte wird dadurch aber auseinandergezogen und getrennt —
aus *FÜR DEINE EIGENE SICHERHEIT* wurde ein gestreckter Zweizeiler mit
*SICHER-HEIT*.

Überschriften, Labelzeilen, Bildunterschriften, Tabellenköpfe und
Listeneinträge stehen deshalb linksbündig und ungetrennt. Die gemeinsame
Datei bleibt unberührt: Datenblatt und Broschüre hängen daran.

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

## Tabellen

Abschnitte dürfen eine echte Tabelle führen (`table` mit `columns`, `rows`
und optionaler `note`). Die Vorlagen stellen Verbrauchsangaben zweispaltig
gegenüber; bei NovuSticks wird daraus auf einen Blick sichtbar, dass ein
Stick auf rund 3 cm Mauerwerk kommt. Als vier Sätze untereinander geht das
verloren. Der Datenvertrag kannte bis 31.08.2026 nur `bullets` und
`formulas` — das war die Lücke dahinter, benannt im Prüfbericht.

Das Icon dafür ist `table`, nicht `drop`: Ein Tropfen über einer
Stückzahltabelle behauptet etwas Falsches über das Produkt. `drop` bleibt
den flüssigen Produkten vorbehalten.

## Umbruch in Überschriften

`text-wrap: pretty` kennt WeasyPrint 69 nicht — am gebauten PDF geprüft,
es bewirkt nichts. Zweiwort-Umbrüche wie *VERBRAUCH / PLANEN* sind
richtig und bleiben. Der eine schlechte Fall war *FÜR DIE ANWENDUNG
BRAUCHST / DU*, ein Zweibuchstaben-Rest auf eigener Zeile. Er ist im
Content gelöst: Ein geschütztes Leerzeichen (U+00A0) bindet die letzten
beiden Wörter. Das ist keine Änderung am freigegebenen Wortlaut, sondern
eine Bindung.

## Bildformat

Alle Abbildungen und Platzhalter stehen im Format **16:9**. Die Höhe wird
aus der Spaltenbreite gerechnet, nicht gesetzt — in der 84,7-mm-Spalte sind
das 47,64 mm:

```css
--anl-col2:  calc((var(--anl-width) - var(--anl-gutter)) / 2);
--anl-fig-h: calc(var(--anl-col2) * 9 / 16);
```

`aspect-ratio` wäre der richtige Weg, aber **WeasyPrint 69 kennt die
Eigenschaft nicht** — das Element wird damit gar nicht gezeichnet, am
31.08.2026 nachgemessen. `padding-top` in Prozent löst dort nicht gegen die
Breite auf. Bleibt `calc`. Eine gesetzte Höhe wäre die zweite Zahl neben
der Breite, und zwei Zahlen laufen auseinander.

Höchstens **vier Abbildungen je Seite**: 47,64 mm Bild plus rund 4 mm
Unterschrift und 5 mm Abstand ergeben 56,6 mm; bei 245 mm nutzbarer
Spaltenhöhe passen vier. `check_abbildungen()` meldet die fünfte.

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

## Canvasfassung

`scripts/build_anleitung_canvas.py` erzeugt aus derselben `content.json`
die Fassung für Claude Design: `templates/brochure/I-Anleitung.dc.html`.

Sie enthält **nur die A4-Blätter** — keine Gruppen-Navigation, keinen
Kopfblock, keine Labelleiste. Die acht Vorlagengruppen A bis H tragen das
zu Recht, weil aus ihnen ausgewählt wird; die Anleitung ist ein Dokument
und wird als Blattfolge gelesen, nicht als Sammlung durchgesehen. Links
auf die anderen Gruppen wären darin tote Fracht, und der Kopfblock war
Text über die Datei, nicht Inhalt der Anleitung.

Jedes Blatt trägt seine Kennung als `id` und seinen Namen als
`data-screen-label` — anspringbar und in Kommentaren benannt, ohne dass
etwas davon auf dem Blatt steht.

### Was der Bau prüft

Canvas und Produktion sind zwei Wege zu demselben Blatt, und die laufen
auseinander. Viermal ist es passiert: Hero-Grafik, Fotolage, Keyvisual,
und zuletzt das Titelblatt, dem `cover-spec.css` fehlte. Deshalb prüft
der Bau selbst und bricht ab, wenn etwas nicht stimmt:

| Prüfung | worauf sie sieht |
|---|---|
| `check_chrome` | keine Gruppenlinks, kein `<h1>` außerhalb der Blätter, keine Labelleiste, Blattzahl, eindeutige Kennungen |
| `check_seitenrahmen` | `html, body` auf Blattmaß darf aus `cover-spec.css` nicht durchkommen — das reißt die Arbeitsfläche auseinander |
| `check_fotolage` | Titelfoto gegen `cover_geometry.photo` aus `brand.json`, und ob die Regel auch **zuletzt** steht; dazu die Variantenklasse am Wrapper |
| `check_schriftangebot` | welche Schnitte der Canvas zur Auswahl stellt, gegen `typography` — meldet nur, bricht nicht ab |

Gemessen wird gegen `brand.json`, nicht gegen die CSS: sonst prüft die
Vorgabe sich selbst.

Dass die Prüfungen auch greifen, steht in `scripts/gegenproben_canvas.py`
— elf Fälle, jeder mit einem echten Fehler vorgesetzt:

```bash
python3 scripts/gegenproben_canvas.py
```

**Offen:** Der Canvas bietet TT Norms Pro in 300, 500 und 600 an, obwohl
`brand.json` nur 400 und 700 zulässt. Die Schnitte stehen in
`design-system/base.css` und ihre Dateien liegen im Repository, sie sind
also wählbar — genau so ist Unbounded SemiBold in die Bestandsanleitungen
geraten. `BKM PDF Sans` ist davon ausgenommen: das ist die eingebettete
Druckfassung nach `AGENTS.md`, Regel 11.
