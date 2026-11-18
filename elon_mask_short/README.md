# Ilon Mask — Shorts / Reels / TikTok (9:16)

A 39-second vertical video cut to the original voice-over (`Neytron_yulduzining_..._SadoStudio_7.wav`).
Despite the file name, the recording is about Elon Musk, so the edit follows what the voice says.

| File | What it is |
|---|---|
| `Final_Video.mp4` | Final video: 1080×1920, 30 fps, H.264 + AAC, −14 LUFS |
| `Subtitles.srt` | Synced Uzbek subtitles |
| `remotion/` | Remotion + React + TypeScript project (editable source) |
| `Media_Sources.md` | Every video, photo and sound used, with its licence |
| `Storyboard.md` | Scenes, time codes and effects |
| `Quality_Report.md` | Final quality check |
| `tools/` | Helper scripts (Wikimedia fetch, SRT generation) |

## Re-rendering
```bash
cd remotion
npm install
npx remotion studio                       # preview and edit
npx remotion render src/index.ts Main out/render_raw.mp4 --codec=h264 --crf=17
# then normalise the loudness to -14 LUFS (see Quality_Report.md)
```
Word timings are in `remotion/src/data/words.ts`; all scenes are in `remotion/src/Main.tsx`.
The voice-over was cleaned with ffmpeg: `highpass 75 → afftdn → EQ (−2 dB @220 Hz, +2.5 dB @3.2 kHz, +1.5 dB high shelf) → deesser → acompressor 3:1 → loudnorm −16 LUFS`.
