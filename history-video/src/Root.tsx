import React from "react";
import { Composition } from "remotion";
import { HistoryVideo, FPS, totalFrames } from "./HistoryVideo";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="HistoryVideo"
    component={HistoryVideo}
    durationInFrames={totalFrames}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
