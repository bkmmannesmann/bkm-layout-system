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
| Mindestbreite Druck | 15 mm |
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

Die Zeile „AI GENERATED" misst 24 % der Logohöhe. Bei 15 mm Logobreite ergibt das
rund 0,85 mm Versalhöhe.

Ein rein prozentualer Wert fällt auf kleinen Bildern darunter: auf 85 mm Bildbreite
ergeben 9,5 % nur 8,1 mm Marke und 0,46 mm Versalhöhe — die Zeile ist dort nicht
mehr zu entziffern.

Das Mindestmaß ist so gewählt, dass es **die bestehende Praxis nicht antastet**:
9,5 % erreichen 15 mm bereits bei 158 mm Bildbreite. Ein Motiv über die volle
Satzbreite behält deshalb seine 16,5 mm — dort greift weiterhin der Anteil.
Angehoben werden nur schmalere Bilder.

| Bildbreite | 9,5 % | es gilt | Marke | Anteil | Versalhöhe |
|---:|---:|:---|---:|---:|---:|
| 174 mm | 16,5 mm | Anteil | 16,5 mm | 9,5 % | 0,94 mm |
| 158 mm | 15,0 mm | Umschlagpunkt | 15,0 mm | 9,5 % | 0,85 mm |
| 113 mm | 10,7 mm | Mindestmaß | 15,0 mm | 13,3 % | 0,85 mm |
| 85 mm | 8,1 mm | Mindestmaß | 15,0 mm | 17,6 % | 0,85 mm |
| 55 mm | 5,2 mm | Mindestmaß | 15,0 mm | 27,3 % | 0,85 mm |

Entschieden am 08.09.2026 nach einer Formatprobe über sieben Bildformate von
21:9 bis 9:16. Ein zuvor geprüfter Wert von 20 mm hätte 1,14 mm Versalhöhe
gehalten, dafür aber 24 bis 36 % der Bildbreite beansprucht und wirkte am Motiv
zu schwer.

### Die Platzierungsbreite gehört zum Stempeln

Die Marke wird ins Pixelbild gebrannt und skaliert mit der Platzierung mit. Ihre
gedruckte Größe hängt deshalb **allein an der Breite, in der das Motiv im Layout
steht** — nicht an seiner Auflösung. Ein Stempellauf, der diese Breite nicht
kennt, kann das Mindestmaß in Millimetern gar nicht einhalten; er weiß nicht, wie
groß das Bild am Ende wird.

Wer für den Druck stempelt, gibt sie mit:

```
python3 scripts/pruefe_kennzeichnung.py --stempeln --druckbreite 85 uploads/x.webp
```

Ohne `--druckbreite` gilt der Anteil an der Bildbreite — die Bildschirmrechnung
und zugleich die bisherige BKM-Praxis.

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

Gesucht wird über **5 % bis 45 % der Bildbreite**. Die Obergrenze folgt aus dem
Mindestmaß: druckgerecht gesetzt misst die Marke auf einem 42 mm breiten Motiv
36 % der Bildbreite. Sie lag zuerst bei 21 % — damit fand der Sucher genau die
Marken nicht, die das Repository selbst druckgerecht aufbringt.

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

Die Bewertung läuft von 0 bis 1. Zur Einordnung: eine sehr dunkle Ecke erreicht
**0,89**, die bereits gekennzeichneten BKM-Motive liegen bei **0,75 bis 0,80**,
eine mittelhelle Fläche bei **0,52**, eine weiße bei **0,30**. Unter **0,45** trägt
die Ecke nicht mehr — dann wandert der Bildausschnitt, nicht die Farbe der Marke.

Ohne `--ausgabe` wird die Datei an Ort und Stelle ersetzt. Bildgröße und
Farbmodell bleiben unverändert.

## Der Beschnitt entscheidet mit

```
python3 scripts/pruefe_kennzeichnung.py --platzierung
```

Ein Vermerk, der im Bild steht, aber vom Layoutkasten weggeschnitten wird,
erfüllt die Kennzeichnungspflicht **nicht** — im Dokument ist er nicht da.

`object-fit: cover` füllt den Kasten und schneidet zentral weg, was übersteht.
Weil der Vermerk in einer Ecke mit 1 % Randabstand sitzt, ist er das Erste, was
verlorengeht: sobald der Kasten ein anderes Seitenverhältnis hat als das Motiv,
fällt seine Ecke aus dem sichtbaren Bereich.

Ein Beispiel aus dem Bestand: `magnific_ultrarealistic-architectu…` misst
2,356 : 1 und steht im Titelblatt in einem Kasten von 210 × 179,5 mm, also
1,17 : 1. Sichtbar bleiben davon **25,2 bis 74,8 %** der Bildbreite — der Vermerk
bei 1,0 bis 10,5 % liegt weit außerhalb.

Geprüft werden die Canvas-Vorlagen, nicht ein Export: was dort steht, geht in
jede daraus gebaute Broschüre ein. `scripts/check_export.py` prüft dasselbe am
exportierten PDF, setzt aber voraus, dass jemand exportiert hat.

Abhilfe nach der Regel unten: der Bildausschnitt wandert, nicht der Kasten —
also eine eigene, auf das Platzierungsformat zugeschnittene und dann gestempelte
Fassung je Platzierung.

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
