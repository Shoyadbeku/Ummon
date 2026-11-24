# Og'iz chayqash suyuqligini yutib yuborsangiz nima bo'ladi? — Zack D. Films uslubida 31.6 s video.
# Asos: zack_test/scene3.py + mixchar.py + kiprik/kiprik.py (lib.py, organs.py) + burish/parts.py
# Render: OUT=/tmp/claude-0/frames_ch/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/chayqash/chayqash.py --render
# Sinov: FRAMES=20,60,110,160,240 PCT=35 ; oraliq: RANGE=1,200
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__)); ZT = os.path.dirname(HERE)
for p in (ZT, os.path.join(ZT, "kiprik"), os.path.join(ZT, "burish"), HERE): sys.path.insert(0, p)
from mathutils import Vector, Matrix, Quaternion, Euler
bpy.ops.wm.read_factory_settings(use_empty=True)
import mixchar as mc
import lib as U
import organs as O
import parts as P
from lib import R, key, interp, vis, mat, bsdf, box, cyl, sphere, plane, empty, camera, shake, lens_keys, area, lights_for

OUT = os.environ.get("OUT", "/tmp/claude-0/frames_ch/")
PH = U.PH
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 760
sc.frame_start, sc.frame_end = 1, END
rnd = random.Random(7)

# ---------------- kadrlar (ovoz so'zlariga bog'langan: kadr = t*24+1) ----------------
SHOTS = [(1, "hook"), (37, "gulp"), (88, "xray"), (141, "stomach"), (190, "bact"), (284, "mol"), (347, "dizzy"),
         (418, "gut"), (463, "child"), (514, "xchild"), (588, "blood"), (681, "floor")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
BATH = ["hook", "gulp", "dizzy", "gut", "child", "floor"]
XRS = ["xray", "xchild"]

XR = Vector((-40.0, 0, 0)); XR2 = Vector((-50.0, 0, 0)); SI = Vector((40.0, 0, 0)); BA = Vector((80.0, 0, 0))
MO = Vector((120.0, 0, 0)); BV = Vector((160.0, 0, 0))

# ======================================================================
# MATERIALLAR
# ======================================================================
def liquid_mat(name="mouthwash", col=(0.05, 0.85, 0.35), dens=14.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.45, 1.0, 0.6, 1); b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.36; b.inputs["Roughness"].default_value = 0.02
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    va = N.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (*col, 1); va.inputs["Density"].default_value = dens
    L.new(va.outputs[0], N["Material Output"].inputs["Volume"])
    return m

M_liq = liquid_mat(col=(0.02, 0.8, 0.22), dens=70.0)
M_plastic = mat("clear_plastic", (0.95, 0.97, 1.0), 0.06); bsdf(M_plastic).inputs["Transmission Weight"].default_value = 1.0
bsdf(M_plastic).inputs["IOR"].default_value = 1.45
M_cap = mat("cap_white", (0.92, 0.93, 0.95), 0.35, coat=0.3)
M_chrome = mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0)
M_cer = mat("ceramic", (0.93, 0.93, 0.92), 0.12, coat=0.8)

def label_mat():
    m = bpy.data.materials.new("label"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["UV"], sep.inputs[0])
    # oq fon, o'rtasida ko'k-yashil to'lqinli chiziq, tepada ko'k blok (matnsiz)
    wv = U._m(N, L, "SINE", U._m(N, L, "MULTIPLY", sep.outputs[0], 9.0))
    band = U._m(N, L, "LESS_THAN", U._m(N, L, "ABSOLUTE", U._m(N, L, "SUBTRACT", sep.outputs[1], U._m(N, L, "ADD", 0.45, U._m(N, L, "MULTIPLY", wv, 0.05)))), 0.09)
    top = U._m(N, L, "GREATER_THAN", sep.outputs[1], 0.78)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(band, c1.inputs["Factor"])
    c1.inputs[6].default_value = (0.95, 0.96, 0.97, 1); c1.inputs[7].default_value = (0.0, 0.55, 0.35, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(top, c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.02, 0.12, 0.45, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.3
    return m
M_label = label_mat()

def bevel_box(name, size, loc, m, parent=None, w=0.012, seg=4):
    o = box(name, size, loc, m, parent=parent)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = w; bv.segments = seg
    for p in o.data.polygons: p.use_smooth = True
    o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o

def make_bottle(name, parent, cap_on=True):
    """og'iz chayqash shishasi (brendsiz): yashil suyuqlik, shaffof plastik, oq qopqoq, oldida yorliq. Asos z=0."""
    root = empty(name, (0, 0, 0), parent)
    bevel_box(name + "_body", (0.072, 0.048, 0.165), (0, 0, 0.0825), M_liq, parent=root, w=0.016)
    sh = U.uvsphere(name + "_shoulder", 1.0, (0, 0, 0.163), M_liq, scale=(0.034, 0.022, 0.022), parent=root)
    cyl(name + "_neck", 0.0135, 0.03, (0, 0, 0.185), M_plastic, parent=root)
    lb = plane(name + "_label", (0.06, 0.075), (0, -0.0245, 0.07), M_label, rot=(90, 0, 0), parent=root)
    if cap_on:
        cyl(name + "_cap", 0.018, 0.026, (0, 0, 0.21), M_cap, parent=root, verts=40)
    return root

def make_cup(name, parent, fill=0.6, r=0.019, h=0.028):
    """qopqoq-o'lchov stakanchasi ichida yashil suyuqlik"""
    root = empty(name, (0, 0, 0), parent)
    c = cyl(name + "_shell", r, h, (0, 0, h / 2), M_plastic, parent=root, verts=40)
    so = c.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.0015
    # ichi bo'sh bo'lishi uchun tepa qopqog'ini olib tashlaymiz
    me = c.data
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    for f_ in [f_ for f_ in bm.faces if f_.normal.z > 0.9]: bm.faces.remove(f_)
    bm.to_mesh(me); bm.free()
    cyl(name + "_liq", r - 0.0016, h * fill, (0, 0, h * fill / 2 + 0.001), M_liq, parent=root, verts=40)
    return root

# ======================================================================
# 1) HAMMOM (dunyo markazi): x -1.6..1.6, y -1.6..1.3, shift 2.6
# ======================================================================
broot = empty("bathroom", (0, 0, 0))
M_wall = U.pbr("tiles_wall", "long_white_tiles", 0.9)
M_floor = U.pbr("tiles_floor", "large_grey_tiles", 0.45)
M_marble = U.pbr("marble_top", "marble_01", 0.8)
plane("b_floor", (3.2, 2.9), (0, -0.15, 0), M_floor, parent=broot)
plane("b_ceil", (3.2, 2.9), (0, -0.15, 2.6), mat("b_ceil", (0.92, 0.92, 0.9), 0.9), rot=(180, 0, 0), parent=broot)
plane("b_n", (3.2, 2.6), (0, 1.3, 1.3), M_wall, rot=(90, 0, 0), parent=broot)
plane("b_s", (3.2, 2.6), (0, -1.6, 1.3), M_wall, rot=(90, 0, 0), parent=broot)
plane("b_w", (2.9, 2.6), (-1.6, -0.15, 1.3), M_wall, rot=(90, 0, 90), parent=broot)
plane("b_e", (2.9, 2.6), (1.6, -0.15, 1.3), M_wall, rot=(90, 0, 90), parent=broot)
# eshik (janubiy devor)
M_wood = mat("door_wood", (0.42, 0.27, 0.16), 0.45)
box("door", (0.85, 0.05, 2.05), (0.9, -1.575, 1.025), M_wood, parent=broot)
cyl("door_knob", 0.025, 0.06, (0.55, -1.53, 1.0), M_chrome, rot=(90, 0, 0), parent=broot)
# peshtaxta (shimoliy devor bo'ylab): tepa z = 0.86
CT = 0.86
M_cab = mat("cabinet", (0.86, 0.86, 0.84), 0.35, coat=0.3)
bevel_box("cabinet", (1.8, 0.5, 0.8), (-0.1, 1.04, 0.42), M_cab, parent=broot, w=0.01)
box("cab_kick", (1.76, 0.46, 0.06), (-0.1, 1.06, 0.03), mat("kick", (0.2, 0.2, 0.2), 0.6), parent=broot)
for i, x in enumerate((-0.55, 0.35)):
    box(f"cab_gap{i}", (0.004, 0.005, 0.7), (x, 0.787, 0.43), mat("gap", (0.1, 0.1, 0.1), 0.8), parent=broot)
    cyl(f"cab_handle{i}", 0.006, 0.14, (x + 0.06, 0.775, 0.7), M_chrome, parent=broot)
bevel_box("counter_top", (1.86, 0.56, 0.04), (-0.1, 1.02, CT - 0.02), M_marble, parent=broot, w=0.006)
# chanoq (lavabo): yarim sfera
import bmesh
SINK = Vector((-0.45, 1.02, CT))
sk = U.uvsphere("sink", 1.0, (0, 0, 0), M_cer, seg=48, ring=24, parent=broot)
bm = bmesh.new(); bm.from_mesh(sk.data)
for v in [v for v in bm.verts if v.co.z > 0.001]: bm.verts.remove(v)
bm.to_mesh(sk.data); bm.free()
sk.scale = (0.21, 0.16, 0.12); sk.location = SINK + Vector((0, 0, 0.12))
so = sk.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.08; sk.modifiers.new("sub", "SUBSURF").levels = 1
cyl("faucet", 0.013, 0.24, tuple(SINK + Vector((0, 0.2, 0.12))), M_chrome, parent=broot)
fs_ = cyl("faucet_spout", 0.011, 0.14, tuple(SINK + Vector((0, 0.135, 0.235))), M_chrome, rot=(90, 0, 0), parent=broot)
cyl("faucet_lever", 0.007, 0.07, tuple(SINK + Vector((0.035, 0.2, 0.25))), M_chrome, rot=(0, 60, 0), parent=broot)
# ko'zgu
M_mirror = mat("mirror", (0.92, 0.94, 0.95), 0.015, metal=1.0)
box("mirror", (1.3, 0.02, 0.95), (-0.2, 1.285, 1.62), M_mirror, parent=broot)
box("mirror_frame", (1.34, 0.015, 0.99), (-0.2, 1.293, 1.62), mat("mframe", (0.1, 0.1, 0.1), 0.4), parent=broot)
M_lamp = mat("vanity_lamp", (1, 0.95, 0.85), 0.3, emit=12.0, emit_col=(1, 0.93, 0.8))
box("vanity_lamp", (0.9, 0.06, 0.05), (-0.2, 1.25, 2.17), M_lamp, parent=broot)
# tish cho'tkasi stakani, sovun, rezina o'rdakcha
M_glass = mat("glass", (0.95, 0.98, 1.0), 0.03); bsdf(M_glass).inputs["Transmission Weight"].default_value = 1.0
tc_ = cyl("tb_cup", 0.034, 0.1, tuple(SINK + Vector((-0.33, 0.12, 0.05))), M_glass, parent=broot)
for i, (col, tilt) in enumerate((((0.1, 0.4, 0.9), 12), ((0.95, 0.3, 0.4), -10))):
    cyl(f"toothbrush{i}", 0.0045, 0.19, tuple(SINK + Vector((-0.33 + 0.012 * (1 - 2 * i), 0.12, 0.13))), mat(f"tb{i}", col, 0.3),
        rot=(0, tilt, 0), parent=broot)
bevel_box("soap", (0.07, 0.045, 0.025), tuple(SINK + Vector((0.3, 0.1, 0.0125))), mat("soap", (0.95, 0.75, 0.8), 0.3, sss=0.3),
          parent=broot, w=0.008)
duck_root, duck = U.import_ph("rubber_duck_toy", broot, (0.55, 1.12, CT), -150, 1.0)
# sochiq
M_towel = mat("towel", (0.25, 0.55, 0.62), 0.95)
tw = bevel_box("towel", (0.45, 0.06, 0.6), (1.2, 1.24, 1.15), M_towel, parent=broot, w=0.02)
cyl("towel_bar", 0.01, 0.55, (1.2, 1.25, 1.47), M_chrome, rot=(0, 90, 0), parent=broot)
# qahramon shishasi (peshtaxtada, chanoq o'ng tomonida)
BOT = Vector((0.12, 0.94, CT))
bot_root = make_bottle("bottle", broot, cap_on=False)
bot_root.location = BOT; bot_root.rotation_euler = (0, 0, R(-18))
cup_ct = make_cup("cup_counter", broot, fill=0.75)
cup_ct.location = BOT + Vector((0.12, -0.06, 0.0))
# polga ag'darilgan shisha + ko'lmak (oxirgi kadr)
FLOOR_B = Vector((0.55, -0.35, 0.0))
fb = make_bottle("bottle_floor", broot, cap_on=False)
fb.location = FLOOR_B + Vector((0, 0, 0.024)); fb.rotation_euler = (R(90), 0, R(-60))
M_pud = mat("puddle", (0.02, 0.45, 0.18), 0.02, coat=1.0)
bsdf(M_pud).inputs["Transmission Weight"].default_value = 0.6
pud = U.uvsphere("puddle", 1.0, tuple(FLOOR_B + Vector((-0.2, 0.12, 0.0))), M_pud, scale=(0.32, 0.2, 0.004), seg=48, ring=12, parent=broot)
pd = pud.modifiers.new("d", "DISPLACE"); pdt = bpy.data.textures.new("pudtex", "CLOUDS"); pdt.noise_scale = 0.25; pd.texture = pdt
pd.direction = "X"; pd.strength = 0.25; pd.texture_coords = "GLOBAL"
pcap = cyl("cap_floor", 0.018, 0.026, tuple(FLOOR_B + Vector((-0.45, 0.3, 0.018))), M_cap, rot=(90, 0, 30), parent=broot, verts=40)
vis(broot, rng(*BATH))
for o in (fb, pud, pcap):                     # faqat oxirgi kadrda: broot kalitlarini tozalab, qaytadan
    for x in [o] + list(o.children_recursive): x.animation_data_clear()
    vis(o, rng("floor"))

# ======================================================================
# 2) QAHRAMONLAR: Kate (ona) va bola (Megan, 0.62)
# ======================================================================
kroot, kate, kmesh = mc.load_character("kate", "Kate.fbx")
U.soften(kmesh)
croot_, child, cmesh = mc.load_character("child", "Megan.fbx")
U.soften(cmesh)
croot_.scale = (0.62,) * 3
A = lambda f, inplace=True: mc.load_action(f, inplace)

def strip(arm, act, start, end, src=None, blend=4, speed=1.0):
    s = mc.add_strip(arm, act, start, blend=blend, src=src, speed=speed, hold=False)
    ln = (s.action_frame_end - s.action_frame_start) * s.scale
    s.repeat = max(1.0, (end - start + 1) / max(ln, 0.01))
    return s

KPOS = Vector((-0.38, 0.38, 0.0))      # lavabo oldida, +Y (ko'zgu) ga qaragan
# 2 ichish
G0, G1 = S["gulp"]
U.at(kroot, 1, tuple(KPOS), 180)
strip(kate, A("Drinking.fbx"), G0 - 62, G1 + 2, blend=0)
# 7 bosh aylanishi, 8 qorin og'rig'i
D0, D1 = S["dizzy"]; GU0, GU1 = S["gut"]
U.at(kroot, D0, tuple(KPOS), 180)
strip(kate, A("Dizzy_Idle.fbx"), D0 - 30, D1 + 2, blend=0)
strip(kate, A("Standing_React_Large_Gut.fbx"), GU0 - 3, GU1 + 2, blend=3, speed=0.75)
# 3 rentgen: tik turgan poza
X0, X1 = S["xray"]
U.at(kroot, X0, tuple(XR), 180)
strip(kate, A("Idle_9.fbx"), X0 - 1, X1 + 1, src=(60, 61), blend=0)
# 12 polda yotibdi
F0, F1 = S["floor"]
LAY = Vector((-0.1, -0.55, 0.0))
U.at(kroot, F0, tuple(LAY), 90)
lay_s = strip(kate, A("Laying_Breathless.fbx"), F0 - 1, F1 + 2, blend=0, speed=0.55)
interp(kroot, "CONSTANT")
# bola
C0, C1 = S["child"]; XC0, XC1 = S["xchild"]
CPOS = Vector((BOT.x - 0.12, 0.47, 0.0))
BOT_C = Vector((BOT.x, 0.8, CT))
for f_, p_ in ((1, BOT), (S["child"][0], BOT_C), (S["child"][1] + 1, BOT)): key(bot_root, f_, loc=tuple(p_))
interp(bot_root, "CONSTANT")
U.at(croot_, 1, tuple(CPOS), 180)
strip(child, A("Reaching_Out.fbx"), C0 - 40, C1 + 2, blend=0)
U.at(croot_, XC0, tuple(XR2), 180)
strip(child, A("Idle_9.fbx"), XC0 - 1, XC1 + 1, src=(60, 61), blend=0)
interp(croot_, "CONSTANT")

def bh(arm, bn): return arm.matrix_world @ arm.pose.bones["mixamorig:" + bn].head

# yotgan Kate'ni polga tushiramiz: kadr o'rtasida eng past nuqta 0 ga
sc.frame_set(F0 + 20); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
zmin = min((o.evaluated_get(dg).matrix_world @ v.co).z for o in kmesh if "Body" in o.name or "Shirt" in o.name
           for v in o.evaluated_get(dg).data.vertices)
kroot.location.z -= zmin - 0.005; kroot.keyframe_insert("location", frame=F0)
interp(kroot, "CONSTANT")
print("lay zmin", zmin)
sc.frame_set(1)

# ichish stakanchasi chap qo'lda
cup_b = U.bone_empty("cup_bone", kate, "LeftHand")
cup_off = empty("cup_off", (0.0, 0.05, 0.035), cup_b)      # LeftHand: Y = barmoqlar, Z = kaft, -X = stakan tepasi
cup_off.rotation_euler = (0, R(-90), 0)
cup_h = make_cup("cup_hand", cup_off, fill=0.7, r=0.024, h=0.04)
cup_h.location = (0, 0, -0.02)
vis(cup_b, rng("gulp"))
khead = U.bone_empty("kate_head", kate, "Head")
kface = empty("kate_face", (0, 0.06, 0.09), khead)
chead = U.bone_empty("child_head", child, "Head")
chand = U.bone_empty("child_hand", child, "RightHand")
kchest = U.bone_empty("kate_chest", kate, "Spine2")

# ======================================================================
# 3) RENTGEN: shaffof tana + qizilo'ngach + oshqozon
# ======================================================================
def ghosts_of(meshes, m):
    out = []
    for o in meshes:
        if "Eyelash" in o.name: continue
        g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g); g.animation_data_clear()
        for slot in g.material_slots: slot.link = "OBJECT"; slot.material = m
        out.append(g)
    return out

def organ_material(name, col=(1.0, 0.45, 0.5)):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    fac = U._m(N, L, "POWER", lw.outputs["Facing"], 1.3)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    L.new(U._m(N, L, "ADD", U._m(N, L, "MULTIPLY", fac, 2.0), 0.35), em.inputs["Strength"])
    trn = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader")
    L.new(U._m(N, L, "ADD", U._m(N, L, "MULTIPLY", fac, 0.6), 0.18, clamp=True), ms.inputs[0])
    L.new(trn.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2]); L.new(ms.outputs[0], N["Material Output"].inputs["Surface"])
    return m

def fill_material(name, col=(0.06, 1.0, 0.2), strength=4.0):
    """yashil suyuqlik: 'u' (egri bo'ylab) < FILL bo'lgan joy ko'rinadi"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    U.value_node(m, "FILL", 0.0)
    vis_ = U._m(N, L, "LESS_THAN", ua.outputs["Fac"], N["FILL"].outputs[0])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    trn = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader")
    L.new(vis_, ms.inputs[0]); L.new(trn.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
    L.new(ms.outputs[0], N["Material Output"].inputs["Surface"])
    return m

def build_gut(arm, prefix, scale=1.0):
    """bo'g'imlardan qizilo'ngach va oshqozon egri chiziqlari (dunyo koordinatasida)"""
    W3 = arm.matrix_world.to_3x3().normalized() @ arm.pose.bones["mixamorig:Spine1"].matrix.to_3x3().normalized()
    fwd = (W3 @ Vector((0, 0, 1))).normalized(); left = (W3 @ Vector((1, 0, 0))).normalized(); up = Vector((0, 0, 1))
    neck = bh(arm, "Neck"); head = bh(arm, "Head"); sp2 = bh(arm, "Spine2"); sp1 = bh(arm, "Spine1"); sp = bh(arm, "Spine")
    mouth = head.lerp(neck, 0.2) + fwd * 0.06 * scale + up * 0.02 * scale
    s = scale
    eso = [mouth, neck + fwd * 0.03 * s, sp2 + fwd * 0.02 * s, sp1 + fwd * 0.03 * s + left * 0.015 * s,
           sp1.lerp(sp, 0.3) + fwd * 0.05 * s + left * 0.04 * s]
    st_c = sp1.lerp(sp, 0.55) + fwd * 0.07 * s + left * 0.045 * s
    stom = [eso[-1] + left * 0.01 * s + up * 0.025 * s, st_c + left * 0.04 * s + up * 0.02 * s, st_c + left * 0.02 * s - up * 0.05 * s,
            st_c - left * 0.04 * s - up * 0.06 * s, st_c - left * 0.09 * s - up * 0.02 * s, st_c - left * 0.11 * s + up * 0.01 * s]
    return eso, stom, st_c, fwd, left, up

M_xbody = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.3, base=0.012)
M_xchild = P.xray_material("xray_child", col=(1.0, 0.25, 0.2), strength=1.5, base=0.02)
M_organ = organ_material("xray_organ")
M_eso = organ_material("xray_eso", (1.0, 0.55, 0.6))
xray_parts = {}
for arm, meshes, nm, sh, mx_, scl in ((kate, kmesh, "k", "xray", M_xbody, 1.0), (child, cmesh, "c", "xchild", M_xchild, 0.62)):
    f0, f1 = S[sh]
    sc.frame_set(f0 + 2); bpy.context.view_layer.update()
    gh = ghosts_of(meshes, mx_)
    eso, stom, st_c, fwd, left, up = build_gut(arm, nm, scl)
    t_eso = P.tube(f"{nm}_eso", [tuple(p) for p in eso], 0.011 * scl, M_eso)
    t_sto = P.tube(f"{nm}_stomach", [tuple(p) for p in stom], 0.055 * scl, M_organ, taper=[0.55, 0.95, 1.0, 0.85, 0.55, 0.35])
    M_fe = fill_material(f"{nm}_fill_eso"); M_fs = fill_material(f"{nm}_fill_sto")
    f_eso = P.tube(f"{nm}_eso_fill", [tuple(p) for p in eso], 0.008 * scl, M_fe)
    f_sto = P.tube(f"{nm}_sto_fill", [tuple(p) for p in stom], 0.046 * scl, M_fs, taper=[0.5, 0.9, 1.0, 0.8, 0.5, 0.3])
    # suyuqlik tomchilari qizilo'ngach bo'ylab
    M_drop = mat(f"{nm}_xdrop", (0.3, 1, 0.4), 0.3, emit=12.0, emit_col=(0.3, 1.0, 0.4))
    drops = []
    for k in range(14):
        o = sphere(f"{nm}_xd{k}", rnd.uniform(0.006, 0.01) * scl, (0, 0, 0), M_drop, scale=(1, 1, 1.6), sub=2)
        st = f0 + 2 + k * 2; dur = 16
        for f in range(st, min(st + dur, f1) + 1):
            o.location = U.path_point(eso, (f - st) / dur); o.keyframe_insert("location", frame=f)
        vis(o, [(st, min(st + dur - 1, f1))], False); drops.append(o)
    allp = gh + [t_eso, t_sto, f_eso, f_sto] + drops
    for o in gh + [t_eso, t_sto, f_eso, f_sto]: vis(o, rng(sh), False)
    xray_parts[nm] = dict(gh=gh, eso=eso, stom=stom, st_c=st_c, fwd=fwd, left=left, up=up, M_fe=M_fe, M_fs=M_fs, t_sto=t_sto)
    # to'ldirish
    for f, v in ((f0, 0.0), (f0 + 4, 0.0), (f0 + 22, 1.05)): U.key_value(M_fe, "FILL", f, v)
    for f, v in ((f0, 0.0), (f0 + 16, 0.0), (f1, 0.75 if nm == "k" else 0.95)): U.key_value(M_fs, "FILL", f, v)
sc.frame_set(1)
# bola: qizil xavf "pulsi" (rentgen tanasi yorqinligi)
for o in xray_parts["c"]["gh"]: pass
XCN = M_xchild.node_tree.nodes
emc = next(n for n in XCN if n.type == "EMISSION")
for i, f in enumerate(range(XC0, XC1 + 1, 12)):
    emc.inputs["Color"].default_value = (1.0, 0.22, 0.18, 1); emc.inputs["Color"].keyframe_insert("default_value", frame=f)
    emc.inputs["Color"].default_value = (0.35, 0.05, 0.04, 1); emc.inputs["Color"].keyframe_insert("default_value", frame=f + 6)

# haqiqiy meshlar rentgen va boshqa joylarda ko'rinmaydi
KVIS = rng("gulp", "dizzy", "gut", "floor")
for o in [kroot, kate] + kmesh: vis(o, KVIS, False)
for o in [croot_, child] + cmesh: vis(o, rng("child"), False)

# ======================================================================
# 4) OSHQOZON ICHI (x = 40): burmali shilliq qavat, yashil to'lqin
# ======================================================================
sroot = empty("stomach_in", tuple(SI))
def mucosa_material(name="mucosa"):
    m = O.airway_material(name); N = m.node_tree.nodes; L = m.node_tree.links
    U.value_node(m, "FRONT", 10.0)
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    burn = U._m(N, L, "MULTIPLY", U._m(N, L, "GREATER_THAN", sep.outputs[0], N["FRONT"].outputs[0]), 0.75)
    b = N["Principled BSDF"]; src = b.inputs["Base Color"].links[0].from_socket
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(burn, mx.inputs["Factor"])
    L.new(src, mx.inputs[6]); mx.inputs[7].default_value = (0.5, 0.02, 0.03, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    return m
M_muc = mucosa_material()
fl = plane("rugae", (9, 6), (0, 0, 0), M_muc, parent=sroot, sub=0)
sb = fl.modifiers.new("sub", "SUBSURF"); sb.subdivision_type = "SIMPLE"; sb.levels = sb.render_levels = 7
rt = bpy.data.textures.new("rugae_tex", "MARBLE"); rt.marble_type = "SHARP"; rt.noise_scale = 0.55; rt.turbulence = 4.0
rd = fl.modifiers.new("rug", "DISPLACE"); rd.texture = rt; rd.strength = 0.22; rd.texture_coords = "LOCAL"
rt2 = bpy.data.textures.new("rugae_tex2", "CLOUDS"); rt2.noise_scale = 0.3
rd2 = fl.modifiers.new("rug2", "DISPLACE"); rd2.texture = rt2; rd2.strength = 0.06; rd2.texture_coords = "LOCAL"
for p in fl.data.polygons: p.use_smooth = True
dome = U.uvsphere("stomach_dome", 1.0, (0, 0, -0.3), M_muc, scale=(5.0, 3.6, 2.6), seg=64, ring=32, parent=sroot)
dd = dome.modifiers.new("d", "DISPLACE"); dd.texture = rt; dd.strength = 0.25; dd.texture_coords = "LOCAL"
# yashil to'lqin: +X tomondan kameraga (-X) qarab keladi
ST0, ST1 = S["stomach"]
M_wave = liquid_mat("wave_liq", (0.03, 0.9, 0.25), dens=9.0, emit=0.4)
wave = box("wave", (6.0, 7.0, 0.5), (0, 0, 0), M_wave, parent=sroot)
wave.modifiers.new("sub", "SUBSURF").levels = 3
wt = bpy.data.textures.new("wave_tex", "CLOUDS"); wt.noise_scale = 0.35
wd = wave.modifiers.new("d", "DISPLACE"); wd.texture = wt; wd.strength = 0.18; wd.texture_coords = "GLOBAL"
for p in wave.data.polygons: p.use_smooth = True
for f, x in ((ST0, 4.2), (ST0 + 26, 2.4), (ST1 + 1, 1.0)):
    key(wave, f, loc=(x + 3.0, 0, 0.05))
    U.key_value(M_muc, "FRONT", f, x - 0.1)
M_bub = P.bubble_material()
M_foam = mat("foam", (0.75, 1.0, 0.8), 0.2, emit=0.3, emit_col=(0.5, 1, 0.6))
for k in range(90):
    o = sphere(f"fizz{k}", rnd.uniform(0.015, 0.06), (0, 0, 0), M_foam if k % 3 == 0 else M_bub, sub=2, parent=sroot)
    y = rnd.uniform(-1.6, 1.6); t0 = rnd.randint(ST0, ST1 - 6); life = rnd.randint(10, 22)
    xf = 4.2 + (1.0 - 4.2) * ((t0 - ST0) / (ST1 - ST0)) ** 0.8
    for f, z, s in ((t0, 0.05, 0.2), (t0 + life // 2, 0.35, 1.0), (t0 + life, 0.7, 0.0)):
        key(o, f, loc=(xf + rnd.uniform(-0.15, 0.25), y, z), scale=(s, s, s))
    o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=t0 - 1)
vis(sroot, rng("stomach"))

# ======================================================================
# 5) TISH YUZASI MAKRO (x = 80): bakteriyalar va yashil to'lqin
# ======================================================================
aroot = empty("enamel_root", tuple(BA))
def enamel_material():
    m = bpy.data.materials.new("enamel"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.82, 0.76, 0.62, 1); cr.color_ramp.elements[1].color = (0.96, 0.94, 0.88, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.18
    b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.02
    b.inputs["Coat Weight"].default_value = 0.6
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
en = plane("enamel", (12, 8), (0, 0, 0), enamel_material(), parent=aroot)
sb = en.modifiers.new("sub", "SUBSURF"); sb.subdivision_type = "SIMPLE"; sb.levels = sb.render_levels = 7
et = bpy.data.textures.new("enamel_tex", "CLOUDS"); et.noise_scale = 0.6
ed = en.modifiers.new("d", "DISPLACE"); ed.texture = et; ed.strength = 0.12; ed.texture_coords = "LOCAL"
for p in en.data.polygons: p.use_smooth = True
# bakteriyalar: bitta material, Object Info joylashuvi FRONT dan katta bo'lsa "o'lik" rang
M_bac = bpy.data.materials.new("bact"); M_bac.use_nodes = True
N = M_bac.node_tree.nodes; L = M_bac.node_tree.links; b = N["Principled BSDF"]
oi = N.new("ShaderNodeObjectInfo"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(oi.outputs["Location"], sep.inputs[0])
U.value_node(M_bac, "FRONT", 999.0)
dead = U._m(N, L, "GREATER_THAN", sep.outputs[0], N["FRONT"].outputs[0])
cmx = N.new("ShaderNodeMix"); cmx.data_type = "RGBA"; L.new(dead, cmx.inputs["Factor"])
crr = N.new("ShaderNodeValToRGB"); L.new(oi.outputs["Random"], crr.inputs[0])
crr.color_ramp.elements[0].color = (0.45, 0.12, 0.75, 1); crr.color_ramp.elements[1].color = (0.85, 0.25, 0.55, 1)
L.new(crr.outputs[0], cmx.inputs[6]); cmx.inputs[7].default_value = (0.28, 0.25, 0.18, 1); L.new(cmx.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.3; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.01
b.inputs["Coat Weight"].default_value = 0.6
BA0, BA1 = S["bact"]
FR_K = [(BA0, 3.2), (BA0 + 30, 2.0), (BA1 + 1, -0.45)]       # to'lqin oldi (mahalliy x), +X dan -X ga
def front_at(f):
    for (fa, xa), (fb_, xb) in zip(FR_K, FR_K[1:]):
        if fa <= f <= fb_: return xa + (xb - xa) * (f - fa) / (fb_ - fa)
    return FR_K[-1][1]
for f, x in FR_K: U.key_value(M_bac, "FRONT", f, BA.x + x - 0.05)
bacts = []
for k in range(170):
    x = rnd.uniform(-1.6, 2.6); y = rnd.uniform(-1.2, 1.4)
    if rnd.random() < 0.6:
        o = O.bacterium(f"bac{k}", rnd.uniform(0.022, 0.03), rnd.uniform(0.06, 0.12), M_bac, parent=aroot)
        o.rotation_euler = (R(90), 0, rnd.uniform(0, 6.28)); z = 0.03
    else:
        o = sphere(f"bac{k}", rnd.uniform(0.025, 0.035), (0, 0, 0), M_bac, sub=2, parent=aroot); z = 0.035
    o.location = (x, y, z + 0.02)
    # to'lqin yetganda bujmayadi
    fk = next((f for f in range(BA0, BA1 + 40) if front_at(f) < x), None)
    if fk:
        s0 = o.scale.copy()
        o.keyframe_insert("scale", frame=fk)
        o.scale = (s0.x * 0.75, s0.y * 0.75, s0.z * 0.45); o.keyframe_insert("scale", frame=fk + 8)
    for f in (BA0, BA1 + 1):
        o.location = (x + 0.0006 * (f - BA0) * math.sin(k), y, z + 0.02); o.keyframe_insert("location", frame=f)
    bacts.append(o)
M_bw = liquid_mat("bact_wave", (0.03, 0.9, 0.25), dens=10.0, emit=0.3)
bw = box("bact_wave", (6.0, 5.0, 0.35), (0, 0, 0), M_bw, parent=aroot)
bw.modifiers.new("sub", "SUBSURF").levels = 3
bwd = bw.modifiers.new("d", "DISPLACE"); bwd.texture = wt; bwd.strength = 0.14; bwd.texture_coords = "GLOBAL"
for p in bw.data.polygons: p.use_smooth = True
for f, x in FR_K: key(bw, f, loc=(x + 3.0, 0, 0.12))
for k in range(50):
    o = sphere(f"bbub{k}", rnd.uniform(0.012, 0.035), (0, 0, 0), M_bub, sub=2, parent=aroot)
    t0 = rnd.randint(BA0, BA1 - 8); xf = front_at(t0)
    y = rnd.uniform(-1.0, 1.0)
    for f, z, s in ((t0, 0.05, 0.3), (t0 + 10, 0.25, 1.0), (t0 + 20, 0.4, 0.0)):
        key(o, f, loc=(xf + rnd.uniform(0, 0.3), y, z), scale=(s, s, s))
    o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=t0 - 1)
vis(aroot, rng("bact"))

# ======================================================================
# 6) MOLEKULALAR (x = 120): spirt (C2H5OH) va ftorid ionlari, yashil suyuqlik ichida
# ======================================================================
mroot = empty("mol_root", tuple(MO))
M_C = mat("atom_C", (0.12, 0.12, 0.13), 0.25, coat=1.0)
M_O = mat("atom_O", (0.85, 0.08, 0.06), 0.25, coat=1.0)
M_H = mat("atom_H", (0.95, 0.95, 0.95), 0.25, coat=1.0)
M_bd = mat("bond", (0.75, 0.75, 0.72), 0.3)
M_F = mat("fluoride", (0.75, 1.0, 0.25), 0.2, emit=2.5, emit_col=(0.7, 1.0, 0.2), coat=1.0)
def ethanol(name, parent, size=0.12):
    root = empty(name, (0, 0, 0), parent)
    A_ = {"C1": (0, 0, 0), "C2": (1.52, 0, 0), "O": (2.1, 1.25, 0), "HO": (3.05, 1.2, 0.1),
          "H1": (-0.4, -1.0, 0.2), "H2": (-0.4, 0.5, 0.85), "H3": (-0.4, 0.5, -0.85),
          "H4": (1.9, -0.55, 0.88), "H5": (1.9, -0.55, -0.88)}
    BND = [("C1", "C2"), ("C2", "O"), ("O", "HO"), ("C1", "H1"), ("C1", "H2"), ("C1", "H3"), ("C2", "H4"), ("C2", "H5")]
    for a, p in A_.items():
        r_ = {"C": 0.62, "O": 0.6, "H": 0.38}[a[0]]
        sphere(f"{name}_{a}", r_ * size, tuple(Vector(p) * size), {"C": M_C, "O": M_O, "H": M_H}[a[0]], sub=3, parent=root)
    for a, b_ in BND:
        pa, pb = Vector(A_[a]) * size, Vector(A_[b_]) * size; d = pb - pa
        c = cyl(f"{name}_{a}{b_}", 0.13 * size, d.length, tuple((pa + pb) / 2), M_bd, parent=root, verts=12)
        c.rotation_mode = "QUATERNION"; c.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return root
MO0, MO1 = S["mol"]
mols = []
for k in range(9):
    e = ethanol(f"eth{k}", mroot, size=0.12 if k else 0.16)
    p = Vector((0, 0, 0)) if k == 0 else Vector((rnd.uniform(-1.6, 1.6), rnd.uniform(-1.2, 1.6), rnd.uniform(-1.0, 1.0)))
    rot0 = Vector((rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6)))
    for f in (MO0, MO1 + 1):
        t = f - MO0
        e.location = p + Vector((0.0, 0.0, 0.002 * t)) - Vector((0.25, 0, 0)) * (k == 0)
        e.rotation_euler = rot0 + Vector((0.012, 0.02, 0.008)) * t * (1 if k % 2 else -1)
        e.keyframe_insert("location", frame=f); e.keyframe_insert("rotation_euler", frame=f)
    interp(e, "LINEAR"); mols.append(e)
for k in range(14):
    p = Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-1.0, 1.8), rnd.uniform(-1.0, 1.0)))
    if p.length < 0.5: p += Vector((0.6, 0.6, 0))
    o = sphere(f"fion{k}", rnd.uniform(0.05, 0.075), tuple(p), M_F, sub=3, parent=mroot)
    for f in (MO0, MO1 + 1):
        o.location = p + Vector((math.sin(k), math.cos(k), 0.5)) * 0.002 * (f - MO0); o.keyframe_insert("location", frame=f)
    interp(o, "LINEAR")
M_mb = mat("mol_bokeh", (0.5, 1.0, 0.6), 0.3, emit=3.0, emit_col=(0.4, 1.0, 0.5))
for k in range(60):
    p = Vector((rnd.uniform(-3, 3), rnd.uniform(1.5, 5), rnd.uniform(-2.5, 2.5)))
    sphere(f"mbok{k}", rnd.uniform(0.01, 0.03), tuple(p), M_mb if k % 2 else M_bub, sub=2, parent=mroot)
vis(mroot, rng("mol"))

# ======================================================================
# 7) QON TOMIRI (x = 160): o'q +Y, eritrotsitlar oqimi, yashil molekulalar devordan
# ======================================================================
vroot = empty("vessel_root", tuple(BV))
def vessel_material():
    m = O.airway_material("vessel"); N = m.node_tree.nodes
    cr = next(n for n in N if n.type == "VALTORGB")
    cr.color_ramp.elements[0].color = (0.25, 0.01, 0.02, 1); cr.color_ramp.elements[1].color = (0.62, 0.08, 0.1, 1)
    return m
vt = O.tunnel("vessel", length=36.0, r=1.0, nx=300, nr=64, ring_pitch=1e6, parent=vroot, m=vessel_material())
def rbc_mesh(name, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.0)
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        d = math.hypot(v.co.x, v.co.y)
        v.co.z *= 0.32 * (0.35 + 1.2 * d ** 2)
    o.data.materials.append(m); U._smooth(o)
    return o
M_rbc = mat("rbc", (0.6, 0.02, 0.03), 0.25, sss=0.6, coat=0.5)
bsdf(M_rbc).inputs["Subsurface Scale"].default_value = 0.05
rbc0 = rbc_mesh("rbc_src", M_rbc); rbc0.parent = vroot; rbc0.location = (0, -50, 0)
BV0, BV1 = S["blood"]
for k in range(110):
    o = rbc0.copy(); o.data = rbc0.data; sc.collection.objects.link(o); o.parent = vroot; o.name = f"rbc{k}"
    s = rnd.uniform(0.14, 0.18); o.scale = (s, s, s)
    a = rnd.uniform(0, 6.283); rr = rnd.uniform(0.0, 0.75)
    y0 = rnd.uniform(-2, 30); v = rnd.uniform(0.05, 0.09) * (1.2 - rr * 0.5)
    r0 = Vector((rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6))); dr = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.04
    for f in (BV0, BV1 + 1):
        t = f - BV0
        o.location = (rr * math.cos(a), y0 + v * t, rr * math.sin(a)); o.keyframe_insert("location", frame=f)
        o.rotation_euler = r0 + dr * t; o.keyframe_insert("rotation_euler", frame=f)
    interp(o, "LINEAR")
M_tox = mat("toxin", (0.5, 1.0, 0.25), 0.3, emit=5.0, emit_col=(0.45, 1.0, 0.2))
for k in range(40):
    o = O.molecule(f"vtox{k}", M_tox, M_tox, M_bd, 300 + k, size=0.035, parent=vroot)
    a = rnd.uniform(0, 6.283); y0 = rnd.uniform(1.0, 12.0); t_in = rnd.randint(BV0, BV1 - 20)
    for f, rr, dy in ((BV0, 1.08, 0.0), (t_in, 1.08, 0.0), (t_in + 25, 0.6, 1.2), (BV1 + 1, 0.4, 1.2 + 0.07 * (BV1 + 1 - t_in - 25))):
        o.location = (rr * math.cos(a), y0 + dy, rr * math.sin(a)); o.keyframe_insert("location", frame=f)
        o.rotation_euler = (f * 0.03, f * 0.05 + k, 0); o.keyframe_insert("rotation_euler", frame=f)
vis(vroot, rng("blood"))

# ======================================================================
# 8) KAMERALAR
# ======================================================================
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c
def cam_path(c, pairs):
    for f, loc in pairs: key(c, f, loc=tuple(loc))
def smooth_path(c, f0, f1, p0, p1, ease=2.0, step=2):
    for f in range(f0, f1 + 2, step):
        t = (f - f0) / max(1, f1 + 1 - f0); e = 1 - (1 - t) ** ease
        key(c, f, loc=tuple(Vector(p0).lerp(Vector(p1), e)))

# 1 hook: shisha makro, past, aylanma
H0, H1 = S["hook"]
bT = empty("botT", tuple(BOT + Vector((0.02, 0, 0.1))))
c = shot_cam("hook", (0, 0, 0), bT, 32, 2.0, focus=bT)
for f in range(H0, H1 + 2, 2):
    t = (f - H0) / (H1 + 1 - H0); a = R(-125 + 40 * t); d = 0.5 - 0.16 * t
    key(c, f, loc=tuple(BOT + Vector((math.cos(a) * d, 0.0 + math.sin(a) * d, 0.035 + 0.04 * t))))
# 2 ichish: pastdan yuzga yaqin
gT = empty("gulpT", (0, 0, 0), kface)
c = shot_cam("gulp", (0, 0, 0), kface, 30, 2.0, focus=kface)
sc.frame_set(G0 + 10); bpy.context.view_layer.update(); fpos = kface.matrix_world.translation.copy(); sc.frame_set(1)
smooth_path(c, G0, G1, fpos + Vector((0.32, 0.62, -0.32)), fpos + Vector((0.2, 0.42, -0.22)))
# 3 rentgen: ko'krakdan oshqozonga
kx = xray_parts["k"]
xT = empty("xrayT", tuple(kx["eso"][2]))
c = shot_cam("xray", (0, 0, 0), xT, 35, 4.0, focus=xT)
fd = (kx["fwd"] + kx["left"] * 0.35).normalized()
smooth_path(c, X0, X1, kx["eso"][2] + fd * 1.3 + kx["up"] * 0.15, kx["st_c"] + fd * 0.55 + kx["up"] * 0.05, ease=1.6)
cam_path(xT, [(X0, kx["eso"][1]), (X1 + 1, kx["st_c"])])
# 4 oshqozon ichi: past uchish
c = shot_cam("stomach", (0, 0, 0), None, 16, 5.6, focus=1.8)
c.rotation_euler = (R(84), 0, R(-90))
smooth_path(c, ST0, ST1, SI + Vector((-3.2, 0.2, 0.55)), SI + Vector((-2.3, -0.1, 0.45)), ease=1.3)
shake(c, ST0 + 24, ST0 + 40, 0.03, 4)
# 5 bakteriyalar: makro, yon dolly
baT = empty("bactT", tuple(BA + Vector((0.3, 0.0, 0.05))))
c = shot_cam("bact", (0, 0, 0), baT, 28, 4.5, focus=baT)
smooth_path(c, BA0, BA1, BA + Vector((-1.2, -0.75, 0.48)), BA + Vector((-0.95, 0.3, 0.4)), ease=1.2)
cam_path(baT, [(BA0, BA + Vector((-0.35, -0.1, 0.03))), (BA1 + 1, BA + Vector((-0.2, 0.35, 0.03)))])
# 6 molekulalar: orbit
moT = empty("molT", tuple(MO))
c = shot_cam("mol", (0, 0, 0), moT, 40, 3.2, focus=moT)
for f in range(MO0, MO1 + 2, 2):
    t = (f - MO0) / (MO1 + 1 - MO0); a = R(-110 + 70 * t)
    key(c, f, loc=tuple(MO + Vector((math.cos(a) * (1.9 - 0.45 * t), math.sin(a) * (1.9 - 0.45 * t), 0.35 - 0.2 * t))))
# 7 bosh aylanishi: pastdan keng
dT = empty("dizzyT", (0, 0, 0), kchest)
c = shot_cam("dizzy", (0, 0, 0), kchest, 16, 4.0, focus=khead)
smooth_path(c, D0, D1, Vector((1.0, 0.6, 0.2)), Vector((0.88, 0.52, 0.3)), ease=1.4)
# 8 qorin og'rig'i: yuzga yaqin, silkinish
c = shot_cam("gut", (0, 0, 0), kface, 32, 2.0, focus=kface)
smooth_path(c, GU0, GU1, Vector((-0.95, 0.95, 0.95)), Vector((-0.88, 0.88, 1.0)), ease=1.5)
shake(c, GU0 + 2, GU0 + 18, 0.03, 8)
# 9 bola: poldan, shisha oldingi planda
c = shot_cam("child", (0, 0, 0), None, 18, 3.5, focus=0.55)
chT = empty("childT", tuple(BOT_C + Vector((-0.06, -0.06, 0.08))))
c.constraints.new("TRACK_TO").target = chT
c.constraints[0].track_axis = "TRACK_NEGATIVE_Z"; c.constraints[0].up_axis = "UP_Y"
smooth_path(c, C0, C1, Vector((0.9, 0.28, 0.3)), Vector((0.78, 0.36, 0.36)), ease=1.4)
# 10 bola rentgen
cx = xray_parts["c"]
xcT = empty("xchildT", tuple(cx["st_c"]))
c = shot_cam("xchild", (0, 0, 0), xcT, 35, 4.0, focus=xcT)
fdc = (cx["fwd"] - cx["left"] * 0.3).normalized()
smooth_path(c, XC0, XC1, cx["st_c"] + fdc * 1.1 + cx["up"] * 0.25, cx["st_c"] + fdc * 0.42 + cx["up"] * 0.05, ease=1.6)
# 11 qon tomiri
bvT = empty("bloodT", tuple(BV + Vector((0, 8, 0))))
c = shot_cam("blood", (0, 0, 0), bvT, 22, 4.0, focus=1.5)
smooth_path(c, BV0, BV1, BV + Vector((0.25, 0.0, 0.2)), BV + Vector((0.1, 2.6, 0.05)), ease=1.0)
cam_path(bvT, [(BV0, BV + Vector((0, 8, 0))), (BV1 + 1, BV + Vector((0.15, 11, -0.1)))])
# 12 polda: tepadan, sekin ko'tarilib aylanadi
sc.frame_set(F0 + 10); bpy.context.view_layer.update()
chest_p = kchest.matrix_world.translation.copy(); sc.frame_set(1)
flT = empty("floorT", tuple(chest_p))
FB2 = Vector((chest_p.x + 0.2, chest_p.y - 0.42, 0.0))
fb.location = FB2 + Vector((0, 0, 0.024)); pud.location = FB2 + Vector((-0.18, 0.16, 0.0)); pcap.location = FB2 + Vector((0.3, -0.12, 0.018))
c = shot_cam("floor", (0, 0, 0), None, 24, 4.0, focus=1.5)
for f in range(F0, F1 + 2, 2):
    t = (f - F0) / (F1 + 1 - F0)
    c.location = chest_p + Vector((0.1, -0.15, 1.2 + 0.7 * t)); c.keyframe_insert("location", frame=f)
    c.rotation_euler = (0, 0, R(90 + 18 * t)); c.keyframe_insert("rotation_euler", frame=f)
c.data.dof.focus_object = flT

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 9) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "modern_bathroom.hdr")
flat = N.new("ShaderNodeMix"); flat.data_type = "RGBA"; L.new(env.outputs[0], flat.inputs[6])
bg = N["Background"]; L.new(flat.outputs[2], bg.inputs[0])
BATHW = (0.6, 0, (0, 0, 0))
WL = {"hook": BATHW, "gulp": BATHW, "xray": (1.0, 1, (0.0, 0.004, 0.012)), "stomach": (1.0, 1, (0.08, 0.01, 0.012)),
      "bact": (1.0, 1, (0.06, 0.03, 0.04)), "mol": (1.0, 1, (0.01, 0.06, 0.03)), "dizzy": BATHW, "gut": BATHW, "child": BATHW,
      "xchild": (1.0, 1, (0.012, 0.0, 0.002)), "blood": (1.0, 1, (0.03, 0.0, 0.0)), "floor": (0.4, 0, (0, 0, 0))}
for f, n in SHOTS:
    cur = WL[n]
    bg.inputs[1].default_value = cur[0]; bg.inputs[1].keyframe_insert("default_value", frame=f)
    flat.inputs["Factor"].default_value = cur[1]; flat.inputs["Factor"].keyframe_insert("default_value", frame=f)
    flat.inputs[7].default_value = (*cur[2], 1); flat.inputs[7].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

BR = rng(*BATH)
area("ceil_light", (0.0, -0.1, 2.5), 1.0, (1, 0.95, 0.88), lights_for(BR, 160), target=None)
bpy.data.objects["ceil_light"].rotation_euler = (0, 0, 0)
area("vanity_key", (-0.2, 1.05, 2.1), 0.8, (1, 0.93, 0.82), lights_for(BR, 90), target=kchest)
# hook: shisha orqasidan yashil nurlanish uchun kontur nur
area("hook_rim", tuple(BOT + Vector((0.25, 0.25, 0.35))), 0.25, (1, 1, 0.95), lights_for(rng("hook"), 25), target=bT)
area("hook_fill", tuple(BOT + Vector((-0.4, -0.5, 0.25))), 0.4, (1, 0.92, 0.85), lights_for(rng("hook"), 12), target=bT)
area("face_key", tuple(KPOS + Vector((0.6, 0.9, 1.9))), 0.6, (1, 0.92, 0.85), lights_for(rng("gulp", "gut"), 70), target=kface)
area("face_rim", tuple(KPOS + Vector((-0.8, -0.6, 1.9))), 0.4, (0.7, 0.85, 1.0), lights_for(rng("gulp", "gut", "dizzy"), 60), target=kface)
area("child_key", tuple(BOT + Vector((0.6, -0.3, 0.6))), 0.5, (1, 0.9, 0.8), lights_for(rng("child"), 40), target=chT)
# pol: chiroq so'nadi
fl_l = area("floor_key", tuple(LAY + Vector((0.4, 0.3, 2.3))), 1.0, (1, 0.92, 0.85), [(1, 0), (F0, 140), (F1 - 20, 60), (F1 + 1, 0)], target=flT)
for fc in U.fcurves(fl_l.data):
    for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
cl = bpy.data.objects["ceil_light"].data
for f, e in ((F0, 160), (F1 - 10, 50)):
    cl.energy = e; cl.keyframe_insert("energy", frame=f)
# oshqozon / tomir / bakteriya / molekula
area("st_key", tuple(SI + Vector((-1.5, -1.5, 2.0))), 2.0, (1, 0.85, 0.8), lights_for(rng("stomach"), 400), target=sroot)
area("st_rim", tuple(SI + Vector((2.0, 1.0, 1.2))), 1.5, (0.6, 1.0, 0.6), lights_for(rng("stomach"), 300), target=sroot)
area("st_cam", (0, 0, 0), 0.2, (1, 0.9, 0.85), lights_for(rng("stomach"), 60), parent=CAMS["stomach"], kind="POINT")
area("ba_key", tuple(BA + Vector((-1.2, -1.6, 2.0))), 2.0, (1, 0.95, 0.9), lights_for(rng("bact"), 300), target=aroot)
area("ba_rim", tuple(BA + Vector((2.0, 1.6, 0.8))), 1.5, (0.5, 1.0, 0.6), lights_for(rng("bact"), 250), target=aroot)
area("mo_key", tuple(MO + Vector((-1.5, -1.0, 1.8))), 1.5, (1, 0.95, 0.9), lights_for(rng("mol"), 220), target=mroot)
area("mo_rim", tuple(MO + Vector((1.5, 2.0, 0.5))), 1.5, (0.4, 1.0, 0.5), lights_for(rng("mol"), 260), target=mroot)
area("bv_cam", (0.05, 0.08, 0.05), 0.15, (1, 0.9, 0.85), lights_for(rng("blood"), 45), parent=CAMS["blood"], kind="POINT")
area("bv_glow", tuple(BV + Vector((0, 16, 0))), 1.0, (1.0, 0.3, 0.25), lights_for(rng("blood"), 80), kind="POINT")

# ======================================================================
# 10) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.1
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = os.environ.get("PERSIST", "1") == "1"
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b_ = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b_
        bpy.ops.render.render(animation=True)
