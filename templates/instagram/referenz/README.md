# Instagram-Referenz

Designvorlage aus Claude Design, **nur für Instagram-Karussells**. Sie wird nicht gepostet und
nicht inhaltlich verändert; aus ihr werden die Folientypen abgeleitet, mit denen die Posts aus
dem Content-Plan gebaut werden.

| | |
|:---|:---|
| Quelle | Claude Design, Artifact `R9vh1p5to5LTqunofAvP3x`, Stand 15.10.2026 |
| Maßgeblich | **Runde 4 · Version 2** (Karussells 4a DIY, 4b Feuchte-Check, 4c Fachbetrieb) |
| Archiv | Runde 3 (3a–3c) steht zum Vergleich in derselben Datei |
| Format | 1080 × 1350 px, je 7 Folien, StoryBrand: der Kunde ist der Held, BKM der Begleiter |

`index.html` ist der Export ohne die Verpackung von Claude Design: dieselbe Vorlage, die
eingebetteten Dateien liegen mit sprechenden Namen unter `dateien/`. React liegt lokal bei,
damit die Datei ohne Internet rendert. Kontrolle: alle 42 Folien pixelgleich mit dem Export.

```bash
python3 scripts/build_instagram.py templates/instagram/referenz/ --slug referenz --min 1 --max 100
```

Die Fotos sind Kopien aus der Referenz. Trägt ein Motiv den Vermerk „AI GENERATED", bleibt er
sichtbar (AGENTS.md, Regel 7).
