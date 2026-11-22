import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {EpisodeProps} from './types';
import {ShotLayer} from './components/ShotLayer';
import {Captions} from './components/Captions';
import {GraphicCard, Headline, Intro, LowerThird, Outro, Ticker, TopBar} from './components/Overlays';
import {Thumbnail} from './components/Thumbnail';

export const INTRO_SEC = 2.6;
export const OUTRO_SEC = 2.5;

export const NewsVideo: React.FC<EpisodeProps> = (p) => {
	const {fps, durationInFrames: total} = useVideoConfig();
	const f = (s: number) => Math.round(s * fps);
	const coverFrom = total - f(p.coverSec || 0);
	const outroFrom = coverFrom - f(OUTRO_SEC);
	const env = p.musicVolume && p.musicVolume.length > 1 ? p.musicVolume : [{t: 0, v: 0.08}, {t: p.durationSec, v: 0.08}];

	return (
		<AbsoluteFill style={{backgroundColor: '#000'}}>
			{/* footage / photo / map timeline (shot level, 2-5 s cuts) */}
			{p.shots.map((s, i) => (
				<Sequence key={`s${i}`} from={f(s.start)} durationInFrames={Math.max(1, f(s.end - s.start))} layout="absolute-fill">
					<ShotLayer shot={s} index={i} />
				</Sequence>
			))}

			{/* motion graphics cards */}
			{p.overlays.map((o, i) => (
				<Sequence key={`o${i}`} from={f(o.start)} durationInFrames={Math.max(12, f(o.end - o.start))} layout="absolute-fill">
					<GraphicCard g={o.graphic} durFrames={Math.max(12, f(o.end - o.start))} />
				</Sequence>
			))}
			{p.lowerThirds.map((l, i) => (
				<Sequence key={`l${i}`} from={f(l.start)} durationInFrames={Math.max(12, f(l.end - l.start))} layout="absolute-fill">
					<LowerThird text={l.text} />
				</Sequence>
			))}

			<Sequence from={f(INTRO_SEC) - 6} durationInFrames={outroFrom - f(INTRO_SEC) + 6} layout="absolute-fill">
				<Headline text={p.headline} dateLabel={p.dateLabel} />
			</Sequence>

			<Captions words={p.words} />

			<Sequence from={f(INTRO_SEC)} durationInFrames={coverFrom - f(INTRO_SEC)} layout="absolute-fill">
				<Ticker text={p.ticker} />
			</Sequence>
			<Sequence from={0} durationInFrames={coverFrom} layout="absolute-fill">
				<TopBar brand={p.brand} kicker={p.kicker} region={p.region} breaking={p.breaking} />
			</Sequence>

			<Sequence from={0} durationInFrames={f(INTRO_SEC) + 10} layout="absolute-fill">
				<Intro hook={p.hook} breaking={p.breaking} />
			</Sequence>
			<Sequence from={outroFrom} durationInFrames={coverFrom - outroFrom} layout="absolute-fill">
				<Outro brand={p.brand} text={p.outroText} />
			</Sequence>
			{p.coverSec ? (
				<Sequence from={coverFrom} layout="absolute-fill">
					<Thumbnail brand={p.brand} kicker={p.kicker} region={p.region} text={p.thumbnailText} headline={p.headline} media={p.coverMedia} />
				</Sequence>
			) : null}

			{/* sound: narration (main), ducked music bed, transition SFX */}
			<Audio src={staticFile(p.audio)} />
			{p.music ? (
				<Audio
					src={staticFile(p.music)}
					volume={(fr) =>
						interpolate(fr / fps, env.map((e) => e.t), env.map((e) => e.v), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) *
						interpolate(fr, [total - 20, total], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
					}
				/>
			) : null}
			{(p.sfx ?? []).map((s, i) => (
				<Sequence key={`fx${i}`} from={f(s.at)} layout="none">
					<Audio src={staticFile(s.src)} volume={s.volume} />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
