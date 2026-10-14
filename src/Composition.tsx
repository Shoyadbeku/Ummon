import React from 'react';
import {AbsoluteFill, Html5Audio, interpolate, interpolateColors, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {TransitionSeries, springTiming, linearTiming, type TransitionPresentation} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {wipe} from '@remotion/transitions/wipe';
import {flip} from '@remotion/transitions/flip';
import {clockWipe} from '@remotion/transitions/clock-wipe';
import {iris} from '@remotion/transitions/iris';
import {pushCut} from '@remotion/transitions/push-cut';
import {SCENES, type TransitionKind} from './data/script';
import {AnimatedBackground} from './components/background/AnimatedBackground';
import {SceneProvider} from './lib/scene-context';
import {sceneStarts, TRANSITION_FRAMES, type PalovVideoProps} from './lib/timeline';
import {COLORS, FONT_BODY} from './lib/theme';
import {Scene01Hook} from './scenes/Scene01Hook';
import {Scene02Intro} from './scenes/Scene02Intro';
import {Scene03HotPlov} from './scenes/Scene03HotPlov';
import {Scene04Stop} from './scenes/Scene04Stop';
import {Scene05Photoshoot} from './scenes/Scene05Photoshoot';
import {Scene06Waiting} from './scenes/Scene06Waiting';
import {Scene07Passport} from './scenes/Scene07Passport';
import {Scene08Posted} from './scenes/Scene08Posted';
import {Scene09Moral} from './scenes/Scene09Moral';
import {Scene10Question} from './scenes/Scene10Question';

const SCENE_COMPONENTS: Record<string, React.FC> = {
  '01-hook': Scene01Hook,
  '02-intro': Scene02Intro,
  '03-hot-plov': Scene03HotPlov,
  '04-stop': Scene04Stop,
  '05-photoshoot': Scene05Photoshoot,
  '06-waiting': Scene06Waiting,
  '07-passport': Scene07Passport,
  '08-posted': Scene08Posted,
  '09-moral': Scene09Moral,
  '10-question': Scene10Question,
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyPresentation = TransitionPresentation<any>;

const presentationFor = (kind: TransitionKind, width: number, height: number): AnyPresentation => {
  switch (kind) {
    case 'slide-left':
      return slide({direction: 'from-right'});
    case 'slide-up':
      return slide({direction: 'from-bottom'});
    case 'wipe':
      return wipe({direction: 'from-top-left'});
    case 'flip':
      return flip({direction: 'from-right'});
    case 'clock':
      return clockWipe({width, height});
    case 'iris':
      return iris({width, height});
    case 'push':
      return pushCut({flashColor: '#FFFFFF', flashOpacity: 0.35});
    default:
      return fade();
  }
};

export const PalovVideo: React.FC<PalovVideoProps> = ({timeline, music, musicVolume}) => {
  const frame = useCurrentFrame();
  const {width, height, durationInFrames} = useVideoConfig();
  const starts = sceneStarts(timeline);

  // Fon rangi sahnalar bo'ylab yumshoq o'zgaradi
  const accent =
    timeline.length > 1
      ? interpolateColors(
          frame,
          starts.map((s, i) => (i === 0 ? s : s + TRANSITION_FRAMES / 2)),
          SCENES.slice(0, timeline.length).map((s) => s.accent),
        )
      : SCENES[0].accent;

  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bg0}}>
      <AnimatedBackground accent={accent} />

      <TransitionSeries>
        {timeline.map((t, i) => {
          const scene = SCENES.find((s) => s.id === t.id)!;
          const Comp = SCENE_COMPONENTS[t.id];
          const elements = [
            <TransitionSeries.Sequence key={t.id} durationInFrames={t.durationInFrames} name={`${t.id} ${scene.title}`}>
              <SceneProvider scene={scene} timing={t}>
                <Comp />
                {t.audio && (
                  <Sequence from={t.speechStart} name={`voiceover ${t.id}`}>
                    <Html5Audio src={staticFile(t.audio)} />
                  </Sequence>
                )}
              </SceneProvider>
            </TransitionSeries.Sequence>,
          ];
          if (i < timeline.length - 1) {
            const timing =
              scene.transitionOut === 'clock' || scene.transitionOut === 'iris'
                ? linearTiming({durationInFrames: TRANSITION_FRAMES})
                : springTiming({config: {damping: 200}, durationInFrames: TRANSITION_FRAMES});
            elements.push(
              <TransitionSeries.Transition
                key={`${t.id}-tr`}
                presentation={presentationFor(scene.transitionOut, width, height)}
                timing={timing}
              />,
            );
          }
          return elements;
        })}
      </TransitionSeries>

      {music && (
        <Html5Audio
          src={staticFile(music)}
          volume={(f) =>
            interpolate(f, [0, 30, durationInFrames - 90, durationInFrames], [0, musicVolume, musicVolume, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })
          }
        />
      )}

      <Hud accent={accent} />
    </AbsoluteFill>
  );
};

/** Doimiy interfeys: brend belgisi va progress chizig'i */
const Hud: React.FC<{accent: string}> = ({accent}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = frame / Math.max(1, durationInFrames - 1);
  const intro = interpolate(frame, [0, 30], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          top: 58,
          right: 130,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          fontFamily: FONT_BODY,
          fontWeight: 700,
          fontSize: 26,
          letterSpacing: 4,
          color: COLORS.text,
          opacity: intro * 0.85,
          padding: '12px 24px',
          borderRadius: 40,
          background: 'rgba(255,255,255,0.06)',
          border: '1.5px solid rgba(255,255,255,0.14)',
        }}
      >
        <span>🍚</span>
        <span>PALOV HIKOYALARI</span>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 8, background: 'rgba(255,255,255,0.06)'}}>
        <div
          style={{
            width: `${progress * 100}%`,
            height: '100%',
            background: `linear-gradient(90deg, ${accent}, #FFFFFF)`,
            boxShadow: `0 0 24px ${accent}`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
