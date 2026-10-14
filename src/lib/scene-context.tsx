import React, {createContext, useContext} from 'react';
import type {SceneConfig} from '../data/script';
import {FPS, type SceneTiming} from './timeline';

type SceneCtx = {scene: SceneConfig; timing: SceneTiming};

const Ctx = createContext<SceneCtx | null>(null);

export const SceneProvider: React.FC<SceneCtx & {children: React.ReactNode}> = ({scene, timing, children}) => (
  <Ctx.Provider value={{scene, timing}}>{children}</Ctx.Provider>
);

export const useScene = () => {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useScene() faqat <SceneProvider> ichida ishlaydi');
  return ctx;
};

export type Window = {start: number; end: number; duration: number};

/**
 * Har bir matn bo'lagi (segment) nutqning qaysi qismida aytilishini
 * belgilar soniga proporsional ravishda hisoblaydi. Ovoz fayli bo'lsa,
 * uning haqiqiy davomiyligi ishlatiladi — shu bilan matn ovozga sinxron chiqadi.
 */
export const useSegmentWindows = (): Window[] => {
  const {scene, timing} = useScene();
  if (timing.segmentTimes) {
    // Aniq vaqtlar (ElevenLabs alignment) — kadrlarga aylantiramiz
    return timing.segmentTimes.map(([a, b]) => {
      const start = timing.speechStart + Math.round(a * FPS);
      const end = timing.speechStart + Math.round(b * FPS);
      return {start, end, duration: Math.max(6, end - start)};
    });
  }
  const lengths = scene.segments.map((s) => s.text.length + 1);
  const total = lengths.reduce((a, b) => a + b, 0);
  let acc = 0;
  return lengths.map((len) => {
    const start = timing.speechStart + (acc / total) * timing.speechFrames;
    acc += len;
    const end = timing.speechStart + (acc / total) * timing.speechFrames;
    return {start: Math.round(start), end: Math.round(end), duration: Math.round(end - start)};
  });
};
