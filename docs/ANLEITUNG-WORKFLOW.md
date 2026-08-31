# Ablauf: neue Verarbeitungsanleitung

Wie aus einem Textdokument und den passenden Bildern eine druckfähige
Verarbeitungsanleitung wird. Ergänzt den [Layoutvertrag](ANLEITUNG-LAYOUT.md)
um die praktische Arbeit; der Datenvertrag steht maschinenlesbar in
[`anleitung-content.schema.json`](anleitung-content.schema.json).

> **Grundsatz:** Eine Verarbeitungsanleitung ist eine technische Anweisung.
> Sie ersetzt weder das technische Datenblatt noch das Sicherheitsdatenblatt —
> beide bleiben die verbindliche Quelle. Unbelegte Angaben bleiben sichtbar
> markiert und blockieren die Veröffentlichung.

## Was du lieferst

| | |
|---|---|
| **Text** | Formlos. Word, Mail oder Notiz. Er muss die vier Rubriken abdecken: Vorteile, Vorbereitung, Anleitung, Nacharbeit. |
| **Bilder** | Im Format **16:9**. Pro Anleitungsseite höchstens vier. Wer keins hat, beschreibt das fehlende Motiv — daraus wird eine beschriftete Platzhalterfläche. |
| **Produkt** | Name und Linie. Pro Line oder Home Line; die Zuordnung ist fest (Produkte mit *Novu* im Namen gehören zur Home Line). |

Der Text braucht keine Struktur mitzubringen. Die Rubrikenfolge steht fest
und ist an sieben freigegebenen Anleitungen abgelesen — sie wird nicht je
Produkt neu entschieden.

## Was daraus wird

```
content/anleitung-<produkt-slug>/content.json     der Inhalt
uploads/<motiv>.jpg                               die Bilder
output/anleitung/anleitung-<slug>.pdf             das Ergebnis
```

Der Produkt-Slug wird kleingeschrieben und nutzt Bindestriche:
`content/anleitung-hz250pro/`, `content/anleitung-novusan/`.

## Der Weg

**1. Von einer freigegebenen Referenz kopieren**, nicht von einer leeren
Vorlage. Sieben stehen bereit — nimm die strukturell nächste:

| Ordner | Produkt | Linie | Passt für |
|---|---|---|---|
| `anleitung-hz250pro` | BKM HZ 250 Pro | Pro | Injektion mit Verbrauchsformeln und Bohrlochmustern |
| `anleitung-hzc` | BKM HZ-C | Pro | Injektionscreme, kurzer Ablauf |
| `anleitung-sp-express` | BKM SP Express | Pro | Systemaufbau in Lagen mit Verbrauch je Lage |
| `anleitung-rd` | BKM RD ReparaturDicht | Pro | Streichbare Beschichtung |
| `anleitung-novusan` | Novusan | Home | Injektion mit Flaschen, zwei Sperrarten |
| `anleitung-novusticks` | NovuSticks | Home | Feststoff, Verbrauchstabelle |
| `anleitung-novuprotect` | NovuProtect | Home | Beschichtung in zwei Aufträgen |

```bash
cp -R content/anleitung-hz250pro content/anleitung-neues-produkt
```

**2. Werte ersetzen.** Nur `content.json`; HTML und CSS bleiben unberührt.
`issued` trägt das Datum, an dem die Fassung erzeugt wird. Alles, was nicht
belegt ist, bekommt einen sichtbaren Marker:

```
[ANGABE FEHLT: Bohrerdurchmesser in mm – bitte fachlich bestätigen.]
```

**3. Bilder ablegen** unter `uploads/`, im Format 16:9. Im Content wird
darauf mit `image` verwiesen; solange keins vorliegt, beschreibt
`image_needed` das Motiv.

**4. Prüfen und bauen.**

```bash
python3 scripts/validate_anleitung.py content/anleitung-neues-produkt/content.json
python3 scripts/build_anleitung.py    content/anleitung-neues-produkt/content.json
```

Der Validator liest den Inhalt, der Bau liest das Ergebnis. Beides ist
nötig: Was zählbar ist, fällt im PDF nicht auf — und ein abgeschnittener
Absatz fällt nur dort auf.

**5. Umbruch nachziehen.** Jede Seite muss ihren Inhalt fassen. Läuft eine
über, meldet der Bau es; dann wandert der letzte Abschnitt eine Seite
weiter, und `page_total` wird nachgezogen.

**6. Freigabe.** `--release` an beide Aufrufe. Offene Angaben blockieren
dann die Ausgabe.

## Was geprüft wird

**Am Inhalt** (`validate_anleitung.py`) — Pflichtfelder, Rubrikenfolge,
Linie gegen Badge, Seitenzählung, Länge der Subheadline, Anzahl der Vorteile
und Abbildungen, Datumsformat, Bild- und Iconverweise am Dateisystem.

**Am Ergebnis** (`build_anleitung.py`) — eingebettete Schriften,
Vollständigkeit ab drei Zeichen, Seitenzahl, Paginierung, Abbildungen je
Seite, Display-Größen gegen `type_scale.anleitung`.

Beide Wege enden mit `exit 1`, wenn etwas nicht stimmt. Der Bau führt
Titelblatt und Innenteil zu einer Datei zusammen und bricht ab, wenn das
Titelblatt beanstandet wird.

## Grenzen, die aus dem Layout kommen

| | |
|---|---|
| Subheadline auf dem Titel | höchstens zwei Zeilen, rund 70 Zeichen |
| Vorteile | zwei bis vier |
| Abbildungen je Anleitungsseite | vier |
| Anleitungsseiten | eine bis vier |
| Werkzeug- und Sicherheitsliste | höchstens zwölf Einträge |

Diese Zahlen sind gemessen, nicht gesetzt: Sie ergeben sich aus 259 mm
Satzhöhe und 84,7 mm Spaltenbreite. Wer sie überschreitet, bekommt keinen
Fehler im Layout, sondern abgeschnittenen Text — deshalb prüfen beide Wege
darauf.

## Rollen

| Rolle | Verantwortung |
|---|---|
| Redaktion | Strukturiert den Text, formuliert in BKM-Sprache, markiert offene Angaben. |
| Anwendungstechnik | Prüft Verarbeitungsschritte, Kennwerte, Verbrauch und Plausibilität. |
| Qualitätsmanagement | Prüft Normen, Sicherheitsangaben und den Verweis auf das Sicherheitsdatenblatt. |
| Leitung Technik | Erteilt die fachliche Freigabe. |
| Satz | Führt den Release-Build aus und prüft die PDF-Ausgabe. |
