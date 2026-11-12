import React from "react";
import { Composition, Folder } from "remotion";
import { TarixVideo, FPS, totalFrames } from "./TarixVideo";
import { tarixSchema, type TarixProps } from "./schema";
import { defaultProps } from "./defaultProps";

// Har bir sahnani alohida ko'rish / render qilish uchun yordamchi kompozitsiyalar
const single = (i: number): TarixProps => ({
  ...defaultProps,
  transition: "none",
  scenes: [defaultProps.scenes[i]],
});

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="TarixVideo"
      component={TarixVideo}
      schema={tarixSchema}
      defaultProps={defaultProps}
      fps={FPS}
      width={1920}
      height={1080}
      durationInFrames={totalFrames(defaultProps)}
      calculateMetadata={({ props }) => ({ durationInFrames: totalFrames(props) })}
    />
    <Folder name="Sahnalar">
      {defaultProps.scenes.map((s, i) => (
        <Composition
          key={i}
          id={`Sahna-${i + 1}-${s.type}`}
          component={TarixVideo}
          schema={tarixSchema}
          defaultProps={single(i)}
          fps={FPS}
          width={1920}
          height={1080}
          durationInFrames={totalFrames(single(i))}
          calculateMetadata={({ props }) => ({ durationInFrames: totalFrames(props) })}
        />
      ))}
    </Folder>
  </>
);
