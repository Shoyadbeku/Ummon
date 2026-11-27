# Ko'zni ishqalash — Zack D. Films uslubida 44 s video (1056 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, zack_test/yelim/yelim.py (xona, makro ko'z, kesim, kamera yordamchilari),
# zack_test/qovoq (rentgen materiali, impuls poyezdi); egri chiziqlar/miya: zack_test/burish/parts.py
# Assetlar: zack_test/tools/get_ishqalash.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/ishqalash/ishqalash.py --render
# Sinov:  FRAMES=30,80,200,300,460 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, os.path.join(ZT, "qovoq"))
sys.path.insert(0, os.path.join(ZT, "yelim")); sys.path.insert(0, HERE)
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
import eye as EY
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1056
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (45, "rub"), (115, "xin"), (164, "horror"), (227, "press"), (271, "skull"), (341, "deform"),
         (384, "harder"), (419, "thin"), (500, "bulge"), (549, "cone"), (596, "flash"), (687, "dots"), (769, "retina"),
         (819, "signal"), (894, "habit"), (942, "rupture"), (966, "surgery")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "rub", "harder", "dots", "habit")
XRN = ("xin", "horror", "skull", "signal")
MACN = ("press",)
CUTN = ("deform", "thin", "bulge", "cone", "retina", "rupture")
POVN = ("flash",)
ORN = ("surgery",)
ROOM = rng(*ROOMN); XR = rng(*XRN); MACR = rng(*MACN); CUTR = rng(*CUTN); POVR = rng(*POVN); ORR = rng(*ORN)
F_HORROR = 195      # "dahshatga"
F_OFF = 742         # "yorug'lik emas" — lampa va noutbuk o'chadi
F_BRAIN = 821       # "miyaga"
F_PAIN = 848        # "og'riq"
F_FAKE = 872        # "soxta signallari"
F_CRACK = 952       # "yorilib"

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
em = N.new("ShaderNodeEmission"); L.new(emc.outputs[2], em.inputs["Color"])
scr_on = value_node(screen_m, "on", 2.0); L.new(scr_on, em.inputs["Strength"])
L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
scr = plane("lap_screen", (0.30, 0.19), (0, 0.0005, 0.115), screen_m, rot=(90, 0, 0), parent=scr_par)
scr.rotation_euler = (R(90), 0, R(180))
val_key(screen_m, "on", 1, 2.0); val_key(screen_m, "on", F_OFF, 2.0); val_key(screen_m, "on", F_OFF + 1, 0.0); val_key(screen_m, "on", S["habit"][0], 2.0)
ckey(screen_m.node_tree)
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
# 2) MEGAN: o'tirgan holda (Typing), esnash (Yawn), ko'z ishqalash (Crying, oldinga-orqaga zanjir)
#    operatsiya xonasida yotadi (Laying_Idle)
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
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)

MEG = Vector((0.6, -0.6, 0.0))
ORP = Vector((-40.0, 0.0, 0.0))                          # operatsiya xonasi
place(mroot, 1, tuple(MEG), 0)
SU0, SU1 = S["surgery"]
place(mroot, SU0, tuple(ORP + V(0, 0, -0.1)), 0)
ckey(mroot)
TYP = A_("Typing.fbx")
strip(meg, TYP, 1, repeat=span(TYP, SU0 + 2))
YAW = upper(A_("Yawn.fbx"))
strip(meg, YAW, -14, src=(6, 80), speed=1.15, bi=0, bo=6)
CRY = upper(A_("Crying.fbx"))
RUB0 = 34                                                 # qo'llar ~24 kadrda ko'zga yetadi
strip(meg, CRY, RUB0, src=(1, 31), bi=6, bo=0)
RA, RB = 31, 75                                           # ishqalash bo'lagi (oldinga/orqaga zanjir)
seg = int(round((RB - RA) * 0.8))
f = RUB0 + int(round(30 * 0.8)); k = 0
RUB_END = S["habit"][1] + 6
while f < RUB_END:
    strip(meg, CRY, f, src=(RA, RB), rev=(k % 2 == 1), speed=1.0 if k % 3 else 1.15)
    f += int(round((RB - RA) * 0.8 / (1.0 if k % 3 else 1.15))); k += 1
strip(meg, CRY, f, src=(RB, 189), bi=0, bo=0)
LAY = A_("Laying_Idle.fbx", inplace=False)
strip(meg, LAY, SU0, repeat=span(LAY, SU1 - SU0 + 4))
for o in mmeshes: vis(o, ROOM + ORR, recursive=False)

headE = child_of_bone("meg_head", meg, "Head")
eyeE = empty("eyeE", TW.EYE_H, headE)                     # chap ko'z oldi (Head: X chap, Y tepa, Z old)
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items()}
FACE0 = {n: wpos(faceT, a) for n, (a, b) in S.items()}
print("FACE", {k: tuple(round(x, 3) for x in v) for k, v in FACE.items()})

# ======================================================================
# 3) RENTGEN: shaffof Megan, bosh suyagi, ko'z olmalari, ko'rish nervlari, miya
# ======================================================================
xbody = xr_mat("xr_body")
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name or "Sneakers" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    g.animation_data_clear()        # nusxa asl tananing hide_render harakatini ulashmasin
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
for o in mmeshes: vis(o, ROOM + ORR, recursive=False)
# bosh suyagi (BlenderKit 49c13194): mahalliy -Y old, +Z tepa -> Head fazosi (X chap, Y tepa, Z old)
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
SK_S = float(os.environ.get("SK_S", 0.80))
SK_OFF = tuple(float(x) for x in os.environ.get("SK_OFF", "0,-0.012,0.034").split(","))
skullE = empty("skullE", SK_OFF, headE); skullE.rotation_euler = (R(-90), 0, 0); skullE.scale = (SK_S,) * 3
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=BK + "49c13194_u.glb")
_sk_new = [o for o in bpy.data.objects if o not in _before]
skm = bone_mat("xr_bone")
for o in _sk_new:
    if o.type == "MESH" and o.name.startswith("Text"): bpy.data.objects.remove(o, do_unlink=True); continue
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.parent is None: o.parent = skullE
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(skm)
skull_objs = [o for o in bpy.data.objects if o not in _before]
vis(skullE, XR)
# ko'z olmalari (Head fazosida), ezilish kalitlari
EYEB = []
for sx_, nm in ((1, "L"), (-1, "R")):
    c = empty(f"xeye{nm}", (sx_ * TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2] - 0.0125), headE)
    sq = empty(f"xeye{nm}_sq", (0, 0, 0), c)
    b_, red_ = EY.build_eyeball(f"xeyeball{nm}", 0.0122, "human", sq)
    b_.rotation_euler = (R(-90), 0, 0)
    EYEB.append((c, sq, b_))
xeye_m = EYEB[0][2].data.materials[0]
for c, sq, b_ in EYEB:
    b_.data.materials.clear(); b_.data.materials.append(xeye_m)
    _bb = xeye_m.node_tree.nodes.get("Principled BSDF")
    if _bb: _bb.inputs["Emission Color"].default_value = (1, 1, 1, 1); _bb.inputs["Emission Strength"].default_value = 0.6
def squish(f, k):
    """k = 0 dumaloq, 1 qattiq ezilgan (oldidan bosilgan, ichkariga itarilgan)"""
    for c, sq, b_ in EYEB:
        sq.scale = (1 + 0.09 * k, 1 + 0.07 * k, 1 - 0.24 * k); sq.keyframe_insert("scale", frame=f)
        sq.location = (0, 0, -0.0045 * k); sq.keyframe_insert("location", frame=f)
squish(1, 0.0)
f = S["rub"][0] + 8
while f < S["signal"][1]:
    hard = 1.0 if S["skull"][0] <= f <= S["skull"][1] else 0.55
    squish(f, 0.15 * hard); squish(f + 9, 0.9 * hard); squish(f + 18, 0.35 * hard); squish(f + 27, 1.0 * hard)
    f += 37
for c, sq, b_ in EYEB: vis(c, XR)
# ko'rish nervlari: ko'z ortidan kesishma (xiazma) orqali miyaning ensa qismiga
xb_m = brain_mat2("xbrain_m", 0.8)
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, XR)
nerve_ms = []; nerves = []
for sx_ in (1, -1):
    pts = [(sx_ * 0.033, 0.088, 0.104), (sx_ * 0.026, 0.084, 0.085), (sx_ * 0.008, 0.08, 0.07), (sx_ * 0.012, 0.085, 0.045),
           (sx_ * 0.026, 0.095, 0.01), (sx_ * 0.03, 0.105, -0.03), (sx_ * 0.025, 0.115, -0.06)]
    m = train_mat(f"onerve{sx_}", col=(0.9, 0.75, 0.4), pcol=(1.0, 0.6, 0.25)); nerve_ms.append(m)
    t_ = P.tube(f"onerve{sx_}", pts, 0.0024, m, headE, taper=[1.0] * len(pts)); nerves.append(t_)
for t_ in nerves: vis(t_, XR, recursive=False)
SG0, SG1 = S["signal"]
for m in nerve_ms:
    val_key(m, "count", 1, 2.0); val_key(m, "amp", 1, 0.0); val_key(m, "phase", 1, 0.0); val_key(m, "glow", 1, 0.6)
    val_key(m, "amp", F_BRAIN - 6, 0.0); val_key(m, "amp", F_BRAIN, 25.0); val_key(m, "phase", F_BRAIN - 6, 0.0)
    val_key(m, "count", F_PAIN, 4.0)
    val_key(m, "phase", SG1 + 1, (SG1 + 1 - F_BRAIN + 6) / 9.0)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        if "phase" in fc.data_path or 'nodes["phase"]' in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
val_key(xb_m, "glow", 1, 0.8); val_key(xb_m, "red", 1, 0.0)
val_key(xb_m, "glow", F_BRAIN + 8, 0.8)
for f in range(F_BRAIN + 10, SG1 + 1, 4):
    strong = f >= F_PAIN
    val_key(xb_m, "glow", f, 6.0 if strong else 3.0); val_key(xb_m, "glow", f + 2, 1.5)
val_key(xb_m, "red", F_PAIN - 1, 0.0); val_key(xb_m, "red", F_PAIN, 1.0)
for fc in mc._fcurves(xb_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
# "soxta signallar": miya ortida rang-barang uchqunlar
spark_ms = [mat(f"spark{i}", c, 0.5, emit=8.0) for i, c in enumerate(((1, 0.2, 0.15), (0.2, 1, 0.35), (0.3, 0.5, 1), (1, 0.85, 0.2), (0.9, 0.3, 1)))]
rs_ = random.Random(12)
sparks = empty("xsparks", (0, 0, 0), headE)
for k in range(40):
    p = (rs_.uniform(-0.05, 0.05), rs_.uniform(0.08, 0.15), rs_.uniform(-0.09, -0.03))
    o = sphere(f"xspark{k}", rs_.uniform(0.002, 0.004), p, rs_.choice(spark_ms), sub=1, parent=sparks)
    on = []
    f = F_FAKE + rs_.randint(-3, 3)
    while f < SG1:
        on += list(range(f, f + rs_.randint(2, 4))); f += rs_.randint(4, 9)
    frames_vis(o, on)

# ======================================================================
# 4) MAKRO KO'Z (real o'lcham): barmoq yopiq qovoqni bosadi
# ======================================================================
MAC = V(0.0, 30.0, 1.2)
eye = EY.build_eye("meye", tuple(MAC), states={"shut": (0.0, 0.32)})
LS = eye["shape"]; eroot = eye["root"]
bskin = mat("macro_skin", (0.56, 0.33, 0.25), 0.5, sss=0.3)
bskin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.002
mback = plane("macro_back", (0.5, 0.5), tuple(MAC + V(0, -0.0045, 0)), bskin, rot=(90, 0, 0))
def EL(p): return MAC + Vector(p)
PR0, PR1 = S["press"]
EY.set_key(eye, "shut", 1, 1.0)
eye["red"].outputs[0].default_value = 0.35; eye["red"].outputs[0].keyframe_insert("default_value", frame=1)
mskin = P.skin_material("mfinger_skin", base=(0.7, 0.44, 0.34))
fing = P.build_finger("mfinger", None, r=0.0085, length=0.08, skin=mskin)
def frame_dir(d, face=Vector((0, -1, 0))):
    Yl = d.normalized(); Zl = (face - Yl * face.dot(Yl)).normalized(); Xl = Yl.cross(Zl)
    return Matrix((Xl, Yl, Zl)).transposed().to_euler()
# barmoq tanasi kameradan o'ngga-tepaga, yostiqchasi qovoqqa qaraydi (-Z mahalliy = yostiqcha)
fing.rotation_euler = frame_dir(Vector((0.55, -0.55, 0.62)), Vector((0.2, -0.3, 1.0)))
LID_TOP = EL((0.0005, LS.depth(0.0, 0.004) - 0.0085, 0.0045))
for f, k in ((PR0, 0.0), (PR0 + 8, 0.35), (PR0 + 16, 1.0), (PR0 + 22, 0.7), (PR0 + 28, 1.0), (PR0 + 34, 0.75), (PR1 + 1, 1.0)):
    key(fing, f, loc=tuple(LID_TOP + V(0.0015 * math.sin(f * 0.4), -0.004 * (1 - k) + 0.0012 * k, 0.003 * (1 - k))))
    key(eroot, f, loc=tuple(MAC + V(0, 0.0016 * k, 0)))
    for o in (eye["lids"], eye["lash"]):
        o.scale = (1.0 + 0.03 * k, 1.0, 1.0 - 0.06 * k); o.keyframe_insert("scale", frame=f)
vis(eroot, MACR); vis(fing, MACR); vis(mback, MACR)

# ======================================================================
# 5) KESIM (cutaway): ko'zning 10x kattalashtirilgan yarim kesimi
#    mahalliy o'qlar (cutE ichida): old = -Y, tepa = +Z, kesim tekisligi x = 0 (kamera +X tomonda)
# ======================================================================
CUT = V(40.0, 0.0, 1.5)
Re = 0.12
cutE = empty("cutE", tuple(CUT))
cut_objs = [cutE]
def C_(o, par=True):
    if par and o.parent is None: o.parent = cutE
    return o
def CPl(th_deg, r, x=0.0):
    t = R(th_deg); return Vector((x, -r * math.cos(t), r * math.sin(t)))
def r_dome(s): return Re * (1 + 0.06 * math.cos(min(1.0, s / 0.5) * math.pi / 2) ** 2) if s < 0.5 else Re
# sklera (yarim shar, shox parda o'rni ochiq)
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=96, radius=Re, rotation=(R(90), 0, 0), location=(0, 0, 0))
ball = bpy.context.object; ball.name = "cut_ball"; bpy.ops.object.transform_apply(rotation=True)
bm = bmesh.new(); bm.from_mesh(ball.data)
dl = [v for v in bm.verts if v.co.x > 0.0005 or (v.co.normalized().y < 0 and math.hypot(v.co.normalized().x, v.co.normalized().z) < 0.47)]
bmesh.ops.delete(bm, geom=dl, context="VERTS"); bm.to_mesh(ball.data); bm.free()
for p in ball.data.polygons: p.use_smooth = True
so = ball.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.011; so.offset = -1.0
sclera_m = mat("cut_sclera", (0.93, 0.9, 0.86), 0.3, coat=0.5, sss=0.2)
sclera_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.004
# qon tomirlari
N = sclera_m.node_tree.nodes; L = sclera_m.node_tree.links; _b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 14.0; wv.inputs["Distortion"].default_value = 12.0
wv.inputs["Detail"].default_value = 6.0; L.new(tc.outputs["Object"], wv.inputs["Vector"])
vein = P.math_n(N, L, "GREATER_THAN", wv.outputs["Fac"], 0.93)
vc = N.new("ShaderNodeMix"); vc.data_type = "RGBA"; L.new(vein, vc.inputs["Factor"])
vc.inputs[6].default_value = (0.93, 0.9, 0.86, 1); vc.inputs[7].default_value = (0.7, 0.08, 0.06, 1); L.new(vc.outputs[2], _b.inputs["Base Color"])
ball.data.materials.append(sclera_m); C_(ball)
# shox parda (alohida): "cone" shape key = keratokonus (pastroqqa siljigan konus), qalinlik = Solidify (yupqalashadi)
bpy.ops.mesh.primitive_uv_sphere_add(segments=160, ring_count=120, radius=Re, rotation=(R(90), 0, 0), location=(0, 0, 0))
corn = bpy.context.object; corn.name = "cut_cornea"; bpy.ops.object.transform_apply(rotation=True)
bm = bmesh.new(); bm.from_mesh(corn.data)
dl = [v for v in bm.verts if v.co.x > 0.0005 or not (v.co.normalized().y < 0 and math.hypot(v.co.normalized().x, v.co.normalized().z) < 0.52)]
bmesh.ops.delete(bm, geom=dl, context="VERTS"); bm.to_mesh(corn.data); bm.free()
APEX = Vector((0, -1, -0.22)).normalized()
base_co = []; cone_co = []
for v in corn.data.vertices:
    d = v.co.normalized(); s = math.hypot(d.x, d.z)
    b0 = d * r_dome(s); base_co.append(b0)
    a = d.angle(APEX); edge = max(0.0, 1 - (s / 0.52) ** 2)
    k = max(0.0, 1 - a / 0.62) ** 1.25 * edge
    cone_co.append(b0 + d * Re * 0.42 * k)
    v.co = b0
for p in corn.data.polygons: p.use_smooth = True
corn.shape_key_add(name="Basis")
kc = corn.shape_key_add(name="cone", from_mix=False); kc.value = 0.0
for i, c in enumerate(cone_co): kc.data[i].co = c
cso = corn.modifiers.new("solid", "SOLIDIFY"); cso.thickness = 0.011; cso.offset = -1.0
corn_m = bpy.data.materials.new("cut_cornea_m"); corn_m.use_nodes = True
N = corn_m.node_tree.nodes; L = corn_m.node_tree.links; _b = N["Principled BSDF"]
_b.inputs["Base Color"].default_value = (0.75, 0.9, 1.0, 1); _b.inputs["Roughness"].default_value = 0.05
_b.inputs["Transmission Weight"].default_value = 0.4; _b.inputs["IOR"].default_value = 1.376; _b.inputs["Coat Weight"].default_value = 1.0
_b.inputs["Emission Color"].default_value = (0.3, 0.75, 1.0, 1)
cglow = value_node(corn_m, "glow", 0.3); crack = value_node(corn_m, "crack", 0.0)
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 26.0
L.new(tc.outputs["Object"], vo.inputs["Vector"])
sxo = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sxo.inputs[0])
apexm = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", sxo.outputs["Y"], -1.0), 0.115), 30.0, clamp=True)
crk = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", vo.outputs["Distance"], 0.007), crack), apexm)
L.new(P.math_n(N, L, "ADD", cglow, P.math_n(N, L, "MULTIPLY", crk, 25.0)), _b.inputs["Emission Strength"])
ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; L.new(crk, ec.inputs["Factor"])
ec.inputs[6].default_value = (0.3, 0.75, 1.0, 1); ec.inputs[7].default_value = (1.0, 0.08, 0.03, 1); L.new(ec.outputs[2], _b.inputs["Emission Color"])
corn.data.materials.append(corn_m); C_(corn)
# kesim yuzasi: halqalar (sklera, tomirli qavat, to'r parda, shishasimon tana)
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=Re - 0.0005, fill_type="NGON", location=(-0.0004, 0, 0), rotation=(0, R(90), 0))
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
# to'r parda ezilganda qizil yonadi (orqa yarmi)
ret = value_node(disc_m, "ret", 0.0)
ring = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "GREATER_THAN", rr_, 0.80), P.math_n(N, L, "LESS_THAN", rr_, 0.87))
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", ring, ret), 6.0), _b.inputs["Emission Strength"])
_b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.05, 1)
disc.data.materials.append(disc_m); C_(disc)
lens_m = mat("cut_lens", (0.95, 0.85, 0.55), 0.08, coat=1.0, sss=0.2)
C_(sphere("cut_lens", 0.05, (-0.002, -0.072, 0), lens_m, scale=(0.12, 0.42, 0.95), sub=4))
iris_m = mat("cut_iris", (0.15, 0.3, 0.38), 0.4)
for sgn in (1, -1): C_(box(f"cut_iris{sgn}", (0.006, 0.006, 0.042), (-0.002, -0.094, sgn * 0.073), iris_m, bevel=0.002))
# ko'rish nervi (ko'z ortidan), impulslar poyezdi
cn_m = train_mat("cut_nerve_m", col=(0.92, 0.8, 0.55), pcol=(1.0, 0.55, 0.2))
cnerve = C_(P.tube("cut_nerve", [(0.0, Re * 0.9, -0.012), (0.0, Re + 0.05, -0.02), (0.0, Re + 0.16, -0.015), (0.0, Re + 0.4, 0.02)], 0.019, cn_m, cutE,
                   taper=[1.0, 1.0, 1.0, 1.0]))
RE0, RE1 = S["retina"]
val_key(cn_m, "count", 1, 3.0); val_key(cn_m, "amp", 1, 0.0); val_key(cn_m, "glow", 1, 0.3); val_key(cn_m, "phase", 1, 0.0)
val_key(cn_m, "amp", RE0 + 8, 0.0); val_key(cn_m, "amp", RE0 + 12, 25.0); val_key(cn_m, "phase", RE0 + 8, 0.0); val_key(cn_m, "phase", RE1 + 1, -4.0)
for fc in mc._fcurves(cn_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# to'r parda uchqunlari (ezilgan joyda)
rsp = random.Random(21)
rsparks = empty("rsparks", (0, 0, 0), cutE)
for k in range(46):
    th = rsp.uniform(110, 250); r_ = Re * rsp.uniform(0.8, 0.865)
    p = CPl(th, r_, 0.003)
    o = sphere(f"rspark{k}", rsp.uniform(0.0025, 0.005), tuple(p), rsp.choice(spark_ms), sub=1, parent=rsparks)
    on = []; f = RE0 + rsp.randint(0, 10)
    while f < RE1:
        on += list(range(f, f + rsp.randint(2, 4))); f += rsp.randint(5, 12)
    frames_vis(o, on)
val_key(disc_m, "ret", 1, 0.0); val_key(disc_m, "ret", RE0, 0.6)
for f in range(RE0, RE1, 6): val_key(disc_m, "ret", f, 1.0); val_key(disc_m, "ret", f + 3, 0.4)
val_key(disc_m, "ret", RE1 + 1, 0.0)
for fc in mc._fcurves(disc_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
# bosuvchi barmoq (10x) — "deform" kadri
cfskin = P.skin_material("cfinger_skin", base=(0.7, 0.44, 0.34))
cfing = P.build_finger("cfinger", None, r=0.07, length=0.5, skin=cfskin)      # cutE ga bog'lanmaydi (ezilish masshtabi tegmasin)
cfing.rotation_euler = frame_dir(Vector((0.0, -1.0, 0.18)), Vector((0.0, 0.0, 1.0)))
DF0, DF1 = S["deform"]
FRONT = -Re * 1.06
for f, k in ((1, 0.0), (DF0, 0.0), (DF0 + 6, 0.3), (DF0 + 14, 0.85), (DF0 + 22, 0.7), (DF0 + 30, 1.0), (DF1 + 1, 1.0)):
    sy = 1 - 0.24 * k
    cutE.scale = (1.0, sy, 1 + 0.11 * k); cutE.keyframe_insert("scale", frame=f)
    key(cfing, f, loc=tuple(CUT + V(0.0, FRONT * sy - 0.002 - 0.06 * (1 - min(1, k * 3)), -0.005)))
cutE.scale = (1, 1, 1); cutE.keyframe_insert("scale", frame=DF1 + 1)
vis(cfing, [S["deform"]])
# yupqalashish, bo'rtish, konus, yorilish
TH0, TH1 = S["thin"]; BU0, BU1 = S["bulge"]; CO0, CO1 = S["cone"]; RU0, RU1 = S["rupture"]
def cso_t(f, v): cso.thickness = v; cso.keyframe_insert("thickness", frame=f)
cso_t(1, 0.011); cso_t(TH0 + 10, 0.011); cso_t(TH1 - 6, 0.0038)
def cone_k(f, v): kc.value = v; kc.keyframe_insert("value", frame=f)
cone_k(1, 0.0); cone_k(BU0 + 2, 0.0); cone_k(BU1, 0.55); cone_k(CO0 + 4, 0.62); cone_k(CO1, 1.0)
cone_k(RU0, 1.0); cone_k(F_CRACK, 1.02); cone_k(F_CRACK + 8, 0.84); cone_k(RU1, 0.8)
val_key(corn_m, "glow", 1, 0.25); val_key(corn_m, "glow", TH0 + 4, 0.25); val_key(corn_m, "glow", TH0 + 16, 2.2); val_key(corn_m, "glow", CO1, 1.6)
val_key(corn_m, "glow", RU0, 1.4)
val_key(corn_m, "crack", 1, 0.0); val_key(corn_m, "crack", F_CRACK - 3, 0.0); val_key(corn_m, "crack", F_CRACK, 0.35); val_key(corn_m, "crack", F_CRACK + 6, 1.0)
# sog'lom gumbazning sharpa chizig'i (konus kadrida)
ghost_m = mat("dome_ghost", (0.4, 1.0, 0.5), 0.5, emit=4.0)
gpts = [tuple(CPl(th, r_dome(abs(math.sin(R(th)))) + 0.001, 0.004)) for th in range(-32, 33, 4)]
gline = C_(P.tube("dome_ghost", gpts, 0.0022, ghost_m, cutE))
vis(gline, [S["cone"]])
# yorilishda suyuqlik otilib chiqadi
fluid_m = mat("aqueous", (0.6, 0.85, 1.0), 0.02, trans=0.9, coat=1.0, emit=0.4, emit_col=(0.4, 0.75, 1.0))
fl = empty("fluid", (0, 0, 0), cutE)
rf = random.Random(17)
A_P = APEX * (Re * 1.06 + Re * 0.42 * 0.95)
for k in range(28):
    o = sphere(f"fl{k}", rf.uniform(0.004, 0.009), tuple(A_P), fluid_m, sub=2, parent=fl)
    v_ = (APEX + Vector((rf.uniform(0.2, 0.9), rf.uniform(-0.3, 0.3), rf.uniform(-0.4, 0.5)))).normalized() * rf.uniform(0.0025, 0.006)
    f0 = F_CRACK + rf.randint(0, 6)
    key(o, 1, loc=tuple(A_P), scale=0.001); key(o, f0, loc=tuple(A_P), scale=0.001)
    for j in range(1, 14):
        p = A_P + v_ * j + Vector((0, 0, -0.0003 * j * j)); key(o, f0 + j, loc=tuple(p), scale=1.0)
    interp(o, "LINEAR", "location")
vis(fl, [S["rupture"]])
for o in cut_objs: vis(o, CUTR)

# ======================================================================
# 6) POV: yopiq ko'z ichi — fosfenlar (chaqnashlar, naqshlar, rangli nuqtalar)
# ======================================================================
POVP = V(0.0, -40.0, 1.5)
pov_m = bpy.data.materials.new("pov"); pov_m.use_nodes = True
N = pov_m.node_tree.nodes; L = pov_m.node_tree.links; N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord")
T_ = value_node(pov_m, "t", 0.0); FL_ = value_node(pov_m, "flash", 0.0); PA_ = value_node(pov_m, "pat", 0.0); DO_ = value_node(pov_m, "dots", 0.0)
def n4(scale, detail=4.0, dist=0.0, wmul=1.0):
    n = N.new("ShaderNodeTexNoise"); n.noise_dimensions = "4D"; n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    n.inputs["Distortion"].default_value = dist; L.new(tc.outputs["Object"], n.inputs["Vector"]); L.new(P.math_n(N, L, "MULTIPLY", T_, wmul), n.inputs["W"]); return n
base = n4(2.0, 3.0, 0.5, 0.3)
basec = N.new("ShaderNodeMix"); basec.data_type = "RGBA"; L.new(base.outputs["Fac"], basec.inputs["Factor"])
basec.inputs[6].default_value = (0.04, 0.003, 0.002, 1); basec.inputs[7].default_value = (0.22, 0.02, 0.01, 1)
fl_n = n4(1.4, 2.0, 1.5, 1.6)
flash = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", fl_n.outputs["Fac"], 7.0), P.math_n(N, L, "MULTIPLY", FL_, 60.0))
# radial naqsh (halqalar + spiral)
sxp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sxp.inputs[0])
rad = P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sxp.outputs["X"], sxp.outputs["X"]), P.math_n(N, L, "MULTIPLY", sxp.outputs["Y"], sxp.outputs["Y"])))
ang = P.math_n(N, L, "ARCTAN2", sxp.outputs["Y"], sxp.outputs["X"])
spir = P.math_n(N, L, "SINE", P.math_n(N, L, "ADD", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", rad, 40.0), P.math_n(N, L, "MULTIPLY", T_, 6.0)), P.math_n(N, L, "MULTIPLY", ang, 6.0)))
pat = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", spir, 1.0), 0.5), 6.0), PA_)
hue = N.new("ShaderNodeCombineColor"); hue.mode = "HSV"
L.new(P.math_n(N, L, "FRACT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", rad, 3.0), P.math_n(N, L, "MULTIPLY", T_, 0.15))), hue.inputs[0])
hue.inputs[1].default_value = 0.85; hue.inputs[2].default_value = 1.0
vor = N.new("ShaderNodeTexVoronoi"); vor.voronoi_dimensions = "4D"; vor.inputs["Scale"].default_value = 9.0
L.new(tc.outputs["Object"], vor.inputs["Vector"]); L.new(P.math_n(N, L, "MULTIPLY", T_, 0.4), vor.inputs["W"])
dot = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", vor.outputs["Distance"], 0.11), DO_)
e1 = N.new("ShaderNodeEmission"); L.new(basec.outputs[2], e1.inputs["Color"]); e1.inputs["Strength"].default_value = 1.0
e2 = N.new("ShaderNodeEmission"); e2.inputs["Color"].default_value = (1.0, 0.92, 0.7, 1); L.new(flash, e2.inputs["Strength"])
e3 = N.new("ShaderNodeEmission"); L.new(hue.outputs[0], e3.inputs["Color"]); L.new(P.math_n(N, L, "MULTIPLY", pat, 4.0), e3.inputs["Strength"])
e4 = N.new("ShaderNodeEmission"); L.new(vor.outputs["Color"], e4.inputs["Color"]); L.new(P.math_n(N, L, "MULTIPLY", dot, 6.0), e4.inputs["Strength"])
a1 = N.new("ShaderNodeAddShader"); L.new(e1.outputs[0], a1.inputs[0]); L.new(e2.outputs[0], a1.inputs[1])
a2 = N.new("ShaderNodeAddShader"); L.new(a1.outputs[0], a2.inputs[0]); L.new(e3.outputs[0], a2.inputs[1])
a3 = N.new("ShaderNodeAddShader"); L.new(a2.outputs[0], a3.inputs[0]); L.new(e4.outputs[0], a3.inputs[1])
L.new(a3.outputs[0], N["Material Output"].inputs["Surface"])
povpl = plane("pov_plane", (2.0, 2.0), tuple(POVP), pov_m, rot=(90, 0, 0))
FL0, FL1 = S["flash"]
val_key(pov_m, "t", 1, 0.0); val_key(pov_m, "t", FL0, 0.0); val_key(pov_m, "t", FL1 + 1, 9.0)
for fc in mc._fcurves(pov_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
for f, fv, pv, dv in ((FL0, 0.0, 0.0, 0.0), (FL0 + 6, 0.8, 0.0, 0.0), (FL0 + 9, 0.1, 0.0, 0.0), (FL0 + 16, 1.0, 0.2, 0.0),
                       (FL0 + 22, 0.2, 0.5, 0.0), (FL0 + 34, 0.6, 1.0, 0.2), (FL0 + 46, 1.0, 0.8, 0.4), (657, 1.6, 1.0, 0.6),
                       (662, 0.4, 1.0, 0.8), (668, 1.8, 0.7, 1.0), (674, 0.5, 0.6, 1.0), (680, 1.4, 0.5, 1.0), (FL1, 0.6, 0.4, 1.0)):
    val_key(pov_m, "flash", f, fv); val_key(pov_m, "pat", f, pv); val_key(pov_m, "dots", f, dv)
vis(povpl, POVR)

# ======================================================================
# 7) XONADA SUZUVCHI RANGLI NUQTALAR ("dots" kadri)
# ======================================================================
DO0, DO1 = S["dots"]
fdots = empty("fdots", tuple(FACE["dots"]))
rd = random.Random(5)
dot_ms = [mat(f"fdot{i}", c, 0.5, emit=6.0) for i, c in enumerate(((1, 0.25, 0.2), (0.25, 1, 0.4), (0.3, 0.55, 1), (1, 0.9, 0.25), (0.95, 0.35, 1), (0.2, 1, 1)))]
for k in range(60):
    p0 = Vector((rd.uniform(-0.22, 0.22), rd.uniform(-0.38, -0.05), rd.uniform(-0.16, 0.2)))
    o = sphere(f"fdot{k}", rd.uniform(0.003, 0.009), tuple(p0), rd.choice(dot_ms), sub=2, parent=fdots)
    d_ = Vector((rd.uniform(-1, 1), rd.uniform(-1, 1), rd.uniform(-0.5, 1))).normalized() * rd.uniform(0.03, 0.08)
    key(o, DO0, loc=tuple(p0), scale=0.2); key(o, DO0 + rd.randint(4, 14), scale=1.0); key(o, DO1 + 1, loc=tuple(p0 + d_))
vis(fdots, [S["dots"]])

# ======================================================================
# 8) OPERATSIYA XONASI
# ======================================================================
or_objs = []
def O_(o): or_objs.append(o); return o
tile_m = mat("or_tile", (0.55, 0.72, 0.7), 0.35, coat=0.3)
tn = tile_m.node_tree.nodes; tl = tile_m.node_tree.links
_br = tn.new("ShaderNodeTexBrick"); _br.inputs["Scale"].default_value = 6.0; _br.inputs["Mortar Size"].default_value = 0.012
_br.inputs["Color1"].default_value = (0.55, 0.72, 0.7, 1); _br.inputs["Color2"].default_value = (0.5, 0.68, 0.66, 1); _br.inputs["Mortar"].default_value = (0.85, 0.88, 0.86, 1)
_br.offset = 0.0; _tc = tn.new("ShaderNodeTexCoord"); tl.new(_tc.outputs["Object"], _br.inputs["Vector"]); tl.new(_br.outputs["Color"], tn["Principled BSDF"].inputs["Base Color"])
O_(plane("or_floor", (8, 8), tuple(ORP), mat("or_floor_m", (0.3, 0.36, 0.36), 0.3, coat=0.4)))
for nm, sz, off in (("or_wN", (8, 0.1, 3.2), (0, 3.5, 1.6)), ("or_wS", (8, 0.1, 3.2), (0, -3.5, 1.6)),
                    ("or_wE", (0.1, 8, 3.2), (3.5, 0, 1.6)), ("or_wW", (0.1, 8, 3.2), (-3.5, 0, 1.6))):
    O_(box(nm, sz, tuple(ORP + V(*off)), tile_m))
O_(box("or_ceil", (8, 8, 0.05), tuple(ORP + V(0, 0, 3.2)), mat("or_ceil_m", (0.9, 0.92, 0.92), 0.6)))
for x in (-1.2, 1.2):
    O_(box(f"or_panel{x}", (0.8, 0.8, 0.02), tuple(ORP + V(x, 0.0, 3.17)), mat(f"or_panel_m{x}", (1, 1, 1), 0.5, emit=6.0)))
steel = mat("steel", (0.75, 0.76, 0.78), 0.25, metal=1.0)
TOP = 0.88
O_(box("or_table", (0.62, 2.0, 0.08), tuple(ORP + V(0, 0.0, TOP - 0.04)), mat("or_pad", (0.08, 0.1, 0.12), 0.5), bevel=0.02))
O_(cyl("or_post", 0.09, TOP - 0.1, tuple(ORP + V(0, 0, (TOP - 0.1) / 2)), steel))
O_(box("or_base", (0.5, 0.8, 0.06), tuple(ORP + V(0, 0, 0.03)), steel, bevel=0.01))
drape_m = mat("drape", (0.12, 0.42, 0.42), 0.85, sss=0.05)
dr = O_(box("or_drape", (0.72, 1.35, 0.34), tuple(ORP + V(0, -0.38, TOP + 0.13)), drape_m, bevel=0.06))
dd = dr.modifiers.new("d", "DISPLACE"); _t = bpy.data.textures.new("drape_t", "CLOUDS"); _t.noise_scale = 0.25; dd.texture = _t; dd.strength = 0.02
# jarrohlik lampasi
LAMP = ORP + V(0.55, 0.85, 1.95)
lampg = O_(empty("or_lamp", tuple(LAMP))); lampg.rotation_euler = (R(-12), R(10), 0)
cyl("or_lamp_shell", 0.36, 0.1, (0, 0, 0.05), mat("or_lamp_shell_m", (0.88, 0.9, 0.9), 0.3), parent=lampg, verts=64)
bulb_m = mat("or_bulb", (1.0, 0.98, 0.95), 0.2, emit=30.0)
for i in range(7):
    a = 2 * math.pi * i / 7 if i else 0; rr = 0.0 if i == 0 else 0.2
    cyl(f"or_bulb{i}", 0.075, 0.02, (rr * math.cos(a), rr * math.sin(a), -0.005), bulb_m, parent=lampg, verts=32)
cyl("or_lamp_arm", 0.03, 1.2, (0, 0, 0.65), steel, parent=lampg)
# monitor (yurak urishi chizig'i)
mon = O_(empty("or_mon", tuple(ORP + V(0.9, 0.9, 1.4)))); mon.rotation_euler = (0, 0, R(-130))
box("or_mon_box", (0.5, 0.06, 0.36), (0, 0, 0), mat("or_mon_m", (0.05, 0.05, 0.06), 0.4), parent=mon, bevel=0.01)
ecg_m = mat("ecg", (0.2, 1.0, 0.4), 0.5, emit=6.0)
ecg_pts = []
for i in range(40):
    x = -0.2 + 0.4 * i / 39; ph = (i % 13)
    z = {5: 0.04, 6: -0.03, 7: 0.09, 8: -0.05}.get(ph, 0.0)
    ecg_pts.append((x, -0.035, z))
P.tube("or_ecg", ecg_pts, 0.002, ecg_m, mon)
cyl("or_mon_pole", 0.02, 1.2, (0, 0.05, -0.75), steel, parent=mon)
# asboblar laganchasi
tray = O_(empty("or_tray", tuple(ORP + V(-0.62, 0.2, 1.0))))
box("or_tray_b", (0.45, 0.32, 0.02), (0, 0, 0), steel, parent=tray, bevel=0.005)
for i in range(5):
    cyl(f"or_tool{i}", 0.004, 0.16, (-0.15 + 0.07 * i, 0, 0.02), steel, rot=(90, 0, 10 * i), parent=tray)
cyl("or_tray_pole", 0.015, 1.0, (0, 0, -0.5), steel, parent=tray)
O_(box("or_head_rest", (0.28, 0.25, 0.06), tuple(ORP + V(0, 0.6, TOP + 0.03)), mat("or_rest_m", (0.1, 0.12, 0.14), 0.5), bevel=0.02))
for o in or_objs: vis(o, ORR)

for o in room_objs: vis(o, ROOM)

# ======================================================================
# 9) KAMERALAR
# ======================================================================
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
def head_w(f):
    sc.frame_set(f); bpy.context.view_layer.update(); return headE.matrix_world.translation.copy()
# 1 ILGAK: poldan, keng ob'ektiv, tez push-in
H0, H1 = S["hook"]; FP = FACE["hook"]
c = abs_cam("hook", [(H0, FP + V(0.62, -0.68, -0.36)), (H1, FP + V(0.3, -0.46, -0.2))],
            [(H0, FP + V(0, -0.02, -0.08)), (H1, FP + V(0, 0.0, -0.02))], 16, 2.8)
lens_keys(c, [(H0, 15), (H1, 19)])
# 2 ishqalash: yuzga yaqin, yondan ergashish
RB0, RB1 = S["rub"]
c = rel_cam("rub", faceT, 42, 2.0, [(RB0, V(0.3, -0.32, -0.02)), (RB1, V(0.2, -0.33, 0.01))])
# 3 rentgenga o'tish: aylanma
XI0, XI1 = S["xin"]; FX = FACE["xin"]
c = abs_cam("xin", [(XI0, FX + V(0.55, -0.62, -0.05)), (XI0 + 24, FX + V(0.15, -0.68, -0.02)), (XI1, FX + V(-0.25, -0.55, 0.02))],
            [(XI0, FX + V(0, 0, -0.12)), (XI1, FX + V(0, 0, -0.06))], 30, 4.0)
# 4 dahshat: crash zoom
HO0, HO1 = S["horror"]
c = rel_cam("horror", faceT, 24, 4.0, [(HO0, V(0.05, -0.6, 0.06)), (F_HORROR - 1, V(0.04, -0.42, 0.04)), (F_HORROR + 2, V(0.03, -0.26, 0.02)), (HO1, V(0.06, -0.24, 0.02))])
lens_keys(c, [(HO0, 22), (F_HORROR - 1, 26), (F_HORROR + 2, 42), (HO1, 46)]); shake(c, F_HORROR, F_HORROR + 12, 0.012, seed=3)
# 5 makro bosish
PR0, PR1 = S["press"]
c = abs_cam("press", [(PR0, EL((0.045, -0.105, -0.02))), (PR1, EL((0.03, -0.085, -0.012)))],
            [(PR0, EL((0.004, -0.012, 0.002))), (PR1, EL((0.003, -0.01, 0.003)))], 38, 14.0)
# 6 bosh suyagi, yondan
SK0, SK1 = S["skull"]; FS_ = FACE["skull"]
c = abs_cam("skull", [(SK0, FS_ + V(0.55, -0.32, 0.06)), (SK1, FS_ + V(0.58, -0.05, 0.04))],
            [(SK0, FS_ + V(0.02, 0.03, 0.0)), (SK1, FS_ + V(0.02, 0.05, 0.0))], 38, 5.6)
# 7 kesim: ezilish, crash zoom
DF0, DF1 = S["deform"]; CF = CUT + V(0, -0.06, 0)
c = abs_cam("deform", [(DF0, CF + V(0.95, -0.18, 0.1)), (DF0 + 8, CF + V(0.55, -0.12, 0.05)), (DF1, CF + V(0.5, -0.1, 0.03))],
            [(DF0, CF), (DF1, CF + V(0, -0.02, 0))], 28, 8.0)
lens_keys(c, [(DF0, 24), (DF0 + 8, 32), (DF1, 34)]); shake(c, DF0 + 12, DF0 + 32, 0.01, seed=7, decay=False)
# 8 qattiqroq: past burchak, qo'l kamerasi
HA0, HA1 = S["harder"]; FH = FACE["harder"]
c = abs_cam("harder", [(HA0, FH + V(0.42, -0.42, -0.6)), (HA1, FH + V(0.3, -0.34, -0.45))], [(HA0, FH + V(0, -0.04, -0.02))], 17, 2.8)
shake(c, HA0, HA1, 0.012, seed=8, decay=False)
# 9 yupqalashish: aylanma
CORF = CUT + V(0, -Re * 1.06, -0.01)
c = abs_cam("thin", [(TH0, CORF + V(0.3, -0.16, 0.1)), (TH1, CORF + V(0.27, -0.2, -0.07))], [(TH0, CORF + V(0, 0.02, 0)), (TH1, CORF + V(0, 0.01, 0))], 38, 8.0)
# 10 bo'rtish: profil, crash zoom
c = abs_cam("bulge", [(BU0, CORF + V(0.9, -0.05, 0.0)), (BU0 + 6, CORF + V(0.48, -0.08, -0.01)), (BU1, CORF + V(0.44, -0.1, -0.02))],
            [(BU0, CORF + V(0, -0.02, -0.01)), (BU1, CORF + V(0, -0.04, -0.02))], 32, 8.0)
lens_keys(c, [(BU0, 26), (BU0 + 6, 40), (BU1, 42)]); shake(c, BU0 + 5, BU0 + 14, 0.008, seed=10)
# 11 konus: aylanma
APW = CUT + A_P
c = abs_cam("cone", [(CO0, APW + V(0.46, -0.3, 0.14)), (CO1, APW + V(0.5, -0.06, -0.12))], [(CO0, APW + V(0, 0.05, 0)), (CO1, APW + V(0, 0.06, 0.01))], 36, 8.0)
# 12 POV: aylanuvchi va yaqinlashuvchi
c = shot_cam("flash", tuple(POVP + V(0, -0.55, 0)), None, 30)
for f, rz, y in ((FL0, 0, -0.55), (FL1, 35, -0.38)):
    c.rotation_euler = (R(90), R(rz), 0); c.keyframe_insert("rotation_euler", frame=f)
    c.location = tuple(POVP + V(0, y, 0)); c.keyframe_insert("location", frame=f)
for f in (657, 668, 680): shake(c, f, f + 5, 0.01, seed=f)
# 13 rangli nuqtalar: yuzga sekin push-in, nuqtalar oldingi planda xira
c = rel_cam("dots", faceT, 34, 1.8, [(DO0, V(0.16, -0.5, 0.02)), (DO1, V(0.1, -0.36, 0.0))])
# 14 to'r parda: orqa devor bo'ylab
c = abs_cam("retina", [(RE0, CUT + V(0.38, 0.0, 0.14)), (RE1, CUT + V(0.34, 0.12, -0.04))], [(RE0, CUT + V(0, 0.07, 0.02)), (RE1, CUT + V(0, 0.12, -0.01))], 34, 8.0)
# 15 signallar: rentgen bosh, yondan-orqaga yonlama siljish
FG = FACE["signal"]
c = abs_cam("signal", [(SG0, FG + V(0.55, -0.3, 0.18)), (SG1, FG + V(0.5, 0.35, 0.2))], [(SG0, FG + V(0, 0.1, 0.05)), (SG1, FG + V(0, 0.12, 0.05))], 30, 5.6)
# 16 odat: sekin push-in
HB0, HB1 = S["habit"]
c = rel_cam("habit", faceT, 30, 2.4, [(HB0, V(0.62, -0.5, -0.12)), (HB1, V(0.36, -0.32, -0.06))])
# 17 yorilish: crash zoom
c = abs_cam("rupture", [(RU0, APW + V(0.85, -0.25, 0.05)), (F_CRACK - 1, APW + V(0.62, -0.2, 0.03)), (F_CRACK + 2, APW + V(0.45, -0.18, 0.02)), (RU1, APW + V(0.42, -0.2, 0.01))],
            [(RU0, APW + V(0, 0.07, 0)), (RU1, APW + V(0, 0.05, -0.01))], 30, 8.0)
lens_keys(c, [(RU0, 26), (F_CRACK - 1, 30), (F_CRACK + 2, 44), (RU1, 46)]); shake(c, F_CRACK, F_CRACK + 12, 0.012, seed=17)
# 18 operatsiya: tepadan aylanib tushish
FO = FACE["surgery"]
c = abs_cam("surgery", [(SU0, FO + V(0.15, -0.55, 1.45)), (SU0 + 45, FO + V(0.12, -0.3, 0.9)), (SU1, FO + V(0.06, -0.14, 0.5))],
            [(SU0, FO + V(0, -0.25, 0)), (SU1, FO + V(0, -0.02, 0))], 20, 4.0)
lens_keys(c, [(SU0, 18), (SU1, 26)])
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
# 10) YORUG'LIK VA FON
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
WORLD = {"room": (0.035, (0.004, 0.008, 0.02), 1.0), "xr": (0.0, (0.004, 0.01, 0.028), 1.0), "mac": (0.0, (0.0, 0.0, 0.0), 0.0),
         "cut": (0.0, (0.012, 0.018, 0.035), 1.0), "pov": (0.0, (0, 0, 0), 0.0), "or": (0.25, (0.3, 0.38, 0.38), 0.3)}
def world_of(n):
    return "room" if n in ROOMN else "xr" if n in XRN else "mac" if n in MACN else "cut" if n in CUTN else "pov" if n in POVN else "or"
for f, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
def lit(ranges, e, off=None):
    ks = lights_for(ranges, e)
    if off:
        a, b = off; ks = sorted(ks + [(a, e * 0.02)])
    return ks
DOTS_OFF = (F_OFF + 1, S["dots"][1])
# xona (kechqurun): stol lampasi, noutbuk, shift, oy nuri
area("lamp_key", (1.2, -1.35, 1.3), 0.25, (1.0, 0.68, 0.38), lit(ROOM, 60.0, DOTS_OFF), target=FT)
area("lap_glow", tuple(LAP + V(0, -0.05, 0.25)), 0.3, (0.6, 0.75, 1.0), lit(ROOM, 9.0, DOTS_OFF), target=FT)
area("ceil_fill", (0.0, 0.6, 2.6), 2.0, (1.0, 0.85, 0.7), lit(ROOM, 18.0, DOTS_OFF), target=empty("cfT", (0, 0.6, 0)))
area("moon_rim", (0.6, Y0 + 0.3, 2.0), 1.4, (0.55, 0.7, 1.0), lights_for(ROOM, 45.0), target=FT)
area("face_fill", (1.35, -1.05, 1.45), 0.5, (1.0, 0.9, 0.82), lit(rng("rub", "harder", "habit", "dots"), 14.0, DOTS_OFF), target=FT)
point("dots_glow", tuple(FACE["dots"] + V(0, -0.2, 0)), 0.1, (0.8, 0.6, 1.0), lights_for([S["dots"]], 0.0) + [(F_OFF + 1, 3.0), (S["dots"][1] + 1, 0.0)])
lamp_bulb = point("lamp_bulb", (1.22, -1.38, 1.18), 0.02, (1.0, 0.7, 0.4), lit(ROOM, 6.0, DOTS_OFF))
# rentgen
HT = empty("xrT"); clh = HT.constraints.new("COPY_LOCATION"); clh.target = headE
area("X_key", tuple(MEG + V(1.2, -1.2, 2.0)), 1.0, (0.8, 0.9, 1.0), lights_for(XR, 25.0), target=HT)
area("X_rim", tuple(MEG + V(-1.0, 0.8, 1.8)), 1.0, (0.3, 0.55, 1.0), lights_for(XR, 30.0), target=HT)
# makro
MT = empty("macroT", tuple(EL((0, -0.012, 0))))
area("M_key", tuple(EL((-0.12, -0.2, 0.16))), 0.18, (1.0, 0.95, 0.9), lights_for(MACR, 5.0), target=MT)
area("M_fill", tuple(EL((0.16, -0.18, -0.06))), 0.2, (0.9, 0.93, 1.0), lights_for(MACR, 2.0), target=MT)
area("M_top", tuple(EL((0.02, -0.1, 0.2))), 0.1, (1.0, 0.97, 0.92), lights_for(MACR, 2.5), target=MT)
# kesim
CT_ = empty("cutT", tuple(CUT + V(0, -0.06, 0)))
area("C_key", tuple(CUT + V(0.6, -0.45, 0.45)), 0.7, (1.0, 0.95, 0.9), lights_for(CUTR, 45.0), target=CT_)
area("C_fill", tuple(CUT + V(0.5, 0.25, -0.35)), 0.6, (1.0, 0.85, 0.7), lights_for(CUTR, 15.0), target=CT_)
area("C_rim", tuple(CUT + V(-0.25, -0.55, 0.35)), 0.5, (0.35, 0.6, 1.0), lights_for(CUTR, 25.0), target=CT_)
# operatsiya
OT = empty("orT", tuple(FO))
area("OR_lamp", tuple(LAMP + V(0, 0, -0.05)), 0.6, (0.95, 0.98, 1.0), lights_for(ORR, 260.0), target=OT)
area("OR_fill", tuple(ORP + V(1.6, -1.2, 2.4)), 1.5, (0.8, 0.95, 0.95), lights_for(ORR, 120.0), target=OT)
area("OR_rim", tuple(ORP + V(-1.5, 1.5, 2.2)), 1.2, (0.6, 0.85, 1.0), lights_for(ORR, 80.0), target=OT)

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
