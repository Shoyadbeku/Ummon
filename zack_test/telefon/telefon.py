# "Bir ko'z bilan telefon" (vaqtincha smartfon ko'rligi) — Zack D. Films uslubida 41.4 s video (994 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, yostiq/yostiq.py (yotoqxona, Megan yonboshlab yotadi), ishqalash/ishqalash.py
# (rentgen bosh, ko'z kesimi), yelim/eye.py (makro ko'z, qorachiq "PUPIL"), burish/parts.py (naychalar, miya), lib.py (yordamchilar).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_telefon.sh
# Render: OUT=/tmp/claude-0/frames_t/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/telefon/telefon.py --render
# Sinov:  FRAMES=20,60,100,300 PCT=30 OUT=/tmp/claude-0/test/ ... --render   |   Bo'lak: RANGE=a,b
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ZT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ZT)
from lib import *                     # sahnani tozalaydi; bpy, math, random, Vector, mc, sc, R, PH, BK, yordamchilar
import bmesh
from mathutils import Quaternion
for d in ("burish", "yelim", "qovoq"): sys.path.insert(0, os.path.join(ZT, d))
import parts as PT
import eye as EY
import twitch as TW
PT.VIEWPORT_OFF = True
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_t/")
random.seed(7)
END = 994
sc.frame_start, sc.frame_end = 1, END
def V(*a): return Vector(a)
def ckey(idb, path=None): interp(idb, "CONSTANT", path)

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md, words.json) ----------------
SHOTS = [(1, "hook"), (37, "wide"), (75, "face"), (127, "ots"), (192, "xoff"), (248, "pupil"), (335, "maxpup"),
         (383, "beam"), (464, "cut"), (522, "retina"), (620, "xcalm"), (694, "xburn"), (747, "clash"), (801, "off"),
         (883, "pov"), (947, "end")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "wide", "face", "ots", "beam", "off", "pov", "end")
XRN = ("xoff", "xcalm", "xburn", "clash")
MACN = ("pupil", "maxpup")
ROOM = rng(*ROOMN); XR = rng(*XRN); MACR = rng(*MACN); CUTR = rng("cut"); RETR = rng("retina")
F_LAMP = 14         # "o'chirib" (0.54 s) — tungi lampa o'chadi
F_DARK = 231        # "o'chirib qo'yadi" (9.58 s) — ekran ko'zi so'nadi (rentgen)
F_MAXP = 335        # "maksimal" — qorachiq birdan kengayadi
F_LASER = 567       # "xuddi lazer" — lazer nuri tushadi
F_HIT = 605         # "zarba beradi"
F_CLASH = 766       # "signal chalkashuvi"
F_OFF = 818         # "o'chirgan" — telefon ekrani o'chadi
F_15 = 898          # "15 daqiqa"

# ======================================================================
# 1) YOTOQXONA (tun): karavot, tumbochka, tungi lampa, deraza (shahar), devor soati (yostiq.py dan)
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
# devor soati (chap devorda, karavot ustida): "15 daqiqa" da minut strelkasi aylanadi
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
# yostiq (toza paxta jild) va ko'rpa
pillow_m = mat("pillow", (0.86, 0.88, 0.92), 0.8, sss=0.08)
_pb = pillow_m.node_tree.nodes["Principled BSDF"]; _pb.inputs["Sheen Weight"].default_value = 0.5
_N = pillow_m.node_tree.nodes; _L = pillow_m.node_tree.links; _tc = _N.new("ShaderNodeTexCoord")
_wv = _N.new("ShaderNodeTexWave"); _wv.inputs["Scale"].default_value = 160.0; _L.new(_tc.outputs["Object"], _wv.inputs["Vector"])
_bp = _N.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.12; _L.new(_wv.outputs["Fac"], _bp.inputs["Height"]); _L.new(_bp.outputs[0], _pb.inputs["Normal"])
blanket_m = mat("blanket", (0.32, 0.4, 0.62), 0.85, sss=0.05)
nb = blanket_m.node_tree.nodes; lb = blanket_m.node_tree.links
_wv2 = nb.new("ShaderNodeTexWave"); _wv2.inputs["Scale"].default_value = 60.0; _bp2 = nb.new("ShaderNodeBump"); _bp2.inputs["Strength"].default_value = 0.15
lb.new(_wv2.outputs["Fac"], _bp2.inputs["Height"]); lb.new(_bp2.outputs[0], nb["Principled BSDF"].inputs["Normal"])

# ======================================================================
# 2) MEGAN: karavotda yonboshlab yotadi (Laying_Sleeping), pastki ko'z yostiqqa botgan; o'ng qo'lda telefon (IK)
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
SLEEP = Vector((BED.x, BED.y + HEAD_SIGN * 0.12, MTOP - 0.95))
place(mroot, 1, tuple(SLEEP), 0 if HEAD_SIGN > 0 else 180)
SLP = A_("Laying_Sleeping.fbx", inplace=False)
strip2(meg, SLP, 1, speed=0.6, repeat=span(SLP, END + 4) * 0.6)     # sekin nafas (uyquda emas, telefonga qarab yotibdi)
BODY = next(o for o in mmeshes if "body" in o.name.lower())
headE = child_of_bone("meg_head", meg, "Head")
def wp(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
def hmat(f):
    sc.frame_set(f); bpy.context.view_layer.update(); return headE.matrix_world.normalized()
H1 = hmat(60)
HXL = (H1.to_3x3() @ V(1, 0, 0)).normalized()      # Megan'ning chapi
HUP = (H1.to_3x3() @ V(0, 1, 0)).normalized()      # boshning tepasi
FDIR = (H1.to_3x3() @ V(0, 0, 1)).normalized()     # yuz tomoni
EYE_L = H1 @ V(*TW.EYE_H)                          # chap ko'z (Head fazosi X = chap)
EYE_R = H1 @ V(-TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2])
LOW_EYE, UP_EYE = (EYE_L, EYE_R) if EYE_L.z < EYE_R.z else (EYE_R, EYE_L)
LOW_SX = 1 if EYE_L.z < EYE_R.z else -1           # Head fazosida pastki (yostiqdagi) ko'z X belgisi
print("HEAD axes X", tuple(round(x, 2) for x in HXL), "Y", tuple(round(x, 2) for x in HUP), "Z", tuple(round(x, 2) for x in FDIR))
print("EYES low", tuple(round(x, 3) for x in LOW_EYE), "up", tuple(round(x, 3) for x in UP_EYE), "LOW_SX", LOW_SX)
for bn in ("RightHand", "LeftHand", "RightForeArm", "LeftForeArm", "Head", "Hips"):
    pb = meg.pose.bones["mixamorig:" + bn]; print("BONE", bn, tuple(round(x, 3) for x in meg.matrix_world @ pb.head))

HEADW = wp(headE, 60)
EYEM = (LOW_EYE + UP_EYE) / 2
# yostiq: pastki ko'z yostiqqa botadi (yostiq usti pastki ko'zdan ~1 sm baland, yuqori ko'z ochiq qoladi)
PIL_TOP = LOW_EYE.z + 0.012
PH_ = max(0.1, PIL_TOP - MTOP + 0.01)
pil = R_(box("pillow", (0.66, 0.42, PH_), (BED.x, HEADW.y + 0.03 * HEAD_SIGN, MTOP + PH_ / 2 - 0.01), pillow_m, bevel=0.05))
pil.modifiers.new("sub", "SUBSURF").levels = 2
print("PILLOW top", round(PIL_TOP, 3), "h", round(PH_, 3), "MTOP", round(MTOP, 3))
sc.frame_set(60); bpy.context.view_layer.update()
BPTS = []
for bn in ("Hips", "Spine", "Spine1", "Spine2", "LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg", "LeftFoot", "RightFoot"):
    pb = meg.pose.bones["mixamorig:" + bn]
    for t_ in (0.0, 0.5):
        BPTS.append(meg.matrix_world @ pb.head.lerp(pb.tail, t_))
SPY = (meg.matrix_world @ meg.pose.bones["mixamorig:Spine2"].head).y
def blanket_mesh():
    n_x, n_y = 70, 80; bm = bmesh.new(); vs = []
    y0 = BED.y - 1.05 * HEAD_SIGN; y1 = SPY + 0.02 * HEAD_SIGN
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

# ---- telefon: yuzdan ~27 sm oldinda, ekrani yuqori ko'zga qaragan; ekranda lenta suriladi ----
PW, PHh, PT_ = 0.072, 0.152, 0.008
phone = empty("phone", (0, 0, 0))
def phone_frame(f):
    """telefon markazi va yo'nalishi (dunyo): ekran normali yuqori ko'zga, uzun o'qi bosh tepasiga"""
    Hm = hmat(f); up_e = Hm @ V(-LOW_SX * TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2]); mid = Hm @ V(0, TW.EYE_H[1], TW.EYE_H[2])
    fd = (Hm.to_3x3() @ V(0, 0, 1)).normalized(); hu = (Hm.to_3x3() @ V(0, 1, 0)).normalized()
    sway = 0.004 * math.sin(f * 0.11) + 0.002 * math.sin(f * 0.37)
    c = mid + fd * 0.27 - hu * 0.05 + (Hm.to_3x3() @ V(1, 0, 0)).normalized() * (-LOW_SX * 0.01 + sway)
    n_ = (up_e - c).normalized()                                   # ekran normali -> ko'z
    yy = (hu - n_ * hu.dot(n_)).normalized(); xx = yy.cross(n_)
    return c, Matrix((xx, yy, n_)).transposed()
for f in range(1, END + 2, 2):
    c, M3 = phone_frame(f)
    phone.location = c; phone.rotation_euler = M3.to_euler(); phone.keyframe_insert("location", frame=f); phone.keyframe_insert("rotation_euler", frame=f)
interp(phone, "LINEAR")
# korpus (yumaloq burchakli), ramka, kamera bloki
ph_body_m = mat("phone_body", (0.02, 0.022, 0.026), 0.25, metal=0.6, coat=0.6)
prof = rrect(PW, PHh, 0.0, n=48, p=0.18)
def slab(name, prof, z0, z1, m, parent):
    k = len(prof); vs = [(x, y, z0) for x, y in prof] + [(x, y, z1) for x, y in prof]
    fs = [tuple(range(k))[::-1], tuple(range(k, 2 * k))] + [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
    return mesh_obj(name, vs, fs, m, parent)
pb_ = slab("phone_body", prof, -PT_, 0.0, ph_body_m, phone)
pb_.modifiers.new("bev", "BEVEL").width = 0.0015
scr_m = bpy.data.materials.new("phone_screen"); scr_m.use_nodes = True
N = scr_m.node_tree.nodes; L = scr_m.node_tree.links; N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs[0])
scroll = value_node(scr_m, "scroll", 0.0); on_ = value_node(scr_m, "on", 1.0)
cxyz = N.new("ShaderNodeCombineXYZ"); L.new(scroll, cxyz.inputs[1]); L.new(cxyz.outputs[0], mp.inputs["Location"])
br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 9.0; br.offset = 0.0; br.squash = 1.0
br.inputs["Brick Width"].default_value = 0.5; br.inputs["Row Height"].default_value = 0.36; br.inputs["Mortar Size"].default_value = 0.012
br.inputs["Mortar"].default_value = (0.92, 0.94, 0.97, 1); br.inputs["Mortar Size"].default_value = 0.035
L.new(mp.outputs[0], br.inputs["Vector"])
# "rasm" kartochkalari: rang-barang shovqin; "matn" kartochkalari: oq fon + kulrang qatorlar
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 14.0; nz.inputs["Detail"].default_value = 3.0; L.new(mp.outputs[0], nz.inputs["Vector"])
ramp = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], ramp.inputs[0]); E_ = ramp.color_ramp.elements
E_[0].position, E_[0].color = 0.3, (0.1, 0.35, 1.0, 1); E_[1].position, E_[1].color = 0.7, (1.0, 0.45, 0.35, 1)
_e = E_.new(0.5); _e.color = (0.95, 0.8, 0.3, 1)
wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.inputs["Scale"].default_value = 70.0; L.new(mp.outputs[0], wv.inputs["Vector"])
txt = N.new("ShaderNodeMix"); txt.data_type = "RGBA"; L.new(P.math_n(N, L, "GREATER_THAN", wv.outputs["Fac"], 0.75), txt.inputs["Factor"])
txt.inputs[6].default_value = (0.96, 0.97, 1.0, 1); txt.inputs[7].default_value = (0.55, 0.6, 0.7, 1)
L.new(ramp.outputs[0], br.inputs["Color1"]); L.new(txt.outputs[2], br.inputs["Color2"])
em = N.new("ShaderNodeEmission"); L.new(br.outputs["Color"], em.inputs["Color"])
L.new(P.math_n(N, L, "MULTIPLY", on_, 2.2), em.inputs["Strength"])
gl_ = N.new("ShaderNodeBsdfGlossy"); gl_.inputs["Roughness"].default_value = 0.05; gl_.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1)
ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(gl_.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
scr = slab("phone_screen", rrect(PW - 0.005, PHh - 0.006, 0.0, n=48, p=0.16), 0.0, 0.0006, scr_m, phone)
cam_m = mat("phone_cam", (0.01, 0.01, 0.012), 0.1, coat=1.0)
for k_, (dx, dy) in enumerate(((-0.022, 0.058), (-0.022, 0.044))):
    cyl(f"phone_lens{k_}", 0.0045, 0.002, (dx, dy, -PT_ - 0.0008), cam_m, parent=phone, verts=24)
# lenta surilishi: har ~1.2 s da bir "surish" (tez, keyin to'xtash)
sv = 0.0; f = 1
while f < END:
    val_key(scr_m, "scroll", f, sv); sv += 0.17; val_key(scr_m, "scroll", f + 6, sv); f += 29
val_key(scr_m, "on", 1, 1.0); val_key(scr_m, "on", F_OFF - 1, 1.0); val_key(scr_m, "on", F_OFF, 0.0)
interp(scr_m.node_tree, "LINEAR"); ckey(scr_m.node_tree, 'nodes["on"]')
# o'ng qo'l telefonni orqasidan ushlaydi: IK (bilak -> telefon pastki-orqa qismi), kaft telefonga, barmoqlar yon tomonga
gripT = empty("gripT", (0, 0, 0), phone); GS = 1.0                      # tutish tomoni (sinovda +1 tabiiyroq chiqdi)
gripT.location = (GS * 0.05, -0.075, -0.022)
fingT = empty("fingT", (0, 0, 0), phone); fingT.location = (-GS * 0.05, -0.02, -0.014)
palmT = empty("palmT", (0, 0, 0), phone); palmT.location = (0.0, -0.04, 0.2)
pbF = meg.pose.bones["mixamorig:RightForeArm"]; ik = pbF.constraints.new("IK"); ik.target = gripT; ik.use_tail = True; ik.chain_count = 2
pole = empty("elbow_pole", (0, 0, 0)); pole.parent = phone; pole.location = (-LOW_SX * 0.25, -0.35, -0.3)
ik.pole_target = pole; ik.pole_angle = R(-90)
pbH = meg.pose.bones["mixamorig:RightHand"]
dt = pbH.constraints.new("DAMPED_TRACK"); dt.target = fingT; dt.track_axis = "TRACK_Y"
lt = pbH.constraints.new("LOCKED_TRACK"); lt.target = palmT; lt.track_axis = "TRACK_Z"; lt.lock_axis = "LOCK_Y"
for fn in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
    for j in (1, 2, 3):
        b_ = meg.pose.bones.get(f"mixamorig:RightHand{fn}{j}")
        if not b_: continue
        c_ = b_.constraints.new("TRANSFORM"); c_.map_from = "ROTATION"; c_.map_to = "ROTATION"
        c_.owner_space = c_.target_space = "LOCAL"; c_.target = meg; c_.subtarget = "mixamorig:Hips"
        c_.from_min_x_rot = c_.from_max_x_rot = 0.0
        c_.to_min_x_rot = c_.to_max_x_rot = R(48 if fn != "Thumb" else 10)
sc.frame_set(60); bpy.context.view_layer.update()
print("RHAND after IK", tuple(round(x, 3) for x in meg.matrix_world @ meg.pose.bones["mixamorig:RightHand"].head),
      "PHONE", tuple(round(x, 3) for x in phone.matrix_world.translation))

# visibility of Megan / phone (POV: kamera ko'z oldida -> Megan va telefon yashiriladi)
for o in mmeshes: vis(o, rng("hook", "wide", "face", "ots", "beam", "off", "end"), recursive=False)
vis(phone, rng("hook", "wide", "face", "ots", "beam", "off", "end") + XR)

# ---------------- umumiy materiallar (ishqalash.py / qovoq.py dan) ----------------
def xr_mat(name, col=(0.35, 0.75, 1.0), glow=1.2):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", glow)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.015), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.6), 0.04, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
def bone_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.2)
    gl = value_node(m, "glow", 1.4)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.82, 0.92, 1.0, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.06), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.7), 0.1, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
def brain_mat2(name, glow=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15; b.inputs["Roughness"].default_value = 0.4
    gl = value_node(m, "glow", glow); red = value_node(m, "red", 0.0)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs[6].default_value = (0.78, 0.42, 0.45, 1); base.inputs[7].default_value = (0.92, 0.6, 0.6, 1)
    L.new(nz.outputs["Fac"], base.inputs["Factor"]); L.new(base.outputs[2], b.inputs["Base Color"])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.inputs[6].default_value = (1.0, 0.55, 0.65, 1); c2.inputs[7].default_value = (1.0, 0.04, 0.02, 1)
    L.new(red, c2.inputs["Factor"]); L.new(c2.outputs[2], b.inputs["Emission Color"])
    fl = P.math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", fl, 0.15), gl), b.inputs["Emission Strength"])
    return m
def train_mat(name, col=(0.25, 0.55, 1.0), pcol=(0.6, 0.85, 1.0)):
    """egri bo'ylab impulslar poyezdi: 'count' ta impuls, 'phase' oshgan sari oldinga yuradi, 'amp' yorqinlik"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.35
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    cnt = value_node(m, "count", 1.0); ph = value_node(m, "phase", -1.0); amp = value_node(m, "amp", 0.0); gl = value_node(m, "glow", 0.4)
    x = P.math_n(N, L, "FRACT", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", ua.outputs["Fac"], cnt), ph))
    d = P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", x, 0.5))
    p = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", d, 0.12), clamp=True), 2.0)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", p, amp), gl), b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (*pcol, 1)
    return m
def shell_mat(name, g=1.5, hot=0.0):
    """ko'z atrofidagi nur qobig'i: Transparent + Emission (Add), 'g' kuch, 'hot' 0 = sovuq ko'k, 1 = kuygan to'q sariq"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    gv = value_node(m, "g", g); hv = value_node(m, "hot", hot)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    rim = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"], clamp=True), 1.5)
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; L.new(hv, c.inputs["Factor"])
    c.inputs[6].default_value = (0.25, 0.6, 1.0, 1); c.inputs[7].default_value = (1.0, 0.32, 0.04, 1)
    em = N.new("ShaderNodeEmission"); L.new(c.outputs[2], em.inputs["Color"])
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", rim, 0.8), 0.2), gv), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
    return m
def nkeys(m, pairs, mode="LINEAR"):
    for name, f, v in pairs: val_key(m, name, f, v)
    interp(m.node_tree, mode)
def frames_vis(o, frames):
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    fs = sorted(set(frames)); prev = None
    for f in fs:
        if prev is None or f != prev + 1:
            o.hide_render = False; o.keyframe_insert("hide_render", frame=f)
        if f + 1 not in fs:
            o.hide_render = True; o.keyframe_insert("hide_render", frame=f + 1)
        prev = f
    ckey(o, "hide_render")

# ======================================================================
# 3) RENTGEN: shaffof Megan, bosh suyagi, ikki ko'z olmasi (nur qobig'i bilan), ko'rish nervlari, xiazma, miya, yostiq sharpasi
# ======================================================================
xbody = xr_mat("xr_body")
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name or "Sneakers" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
xpil = pil.copy(); xpil.name = "pillow_xray"; sc.collection.objects.link(xpil); xpil.animation_data_clear()
xpil.data = pil.data.copy(); xpil.data.materials.clear(); xpil.data.materials.append(xr_mat("xr_pillow", (0.5, 0.55, 0.9), 0.12))
vis(xpil, XR)
skullE = empty("skullE", (0, -0.012, 0.034), headE); skullE.rotation_euler = (R(-90), 0, 0); skullE.scale = (0.8,) * 3
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=BK + "49c13194_u.glb")
skm = bone_mat("xr_bone")
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.type == "MESH" and o.name.startswith("Text"): bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.parent is None: o.parent = skullE
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(skm)
vis(skullE, XR)
EYES = {}          # "low" (yostiqdagi, qorong'ilikka moslashgan) / "up" (ekranga qaragan)
for tag, sx_ in (("low", LOW_SX), ("up", -LOW_SX)):
    c = empty(f"xeye_{tag}", (sx_ * TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2] - 0.0125), headE)
    b_, red_ = EY.build_eyeball(f"xeyeball_{tag}", 0.0122, "human", c); b_.rotation_euler = (R(-90), 0, 0)
    bm_ = b_.data.materials[0]; bb = bm_.node_tree.nodes["Principled BSDF"]
    bb.inputs["Emission Color"].default_value = (1, 1, 1, 1); bb.inputs["Emission Strength"].default_value = 0.6
    sh = sphere(f"xshell_{tag}", 0.0165, (0, 0, 0), shell_mat(f"shell_{tag}"), sub=4, parent=c)
    EYES[tag] = dict(c=c, ball=b_, m=bm_, shell=sh, sm=sh.data.materials[0])
    vis(c, XR)
def eye_emit(tag, f, v):
    s_ = EYES[tag]["m"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]; s_.default_value = v; s_.keyframe_insert("default_value", frame=f)
def eye_pupil(tag, f, v): val_key(EYES[tag]["m"], "PUPIL", f, v)
XO0, XO1 = S["xoff"]; XC0, XC1 = S["xcalm"]; XB0, XB1 = S["xburn"]; CL0, CL1 = S["clash"]
for tag in ("low", "up"):
    sm = EYES[tag]["sm"]
    val_key(sm, "g", 1, 1.6); val_key(sm, "hot", 1, 0.0); eye_emit(tag, 1, 0.6); eye_pupil(tag, 1, 0.3)
# "o'chirib qo'yadi": ekran ko'zi so'nadi
val_key(EYES["up"]["sm"], "g", F_DARK - 1, 1.6); val_key(EYES["up"]["sm"], "g", F_DARK + 3, 0.0); eye_emit("up", F_DARK - 1, 0.6); eye_emit("up", F_DARK + 3, 0.0)
# moslashgan ko'z (xcalm): keng qorachiq, tinch ko'k nur; ekran ko'zi kuygan (xburn): to'q sariq miltillash
for tag in ("low", "up"):
    eye_pupil(tag, XC0, 0.44); eye_emit(tag, XC0, 0.5)
val_key(EYES["low"]["sm"], "g", XC0, 2.6); val_key(EYES["up"]["sm"], "g", XC0, 0.9); val_key(EYES["up"]["sm"], "hot", XC0, 1.0)
for f in range(XC0, XC1, 16):
    val_key(EYES["low"]["sm"], "g", f + 8, 2.0); val_key(EYES["low"]["sm"], "g", f + 16, 2.6)
eye_pupil("up", XB0, 0.2); eye_emit("up", XB0, 0.0); val_key(EYES["up"]["sm"], "hot", XB0, 1.0)
for f in range(XB0, CL1 + 1, 4):
    val_key(EYES["up"]["sm"], "g", f, 6.0); val_key(EYES["up"]["sm"], "g", f + 2, 3.5)
val_key(EYES["low"]["sm"], "g", XB0, 1.6)
for tag in ("low", "up"):
    for fc in mc._fcurves(EYES[tag]["sm"].node_tree.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# ko'rish nervlari (ko'z ortidan xiazma orqali miyaning ensa qismiga) va miya
xb_m = brain_mat2("xbrain_m", 0.6)
xbrain, _ = PT.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, XR)
NERV = {}
for tag, sx_, pc in (("low", LOW_SX, (0.35, 0.7, 1.0)), ("up", -LOW_SX, (1.0, 0.45, 0.1))):
    pts = [(sx_ * 0.033, 0.088, 0.104), (sx_ * 0.026, 0.084, 0.085), (sx_ * 0.008, 0.08, 0.07), (sx_ * 0.012, 0.085, 0.045),
           (sx_ * 0.026, 0.095, 0.01), (sx_ * 0.03, 0.105, -0.03), (sx_ * 0.025, 0.115, -0.06)]
    m = train_mat(f"onerve_{tag}", col=(0.9, 0.78, 0.5), pcol=pc)
    t_ = PT.tube(f"onerve_{tag}", pts, 0.0024, m, headE, taper=[1.0] * len(pts)); NERV[tag] = m
    vis(t_, XR, recursive=False)
for tag, m in NERV.items():
    nkeys(m, [("count", 1, 3.0), ("amp", 1, 0.0), ("glow", 1, 0.8), ("phase", 1, 0.0)])
val_key(NERV["up"], "glow", F_DARK - 1, 0.8); val_key(NERV["up"], "glow", F_DARK + 3, 0.03)
val_key(NERV["up"], "glow", XC0, 0.8)
for tag, m in NERV.items():
    val_key(m, "amp", CL0 - 1, 0.0); val_key(m, "amp", CL0 + 2, 30.0); val_key(m, "phase", CL0 - 1, 0.0); val_key(m, "phase", CL1 + 1, 5.0)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT" if "phase" not in fc.data_path else "LINEAR"
nkeys(xb_m, [("glow", 1, 0.6), ("red", 1, 0.0), ("glow", F_CLASH - 1, 0.6)], "CONSTANT")
for f in range(F_CLASH, CL1 + 1, 4):
    val_key(xb_m, "glow", f, 5.0); val_key(xb_m, "glow", f + 2, 1.2)
val_key(xb_m, "red", F_CLASH - 1, 0.0); val_key(xb_m, "red", F_CLASH, 1.0); ckey(xb_m.node_tree)
# xiazmada to'qnashuv uchqunlari (ko'k + to'q sariq)
spark_ms = [mat("spark_b", (0.3, 0.6, 1.0), 0.5, emit=10.0), mat("spark_o", (1.0, 0.45, 0.1), 0.5, emit=10.0), mat("spark_w", (1, 0.9, 0.8), 0.5, emit=12.0)]
rs_ = random.Random(12); sparks = empty("xsparks", (0, 0.08, 0.068), headE)
for k in range(36):
    d_ = Vector((rs_.uniform(-1, 1), rs_.uniform(-1, 1), rs_.uniform(-1, 1))).normalized() * rs_.uniform(0.002, 0.016)
    o = sphere(f"xspark{k}", rs_.uniform(0.0008, 0.0018), tuple(d_), rs_.choice(spark_ms), sub=1, parent=sparks)
    on = []; f = F_CLASH + rs_.randint(-2, 3)
    while f < CL1:
        on += list(range(f, f + rs_.randint(2, 3))); f += rs_.randint(3, 7)
    frames_vis(o, on)

# ======================================================================
# 4) MAKRO KO'Z (real o'lcham): qorong'uda qorachiq kengayadi
# ======================================================================
MAC = V(0.0, 30.0, 1.2)
meye = EY.build_eye("meye", tuple(MAC))
meroot = meye["root"]; mball_m = meye["ball"].data.materials[0]
mskin = mat("macro_skin", (0.5, 0.3, 0.23), 0.5, sss=0.3, sss_scale=0.002)
mback = plane("macro_back", (0.5, 0.5), tuple(MAC + V(0, 0.006, 0)), mskin, rot=(90, 0, 0))
PU0, PU1 = S["pupil"]; MP0, MP1 = S["maxpup"]
val_key(mball_m, "PUPIL", 1, 0.17); val_key(mball_m, "PUPIL", PU0, 0.17); val_key(mball_m, "PUPIL", PU1, 0.3)
val_key(mball_m, "PUPIL", F_MAXP + 1, 0.47); val_key(mball_m, "PUPIL", F_MAXP + 4, 0.44); val_key(mball_m, "PUPIL", MP1 + 1, 0.45)
interp(mball_m.node_tree, "LINEAR")
for f, v in ((1, 0.0), (PU0 + 40, 0.0), (PU0 + 43, 1.0), (PU0 + 46, 0.0)):
    EY.set_key(meye, "blink", f, v)
vis(meroot, MACR); vis(mback, MACR)

# ======================================================================
# 5) KESIM (10x): ko'k nur keng qorachiqdan, gavhardan o'tib, ko'z tubida nuqtaga yig'iladi
#    mahalliy o'qlar (cutE): old = -Y, tepa = +Z, kesim tekisligi x = 0 (kamera +X tomonda)
# ======================================================================
CUT = V(40.0, 0.0, 1.5); Re = 0.12
cutE = empty("cutE", tuple(CUT))
def C_(o):
    if o.parent is None: o.parent = cutE
    return o
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=96, radius=Re, rotation=(R(90), 0, 0), location=(0, 0, 0))
ball = bpy.context.object; ball.name = "cut_ball"; bpy.ops.object.transform_apply(rotation=True)
bm = bmesh.new(); bm.from_mesh(ball.data)
dl = [v for v in bm.verts if v.co.x > 0.0005 or (v.co.normalized().y < 0 and math.hypot(v.co.normalized().x, v.co.normalized().z) < 0.47)]
bmesh.ops.delete(bm, geom=dl, context="VERTS"); bm.to_mesh(ball.data); bm.free()
for p_ in ball.data.polygons: p_.use_smooth = True
so = ball.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.011; so.offset = -1.0
sclera_m = mat("cut_sclera", (0.93, 0.9, 0.86), 0.3, coat=0.5, sss=0.2, sss_scale=0.004)
ball.data.materials.append(sclera_m); C_(ball)
def r_dome(s): return Re * (1 + 0.06 * math.cos(min(1.0, s / 0.5) * math.pi / 2) ** 2) if s < 0.5 else Re
bpy.ops.mesh.primitive_uv_sphere_add(segments=160, ring_count=120, radius=Re, rotation=(R(90), 0, 0), location=(0, 0, 0))
corn = bpy.context.object; corn.name = "cut_cornea"; bpy.ops.object.transform_apply(rotation=True)
bm = bmesh.new(); bm.from_mesh(corn.data)
dl = [v for v in bm.verts if v.co.x > 0.0005 or not (v.co.normalized().y < 0 and math.hypot(v.co.normalized().x, v.co.normalized().z) < 0.52)]
bmesh.ops.delete(bm, geom=dl, context="VERTS"); bm.to_mesh(corn.data); bm.free()
for v in corn.data.vertices:
    d = v.co.normalized(); v.co = d * r_dome(math.hypot(d.x, d.z))
for p_ in corn.data.polygons: p_.use_smooth = True
corn.modifiers.new("solid", "SOLIDIFY").thickness = 0.008
corn.data.materials.append(mat("cut_cornea_m", (0.75, 0.9, 1.0), 0.05, trans=0.4, coat=1.0, ior=1.376, emit=0.3, emit_col=(0.3, 0.75, 1.0))); C_(corn)
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=Re - 0.0005, fill_type="NGON", location=(-0.0004, 0, 0), rotation=(0, R(90), 0))
disc = bpy.context.object; disc.name = "cut_disc"
disc_m = bpy.data.materials.new("cut_disc"); disc_m.use_nodes = True
N = disc_m.node_tree.nodes; L = disc_m.node_tree.links; _b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
rr_ = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sx.outputs["X"], sx.outputs["X"]),
      P.math_n(N, L, "MULTIPLY", sx.outputs["Y"], sx.outputs["Y"]))), Re)
ramp = N.new("ShaderNodeValToRGB"); L.new(rr_, ramp.inputs[0]); E = ramp.color_ramp.elements; ramp.color_ramp.interpolation = "EASE"
E[0].position, E[0].color = 0.0, (0.42, 0.5, 0.62, 1); E[1].position, E[1].color = 0.78, (0.55, 0.6, 0.68, 1)
for pos, col in ((0.81, (0.85, 0.42, 0.3, 1)), (0.85, (0.28, 0.04, 0.03, 1)), (0.9, (0.3, 0.05, 0.04, 1)), (0.915, (0.92, 0.9, 0.86, 1))):
    e = E.new(pos); e.color = col
L.new(ramp.outputs[0], _b.inputs["Base Color"]); _b.inputs["Roughness"].default_value = 0.45; _b.inputs["Coat Weight"].default_value = 0.4
disc.data.materials.append(disc_m); C_(disc)
lens_m = mat("cut_lens", (0.95, 0.85, 0.55), 0.08, coat=1.0, sss=0.2)
C_(sphere("cut_lens", 0.05, (-0.002, -0.072, 0), lens_m, scale=(0.12, 0.42, 0.95), sub=4))
iris_m = mat("cut_iris", (0.15, 0.3, 0.38), 0.4)
for sgn in (1, -1): C_(box(f"cut_iris{sgn}", (0.006, 0.006, 0.018), (-0.002, -0.094, sgn * 0.086), iris_m, bevel=0.002))    # keng qorachiq
cn_m = train_mat("cut_nerve_m", col=(0.92, 0.8, 0.55), pcol=(0.5, 0.8, 1.0))
C_(PT.tube("cut_nerve", [(0.0, Re * 0.9, -0.012), (0.0, Re + 0.05, -0.02), (0.0, Re + 0.16, -0.015), (0.0, Re + 0.4, 0.02)], 0.019, cn_m, cutE,
           taper=[1.0, 1.0, 1.0, 1.0]))
CU0, CU1 = S["cut"]
nkeys(cn_m, [("count", 1, 3.0), ("amp", 1, 0.0), ("glow", 1, 0.3), ("phase", 1, 0.0), ("amp", CU0 + 30, 0.0), ("amp", CU0 + 34, 22.0), ("phase", CU0 + 30, 0.0), ("phase", CU1 + 1, -3.0)])
# nur: oldindan (y = -0.5) qorachiqdan gavhargacha keng dasta, gavhardan to'r pardagacha konus (fokus nuqtasi)
FOC = V(0, Re * 0.86, 0.0)
def beam_mesh(name, rings, n=24):
    vs = []; fs = []
    for (y, r) in rings:
        for i in range(n):
            a = 2 * math.pi * i / n; vs.append((0.0 + r * math.cos(a) * 0.35, y, r * math.sin(a)))
    for j in range(len(rings) - 1):
        for i in range(n):
            fs.append((j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i))
    return mesh_obj(name, vs, fs)
def beam_mat(name, col=(0.35, 0.65, 1.0)):
    """ko'k nur: Transparent + Emission; 'a' kuch, 'reach' — nur uchi (mahalliy y), 't' — oqim chiziqlari"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    a = value_node(m, "a", 0.0); reach = value_node(m, "reach", 10.0); t = value_node(m, "t", 0.0); ax = value_node(m, "ax", 1.0)
    tc = N.new("ShaderNodeTexCoord"); sx_ = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx_.inputs[0])
    along = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sx_.outputs["Y"], ax), P.math_n(N, L, "MULTIPLY", sx_.outputs["Z"], P.math_n(N, L, "SUBTRACT", 1.0, ax)))
    cut_ = P.math_n(N, L, "LESS_THAN", along, reach)
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Y"; wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 2.0
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs[0]); cx = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "MULTIPLY", t, -1.0), cx.inputs[1]); L.new(cx.outputs[0], mp.inputs["Location"])
    L.new(mp.outputs[0], wv.inputs["Vector"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    core = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.5)
    st = P.math_n(N, L, "ADD", 0.45, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", wv.outputs["Fac"], 4.0), 1.6))
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", st, core), a), cut_), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
    return m
cbeam_m = beam_mat("cut_beam_m")
rings = [(-0.55, 0.05), (-0.14, 0.05), (-0.09, 0.048), (-0.072, 0.045)] + [(-0.072 + (FOC.y + 0.072) * k / 10, 0.045 * (1 - k / 10) + 0.003) for k in range(1, 11)]
cbeam = C_(beam_mesh("cut_beam", rings)); cbeam.data.materials.append(cbeam_m); cbeam.location.x = 0.004
nkeys(cbeam_m, [("a", 1, 0.0), ("a", CU0, 2.5), ("reach", 1, -0.55), ("reach", CU0, -0.55), ("reach", CU0 + 26, FOC.y + 0.01), ("t", CU0, 0.0), ("t", CU1 + 1, 3.0)])
hit_m = mat("cut_hit", (0.6, 0.85, 1.0), 0.5, emit=0.0)
hit = C_(sphere("cut_hit", 0.012, tuple(FOC + V(0.004, -0.004, 0)), hit_m, sub=3))
_hs = hit_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.0), (CU0 + 25, 0.0), (CU0 + 28, 40.0), (CU0 + 34, 14.0), (CU1, 20.0)):
    _hs.default_value = v; _hs.keyframe_insert("default_value", frame=f)
vis(cutE, CUTR)

# ======================================================================
# 6) MIKRO TO'R PARDA: tayoqcha va kolbochkalar "o'rmoni"; ko'k lazer tushib, zarba to'lqini tarqaladi
# ======================================================================
RET = V(80.0, 0.0, 0.0)
def ret_mat(name, col, tip_col):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.35; b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 0.5
    tc = N.new("ShaderNodeTexCoord"); sx_ = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx_.inputs[0])
    hz = P.math_n(N, L, "MULTIPLY", sx_.outputs["Z"], 0.8, clamp=True)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(hz, cm.inputs["Factor"]); cm.inputs[6].default_value = (*col, 1); cm.inputs[7].default_value = (*tip_col, 1)
    L.new(cm.outputs[2], b.inputs["Base Color"])
    wave = value_node(m, "wave", -1.0); amp = value_node(m, "amp", 0.0); hot = value_node(m, "hot", 0.0); calm = value_node(m, "calm", 0.15)
    dist = P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sx_.outputs["X"], sx_.outputs["X"]), P.math_n(N, L, "MULTIPLY", sx_.outputs["Y"], sx_.outputs["Y"])))
    ring = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", dist, wave)), 0.35), clamp=True)
    core = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", dist, P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", hot, 0.9), 0.01)), clamp=True), hot)
    e_ = P.math_n(N, L, "ADD", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", ring, amp), P.math_n(N, L, "MULTIPLY", core, 4.0)), P.math_n(N, L, "MULTIPLY", hz, calm))
    L.new(e_, b.inputs["Emission Strength"])
    ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", core, 2.0, clamp=True), ec.inputs["Factor"])
    ec.inputs[6].default_value = (0.45, 0.7, 1.0, 1); ec.inputs[7].default_value = (1.0, 0.55, 0.2, 1); L.new(ec.outputs[2], b.inputs["Emission Color"])
    return m
rod_m = ret_mat("rod_m", (0.32, 0.2, 0.42), (0.75, 0.5, 0.85)); cone_m = ret_mat("cone_m", (0.5, 0.32, 0.12), (1.0, 0.78, 0.35))
def receptors():
    rr = random.Random(31); bm_r = bmesh.new(); bm_c = bmesh.new()
    def column(bm_, x, y, r, h, tip, n=8):
        lo = [bm_.verts.new((x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n), 0.0)) for i in range(n)]
        hi = [bm_.verts.new((x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n), h)) for i in range(n)]
        top = bm_.verts.new((x, y, h + tip))
        for i in range(n):
            j = (i + 1) % n; bm_.faces.new((lo[i], lo[j], hi[j], hi[i])); bm_.faces.new((hi[i], hi[j], top))
    sp = 0.15; k = 0
    for ix in range(-26, 27):
        for iy in range(-26, 27):
            x = ix * sp + rr.uniform(-0.04, 0.04) + (sp / 2 if iy % 2 else 0); y = iy * sp * 0.87 + rr.uniform(-0.04, 0.04)
            if x * x + y * y > 3.6 ** 2: continue
            if rr.random() < 0.18: column(bm_c, x, y, 0.06, rr.uniform(0.55, 0.7), 0.22)
            else: column(bm_r, x, y, 0.035, rr.uniform(0.95, 1.2), 0.04); k += 1
    out = []
    for nm, bm_, m in (("rods", bm_r, rod_m), ("cones", bm_c, cone_m)):
        me = bpy.data.meshes.new(nm); bm_.to_mesh(me); bm_.free()
        o = bpy.data.objects.new(nm, me); sc.collection.objects.link(o); o.location = RET; me.materials.append(m); smooth(o); out.append(o)
    print("receptors", k)
    return out
recs = receptors()
rpe = plane("rpe", (9, 9), tuple(RET), mat("rpe_m", (0.12, 0.03, 0.03), 0.6, sss=0.2))
RE0, RE1 = S["retina"]
for m in (rod_m, cone_m):
    nkeys(m, [("wave", 1, -1.0), ("amp", 1, 0.0), ("hot", 1, 0.0), ("calm", 1, 0.25),
              ("hot", F_LASER + 2, 0.0), ("hot", F_LASER + 6, 0.25), ("hot", F_HIT - 1, 0.35), ("hot", F_HIT + 3, 1.0), ("hot", RE1, 1.2),
              ("wave", F_HIT, 0.0), ("wave", F_HIT + 16, 4.0), ("amp", F_HIT - 1, 0.0), ("amp", F_HIT, 9.0), ("amp", F_HIT + 16, 2.0)])
laser_m = beam_mat("laser_m", (0.4, 0.7, 1.0))
laser = beam_mesh("laser", [(-0.2, 0.22), (7.0, 0.22)], n=32); laser.rotation_euler = (R(-90), 0, 0); laser.location = RET
laser.data.materials.append(laser_m)
val_key(laser_m, "ax", 1, 1.0)
nkeys(laser_m, [("a", 1, 0.0), ("a", F_LASER, 0.0), ("a", F_LASER + 2, 3.0), ("a", F_HIT, 4.5), ("a", F_HIT + 4, 7.0), ("a", RE1, 5.0),
                ("reach", 1, 7.0), ("t", RE0, 0.0), ("t", RE1 + 1, 12.0)])
# lazer yuqoridan tushadi: 'reach' o'rniga ob'ektni yuqoridan pastga cho'zamiz (scale z mahalliy y bo'ylab)
laser.scale = (1, 0.01, 1); laser.location = RET + V(0, 0, 6.8); laser.keyframe_insert("scale", frame=F_LASER); laser.keyframe_insert("location", frame=F_LASER)
laser.scale = (1, 1, 1); laser.location = RET; laser.keyframe_insert("scale", frame=F_LASER + 5); laser.keyframe_insert("location", frame=F_LASER + 5)
for o in recs + [rpe, laser]: vis(o, RETR)

# ======================================================================
# 7) XONADAGI KO'K NUR: ekrandan yuqori ko'zga konus (faqat "beam" kadri), ichida oqim "fotonlari"
# ======================================================================
BM0, BM1 = S["beam"]
sc.frame_set((BM0 + BM1) // 2); bpy.context.view_layer.update()
EYE_LOC = phone.matrix_world.inverted() @ (headE.matrix_world.normalized() @ V(-LOW_SX * TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2] + 0.004))
def pyr(name, w0, h0, w1, p1, n=12):
    vs = []; fs = []
    for j in range(n + 1):
        t = j / n; c = Vector((0, 0, 0.001)).lerp(p1, t); ww = w0 + (w1 - w0) * t; hh = h0 + (w1 - h0) * t
        for (sx_, sy_) in ((-1, -1), (1, -1), (1, 1), (-1, 1)): vs.append((c.x + sx_ * ww / 2, c.y + sy_ * hh / 2, c.z))
    for j in range(n):
        for i in range(4): fs.append((j * 4 + i, j * 4 + (i + 1) % 4, (j + 1) * 4 + (i + 1) % 4, (j + 1) * 4 + i))
    return mesh_obj(name, vs, fs)
rbeam_m = beam_mat("room_beam_m", (0.2, 0.45, 1.0))
rbeam = pyr("room_beam", PW * 0.9, PHh * 0.9, 0.007, EYE_LOC); rbeam.parent = phone; rbeam.data.materials.append(rbeam_m)
nkeys(rbeam_m, [("ax", 1, 0.0), ("a", 1, 0.0), ("a", BM0, 0.0), ("a", BM0 + 8, 0.55), ("a", BM1, 0.7), ("reach", 1, 0.0), ("reach", BM0, 0.0),
                ("reach", BM0 + 14, EYE_LOC.z + 0.01), ("t", BM0, 0.0), ("t", BM1 + 1, -60.0)])
vis(rbeam, [S["beam"]])
phot_m = mat("photon", (0.6, 0.85, 1.0), 0.5, emit=25.0)
rp = random.Random(9)
for k in range(26):
    o = sphere(f"photon{k}", 0.0012, (0, 0, 0), phot_m, scale=(1, 1, 5), sub=1, parent=phone)
    s0 = Vector((rp.uniform(-0.03, 0.03), rp.uniform(-0.065, 0.065), 0.002)); per = rp.randint(9, 14); ph0 = rp.randint(0, per)
    f = BM0 + 10 - ph0
    while f < BM1 + 2:
        o.location = s0; o.keyframe_insert("location", frame=f)
        o.location = EYE_LOC + Vector((rp.uniform(-0.002, 0.002), rp.uniform(-0.002, 0.002), 0)); o.keyframe_insert("location", frame=f + per - 1)
        f += per
    interp(o, "LINEAR", "location")
    o.rotation_euler = (math.atan2(-(EYE_LOC.y - s0.y), EYE_LOC.z), 0, 0)
    vis(o, [(BM0 + 10, BM1)])

# ======================================================================
# 8) POV: Megan ko'zi bilan — chap yarmi (moslashgan ko'z) xonani ko'radi, o'ng yarmi (ekran ko'zi) zimziyo + "keyingi iz"
# ======================================================================
# devor soati o'ng devorga ko'chiriladi: POV da ko'rinadi, minut strelkasi 15 daqiqa yuradi
_Y = V(0, 0, 1); _Z = V(-1, 0, 0); _X = _Y.cross(_Z)
clk.location = (X1 - 0.02, 2.05, 1.62); clk.rotation_euler = Matrix((_X, _Y, _Z)).transposed().to_euler(); clk.scale = (1.6,) * 3
PV0, PV1 = S["pov"]
for f, mm in ((1, 47), (F_15 - 2, 47), (PV1 - 6, 62), (END, 62.5)):
    hand_m.rotation_euler = (0, 0, R(-mm / 60 * 360)); hand_m.keyframe_insert("rotation_euler", frame=f)
    hand_h.rotation_euler = (0, 0, R(-(11 + mm / 60) / 12 * 360)); hand_h.keyframe_insert("rotation_euler", frame=f)
interp(hand_m, "LINEAR"); interp(hand_h, "LINEAR")

# ======================================================================
# 9) KAMERALAR (bosh fazosida: X chap, Y tepa, Z old — yotgan yuz tik ko'rinadi; xona umumiy planlari dunyo fazosida)
# ======================================================================
H1i = H1.inverted(); WUP_H = (H1i.to_3x3() @ V(0, 0, 1)).normalized()
UPE_H = V(-LOW_SX * TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2]); LOWE_H = V(LOW_SX * TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2])
def look_rot(pos, tgt, up, roll=0.0):
    fw = (Vector(tgt) - Vector(pos)).normalized(); u = (Vector(up) - fw * Vector(up).dot(fw)).normalized()
    if roll: u = Quaternion(fw, R(roll)) @ u
    return Matrix((fw.cross(u), u, -fw)).transposed().to_euler()
def hcam(name, keys, lens, fstop=None, up="head", clip=0.004):
    """keys: [(f, pos_h, tgt_h[, roll])] bosh fazosida; up: 'head' (yuz tik) yoki 'world'"""
    c = shot_cam(name, (0, 0, 0), None, lens, None, clip=clip); c.parent = headE
    ft = empty(name + "_f", (0, 0, 0), headE)
    for k_ in keys:
        f, p_, t_ = k_[:3]; roll = k_[3] if len(k_) > 3 else 0.0
        c.location = p_; c.rotation_euler = look_rot(p_, t_, V(0, 1, 0) if up == "head" else WUP_H, roll)
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        ft.location = t_; ft.keyframe_insert("location", frame=f)
    if fstop: c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop; c.data.dof.focus_object = ft
    return c
def wcam(name, keys, lens, fstop=None, clip=0.005, roll=0.0):
    """keys: [(f, pos, tgt)] dunyo fazosida, TRACK_TO siz (aylanish kalitlanadi)"""
    c = shot_cam(name, (0, 0, 0), None, lens, None, clip=clip); ft = empty(name + "_f")
    for f, p_, t_ in keys:
        c.location = p_; c.rotation_euler = look_rot(p_, t_, V(0, 0, 1), roll)
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        ft.location = t_; ft.keyframe_insert("location", frame=f)
    if fstop: c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop; c.data.dof.focus_object = ft
    return c
HEADC = V(0, 0.1, 0.06)
# 1 ILGAK: tumbochka sathidan, lampa yonidan yuzga tez push-in (lampa 14-kadrda o'chadi)
H0, H1_ = S["hook"]
c = wcam("hook", [(H0, V(-0.48, 2.08, 0.92), EYEM + V(0.05, 0, 0)), (H0 + 14, V(-0.66, 2.08, 0.86), EYEM + V(0.03, 0, 0)), (H1_, EYEM + V(0.42, -0.1, 0.12), EYEM)], 20, 2.8)
lens_keys(c, [(H0, 18), (H0 + 14, 20), (H1_, 30)])
# 2 KENG PLAN: tepa-yondan sekin dolly
W0, W1 = S["wide"]
c = wcam("wide", [(W0, V(0.35, 0.55, 1.95), BED + V(0.05, 0.45, 0.45)), (W1, V(0.1, 0.95, 1.7), BED + V(0.0, 0.55, 0.5))], 24, 5.6)
# 3 YAQIN PLAN: yostiq sathidan, pastki ko'z yostiqqa botgan; 50 mm f/2, yonlama siljish
F0, F1 = S["face"]
c = hcam("face", [(F0, V(0.22, 0.05, 0.62), V(0.005, 0.085, 0.135)), (F1, V(0.17, 0.09, 0.56), V(0.0, 0.088, 0.135))], 50, 2.0)
# 4 TELEFON ORTIDAN: ochiq ko'zga push-in
O0, O1 = S["ots"]
c = hcam("ots", [(O0, V(-0.08, 0.16, 0.66), UPE_H), (O1, V(-0.06, 0.13, 0.44), UPE_H)], 40, 2.8)
# 5 RENTGEN: bosh atrofida aylanma (telefon ustidan)
X0_, X1_ = S["xoff"]
c = hcam("xoff", [(X0_ + int(i * (X1_ - X0_) / 6), V(0.36 * math.sin(R(40 - 70 * i / 6)), 0.26, 0.36 * math.cos(R(40 - 70 * i / 6)) + 0.06), HEADC + V(0, -0.01, 0.03)) for i in range(7)], 32, 5.6)
# 6 MAKRO: qorachiq kengayadi, sekin push-in; 7 crash zoom
c = wcam("pupil", [(PU0, MAC + V(0.004, -0.085, 0.006), MAC), (PU1, MAC + V(0.002, -0.062, 0.003), MAC)], 50, 11.0, clip=0.001)
c = wcam("maxpup", [(MP0, MAC + V(0.0, -0.06, 0.002), MAC), (MP1, MAC + V(0.0, -0.05, 0.0), MAC)], 50, 16.0, clip=0.001)
lens_keys(c, [(MP0, 50), (MP0 + 4, 66), (MP1, 70)]); shake(c, MP0 + 3, MP0 + 16, 0.0015, seed=7)
# 8 PAST BURCHAK: ekran yonidan nur bo'ylab ko'zga uchish (18 mm)
c = hcam("beam", [(BM0, V(-0.13, -0.11, 0.44), V(-0.02, 0.06, 0.25)), (BM0 + 40, V(-0.1, 0.0, 0.3), UPE_H), (BM1, V(-0.045, 0.075, 0.19), UPE_H)], 18, 4.0)
lens_keys(c, [(BM0, 18), (BM1, 24)])
# 9 KESIM: nur bo'ylab yon tomondan ergashish
c = wcam("cut", [(CU0, CUT + V(0.62, -0.5, 0.06), CUT + V(0, -0.32, 0)), (CU0 + 26, CUT + V(0.55, -0.12, 0.05), CUT + V(0, -0.04, 0)), (CU1, CUT + V(0.46, 0.05, 0.04), CUT + V(0, 0.05, 0))], 30, 8.0, clip=0.01)
# 10 TO'R PARDA: o'rmon chetidan past burchak, "zarba"da crash zoom + silkinish
c = wcam("retina", [(RE0, RET + V(3.4, -2.8, 3.0), RET + V(0, 0, 0.6)), (F_HIT - 1, RET + V(2.7, -2.2, 2.5), RET + V(0, 0, 0.7)), (RE1, RET + V(2.3, -1.9, 2.2), RET + V(0, 0, 0.8))], 20, None, clip=0.01)
lens_keys(c, [(RE0, 20), (F_HIT - 1, 21), (F_HIT + 3, 30), (RE1, 32)]); shake(c, F_HIT, F_HIT + 18, 0.12, seed=10)
# 11 moslashgan ko'z (yostiq tomoni), 12 kuygan ko'z (whip), 13 xiazma (crash zoom)
c = hcam("xcalm", [(XC0, V(0.05, 0.24, 0.4), LOWE_H), (XC1, V(0.04, 0.18, 0.32), LOWE_H)], 40, 5.6)
c = hcam("xburn", [(XB0, V(-0.17, 0.13, 0.3), LOWE_H), (XB0 + 4, V(-0.17, 0.12, 0.3), UPE_H), (XB1, V(-0.11, 0.1, 0.25), UPE_H)], 40, 5.6)
c = hcam("clash", [(CL0, V(0.0, 0.42, 0.3), V(0, 0.08, 0.05)), (CL1, V(0.01, 0.4, 0.28), V(0, 0.08, 0.06))], 30, 5.6)
lens_keys(c, [(CL0, 30), (F_CLASH - 1, 32), (F_CLASH + 3, 55), (CL1, 58)])
shake(c, F_CLASH, F_CLASH + 16, 0.006, seed=13)
# 14 telefon o'chadi: yondan ko'zga push-in
OF0, OF1 = S["off"]
c = hcam("off", [(OF0, V(-0.15, -0.02, 0.48), UPE_H), (F_OFF, V(-0.12, 0.02, 0.4), UPE_H), (OF1, V(-0.07, 0.07, 0.25), UPE_H)], 35, 2.8)
# 15 POV: ko'z oldidan soatga qarab
POVP = UP_EYE + FDIR * 0.05
CLKW = Vector(clk.location)
c = wcam("pov", [(PV0, POVP, CLKW + V(0, -0.42, -0.05)), (PV1, POVP + V(0.01, 0.0, 0.01), CLKW + V(0, -0.38, -0.08))], 30, None, clip=0.01, roll=-14.0)
# 16 FINAL: yuzdan orqaga chekinish, yorug'lik so'nadi
EN0, EN1 = S["end"]
c = hcam("end", [(EN0, V(-0.12, 0.1, 0.3), UPE_H), (EN1, V(-0.2, 0.13, 0.52), UPE_H)], 35, 2.8)
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        if fc.data_path in ("location", "rotation_euler") and n in ("xoff",):
            for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
for f_, n in SHOTS:
    sc.timeline_markers.new(n, frame=f_).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ---- chaqnash kartochkalari (kameraga bog'langan): 'a' 0..1 ----
def flash(cam, keys, col=(1, 1, 1), s=4.0):
    m = bpy.data.materials.new("flash_" + cam.name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    a = value_node(m, "a", 0.0); em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = s
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); L.new(a, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs[0])
    pl = plane("flash_" + cam.name, (0.2, 0.3), (0, 0, -0.012), m, parent=cam)
    for f, v in [(1, 0.0)] + keys: val_key(m, "a", f, v)
    interp(m.node_tree, "LINEAR"); pl.visible_shadow = False
    return pl
flash(CAMS["xoff"], [(X0_, 0.9), (X0_ + 3, 0.0), (F_DARK - 1, 0.0), (F_DARK, 0.55), (F_DARK + 4, 0.0)], (1, 1, 1))
_fr = bpy.data.objects["flash_cam_xoff"].data.materials[0]
flash(CAMS["xoff"], [(F_DARK - 1, 0.0), (F_DARK, 0.6), (F_DARK + 5, 0.0)], (1.0, 0.08, 0.04), 3.0)
flash(CAMS["cut"], [(CU0, 0.75), (CU0 + 4, 0.0)], (0.75, 0.9, 1.0))
flash(CAMS["retina"], [(F_HIT - 1, 0.0), (F_HIT, 0.95), (F_HIT + 6, 0.0)], (0.85, 0.95, 1.0))
flash(CAMS["clash"], [(F_CLASH - 1, 0.0), (F_CLASH, 0.45), (F_CLASH + 2, 0.0), (F_CLASH + 9, 0.0), (F_CLASH + 10, 0.3), (F_CLASH + 12, 0.0)], (1.0, 0.1, 0.05), 3.0)
flash(CAMS["xcalm"], [(XC0, 0.6), (XC0 + 3, 0.0)], (0.75, 0.9, 1.0))
flash(CAMS["end"], [(EN1 - 10, 0.0), (EN1 - 4, 1.0)], (0, 0, 0), 0.0)
# ---- POV: o'ng yarmi zimziyo (yumshoq chegara), ichida telefonning "keyingi izi", "15 DAQIQA" yozuvi ----
pc = CAMS["pov"]; D_ = 0.05; HH = D_ * 12 / pc.data.lens; HW = HH * 9 / 16
mk_m = bpy.data.materials.new("pov_mask"); mk_m.use_nodes = True; N = mk_m.node_tree.nodes; L = mk_m.node_tree.links; N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord"); sx_ = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx_.inputs[0])
edge = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ADD", sx_.outputs["X"], HW * 0.08), HW * 0.22, clamp=True)
mk_a = value_node(mk_m, "a", 1.0)
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0, 0, 0, 1); em.inputs["Strength"].default_value = 0.0
tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "MULTIPLY", edge, mk_a), mx.inputs[0])
L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs[0])
mask = mesh_obj("pov_mask", [(-HW * 0.2, -HH * 1.5, 0), (HW * 2, -HH * 1.5, 0), (HW * 2, HH * 1.5, 0), (-HW * 0.2, HH * 1.5, 0)], [(0, 1, 2, 3)], mk_m, pc, (0, 0, -D_))
nkeys(mk_m, [("a", PV0, 0.0), ("a", PV0 + 5, 1.0)])
ai_m = mat("afterimage", (0.0, 0.0, 0.0), 0.5, emit=0.0, emit_col=(0.55, 0.3, 0.9), alpha=0.6)
ai = mesh_obj("afterimage", [(x * 0.32 * HW, y * 0.32 * HW, 0) for x, y in rrect(1.0, 2.1, 0.0, n=32, p=0.25)], [tuple(range(32))], ai_m, pc, (HW * 0.52, HH * 0.08, -D_ + 0.0004))
_ae = ai_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.0), (PV0, 0.0), (PV0 + 6, 1.4), (F_15, 0.9), (PV1, 0.25)):
    _ae.default_value = v; _ae.keyframe_insert("default_value", frame=f)
txt_m = mat("pov_txt", (1, 1, 1), 0.5, emit=3.0)
t15 = text("t15", "15 DAQIQA", HW * 0.16, (HW * 0.52, -HH * 0.32, -D_ + 0.0006), (0, 0, 0), txt_m, parent=pc)
for o in (mask, ai): vis(o, [S["pov"]])
vis(t15, [(F_15, PV1)])

# ======================================================================
# 10) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links; bg = N["Background"]
WORLD = {"night": (0.002, 0.004, 0.012), "xr": (0.0, 0.006, 0.02), "mac": (0.0, 0.0, 0.0), "cut": (0.012, 0.018, 0.035), "ret": (0.03, 0.008, 0.03)}
def world_of(n):
    if n in ROOMN: return "night"
    if n in XRN: return "xr"
    return {"pupil": "mac", "maxpup": "mac", "cut": "cut", "retina": "ret"}[n]
for f_, n in SHOTS:
    bg.inputs[0].default_value = (*WORLD[world_of(n)], 1); bg.inputs[0].keyframe_insert("default_value", frame=f_)
    bg.inputs[1].default_value = 1.0
ckey(w.node_tree)
FT = empty("faceKeyT"); _cl = FT.constraints.new("COPY_LOCATION"); _cl.target = headE
ROOMLIT = rng("hook", "wide", "face", "ots", "beam", "off", "pov")
# tungi lampa: 14-kadrgacha yonadi
point("bed_bulb", tuple(BL + V(0, 0, 0.36)), 0.04, (1.0, 0.68, 0.36), [(1, 45.0), (F_LAMP, 0.0)])
area("bed_warm", tuple(BL + V(-0.4, -0.4, 0.6)), 0.6, (1.0, 0.7, 0.45), [(1, 22.0), (F_LAMP, 0.0)], target=FT)
shade_e = shade_m.node_tree.nodes["Principled BSDF"]; shade_e.inputs["Emission Color"].default_value = (1.0, 0.75, 0.45, 1)
for f_, e in ((1, 2.5), (F_LAMP, 0.0)):
    shade_e.inputs["Emission Strength"].default_value = e; shade_e.inputs["Emission Strength"].keyframe_insert("default_value", frame=f_)
ckey(shade_m.node_tree)
# oy nuri (derazadan), xona to'ldiruvchisi, yuz chet nuri
moon = area("moon_key", (0.6, -1.0, 2.1), 1.4, (0.45, 0.6, 1.0), lights_for(ROOMLIT, 13.0), target=empty("moonT", tuple(BED + V(0.1, 0.7, 0.5))))
area("room_fill", (0.6, 0.6, 2.5), 2.0, (0.5, 0.58, 0.85), lights_for(ROOMLIT, 1.5), target=empty("rfT", (BED.x, BED.y, 0.5)))
area("face_rim", tuple(EYEM + HUP * 0.35 - HXL * 0.25 - FDIR * 0.15), 0.3, (0.55, 0.7, 1.0), lights_for(rng("face", "ots", "beam", "off"), 2.0), target=FT)
# yakun: oy nuri asta so'nadi
eL = area("end_moon", tuple(EYEM - HXL * 0.5 + FDIR * 0.4 + V(0, 0, 0.3)), 0.5, (0.45, 0.6, 1.0), [(1, 0), (EN0, 3.0), (EN1 - 12, 0.8), (EN1 - 4, 0.0)], target=FT)
interp(eL.data, "LINEAR")
area("pov_clock", tuple(CLKW + V(-1.2, -0.6, 0.6)), 0.8, (0.5, 0.62, 1.0), lights_for([S["pov"]], 7.0), target=empty("clkT", tuple(CLKW)))
# telefon ekrani nuri (yuzga): to'rtburchak AREA, ekran normali bo'ylab (+Z mahalliy)
pl_ = area("phone_light", (0, 0, 0.004), 0.07, (0.72, 0.82, 1.0), [(1, 1.3), (F_OFF, 0.0)], parent=phone, shape=(0.065, 0.14))
pl_.rotation_euler = (math.pi, 0, 0)
# rentgen: sovuq to'ldiruvchi; makro: oy cheti + telefon aksi; kesim; to'r parda
area("xr_key", tuple(EYEM + FDIR * 0.6 + V(0, 0, 0.5)), 0.6, (0.6, 0.8, 1.0), lights_for(XR, 6.0), target=FT)
MT = empty("macT", tuple(MAC))
area("mac_rim", tuple(MAC + V(-0.09, -0.08, 0.09)), 0.06, (0.45, 0.6, 1.0), lights_for(MACR, 0.25), target=MT)
area("mac_phone", tuple(MAC + V(0.05, -0.22, 0.03)), 0.04, (0.75, 0.85, 1.0), [(1, 0), (PU0, 0.15), (F_MAXP, 0.6), (MP1 + 1, 0)], target=MT, shape=(0.02, 0.04))
CT_ = empty("cutT", tuple(CUT))
area("C_key", tuple(CUT + V(0.9, -0.6, 0.7)), 0.6, (1.0, 0.95, 0.9), lights_for(CUTR, 30.0), target=CT_)
area("C_fill", tuple(CUT + V(0.8, 0.6, -0.5)), 0.6, (1.0, 0.85, 0.75), lights_for(CUTR, 10.0), target=CT_)
area("C_rim", tuple(CUT + V(-0.4, -0.8, 0.6)), 0.5, (0.35, 0.6, 1.0), lights_for(CUTR, 20.0), target=CT_)
RT_ = empty("retT", tuple(RET + V(0, 0, 0.6)))
area("R_key", tuple(RET + V(-3.0, -3.5, 4.0)), 3.0, (0.85, 0.75, 1.0), lights_for(RETR, 260.0), target=RT_)
area("R_rim", tuple(RET + V(3.5, 3.0, 1.5)), 2.5, (0.4, 0.6, 1.0), lights_for(RETR, 300.0), target=RT_)

# ======================================================================
# 11) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
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
