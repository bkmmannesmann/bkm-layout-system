# KI-Kennzeichnung

Ein KI-generiertes Motiv trägt den Vermerk **„AI GENERATED"** im Bild selbst.
Nicht als Bildunterschrift, nicht als Zeile im Layout, nicht als Sammelangabe im
Impressum — im Motiv. So verlangt es die EU-KI-Verordnung, und so überlebt der
Vermerk auch dann, wenn das Bild weiterverwendet, zugeschnitten oder aus dem
Dokument gelöst wird.

Eine Sammelangabe im Impressum ist zusätzlich zulässig. Sie ersetzt den Vermerk
am Bild nicht.

## Die Marke

`assets/kennzeichnung/bkm-ai-generated.svg`

Eine Sperrmarke: BKM-Wortmarke, darunter die Zeile „AI GENERATED", rechts die
Signetstriche. Sie wird als Ganzes gesetzt und nicht auseinandergenommen — die
Zeile allein ist keine gültige Kennzeichnung, die Wortmarke allein erst recht
nicht.

| | |
|---|---|
| Seitenverhältnis | 4,125 : 1 (195,131 × 47,307 Einheiten) |
| Farbe | Weiß, `#ffffff` |
| Breite | 9,5 % der Bildbreite |
| Abstand zur Kante | 1,0 % der Bildbreite, in x und y derselbe Pixelwert |
| Mindestbreite Bildschirm | 90 px |
| Mindestbreite Druck | 20 mm |
| Ecke | unten rechts oder unten links, nach Kontrast |

Die Werte für Breite und Abstand sind nicht gesetzt, sondern **gemessen**: an
sechs bereits gekennzeichneten Motiven des Repositories, am 08.09.2026. Vier
lagen exakt bei 9,50 % Breite und 10 px Abstand, zwei bei 9,00 %. Die Tabelle
gibt diese Messung auf runde Zahlen gebracht wieder. Sie steht maschinenlesbar in
`brand.json` unter `ai_generated_images.marke`.

### Warum Weiß, immer

Die Ecke wird nach dem Kontrast gewählt, nicht die Farbe nach der Ecke. So bleibt
die Kennzeichnung über alle Motive hinweg dieselbe Marke und wird als solche
wiedererkannt. Trägt kein Bereich des Motivs die weiße Marke, ist das ein Hinweis
auf das Motiv, nicht auf die Marke — dann wird der Bildausschnitt geändert.

### Warum eine Mindestbreite in Millimetern

Die Zeile „AI GENERATED" misst 24 % der Logohöhe. Bei 20 mm Logobreite ergibt das
rund 1,2 mm Versalhöhe — die untere Grenze der Lesbarkeit im Druck. Ein rein
prozentualer Wert unterschreitet sie: ein 80 mm breit gedrucktes Motiv käme mit
9,5 % auf 0,44 mm und wäre unlesbar. Bei kleinen Bildern greift deshalb die
absolute Grenze, und der Vermerk wird relativ größer. Das ist gewollt.

## Das Register

`assets/kennzeichnung/register.json`

Welche Motive KI-generiert sind, kann kein Bildvergleich entscheiden — das weiß
nur, wer sie erzeugt hat. Deshalb steht es in einer Liste, die von Hand gepflegt
wird:

- **`ki_motive`** — braucht den Vermerk. Fehlt er, meldet die Prüfung einen
  Fehler und die CI bricht ab.
- **`keine_ki`** — braucht ihn nicht. Fotografiert, gezeichnet oder gesetzt.

Ein Bild in keiner der beiden Listen erzeugt einen **Hinweis, keinen Fehler**: es
ist noch nicht eingeordnet. Wer ein neues Motiv ablegt, trägt es ein.

Die Trennung ist bewusst so gebaut. Ein Skript, das aus dem Dateinamen oder dem
Bildinhalt errät, ob ein Motiv aus einem Generator stammt, würde in beide
Richtungen irren — und ein falsch als „braucht keinen Vermerk" eingestuftes Bild
fällt niemandem auf.

## Die Prüfung

```
python3 scripts/pruefe_kennzeichnung.py              # den Bestand des Registers
python3 scripts/pruefe_kennzeichnung.py uploads/x.webp
python3 scripts/pruefe_kennzeichnung.py --alle       # auch nicht eingeordnete Bilder
```

Gesucht wird über eine **normierte Kreuzkorrelation** der Bildhelligkeit gegen die
Deckungsmaske des Logos — über sechzehn Maßstäbe und alle vier Ecken, danach eine
Feinsuche um den Treffer. Die NCC ist unempfindlich gegen Helligkeit und Kontrast
des Grundes; deshalb findet sie den weißen Vermerk auf der dunklen Kellerwand
ebenso wie auf der hellen Wohnzimmerfläche.

**Trennschärfe.** An sechzehn Motiven des Repositories geprüft: die sechs
gekennzeichneten erreichen 0,945 bis 0,963, die zehn ungekennzeichneten bleiben
unter 0,455. Die Schwelle liegt bei 0,75, mitten in der Lücke. Reines Rauschen
kommt über fünf Durchgänge nicht über 0,20.

Gefunden ist nicht gleich in Ordnung. Beanstandet wird auch ein Vermerk, der
vorhanden, aber zu klein gesetzt ist oder die Bildkante berührt — letzteres fällt
beim Beschnitt als Erstes weg.

## Das Aufbringen

```
python3 scripts/pruefe_kennzeichnung.py --stempeln uploads/x.webp
python3 scripts/pruefe_kennzeichnung.py --stempeln --ecke unten_links uploads/x.webp
python3 scripts/pruefe_kennzeichnung.py --stempeln --ausgabe /tmp/probe uploads/x.webp
```

Nur auf ausdrückliche Anweisung. Die Prüfung meldet Fehlstellen, sie setzt den
Vermerk **nicht von sich aus** — ein Vermerk, den ein Skript ungefragt an die
falsche Stelle setzt, ist schlechter als ein gemeldeter fehlender.

Ohne `--ecke` entscheidet der Kontrast: bewertet wird für jede zugelassene Ecke,
wie dunkel und wie ruhig die Fläche dort ist. Eine ruhige dunkle Fläche schlägt
eine ebenso dunkle, aber stark strukturierte — auf letzterer verliert sich die
Marke, obwohl die Helligkeit stimmt.

Ohne `--ausgabe` wird die Datei an Ort und Stelle ersetzt. Bildgröße und
Farbmodell bleiben unverändert.

## Was nicht erlaubt ist

Ein vorhandener Vermerk wird nicht wegretuschiert, nicht überdeckt und nicht
beschnitten.

Beim Beschnitt gilt: **die Bildkomposition hat Vorrang.** Ein Motiv wird nicht in
ein abweichendes Format gepresst, nur damit der Vermerk sichtbar bleibt. Wer ein
Motiv platziert, prüft, welche Ecken der Beschnitt übriglässt, und setzt den
Vermerk dorthin. Reicht keine Ecke, wandert der Bildausschnitt — nicht der Kasten.
`scripts/check_export.py` meldet zu jedem beschnittenen Bild, welche Ecken sichtbar
bleiben.

## Gegenproben

```
python3 scripts/gegenproben_kennzeichnung.py
```

Vierunddreißig Fälle. Ein Sucher wie dieser hat zwei Arten zu irren: er übersieht
einen vorhandenen Vermerk, oder er meldet einen, wo keiner ist. Das zweite ist das
gefährlichere — eine Prüfung, die auf Bildrauschen anspringt, gibt ein Motiv als
gekennzeichnet frei, das es nicht ist. Deshalb sind die stummen Fälle in der
Überzahl.

Beide Prüfungen laufen in der CI (`.github/workflows/brochure.yml`).
