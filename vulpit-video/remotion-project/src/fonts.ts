import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

const faces: [string, string, string][] = [
  ['Montserrat', 'montserrat-latin-600-normal.woff2', '600'],
  ['Montserrat', 'montserrat-latin-800-normal.woff2', '800'],
  ['Montserrat', 'montserrat-latin-900-normal.woff2', '900'],
  ['Cinzel', 'cinzel-latin-700-normal.woff2', '700'],
  ['Cinzel', 'cinzel-latin-900-normal.woff2', '900'],
];
export const fontsReady = Promise.all(
  faces.map(([family, file, weight]) =>
    loadFont({family, url: staticFile(`fonts/${file}`), weight, format: 'woff2'}),
  ),
);
