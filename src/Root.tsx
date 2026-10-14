import React from 'react';
import {Composition} from 'remotion';
import {PalovVideo} from './Composition';
import {calculatePalovMetadata, FPS, HEIGHT, WIDTH, type PalovVideoProps} from './lib/timeline';

const defaultProps: PalovVideoProps = {
  timeline: [],
  music: null,
  musicVolume: 0.12,
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="PalovVideo"
    component={PalovVideo}
    width={WIDTH}
    height={HEIGHT}
    fps={FPS}
    durationInFrames={FPS * 60}
    defaultProps={defaultProps}
    // Davomiylik ovoz fayllaridan (yoki matndan) avtomatik hisoblanadi
    calculateMetadata={calculatePalovMetadata}
  />
);
