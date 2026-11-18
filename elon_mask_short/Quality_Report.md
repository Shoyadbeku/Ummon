# Quality Report — Final_Video.mp4

## Technical specs (measured with ffprobe and ebur128)
| Parameter | Requirement | Result |
|---|---|---|
| Aspect ratio / resolution | 9:16, 1080×1920 | ✅ 1080×1920 |
| FPS | 30 or 60 | ✅ 30 fps (CFR) |
| Video codec | H.264 | ✅ H.264 High, CRF 17, ~9.1 Mbit/s |
| Audio codec | AAC | ✅ AAC-LC 48 kHz, 256 kbit/s |
| Duration | Matches the original audio (39.37 s) | ✅ 39.37–39.40 s |
| Loudness | Platform standard | ✅ −14.0 LUFS integrated, true peak −1.3 dBFS |
| Size | — | 46.5 MB, `+faststart` |

## The 10-point checklist
1. **Does each shot match what the voice says?** ✅ Every scene is tied to the words in it (see `Storyboard.md`). The company names, years and the 307 million counter appear at the moment each word is spoken. Despite the file name, the recording is about Elon Musk, not neutron stars, so the visuals follow the recording.
2. **Is the subtitle timing right?** ✅ Word-level timestamps come from Whisper large-v3. Unclear spots ("1990-yillarda", "daholik") were re-checked by transcribing the clip in several languages. The active word is highlighted.
3. **Do the motion graphics run smoothly?** ✅ Spring- and easing-based animations. Checked frame by frame across 30 sample frames.
4. **Any unwanted black frames?** ✅ `blackdetect` found 0. Every shot overlaps the next by 8 frames. Fixed during QC: the bottom half of the shower/gym split screen was black for ~1 s; it now shows the gym clip dimmed until its cue.
5. **Is the voice/music balance right?** ✅ The voice was cleaned (highpass, denoise, EQ, de-ess, 3:1 compression) and set to −16 LUFS. Music sits at roughly −16 dB below the voice and rises slightly after the drop at 32.7 s. SFX are kept low.
6. **Is the visual rhythm engaging?** ✅ 23+ shot changes plus graphic layers; the picture refreshes every 0.5–2.5 s.
7. **Is any footage repeated too much?** ✅ The only reuse is deliberate: the "orbit" clip for two cuts at 34.4 s and 34.9 s, and the "office sleeper" callback in the 30.5 s flashback, which uses a different clip.
8. **Is text readable on a phone screen?** ✅ Captions are Montserrat 900 at 82–88 px with a 14 px black stroke. They sit at y≈1300–1500 with 130 px right padding to clear the right-hand buttons. Headlines are Anton at 130–300 px. Fixed during QC: in "1990-YILLARDA U" the words ran together; long words now scale less when highlighted.
9. **Is the opening hook strong?** ✅ Frame 0: Falcon 9 liftoff + white flash + shake + impact. At 1.4 s the portrait whips in with a gold "ENG BOY"; at 3.0 s a giant "ILON MASK".
10. **Is it studio-grade?** Assessment: high-quality social documentary editing. See the limitations below.

## Honest limitations
- **Media sources.** Only sources with verifiable licences were used: NASA, Mixkit and Wikimedia Commons. Clips from X, Facebook, VK, Reddit and YouTube were not used, because their reuse rights could not be verified. Pexels and Pixabay returned 403 from this environment.
- **No footage of Zip2 or the 1990s.** None exists under an open licence. That scene uses an original motion-graphics reconstruction of a 90s browser window.
- **Music and SFX were chosen by loudness analysis, not by ear.** The track's drop is placed on the 32.72 s cue. Give it one listen before posting.
- **Subtitle accuracy.** The Uzbek ASR was corrected by hand, but a few words may still need checking against your own pronunciation, e.g. "qilishga esa" at 16.4 s.
- **Attribution.** The CC BY / CC BY-SA photos require credit. A ready-to-paste credit line for the post description is in `Media_Sources.md`.

## Loudness normalisation command
```bash
ffmpeg -i render_raw.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_...:linear=true" -c:a aac -b:a 256k -movflags +faststart Final_Video.mp4
```
