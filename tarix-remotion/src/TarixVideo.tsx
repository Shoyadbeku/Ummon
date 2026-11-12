import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming, type TransitionPresentation } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { fonts } from "./fonts";
import type { Scene, TarixProps } from "./schema";
import { Grain, ThemeContext } from "./components/ui";
import { Intro } from "./scenes/Intro";
import { Chapter } from "./scenes/Chapter";
import { ImageScene } from "./scenes/ImageScene";
import { MapScene } from "./scenes/MapScene";
import { Timeline } from "./scenes/Timeline";
import { Quote } from "./scenes/Quote";
import { Person } from "./scenes/Person";
import { Stats } from "./scenes/Stats";
import { Outro } from "./scenes/Outro";

export const FPS = 30;

const renderScene = (s: Scene) => {
  switch (s.type) {
    case "intro":
      return <Intro {...s} />;
    case "chapter":
      return <Chapter {...s} />;
    case "image":
      return <ImageScene {...s} />;
    case "map":
      return <MapScene {...s} />;
    case "timeline":
      return <Timeline {...s} />;
    case "quote":
      return <Quote {...s} />;
    case "person":
      return <Person {...s} />;
    case "stats":
      return <Stats {...s} />;
    case "outro":
      return <Outro {...s} />;
  }
};

export const transitionFrames = (p: Pick<TarixProps, "transition" | "transitionSeconds">) =>
  p.transition === "none" ? 0 : Math.round(p.transitionSeconds * FPS);

/** Total length = sum of scenes minus the overlap each transition creates. */
export const totalFrames = (p: TarixProps) => {
  const sum = p.scenes.reduce((a, s) => a + Math.round(s.seconds * FPS), 0);
  const overlap = transitionFrames(p) * Math.max(0, p.scenes.length - 1);
  return Math.max(1, sum - overlap);
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const presentation = (kind: TarixProps["transition"]): TransitionPresentation<any> => {
  switch (kind) {
    case "slide":
      return slide({ direction: "from-right" }) as TransitionPresentation<any>;
    case "wipe":
      return wipe({ direction: "from-left" }) as TransitionPresentation<any>;
    default:
      return fade() as TransitionPresentation<any>;
  }
};

const Watermark: React.FC<{ text: string; color: string }> = ({ text, color }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  if (!text || frame < 60 || frame > durationInFrames - 30) return null;
  return (
    <div
      style={{
        position: "absolute",
        top: 44,
        right: 56,
        fontFamily: fonts.display,
        fontSize: 20,
        letterSpacing: 6,
        color,
        opacity: 0.45,
      }}
    >
      {text}
    </div>
  );
};

export const TarixVideo: React.FC<TarixProps> = (props) => {
  const { theme, scenes, grain, watermark } = props;
  const tf = transitionFrames(props);
  return (
    <ThemeContext.Provider value={theme}>
      <AbsoluteFill style={{ background: theme.background }}>
        <TransitionSeries>
          {scenes.flatMap((s, i) => [
            <TransitionSeries.Sequence
              key={`s${i}`}
              durationInFrames={Math.max(tf + 1, Math.round(s.seconds * FPS))}
              name={`${i + 1}. ${s.type}`}
            >
              {renderScene(s)}
            </TransitionSeries.Sequence>,
            i < scenes.length - 1 && tf > 0 ? (
              <TransitionSeries.Transition
                key={`t${i}`}
                presentation={presentation(props.transition)}
                timing={linearTiming({ durationInFrames: tf })}
              />
            ) : null,
          ].filter(Boolean))}
        </TransitionSeries>
        <Watermark text={watermark} color={theme.text} />
        {grain ? <Grain /> : null}
      </AbsoluteFill>
    </ThemeContext.Provider>
  );
};
