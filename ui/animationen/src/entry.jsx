/* Einstieg für dist/bkm-motion.js: React wird mitgebündelt, damit die Datei
   auf jeder Seite ohne Build läuft. Liest data-bkm-* nach dem Laden selbst. */
import BkmMotion from './bkm-motion.jsx';

if (typeof document !== 'undefined' && !document.currentScript?.hasAttribute('data-manual')) {
  const go = () => BkmMotion.autoInit(document);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go);
  else go();
}

export default BkmMotion;
