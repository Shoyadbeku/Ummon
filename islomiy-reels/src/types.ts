export type Move = 'pushIn' | 'pullOut' | 'panL' | 'panR' | 'rise' | 'sink' | 'drift' | 'punch';
export type Transition = 'dissolve' | 'cut' | 'flash' | 'zoom' | 'dip' | 'whip';
export type Fx =
  | 'cracks'
  | 'shake'
  | 'gold'
  | 'rays'
  | 'dust'
  | 'glow'
  | 'pattern'
  | 'keys'
  | 'lightning';

export type ShotData = {
  id: string;
  start: number;
  end: number;
  src: string;
  kind: 'video' | 'image' | 'gfx';
  file: string | null;
  mv: Move;
  tr: Transition;
  fx: Fx[];
  badge: [string, string] | null;
  note: string;
};
