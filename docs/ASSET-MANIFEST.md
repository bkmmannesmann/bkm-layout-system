# Asset-Manifest — templates/brochure/

Alle Dateien, die die neun Vorlagen referenzieren. Pfade relativ zum
Repository-Wurzelverzeichnis.

## assets/ (45)
- `assets/fonts/TT_Norms_Pro_Bold.woff2`
- `assets/fonts/TT_Norms_Pro_Compact_Regular.woff2`
- `assets/fonts/Unbounded_400.woff2`
- `assets/fonts/Unbounded_700.woff2`
- `assets/fonts/Unbounded_900.woff2`
- `assets/icons/phosphor/bold/arrow-right.svg`
- `assets/icons/phosphor/bold/arrows-out.svg`
- `assets/icons/phosphor/bold/atom.svg`
- `assets/icons/phosphor/bold/caret-right.svg`
- `assets/icons/phosphor/bold/certificate.svg`
- `assets/icons/phosphor/bold/chat-centered-text.svg`
- `assets/icons/phosphor/bold/check.svg`
- `assets/icons/phosphor/bold/compass.svg`
- `assets/icons/phosphor/bold/drop-half.svg`
- `assets/icons/phosphor/bold/drop.svg`
- `assets/icons/phosphor/bold/eye.svg`
- `assets/icons/phosphor/bold/flask.svg`
- `assets/icons/phosphor/bold/funnel.svg`
- `assets/icons/phosphor/bold/gear-six.svg`
- `assets/icons/phosphor/bold/globe.svg`
- `assets/icons/phosphor/bold/hammer.svg`
- `assets/icons/phosphor/bold/handshake.svg`
- `assets/icons/phosphor/bold/house.svg`
- `assets/icons/phosphor/bold/image.svg`
- `assets/icons/phosphor/bold/magnifying-glass.svg`
- `assets/icons/phosphor/bold/map-pin.svg`
- `assets/icons/phosphor/bold/package.svg`
- `assets/icons/phosphor/bold/scales.svg`
- `assets/icons/phosphor/bold/seal-check.svg`
- `assets/icons/phosphor/bold/shield-check.svg`
- `assets/icons/phosphor/bold/squares-four.svg`
- `assets/icons/phosphor/bold/stack.svg`
- `assets/icons/phosphor/bold/table.svg`
- `assets/icons/phosphor/bold/trash.svg`
- `assets/icons/phosphor/bold/tree-structure.svg`
- `assets/icons/phosphor/bold/warehouse.svg`
- `assets/icons/phosphor/bold/warning.svg`
- `assets/images/badge-homeline.png`
- `assets/images/badge-proline.png`
- `assets/keyvisual/keyvisual-lime.svg`
- `assets/keyvisual/keyvisual-on-dark.svg`
- `assets/keyvisual/keyvisual-on-light.svg`
- `assets/logos/bkm-logo-stonegrey-puregreen.svg`
- `assets/logos/bkm-logo-white-puregreen.svg`
- `assets/logos/bkm-logo-white.svg`

## uploads/ (22)
- `uploads/a4-texture-deep-green-2.jpg`
- `uploads/a4-texture-deep-green-3.jpg`
- `uploads/a4-texture-deep-green.jpg`
- `uploads/a4-texture-transition-green-2.jpg`
- `uploads/a4-texture-transition-green.jpg`
- `uploads/a4-texture-white-5.jpg`
- `uploads/bkm-fachbetrieb-messergebnis-schadensanalyse.webp`
- `uploads/bkm-fachbetrieb-sanierter-keller-ergebnis.webp`
- `uploads/bkm-fachbetrieb-schadensanalyse-abplatzender-putz.webp`
- `uploads/bkm-fachbetriebs-kunde-sucht-hilfe-beifeuchteschaden.webp`
- `uploads/druckwasser-abplazender-putz-feuchte-waende.jpg`
- `uploads/fachbetrieb-partner-standard.webp`
- `uploads/feuchte-waende-selbst-sanieren.webp`
- `uploads/magnific_nano-banana-2-halbnah-san_3GXw9NsREY.jpg`
- `uploads/magnific_ultrarealistic-architectu_CHxX15MEEy.jpg`
- `uploads/signatur-bkm-systempartner-logo.png`
- `uploads/titel-hero-anleitung-d5b6a7aa.png`
- `uploads/titel-hero-bkm-ag-web.png`
- `uploads/titel-hero-fachbetrieb.png`
- `uploads/titel-hero-home-line-web.png`
- `uploads/titel-hero-pro-line-web.png`
- `uploads/trockene-waende-mit-novusan.webp`

## Hinweise

**Texturen** `a4-texture-*.jpg`: im Repository 1240 × 1754 px = 150 dpi, siehe
„Bildaufbereitung" unten. Die Originale liegen als PNG mit 2480 × 3508 px = 300 dpi
im Projekt. Als `background` der Seite setzen, nicht als absolut positioniertes Bild.

**Hero-Grafiken** `titel-hero-*.png`: 210 × 125 mm; drei davon liegen halbauflösend
mit Suffix `-web` im Repository. Enthalten den 16:9-Farbbereich
(118,125 mm) plus die Eckerweiterung unten rechts. Fünf Varianten, je Absender eine.

**Fotos** `*.webp` / `magnific_*.png`: Kundenreise und Fachbetriebs-Prozess.
Casting-Konvention: Kunde grünes Hemd, Fachbetrieb schwarzes Polo.
KI-generierte Motive tragen den Vermerk „AI GENERATED" unten rechts —
nach EU-KI-Verordnung sichtbar lassen, nicht beschneiden.

**Icons**: Phosphor Bold, `viewBox="0 0 256 256"`, `fill="currentColor"`.
Im Canvas als CSS-Maske eingesetzt, deshalb ohne Inline-Füllung.
Für die WeasyPrint-Pipeline brauchen sie `style="fill:#b4e717"` am `svg`-Element —
siehe LAYOUT-CONTRACT.md, Abschnitt Icons.

**Doppelung zum TDS-Set**: `table.svg`, `warning.svg`, `package.svg`, `scales.svg`,
`seal-check.svg`, `atom.svg`, `house-line.svg` liegen auch in `templates/tds/icons/`
unter Blocknamen. Der Canvas nutzt die Motivnamen. Nicht zusammenlegen —
die TDS-Dateien sind über einen Geometrie-Hash ans Manifest gebunden.

## Bildaufbereitung für das Repo

Alle Bilder in `uploads/` sind bewusst für Bildschirm und Layout-Abstimmung aufbereitet, nicht für den Druck:

- **A4-Texturen** — JPEG, 1240 × 1754 px (150 dpi), Qualität 0,78. Originale lagen als PNG mit 8–10 MB je Datei vor.
- **Hero-Grafiken** — PNG mit Alphakanal, halbe Auflösung (1240 × 738 px), Suffix `-web`. Die Transparenz der Eckerweiterung bleibt erhalten, deshalb kein JPEG.
- **Fotos** — JPEG, längste Kante 1600 px, Qualität 0,8.

Gesamtgewicht `uploads/`: 5,4 MB statt 84 MB.

Geht eine Broschüre in Druck, ersetzt die Druckvorstufe die betroffenen Bilder durch die Originale in voller Auflösung. Die Dateinamen bleiben gleich, beim Hero fällt das Suffix `-web` weg.

## Stand im Repository

Eingespielt am 25.08.2026. Abweichungen von der Lieferung, die beim Einspielen
aufgelöst wurden:

- Das Siegel kam als `signatur bkm-systempartner-logo-web-44044a3e.png` mit einem
  Leerzeichen im Dateinamen. Ein Leerzeichen erzwingt `%20` in der URL, und genau
  daran ist der Verweis vorher schon einmal gescheitert — der Browser dekodiert es
  zurück und findet die Datei nicht. Übernommen wurde der Name aus der Liste oben:
  `signatur-bkm-systempartner-logo.png`.
- Die neun `.dc.html` lagen dem Archiv nicht bei. Die Bildpfade in
  `templates/brochure/` sind stattdessen im Repository umgestellt worden; alle 48
  Verweise lösen auf.
- Die Schriftverweise zeigen wieder auf die `.woff2`-Dateien. Sie hatten
  zwischenzeitlich auf die TTF gezeigt, weil die woff2 im Repository fehlten —
  jetzt liegen sie hier.

Die sechs A4-Texturen sind abgelegt, werden von den Vorlagen aber **noch nicht
referenziert**. Sie stehen bereit für Seiten, die einen Texturgrund bekommen sollen.
