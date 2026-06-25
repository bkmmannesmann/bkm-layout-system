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

### PDF generieren

```bash
# Standard-Build (nutzt content/prospekt-fachbetrieb/content.json)
python3 scripts/build.py prospekt-fachbetrieb

# Mit benutzerdefiniertem Content
python3 scripts/build.py prospekt-fachbetrieb --content content/mein-projekt/content.json

# Mit benutzerdefiniertem Output-Pfad
python3 scripts/build.py prospekt-fachbetrieb --output output/mein-prospekt.pdf
```

Das generierte PDF liegt anschließend im `/output/`-Verzeichnis.

## Projektstruktur

```
bkm-layout-system/
├── assets/
│   ├── fonts/              ← Schriftdateien (Unbounded, TT Norms Pro)
│   └── images/
│       ├── logos/          ← BKM-Logos (SVG/EPS)
│       ├── icons/          ← Icons und Symbole
│       └── placeholder/    ← Platzhalter-Bilder für Entwicklung
├── design-system/
│   ├── variables.css       ← Zentrale CD-Variablen (Farben, Schriften, Abstände)
│   └── base.css            ← Basis-Stylesheet (Reset, Typografie, Paged Media)
├── components/
│   └── components.css      ← Wiederverwendbare Layout-Bausteine
├── templates/
│   └── prospekt-fachbetrieb/
│       ├── template.html   ← HTML-Template mit Jinja2-Platzhaltern
│       └── template.css    ← Template-spezifisches CSS
├── content/
│   └── prospekt-fachbetrieb/
│       └── content.json    ← Texte, Bildpfade und Metadaten
├── scripts/
│   ├── build.py            ← Haupt-Build-Skript
│   └── validate_json.py    ← JSON-Validierung
├── output/                 ← Generierte PDFs (gitignored)
└── README.md
```

## Corporate Design

### Schriften

| Schrift | Verwendung | Schnitte |
|:---|:---|:---|
| **Unbounded** | Display-Headlines | Black, ExtraBold, Bold, SemiBold, Medium, Regular, Light, ExtraLight |
| **TT Norms Pro** | Fließtext, Subheadlines | Bold, DemiBold, Medium, Regular, Light (jeweils + Italic) |

Die Schriftdateien müssen in `/assets/fonts/` abgelegt werden. Sie sind nicht im Repository enthalten (lizenziert).

### Farbpalette

| Variable | Farbe | Hex | Verwendung |
|:---|:---|:---|:---|
| `--bkm-pure-green` | Pure Green | `#009245` | Haupt-Markenfarbe, Headlines, CTAs |
| `--bkm-deep-green` | Deep Green | `#006837` | Chevrons, Akzente |
| `--bkm-transition-green` | Transition Green | `#00A99D` | Hintergründe |
| `--bkm-lime-green` | Lime Green | `#8CC63F` | Subheadlines, Highlights |
| `--bkm-stone-grey` | Stone Grey | `#4A4A4A` | Kontrastflächen |
| `--bkm-black` | Schwarz | `#000000` | Fließtext |
| `--bkm-white` | Weiß | `#FFFFFF` | Hintergrund |

## Verfügbare Komponenten

Das System bietet folgende wiederverwendbare Layout-Bausteine:

| Komponente | CSS-Klasse | Beschreibung |
|:---|:---|:---|
| Cover | `.cover` | Titelseite mit Logo, Headline, Hero-Bild und Chevron-Grafik |
| Headline-Block | `.headline-block` | Grüne Headline + kursive Subline |
| Spalten-Layout | `.columns-2`, `.columns-3` | Mehrspaltige Textblöcke |
| Grid-Layout | `.grid-2`, `.grid-2--wide-left` | Asymmetrische Raster |
| Zitat-Box | `.quote-box` | Grüne Box mit abgerundeten Ecken und Anführungszeichen |
| Bild-Block | `.image-block` | Bildplatzhalter mit Cover-Fit |
| Dunkle Sektion | `.dark-section` | Kontrastfläche mit weißem Text |
| Prozess-Liste | `.process-list` | Nummerierte Schritte |
| Info-Block | `.info-block` | Titel + Beschreibung (für Aufzählungen) |
| CTA-Text | `.cta-text` | Grüner Call-to-Action |
| Footer | `.footer` | Logos + Kontaktdaten |
| Rückseite | `.back-cover` | Hero-Bild + CTA + Kontakt |

## Workflow: Neues Dokument erstellen

### 1. Content-Datei anlegen

Erstelle eine neue JSON-Datei unter `/content/<projektname>/content.json`:

```json
{
  "meta": {
    "title": "Mein neues Dokument",
    "template": "prospekt-fachbetrieb",
    "format": "DIN A4",
    "language": "de"
  },
  "global": {
    "logo_path": "../../assets/images/logos/bkm-logo-weiss.svg",
    "company_name": "BKM Mauertrocknungs GmbH",
    ...
  },
  "page1_cover": {
    "cover_title": "MEINE HEADLINE",
    "cover_subtitle": "Meine Subline",
    ...
  }
}
```

### 2. Bilder bereitstellen

Lege die Bilder unter `/assets/images/` ab und referenziere sie in der Content-Datei mit relativen Pfaden.

### 3. PDF generieren

```bash
python3 scripts/build.py prospekt-fachbetrieb --content content/mein-projekt/content.json
```

## Neues Template erstellen

1. Erstelle einen neuen Ordner unter `/templates/<template-name>/`
2. Erstelle `template.html` mit Jinja2-Platzhaltern (`{{ variable_name }}`)
3. Erstelle `template.css` für template-spezifische Stile
4. Importiere das Design-System und die Komponenten im HTML-Head
5. Erstelle eine passende Content-JSON-Datei unter `/content/<template-name>/`

## Hinweise

- **Schriften:** Die Schriftdateien (Unbounded, TT Norms Pro) sind lizenziert und müssen separat in `/assets/fonts/` abgelegt werden.
- **Bilder:** Platzhalter-Bilder können durch echte Bilder ersetzt werden, indem die Pfade in der Content-JSON angepasst werden.
- **Print-Qualität:** Für Druckproduktion sollten Bilder mindestens 300 DPI haben.
- **CMYK:** WeasyPrint generiert RGB-PDFs. Für CMYK-Konvertierung kann Ghostscript oder ein professionelles Preflight-Tool verwendet werden.

## Lizenz

Proprietär – BKM Mannesmann AG. Nicht zur Weitergabe bestimmt.
