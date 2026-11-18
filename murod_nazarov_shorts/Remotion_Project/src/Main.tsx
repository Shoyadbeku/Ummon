import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, Clip, Enter, Flash, Fonts, Grain, LightLeak, Still, FONT_SERIF, FONT_DISPLAY, FONT_UI, useSec, useShake, ease} from './components/core';
import {Bar, Chip, Counter, KineticLine, Safe, Scrim, Serif, Slam, WipeText} from './components/type';
import {Globe, TASHKENT, TSUKUBA, DIST_KM} from './components/Globe';
import {SCENES, SFX, WORDS as W, f, DURATION_S, type SceneId} from './timeline';

const sceneById = (id: SceneId) => SCENES.find((s) => s.id === id)!;
/** Word time relative to the start of a scene. */
const r = (id: SceneId, word: number) => +(word - sceneById(id).from).toFixed(3);
const dur = (id: SceneId) => sceneById(id).to - sceneById(id).from;

// ---------------------------------------------------------------- scenes

const Hook: React.FC = () => {
  const shake = useShake(0.12, 22, 0.4);
  return (
    <AbsoluteFill style={{transform: shake}}>
      <Enter type="none">
        <Still src="cm_tashkent_city_night.jpg" focusX={62} grade="night" zoom={[1.45, 1.12]} duration={dur('hook')} />
      </Enter>
      <Scrim strength={0.45} />
      <Safe>
        <Chip text="Bugun" at={0.0} />
        <Slam text="TOSHKENT" at={0.12} size={150} />
        <Bar at={0.4} width={360} />
      </Safe>
    </AbsoluteFill>
  );
};

const Cranes: React.FC = () => (
  <Enter type="whip">
    <Clip src="cranes" zoom={[1.0, 1.14]} duration={dur('cranes')} />
    <Scrim from="bottom" strength={0.35} />
    <Safe justify="flex-end" bottom={560}>
      <KineticLine
        size={150}
        words={[
          {t: 'KATTA', at: 0.0},
          {t: 'BINOLAR', at: r('cranes', W.binolar), color: C.accent},
        ]}
      />
      <div style={{marginTop: 10}}>
        <KineticLine size={80} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'qurayotgan…', at: r('cranes', W.qurayotgan)}]} />
      </div>
    </Safe>
  </Enter>
);

const NameCard: React.FC = () => {
  const shake = useShake(0.0, 14, 0.25);
  return (
    <AbsoluteFill style={{transform: shake}}>
      <Enter type="punch">
        <Clip src="cranesun" grade="warm" zoom={[1.18, 1.02]} duration={dur('name')} />
      </Enter>
      <Scrim strength={0.5} />
      <Safe align="flex-start">
        <Bar at={0.0} width={180} />
        <WipeText text="MUROD" at={0.0} size={150} />
        <WipeText text="NAZAROV" at={r('name', W.nazarov)} size={150} color={C.accent} />
      </Safe>
    </AbsoluteFill>
  );
};

const Flag: React.FC = () => (
  <Enter type="whip">
    <Clip src="flag" grade="cine" zoom={[1.0, 1.12]} duration={dur('flag')} />
    <Scrim from="bottom" strength={0.35} />
    <Safe justify="flex-end" bottom={560}>
      <KineticLine size={78} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'bir', at: 0.0}, {t: 'paytlar', at: 0.1}]} />
      <Slam text="YAPONIYADA" at={r('flag', W.yaponiyada)} size={118} color={C.white} />
    </Safe>
  </Enter>
);

const Shibuya: React.FC = () => {
  const t = useSec();
  const qAt = r('shibuya', W.bilarmidingiz);
  const breathe = 1 + Math.max(0, t - qAt - 0.4) * 0.05;
  return (
    <Enter type="punch">
      <Clip src="shibuya" grade="night" zoom={[1.05, 1.22]} duration={dur('shibuya')} />
      <Scrim strength={0.55} />
      <Safe>
        <KineticLine
          size={110}
          words={[
            {t: 'TAHSIL', at: r('shibuya', W.tahsil)},
            {t: 'OLGAN', at: r('shibuya', W.tahsil) + 0.3},
          ]}
        />
        <div style={{transform: `scale(${breathe})`, height: 520, display: 'flex', alignItems: 'center'}}>
          <Slam text="?" at={qAt} size={560} color={C.accent} font={FONT_SERIF} />
        </div>
        <KineticLine size={72} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'bilarmidingiz', at: qAt + 0.1}]} />
      </Safe>
    </Enter>
  );
};

const Year: React.FC = () => (
  <AbsoluteFill>
    <Enter type="fade" frames={5}>
      <Still src="cm_tashkent_skyline_2019.jpg" grade="vintage" focusX={42} zoom={[1.3, 1.08]} duration={dur('year')} />
    </Enter>
    <AbsoluteFill style={{background: 'rgba(20,12,4,0.35)'}} />
    <Grain opacity={0.22} />
    <Safe>
      <Chip text="Tugʻilgan yili" at={0.05} />
      <Counter from={1950} to={1982} at={r('year', W.y1982) - 0.15} dur={0.75} size={300} color={C.accent} />
      <WipeText text="TOSHKENT" at={r('year', W.toshkentda2) - 0.35} size={96} tracking={10} />
    </Safe>
  </AbsoluteFill>
);

const GlobeTashkent: React.FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, #0d1a2b 0%, #04070c 70%)'}}>
    <Globe
      rotFrom={[30, 15]}
      rotTo={TASHKENT}
      scaleFrom={420}
      scaleTo={1200}
      moveDur={0.85}
      highlight={['Uzbekistan']}
      pins={[{at: 0.45, coord: TASHKENT, label: 'TOSHKENT'}]}
      cy={980}
    />
    <AbsoluteFill style={{top: 1340}}>
      <div style={{textAlign: 'center'}}>
        <KineticLine size={84} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'tugʻilgan', at: r('globeTashkent', W.tugilgan)}]} />
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);

const Father: React.FC = () => (
  <Enter type="fade" frames={6}>
    <Clip src="father" grade="warm" zoom={[1.0, 1.08]} duration={dur('father')} />
    <Scrim strength={0.4} />
    <Safe>
      <Counter from={0} to={14} at={0.02} dur={0.45} size={420} font={FONT_SERIF} color={C.white} />
      <WipeText text="YOSHIDA" at={r('father', W.yoshida)} size={90} tracking={14} color={C.accent} />
    </Safe>
  </Enter>
);

const Boy: React.FC = () => {
  const t = useSec();
  const desat = interpolate(t, [0, 0.6], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill>
      <Clip src="boy" grade="mono" zoom={[1.12, 1.0]} duration={dur('boy')} />
      <AbsoluteFill style={{background: `rgba(10,15,25,${0.25 * desat})`}} />
      <Scrim from="bottom" strength={0.45} />
      <Safe justify="flex-end" bottom={560}>
        <KineticLine
          size={96}
          font={FONT_SERIF}
          weight={900}
          italic
          tracking={0}
          words={[
            {t: 'otasidan', at: r('boy', W.otasidan)},
            {t: 'ayrilgan', at: r('boy', W.ayrilgan)},
          ]}
        />
      </Safe>
    </AbsoluteFill>
  );
};

const Institute: React.FC = () => (
  <Enter type="whip">
    <Still src="cm_tsios_main.jpg" focusX={14} zoom={[1.02, 1.16]} panX={[2, -2]} duration={dur('institute')} />
    <Scrim from="bottom" strength={0.6} />
    <Safe justify="flex-end" bottom={520} align="flex-start">
      <Chip text="Taʼlim · 01" at={0.05} />
      <KineticLine size={64} weight={800} align="left" tracking={0} words={[{t: 'Toshkent', at: r('institute', W.tdshi)}, {t: 'Davlat', at: r('institute', W.tdshi) + 0.25}]} />
      <WipeText text="SHARQSHUNOSLIK" at={r('institute', W.sharqshunoslik)} size={84} color={C.accent} />
      <KineticLine size={64} weight={800} align="left" tracking={0} words={[{t: 'Instituti', at: r('institute', W.institutida)}]} />
    </Safe>
  </Enter>
);

const Books: React.FC = () => (
  <Enter type="punch">
    <Clip src="books" grade="warm" zoom={[1.1, 1.0]} duration={dur('books')} />
    <Scrim strength={0.35} />
    <Safe>
      <KineticLine size={92} font={FONT_SERIF} weight={900} italic tracking={0} words={[{t: 'tahsil', at: 0.2}, {t: 'olgan', at: 0.45}]} />
    </Safe>
  </Enter>
);

const Flight: React.FC = () => {
  const t = useSec();
  const o = interpolate(t, [0.5, 0.8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, #0d1a2b 0%, #04070c 70%)'}}>
      <Globe
        rotFrom={TASHKENT}
        rotTo={[106, 38]}
        scaleFrom={1000}
        scaleTo={620}
        moveDur={0.9}
        highlight={['Uzbekistan', 'Japan']}
        pins={[
          {at: 0.0, coord: TASHKENT, label: 'TOSHKENT'},
          {at: r('flight', W.tsukuba), coord: TSUKUBA, label: 'TSUKUBA', color: C.accent2},
        ]}
        arc={{from: TASHKENT, to: TSUKUBA, at: 0.15, dur: 0.95}}
        cy={1000}
      />
      <div style={{position: 'absolute', top: 330, width: '100%', textAlign: 'center', opacity: o}}>
        <div style={{fontFamily: FONT_UI, fontWeight: 700, fontSize: 34, letterSpacing: 6, color: C.cool}}>OʻZBEKISTON → YAPONIYA</div>
        <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: 96, color: '#fff', marginTop: 8}}>
          ≈ {DIST_KM.toLocaleString('en-US').replace(',', ' ')} km
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Tsukuba: React.FC = () => (
  <Enter type="punch">
    <Still src="cm_tsukuba1.jpg" focusX={78} zoom={[1.16, 1.0]} duration={dur('tsukuba')} />
    <Scrim from="top" strength={0.35} />
    <Scrim from="bottom" strength={0.6} />
    <Safe justify="flex-end" bottom={520} align="flex-start">
      <Chip text="Taʼlim · 02" at={0.0} color={C.accent2} />
      <WipeText text="TSUKUBA" at={0.0} size={150} />
      <WipeText text="UNIVERSITETI" at={0.15} size={84} color={C.accent2} />
      <KineticLine size={64} font={FONT_SERIF} weight={700} italic align="left" tracking={0} words={[{t: 'ham', at: r('tsukuba', 18.2)}, {t: 'oʻqigan', at: r('tsukuba', 18.42)}]} />
    </Safe>
  </Enter>
);

const Today: React.FC = () => (
  <Enter type="whipUp">
    <Clip src="construct" zoom={[1.0, 1.16]} duration={dur('today')} />
    <Scrim strength={0.45} />
    <Safe>
      <Slam text="BUGUN" at={0.02} size={230} />
      <KineticLine size={80} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'esa', at: r('today', 19.42)}, {t: 'u…', at: r('today', 19.64)}]} />
    </Safe>
  </Enter>
);

const Brand: React.FC = () => {
  const shake = useShake(0.0, 20, 0.35);
  return (
    <AbsoluteFill style={{transform: shake}}>
      <Enter type="punch">
        <Clip src="aerial" zoom={[1.25, 1.02]} rotate={[2, 0]} duration={dur('brand')} />
      </Enter>
      <Scrim strength={0.55} />
      <Safe>
        <Slam text="MURAD" at={0.02} size={200} />
        <Slam text="BUILDINGS" at={r('brand', W.buildings)} size={128} color={C.accent} />
      </Safe>
    </AbsoluteFill>
  );
};

const Founder: React.FC = () => (
  <Enter type="whip">
    <Still src="cm_tashkentcity.jpg" focusX={60} zoom={[1.05, 1.22]} panY={[2, -2]} duration={dur('founder')} />
    <Scrim strength={0.5} />
    <Safe>
      <Chip text="Kompaniya" at={0.0} />
      <Slam text="ASOSCHISI" at={r('founder', W.asoschisi)} size={130} />
      <Bar at={0.35} width={300} />
      <KineticLine size={68} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'sifatida', at: r('founder', W.sifatida)}, {t: 'tanilgan', at: r('founder', 22.44)}]} />
    </Safe>
  </Enter>
);

const Question: React.FC = () => (
  <Enter type="fade" frames={6}>
    <Clip src="chess" zoom={[1.0, 1.14]} duration={dur('question')} />
    <Scrim strength={0.5} />
    <Safe>
      <KineticLine size={70} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'Uning', at: r('question', W.uning)}, {t: 'faoliyati', at: r('question', 23.78)}]} />
      <KineticLine
        size={128}
        words={[
          {t: 'ODDIY', at: r('question', W.oddiy)},
          {t: 'BIR', at: r('question', 24.78)},
          {t: 'SAVOL', at: r('question', W.savolni), color: C.accent},
        ]}
      />
      <KineticLine size={70} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: 'tugʻdiradi', at: r('question', W.tugdiradi)}]} />
    </Safe>
  </Enter>
);

const Business: React.FC = () => {
  const shake = useShake(0.05, 24, 0.45);
  return (
    <AbsoluteFill style={{transform: shake}}>
      <Enter type="punch" frames={5}>
        <Clip src="up" zoom={[1.02, 1.28]} rotate={[0, -5]} duration={dur('business')} />
      </Enter>
      <Scrim strength={0.6} />
      <Safe>
        <KineticLine size={140} words={[{t: 'KATTA', at: r('business', W.katta2)}, {t: 'BIZNES', at: r('business', W.biznes), color: C.accent}]} />
        <KineticLine size={84} weight={800} words={[{t: 'qurish', at: r('business', W.qurishUchun)}, {t: 'uchun', at: r('business', 27.55)}]} />
        <KineticLine size={110} words={[{t: 'ENG', at: r('business', W.eng)}, {t: 'MUHIMI', at: r('business', W.muhimi)}]} />
        <Slam text="NIMA?" at={r('business', W.nima) - 0.05} size={210} color={C.accent} />
      </Safe>
    </AbsoluteFill>
  );
};

const Option: React.FC<{id: SceneId; clip: string; num: string; word: string; at: number; size: number; color?: string; startFrom?: number; sub?: string}> = ({
  id,
  clip,
  num,
  word,
  at,
  size,
  color = C.accent,
  startFrom = 0,
  sub,
}) => {
  const shake = useShake(at, 16, 0.3);
  return (
    <AbsoluteFill style={{transform: shake}}>
      <Enter type="punch" frames={5}>
        <Clip src={clip} startFrom={startFrom} zoom={[1.15, 1.0]} duration={dur(id)} />
      </Enter>
      <Scrim strength={0.5} />
      <Safe>
        <Slam text={num} at={at - 0.1} size={150} color={color} stroke />
        <Slam text={word} at={at} size={size} />
        {sub ? <KineticLine size={72} font={FONT_SERIF} weight={700} italic tracking={0} words={[{t: sub, at: at + 0.35}]} /> : null}
      </Safe>
    </AbsoluteFill>
  );
};

const Band: React.FC<{clip: string; startFrom: number; idx: number; label: string; num: string}> = ({clip, startFrom, idx, label, num}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const d = idx * 3;
  const p = interpolate(frame - d, [0, 9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const dir = idx % 2 === 0 ? -1 : 1;
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: idx * 640,
        width: 1080,
        height: 636,
        overflow: 'hidden',
        transform: `translateX(${(1 - p) * dir * 100}%)`,
      }}
    >
      <Clip src={clip} startFrom={startFrom} zoom={[1.0, 1.08]} duration={DURATION_S - 32.25} />
      <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.1) 70%)'}} />
      <div style={{position: 'absolute', left: 80, top: [300, 70, 150][idx], display: 'flex', alignItems: 'baseline', gap: 26, opacity: p}}>
        <span style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: 110, color: 'transparent', WebkitTextStroke: `3px ${C.accent}`}}>{num}</span>
        <span style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: label.length > 8 ? 70 : 92, color: '#fff', textShadow: '0 4px 20px rgba(0,0,0,0.7)'}}>{label}</span>
      </div>
      <span style={{display: 'none'}}>{fps}</span>
    </div>
  );
};

const Choice: React.FC = () => {
  const t = useSec();
  const cardP = interpolate(t, [0.05, 0.4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const ctaP = interpolate(t, [1.45, 1.75], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const pulse = 1 + Math.sin(t * 9) * 0.025 * ctaP;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <Band clip="cash" startFrom={0.3} idx={0} num="1" label="PUL" />
      <Band clip="library" startFrom={1.0} idx={1} num="2" label="BILIM" />
      <Band clip="climb" startFrom={1.8} idx={2} num="3" label="TAVAKKALCHILIK" />
      <AbsoluteFill style={{alignItems: 'center'}}>
        <div
          style={{
            position: 'absolute',
            top: 975,
            padding: '30px 44px',
            width: 880,
            borderRadius: 36,
            background: 'rgba(8,10,16,0.78)',
            border: `3px solid ${C.accent}`,
            boxShadow: `0 30px 80px rgba(0,0,0,0.6), 0 0 60px ${C.accent}33`,
            backdropFilter: 'blur(14px)',
            opacity: cardP,
            transform: `scale(${0.85 + 0.15 * cardP}) translateY(${(1 - cardP) * 40}px)`,
            textAlign: 'center',
          }}
        >
          <KineticLine
            size={74}
            words={[
              {t: 'SIZ', at: r('choice', W.siz)},
              {t: 'QAYSI', at: r('choice', W.qaysiBirini)},
              {t: 'BIRINI', at: r('choice', W.qaysiBirini) + 0.3},
              {t: 'TANLAYSIZ?', at: r('choice', W.tanlaysiz), color: C.accent},
            ]}
          />
          <div
            style={{
              display: 'inline-block',
              marginTop: 18,
              padding: '12px 30px',
              borderRadius: 999,
              background: C.accent,
              color: '#111',
              fontFamily: FONT_UI,
              fontWeight: 700,
              fontSize: 34,
              opacity: ctaP,
              transform: `scale(${pulse}) translateY(${(1 - ctaP) * 20}px)`,
            }}
          >
            Izohda yozing: 1, 2 yoki 3 ↓
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const SCENE_COMPONENTS: Record<SceneId, React.FC> = {
  hook: Hook,
  cranes: Cranes,
  name: NameCard,
  flag: Flag,
  shibuya: Shibuya,
  year: Year,
  globeTashkent: GlobeTashkent,
  father: Father,
  boy: Boy,
  institute: Institute,
  books: Books,
  flight: Flight,
  tsukuba: Tsukuba,
  today: Today,
  brand: Brand,
  founder: Founder,
  question: Question,
  business: Business,
  money: () => <Option id="money" clip="money" num="01" word="PUL" at={r('money', W.pul)} size={300} sub="mi?" />,
  knowledge: () => <Option id="knowledge" clip="library" num="02" word="BILIM" at={r('knowledge', W.bilim)} size={240} />,
  risk: () => <Option id="risk" clip="climb" num="03" word="TAVAKKALCHILIK" at={r('risk', W.tavakkalchilik)} size={88} sub="yoki…" />,
  choice: Choice,
};

// ---------------------------------------------------------------- audio

const Music: React.FC = () => {
  const {fps} = useVideoConfig();
  return (
    <Audio
      src={staticFile('audio/music.wav')}
      volume={(fr) => {
        const s = fr / fps;
        const fadeIn = interpolate(s, [0, 2.0], [0.35, 1], {extrapolateRight: 'clamp'});
        const fadeOut = interpolate(s, [DURATION_S - 0.9, DURATION_S], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        // before the drop the track is quieter -> more gain; after the drop pull back under the voice
        const base = s < 25.95 ? 0.27 : s < 28.95 ? 0.085 : 0.11;
        return base * fadeIn * fadeOut;
      }}
    />
  );
};

// ---------------------------------------------------------------- main

export const Main: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <Fonts />
      {SCENES.map((s) => {
        const Comp = SCENE_COMPONENTS[s.id];
        return (
          <Sequence key={s.id} from={f(s.from)} durationInFrames={f(s.to) - f(s.from)} name={s.id}>
            <Comp />
          </Sequence>
        );
      })}

      {/* global finishing layers */}
      <Grain opacity={0.08} />
      <LightLeak at={2.52} />
      <LightLeak at={12.45} />
      <LightLeak at={17.46} color="255,120,90" />
      <LightLeak at={21.4} />
      <LightLeak at={32.25} />
      <Flash at={9.15} color="#5fd0ff" max={0.5} />
      <Flash at={19.8} max={0.85} />
      <Flash at={25.97} max={0.95} dur={0.32} />
      <Flash at={28.95} max={0.5} dur={0.18} />
      <Flash at={29.9} max={0.5} dur={0.18} />
      <Flash at={30.7} max={0.5} dur={0.18} />

      {/* audio */}
      <Audio src={staticFile('audio/voice.wav')} volume={1} />
      <Music />
      {SFX.map(([file, at, vol], i) => (
        <Sequence key={`sfx${i}`} from={f(at)} name={`sfx ${file}`}>
          <Audio src={staticFile(`audio/${file}`)} volume={vol} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
