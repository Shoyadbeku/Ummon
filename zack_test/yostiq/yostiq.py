# "Yostiq jildi va bakteriyalar" — Zack D. Films uslubida 42.9 s video (1029 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, kana/kana.py (yotoqxona, hammom, mikro teri, kesim), ogri/lib.py (yordamchilar).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_yostiq.sh
# Render: OUT=/tmp/claude-0/frames_y/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/yostiq/yostiq.py --render
# Sinov:  FRAMES=20,60,130,200 PCT=30 OUT=/tmp/claude-0/test/ ... --render   |   Bo'lak: RANGE=a,b
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ZT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ZT)
from lib import *                     # sahnani tozalaydi; bpy, math, random, Vector, mc, sc, R, PH, BK, yordamchilar
import bmesh
import mite as M
import micro as U
sys.path.insert(0, os.path.join(ZT, "gemorroy")); import parts as PT
PT.VIEWPORT_OFF = True
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_y/")
random.seed(7)
END = 1029
sc.frame_start, sc.frame_end = 1, END
def V(*a): return Vector(a)
def ckey(idb, path=None): interp(idb, "CONSTANT", path)

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (47, "tlapse"), (81, "face"), (105, "toilet"), (136, "petri"), (182, "press"), (251, "night8"),
         (299, "sweat"), (342, "flakes"), (378, "dust"), (406, "saliva"), (462, "soak"), (513, "thermal"), (575, "fungi"),
         (601, "breed"), (690, "rub"), (747, "smear"), (789, "pores"), (858, "inflame"), (925, "cream"), (968, "apply")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "tlapse", "face", "night8", "sweat", "saliva", "thermal", "rub")
FABN = ("press", "flakes", "dust", "soak", "fungi", "breed", "smear")
BATHN = ("cream", "apply")
ROOM = rng(*ROOMN); FAB = rng(*FABN); BATHR = rng(*BATHN)
F_17 = 140          # "17 000" — yozuv chiqadi
F_PRESS = 222       # "bosib yotgan" — teri matoga tegadi
F_PUS = 882         # "yiringli"
DAY = 1             # kunduz/tun almashishi: tlapse kadrida

# ======================================================================
# 1) YOTOQXONA (tun): karavot, tumbochka, tungi chiroq, deraza (shahar), devor soati
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.82, 0.86, 0.93))
X0, X1, Y0, Y1, HZ_ = -2.6, 2.4, -1.8, 2.6, 2.7
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
R_(box("wall_L", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_F", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
WX0, WX1, WZ0, WZ1 = -0.3, 1.5, 0.95, 2.25
R_(box("wall_B1", (WX0 - X0, 0.1, HZ_), ((X0 + WX0) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
R_(box("wall_B2", (X1 - WX1, 0.1, HZ_), ((WX1 + X1) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
R_(box("wall_B3", (WX1 - WX0, 0.1, WZ0), ((WX0 + WX1) / 2, Y0 - 0.05, WZ0 / 2), wall_m))
R_(box("wall_B4", (WX1 - WX0, 0.1, HZ_ - WZ1), ((WX0 + WX1) / 2, Y0 - 0.05, (WZ1 + HZ_) / 2), wall_m))
frame_m = mat("win_frame", (0.93, 0.93, 0.9), 0.4)
WC = Vector(((WX0 + WX1) / 2, Y0 - 0.05, (WZ0 + WZ1) / 2)); WW, WH = WX1 - WX0, WZ1 - WZ0
for nm, sz, off in (("wf_t", (WW + 0.04, 0.12, 0.05), (0, 0, WH / 2)), ("wf_b", (WW + 0.04, 0.2, 0.06), (0, 0.05, -WH / 2)),
                    ("wf_l", (0.05, 0.12, WH), (-WW / 2, 0, 0)), ("wf_r", (0.05, 0.12, WH), (WW / 2, 0, 0)),
                    ("wf_m", (0.04, 0.08, WH), (0, 0, 0))):
    R_(box(nm, sz, tuple(WC + Vector(off)), frame_m))
for x in (WX0 - 0.25, WX1 + 0.25):
    R_(box("curtain", (0.45, 0.06, 2.4), (x, Y0 + 0.08, 1.3), mat("curtain_m", (0.55, 0.6, 0.72), 0.9, sss=0.1)))
R_(box("baseboard", (X1 - X0, 0.03, 0.1), ((X0 + X1) / 2, Y1 - 0.015, 0.05), frame_m))
R_(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X0 + 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
R_(plane("out_ground", (40, 30), (0, Y0 - 16, -0.3), mat("out_grass", (0.03, 0.05, 0.03), 0.9)))
rw = random.Random(3)
win_ms = [mat("citylight_w", (1.0, 0.75, 0.4), 0.5, emit=3.0), mat("citylight_b", (0.6, 0.75, 1.0), 0.5, emit=2.0)]
bld_m = mat("bld", (0.02, 0.022, 0.03), 0.8)
for i in range(7):
    x = -6 + i * 2.2 + rw.uniform(-0.4, 0.4); h = rw.uniform(4, 11); y = -12 - rw.uniform(0, 6)
    R_(box(f"bld{i}", (1.8, 1.5, h), (x, y, h / 2 - 0.3), bld_m))
    for k in range(rw.randint(5, 10)):
        R_(box(f"bwin{i}_{k}", (0.25, 0.02, 0.3), (x + rw.uniform(-0.7, 0.7), y + 0.76, rw.uniform(0.5, h - 0.5)), rw.choice(win_ms)))
def gltf(path, loc, rot_z=0.0, scale=1.0):
    e = empty(os.path.basename(path).split(".")[0] + "_grp", loc); import_gltf(path, e)
    e.rotation_euler.z = R(rot_z); e.scale = (scale,) * 3 if not isinstance(scale, tuple) else scale
    return e
R_(gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.95, -1.4, 0), 70, 1.0))
R_(gltf(PH + "Shelf_01/Shelf_01.gltf", (X1 - 0.02, 0.6, 0), -90, 1.0))
R_(gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X1 - 0.15, 0.8, 1.03), -90, 1.0))
R_(plane("rug", (1.6, 1.2), (0.3, 0.5, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))
BED = Vector((-1.5, 1.42, 0.0))
bed_grp = R_(gltf(PH + "GothicBed_01/GothicBed_01.gltf", tuple(BED), 0, 1.0))
bpy.context.view_layer.update()
_dg = bpy.context.evaluated_depsgraph_get()
def hit_z(x, y, z0=1.9):
    ok, loc, *_ = sc.ray_cast(_dg, Vector((x, y, z0)), Vector((0, 0, -1)))
    return loc.z if ok else 0.0
MTOP = hit_z(BED.x, BED.y)
HEAD_SIGN = 1 if hit_z(BED.x, BED.y + 0.97) > hit_z(BED.x, BED.y - 0.97) else -1
print("BED mattress", round(MTOP, 3), "head", HEAD_SIGN)
if HEAD_SIGN < 0: bed_grp.rotation_euler.z = R(180)
R_(gltf(PH + "ClassicNightstand_01/ClassicNightstand_01.gltf", (BED.x + 1.08, BED.y + 0.78, 0), 0, 1.0))
NS_TOP = 0.70
R_(gltf(PH + "alarm_clock_01/alarm_clock_01.gltf", (BED.x + 1.2, BED.y + 0.66, NS_TOP), -60, 1.0))
BL = Vector((BED.x + 0.98, BED.y + 0.9, NS_TOP))
shade_m = mat("shade", (0.95, 0.88, 0.75), 0.8, sss=0.2)
R_(cyl("bl_base", 0.07, 0.03, tuple(BL + V(0, 0, 0.015)), mat("bl_base_m", (0.75, 0.6, 0.35), 0.25, metal=0.9)))
R_(cyl("bl_stem", 0.01, 0.28, tuple(BL + V(0, 0, 0.16)), mat("bl_stem_m", (0.75, 0.6, 0.35), 0.25, metal=0.9)))
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.15, radius2=0.09, depth=0.2, end_fill_type="NOTHING")
shade = bpy.context.object; shade.name = "bl_shade"; shade.location = tuple(BL + V(0, 0, 0.36)); shade.data.materials.append(shade_m)
shade.modifiers.new("so", "SOLIDIFY").thickness = 0.004; smooth(shade); R_(shade)
# devor soati (chap devorda, karavot ustida): strelkalar timelapse'da aylanadi
CLK = Vector((X0 + 0.02, BED.y - 0.35, 1.95))
clk = R_(empty("clock", tuple(CLK))); clk.rotation_euler = (0, R(90), 0)       # mahalliy +Z -> dunyo +X (xonaga qaraydi)
cyl("clk_body", 0.17, 0.04, (0, 0, 0.02), mat("clk_body_m", (0.08, 0.08, 0.09), 0.3), parent=clk, verts=48)
cyl("clk_face", 0.15, 0.005, (0, 0, 0.042), mat("clk_face_m", (0.95, 0.94, 0.9), 0.5), parent=clk, verts=48)
tick_m = mat("tick", (0.05, 0.05, 0.05), 0.5)
for k in range(12):
    a = 2 * math.pi * k / 12
    box(f"tick{k}", (0.008, 0.025 if k % 3 else 0.035, 0.004), (0.125 * math.sin(a), 0.125 * math.cos(a), 0.046), tick_m, rot=(0, 0, -math.degrees(a)), parent=clk)
hand_h = empty("hand_h", (0, 0, 0.048), clk); hand_m = empty("hand_m", (0, 0, 0.05), clk)
box("hh", (0.012, 0.075, 0.003), (0, 0.032, 0), tick_m, parent=hand_h)
box("hm", (0.008, 0.11, 0.003), (0, 0.05, 0), mat("hand_red", (0.7, 0.05, 0.03), 0.4), parent=hand_m)
# yostiq: paxta jild, sarg'aygan dog' ('dirt'), so'lak izi ('drool')
pillow_m = bpy.data.materials.new("pillow"); pillow_m.use_nodes = True
_N = pillow_m.node_tree.nodes; _L = pillow_m.node_tree.links; _b = _N["Principled BSDF"]
_b.inputs["Roughness"].default_value = 0.8; _b.inputs["Sheen Weight"].default_value = 0.5; _b.inputs["Subsurface Weight"].default_value = 0.08
_tc = _N.new("ShaderNodeTexCoord"); _sep = _N.new("ShaderNodeSeparateXYZ"); _L.new(_tc.outputs["Object"], _sep.inputs[0])
_nz = _N.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 7.0; _nz.inputs["Detail"].default_value = 8; _L.new(_tc.outputs["Object"], _nz.inputs["Vector"])
p_dirt = value_node(pillow_m, "dirt", 1.0); p_cx = value_node(pillow_m, "cx", 0.0); p_cy = value_node(pillow_m, "cy", 0.0)
_dx = P.math_n(_N, _L, "SUBTRACT", _sep.outputs["X"], p_cx); _dy = P.math_n(_N, _L, "SUBTRACT", _sep.outputs["Y"], p_cy)
_d = P.math_n(_N, _L, "SQRT", P.math_n(_N, _L, "ADD", P.math_n(_N, _L, "MULTIPLY", _dx, _dx), P.math_n(_N, _L, "MULTIPLY", P.math_n(_N, _L, "MULTIPLY", _dy, _dy), 1.6)))
_rad = P.math_n(_N, _L, "ADD", P.math_n(_N, _L, "MULTIPLY", p_dirt, 0.3), P.math_n(_N, _L, "MULTIPLY", _nz.outputs["Fac"], 0.12))
_st = P.math_n(_N, _L, "MULTIPLY", P.math_n(_N, _L, "SUBTRACT", 1.0, P.math_n(_N, _L, "DIVIDE", _d, _rad), clamp=True), 1.6)
_st = P.math_n(_N, _L, "MULTIPLY", P.math_n(_N, _L, "MINIMUM", _st, 1.0), p_dirt)
_c0 = _N.new("ShaderNodeMix"); _c0.data_type = "RGBA"; _c0.inputs[6].default_value = (0.9, 0.91, 0.93, 1); _c0.inputs[7].default_value = (0.78, 0.76, 0.7, 1)
_L.new(P.math_n(_N, _L, "MULTIPLY", p_dirt, 0.8), _c0.inputs["Factor"])
_c1 = _N.new("ShaderNodeMix"); _c1.data_type = "RGBA"; _c1.inputs[7].default_value = (0.5, 0.34, 0.08, 1)
_L.new(_c0.outputs[2], _c1.inputs[6]); _L.new(P.math_n(_N, _L, "MULTIPLY", _st, 1.0), _c1.inputs["Factor"]); _L.new(_c1.outputs[2], _b.inputs["Base Color"])
_wv = _N.new("ShaderNodeTexWave"); _wv.inputs["Scale"].default_value = 160.0; _L.new(_tc.outputs["Object"], _wv.inputs["Vector"])
_bp = _N.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.12; _L.new(_wv.outputs["Fac"], _bp.inputs["Height"]); _L.new(_bp.outputs[0], _b.inputs["Normal"])
blanket_m = mat("blanket", (0.32, 0.4, 0.62), 0.85, sss=0.05)
nb = blanket_m.node_tree.nodes; lb = blanket_m.node_tree.links
_wv2 = nb.new("ShaderNodeTexWave"); _wv2.inputs["Scale"].default_value = 60.0; _bp2 = nb.new("ShaderNodeBump"); _bp2.inputs["Strength"].default_value = 0.15
lb.new(_wv2.outputs["Fac"], _bp2.inputs["Height"]); lb.new(_bp2.outputs[0], nb["Principled BSDF"].inputs["Normal"])

# ======================================================================
# 2) MEGAN: karavotda uxlaydi (Laying_Sleeping) -> hammomda yuziga krem surtadi (Crying, oldinga/orqaga zanjir)
# ======================================================================
def soften2(meshes, rough=0.48):
    soften(meshes)
    for o in meshes:
        for m in o.data.materials:
            if m and m.use_nodes and "hair" not in m.name.lower():
                for n in m.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED": n.inputs["Roughness"].default_value = rough
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften2(mmeshes)
def strip2(arm, act, start, repeat=1.0, speed=1.0, src=None, rev=False):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = 0; s.blend_out = 0; s.use_reverse = rev
    return s
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)
BATH = Vector((-40.0, -30.0, 0.0))
SLEEP = Vector((BED.x, BED.y + HEAD_SIGN * 0.12, MTOP - 0.95))
C0_ = S["cream"][0]
place(mroot, 1, tuple(SLEEP), 0 if HEAD_SIGN > 0 else 180)
place(mroot, C0_, tuple(BATH), 0)
ckey(mroot)
SLP = A_("Laying_Sleeping.fbx", inplace=False)
strip2(meg, SLP, 1, repeat=span(SLP, C0_ + 2))
N0, N1 = S["night8"]
strip2(meg, SLP, N0, speed=4.0, repeat=span(SLP, (N1 - N0 + 2) * 4.0))           # timelapse: tez ag'darilish
CRY = A_("Crying.fbx")
CS = C0_ - 22
strip2(meg, CRY, CS, src=(1, 31))
RA, RB = 31, 75
f = CS + int(round(30 * 0.8)); k = 0
while f < END + 4:
    strip2(meg, CRY, f, src=(RA, RB), rev=(k % 2 == 1), speed=1.25)
    f += int(round((RB - RA) * 0.8 / 1.25)); k += 1
# yuzni yostiqqa ishqalash (rub): Head/Neck ga qo'shimcha burilish (COMBINE)
RU0, RU1 = S["rub"]
rub = bpy.data.actions.new("rub_add"); rub.use_fake_user = True
meg.animation_data.action = rub
from mathutils import Quaternion
for bn, amp in (("mixamorig:Head", 28.0), ("mixamorig:Neck", 12.0)):
    pb = meg.pose.bones[bn]; pb.rotation_mode = "QUATERNION"
    for fr in range(RU0 - 6, RU1 + 8, 3):
        t = (fr - RU0) / max(1, RU1 - RU0)
        w = max(0.0, min(1.0, (fr - RU0 + 6) / 8.0)) * max(0.0, min(1.0, (RU1 + 6 - fr) / 8.0))
        a = R(amp) * w * math.sin(t * 2 * math.pi * 2.5)
        pb.rotation_quaternion = Quaternion((0, 1, 0), a) @ Quaternion((1, 0, 0), R(amp * 0.25) * w * math.sin(t * 2 * math.pi * 5))
        pb.keyframe_insert("rotation_quaternion", frame=fr)
    pb.rotation_quaternion = (1, 0, 0, 0)
meg.animation_data.action = None
tr = meg.animation_data.nla_tracks.new(); tr.name = "rub"
st_ = tr.strips.new("rub", RU0 - 6, rub)
if hasattr(st_, "action_slot") and rub.slots: st_.action_slot = rub.slots[0]
st_.blend_type = "COMBINE"; st_.extrapolation = "HOLD"
for o in mmeshes:
    vis(o, BATHR if any(k in o.name for k in ("Pants", "Sneakers")) else ROOM + BATHR, recursive=False)
# yopiq ko'zlar (uxlayotganda): ko'z soqqasi orollari nusxasi 1.14x, teri materiali (CLAUDE.md: yelim.py usuli)
def closed_eyes(body):
    sc.frame_set(1); bpy.context.view_layer.update()
    M_ = mroot.matrix_world.inverted() @ body.matrix_world
    bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
    seen = set(); keep = set(); cents = [Vector((0.0324, -0.1185, 1.6211)), Vector((-0.0324, -0.1185, 1.6211))]
    for v in bm.verts:
        if v.index in seen: continue
        isl = []; st = [v]; seen.add(v.index)
        while st:
            x = st.pop(); isl.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        if len(isl) > 3000: continue
        c = sum((M_ @ x.co for x in isl), Vector()) / len(isl)
        for ce in cents:
            if (c - ce).length < 0.02: keep |= {x.index for x in isl}
    print("eye verts", len(keep))
    o = body.copy(); o.data = body.data.copy(); o.name = "meg_lids"; sc.collection.objects.link(o)
    bm2 = bmesh.new(); bm2.from_mesh(o.data); bm2.verts.ensure_lookup_table()
    Mi = M_.inverted()
    for v in bm2.verts:
        if v.index in keep:
            pw = M_ @ v.co; ce = cents[0] if pw.x > 0 else cents[1]
            v.co = Mi @ (ce + (pw - ce) * 1.2)
    bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if v.index not in keep], context="VERTS")
    bm2.to_mesh(o.data); bm2.free(); bm.free()
    skin = mat("lid_skin", (0.37, 0.2, 0.15), 0.55, sss=0.15, sss_scale=0.002)
    o.data.materials.clear(); o.data.materials.append(skin)
    for pl in o.data.polygons: pl.material_index = 0
    return o
lids = closed_eyes(next(o for o in mmeshes if "body" in o.name.lower()))
vis(lids, ROOM, recursive=False)
headE = child_of_bone("meg_head", meg, "Head")
lash_m = mat("lashline", (0.03, 0.02, 0.015), 0.5)
for sx in (1, -1):
    pts = [Vector((sx * 0.033 + sx * 0.0128 * math.cos(a), 0.0855 - 0.004 * math.sin(a), 0.1355 + 0.0115 * math.sin(a))) for a in [math.pi * i / 8 for i in range(9)]]
    lt = PT.tube(f"lashline{sx}", pts, 0.0008, lash_m, headE); vis(lt, ROOM, recursive=False)
BODY = next(o for o in mmeshes if "body" in o.name.lower())
print("MEG meshes", [o.name for o in mmeshes])
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
mouthT = empty("mouthT", (0.0, 0.022, 0.118), headE)
_t1 = empty("_t1", (0.05, 0.05, 0.1), headE); _t2 = empty("_t2", (-0.05, 0.05, 0.1), headE)
sc.frame_set((S["sweat"][0] + S["sweat"][1]) // 2); bpy.context.view_layer.update()
CS_ = 1 if _t1.matrix_world.translation.z > _t2.matrix_world.translation.z else -1      # tepadagi yonoq
print("upper cheek sign", CS_)
cheekT = empty("cheekT", (0.05 * CS_, 0.05, 0.1), headE)
def wp(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wp(faceT, (a + b) // 2) for n, (a, b) in S.items() if n in ROOMN + BATHN}
print("FACE", {k_: tuple(round(x, 3) for x in v) for k_, v in FACE.items()})
HEADW = wp(headE, S["hook"][0] + 10)
# yostiq va ko'rpa
pil = R_(box("pillow", (0.66, 0.42, 0.13), (BED.x, HEADW.y + 0.03 * HEAD_SIGN, MTOP + 0.05), pillow_m, bevel=0.045))
pil.modifiers.new("sub", "SUBSURF").levels = 2
_pl = HEADW - pil.location
pillow_m.node_tree.nodes["cx"].outputs[0].default_value = _pl.x + 0.06
pillow_m.node_tree.nodes["cy"].outputs[0].default_value = _pl.y
TL0, TL1 = S["tlapse"]
val_key(pillow_m, "dirt", 1, 1.0); val_key(pillow_m, "dirt", TL0, 0.05)
for i in range(7):
    val_key(pillow_m, "dirt", TL0 + 2 + int((TL1 - TL0 - 4) * (i + 1) / 7), 0.05 + 0.95 * (i + 1) / 7)
interp(pillow_m.node_tree, "CONSTANT")
sc.frame_set(60); bpy.context.view_layer.update()
BPTS = []
for bn in ("Hips", "Spine", "Spine1", "Spine2", "LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg", "LeftFoot", "RightFoot"):
    pb = meg.pose.bones["mixamorig:" + bn]
    for t_ in (0.0, 0.5):
        BPTS.append(meg.matrix_world @ pb.head.lerp(pb.tail, t_))
SPY = (meg.matrix_world @ meg.pose.bones["mixamorig:Spine2"].head).y
def blanket_mesh():
    n_x, n_y = 70, 80; bm = bmesh.new(); vs = []
    y0 = BED.y - 1.05 * HEAD_SIGN; y1 = SPY + 0.08 * HEAD_SIGN
    for j in range(n_y):
        for i in range(n_x):
            x = BED.x - 0.8 + 1.6 * i / (n_x - 1); y = y0 + (y1 - y0) * j / (n_y - 1)
            dx = abs(x - BED.x)
            z = MTOP + 0.03
            for bp_ in BPTS:
                d2 = (x - bp_.x) ** 2 + (y - bp_.y) ** 2
                z = max(z, MTOP + 0.03 + min(0.2, (bp_.z - MTOP) * 0.8 + 0.07) * math.exp(-d2 / (2 * 0.17 ** 2)))
            if dx > 0.72: z = min(z, MTOP + 0.02) - (dx - 0.72) * 1.2
            z += 0.012 * math.sin(x * 23 + y * 7) * math.sin(y * 11)
            vs.append(bm.verts.new((x, y, z)))
    for j in range(n_y - 1):
        for i in range(n_x - 1):
            a = j * n_x + i; bm.faces.new((vs[a], vs[a + 1], vs[a + n_x + 1], vs[a + n_x]))
    me = bpy.data.meshes.new("blanket"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("blanket", me); sc.collection.objects.link(o); me.materials.append(blanket_m); smooth(o)
    o.modifiers.new("so", "SOLIDIFY").thickness = 0.03
    return o
blk = R_(blanket_mesh())
for o in room_objs: vis(o, ROOM)

# ter/yog' tomchilari (yuzda), so'lak tomchilari (og'izdan)
water_m = mat("sweat", (1.0, 1.0, 1.0), 0.0, trans=1.0, ior=1.33)
oil_m = mat("oil", (1.0, 0.9, 0.6), 0.0, trans=1.0, ior=1.47)
SW0, SW1 = S["sweat"]
rs = random.Random(5); sweat = []
for i in range(34):
    a = rs.uniform(0, 6.28); d = rs.uniform(0.0, 0.055)
    p_ = Vector((0.045 * CS_ + math.cos(a) * d * 0.8, 0.07 + math.sin(a) * d, 0.0))
    p_.z = 0.105 - 0.25 * (p_.x ** 2 + (p_.y - 0.07) ** 2) * 6
    o = sphere(f"sweat{i}", rs.uniform(0.0012, 0.003), tuple(p_), water_m if i % 3 else oil_m, sub=3, parent=headE)
    o.scale = (1, 1, 0.4)
    U.pop(o, SW0 + rs.randint(0, 24), 8, s1=(1, 1, 0.4))
    sw_ = o.constraints.new("SHRINKWRAP"); sw_.target = BODY; sw_.shrinkwrap_type = "NEAREST_SURFACE"; sw_.distance = 0.0008
    sweat.append(o)
    vis(o, [S["sweat"]], recursive=False)
SA0, SA1 = S["saliva"]
FDIR0 = Vector((0.83, -0.08, 0.55))
sal_m = mat("saliva_m", (0.9, 0.95, 1.0), 0.05, alpha=0.6, coat=1.0, ior=1.33, emit=2.0, emit_col=(0.75, 0.88, 1.0))
saliva = []
for i in range(46):
    o = sphere(f"sal{i}", rs.uniform(0.0018, 0.004), (0, 0, 0), sal_m, sub=2)
    t0 = SA0 + rs.randint(0, SA1 - SA0 - 14); dur = rs.randint(10, 18)
    p0 = wp(mouthT, t0); vdir = FDIR0 * rs.uniform(0.5, 1.0) + Vector((rs.uniform(-0.1, 0.1), rs.uniform(-0.15, 0.1), rs.uniform(0.0, 0.25)))
    for f_ in range(t0, t0 + dur + 1, 2):
        t = (f_ - t0) / 24.0
        key(o, f_, loc=tuple(p0 + vdir * t * 0.6 + Vector((0, 0, -2.2 * t * t))))
    interp(o, "LINEAR", "location")
    frames = set(range(t0, t0 + dur + 1))
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=t0)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=t0 + dur + 1); ckey(o, "hide_render")
    saliva.append(o)
# husnbuzarlar (hammomda, yonoqlarda)
pimp_m = mat("pimple", (0.7, 0.08, 0.06), 0.3, sss=0.3, coat=0.4)
pimp_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.002
head_m = mat("pimple_head", (0.95, 0.88, 0.62), 0.3, sss=0.3, coat=0.5)
pimples = []
for i, (x, y, z, r_) in enumerate(((0.052, 0.045, 0.098, 0.0042), (0.06, 0.03, 0.09, 0.0032), (0.042, 0.022, 0.108, 0.003),
                                  (-0.052, 0.045, 0.098, 0.004), (-0.058, 0.025, 0.092, 0.0035), (-0.035, 0.06, 0.115, 0.0028),
                                  (0.012, 0.13, 0.12, 0.003), (0.064, 0.055, 0.085, 0.0028))):
    o = sphere(f"pimple{i}", r_ * 2.0, (x, y, z), pimp_m, scale=(1, 1, 0.6), sub=3, parent=headE); pimples.append(o)
    sw_ = o.constraints.new("SHRINKWRAP"); sw_.target = BODY; sw_.shrinkwrap_type = "NEAREST_SURFACE"; sw_.distance = 0.0
    if i % 3 == 0:
        o2 = sphere(f"pimpleh{i}", r_ * 0.55, (x, y, z), head_m, sub=2, parent=headE); pimples.append(o2)
        sw_ = o2.constraints.new("SHRINKWRAP"); sw_.target = BODY; sw_.shrinkwrap_type = "NEAREST_SURFACE"; sw_.distance = r_ * 0.5
for o in pimples: vis(o, BATHR, recursive=False)

# ======================================================================
# 3) ISSIQLIK KAMERASI: xona va Megan materiallariga "th" aralashmasi (emissiya, issiqlik ranglari)
# ======================================================================
TH0, TH1 = S["thermal"]
def thermalize(m, heat):
    if not m or not m.use_nodes or m.get("thermal"): return
    m["thermal"] = 1
    N = m.node_tree.nodes; L = m.node_tree.links
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    h = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", 0.55, P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], -0.45 * -1)), heat),
                 P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.12))
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
    stops = [(0.0, (0.0, 0.0, 0.05)), (0.25, (0.12, 0.0, 0.45)), (0.5, (0.8, 0.0, 0.35)), (0.68, (1.0, 0.25, 0.0)), (0.85, (1.0, 0.75, 0.0)), (1.0, (1.0, 1.0, 0.85))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p_, c_ in stops[1:-1]: e = cr.elements.new(p_); e.color = (*c_, 1)
    L.new(h, ramp.inputs[0])
    em = N.new("ShaderNodeEmission"); L.new(ramp.outputs[0], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.6
    th = value_node(m, "th", 0.0)
    mx = N.new("ShaderNodeMixShader"); L.new(th, mx.inputs[0])
    if src: L.new(src, mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    val_key(m, "th", 1, 0.0); val_key(m, "th", TH0, 1.0); val_key(m, "th", TH1 + 1, 0.0)
    for fc in fcurves(m.node_tree):
        if 'nodes["th"]' in fc.data_path:
            for k_ in fc.keyframe_points: k_.interpolation = "CONSTANT"
def mats_of(objs):
    out = set()
    for o in objs:
        for x in [o] + list(o.children_recursive):
            if x.type in ("MESH", "CURVE", "FONT"):
                for s in x.material_slots:
                    if s.material: out.add(s.material)
    return out
for m in mats_of(mmeshes): thermalize(m, 0.7 if "hair" in m.name.lower() else 1.05)
thermalize(pillow_m, 0.9); thermalize(blanket_m, 0.66)
for m in mats_of([bed_grp]): thermalize(m, 0.22)
for m in mats_of(room_objs): thermalize(m, 0.06)

# ======================================================================
# 4) UNITAZ (sovuq hojatxona) va PETRI IDISHLARI (laboratoriya stoli)
# ======================================================================
TOI = Vector((-40.0, 0.0, 0.0))
toil_objs = []
tile_m = pbr("toi_tile", "interior_tiles", 0.9)
toil_objs.append(plane("t_floor", (3, 3), tuple(TOI), tile_m))
toil_objs.append(box("t_wall", (3, 0.1, 2.6), tuple(TOI + V(0, 0.72, 1.3)), tile_m))
toil_objs.append(box("t_wallL", (0.1, 3, 2.6), tuple(TOI + V(-1.0, 0, 1.3)), tile_m))
toiletE = empty("toilet", tuple(TOI + V(0, 0.66, 0))); import_gltf(BK + "6a342733_u.glb", toiletE); toil_objs.append(toiletE)
toil_objs.append(cyl("t_roll", 0.055, 0.1, tuple(TOI + V(-0.94, 0.25, 0.75)), mat("paper_m", (0.95, 0.95, 0.93), 0.8), rot=(0, 90, 0)))
for o in toil_objs: vis(o, [S["toilet"]])
LAB = Vector((-40.0, 20.0, 0.0))
lab_objs = []
lab_objs.append(box("lab_table", (3.0, 1.6, 0.06), tuple(LAB + V(0, 0, 0.87)), mat("lab_top", (0.88, 0.9, 0.92), 0.25, coat=0.4)))
lab_objs.append(plane("lab_floor", (8, 8), tuple(LAB), mat("lab_floor_m", (0.25, 0.27, 0.3), 0.6)))
lab_objs.append(box("lab_wall", (8, 0.1, 4), tuple(LAB + V(0, 1.6, 2)), mat("lab_wall_m", (0.12, 0.16, 0.2), 0.7)))
glass_m = mat("petri_glass", (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=1.5)
agar_m = mat("agar", (0.72, 0.42, 0.12), 0.15, sss=0.6, trans=0.3, coat=0.8)
agar_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.01
col_ms = [mat("col_cream", (0.9, 0.82, 0.55), 0.25, sss=0.4, coat=0.8), mat("col_yel", (0.95, 0.75, 0.15), 0.2, sss=0.4, coat=0.8),
          mat("col_white", (0.92, 0.9, 0.85), 0.3, sss=0.4, coat=0.8), mat("col_orng", (0.9, 0.42, 0.1), 0.2, sss=0.4, coat=0.8),
          mat("col_green", (0.45, 0.6, 0.2), 0.25, sss=0.4, coat=0.8)]
for m in col_ms: m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.003
TZ = 0.9
DL, DR = LAB + V(-0.32, 0.0, TZ), LAB + V(0.32, 0.0, TZ)
rp = random.Random(9); colonies = []
PE0, PE1 = S["petri"]
for nm, c_, n_ in (("L", DL, 5), ("R", DR, 420)):
    d_ = empty("dish" + nm, tuple(c_)); lab_objs.append(d_)
    cyl("dish_base" + nm, 0.2, 0.004, (0, 0, 0.002), glass_m, parent=d_, verts=64)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.2, depth=0.03, end_fill_type="NOTHING"); w_ = bpy.context.object
    w_.name = "dish_wall" + nm; w_.location = (0, 0, 0.015); w_.data.materials.append(glass_m); w_.parent = d_
    w_.modifiers.new("so", "SOLIDIFY").thickness = 0.003; smooth(w_)
    cyl("agar" + nm, 0.196, 0.012, (0, 0, 0.01), agar_m, parent=d_, verts=64)
    for i in range(n_):
        a = rp.uniform(0, 6.28); rr = 0.18 * math.sqrt(rp.random())
        r_ = rp.uniform(0.004, 0.018) if nm == "R" else rp.uniform(0.01, 0.016)
        if nm == "R" and rp.random() < 0.1: r_ = rp.uniform(0.02, 0.03)
        o = sphere(f"col{nm}{i}", r_, (math.cos(a) * rr, math.sin(a) * rr, 0.016), rp.choice(col_ms), scale=(1, 1, 0.35), sub=2, parent=d_)
        if nm == "R":
            U.pop(o, PE0 + 2 + int((PE1 - PE0 - 14) * (i / n_) ** 0.6), 6, s1=(1, 1, 0.35))
        colonies.append(o)
lbl_m = mat("lbl", (0.05, 0.05, 0.06), 0.5)
lab_objs.append(text("lblL", "UNITAZ", 0.055, tuple(DL + V(0, -0.27, -0.025)), (90, 0, 0), lbl_m))
lab_objs.append(text("lblR", "YOSTIQ", 0.055, tuple(DR + V(0, -0.27, -0.025)), (90, 0, 0), lbl_m))
big_m = mat("big_txt", (1.0, 0.25, 0.1), 0.4, emit=2.2, emit_col=(1.0, 0.2, 0.05))
big = text("big17", "17 000×", 0.22, tuple(LAB + V(0.0, 0.3, TZ + 0.3)), (75, 0, 0), big_m, extrude=0.02)
big.scale = (0.001,) * 3; big.keyframe_insert("scale", frame=F_17 - 1)
big.scale = (1.25,) * 3; big.keyframe_insert("scale", frame=F_17 + 3); big.scale = (1.0,) * 3; big.keyframe_insert("scale", frame=F_17 + 7)
lab_objs.append(big)
for o in lab_objs: vis(o, [S["petri"]])

# ======================================================================
# 5) MIKRO MATO (1000x): to'qilgan iplar, bakteriyalar, qipiqlar, chang, so'lak, zamburug'
#    mahalliy o'qlar (fabE): mato z ~ 0, maydon -7..7
# ======================================================================
MIC = V(0.0, 60.0, 0.0)
fabE = empty("fabE", tuple(MIC))
fab_m = U.fabric_material()
threads, BVH = U.weave("thr", 14.0, 0.9, 0.42, fab_m, fabE)
val_key(fab_m, "dirt", 1, 0.85)
fuzz_m = M.hair_material("fuzz", (0.9, 0.88, 0.82), 0.6, trans=0.4)
fuzzes = U.fuzz("fuzz", BVH, 70, fuzz_m, fabE, (-6.5, 6.5, -6.5, 6.5), hair_fn=M.hair)
fab_static = threads + fuzzes
bk = U.BKit()
def FP(x, y, z=0.0): return MIC + V(x, y, z)
A_C, B_C, D_C, C_C, E_C = (-3.5, -3.5), (3.5, -3.5), (3.5, 3.5), (-3.5, 3.0), (0.2, 0.6)
bg_b = U.scatter_bacteria(bk, "bbg", BVH, 520, (-6.8, 6.8, -6.8, 6.8), fabE, seed=2)
dense = U.scatter_bacteria(bk, "bA", BVH, 950, (-6.5, -0.5, -6.5, -0.5), fabE, seed=3, clump=0.75,
                           centers=[(-3.5, -3.5, 1.2), (-2.2, -4.6, 0.7), (-4.8, -2.2, 0.8), (-2.6, -2.4, 0.6), (-4.2, -4.8, 0.7)])
fab_static += bg_b + dense
# bakteriyalar ko'payishi (breed): urug'lardan atrofga tarqaladi, eksponensial vaqt
BR0, BR1 = S["breed"]
rb = random.Random(31); born = [(C_C[0] + rb.uniform(-0.4, 0.4), C_C[1] + rb.uniform(-0.4, 0.4)) for _ in range(6)]
NB = 760
for i in range(NB - 6):
    px, py = rb.choice(born); a = rb.uniform(0, 6.28); d = rb.uniform(0.1, 0.2)
    born.append((px + math.cos(a) * d, py + math.sin(a) * d))
breed = []
for i, (x, y) in enumerate(born):
    o = U.scatter_bacteria(bk, f"br{i}_", BVH, 1, (x, x, y, y), fabE, seed=100 + i, kinds=("acne", "acne", "rod", "coc"))[0]
    fb = BR0 + 2 + int((BR1 - BR0 - 14) * math.log(1 + i) / math.log(NB))
    U.pop(o, fb, 5)
    breed.append(o)
    vis(o, [S["breed"]], recursive=False)
# o'lik teri qipiqlari yog'iladi (flakes)
FL0, FL1 = S["flakes"]
flake_m = M.skin_micro_material("flake_m")
fme = bpy.data.meshes.new("flake")
_bm = bmesh.new(); bmesh.ops.create_cone(_bm, cap_ends=True, segments=7, radius1=1.0, radius2=0.9, depth=0.07)
for v in _bm.verts: v.co.x *= 1 + 0.25 * math.sin(v.co.y * 3); v.co.z += 0.12 * (v.co.x ** 2 - v.co.y ** 2) * 0.5
_bm.to_mesh(fme); _bm.free(); fme.materials.append(flake_m)
rfl = random.Random(41); flakes_ = []
for i in range(46):
    o = PT.link(bpy.data.objects.new(f"flk{i}", fme), fabE)
    s_ = rfl.uniform(0.18, 0.42); o.scale = (s_, s_ * rfl.uniform(0.6, 1.0), s_)
    x = B_C[0] + rfl.uniform(-2.2, 2.2); y = B_C[1] + rfl.uniform(-2.2, 2.2); z, _ = U.top_z(BVH, x, y)
    o.rotation_euler = (rfl.uniform(-1, 1), rfl.uniform(-1, 1), rfl.uniform(0, 6))
    t0 = FL0 - 40 + rfl.randint(0, 50)
    U.fall(o, t0, t0 + rfl.randint(22, 34), (x + rfl.uniform(-0.6, 0.6), y + rfl.uniform(-0.6, 0.6), z + rfl.uniform(3.5, 6)), (x, y, z + 0.03), rfl.uniform(-2, 2))
    flakes_.append(o)
# soch tolasi va chang (dust)
DU0, DU1 = S["dust"]
hair_m = M.hair_material("big_hair", (0.12, 0.07, 0.04), 0.35)
bighair = M.hair("bighair", (B_C[0] - 3.0, B_C[1] + 3.4, 1.6), (1.0, 0.25, 0.08), 6.5, 0.3, hair_m, fabE, bend=Vector((0, 0, -0.4)), depth=0.0)
dust_ms = [mat("dust_g", (0.35, 0.33, 0.3), 0.85), mat("dust_b", (0.28, 0.2, 0.14), 0.85), mat("dust_w", (0.7, 0.68, 0.62), 0.8)]
rdu = random.Random(51); dusts = []
for i in range(60):
    me = U.dust_mesh(f"dust{i}", seed=i); me.materials.append(rdu.choice(dust_ms))
    o = PT.link(bpy.data.objects.new(f"dust{i}", me), fabE); s_ = rdu.uniform(0.03, 0.11); o.scale = (s_,) * 3
    t = rdu.uniform(0.15, 0.95); hp_ = Vector((B_C[0] - 3.0, B_C[1] + 3.4, 1.6)) + Vector((1.0, 0.25, 0.08)).normalized() * 6.5 * t
    x, y = hp_.x + rdu.uniform(-0.3, 0.3), hp_.y + rdu.uniform(-0.3, 0.3); z, _ = U.top_z(BVH, x, y)
    t0 = DU0 - 6 + rdu.randint(0, 22)
    o.location = (hp_.x, hp_.y, hp_.z - 0.3); o.keyframe_insert("location", frame=1)
    U.fall(o, t0, t0 + rdu.randint(16, 26), (hp_.x, hp_.y, hp_.z - 0.28), (x, y, z + s_ * 0.8), rdu.uniform(-3, 3))
    dusts.append(o)
# so'lak tomchilari matoga singadi (soak)
SO0, SO1 = S["soak"]
dropm = mat("drop_m", (0.9, 0.95, 1.0), 0.0, alpha=0.3, coat=1.0, ior=1.33)
rso = random.Random(61); drops = []
for i in range(9):
    a = rso.uniform(0, 6.28); d = rso.uniform(0, 1.6) if i else 0.0
    x, y = D_C[0] + math.cos(a) * d, D_C[1] + math.sin(a) * d; z, _ = U.top_z(BVH, x, y)
    r_ = rso.uniform(0.35, 0.6) if i == 0 else rso.uniform(0.15, 0.35)
    o = sphere(f"drop{i}", r_, (x, y, z + r_ * 0.55), dropm, scale=(1, 1, 0.72), sub=4, parent=fabE)
    ts = SO0 + 8 + rso.randint(0, 12)
    for f_, s_, zz in ((1, 1.0, 0.72), (ts, 1.0, 0.72), (ts + 22, 0.55, 0.28), (SO1 - 2, 0.15, 0.06)):
        o.scale = (s_, s_, zz * s_); o.keyframe_insert("scale", frame=f_)
        o.location.z = z + r_ * zz * s_ * 0.6; o.keyframe_insert("location", frame=f_)
    drops.append(o)
for nm, v in (("wx", D_C[0]), ("wy", D_C[1])): val_key(fab_m, nm, 1, v)
val_key(fab_m, "wet", 1, 0.0); val_key(fab_m, "wet", SO0, 1.0); val_key(fab_m, "wet", SO1 + 1, 0.0)
val_key(fab_m, "wr", 1, 0.0); val_key(fab_m, "wr", SO0 + 8, 0.0); val_key(fab_m, "wr", SO1, 1.9)
for fc in fcurves(fab_m.node_tree):
    if 'nodes["wet"]' in fc.data_path:
        for k_ in fc.keyframe_points: k_.interpolation = "CONSTANT"
# zamburug' gifalari (fungi)
FU0, FU1 = S["fungi"]
hy_m = U.hypha_material()
hyph, tips = U.hyphae("hy", BVH, E_C, 18, hy_m, fabE, PT.tube, seed=7, step=0.14, nsteps=30, r=0.045)
val_key(hy_m, "grow", 1, 0.0); val_key(hy_m, "grow", FU0 - 30, 0.15); val_key(hy_m, "grow", FU1, 1.0)
spore_m = mat("spore", (0.15, 0.32, 0.12), 0.4, sss=0.3, coat=0.5)
spores = []
for i, tp in enumerate(tips):
    o = sphere(f"spore{i}", 0.08, tuple(tp + Vector((0, 0, 0.06))), spore_m, sub=3, parent=fabE)
    U.pop(o, FU1 - 8 + (i % 5), 5); spores.append(o)
# ulkan teri (press, smear): ostki tomoni bilan matoga tushadi; ostida yopishgan bakteriyalar
SKN_PORES = [(rx, ry, 0.14, 0.4) for rx, ry in ((-1.2, -0.6), (0.8, 1.1), (1.6, -1.4), (-0.4, 1.8), (-1.8, 1.2), (0.3, -1.9))]
SKN_PORES = [(rx * 1.1, ry * 1.1, r_ * 1.4, d_) for rx, ry, r_, d_ in SKN_PORES]
SKa = M.Skin(5.6, SKN_PORES, seed=4)
skin_m = M.skin_micro_material()
gskin = empty("gskin", (A_C[0], A_C[1], 4.0), fabE); gskin.rotation_euler = (R(180), 0, 0)
gsurf = M.skin_surface("gsurf", SKa, 0.04, skin_m, gskin)
_so = gsurf.modifiers.new("so", "SOLIDIFY"); _so.thickness = 0.5; _so.offset = -1
glued = []
rg = random.Random(71)
for i in range(700):
    o = bk.new(f"glued{i}", rg.choice(("rod", "acne", "coc")), gskin)
    x, y = rg.uniform(-2.6, 2.6), rg.uniform(-2.6, 2.6)
    o.location = (x, y, SKa.H(x, y) + 0.02); s_ = rg.uniform(0.8, 1.2); o.scale = (s_,) * 3
    o.rotation_euler = (R(rg.uniform(-10, 10)), R(rg.uniform(-10, 10)), rg.uniform(0, 6.28))
    glued.append(o)
PR0, PR1 = S["press"]; SM0, SM1 = S["smear"]
TOPZ = 0.62
for f_, z_, xo in ((1, 4.0, 0.0), (F_PRESS - 26, 4.0, 0.0), (F_PRESS, TOPZ, 0.0), (PR1, TOPZ - 0.03, 0.0),
                   (SM0, 0.95, -1.3), (SM1, 0.95, 0.9)):
    gskin.location = (A_C[0] + xo, A_C[1], z_); gskin.keyframe_insert("location", frame=f_)
for fc in fcurves(gskin):
    for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
    for k_ in fc.keyframe_points:
        if int(k_.co.x) == SM0: k_.interpolation = "LINEAR"
for k_ in [k_ for fc in fcurves(gskin) for k_ in fc.keyframe_points if int(k_.co.x) == PR1]: k_.interpolation = "CONSTANT"
vis(gskin, rng("press", "smear"))
for o in fab_static + flakes_ + [bighair] + dusts + drops + hyph + spores: vis(o, FAB, recursive=False)
for o in [bighair] + dusts: vis(o, [S["dust"]], recursive=False)
for o in flakes_: vis(o, [S["flakes"]], recursive=False)
for o in drops: vis(o, [S["soak"]], recursive=False)
for o in hyph + spores: vis(o, rng("fungi", "breed"), recursive=False)

# ======================================================================
# 6) MIKRO TERI (teshiklar): bakteriyalar ip bosimi bilan teshikka kiradi
# ======================================================================
SKW = V(60.0, 60.0, 0.0)
skE = empty("skE", tuple(SKW))
pores = [(0.0, 0.0, 0.62, 1.1)]
rp2 = random.Random(81)
for _ in range(220):
    x, y = rp2.uniform(-4.6, 4.6), rp2.uniform(-4.6, 4.6)
    if all(math.hypot(x - a, y - b) > 1.0 for a, b, *_ in pores): pores.append((x, y, rp2.uniform(0.12, 0.2), 0.6))
SKb = M.Skin(10.0, pores, seed=3)
ssurf = M.skin_surface("ssurf", SKb, 0.03, skin_m, skE)
sflk = M.flakes("sflake", SKb, 50, flake_m, skE)
vh_m = M.hair_material("vellus", (0.5, 0.36, 0.24), 0.35, trans=0.5)
shairs = [M.hair(f"vh{i}", (x, y, SKb.H(x, y) - 0.05), (rp2.uniform(-0.5, 0.5), rp2.uniform(-0.5, 0.5), 1), rp2.uniform(1.0, 2.2), 0.035, vh_m, skE,
                 bend=Vector((0, 0, -0.25)), depth=0.5) for i, (x, y, r_, d_) in enumerate(pores[1:40])]
PO0, PO1 = S["pores"]
inpore = []
for i in range(70):
    a = rp2.uniform(0, 6.28); d0 = rp2.uniform(0.7, 1.9)
    o = bk.new(f"ip{i}", rp2.choice(("acne", "acne", "rod", "coc")), skE); s_ = rp2.uniform(0.9, 1.4); o.scale = (s_,) * 3
    ts = PO0 + 10 + rp2.randint(0, 34); dur = rp2.randint(14, 22)
    for f_ in list(range(PO0, PO1 + 2, 2)):
        t = max(0.0, min(1.0, (f_ - ts) / dur)); t = t * t * (3 - 2 * t)
        d = d0 * (1 - t) + 0.05 * t; x, y = math.cos(a) * d, math.sin(a) * d
        dep = max(0.0, (t - 0.55) / 0.45) * rp2.uniform(0.4, 0.9) if t > 0.55 else 0.0
        o.location = (x, y, SKb.H(x, y) + 0.03 - dep * 0.9 if d > 0.3 else -0.25 - dep * 0.6)
        o.rotation_euler = (R(60 * t), 0, a + math.pi / 2); o.keyframe_insert("location", frame=f_); o.keyframe_insert("rotation_euler", frame=f_)
    interp(o, "LINEAR", "location"); inpore.append(o)
for i in range(160):
    x, y = rp2.uniform(-4, 4), rp2.uniform(-4, 4)
    if math.hypot(x, y) < 2.0: continue
    o = bk.new(f"sb{i}", rp2.choice(("acne", "rod", "coc")), skE); o.location = (x, y, SKb.H(x, y) + 0.03)
    o.rotation_euler = (0, 0, rp2.uniform(0, 6.28)); inpore.append(o)
# teshik ustidan sirpanib bosuvchi ulkan iplar
thr_g = empty("thr_g", (0, 0, 0), skE)
for k in range(3):
    pts = [Vector((-6 + i * 0.25, k * 0.95, 0.0)) for i in range(49)]
    me = U.tube_mesh(f"pthr{k}", pts, 0.42, 0.28); me.materials.append(fab_m)
    PT.link(bpy.data.objects.new(f"pthr{k}", me), thr_g)
for f_, y_, z_ in ((PO0, 3.4, 1.2), (PO0 + 24, 2.2, 0.42), (PO1, 0.75, 0.38)):
    thr_g.location = (0, y_, z_); thr_g.keyframe_insert("location", frame=f_)
interp(thr_g, "LINEAR", "location")
for o in [skE]: vis(o, [S["pores"]])

# ======================================================================
# 7) KESIM: teri va teshik, ichida bakteriyalar, yallig'lanish (qizil nur), yiring, teri bo'rtadi
#    mahalliy o'qlar (cutE): tepa = +Z (teri yuzasi z=0), kesim tekisligi x = 0, kamera +X tomonda
# ======================================================================
CUT = V(60.0, 0.0, 0.0)
cutE = empty("cutE", tuple(CUT))
cutm = M.cut_material()
blk_c = box("skin_block", (1.6, 4.4, 2.6), (-0.8, 0.0, -1.3), cutm)
AX = Vector((0, 0.0, -1)).normalized(); FOLL_D = 1.5
def AP(d, y=0.0, x=0.0): return AX * d + Vector((x, y, 0))
cutter = cyl("canal_cut", 0.2, FOLL_D + 0.6, (0, 0, -(FOLL_D / 2 - 0.25)), cutm, verts=48)
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.2, radius2=0.42, depth=0.42, location=(0, 0, -0.17))
funnel = bpy.context.object; funnel.name = "funnel_cut"
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.55, location=(0, 0, -FOLL_D + 0.05))
pocket = bpy.context.object; pocket.name = "pocket_cut"; pocket.scale = (1, 1.15, 0.8)
for ct in (cutter, funnel, pocket):
    bo = blk_c.modifiers.new("b_" + ct.name, "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = ct; bo.solver = "EXACT"
    bo.use_self = True; bo.use_hole_tolerant = True
    ct.hide_render = True; ct.hide_viewport = True
bpy.context.view_layer.objects.active = blk_c
for o in bpy.context.view_layer.objects: o.select_set(False)
blk_c.select_set(True)
for md in list(blk_c.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
for o in (cutter, funnel, pocket): bpy.data.objects.remove(o)
blk_c.parent = cutE
cut_objs = [blk_c]
IN0, IN1 = S["inflame"]
# teri bo'rtishi: kesilgan yarim gumbaz (teri rangi)
bump_m = mat("bump_m", (0.75, 0.4, 0.33), 0.35, sss=0.5, coat=0.4)
bump_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.05
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.8); bmp = bpy.context.object; bmp.name = "bump"
M.bisect_keep_neg_x(bmp)
bmp.data.materials.append(bump_m); smooth(bmp); bmp.parent = cutE
for f_, s_ in ((1, 0.05), (IN0, 0.05), (F_PUS, 0.18), (IN1, 0.4)):
    bmp.scale = (1, 1, s_); bmp.keyframe_insert("scale", frame=f_)
cut_objs.append(bmp)
# yallig'lanish nuri (qizil) va yiring
infl_m = glow_mat("infl", (1.0, 0.08, 0.03))
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0); infl = bpy.context.object; infl.name = "infl"
M.bisect_keep_neg_x(infl, fill=False); infl.data.materials.append(infl_m); smooth(infl); infl.parent = cutE
infl.location = (0, 0, -FOLL_D + 0.15)
for f_, s_, a_ in ((1, 0.3, 0.0), (IN0 + 6, 0.35, 0.3), (F_PUS, 0.8, 2.0), (IN1, 1.05, 2.6)):
    infl.scale = (s_, s_ * 1.2, s_); infl.keyframe_insert("scale", frame=f_); val_key(infl_m, "a", f_, a_)
cut_objs.append(infl)
pus_m = mat("pus", (0.95, 0.86, 0.45), 0.25, sss=0.6, coat=0.7)
pus_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.03
rpu = random.Random(91); pus = []
for i in range(9):
    c_ = Vector((rpu.uniform(-0.3, -0.02), rpu.uniform(-0.25, 0.25), -FOLL_D + 0.05 + rpu.uniform(-0.15, 0.25)))
    o = sphere(f"pus{i}", rpu.uniform(0.12, 0.22), tuple(c_), pus_m, sub=3, parent=cutE)
    U.pop(o, F_PUS - 6 + i * 3, 14); pus.append(o)
cbact = []
for i in range(140):
    z = rpu.uniform(-FOLL_D + 0.1, -0.15); rr = 0.17 if z > -FOLL_D + 0.55 else 0.42
    a = rpu.uniform(math.pi / 2, 3 * math.pi / 2); d = rr * math.sqrt(rpu.random())
    o = bk.new(f"cb{i}", rpu.choice(("acne", "acne", "rod", "coc")), cutE); s_ = rpu.uniform(0.7, 1.1); o.scale = (s_,) * 3
    o.location = (math.cos(a) * d * 0.9 - 0.02, math.sin(a) * d, z); o.rotation_euler = (rpu.uniform(0, 3), rpu.uniform(0, 3), rpu.uniform(0, 3))
    U.pop(o, IN0 + int(50 * (i / 140) ** 0.7), 5); cbact.append(o)
vessel_m = mat("vessel", (0.55, 0.03, 0.03), 0.3, sss=0.4, coat=0.4)
for i, pts in enumerate(([(0, -2.1, -0.6), (0, -1.2, -0.72), (0, -0.7, -0.5)], [(0, 2.1, -1.2), (0, 1.3, -1.05), (0, 0.8, -1.3)],
                         [(0, -2.1, -2.1), (0, -1.0, -1.95), (0, 0.9, -2.3)])):
    cut_objs.append(PT.tube(f"vessel{i}", [Vector(p) + Vector((0.005, 0, 0)) for p in pts], 0.04, vessel_m, cutE))
for o in cut_objs + pus + cbact: vis(o, [S["inflame"]], recursive=False)

# ======================================================================
# 8) HAMMOM: plitka, oyna, lavabo, qimmat krem; Megan yuziga krem surtadi
# ======================================================================
bath_objs = []
def B_(o): bath_objs.append(o); return o
tile_w = pbr("tile_w", "long_white_tiles", 1.4); tile_f = pbr("tile_f", "floor_tiles_06", 1.0)
B_(plane("b_floor", (2.4, 2.4), tuple(BATH + V(0, 0.3, 0)), tile_f))
B_(box("b_wall", (2.4, 0.1, 2.6), tuple(BATH + V(0, -0.8, 1.3)), tile_w))
B_(box("b_wallL", (0.1, 2.4, 2.6), tuple(BATH + V(-1.15, 0.3, 1.3)), tile_w))
B_(box("b_wallR", (0.1, 2.4, 2.6), tuple(BATH + V(1.15, 0.3, 1.3)), tile_w))
B_(box("b_ceil", (2.4, 2.4, 0.05), tuple(BATH + V(0, 0.3, 2.62)), mat("b_ceil_m", (0.92, 0.92, 0.9), 0.8)))
B_(box("vanity", (1.2, 0.5, 0.82), tuple(BATH + V(0, -0.5, 0.41)), mat("vanity", (0.18, 0.2, 0.22), 0.4), bevel=0.01))
CTOP = 0.86
B_(box("counter", (1.26, 0.56, 0.04), tuple(BATH + V(0, -0.48, 0.84)), mat("counter_m", (0.15, 0.15, 0.16), 0.1, coat=0.6), bevel=0.005))
ceramic = mat("ceramic", (0.95, 0.95, 0.94), 0.08, coat=0.8)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.21); bowl = bpy.context.object; bowl.name = "bowl"
bm_ = bmesh.new(); bm_.from_mesh(bowl.data)
bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.z > 0.0], context="VERTS"); bm_.to_mesh(bowl.data); bm_.free()
bowl.scale = (1, 1, 0.62); bowl.location = tuple(BATH + V(-0.2, -0.45, 0.99))
bowl.data.materials.append(ceramic); bowl.modifiers.new("so", "SOLIDIFY").thickness = 0.012; smooth(bowl); B_(bowl)
chrome = mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0)
B_(cyl("tap_post", 0.018, 0.32, tuple(BATH + V(-0.2, -0.7, 1.02)), chrome))
B_(cyl("tap_spout", 0.014, 0.2, tuple(BATH + V(-0.2, -0.61, 1.17)), chrome, rot=(90, 0, 0)))
B_(plane("mirror", (1.0, 0.85), tuple(BATH + V(0, -0.745, 1.58)), mat("mirror", (0.95, 0.95, 0.95), 0.02, metal=1.0), rot=(90, 0, 0)))
B_(box("mirror_light", (0.9, 0.04, 0.03), tuple(BATH + V(0, -0.72, 2.06)), mat("mlight", (1, 0.97, 0.92), 0.5, emit=6.0)))
B_(box("towel", (0.35, 0.06, 0.5), tuple(BATH + V(-0.85, -0.7, 1.2)), mat("towel_m", (0.75, 0.82, 0.88), 0.95), bevel=0.02))
B_(gltf(PH + "potted_plant_01/potted_plant_01.gltf", tuple(BATH + V(0.5, -0.62, CTOP)), 30, 0.45))
# qimmat krem: qora shisha banka, oltin qopqoq, oltin yozuv, narx yorlig'i
JAR = BATH + V(0.22, -0.4, CTOP)
jar = B_(empty("jar", tuple(JAR))); jar.rotation_euler.z = R(125)
gold = mat("gold", (1.0, 0.72, 0.32), 0.18, metal=1.0)
cyl("jar_body", 0.05, 0.06, (0, 0, 0.03), mat("jar_glass", (0.02, 0.02, 0.025), 0.05, coat=1.0), parent=jar, verts=64)
lid = cyl("jar_lid", 0.052, 0.028, (0, 0, 0.074), gold, parent=jar, verts=64)
cyl("jar_cream", 0.044, 0.008, (0, 0, 0.058), mat("cream_in", (0.97, 0.95, 0.92), 0.2, sss=0.3), parent=jar, verts=48)
text("jar_txt", "LUXE", 0.016, (0, -0.0505, 0.032), (90, 0, 0), gold, parent=jar)
text("jar_txt2", "gold serum", 0.007, (0, -0.0505, 0.016), (90, 0, 0), gold, parent=jar)
tag = box("tag", (0.05, 0.002, 0.026), (0.07, -0.03, 0.02), mat("tag_m", (0.95, 0.94, 0.9), 0.6), rot=(0, 0, 20), parent=jar)
text("tag_txt", "$350", 0.011, (0.071, -0.0322, 0.02), (90, 0, 20), mat("tag_t", (0.7, 0.05, 0.03), 0.5), parent=jar)
CR0, CR1 = S["cream"]
lid.location = (0, 0, 0.074); lid.keyframe_insert("location", frame=CR0); lid.rotation_euler = (0, 0, 0); lid.keyframe_insert("rotation_euler", frame=CR0)
lid.location = (0.12, 0.02, -0.0); lid.keyframe_insert("location", frame=CR0 + 20)
lid.rotation_euler = (0, 0, R(220)); lid.keyframe_insert("rotation_euler", frame=CR0 + 20)
for o in bath_objs: vis(o, BATHR)
# krem: yuzda va barmoqlarda
cream_m = mat("cream", (0.98, 0.97, 0.95), 0.25, sss=0.5, coat=0.6)
cream_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.003
rcr = random.Random(11); cream = []
for ci, (c_, sp) in enumerate((((0.05, 0.05, 0.1), 0.018), ((-0.05, 0.05, 0.1), 0.018), ((0, 0.13, 0.115), 0.022))):
    for i in range(10):
        p_ = Vector(c_) + Vector((rcr.uniform(-sp, sp), rcr.uniform(-sp, sp) * 0.7, rcr.uniform(-0.004, 0.003)))
        o = sphere(f"crf{ci}_{i}", rcr.uniform(0.004, 0.008), tuple(p_), cream_m, scale=(1, 0.7, 0.25), sub=3, parent=headE)
        sw_ = o.constraints.new("SHRINKWRAP"); sw_.target = BODY; sw_.shrinkwrap_type = "NEAREST_SURFACE"; sw_.distance = 0.0005
        cream.append(o)
for bone in ("LeftHand", "RightHand"):
    hb = child_of_bone("cream_" + bone, meg, bone)
    for i in range(6):
        p_ = Vector((rcr.uniform(-0.03, 0.03), rcr.uniform(0.06, 0.1), rcr.uniform(-0.02, 0.0)))
        cream.append(sphere(f"crh{bone}{i}", rcr.uniform(0.003, 0.006), tuple(p_), cream_m, scale=(1, 1, 0.4), sub=2, parent=hb))
for o in cream: vis(o, [S["apply"]], recursive=False)

# ======================================================================
# 9) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.005):
    t = empty(name + "_t"); path(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path(c, pts)
    return c
HUP = Vector((0.17, 0.98, -0.12)); FDIR = Vector((0.83, -0.08, 0.55)); HXL = Vector((0.53, -0.2, -0.83))
def look_cam(name, target, lens, fstop, keys, up=HUP, clip=0.003):
    """TRACK_TO siz: kamera -Z nishonga, +Y 'up' ga (yotgan yuz tik ko'rinadi). keys: [(f, offset)] nishondan"""
    c = shot_cam(name, (0, 0, 0), None, lens, fstop, focus=target, clip=clip)
    for f_, off in keys:
        tp = wp(target, f_); loc = tp + Vector(off)
        fw = (tp - loc).normalized(); upv = (up - fw * up.dot(fw)).normalized(); x_ = fw.cross(upv)
        c.rotation_euler = Matrix((x_, upv, -fw)).transposed().to_euler()
        key(c, f_, loc=tuple(loc)); c.keyframe_insert("rotation_euler", frame=f_)
    return c
def rig(name, target):
    e = empty(name + "_rig"); c_ = e.constraints.new("COPY_LOCATION"); c_.target = target; return e
def rel_cam(name, target, lens, fstop, offsets, clip=0.003):
    r_ = rig(name, target)
    c = shot_cam(name, (0, 0, 0), target, lens, fstop, focus=target, clip=clip); c.parent = r_
    path(c, offsets); return c
PIL = Vector((HEADW.x + 0.2, HEADW.y - 0.06, MTOP + 0.12))
FDIR = Vector((0.83, -0.08, 0.55)); CHK_OUT = Vector((-0.53, 0.2, 0.83))
# 1 ILGAK: poldan past burchak, yostiqqa crash zoom
H0, H1 = S["hook"]
c = abs_cam("hook", [(H0, PIL + V(1.5, -1.5, -0.42)), (H0 + 20, PIL + V(1.05, -1.0, -0.2)), (H0 + 26, PIL + V(0.42, -0.36, 0.2)), (H1, PIL + V(0.34, -0.28, 0.18))],
            [(H0, PIL + V(-0.1, 0.0, 0.05)), (H0 + 20, PIL + V(-0.05, 0.0, 0.03)), (H1, PIL + V(0.0, 0.02, 0.0))], 16, 2.8)
lens_keys(c, [(H0, 15), (H0 + 20, 17), (H0 + 26, 26), (H1, 28)]); shake(c, H0 + 25, H0 + 38, 0.03, seed=1)
# 2 timelapse: tepadan sekin aylanma
c = abs_cam("tlapse", [(TL0, HEADW + V(1.3, -1.2, 1.3)), (TL1, HEADW + V(1.45, -0.6, 1.25))], [(TL0, HEADW + V(0.2, -0.6, -0.1)), (TL1, HEADW + V(0.2, -0.5, -0.1))], 18, 5.6)
# 3 yuz yostiqqa botgan: DOF, yonlama siljish
F0, F1 = S["face"]
c = look_cam("face", faceT, 45, 2.0, [(F0, tuple(FDIR * 0.42 - HXL * 0.12 - HUP * 0.06)), (F1, tuple(FDIR * 0.36 - HXL * 0.2 - HUP * 0.03))])
# 4 unitaz: past burchak push-in
T0, T1 = S["toilet"]; TS = TOI + V(0, 0.33, 0.47)
c = abs_cam("toilet", [(T0, TS + V(0.75, -1.35, -0.25)), (T1, TS + V(0.32, -0.62, 0.05))], [(T0, TS + V(0, 0.05, 0.0)), (T1, TS + V(0, 0.05, -0.02))], 18, 4.0)
# 5 Petri idishlari: chapdan o'ngga, "17 000×" da silkinish
MD = (DL + DR) / 2
c = abs_cam("petri", [(PE0, DL + V(-0.05, -0.5, 0.32)), (F_17 - 1, DL + V(0.0, -0.55, 0.34)), (F_17 + 5, MD + V(0.0, -1.3, 0.72)), (PE1, MD + V(0.14, -1.05, 0.58))],
            [(PE0, DL + V(0, 0, 0.0)), (F_17 - 1, DL + V(0.03, 0, 0.0)), (F_17 + 5, MD + V(0, 0.15, 0.13)), (PE1, MD + V(0.14, 0.12, 0.1))], 24, 5.6)
lens_keys(c, [(PE0, 26), (F_17 - 1, 26), (F_17 + 5, 16), (PE1, 17)])
shake(c, F_17, F_17 + 14, 0.02, seed=5)
# 6 bosib yotish: bakteriyalar orasidan orqaga chekinish, teri tushadi
AP_ = FP(*A_C)
c = abs_cam("press", [(PR0, AP_ + V(3.3, -0.6, 0.72)), (F_PRESS - 4, AP_ + V(5.6, -0.9, 1.0)), (PR1, AP_ + V(6.2, -1.0, 0.8))],
            [(PR0, AP_ + V(2.6, 0.0, 0.55)), (F_PRESS - 4, AP_ + V(2.2, 0.0, 1.0)), (PR1, AP_ + V(2.4, 0.0, 0.62))], 22, 4.0, clip=0.01)
shake(c, F_PRESS, F_PRESS + 14, 0.08, seed=6)
# 7 sakkiz soat: karavot yonidan past burchak
c = abs_cam("night8", [(N0, HEADW + V(1.6, -1.4, -0.12)), (N1, HEADW + V(1.35, -0.8, 0.0))], [(N0, HEADW + V(0, -0.6, 0.0)), (N1, HEADW + V(0, -0.5, 0.0))], 16, 4.0)
# 8 ter/yog': yonoqqa makro push-in
c = look_cam("sweat", cheekT, 50, 5.6, [(SW0, tuple(CHK_OUT * 0.2 + FDIR * 0.22)), (SW1, tuple(CHK_OUT * 0.12 + FDIR * 0.14))], clip=0.002)
# 9 qipiqlar yog'iladi: tepadan pastga
BP_ = FP(*B_C)
c = abs_cam("flakes", [(FL0, BP_ + V(0.6, -3.2, 3.6)), (FL1, BP_ + V(0.5, -2.6, 1.6))], [(FL0, BP_ + V(0, 0, 0.8)), (FL1, BP_ + V(0, 0, 0.2))], 24, 4.0, clip=0.01)
# 10 chang: soch tolasi yonidan
DP_ = BP_ + V(-0.2, 3.0, 0.8)
c = abs_cam("dust", [(DU0, DP_ + V(2.6, -2.8, 0.6)), (DU1, DP_ + V(1.6, -2.4, 0.3))], [(DU0, DP_ + V(0, 0, -0.2)), (DU1, DP_ + V(0.3, 0, -0.5))], 26, 4.0, clip=0.01)
# 11 so'lak: yuzga yaqin, orqa yorug'lik
c = look_cam("saliva", mouthT, 35, 4.0, [(SA0, tuple(-HXL * 0.3 + FDIR * 0.12 - HUP * 0.04)), (SA1, tuple(-HXL * 0.24 + FDIR * 0.1 - HUP * 0.02))])
# 12 singish: iplarga push-in
DPc = FP(*D_C)
c = abs_cam("soak", [(SO0, DPc + V(1.6, -3.2, 2.2)), (SO1, DPc + V(0.9, -1.8, 1.1))], [(SO0, DPc + V(0, 0, 0.2)), (SO1, DPc)], 26, 4.0, clip=0.01)
# 13 issiqlik kamerasi: tepadan aylanma
c = abs_cam("thermal", [(TH0, HEADW + V(1.2, -1.6, 1.6)), (TH1, HEADW + V(1.7, -0.6, 1.35))], [(TH0, HEADW + V(0.1, -0.7, -0.15)), (TH1, HEADW + V(0.1, -0.6, -0.15))], 18, 5.6)
# 14 zamburug': crash zoom
EP_ = FP(*E_C)
c = abs_cam("fungi", [(FU0, EP_ + V(1.6, -3.4, 3.0)), (FU0 + 5, EP_ + V(0.9, -1.9, 1.6)), (FU1, EP_ + V(0.8, -1.6, 1.3))], [(FU0, EP_ + V(0.6, 0.3, 0)), (FU1, EP_ + V(0.7, 0.4, 0))], 22, 4.0, clip=0.01)
lens_keys(c, [(FU0, 20), (FU0 + 5, 30), (FU1, 32)]); shake(c, FU0 + 4, FU0 + 16, 0.05, seed=14)
# 15 ko'payish: orqaga chekinish + aylanma
CPc = FP(*C_C)
c = abs_cam("breed", [(BR0, CPc + V(0.5, -0.9, 0.55)), ((BR0 + BR1) // 2, CPc + V(1.6, -2.2, 1.3)), (BR1, CPc + V(2.8, -2.2, 2.6))],
            [(BR0, CPc + V(0, 0, 0)), (BR1, CPc + V(0.1, 0.1, 0))], 28, 4.0, clip=0.01)
# 16 ishqalash: past burchak, yuzga push-in
c = look_cam("rub", faceT, 30, 4.0, [(RU0, tuple(FDIR * 0.6 - HXL * 0.08 - HUP * 0.12)), (RU1, tuple(FDIR * 0.42 - HXL * 0.05 - HUP * 0.05))])
shake(c, RU0, RU1, 0.006, seed=16, decay=False)
# 17 surtilish: yonlama ergashish (teri va mato orasidagi tirqish darajasida)
c = abs_cam("smear", [(SM0, AP_ + V(-1.6, -2.4, 0.68)), (SM1, AP_ + V(0.6, -2.4, 0.66))], [(SM0, AP_ + V(-1.0, 0.0, 0.7)), (SM1, AP_ + V(1.2, 0.0, 0.68))], 20, 4.0, clip=0.01)
# 18 teshiklar: teshikka sho'ng'ish
c = abs_cam("pores", [(PO0, SKW + V(0.8, -3.6, 2.4)), (PO0 + 40, SKW + V(0.4, -2.4, 1.5)), (PO1, SKW + V(0.15, -1.25, 0.9))],
            [(PO0, SKW + V(0, 0.4, 0)), (PO1, SKW + V(0, 0.1, -0.25))], 24, 5.6, clip=0.01)
# 19 kesim: push-in, yiringda silkinish
c = abs_cam("inflame", [(IN0, CUT + V(4.2, -0.4, 0.5)), (F_PUS - 1, CUT + V(3.4, -0.2, 0.1)), (IN1, CUT + V(2.7, 0.0, -0.3))],
            [(IN0, CUT + V(0, 0, -0.8)), (IN1, CUT + V(0, 0, -1.1))], 24, 8.0, clip=0.01)
shake(c, F_PUS, F_PUS + 14, 0.05, seed=19)
# 20 krem: past burchakdan aylanma
JR = JAR + V(0, 0, 0.05)
c = abs_cam("cream", [(CR0, JR + V(0.42, 0.12, -0.01)), (CR1, JR + V(0.2, 0.34, 0.07))], [(CR0, JR), (CR1, JR + V(0, 0, 0.01))], 32, 2.8, clip=0.01)
# 21 surtish: yuzga push-in
AP0, AP1 = S["apply"]
c = rel_cam("apply", faceT, 42, 2.8, [(AP0, V(0.2, -0.55, -0.04)), (AP1, V(0.1, -0.32, -0.03))])
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        if fc.data_path == "location":
            for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
for f_, n in SHOTS:
    sc.timeline_markers.new(n, frame=f_).camera = CAMS[n]
sc.camera = CAMS["hook"]
# ekran yozuvi (kameraga bog'langan): "1-KUN -> 7-KUN", "8 SOAT"
ov_m = mat("ov_txt", (1, 1, 1), 0.5, emit=4.0)
day = text("daycount", "1-KUN", 0.045, (0, 0.085, -0.4), (0, 0, 0), ov_m, parent=CAMS["tlapse"])
def _day(scene, *a):
    f_ = scene.frame_current
    d = 1 + int(6 * max(0.0, min(1.0, (f_ - TL0 - 2) / (TL1 - TL0 - 4))) + 0.0001)
    day.data.body = f"{d}-KUN"
bpy.app.handlers.frame_change_pre.append(_day)
vis(day, [S["tlapse"]])
hrs = text("hours", "8 SOAT", 0.045, (0, 0.085, -0.4), (0, 0, 0), ov_m, parent=CAMS["night8"]); vis(hrs, [S["night8"]])

# ======================================================================
# 10) YORUG'LIK, FON VA TIMELAPSE
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_env = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_env.inputs[0])
bg_col = N.new("ShaderNodeBackground")
a1 = N.new("ShaderNodeAddShader"); L.new(bg_env.outputs[0], a1.inputs[0]); L.new(bg_col.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WORLD = {"night": (0.0, (0.002, 0.004, 0.012), 1.0), "black": (0.0, (0, 0, 0), 0.0), "toilet": (0.0, (0.02, 0.025, 0.03), 1.0),
         "lab": (0.0, (0.01, 0.015, 0.02), 1.0), "fab": (0.0, (0.16, 0.2, 0.28), 1.0), "skin": (0.0, (0.16, 0.07, 0.055), 1.0),
         "cut": (0.0, (0.012, 0.018, 0.035), 1.0), "bath": (0.0, (0.02, 0.02, 0.02), 1.0)}
def world_of(n):
    if n == "thermal": return "black"
    if n in ROOMN: return "night"
    if n in FABN: return "fab"
    return {"toilet": "toilet", "petri": "lab", "pores": "skin", "inflame": "cut"}.get(n, "bath")
for f_, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f_)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f_)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f_)
# timelapse: kun/tun (HDRI kuchi + quyosh nuri derazadan), soat strelkalari
sun = area("sun_win", tuple(WC + V(0.0, -0.8, 0.6)), 1.6, (1.0, 0.92, 0.8), [(1, 0)], target=empty("sunT", tuple(BED + V(0.3, 0.6, 0.6))))
for i in range(7):
    a_ = TL0 + 2 + int((TL1 - TL0 - 4) * i / 7); b_ = a_ + int((TL1 - TL0 - 4) / 14)
    sun.data.energy = 900.0; sun.data.keyframe_insert("energy", frame=a_); sun.data.energy = 0.0; sun.data.keyframe_insert("energy", frame=b_)
    bg_env.inputs[1].default_value = 1.0; bg_env.inputs[1].keyframe_insert("default_value", frame=a_)
    bg_env.inputs[1].default_value = 0.0; bg_env.inputs[1].keyframe_insert("default_value", frame=b_)
sun.data.energy = 0.0; sun.data.keyframe_insert("energy", frame=TL1 + 1)
interp(sun.data, "CONSTANT"); interp(w.node_tree, "CONSTANT")
for f_, hm, mm in ((1, 0, 0), (TL0, 0, 0), (TL1, -7 * 360 * 2, -7 * 360 * 24), (N0, -10 * 30, -10 * 360), (N1, -18 * 30, -18 * 360)):
    hand_h.rotation_euler = (0, 0, R(hm)); hand_h.keyframe_insert("rotation_euler", frame=f_)
    hand_m.rotation_euler = (0, 0, R(mm)); hand_m.keyframe_insert("rotation_euler", frame=f_)
for o in (hand_h, hand_m):
    for fc in fcurves(o):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
        for k_ in fc.keyframe_points:
            if int(k_.co.x) in (TL1, N1): k_.interpolation = "CONSTANT"
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
NIGHT = rng("hook", "tlapse", "face", "night8", "sweat", "saliva", "rub")
point("bed_bulb", tuple(BL + V(0, 0, 0.36)), 0.04, (1.0, 0.68, 0.36), lights_for(NIGHT, 45.0))
area("bed_warm", tuple(BL + V(-0.4, -0.4, 0.6)), 0.6, (1.0, 0.7, 0.45), lights_for(NIGHT, 22.0), target=FT)
shade_e = shade_m.node_tree.nodes["Principled BSDF"]; shade_e.inputs["Emission Color"].default_value = (1.0, 0.75, 0.45, 1)
for f_, e in ((1, 2.5), (TH0, 0.0), (TH1 + 1, 2.5)):
    shade_e.inputs["Emission Strength"].default_value = e; shade_e.inputs["Emission Strength"].keyframe_insert("default_value", frame=f_)
area("moon_key", (BED.x + 1.6, BED.y - 1.4, 2.2), 1.2, (0.45, 0.6, 1.0), lights_for(NIGHT, 45.0), target=FT)
area("moon_fill", (BED.x - 0.2, BED.y - 2.0, 1.4), 1.5, (0.4, 0.5, 0.9), lights_for(NIGHT, 12.0), target=FT)
area("room_fill", (0.6, 0.0, 2.5), 2.0, (0.6, 0.65, 0.85), lights_for(NIGHT, 14.0), target=empty("rfT", (BED.x, BED.y, 0.5)))
area("cheek_key", (0, 0, 0), 0.15, (1.0, 0.9, 0.8), lights_for([S["sweat"]], 6.0), target=cheekT, parent=None)
ck = bpy.data.objects["cheek_key"]; ck.location = tuple(wp(cheekT, (SW0 + SW1) // 2) + V(0.2, -0.25, 0.2))
area("sal_rim", tuple(wp(mouthT, (SA0 + SA1) // 2) + V(0.25, 0.3, 0.2)), 0.2, (0.8, 0.9, 1.0), lights_for([S["saliva"]], 30.0), target=mouthT)
# unitaz: sovuq ko'kish shift nuri
TT = empty("toiT", tuple(TOI + V(0, 0.4, 0.4)))
area("T_key", tuple(TOI + V(0.6, -0.4, 2.4)), 0.8, (0.85, 0.92, 1.0), lights_for([S["toilet"]], 160.0), target=TT)
area("T_rim", tuple(TOI + V(-0.8, 0.2, 1.2)), 0.6, (0.5, 0.75, 1.0), lights_for([S["toilet"]], 50.0), target=TT)
# laboratoriya
LT = empty("labT", tuple(LAB + V(0, 0, TZ)))
area("L_key", tuple(LAB + V(0.0, -0.6, 2.2)), 1.2, (1.0, 0.97, 0.93), lights_for([S["petri"]], 140.0), target=LT)
area("L_rim", tuple(LAB + V(0.8, 1.0, 1.5)), 0.8, (0.5, 0.75, 1.0), lights_for([S["petri"]], 60.0), target=LT)
area("L_under", tuple(LAB + V(0, -0.3, TZ - 0.03)), 0.6, (1.0, 0.85, 0.6), lights_for([S["petri"]], 4.0), target=empty("luT", tuple(LAB + V(0, 0, TZ + 1))))
# mikro mato: iliq asosiy nur, ko'k chet nuri; teri bosganda yon nurlar
def fab_lights(tag, c, ranges, key_e, rim_e, low=False):
    t = empty(f"fT_{tag}", tuple(c))
    zk = 1.2 if low else 4.0
    area(f"fk_{tag}", tuple(c + V(-3.0, -3.5, zk)), 3.0, (1.0, 0.9, 0.78), lights_for(ranges, key_e), target=t)
    area(f"fr_{tag}", tuple(c + V(3.5, 3.0, zk * 0.5)), 2.5, (0.5, 0.7, 1.0), lights_for(ranges, rim_e), target=t)
    area(f"ff_{tag}", tuple(c + V(2.5, -3.0, 1.0)), 2.5, (1.0, 0.85, 0.75), lights_for(ranges, key_e * 0.3), target=t)
fab_lights("A", AP_, [S["press"]], 400.0, 500.0, low=True)
fab_lights("Am", AP_, [S["smear"]], 300.0, 450.0, low=True)
fab_lights("B", BP_, rng("flakes", "dust"), 500.0, 400.0)
fab_lights("D", DPc, [S["soak"]], 450.0, 450.0)
fab_lights("E", (EP_ + CPc) / 2, rng("fungi", "breed"), 600.0, 450.0)
# mikro teri
SKT = empty("skT", tuple(SKW))
area("S_key", tuple(SKW + V(-1.5, -1.8, 2.4)), 1.5, (1.0, 0.9, 0.78), lights_for([S["pores"]], 90.0), target=SKT)
area("S_rim", tuple(SKW + V(1.8, 1.6, 0.9)), 1.2, (0.5, 0.7, 1.0), lights_for([S["pores"]], 160.0), target=SKT)
area("S_fill", tuple(SKW + V(1.2, -1.6, 0.6)), 1.5, (1.0, 0.8, 0.7), lights_for([S["pores"]], 25.0), target=SKT)
# kesim
CT_ = empty("cutT", tuple(CUT + V(0, 0, -0.8)))
area("C_key", tuple(CUT + V(2.4, -1.8, 1.8)), 2.0, (1.0, 0.95, 0.9), lights_for([S["inflame"]], 260.0), target=CT_)
area("C_fill", tuple(CUT + V(2.2, 1.6, -1.2)), 1.8, (1.0, 0.85, 0.75), lights_for([S["inflame"]], 90.0), target=CT_)
area("C_rim", tuple(CUT + V(-0.6, -2.4, 1.6)), 1.5, (0.35, 0.6, 1.0), lights_for([S["inflame"]], 160.0), target=CT_)
point("C_red", tuple(CUT + V(0.4, 0, -FOLL_D + 0.2)), 0.3, (1.0, 0.1, 0.05), [(1, 0), (S["inflame"][0], 0), (F_PUS, 60.0), (S["inflame"][1] + 1, 0)])
# hammom
BT = empty("bathT", tuple(BATH + V(0, -0.1, 1.45)))
area("B_ceil", tuple(BATH + V(0.2, 0.1, 2.5)), 1.0, (1.0, 0.97, 0.94), lights_for(BATHR, 120.0), target=BT)
area("B_mirror", tuple(BATH + V(0, -0.6, 2.0)), 0.8, (1.0, 0.95, 0.9), lights_for(BATHR, 40.0), target=FT)
area("B_rim", tuple(BATH + V(-0.8, 0.6, 1.8)), 0.6, (0.7, 0.85, 1.0), lights_for(BATHR, 35.0), target=FT)
area("B_jar", tuple(JAR + V(0.3, -0.3, 0.4)), 0.3, (1.0, 0.9, 0.75), lights_for([S["cream"]], 12.0), target=jar)

# ======================================================================
# 11) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0
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
