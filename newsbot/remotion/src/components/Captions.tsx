import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Word} from '../types';
import {theme} from '../theme';

// Group words into short on-screen phrases (max ~3 words / 22 chars), TikTok-style kinetic captions.
export const groupWords = (words: Word[]) => {
	const groups: Word[][] = [];
	let cur: Word[] = [];
	let chars = 0;
	for (const w of words) {
		const endsSentence = /[.!?…]$/.test(w.text);
		if (cur.length && (cur.length >= 3 || chars + w.text.length > 22)) {
			groups.push(cur);
			cur = [];
			chars = 0;
		}
		cur.push(w);
		chars += w.text.length + 1;
		if (endsSentence) {
			groups.push(cur);
			cur = [];
			chars = 0;
		}
	}
	if (cur.length) groups.push(cur);
	return groups;
};

export const Captions: React.FC<{words: Word[]}> = ({words}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const groups = React.useMemo(() => groupWords(words), [words]);
	const g = groups.find((gr) => t >= gr[0].start - 0.05 && t < gr[gr.length - 1].end + 0.12);
	if (!g) return null;
	const gStartFrame = Math.round(g[0].start * fps);
	const pop = spring({frame: frame - gStartFrame, fps, config: {damping: 14, stiffness: 220}});
	return (
		<div
			style={{
				position: 'absolute',
				top: 1030,
				left: 60,
				right: 140,
				display: 'flex',
				flexWrap: 'wrap',
				justifyContent: 'center',
				gap: '6px 18px',
				transform: `scale(${0.85 + 0.15 * pop})`,
			}}
		>
			{g.map((w, i) => {
				const active = t >= w.start && t < w.end + 0.05;
				const color = w.highlight ? theme.yellow : active ? theme.white : 'rgba(255,255,255,0.88)';
				return (
					<span
						key={i}
						style={{
							fontFamily: theme.font,
							fontWeight: 900,
							fontSize: 78,
							lineHeight: 1.1,
							color,
							textTransform: 'uppercase',
							letterSpacing: -1,
							padding: '2px 14px',
							borderRadius: 14,
							background: active ? (w.highlight ? theme.red : 'rgba(30,107,255,0.92)') : 'transparent',
							textShadow: active ? 'none' : '0 4px 18px rgba(0,0,0,0.9), 0 0 3px rgba(0,0,0,1)',
							WebkitTextStroke: active ? undefined : '2px rgba(0,0,0,0.55)',
						}}
					>
						{w.text}
					</span>
				);
			})}
		</div>
	);
};
