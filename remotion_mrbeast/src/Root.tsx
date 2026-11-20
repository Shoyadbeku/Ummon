import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {DURATION, FPS, HEIGHT, WIDTH} from './timeline';

export const Root: React.FC = () => (
	<Composition id="Main" component={Main} durationInFrames={DURATION} fps={FPS} width={WIDTH} height={HEIGHT} />
);
