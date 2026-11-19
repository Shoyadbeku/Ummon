import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import './fonts';
import {f, FPS, WORDS, DURATION_S} from './data/timing';
import {C, Clip, Darken, Headline, Particles, Photo, Pill, Shake, WhipIn, clamp, ease} from './components/base';
import {Counter, Globe, IdCard, NameVs, RiseGraph, TimelineChip, UzMap, VinylCTA} from './components/Graphics';
import {Flashes, Grain, LightLeaks, SplitTone, Vignette} from './components/Overlays';

/** A scene from a → b seconds. Children get local frames. */
const S: React.FC<{a: number; b: number; whip?: number; children: (dur: number) => React.ReactNode}> = ({a, b, whip = 1, children}) => {
  const dur = f(b) - f(a);
  return (
    <Sequence from={f(a)} durationInFrames={dur} name={`${a.toFixed(2)}–${b.toFixed(2)}`}>
      {whip > 0 ? <WhipIn strength={whip}>{children(dur)}</WhipIn> : children(dur)}
    </Sequence>
  );
};

/** Overlay that lives on its own time range (not affected by scene whips). */
const O: React.FC<{a: number; b: number; children: React.ReactNode}> = ({a, b, children}) => (
  <Sequence from={f(a)} durationInFrames={f(b) - f(a)} layout="absolute-fill">
    {children}
  </Sequence>
);

const L = (abs: number, sceneStart: number) => f(abs) - f(sceneStart); // absolute second → local frame

const Visuals: React.FC = () => (
  <>
    {/* 1 · HOOK — real photo, slam zoom */}
    <S a={0} b={1.56} whip={0}>
      {(d) => (
        <Shake len={9} amp={22}>
          <ZoomSlam>
            <Photo src="shahzoda_2012.jpg" pos="66% 28%" dur={d} move={{from: 1.12, to: 1.22}} />
          </ZoomSlam>
          <Darken top={0.6} mid={0.05} bottom={0.55} />
          <Headline text="SHAHZODA" y={300} size={142} tracking={-4} color={C.gold} glow="rgba(255,200,61,.55)" delay={4} />
        </Shake>
      )}
    </S>

    {/* 2 · MYSTERY — redacted ID card */}
    <S a={1.56} b={4.18}>
      {(d) => (
        <>
          <Clip src="24621" dur={d} startFrom={1} move={{from: 1.15, to: 1.3}} filter="blur(6px) brightness(.55)" />
          <Particles seed="m" n={18} />
          <IdCard mystery y={300} />
          <Pill text="HAQIQIY ISMI?" y={930} delay={L(2.34, 1.56)} bg={C.accent} />
        </>
      )}
    </S>

    {/* 3 · MAP — O‘zbekiston */}
    <S a={4.18} b={5.84}>
      {(d) => (
        <>
          <Clip src="11942" dur={d} startFrom={3} move={{from: 1.1, to: 1.2}} filter="blur(10px) brightness(.4)" />
          <UzMap y={300} />
        </>
      )}
    </S>

    {/* 4 · estrada yulduzlari — stage b-roll */}
    <S a={5.84} b={6.55}>
      {(d) => <Clip src="474" dur={d} startFrom={2} pos="45% 50%" move={{from: 1.05, to: 1.18}} />}
    </S>
    <S a={6.55} b={7.12} whip={0.6}>
      {(d) => <Clip src="4743" dur={d} startFrom={3} pos="40% 50%" move={{from: 1.1, to: 1.25}} />}
    </S>
    <O a={5.84} b={7.12}>
      <Darken top={0.55} mid={0} bottom={0.4} />
      <Particles seed="s" n={30} speed={1.4} />
      <Headline text="★ ESTRADA ★" y={300} size={120} color="#fff" glow="rgba(255,200,61,.6)" delay={2} />
      <Headline text="YULDUZI" y={430} size={150} color={C.gold} glow="rgba(255,200,61,.6)" delay={8} />
    </O>

    {/* 5 · REVEAL — Zilola Musayeva */}
    <S a={7.12} b={9.76}>
      {(d) => (
        <Shake at={L(8.46, 7.12)} len={10} amp={14}>
          <Clip src="2850" dur={d} startFrom={1} move={{from: 1.1, to: 1.25}} filter="blur(4px) brightness(.5)" />
          <Particles seed="r" n={24} color={C.green} />
          <IdCard y={300} revealZilola={L(8.46, 7.12)} revealMusayeva={L(9.04, 7.12)} />
        </Shake>
      )}
    </S>

    {/* 6 · before solo career — band b-roll */}
    <S a={9.76} b={10.8}>
      {(d) => <Clip src="484" dur={d} startFrom={4} move={{from: 1.05, to: 1.15, x: [30, -30]}} />}
    </S>
    <S a={10.8} b={12.04} whip={0.6}>
      {(d) => <Clip src="472" dur={d} startFrom={5} move={{from: 1.15, to: 1.05}} />}
    </S>
    <O a={9.76} b={12.04}>
      <Darken top={0.6} mid={0.1} bottom={0.45} />
      <Pill text="YAKKAXON IJODDAN OLDIN" y={430} delay={8} bg="#fff" size={46} />
    </O>

    {/* 7 · «Jonim» guruhi */}
    <S a={12.04} b={13.76}>
      {(d) => <Clip src="14106" dur={d} startFrom={2} move={{from: 1.08, to: 1.2}} />}
    </S>
    <O a={12.04} b={13.76}>
      <Darken top={0.6} mid={0.1} bottom={0.45} />
      <Headline text="«JONIM»" y={440} size={150} color={C.gold} glow="rgba(255,200,61,.5)" delay={0} />
      <Pill text="GURUHI" y={610} delay={10} />
    </O>

    {/* 8 · stage name — Shahzoda */}
    <S a={13.76} b={15.9}>
      {(d) => (
        <>
          <Clip src="11942" dur={d} startFrom={12} move={{from: 1.0, to: 1.3}} />
          <Darken top={0.55} mid={0.1} bottom={0.45} />
          <Particles seed="t" n={26} />
          <Headline text="SHAHZODA" y={500} size={142} tracking={-4} color={C.gold} glow="rgba(255,200,61,.65)" delay={L(14.5, 13.76)} />
          <Pill text="TAXALLUS" y={700} delay={L(15.18, 13.76)} bg="#fff" />
        </>
      )}
    </S>

    {/* 9 · sahnaga chiqib */}
    <S a={15.9} b={16.56}>
      {(d) => <Clip src="14756" dur={d} startFrom={1.5} pos="62% 50%" move={{from: 1.0, to: 1.15}} />}
    </S>

    {/* 10 · katta mashhurlik — crowd + rising graph */}
    <S a={16.56} b={18.22}>
      {(d) => (
        <>
          <Clip src="14084" dur={d} startFrom={2} move={{from: 1.05, to: 1.15}} />
          <Darken top={0.75} mid={0.25} bottom={0.4} />
          <RiseGraph y={250} />
        </>
      )}
    </S>

    {/* career timeline chip (9.76 → 16.56) */}
    <O a={9.76} b={16.6}>
      <TimelineChip switchAt={L(13.76, 9.76)} outAt={L(16.4, 9.76)} />
    </O>

    {/* 11 · listeners */}
    <S a={18.22} b={19.42}>
      {(d) => (
        <>
          <Clip src="43390" dur={d} startFrom={1} pos="50% 40%" move={{from: 1.0, to: 1.08}} />
          <Darken top={0.5} mid={0} bottom={0.4} />
          <Pill text="♫  QOʻSHIQLARI" y={330} delay={L(18.86, 18.22)} />
        </>
      )}
    </S>

    {/* 12 · globe — beyond Uzbekistan */}
    <S a={19.42} b={21.14}>
      {(d) => (
        <>
          <Clip src="34314" dur={d} startFrom={0} move={{from: 1.3, to: 1.4}} filter="brightness(.35) blur(3px)" />
          <Globe y={760} size={400} arcsAt={L(20.36, 19.42)} />
          <Headline text="CHEGARADAN" y={200} size={96} color="#fff" delay={L(20.36, 19.42) - 6} stagger={1} />
          <Headline text="TASHQARIDA" y={310} size={110} color={C.gold} glow="rgba(255,200,61,.5)" delay={L(20.36, 19.42)} stagger={1} />
        </>
      )}
    </S>

    {/* 13 · tinglovchilar topgan */}
    <S a={21.14} b={22.2}>
      {(d) => (
        <>
          <Clip src="32559" dur={d} startFrom={3} pos="40% 50%" move={{from: 1.05, to: 1.15}} />
          <Darken top={0.55} mid={0.05} bottom={0.4} />
          <Pill text="TINGLOVCHILAR" y={360} delay={2} bg={C.accent} />
        </>
      )}
    </S>

    {/* 14 · ENG QIZIG‘I — pattern interrupt */}
    <S a={22.2} b={23.08} whip={1.4}>
      {(d) => (
        <Shake len={14} amp={26}>
          <Clip src="32591" dur={d} startFrom={4} move={{from: 1.3, to: 1.1}} />
          <Darken top={0.5} mid={0.3} bottom={0.5} />
          <Headline text="ENG" y={480} size={130} color="#fff" delay={0} />
          <Headline text="QIZIGʻI..." y={620} size={150} color={C.accent} glow="rgba(94,231,255,.6)" delay={L(22.64, 22.2)} stagger={1.2} />
        </Shake>
      )}
    </S>

    {/* 15 · millions of people — counter */}
    <S a={23.08} b={24.28}>
      {(d) => (
        <>
          <Clip src="48509" dur={d} startFrom={2} rate={0.8} move={{from: 1.05, to: 1.18}} />
          <Darken top={0.7} mid={0.25} bottom={0.45} />
          <Counter to={1000000} dur={22} y={330} label="MILLIONLAB ODAMLAR" />
        </>
      )}
    </S>

    {/* 16 · split screen: birth name ✗ vs stage name ✓ */}
    <S a={24.28} b={28.23}>
      {(d) => (
        <>
          <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 960, overflow: 'hidden'}}>
            <Clip src="4269" dur={d} startFrom={1} move={{from: 1.05, to: 1.2}} filter="grayscale(1) brightness(.45)" />
          </div>
          <SplitBottom dur={d} openAt={L(26.12, 24.28)} />
          <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: `linear-gradient(90deg, ${C.goldDeep}, ${C.gold}, ${C.goldDeep})`, boxShadow: `0 0 30px ${C.gold}`}} />
          <NameVs strikeAt={L(25.8, 24.28)} stageAt={L(26.12, 24.28)} checkAt={L(26.94, 24.28)} />
        </>
      )}
    </S>

    {/* 17 · needle drop */}
    <S a={28.23} b={29.08}>
      {(d) => <Clip src="46722" dur={d} startFrom={4} move={{from: 1.2, to: 1.05}} />}
    </S>

    {/* 18 · CTA */}
    <S a={29.08} b={DURATION_S}>
      {(d) => (
        <>
          <Clip src="36190" dur={d} startFrom={5} move={{from: 1.1, to: 1.25}} filter="blur(8px) brightness(.35)" />
          <Particles seed="c" n={22} />
          <Headline text="ENG ZOʻR" y={130} size={96} color="#fff" delay={L(29.96, 29.08)} stagger={1} />
          <VinylCTA />
        </>
      )}
    </S>
  </>
);

const ZoomSlam: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  const s = interpolate(frame, [0, 12], [1.45, 1], {...clamp, easing: ease});
  const blur = interpolate(frame, [0, 8], [16, 0], clamp);
  return <AbsoluteFill style={{transform: `scale(${s})`, filter: blur > 0.2 ? `blur(${blur}px)` : undefined}}>{children}</AbsoluteFill>;
};

/** Bottom half of the split: the real photo, wiping open from the seam when the stage name is said. */
const SplitBottom: React.FC<{dur: number; openAt: number}> = ({dur, openAt}) => {
  const frame = useCurrentFrame();
  const open = interpolate(frame, [openAt - 4, openAt + 8], [0, 1], {...clamp, easing: ease});
  return (
    <div style={{position: 'absolute', left: 0, top: 960, width: 1080, height: 960, overflow: 'hidden', background: '#07070c'}}>
      <div style={{position: 'absolute', inset: 0, clipPath: `inset(0 0 ${(1 - open) * 100}% 0)`}}>
        <Photo src="shahzoda_2012.jpg" pos="100% 22%" dur={dur} move={{from: 1.0, to: 1.08}} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0) 55%, rgba(0,0,0,.7) 100%)'}} />
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Sound design                                                        */
/* ------------------------------------------------------------------ */
type Sfx = {id: string; at: number; vol: number; from?: number; len?: number};
const SFX: Sfx[] = [
  {id: '2908', at: 0.0, vol: 0.75, from: 0.95}, // hook impact (peak at 1.0 s in file)
  {id: '1492', at: 1.45, vol: 0.45},
  {id: '166', at: 3.95, vol: 0.5},
  {id: '3005', at: 4.9, vol: 0.55}, // map pin
  {id: '1490', at: 5.7, vol: 0.4},
  {id: '788', at: 6.26, vol: 0.85}, // riser → hit exactly on "Zilola" (8.46)
  {id: '2350', at: 8.16, vol: 0.55},
  {id: '1492', at: 9.62, vol: 0.4},
  {id: '3005', at: 12.36, vol: 0.55},
  {id: '3115', at: 13.62, vol: 0.5},
  {id: '772', at: 14.1, vol: 0.6}, // peak lands on "Shahzoda" 14.5
  {id: '166', at: 15.82, vol: 0.4},
  {id: '3115', at: 16.45, vol: 0.45},
  {id: '478', at: 16.56, vol: 0.16, from: 2, len: 1.8}, // crowd
  {id: '1490', at: 18.05, vol: 0.35},
  {id: '1492', at: 19.3, vol: 0.4},
  {id: '2350', at: 20.1, vol: 0.45}, // arcs
  {id: '166', at: 21.05, vol: 0.4},
  {id: '784', at: 22.0, vol: 0.6}, // pattern interrupt
  {id: '1490', at: 22.95, vol: 0.35},
  {id: '478', at: 23.08, vol: 0.14, from: 6, len: 1.3},
  {id: '3115', at: 24.15, vol: 0.45},
  {id: '772', at: 25.4, vol: 0.6}, // strike on "emas"
  {id: '2350', at: 25.85, vol: 0.45},
  {id: '1492', at: 28.1, vol: 0.4},
  {id: '3005', at: 29.05, vol: 0.5},
  {id: '3005', at: 29.62, vol: 0.5},
];

const speakingAt = (t: number) => WORDS.some((w) => t >= w.s - 0.12 && t <= w.e + 0.3);

const MUSIC_VOL = (frame: number) => {
  // Smooth ducking: average the speaking state over ±5 frames.
  let acc = 0;
  for (let k = -5; k <= 5; k++) acc += speakingAt((frame + k) / FPS) ? 1 : 0;
  const duck = acc / 11;
  const base = 0.21 - 0.11 * duck;
  const fadeIn = interpolate(frame, [0, 8], [0.4, 1], clamp);
  const fadeOut = interpolate(frame, [f(31.3), f(DURATION_S)], [1, 0], clamp);
  return base * fadeIn * fadeOut;
};

const SoundDesign: React.FC = () => (
  <>
    <Audio src={staticFile('media/voice_clean.wav')} volume={1} />
    <Audio src={staticFile('media/music/168.mp3')} startFrom={f(8.0)} volume={MUSIC_VOL} />
    {SFX.map((s, i) => (
      <Sequence key={i} from={f(s.at)} durationInFrames={s.len ? f(s.len) : undefined}>
        <Audio
          src={staticFile(`media/sfx/${s.id}.mp3`)}
          startFrom={s.from ? f(s.from) : 0}
          volume={(fr) => (s.len ? s.vol * interpolate(fr, [0, 6, f(s.len) - 10, f(s.len)], [0, 1, 1, 0], clamp) : s.vol)}
        />
      </Sequence>
    ))}
  </>
);

export const Main: React.FC = () => {
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Visuals />
      <SplitTone />
      <LightLeaks at={[0.05, 4.18, 7.12, 13.76, 19.42, 22.2, 26.12, 29.08]} />
      <Vignette />
      <Grain />
      <Flashes at={[8.46, 14.5, 22.2, 26.12]} />
      <SoundDesign />
    </AbsoluteFill>
  );
};
