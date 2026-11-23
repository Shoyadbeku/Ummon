import React from 'react';
import {
	AbsoluteFill,
	Img,
	OffthreadVideo,
	interpolate,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
	Easing,
} from 'remotion';
import {C, SANS, SERIF, STATUS_LABEL, Status} from '../theme';

/* ---------- helpers ---------- */

export const useEnter = (delay = 0, damping = 200) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return spring({frame: frame - delay, fps, config: {damping, mass: 0.9}});
};

/** Fade in at start / fade out at end of the current Sequence. */
export const useFade = (inFrames = 10, outFrames = 10) => {
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	return interpolate(
		frame,
		[0, inFrames, durationInFrames - outFrames, durationInFrames],
		[0, 1, 1, 0],
		{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
	);
};

/* ---------- cinematic look ---------- */

export const Grade: React.FC = () => (
	<>
		<AbsoluteFill
			style={{
				background:
					'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)',
				pointerEvents: 'none',
			}}
		/>
		<AbsoluteFill
			style={{
				background: 'linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 62%, rgba(0,0,0,0.55) 100%)',
			}}
		/>
	</>
);

export const Grain: React.FC = () => {
	const frame = useCurrentFrame();
	const i = Math.floor(frame / 2) % 6;
	return (
		<AbsoluteFill style={{opacity: 0.06, mixBlendMode: 'overlay', pointerEvents: 'none'}}>
			<Img src={staticFile(`fx/grain${i}.png`)} style={{width: '100%', height: '100%', imageRendering: 'pixelated'}} />
		</AbsoluteFill>
	);
};

export const Letterbox: React.FC = () => null;

/* ---------- video ---------- */

export const VideoShot: React.FC<{
	src: string;
	startFrom?: number; // seconds into the clip
	zoom?: [number, number];
	origin?: string;
	dim?: number;
	blur?: number;
}> = ({src, startFrom = 0, zoom = [1.02, 1.1], origin = '50% 40%', dim = 0, blur = 0}) => {
	const frame = useCurrentFrame();
	const {durationInFrames, fps} = useVideoConfig();
	const sc = interpolate(frame, [0, durationInFrames], zoom, {easing: Easing.inOut(Easing.quad)});
	return (
		<AbsoluteFill style={{background: C.ink, overflow: 'hidden'}}>
			<AbsoluteFill style={{transform: `scale(${sc})`, transformOrigin: origin, filter: `saturate(0.88) contrast(1.06) ${blur ? `blur(${blur}px)` : ''}`}}>
				<OffthreadVideo
					src={staticFile(`media/${src}`)}
					startFrom={Math.round(startFrom * fps)}
					muted
					style={{width: '100%', height: '100%', objectFit: 'cover'}}
				/>
			</AbsoluteFill>
			{dim > 0 && <AbsoluteFill style={{background: `rgba(5,6,8,${dim})`}} />}
		</AbsoluteFill>
	);
};

/* ---------- photo with Ken Burns, blurred fill for non 16:9 ---------- */

export const PhotoShot: React.FC<{
	src: string;
	from?: {x: number; y: number; s: number};
	to?: {x: number; y: number; s: number};
	fit?: 'cover' | 'contain';
	dim?: number;
	frame?: boolean; // archival print frame
	tilt?: number;
}> = ({src, from = {x: 0, y: 0, s: 1.0}, to = {x: 0, y: -10, s: 1.08}, fit = 'contain', dim = 0, frame: framed = false, tilt = 0}) => {
	const f = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const p = interpolate(f, [0, durationInFrames], [0, 1], {easing: Easing.inOut(Easing.cubic)});
	const x = from.x + (to.x - from.x) * p;
	const y = from.y + (to.y - from.y) * p;
	const sc = from.s + (to.s - from.s) * p;
	const bgShift = interpolate(p, [0, 1], [1.15, 1.25]);
	return (
		<AbsoluteFill style={{background: C.ink, overflow: 'hidden'}}>
			{fit === 'contain' && (
				<AbsoluteFill style={{transform: `scale(${bgShift})`}}>
					<Img src={staticFile(`blur/${src}`)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
				</AbsoluteFill>
			)}
			<AbsoluteFill
				style={{
					transform: `translate(${x}px, ${y}px) scale(${sc}) rotate(${tilt}deg)`,
					alignItems: 'center',
					justifyContent: 'center',
				}}
			>
				<Img
					src={staticFile(`media/${src}`)}
					style={{
						width: fit === 'cover' ? '100%' : undefined,
						height: fit === 'cover' ? '100%' : '86%',
						maxWidth: fit === 'contain' ? '88%' : undefined,
						objectFit: fit,
						filter: 'saturate(0.9) contrast(1.05)',
						boxShadow: framed ? '0 30px 80px rgba(0,0,0,0.65)' : undefined,
						border: framed ? '10px solid #ece6d8' : undefined,
					}}
				/>
			</AbsoluteFill>
			{dim > 0 && <AbsoluteFill style={{background: `rgba(5,6,8,${dim})`}} />}
		</AbsoluteFill>
	);
};

/* ---------- text elements ---------- */

export const Credit: React.FC<{text: string}> = ({text}) => {
	const o = useFade(12, 8);
	return (
		<div
			style={{
				position: 'absolute',
				right: 48,
				top: 40,
				fontFamily: SANS,
				fontSize: 19,
				letterSpacing: 0.3,
				color: 'rgba(244,241,234,0.78)',
				background: 'rgba(0,0,0,0.45)',
				padding: '6px 12px',
				borderRadius: 4,
				opacity: o,
			}}
		>
			{text}
		</div>
	);
};

export const LowerThird: React.FC<{name: string; role?: string; delay?: number; status?: Status}> = ({name, role, delay = 6, status}) => {
	const e = useEnter(delay, 18);
	const o = useFade(1, 10);
	return (
		<div style={{position: 'absolute', left: 96, bottom: 250, opacity: o}}>
			<div style={{display: 'flex', alignItems: 'stretch', transform: `translateX(${(1 - e) * -60}px)`, opacity: e, background: 'linear-gradient(90deg, rgba(6,7,9,0.88) 0%, rgba(6,7,9,0.72) 80%, rgba(6,7,9,0) 100%)', padding: '18px 60px 18px 22px', borderRadius: 6}}>
				<div style={{width: 8, background: status ? C[status] : C.gold, marginRight: 22, borderRadius: 2}} />
				<div>
					<div style={{fontFamily: SERIF, fontSize: 58, fontWeight: 700, color: C.text, lineHeight: 1.05, textShadow: '0 4px 20px rgba(0,0,0,0.7)'}}>{name}</div>
					{role && (
						<div style={{fontFamily: SANS, fontSize: 27, fontWeight: 500, color: C.gold, marginTop: 8, letterSpacing: 0.5, textShadow: '0 2px 12px rgba(0,0,0,0.8)'}}>
							{role}
						</div>
					)}
				</div>
			</div>
		</div>
	);
};

export const StatusBadge: React.FC<{status: Status; delay?: number; style?: React.CSSProperties; label?: string}> = ({status, delay = 0, style, label}) => {
	const e = useEnter(delay, 14);
	return (
		<div
			style={{
				display: 'inline-flex',
				alignItems: 'center',
				gap: 12,
				padding: '10px 20px',
				border: `2px solid ${C[status]}`,
				background: 'rgba(0,0,0,0.55)',
				color: C[status],
				fontFamily: SANS,
				fontWeight: 700,
				fontSize: 24,
				letterSpacing: 2,
				borderRadius: 4,
				transform: `scale(${0.85 + 0.15 * e})`,
				opacity: e,
				...style,
			}}
		>
			<div style={{width: 12, height: 12, borderRadius: 6, background: C[status]}} />
			{label ?? STATUS_LABEL[status]}
		</div>
	);
};

export const ChapterCard: React.FC<{n: string; title: string; bg?: React.ReactNode}> = ({n, title, bg}) => {
	const f = useCurrentFrame();
	const e = useEnter(2, 20);
	const e2 = useEnter(10, 20);
	const o = useFade(6, 10);
	const lineW = interpolate(f, [4, 30], [0, 360], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
	return (
		<AbsoluteFill style={{background: C.ink, opacity: o}}>
			{bg && <AbsoluteFill style={{opacity: 0.35}}>{bg}</AbsoluteFill>}
			<AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(8,9,11,0.92) 30%, rgba(8,9,11,0.55) 100%)'}} />
			<AbsoluteFill style={{justifyContent: 'center', paddingLeft: 170}}>
				<div style={{fontFamily: SANS, fontSize: 30, letterSpacing: 10, color: C.gold, fontWeight: 600, opacity: e, transform: `translateY(${(1 - e) * 20}px)`}}>
					{n}-SIR
				</div>
				<div style={{height: 3, width: lineW, background: C.red, margin: '26px 0 30px'}} />
				<div style={{fontFamily: SERIF, fontSize: 92, fontWeight: 700, color: C.text, maxWidth: 1400, lineHeight: 1.08, opacity: e2, transform: `translateY(${(1 - e2) * 30}px)`}}>
					{title}
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

export const BigText: React.FC<{kicker?: string; title: string; sub?: string; align?: 'center' | 'left'; size?: number; color?: string}> = ({kicker, title, sub, align = 'center', size = 100, color = C.text}) => {
	const e = useEnter(0, 20);
	const e2 = useEnter(12, 20);
	const o = useFade(8, 10);
	return (
		<AbsoluteFill style={{justifyContent: 'center', alignItems: align === 'center' ? 'center' : 'flex-start', paddingLeft: align === 'left' ? 170 : 0, opacity: o, textAlign: align}}>
			{kicker && (
				<div style={{fontFamily: SANS, fontSize: 28, letterSpacing: 8, color: C.gold, fontWeight: 600, marginBottom: 24, opacity: e}}>{kicker}</div>
			)}
			<div style={{fontFamily: SERIF, fontSize: size, fontWeight: 700, color, lineHeight: 1.08, maxWidth: 1500, opacity: e, transform: `translateY(${(1 - e) * 26}px) scale(${0.97 + 0.03 * e})`, textShadow: '0 8px 40px rgba(0,0,0,0.7)'}}>
				{title}
			</div>
			{sub && (
				<div style={{fontFamily: SANS, fontSize: 34, color: C.muted, marginTop: 28, maxWidth: 1300, opacity: e2, lineHeight: 1.35}}>{sub}</div>
			)}
		</AbsoluteFill>
	);
};

export const Panel: React.FC<{children: React.ReactNode; style?: React.CSSProperties; delay?: number}> = ({children, style, delay = 0}) => {
	const e = useEnter(delay, 20);
	return (
		<div
			style={{
				background: C.panel,
				border: `1px solid ${C.line}`,
				borderRadius: 10,
				padding: '40px 50px',
				boxShadow: '0 30px 90px rgba(0,0,0,0.5)',
				opacity: e,
				transform: `translateY(${(1 - e) * 30}px)`,
				...style,
			}}
		>
			{children}
		</div>
	);
};

export const DarkBg: React.FC<{children?: React.ReactNode}> = ({children}) => (
	<AbsoluteFill style={{background: 'radial-gradient(ellipse at 30% 20%, #1b1e24 0%, #0b0d10 60%, #060708 100%)'}}>{children}</AbsoluteFill>
);
