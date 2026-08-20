# Markenschriften

Diese Dateien sind Teil des Repositories, weil BKM.MANNESMANN AG die Nutzungsrechte hält. Niemand
muss sie lokal installieren — Template und Build finden sie hier.

| Datei | Verwendung im TDS |
|:---|:---|
| `TT_Norms_Pro_Regular.ttf` / `.otf` | Fließtext, Tabellenwerte, Fußzeile |
| `TT_Norms_Pro_Bold.ttf` / `.otf` | Auszeichnung, Parameternamen, Subheadline |
| `Unbounded-Black.ttf` | Headlines und Abschnittstitel |

Nicht ersetzen, nicht konvertieren, nicht durch Webfont-CDN-Einbindungen austauschen. Wird eine
Datei entfernt, setzt WeasyPrint Ersatzschriften und Laufweite sowie Umbruch weichen ab;
`scripts/validate_tds.py` bricht den Release-Build dann ab.

**Vor einem Wechsel auf ein öffentliches Repository klären**, ob der Lizenzvertrag die
Weitergabe der Schriftdateien deckt. In einem privaten Repository ist die Ablage unkritisch.
