import {makeProject} from '@motion-canvas/core';

import scene from './scenes/scene?scene';
import audio from '../audio/audio.wav';

export default makeProject({
  scenes: [scene],
  audio,
});
