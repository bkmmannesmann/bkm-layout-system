# BKM Motion – Animationen für die Oberfläche

Bewegung für BKM-Weboberflächen (Website, Support-Cockpit, Konfiguratoren). Gebaut auf drei
Bibliotheken von [Libraries.dev](https://github.com/Jakubantalik/Libraries.dev) (MIT), festgelegt
auf die BKM-Palette, den Markenradius 5 px und die sechs benannten Flächen.

**Nur Bildschirm.** Nichts davon gehört in Datenblatt, Broschüre, Anleitung oder Instagram-Folie.
Die Druckstrecke (`templates/`, `design-system/`) bleibt unberührt.

| Effekt | Grundlage | Wofür |
|:---|:---|:---|
| **Lichtkante** `beam` | `border-beam` 1.4.1, Palette `forest`, Farben statisch | Hauptfeld oder Haupt-CTA hervorheben, arbeitendes Element bei Wartezeit |
| **Orb** `orb` | `thinking-orbs` 0.3.2, Tinte aus der Fläche | Wartezustand mit Text („Analyse läuft …") |
| **Metallring** `metal` | `metal-fx` 2.0.11, nur Preset `silver` | Genau ein Verkaufs-CTA pro Ansicht („Fachbetrieb finden") |

Ansehen: `demo.html` im Browser öffnen (liegt neben `dist/`, lädt die Markenschriften aus `assets/fonts/`).

## Einbinden ohne Build

```html
<script src="ui/animationen/dist/bkm-motion.js"></script>

<button class="btn" data-bkm-beam="pulse-inner" data-bkm-surface="deep">Feuchte-Check starten</button>
<span data-bkm-orb="sucht" data-bkm-label="Sucht passende Verfahren …"></span>
<a class="btn" href="/fachbetrieb" data-bkm-metal data-bkm-surface="deep">Fachbetrieb finden</a>
<span data-bkm-badge>Neu</span>
```

React ist in `dist/bkm-motion.js` mitgebündelt. Die Datei liest die `data-bkm-*`-Attribute nach dem
Laden selbst; mit `<script data-manual>` unterbleibt das. Per Skript:

```js
const kante = BkmMotion.beam(document.querySelector('#suche'), { type: 'line', surface: 'white', active: false });
const ende = BkmMotion.whileWaiting({
  onOrb: (an) => { /* Orb mit Text zeigen oder entfernen */ },
  onBeam: (an) => kante.setActive(an),
});
await fetch(/* … */);
ende();
```

## Einbinden in React

```jsx
import { BkmBeam, BkmOrb, BkmMetal } from './ui/animationen/src/bkm-motion.jsx';

<BkmBeam type="line" surface="white" active={isSearching}><div className="field">…</div></BkmBeam>
<BkmOrb state="prueft" label="Prüft Kennwerte …" surface="white" />
<BkmMetal surface="deep"><a href="/fachbetrieb">Fachbetrieb finden</a></BkmMetal>
```

`npm install` in diesem Ordner holt die drei Pakete; `npm run build` erzeugt `dist/bkm-motion.js` neu.

## Regeln

1. **Fläche statt Farbe.** Jeder Aufruf nennt eine der sechs Flächen (`deep`, `transition`, `pure`,
   `stone`, `sand`, `white`). Sie legt hell/dunkel, Orb-Tinte und Innenfläche des Metallrings fest.
   Farbwerte werden nicht übergeben; eine unbekannte Fläche bricht mit Fehler ab.
2. **Wartezeit entscheidet.** Unter 2 s: nichts. Ab 2 s: Orb mit Text. Ab 3 s: zusätzlich die
   Lichtkante am arbeitenden Element. `BkmMotion.whileWaiting` setzt genau das um.
3. **Sparsam.** Pro Ansicht höchstens ein hervorgehobenes Feld (`pulse-outside`), ein
   hervorgehobener Button (`pulse-inner`) und ein Metallring. Nie in Listen oder Tabellenzeilen.
4. **Typen der Lichtkante:** `pulse-inner` Button oder Karte, die eine Entscheidung erwartet ·
   `pulse-outside` Hauptfeld · `line` Suchfeld nach dem Absenden · `md` Karte, die arbeitet ·
   `sm` kleiner Button.
5. **Orb-Zustände** auf Deutsch: `arbeitet`, `sucht`, `prueft`, `hoert`, `verbindet`, `schreibt`,
   `denkt`, `plant`, `gestaltet`. Größe 20 in der Textzeile, 64 im Avatar-Platz. Immer mit Text,
   außer im Avatar-Platz.
6. **Metall nur Silber.** `chromatic` (Regenbogen) und `gold` passen nicht zur Palette und werden
   von `BkmMetal` nicht angeboten.
7. **Reduzierte Bewegung wird respektiert.** Bei `prefers-reduced-motion: reduce` laufen keine
   Lichtkanten, Orbs und Metallringe stehen still.

## Grenzen und bekannte Abweichungen

- Die Lichtkante nutzt die fest eingebauten Grüntöne der Palette `forest` von border-beam. Sie liegen
  in der Grünfamilie der Marke, sind aber keine Palettenwerte. Mit `staticColors` und `hueRange={0}`
  wandern sie nicht in andere Farbtöne. Exakte Palettenwerte gingen nur über das `css`-Feld der
  Bibliothek und ein Nachbauen ihrer Verlaufsebenen.
- `check_brand_drift.py` meldet für `dist/bkm-motion.js` viele fremde Farben. Das sind die
  Bibliotheken selbst (alle Paletten, Shader-Konstanten), nicht BKM-Code. Geprüft werden `src/` und
  `demo.html`, beide ohne Befund.
- Der Metallring braucht WebGL. Ohne WebGL bleibt der CTA ein normaler Button.
- Nicht übernommen: `voice-glow`, `bot-avatars`, `liquid-gooey`, `img-fx`. Sie passen erst, wenn
  es eine Sprachfunktion, einen Assistenten-Avatar oder KI-Bildgenerierung in der Oberfläche gibt.
  `img-fx` würde dabei die Kennzeichnungspflicht nach `docs/KI-KENNZEICHNUNG.md` nicht ersetzen.

## Lizenzen

`border-beam`, `thinking-orbs`, `metal-fx` stehen unter MIT (© Jakub Antalik). `metal-fx` enthält
Shader von Paper Design unter Apache 2.0. Texte unter `lizenzen/`, Hinweis auch im Kopf von
`dist/bkm-motion.js`. Die Pro-Inhalte von Libraries.dev (Studio, Pro-Presets) sind nicht verwendet.
