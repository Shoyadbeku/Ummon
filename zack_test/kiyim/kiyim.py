# "Ko'cha shimida karavotga yotish" — Zack D. Films uslubida 40.4 s video (970 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, yostiq/ (lib.py, micro.py, mite.py), yangi: denim.py (jinsi, E. coli, chang kanasi, kesim).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_kiyim.sh
# Render: OUT=/tmp/claude-0/frames_k/ SAMPLES=8 PCT=50 python3 -I zack_test/kiyim/kiyim.py --render
# Sinov:  FRAMES=20,60,130 PCT=30 OUT=/tmp/claude-0/test/ ... --render   |   Bo'lak: RANGE=a,b
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ZT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ZT)
from lib import *                     # sahnani tozalaydi; bpy, math, random, Vector, Matrix, mc, sc, R, PH, BK, yordamchilar
import bmesh
import mite as M
import micro as U
import denim as DN
sys.path.insert(0, os.path.join(ZT, "gemorroy")); import parts as PT
PT.VIEWPORT_OFF = True
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_k/")
random.seed(7)
END = 970
sc.frame_start, sc.frame_end = 1, END
def V(*a): return Vector(a)
def ckey(idb, path=None): interp(idb, "CONSTANT", path)
def Rz(v, deg):
    a = R(deg); return Vector((v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a), 0))

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "enter"), (47, "jeans"), (92, "flop"), (143, "morph"), (176, "busup"), (213, "bus"), (255, "taxi"), (267, "cafe"),
         (284, "hosp"), (325, "dive"), (341, "divem"), (359, "flakes"), (431, "ecoli"), (461, "eggs"), (551, "allday"),
         (623, "drop"), (647, "xsec"), (691, "sitbed"), (758, "transfer"), (851, "night"), (937, "revealm"), (953, "revealw")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
APT_EVE = rng("enter", "jeans", "flop", "morph", "sitbed")
APT_NIGHT = rng("night", "revealw")
APT = APT_EVE + APT_NIGHT
BUSR = rng("busup", "bus", "allday")
DENR = rng("divem", "flakes", "ecoli", "eggs", "drop")
HOSPR = rng("hosp", "dive")
F_HATCH = 506          # tuxum yoriladi
F_TH = 880             # "siz ularni..." — issiqlik kamerasi yoqiladi
F_DROP = 631           # ter tomchisi matoga tegadi

# ======================================================================
# 1) KVARTIRA: yotoqxona (kechqurun / tun) — karavot chap devorda, eshik old devorda, deraza o'ng devorda
# ======================================================================
apt_objs = []
def A(o): apt_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.92, 0.88, 0.8))
X0, X1, Y0, Y1, HZ = -2.6, 2.4, -2.2, 2.4, 2.7
A(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
A(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
A(box("wall_L", (0.1, Y1 - Y0, HZ), (X0 - 0.05, (Y0 + Y1) / 2, HZ / 2), wall_m))
A(box("wall_B", (X1 - X0, 0.1, HZ), ((X0 + X1) / 2, Y1 + 0.05, HZ / 2), wall_m))
# old devor: eshik o'yig'i (DX0..DX1, balandlik 2.1)
DX0, DX1, DH = -0.15, 0.75, 2.1
A(box("wall_F1", (DX0 - X0, 0.1, HZ), ((X0 + DX0) / 2, Y0 - 0.05, HZ / 2), wall_m))
A(box("wall_F2", (X1 - DX1, 0.1, HZ), ((DX1 + X1) / 2, Y0 - 0.05, HZ / 2), wall_m))
A(box("wall_F3", (DX1 - DX0, 0.1, HZ - DH), ((DX0 + DX1) / 2, Y0 - 0.05, (DH + HZ) / 2), wall_m))
frame_m = mat("trim", (0.93, 0.92, 0.88), 0.35)
for nm, sz, lc in (("df_l", (0.06, 0.14, DH), (DX0 - 0.03, Y0 - 0.05, DH / 2)), ("df_r", (0.06, 0.14, DH), (DX1 + 0.03, Y0 - 0.05, DH / 2)),
                   ("df_t", (DX1 - DX0 + 0.12, 0.14, 0.06), ((DX0 + DX1) / 2, Y0 - 0.05, DH + 0.03))):
    A(box(nm, sz, lc, frame_m))
door = A(empty("door_hinge", (DX1, Y0 - 0.02, 0)))
box("door_leaf", (DX1 - DX0 - 0.02, 0.045, DH - 0.01), (-(DX1 - DX0) / 2, 0, DH / 2), mat("door_m", (0.42, 0.27, 0.16), 0.45, coat=0.3), parent=door)
cyl("door_knob", 0.025, 0.07, (-(DX1 - DX0) + 0.1, 0.05, 1.0), mat("brass", (0.9, 0.7, 0.35), 0.25, metal=1.0), rot=(90, 0, 0), parent=door)
for f_, a_ in ((1, 0), (3, 0), (12, 98), (16, 92)):
    door.rotation_euler = (0, 0, R(a_)); door.keyframe_insert("rotation_euler", frame=f_)
# yo'lak (eshik ortida, iliq chiroq)
A(box("hall_floor", (3.0, 2.5, 0.02), (0.3, Y0 - 1.35, -0.01), floor_m))
A(box("hall_wall", (3.0, 0.1, HZ), (0.3, Y0 - 2.6, HZ / 2), mat("hall_w", (0.75, 0.62, 0.48), 0.7)))
A(box("hall_wallL", (0.1, 2.5, HZ), (-1.2, Y0 - 1.35, HZ / 2), mat("hall_w2", (0.75, 0.62, 0.48), 0.7)))
A(box("hall_wallR", (0.1, 2.5, HZ), (1.8, Y0 - 1.35, HZ / 2), mat("hall_w3", (0.75, 0.62, 0.48), 0.7)))
A(box("hall_ceil", (3.0, 2.5, 0.05), (0.3, Y0 - 1.35, HZ), mat("hall_c", (0.85, 0.85, 0.82), 0.8)))
# o'ng devor: deraza (kechki quyosh shu yerdan)
WY0, WY1, WZ0, WZ1 = -1.3, 0.4, 0.9, 2.25
A(box("wall_R1", (0.1, WY0 - Y0, HZ), (X1 + 0.05, (Y0 + WY0) / 2, HZ / 2), wall_m))
A(box("wall_R2", (0.1, Y1 - WY1, HZ), (X1 + 0.05, (WY1 + Y1) / 2, HZ / 2), wall_m))
A(box("wall_R3", (0.1, WY1 - WY0, WZ0), (X1 + 0.05, (WY0 + WY1) / 2, WZ0 / 2), wall_m))
A(box("wall_R4", (0.1, WY1 - WY0, HZ - WZ1), (X1 + 0.05, (WY0 + WY1) / 2, (WZ1 + HZ) / 2), wall_m))
WCw = Vector((X1 + 0.05, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2)); WW, WH = WY1 - WY0, WZ1 - WZ0
for nm, sz, off in (("wf_t", (0.12, WW + 0.04, 0.05), (0, 0, WH / 2)), ("wf_b", (0.2, WW + 0.04, 0.06), (-0.05, 0, -WH / 2)),
                    ("wf_l", (0.12, 0.05, WH), (0, -WW / 2, 0)), ("wf_r", (0.12, 0.05, WH), (0, WW / 2, 0)), ("wf_m", (0.08, 0.04, WH), (0, 0, 0))):
    A(box(nm, sz, tuple(WCw + Vector(off)), frame_m))
A(box("curtain", (0.06, 0.45, 2.4), (X1 - 0.08, WY1 + 0.3, 1.3), mat("curtain_m", (0.62, 0.45, 0.32), 0.9, sss=0.1)))
A(box("baseboard", (X1 - X0, 0.03, 0.1), ((X0 + X1) / 2, Y1 - 0.015, 0.05), frame_m))
A(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X0 + 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
A(plane("out_ground", (40, 40), (X1 + 20, 0, -0.3), mat("out_grass", (0.05, 0.07, 0.04), 0.9)))
rw = random.Random(3); bld_m = mat("bld", (0.35, 0.3, 0.27), 0.8)
win_lit = mat("bwin_lit", (1.0, 0.75, 0.42), 0.4, emit=2.5)
for i in range(6):
    y = -7 + i * 2.6 + rw.uniform(-0.4, 0.4); h = rw.uniform(5, 14); x = X1 + 12 + rw.uniform(0, 6)
    A(box(f"bld{i}", (1.6, 2.0, h), (x, y, h / 2 - 0.3), bld_m))
    for k in range(rw.randint(4, 8)):
        A(box(f"bwin{i}_{k}", (0.02, 0.28, 0.32), (x - 0.81, y + rw.uniform(-0.8, 0.8), rw.uniform(0.6, h - 0.6)), win_lit))
def gltf(path, loc, rot_z=0.0, scale=1.0):
    e = empty(os.path.basename(path).split(".")[0] + "_grp", loc); import_gltf(path, e)
    e.rotation_euler.z = R(rot_z); e.scale = (scale,) * 3 if not isinstance(scale, tuple) else scale
    return e
A(gltf(PH + "Sofa_01/Sofa_01.gltf", (X1 - 0.38, 1.35, 0), 90, 1.0))
A(gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (X1 - 1.25, 1.35, 0), 0, 1.0))
A(gltf(PH + "potted_plant_01/potted_plant_01.gltf", (X1 - 0.35, -1.75, 0), 200, 1.0))
A(gltf(PH + "Shelf_01/Shelf_01.gltf", (X1 - 0.02, 2.1, 0), 90, 0.8))
A(plane("rug", (1.8, 1.3), (0.6, 0.2, 0.004), mat("rug", (0.45, 0.22, 0.16), 0.95)))
# karavot: uzun o'qi Y, bosh tomoni orqa devorda (+Y)
bed_grp = A(gltf(PH + "GothicBed_01/GothicBed_01.gltf", (0, 0, 0), 0, 1.0))
bpy.context.view_layer.update(); _dg = bpy.context.evaluated_depsgraph_get()
def hit_z(x, y, z0=2.0):
    dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, *_ = sc.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
    return loc.z if ok else 0.0
HEAD_SIGN = 1 if hit_z(0.03, 1.0) > hit_z(0.03, -0.97) else -1
if HEAD_SIGN < 0: bed_grp.rotation_euler.z = R(180)
BED = Vector((X0 + 0.78, Y1 - 1.08, 0.0)); bed_grp.location = BED
bpy.context.view_layer.update()
MTOP = hit_z(BED.x, BED.y, 1.2)
FOOT_Y = BED.y - 0.99
FOOT_TOP = hit_z(BED.x, FOOT_Y + 0.03, 1.4)
print("BED", tuple(BED), "mattress", round(MTOP, 3), "foot", round(FOOT_TOP, 3), "head", HEAD_SIGN)
A(gltf(PH + "ClassicNightstand_01/ClassicNightstand_01.gltf", (BED.x + 1.08, Y1 - 0.25, 0), 0, 1.0))
NS_TOP = 0.70
BL = Vector((BED.x + 1.08, Y1 - 0.25, NS_TOP))
shade_m = mat("shade", (0.95, 0.88, 0.75), 0.8, sss=0.2)
A(cyl("bl_base", 0.07, 0.03, tuple(BL + V(0, 0, 0.015)), mat("bl_base_m", (0.75, 0.6, 0.35), 0.25, metal=0.9)))
A(cyl("bl_stem", 0.01, 0.28, tuple(BL + V(0, 0, 0.16)), mat("bl_stem_m", (0.75, 0.6, 0.35), 0.25, metal=0.9)))
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.15, radius2=0.09, depth=0.2, end_fill_type="NOTHING")
shade = bpy.context.object; shade.name = "bl_shade"; shade.location = tuple(BL + V(0, 0, 0.36)); shade.data.materials.append(shade_m)
shade.modifiers.new("so", "SOLIDIFY").thickness = 0.004; smooth(shade); A(shade)
# ko'rpa matosi: mayin to'qima + "mq" (0..1) -> avtobus o'rindig'i naqshiga aylanadi (morph kadri)
def moquette_color(N, L, vec, prefix=""):
    """avtobus o'rindig'i matosi: to'q ko'k asos, binafsha/sariq/firuza bo'laklar (Voronoi hujayralari)"""
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 24.0; vo.inputs["Randomness"].default_value = 1.0
    L.new(vec, vo.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "CONSTANT"
    cols = [(0.0, (0.015, 0.02, 0.09)), (0.55, (0.015, 0.02, 0.09)), (0.7, (0.5, 0.03, 0.32)), (0.8, (0.9, 0.62, 0.05)), (0.9, (0.02, 0.45, 0.45))]
    cr.elements[0].position, cr.elements[0].color = cols[0][0], (*cols[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = cols[1][0], (*cols[1][1], 1)
    for p_, c_ in cols[2:]: e = cr.elements.new(p_); e.color = (*c_, 1)
    sep = N.new("ShaderNodeSeparateColor"); L.new(vo.outputs["Color"], sep.inputs[0]); L.new(sep.outputs[0], ramp.inputs[0])
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.feature = "DISTANCE_TO_EDGE"; vo2.inputs["Scale"].default_value = 24.0; L.new(vec, vo2.inputs["Vector"])
    edge = P.math_n(N, L, "LESS_THAN", vo2.outputs["Distance"], 0.06)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[7].default_value = (0.015, 0.02, 0.09, 1)
    L.new(ramp.outputs[0], mx.inputs[6]); L.new(edge, mx.inputs["Factor"])
    return mx.outputs[2]
def fabric_shader(name, base_col, scale_obj=1.0, morph=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.88; b.inputs["Sheen Weight"].default_value = 0.6; b.inputs["Subsurface Weight"].default_value = 0.05
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale_obj,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 60.0; L.new(mp.outputs[0], wv.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; L.new(mp.outputs[0], nz.inputs["Vector"])
    c0 = N.new("ShaderNodeMix"); c0.data_type = "RGBA"; c0.inputs[6].default_value = (*base_col, 1)
    c0.inputs[7].default_value = (*[x * 0.75 for x in base_col], 1); L.new(nz.outputs["Fac"], c0.inputs["Factor"])
    col = c0.outputs[2]
    if morph:
        mqv = value_node(m, "mq", 0.0)
        mqc = moquette_color(N, L, mp.outputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(col, mx.inputs[6]); L.new(mqc, mx.inputs[7]); L.new(mqv, mx.inputs["Factor"])
        col = mx.outputs[2]
    L.new(col, b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
throw_m = fabric_shader("throw", (0.55, 0.5, 0.42), 1.0, morph=True)
def rumple_plane(name, w, d, z, m, amp=0.012, n=40, drape=0.0):
    bm = bmesh.new(); vs = []
    for j in range(n):
        for i in range(n):
            x = -w / 2 + w * i / (n - 1); y = -d / 2 + d * j / (n - 1)
            zz = amp * (math.sin(x * 9 + y * 3) * math.sin(y * 7 - x * 2) + 0.5 * math.sin(x * 17 + 1.3))
            if drape and abs(x) > w / 2 - drape: zz -= (abs(x) - (w / 2 - drape)) * 2.2
            vs.append(bm.verts.new((x, y, zz)))
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i; bm.faces.new((vs[a], vs[a + 1], vs[a + n + 1], vs[a + n]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(m); smooth(o)
    o.location = (0, 0, z); o.modifiers.new("so", "SOLIDIFY").thickness = 0.015
    return o
throw = A(rumple_plane("throw", 1.62, 1.3, MTOP + 0.012, throw_m, drape=0.12)); throw.location.x = BED.x; throw.location.y = FOOT_Y + 0.72
pillow_m = mat("pillow", (0.9, 0.9, 0.88), 0.8, sss=0.08)
pillow_m.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.5
pil = A(box("pillow", (0.66, 0.42, 0.13), (BED.x, BED.y + 0.72, MTOP + 0.06), pillow_m, bevel=0.045)); pil.modifiers.new("sub", "SUBSURF").levels = 2
for o in apt_objs: vis(o, APT)

# ======================================================================
# 2) BRIAN (asosiy qahramon, jinsi shim) + yo'lovchilar
# ======================================================================
def soften2(meshes, rough=0.5):
    soften(meshes)
    for o in meshes:
        for m in o.data.materials:
            if m and m.use_nodes and "hair" not in m.name.lower():
                for n in m.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED": n.inputs["Roughness"].default_value = rough
def load(name, file):
    r_, a_, ms = mc.load_character(name, file); sc.render.fps = 24; soften2(ms); return r_, a_, ms
broot, bri, bmeshes = load("bri", "Brian.fbx")
print("BRIAN meshes", [(o.name, [m.name for m in o.data.materials]) for o in bmeshes])
def act(file, inplace=True): a = mc.load_action(file, inplace); sc.render.fps = 24; return a
def S_(arm, a, start, src=None, speed=1.0, blend=0, repeat=1.0):
    s = mc.add_strip(arm, a, start, src=src, speed=speed, blend=blend, hold=True, repeat=repeat)
    s.use_auto_blend = False; s.blend_out = 0
    if blend: s.blend_in = blend
    return s
def span(a, n, src=None, speed=1.0):
    a0, b0 = src or a.frame_range
    return max(1.0, n * speed / ((b0 - a0) * 0.8))
def root_for(hips_w, rot, hips_local, z):
    p = Vector(hips_w) - Rz(hips_local, rot); return (p.x, p.y, z)
WALK = act("Sad_Walk.fbx"); STS = act("Stand_To_Sit.fbx", inplace=False); LIE = act("Lying_Down.fbx", inplace=False)
SIT4 = act("Sitting_Idle_4.fbx", inplace=False); SIT5 = act("Sitting_Idle_5.fbx", inplace=False); SIT3 = act("Sitting_Idle_3.fbx", inplace=False)
JOS = act("Jostled_Passenger.fbx", inplace=False); SLP = act("Laying_Sleeping.fbx", inplace=False)
# karavot oyog'ida 0.68 m suyanchiq bor: uzun yon tomonga (+X ga qarab, root 90) o'tiradi va eni bo'ylab chalqancha yotadi
RS = 90
HIPS_SIT = Vector((BED.x + 0.75 - 0.38, BED.y - 0.25, 0))
# 1 kirish: eshikdan +Y ga yuradi (root 180), 1.3x tezlik
WS = 1.3; W0 = Vector((0.32, Y0 - 0.55, 0)); WV = 0.032 * WS * 0.8 / 0.8
place(broot, 1, tuple(W0), 180)
place(broot, 46, tuple(W0 + V(0, 0.0415 * 45, 0)), 180)
S_(bri, WALK, 1, speed=WS, repeat=span(WALK, 48, speed=WS))
# 2 o'tirish (oyoq tomonda, -Y ga qarab)
J0 = S["jeans"][0]
place(broot, J0, root_for(HIPS_SIT, RS, (0, 0.45), 0.0), RS)
S_(bri, STS, J0, src=(8, 68), speed=1.15)
# 3 chalqancha yotish (Lying_Down 40-kadridan: oyoqlar ko'tarilgan)
F0_ = S["flop"][0]
LH = Vector((0, 0.06, 0))
place(broot, F0_, root_for(HIPS_SIT, RS, LH, -0.27), RS)
S_(bri, LIE, F0_, src=(40, 140), speed=1.7, blend=3)
place(broot, F0_ + 24, root_for(HIPS_SIT, RS, LH, -0.18), RS)
# 5 avtobus: o'rindiqqa o'tiradi (oldinga +X, root 90)
BUS = Vector((60.0, 0.0, 0.0)); PITCH = 0.86
def row_x(i): return BUS.x - 3.6 + i * PITCH
SEAT_Z = 0.46
def seat_hips(i, side, aisle=True):
    return Vector((row_x(i) + 0.0, BUS.y + side * (0.5 if aisle else 0.96), SEAT_Z + 0.1))
B_SEAT = seat_hips(4, -1)
B0, B1 = S["bus"]
place(broot, B0, root_for(B_SEAT, 90, (0, 0.45), 0.01), 90)
S_(bri, STS, B0, src=(1, 68), speed=1.25)
# 6 taksi / 7 kafe: "tushib o'tirish" (Sitting_Idle_4 + root sakrashi)
TX = Vector((60.0, 25.0, 0.0)); CF = Vector((60.0, 50.0, 0.0)); HP = Vector((60.0, 75.0, 0.0))
TX_SEAT_Z = 0.42
def plop(root, f, hips, rot, seat_z, hl=(0, -0.04, 0.59), h=0.16):
    zz = seat_z + 0.1 - hl[2]; base = root_for(hips, rot, hl, zz)
    for df, dz in ((0, h), (4, -0.035), (7, 0.012), (10, 0.0)):
        place(root, f + df, (base[0], base[1], base[2] + dz), rot)
T0_ = S["taxi"][0]; plop(broot, T0_, TX + V(0.0, -0.32, 0), 90, TX_SEAT_Z)
S_(bri, SIT4, T0_)
C0_ = S["cafe"][0]
CHAIR = CF + V(0, 0.0, 0)
plop(broot, C0_ + 2, CHAIR + V(0, 0.06, 0), 0, 0.47)
S_(bri, SIT4, C0_)
# 8 kasalxona: stullar qatori (-Y ga qaraydi)
H0_ = S["hosp"][0]
HCH = [HP + V(x, 0, 0) for x in (-0.825, -0.275, 0.275, 0.825)]
H_SEAT = HCH[2] + V(0, 0.04, 0.56)
place(broot, H0_, root_for(H_SEAT, 0, (0, 0.45), 0.01), 0)
S_(bri, STS, H0_, src=(1, 68), speed=1.15)
# 13 kun bo'yi (avtobus timelapse): o'tirgan
AD0, AD1 = S["allday"]
place(broot, AD0, root_for(B_SEAT, 90, (0, -0.04), SEAT_Z + 0.1 - 0.59), 90)
S_(bri, SIT5, AD0, speed=2.5, repeat=span(SIT5, AD1 - AD0 + 4, speed=2.5))
# 16 choyshabga o'tirish
SB0 = S["sitbed"][0]
place(broot, SB0, root_for(HIPS_SIT, RS, (0, 0.45), 0.0), RS)
S_(bri, STS, SB0, src=(1, 68), speed=1.0)
# 18 tun: uxlaydi (Laying_Sleeping), boshi yostiqda
N0, N1 = S["night"]
SLEEP_ROOT = Vector((BED.x - 0.03, BED.y + 0.72 - 0.57, MTOP - 0.95))
place(broot, N0, tuple(SLEEP_ROOT), 0)
S_(bri, SLP, N0, repeat=span(SLP, END - N0 + 4))
ckey(broot)
SMOOTH_R = [(F0_, F0_ + 24), (T0_, T0_ + 10), (C0_ + 2, C0_ + 12)]     # yotish va "tushib o'tirish" — silliq
for fc in fcurves(broot):
    for k in fc.keyframe_points:
        if int(k.co.x) == 1: k.interpolation = "LINEAR"                 # yurish
        if fc.data_path == "location" and any(a <= int(k.co.x) < b for a, b in SMOOTH_R): k.interpolation = "BEZIER"

# yo'lovchilar (avtobus va kasalxona)
def passenger(name, file, keys):
    r_, a_, ms = load(name, file)
    for f_, loc, rot_, action, spd in keys:
        place(r_, f_, loc, rot_)
        S_(a_, action, f_, speed=spd, repeat=span(action, 400, speed=spd))
    ckey(r_)
    return r_, a_, ms
P_FAR = Vector((0, -300, -50))
SIT_Z = SEAT_Z + 0.1 - 0.59
jroot, joe, jmeshes = passenger("joe", "Joe.fbx", [(1, root_for(seat_hips(3, 1), 90, (0, 0.01), SEAT_Z + 0.1 - 0.58), 90, JOS, 0.9)])
kroot, kate, kmeshes = passenger("kate", "Kate.fbx", [(1, root_for(seat_hips(6, 1, False), 90, (0, -0.04), SIT_Z), 90, SIT5, 1.0)])
proot, pete, pmeshes = passenger("pete", "Pete.fbx", [(1, root_for(seat_hips(6, -1, False), 90, (0, -0.04), SEAT_Z + 0.1 - 0.55), 90, SIT3, 1.0),
                                                       (H0_, root_for(HCH[0] + V(0, 0.04, 0.56), 0, (0, -0.04), 0.01), 0, SIT3, 1.0),
                                                       (S["dive"][1] + 1, root_for(seat_hips(6, -1, False), 90, (0, -0.04), SEAT_Z + 0.1 - 0.55), 90, SIT3, 1.0)])
# timelapse: yo'lovchilar paydo bo'lib / yo'qolib turadi
def flick(meshes, base_ranges, gaps):
    rr = []
    for a, b in base_ranges:
        cur = a
        for g0, g1 in gaps:
            if a <= g0 <= b:
                if g0 - 1 >= cur: rr.append((cur, g0 - 1))
                cur = g1 + 1
        if cur <= b: rr.append((cur, b))
    for o in meshes: vis(o, rr, recursive=False)
flick(jmeshes, BUSR, [(AD0 + 8, AD0 + 30), (AD0 + 52, AD1)])
flick(kmeshes, BUSR, [(AD0, AD0 + 18), (AD0 + 40, AD0 + 58)])
flick(pmeshes, BUSR + HOSPR, [(AD0 + 22, AD0 + 46)])

# Brian bog'lanish nuqtalari
hipsE = child_of_bone("bri_hips", bri, "Hips"); headE = child_of_bone("bri_head", bri, "Head")
thighE = child_of_bone("bri_thigh", bri, "RightUpLeg")
thighM = empty("bri_thighM", (0, 0.2, 0.06), thighE)
def wp(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
# sumka: o'ng qo'lda, 28-kadrda yerga tushadi
bag = empty("bag")
box("bag_body", (0.3, 0.14, 0.4), (0, 0, -0.2), mat("bag_m", (0.06, 0.07, 0.08), 0.6), parent=bag, bevel=0.03)
cyl("bag_strap", 0.012, 0.18, (0, 0, 0.02), mat("strap_m", (0.04, 0.04, 0.04), 0.5), rot=(0, 90, 0), parent=bag)
handE = child_of_bone("bri_hand", bri, "RightHand")
for f_ in range(1, 29, 2):
    p_ = wp(handE, f_) + V(0, 0, -0.04); key(bag, f_, loc=tuple(p_), rot=(0, 0, 180))
p_ = wp(handE, 28)
key(bag, 33, loc=(p_.x + 0.05, p_.y + 0.1, 0.2), rot=(20, 0, 170)); key(bag, 35, loc=(p_.x + 0.06, p_.y + 0.12, 0.22), rot=(25, 0, 168))
key(bag, 38, loc=(p_.x + 0.08, p_.y + 0.14, 0.21), rot=(14, 0, 165)); key(bag, 40, loc=(p_.x + 0.08, p_.y + 0.14, 0.2), rot=(10, 0, 165))
interp(bag, "LINEAR"); vis(bag, APT_EVE)
HIPS_LIE = wp(hipsE, S["morph"][0] + 4)
print("lying hips", tuple(round(x, 3) for x in HIPS_LIE))

# ko'rpa (tun): uxlayotgan tana bo'ylab Gauss do'ngliklari
sc.frame_set(N0 + 10); bpy.context.view_layer.update()
BPTS = []
for bn in ("Hips", "Spine", "Spine1", "Spine2", "LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg", "LeftFoot", "RightFoot"):
    pb = bri.pose.bones["mixamorig:" + bn]
    for t_ in (0.0, 0.5):
        BPTS.append(bri.matrix_world @ pb.head.lerp(pb.tail, t_))
SPY = (bri.matrix_world @ bri.pose.bones["mixamorig:Spine2"].head).y
blanket_m = fabric_shader("blanket", (0.2, 0.3, 0.55), 1.0)
def blanket_mesh():
    n_x, n_y = 70, 80; bm = bmesh.new(); vs = []
    y0 = BED.y - 1.0; y1 = SPY + 0.05
    for j in range(n_y):
        for i in range(n_x):
            x = BED.x - 0.8 + 1.6 * i / (n_x - 1); y = y0 + (y1 - y0) * j / (n_y - 1)
            dx = abs(x - BED.x); z = MTOP + 0.03
            for bp_ in BPTS:
                d2 = (x - bp_.x) ** 2 + (y - bp_.y) ** 2
                z = max(z, MTOP + 0.03 + min(0.24, (bp_.z - MTOP) * 0.85 + 0.08) * math.exp(-d2 / (2 * 0.17 ** 2)))
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
blk = blanket_mesh(); vis(blk, APT_NIGHT)
vis(throw, APT_EVE)

# ======================================================================
# 3) AVTOBUS SALONI (protsedural): o'rindiqlar (naqshli mato), tutqichlar, derazalar, harakatlanuvchi shahar
# ======================================================================
bus_objs = []
def B(o): bus_objs.append(o); return o
mq_m = bpy.data.materials.new("moquette"); mq_m.use_nodes = True
_N = mq_m.node_tree.nodes; _L = mq_m.node_tree.links; _b = _N["Principled BSDF"]
_tc = _N.new("ShaderNodeTexCoord"); _mp = _N.new("ShaderNodeMapping"); _mp.inputs["Scale"].default_value = (1.0,) * 3; _L.new(_tc.outputs["Object"], _mp.inputs[0])
_L.new(moquette_color(_N, _L, _mp.outputs[0]), _b.inputs["Base Color"])
_b.inputs["Roughness"].default_value = 0.92; _b.inputs["Sheen Weight"].default_value = 0.8; _b.inputs["Sheen Roughness"].default_value = 0.35
_wv = _N.new("ShaderNodeTexNoise"); _wv.inputs["Scale"].default_value = 400.0; _L.new(_mp.outputs[0], _wv.inputs["Vector"])
_bp = _N.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.2; _L.new(_wv.outputs["Fac"], _bp.inputs["Height"]); _L.new(_bp.outputs[0], _b.inputs["Normal"])
plastic_m = mat("bus_plastic", (0.55, 0.57, 0.58), 0.4)
pole_m = mat("pole", (0.95, 0.72, 0.05), 0.25, coat=0.5)
floor_bus = mat("bus_floor", (0.18, 0.19, 0.2), 0.65)
wall_bus = mat("bus_wall", (0.78, 0.8, 0.8), 0.45)
BL_, BW_, BH_ = 10.0, 2.5, 2.25
B(box("bus_floor", (BL_, BW_, 0.06), tuple(BUS + V(0, 0, -0.03)), floor_bus))
B(box("bus_ceil", (BL_, BW_, 0.06), tuple(BUS + V(0, 0, BH_ + 0.03)), wall_bus))
for sy in (-1, 1):
    B(box(f"bus_wlow{sy}", (BL_, 0.08, 0.92), tuple(BUS + V(0, sy * BW_ / 2, 0.46)), wall_bus))
    B(box(f"bus_whigh{sy}", (BL_, 0.08, 0.42), tuple(BUS + V(0, sy * BW_ / 2, BH_ - 0.21)), wall_bus))
    for k in range(13):
        B(box(f"bus_pil{sy}_{k}", (0.1, 0.1, BH_ - 1.34), tuple(BUS + V(-BL_ / 2 + k * BL_ / 12, sy * BW_ / 2, 0.92 + (BH_ - 1.34) / 2)), plastic_m))
    B(box(f"bus_rail{sy}", (BL_, 0.03, 0.03), tuple(BUS + V(0, sy * 0.55, BH_ - 0.32)), pole_m))
    B(box(f"bus_light{sy}", (BL_ - 0.4, 0.12, 0.03), tuple(BUS + V(0, sy * 0.35, BH_ - 0.02)), mat(f"bus_lamp{sy}", (1, 1, 1), 0.3, emit=6.0)))
B(box("bus_back", (0.08, BW_, BH_), tuple(BUS + V(-BL_ / 2, 0, BH_ / 2)), wall_bus))
B(box("bus_front", (0.08, BW_, BH_), tuple(BUS + V(BL_ / 2, 0, BH_ / 2)), wall_bus))
for i in range(10):
    x = row_x(i)
    for sy in (-1, 1):
        cy = BUS.y + sy * 0.73
        B(box(f"seat_c{i}{sy}", (0.46, 0.88, 0.12), (x + 0.02, cy, SEAT_Z - 0.06), mq_m, bevel=0.03))
        bk = B(box(f"seat_b{i}{sy}", (0.1, 0.88, 0.62), (x - 0.24, cy, SEAT_Z + 0.33), mq_m, rot=(0, -10, 0), bevel=0.03))
        B(box(f"seat_shell{i}{sy}", (0.04, 0.9, 0.66), (x - 0.31, cy, SEAT_Z + 0.32), plastic_m, rot=(0, -10, 0), bevel=0.01))
        B(box(f"seat_leg{i}{sy}", (0.06, 0.06, SEAT_Z - 0.12), (x, cy + sy * 0.0 - sy * 0.3, (SEAT_Z - 0.12) / 2), plastic_m))
        if i % 2 == 0:
            B(cyl(f"pole{i}{sy}", 0.018, BH_, (x - 0.3, BUS.y + sy * 0.3, BH_ / 2), pole_m, verts=16))
        if not (i == 5 and sy < 0):                     # Brian engashganda boshi tutqichga kirib qolmasin
            B(cyl(f"grab{i}{sy}", 0.016, 0.3, (x - 0.24, BUS.y + sy * 0.3, SEAT_Z + 0.7), pole_m, rot=(90, 0, 0), verts=12))
B(box("stop_btn", (0.03, 0.06, 0.06), (row_x(4) - 0.3, BUS.y - 0.3, 1.25), mat("stop_red", (0.9, 0.05, 0.03), 0.3, emit=1.5)))
glass_bus = mat("bus_glass", (0.85, 0.9, 0.92), 0.02, alpha=0.08)
for sy in (-1, 1):
    B(plane(f"bus_glass{sy}", (BL_, BH_ - 1.34), tuple(BUS + V(0, sy * (BW_ / 2 + 0.01), 0.92 + (BH_ - 1.34) / 2)), glass_bus, rot=(90, 0, 0)))
# shahar (avtobus ortga qoldiradi): bo'sh ob'ekt -X ga suriladi
city = B(empty("city", tuple(BUS)))
asph = pbr("asphalt", "asphalt_02", 0.25); pave = pbr("pave", "concrete_pavement", 0.4)
plane("road", (260, 14), (60, 0, -0.55), asph, parent=city)
for sy in (-1, 1): plane(f"walk{sy}", (260, 4), (60, sy * 9, -0.4), pave, parent=city)
rc = random.Random(21)
fac_ms = [mat("fac1", (0.6, 0.55, 0.48), 0.8), mat("fac2", (0.42, 0.45, 0.5), 0.7), mat("fac3", (0.7, 0.62, 0.5), 0.8), mat("fac4", (0.35, 0.3, 0.28), 0.8)]
glass_city = mat("cwin", (0.15, 0.2, 0.25), 0.1, metal=0.6)
x = -60.0
while x < 190:
    w_ = rc.uniform(5, 11); h_ = rc.uniform(5, 18)
    for sy in (-1, 1):
        bx = box(f"cb{int(x)}{sy}", (w_ - 0.6, 6, h_), (x + w_ / 2, sy * 14.5, h_ / 2 - 0.4), rc.choice(fac_ms), parent=city)
        for fl in range(int(h_ / 3)):
            box(f"cw{int(x)}{sy}{fl}", (w_ - 1.6, 0.05, 1.2), (x + w_ / 2, sy * 11.45, 1.4 + fl * 3), glass_city, parent=city)
    if rc.random() < 0.5:
        for sy in (-1, 1):
            cyl(f"tree{int(x)}{sy}", 0.12, 3.0, (x + 1, sy * 8.0, 1.1), mat("trunk", (0.2, 0.13, 0.08), 0.8), parent=city, verts=8)
            sphere(f"crown{int(x)}{sy}", 1.4, (x + 1, sy * 8.0, 3.2), mat("leaf", (0.12, 0.22, 0.06), 0.8), parent=city, sub=2)
    x += w_
for f_, xx in ((S["busup"][0], 0.0), (AD0, -32.0), (AD1, -140.0)):
    city.location = BUS + V(xx, 0, 0); city.keyframe_insert("location", frame=f_)
interp(city, "LINEAR")
for o in bus_objs: vis(o, BUSR)

# ======================================================================
# 4) TAKSI ichi, KAFE, KASALXONA
# ======================================================================
tx_objs = []
def T(o): tx_objs.append(o); return o
leather = mat("taxi_seat", (0.08, 0.075, 0.07), 0.45, coat=0.2)
cush = T(box("tx_cush", (0.52, 1.4, 0.14), tuple(TX + V(0.0, 0, TX_SEAT_Z - 0.07)), leather, bevel=0.04))
for f_, s_ in ((1, 1.0), (T0_ + 3, 1.0), (T0_ + 5, 0.7), (T0_ + 8, 1.05), (T0_ + 11, 1.0)):
    cush.scale = (1, 1, s_); cush.keyframe_insert("scale", frame=f_)
T(box("tx_back", (0.14, 1.4, 0.62), tuple(TX + V(-0.3, 0, TX_SEAT_Z + 0.3)), leather, rot=(0, -14, 0), bevel=0.04))
for sy in (-1, 1):
    T(box(f"tx_front{sy}", (0.16, 0.55, 0.75), tuple(TX + V(0.78, sy * 0.38, 0.75)), leather, rot=(0, -8, 0), bevel=0.05))
    T(box(f"tx_door{sy}", (1.6, 0.06, 0.62), tuple(TX + V(0.2, sy * 0.8, 0.5)), mat(f"tx_door_m{sy}", (0.12, 0.12, 0.13), 0.5)))
    T(box(f"tx_doorup{sy}", (1.6, 0.06, 0.06), tuple(TX + V(0.2, sy * 0.8, 1.2)), mat(f"tx_frame{sy}", (0.05, 0.05, 0.05), 0.4)))
T(box("tx_roof", (1.8, 1.7, 0.05), tuple(TX + V(0.2, 0, 1.26)), mat("tx_head", (0.55, 0.53, 0.5), 0.9)))
T(box("tx_floor", (1.8, 1.7, 0.05), tuple(TX + V(0.2, 0, 0.08)), mat("tx_carpet", (0.05, 0.05, 0.05), 0.95)))
tx_city = T(empty("tx_city", tuple(TX)))
for k in range(26):
    h_ = rc.uniform(3, 9)
    box(f"txb{k}", (2.5, 1.0, h_), (-30 + k * 3.0, -6.0, h_ / 2 - 0.5), rc.choice(fac_ms), parent=tx_city)
    if k % 3 == 0: sphere(f"txl{k}", 0.15, (-30 + k * 3.0 + 1, -4.5, 2.5), mat(f"txlamp{k}", (1, 0.8, 0.4), 0.3, emit=8.0), parent=tx_city, sub=2)
for f_, xx in ((T0_ - 2, 6.0), (T0_ + 14, -6.0)):
    tx_city.location = TX + V(xx, 0, 0); tx_city.keyframe_insert("location", frame=f_)
interp(tx_city, "LINEAR")
for o in tx_objs: vis(o, [S["taxi"]])
cf_objs = []
def Cq(o): cf_objs.append(o); return o
Cq(plane("cf_floor", (6, 6), tuple(CF), pbr("cf_floor_m", "laminate_floor_02", 0.5)))
Cq(box("cf_wall", (6, 0.1, 3), tuple(CF + V(0, 1.4, 1.5)), mat("cf_brick", (0.45, 0.22, 0.14), 0.85)))
Cq(box("cf_wallL", (0.1, 6, 3), tuple(CF + V(-2.2, 0, 1.5)), mat("cf_wl", (0.82, 0.74, 0.62), 0.8)))
Cq(gltf(PH + "GreenChair_01/GreenChair_01.gltf", tuple(CHAIR), 0, 1.0))
tbl = Cq(gltf(PH + "round_wooden_table_01/round_wooden_table_01.gltf", tuple(CF + V(0, -0.85, 0)), 0, (0.7, 0.7, 0.76)))
Cq(cyl("cup", 0.042, 0.09, tuple(CF + V(0.15, -0.65, 0.76 + 0.045)), mat("cup_m", (0.95, 0.94, 0.9), 0.15, coat=0.6)))
Cq(cyl("coffee", 0.038, 0.005, tuple(CF + V(0.15, -0.65, 0.76 + 0.085)), mat("coffee_m", (0.12, 0.05, 0.02), 0.1, coat=1.0)))
Cq(gltf(PH + "GreenChair_01/GreenChair_01.gltf", tuple(CF + V(1.2, -0.2, 0)), -30, 1.0))
Cq(gltf(PH + "potted_plant_01/potted_plant_01.gltf", tuple(CF + V(-1.7, 1.0, 0)), 0, 1.0))
for k in range(3):
    Cq(sphere(f"cf_bulb{k}", 0.07, tuple(CF + V(-0.8 + k * 0.9, -0.4, 2.1)), mat(f"cf_bulb_m{k}", (1, 0.75, 0.4), 0.3, emit=12.0), sub=3))
    Cq(cyl(f"cf_cord{k}", 0.005, 0.9, tuple(CF + V(-0.8 + k * 0.9, -0.4, 2.6)), mat("cord", (0.02, 0.02, 0.02), 0.5), verts=6))
for o in cf_objs: vis(o, [S["cafe"]])
hp_objs = []
def Hq(o): hp_objs.append(o); return o
Hq(plane("hp_floor", (8, 8), tuple(HP), pbr("hp_floor_m", "floor_tiles_06", 0.8)))
mint = mat("hp_wall", (0.62, 0.75, 0.7), 0.6)
Hq(box("hp_wall", (8, 0.1, 3), tuple(HP + V(0, 0.55, 1.5)), mint))
Hq(box("hp_wallL", (0.1, 8, 3), tuple(HP + V(-2.6, 0, 1.5)), mint))
Hq(box("hp_stripe", (8, 0.02, 0.12), tuple(HP + V(0, 0.49, 1.0)), mat("hp_stripe_m", (0.1, 0.35, 0.55), 0.5)))
hseat_m = mat("hosp_seat", (0.1, 0.2, 0.42), 0.85)
metal = mat("hp_metal", (0.7, 0.72, 0.75), 0.3, metal=0.9)
Hq(box("hp_beam", (2.3, 0.06, 0.05), tuple(HP + V(0, 0.05, 0.3)), metal))
hcush = []
for i, c_ in enumerate(HCH):
    hcush.append(Hq(box(f"hp_seat{i}", (0.5, 0.46, 0.08), tuple(c_ + V(0, 0, 0.42)), hseat_m, bevel=0.03)))
    Hq(box(f"hp_back{i}", (0.5, 0.06, 0.5), tuple(c_ + V(0, 0.27, 0.72)), hseat_m, rot=(-8, 0, 0), bevel=0.02))
    Hq(box(f"hp_leg{i}", (0.04, 0.04, 0.3), tuple(c_ + V(0, 0.05, 0.15)), metal))
Hq(gltf(PH + "WetFloorSign_01/WetFloorSign_01.gltf", tuple(HP + V(1.6, -1.0, 0)), 30, 1.0))
Hq(box("hp_board", (1.2, 0.03, 0.7), tuple(HP + V(-1.0, 0.5, 1.75)), mat("hp_board_m", (0.95, 0.95, 0.93), 0.5)))
Hq(text("hp_txt", "NAVBAT", 0.16, tuple(HP + V(-1.0, 0.48, 1.85)), (90, 0, 0), mat("hp_txt_m", (0.1, 0.35, 0.55), 0.5)))
Hq(text("hp_num", "A-047", 0.12, tuple(HP + V(-1.0, 0.48, 1.62)), (90, 0, 0), mat("hp_num_m", (0.8, 0.1, 0.05), 0.4, emit=1.0)))
for o in hp_objs: vis(o, HOSPR)

# ======================================================================
# 5) MIKRO JINSI (1000x): twill, teri qipiqlari, E. coli, kana tuxumlari, ter tomchisi
# ======================================================================
DNC = V(0.0, 150.0, 0.0)
denE = empty("denE", tuple(DNC))
m_warp, m_weft = DN.denim_materials()
for m_ in (m_warp, m_weft): val_key(m_, "dirt", 1, 0.2)
den_thr, DBVH = DN.twill("dtw", 15.0, 0.62, 0.36, m_warp, m_weft, denE)
fuzz_m = M.hair_material("fuzz_b", (0.3, 0.38, 0.6), 0.6, trans=0.3)
den_static = den_thr + U.fuzz("dfz", DBVH, 60, fuzz_m, denE, (-7, 7, -7, 7), hair_fn=M.hair)
bk = U.BKit()
den_static += U.scatter_bacteria(bk, "dbg", DBVH, 380, (-7, 7, -7, 7), denE, seed=2)
def DP(x, y, z=0.0): return DNC + V(x, y, z)
A_C, B_C, C_C, D_C = (-3.5, -3.5), (3.5, -3.5), (3.5, 3.5), (-3.5, 3.5)
# teri qipiqlari: ko'plari allaqachon yopishgan, qolganlari yog'iladi
flake_m = M.skin_micro_material("flake_m")
fme = bpy.data.meshes.new("flake")
_bm = bmesh.new(); bmesh.ops.create_cone(_bm, cap_ends=True, segments=7, radius1=1.0, radius2=0.9, depth=0.07)
for v in _bm.verts: v.co.x *= 1 + 0.25 * math.sin(v.co.y * 3); v.co.z += 0.12 * (v.co.x ** 2 - v.co.y ** 2) * 0.5
_bm.to_mesh(fme); _bm.free(); fme.materials.append(flake_m)
rfl = random.Random(41)
FL0, FL1 = S["flakes"]
for i in range(200):
    o = PT.link(bpy.data.objects.new(f"sflk{i}", fme), denE); s_ = rfl.uniform(0.12, 0.34); o.scale = (s_, s_ * rfl.uniform(0.6, 1.0), s_)
    x, y = rfl.uniform(-7, 7), rfl.uniform(-7, 7); z, nr = U.top_z(DBVH, x, y)
    o.location = (x, y, z + 0.02); o.rotation_euler = (rfl.uniform(-0.4, 0.4), rfl.uniform(-0.4, 0.4), rfl.uniform(0, 6))
for i in range(70):
    o = PT.link(bpy.data.objects.new(f"flk{i}", fme), denE)
    s_ = rfl.uniform(0.18, 0.42); o.scale = (s_, s_ * rfl.uniform(0.6, 1.0), s_)
    x = A_C[0] + rfl.uniform(-2.4, 2.4); y = A_C[1] + rfl.uniform(-2.4, 2.4); z, _ = U.top_z(DBVH, x, y)
    o.rotation_euler = (rfl.uniform(-1, 1), rfl.uniform(-1, 1), rfl.uniform(0, 6))
    t0 = FL0 - 30 + rfl.randint(0, 64)
    U.fall(o, t0, t0 + rfl.randint(20, 32), (x + rfl.uniform(-0.6, 0.6), y + rfl.uniform(-0.6, 0.6), z + rfl.uniform(3.5, 6)), (x, y, z + 0.03), rfl.uniform(-2, 2))
# E. coli: xivchinli tayoqchalar ip ustida emaklaydi
ek = DN.EKit(); EC0, EC1 = S["ecoli"]; ecolis = []
rec = random.Random(51)
for i in range(9):
    x0 = B_C[0] + rec.uniform(-1.4, 1.4); y0 = B_C[1] + rec.uniform(-1.4, 1.4)
    r_, body, flags = DN.build_ecoli(f"ecoli{i}", ek, denE, seed=i)
    s_ = rec.uniform(1.1, 1.6) if i else 2.0
    if i == 0: x0, y0 = B_C
    r_.scale = (s_,) * 3
    a = rec.uniform(0, 6.28); d = Vector((math.cos(a), math.sin(a), 0))
    for f_ in range(EC0 - 10, EC1 + 6, 3):
        t = (f_ - EC0) / 24.0
        p = Vector((x0, y0, 0)) + d * t * 0.35 + Vector((-d.y, d.x, 0)) * 0.05 * math.sin(t * 7 + i)
        z, nr = U.top_z(DBVH, p.x, p.y); p.z = z + 0.05 * s_
        r_.location = p; r_.rotation_euler = M.orient(d + Vector((0, 0, 0)), Vector(nr))
        r_.keyframe_insert("location", frame=f_); r_.keyframe_insert("rotation_euler", frame=f_)
    DN.spin(flags, EC0 - 12, EC1 + 8, turns_per_s=2.5 + rec.random())
    ecolis.append(r_)
# kana tuxumlari (C) — bittasi yoriladi, ichidan 6 oyoqli lichinka chiqadi
egg_m = DN.egg_material(); eggs = []
ege = random.Random(61); EG0, EG1 = S["eggs"]
egg_me = DN.egg_mesh("egg"); egg_me.materials.append(egg_m)
eggb_me = DN.egg_mesh("egg_body_open", part="body"); egg_cap_me = DN.egg_mesh("egg_cap", part="cap")
for me_ in (eggb_me, egg_cap_me): me_.materials.append(egg_m)
EGP = []
for i in range(22):
    a = ege.uniform(0, 6.28); d = 1.1 * math.sqrt(ege.random()) if i else 0.0
    x, y = C_C[0] + math.cos(a) * d, C_C[1] + math.sin(a) * d
    z, nr = U.top_z(DBVH, x, y); s_ = ege.uniform(2.6, 3.2)
    o = PT.link(bpy.data.objects.new(f"egg{i}", egg_me if i else eggb_me), denE)
    o.scale = (s_,) * 3; o.location = (x, y, z + 0.045 * s_ * 0.8)
    o.rotation_euler = M.orient(Vector((math.cos(a + 1.2), math.sin(a + 1.2), ege.uniform(0.2, 0.6))), Vector(nr)); eggs.append(o); EGP.append((x, y, z))
egg0 = eggs[0]; s0 = egg0.scale[0]
# eng ustki egg[0] — qopqoq
cap = PT.link(bpy.data.objects.new("egg_cap", egg_cap_me), egg0)
cap.location = (0, 0.62 * 0.07, 0); cap.rotation_euler = (0, 0, 0)
for k in egg_cap_me.vertices: k.co.y -= 0.62 * 0.07
for f_, rx, ly in ((1, 0, 0.0434), (F_HATCH - 1, 0, 0.0434), (F_HATCH + 3, -75, 0.06), (F_HATCH + 10, -110, 0.05)):
    cap.rotation_euler = (R(rx), 0, 0); cap.location = (0, ly, 0.0 if f_ < F_HATCH else 0.02)
    cap.keyframe_insert("rotation_euler", frame=f_); cap.keyframe_insert("location", frame=f_)
dk = DN.DKit()
larva, lbody = DN.build_dmite("larva", dk, denE, seed=3, pairs=3, scale=1.6)
EGW = Vector(EGP[0]) + Vector((0, 0, 0.1))
bpy.context.view_layer.update()
eg_axis = (egg0.rotation_euler.to_matrix() @ Vector((0, 1, 0))).normalized()
for f_, t in ((1, 0.0), (F_HATCH + 2, 0.0), (F_HATCH + 18, 0.55), (F_HATCH + 30, 0.9), (EG1, 1.6)):
    p_ = Vector(egg0.location) + eg_axis * 0.07 * s0 * (t * 1.4 - 0.25)
    if t > 0.9: p_ = Vector(egg0.location) + eg_axis * 0.07 * s0 * 1.0 + Vector((eg_axis.x, eg_axis.y, 0)).normalized() * (t - 0.9) * 0.9
    z, nr = U.top_z(DBVH, p_.x, p_.y); p_.z = max(p_.z, z + 0.08)
    larva.location = p_; larva.rotation_euler = M.orient(eg_axis if t < 0.9 else Vector((eg_axis.x, eg_axis.y, -0.1)), Vector((0, 0, 1)))
    larva.keyframe_insert("location", frame=f_); larva.keyframe_insert("rotation_euler", frame=f_)
    larva.scale = (1.6 * (0.6 + 0.4 * min(1, t * 1.5)),) * 3; larva.keyframe_insert("scale", frame=f_)
M.walk(larva, F_HATCH + 4, EG1, 9)
adults = []
for i in range(2):
    m_, _ = DN.build_dmite(f"dmite{i}", dk, denE, seed=10 + i, scale=2.4)
    a0 = 1.2 + i * 2.6; ctr = Vector((C_C[0], C_C[1], 0))
    for f_ in range(EG0 - 6, EG1 + 6, 3):
        t = (f_ - EG0) / 24.0; a = a0 + t * (0.35 if i == 0 else -0.3)
        p_ = ctr + Vector((math.cos(a), math.sin(a), 0)) * (1.7 + 0.2 * i)
        z, nr = U.top_z(DBVH, p_.x, p_.y); p_.z = z + 0.09
        fw = Vector((-math.sin(a), math.cos(a), 0)) * (1 if i == 0 else -1)
        m_.location = p_; m_.rotation_euler = M.orient(fw, Vector(nr)); m_.keyframe_insert("location", frame=f_); m_.keyframe_insert("rotation_euler", frame=f_)
    M.walk(m_, EG0 - 6, EG1 + 6, 12); adults.append(m_)
# ter tomchisi (D): ichida bakteriyalar, matoga urilib yoyiladi
DR0, DR1 = S["drop"]
drop_m = bpy.data.materials.new("sweat_drop"); drop_m.use_nodes = True
_N = drop_m.node_tree.nodes; _L = drop_m.node_tree.links; _N.remove(_N["Principled BSDF"])
_tr = _N.new("ShaderNodeBsdfTransparent"); _gl = _N.new("ShaderNodeBsdfGlossy"); _gl.inputs["Roughness"].default_value = 0.02
_lw = _N.new("ShaderNodeLayerWeight"); _lw.inputs["Blend"].default_value = 0.35
_mx = _N.new("ShaderNodeMixShader"); _L.new(_lw.outputs["Fresnel"], _mx.inputs[0]); _L.new(_tr.outputs[0], _mx.inputs[1]); _L.new(_gl.outputs[0], _mx.inputs[2])
_em = _N.new("ShaderNodeEmission"); _em.inputs["Color"].default_value = (1.0, 0.9, 0.6, 1)
_L.new(P.math_n(_N, _L, "MULTIPLY", P.math_n(_N, _L, "POWER", _lw.outputs["Facing"], 3.0), 0.8), _em.inputs["Strength"])
_ad = _N.new("ShaderNodeAddShader"); _L.new(_mx.outputs[0], _ad.inputs[0]); _L.new(_em.outputs[0], _ad.inputs[1]); _L.new(_ad.outputs[0], _N["Material Output"].inputs[0])
drop = sphere("sweat_drop", 0.7, (0, 0, 0), drop_m, sub=4, parent=denE)
DZ, _ = U.top_z(DBVH, *D_C)
for f_, z_, sxy, sz_ in ((1, 6.0, 0.85, 1.15), (DR0, 6.0, 0.85, 1.15), (F_DROP, DZ + 0.75, 0.9, 1.1), (F_DROP + 3, DZ + 0.35, 1.45, 0.45),
                         (F_DROP + 7, DZ + 0.28, 1.6, 0.36), (DR1, DZ + 0.12, 1.75, 0.16)):
    drop.location = (D_C[0], D_C[1], z_); drop.scale = (sxy, sxy, sz_)
    drop.keyframe_insert("location", frame=f_); drop.keyframe_insert("scale", frame=f_)
for fc in fcurves(drop):
    for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
inb = []
for i in range(26):
    o = bk.new(f"dropb{i}", random.choice(("rod", "acne", "coc")), drop)
    a = random.uniform(0, 6.28); rr = random.uniform(0, 0.75); zz = random.uniform(-0.6, 0.6)
    o.location = (math.cos(a) * rr * 0.72, math.sin(a) * rr * 0.72, zz * 0.72); o.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
    o.scale = (1.3, 1.3 / 0.85, 1.3)
    inb.append(o)
for nm, v in (("wx", D_C[0]), ("wy", D_C[1])):
    for m_ in (m_warp, m_weft): val_key(m_, nm, 1, v)
for m_ in (m_warp, m_weft):
    val_key(m_, "wet", 1, 0.0); val_key(m_, "wet", DR0, 1.0); val_key(m_, "wet", DR1 + 1, 0.0)
    val_key(m_, "wr", 1, 0.0); val_key(m_, "wr", F_DROP + 2, 0.0); val_key(m_, "wr", DR1, 1.5)
    for fc in fcurves(m_.node_tree):
        if 'nodes["wet"]' in fc.data_path:
            for k_ in fc.keyframe_points: k_.interpolation = "CONSTANT"
vis(denE, DENR)
vis(drop, [S["drop"]])
vis(larva, [(F_HATCH - 2, EG1)])               # ota (denE) dan keyin

# ======================================================================
# 6) JINSI KESIMI: tolalar to'plami (halqali bo'yash), bakteriyalar va ter pastga singadi
# ======================================================================
XS = V(40.0, 150.0, 0.0)
xsE = empty("xsE", tuple(XS))
fib_me = DN.fiber_meshes(3.0); fib_me.materials.append(mat("fib_tmp", (1, 1, 1)))
fm_out = DN.section_fiber_mat("fib_indigo", (0.04, 0.09, 0.3)); fm_in = DN.section_fiber_mat("fib_white", (0.85, 0.85, 0.82))
fm_weft = DN.section_fiber_mat("fib_weft", (0.75, 0.74, 0.7))
xs_parts = []
for k in range(6):
    xs_parts += DN.yarn_section(f"yarn{k}", (0, -2.0 + k * 0.82, 0.0), 0.38, 0.24, 70, fib_me, fm_out, fm_in, xsE, seed=k)
for k in range(2):                                      # arqoq: ip bo'ylab (Y) kesilgan, ustdan/ostdan o'tadi
    pts = [Vector((-0.35 - k * 0.5, -2.6 + i * 0.1, 0.33 * math.sin((i * 0.1) / 0.82 * math.pi + k * math.pi))) for i in range(53)]
    xs_parts.append(PT.tube(f"weft_x{k}", pts, 0.2, fm_weft, xsE))
XS0, XS1 = S["xsec"]
for m_ in (fm_out, fm_in, fm_weft):
    val_key(m_, "wl", 1, XS.z + 0.6); val_key(m_, "wl", XS0 + 4, XS.z + 0.6); val_key(m_, "wl", XS1, XS.z - 0.32)
xs_b = []
rxs = random.Random(71)
for i in range(70):
    o = bk.new(f"xsb{i}", rxs.choice(("rod", "acne", "coc")), xsE); s_ = rxs.uniform(1.0, 1.6); o.scale = (s_,) * 3
    y = rxs.uniform(-2.3, 2.3); x = rxs.uniform(-0.15, 0.05)
    o.rotation_euler = (rxs.uniform(0, 3), rxs.uniform(0, 3), rxs.uniform(0, 3))
    z0, z1 = rxs.uniform(0.35, 0.55), rxs.uniform(-0.3, 0.25)
    t0 = XS0 + rxs.randint(0, 10)
    key(o, 1, loc=(x, y, z0)); key(o, t0, loc=(x, y, z0)); key(o, XS1, loc=(x, y + rxs.uniform(-0.15, 0.15), z1))
    xs_b.append(o)
vis(xsE, [S["xsec"]])

# ======================================================================
# 7) O'TISH: jinsi (ustda) -> paxta choyshab (pastda); kanalar, bakteriyalar, tuxumlar ko'chib o'tadi
# ======================================================================
TRW = V(80.0, 150.0, 0.0)
trE = empty("trE", tuple(TRW))
cot_m = U.fabric_material("cotton_sheet"); val_key(cot_m, "dirt", 1, 0.2)
cot, CBVH = U.weave("cot", 15.0, 0.9, 0.42, cot_m, trE)
U.fuzz("cfz", CBVH, 50, M.hair_material("fuzz_w", (0.9, 0.88, 0.84), 0.6, trans=0.4), trE, (-7, 7, -7, 7), hair_fn=M.hair)
DZT = 1.08
den2E = empty("den2E", (-3.75, 0, DZT), trE)
den2, D2BVH = DN.twill("dtw2", 7.5, 0.62, 0.36, m_warp, m_weft, den2E, size_y=15.0)
U.scatter_bacteria(bk, "cbg", CBVH, 160, (0.5, 7, -7, 7), trE, seed=5)
U.scatter_bacteria(bk, "d2bg", D2BVH, 200, (-3.7, 3.7, -7, 7), den2E, seed=6)
TR0, TR1 = S["transfer"]
def topD(x, y): z, _ = U.top_z(D2BVH, x + 3.75, y); return z + DZT
def topC(x, y): z, _ = U.top_z(CBVH, x, y); return z
tr_mites = []
for i in range(5):
    y = -1.6 + i * 0.8 + random.uniform(-0.15, 0.15)
    m_, _ = DN.build_dmite(f"trm{i}", dk, trE, seed=20 + i, scale=2.2)
    t_off = i * 9
    pts = [(-2.2 + i * 0.25, topD(-2.2 + i * 0.25, y) + 0.12, (0, 0, 1)), (-0.25, topD(-0.25, y) + 0.12, (0, 0, 1)),
           (0.12, topD(-0.3, y) - 0.15, (1, 0, 0.6)), (0.22, topC(0.3, y) + 0.45, (1, 0, 0.2)), (0.6, topC(0.6, y) + 0.12, (0.3, 0, 1)),
           (2.4, topC(2.4, y) + 0.12, (0, 0, 1))]
    n_ = len(pts) - 1; f_a = TR0 - 10 + t_off; f_b = TR1 + 4
    for f_ in range(f_a, f_b + 1, 2):
        u = (f_ - f_a) / (f_b - f_a) * n_; k_ = min(int(u), n_ - 1); t = u - k_
        x0, z0, n0 = pts[k_]; x1, z1, n1 = pts[k_ + 1]
        p_ = Vector((x0 + (x1 - x0) * t, y, z0 + (z1 - z0) * t)); up = Vector(n0).lerp(Vector(n1), t).normalized()
        fw = Vector((x1 - x0, 0, z1 - z0)).normalized()
        m_.location = p_; m_.rotation_euler = M.orient(fw, up); m_.keyframe_insert("location", frame=f_); m_.keyframe_insert("rotation_euler", frame=f_)
    M.walk(m_, f_a, f_b, 14); tr_mites.append(m_)
rtr = random.Random(81)
for i in range(30):
    kind = rtr.choice(("rod", "acne", "coc", "egg"))
    if kind == "egg":
        o = PT.link(bpy.data.objects.new(f"tregg{i}", egg_me), trE); o.scale = (2.6,) * 3
    else:
        o = bk.new(f"trb{i}", kind, trE); o.scale = (1.3,) * 3
    y = rtr.uniform(-2.5, 2.5); x0 = rtr.uniform(-0.6, -0.1); t0 = TR0 + rtr.randint(0, 70)
    x1 = rtr.uniform(0.3, 1.6)
    o.location = (x0, y, topD(x0, y) + 0.05); o.keyframe_insert("location", frame=1)
    U.fall(o, t0, t0 + rtr.randint(14, 22), (x0 + 0.1, y, topD(x0, y) + 0.06), (x1, y + rtr.uniform(-0.2, 0.2), topC(x1, y) + 0.05), rtr.uniform(-2, 2))
vis(trE, [S["transfer"]])

# ======================================================================
# 8) YOSTIQ MIKRO (tun): paxta jild + ulkan yonoq terisi (issiq) + kanalar unga qarab emaklaydi
# ======================================================================
PLW = V(120.0, 150.0, 0.0)
plE = empty("plE", tuple(PLW))
pcot_m = U.fabric_material("pillow_cot"); val_key(pcot_m, "dirt", 1, 0.6)
pcot, PBVH = U.weave("pcot", 15.0, 0.9, 0.42, pcot_m, plE)
U.scatter_bacteria(bk, "pbg", PBVH, 420, (-7, 7, -7, 7), plE, seed=9)
SKP = [(rx, ry, 0.2, 0.4) for rx, ry in ((-1.2, -0.6), (0.8, 1.1), (1.6, -1.4), (-0.4, 1.8))]
SKa = M.Skin(7.0, SKP, seed=4)
skin_m = M.skin_micro_material()
gsk = empty("gsk", (2.6, 0.0, 2.9), plE); gsk.rotation_euler = (R(180), R(-18), 0)
M.skin_surface("gsurf", SKa, 0.045, skin_m, gsk).modifiers.new("so", "SOLIDIFY").thickness = 0.4
RV0, RV1 = S["revealm"]
pl_mites = []
for i in range(6):
    m_, _ = DN.build_dmite(f"plm{i}", dk, plE, seed=40 + i, scale=2.4)
    y = -1.8 + i * 0.7; xa = -2.6 + random.uniform(-0.4, 0.4)
    for f_ in range(RV0 - 8, RV1 + 6, 2):
        t = (f_ - RV0) / 24.0; x_ = xa + t * 0.9
        z, nr = U.top_z(PBVH, x_, y)
        m_.location = (x_, y + 0.1 * math.sin(t * 3 + i), z + 0.1); m_.rotation_euler = M.orient(Vector((1, 0.1 * math.cos(t * 3 + i), 0)), Vector(nr))
        m_.keyframe_insert("location", frame=f_); m_.keyframe_insert("rotation_euler", frame=f_)
    M.walk(m_, RV0 - 8, RV1 + 6, 10); pl_mites.append(m_)
vis(plE, [S["revealm"]])

# ======================================================================
# 9) ISSIQLIK KAMERASI (tun): xona va Brian materiallariga "th" aralashmasi
# ======================================================================
TH_R = [(F_TH, S["night"][1])]
def thermalize(m, heat):
    if not m or not m.use_nodes or m.get("thermal"): return
    m["thermal"] = 1
    N = m.node_tree.nodes; L = m.node_tree.links
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    h = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", 0.55, P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 0.45)), heat),
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
    val_key(m, "th", 1, 0.0)
    for a, b in TH_R: val_key(m, "th", a, 1.0); val_key(m, "th", b + 1, 0.0)
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
for m in mats_of(bmeshes): thermalize(m, 0.62 if "hair" in m.name.lower() else 1.0)
thermalize(pillow_m, 0.85); thermalize(blanket_m, 0.62)
for m in mats_of([bed_grp]): thermalize(m, 0.2)
for m in mats_of(apt_objs): thermalize(m, 0.05)

# ======================================================================
# 10) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.01):
    t = empty(name + "_t"); path(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path(c, pts)
    return c
# 1 KIRISH: past burchak (18 mm), eshik tomon push-in
E0, E1 = S["enter"]
c = abs_cam("enter", [(E0, V(0.55, 0.9, 0.22)), (E1, V(0.45, 0.25, 0.3))], [(E0, V(0.35, Y0 - 0.2, 1.05)), (E1, V(0.32, -0.6, 1.0))], 18, 4.0)
shake(c, 30, 40, 0.012, seed=1)
# 2 JINSI: shimga crash zoom (35 -> 85 mm)
J0, J1 = S["jeans"]
TH_ = wp(thighM, J0 + 30)
c = abs_cam("jeans", [(J0, TH_ + V(0.9, -1.9, 0.45)), (J0 + 6, TH_ + V(0.5, -1.15, 0.2)), (J1, TH_ + V(0.45, -1.05, 0.15))],
            [(J0, TH_ + V(0, 0, 0.15)), (J0 + 6, TH_ + V(0, 0, 0.0)), (J1, TH_ + V(0, 0, -0.03))], 30, 2.2)
lens_keys(c, [(J0, 22), (J0 + 6, 40), (J1, 44)]); shake(c, J0 + 5, J0 + 14, 0.012, seed=2); c.data.dof.aperture_fstop = 5.6
c.data.dof.focus_object = thighM
# 3 YIQILISH: keng (28 mm), karavot oyog'idan dolly + ko'tarilish
F0, F1 = S["flop"]
HL = wp(hipsE, F0 + 30)
c = abs_cam("flop", [(F0, HL + V(1.9, -2.0, 0.15)), (F1, HL + V(1.5, -1.5, 0.85))], [(F0, HL + V(-0.1, 0.25, 0.1)), (F1, HL + V(-0.1, 0.3, 0.0))], 26, 5.6)
shake(c, F0 + 18, F0 + 28, 0.02, seed=3)
# 4a MORF: tepadan, aylanma (ko'rpa avtobus matosiga aylanadi)
MO0, MO1 = S["morph"]
c = shot_cam("morph", (0, 0, 0), None, 30, 5.6, focus=hipsE, clip=0.01)
for f_ in range(MO0, MO1 + 1, 2):
    t = (f_ - MO0) / (MO1 - MO0); a = R(-90 + 70 * t)
    key(c, f_, loc=tuple(HIPS_LIE + V(0.12 * math.cos(a), 0.12 * math.sin(a) - 0.35, 1.35 - 0.55 * t)), rot=(0, 0, math.degrees(a) + 90 + 180))
val_key(throw_m, "mq", 1, 0.0); val_key(throw_m, "mq", MO0 + 8, 0.0); val_key(throw_m, "mq", MO1 - 6, 1.0); val_key(throw_m, "mq", MO1 + 1, 0.0)
for fc in fcurves(throw_m.node_tree):
    for k_ in fc.keyframe_points:
        if int(k_.co.x) == MO1 + 1 or int(k_.co.x) == MO1 - 6: k_.interpolation = "CONSTANT"
c.rotation_euler = (0, 0, 0)
for fc in fcurves(c):
    if fc.data_path == "rotation_euler" and fc.array_index in (0, 1): fc.keyframe_points.clear()
# 4b AVTOBUS (tepadan o'rindiq -> yuqoriga, yo'lovchilar ochiladi)
BU0, BU1 = S["busup"]
SEAT_TOP = Vector((B_SEAT.x + 0.02, B_SEAT.y, SEAT_Z + 0.01))
c = abs_cam("busup", [(BU0, SEAT_TOP + V(0.0, 0.0, 0.8)), (BU0 + 14, SEAT_TOP + V(-0.3, 0.05, 1.45)), (BU1, SEAT_TOP + V(-1.6, 0.15, 1.65))],
            [(BU0, SEAT_TOP + V(0.01, 0.0, 0)), (BU0 + 14, SEAT_TOP + V(0.4, 0.2, 0)), (BU1, SEAT_TOP + V(1.4, 0.45, 0.5))], 22, 5.6)
# 5 AVTOBUS: yo'lak bo'ylab tracking (24 mm)
c = abs_cam("bus", [(B0, B_SEAT + V(2.4, 0.95, 0.55)), (B1, B_SEAT + V(1.4, 0.85, 0.5))], [(B0, B_SEAT + V(0, 0, 0.25)), (B1, B_SEAT + V(0, 0, 0.1))], 22, 4.0)
shake(c, B0, B1, 0.006, seed=5, decay=False)
# 6 TAKSI: o'rindiq darajasida
TS_ = TX + V(0.0, -0.32, TX_SEAT_Z + 0.1)
c = abs_cam("taxi", [(T0_, TS_ + V(0.55, 0.95, 0.12)), (S["taxi"][1], TS_ + V(0.4, 0.75, 0.08))], [(T0_, TS_ + V(0, 0, 0.08)), (S["taxi"][1], TS_ + V(0, 0, 0.0))], 24, 2.8)
shake(c, T0_ + 4, T0_ + 12, 0.02, seed=6)
# 7 KAFE: past burchak
CS_ = CHAIR + V(0, 0.06, 0.6)
c = abs_cam("cafe", [(C0_, CS_ + V(1.0, -1.25, -0.35)), (S["cafe"][1], CS_ + V(0.8, -1.05, -0.3))], [(C0_, CS_ + V(0, 0, 0.1)), (S["cafe"][1], CS_ + V(0, 0, 0.05))], 22, 2.8)
shake(c, C0_ + 6, C0_ + 14, 0.02, seed=7)
# 8 KASALXONA: past burchak 18 mm, yonlama siljish
HS_ = H_SEAT
c = abs_cam("hosp", [(H0_, HS_ + V(1.6, -1.8, -0.4)), (S["hosp"][1], HS_ + V(0.7, -1.7, -0.38))], [(H0_, HS_ + V(-0.4, 0, 0.3)), (S["hosp"][1], HS_ + V(-0.5, 0, 0.25))], 18, 4.0)
# 9a SHO'NG'ISH: shimga crash zoom
DV0, DV1 = S["dive"]
TH2 = wp(thighM, DV0 + 8)
c = abs_cam("dive", [(DV0, TH2 + V(0.5, -1.3, 0.3)), (DV1, TH2 + V(0.06, -0.14, 0.03))], [(DV0, TH2), (DV1, TH2)], 35, 4.0, clip=0.003)
lens_keys(c, [(DV0, 35), (DV1, 90)])
c.data.dof.focus_object = thighM
# 9b MIKRO: yuqoridan tushish
DM0, DM1 = S["divem"]
c = abs_cam("divem", [(DM0, DP(0.3, -0.8, 13.0)), (DM1, DP(0.5, -2.6, 3.0))], [(DM0, DP(0.0, 0.0, 0.0)), (DM1, DP(0.3, 0.0, 0.0))], 24, 8.0)
# 10 qipiqlar yog'iladi: tepadan pastga + aylanma
AP_ = DP(*A_C)
c = abs_cam("flakes", [(FL0, AP_ + V(0.8, -3.4, 3.8)), (FL1, AP_ + V(1.5, -2.6, 1.6))], [(FL0, AP_ + V(0, 0, 0.8)), (FL1, AP_ + V(0, 0, 0.2))], 24, 4.0)
# 11 E. coli: yaqin, yonlama
BP_ = DP(*B_C)
c = abs_cam("ecoli", [(EC0, BP_ + V(-1.3, -1.7, 0.95)), (EC1, BP_ + V(-0.5, -1.9, 0.8))], [(EC0, BP_ + V(0, 0, 0.15)), (EC1, BP_ + V(0.25, 0.05, 0.15))], 32, 4.0)
# 12 tuxumlar: past burchakdan push-in, yorilishda silkinish
CPc = DP(*C_C)
c = abs_cam("eggs", [(EG0, CPc + V(-1.1, -2.6, 1.5)), (F_HATCH - 2, CPc + V(-0.5, -1.5, 1.05)), (EG1, CPc + V(-0.3, -1.2, 1.0))],
            [(EG0, CPc + V(0, 0, 0.25)), (F_HATCH - 2, CPc + V(0, 0, 0.25)), (EG1, CPc + V(0.25, 0.3, 0.2))], 28, 5.6)
shake(c, F_HATCH, F_HATCH + 14, 0.04, seed=12)
# 13 KUN BO'YI: avtobusda yonlama dolly (timelapse)
c = abs_cam("allday", [(AD0, B_SEAT + V(1.9, 1.05, 0.7)), (AD1, B_SEAT + V(0.9, 1.0, 0.45))], [(AD0, B_SEAT + V(-0.3, 0, 0.25)), (AD1, B_SEAT + V(-0.1, 0, 0.3))], 24, 4.0)
# 14 ter tomchisi: mikro crash zoom
DPd = DP(*D_C)
c = abs_cam("drop", [(DR0, DPd + V(0.3, -4.2, 2.2)), (F_DROP + 1, DPd + V(0.2, -2.6, 1.2)), (DR1, DPd + V(0.2, -2.3, 1.05))],
            [(DR0, DPd + V(0, 0, 1.6)), (F_DROP + 1, DPd + V(0, 0, 0.4)), (DR1, DPd + V(0, 0, 0.25))], 26, 5.6)
shake(c, F_DROP, F_DROP + 10, 0.05, seed=14)
# 15 kesim: push-in
c = abs_cam("xsec", [(XS0, XS + V(3.2, -1.0, 0.9)), (XS1, XS + V(1.9, -0.35, 0.35))], [(XS0, XS + V(0, 0, 0.0)), (XS1, XS + V(0, 0.1, -0.05))], 24, 8.0)
# 16 choyshabga o'tirish: choyshab darajasida, yonlama
SB0, SB1 = S["sitbed"]
c = abs_cam("sitbed", [(SB0, HIPS_SIT + V(1.0, -1.25, MTOP + 0.06)), (SB1, HIPS_SIT + V(0.8, -1.0, MTOP + 0.06))],
            [(SB0, HIPS_SIT + V(-0.05, 0.05, MTOP + 0.1)), (SB1, HIPS_SIT + V(-0.1, 0.05, MTOP + 0.05))], 20, 2.8)
shake(c, SB0 + 34, SB0 + 46, 0.015, seed=16)
# 17 o'tish: yonlama ergashish
c = abs_cam("transfer", [(TR0, TRW + V(-1.2, -3.6, 1.6)), (TR1, TRW + V(1.6, -3.4, 1.1))], [(TR0, TRW + V(-0.6, 0, 0.9)), (TR1, TRW + V(1.0, 0, 0.5))], 22, 5.6)
# 18 tun: tepadan aylanma -> yuzga push-in (issiqlik kamerasi)
HDN = wp(headE, N0 + 20)
c = abs_cam("night", [(N0, HDN + V(1.6, -1.8, 1.6)), (F_TH - 1, HDN + V(1.4, -1.2, 1.3)), (F_TH, HDN + V(1.0, -0.9, 0.9)), (N1, HDN + V(0.55, -0.45, 0.45))],
            [(N0, HDN + V(0.0, -0.8, -0.1)), (F_TH - 1, HDN + V(0, -0.7, -0.1)), (F_TH, HDN + V(0, -0.5, -0.05)), (N1, HDN + V(0, -0.1, 0))], 18, 4.0)
lens_keys(c, [(N0, 18), (F_TH - 1, 18), (F_TH, 24), (N1, 32)])
# 19a yostiq mikro: kana yaqinidan tez orqaga
PLc = PLW + V(-1.6, 0, 0.3)
c = abs_cam("revealm", [(RV0, PLW + V(-2.3, -1.3, 0.55)), (RV1, PLW + V(-3.0, -5.2, 1.8))], [(RV0, PLW + V(-2.1, -0.4, 0.15)), (RV1, PLW + V(0.2, 0, 0.9))], 26, 5.6)
# 19b xona: yuzdan butun xonaga tez pull-out
RW0, RW1 = S["revealw"]
c = abs_cam("revealw", [(RW0, HDN + V(0.35, -0.3, 0.3)), (RW0 + 8, HDN + V(1.2, -1.4, 1.2)), (RW1, HDN + V(3.2, -3.4, 1.95))],
            [(RW0, HDN), (RW1, HDN + V(0, -0.7, -0.2))], 20, 5.6)
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        if fc.data_path == "location":
            for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
for f_, n in SHOTS:
    sc.timeline_markers.new(n, frame=f_).camera = CAMS[n]
sc.camera = CAMS["enter"]
# ekran yozuvlari (kameraga bog'langan, chap-yuqorida emas — markazda yuqorida)
ov_m = mat("ov_txt", (1, 1, 1), 0.5, emit=5.0)
ov_y = mat("ov_yel", (1.0, 0.8, 0.1), 0.5, emit=5.0)
def label(cam_name, body, lens, ranges, m=ov_m, size=0.042, y_frac=0.62):
    d = 0.12; half = d * 12.0 / lens
    t = text("lbl_" + cam_name, body, size * half / 0.225, (0, half * y_frac, -d), (0, 0, 0), m, parent=CAMS[cam_name], extrude=0.002)
    f0 = ranges[0][0]
    t.scale = (0.01,) * 3; t.keyframe_insert("scale", frame=f0); t.scale = (1.2,) * 3; t.keyframe_insert("scale", frame=f0 + 3)
    t.scale = (1.0,) * 3; t.keyframe_insert("scale", frame=f0 + 5)
    vis(t, ranges); return t
# Yozuvlar (AVTOBUS, TAKSI, KAFE, KASALXONA, 1000×, soat) montajda ffmpeg drawtext bilan qo'yiladi:
# kameraga bog'langan 3D matn DOF'da xiralashib, ustunlar orqasida qolib ketdi.

# ======================================================================
# 11) YORUG'LIK, FON
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
WORLD = {"eve": (0.35, (0.0, 0.0, 0.0), 0.0), "day": (1.0, (0, 0, 0), 0.0), "night": (0.0, (0.002, 0.004, 0.012), 1.0),
         "in": (0.15, (0.0, 0.0, 0.0), 0.0), "den": (0.0, (0.03, 0.05, 0.12), 1.0), "cot": (0.0, (0.16, 0.2, 0.28), 1.0),
         "xs": (0.0, (0.01, 0.015, 0.03), 1.0), "warm": (0.0, (0.12, 0.05, 0.03), 1.0)}
def world_of(n):
    if n in ("enter", "jeans", "flop", "morph", "sitbed"): return "eve"
    if n in ("busup", "bus", "allday", "taxi"): return "day"
    if n in ("night", "revealw"): return "night"
    if n in ("cafe", "hosp", "dive"): return "in"
    if n in ("divem", "flakes", "ecoli", "eggs", "drop"): return "den"
    return {"xsec": "xs", "transfer": "cot", "revealm": "warm"}[n]
for f_, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f_)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f_)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f_)
interp(w.node_tree, "CONSTANT")
def sun(name, rot, col, strength, ranges, angle=2.0):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN")); sc.collection.objects.link(l)
    l.rotation_euler = [R(a) for a in rot]; l.data.color = col; l.data.angle = R(angle)
    for f_, e in lights_for(ranges, strength): l.data.energy = e; l.data.keyframe_insert("energy", frame=f_)
    interp(l.data, "CONSTANT"); return l
# kechki quyosh: o'ng derazadan past, iliq
sun("sun_eve", (0, 72, 12), (1.0, 0.62, 0.35), 4.5, APT_EVE)
# kunduzgi quyosh (avtobus, taksi): timelapse'da aylanadi
sb = sun("sun_day", (0, 50, 75), (1.0, 0.92, 0.82), 3.5, BUSR + [S["taxi"]])
for f_, rz in ((AD0, 75), (AD1, -60)):
    sb.rotation_euler.z = R(rz); sb.keyframe_insert("rotation_euler", index=2, frame=f_)
for fc in fcurves(sb):
    for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
TGT = lambda n, p: empty(n, tuple(p))
# kvartira (kechqurun): shift lampasi + iliq to'ldiruvchi
AT = TGT("aptT", (BED.x + 0.6, FOOT_Y + 0.3, 0.8))
area("apt_fill", (1.0, -0.6, 2.55), 2.0, (1.0, 0.85, 0.7), lights_for(APT_EVE, 70.0), target=AT)
area("apt_win", (X1 - 0.3, -0.45, 1.6), 1.4, (1.0, 0.7, 0.45), lights_for(APT_EVE, 60.0), target=AT)
area("hall_l", (0.3, Y0 - 1.2, 2.5), 1.0, (1.0, 0.75, 0.45), lights_for(APT_EVE, 120.0), target=TGT("hallT", (0.3, Y0 - 1.2, 0)))
area("apt_rim", (BED.x - 0.5, Y1 - 0.4, 2.0), 1.2, (1.0, 0.8, 0.6), lights_for(APT_EVE, 40.0), target=AT)
# kvartira (tun): oy nuri + tungi chiroq
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = headE
point("bed_bulb", tuple(BL + V(0, 0, 0.36)), 0.04, (1.0, 0.68, 0.36), lights_for(APT_NIGHT, 35.0))
area("moon_key", (X1 - 0.5, -0.5, 2.1), 1.2, (0.45, 0.6, 1.0), lights_for(APT_NIGHT, 110.0), target=FT)
area("moon_room", (0.0, 0.5, 2.6), 2.5, (0.4, 0.5, 0.9), lights_for(APT_NIGHT, 45.0), target=TGT("roomT", (BED.x, BED.y, 0.4)))
area("moon_fill", (BED.x + 1.5, BED.y - 2.0, 1.4), 1.5, (0.4, 0.5, 0.9), lights_for(APT_NIGHT, 14.0), target=FT)
shade_e = shade_m.node_tree.nodes["Principled BSDF"]; shade_e.inputs["Emission Color"].default_value = (1.0, 0.75, 0.45, 1)
for f_, e in ((1, 0.0), (N0, 2.5), (F_TH, 0.0), (S["revealw"][0], 2.5)):
    shade_e.inputs["Emission Strength"].default_value = e; shade_e.inputs["Emission Strength"].keyframe_insert("default_value", frame=f_)
interp(shade_m.node_tree, "CONSTANT")
# avtobus: lyuminestsent
BT = TGT("busT", tuple(B_SEAT + V(0, 0, 0.3)))
for k in range(3):
    area(f"bus_l{k}", tuple(BUS + V(-3 + k * 3, 0, BH_ - 0.1)), 1.2, (0.9, 0.95, 1.0), lights_for(BUSR, 90.0), target=TGT(f"busT{k}", tuple(BUS + V(-3 + k * 3, 0, 0))))
area("bus_key", tuple(B_SEAT + V(1.0, 0.9, 1.2)), 0.8, (1.0, 0.95, 0.9), lights_for(BUSR, 25.0), target=BT)
# taksi
TT = TGT("taxiT", tuple(TS_))
area("tx_key", tuple(TX + V(0.5, 0.6, 1.1)), 0.6, (1.0, 0.92, 0.8), lights_for([S["taxi"]], 40.0), target=TT)
area("tx_win", tuple(TX + V(0.2, -1.4, 0.95)), 1.0, (1.0, 0.85, 0.55), lights_for([S["taxi"]], 80.0), target=TT)
# kafe
CT = TGT("cafeT", tuple(CS_))
area("cf_key", tuple(CF + V(0.9, -1.4, 2.2)), 1.0, (1.0, 0.75, 0.45), lights_for([S["cafe"]], 110.0), target=CT)
area("cf_rim", tuple(CF + V(-1.0, 1.0, 1.8)), 0.8, (1.0, 0.6, 0.35), lights_for([S["cafe"]], 60.0), target=CT)
# kasalxona
HT = TGT("hospT", tuple(HS_))
area("hp_ceil", tuple(HP + V(0.3, -0.8, 2.8)), 1.6, (0.85, 1.0, 0.92), lights_for(HOSPR, 200.0), target=HT)
area("hp_fill", tuple(HP + V(1.8, -2.0, 1.2)), 1.2, (0.8, 0.95, 1.0), lights_for(HOSPR, 50.0), target=HT)
# mikro dunyolar: iliq asosiy, ko'k chet nuri
def fab_lights(tag, c, ranges, key_e, rim_e, low=False, kc=(1.0, 0.9, 0.78), rc_=(0.5, 0.7, 1.0)):
    t = empty(f"fT_{tag}", tuple(c)); zk = 1.4 if low else 4.0
    area(f"fk_{tag}", tuple(c + V(-3.0, -3.5, zk)), 3.0, kc, lights_for(ranges, key_e), target=t)
    area(f"fr_{tag}", tuple(c + V(3.5, 3.0, zk * 0.5)), 2.5, rc_, lights_for(ranges, rim_e), target=t)
    area(f"ff_{tag}", tuple(c + V(2.5, -3.0, 1.0)), 2.5, (1.0, 0.85, 0.75), lights_for(ranges, key_e * 0.3), target=t)
fab_lights("dv", DP(0, 0), [S["divem"]], 900.0, 500.0)
fab_lights("A", AP_, [S["flakes"]], 520.0, 450.0)
fab_lights("B", BP_, [S["ecoli"]], 420.0, 500.0, low=True)
fab_lights("C", CPc, [S["eggs"]], 420.0, 520.0, low=True)
fab_lights("D", DPd, [S["drop"]], 480.0, 500.0)
fab_lights("X", XS, [S["xsec"]], 380.0, 420.0)
fab_lights("T", TRW + V(0, 0, 0.6), [S["transfer"]], 480.0, 420.0, low=True)
fab_lights("P", PLc, [S["revealm"]], 380.0, 300.0, low=True, kc=(1.0, 0.55, 0.3), rc_=(0.4, 0.55, 1.0))
area("P_skin", tuple(PLW + V(1.8, -1.5, 0.8)), 1.5, (1.0, 0.35, 0.15), lights_for([S["revealm"]], 160.0), target=gsk)

# ======================================================================
# 12) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
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
