import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import storyboard from './data/storyboard.json';
import subtitles from './data/subtitles.json';
import {BODY, C, FPS} from './theme';
import {ClipLayer, fadeIn, GraphicBg, HookTitle, OverlayWord, sec, SourceLabel, sourceLabel} from './Layers';
import {
  Bars, Calendar, Chapter, Compare, Credits, Cta, Flow, Rank, Recap, Reciprocity, Risk,
  SplitClips, Split57, Steps, Timeline, Typo, VisaMap,
} from './Graphics';

type Ref = [string, number];
type Scene = {t: number; end: number; clip?: Ref; bg?: Ref; g?: string; [k: string]: any};
const SCENES = storyboard as Scene[];
const SUBS = subtitles as {s: number; e: number; x: string}[];
const XFADE = 8;
export const TOTAL_FRAMES = sec(SCENES[SCENES.length - 1].end);
const CREDITS_START = SCENES[SCENES.length - 1].t;

const GraphicBody: React.FC<{s: Scene; dur: number}> = ({s, dur}) => {
  switch (s.g) {
    case 'chapter': return <Chapter num={s.num} title={s.title} sub={s.sub} />;
    case 'typo': return <Typo text={s.text} sub={s.sub} />;
    case 'steps': return <Steps title={s.title} items={s.items} dur={dur} />;
    case 'checklist': return <Steps title={s.title} items={s.items} numbered={false} dur={dur} />;
    case 'visaMap': return <VisaMap items={s.items} />;
    case 'rank': return <Rank rank={s.rank} dest={s.dest} />;
    case 'bars': return <Bars title={s.title} bars={s.bars} note={s.note} />;
    case 'split57': return <Split57 title={s.title} left={s.left} right={s.right} />;
    case 'risk': return <Risk title={s.title} />;
    case 'reciprocity': return <Reciprocity a={s.a} b={s.b} ab={s.ab} ba={s.ba} />;
    case 'timeline': return <Timeline points={s.points} />;
    case 'flow': return <Flow steps={s.steps} />;
    case 'calendar': return <Calendar />;
    case 'compare': return <Compare rows={s.rows} cols={s.cols} />;
    case 'recap': return <Recap items={s.items} />;
    case 'cta': return <Cta text={s.text} />;
    default: return null;
  }
};

const SceneView: React.FC<{s: Scene; i: number; dur: number}> = ({s, i, dur}) => {
  const f = useCurrentFrame();
  const op = i === 0 ? 1 : fadeIn(f, XFADE);
  let body: React.ReactNode;
  let label = '';
  if (s.g === 'credits') {
    body = <Credits dur={dur} />;
  } else if (s.g === 'split' || s.g === 'vs') {
    body = <SplitClips left={s.left} right={s.right} leftLabel={s.leftLabel} rightLabel={s.rightLabel} dur={dur} seed={i} />;
  } else if (s.g) {
    body = (
      <>
        <GraphicBg bg={s.bg} dur={dur} seed={i} />
        <GraphicBody s={s} dur={dur} />
      </>
    );
    label = s.bg ? sourceLabel(s.bg[0]) : '';
  } else if (s.clip) {
    body = (
      <>
        <ClipLayer src={s.clip} dur={dur} seed={i} />
        {s.title ? <HookTitle text={s.title} dur={dur} /> : null}
        {s.overlay ? <OverlayWord text={s.overlay} /> : null}
      </>
    );
    label = sourceLabel(s.clip[0]);
  }
  return (
    <AbsoluteFill style={{opacity: op}}>
      {body}
      {label ? <SourceLabel text={label} /> : null}
    </AbsoluteFill>
  );
};

const Subtitles: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  if (t >= CREDITS_START || t < SCENES[1].t) return null;
  const cue = SUBS.find((c) => t >= c.s && t < c.e);
  if (!cue) return null;
  const local = (t - cue.s) * FPS;
  const out = (cue.e - t) * FPS;
  const op = Math.min(interpolate(local, [0, 4], [0, 1], {extrapolateRight: 'clamp'}), interpolate(out, [0, 4], [0, 1], {extrapolateRight: 'clamp'}));
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 92, pointerEvents: 'none'}}>
      <div
        style={{
          maxWidth: 1400,
          textAlign: 'center',
          fontFamily: BODY,
          fontWeight: 600,
          fontSize: 40,
          lineHeight: 1.3,
          color: C.ink,
          padding: '8px 22px',
          background: 'rgba(7,16,31,0.62)',
          borderRadius: 6,
          opacity: op,
          textShadow: '0 2px 6px rgba(0,0,0,0.6)',
        }}
      >
        {cue.x}
      </div>
    </AbsoluteFill>
  );
};

const Sfx: React.FC = () => (
  <>
    {SCENES.map((s, i) => {
      if (!s.g || s.g === 'credits' || i === 0) return null;
      const hit = s.g === 'chapter' || s.sfx === 'impact';
      return (
        <Sequence key={`sfx${i}`} from={Math.max(0, sec(s.t) - (hit ? 0 : 6))} durationInFrames={sec(1.6)}>
          <Audio src={staticFile(hit ? 'audio/impact.wav' : 'audio/whoosh.wav')} volume={hit ? 0.55 : 0.35} />
        </Sequence>
      );
    })}
    <Sequence from={sec(62.0)} durationInFrames={sec(3)}>
      <Audio src={staticFile('audio/riser.wav')} volume={0.35} />
    </Sequence>
  </>
);

export const Documentary: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: C.navy}}>
    {SCENES.map((s, i) => {
      const from = sec(s.t);
      const last = i === SCENES.length - 1;
      const dur = sec(s.end) - from + (last ? 0 : XFADE);
      return (
        <Sequence key={i} from={from} durationInFrames={dur} name={`${i} ${s.g ?? s.clip?.[0]}`}>
          <SceneView s={s} i={i} dur={dur} />
        </Sequence>
      );
    })}
    <Subtitles />
    <Audio src={staticFile('audio/voice.wav')} />
    <Audio
      src={staticFile('audio/music.wav')}
      volume={(f) => interpolate(f, [TOTAL_FRAMES - sec(16), TOTAL_FRAMES - sec(14), TOTAL_FRAMES - 30, TOTAL_FRAMES], [0.55, 1.6, 1.6, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}
    />
    <Sfx />
  </AbsoluteFill>
);
