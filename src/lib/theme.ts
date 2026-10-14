import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

/**
 * Shriftlar lokal (public/fonts) — internetga bog'liq emas, render barqaror.
 * Montserrat — sarlavhalar, Inter — matn. Ikkalasi ham SIL OFL litsenziyasida.
 */
const FONTS: [family: string, file: string, weight: string][] = [
  ['Montserrat', 'montserrat-latin-600-normal.woff2', '600'],
  ['Montserrat', 'montserrat-latin-700-normal.woff2', '700'],
  ['Montserrat', 'montserrat-latin-800-normal.woff2', '800'],
  ['Montserrat', 'montserrat-latin-900-normal.woff2', '900'],
  ['Inter', 'inter-latin-400-normal.woff2', '400'],
  ['Inter', 'inter-latin-500-normal.woff2', '500'],
  ['Inter', 'inter-latin-600-normal.woff2', '600'],
  ['Inter', 'inter-latin-700-normal.woff2', '700'],
];

for (const [family, file, weight] of FONTS) {
  loadFont({family, url: staticFile(`fonts/${file}`), weight, display: 'block'}).catch((err) => {
    console.error(`Shrift yuklanmadi: ${file}`, err);
  });
}

export const FONT_DISPLAY = 'Montserrat, "Noto Color Emoji", sans-serif';
export const FONT_BODY = 'Inter, "Noto Color Emoji", sans-serif';

export const COLORS = {
  bg0: '#070A14',
  bg1: '#0D1326',
  panel: 'rgba(255,255,255,0.06)',
  panelBorder: 'rgba(255,255,255,0.14)',
  text: '#F8FAFC',
  muted: '#94A3B8',
  saffron: '#FF8A3D',
  amber: '#F59E0B',
  cyan: '#22D3EE',
  violet: '#8B5CF6',
  pink: '#EC4899',
  red: '#EF4444',
  cold: '#38BDF8',
  green: '#10B981',
};

export const GRADIENT_TEXT = (a: string, b: string) => ({
  backgroundImage: `linear-gradient(100deg, ${a} 0%, ${b} 100%)`,
  WebkitBackgroundClip: 'text' as const,
  backgroundClip: 'text' as const,
  color: 'transparent',
});
