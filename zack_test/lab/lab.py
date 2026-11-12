# Lab pufakchasi (mukotsele) — Zack D. Films uslubida 35.25 s video (846 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, zack_test/ishqalash/ishqalash.py (xona, kamera va material yordamchilari),
# zack_test/burish/parts.py (quvur/egri chiziq, impuls poyezdi).
# Assetlar: zack_test/tools/get_lab.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/lab/lab.py --render
# Sinov:  FRAMES=30,150,450,640,800 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler, Quaternion
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
END = 846
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (44, "face"), (94, "dent"), (127, "bubble"), (217, "pop"), (265, "days"), (309, "regrow"),
         (370, "dive"), (426, "glands"), (526, "bite2"), (561, "duct"), (625, "snap"), (680, "pump"), (749, "swell"),
         (819, "final")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "face", "days", "bite2")
MACN = ("dent", "bubble", "pop", "regrow", "final")
CUTN = ("dive", "glands", "duct", "snap", "pump", "swell")
ROOM = rng(*ROOMN); MACR = rng(*MACN); CUTR = rng(*CUTN)
F_DENT = 97          # "tishlab" — tishlar qisadi
F_SEZ = 196          # "sezganmisiz" — crash zoom
F_POP = 240          # "yorib"
F_CHIQ = 338         # "chiqib"
F_YUZ = 455          # "yuzlab"
F_BIR = 577          # "birining"
F_NAY = 611          # "ingichka naychasi"
F_UZ = 640           # "uzilib"
F_EZ = 664           # "ezilib"
F_CHQM = 783         # "chiqolmay"

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

def mixc(N, L, fac, a, b):
    """RGBA aralashma: fac (soket yoki son), a/b (soket yoki rang)"""
    m = N.new("ShaderNodeMix"); m.data_type = "RGBA"
    if isinstance(fac, (int, float)): m.inputs[0].default_value = fac
    else: L.new(fac, m.inputs[0])
    for i, x in ((6, a), (7, b)):
        if isinstance(x, tuple): m.inputs[i].default_value = (*x[:3], 1)
        else: L.new(x, m.inputs[i])
    return m.outputs[2]
def clamp01(N, L, x): return P.math_n(N, L, "MAXIMUM", P.math_n(N, L, "MINIMUM", x, 1.0), 0.0)
def frame_dir(d, face=Vector((0, -1, 0))):
    Yl = d.normalized(); Zl = (face - Yl * face.dot(Yl)).normalized(); Xl = Yl.cross(Zl)
    return Matrix((Xl, Yl, Zl)).transposed().to_euler()

# ---------------- shilliq qavat materiali (makro lab va kesim) ----------------
def mucosa_mat(name, nscale=60.0, zmap=False, bub=None, rb=0.04, sss_scale=0.004):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = nscale * 0.25; nz.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    col = mixc(N, L, nz.outputs["Fac"], (0.66, 0.2, 0.24), (0.88, 0.42, 0.44))
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = nscale * 0.08; wv.inputs["Distortion"].default_value = 11.0
    wv.inputs["Detail"].default_value = 6.0; wv.inputs["Detail Scale"].default_value = 2.0; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    vein = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "GREATER_THAN", wv.outputs["Fac"], 0.91), 0.6)
    wv2 = N.new("ShaderNodeTexWave"); wv2.inputs["Scale"].default_value = nscale * 0.2; wv2.inputs["Distortion"].default_value = 16.0
    wv2.inputs["Detail"].default_value = 4.0; L.new(tc.outputs["Object"], wv2.inputs["Vector"]); wv2.bands_direction = "Y"
    vein2 = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "GREATER_THAN", wv2.outputs["Fac"], 0.93), 0.45)
    verm = None; skin = None
    if zmap:
        verm = clamp01(N, L, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", -0.085, sp.outputs["Z"]), 0.035))
        skin = clamp01(N, L, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", -0.165, sp.outputs["Z"]), 0.03))
        vmask = P.math_n(N, L, "SUBTRACT", 1.0, verm)
        vein = P.math_n(N, L, "MULTIPLY", vein, vmask); vein2 = P.math_n(N, L, "MULTIPLY", vein2, vmask)
    col = mixc(N, L, vein, col, (0.42, 0.03, 0.07))
    col = mixc(N, L, vein2, col, (0.55, 0.08, 0.14))
    rough = P.math_n(N, L, "ADD", 0.1, P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.12))
    coat = 1.0
    if zmap:
        lipn = N.new("ShaderNodeTexNoise"); lipn.inputs["Scale"].default_value = nscale * 2; L.new(tc.outputs["Object"], lipn.inputs["Vector"])
        col = mixc(N, L, verm, col, mixc(N, L, lipn.outputs["Fac"], (0.5, 0.1, 0.12), (0.62, 0.17, 0.18)))
        col = mixc(N, L, skin, col, (0.74, 0.47, 0.37))
        rough = P.math_n(N, L, "ADD", rough, P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", verm, 0.18), P.math_n(N, L, "MULTIPLY", skin, 0.2)))
        coat = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", verm, 0.8))
    em = None; tr = None
    if bub is not None:
        bx, bz = bub
        cmb = N.new("ShaderNodeCombineXYZ"); L.new(sp.outputs["X"], cmb.inputs[0]); L.new(sp.outputs["Z"], cmb.inputs[2])
        d = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "DISTANCE", cmb.outputs[0], (bx, 0.0, bz), vec=True), rb)
        bv = value_node(m, "bub", 0.0); wd = value_node(m, "wound", 0.0)
        bm_ = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", clamp01(N, L, P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", d, d))), 0.45), bv)
        col = mixc(N, L, P.math_n(N, L, "MULTIPLY", bm_, 0.88), col, (0.6, 0.66, 0.92))
        rough = mixc(N, L, bm_, rough, (0.02, 0.02, 0.02))
        rough = P.math_n(N, L, "ADD", rough, 0.0)   # rang soketidan qiymatga
        em = P.math_n(N, L, "MULTIPLY", bm_, 0.35)
        tr = P.math_n(N, L, "MULTIPLY", bm_, 0.3)
        wn = N.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = nscale * 1.2; L.new(tc.outputs["Object"], wn.inputs["Vector"])
        dw = P.math_n(N, L, "DIVIDE", d, 0.7)
        wm = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", clamp01(N, L, P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", dw, dw))),
                      P.math_n(N, L, "ADD", 0.45, P.math_n(N, L, "MULTIPLY", wn.outputs["Fac"], 0.8))), wd)
        wm = clamp01(N, L, P.math_n(N, L, "MULTIPLY", wm, 1.6))
        col = mixc(N, L, wm, col, (0.34, 0.02, 0.04))
        ring = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "GREATER_THAN", dw, 0.75), P.math_n(N, L, "LESS_THAN", dw, 0.95)), wd)
        col = mixc(N, L, P.math_n(N, L, "MULTIPLY", ring, 0.6), col, (0.9, 0.82, 0.7))
    L.new(col, b.inputs["Base Color"])
    if isinstance(rough, (int, float)): b.inputs["Roughness"].default_value = rough
    else: L.new(rough, b.inputs["Roughness"])
    if isinstance(coat, (int, float)): b.inputs["Coat Weight"].default_value = coat
    else: L.new(coat, b.inputs["Coat Weight"])
    b.inputs["Coat Roughness"].default_value = 0.04
    b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Scale"].default_value = sss_scale
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.25)
    bnz = N.new("ShaderNodeTexNoise"); bnz.inputs["Scale"].default_value = nscale * 4; bnz.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Object"], bnz.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.18; bp.inputs["Distance"].default_value = 0.002
    L.new(bnz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    if em is not None:
        b.inputs["Emission Color"].default_value = (0.45, 0.6, 1.0, 1); L.new(em, b.inputs["Emission Strength"])
        L.new(tr, b.inputs["Transmission Weight"])
    return m

def enamel_mat(name):
    m = mat(name, (0.93, 0.89, 0.78), 0.18, coat=0.6, sss=0.25)
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Subsurface Scale"].default_value = 0.01
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.9, 0.7)
    return m

def tooth_mesh(name, w, h, t, m, parent=None, edge_taper=0.5):
    """kurak tish toji: kesuvchi qirrasi pastda (z=0), tanasi +Z bo'ylab; old yuz -Y"""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        x, y, z = v.co
        x = math.copysign(abs(x) ** 0.45, x); z = math.copysign(abs(z) ** 0.35, z); y = math.copysign(abs(y) ** 0.7, y)
        k = (z + 1) / 2                                    # 0 qirra, 1 ildiz
        y *= edge_taper + (1 - edge_taper) * min(1.0, k * 1.6)
        if y < 0: y *= 0.85                                 # old yuzi tekisroq
        v.co = (x * w / 2, y * t / 2, (z + 1) / 2 * h)
    o.data.shade_smooth(); o.data.materials.append(m)
    if parent: o.parent = parent
    return o

# ======================================================================
# 1) OSHXONA (kunduzi): ovqat stoli, likop, sendvich, devor soati, oshxona shkaflari
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.96, 0.92, 0.84))
X0, X1, Y0, Y1, HZ_ = -2.4, 2.4, -1.8, 2.6, 2.7
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.92, 0.92, 0.9), 0.8)))
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
    c_ = R_(box("curtain", (0.45, 0.06, 2.4), (x, Y0 + 0.08, 1.3), mat("curtain_m", (0.92, 0.88, 0.78), 0.9, sss=0.1)))
    d_ = c_.modifiers.new("wave", "WAVE"); d_.height = 0.04; d_.width = 0.12; d_.narrowness = 1; d_.use_y = False; d_.speed = 0
R_(box("baseboard", (X1 - X0, 0.03, 0.1), (0, Y1 - 0.015, 0.05), frame_m))
R_(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X0 + 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
# tashqarida: kunduzgi hovli, daraxtlar, qo'shni uylar
R_(plane("out_ground", (40, 30), (0, Y0 - 16, -0.3), mat("out_grass", (0.12, 0.2, 0.06), 0.9)))
rw = random.Random(3)
bld_ms = [mat("bld_a", (0.75, 0.68, 0.58), 0.8), mat("bld_b", (0.62, 0.6, 0.58), 0.8)]
glass_m = mat("bglass", (0.08, 0.1, 0.13), 0.1, metal=0.4)
for i in range(6):
    x = -6 + i * 2.6 + rw.uniform(-0.4, 0.4); h = rw.uniform(4, 9); y = -14 - rw.uniform(0, 6)
    R_(box(f"bld{i}", (2.0, 1.5, h), (x, y, h / 2 - 0.3), rw.choice(bld_ms)))
    for k in range(rw.randint(4, 8)):
        R_(box(f"bwin{i}_{k}", (0.35, 0.02, 0.45), (x + rw.uniform(-0.7, 0.7), y + 0.76, rw.uniform(0.6, h - 0.6)), glass_m))
leaf_m = mat("leaf", (0.12, 0.3, 0.07), 0.7, sss=0.2); bark_m = mat("bark", (0.22, 0.15, 0.1), 0.9)
for i in range(5):
    x = -5 + i * 2.7 + rw.uniform(-0.5, 0.5); y = -6 - rw.uniform(0, 4)
    R_(cyl(f"trunk{i}", 0.12, 2.0, (x, y, 0.7), bark_m, verts=12))
    tr_ = R_(sphere(f"crown{i}", 1.4, (x, y, 2.4), leaf_m, scale=(1, 1, 1.15), sub=3))
    dd = tr_.modifiers.new("d", "DISPLACE"); _t = bpy.data.textures.new(f"crown_t{i}", "CLOUDS"); _t.noise_scale = 0.5; dd.texture = _t; dd.strength = 0.5

DESK = Vector((0.6, -1.3, 0)); DESK_TOP = 0.715
R_(import_gltf(PH + "WoodenTable_01/WoodenTable_01.gltf", tuple(DESK), 0, (1.0, 1.1, 1.3)))
R_(import_gltf(PH + "modern_arm_chair_01/modern_arm_chair_01.gltf", (0.6, -0.5, 0), 0, 1.0))
# dasturxon (stol yo'lagi), likop, sendvichlar, sharbat stakani, salat
R_(box("runner", (0.42, 0.95, 0.003), (0.6, -1.3, DESK_TOP + 0.0015), mat("runner_m", (0.75, 0.22, 0.15), 0.85)))
cer = mat("cer_w", (0.93, 0.93, 0.9), 0.2, coat=0.7)
PLATE = Vector((0.6, -1.08, DESK_TOP + 0.003))
def plate(name, loc, r):
    g = R_(empty(name, tuple(loc)))
    cyl(name + "_b", r * 0.62, 0.008, (0, 0, 0.004), cer, parent=g, verts=48)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r * 0.64, radius2=r, depth=0.018, location=(0, 0, 0.012))
    c_ = bpy.context.object; c_.name = name + "_rim"; c_.data.materials.append(cer); c_.parent = g
    so_ = c_.modifiers.new("s", "SOLIDIFY"); so_.thickness = 0.004
    bm = bmesh.new(); bm.from_mesh(c_.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.99], context="FACES_ONLY")
    bm.to_mesh(c_.data); bm.free(); c_.data.shade_smooth()
    return g
plate("plate", PLATE, 0.13)
bread_m = mat("bread", (0.86, 0.66, 0.38), 0.75, sss=0.15); crust_m = mat("crust", (0.55, 0.32, 0.12), 0.7)
lett_m = mat("lettuce", (0.3, 0.6, 0.12), 0.45, sss=0.3); tom_m = mat("tomato", (0.75, 0.08, 0.04), 0.25, coat=0.5, sss=0.2)
chs_m = mat("cheese", (0.95, 0.68, 0.15), 0.4, sss=0.2); ham_m = mat("ham", (0.85, 0.45, 0.42), 0.45, sss=0.3)
def sandwich(name, parent=None, loc=(0, 0, 0)):
    """uchburchak sendvich: mahalliy +X = uchi (tishlanadigan tomon), Z = qalinlik"""
    g = empty(name, loc, parent)
    def tri(nm, th, z, m, s=1.0, wav=0.0):
        bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=0.072 * s, depth=th, location=(0, 0, z))
        o = bpy.context.object; o.name = name + nm; o.data.materials.append(m); o.parent = g
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = min(0.006, th * 0.45); bv.segments = 3
        if wav:
            o.data.update(); sd = o.modifiers.new("sd", "SUBSURF"); sd.levels = 2
            dd = o.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new(name + nm + "_t", "CLOUDS"); t_.noise_scale = 0.01
            dd.texture = t_; dd.strength = wav
        for p in o.data.polygons: p.use_smooth = True
        return o
    tri("_b0", 0.014, -0.016, bread_m); tri("_l", 0.004, -0.007, lett_m, 1.06, 0.004); tri("_h", 0.004, -0.002, ham_m, 1.0)
    tri("_c", 0.003, 0.002, chs_m, 1.03); tri("_t", 0.004, 0.006, tom_m, 0.95); tri("_b1", 0.014, 0.016, bread_m)
    for o in g.children:
        if o.name.endswith(("_b0", "_b1")):
            o.data.materials.append(crust_m)
            for p in o.data.polygons: p.material_index = 1 if abs(p.normal.z) < 0.5 else 0
    return g
R_(sandwich("sand_plate", None, tuple(PLATE + V(0.02, -0.02, 0.03))))
glass_jm = mat("juice_glass", (0.95, 0.97, 1.0), 0.02, trans=1.0); juice_m = mat("juice", (1.0, 0.45, 0.05), 0.05, trans=0.6, sss=0.3)
GL = V(0.1, -1.02, DESK_TOP)
R_(cyl("glass", 0.035, 0.12, tuple(GL + V(0, 0, 0.06)), glass_jm)); R_(cyl("juice", 0.031, 0.085, tuple(GL + V(0, 0, 0.045)), juice_m))
bowl = R_(sphere("bowl", 0.085, tuple(V(0.28, -1.25, DESK_TOP + 0.06)), cer, scale=(1, 1, 0.6), sub=4))
bm = bmesh.new(); bm.from_mesh(bowl.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.02], context="VERTS"); bm.to_mesh(bowl.data); bm.free()
bowl.modifiers.new("s", "SOLIDIFY").thickness = 0.004
fruit_ms = [mat("apple_r", (0.7, 0.05, 0.04), 0.3, coat=0.6), mat("apple_g", (0.45, 0.65, 0.1), 0.3, coat=0.6), mat("orange", (1.0, 0.45, 0.04), 0.5)]
for i, (x, y) in enumerate(((-0.03, 0.0), (0.035, 0.01), (0.0, 0.035), (0.01, -0.035))):
    R_(sphere(f"fruit{i}", 0.032, tuple(V(0.28 + x, -1.25 + y, DESK_TOP + 0.07 + 0.01 * (i % 2))), fruit_ms[i % 3], sub=3))
R_(cyl("napkin", 0.05, 0.004, tuple(V(0.95, -1.25, DESK_TOP + 0.002)), mat("napkin_m", (0.95, 0.95, 0.92), 0.9), verts=4))
# oshxona shkaflari (o'ng devor)
cab_m = mat("cab", (0.32, 0.45, 0.42), 0.45, coat=0.2); top_m = mat("counter", (0.85, 0.83, 0.8), 0.25, coat=0.4)
steel = mat("steel", (0.75, 0.76, 0.78), 0.25, metal=1.0)
for i, y in enumerate((0.0, 0.6, 1.2, 1.8)):
    R_(box(f"cab_lo{i}", (0.6, 0.58, 0.86), (X1 - 0.3, y + 0.3, 0.43), cab_m, bevel=0.006))
    R_(box(f"cab_hi{i}", (0.35, 0.58, 0.7), (X1 - 0.175, y + 0.3, 1.85), cab_m, bevel=0.006))
    R_(box(f"handle_lo{i}", (0.02, 0.15, 0.015), (X1 - 0.61, y + 0.3, 0.78), steel))
R_(box("counter", (0.64, 2.44, 0.04), (X1 - 0.32, 1.22, 0.88), top_m))
R_(box("backsplash", (0.01, 2.44, 0.6), (X1 - 0.005, 1.22, 1.2), mat("tile_w", (0.9, 0.9, 0.87), 0.15, coat=0.5)))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.0, 2.2, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.95, -1.45, 0), 70, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.9, Y1 - 0.03, 1.45), 0, 1.3))
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.9, 2.15, 0), 0, 1.0))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, 0.9, 0), 90, 1.0))
R_(plane("rug", (2.2, 1.6), (-0.8, 1.3, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))
# devor soati (chap devor), millari timelapse'da aylanadi
CLK = V(X0 + 0.02, -0.75, 1.85)
clk = R_(empty("clock", tuple(CLK)))
cyl("clk_rim", 0.2, 0.05, (0.025, 0, 0), mat("clk_rim_m", (0.08, 0.08, 0.09), 0.3, metal=0.5), rot=(0, 90, 0), parent=clk, verts=64)
cyl("clk_face", 0.18, 0.052, (0.026, 0, 0), mat("clk_face_m", (0.97, 0.96, 0.93), 0.5), rot=(0, 90, 0), parent=clk, verts=64)
mark_m = mat("clk_mark", (0.05, 0.05, 0.05), 0.5)
for i in range(12):
    a = 2 * math.pi * i / 12
    box(f"clk_m{i}", (0.004, 0.012 if i % 3 else 0.018, 0.03 if i % 3 else 0.045), (0.053, 0.15 * math.sin(a), 0.15 * math.cos(a)), mark_m,
        rot=(-math.degrees(a), 0, 0), parent=clk)
hand_m = mat("clk_hand", (0.04, 0.04, 0.05), 0.4)
hourE = empty("clk_hour", (0.056, 0, 0), clk); minE = empty("clk_min", (0.06, 0, 0), clk)
box("clk_hh", (0.004, 0.014, 0.1), (0, 0, 0.04), hand_m, parent=hourE)
box("clk_mh", (0.004, 0.009, 0.15), (0, 0, 0.06), hand_m, parent=minE)
box("clk_sec", (0.003, 0.003, 0.16), (0.004, 0, 0.05), mat("clk_red", (0.8, 0.05, 0.03), 0.4), parent=minE)
DA0, DA1 = S["days"]
for e_, turns in ((hourE, 4.0), (minE, 48.0)):
    e_.rotation_euler = (R(-90), 0, 0); e_.keyframe_insert("rotation_euler", frame=DA0)
    e_.rotation_euler = (R(-90) - turns * 2 * math.pi, 0, 0); e_.keyframe_insert("rotation_euler", frame=DA1 + 1)
    interp(e_, "LINEAR")
hourE.rotation_euler = (R(-90), 0, 0)

# ======================================================================
# 2) MEGAN: o'tiradi (Typing oyoqlar + Seated_Idle tananing yuqori qismi), sendvich tishlaydi (Drinking), siltanadi (Spat_In_Face)
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
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0, rev=False):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo; s.use_reverse = rev
    return s
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)
MEG = Vector((0.6, -0.6, 0.0))
mroot.location = MEG
TYP = A_("Typing.fbx")
strip(meg, TYP, 1, repeat=span(TYP, END + 2))
SID = upper(A_("Seated_Idle.fbx"))
strip(meg, SID, 1, repeat=span(SID, END + 2))
strip(meg, SID, DA0 - 2, speed=2.6, repeat=span(SID, (DA1 - DA0 + 6) * 2.6), bi=2, bo=2)    # timelapse: tezlashgan
DRK = upper(A_("Drinking.fbx"))
SPT = upper(A_("Spat_In_Face.fbx"))
def bite(f0, hold_to, flinch):
    """sendvichni og'izga olib boradi (Drinking 60..104), og'izda ushlab turadi, keyin siltanadi"""
    strip(meg, DRK, f0, src=(60, 104), bi=5)
    f = f0 + 35; k = 0
    while f < hold_to:
        strip(meg, DRK, f, src=(92, 104), rev=(k % 2 == 0)); f += 10; k += 1
    strip(meg, SPT, flinch, src=(1, 77), bi=4, bo=8)
    return f0 + 26                                      # qo'l og'izga yetgan kadr
F_MOUTH1 = bite(4, 66, 66)
F_MOUTH2 = bite(506, 544, 542)
for o in mmeshes: vis(o, ROOM, recursive=False)

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
mouthT = empty("mouthT", (0.0, 0.0, 0.125), headE)          # Head: X chap, Y tepa, Z old
handE = child_of_bone("meg_lhand", meg, "LeftHand")
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
# sendvich: qo'lda, uchi og'izga qaragan (og'izdagi kadrda qo'l fazosida o'lchanadi)
sc.frame_set(F_MOUTH1 + 6); bpy.context.view_layer.update()
mloc = handE.matrix_world.inverted() @ mouthT.matrix_world.translation
hup = handE.matrix_world.inverted().to_3x3() @ Vector((0, 0, 1))
sandE = empty("sandE", tuple(mloc * 0.7), handE)
sandE.rotation_euler = frame_dir(mloc, hup)                 # mahalliy Y = og'iz tomoni
sh = sandwich("sand_hand", sandE, (0, 0.0, 0)); sh.rotation_euler = (0, 0, R(90)); sh.scale = (0.85,) * 3
print("SANDWICH mloc", tuple(round(x, 3) for x in mloc), "len", round(mloc.length, 3))
vis(sandE, ROOM)
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items()}
print("FACE", {k: tuple(round(x, 3) for x in v) for k, v in FACE.items() if k in ROOMN})

# ======================================================================
# 3) MAKRO LAB (10x masshtab: 1 sm = 0.1 m): ag'darilgan pastki labning ichki shilliq qavati, milk, pastki tishlar
#    mahalliy o'qlar: x o'ng, z tepa, kamera -Y tomonda (sirt kameraga qaragan)
# ======================================================================
MO = V(0.0, 30.0, 1.0)
mac_objs = []
def M_(o): mac_objs.append(o); return o
BC = (0.03, -0.025)                 # pufakcha markazi (x, z)
RB, HB = 0.04, 0.03                 # pufakcha radiusi va balandligi
def lip_y(x, z):
    y = 0.9 * x * x + 0.004 * math.sin(x * 37 + 1.3) * math.cos(z * 29)
    if z < -0.085: y += 6.5 * (-0.085 - z) ** 2
    if z > 0.05: y += 7.0 * (z - 0.05) ** 2
    return y
def grid(name, xr, zr, step, fy, m, parent=None):
    nx = int(round((xr[1] - xr[0]) / step)) + 1; nz = int(round((zr[1] - zr[0]) / step)) + 1
    verts = []; faces = []
    for j in range(nz):
        z = zr[0] + (zr[1] - zr[0]) * j / (nz - 1)
        for i in range(nx):
            x = xr[0] + (xr[1] - xr[0]) * i / (nx - 1); verts.append((x, fy(x, z), z))
    for j in range(nz - 1):
        for i in range(nx - 1):
            a = j * nx + i; faces.append((a, a + 1, a + nx + 1, a + nx))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(m)
    if parent: o.parent = parent
    return o
macE = M_(empty("macE", tuple(MO)))
lip_m = mucosa_mat("lip_mucosa", nscale=60.0, zmap=True, bub=BC, rb=RB)
lip = grid("lip", (-0.36, 0.36), (-0.26, 0.105), 0.0025, lip_y, lip_m, macE)
lip.shape_key_add(name="Basis")
def add_key(o, name, fn):
    k = o.shape_key_add(name=name, from_mix=False); k.value = 0.0
    for i, v in enumerate(o.data.vertices):
        d = fn(v.co)
        if d is not None: k.data[i].co = v.co + d
    return k
def bump_fn(co):
    r = math.hypot(co.x - BC[0], co.z - BC[1]) / RB
    if r >= 1.0: return None
    return Vector((0, -HB * (1 - r * r) ** 0.75, 0))
def dent_fn(co):
    dx = (co.x - BC[0]) / 0.07; dz = (co.z - BC[1] - 0.004) / 0.011
    if abs(dx) > 1.4 or abs(dz) > 3.5: return None
    w = math.exp(-dz * dz) * max(0.0, 1 - dx ** 6)
    return Vector((0, 0.012 * w, 0))
KB = add_key(lip, "bump", bump_fn); KD = add_key(lip, "dent", dent_fn)
# milk (gum) va pastki kurak tishlar
gum_m = mucosa_mat("gum", nscale=90.0)
gb = gum_m.node_tree.nodes["Principled BSDF"]
gum_tint = gum_m.node_tree.nodes.new("ShaderNodeMix"); gum_tint.data_type = "RGBA"; gum_tint.blend_type = "MULTIPLY"
gum_tint.inputs[0].default_value = 1.0; gum_tint.inputs[7].default_value = (1.1, 0.95, 0.95, 1)
src_ = gb.inputs["Base Color"].links[0].from_socket; gum_m.node_tree.links.new(src_, gum_tint.inputs[6]); gum_m.node_tree.links.new(gum_tint.outputs[2], gb.inputs["Base Color"])
def gum_y(x, z): return 0.9 * x * x + 0.024 - 1.4 * (z - 0.09) * (0.215 - z)
M_(grid("gum", (-0.36, 0.36), (0.09, 0.215), 0.003, gum_y, gum_m, macE))
en_m = enamel_mat("enamel")
for k, (xc, w) in enumerate(((-0.0285, 0.054), (0.0285, 0.054), (-0.085, 0.058), (0.085, 0.058), (-0.146, 0.064), (0.146, 0.064),
                             (-0.208, 0.07), (0.208, 0.07))):
    zb = 0.192 if abs(xc) < 0.1 else 0.196
    t_ = tooth_mesh(f"ltooth{k}", w, 0.095 if abs(xc) < 0.12 else 0.1, 0.06, en_m, macE, edge_taper=0.45)
    t_.rotation_euler = (0, R(180), R(-math.degrees(math.atan(1.8 * xc))))      # Y atrofida 180°: qirrasi tepada, old yuzi -Y da qoladi
    t_.location = (xc, gum_y(xc, 0.2) + 0.012, zb + 0.095)
mouth_dark = M_(plane("mouth_dark", (1.6, 1.0), tuple(MO + V(0, 0.32, 0.25)), mat("mouth_dark_m", (0.05, 0.008, 0.01), 0.6), rot=(90, 0, 0)))
# so'lak tomchilari (ho'l yaltirash)
wet_m = P.water_material("saliva", (0.95, 0.97, 1.0), 0.01)
rs = random.Random(31)
for k in range(26):
    x = rs.uniform(-0.25, 0.25); z = rs.uniform(-0.08, 0.06)
    if math.hypot(x - BC[0], z - BC[1]) < RB * 1.3: continue
    r_ = rs.uniform(0.0015, 0.005)
    d_ = P.droplet(f"saliva{k}", (x, lip_y(x, z) - r_ * 0.25, z), r_, macE, wet_m, squash=0.45)
    d_.rotation_euler = (R(90), 0, 0)
# yuqori kurak tishlar (tishlash uchun): qirrasi pastda
TDIR = V(0, -0.6, 0.8)                                       # tish tanasi yo'nalishi (kameraga va tepaga)
upT = empty("upT", tuple(MO + V(BC[0], -0.25, 0.4))); upT.rotation_euler = (math.asin(0.6), 0, 0)
for k, (xc, w, h) in enumerate(((-0.044, 0.086, 0.105), (0.044, 0.086, 0.105), (-0.118, 0.066, 0.092), (0.118, 0.066, 0.092))):
    t_ = tooth_mesh(f"utooth{k}", w, h, 0.07, en_m, upT, edge_taper=0.4)
    t_.location = (xc, 0.0, 0.0 if abs(xc) < 0.1 else 0.008); t_.rotation_euler = (0, 0, R(-math.degrees(math.atan(1.2 * xc))))
ugum = grid("ugum", (-0.2, 0.2), (0.09, 0.15), 0.004, lambda x, z: 0.9 * x * x + 0.03, gum_m, upT)
TOP_PRESS = V(BC[0], lip_y(*BC), BC[1] + 0.004)              # tishlar qirrasi shilliq qavatga tegadigan nuqta
AWAY = TDIR.normalized() * 0.45
def bite_keys(f_hit, f_up_from, f_up_to, contact, press, pre=10):
    key(upT, f_hit - pre, loc=tuple(MO + TOP_PRESS + AWAY))
    key(upT, f_hit, loc=tuple(MO + contact))
    key(upT, f_hit + 3, loc=tuple(MO + press))
    key(upT, f_up_from, loc=tuple(MO + press - V(0, 0.002, 0)))
    key(upT, f_up_to, loc=tuple(MO + TOP_PRESS + AWAY))
D0, D1 = S["dent"]; PO0, PO1 = S["pop"]
key(upT, 1, loc=tuple(MO + TOP_PRESS + AWAY))
bite_keys(F_DENT, F_DENT + 12, D1 + 1, TOP_PRESS - V(0, 0.003, 0), TOP_PRESS + V(0, 0.009, 0))
bite_keys(F_POP, F_POP + 8, PO1 + 1, TOP_PRESS - V(0, HB, 0), TOP_PRESS + V(0, 0.004, 0))
def sk(k, f, v): k.value = v; k.keyframe_insert("value", frame=f)
sk(KD, 1, 0.0); sk(KD, F_DENT, 0.0); sk(KD, F_DENT + 2, 1.0); sk(KD, F_DENT + 12, 1.0); sk(KD, D1 + 1, 0.55); sk(KD, S["bubble"][0] + 30, 0.0)
B0_, B1_ = S["bubble"]; RG0, RG1 = S["regrow"]; FN0, FN1 = S["final"]
sk(KB, 1, 0.0); sk(KB, B0_ + 6, 0.0); sk(KB, B0_ + 30, 0.35); sk(KB, B0_ + 62, 0.85); sk(KB, B1_, 1.0)
sk(KB, F_POP - 1, 1.0); sk(KB, F_POP + 1, 0.85); sk(KB, F_POP + 4, 0.08); sk(KB, PO1, 0.0)
sk(KB, RG0, 0.0); sk(KB, RG0 + 6, 0.08); sk(KB, F_CHIQ, 0.6); sk(KB, RG1, 1.0); sk(KB, FN0, 1.05); sk(KB, FN1, 1.25)
def mv(f, name, v): val_key(lip_m, name, f, v)
mv(1, "bub", 0.0); mv(B0_ + 6, "bub", 0.0); mv(B0_ + 40, "bub", 0.8); mv(B1_, "bub", 1.0); mv(F_POP, "bub", 1.0); mv(F_POP + 4, "bub", 0.0)
mv(RG0 + 6, "bub", 0.0); mv(F_CHIQ, "bub", 0.8); mv(RG1, "bub", 1.0); mv(FN1, "bub", 1.0)
mv(1, "wound", 0.0); mv(F_DENT + 1, "wound", 0.0); mv(F_DENT + 4, "wound", 0.55); mv(B0_ + 20, "wound", 0.25); mv(B0_ + 50, "wound", 0.0)
mv(F_POP + 1, "wound", 0.0); mv(F_POP + 4, "wound", 1.0); mv(PO1, "wound", 0.9); mv(RG0, "wound", 0.6); mv(F_CHIQ, "wound", 0.15); mv(RG1, "wound", 0.0)
# yorilganda suyuqlik sachraydi
fluid_m = mat("mucus_fl", (0.75, 0.85, 1.0), 0.02, trans=0.85, coat=1.0, emit=0.25, emit_col=(0.5, 0.7, 1.0))
BCW = V(BC[0], lip_y(*BC) - HB, BC[1])
rf = random.Random(17)
spl = M_(empty("splash", (0, 0, 0), macE))
for k in range(26):
    o = sphere(f"spl{k}", rf.uniform(0.0025, 0.007), tuple(BCW), fluid_m, sub=2, parent=spl)
    v_ = Vector((rf.uniform(-0.8, 0.8), rf.uniform(-1.4, -0.5), rf.uniform(-0.3, 1.0))).normalized() * rf.uniform(0.004, 0.011)
    f0 = F_POP + rf.randint(0, 3)
    key(o, 1, loc=tuple(BCW), scale=0.001); key(o, f0, loc=tuple(BCW), scale=0.001)
    for j in range(1, 16):
        key(o, f0 + j, loc=tuple(BCW + v_ * j + V(0, 0, -0.00035 * j * j)), scale=1.0)
    interp(o, "LINEAR", "location")
for o in mac_objs: vis(o, MACR)
vis(spl, [S["pop"]])                      # umumiy vis'dan KEYIN (recursive vis bolalarnikini qayta yozadi)
vis(upT, [(D0 - 8, D1), (PO0, PO1)])

# ======================================================================
# 4) KESIM: lab to'qimasining bloki (sxematik masshtab). Mahalliy: old kesim yuzi y = -0.6 (kamera -Y tomonda),
#    epiteliy usti z = 0; biriktiruvchi (shaffof) qavat z -0.55..-0.06; mushak z -0.9..-0.55
# ======================================================================
CO = V(40.0, 0.0, 1.0)
cutE = empty("cutE", tuple(CO))
cut_objs = [cutE]
def C_(o):
    if o.parent is None: o.parent = cutE
    return o
BX, BY = 1.0, 0.6
G_S = V(0.06, -0.42, -0.33)                       # asosiy bez (old yuzga yaqin)
Q = V(0.13, -0.27, 0.0)                           # uning naychasi teshigi (sirtda)
K = (G_S + V(0, 0, 0.06)).lerp(Q, 0.4)            # naycha uziladigan nuqta
DOME_R, DOME_H = 0.36, 0.2
def epi_z(x, y): return 0.006 * math.sin(x * 9 + 0.5) * math.cos(y * 7)
epi_m = mucosa_mat("epi_top", nscale=9.0, sss_scale=0.02)
epi_cut = bpy.data.materials.new("epi_cut"); epi_cut.use_nodes = True
N = epi_cut.node_tree.nodes; L = epi_cut.node_tree.links; _b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); sp_ = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp_.inputs[0])
rmp = N.new("ShaderNodeValToRGB"); L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", sp_.outputs["Z"], 0.06), 16.6), rmp.inputs[0])
E_ = rmp.color_ramp.elements; E_[0].position, E_[0].color = 0.0, (0.55, 0.12, 0.2, 1); E_[1].position, E_[1].color = 1.0, (0.95, 0.62, 0.62, 1)
e_ = E_.new(0.18); e_.color = (0.75, 0.25, 0.32, 1)
cvn = N.new("ShaderNodeTexVoronoi"); cvn.inputs["Scale"].default_value = 90.0; L.new(tc.outputs["Object"], cvn.inputs["Vector"])
L.new(mixc(N, L, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", cvn.outputs["Distance"], 0.08), 0.35), rmp.outputs[0], (0.4, 0.08, 0.15)), _b.inputs["Base Color"])
_b.inputs["Roughness"].default_value = 0.35; _b.inputs["Coat Weight"].default_value = 0.5; _b.inputs["Subsurface Weight"].default_value = 0.2
_b.inputs["Subsurface Scale"].default_value = 0.01
epi = grid("epi", (-BX, BX), (-BY, BY), 0.01, lambda x, y: 0.0, epi_m)
for v in epi.data.vertices: v.co = (v.co.x, v.co.z, epi_z(v.co.x, v.co.z))     # grid() XZ tekisligida yasaydi: XY ga o'tkazamiz
epi.data.update(); epi.data.materials.append(epi_cut); C_(epi)
eso = epi.modifiers.new("solid", "SOLIDIFY"); eso.thickness = 0.06; eso.offset = -1.0; eso.material_offset_rim = 1; eso.use_rim = True
epi.shape_key_add(name="Basis")
def epi_dent(co):
    dx = (co.x - Q.x) / 0.3; dy = (co.y - Q.y) / 0.14
    if abs(dx) > 1.3 or abs(dy) > 3.2: return None
    w = math.exp(-dy * dy) * max(0.0, 1 - dx ** 6)
    return Vector((0, 0, -0.12 * w))
def epi_dome(co):
    r = math.hypot(co.x - Q.x, co.y - Q.y) / DOME_R
    if r >= 1.25: return None
    h = DOME_H * (math.cos(min(1.0, r / 1.25) * math.pi) * 0.5 + 0.5) ** 1.1
    return Vector((0, 0, h))
EK_D = add_key(epi, "dent", epi_dent); EK_O = add_key(epi, "dome", epi_dome)
# biriktiruvchi qavat (shaffof jele) va mushak
lam_m = bpy.data.materials.new("lamina"); lam_m.use_nodes = True
N = lam_m.node_tree.nodes; L = lam_m.node_tree.links; _b = N["Principled BSDF"]; out_ = N["Material Output"]
tc = N.new("ShaderNodeTexCoord"); lnz = N.new("ShaderNodeTexNoise"); lnz.inputs["Scale"].default_value = 6.0; lnz.inputs["Detail"].default_value = 5
L.new(tc.outputs["Object"], lnz.inputs["Vector"])
L.new(mixc(N, L, lnz.outputs["Fac"], (0.95, 0.72, 0.7), (1.0, 0.85, 0.8)), _b.inputs["Base Color"])
_b.inputs["Roughness"].default_value = 0.3; _b.inputs["Emission Color"].default_value = (1.0, 0.6, 0.6, 1); _b.inputs["Emission Strength"].default_value = 0.05
_b.inputs["Coat Weight"].default_value = 0.4
trn = N.new("ShaderNodeBsdfTransparent"); mxs = N.new("ShaderNodeMixShader"); mxs.inputs[0].default_value = 0.28
L.new(trn.outputs[0], mxs.inputs[1]); L.new(_b.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], out_.inputs["Surface"])
C_(box("lamina", (2 * BX - 0.004, 2 * BY - 0.004, 0.49), (0, 0, -0.305), lam_m))
mus_m = bpy.data.materials.new("muscle"); mus_m.use_nodes = True
N = mus_m.node_tree.nodes; L = mus_m.node_tree.links; _b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); mw = N.new("ShaderNodeTexWave"); mw.bands_direction = "Z"; mw.inputs["Scale"].default_value = 70.0
mw.inputs["Distortion"].default_value = 3.0; mw.inputs["Detail"].default_value = 3.0; L.new(tc.outputs["Object"], mw.inputs["Vector"])
mvo = N.new("ShaderNodeTexVoronoi"); mvo.feature = "DISTANCE_TO_EDGE"; mvo.inputs["Scale"].default_value = 22.0; L.new(tc.outputs["Object"], mvo.inputs["Vector"])
mc_ = mixc(N, L, mw.outputs["Fac"], (0.42, 0.04, 0.05), (0.66, 0.1, 0.1))
mc_ = mixc(N, L, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", mvo.outputs["Distance"], 0.012), 0.5), mc_, (0.85, 0.62, 0.58))
L.new(mc_, _b.inputs["Base Color"]); _b.inputs["Roughness"].default_value = 0.35; _b.inputs["Coat Weight"].default_value = 0.6
_b.inputs["Subsurface Weight"].default_value = 0.2; _b.inputs["Subsurface Scale"].default_value = 0.02
mbp = N.new("ShaderNodeBump"); mbp.inputs["Strength"].default_value = 0.4; L.new(mw.outputs["Fac"], mbp.inputs["Height"]); L.new(mbp.outputs[0], _b.inputs["Normal"])
C_(box("muscle", (2 * BX, 2 * BY, 0.35), (0, 0, -0.725), mus_m))
# kapillyarlar
cap_m = mat("capillary", (0.55, 0.03, 0.04), 0.3, emit=0.3, emit_col=(0.8, 0.05, 0.05), coat=0.5)
rc = random.Random(41)
for k in range(10):
    y0 = rc.uniform(-0.55, 0.55); z0 = rc.uniform(-0.5, -0.12)
    pts = [(-BX + 0.01 + (2 * BX - 0.02) * t / 6, y0 + rc.uniform(-0.08, 0.08), z0 + rc.uniform(-0.05, 0.05)) for t in range(7)]
    C_(P.tube(f"cap{k}", pts, rc.uniform(0.006, 0.011), cap_m, cutE))
# so'lak bezlari: bo'lakchalar (acinus sharlari) + naychalar
gl_m = bpy.data.materials.new("gland"); gl_m.use_nodes = True
N = gl_m.node_tree.nodes; L = gl_m.node_tree.links; _b = N["Principled BSDF"]
_b.inputs["Base Color"].default_value = (0.98, 0.8, 0.55, 1); _b.inputs["Roughness"].default_value = 0.3; _b.inputs["Coat Weight"].default_value = 0.6
_b.inputs["Subsurface Weight"].default_value = 0.5; _b.inputs["Subsurface Scale"].default_value = 0.01
oi = N.new("ShaderNodeObjectInfo"); sep_c = N.new("ShaderNodeSeparateColor"); L.new(oi.outputs["Color"], sep_c.inputs[0])
_b.inputs["Emission Color"].default_value = (1.0, 0.75, 0.3, 1)
L.new(P.math_n(N, L, "ADD", 0.08, P.math_n(N, L, "MULTIPLY", sep_c.outputs["Red"], 3.5)), _b.inputs["Emission Strength"])
duct_m = train_mat("duct", col=(0.95, 0.88, 0.75), pcol=(0.6, 0.85, 1.0))
sduct_m = train_mat("sduct", col=(0.95, 0.88, 0.75), pcol=(0.6, 0.85, 1.0))
def lobule(name, c, n, rr, seed):
    r_ = random.Random(seed); bm = bmesh.new()
    pts = [Vector((0, 0, 0))]
    while len(pts) < n:
        p = Vector((r_.uniform(-1, 1), r_.uniform(-1, 1), r_.uniform(-0.8, 0.8))) * rr
        if p.length <= rr: pts.append(p)
    for p in pts:
        rad = r_.uniform(0.38, 0.55) * rr
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rad, matrix=Matrix.Translation(p))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(gl_m); o.location = c; C_(o)
    o.color = (0, 0, 0, 1)
    return o
rg = random.Random(53)
GL_POS = [G_S]
while len(GL_POS) < 64:
    p = V(rg.uniform(-0.92, 0.92), rg.uniform(-0.52, 0.5), rg.uniform(-0.47, -0.2))
    if all((p - q).length > 0.19 for q in GL_POS): GL_POS.append(p)
LOBS = []; DUCTS = []; DROPS = []
drop_m = mat("saliva_drop", (0.85, 0.93, 1.0), 0.02, trans=0.9, coat=1.0, emit=0.15, emit_col=(0.5, 0.75, 1.0))
for i, c in enumerate(GL_POS):
    main = i == 0
    o = lobule(f"lob{i}", tuple(c), 14 if main else rg.randint(8, 13), 0.075 if main else rg.uniform(0.05, 0.072), 100 + i)
    LOBS.append(o)
    top = c + V(0, 0, 0.06)
    pore = Q if main else V(c.x + rg.uniform(-0.06, 0.06), c.y + rg.uniform(-0.06, 0.06), 0.0)
    mid1 = top.lerp(pore, 0.35) + V(rg.uniform(-0.025, 0.025), rg.uniform(-0.025, 0.025), 0)
    mid2 = top.lerp(pore, 0.7) + V(rg.uniform(-0.02, 0.02), rg.uniform(-0.02, 0.02), 0)
    if main:
        lo = [tuple(top), tuple(top.lerp(K, 0.5) + V(0.004, 0, 0)), tuple(K)]
        up = [tuple(K), tuple(K.lerp(Q, 0.5) + V(0.003, 0.002, 0)), tuple(Q + V(0, 0, 0.006))]
        DLO = C_(P.tube("sduct_lo", lo, 0.0115, sduct_m, cutE)); DUP = C_(P.tube("sduct_up", up, 0.0115, sduct_m, cutE))
    else:
        DUCTS.append(C_(P.tube(f"duct{i}", [tuple(top), tuple(mid1), tuple(mid2), tuple(pore + V(0, 0, 0.006))], rg.uniform(0.006, 0.009), duct_m, cutE)))
    d = sphere(f"pdrop{i}", 0.016, tuple(pore + V(0, 0, epi_z(pore.x, pore.y) + 0.008)), drop_m, scale=(1, 1, 0.7), sub=2); C_(d); DROPS.append(d)
CU0 = S["dive"][0]
for i, d in enumerate(DROPS):
    ph = rg.randint(0, 40)
    d.scale = (0.01,) * 3; d.keyframe_insert("scale", frame=1)
    if i == 0: continue
    for f in range(CU0 - 40 + ph, END + 1, 44):
        for df, s in ((0, 0.01), (22, 0.8), (36, 1.0), (40, 0.01)):
            d.scale = (s, s, s * 0.7); d.keyframe_insert("scale", frame=f + df)
DROPS[0].scale = (0.01,) * 3; DROPS[0].keyframe_insert("scale", frame=1)
for f in range(CU0 - 30, F_UZ - 20, 40):
    for df, s in ((0, 0.01), (20, 0.9), (34, 1.0), (38, 0.01)):
        DROPS[0].scale = (s, s, s * 0.7); DROPS[0].keyframe_insert("scale", frame=f + df)
DROPS[0].scale = (0.01,) * 3; DROPS[0].keyframe_insert("scale", frame=F_UZ - 20)
# so'lak impulslari: naychalar bo'ylab bezdan teshikka (phase oshadi)
for m in (duct_m, sduct_m):
    val_key(m, "count", 1, 3.0); val_key(m, "amp", 1, 6.0); val_key(m, "glow", 1, 0.25)
    val_key(m, "phase", 1, 0.0); val_key(m, "phase", END + 1, (END + 1) / 30.0)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        if "phase" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# "yuzlab bezlar": chapdan o'ngga to'lqin bo'lib yonadi; asosiy bez "birining" da sariq yonadi
GLA0, GLA1 = S["glands"]
order = sorted(range(1, len(LOBS)), key=lambda i: GL_POS[i].x + 0.3 * GL_POS[i].y)
def ckey_(o, f, v): o.color = (v, 0, 0, 1); o.keyframe_insert("color", frame=f)
for rank, i in enumerate(order):
    o = LOBS[i]; f0 = GLA0 + 6 + int(rank * 1.1)
    ckey_(o, 1, 0.0); ckey_(o, f0, 0.0); ckey_(o, f0 + 4, 1.0); ckey_(o, f0 + 26, 0.12); ckey_(o, GLA1, 0.1); ckey_(o, GLA1 + 1, 0.0)
G0 = LOBS[0]
ckey_(G0, 1, 0.0); ckey_(G0, GLA0 + 4, 0.0); ckey_(G0, GLA0 + 8, 1.0); ckey_(G0, GLA0 + 30, 0.12); ckey_(G0, F_BIR - 3, 0.12)
ckey_(G0, F_BIR + 2, 1.6)
val_key(sduct_m, "glow", F_NAY - 8, 0.25); val_key(sduct_m, "glow", F_NAY, 2.5); val_key(sduct_m, "amp", F_NAY, 10.0)
# bez pulsatsiyasi (uzilgandan keyin ham so'lak ishlab chiqaradi)
G0.scale = (1, 1, 1); G0.keyframe_insert("scale", frame=1)
PU0, PU1 = S["pump"]; SW0, SW1 = S["swell"]
f = F_UZ + 4
while f < SW1:
    ckey_(G0, f, 1.8); ckey_(G0, f + 6, 0.9)
    G0.scale = (1.07,) * 3; G0.keyframe_insert("scale", frame=f); G0.scale = (0.97,) * 3; G0.keyframe_insert("scale", frame=f + 6)
    f += 12
# tish (kesimdagi): yuqoridan tushib bosadi
tc_m = enamel_mat("enamel_cut")
toothE = empty("toothE", (0, 0, 0)); C_(toothE)
tth = tooth_mesh("cut_tooth", 0.62, 1.45, 0.34, tc_m, toothE, edge_taper=0.32)
SN0, SN1 = S["snap"]
def tkey(f, z): key(toothE, f, loc=(Q.x, Q.y + 0.02, z))
tkey(1, 1.6); tkey(SN0, 1.3); tkey(F_UZ - 5, 0.01); tkey(F_UZ, -0.09); tkey(F_EZ - 4, -0.085); tkey(F_EZ, -0.125); tkey(SN1 - 6, -0.12); tkey(SN1 + 1, 0.7)
LATE = [lambda: vis(toothE, [S["snap"]])]
sk(EK_D, 1, 0.0); sk(EK_D, F_UZ - 5, 0.0); sk(EK_D, F_UZ, 0.78); sk(EK_D, F_EZ - 4, 0.75); sk(EK_D, F_EZ, 1.05); sk(EK_D, SN1 - 6, 1.0)
sk(EK_D, SN1 + 1, 0.15); sk(EK_D, PU0 + 30, 0.0)
# naycha uziladi: yuqori bo'lagi tepaga, pastki bo'lagi pastga siltanadi; ezilganda yuqori bo'lak yassilanadi
for o, d in ((DUP, V(0.012, 0.004, 0.03)), (DLO, V(-0.008, 0.0, -0.018))):
    key(o, 1, loc=(0, 0, 0)); key(o, F_UZ - 1, loc=(0, 0, 0)); key(o, F_UZ + 2, loc=tuple(d * 1.3)); key(o, F_UZ + 8, loc=tuple(d))
P.tube_r(DUP, 1, 0.0115); P.tube_r(DUP, F_EZ - 1, 0.0115); P.tube_r(DUP, F_EZ + 3, 0.0045)
P.tube_r(DLO, 1, 0.0115)
sparks_m = mat("snap_spark", (1.0, 0.15, 0.08), 0.5, emit=3.0)
rsp = random.Random(9)
for k in range(18):
    o = sphere(f"snapsp{k}", rsp.uniform(0.004, 0.009), tuple(K + V(rsp.uniform(-0.03, 0.03), rsp.uniform(-0.03, 0.03), rsp.uniform(-0.02, 0.03))), sparks_m, sub=1)
    C_(o); f0 = F_UZ + rsp.randint(0, 3)
    v_ = Vector((rsp.uniform(-1, 1), rsp.uniform(-1, 0.3), rsp.uniform(-0.5, 1))).normalized() * 0.006
    key(o, f0, loc=tuple(o.location)); key(o, f0 + 8, loc=tuple(o.location + v_ * 8))
    LATE.append(lambda o=o, fr=list(range(f0, f0 + rsp.randint(5, 9))): (vis(o, [], recursive=False), frames_vis(o, fr)))
# suyuqlik "xaltasi" (mukotsele): uzilgan uchdan to'qimaga yig'iladi, epiteliyni gumbaz qilib ko'taradi
pool_m = bpy.data.materials.new("pool"); pool_m.use_nodes = True
N = pool_m.node_tree.nodes; L = pool_m.node_tree.links; _b = N["Principled BSDF"]; out_ = N["Material Output"]
_b.inputs["Base Color"].default_value = (0.72, 0.84, 1.0, 1); _b.inputs["Roughness"].default_value = 0.08; _b.inputs["Coat Weight"].default_value = 1.0
_b.inputs["Transmission Weight"].default_value = 0.5; _b.inputs["Emission Color"].default_value = (0.45, 0.7, 1.0, 1)
lwp = N.new("ShaderNodeLayerWeight"); lwp.inputs["Blend"].default_value = 0.4
L.new(P.math_n(N, L, "ADD", 0.25, P.math_n(N, L, "MULTIPLY", lwp.outputs["Facing"], 2.2)), _b.inputs["Emission Strength"])
trn = N.new("ShaderNodeBsdfTransparent"); mxs = N.new("ShaderNodeMixShader")
L.new(P.math_n(N, L, "ADD", 0.45, P.math_n(N, L, "MULTIPLY", lwp.outputs["Facing"], 0.5), clamp=True), mxs.inputs[0])
L.new(trn.outputs[0], mxs.inputs[1]); L.new(_b.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], out_.inputs["Surface"])
pool = sphere("pool", 1.0, (0, 0, 0), pool_m, sub=5); C_(pool)
pdisp = pool.modifiers.new("d", "DISPLACE"); _pt = bpy.data.textures.new("pool_t", "CLOUDS"); _pt.noise_scale = 0.6; pdisp.texture = _pt; pdisp.strength = 0.08
PC_END = V(Q.x - 0.01, Q.y - 0.05, -0.045)
def pkey(f, k):
    p = K.lerp(PC_END, min(1.0, k * 1.4)); key(pool, f, loc=tuple(p), scale=(0.3 * k + 0.001, 0.27 * k + 0.001, 0.2 * k + 0.001))
pkey(1, 0.0); pkey(F_UZ + 10, 0.0); pkey(PU0 + 10, 0.08); pkey(PU1, 0.32); pkey(F_CHQM, 0.62); pkey(SW1, 1.0)
sk(EK_O, 1, 0.0); sk(EK_O, PU0 + 20, 0.0); sk(EK_O, PU1, 0.22); sk(EK_O, F_CHQM, 0.6); sk(EK_O, SW1, 1.0)
# uzilgan uchdan suyuqlik tomchilari xaltaga oqadi
rl = random.Random(77)
leak = empty("leak", (0, 0, 0)); C_(leak)
KL = K + V(-0.008, 0.0, -0.018)
for k in range(30):
    o = sphere(f"leak{k}", rl.uniform(0.008, 0.014), tuple(KL), pool_m, sub=2, parent=leak)
    f0 = F_UZ + 8 + k * 5 + rl.randint(0, 2)
    if f0 > SW1: break
    tgt = KL.lerp(PC_END, 0.3 + 0.5 * min(1, (f0 - F_UZ) / 150)) + V(rl.uniform(-0.04, 0.04), rl.uniform(-0.03, 0.03), rl.uniform(-0.02, 0.03))
    key(o, 1, loc=tuple(KL), scale=0.001); key(o, f0, loc=tuple(KL), scale=0.001); key(o, f0 + 2, loc=tuple(KL), scale=1.0)
    key(o, f0 + 14, loc=tuple(tgt), scale=0.9); key(o, f0 + 16, loc=tuple(tgt), scale=0.001)
for o in cut_objs: vis(o, CUTR)
vis(leak, [(PU0, SW1)]); vis(pool, [(F_UZ + 8, SW1)])
for fn in LATE: fn()

for o in room_objs: vis(o, ROOM)

# ======================================================================
# 5) KAMERALAR
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
def M(x, y, z): return MO + V(x, y, z)
BCM = M(BC[0], lip_y(*BC), BC[1])
def C(x, y, z): return CO + V(x, y, z)
# 1 ILGAK: poldan, keng ob'ektiv, tez push-in
H0, H1 = S["hook"]; FP = FACE["hook"]
c = abs_cam("hook", [(H0, FP + V(0.7, -0.72, -0.5)), (H1, FP + V(0.36, -0.5, -0.28))],
            [(H0, FP + V(0, -0.05, -0.12)), (H1, FP + V(0, -0.02, -0.05))], 16, 2.8)
lens_keys(c, [(H0, 15), (H1, 19)])
# 2 yuzga yaqin: tishlaydi, siltanadi
F0_, F1_ = S["face"]
c = rel_cam("face", faceT, 40, 2.0, [(F0_, V(0.3, -0.36, -0.04)), (F1_, V(0.2, -0.3, -0.01))])
shake(c, 66, 80, 0.008, seed=2)
# 3 makro: tishlar qisadi
c = abs_cam("dent", [(D0, BCM + V(0.14, -0.5, 0.1)), (F_DENT, BCM + V(0.1, -0.42, 0.07)), (D1, BCM + V(0.07, -0.36, 0.05))],
            [(D0, BCM + V(0, 0, 0.01)), (D1, BCM + V(0, 0, 0.0))], 34, 9.0)
shake(c, F_DENT, F_DENT + 12, 0.006, seed=3)
# 4 pufakcha o'sadi: keng makro -> aylanma -> crash zoom
c = abs_cam("bubble", [(B0_, BCM + V(-0.2, -0.6, 0.16)), (F_SEZ - 1, BCM + V(0.08, -0.5, 0.06)), (F_SEZ + 2, BCM + V(0.04, -0.24, 0.02)),
                       (B1_, BCM + V(0.045, -0.22, 0.016))],
            [(B0_, BCM + V(0.0, 0, 0.06)), (F_SEZ - 1, BCM + V(0, 0, 0.01)), (B1_, BCM)], 30, 10.0)
lens_keys(c, [(B0_, 26), (F_SEZ - 1, 30), (F_SEZ + 2, 44), (B1_, 46)]); shake(c, F_SEZ, F_SEZ + 10, 0.005, seed=4)
# 5 tishlab yoradi
c = abs_cam("pop", [(PO0, BCM + V(0.26, -0.48, 0.12)), (F_POP, BCM + V(0.19, -0.4, 0.07)), (PO1, BCM + V(0.15, -0.34, 0.04))],
            [(PO0, BCM + V(0, 0, 0.03)), (PO1, BCM + V(0, -0.01, 0.0))], 32, 10.0)
shake(c, F_POP, F_POP + 14, 0.008, seed=5)
# 6 timelapse: yondan, yonlama siljish (soat, deraza nuri, Megan)
FD = FACE["days"]
c = abs_cam("days", [(DA0, FD + V(1.25, -0.55, 0.15)), (DA1, FD + V(1.25, 0.15, 0.25))],
            [(DA0, FD + V(-1.2, -0.2, 0.25)), (DA1, FD + V(-1.2, -0.05, 0.3))], 20, 5.6)
# 7 qayta o'sadi: crash zoom "chiqib"
c = abs_cam("regrow", [(RG0, BCM + V(-0.18, -0.5, -0.08)), (F_CHIQ - 1, BCM + V(-0.12, -0.42, -0.03)), (F_CHIQ + 2, BCM + V(-0.05, -0.22, 0.0)),
                       (RG1, BCM + V(-0.045, -0.2, 0.005))],
            [(RG0, BCM + V(0, 0, 0.0)), (RG1, BCM + V(0, -0.01, 0.0))], 30, 10.0)
lens_keys(c, [(RG0, 28), (F_CHIQ - 1, 32), (F_CHIQ + 2, 46), (RG1, 48)]); shake(c, F_CHIQ, F_CHIQ + 10, 0.005, seed=7)
# 8 kesimga sho'ng'ish: sirt ustidan pastga va old yuzga
DV0, DV1 = S["dive"]
c = abs_cam("dive", [(DV0, C(0.25, -0.2, 0.55)), (DV0 + 22, C(0.6, -1.3, 0.45)), (DV1, C(0.9, -2.3, 0.15))],
            [(DV0, C(0.15, -0.3, 0.0)), (DV0 + 22, C(0.1, -0.55, -0.15)), (DV1, C(0.0, -0.5, -0.32))], 24, 6.0)
lens_keys(c, [(DV0, 30), (DV1, 26)])
# 9 bezlar: yaqin aylanma -> "yuzlab" da keng plan
c = abs_cam("glands", [(GLA0, C(0.55, -1.05, -0.12)), (F_YUZ - 2, C(0.15, -1.0, -0.05)), (F_YUZ + 14, C(1.2, -2.6, 0.7)), (GLA1, C(1.7, -3.0, 1.0))],
            [(GLA0, C(0.0, -0.4, -0.32)), (F_YUZ - 2, C(-0.1, -0.35, -0.3)), (F_YUZ + 14, C(0.0, -0.1, -0.55)), (GLA1, C(0.0, 0.0, -0.5))], 26, 8.0)
lens_keys(c, [(GLA0, 30), (F_YUZ - 2, 28), (F_YUZ + 14, 22), (GLA1, 22)])
# 10 yana tishlaydi: past burchak, qo'l kamerasi
BI0, BI1 = S["bite2"]; FB = FACE["bite2"]
c = abs_cam("bite2", [(BI0, FB + V(0.62, -0.55, -0.4)), (BI1, FB + V(0.36, -0.42, -0.28))], [(BI0, FB + V(0, -0.04, -0.06)), (BI1, FB + V(0, -0.02, -0.03))], 17, 2.8)
shake(c, BI0, BI1, 0.01, seed=10, decay=False)
# 11 bitta bez va uning naychasi: aylanma
DU0, DU1 = S["duct"]
c = abs_cam("duct", [(DU0, C(G_S.x + 0.6, -1.15, G_S.z + 0.1)), (DU1, C(G_S.x - 0.25, -1.1, G_S.z + 0.32))],
            [(DU0, C(G_S.x, G_S.y, G_S.z)), (F_NAY, C(K.x, K.y, K.z)), (DU1, C(K.x, K.y, -0.1))], 30, 8.0)
# 12 tish bosadi, naycha uziladi: crash zoom
c = abs_cam("snap", [(SN0, C(Q.x + 0.95, -1.55, 0.3)), (F_UZ - 1, C(Q.x + 0.75, -1.3, 0.12)), (F_UZ + 2, C(Q.x + 0.42, -0.95, 0.0)), (SN1, C(Q.x + 0.38, -0.92, -0.02))],
            [(SN0, C(Q.x, Q.y, 0.05)), (F_UZ - 1, C(K.x, K.y, -0.08)), (SN1, C(K.x, K.y, -0.14))], 24, 8.0)
lens_keys(c, [(SN0, 22), (F_UZ - 1, 26), (F_UZ + 2, 40), (SN1, 42)]); shake(c, F_UZ, F_UZ + 12, 0.012, seed=12); shake(c, F_EZ, F_EZ + 8, 0.008, seed=13)
# 13 bez ishlashda davom etadi: push-in
c = abs_cam("pump", [(PU0, C(G_S.x + 0.42, -1.0, G_S.z + 0.05)), (PU1, C(G_S.x + 0.22, -0.82, G_S.z + 0.1))],
            [(PU0, C(G_S.x + 0.02, G_S.y, G_S.z + 0.08)), (PU1, C(K.x, K.y, K.z - 0.04))], 32, 8.0)
# 14 xalta o'sadi, sirt gumbaz bo'ladi: yondan
c = abs_cam("swell", [(SW0, C(Q.x + 1.15, -1.35, 0.12)), (SW1, C(Q.x + 0.8, -1.4, 0.38))],
            [(SW0, C(Q.x, Q.y, -0.12)), (SW1, C(Q.x, Q.y, -0.02))], 28, 8.0)
# 15 makro: katta pufakcha yana shishadi
c = abs_cam("final", [(FN0, BCM + V(0.1, -0.48, 0.1)), (FN1, BCM + V(0.06, -0.32, 0.06))], [(FN0, BCM), (FN1, BCM + V(0, -0.015, 0))], 34, 10.0)
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
# 6) YORUG'LIK VA FON
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
WORLD = {"room": (1.0, (0.0, 0.0, 0.0), 0.0), "mac": (0.0, (0.012, 0.004, 0.004), 1.0), "cut": (0.0, (0.008, 0.012, 0.026), 1.0)}
def world_of(n): return "room" if n in ROOMN else "mac" if n in MACN else "cut"
for f, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
# timelapse: 2 kun-tun sikli (osmon yorqinligi)
def daylight(f):
    t = (f - DA0) / (DA1 + 1 - DA0) * 2.0
    return max(0.0, math.sin(2 * math.pi * (t + 0.15)))
for f in range(DA0, DA1 + 1):
    bg_env.inputs[1].default_value = 0.03 + 0.97 * daylight(f); bg_env.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
# oshxona: quyosh (derazadan), shift yorug'ligi, yuz uchun yumshoq yorug'lik
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.93, 0.82)
def sun_dir(az, el):
    d = Vector((math.sin(R(az)) * math.cos(R(el)), math.cos(R(az)) * math.cos(R(el)), -math.sin(R(el))))
    return d.to_track_quat("-Z", "Y").to_euler()
sun.rotation_euler = sun_dir(-20, 38)
sun_keys = lights_for(ROOM, 4.0)
for f, e in sun_keys: sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
sun.keyframe_insert("rotation_euler", frame=1)
for f in range(DA0, DA1 + 1):
    t = ((f - DA0) / (DA1 + 1 - DA0) * 2.0 + 0.15) % 1.0
    sun.rotation_euler = sun_dir(-75 + 150 * min(1.0, t * 2), 12 + 40 * math.sin(math.pi * min(1.0, t * 2)))
    sun.keyframe_insert("rotation_euler", frame=f)
    sun.data.energy = 5.0 * daylight(f); sun.data.keyframe_insert("energy", frame=f)
sun.rotation_euler = sun_dir(-20, 38); sun.keyframe_insert("rotation_euler", frame=DA1 + 1)
sun.data.energy = 4.0; sun.data.keyframe_insert("energy", frame=DA1 + 1)
interp(sun.data, "CONSTANT"); interp(sun, "CONSTANT")
night_keys = lights_for(ROOM, 0.0)
for f in range(DA0, DA1 + 1): night_keys.append((f, 30.0 * (1 - daylight(f)) ** 2))
night_keys.append((DA1 + 1, 0.0)); night_keys.sort()
area("ceil_fill", (0.0, 0.0, 2.6), 2.0, (1.0, 0.92, 0.82), lights_for(ROOM, 22.0), target=empty("cfT", (0, 0, 0)))
area("night_lamp", (0.6, -0.9, 2.5), 0.6, (1.0, 0.72, 0.42), night_keys, target=FT)
area("win_fill", (0.6, Y0 + 0.25, 1.6), 1.6, (0.85, 0.92, 1.0), lights_for(ROOM, 60.0), target=FT)
area("face_fill", (1.35, -1.05, 1.45), 0.5, (1.0, 0.95, 0.9), lights_for(rng("face", "bite2", "hook"), 14.0), target=FT)
area("rim_back", (-0.4, 0.6, 2.0), 0.8, (1.0, 0.9, 0.8), lights_for(ROOM, 25.0), target=FT)
# makro
MT = empty("macroT", tuple(BCM))
area("M_key", tuple(BCM + V(-0.25, -0.35, 0.3)), 0.25, (1.0, 0.95, 0.9), lights_for(MACR, 14.0), target=MT)
area("M_fill", tuple(BCM + V(0.3, -0.3, -0.08)), 0.3, (0.9, 0.93, 1.0), lights_for(MACR, 6.0), target=MT)
area("M_top", tuple(BCM + V(0.02, -0.15, 0.35)), 0.15, (1.0, 0.97, 0.92), lights_for(MACR, 6.0), target=MT)
area("M_ring", tuple(BCM + V(0.0, -0.45, 0.02)), 0.12, (1.0, 1.0, 1.0), lights_for(MACR, 5.0), target=MT)
# kesim
CT_ = empty("cutT", tuple(C(0, -0.3, -0.25)))
area("C_key", tuple(C(1.4, -2.0, 1.6)), 1.2, (1.0, 0.95, 0.9), lights_for(CUTR, 260.0), target=CT_)
area("C_fill", tuple(C(-1.6, -1.6, 0.3)), 1.0, (0.85, 0.9, 1.0), lights_for(CUTR, 90.0), target=CT_)
area("C_rim", tuple(C(-0.5, 1.6, 1.4)), 1.0, (0.4, 0.65, 1.0), lights_for(CUTR, 160.0), target=CT_)
area("C_under", tuple(C(0.3, -1.4, -1.4)), 0.8, (1.0, 0.75, 0.6), lights_for(CUTR, 50.0), target=CT_)

# ======================================================================
# 7) RENDER
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
