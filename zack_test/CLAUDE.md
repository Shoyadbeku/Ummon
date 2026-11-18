# zack_test — procedural Blender short ("Rat on the can")

43.7 s vertical (1080×1920, 24 fps) 3D short built entirely from Python with `bpy==5.2.3`
(Blender 5.2.3 LTS as a pip module — no Blender GUI needed). Narration: `audio/narration.wav`.

## Pipeline
```
python3 scripts/fetch_assets.py          # Mixamo (HF) + Poly Haven CC0 -> assets/
python3 scripts/build_scene.py all       # -> blend/<shot>.blend (s1 s1b s2 s3 s4 s5 s6)
python3 scripts/render.py s3 --frames 420 --preview         # one preview frame
scripts/render_final.sh                  # all 1049 frames, resumable -> renders/final/
python3 scripts/sound_design.py          # procedural SFX -> audio/sfx.wav
python3 scripts/assemble_video.py        # -> output/final_video.mp4
python3 scripts/qa_video.py              # ffprobe/blackdetect/loudness/flicker -> logs/qa_report.json
```
Edit timing lives in `scripts/shots.py: SHOTS` (global frame ranges). Every shot blend uses
global frame numbers, so frames drop straight into `renders/final/frame_XXXXXX.png`.

## Files
- `mixchar.py` — Mixamo character/motion loading, NLA sequencing, hand-grip & bone attach.
- `scripts/common.py` — render settings, PBR/procedural materials, cameras, lights, procedural can (lid, tear panel, tab).
- `scripts/sets.py` — store with open multideck cooler; night warehouse with can pallet.
- `scripts/shots.py` (s1) and `scripts/shots2.py` (s1b–s6) — shot builders.
- `tools/contact_sheet.py` — tile test renders.

## Known pitfalls (learned the hard way)
- Blender 5.x: `Action.fcurves` is gone — use `layers[].strips[].channelbags[].fcurves` (`common.fcurves_of`).
  NLA strips need `strip.action_slot`; extrapolation property is `NlaStrip.extrapolation` (not `extend_mode`).
- Mixamo character FBX and `animation_motion/*.fbx` share the 65-bone `mixamorig:` rig; rest poses differ by
  only ~4°, so actions transfer directly. Hips translation is rescaled by hip-height ratio.
- Mixamo FBX materials import gloss maps into Roughness → plastic skin. `mixchar.fix_materials` unlinks them.
- Megan faces −Y at import (armature rot X = 90°, scale 0.01). In `Drinking` the **left** hand drinks;
  in `Lifting` the **right** hand picks up from ~0.23 m.
- After setting `obj.location/scale`, call `view_layer.update()` before reading `matrix_world`
  (otherwise identity → 1 m organs in the x-ray shot).
- Boolean cutters must not be `hide_viewport=True` (excluded from depsgraph) — only `hide_render`.
- Poly Haven API returns 403 to urllib's default User-Agent — send a UA header.
- Poly Haven `street_rat` is 0.148 m long, static (no rig); its head points −Y. `shots2.make_rat`
  auto-detects head direction; the gallop is procedural (bob/pitch/yaw per frame).
- `render.py` calls `setup_render`, which reads exposure from the scene custom prop `exposure`
  (warehouse sets +1.0).
- No GPU in the cloud container: CPU Cycles ≈ 85 s/frame at 1080×1920 / 20 spp; ≈ 15–25 s at 540×960 / 16 spp.
  The approved final uses 540×960 + Lanczos upscale in FFmpeg.
- Blend files are 10–70 MB (packed 4K Mixamo textures) and assets are 139 MB: both are git-ignored
  and fully reproducible with the two commands above.
