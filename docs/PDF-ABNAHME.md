# PDF-Abnahme

`scripts/pruefe_pdf.py` prüft ein fertiges PDF gegen den Layoutvertrag —
**gleich, wer es gebaut hat.**

```bash
python3 scripts/pruefe_pdf.py broschuere.pdf
python3 scripts/pruefe_pdf.py anleitung.pdf --art anleitung
python3 scripts/pruefe_pdf.py broschuere.pdf --fuellgrad
```

Sie ändert nichts. Sie misst und meldet. Exit 1, wenn etwas zu
beanstanden ist.

## Warum es sie gibt

Der Bau im Repo prüft, was er selbst erzeugt. Der Weg über Claude Design
geht daran vorbei. Am 03.09.2026 kam eine 51-seitige Broschüre zurück, in
der

- die Blattbeschriftung des Canvas mitgedruckt war („U2" oben rechts),
- neun Seiten Text unter dem Fußsteg trugen, drei davon bis in den
  Beschnitt — auf einer Seite bis 299,9 mm auf einem 297-mm-Blatt,
- und nach der Korrekturrunde Wörter mitten durchbrachen:
  „Technologi/emarke", „Partnernet/zwerk".

**Jeder dieser Fehler wäre im Repo-Bau gemeldet worden.** Er lief nur
nicht. Diese Prüfung schließt die Lücke: Design exportiert, das PDF geht
hier durch, und die Liste steht, bevor jemand das Dokument ansieht.

## Was geprüft wird

| Prüfung | worauf sie sieht |
|---|---|
| Blattbeschriftung | `U2`–`U4`, `Artboard n`, `Screen n`, `Frame n` — Canvas-Gerüst im Druck |
| Blattkante | Text jenseits von 297 mm; wird beschnitten |
| Satzspiegel | Kopfsteg, Fußsteg, rechte Fluchtlinie |
| Wortbrüche | Wörter, die ohne Trennstrich mitten durchbrechen |
| Schriften | Fremdschriften und Type 3 |
| Blattformat | DIN A4 |

## Drei Entscheidungen, die man kennen muss

**Die Toleranz rechts ist 1,0 mm, und das ist gemessen.** Der Blockrahmen
der Textextraktion umfasst den Vorschub des letzten Glyphen, nicht seine
Schwärze. Nachgemessen an einer Anleitung: die Extraktion meldete
192,80 mm, die rechteste dunkle Bildspalte lag bei **191,96 mm** — genau
auf der Fluchtlinie. Über alle acht Anleitungen war der größte solche
Überhang 0,90 mm. Ab 1,0 mm steht wirklich Tinte im Rand.

**Am Kopfsteg sind es 1,5 mm**, aus einem anderen Grund: der Blockrahmen
umfasst die ganze Zeilenbox, nicht die Grundlinie. Eine Unbounded-Rubrik,
die vertragsgemäß bei 18 mm beginnt, misst 17,4 mm.

**Beiwerk wird von Fließtext unterschieden.** Ein PDF allein sagt nicht,
was Folio ist und was ein Absatz. Unterschieden wird daran, dass Beiwerk
sich wiederholt: was auf drei oder mehr Seiten an derselben Höhe steht,
gilt als Fußzeile und wird einmal zusammengefasst. Das Impressum wird an
seinem Inhalt erkannt — „Copyright", „Ausgegeben am" — nicht an seiner
Position, denn seit dem Prüfprotokoll ist die Impressumsseite nicht mehr
die letzte.

Beides erscheint als **Hinweis**, nicht als Beanstandung. Sonst meldet
jedes eigene Dokument dauerhaft einen Fehler, den niemand beheben will,
und die Meldung verliert ihre Kraft.

## Dass die Prüfungen greifen

```bash
python3 scripts/gegenproben_pdf.py
```

Zwölf Fälle, jeder mit einem präparierten PDF: die Fehler, die wirklich
im Dokument standen, plus die Gegenprobe, dass ein gewöhnlicher Umbruch
**kein** Wortbruch ist und das Impressum im Fußsteg **keine**
Beanstandung.

Eine dieser Gegenproben hat einen Fehler in der Prüfung selbst
aufgedeckt: bei einem Einzelblatt ist die letzte Seite auch die erste,
und die damalige Positionsregel erklärte jeden Absatz im Fußsteg zum
Impressum.

## Stand

Alle acht Verarbeitungsanleitungen laufen mit **null Beanstandungen**
durch. Was die Prüfung meldet, ist dann auch etwas.


## Drei Satzspiegel, drei Prüfarten

```bash
python3 scripts/pruefe_pdf.py datei.pdf                      # Druckweg
python3 scripts/pruefe_pdf.py datei.pdf --art innenteil      # Canvas-Innenteil
python3 scripts/pruefe_pdf.py datei.pdf --art anleitung      # Anleitung
```

| Art | Satzspiegel senkrecht | wer baut so |
|:---|:---|:---|
| `broschuere` | 26,7 bis 273,5 mm | `scripts/build_pages.py`, Seitenzahl unten |
| `innenteil` | 18,0 bis 276,0 mm | Canvas-Vorlagen, Beiwerk unten bei 284,6 mm |
| `anleitung` | 18,0 bis 277,0 mm | `scripts/build_anleitung.py` |

Die falsche Art zu wählen, meldet jede korrekt gesetzte Seite als Fehler.
An den vier umgebauten Innenseiten waren es sieben Beanstandungen gegen
`broschuere` und eine gegen `innenteil` — und diese eine kam aus dem
Design-Export, nicht aus dem Satz.

**Schriftnamen werden ohne Trennzeichen verglichen.** Ein Erzeuger bettet
`TT-Norms-Pro-Bold` ein, ein anderer `TT Norms Pro Bold`. Die Klarform mit
Leerzeichen wurde als Fremdschrift gemeldet, obwohl es die Hausschrift ist.

## Der zweite Riegel: der Feldabgleich

Die PDF-Abnahme greift am Ende. Davor steht seit dem 03.09.2026 eine
zweite Prüfung, die früher greift: **jedes Feld im Content muss vom
Template auch gesetzt werden.**

```bash
python3 scripts/validate_brochure.py content/<name>/content.json
python3 scripts/validate_anleitung.py content/<name>/content.json
python3 scripts/gegenproben_felder.py
```

Beide Prüfer lesen dafür ihr eigenes Template und ziehen heraus, welches
Feld welcher Seitentyp liest. Ein Feld, das dort nicht vorkommt, ist tot
— der Inhalt fällt weg, ohne dass irgendetwas meldet.

Der Anlass: fünfzehn `list`-Seiten führten ihre Einträge unter `items`
und ihre Überschrift unter `headline_section`. Der Seitentyp liest
`entries` und `headline`. Die Seiten kamen fast leer heraus.

Der Abgleich hat sofort einen zweiten Fall gefunden, älter und in allen
acht Verarbeitungsanleitungen: `icon` stand auf jeder Nacharbeitsseite im
Content und im Datenvertrag und wurde nie gesetzt — die Nacharbeitsseite
war die einzige, deren Überschrift ohne Icon blieb. Jetzt trägt sie
eines, wie jede andere Abschnittsüberschrift auch.

**Warum nicht über das JSON-Schema?** `docs/anleitung-content.schema.json`
verbietet fremde Felder über `additionalProperties: false` — an achtzehn
Stellen. Das Paket `jsonschema` liegt nicht im Bestand, der Datenvertrag
wird von Hand geprüft, und diese eine Regel war dabei nie umgesetzt. Der
Feldabgleich holt sie nach, und zwar gegen das Template statt gegen das
Schema: das Template ist die Wahrheit darüber, was gesetzt wird.


## Der dritte Riegel: die Wortlänge

Ein Wort, das breiter ist als seine Spalte, ist ein Fehler in zwei
Gestalten. Mit `overflow-wrap: break-word` wird es mitten durchgehackt —
so entstanden `Technologi/emarke` und `Partnernet/zwerk`. Ohne diese
Regel steht es über die Spaltenkante hinaus. Beides sieht man erst im
fertigen PDF.

```bash
python3 scripts/pruefe_wortlaenge.py <datei.html> [--basis <ordner>]
python3 scripts/gegenproben_wortlaenge.py
```

Die Bauwege rufen die Prüfung selbst auf. `scripts/build_pages.py` und
`scripts/build_anleitung.py` legen den Satz ohnehin aus, bevor sie
schreiben — sie reichen das ausgelegte Dokument herein, statt es ein
zweites Mal auszulegen. Ein zu langes Wort steht dann unter den
Beanstandungen des Baus, bevor jemand das PDF öffnet.

**Gemessen, nicht geschätzt.** Jedes Wort wird mit seinem eigenen Stil
noch einmal ausgelegt — Schrift, Schnitt, Größe, Laufweite — und die
Breite geht gegen die Innenbreite seines Kastens. Zeichenzahl mal
Durchschnittsbreite wäre geraten; das `W` ist in TT Norms Pro dreimal so
breit wie das `i`.

**Zwei Dinge sind ausdrücklich kein Fehler.** Unter `hyphens: auto` darf
das Wort brechen; gemessen wird dann nicht das ganze Wort, sondern seine
längste Silbe. Und ein Bindestrichwort zerfällt in seine Teile, die
einzeln gemessen werden. Ohne diese Unterscheidung wäre jeder deutsche
Fließtext voller Falschmeldungen — und eine Prüfung, die immer
anschlägt, sieht sich nach kurzer Zeit niemand mehr an.

**Eine Fallgrube, die zwei Anläufe gekostet hat:** WeasyPrint wirft das
weiche Trennzeichen U+00AD beim Auslegen weg. Im Boxbaum steht
`Technologiemarke`, nicht `Technologie­marke` — die vom Setzer von Hand
gesetzte Bruchstelle ist unsichtbar. Ohne Gegenmaßnahme hätte die Prüfung
ausgerechnet das Wort angemahnt, an dem der Fehler schon behoben war,
und der in ihrem eigenen Hinweistext empfohlene Weg hätte nicht
funktioniert. Die Prüfung liest die weichen Trennzeichen deshalb aus der
Quelle nach.

**Wo sie nichts findet, und warum das richtig ist:** eine Tabellenspalte
ohne feste Breite wächst mit ihrem Inhalt. Dort entsteht kein Wortbruch,
sondern eine zu breite Tabelle — ein anderer Fehler, den die Blattkante
oben findet. Diese Prüfung greift, wo die Breite feststeht, und das ist
im Satzspiegel die Regel.


## Der vierte Riegel: Löcher im Blocksatz

Blocksatz dehnt den Wortzwischenraum, bis die Zeile die Spalte füllt.
Passt das nächste Wort nicht mehr und lässt es sich nicht trennen, reißt
die Zeile auf. Am 07.09.2026 nachgemessen — 1759 Zeilen aus drei
Broschüren und drei Verarbeitungsanleitungen, jede Lücke gegen die
**0,7303 mm**, die TT Norms Pro bei 9 pt für das Leerzeichen vorsieht:

| Zeichen je Zeile | Wortabstand im Mittel | über 1,33× | über 2,0× |
|---:|---:|---:|---:|
| 30–34 | 1,51× | 59 % | 24 % |
| 35–39 | 1,28× | 43 % | 3 % |
| 40–44 | 1,00× | 6 % | 1 % |
| ab 45 | 1,00× | unter 10 % | unter 2 % |

**Der Bruch liegt bei vierzig Zeichen.** Die dreispaltige Anlage trägt
bei 55,4 mm und 9 pt sechsunddreißig — knapp darunter. Deshalb standen in
der Broschüre vom 03.09.2026 vierzig Prozent aller Zeilen über der
Setzergrenze und acht Prozent über dem Doppelten. Die
Verarbeitungsanleitungen mit 76 und 85 mm liegen im selben Repository bei
1,00×; es lag nicht am Text.

**Kein Schalter hilft dagegen.** Getrennt wird bereits am Anschlag —
dreiundzwanzig Prozent der Zeilen endeten mit Trennstrich.
`hyphenate-limit-zone` von 0 bis 20 %, `hyphenate-limit-chars` von 4 2 2
bis 5 3 3, kleinere Laufweite, engerer Grundwortabstand: alles gemessen,
alles unter einem Prozentpunkt Wirkung, und die strengere Trennregel
machte es schlechter. Pango bricht gierig um; es nutzt eine Trennstelle
nur, wenn das Wort sonst gar nicht passt, nicht um eine Lücke zu
verkleinern.

**Also: Blocksatz behält, wer ihn tragen kann.** Die vier Spaltenklassen,
die 55 mm erzeugen, laufen linksbündig; alles ab 85 mm bleibt Blocksatz —
und das ist der größere Teil jeder Seite. Die Regel steht mit ihrer
Begründung in `templates/pages/pages-spec.css`.

Was das gebracht hat, an denselben drei Broschüren gemessen:

| | Wortabstand im Mittel | über 1,33× | Löcher |
|:---|---:|---:|---:|
| vorher | 1,20–1,33× | 36–49 % | 7–10 % |
| nachher | 1,00× | 4–7 % | 0–1 Zeile |

```bash
python3 scripts/pruefe_pdf.py <datei.pdf>
python3 scripts/gegenproben_wortabstand.py
```

Die Meldung nennt die Seite, den Faktor, die Spaltenbreite und **das Wort
am Anfang der nächsten Zeile** — das ist das, was nicht mehr gepasst hat.
Ein weiches Trennzeichen U+00AD darin schließt die Lücke meistens.

**Warum es wirkt, ist nicht das, was man zuerst denkt.** Die erste
Vermutung war: die erste Silbe des Wortes rutscht in die Lücke. Gemessen
stimmt das so gut wie nie — genau dann hätte Pango nämlich von sich aus
getrennt. Es wirkt, weil es den Umbruch der ganzen Zeile verschiebt. Das
Ergebnis ist deshalb nicht vorherzusagen: setzen, neu bauen, nachmessen.
In der 49-seitigen Broschüre haben so gesetzte 37 Trennzeichen elf Löcher
auf eines gebracht — in drei Runden, weil jede Runde den Fluss verschob.

Gemeldet wird ab dem Doppelten, und zwar **unter den Hinweisen**: ein
Loch ist hässlich, aber es bricht keine Zusage — anders als Text über der
Blattkante oder eine fehlende Schrift. Der Rückgabewert bleibt davon
unberührt. Das Auffällige unter 2,0× steht nur in der Kennzahl; alles ab
1,33× einzeln zu melden hieße, vierzig Prozent einer Broschüre zu melden,
und eine Prüfung, die das tut, liest niemand zu Ende.

**Gemessen wird nur die Broschüre.** Das Thema ist an der dreispaltigen
Anlage des Innenteils entstanden — 55 mm, sechsunddreißig Zeichen je
Zeile. Verarbeitungsanleitungen und Datenblätter setzen ihren Text 76 bis
114 mm breit und liegen bei 1,00×; dort ist nichts zu holen. Vier
Randbefunde über acht Anleitungen — Novusan S3, RD S4, SH-1K S3 zweimal —
würden nur den Bericht zustellen. Sie stehen alle als vorletzte Zeile
eines kurzen Absatzes, und ein weiches Trennzeichen hat dort den Satz an
der rechten Fluchtlinie aufgerissen statt die Lücke zu schließen; die
Texte sind ohnehin wortgetreue Transkriptionen freigegebener Anleitungen
und werden nicht angefasst.

Wer trotzdem nachsehen will:

```bash
python3 scripts/pruefe_pdf.py anleitung.pdf --art anleitung --blocksatz
```

### Ein weiches Trennzeichen ist nicht folgenlos

Beim Schließen der letzten Lücken kam ein zweiter Fund heraus. Ein
einziges U+00AD im Fließtext einer `feature`-Seite hat den Textkasten von
174 auf **599 mm** aufgeblasen; der Satz stand zwanzig Millimeter über
dem Blattrand. Ursache war nicht das Zeichen, sondern ein Flexelement
ohne `min-width: 0` — es rechnete seine Mindestbreite aus dem Inhalt.
Das konnte jederzeit auch ohne Zutun geschehen, denn `hyphens: auto` gilt
dort ohnehin. Behoben in `.feature-split__body`; gefunden hat es die
Ausgabeprüfung des Baus, nicht das Auge.

Zwei Dinge folgen daraus. Ein Trennzeichen gehört **nur in
Fließtextfelder** — nicht in Überschriften, Verzeichniseinträge oder
Pfade; ein globaler Textersatz über die ganze `content.json` trifft sie
alle und war der erste Fehlversuch. Und nach jedem gesetzten Trennzeichen
läuft der Bau samt Ausgabeprüfung, weil jede Satzkorrektur den Umbruch
verschiebt und anderswo eine neue Lücke aufmachen kann.
