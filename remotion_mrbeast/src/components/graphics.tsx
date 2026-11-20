import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {geoGraticule10, geoOrthographic, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore — JSON modul
import world from 'world-atlas/countries-50m.json';
import {COLORS, FONT_BODY, FONT_HEAD} from './fx';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// ───────────────── Globus → Janubiy Koreya (map animation) ─────────────────
export const Globe: React.FC<{dur: number}> = ({dur}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const countries = useMemo(
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		() => (feature(world as any, (world as any).objects.countries) as any).features as any[],
		[],
	);
	const p = interpolate(frame, [0, dur * 0.78], [0, 1], {...clamp, easing: Easing.bezier(0.6, 0, 0.2, 1)});
	const lon = interpolate(p, [0, 1], [40, 127.8]);
	const lat = interpolate(p, [0, 1], [10, 36.3]);
	const scale = interpolate(p, [0, 0.55, 1], [430, 620, 3300]);
	const proj = geoOrthographic()
		.rotate([-lon, -lat])
		.scale(scale)
		.translate([540, 900])
		.clipAngle(90);
	const path = geoPath(proj);
	const seoul = proj([126.98, 37.57]) ?? [540, 900];
	const pin = spring({frame: frame - Math.round(dur * 0.72), fps, config: {damping: 9, stiffness: 180}});
	const ring = ((frame - dur * 0.72) % 18) / 18;
	return (
		<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 45%, #0f2238 0%, #05070c 70%)'}}>
			<svg width={1080} height={1920}>
				<defs>
					<radialGradient id="ocean" cx="40%" cy="35%">
						<stop offset="0%" stopColor="#173a5e" />
						<stop offset="100%" stopColor="#081626" />
					</radialGradient>
				</defs>
				<path d={path({type: 'Sphere'}) ?? ''} fill="url(#ocean)" stroke="rgba(120,200,255,0.35)" strokeWidth={2} />
				<path d={path(geoGraticule10()) ?? ''} fill="none" stroke="rgba(120,200,255,0.10)" strokeWidth={1} />
				{countries.map((c, i) => {
					const isKr = c.id === '410';
					return (
						<path
							key={i}
							d={path(c) ?? ''}
							fill={isKr ? COLORS.pink : '#2a4a63'}
							stroke={isKr ? '#fff' : 'rgba(255,255,255,0.18)'}
							strokeWidth={isKr ? 3 : 0.8}
							style={isKr ? {filter: `drop-shadow(0 0 ${10 + 20 * p}px ${COLORS.pink})`} : undefined}
						/>
					);
				})}
				{pin > 0.01 ? (
					<g transform={`translate(${seoul[0]}, ${seoul[1]})`}>
						<circle r={20 + ring * 80} fill="none" stroke={COLORS.pink} strokeWidth={4} opacity={1 - ring} />
						<g transform={`scale(${pin})`}>
							<circle r={16} fill="#fff" />
							<circle r={8} fill={COLORS.pink} />
						</g>
					</g>
				) : null}
			</svg>
			<div
				style={{
					position: 'absolute',
					top: 330,
					width: 1080,
					textAlign: 'center',
					fontFamily: FONT_HEAD,
					fontSize: 130,
					color: '#fff',
					textShadow: '0 10px 40px rgba(0,0,0,0.7)',
					opacity: interpolate(frame, [dur * 0.45, dur * 0.6], [0, 1], clamp),
					transform: `translateY(${interpolate(frame, [dur * 0.45, dur * 0.65], [40, 0], clamp)}px)`,
				}}
			>
				JANUBIY KOREYA
			</div>
			<div
				style={{
					position: 'absolute',
					left: seoul[0] + 34,
					top: seoul[1] - 30,
					fontFamily: FONT_BODY,
					fontWeight: 800,
					fontSize: 40,
					color: '#fff',
					background: 'rgba(0,0,0,0.55)',
					padding: '6px 18px',
					borderRadius: 10,
					opacity: pin,
				}}
			>
				SEUL
			</div>
		</AbsoluteFill>
	);
};

// ───────────────── 456 ta o‘yinchi (infografika) ─────────────────
const Person: React.FC<{color: string; size: number}> = ({color, size}) => (
	<svg width={size} height={size} viewBox="0 0 20 20">
		<circle cx={10} cy={5} r={3.6} fill={color} />
		<path d="M3.5 19 Q3.5 10 10 10 Q16.5 10 16.5 19 Z" fill={color} />
	</svg>
);

export const PlayerGrid: React.FC<{start: number; fill: number}> = ({start, fill}) => {
	const frame = useCurrentFrame();
	const cols = 19;
	const rows = 24; // 19 × 24 = 456
	const cell = 40;
	const order = useMemo(() => {
		// markazdan tashqariga "to‘lqin" bo‘lib to‘lishi
		const idx = Array.from({length: cols * rows}, (_, i) => i);
		const cx = (cols - 1) / 2;
		const cy = (rows - 1) / 2;
		const d = idx.map((i) => Math.hypot((i % cols) - cx, Math.floor(i / cols) - cy) + random(`p${i}`) * 2.2);
		const sorted = [...idx].sort((a, b) => d[a] - d[b]);
		const rank = new Array(idx.length);
		sorted.forEach((v, r) => (rank[v] = r));
		return rank as number[];
	}, []);
	const shown = interpolate(frame, [start, start + fill], [0, cols * rows], {...clamp, easing: Easing.out(Easing.quad)});
	return (
		<div
			style={{
				position: 'absolute',
				top: 680,
				left: (1080 - cols * cell) / 2,
				width: cols * cell,
				display: 'grid',
				gridTemplateColumns: `repeat(${cols}, ${cell}px)`,
			}}
		>
			{order.map((r, i) => {
				const on = r < shown;
				const age = on ? shown - r : 0;
				const sc = on ? interpolate(age, [0, 14], [0.2, 1], clamp) : 0;
				const special = i === 0 || i === cols * rows - 1;
				return (
					<div key={i} style={{width: cell, height: cell, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${sc})`, opacity: on ? 1 : 0}}>
						<Person color={special ? COLORS.pink : COLORS.teal} size={cell - 6} />
					</div>
				);
			})}
		</div>
	);
};

// ───────────────── Byudjet taqqoslash (bar chart) ─────────────────
export const BudgetBars: React.FC<{start: number}> = ({start}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const row = (label: string, value: string, ratio: number, color: string, at: number, top: number) => {
		const sp = spring({frame: frame - at, fps, config: {damping: 18, stiffness: 70}});
		return (
			<div style={{position: 'absolute', top, left: 90, width: 900, opacity: frame < at ? 0 : 1}}>
				<div style={{fontFamily: FONT_BODY, fontWeight: 800, fontSize: 38, color: 'rgba(255,255,255,0.85)', letterSpacing: 1.5, marginBottom: 14}}>
					{label}
				</div>
				<div style={{height: 92, width: 900, background: 'rgba(255,255,255,0.08)', borderRadius: 18, overflow: 'hidden', position: 'relative'}}>
					<div
						style={{
							height: '100%',
							width: `${ratio * 100 * sp}%`,
							background: `linear-gradient(90deg, ${color}aa, ${color})`,
							borderRadius: 18,
							boxShadow: `0 0 40px ${color}88`,
						}}
					/>
					<div
						style={{
							position: 'absolute',
							right: 24,
							top: 0,
							height: 92,
							display: 'flex',
							alignItems: 'center',
							fontFamily: FONT_HEAD,
							fontSize: 60,
							color: '#fff',
							textShadow: '0 4px 14px rgba(0,0,0,0.6)',
							opacity: interpolate(sp, [0.4, 0.9], [0, 1], clamp),
						}}
					>
						{value}
					</div>
				</div>
			</div>
		);
	};
	return (
		<>
			{row('G‘OLIB MUKOFOTI', '$456 ming', 456 / 3500, COLORS.teal, start, 1080)}
			{row('LOYIHA XARAJATI', '≈ $3,5 mln', 1, COLORS.gold, start + 10, 1260)}
		</>
	);
};

// ───────────────── ID-karta: "asl ismi" ─────────────────
export const IdCard: React.FC<{start: number; nameAt: number; photo: string}> = ({start, nameAt, photo}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const sp = spring({frame: frame - start, fps, config: {damping: 14, stiffness: 120}});
	const name = 'JIMMY DONALDSON';
	const chars = Math.floor(interpolate(frame, [nameAt, nameAt + 14], [0, name.length], clamp));
	const caret = Math.floor(frame / 8) % 2 === 0;
	return (
		<div
			style={{
				position: 'absolute',
				top: 980,
				left: 80,
				width: 920,
				height: 380,
				borderRadius: 34,
				background: 'linear-gradient(135deg, rgba(20,22,30,0.92), rgba(10,10,14,0.88))',
				border: '2px solid rgba(255,255,255,0.18)',
				boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
				transform: `perspective(1400px) rotateX(${(1 - sp) * 40}deg) translateY(${(1 - sp) * 200}px)`,
				opacity: interpolate(sp, [0, 0.3], [0, 1], clamp),
				overflow: 'hidden',
				display: 'flex',
			}}
		>
			<div style={{width: 14, background: `linear-gradient(${COLORS.pink}, ${COLORS.teal})`}} />
			<Img src={staticFile(photo)} style={{width: 260, height: 380, objectFit: 'cover', objectPosition: '50% 20%'}} />
			<div style={{padding: '44px 40px', flex: 1}}>
				<div style={{fontFamily: FONT_BODY, fontWeight: 800, fontSize: 30, letterSpacing: 4, color: COLORS.pink}}>ASL ISMI</div>
				<div style={{fontFamily: FONT_HEAD, fontSize: 82, color: '#fff', lineHeight: 1.05, marginTop: 14, minHeight: 172}}>
					{name.slice(0, chars)}
					<span style={{opacity: caret && chars < name.length ? 1 : 0, color: COLORS.pink}}>|</span>
				</div>
				<div style={{fontFamily: FONT_BODY, fontWeight: 700, fontSize: 30, color: 'rgba(255,255,255,0.65)', letterSpacing: 2}}>
					TAXALLUSI: <span style={{color: '#fff'}}>MrBeast</span>
				</div>
			</div>
		</div>
	);
};

// ───────────────── Blueprint: maydon chizmasi (path drawing) ─────────────────
export const Blueprint: React.FC<{dur: number}> = ({dur}) => {
	const frame = useCurrentFrame();
	const p = interpolate(frame, [2, dur - 6], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
	const lines = [
		{d: 'M 160 760 H 920 V 1360 H 160 Z', len: 2720},
		{d: 'M 160 900 H 920', len: 760},
		{d: 'M 160 1240 H 920', len: 760},
		{d: 'M 540 760 V 1360', len: 600},
		{d: 'M 540 1060 m -110 0 a 110 110 0 1 0 220 0 a 110 110 0 1 0 -220 0', len: 692},
		{d: 'M 250 820 l 40 -40 l 40 40 z', len: 200},
		{d: 'M 760 790 h 70 v 70 h -70 z', len: 280},
	];
	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			<AbsoluteFill
				style={{
					backgroundImage:
						'linear-gradient(rgba(120,200,255,0.16) 2px, transparent 2px), linear-gradient(90deg, rgba(120,200,255,0.16) 2px, transparent 2px)',
					backgroundSize: '60px 60px',
					opacity: interpolate(frame, [0, 6], [0, 1], clamp),
					mixBlendMode: 'screen',
				}}
			/>
			<svg width={1080} height={1920} style={{position: 'absolute'}}>
				{lines.map((l, i) => {
					const lp = interpolate(p, [i * 0.08, Math.min(1, i * 0.08 + 0.55)], [0, 1], clamp);
					return (
						<path
							key={i}
							d={l.d}
							fill="none"
							stroke="#9fdcff"
							strokeWidth={6}
							strokeLinecap="round"
							strokeDasharray={l.len}
							strokeDashoffset={l.len * (1 - lp)}
							style={{filter: 'drop-shadow(0 0 10px rgba(120,200,255,0.9))'}}
						/>
					);
				})}
			</svg>
		</AbsoluteFill>
	);
};

// ───────────────── REC UI (bloger kamerasi) ─────────────────
export const RecUI: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = Math.floor(frame / fps);
	const ff = frame % fps;
	return (
		<>
			<div style={{position: 'absolute', top: 250, left: 100, display: 'flex', alignItems: 'center', gap: 16, fontFamily: FONT_BODY, fontWeight: 800, fontSize: 40, color: '#fff'}}>
				<div style={{width: 30, height: 30, borderRadius: 15, background: COLORS.red, opacity: Math.floor(frame / 10) % 2 ? 0.25 : 1}} />
				REC
			</div>
			<div style={{position: 'absolute', top: 250, right: 100, fontFamily: 'monospace', fontWeight: 700, fontSize: 38, color: '#fff'}}>
				00:00:{String(s).padStart(2, '0')}:{String(ff).padStart(2, '0')}
			</div>
		</>
	);
};

// ───────────────── Video pleyer UI ("oddiy YouTube video") ─────────────────
export const PlayerUI: React.FC<{start: number}> = ({start}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const sp = spring({frame: frame - start, fps, config: {damping: 15, stiffness: 140}});
	const prog = interpolate(frame, [start, start + 60], [0.08, 0.42], clamp);
	return (
		<div
			style={{
				position: 'absolute',
				top: 640,
				left: 70,
				width: 940,
				height: 529,
				borderRadius: 26,
				border: '4px solid rgba(255,255,255,0.9)',
				boxShadow: '0 30px 90px rgba(0,0,0,0.7)',
				transform: `scale(${interpolate(sp, [0, 1], [0.7, 1])})`,
				opacity: interpolate(sp, [0, 0.3], [0, 1], clamp),
				overflow: 'hidden',
				background: 'rgba(0,0,0,0.15)',
			}}
		>
			<div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
				<div style={{width: 170, height: 120, borderRadius: 34, background: COLORS.red, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 10px 40px rgba(0,0,0,0.5)', transform: `scale(${1 + 0.05 * Math.sin(frame / 4)})`}}>
					<div style={{width: 0, height: 0, borderTop: '28px solid transparent', borderBottom: '28px solid transparent', borderLeft: '48px solid #fff', marginLeft: 10}} />
				</div>
			</div>
			<div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 70, background: 'linear-gradient(transparent, rgba(0,0,0,0.75))'}} />
			<div style={{position: 'absolute', left: 30, right: 30, bottom: 26, height: 8, background: 'rgba(255,255,255,0.3)', borderRadius: 4}}>
				<div style={{width: `${prog * 100}%`, height: '100%', background: COLORS.red, borderRadius: 4}} />
				<div style={{position: 'absolute', left: `calc(${prog * 100}% - 12px)`, top: -8, width: 24, height: 24, borderRadius: 12, background: COLORS.red}} />
			</div>
		</div>
	);
};

// ───────────────── Split screen: TV vs YouTube ko‘lami ─────────────────
export const ScaleMeter: React.FC<{start: number; overtakeAt: number; tvTop?: number; ytTop?: number}> = ({start, overtakeAt, tvTop = 640, ytTop = 1240}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const a = spring({frame: frame - start, fps, config: {damping: 20, stiffness: 80}});
	const b = spring({frame: frame - overtakeAt, fps, config: {damping: 10, stiffness: 120}});
	const tv = 0.62 * a;
	const yt = 0.5 * a + 0.48 * b;
	const bar = (label: string, v: number, color: string, top: number) => (
		<div style={{position: 'absolute', left: 90, top, width: 900}}>
			<div style={{fontFamily: FONT_BODY, fontWeight: 800, fontSize: 32, color: '#fff', letterSpacing: 2, marginBottom: 10, textShadow: '0 2px 10px rgba(0,0,0,0.8)'}}>{label}</div>
			<div style={{height: 34, background: 'rgba(0,0,0,0.45)', borderRadius: 17, overflow: 'hidden', border: '2px solid rgba(255,255,255,0.25)'}}>
				<div style={{width: `${v * 100}%`, height: '100%', background: color, borderRadius: 17, boxShadow: `0 0 30px ${color}`}} />
			</div>
		</div>
	);
	return (
		<>
			{bar('KO‘LAM', tv, '#9aa6bd', tvTop)}
			{bar('KO‘LAM', yt, COLORS.pink, ytTop)}
		</>
	);
};

// ───────────────── So‘rovnoma (yakuniy savol) ─────────────────
export const Poll: React.FC<{start: number}> = ({start}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const btn = (label: string, color: string, i: number) => {
		const sp = spring({frame: frame - start - i * 5, fps, config: {damping: 11, stiffness: 170}});
		const pulse = 1 + 0.03 * Math.sin((frame - start) / 5 + i * 2);
		return (
			<div
				style={{
					width: 400,
					height: 130,
					borderRadius: 30,
					background: color,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
					fontFamily: FONT_HEAD,
					fontSize: 76,
					color: '#fff',
					transform: `scale(${sp * pulse}) translateY(${(1 - sp) * 80}px)`,
					boxShadow: `0 16px 50px ${color}88`,
				}}
			>
				{label}
			</div>
		);
	};
	return (
		<div style={{position: 'absolute', top: 1180, width: 1080, display: 'flex', justifyContent: 'center', gap: 50}}>
			{btn('HA', COLORS.teal, 0)}
			{btn('YO‘Q', COLORS.pink, 1)}
		</div>
	);
};
