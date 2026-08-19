# Produktbilder für technische Datenblätter

Lege pro Datenblatt ein freigestelltes Produktbild als PNG mit transparentem Hintergrund ab. Der Dateiname entspricht dem Produkt-Slug im zugehörigen `content/tds-<produkt-slug>/content.json`, beispielsweise `assets/images/products/novusan.png`.

Die Layoutfläche im TDS beträgt 230 × 312 Pixel. Das Bild darf davon abweichende Pixelmaße haben, muss aber ein transparentes PNG sein und wird proportional innerhalb dieser Fläche dargestellt. Bilder mit weißem oder grauem Hintergrund sind nicht zulässig, weil der Hintergrund im PDF sichtbar würde.

Diese Assets sind vor einem Release bereitzustellen. Der Release-Build blockiert bei fehlendem Produktbild.
