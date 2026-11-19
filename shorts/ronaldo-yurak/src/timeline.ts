// All timings come from the Whisper word timestamps of the voice-over (seconds).
export const FPS = 30;
export const AUDIO_SECONDS = 35.02;
export const TOTAL_FRAMES = Math.ceil(AUDIO_SECONDS * FPS);
export const f = (sec: number) => Math.round(sec * FPS);

// Heartbeats baked into the score (audio/synth.py). Visuals pulse on these.
const calm: number[] = [];
for (let t = 0; t < 10.6; t += 60 / 72) calm.push(t);
export const CALM_BEATS = calm;
export const TACHY_BEATS = [10.68, 11.3467, 11.9366, 12.4587, 12.9208, 13.3296, 13.6915, 14.0117];
export const RECOVERY_BEATS = [15.1, 15.95, 16.8, 17.65];
export const LATE_BEATS = [27.56, 28.3];
export const ALL_BEATS = [...CALM_BEATS, ...TACHY_BEATS, ...RECOVERY_BEATS, ...LATE_BEATS];

// Scene boundaries (seconds) — see STORYBOARD.md
export const S = {
  hookName: [0, 0.76],
  hookAge: [0.76, 1.7],
  hookQuit: [1.7, 4.48],
  today: [4.48, 5.32],
  fans: [5.32, 6.76],
  teen: [6.76, 8.26],
  heart: [8.26, 10.68],
  doctors: [10.68, 11.48],
  bpm: [11.48, 14.36],
  treatment: [14.36, 16.12],
  soon: [16.12, 17.06],
  training: [17.06, 18.5],
  later: [18.5, 19.2],
  map: [19.2, 22.8],
  trophies: [22.8, 24.3],
  twist: [24.3, 25.34],
  boy: [25.34, 27.84],
  history: [27.84, 29.1],
  famous: [29.1, 31.46],
  versus: [31.46, AUDIO_SECONDS],
} as const;
