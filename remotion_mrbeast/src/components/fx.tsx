import React from 'react';
import {
	AbsoluteFill,
	Easing,
	Img,
	OffthreadVideo,
	interpolate,
	random,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {FPS} from '../timeline';

export const COLORS = {
	pink: '#FF2E7E', // Squid Game pushti
	teal: '#13B79B', // o‘yinchi formasi yashili
	gold: '#FFC53D',
	ink: '#07080B',
	white: '#FFFFFF',
	red: '#FF3B30',
};

export const FONT_HEAD = 'Anton, Impact, sans-serif';
export const FONT_BODY = 'Montserrat, Arial, sans-serif';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// ───────────────────────────── Footage ─────────────────────────────
type FootageProps = {
	src: string;
	kind?: 'video' | 'image';
	trim?: number; // sekund, video boshidan
	rate?: number;
	zoom?: [number, number];
	pan?: [number, number, number, number]; // x0,y0 → x1,y1 (px)
	grade?: string;
	objectPosition?: string;
	enter?: 'punch' | 'whip' | 'zoomblur' | 'slideUp' | 'none';
	dur: number; // kadrlarda
	blurBg?: boolean; // landshaft rasmni xira fon bilan to‘ldirish
	fit?: 'cover' | 'contain';
};

export const Footage: React.FC<FootageProps> = ({
	src,
	kind = 'video',
	trim = 0,
	rate = 1,
	zoom = [1.08, 1.18],
	pan = [0, 0, 0, 0],
	grade = 'contrast(1.12) saturate(1.12)',
	objectPosition = 'center',
	enter = 'punch',
	dur,
	blurBg = false,
	fit = 'cover',
}) => {
	const frame = useCurrentFrame();
	const p = interpolate(frame, [0, dur], [0, 1], {...clamp, easing: Easing.bezier(0.33, 0, 0.2, 1)});
	let s = interpolate(p, [0, 1], zoom);
	const tx = interpolate(p, [0, 1], [pan[0], pan[2]]);
	const ty = interpolate(p, [0, 1], [pan[1], pan[3]]);

	// Kirish o‘tishlari
	const e = interpolate(frame, [0, 7], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
	let extra = '';
	let blur = 0;
	if (enter === 'punch') {
		s *= interpolate(e, [0, 1], [1.22, 1]);
		blur = interpolate(e, [0, 1], [14, 0]);
	} else if (enter === 'zoomblur') {
		s *= interpolate(e, [0, 1], [0.82, 1]);
		blur = interpolate(e, [0, 1], [22, 0]);
	} else if (enter === 'whip') {
		extra = `translateX(${interpolate(e, [0, 1], [-420, 0])}px)`;
		blur = interpolate(e, [0, 1], [30, 0]);
	} else if (enter === 'slideUp') {
		extra = `translateY(${interpolate(e, [0, 1], [500, 0])}px)`;
		blur = interpolate(e, [0, 1], [20, 0]);
	}

	const media = (style: React.CSSProperties) =>
		kind === 'video' ? (
			<OffthreadVideo
				src={staticFile(src)}
				muted
				trimBefore={Math.round(trim * FPS)}
				playbackRate={rate}
				style={style}
			/>
		) : (
			<Img src={staticFile(src)} style={style} />
		);

	return (
		<AbsoluteFill style={{overflow: 'hidden', backgroundColor: grade === 'none' ? undefined : COLORS.ink}}>
			{blurBg ? (
				<AbsoluteFill style={{transform: `scale(${1.3 * s})`, filter: `blur(40px) brightness(0.45) ${grade}`}}>
					{media({width: '100%', height: '100%', objectFit: 'cover'})}
				</AbsoluteFill>
			) : null}
			<AbsoluteFill
				style={{
					transform: `${extra} translate(${tx}px, ${ty}px) scale(${s})`,
					filter: grade === 'none' ? undefined : `${grade} blur(${blur}px)`,
				}}
			>
				{media({width: '100%', height: '100%', objectFit: fit, objectPosition})}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

// ───────────────────────────── Overlays ─────────────────────────────
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.09}) => {
	const frame = useCurrentFrame();
	const x = Math.floor(random(`gx${frame}`) * 512);
	const y = Math.floor(random(`gy${frame}`) * 512);
	return (
		<AbsoluteFill
			style={{
				backgroundImage: `url(${staticFile('fx/grain.png')})`,
				backgroundPosition: `${x}px ${y}px`,
				backgroundSize: '512px 512px',
				mixBlendMode: 'overlay',
				opacity,
				pointerEvents: 'none',
			}}
		/>
	);
};

export const Vignette: React.FC<{strength?: number}> = ({strength = 0.62}) => (
	<AbsoluteFill
		style={{
			background: `radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 45%, rgba(0,0,0,${strength}) 100%)`,
			pointerEvents: 'none',
		}}
	/>
);

// Matn o‘qilishi uchun yuqori/pastki gradient
export const Scrim: React.FC<{top?: number; bottom?: number}> = ({top = 0.55, bottom = 0.7}) => (
	<AbsoluteFill
		style={{
			background: `linear-gradient(180deg, rgba(0,0,0,${top}) 0%, rgba(0,0,0,0) 32%, rgba(0,0,0,0) 55%, rgba(0,0,0,${bottom}) 100%)`,
		}}
	/>
);

export const LightLeak: React.FC<{seed?: number; dur: number; color?: string; peak?: number}> = ({
	seed = 1,
	dur,
	color = '255,120,40',
	peak = 0.55,
}) => {
	const frame = useCurrentFrame();
	const o = interpolate(frame, [0, dur * 0.35, dur], [0, peak, 0], clamp);
	const x = interpolate(frame, [0, dur], [-20 + seed * 13, 110 - seed * 9]);
	const y = 20 + random(`ll${seed}`) * 60;
	return (
		<AbsoluteFill
			style={{
				background: `radial-gradient(circle at ${x}% ${y}%, rgba(${color},0.95) 0%, rgba(${color},0.35) 22%, rgba(0,0,0,0) 55%)`,
				mixBlendMode: 'screen',
				opacity: o,
				pointerEvents: 'none',
			}}
		/>
	);
};

export const Flash: React.FC<{at: number; len?: number; color?: string; peak?: number}> = ({
	at,
	len = 5,
	color = '#fff',
	peak = 0.9,
}) => {
	const frame = useCurrentFrame();
	const o = interpolate(frame, [at, at + 1, at + len], [0, peak, 0], clamp);
	return <AbsoluteFill style={{backgroundColor: color, opacity: o, pointerEvents: 'none'}} />;
};

// Kamera silkinishi — faqat zarbalarda
export const useShake = (hits: number[], amp = 18, len = 9) => {
	const frame = useCurrentFrame();
	let x = 0;
	let y = 0;
	let r = 0;
	for (const h of hits) {
		const d = frame - h;
		if (d >= 0 && d < len) {
			const k = (1 - d / len) ** 2;
			x += (random(`sx${h}-${d}`) - 0.5) * 2 * amp * k;
			y += (random(`sy${h}-${d}`) - 0.5) * 2 * amp * k;
			r += (random(`sr${h}-${d}`) - 0.5) * 1.2 * k;
		}
	}
	return `translate(${x}px, ${y}px) rotate(${r}deg)`;
};

// ───────────────────────────── Typography ─────────────────────────────
type Word = {t: string; at: number; color?: string; size?: number; bg?: string};

// So‘zlar spring bilan "urilib" chiqadi — Kinetic typography
export const Kinetic: React.FC<{
	words: Word[];
	size?: number;
	top?: number;
	align?: 'center' | 'left';
	lineGap?: number;
	exitAt?: number;
	font?: string;
	maxWidth?: number;
	tilt?: number;
}> = ({words, size = 120, top = 300, align = 'center', exitAt, font = FONT_HEAD, maxWidth = 920, tilt = 0}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const exit = exitAt === undefined ? 0 : interpolate(frame, [exitAt, exitAt + 6], [0, 1], clamp);
	return (
		<div
			style={{
				position: 'absolute',
				top,
				left: (1080 - maxWidth) / 2,
				width: maxWidth,
				display: 'flex',
				flexWrap: 'wrap',
				justifyContent: align === 'center' ? 'center' : 'flex-start',
				alignItems: 'baseline',
				columnGap: size * 0.22,
				rowGap: size * 0.02,
				transform: `rotate(${tilt}deg)`,
				opacity: 1 - exit,
				filter: `blur(${exit * 12}px)`,
			}}
		>
			{words.map((w, i) => {
				const sp = spring({frame: frame - w.at, fps, config: {damping: 11, stiffness: 190, mass: 0.7}});
				const vis = frame >= w.at;
				const sz = w.size ?? size;
				return (
					<span
						key={i}
						style={{
							fontFamily: font,
							fontSize: sz,
							lineHeight: 1.02,
							color: w.color ?? COLORS.white,
							textTransform: 'uppercase',
							letterSpacing: font === FONT_HEAD ? 1 : -1,
							fontWeight: font === FONT_HEAD ? 400 : 900,
							display: 'inline-block',
							opacity: vis ? interpolate(sp, [0, 0.4], [0, 1], clamp) : 0,
							transform: `translateY(${(1 - sp) * sz * 0.5}px) scale(${interpolate(sp, [0, 1], [0.55, 1])})`,
							textShadow: '0 8px 30px rgba(0,0,0,0.65), 0 2px 0 rgba(0,0,0,0.5)',
							WebkitTextStroke: w.bg ? undefined : '2px rgba(0,0,0,0.35)',
							background: w.bg,
							padding: w.bg ? `0 ${sz * 0.14}px` : undefined,
							borderRadius: w.bg ? 10 : undefined,
						}}
					>
						{w.t}
					</span>
				);
			})}
		</div>
	);
};

// Kichik yorliq ("chip")
export const Chip: React.FC<{
	text: string;
	at: number;
	top: number;
	left?: number;
	color?: string;
	textColor?: string;
	size?: number;
	icon?: React.ReactNode;
	center?: boolean;
}> = ({text, at, top, left = 80, color = COLORS.pink, textColor = '#fff', size = 40, icon, center}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const sp = spring({frame: frame - at, fps, config: {damping: 14, stiffness: 160}});
	const w = interpolate(sp, [0, 1], [0, 1]);
	return (
		<div
			style={{
				position: 'absolute',
				top,
				left: center ? 0 : left,
				width: center ? 1080 : undefined,
				display: 'flex',
				justifyContent: center ? 'center' : 'flex-start',
				opacity: frame < at ? 0 : 1,
			}}
		>
			<div
				style={{
					display: 'flex',
					alignItems: 'center',
					gap: 14,
					background: color,
					color: textColor,
					fontFamily: FONT_BODY,
					fontWeight: 800,
					fontSize: size,
					letterSpacing: 1.5,
					textTransform: 'uppercase',
					padding: `${size * 0.32}px ${size * 0.6}px`,
					borderRadius: 999,
					clipPath: `inset(0 ${(1 - w) * 100}% 0 0 round 999px)`,
					transform: `translateX(${(1 - w) * -30}px)`,
					boxShadow: '0 12px 40px rgba(0,0,0,0.45)',
					whiteSpace: 'nowrap',
				}}
			>
				{icon}
				{text}
			</div>
		</div>
	);
};

// ○ △ □ — chiziq chizilishi animatsiyasi (stroke-dashoffset)
export const Shapes: React.FC<{at: number; top: number; size?: number; color?: string; gap?: number; stroke?: number}> = ({
	at,
	top,
	size = 120,
	color = COLORS.pink,
	gap = 60,
	stroke = 12,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const shapes = [
		{d: `M ${size / 2} ${stroke} A ${size / 2 - stroke} ${size / 2 - stroke} 0 1 1 ${size / 2 - 0.01} ${stroke}`, len: Math.PI * (size - 2 * stroke)},
		{d: `M ${size / 2} ${stroke} L ${size - stroke} ${size - stroke} L ${stroke} ${size - stroke} Z`, len: size * 3.1},
		{d: `M ${stroke} ${stroke} H ${size - stroke} V ${size - stroke} H ${stroke} Z`, len: (size - 2 * stroke) * 4},
	];
	const total = shapes.length * size + (shapes.length - 1) * gap;
	return (
		<div style={{position: 'absolute', top, left: (1080 - total) / 2, display: 'flex', gap}}>
			{shapes.map((s, i) => {
				const p = spring({frame: frame - at - i * 4, fps, config: {damping: 200}, durationInFrames: 16});
				const pulse = 1 + 0.06 * Math.max(0, Math.sin((frame - at) / 5 - i));
				return (
					<svg key={i} width={size} height={size} style={{overflow: 'visible', transform: `scale(${pulse})`, filter: `drop-shadow(0 0 18px ${color})`}}>
						<path
							d={s.d}
							fill="none"
							stroke={color}
							strokeWidth={stroke}
							strokeLinejoin="round"
							strokeLinecap="round"
							strokeDasharray={s.len}
							strokeDashoffset={s.len * (1 - p)}
						/>
					</svg>
				);
			})}
		</div>
	);
};

// Raqam hisoblagich (animated counter)
export const formatUz = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

export const Counter: React.FC<{
	from?: number;
	to: number;
	start: number;
	dur: number;
	size?: number;
	top: number;
	prefix?: string;
	suffix?: string;
	color?: string;
	format?: (n: number) => string;
	glow?: string;
}> = ({from = 0, to, start, dur, size = 260, top, prefix = '', suffix = '', color = '#fff', format = formatUz, glow}) => {
	const frame = useCurrentFrame();
	const p = interpolate(frame, [start, start + dur], [0, 1], {...clamp, easing: Easing.out(Easing.exp)});
	const v = frame >= start + dur ? to : from + (to - from) * Math.min(1, p / 0.999);
	const land = interpolate(frame, [start + dur - 2, start + dur + 4, start + dur + 10], [1, 1.12, 1], clamp);
	return (
		<div
			style={{
				position: 'absolute',
				top,
				width: 1080,
				textAlign: 'center',
				fontFamily: FONT_HEAD,
				fontSize: size,
				lineHeight: 1,
				color,
				opacity: frame < start ? 0 : 1,
				transform: `scale(${land})`,
				textShadow: glow ? `0 0 40px ${glow}, 0 10px 40px rgba(0,0,0,0.7)` : '0 10px 40px rgba(0,0,0,0.7)',
				fontVariantNumeric: 'tabular-nums',
			}}
		>
			{prefix}
			{format(v)}
			{suffix}
		</div>
	);
};

// Ramka burchaklari (kamera viewfinder)
export const Corners: React.FC<{inset?: number; color?: string; len?: number; w?: number}> = ({
	inset = 70,
	color = 'rgba(255,255,255,0.9)',
	len = 80,
	w = 6,
}) => {
	const c = (style: React.CSSProperties) => (
		<div style={{position: 'absolute', width: len, height: len, borderColor: color, borderStyle: 'solid', ...style}} />
	);
	return (
		<AbsoluteFill>
			{c({top: inset + 160, left: inset, borderWidth: `${w}px 0 0 ${w}px`})}
			{c({top: inset + 160, right: inset, borderWidth: `${w}px ${w}px 0 0`})}
			{c({bottom: inset + 300, left: inset, borderWidth: `0 0 ${w}px ${w}px`})}
			{c({bottom: inset + 300, right: inset, borderWidth: `0 ${w}px ${w}px 0`})}
		</AbsoluteFill>
	);
};

// Rasm uchun manba/litsenziya yozuvi (CC BY talabi)
export const Credit: React.FC<{text: string}> = ({text}) => (
	<div
		style={{
			position: 'absolute',
			left: 40,
			top: 1520,
			fontFamily: FONT_BODY,
			fontSize: 20,
			fontWeight: 600,
			color: 'rgba(255,255,255,0.62)',
			textShadow: '0 1px 4px rgba(0,0,0,0.9)',
			maxWidth: 800,
		}}
	>
		{text}
	</div>
);

// Xromatik aberratsiya (glitch) qatlami
export const Glitch: React.FC<{children: React.ReactNode; at: number; len?: number}> = ({children, at, len = 8}) => {
	const frame = useCurrentFrame();
	const d = frame - at;
	const on = d >= 0 && d < len;
	const k = on ? 1 - d / len : 0;
	const off = k * 22 * (random(`g${frame}`) > 0.5 ? 1 : -1);
	return (
		<AbsoluteFill>
			{on ? (
				<>
					<AbsoluteFill style={{transform: `translateX(${off}px)`, mixBlendMode: 'screen', opacity: 0.8, filter: 'url(#redOnly)'}}>
						{children}
					</AbsoluteFill>
					<AbsoluteFill style={{transform: `translateX(${-off}px)`, mixBlendMode: 'screen', opacity: 0.8, filter: 'url(#cyanOnly)'}}>
						{children}
					</AbsoluteFill>
				</>
			) : (
				children
			)}
		</AbsoluteFill>
	);
};

export const SvgFilters: React.FC = () => (
	<svg width={0} height={0} style={{position: 'absolute'}}>
		<defs>
			<filter id="redOnly">
				<feColorMatrix type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" />
			</filter>
			<filter id="chroma" colorInterpolationFilters="sRGB">
				{/* yashil fonni kesish (chroma key) + yashil "spill"ni kamaytirish */}
				<feColorMatrix type="matrix" values="1 0 0 0 0  0.3 0.4 0.3 0 0  0 0 1 0 0  6 -8.4 6 0 0.6" />
			</filter>
			<filter id="cyanOnly">
				<feColorMatrix type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" />
			</filter>
		</defs>
	</svg>
);
