import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import Ctx
from engine import render
import timeline

W = int(sys.argv[1]); H = W * 9 // 16
out = sys.argv[2]
t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
t1 = float(sys.argv[4]) if len(sys.argv) > 4 else None
preset = sys.argv[5] if len(sys.argv) > 5 else "faster"
ctx = Ctx(W, H, 25)
shots = timeline.build(ctx)
render(ctx, shots, out, timeline.global_overlays(ctx), t0, t1, preset=preset, crf=17 if W >= 3000 else 20)
