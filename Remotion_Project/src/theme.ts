import {ensureFonts} from './fonts';
ensureFonts();
export const SANS = "'Inter', sans-serif";
export const SERIF = "'Playfair Display', serif";

export const FPS = 30;
export const W = 1920;
export const H = 1080;

export const C = {
	ink: '#0b0d10',
	panel: 'rgba(12,14,18,0.82)',
	text: '#f4f1ea',
	muted: '#a9a59c',
	gold: '#d8b46a',
	red: '#c8312b',
	line: 'rgba(244,241,234,0.18)',
	// claim status colors
	fact: '#5fb98a',
	investigation: '#e0a63a',
	unconfirmed: '#e05252',
};

export type Status = 'fact' | 'investigation' | 'unconfirmed';
export const STATUS_LABEL: Record<Status, string> = {
	fact: 'RASMIY FAKT',
	investigation: 'JURNALISTIK SURISHTIRUV',
	unconfirmed: 'TASDIQLANMAGAN DA’VO',
};

export const s = (sec: number) => Math.round(sec * FPS);
