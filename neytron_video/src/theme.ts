import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadOswald} from '@remotion/google-fonts/Oswald';
import {loadFont as loadSerif} from '@remotion/google-fonts/PlayfairDisplay';

export const sans = loadInter('normal', {weights: ['400', '600', '800'], subsets: ['latin', 'latin-ext']}).fontFamily;
export const condensed = loadOswald('normal', {weights: ['400', '600', '700'], subsets: ['latin', 'latin-ext']}).fontFamily;
export const serif = loadSerif('normal', {weights: ['700', '900'], subsets: ['latin', 'latin-ext']}).fontFamily;

export const C = {
  bg: '#07080b',
  ink: '#f4f1ea',
  dim: 'rgba(244,241,234,0.62)',
  red: '#d7262f',
  redDeep: '#7d0f14',
  gold: '#d9b45a',
  panel: 'rgba(8,9,12,0.72)',
};
