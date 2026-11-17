# "Quvvatlanayotgan telefonda o'yin -> batareya portlashi" — Zack D. Films uslubida 43.6 s video (1047 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, ogri/ogri.py (yordamchilar: telefon/lib.py). Kadr rejasi: STORYBOARD.md.
# Assetlar: zack_test/tools/get_telefon.sh
# Render: OUT=/tmp/claude-0/frames_t/ SAMPLES=8 PCT=40 python3 -I zack_test/telefon/telefon.py --render
# Sinov: FRAMES=20,60,130 PCT=30   |   Bo'lak: RANGE=a,b
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *                      # sahnani tozalaydi
import numpy as np
from mathutils import Quaternion
random.seed(7)

END = 1047
sc.frame_start, sc.frame_end = 1, END
def T(sec): return int(round(sec * 24)) + 1

# ---------------- kadrlar (Whisper so'z vaqtlari) ----------------
SHOTS = [(1, "hook"), (T(2.4), "game"), (T(4.9), "face"), (T(6.8), "reactor"), (T(8.7), "xray"), (T(11.9), "ions"),
         (T(15.9), "thumbs"), (T(17.9), "cpu"), (T(20.4), "draw"), (T(25.1), "temp"), (T(28.0), "melt"), (T(29.9), "touch"),
         (T(32.7), "short"), (T(34.4), "swell"), (T(36.6), "bulge"), (T(38.8), "crack"), (T(40.7), "boom")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
def F0(n): return S[n][0]
def F1(n): return S[n][1]
ALL = [(1, END)]
F_PLUG = T(1.05)       # vilka portga kiradi ("ula")
F_XR = T(7.35)         # qo'ldagi telefon rentgenga o'tadi ("qizdirish")
F_SHORT = T(33.0)      # qisqa tutashuv ("qisqa")
F_CRACK = T(39.85)     # ekran yoriladi ("yorib")
F_BOOM = T(41.0)       # olov otilib chiqadi
ROOM_SHOTS = rng("hook", "game", "face", "reactor", "thumbs", "bulge", "crack", "boom")
PH_SHOTS = rng("xray", "cpu", "draw", "swell")            # rentgen studiya (S1)
CELL_SHOTS = rng("ions", "temp", "melt", "touch", "short")  # batareya qatlamlari (C0)
S1 = Vector((0.0, -60.0, 1.0)); C0 = Vector((0.0, -80.0, 0.0))

def kv(o, path, pairs, mode="LINEAR", data=False):
    tgt = o.data if data else o
    for f, v in pairs:
        setattr(tgt, path, v); tgt.keyframe_insert(path, frame=f)
    interp(tgt, mode, path)
def mkeys(m, name, pairs, mode="LINEAR"):
    for f, v in pairs: val_key(m, name, f, v)
    for fc in fcurves(m.node_tree):
        if name in fc.data_path:
            for k in fc.keyframe_points: k.interpolation = mode
def cyc_node(m, name, f0, v0, f1, v1):
    val_key(m, name, f0, v0); val_key(m, name, f1, v1)
    for fc in fcurves(m.node_tree):
        if name in fc.data_path:
            for k in fc.keyframe_points: k.interpolation = "LINEAR"
            fc.extrapolation = "LINEAR"

# issiqlik egri chiziqlari (batareya va protsessor)
HEAT = [(1, 0.05), (F_XR - 4, 0.08), (T(8.4), 0.45), (T(12.5), 0.3), (T(15.6), 0.55), (T(20.4), 0.6), (T(25.1), 0.72),
        (T(28.0), 0.95), (F_SHORT - 1, 1.05), (F_SHORT + 1, 2.6), (T(34.3), 1.7), (T(38.8), 1.9), (END, 2.2)]
CPUH = [(1, 0.1), (T(18.3), 0.15), (T(19.4), 1.0), (T(24.9), 1.15), (END, 1.2)]
TEMP = [(1, 36.0), (T(17.9), 38.0), (T(20.4), 47.0), (T(25.1), 60.0), (T(28.0), 90.0), (T(32.7), 118.0), (F_SHORT + 2, 160.0),
        (T(34.4), 190.0), (END, 400.0)]
def temp_at(f):
    for (a, va), (b, vb) in zip(TEMP, TEMP[1:]):
        if a <= f <= b: return va + (vb - va) * (f - a) / max(1, b - a)
    return TEMP[-1][1]

# ======================================================================
# 1) MATERIALLAR
# ======================================================================
plaster = pbr("plaster", "painted_plaster_wall", 0.6, tint=(0.78, 0.74, 0.7))
floor_m = pbr("laminate", "laminate_floor_02", 0.5)
trim = mat("trim", (0.92, 0.91, 0.88), 0.4)
ceil_m = mat("ceil", (0.88, 0.87, 0.85), 0.85)
white_pl = mat("socket", (0.9, 0.9, 0.88), 0.35)
black = mat("black", (0.012, 0.012, 0.014), 0.4)
alu = mat("alu", (0.16, 0.165, 0.18), 0.28, metal=1.0)
backglass = mat("backglass", (0.02, 0.025, 0.035), 0.12, coat=1.0)
steel = mat("steel", (0.8, 0.8, 0.82), 0.22, metal=1.0)
cable_m = mat("cable", (0.85, 0.85, 0.83), 0.45)
lens_m = mat("camlens", (0.0, 0.0, 0.0), 0.05, coat=1.0)
shade_m = mat("shade", (0.95, 0.85, 0.7), 0.8, emit=2.5, emit_col=(1.0, 0.7, 0.4))
studio_bg = mat("studio_bg", (0.004, 0.005, 0.008), 0.9)

def ramp_heat(N, L, val, scale=1 / 2.6):
    mr = P.math_n(N, L, "MULTIPLY", val, scale, clamp=True)
    cr = N.new("ShaderNodeValToRGB"); L.new(mr, cr.inputs[0]); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.35, 0.03, 0.005, 1); e[1].position = 1.0; e[1].color = (1.0, 0.85, 0.6, 1)
    m1 = e.new(0.35); m1.color = (1.0, 0.22, 0.02, 1)
    m2 = e.new(0.6); m2.color = (1.0, 0.5, 0.1, 1)
    return cr.outputs[0]

def heat_mat(name, base, rough=0.4, metal=0.0, k=4.0, xa=0.0, grains=0.0, grain_col=None, bump=0.0, rs=1 / 2.6):
    """oddiy sirt + issiqlik nuri (qiymat 'heat'); xa > 0: rentgen shaffofligi; grains: Voronoi donachalar"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; out = N["Material Output"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    h = value_node(m, "heat", 0.0)
    tc = N.new("ShaderNodeTexCoord")
    patt = None
    if grains:
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = grains
        L.new(tc.outputs["Object"], vo.inputs["Vector"])
        if grain_col:
            mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
            L.new(vo.outputs["Distance"], mx.inputs["Factor"]); mx.inputs[6].default_value = (*grain_col, 1); mx.inputs[7].default_value = (*base, 1)
            L.new(mx.outputs[2], b.inputs["Base Color"])
        patt = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, vo.outputs["Distance"], clamp=True), 2.0)
        if bump:
            bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(vo.outputs["Distance"], bp.inputs["Height"])
            L.new(bp.outputs[0], b.inputs["Normal"])
    em = N.new("ShaderNodeEmission"); L.new(ramp_heat(N, L, h, rs), em.inputs["Color"])
    s = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", h, 1.5), k)
    if patt is not None: s = P.math_n(N, L, "MULTIPLY", s, P.math_n(N, L, "ADD", 0.35, patt))
    L.new(s, em.inputs["Strength"])
    surf = b.outputs[0]
    if xa:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = xa
        L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); surf = mx.outputs[0]
    ad = N.new("ShaderNodeAddShader"); L.new(surf, ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs[0])
    return m
HEATMATS = []
def hm(*a, **k):
    m = heat_mat(*a, **k); HEATMATS.append(m); return m

bat_m = hm("battery", (0.13, 0.13, 0.14), 0.6, metal=0.2, k=1.1, xa=0.3, rs=1 / 3.6)
bat_real_m = hm("battery_real", (0.13, 0.13, 0.14), 0.6, metal=0.2, k=2.0)
cpu_m = heat_mat("cpu", (0.03, 0.03, 0.035), 0.3, k=5.0, rs=1 / 4.8)
pcb_m = mat("pcb", (0.02, 0.18, 0.12), 0.35, coat=0.4, alpha=0.75)
xshell = glow_mat("xshell", (0.25, 0.55, 1.0)); xshell.node_tree.nodes["a"].outputs[0].default_value = 1.4
xcable = glow_mat("xcable", (0.6, 0.85, 1.0)); xcable.node_tree.nodes["a"].outputs[0].default_value = 1.2
# batareya qatlamlari (kesim)
copper_c = hm("cell_cu", (0.9, 0.42, 0.22), 0.3, metal=1.0, k=0.7)
alfoil_c = hm("cell_al", (0.85, 0.86, 0.88), 0.3, metal=1.0, k=0.7)
anode_c = hm("cell_anode", (0.025, 0.025, 0.028), 0.55, k=1.3, grains=38, grain_col=(0.09, 0.09, 0.1), bump=0.6)
cathode_c = hm("cell_cathode", (0.07, 0.06, 0.08), 0.5, k=1.3, grains=34, grain_col=(0.32, 0.08, 0.06), bump=0.6)

def separator_mat():
    m = bpy.data.materials.new("separator"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; out = N["Material Output"]
    b.inputs["Base Color"].default_value = (0.92, 0.93, 0.95, 1); b.inputs["Roughness"].default_value = 0.6
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.01
    melt = value_node(m, "melt", 0.0)
    tc = N.new("ShaderNodeTexCoord"); no = N.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = 9.0; no.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], no.inputs["Vector"])
    # band: |x| kichik joyda tezroq eriydi (qatlamlar shu yerda tegadi)
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    ax = P.math_n(N, L, "ABSOLUTE", sx.outputs[0])
    band = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", ax, 0.35), clamp=True)
    field = P.math_n(N, L, "ADD", no.outputs["Fac"], P.math_n(N, L, "MULTIPLY", band, 0.45))
    thr = P.math_n(N, L, "SUBTRACT", 1.15, P.math_n(N, L, "MULTIPLY", melt, 0.75))
    d = P.math_n(N, L, "SUBTRACT", field, thr)                       # > 0: teshik
    hole = P.math_n(N, L, "GREATER_THAN", d, 0.0)
    edge = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", d), 0.06), clamp=True),
                    P.math_n(N, L, "GREATER_THAN", melt, 0.02))
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.35, 0.05, 1)
    L.new(P.math_n(N, L, "MULTIPLY", edge, 6.0), em.inputs["Strength"])
    ad = N.new("ShaderNodeAddShader"); L.new(b.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(hole, mx.inputs[0]); L.new(ad.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0])
    return m
sep_m = separator_mat()
ion_m = emit_mat("ion", (0.25, 0.75, 1.0), 6.0)
pulse_g = emit_mat("pulse_g", (0.3, 1.0, 0.35), 9.0)
pulse_y = emit_mat("pulse_y", (1.0, 0.8, 0.15), 9.0)
spark_m = emit_mat("spark", (1.0, 0.6, 0.25), 14.0)
arc_m = emit_mat("arc", (0.75, 0.9, 1.0), 9.0)
plus_m = emit_mat("plus", (1.0, 0.25, 0.15), 2.2)
minus_m = emit_mat("minus", (0.25, 0.55, 1.0), 2.2)
bubble_m = glow_mat("bubble", (0.9, 0.95, 1.0)); bubble_m.node_tree.nodes["a"].outputs[0].default_value = 1.5

# ---------------- ekran rasmlari (o'yin, chaqmoq) — numpy bilan chiziladi ----------------
GW, GH = 768, 352
def poly_mask(xs, ys, pts):
    m = np.zeros(xs.shape, bool); n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
        c = ((y1 > ys) != (y2 > ys)) & (xs < (x2 - x1) * (ys - y1) / (y2 - y1 + 1e-9) + x1)
        m ^= c
    return m
def game_image():
    yy, xx = np.mgrid[0:GH, 0:GW].astype(np.float32); v = yy / GH; u = xx / GW
    img = np.zeros((GH, GW, 4), np.float32); img[..., 3] = 1
    hor = 0.42
    sky = np.clip((v - hor) / (1 - hor), 0, 1)[..., None]
    img[..., :3] = (1 - sky) * np.array([1.0, 0.35, 0.25]) + sky * np.array([0.05, 0.02, 0.22])
    sun = ((u - 0.68) ** 2 * (GW / GH) ** 2 + (v - 0.55) ** 2) < 0.012
    img[sun, :3] = [1.0, 0.85, 0.25]
    for k, (amp, fr, ph, col) in enumerate(((0.12, 9, 0.3, (0.18, 0.05, 0.25)), (0.08, 17, 1.7, (0.09, 0.02, 0.15)))):
        mh = hor + amp * (0.6 + 0.4 * np.sin(u * fr + ph)) * (0.7 + 0.3 * np.sin(u * fr * 2.3 + ph))
        msk = (v > hor) & (v < mh); img[msk, :3] = col
    gnd = v <= hor
    img[gnd, :3] = [0.03, 0.02, 0.06]
    d = np.clip((hor - v) / hor, 1e-3, 1)
    # perspektiv neon chiziqlar
    for k in np.linspace(-1.2, 1.2, 9):
        x_at = 0.5 + k * d * 0.9
        ln = gnd & (np.abs(u - x_at) < 0.0025 + 0.004 * d)
        img[ln, :3] = [1.0, 0.1, 0.8]
    for z in range(1, 14):
        yz = hor * (1 - 1 / (1 + 0.35 * z * z))
        img[gnd & (np.abs(v - (hor - yz)) < 0.003 + 0.004 * yz), :3] = [0.9, 0.1, 0.75]
    # yo'l o'rtasidagi punktir
    dash = gnd & (np.abs(u - 0.5) < 0.006 + 0.02 * d) & (np.sin(1 / d * 4.0) > 0.2)
    img[dash, :3] = [1, 0.95, 0.6]
    # mashina (o'yinchi)
    car = (np.abs(u - 0.5) < 0.07) & (v > 0.08) & (v < 0.2)
    img[car, :3] = [0.95, 0.08, 0.1]
    img[(np.abs(u - 0.5) < 0.05) & (v > 0.18) & (v < 0.26), :3] = [0.85, 0.05, 0.08]
    img[(np.abs(u - 0.5) < 0.04) & (v > 0.19) & (v < 0.245), :3] = [0.4, 0.8, 1.0]
    for wx in (0.44, 0.56):
        img[((u - wx) ** 2 * 4 + (v - 0.085) ** 2 * 1.0) < 0.0009, :3] = [0.02, 0.02, 0.02]
    img[(np.abs(u - 0.455) < 0.012) & (v > 0.12) & (v < 0.15), :3] = [1, 0.9, 0.5]
    img[(np.abs(u - 0.545) < 0.012) & (v > 0.12) & (v < 0.15), :3] = [1, 0.9, 0.5]
    # raqiblar
    for (cx, cy, s_, col) in ((0.38, 0.3, 0.025, (0.1, 0.9, 1.0)), (0.6, 0.34, 0.016, (1.0, 0.85, 0.1))):
        img[(np.abs(u - cx) < s_) & (np.abs(v - cy) < s_ * 0.9), :3] = col
    # HUD: hayot, tezlik, joystiklar
    img[(u > 0.04) & (u < 0.28) & (v > 0.9) & (v < 0.94), :3] = [0.15, 0.15, 0.15]
    img[(u > 0.045) & (u < 0.22) & (v > 0.905) & (v < 0.935), :3] = [0.2, 1.0, 0.3]
    for cx in (0.12, 0.88):
        r2 = (u - cx) ** 2 * (GW / GH) ** 2 + (v - 0.2) ** 2
        img[(r2 < 0.018) & (r2 > 0.014), :3] = img[(r2 < 0.018) & (r2 > 0.014), :3] * 0.4 + 0.6
        img[r2 < 0.005, :3] = img[r2 < 0.005, :3] * 0.5 + 0.5
    # batareya belgisi (zaryadlanmoqda)
    img[(u > 0.9) & (u < 0.96) & (v > 0.9) & (v < 0.95), :3] = [0.9, 0.9, 0.9]
    img[(u > 0.905) & (u < 0.94) & (v > 0.907) & (v < 0.943), :3] = [0.2, 1.0, 0.3]
    img[..., :3] = np.clip(img[..., :3], 0, 1) ** 2.2
    return img
def bolt_image():
    yy, xx = np.mgrid[0:GH, 0:GW].astype(np.float32)
    x = (xx - GW / 2) / GH; y = (yy - GH / 2) / GH
    img = np.zeros((GH, GW, 4), np.float32)
    pts = [(0.06, 0.36), (-0.12, -0.02), (0.0, -0.02), (-0.06, -0.36), (0.13, 0.06), (0.01, 0.06), (0.08, 0.36)]
    m = poly_mask(x, y, pts)
    r = np.sqrt(x * x + y * y); ring = (r > 0.41) & (r < 0.44)
    img[m] = [0.25, 1.0, 0.35, 1]; img[ring] = [0.25, 1.0, 0.35, 1]
    return img
def to_image(name, arr):
    im = bpy.data.images.new(name, GW, GH, alpha=True, float_buffer=True)
    im.pixels.foreach_set(arr.ravel()); im.pack(); return im
IMG_GAME = to_image("game", game_image()); IMG_BOLT = to_image("bolt", bolt_image())

def screen_mat():
    m = bpy.data.materials.new("screen"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; out = N["Material Output"]
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1); b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 0.0; b.inputs["Specular IOR Level"].default_value = 0.06
    b.inputs["Roughness"].default_value = 0.35
    scr = value_node(m, "scr", 1.0); bolt = value_node(m, "bolt", 0.0); scroll = value_node(m, "scroll", 0.0); crack = value_node(m, "crack", 0.0)
    uv = N.new("ShaderNodeUVMap")
    sh = N.new("ShaderNodeVectorMath"); sh.operation = "ADD"; L.new(uv.outputs[0], sh.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(scroll, cmb.inputs[0]); L.new(cmb.outputs[0], sh.inputs[1])
    tg = N.new("ShaderNodeTexImage"); tg.image = IMG_GAME; tg.extension = "REPEAT"; L.new(sh.outputs[0], tg.inputs[0])
    tb = N.new("ShaderNodeTexImage"); tb.image = IMG_BOLT; tb.extension = "CLIP"; L.new(uv.outputs[0], tb.inputs[0])
    # o'yin + chaqmoq (chaqmoq paytida o'yin xiralashadi)
    dim = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", bolt, 0.85))
    gcol = P.math_n(N, L, "SCALE", tg.outputs[0], None, vec=True); L.new(dim, gcol.node.inputs["Scale"])
    bcol = P.math_n(N, L, "SCALE", tb.outputs[0], None, vec=True); L.new(P.math_n(N, L, "MULTIPLY", bolt, tb.outputs["Alpha"]), bcol.node.inputs["Scale"])
    col = P.math_n(N, L, "ADD", gcol, bcol, vec=True)
    # yoriqlar: Voronoi qirralari, yoriq markazidan radius = crack
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 90.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.feature = "DISTANCE_TO_EDGE"; vo2.inputs["Scale"].default_value = 260.0
    L.new(tc.outputs["Object"], vo2.inputs["Vector"])
    dist = P.math_n(N, L, "DISTANCE", tc.outputs["Object"], (0.025, -0.01, 0.0), vec=True)
    reach = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", dist, P.math_n(N, L, "MAXIMUM", P.math_n(N, L, "MULTIPLY", crack, 0.13), 1e-4)), clamp=True)
    line1 = P.math_n(N, L, "LESS_THAN", vo.outputs["Distance"], 0.03)
    line2 = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", vo2.outputs["Distance"], 0.025), P.math_n(N, L, "GREATER_THAN", reach, 0.6))
    cr = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MAXIMUM", line1, line2), P.math_n(N, L, "GREATER_THAN", reach, 0.0))
    # displey chegarasi (UV ichida)
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs[0], sx.inputs[0])
    inside = P.math_n(N, L, "MULTIPLY",
                      P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "GREATER_THAN", sx.outputs[0], 0.015), P.math_n(N, L, "LESS_THAN", sx.outputs[0], 0.985)),
                      P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "GREATER_THAN", sx.outputs[1], 0.03), P.math_n(N, L, "LESS_THAN", sx.outputs[1], 0.97)))
    stren = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", inside, scr), P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", cr, 0.7)))
    em = N.new("ShaderNodeEmission"); L.new(col, em.inputs["Color"]); L.new(P.math_n(N, L, "MULTIPLY", stren, 0.85), em.inputs["Strength"])
    # yoriq oq chiziq (sinig'an shisha)
    em2 = N.new("ShaderNodeEmission"); em2.inputs["Color"].default_value = (0.85, 0.9, 1.0, 1); L.new(P.math_n(N, L, "MULTIPLY", cr, 0.8), em2.inputs["Strength"])
    a1 = N.new("ShaderNodeAddShader"); L.new(b.outputs[0], a1.inputs[0]); L.new(em.outputs[0], a1.inputs[1])
    a2 = N.new("ShaderNodeAddShader"); L.new(a1.outputs[0], a2.inputs[0]); L.new(em2.outputs[0], a2.inputs[1])
    L.new(a2.outputs[0], out.inputs[0])
    return m
screen_m = screen_mat()

# ======================================================================
# 2) XONA: divan (0,0) -Y ga qaraydi; orqa devor y=0.85; deraza x=3 devorda; stol y=-1.15
# ======================================================================
H = 2.7; WT = 0.15
room = empty("room")
RX0, RX1, RY0, RY1 = -3.0, 3.0, -4.0, 0.85
WIN_Y, WIN_W, WIN_Z0, WIN_Z1 = -1.4, 1.4, 0.9, 2.2
def wall(name, size, loc): return box(name, size, loc, plaster, parent=room)
wall("w_back", (RX1 - RX0 + 0.3, WT, H), (0, RY1 + WT / 2, H / 2))
wall("w_front", (RX1 - RX0 + 0.3, WT, H), (0, RY0 - WT / 2, H / 2))
wall("w_left", (WT, RY1 - RY0, H), (RX0 - WT / 2, (RY0 + RY1) / 2, H / 2))
# o'ng devor deraza teshigi bilan
y_a, y_b = WIN_Y - WIN_W / 2, WIN_Y + WIN_W / 2
wall("w_right_a", (WT, y_a - RY0, H), (RX1 + WT / 2, (RY0 + y_a) / 2, H / 2))
wall("w_right_b", (WT, RY1 - y_b, H), (RX1 + WT / 2, (y_b + RY1) / 2, H / 2))
wall("w_right_lo", (WT, WIN_W, WIN_Z0), (RX1 + WT / 2, WIN_Y, WIN_Z0 / 2))
wall("w_right_hi", (WT, WIN_W, H - WIN_Z1), (RX1 + WT / 2, WIN_Y, (H + WIN_Z1) / 2))
box("win_glass", (0.01, WIN_W, WIN_Z1 - WIN_Z0), (RX1 + 0.05, WIN_Y, (WIN_Z0 + WIN_Z1) / 2),
    mat("win_glass", (0.7, 0.8, 0.85), 0.02, trans=1.0, ior=1.45), parent=room)
for dy in (-WIN_W / 2 - 0.03, WIN_W / 2 + 0.03):
    box("wframe", (WT + 0.05, 0.06, WIN_Z1 - WIN_Z0 + 0.06), (RX1 + WT / 2, WIN_Y + dy, (WIN_Z0 + WIN_Z1) / 2), trim, parent=room)
for z in (WIN_Z0 - 0.03, WIN_Z1 + 0.03):
    box("wframe_h", (WT + 0.12, WIN_W + 0.12, 0.06), (RX1 + WT / 2, WIN_Y, z), trim, parent=room)
for dy in (-0.95, 0.95):
    c_ = box("curtain", (0.06, 0.5, 2.4), (RX1 - 0.14, WIN_Y + dy, 1.28), mat("curtain", (0.32, 0.36, 0.42), 0.9), parent=room)
    wv = c_.modifiers.new("wave", "WAVE"); wv.height = 0.03; wv.width = 0.12; wv.narrowness = 1.0; wv.use_y = False; wv.speed = 0
    c_.modifiers.new("sub", "SUBSURF").levels = 1
plane("floor", (RX1 - RX0, RY1 - RY0), (0, (RY0 + RY1) / 2, 0.0), floor_m, parent=room)
box("ceiling", (RX1 - RX0 + 0.4, RY1 - RY0 + 0.4, 0.12), (0, (RY0 + RY1) / 2, H + 0.06), ceil_m, parent=room)
box("baseboard_b", (RX1 - RX0, 0.025, 0.1), (0, RY1 - 0.012, 0.05), trim, parent=room)
box("baseboard_l", (0.025, RY1 - RY0, 0.1), (RX0 + 0.012, (RY0 + RY1) / 2, 0.05), trim, parent=room)
rug = plane("rug", (2.6, 1.9), (0.0, -1.0, 0.004), mat("rug", (0.32, 0.22, 0.16), 0.95), parent=room)
# mebel (Poly Haven)
sofa = empty("sofa", (0, 0, 0), room); import_gltf(PH + "Sofa_01/Sofa_01.gltf", sofa); sofa.scale = (1.3,) * 3
TABLE = Vector((0.05, -1.2, 0.0)); TABLE_TOP = 0.392
table = empty("ctable", TABLE, room); import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", table); table.rotation_euler = (0, 0, R(90))
plant = empty("plant", (1.55, 0.45, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plant); plant.scale = (1.15,) * 3
# torsher (iliq chiroq) divanning chap tomonida
LAMP = Vector((-1.45, 0.35, 0))
cyl("lamp_base", 0.16, 0.03, LAMP + Vector((0, 0, 0.015)), black, parent=room)
cyl("lamp_pole", 0.012, 1.5, LAMP + Vector((0, 0, 0.78)), steel, parent=room)
bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.24, radius2=0.16, depth=0.32, end_fill_type="NOTHING")
shd = bpy.context.object; shd.name = "lamp_shade"; shd.location = LAMP + Vector((0, 0, 1.62)); shd.data.materials.append(shade_m); shd.parent = room
shd.modifiers.new("sol", "SOLIDIFY").thickness = 0.004
# devordagi rozetka (kabel shu yerga ulangan)
SOCK = Vector((-1.3, RY1 - 0.005, 0.3))
box("socket_plate", (0.085, 0.012, 0.085), SOCK, white_pl, parent=room, bevel=0.004)
cyl("socket_hole", 0.022, 0.006, SOCK + Vector((0, -0.007, 0)), mat("sock_in", (0.75, 0.75, 0.73), 0.5), rot=(90, 0, 0), parent=room)
box("charger", (0.04, 0.035, 0.045), SOCK + Vector((0, -0.03, 0)), white_pl, parent=room, bevel=0.005)

# ======================================================================
# 3) TELEFON (protsedural): yotiq holatda X = uzun tomon (0.162), Y = 0.075, Z = ekran normali
# ======================================================================
PW, PHh, PD = 0.162, 0.075, 0.0085
def rr_loop(w, h, n=64, p=0.13):
    return [(x, y) for x, y in rrect(w, h, 0.0, n, p)]
def prism(name, w, h, z0, z1, m, parent, n=64, p=0.13):
    lp = rr_loop(w, h, n, p); k = len(lp)
    vs = [(x, y, z0) for x, y in lp] + [(x, y, z1) for x, y in lp]
    fs = [tuple(range(k))[::-1], tuple(range(k, 2 * k))] + [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
    o = mesh_obj(name, vs, fs, m, parent)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.0012; bv.segments = 3; bv.limit_method = "ANGLE"
    o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o
def screen_mesh(name, w, h, z, m, parent):
    lp = rr_loop(w, h, 64, 0.13)
    vs = [(0, 0, z)] + [(x, y, z) for x, y in lp]; k = len(lp)
    fs = [(0, 1 + i, 1 + (i + 1) % k) for i in range(k)]
    o = mesh_obj(name, vs, fs, m, parent)
    uvl = o.data.uv_layers.new(name="UVMap")
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            v = o.data.vertices[o.data.loops[li].vertex_index].co
            uvl.data[li].uv = ((v.x + w / 2) / w, (v.y + h / 2) / h)
    return o
def grid_box(name, sx, sy, sz, m, parent, nx=24, ny=12, loc=(0, 0, 0)):
    """bo'linib yasalgan quti (shape key uchun): markaz (0,0,0)"""
    bm_ = bpy.data.meshes.new(name)
    import bmesh
    b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)
    bmesh.ops.scale(b, vec=(sx, sy, sz), verts=b.verts)
    bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=max(nx, ny), use_grid_fill=True)
    b.to_mesh(bm_); b.free()
    o = bpy.data.objects.new(name, bm_); sc.collection.objects.link(o); o.location = loc
    if m: bm_.materials.append(m)
    if parent: o.parent = parent
    return o
def swell_key(o, amp, sx, sy):
    o.shape_key_add(name="Basis", from_mix=False)
    k = o.shape_key_add(name="swell", from_mix=False); k.value = 0
    for i, v in enumerate(o.data.vertices):
        u = 1 - (2 * v.co.x / sx) ** 2; w_ = 1 - (2 * v.co.y / sy) ** 2
        b_ = max(0.0, u) ** 0.6 * max(0.0, w_) ** 0.6
        k.data[i].co = v.co + Vector((0, 0, math.copysign(amp * b_, v.co.z) if abs(v.co.z) > 1e-5 else 0))
    return k

def build_phone(name, parent, real=True):
    R_ = {}
    root = empty(name, (0, 0, 0), parent); R_["root"] = root
    if real:
        R_["body"] = prism(name + "_body", PW, PHh, -PD / 2, PD / 2 - 0.0006, alu, root)
        R_["back"] = prism(name + "_back", PW - 0.002, PHh - 0.002, -PD / 2 - 0.0002, -PD / 2 + 0.001, backglass, root)
        hinge = empty(name + "_scr_hinge", (0, PHh / 2 - 0.001, PD / 2 - 0.0006), root); R_["hinge"] = hinge
        R_["screen"] = screen_mesh(name + "_screen", PW - 0.0016, PHh - 0.0016, 0.0, screen_m, None)
        R_["screen"].parent = hinge; R_["screen"].location = (0, -(PHh / 2 - 0.001), 0.0004)
        prism(name + "_glass", PW - 0.0016, PHh - 0.0016, -0.0003, 0.0, black, hinge).location = (0, -(PHh / 2 - 0.001), 0.0004)
        # orqa kamera bloki (+X tomonda)
        box(name + "_cambump", (0.03, 0.03, 0.0015), (PW / 2 - 0.025, 0.012, -PD / 2 - 0.0008), backglass, parent=root, bevel=0.003)
        for dx, dy in ((-0.007, 0.007), (0.007, 0.007), (-0.007, -0.007)):
            cyl(name + "_lens", 0.0045, 0.002, (PW / 2 - 0.025 + dx, 0.012 + dy, -PD / 2 - 0.0016), lens_m, parent=root, verts=24)
        # USB-C port (-X uchida)
        box(name + "_port", (0.003, 0.0089, 0.0032), (-PW / 2 + 0.0008, 0, 0), black, parent=root, bevel=0.0012)
        for s_ in (-1, 1):
            box(name + "_btn", (0.012 if s_ > 0 else 0.022, 0.0012, 0.003), (0.02 * s_, s_ * (PHh / 2 + 0.0004), 0), alu, parent=root, bevel=0.0005)
    else:
        xs = prism(name + "_xshell", PW, PHh, -PD / 2, PD / 2, xshell, root); R_["xshell"] = xs
    # ichki qismlar
    bat = grid_box(name + "_bat", 0.096, 0.062, 0.0046, bat_real_m if real else bat_m, root, nx=20, loc=(0.022, 0, -0.0005))
    bat.modifiers.new("bev", "BEVEL").width = 0.001
    R_["bat"] = bat; R_["swell"] = swell_key(bat, 0.0025 if real else 0.011, 0.096, 0.062)   # haqiqiy telefonda ekrandan teshib chiqmasin
    R_["board"] = box(name + "_board", (0.048, 0.066, 0.001), (-0.053, 0, -0.0018), pcb_m, parent=root)
    R_["cpu"] = box(name + "_cpu", (0.013, 0.013, 0.0014), (-0.056, 0.01, -0.0005), cpu_m, parent=root, bevel=0.0004)
    for i in range(6):
        box(name + f"_chip{i}", (random.uniform(0.004, 0.009), random.uniform(0.003, 0.007), 0.001),
            (-0.062 + random.uniform(-0.012, 0.016), random.uniform(-0.028, 0.026), -0.0007), black, parent=root)
    return R_

# qo'ldagi telefon (real + rentgen qobiq bir xil joyda)
PHN = build_phone("phone", None, real=True)
proot = PHN["root"]; proot.rotation_mode = "QUATERNION"
XSH = prism("phone_xshell", PW, PHh, -PD / 2, PD / 2, xshell, proot)
# ekran nuri (yuzga)
scr_light = bpy.data.objects.new("scr_light", bpy.data.lights.new("scr_light", "AREA")); sc.collection.objects.link(scr_light)
scr_light.data.shape = "RECTANGLE"; scr_light.data.size, scr_light.data.size_y = 0.15, 0.07; scr_light.data.color = (0.75, 0.6, 1.0)
scr_light.parent = proot; scr_light.location = (0, 0, 0.12); scr_light.rotation_euler = (R(180), 0, 0); scr_light.visible_camera = False   # +Z (yuz) tomonga
scr_light.data.energy = 3.0

# ======================================================================
# 4) MEGAN: divanda o'tirib o'ynaydi (Gaming), portlashda sakrab turadi (Scared)
# ======================================================================
mroot, marm, mmesh = mc.load_character("Megan", "Megan.fbx"); sc.render.fps = 24
soften(mmesh)
ROOT0 = Vector((0.0, 0.12, -0.06))
mroot.location = ROOT0
def bwp(b): return (marm.matrix_world @ marm.pose.bones["mixamorig:" + b].head).copy()
gaming = A_("Gaming.fbx", inplace=False); scared = A_("Scared.fbx", inplace=False)
gs = mc.add_strip(marm, gaming, 1, repeat=(F_BOOM + 10) / (151 * 0.8), hold=True); gs.blend_in = 0
ss = mc.add_strip(marm, scared, F_BOOM - 2, src=(40, 303), hold=True); ss.blend_in = 4; ss.use_auto_blend = False
face_t = child_of_bone("face_t", marm, "Head", (0, 0.09, 0.09))

# telefonni qo'llarga "bake" qilish (har kadr), keyin stolga uchishi
def phone_pose(f):
    sc.frame_set(f)
    # bosh barmoqlar ekranda, qolgan barmoqlar orqada: markaz = bosh barmoqlar o'rtasi, normal = ko'zlarga
    lk, rk = bwp("LeftHandMiddle1"), bwp("RightHandMiddle1")
    lt, rt, hd = bwp("LeftHandThumb3"), bwp("RightHandThumb3"), bwp("Head")
    ct = (lt + rt) / 2; lg = (lk - rk).normalized()
    n = hd + Vector((0, -0.07, 0.1)) - ct; n = (n - lg * n.dot(lg)).normalized()
    c = ct - n * 0.009 + lg * 0.01
    return c, lg, n
POSES = {}
for f in range(1, F_BOOM + 3):
    POSES[f] = phone_pose(f)
def smooth_pose(f, k=2):
    fs = [x for x in range(f - k, f + k + 1) if x in POSES]
    c = sum((POSES[x][0] for x in fs), Vector()) / len(fs)
    lg = sum((POSES[x][1] for x in fs), Vector()).normalized(); n = sum((POSES[x][2] for x in fs), Vector()).normalized()
    n = (n - lg * n.dot(lg)).normalized()
    return c, n.cross(lg), n
LAND = Vector((TABLE.x + 0.08, TABLE.y + 0.12, TABLE_TOP + PD / 2 + 0.001))
F_LAND = F_BOOM + 14
for f in range(1, END + 1):
    if f <= F_BOOM + 2:
        c, fw, n = smooth_pose(f); q = frame_q(fw, n)
    elif f <= F_LAND:
        t = (f - F_BOOM - 2) / (F_LAND - F_BOOM - 2)
        c0, fw0, n0 = smooth_pose(F_BOOM + 2)
        c = c0.lerp(LAND, t) + Vector((0, 0, 0.35 * math.sin(math.pi * t)))
        q0 = frame_q(fw0, n0); q1 = frame_q(Vector((math.sin(R(30)), math.cos(R(30)), 0)), Vector((0, 0, 1)))
        spin = Quaternion(Vector((1, 0.3, 0)).normalized(), R(360) * t * (1 - t) * 2)
        q = spin @ q0.slerp(q1, t)
    else:
        bounce = 0.012 * math.exp(-(f - F_LAND) / 2.0) * abs(math.sin((f - F_LAND) * 1.3))
        c = LAND + Vector((0, 0, bounce)); q = frame_q(Vector((math.sin(R(30)), math.cos(R(30)), 0)), Vector((0, 0, 1)))
    proot.location = c; proot.rotation_quaternion = q
    proot.keyframe_insert("location", frame=f); proot.keyframe_insert("rotation_quaternion", frame=f)
interp(proot, "LINEAR")

# ---------------- zaryadlovchi kabel: vilka (bake) + NURBS egri, ikki uchi hook bilan ----------------
plug = empty("plug_end"); plug.rotation_mode = "QUATERNION"
PORT_L = Vector((-PW / 2, 0, 0))
F_PLUG0 = 1
def port_world(f, out=0.0):
    sc.frame_set(f)
    return proot.matrix_world @ (PORT_L + Vector((-out, 0, 0))), proot.matrix_world.to_quaternion()
SEAT_DROP = Vector((-0.25, -0.42, 0.43))
for f in range(1, END + 1):
    if f <= F_BOOM + 1:
        t = min(1.0, max(0.0, (f - 1) / (F_PLUG - 1)))
        out = 0.03 * (1 - ease(t)) if f < F_PLUG else 0.0
        p, q = port_world(f, out)
    else:
        if f == F_BOOM + 2:
            p_rel, q_rel = port_world(F_BOOM + 1)
        t = min(1.0, (f - F_BOOM - 1) / 8.0)
        p = p_rel.lerp(SEAT_DROP, t) + Vector((0, 0, 0.12 * math.sin(math.pi * t)))
        q = q_rel.slerp(frame_q(Vector((0, 1, 0)), Vector((0, 0, 1))) @ Quaternion((0, 0, 1), R(90)), t)
    plug.location = p; plug.rotation_quaternion = q
    plug.keyframe_insert("location", frame=f); plug.keyframe_insert("rotation_quaternion", frame=f)
interp(plug, "LINEAR")
# vilka: metall tilcha + oq korpus (plug_end mahalliy -X tomonga)
box("plug_tip", (0.0075, 0.0083, 0.0026), (0.0025, 0, 0), steel, parent=plug, bevel=0.001)
box("plug_body", (0.022, 0.012, 0.0065), (-0.0125, 0, 0), white_pl, parent=plug, bevel=0.0025)
cyl("plug_boot", 0.0028, 0.012, (-0.0285, 0, 0), white_pl, rot=(0, 90, 0), parent=plug, verts=16)
sc.frame_set(1); bpy.context.view_layer.update()
M1 = plug.matrix_world.copy()
CPTS = [M1 @ Vector((-0.034, 0, 0)), M1 @ Vector((-0.07, 0, 0)), Vector((-0.3, -0.42, 0.62)), Vector((-0.33, -0.38, 0.44)),
        Vector((-0.5, -0.5, 0.36)), Vector((-0.62, -0.62, 0.05)), Vector((-0.75, -0.75, 0.006)), Vector((-1.25, -0.55, 0.006)),
        Vector((-1.45, 0.2, 0.006)), Vector((-1.32, 0.78, 0.04)), SOCK + Vector((0, -0.05, -0.02))]
cu = bpy.data.curves.new("cable", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0019; cu.bevel_resolution = 3; cu.resolution_u = 16
spl = cu.splines.new("NURBS"); spl.points.add(len(CPTS) - 1)
for i, p in enumerate(CPTS): spl.points[i].co = (*p, 1.0)
spl.order_u = 3; spl.use_endpoint_u = True; spl.use_smooth = True
cable = bpy.data.objects.new("cable", cu); sc.collection.objects.link(cable); cu.materials.append(cable_m)
hk = cable.modifiers.new("hook", "HOOK"); hk.object = plug; hk.vertex_indices_set([0, 1]); hk.matrix_inverse = M1.inverted()

# ======================================================================
# 5) RENTGEN STUDIYASI (S1): katta qora sfera ichida yotgan rentgen telefon, oqimlar, issiqlik to'lqinlari
# ======================================================================
def studio(name, c, r=4.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r); o = bpy.context.object; o.name = name
    o.location = c; o.data.materials.append(studio_bg)
    for p in o.data.polygons: p.flip()
    return o
studio("studio_ph", S1); studio("studio_cell", C0 + Vector((0, 0, 0.2)), 5.0)
plane("studio_floor", (6, 6), S1 + Vector((0, 0, -0.02)), mat("sfloor", (0.008, 0.01, 0.014), 0.25, coat=0.6))
XP = build_phone("xphone", None, real=False); xroot = XP["root"]; xroot.location = S1; xroot.rotation_euler = (0, 0, R(18))
sc.frame_set(1); bpy.context.view_layer.update()
def xw(p): return xroot.matrix_world @ Vector(p)
# kabel (rentgen) + oqim yo'llari
def poly_curve(name, pts, m, bev=0.0):
    c_ = bpy.data.curves.new(name, "CURVE"); c_.dimensions = "3D"; c_.bevel_depth = bev; c_.resolution_u = 12
    sp_ = c_.splines.new("BEZIER"); sp_.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp_ = sp_.bezier_points[i]; bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, c_); sc.collection.objects.link(o)
    if m: c_.materials.append(m)
    return o
poly_curve("xcable", [xw((-0.4, -0.05, -0.01)), xw((-0.2, 0.0, 0.0)), xw((-0.1, 0, 0)), xw((-PW / 2 - 0.004, 0, 0))], xcable, 0.0025)
G_PATH = poly_curve("g_path", [xw((-0.4, -0.05, -0.006)), xw((-0.2, -0.0, -0.002)), xw((-0.08, -0.012, 0.004)), xw((-0.03, -0.014, 0.004)),
                               xw((0.02, -0.012, 0.004))], None)
Y_PATH = poly_curve("y_path", [xw((0.0, 0.014, 0.004)), xw((-0.03, 0.016, 0.004)), xw((-0.056, 0.01, 0.003))], None)
for pth in (G_PATH, Y_PATH): pth.data.use_path = True; pth.hide_render = True
def pulses(name, pth, m, n, period, ranges, r=0.0022):
    out = []
    for i in range(n):
        o = sphere(f"{name}{i}", r, (0, 0, 0), m, sub=2)
        c_ = o.constraints.new("FOLLOW_PATH"); c_.target = pth; c_.use_fixed_location = True
        ph = i / n
        f0 = 1 - int(ph * period)
        c_.offset_factor = 0.0; c_.keyframe_insert("offset_factor", frame=f0)
        c_.offset_factor = 1.0; c_.keyframe_insert("offset_factor", frame=f0 + period)
        for fc in fcurves(o):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"
            fc.modifiers.new("CYCLES")
        vis(o, ranges); out.append(o)
    return out
pulses("gp", G_PATH, pulse_g, 14, 30, rng("xray", "draw"))
pulses("yp", Y_PATH, pulse_y, 6, 16, rng("draw"))
# protsessordan issiqlik to'lqinlari (radial halqalar shader'i)
def wave_mat():
    m = bpy.data.materials.new("heatwave"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); ph = value_node(m, "ph", 0.0); amt = value_node(m, "amt", 0.0)
    d = P.math_n(N, L, "LENGTH", tc.outputs["Object"], None, vec=True)
    fr = P.math_n(N, L, "FRACT", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", d, 45.0), ph))
    ring = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", fr, 0.5)), 2.0)), 8.0)
    fade = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", d, 0.1), clamp=True)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.18, 0.03, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", ring, fade), P.math_n(N, L, "MULTIPLY", amt, 5.0)), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
    return m
wave_m = wave_mat()
wv_o = plane("heatwave", (0.2, 0.2), (-0.056, 0.01, 0.0055), wave_m, parent=xroot)
cyc_node(wave_m, "ph", F0("cpu"), 0.0, F0("cpu") + 24, 1.0)
mkeys(wave_m, "amt", [(1, 0.0), (T(19.0), 0.0), (T(19.6), 1.0), (END, 1.0)])
# gaz pufakchalari (batareya ichida)
BUB = []
for i in range(14):
    o = sphere(f"bubble{i}", 1.0, (0.022 + random.uniform(-0.04, 0.04), random.uniform(-0.025, 0.025), 0.0005), bubble_m, sub=2, parent=xroot)
    r0 = random.uniform(0.002, 0.005); fs_ = F0("swell") + random.randint(0, 20)
    key(o, 1, scale=(0.0001,) * 3); key(o, fs_, scale=(0.0001,) * 3); key(o, fs_ + 16, scale=(r0, r0, r0 * 0.6)); BUB.append(o)

# ======================================================================
# 6) BATAREYA QATLAMLARI KESIMI (C0): Cu | anod | separator | katod | Al ; ionlar, erish, tegish, uchqun
# ======================================================================
cell = empty("cell", C0)
CW, CDp = 1.3, 0.7
LAY = {"cu": (0.0, 0.015), "anode": (0.015, 0.135), "sep": (0.215, 0.235), "cathode": (0.315, 0.435), "al": (0.435, 0.45)}
def slab(name, z0, z1, m, nx=90):
    o = grid_box(name, CW, CDp, z1 - z0, m, cell, nx=nx, loc=(0, 0, (z0 + z1) / 2))
    return o
slab("cu", *LAY["cu"], copper_c, 12)
anode = slab("anode", *LAY["anode"], anode_c)
sep = slab("separator", *LAY["sep"], sep_m, 30)
cathode = slab("cathode", *LAY["cathode"], cathode_c)
slab("al", *LAY["al"], alfoil_c, 12)
def ridge_key(o, sign, amp=0.09, w=0.075):
    o.shape_key_add(name="Basis", from_mix=False); k = o.shape_key_add(name="bend", from_mix=False); k.value = 0
    hz = max(v.co.z for v in o.data.vertices)
    for i, v in enumerate(o.data.vertices):
        t = (v.co.z + hz) / (2 * hz); t = t if sign > 0 else 1 - t      # tegish yuzasi 1, qarama-qarshi yuza 0
        k.data[i].co = v.co + Vector((0, 0, sign * amp * t * math.exp(-(v.co.x / w) ** 2)))
    return k
bend_a = ridge_key(anode, +1); bend_c = ridge_key(cathode, -1)
text("t_plus", "+", 0.14, (-CW / 2 - 0.12, -CDp / 2, 0.375), (90, 0, 0), plus_m, parent=cell)
text("t_minus", "−", 0.14, (-CW / 2 - 0.12, -CDp / 2, 0.075), (90, 0, 0), minus_m, parent=cell)
# litiy ionlari: katoddan anodga (zaryadlanish)
IONS = []
for i in range(46):
    x = random.uniform(-0.55, 0.55); y = random.uniform(-CDp / 2 + 0.02, -0.04); per = random.randint(30, 44)
    o = sphere(f"ion{i}", 0.011, (0, 0, 0), ion_m, sub=2, parent=cell)
    f0 = 1 - random.randint(0, per)
    key(o, f0, loc=(x, y, 0.36)); key(o, f0 + per, loc=(x + random.uniform(-0.04, 0.04), y, 0.09))
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
    IONS.append(o)
# qisqa tutashuv uchquni (old yuzada, tegish chizig'ida)
SPK = Vector((0.0, -CDp / 2 - 0.005, 0.225))
arc = empty("arc", SPK, cell)
for i in range(46):
    d_ = Vector((random.uniform(-1, 1), random.uniform(-1.0, -0.1), random.uniform(-1, 1))).normalized(); ln = random.uniform(0.04, 0.28)
    c_ = cyl(f"arc_ray{i}", 0.0018, ln, (0, 0, 0), arc_m if i % 3 else spark_m, parent=arc, verts=6)
    c_.location = d_ * ln / 2; c_.rotation_mode = "QUATERNION"; c_.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d_)
sphere("arc_core", 0.03, (0, 0, 0), arc_m, sub=2, parent=arc)
glow_c = sphere("arc_glow", 0.12, (0, 0, 0), glow_mat("arc_glow", (0.7, 0.85, 1.0)), sub=3, parent=arc)
glow_c.data.materials[0].node_tree.nodes["a"].outputs[0].default_value = 1.0
arc.rotation_mode = "XYZ"
key(arc, 1, scale=(0.001,) * 3); key(arc, F_SHORT - 1, scale=(0.001,) * 3)
for j, f in enumerate(range(F_SHORT, F1("short") + 2, 2)):
    s_ = (1.25 if j == 0 else random.uniform(0.55, 1.0)) * (1.0 if f <= F1("short") else 0.001)
    key(arc, f, scale=(s_,) * 3, rot=(random.uniform(-25, 25), random.uniform(-180, 180), random.uniform(-25, 25)))
interp(arc, "CONSTANT")

# ======================================================================
# 7) OLOV, TUTUN, UCHQUNLAR
# ======================================================================
anchor = empty("fire_anchor")
cl = anchor.constraints.new("COPY_LOCATION"); cl.target = proot
def flame_mat(name, col_hot=(1.0, 0.72, 0.25)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); ph = value_node(m, "ph", 0.0); amt = value_node(m, "amt", 0.0)
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    h = P.math_n(N, L, "DIVIDE", sx.outputs[2], 1.0, clamp=True)           # mahalliy z 0..1 (ob'ekt scale bilan cho'ziladi)
    rr = P.math_n(N, L, "LENGTH", P.math_n(N, L, "MULTIPLY", tc.outputs["Object"], (1.0, 1.0, 0.0), vec=True), None, vec=True)
    wdt = P.math_n(N, L, "ADD", 0.28, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SINE", P.math_n(N, L, "MULTIPLY", h, 2.6)), 0.4))
    prof = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", rr, wdt), clamp=True),
                    P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, h, clamp=True), 0.8))
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "MULTIPLY", ph, -1.0), cmb.inputs[2]); L.new(cmb.outputs[0], mp.inputs["Location"])
    mp.inputs["Scale"].default_value = (2.6, 2.6, 1.6)
    no = N.new("ShaderNodeTexNoise"); no.noise_dimensions = "4D"; no.inputs["Scale"].default_value = 1.6; no.inputs["Detail"].default_value = 6.0
    no.inputs["Roughness"].default_value = 0.65; no.inputs["Distortion"].default_value = 0.6; L.new(mp.outputs[0], no.inputs["Vector"]); L.new(ph, no.inputs["W"])
    d = P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", prof, 1.3), P.math_n(N, L, "MULTIPLY", no.outputs["Fac"], 1.9)), 1.2)
    d = P.math_n(N, L, "MULTIPLY", d, 2.2, clamp=True)
    d = P.math_n(N, L, "MULTIPLY", d, amt)
    cr = N.new("ShaderNodeValToRGB"); L.new(P.math_n(N, L, "MULTIPLY", d, P.math_n(N, L, "SUBTRACT", 1.3, h)), cr.inputs[0])
    e = cr.color_ramp.elements; e[0].position = 0.0; e[0].color = (0.2, 0.01, 0.0, 1); e[1].position = 0.85; e[1].color = (*col_hot, 1)
    e.new(0.3).color = (1.0, 0.2, 0.005, 1); e.new(0.6).color = (1.0, 0.45, 0.04, 1)
    pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.0
    L.new(cr.outputs[0], pv.inputs["Emission Color"]); L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", d, 1.5), 65.0), pv.inputs["Emission Strength"])
    L.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
    return m
def smoke_mat(name, dens=6.0, col=(0.06, 0.06, 0.065)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); ph = value_node(m, "ph", 0.0); amt = value_node(m, "amt", 0.0)
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    h = P.math_n(N, L, "MAXIMUM", sx.outputs[2], 0.0)
    rr = P.math_n(N, L, "LENGTH", P.math_n(N, L, "MULTIPLY", tc.outputs["Object"], (1.0, 1.0, 0.0), vec=True), None, vec=True)
    prof = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", rr, P.math_n(N, L, "ADD", 0.25, P.math_n(N, L, "MULTIPLY", h, 0.6))), clamp=True),
                    P.math_n(N, L, "SUBTRACT", 1.0, h, clamp=True))
    prof = P.math_n(N, L, "MULTIPLY", prof, P.math_n(N, L, "MULTIPLY", h, 5.0, clamp=True))     # pastki qopqoq keskin chiqmasin
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "MULTIPLY", ph, -0.6), cmb.inputs[2]); L.new(cmb.outputs[0], mp.inputs["Location"])
    no = N.new("ShaderNodeTexNoise"); no.noise_dimensions = "4D"; no.inputs["Scale"].default_value = 3.0; no.inputs["Detail"].default_value = 4.0
    L.new(mp.outputs[0], no.inputs["Vector"]); L.new(ph, no.inputs["W"])
    d = P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", prof, 1.8), no.outputs["Fac"]), 0.85, clamp=True)
    d = P.math_n(N, L, "MULTIPLY", d, P.math_n(N, L, "MULTIPLY", prof, 4.0, clamp=True))     # hajm devorida keskin chegara bo'lmasin
    pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", d, amt), dens), pv.inputs["Density"])
    L.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
    return m
fire_m = flame_mat("fire")
flame = cyl("flame", 1.0, 1.0, (0, 0, 0), fire_m, parent=anchor, verts=16)
for v in flame.data.vertices: v.co.z += 0.5
flame.scale = (0.38, 0.38, 0.95)
cyc_node(fire_m, "ph", F_BOOM, 0.0, F_BOOM + 24, 1.6)
fa = [(1, 0.0), (F_BOOM - 1, 0.0), (F_BOOM + 2, 1.25), (F_BOOM + 8, 0.95)]
for f in range(F_BOOM + 10, END + 1, 3): fa.append((f, random.uniform(0.85, 1.05)))
mkeys(fire_m, "amt", fa)
smoke_m = smoke_mat("smoke", 9.0, (0.16, 0.15, 0.15))
smk = cyl("smoke", 1.0, 1.0, (0, 0, 0), smoke_m, parent=anchor, verts=16)
for v in smk.data.vertices: v.co.z += 0.5
smk.scale = (0.8, 0.8, 1.6); smk.location = (0, 0, 0.35)
cyc_node(smoke_m, "ph", F_BOOM, 0.0, F_BOOM + 24, 0.8)
mkeys(smoke_m, "amt", [(1, 0.0), (F_BOOM + 3, 0.0), (F_BOOM + 20, 0.7), (END, 1.0)])
# ekran chetidan sizib chiqadigan oq tutun (bulge/crack)
wisp_m = smoke_mat("wisp", 2.2, (0.6, 0.6, 0.62))
wisp_a = empty("wisp_anchor", (0.0, -PHh / 2, 0.003), proot)
wisp = cyl("wisp", 1.0, 1.0, (0, 0, 0), wisp_m, verts=12)
for v in wisp.data.vertices: v.co.z += 0.5
wisp.parent = None
cw = wisp.constraints.new("COPY_LOCATION"); cw.target = wisp_a
wisp.scale = (0.025, 0.025, 0.25)
cyc_node(wisp_m, "ph", F0("bulge"), 0.0, F0("bulge") + 24, 1.4)
mkeys(wisp_m, "amt", [(1, 0.0), (T(37.2), 0.0), (T(38.4), 0.8), (F_BOOM, 1.0)])
# uchqunlar (particle system): yoriqdan va portlashda
spark_obj = sphere("spark_inst", 0.0012, (0, -200, 0), spark_m, sub=1)
def sparks(name, parent, loc, f0, f1, count, vel, life, size=1.0, normal=(0, 0, 1)):
    em_ = plane(name, (0.02, 0.02), loc, None, parent=parent)
    ps_mod = em_.modifiers.new(name, "PARTICLE_SYSTEM"); st = em_.particle_systems[0].settings
    st.count = count; st.frame_end = f1; st.frame_start = f0; st.lifetime = life; st.lifetime_random = 0.6
    st.normal_factor = vel; st.factor_random = vel * 0.8; st.object_align_factor = (0, 0, 0)
    st.render_type = "OBJECT"; st.instance_object = spark_obj; st.particle_size = size; st.size_random = 0.6
    st.effector_weights.gravity = 1.0; st.use_rotations = False
    em_.show_instancer_for_render = False; em_.show_instancer_for_viewport = False
    return em_
sparks("sp_crack", PHN["hinge"], (0.025, -(PHh / 2 - 0.001) - 0.01, 0.001), F_CRACK, F_CRACK + 30, 260, 0.9, 10, 0.8)
sparks("sp_boom", anchor, (0, 0, 0.01), F_BOOM, F_BOOM + 40, 700, 3.2, 18, 2.2)

# ======================================================================
# 8) VAQT BO'YICHA O'ZGARISHLAR: issiqlik, ekran, rentgen, shishish, erish, egilish
# ======================================================================
for m in HEATMATS: mkeys(m, "heat", HEAT)
mkeys(cpu_m, "heat", CPUH)
mkeys(screen_m, "bolt", [(1, 0.0), (F_PLUG - 1, 0.0), (F_PLUG + 1, 1.0), (F_PLUG + 16, 1.0), (F_PLUG + 26, 0.0)])
cyc_node(screen_m, "scroll", 1, 0.0, 241, 1.0)
mkeys(screen_m, "scr", [(1, 1.0), (F_CRACK, 1.0), (F_CRACK + 1, 0.4), (F_CRACK + 3, 0.9), (F_BOOM, 0.6), (F_BOOM + 1, 0.0)], "CONSTANT")
mkeys(screen_m, "crack", [(1, 0.0), (F_CRACK - 1, 0.0), (F_CRACK + 3, 0.75), (F_CRACK + 12, 1.0), (F_BOOM + 4, 1.6)])
mkeys(sep_m, "melt", [(1, 0.0), (T(28.2), 0.0), (T(29.8), 0.85), (T(32.0), 0.95), (END, 1.0)])
for k_ in (bend_a, bend_c): skey(k_, [(1, 0.0), (T(30.0), 0.0), (F_SHORT, 1.0)])
for fc in fcurves(anode.data.shape_keys) + fcurves(cathode.data.shape_keys):
    for k in fc.keyframe_points: k.interpolation = "BEZIER"
for k_ in (XP["swell"], PHN["swell"]): skey(k_, [(1, 0.0), (T(34.7), 0.0), (T(36.4), 0.75), (T(38.8), 1.0), (END, 1.25)])
# ekran ko'tarilishi (bulge) va portlashda uzilishi
hg = PHN["hinge"]
kv(hg, "rotation_euler", [(1, (0, 0, 0)), (T(36.8), (0, 0, 0)), (T(38.6), (R(-11), 0, 0)), (F_BOOM, (R(-14), 0, 0)), (F_BOOM + 4, (R(-55), 0, 0)),
                          (END, (R(-70), 0, 0))], "BEZIER")
# ekran ostidagi qizigan batareya nuri (ekran ko'tarilganda yoriqdan ko'rinadi)
gap_m = emit_mat("gapglow", (1.0, 0.35, 0.05), 0.0)
plane("gap_glow", (PW - 0.01, PHh - 0.01), (0, 0, PD / 2 - 0.0012), gap_m, parent=proot)
gk = gap_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.0), (T(36.8), 0.0), (T(38.0), 6.0), (F_BOOM, 12.0)): gk.default_value = v; gk.keyframe_insert("default_value", frame=f)
# ekran nuri
kv(scr_light.data, "energy", [(1, 2.5), (F_CRACK, 2.5), (F_CRACK + 1, 0.8), (F_BOOM, 1.2), (F_BOOM + 1, 0.0)], "CONSTANT")
# rentgen ko'rinishlari (qo'ldagi telefon)
XR_RANGE = [(F_XR, F1("reactor"))]
REAL = [o for o in proot.children_recursive if o.type == "MESH" and not o.name.startswith(("phone_bat", "phone_board", "phone_cpu", "phone_chip", "phone_xshell"))]
for o in REAL: vis(o, [(1, F_XR - 1), (F1("reactor") + 1, END)], recursive=False)
vis(XSH, XR_RANGE, recursive=False)
# studiya qismlari faqat o'z kadrlarida (render tezligi uchun)
vis(cell, CELL_SHOTS)
for o in IONS: vis(o, rng("ions", "temp"), recursive=False)      # bolalar otadan KEYIN
for o in [xroot]: vis(o, PH_SHOTS)
vis(wv_o, rng("draw"), recursive=False)
for o in BUB: vis(o, rng("swell"), recursive=False)
vis(flame, [(F_BOOM - 1, END)]); vis(smk, [(F_BOOM, END)]); vis(wisp, [(T(37.0), END)])

# ======================================================================
# 9) KAMERALAR
# ======================================================================
def cam_path(name, keys, tgt, lens, fstop=None, focus=None, lin=False, tgt_keys=None, parent=None, clip=0.005):
    if tgt is None:
        tgt = empty(name + "_t", (0, 0, 0), parent); path(tgt, tgt_keys)
    c = shot_cam(name, keys[0][1], tgt, lens, fstop=fstop, focus=focus, clip=clip)
    if parent: c.parent = parent
    path(c, keys, lin=lin)
    return c
def ploc(name, p): return empty(name, p, proot)
f0, f1 = S["hook"]          # makro: vilka portga kiradi, crash zoom
c = cam_path("hook", [(f0, (-0.2, -0.1, 0.05)), (F_PLUG, (-0.15, -0.075, 0.04)), (f1, (-0.13, -0.07, 0.045))], None, 32, fstop=2.8,
             tgt_keys=[(f0, (-PW / 2 - 0.02, 0, 0.0)), (f1, (-PW / 2 + 0.01, 0, 0.0))], parent=proot, clip=0.002)
lens_keys(c, [(f0, 26), (F_PLUG - 2, 30), (F_PLUG + 2, 44), (f1, 48)]); shake(c, F_PLUG, F_PLUG + 10, 0.004, seed=1)
f0, f1 = S["game"]          # poldan past burchak, aylanma
c = orbit_cam("game", f0, f1, (0.0, -0.1, 0), 1.5, 1.3, -18, -48, 0.14, 0.22, 16, empty("game_t", (0.0, -0.25, 0.78)), fstop=5.6)
f0, f1 = S["face"]          # yuz yaqin, DOF
c = cam_path("face", [(f0, (0.32, -0.78, 1.22)), (f1, (0.2, -0.62, 1.16))], face_t, 50, fstop=1.8)
f0, f1 = S["reactor"]       # yelka ortidan, rentgenga o'tish
c = cam_path("reactor", [(f0, (-0.34, 0.12, 1.3)), (f1, (-0.24, -0.02, 1.16))], proot, 30, fstop=2.8)
c.data.dof.focus_object = proot; shake(c, F_XR, F_XR + 8, 0.012, seed=2)
f0, f1 = S["xray"]          # studiya: rentgen telefon, batareyaga sho'ng'ish
c = cam_path("xray", [(f0, tuple(xw((-0.12, -0.32, 0.22)))), (f1 - 14, tuple(xw((-0.02, -0.12, 0.08)))), (f1, tuple(xw((0.02, -0.03, 0.02))))],
             None, 26, fstop=4.0, tgt_keys=[(f0, tuple(xw((-0.04, 0, 0)))), (f1, tuple(xw((0.022, 0, 0))))], clip=0.001)
f0, f1 = S["ions"]          # batareya qatlamlari, yonga sirpanish
c = cam_path("ions", [(f0, tuple(C0 + Vector((-0.55, -1.25, 0.42)))), (f1, tuple(C0 + Vector((0.3, -0.95, 0.3))))], None, 34, fstop=5.6,
             tgt_keys=[(f0, tuple(C0 + Vector((-0.15, -0.3, 0.22)))), (f1, tuple(C0 + Vector((0.1, -0.3, 0.22))))])
f0, f1 = S["thumbs"]        # barmoqlar va ekran makro
c = cam_path("thumbs", [(f0, (0.1, -0.11, 0.075)), (f1, (-0.06, -0.1, 0.07))], None, 26, fstop=2.8,
             tgt_keys=[(f0, (0.03, 0, 0.0)), (f1, (-0.02, 0, 0.0))], parent=proot, clip=0.002)
f0, f1 = S["cpu"]           # protsessorga crash zoom
cpu_w = xw((-0.056, 0.01, 0.0))
c = cam_path("cpu", [(f0, tuple(xw((-0.26, -0.22, 0.16)))), (T(18.9), tuple(xw((-0.14, -0.12, 0.09)))), (f1, tuple(xw((-0.09, -0.07, 0.06))))],
             empty("cpu_t", tuple(cpu_w)), 24, fstop=4.0, clip=0.001)
lens_keys(c, [(f0, 22), (T(18.85), 24), (T(19.05), 42), (f1, 46)]); shake(c, T(18.95), T(18.95) + 8, 0.006, seed=3)
f0, f1 = S["draw"]          # tepadan aylanma
c = orbit_cam("draw", f0, f1, tuple(xw((-0.02, 0, 0))), 0.2, 0.14, -120, -40, 0.24, 0.17, 28, empty("draw_t", tuple(xw((-0.02, 0, 0)))), fstop=5.6)
c.data.clip_start = 0.001
f0, f1 = S["temp"]          # qatlamlar, orqaga chekinish
c = cam_path("temp", [(f0, tuple(C0 + Vector((0.15, -0.62, 0.26)))), (f1, tuple(C0 + Vector((-0.25, -1.45, 0.5))))], None, 30, fstop=5.6,
             tgt_keys=[(f0, tuple(C0 + Vector((0.05, -0.3, 0.23)))), (f1, tuple(C0 + Vector((0.0, -0.3, 0.22))))])
f0, f1 = S["melt"]          # separator ustida, qatlamlar orasida
c = cam_path("melt", [(f0, tuple(C0 + Vector((-0.08, -0.62, 0.28)))), (f1, tuple(C0 + Vector((-0.02, -0.4, 0.27))))], None, 18, fstop=2.8,
             tgt_keys=[(f0, tuple(C0 + Vector((0.0, 0.0, 0.222)))), (f1, tuple(C0 + Vector((0.02, 0.05, 0.222))))], clip=0.002)
f0, f1 = S["touch"]         # yon tomondan, push-in
c = cam_path("touch", [(f0, tuple(C0 + Vector((0.32, -1.05, 0.28)))), (f1, tuple(C0 + Vector((0.12, -0.72, 0.24))))], None, 40, fstop=4.0,
             tgt_keys=[(f0, tuple(C0 + Vector((0.0, -0.33, 0.225)))), (f1, tuple(C0 + Vector((0.0, -0.33, 0.225))))])
f0, f1 = S["short"]         # uchqun, silkinish
c = cam_path("short", [(f0, tuple(C0 + Vector((0.14, -0.8, 0.27)))), (f1, tuple(C0 + Vector((0.2, -0.95, 0.3))))], None, 34, fstop=4.0,
             tgt_keys=[(f0, tuple(C0 + Vector((0.0, -0.33, 0.225)))), (f1, tuple(C0 + Vector((0.0, -0.33, 0.225))))])
shake(c, F_SHORT, F1("short"), 0.02, seed=4)
f0, f1 = S["swell"]         # rentgen telefon, past burchak
c = cam_path("swell", [(f0, tuple(xw((0.16, -0.17, 0.12)))), (f1, tuple(xw((0.11, -0.12, 0.08))))], None, 30, fstop=8.0,
             tgt_keys=[(f0, tuple(xw((0.022, 0, 0.002)))), (f1, tuple(xw((0.022, 0, 0.003))))], clip=0.001)
f0, f1 = S["bulge"]         # qo'ldagi telefon, ekran ko'tariladi, Megan yuzi orqada xira
c = cam_path("bulge", [(f0, (0.11, -0.15, 0.03)), (f1, (0.075, -0.12, 0.022))], None, 30, fstop=5.6,
             tgt_keys=[(f0, (0.01, -0.03, 0.006)), (f1, (0.01, -0.034, 0.008))], parent=proot, clip=0.002)
f0, f1 = S["crack"]         # ekranga makro, crash zoom
c = cam_path("crack", [(f0, (0.1, -0.1, 0.1)), (F_CRACK, (0.07, -0.07, 0.075)), (f1, (0.06, -0.06, 0.065))], None, 28, fstop=11.0,
             tgt_keys=[(f0, (0.02, -0.01, 0.0)), (f1, (0.025, -0.012, 0.0))], parent=proot, clip=0.002)
lens_keys(c, [(f0, 26), (F_CRACK - 1, 28), (F_CRACK + 2, 44), (f1, 46)]); shake(c, F_CRACK, F_CRACK + 12, 0.005, seed=5)
f0, f1 = S["boom"]          # poldan past burchak, keng
c = cam_path("boom", [(f0, (1.15, -2.35, 0.62)), (f1, (0.9, -2.05, 0.58))], None, 16, fstop=5.6,
             tgt_keys=[(f0, (0.0, -0.45, 0.8)), (F_LAND, (0.08, -0.95, 0.75)), (f1, (0.08, -1.0, 0.75))])
shake(c, F_BOOM, F_BOOM + 18, 0.035, seed=6)
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# harorat ko'rsatkichi montajda (ffmpeg drawtext) qo'shiladi: HUD_SHOTS, TEMP -> EVENTS json
HUD_SHOTS = ["cpu", "draw", "temp", "swell"]

# ======================================================================
# 10) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
WN = w.node_tree.nodes; WL = w.node_tree.links
env = WN.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mx = WN.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
WL.new(env.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.45, 0.55, 1.0, 1)
bg = WN["Background"]; WL.new(mx.outputs[2], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.35
ROOMR = ROOM_SHOTS
# kechki deraza nuri (ko'kish) + torsher (iliq) + ship to'ldiruvchi
area("win_fill", (RX1 + 1.0, WIN_Y, 1.7), 1.4, (0.55, 0.68, 1.0), lights_for(ALL, 120.0), target=empty("wf_t", (0.0, -0.6, 0.6)))
area("lamp_key", tuple(LAMP + Vector((0.1, -0.15, 1.45))), 0.35, (1.0, 0.68, 0.38), lights_for(ALL, 45.0), target=face_t)
area("ceil_fill", (0.3, -1.6, H - 0.1), 2.0, (1.0, 0.82, 0.62), lights_for(ALL, 35.0))
point("lamp_bulb", tuple(LAMP + Vector((0, 0, 1.6))), 0.08, (1.0, 0.65, 0.35), lights_for(ALL, 25.0))
area("face_rim", (0.6, 0.6, 1.6), 0.4, (0.7, 0.8, 1.0), lights_for(rng("face", "bulge"), 12.0), target=face_t)
# olov nuri (miltillaydi)
fl = point("fire_light", (0, 0, 0.15), 0.06, (1.0, 0.45, 0.12), [(1, 0)], parent=anchor, const=False)
fl.data.energy = 0; fl.data.keyframe_insert("energy", frame=F_BOOM - 1)
for f in range(F_BOOM, END + 2, 2):
    fl.data.energy = (900 if f < F_BOOM + 4 else random.uniform(220, 380)); fl.data.keyframe_insert("energy", frame=f)
fl.visible_camera = False
# studiyalar
area("ph_top", tuple(S1 + Vector((0.2, -0.3, 0.8))), 0.8, (0.8, 0.9, 1.0), lights_for(PH_SHOTS, 18.0), target=xroot)
area("ph_rim", tuple(S1 + Vector((-0.5, 0.6, 0.3))), 0.6, (0.3, 0.55, 1.0), lights_for(PH_SHOTS, 25.0), target=xroot)
ck = area("cell_key", tuple(C0 + Vector((-0.6, -1.2, 1.2))), 1.2, (1.0, 0.95, 0.9), lights_for(CELL_SHOTS, 80.0), target=empty("ck_t", tuple(C0 + Vector((0, -0.3, 0.2)))))
area("cell_rim", tuple(C0 + Vector((0.9, 0.4, 0.8))), 0.8, (0.35, 0.6, 1.0), lights_for(CELL_SHOTS, 60.0), target=empty("cr_t", tuple(C0 + Vector((0, 0, 0.2)))))
area("cell_gap", tuple(C0 + Vector((0.0, -0.9, 0.275))), 0.5, (1.0, 0.9, 0.8), lights_for(rng("melt"), 15.0), target=empty("cg_t", tuple(C0 + Vector((0, 0, 0.22)))))
ap = point("arc_light", tuple(C0 + SPK + Vector((0, -0.05, 0))), 0.02, (0.7, 0.85, 1.0), [(1, 0)], const=True)
for f in range(F_SHORT, F1("short") + 2, 2): ap.data.energy = 0 if f > F1("short") else random.uniform(8, 30); ap.data.keyframe_insert("energy", frame=f)
ap.visible_camera = False

# xona chiroqlari telefon ekranida oq dog' bo'lib aks etmasin
for l in bpy.data.objects:
    if l.type == "LIGHT" and l.data.type == "AREA": l.visible_glossy = False

# tovush effektlari uchun voqea kadrlari
if os.environ.get("EVENTS"):
    import json
    json.dump({"shots": SHOTS, "plug": F_PLUG, "xr": F_XR, "short": F_SHORT, "crack": F_CRACK, "boom": F_BOOM, "land": F_LAND,
               "cpu_zoom": T(18.95), "end": END, "temp": TEMP, "hud": [S[n] for n in HUD_SHOTS]}, open(os.environ["EVENTS"], "w"))

# ======================================================================
# 11) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 2.0; sc.cycles.volume_max_steps = 128
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT if (OUT := os.environ.get("OUT", "/tmp/claude-0/frames_t/")) else ""
r.use_persistent_data = os.environ.get("PERSIST", "0") == "1"
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("DBG"):
    exec(open(os.environ["DBG"]).read())
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
