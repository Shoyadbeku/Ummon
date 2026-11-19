import storyboardJson from './data/storyboard.json';
import subtitlesJson from './data/subtitles.json';
import volumeJson from './data/volume.json';

export type Motion =
  | 'pushIn' | 'pullOut' | 'panL' | 'panR' | 'tiltUp' | 'tiltDown' | 'drift' | 'slam'
  | 'shake' | 'desat' | 'dim' | 'flash' | 'rotate' | 'punch';

export type SceneT = {
  id: string; from: number; to: number; image: string; motion: Motion;
  fx: number; fy: number; z0: number; z1: number; note: string;
};
export type OverlayT = {
  from: number; dur: number; type: string; text: string;
  sub?: string; color?: string; pos?: number; num?: string; suffix?: string; times?: number[]; bell?: number;
};
export type SfxT = {from: number; src: string; volume: number};
export type SubWord = {t: string; s: number; e: number; k: '' | 'g' | 'y'};
export type SubPage = {from: number; to: number; hook: boolean; words: SubWord[]};

type SB = {
  fps: number; width: number; height: number; durationInFrames: number; hookFrames: number; titleStart: number;
  voice: string; music: string; hookClips: {fromSec: number; toSec: number; atFrame: number}[];
  scenes: SceneT[]; overlays: OverlayT[]; sfx: SfxT[];
};

export const SB = storyboardJson as unknown as SB;
export const SUBS = (subtitlesJson as unknown as {subs: SubPage[]}).subs;
export const MUSIC_VOL = (volumeJson as {music: number[]; voice: number[]}).music;
export const VOICE_LVL = (volumeJson as {music: number[]; voice: number[]}).voice;

export const COLORS = {
  green: '#6CF0A0',
  greenDeep: '#1FA968',
  gold: '#F3C969',
  white: '#F7F4EE',
  ink: '#05080A',
};
export const FONT_SANS = 'Montserrat, sans-serif';
export const FONT_SERIF = 'Cinzel, serif';

// Layout of the 9:16 frame: the 16:9 photograph lives in a central "band"
export const BAND_TOP = 270;
export const BAND_H = 1340;
export const BAND_CY = BAND_TOP + BAND_H / 2;
