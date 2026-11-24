# "Uzoq o'tirish -> tromb -> o'pka tromboemboliyasi" — Zack D. Films uslubida 40.2 s video (966 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; salon illyuminator/illyuminator.py dan; rentgen tana, vena, kamera va yorug'lik
# yordamchilari gemorroy/gemorroy.py dan (lib.py); quvur/impuls/rentgen materiallari burish/parts.py dan. Kadr rejasi: STORYBOARD.md.
# Assetlar: zack_test/tools/get_tromb.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/tromb/tromb.py --render
# Sinov:  FRAMES=20,60,130 PCT=30 OUT=/tmp/claude-0/test/ ... --render   |   Bo'lak: RANGE=a,b
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from lib import *                      # sahnani tozalaydi; bpy, math, random, Vector, Matrix, mc, P, sc, R, PH, BK, yordamchilar
import bmesh
from mathutils import Quaternion
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
random.seed(7)
END = 966
sc.frame_start, sc.frame_end = 1, END
def T(sec): return int(round(sec * 24)) + 1           # ovoz vaqti -> kadr
def V(*a): return Vector(a)

# ---------------- kadrlar (Whisper so'z vaqtlari, /tmp/claude-0/words.json) ----------------
SHOTS = [(1, "hook"), (T(1.84), "desk"), (T(4.96), "xlegs"), (T(7.1), "puddle"), (T(9.58), "calf"), (T(11.78), "pump"),
         (T(16.6), "slow"), (T(19.62), "clot"), (T(23.7), "face"), (T(25.24), "stand"), (T(27.54), "detach"), (T(29.7), "travel"),
         (T(32.64), "lung"), (T(34.92), "choke"), (T(37.38), "lungdark"), (T(39.3), "end")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
F_STOP = T(15.84)        # "to'xtab qoladi" — nasos to'xtaydi
F_TROMB = T(21.92)       # "tromb" — crash zoom
F_RIP = T(29.14)         # "uzilib" — tromb devordan uziladi
F_LODGE = T(34.06)       # "to'sib" — tromb o'pka arteriyasiga tiqiladi
F_STAND = S["stand"][0] + 2
CABIN_REAL = rng("hook", "face", "stand", "choke", "end")
XR_SEAT = rng("xlegs", "calf"); XR_STAND = rng("travel")
CAB_ALL = CABIN_REAL + XR_SEAT + XR_STAND

# ======================================================================
# 1) SALON (A320 ichi; illyuminator.py dan). O'q X bo'ylab, oldi -X; chap (deraza) tomoni -Y. Pol z=0.
# ======================================================================
cabin = []
def C_(o): cabin.append(o); return o
def bm_obj(name, bm, m=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    if m: me.materials.append(m)
    return o
M = dict(
    plastic=mat("plastic", (0.86, 0.85, 0.82), 0.45),
    fabric=mat("fabric", (0.05, 0.09, 0.2), 0.95),
    cover=mat("cover", (0.85, 0.85, 0.82), 0.8),
    carpet=mat("carpet", (0.12, 0.13, 0.17), 1.0),
    cove=mat("cove", (1.0, 0.85, 0.65), 0.5, emit=6.0),
    steel=mat("steel", (0.32, 0.33, 0.35), 0.45, metal=1.0),
    screen=mat("screen", (0.01, 0.01, 0.012), 0.15, coat=1.0),
    darkglass=mat("darkglass", (0.01, 0.012, 0.016), 0.05, coat=1.0),
)
fab = M["fabric"]; _n = fab.node_tree.nodes; _l = fab.node_tree.links; _w = _n.new("ShaderNodeTexWave"); _w.inputs["Scale"].default_value = 40.0
_tc = _n.new("ShaderNodeTexCoord"); _l.new(_tc.outputs["Object"], _w.inputs["Vector"])
_mx = _n.new("ShaderNodeMix"); _mx.data_type = "RGBA"; _mx.inputs[6].default_value = (0.05, 0.09, 0.2, 1); _mx.inputs[7].default_value = (0.03, 0.05, 0.12, 1)
_l.new(_w.outputs["Fac"], _mx.inputs["Factor"]); _l.new(_mx.outputs[2], _n["Principled BSDF"].inputs["Base Color"])
RC, ZC = 1.85, 0.6
ROWS = [0.12 + 0.82 * (k - 6) for k in range(15)]
MEG_X = ROWS[6]; MEG_Y = -0.5
SEAT_YS = (-1.44, -0.97, -0.5, 0.5, 0.97, 1.44)
SEATS = {}
PHI = math.asin((1.05 - ZC) / RC)
def basis(X, Y, Z, pos):
    m = Matrix.Identity(4)
    for i, v in enumerate((X, Y, Z, pos)):
        for j in range(3): m[j][i] = v[j]
    return m
def win_frame(side):
    d = V(0, side * math.cos(PHI), math.sin(PHI)); t = V(0, -side * math.sin(PHI), math.cos(PHI))
    return d, t, t.cross(d)
def cabin_tube(name, r, x0, x1, m, nx=40):
    bm = bmesh.new(); seg = 96; xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]
    rings = [[bm.verts.new((x, r * math.cos(2 * math.pi * j / seg), ZC + r * math.sin(2 * math.pi * j / seg))) for j in range(seg)] for x in xs]
    for i in range(len(xs) - 1):
        for j in range(seg):
            k = (j + 1) % seg; bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]))
    o = bm_obj(name, bm, m); smooth(o); return o
shell = C_(cabin_tube("cabin_shell", RC, -7, 7, M["plastic"]))
sol = shell.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.08
cut_bm = bmesh.new(); WINS = []
for side in (-1, 1):
    d, t, w = win_frame(side)
    for x in ROWS:
        c = V(x - 0.28, 0, ZC) + d * RC
        r = bmesh.ops.create_cone(cut_bm, cap_ends=True, segments=32, radius1=1, radius2=1, depth=1)
        bmesh.ops.transform(cut_bm, matrix=basis(w, t, d, c) @ Matrix.Diagonal((0.125, 0.18, 0.5, 1)), verts=r["verts"])
        WINS.append((c, w, t, d))
cutter = bm_obj("win_cutter", cut_bm)
bo = shell.modifiers.new("win", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cutter; bo.solver = "EXACT"
bpy.context.view_layer.objects.active = shell
for mod in list(shell.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter, do_unlink=True)
# illyuminator ramkasi (BlenderKit 7250f009): bir marta import, keyin mesh'ni ulashgan nusxalar (X = en, Y = bo'y, Z = qalinlik)
bz0 = empty("bezel_src"); bz_new = import_gltf(BK + "7250f009_u.glb", bz0)
bpy.context.view_layer.update()
def is_cover(o): return any(m and m.name.startswith("Circle.002") for m in o.data.materials)
bz_parts = []
for o in bz_new:
    if o.type != "MESH": continue
    if is_cover(o) or max(o.dimensions) > 1.0: continue
    bz_parts.append((o, bz0.matrix_world.inverted() @ o.matrix_world))
for c, w, t, d in WINS:
    W_ = basis(w, t, d, c - d * 0.085) @ Matrix.Diagonal((0.95, 0.95, 1, 1))
    for o, rel in bz_parts:
        n_ = o.copy(); n_.parent = None; sc.collection.objects.link(n_); n_.matrix_world = W_ @ rel; C_(n_)
for o in bz_new: bpy.data.objects.remove(o, do_unlink=True)
C_(box("cabin_floor", (14, 3.6, 0.1), (0, 0, -0.05), M["carpet"]))
C_(box("aisle", (14, 0.5, 0.012), (0, 0, 0.006), mat("aislecarpet", (0.25, 0.05, 0.06), 1.0)))
for side in (-1, 1):
    C_(box("bins", (14, 0.72, 0.42), (0, side * 1.22, 1.86), M["plastic"], rot=(side * -18, 0, 0), bevel=0.04))
    C_(box("cove", (14, 0.03, 0.03), (0, side * 0.86, 2.08), M["cove"]))
    C_(box("sidewall_lo", (14, 0.05, 0.42), (0, side * 1.72, 0.21), M["plastic"]))
for x in (-7.0, 7.0): C_(box("bulkhead", (0.1, 3.8, 3.0), (x, 0, 1.0), M["plastic"]))
def seat(x, y):
    o = [box("seat_pan", (0.48, 0.42, 0.12), (x + 0.02, y, 0.44), M["fabric"], bevel=0.04),
         box("seat_back", (0.1, 0.42, 0.62), (x + 0.27, y, 0.79), M["fabric"], rot=(0, -10, 0), bevel=0.04),
         box("seat_head", (0.12, 0.36, 0.18), (x + 0.31, y, 1.0), M["cover"], rot=(0, -10, 0), bevel=0.03),
         box("seat_leg", (0.05, 0.05, 0.38), (x, y, 0.19), M["steel"]),
         box("seat_screen", (0.012, 0.2, 0.13), (x + 0.33, y, 0.84), M["screen"], rot=(0, -10, 0), bevel=0.004)]
    arms = {dy: box("arm", (0.42, 0.05, 0.05), (x + 0.05, y + dy, 0.64), M["plastic"], bevel=0.015) for dy in (-0.235, 0.235)}
    SEATS[(round(x, 2), y)] = (o, arms)
    for x_ in o + list(arms.values()): C_(x_)
for x in ROWS:
    for y in SEAT_YS: seat(x, y)
# tashqarida: bulutlar ustidagi osmon (HDRI dunyo) — derazalardan ko'rinadi
HIDE_XR = []                                     # rentgen (o'tirgan) kadrlarida oldingi qator va qo'l tayanchi kamerani to'sadi
for y in (-0.5, -0.97):
    o_, a_ = SEATS[(round(ROWS[5], 2), y)]; HIDE_XR += o_ + list(a_.values())
HIDE_XR.append(SEATS[(round(MEG_X, 2), MEG_Y)][1][0.235])
for o in cabin: vis(o, CABIN_REAL + XR_STAND + ([] if o in HIDE_XR else XR_SEAT), recursive=False)

# ======================================================================
# 2) ISH XONASI (0,60,0): stol, kompyuter, devor soati (timelapse), deraza
# ======================================================================
RM = V(0, 60, 0)
room = []
def RM_(o): room.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.95, 0.9, 0.82))
RM_(plane("r_floor", (6, 6), tuple(RM), floor_m))
RM_(box("r_wall_f", (6, 0.1, 2.8), tuple(RM + V(0, -1.45, 1.4)), wall_m))
RM_(box("r_wall_b", (6, 0.1, 2.8), tuple(RM + V(0, 2.0, 1.4)), wall_m))
RM_(box("r_wall_r", (0.1, 4, 2.8), tuple(RM + V(1.9, 0.3, 1.4)), wall_m))
# chap devorda deraza
RM_(box("r_wall_l1", (0.1, 4, 0.8), tuple(RM + V(-1.9, 0.3, 0.4)), wall_m))
RM_(box("r_wall_l2", (0.1, 4, 0.5), tuple(RM + V(-1.9, 0.3, 2.55)), wall_m))
RM_(box("r_wall_l3", (0.1, 1.6, 1.5), tuple(RM + V(-1.9, -0.75, 1.55)), wall_m))
RM_(box("r_wall_l4", (0.1, 1.2, 1.5), tuple(RM + V(-1.9, 1.7, 1.55)), wall_m))
RM_(box("r_ceil", (6, 6, 0.05), tuple(RM + V(0, 0, 2.82)), mat("r_ceil_m", (0.92, 0.92, 0.9), 0.8)))
sky_m = mat("r_sky", (0.6, 0.75, 1.0), 0.5, emit=5.0)
RM_(plane("r_sky", (3, 2.2), tuple(RM + V(-2.6, 0.5, 1.6)), sky_m, rot=(90, 0, 90)))
frame_m = mat("r_win_frame", (0.93, 0.93, 0.9), 0.4)
for nm, sz, off in (("wf_t", (0.12, 1.3, 0.05), (0, 0, 0.75)), ("wf_b", (0.22, 1.3, 0.06), (0.05, 0, -0.75)),
                    ("wf_m", (0.08, 0.04, 1.5), (0, 0, 0)), ("wf_h", (0.08, 1.2, 0.04), (0, 0, 0.2))):
    RM_(box(nm, sz, tuple(RM + V(-1.9, 0.5, 1.55) + V(*off)), frame_m))
# stol (WoodenTable_01, 0.55 m -> 1.3x), kompyuter, klaviatura
desk = empty("desk", tuple(RM + V(0, -0.68, 0))); RM_(desk)
for o in import_gltf(PH + "WoodenTable_01/WoodenTable_01.gltf", desk): RM_(o)
desk.scale = (1.0, 1.0, 1.3)
bpy.context.view_layer.update()
DESK_Z = ray_down([o for o in room if o.type == "MESH" and o.name.startswith("WoodenTable")], RM.x, RM.y - 0.68, 1.5) or 0.72
print("DESK_Z", DESK_Z)
mon_m = mat("monitor", (0.02, 0.02, 0.025), 0.3)
code_m = bpy.data.materials.new("code"); code_m.use_nodes = True
_n = code_m.node_tree.nodes; _l = code_m.node_tree.links; _b = _n["Principled BSDF"]
_tc = _n.new("ShaderNodeTexCoord"); _br = _n.new("ShaderNodeTexBrick"); _br.inputs["Scale"].default_value = 14.0
_br.inputs["Mortar Size"].default_value = 0.008; _br.inputs["Brick Width"].default_value = 1.6; _br.inputs["Row Height"].default_value = 0.12
_br.inputs["Color1"].default_value = (0.25, 0.75, 1.0, 1); _br.inputs["Color2"].default_value = (0.9, 0.9, 0.95, 1); _br.inputs["Mortar"].default_value = (0.02, 0.03, 0.06, 1)
_l.new(_tc.outputs["Object"], _br.inputs["Vector"]); _l.new(_br.outputs["Color"], _b.inputs["Emission Color"])
_b.inputs["Emission Strength"].default_value = 2.2; _b.inputs["Base Color"].default_value = (0, 0, 0, 1); _b.inputs["Roughness"].default_value = 0.1
MON = RM + V(0, -1.0, DESK_Z)
RM_(box("mon_body", (0.62, 0.03, 0.38), tuple(MON + V(0, 0, 0.36)), mon_m, bevel=0.006))
RM_(plane("mon_screen", (0.58, 0.34), tuple(MON + V(0, 0.017, 0.36)), code_m, rot=(90, 0, 0)))
RM_(box("mon_neck", (0.05, 0.04, 0.17), tuple(MON + V(0, 0.01, 0.09)), mon_m))
RM_(box("mon_base", (0.24, 0.16, 0.012), tuple(MON + V(0, 0.02, 0.006)), mon_m))
RM_(box("keyboard", (0.42, 0.14, 0.02), tuple(RM + V(0, -0.55, DESK_Z + 0.01)), mat("kb", (0.85, 0.85, 0.87), 0.4), bevel=0.004))
RM_(box("mouse", (0.06, 0.1, 0.03), tuple(RM + V(0.33, -0.55, DESK_Z + 0.015)), mat("mouse", (0.85, 0.85, 0.87), 0.3), bevel=0.012))
RM_(cyl("mug", 0.04, 0.1, tuple(RM + V(-0.4, -0.75, DESK_Z + 0.05)), mat("mug", (0.85, 0.2, 0.1), 0.25, coat=0.6)))
chair_m = mat("chair", (0.05, 0.05, 0.06), 0.5)
RM_(box("chair_seat", (0.48, 0.46, 0.08), tuple(RM + V(0, 0.02, 0.46)), chair_m, bevel=0.03))
RM_(box("chair_back", (0.46, 0.06, 0.55), tuple(RM + V(0, 0.3, 0.85)), chair_m, rot=(-8, 0, 0), bevel=0.03))
RM_(cyl("chair_post", 0.03, 0.42, tuple(RM + V(0, 0.02, 0.21)), M["steel"]))
pl = empty("r_plant", tuple(RM + V(1.4, -1.1, 0))); RM_(pl)
for o in import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", pl): RM_(o)
pl.scale = (1.3,) * 3
# devor soati: monitor ustida, old devorda — "4-5 soat" timelapse
CLK = RM + V(-0.75, -1.38, 1.75)
clk = empty("clock", tuple(CLK)); clk.rotation_euler = (R(-90), 0, 0); RM_(clk)       # mahalliy +Z -> dunyo +Y (xonaga qaraydi)
RM_(cyl("clk_body", 0.2, 0.04, (0, 0, 0.02), mat("clk_body_m", (0.08, 0.08, 0.09), 0.3), parent=clk, verts=48))
RM_(cyl("clk_face", 0.18, 0.005, (0, 0, 0.042), mat("clk_face_m", (0.95, 0.94, 0.9), 0.5), parent=clk, verts=48))
tick_m = mat("tick", (0.05, 0.05, 0.05), 0.5)
for k in range(12):
    a = 2 * math.pi * k / 12
    RM_(box(f"tick{k}", (0.009, 0.03 if k % 3 else 0.042, 0.004), (0.15 * math.sin(a), 0.15 * math.cos(a), 0.046), tick_m, rot=(0, 0, -math.degrees(a)), parent=clk))
hand_h = empty("hand_h", (0, 0, 0.048), clk); hand_m = empty("hand_m", (0, 0, 0.05), clk)
RM_(box("hh", (0.014, 0.09, 0.003), (0, 0.038, 0), tick_m, parent=hand_h))
RM_(box("hm", (0.009, 0.13, 0.003), (0, 0.06, 0), mat("hand_red", (0.7, 0.05, 0.03), 0.4), parent=hand_m))
D0, D1 = S["desk"]
for f, mins in ((1, 0), (D0 + 4, 0), (D1, 270), (END, 270)):                     # 13:00 -> 17:30
    hand_m.rotation_euler = (0, 0, R(mins / 60 * 360)); hand_m.keyframe_insert("rotation_euler", frame=f)
    hand_h.rotation_euler = (0, 0, R((1 + mins / 60) / 12 * 360)); hand_h.keyframe_insert("rotation_euler", frame=f)
interp(hand_m, "LINEAR"); interp(hand_h, "LINEAR")
# deraza: kunduz -> oqshom (timelapse)
_se = sky_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]; _ss = sky_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, c_, s_ in ((D0, (0.6, 0.78, 1.0), 6.0), (D0 + 40, (1.0, 0.55, 0.25), 4.0), (D1, (0.1, 0.15, 0.4), 1.2)):
    _se.default_value = (*c_, 1); _se.keyframe_insert("default_value", frame=f); _ss.default_value = s_; _ss.keyframe_insert("default_value", frame=f)
for o in room: vis(o, rng("desk"), recursive=False)

# ======================================================================
# 3) QAHRAMONLAR: Megan (asosiy), yo'lovchilar (Kate, Josh, David, Pete)
# ======================================================================
def load(name, file):
    root, arm, meshes = mc.load_character(name, file); sc.render.fps = 24; soften(meshes); return root, arm, meshes
mroot, meg, mmeshes = load("meg", "Megan.fbx")
SIT5 = A_("Sitting_Idle_5.fbx", False); SIT3 = A_("Sitting_Idle_3.fbx", False); SIT4 = A_("Sitting_Idle_4.fbx", False)
TYPE = A_("Typing.fbx", False); S2S = A_("Sit_To_Stand.fbx", False); WALK = A_("Female_Walk.fbx")
BREATH = A_("Breathing_Idle.fbx"); DIE = A_("Dying_6.fbx", False); DISB = A_("Sitting_Disbelief_3.fbx", False)
# o'tirish -> (xona: Typing) -> o'tirish -> turish -> yurish -> turib qolish -> ko'krakni changallab yiqilish
strip(meg, SIT5, 1, blend=0, bout=0, repeat=0.3)
strip(meg, TYPE, D0, src=(30, 300), blend=0, bout=0)
strip(meg, SIT5, S["xlegs"][0], blend=0, bout=0, repeat=3.25)
strip(meg, S2S, F_STAND, speed=1.35, blend=0, bout=0)
F_WALK = F_STAND + 37
strip(meg, WALK, F_WALK, blend=6, bout=0, repeat=2.0)
F_IDLE = F_WALK + 50
strip(meg, BREATH, F_IDLE, blend=8, bout=0, repeat=1.0)
F_DIE = S["choke"][0] + 2
strip(meg, DIE, F_DIE, blend=4, bout=0, speed=1.0)
for tr in meg.animation_data.nla_tracks:
    for s_ in tr.strips: s_.extrapolation = "HOLD_FORWARD" if s_.action == DIE else "NOTHING"
SEAT = V(MEG_X + 0.06, MEG_Y, -0.06)
WSPD = 0.051
def mkey(f, loc, rz=-90.0): place(mroot, f, tuple(loc), rz)
S2S_FWD = float(os.environ.get("S2S_FWD", 0.48))      # Sit_To_Stand oxirida Hips oldinga siljigan (yurish strip'i buni nolga qaytaradi)
mkey(1, SEAT); mkey(D0, RM + V(0, 0.1, 0.0), 0.0); mkey(S["xlegs"][0], SEAT)
mkey(F_STAND, SEAT); mkey(F_WALK, SEAT + V(0, 0, 0.06))
W1 = SEAT + V(-S2S_FWD - WSPD * 8, -MEG_Y, 0.06)                                  # yo'lakka qadam + Hips kompensatsiyasi
mkey(F_WALK + 12, W1)
WEND = W1 + V(-WSPD * (F_IDLE - F_WALK - 12), 0, 0)
mkey(F_IDLE, WEND); mkey(F_DIE - 1, WEND); mkey(F_DIE, WEND)
for fc in fcurves(mroot):
    for k in fc.keyframe_points:
        k.interpolation = "CONSTANT" if int(k.co.x) in (1, D0, S["xlegs"][0], F_IDLE, F_DIE - 1, F_DIE) else "LINEAR"
def bw(b, arm=None):
    a = arm or meg; return (a.matrix_world @ a.pose.bones["mixamorig:" + b].head).copy()
headE = child_of_bone("meg_head", meg, "Head"); faceT = empty("faceT", (0, 0.06, 0.09), headE)
chestE = child_of_bone("meg_chest", meg, "Spine2")
# ko'krakni changallash: Dying_6 ustiga ikkala bilakka IK (nishonlar Spine2 fazosida: X chap, Y tepa, Z old)
for sd, loc in (("Left", (0.03, 0.03, 0.15)), ("Right", (-0.06, -0.03, 0.16))):
    tg = child_of_bone(f"clutch_{sd}", meg, "Spine2", loc)
    ik = meg.pose.bones[f"mixamorig:{sd}ForeArm"].constraints.new("IK"); ik.target = tg; ik.chain_count = 2; ik.use_tail = True
    for f, v in ((1, 0.0), (F_DIE, 0.0), (F_DIE + 8, 1.0), (F_DIE + 42, 1.0), (F_DIE + 54, 0.0)):
        ik.influence = v; meg.keyframe_insert(f'pose.bones["mixamorig:{sd}ForeArm"].constraints["{ik.name}"].influence', frame=f)
MEG_REAL = rng("hook", "desk", "face", "stand", "choke", "end")
for o in mmeshes: vis(o, MEG_REAL, recursive=False)
# yo'lovchilar (o'tirgan; voqeada o'girilib qarashadi)
PASS = []
for nm, file, row, y, act, dz in (("kate", "Kate.fbx", 6, -0.97, SIT3, -0.06), ("josh", "Josh.fbx", 5, 0.5, SIT4, -0.06),
                                  ("david", "David.fbx", 7, 0.97, SIT5, -0.06), ("pete", "Pete.fbx", 8, -0.5, SIT3, -0.06)):
    r_, a_, ms = load(nm, file)
    strip(a_, act, -random.randint(0, 60), blend=0, bout=0, repeat=12.0)
    strip(a_, DISB, S["choke"][0] + 18 + random.randint(0, 8), src=(1, 60), blend=6, bout=0)
    for tr in a_.animation_data.nla_tracks:
        for s_ in tr.strips: s_.extrapolation = "HOLD_FORWARD" if s_.action == DISB else "NOTHING"
    place(r_, 1, (ROWS[row] + 0.06, y, dz), -90)
    for o in ms: vis(o, CABIN_REAL + XR_SEAT + XR_STAND, recursive=False)
    PASS.append((nm, r_, a_, ms))

# rentgen nusxa (Megan)
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.1, base=0.01)
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g); g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, XR_SEAT + XR_STAND, recursive=False)

# ======================================================================
# 4) RENTGEN ICHI: oyoq venalari, boldir mushagi, pastki kovak vena, yurak, o'pkalar; tromb nuqtasi
# ======================================================================
vein_x = P.pulse_material("x_vein", (0.05, 0.15, 0.9), base_emit=0.5, pulse_col=(0.35, 0.65, 1.0), width=0.05)
cava_x = P.pulse_material("x_cava", (0.08, 0.2, 0.9), base_emit=0.9, pulse_col=(0.35, 0.65, 1.0), width=0.05)
muscle_x = mat("x_muscle", (0.75, 0.12, 0.12), 0.4, emit=0.25, emit_col=(0.9, 0.2, 0.18), sss=0.2)
_mn = muscle_x.node_tree.nodes; _ml = muscle_x.node_tree.links
_wv = _mn.new("ShaderNodeTexWave"); _wv.wave_type = "BANDS"; _wv.bands_direction = "Z"; _wv.inputs["Scale"].default_value = 18.0
_wv.inputs["Distortion"].default_value = 2.0; _tcm = _mn.new("ShaderNodeTexCoord"); _ml.new(_tcm.outputs["Generated"], _wv.inputs["Vector"])
_mm = _mn.new("ShaderNodeMix"); _mm.data_type = "RGBA"; _mm.inputs[6].default_value = (0.75, 0.12, 0.12, 1); _mm.inputs[7].default_value = (0.45, 0.04, 0.05, 1)
_ml.new(_wv.outputs["Fac"], _mm.inputs["Factor"]); _ml.new(_mm.outputs[2], _mn["Principled BSDF"].inputs["Base Color"])
heart_x = mat("x_heart", (0.9, 0.08, 0.08), 0.3, emit=1.2)
lung_x = mat("x_lung", (0.95, 0.45, 0.5), 0.4, emit=0.5, alpha=0.5)
clotdot_m = glow_mat("x_clotdot", (1.0, 0.05, 0.02))
def leg_paths(f):
    sc.frame_set(f); bpy.context.view_layer.update()
    H = bw("Hips"); SP2 = bw("Spine2"); UP = (SP2 - H).normalized()
    FW = V(-1, 0, 0); XA = UP.cross(FW).normalized()
    JN = H + UP * 0.05 + FW * 0.02
    HEART = H + UP * 0.40 + FW * 0.06 + XA * 0.03
    legs = {}
    for sd, sg in (("Left", 1), ("Right", -1)):
        toe, ank, knee, hip = bw(sd + "ToeBase"), bw(sd + "Foot"), bw(sd + "Leg"), bw(sd + "UpLeg")
        shin = (ank - knee).normalized(); back = (FW - shin * FW.dot(shin)).normalized() * -1.0
        pts = [toe + V(0, 0, 0.02), ank + back * 0.025, knee.lerp(ank, 0.5) + back * 0.035, knee + back * 0.03,
               knee.lerp(hip, 0.5) + back * 0.02, hip + V(0, 0, -0.01), JN]
        legs[sd] = dict(pts=pts, knee=knee, ank=ank, shin=shin, back=back)
    return dict(H=H, UP=UP, FW=FW, XA=XA, JN=JN, HEART=HEART, legs=legs)
def build_xray(tag, f, ranges, muscles=False):
    g = leg_paths(f); parts = []
    for sd, L in g["legs"].items():
        parts.append(P.tube(f"{tag}_leg{sd}", L["pts"], 0.0065, vein_x, None, taper=[0.5, 0.7, 0.85, 0.95, 1.1, 1.2, 1.3]))
        if muscles:
            ln = (L["ank"] - L["knee"]).length
            ctr = L["knee"] + L["shin"] * ln * 0.38 + L["back"] * 0.03
            m_ = sphere(f"{tag}_calf{sd}", 1.0, tuple(ctr), muscle_x, sub=4)
            m_.rotation_mode = "QUATERNION"; m_.rotation_quaternion = frame_q(L["back"], L["shin"])      # +Y = orqa, +Z = boldir
            m_.scale = (0.03, 0.036, ln * 0.27); parts.append(m_)
    parts.append(P.tube(f"{tag}_cava", [g["JN"], g["JN"] + g["UP"] * 0.15, g["JN"] + g["UP"] * 0.28 + g["FW"] * 0.03, g["HEART"]], 0.011, cava_x, None))
    ht = sphere(f"{tag}_heart", 0.05, tuple(g["HEART"]), heart_x, scale=(1, 0.85, 1.1), sub=3); parts.append(ht)
    for sx in (-1, 1):
        parts.append(sphere(f"{tag}_lung{sx}", 0.075, tuple(g["HEART"] + g["UP"] * 0.1 + g["XA"] * sx * 0.09 - g["FW"] * 0.02),
                            lung_x, scale=(0.85, 0.9, 1.55), sub=4))
    for o in parts: vis(o, ranges, recursive=False)
    a, b_ = ranges[0][0], ranges[-1][1]
    for fr in range(a, b_ + 1, 10):
        key(ht, fr, scale=(1, 0.85, 1.1)); key(ht, fr + 3, scale=(1.2, 1.0, 1.32))
    return g, parts
XG, _ = build_xray("xs", S["xlegs"][0] + 20, XR_SEAT, muscles=True)
XG2, _ = build_xray("xt", S["travel"][0] + 20, XR_STAND)
# impulslar: oyoqlarda sekinlashadi (xlegs), boldirda deyarli yo'q (calf), yo'lda — tromb nuqtasi
XL0, XL1 = S["xlegs"]
pk = [(1, -0.2)]
p_, spd = -0.2, 0.045
for f in range(XL0, XL1 + 1, 2):
    p_ += spd; spd *= 0.94
    if p_ > 1.15: p_ = -0.15
    pk.append((f, p_))
pk += [(S["calf"][0], 0.3), (S["calf"][1], 0.36), (S["travel"][0], 0.0), (S["travel"][1], 0.0)]
for f, v in pk: val_key(vein_x, "pos", f, v)
interp(vein_x.node_tree, "LINEAR")
for f, v in ((1, 0.6), (XL0, 0.7), (XL1, 0.2), (S["calf"][0], 0.15), (S["travel"][0], 0.5)): val_key(vein_x, "glow", f, v)
# tromb nuqtasi (travel): chap boldirdan -> son -> kovak vena -> yurak -> o'ng o'pka
TR0, TR1 = S["travel"]
Lp = XG2["legs"]["Right"]["pts"]
dot_path = catmull([Lp[2], Lp[3], Lp[4], Lp[5], XG2["JN"], XG2["JN"] + XG2["UP"] * 0.15, XG2["HEART"],
                    XG2["HEART"] + XG2["UP"] * 0.08 - XG2["FW"] * 0.01, XG2["HEART"] + XG2["UP"] * 0.13 - XG2["XA"] * 0.08], step=0.01)
dot = sphere("clot_dot", 0.014, tuple(dot_path[0]), clotdot_m, sub=3)
halo = sphere("clot_halo", 0.045, (0, 0, 0), glow_mat("clot_halo_m", (1.0, 0.1, 0.03)), sub=3, parent=dot)
val_key(bpy.data.materials["clot_halo_m"], "a", 1, 3.0); val_key(clotdot_m, "a", 1, 6.0)
dot_core = sphere("clot_core", 0.011, (0, 0, 0), mat("clot_core_m", (0.3, 0.0, 0.0), 0.4, emit=3.0, emit_col=(1, 0.05, 0.02)), sub=3, parent=dot)
DOT_F = []
for f in range(TR0, TR1 + 1):
    t = ease(min(1.0, max(0.0, (f - TR0 - 4) / (TR1 - TR0 - 10.0))))
    i = min(len(dot_path) - 1, int(t * (len(dot_path) - 1))); DOT_F.append((f, dot_path[i]))
    key(dot, f, loc=tuple(dot_path[i]))
vis(dot, XR_STAND)
# rentgen boshlanishida ko'k "skan" halqasi emas, faqat sekin impuls; xlegs da qon "to'xtaydi"

# ======================================================================
# 5) VENA STUDIYASI (100,0,0): yarim kesilgan vena (kameraga ochiq, -Y), klapan, qon tanachalari, tromb
#    1 birlik ~ 1 sm. Qon +Z (yurak) tomonga oqadi.
# ======================================================================
CV = V(100.0, 0.0, 0.0)
VR, VZ0, VZ1 = 0.32, -1.8, 3.2
def half_tube(name, r_fn, z0, z1, nz, na, m, rim_m, thick, loc):
    vs = []; fs = []
    for i in range(nz + 1):
        z = z0 + (z1 - z0) * i / nz; r_ = r_fn(z)
        for j in range(na + 1):
            a = math.pi * j / na; vs.append((r_ * math.cos(a), r_ * math.sin(a), z))
    for i in range(nz):
        for j in range(na):
            a_ = i * (na + 1) + j; fs.append((a_, a_ + na + 1, a_ + na + 2, a_ + 1))
    o = mesh_obj(name, vs, fs, m, None, loc); smooth(o); o.data.materials.append(rim_m)
    nrm = o.data.polygons[0].normal; ctr = o.data.polygons[0].center
    s_ = o.modifiers.new("sol", "SOLIDIFY"); s_.thickness = thick; s_.material_offset_rim = 1
    s_.offset = 1.0 if nrm.dot(V(ctr.x, ctr.y, 0)) > 0 else -1.0
    return o
vwall_m = mat("vein_wall", (0.32, 0.12, 0.3), 0.32, coat=0.5, sss=0.3, sss_scale=0.03)
_vn = vwall_m.node_tree.nodes; _vl = vwall_m.node_tree.links
_vz = _vn.new("ShaderNodeTexNoise"); _vz.inputs["Scale"].default_value = 3.0; _vz.inputs["Detail"].default_value = 8.0
_vcr = _vn.new("ShaderNodeValToRGB"); _vl.new(_vz.outputs["Fac"], _vcr.inputs[0])
_vcr.color_ramp.elements[0].color = (0.22, 0.06, 0.2, 1); _vcr.color_ramp.elements[1].color = (0.55, 0.2, 0.4, 1)
_vl.new(_vcr.outputs[0], _vn["Principled BSDF"].inputs["Base Color"])
_vbp = _vn.new("ShaderNodeBump"); _vbp.inputs["Strength"].default_value = 0.3; _vl.new(_vz.outputs["Fac"], _vbp.inputs["Height"])
_vl.new(_vbp.outputs[0], _vn["Principled BSDF"].inputs["Normal"])
vrim_m = mat("vein_rim", (0.85, 0.55, 0.62), 0.4, sss=0.2, sss_scale=0.02)
def sinus(z, z0):                       # klapan cho'ntagi atrofida tomir biroz kengayadi
    return 0.06 * math.exp(-((z - z0 - 0.35) / 0.3) ** 2)
VALVE_Z = 0.0
vein = half_tube("vein", lambda z: VR + sinus(z, VALVE_Z), VZ0, VZ1, 120, 48, vwall_m, vrim_m, 0.06, tuple(CV))
plane("vein_bg", (16, 12), tuple(CV + V(0, 2.2, 0.6)), mat("vein_bg", (0.12, 0.02, 0.03), 0.85), rot=(90, 0, 0))
# klapan qopqoqlari (2 ta yarim): devordan (z0) markazga (z0+h) qiyshiq parda; shape key "close"
valve_m = mat("valve", (0.95, 0.75, 0.78), 0.35, alpha=0.55, sss=0.3, sss_scale=0.02)
def leaflet(name, a0, a1, z0, h, r_fn, loc, open_d=0.35, na=24, nt=10):
    vs = []; fs = []; vs2 = []
    for i in range(na + 1):
        a = a0 + (a1 - a0) * i / na; u = (i / na); lift = 0.12 * math.sin(math.pi * u)
        for k in range(nt + 1):
            t = k / nt; rr = r_fn(z0 + t * h)
            zb = z0 - 0.15 * math.sin(math.pi * u) * (1 - t)
            for dst, d in ((vs, rr * open_d), (vs2, rr * 0.97)):
                r_ = rr - t * d; dst.append((r_ * math.cos(a), r_ * math.sin(a), zb + t * (h + lift * 0)))
    for i in range(na):
        for k in range(nt):
            a_ = i * (nt + 1) + k; fs.append((a_, a_ + 1, a_ + nt + 2, a_ + nt + 1))
    o = mesh_obj(name, vs, fs, valve_m, None, loc); smooth(o)
    o.shape_key_add(name="Basis"); kb = o.shape_key_add(name="close", from_mix=False); kb.value = 0.0
    for v, c_ in zip(kb.data, vs2): v.co = c_
    s_ = o.modifiers.new("sol", "SOLIDIFY"); s_.thickness = 0.015
    return o, kb
VH = 0.75
rfn = lambda z: VR + sinus(z, VALVE_Z)
lfR, kR = leaflet("leafR", 0.0, math.pi / 2, VALVE_Z, VH, rfn, tuple(CV))
lfL, kL = leaflet("leafL", math.pi / 2, math.pi, VALVE_Z, VH, rfn, tuple(CV))
# qon tanachalari (bikonkav disk)
cell_m = mat("blood_cell", (0.55, 0.015, 0.015), 0.28, coat=0.5, sss=0.25, sss_scale=0.01, emit=0.05, emit_col=(0.6, 0, 0))
def cell_mesh(name="cell_me"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=1.0); o_ = bpy.context.object; me = o_.data; bpy.data.objects.remove(o_)
    for v in me.vertices:
        rr = math.hypot(v.co.x, v.co.y); dip = 0.55 * math.exp(-(rr / 0.45) ** 2)
        v.co.z = v.co.z * 0.42 * (1 - dip) if abs(v.co.z) > 0 else 0
    for p_ in me.polygons: p_.use_smooth = True
    me.materials.append(cell_m); me.name = name; return me
cmesh = cell_mesh()
def fill_keys(o, path_, frames, vals):
    """tez keyframe: vals[i] = (x,y,z) har frames[i] da"""
    setattr(o, path_, vals[0]); o.keyframe_insert(path_, frame=frames[0])
    fcs = sorted([fc for fc in fcurves(o) if fc.data_path == path_], key=lambda fc: fc.array_index)
    for i, fc in enumerate(fcs):
        fc.keyframe_points.add(len(frames) - 1)
        co = []
        for f, v in zip(frames, vals): co += [f, v[i]]
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * len(frames))          # 1 = LINEAR
        fc.update()
# oqim: kumulyativ masofa D(f) (birlik); har tanacha tezligi markazda kattaroq
PD0, PD1 = S["puddle"]; SL0, SL1 = S["slow"]; CL0, CL1 = S["clot"]; DT0, DT1 = S["detach"]
def speed(f):
    if PD0 - 4 <= f <= PD1: t = (f - PD0) / (PD1 - PD0); return 0.07 * (1 - t) ** 2.2 + 0.002
    if SL0 - 4 <= f <= SL1: return 0.0045
    if CL0 <= f <= CL1: return 0.0015
    if DT0 <= f <= DT1: return 0.0015 if f < F_RIP - 4 else min(0.09, 0.0015 + 0.012 * (f - F_RIP + 4))
    return 0.0
DCUM = {}; acc = 0.0
for f in range(1, END + 2): DCUM[f] = acc; acc += speed(f)
DTOT = acc
VFR = [f for f in range(PD0 - 6, DT1 + 3, 2)]
rc = random.Random(21); NC = int(os.environ.get("NCELLS", 420))
cells = []
VIS_V = rng("puddle", "slow", "clot", "detach")
for i in range(NC):
    rr = 0.21 * math.sqrt(rc.random()); a = rc.uniform(-0.5, math.pi + 0.5)
    x, y = rr * math.cos(a), max(-0.12, rr * math.sin(a))
    k_ = 1.35 - 0.75 * (rr / 0.21) ** 2
    z0 = rc.uniform(VZ1 - 0.2 - DTOT * 1.35 - 0.5, VZ1 + 0.2)
    o = bpy.data.objects.new(f"cell{i}", cmesh); sc.collection.objects.link(o); o.parent = None
    s_ = rc.uniform(0.042, 0.052); o.scale = (s_, s_, s_)
    o.rotation_euler = (rc.uniform(0, 6.28), rc.uniform(0, 6.28), rc.uniform(0, 6.28))
    vals = []
    for f in VFR:
        z = z0 + DCUM[f] * k_; wob = 0.01 * math.sin(f * 0.11 + i)
        vals.append((CV.x + x + wob, CV.y + y, CV.z + z))
    fill_keys(o, "location", VFR, vals)
    cells.append(o)
for o in cells: vis(o, VIS_V, recursive=False)
# tromb: o'ng klapan cho'ntagida (devor va qopqoq orasida) o'sadi, fibrin iplar; uzilib oqimga tushadi
CLOT_A = math.pi * 0.3
CLOT_P = CV + V((VR - 0.02) * math.cos(CLOT_A) * 0.78, (VR - 0.02) * math.sin(CLOT_A) * 0.78, VALVE_Z + 0.42)
clot_m = mat("clot", (0.1, 0.003, 0.006), 0.5, coat=0.25, sss=0.1, sss_scale=0.005)
_cn = clot_m.node_tree.nodes; _cl = clot_m.node_tree.links
_cv = _cn.new("ShaderNodeTexVoronoi"); _cv.inputs["Scale"].default_value = 9.0
_ccr = _cn.new("ShaderNodeValToRGB"); _cl.new(_cv.outputs["Distance"], _ccr.inputs[0])
_ccr.color_ramp.elements[0].color = (0.2, 0.004, 0.01, 1); _ccr.color_ramp.elements[1].color = (0.04, 0.0, 0.003, 1)
_cl.new(_ccr.outputs[0], _cn["Principled BSDF"].inputs["Base Color"])
_cbp = _cn.new("ShaderNodeBump"); _cbp.inputs["Strength"].default_value = 0.6; _cl.new(_cv.outputs["Distance"], _cbp.inputs["Height"])
_cl.new(_cbp.outputs[0], _cn["Principled BSDF"].inputs["Normal"])
def blob(name, r, m, seed, sub=4, amp=0.25):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r); o = bpy.context.object; o.name = name
    rn = random.Random(seed); bumps = [(V(rn.uniform(-1, 1), rn.uniform(-1, 1), rn.uniform(-1, 1)).normalized(), rn.uniform(0.3, 0.7)) for _ in range(14)]
    for v in o.data.vertices:
        n = v.co.normalized(); s_ = 1.0 + sum(amp * w * max(0.0, n.dot(d)) ** 6 for d, w in bumps)
        v.co = v.co * s_
    smooth(o); o.data.materials.append(m); return o
clotE = empty("clotE", tuple(CLOT_P))
clot = blob("clot", 1.0, clot_m, 5); clot.parent = clotE; clot.scale = (0.11, 0.09, 0.22)
fib_m = mat("fibrin", (0.95, 0.88, 0.7), 0.5, sss=0.3, sss_scale=0.005, emit=0.15, emit_col=(1, 0.9, 0.7))
fibs = []
rf = random.Random(9)
for i in range(16):
    a1 = rf.uniform(0, 6.28); a2 = a1 + rf.uniform(1.5, 3.5); z1 = rf.uniform(-0.18, 0.18); z2 = rf.uniform(-0.2, 0.2)
    p1 = V(0.1 * math.cos(a1), 0.08 * math.sin(a1), z1); p2 = V(0.12 * math.cos(a2), 0.1 * math.sin(a2), z2)
    mid = (p1 + p2) / 2 + V(rf.uniform(-0.05, 0.05), -0.06, rf.uniform(-0.05, 0.05))
    fibs.append(P.tube(f"fib{i}", [tuple(p1), tuple(mid), tuple(p2)], 0.0025, fib_m, clotE))
anchors = []        # tromb -> tomir devori iplari (uziladi)
for i in range(7):
    a = CLOT_A + rf.uniform(-0.45, 0.45); z = rf.uniform(-0.15, 0.2)
    wall = V(VR * math.cos(a), VR * math.sin(a), VALVE_Z + 0.42 + z) + CV - CLOT_P
    p1 = V(rf.uniform(-0.05, 0.05), rf.uniform(-0.03, 0.03), z * 0.8)
    anchors.append(P.tube(f"anchor{i}", [tuple(p1), tuple(p1.lerp(wall, 0.5) + V(0, -0.02, 0.02)), tuple(wall)], 0.005, fib_m, clotE))
# yopishgan tanachalar (tromb ichida)
stuck = []
for i in range(34):
    d = V(rf.uniform(-1, 1), rf.uniform(-1, 0.3), rf.uniform(-1, 1)).normalized()
    o = bpy.data.objects.new(f"stuck{i}", cmesh); sc.collection.objects.link(o); o.parent = clotE
    o.location = V(d.x * 0.1, d.y * 0.085, d.z * 0.21) * rf.uniform(0.85, 1.05)
    s_ = rf.uniform(0.04, 0.05); o.scale = (s_, s_, s_); o.rotation_euler = (rf.uniform(0, 6), rf.uniform(0, 6), rf.uniform(0, 6))
    stuck.append(o)
# o'sish: SL (tanachalar yig'iladi) -> CL (tromb kattalashadi, iplar) -> DT (uziladi, tepaga uchadi)
G0 = SL0 + 20
for f, s_ in ((1, 0.0), (G0, 0.05), (SL1, 0.45), (CL0 + 10, 0.55), (F_TROMB - 3, 0.85), (F_TROMB + 2, 1.05), (F_TROMB + 6, 1.0), (CL1, 1.08), (END, 1.08)):
    key(clotE, f, scale=(s_,) * 3)
for i, o in enumerate(stuck):
    f_in = int(SL0 + 6 + i * (SL1 - SL0 - 10) / len(stuck))
    for f, h in ((1, True), (f_in, False), (DT1 + 1, True)): o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
    interp(o, "CONSTANT", "hide_render")
for i, fb in enumerate(fibs):
    f_in = CL0 + 4 + i * 4
    P.tube_r(fb, 1, 0.0); P.tube_r(fb, f_in, 0.0); P.tube_r(fb, f_in + 8, 0.0025)
for i, an in enumerate(anchors):
    f_in = CL0 + 10 + i * 6; f_cut = F_RIP - 6 + i
    for f, v in ((1, 0.0), (f_in, 0.0), (f_in + 8, 0.005), (f_cut, 0.005), (f_cut + 1, 0.0)): P.tube_r(an, f, v)
# uzilish: silkinish, keyin oqim bilan tepaga uchadi (aylanib)
key(clotE, 1, loc=tuple(CLOT_P), rot=(0, 0, 0)); key(clotE, F_RIP - 6, loc=tuple(CLOT_P), rot=(0, 0, 0))
for k_, f in enumerate(range(F_RIP - 5, F_RIP + 1)):
    key(clotE, f, loc=tuple(CLOT_P + V(0.012 * (-1) ** k_, 0, 0.006 * k_)), rot=(0, 3 * (-1) ** k_, 0))
zc = CLOT_P.z; xc = CLOT_P.x; yc = CLOT_P.y
for f in range(F_RIP + 1, END + 1, 2):
    v_ = min(0.11, 0.008 * (f - F_RIP)); zc += v_ * 2
    xc += (CV.x - xc) * 0.12; yc += (CV.y + 0.02 - yc) * 0.12
    key(clotE, f, loc=(xc, yc, zc), rot=(0, (f - F_RIP) * 4.0, (f - F_RIP) * 2.5))
for o in [clot] + fibs + anchors: vis(o, rng("slow", "clot", "detach"), recursive=False)
# klapan: oqimda ochiq, turib qolganda yarim yopiq
for kb in (kR, kL): skey(kb, [(1, 0.0), (PD0, 0.0), (PD1, 0.4), (SL0, 0.45), (CL1, 0.5), (F_RIP, 0.5), (F_RIP + 8, 0.0)])
for o in (vein, lfR, lfL): vis(o, VIS_V, recursive=False)

# ======================================================================
# 6) NASOS STUDIYASI (140,0,0): ikki boldir mushagi venani siqadi, 2 klapan, tanachalar tepaga; keyin to'xtaydi
# ======================================================================
CP = V(140.0, 0.0, 0.0)
PU0, PU1 = S["pump"]
PR = 0.26; PZ0, PZ1 = -3.0, 3.4
SQ_LO, SQ_HI = -0.7, 0.9
def pinch(z): return math.exp(-((z - 0.1) / 0.55) ** 2)
pvein = half_tube("pvein", lambda z: PR, PZ0, PZ1, 140, 40, vwall_m, vrim_m, 0.05, tuple(CP))
pvein.shape_key_add(name="Basis"); kSQ = pvein.shape_key_add(name="squeeze", from_mix=False); kSQ.value = 0.0
for v, v0 in zip(kSQ.data, pvein.data.vertices):
    z = v0.co.z; f_ = 1.0 - 0.5 * pinch(z); v.co = V(v0.co.x * f_, v0.co.y * f_, z)
pv_lo = [leaflet(f"pvl{s}", a0, a1, -1.25, 0.55, lambda z: PR, tuple(CP), open_d=0.3) for s, (a0, a1) in enumerate(((0, math.pi / 2), (math.pi / 2, math.pi)))]
pv_hi = [leaflet(f"pvh{s}", a0, a1, 1.25, 0.55, lambda z: PR, tuple(CP), open_d=0.3) for s, (a0, a1) in enumerate(((0, math.pi / 2), (math.pi / 2, math.pi)))]
musc_m = mat("muscle", (0.62, 0.08, 0.09), 0.35, coat=0.3, sss=0.3, sss_scale=0.05)
_mn = musc_m.node_tree.nodes; _ml = musc_m.node_tree.links
_wv = _mn.new("ShaderNodeTexWave"); _wv.wave_type = "BANDS"; _wv.bands_direction = "Z"; _wv.inputs["Scale"].default_value = 30.0
_wv.inputs["Distortion"].default_value = 3.0; _tcm = _mn.new("ShaderNodeTexCoord"); _ml.new(_tcm.outputs["Generated"], _wv.inputs["Vector"])
_mm = _mn.new("ShaderNodeMix"); _mm.data_type = "RGBA"; _mm.inputs[6].default_value = (0.7, 0.1, 0.1, 1); _mm.inputs[7].default_value = (0.38, 0.03, 0.05, 1)
_ml.new(_wv.outputs["Fac"], _mm.inputs["Factor"]); _ml.new(_mm.outputs[2], _mn["Principled BSDF"].inputs["Base Color"])
_bp = _mn.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.4; _ml.new(_wv.outputs["Fac"], _bp.inputs["Height"])
_ml.new(_bp.outputs[0], _mn["Principled BSDF"].inputs["Normal"])
musc = []
for sx in (-1, 1):
    m_ = sphere(f"musc{sx}", 1.0, tuple(CP + V(sx * 0.82, 0.25, 0.1)), musc_m, sub=4); musc.append((m_, sx))
cycles = [PU0 + 6 + 24 * k for k in range(4) if PU0 + 6 + 24 * k + 12 < F_STOP]
for m_, sx in musc:
    key(m_, 1, loc=tuple(CP + V(sx * 0.82, 0.25, 0.1)), scale=(0.5, 0.5, 1.7))
    for c0 in cycles:
        key(m_, c0, loc=tuple(CP + V(sx * 0.82, 0.25, 0.1)), scale=(0.5, 0.5, 1.7))
        key(m_, c0 + 7, loc=tuple(CP + V(sx * 0.66, 0.25, 0.1)), scale=(0.64, 0.6, 1.55))
        key(m_, c0 + 14, loc=tuple(CP + V(sx * 0.82, 0.25, 0.1)), scale=(0.5, 0.5, 1.7))
    key(m_, F_STOP + 6, loc=tuple(CP + V(sx * 0.86, 0.25, 0.08)), scale=(0.48, 0.5, 1.72))
skey(kSQ, [(1, 0.0)] + [p for c0 in cycles for p in ((c0, 0.0), (c0 + 7, 1.0), (c0 + 14, 0.0))])
for kb in (pv_lo[0][1], pv_lo[1][1]):       # siqilganda pastki klapan yopiq, bo'shashganda ochiq
    skey(kb, [(1, 0.0)] + [p for c0 in cycles for p in ((c0, 0.0), (c0 + 4, 1.0), (c0 + 12, 1.0), (c0 + 17, 0.0))] + [(F_STOP + 6, 0.55)])
for kb in (pv_hi[0][1], pv_hi[1][1]):
    skey(kb, [(1, 1.0)] + [p for c0 in cycles for p in ((c0, 1.0), (c0 + 3, 0.0), (c0 + 11, 0.0), (c0 + 15, 1.0))] + [(F_STOP + 6, 0.55)])
# tanachalar: siqilganda tepaga 1.0 birlik suriladi, to'xtagach joyida qoladi
def pump_D(f):
    d = 0.0
    for c0 in cycles: d += 1.05 * ease(min(1.0, max(0.0, (f - c0) / 10.0)))
    if f > F_STOP: d += 0.0
    return d
NP = 220; rp = random.Random(4); pcells = []
PFR = list(range(PU0 - 2, PU1 + 3, 1))
for i in range(NP):
    rr = 0.16 * math.sqrt(rp.random()); a = rp.uniform(-0.4, math.pi + 0.4)
    x, y = rr * math.cos(a), max(-0.08, rr * math.sin(a))
    z0 = rp.uniform(PZ0 - 4.2, PZ1)
    o = bpy.data.objects.new(f"pcell{i}", cmesh); sc.collection.objects.link(o)
    s_ = rp.uniform(0.038, 0.046); o.scale = (s_,) * 3; o.rotation_euler = (rp.uniform(0, 6), rp.uniform(0, 6), rp.uniform(0, 6))
    vals = []
    for f in PFR:
        z = z0 + pump_D(f) * rp.uniform(0.95, 1.05) if False else z0 + pump_D(f)
        sq = 0.0
        for c0 in cycles:
            if c0 <= f <= c0 + 14: sq = max(sq, math.sin(math.pi * (f - c0) / 14.0))
        f_ = 1.0 - 0.45 * sq * pinch(z)
        vals.append((CP.x + x * f_, CP.y + y * f_, CP.z + z))
    fill_keys(o, "location", PFR, vals); pcells.append(o)
# tepaga sariq strelkalar (faqat nasos ishlaganda)
arr_m = mat("arrow", (1.0, 0.6, 0.02), 0.5, emit=5.0)
arrows = []
for i, sx in enumerate((-1, 1)):
    a_ = arrow(f"parrow{i}", arr_m, s=6.0); a_.rotation_euler = (R(180), 0, 0)
    for c0 in cycles:
        key(a_, c0, loc=tuple(CP + V(sx * 0.4, -0.45, -0.6)), scale=(0.01,) * 3)
        key(a_, c0 + 3, loc=tuple(CP + V(sx * 0.4, -0.45, -0.3)), scale=(1.0,) * 3)
        key(a_, c0 + 14, loc=tuple(CP + V(sx * 0.4, -0.45, 0.9)), scale=(1.0,) * 3)
        key(a_, c0 + 17, loc=tuple(CP + V(sx * 0.4, -0.45, 1.1)), scale=(0.01,) * 3)
    key(a_, 1, scale=(0.01,) * 3)
    arrows.append(a_)
pbg = plane("pump_bg", (16, 14), tuple(CP + V(0, 2.4, 0.4)), mat("pump_bg", (0.1, 0.02, 0.03), 0.85), rot=(90, 0, 0))
PUMP_OBJ = [pvein, pbg] + [o for o, _ in pv_lo + pv_hi] + [m_ for m_, _ in musc] + pcells
for o in PUMP_OBJ: vis(o, rng("pump"), recursive=False)
for a_ in arrows: vis(a_, [(PU0, F_STOP)])

# ======================================================================
# 7) O'PKA STUDIYASI (180,0,0): ikki o'pka (shaffof pushti), o'pka arteriyasi daraxti, yurak; tromb tiqiladi
#    1 birlik ~ 10 sm
# ======================================================================
CL = V(180.0, 0.0, 0.0)
LU0, LU1 = S["lung"]; LD0, LD1 = S["lungdark"]
def lung_material(name):
    lung_m = bpy.data.materials.new(name); lung_m.use_nodes = True
    N = lung_m.node_tree.nodes; L = lung_m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 10.0; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 26.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.75, 0.28, 0.32, 1); cr.color_ramp.elements[1].color = (0.98, 0.62, 0.62, 1)
    # o'lik (qon kelmaydigan) zona: Object koordinatasida nuqtadan masofa < DEAD radius
    dead_r = value_node(lung_m, "DEAD", 0.0)
    dp = N.new("ShaderNodeVectorMath"); dp.operation = "DISTANCE"; L.new(tc.outputs["Object"], dp.inputs[0]); dp.inputs[1].default_value = (0.25, 0.0, 0.35)
    dm = P.math_n(N, L, "SUBTRACT", dead_r, dp.outputs["Value"])
    dmask = P.math_n(N, L, "MULTIPLY", dm, 3.0, clamp=True)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(dmask, mx.inputs["Factor"])
    L.new(cr.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.3, 0.27, 0.36, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.5
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.05
    alpha_v = value_node(lung_m, "ALPHA", 0.45); L.new(P.math_n(N, L, "ADD", alpha_v, P.math_n(N, L, "MULTIPLY", dmask, 0.45), clamp=True), b.inputs["Alpha"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
    L.new(P.math_n(N, L, "ADD", nz.outputs["Fac"], P.math_n(N, L, "MULTIPLY", vo.outputs["Distance"], 0.5)), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, dmask), 0.25), b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (1.0, 0.35, 0.35, 1)
    return lung_m, dp
lung_mL, _ = lung_material("lungL")
lung_m, dp = lung_material("lungR")
def lung_mesh(name, sx):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0); o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        x, y, z = v.co
        w = 1.0 - 0.25 * z                     # tepasi tor, pasti keng
        x2 = x * 0.95 * w; y2 = y * 0.75 * w
        if x * sx < 0: x2 *= 0.55             # ichki (yurak) tomoni yassi
        if z < -0.6: z = -0.6 + (z + 0.6) * 0.4
        v.co = V(x2, y2, z * 1.55)
    smooth(o); o.data.materials.append(lung_m if sx > 0 else lung_mL); o.location = CL + V(sx * 0.95, 0.0, 0.25); return o
lungs = [lung_mesh(f"lung{sx}", sx) for sx in (-1, 1)]
art_m = P.pulse_material("partery", (0.03, 0.1, 0.6), base_emit=0.35, pulse_col=(0.15, 0.4, 1.0), width=0.08)
blk_m = mat("blocked", (0.12, 0.12, 0.16), 0.5, emit=0.0)
blk_mix = P.pulse_material("partery_b", (0.03, 0.1, 0.6), base_emit=0.35, pulse_col=(0.15, 0.4, 1.0), width=0.08)
def no_trail(m_):
    for n in m_.node_tree.nodes:
        if n.type == "MATH" and n.operation == "MULTIPLY" and abs(n.inputs[1].default_value - 4.0) < 1e-6: n.inputs[1].default_value = 0.0
        if n.type == "MATH" and n.operation == "MULTIPLY" and abs(n.inputs[1].default_value - 40.0) < 1e-6: n.inputs[1].default_value = 6.0
no_trail(art_m); no_trail(blk_mix)
heartL = sphere("l_heart", 0.42, tuple(CL + V(0.1, -0.15, -1.2)), mat("l_heart_m", (0.62, 0.03, 0.04), 0.3, coat=0.6, sss=0.3), scale=(1.1, 0.9, 1.0), sub=4)
for fr in range(LU0 - 2, END + 1, 12):
    key(heartL, fr, scale=(1.1, 0.9, 1.0)); key(heartL, fr + 4, scale=(1.22, 1.0, 1.1))
TRUNK0 = CL + V(0.1, -0.15, -0.85); TRUNK1 = CL + V(0.0, -0.05, -0.15)
rt = random.Random(11); arts = []; blocked = []
P.tube("trunk", [tuple(TRUNK0), tuple(TRUNK0.lerp(TRUNK1, 0.5) + V(-0.05, 0, 0)), tuple(TRUNK1)], 0.085, art_m, None)
arts.append(bpy.data.objects["trunk"])
LODGE = None; LODGE_PATH = None
def grow(p0, d, ln, rad, lvl, side, path_, mat_, tag):
    global LODGE, LODGE_PATH
    p1 = p0 + d * ln
    mid = p0.lerp(p1, 0.5) + V(rt.uniform(-1, 1), rt.uniform(-0.4, 0.4), rt.uniform(-1, 1)) * ln * 0.1
    is_lodge = (tag == "RL" and LODGE is None)
    m_here = mat_
    o = P.tube(f"art{len(arts)}", [tuple(p0), tuple(mid), tuple(p1)], rad, m_here, None, taper=[1, 0.9, 0.8]); arts.append(o)
    if mat_ is blk_mix: blocked.append(o)
    path2 = path_ + [p1]
    if is_lodge:
        LODGE = p1.copy(); LODGE_PATH = list(path2); mat_ = blk_mix          # shu nuqtadan keyingi shoxlar qon olmaydi
    if lvl >= 5: return
    for k in (-1, 1):
        ang = R(rt.uniform(24, 40)) * k
        ax = d.cross(V(0, 1, 0)).normalized()
        nd = (Quaternion(ax, ang) @ d)
        nd = (Quaternion(d, R(rt.uniform(-50, 50))) @ nd).normalized()
        nd = (nd + V(side * 0.12, 0, -0.05)).normalized()
        grow(p1, nd, ln * rt.uniform(0.66, 0.78), rad * 0.7, lvl + 1, side, path2, mat_, tag + ("L" if k < 0 else "R"))
for sx in (-1, 1):
    d0 = V(sx * 0.85, 0.05, 0.45).normalized()
    grow(TRUNK1, d0, 0.55, 0.06, 1, sx, [TRUNK0, TRUNK1], art_m, "R" if sx > 0 else "L")
print("LODGE", LODGE)
# bloklangan shoxlar: impuls kelmaydi, kulrangga o'tadi
bb = blk_mix.node_tree.nodes["Principled BSDF"]
for f, c_, g_ in ((1, (0.03, 0.1, 0.6), 0.35), (F_LODGE, (0.03, 0.1, 0.6), 0.35), (F_LODGE + 14, (0.14, 0.14, 0.18), 0.02), (END, (0.12, 0.12, 0.15), 0.0)):
    bb.inputs["Base Color"].default_value = (*c_, 1); bb.inputs["Base Color"].keyframe_insert("default_value", frame=f); val_key(blk_mix, "glow", f, g_)
for m_, last in ((art_m, END), (blk_mix, F_LODGE - 12)):
    ks = [(1, -0.1)]
    for c0 in range(LU0 - 12, last + 1, 12): ks += [(c0, -0.1), (c0 + 11, 1.1)]
    for f, v in ks: val_key(m_, "pos", f, v)
    val_key(m_, "pos", last + 12, -0.1)
    interp(m_.node_tree, "LINEAR")
# o'lik zona o'sadi
for f, v in ((1, 0.0), (F_LODGE, 0.0), (LU1, 0.8), (LD0, 0.85), (LD1, 1.55), (END, 1.7)): val_key(lung_m, "DEAD", f, v)
dp.inputs[1].default_value = tuple((LODGE - lungs[1].location) + V(0.15, 0, 0.1)) if LODGE else (0.25, 0, 0.35)
# tromb (o'pka masshtabida): trunk -> o'ng arteriya -> tiqiladi
lclotE = empty("lclotE", tuple(TRUNK0))
lclot = blob("lclot", 1.0, clot_m, 6); lclot.parent = lclotE; lclot.scale = (0.05, 0.05, 0.11)
lpath = catmull(LODGE_PATH, step=0.01)
for f in range(LU0, F_LODGE + 1):
    t = ease(min(1.0, max(0.0, (f - LU0) / float(F_LODGE - LU0))))
    i = min(len(lpath) - 1, int(t * (len(lpath) - 1))); p_ = lpath[i]
    j = min(len(lpath) - 1, i + 3); d_ = (lpath[j] - p_)
    lclotE.location = p_ - d_.normalized() * 0.06 if d_.length > 1e-6 else p_; lclotE.keyframe_insert("location", frame=f)
    if d_.length > 1e-6:
        lclotE.rotation_mode = "QUATERNION"; lclotE.rotation_quaternion = V(0, 0, 1).rotation_difference(d_.normalized()); lclotE.keyframe_insert("rotation_quaternion", frame=f)
# signal: tiqilgan joyda qizil nur, keyin lungdark da butun o'pka miltillaydi
alarm_m = glow_mat("alarm", (1.0, 0.05, 0.02))
alarm = sphere("alarm", 0.16, tuple(LODGE), alarm_m, sub=4)
for f, v in ((1, 0.0), (F_LODGE - 1, 0.0), (F_LODGE, 8.0), (F_LODGE + 6, 2.0)): val_key(alarm_m, "a", f, v)
for f in range(F_LODGE + 6, END, 12): val_key(alarm_m, "a", f, 4.0); val_key(alarm_m, "a", f + 6, 10.0)
for m_ in (lung_m, lung_mL):
    for f, v in ((1, 0.45), (LD0, 0.45), (LD1, 0.6)): val_key(m_, "ALPHA", f, v)
for f, v in ((1, 0.0), (LD0, 0.0), (LD1, 0.95), (END, 1.1)): val_key(lung_mL, "DEAD", f, v)
lbg = plane("lung_bg", (20, 16), tuple(CL + V(0, 3.0, 0.4)), mat("lung_bg", (0.015, 0.02, 0.04), 0.9), rot=(90, 0, 0))
LUNG_OBJ = lungs + arts + [heartL, lclot, alarm, lbg]
for o in LUNG_OBJ: vis(o, rng("lung", "lungdark"), recursive=False)
# bronxlar/traxeya (oq, faqat ko'rinish uchun)
tra_m = mat("trachea", (0.85, 0.8, 0.75), 0.4, sss=0.2)
tra = P.tube("trachea", [tuple(CL + V(0, 0.35, 2.6)), tuple(CL + V(0, 0.35, 1.7)), tuple(CL + V(0, 0.35, 1.2))], 0.13, tra_m, None)
for sx in (-1, 1):
    P.tube(f"bronch{sx}", [tuple(CL + V(0, 0.35, 1.2)), tuple(CL + V(sx * 0.4, 0.33, 0.95)), tuple(CL + V(sx * 0.75, 0.3, 0.7))], 0.08, tra_m, None)
for o in [tra] + [bpy.data.objects[f"bronch{sx}"] for sx in (-1, 1)]: vis(o, rng("lung", "lungdark"), recursive=False)

# ======================================================================
# 8) KAMERALAR (har kadrda harakat: crash zoom, aylanma, ergashish, silkinish)
# ======================================================================
def mid_pos(f, b_): sc.frame_set(f); return bw(b_)
# 1 hook: yo'lak oldidan past burchak, qizga uchib boradi
H0, H1 = S["hook"]
sc.frame_set(H1); HEADP = faceT.matrix_world.translation.copy()
ht = tgt_path("hook_tgt", [(H0, tuple(HEADP + V(-0.3, 0.1, -0.35))), (H1 - 14, tuple(HEADP + V(0, 0, -0.08))), (H1, tuple(HEADP))])
c = shot_cam("hook", (0, 0, 0), ht, 16, fstop=2.8, clip=0.02)
path(c, [(H0, (MEG_X - 5.2, 0.0, 0.5)), (H1 - 14, (MEG_X - 1.3, 0.1, 0.9)), (H1, (MEG_X - 0.6, 0.05, 1.1))])
lens_keys(c, [(H0, 16), (H1 - 14, 18), (H1 - 4, 30), (H1, 32)]); shake(c, H1 - 6, H1, 0.01, seed=1)
# 2 desk: yelka ortidan monitor + soat; sekin aylanma
sc.frame_set(D0 + 30); dhead = faceT.matrix_world.translation.copy()
dt_ = tgt_path("desk_tgt", [(D0, tuple(RM + V(-0.2, -0.95, 1.2))), (D1, tuple(RM + V(-0.5, -1.2, 1.5)))])
c = shot_cam("desk", (0, 0, 0), dt_, 22, fstop=4.0, clip=0.02)
path(c, [(D0, tuple(RM + V(0.75, 0.75, 1.45))), (D1, tuple(RM + V(0.35, 0.55, 1.35)))])
c.data.dof.focus_object = clk
# 3 xlegs: boshdan oyoqqa aylanib tushadi (yo'lak tomondan)
X0, X1 = S["xlegs"]
xt = tgt_path("xlegs_tgt", [(X0, tuple(XG["HEART"])), (X1, tuple(XG["legs"]["Left"]["knee"].lerp(XG["legs"]["Left"]["ank"], 0.5)))])
c = shot_cam("xlegs", (0, 0, 0), xt, 22, clip=0.02)
path(c, [(X0, (MEG_X - 1.0, -0.05, 1.4)), (X1, (MEG_X - 0.85, -0.2, 0.5))])
# 4 puddle: vena ichida, oqim bo'ylab sirpanadi
t_ = tgt_path("pud_tgt", [(PD0, (0, 0.1, 1.3)), (PD1, (0, 0.12, 0.6))], CV)
c = shot_cam("puddle", (0, 0, 0), t_, 24, fstop=5.6, clip=0.05)
path(c, [(PD0, (0.35, -1.6, -0.4)), (PD1, (0.15, -1.25, 0.05))], CV)
# 5 calf: boldir mushagi, yondan push-in
CA0, CA1 = S["calf"]
cm_ = bpy.data.objects["xs_calfRight"].location.copy()
ct = empty("calf_tgt", tuple(cm_))
c = shot_cam("calf", (0, 0, 0), ct, 30, fstop=4.0, clip=0.02)
path(c, [(CA0, (cm_.x - 0.55, cm_.y + 0.3, cm_.z + 0.25)), (CA1, (cm_.x - 0.4, cm_.y + 0.22, cm_.z + 0.12))])
# 6 pump: oldidan, to'xtaganda silkinish
t_ = tgt_path("pump_tgt", [(PU0, (0, 0, 0.3)), (F_STOP, (0, 0, 0.2)), (PU1, (0, 0, 0.1))], CP)
c = shot_cam("pump", (0, 0, 0), t_, 26, fstop=8, clip=0.05)
path(c, [(PU0, (0.9, -5.2, 0.9)), (F_STOP, (0.3, -4.1, 0.4)), (PU1, (0.1, -3.4, 0.2))], CP)
shake(c, F_STOP, F_STOP + 10, 0.05, seed=2)
# 7 slow: klapan cho'ntagiga sekin push-in
t_ = tgt_path("slow_tgt", [(SL0, (0.05, 0.1, 0.9)), (SL1, tuple(CLOT_P - CV + V(-0.05, 0, 0.05)))], CV)
c = shot_cam("slow", (0, 0, 0), t_, 26, fstop=5.6, clip=0.05)
path(c, [(SL0, (-0.4, -1.9, 1.6)), (SL1, (-0.1, -1.25, 0.85))], CV)
# 8 clot: tromb o'sadi, "tromb" da crash zoom
t_ = empty("clot_tgt", tuple(CLOT_P + V(-0.03, 0, 0.0)))
c = shot_cam("clot", (0, 0, 0), t_, 28, fstop=5.6, clip=0.03)
path(c, [(CL0, tuple(CLOT_P + V(-0.6, -1.6, 0.45))), (F_TROMB - 4, tuple(CLOT_P + V(-0.45, -1.3, 0.3))),
         (F_TROMB + 2, tuple(CLOT_P + V(-0.3, -0.85, 0.15))), (CL1, tuple(CLOT_P + V(-0.26, -0.78, 0.12)))])
lens_keys(c, [(CL0, 26), (F_TROMB - 3, 28), (F_TROMB + 2, 36), (CL1, 38)]); shake(c, F_TROMB, F_TROMB + 8, 0.02, seed=3)
# 9 face: yuzga yaqin plan
FA0, FA1 = S["face"]
c = shot_cam("face", (0, 0, 0), faceT, 32, fstop=2.0, clip=0.02)
sc.frame_set(FA0 + 10); FP = faceT.matrix_world.translation.copy()
path(c, [(FA0, tuple(V(MEG_X - 0.44, MEG_Y + 0.16, FP.z + 0.02))), (FA1, tuple(V(MEG_X - 0.36, MEG_Y + 0.1, FP.z + 0.0)))])
lens_keys(c, [(FA0, 24), (FA1, 32)])
# 10 stand: yo'lakdan past burchak, qiz turib kameraga qarab yuradi
ST0, ST1 = S["stand"]
sc.frame_set(ST1); WP = bw("Hips")
stt = tgt_path("stand_tgt", [(ST0, (MEG_X - 0.2, MEG_Y + 0.05, 0.95)), (ST1, (WP.x, WP.y, 1.15))])
c = shot_cam("stand", (0, 0, 0), stt, 18, fstop=2.8, clip=0.02)
path(c, [(ST0, (MEG_X - 2.2, 0.1, 0.3)), (ST1, (MEG_X - 2.6, 0.05, 0.42))])
# 11 detach: tromb uziladi, kamera ergashadi
t_ = tgt_path("det_tgt", [(DT0, tuple(CLOT_P)), (F_RIP, tuple(CLOT_P)), (DT1, tuple(CV + V(0.05, 0.05, CLOT_P.z - CV.z + 1.4)))])
c = shot_cam("detach", (0, 0, 0), t_, 26, fstop=5.6, clip=0.03)
path(c, [(DT0, tuple(CLOT_P + V(-0.3, -0.75, 0.05))), (F_RIP, tuple(CLOT_P + V(-0.25, -0.68, 0.05))), (DT1, tuple(CV + V(-0.2, -1.5, 1.2)))])
shake(c, F_RIP - 6, F_RIP + 6, 0.025, seed=4); c.data.dof.focus_object = clotE
# 12 travel: rentgen, tromb nuqtasiga ergashib pastdan tepaga
DT_ = empty("trav_tgt"); cpl = DT_.constraints.new("COPY_LOCATION"); cpl.target = dot
c = shot_cam("travel", (0, 0, 0), DT_, 24, clip=0.02)
for f, p_ in DOT_F[::4] + [DOT_F[-1]]:
    key(c, f, loc=(p_.x - 0.85, 0.12, p_.z + 0.05 + 0.1 * (f - TR0) / (TR1 - TR0)))
# 13 lung: tromb trunk bo'ylab ko'tariladi, tiqilganda zarba
c = shot_cam("lung", (0, 0, 0), None, 22, clip=0.05)
lt = tgt_path("lung_tgt", [(LU0, tuple(TRUNK0.lerp(TRUNK1, 0.5))), (F_LODGE, tuple(LODGE)), (LU1, tuple(LODGE + V(0.1, 0, 0.1)))])
aim(c, lt)
path(c, [(LU0, tuple(CL + V(0.9, -5.2, -0.6))), (F_LODGE - 4, tuple(CL + V(0.6, -4.2, 0.0))), (F_LODGE + 2, tuple(LODGE + V(-0.35, -3.3, 0.15))), (LU1, tuple(LODGE + V(-0.4, -3.0, 0.2)))])
shake(c, F_LODGE, F_LODGE + 10, 0.04, seed=5)
# 14 choke: past burchak, qiz ko'kragini changallab tizzaga cho'kadi
CH0, CH1 = S["choke"]
sc.frame_set(CH0 + 4); CP0 = bw("Hips"); sc.frame_set(CH1); CP1 = bw("Head")
cht = tgt_path("choke_tgt", [(CH0, tuple(CP0 + V(0, 0, 0.62))), (CH0 + 30, tuple(CP0 + V(-0.15, 0, 0.3))), (CH1, tuple(CP1 + V(0, 0, 0.1)))])
c = shot_cam("choke", (0, 0, 0), cht, 20, fstop=2.8, clip=0.02)
path(c, [(CH0, tuple(V(CP0.x - 1.9, 0.12, 0.35))), (CH1, tuple(V(CP0.x - 2.2, 0.05, 0.28)))])
shake(c, CH0 + 40, CH0 + 52, 0.02, seed=6)
# 15 lungdark: o'pkalar qorayadi, sekin aylanma
lc = empty("ld_ctr", tuple(CL + V(0.2, 0, 0.2)))
orbit_cam("lungdark", LD0, LD1, CL + V(0, 0, 0.1), 5.6, 5.0, -70, -110, 0.6, 0.3, 24, lc)
# 16 end: tepadan, qiz yo'lakda yotibdi
E0, E1 = S["end"]
sc.frame_set(E0 + 10); EH = bw("Hips")
et = empty("end_tgt", tuple(EH + V(-0.2, 0, 0)))
c = shot_cam("end", (0, 0, 0), et, 16, clip=0.02)
path(c, [(E0, tuple(EH + V(0.6, 0.05, 1.6))), (E1, tuple(EH + V(0.75, 0.05, 2.0)))])
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 9) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
WN = w.node_tree.nodes; WL = w.node_tree.links
bg = WN["Background"]; bg.inputs["Color"].default_value = (0.01, 0.015, 0.03, 1); bg.inputs["Strength"].default_value = 1.0
env = WN.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
bg2 = WN.new("ShaderNodeBackground"); WL.new(env.outputs[0], bg2.inputs["Color"]); bg2.inputs["Strength"].default_value = 1.2
mixw = WN.new("ShaderNodeMixShader"); hv = WN.new("ShaderNodeValue"); hv.name = "hdri"
WL.new(hv.outputs[0], mixw.inputs[0]); WL.new(bg.outputs[0], mixw.inputs[1]); WL.new(bg2.outputs[0], mixw.inputs[2])
WL.new(mixw.outputs[0], WN["World Output"].inputs["Surface"])
hk = [(1, 0.0)]
for a, b_ in CABIN_REAL: hk += [(a, 1.0), (b_ + 1, 0.0)]
for a, b_ in XR_SEAT + XR_STAND: hk += [(a, 0.25), (b_ + 1, 0.0)]
for f, v in sorted(hk): hv.outputs[0].default_value = v; hv.outputs[0].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# salon
ceil_l = area("cabin_light", (0, 0, 2.3), 1.0, (1.0, 0.88, 0.72), lights_for(CABIN_REAL, 900.0), shape=(10, 0.6))
ceil_l.data.shape = "RECTANGLE"; ceil_l.data.size = 10; ceil_l.data.size_y = 0.6
for f, v in ((E0, 900.0), (E1, 350.0)): ceil_l.data.energy = v; ceil_l.data.keyframe_insert("energy", frame=f)
area("x_dim", (0, 0, 2.3), 1.0, (0.3, 0.45, 0.9), lights_for(XR_SEAT + XR_STAND, 140.0), shape=(10, 0.6))
area("win_fill", (MEG_X - 0.3, -1.55, 1.15), 0.6, (0.85, 0.92, 1.0), lights_for(rng("hook", "face"), 25.0), target=faceT)
area("face_key", (MEG_X - 0.9, 0.5, 1.6), 0.5, (1.0, 0.92, 0.85), lights_for(rng("face", "stand", "choke"), 30.0), target=faceT)
area("aisle_key", (MEG_X - 3.0, 0.0, 1.7), 1.0, (1.0, 0.92, 0.85), lights_for(rng("stand", "choke", "end"), 120.0), target=chestE)
# xona
dk = [(1, 0)]; area("r_ceil_l", tuple(RM + V(0.2, -0.2, 2.7)), 1.2, (1.0, 0.95, 0.88), lights_for(rng("desk"), 160.0), target=empty("r_t", tuple(RM + V(0, -0.5, 0.8))))
wl = area("r_window_l", tuple(RM + V(-1.6, 0.5, 1.6)), 1.2, (1.0, 0.95, 0.85), [(1, 0)], target=empty("r_t2", tuple(RM + V(0, -0.3, 1.0))))
for f, e, col in ((D0, 260.0, (0.85, 0.92, 1.0)), (D0 + 40, 200.0, (1.0, 0.55, 0.25)), (D1, 30.0, (0.3, 0.4, 1.0)), (D1 + 1, 0.0, (0.3, 0.4, 1.0))):
    wl.data.energy = e; wl.data.color = col; wl.data.keyframe_insert("energy", frame=f); wl.data.keyframe_insert("color", frame=f)
interp(wl.data, "LINEAR")
ml = area("r_monitor_l", tuple(MON + V(0, 0.15, 0.36)), 0.5, (0.6, 0.8, 1.0), lights_for(rng("desk"), 14.0), target=faceT)
# vena studiyasi
vT = empty("vein_lt", tuple(CV + V(0, 0.1, 0.4)))
VS = rng("puddle", "slow", "clot", "detach")
area("v_key", tuple(CV + V(-1.4, -2.4, 1.9)), 1.5, (1.0, 0.92, 0.86), lights_for(VS, 380.0), target=vT)
area("v_rim", tuple(CV + V(1.7, 0.3, 1.0)), 1.0, (0.8, 0.88, 1.0), lights_for(VS, 160.0), target=vT)
area("v_in", tuple(CV + V(0.0, -1.0, 0.4)), 0.5, (1.0, 0.8, 0.7), lights_for(VS, 35.0), target=vT)
fl = point("tromb_flash", tuple(CLOT_P + V(-0.1, -0.4, 0.1)), 0.1, (1.0, 0.25, 0.15), [(1, 0)], const=False)
for f, v in ((F_TROMB - 1, 0), (F_TROMB, 40), (F_TROMB + 6, 6), (F_TROMB + 14, 0), (F_RIP - 1, 0), (F_RIP, 35), (F_RIP + 8, 0)):
    fl.data.energy = v; fl.data.keyframe_insert("energy", frame=f)
fl.visible_camera = False
# nasos
pT = empty("pump_lt", tuple(CP + V(0, 0, 0.2)))
pk_ = area("p_key", tuple(CP + V(-1.8, -3.0, 2.2)), 1.8, (1.0, 0.92, 0.86), [(1, 0), (PU0, 520.0), (F_STOP, 520.0), (F_STOP + 8, 200.0), (PU1 + 1, 0)], target=pT)
interp(pk_.data, "LINEAR")
area("p_rim", tuple(CP + V(2.2, 0.4, 1.2)), 1.2, (0.8, 0.88, 1.0), lights_for(rng("pump"), 240.0), target=pT)
area("p_low", tuple(CP + V(0.3, -2.0, -1.6)), 0.8, (1.0, 0.85, 0.75), lights_for(rng("pump"), 70.0), target=pT)
# o'pka
lT = empty("lung_lt", tuple(CL + V(0, 0, 0.2)))
LS = rng("lung", "lungdark")
area("l_key", tuple(CL + V(-2.5, -4.0, 2.5)), 2.0, (1.0, 0.92, 0.86), lights_for(LS, 600.0), target=lT)
area("l_rim", tuple(CL + V(3.0, 1.0, 1.5)), 1.5, (0.7, 0.85, 1.0), lights_for(LS, 400.0), target=lT)
ar = point("l_alarm", tuple(LODGE + V(0, -0.5, 0)), 0.2, (1.0, 0.08, 0.04), [(1, 0)], const=False)
for f in range(F_LODGE, END, 12):
    ar.data.energy = 10 if f < LD0 else 30; ar.data.keyframe_insert("energy", frame=f)
    ar.data.energy = 60 if f < LD0 else 140; ar.data.keyframe_insert("energy", frame=f + 6)
ar.visible_camera = False

# voqea kadrlari (tovush effektlari uchun)
if os.environ.get("EVENTS"):
    import json
    json.dump({"shots": SHOTS, "stop": F_STOP, "tromb": F_TROMB, "rip": F_RIP, "lodge": F_LODGE, "stand": F_STAND, "walk": F_WALK,
               "die": F_DIE, "knees": F_DIE + 44, "floor": F_DIE + 66, "cycles": cycles, "end": END}, open(os.environ["EVENTS"], "w"))
if os.environ.get("DBG"):
    for f in map(int, os.environ["DBG"].split(",")):
        sc.frame_set(f); print("DBG", f, [(b_, tuple(round(v, 2) for v in bw(b_))) for b_ in ("Hips", "Head", "LeftFoot")], tuple(round(v, 2) for v in mroot.location))

# ======================================================================
# 10) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = 0.0
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = os.environ.get("PERSIST", "0") == "1"
r.use_overwrite = False; r.use_placeholder = True
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
