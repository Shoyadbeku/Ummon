import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile} from 'remotion';
import {Grade, Grain} from './components/Primitives';
import {Subtitles} from './components/Subtitles';
import {SCENES, SceneTrack} from './data/scenes';
import {TRANSCRIPT} from './data/transcript';
import {C, FPS, s} from './theme';

/** Music ducks under speech and rises in pauses / on cards. */
const musicVolume = (f: number) => {
	const t = f / FPS;
	const speaking = TRANSCRIPT.some((l) => t >= l.start - 0.2 && t <= l.end + 0.3);
	const base = speaking ? 0.28 : 0.55;
	const fadeIn = interpolate(t, [0, 2], [0, 1], {extrapolateRight: 'clamp'});
	const fadeOut = interpolate(t, [538, 545], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return base * fadeIn * fadeOut;
};

export const Documentary: React.FC = () => {
	return (
		<AbsoluteFill style={{background: C.ink}}>
			<SceneTrack />
			<Grade />
			<Grain />
			<Subtitles />

			{/* Original voice — cleaned and normalized, never altered in content or timing */}
			<Audio src={staticFile('audio/voice.wav')} volume={1} />
			{/* Original synthesized ambient bed (no third-party music) */}
			<Audio src={staticFile('audio/music.wav')} volume={musicVolume} />
			{SCENES.filter((sc) => sc.sfx).map((sc) => (
				<Sequence key={'sfx-' + sc.id} from={Math.max(0, s(sc.from) - (sc.sfx === 'whoosh' ? 10 : 0))} durationInFrames={s(2.2)}>
					<Audio src={staticFile(`audio/${sc.sfx}.wav`)} volume={sc.sfx === 'whoosh' ? 0.18 : 0.3} />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
