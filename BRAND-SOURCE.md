# BKM Markenquelle

Dieses Repository verwendet den zentralen Marken- und Icon-Standard aus [`bkmmannesmann/bkm-design-system`](https://github.com/bkmmannesmann/bkm-design-system).

| Element | Festgelegte Quelle |
|---|---|
| Repository | `bkmmannesmann/bkm-design-system` |
| Revision | [`db65c2b`](https://github.com/bkmmannesmann/bkm-design-system/commit/db65c2b9f5ccb3969ba72106d2b10836a3643f1f) |
| Icon-Manifest | `assets/icons/phosphor/manifest.json` |
| Schriften | `assets/fonts/` — mit `python3 scripts/sync_fonts.py` aus dieser Revision geholt |
| Icon-Regel | `docs/icon-system.md` |
| Repository-Governance | `docs/repository-architecture.md` |

Die TDS-Abschnittsicons unter `templates/tds/icons/` sind lokale, kuratierte Phosphor-**Bold**-SVGs aus diesem Stand. Die lokale Kopie dient der reproduzierbaren PDF-Erzeugung. Neue oder geänderte Icons müssen zuerst im zentralen Design-System geprüft und dokumentiert werden; anschließend wird dieser Pin in einem eigenen Pull Request aktualisiert.

Die lizenzierten Markenschriften werden nicht in dieses Repository kopiert. `scripts/sync_fonts.py`
liest die oben festgelegte Revision aus dieser Datei und holt die fünf woff2-Dateien direkt von dort
nach `assets/fonts/`. Eine neue Schriftrevision wird deshalb ausschließlich über eine Änderung des
Revisions-Pins übernommen.
