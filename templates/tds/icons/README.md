# TDS-Abschnittsicons

Dieses Verzeichnis enthält die für technische Datenblätter benötigten, lokal eingebundenen
**Phosphor Icons in Bold**. Die Symbolnamen folgen aus Kompatibilitätsgründen den bisherigen
TDS-Dateinamen; die SVG-Inhalte stammen aus dem kuratierten BKM-Icon-System.

- Zentrale Quelle: `bkmmannesmann/bkm-design-system`, `assets/icons/phosphor/manifest.json`
- Upstream: Phosphor Icons Core `v2.0.8`
- Lizenz: MIT; vollständiger Lizenztext in `LICENSE-PHOSPHOR-MIT.txt`

Für neue oder geänderte Abschnittsicons ausschließlich das zentrale BKM-Manifest und die
Regeln in `bkm-design-system/docs/icon-system.md` verwenden.

## Einfärbung im PDF-Build

Die SVG bleiben unverändert bei `fill="currentColor"`. WeasyPrint rendert eingebettete
SVG mit einer eigenen Engine, in die weder die Dokument-CSS noch `currentColor` hineinreichen —
ohne gesetztes `fill`-Attribut zeichnet es die Glyphen schwarz. `scripts/build_tds.py` setzt die
Füllfarbe deshalb beim Rendern ein und liest sie aus der Markenvariable `--tds-lime`
in `templates/tds/template.css`. Die Regel in `template.css` bleibt für die Browser-Vorschau bestehen.
Die Icon-Dateien dürfen dafür nicht angepasst werden; sie entsprechen dem in `BRAND-SOURCE.md`
festgelegten Stand.
