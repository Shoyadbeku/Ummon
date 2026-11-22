import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Shot} from '../types';
import {theme} from '../theme';
import {MapShot} from './MapShot';

// Broadcast-style grade: a touch more contrast, slightly cool shadows, vignette.
const GRADE = 'contrast(1.1) saturate(1.12) brightness(0.96)';

const Vignette = () => (
	<AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
);

const Credit: React.FC<{text?: string | null; illustrative?: boolean}> = ({text, illustrative}) => {
	if (!text && !illustrative) return null;
	return (
		<div style={{position: 'absolute', left: 60, top: 1546, display: 'flex', gap: 10, alignItems: 'center', maxWidth: 860}}>
			{illustrative ? (
				<span style={{fontFamily: theme.font, fontWeight: 800, fontSize: 21, color: '#0B0F17', background: 'rgba(255,255,255,.85)', padding: '3px 9px', borderRadius: 5, letterSpacing: 1}}>
					ILLYUSTRATIV
				</span>
			) : null}
			{text ? (
				<span style={{fontFamily: theme.font, fontWeight: 600, fontSize: 21, color: 'rgba(255,255,255,.92)', textShadow: '0 1px 6px rgba(0,0,0,1)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>
					{text}
				</span>
			) : null}
		</div>
	);
};

export const ShotLayer: React.FC<{shot: Shot; index: number}> = ({shot, index}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const len = Math.max(1, (shot.end - shot.start) * fps);
	const p = Math.min(1, frame / len);
	const tr = shot.transition ?? 'cut';

	// transition-in (first ~8 frames)
	const tIn = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
	const punch = tr === 'zoom' ? 1.18 - 0.18 * tIn : 1;
	const whipX = tr === 'whip' ? (1 - tIn) * 300 : 0;
	const whipBlur = tr === 'whip' ? (1 - tIn) * 30 : 0;
	const flash = tr === 'flash' ? interpolate(frame, [0, 6], [0.85, 0], {extrapolateRight: 'clamp'}) : 0;

	if (shot.map) {
		return (
			<AbsoluteFill>
				<MapShot spec={shot.map} durFrames={len} />
				<AbsoluteFill style={{background: '#fff', opacity: flash}} />
			</AbsoluteFill>
		);
	}

	// Ken Burns on stills, gentle push on video
	const isVideo = shot.mediaType === 'video';
	const zoomIn = index % 2 === 0;
	const kb = isVideo ? 1.04 + p * 0.05 : zoomIn ? 1.06 + p * 0.16 : 1.22 - p * 0.16;
	const dx = isVideo ? 0 : (index % 3 === 0 ? -1 : index % 3 === 1 ? 1 : 0) * p * 50;
	const style: React.CSSProperties = {
		width: '100%',
		height: '100%',
		objectFit: 'cover',
		transform: `translateX(${dx + whipX}px) scale(${kb * punch})`,
		filter: `${GRADE} blur(${whipBlur}px)`,
	};
	return (
		<AbsoluteFill style={{backgroundColor: '#000'}}>
			{shot.media ? (
				isVideo ? (
					<OffthreadVideo src={staticFile(shot.media)} muted playbackRate={shot.speed ?? 1} style={style} />
				) : (
					<Img src={staticFile(shot.media)} style={style} />
				)
			) : null}
			<Vignette />
			<AbsoluteFill
				style={{
					background:
						'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.0) 22%, rgba(0,0,0,0.0) 45%, rgba(0,0,0,0.75) 72%, rgba(0,0,0,0.9) 100%)',
				}}
			/>
			<Credit text={shot.credit} illustrative={shot.illustrative} />
			<AbsoluteFill style={{background: '#fff', opacity: flash}} />
		</AbsoluteFill>
	);
};
