import React from 'react';
import {Composition, Still} from 'remotion';
import {NewsVideo} from './NewsVideo';
import {Thumbnail} from './components/Thumbnail';
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
	shots: [{start: 0, end: 12, map: {center: [64.5, 41.3], zoomFrom: 900, zoomTo: 2600, highlight: ['860'], label: "O'ZBEKISTON", pins: [{name: 'Qarshi', lon: 65.79, lat: 38.86, main: true}]}}],
	overlays: [],
	lowerThirds: [],
	words: [],
	ticker: 'Demo ticker',
	outroText: 'Har kuni eng muhim yangiliklar',
	thumbnailText: 'DEMO | 200 → 350',
	coverMedia: null,
	coverSec: 0.7,
};

type AnyProps = Record<string, unknown>;

export const RemotionRoot: React.FC = () => (
	<>
		<Composition
			id="NewsVideo"
			component={NewsVideo as unknown as React.FC<AnyProps>}
			width={1080}
			height={1920}
			fps={30}
			durationInFrames={360}
			defaultProps={demo as unknown as AnyProps}
			calculateMetadata={({props}) => ({durationInFrames: Math.ceil((props as unknown as EpisodeProps).durationSec * 30)})}
		/>
		<Still
			id="Thumbnail"
			width={1080}
			height={1920}
			component={((p: EpisodeProps) => (
				<Thumbnail brand={p.brand} kicker={p.kicker} region={p.region} text={p.thumbnailText} headline={p.headline} media={p.coverMedia} />
			)) as unknown as React.FC<AnyProps>}
			defaultProps={demo as unknown as AnyProps}
		/>
	</>
);
