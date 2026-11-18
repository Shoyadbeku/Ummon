"""Build one shot and save it as blend/<shot>.blend.
usage: python3 build_scene.py s1 [s2 ...]  (or 'all')"""
import sys, os, time, bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import shots as SH
import shots2  # registers s1b..s6

if __name__ == "__main__":
    names = sys.argv[1:] or ["all"]
    if names == ["all"]:
        names = list(SH.BUILDERS)
    os.makedirs(os.path.join(C.ROOT, "blend"), exist_ok=True)
    for n in names:
        t = time.time()
        sc = SH.build(n)
        C.setup_render(sc, "final")
        out = os.path.join(C.ROOT, "blend", f"{n}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        if os.path.exists(out + "1"):
            os.remove(out + "1")
        print(f"[build] {n} -> {out} ({time.time() - t:.1f}s)")
