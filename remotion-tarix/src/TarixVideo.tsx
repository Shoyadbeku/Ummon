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
import {OVERLAYS, Overlay, At} from './data/overlays';
import {LowerThird} from './components/graphics/LowerThird';
import {Location} from './components/graphics/Location';
import {Stat} from './components/graphics/Stat';
import {Keyword} from './components/graphics/Keyword';
import {Stamp} from './components/graphics/Stamp';
import {Versus} from './components/graphics/Versus';
import {Question} from './components/graphics/Question';
import {LightLeak} from './components/graphics/LightLeak';

const SCENES = scenes as SceneData[];
const SUBS = subtitles as {start: number; end: number; words: Word[]}[];

// Overlay vaqtini topish: gap boshi yoki aniq so'z aytilgan payt
const resolveAt = (at: At): number => {
  const sub = SUBS[at.seg];
  let t = sub.start;
  if (at.word) {
    const w = sub.words.find((x) => x.t === at.word) ?? sub.words.find((x) => x.t.includes(at.word as string));
    if (w) t = w.s;
  }
  return t + (at.delay ?? 0);
};

const DEFAULT_DUR: Record<Overlay['type'], number> = {
  lowerThird: 5, location: 5, stat: 3.6, keyword: 2.2, stamp: 3.5, versus: 10, question: 12,
};
const SFX: Record<Overlay['type'], [string, number][]> = {
  lowerThird: [['sfx/whoosh.wav', 0.22]],
  location: [['sfx/pop.wav', 0.35], ['sfx/whoosh.wav', 0.15]],
  stat: [['sfx/pop.wav', 0.35]],
  keyword: [['sfx/impact.wav', 0.5], ['sfx/whoosh.wav', 0.2]],
  stamp: [['sfx/stamp.wav', 0.6]],
  versus: [['sfx/whoosh.wav', 0.35], ['sfx/impact.wav', 0.3]],
  question: [['sfx/whoosh.wav', 0.3]],
};

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

  // Overlaylar vaqt bo'yicha
  const items = OVERLAYS.map((o) => {
    const from = toF(resolveAt(o.at));
    let dur = Math.round((('dur' in o ? o.dur : undefined) ?? DEFAULT_DUR[o.type]) * fps);
    if (o.type === 'versus') dur = toF(SUBS[o.untilSeg].start) - from;
    if (o.type === 'question') dur = voiceEndF - from;
    return {o, from, dur};
  });
  // Bir joyda turadigan elementlar ustma-ust tushmasin: keyingisi chiqishidan oldin tugaydi
  const slot = (t: Overlay['type']) => (t === 'location' || t === 'stat' || t === 'stamp' ? 'rt' : t === 'lowerThird' ? 'lt' : 'c');
  items.forEach((it, i) => {
    const next = items.slice(i + 1).find((x) => slot(x.o.type) === slot(it.o.type) && x.from > it.from);
    if (next && it.from + it.dur > next.from - 4) it.dur = Math.max(20, next.from - 4 - it.from);
  });
  // Kamera silkinishi (kalit so'z va muhrlarda)
  const hits = items.filter((x) => x.o.type === 'keyword' || x.o.type === 'stamp').map((x) => x.from + 7);
  const h = hits.find((f) => frame >= f && frame < f + 12);
  const amp = h === undefined ? 0 : 14 * (1 - (frame - h) / 12);
  const shake = amp ? `translate(${Math.sin(frame * 3.1) * amp}px, ${Math.cos(frame * 2.3) * amp}px) scale(1.02)` : undefined;
  // Bob boshlanishlari (yorug'lik o'tishi uchun)
  const chapterFrames = CHAPTERS.slice(1)
    .map((c) => SCENES.find((x) => x.n === c.scene && !x.repeat))
    .filter(Boolean)
    .map((x) => toF((x as SceneData).start));

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <AbsoluteFill style={{transform: shake}}>
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

      </AbsoluteFill>

      <FilmOverlay />

      {/* Bob o'tishlari: light leak + whoosh */}
      {chapterFrames.map((f, i) => (
        <Sequence key={`leak-${i}`} from={f - 14} durationInFrames={36} name="Light leak">
          <LightLeak seed={i} />
          <Audio src={staticFile('sfx/whoosh.wav')} volume={0.4} />
        </Sequence>
      ))}

      {/* Motion graphics */}
      {items.map(({o, from, dur}, i) => (
        <Sequence key={`ov-${i}`} from={from} durationInFrames={Math.max(1, dur)} name={`${o.type}`}>
          {o.type === 'lowerThird' ? <LowerThird name={o.name} role={o.role} /> : null}
          {o.type === 'location' ? <Location place={o.place} country={o.country} coords={o.coords} /> : null}
          {o.type === 'stat' ? <Stat value={o.value} suffix={o.suffix} label={o.label} sub={o.sub} /> : null}
          {o.type === 'keyword' ? <Keyword text={o.text} color={o.color} /> : null}
          {o.type === 'stamp' ? <Stamp text={o.text} sub={o.sub} /> : null}
          {o.type === 'versus' ? (
            <Versus left={o.left} right={o.right} rightAt={toF(SUBS[o.at.seg + 1].start) - from} />
          ) : null}
          {o.type === 'question' ? <Question title={o.title} a={o.a} b={o.b} cta={o.cta} /> : null}
          {SFX[o.type].map(([src, v], k) => (
            <Audio key={k} src={staticFile(src)} volume={v} />
          ))}
        </Sequence>
      ))}

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
            <Audio src={staticFile('sfx/impact.wav')} volume={0.22} />
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
        <Audio src={staticFile('sfx/impact.wav')} volume={0.45} />
      </Sequence>
      <Sequence from={intro - 16} durationInFrames={36} name="Intro leak">
        <LightLeak />
        <Audio src={staticFile('sfx/whoosh.wav')} volume={0.35} />
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
