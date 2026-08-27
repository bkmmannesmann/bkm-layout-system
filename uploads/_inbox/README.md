# Eingang für neue Assets

Hier landen hochgeladene Dateien, bevor sie an ihren Platz kommen.

## Warum es diesen Ordner gibt

Über die GitHub-Weboberfläche lässt sich kein ZIP entpacken, und pro Vorgang
gehen höchstens **100 Dateien mit je 25 MB**. Viele Assets auf einmal muss man
deshalb in mehreren Portionen hochladen — und dabei jedes Mal von Hand den
richtigen Zielordner treffen. Das geht schief.

Stattdessen: alles hier hochladen, dann einmal sortieren lassen.

## So geht es

1. **Hochladen** — im Repository auf *Add file → Upload files*, die Dateien in
   diesen Ordner ziehen. Bei vielen Dateien in mehreren Portionen; jede Portion
   ist ein eigener Commit, das ist in Ordnung.

2. **Sortieren lassen**

   ```bash
   python3 scripts/sort_assets.py            # zeigt nur an, verschiebt nichts
   python3 scripts/sort_assets.py --write    # verschiebt
   ```

3. **Manifest nachziehen** — neue Dateien in `docs/ASSET-MANIFEST.md` eintragen,
   sobald eine Vorlage sie referenziert.

## Was das Skript prüft

Einsortiert wird nach Dateityp und — bei Bildern — nach dem **gemessenen
Seitenverhältnis**, nicht nach dem Dateinamen. Der Name sagt, was gemeint war;
das Verhältnis sagt, was die Datei ist. Weichen beide voneinander ab, bleibt die
Datei liegen und wird gemeldet.

Die Bildformate der Marke:

| Format | Verhältnis | bei 210 mm breit | wofür |
|:---|:---|:---|:---|
| Hero-Grafik | `1,680` | 125 mm | Titelblatt, trägt die Eckerweiterung |
| A4-Fläche | `0,707` | 297 mm | ganzseitige Textur |
| 16:9 | `1,778` | 118,125 mm | **nicht** als Titelblatt-Hintergrund geeignet |

**Der häufigste Fehler:** ein Titelblatt-Hintergrund im Format 16:9. Er endet bei
`118,125 mm` — genau dort, wo die Eckerweiterung *anfängt*. Er kann sie nicht
mitbringen, und im PDF schaut an dieser Stelle rechts unten das Foto durch. Die
Hero-Grafik ist deshalb `210 × 125 mm` und braucht einen **Alphakanal**:
unterhalb der 16:9-Kante ist nur der Eckzipfel deckend.

Beides meldet das Skript, statt die Datei durchzulassen.
