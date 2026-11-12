import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {KenBurnsImage} from './components/KenBurnsImage';
import {FilmOverlay} from './components/FilmOverlay';
import {Captions} from './components/Captions';
import {YearStamp} from './components/YearStamp';
import {ChapterTag} from './components/ChapterTag';
import {Intro} from './components/Intro';
import {Outro} from './components/Outro';
import {CHAPTERS, STAMPS, VIDEO} from './config';
import scenes from './data/scenes.json';
import subtitles from './data/subtitles.json';
import {SceneData, Word} from './types';

const SCENES = scenes as SceneData[];
const SUBS = subtitles as {start: number; end: number; words: Word[]}[];

export const totalFrames = (fps: number) => {
  const voiceEnd = SCENES[SCENES.length - 1].end;
  return Math.ceil((VIDEO.introSeconds + voiceEnd + VIDEO.outroSeconds) * fps);
};

const Scene: React.FC<{scene: SceneData; index: number; dur: number}> = ({scene, index, dur}) => {
  const frame = useCurrentFrame();
  const T = VIDEO.transitionFrames;
  const opacity = interpolate(frame, [0, T], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: index === 0 ? 1 : opacity}}>
      <KenBurnsImage src={scene.image} index={index} />
    </AbsoluteFill>
  );
};

const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 6, background: 'rgba(255,255,255,0.08)'}}>
      <div style={{width: `${(frame / durationInFrames) * 100}%`, height: '100%', background: VIDEO.accent, opacity: 0.85}} />
    </div>
  );
};

export const TarixVideo: React.FC = () => {
  const {fps, durationInFrames} = useVideoConfig();
  const frame = useCurrentFrame();
  const intro = Math.round(VIDEO.introSeconds * fps);
  const T = VIDEO.transitionFrames;
  const toF = (sec: number) => intro + Math.round(sec * fps);
  const voiceEndF = toF(SCENES[SCENES.length - 1].end);

  // Musiqa: intro va outro'da balandroq, ovoz paytida pastroq
  const musicVol = (f: number) => {
    const v = interpolate(f, [0, intro - 15, intro + 10, voiceEndF, voiceEndF + 30], [
      VIDEO.musicVolumeIntro,
      VIDEO.musicVolumeIntro,
      VIDEO.musicVolume,
      VIDEO.musicVolume,
      VIDEO.musicVolumeIntro,
    ], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    const fadeOut = interpolate(f, [durationInFrames - fps * 2, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    const fadeIn = interpolate(f, [0, fps], [0, 1], {extrapolateRight: 'clamp'});
    return v * fadeOut * fadeIn;
  };

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {/* Rasmlar */}
      {SCENES.map((s, i) => {
        const from = i === 0 ? intro - T : toF(s.start) - Math.round(T / 2);
        const next = SCENES[i + 1];
        const until = next ? toF(next.start) + Math.round(T / 2) : durationInFrames;
        const dur = Math.max(1, until - from);
        return (
          <Sequence key={`${i}-${s.image}`} from={from} durationInFrames={dur} name={`Sahna ${i + 1}`}>
            <Scene scene={s} index={i} dur={dur} />
          </Sequence>
        );
      })}

      <FilmOverlay />

      {/* Yil belgilari */}
      {SCENES.map((s, i) => {
        const st = STAMPS[s.n];
        if (!st || s.repeat) return null;
        // Bob sarlavhasi bilan bir vaqtda bo'lsa, 3 soniya keyin chiqadi
        const isChapter = CHAPTERS.some((c, ci) => ci > 0 && c.scene === s.n);
        const from = toF(s.start) + (isChapter ? 3 * fps : 0);
        const dur = Math.max(30, toF(SCENES[i + 1]?.end ?? s.end) - from);
        return (
          <Sequence key={`stamp-${i}`} from={from} durationInFrames={Math.min(dur, fps * 6)} name={`Yil ${st[0]}`}>
            <YearStamp year={st[0]} caption={st[1]} />
          </Sequence>
        );
      })}

      {/* Boblar */}
      {CHAPTERS.map((c, ci) => {
        const s = SCENES.find((x) => x.n === c.scene && !x.repeat);
        if (!s) return null;
        const nextC = CHAPTERS[ci + 1];
        const from = toF(s.start);
        const ns = nextC ? SCENES.find((x) => x.n === nextC.scene && !x.repeat) : undefined;
        const until = ns ? toF(ns.start) : voiceEndF;
        return (
          <Sequence key={c.label} from={from} durationInFrames={Math.max(1, until - from)} name={c.label}>
            <ChapterTag label={c.label} big={ci > 0} />
          </Sequence>
        );
      })}

      {/* Subtitrlar (ovozga moslangan) */}
      {SUBS.map((sub, i) => {
        const from = toF(sub.start) - 6;
        const nxt = SUBS[i + 1];
        const until = nxt ? Math.min(toF(sub.end) + 12, toF(nxt.start) - 6) : toF(sub.end) + 12;
        return (
          <Sequence key={`sub-${i}`} from={from} durationInFrames={Math.max(1, until - from)} name={`Subtitr ${i + 1}`} layout="none">
            <Captions words={sub.words} sceneStart={sub.start - 6 / fps} sceneEnd={sub.end} />
          </Sequence>
        );
      })}

      <ProgressBar />

      <Sequence from={0} durationInFrames={intro + 10} name="Intro">
        <Intro image={SCENES[0].image} />
      </Sequence>
      <Sequence from={voiceEndF} name="Outro">
        <Outro />
      </Sequence>

      {/* Audio */}
      <Sequence from={intro} name="Ovoz">
        <Audio src={staticFile(VIDEO.voice)} />
      </Sequence>
      <Audio src={staticFile(VIDEO.music)} volume={musicVol} />
    </AbsoluteFill>
  );
};
