import {getStaticFiles, staticFile, type CalculateMetadataFunction} from 'remotion';
import {getAudioDurationInSeconds} from '@remotion/media-utils';
import {narrationOf, SCENES, type SceneConfig} from '../data/script';

export const FPS = 60;
export const WIDTH = 1920;
export const HEIGHT = 1080;

/** Ovoz boshlanishidan oldingi pauza (sahna "nafas olishi" uchun) */
export const LEAD_IN_SEC = 0.45;
/** Ovoz tugaganidan keyingi pauza */
export const TAIL_SEC = 0.55;
/** Sahnalar orasidagi o'tish davomiyligi (kadr) */
export const TRANSITION_FRAMES = 30;
/** Ovoz yo'q bo'lsa — o'zbekcha nutq tezligi taxmini (belgi/soniya) */
const CHARS_PER_SEC = 13.5;

const AUDIO_EXT = ['wav', 'mp3', 'm4a', 'aac', 'ogg'];
const IMAGE_EXT = ['png', 'jpg', 'jpeg', 'webp'];

export type SceneTiming = {
  id: string;
  /** Sahna davomiyligi (o'tish qoplamasi bilan birga) */
  durationInFrames: number;
  /** Ovoz/nutq sahna ichida qaysi kadrdan boshlanadi */
  speechStart: number;
  /** Nutq davomiyligi (kadr) — kinetik matn shunga sinxronlanadi */
  speechFrames: number;
  /** public/ ichidagi ovoz fayli (yoki null) */
  audio: string | null;
  /** public/ ichidagi AI rasm (yoki null) */
  image: string | null;
};

export type PalovVideoProps = {
  timeline: SceneTiming[];
  /** Ovoz bo'lmasa ham fon musiqasi uchun (ixtiyoriy) public/music/... */
  music: string | null;
  musicVolume: number;
};

const findAsset = (names: string[], base: string, exts: string[]): string | null => {
  for (const ext of exts) {
    const candidate = `${base}.${ext}`;
    if (names.includes(candidate)) return candidate;
  }
  return null;
};

export const estimateSpeechSeconds = (scene: SceneConfig) =>
  Math.max(1.6, narrationOf(scene).length / CHARS_PER_SEC);

export const buildTimeline = async (): Promise<{timeline: SceneTiming[]; music: string | null}> => {
  let names: string[] = [];
  try {
    names = getStaticFiles().map((f) => f.name);
  } catch {
    names = [];
  }

  const timeline: SceneTiming[] = [];
  for (const scene of SCENES) {
    const audio = findAsset(names, `voiceover/${scene.id}`, AUDIO_EXT);
    const image = findAsset(names, `images/${scene.id}`, IMAGE_EXT);

    let speechSec = estimateSpeechSeconds(scene);
    if (audio) {
      try {
        speechSec = await getAudioDurationInSeconds(staticFile(audio));
      } catch (err) {
        console.warn(`[timeline] ${audio} o'qilmadi, taxminiy davomiylik ishlatiladi`, err);
      }
    }

    const speechStart = Math.round(LEAD_IN_SEC * FPS);
    const speechFrames = Math.round(speechSec * FPS);
    const natural = speechStart + speechFrames + Math.round(TAIL_SEC * FPS) + TRANSITION_FRAMES;
    const durationInFrames = Math.max(natural, Math.round(scene.minSeconds * FPS) + TRANSITION_FRAMES);

    timeline.push({id: scene.id, durationInFrames, speechStart, speechFrames, audio, image});
  }

  const music = findAsset(names, 'music/background', AUDIO_EXT);
  return {timeline, music};
};

export const totalDuration = (timeline: SceneTiming[]) =>
  timeline.reduce((sum, t) => sum + t.durationInFrames, 0) - TRANSITION_FRAMES * (timeline.length - 1);

/** Har bir sahnaning global boshlanish kadri (o'tishlar hisobga olingan) */
export const sceneStarts = (timeline: SceneTiming[]) => {
  const starts: number[] = [];
  let acc = 0;
  for (const t of timeline) {
    starts.push(acc);
    acc += t.durationInFrames - TRANSITION_FRAMES;
  }
  return starts;
};

export const calculatePalovMetadata: CalculateMetadataFunction<PalovVideoProps> = async ({props}) => {
  const {timeline, music} = await buildTimeline();
  return {
    durationInFrames: totalDuration(timeline),
    fps: FPS,
    width: WIDTH,
    height: HEIGHT,
    props: {...props, timeline, music},
  };
};
