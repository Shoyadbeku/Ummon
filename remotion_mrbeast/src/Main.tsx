import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import '@fontsource/anton/400.css';
import '@fontsource/anton/latin-ext-400.css';
import '@fontsource/montserrat/700.css';
import '@fontsource/montserrat/800.css';
import '@fontsource/montserrat/900.css';
import '@fontsource/montserrat/latin-ext-800.css';
import {AUDIO_END, BEAT, DURATION, SFX, SHOTS, SPEECH, f} from './timeline';
import {
	COLORS,
	Chip,
	Corners,
	Counter,
	Credit,
	FONT_BODY,
	FONT_HEAD,
	Flash,
	Footage,
	Glitch,
	Grain,
	Kinetic,
	LightLeak,
	Scrim,
	Shapes,
	SvgFilters,
	Vignette,
	useShake,
} from './components/fx';
import {BudgetBars, Blueprint, Globe, IdCard, PlayerGrid, PlayerUI, Poll, RecUI, ScaleMeter} from './components/graphics';
import {IMG} from './media';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Sahna o‘rami: SHOTS dagi vaqt bo‘yicha Sequence
const Shot: React.FC<{k: keyof typeof SHOTS; children: (dur: number, rel: (sec: number) => number) => React.ReactNode}> = ({k, children}) => {
	const [a, b] = SHOTS[k];
	const from = f(a);
	const dur = f(b) - from;
	const rel = (sec: number) => f(sec) - from; // absolyut sekund → sahna ichidagi kadr
	return (
		<Sequence from={from} durationInFrames={dur} premountFor={45} name={k}>
			{children(dur, rel)}
		</Sequence>
	);
};

// Beatga mos yengil "puls" (musiqaga sinxron)
const useBeatPulse = (amount = 0.012) => {
	const frame = useCurrentFrame();
	const t = frame / 30;
	const ph = (t % BEAT) / BEAT;
	return 1 + amount * Math.exp(-ph * 7);
};

const Scenes: React.FC = () => {
	const pulse = useBeatPulse();
	const shake = useShake([f(0), f(3.34), f(6.42), f(13.3), f(17.92), f(33.7), f(35.62)], 16, 10);
	return (
		<AbsoluteFill style={{transform: `${shake} scale(${pulse})`}}>
			{/* 1 — HOOK: "Tasavvur qiling" */}
			<Shot k="hookEye">
				{(dur) => (
					<>
						<Glitch at={0} len={8}>
							<Footage src="video/46741.mp4" trim={0.6} dur={dur} zoom={[1.0, 1.25]} objectPosition="45% 45%" grade="contrast(1.3) saturate(0.7) brightness(1.05)" enter="none" />
						</Glitch>
						<AbsoluteFill style={{background: 'radial-gradient(circle, rgba(0,0,0,0) 30%, rgba(0,0,0,0.75) 100%)'}} />
						<Kinetic
							top={700}
							size={190}
							words={[
								{t: 'TASAVVUR', at: 1},
								{t: 'QILING', at: 6, color: COLORS.pink},
							]}
						/>
						<Flash at={0} len={6} />
					</>
				)}
			</Shot>

			{/* 2 — "bir bloger videosi uchun" */}
			<Shot k="vlogger">
				{(dur, rel) => (
					<>
						<Sequence durationInFrames={rel(1.58)}>
							<Footage src="video/34477.mp4" trim={2} dur={rel(1.58)} enter="whip" zoom={[1.0, 1.08]} />
						</Sequence>
						<Sequence from={rel(1.58)}>
							<Footage src="video/23485.mp4" trim={6} dur={dur - rel(1.58)} enter="punch" zoom={[1.05, 1.15]} objectPosition="20% 50%" grade="contrast(1.12) saturate(1.1) brightness(1.15)" />
							<Flash at={0} len={4} peak={0.6} />
						</Sequence>
						<Scrim />
						<Corners />
						<RecUI />
						<Kinetic top={1180} size={120} words={[{t: '1 ta bloger', at: rel(1.58), color: COLORS.gold}, {t: 'videosi uchun', at: rel(2.12)}]} />
					</>
				)}
			</Shot>

			{/* 3 — "haqiqiy Squid Game" */}
			<Shot k="guards">
				{(dur, rel) => (
					<>
						<Footage src={IMG.guards.file} kind="image" dur={dur} zoom={[1.15, 1.3]} pan={[0, 30, 0, -20]} enter="whip" grade="contrast(1.15) saturate(1.25)" blurBg fit="cover" objectPosition="50% 40%" />
						<AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(255,46,126,0.0) 40%, rgba(40,0,15,0.85) 100%)'}} />
						<Chip text="HAQIQIY" at={rel(2.92)} top={1060} center color="#fff" textColor={COLORS.ink} size={44} />
						<Kinetic top={1150} size={210} words={[{t: 'SQUID', at: rel(3.34), color: COLORS.pink}, {t: 'GAME', at: rel(3.74)}]} />
						<Shapes at={rel(3.4)} top={430} size={110} />
						<Flash at={rel(3.34)} len={5} color={COLORS.pink} peak={0.5} />
						<Credit text={IMG.guards.credit} />
					</>
				)}
			</Shot>

			{/* 4 — "maydonini qurdirgan" */}
			<Shot k="build">
				{(dur, rel) => (
					<>
						<Footage src="video/9686.mp4" trim={4} rate={2.2} dur={dur} enter="punch" zoom={[1.1, 1.25]} grade="contrast(1.2) saturate(0.9) hue-rotate(-8deg)" />
						<AbsoluteFill style={{background: 'rgba(5,20,40,0.45)'}} />
						<Blueprint dur={dur} />
						<Kinetic top={330} size={130} words={[{t: 'MAYDONNI', at: 2}, {t: 'QURDIRDI', at: rel(4.86), color: COLORS.gold}]} />
						<LightLeak dur={dur} seed={2} />
					</>
				)}
			</Shot>

			{/* 5 — "Bu inson — MrBeast" */}
			<Shot k="mrbeast">
				{(dur, rel) => (
					<>
						<Footage src={IMG.mrbeast.file} kind="image" dur={dur} zoom={[1.0, 1.14]} pan={[0, 40, 0, -10]} enter="zoomblur" blurBg fit="cover" objectPosition="50% 22%" grade="contrast(1.1) saturate(1.15)" />
						<Scrim top={0.2} bottom={0.85} />
						<Kinetic top={1110} size={96} font={FONT_BODY} words={[{t: 'Bu inson', at: 0}]} />
						<Kinetic top={1230} size={250} words={[{t: 'MrBEAST', at: rel(6.42), color: COLORS.gold}]} />
						<Flash at={rel(6.42)} len={5} peak={0.7} />
						<LightLeak dur={dur} seed={4} color="255,190,60" peak={0.4} />
						<Credit text={IMG.mrbeast.credit} />
					</>
				)}
			</Shot>

			{/* 6 — "asl ismi Jimmy Donaldson" */}
			<Shot k="idcard">
				{(dur, rel) => (
					<>
						<Footage src={IMG.mrbeast2.file} kind="image" dur={dur} zoom={[1.25, 1.35]} enter="punch" blurBg fit="cover" objectPosition="50% 25%" grade="blur(18px) brightness(0.5) saturate(1.2)" />
						<AbsoluteFill style={{background: 'linear-gradient(160deg, rgba(255,46,126,0.25), rgba(19,183,155,0.2))'}} />
						<IdCard start={2} nameAt={rel(8.38)} photo={IMG.mrbeast2.file} />
						<SignatureReveal start={rel(8.7)} />
						<Credit text={IMG.mrbeast2.credit} />
					</>
				)}
			</Shot>

			{/* 7 — "2021-yilda" */}
			<Shot k="year">
				{(dur) => (
					<>
						<Footage src="video/39474.mp4" trim={1} dur={dur} enter="whip" zoom={[1.2, 1.35]} grade="contrast(1.2) saturate(1.3) brightness(0.55) blur(3px)" />
						<YearRoll dur={dur} />
					</>
				)}
			</Shot>

			{/* 8 — "mashhur Koreya serialidan" — globus */}
			<Shot k="globe">{(dur) => <Globe dur={dur} />}</Shot>

			{/* 9 — "ilhomlangan" — Koreya bayrog‘i, Seul */}
			<Shot k="flag">
				{(dur) => (
					<>
						<Footage src="video/8825.mp4" trim={3} dur={dur} enter="punch" zoom={[1.3, 1.45]} grade="contrast(1.15) saturate(1.1)" />
						<Scrim />
						<Kinetic top={1250} size={110} words={[{t: 'serialdan', at: 0}, {t: 'ilhomlanib', at: 6, color: COLORS.pink}]} />
					</>
				)}
			</Shot>

			{/* 10 — "ulkan musobaqa tashkil qildi" */}
			<Shot k="contest">
				{(dur, rel) => (
					<>
						<Sequence durationInFrames={rel(14.62)}>
							<Footage src={IMG.players.file} kind="image" dur={rel(14.62)} zoom={[1.12, 1.25]} pan={[30, 0, -30, 0]} enter="zoomblur" blurBg objectPosition="50% 40%" grade="contrast(1.15) saturate(1.2)" />
							<Credit text={IMG.players.credit} />
						</Sequence>
						<Sequence from={rel(14.62)}>
							<Footage src={IMG.promo.file} kind="image" dur={dur - rel(14.62)} zoom={[1.1, 1.2]} enter="punch" blurBg objectPosition="50% 45%" grade="contrast(1.15) saturate(1.2)" />
							<Credit text={IMG.promo.credit} />
						</Sequence>
						<Scrim top={0.6} bottom={0.75} />
						<Kinetic top={300} size={200} words={[{t: 'ULKAN', at: 0, color: COLORS.gold}, {t: 'MUSOBAQA', at: rel(14.04)}]} />
						<Chip text="2021" at={rel(14.62)} top={760} center color={COLORS.pink} size={46} />
						<Flash at={0} len={6} peak={0.7} />
					</>
				)}
			</Shot>

			{/* 11 — "Unda 456 nafar ishtirokchi qatnashdi" */}
			<Shot k="players">
				{(dur, rel) => (
					<>
						<Footage src="video/13192.mp4" trim={2} dur={dur} enter="slideUp" zoom={[1.2, 1.3]} grade="contrast(1.1) saturate(0.4) brightness(0.35) blur(6px)" />
						<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 55%, rgba(19,183,155,0.25), rgba(0,0,0,0.6))'}} />
						<Kinetic top={420} size={200} words={[{t: 'UNDA…', at: 0}]} exitAt={rel(15.9)} />
						<Counter to={456} start={rel(15.96)} dur={30} top={300} size={300} color="#fff" glow={COLORS.teal} />
						<Kinetic top={600} size={72} font={FONT_BODY} words={[{t: 'nafar', at: rel(16.32)}, {t: 'ishtirokchi', at: rel(17.02), color: COLORS.teal}]} />
						<PlayerGrid start={rel(15.96)} fill={rel(17.9) - rel(15.96)} />
					</>
				)}
			</Shot>

			{/* 12 — "G‘olib uchun" */}
			<Shot k="winner">
				{(dur) => (
					<>
						<Footage src="video/8890.mp4" trim={3.2} dur={dur} enter="punch" zoom={[1.15, 1.3]} grade="contrast(1.2) saturate(1.2)" objectPosition="45% 50%" />
						<Scrim />
						<Kinetic top={1200} size={190} words={[{t: 'G‘OLIB', at: 1, color: COLORS.gold}]} />
						<Flash at={0} len={5} peak={0.8} />
					</>
				)}
			</Shot>

			{/* 13 — "456 000 dollar mukofot belgilandi" */}
			<Shot k="prize">
				{(dur, rel) => (
					<>
						<Sequence durationInFrames={rel(20.28)}>
							<Footage src="video/18262.mp4" trim={1} dur={rel(20.28)} enter="punch" zoom={[1.1, 1.22]} grade="contrast(1.15) saturate(1.1) brightness(0.7)" />
						</Sequence>
						<Sequence from={rel(20.28)}>
							<Footage src="video/18305.mp4" trim={3} dur={dur - rel(20.28)} enter="zoomblur" zoom={[1.1, 1.2]} grade="contrast(1.15) saturate(1.1) brightness(0.65)" />
						</Sequence>
						<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 45%, rgba(255,197,61,0.18), rgba(0,0,0,0.55))'}} />
						<Counter to={456000} start={0} dur={rel(20.28)} top={700} size={185} prefix="$" color={COLORS.gold} glow="rgba(255,197,61,0.8)" />
						<Chip text="MUKOFOT" at={rel(20.58)} top={600} center color={COLORS.gold} textColor={COLORS.ink} size={48} />
						<Kinetic top={960} size={70} font={FONT_BODY} words={[{t: 'g‘olibga', at: rel(20.58)}, {t: 'belgilandi', at: rel(21.1), color: COLORS.gold}]} />
						<CoinBurst at={rel(20.2)} />
					</>
				)}
			</Shot>

			{/* 14 — "MrBeast'ning aytishicha, loyiha uchun" */}
			<Shot k="quote">
				{(dur, rel) => (
					<>
						<Footage src={IMG.mrbeast3.file} kind="image" dur={dur} zoom={[1.0, 1.07]} pan={[-30, 70, 30, 90]} enter="whip" blurBg fit="cover" objectPosition="50% 30%" grade="contrast(1.1) saturate(1.1)" />
						<Scrim top={0.3} bottom={0.85} />
						<QuoteCard at={rel(22.62)} />
						<Credit text={IMG.mrbeast3.credit} />
					</>
				)}
			</Shot>

			{/* 15 — "taxminan 3,5 million dollar sarflangan" */}
			<Shot k="budget">
				{(dur, rel) => (
					<>
						<Footage src="video/45703.mp4" trim={2} dur={dur} enter="punch" zoom={[1.15, 1.3]} grade="contrast(1.1) saturate(0.8) brightness(0.45) blur(4px)" />
						<AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.5), rgba(0,0,0,0.2) 40%, rgba(0,0,0,0.75))'}} />
						<Chip text="TAXMINAN" at={0} top={330} center color="#fff" textColor={COLORS.ink} size={44} />
						<Counter from={0} to={3.5} start={rel(24.4)} dur={rel(25.5) - rel(24.4)} top={440} size={250} prefix="$" suffix=" MLN" color={COLORS.gold} glow="rgba(255,197,61,0.7)" format={(n) => n.toFixed(1).replace('.', ',')} />
						<Kinetic top={730} size={74} font={FONT_BODY} words={[{t: 'loyihaga', at: rel(25.6)}, {t: 'sarflangan', at: rel(26.36), color: COLORS.gold}]} />
						<BudgetBars start={rel(25.1)} />
						<LightLeak dur={dur} seed={6} color="255,190,60" peak={0.35} />
					</>
				)}
			</Shot>

			{/* 16 — "Eng qizig‘i" */}
			<Shot k="twist">
				{(dur) => (
					<>
						<Glitch at={0} len={6}>
							<Footage src="video/4508.mp4" trim={1.2} dur={dur} enter="none" zoom={[1.25, 1.4]} grade="contrast(1.2) saturate(1.1)" objectPosition="50% 40%" />
						</Glitch>
						<Scrim />
						<Kinetic top={1180} size={170} words={[{t: 'ENG', at: 0}, {t: 'QIZIG‘I…', at: 9, color: COLORS.pink}]} />
					</>
				)}
			</Shot>

			{/* 17 — "bu oddiy YouTube video edi" */}
			<Shot k="youtube">
				{(dur, rel) => (
					<>
						<Footage src="video/41273.mp4" trim={2} dur={dur} enter="whip" zoom={[1.1, 1.2]} grade="contrast(1.1) saturate(1.05) brightness(0.55) blur(5px)" />
						<PlayerUI start={2} />
						<Kinetic top={330} size={150} words={[{t: 'ODDIY', at: 0, color: COLORS.gold}, {t: 'YOUTUBE', at: rel(28.82)}, {t: 'VIDEO', at: rel(29.14)}]} />
					</>
				)}
			</Shot>

			{/* 18 — "Ammo uning ishlab chiqarish ko‘lami" */}
			<Shot k="crew">
				{(dur, rel) => (
					<>
						<Sequence durationInFrames={rel(30.72)}>
							<Footage src="video/46353.mp4" trim={2.5} dur={rel(30.72)} enter="punch" zoom={[1.15, 1.25]} grade="contrast(1.2) saturate(1.05)" />
						</Sequence>
						<Sequence from={rel(30.72)}>
							<Footage src="video/22973.mp4" trim={4} dur={dur - rel(30.72)} enter="whip" zoom={[1.1, 1.2]} grade="contrast(1.15) saturate(1.1)" />
						</Sequence>
						<Scrim />
						<Kinetic top={300} size={150} words={[{t: 'AMMO…', at: 0, color: COLORS.pink}]} exitAt={rel(30.72)} />
						<Kinetic top={1180} size={110} words={[{t: 'ishlab chiqarish', at: rel(30.72)}, {t: 'ko‘lami', at: rel(31.42), color: COLORS.gold}]} />
					</>
				)}
			</Shot>

			{/* 19 — Split screen: TV vs YouTube */}
			<Shot k="split">
				{(dur, rel) => <SplitScene dur={dur} rel={rel} />}
			</Shot>

			{/* 20 — "Siz shunday" — qo‘g‘irchoq */}
			<Shot k="doll">
				{(dur) => (
					<>
						<Footage src={IMG.doll.file} kind="image" dur={dur} zoom={[1.1, 1.3]} enter="zoomblur" blurBg objectPosition="13% 30%" grade="contrast(1.25) saturate(1.1) brightness(0.85)" />
						<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 40%, rgba(0,0,0,0) 20%, rgba(80,0,10,0.75) 100%)'}} />
						<Kinetic top={1220} size={160} words={[{t: 'SIZ-CHI?', at: 2, color: '#fff'}]} />
						<Credit text={IMG.doll.credit} />
					</>
				)}
			</Shot>

			{/* 21 — "o‘yinda qatnasharmidingiz?" + outro */}
			<Shot k="question">
				{(dur, rel) => (
					<>
						<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 60%, #5a0f2c 0%, #1a0710 55%, #07080B 100%)'}} />
						<AbsoluteFill style={{filter: 'url(#chroma) brightness(0.8) contrast(1.1)', opacity: 0.55}}>
							<Footage src="video/47495.mp4" trim={1} dur={dur} enter="none" zoom={[1.55, 1.65]} objectPosition="50% 30%" grade="none" />
						</AbsoluteFill>
						<AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(7,8,11,0.65) 0%, rgba(7,8,11,0.2) 45%, rgba(7,8,11,0.85) 100%)'}} />
						<Shapes at={0} top={300} size={100} gap={50} />
						<Kinetic
							top={520}
							size={140}
							words={[
								{t: 'SHUNDAY', at: 0},
								{t: 'O‘YINDA', at: rel(35.62), color: COLORS.pink},
								{t: 'QATNASHAR-', at: rel(35.9)},
								{t: 'MIDINGIZ?', at: rel(36.2), color: COLORS.gold},
							]}
						/>
						<Poll start={rel(36.8)} />
						<Chip text="Izohda yozing ↓" at={rel(37.1)} top={1360} center color="rgba(255,255,255,0.14)" size={38} />
						<Flash at={0} len={5} color={COLORS.pink} peak={0.5} />
					</>
				)}
			</Shot>
		</AbsoluteFill>
	);
};

// ───── kichik sahna komponentlari ─────
const SignatureReveal: React.FC<{start: number}> = ({start}) => {
	const frame = useCurrentFrame();
	const p = interpolate(frame, [start, start + 18], [0, 100], clamp);
	if (!IMG.signature.ok) return null;
	return (
		<Img
			src={staticFile(IMG.signature.file)}
			style={{
				position: 'absolute',
				top: 1380,
				left: 560,
				width: 380,
				filter: 'invert(1) drop-shadow(0 0 12px rgba(255,255,255,0.6))',
				clipPath: `inset(0 ${100 - p}% 0 0)`,
				opacity: 0.95,
			}}
		/>
	);
};

const YearRoll: React.FC<{dur: number}> = ({dur}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const years = [2017, 2018, 2019, 2020, 2021];
	const p = interpolate(frame, [2, 26], [0, years.length - 1], {...clamp, easing: (t) => 1 - Math.pow(1 - t, 3)});
	const land = spring({frame: frame - 26, fps, config: {damping: 9, stiffness: 200}});
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: 640, width: 1080, height: 330, overflow: 'hidden', WebkitMaskImage: 'linear-gradient(transparent, #000 25%, #000 75%, transparent)'}}>
				{years.map((y, i) => (
					<div
						key={y}
						style={{
							position: 'absolute',
							top: (i - p) * 330,
							width: 1080,
							textAlign: 'center',
							fontFamily: FONT_HEAD,
							fontSize: 330,
							lineHeight: '330px',
							color: y === 2021 ? COLORS.pink : 'rgba(255,255,255,0.85)',
							transform: y === 2021 ? `scale(${1 + 0.1 * land * (1 - land) * 4})` : undefined,
							textShadow: y === 2021 ? `0 0 50px ${COLORS.pink}` : undefined,
						}}
					>
						{y}
					</div>
				))}
			</div>
			<Chip text="yilda" at={20} top={1010} center color="#fff" textColor={COLORS.ink} size={48} />
			<div style={{position: 'absolute', top: 1140, width: 1080, textAlign: 'center', fontFamily: FONT_BODY, fontWeight: 800, fontSize: 52, color: '#fff', opacity: interpolate(frame, [dur - 18, dur - 8], [0, 1], clamp), letterSpacing: 2}}>
				mashhur Koreya seriali…
			</div>
		</AbsoluteFill>
	);
};

const CoinBurst: React.FC<{at: number}> = ({at}) => {
	const frame = useCurrentFrame();
	const d = frame - at;
	if (d < 0 || d > 40) return null;
	return (
		<AbsoluteFill>
			{Array.from({length: 26}).map((_, i) => {
				const ang = (i / 26) * Math.PI * 2 + i;
				const v = 18 + (i % 5) * 6;
				const x = 540 + Math.cos(ang) * v * d;
				const y = 800 + Math.sin(ang) * v * d + 0.9 * d * d;
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: x,
							top: y,
							width: 34,
							height: 34,
							borderRadius: 17,
							background: 'radial-gradient(circle at 35% 35%, #fff6c8, #ffc53d 45%, #b07800)',
							opacity: 1 - d / 40,
							transform: `scaleX(${Math.abs(Math.cos(d / 3 + i))})`,
						}}
					/>
				);
			})}
		</AbsoluteFill>
	);
};

const QuoteCard: React.FC<{at: number}> = ({at}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const sp = spring({frame: frame - 2, fps, config: {damping: 13, stiffness: 150}});
	const sp2 = spring({frame: frame - at, fps, config: {damping: 13, stiffness: 150}});
	return (
		<>
			<div style={{position: 'absolute', top: 1060, left: 80, fontFamily: FONT_HEAD, fontSize: 260, color: COLORS.gold, lineHeight: 1, transform: `scale(${sp})`, opacity: sp, textShadow: '0 10px 40px rgba(0,0,0,0.6)'}}>
				“
			</div>
			<div style={{position: 'absolute', top: 1180, left: 90, width: 900, fontFamily: FONT_HEAD, fontSize: 112, color: '#fff', lineHeight: 1.05, transform: `translateY(${(1 - sp) * 60}px)`, opacity: sp, textShadow: '0 8px 30px rgba(0,0,0,0.7)'}}>
				MRBEAST
				<span style={{color: COLORS.gold, opacity: sp2, display: 'inline-block', transform: `translateX(${(1 - sp2) * 40}px)`}}>&nbsp;AYTISHICHA</span>
			</div>
			<div style={{position: 'absolute', top: 1320, left: 90, fontFamily: FONT_BODY, fontWeight: 800, fontSize: 50, color: 'rgba(255,255,255,0.85)', opacity: interpolate(frame, [f(23.04) - f(21.7), f(23.04) - f(21.7) + 6], [0, 1], clamp)}}>
				loyiha uchun…
			</div>
		</>
	);
};

const SplitScene: React.FC<{dur: number; rel: (s: number) => number}> = ({dur, rel}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const open = spring({frame, fps, config: {damping: 16, stiffness: 120}});
	const win = spring({frame: frame - rel(33.7), fps, config: {damping: 12, stiffness: 140}});
	const topH = 960 + 0 * win;
	return (
		<AbsoluteFill style={{backgroundColor: COLORS.ink}}>
			{/* Yuqori: TV studiya */}
			<div style={{position: 'absolute', top: 0, left: 0, width: 1080, height: topH, overflow: 'hidden', transform: `translateX(${(1 - open) * -1080}px)`, filter: `grayscale(${win * 0.8}) brightness(${1 - win * 0.35})`}}>
				<Footage src="video/23104.mp4" trim={3} dur={dur} enter="none" zoom={[1.15, 1.25]} grade="contrast(1.1) saturate(0.9)" />
				<Label text="AYRIM TV LOYIHALAR" top={250} color="#5d6a85" />
			</div>
			{/* Pastki: film ekipaji (MrBeast ko‘lami) */}
			<div style={{position: 'absolute', top: 960, left: 0, width: 1080, height: 960, overflow: 'hidden', transform: `translateX(${(1 - open) * 1080}px)`}}>
				<Footage src="video/23666.mp4" trim={8} dur={dur} enter="none" zoom={[1.15 + win * 0.12, 1.28 + win * 0.12]} grade="contrast(1.15) saturate(1.15)" />
				<Label text="MRBEAST VIDEOSI" top={130} color={COLORS.pink} />
			</div>
			<div style={{position: 'absolute', top: 952, left: 0, width: 1080, height: 16, background: '#fff', boxShadow: '0 0 30px rgba(255,255,255,0.8)', transform: `scaleX(${open})`}} />
			<div style={{position: 'absolute', top: 890, width: 1080, display: 'flex', justifyContent: 'center'}}>
				<div style={{width: 140, height: 140, borderRadius: 70, background: COLORS.ink, border: '6px solid #fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_HEAD, fontSize: 64, color: '#fff', transform: `scale(${open})`}}>VS</div>
			</div>
			<ScaleMeter start={rel(32.4)} overtakeAt={rel(33.7)} tvTop={720} ytTop={1230} />
			<div style={{position: 'absolute', top: 1340, width: 1080, textAlign: 'center', opacity: win}}>
				<span style={{fontFamily: FONT_HEAD, fontSize: 150, color: COLORS.gold, textShadow: '0 0 40px rgba(255,197,61,0.7), 0 10px 30px rgba(0,0,0,0.8)', display: 'inline-block', transform: `scale(${0.6 + 0.4 * win})`}}>
					HAM KATTA!
				</span>
			</div>
			<Flash at={rel(33.7)} len={5} peak={0.6} />
		</AbsoluteFill>
	);
};

const Label: React.FC<{text: string; top: number; color: string}> = ({text, top, color}) => (
	<div style={{position: 'absolute', top, left: 80, background: color, color: '#fff', fontFamily: FONT_BODY, fontWeight: 900, fontSize: 40, letterSpacing: 2, padding: '12px 26px', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.5)'}}>
		{text}
	</div>
);

// ───── Audio: ovoz + musiqa (ducking) + SFX ─────
const musicVolume = (frame: number) => {
	const t = frame / 30;
	let speaking = 0;
	for (const [s, e] of SPEECH) {
		// 0.12 s oldindan pasaytirish, 0.25 s keyin qaytarish
		const v = interpolate(t, [s - 0.12, s, e, e + 0.25], [0, 1, 1, 0], clamp);
		speaking = Math.max(speaking, v);
	}
	const base = interpolate(speaking, [0, 1], [0.32, 0.075]);
	const fadeIn = interpolate(t, [0, 0.3], [0.6, 1], clamp);
	const fadeOut = interpolate(t, [AUDIO_END, DURATION / 30], [1, 0], clamp);
	const outroLift = interpolate(t, [36.8, 37.2], [1, 1.5], clamp);
	return base * fadeIn * fadeOut * outroLift;
};

const AudioMix: React.FC = () => (
	<>
		<Audio src={staticFile('audio/voice_clean.wav')} volume={1} />
		<Audio src={staticFile('audio/music_bed.wav')} volume={musicVolume} />
		{SFX.map(([t, file, vol], i) => (
			<Sequence key={i} from={Math.max(0, f(t))} durationInFrames={f(3)} name={`sfx ${file}`}>
				<Audio src={staticFile(file)} volume={vol * 0.7} />
			</Sequence>
		))}
	</>
);

export const Main: React.FC = () => (
	<AbsoluteFill style={{backgroundColor: COLORS.ink}}>
		<SvgFilters />
		<Scenes />
		<Vignette />
		<Grain />
		<AudioMix />
	</AbsoluteFill>
);
