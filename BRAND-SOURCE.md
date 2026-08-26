# BKM Markenquelle

**Dieses Repository ist die Markenquelle der BKM Mannesmann AG für gestaltete
Unterlagen.** Es liefert Vorlagen, Schriften, Logos, Icons und die Regeln, nach
denen daraus Broschüren, Datenblätter und Titelblätter entstehen — gedacht auch
für externe Werkzeuge wie Claude Design, Manus oder ChatGPT.

**Verbindlich ist [`brand.json`](brand.json).** Farben, Schriften, Raster,
Flächen, Icon- und Bildregeln stehen dort maschinenlesbar in einem Zugriff. Bei
Widerspruch zwischen dieser Datei und Code oder Prosa gewinnt `brand.json`.
`scripts/check_brand_drift.py` liest sie und prüft den Bestand dagegen.

**Wer hier etwas erzeugt, braucht drei Dinge:** die Werte aus `brand.json`, die
Assets unter `assets/` und `uploads/` per relativem Pfad, und den Abschnitt
`open_conflicts` — dort steht, was noch nicht entschieden ist und deshalb nicht
geraten werden darf.

## Was wo liegt

| Zweck | Ort |
|:---|:---|
| Markenwerte, maschinenlesbar | `brand.json` |
| Broschüren-Vorlagen, 30 Seitentypen | `templates/brochure/` |
| Broschüren-Produktion, Jinja und WeasyPrint | `templates/pages/` |
| Technische Datenblätter | `templates/tds/` |
| Titelblätter | `templates/cover/` |
| Schriften, Logos, Keyvisual, Icons | `assets/` |
| Bilder und Texturen | `uploads/` |
| Dateiliste mit Auflösungen | `docs/ASSET-MANIFEST.md` |

## Regeldokumente

Die Prosa zu den Werten. Die Zahlen selbst stehen in `brand.json`.

| Datei | Regelt |
|:---|:---|
| `docs/BROSCHUERE-CANVAS.md` | Broschüren, Design- und Abstimmungsebene |
| `docs/BROSCHUERE-LAYOUT.md` | Broschüren, Produktionsebene |
| `docs/LAYOUT-CONTRACT.md` | Technische Datenblätter |
| `docs/REDAKTIONSSTANDARD.md` | Inhalt, Sprache, Freigabe |
| `AGENTS.md` | Arbeitsweise am Repository |

## Prüfen

```bash
python3 scripts/check_brand_drift.py <datei-oder-verzeichnis>   # Farben, Schriften
python3 scripts/check_brand_drift.py --list                     # geltende Werte
python3 scripts/validate_brochure.py                            # Broschüren-Layout
python3 scripts/validate_layout.py                              # Datenblatt-Layout
```

## Herkunft

Dieses Repository verwendet den zentralen Marken- und Icon-Standard aus [`bkmmannesmann/bkm-design-system`](https://github.com/bkmmannesmann/bkm-design-system).

| Element | Festgelegte Quelle |
|---|---|
| Repository | `bkmmannesmann/bkm-design-system` |
| Revision | [`db65c2b`](https://github.com/bkmmannesmann/bkm-design-system/commit/db65c2b9f5ccb3969ba72106d2b10836a3643f1f) |
| Icon-Manifest | `assets/icons/phosphor/manifest.json` |
| Icon-Regel | `docs/icon-system.md` |
| Repository-Governance | `docs/repository-architecture.md` |

Die TDS-Abschnittsicons unter `templates/tds/icons/` sind lokale, kuratierte Phosphor-**Bold**-SVGs aus diesem Stand. Die lokale Kopie dient der reproduzierbaren PDF-Erzeugung. Neue oder geänderte Icons müssen zuerst im zentralen Design-System geprüft und dokumentiert werden; anschließend wird dieser Pin in einem eigenen Pull Request aktualisiert.
