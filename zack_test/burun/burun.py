# Burun tukini yulish xavfi — Zack D. Films uslubida 43.9 s video (1056 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py va zack_test/qovoq/qovoq.py (mehmonxona, rentgen bosh, nerv impulslari);
# procedural yordamchilar: zack_test/burish/parts.py (tube, miya, math_n)
# Assetlar: zack_test/tools/get_burun.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/burun/burun.py --render
# Sinov:  FRAMES=20,90,200,400,600 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1056
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (48, "pluck"), (114, "gate"), (222, "forest"), (281, "air"), (361, "catch"), (466, "root"),
         (525, "wound"), (634, "tri"), (716, "veins"), (821, "inhale"), (883, "enter"), (964, "brain")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
XRN = ("gate", "veins", "brain")
TUN = ("forest", "catch")
BLK = ("root", "wound", "enter")
ROOMN = ("hook", "pluck", "air", "tri", "inhale")
XR = rng(*XRN); ROOM = rng(*ROOMN)
F_SHART = 85        # "shart"
F_XAVF = 143        # "xavfli"
F_OCH = 184         # "ochib"
F_ZAMB = 374        # "zamburug'"
F_VIR = 389         # "viruslarni"
F_OCHIQ = 574       # "ochiq teshik"
F_QON = 597         # "qon tomir"
F_OLIM = 665        # "o'lim"
F_MIYA = 782        # "miya qobig'iga"
F_QONGA = 941       # "qonga"
F_YAL = 978         # "yallig'lanishi"
F_XOP = 1016        # "xo'ppozini"

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

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, emit_col=None, sss_scale=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if sss_scale: b.inputs["Subsurface Scale"].default_value = sss_scale
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
def const_mat_keys(m):
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"

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
def V(*a): return Vector(a)

def capsule(name, r, length, m, parent=None):
    """tayoqcha bakteriya: Y o'qi bo'ylab"""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=r)
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        v.co.y += (length / 2 - r) * (1 if v.co.y > 0 else -1)
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def spiky(name, r, m, spike_m=None, parent=None, n=0, seed=0):
    """virus: shar + tikanlar (bitta mesh)"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    ico = bmesh.new(); bmesh.ops.create_icosphere(ico, subdivisions=1, radius=1.0)
    dirs = [v.co.copy().normalized() for v in ico.verts]; ico.free()
    for d in dirs:
        q = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r * 0.12, radius2=r * 0.22, depth=r * 0.55,
                                    matrix=Matrix.Translation(d * r * 1.2) @ q)
        for v in res["verts"]: pass
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); P.link(o, parent)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m)
    return o

def rock(name, r, m, seed, parent=None):
    """chang zarrasi: notekis tosh"""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    rr = random.Random(seed); sx = V(rr.uniform(0.6, 1.3), rr.uniform(0.6, 1.3), rr.uniform(0.6, 1.3))
    for v in bm.verts:
        v.co = V(v.co.x * sx.x, v.co.y * sx.y, v.co.z * sx.z) * (1 + rr.uniform(-0.18, 0.18))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); P.link(o, parent); me.materials.append(m)
    return o

# ======================================================================
# 1) MEHMONXONA (kunduzi): orqada deraza, stol, divan
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
    c_ = R_(box("curtain", (0.45, 0.06, 2.4), (x, Y0 + 0.08, 1.3), mat("curtain_m", (0.86, 0.8, 0.68), 0.9, sss=0.1)))
    d_ = c_.modifiers.new("wave", "WAVE"); d_.height = 0.04; d_.width = 0.12; d_.narrowness = 1; d_.use_y = False; d_.speed = 0
R_(box("baseboard", (X1 - X0, 0.03, 0.1), (0, Y1 - 0.015, 0.05), frame_m))
R_(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X0 + 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
R_(plane("out_ground", (40, 30), (0, Y0 - 16, -0.3), mat("out_grass", (0.16, 0.32, 0.08), 0.9)))
leaf_m = mat("out_leaves", (0.12, 0.3, 0.07), 0.7, sss=0.1)
for i, (x, y, s) in enumerate(((-1.5, -6, 1.6), (2.5, -8, 2.0), (0.4, -11, 2.2), (-4, -9, 1.8))):
    R_(cyl(f"out_trunk{i}", 0.1 * s, 2.5 * s, (x, y, 1.25 * s - 0.3), mat(f"bark{i}", (0.2, 0.13, 0.08), 0.9), verts=12))
    cr = R_(sphere(f"out_crown{i}", 1.3 * s, (x, y, 2.9 * s), leaf_m, sub=3))
    dm = cr.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new("clt", "CLOUDS"); t_.noise_scale = 0.5; dm.texture = t_; dm.strength = 0.5 * s
DESK = Vector((0.6, -1.35, 0)); DESK_TOP = 0.715
R_(import_gltf(PH + "WoodenTable_01/WoodenTable_01.gltf", tuple(DESK), 0, (1.0, 1.1, 1.3)))
R_(import_gltf(PH + "desk_lamp_arm_01/desk_lamp_arm_01.gltf", (1.25, -1.45, DESK_TOP), 200, 1.0))
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.9, 2.15, 0), 0, 1.0))
R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.9, 1.2, 0), 0, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.0, 2.2, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.95, -1.4, 0), 70, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.9, Y1 - 0.03, 1.45), 0, 1.3))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, 0.2, 0), 90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, 0.0, 1.03), 90, 1.0))
R_(plane("rug", (2.2, 1.6), (-0.8, 1.3, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))

# ======================================================================
# 2) MEGAN (qiz): xonaning o'rtasida, +Y tomonga (xonaga) qaraydi, orqasida deraza
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
body = next(o for o in mmeshes if o.name.endswith("Body"))

# --- yuz sirti (Head fazosi) BVH: uchburchakni yuzga yopishtirish uchun (dam holati) ---
bpy.context.view_layer.update()
HM0 = (meg.matrix_world @ meg.pose.bones["mixamorig:Head"].matrix).normalized().inverted()
_vs = [HM0 @ (body.matrix_world @ v.co) for v in body.data.vertices]
FACE_BVH = BVHTree.FromPolygons(_vs, [tuple(p.vertices) for p in body.data.polygons])
def on_face(x, y, lift=0.0012):
    hit = FACE_BVH.ray_cast(V(x, y, 0.3), V(0, 0, -1))
    if hit[0] is None: return V(x, y, 0.13)
    return hit[0] + hit[1] * lift

def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo
    return s
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)

MEG = Vector((0.6, -0.6, 0.0))
mroot.location = MEG; mroot.rotation_euler = (0, 0, R(180))
BRE = A_("Breathing_Idle.fbx")
strip(meg, BRE, 1, repeat=span(BRE, END + 2))
REA = A_("Standing_React_Small_From_Front.fbx")
strip(meg, REA, F_SHART - 4, speed=0.8, bi=2, bo=10)                         # "shart": boshi orqaga silkinadi

headE = child_of_bone("meg_head", meg, "Head")
NOSTRIL = V(0.0088, 0.0525, 0.1636)               # chap burun teshigi (Head fazosi: X chap, Y tepa, Z old)
NOSE_TIP = V(0.0, 0.060, 0.173)
nosE = empty("nostrilE", tuple(NOSTRIL), headE)
faceT = empty("faceT", (0.0, 0.07, 0.12), headE)
noseT = empty("noseT", (0.004, 0.055, 0.165), headE)

# --- burundan chiqib turgan tuk ---
hair_m = mat("nose_hair", (0.035, 0.022, 0.015), 0.35, coat=0.3)
HDIR = V(0.18, -1.0, 0.42).normalized()
def nose_hair(name, base, d, length, r, parent, bend=0.25):
    side = d.cross(V(0, 0, 1)).normalized()
    pts = [tuple(base - d * 0.002), tuple(base + d * length * 0.4 + side * length * 0.05 * bend),
           tuple(base + d * length * 0.75 + side * length * 0.12 * bend), tuple(base + d * length)]
    return P.tube(name, pts, r, hair_m, parent, taper=[1.0, 0.9, 0.6, 0.15])
hairN = nose_hair("hair_out", NOSTRIL, HDIR, 0.0095, 0.00028, headE)
vis(hairN, [(1, F_SHART + 1)])
small_hairs = empty("nose_small_hairs", (0, 0, 0), headE)
rh = random.Random(3)
for i in range(9):
    sx = 1 if i % 2 else -1
    b = V(sx * 0.0088 + rh.uniform(-0.0018, 0.0018), 0.0522 + rh.uniform(-0.001, 0.001), 0.1632 + rh.uniform(-0.002, 0.0015))
    d = V(sx * rh.uniform(0.0, 0.3), -1.0, rh.uniform(0.1, 0.5)).normalized()
    nose_hair(f"hs{i}", b + d * -0.0015, d, rh.uniform(0.0025, 0.004), 0.00016, small_hairs)

# --- pinset (Head fazosida harakatlanadi, qo'l unga IK bilan ergashadi) ---
steel = mat("steel", (0.75, 0.76, 0.78), 0.18, metal=1.0)
twz = empty("tweezer", (0, 0, 0), headE)
def prong(name, sx):
    """uchi (0,0,0) da, tutqich +Y bo'ylab (pinset mahalliy fazosi)"""
    bm = bmesh.new()
    prof = [(0.0, 0.0006), (0.014, 0.0015), (0.12, 0.0028)]          # (y, yarim kenglik)
    vs = []
    for y, w in prof:
        g = 0.0004 + y * 0.045                                       # pinset yoyilishi
        for zz in (-w, w):
            for xx in (0, 0.0007):
                vs.append(bm.verts.new((sx * (g + xx), y, zz)))
    bm.verts.ensure_lookup_table()
    for i in range(len(prof) - 1):
        a = i * 4; b = a + 4
        for (p, q) in ((0, 1), (1, 3), (3, 2), (2, 0)):
            bm.faces.new((bm.verts[a + p], bm.verts[a + q], bm.verts[b + q], bm.verts[b + p]))
    bm.faces.new([bm.verts[i] for i in (0, 1, 3, 2)]); bm.faces.new([bm.verts[8 + i] for i in (2, 3, 1, 0)])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); P.link(o, twz); me.materials.append(steel)
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = 0.0002; bv.segments = 2
    return o
prL = prong("prong_L", 1); prR = prong("prong_R", -1)
# yo'nalish: uchi burun teshigi oldida, tutqich o'ng-pastga-oldinga
TW_DIR = V(-0.8, -0.55, 0.22).normalized()
def tw_rot(d):
    q = d.to_track_quat("Y", "Z"); return q.to_euler()
TW_ROT = tw_rot(TW_DIR)
GRIP = NOSTRIL + HDIR * 0.0065                       # tukning qisiladigan joyi
def tw_key(f, tip, close):
    twz.location = tip; twz.keyframe_insert("location", frame=f)
    twz.rotation_euler = TW_ROT; twz.keyframe_insert("rotation_euler", frame=f)
    for o, sx in ((prL, 1), (prR, -1)):
        o.location = (-sx * 0.0004 * close - sx * 0.0018 * close * 0, 0, 0)
        o.rotation_euler = (0, 0, R(sx * 1.6 * close)); o.keyframe_insert("rotation_euler", frame=f)
tw_key(1, GRIP + TW_DIR * 0.20 + V(0, -0.08, 0), 0.0)
tw_key(30, GRIP + TW_DIR * 0.025, 0.0)
tw_key(62, GRIP + TW_DIR * 0.004, 0.0)
tw_key(74, GRIP, 0.0)
tw_key(80, GRIP, 1.0)
tw_key(F_SHART, GRIP + HDIR * 0.001, 1.0)
tw_key(F_SHART + 3, GRIP + HDIR * 0.03 + TW_DIR * 0.02, 1.0)
tw_key(F_SHART + 20, GRIP + HDIR * 0.05 + TW_DIR * 0.06, 1.0)
tw_key(S["pluck"][1] + 1, GRIP + TW_DIR * 0.25 + V(0, -0.15, 0), 1.0)
vis(twz, [(1, S["pluck"][1])])
# yulingan tuk (pinset ichida, ildiz piyozchasi bilan)
hair_pulled = nose_hair("hair_pulled", V(0, 0, 0) - V(0, 0.0065, 0), V(0, 1, 0), 0.0095 + 0.004, 0.00028, twz)
bulb = sphere("hair_bulb", 0.00065, (0, -0.0085, 0), mat("bulb_m", (0.85, 0.78, 0.7), 0.4, sss=0.3, sss_scale=0.0005), scale=(1, 1.6, 1), parent=twz)
vis(hair_pulled, [(F_SHART + 2, S["pluck"][1])]); vis(bulb, [(F_SHART + 2, S["pluck"][1])])
# o'ng qo'l IK: pinset tutqichiga
handT = empty("handT", (0, 0.115, 0), twz)
pinchT = empty("pinchT", (0, 0.04, 0), twz)
ik = meg.pose.bones["mixamorig:RightForeArm"].constraints.new("IK")
ik.target = handT; ik.chain_count = 2; ik.use_tail = True
pole = empty("ik_pole", (-0.45, -0.45, -0.1), headE)
ik.pole_target = pole; ik.pole_angle = R(90)
dt = meg.pose.bones["mixamorig:RightHand"].constraints.new("DAMPED_TRACK"); dt.target = pinchT; dt.track_axis = "TRACK_Y"
for c_, ks in ((ik, [(1, 0.0), (24, 1.0), (S["pluck"][1] - 6, 1.0), (S["pluck"][1] + 4, 0.0)]),
               (dt, [(1, 0.0), (24, 0.8), (S["pluck"][1] - 6, 0.8), (S["pluck"][1] + 4, 0.0)])):
    for f, v in ks: c_.influence = v; c_.keyframe_insert("influence", frame=f)
# barmoqlar pinsetni qisadi
for fn in ("Index", "Middle", "Thumb"):
    for j in (1, 2):
        pb = meg.pose.bones.get(f"mixamorig:RightHand{fn}{j}")
        if not pb: continue
        t = pb.constraints.new("TRANSFORM"); t.target = meg; t.subtarget = "mixamorig:RightHand"
        t.map_from = "LOCATION"; t.map_to = "ROTATION"; t.target_space = t.owner_space = "LOCAL"
        t.to_min_x_rot = t.to_max_x_rot = R(35 if fn != "Thumb" else 15); t.mix_mode_rot = "ADD"
        for f, v in ((1, 0.0), (24, 1.0), (S["pluck"][1] - 6, 1.0), (S["pluck"][1] + 4, 0.0)):
            t.influence = v; t.keyframe_insert("influence", frame=f)

# --- havodagi chang oqimi (air) va bakteriyalar (inhale): burun teshigiga so'riladi ---
dust_m = mat("dust_air", (0.9, 0.85, 0.75), 0.6, emit=1.6, emit_col=(1.0, 0.92, 0.75))
bact_m = mat("bact", (0.25, 0.75, 0.15), 0.3, emit=2.5, emit_col=(0.4, 1.0, 0.2), coat=0.6, sss=0.3, sss_scale=0.0005)
air_grp = empty("air_grp", (0, 0, 0), headE)
ra = random.Random(9)
def suck(o, f0, f1, start, end):
    """o start -> burun teshigi ichi, egri yo'l (Head fazosi)"""
    mid = start.lerp(end, 0.65) + V(0, -0.004, 0.01)
    key(o, f0 - 1, loc=tuple(start), scale=1.0)
    key(o, f0, loc=tuple(start), scale=1.0)
    key(o, int(f0 + (f1 - f0) * 0.7), loc=tuple(mid), scale=1.0)
    key(o, f1, loc=tuple(end), scale=0.0)
AI0, AI1 = S["air"]
IN_PT = NOSTRIL + V(0, 0.006, -0.004)
for i in range(110):
    o = rock(f"aird{i}", ra.uniform(0.00012, 0.00032), dust_m, i, air_grp)
    st = NOSTRIL + V(ra.uniform(-0.03, 0.04), ra.uniform(-0.07, -0.01), ra.uniform(0.01, 0.07))
    f0 = ra.randint(AI0 - 30, AI1 - 12); f1 = f0 + ra.randint(22, 40)
    suck(o, f0, f1, st, IN_PT + V(ra.uniform(-0.002, 0.002), 0, 0))
vis(air_grp, rng("air", "inhale"))
IH0, IH1 = S["inhale"]
bact_grp = empty("bact_grp", (0, 0, 0), headE)
HERO_B = None
for i in range(14):
    o = capsule(f"bact{i}", 0.0006, 0.0024, bact_m, bact_grp)
    st = NOSTRIL + V(ra.uniform(-0.02, 0.03), ra.uniform(-0.05, -0.015), ra.uniform(0.015, 0.05))
    f0 = IH0 - ra.randint(0, 20) + (i * 3 if i else 0); f1 = f0 + ra.randint(40, 60)
    if i == 0: st = NOSTRIL + V(0.012, -0.028, 0.03); f0 = IH0; f1 = IH1 - 8; HERO_B = o
    o.rotation_mode = "XYZ"
    for f in range(f0, f1 + 1, 4):
        o.rotation_euler = (R(ra.uniform(0, 360)), R(ra.uniform(0, 360)), 0); o.keyframe_insert("rotation_euler", frame=f)
    suck(o, f0, f1, st, IN_PT)
vis(bact_grp, rng("inhale"))

# --- o'lim uchburchagi (yuzda): burun ko'prigidan og'iz chetlarigacha ---
TRI = [V(0.0, 0.095), V(0.027, 0.004), V(-0.027, 0.004)]
def reveal_mat(name, col, emit):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Emission Color"].default_value = (*col, 1)
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    rv = value_node(m, "reveal", 0.0); gl = value_node(m, "glow", emit)
    on = P.math_n(N, L, "LESS_THAN", ua.outputs["Fac"], rv)
    L.new(P.math_n(N, L, "MULTIPLY", on, gl), b.inputs["Emission Strength"])
    out = N["Material Output"]; tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(on, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
tri_m = reveal_mat("tri_line", (1.0, 0.03, 0.02), 3.0)
tri_pts = []
for k in range(3):
    A, B = TRI[k], TRI[(k + 1) % 3]
    for j in range(24):
        t = j / 24; p = A.lerp(B, t); tri_pts.append(tuple(on_face(p.x, p.y, 0.0015)))
tri_pts.append(tri_pts[0])
tri_grp = empty("tri_grp", (0, 0, 0), headE)
cu = bpy.data.curves.new("tri_line", "CURVE"); cu.dimensions = "3D"
sp = cu.splines.new("POLY"); sp.points.add(len(tri_pts) - 1)
for i, p in enumerate(tri_pts): sp.points[i].co = (*p, 1)
tri_line = bpy.data.objects.new("tri_line", cu); P.link(tri_line, tri_grp); cu.materials.append(tri_m)
mm = tri_line.modifiers.new("tube", "NODES"); mm.node_group = P.tube_group(); P.set_mod(tri_line, "tube", next(
    it.identifier for it in P.tube_group().interface.items_tree if getattr(it, "name", "") == "Radius"), 0.0007)
# to'ldirilgan qizil soha (yarim shaffof)
fill_m = bpy.data.materials.new("tri_fill"); fill_m.use_nodes = True
N = fill_m.node_tree.nodes; L = fill_m.node_tree.links; N.remove(N["Principled BSDF"])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.05, 0.03, 1)
fgl = value_node(fill_m, "glow", 0.0); L.new(fgl, em.inputs["Strength"])
fa = value_node(fill_m, "alpha", 0.0)
tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); L.new(fa, mx.inputs[0])
L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs[0])
bm = bmesh.new(); n_ = 22; idx = {}
for i in range(n_ + 1):
    for j in range(n_ + 1 - i):
        a = i / n_; b = j / n_; c = 1 - a - b
        p = TRI[0] * c + TRI[1] * a + TRI[2] * b
        idx[(i, j)] = bm.verts.new(on_face(p.x, p.y, 0.0009))
for i in range(n_):
    for j in range(n_ - i):
        bm.faces.new((idx[(i, j)], idx[(i + 1, j)], idx[(i, j + 1)]))
        if (i + 1, j + 1) in idx: bm.faces.new((idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]))
me = bpy.data.meshes.new("tri_fill"); bm.to_mesh(me); bm.free()
tri_fill = bpy.data.objects.new("tri_fill", me); P.link(tri_fill, tri_grp); me.materials.append(fill_m)
for p in me.polygons: p.use_smooth = True
TR0, TR1 = S["tri"]
val_key(tri_m, "reveal", 1, 0.0); val_key(tri_m, "reveal", TR0 + 4, 0.0); val_key(tri_m, "reveal", TR0 + 26, 1.01)
for f, g, a in ((1, 0, 0), (TR0 + 22, 0.0, 0.0), (TR0 + 28, 1.2, 0.25), (F_OLIM - 1, 1.2, 0.25), (F_OLIM, 5.0, 0.6),
                (F_OLIM + 4, 2.0, 0.35), (F_OLIM + 14, 1.4, 0.3), (TR1, 1.6, 0.32), (S["veins"][0], 2.0, 0.3)):
    val_key(fill_m, "glow", f, g); val_key(fill_m, "alpha", f, a)
val_key(tri_m, "glow", 1, 3.0); val_key(tri_m, "glow", F_OLIM, 9.0); val_key(tri_m, "glow", F_OLIM + 6, 3.5)
vis(tri_grp, rng("tri", "veins"))

# ======================================================================
# 3) RENTGEN: shaffof bosh, miya, burun yo'li, darvoza, tomirlar, miya pardasi, xo'ppoz
# ======================================================================
def W(arm, b, f):
    sc.frame_set(f); return arm.matrix_world @ arm.pose.bones["mixamorig:" + b].head
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items()}
NOSEW = {n: wpos(noseT, (a + b) // 2) for n, (a, b) in S.items()}
BWH = W(meg, "Head", 600).copy()
print("FACE hook", FACE["hook"], "HEAD", BWH)

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
vis(hairN, [(1, F_SHART + 1)]); vis(small_hairs, ROOM)

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
GA0, GA1 = S["gate"]; VE0, VE1 = S["veins"]; BR0, BR1 = S["brain"]
for f, g, r_ in ((1, 1.0, 0.0), (F_XAVF, 1.0, 0.0), (F_XAVF + 1, 4.0, 0.8), (F_XAVF + 5, 1.2, 0.2), (200, 1.2, 0.2),
                 (204, 3.5, 0.7), (208, 1.5, 0.3), (212, 3.5, 0.7), (216, 1.5, 0.3), (VE0, 1.0, 0.0), (F_MIYA, 4.0, 0.5),
                 (F_MIYA + 6, 1.4, 0.15), (BR0, 1.2, 0.3)):
    val_key(xb_m, "glow", f, g); val_key(xb_m, "red", f, r_)
f = BR0 + 4
while f < BR1:
    hot = f >= F_YAL
    val_key(xb_m, "glow", f, 3.5 if hot else 1.8); val_key(xb_m, "red", f, 0.9 if hot else 0.5)
    val_key(xb_m, "glow", f + 5, 1.6 if hot else 1.2); val_key(xb_m, "red", f + 5, 0.6 if hot else 0.3)
    f += 12
const_mat_keys(xb_m)

# --- burun yo'li: burun teshigidan yuqoriga, miya ostiga (Head fazosi) ---
NPATH = [NOSTRIL + V(0, 0, 0.006), V(0.006, 0.062, 0.15), V(0.005, 0.078, 0.128), V(0.004, 0.083, 0.10),
         V(0.002, 0.088, 0.075), V(0.0, 0.098, 0.055)]
def train_mat(name, col=(0.25, 0.55, 1.0), pcol=(0.6, 0.85, 1.0)):
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
npath_m = train_mat("npath_m", (0.9, 0.3, 0.3), (1.0, 0.25, 0.15))
npath = P.tube("npath", [tuple(p) for p in NPATH], 0.0014, npath_m, headE, taper=[1.4, 1.2, 1.0, 0.9, 0.8, 0.6])
for f, a, g, ph in ((1, 0.0, 0.3, -0.5), (GA0, 0.0, 0.5, -0.5), (F_OCH, 0.0, 1.0, -0.5), (F_OCH + 2, 12.0, 1.2, -0.5),
                    (GA1, 12.0, 1.2, 1.2)):
    val_key(npath_m, "amp", f, a); val_key(npath_m, "glow", f, g); val_key(npath_m, "phase", f, ph)
val_key(npath_m, "count", 1, 3.0)
for fc in mc._fcurves(npath_m.node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if '"phase"' in fc.data_path else "CONSTANT"
vis(npath, rng("gate"))
# "darvoza": burun teshigidagi qizil halqa ochiladi
gate_m = mat("gate_m", (1.0, 0.08, 0.03), 0.3, emit=6.0, emit_col=(1.0, 0.1, 0.03))
bpy.ops.mesh.primitive_torus_add(major_radius=0.006, minor_radius=0.0007, major_segments=48, minor_segments=8)
gate = bpy.context.object; gate.name = "gate"; gate.data.materials.append(gate_m); gate.parent = headE
gate.location = NOSTRIL + V(0, -0.002, 0.002); gate.rotation_euler = (R(90 - 20), 0, 0)
key(gate, 1, scale=0.05); key(gate, F_XAVF - 4, scale=0.05); key(gate, F_OCH - 4, scale=0.5); key(gate, F_OCH + 2, scale=1.6)
key(gate, GA1, scale=1.8)
for g_ in range(0):                                  # (qanotlar olib tashlandi)
    hinge = empty(f"gate_h{g_}", tuple(NOSTRIL + V((g_ * 2 - 1) * 0.008, -0.002, 0.002)), headE)
    hinge.rotation_euler = (R(70), 0, 0)
    leaf = box(f"gate_leaf{g_}", (0.008, 0.012, 0.0006), ((1 - g_ * 2) * 0.004, 0, 0), mat(f"gl{g_}", (0.7, 0.05, 0.03), 0.3, emit=2.5, emit_col=(1, 0.1, 0.03)), parent=hinge)
    hinge.rotation_mode = "XYZ"
    for f, a in ((1, 0), (F_OCH - 6, 0), (F_OCH + 4, (1 - g_ * 2) * 100), (GA1, (1 - g_ * 2) * 110)):
        hinge.rotation_euler = (R(70), 0, R(a)); hinge.keyframe_insert("rotation_euler", frame=f)
    vis(hinge, rng("gate"))
vis(gate, rng("gate"))
# yashil bakteriyalar oqimi: tashqaridan burun teshigiga, yo'l bo'ylab miyaga
xb_bact = mat("xb_bact", (0.3, 1.0, 0.2), 0.3, emit=5.0, emit_col=(0.35, 1.0, 0.2))
bgrp = empty("xr_bact", (0, 0, 0), headE)
rx = random.Random(4)
def along(path, t):
    n = len(path) - 1; t = min(max(t, 0), 1) * n; i = min(int(t), n - 1); return path[i].lerp(path[i + 1], t - i)
BPATH = [NOSTRIL + V(0.0, -0.06, 0.05), NOSTRIL + V(0, -0.02, 0.015)] + NPATH
for i in range(34):
    o = capsule(f"xbac{i}", 0.0011, 0.004, xb_bact, bgrp); o.rotation_euler = (rx.uniform(0, 6), rx.uniform(0, 6), 0)
    f0 = GA0 + rx.randint(0, 50) + (14 if i % 3 else 0); f1 = f0 + rx.randint(36, 56)
    off = V(rx.uniform(-0.004, 0.004), rx.uniform(-0.003, 0.003), rx.uniform(-0.003, 0.003))
    stop = 0.25 if f0 < F_OCH - 10 else 1.0           # darvoza ochilguncha kirish oldida kutadi
    for k in range(9):
        t = k / 8; f = int(f0 + (f1 - f0) * t)
        tt = t * 0.25 if f < F_OCH else t
        if f < F_OCH and stop < 1: tt = min(tt, 0.2)
        key(o, f, loc=tuple(along(BPATH, tt) + off * (1 - tt * 0.6)))
    o.keyframe_insert("rotation_euler", frame=f0); o.rotation_euler.x += 3; o.keyframe_insert("rotation_euler", frame=f1)
vis(bgrp, rng("gate"))

# --- tomirlar: uchburchakdan ko'z ichi orqali kovak sinusga (miya ostiga) ---
def mirror(p, sx): return V(p.x * sx, p.y, p.z)
VEIN = [on_face(0.024, 0.008, -0.001), on_face(0.016, 0.03, -0.0015), on_face(0.012, 0.055, -0.0015), on_face(0.016, 0.075, -0.0015),
        V(0.02, 0.088, 0.13), V(0.022, 0.09, 0.105), V(0.018, 0.085, 0.08), V(0.012, 0.082, 0.058), V(0.006, 0.09, 0.045)]
vein_ms = []; veins = []
for sx in (1, -1):
    for k, (col, pc, rad) in enumerate((((0.25, 0.3, 0.9), (1.0, 0.15, 0.08), 0.0016), ((0.8, 0.1, 0.1), (1.0, 0.3, 0.15), 0.0011))):
        off = V(0.0012 * sx * k, -0.001 * k, 0)
        m = train_mat(f"vein_m{sx}{k}", col, pc); vein_ms.append(m)
        t_ = P.tube(f"vein{sx}{k}", [tuple(mirror(p, sx) + off) for p in VEIN], rad, m, headE)
        veins.append(t_)
for t_ in veins: vis(t_, rng("veins", "brain"))
sinus_m = mat("sinus", (0.4, 0.1, 0.3), 0.3, emit=2.0, emit_col=(0.8, 0.15, 0.4))
sinus = sphere("sinus", 0.0045, (0, 0.088, 0.046), sinus_m, scale=(1.8, 0.7, 1.0), parent=headE)
vis(sinus, rng("veins", "brain"))
for i, m in enumerate(vein_ms):
    for f, a, g, cnt, ph in ((1, 0, 0.3, 2.0, 0.0), (VE0, 0.0, 0.6, 2.0, 0.0), (VE0 + 10, 25.0, 0.8, 2.0, 0.0),
                             (F_MIYA, 50.0, 2.0, 2.0, (F_MIYA - VE0 - 10) * -0.045), (VE1, 30.0, 1.0, 2.0, (VE1 - VE0 - 10) * -0.045),
                             (BR0, 15.0, 0.6, 3.0, 0.0), (BR1, 15.0, 0.6, 3.0, (BR1 - BR0) * -0.03)):
        val_key(m, "amp", f, a); val_key(m, "glow", f, g); val_key(m, "count", f, cnt); val_key(m, "phase", f, ph)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = "LINEAR" if '"phase"' in fc.data_path else "CONSTANT"

# --- miya pardasi (yallig'lanish) va xo'ppoz ---
def men_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", 0.3)
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 9.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    vein = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", vo.outputs["Distance"], 0.05), clamp=True)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    a = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", vein, 0.6), P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 0.35))
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.06, 0.03, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", vein, 0.25), gl), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", a, 0.55), P.math_n(N, L, "MINIMUM", gl, 1.0)), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
men_m = men_mat("meninges")
men = empty("meninges", (0, 0, 0), xbrain)
for o in list(xbrain.children):
    if o.type != "MESH": continue
    c_ = o.copy(); c_.data = o.data; c_.name = o.name + "_men"; sc.collection.objects.link(c_)
    c_.animation_data_clear()                         # nusxa miya bilan bir xil hide_render action'ni ulashmasin
    c_.parent = men; c_.material_slots[0].link = "OBJECT"; c_.material_slots[0].material = men_m
    c_.scale = (1.07, 1.07, 1.07)
men.location = (0, 0, 0)
vis(men, rng("brain"))
val_key(men_m, "glow", 1, 0.2); val_key(men_m, "glow", BR0, 0.25); val_key(men_m, "glow", F_YAL - 4, 0.3)
f = F_YAL - 3; k_ = 0
while f < BR1:
    val_key(men_m, "glow", f, 2.2 + min(k_, 4) * 0.25); val_key(men_m, "glow", f + 5, 0.9 + min(k_, 4) * 0.1); f += 12; k_ += 1
const_mat_keys(men_m)
abs_m = mat("abscess", (0.75, 0.7, 0.1), 0.25, emit=0.5, emit_col=(0.8, 0.9, 0.1), coat=1.0, sss=0.5, sss_scale=0.003)
ABS = V(0.032, 0.125, 0.085)
absc = sphere("abscess", 0.015, tuple(ABS), abs_m, sub=4, parent=headE)
dm = absc.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new("absn", "CLOUDS"); tx.noise_scale = 0.4; dm.texture = tx; dm.strength = 0.002
ring_m = mat("abs_ring", (1.0, 0.05, 0.02), 0.3, emit=1.5)
absr = sphere("abscess_r", 0.018, tuple(ABS + V(-0.001, 0, -0.002)), ring_m, sub=3, parent=headE)
for o, s_ in ((absc, 1.0), (absr, 1.0)):
    key(o, 1, scale=0.01); key(o, F_XOP - 6, scale=0.01); key(o, F_XOP + 10, scale=0.9 * s_); key(o, F_XOP + 14, scale=0.82 * s_)
    for f in range(F_XOP + 20, BR1 + 1, 10): key(o, f, scale=0.95 * s_); key(o, f + 5, scale=0.86 * s_)
    vis(o, rng("brain"))
for o in (absc, absr): interp(o, "BEZIER", "scale")

# ======================================================================
# 4) MIKRO DUNYO (a): burun ichi tunnel — tuklar o'rmoni, zarralar ushlanadi
# ======================================================================
TUN0 = V(40, 0, 0)                     # tunnel og'zi; tunnel +Y bo'ylab ichkariga
TR_ = 0.55; TL = 4.0
muc_m = bpy.data.materials.new("mucosa"); muc_m.use_nodes = True
N = muc_m.node_tree.nodes; L = muc_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Roughness"].default_value = 0.22; b.inputs["Coat Weight"].default_value = 0.8; b.inputs["Coat Roughness"].default_value = 0.08
b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.02
b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 6
L.new(tc.outputs["Object"], nz.inputs["Vector"])
cr_ = N.new("ShaderNodeMix"); cr_.data_type = "RGBA"; cr_.inputs[6].default_value = (0.62, 0.16, 0.16, 1); cr_.inputs[7].default_value = (0.85, 0.38, 0.36, 1)
L.new(nz.outputs["Fac"], cr_.inputs["Factor"]); L.new(cr_.outputs[2], b.inputs["Base Color"])
vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 14.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=TR_, depth=TL, location=tuple(TUN0 + V(0, TL / 2, 0)), rotation=(R(90), 0, 0), end_fill_type="NOTHING")
tun = bpy.context.object; tun.name = "tunnel"; tun.data.materials.append(muc_m)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=20); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode="OBJECT")
for v in tun.data.vertices:
    t = (TL / 2 - v.co.z) / TL                                       # mahalliy -Z = dunyo +Y (ichkariga)
    sq = 1.0 - 0.35 * math.sin(min(1, max(0, t)) * math.pi * 0.9)    # o'rtada torayadi
    v.co.x *= sq; v.co.y *= sq * 0.85
dm = tun.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new("tun_n", "CLOUDS"); t_.noise_scale = 0.35; dm.texture = t_; dm.strength = 0.12
for p in tun.data.polygons: p.use_smooth = True
# og'iz atrofidagi teri (tashqi yuz) — tekis halqa
skin_out = mat("skin_out", (0.78, 0.5, 0.4), 0.45, sss=0.4, sss_scale=0.02)
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=3.0, fill_type="NGON", location=tuple(TUN0), rotation=(R(90), 0, 0))
lip = bpy.context.object; lip.name = "nostril_rim"; lip.data.materials.append(skin_out)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.inset(thickness=2.45); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
tun_hairs = empty("tun_hairs", (0, 0, 0))
thair_m = mat("thair", (0.05, 0.032, 0.02), 0.32, coat=0.4)
rt = random.Random(12)
HAIR_TIPS = []
for i in range(130):
    t = rt.uniform(0.02, 0.75); a = rt.uniform(0, 2 * math.pi)
    sq = 1.0 - 0.35 * math.sin(t * math.pi * 0.9)
    base = TUN0 + V(math.cos(a) * TR_ * sq * 0.95, t * TL, math.sin(a) * TR_ * sq * 0.85 * 0.95)
    inward = (V(TUN0.x, base.y, TUN0.z) - base).normalized()
    d = (inward * 0.75 + V(0, -0.65, 0) + V(rt.uniform(-0.2, 0.2), 0, rt.uniform(-0.2, 0.2))).normalized()
    ln = rt.uniform(0.35, 0.75) * sq
    side = d.cross(V(0, 1, 0)).normalized()
    pts = [base - d * 0.03, base + d * ln * 0.35 + side * 0.03, base + d * ln * 0.7 + side * 0.07 + V(0, 0, -0.03), base + d * ln]
    P.tube(f"th{i}", [tuple(p) for p in pts], rt.uniform(0.008, 0.013), thair_m, tun_hairs, taper=[1.0, 0.85, 0.55, 0.12])
    HAIR_TIPS.append((pts, ln))
vis(tun_hairs, rng(*TUN)); vis(tun, rng(*TUN)); vis(lip, rng(*TUN))
# zarralar: chang (kulrang tosh), zamburug' sporasi (sariq-yashil), virus (qizil tikanli)
dust2_m = mat("dust2", (0.45, 0.42, 0.38), 0.85)
spore_m = mat("spore", (0.6, 0.65, 0.15), 0.4, sss=0.4, sss_scale=0.01, emit=0.3, emit_col=(0.7, 0.8, 0.2))
virus_m = mat("virus", (0.75, 0.05, 0.05), 0.35, coat=0.5, emit=0.6, emit_col=(1.0, 0.1, 0.05))
part_grp = empty("particles", (0, 0, 0))
sp_tex = bpy.data.textures.new("spore_t", "VORONOI"); sp_tex.noise_scale = 0.008
CA0, CA1 = S["catch"]; FO0, FO1 = S["forest"]
HERO_V = None
for i in range(75):
    kind = "dust" if i < 30 else ("spore" if i < 52 else "virus")
    if kind == "dust": o = rock(f"pd{i}", rt.uniform(0.02, 0.045), dust2_m, i + 100, part_grp)
    elif kind == "spore":
        o = sphere(f"ps{i}", 0.026, (0, 0, 0), spore_m, scale=(1.0, 1.8, 1.0), sub=3, parent=part_grp)
        dm_ = o.modifiers.new("d", "DISPLACE"); dm_.texture = sp_tex; dm_.strength = 0.006
    else: o = spiky(f"pv{i}", rt.uniform(0.022, 0.03), virus_m, parent=part_grp)
    pts, ln = rt.choice(HAIR_TIPS[:90])
    stick = Vector(pts[1]).lerp(Vector(pts[3]), rt.uniform(0.2, 0.9)) + V(rt.uniform(-0.02, 0.02), 0, rt.uniform(-0.02, 0.02))
    start = TUN0 + V(rt.uniform(-0.35, 0.35), rt.uniform(-2.6, -1.2), rt.uniform(-0.3, 0.3))
    f0 = {"dust": CA0 - 30, "spore": F_ZAMB - 18, "virus": F_VIR - 16}[kind] + rt.randint(-6, 30)
    if kind == "virus" and HERO_V is None:
        HERO_V = o; f0 = F_VIR - 8; stick = Vector(HAIR_TIPS[3][0][2]); start = stick + V(0.25, -1.6, 0.15)
    f1 = f0 + rt.randint(14, 26)
    mid = start.lerp(stick, 0.6) + V(0, 0, rt.uniform(-0.1, 0.1))
    key(o, FO0, loc=tuple(start)); key(o, f0, loc=tuple(start)); key(o, (f0 + f1) // 2, loc=tuple(mid)); key(o, f1, loc=tuple(stick))
    key(o, f1 + 4, loc=tuple(stick + V(0, 0.015, 0.008))); key(o, f1 + 9, loc=tuple(stick))       # urilib to'xtaydi
    o.rotation_euler = (rt.uniform(0, 6), rt.uniform(0, 6), rt.uniform(0, 6)); o.keyframe_insert("rotation_euler", frame=f0)
    o.rotation_euler.x += 2.5; o.keyframe_insert("rotation_euler", frame=f1)
vis(part_grp, rng("catch"))
# havo oqimi chiziqlari (forest: shamol)
stream_m = mat("stream", (0.8, 0.9, 1.0), emit=1.2, emit_col=(0.8, 0.9, 1.0), alpha=1.0)

# ======================================================================
# 5) MIKRO DUNYO (b): shilliq qavat kesimi — tuk ildizi, teshik, qon tomir, bakteriyalar
# ======================================================================
BL = V(80, 0, 0)                       # blok markazi (yuqori sirt z=0); kesim yuzasi y = BL.y + CY
CY = -0.3
BX = 2.2
def layer_mat(name):
    """kesim yuzasidagi qatlamlar: epiteliy (to'q pushti), shilliq osti (och), chuqurda qizg'ish"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.1
    b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Scale"].default_value = 0.01
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    zz = P.math_n(N, L, "ADD", sep.outputs["Z"], P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", nz.outputs["Fac"], 0.5), 0.05))
    cr = N.new("ShaderNodeValToRGB"); L.new(P.math_n(N, L, "MULTIPLY", zz, -1.0), cr.inputs[0])
    el = cr.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0.55, 0.06, 0.08, 1)
    el[1].position = 0.08; el[1].color = (0.42, 0.04, 0.06, 1)
    e = el.new(0.1); e.color = (0.8, 0.36, 0.33, 1)
    e = el.new(0.45); e.color = (0.85, 0.48, 0.42, 1)
    e = el.new(0.8); e.color = (0.6, 0.18, 0.18, 1)
    # tolalar (biriktiruvchi to'qima)
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 9.0; wv.inputs["Distortion"].default_value = 8.0; wv.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; L.new(cr.outputs[0], mx.inputs[6])
    L.new(P.math_n(N, L, "MULTIPLY", wv.outputs["Fac"], 0.25), mx.inputs["Factor"]); mx.inputs[7].default_value = (0.8, 0.45, 0.45, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
blk_m = layer_mat("block_m")
sheath_m = mat("sheath", (0.8, 0.55, 0.48), 0.35, sss=0.4, sss_scale=0.01, coat=0.5)
lumen_m = mat("lumen", (0.35, 0.02, 0.03), 0.15, coat=1.0, sss=0.3, sss_scale=0.01)
blk = box("block", (2 * BX, 2.0, 1.2), tuple(BL + V(0, CY + 1.0, -0.6)), blk_m)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=24); bpy.ops.object.mode_set(mode="OBJECT")
for v in blk.data.vertices: v.co.z -= 0.6
blk.location.z += 0.6                                  # origin yuqori sirtda (qatlam rangi Object Z dan)
# follikula kanali (vertikal, kesim yuzasida yarmi ochiq) va qon tomir (X bo'ylab)
FOL = BL + V(0, CY, 0)
VZ = -0.62; VR = 0.16
cutF = cyl("cut_fol", 0.06, 0.62, tuple(FOL + V(0, 0, -0.27)), sheath_m, verts=32)
cutV = cyl("cut_ves", VR, 2 * BX + 0.4, tuple(BL + V(0, CY, VZ)), lumen_m, rot=(0, 90, 0), verts=48)
cutC = cyl("cut_cap", 0.035, 0.12, tuple(FOL + V(0, 0, -0.57 + 0.03)), lumen_m, verts=16)    # follikula tubi -> tomir
for cutter in (cutF, cutV, cutC):
    bo = blk.modifiers.new("b_" + cutter.name, "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cutter; bo.solver = "EXACT"
    bo.material_mode = "TRANSFER"; cutter.hide_render = True; cutter.hide_viewport = True
bpy.context.view_layer.objects.active = blk
for md in list(blk.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
for o in (cutF, cutV, cutC): bpy.data.objects.remove(o, do_unlink=True)
for p in blk.data.polygons: p.use_smooth = True
# sirtdagi shilliq qatlami (yaltiroq) va qisqa tuklar
mucus_m = mat("mucus", (0.85, 0.55, 0.5), 0.05, coat=1.0, trans=0.6, alpha=0.6)
blk_grp = empty("blk_grp", (0, 0, 0))
blk.parent = blk_grp
bh_grp = empty("bh_grp", (0, 0, 0), blk_grp)
rb = random.Random(31)
for i in range(16):
    x = rb.uniform(-BX + 0.2, BX - 0.2); y = rb.uniform(0.25, 1.5)
    if abs(x) < 0.35 and y < 0.5: continue
    base = BL + V(x, CY + y, 0)
    d = V(rb.uniform(-0.3, 0.3), rb.uniform(-0.3, 0.3), 1).normalized(); ln = rb.uniform(0.6, 1.1)
    P.tube(f"bh{i}", [tuple(base - d * 0.2), tuple(base + d * ln * 0.5 + V(0.04, 0, 0)), tuple(base + d * ln)], 0.022, thair_m, bh_grp, taper=[1, 0.8, 0.2])
# asosiy tuk: ildiz piyozchasi bilan (kesim yuzasida)
HAIR_LEN = 1.9
mh = empty("main_hair", tuple(FOL), blk_grp)
P.tube("mh_shaft", [(0, 0, -0.52), (0, 0, 0.3), (0.03, 0, 0.9), (0.08, 0, HAIR_LEN - 0.5)], 0.034, thair_m, mh, taper=[1.0, 1.0, 0.9, 0.5])
bulb_b = sphere("mh_bulb", 0.05, (0, 0, -0.52), mat("mh_bulb_m", (0.92, 0.82, 0.72), 0.35, sss=0.5, sss_scale=0.02, coat=0.4), scale=(1, 1, 1.5), parent=mh)
sheath_o = cyl("mh_sheath", 0.034, 0.2, (0, 0, -0.38), sheath_m, parent=mh, verts=16)        # ildiz bilan chiqadigan qobiq
RO0, RO1 = S["root"]; WO0, WO1 = S["wound"]; EN0, EN1 = S["enter"]
PULL0, PULL1 = RO0 + 10, RO1 - 4
key(mh, 1, loc=tuple(FOL)); key(mh, PULL0, loc=tuple(FOL))
for k in range(1, 9):
    t = k / 8; f = int(PULL0 + (PULL1 - PULL0) * t)
    key(mh, f, loc=tuple(FOL + V(0.01 * math.sin(t * 9), 0, 1.0 * ease(t) + 0.12 * t)))
key(mh, WO0, loc=tuple(FOL + V(0, 0, 3.0)))
vis(mh, rng("root"))
# teshik qirrasidagi yirtiq (qizil halqa) va qon
wound_m = mat("wound", (0.6, 0.03, 0.03), 0.2, coat=1.0, emit=0.4, emit_col=(1, 0.1, 0.05))
bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.012, major_segments=32, minor_segments=8, location=tuple(FOL + V(0, 0, 0.0)))
wring = bpy.context.object; wring.name = "wound_ring"; wring.data.materials.append(wound_m); wring.parent = blk_grp
vis(wring, rng("wound", "enter"))
blood_m = mat("blood", (0.42, 0.01, 0.015), 0.08, coat=1.0, sss=0.4, sss_scale=0.02)
bcol = cyl("blood_col", 0.055, 1.0, (0, 0, 0), blood_m, verts=24)        # kanal ichida ko'tariladigan qon (origin pastda)
for v in bcol.data.vertices: v.co.z += 0.5
bcol.parent = blk_grp; bcol.location = FOL + V(0, 0.002, VZ + VR * 0.6)
key(bcol, 1, scale=(1, 1, 0.01)); key(bcol, F_QON - 2, scale=(1, 1, 0.01)); key(bcol, F_QON + 26, scale=(1, 1, (-VZ - VR * 0.6) + 0.02))
key(bcol, EN1, scale=(1, 1, (-VZ - VR * 0.6) + 0.02))
vis(bcol, rng("wound", "enter"))
drop = sphere("blood_drop", 0.11, tuple(FOL + V(0, 0.05, 0.0)), blood_m, scale=(1, 1, 0.7), sub=4, parent=blk_grp)
key(drop, 1, scale=0.01); key(drop, F_QON + 22, scale=0.01); key(drop, WO1, scale=(1.0, 1.0, 0.7)); key(drop, EN1, scale=(1.15, 1.15, 0.75))
vis(drop, rng("wound", "enter"))
# tomir devoridagi yorilish (chaqnaydi)
tear_m = mat("tear", (1.0, 0.2, 0.1), 0.3, emit=0.0, emit_col=(1.0, 0.15, 0.05))
tear = sphere("tear", 0.05, tuple(FOL + V(0, 0.01, VZ + VR * 0.85)), tear_m, scale=(1.4, 0.4, 0.5), parent=blk_grp)
tb = tear_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.0), (F_QON - 1, 0.0), (F_QON + 1, 12.0), (F_QON + 8, 3.0), (WO1, 2.0)): tb.default_value = v; tb.keyframe_insert("default_value", frame=f)
vis(tear, rng("wound", "enter"))
# qizil qon tanachalari tomir ichida X bo'ylab oqadi
rbc_m = mat("rbc", (0.7, 0.03, 0.03), 0.25, coat=0.6, sss=0.5, sss_scale=0.01)
rbc_grp = empty("rbc_grp", (0, 0, 0), blk_grp)
VSPD = 0.012                           # m/kadr
RF0, RF1 = RO0, EN1
rc = random.Random(41)
nrbc = 0
x = -BX - (RF1 - RF0) * VSPD
while x < BX:
    y = CY + rc.uniform(0.0, VR * 0.75); z = VZ + rc.uniform(-VR * 0.7, VR * 0.7)
    o = sphere(f"rbc{nrbc}", 0.06, (0, 0, 0), rbc_m, scale=(1, 1, 0.38), sub=3, parent=rbc_grp)
    o.rotation_euler = (rc.uniform(0, 3), rc.uniform(0, 3), 0)
    p0 = BL + V(x, y, z); p1 = p0 + V((RF1 - RF0) * VSPD, 0, 0)
    key(o, RF0, loc=tuple(p0)); key(o, RF1, loc=tuple(p1)); interp(o, "LINEAR", "location")
    # faqat blok ichida ko'rinadi
    fi = RF0 + max(0, int((BL.x - BX + 0.05 - p0.x) / VSPD)); fo = RF0 + int((BL.x + BX - 0.05 - p0.x) / VSPD)
    a_, b_ = max(fi, RF0), min(fo, RF1)
    vis(o, [(max(a_, x0), min(b_, x1)) for x0, x1 in rng(*BLK) if max(a_, x0) <= min(b_, x1)], recursive=False)
    x += rc.uniform(0.09, 0.2); nrbc += 1
# bakteriyalar teshikka tushib, tomirga o'tadi va oqim bilan ketadi
bk_m = mat("bk_m", (0.25, 0.8, 0.15), 0.3, emit=1.2, emit_col=(0.4, 1.0, 0.2), coat=0.6, sss=0.3, sss_scale=0.01)
bk_grp = empty("bk_grp", (0, 0, 0), blk_grp)
for i in range(7):
    o = capsule(f"bk{i}", 0.035, 0.14, bk_m, bk_grp)
    f0 = EN0 + i * 6; f_in = f0 + 18; f_down = F_QONGA - 4 + i * 3; f_out = EN1 + 1
    p_sky = FOL + V(rc.uniform(-0.6, 0.6), rc.uniform(0.2, 0.8), rc.uniform(0.9, 1.4))
    p_top = FOL + V(rc.uniform(-0.02, 0.02), 0.03, 0.05)
    p_bot = FOL + V(0, 0.03, VZ + VR * 0.2)
    p_end = p_bot + V((f_out - f_down) * VSPD * 0.8, 0, rc.uniform(-0.05, 0.05))
    key(o, EN0, loc=tuple(p_sky)); key(o, f0, loc=tuple(p_sky)); key(o, f_in, loc=tuple(p_top)); key(o, f_down, loc=tuple(p_bot))
    key(o, f_out, loc=tuple(p_end))
    o.rotation_euler = (rc.uniform(0, 3), rc.uniform(0, 3), 0); o.keyframe_insert("rotation_euler", frame=f0)
    o.rotation_euler = (0, R(90), 0); o.keyframe_insert("rotation_euler", frame=f_down)
vis(bk_grp, rng("enter"))
vis(blk, rng(*BLK)); vis(bh_grp, rng(*BLK))
for o in room_objs: vis(o, ROOM)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def rig(name, target):
    e = empty(name + "_rig"); c = e.constraints.new("COPY_LOCATION"); c.target = target; return e
def rel_cam(name, target, lens, fstop, offsets, track=None, clip=0.003):
    r_ = rig(name, target)
    c = shot_cam(name, (0, 0, 0), track or target, lens, fstop, focus=track or target, clip=clip)
    c.parent = r_
    path_keys(c, offsets)
    return c
# 1 ILGAK: poldan keng ob'ektiv, Megan yuziga tez yaqinlashish
H0, H1 = S["hook"]
hT = empty("hookT"); path_keys(hT, [(H0, FACE["hook"] + V(0, 0, -0.35)), (H1, NOSEW["hook"] + V(0, 0, -0.01))])
c = shot_cam("hook", (0, 0, 0), hT, 16, 3.2, focus=noseT)
path_keys(c, [(H0, FACE["hook"] + V(-0.5, 1.1, -1.3)), (H0 + 26, FACE["hook"] + V(-0.15, 0.42, -0.34)), (H1, NOSEW["hook"] + V(-0.05, 0.13, -0.09))])
lens_keys(c, [(H0, 15), (H0 + 26, 18), (H1, 24)])
# 2 YULISH: burun makro, "shart" da silkinish
P0_, P1_ = S["pluck"]
c = rel_cam("pluck", nosE, 50, 7.0, [(P0_, V(-0.05, 0.08, -0.045)), (F_SHART - 2, V(-0.036, 0.062, -0.038)), (F_SHART + 2, V(-0.045, 0.085, -0.05)), (P1_, V(-0.05, 0.1, -0.06))], clip=0.002)
lens_keys(c, [(P0_, 45), (F_SHART - 2, 52), (F_SHART + 1, 40), (P1_, 36)])
shake(c, F_SHART, F_SHART + 14, 0.006, seed=2)
# 3 DARVOZA: rentgen bosh, crash zoom burun teshigiga, keyin yo'l bo'ylab miyaga
gT = empty("gateT", (0, 0, 0), headE); path_keys(gT, [(GA0, NOSTRIL), (F_OCH, NOSTRIL + V(0, 0.005, -0.005)), (GA1, V(0.004, 0.09, 0.07))])
c = rel_cam("gate", gT, 26, 3.5, [(GA0, V(0.55, 0.75, 0.05)), (GA0 + 8, V(0.14, 0.26, -0.04)), (F_OCH - 2, V(0.1, 0.17, -0.05)), (F_OCH + 6, V(0.07, 0.12, -0.03)), (GA1, V(0.22, 0.12, 0.04))])
lens_keys(c, [(GA0, 22), (GA0 + 8, 30), (F_OCH + 6, 36), (GA1, 30)])
shake(c, GA0 + 7, GA0 + 16, 0.012, seed=3); shake(c, F_OCH, F_OCH + 10, 0.006, seed=33)
# 4 O'RMON: tunnel og'zidan tuklar orasidan ichkariga uchish
fT = empty("forestT"); path_keys(fT, [(FO0, TUN0 + V(0, 1.6, 0)), (FO1, TUN0 + V(0.05, 3.2, -0.05))])
c = shot_cam("forest", (0, 0, 0), fT, 18, 2.8, focus=fT, clip=0.01)
path_keys(c, [(FO0, TUN0 + V(0.25, -1.3, 0.3)), (FO0 + 20, TUN0 + V(0.12, 0.1, 0.08)), (FO1, TUN0 + V(-0.05, 1.3, -0.08))])
fT2 = empty("forest_f"); path_keys(fT2, [(FO0, TUN0 + V(0, 0.4, 0)), (FO1, TUN0 + V(0, 1.9, 0))]); c.data.dof.focus_object = fT2
# 5 HAVO: yondan yaqin plan, chang oqimi burunga
AI0, AI1 = S["air"]
c = rel_cam("air", noseT, 40, 3.2, [(AI0, V(0.3, 0.12, -0.02)), (AI1, V(0.2, 0.06, -0.05))])
lens_keys(c, [(AI0, 36), (AI1, 44)])
# 6 USHLASH: tunnel ichidan og'izga qarab, zarralar uchib kelib yopishadi; "viruslarni" da crash zoom
cT = empty("catchT"); path_keys(cT, [(CA0, TUN0 + V(0, 0.2, 0)), (F_VIR - 2, TUN0 + V(0, 0.5, 0)), (F_VIR + 10, Vector(HAIR_TIPS[3][0][2])), (CA1, Vector(HAIR_TIPS[3][0][2]))])
c = shot_cam("catch", (0, 0, 0), cT, 20, 3.0, focus=cT, clip=0.01)
HV = Vector(HAIR_TIPS[3][0][2])
path_keys(c, [(CA0, TUN0 + V(0.1, 2.2, 0.15)), (F_VIR - 4, TUN0 + V(-0.05, 1.8, 0.05)), (F_VIR + 8, HV + V(0.12, 0.35, 0.1)), (CA1, HV + V(0.18, 0.28, 0.02))])
lens_keys(c, [(CA0, 18), (F_VIR - 4, 20), (F_VIR + 8, 30), (CA1, 34)])
shake(c, F_VIR + 6, F_VIR + 18, 0.02, seed=6)
# 7 ILDIZ: kesim bloki, past burchakdan, tuk sekin sug'uriladi
rT = empty("rootT", (0, 0, 0)); cl_ = rT.constraints.new("COPY_LOCATION"); cl_.target = mh
rT2 = empty("rootT2", (0, 0, 0), rT); rT2.location = (0, 0, -0.35)
c = shot_cam("root", (0, 0, 0), rT2, 26, 4.0, focus=rT2, clip=0.01)
path_keys(c, [(RO0, FOL + V(1.6, -2.4, -0.35)), (RO1, FOL + V(0.9, -2.0, 0.25))])
lens_keys(c, [(RO0, 24), (RO1, 30)])
# 8 JAROHAT: bo'sh teshikka push-in, "qon tomir" da pastga tilt + silkinish
wT = empty("woundT"); path_keys(wT, [(WO0, FOL + V(0, 0.2, 0.0)), (F_OCHIQ, FOL + V(0, 0.1, -0.05)), (F_QON - 2, FOL + V(0, 0.0, -0.4)), (F_QON + 10, FOL + V(0, 0, VZ + 0.1)), (F_QON + 30, FOL + V(0, 0, -0.15)), (WO1, FOL + V(0, 0.05, 0.05))])
c = shot_cam("wound", (0, 0, 0), wT, 24, 3.5, focus=wT, clip=0.01)
path_keys(c, [(WO0, FOL + V(-0.9, -1.2, 1.6)), (F_OCHIQ, FOL + V(-0.35, -0.6, 0.7)), (F_QON - 2, FOL + V(-0.5, -1.4, 0.1)), (F_QON + 10, FOL + V(-0.45, -1.3, -0.2)), (WO1, FOL + V(0.6, -1.5, 0.5))])
lens_keys(c, [(WO0, 22), (F_OCHIQ, 28), (F_QON - 2, 26), (F_QON + 4, 34), (WO1, 30)])
shake(c, F_OCHIQ, F_OCHIQ + 8, 0.03, seed=8); shake(c, F_QON, F_QON + 14, 0.04, seed=88)
# 9 UCHBURCHAK: yuz atrofida aylanma, "o'lim" da punch zoom
TR0, TR1 = S["tri"]
trT = empty("triT", (0.0, 0.05, 0.15), headE)
c = rel_cam("tri", trT, 40, 3.2, [(TR0, V(-0.32, 0.35, 0.02)), ((TR0 + F_OLIM) // 2, V(-0.15, 0.42, 0.0)), (F_OLIM, V(0.0, 0.42, -0.03)), (TR1, V(0.2, 0.36, -0.06))])
lens_keys(c, [(TR0, 36), (F_OLIM - 1, 40), (F_OLIM + 2, 52), (F_OLIM + 10, 46), (TR1, 48)])
shake(c, F_OLIM, F_OLIM + 10, 0.008, seed=9)
# 10 TOMIRLAR: rentgen, og'iz chetidan miyaga yonlama ergashish
vT = empty("veinT", (0, 0, 0), headE)
for f, p in ((VE0, VEIN[2]), (VE0 + 30, V(0.01, 0.085, 0.11)), (F_MIYA - 6, V(0.005, 0.095, 0.07)), (VE1, V(0.0, 0.105, 0.05))): key(vT, f, loc=tuple(p))
c = rel_cam("veins", vT, 30, 6.0, [(VE0, V(-0.08, 0.36, -0.05)), (VE0 + 30, V(-0.12, 0.38, 0.02)), (F_MIYA - 4, V(-0.16, 0.38, 0.07)), (F_MIYA + 4, V(-0.14, 0.32, 0.06)), (VE1, V(-0.18, 0.34, 0.1))])
lens_keys(c, [(VE0, 32), (F_MIYA - 4, 28), (F_MIYA + 3, 34), (VE1, 32)])
shake(c, F_MIYA, F_MIYA + 10, 0.008, seed=10)
# 11 NAFAS: burun makro, bakteriyaga ergashish
iT = empty("inhT", (0, 0, 0)); cl_ = iT.constraints.new("COPY_LOCATION"); cl_.target = HERO_B
c = rel_cam("inhale", nosE, 45, 9.0, [(IH0, V(-0.05, 0.11, -0.07)), (IH1, V(-0.025, 0.06, -0.05))], clip=0.002)
lens_keys(c, [(IH0, 40), (IH1, 50)])
# 12 KIRISH: kesim, bakteriyalar teshikka tushadi, keyin tomir bo'ylab
eT = empty("enterT"); path_keys(eT, [(EN0, FOL + V(0, 0.1, 0.4)), (EN0 + 30, FOL + V(0, 0.05, 0.0)), (F_QONGA - 4, FOL + V(0, 0, VZ + 0.1)), (EN1, FOL + V(0.55, 0, VZ))])
c = shot_cam("enter", (0, 0, 0), eT, 24, 3.5, focus=eT, clip=0.01)
path_keys(c, [(EN0, FOL + V(0.6, -1.4, 1.3)), (EN0 + 30, FOL + V(0.3, -1.1, 0.5)), (F_QONGA - 4, FOL + V(-0.3, -1.3, -0.25)), (EN1, FOL + V(0.1, -1.0, -0.45))])
lens_keys(c, [(EN0, 22), (F_QONGA - 4, 26), (F_QONGA + 2, 32), (EN1, 30)])
shake(c, F_QONGA, F_QONGA + 10, 0.03, seed=12)
# 13 MIYA: rentgen bosh, miya pardasi qizaradi; "xo'ppoz" da crash zoom
bT = empty("brainT", (0.01, 0.11, 0.05), headE)
c = rel_cam("brain", bT, 26, 6.0, [(BR0, V(-0.6, 0.45, 0.3)), (F_YAL, V(-0.42, 0.34, 0.2)), (F_XOP - 2, V(-0.36, 0.3, 0.18)), (F_XOP + 6, V(-0.2, 0.2, 0.11)), (BR1, V(-0.18, 0.18, 0.1))])
lens_keys(c, [(BR0, 22), (F_YAL, 24), (F_XOP - 2, 25), (F_XOP + 6, 32), (BR1, 35)])
bT2 = empty("brainT2", (0, 0, 0), headE); path_keys(bT2, [(BR0, V(0.01, 0.11, 0.05)), (F_XOP - 2, V(0.01, 0.11, 0.05)), (F_XOP + 6, ABS), (BR1, ABS)])
c.data.dof.focus_object = bT2; c.constraints[0].target = bT2
shake(c, F_YAL, F_YAL + 8, 0.006, seed=13); shake(c, F_XOP + 2, F_XOP + 16, 0.01, seed=14)
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
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.01, 0.03, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_day.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    day = n in ROOMN or n in TUN
    bg_day.inputs[1].default_value = 1.0 if day else 0.0; bg_day.inputs[1].keyframe_insert("default_value", frame=f)
    bg_dk.inputs[1].default_value = 0.0 if day else (1.0 if n in XRN else 0.6); bg_dk.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(58), 0, R(18))
for f, e in lights_for(ROOM, 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
area("key_front", tuple(MEG + V(-0.6, 1.3, 1.9)), 1.2, (1.0, 0.95, 0.9), lights_for(ROOM, 110.0), target=FT)
area("ceil_fill", (0.0, 0.6, 2.6), 2.0, (1.0, 0.88, 0.72), lights_for(ROOM, 60.0), target=empty("cfT", (0, 0.6, 0)))
area("sofa_fill", (-0.9, 1.0, 2.2), 1.5, (1.0, 0.85, 0.7), lights_for(ROOM, 40.0), target=empty("sfT", (-0.9, 2.0, 0.4)))
area("win_rim", tuple(MEG + V(0.5, -0.8, 1.9)), 1.0, (0.85, 0.92, 1.0), lights_for(ROOM, 90.0), target=FT)
area("nose_fill", tuple(MEG + V(0.2, 0.6, 1.2)), 0.4, (1.0, 0.9, 0.85), lights_for(rng("pluck", "inhale", "air"), 8.0), target=FT)
# rentgen
area("X_rim", tuple(BWH + V(0.6, -0.6, 0.6)), 0.8, (0.3, 0.6, 1.0), lights_for(XR, 15.0), target=headE)
area("X_key", tuple(BWH + V(-0.7, 0.8, 0.5)), 0.8, (0.9, 0.85, 1.0), lights_for(XR, 8.0), target=headE)
# tunnel: og'izdan yorug' kun nuri, ichkarida iliq to'ldiruvchi
TT = empty("tunT", tuple(TUN0 + V(0, 1.5, 0)))
area("T_mouth", tuple(TUN0 + V(0, -2.5, 0.6)), 3.0, (1.0, 0.95, 0.88), lights_for(rng(*TUN), 700.0), target=TT)
area("T_deep", tuple(TUN0 + V(0, 3.2, 0.2)), 0.6, (1.0, 0.45, 0.35), lights_for(rng(*TUN), 60.0), target=empty("tunT2", tuple(TUN0)))
pl = point("T_fill", tuple(TUN0 + V(0.0, 1.2, 0.0)), 0.3, (1.0, 0.7, 0.6), lights_for(rng(*TUN), 25.0))
# kesim bloki: studiya
BT = empty("blkT", tuple(FOL + V(0, 0.3, -0.2)))
area("B_key", tuple(FOL + V(-2.2, -2.6, 2.6)), 2.0, (1.0, 0.93, 0.88), lights_for(rng(*BLK), 380.0), target=BT)
area("B_rim", tuple(FOL + V(2.5, 2.0, 1.8)), 2.0, (0.6, 0.75, 1.0), lights_for(rng(*BLK), 260.0), target=BT)
area("B_fill", tuple(FOL + V(1.5, -3.0, -0.4)), 1.5, (1.0, 0.75, 0.7), lights_for(rng(*BLK), 90.0), target=BT)

# ======================================================================
# 8) RENDER
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
