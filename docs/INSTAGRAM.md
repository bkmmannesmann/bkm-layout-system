# Instagram-Karussells

Karussell-Posts entstehen in **Claude Design** und werden hier unverändert zu PNGs gesetzt —
von Chromium, demselben Browser, in dem Claude Design den Entwurf zeigt. Es gibt keine
Nachbildung als Template: das PNG ist der Entwurf.

| | |
|:---|:---|
| Format | 1080 × 1350 px (4:5, Instagram-Hochformat). `--format 1:1` oder `9:16` auf Wunsch. |
| Folien | 7 bis 10 je Post. Abweichung bricht ab (`--min`, `--max` zum Übersteuern). |
| Datei | PNG, RGB ohne Alphakanal, sRGB — verlustfrei. Instagram komprimiert erst beim Upload. |
| Ablage | Entwurf: `social/instagram/<post>/` · Ausgabe: `output/instagram/<post>/` (nicht im Git) |

## 1. Entwurf in Claude Design

- Jede Folie ein eigenes Artboard. Die Größe ist frei, solange das **Seitenverhältnis 4:5**
  stimmt — 1080 × 1350 ist am einfachsten, 540 × 675 geht genauso; das Skript rendert mit der
  passenden Pixeldichte, es rechnet nicht hoch.
- Reihenfolge im Canvas = Reihenfolge im Karussell.
- Die Artboards erkennt das Skript an `data-screen-label` (setzt Claude Design selbst). Wer
  eigenes HTML baut, markiert die Folien mit `data-slide`.
- Farben und Schriften aus `brand.json`. Bilder mit dem Vermerk „AI GENERATED" behalten ihn
  sichtbar (AGENTS.md, Regel 7).

## 2. Export

**Project archive** wählen, nicht Standalone HTML. Das Archiv ist sofort da und kostet nichts;
Standalone HTML bettet alle Bilder base64-kodiert ein und wird dadurch rund ein Drittel
größer als die Bilder selbst — bei bildlastigen Posts schnell über 30 MB.

## 3. Ins Repository

**Weg A — im Browser auf github.com** (Grenze: 25 MB je Datei, 100 Dateien je Upload)

1. ZIP auf dem Rechner entpacken.
2. Im Repository *Add file → Upload files*, den entpackten **Ordnerinhalt** in einen neuen
   Ordner `social/instagram/<post>/` ziehen. Den Ordnernamen gibt man im Pfadfeld oben ein.
3. Committen. Die Action **Instagram** baut die PNGs (siehe 4).

Ist das ZIP selbst kleiner als 25 MB, darf auch nur das ZIP in den Post-Ordner — das Skript
entpackt es beim Bau nach `_entpackt/`.

Einzelne Bilder über 25 MB: vorher als JPEG in hoher Qualität (90+) speichern. Sichtbar wird
das nicht, Instagram komprimiert ohnehin selbst. Oder Weg B nehmen.

**Weg B — lokal mit git** (bis 100 MB je Datei)

```bash
python3 scripts/build_instagram.py ~/Downloads/<projekt>.zip --slug <post>
git add social/instagram/<post> && git commit -m "Instagram: <post>" && git push
```

Das ZIP wird nach `social/instagram/<post>/` entpackt und sofort gebaut.

## 4. PNGs bauen

**Auf GitHub:** Jeder Push unter `social/instagram/` startet die Action *Instagram* und baut die
geänderten Posts. Von Hand: *Actions → Instagram → Run workflow* (Feld leer = alle Posts).
Die PNGs liegen danach im Lauf unten unter **Artifacts → instagram-png**.

**Lokal:**

```bash
pip install -r requirements.txt && playwright install chromium   # einmalig
python3 scripts/build_instagram.py social/instagram/<post>/
python3 scripts/build_instagram.py --alle
```

Ergebnis: `output/instagram/<post>/<post>-01.png` … und `<post>.zip` mit allen Folien.

## Was geprüft wird

| Prüfung | Folge |
|:---|:---|
| Schrift lädt nicht oder wird verwendet, ohne geladen zu sein | Fehler — Chromium setzt sonst still eine Ersatzschrift |
| Bild in einer Folie lädt nicht | Fehler |
| Folie nicht im Zielformat | Fehler, Folie wird nicht gespeichert |
| Folienzahl außerhalb 7–10 | Fehler |
| Farben/Schriften außerhalb `brand.json` (`check_brand_drift.py`) | Hinweis |

Bei Fehlern entstehen die PNGs trotzdem (zum Ansehen), der Lauf endet aber mit Exit-Code 1.

## Wenn etwas nicht passt

- **„Keine Folie gefunden"** — Folien mit `data-slide` markieren oder
  `--selector ".meine-folie"` angeben.
- **Mehrere HTML-Dateien** — `--datei <name>.html`.
- **Schrift lädt nicht** — die Schriftdatei fehlt im Export oder der Pfad stimmt nicht. Die
  Markenschriften liegen unter `assets/fonts/`; relativ aus `social/instagram/<post>/` ist das
  `../../../assets/fonts/`.
- **Inhalt erscheint verspätet** (Skripte, Animationen) — `--warten 2000`.
