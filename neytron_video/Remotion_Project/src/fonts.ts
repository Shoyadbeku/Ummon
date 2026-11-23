import {continueRender, delayRender, staticFile} from 'remotion';
import fonts from './data/fonts.json';

// Locally bundled Google Fonts (OFL) — Inter + Playfair Display, latin & latin-ext (covers o‘ g‘ ’)
const handle = delayRender('Loading fonts');
Promise.all(
  fonts.map((f) => {
    const face = new FontFace(f.family, `url(${staticFile('fonts/' + f.file)}) format('woff2')`, {
      weight: f.weight,
      unicodeRange: f.range,
    });
    return face.load().then((loaded) => document.fonts.add(loaded));
  }),
).then(() => continueRender(handle));

export const FONT = '"Inter", Arial, sans-serif';
export const SERIF = '"Playfair Display", Georgia, serif';
