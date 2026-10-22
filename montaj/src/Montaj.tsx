import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CALLOUTS, DURATION, f, LINES, SHOTS} from './data';
import {Callout} from './Callouts';
import {Subtitles} from './Subtitles';

const groupStart = (frame: number) => {
  let start = 0;
  for (const s of SHOTS) {
    if (f(s.from) > frame) break;
    if (s.cut) start = f(s.from);
  }
  return start;
};

const VideoLayer: React.FC = () => {
  const frame = useCurrentFrame();
  const g = groupStart(frame);
  const t = frame - g;
  // Sekin Ken Burns + kesishda zoom-punch.
  const drift = interpolate(t, [0, 240], [1.03, 1.1], {extrapolateRight: 'clamp'});
  const punch = interpolate(t, [0, 9], [0.14, 0], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const shake = t < 9 ? Math.sin(t * 2.3) * (9 - t) * 1.2 : 0;
  const blur = interpolate(t, [0, 5], [10, 0], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill
      style={{
        transform: `scale(${drift + punch}) translateX(${shake}px)`,
        filter: `contrast(1.08) saturate(1.15) blur(${g === 0 ? 0 : blur}px)`,
      }}
    >
      {SHOTS.map((s, i) => (
        <Sequence key={i} from={f(s.from)} durationInFrames={f(s.to) - f(s.from)}>
          <OffthreadVideo
            src={staticFile(`clip${s.clip}.mp4`)}
            trimBefore={f(s.src)}
            playbackRate={s.rate}
            muted
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const Flash: React.FC = () => {
  const frame = useCurrentFrame();
  const g = groupStart(frame);
  if (g === 0) return null;
  const o = interpolate(frame - g, [0, 6], [0.75, 0], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: '#fff6dc', opacity: o}} />;
};

const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        height: 10,
        width: `${(frame / durationInFrames) * 100}%`,
        background: 'linear-gradient(90deg,#ffb300,#ffe14d)',
        boxShadow: '0 0 18px rgba(255,200,0,0.8)',
      }}
    />
  );
};

export const Montaj: React.FC = () => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, 8], [1, 0], {extrapolateRight: 'clamp'});
  const fadeOut = interpolate(frame, [f(DURATION) - 12, f(DURATION)], [0, 1], {extrapolateLeft: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: '#000', fontFamily: '"Inter Display", Inter, sans-serif'}}>
      <VideoLayer />
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%), linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)',
        }}
      />
      <Flash />

      {CALLOUTS.map((c, i) => (
        <Sequence key={i} from={f(c.from)} durationInFrames={f(c.to) - f(c.from)}>
          <Callout {...c} />
        </Sequence>
      ))}

      <Subtitles lines={LINES} hideAfter={45.4} />
      <Progress />

      <Audio src={staticFile('ovoz.mp3')} />
      {SHOTS.filter((s) => s.cut && s.from > 0).map((s, i) => (
        <Sequence key={`w${i}`} from={Math.max(0, f(s.from) - 6)} durationInFrames={20}>
          <Audio src={staticFile('whoosh.wav')} volume={0.28} />
        </Sequence>
      ))}
      {CALLOUTS.filter((c) => c.kind !== 'hook').map((c, i) => (
        <Sequence key={`p${i}`} from={f(c.from)} durationInFrames={12}>
          <Audio src={staticFile(c.kind === 'sls' || c.kind === 'stamp' ? 'boom.wav' : 'pop.wav')} volume={0.3} />
        </Sequence>
      ))}

      <AbsoluteFill style={{backgroundColor: '#000', opacity: Math.max(fadeIn, fadeOut)}} />
    </AbsoluteFill>
  );
};
