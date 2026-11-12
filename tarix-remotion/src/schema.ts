import { zColor } from "@remotion/zod-types";
import { z } from "zod";

// Har bir sahna uchun umumiy maydon: davomiylik (soniya)
const base = { seconds: z.number().min(1).max(120) };

// Rasm yo'li: "public/" papkasidagi fayl nomi (masalan "samarqand.jpg") yoki
// to'liq https:// manzil. Bo'sh qoldirilsa, chiroyli zaxira fon chiziladi.
const image = z.string();

export const introScene = z.object({
  type: z.literal("intro"),
  ...base,
  kicker: z.string(),
  title: z.string(),
  subtitle: z.string(),
  yearFrom: z.number(),
  yearTo: z.number(),
  image,
});

export const chapterScene = z.object({
  type: z.literal("chapter"),
  ...base,
  number: z.number().int().min(1).max(50),
  title: z.string(),
  dates: z.string(),
});

export const imageScene = z.object({
  type: z.literal("image"),
  ...base,
  image,
  caption: z.string(),
  place: z.string(),
  date: z.string(),
  credit: z.string(),
  zoom: z.enum(["in", "out"]),
  pan: z.enum(["left", "right", "up", "down", "none"]),
});

export const mapScene = z.object({
  type: z.literal("map"),
  ...base,
  title: z.string(),
  subtitle: z.string(),
  // Xarita chegaralari (uzunlik / kenglik, gradusda)
  bounds: z.object({
    lonMin: z.number(),
    lonMax: z.number(),
    latMin: z.number(),
    latMax: z.number(),
  }),
  points: z.array(
    z.object({
      name: z.string(),
      lon: z.number(),
      lat: z.number(),
      label: z.string(),
    }),
  ),
  image,
});

export const timelineScene = z.object({
  type: z.literal("timeline"),
  ...base,
  title: z.string(),
  events: z.array(
    z.object({
      year: z.string(),
      title: z.string(),
      text: z.string(),
    }),
  ),
});

export const quoteScene = z.object({
  type: z.literal("quote"),
  ...base,
  text: z.string(),
  author: z.string(),
  source: z.string(),
});

export const personScene = z.object({
  type: z.literal("person"),
  ...base,
  name: z.string(),
  years: z.string(),
  role: z.string(),
  facts: z.array(z.string()),
  image,
});

export const statsScene = z.object({
  type: z.literal("stats"),
  ...base,
  title: z.string(),
  stats: z.array(
    z.object({
      value: z.number(),
      prefix: z.string(),
      suffix: z.string(),
      label: z.string(),
    }),
  ),
});

export const outroScene = z.object({
  type: z.literal("outro"),
  ...base,
  title: z.string(),
  channel: z.string(),
  cta: z.string(),
  next: z.string(),
});

export const scene = z.discriminatedUnion("type", [
  introScene,
  chapterScene,
  imageScene,
  mapScene,
  timelineScene,
  quoteScene,
  personScene,
  statsScene,
  outroScene,
]);

export const tarixSchema = z.object({
  theme: z.object({
    accent: zColor(),
    background: zColor(),
    text: zColor(),
    paper: zColor(),
  }),
  transition: z.enum(["fade", "slide", "wipe", "none"]),
  transitionSeconds: z.number().min(0).max(3),
  grain: z.boolean(),
  watermark: z.string(),
  scenes: z.array(scene),
});

export type TarixProps = z.infer<typeof tarixSchema>;
export type Scene = z.infer<typeof scene>;
export type Theme = TarixProps["theme"];
export type IntroProps = z.infer<typeof introScene>;
export type ChapterProps = z.infer<typeof chapterScene>;
export type ImageProps = z.infer<typeof imageScene>;
export type MapProps = z.infer<typeof mapScene>;
export type TimelineProps = z.infer<typeof timelineScene>;
export type QuoteProps = z.infer<typeof quoteScene>;
export type PersonProps = z.infer<typeof personScene>;
export type StatsProps = z.infer<typeof statsScene>;
export type OutroProps = z.infer<typeof outroScene>;
