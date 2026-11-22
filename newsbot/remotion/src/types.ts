// Episode props passed from the Python pipeline (episodes/<id>/render_props.json).
export type Word = {text: string; start: number; end: number; highlight?: boolean};

export type Pin = {name: string; lon: number; lat: number; main?: boolean};

export type Graphic =
	| {type: 'stat'; value: number; prefix?: string; suffix?: string; label: string; decimals?: number}
	| {type: 'location'; place: string; country: 'uz' | 'world' | string}
	| {type: 'quote'; text: string; who: string}
	| {type: 'list'; title: string; items: string[]}
	| {type: 'timeline'; title?: string; items: {date: string; text: string; active?: boolean}[]};

// Full-frame animated map (replaces footage for its shot).
export type MapSpec = {
	center: [number, number]; // lon, lat
	zoomFrom: number; // projection scale at start (e.g. 900 = Central Asia, 4000 = region)
	zoomTo: number;
	highlight?: string[]; // ISO 3166-1 numeric ids, e.g. "860" = Uzbekistan
	label?: string; // big country label
	pins?: Pin[];
};

export type Shot = {
	start: number; // seconds
	end: number;
	media?: string | null;
	mediaType?: 'image' | 'video';
	credit?: string | null; // on-screen source credit while visible
	illustrative?: boolean; // footage not from the actual event -> labelled
	speed?: number; // video playback rate (0.6 = slow motion)
	transition?: 'cut' | 'flash' | 'whip' | 'zoom';
	map?: MapSpec | null;
};

export type Overlay = {start: number; end: number; graphic: Graphic};
export type LowerThirdSpec = {start: number; end: number; text: string};
export type Sfx = {src: string; at: number; volume: number};

export type EpisodeProps = {
	brand: string;
	kicker: string;
	region: 'uz' | 'world';
	breaking: boolean;
	hook: string;
	headline: string;
	dateLabel: string;
	audio: string;
	music?: string | null;
	musicVolume?: {t: number; v: number}[]; // ducking envelope
	sfx?: Sfx[];
	durationSec: number;
	shots: Shot[];
	overlays: Overlay[];
	lowerThirds: LowerThirdSpec[];
	words: Word[];
	ticker: string;
	outroText: string;
	thumbnailText: string;
	coverMedia?: string | null;
	coverSec: number;
	// legacy (v1 template)
	segments?: unknown[];
	credits?: string;
};
