import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {Graphic} from '../types';
import {theme} from '../theme';

const font = theme.font;

export const ProgressBar: React.FC<{durationSec: number}> = ({durationSec}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const p = Math.min(1, frame / (durationSec * fps));
	return (
		<div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 10, background: 'rgba(255,255,255,0.18)'}}>
			<div style={{width: `${p * 100}%`, height: '100%', background: theme.red}} />
		</div>
	);
};

// Small uzbek flag drawn in CSS (no emoji fonts needed).
export const UzFlag: React.FC<{w?: number}> = ({w = 54}) => (
	<div style={{width: w, height: w / 2, display: 'flex', flexDirection: 'column', borderRadius: 4, overflow: 'hidden', boxShadow: '0 2px 6px rgba(0,0,0,.5)'}}>
		<div style={{flex: 10, background: theme.uz.blue}} />
		<div style={{flex: 1, background: theme.uz.red}} />
		<div style={{flex: 10, background: '#fff'}} />
		<div style={{flex: 1, background: theme.uz.red}} />
		<div style={{flex: 10, background: theme.uz.green}} />
	</div>
);

export const Globe: React.FC<{size?: number}> = ({size = 34}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8">
		<circle cx="12" cy="12" r="10" />
		<path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
	</svg>
);

export const TopBar: React.FC<{brand: string; kicker: string; region: 'uz' | 'world'; breaking: boolean}> = ({brand, kicker, region, breaking}) => {
	const frame = useCurrentFrame();
	const blink = breaking ? 0.55 + 0.45 * Math.abs(Math.sin(frame / 8)) : 1;
	return (
		<div style={{position: 'absolute', top: 40, left: 60, right: 60, display: 'flex', alignItems: 'center', gap: 18}}>
			<div style={{fontFamily: font, fontWeight: 900, fontSize: 40, color: '#fff', letterSpacing: -0.5, padding: '8px 18px', background: theme.ink, borderRadius: 10, border: '2px solid rgba(255,255,255,.25)'}}>
				{brand}
			</div>
			<div style={{display: 'flex', alignItems: 'center', gap: 12, background: theme.red, padding: '10px 18px', borderRadius: 10}}>
				<div style={{width: 16, height: 16, borderRadius: 8, background: '#fff', opacity: blink}} />
				<span style={{fontFamily: font, fontWeight: 800, fontSize: 32, color: '#fff', textTransform: 'uppercase'}}>{kicker}</span>
			</div>
			<div style={{marginLeft: 'auto'}}>{region === 'uz' ? <UzFlag /> : <Globe />}</div>
		</div>
	);
};

// 0–2.6s: breaking-news intro with kinetic hook.
export const Intro: React.FC<{hook: string; breaking: boolean}> = ({hook, breaking}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const barIn = spring({frame, fps, config: {damping: 200}});
	const out = interpolate(frame, [fps * 2.3, fps * 2.7], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const words = hook.split(/\s+/);
	return (
		<AbsoluteFill style={{opacity: out, justifyContent: 'center', alignItems: 'center', padding: '0 70px'}}>
			<div
				style={{
					transform: `translateX(${(1 - barIn) * -1100}px)`,
					background: breaking ? theme.red : theme.blue,
					color: '#fff',
					fontFamily: font,
					fontWeight: 900,
					fontSize: 54,
					padding: '12px 30px',
					borderRadius: 8,
					marginBottom: 30,
					letterSpacing: 2,
				}}
			>
				{breaking ? 'SHOSHILINCH XABAR' : 'MUHIM YANGILIK'}
			</div>
			<div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0 20px'}}>
				{words.map((w, i) => {
					const s = spring({frame: frame - 6 - i * 3, fps, config: {damping: 12, stiffness: 180}});
					return (
						<span
							key={i}
							style={{
								fontFamily: font,
								fontWeight: 900,
								fontSize: 92,
								lineHeight: 1.05,
								color: i % 4 === 1 ? theme.yellow : '#fff',
								textTransform: 'uppercase',
								transform: `translateY(${(1 - s) * 60}px) scale(${0.6 + 0.4 * s})`,
								opacity: s,
								textShadow: '0 6px 30px rgba(0,0,0,.8)',
								textAlign: 'center',
							}}
						>
							{w}
						</span>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};

export const Headline: React.FC<{text: string; dateLabel: string}> = ({text, dateLabel}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame, fps, config: {damping: 200}});
	return (
		<div style={{position: 'absolute', top: 150, left: 60, right: 60, transform: `translateY(${(1 - s) * -40}px)`, opacity: s}}>
			<div style={{fontFamily: font, fontSize: 28, fontWeight: 700, color: theme.yellow, marginBottom: 8, letterSpacing: 1}}>{dateLabel}</div>
			<div style={{fontFamily: font, fontWeight: 900, fontSize: 56, lineHeight: 1.08, color: '#fff', textShadow: '0 4px 24px rgba(0,0,0,.9)', borderLeft: `10px solid ${theme.red}`, paddingLeft: 22}}>
				{text}
			</div>
		</div>
	);
};

export const LowerThird: React.FC<{text: string}> = ({text}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame, fps, config: {damping: 200}});
	return (
		<div style={{position: 'absolute', top: 1370, left: 60, right: 140, display: 'flex'}}>
			<div style={{width: 12, background: theme.red, transform: `scaleY(${s})`}} />
			<div style={{background: theme.glass, padding: '14px 24px', clipPath: `inset(0 ${(1 - s) * 100}% 0 0)`}}>
				<span style={{fontFamily: font, fontWeight: 700, fontSize: 36, color: '#fff'}}>{text}</span>
			</div>
		</div>
	);
};

const fmt = (n: number, decimals = 0) => n.toLocaleString('ru-RU', {minimumFractionDigits: decimals, maximumFractionDigits: decimals}).replace(/ /g, ' ');

export const GraphicCard: React.FC<{g: Graphic; durFrames: number}> = ({g, durFrames}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame, fps, config: {damping: 15, stiffness: 160}});
	const out = interpolate(frame, [durFrames - 8, durFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const box: React.CSSProperties = {
		position: 'absolute',
		top: 560,
		left: 80,
		right: 160,
		background: 'rgba(11,15,23,0.86)',
		border: '2px solid rgba(255,255,255,0.15)',
		borderRadius: 28,
		padding: '34px 40px',
		transform: `scale(${0.7 + 0.3 * s})`,
		opacity: s * out,
		boxShadow: '0 20px 60px rgba(0,0,0,.6)',
	};
	if (g.type === 'stat') {
		const v = interpolate(frame, [0, fps * 1.2], [0, g.value], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
		return (
			<div style={box}>
				<div style={{fontFamily: font, fontWeight: 900, fontSize: 120, color: theme.yellow, lineHeight: 1}}>
					{g.prefix ?? ''}
					{fmt(v, g.decimals ?? 0)}
					{g.suffix ?? ''}
				</div>
				<div style={{fontFamily: font, fontWeight: 700, fontSize: 40, color: '#fff', marginTop: 12}}>{g.label}</div>
			</div>
		);
	}
	if (g.type === 'location') {
		const pulse = 1 + 0.25 * Math.abs(Math.sin(frame / 7));
		return (
			<div style={{...box, display: 'flex', alignItems: 'center', gap: 30}}>
				<div style={{position: 'relative', width: 90, height: 90}}>
					<div style={{position: 'absolute', inset: 0, borderRadius: 45, background: theme.red, opacity: 0.35, transform: `scale(${pulse})`}} />
					<div style={{position: 'absolute', inset: 22, borderRadius: 23, background: theme.red}} />
				</div>
				<div>
					<div style={{fontFamily: font, fontWeight: 600, fontSize: 30, color: 'rgba(255,255,255,.7)'}}>VOQEA JOYI</div>
					<div style={{fontFamily: font, fontWeight: 900, fontSize: 58, color: '#fff'}}>{g.place}</div>
				</div>
				<div style={{marginLeft: 'auto'}}>{g.country === 'uz' ? <UzFlag w={90} /> : <Globe size={70} />}</div>
			</div>
		);
	}
	if (g.type === 'quote') {
		return (
			<div style={box}>
				<div style={{fontFamily: font, fontWeight: 900, fontSize: 110, color: theme.red, lineHeight: 0.6}}>“</div>
				<div style={{fontFamily: font, fontWeight: 800, fontSize: 48, color: '#fff', lineHeight: 1.15}}>{g.text}</div>
				<div style={{fontFamily: font, fontWeight: 600, fontSize: 32, color: theme.yellow, marginTop: 18}}>— {g.who}</div>
			</div>
		);
	}
	if (g.type === 'timeline') {
		return (
			<div style={box}>
				{g.title ? <div style={{fontFamily: font, fontWeight: 900, fontSize: 40, color: theme.yellow, marginBottom: 18}}>{g.title}</div> : null}
				<div style={{position: 'relative', paddingLeft: 44}}>
					<div style={{position: 'absolute', left: 14, top: 10, bottom: 10, width: 6, background: 'rgba(255,255,255,.25)', borderRadius: 3}} />
					{g.items.map((it, i) => {
						const si = spring({frame: frame - 6 - i * 10, fps, config: {damping: 200}});
						return (
							<div key={i} style={{position: 'relative', marginBottom: 22, opacity: si, transform: `translateX(${(1 - si) * 50}px)`}}>
								<div style={{position: 'absolute', left: -42, top: 8, width: 30, height: 30, borderRadius: 15, background: it.active ? theme.red : '#fff', boxShadow: it.active ? `0 0 0 8px ${theme.red}55` : 'none'}} />
								<div style={{fontFamily: font, fontWeight: 900, fontSize: 36, color: it.active ? theme.yellow : '#fff'}}>{it.date}</div>
								<div style={{fontFamily: font, fontWeight: 600, fontSize: 34, color: 'rgba(255,255,255,.92)', lineHeight: 1.2}}>{it.text}</div>
							</div>
						);
					})}
				</div>
			</div>
		);
	}
	// list
	return (
		<div style={box}>
			<div style={{fontFamily: font, fontWeight: 900, fontSize: 46, color: theme.yellow, marginBottom: 14}}>{g.title}</div>
			{g.items.map((it, i) => {
				const si = spring({frame: frame - 8 - i * 6, fps, config: {damping: 200}});
				return (
					<div key={i} style={{display: 'flex', gap: 16, alignItems: 'flex-start', marginTop: 12, opacity: si, transform: `translateX(${(1 - si) * 60}px)`}}>
						<div style={{minWidth: 46, height: 46, borderRadius: 23, background: theme.red, color: '#fff', fontFamily: font, fontWeight: 900, fontSize: 28, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{i + 1}</div>
						<div style={{fontFamily: font, fontWeight: 700, fontSize: 38, color: '#fff', lineHeight: 1.2}}>{it}</div>
					</div>
				);
			})}
		</div>
	);
};

export const Ticker: React.FC<{text: string}> = ({text}) => {
	const frame = useCurrentFrame();
	const x = -((frame * 4) % (text.length * 22 + 1080));
	return (
		<div style={{position: 'absolute', top: 1470, left: 0, right: 0, height: 64, background: 'rgba(227,38,47,0.95)', display: 'flex', alignItems: 'center', overflow: 'hidden'}}>
			<div style={{background: theme.ink, height: '100%', display: 'flex', alignItems: 'center', padding: '0 20px', zIndex: 2, fontFamily: font, fontWeight: 900, fontSize: 30, color: '#fff'}}>YANGILIKLAR</div>
			<div style={{whiteSpace: 'nowrap', transform: `translateX(${x + 1080}px)`, fontFamily: font, fontWeight: 700, fontSize: 32, color: '#fff'}}>
				{text} &nbsp;•&nbsp; {text}
			</div>
		</div>
	);
};

export const Outro: React.FC<{brand: string; text: string}> = ({brand, text}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame, fps, config: {damping: 14}});
	return (
		<AbsoluteFill style={{background: `rgba(11,15,23,${0.85 * s})`, justifyContent: 'center', alignItems: 'center'}}>
			<div style={{transform: `scale(${0.6 + 0.4 * s})`, opacity: s, textAlign: 'center'}}>
				<div style={{fontFamily: font, fontWeight: 900, fontSize: 120, color: '#fff', letterSpacing: -2}}>{brand}</div>
				<div style={{fontFamily: font, fontWeight: 800, fontSize: 50, color: theme.yellow, marginTop: 10}}>{text}</div>
				<div style={{marginTop: 40, display: 'inline-block', background: theme.red, color: '#fff', fontFamily: font, fontWeight: 900, fontSize: 46, padding: '18px 44px', borderRadius: 60}}>OBUNA BO‘LING</div>
			</div>
		</AbsoluteFill>
	);
};
