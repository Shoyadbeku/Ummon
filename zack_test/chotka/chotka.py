# "Unitaz aerozoli va tish cho'tkasi" — Zack D. Films uslubida 40.1 s video (962 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, yostiq/yostiq.py (lib.py yordamchilari, micro.py bakteriyalari).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_chotka.sh
# Render: OUT=/tmp/claude-0/frames_c/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/chotka/chotka.py --render
# Sinov:  FRAMES=20,60,130,200 PCT=30 OUT=/tmp/claude-0/test/ ... --render   |   Bo'lak: RANGE=a,b
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ZT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "yostiq"))
from lib import *                     # sahnani tozalaydi; bpy, math, random, Vector, mc, sc, R, PH, BK, yordamchilar
import bmesh
import numpy as np
from mathutils import Quaternion
import micro as U
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_c/")
random.seed(7)
END = 962
sc.frame_start, sc.frame_end = 1, END
def V(*a): return Vector(a)
def ckey(idb, path=None): interp(idb, "CONSTANT", path)
def sstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (28, "room"), (62, "cup"), (122, "morning"), (152, "face"), (175, "reveal"), (237, "lid"),
         (285, "vortex"), (326, "burst"), (371, "drops"), (450, "height"), (509, "spread"), (566, "hours"),
         (627, "drift"), (683, "land"), (739, "micro"), (817, "breed"), (851, "cap"), (911, "trap")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
F_REVEAL = 176      # "ko'zga ko'rinmas" — crash zoom
F_PUSH = 258        # tugma bosiladi
F_FLUSH = 280       # girdob boshlanadi
F_BURST = 338       # aerozol otiladi ("aerozol" 14.2 s)
F_TOP = 492         # bulut 2 m ga yetadi ("otilib chiqadi")
F_SP = 512          # xona bo'ylab tarqalish
F_DR = 630          # cho'tka tomon suzish
F_CAP = 884         # qopqoq kiydiriladi
F_TRAP = 912        # rentgen

# ======================================================================
# 1) HAMMOM (hammom + hojatxona bitta xonada): plitka, unitaz, lavabo, oyna, stakandagi cho'tkalar
# ======================================================================
bath = []
def B_(o): bath.append(o); return o
X0, X1, Y0, Y1, HZ = -1.6, 1.6, -1.4, 1.4, 2.6
tile_w = pbr("tile_w", "long_white_tiles", 1.2); tile_f = pbr("tile_f", "floor_tiles_06", 0.9)
plaster = pbr("plaster", "painted_plaster_wall", 0.8, tint=(0.86, 0.9, 0.93))
B_(plane("floor", (X1 - X0, Y1 - Y0), (0, 0, 0), tile_f))
B_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), (0, 0, HZ + 0.025), mat("ceil_m", (0.92, 0.92, 0.9), 0.8)))
B_(box("wall_B", (X1 - X0, 0.1, HZ), (0, Y1 + 0.05, HZ / 2), tile_w))
B_(box("wall_R", (0.1, Y1 - Y0, HZ), (X1 + 0.05, 0, HZ / 2), tile_w))
B_(box("wall_F", (X1 - X0, 0.1, HZ), (0, Y0 - 0.05, HZ / 2), plaster))
# chap devor: deraza (xira shisha) bilan
WY0, WY1, WZ0, WZ1 = -0.55, 0.45, 1.35, 2.2
B_(box("wall_L1", (0.1, WY0 - Y0, HZ), (X0 - 0.05, (Y0 + WY0) / 2, HZ / 2), tile_w))
B_(box("wall_L2", (0.1, Y1 - WY1, HZ), (X0 - 0.05, (WY1 + Y1) / 2, HZ / 2), tile_w))
B_(box("wall_L3", (0.1, WY1 - WY0, WZ0), (X0 - 0.05, (WY0 + WY1) / 2, WZ0 / 2), tile_w))
B_(box("wall_L4", (0.1, WY1 - WY0, HZ - WZ1), (X0 - 0.05, (WY0 + WY1) / 2, (WZ1 + HZ) / 2), tile_w))
frame_m = mat("win_frame", (0.93, 0.93, 0.9), 0.4)
WCn = V(X0 - 0.03, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2)
frost = mat("frost", (0.95, 0.97, 1.0), 0.35, trans=0.9, ior=1.5)
B_(box("win_glass", (0.01, WY1 - WY0, WZ1 - WZ0), tuple(WCn), frost))
for nm, sz, off in (("wf_t", (0.12, WY1 - WY0 + 0.04, 0.05), (0, 0, (WZ1 - WZ0) / 2)), ("wf_b", (0.18, WY1 - WY0 + 0.04, 0.05), (0.04, 0, -(WZ1 - WZ0) / 2)),
                    ("wf_l", (0.12, 0.05, WZ1 - WZ0), (0, -(WY1 - WY0) / 2, 0)), ("wf_r", (0.12, 0.05, WZ1 - WZ0), (0, (WY1 - WY0) / 2, 0)),
                    ("wf_m", (0.08, 0.04, WZ1 - WZ0), (0, 0, 0))):
    B_(box(nm, sz, tuple(WCn + V(*off)), frame_m))
B_(box("baseboard", (X1 - X0, 0.02, 0.08), (0, Y0 + 0.01, 0.04), frame_m))
# eshik (old devorda)
B_(box("door", (0.85, 0.05, 2.05), (0.9, Y0 + 0.02, 1.025), mat("door_m", (0.82, 0.8, 0.76), 0.5), bevel=0.01))
B_(sphere("door_knob", 0.03, (0.56, Y0 + 0.07, 1.0), mat("knob", (0.85, 0.85, 0.88), 0.15, metal=1.0), sub=3))
def gltf(path, loc, rot_z=0.0, scale=1.0):
    e = empty(os.path.basename(path).split(".")[0] + "_grp", loc); new = import_gltf(path, e)
    e.rotation_euler.z = R(rot_z); e.scale = (scale,) * 3
    return e, new
TOIL = V(-0.85, Y1 - 0.02, 0.0)
toilet, toil_new = gltf(BK + "6a342733_u.glb", tuple(TOIL)); B_(toilet)
SINK = V(0.78, Y1 - 0.29, 0.0)
sink, sink_new = gltf(BK + "a541b293_u.glb", tuple(SINK)); B_(sink)
plant, _ = gltf(PH + "potted_plant_01/potted_plant_01.gltf", (X0 + 0.35, Y0 + 0.4, 0), 40, 1.0); B_(plant)
bpy.context.view_layer.update()
_dg = bpy.context.evaluated_depsgraph_get()
def hit(o, d=V(0, 0, -1)):
    ok, loc, nor, *_ = sc.ray_cast(_dg, Vector(o), d)
    return (loc, nor) if ok else (None, None)
CUPXY = V(SINK.x + 0.38, SINK.y + 0.12, 0)
CTOP = hit(CUPXY + V(0, 0, 1.5))[0].z
BASIN = SINK + V(-0.176, 0.02, 0)
print("counter", round(CTOP, 3))
# unitaz kosasi: suv sathi va radiuslari (ray cast)
BOWL = TOIL + V(0, -0.43, 0)
RIM = hit(BOWL + V(0.17, 0, 1.2))[0].z        # o'rindiq usti
def _rads(z):
    out = []
    for k in range(24):
        a = 2 * math.pi * k / 24; l, _ = hit(BOWL + V(0, 0, z), V(math.cos(a), math.sin(a), 0))
        out.append(((l - (BOWL + V(0, 0, z))).length if l else 0.1) - 0.004)
    return out
WZ = 0.24
while WZ < 0.4 and sum(_rads(WZ)) / 24 < 0.105: WZ += 0.005
rads = []
for k in range(24):
    a = 2 * math.pi * k / 24; l, _ = hit(BOWL + V(0, 0, WZ), V(math.cos(a), math.sin(a), 0))
    rads.append(((l - (BOWL + V(0, 0, WZ))).length if l else 0.1) - 0.004)
print("seat", round(RIM, 3), "water z", round(WZ, 3), "rad", round(min(rads), 3), round(max(rads), 3))
WATER = BOWL + V(0, 0, WZ)
# suv: girdob (shape key "funnel"), aylanuvchi to'lqin normal
bm_ = bmesh.new(); NR_, NA_ = 14, 48
cv = bm_.verts.new((0, 0, 0)); rings = []
for i in range(1, NR_ + 1):
    ring = []
    for k in range(NA_):
        a = 2 * math.pi * k / NA_; rr = np.interp(a, [2 * math.pi * j / 24 for j in range(25)], rads + [rads[0]]) * i / NR_
        ring.append(bm_.verts.new((math.cos(a) * rr, math.sin(a) * rr, 0)))
    rings.append(ring)
for k in range(NA_): bm_.faces.new((cv, rings[0][k], rings[0][(k + 1) % NA_]))
for i in range(NR_ - 1):
    for k in range(NA_): bm_.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % NA_], rings[i][(k + 1) % NA_]))
wme = bpy.data.meshes.new("water"); bm_.to_mesh(wme); bm_.free()
water = bpy.data.objects.new("water", wme); sc.collection.objects.link(water); water.location = tuple(WATER); smooth(water); B_(water)
water.shape_key_add(name="Basis", from_mix=False); fk = water.shape_key_add(name="funnel", from_mix=False); fk.value = 0
for v, bv in zip(fk.data, wme.vertices):
    r_ = Vector((bv.co.x, bv.co.y)).length / max(rads); v.co.z = -0.09 * (1 - min(1, r_)) ** 2.2 + 0.012 * min(1, r_)
skey(fk, [(1, 0), (F_FLUSH, 0), (F_FLUSH + 14, 1.0), (F_BURST + 10, 1.0), (F_BURST + 40, 0.15), (S["burst"][1] + 1, 0)])
wm = bpy.data.materials.new("water_m"); wm.use_nodes = True; N = wm.node_tree.nodes; L = wm.node_tree.links; b_ = N["Principled BSDF"]
b_.inputs["Base Color"].default_value = (0.55, 0.78, 0.85, 1); b_.inputs["Transmission Weight"].default_value = 0.55
b_.inputs["IOR"].default_value = 1.333; b_.inputs["Roughness"].default_value = 0.03
tc = N.new("ShaderNodeTexCoord"); spin = value_node(wm, "spin", 0.0)
sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
rr_ = P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]), P.math_n(N, L, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"])))
ang = P.math_n(N, L, "MULTIPLY", spin, P.math_n(N, L, "DIVIDE", 0.05, P.math_n(N, L, "ADD", rr_, 0.02)))
vr = N.new("ShaderNodeVectorRotate"); vr.rotation_type = "Z_AXIS"; L.new(tc.outputs["Object"], vr.inputs["Vector"]); L.new(ang, vr.inputs["Angle"])
wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 9.0; wv.inputs["Distortion"].default_value = 6.0
wv.inputs["Detail"].default_value = 3; L.new(vr.outputs[0], wv.inputs["Vector"])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 14.0; L.new(vr.outputs[0], nz.inputs["Vector"])
amp = value_node(wm, "amp", 0.15)
hgt = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", wv.outputs["Fac"], nz.outputs["Fac"]), amp)
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 1.0; bp.inputs["Distance"].default_value = 0.01
L.new(hgt, bp.inputs["Height"]); L.new(bp.outputs[0], b_.inputs["Normal"])
wme.materials.append(wm)
for f_, s_, a_ in ((1, 0.0, 0.08), (F_FLUSH, 0.0, 0.08), (F_FLUSH + 10, 3.0, 0.9), (S["burst"][1], 60.0, 0.9), (S["burst"][1] + 1, 60.0, 0.1)):
    val_key(wm, "spin", f_, s_); val_key(wm, "amp", f_, a_)
interp(wm.node_tree, "LINEAR")
# suv tugmasi (bak ustida, xrom) — bosilganda pastga
BTN = TOIL + V(0, -0.15, 0.0); BTN.z = hit(BTN + V(0, 0, 1.5))[0].z
btn = B_(cyl("flush_btn", 0.028, 0.012, tuple(BTN + V(0, 0, 0.004)), mat("btn_m", (0.9, 0.9, 0.92), 0.12, metal=1.0), verts=40))
key(btn, F_PUSH - 3, loc=tuple(BTN + V(0, 0, 0.004))); key(btn, F_PUSH, loc=tuple(BTN + V(0, 0, -0.004))); key(btn, F_PUSH + 8, loc=tuple(BTN + V(0, 0, 0.004)))
print("button", tuple(round(x, 3) for x in BTN))
# oyna, chiroq, sochiq, qog'oz, gilam, devor soati
MIR = V(SINK.x, Y1 - 0.005, 1.45)
B_(plane("mirror", (1.1, 0.85), tuple(MIR), mat("mirror", (0.95, 0.95, 0.95), 0.02, metal=1.0), rot=(90, 0, 0)))
B_(box("mirror_frame", (1.14, 0.015, 0.89), tuple(MIR + V(0, 0.0095, 0)), mat("mframe", (0.1, 0.1, 0.11), 0.4)))
B_(box("mirror_light", (0.9, 0.04, 0.03), tuple(MIR + V(0, -0.03, 0.5)), mat("mlight", (1, 0.97, 0.92), 0.5, emit=6.0)))
towel_m = mat("towel_m", (0.62, 0.78, 0.86), 0.95)
B_(cyl("towel_bar", 0.008, 0.5, (X1 - 0.06, 0.55, 1.15), mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0), rot=(90, 0, 0)))
B_(box("towel", (0.05, 0.45, 0.6), (X1 - 0.07, 0.55, 0.88), towel_m, bevel=0.02))
B_(cyl("t_roll", 0.055, 0.1, (X0 + 0.07, TOIL.y - 0.45, 0.7), mat("paper_m", (0.95, 0.95, 0.93), 0.8), rot=(90, 0, 90)))
B_(plane("bath_mat", (0.7, 0.45), (SINK.x - 0.1, 0.45, 0.005), mat("rug", (0.3, 0.55, 0.62), 0.95)))
CLK = V(X1 - 0.02, -0.35, 1.95)
clk = B_(empty("clock", tuple(CLK))); clk.rotation_euler = (0, R(-90), 0)        # mahalliy +Z -> dunyo -X (xonaga)
cyl("clk_body", 0.15, 0.04, (0, 0, 0.02), mat("clk_body_m", (0.08, 0.08, 0.09), 0.3), parent=clk, verts=48)
cyl("clk_face", 0.13, 0.005, (0, 0, 0.042), mat("clk_face_m", (0.95, 0.94, 0.9), 0.5), parent=clk, verts=48)
tick_m = mat("tick", (0.05, 0.05, 0.05), 0.5)
for k in range(12):
    a = 2 * math.pi * k / 12
    box(f"tick{k}", (0.007, 0.022 if k % 3 else 0.03, 0.004), (0.108 * math.sin(a), 0.108 * math.cos(a), 0.046), tick_m, rot=(0, 0, -math.degrees(a)), parent=clk)
hand_h = empty("hand_h", (0, 0, 0.048), clk); hand_m = empty("hand_m", (0, 0, 0.05), clk)
box("hh", (0.011, 0.065, 0.003), (0, 0.028, 0), tick_m, parent=hand_h)
box("hm", (0.007, 0.095, 0.003), (0, 0.043, 0), mat("hand_red", (0.7, 0.05, 0.03), 0.4), parent=hand_m)
H0_, H1_ = S["hours"]
for f_, hm, mm in ((1, -45, 0), (H0_, -45, 0), (H1_, -45 - 60, -720)):
    hand_h.rotation_euler = (0, 0, R(hm)); hand_h.keyframe_insert("rotation_euler", frame=f_)
    hand_m.rotation_euler = (0, 0, R(mm)); hand_m.keyframe_insert("rotation_euler", frame=f_)
for o in (hand_h, hand_m): interp(o, "LINEAR")

# ======================================================================
# 2) TISH CHO'TKASI (makro "qahramon" cho'tka): dasta, bosh, tuklar (to'p-to'p), tomchilar, qopqoq
#    mahalliy o'qlar: dasta +Z bo'ylab (0..0.183), tuklar -Y tomonga
# ======================================================================
brush_m = mat("brush_plastic", (0.04, 0.22, 0.85), 0.25, coat=0.6, sss=0.1)
grip_m = mat("brush_grip", (0.92, 0.94, 0.96), 0.55)
nylon_w = mat("nylon_w", (0.93, 0.95, 0.97), 0.3, trans=0.25, sss=0.2, coat=0.3)
nylon_b = mat("nylon_b", (0.25, 0.65, 0.95), 0.3, trans=0.25, sss=0.2, coat=0.3)
for m in (nylon_w, nylon_b): m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.0002
HEADZ0, HEADZ1, THK = 0.150, 0.183, 0.0048
def _wt(z):
    """(eni, qalinligi) dasta bo'ylab"""
    if z < 0.004: return 0.010 * (0.6 + 0.4 * z / 0.004), 0.0075 * (0.6 + 0.4 * z / 0.004)
    if z < 0.10: return 0.0115, 0.0078
    if z < 0.13: t = (z - 0.10) / 0.03; return 0.0115 - 0.006 * t, 0.0078 - 0.0028 * t
    if z < HEADZ0: return 0.0055, 0.005
    if z < HEADZ0 + 0.004: t = (z - HEADZ0) / 0.004; return 0.0055 + 0.0055 * math.sqrt(t), THK
    if z < HEADZ1 - 0.005: return 0.011, THK
    t = (z - (HEADZ1 - 0.005)) / 0.005; return 0.011 * math.sqrt(max(0.05, 1 - t * t)), THK
def handle_mesh(name):
    zs = [i / 120 * HEADZ1 for i in range(121)]; n = 20; vs = []; fs = []
    for z in zs:
        w_, t_ = _wt(z)
        for x, y in rrect(w_, t_, 0.0, n, 0.35): vs.append((x, y + (0.0015 if z < 0.13 else 0.0) * math.sin(z / 0.13 * math.pi), z))
    for i in range(len(zs) - 1):
        for j in range(n): fs.append((i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j))
    fs.append(tuple(range(n))[::-1]); fs.append(tuple(range(len(zs) * n - n, len(zs) * n)))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p in me.polygons: p.use_smooth = True
    return me
def bristle_meshes(seed=3):
    """24 ta to'p (3 x 8), har birida ~18 tuk; ikkita mesh: oq va ko'k qatorlar. Qaytaradi: (mesh_w, mesh_b, tuk uchlari)"""
    rnd = random.Random(seed); out = {"w": ([], []), "b": ([], [])}; tips = []
    y0 = -THK / 2 + 0.0004
    for ci, cx in enumerate((-0.0034, 0.0, 0.0034)):
        for ri in range(8):
            cz = HEADZ0 + 0.0045 + ri * 0.0034
            if cz > HEADZ1 - 0.003: continue
            col = "b" if ri in (0, 1, 6, 7) else "w"
            length = 0.0105 + (0.0012 if ci != 1 else 0.0) + 0.0008 * math.sin(ri * 1.3)
            for k in range(18):
                a = rnd.uniform(0, 6.28); d = 0.00075 * math.sqrt(rnd.random())
                bx, bz = cx + math.cos(a) * d, cz + math.sin(a) * d
                sp = Vector((math.cos(a) * d * 1.6 + rnd.uniform(-0.0003, 0.0003), 0, math.sin(a) * d * 1.6 + rnd.uniform(-0.0003, 0.0003)))
                L_ = length * rnd.uniform(0.95, 1.03); r_ = 0.00011
                base = Vector((bx, y0, bz)); tip = base + Vector((sp.x, -L_, sp.z))
                axis = (tip - base).normalized(); u_ = axis.cross(Vector((0, 0, 1))).normalized(); v_ = axis.cross(u_)
                vs, fs = out[col]; i0 = len(vs)
                for t in (0.0, 0.92):
                    c = base.lerp(tip, t)
                    for j in range(6):
                        aa = 2 * math.pi * j / 6; vs.append(tuple(c + (u_ * math.cos(aa) + v_ * math.sin(aa)) * r_))
                c = base.lerp(tip, 0.975)
                for j in range(6):
                    aa = 2 * math.pi * j / 6; vs.append(tuple(c + (u_ * math.cos(aa) + v_ * math.sin(aa)) * r_ * 0.6))
                vs.append(tuple(tip))
                for ring in range(2):
                    for j in range(6): fs.append((i0 + ring * 6 + j, i0 + ring * 6 + (j + 1) % 6, i0 + (ring + 1) * 6 + (j + 1) % 6, i0 + (ring + 1) * 6 + j))
                for j in range(6): fs.append((i0 + 12 + j, i0 + 12 + (j + 1) % 6, i0 + 18))
                tips.append((tip.copy(), base.copy()))
    mes = []
    for col, m in (("w", nylon_w), ("b", nylon_b)):
        vs, fs = out[col]; me = bpy.data.meshes.new("bristles_" + col); me.from_pydata(vs, [], fs); me.update()
        for p in me.polygons: p.use_smooth = True
        me.materials.append(m); mes.append(me)
    return mes[0], mes[1], tips
HANDLE_ME = handle_mesh("handle"); HANDLE_ME.materials.append(brush_m)
BR_W, BR_B, TIPS = bristle_meshes()
def build_brush(name, parent=None):
    e = empty(name, (0, 0, 0), parent)
    h = bpy.data.objects.new(name + "_handle", HANDLE_ME); sc.collection.objects.link(h); h.parent = e
    for me in (BR_W, BR_B):
        o = bpy.data.objects.new(name + "_" + me.name, me); sc.collection.objects.link(o); o.parent = e
    # rezina tutqich (oq) dasta orqasida
    g = box(name + "_grip", (0.008, 0.002, 0.055), (0, 0.0042, 0.05), grip_m, parent=e, bevel=0.0008)
    return e
HEADC = V(0, -0.006, (HEADZ0 + HEADZ1) / 2)        # tuklar markazi (mahalliy)

# --- stakan + 2 ta BlenderKit cho'tka + qahramon cho'tka ---
cupE, cup_new = gltf(BK + "f70efd3c_u.glb", (CUPXY.x, CUPXY.y, CTOP), -20, 1.0); B_(cupE)
for o in cup_new:
    if o.name.startswith("toothbrush.003") or any(o.name.startswith(f"Circle.{k:03d}") for k in range(10, 15)):
        o.hide_render = True; o.hide_viewport = True
HERO = empty("hero_pos", (0, 0, 0))
hero = build_brush("hero", HERO); B_(HERO)
HERO.parent = cupE; HERO.location = (0.022, 0.006, 0.006); HERO.rotation_euler = (R(-6), R(14), R(70))
bpy.context.view_layer.update()
HM_ = HERO.matrix_world.copy()
HEADW = HM_ @ HEADC
TIPW = [HM_ @ t for t, b in TIPS]
print("hero head", tuple(round(x, 3) for x in HEADW))
water_m = mat("drop_m", (0.9, 0.97, 1.0), 0.02, trans=1.0, ior=1.333)
# ho'l tomchilar tuklar orasida
rd = random.Random(21); hero_drops = []
for i in range(55):
    t, b0 = rd.choice(TIPS); p_ = b0.lerp(t, rd.uniform(0.35, 1.0)) + Vector((rd.uniform(-0.0006, 0.0006), 0, rd.uniform(-0.0006, 0.0006)))
    r_ = rd.uniform(0.00025, 0.0007) if i > 6 else rd.uniform(0.0009, 0.0013)
    o = sphere(f"hdrop{i}", r_, tuple(p_), water_m, scale=(1, 0.85, 1), sub=3, parent=hero); hero_drops.append(o)
# najas zarralari (yashil "UV" ko'rinish): qo'nadiganlar (land) va ko'payadiganlar (trap)
speck_m = mat("speck", (0.35, 0.55, 0.08), 0.5, emit=1.8, emit_col=(0.35, 1.0, 0.15))
speck_m2 = mat("speck2", (0.45, 0.35, 0.1), 0.5, emit=1.2, emit_col=(0.55, 1.0, 0.1))
L0, L1 = S["land"]
rs = random.Random(5); land_specks = []
for i in range(140):
    t, b0 = rs.choice(TIPS); end_ = b0.lerp(t, rs.uniform(0.55, 1.0)) + Vector((rs.uniform(-0.0007, 0.0007), 0, rs.uniform(-0.0007, 0.0007)))
    r_ = rs.uniform(0.00009, 0.00022)
    o = sphere(f"lspk{i}", r_, tuple(end_), speck_m if i % 3 else speck_m2, sub=1, parent=hero)
    st = Vector((rs.uniform(-0.02, 0.02), -rs.uniform(0.01, 0.03), rs.uniform(0.0, 0.035)))
    fa = L0 - 30 + int(rs.uniform(0, 60)); fb = fa + int(rs.uniform(18, 34))
    for f_ in range(L0 - 32, fb + 1, 3):
        u = max(0.0, min(1.0, (f_ - fa) / (fb - fa))); u = 1 - (1 - u) ** 2
        wob = Vector((math.sin(f_ * 0.21 + i) * 0.0015, 0, math.cos(f_ * 0.17 + i) * 0.0015)) * (1 - u)
        key(o, f_, loc=tuple(end_ + st * (1 - u) + wob))
    land_specks.append(o)
# ko'payish (trap): qopqoq ichida yangi zarralar paydo bo'ladi
T0, T1 = S["trap"]
trap_specks = []
for i in range(260):
    t, b0 = rs.choice(TIPS); p_ = b0.lerp(t, rs.uniform(0.2, 1.0)) + Vector((rs.uniform(-0.0009, 0.0009), rs.uniform(-0.0004, 0.0004), rs.uniform(-0.0009, 0.0009)))
    o = sphere(f"tspk{i}", rs.uniform(0.0001, 0.00024), tuple(p_), speck_m, sub=1, parent=hero)
    U.pop(o, T0 + 4 + int((T1 - T0 - 10) * (i / 260) ** 0.7), 5); trap_specks.append(o)
# qopqoq: bosh + tuklarni yopadigan shaffof plastik, bug' tomchilari ichida
cap = empty("capE", (0, 0, 0), hero)
bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0)
for v in bm_.verts: v.co = Vector((v.co.x * 0.0168, (v.co.y + 0.5) * 0.0175 - 0.0148, (v.co.z + 0.5) * 0.043 + HEADZ0 - 0.006))
bmesh.ops.delete(bm_, geom=[f for f in bm_.faces if f.normal.z < -0.9], context="FACES")
cme = bpy.data.meshes.new("cap"); bm_.to_mesh(cme); bm_.free()
cap_o = bpy.data.objects.new("cap_shell", cme); sc.collection.objects.link(cap_o); cap_o.parent = cap
bv = cap_o.modifiers.new("bev", "BEVEL"); bv.width = 0.0035; bv.segments = 5; bv.limit_method = "NONE"
so_ = cap_o.modifiers.new("so", "SOLIDIFY"); so_.thickness = 0.0007
cap_o.modifiers.new("sub", "SUBSURF").levels = 1; smooth(cap_o)
cap_m = bpy.data.materials.new("cap_m"); cap_m.use_nodes = True; N = cap_m.node_tree.nodes; L = cap_m.node_tree.links
cb = N["Principled BSDF"]; cb.inputs["Base Color"].default_value = (0.75, 0.88, 1.0, 1); cb.inputs["Transmission Weight"].default_value = 0.9
cb.inputs["Roughness"].default_value = 0.08; cb.inputs["IOR"].default_value = 1.45
xr = value_node(cap_m, "xray", 0.0)
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.4, 0.75, 1.0, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 2.0), 6.0), em.inputs["Strength"])
tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader"); L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
mx = N.new("ShaderNodeMixShader"); L.new(xr, mx.inputs[0]); L.new(cb.outputs[0], mx.inputs[1]); L.new(ad.outputs[0], mx.inputs[2])
L.new(mx.outputs[0], N["Material Output"].inputs[0]); cme.materials.append(cap_m)
val_key(cap_m, "xray", 1, 0.0); val_key(cap_m, "xray", T0, 1.0); ckey(cap_m.node_tree)
C0, C1 = S["cap"]
key(cap, 1, loc=(0, 0, 0.07)); key(cap, C0 + 4, loc=(0, 0, 0.07)); key(cap, F_CAP - 6, loc=(0, 0, 0.012)); key(cap, F_CAP, loc=(0, 0, 0.0))
fog_drops = []
for i in range(120):
    side = rs.choice(("x+", "x-", "y")); z_ = rs.uniform(HEADZ0, HEADZ0 + 0.03)
    if side == "y": p_ = (rs.uniform(-0.0075, 0.0075), -0.0145, z_)
    else: p_ = ((0.0077 if side == "x+" else -0.0077), rs.uniform(-0.014, 0.001), z_)
    o = sphere(f"fog{i}", rs.uniform(0.00012, 0.0004), p_, water_m, scale=(1, 1, 1), sub=2, parent=cap)
    U.pop(o, T0 + 2 + int(rs.uniform(0, T1 - T0 - 12)), 8); fog_drops.append(o)
vis(cap, [(C0, END)])
for o in land_specks: vis(o, [(L0, L1)] + rng("cap", "trap"), recursive=False)
for o in trap_specks: vis(o, [S["trap"]], recursive=False)

# ======================================================================
# 3) MEGAN: lavabo oldida tish yuvadi (Breathing_Idle + o'ng qo'l IK, cho'tka boshga "bake" qilingan),
#    keyin unitaz bakidagi tugmani bosadi (Button_Pushing + IK)
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften(mmeshes)
for o in mmeshes:
    for m in o.data.materials:
        if m and m.use_nodes and "hair" not in m.name.lower():
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED": n.inputs["Roughness"].default_value = 0.48
BRS = V(BASIN.x + 0.02, 0.6, 0.0); BR_ROT = 180 - 18
LID0, LID1 = S["lid"]
PUSHR = V(-0.4, BTN.y - 0.12, 0.0)                  # bak yonida, tugmaga qaraydi
_d = (BTN - PUSHR); PU_ROT = math.degrees(math.atan2(_d.x, -_d.y))
place(mroot, 1, tuple(BRS), BR_ROT); place(mroot, LID0, tuple(PUSHR), PU_ROT); ckey(mroot)
IDLE = A_("Breathing_Idle.fbx"); PUSH = A_("Button_Pushing.fbx")
s1 = mc.add_strip(meg, IDLE, 1, hold=False, repeat=1.0, blend=0)
s1.use_auto_blend = False; s1.blend_in = s1.blend_out = 0
PS0 = F_PUSH - int(round(33 * 0.8))                 # Button_Pushing: qo'l eng oldinda ~33-kadr (30 fps)
s2 = mc.add_strip(meg, PUSH, min(PS0, LID0), hold=True, blend=0); s2.use_auto_blend = False; s2.blend_in = s2.blend_out = 0
print("idle strip", s1.frame_start, s1.frame_end, "push", s2.frame_start)
headE = child_of_bone("headE", meg, "Head")
MOUTH_IN = V(0.004, 0.008, 0.138); MOUTH_OUT = V(-0.03, -0.012, 0.215); MOUTH = MOUTH_IN; R0_ = 175
_zb = V(0.55, 0.12, -0.82).normalized(); _yb = V(0, -1, 0); _yb = (_yb - _zb * _yb.dot(_zb)).normalized(); _xb = _yb.cross(_zb)
BRQ = Matrix((_xb, _yb, _zb)).transposed().to_4x4()
brushE = empty("brushE")
MB0, MB1 = S["morning"][0], S["reveal"][1]
for f_ in range(1, LID0 + 1):
    sc.frame_set(f_)
    hm = headE.matrix_world.normalized()
    osc = 0.009 * math.sin(f_ * 2 * math.pi / 6.0) * (0.25 if f_ >= R0_ else 1.0)
    MOUTH = MOUTH_IN if f_ < R0_ else MOUTH_OUT
    loc = hm @ (MOUTH + _zb * (-osc) * 0.0 + V(osc, 0, 0) * 0.0)
    M_ = hm.to_3x3().to_4x4() @ BRQ
    q = M_.to_quaternion()
    brushE.rotation_mode = "QUATERNION"; brushE.rotation_quaternion = q; brushE.keyframe_insert("rotation_quaternion", frame=f_)
    loc = loc + (M_.to_3x3() @ V(0, 0, 1)) * osc
    brushE.location = loc; brushE.keyframe_insert("location", frame=f_)
megb = build_brush("megb", brushE)
megb.location = tuple(-HEADC)
gripT = empty("gripT", tuple(V(0, 0, 0.045) - HEADC), brushE)
tipT = empty("tipT", tuple(V(0, 0, 0.10) - HEADC), brushE)
ik = meg.pose.bones["mixamorig:RightForeArm"].constraints.new("IK"); ik.target = gripT; ik.chain_count = 2; ik.use_tail = True
dt = meg.pose.bones["mixamorig:RightHand"].constraints.new("DAMPED_TRACK"); dt.target = tipT; dt.track_axis = "TRACK_Y"
pushT = empty("pushT", tuple(BTN + V(0.03, 0.0, 0.11)))
ik2 = meg.pose.bones["mixamorig:RightForeArm"].constraints.new("IK"); ik2.target = pushT; ik2.chain_count = 2; ik2.use_tail = True
dt2 = meg.pose.bones["mixamorig:RightHand"].constraints.new("DAMPED_TRACK"); dt2.target = empty("btnT", tuple(BTN)); dt2.track_axis = "TRACK_Y"
for bn, c_, keys in (("mixamorig:RightForeArm", ik, [(1, 1.0), (LID0, 0.0)]), ("mixamorig:RightHand", dt, [(1, 1.0), (LID0, 0.0)]),
                     ("mixamorig:RightForeArm", ik2, [(1, 0.0), (F_PUSH - 9, 0.0), (F_PUSH - 2, 1.0), (F_PUSH + 6, 1.0), (F_PUSH + 14, 0.0)]),
                     ("mixamorig:RightHand", dt2, [(1, 0.0), (F_PUSH - 9, 0.0), (F_PUSH - 2, 0.9), (F_PUSH + 6, 0.9), (F_PUSH + 14, 0.0)])):
    for f_, v in keys:
        c_.influence = v; c_.keyframe_insert("influence", frame=f_)
for fc in fcurves(meg):
    if "constraints" in fc.data_path and fc.data_path.endswith("influence"):
        for k_ in fc.keyframe_points:
            if int(k_.co.x) == LID0: k_.interpolation = "CONSTANT"
# ko'pik (og'iz burchagida)
foam_m = mat("foam", (0.97, 0.98, 1.0), 0.6, sss=0.4)
rf = random.Random(4)
for i in range(9):
    p_ = MOUTH_IN + V(rf.uniform(-0.022, 0.012), rf.uniform(-0.008, 0.004), 0.012 + rf.uniform(0, 0.004))
    o = sphere(f"foam{i}", rf.uniform(0.0018, 0.0035), tuple(p_), foam_m, scale=(1, 0.8, 0.7), sub=2, parent=headE)
    vis(o, rng("morning", "face", "reveal"))
# megb: UV ko'rinishda yonuvchi zarralar (reveal)
R0, R1 = S["reveal"]
rv = []
for i in range(110):
    t, b0 = rs.choice(TIPS); p_ = b0.lerp(t, rs.uniform(0.3, 1.0)) + Vector((rs.uniform(-0.0009, 0.0009), rs.uniform(-0.0005, 0.0005), rs.uniform(-0.0009, 0.0009)))
    o = sphere(f"rspk{i}", rs.uniform(0.00018, 0.0004), tuple(p_), speck_m, sub=1, parent=megb)
    U.pop(o, F_REVEAL + 2 + int(rs.uniform(0, 24)), 5); rv.append(o)
for o in rv: vis(o, [S["reveal"]], recursive=False)
MEGR = rng("morning", "face", "reveal", "lid")
for o in mmeshes: vis(o, MEGR, recursive=False)
vis(megb, rng("morning", "face", "reveal"))
vis(hero, [(1, S["morning"][0] - 1), (S["lid"][0], END)])
for o in hero_drops: vis(o, rng("cup", "land", "cap", "trap"), recursive=False)
for o in fog_drops: vis(o, [S["trap"]], recursive=False)

# ======================================================================
# 4) AEROZOL BULUTI: ~2600 zarracha (handler bilan har kadr hisoblanadi) + hajmli "tuman" sharlari
# ======================================================================
NP_ = 4200
rp = np.random.default_rng(11)
t0 = F_BURST + rp.uniform(0, 12, NP_)
Hm = 1.85 * rp.random(NP_) ** 0.55
ang_ = rp.uniform(0, 2 * np.pi, NP_); r0 = 0.11 * np.sqrt(rp.random(NP_)); wid = rp.uniform(0.15, 0.55, NP_)
tgt = np.stack([rp.uniform(X0 + 0.15, X1 - 0.15, NP_), rp.uniform(Y0 + 0.15, Y1 - 0.15, NP_), rp.uniform(0.25, 2.45, NP_)], 1)
dl = rp.uniform(0, 30, NP_)
ph = rp.uniform(0, 2 * np.pi, (NP_, 3)); om = rp.uniform(0.02, 0.06, (NP_, 3))
sub = rp.random(NP_) < 0.14
ctg = np.array(HEADW)[None, :] + np.stack([rp.normal(0, 0.03, NP_), rp.normal(0, 0.03, NP_), rp.normal(0.0, 0.025, NP_)], 1)
prad = rp.uniform(0.0016, 0.0048, NP_)
def _ease(u): u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)
def aero_pos(f):
    u = np.clip((f - t0) / (F_TOP - t0), 0, 1)
    h = Hm * (1 - (1 - u) ** 3)
    rr = r0 + wid * (h / 1.85) ** 0.8 * (0.4 + 0.6 * u)
    p = np.stack([WATER.x + np.cos(ang_) * rr, WATER.y + np.sin(ang_) * rr * 0.8, WATER.z + h], 1)
    w = _ease((f - F_SP - dl) / 85.0)[:, None]
    p = p * (1 - w) + tgt * w
    sink_ = 0.18 * _ease((f - S["hours"][0]) / 70.0)
    p[:, 2] -= sink_ * (p[:, 2] > 0.4)
    amp = 0.012 + 0.05 * _ease((f - F_TOP + 30) / 60.0)
    p += amp * np.sin(om * f + ph)
    w2 = (_ease((f - F_DR - dl * 0.8) / 60.0) * sub)[:, None]
    p = p * (1 - w2) + ctg * w2
    vis_ = (f >= t0).astype(float)
    return p, vis_
aero_me = bpy.data.meshes.new("aero"); aero_me.from_pydata([(0, 0, 0)] * NP_, [], []); aero_me.update()
aero_me.attributes.new("pr", "FLOAT", "POINT")
aero = bpy.data.objects.new("aero", aero_me); sc.collection.objects.link(aero)
aero_m = mat("aero_m", (0.3, 0.6, 0.15), 0.4, emit=2.5, emit_col=(0.35, 1.0, 0.2), trans=0.6)
ng = bpy.data.node_groups.new("inst", "GeometryNodeTree"); I = ng.interface
I.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"); I.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
Nn = ng.nodes; Ln = ng.links; gi = Nn.new("NodeGroupInput"); go = Nn.new("NodeGroupOutput")
ico = Nn.new("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = 1.0; ico.inputs["Subdivisions"].default_value = 2
ss = Nn.new("GeometryNodeSetShadeSmooth"); Ln.new(ico.outputs["Mesh"], ss.inputs["Geometry"])
sm_ = Nn.new("GeometryNodeSetMaterial"); sm_.inputs["Material"].default_value = aero_m; Ln.new(ss.outputs[0], sm_.inputs["Geometry"])
na = Nn.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"; na.inputs["Name"].default_value = "pr"
iop = Nn.new("GeometryNodeInstanceOnPoints"); Ln.new(gi.outputs[0], iop.inputs["Points"]); Ln.new(sm_.outputs[0], iop.inputs["Instance"])
Ln.new(na.outputs["Attribute"], iop.inputs["Scale"]); Ln.new(iop.outputs["Instances"], go.inputs[0])
md = aero.modifiers.new("inst", "NODES"); md.node_group = ng
# hajmli tuman sharlari (zarrachalar bilan birga harakatlanadi)
NPUFF = 26
puff_idx = rp.choice(np.where(Hm > 0.5)[0], NPUFF, replace=False)
puff_m = bpy.data.materials.new("puff_m"); puff_m.use_nodes = True; N = puff_m.node_tree.nodes; L = puff_m.node_tree.links
N.remove(N["Principled BSDF"]); pv = N.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.0; pv.inputs["Emission Color"].default_value = (0.3, 1.0, 0.25, 1)
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 4
L.new(tc.outputs["Object"], nz.inputs["Vector"])
dist = P.math_n(N, L, "LENGTH", tc.outputs["Object"], None, vec=True)
fall_ = P.math_n(N, L, "SUBTRACT", 1.0, dist, clamp=True)
pstr = value_node(puff_m, "ps", 1.6)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", fall_, fall_), nz.outputs["Fac"]), pstr), pv.inputs["Emission Strength"])
L.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
puffs = []
for j in range(NPUFF):
    o = sphere(f"puff{j}", 1.0, (0, 0, 0), puff_m, sub=2); puffs.append(o)
AERO_R = rng("burst", "height", "spread", "hours", "drift")
_last = [None]
def _aero(scene, *a):
    f = scene.frame_current + scene.frame_subframe
    if _last[0] == f: return
    _last[0] = f
    p, v = aero_pos(f)
    aero_me.vertices.foreach_set("co", p.ravel().astype(np.float32))
    aero_me.attributes["pr"].data.foreach_set("value", (prad * v).astype(np.float32))
    aero_me.update()
    grow = 0.12 + 0.38 * float(_ease(np.array((f - F_BURST) / 140.0)))
    for j, o in enumerate(puffs):
        i = puff_idx[j]; o.location = tuple(p[i]); s_ = grow * v[i] * (0.8 + 0.4 * (j % 3) / 2)
        o.scale = (s_, s_, s_ * 1.2)
bpy.app.handlers.frame_change_pre.append(_aero)
vis(aero, AERO_R)
for o in puffs: vis(o, AERO_R, recursive=False)
aero.cycles.use_motion_blur = False
for o in puffs: o.cycles.use_motion_blur = False

# "2 M" chizg'ichi (unitaz yonida) va "x M" masofa chizig'i
yel = mat("yel", (1.0, 0.75, 0.05), 0.4, emit=1.6, emit_col=(1.0, 0.7, 0.05))
red = mat("red", (1.0, 0.08, 0.04), 0.4, emit=1.8, emit_col=(1.0, 0.1, 0.04))
RUL = WATER + V(0.42, -0.25, 0); RUL.z = 0
ruler = empty("ruler", tuple(RUL))
cyl("rul_bar", 0.008, 2.0, (0, 0, 1.0), yel, parent=ruler, verts=12)
for k in range(11):
    box(f"rul_t{k}", (0.07 if k % 5 == 0 else 0.04, 0.012, 0.01), (0.0, 0, k * 0.2), yel, parent=ruler)
rtxt = text("rul_txt", "2 M", 0.3, (0.0, 0, 2.2), (90, 0, 0), yel, parent=ruler, extrude=0.01)
HT0, HT1 = S["height"]
ruler.scale = (1, 1, 0.001); ruler.keyframe_insert("scale", frame=HT0)
ruler.scale = (1, 1, 1.0); ruler.keyframe_insert("scale", frame=F_TOP - 4)
interp(ruler, "LINEAR", "scale")
rtxt.scale = (0.001,) * 3; rtxt.keyframe_insert("scale", frame=F_TOP - 5)
rtxt.scale = (1.3,) * 3; rtxt.keyframe_insert("scale", frame=F_TOP); rtxt.scale = (1.0,) * 3; rtxt.keyframe_insert("scale", frame=F_TOP + 4)
vis(ruler, [S["height"]])
CUPW = V(CUPXY.x, CUPXY.y, CTOP + 0.1)
dline = empty("dline", (0, 0, 0))
a_, b_ = V(WATER.x, WATER.y, RIM + 0.05), CUPW
nseg = 16
for k in range(nseg):
    if k % 2: continue
    p0 = a_.lerp(b_, k / nseg); p1 = a_.lerp(b_, (k + 1) / nseg); d_ = p1 - p0
    o = cyl(f"dl{k}", 0.012, d_.length, tuple((p0 + p1) / 2), red, parent=dline, verts=12)
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d_).to_euler()
DIST = (b_ - a_).length
dtx = text("dist_txt", f"{DIST:.1f} M", 0.17, tuple((a_ + b_) / 2 + V(0, 0, 0.16)), (0, 0, 0), red, parent=dline, extrude=0.01)
RM0, RM1 = S["room"]
for k, o in enumerate(c for c in dline.children if c.name.startswith("dl")):
    U.pop(o, RM0 + 3 + k, 4)
U.pop(dtx, RM0 + 14, 6)
vis(dline, [S["room"]])
print("dist toilet->cup", round(DIST, 2))

# ======================================================================
# 5) MIKRO TOMCHILAR (havodagi suv tomchilari ichida ichak bakteriyalari)
# ======================================================================
DW = V(0.0, -80.0, 0.0)
bk = U.BKit()
gut_m = U.bact_material("bact_gut", (0.55, 0.42, 0.12), (0.75, 0.6, 0.2), 0.06)
bk.rod.materials[0] = bk.m_rod
drop_m = bpy.data.materials.new("drop_ghost"); drop_m.use_nodes = True; N = drop_m.node_tree.nodes; L = drop_m.node_tree.links
N.remove(N["Principled BSDF"])
gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03; tr = N.new("ShaderNodeBsdfTransparent")
tr.inputs["Color"].default_value = (0.9, 0.97, 1.0, 1)
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
mx = N.new("ShaderNodeMixShader"); L.new(lw.outputs["Fresnel"], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.45, 0.8, 1.0, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 3.0), 0.9), em.inputs["Strength"])
ad = N.new("ShaderNodeAddShader"); L.new(mx.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
D0, D1 = S["drops"]
drop_world = empty("dropW", tuple(DW)); rdw = random.Random(17)
for i in range(80):
    c = V(rdw.uniform(-3.5, 3.5), rdw.uniform(-4, 22), rdw.uniform(-2.6, 2.6))
    if abs(c.x) < 0.9 and abs(c.z) < 0.7: c.x += 1.8 * (1 if c.x >= 0 else -1)
    r_ = rdw.uniform(0.35, 1.1)
    de = empty(f"dE{i}", tuple(c), drop_world)
    sphere(f"drop{i}", r_, (0, 0, 0), drop_m, scale=(1, 1, rdw.uniform(0.9, 1.05)), sub=4, parent=de)
    for k in range(rdw.randint(2, 6)):
        kd = rdw.choice(("rod", "rod", "coc", "acne"))
        o = bk.new(f"db{i}_{k}", kd, de); s_ = r_ * rdw.uniform(1.4, 2.4)
        o.scale = (s_,) * 3; d_ = r_ * 0.55 * rdw.random() ** 0.5
        a1, a2 = rdw.uniform(0, 6.28), rdw.uniform(-1.2, 1.2)
        o.location = (math.cos(a1) * math.cos(a2) * d_, math.sin(a1) * math.cos(a2) * d_, math.sin(a2) * d_)
        o.rotation_euler = (rdw.uniform(0, 6.28), rdw.uniform(0, 6.28), rdw.uniform(0, 6.28))
        if kd == "rod": o.data = bk.rod
    key(de, D0 - 2, loc=tuple(c), rot=(0, 0, 0)); key(de, D1 + 2, loc=tuple(c + V(rdw.uniform(-0.3, 0.3), rdw.uniform(-0.2, 0.2), rdw.uniform(0.4, 0.9))), rot=(rdw.uniform(-40, 40), rdw.uniform(-40, 40), rdw.uniform(-60, 60)))
    interp(de, "LINEAR")
vis(drop_world, [S["drops"]])

# ======================================================================
# 6) MIKRO TUKLAR (1 tuk ~ 1 m): nam tuklar o'rmoni, suv tomchilari, bakteriyalar ko'payadi
# ======================================================================
MW = V(80.0, 0.0, 0.0)
mw = empty("microW", tuple(MW))
fib_m = mat("fiber", (0.9, 0.94, 0.97), 0.25, trans=0.35, sss=0.3, coat=0.8)
fib_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.2
fib_b = mat("fiber_b", (0.3, 0.65, 0.95), 0.25, trans=0.35, sss=0.3, coat=0.8)
fib_b.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.2
for m in (fib_m, fib_b):
    Nf = m.node_tree.nodes; Lf = m.node_tree.links; tcf = Nf.new("ShaderNodeTexCoord"); wvf = Nf.new("ShaderNodeTexWave")
    wvf.wave_type = "BANDS"; wvf.bands_direction = "Z"; wvf.inputs["Scale"].default_value = 1.2; wvf.inputs["Distortion"].default_value = 4
    Lf.new(tcf.outputs["Object"], wvf.inputs["Vector"]); bpf = Nf.new("ShaderNodeBump"); bpf.inputs["Strength"].default_value = 0.08
    Lf.new(wvf.outputs["Fac"], bpf.inputs["Height"]); Lf.new(bpf.outputs[0], Nf["Principled BSDF"].inputs["Normal"])
rm = random.Random(8); fibers = []
FR_ = 0.5
tufts = [(-4.2, -1.5), (0.0, 0.0), (4.3, 1.2), (-2.0, 4.6), (2.6, 5.4), (-6.0, 3.8), (6.4, -3.0), (-1.2, -5.2), (3.0, -4.6)]
fib_pts = []
for ti, (tx, ty) in enumerate(tufts):
    for k in range(70):
        a = rm.uniform(0, 6.28); d = 2.4 * math.sqrt(rm.random())
        x, y = tx + math.cos(a) * d, ty + math.sin(a) * d
        if any((x - px) ** 2 + (y - py) ** 2 < (2 * FR_ + 0.08) ** 2 for px, py, _ in fib_pts): continue
        top = rm.uniform(-0.6, 0.6) + (0.8 if ti % 3 == 0 else 0.0)
        fib_pts.append((x, y, top))
for i, (x, y, top) in enumerate(fib_pts):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=FR_); o = bpy.context.object
    for v in o.data.vertices:
        if v.co.z < 0: v.co.z = v.co.z - 14.0
    o.name = f"fib{i}"; o.location = tuple(MW + V(x, y, top)); smooth(o); o.data.materials.append(fib_b if i % 4 == 0 else fib_m)
    o.rotation_euler = (R(rm.uniform(-4, 4)), R(rm.uniform(-4, 4)), 0); o.parent = None
    fibers.append(o)
print("fibers", len(fibers))
# suv tomchilari tuklar orasida
big_water = mat("bigwater", (0.85, 0.95, 1.0), 0.01, trans=1.0, ior=1.333)
mdrops = []
for i in range(40):
    x, y, top = rm.choice(fib_pts); a = rm.uniform(0, 6.28)
    p_ = MW + V(x + math.cos(a) * (FR_ + 0.15), y + math.sin(a) * (FR_ + 0.15), top - rm.uniform(0.5, 5.0))
    r_ = rm.uniform(0.25, 0.75)
    mdrops.append(sphere(f"mdrop{i}", r_, tuple(p_), big_water, scale=(1, 1, 1.25), sub=4))
# bakteriyalar tuk sirtida
def on_fiber(x, y, top, zoff, a, lift=0.06):
    n = V(math.cos(a), math.sin(a), 0)
    return MW + V(x, y, top) + n * (FR_ + lift) + V(0, 0, zoff), n
mbact = []; born = []
for i in range(560):
    x, y, top = rm.choice(fib_pts); a = rm.uniform(0, 6.28); zoff = -rm.uniform(0.0, 6.0) ** 1.3 * 0.6
    if rm.random() < 0.2:                       # uchida
        p_ = MW + V(x, y, top) + V(math.cos(a), math.sin(a), 0) * rm.uniform(0, 0.3) + V(0, 0, FR_ * 0.95 + 0.06); n = V(0, 0, 1)
    else:
        p_, n = on_fiber(x, y, top, zoff, a)
    kd = rm.choice(("rod", "rod", "coc", "acne")); o = bk.new(f"mb{i}", kd, None); s_ = rm.uniform(1.3, 2.0)
    o.scale = (s_,) * 3; o.location = tuple(p_)
    up = V(0, 0, 1) if n.z < 0.5 else V(1, 0, 0)
    Y_ = n.cross(up).normalized(); Y_ = (Quaternion(n, rm.uniform(-1.2, 1.2)) @ Y_); Z_ = n; X_ = Y_.cross(Z_)
    o.rotation_euler = Matrix((X_, Y_, Z_)).transposed().to_euler(); mbact.append(o); born.append((p_, n, X_, Y_))
# fekal zarralar (qo'ng'ir-yashil to'dalar) tuklarga yopishgan
fec_m = mat("fecal", (0.32, 0.24, 0.08), 0.6, emit=0.4, emit_col=(0.4, 0.8, 0.1))
for i in range(30):
    x, y, top = rm.choice(fib_pts); a = rm.uniform(0, 6.28); p_, n = on_fiber(x, y, top, -rm.uniform(0, 4), a, 0.1)
    o = sphere(f"fec{i}", rm.uniform(0.12, 0.3), tuple(p_), fec_m, scale=(1, rm.uniform(0.6, 1.0), rm.uniform(0.6, 1.0)), sub=3)
    dsp = o.modifiers.new("d", "DISPLACE"); tx_ = bpy.data.textures.new(f"fx{i}", "CLOUDS"); tx_.noise_scale = 0.08; dsp.texture = tx_; dsp.strength = 0.08
    mbact.append(o)
# ko'payish: mavjud bakteriyalar yonida yangilari paydo bo'ladi (eksponensial vaqt)
BR0, BR1 = S["breed"]
HOT = min(fib_pts, key=lambda q: (q[0] + 1.6) ** 2 + (q[1] + 2.6) ** 2)
HOTD = (V(-3.6, -5.2, 0) - V(HOT[0], HOT[1], 0)).normalized()
hot_born = []
for i in range(90):                                  # "issiq" tuk: kamera tomondagi sirtda to'da
    a = rm.uniform(0, 6.28); el = rm.uniform(0.25, 1.45)
    n = V(math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el))
    p_ = MW + V(HOT[0], HOT[1], HOT[2]) + n * (FR_ + 0.06)
    Y_ = n.cross(V(0, 0, 1)).normalized(); Y_ = Quaternion(n, rm.uniform(-1.2, 1.2)) @ Y_; X_ = Y_.cross(n)
    if i < 30:
        kd = rm.choice(("rod", "coc", "acne")); o = bk.new(f"hb{i}", kd, None); s_ = rm.uniform(1.3, 2.0)
        o.scale = (s_,) * 3; o.location = tuple(p_); o.rotation_euler = Matrix((X_, Y_, n)).transposed().to_euler(); mbact.append(o)
    hot_born.append((p_, n, X_, Y_))
newb = []
for i in range(620):
    p_, n, X_, Y_ = rm.choice(hot_born) if i % 5 < 3 else rm.choice(born)
    q = p_ + Y_ * rm.choice((-1, 1)) * rm.uniform(0.35, 0.7) + X_ * rm.uniform(-0.3, 0.3)
    kd = rm.choice(("rod", "rod", "coc", "acne")); o = bk.new(f"nb{i}", kd, None); s_ = rm.uniform(1.3, 2.0)
    o.scale = (s_,) * 3; o.location = tuple(q)
    o.rotation_euler = Matrix((X_, Y_, n)).transposed().to_euler(); o.rotation_euler.z += rm.uniform(-0.5, 0.5)
    U.pop(o, BR0 - 4 + int((BR1 - BR0) * (i / 620) ** 0.5), 4); newb.append(o)
MIC_R = rng("micro", "breed")
for o in fibers + mdrops + mbact: vis(o, MIC_R, recursive=False)
for o in newb: vis(o, MIC_R, recursive=False)

# ======================================================================
# 7) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.005, focus=None):
    t = empty(name + "_t"); path(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=focus or t, clip=clip); path(c, pts)
    return c
TOIF = TOIL + V(0, -0.35, 0.45)
# 1 ILGAK: poldan past burchak, unitaz va lavabo orasiga tez push-in
c = abs_cam("hook", [(1, V(0.05, -1.3, 0.1)), (18, V(0.0, -0.95, 0.16)), (27, V(-0.02, -0.75, 0.2))],
            [(1, V(-0.05, 1.2, 0.62)), (27, V(-0.08, 1.2, 0.58))], 12, 5.6)
lens_keys(c, [(1, 11), (18, 12), (27, 15)]); shake(c, 16, 27, 0.01, seed=1)
# 2 tepadan aylanma: unitaz <-> stakan masofasi
MIDR = (a_ + b_) / 2
c = orbit_cam("room", RM0, RM1, MIDR + V(0, -0.6, 0), 0.25, 0.15, -100, -60, 2.5 - MIDR.z, 2.42 - MIDR.z, 11, empty("roomT", tuple(MIDR + V(0, 0.1, -0.6))), fstop=8.0)
# 3 stakan: makro yonlama siljish, fonda xira unitaz
CU0, CU1 = S["cup"]
CC = V(CUPXY.x, CUPXY.y, CTOP + 0.16)
c = abs_cam("cup", [(CU0, HEADW + V(0.3, -0.32, -0.04)), (CU1, HEADW + V(0.08, -0.36, -0.01))],
            [(CU0, HEADW + V(-0.03, 0, -0.05)), (CU1, HEADW + V(-0.04, 0, -0.04))], 45, 2.8, focus=empty("cupF", tuple(HEADW)))
# 4 ertalab: past burchak, Megan lavabo oldida
MO0, MO1 = S["morning"]
MF = BRS + V(0, 0, 1.45)
c = abs_cam("morning", [(MO0, BRS + V(0.75, -0.05, 0.85)), (MO1, BRS + V(0.62, 0.1, 0.95))],
            [(MO0, MF + V(0.0, 0.05, -0.2)), (MO1, MF + V(0.0, 0.05, -0.12))], 16, 4.0)
# 5 yuzga yaqin: DOF
FA0, FA1 = S["face"]
faceT = empty("faceT", tuple(MOUTH_IN + V(0, 0.03, 0)), headE)
c = shot_cam("face", (0, 0, 0), faceT, 50, 2.0, focus=faceT, clip=0.01)
fr_ = wpos(faceT, FA0)
path(c, [(FA0, fr_ + V(0.42, -0.32, -0.02)), (FA1, fr_ + V(0.3, -0.24, -0.0))])
# 6 reveal: cho'tka boshiga crash zoom (UV)
brT = empty("brT", tuple(HEADC + V(0, -0.004, 0)), megb)
c = shot_cam("reveal", (0, 0, 0), brT, 40, 5.6, focus=brT, clip=0.002)
rp0 = wpos(brT, R0)
path(c, [(R0, rp0 + V(0.25, -0.2, 0.03)), (F_REVEAL + 4, rp0 + V(0.06, -0.05, 0.01)), (R1, rp0 + V(0.045, -0.035, 0.012))])
lens_keys(c, [(R0, 35), (F_REVEAL + 4, 60), (R1, 70)]); shake(c, F_REVEAL + 3, F_REVEAL + 16, 0.003, seed=6)
# 7 unitaz qopqog'i: past burchak keng
c = abs_cam("lid", [(LID0, TOIF + V(0.75, -0.75, 0.35)), (LID1, TOIF + V(0.55, -0.6, 0.25))],
            [(LID0, TOIF + V(0.05, 0.3, 0.1)), (LID1, TOIF + V(0.05, 0.25, 0.05))], 16, 4.0)
# 8 girdob: tepadan, aylanuvchi
VO0, VO1 = S["vortex"]
c = shot_cam("vortex", (0, 0, 0), empty("vortT", tuple(WATER + V(0, 0, -0.03))), 24, 5.6, clip=0.01)
for f_ in range(VO0, VO1 + 1, 2):
    t = (f_ - VO0) / (VO1 - VO0); a = R(-90 + 70 * t); r_ = 0.12 - 0.05 * t
    key(c, f_, loc=tuple(WATER + V(math.cos(a) * r_, math.sin(a) * r_ - 0.02, 0.52 - 0.12 * t)))
c.constraints[0].up_axis = "UP_Y"
# 9 portlash: unitaz chetidan, silkinish
BU0, BU1 = S["burst"]
c = abs_cam("burst", [(BU0, WATER + V(0.5, -0.75, 0.25)), (F_BURST - 1, WATER + V(0.45, -0.68, 0.25)), (BU1, WATER + V(0.75, -1.1, 0.35))],
            [(BU0, WATER + V(0, 0, 0.18)), (F_BURST, WATER + V(0, 0, 0.3)), (BU1, WATER + V(0, 0, 0.75))], 16, 5.6)
shake(c, F_BURST, F_BURST + 18, 0.025, seed=9)
# 10 mikro tomchilar: uchib o'tish
c = abs_cam("drops", [(D0, DW + V(0.0, -6.0, 0.2)), (D1, DW + V(0.3, 12.0, -0.1))], [(D0, DW + V(0.0, 2.0, 0.0)), (D1, DW + V(0.5, 22.0, 0.3))], 22, 2.8, clip=0.05)
c.data.dof.focus_object = None; c.data.dof.focus_distance = 3.0
# 11 balandlik: yondan keng plan, pastdan tepaga
c = abs_cam("height", [(HT0, WATER + V(1.6, -1.55, 0.15)), (HT1, WATER + V(1.5, -1.65, 0.45))],
            [(HT0, WATER + V(0.1, 0.0, 0.7)), (HT1, WATER + V(0.1, 0.0, 1.2))], 14, 8.0)
# 12 tarqalish: tepadan keng, aylanma
SP0, SP1 = S["spread"]
c = orbit_cam("spread", SP0, SP1, V(0, 0, 0), 0.6, 0.5, -120, -60, 2.45, 2.4, 12, empty("sprT", (0, 0.2, 0.6)), fstop=11.0)
# 13 ikki soat: sekin aylanma, soat ko'rinadi
c = abs_cam("hours", [(H0_, V(-1.1, -1.05, 1.0)), (H1_, V(-1.15, -0.6, 1.15))], [(H0_, V(0.6, 0.0, 1.5)), (H1_, V(0.7, -0.2, 1.6))], 16, 8.0)
# 14 suzish: lavabo/oyna tomon ergashish
DR0, DR1 = S["drift"]
c = abs_cam("drift", [(DR0, CC + V(-0.9, -1.1, 0.35)), (DR1, CC + V(-0.25, -0.5, 0.12))], [(DR0, CC + V(-0.1, 0.1, 0.1)), (DR1, CC + V(0, 0, 0.0))], 24, 4.0)
# 15 qo'nish: makro, sekin push-in
HD = HEADW
hx = (HM_.to_3x3() @ V(1, 0, 0)).normalized(); hy = (HM_.to_3x3() @ V(0, -1, 0)).normalized(); hz = (HM_.to_3x3() @ V(0, 0, 1)).normalized()
c = abs_cam("land", [(L0, HD + hy * 0.075 + hx * 0.03 + hz * 0.02), (L1, HD + hy * 0.05 + hx * 0.018 + hz * 0.012)],
            [(L0, HD + hy * 0.004), (L1, HD + hy * 0.006)], 60, 8.0, clip=0.002)
# 16 mikro tuklar: o'rmon ichida siljish
MI0, MI1 = S["micro"]
c = abs_cam("micro", [(MI0, MW + V(-7.5, -7.0, 1.6)), (MI1, MW + V(-3.6, -5.2, 0.6))], [(MI0, MW + V(0, 0, -1.2)), (MI1, MW + V(0.5, 0.5, -1.0))], 20, 4.0, clip=0.05)
# 17 ko'payish: crash zoom
bc = born[0][0] if born else MW
BCN = MW + V(0, 0, 0.9)
HP_ = MW + V(HOT[0], HOT[1], HOT[2] + 0.2)
c = abs_cam("breed", [(BR0, MW + V(-3.6, -5.2, 2.2)), (BR0 + 5, HP_ + HOTD * 1.6 + V(0, 0, 2.4)), (BR1, HP_ + HOTD * 1.3 + V(0, 0, 2.0))], [(BR0, MW + V(0.5, 0.5, -1.0)), (BR0 + 5, HP_), (BR1, HP_ + V(0, 0, 0.05))], 20, 5.6, clip=0.05)
lens_keys(c, [(BR0, 20), (BR0 + 5, 32), (BR1, 35)]); shake(c, BR0 + 4, BR0 + 16, 0.08, seed=17)
# 18 qopqoq: makro yonlama, past burchak
c = abs_cam("cap", [(C0, HD + hx * 0.09 + hy * 0.05 - hz * 0.02), (C1, HD + hx * 0.06 + hy * 0.07 + hz * 0.0)],
            [(C0, HD + hz * 0.02), (C1, HD + hz * 0.006)], 45, 8.0, clip=0.002)
# 19 rentgen: push-in, oxirida silkinish
c = abs_cam("trap", [(T0, HD + hy * 0.1 + hx * 0.045 + hz * 0.01), (T1 - 12, HD + hy * 0.075 + hx * 0.03), (T1, HD + hy * 0.08 + hx * 0.032)],
            [(T0, HD + hz * 0.004), (T1, HD + hy * 0.003)], 45, 8.0, clip=0.002)
shake(c, T0, T0 + 12, 0.002, seed=19); shake(c, T1 - 12, T1, 0.0015, seed=20)
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        if fc.data_path == "location":
            for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
for f_, n in SHOTS:
    sc.timeline_markers.new(n, frame=f_).camera = CAMS[n]
sc.camera = CAMS["hook"]
ov_m = mat("ov_txt", (1, 1, 1), 0.5, emit=4.0)
hrs = text("hours_txt", "2 SOAT", 0.045, (0, 0.085, -0.4), (0, 0, 0), ov_m, parent=CAMS["hours"]); vis(hrs, [S["hours"]])

# ======================================================================
# 8) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
bg_env = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_env.inputs[0])
bg_col = N.new("ShaderNodeBackground")
a1 = N.new("ShaderNodeAddShader"); L.new(bg_env.outputs[0], a1.inputs[0]); L.new(bg_col.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WORLD = {"bath": (1.0, (0, 0, 0), 0.0), "drops": (0.0, (0.008, 0.025, 0.045), 1.0), "micro": (0.0, (0.01, 0.02, 0.045), 1.0)}
for f_, n in SHOTS:
    es, col, cs = WORLD["drops" if n == "drops" else "micro" if n in ("micro", "breed") else "bath"]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f_)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f_)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f_)
interp(w.node_tree, "CONSTANT")
BATHS = rng("hook", "room", "cup", "morning", "face", "reveal", "lid", "vortex", "burst", "height", "spread", "hours", "drift", "land", "cap", "trap")
for o in bath: vis(o, BATHS)
mm = bpy.data.objects["mirror_light"]
RT = empty("roomT0", (0.0, 0.6, 0.9))
area("ceil_key", (0.0, 0.3, HZ - 0.05), 1.2, (1.0, 0.96, 0.9), lights_for(BATHS, 160.0), target=empty("ckT", (0, 0.3, 0)))
area("win_sun", tuple(WCn + V(-0.6, 0, 0.3)), 1.2, (1.0, 0.85, 0.65), lights_for(BATHS, 450.0), target=empty("wsT", (0.4, 0.6, 0.5)))
area("mirror_fill", tuple(MIR + V(0, -0.25, 0.55)), 0.9, (1.0, 0.95, 0.88), lights_for(BATHS, 60.0), target=empty("mfT", tuple(BRS + V(0, 0.2, 1.4))))
area("toil_rim", tuple(TOIL + V(0.8, -0.2, 1.6)), 0.6, (0.6, 0.8, 1.0), lights_for(BATHS, 40.0), target=empty("trT", tuple(WATER)))
area("cup_key", tuple(CC + V(-0.25, -0.35, 0.3)), 0.25, (1.0, 0.95, 0.9), lights_for(rng("cup", "land", "cap", "trap", "reveal"), 14.0), target=empty("cpT", tuple(HEADW)))
area("cup_rim", tuple(CC + V(0.3, 0.12, 0.2)), 0.2, (0.5, 0.75, 1.0), lights_for(rng("cup", "land", "cap", "trap"), 10.0), target=bpy.data.objects["cpT"])
area("face_key", (0, 0, 0), 0.3, (1.0, 0.92, 0.85), lights_for(rng("face", "reveal"), 18.0), target=faceT)
bpy.data.objects["face_key"].location = tuple(wpos(faceT, FA0) + V(0.35, -0.35, 0.25))
point("bowl_glow", tuple(WATER + V(0, 0, 0.08)), 0.05, (0.35, 1.0, 0.25), [(1, 0), (F_BURST - 2, 0), (F_BURST, 8.0), (F_BURST + 30, 3.0), (S["burst"][1] + 1, 0)], const=False)
# mikro tomchilar
DT = empty("dT", tuple(DW + V(0, 6, 0)))
area("D_key", tuple(DW + V(-4, 0, 5)), 6.0, (0.9, 0.95, 1.0), lights_for([S["drops"]], 900.0), target=DT)
area("D_rim", tuple(DW + V(5, 14, -2)), 6.0, (0.3, 0.7, 1.0), lights_for([S["drops"]], 1500.0), target=DT)
area("D_back", tuple(DW + V(0, 26, 0)), 8.0, (0.4, 0.9, 0.6), lights_for([S["drops"]], 600.0), target=DT)
# mikro tuklar
MT = empty("mT", tuple(MW + V(0, 0, -1)))
area("M_key", tuple(MW + V(-6, -6, 8)), 5.0, (0.95, 0.97, 1.0), lights_for(MIC_R, 1400.0), target=MT)
area("M_rim", tuple(MW + V(6, 7, 2)), 5.0, (0.3, 0.6, 1.0), lights_for(MIC_R, 1800.0), target=MT)
area("M_fill", tuple(MW + V(-8, 2, -2)), 5.0, (0.4, 0.9, 0.5), lights_for(MIC_R, 500.0), target=MT)

# ======================================================================
# 9) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 8
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = False
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("PROBE"): exec(open(os.environ["PROBE"]).read())
if os.environ.get("SAVE"): bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f_ in map(int, fs.split(",")):
            sc.frame_set(f_); r.filepath = f"{OUT}test_{f_:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
