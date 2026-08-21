# Markenschriften

Diese Dateien sind Teil des Repositories, weil BKM.MANNESMANN AG die Nutzungsrechte hält. Niemand
muss sie lokal installieren — Template und Build finden sie hier.

| Datei | Verwendung im TDS |
|:---|:---|
| `TT_Norms_Pro_Regular.ttf` / `.otf` | Fließtext, Tabellenwerte, Fußzeile |
| `TT_Norms_Pro_Bold.ttf` / `.otf` | Auszeichnung, Parameternamen, Subheadline |
| `Unbounded-Black.ttf` | Headlines und Abschnittstitel |
| `LiberationSans-Regular.ttf` / `LiberationSans-Bold.ttf` | Vollständig eingebettete PDF-Sicherheitsfamilie für den gesamten TDS-Fließtext und alle Textgewichte im Druckmodus |
| `OFL-1.1-Liberation-Sans.txt` | Lizenzhinweis für die mitgelieferten Liberation-Sans-Dateien |

TT Norms Pro und Unbounded nicht ersetzen, nicht konvertieren und nicht durch Webfont-CDN-Einbindungen austauschen. Wird eine
Datei entfernt, setzt WeasyPrint Ersatzschriften und Laufweite sowie Umbruch weichen ab;
`scripts/validate_tds.py` bricht den Release-Build dann ab.

Der gespeicherte TDS-PDF-Export nutzt Liberation Sans für den vollständigen Fließtext, damit kein PDF-Viewer oder Druckertreiber die fehlerhaften TT-Norms-Pro-Trialglyphen nachträglich ausführen kann. Die Bildschirmansicht nutzt weiterhin TT Norms Pro. Diese Druckregel darf erst nach einem reproduzierbar fehlerfreien Speichern und nachfolgenden Drucken mit geprüften Vollversionen entfernt werden. Die beigefügte Lizenzdatei ist Teil der Auslieferung.

**Vor einem Wechsel auf ein öffentliches Repository klären**, ob der Lizenzvertrag die Weitergabe der TT-Norms-Pro- und Unbounded-Dateien deckt. Für die eingebetteten Liberation-Sans-Dateien gilt der mitgelieferte OFL-1.1-Lizenzhinweis.
