import React from "react";
import { Composition } from "remotion";
import { Documentary } from "./Documentary";
import timeline from "./data/timeline.json";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Documentary"
      component={Documentary}
      durationInFrames={timeline.durationInFrames}
      fps={timeline.fps}
      width={1920}
      height={1080}
    />
  );
};
