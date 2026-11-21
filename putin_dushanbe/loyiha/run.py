import sys, time
sys.path.insert(0, sys.argv[1])
import sb, engine
k, n, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
F = int(round(sb.TOTAL * engine.FPS)); step = (F + n - 1) // n
f0, f1 = k * step, min(F, (k + 1) * step)
t = time.time(); engine.render_range(sb.timeline(), f0, f1, out); print('part', k, f0, f1, round(time.time() - t), 's', flush=True)
