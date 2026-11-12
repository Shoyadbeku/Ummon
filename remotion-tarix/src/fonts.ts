import {continueRender, delayRender, staticFile} from 'remotion';
import faces from './fontfaces.json';

// Shriftlar public/fonts ichida — internet kerak emas
export const serif = '"Playfair Display", Georgia, serif';
export const sans = 'Montserrat, Arial, sans-serif';

if (typeof document !== 'undefined' && !document.getElementById('local-fonts')) {
  const style = document.createElement('style');
  style.id = 'local-fonts';
  style.innerHTML = faces
    .map(
      (f) =>
        `@font-face{font-family:'${f.family}';font-style:${f.style};font-weight:${f.weight};font-display:block;src:url('${staticFile(f.file)}') format('woff2');unicode-range:${f.range};}`
    )
    .join('\n');
  document.head.appendChild(style);
  const handle = delayRender('Shriftlar yuklanmoqda');
  Promise.all(
    faces.map((f) => document.fonts.load(`${f.style} ${f.weight} 40px "${f.family}"`, 'Aa‘ʻ'))
  )
    .catch(() => undefined)
    .then(() => continueRender(handle));
}
