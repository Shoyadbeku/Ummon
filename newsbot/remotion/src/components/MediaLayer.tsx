import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Segment} from '../types';
import {theme} from '../theme';

// Animated fallback background when a segment has no media (never a blank/static slide).
const GridBackground: React.FC<{region: 'uz' | 'world'}> = ({region}) => {
	const frame = useCurrentFrame();
	const shift = (frame * 1.2) % 120;
	const accent = region === 'uz' ? theme.uz.blue : theme.blue;
	return (
		<AbsoluteFill style={{background: `radial-gradient(circle at 30% 20%, ${accent}55, ${theme.ink} 60%)`}}>
			<AbsoluteFill
				style={{
					backgroundImage:
						'linear-gradient(rgba(255,255,255,0.06) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.06) 2px, transparent 2px)',
					backgroundSize: '120px 120px',
					backgroundPosition: `${shift}px ${shift}px`,
				}}
			/>
		</AbsoluteFill>
	);
};

const KenBurns: React.FC<{seg: Segment; index: number}> = ({seg, index}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const len = Math.max(1, (seg.end - seg.start) * fps);
	const p = Math.min(1, frame / len);
	// Alternate zoom-in / zoom-out and pan direction per segment.
	const zoomIn = index % 2 === 0;
	const scale = zoomIn ? 1.05 + p * 0.18 : 1.23 - p * 0.18;
	const dx = (index % 3 === 0 ? -1 : index % 3 === 1 ? 1 : 0) * p * 40;
	const fade = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
	const src = staticFile(seg.media as string);
	const style: React.CSSProperties = {
		width: '100%',
		height: '100%',
		objectFit: 'cover',
		transform: `scale(${scale}) translateX(${dx}px)`,
	};
	return (
		<AbsoluteFill style={{opacity: fade, backgroundColor: theme.ink}}>
			{/* blurred fill behind, so horizontal photos still fill a 9:16 frame */}
			<AbsoluteFill style={{filter: 'blur(40px) brightness(0.55)', transform: 'scale(1.3)'}}>
				{seg.mediaType === 'video' ? (
					<OffthreadVideo src={src} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
				) : (
					<Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
				)}
			</AbsoluteFill>
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
				<div style={{width: '100%', height: '72%', overflow: 'hidden', marginTop: -120}}>
					{seg.mediaType === 'video' ? (
						<OffthreadVideo src={src} muted style={style} />
					) : (
						<Img src={src} style={style} />
					)}
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

export const MediaLayer: React.FC<{seg: Segment; index: number; region: 'uz' | 'world'}> = ({seg, index, region}) => {
	return (
		<AbsoluteFill>
			{seg.media ? <KenBurns seg={seg} index={index} /> : <GridBackground region={region} />}
			{/* readability gradient */}
			<AbsoluteFill
				style={{
					background:
						'linear-gradient(180deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.05) 28%, rgba(0,0,0,0.15) 50%, rgba(0,0,0,0.85) 78%, rgba(0,0,0,0.9) 100%)',
				}}
			/>
		</AbsoluteFill>
	);
};
