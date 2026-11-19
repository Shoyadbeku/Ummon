import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, continueRender, delayRender, interpolate, Sequence, staticFile} from 'remotion';
import {MUSIC_VOL, SB, SceneT} from './data';
import {fontsReady} from './fonts';
import {DipBlack, Scene, TransitionKind} from './components/Scene';
import {Bookends, Grade, Grain, LightLeak, Particles, Progress} from './components/Effects';
import {Subtitles} from './components/Subtitles';
import {Overlays} from './components/Overlays';

const TR = 14; // default cross-dissolve length (frames)

const transitionFor = (s: SceneT, prev: SceneT | undefined): TransitionKind => {
  if (!prev) return 'none';
  if (s.id === 'TITLE') return 'white';
  if (s.motion === 'punch' || prev.motion === 'punch') return 'cut';
  if (s.motion === 'flash') return 'white';
  if (s.motion === 'dim') return 'black';
  if (s.motion === 'slam') return 'cut';
  const nearTheory = SB.overlays.some((o) => (o.type === 'theory' || o.type === 'chapter') && Math.abs(o.from - s.from) < 12);
  if (nearTheory) return 'wipe';
  return 'fade';
};

const Visuals: React.FC = () => (
  <>
    {SB.scenes.map((s, i) => {
      const prev = SB.scenes[i - 1];
      const next = SB.scenes[i + 1];
      const t = transitionFor(s, prev);
      const nextT = next ? transitionFor(next, s) : 'none';
      const tail = nextT === 'cut' || nextT === 'none' ? 0 : TR + 6; // keep drawing under the incoming scene
      const dur = s.to - s.from + tail;
      return (
        <React.Fragment key={s.id}>
          <Sequence from={s.from} durationInFrames={dur} name={`${s.id} ${s.note}`}>
            <Scene scene={s} dur={dur} transition={t} tr={TR} />
          </Sequence>
          {t === 'black' ? (
            <Sequence from={s.from - Math.round(TR * 0.6)} durationInFrames={TR * 3} name="dip">
              <DipBlack tr={TR} />
            </Sequence>
          ) : null}
        </React.Fragment>
      );
    })}
  </>
);

const AudioLayers: React.FC = () => (
  <>
    {/* HOOK: two lines of the original narration, re-used as a cold open (no new words, voice untouched) */}
    {SB.hookClips.map((c, i) => {
      const len = Math.round((c.toSec - c.fromSec) * SB.fps);
      return (
        <Sequence key={`h${i}`} from={c.atFrame} durationInFrames={len} name={`hook voice ${i + 1}`}>
          <Audio
            src={staticFile(SB.voice)}
            trimBefore={Math.round(c.fromSec * SB.fps)}
            trimAfter={Math.round(c.toSec * SB.fps)}
            volume={(f) => interpolate(f, [0, 3, len - 4, len], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}
          />
        </Sequence>
      );
    })}
    {/* full original narration */}
    <Sequence from={SB.hookFrames} name="voice">
      <Audio src={staticFile(SB.voice)} />
    </Sequence>
    {/* original score, ducked under the voice frame-by-frame */}
    <Audio src={staticFile(SB.music)} volume={(f) => MUSIC_VOL[f] ?? 0} />
    {SB.sfx.map((x, i) => (
      <Sequence key={`s${i}`} from={x.from} durationInFrames={SB.fps * 9} name={`sfx ${x.src}`}>
        <Audio src={staticFile(x.src)} volume={x.volume} />
      </Sequence>
    ))}
  </>
);

export const Main: React.FC = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    fontsReady.then(() => continueRender(handle)).catch((e) => {
      console.error(e);
      continueRender(handle);
    });
  }, [handle]);

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <Visuals />
      <Grade />
      <Particles />
      {SB.overlays
        .filter((o) => o.type === 'chapter')
        .map((o, i) => (
          <Sequence key={`lk${i}`} from={o.from - 4} durationInFrames={48} layout="none">
            <LightLeak dur={48} />
          </Sequence>
        ))}
      <Overlays />
      <Subtitles />
      <Progress />
      <Grain />
      <Bookends />
      <AudioLayers />
    </AbsoluteFill>
  );
};
