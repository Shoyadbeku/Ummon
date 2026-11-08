# Ko'zga super yelim — Zack D. Films uslubida 47.5 s video (1140 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py va zack_test/qovoq/qovoq.py (mehmonxona, kamera yordamchilari);
# makro ko'z: zack_test/yelim/eye.py (ebbi loyihasidan, "shut" holati qo'shilgan); quvur/egri chiziqlar: zack_test/burish/parts.py
# Assetlar: zack_test/tools/get_yelim.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/yelim/yelim.py --render
# Sinov:  FRAMES=20,100,480,560,800 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, os.path.join(ZT, "qovoq")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
import twitch as TW
import eye as EY
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1140
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (37, "bottles"), (69, "drop"), (125, "close"), (211, "sealed"), (287, "panic"), (357, "pull"),
         (403, "mistake"), (444, "lashes"), (530, "peel"), (587, "good"), (684, "renew"), (768, "tears"), (843, "soft"),
         (894, "days"), (986, "push"), (1067, "open")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "bottles", "panic", "mistake", "good", "days")
MACN = ("drop", "close", "sealed", "pull", "push", "open")
CUTN = ("lashes", "peel", "renew", "tears", "soft")
ROOM = rng(*ROOMN); MACR = rng(*MACN); CUTR = rng(*CUTN)
F_DROP = 101        # tomchi ko'zga tushadi ("yelim tomizib")
F_RIP = 470         # "kipriklarni" — kipriklar uziladi
F_PEEL = 561        # "shilib"
F_PUSH = 1037       # "itarib"
F_OPEN = 1084       # "ochiladi" oldidan

# ---------------- yordamchilar (qovoq.py dan) ----------------
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

# --- divan, jurnal stoli, o'simlik, rasm, javon ---
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.9, 2.15, 0), 0, 1.0))
R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.9, 1.2, 0), 0, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.0, 2.2, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.95, -1.4, 0), 70, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.9, Y1 - 0.03, 1.45), 0, 1.3))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, 0.2, 0), 90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, 0.0, 1.03), 90, 1.0))
R_(plane("rug", (2.2, 1.6), (-0.8, 1.3, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))

def V(*a): return Vector(a)
def text_obj(name, body, loc, rot, size, m, parent=None):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = 0.00005; cu.space_line = 0.9
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.parent = parent
    o.location = loc; o.rotation_euler = [R(a) for a in rot]; cu.materials.append(m)
    return o

# ======================================================================
# 1b) STOLDAGI SHISHALAR: "KO'Z TOMCHISI" va "SUPER YELIM" (bir-biriga juda o'xshash)
# ======================================================================
plastic_m = mat("plastic_w", (0.88, 0.88, 0.86), 0.3, coat=0.4, sss=0.05)
cap_blue = mat("cap_blue", (0.05, 0.25, 0.7), 0.3, coat=0.5)
cap_red = mat("cap_red", (0.7, 0.04, 0.03), 0.3, coat=0.5)
lab_blue = mat("lab_blue", (0.08, 0.35, 0.8), 0.45)
lab_red = mat("lab_red", (0.75, 0.06, 0.04), 0.45)
lab_yel = mat("lab_yel", (0.95, 0.75, 0.1), 0.45)
txt_w = mat("txt_w", (0.95, 0.95, 0.95), 0.4)
txt_k = mat("txt_k", (0.02, 0.02, 0.02), 0.4)
def bottle(name, kind, parent=None, cap=True):
    """uchi (0,0,0) da, tanasi +Z bo'ylab; yorliq -Y tomonda"""
    g = empty(name, (0, 0, 0), parent)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.0009, radius2=0.0048, depth=0.016, location=(0, 0, 0.008))
    o = bpy.context.object; o.name = name + "_noz"; o.data.materials.append(plastic_m); o.parent = g
    for p in o.data.polygons: p.use_smooth = True
    cyl(name + "_neck", 0.0065, 0.007, (0, 0, 0.0195), plastic_m, parent=g)
    box(name + "_body", (0.028, 0.017, 0.06), (0, 0, 0.053), plastic_m, parent=g, bevel=0.005)
    if kind == "drop":
        box(name + "_lab", (0.026, 0.0004, 0.034), (0, -0.0086, 0.054), lab_blue, parent=g)
        text_obj(name + "_t", "KO'Z\nTOMCHISI", (0, -0.0090, 0.054), (90, 180, 0), 0.0058, txt_w, g)
        cm = cap_blue
    else:
        box(name + "_lab", (0.026, 0.0004, 0.034), (0, -0.0086, 0.054), lab_red, parent=g)
        box(name + "_lab2", (0.026, 0.0005, 0.007), (0, -0.0088, 0.041), lab_yel, parent=g)
        text_obj(name + "_t", "SUPER\nYELIM", (0, -0.0092, 0.0575), (90, 180, 0), 0.0064, txt_w, g)
        text_obj(name + "_t2", "TEZ QOTADI", (0, -0.0093, 0.041), (90, 180, 0), 0.0032, txt_k, g)
        cm = cap_red
    if cap:
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.0035, radius2=0.0062, depth=0.022, location=(0, 0, 0.009))
        c = bpy.context.object; c.name = name + "_cap"; c.data.materials.append(cm); c.parent = g
        for p in c.data.polygons: p.use_smooth = True
    return g
BOT_D = V(0.08, -1.27, DESK_TOP + 0.083); BOT_G = V(0.135, -1.29, DESK_TOP + 0.083)
bd_ = bottle("bot_drop", "drop"); bd_.location = BOT_D; bd_.rotation_euler = (R(180), 0, R(-8))
bg_ = bottle("bot_glue", "glue"); bg_.location = BOT_G; bg_.rotation_euler = (R(180), 0, R(10))
BO0, BO1 = S["bottles"]
key(bg_, BO0, loc=tuple(BOT_G)); key(bg_, BO0 + 15, loc=tuple(BOT_G)); key(bg_, BO1, loc=tuple(BOT_G + V(0.03, 0.12, 0.32)))
interp(bg_, "LINEAR")
R_(bd_); R_(bg_)

# ======================================================================
# 2) MEGAN
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
# yopishgan chap ko'z: ko'z soqqasi orolining 1.07x kattalashtirilgan teri nusxasi (dam holatida yasaladi)
body = next(o for o in mmeshes if o.name.endswith("Body"))
_seen, _n = TW._islands(body.data)
_cnt = {}
for i in _seen: _cnt[i] = _cnt.get(i, 0) + 1
_big = max(_cnt, key=_cnt.get)
Wb = body.matrix_world.copy(); Wbi = Wb.inverted()
_near = {}
for i, v in enumerate(body.data.vertices):
    if _seen[i] != _big and ((Wb @ v.co) - TW.EYE_W).length < 0.03: _near[_seen[i]] = _near.get(_seen[i], 0) + 1
EYE_ISL = max(_near, key=_near.get)
lidcap = body.copy(); lidcap.data = body.data.copy(); lidcap.name = "meg_lidcap"; sc.collection.objects.link(lidcap)
bm = bmesh.new(); bm.from_mesh(lidcap.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if _seen[v.index] != EYE_ISL], context="VERTS")
EC = Vector((0.0324, -0.1185, 1.6211))
for v in bm.verts:
    p = Wb @ v.co; v.co = Wbi @ (EC + (p - EC) * float(os.environ.get("CAPS", 1.14)))
bm.to_mesh(lidcap.data); bm.free()
lid_skin = bpy.data.materials.new("lidcap_skin"); lid_skin.use_nodes = True
_b = lid_skin.node_tree.nodes["Principled BSDF"]
_b.inputs["Base Color"].default_value = (0.46, 0.25, 0.19, 1); _b.inputs["Roughness"].default_value = 0.42
_b.inputs["Subsurface Weight"].default_value = 0.1; _b.inputs["Subsurface Scale"].default_value = 0.002
_b.inputs["Coat Weight"].default_value = 0.2       # yelimning yaltirashi
lidcap.data.materials.clear(); lidcap.data.materials.append(lid_skin)
GLUED = rng("panic", "mistake", "good", "days")
vis(lidcap, GLUED, recursive=False)

def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
LOWER = ("Hips", "UpLeg", "Leg", "Foot", "ToeBase", "Toe_End")
def upper(act, drop=()):
    a = act.copy(); a.name = act.name + "_upper" + "".join(drop); a.use_fake_user = True
    for fc in list(mc._fcurves(a)):
        b = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        if any(b.endswith(s) for s in LOWER) or any(d in b for d in drop): mc._channelbag_remove(a, fc)
    return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0, infl=None):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo
    if infl is not None:
        s.use_animated_influence = True; s.influence = infl; s.keyframe_insert("influence", frame=start)
    return s
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)

MEG = Vector((0.6, -0.6, 0.0))
place(mroot, 1, tuple(MEG), 0)
TYP = A_("Typing.fbx")
strip(meg, TYP, 1, repeat=span(TYP, END + 2))
DIS = upper(A_("Sitting_Disbelief.fbx"), drop=("LeftArm", "LeftForeArm", "LeftHand"))
strip(meg, DIS, -8, src=(40, 92), speed=1.0, bi=0, bo=6, infl=float(os.environ.get("DIS_INF", 0.8)))
D3 = upper(A_("Sitting_Disbelief_3.fbx"))
strip(meg, D3, S["panic"][0] - 14, src=(1, 110), speed=1.25, bi=4, bo=6)
CRY = upper(A_("Crying.fbx"))
strip(meg, CRY, S["mistake"][0] - 22, src=(1, 150), speed=1.0, bi=5, bo=6)
REL = upper(A_("Relieved_Sigh.fbx"))
strip(meg, REL, S["good"][0] - 4, src=(1, 90), speed=0.85, bi=4, bo=6)
DA0, DA1 = S["days"]
strip(meg, TYP, DA0, src=(1, 480), speed=5.0, bi=0, bo=0, repeat=1.0)        # timelapse: tez yozadi
# ILGAK: o'ng qo'l chap ko'z ustida yelim naychasini ushlab turadi (IK)
tubeE = child_of_bone("tubeE", meg, "Head", loc=(TW.EYE_H[0] + 0.002, TW.EYE_H[1] + 0.003, TW.EYE_H[2] + 0.045))
htube = bottle("hand_tube", "glue", parent=tubeE, cap=False)
gripE = empty("gripE", (-0.01, -0.02, 0.115), tubeE)
ikR = meg.pose.bones["mixamorig:LeftForeArm"].constraints.new("IK"); ikR.target = gripE; ikR.use_tail = True; ikR.chain_count = 2
for f, v in ((1, 1.0), (S["hook"][1], 1.0), (S["hook"][1] + 1, 0.0)):
    ikR.influence = v; ikR.keyframe_insert("influence", frame=f)
interp(meg, "CONSTANT", "pose.bones")
vis(htube, [S["hook"]])
# naycha uchidan tomchi osilib turadi
glue_m = bpy.data.materials.new("glue_wet"); glue_m.use_nodes = True
_b = glue_m.node_tree.nodes["Principled BSDF"]
_b.inputs["Base Color"].default_value = (1.0, 0.95, 0.8, 1); _b.inputs["Roughness"].default_value = 0.02
_b.inputs["Transmission Weight"].default_value = 0.92; _b.inputs["IOR"].default_value = 1.48; _b.inputs["Coat Weight"].default_value = 0.6
hdrop = sphere("hook_drop", 0.0016, (0, 0, -0.0016), glue_m, scale=(1, 1, 1.25), parent=tubeE)
vis(hdrop, [S["hook"]])
for o in mmeshes: vis(o, ROOM, recursive=False)

# ======================================================================
# 3) MAKRO KO'Z (real o'lcham): tomchi, yopishish, barmoqlar, yelim bo'lagi
# ======================================================================
MAC = V(0.0, 30.0, 1.2)
eye = EY.build_eye("meye", tuple(MAC), states={"shut": (0.0, 0.32), "half": (0.45, 0.75)})
LS = eye["shape"]; eroot = eye["root"]
bskin = mat("macro_skin", (0.56, 0.33, 0.25), 0.5, sss=0.3)
bskin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.002
plane("macro_back", (0.5, 0.5), tuple(MAC + V(0, -0.0045, 0)), bskin, rot=(90, 0, 0))
def EL(p): return MAC + Vector(p)       # ko'z mahalliy -> dunyo (ildiz burilmagan)
# qovoq holati
EY.set_key(eye, "shut", 1, 0.0); EY.set_key(eye, "half", 1, 0.0)
CL0, CL1 = S["close"]
for f, v in ((CL0 + 8, 0.0), (CL0 + 18, 0.12), (CL0 + 24, 0.06), (CL0 + 34, 0.38), (CL0 + 40, 0.3), (CL0 + 52, 0.62),
             (CL0 + 58, 0.55), (CL0 + 68, 0.86), (CL0 + 74, 0.82), (CL0 + 80, 1.0)):
    EY.set_key(eye, "shut", f, v)
OP0, OP1 = S["open"]
for f, v in ((F_OPEN, 1.0), (F_OPEN + 6, 0.9), (F_OPEN + 10, 0.93), (F_OPEN + 22, 0.35), (F_OPEN + 30, 0.0),
             (F_OPEN + 40, 0.0), (F_OPEN + 43, 0.95), (F_OPEN + 47, 0.0)):
    EY.set_key(eye, "shut", f, v)
for f, v in ((1, 0.15), (CL0 + 40, 0.6), (S["push"][0], 0.35), (OP1, 0.2)):
    eye["red"].outputs[0].default_value = v; eye["red"].outputs[0].keyframe_insert("default_value", frame=f)
# naycha (tomchi shoti): uchi ko'z oldida, tanasi kamera tomonga/tepaga
DR0, DR1 = S["drop"]
mtube = bottle("macro_tube", "glue", cap=False)
TIP = EL((0.0015, -0.031, 0.0085))
mtube.location = TIP
_d = Vector((0.15, -0.55, 0.82)).normalized(); mtube.rotation_euler = _d.to_track_quat("Z", "Y").to_euler()
vis(mtube, [S["drop"]])
CORNEA = EL(tuple(EY.on_eye(eye, 0.0008, 0.0012, lift=0.0)))
drop = sphere("macro_drop", 0.0019, tuple(TIP), glue_m, sub=4)
key(drop, 1, loc=tuple(TIP + V(0, 0, -0.0012)), scale=0.05)
key(drop, DR0 + 4, loc=tuple(TIP + V(0, 0, -0.0012)), scale=0.15)
key(drop, F_DROP - 8, loc=tuple(TIP + V(0, 0, -0.0019)), scale=(1.0, 1.0, 1.15))
key(drop, F_DROP - 4, loc=tuple(TIP + V(0, 0.0015, -0.0028)), scale=(0.9, 0.9, 1.35))
key(drop, F_DROP, loc=tuple(CORNEA + V(0, -0.0012, 0.0)), scale=(1.0, 1.25, 0.95))
key(drop, F_DROP + 1, loc=tuple(CORNEA), scale=0.01)
vis(drop, [(DR0, F_DROP)])
splat = sphere("macro_splat", 0.0032, tuple(CORNEA + V(0, 0.0004, 0)), glue_m, scale=(1, 0.22, 1), sub=4)
key(splat, 1, scale=(0.01, 0.01, 0.01)); key(splat, F_DROP, scale=(0.01, 0.01, 0.01))
key(splat, F_DROP + 2, scale=(0.8, 0.3, 0.8)); key(splat, F_DROP + 14, scale=(1.2, 0.16, 1.1)); key(splat, CL0 + 40, scale=(1.5, 0.12, 1.35))
vis(splat, [(F_DROP, CL0 + 46)])
# qotgan yelim: yopiq qovoq cheti bo'ylab sarg'ish qobiq + kipriklar ichida mayda tomchilar
crust_m = bpy.data.materials.new("crust"); crust_m.use_nodes = True
N = crust_m.node_tree.nodes; L = crust_m.node_tree.links; _b = N["Principled BSDF"]
hard = value_node(crust_m, "hard", 0.0)
cmx = N.new("ShaderNodeMix"); cmx.data_type = "RGBA"; cmx.inputs[6].default_value = (1.0, 0.97, 0.85, 1); cmx.inputs[7].default_value = (0.95, 0.72, 0.28, 1)
L.new(hard, cmx.inputs["Factor"]); L.new(cmx.outputs[2], _b.inputs["Base Color"])
L.new(P.math_n(N, L, "SUBTRACT", 0.85, P.math_n(N, L, "MULTIPLY", hard, 0.55)), _b.inputs["Transmission Weight"])
_b.inputs["Roughness"].default_value = 0.12; _b.inputs["Coat Weight"].default_value = 1.0; _b.inputs["IOR"].default_value = 1.5
nzc = N.new("ShaderNodeTexNoise"); nzc.inputs["Scale"].default_value = 2500.0; bpc = N.new("ShaderNodeBump"); bpc.inputs["Strength"].default_value = 0.4
bpc.inputs["Distance"].default_value = 0.00005
L.new(nzc.outputs["Fac"], bpc.inputs["Height"]); L.new(bpc.outputs[0], _b.inputs["Normal"])
crustE = empty("crustE", (0, 0, 0), eroot)
cpts = []
for k in range(17):
    x = -LS.W * 0.93 + 2 * LS.W * 0.93 * k / 16
    z = LS.margin(x, True, 0.0, 0.32)
    cpts.append((x, LS.depth(x, z) - 0.00045, z))
crust = P.tube("crust", cpts, 0.0006, crust_m, crustE)
rr = random.Random(4)
blobs = []
for k in range(14):
    x = rr.uniform(-LS.W * 0.85, LS.W * 0.85); z = LS.margin(x, True, 0.0, 0.32) + rr.uniform(-0.0005, 0.0005)
    blobs.append(sphere(f"crust_b{k}", rr.uniform(0.0004, 0.0008), (x, LS.depth(x, z) - 0.0006, z), crust_m, scale=(1.5, 0.8, 1), sub=2, parent=crustE))
P.tube_r(crust, 1, 0.0); P.tube_r(crust, CL0 + 50, 0.0); P.tube_r(crust, CL0 + 80, 0.0007)
for o in blobs: key(o, 1, scale=0.001); key(o, CL0 + 55, scale=0.001); key(o, CL0 + 80, scale=1.0)
val_key(crust_m, "hard", 1, 0.0); val_key(crust_m, "hard", CL0 + 70, 0.0); val_key(crust_m, "hard", S["sealed"][0] + 40, 1.0)
# yelim bo'lagi ko'chib tushadi
PU0, PU1 = S["push"]
key(crustE, 1, loc=(0, 0, 0), rot=(0, 0, 0)); key(crustE, PU0 + 12, loc=(0, 0, 0), rot=(0, 0, 0))
key(crustE, F_PUSH - 8, loc=(0, -0.0006, -0.0002), rot=(4, 0, 0))
key(crustE, F_PUSH + 4, loc=(0.0005, -0.0035, -0.002), rot=(22, 6, -5))
key(crustE, PU1 + 2, loc=(0.002, -0.009, -0.03), rot=(70, 25, -20))
vis(crustE, [(F_DROP, PU1)])
# barmoqlar (qovoqlarni kuch bilan ochishga urinish): teri cho'ziladi, ochilmaydi
PL0, PL1 = S["pull"]
def frame_dir(d, face=Vector((0, -1, 0))):
    Yl = d.normalized(); Zl = (face - Yl * face.dot(Yl)).normalized(); Xl = Yl.cross(Zl)
    return Matrix((Xl, Yl, Zl)).transposed().to_euler()
fU = EY.build_finger("fingerU", eroot); fU.rotation_euler = frame_dir(Vector((0.7, -0.35, 1.0)), Vector((0.3, -1, 0.2)))
fL = EY.build_finger("fingerL", eroot); fL.rotation_euler = frame_dir(Vector((0.6, -0.4, -1.0)), Vector((0.3, -1, -0.2)))
def lidpt(x, z, out=0.0062): return Vector((x, LS.depth(x, z) - out, z))
U0 = lidpt(0.001, 0.0095); L0 = lidpt(-0.001, -0.0085)
pull = [(PL0, 0.0), (PL0 + 8, 0.25), (PL0 + 12, 0.15), (PL0 + 20, 0.7), (PL0 + 24, 0.5), (PL0 + 32, 1.0), (PL0 + 36, 0.75), (PL1, 1.0)]
for f, k in pull:
    key(fU, f, loc=tuple(U0 + Vector((0, -0.0008 * k, 0.0017 * k))))
    key(fL, f, loc=tuple(L0 + Vector((0, -0.0006 * k, -0.0013 * k))))
    for o in (eye["lids"], eye["lash"]):
        o.scale = (1.0, 1.0, 1.0 + 0.07 * k); o.keyframe_insert("scale", frame=f)
for o in (eye["lids"], eye["lash"]):
    o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=PL1 + 1)
macro_objs = [eroot]
vis(eroot, MACR)
for o in (fU, fL): vis(o, [])          # barmoqlar juda yaqinda "tosh"ga o'xshadi: faqat teri cho'zilishi qoldi
vis(bpy.data.objects["macro_back"], MACR)
for o in (crustE,): vis(o, [(max(F_DROP, MACR[1][0]), PU1)])

# ======================================================================
# 4) KESIM (cutaway): ko'zning 10x kattalashtirilgan yarim kesimi
#    mahalliy o'qlar: old = -Y, tepa = +Z, kesim tekisligi x = 0 (kamera +X tomonda)
# ======================================================================
CUT = V(40.0, 0.0, 1.5)
Re = 0.12
def rc(th):
    s = abs(math.sin(th))
    return Re * (1 + 0.06 * math.cos(s / 0.5 * math.pi / 2) ** 2) if (s < 0.5 and math.cos(th) > 0) else Re
def CP(th_deg, r, x=0.0):
    t = R(th_deg); return CUT + Vector((x, -r * math.cos(t), r * math.sin(t)))
cut_objs = []
def C_(o): cut_objs.append(o); return o
# ko'z soqqasi qobig'i (sklera + shox parda), yarmi
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=96, radius=Re, rotation=(R(90), 0, 0), location=tuple(CUT))
ball = bpy.context.object; ball.name = "cut_ball"; bpy.ops.object.transform_apply(rotation=True)
for v in ball.data.vertices:
    d = v.co.normalized(); s = math.hypot(d.x, d.z)
    if d.y < 0 and s < 0.5: v.co = d * (Re + 0.06 * Re * math.cos(s / 0.5 * math.pi / 2) ** 2)
bm = bmesh.new(); bm.from_mesh(ball.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0.0005], context="VERTS"); bm.to_mesh(ball.data); bm.free()
for p in ball.data.polygons: p.use_smooth = True
so = ball.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.011; so.offset = -1.0
sclera_m = bpy.data.materials.new("cut_sclera"); sclera_m.use_nodes = True
N = sclera_m.node_tree.nodes; L = sclera_m.node_tree.links; _b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); nv = N.new("ShaderNodeVectorMath"); nv.operation = "NORMALIZE"; L.new(tc.outputs["Object"], nv.inputs[0])
sx = N.new("ShaderNodeSeparateXYZ"); L.new(nv.outputs[0], sx.inputs[0])
ss = P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sx.outputs["X"], sx.outputs["X"]), P.math_n(N, L, "MULTIPLY", sx.outputs["Z"], sx.outputs["Z"])))
corn = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", sx.outputs["Y"], 0.0), P.math_n(N, L, "LESS_THAN", ss, 0.5))
cc = N.new("ShaderNodeMix"); cc.data_type = "RGBA"; L.new(corn, cc.inputs["Factor"])
cc.inputs[6].default_value = (0.92, 0.9, 0.86, 1); cc.inputs[7].default_value = (0.62, 0.82, 0.95, 1)
L.new(cc.outputs[2], _b.inputs["Base Color"]); _b.inputs["Roughness"].default_value = 0.3; _b.inputs["Coat Weight"].default_value = 0.6
_b.inputs["Subsurface Weight"].default_value = 0.2; _b.inputs["Subsurface Scale"].default_value = 0.004
L.new(P.math_n(N, L, "MULTIPLY", corn, 0.4), _b.inputs["Emission Strength"]); _b.inputs["Emission Color"].default_value = (0.4, 0.7, 1.0, 1)
ball.data.materials.append(sclera_m); C_(ball)
# kesim yuzasi: halqalar (sklera, tomirli qavat, to'r parda, shishasimon tana)
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=Re - 0.0005, fill_type="NGON", location=tuple(CUT + V(-0.0004, 0, 0)), rotation=(0, R(90), 0))
disc = bpy.context.object; disc.name = "cut_disc"
disc_m = bpy.data.materials.new("cut_disc"); disc_m.use_nodes = True
N = disc_m.node_tree.nodes; L = disc_m.node_tree.links; _b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
rr_ = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sx.outputs["X"], sx.outputs["X"]),
      P.math_n(N, L, "MULTIPLY", sx.outputs["Y"], sx.outputs["Y"]))), Re)
ramp = N.new("ShaderNodeValToRGB"); L.new(rr_, ramp.inputs[0]); E = ramp.color_ramp.elements; ramp.color_ramp.interpolation = "EASE"
E[0].position, E[0].color = 0.0, (0.5, 0.58, 0.68, 1); E[1].position, E[1].color = 0.78, (0.62, 0.66, 0.72, 1)
for pos, col in ((0.81, (0.85, 0.42, 0.3, 1)), (0.85, (0.28, 0.04, 0.03, 1)), (0.9, (0.3, 0.05, 0.04, 1)), (0.915, (0.92, 0.9, 0.86, 1))):
    e = E.new(pos); e.color = col
L.new(ramp.outputs[0], _b.inputs["Base Color"]); _b.inputs["Roughness"].default_value = 0.45; _b.inputs["Coat Weight"].default_value = 0.4
disc.data.materials.append(disc_m); C_(disc)
lens_m = mat("cut_lens", (0.95, 0.85, 0.55), 0.08, coat=1.0, sss=0.2)
C_(sphere("cut_lens", 0.05, tuple(CUT + V(-0.002, -0.072, 0)), lens_m, scale=(0.12, 0.42, 0.95), sub=4))
iris_m = mat("cut_iris", (0.15, 0.3, 0.38), 0.4)
for sgn in (1, -1): C_(box(f"cut_iris{sgn}", (0.006, 0.006, 0.042), tuple(CUT + V(-0.002, -0.094, sgn * 0.073)), iris_m, bevel=0.002))
# shox parda epiteliysi: hujayralar qatlamlari (kesim tekisligi yonida)
cell_m = bpy.data.materials.new("cell"); cell_m.use_nodes = True
N = cell_m.node_tree.nodes; L = cell_m.node_tree.links; _b = N["Principled BSDF"]
_b.inputs["Base Color"].default_value = (0.95, 0.72, 0.7, 1); _b.inputs["Roughness"].default_value = 0.3; _b.inputs["Coat Weight"].default_value = 0.5
_b.inputs["Subsurface Weight"].default_value = 0.3; _b.inputs["Subsurface Scale"].default_value = 0.002
_b.inputs["Emission Color"].default_value = (0.3, 1.0, 0.4, 1)
green = value_node(cell_m, "green", 0.0); L.new(green, _b.inputs["Emission Strength"])
raw_m = bpy.data.materials.new("cell_raw"); raw_m.use_nodes = True
N = raw_m.node_tree.nodes; L = raw_m.node_tree.links; _b = N["Principled BSDF"]
rawv = value_node(raw_m, "raw", 0.0)
rc_ = N.new("ShaderNodeMix"); rc_.data_type = "RGBA"; L.new(rawv, rc_.inputs["Factor"])
rc_.inputs[6].default_value = (0.95, 0.72, 0.7, 1); rc_.inputs[7].default_value = (0.75, 0.04, 0.03, 1)
L.new(rc_.outputs[2], _b.inputs["Base Color"]); _b.inputs["Roughness"].default_value = 0.2; _b.inputs["Coat Weight"].default_value = 0.8
_b.inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1); L.new(P.math_n(N, L, "MULTIPLY", rawv, 1.6), _b.inputs["Emission Strength"])
new_m = mat("cell_new", (0.6, 0.95, 0.6), 0.3, emit=2.0, emit_col=(0.3, 1.0, 0.35), coat=0.5)
glueE = empty("glueE", (0, 0, 0))
cells = []; peel_cells = []; raw_cells = []
rc1 = random.Random(9)
XROWS = (0.0, -0.0055, -0.011, -0.0165, -0.022)
TH_STUCK = 15.0
for li in range(3):
    for xi, x in enumerate(XROWS):
        r0 = None; th = -34.0 + (xi % 2) * 0.9 + li * 0.5
        while th < 34.0:
            r = rc(R(th)) + 0.0028 + li * 0.0043
            cr = 0.0023
            o = sphere(f"cell{li}_{xi}_{len(cells)}", cr, tuple(CP(th, r, x + rc1.uniform(-0.0006, 0.0006))),
                       raw_m if (li == 1 and abs(th) < TH_STUCK - 1) else cell_m,
                       scale=(1.0, 1.0, 1.0), sub=2)
            o.scale = (rc1.uniform(0.9, 1.1), rc1.uniform(0.75, 0.95), rc1.uniform(0.9, 1.1)); o.rotation_euler = (R(th), 0, 0)
            if li == 2 and abs(th) < TH_STUCK: o.parent = glueE; peel_cells.append(o)
            else: C_(o)
            cells.append((li, th, x, o))
            th += math.degrees(2 * cr * 0.98 / r)
# qovoqlar kesimi (prizma): ichki radius = hujayralar ustidan, tashqi = + qalinlik
lid_m = bpy.data.materials.new("cut_lid"); lid_m.use_nodes = True
_b = lid_m.node_tree.nodes["Principled BSDF"]; _b.inputs["Base Color"].default_value = (0.82, 0.55, 0.45, 1)
_b.inputs["Roughness"].default_value = 0.45; _b.inputs["Subsurface Weight"].default_value = 0.35; _b.inputs["Subsurface Scale"].default_value = 0.01
_b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25)
lidcut_m = bpy.data.materials.new("cut_lid_face"); lidcut_m.use_nodes = True
N = lidcut_m.node_tree.nodes; L = lidcut_m.node_tree.links; _b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 30.0; wv.inputs["Distortion"].default_value = 4.0
L.new(tc.outputs["Object"], wv.inputs["Vector"])
lc = N.new("ShaderNodeMix"); lc.data_type = "RGBA"; L.new(wv.outputs["Fac"], lc.inputs["Factor"])
lc.inputs[6].default_value = (0.78, 0.3, 0.25, 1); lc.inputs[7].default_value = (0.92, 0.6, 0.5, 1)
L.new(lc.outputs[2], _b.inputs["Base Color"]); _b.inputs["Roughness"].default_value = 0.5; _b.inputs["Coat Weight"].default_value = 0.3
LID_IN = 0.0175; LID_T = 0.036; XL = -0.16
def lid(name, sgn, th_m=2.6, th_far=88.0):
    prof = []
    n = 26
    for i in range(n + 1):
        th = th_m + (th_far - th_m) * (i / n) ** 1.3
        ri = rc(R(th)) + LID_IN
        prof.append((th, ri))
    outer = [(th, ri + LID_T * min(1.0, 0.55 + (th - th_m) / 12.0)) for th, ri in prof]
    cap = []
    th0, ri0 = prof[0]; ro0 = outer[0][1]; mid = (ri0 + ro0) / 2; hr = (ro0 - ri0) / 2
    for k in range(1, 8):            # yumaloq qovoq cheti
        a = math.pi * k / 8
        cap.append((th0 - math.degrees(math.sin(a) * hr * 0.8 / mid), mid - math.cos(a) * hr))
    ring = list(prof) + list(reversed(outer)) + list(reversed(cap))
    pts2 = [(-r * math.cos(R(sgn * th)), r * math.sin(R(sgn * th))) for th, r in ring]
    me = bpy.data.meshes.new(name); nv_ = len(pts2); verts = []
    for x in (XL, 0.0):
        for y, z in pts2: verts.append((x, y, z))
    faces = [list(range(nv_))[::-1], list(range(nv_, 2 * nv_))]
    for i in range(nv_):
        j = (i + 1) % nv_; faces.append([i, j, nv_ + j, nv_ + i])
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = CUT
    me.materials.append(lid_m); me.materials.append(lidcut_m)
    me.polygons[1].material_index = 1
    for p in me.polygons[2:]: p.use_smooth = True
    return o
lidU = C_(lid("cut_lidU", 1)); lidL = C_(lid("cut_lidL", -1, th_far=80.0))
# kipriklar (yuqorisi yelimga yopishib qoladi -> glueE ga bog'langan)
lash_m = mat("cut_lash", (0.03, 0.02, 0.015), 0.35)
blood_m = mat("cut_blood", (0.6, 0.02, 0.02), 0.2, emit=0.6, emit_col=(1.0, 0.05, 0.03))
up_lashes = []
for k, x in enumerate((-0.004, -0.02, -0.04, -0.065, -0.095, -0.125)):
    for sgn in (1, -1):
        th0 = sgn * 3.2; r0 = rc(R(th0)) + LID_IN + LID_T * 0.42
        base = CP(th0, r0, x) - CUT
        pts = [tuple(base), tuple(base + V(0, -0.028, sgn * 0.004)), tuple(base + V(0, -0.05, sgn * 0.022)), tuple(base + V(0, -0.062, sgn * 0.045))]
        o = P.tube(f"cut_lash{k}{sgn}", pts, 0.0013, lash_m)
        o.location = CUT
        if sgn > 0:
            o.parent = glueE; up_lashes.append(o)
            b_ = sphere(f"cut_root{k}", 0.0022, tuple(CUT + base + V(0, 0.002, 0)), blood_m, parent=glueE); key(b_, 1, scale=0.001); key(b_, F_RIP - 2, scale=0.001); key(b_, F_RIP + 4, scale=1.0); key(b_, S["peel"][1] + 1, scale=0.001)
        else:
            o.parent = lidL; o.location = (0, 0, 0)     # lidL ildizi CUT da: mahalliy koordinata = base
# yelim bo'lagi (kesimda): qovoq chetlari orasida, hujayralarning ustki qatlamiga tegib turadi
gl_m = bpy.data.materials.new("cut_glue"); gl_m.use_nodes = True
N = gl_m.node_tree.nodes; L = gl_m.node_tree.links; _b = N["Principled BSDF"]
soft = value_node(gl_m, "soft", 0.0)
gc = N.new("ShaderNodeMix"); gc.data_type = "RGBA"; L.new(soft, gc.inputs["Factor"])
gc.inputs[6].default_value = (1.0, 0.72, 0.18, 1); gc.inputs[7].default_value = (0.95, 0.94, 0.9, 1)
L.new(gc.outputs[2], _b.inputs["Base Color"])
L.new(P.math_n(N, L, "ADD", 0.08, P.math_n(N, L, "MULTIPLY", soft, 0.45)), _b.inputs["Roughness"])
L.new(P.math_n(N, L, "SUBTRACT", 0.55, P.math_n(N, L, "MULTIPLY", soft, 0.45)), _b.inputs["Transmission Weight"])
_b.inputs["Coat Weight"].default_value = 1.0; _b.inputs["Subsurface Weight"].default_value = 0.3; _b.inputs["Subsurface Scale"].default_value = 0.005
_b.inputs["Emission Color"].default_value = (1.0, 0.6, 0.15, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, soft), 0.25), _b.inputs["Emission Strength"])
GC = CP(0.0, rc(0.0) + 0.0185, -0.075)
cglue = sphere("cut_glue", 1.0, tuple(GC), gl_m, scale=(0.078, 0.011, 0.02), sub=5)
cglue.parent = glueE
gdisp = cglue.modifiers.new("wob", "DISPLACE"); _t = bpy.data.textures.new("gwob", "CLOUDS"); _t.noise_scale = 0.012; gdisp.texture = _t
gdisp.texture_coords = "GLOBAL"; gdisp.strength = 0.0
for th in (-2.0, 2.0):                                         # qovoq chetlari orasidagi "ko'prik"
    sphere(f"cut_glue_e{th}", 1.0, tuple(CP(th * 2.2, rc(0.0) + 0.03, -0.075)), gl_m, scale=(0.078, 0.012, 0.012), sub=4).parent = glueE
# qovoqlar ochiladi (kipriklar uziladi), keyin yelim hujayralarni ko'chirib ketadi; 590 da hammasi joyiga qaytadi
LA0, LA1 = S["lashes"]; PE0, PE1 = S["peel"]
RST = S["good"][0] + 2
for o, a in ((lidU, -16.0), (lidL, 11.0)):
    key(o, 1, rot=(0, 0, 0)); key(o, LA0 + 8, rot=(0, 0, 0)); key(o, LA0 + 16, rot=(a * 0.15, 0, 0)); key(o, LA0 + 20, rot=(a * 0.1, 0, 0))
    key(o, F_RIP - 6, rot=(a * 0.3, 0, 0)); key(o, F_RIP + 3, rot=(a * 0.85, 0, 0)); key(o, LA1, rot=(a, 0, 0))
    key(o, PE1, rot=(a * 1.1, 0, 0)); key(o, RST, rot=(0, 0, 0))
    interp(o, "LINEAR")
key(glueE, 1, loc=(0, 0, 0)); key(glueE, PE0 + 6, loc=(0, 0, 0)); key(glueE, F_PEEL - 3, loc=(0, -0.006, 0.001))
key(glueE, F_PEEL + 8, loc=(0, -0.045, 0.006)); key(glueE, PE1, loc=(0, -0.062, 0.009)); key(glueE, RST, loc=(0, 0, 0))
interp(glueE, "LINEAR")
val_key(raw_m, "raw", 1, 0.0); val_key(raw_m, "raw", F_PEEL - 2, 0.0); val_key(raw_m, "raw", F_PEEL + 6, 1.0)
val_key(raw_m, "raw", RST, 0.0)
# yangilanish: hujayralar yashil yonadi, yangi hujayralar bo'linib chiqadi
RN0, RN1 = S["renew"]
val_key(cell_m, "green", 1, 0.0); val_key(cell_m, "green", RN0 + 2, 0.0)
for f in range(RN0 + 6, RN1, 10): val_key(cell_m, "green", f, 0.8); val_key(cell_m, "green", f + 5, 0.15)
val_key(cell_m, "green", RN1 + 1, 0.0)
rn = random.Random(31)
newc = empty("newcells")
for k, (li, th, x, o) in enumerate([c for c in cells if c[0] == 0 and abs(c[1]) < 30 and c[2] > -0.012]):
    if rn.random() > 0.55: continue
    t_ = R(th + 2.3 * rn.choice((-1, 1)))
    p = CP(math.degrees(t_), rc(t_) + 0.0028 + 0.002, x + 0.0045)
    n_ = sphere(f"newcell{k}", 0.0021, tuple(p), new_m, sub=2, parent=newc)
    f0 = RN0 + 8 + rn.randint(0, 55)
    key(n_, 1, scale=0.001); key(n_, f0, scale=0.001); key(n_, f0 + 6, scale=1.15); key(n_, f0 + 9, scale=1.0)
vis(newc, rng("renew", "tears", "soft"))
# yosh bezi va ko'k yosh tomchilari: qovoq ostidan yelim tagiga oqib boradi
gland_m = mat("gland", (0.85, 0.45, 0.45), 0.35, sss=0.4, coat=0.4)
gland = C_(sphere("cut_gland", 0.017, tuple(CP(58, rc(R(58)) + LID_IN + LID_T * 0.55, -0.004)), gland_m, sub=4))
dg = gland.modifiers.new("d", "DISPLACE"); _t = bpy.data.textures.new("gl_t", "CLOUDS"); _t.noise_scale = 0.006; dg.texture = _t; dg.strength = 0.004
tear_m = mat("tear", (0.3, 0.65, 1.0), 0.05, emit=1.5, emit_col=(0.3, 0.7, 1.0), coat=1.0)
TE0, TE1 = S["tears"]; SO0, SO1 = S["soft"]
tears = empty("tears")
PATH = [(56, LID_IN + 0.006 + LID_T * 0.3), (46, LID_IN - 0.001), (30, LID_IN - 0.002), (14, LID_IN - 0.0025), (6, LID_IN - 0.003), (0, 0.0145)]
rt = random.Random(5)
for k in range(70):
    o = sphere(f"tear{k}", rt.uniform(0.0019, 0.0028), (0, 0, 0), tear_m, sub=2, parent=tears)
    f0 = TE0 - 4 + int(k * 0.95) + rt.randint(0, 3); dur = rt.randint(26, 36); xo = rt.uniform(0.0015, 0.0045)
    endth = rt.uniform(-7, 7); endr = rt.uniform(0.0125, 0.016)
    pts = [CP(th, rc(R(th)) + r_, xo) for th, r_ in PATH[:-1]] + [CP(endth, rc(R(endth)) + endr, xo)]
    key(o, 1, loc=tuple(pts[0]), scale=0.001); key(o, f0 - 1, loc=tuple(pts[0]), scale=0.001)
    for i, p in enumerate(pts): key(o, f0 + int(dur * (i / (len(pts) - 1)) ** 0.9), loc=tuple(p), scale=1.0)
    key(o, SO1, loc=tuple(pts[-1] + V(0, rt.uniform(-0.002, 0.0), 0)), scale=1.25)
    interp(o, "LINEAR", "location")
vis(tears, rng("tears", "soft"))
# yumshash: yelim rangi oqaradi, shishadi va yuzadan ko'tariladi
val_key(gl_m, "soft", 1, 0.0); val_key(gl_m, "soft", SO0 + 4, 0.15); val_key(gl_m, "soft", SO1, 1.0)
gdisp.strength = 0.0; gdisp.keyframe_insert("strength", frame=SO0 + 4); gdisp.strength = 0.006; gdisp.keyframe_insert("strength", frame=SO1)
key(cglue, 1, scale=(0.078, 0.011, 0.02)); key(cglue, SO0 + 4, scale=(0.078, 0.011, 0.02)); key(cglue, SO1, scale=(0.08, 0.016, 0.023))
key(cglue, SO0 + 3, loc=tuple(GC)); key(cglue, SO1, loc=tuple(GC + V(0, -0.006, 0)))
for o in cut_objs + [glueE]: vis(o, CUTR)

# ======================================================================
# 5) KALENDAR (timelapse: 1-KUN .. 4-KUN)
# ======================================================================
CAL = V(0.2, -1.52, DESK_TOP + 0.13)            # stol kalendari
calp = box("cal_paper", (0.26, 0.01, 0.26), tuple(CAL), mat("cal_paper", (0.95, 0.94, 0.9), 0.7))
box("cal_head", (0.26, 0.012, 0.055), tuple(CAL + V(0, 0.001, 0.105)), mat("cal_red", (0.75, 0.05, 0.04), 0.5))
box("cal_stand", (0.26, 0.12, 0.004), tuple(CAL + V(0, -0.04, -0.128)), mat("cal_stand", (0.1, 0.1, 0.1), 0.5), rot=(-10, 0, 0))
ndays = 4; dl = (DA1 - DA0 + 1) / ndays
cal_txt = []
for d in range(ndays):
    t_ = text_obj(f"cal_{d}", f"{d + 1}", tuple(CAL + V(0, 0.007, -0.02)), (90, 0, 180), 0.18, txt_k)
    t2 = text_obj(f"cal_k{d}", "KUN", tuple(CAL + V(0, 0.008, 0.105)), (90, 0, 180), 0.04, txt_w)
    a = int(DA0 + d * dl); b = int(DA0 + (d + 1) * dl) - 1 if d < ndays - 1 else DA1
    rngs = [(a, b)] + ([(DA1 + 1, END)] if d == ndays - 1 else []) + ([(1, DA0 - 1)] if d == 0 else [])
    vis(t_, rngs); vis(t2, rngs)

for o in room_objs: vis(o, ROOM)
for _n in ("cal_paper", "cal_head", "cal_stand"): vis(bpy.data.objects[_n], ROOM)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
headE = child_of_bone("meg_head", meg, "Head")
eyeE = empty("eyeE", TW.EYE_H, headE)
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
# yopishgan qovoq chizig'i: kipriklar + qotgan yelim (Head fazosi: X chap, Y tepa, Z old)
lline_m = mat("lidline", (0.06, 0.035, 0.02), 0.25, coat=0.8)
lpts = []
for k in range(9):
    x = 0.019 + 0.027 * k / 8; u = (x - 0.0325) / 0.0135
    lpts.append((x, TW.EYE_H[1] - 0.0015 - 0.0012 * u * u, TW.EYE_H[2] + 0.0045 - 0.0045 * u * u))
lline = P.tube("meg_lidline", lpts, 0.0006, lline_m, headE)
lline2 = P.tube("meg_lidglue", [(x, y - 0.0004, z + 0.0004) for x, y, z in lpts], 0.0005, crust_m, headE)
for o in (lline, lline2): vis(o, GLUED, recursive=False)
def rig(name, target):
    e = empty(name + "_rig"); c = e.constraints.new("COPY_LOCATION"); c.target = target; return e
def rel_cam(name, target, lens, fstop, offsets, track=None, clip=0.003):
    r_ = rig(name, target)
    c = shot_cam(name, (0, 0, 0), track or target, lens, fstop, focus=track or target, clip=clip)
    c.parent = r_
    path_keys(c, offsets)
    return c
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
H0, H1 = S["hook"]
c = rel_cam("hook", eyeE, 18, 2.8, [(H0, V(0.85, -0.55, 0.62)), (H1, V(0.42, -0.3, 0.38))])
lens_keys(c, [(H0, 16), (H1, 22)])
B0, B1 = S["bottles"]
BM = (BOT_D + BOT_G) / 2 + V(0, 0, -0.035)
c = abs_cam("bottles", [(B0, BM + V(0.12, 0.17, 0.0)), (B1, BM + V(-0.03, 0.14, 0.01))], [(B0, BM + V(0.02, 0, 0)), (B1, BM + V(0.0, 0, 0.01))], 38, 4.0)
DR0, DR1 = S["drop"]
c = abs_cam("drop", [(DR0, EL((0.062, -0.068, -0.006))), (DR1, EL((0.045, -0.058, -0.002)))],
            [(DR0, EL((0.0, -0.02, 0.005))), (F_DROP, EL((0.0, -0.017, 0.003))), (DR1, EL((0.0, -0.014, 0.001)))], 40, 11.0)
CL0, CL1 = S["close"]
c = abs_cam("close", [(CL0, EL((-0.03, -0.072, 0.012))), (CL1, EL((0.028, -0.068, 0.004)))], [(CL0, EL((0, -0.012, 0))), (CL1, EL((0, -0.012, -0.001)))], 50, 11.0)
SE0, SE1 = S["sealed"]
c = abs_cam("sealed", [(SE0, EL((0.0, -0.16, 0.025))), (SE0 + 6, EL((0.0, -0.058, 0.002))), (SE1, EL((0.006, -0.078, 0.006)))],
            [(SE0, EL((0, -0.012, -0.001)))], 45, 11.0)
lens_keys(c, [(SE0, 35), (SE0 + 6, 60), (SE1, 52)]); shake(c, SE0 + 5, SE0 + 16, 0.0025, seed=5)
PL0, PL1 = S["pull"]
c = abs_cam("pull", [(PL0, EL((0.016, -0.11, -0.014))), (PL1, EL((0.006, -0.09, -0.005)))], [(PL0, EL((0, -0.012, 0)))], 42, 11.0)
for f in (PL0 + 20, PL0 + 32): shake(c, f, f + 5, 0.0012, seed=f)
PU0, PU1 = S["push"]
c = abs_cam("push", [(PU0, EL((0.005, -0.072, -0.022))), (PU1, EL((0.0, -0.06, -0.016)))], [(PU0, EL((0, -0.012, -0.003))), (PU1, EL((0, -0.014, -0.006)))], 50, 11.0)
OP0, OP1 = S["open"]
c = abs_cam("open", [(OP0, EL((0.0, -0.05, 0.004))), (F_OPEN + 30, EL((0.0, -0.07, 0.006))), (OP1, EL((0.0, -0.12, 0.012)))], [(OP0, EL((0, -0.012, 0)))], 55, 11.0)
PA0, PA1 = S["panic"]
c = rel_cam("panic", faceT, 16, 2.8, [(PA0, V(0.58, -0.22, -0.42)), (PA1, V(0.45, -0.32, -0.32))])
shake(c, PA0, PA1, 0.008, seed=8, decay=False)
MI0, MI1 = S["mistake"]
c = rel_cam("mistake", faceT, 30, 2.4, [(MI0, V(0.34, -0.3, -0.06)), (MI1, V(0.28, -0.26, -0.04))])
lens_keys(c, [(MI0, 28), (412, 30), (415, 46), (422, 40), (MI1, 42)]); shake(c, 414, 424, 0.006, seed=14)
GO0, GO1 = S["good"]
c = rel_cam("good", faceT, 28, 2.4, [(GO0, V(0.5, -0.55, -0.14)), (GO1, V(0.3, -0.38, -0.07))])
DA0, DA1 = S["days"]
c = abs_cam("days", [(DA0, V(1.75, 0.55, 1.45)), (DA1, V(1.6, 0.35, 1.4))], [(DA0, V(1.0, -1.3, 1.2)), (DA1, V(1.05, -1.35, 1.22))], 17, 5.6)
LA0, LA1 = S["lashes"]
CF = CUT + V(0, -0.14, 0.0)
c = abs_cam("lashes", [(LA0, CF + V(0.5, -0.06, 0.07)), (LA1, CF + V(0.36, -0.07, 0.03))], [(LA0, CF + V(-0.02, 0, 0.0)), (LA1, CF + V(-0.02, -0.01, 0.01))], 35, 8.0)
PE0, PE1 = S["peel"]
c = abs_cam("peel", [(PE0, CF + V(0.36, -0.05, 0.06)), (PE0 + 7, CF + V(0.17, -0.02, 0.02)), (PE1, CF + V(0.15, -0.04, 0.01))],
            [(PE0, CF + V(-0.01, -0.005, 0)), (PE1, CF + V(-0.01, -0.015, 0.002))], 32, 8.0)
lens_keys(c, [(PE0, 28), (PE0 + 7, 40), (PE1, 42)]); shake(c, F_PEEL - 1, F_PEEL + 12, 0.006, seed=21)
RN0, RN1 = S["renew"]
c = abs_cam("renew", [(RN0, CF + V(0.17, -0.02, 0.07)), (RN1, CF + V(0.16, -0.02, -0.06))], [(RN0, CF + V(-0.01, 0.01, 0.035)), (RN1, CF + V(-0.01, 0.01, -0.03))], 35, 8.0)
TE0, TE1 = S["tears"]
c = abs_cam("tears", [(TE0, CUT + V(0.3, -0.1, 0.16)), (TE1, CUT + V(0.27, -0.16, 0.04))],
            [(TE0, CP(48, rc(R(48)) + 0.02, 0) ), (TE1, CP(8, rc(R(8)) + 0.015, 0))], 35, 8.0)
SO0, SO1 = S["soft"]
c = abs_cam("soft", [(SO0, CF + V(0.16, -0.03, 0.03)), (SO1, CF + V(0.13, -0.04, 0.01))], [(SO0, CF + V(-0.01, -0.015, 0)), (SO1, CF + V(-0.01, -0.02, 0))], 38, 8.0)
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
# 7) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_day = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_day.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.012, 0.018, 0.035, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_day.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
def day_curve(f):
    """timelapse: har 'dl' kadrda bir kun; 0 = tun, 1 = tush"""
    t = (f - DA0) / dl
    return max(0.0, math.sin(2 * math.pi * (t + 0.15))) ** 0.8
for f, n in SHOTS:
    ct = n in CUTN
    bg_day.inputs[1].default_value = 0.0 if ct else 1.0; bg_day.inputs[1].keyframe_insert("default_value", frame=f)
    bg_dk.inputs[1].default_value = 1.0 if ct else 0.0; bg_dk.inputs[1].keyframe_insert("default_value", frame=f)
for f in range(DA0, DA1 + 1):
    bg_day.inputs[1].default_value = 0.04 + 0.96 * day_curve(f); bg_day.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(58), 0, R(18))
for f, e in lights_for(ROOM, 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
for f in range(DA0, DA1 + 1):
    sun.data.energy = 4.5 * day_curve(f); sun.data.keyframe_insert("energy", frame=f)
    t = (f - DA0) / dl; sun.rotation_euler = (R(40 + 30 * math.sin(2 * math.pi * (t + 0.15))), 0, R(-60 + 160 * ((t + 0.15) % 1.0)))
    sun.keyframe_insert("rotation_euler", frame=f)
sun.rotation_euler = (R(58), 0, R(18)); sun.keyframe_insert("rotation_euler", frame=DA0 - 1); sun.keyframe_insert("rotation_euler", frame=DA1 + 1)
interp(sun.data, "CONSTANT"); interp(sun, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
def room_keys(e_day, night_floor=0.08):
    ks = lights_for(ROOM, e_day)
    ks = [(f, v) for f, v in ks if not (DA0 <= f <= DA1)]
    ks += [(f, e_day * (night_floor + (1 - night_floor) * day_curve(f))) for f in range(DA0, DA1 + 1)]
    return sorted(ks)
area("win_key", (0.6, Y0 + 0.25, 1.65), 1.6, (0.95, 0.97, 1.0), room_keys(160.0, 0.0), target=FT)
area("ceil_fill", (0.0, 0.6, 2.6), 2.0, (1.0, 0.88, 0.72), room_keys(70.0, 0.25), target=empty("cfT", (0, 0.6, 0)))
area("sofa_fill", (-0.9, 1.0, 2.2), 1.5, (1.0, 0.85, 0.7), room_keys(45.0, 0.2), target=empty("sfT", (-0.9, 2.0, 0.4)))
area("rim_warm", tuple(MEG + V(-0.7, 0.8, 1.7)), 0.6, (1.0, 0.7, 0.45), room_keys(30.0, 1.0), target=FT)
lamp_k = [(1, 0.0)] + [(f, 25.0 * (1 - day_curve(f))) for f in range(DA0, DA1 + 1)] + [(DA1 + 1, 0.0)]
area("lamp_night", (1.2, -1.35, 1.25), 0.25, (1.0, 0.7, 0.4), lamp_k, target=FT)
area("lap_glow", tuple(LAP + V(0, -0.05, 0.25)), 0.3, (0.6, 0.75, 1.0), lights_for(rng("hook", "panic", "mistake", "good", "days"), 6.0), target=FT)
area("face_fill", (1.35, -1.05, 1.45), 0.5, (1.0, 0.9, 0.82), lights_for(rng("panic", "mistake", "good"), 22.0), target=FT)
# makro
MT = empty("macroT", tuple(EL((0, -0.012, 0))))
area("M_key", tuple(EL((-0.12, -0.2, 0.16))), 0.18, (1.0, 0.95, 0.9), lights_for(MACR, 5.0), target=MT)
area("M_fill", tuple(EL((0.16, -0.18, -0.06))), 0.2, (0.9, 0.93, 1.0), lights_for(MACR, 2.0), target=MT)
area("M_top", tuple(EL((0.02, -0.1, 0.2))), 0.1, (1.0, 0.97, 0.92), lights_for(MACR, 2.5), target=MT)
# kesim
CT_ = empty("cutT", tuple(CUT + V(0, -0.13, 0)))
area("C_key", tuple(CUT + V(0.6, -0.45, 0.45)), 0.7, (1.0, 0.95, 0.9), lights_for(CUTR, 45.0), target=CT_)
area("C_fill", tuple(CUT + V(0.5, 0.15, -0.35)), 0.6, (1.0, 0.85, 0.7), lights_for(CUTR, 15.0), target=CT_)
area("C_rim", tuple(CUT + V(-0.25, -0.55, 0.35)), 0.5, (0.35, 0.6, 1.0), lights_for(CUTR, 25.0), target=CT_)

# ======================================================================
# 8) RENDER
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
