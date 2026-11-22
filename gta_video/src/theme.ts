import {continueRender, delayRender, staticFile} from 'remotion';
import fonts from './data/fonts.json';

// Fonts are self-hosted in public/fonts (Montserrat + Anton, SIL Open Font License)
// so rendering works offline and behind proxies.
export const MONT = 'Montserrat';
export const ANTON = 'Anton';

if (typeof document !== 'undefined') {
  const handle = delayRender('Loading fonts');
  Promise.all(
    (fonts as [string, string, string, string][]).map(([family, weight, file, range]) => {
      const ff = new FontFace(family, `url(${staticFile(`fonts/${file}`)}) format('woff2')`, {weight, unicodeRange: range});
      (document.fonts as unknown as {add: (f: FontFace) => void}).add(ff);
      return ff.load();
    }),
  )
    .then(() => continueRender(handle))
    .catch((e) => {
      console.error(e);
      continueRender(handle);
    });
}

export const C = {
  bg: '#06060a',
  ink: '#0b0b12',
  white: '#ffffff',
  yellow: '#FFD23F',
  orange: '#FF8A00',
  pink: '#FF2E63',
  cyan: '#28E0FF',
  green: '#3DFF8A',
  muted: 'rgba(255,255,255,0.62)',
};

export const W = 1080;
export const H = 1920;
export const FPS = 30;

export const accent = (name?: string) =>
  name === 'pink' ? C.pink : name === 'cyan' ? C.cyan : name === 'green' ? C.green : name === 'orange' ? C.orange : C.yellow;
