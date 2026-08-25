# Layoutvertrag Broschüren

Gilt für A4-Broschüren: Imagebroschüren der BKM MANNESMANN AG, Produktlinien- und
Katalogbroschüren, Fachbetriebsprospekte und Verarbeitungsanleitungen.

Dieser Vertrag steht **neben** `LAYOUT-CONTRACT.md`, nicht darüber. Der TDS-Vertrag
regelt technische Datenblätter, die aus der Technik heraus über
`scripts/build_tds.py` erzeugt werden. Broschüren sind ein eigener Dokumenttyp mit
eigener Aufgabe: nicht Kennwerte auf drei Seiten, sondern Argumentation, Bildführung
und Navigation über zwanzig und mehr Seiten.

## Dateien

30 Vorlagen in acht Gruppen, je eine Datei pro Gruppe. Jede öffnet direkt im Browser.

| Datei | Gruppe | Vorlagen |
|:---|:---|:---|
| `Bibliothek.dc.html` | Index | Übersicht, verlinkt alle Gruppen |
| `A-Titelblaetter.dc.html` | Titelblätter | 6 |
| `B-Rahmenseiten.dc.html` | Rahmenseiten | 7 |
| `C-Navigation.dc.html` | Navigation | 3 |
| `D-Textstrecken.dc.html` | Textstrecken | 4 |
| `E-Strecken.dc.html` | Komplette Strecken | 3 |
| `F-Verfahren.dc.html` | Verfahren | 2 |
| `G-Produktseiten.dc.html` | Produktseiten | 3 |
| `H-Fachbetrieb.dc.html` | Fachbetrieb | 2 |

## Maße und Raster

| Invariante | Wert | Grund |
|:---|:---|:---|
| Seitenformat | `210 × 297 mm` | A4, doppelseitig gesetzt |
| Achse außen und innen | `18 mm` | Wie TDS: die eine Fluchtlinie |
| Kopfsteg | `26,7 mm` | Innenseiten |
| Fußsteg | `23,5 mm` | Innenseiten |
| Textbreite | `174 mm` | 210 − 2 × 18 |
| Dreispaltig | `55 mm` Spalte, `4,6 mm` Steg | Fließtextseiten |
| Marginalspalte | `38 mm`, Steg `6 mm` | Textstrecken, Verfahren, Produktseiten |
| Radius | `5 px` | Abweichung, siehe unten |
| Haarlinie | `#e3e1dc` | Wie TDS |

## Titelblatt

| Element | Wert |
|:---|:---|
| Hero-Grafik | `210 × 125 mm` — 118,125 mm für den 16:9-Teil, darunter 6,875 mm Eckerweiterung unten rechts |
| Keyvisual | `42 mm` breit, rechts angeschnitten, `top: 102,416 mm`, dreifarbig |
| Foto | ab `117,46 mm` bis Seitenunterkante, `210 × 179,54 mm`, `object-fit: cover` |
| Logo | `42 mm`, Kopfsteg `18 mm` |
| Siegel (Fachbetriebs-Titel) | `28,16 mm` rund, Kopfsteg `12 mm`, ersetzt das Logo |
| Headline | Unbounded 900, `30 pt`, Zeilenhöhe `1,25`, Laufweite `0` |
| Subheadline | Unbounded 900, `12 pt`, Zeilenhöhe `1,3`, Laufweite `0` |
| Fließtext | TT Norms Pro 400, `12 pt`, Zeilenhöhe `1,25`, Laufweite `−0,015 em`, max. 2 Zeilen |

### Abstände optisch, nicht auf Kastenmaß

Alle drei Textblöcke tragen `text-box: trim-both cap alphabetic`. Die Werte gelten
von Versalhöhe zu Grundlinie, nicht von Kastenkante zu Kastenkante:

- Logo-Unterkante → Versalhöhe Headline: `18 mm`
- Headline-Grundlinie → Versalhöhe Subheadline: `7,87 mm` (95 px bei 300 dpi)
- Subheadline-Grundlinie → Versalhöhe Fließtext: `2,37 mm`

Grund: Ein Kastenabstand trägt den unsichtbaren Vorschub der Schrift mit. Ändert
jemand die Schriftgröße, verschiebt sich der sichtbare Abstand — die Zahl im Code
bedeutet dann nichts mehr. Optisch gemessen ist `18 mm` im Code `18 mm` auf dem Papier.

### Keyvisual-Position

`102,416 mm` ist kein gerundeter Wert. Die linke Oberkante des Pure-Green-Chevrons
liegt bei 73,33 von 464,8 SVG-Einheiten, bei 42 mm Breite also 15,709 mm unter der
Bildoberkante. Nur bei `102,416 mm` trifft sie die Unterkante des 16:9-Bereichs exakt.

### Blitzerschutz

Die Eckerweiterung ist `10 × 10 mm` bei `top: 117,6 mm` — sie ragt also 0,5 mm in
die Hero-Fläche hinein. Zusätzlich beginnt das Foto bei `117,46 mm`, überlappt die
Hero-Grafik damit um 7,54 mm. Zwei Überlappungen, weil an dieser Kante drei Ebenen
zusammentreffen.

Der TDS löst dasselbe Problem über `.tds-band` mit `margin-top: -10px`. Beide Wege
sind gültig; der Broschüren-Weg ist nötig, weil das Hero eine Grafikdatei ist und
kein CSS-Balken.

## Farbflächen

| Rolle | Hex |
|:---|:---|
| Deep Green | `#1c4b42` |
| Transition Green | `#287d4b` |
| Pure Green | `#4daf46` |
| Lime Green | `#b4e717` |
| Sand White | `#f6f5f2` |
| Stone Grey | `#494949` |
| Haarlinie | `#e3e1dc` |

Seitenflächen sind Clean White. **Sand White nur als Element, nie als Seitenfläche** —
im Druck wirkt eine vollflächige Sand-White-Seite schmutzig, am Bildschirm nicht.

**Fachbetriebsbroschüren, die an Endkunden des Betriebs gehen, ersetzen Deep Green
durch Transition Green.** Deep Green bleibt der AG vorbehalten.

Maximal zwei Flächenfarben je Broschüre.

## Icons

Deep-Green-Kasten mit `5 px` Radius, Glyph in Lime Green. Auf dunklem Grund wird
der Kasten Transition Green, damit er sichtbar bleibt.

| Einsatz | Kasten | Glyph |
|:---|:---|:---|
| Kategorie-Opener | `12 mm` | `7,5 mm` |
| Im Text (Merksatz, Profi-Tipp, Linien) | `9,5 mm` | `6 mm` |
| Kontakt- und Impressumblöcke | `6,5 mm` | `3,8 mm` |

Quelle: Phosphor **Bold**, lokale SVGs, als CSS-Maske auf der Glyph-Fläche.
Keine Webfont, kein CDN.

**Abweichung zum TDS:** Dort steht der Glyph frei in einer 20-px-Kachel und trägt
seine Lime-Füllung inline, weil WeasyPrint das Dokument-Stylesheet nicht auf
SVG-Kinder anwendet. Broschüren rendern im Browser, nicht über WeasyPrint — dort
funktioniert die Maske. Die Neun-Dateien-Regel aus `templates/tds/icons/` gilt
für Broschüren nicht; sie brauchen ein größeres Set (Kategorien, Verfahren,
Partnerstufen).

## Texturen

`uploads/a4-texture-*.png`, je `2480 × 3508 px` — 210 × 297 mm bei 300 dpi.
Varianten in Deep Green, Transition Green, Pure Green und Weiß.

**Als `background` der Seite setzen, nicht als absolut positioniertes Bild.** Ein
absolut positioniertes Bild liegt über statisch positioniertem Inhalt, sobald die
Seite kein eigener Stacking Context ist — dann verschwinden Blöcke, die kein
`z-index` tragen.

Abschwächen über eine Farbebene, nicht über `opacity`:

```css
background: linear-gradient(rgba(255,255,255,.8), rgba(255,255,255,.8)),
            #fff url('…') center/cover no-repeat;
```

## Schrift

Unbounded 900 für Headlines, Versalien. TT Norms Pro 400/700 für Fließtext,
Auszeichnungen, Zahlen und Preise.

**Keine Monospace.** Auszeichnungszeilen mit Tracking laufen in TT Norms Pro Bold,
eine halbe Punktgröße größer als der Fließtext — Monospace trägt optisch mehr und
sah im Satz technisch statt redaktionell aus.

## Verhältnis zum TDS-Vertrag

Drei Werte weichen bewusst ab. Sie werden **nicht** angeglichen:

| Punkt | TDS | Broschüre | Grund |
|:---|:---|:---|:---|
| Radius | `3 px` | `5 px` | 3 px sind auf 20-px-Icon-Kacheln und dichte Datentabellen gerechnet. Bei 34-mm-Bildkästen und ganzseitigen Farbfeldern verschwindet der Radius optisch; 5 px sind die Entsprechung im größeren Maßstab. |
| Keyvisual | `10 %` der Blattbreite | `42 mm` = 20 % | Das Titelblatt setzt das Keyvisual als Bildelement, nicht als Randmarke. 42 mm entsprechen der Logobreite und damit einem Fünftel — dieselbe Proportion, in der Logo und Keyvisual zueinander stehen. |
| Icon-Set | genau 9 Dateien | offen | Broschüren decken Kategorien, Verfahren und Partnerstufen ab; ein festes Neuner-Set reicht nicht. |

Übernommen wurden: Achse `18 mm`, Farbwerte, Haarlinie `#e3e1dc`, Phosphor Bold als
lokale SVGs, Grundschriftgröße ohne seitenbezogene Verkleinerung.

## Offen

- Echte Shop-Kategorie-Icons fehlen; `C-Navigation.dc.html` nutzt Phosphor-Platzhalter
- Preise für Mehrfach-Gebinde in `G-Produktseiten.dc.html` stehen als „auf Anfrage"
- Haftungstext in `rahmen-glossar` rechtlich prüfen lassen
- Kein Validator-Skript für Broschüren; die Prüfung liegt bei Redaktion und Review
