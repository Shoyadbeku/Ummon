"""Bitta kadrni (shot) render qilish.

python render_shot.py --shot 3 --out OUT_DIR [--frames 140 150] [--step 1] [--samples 16]
ZACK_ASSETS muhit o'zgaruvchisi yuklangan assetlar papkasini ko'rsatadi.
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]

import bpy  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--shot", type=int, required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--frames", type=int, nargs=2)
ap.add_argument("--only", type=int, nargs="*", help="faqat shu kadrlar (sinov)")
ap.add_argument("--samples", type=int)
ap.add_argument("--save-blend", action="store_true")
args = ap.parse_args()

bpy.ops.wm.read_factory_settings(use_empty=True)
if args.shot <= 5:
    import shots_room as S
else:
    import shots_throat as S
sc = S.build(args.shot)
if args.samples:
    sc.cycles.samples = args.samples
if args.frames:
    sc.frame_start, sc.frame_end = args.frames
os.makedirs(args.out, exist_ok=True)
if args.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.out, f"shot{args.shot:02d}.blend"))
t0 = time.time()
if args.only:
    for f in args.only:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(args.out, f"s{args.shot:02d}_{f:04d}.jpg")
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {f} {time.time() - t0:.1f}s", flush=True)
else:
    # qolgan joyidan davom etish: mavjud kadrlar o'tkazib yuboriladi,
    # placeholder bir xil shotni parallel jarayonlarga bo'lib beradi
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    sc.render.filepath = os.path.join(args.out, "####")
    bpy.ops.render.render(animation=True)
print(f"DONE shot {args.shot} in {time.time() - t0:.1f}s", flush=True)
