import React from 'react';
import {Composition} from 'remotion';
import {NewsVideo} from './NewsVideo';
import {EpisodeProps} from './types';

const demo: EpisodeProps = {
	brand: 'POMI.UZ',
	kicker: "O'ZBEKISTON",
	region: 'uz',
	breaking: true,
	hook: 'Toshkentda muhim qaror qabul qilindi',
	headline: 'Demo sarlavha',
	dateLabel: '21-NOYABR, 2026',
	audio: 'audio.wav',
	music: null,
	durationSec: 12,
	segments: [{start: 0, end: 12, media: null, graphic: {type: 'stat', value: 1250, label: 'demo', suffix: ' ta'}, lowerThird: 'Toshkent'}],
	words: [],
	ticker: 'Demo ticker',
	credits: '',
	outroText: 'Har kuni eng muhim yangiliklar',
};

export const RemotionRoot: React.FC = () => (
	<Composition
		id="NewsVideo"
		component={NewsVideo as unknown as React.FC<Record<string, unknown>>}
		width={1080}
		height={1920}
		fps={30}
		durationInFrames={360}
		defaultProps={demo as unknown as Record<string, unknown>}
		calculateMetadata={({props}) => ({durationInFrames: Math.ceil((props as unknown as EpisodeProps).durationSec * 30)})}
	/>
);
