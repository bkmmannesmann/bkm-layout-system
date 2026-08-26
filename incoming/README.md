# Eingang

Ablage für Dateien, die von außerhalb kommen und noch nicht Teil des geprüften
Systems sind — Entwürfe aus Claude Design, Exporte, Zulieferungen.

`design-canvas/` nimmt die `.dc.html`-Artboards aus dem Claude-Design-Projekt
"Broschüren-Templates" auf.

Ablauf für jede eingehende Datei:

```bash
python3 scripts/check_brand_drift.py incoming/design-canvas/<datei>
```

Nichts hier ist verbindlich. Was übernommen wird, wandert nach `templates/`
oder `content/` und gilt erst dann, wenn `validate_brochure.py` und der Bau
grün sind. Der Eingang selbst wird nicht von der CI geprüft.
