import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {CUES} from '../data/transcript';
import {C, SANS} from '../theme';

export const Subtitles: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const cue = CUES.find((c) => t >= c.start && t < c.end + 0.15);
	if (!cue) return null;
	const local = t - cue.start;
	const o = interpolate(local, [0, 0.12], [0, 1], {extrapolateRight: 'clamp'});
	const y = interpolate(local, [0, 0.18], [8, 0], {extrapolateRight: 'clamp'});
	return (
		<div style={{position: 'absolute', left: 0, right: 0, bottom: 74, display: 'flex', justifyContent: 'center', pointerEvents: 'none'}}>
			<div
				style={{
					maxWidth: 1500,
					textAlign: 'center',
					fontFamily: SANS,
					fontWeight: 600,
					fontSize: 44,
					lineHeight: 1.3,
					color: C.text,
					background: 'rgba(8,9,11,0.62)',
					padding: '12px 30px 14px',
					borderRadius: 8,
					opacity: o,
					transform: `translateY(${y}px)`,
					textShadow: '0 2px 8px rgba(0,0,0,0.6)',
				}}
			>
				{cue.text}
			</div>
		</div>
	);
};
