import {continueRender, delayRender} from 'remotion';

import {FONT_CSS} from './fonts.generated';

// Fonts (SIL Open Font License) are embedded as data URIs: no fetches, so no render stalls.
if (typeof document !== 'undefined' && !document.getElementById('doc-fonts')) {
  const style = document.createElement('style');
  style.id = 'doc-fonts';
  style.textContent = FONT_CSS;
  document.head.appendChild(style);
  const handle = delayRender('Decoding embedded fonts', {timeoutInMilliseconds: 120000});
  let released = false;
  const release = () => {
    if (!released) {
      released = true;
      continueRender(handle);
    }
  };
  Promise.all(
    ['400 20px Inter', '600 20px Inter', '400 20px Oswald', '700 20px Oswald', '700 20px "Playfair Display"', '900 20px "Playfair Display"'].map((f) => document.fonts.load(f, 'Aa o‘g‘ 2017')),
  ).then(release, release);
  setTimeout(release, 8000);
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
