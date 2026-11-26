export type Fit = 'cover' | 'contain';

/** Ken Burns move: scale and focal offset (in % of frame) from start to end. */
export type Move = {s0: number; s1: number; x0?: number; y0?: number; x1?: number; y1?: number};

export type Pin = {name: string; lon: number; lat: number; main?: boolean};

export type Visual =
  | {kind: 'video'; file: string; from: number; fit?: Fit; move?: Move; rate?: number}
  | {kind: 'photo'; file: string; fit?: Fit; move?: Move; depth?: boolean}
  | {kind: 'map'; center: [number, number]; scale0: number; scale1: number; pins: Pin[]; arcs?: [string, string][]; caption?: string}
  | {kind: 'card'; kicker?: string; title: string; sub?: string; tone?: 'red' | 'dark'}
  | {kind: 'date'; date: string; place?: string}
  | {kind: 'tree'; focus: string[]; dead?: string[]}
  | {kind: 'timeline'; items: {year: string; label: string}[]; active: number}
  | {kind: 'stat'; value: number; prefix?: string; suffix?: string; label: string; decimals?: number}
  | {kind: 'question'; lines: string[]}
  | {kind: 'split'; left: {file: string; name: string; move?: Move}; right: {file: string; name: string; move?: Move}; mid?: string}
  | {kind: 'molecule'}
  | {kind: 'cctv'; title: string; lines: string[]};

/** On-screen attribution for any third-party footage/photo in a scene. */
export type Source = {label: string; license: string};

export type Scene = {
  start: number; // seconds in the narration
  end: number;
  v: Visual;
  source?: Source;
  lower?: {name: string; role: string};
  /** Why this visual is here (storyboard rationale). */
  note: string;
};
