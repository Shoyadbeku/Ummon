/**
 * Headless render kirish nuqtasi (scripts/render.mjs Playwright orqali ochadi).
 * Motion Canvas Renderer'ini to'g'ridan-to'g'ri ishga tushiradi va kadrlarni
 * @motion-canvas/ffmpeg exporteriga yuboradi -> output/<name>.mp4
 */
import {Renderer, RendererResult, Vector2} from '@motion-canvas/core';
import project from './project?project';

const log = document.getElementById('log')!;
const w = window as any;
w.renderStatus = 'working';

const renderer = new Renderer(project);
renderer.onFrameChanged.subscribe(frame => {
  w.renderFrame = frame;
  log.textContent = `frame ${frame}`;
});
renderer.onFinished.subscribe(result => {
  w.renderStatus = RendererResult[result];
  log.textContent = `finished: ${RendererResult[result]}`;
});

renderer.render({
  name: 'bitta-kichkina-narsa',
  range: [0, Infinity],
  fps: 30,
  size: new Vector2(1920, 1080),
  resolutionScale: 1,
  colorSpace: 'srgb',
  background: '#000000',
  exporter: {
    name: '@motion-canvas/ffmpeg',
    options: {fastStart: true, includeAudio: true},
  },
});
