# "Oq sochni yulish" — Zack D. Films uslubida 44.3 s (1063 kadr, 24 fps, 9:16).
# Uch dunyo bitta faylda: hammom (0,0,0) [metr], bosh terisi makro (1000,0,0) [1 birlik = 1 mm],
# soch follikulasi kesimi (2000,0,0) [1 birlik = 1 mm]. Kesishlar kamera markerlari bilan (STORYBOARD.md).
# Render: OUT=... SAMPLES=8 PCT=40 python -I oqsoch.py --render   (FRAMES=1,60 sinov uchun, RANGE=a,b qism)
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ZT, "goz")); sys.path.insert(0, ZT)
from mathutils import Vector, Matrix
import numpy as np
import parts as P                                   # zack_test/goz/parts.py
from parts import R, box, cyl, sphere, empty, par, mat, bsdf, vis, cam_move, camera
import mixchar as mc

OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
NF = 1063
sc.frame_start, sc.frame_end, sc.render.fps = 1, NF, 24

# kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md)
S = {1: (1, 43), 2: (44, 82), 3: (83, 121), 4: (122, 171), 5: (172, 216), 6: (217, 262), 7: (263, 341), 8: (342, 373),
     9: (374, 451), 10: (452, 506), 11: (507, 547), 12: (548, 593), 13: (594, 668), 14: (669, 747), 15: (748, 819),
     16: (820, 922), 17: (923, 996), 18: (997, NF)}
def rng(*shots): return [S[s] for s in shots]
BA = Vector((0, 0, 0)); SK = Vector((1000, 0, 0)); CX = Vector((2000, 0, 0))
K = lambda v: tuple(v)

def all_const(idb):
    for fc in P.all_fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"

def vis_only(o, ranges):
    """Ota vis() qoldirgan hide_render kalitlarini o'chirib, faqat shu oraliqlarni qo'yish (o va bolalari)."""
    for x in [o] + list(o.children_recursive):
        ad = x.animation_data
        if ad and ad.action:
            act = ad.action
            bags = [cb for l in act.layers for st in l.strips for cb in st.channelbags] if getattr(act, "layers", None) else [act]
            for cb in bags:
                for fc in [fc for fc in cb.fcurves if fc.data_path == "hide_render"]: cb.fcurves.remove(fc)
    vis(o, ranges)

def keyv(sock, f, v, path="default_value"):
    setattr(sock, path, v); sock.keyframe_insert(path, frame=f)

def tame(meshes, rough=0.55):
    """Mixamo materiallarining plastmassa yaltirashini kamaytirish."""
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.3
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = rough
                    n.inputs["Coat Weight"].default_value = 0.0

def area(nm, loc, rot, en, size, col, parent, cam_vis=False):
    l = P.link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA"))); l.data.energy = en; l.data.size = size
    l.data.color = col; l.location = loc; l.rotation_euler = rot; l.visible_camera = cam_vis; par(l, parent); return l

def glow_mat(name, col, strength=4.0):
    """Yumshoq nur shari: markazi yorqin, chetlari shaffof (yallig'lanish)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = N["Material Output"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L.new(lw.outputs["Facing"], inv.inputs[1])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; L.new(inv.outputs[0], pw.inputs[0]); pw.inputs[1].default_value = 2.0
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(pw.outputs[0], mu.inputs[0])
    st = N.new("ShaderNodeValue"); st.name = "STR"; st.outputs[0].default_value = strength; L.new(st.outputs[0], mu.inputs[1])
    L.new(mu.outputs[0], em.inputs["Strength"])
    ad = N.new("ShaderNodeAddShader"); tr = N.new("ShaderNodeBsdfTransparent")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs["Surface"])
    return m

def cyl_up(name, r, h, m, verts=24):
    """Asosi (0,0,0) da, +Z bo'ylab h balandlikdagi silindr (scale.z bilan o'stirish uchun)."""
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=h)
    for v in bm.verts: v.co.z += h / 2
    o = P.mesh_obj(name, bm, m); P.smooth(o); return o

def tube(name, pts, r, m, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 4
    spl = cu.splines.new("BEZIER"); spl.bezier_points.add(len(pts) - 1)
    for bp_, p in zip(spl.bezier_points, pts):
        bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
    o = P.link(bpy.data.objects.new(name, cu)); cu.materials.append(m)
    if parent: o.parent = parent
    return o

A = lambda f, inplace=True: mc.load_action(f, inplace)

# =================================================================== 1) HAMMOM (metr)
bath = empty("SET_bath")
tiles = P.tex_image_mat("ph_tiles", PH + "long_white_tiles", 0.8)
floor_m = P.tex_image_mat("ph_floor", PH + "floor_tiles_06", 0.7)
plaster = P.tex_image_mat("ph_plaster", PH + "painted_plaster_wall", 0.6, tint=(0.82, 0.86, 0.9))
def bx(name, size, loc, m, bevel=0.0):
    o = box(name, size, loc, m, bevel); par(o, bath); return o
bx("floor", (3.0, 3.4, 0.04), (0, 0.4, -0.02), floor_m)
bx("ceiling", (3.0, 3.4, 0.04), (0, 0.4, 2.62), mat("ceil", (0.9, 0.9, 0.88), 0.8))
bx("wall_mirror", (3.0, 0.06, 2.64), (0, -0.93, 1.3), tiles)
bx("wall_back", (3.0, 0.06, 2.64), (0, 2.1, 1.3), plaster)
bx("wall_l", (0.06, 3.4, 2.64), (1.4, 0.4, 1.3), plaster)
bx("wall_r", (0.06, 3.4, 2.64), (-1.4, 0.4, 1.3), tiles)
# yuvinish stoli (tumba), stoleshnitsa, rakovina, jo'mrak
wood = mat("vanity", (0.32, 0.22, 0.15), 0.45, coat=0.3)
bx("vanity", (1.3, 0.5, 0.8), (0, -0.65, 0.42), wood, bevel=0.01)
for x in (-0.33, 0.33):
    bx("vanity_door_gap", (0.006, 0.505, 0.7), (x, -0.65, 0.42), mat("gap", (0.03, 0.02, 0.015), 0.6))
marble = mat("counter", (0.92, 0.91, 0.89), 0.18, coat=0.5)
bx("counter", (1.36, 0.54, 0.04), (0, -0.65, 0.84), marble, bevel=0.005)
bm = bmesh.new()
prof = [(0.0, 0.0), (0.15, 0.0), (0.2, 0.05), (0.215, 0.13), (0.205, 0.13), (0.19, 0.055), (0.145, 0.014), (0.0, 0.014)]
vs = [bm.verts.new((x, 0, z)) for x, z in prof]
for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=48, use_duplicate=False)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
porcelain = mat("porcelain", (0.95, 0.95, 0.94), 0.08, coat=0.8)
sink = P.mesh_obj("sink_bowl", bm, porcelain, (0.0, -0.66, 0.86)); P.smooth(sink); par(sink, bath)
sink.scale = (1.0, 0.8, 0.9)
chrome = mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0)
f1 = cyl("faucet_post", 0.016, 0.28, (0, -0.86, 1.0), chrome); par(f1, bath)
f2 = cyl("faucet_spout", 0.012, 0.16, (0, -0.79, 1.13), chrome, rot=(90, 0, 0)); par(f2, bath)
f3 = cyl("faucet_lever", 0.008, 0.08, (0.04, -0.86, 1.15), chrome, rot=(0, 60, 0)); par(f3, bath)
# ko'zgu va uning ustidagi chiroq
mirror_m = mat("mirror", (0.92, 0.93, 0.95), 0.02, metal=1.0)
bx("mirror_frame", (0.98, 0.03, 0.92), (0, -0.905, 1.58), mat("frame", (0.03, 0.03, 0.03), 0.35, metal=0.6), bevel=0.006)
bx("mirror_glass", (0.92, 0.01, 0.86), (0, -0.888, 1.58), mirror_m)
bx("mirror_lamp", (0.7, 0.05, 0.04), (0, -0.87, 2.09), mat("lampbar", (1.0, 0.85, 0.65), 0.3, emit=12.0))
# mayda buyumlar: stakan + tish cho'tkasi, sovun idishi, sochiq
glass_m = mat("cup", (0.5, 0.75, 0.8), 0.15, coat=0.6)
c_ = cyl("cup", 0.035, 0.1, (0.42, -0.75, 0.91), glass_m); par(c_, bath)
for i, col in enumerate(((0.9, 0.2, 0.2), (0.2, 0.5, 0.9))):
    tb = cyl(f"brush{i}", 0.006, 0.19, (0.415 + i * 0.012, -0.75, 0.99), mat(f"brush_m{i}", col, 0.3), rot=(8 - 16 * i, 6, 0)); par(tb, bath)
sb = cyl("soap", 0.03, 0.15, (-0.45, -0.78, 0.935), mat("soap", (0.85, 0.75, 0.55), 0.2, coat=0.4)); par(sb, bath)
sp_ = cyl("soap_pump", 0.008, 0.05, (-0.45, -0.78, 1.03), chrome); par(sp_, bath)
towel_m = mat("towel", (0.75, 0.55, 0.45), 0.95)
bx("towel_bar", (0.02, 0.6, 0.02), (-1.34, 0.2, 1.25), chrome)
tw = bx("towel", (0.04, 0.5, 0.55), (-1.33, 0.2, 1.0), towel_m, bevel=0.015)
proot, _ = P.import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.05, -0.55, 0.0), name="plant"); proot.scale = (1.4,) * 3
par(proot, bath)
# deraza (chap devorda) va yorug'lik
bx("window", (0.02, 0.9, 1.0), (1.37, 0.6, 1.6), mat("window", (0.85, 0.92, 1.0), 0.2, emit=6.0))
area("bath_window", (1.25, 0.6, 1.6), (0, R(-90), 0), 120, 1.0, (0.8, 0.88, 1.0), bath)
area("bath_ceiling", (0, 0.2, 2.55), (0, 0, 0), 90, 1.2, (1.0, 0.9, 0.78), bath)
area("bath_mirrorlamp", (0, -0.8, 2.02), (R(25), 0, 0), 60, 0.7, (1.0, 0.82, 0.62), bath)
area("bath_rim", (-0.8, 1.2, 2.1), (R(-50), 0, R(-150)), 70, 0.8, (1.0, 0.8, 0.6), bath)

# --- Kate (ona) ko'zgu oldida ---
kroot, kate, kmesh = mc.load_character("kate", "Kate.fbx"); sc.render.fps = 24; tame(kmesh, 0.5)
kroot.location = (0, 0.02, 0)
_br = A("Breathing_Idle.fbx"); sc.render.fps = 24
_len = (_br.frame_range[1] - _br.frame_range[0]) * 0.8
mc.add_strip(kate, _br, -10, repeat=math.ceil((NF + 20) / _len) + 1, blend=0)

def head_child(name, loc=(0, 0, 0)):
    """Kate boshiga yopishgan bo'sh ob'ekt; mahalliy o'qlar: X chap, Y tepa, Z old (metr)."""
    e = empty(name); e.location = loc
    c = e.constraints.new("CHILD_OF"); c.target = kate; c.subtarget = "mixamorig:Head"
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False
    c.inverse_matrix = Matrix.Identity(4)
    return e
PIN = Vector((-0.062, 0.188, 0.035))                     # o'ng-tepa (bosh fazosi)
DIR = (PIN - Vector((0, 0.09, 0.0))).normalized()          # sochdan tashqariga
rig = head_child("pluck_rig")
yk = empty("pluck_yank"); yk.parent = rig
pinchE = empty("pinchE", K(PIN + DIR * 0.03)); pinchE.parent = yk
wristE = empty("wristE", K(PIN + Vector((-0.075, -0.075, 0.055)))); wristE.parent = yk
poleE = empty("poleE", (-0.6, 0.15, 1.2)); par(poleE, kroot)
# oq soch (yulinadigan)
WH = mat("white_hair", (0.92, 0.92, 0.9), 0.3, emit=0.25, emit_col=(1, 1, 1))
hp_ = [PIN - DIR * 0.012, PIN + DIR * 0.025, PIN + DIR * 0.05 + Vector((-0.01, 0.005, 0.01)), PIN + DIR * 0.075 + Vector((-0.025, -0.005, 0.02))]
whair = tube("kate_white_hair", [K(p) for p in hp_], 0.00028, WH, parent=yk)
whair.data.bevel_resolution = 2
fa = kate.pose.bones["mixamorig:RightForeArm"]; hb = kate.pose.bones["mixamorig:RightHand"]
ik = fa.constraints.new("IK"); ik.target = wristE; ik.chain_count = 2; ik.use_tail = True
ik.pole_target = poleE; ik.pole_angle = R(-90)
dt = hb.constraints.new("DAMPED_TRACK"); dt.target = pinchE; dt.track_axis = "TRACK_Y"
curlE = empty("curlE", (1.0, 0, 0))
curls = []
for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
    for i in (1, 2, 3):
        pbn = kate.pose.bones.get(f"mixamorig:RightHand{fn}{i}")
        if not pbn: continue
        c_ = pbn.constraints.new("TRANSFORM"); c_.target = curlE; c_.map_from = "LOCATION"; c_.from_min_x = 0; c_.from_max_x = 1
        c_.map_to = "ROTATION"; c_.owner_space = "LOCAL"; c_.target_space = "WORLD"; c_.mix_mode_rot = "AFTER"
        c_.map_to_x_from = "X"; c_.to_min_x_rot = 0
        c_.to_max_x_rot = R({"Index": 38, "Thumb": 22}.get(fn, 75))
        curls.append(c_)
# yulish voqealari: (qo'l ko'tarila boshlaydi, qo'l boshda, [yulish kadrlari], qo'l tusha boshlaydi)
EVENTS = [(26, 40, [62], 72), (452, 466, [485], 494), (669, 680, [692, 716, 740], 750)]
OUTV = DIR * 0.14 + Vector((-0.04, -0.03, 0.03))
def infl(f, v):
    for con in [ik, dt] + curls:
        con.influence = v; con.keyframe_insert("influence", frame=f)
infl(1, 0.0)
hair_vis = []
for r0, r1, yanks, low in EVENTS:
    infl(r0, 0.0); infl(r1, 1.0); infl(low, 1.0); infl(low + 16, 0.0)
    prev = r0
    for i, y in enumerate(yanks):
        yk.location = (0, 0, 0); yk.keyframe_insert("location", frame=y - 1)
        if i == 0: yk.keyframe_insert("location", frame=r0)
        yk.location = OUTV; yk.keyframe_insert("location", frame=y + 2); yk.keyframe_insert("location", frame=y + 7)
        if i + 1 < len(yanks):
            back = y + 15
            yk.location = (0, 0, 0); yk.keyframe_insert("location", frame=back)
            hair_vis.append((prev, y + 8)); prev = back
        else:
            yk.location = OUTV * 1.1; yk.keyframe_insert("location", frame=low + 16)
            hair_vis.append((prev, low + 4))
for fc in P.all_fcurves(yk):
    for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "AUTO"
par(kroot, bath)
vis(bath, rng(2, 10, 14))
vis_only(whair, hair_vis)                              # otadan keyin (CLAUDE.md)

# =================================================================== 2) BOSH TERISI MAKRO (1 birlik = 1 mm)
sk_root = empty("SET_scalp", K(SK))
def scalp_material(name):
    m = mat(name, (0.8, 0.58, 0.5), 0.45)
    b = bsdf(m); nt = m.node_tree; N = nt.nodes; L = nt.links; g = P.G(nt)
    b.inputs["Subsurface Weight"].default_value = 0.5
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25); b.inputs["Subsurface Scale"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 0.2; b.inputs["Coat Roughness"].default_value = 0.3
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 0.9
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.feature = "DISTANCE_TO_EDGE"; vo2.inputs["Scale"].default_value = 4.0
    L.new(tc.outputs["Object"], vo2.inputs["Vector"])
    ns = N.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 6.0; ns.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], ns.inputs["Vector"])
    cre = g.add(g.mul(g.maprange(vo.outputs["Distance"], 0.0, 0.08, 0, 1), 0.7), g.mul(g.maprange(vo2.outputs["Distance"], 0, 0.05, 0, 1), 0.3))
    # kal dog' niqobi: markazdan masofa < bald*R
    x, y, _ = g.objxyz("Object")
    d = g.sqrt(g.add(g.mul(x, x), g.mul(y, y)))
    bv = g.value("BALD", 0.0)
    mask = g.maprange(g.sub(g.mul(bv.outputs[0], 9.0), d), -1.0, 1.5, 0.0, 1.0)
    h = g.add(g.mul(cre, g.sub(1.0, g.mul(mask, 0.8))), g.mul(ns.outputs["Fac"], 0.2))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.inputs["Distance"].default_value = 0.05
    L.new(h, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    colv = g.mixcol(g.maprange(ns.outputs["Fac"], 0.35, 0.65, 0, 1), (0.72, 0.48, 0.4), (0.82, 0.58, 0.48))
    colv = g.mixcol(g.maprange(cre, 0.0, 0.5, 0.3, 0.0), colv, (0.6, 0.38, 0.32))
    colv = g.mixcol(mask, colv, (0.88, 0.56, 0.5))
    L.new(colv, b.inputs["Base Color"])
    L.new(g.add(g.mul(g.maprange(cre, 0, 1, 0.55, 0.4), g.sub(1.0, mask)), g.mul(mask, 0.22)), b.inputs["Roughness"])
    return m
SCALP = scalp_material("scalp_macro")
W, RES = 40.0, 360
rr_ = random.Random(7)
fol = []; sp = 1.45
for i in range(int(W / sp) + 1):
    for j in range(int(W / sp) + 1):
        x = -W / 2 + 0.5 + i * sp + rr_.uniform(-0.4, 0.4); y = -W / 2 + 0.5 + j * sp + rr_.uniform(-0.4, 0.4)
        if abs(x) < W / 2 - 0.3 and abs(y) < W / 2 - 0.3 and math.hypot(x, y) > 0.75: fol.append((x, y))
fol.append((0.0, 0.0))                                # markazdagi (oq soch) teshigi — oxirgisi
fol = np.array(fol)
def base_h(x, y): return 0.15 * np.sin(x * 0.3 + 1.0) * np.cos(y * 0.26) + 0.05 * np.sin(x * 1.1 + y * 0.8)
xs = np.linspace(-W / 2, W / 2, RES); X, Y = np.meshgrid(xs, xs, indexing="ij")
Z = base_h(X, Y)
for (fx, fy) in fol:
    Z -= 0.06 * np.exp(-((X - fx) ** 2 + (Y - fy) ** 2) / 0.02)
bm = bmesh.new(); V = {}
for i in range(RES):
    for j in range(RES):
        V[i, j] = bm.verts.new((X[i, j], Y[i, j], Z[i, j]))
for i in range(RES - 1):
    for j in range(RES - 1):
        bm.faces.new((V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]))
scalp = P.mesh_obj("scalp_patch", bm, SCALP); P.smooth(scalp); scalp.location = SK; par(scalp, sk_root)
HAIR_M = mat("scalp_hair", (0.07, 0.045, 0.03), 0.32, coat=0.5)
nt = HAIR_M.node_tree; g_ = P.G(nt); oi = nt.nodes.new("ShaderNodeObjectInfo")
nt.links.new(g_.mixcol(oi.outputs["Random"], (0.05, 0.032, 0.022), (0.16, 0.1, 0.06)), bsdf(HAIR_M).inputs["Base Color"])
hsrc = P.hair_strand_mesh("scalp_hair_src", 8.5, 0.05, 0.03, 0.3, seg=12, sides=6); hsrc.data.materials.append(HAIR_M)
hsrc.location = (0, 0, -900); hsrc.hide_render = True

def scalp_hair_gn(name, hair_obj, tilt=48.0, bald_r=9.5):
    """Follikula nuqtalarida uzun sochlar. Bald (0..1): markazdan boshlab sochlar to'kiladi."""
    g = P.GN(name)
    bald = g.inp("Bald", default=0.0)
    pts = g.node("GeometryNodeMeshToPoints", Mesh=g.gi.outputs[0]).outputs[0]
    x, y, z = g.sep(g.node("GeometryNodeInputPosition").outputs[0])
    d = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", x, x), g.math("MULTIPLY", y, y)))
    thr = g.math("ADD", g.math("MULTIPLY", bald, bald_r), g.rand(-1.0, 1.0, seed=31))
    fall = g.math("MINIMUM", 1.0, g.math("MAXIMUM", 0.0, g.math("DIVIDE", g.math("SUBTRACT", thr, d), 1.2)))
    pts = g.node("GeometryNodeSetPosition", Geometry=pts, Offset=g.xyz(0, 0, g.math("MULTIPLY", fall, 3.0))).outputs[0]
    a = g.math("ADD", math.radians(tilt), g.rand(-0.25, 0.25, seed=22))
    a = g.math("ADD", a, g.math("MULTIPLY", fall, 0.6))
    yaw = g.math("ADD", g.rand(-0.45, 0.45, seed=23), g.math("MULTIPLY", fall, 1.5))
    e2r = g.node("FunctionNodeEulerToRotation"); g.set(e2r.inputs[0], g.xyz(0, a, yaw))
    hi = g.node("GeometryNodeObjectInfo", Object=hair_obj); hi.transform_space = "ORIGINAL"
    scl = g.math("MULTIPLY", g.rand(0.75, 1.2, seed=24), g.math("SUBTRACT", 1.0, fall))
    inst = g.node("GeometryNodeInstanceOnPoints", Points=pts, Instance=hi.outputs["Geometry"], Rotation=e2r.outputs[0], Scale=scl)
    g.out(inst.outputs[0])
    return g
bm = bmesh.new()
for (fx, fy) in fol[:-1]: bm.verts.new((fx, fy, float(base_h(fx, fy)) - 0.04))
folo = P.mesh_obj("scalp_follicles", bm); folo.location = SK; par(folo, sk_root)
g_sh = scalp_hair_gn("scalp_hair", hsrc)
mod_sh = P.gn_modifier(folo, g_sh)
BALD_V = SCALP.node_tree.nodes["BALD"].outputs[0]
for f, v in ((1, 0.0), (832, 0.0), (905, 1.0)):
    P.gn_set(mod_sh, g_sh, "Bald", v, frame=f); keyv(BALD_V, f, v)
# oq soch (markazda) — 1, 9-kadrlar
WHM = mat("macro_white_hair", (0.95, 0.95, 0.93), 0.25, coat=0.6, emit=0.5, emit_col=(1, 1, 1))
hero = P.hair_strand_mesh("hero_white_hair", 10.0, 0.085, 0.05, 0.18, seg=14, sides=8); hero.data.materials.append(WHM)
hero.location = SK + Vector((0, 0, float(base_h(0, 0)) - 0.05)); hero.rotation_euler = (0, R(24), R(-25)); par(hero, sk_root)
vis(hero, rng(1, 9))
# 7 ta oq soch (afsona): 3-kadrda otilib chiqadi, 4-kadrda qizil chaqnab yo'qoladi
SEVM = mat("seven_hair", (0.95, 0.95, 0.92), 0.28, coat=0.6, emit=0.2, emit_col=(1, 1, 1))
sevE = bsdf(SEVM).inputs["Emission Strength"]; sevC = bsdf(SEVM).inputs["Emission Color"]
for f, v, c in ((1, 0.2, (1, 1, 1)), (134, 0.2, (1, 1, 1)), (138, 6.0, (1.0, 0.05, 0.02)), (150, 3.0, (1.0, 0.05, 0.02))):
    keyv(sevE, f, v); keyv(sevC, f, (*c, 1))
sev = []
for k_ in range(7):
    h7 = P.hair_strand_mesh(f"seven{k_}", 7.0 + 1.2 * (k_ % 3), 0.055, 0.035, 0.22, seg=12, sides=6); h7.data.materials.append(SEVM)
    h7.location = SK + Vector((0, 0, float(base_h(0, 0)) - 0.05)); par(h7, sk_root)
    yaw = k_ * 360 / 7 + 15; tl = 22 + 10 * (k_ % 2)
    h7.rotation_euler = (0, R(tl), R(yaw))
    d0 = 89 + k_                                             # har biri ketma-ket otiladi
    for f, s in ((1, 0.0), (d0, 0.0), (d0 + 5, 1.15), (d0 + 9, 1.0), (140 + k_, 1.0), (152 + k_ * 2, 0.0)):
        h7.scale = (1, 1, s) if s > 0 else (0.0, 0.0, 0.0); h7.keyframe_insert("scale", frame=f)
    sev.append(h7)
    vis(h7, rng(3, 4))
# soch kepaklari (realizm)
flake_m = mat("flake", (0.92, 0.9, 0.85), 0.6)
for i in range(70):
    fx, fy = rr_.uniform(-18, 18), rr_.uniform(-18, 18)
    fl = P.sphere("flake", 1.0, K(SK + Vector((fx, fy, float(base_h(fx, fy)) + 0.01))), flake_m, scale=(rr_.uniform(0.08, 0.3), rr_.uniform(0.06, 0.2), 0.012), seg=10)
    fl.rotation_euler.z = rr_.uniform(0, 6.28); par(fl, sk_root)
area("scalp_key", K(SK + Vector((-14, -12, 10))), (R(55), 0, R(-50)), 9000, 10, (1.0, 0.93, 0.85), sk_root)
area("scalp_rim", K(SK + Vector((8, 16, 6))), (R(-68), 0, R(25)), 12000, 10, (0.75, 0.85, 1.0), sk_root)
area("scalp_fill", K(SK + Vector((12, -8, 8))), (R(55), 0, R(55)), 2000, 10, (1.0, 0.8, 0.7), sk_root)
vis(sk_root, rng(1, 3, 4, 9, 16))
vis_only(hero, rng(1, 9))
for h7 in sev: vis_only(h7, rng(3, 4))

# =================================================================== 3) KESIM (soch follikulasi, 1 birlik = 1 mm)
cx_root = empty("SET_cross", K(CX))
def cmat(name, col, rough=0.5, emit=0.0, sss=0.0, tex=None, tex_scale=3.0, col2=None, bump=0.0, emit_col=None):
    m = mat(name, col, rough, emit=emit, emit_col=emit_col)
    b = bsdf(m)
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.15
    if tex:
        nt = m.node_tree; N = nt.nodes; L = nt.links; g = P.G(nt)
        tc = N.new("ShaderNodeTexCoord")
        t = N.new("ShaderNodeTexWave" if tex == "wave" else "ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = tex_scale
        if tex == "wave": t.inputs["Distortion"].default_value = 9; t.inputs["Detail"].default_value = 6; t.inputs["Detail Scale"].default_value = 2
        L.new(tc.outputs["Object"], t.inputs["Vector"])
        L.new(g.mixcol(t.outputs["Fac"], col, col2 or tuple(c * 0.7 for c in col)), b.inputs["Base Color"])
        if bump:
            bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(t.outputs["Fac"], bp.inputs["Height"])
            L.new(bp.outputs[0], b.inputs["Normal"])
    return m
def redden(m, val_node_name="RED"):
    """Teri qatlami materialiga markaz atrofida qizarish (18-kadr: yiringli shish)."""
    nt = m.node_tree; N = nt.nodes; L = nt.links; g = P.G(nt); b = bsdf(m)
    src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    x, y, z = g.objxyz("Object")
    d = g.sqrt(g.add(g.mul(x, x), g.mul(y, y)))
    v = g.value(val_node_name, 0.0)
    mask = g.mul(g.maprange(d, 0.4, 3.2, 1.0, 0.0), v.outputs[0])
    base = src if src is not None else tuple(b.inputs["Base Color"].default_value)[:3]
    L.new(g.mixcol(mask, base, (0.75, 0.08, 0.06)), b.inputs["Base Color"])
    return v.outputs[0]
CM = dict(
    epi=cmat("epi", (0.86, 0.62, 0.5), 0.5, sss=0.3, tex="wave", tex_scale=6, col2=(0.7, 0.45, 0.35), bump=0.2),
    corneum=cmat("corneum", (0.9, 0.78, 0.65), 0.45, tex="noise", tex_scale=12, bump=0.3),
    dermis=cmat("dermis", (0.88, 0.5, 0.5), 0.6, sss=0.4, tex="wave", tex_scale=1.6, col2=(0.75, 0.38, 0.4), bump=0.25),
    fat=cmat("fat", (0.98, 0.8, 0.32), 0.25, sss=0.5, tex="noise", tex_scale=4, col2=(0.9, 0.68, 0.22), bump=0.1),
    bulb_dark=cmat("bulb_dark", (0.42, 0.22, 0.14), 0.4, sss=0.3),
    bulb_pale=cmat("bulb_pale", (0.9, 0.8, 0.68), 0.4, sss=0.3),
    papilla=cmat("papilla", (0.75, 0.08, 0.08), 0.3, sss=0.3),
    gland=cmat("gland", (0.92, 0.7, 0.2), 0.3, sss=0.3, tex="noise", tex_scale=8, bump=0.3),
    artery=cmat("artery", (0.65, 0.04, 0.04), 0.3, sss=0.3),
    vein=cmat("vein", (0.12, 0.18, 0.55), 0.3, sss=0.3),
    blood=mat("blood", (0.35, 0.0, 0.005), 0.12, coat=0.8),
    scar=cmat("scar", (0.86, 0.84, 0.8), 0.7, sss=0.2, tex="wave", tex_scale=5, col2=(0.7, 0.66, 0.62), bump=0.5),
    bact=mat("bacteria", (0.25, 0.75, 0.15), 0.35, emit=0.4, emit_col=(0.3, 1.0, 0.2)),
    galea=cmat("galea", (0.85, 0.82, 0.78), 0.45, sss=0.2, tex="wave", tex_scale=9, col2=(0.72, 0.68, 0.64), bump=0.3),
    bone=cmat("bone", (0.9, 0.86, 0.74), 0.6, tex="noise", tex_scale=6, col2=(0.72, 0.62, 0.48), bump=0.6),
    pus=cmat("pus", (0.95, 0.85, 0.35), 0.25, sss=0.6, tex="noise", tex_scale=5, col2=(0.85, 0.7, 0.2), bump=0.3),
    dark_hair=mat("dark_shaft", (0.06, 0.035, 0.022), 0.33, coat=0.4),
    white_hair=mat("white_shaft", (0.92, 0.92, 0.88), 0.3, coat=0.4, emit=0.1, emit_col=(1, 1, 1)),
)
bsdf(CM["pus"]).inputs["Emission Color"].default_value = (1.0, 0.85, 0.3, 1)
RED_VALS = [redden(CM["epi"]), redden(CM["corneum"]), redden(CM["dermis"])]
# follikula xaltachasi (ichki yuzasi kesimda ko'rinadi); "GLOW" — 7-kadrda yonadi, "GREY" — 15-kadrda chandiqlanib xiralashadi
def sheath_mat(name, hero_):
    m = cmat(name, (0.85, 0.5, 0.45), 0.4, sss=0.3, tex="wave", tex_scale=7, col2=(0.72, 0.4, 0.36), bump=0.3,
             emit=0.0001, emit_col=(1.0, 0.55, 0.3))
    shE = bsdf(m).inputs["Emission Strength"]
    for f, v in ((1, 0.0), (276, 0.0), (292, 2.6 if hero_ else 1.2), (334, 2.6 if hero_ else 1.2), (342, 0.0)):
        keyv(shE, f, v)
    if not hero_: return m, None
    nt = m.node_tree; g_ = P.G(nt); b_ = bsdf(m)
    greyv = g_.value("GREY", 0.0)
    src_ = b_.inputs["Base Color"].links[0].from_socket
    nt.links.new(g_.mixcol(greyv.outputs[0], src_, (0.55, 0.52, 0.5)), b_.inputs["Base Color"])
    return m, greyv.outputs[0]
SHEATH, _ = sheath_mat("sheath", False)
SHEATH_H, GREY = sheath_mat("sheath_hero", True)

CW, CD = 16.0, 8.0
LAYERS = [("corneum", 0.0, -0.05, "corneum"), ("epidermis", -0.05, -0.25, "epi"), ("dermis", -0.25, -2.65, "dermis"),
          ("hypodermis", -2.65, -4.9, "fat"), ("galea", -4.9, -5.6, "galea"), ("skull", -5.6, -10.0, "bone")]
HERO_TILT = 0.0
FOLS = [(-5.6, 18.0, False), (-2.9, 14.0, False), (0.0, HERO_TILT, True), (2.9, 16.0, False), (5.6, 20.0, False)]
# kesuvchi: har follikula uchun ariqcha (silindr) + piyozcha bo'shlig'i
cbm = bmesh.new()
for fx, tl, hero_ in FOLS:
    rg = 0.27 if hero_ else 0.22
    M = Matrix.Translation(CX + Vector((fx, 0, 0))) @ Matrix.Rotation(R(tl), 4, "Y")
    bmesh.ops.create_cone(cbm, cap_ends=True, segments=32, radius1=rg, radius2=rg, depth=4.4, matrix=M @ Matrix.Translation((0, 0, -1.4)))
    bmesh.ops.create_uvsphere(cbm, u_segments=24, v_segments=12, radius=0.42 if hero_ else 0.34, matrix=M @ Matrix.Translation((0, 0, -3.3)))
cutter = P.mesh_obj("cutter", cbm); cutter.hide_render = True; cutter.display_type = "WIRE"
def bulge(x, y, z):
    return 0.7 * math.exp(-(x * x) / 2.6) * math.exp(-(y * y) / 2.6) * max(0.0, min(1.0, (z + 4.2) / 2.4))
slabs = []
for nm, z0, z1, mk in LAYERS:
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((CW, CD, z0 - z1)), verts=bm.verts)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=40, use_grid_fill=True)
    o = P.mesh_obj(nm, bm, CM[mk], K(CX + Vector((0, CD / 2, (z0 + z1) / 2))))
    o.shape_key_add(name="Basis", from_mix=False)
    kb = o.shape_key_add(name="bulge", from_mix=False); kb.value = 0.0
    for v, d_ in zip(o.data.vertices, kb.data):
        wx, wy, wz = v.co.x, v.co.y + CD / 2, v.co.z + (z0 + z1) / 2
        d_.co.z += bulge(wx, wy, wz)
    if mk in ("galea", "bone"): slabs.append((o, kb)); par(o, cx_root); continue
    bo = o.modifiers.new("cut", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cutter; bo.solver = "EXACT"; bo.use_self = True; bo.use_hole_tolerant = True
    slabs.append((o, kb)); par(o, cx_root)
for o, kb in slabs:
    for f, v in ((1, 0.0), (1005, 0.0), (1055, 1.0)):
        kb.value = v; kb.keyframe_insert("value", frame=f)
for rv in RED_VALS:
    for f, v in ((1, 0.0), (1005, 0.0), (1050, 1.0)): keyv(rv, f, v)
rr2 = random.Random(9)
for i in range(80):                                   # kesimdagi yog' bo'lakchalari
    x = rr2.uniform(-CW / 2 + 0.3, CW / 2 - 0.3); z = rr2.uniform(-4.6, -2.95)
    if any(abs(x - (fx + z * math.tan(R(tl)))) < 0.55 for fx, tl, _ in FOLS): continue
    o = P.sphere("fatcell", rr2.uniform(0.28, 0.48), K(CX + Vector((x, rr2.uniform(-0.15, 0.05), z))), CM["fat"], scale=(1, 0.5, 0.85), seg=16)
    par(o, cx_root)
tube("artery", [K(CX + Vector((x, -0.12, -2.95 + 0.12 * math.sin(x)))) for x in np.linspace(-CW / 2, CW / 2, 9)], 0.15, CM["artery"], None)
tube("vein", [K(CX + Vector((x, 0.3, -3.1 + 0.1 * math.cos(x)))) for x in np.linspace(-CW / 2, CW / 2, 9)], 0.18, CM["vein"], None)
for o_ in (bpy.data.objects["artery"], bpy.data.objects["vein"]): par(o_, cx_root)

hero_parts = {}
for k_, (fx, tl, hero_) in enumerate(FOLS):
    pv = empty(f"fol_pivot{k_}", K(CX + Vector((fx, 0.0, 0.0)))); pv.rotation_euler = (0, R(tl), 0)
    rg = 0.27 if hero_ else 0.22
    # xaltacha: ariqcha ichini qoplagan yarim qobiq (y >= 0)
    bm = bmesh.new(); rings = []
    nz, na = 24, 16
    for i in range(nz + 1):
        z = -3.2 + 3.1 * i / nz
        rings.append([bm.verts.new((rg * 0.98 * math.cos(math.pi * j / na), rg * 0.98 * math.sin(math.pi * j / na), z)) for j in range(na + 1)])
    for i in range(nz):
        for j in range(na):
            bm.faces.new((rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]))
    sh = P.mesh_obj(f"sheath{k_}", bm, SHEATH_H if hero_ else SHEATH); P.smooth(sh); sh.parent = pv
    sh.modifiers.new("solid", "SOLIDIFY").thickness = 0.03
    root = empty(f"fol_root{k_}"); root.parent = pv
    hm_ = CM["white_hair"] if hero_ else CM["dark_hair"]
    shaft = cyl_up(f"shaft{k_}", 0.075, 11.0, hm_, verts=16); shaft.location = (0, 0, -3.15); shaft.parent = root
    bulb = P.sphere(f"bulb{k_}", 0.25, (0, 0, -3.25), CM["bulb_pale"] if hero_ else CM["bulb_dark"], scale=(1, 1, 1.3), seg=24)
    bulb.parent = root
    pap = P.sphere(f"papilla{k_}", 0.13, (0, -0.02, -3.47), CM["papilla"], scale=(1, 1, 1.1), seg=20); pap.parent = pv
    gl = P.sphere(f"gland{k_}", 0.2, (-0.38, 0.05, -0.75), CM["gland"], scale=(1, 0.8, 1.4), seg=16); gl.parent = pv
    # kapillyarlar: pastdan so'rg'ichga kiradigan halqalar
    caps = []
    for c_i, sx in enumerate((-1, 1)):
        pts = [Vector((sx * 0.55, -0.05, -4.0)), Vector((sx * 0.3, -0.06, -3.75)), Vector((sx * 0.08, -0.07, -3.5)), Vector((0, -0.08, -3.42))]
        ct = tube(f"capillary{k_}_{c_i}", [K(p) for p in pts], 0.028, CM["artery"], pv)
        caps.append(ct)
    if hero_: hero_parts = dict(pv=pv, root=root, shaft=shaft, bulb=bulb, pap=pap, sheath=sh, caps=caps)
    par(pv, cx_root)
H = hero_parts
# 8-kadr: soch piyozchadan o'sib chiqadi (time-lapse); 11-kadr: ildizi bilan sug'uriladi
sh_ = H["shaft"]
for f, s in ((1, 1.0), (342, 1.0), (343, 0.02), (346, 0.02), (371, 1.0), (NF, 1.0)):
    sh_.scale = (1, 1, s); sh_.keyframe_insert("scale", frame=f)
all_const(sh_)
for fc in P.all_fcurves(sh_):
    for kp in fc.keyframe_points:
        if 346 <= kp.co[0] < 371: kp.interpolation = "BEZIER"
rt = H["root"]
for f, z in ((1, 0.0), (512, 0.0), (547, 7.5), (548, 7.5), (560, 14.0)):
    rt.location = (0, 0, z); rt.keyframe_insert("location", frame=f)
for fc in P.all_fcurves(rt):
    for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "EASE_IN"
bl = H["bulb"]
for f, s in ((1, 1.3), (512, 1.3), (520, 1.9), (547, 1.6)):
    bl.scale = (1 - 0.15 * (s > 1.3), 1 - 0.15 * (s > 1.3), s); bl.keyframe_insert("scale", frame=f)
vis(H["root"], [(1, 560)])
vis(sh_, [(1, 560)]); vis(bl, [(1, 560)])
# 12: kapillyarlar uziladi (qisqaradi)
for ct in H["caps"]:
    for f, v in ((1, 1.0), (551, 1.0), (556, 0.55), (NF, 0.55)):
        ct.data.bevel_factor_end = v; ct.data.keyframe_insert("bevel_factor_end", frame=f)
# qon tomchilari va ariqchani to'ldiruvchi qon
rr5 = random.Random(21)
pv = H["pv"]
for i in range(34):
    dp = P.sphere(f"blood_drop{i}", rr5.uniform(0.025, 0.06), (0, 0, 0), CM["blood"], seg=12); dp.parent = pv
    t0 = 551 + rr5.randint(0, 14); v0 = Vector((rr5.uniform(-0.6, 0.6), rr5.uniform(-0.9, -0.05), rr5.uniform(0.4, 1.6)))
    p0 = Vector((rr5.uniform(-0.06, 0.06), -0.08, -3.38))
    for f in range(t0, t0 + 40, 2):
        tt = (f - t0) / 24.0
        dp.location = p0 + v0 * tt * 1.4 + Vector((0, 0, -0.9 * tt * tt)); dp.keyframe_insert("location", frame=f)
    vis(dp, [(t0, min(t0 + 38, 593))])
fill = cyl_up("blood_fill", 0.2, 3.2, CM["blood"], verts=24); fill.location = (0, -0.02, -3.45); fill.parent = pv
for f, s in ((1, 0.0), (556, 0.0), (590, 0.35), (668, 0.7), (748, 0.7), (800, 0.15), (923, 0.3), (NF, 0.3)):
    fill.scale = (1, 1, s); fill.keyframe_insert("scale", frame=f)
vis(fill, [(556, 819), (923, NF)])
# yallig'lanish nuri
INF = glow_mat("inflame", (1.0, 0.12, 0.05), 3.0); infV = INF.node_tree.nodes["STR"].outputs[0]
glow = P.sphere("inflame_glow", 1.0, (0, -0.02, -2.4), INF, scale=(1.1, 0.5, 1.5), seg=32); glow.parent = pv
for f, v in ((1, 0.0), (552, 0.0), (555, 1.2), (575, 0.5), (668, 1.2), (748, 0.6), (790, 0.0), (923, 0.0), (970, 0.8),
             (1000, 1.2), (1063, 2.2)):
    keyv(infV, f, v)
vis(glow, [(548, 819), (923, NF)])
# 15: chandiq ariqchani to'ldiradi, xaltacha kulranglashib kichrayadi, so'rg'ich o'ladi
scar = cyl_up("scar", 0.24, 3.25, CM["scar"], verts=24); scar.location = (0, 0.0, -3.5); scar.parent = pv
for f, s in ((1, 0.0), (752, 0.0), (812, 1.0)):
    scar.scale = (1, 1, s); scar.keyframe_insert("scale", frame=f)
vis(scar, rng(15))
for f, v in ((1, 0.0), (752, 0.0), (812, 1.0), (922, 1.0), (923, 0.25)):
    keyv(GREY, f, v)
shh = H["sheath"]
for f, s in ((1, 1.0), (752, 1.0), (815, 0.72), (922, 0.72), (923, 1.0)):
    shh.scale = (s, s, 1); shh.keyframe_insert("scale", frame=f)
pp = H["pap"]
for f, s in ((1, 1.0), (752, 1.0), (815, 0.45), (922, 0.45), (923, 0.8)):
    pp.scale = (s, s, s * 1.1); pp.keyframe_insert("scale", frame=f)
for fc in P.all_fcurves(shh) + P.all_fcurves(pp):
    for kp in fc.keyframe_points:
        if kp.co[0] >= 922: kp.interpolation = "CONSTANT"
# 17: bakteriyalar bo'sh teshikka tushib, ko'payadi
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
for v in bm.verts:
    v.co.z *= 2.4
bact_me = bpy.data.meshes.new("bact"); bm.to_mesh(bact_me); bm.free(); bact_me.materials.append(CM["bact"])
for p_ in bact_me.polygons: p_.use_smooth = True
rr6 = random.Random(33)
for i in range(46):
    b = P.link(bpy.data.objects.new(f"bact{i}", bact_me)); b.parent = pv
    if i < 22:
        t0 = 926 + int(i * 1.6); t1 = t0 + 14; t2 = t1 + 22
        p0 = Vector((rr6.uniform(-1.4, 1.4), rr6.uniform(-1.2, 0.6), rr6.uniform(1.0, 2.4)))
        p1 = Vector((rr6.uniform(-0.12, 0.12), rr6.uniform(-0.12, 0.05), 0.15))
        p2 = Vector((rr6.uniform(-0.15, 0.15), rr6.uniform(-0.15, 0.0), rr6.uniform(-3.1, -1.2)))
        path = [(t0 - 1, p0, 0.0), (t0, p0, 1.0), (t1, p1, 1.0), (t2, p2, 1.0)]
    else:
        t0 = 960 + (i - 22) * 2; t2 = t0 + 30
        p0 = Vector((rr6.uniform(-0.12, 0.12), rr6.uniform(-0.15, 0.0), rr6.uniform(-3.0, -1.4)))
        p2 = p0 + Vector((rr6.uniform(-0.08, 0.08), rr6.uniform(-0.05, 0.02), rr6.uniform(-0.3, 0.3)))
        path = [(t0 - 1, p0, 0.0), (t0 + 6, p0, 1.0), (t2, p2, 1.0)]
    for f, p, s in path:
        b.location = p; b.scale = (0.035 * s, 0.035 * s, 0.035 * s); b.keyframe_insert("location", frame=f); b.keyframe_insert("scale", frame=f)
    b.rotation_euler = (rr6.uniform(0, 6.28), rr6.uniform(0, 6.28), 0); b.keyframe_insert("rotation_euler", frame=923)
    b.rotation_euler = (b.rotation_euler.x + rr6.uniform(-3, 3), b.rotation_euler.y + rr6.uniform(-3, 3), 0); b.keyframe_insert("rotation_euler", frame=NF)
    vis(b, [(923, NF)])
# 18: yiring xaltachasi shishadi
pus = P.sphere("pus", 1.0, (0, -0.05, -1.7), CM["pus"], scale=(0.05, 0.05, 0.05), seg=40); pus.parent = pv
dd = pus.modifiers.new("lumpy", "DISPLACE"); tx = bpy.data.textures.new("pus_t", "CLOUDS"); tx.noise_scale = 0.5; dd.texture = tx; dd.strength = 0.12
for f, s in ((1, 0.05), (999, 0.05), (1040, 1.1), (NF, 1.25)):
    pus.scale = (s, s * 0.75, s * 1.15); pus.keyframe_insert("scale", frame=f)
pusE = bsdf(CM["pus"]).inputs["Emission Strength"]
for f, v in ((1, 0.0), (1000, 0.0), (1050, 0.6)): keyv(pusE, f, v)
vis(pus, rng(18))
# kesim ortidagi teri sirtidagi sochlar
bm = bmesh.new(); rr3 = random.Random(13)
for i in range(140): bm.verts.new((rr3.uniform(-CW / 2 + 0.4, CW / 2 - 0.4), rr3.uniform(0.5, 7.5), 0.0))
back = P.mesh_obj("cross_back_follicles", bm); back.location = CX; par(back, cx_root)
cross_hair = P.hair_strand_mesh("cross_hair_src", 9.0, 0.075, 0.05, 0.25, seg=10, sides=6); cross_hair.data.materials.append(CM["dark_hair"])
cross_hair.location = (0, 0, -700); cross_hair.hide_render = True
P.gn_modifier(back, P.skin_hair_gn("cross_hair", cross_hair, bump_h=0.0, tilt0=48, tilt1=48))
area("cx_key", K(CX + Vector((-4, -14, 9))), (R(55), 0, R(-15)), 12000, 12, (1.0, 0.95, 0.9), cx_root)
area("cx_rim", K(CX + Vector((6, 6, 8))), (R(-45), 0, R(150)), 5000, 8, (0.6, 0.75, 1.0), cx_root)
area("cx_low", K(CX + Vector((5, -9, -6))), (R(115), 0, R(30)), 2500, 8, (1.0, 0.7, 0.6), cx_root)
CXS = rng(5, 6, 7, 8, 11, 12, 13, 15, 17, 18)
vis(cx_root, CXS)
# bolalarga alohida vis — otadan keyin (CLAUDE.md)
for o in bpy.data.objects:
    if o.name.startswith("blood_drop"):
        fc = [f for f in P.all_fcurves(o) if f.data_path == "location"]
        t0 = int(min(k.co[0] for f in fc for k in f.keyframe_points)); vis_only(o, [(t0, min(t0 + 38, 593))])
    elif o.name.startswith("bact"): vis_only(o, [(923, NF)])
vis_only(fill, [(556, 819), (923, NF)]); vis_only(glow, [(548, 819), (923, NF)]); vis_only(scar, rng(15)); vis_only(pus, rng(18))
vis_only(H["root"], [(a, min(b, 560)) for a, b in CXS if a < 560])

# =================================================================== OSMON / DUNYO
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
nt = w.node_tree; N = nt.nodes; L = nt.links
e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mixS = N.new("ShaderNodeMix"); mixS.data_type = "RGBA"; L.new(e.outputs[0], mixS.inputs[6])
bg = N["Background"]; L.new(mixS.outputs[2], bg.inputs[0])
MAC = (0.035, 0.02, 0.016); CXB = (0.004, 0.003, 0.004)
WT = {2: (0, (0, 0, 0), 0.5), 10: (0, (0, 0, 0), 0.5), 14: (0, (0, 0, 0), 0.5)}
for s_ in (1, 3, 4, 9, 16): WT[s_] = (1, MAC, 1.0)
for s_ in (5, 6, 7, 8, 11, 12, 13, 15, 17, 18): WT[s_] = (1, CXB, 1.0)
for s_, (so, col, stg) in WT.items():
    f = S[s_][0]
    keyv(mixS.inputs[0], f, so); keyv(mixS.inputs[7], f, (*col, 1)); keyv(bg.inputs[1], f, stg)
all_const(nt)

# =================================================================== KAMERALAR
cams = {}
def C(n, lens, fstop=None, focus=None):
    c, t = camera(f"cam{n:02d}", lens, fstop, focus); cams[n] = c; return c, t
def follow(c, obj):
    c.constraints["Track To"].target = obj
kh = head_child("kate_head_t", (0, 0.1, 0.06))
kp = head_child("kate_pin_t", K(PIN + Vector((0, -0.01, 0.0))))
# 1: ILGAK — teri sathidan oq sochga tez push-in (16 mm)
c, t = C(1, 16, 1.4)
cam_move(c, t, *S[1], K(SK + Vector((-9.0, -7.5, 2.6))), K(SK + Vector((-3.6, -3.4, 1.5))),
         K(SK + Vector((1.0, -0.3, 2.4))), K(SK + Vector((2.0, -0.8, 4.0))), "out")
# 2: hammom, ko'zgu tomondan yuzga yaqin (DOF); yulishda silkinish
c, t = C(2, 40, 2.0, focus=kp); follow(c, kp)
cam_move(c, t, *S[2], (-0.3, -0.74, 1.62), (-0.2, -0.6, 1.66), (0, 0, 0), (0, 0, 0), "inout",
         shake=[(62, 76, 0.018)], lens=(38, 46, "inout"), tgt_obj_follow=True)
# 3: makro, tepadan: bo'sh teshik -> 7 ta soch otilib chiqadi, crash zoom
c, t = C(3, 24, 2.0)
cam_move(c, t, *S[3], K(SK + Vector((-3.0, -8.0, 7.5))), K(SK + Vector((-2.2, -6.2, 6.2))),
         K(SK + Vector((0, 0, 0.8))), K(SK + Vector((0.6, 0, 2.0))), "inout", shake=[(90, 104, 0.25)], lens=(22, 34, "out"))
# 4: chaqnab yo'qoladi, kamera orqaga siltanadi
c, t = C(4, 30, 2.4)
cam_move(c, t, *S[4], K(SK + Vector((-2.0, -6.0, 5.8))), K(SK + Vector((-4.5, -12.5, 11.0))),
         K(SK + Vector((0.5, 0, 2.2))), K(SK + Vector((0.5, 0, 1.6))), "out", shake=[(137, 150, 0.35)])
# 5: teri sirtidan kesimga sho'ng'ish
c, t = C(5, 24, 4.0)
cam_move(c, t, *S[5], K(CX + Vector((-1.6, -4.0, 6.5))), K(CX + Vector((0.4, -8.5, -1.2))),
         K(CX + Vector((0.0, 2.5, 0.0))), K(CX + Vector((0.0, 0, -1.6))), "inout")
# 6: keng, past burchakdan yonlama siljish
c, t = C(6, 22, 5.6)
cam_move(c, t, *S[6], K(CX + Vector((-6.0, -10.0, -5.5))), K(CX + Vector((-1.5, -9.5, -4.6))),
         K(CX + Vector((-3.0, 0, -2.8))), K(CX + Vector((0.2, 0, -2.4))), "lin")
# 7: xaltacha yonadi, atrofida aylanma
c, t = C(7, 35, 3.2)
for f in range(S[7][0], S[7][1] + 1):
    u = P.ease((f - S[7][0]) / (S[7][1] - S[7][0]), "inout"); a = R(-32 + 60 * u); rd = 6.2 - 1.2 * u
    c.location = CX + Vector((rd * math.sin(a), -rd * math.cos(a), -1.3 - 0.4 * u)); c.keyframe_insert("location", frame=f)
    t.location = CX + Vector((0, 0, -1.9)); t.keyframe_insert("location", frame=f)
# 8: soch o'sadi, kamera u bilan yuqoriga
c, t = C(8, 30, 3.2)
cam_move(c, t, *S[8], K(CX + Vector((1.0, -5.2, -3.6))), K(CX + Vector((1.0, -6.5, 0.9))),
         K(CX + Vector((0, 0, -3.1))), K(CX + Vector((0, 0, 1.0))), "inout")
# 9: makro, teri sathi bo'ylab past sirpanish
c, t = C(9, 20, 1.8)
cam_move(c, t, *S[9], K(SK + Vector((-11, -6.5, 1.1))), K(SK + Vector((3.5, -7.0, 1.3))),
         K(SK + Vector((-6.5, 0.5, 1.4))), K(SK + Vector((7.5, 0.5, 1.8))), "lin")
# 10: hammom, past burchakdan keng (16 mm), yulishda silkinish
c, t = C(10, 16, 4.0)
cam_move(c, t, *S[10], (-0.8, 0.5, 0.5), (-0.62, 0.32, 0.62), (-0.05, -0.35, 1.5), (-0.05, -0.3, 1.55), "inout",
         shake=[(485, 500, 0.02)])
# 11: ildiz bilan sug'uriladi
c, t = C(11, 26, 4.0)
cam_move(c, t, *S[11], K(CX + Vector((0.8, -8.0, -1.8))), K(CX + Vector((0.5, -9.5, 0.6))),
         K(CX + Vector((0, 0, -2.4))), K(CX + Vector((0, 0, 0.8))), "inout")
# 12: so'rg'ich makro, kapillyarlar uziladi
c, t = C(12, 35, 2.8)
cam_move(c, t, *S[12], K(CX + Vector((0.7, -2.9, -2.8))), K(CX + Vector((0.35, -2.2, -3.0))),
         K(CX + Vector((0, 0, -3.3))), K(CX + Vector((0, 0, -3.2))), "out", shake=[(552, 566, 0.08)])
# 13: jarohat: sirtdan pastga sekin push-in
c, t = C(13, 28, 4.0)
cam_move(c, t, *S[13], K(CX + Vector((-1.2, -9.5, 0.6))), K(CX + Vector((-0.4, -5.6, -1.3))),
         K(CX + Vector((0, 0, -0.6))), K(CX + Vector((0, 0, -2.0))), "inout")
# 14: hammom, qayta-qayta yulish, yonlama aylanma
c, t = C(14, 28, 2.8, focus=kh)
for f in range(S[14][0], S[14][1] + 1):
    u = P.ease((f - S[14][0]) / (S[14][1] - S[14][0]), "inout"); a = R(55 - 100 * u)
    c.location = Vector((0.72 * math.sin(a), -0.05 - 0.68 * math.cos(a), 1.5 + 0.08 * u)); c.keyframe_insert("location", frame=f)
    t.location = (-0.02, -0.04, 1.6); t.keyframe_insert("location", frame=f)
# 15: chandiq (time-lapse)
c, t = C(15, 30, 3.2)
cam_move(c, t, *S[15], K(CX + Vector((1.6, -5.8, -1.0))), K(CX + Vector((-1.1, -5.3, -2.1))),
         K(CX + Vector((0, 0, -1.8))), K(CX + Vector((0, 0, -2.0))), "inout")
# 16: kal dog': kamera ko'tarilib aylanadi
c, t = C(16, 24, 2.8)
for f in range(S[16][0], S[16][1] + 1):
    u = P.ease((f - S[16][0]) / (S[16][1] - S[16][0]), "inout"); a = R(-60 + 70 * u); rd = 5.0 + 6.0 * u
    c.location = SK + Vector((2.5 + rd * math.cos(a), rd * math.sin(a), 3.5 + 27.0 * u)); c.keyframe_insert("location", frame=f)
    t.location = SK + Vector((2.5 * u, 0, 0.3)); t.keyframe_insert("location", frame=f)
# 17: bakteriyalar: sirt ustidan teshik ichiga crash zoom
c, t = C(17, 24, 3.2)
cam_move(c, t, *S[17], K(CX + Vector((0.6, -3.2, 3.2))), K(CX + Vector((0.25, -3.6, -1.2))),
         K(CX + Vector((0, 0, 0.4))), K(CX + Vector((0, 0, -2.2))), "inout", lens=(22, 32, "in"))
# 18: yiringli shish, past burchakdan
c, t = C(18, 24, 4.0)
cam_move(c, t, *S[18], K(CX + Vector((-0.8, -9.5, -2.8))), K(CX + Vector((-0.1, -7.2, -1.9))),
         K(CX + Vector((0, 0, -1.5))), K(CX + Vector((0, 0, -0.7))), "inout", shake=[(1030, 1063, 0.06)])
for n, c in cams.items():
    sc.timeline_markers.new(c.name, frame=S[n][0]).camera = c
sc.camera = cams[1]

# =================================================================== RENDER
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", -0.2))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True
            bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{NF}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
