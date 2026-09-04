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
