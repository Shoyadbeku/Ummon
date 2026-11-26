import {FONT_CSS} from './fonts.generated';

// Fonts (SIL Open Font License) are embedded as data URIs: no fetches, nothing to wait on.
// A hidden warm-up element (see Documentary.tsx) forces every face to decode on the first frame.
if (typeof document !== 'undefined' && !document.getElementById('doc-fonts')) {
  const style = document.createElement('style');
  style.id = 'doc-fonts';
  style.textContent = FONT_CSS;
  document.head.appendChild(style);
}

export const sans = 'Inter, sans-serif';
export const condensed = 'Oswald, sans-serif';
export const serif = '"Playfair Display", serif';

export const C = {
  bg: '#07080b',
  ink: '#f4f1ea',
  dim: 'rgba(244,241,234,0.62)',
  red: '#d7262f',
  redDeep: '#7d0f14',
  gold: '#d9b45a',
  panel: 'rgba(8,9,12,0.72)',
};
