"""Render frames of a shot blend. Resumable: skips frames already on disk.
usage: python3 render.py <shot> [--frames 10,20,30 | --range a-b] [--preview] [--out DIR]
       [--res 540x960] [--samples N] [--force]"""
import sys, os, time, argparse, bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import shots as SH

ap = argparse.ArgumentParser()
ap.add_argument("shot")
ap.add_argument("--frames")
ap.add_argument("--range")
ap.add_argument("--preview", action="store_true")
ap.add_argument("--out")
ap.add_argument("--res")
ap.add_argument("--samples", type=int)
ap.add_argument("--force", action="store_true")
a = ap.parse_args(sys.argv[1:])

blend = os.path.join(C.ROOT, "blend", f"{a.shot}.blend")
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
res = tuple(int(v) for v in a.res.split("x")) if a.res else (1080, 1920)
C.setup_render(sc, "preview" if a.preview else "final", res, a.samples)
out = a.out or os.path.join(C.ROOT, "renders", "previews" if a.preview else "final")
os.makedirs(out, exist_ok=True)
if a.frames:
    frames = [int(x) for x in a.frames.split(",")]
elif a.range:
    s, e = (int(x) for x in a.range.split("-"))
    frames = list(range(s, e + 1))
else:
    frames = list(range(sc.frame_start, sc.frame_end + 1))
log = open(os.path.join(C.ROOT, "logs", f"render_{a.shot}.log"), "a")
for f in frames:
    path = os.path.join(out, f"frame_{f:06d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 1000 and not a.force:
        continue
    t = time.time()
    sc.frame_set(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    msg = f"{time.strftime('%H:%M:%S')} {a.shot} frame {f} cam={sc.camera.name} {res[0]}x{res[1]} {time.time() - t:.1f}s"
    print("[render]", msg, flush=True)
    log.write(msg + "\n"); log.flush()
