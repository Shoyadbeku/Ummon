// Barcha vaqtlar soniyada. Manba: Whisper large-v3 so‘z darajasidagi vaqt belgilari
// (faster-whisper, word_timestamps=True) + qo‘lda tozalangan o‘zbekcha matn.
export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const AUDIO_END = 37.1; // original ovoz uzunligi
export const TOTAL_SEC = 38.4; // 1.3 s musiqiy outro
export const DURATION = Math.round(TOTAL_SEC * FPS);

export const f = (sec: number) => Math.round(sec * FPS);

export type Word = {w: string; s: number; e: number};
export type Sentence = {start: number; end: number; text: string; words: Word[]};

export const SENTENCES: Sentence[] = [
	{
		start: 0.0, end: 5.32,
		text: 'Tasavvur qiling, bir bloger videosi uchun haqiqiy Squid Game maydonini qurdirgan.',
		words: [
			{w: 'Tasavvur', s: 0.0, e: 0.76}, {w: 'qiling,', s: 0.76, e: 1.04}, {w: 'bir', s: 1.12, e: 1.58},
			{w: 'bloger', s: 1.58, e: 2.12}, {w: 'videosi', s: 2.12, e: 2.7}, {w: 'uchun', s: 2.7, e: 2.92},
			{w: 'haqiqiy', s: 2.92, e: 3.34}, {w: 'Squid', s: 3.34, e: 3.74}, {w: 'Game', s: 3.74, e: 4.26},
			{w: 'maydonini', s: 4.26, e: 4.86}, {w: 'qurdirgan.', s: 4.86, e: 5.32},
		],
	},
	{
		start: 5.72, end: 9.48,
		text: 'Bu inson — MrBeast, asl ismi Jimmy Donaldson.',
		words: [
			{w: 'Bu', s: 5.72, e: 6.14}, {w: 'inson', s: 6.14, e: 6.42}, {w: 'MrBeast,', s: 6.42, e: 7.4},
			{w: 'asl', s: 7.6, e: 8.1}, {w: 'ismi', s: 8.1, e: 8.38}, {w: 'Jimmy', s: 8.38, e: 8.7},
			{w: 'Donaldson.', s: 8.7, e: 9.48},
		],
	},
	{
		start: 9.66, end: 15.26,
		text: '2021-yilda u mashhur Koreya serialidan ilhomlangan ulkan musobaqa tashkil qildi.',
		words: [
			{w: '2021-yilda', s: 9.66, e: 11.22}, {w: 'u', s: 11.22, e: 11.3}, {w: 'mashhur', s: 11.3, e: 11.78},
			{w: 'Koreya', s: 11.78, e: 12.08}, {w: 'serialidan', s: 12.08, e: 12.62}, {w: 'ilhomlangan', s: 12.62, e: 13.3},
			{w: 'ulkan', s: 13.3, e: 14.04}, {w: 'musobaqa', s: 14.04, e: 14.62}, {w: 'tashkil', s: 14.62, e: 14.96},
			{w: 'qildi.', s: 14.96, e: 15.26},
		],
	},
	{
		start: 15.3, end: 17.92,
		text: 'Unda 456 nafar ishtirokchi qatnashdi.',
		words: [
			{w: 'Unda', s: 15.3, e: 15.96}, {w: '456', s: 15.96, e: 16.32}, {w: 'nafar', s: 16.32, e: 17.02},
			{w: 'ishtirokchi', s: 17.02, e: 17.36}, {w: 'qatnashdi.', s: 17.36, e: 17.92},
		],
	},
	{
		start: 18.06, end: 21.56,
		text: 'G‘olib uchun 456 000 dollar mukofot belgilandi.',
		words: [
			{w: 'G‘olib', s: 18.06, e: 18.7}, {w: 'uchun', s: 18.7, e: 18.98}, {w: '456 000', s: 18.98, e: 20.28},
			{w: 'dollar', s: 20.28, e: 20.58}, {w: 'mukofot', s: 20.58, e: 21.1}, {w: 'belgilandi.', s: 21.1, e: 21.56},
		],
	},
	{
		start: 21.74, end: 26.92,
		text: 'MrBeast’ning aytishicha, loyiha uchun taxminan 3,5 million dollar sarflangan.',
		words: [
			{w: 'MrBeast’ning', s: 21.74, e: 22.62}, {w: 'aytishicha,', s: 22.62, e: 23.04}, {w: 'loyiha', s: 23.04, e: 23.58},
			{w: 'uchun', s: 23.58, e: 23.92}, {w: 'taxminan', s: 23.92, e: 24.4}, {w: '3,5', s: 24.4, e: 25.08},
			{w: 'million', s: 25.08, e: 26.14}, {w: 'dollar', s: 26.14, e: 26.36}, {w: 'sarflangan.', s: 26.36, e: 26.92},
		],
	},
	{
		start: 27.12, end: 29.92,
		text: 'Eng qizig‘i, bu oddiy YouTube video edi.',
		words: [
			{w: 'Eng', s: 27.12, e: 27.56}, {w: 'qizig‘i,', s: 27.56, e: 27.96}, {w: 'bu', s: 27.96, e: 28.38},
			{w: 'oddiy', s: 28.38, e: 28.82}, {w: 'YouTube', s: 28.82, e: 29.14}, {w: 'video', s: 29.14, e: 29.56},
			{w: 'edi.', s: 29.56, e: 29.92},
		],
	},
	{
		start: 30.0, end: 34.5,
		text: 'Ammo uning ishlab chiqarish ko‘lami ayrim televizion loyihalarnikidan ham katta bo‘lgan.',
		words: [
			{w: 'Ammo', s: 30.0, e: 30.38}, {w: 'uning', s: 30.38, e: 30.72}, {w: 'ishlab chiqarish', s: 30.72, e: 31.42},
			{w: 'ko‘lami', s: 31.42, e: 31.76}, {w: 'ayrim', s: 31.76, e: 32.38}, {w: 'televizion', s: 32.38, e: 32.94},
			{w: 'loyihalarnikidan', s: 32.94, e: 33.46}, {w: 'ham', s: 33.46, e: 33.7}, {w: 'katta', s: 33.7, e: 34.22},
			{w: 'bo‘lgan.', s: 34.22, e: 34.5},
		],
	},
	{
		start: 34.58, end: 36.76,
		text: 'Siz shunday o‘yinda qatnasharmidingiz?',
		words: [
			{w: 'Siz', s: 34.58, e: 35.18}, {w: 'shunday', s: 35.18, e: 35.62}, {w: 'o‘yinda', s: 35.62, e: 35.9},
			{w: 'qatnasharmidingiz?', s: 35.9, e: 36.76},
		],
	},
];

// Musiqa: Mixkit "Epic Games" (#76), 6.833 s dan boshlab kesilgan → birinchi beat t=0 da.
export const BEAT = 0.5805; // ≈103.4 BPM
export const beatAt = (t: number) => {
	const k = t / BEAT;
	const frac = k - Math.floor(k);
	return frac; // 0..1 beat fazasi
};

// Ovoz faol bo‘lgan oraliqlar (musiqa ducking uchun)
export const SPEECH: Array<[number, number]> = (() => {
	const all = SENTENCES.flatMap((s) => s.words.map((w) => [w.s, w.e] as [number, number]));
	const merged: Array<[number, number]> = [];
	for (const [s, e] of all) {
		const last = merged[merged.length - 1];
		if (last && s - last[1] < 0.35) last[1] = Math.max(last[1], e);
		else merged.push([s, e]);
	}
	return merged;
})();

// Sahnalar (shot list) — kesimlar so‘z vaqtlariga bog‘langan
export const SHOTS = {
	hookEye: [0, 0.9],
	vlogger: [0.9, 2.7],
	guards: [2.7, 4.26],
	build: [4.26, 5.72],
	mrbeast: [5.72, 7.55],
	idcard: [7.55, 9.62],
	year: [9.62, 11.22],
	globe: [11.22, 12.62],
	flag: [12.62, 13.3],
	contest: [13.3, 15.3],
	players: [15.3, 18.02],
	winner: [18.02, 18.98],
	prize: [18.98, 21.7],
	quote: [21.7, 23.9],
	budget: [23.9, 27.1],
	twist: [27.1, 28.38],
	youtube: [28.38, 30.0],
	crew: [30.0, 31.76],
	split: [31.76, 34.56],
	doll: [34.56, 35.62],
	question: [35.62, TOTAL_SEC],
} as const;

// SFX cue'lari: [vaqt (s), fayl, ovoz balandligi]
export const SFX: Array<[number, string, number]> = [
	[0.0, 'sfx/2908.mp3', 0.55], // trailer impact — hook
	[0.0, 'sfx/2950.mp3', 0.22], // glitch text
	[0.86, 'sfx/1492.mp3', 0.3], // whoosh → vlogger
	[1.58, 'sfx/1133.mp3', 0.35], // kamera shutter (bloger)
	[2.66, 'sfx/1490.mp3', 0.3], // whoosh → guards
	[3.34, 'sfx/788.mp3', 0.32], // impact on "Squid Game"
	[4.22, 'sfx/1486.mp3', 0.22], // tunnel whoosh → build
	[5.3, 'sfx/790.mp3', 0.28], // riser → MrBeast reveal
	[6.42, 'sfx/2903.mp3', 0.4], // impact "MrBeast"
	[7.52, 'sfx/3005.mp3', 0.35], // pop → ID card
	[8.38, 'sfx/2364.mp3', 0.25], // pop name
	[9.58, 'sfx/1492.mp3', 0.28], // whoosh → year
	[9.7, 'sfx/1053.mp3', 0.18], // ticking counter
	[11.18, 'sfx/1486.mp3', 0.25], // whoosh → globe
	[12.4, 'sfx/2357.mp3', 0.3], // pin pop
	[13.28, 'sfx/2918.mp3', 0.38], // whoosh impact → contest
	[15.26, 'sfx/1490.mp3', 0.25], // whoosh → players
	[15.95, 'sfx/1054.mp3', 0.2], // electric counter
	[17.9, 'sfx/1143.mp3', 0.3], // deep impact → winner
	[18.98, 'sfx/1989.mp3', 0.4], // money bag drop
	[20.2, 'sfx/1999.mp3', 0.35], // coin prize
	[21.66, 'sfx/1492.mp3', 0.25],
	[23.86, 'sfx/645.mp3', 0.2], // synth riser → budget
	[25.08, 'sfx/1936.mp3', 0.35], // coin win at "million"
	[27.06, 'sfx/2951.mp3', 0.3], // glitch → twist
	[28.34, 'sfx/1490.mp3', 0.25],
	[29.96, 'sfx/1133.mp3', 0.3], // clapper/shutter
	[31.72, 'sfx/1486.mp3', 0.25], // split
	[33.66, 'sfx/2903.mp3', 0.35], // "katta" impact
	[34.5, 'sfx/498.mp3', 0.5], // heartbeat — doll
	[35.58, 'sfx/2908.mp3', 0.35], // final impact
	[36.8, 'sfx/2357.mp3', 0.3], // poll pop
	[37.1, 'sfx/2357.mp3', 0.25],
];
