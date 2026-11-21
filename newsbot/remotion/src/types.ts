// Episode props passed from the Python pipeline (episodes/<id>/render_props.json).
export type Word = {text: string; start: number; end: number; highlight?: boolean};

export type Graphic =
	| {type: 'stat'; value: number; prefix?: string; suffix?: string; label: string; decimals?: number}
	| {type: 'location'; place: string; country: 'uz' | 'world' | string}
	| {type: 'quote'; text: string; who: string}
	| {type: 'list'; title: string; items: string[]};

export type Segment = {
	start: number; // seconds
	end: number;
	media?: string | null; // path relative to the episode public dir
	mediaType?: 'image' | 'video';
	graphic?: Graphic | null;
	lowerThird?: string | null;
};

export type EpisodeProps = {
	brand: string;
	kicker: string; // e.g. "O'ZBEKISTON" / "DUNYO"
	region: 'uz' | 'world';
	breaking: boolean;
	hook: string;
	headline: string;
	dateLabel: string;
	audio: string; // relative path
	music?: string | null;
	durationSec: number;
	segments: Segment[];
	words: Word[];
	ticker: string;
	credits: string;
	outroText: string;
};
