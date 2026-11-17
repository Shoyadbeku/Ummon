# Ko'z qovog'i uchishi (miokimiya) — Zack D. Films uslubida 49.4 s video (1186 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py va zack_test/falaj/falaj.py (rentgen tana, miya, asab impulslari);
# procedural yordamchilar: zack_test/burish/parts.py; qovoq shape key: zack_test/qovoq/twitch.py
# Assetlar: zack_test/tools/get_qovoq.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/qovoq/qovoq.py --render
# Sinov:  FRAMES=20,95,330,900,960 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
import twitch as TW
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1186
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (46, "eye"), (108, "rub"), (193, "mom"), (269, "sos"), (384, "ring"), (458, "fibers"),
         (530, "mag"), (583, "coffee"), (647, "tired"), (701, "short"), (769, "pulse"), (873, "zap"),
         (914, "spasm"), (1005, "feel"), (1111, "mom2")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
XRN = ("sos", "ring", "fibers", "mag", "short", "pulse", "zap")
ROOMN = tuple(n for _, n in SHOTS if n not in XRN)
XR = rng(*XRN); ROOM = rng(*ROOMN)
F_PIR = 91          # "pirpirab"
F_SOS = 335         # "SOS"
F_ZAP = 883         # "elektr tokini"
F_TOK = 956         # "tok urgandek"
F_DEY = 1150        # "deyarli"

# ---------------- yordamchilar (falaj.py dan) ----------------
empty = P.empty
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale if isinstance(scale, (tuple, list)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return mc._fcurves(ad.action)

def interp(idb, mode="LINEAR", path=None):
    for fc in fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode

def vis(o, ranges, recursive=True):
    objs = [o] + (list(o.children_recursive) if recursive else [])
    for x in objs:
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def frames_vis(o, frames, lo=1, hi=END):
    """faqat berilgan kadrlarda ko'rinadi (chaqmoq/uchqun miltillashi)"""
    fs = set(frames)
    prev = None
    for f in range(lo, hi + 2):
        on = f in fs
        if on != prev:
            o.hide_render = not on; o.keyframe_insert("hide_render", frame=f); prev = on
    interp(o, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    return m

def pbr(name, folder, scale=1.0, tint=None, proj="BOX"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = proj; t.projection_blend = 0.25
        if non_color: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = img("diff.jpg")
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        L.new(d.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    else:
        L.new(d.outputs[0], b.inputs["Base Color"])
    L.new(img("rough.jpg", True).outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3
        for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def import_gltf(path, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler.z = R(rot_z); root.scale = scale if isinstance(scale, tuple) else (scale,) * 3
    return root

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.01):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 400
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c

def shake(cam, f0, f1, amp, seed=1, decay=True):
    rnd = random.Random(seed)
    base = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); p = cam.location.copy()
        k = amp * ((1 - (f - f0) / max(1, f1 - f0)) ** 2 if decay else 1.0)
        base[f] = p + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
    for f, p in base.items():
        cam.location = p; cam.keyframe_insert("location", frame=f)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def path_keys(o, pts):
    for f, p in pts: key(o, f, loc=tuple(p))

def orbit(cam, f0, f1, center, r0, r1, a0, a1, z0, z1, step=2):
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = (f - f0) / max(1, f1 - f0); t = t * t * (3 - 2 * t) * 0.5 + t * 0.5
        a = R(a0 + (a1 - a0) * t); rr = r0 + (r1 - r0) * t
        key(cam, f, loc=tuple(Vector(center) + Vector((rr * math.sin(a), -rr * math.cos(a), z0 + (z1 - z0) * t))))

def area(name, loc, size, col, keys, target=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    l.visible_camera = cam_vis
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc; l.visible_camera = False
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)

# ======================================================================
# 1) MEHMONXONA (kunduzi): stol, noutbuk, divan, deraza
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.93, 0.86, 0.76))
X0, X1, Y0, Y1, HZ_ = -2.4, 2.4, -1.8, 2.6, 2.7
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
R_(box("wall_L", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_F", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
# orqa devor (stol ortida): katta deraza (x -0.3..1.5, z 0.95..2.25)
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
for x in (WX0 - 0.25, WX1 + 0.25):                   # pardalar
    c_ = R_(box("curtain", (0.45, 0.06, 2.4), (x, Y0 + 0.08, 1.3), mat("curtain_m", (0.86, 0.8, 0.68), 0.9, sss=0.1)))
    d_ = c_.modifiers.new("wave", "WAVE"); d_.height = 0.04; d_.width = 0.12; d_.narrowness = 1; d_.use_y = False; d_.speed = 0
R_(box("baseboard", (X1 - X0, 0.03, 0.1), (0, Y1 - 0.015, 0.05), frame_m))
R_(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X0 + 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
# tashqarida: maysa va daraxtlar (derazadan ko'rinadi)
R_(plane("out_ground", (40, 30), (0, Y0 - 16, -0.3), mat("out_grass", (0.16, 0.32, 0.08), 0.9)))
leaf_m = mat("out_leaves", (0.12, 0.3, 0.07), 0.7, sss=0.1)
for i, (x, y, s) in enumerate(((-1.5, -6, 1.6), (2.5, -8, 2.0), (0.4, -11, 2.2), (-4, -9, 1.8))):
    R_(cyl(f"out_trunk{i}", 0.1 * s, 2.5 * s, (x, y, 1.25 * s - 0.3), mat(f"bark{i}", (0.2, 0.13, 0.08), 0.9), verts=12))
    cr = R_(sphere(f"out_crown{i}", 1.3 * s, (x, y, 2.9 * s), leaf_m, sub=3))
    dm = cr.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new("clt", "CLOUDS"); t_.noise_scale = 0.5; dm.texture = t_; dm.strength = 0.5 * s

# --- stol, stul, noutbuk, lampa ---
DESK = Vector((0.6, -1.3, 0)); DESK_TOP = 0.715
R_(import_gltf(PH + "WoodenTable_01/WoodenTable_01.gltf", tuple(DESK), 0, (1.0, 1.1, 1.3)))
CHAIR0 = Vector((0.6, -0.5, 0))
chair = R_(import_gltf(PH + "modern_arm_chair_01/modern_arm_chair_01.gltf", tuple(CHAIR0), 0, 1.0))
R_(import_gltf(PH + "desk_lamp_arm_01/desk_lamp_arm_01.gltf", (1.25, -1.45, DESK_TOP), 200, 1.0))
lap_m = mat("lap_alu", (0.55, 0.56, 0.6), 0.3, metal=0.9)
key_m = mat("lap_keys", (0.03, 0.03, 0.035), 0.6)
LAP = Vector((0.6, -1.17, DESK_TOP))
R_(box("lap_base", (0.33, 0.23, 0.014), tuple(LAP + Vector((0, 0, 0.007))), lap_m, bevel=0.004))
R_(box("lap_kb", (0.28, 0.1, 0.002), tuple(LAP + Vector((0, -0.04, 0.0145))), key_m))
HINGE = LAP + Vector((0, -0.115, 0.014))
scr_par = R_(empty("scr_par", tuple(HINGE))); scr_par.rotation_euler = (R(-12), 0, 0)
box("lap_lid", (0.33, 0.008, 0.22), (0, -0.004, 0.11), lap_m, parent=scr_par, bevel=0.003)
screen_m = bpy.data.materials.new("screen"); screen_m.use_nodes = True
N = screen_m.node_tree.nodes; L = screen_m.node_tree.links; N.remove(N["Principled BSDF"])
tcs = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tcs.outputs["Object"], sep.inputs[0])
lines = P.math_n(N, L, "GREATER_THAN", P.math_n(N, L, "SINE", P.math_n(N, L, "MULTIPLY", sep.outputs["Y"], 260.0)), 0.1)
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
cmb = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "MULTIPLY", sep.outputs["X"], 18.0), cmb.inputs[0])
L.new(P.math_n(N, L, "FLOOR", P.math_n(N, L, "MULTIPLY", sep.outputs["Y"], 41.0)), cmb.inputs[1]); L.new(cmb.outputs[0], nz.inputs["Vector"])
txt = P.math_n(N, L, "MULTIPLY", lines, P.math_n(N, L, "GREATER_THAN", nz.outputs["Fac"], 0.5))
emc = N.new("ShaderNodeMix"); emc.data_type = "RGBA"; emc.inputs[6].default_value = (0.92, 0.95, 1.0, 1); emc.inputs[7].default_value = (0.15, 0.2, 0.35, 1)
L.new(txt, emc.inputs["Factor"])
em = N.new("ShaderNodeEmission"); L.new(emc.outputs[2], em.inputs["Color"]); em.inputs["Strength"].default_value = 2.0
L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
scr = plane("lap_screen", (0.30, 0.19), (0, 0.0005, 0.115), screen_m, rot=(90, 0, 0), parent=scr_par)
scr.rotation_euler = (R(90), 0, R(180))
# kofe krujkalari (stol ustida) va qo'ldagi krujka
cer = [mat("cer_w", (0.9, 0.9, 0.88), 0.25, coat=0.6), mat("cer_r", (0.6, 0.06, 0.05), 0.3, coat=0.6),
       mat("cer_k", (0.03, 0.03, 0.03), 0.3, coat=0.6), mat("cer_y", (0.85, 0.6, 0.15), 0.3, coat=0.6)]
coffee_m = mat("coffee", (0.05, 0.02, 0.008), 0.08)
def mug(name, loc, m, parent=None):
    g = empty(name, loc, parent)
    cyl(name + "_b", 0.041, 0.095, (0, 0, 0.0475), m, parent=g)
    cyl(name + "_c", 0.037, 0.003, (0, 0, 0.085), coffee_m, parent=g)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.007, location=(0.045, 0, 0.05), rotation=(R(90), 0, 0))
    h = bpy.context.object; h.name = name + "_h"; h.data.materials.append(m); h.parent = g
    return g
for i, p in enumerate(((0.12, -1.42), (0.24, -1.2), (1.0, -1.12), (1.12, -1.3), (0.02, -1.15))):
    R_(mug(f"mug{i}", (p[0], p[1], DESK_TOP), cer[i % 4]))

# --- divan, jurnal stoli, o'simlik, rasm, javon ---
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.9, 2.15, 0), 0, 1.0))
R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.9, 1.2, 0), 0, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.0, 2.2, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.95, -1.4, 0), 70, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.9, Y1 - 0.03, 1.45), 0, 1.3))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, 0.2, 0), 90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, 0.0, 1.03), 90, 1.0))
R_(plane("rug", (2.2, 1.6), (-0.8, 1.3, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))

# ======================================================================
# 2) MEGAN (qiz) va KATE (ona)
# ======================================================================
def soften(meshes, rough=0.5):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = rough
                    n.inputs["Coat Weight"].default_value = 0.0
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften(mmeshes, 0.48)
# qovoq uchishi: dam holatida (root (0,0,0)) shape key yasaladi
twk = TW.add_twitch([o for o in mmeshes if o.name.endswith(("Body", "Eyelashes"))])
for k in twk: k.slider_max = 3.0
kroot, kate, kmeshes = mc.load_character("kate", "Kate.fbx"); sc.render.fps = 24
soften(kmeshes, 0.55)

def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
LOWER = ("Hips", "UpLeg", "Leg", "Foot", "ToeBase", "Toe_End")
def upper(act):
    """faqat tananing yuqori qismi (o'tirgan oyoqlar Typing'dan qoladi)"""
    a = act.copy(); a.name = act.name + "_upper"; a.use_fake_user = True
    for fc in list(mc._fcurves(a)):
        b = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        if any(b.endswith(s) for s in LOWER): mc._channelbag_remove(a, fc)
    return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo
    return s
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)

MEG = Vector((0.6, -0.6, 0.0))
TURN = 38.0                                        # oxirida onasiga qayriladi
place(mroot, 1, tuple(MEG), 0); place(mroot, S["feel"][0] - 1, tuple(MEG), 0); place(mroot, S["feel"][0], tuple(MEG), TURN)
interp(mroot, "CONSTANT")
place(chair, 1, tuple(CHAIR0), 0); place(chair, S["feel"][0] - 1, tuple(CHAIR0), 0)
place(chair, S["feel"][0], tuple(MEG + Vector((0.1 * math.sin(R(TURN)) * -1, 0.1 * math.cos(R(TURN)), 0))), TURN)
interp(chair, "CONSTANT")
TYP = A_("Typing.fbx")
strip(meg, TYP, 1, repeat=span(TYP, END + 2))
CRY = upper(A_("Crying.fbx"))
strip(meg, CRY, 100, src=(1, 150), bi=6, bo=8)                  # qo'llar ko'zga ~124-kadrda
DRK = upper(A_("Drinking.fbx"))
strip(meg, DRK, 563, src=(55, 165), bi=4, bo=8)                # krujka og'izda ~582..635
YAW = upper(A_("Yawn.fbx"))
strip(meg, YAW, 638, src=(18, 180), speed=1.4, bi=4, bo=6)
TAL = A_("Sitting_Talking.fbx")
strip(meg, TAL, S["feel"][0] - 2, src=(80, 400), speed=1.0, bi=2, bo=0, repeat=1.0)

# qo'ldagi krujka (Drinking: chap qo'l)
lhand = child_of_bone("meg_lhand", meg, "LeftHand")
hmug = mug("hand_mug", (0, 0, 0), cer[1], parent=lhand)
hmug.location = (0.0, 0.085, 0.035); hmug.rotation_euler = (0, R(90), 0)
vis(hmug, [(583, 645)])
mug_d = bpy.data.objects["mug0"]

KATE_A = Vector((1.3, 0.55, 0.0)); KATE_B = Vector((1.3, -0.68, 0.0))
place(kroot, 1, tuple(KATE_A), -32); place(kroot, S["feel"][0], tuple(KATE_B), -90)
interp(kroot, "CONSTANT")
THK = A_("Thinking.fbx")
strip(kate, THK, 1, src=(30, 84), repeat=span(THK, END + 2, (30, 84)))
strip(kate, A_("Whatever_Gesture.fbx"), 205, bi=5, bo=5)
strip(kate, A_("Shrugging.fbx"), 236, bi=4, bo=5)
strip(kate, THK, S["feel"][0] - 8, src=(1, 84), bi=4, bo=0)
strip(kate, A_("Shrugging.fbx"), F_DEY - 14, bi=5, bo=6)
KV = rng("mom", "feel", "mom2")
for o in kmeshes: vis(o, KV, recursive=False)

# --- qovoq uchishi kalitlari ---
def tw_key(f, v):
    for k in twk: k.value = v; k.keyframe_insert("value", frame=f)
rt = random.Random(11)
tw_key(1, 0.0)
def flutter(a, b, lo, hi, step=2, gap=0.0):
    f = a
    while f <= b:
        if gap and rt.random() < gap:
            tw_key(f, 0.0); f += step * 2; continue
        tw_key(f, rt.uniform(lo, hi)); tw_key(f + step // 2 if step > 1 else f, rt.uniform(0.0, lo * 0.5))
        f += step
    tw_key(b + 1, 0.0)
tw_key(F_PIR - 4, 0.0)
flutter(F_PIR - 3, S["rub"][1], 0.5, 1.15, step=2, gap=0.15)
tw_key(S["sos"][0], 0.0)
flutter(S["pulse"][0] + 30, S["zap"][1], 0.6, 1.4, step=2)               # rentgenda ham ko'rinadi
flutter(S["spasm"][0], F_TOK - 3, 0.7, 1.4, step=2, gap=0.1)
flutter(F_TOK - 2, S["spasm"][1], 1.4, 2.4, step=2)                       # "tok urgandek"
SPIKES = []
f = S["feel"][0] + 4
while f < S["feel"][1] - 6:                                               # kuchli zarbalar (kamera "punch")
    SPIKES.append(f); f += rt.randint(14, 22)
for f in range(S["feel"][0], S["feel"][1] + 1, 2):
    near = any(0 <= f - s_ < 6 for s_ in SPIKES)
    tw_key(f, rt.uniform(1.2, 1.9) if near else rt.uniform(0.15, 0.5))
flutter(S["mom2"][0], END, 0.5, 1.2, step=2)
for k in twk:
    pass

# ======================================================================
# 3) RENTGEN: shaffof tana, miya, yuz nervi, ko'z atrofidagi halqa mushak
# ======================================================================
headE = child_of_bone("meg_head", meg, "Head")
eyeE = empty("eyeE", TW.EYE_H, headE)                      # chap ko'z oldi (Head fazosi: X chap, Y tepa, Z old)
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
def W(arm, b, f):
    sc.frame_set(f); return arm.matrix_world @ arm.pose.bones["mixamorig:" + b].head
REF = 300
BW = {b: W(meg, b, REF).copy() for b in ("Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "HeadTop_End", "LeftShoulder", "LeftArm",
      "LeftForeArm", "LeftHand", "RightShoulder", "RightArm", "RightForeArm", "RightHand", "LeftUpLeg", "LeftLeg", "RightUpLeg", "RightLeg")}
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
EYE = {n: wpos(eyeE, (a + b) // 2) for n, (a, b) in S.items()}
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items()}
print("EYE hook", EYE["hook"], "EYE feel", EYE["feel"], "HEAD", BW["Head"])

def xr_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", 1.2)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.75, 1.0, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.015), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.6), 0.04, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
xbody = xr_mat("xr_body")
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name or "Sneakers" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
for o in mmeshes: vis(o, ROOM, recursive=False)

# --- miya ---
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
def assign(root, m):
    for o in root.children_recursive:
        if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(m)
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
xb_m = brain_mat2("xbrain_m", 1.0); assign(xbrain, xb_m)
vis(xbrain, XR)
SO0, SO1 = S["sos"]
val_key(xb_m, "glow", 1, 1.0); val_key(xb_m, "red", 1, 0.0)
# S-O-S: 3 qisqa, 3 uzun, 3 qisqa qizil chaqnash
SOS_ON = []
f = F_SOS - 2
for d_on, d_off in [(2, 2)] * 3 + [(5, 2)] * 3 + [(2, 2)] * 3:
    SOS_ON.append((f, f + d_on - 1)); f += d_on + d_off
val_key(xb_m, "glow", F_SOS - 3, 1.0); val_key(xb_m, "red", F_SOS - 3, 0.0)
for a, b in SOS_ON:
    val_key(xb_m, "glow", a, 7.0); val_key(xb_m, "red", a, 1.0)
    val_key(xb_m, "glow", b + 1, 1.2); val_key(xb_m, "red", b + 1, 0.15)
val_key(xb_m, "glow", SO1 + 1, 1.0); val_key(xb_m, "red", SO1 + 1, 0.0)
SH0_, SH1_ = S["short"]; PU0, PU1 = S["pulse"]; ZA0, ZA1 = S["zap"]
val_key(xb_m, "glow", SH0_, 2.0); val_key(xb_m, "red", SH0_, 0.35)
for f in range(SH0_, SH1_, 7): val_key(xb_m, "glow", f, 3.5); val_key(xb_m, "glow", f + 3, 1.6)
for f in range(PU0, ZA1, 3): val_key(xb_m, "glow", f, 4.0); val_key(xb_m, "glow", f + 1, 2.0)
val_key(xb_m, "red", PU0, 0.5); val_key(xb_m, "glow", ZA1 + 1, 1.0); val_key(xb_m, "red", ZA1 + 1, 0.0)
for fc in mc._fcurves(xb_m.node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "CONSTANT"

# --- yuz nervi: miyadan quloq oldidan ko'z halqasiga (Head fazosi) ---
NERVE_H = [(0.03, 0.15, 0.03), (0.028, 0.09, 0.0), (0.03, 0.05, -0.005), (0.05, 0.03, 0.02), (0.066, 0.042, 0.06),
           (0.066, 0.06, 0.09), (0.058, 0.072, 0.112), (0.05, 0.078, 0.124)]
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
nerve_ms = []; nerves = []
for i in range(3):                                            # 3 ta parallel tola
    off = Vector(((i - 1) * 0.0012, (i - 1) * 0.0008, 0))
    pts = [tuple(Vector(p) + off * (0.3 + j / len(NERVE_H))) for j, p in enumerate(NERVE_H)]
    m = train_mat(f"nerve{i}"); nerve_ms.append(m)
    t_ = P.tube(f"nerve{i}", pts, 0.0011 if i != 1 else 0.0016, m, headE, taper=[1.0] * len(pts))
    nerves.append(t_)
NV = rng("sos", "short", "pulse", "zap")
for t_ in nerves: vis(t_, NV, recursive=False)
for i, m in enumerate(nerve_ms):
    val_key(m, "count", 1, 1.0); val_key(m, "amp", 1, 0.0); val_key(m, "phase", 1, -0.5); val_key(m, "glow", 1, 0.5)
    # SOS: har chaqnashda bitta impuls miyadan ko'zga yuguradi
    for a, b in SOS_ON:
        val_key(m, "phase", a, -0.5); val_key(m, "amp", a, 30.0); val_key(m, "phase", a + 10, 0.55)
    val_key(m, "amp", SO1 + 1, 0.0)
    # qisqa tutashuv: impulslar uzilib-uzilib
    val_key(m, "count", SH0_, 2.0); val_key(m, "amp", SH0_, 18.0); val_key(m, "glow", SH0_, 0.8)
    f = SH0_ + i
    while f < SH1_:
        val_key(m, "phase", f, 0.0); val_key(m, "phase", f + 5, 0.6 + rt.uniform(0, 0.3)); f += rt.randint(5, 9)
    # soniyasiga o'nlab: 6 ta impuls poyezdi, tez
    val_key(m, "count", PU0, 6.0); val_key(m, "amp", PU0, 35.0); val_key(m, "glow", PU0, 1.2)
    val_key(m, "phase", PU0, i * 0.3); val_key(m, "phase", ZA1 + 1, i * 0.3 + (ZA1 + 1 - PU0) * 0.55)
    val_key(m, "amp", ZA0, 35.0); val_key(m, "amp", F_ZAP, 80.0); val_key(m, "glow", F_ZAP, 4.0)
    val_key(m, "amp", ZA1 + 1, 0.0); val_key(m, "glow", ZA1 + 1, 0.5)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR" if '"phase"' in fc.data_path else "CONSTANT"
    # SOS bo'limida faza har chaqnashda qaytadan boshlanadi (keskin)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        if '"phase"' in fc.data_path:
            for k in fc.keyframe_points:
                if any(k.co.x == a + 10 for a, b in SOS_ON) or (SH0_ <= k.co.x < SH1_ and k.co.x > SH0_ and False): pass

# --- ko'z atrofidagi halqa mushak (orbicularis oculi) ---
EX, EYY = TW.EYE_H[0], TW.EYE_H[1] + 0.001
def face_z(x, y):
    """yuz yuzasi (Head Z, old) — o'lchangan chuqurlik, x: chap, y: tepa"""
    z = 0.134
    if x > 0.04: z -= (x - 0.04) * 1.2
    if x < 0.012: z += (0.012 - x) * 0.8
    if y > 0.1: z -= (y - 0.1) * 0.3
    return z - 0.003
def ring_mat(name, seed):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.65, 0.06, 0.05, 1); b.inputs["Roughness"].default_value = 0.35
    b.inputs["Coat Weight"].default_value = 0.5; b.inputs["Subsurface Weight"].default_value = 0.2; b.inputs["Subsurface Scale"].default_value = 0.0005
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    gl = value_node(m, "glow", 1.0)
    st = P.math_n(N, L, "POWER", P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SINE", P.math_n(N, L, "MULTIPLY", ua.outputs["Fac"], 180.0 + seed * 7))), 6.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", st, 1.5), 0.6), gl), b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (1.0, 0.18, 0.1, 1)
    out = N["Material Output"]; tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.7
    L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
ring_ms = [ring_mat(f"ring_m{i}", i) for i in range(3)]
ringE = empty("ringE", (0, 0, 0), headE)
rr = random.Random(21)
for k in range(9):
    t = k / 8.0
    a = 0.017 + t * 0.016; b = 0.009 + t * 0.016                # ichki -> tashqi
    pts = []
    n = 40
    ph = rr.uniform(0, 6.28)
    for j in range(n + 1):
        th = j / n * 2 * math.pi
        w = 1 + 0.03 * math.sin(3 * th + ph)
        x = EX + a * w * math.cos(th); y = EYY + b * w * math.sin(th) + (0.002 if math.sin(th) > 0 else 0)
        pts.append((x, y, face_z(x, y) - 0.001 * t))
    P.tube(f"ring{k}", pts, 0.0005 + 0.0002 * rr.random(), ring_ms[k % 3], ringE)
RV = rng("ring", "fibers", "short", "pulse", "zap")
vis(ringE, RV)
RI0, RI1 = S["ring"]; FB0, FB1 = S["fibers"]
for i, m in enumerate(ring_ms):
    val_key(m, "glow", 1, 0.0); val_key(m, "glow", RI0, 0.0)
    for j, f in enumerate(range(RI0 + 4, RI0 + 30, 3)): val_key(m, "glow", f, min(1.0, 0.1 + 0.1 * j))
    val_key(m, "glow", RI1, 1.0)
    # charchaydigan tolalar: miltillab so'nadi
    for f in range(FB0, FB1 + 1, 3): val_key(m, "glow", f, max(0.1, 1.0 - (f - FB0) / (FB1 - FB0) * 0.85) * rt.choice((1, 1, 0.35, 1.2)))
    val_key(m, "glow", SH0_, 0.8)
    for f in range(PU0, ZA1 + 1, 2): val_key(m, "glow", f, rt.choice((3.0, 2.0, 0.8)) if (f // 2 + i) % 2 else 0.5)
    val_key(m, "glow", F_ZAP, 5.0)
    interp(m.node_tree, "CONSTANT")

# --- uchqunlar / chaqmoqlar ---
spark_m = mat("spark", (0.7, 0.85, 1.0), emit=40.0, emit_col=(0.75, 0.88, 1.0))
def bolt(name, a, b, segs=7, jit=0.004, seed=0, r=0.0004, parent=None):
    rb = random.Random(seed); A = Vector(a); B = Vector(b); pts = []
    for i in range(segs + 1):
        t = i / segs; p = A.lerp(B, t)
        if 0 < i < segs: p += Vector((rb.uniform(-jit, jit), rb.uniform(-jit, jit), rb.uniform(-jit, jit)))
        pts.append(tuple(p))
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(spark_m); o.parent = parent
    return o
JUNC = Vector(NERVE_H[4])
bolts = []
for k in range(10):
    d = Vector((rt.uniform(-1, 1), rt.uniform(-1, 1), rt.uniform(-1, 1))).normalized() * rt.uniform(0.008, 0.016)
    o = bolt(f"sbolt{k}", JUNC, JUNC + d, segs=5, jit=0.003, seed=k, r=0.0003, parent=headE)
    fr = [f for f in range(SH0_ + 6, SH1_ + 1) if rt.random() < 0.28]
    frames_vis(o, fr); bolts.append(o)
sparkL = point("spark_l", (0, 0, 0), 0.005, (0.6, 0.8, 1.0), [(1, 0)])
cl_ = sparkL.constraints.new("CHILD_OF"); cl_.target = headE; cl_.inverse_matrix = Matrix.Identity(4); sparkL.location = JUNC
for f in range(SH0_, SH1_ + 1):
    sparkL.data.energy = rt.choice((0, 0, 1.5, 4.0)) if f > SH0_ + 5 else 0; sparkL.data.keyframe_insert("energy", frame=f)
sparkL.data.energy = 0; sparkL.data.keyframe_insert("energy", frame=SH1_ + 1)
interp(sparkL.data, "CONSTANT")
NEND = Vector(NERVE_H[-1])
for k in range(14):                                          # ko'z atrofidagi chaqmoqlar ("elektr toki")
    th = rt.uniform(0, 2 * math.pi); a = 0.03 * rt.uniform(0.7, 1.05); b = 0.024 * rt.uniform(0.7, 1.05)
    x = EX + a * math.cos(th); y = EYY + b * math.sin(th)
    o = bolt(f"zbolt{k}", NEND, (x, y, face_z(x, y) + 0.002), segs=8, jit=0.004, seed=100 + k, r=0.00035, parent=headE)
    fr = [f for f in range(ZA0, ZA1 + 1) if (f >= F_ZAP - 1 and rt.random() < 0.55) or rt.random() < 0.12]
    frames_vis(o, fr)
zapL = point("zap_l", (0, 0, 0), 0.01, (0.7, 0.85, 1.0), [(1, 0)])
cl_ = zapL.constraints.new("CHILD_OF"); cl_.target = headE; cl_.inverse_matrix = Matrix.Identity(4); zapL.location = (EX, EYY, 0.16)
for f in range(ZA0, ZA1 + 1):
    zapL.data.energy = (rt.choice((2.0, 6.0, 10.0)) if f >= F_ZAP - 1 else rt.choice((0, 0, 2.0))); zapL.data.keyframe_insert("energy", frame=f)
zapL.data.energy = 0; zapL.data.keyframe_insert("energy", frame=ZA1 + 1); interp(zapL.data, "CONSTANT")

# --- magniy zarralari (yashil): tanadan chiqib so'nadi ---
MG0, MG1 = S["mag"]
mg_m = mat("mg", (0.3, 1.0, 0.35), emit=6.0, emit_col=(0.35, 1.0, 0.4))
segs = [("Head", "HeadTop_End"), ("Neck", "Head"), ("Spine2", "Neck"), ("Spine1", "Spine2"), ("Spine", "Spine1"), ("Hips", "Spine"),
        ("LeftShoulder", "LeftArm"), ("LeftArm", "LeftForeArm"), ("LeftForeArm", "LeftHand"),
        ("RightShoulder", "RightArm"), ("RightArm", "RightForeArm"), ("RightForeArm", "RightHand")]
mg_grp = empty("mg_grp")
BWm = {b: W(meg, b, (MG0 + MG1) // 2).copy() for b in set(x for s_ in segs for x in s_)}
for i in range(70):
    a, b = rt.choice(segs); p = BWm[a].lerp(BWm[b], rt.random())
    p += Vector((rt.uniform(-0.05, 0.05), rt.uniform(-0.05, 0.05), rt.uniform(-0.04, 0.04)))
    o = sphere(f"mg{i}", rt.uniform(0.003, 0.0065), tuple(p), mg_m, sub=2, parent=mg_grp)
    out_ = (p - BWm["Spine1"]); out_.z *= 0.3; out_ = out_.normalized() * rt.uniform(0.15, 0.4) + Vector((0, 0, rt.uniform(0.05, 0.2)))
    f0 = MG0 + rt.randint(0, 22); f1 = f0 + rt.randint(18, 30)
    key(o, MG0, loc=tuple(p), scale=1.0); key(o, f0, loc=tuple(p), scale=1.0); key(o, f1, loc=tuple(p + out_), scale=0.0)
vis(mg_grp, rng("mag"))

for o in room_objs: vis(o, ROOM)
chair.hide_render = False

# ======================================================================
# 4) KAMERALAR
# ======================================================================
def V(*a): return Vector(a)
def rig(name, target):
    e = empty(name + "_rig"); c = e.constraints.new("COPY_LOCATION"); c.target = target; return e
def rel_cam(name, target, lens, fstop, offsets, track=None, clip=0.003):
    """kamera nishonga (bosh bilan birga yuradi) nisbatan joylashadi"""
    r_ = rig(name, target)
    c = shot_cam(name, (0, 0, 0), track or target, lens, fstop, focus=track or target, clip=clip)
    c.parent = r_
    path_keys(c, offsets)
    return c
eyeRig = eyeE
# 1 ILGAK: past burchakdan keng ob'ektiv, tez yaqinlashish
H0, H1 = S["hook"]
hT = empty("hookT"); path_keys(hT, [(H0, FACE["hook"] + V(0, 0.15, -0.25)), (H1, FACE["hook"] + V(0, 0.05, -0.05))])
c = shot_cam("hook", (0, 0, 0), hT, 16, 3.2, focus=faceT)
path_keys(c, [(H0, V(-0.95, -0.5, 0.22)), (H1, V(-0.32, -0.66, 0.5))])
lens_keys(c, [(H0, 15), (H1, 20)])
# 2 ko'z makro: "pirpirab"
E0, E1 = S["eye"]
c = rel_cam("eye", eyeE, 50, 6.0, [(E0, V(0.07, -0.26, 0.03)), (F_PIR - 4, V(0.035, -0.15, 0.0)), (E1, V(0.025, -0.115, -0.006))])
lens_keys(c, [(E0, 42), (E1, 55)])
# 3 ko'zini ishqalaydi: yondan ergashish
RB0, RB1 = S["rub"]
c = rel_cam("rub", faceT, 35, 2.8, [(RB0, V(0.55, -0.42, 0.05)), (RB1, V(0.36, -0.5, 0.0))])
# 4 ona: Megan boshi oldingi fonda xira, ona keng planda (past burchak)
M0, M1 = S["mom"]
kateHead = child_of_bone("kate_head", kate, "Head")
kT = empty("momT", (0, 0.0, 0.0)); cl_ = kT.constraints.new("COPY_LOCATION"); cl_.target = kateHead
c = shot_cam("mom", (0, 0, 0), kT, 22, 2.8, focus=kateHead)
path_keys(c, [(M0, V(1.0, -1.0, 0.72)), (M1, V(1.02, -0.78, 0.82))])
lens_keys(c, [(M0, 22), (M1, 28)])
# 5 SOS: rentgen bosh, crash zoom
brT = empty("brainT", (0.02, 0.1, 0.04), headE)
c = rel_cam("sos", brT, 26, 3.5, [(SO0, V(0.9, -0.75, 0.35)), (SO0 + 8, V(0.42, -0.34, 0.16)), (F_SOS - 4, V(0.3, -0.28, 0.12)), (SO1, V(0.22, -0.3, 0.1))])
lens_keys(c, [(SO0, 22), (SO0 + 8, 30), (SO1, 34)])
shake(c, SO0 + 7, SO0 + 18, 0.02, seed=3)
for a, b in SOS_ON[3:6]: shake(c, a, a + 3, 0.006, seed=a)
# 6 halqa mushak: ko'z atrofida aylanma
c = rel_cam("ring", eyeE, 40, 4.0, [(RI0, V(0.14, -0.13, 0.07)), ((RI0 + RI1) // 2, V(0.06, -0.16, 0.04)), (RI1, V(-0.02, -0.15, 0.03))])
# 7 tolalar: juda yaqin makro
fibT = empty("fibT", (EX + 0.018, EYY - 0.012, 0.128), headE)
c = rel_cam("fibers", fibT, 32, 8.0, [(FB0, V(0.05, -0.05, -0.03)), (FB1, V(0.025, -0.04, -0.02))], clip=0.001)
# 8 magniy: tanadan orqaga chekinish
chT = empty("magT"); path_keys(chT, [(MG0, BWm["Spine2"] + V(0, 0, 0.12)), (MG1, BWm["Spine2"] + V(0, 0, 0.05))])
c = shot_cam("mag", (0, 0, 0), chT, 24, 4.0, focus=chT)
path_keys(c, [(MG0, BWm["Spine2"] + V(0.45, -0.75, 0.3)), (MG1, BWm["Spine2"] + V(0.8, -1.15, 0.45))])
# 9 kofe: past burchak, krujkalar oldingi fonda
CF0, CF1 = S["coffee"]
c = rel_cam("coffee", faceT, 26, 2.8, [(CF0, V(-0.38, -0.48, -0.36)), (CF1, V(-0.26, -0.4, -0.3))])
# 10 charchoq: tepadan aylanma
TI0, TI1 = S["tired"]
tiT = empty("tiredT"); path_keys(tiT, [(TI0, FACE["tired"] + V(0, 0, -0.05)), (TI1, FACE["tired"] + V(0, 0, -0.08))])
c = shot_cam("tired", (0, 0, 0), tiT, 18, 4.0, focus=faceT)
orbit(c, TI0, TI1, V(FACE["tired"].x, FACE["tired"].y, 0), 0.7, 0.5, -70, -20, FACE["tired"].z + 1.0, FACE["tired"].z + 0.75)
# 11 qisqa tutashuv: quloq oldidagi tugun
jT = empty("juncT", tuple(JUNC), headE)
c = rel_cam("short", jT, 30, 3.5, [(SH0_, V(0.3, -0.12, 0.12)), (SH0_ + 6, V(0.13, -0.06, 0.05)), (SH1_, V(0.11, -0.08, 0.04))])
lens_keys(c, [(SH0_, 26), (SH0_ + 6, 34), (SH1_, 36)])
shake(c, SH0_ + 6, SH1_, 0.004, seed=11, decay=False)
# 12 impulslar: nerv bo'ylab miyadan ko'zga yonlama ergashish
puT = empty("pulseT", NERVE_H[1], headE)
for f, p in ((PU0, NERVE_H[1]), ((PU0 + PU1) // 2, NERVE_H[4]), (PU1, NERVE_H[7])): key(puT, f, loc=p)
c = rel_cam("pulse", puT, 30, 4.0, [(PU0, V(0.28, -0.05, 0.08)), ((PU0 + PU1) // 2, V(0.2, -0.1, 0.06)), (PU1, V(0.1, -0.14, 0.04))])
# 13 elektr toki: ko'zga crash zoom
c = rel_cam("zap", eyeE, 30, 4.0, [(ZA0, V(0.07, -0.3, 0.06)), (F_ZAP - 1, V(0.05, -0.22, 0.04)), (F_ZAP + 2, V(0.025, -0.11, 0.015)), (ZA1, V(0.02, -0.1, 0.012))])
lens_keys(c, [(ZA0, 30), (F_ZAP - 1, 32), (F_ZAP + 2, 42), (ZA1, 45)])
shake(c, F_ZAP, ZA1, 0.006, seed=13, decay=False)
# 14 spazm: haqiqiy ko'z, pastdan makro; "tok urgandek" silkinish
SP0, SP1 = S["spasm"]
c = rel_cam("spasm", eyeE, 50, 6.0, [(SP0, V(-0.02, -0.13, -0.045)), (SP1, V(0.01, -0.105, -0.03))])
lens_keys(c, [(SP0, 46), (F_TOK - 1, 50), (F_TOK + 2, 64), (SP1, 66)])
shake(c, F_TOK, F_TOK + 16, 0.004, seed=14)
# 15 sezgi: yuzga past burchakdan, har zarbada "punch zoom"
FE0, FE1 = S["feel"]
c = rel_cam("feel", faceT, 32, 2.4, [(FE0, V(0.42, -0.08, -0.12)), (FE1, V(0.32, -0.02, -0.08))])
lk = [(FE0, 32)]
for s_ in SPIKES: lk += [(s_ - 1, 32 + (s_ - FE0) * 0.03), (s_ + 1, 40 + (s_ - FE0) * 0.03), (s_ + 7, 33 + (s_ - FE0) * 0.03)]
lk.append((FE1, 36)); lens_keys(c, lk)
# 16 ona yelkasi ortidan: qovoq deyarli ko'rinmaydi
MO0, MO1 = S["mom2"]
c = shot_cam("mom2", (0, 0, 0), eyeE, 50, 2.8, focus=eyeE)
sc.frame_set(MO0); bpy.context.view_layer.update(); KH = kateHead.matrix_world.translation.copy()
path_keys(c, [(MO0, KH + V(0.3, -0.28, 0.02)), (MO1, KH + V(0.2, -0.22, -0.02))])
lens_keys(c, [(MO0, 48), (MO1, 58)])
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 5) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_day = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_day.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.01, 0.03, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_day.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    xr = n in XRN
    bg_day.inputs[1].default_value = 0.0 if xr else 1.0; bg_day.inputs[1].keyframe_insert("default_value", frame=f)
    bg_dk.inputs[1].default_value = 1.0 if xr else 0.0; bg_dk.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(58), 0, R(18))
for f, e in lights_for(ROOM, 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
area("win_key", (0.6, Y0 + 0.25, 1.65), 1.6, (0.95, 0.97, 1.0), lights_for(ROOM, 160.0), target=FT)
area("ceil_fill", (0.0, 0.6, 2.6), 2.0, (1.0, 0.88, 0.72), lights_for(ROOM, 70.0), target=empty("cfT", (0, 0.6, 0)))
area("sofa_fill", (-0.9, 1.0, 2.2), 1.5, (1.0, 0.85, 0.7), lights_for(ROOM, 45.0), target=empty("sfT", (-0.9, 2.0, 0.4)))
area("rim_warm", tuple(MEG + V(-0.7, 0.8, 1.7)), 0.6, (1.0, 0.7, 0.45), lights_for(ROOM, 30.0), target=FT)
area("lap_glow", tuple(LAP + V(0, -0.05, 0.25)), 0.3, (0.6, 0.75, 1.0), lights_for(rng("eye", "spasm", "coffee", "tired"), 6.0), target=FT)
# rentgen
area("X_rim", tuple(BW["Head"] + V(-0.6, 0.6, 0.6)), 0.8, (0.3, 0.6, 1.0), lights_for(XR, 15.0), target=headE)
area("X_key", tuple(BW["Head"] + V(0.7, -0.8, 0.5)), 0.8, (0.9, 0.85, 1.0), lights_for(XR, 8.0), target=headE)

# ======================================================================
# 6) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 5; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 4
sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = False
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("PROBE"): exec(open(os.environ["PROBE"]).read())
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
