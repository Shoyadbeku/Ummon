import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {C, SANS, SERIF, Status, STATUS_LABEL} from '../theme';
import {DarkBg, Panel, StatusBadge, useEnter, useFade} from './Primitives';

/** Source / document card: an outlet, a date and what it published. */
export const DocCard: React.FC<{
	outlet: string;
	date: string;
	headline: string;
	lines?: {at: number; text: string}[]; // at = frames after scene start
	status: Status;
	quote?: {text: string; translation?: string; who: string};
	bg?: React.ReactNode;
}> = ({outlet, date, headline, lines = [], status, quote, bg}) => {
	const f = useCurrentFrame();
	const o = useFade(8, 10);
	return (
		<AbsoluteFill style={{opacity: o}}>
			{bg ?? <DarkBg />}
			{bg && <AbsoluteFill style={{background: 'rgba(6,7,9,0.72)'}} />}
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
				<Panel style={{width: 1340, padding: '54px 70px'}}>
					<div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
						<div style={{fontFamily: SANS, fontSize: 30, fontWeight: 800, letterSpacing: 3, color: C.gold}}>{outlet}</div>
						<div style={{fontFamily: SANS, fontSize: 28, color: C.muted, fontWeight: 500}}>{date}</div>
					</div>
					<div style={{height: 2, background: C.line, margin: '26px 0 30px'}} />
					<div style={{fontFamily: SERIF, fontSize: 54, fontWeight: 700, color: C.text, lineHeight: 1.18}}>{headline}</div>
					{quote && (
						<QuoteBlock quote={quote} />
					)}
					{lines.map((l, i) => {
						const e = interpolate(f - l.at, [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
						return (
							<div key={i} style={{display: 'flex', gap: 18, marginTop: 24, opacity: e, transform: `translateX(${(1 - e) * 20}px)`}}>
								<div style={{width: 10, height: 10, borderRadius: 5, background: C[status], marginTop: 16, flexShrink: 0}} />
								<div style={{fontFamily: SANS, fontSize: 34, color: C.text, lineHeight: 1.35}}>{l.text}</div>
							</div>
						);
					})}
					<div style={{marginTop: 36}}>
						<StatusBadge status={status} delay={14} />
					</div>
				</Panel>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

const QuoteBlock: React.FC<{quote: {text: string; translation?: string; who: string}}> = ({quote}) => {
	const e = useEnter(14, 20);
	return (
		<div style={{marginTop: 34, borderLeft: `5px solid ${C.gold}`, paddingLeft: 30, opacity: e}}>
			<div style={{fontFamily: SERIF, fontSize: 44, fontStyle: 'italic', color: C.text, lineHeight: 1.25}}>«{quote.text}»</div>
			{quote.translation && <div style={{fontFamily: SANS, fontSize: 31, color: C.muted, marginTop: 14, lineHeight: 1.35}}>{quote.translation}</div>}
			<div style={{fontFamily: SANS, fontSize: 25, color: C.gold, marginTop: 16, letterSpacing: 1}}>{quote.who}</div>
		</div>
	);
};

/** Three-tier truth legend used in intro and recap. */
export const Legend: React.FC<{times: number[]; highlight?: number}> = ({times}) => {
	const f = useCurrentFrame();
	const o = useFade(10, 12);
	const items: {status: Status; title: string; desc: string}[] = [
		{status: 'fact', title: 'Rasmiy faktlar', desc: 'Rasmiy hujjatlar va bayonotlar bilan tasdiqlangan'},
		{status: 'investigation', title: 'Jurnalistik surishtiruvlar', desc: 'Mustaqil jurnalistlarning tekshirilgan materiallari'},
		{status: 'unconfirmed', title: 'Tasdiqlanmagan da’volar', desc: 'Hali mustaqil tasdiqlanmagan ma’lumotlar'},
	];
	return (
		<AbsoluteFill style={{opacity: o}}>
			<DarkBg />
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', flexDirection: 'column', gap: 34}}>
				{items.map((it, i) => {
					const e = interpolate(f - times[i], [0, 16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
					return (
						<div
							key={i}
							style={{
								width: 1260,
								display: 'flex',
								alignItems: 'center',
								gap: 36,
								padding: '30px 44px',
								background: 'rgba(255,255,255,0.04)',
								borderLeft: `10px solid ${C[it.status]}`,
								borderRadius: 8,
								opacity: e,
								transform: `translateX(${(1 - e) * -50}px)`,
							}}
						>
							<div style={{fontFamily: SANS, fontSize: 24, fontWeight: 800, letterSpacing: 2, color: C[it.status], width: 380}}>{STATUS_LABEL[it.status]}</div>
							<div>
								<div style={{fontFamily: SERIF, fontSize: 46, fontWeight: 700, color: C.text}}>{it.title}</div>
								<div style={{fontFamily: SANS, fontSize: 27, color: C.muted, marginTop: 6}}>{it.desc}</div>
							</div>
						</div>
					);
				})}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

/** Big date / number card. */
export const DateCard: React.FC<{big: string; small?: string; sub?: string; status?: Status; bg?: React.ReactNode}> = ({big, small, sub, status, bg}) => {
	const e = useEnter(0, 16);
	const e2 = useEnter(10, 20);
	const o = useFade(8, 10);
	return (
		<AbsoluteFill style={{opacity: o}}>
			{bg ?? <DarkBg />}
			{bg && <AbsoluteFill style={{background: 'rgba(6,7,9,0.7)'}} />}
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', flexDirection: 'column'}}>
				{small && <div style={{fontFamily: SANS, fontSize: 34, letterSpacing: 10, color: C.gold, fontWeight: 600, opacity: e2}}>{small}</div>}
				<div style={{fontFamily: SERIF, fontSize: 230, fontWeight: 800, color: C.text, lineHeight: 1, opacity: e, transform: `scale(${1.15 - 0.15 * e})`, letterSpacing: -4}}>{big}</div>
				{sub && <div style={{fontFamily: SANS, fontSize: 38, color: C.text, marginTop: 30, opacity: e2, maxWidth: 1300, textAlign: 'center', lineHeight: 1.35}}>{sub}</div>}
				{status && <div style={{marginTop: 40}}><StatusBadge status={status} delay={16} /></div>}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

/** Counter for money / years. */
export const Counter: React.FC<{to: number; prefix?: string; suffix?: string; label: string; status?: Status; note?: string}> = ({to, prefix = '', suffix = '', label, status, note}) => {
	const f = useCurrentFrame();
	const o = useFade(8, 10);
	const v = interpolate(f, [6, 60], [0, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
	const formatted = Math.round(v).toLocaleString('en-US').replace(/,/g, ' ');
	return (
		<AbsoluteFill style={{opacity: o}}>
			<DarkBg />
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', flexDirection: 'column'}}>
				<div style={{fontFamily: SANS, fontSize: 32, letterSpacing: 8, color: C.gold, fontWeight: 600}}>{label}</div>
				<div style={{fontFamily: SERIF, fontSize: 190, fontWeight: 800, color: C.text, marginTop: 10, fontVariantNumeric: 'tabular-nums'}}>
					{prefix}
					{formatted}
					{suffix}
				</div>
				{note && <div style={{fontFamily: SANS, fontSize: 32, color: C.muted, marginTop: 10}}>{note}</div>}
				{status && <div style={{marginTop: 36}}><StatusBadge status={status} delay={20} /></div>}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

/** Chips / bullet list that reveal in sync with speech. */
export const Chips: React.FC<{title?: string; items: {at: number; text: string}[]; status?: Status; bg?: React.ReactNode; footer?: {at: number; text: string}}> = ({title, items, status, bg, footer}) => {
	const f = useCurrentFrame();
	const o = useFade(8, 10);
	const fe = footer ? interpolate(f - footer.at, [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0;
	return (
		<AbsoluteFill style={{opacity: o}}>
			{bg ?? <DarkBg />}
			{bg && <AbsoluteFill style={{background: 'rgba(6,7,9,0.74)'}} />}
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', flexDirection: 'column'}}>
				{title && <div style={{fontFamily: SERIF, fontSize: 64, fontWeight: 700, color: C.text, marginBottom: 54, textAlign: 'center', maxWidth: 1500, lineHeight: 1.15}}>{title}</div>}
				<div style={{display: 'flex', gap: 28, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 1600}}>
					{items.map((it, i) => {
						const e = interpolate(f - it.at, [0, 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.back(1.6))});
						return (
							<div
								key={i}
								style={{
									fontFamily: SANS,
									fontSize: 40,
									fontWeight: 600,
									color: C.text,
									padding: '24px 40px',
									border: `2px solid ${status ? C[status] : C.gold}`,
									borderRadius: 8,
									background: 'rgba(0,0,0,0.5)',
									opacity: e,
									transform: `scale(${0.8 + 0.2 * e})`,
								}}
							>
								{it.text}
							</div>
						);
					})}
				</div>
				{footer && <div style={{fontFamily: SANS, fontSize: 34, color: C.muted, marginTop: 56, opacity: fe, fontStyle: 'italic'}}>{footer.text}</div>}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

/** Name cards without photos (used where no licensed photo exists or for minors). */
export const NameCards: React.FC<{names: {name: string; sub?: string; at: number}[]; caption?: string; status: Status; title?: string}> = ({names, caption, status, title}) => {
	const f = useCurrentFrame();
	const o = useFade(8, 10);
	return (
		<AbsoluteFill style={{opacity: o}}>
			<DarkBg />
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', flexDirection: 'column'}}>
				{title && <div style={{fontFamily: SERIF, fontSize: 60, fontWeight: 700, color: C.text, marginBottom: 50}}>{title}</div>}
				<div style={{display: 'flex', gap: 60}}>
					{names.map((n, i) => {
						const e = interpolate(f - n.at, [0, 16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
						return (
							<div
								key={i}
								style={{
									width: 620,
									padding: '56px 40px',
									textAlign: 'center',
									border: `1px solid ${C.line}`,
									borderTop: `6px solid ${C[status]}`,
									background: 'rgba(255,255,255,0.035)',
									borderRadius: 10,
									opacity: e,
									transform: `translateY(${(1 - e) * 40}px)`,
								}}
							>
								<div style={{fontFamily: SERIF, fontSize: 76, fontWeight: 700, color: C.text}}>{n.name}</div>
								{n.sub && <div style={{fontFamily: SANS, fontSize: 30, color: C.muted, marginTop: 16, lineHeight: 1.35}}>{n.sub}</div>}
							</div>
						);
					})}
				</div>
				{caption && <div style={{fontFamily: SANS, fontSize: 30, color: C.muted, marginTop: 50}}>{caption}</div>}
				<div style={{marginTop: 34}}>
					<StatusBadge status={status} delay={20} />
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

/** Age gap infographic. */
export const AgeGap: React.FC = () => {
	const f = useCurrentFrame();
	const o = useFade(8, 10);
	const w = interpolate(f, [10, 50], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
	const total = 1300;
	const x1 = 0;
	const x2 = (31 / 40) * total;
	return (
		<AbsoluteFill style={{opacity: o}}>
			<DarkBg />
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
				<div style={{position: 'relative', width: total, height: 300}}>
					<div style={{position: 'absolute', top: 150, left: 0, height: 4, width: total * w, background: C.line}} />
					<div style={{position: 'absolute', top: 146, left: x1, height: 12, width: x2 * w, background: C.gold, borderRadius: 6}} />
					{[{x: x1, y: '1952', n: 'Vladimir Putin'}, {x: x2, y: '1983', n: 'Alina Kabayeva'}].map((p, i) => {
						const e = interpolate(f, [i === 0 ? 4 : 44, i === 0 ? 20 : 60], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
						return (
							<div key={i} style={{position: 'absolute', left: p.x - 90, top: 60, width: 180, textAlign: 'center', opacity: e}}>
								<div style={{fontFamily: SANS, fontSize: 26, color: C.muted}}>{p.n}</div>
								<div style={{width: 26, height: 26, borderRadius: 13, background: C.text, margin: '30px auto 0'}} />
								<div style={{fontFamily: SERIF, fontSize: 64, fontWeight: 700, color: C.text, marginTop: 30}}>{p.y}</div>
							</div>
						);
					})}
					<div style={{position: 'absolute', left: x2 / 2 - 260, top: -40, width: 520, textAlign: 'center', fontFamily: SERIF, fontSize: 72, fontWeight: 800, color: C.gold, opacity: w}}>
						≈ 30 yil farq
					</div>
				</div>
			</AbsoluteFill>
			<div style={{position: 'absolute', bottom: 290, width: '100%', textAlign: 'center', fontFamily: SANS, fontSize: 24, color: C.muted}}>
				Tug‘ilgan yillar: ochiq biografik ma’lumotlar
			</div>
		</AbsoluteFill>
	);
};

/** Recap timeline. */
export const Timeline: React.FC<{events: {year: string; text: string; status: Status; at: number}[]}> = ({events}) => {
	const f = useCurrentFrame();
	const o = useFade(10, 12);
	const lineP = interpolate(f, [0, 40], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
	const step = 1640 / (events.length - 1);
	return (
		<AbsoluteFill style={{opacity: o}}>
			<DarkBg />
			<div style={{position: 'absolute', left: 140, top: 470, height: 4, width: 1640 * lineP, background: C.line}} />
			{events.map((ev, i) => {
				const e = interpolate(f - ev.at, [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
				const up = i % 2 === 0;
				return (
					<div key={i} style={{position: 'absolute', left: 140 + i * step - 120, top: up ? 240 : 500, width: 240, textAlign: 'center', opacity: e, transform: `translateY(${(1 - e) * (up ? -20 : 20)}px)`}}>
						{up ? (
							<>
								<div style={{fontFamily: SERIF, fontSize: 56, fontWeight: 800, color: C[ev.status]}}>{ev.year}</div>
								<div style={{fontFamily: SANS, fontSize: 25, color: C.text, marginTop: 8, lineHeight: 1.3, minHeight: 100}}>{ev.text}</div>
								<div style={{width: 22, height: 22, borderRadius: 11, background: C[ev.status], margin: '0 auto', border: '4px solid #0b0d10'}} />
							</>
						) : (
							<>
								<div style={{width: 22, height: 22, borderRadius: 11, background: C[ev.status], margin: '-11px auto 18px', border: '4px solid #0b0d10'}} />
								<div style={{fontFamily: SERIF, fontSize: 56, fontWeight: 800, color: C[ev.status]}}>{ev.year}</div>
								<div style={{fontFamily: SANS, fontSize: 25, color: C.text, marginTop: 8, lineHeight: 1.3}}>{ev.text}</div>
							</>
						)}
					</div>
				);
			})}
		</AbsoluteFill>
	);
};

/** Split screen: public life vs private life. */
export const SplitScreen: React.FC<{left: React.ReactNode; right: React.ReactNode; leftLabel: string; rightLabel: string; rightAt: number}> = ({left, right, leftLabel, rightLabel, rightAt}) => {
	const f = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const o = useFade(10, 12);
	const r = interpolate(f - rightAt, [0, 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
	const leftW = interpolate(r, [0, 1], [1920, 960]);
	return (
		<AbsoluteFill style={{opacity: o, background: C.ink}}>
			<div style={{position: 'absolute', left: 960, top: 0, width: 960, height: 1080, overflow: 'hidden', opacity: r}}>{right}</div>
			<div style={{position: 'absolute', left: 0, top: 0, width: leftW, height: 1080, overflow: 'hidden'}}>{left}</div>
			<div style={{position: 'absolute', left: 959, top: 0, width: 3, height: 1080, background: C.gold, opacity: r}} />
			<Label text={leftLabel} x={leftW / 2} />
			<div style={{opacity: r}}>
				<Label text={rightLabel} x={1440} />
			</div>
			<div style={{display: 'none'}}>{durationInFrames}</div>
		</AbsoluteFill>
	);
};

const Label: React.FC<{text: string; x: number}> = ({text, x}) => (
	<div style={{position: 'absolute', top: 90, left: x - 300, width: 600, textAlign: 'center'}}>
		<span style={{fontFamily: SANS, fontSize: 30, fontWeight: 800, letterSpacing: 8, color: C.text, background: 'rgba(0,0,0,0.6)', padding: '12px 26px', borderRadius: 4}}>{text}</span>
	</div>
);

/** Document image (screenshot) shown as paper. */
export const DocImage: React.FC<{src: string; header: string; date: string; status: Status; caption?: string; top?: string}> = ({src, header, date, status, caption, top}) => {
	const f = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const o = useFade(8, 10);
	const e = useEnter(0, 20);
	const sc = interpolate(f, [0, durationInFrames], [1.0, 1.06]);
	return (
		<AbsoluteFill style={{opacity: o}}>
			<DarkBg />
			<AbsoluteFill style={{alignItems: 'center', paddingTop: 70}}>
				<div style={{display: 'flex', gap: 30, alignItems: 'center', opacity: e}}>
					<div style={{fontFamily: SANS, fontSize: 30, fontWeight: 800, letterSpacing: 3, color: C.gold}}>{header}</div>
					<div style={{fontFamily: SANS, fontSize: 28, color: C.muted}}>{date}</div>
					<StatusBadge status={status} delay={10} />
				</div>
				{top && (
					<Img src={staticFile(`media/${top}`)} style={{width: 1300, marginTop: 30, borderRadius: 6, opacity: e, boxShadow: '0 20px 60px rgba(0,0,0,0.6)'}} />
				)}
				<div style={{marginTop: 36, transform: `scale(${sc}) translateY(${(1 - e) * 40}px)`, opacity: e}}>
					<Img src={staticFile(`media/${src}`)} style={{width: 1300, borderRadius: 6, boxShadow: '0 30px 90px rgba(0,0,0,0.7)', border: '14px solid #fff'}} />
				</div>
				{caption && <div style={{fontFamily: SANS, fontSize: 28, color: C.muted, marginTop: 26}}>{caption}</div>}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

export const QuestionMarks: React.FC = () => {
	const f = useCurrentFrame();
	return (
		<AbsoluteFill style={{background: 'radial-gradient(ellipse at center, #1a1c21 0%, #08090b 75%)', justifyContent: 'center', alignItems: 'center'}}>
			<div style={{fontFamily: SERIF, fontSize: 420, color: 'rgba(216,180,106,0.18)', fontWeight: 800, transform: `scale(${1 + 0.04 * Math.sin(f / 20)})`}}>?</div>
		</AbsoluteFill>
	);
};
