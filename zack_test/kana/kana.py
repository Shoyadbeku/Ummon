# Yuzdagi kanalar (Demodex) — Zack D. Films uslubida 40 s video (960 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, zack_test/ishqalash/ishqalash.py (xona, yordamchilar, kamera), zack_test/yelim/eye.py (makro ko'z),
# zack_test/kana/mite.py (kana, mikro teri, kesim modellari).
# Assetlar: zack_test/tools/get_kana.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/kana/kana.py --render
# Sinov:  FRAMES=20,60,100,140,300 PCT=35 OUT=/tmp/claude-0/test/ ... --render
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
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
import eye as EY
import mite as M
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 960
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (32, "eye"), (77, "lashes"), (119, "crawl"), (162, "wash"), (215, "soap"), (249, "demodex"),
         (315, "follicle"), (387, "feed"), (462, "fear"), (514, "lightsoff"), (564, "emerge"), (590, "walk"),
         (641, "sleepface"), (673, "gross"), (708, "noanus"), (771, "waste"), (860, "die"), (896, "burst")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "lightsoff", "sleepface")
BATHN = ("wash",)
MACN = ("eye",)
MICN = ("lashes", "crawl", "demodex", "fear", "emerge", "walk", "gross")
CUTN = ("soap", "follicle", "feed", "die", "burst")
XRMN = ("noanus", "waste")
ROOM = rng(*ROOMN); BATHR = rng(*BATHN); MACR = rng(*MACN); MICR = rng(*MICN); CUTR = rng(*CUTN); XRMR = rng(*XRMN)
F_OFF = 532        # "o'chirib" — chiroq o'chadi
F_GROSS = 677      # "jirkanch"
F_BURST = 929      # "yorilib"

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
val_key(screen_m, "on", 1, 2.0)
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
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.95, -1.4, 0), 70, 1.0))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, -0.75, 0), 90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, -0.95, 1.03), 90, 1.0))
R_(plane("rug", (1.6, 1.2), (-0.2, 0.6, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))
# karavot (Poly Haven GothicBed_01): uzunligi Y bo'ylab; matras balandligi va bosh tomoni ray_cast bilan o'lchanadi
BED = Vector((-1.5, 1.42, 0.0))
bed_grp = R_(import_gltf(PH + "GothicBed_01/GothicBed_01.gltf", tuple(BED), 0, 1.0))
bpy.context.view_layer.update()
_dg = bpy.context.evaluated_depsgraph_get()
def hit_z(x, y):
    ok, loc, *_ = sc.ray_cast(_dg, Vector((x, y, 1.9)), Vector((0, 0, -1)))
    return loc.z if ok else 0.0
MTOP = hit_z(BED.x, BED.y)
HEAD_SIGN = 1 if hit_z(BED.x, BED.y + 0.97) > hit_z(BED.x, BED.y - 0.97) else -1
print("BED mattress", round(MTOP, 3), "head", HEAD_SIGN)
if HEAD_SIGN < 0:
    bed_grp.rotation_euler.z = R(180)
R_(import_gltf(PH + "ClassicNightstand_01/ClassicNightstand_01.gltf", (BED.x + 1.08, BED.y + 0.78, 0), 0, 1.0))
NS_TOP = 0.70
R_(import_gltf(PH + "alarm_clock_01/alarm_clock_01.gltf", (BED.x + 1.2, BED.y + 0.7, NS_TOP), -30, 1.0))
# tungi chiroq (tumbochkada)
BL = Vector((BED.x + 0.98, BED.y + 0.86, NS_TOP))
shade_m = mat("shade", (0.95, 0.88, 0.75), 0.8, sss=0.2)
shade_on = None
R_(cyl("bl_base", 0.07, 0.03, tuple(BL + V(0, 0, 0.015)), mat("bl_base_m", (0.75, 0.6, 0.35), 0.25, metal=0.9)))
R_(cyl("bl_stem", 0.01, 0.28, tuple(BL + V(0, 0, 0.16)), mat("bl_stem_m", (0.75, 0.6, 0.35), 0.25, metal=0.9)))
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.15, radius2=0.09, depth=0.2, end_fill_type="NOTHING", location=tuple(BL + V(0, 0, 0.36)))
shade = bpy.context.object; shade.name = "bl_shade"; shade.data.materials.append(shade_m)
so_ = shade.modifiers.new("so", "SOLIDIFY"); so_.thickness = 0.004
for p_ in shade.data.polygons: p_.use_smooth = True
R_(shade)
# yostiq, ko'rpa
pillow_m = mat("pillow", (0.92, 0.92, 0.95), 0.75, sss=0.1)
blanket_m = mat("blanket", (0.42, 0.55, 0.72), 0.85, sss=0.05)
nb = blanket_m.node_tree.nodes; lb = blanket_m.node_tree.links
_wv = nb.new("ShaderNodeTexWave"); _wv.inputs["Scale"].default_value = 60.0; _bp = nb.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.15
lb.new(_wv.outputs["Fac"], _bp.inputs["Height"]); lb.new(_bp.outputs[0], nb["Principled BSDF"].inputs["Normal"])

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


# ======================================================================
# 2) MEGAN: stolda (Typing) -> hammomda yuz yuvish (Crying, oldinga/orqaga zanjir) -> karavotda uxlaydi (Laying_Sleeping)
# ======================================================================
MEG = Vector((0.6, -0.6, 0.0))
BATH = Vector((-40.0, 0.0, 0.0))
SLEEP = Vector((BED.x - 0.12 * HEAD_SIGN * 0, BED.y + HEAD_SIGN * 0.12, MTOP - 0.95))
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften(mmeshes, 0.48)
place(mroot, 1, tuple(MEG), 0)
W0, W1 = S["wash"]
place(mroot, W0 - 24, tuple(BATH), 0)
LO0 = S["lightsoff"][0]
place(mroot, LO0 - 2, tuple(SLEEP), 0 if HEAD_SIGN > 0 else 180)
ckey(mroot)
TYP = A_("Typing.fbx")
strip(meg, TYP, 1, repeat=span(TYP, W0 - 26))
CRY = A_("Crying.fbx")
C0 = W0 - 22                                              # qo'llar ~20 kadrda yuzga yetadi
strip(meg, CRY, C0, src=(1, 31))
RA, RB = 31, 75
f = C0 + int(round(30 * 0.8)); k = 0
while f < W1 + 4:
    strip(meg, CRY, f, src=(RA, RB), rev=(k % 2 == 1), speed=1.25)
    f += int(round((RB - RA) * 0.8 / 1.25)); k += 1
SLP = A_("Laying_Sleeping.fbx", inplace=False)
strip(meg, SLP, LO0 - 2, repeat=span(SLP, END - LO0 + 4))
for o in mmeshes: vis(o, ROOM + BATHR, recursive=False)
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items() if n in ROOMN + BATHN}
print("FACE", {k: tuple(round(x, 3) for x in v) for k, v in FACE.items()})

# yostiq va ko'rpa (karavotda yotgan Megan atrofida)
HEADW = wpos(headE, S["lightsoff"][0] + 10)
pil = R_(box("pillow", (0.62, 0.4, 0.12), (BED.x, HEADW.y + 0.04 * HEAD_SIGN, MTOP + 0.05), pillow_m, bevel=0.04))
pil.modifiers.new("sub", "SUBSURF").levels = 2
def blanket_mesh():
    n_x, n_y = 60, 70; bm = bmesh.new(); vs = []
    y0 = SLEEP.y - HEAD_SIGN * 1.25; y1 = SLEEP.y + HEAD_SIGN * 0.12
    rr = random.Random(4)
    for j in range(n_y):
        for i in range(n_x):
            x = BED.x - 0.78 + 1.56 * i / (n_x - 1); y = y0 + (y1 - y0) * j / (n_y - 1)
            dx = abs(x - BED.x)
            z = MTOP + 0.025 + 0.2 * math.exp(-((x - (SLEEP.x + 0.02)) / 0.24) ** 2) * min(1, (j / (n_y - 1)) * 3 + 0.4)
            if dx > 0.7: z = MTOP + 0.02 - (dx - 0.7) * 0.3
            z += 0.012 * math.sin(x * 23 + y * 7) * math.sin(y * 11)
            vs.append(bm.verts.new((x, y, z)))
    for j in range(n_y - 1):
        for i in range(n_x - 1):
            a = j * n_x + i; bm.faces.new((vs[a], vs[a + 1], vs[a + n_x + 1], vs[a + n_x]))
    me = bpy.data.meshes.new("blanket"); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new("blanket", me); sc.collection.objects.link(o); me.materials.append(blanket_m)
    so = o.modifiers.new("so", "SOLIDIFY"); so.thickness = 0.03
    return o
blk = R_(blanket_mesh())
vis(blk, rng("lightsoff", "sleepface")); vis(pil, rng("lightsoff", "sleepface"))

# ======================================================================
# 3) HAMMOM: plitka devorlar, oyna, lavabo, jo'mrak, ko'pik
# ======================================================================
bath_objs = []
def B_(o): bath_objs.append(o); return o
tile_w = pbr("tile_w", "long_white_tiles", 1.4)
tile_f = pbr("tile_f", "floor_tiles_06", 1.0)
BW = BATH.y - 0.75
B_(plane("b_floor", (2.4, 2.4), tuple(BATH + V(0, 0.3, 0)), tile_f))
B_(box("b_wall", (2.4, 0.1, 2.6), tuple(BATH + V(0, -0.8, 1.3)), tile_w))
B_(box("b_wallL", (0.1, 2.4, 2.6), tuple(BATH + V(-1.15, 0.3, 1.3)), tile_w))
B_(box("b_wallR", (0.1, 2.4, 2.6), tuple(BATH + V(1.15, 0.3, 1.3)), tile_w))
B_(box("b_ceil", (2.4, 2.4, 0.05), tuple(BATH + V(0, 0.3, 2.62)), mat("b_ceil_m", (0.92, 0.92, 0.9), 0.8)))
vanity_m = mat("vanity", (0.18, 0.2, 0.22), 0.4)
B_(box("vanity", (1.2, 0.5, 0.82), tuple(BATH + V(0, -0.5, 0.41)), vanity_m, bevel=0.01))
B_(box("counter", (1.26, 0.56, 0.04), tuple(BATH + V(0, -0.48, 0.84)), mat("counter_m", (0.92, 0.9, 0.86), 0.12, coat=0.5), bevel=0.005))
ceramic = mat("ceramic", (0.95, 0.95, 0.94), 0.08, coat=0.8)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.21, location=tuple(BATH + V(0, -0.45, 0.99)))
bowl = bpy.context.object; bowl.name = "bowl"; bowl.scale = (1, 1, 0.62)
bm_ = bmesh.new(); bm_.from_mesh(bowl.data)
bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.z > 0.0], context="VERTS"); bm_.to_mesh(bowl.data); bm_.free()
bowl.data.materials.append(ceramic); bsol = bowl.modifiers.new("so", "SOLIDIFY"); bsol.thickness = 0.012
for p_ in bowl.data.polygons: p_.use_smooth = True
B_(bowl)
chrome = mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0)
B_(cyl("tap_post", 0.018, 0.32, tuple(BATH + V(0, -0.7, 1.02)), chrome))
B_(cyl("tap_spout", 0.014, 0.2, tuple(BATH + V(0, -0.61, 1.17)), chrome, rot=(90, 0, 0)))
water_m = P.water_material("tapwater")
B_(cyl("stream", 0.0055, 0.28, tuple(BATH + V(0, -0.515, 1.02)), water_m))
mirror_m = mat("mirror", (0.95, 0.95, 0.95), 0.02, metal=1.0)
B_(plane("mirror", (1.0, 0.85), tuple(BATH + V(0, -0.745, 1.58)), mirror_m, rot=(90, 0, 0)))
B_(box("mirror_light", (0.9, 0.04, 0.03), tuple(BATH + V(0, -0.72, 2.06)), mat("mlight", (1, 0.97, 0.92), 0.5, emit=6.0)))
B_(box("towel", (0.35, 0.06, 0.5), tuple(BATH + V(-0.85, -0.7, 1.2)), mat("towel_m", (0.75, 0.82, 0.88), 0.95), bevel=0.02))
B_(cyl("soap_bottle", 0.035, 0.16, tuple(BATH + V(0.4, -0.62, 0.94)), mat("soapb", (0.55, 0.85, 0.75), 0.15, trans=0.6)))
B_(cyl("soap_pump", 0.01, 0.05, tuple(BATH + V(0.4, -0.62, 1.04)), chrome))
B_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", tuple(BATH + V(0.75, -0.55, 0.86)), 30, 0.55))
for o in bath_objs: vis(o, BATHR)
# ko'pik: yuzda va kaftlarda (Head: X chap, Y tepa, Z old)
foam_m = mat("foam", (0.97, 0.97, 0.98), 0.35, sss=0.4, coat=0.6)
foam_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.004
rf = random.Random(11)
foam = []
FOAM_PTS = [((0.038, 0.05, 0.095), 0.018), ((-0.038, 0.05, 0.095), 0.018), ((0, 0.12, 0.105), 0.025), ((0, 0.01, 0.1), 0.014),
            ((0.022, 0.08, 0.11), 0.01), ((-0.022, 0.08, 0.11), 0.01)]
for ci, (c_, sp) in enumerate(FOAM_PTS):
    for i in range(18):
        p_ = Vector(c_) + Vector((rf.uniform(-sp, sp), rf.uniform(-sp, sp) * 0.7, rf.uniform(-0.004, 0.006)))
        foam.append(sphere(f"foamf{ci}_{i}", rf.uniform(0.003, 0.007), tuple(p_), foam_m, sub=2, parent=headE))
for bone in ("LeftHand", "RightHand"):
    hb = child_of_bone("foam_" + bone, meg, bone)
    for i in range(16):
        p_ = Vector((rf.uniform(-0.035, 0.035), rf.uniform(0.02, 0.11), rf.uniform(-0.025, 0.025)))
        foam.append(sphere(f"foam{bone}{i}", rf.uniform(0.006, 0.012), tuple(p_), foam_m, sub=2, parent=hb))
for o in foam: vis(o, BATHR, recursive=False)

# ======================================================================
# 4) MAKRO KO'Z (real o'lcham): ochiq ko'z, kipriklar
# ======================================================================
MAC = V(0.0, 30.0, 1.2)
eye = EY.build_eye("meye", tuple(MAC))
LS = eye["shape"]; eroot = eye["root"]
bskin = mat("macro_skin", (0.62, 0.38, 0.3), 0.5, sss=0.3)
bskin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.002
mback = plane("macro_back", (0.5, 0.5), tuple(MAC + V(0, -0.0045, 0)), bskin, rot=(90, 0, 0))
def EL(p): return MAC + Vector(p)
vis(eroot, MACR); vis(mback, MACR)

# ======================================================================
# 5) MIKRO TERI (1000x): teshiklar, tuklar, kipriklar, po'stlar, kanalar
# ======================================================================
MIC = V(0.0, 60.0, 0.0)
micE = empty("micE", tuple(MIC))
rp = random.Random(21)
EVP = {"lash1": (-3.0, -3.2), "lash2": (-2.1, -3.5), "lash3": (-3.9, -2.6), "fear": (2.6, 2.4), "emerge": (-2.3, 2.3),
       "hero": (2.9, -2.9), "walk1": (-0.6, 0.9), "walk2": (1.2, -0.7)}
pores = [(x, y, 0.2, 0.75) for x, y in EVP.values()]
for _ in range(900):
    x, y = rp.uniform(-4.6, 4.6), rp.uniform(-4.6, 4.6)
    if all(math.hypot(x - a, y - b) > 1.15 for a, b, *_ in pores) and math.hypot(x - 2.2, y + 2.0) > 0.9 \
       and not (-3.4 < x < 3.4 and -0.45 < y < 0.45):
        pores.append((x, y, rp.uniform(0.13, 0.2), 0.7))
SK = M.Skin(10.0, pores, seed=3)
skin_m = M.skin_micro_material()
surf = M.skin_surface("micro_skin", SK, 0.025, skin_m, micE)
def SH(x, y): return SK.H(x, y)
def SN(x, y, e=0.02):
    return Vector((-(SH(x + e, y) - SH(x - e, y)) / (2 * e), -(SH(x, y + e) - SH(x, y - e)) / (2 * e), 1)).normalized()
def MP(x, y, z=0.0): return MIC + V(x, y, z)
flk = M.flakes("flake", SK, 70, M.skin_micro_material("flake_m"), micE)
vh_m = M.hair_material("vellus", (0.5, 0.36, 0.24), 0.35, trans=0.5)
lash_m = M.hair_material("lash_micro", (0.05, 0.03, 0.02), 0.3)
hairs = []
for i, (x, y, r, d) in enumerate(pores):
    lash = i < 3
    a = rp.uniform(0, 6.28); tilt = 0.55 if lash else rp.uniform(0.3, 0.8)
    dirv = Vector((math.cos(a) * tilt, math.sin(a) * tilt, 1))
    if lash: dirv = Vector((0.35, 0.9, 0.6))
    hairs.append(M.hair(f"hair{i}", (x, y, SH(x, y) - 0.05), dirv, 4.5 if lash else rp.uniform(1.2, 2.6), 0.075 if lash else rp.uniform(0.03, 0.045),
                        lash_m if lash else vh_m, micE, bend=Vector((0, 0, -0.6 if lash else -0.25)), depth=d * 0.9))
kit = M.Kit()
mite_m = kit.mat
# teshiklardan chiqib turgan dumlar (boshi pastda)
tails = []
for i, (x, y, r, d) in enumerate(pores):
    if (x, y) in (EVP["fear"], EVP["emerge"]): continue
    n_ = 4 if i < 3 else rp.choice((1, 2, 2, 3))
    for k in range(n_):
        a = rp.uniform(0, 6.28) + k * 2.1; off = rp.uniform(0.045, 0.085)
        t_, _ = M.build_mite(f"tail{i}_{k}", kit, micE, legs=False, seed=i * 10 + k)
        up_ = rp.uniform(0.04, 0.16)
        # dum uchi (y=-0.225) teshikdan up_ ga chiqadi: root = uchi - fwd*(-0.225) ... fwd pastga qaragan
        fwd = Vector((-math.cos(a) * 0.12, -math.sin(a) * 0.12, -1)).normalized()
        tip = Vector((x + off * math.cos(a), y + off * math.sin(a), SH(x, y) * 0.0 + up_))
        t_.location = tip + fwd * 0.225
        t_.rotation_euler = M.orient(fwd, Vector((math.cos(a), math.sin(a), 0)))
        tails.append(t_)
# qahramon kana (yuruvchi)
hero, hero_b = M.build_mite("hero", kit, micE, seed=2)
def put(o, f, x, y, heading, lift=0.036, roll=0.0):
    n_ = SN(x, y); fw = Vector((math.cos(heading), math.sin(heading), 0)); fw = (fw - n_ * fw.dot(n_)).normalized()
    up_ = n_
    if roll: up_ = (Matrix.Rotation(roll, 3, fw) @ n_)
    o.location = Vector((x, y, SH(x, y))) + n_ * lift; o.keyframe_insert("location", frame=f)
    o.rotation_euler = M.orient(fw, up_, o.rotation_euler); o.keyframe_insert("rotation_euler", frame=f)
def walk_path(o, f0, f1, p0, p1, wig=0.12, step=3, curve=0.0):
    """p0 -> p1 to'g'ri/egri yo'l, bosh yo'nalishga qaraydi, yengil chayqalish"""
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; nrm = Vector((-d.y, d.x)).normalized()
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = (f - f0) / max(1, f1 - f0); q = p0 + d * t + nrm * curve * math.sin(math.pi * t)
        dd = d + nrm * curve * math.pi * math.cos(math.pi * t)
        hd = math.atan2(dd.y, dd.x) + wig * math.sin(f * 0.45 + sum(map(ord, o.name)) % 7)
        put(o, f, q.x, q.y, hd)
HX, HY = 2.2, -2.0
CR0, CR1 = S["crawl"]; walk_path(hero, CR0, CR1, (HX - 0.25, HY - 0.12), (HX + 0.08, HY + 0.02)); M.walk(hero, CR0, CR1, 4.5)
DM0, DM1 = S["demodex"]; walk_path(hero, DM0, DM1, (HX + 0.0, HY + 0.0), (HX + 0.14, HY + 0.12), curve=0.05); M.walk(hero, DM0, DM1, 5)
GR0, GR1 = S["gross"]; walk_path(hero, GR0, GR1, (HX - 0.05, HY - 0.05), (HX + 0.1, HY + 0.02)); M.walk(hero, GR0, GR1, 3)
interp(hero, "LINEAR", "location"); interp(hero, "LINEAR", "rotation_euler")
vis(hero, rng("crawl", "demodex", "gross"))
# yorug'likdan qochish: 4 kana teshik atrofidan dumi bilan teshikka sirg'alib kiradi
FE0, FE1 = S["fear"]
fx, fy = EVP["fear"]
fearm = []
for k in range(4):
    m_, _ = M.build_mite(f"fear{k}", kit, micE, seed=40 + k); fearm.append(m_)
    a = 0.6 + k * 1.57 + rp.uniform(-0.3, 0.3); d0 = 0.42 + 0.05 * k
    st = FE0 + 4 + k * 4
    for f in range(FE0, FE1 + 2, 2):
        t = max(0.0, min(1.0, (f - st) / 36.0)); t = t * t * (3 - 2 * t)
        dist = d0 * (1 - t) + 0.0 * t
        x = fx + math.cos(a) * max(dist, 0.0); y = fy + math.sin(a) * max(dist, 0.0)
        hd = a                                                  # bosh tashqariga, dum teshikka
        if dist > 0.18:
            put(m_, f, x, y, hd)
        else:                                                   # teshik ichiga pastga sirg'aladi
            dn = (0.18 - dist) / 0.18
            fwd = Vector((math.cos(a), math.sin(a), 0.2 + 2.5 * dn)).normalized()
            p_ = Vector((fx + math.cos(a) * 0.18 * (1 - dn) * 0.6, fy + math.sin(a) * 0.18 * (1 - dn) * 0.6, SH(x, y) + 0.03 - 0.45 * dn))
            m_.location = p_ - fwd * 0.12 * dn; m_.keyframe_insert("location", frame=f)
            m_.rotation_euler = M.orient(fwd, Vector((-math.cos(a), -math.sin(a), 0.4)), m_.rotation_euler); m_.keyframe_insert("rotation_euler", frame=f)
    M.walk(m_, FE0, FE1, -6)
    vis(m_, [S["fear"]])
# tunda teshikdan chiqish
EM0, EM1 = S["emerge"]
ex, ey = EVP["emerge"]
emm = []
for k in range(3):
    m_, _ = M.build_mite(f"emerge{k}", kit, micE, seed=60 + k); emm.append(m_)
    a = 0.4 + k * 2.1
    for f in range(EM0, EM1 + 2, 2):
        t = (f - EM0 + k * 3) / 30.0; t = max(0.0, min(1.0, t))
        if t < 0.55:
            dn = 1 - t / 0.55
            fwd = Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, 1.0 - 0.5 * (1 - dn))).normalized()
            p_ = Vector((ex + math.cos(a) * 0.05, ey + math.sin(a) * 0.05, SH(ex, ey) * 0.2 - 0.38 * dn + 0.03))
            m_.location = p_; m_.keyframe_insert("location", frame=f)
            m_.rotation_euler = M.orient(fwd, Vector((math.cos(a), math.sin(a), -0.2)), m_.rotation_euler); m_.keyframe_insert("rotation_euler", frame=f)
        else:
            d_ = 0.12 + (t - 0.55) / 0.45 * 0.3
            put(m_, f, ex + math.cos(a) * d_, ey + math.sin(a) * d_, a)
    M.walk(m_, EM0, EM1, 5)
    vis(m_, [S["emerge"]])
# tungi sayr: yuruvchi kanalar to'dasi (y ~ 0 yo'lak)
WK0, WK1 = S["walk"]
walkers = []
for k in range(7):
    m_, _ = M.build_mite(f"walker{k}", kit, micE, seed=80 + k); walkers.append(m_)
    y0 = rp.uniform(-0.3, 0.3); x0 = -1.9 + k * 0.5 + rp.uniform(-0.15, 0.15)
    walk_path(m_, WK0, WK1, (x0, y0), (x0 + 0.55, y0 + rp.uniform(-0.12, 0.12)), wig=0.15, curve=rp.uniform(-0.08, 0.08))
    M.walk(m_, WK0, WK1, 6)
    vis(m_, [S["walk"]])
for m_ in walkers + fearm + emm:
    interp(m_, "LINEAR", "location"); interp(m_, "LINEAR", "rotation_euler")
mic_static = [surf] + flk + hairs + tails
for o in mic_static: vis(o, MICR, recursive=False)

# ======================================================================
# 6) KESIM (1000x): teri bloki, tuk illizi, tuk, yog' bezi, illizdagi kanalar
#    mahalliy o'qlar (cutE): tepa = +Z (teri yuzasi z=0), kesim tekisligi x = 0, kamera +X tomonda
# ======================================================================
CUT = V(60.0, 0.0, 0.0)
cutE = empty("cutE", tuple(CUT))
cut_objs = [cutE]
def C_(o):
    if o.parent is None: o.parent = cutE
    cut_objs.append(o); return o
cutm = M.cut_material()
blk_c = box("skin_block", (1.6, 4.4, 2.6), (-0.8, 0.0, -1.3), cutm)
AX = Vector((0, 0.24, -1)).normalized()
FOLL_D = 1.95
def AP(d, y=0.0, x=0.0): return AX * d + Vector((x, y, 0))
cutter = cyl("canal_cut", 0.165, FOLL_D + 0.6, (0, 0, 0), cutm, verts=48)
cutter.location = tuple(AX * (FOLL_D / 2 - 0.25)); cutter.rotation_euler = AX.to_track_quat("Z", "Y").to_euler()
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.17, radius2=0.42, depth=0.42, location=(0, 0, -0.17))
funnel = bpy.context.object; funnel.name = "funnel_cut"
for ct in (cutter, funnel):
    bo = blk_c.modifiers.new("b_" + ct.name, "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = ct; bo.solver = "EXACT"
    ct.hide_render = True; ct.hide_viewport = True
bpy.context.view_layer.objects.active = blk_c
for o in bpy.context.view_layer.objects: o.select_set(False)
blk_c.select_set(True)
for md in list(blk_c.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
bpy.data.objects.remove(cutter); bpy.data.objects.remove(funnel)
for p_ in blk_c.data.polygons: p_.use_smooth = False
C_(blk_c)                                                    # boolean'dan keyin bog'lanadi (kesuvchilar dunyo koordinatasida)
# tuk va piyozchasi
chair_m = M.hair_material("cut_hair", (0.2, 0.12, 0.07), 0.3)
C_(M.hair("cut_hair", AP(0, x=-0.1), -AX + Vector((0, 0.05, 0)), 1.6, 0.06, chair_m, None, bend=Vector((0, 0.5, -0.2)), depth=FOLL_D - 0.15))
bulb_m = mat("bulb", (0.32, 0.18, 0.12), 0.4, sss=0.3)
C_(sphere("hair_bulb", 0.13, tuple(AP(FOLL_D - 0.05, x=-0.1)), bulb_m, scale=(1, 1, 1.3)))
# yog' bezi (metaball bo'laklari), kesilgan
gl_c = AP(0.85, y=-0.33)
balls = [(gl_c.x, gl_c.y + dy, gl_c.z + dz, r) for dy, dz, r in ((0, 0, 0.17), (-0.12, 0.1, 0.13), (-0.08, -0.15, 0.14), (0.08, -0.12, 0.12),
                                                                  (-0.2, -0.05, 0.11), (0.1, 0.12, 0.11), (0.17, 0.02, 0.09))]
gland_m = mat("gland_m", (0.95, 0.78, 0.35), 0.3, sss=0.5, coat=0.5)
for i, (x, y, z, r_) in enumerate(balls):
    C_(sphere(f"gland{i}", r_, (x, y, z), gland_m, scale=(0.6, 1, 1), sub=4))
duct = C_(P.tube("duct", [gl_c + Vector((0, 0.15, 0.05)), AP(0.72, y=-0.09, x=-0.02)], 0.04, gland_m, None))
# qon tomirlari (kesim yuzasida)
vessel_m = mat("vessel", (0.55, 0.03, 0.03), 0.3, sss=0.4, coat=0.4)
for i, pts in enumerate(([(0, -2.1, -0.5), (0, -1.2, -0.62), (0, -0.6, -0.4), (0, -0.35, -0.3)],
                         [(0, 2.1, -1.2), (0, 1.3, -1.05), (0, 0.8, -1.3), (0, 0.6, -1.6)],
                         [(0, -2.1, -1.9), (0, -1.0, -1.75), (0, -0.2, -2.05), (0, 0.6, -2.3)])):
    C_(P.tube(f"vessel{i}", [Vector(p) + Vector((0.005, 0, 0)) for p in pts], 0.035, vessel_m, None))
# yuza po'stlari
for i in range(14):
    fl_ = C_(sphere(f"cflake{i}", 1.0, (-rp.uniform(0.05, 1.4), rp.uniform(-2.0, 2.0), 0.004), mat("cfl", (0.95, 0.88, 0.7), 0.6), sub=1))
    s_ = rp.uniform(0.06, 0.14); fl_.scale = (s_, s_ * 0.8, 0.012)
    if abs(fl_.location.y) < 0.5: fl_.location.y += 0.8
# illizdagi kanalar (boshi pastda, orqasi kameraga)
cmites = []
for k, (d, y, x) in enumerate(((0.48, 0.085, 0.0), (0.8, -0.08, 0.01), (1.1, 0.075, 0.0))):
    m_, b_ = M.build_mite(f"cmite{k}", kit, cutE, seed=100 + k, mat=(M.mite_material(f"cmite_m{k}") if k == 1 else None))
    m_.location = AP(d, y=y, x=x) - AX * 0.0
    m_.rotation_euler = M.orient(AX, Vector((1, 0, 0.0)))
    m_["amp"] = 0.55; m_.keyframe_insert('["amp"]', frame=1)
    M.walk(m_, 1, END, 70)
    cmites.append((m_, b_))
DIE_M, DIE_B = cmites[1]
die_mat = DIE_B.material_slots[0].material
for o in DIE_M.children:
    if o.material_slots: o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = die_mat
DI0, DI1 = S["die"]; BU0, BU1 = S["burst"]
val_key(die_mat, "dead", 1, 0.0); val_key(die_mat, "dead", DI0 + 2, 0.0); val_key(die_mat, "dead", DI0 + 30, 1.0)
DIE_M["amp"] = 0.55; DIE_M.keyframe_insert('["amp"]', frame=DI0 + 2); DIE_M["amp"] = 0.0; DIE_M.keyframe_insert('["amp"]', frame=DI0 + 14)
for f, s_ in ((BU0, 1.0), (BU0 + 12, 1.12), (F_BURST - 1, 1.32)):
    DIE_M.scale = (s_, 1.0 + (s_ - 1) * 0.2, s_); DIE_M.keyframe_insert("scale", frame=f)
for f, s_ in ((F_BURST - 4, 1.30), (F_BURST - 3, 1.36), (F_BURST - 2, 1.28), (F_BURST - 1, 1.34)):
    DIE_M.scale = (s_, 1.0 + (s_ - 1) * 0.2, s_); DIE_M.keyframe_insert("scale", frame=f)
for o in [DIE_M] + list(DIE_M.children):
    o.hide_render = False; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=F_BURST); interp(o, "CONSTANT", "hide_render")
# teri yog'i tomchilari (og'izlar yonida), oziqlanganda kichrayadi
sebum_m = mat("sebum", (0.98, 0.82, 0.3), 0.08, sss=0.3, coat=1.0, trans=0.3)
FE_0, FE_1 = S["feed"]
sebum = []
for k, (m_, b_) in enumerate(cmites):
    head = m_.location + AX * 0.1
    for i in range(4):
        p_ = head + AX * rp.uniform(0.0, 0.08) + Vector((rp.uniform(-0.04, 0.0), rp.uniform(-0.07, 0.07), 0))
        s0 = rp.uniform(0.02, 0.035); o = C_(sphere(f"sebum{k}_{i}", s0, tuple(p_), sebum_m, sub=3))
        o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=FE_0 + 6)
        o.scale = (0.25,) * 3; o.keyframe_insert("scale", frame=FE_1 - rp.randint(0, 20))
        sebum.append(o)
# yorilish: axlat va tana parchalari otilib chiqadi
waste_m = mat("waste", (0.12, 0.07, 0.03), 0.4, coat=0.6)
shard_m = mat("shard", (0.7, 0.6, 0.45), 0.4, sss=0.4)
debris = []
bc = DIE_M.location.copy()
for i in range(110):
    tail_t = rp.uniform(-0.2, 0.05)
    p0 = bc + AX * (-tail_t) * 1.0 + Vector((rp.uniform(-0.02, 0.02), rp.uniform(-0.025, 0.025), 0))
    v = Vector((rp.uniform(0.05, 0.45), rp.uniform(-0.7, 0.7), rp.uniform(-0.6, 0.6)))
    v -= AX * v.dot(AX) * 0.3
    isw = i < 80
    o = C_(sphere(f"debris{i}", rp.uniform(0.008, 0.028) if isw else rp.uniform(0.01, 0.02), tuple(p0), waste_m if isw else shard_m, sub=2))
    if not isw: o.scale = (1.6, 0.5, 1.0)
    for f in (F_BURST, F_BURST + 2, F_BURST + 5, F_BURST + 10, F_BURST + 18, END + 1):
        t = f - F_BURST; s_ = (1 - math.exp(-t / 5.0)) * 0.45
        q = p0 + v * s_
        q.x = min(q.x, 0.35)
        key(o, f, loc=tuple(q))
    interp(o, "BEZIER", "location")
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=F_BURST)
    interp(o, "CONSTANT", "hide_render")
    debris.append(o)
# ko'pik (sovun) teri ustida — faqat "soap" kadri
bub_m = mat("soapbub", (1, 1, 1), 0.0, trans=1.0)
_bb = bub_m.node_tree.nodes["Principled BSDF"]; _bb.inputs["IOR"].default_value = 1.08
if "Thin Film Thickness" in _bb.inputs: _bb.inputs["Thin Film Thickness"].default_value = 260.0; _bb.inputs["Thin Film IOR"].default_value = 1.33
foam2_m = mat("foam2", (0.97, 0.97, 0.98), 0.3, sss=0.3, coat=0.5)
cfoam = []
for i in range(150):
    a = rp.uniform(0, 6.28); rr = 1.6 * math.sqrt(rp.random())
    y = math.sin(a) * rr; x = -abs(math.cos(a) * rr) * 0.8 - 0.04
    r_ = rp.uniform(0.03, 0.2) if i % 3 else rp.uniform(0.015, 0.05)
    o = sphere(f"cbub{i}", r_, (x, y, r_ * 0.75), bub_m if i % 2 else foam2_m, sub=3)
    if abs(y) < 0.38 and x > -0.45: o.location.z = r_ * 0.7 + 0.02           # teshik ustida ham — lekin ichkariga kirmaydi
    cfoam.append(C_(o))
for o in cfoam: vis(o, [S["soap"]], recursive=False)
for o in cut_objs:
    if o in cfoam or o in debris or o is DIE_M: continue
    vis(o, CUTR, recursive=False)
for m_, b_ in cmites:
    if m_ is DIE_M: continue
    vis(m_, CUTR)
for o in [DIE_M] + list(DIE_M.children):
    for fc in fcurves(o):
        if fc.data_path == "hide_render": fc.keyframe_points.clear()
    for f, on in ((1, False), (CUTR[0][0], True), (CUTR[0][1] + 1, False), (S["follicle"][0], True), (S["feed"][1] + 1, False), (DI0, True), (F_BURST, False)):
        o.hide_render = not on; o.keyframe_insert("hide_render", frame=f)
    interp(o, "CONSTANT", "hide_render")
for o in debris:
    for fc in fcurves(o):
        if fc.data_path == "hide_render": fc.keyframe_points.clear()
    for f, on in ((1, False), (F_BURST, True)):
        o.hide_render = not on; o.keyframe_insert("hide_render", frame=f)
    interp(o, "CONSTANT", "hide_render")

# ======================================================================
# 7) RENTGEN KANA: shaffof tana, ichak, to'planayotgan axlat, yopiq dum uchi
# ======================================================================
XRM = V(60.0, -60.0, 1.0)
xm = xr_mat("xr_mite")
xme = empty("xmE", tuple(XRM))
xmite, xbody = M.build_mite("xmite", kit, xme, mat=xm, seed=5)
xmite.rotation_euler = (0, 0, R(90))                        # bosh +X ... kamera -Y tomondan
M.walk(xmite, S["noanus"][0], END, 30)
gut_m = mat("gut", (0.9, 0.45, 0.35), 0.4, emit=0.4, alpha=0.25)
gut = sphere("gut", 1.0, (0, -0.085, -0.002), gut_m, sub=4, parent=xmite); gut.scale = (0.019, 0.125, 0.016)
pharynx = P.tube("pharynx", [Vector((0, 0.083, -0.004)), Vector((0, 0.05, -0.002)), Vector((0, 0.035, -0.002))], 0.006, gut_m, xmite)
WA0, WA1 = S["waste"]
xwaste = []
NW = 46
for i in range(NW):
    t = i / (NW - 1)
    y = -0.19 + t * 0.2 + rp.uniform(-0.01, 0.01)
    rmax = 0.017 * math.sqrt(max(0.05, 1 - ((y + 0.085) / 0.125) ** 2))
    a = rp.uniform(0, 6.28); rr = rp.uniform(0, rmax * 0.7)
    o = sphere(f"xwaste{i}", rp.uniform(0.0045, 0.008), (math.cos(a) * rr, y, math.sin(a) * rr * 0.8), waste_m, sub=2, parent=xmite)
    fa = int(WA0 + 6 + t * (WA1 - WA0 - 20))
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=fa - 1)
    o.scale = (1.0,) * 3; o.keyframe_insert("scale", frame=fa + 4)
    xwaste.append(o)
# dastlabki ozgina axlat (1-kun)
seal_m = bpy.data.materials.new("seal"); seal_m.use_nodes = True
_b = seal_m.node_tree.nodes["Principled BSDF"]; _b.inputs["Base Color"].default_value = (1, 0.05, 0.03, 1)
_b.inputs["Emission Color"].default_value = (1, 0.05, 0.02, 1); _b.inputs["Emission Strength"].default_value = 0.0
seal = sphere("seal", 0.013, (0, M.TAIL_Y + 0.006, 0), seal_m, sub=3, parent=xmite)
NA0, NA1 = S["noanus"]
for f, e in ((1, 0.0), (NA0 + 26, 0.0), (NA0 + 34, 2.2), (NA0 + 42, 0.8), (NA0 + 48, 2.2), (NA0 + 56, 0.8), (NA1, 2.0), (WA0 + 10, 0.0)):
    _b.inputs["Emission Strength"].default_value = e; _b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
# kun hisoblagichi: "1-KUN" -> "14-KUN"
txt_m = mat("txt", (1, 1, 1), 0.5, emit=3.0)
cnt = text_obj("daycount", "1-KUN", tuple(XRM + V(0.07, 0.0, 0.11)), (90, 0, 0), 0.045, txt_m)
DAY0, DAY1 = WA0 + 6, WA1 - 14
def _day(scene, *a):
    f = scene.frame_current
    d = 1 + int(round(13 * max(0.0, min(1.0, (f - DAY0) / (DAY1 - DAY0)))))
    cnt.data.body = f"{d}-KUN"
bpy.app.handlers.frame_change_pre.append(_day)
vis(xme, XRMR)
vis(cnt, [S["waste"]])

# ======================================================================
# 8) KAMERALAR
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
def hero_w(f):
    sc.frame_set(f); bpy.context.view_layer.update(); return hero.matrix_world.translation.copy()
# 1 ILGAK: poldan, keng ob'ektiv, tez push-in
H0, H1 = S["hook"]; FP = FACE["hook"]
c = abs_cam("hook", [(H0, FP + V(1.05, -0.35, -0.42)), (H1, FP + V(0.42, -0.3, -0.1))],
            [(H0, FP + V(0, -0.15, -0.15)), (H1, FP + V(0, -0.02, -0.02))], 16, 2.8)
lens_keys(c, [(H0, 15), (H1, 21)])
# 2 makro ko'z: kipriklar ildiziga push-in
E0, E1 = S["eye"]
c = abs_cam("eye", [(E0, EL((0.02, -0.07, -0.012))), (E1, EL((0.006, -0.038, -0.002)))],
            [(E0, EL((0.0, -0.012, 0.004))), (E1, EL((0.002, -0.013, 0.006)))], 40, 16.0)
# 3 kipriklar ildizi (mikro): tepadan crash zoom
LA0, LA1 = S["lashes"]; LP = MP(*EVP["lash1"])
c = abs_cam("lashes", [(LA0, LP + V(1.6, -2.4, 2.2)), (LA0 + 8, LP + V(0.7, -1.2, 1.05)), (LA1, LP + V(0.5, -0.95, 0.8))],
            [(LA0, LP + V(0, 0, 0.0)), (LA1, LP + V(0, 0, 0.02))], 26, 4.0, clip=0.01)
lens_keys(c, [(LA0, 20), (LA0 + 8, 30), (LA1, 32)]); shake(c, LA0 + 7, LA0 + 18, 0.03, seed=3)
# 4 kana yuradi: yonlama ergashish, past burchak
CR0, CR1 = S["crawl"]
hw0, hw1 = hero_w(CR0), hero_w(CR1)
c = abs_cam("crawl", [(CR0, hw0 + V(0.1, -0.6, 0.3)), (CR1, hw1 + V(0.25, -0.52, 0.26))],
            [(CR0, hw0 + V(0.0, 0, 0.0)), (CR1, hw1 + V(0.02, 0, 0.0))], 45, 2.8, clip=0.01)
# 5 hammom: yondan, past burchak, qo'l kamerasi
FW = FACE["wash"]
c = abs_cam("wash", [(W0, FW + V(0.62, 0.05, -0.28)), (W1, FW + V(0.48, -0.08, -0.2))],
            [(W0, FW + V(0, -0.04, -0.06)), (W1, FW + V(0, -0.04, -0.04))], 24, 2.8)
shake(c, W0, W1, 0.01, seed=5, decay=False)
# 6 sovun yetmaydi (kesim): ko'pikdan illiz tubiga qarab tushish
SO0, SO1 = S["soap"]; CP = CUT
c = abs_cam("soap", [(SO0, CP + V(2.6, -0.5, 0.9)), (SO1, CP + V(2.4, -0.1, -0.7))],
            [(SO0, CP + V(0, 0.0, 0.05)), (SO1, CP + AP(0.85))], 24, 8.0, clip=0.01)
# 7 Demodex: qahramon plan, sekin aylanma
DM0, DM1 = S["demodex"]; hd_ = hero_w((DM0 + DM1) // 2)
c = abs_cam("demodex", [(DM0, hd_ + V(0.42, -0.42, 0.16)), ((DM0 + DM1) // 2, hd_ + V(0.55, 0.0, 0.14)), (DM1, hd_ + V(0.4, 0.42, 0.12))],
            [(DM0, hd_ + V(0, 0, 0.0)), (DM1, hd_ + V(0.03, 0.03, 0.0))], 50, 2.4, clip=0.01)
# 8 illiz ichida: pastga push-in
FO0, FO1 = S["follicle"]
c = abs_cam("follicle", [(FO0, CP + V(2.2, 0.0, 0.1)), (FO1, CP + AP(0.6) + V(1.15, 0.0, 0.05))],
            [(FO0, CP + AP(0.5)), (FO1, CP + AP(0.78))], 30, 5.6, clip=0.01)
# 9 oziqlanish: og'izlar yaqin, aylanma
FE0_, FE1_ = S["feed"]; MH = CP + cmites[0][0].location + AX * 0.12
c = abs_cam("feed", [(FE0_, MH + V(0.55, -0.3, 0.12)), (FE1_, MH + V(0.5, 0.25, -0.1))],
            [(FE0_, MH), (FE1_, MH + AX * 0.04)], 42, 4.0, clip=0.01)
# 10 yorug'likdan qochish: tepadan, yorqin; sekin pastga
FP_ = MP(*EVP["fear"])
c = abs_cam("fear", [(FE0, FP_ + V(0.4, -1.25, 1.0)), (FE1, FP_ + V(0.25, -0.95, 0.65))], [(FE0, FP_ + V(0, 0, -0.02)), (FE1, FP_ + V(0, 0, -0.08))], 30, 4.0, clip=0.01)
# 11 chiroq o'chadi: karavot, past burchak, sekin push-in
L0, L1 = S["lightsoff"]; FL = FACE["lightsoff"]
c = abs_cam("lightsoff", [(L0, FL + V(1.5, -1.3, 0.55)), (L1, FL + V(1.15, -0.95, 0.42))],
            [(L0, FL + V(0.15, -0.45, -0.1)), (L1, FL + V(0.1, -0.3, -0.05))], 22, 4.0)
# 12 teshikdan chiqish: crash zoom
EP = MP(*EVP["emerge"])
c = abs_cam("emerge", [(EM0, EP + V(0.9, -1.5, 1.1)), (EM0 + 6, EP + V(0.45, -0.8, 0.5)), (EM1, EP + V(0.4, -0.72, 0.45))],
            [(EM0, EP + V(0, 0, 0)), (EM1, EP + V(0.05, 0.05, 0))], 28, 4.0, clip=0.01)
lens_keys(c, [(EM0, 22), (EM0 + 6, 34), (EM1, 36)]); shake(c, EM0 + 5, EM0 + 16, 0.02, seed=12)
# 13 tungi sayr: yonlama siljish
c = abs_cam("walk", [(WK0, MP(-1.0, -1.35, 1.0)), (WK1, MP(0.2, -1.3, 0.9))], [(WK0, MP(-0.6, 0.0, 0.0)), (WK1, MP(0.5, 0.0, 0.0))], 32, 4.0, clip=0.01)
# 14 uxlayotgan yuz: sekin push-in
SF0, SF1 = S["sleepface"]; FS = FACE["sleepface"]
c = rel_cam("sleepface", faceT, 40, 2.2, [(SF0, V(0.25, -0.5, 0.3)), (SF1, V(0.18, -0.36, 0.22))])
# 15 jirkanch: crash zoom
gw = hero_w(F_GROSS)
c = abs_cam("gross", [(GR0, gw + V(0.9, -0.9, 0.55)), (F_GROSS - 1, gw + V(0.7, -0.7, 0.42)), (F_GROSS + 3, gw + V(0.34, -0.36, 0.2)), (GR1, gw + V(0.3, -0.33, 0.18))],
            [(GR0, gw), (GR1, gw + V(0.05, 0.02, 0))], 30, 2.8, clip=0.01)
lens_keys(c, [(GR0, 26), (F_GROSS - 1, 28), (F_GROSS + 3, 42), (GR1, 45)]); shake(c, F_GROSS, F_GROSS + 12, 0.02, seed=15)
# 16 orqa teshik yo'q: tana bo'ylab dumga siljish (rentgen)
NA0, NA1 = S["noanus"]; XC = XRM
c = abs_cam("noanus", [(NA0, XC + V(-0.12, -0.5, 0.16)), (NA1, XC + V(0.3, -0.36, 0.08))],
            [(NA0, XC + V(0.0, 0, 0)), (NA1, XC + V(0.2, 0, 0))], 40, 5.6, clip=0.005)
# 17 axlat to'planadi: aylanma
c = abs_cam("waste", [(WA0, XC + V(-0.2, -0.62, 0.22)), ((WA0 + WA1) // 2, XC + V(0.05, -0.66, 0.12)), (WA1, XC + V(0.3, -0.58, 0.05))],
            [(WA0, XC + V(0.07, 0, 0.02)), (WA1, XC + V(0.07, 0, 0.02))], 32, 8.0, clip=0.005)
# 18 o'lim: illizdagi kana, sekin push-in
DW = CP + DIE_M.location
c = abs_cam("die", [(DI0, DW + V(1.0, -0.15, 0.1)), (DI1, DW + V(0.72, -0.1, 0.06))], [(DI0, DW), (DI1, DW)], 40, 4.0, clip=0.01)
# 19 yorilish: crash zoom + silkinish
c = abs_cam("burst", [(BU0, DW + V(0.85, 0.15, 0.12)), (F_BURST - 1, DW + V(0.7, 0.1, 0.08)), (F_BURST + 3, DW + V(0.85, 0.05, 0.1)), (BU1, DW + V(1.0, 0.0, 0.12))],
            [(BU0, DW), (BU1, DW)], 34, 4.0, clip=0.01)
lens_keys(c, [(BU0, 32), (F_BURST - 1, 42), (F_BURST + 3, 30), (BU1, 28)]); shake(c, F_BURST, F_BURST + 16, 0.035, seed=19)
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
# 9) YORUG'LIK VA FON
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
WORLD = {"room": (0.035, (0.004, 0.008, 0.02), 1.0), "night": (0.0, (0.002, 0.004, 0.012), 1.0), "bath": (0.0, (0.02, 0.02, 0.02), 1.0),
         "mac": (0.0, (0.0, 0.0, 0.0), 0.0), "mic": (0.0, (0.16, 0.07, 0.055), 1.0), "micn": (0.0, (0.01, 0.025, 0.06), 1.0),
         "cut": (0.0, (0.012, 0.018, 0.035), 1.0), "xrm": (0.0, (0.003, 0.008, 0.025), 1.0)}
def world_of(n):
    if n == "hook": return "room"
    if n in ROOMN: return "night"
    if n in BATHN: return "bath"
    if n in MACN: return "mac"
    if n in ("emerge", "walk"): return "micn"
    if n in MICN: return "mic"
    if n in CUTN: return "cut"
    return "xrm"
for f, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
HOOK = [S["hook"]]
# xona (kechqurun, ilgak): stol lampasi, noutbuk, shift, oy nuri
area("lamp_key", (1.2, -1.35, 1.3), 0.25, (1.0, 0.68, 0.38), lights_for(HOOK, 60.0), target=FT)
area("lap_glow", tuple(LAP + V(0, -0.05, 0.25)), 0.3, (0.6, 0.75, 1.0), lights_for(HOOK, 9.0), target=FT)
area("ceil_fill", (0.0, 0.6, 2.6), 2.0, (1.0, 0.85, 0.7), lights_for(HOOK, 18.0), target=empty("cfT", (0, 0.6, 0)))
area("moon_rim", (0.6, Y0 + 0.3, 2.0), 1.4, (0.55, 0.7, 1.0), lights_for(HOOK, 45.0), target=FT)
point("lamp_bulb", (1.22, -1.38, 1.18), 0.02, (1.0, 0.7, 0.4), lights_for(HOOK, 6.0))
# tun: tungi chiroq (F_OFF da o'chadi), keyin ko'k oy nuri
NIGHT = rng("lightsoff", "sleepface")
point("bed_bulb", tuple(BL + V(0, 0, 0.36)), 0.04, (1.0, 0.68, 0.36), [(1, 0), (L0, 60.0), (F_OFF, 0.0)])
area("bed_warm", tuple(BL + V(-0.4, -0.4, 0.6)), 0.6, (1.0, 0.7, 0.45), [(1, 0), (L0, 30.0), (F_OFF, 0.0)], target=FT)
shade_e = shade_m.node_tree.nodes["Principled BSDF"]
shade_e.inputs["Emission Color"].default_value = (1.0, 0.75, 0.45, 1)
for f, e in ((1, 0.0), (L0, 2.5), (F_OFF, 0.0)):
    shade_e.inputs["Emission Strength"].default_value = e; shade_e.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
ckey(shade_m.node_tree)
area("moon_key", (BED.x + 1.6, BED.y - 1.2, 2.2), 1.2, (0.45, 0.6, 1.0), [(1, 0), (L0, 10.0), (F_OFF, 50.0), (S["sleepface"][1] + 1, 0)], target=FT)
area("moon_fill", (BED.x - 0.2, BED.y - 2.0, 1.4), 1.5, (0.4, 0.5, 0.9), [(1, 0), (L0, 4.0), (F_OFF, 14.0), (S["sleepface"][1] + 1, 0)], target=FT)
# hammom
BT = empty("bathT", tuple(BATH + V(0, -0.1, 1.45)))
area("B_ceil", tuple(BATH + V(0.2, 0.1, 2.5)), 1.0, (1.0, 0.97, 0.94), lights_for(BATHR, 120.0), target=BT)
area("B_mirror", tuple(BATH + V(0, -0.6, 2.0)), 0.8, (1.0, 0.95, 0.9), lights_for(BATHR, 40.0), target=FT)
area("B_rim", tuple(BATH + V(-0.8, 0.6, 1.8)), 0.6, (0.7, 0.85, 1.0), lights_for(BATHR, 35.0), target=FT)
# makro ko'z
MT = empty("macroT", tuple(EL((0, -0.012, 0))))
area("M_key", tuple(EL((-0.12, -0.2, 0.16))), 0.18, (1.0, 0.95, 0.9), lights_for(MACR, 5.0), target=MT)
area("M_fill", tuple(EL((0.16, -0.18, -0.06))), 0.2, (0.9, 0.93, 1.0), lights_for(MACR, 2.0), target=MT)
# mikro teri: kunduzi iliq, "fear" da kuchli oq nur, tunda ko'k
MICD = rng("lashes", "crawl", "demodex", "gross")
MICN_ = rng("emerge", "walk")
def micro_lights(tag, cx, cy, ranges, key_e, rim_e, key_col=(1.0, 0.9, 0.78), rim_col=(0.5, 0.7, 1.0)):
    t = empty(f"mT_{tag}", tuple(MP(cx, cy, 0)))
    area(f"mk_{tag}", tuple(MP(cx - 1.5, cy - 1.8, 2.4)), 1.5, key_col, lights_for(ranges, key_e), target=t)
    area(f"mr_{tag}", tuple(MP(cx + 1.8, cy + 1.6, 0.9)), 1.2, rim_col, lights_for(ranges, rim_e), target=t)
    area(f"mf_{tag}", tuple(MP(cx + 1.2, cy - 1.6, 0.6)), 1.5, (1.0, 0.8, 0.7), lights_for(ranges, key_e * 0.25), target=t)
micro_lights("hero", HX, HY, rng("crawl", "demodex", "gross"), 55.0, 140.0)
micro_lights("lash", *EVP["lash1"], [S["lashes"]], 90.0, 160.0)
micro_lights("fear", *EVP["fear"], [S["fear"]], 260.0, 80.0, key_col=(1.0, 1.0, 1.0))
micro_lights("emerge", *EVP["emerge"], [S["emerge"]], 30.0, 140.0, key_col=(0.45, 0.6, 1.0), rim_col=(0.3, 0.8, 1.0))
micro_lights("walk", 0.0, 0.0, [S["walk"]], 30.0, 140.0, key_col=(0.45, 0.6, 1.0), rim_col=(0.3, 0.8, 1.0))
# kesim
CT_ = empty("cutT", tuple(CUT + AP(0.6)))
area("C_key", tuple(CUT + V(2.4, -1.8, 1.8)), 2.0, (1.0, 0.95, 0.9), lights_for(CUTR, 260.0), target=CT_)
area("C_fill", tuple(CUT + V(2.2, 1.6, -1.2)), 1.8, (1.0, 0.85, 0.75), lights_for(CUTR, 90.0), target=CT_)
area("C_rim", tuple(CUT + V(-0.6, -2.4, 1.6)), 1.5, (0.35, 0.6, 1.0), lights_for(CUTR, 160.0), target=CT_)
area("C_top", tuple(CUT + V(0.4, 0.3, 2.4)), 1.5, (1.0, 0.95, 0.9), lights_for([S["soap"]], 150.0), target=empty("cutT2", tuple(CUT)))
# rentgen kana
XT = empty("xmT", tuple(XRM))
area("X_key", tuple(XRM + V(0.4, -0.6, 0.6)), 0.6, (0.8, 0.9, 1.0), lights_for(XRMR, 12.0), target=XT)
area("X_rim", tuple(XRM + V(-0.5, 0.6, 0.4)), 0.6, (0.3, 0.55, 1.0), lights_for(XRMR, 18.0), target=XT)

# ======================================================================
# 10) RENDER
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
