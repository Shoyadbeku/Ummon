import {staticFile} from 'remotion';

export const FPS = 30;
export const C = {
  navy: '#07101F',
  navy2: '#0E1D36',
  ink: '#F4F1EA',
  dim: 'rgba(244,241,234,0.66)',
  gold: '#F2C14E',
  teal: '#1FB59F',
  red: '#E5484D',
  blue: '#3A8DFF',
  line: 'rgba(244,241,234,0.18)',
};
export const HEAD = 'Montserrat, sans-serif';
export const BODY = 'Inter, sans-serif';

// Fonts: Montserrat + Inter (OFL). Installed system-wide for rendering (see README);
// the @font-face rule prefers the local() system font and falls back to the bundled file.
if (typeof document !== 'undefined' && !(window as any).__fontsQueued) {
  (window as any).__fontsQueued = true;
  const style = document.createElement('style');
  style.textContent = `
    @font-face { font-family: 'Montserrat'; src: local('Montserrat'), url('${staticFile('fonts/Montserrat.ttf')}') format('truetype'); font-weight: 100 900; }
    @font-face { font-family: 'Inter'; src: local('Inter'), url('${staticFile('fonts/Inter.ttf')}') format('truetype'); font-weight: 100 900; }`;
  document.head.appendChild(style);
}
