/* ============================================================
   BKM MOTION – Animationen für die BKM-Mannesmann-Oberfläche
   ============================================================
   Drei Effekte aus Libraries.dev (MIT, Jakub Antalik), auf die
   BKM-Palette und die sechs benannten Flächen festgelegt:

     beam   border-beam    Lichtkante an Eingabe, Karte, Button
     orb    thinking-orbs  Wartezustand („Analyse läuft …")
     metal  metal-fx       Metallring an genau einem Verkaufs-CTA

   Zwei Wege, sie zu benutzen:
     React:   import { BkmBeam, BkmOrb, BkmMetal } from './bkm-motion.jsx'
     Ohne:    dist/bkm-motion.js laden, dann data-Attribute oder
              BkmMotion.beam(el, …) / .orb(el, …) / .metal(el, …)

   Regeln: ui/animationen/README.md
   ============================================================ */

import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BorderBeam } from 'border-beam';
import { ThinkingOrb } from 'thinking-orbs';
import { MetalFx, MetalBadge } from 'metal-fx';

/* ── Marke ─────────────────────────────────────────────────── */

/** Palettenwerte aus brand.json. Keine weiteren. */
export const PALETTE = {
  deep: '#1c4b42',
  transition: '#287d4b',
  pure: '#4daf46',
  lime: '#b4e717',
  stone: '#494949',
  sand: '#f6f5f2',
  white: '#ffffff',
};

/** Markenradius (brand.json → radius.value_px). */
export const RADIUS = 5;

/**
 * Die sechs Flächen aus docs/BROSCHUERE-LAYOUT.md. Die Fläche legt fest,
 * ob ein Effekt hell oder dunkel getunt wird und welche Tinte der Orb trägt.
 */
export const SURFACES = {
  deep: { theme: 'dark', ink: PALETTE.lime, bg: PALETTE.deep },
  transition: { theme: 'dark', ink: PALETTE.lime, bg: PALETTE.transition },
  pure: { theme: 'dark', ink: PALETTE.white, bg: PALETTE.pure },
  stone: { theme: 'dark', ink: PALETTE.lime, bg: PALETTE.stone },
  sand: { theme: 'light', ink: PALETTE.transition, bg: PALETTE.sand },
  white: { theme: 'light', ink: PALETTE.transition, bg: PALETTE.white },
};

function surfaceOf(name) {
  const s = SURFACES[name];
  if (!s) {
    throw new Error(
      `BKM Motion: unbekannte Fläche "${name}". Erlaubt: ${Object.keys(SURFACES).join(', ')}`,
    );
  }
  return s;
}

/** Was eine Wartezeit an Effekt bekommt (Regel von Libraries.dev). */
export const WAIT = { orbAfterMs: 2000, beamAfterMs: 3000 };

/* ── Reduzierte Bewegung ───────────────────────────────────── */

const RM_QUERY = '(prefers-reduced-motion: reduce)';

export function prefersReducedMotion() {
  return typeof window !== 'undefined' && !!window.matchMedia && window.matchMedia(RM_QUERY).matches;
}

export function useReducedMotion() {
  const [reduced, setReduced] = useState(prefersReducedMotion);
  useEffect(() => {
    if (!window.matchMedia) return undefined;
    const mq = window.matchMedia(RM_QUERY);
    const on = (e) => setReduced(e.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return reduced;
}

/* ── Effekte als React-Komponenten ─────────────────────────── */

/**
 * Lichtkante in BKM-Grün.
 * type: 'md' (Karte, laufend) · 'sm' (Button, laufend) · 'line' (Suchfeld, Unterkante)
 *       'pulse-inner' (Button hervorheben) · 'pulse-outside' (Eingabe hervorheben)
 */
export function BkmBeam({ type = 'md', surface = 'deep', active = true, strength = 0.85, children, ...rest }) {
  const { theme } = surfaceOf(surface);
  const reduced = useReducedMotion();
  return (
    <BorderBeam
      size={type}
      colorVariant="forest"
      staticColors
      hueRange={0}
      theme={theme}
      borderRadius={RADIUS}
      strength={strength}
      active={active && !reduced}
      {...rest}
    >
      {children}
    </BorderBeam>
  );
}

/** Zustände in BKM-Sprache → Orb-Zustände. */
export const ORB_STATES = {
  arbeitet: 'working',
  sucht: 'searching',
  prueft: 'solving',
  hoert: 'listening',
  verbindet: 'connecting',
  schreibt: 'composing',
  denkt: 'breathing',
  plant: 'weaving',
  gestaltet: 'shaping',
};

/** Wartezustand. size 64 (Avatar-Platz) oder 20 (in der Textzeile). */
export function BkmOrb({ state = 'arbeitet', size = 20, surface = 'white', label, ...rest }) {
  const { theme, ink } = surfaceOf(surface);
  const reduced = useReducedMotion();
  const orbState = ORB_STATES[state] || state;
  return (
    <span
      role="status"
      aria-label={label || undefined}
      style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}
    >
      <ThinkingOrb state={orbState} size={size} theme={theme} color={ink} paused={reduced} {...rest} />
      {label ? <span>{label}</span> : null}
    </span>
  );
}

/**
 * Metallring. Nur für genau einen Verkaufs-CTA pro Ansicht.
 * BKM nutzt ausschließlich die Silber-Tuning (Silber steht in den
 * InDesign-Akzenten der Marke); Chromatic und Gold sind gesperrt.
 */
export function BkmMetal({ variant = 'button', surface = 'deep', strength = 0.7, style, children, ...rest }) {
  const { theme, bg } = surfaceOf(surface);
  const reduced = useReducedMotion();
  // metal-fx malt die Innenfläche mit eigenem Neutralgrau bzw. Weiß.
  // BKM setzt dort die Fläche, auf der der CTA steht.
  return (
    <MetalFx
      variant={variant}
      preset="silver"
      theme={theme}
      strength={strength}
      paused={reduced}
      style={{ background: bg, color: theme === 'dark' ? PALETTE.white : PALETTE.deep, ...style }}
      {...rest}
    >
      {children}
    </MetalFx>
  );
}

export function BkmMetalBadge({ children = 'Neu' }) {
  return <MetalBadge>{children}</MetalBadge>;
}

/* ── Vorhandenes Markup ohne React umhüllen ────────────────── */

/**
 * Setzt ein bestehendes DOM-Element als erstes Kind in den Effekt-Wrapper.
 * Die Bibliotheken lesen Radius und Größe am ersten Kind ab; das Element
 * bleibt dasselbe Objekt mit seinen Listenern.
 */
function Adopt({ node }) {
  const marker = useRef(null);
  useLayoutEffect(() => {
    const m = marker.current;
    m.parentNode.insertBefore(node, m);
  }, [node]);
  return <span ref={marker} hidden />;
}

function wrapperDisplay(el) {
  return getComputedStyle(el).display.startsWith('inline') ? 'inline-block' : 'block';
}

function mountAround(el, render) {
  const host = document.createElement('span');
  host.setAttribute('data-bkm-motion-host', '');
  host.style.display = wrapperDisplay(el) === 'block' ? 'block' : 'inline-block';
  const parent = el.parentNode;
  const next = el.nextSibling;
  parent.insertBefore(host, el);
  const root = createRoot(host);
  const display = wrapperDisplay(el);
  let props = {};
  const paint = () => root.render(render(props, display));
  paint();
  return {
    update(next) {
      props = { ...props, ...next };
      paint();
    },
    destroy() {
      root.unmount();
      parent.insertBefore(el, next && next.parentNode === parent ? next : null);
      host.remove();
    },
  };
}

function beam(el, opts = {}) {
  const ctl = mountAround(el, (p, display) => (
    <BkmBeam {...opts} {...p} style={{ display }}>
      <Adopt node={el} />
    </BkmBeam>
  ));
  return { ...ctl, setActive: (active) => ctl.update({ active }) };
}

function metal(el, opts = {}) {
  return mountAround(el, (p, display) => (
    <BkmMetal {...opts} {...p} style={{ display }}>
      <Adopt node={el} />
    </BkmMetal>
  ));
}

function orb(el, opts = {}) {
  const root = createRoot(el);
  let props = { ...opts };
  const paint = () => root.render(<BkmOrb {...props} />);
  paint();
  return {
    update(next) {
      props = { ...props, ...next };
      paint();
    },
    destroy: () => root.unmount(),
  };
}

function badge(el, opts = {}) {
  const root = createRoot(el);
  root.render(<BkmMetalBadge>{opts.text || el.textContent.trim() || 'Neu'}</BkmMetalBadge>);
  return { destroy: () => root.unmount() };
}

/**
 * Liest data-Attribute:
 *   <button data-bkm-beam="pulse-inner" data-bkm-surface="deep">
 *   <span   data-bkm-orb="sucht" data-bkm-label="Analyse läuft …">
 *   <a      data-bkm-metal data-bkm-surface="deep">
 *   <span   data-bkm-badge>Neu</span>
 *   data-bkm-active="false" startet eine Lichtkante ausgeschaltet.
 */
function autoInit(scope = document) {
  const made = [];
  const surface = (el, fallback) => el.dataset.bkmSurface || fallback;
  scope.querySelectorAll('[data-bkm-beam]').forEach((el) => {
    const ctl = beam(el, {
      type: el.dataset.bkmBeam || 'md',
      surface: surface(el, 'deep'),
      active: el.dataset.bkmActive !== 'false',
    });
    el.bkmMotion = ctl;
    made.push(ctl);
  });
  scope.querySelectorAll('[data-bkm-orb]').forEach((el) => {
    const ctl = orb(el, {
      state: el.dataset.bkmOrb || 'arbeitet',
      size: Number(el.dataset.bkmSize || 20),
      surface: surface(el, 'white'),
      label: el.dataset.bkmLabel,
    });
    el.bkmMotion = ctl;
    made.push(ctl);
  });
  scope.querySelectorAll('[data-bkm-metal]').forEach((el) => {
    const ctl = metal(el, {
      variant: el.dataset.bkmMetal === 'circle' ? 'circle' : 'button',
      surface: surface(el, 'deep'),
    });
    el.bkmMotion = ctl;
    made.push(ctl);
  });
  scope.querySelectorAll('[data-bkm-badge]').forEach((el) => {
    made.push(badge(el));
  });
  return made;
}

/**
 * Wartezeit-Regel als Helfer: Orb erst nach 2 s, Lichtkante erst nach 3 s.
 * Gibt eine Funktion zurück, die beim Ende der Arbeit aufgerufen wird.
 */
function whileWaiting({ onOrb, onBeam }) {
  const t1 = setTimeout(() => onOrb && onOrb(true), WAIT.orbAfterMs);
  const t2 = setTimeout(() => onBeam && onBeam(true), WAIT.beamAfterMs);
  return () => {
    clearTimeout(t1);
    clearTimeout(t2);
    if (onOrb) onOrb(false);
    if (onBeam) onBeam(false);
  };
}

export const BkmMotion = {
  PALETTE,
  SURFACES,
  ORB_STATES,
  WAIT,
  beam,
  orb,
  metal,
  badge,
  autoInit,
  whileWaiting,
  prefersReducedMotion,
};

export default BkmMotion;
