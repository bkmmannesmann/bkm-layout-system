# TDS-Änderung: Prüfliste

## Art der Änderung

- [ ] Neues Datenblatt oder neue Produktrevision
- [ ] Korrektur eines bestehenden Produktinhalts
- [ ] Änderung am TDS-Template, Design-System oder Build-Ablauf

## Inhalt und Nachweise

- [ ] Alle technischen Kennwerte stammen aus einer bestätigten Quellinformation.
- [ ] Verbrauch, Zeitketten, Einheiten, Normen und Artikelnummern wurden nach `docs/REDAKTIONSSTANDARD.md` geprüft.
- [ ] Vorteile und Eigenschaften sind getrennt, sachlich und BKM-konform formuliert.
- [ ] Revision und Ausgabe entsprechen der Änderungsart.
- [ ] Der technische Freigabestatus ist im vorgesehenen Freigaberegister dokumentiert.

## Assets und Layout

- [ ] Das Produktbild liegt als freigestelltes PNG unter `assets/images/products/` vor.
- [ ] Das Produktbild wurde visuell auf transparenten Hintergrund und ausreichende Qualität geprüft.
- [ ] Der korrekte Home-Line- oder Pro-Line-Badge ist gesetzt.
- [ ] Die lokale PDF-Prüfung erfolgte mit den lizenzierten BKM-Schriften.

## Build-Nachweis

- [ ] `python3 scripts/validate_tds.py <content.json> --release` läuft fehlerfrei.
- [ ] `python3 scripts/build_tds.py --content <content.json> --release` läuft fehlerfrei.
- [ ] Die erzeugte PDF hat exakt drei veröffentlichte Seiten.
- [ ] Es gibt keine `[ANGABE FEHLT: …]`- oder `[ZU PRÜFEN: …]`-Marker.
- [ ] Der `review`-Block wurde für die Release-Fassung entfernt.

## Review

- [ ] Technische Prüfung
- [ ] Nachweisprüfung / Qualitätsmanagement
- [ ] Freigabe Leitung Technik
- [ ] Satz- und Sichtprüfung
