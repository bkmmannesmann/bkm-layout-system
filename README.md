# BKM Layout System

Programmatisches Layout-System für die Erstellung von Broschüren, Magazinen und Produktkatalogen im BKM Mannesmann Corporate Design.

## Überblick

Dieses Repository ermöglicht die automatisierte Generierung druckfertiger PDFs (DIN A4) aus HTML/CSS-Templates und JSON-Content-Dateien. Das Corporate Design (Schriften, Farben, Abstände) ist zentral definiert und wird konsistent auf alle Dokumente angewendet.

**Technologie-Stack:**
- HTML/CSS (Paged Media) für Layout-Definition
- Jinja2 für Template-Rendering
- WeasyPrint für PDF-Generierung
- Python 3.11+ als Build-Umgebung

## Schnellstart

### Voraussetzungen

```bash
pip3 install weasyprint jinja2
```

### Cover generieren (alle 5 Varianten)

```bash
python3 scripts/build_cover.py all
```

### Einzelne Cover-Variante generieren

```bash
python3 scripts/build_cover.py mannesmann
python3 scripts/build_cover.py fachbetriebe
python3 scripts/build_cover.py homeline
python3 scripts/build_cover.py proline
python3 scripts/build_cover.py anleitung
```

### Prospekt generieren (Innenseiten)

```bash
python3 scripts/build.py prospekt-fachbetrieb
```

Das generierte PDF liegt anschließend im `/output/`-Verzeichnis.

## Projektstruktur

```
bkm-layout-system/
├── assets/
│   ├── fonts/                    ← Schriftdateien (woff2)
│   │   ├── Unbounded_400.woff2
│   │   ├── Unbounded_700.woff2
│   │   ├── Unbounded_900.woff2
│   │   ├── TT_Norms_Pro_Compact_Regular.woff2
│   │   └── TT_Norms_Pro_Bold.woff2
│   └── images/
│       ├── logos/                ← BKM-Logos (4 Varianten: SVG + PNG)
│       ├── keyvisual-on-light.png
│       ├── keyvisual-on-dark.png
│       ├── badge-homeline.png
│       ├── badge-proline.png
│       └── placeholder/
├── design-system/
│   ├── variables.css             ← Zentrale CD-Variablen
│   └── base.css                  ← Basis-Stylesheet
├── components/
│   └── components.css            ← Wiederverwendbare Layout-Bausteine
├── templates/
│   ├── cover/                    ← TITELBLATT (pixelgenau definiert)
│   │   ├── cover.html            ← HTML-Template mit Jinja2
│   │   ├── cover-spec.css        ← Exakte Layout-Spezifikation
│   │   └── cover-layout.json     ← Maschinenlesbare Maße
│   └── prospekt-fachbetrieb/
│       ├── template.html
│       └── template.css
├── content/
│   └── prospekt-fachbetrieb/
│       └── content.json
├── scripts/
│   ├── build_cover.py            ← Cover-Builder (5 Varianten)
│   ├── build.py                  ← Prospekt-Builder
│   └── validate_json.py
├── output/                       ← Generierte PDFs (gitignored)
│   └── covers/
└── README.md
```

## Corporate Design – Titelblatt

### Grundraster

| Parameter | Wert | Berechnung |
|:---|:---|:---|
| Format | DIN A4 (210mm × 297mm) | — |
| Farbkasten | 210mm × 118.1mm | 16:9 Verhältnis zur Breite |
| 8mm-Erweiterung | Rechts unten, bündig | L-förmige Farbfläche |
| Key Visual Breite | 42mm | 1/5 der Formatbreite |
| Logo Breite | 42mm | 1/5 der Formatbreite |
| Linker Rand | 18mm | Fluchtlinie für alle Textelemente |

### Typografie

| Element | Schrift | Größe | Laufweite | Besonderheiten |
|:---|:---|:---|:---|:---|
| Headline | Unbounded Black (900) | 30pt | 0 | VERSALIEN, immer 2-zeilig, Z1 < Z2, NIE 3-zeilig |
| Subheadline | Unbounded Black (900) | 12pt | 0 | Keine Versalien, ein- oder zweizeilig |
| Fließtext | TT Norms Pro Regular (400) | 12pt | -0.015em | Max 2 Zeilen, NIE mehr |

### Abstände (pixelgenau bei 300dpi)

| Von → Nach | Abstand | mm |
|:---|:---|:---|
| Logo Oberkante → Seitenrand oben | 18mm | 213px |
| Logo Linkskante → Seitenrand links | 18mm | 213px |
| Logo Unterkante → Headline Oberkante | 18mm | 213px |
| Headline Unterkante → Subheadline Oberkante | **95px** | 7.87mm |
| Subheadline Unterkante → Fließtext Oberkante | **10px** | 0.85mm |

### Ebenen (z-index, von hinten nach vorne)

1. Hero-Bild (unterste Ebene, vollflächig)
2. L-förmige Farbfläche (16:9-Kasten + 8mm-Erweiterung)
3. Key Visual + Badge (immer davor)
4. Text-Elemente (Logo, Headline, Subheadline, Fließtext)

### 5 Broschüren-Varianten

| Variante | Hintergrund | Logo | Headline + Fließtext | Subheadline | Badge |
|:---|:---|:---|:---|:---|:---|
| BKM Mannesmann AG | Deep Green (#1c4b42) | Weiß-Grün | Weiß | Lime Green (#b4e717) | — |
| Fachbetriebe | Transition Green (#287d4b) | Weiß-Grün | Weiß | Pure Green (#4daf46) | — |
| BKM Home Line | Pure Green (#4daf46) | Weiß-Grün | Weiß | Deep Green (#1c4b42) | Home Line (Silber) |
| BKM Pro Line | Stone Grey (#494949) | Weiß-Grün | Weiß | Pure Green (#4daf46) | Pro Line (Gold) |
| Verarbeitungsanleitung | Weiß (#ffffff) | Grau-Grün | Stone Grey (#494949) | Pure Green (#4daf46) | — |

### Regeln

- **Headline:** IMMER 2-zeilig, NIE 3-zeilig. Zeile 1 hat weniger Zeichen als Zeile 2.
- **Fließtext:** MAXIMAL 2 Zeilen, NIE mehr.
- **Logo-Kontrast:** Immer die Variante mit höchstem Kontrast zum Hintergrund.
- **Text auf dunklem BG:** Weiß. Text auf weißem BG: Stone Grey.
- **Key Visual:** IMMER das dreifarbige (on-light), NIE in Code nachbauen.
- **Badge:** Nur bei Home Line und Pro Line. Linksbündig, zentriert auf Farbkasten-Unterkante.

## Farbpalette (korrigierte Werte)

| Name | Hex | Verwendung |
|:---|:---|:---|
| Deep Green | `#1c4b42` | BKM Mannesmann AG Hintergrund |
| Transition Green | `#287d4b` | Fachbetriebe Hintergrund |
| Pure Green | `#4daf46` | Home Line Hintergrund, Subheadline-Akzent |
| Lime Green | `#b4e717` | Subheadline-Akzent (auf dunklem BG) |
| Stone Grey | `#494949` | Pro Line Hintergrund, Text auf Weiß |
| Weiß | `#ffffff` | Verarbeitungsanleitung Hintergrund |

## Schriften

Die Schriftdateien liegen in `/assets/fonts/` (woff2-Format):

| Datei | Schrift | Gewicht |
|:---|:---|:---|
| `Unbounded_900.woff2` | Unbounded Black | 900 – Headline + Subheadline |
| `Unbounded_700.woff2` | Unbounded Bold | 700 |
| `Unbounded_400.woff2` | Unbounded Regular | 400 |
| `TT_Norms_Pro_Compact_Regular.woff2` | TT Norms Pro | 400 – Fließtext |
| `TT_Norms_Pro_Bold.woff2` | TT Norms Pro Bold | 700 |

## Nächste Schritte (TODO)

- [ ] Innenseiten-Templates (Spalten, Zitat-Box, Produkt-Grid)
- [ ] Rückseiten-Template
- [ ] Content-Pipeline für verschiedene Broschüren-Typen
- [ ] CMYK-Konvertierung für Druckproduktion

## Lizenz

Proprietär – BKM Mannesmann AG. Nicht zur Weitergabe bestimmt.
