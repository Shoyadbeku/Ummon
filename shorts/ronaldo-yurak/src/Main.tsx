import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { ALL_BEATS, CALM_BEATS, LATE_BEATS, RECOVERY_BEATS, S, TACHY_BEATS, f } from './timeline';
import { C, BODY, HEAD, SceneStart, useAbsFrame, Flash, Glitch, Grain, LightLeak, Vignette, beatPulse, shake } from './components/fx';
import { Clip, Photo } from './components/media';
import { Stack, Tag, Word } from './components/text';
import { BPMPanel, Counter, ECG, Heart, StatChips, VHS, YearRewind } from './components/graphics';
import { MapJourney } from './components/MapJourney';

/* ------------------------------------------------------------------ helpers */
type Enter = 'punch' | 'whipUp' | 'whipLeft' | 'whipRight' | 'iris' | 'fade' | 'none';

/** Scene = Sequence that starts a few frames early (overlap) with an entrance transition. */
const Scene: React.FC<{ range: readonly [number, number]; enter?: Enter; overlap?: number; children: React.ReactNode; name: string }> = ({
  range,
  enter = 'punch',
  overlap = 4,
  children,
  name,
}) => {
  const from = Math.max(0, f(range[0]) - overlap);
  const dur = f(range[1]) - from + 2;
  return (
    <Sequence from={from} durationInFrames={dur} name={name}>
      <SceneStart.Provider value={from}>
        <Entrance type={enter} len={overlap + 4}>
          {children}
        </Entrance>
      </SceneStart.Provider>
    </Sequence>
  );
};

const Entrance: React.FC<{ type: Enter; len: number; children: React.ReactNode }> = ({ type, len, children }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, len], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  let style: React.CSSProperties = {};
  switch (type) {
    case 'punch':
      style = { transform: `scale(${interpolate(p, [0, 1], [1.35, 1])})`, filter: `blur(${(1 - p) * 16}px)`, opacity: Math.min(1, p * 3) };
      break;
    case 'whipUp':
      style = { transform: `translateY(${(1 - p) * 100}%)`, filter: `blur(${(1 - p) * 22}px)` };
      break;
    case 'whipLeft':
      style = { transform: `translateX(${(1 - p) * 100}%) skewX(${(1 - p) * -8}deg)`, filter: `blur(${(1 - p) * 22}px)` };
      break;
    case 'whipRight':
      style = { transform: `translateX(${-(1 - p) * 100}%) skewX(${(1 - p) * 8}deg)`, filter: `blur(${(1 - p) * 22}px)` };
      break;
    case 'iris':
      style = { clipPath: `circle(${p * 120}% at 50% 45%)` };
      break;
    case 'fade':
      style = { opacity: p };
      break;
  }
  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};

/** Local-frame converter for a scene whose sequence starts `overlap` frames early. */
const at = (sceneStart: number, sec: number, overlap = 4) => f(sec) - (f(sceneStart) - overlap);

const Shake: React.FC<{ amount: number; seed?: string; children: React.ReactNode }> = ({ amount, seed = 's', children }) => {
  const frame = useCurrentFrame();
  const s = shake(frame, amount, seed);
  return <AbsoluteFill style={{ transform: `translate(${s.x}px, ${s.y}px) rotate(${s.r}deg)` }}>{children}</AbsoluteFill>;
};

const Darken: React.FC<{ top?: number; bottom?: number }> = ({ top = 0.55, bottom = 0.75 }) => (
  <AbsoluteFill
    style={{
      background: `linear-gradient(180deg, rgba(0,0,0,${top}) 0%, rgba(0,0,0,0.1) 38%, rgba(0,0,0,0.15) 55%, rgba(0,0,0,${bottom}) 100%)`,
    }}
  />
);

/* ------------------------------------------------------------------ scenes */

// 0.00 – 0.76  "RONALDO"
const HookName: React.FC = () => {
  const s0 = S.hookName[0];
  const frame = useCurrentFrame();
  const pulse = beatPulse(frame, 30, CALM_BEATS, 8);
  return (
    <Glitch at={0} dur={8}>
      <Shake amount={interpolate(frame, [0, 12], [26, 4], { extrapolateRight: 'clamp' })} seed="h1">
        <Photo src="w00.jpg" dur={30} zoom={[1.45, 1.18]} objectPosition="50% 20%" grade="contrast(1.25) saturate(0.85) brightness(0.9)" />
        <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, rgba(255,43,58,${0.15 + pulse * 0.25}) 0%, transparent 60%)`, mixBlendMode: 'screen' }} />
        <Darken top={0.3} bottom={0.85} />
        <Stack top={1180}>
          <Word text="RONALDO" at={at(s0, 0.02, 0)} anim="slam" size={250} letterSpacing={6} />
        </Stack>
      </Shake>
    </Glitch>
  );
};

// 0.76 – 1.70  "15 YOSHIDA"
const HookAge: React.FC = () => {
  const s0 = S.hookAge[0];
  const frame = useCurrentFrame();
  return (
    <Shake amount={interpolate(frame, [4, 14], [30, 3], { extrapolateRight: 'clamp', extrapolateLeft: 'clamp' })} seed="h2">
      <AbsoluteFill style={{ background: C.bg }}>
        <Photo src="w01.jpg" dur={40} zoom={[1.3, 1.45]} pan={[4, -2]} objectPosition="48% 40%" grade="grayscale(1) contrast(1.3) brightness(0.45)" />
        <AbsoluteFill style={{ background: 'radial-gradient(circle at 50% 45%, rgba(255,43,58,0.35), rgba(0,0,0,0.85) 65%)' }} />
        <ECG beats={CALM_BEATS} y={1530} amp={120} opacity={0.75} />
        <Stack top={560} gap={0}>
          <Word text="15" at={at(s0, 0.78)} anim="slam" size={620} color={C.red} glow={C.red} />
          <Word text="YOSHIDA" at={at(s0, 1.12)} anim="letters" size={170} letterSpacing={10} />
        </Stack>
      </AbsoluteFill>
    </Shake>
  );
};

// 1.70 – 4.48  "futbolni butunlay tashlashiga to'g'ri kelishi mumkin edi"
const HookQuit: React.FC = () => {
  const s0 = S.hookQuit[0];
  const frame = useCurrentFrame();
  const desat = interpolate(frame, [at(s0, 2.8), at(s0, 3.6)], [0.6, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <Glitch at={at(s0, 3.94)} dur={6}>
      <Clip id="30601" dur={90} rate={0.7} zoom={[1.2, 1.38]} grade={`grayscale(${desat}) contrast(1.2) brightness(0.7)`} />
      <Darken top={0.5} bottom={0.8} />
      <ECG beats={CALM_BEATS} y={430} amp={110} color={C.red} opacity={0.8} />
      <Stack top={700} gap={6}>
        <Word text="FUTBOLNI" at={at(s0, 1.7)} anim="rise" size={150} />
        <Word text="BUTUNLAY" at={at(s0, 2.2)} anim="mask" size={150} color={C.red} />
        <Word text="TASHLASHI" at={at(s0, 2.8)} anim="rise" size={150} />
        <Word text="MUMKIN EDI" at={at(s0, 3.6)} anim="slam" size={112} bg={C.red} style={{ marginTop: 26 }} />
      </Stack>
    </Glitch>
  );
};

// 4.48 – 5.32  "Bugun"
const Today: React.FC = () => {
  const s0 = S.today[0];
  return (
    <AbsoluteFill>
      <Photo src="w12.jpg" dur={30} zoom={[1.1, 1.22]} panY={[2, -1]} objectPosition="50% 25%" />
      <Darken top={0.6} bottom={0.6} />
      <Tag text="BUGUN" at={at(s0, 4.52)} top={300} />
    </AbsoluteFill>
  );
};

// 5.32 – 6.76  "millionlab muxlislarga ega"
const Fans: React.FC = () => {
  const s0 = S.fans[0];
  const frame = useCurrentFrame();
  const cut = at(s0, 6.0);
  return (
    <AbsoluteFill>
      {frame < cut ? (
        <Clip id="9585" dur={cut} startSec={4} zoom={[1.15, 1.3]} grade="contrast(1.15) saturate(1.1)" />
      ) : (
        <Sequence from={cut}>
          <Photo src="w09.jpg" dur={30} zoom={[1.25, 1.4]} pan={[3, -3]} objectPosition="70% 50%" />
        </Sequence>
      )}
      <Flash at={cut} dur={4} max={0.5} />
      <Darken top={0.55} bottom={0.75} />
      <Stack top={820} gap={4}>
        <Counter to={1000000} at={at(s0, 5.32)} dur={30} size={190} color={C.gold} suffix="+" />
        <Word text="MILLIONLAB" at={at(s0, 5.4)} anim="mask" size={150} />
        <Word text="MUXLIS" at={at(s0, 5.98)} anim="rise" size={150} color={C.gold} />
      </Stack>
    </AbsoluteFill>
  );
};

// 6.76 – 8.26  "futbolchi o'smirligida" (rewind to 2000)
const Teen: React.FC = () => {
  const s0 = S.teen[0];
  const frame = useCurrentFrame();
  const sat = interpolate(frame, [0, 30], [1, 0.25], { extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <Photo
        src="w01.jpg"
        dur={50}
        zoom={[1.15, 1.35]}
        pan={[2, 0]}
        panY={[4, 6]}
        objectPosition="50% 45%"
        grade={`sepia(0.35) saturate(${sat}) contrast(1.15) brightness(0.85)`}
      />
      <VHS opacity={0.45} />
      <Darken top={0.75} bottom={0.75} />
      <YearRewind from={2026} to={2000} at={at(s0, 6.76)} dur={20} top={300} />
      <Stack top={1180} gap={4}>
        <Word text="O‘SMIRLIGIDA" at={at(s0, 7.34)} anim="letters" size={128} />
      </Stack>
    </AbsoluteFill>
  );
};

// 8.26 – 10.68  "yurak bilan bog'liq muammoga duch kelgan"
const HeartScene: React.FC = () => {
  const s0 = S.heart[0];
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: '#0a0002' }}>
      <Clip id="48805" dur={80} startSec={1} rate={0.8} zoom={[1.3, 1.5]} grade="grayscale(1) contrast(1.4) brightness(0.45)" />
      <AbsoluteFill style={{ background: 'rgba(160,0,20,0.45)', mixBlendMode: 'multiply' }} />
      <AbsoluteFill style={{ background: 'radial-gradient(circle at 50% 38%, rgba(255,43,58,0.3), rgba(0,0,0,0.8) 70%)' }} />
      <Heart beats={CALM_BEATS} size={4.2} y={680} at={0} />
      <Stack top={1060} gap={6}>
        <Word text="YURAK" at={at(s0, 8.26)} anim="slam" size={210} color={C.red} glow={C.red} />
        <Word text="BILAN BOG‘LIQ" at={at(s0, 8.64)} anim="rise" size={110} />
      </Stack>
      <Sequence from={at(s0, 9.3)}>
        <AbsoluteFill style={{ border: `${14 + Math.sin(frame / 2) * 4}px solid ${C.red}`, opacity: 0.6, boxShadow: `inset 0 0 120px ${C.red}` }} />
      </Sequence>
      <Stack top={1360}>
        <Word text="⚠ MUAMMO" at={at(s0, 9.3)} anim="slam" size={120} bg={C.red} />
      </Stack>
    </AbsoluteFill>
  );
};

// 10.68 – 11.48  "Shifokorlar"
const Doctors: React.FC = () => {
  const s0 = S.doctors[0];
  return (
    <AbsoluteFill>
      <Clip id="6562" dur={30} startSec={3} zoom={[1.35, 1.5]} pan={[6, 4]} grade="contrast(1.15) saturate(0.7) brightness(0.85) hue-rotate(-8deg)" />
      <Darken top={0.6} bottom={0.7} />
      <Tag text="SHIFOKORLAR" at={at(s0, 10.7)} color="#1d6fff" top={300} />
    </AbsoluteFill>
  );
};

// 11.48 – 14.36  tachycardia read-out
const BPM: React.FC = () => {
  const s0 = S.bpm[0];
  const frame = useCurrentFrame();
  const abs = useAbsFrame();
  const t = abs / 30;
  const panic = interpolate(t, [11.5, 14.1], [2, 22], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const pulse = beatPulse(abs, 30, TACHY_BEATS, 9);
  return (
    <Shake amount={panic} seed="bpm">
      <AbsoluteFill style={{ transform: `scale(${1 + pulse * 0.03})` }}>
        <Clip id="49226" dur={90} zoom={[1.2, 1.5]} grade="contrast(1.25) saturate(1.2) brightness(0.55)" />
        <AbsoluteFill style={{ background: `rgba(255,0,30,${0.1 + pulse * 0.25})`, mixBlendMode: 'screen' }} />
        <Darken top={0.4} bottom={0.8} />
        <BPMPanel beats={TACHY_BEATS} startBpm={90} mode="rising" at={0} top={360} alertAt={at(s0, 12.24)} />
        <ECG beats={TACHY_BEATS} y={1010} amp={150} color={C.red} pxPerSec={620} />
        <Stack top={1180} gap={4}>
          <Word text="HADDAN TASHQARI" at={at(s0, 12.24)} anim="rise" size={118} />
          <Word text="TEZ URISHI" at={at(s0, 13.02)} anim="slam" size={168} color={C.red} glow={C.red} />
        </Stack>
        <Sequence from={at(s0, 13.6)}>
          <div
            style={{
              position: 'absolute',
              top: 230,
              left: 0,
              right: 0,
              textAlign: 'center',
              fontFamily: BODY,
              fontWeight: 800,
              fontSize: 36,
              letterSpacing: 8,
              color: C.red,
            }}
          >
            ● TAXIKARDIYA
          </div>
        </Sequence>
      </AbsoluteFill>
    </Shake>
  );
};

// 14.36 – 16.12  "U muolajadan o'tgan"
const Treatment: React.FC = () => {
  const s0 = S.treatment[0];
  const frame = useCurrentFrame();
  const cut = at(s0, 15.25);
  const ok = at(s0, 15.6);
  const s = spring({ frame: frame - ok, fps: 30, config: { damping: 12, stiffness: 160 } });
  return (
    <AbsoluteFill>
      {frame < cut ? (
        <Clip id="47020" dur={cut} startSec={2} zoom={[1.2, 1.35]} pan={[-3, 2]} grade="contrast(1.1) saturate(0.85)" />
      ) : (
        <Sequence from={cut}>
          <Clip id="46366" dur={30} startSec={6} zoom={[1.3, 1.45]} grade="contrast(1.15) saturate(0.9) brightness(0.8)" />
        </Sequence>
      )}
      <Darken top={0.5} bottom={0.75} />
      <BPMPanel beats={RECOVERY_BEATS} startBpm={187} mode="falling" at={at(s0, 14.6)} top={330} />
      <Stack top={1120} gap={8}>
        <Word text="MUOLAJA" at={at(s0, 14.82)} anim="mask" size={180} />
      </Stack>
      {frame >= ok && (
        <div style={{ position: 'absolute', top: 1330, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
          <div
            style={{
              fontFamily: BODY,
              fontWeight: 800,
              fontSize: 48,
              color: '#04140a',
              background: C.green,
              padding: '14px 34px',
              borderRadius: 60,
              transform: `scale(${s})`,
              boxShadow: `0 0 50px ${C.green}`,
            }}
          >
            ✓ MUOLAJADAN O‘TDI
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// 16.12 – 17.06  "ko'p o'tmay"
const Soon: React.FC = () => {
  const s0 = S.soon[0];
  const frame = useCurrentFrame();
  const ang = interpolate(frame, [0, 28], [0, 720], { easing: Easing.inOut(Easing.cubic), extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <Clip id="43484" dur={30} rate={0.6} zoom={[1.15, 1.3]} grade="contrast(1.1) saturate(1.05) brightness(0.8)" />
      <Darken top={0.6} bottom={0.7} />
      <div style={{ position: 'absolute', top: 470, left: 390, width: 300, height: 300, borderRadius: '50%', border: '8px solid #fff', boxShadow: '0 0 40px rgba(255,255,255,0.5)' }}>
        <div style={{ position: 'absolute', left: 146, top: 40, width: 8, height: 115, background: C.gold, transformOrigin: '50% 100%', transform: `rotate(${ang}deg)`, borderRadius: 4 }} />
        <div style={{ position: 'absolute', left: 146, top: 70, width: 8, height: 85, background: '#fff', transformOrigin: '50% 100%', transform: `rotate(${ang / 12}deg)`, borderRadius: 4 }} />
      </div>
      <Stack top={1100}>
        <Word text="KO‘P O‘TMAY" at={at(s0, 16.12)} anim="letters" size={160} />
      </Stack>
    </AbsoluteFill>
  );
};

// 17.06 – 18.50  "yana mashg'ulotlarga qaytgan"
const Training: React.FC = () => {
  const s0 = S.training[0];
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Clip id="42541r" dur={46} zoom={[1.02, 1.12]} grade="contrast(1.15) saturate(1.1) brightness(0.9)" />
      <Darken top={0.5} bottom={0.7} />
      <ECG beats={RECOVERY_BEATS} y={360} amp={80} color={C.green} opacity={0.85} thickness={5} />
      <Stack top={1060} gap={4}>
        <Word text="YANA" at={at(s0, s0)} anim="rise" size={120} color={C.green} />
        <Word text="MASHG‘ULOTLARGA" at={at(s0, 17.06)} anim="mask" size={118} />
        <Word text="QAYTDI" at={at(s0, 17.74)} anim="slam" size={190} color={C.green} glow={C.green} />
      </Stack>
    </AbsoluteFill>
  );
};

// 18.50 – 19.20  "Keyinchalik"
const Later: React.FC = () => {
  const s0 = S.later[0];
  return (
    <Shake amount={10} seed="later">
      <Clip id="4262" dur={24} startSec={1.5} zoom={[1.6, 1.3]} grade="contrast(1.2) saturate(1.1) brightness(0.8)" />
      <Darken top={0.4} bottom={0.6} />
      <Stack top={820}>
        <Word text="KEYINCHALIK…" at={at(s0, 18.52)} anim="slam" size={150} />
      </Stack>
    </Shake>
  );
};

// 19.20 – 22.80  career map
const Career: React.FC = () => {
  const s0 = S.map[0];
  const o = 4;
  return (
    <MapJourney
      dur={f(S.map[1]) - f(s0) + o}
      stops={[
        { name: 'MANCHESTER UNITED', sub: 'ANGLIYA', lonlat: [-2.24, 53.48], at: at(s0, 19.3), img: 'w02.jpg', country: '826' },
        { name: 'REAL MADRID', sub: 'ISPANIYA', lonlat: [-3.7, 40.42], at: at(s0, 20.44), img: 'w05.jpg', country: '724' },
        { name: 'PORTUGALIYA', sub: 'TERMA JAMOASI', lonlat: [-9.14, 38.72], at: at(s0, 21.42), img: 'w07.jpg', country: '620' },
      ]}
    />
  );
};

// 22.80 – 24.30  "tarixiy yutuqlarga erishgan"
const Trophies: React.FC = () => {
  const s0 = S.trophies[0];
  return (
    <AbsoluteFill>
      <Photo src="w04.jpg" dur={50} zoom={[1.15, 1.35]} panY={[0, 3]} objectPosition="50% 30%" grade="contrast(1.15) saturate(1.1) sepia(0.25) brightness(0.85)" />
      <AbsoluteFill style={{ mixBlendMode: 'screen', opacity: 0.55 }}>
        <Clip id="4064" dur={50} startSec={6} zoom={[1, 1.1]} grade="brightness(0.9)" />
      </AbsoluteFill>
      <Darken top={0.55} bottom={0.85} />
      <Stack top={290} gap={0}>
        <Word text="TARIXIY" at={at(s0, 22.82)} anim="rise" size={150} color={C.gold} glow="rgba(255,201,74,0.6)" />
        <Word text="YUTUQLAR" at={at(s0, 23.4)} anim="slam" size={150} />
      </Stack>
      <StatChips
        at={at(s0, 23.0)}
        top={1010}
        items={[
          { big: '5×', small: 'BALLON D’OR' },
          { big: '5×', small: 'CHEMPIONLAR LIGASI' },
          { big: '2016', small: 'YEVROPA CHEMPIONI' },
        ]}
      />
    </AbsoluteFill>
  );
};

// 24.30 – 25.34  "Eng qizig'i,"  (pattern interrupt)
const Twist: React.FC = () => {
  const s0 = S.twist[0];
  const frame = useCurrentFrame();
  return (
    <Glitch at={0} dur={7}>
      <Shake amount={interpolate(frame, [0, 10], [24, 0], { extrapolateRight: 'clamp' })} seed="tw">
        <AbsoluteFill style={{ background: C.bg }}>
          <AbsoluteFill style={{ background: 'radial-gradient(circle at 50% 50%, rgba(255,201,74,0.18), transparent 60%)' }} />
          <Stack top={700} gap={0}>
            <Word text="ENG" at={at(s0, 24.3, 2)} anim="slam" size={240} />
            <Word text="QIZIG‘I…" at={at(s0, 24.94, 2)} anim="slam" size={240} color={C.gold} glow="rgba(255,201,74,0.5)" />
          </Stack>
        </AbsoluteFill>
      </Shake>
    </Glitch>
  );
};

// 25.34 – 27.84  "bir paytlar sog'lig'i xavotir uyg'otgan bola"
const Boy: React.FC = () => {
  const s0 = S.boy[0];
  return (
    <AbsoluteFill>
      <Photo src="w14.jpg" dur={80} zoom={[1.15, 1.35]} pan={[-6, -8]} objectPosition="30% 25%" grade="grayscale(0.85) contrast(1.25) brightness(0.7) sepia(0.2)" />
      <VHS opacity={0.25} />
      <Darken top={0.6} bottom={0.85} />
      <ECG beats={LATE_BEATS.concat([25.3, 26.1, 26.9])} y={430} amp={110} color={C.red} opacity={0.9} />
      <Stack top={950} gap={4}>
        <Word text="BIR PAYTLAR" at={at(s0, 25.34)} anim="blur" size={130} color="#ffffffcc" />
        <Word text="SOG‘LIG‘I" at={at(s0, 26.18)} anim="rise" size={130} />
        <Word text="XAVOTIR UYG‘OTGAN" at={at(s0, 26.66)} anim="mask" size={100} color={C.red} />
        <Word text="BOLA" at={at(s0, 27.56)} anim="slam" size={220} />
      </Stack>
    </AbsoluteFill>
  );
};

// 27.84 – 29.10  "futbol tarixidagi"
const History: React.FC = () => {
  const s0 = S.history[0];
  const frame = useCurrentFrame();
  const cut = at(s0, 28.6);
  return (
    <AbsoluteFill>
      {frame < cut ? (
        <Clip id="17398" dur={cut} startSec={3} zoom={[1.4, 1.2]} grade="contrast(1.15) saturate(1.05) brightness(0.8)" />
      ) : (
        <Sequence from={cut}>
          <Photo src="w13.jpg" dur={20} zoom={[1.2, 1.32]} objectPosition="45% 40%" />
        </Sequence>
      )}
      <Flash at={cut} dur={4} max={0.6} />
      <Darken top={0.55} bottom={0.75} />
      <Stack top={1040} gap={0}>
        <Word text="FUTBOL" at={at(s0, 27.84)} anim="rise" size={170} />
        <Word text="TARIXIDAGI" at={at(s0, 28.6)} anim="mask" size={170} color={C.gold} />
      </Stack>
    </AbsoluteFill>
  );
};

// 29.10 – 31.46  "eng mashhur sportchilardan biri bo'ldi"
const Famous: React.FC = () => {
  const s0 = S.famous[0];
  const frame = useCurrentFrame();
  const cut = at(s0, 30.66);
  return (
    <AbsoluteFill>
      {frame < cut ? (
        <Photo src="w08.jpg" dur={cut} zoom={[1.2, 1.4]} pan={[2, -1]} objectPosition="62% 50%" grade="contrast(1.2) saturate(1.15) brightness(0.85)" />
      ) : (
        <Sequence from={cut}>
          <Photo src="w06.jpg" dur={30} zoom={[1.15, 1.3]} panY={[-2, 2]} objectPosition="45% 30%" grade="contrast(1.15) saturate(1.1)" />
        </Sequence>
      )}
      <LightLeak at={0} dur={45} hue="gold" />
      <Flash at={cut} dur={4} max={0.5} color={C.gold} />
      <Darken top={0.5} bottom={0.8} />
      <Stack top={300} gap={0}>
        <Word text="ENG" at={at(s0, 29.1)} anim="slam" size={170} />
        <Word text="MASHHUR" at={at(s0, 29.5)} anim="slam" size={210} color={C.gold} glow="rgba(255,201,74,0.6)" />
      </Stack>
      <Stack top={1150} gap={0}>
        <Word text="SPORTCHILARDAN" at={at(s0, 30.0)} anim="mask" size={120} />
        <Word text="BIRI" at={at(s0, 30.66)} anim="slam" size={200} color={C.gold} />
      </Stack>
    </AbsoluteFill>
  );
};

// 31.46 – end  "Sizningcha Ronaldo kuchlimi yoki Messi?"
const Versus: React.FC = () => {
  const s0 = S.versus[0];
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const split = at(s0, 32.1);
  const tR = at(s0, 32.3);
  const tM = at(s0, 34.06);
  const sp = spring({ frame: frame - split, fps, config: { damping: 15, stiffness: 120 } });
  const ronOn = interpolate(frame, [tR, tR + 6, tM - 2, tM + 4], [0.5, 1, 1, 0.45], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const mesOn = interpolate(frame, [tR, tR + 6, tM - 2, tM + 4], [0.5, 0.35, 0.35, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const vs = spring({ frame: frame - split - 6, fps, config: { damping: 9, stiffness: 220 } });
  const pulseQ = 1 + Math.sin(frame / 4) * 0.04;
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      {/* Intro: the two together */}
      {frame < split + 10 && (
        <AbsoluteFill style={{ opacity: interpolate(frame, [split, split + 10], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
          <Photo src="w10.jpg" dur={split + 10} zoom={[1.1, 1.22]} objectPosition="50% 25%" />
          <Darken top={0.5} bottom={0.6} />
        </AbsoluteFill>
      )}
      {frame >= split && (
        <>
          {/* top: Ronaldo */}
          <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 960, overflow: 'hidden', transform: `translateX(${(1 - sp) * -100}%)`, clipPath: 'polygon(0 0, 100% 0, 100% 88%, 0 100%)' }}>
            <Img src={staticFile('img/w07.jpg')} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 18%', filter: `brightness(${ronOn}) contrast(1.15) saturate(${ronOn})`, transform: `scale(${1.08 + (frame - split) * 0.0015})` }} />
            <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(0,0,0,0.5), transparent 30%, transparent 60%, rgba(160,0,20,0.55))' }} />
          </div>
          {/* bottom: Messi */}
          <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 1060, overflow: 'hidden', transform: `translateX(${(1 - sp) * 100}%)`, clipPath: 'polygon(0 10%, 100% 0, 100% 100%, 0 100%)' }}>
            <Img src={staticFile('img/w15.jpg')} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 12%', filter: `brightness(${mesOn}) contrast(1.15) saturate(${mesOn})`, transform: `scale(${1.08 + (frame - split) * 0.0015})` }} />
            <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(0deg, rgba(0,0,0,0.75), transparent 40%, transparent 75%, rgba(40,120,220,0.45))' }} />
          </div>
          {/* labels */}
          <div style={{ position: 'absolute', top: 640, left: 70, opacity: sp }}>
            <Word text="RONALDO" at={tR} anim="slam" size={150} color={frame >= tR && frame < tM ? '#fff' : '#ffffff88'} glow={frame >= tR && frame < tM ? C.red : undefined} />
          </div>
          <div style={{ position: 'absolute', top: 1270, right: 70, opacity: sp }}>
            <Word text="MESSI" at={tM} anim="slam" size={150} color="#fff" glow="#4aa3ff" />
          </div>
          {/* VS badge */}
          <div style={{ position: 'absolute', top: 905, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
            <div
              style={{
                width: 200,
                height: 200,
                borderRadius: '50%',
                background: 'radial-gradient(circle, #ffd76a, #ff8a00)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: HEAD,
                fontSize: 110,
                color: '#000',
                transform: `scale(${vs}) rotate(${(1 - vs) * -90}deg)`,
                boxShadow: '0 0 60px rgba(255,180,40,0.9), 0 0 0 8px #000',
              }}
            >
              VS
            </div>
          </div>
        </>
      )}
      {/* Question header */}
      <div style={{ position: 'absolute', top: 250, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
        <Word text="SIZNINGCHA?" at={at(s0, 31.46)} anim="letters" size={110} bg="rgba(0,0,0,0.75)" />
      </div>
      {frame >= at(s0, 33.02) && frame < tM && (
        <div style={{ position: 'absolute', top: 400, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
          <Word text="KUCHLIMI…" at={at(s0, 33.02)} anim="rise" size={90} color={C.gold} />
        </div>
      )}
      {frame >= tM && (
        <div style={{ position: 'absolute', top: 1530, left: 0, right: 0, display: 'flex', justifyContent: 'center', transform: `scale(${pulseQ})` }}>
          <Word text="YOKI…?" at={tM} anim="slam" size={80} color={C.gold} bg="rgba(0,0,0,0.6)" />
        </div>
      )}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ main */
export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const pulse = frame < f(10.6) ? beatPulse(frame, 30, CALM_BEATS, 9) : 0;
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Audio src={staticFile('mix.wav')} />
      <AbsoluteFill style={{ transform: `scale(${1 + pulse * 0.018})` }}>
        <Scene name="Hook: RONALDO" range={S.hookName} enter="none" overlap={0}>
          <HookName />
        </Scene>
        <Scene name="Hook: 15 yoshida" range={S.hookAge} enter="punch">
          <HookAge />
        </Scene>
        <Scene name="Hook: tashlash" range={S.hookQuit} enter="whipUp">
          <HookQuit />
        </Scene>
        <Scene name="Bugun" range={S.today} enter="whipLeft">
          <Today />
        </Scene>
        <Scene name="Muxlislar" range={S.fans} enter="whipUp">
          <Fans />
        </Scene>
        <Scene name="O'smirlik" range={S.teen} enter="iris">
          <Teen />
        </Scene>
        <Scene name="Yurak" range={S.heart} enter="punch">
          <HeartScene />
        </Scene>
        <Scene name="Shifokorlar" range={S.doctors} enter="whipRight">
          <Doctors />
        </Scene>
        <Scene name="BPM" range={S.bpm} enter="punch">
          <BPM />
        </Scene>
        <Scene name="Muolaja" range={S.treatment} enter="fade" overlap={3}>
          <Treatment />
        </Scene>
        <Scene name="Ko'p o'tmay" range={S.soon} enter="whipLeft">
          <Soon />
        </Scene>
        <Scene name="Mashg'ulot" range={S.training} enter="whipUp">
          <Training />
        </Scene>
        <Scene name="Keyinchalik" range={S.later} enter="punch" overlap={1}>
          <Later />
        </Scene>
        <Scene name="Xarita" range={S.map} enter="iris">
          <Career />
        </Scene>
        <Scene name="Yutuqlar" range={S.trophies} enter="whipUp">
          <Trophies />
        </Scene>
        <Scene name="Eng qizig'i" range={S.twist} enter="none" overlap={0}>
          <Twist />
        </Scene>
        <Scene name="Bola" range={S.boy} enter="fade" overlap={4}>
          <Boy />
        </Scene>
        <Scene name="Tarix" range={S.history} enter="whipLeft">
          <History />
        </Scene>
        <Scene name="Eng mashhur" range={S.famous} enter="punch" overlap={2}>
          <Famous />
        </Scene>
        <Scene name="Versus" range={S.versus} enter="punch">
          <Versus />
        </Scene>
      </AbsoluteFill>

      {/* Global finishing */}
      <Flash at={0} dur={4} max={1} />
      <Flash at={f(0.76)} dur={4} max={0.7} color={C.red} />
      <Flash at={f(10.68)} dur={4} max={0.4} />
      <Flash at={f(18.5)} dur={6} max={0.9} />
      <Flash at={f(29.1)} dur={6} max={0.8} />
      <Flash at={f(31.46)} dur={4} max={0.6} />
      <LightLeak at={f(18.4)} dur={30} hue="warm" />
      <LightLeak at={f(22.7)} dur={40} hue="gold" intensity={0.6} />
      <LightLeak at={f(8.2)} dur={40} hue="red" intensity={0.5} />
      <Vignette strength={0.7} />
      <Grain opacity={0.1} />
    </AbsoluteFill>
  );
};

export const _unused = { ALL_BEATS, Easing };
