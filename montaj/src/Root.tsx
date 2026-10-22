import {Composition} from 'remotion';
import {Montaj} from './Montaj';
import {DURATION, FPS} from './data';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Montaj"
    component={Montaj}
    durationInFrames={Math.round(DURATION * FPS)}
    fps={FPS}
    width={1080}
    height={1920}
  />
);
