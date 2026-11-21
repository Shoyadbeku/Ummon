import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {EpisodeProps} from './types';
import {MediaLayer} from './components/MediaLayer';
import {Captions} from './components/Captions';
import {GraphicCard, Headline, Intro, LowerThird, Outro, ProgressBar, Ticker, TopBar} from './components/Overlays';

export const INTRO_SEC = 2.6;
export const OUTRO_SEC = 2.5;

export const NewsVideo: React.FC<EpisodeProps> = (p) => {
	const {fps, durationInFrames} = useVideoConfig();
	const f = (s: number) => Math.round(s * fps);
	const outroFrom = durationInFrames - f(OUTRO_SEC);
	return (
		<AbsoluteFill style={{backgroundColor: '#0B0F17'}}>
			{/* B-roll / media timeline */}
			{p.segments.map((seg, i) => (
				<Sequence key={`m${i}`} from={f(seg.start)} durationInFrames={Math.max(1, f(seg.end - seg.start) + 10)} layout="absolute-fill">
					<MediaLayer seg={seg} index={i} region={p.region} />
				</Sequence>
			))}

			{/* Motion-graphics cards and lower thirds tied to segments */}
			{p.segments.map((seg, i) =>
				seg.graphic ? (
					<Sequence key={`g${i}`} from={f(seg.start) + 6} durationInFrames={Math.max(12, f(seg.end - seg.start) - 6)} layout="absolute-fill">
						<GraphicCard g={seg.graphic} durFrames={Math.max(12, f(seg.end - seg.start) - 6)} />
					</Sequence>
				) : null,
			)}
			{p.segments.map((seg, i) =>
				seg.lowerThird ? (
					<Sequence key={`l${i}`} from={f(seg.start) + 4} durationInFrames={Math.max(12, f(seg.end - seg.start) - 4)} layout="absolute-fill">
						<LowerThird text={seg.lowerThird} />
					</Sequence>
				) : null,
			)}

			<Sequence from={f(INTRO_SEC) - 6} durationInFrames={outroFrom - f(INTRO_SEC) + 6} layout="absolute-fill">
				<Headline text={p.headline} dateLabel={p.dateLabel} />
			</Sequence>

			<Captions words={p.words} />

			<Sequence from={f(INTRO_SEC)} layout="absolute-fill">
				<Ticker text={p.ticker} />
			</Sequence>

			<TopBar brand={p.brand} kicker={p.kicker} region={p.region} breaking={p.breaking} />
			<ProgressBar durationSec={p.durationSec} />

			<Sequence from={0} durationInFrames={f(INTRO_SEC) + 10} layout="absolute-fill">
				<Intro hook={p.hook} breaking={p.breaking} />
			</Sequence>

			<Sequence from={outroFrom} layout="absolute-fill">
				<Outro brand={p.brand} text={p.outroText} />
			</Sequence>

			{/* credits line (media licenses), small, above the UI safe area */}
			<div style={{position: 'absolute', top: 1545, left: 60, right: 160, fontFamily: 'Inter', fontSize: 20, color: 'rgba(255,255,255,0.6)'}}>{p.credits}</div>

			<Audio src={staticFile(p.audio)} />
			{p.music ? (
				<Audio
					src={staticFile(p.music)}
					volume={(fr) => interpolate(fr, [0, 15, durationInFrames - 30, durationInFrames], [0, 0.09, 0.09, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}
				/>
			) : null}
		</AbsoluteFill>
	);
};
