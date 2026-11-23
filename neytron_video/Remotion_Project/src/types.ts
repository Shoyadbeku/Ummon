export type SceneKind = 'video' | 'photo' | 'title' | 'stat' | 'compare' | 'statement';

export interface Scene {
  id: string;
  /** Start / end in seconds on the original voice-over timeline */
  start: number;
  end: number;
  kind: SceneKind;
  /** Media path relative to /public (video/photo) */
  src?: string;
  /** Offset (s) inside the source video to start playing from */
  srcStart?: number;
  /** Playback rate for video sources (slow-motion for long holds) */
  rate?: number;
  /** Ken Burns direction for photos/videos */
  move?: 'in' | 'out' | 'left' | 'right' | 'up' | 'down';
  /** Focus point for zoom, 0..1 */
  focusX?: number;
  focusY?: number;
  /** Source attribution shown on screen */
  credit?: string;
  /** Small on-screen label (e.g. object name / what is shown) */
  label?: string;
  /** Title card / statement text */
  title?: string;
  subtitle?: string;
  /** Stat card */
  value?: number;
  decimals?: number;
  prefix?: string;
  unit?: string;
  note?: string;
  /** Compare scene: two items */
  left?: {src?: string; label: string; value?: string};
  right?: {src?: string; label: string; value?: string};
  /** Background media for stat/statement/title scenes */
  bg?: string;
}

export interface Cue {
  start: number;
  end: number;
  text: string;
  words: {w: string; s: number; e: number}[];
}
