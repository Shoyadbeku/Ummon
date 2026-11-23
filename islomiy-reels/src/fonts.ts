import {continueRender, delayRender, staticFile} from 'remotion';

/** Self-hosted fonts (SIL Open Font License): Amiri for Arabic, Cormorant Garamond for Latin. */
export const AMIRI = 'AmiriLocal';
export const CORMORANT = 'CormorantLocal';

const faces: [string, string, string][] = [
  [AMIRI, 'fonts/amiri-700-arabic.woff2', 'U+0600-06FF, U+0750-077F, U+08A0-08FF, U+FB50-FDFF, U+FE70-FEFF, U+0660-0669'],
  [AMIRI, 'fonts/amiri-700-latin.woff2', 'U+0000-00FF, U+2013-2014'],
  [CORMORANT, 'fonts/cormorant-600-latin.woff2', 'U+0000-00FF, U+2013-2014, U+2018-201D'],
  [CORMORANT, 'fonts/cormorant-600-latinext.woff2', 'U+0100-024F, U+02BB-02BC, U+1E00-1EFF'],
];

if (typeof document !== 'undefined') {
  const handle = delayRender('Loading local fonts');
  Promise.all(
    faces.map(([family, file, range]) => {
      const f = new FontFace(family, `url(${staticFile(file)}) format('woff2')`, {unicodeRange: range, weight: '400 800'});
      return f.load().then((loaded) => document.fonts.add(loaded));
    }),
  )
    .then(() => continueRender(handle))
    .catch((e) => {
      console.error(e);
      continueRender(handle);
    });
}
