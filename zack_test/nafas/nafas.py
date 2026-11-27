# Nafasni ushlab turish — Zack D. Films uslubida 41.5 s video (996 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, zack_test/ishqalash/ishqalash.py (xona, rentgen bosh, kamera yordamchilari),
# egri chiziqlar/miya: zack_test/burish/parts.py
# Assetlar: zack_test/tools/get_nafas.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/nafas/nafas.py --render
# Sinov:  FRAMES=30,120,250,300,420 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, os.path.join(ZT, "qovoq"))
sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
import twitch as TW
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 996
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (37, "timer"), (73, "lungs"), (149, "cheeks"), (204, "pain"), (272, "myth"), (326, "brain"),
         (393, "alarm"), (483, "o2"), (537, "co2"), (651, "panic"), (711, "diaph"), (739, "gasp"), (767, "push"),
         (843, "bp"), (891, "faint"), (958, "drown")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "timer", "cheeks", "gasp")
XRN = ("lungs", "pain", "brain", "alarm", "panic", "diaph")
MICN = ("myth", "o2", "co2", "bp")
UWN = ("push", "faint", "drown")
ROOM = rng(*ROOMN); XR = rng(*XRN); MICR = rng(*MICN); UWR = rng(*UWN)
F_PAIN = 239        # "og'riq"
F_SAFE = 437        # "xavfsizlik"
F_CARB = 607        # "karbonat" (2-marta)
F_CHOKE = 674       # "bo'g'ilish"
F_FORCE = 721       # "majburan"
F_BP = 851          # "qon bosimi" "keskin"
F_OUT = 896         # "hushdan" — havo chiqib ketadi

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
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]     # transform_apply joylashuvni ham mesh'ga yozib yuboradi
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

# ---------------- rentgen / impuls materiallari (qovoq.py dan) ----------------
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

def V(*a): return Vector(a)
def text_obj(name, body, loc, rot, size, m, parent=None):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = 0.00005; cu.space_line = 0.9
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.parent = parent
    o.location = loc; o.rotation_euler = [R(a) for a in rot]; cu.materials.append(m)
    return o
def ckey(idb, mode="CONSTANT", path=None): interp(idb, mode, path)

# ======================================================================
# 1) XONA (kechqurun): stol, noutbuk, lampa, divan, deraza (yelim.py dan)
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
# tashqarida: tungi shahar chiroqlari (derazadan ko'rinadi)
R_(plane("out_ground", (40, 30), (0, Y0 - 16, -0.3), mat("out_grass", (0.03, 0.05, 0.03), 0.9)))
rw = random.Random(3)
win_ms = [mat("citylight_w", (1.0, 0.75, 0.4), 0.5, emit=3.0), mat("citylight_b", (0.6, 0.75, 1.0), 0.5, emit=2.0)]
bld_m = mat("bld", (0.02, 0.022, 0.03), 0.8)
for i in range(7):
    x = -6 + i * 2.2 + rw.uniform(-0.4, 0.4); h = rw.uniform(4, 11); y = -12 - rw.uniform(0, 6)
    R_(box(f"bld{i}", (1.8, 1.5, h), (x, y, h / 2 - 0.3), bld_m))
    for k in range(rw.randint(5, 10)):
        R_(box(f"bwin{i}_{k}", (0.25, 0.02, 0.3), (x + rw.uniform(-0.7, 0.7), y + 0.76, rw.uniform(0.5, h - 0.5)), rw.choice(win_ms)))

DESK = Vector((0.6, -1.3, 0)); DESK_TOP = 0.715
R_(import_gltf(PH + "WoodenTable_01/WoodenTable_01.gltf", tuple(DESK), 0, (1.0, 1.1, 1.3)))
CHAIR0 = Vector((0.6, -0.5, 0))
R_(import_gltf(PH + "modern_arm_chair_01/modern_arm_chair_01.gltf", tuple(CHAIR0), 0, 1.0))
R_(import_gltf(PH + "desk_lamp_arm_01/desk_lamp_arm_01.gltf", (1.25, -1.45, DESK_TOP), 200, 1.0))
lap_m = mat("lap_alu", (0.55, 0.56, 0.6), 0.3, metal=0.9)
key_m = mat("lap_keys", (0.03, 0.03, 0.035), 0.6)
LAP = Vector((0.6, -1.17, DESK_TOP))
R_(box("lap_base", (0.33, 0.23, 0.014), tuple(LAP + Vector((0, 0, 0.007))), lap_m, bevel=0.004))
R_(box("lap_kb", (0.28, 0.1, 0.002), tuple(LAP + Vector((0, -0.04, 0.0145))), key_m))
HINGE = LAP + Vector((0, -0.115, 0.014))
scr_par = R_(empty("scr_par", tuple(HINGE))); scr_par.rotation_euler = (R(-12), 0, 0)
box("lap_lid", (0.33, 0.008, 0.22), (0, -0.004, 0.11), lap_m, parent=scr_par, bevel=0.003)
# ekran: qora fonli sekundomer ilovasi (raqamlar matn ob'ekti, frame_change_pre da yangilanadi)
screen_m = mat("screen", (0.0, 0.0, 0.0), 0.3, emit=1.0, emit_col=(0.015, 0.02, 0.035))
scr = plane("lap_screen", (0.30, 0.19), (0, 0.0005, 0.115), screen_m, rot=(90, 0, 0), parent=scr_par)
scr.rotation_euler = (R(90), 0, R(180))
digit_m = mat("digits", (1, 1, 1), 0.3, emit=5.0, emit_col=(1.0, 1.0, 1.0))
ring_m = mat("sw_ring", (1, 0.3, 0.2), 0.3, emit=3.0, emit_col=(1.0, 0.25, 0.15))
timer_t = text_obj("timer_txt", "00:00.0", (0, 0.0012, 0.112), (90, 0, 180), 0.052, digit_m, parent=scr_par)
lbl = text_obj("timer_lbl", "NAFAS", (0, 0.0012, 0.17), (90, 0, 180), 0.018, ring_m, parent=scr_par)
bar = plane("timer_bar", (0.24, 0.004), (0, 0.0011, 0.07), ring_m, rot=(90, 0, 180), parent=scr_par)
def timer_sec(f):
    if f < 40: return 0.0
    if f < 149: return (f - 40) / 24.0
    if f < 204: return 12.0 + (f - 149) / 54.0 * 36.0       # timelapse 00:12 -> 00:48
    if f < 739: return 48.0 + (f - 204) / 24.0
    return 71.0 + (f - 739) / 24.0
def _timer_upd(scene, *a):
    t = timer_sec(scene.frame_current)
    timer_t.data.body = "%02d:%02d.%d" % (int(t) // 60, int(t) % 60, int(t * 10) % 10)
    bar.scale.x = max(0.02, (t % 60) / 60.0)
bpy.app.handlers.frame_change_pre.append(_timer_upd)
R_(timer_t); R_(lbl); R_(bar)
cer = [mat("cer_w", (0.9, 0.9, 0.88), 0.25, coat=0.6), mat("cer_r", (0.6, 0.06, 0.05), 0.3, coat=0.6), mat("cer_k", (0.03, 0.03, 0.03), 0.3, coat=0.6)]
coffee_m = mat("coffee", (0.05, 0.02, 0.008), 0.08)
def mug(name, loc, m, parent=None):
    g = empty(name, loc, parent)
    cyl(name + "_b", 0.041, 0.095, (0, 0, 0.0475), m, parent=g)
    cyl(name + "_c", 0.037, 0.003, (0, 0, 0.085), coffee_m, parent=g)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.007, location=(0.045, 0, 0.05), rotation=(R(90), 0, 0))
    h = bpy.context.object; h.name = name + "_h"; h.data.materials.append(m); h.parent = g
    return g
for i, (x, y) in enumerate(((0.15, -1.25), (0.25, -1.42), (1.0, -1.2))):
    R_(mug(f"mug{i}", (x, y, DESK_TOP), cer[i]))
paper_m = mat("paper", (0.92, 0.91, 0.87), 0.8)
for i in range(4):
    R_(box(f"paper{i}", (0.21, 0.297, 0.002), (0.98 + 0.02 * i, -1.0 - 0.01 * i, DESK_TOP + 0.001 + 0.002 * i), paper_m, rot=(0, 0, -8 + 7 * i)))
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.9, 2.15, 0), 0, 1.0))
R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.9, 1.2, 0), 0, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.0, 2.2, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.95, -1.4, 0), 70, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.9, Y1 - 0.03, 1.45), 0, 1.3))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, 0.2, 0), 90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, 0.0, 1.03), 90, 1.0))
R_(plane("rug", (2.2, 1.6), (-0.8, 1.3, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))

# ======================================================================
# 2) MEGAN: xonada o'tiradi (Sitting_Idle_4), chuqur nafas (qo'shimcha COMBINE harakati), havo yutish (Sitting_Disbelief);
#    basseynda suv ostida (Treading_Water), hushdan ketadi (Floating, sekinlashtirilgan)
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
body = next(o for o in mmeshes if "Body" in o.name)
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
LOWER = ("Hips", "UpLeg", "Leg", "Foot", "ToeBase", "Toe_End")
def upper(act, drop=()):
    a = act.copy(); a.name = act.name + "_upper" + "".join(drop); a.use_fake_user = True
    for fc in list(mc._fcurves(a)):
        b = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        if any(b.endswith(s) for s in LOWER) or any(d in b for d in drop): mc._channelbag_remove(a, fc)
    return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0, infl=None, rev=False):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo; s.use_reverse = rev
    if infl is not None:
        s.use_animated_influence = True; s.influence = infl; s.keyframe_insert("influence", frame=start)
    return s
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)
def place(root, f, loc, rot=0.0, rx=0.0):
    root.location = loc; root.rotation_euler = (R(rx), 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)

MEG = Vector((0.6, -0.6, float(os.environ.get("SIT_Z", 0.0))))
UWP = Vector((0.0, 60.0, 0.0))                           # basseyn (suv osti)
PU0 = S["push"][0]
place(mroot, 1, tuple(MEG), 0)
UW_Z = 0.25
place(mroot, PU0, tuple(UWP + V(0, 0, UW_Z)), 0)
ckey(mroot)
SIT = A_("Sitting_Idle_4.fbx")
strip(meg, SIT, 1, repeat=span(SIT, PU0 + 2))
G0 = S["gasp"][0]
# chuqur nafas: qo'shimcha (COMBINE) harakat — ko'krak orqaga, bosh tepaga
def pose_action(name, keys):
    act = bpy.data.actions.new(name); act.use_fake_user = True
    meg.animation_data.action = act
    if hasattr(meg.animation_data, "action_slot") and act.slots: meg.animation_data.action_slot = act.slots[0]
    for bn, ks in keys.items():
        pb = meg.pose.bones["mixamorig:" + bn]; pb.rotation_mode = "QUATERNION"
        for f, (ax, deg) in ks:
            e = [0, 0, 0]; e["XYZ".index(ax)] = R(deg)
            pb.rotation_quaternion = Euler(e).to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f)
        pb.rotation_quaternion = (1, 0, 0, 0)
    meg.animation_data.action = None
    return act
INH = [(4, 0), (12, 0.6), (26, 1.0), (40, 0.85), (G0 + 2, 0.85), (G0 + 5, 0.0), (G0 + 8, 1.9), (G0 + 16, 2.2), (G0 + 24, 1.3), (PU0 - 1, 1.0)]
inh = pose_action("inhale", {"Spine2": [(f, ("X", -7 * k)) for f, k in INH], "Neck": [(f, ("X", -5 * k)) for f, k in INH],
                             "Spine1": [(f, ("X", -3 * k)) for f, k in INH],
                             "Head": [(f, ("X", -8 * max(0.0, k - 1.0) * 1.6)) for f, k in INH]})
tr_ = meg.animation_data.nla_tracks.new(); tr_.name = "inhale"
st_ = tr_.strips.new("inhale", 1, inh)
if hasattr(st_, "action_slot") and inh.slots: st_.action_slot = inh.slots[0]
st_.blend_type = "COMBINE"; st_.extrapolation = "NOTHING"
# suv osti
TW_ = A_("Treading_Water.fbx")
strip(meg, TW_, PU0, repeat=span(TW_, S["faint"][0] - PU0 + 30), speed=0.75)
FLT = A_("Floating.fbx")
FA0 = S["faint"][0]
strip(meg, FLT, F_OUT - 4, src=(20, 109), speed=0.22, bi=14, bo=0)
# hushdan ketgach tana oldinga og'adi va asta cho'kadi
for f, rx, dz in ((F_OUT, 0, 0), (S["drown"][0], 28, -0.25), (END + 1, 48, -0.5)):
    mroot.location = tuple(UWP + V(0, 0, UW_Z + dz)); mroot.rotation_euler = (R(rx), 0, R(8 * (rx / 48))); 
    mroot.keyframe_insert("location", frame=f); mroot.keyframe_insert("rotation_euler", frame=f)
for o in mmeshes: vis(o, ROOM + UWR, recursive=False)

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
mouthT = empty("mouthT", (0.0, 0.004, 0.15), headE)
chestE = child_of_bone("meg_chest", meg, "Spine2")      # Spine2 fazosi: X chap, Y tepa, Z old
chestT = empty("chestT", (0.0, -0.04, 0.08), chestE)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items()}
CHEST = {n: wpos(chestT, (a + b) // 2) for n, (a, b) in S.items()}
print("FACE", {k: tuple(round(x, 3) for x in v) for k, v in FACE.items()})

# ---- yonoqlarni shishirish (shape key "puff") va yuz qizarishi ----
def add_puff(o):
    me = o.data
    if not me.shape_keys: o.shape_key_add(name="Basis", from_mix=False)
    kb = o.shape_key_add(name="puff", from_mix=False); kb.value = 0.0
    W = mroot.matrix_world.inverted() @ o.matrix_world; Wi = W.inverted().to_3x3()
    for i, v in enumerate(me.vertices):
        p = W @ v.co
        if p.y > -0.105 or not (1.515 < p.z < 1.595): continue
        d = Vector((0, 0, 0))
        for sx in (1, -1):
            c = Vector((sx * 0.043, -0.13, 1.553)); r = (p - c).length
            if r < 0.032:
                w = (1 - (r / 0.032) ** 2) ** 2
                n = (p - Vector((sx * 0.018, -0.09, 1.553))); n.z *= 0.3; n.normalize()
                d += n * 0.013 * w
        # lablar qisilgan (biroz oldinga)
        lr = (p - Vector((0, -0.155, 1.537))).length
        if lr < 0.018: d += Vector((0, -0.002, 0)) * (1 - lr / 0.018)
        kb.data[i].co = v.co + Wi @ d
    return kb
puff = add_puff(body)
def puff_k(f, v): puff.value = v; puff.keyframe_insert("value", frame=f)
for f, v in ((1, 0), (24, 0), (34, 1.0), (G0 + 6, 1.0), (G0 + 10, 0.0), (PU0, 1.0), (F_OUT - 2, 1.0), (F_OUT + 3, 0.15)):
    puff_k(f, v)
# yuz rangi: qizarish (xona) va ko'karish (suv osti)
flush_ms = []
for m in body.data.materials:
    if not m or not m.use_nodes: continue
    N = m.node_tree.nodes; L = m.node_tree.links
    b = next((n for n in N if n.type == "BSDF_PRINCIPLED"), None)
    if not b: continue
    src_ = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    fl = value_node(m, "flush", 0.0); bl = value_node(m, "blue", 0.0)
    m1 = N.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; L.new(fl, m1.inputs["Factor"])
    if src_: L.new(src_, m1.inputs[6])
    else: m1.inputs[6].default_value = b.inputs["Base Color"].default_value
    m1.inputs[7].default_value = (1.0, 0.36, 0.32, 1)
    m2 = N.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; L.new(bl, m2.inputs["Factor"])
    L.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (0.62, 0.72, 0.95, 1)
    L.new(m2.outputs[2], b.inputs["Base Color"])
    flush_ms.append(m)
for m in flush_ms:
    for f, a_, b_ in ((1, 0, 0), (40, 0, 0), (149, 0.25, 0), (203, 0.6, 0), (G0, 0.75, 0), (G0 + 20, 0.4, 0), (PU0, 0, 0.1),
                      (F_OUT, 0.0, 0.35), (END, 0.0, 0.6)):
        val_key(m, "flush", f, a_); val_key(m, "blue", f, b_)

# ======================================================================
# 3) RENTGEN: shaffof Megan; ko'krak (o'pkalar, bronxlar, qovurg'alar, yurak, diafragma);
#    bosh suyagi, miya, miya ustunidagi CO2 sensori, diafragma nervlari
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
for o in mmeshes: vis(o, ROOM + UWR, recursive=False)
def bone_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.2)
    gl = value_node(m, "glow", 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.82, 0.92, 1.0, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.08), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.75), 0.12, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
skm = bone_mat("xr_bone")
# ---- bosh suyagi (BlenderKit 49c13194) ----
skullE = empty("skullE", (0, -0.012, 0.034), headE); skullE.rotation_euler = (R(-90), 0, 0); skullE.scale = (0.8,) * 3
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=BK + "49c13194_u.glb")
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.type == "MESH" and o.name.startswith("Text"): bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.parent is None: o.parent = skullE
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(skm)
vis(skullE, XR)
# ---- miya + miya ustuni + CO2 sensori ----
xb_m = brain_mat2("xbrain_m", 0.7)
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, XR)
stem_m = brain_mat2("stem_m", 0.5)
stem = P.tube("bstem", [(0, 0.085, 0.02), (0, 0.05, 0.0), (0, 0.0, -0.012), (0, -0.05, -0.015)], 0.011, stem_m, headE,
              taper=[1.0, 0.85, 0.7, 0.6])
vis(stem, XR, recursive=False)
sens_m = bpy.data.materials.new("sensor"); sens_m.use_nodes = True
_N = sens_m.node_tree.nodes; _L = sens_m.node_tree.links; _N.remove(_N["Principled BSDF"])
_em = _N.new("ShaderNodeEmission"); _mx = _N.new("ShaderNodeMix"); _mx.data_type = "RGBA"
_mx.inputs[6].default_value = (0.2, 1.0, 0.45, 1); _mx.inputs[7].default_value = (1.0, 0.05, 0.03, 1)
L_red = value_node(sens_m, "red", 0.0); _L.new(L_red, _mx.inputs["Factor"]); _L.new(_mx.outputs[2], _em.inputs["Color"])
_L.new(value_node(sens_m, "glow", 2.0), _em.inputs["Strength"]); _L.new(_em.outputs[0], _N["Material Output"].inputs[0])
sensor = sphere("co2_sensor", 0.0075, (0, 0.035, 0.004), sens_m, sub=3, parent=headE)
vis(sensor, XR, recursive=False)
AL0, AL1 = S["alarm"]; BR0 = S["brain"][0]
val_key(sens_m, "red", 1, 0.0); val_key(sens_m, "red", AL0 + 10, 0.0); val_key(sens_m, "red", AL0 + 40, 1.0)
val_key(sens_m, "glow", 1, 2.0)
for f in range(AL0 + 10, S["panic"][1], 8):
    val_key(sens_m, "glow", f, 2.0); val_key(sens_m, "glow", f + 3, 9.0 if f > F_SAFE - 6 else 5.0)
for fc in mc._fcurves(sens_m.node_tree.animation_data.action):
    if "glow" in fc.data_path:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# signal halqalari (sonar kabi tarqaladi)
ring_ms = []
for i in range(3):
    m = mat(f"aring{i}", (1, 0.1, 0.05), 0.5, emit=6.0, emit_col=(1.0, 0.12, 0.05)); ring_ms.append(m)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.01, minor_radius=0.0008, major_segments=64, minor_segments=8)
    rg = bpy.context.object; rg.name = f"aring{i}"; rg.data.materials.append(m); rg.parent = headE
    rg.location = (0, 0.035, 0.004); rg.rotation_euler = (R(90), 0, 0)
    on = []
    for f0 in range(AL0 + 30 + i * 6, S["panic"][1] - 14, 18):
        key(rg, f0, scale=0.3); key(rg, f0 + 15, scale=6.5)
        on += list(range(f0, f0 + 15))
    interp(rg, "LINEAR", "scale")
    frames_vis(rg, [f for f in on if any(a <= f <= b for a, b in XR)])
# ---- ko'krak qafasi (Spine2 fazosi) ----
CZ = 0.068                                               # ko'krak bo'shlig'i markazi (old-orqa)
lung_m = brain_mat2("lung_m", 0.45)
lung_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.01
lungs = []
for sx in (1, -1):
    le = empty(f"lungE{sx}", (sx * 0.062, -0.0, CZ), chestE)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=1.0)
    lo = bpy.context.object; lo.name = f"lung{sx}"
    for v in lo.data.vertices:
        x, y, z = v.co.x, v.co.z, v.co.y                  # y = tepa (Spine2), z = old
        if y > 0: x *= 1 - 0.5 * y; z *= 1 - 0.4 * y
        if y < -0.55: y = -0.55 + (y + 0.55) * 0.25
        y += 0.12 * max(0.0, 1 - x * x - z * z) * (1 if y < 0 else 0)
        if x * sx < -0.35: x = -sx * 0.35 + (x + sx * 0.35) * 0.3
        v.co = Vector((x * 0.062, y * 0.13, z * 0.08))
    for p in lo.data.polygons: p.use_smooth = True
    lo.data.materials.append(lung_m); lo.parent = le; lo.rotation_euler = (R(90), 0, 0)
    lo.rotation_euler = (0, 0, 0)
    # mesh'da y = tepa bo'lishi uchun (yuqorida z<->y almashtirildi)
    lungs.append(le)
    vis(le, XR)
LU0, LU1 = S["lungs"]
for le in lungs:
    key(le, 1, scale=(0.82, 0.9, 0.8)); key(le, LU0 + 8, scale=(0.82, 0.9, 0.8)); key(le, LU0 + 50, scale=(1.12, 1.06, 1.15))
    key(le, S["pain"][0], scale=(1.12, 1.06, 1.15))
    for f in range(S["pain"][0] + 6, S["pain"][1], 12):          # bosim: o'pkalar zo'riqib titraydi
        key(le, f, scale=(1.16, 1.08, 1.19)); key(le, f + 3, scale=(1.1, 1.05, 1.13))
    key(le, S["diaph"][0], scale=(1.12, 1.06, 1.15))
    for f in (F_FORCE, F_FORCE + 9, F_FORCE + 17):                # majburiy qisqarish
        key(le, f, scale=(1.05, 0.98, 1.08)); key(le, f + 3, scale=(1.13, 1.07, 1.16))
val_key(lung_m, "glow", 1, 0.45); val_key(lung_m, "red", 1, 0.0)
val_key(lung_m, "glow", LU0 + 10, 0.45); val_key(lung_m, "glow", LU0 + 45, 1.4)
PA0, PA1 = S["pain"]
val_key(lung_m, "red", PA0 + 2, 0.0); val_key(lung_m, "red", PA0 + 14, 0.8)
for f in range(PA0 + 6, PA1 + 1, 12):
    val_key(lung_m, "glow", f, 1.2); val_key(lung_m, "glow", f + 3, 4.5 if f >= F_PAIN - 3 else 3.0)
val_key(lung_m, "red", S["diaph"][0], 1.0)
# bronxlar (havo oqimi: ko'k impuls poyezdi)
air_m = train_mat("air", col=(0.5, 0.75, 1.0), pcol=(0.4, 0.8, 1.0))
TRA = [(0, 0.2, CZ - 0.005), (0, 0.12, CZ + 0.0), (0, 0.04, CZ + 0.0)]
br_objs = [P.tube("trachea", TRA, 0.008, air_m, chestE)]
rb = random.Random(5)
for sx in (1, -1):
    main = [(0, 0.04, CZ), (sx * 0.025, 0.02, CZ), (sx * 0.048, -0.01, CZ + 0.005)]
    br_objs.append(P.tube(f"bronch{sx}", main, 0.0055, air_m, chestE))
    for k in range(7):
        a = R(rb.uniform(-150, 150)); L_ = rb.uniform(0.04, 0.075)
        p0 = Vector((sx * 0.048, -0.01, CZ + 0.005))
        d = Vector((sx * abs(math.sin(a)) * 0.7, math.cos(a), rb.uniform(-0.5, 0.5))).normalized()
        p1 = p0 + d * L_ * 0.5 + Vector((0, 0, rb.uniform(-0.01, 0.01))); p2 = p0 + d * L_
        br_objs.append(P.tube(f"bron{sx}_{k}", [tuple(p0), tuple(p1), tuple(p2)], 0.0028, air_m, chestE, taper=[1, 0.7, 0.35]))
for o in br_objs: vis(o, XR, recursive=False)
val_key(air_m, "count", 1, 3.0); val_key(air_m, "amp", 1, 0.0); val_key(air_m, "glow", 1, 0.5); val_key(air_m, "phase", 1, 0.0)
val_key(air_m, "amp", LU0 + 4, 0.0); val_key(air_m, "amp", LU0 + 8, 30.0); val_key(air_m, "amp", LU0 + 52, 30.0); val_key(air_m, "amp", LU0 + 62, 0.0)
val_key(air_m, "phase", LU0 + 4, 0.0); val_key(air_m, "phase", LU0 + 62, 6.0)
for fc in mc._fcurves(air_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# qovurg'alar, umurtqa, to'sh suyagi
rib_objs = []
for i in range(9):
    y = 0.15 - i * 0.03; ax_ = 0.07 + 0.085 * min(1.0, (i + 1) / 4); az = 0.112
    th1 = math.pi - (0.3 if i < 7 else 0.95 + 0.2 * (i - 7))
    for sx in (1, -1):
        pts = []
        for k in range(10):
            th = 0.2 + (th1 - 0.2) * k / 9
            pts.append((sx * ax_ * math.sin(th) * (1 - 0.12 * math.sin(th) ** 8), y - 0.08 * (th / math.pi) ** 1.6, CZ - az * math.cos(th) - 0.015))
        rib_objs.append(P.tube(f"rib{i}_{sx}", pts, 0.0036, skm, chestE))
rib_objs.append(P.tube("spine", [(0, 0.24, -0.03), (0, 0.1, -0.035), (0, -0.05, -0.03), (0, -0.2, -0.02)], 0.011, skm, chestE))
rib_objs.append(box("sternum", (0.022, 0.15, 0.01), (0, 0.06, CZ + 0.093), skm, rot=(-12, 0, 0), parent=chestE))
for o in rib_objs: vis(o, XR, recursive=False)
# yurak (uradi)
heart_m = mat("heart", (0.55, 0.04, 0.05), 0.35, emit=1.5, emit_col=(1.0, 0.1, 0.08), sss=0.3)
heart = sphere("heart", 1.0, (0.018, -0.06, CZ + 0.035), heart_m, scale=(0.038, 0.045, 0.034), sub=4, parent=chestE)
heart.rotation_euler = (0, 0, R(-25)); vis(heart, XR, recursive=False)
f = 1; k = 0
while f < END:
    bpm = 9 if f < S["pain"][0] else 7
    key(heart, f, scale=(0.038, 0.045, 0.034)); key(heart, f + 2, scale=(0.044, 0.05, 0.04)); f += bpm
# diafragma (gumbaz)
dia_m = mat("diaph", (0.45, 0.06, 0.06), 0.4, emit=0.35, emit_col=(1.0, 0.25, 0.2), sss=0.2)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0)
dia = bpy.context.object; dia.name = "diaphragm"
bm = bmesh.new(); bm.from_mesh(dia.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context="VERTS"); bm.to_mesh(dia.data); bm.free()
for v in dia.data.vertices: v.co = Vector((v.co.x * 0.105, v.co.z * 0.055, v.co.y * 0.08))
for p in dia.data.polygons: p.use_smooth = True
so_ = dia.modifiers.new("solid", "SOLIDIFY"); so_.thickness = 0.004
dia.data.materials.append(dia_m); dia.parent = chestE; dia.location = (0, -0.112, CZ)
vis(dia, XR, recursive=False)
DI0, DI1 = S["diaph"]
key(dia, 1, loc=(0, -0.112, CZ), scale=1.0); key(dia, DI0, loc=(0, -0.112, CZ), scale=1.0)
for f in (F_FORCE - 2, F_FORCE + 7, F_FORCE + 15):
    key(dia, f, loc=(0, -0.112, CZ), scale=1.0); key(dia, f + 3, loc=(0, -0.132, CZ), scale=(1.0, 0.45, 1.0))
    key(dia, f + 6, loc=(0, -0.114, CZ), scale=(1.0, 0.95, 1.0))
# diafragma nervlari: miya ustunidan bo'yin orqali diafragmaga (impuls poyezdi)
nerve_ms = []; nerves = []
for sx in (1, -1):
    pts = [(sx * 0.006, 0.215, 0.0), (sx * 0.02, 0.15, 0.03), (sx * 0.045, 0.07, 0.06), (sx * 0.075, -0.04, 0.085), (sx * 0.06, -0.14, 0.08)]
    m = train_mat(f"phren{sx}", col=(0.9, 0.75, 0.4), pcol=(1.0, 0.35, 0.2)); nerve_ms.append(m)
    t_ = P.tube(f"phren{sx}", pts, 0.0022, m, chestE); nerves.append(t_)
for t_ in nerves: vis(t_, XR, recursive=False)
PN0, PN1 = S["panic"]
for m in nerve_ms:
    val_key(m, "count", 1, 3.0); val_key(m, "amp", 1, 0.0); val_key(m, "phase", 1, 0.0); val_key(m, "glow", 1, 0.5)
    val_key(m, "amp", F_CHOKE - 4, 0.0); val_key(m, "amp", F_CHOKE, 28.0); val_key(m, "phase", F_CHOKE - 4, 0.0)
    val_key(m, "phase", DI1 + 1, (DI1 + 1 - F_CHOKE + 4) / 8.0)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        if "phase" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
val_key(xb_m, "glow", 1, 0.7); val_key(xb_m, "red", 1, 0.0)
val_key(xb_m, "glow", F_CHOKE - 8, 0.7)
for f in range(F_CHOKE - 6, PN1 + 1, 5):
    val_key(xb_m, "glow", f, 5.0); val_key(xb_m, "glow", f + 2, 1.5)
val_key(xb_m, "red", F_CHOKE - 7, 0.0); val_key(xb_m, "red", F_CHOKE - 6, 1.0)
for fc in mc._fcurves(xb_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

# ======================================================================
# 4) QON TOMIRI ICHI: eritrotsitlar (ko'k O2 bilan), CO2 molekulalari; oqim +X yo'nalishida
# ======================================================================
MIC = V(0.0, -60.0, 1.5)
RV = 1.0
M0 = S["myth"][0]
VC, VB = 0.05, 0.065                                     # kamera tashuvchisi / qon oqimi tezligi (m/kadr)
def carrier_x(f): return VC * (f - M0)
vesE = empty("vessel", tuple(MIC))
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=RV, depth=70, location=(0, 0, 0), rotation=(0, R(90), 0), end_fill_type="NOTHING")
ves = bpy.context.object; ves.name = "vessel_wall"; bpy.ops.object.transform_apply(rotation=True)
bm = bmesh.new(); bm.from_mesh(ves.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 1], cuts=140)
bm.to_mesh(ves.data); bm.free()
for p in ves.data.polygons: p.use_smooth = True
ves.location = (17.5, 0, 0); ves.parent = vesE
vw_m = bpy.data.materials.new("vessel_m"); vw_m.use_nodes = True
N = vw_m.node_tree.nodes; L = vw_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.8; b.inputs["Coat Roughness"].default_value = 0.1
b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.1
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 3.0
mpv = N.new("ShaderNodeMapping"); mpv.inputs["Scale"].default_value = (0.35, 1.0, 1.0); L.new(tc.outputs["Object"], mpv.inputs[0]); L.new(mpv.outputs[0], vo.inputs["Vector"])
nzv = N.new("ShaderNodeTexNoise"); nzv.inputs["Scale"].default_value = 2.5; nzv.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nzv.inputs["Vector"])
cr = N.new("ShaderNodeMix"); cr.data_type = "RGBA"; cr.inputs[6].default_value = (0.32, 0.02, 0.03, 1); cr.inputs[7].default_value = (0.75, 0.12, 0.1, 1)
L.new(nzv.outputs["Fac"], cr.inputs["Factor"]); L.new(cr.outputs[2], b.inputs["Base Color"])
bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.4; L.new(vo.outputs["Distance"], bmp.inputs["Height"]); L.new(bmp.outputs[0], b.inputs["Normal"])
b.inputs["Emission Color"].default_value = (1.0, 0.15, 0.1, 1)
vw_glow = value_node(vw_m, "glow", 0.0); L.new(P.math_n(N, L, "MULTIPLY", nzv.outputs["Fac"], vw_glow), b.inputs["Emission Strength"])
ves.data.materials.append(vw_m)
vis(vesE, MICR)
BP0, BP1 = S["bp"]
key(ves, 1, scale=1.0); key(ves, BP0, scale=1.0)
for f, s_ in ((F_BP - 2, 1.0), (F_BP + 2, (1, 0.72, 0.72)), (F_BP + 9, (1, 1.22, 1.22)), (F_BP + 15, (1, 0.8, 0.8)),
              (F_BP + 21, (1, 1.18, 1.18)), (F_BP + 27, (1, 0.78, 0.78)), (F_BP + 33, (1, 1.15, 1.15)), (BP1 + 1, (1, 0.9, 0.9))):
    key(ves, f, scale=s_)
val_key(vw_m, "glow", 1, 0.0); val_key(vw_m, "glow", F_BP - 1, 0.0)
for f in range(F_BP, BP1 + 1, 6): val_key(vw_m, "glow", f, 1.5); val_key(vw_m, "glow", f + 3, 0.3)
# eritrotsit (ikki tomoni botiq disk)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=1.0)
rbc0 = bpy.context.object; rbc0.name = "rbc_proto"
for v in rbc0.data.vertices:
    r = min(1.0, math.hypot(v.co.x, v.co.y)); sgn = 1 if v.co.z >= 0 else -1
    h = 0.5 * math.sqrt(max(0.0, 1 - r * r)) * (0.24 + 2.0 * r * r - 1.12 * r ** 4)
    v.co = Vector((v.co.x * 0.18, v.co.y * 0.18, sgn * max(0.012, h) * 0.18))
for p in rbc0.data.polygons: p.use_smooth = True
rbc_m = mat("rbc_m", (0.62, 0.03, 0.03), 0.3, sss=0.5, coat=0.4)
rbc_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.03
rbc_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (1.0, 0.2, 0.1)
rbc0.data.materials.append(rbc_m)
rbc0.modifiers.new("s", "SUBSURF").levels = 1
rbc0.hide_render = True
# O2 (ikki ko'k shar) va CO2 (O=C=O) molekulalari
def molecule(name, parts_, m_list):
    objs = []
    for (p, r_), m in zip(parts_, m_list):
        objs.append(sphere(name + "_p", r_, p, m, sub=3))
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join()
    o = bpy.context.object; o.name = name; o.location = (0, 0, 0)
    return o
o2_m = mat("o2_m", (0.02, 0.2, 1.0), 0.2, emit=1.0, emit_col=(0.02, 0.3, 1.0), coat=0.6)
c_m = mat("co2_c", (0.015, 0.015, 0.018), 0.3, coat=0.7, emit=0.08, emit_col=(0.6, 0.3, 1.0))
oo_m = mat("co2_o", (0.05, 0.045, 0.06), 0.3, coat=0.7, emit=0.12, emit_col=(0.6, 0.3, 1.0))
o2p = molecule("o2_proto", [((-0.032, 0, 0), 0.04), ((0.032, 0, 0), 0.04)], [o2_m, o2_m]); o2p.hide_render = True
co2p = molecule("co2_proto", [((0, 0, 0), 0.05), ((-0.075, 0, 0), 0.042), ((0.075, 0, 0), 0.042)], [c_m, oo_m, oo_m]); co2p.hide_render = True
def inst(proto, name):
    o = bpy.data.objects.new(name, proto.data); sc.collection.objects.link(o)
    for md in proto.modifiers:
        n_ = o.modifiers.new(md.name, md.type)
        if md.type == "SUBSURF": n_.levels = md.levels; n_.render_levels = md.render_levels
    return o
mic_objs = []
rr = random.Random(21)
O2_DROP0, O2_DROP1 = S["o2"][0] - 4, S["o2"][1] - 6
def flow_keys(o, x0, y, z, spin):
    """x0 = M0 kadrdagi joylashuv (tomir boshiga nisbatan); chiziqli oqim"""
    for f in (1, END):
        o.location = (x0 + VB * (f - M0), y, z); o.keyframe_insert("location", frame=f)
    o.rotation_euler = spin[0]; o.keyframe_insert("rotation_euler", frame=1)
    o.rotation_euler = spin[1]; o.keyframe_insert("rotation_euler", frame=END)
    interp(o, "LINEAR")
NRBC = int(os.environ.get("NRBC", 150))
o2_list = []
for i in range(NRBC):
    o = inst(rbc0, f"rbc{i}"); o.parent = vesE; mic_objs.append(o)
    a = rr.uniform(0, 2 * math.pi); r_ = 0.72 * math.sqrt(rr.random())
    x0 = rr.uniform(-16, 13)
    e0 = Euler((rr.uniform(0, 6.3), rr.uniform(0, 6.3), rr.uniform(0, 6.3)))
    e1 = Euler((e0.x + rr.uniform(-6, 6), e0.y + rr.uniform(-6, 6), e0.z + rr.uniform(-3, 3)))
    flow_keys(o, x0, r_ * math.cos(a), r_ * math.sin(a), (e0, e1))
    # 2-3 ta O2 eritrotsitga yopishgan
    for k in range(rr.randint(2, 3)):
        m_ = inst(o2p, f"o2_{i}_{k}"); m_.parent = o; mic_objs.append(m_)
        t = rr.uniform(0, 2 * math.pi); side = rr.choice((1, -1))
        base = Vector((0.13 * math.cos(t), 0.13 * math.sin(t), side * 0.045))
        m_.rotation_euler = (rr.uniform(0, 3), rr.uniform(0, 3), t)
        keep = rr.random() < 0.15                                    # 15% qoladi
        o2_list.append((m_, None if keep else df + 10))
        df = rr.randint(O2_DROP0, O2_DROP1)
        key(m_, 1, loc=tuple(base), scale=1.0); key(m_, df, loc=tuple(base), scale=1.0)
        if not keep:
            key(m_, df + 10, loc=tuple(base * 2.2 + Vector((0, 0, side * 0.15))), scale=0.0)
        interp(m_, "LINEAR", "location"); interp(m_, "LINEAR", "scale")
# CO2: ko'payib boradi (paydo bo'lish kadrlari "co2" kadri davomida zichlashadi)
C0, C1 = S["co2"]
NCO2 = int(os.environ.get("NCO2", 420))
for i in range(NCO2):
    o = inst(co2p, f"co2_{i}"); o.parent = vesE; mic_objs.append(o)
    a = rr.uniform(0, 2 * math.pi); r_ = 0.82 * math.sqrt(rr.random())
    x0 = rr.uniform(-16, 13)
    e0 = Euler((rr.uniform(0, 6.3), rr.uniform(0, 6.3), rr.uniform(0, 6.3)))
    e1 = Euler((e0.x + rr.uniform(-25, 25), e0.y + rr.uniform(-25, 25), e0.z + rr.uniform(-25, 25)))
    u = rr.random()
    if u < 0.06: app = 1
    elif u < 0.2: app = rr.randint(S["o2"][0], C0)
    else: app = int(C0 + (C1 - 30 - C0) * (rr.random() ** 0.7))
    if app > 1:                                            # paydo bo'lganda kamera oldida (0.3..6 m)
        x0 = carrier_x(app) + rr.uniform(0.3, 6.0) - VB * (app - M0)
    flow_keys(o, x0, r_ * math.cos(a), r_ * math.sin(a), (e0, e1))
    sc_ = rr.uniform(0.8, 1.3)
    o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=max(1, app - 1))
    o.scale = (sc_,) * 3; o.keyframe_insert("scale", frame=app + 6)
for o in mic_objs:
    if o.parent is vesE: vis(o, MICR, recursive=False)
for m_, lim in o2_list:                                   # bolalarga alohida vis (otadan keyin)
    vis(m_, [(a, min(b, lim) if lim else b) for a, b in MICR if not lim or a <= lim], recursive=False)
mic_objs = [o for o in mic_objs if o.parent is vesE]
# kamera tashuvchisi (oqim bilan birga)
carr = empty("carrier", (0, 0, 0), vesE)
for f in (1, END):
    carr.location = (carrier_x(f), 0, 0); carr.keyframe_insert("location", frame=f)
interp(carr, "LINEAR")
# shakl (plazma)da suzuvchi mayda zarralar (chuqurlik hissi)
dust_m = mat("plasma_dust", (0.9, 0.6, 0.4), 0.5, emit=0.8, emit_col=(1.0, 0.55, 0.35))
for i in range(120):
    a = rr.uniform(0, 2 * math.pi); r_ = 0.9 * math.sqrt(rr.random())
    d_ = sphere(f"pdust{i}", rr.uniform(0.004, 0.012), (0, 0, 0), dust_m, sub=1, parent=vesE)
    flow_keys(d_, rr.uniform(-16, 13), r_ * math.cos(a), r_ * math.sin(a), (Euler(), Euler()))
    vis(d_, MICR, recursive=False)

# ======================================================================
# 5) BASSEYN (suv osti): plitkali tub va devorlar, to'lqinli yorug' sirt, ko'k suv hajmi, kaustika, pufakchalar
# ======================================================================
uw_objs = []
def U_(o): uw_objs.append(o); return o
PX, PY, PD = 4.0, 3.0, 2.9                              # yarim o'lchamlar, chuqurlik (suv sathi z = PD)
tiles = pbr("pool_tiles", "blue_floor_tiles_01", 1.6)
# kaustika: tub va devorlarga harakatlanuvchi yorug' to'r (Voronoi chegaralari, W vaqt bilan)
Nt = tiles.node_tree.nodes; Lt = tiles.node_tree.links; bt = Nt["Principled BSDF"]
tct = Nt.new("ShaderNodeTexCoord"); vc_ = Nt.new("ShaderNodeTexVoronoi"); vc_.voronoi_dimensions = "4D"; vc_.feature = "DISTANCE_TO_EDGE"
vc_.inputs["Scale"].default_value = 4.5; Lt.new(tct.outputs["Object"], vc_.inputs["Vector"])
cw = value_node(tiles, "w", 0.0); Lt.new(cw, vc_.inputs["W"])
ca = P.math_n(Nt, Lt, "POWER", P.math_n(Nt, Lt, "SUBTRACT", 1.0, P.math_n(Nt, Lt, "MULTIPLY", vc_.outputs["Distance"], 14.0), clamp=True), 3.0)
bt.inputs["Emission Color"].default_value = (0.75, 0.95, 1.0, 1)
Lt.new(P.math_n(Nt, Lt, "MULTIPLY", ca, 0.7), bt.inputs["Emission Strength"])
val_key(tiles, "w", 1, 0.0); val_key(tiles, "w", END, 12.0)
for fc in mc._fcurves(tiles.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
U_(box("pool_floor", (2 * PX, 2 * PY, 0.1), tuple(UWP + V(0, 0, -0.05)), tiles))
for nm, sz, off in (("pw1", (2 * PX, 0.1, PD + 0.6), (0, -PY - 0.05, (PD + 0.6) / 2)), ("pw2", (2 * PX, 0.1, PD + 0.6), (0, PY + 0.05, (PD + 0.6) / 2)),
                    ("pw3", (0.1, 2 * PY, PD + 0.6), (-PX - 0.05, 0, (PD + 0.6) / 2)), ("pw4", (0.1, 2 * PY, PD + 0.6), (PX + 0.05, 0, (PD + 0.6) / 2))):
    U_(box(nm, sz, tuple(UWP + V(*off)), tiles))
lane_m = mat("lane", (0.02, 0.05, 0.25), 0.4)
for x in (-2.0, 0.0, 2.0):
    U_(box(f"lane{x}", (0.25, 2 * PY - 0.6, 0.005), tuple(UWP + V(x, 0, 0.003)), lane_m))
U_(box("pool_lamp", (0.4, 0.05, 0.25), tuple(UWP + V(0, PY - 0.01, 1.3)), mat("plamp", (0.8, 0.95, 1.0), 0.3, emit=6.0)))
# suv sathi (pastdan): yorug', to'lqinli; Transparent bilan aralash (osmon ko'rinadi)
surf_m = bpy.data.materials.new("surface"); surf_m.use_nodes = True
N = surf_m.node_tree.nodes; L = surf_m.node_tree.links; N.remove(N["Principled BSDF"])
tcs_ = N.new("ShaderNodeTexCoord"); vs = N.new("ShaderNodeTexVoronoi"); vs.voronoi_dimensions = "4D"; vs.feature = "DISTANCE_TO_EDGE"
vs.inputs["Scale"].default_value = 2.2; L.new(tcs_.outputs["Object"], vs.inputs["Vector"])
sw = value_node(surf_m, "w", 0.0); L.new(sw, vs.inputs["W"])
nzs = N.new("ShaderNodeTexNoise"); nzs.noise_dimensions = "4D"; nzs.inputs["Scale"].default_value = 1.6; nzs.inputs["Detail"].default_value = 3.0
nzs.inputs["Distortion"].default_value = 1.5; L.new(tcs_.outputs["Object"], nzs.inputs["Vector"]); L.new(sw, nzs.inputs["W"])
ridge = P.math_n(N, L, "ADD", P.math_n(N, L, "POWER", nzs.outputs["Fac"], 4.0),
                 P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", vs.outputs["Distance"], 10.0), clamp=True), 4.0), 0.25))
ems = N.new("ShaderNodeEmission"); ems.inputs["Color"].default_value = (0.7, 0.93, 1.0, 1)
L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", ridge, 9.0), 0.35), ems.inputs["Strength"])
L.new(ems.outputs[0], N["Material Output"].inputs["Surface"])
val_key(surf_m, "w", 1, 0.0); val_key(surf_m, "w", END, 9.0)
for fc in mc._fcurves(surf_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
U_(plane("water_surface", (2 * PX + 0.2, 2 * PY + 0.2), tuple(UWP + V(0, 0, PD)), surf_m, rot=(180, 0, 0)))
# suv hajmi (ko'k tuman)
vol_m = bpy.data.materials.new("water_vol"); vol_m.use_nodes = True
N = vol_m.node_tree.nodes; L = vol_m.node_tree.links; N.remove(N["Principled BSDF"])
pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (0.02, 0.22, 0.38, 1)
pv.inputs["Density"].default_value = float(os.environ.get("UW_DENS", 0.3)); pv.inputs["Absorption Color"].default_value = (0.0, 0.28, 0.5, 1)
L.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
wv_ = U_(box("water_volume", (2 * PX - 0.02, 2 * PY - 0.02, PD - 0.01), tuple(UWP + V(0, 0, PD / 2)), vol_m))
for o in uw_objs: vis(o, UWR)
# pufakchalar: itarib turganda burundan mayda, hushdan ketganda og'izdan katta to'p
bub_m = P.bubble_material()
bub_objs = []
rbb = random.Random(33)
def bubbles(n, f0, f1, rmin, rmax, seed, spread=0.01):
    rb_ = random.Random(seed)
    for i in range(n):
        s = rb_.randint(f0, f1); p0 = wpos(mouthT, s) + Vector((rb_.uniform(-spread, spread), rb_.uniform(-0.02, 0.0), rb_.uniform(-spread, spread)))
        r_ = rb_.uniform(rmin, rmax)
        o = sphere(f"bub{seed}_{i}", r_, tuple(p0), bub_m, scale=(1, 1, 0.85), sub=3)
        vz = 0.005 + r_ * 0.35; ph = rb_.uniform(0, 6)
        for f in range(s, min(END, s + 80) + 1, 4):
            t = f - s
            key(o, f, loc=tuple(p0 + Vector((0.01 * math.sin(t * 0.3 + ph), 0.01 * math.cos(t * 0.25 + ph), vz * t))))
        interp(o, "LINEAR", "location")
        vis(o, [(s, min(END, s + 80))], recursive=False)
        bub_objs.append(o)
bubbles(10, PU0 + 10, S["push"][1], 0.003, 0.007, 1)
bubbles(45, F_OUT, F_OUT + 22, 0.004, 0.016, 2, spread=0.02)
bubbles(12, S["drown"][0] - 20, END, 0.003, 0.008, 3)

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
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002, parent=None):
    t = empty(name + "_t", (0, 0, 0), parent); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip)
    if parent: c.parent = parent
    path_keys(c, pts)
    return c
def mid(n): a, b = S[n]; return (a + b) // 2
HEADW = {n: wpos(headE, mid(n)) for n in S}
SENS = wpos(sensor, mid("alarm"))
# 1 ILGAK: poldan, keng ob'ektiv, tez push-in
H0, H1 = S["hook"]; FP = FACE["hook"]
c = abs_cam("hook", [(H0, FP + V(0.62, -0.68, -0.4)), (H1, FP + V(0.3, -0.46, -0.22))],
            [(H0, FP + V(0, -0.02, -0.1)), (H1, FP + V(0, 0.0, -0.03))], 15, 2.8)
lens_keys(c, [(H0, 14), (H1, 19)])
# 2 sekundomer: yelka ortidan noutbuk ekraniga crash push
T0, T1 = S["timer"]; SCR = LAP + V(0, -0.135, 0.125)
c = abs_cam("timer", [(T0, SCR + V(-0.12, 0.62, 0.3)), (T0 + 8, SCR + V(-0.05, 0.44, 0.18)), (T1, SCR + V(-0.03, 0.4, 0.14))],
            [(T0, SCR + V(0, 0, 0.0)), (T1, SCR + V(0, 0, -0.01))], 28, 2.8)
lens_keys(c, [(T0, 24), (T0 + 8, 34), (T1, 36)])
# 3 o'pkalar: rentgen ko'krak, aylanma
CL = CHEST["lungs"]
c = abs_cam("lungs", [(LU0, CL + V(0.55, -0.55, 0.12)), (LU0 + 38, CL + V(0.05, -0.75, 0.08)), (LU1, CL + V(-0.5, -0.5, 0.02))],
            [(LU0, CL + V(0, 0, 0.04)), (LU1, CL + V(0, 0, 0.0))], 30, 4.0)
# 4 yonoqlar: yuzga yaqin, qo'l kamerasi; old planda sekundomer
CK0, CK1 = S["cheeks"]
c = rel_cam("cheeks", faceT, 42, 2.0, [(CK0, V(0.17, -0.36, -0.03)), (CK1, V(0.12, -0.3, -0.02))])
shake(c, CK0, CK1, 0.004, seed=4, decay=False)
# 5 og'riq: rentgen ko'krak, old; crash zoom + silkinish
CP = CHEST["pain"]
c = abs_cam("pain", [(PA0, CP + V(0.08, -0.95, 0.05)), (F_PAIN - 1, CP + V(0.06, -0.7, 0.04)), (F_PAIN + 2, CP + V(0.04, -0.62, 0.03)), (PA1, CP + V(0.05, -0.58, 0.02))],
            [(PA0, CP + V(0, 0, 0.02)), (PA1, CP + V(0, 0, 0.0))], 24, 4.0)
lens_keys(c, [(PA0, 22), (F_PAIN - 1, 25), (F_PAIN + 2, 33), (PA1, 34)]); shake(c, F_PAIN, F_PAIN + 14, 0.014, seed=5)
# 6 tomir: oqim bilan uchish
MY0, MY1 = S["myth"]
c = abs_cam("myth", [(MY0, (-1.2, 0.45, 0.25)), (MY1, (0.4, 0.3, 0.12))], [(MY0, (2.5, 0.0, 0.0)), (MY1, (3.2, -0.1, 0.0))], 22, 5.6, parent=carr)
# 7 miya: yuzdan miyaga crash zoom
B0, B1 = S["brain"]; HB = HEADW["brain"]; FB = FACE["brain"]
c = abs_cam("brain", [(B0, FB + V(0.12, -0.85, 0.12)), (B0 + 14, FB + V(0.08, -0.5, 0.08)), (B0 + 18, FB + V(0.06, -0.32, 0.05)), (B1, FB + V(0.1, -0.28, 0.0))],
            [(B0, FB), (B1, HB + V(0, 0, 0.05))], 26, 4.0)
lens_keys(c, [(B0, 24), (B0 + 14, 28), (B0 + 18, 40), (B1, 42)]); shake(c, B0 + 18, B0 + 28, 0.008, seed=7)
# 8 signal: sensor atrofida aylanma (pastdan-yondan)
c = abs_cam("alarm", [(AL0, SENS + V(0.3, -0.22, -0.08)), (AL1, SENS + V(-0.28, -0.24, -0.06))], [(AL0, SENS + V(0, 0, 0.02))], 34, 5.6)
shake(c, F_SAFE, F_SAFE + 14, 0.008, seed=8)
# 9 O2 kamayadi: yonlama siljish
O0, O1 = S["o2"]
c = abs_cam("o2", [(O0, (0.0, -0.5, 0.05)), (O1, (0.9, -0.42, 0.1))], [(O0, (1.4, 0.05, 0.0)), (O1, (2.1, 0.05, 0.0))], 30, 5.6, parent=carr)
# 10 CO2 ko'payadi: keng -> "karbonat" da crash zoom
c = abs_cam("co2", [(C0, (-0.6, 0.0, 0.5)), (F_CARB - 1, (0.2, 0.05, 0.35)), (F_CARB + 2, (0.6, 0.05, 0.25)), (C1, (0.7, 0.05, 0.22))],
            [(C0, (3.0, 0.0, 0.0)), (C1, (3.0, 0.0, -0.05))], 18, 5.6, parent=carr)
lens_keys(c, [(C0, 16), (F_CARB - 1, 20), (F_CARB + 2, 34), (C1, 36)]); shake(c, F_CARB, F_CARB + 14, 0.02, seed=10)
# 11 vahima: yondan, boshdan bo'yin bo'ylab pastga
HP = HEADW["panic"]; CPn = CHEST["panic"]
c = abs_cam("panic", [(PN0, HP + V(0.5, -0.32, 0.12)), (PN1, CPn + V(0.55, -0.4, 0.14))], [(PN0, HP + V(0, 0, 0.06)), (PN1, CPn + V(0, 0, 0.06))], 28, 5.6)
# 12 diafragma: pastdan-oldan, silkinish
CD = CHEST["diaph"]
c = abs_cam("diaph", [(DI0, CD + V(0.25, -0.6, -0.3)), (DI1, CD + V(0.18, -0.5, -0.25))], [(DI0, CD + V(0, 0, -0.08))], 24, 4.0)
shake(c, F_FORCE - 2, DI1, 0.01, seed=12, decay=False)
# 13 havo yutish: past burchak, silkinish
GF = FACE["gasp"]; GA1 = S["gasp"][1]
c = abs_cam("gasp", [(G0, GF + V(0.4, -0.55, -0.3)), (GA1, GF + V(0.3, -0.45, -0.22))], [(G0, GF + V(0, 0, -0.02)), (GA1, GF + V(0, 0.04, 0.03))], 17, 2.8)
shake(c, G0, GA1, 0.012, seed=13)
# 14 suv osti: tubdan keng ob'ektiv, sekin push-in
PU1 = S["push"][1]; FU = FACE["push"]
c = abs_cam("push", [(PU0, FU + V(0.9, -1.9, -1.55)), (PU1, FU + V(0.55, -1.2, -1.2))], [(PU0, FU + V(0, 0, -0.5)), (PU1, FU + V(0, 0, -0.3))], 16, 4.0)
# 15 qon bosimi: tomir markazi, silkinish
c = abs_cam("bp", [(BP0, (-0.3, 0.0, 0.0)), (BP1, (0.5, 0.0, 0.05))], [(BP0, (3.0, 0.2, 0.1))], 16, 8.0, parent=carr)
shake(c, F_BP, BP1, 0.03, seed=15)
# 16 hushdan ketish: yuzga yaqin
FA1 = S["faint"][1]
c = rel_cam("faint", faceT, 40, 2.8, [(FA0, V(0.2, -0.45, 0.05)), (FA1, V(0.1, -0.32, 0.02))])
# 17 cho'kish: tubdan tepaga, yorug' sirt fonida siluet
DR0 = S["drown"][0]; HD = HEADW["drown"]
c = abs_cam("drown", [(DR0, UWP + V(0.5, -0.9, 0.12)), (END, UWP + V(0.35, -0.75, 0.12))], [(DR0, HD + V(0, 0.2, -0.3)), (END, HD + V(0, 0.15, -0.5))], 14, 2.8)
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
# 7) YORUG'LIK VA FON
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
WORLD = {"room": (0.035, (0.004, 0.008, 0.02), 1.0), "xr": (0.0, (0.004, 0.01, 0.028), 1.0), "mic": (0.0, (0.03, 0.002, 0.002), 1.0),
         "uw": (0.0, (0.005, 0.04, 0.07), 1.0)}
def world_of(n):
    return "room" if n in ROOMN else "xr" if n in XRN else "mic" if n in MICN else "uw"
for f, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
# xona (kechqurun): stol lampasi, noutbuk, shift, oy nuri
area("lamp_key", (1.2, -1.35, 1.3), 0.25, (1.0, 0.68, 0.38), lights_for(ROOM, 60.0), target=FT)
area("lap_glow", tuple(LAP + V(0, -0.05, 0.25)), 0.3, (0.6, 0.75, 1.0), lights_for(ROOM, 9.0), target=FT)
area("ceil_fill", (0.0, 0.6, 2.6), 2.0, (1.0, 0.85, 0.7), lights_for(ROOM, 18.0), target=empty("cfT", (0, 0.6, 0)))
area("moon_rim", (0.6, Y0 + 0.3, 2.0), 1.4, (0.55, 0.7, 1.0), lights_for(ROOM, 45.0), target=FT)
area("face_fill", (1.35, -1.05, 1.45), 0.5, (1.0, 0.9, 0.82), lights_for(rng("cheeks", "gasp", "hook"), 14.0), target=FT)
point("lamp_bulb", (1.22, -1.38, 1.18), 0.02, (1.0, 0.7, 0.4), lights_for(ROOM, 6.0))
# rentgen
HT = empty("xrT"); clh = HT.constraints.new("COPY_LOCATION"); clh.target = chestT
area("X_key", tuple(MEG + V(1.2, -1.2, 2.0)), 1.0, (0.8, 0.9, 1.0), lights_for(XR, 25.0), target=HT)
area("X_rim", tuple(MEG + V(-1.0, 0.8, 1.8)), 1.0, (0.3, 0.55, 1.0), lights_for(XR, 30.0), target=HT)
area("X_front", tuple(MEG + V(0.2, -1.4, 1.2)), 0.8, (0.9, 0.95, 1.0), lights_for(XR, 12.0), target=HT)
# tomir ichi: kamera bilan yuradigan "endoskop" chiroqlari
for i, (p, e, col) in enumerate((((0.0, 0.3, 0.45), 60.0, (1.0, 0.8, 0.7)), ((2.5, -0.3, -0.4), 45.0, (1.0, 0.55, 0.45)), ((5.0, 0.2, 0.3), 35.0, (1.0, 0.5, 0.4)))):
    l_ = point(f"mic_l{i}", p, 0.3, col, lights_for(MICR, e)); l_.parent = carr
# suv osti: tepadan quyosh (hajmda nur ustunlari), sirt ostidan yumshoq yorug'lik
sun = bpy.data.objects.new("uw_sun", bpy.data.lights.new("uw_sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(18), R(8), 0); sun.data.angle = R(2); sun.data.color = (0.9, 0.97, 1.0)
for f, e in lights_for(UWR, 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
UT = empty("uwT"); clu = UT.constraints.new("COPY_LOCATION"); clu.target = faceT
area("UW_top", tuple(UWP + V(0.3, -0.6, PD - 0.15)), 2.5, (0.7, 0.92, 1.0), lights_for(UWR, 110.0), target=UT)
area("UW_fill", tuple(UWP + V(1.5, -2.0, 0.6)), 1.0, (0.4, 0.75, 1.0), lights_for(UWR, 40.0), target=UT)
# xona yorug'liklari (quyosh) boshqa dunyolarga tushmasin: quyosh faqat UW kadrlarida yonadi

# ======================================================================
# 8) RENDER
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
