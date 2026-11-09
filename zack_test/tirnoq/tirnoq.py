# Tirnoq ostidagi qon (subungual gematoma) — Zack D. Films uslubida 41.1 s video (987 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, yordamchilar zack_test/yelim/yelim.py dan; barmoq/quvur/impuls: zack_test/burish/parts.py
# Assetlar: zack_test/tools/get_tirnoq.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/tirnoq/tirnoq.py --render
# Sinov:  FRAMES=40,120,250,400,560,800,850 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 987
sc.frame_start, sc.frame_end = 1, END
V = lambda *a: Vector(a)

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "door"), (53, "hammer"), (91, "blood"), (173, "face"), (216, "xray"), (276, "tight"), (334, "press"),
         (433, "clinic"), (501, "heat"), (576, "touch"), (621, "nonerve"), (680, "calm"), (728, "melt"), (816, "fountain"),
         (873, "release"), (931, "relief")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
HALLN = ("door", "face"); MWN = ("hammer", "blood"); MCN = ("heat", "touch", "melt", "fountain")
CUTN = ("tight", "press", "nonerve", "release"); CLN = ("clinic", "calm", "relief"); XRN = ("xray",)
HALL_R = rng(*HALLN); MW_R = rng(*MWN); MC_R = rng(*MCN); CUT_R = rng(*CUTN); CL_R = rng(*CLN); XR_R = rng(*XRN)
F_SLAM = 40          # "qisib" — eshik yopiladi
F_HIT = 78           # "urib" — bolg'a tushadi
F_TOUCH = 611        # "bosadi" — cho'g' uch tirnoqqa tegadi
F_PIERCE = 793       # "teshadi"
F_OUT = 818          # uch chiqariladi
F_JET = 826          # favvora
BEATS_X = (222, 242, 262)                       # rentgen: yurak urishlari
BEATS = list(range(96, 172, 19)) + [180, 199] + list(BEATS_X)

# ---------------- yordamchilar (yelim.py dan) ----------------
empty = P.empty
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale if isinstance(scale, (tuple, list, Vector)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)

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
    if m: o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3
        for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def uvsphere(name, loc, scale, m, parent=None, seg=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def import_gltf(path, loc, rot=(0, 0, 0), scale=1.0, parent=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc, parent)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler = [R(a) for a in rot]; root.scale = scale if isinstance(scale, tuple) else (scale,) * 3
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

def area(name, loc, size, col, keys, target=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    l.visible_camera = cam_vis
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, const=True, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc; l.visible_camera = False
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)

def boolean_cut(o, cutter, m_cut=None):
    """kesim: cutter (dunyo koordinatasida, ota-onaga bog'lashdan OLDIN) — yangi yuzlar cutter materialini oladi"""
    md = o.modifiers.new("cut", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cutter; md.solver = "EXACT"
    if m_cut is not None: md.material_mode = "TRANSFER"
    return md

# ======================================================================
# MATERIALLAR (umumiy)
# ======================================================================
blood_m = mat("blood", (0.07, 0.0, 0.002), 0.06, coat=1.0)
blood_dark = mat("blood_dark", (0.07, 0.003, 0.008), 0.2, coat=0.6)
steel_m = mat("steel", (0.62, 0.62, 0.64), 0.25, metal=1.0)

def clip_material(name):
    """qog'oz qisqichi: 'heat' (0..1) — uchidan (u=0) cho'g'ga aylanadi"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.7, 0.7, 0.72, 1); b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.22
    heat = value_node(m, "heat", 0.0)
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    mask = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", ua.outputs["Fac"], 0.32), clamp=True)
    mask = P.math_n(N, L, "POWER", mask, 1.4)
    h = P.math_n(N, L, "MULTIPLY", mask, heat)
    cr = N.new("ShaderNodeValToRGB"); L.new(h, cr.inputs[0])
    els = cr.color_ramp.elements; els[0].color = (0.25, 0.02, 0.0, 1); els[1].color = (1.0, 0.55, 0.12, 1)
    e2 = els.new(0.55); e2.color = (1.0, 0.12, 0.01, 1)
    L.new(cr.outputs[0], b.inputs["Emission Color"])
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", h, 1.5), 16.0), b.inputs["Emission Strength"])
    # qizigan metall qorayadi (oksid)
    dk = N.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.inputs[6].default_value = (0.7, 0.7, 0.72, 1); dk.inputs[7].default_value = (0.12, 0.08, 0.07, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", ua.outputs["Fac"], 0.55), clamp=True), heat), dk.inputs["Factor"])
    L.new(dk.outputs[2], b.inputs["Base Color"])
    return m

def nail_blood_material(name):
    """tirnoq: 'blood' (0..1) — ostida qon dog'i kengayadi; 'throb' — yurak urishida qorayadi;
       'hole' — markazda teshik radiusi (ob'ekt koord.), 'burn' — teshik chekkasi cho'g'i"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 0.45; b.inputs["Coat Roughness"].default_value = 0.08
    b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.0005
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.3)
    bl = value_node(m, "blood", 0.0); th = value_node(m, "throb", 0.0); ho = value_node(m, "hole", 0.0); bu = value_node(m, "burn", 0.0)
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    dx = sp.outputs["X"]; dy = P.math_n(N, L, "SUBTRACT", sp.outputs["Y"], 0.12)
    d = P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", dx, dx), P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", dy, dy), 0.8)))
    d = P.math_n(N, L, "ADD", d, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", nz.outputs["Fac"], 0.5), 0.35))
    rad = P.math_n(N, L, "MULTIPLY", bl, 1.05)
    spot = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", d, rad), 0.18), clamp=True)
    spot = P.math_n(N, L, "MULTIPLY", spot, P.math_n(N, L, "MINIMUM", P.math_n(N, L, "MULTIPLY", bl, 4.0), 1.0))
    core = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", d, P.math_n(N, L, "MULTIPLY", rad, 0.6)), 0.25), clamp=True)
    core = P.math_n(N, L, "MULTIPLY", core, bl)
    c0 = N.new("ShaderNodeMix"); c0.data_type = "RGBA"; c0.inputs[6].default_value = (0.86, 0.6, 0.56, 1)
    c0.inputs[7].default_value = (0.13, 0.004, 0.02, 1); L.new(spot, c0.inputs["Factor"])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(c0.outputs[2], c1.inputs[6])
    c1.inputs[7].default_value = (0.02, 0.0015, 0.008, 1)
    L.new(P.math_n(N, L, "MINIMUM", P.math_n(N, L, "ADD", core, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", spot, th), 0.6)), 1.0), c1.inputs["Factor"])
    # teshik
    dh = P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sp.outputs["X"], sp.outputs["X"]),
                 P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", dy, dy), 0.25)))
    inside = P.math_n(N, L, "LESS_THAN", dh, ho)
    rim = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", dh, P.math_n(N, L, "ADD", ho, 0.04))), 0.07), clamp=True)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.02, 0.0, 0.0, 1)
    L.new(P.math_n(N, L, "MAXIMUM", inside, P.math_n(N, L, "MULTIPLY", rim, 0.7)), c2.inputs["Factor"])
    L.new(c2.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (1.0, 0.3, 0.03, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", rim, bu), 12.0), b.inputs["Emission Strength"])
    L.new(P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", inside, 0.0)), b.inputs["Alpha"])
    return m

def smoke_material(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.8, 0.8, 0.82, 1)
    dens = value_node(m, "dens", 0.0); ph = value_node(m, "rise", 0.0)
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "MULTIPLY", ph, -1.0), cmb.inputs["Z"]); L.new(cmb.outputs[0], mp.inputs["Location"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 140.0; nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Distortion"].default_value = 1.2; L.new(mp.outputs[0], nz.inputs["Vector"])
    # radial (Generated X,Y 0..1, markaz 0.5) va balandlik bo'yicha so'nish
    rx = P.math_n(N, L, "SUBTRACT", sp.outputs["X"], 0.5); ry = P.math_n(N, L, "SUBTRACT", sp.outputs["Y"], 0.5)
    rr = P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", rx, rx), P.math_n(N, L, "MULTIPLY", ry, ry)))
    wid = P.math_n(N, L, "ADD", 0.12, P.math_n(N, L, "MULTIPLY", sp.outputs["Z"], 0.3))
    rad = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", rr, wid), clamp=True)
    hz = P.math_n(N, L, "SUBTRACT", 1.0, sp.outputs["Z"], clamp=True)
    den = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", rad, hz), P.math_n(N, L, "POWER", nz.outputs["Fac"], 2.5))
    L.new(P.math_n(N, L, "MULTIPLY", den, P.math_n(N, L, "MULTIPLY", dens, 14.0)), vol.inputs["Density"])
    L.new(vol.outputs[0], out.inputs["Volume"])
    return m

# ======================================================================
# QO'L (procedural, real o'lcham): o'ng qo'l kafti pastda, barmoqlar -Y tomonga, ko'rsatkich uchi = (0,0,0)
# ======================================================================
SKIN = P.skin_material("hand_skin", base=(0.7, 0.4, 0.3))
SKIN.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.14)
def build_hand(name, loc, nail_m):
    root = empty(name, loc)
    fingers = {}
    spec = (("idx", 0.0, 0.0, 0.0079, 0.13), ("mid", -0.0185, -0.006, 0.0081, 0.135), ("rin", -0.0365, -0.002, 0.0076, 0.13),
            ("pin", -0.0525, 0.012, 0.0066, 0.11))
    for nm, x, y, r, ln in spec:
        f = P.build_finger(f"{name}_{nm}", parent=root, r=r, length=ln, skin=SKIN, strength=0.0, seed=hash(nm) % 7)
        f.location = (x, y, r * 0.93); f.rotation_euler = (R(-2.5), 0, R(x * 40)); f["r_"] = r
        fingers[nm] = f
    for f in fingers.values():
        for c in f.children:
            if c.name.endswith("_nail"):
                r_ = f["r_"]; c.scale = (r_ * 0.76, 0.0118, r_ * 0.1); c.location.z = r_ * 0.7
    nail = next(c for c in fingers["idx"].children if c.name.endswith("_nail"))
    nail.data.materials.clear(); nail.data.materials.append(nail_m)
    th = P.build_finger(f"{name}_thumb", parent=root, r=0.0095, length=0.055, skin=SKIN, seed=3.0)
    th.location = (0.034, 0.072, 0.012); th.rotation_euler = (R(-8), R(-35), R(-38))
    palm = uvsphere(f"{name}_palm", (-0.025, 0.2, 0.012), (0.046, 0.075, 0.012), SKIN, parent=root)
    return root, fingers, nail

# ======================================================================
# 1) YO'LAK + ESHIK (0,0,0)
# ======================================================================
hall = empty("HALL")
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.9, 0.86, 0.8))
trim_m = mat("trim", (0.92, 0.92, 0.9), 0.35)
door_m = mat("door_paint", (0.88, 0.87, 0.84), 0.3, coat=0.2)
plane("h_floor", (6, 6), (0, -1.5, 0), floor_m, parent=hall)
DW, DH = 0.9, 2.05
box("h_wallL", (2.0, 0.12, 2.7), (-DW / 2 - 1.0, 0.06, 1.35), wall_m, parent=hall)
box("h_wallR", (2.0, 0.12, 2.7), (DW / 2 + 1.0, 0.06, 1.35), wall_m, parent=hall)
box("h_wallT", (DW, 0.12, 2.7 - DH), (0, 0.06, (DH + 2.7) / 2), wall_m, parent=hall)
box("h_wallS", (0.12, 4.0, 2.7), (2.2, -1.9, 1.35), wall_m, parent=hall)
box("h_wallS2", (0.12, 4.0, 2.7), (-2.2, -1.9, 1.35), wall_m, parent=hall)
box("h_ceil", (4.6, 4.0, 0.05), (0, -1.9, 2.72), mat("ceil", (0.9, 0.9, 0.88), 0.8), parent=hall)
for nm, sz, lc in (("jambL", (0.06, 0.16, DH), (-DW / 2 - 0.03, 0.03, DH / 2)), ("jambR", (0.06, 0.16, DH), (DW / 2 + 0.03, 0.03, DH / 2)),
                   ("jambT", (DW + 0.12, 0.16, 0.06), (0, 0.03, DH + 0.03))):
    box("h_" + nm, sz, lc, trim_m, parent=hall, bevel=0.004)
box("h_base", (4.4, 0.02, 0.1), (0, -0.01, 0.05), trim_m, parent=hall)
# narigi xona (eshik orqasi): yorug'roq
box("h_far", (3, 0.1, 2.7), (0, 2.5, 1.35), mat("far_wall", (0.8, 0.75, 0.68), 0.8), parent=hall)
plane("h_far_floor", (3, 2.5), (0, 1.3, 0.001), floor_m, parent=hall)
HINGE = V(-DW / 2 + 0.01, -0.005, 0)
door = empty("door_pivot", tuple(HINGE), hall)
box("door_leaf", (DW - 0.03, 0.04, DH - 0.02), ((DW - 0.03) / 2, -0.02, DH / 2), door_m, parent=door, bevel=0.003)
for z in (0.55, 1.45):
    box("door_panel", (0.62, 0.006, 0.7), ((DW - 0.03) / 2, -0.043, z), door_m, parent=door, bevel=0.01)
hd = empty("door_handle", ((DW - 0.03) - 0.07, -0.04, 1.0), door)
cyl("handle_rose", 0.025, 0.012, (0, -0.006, 0), steel_m, rot=(90, 0, 0), parent=hd)
cyl("handle_bar", 0.009, 0.12, (-0.05, -0.05, 0), steel_m, rot=(0, 90, 0), parent=hd)
cyl("handle_neck", 0.008, 0.045, (0, -0.03, 0), steel_m, rot=(90, 0, 0), parent=hd)
for z in (0.25, 1.8):
    cyl("hinge", 0.008, 0.09, (0.0, 0.0, z), steel_m, parent=door)
# eshik: ochiqdan (−82°) tezlashib yopiladi, barmoqlarga urilib to'xtaydi
for f in range(1, F_SLAM + 1):
    t = (f - 1) / (F_SLAM - 1); a = -82 + 78 * (t ** 2.2)
    key(door, f, rot=(0, 0, a))
for f, a in ((F_SLAM + 2, -7.5), (F_SLAM + 5, -4.5), (F_SLAM + 9, -5.5), (F_SLAM + 14, -5.0)):
    key(door, f, rot=(0, 0, a))
plant = import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.75, -1.0, 0), (0, 0, 30), 0.9, parent=hall)
pic = import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (2.13, -1.3, 1.55), (0, 0, 90), 1.0, parent=hall)

# ======================================================================
# 2) KLINIKA (20,0,0)
# ======================================================================
CL = V(20, 0, 0)
clinic = empty("CLINIC", tuple(CL))
tile_m = pbr("tiles", "long_white_tiles", 0.7)
cwall_m = pbr("cwall", "painted_plaster_wall", 0.6, tint=(0.75, 0.88, 0.88))
plane("c_floor", (6, 6), (0, 0, 0), tile_m, parent=clinic)
box("c_wallB", (6, 0.1, 2.8), (0, -1.8, 1.4), cwall_m, parent=clinic)
box("c_wallF", (6, 0.1, 2.8), (0, 2.6, 1.4), cwall_m, parent=clinic)
box("c_wallL", (0.1, 4.4, 2.8), (-2.2, 0.4, 1.4), cwall_m, parent=clinic)
box("c_wallR", (0.1, 4.4, 2.8), (2.2, 0.4, 1.4), cwall_m, parent=clinic)
box("c_ceil", (4.4, 4.4, 0.05), (0, 0.4, 2.8), mat("cceil", (0.92, 0.93, 0.93), 0.8), parent=clinic)
desk = import_gltf(PH + "metal_office_desk/metal_office_desk.gltf", (0, 0, 0), (0, 0, 0), (0.6, 1.0, 0.95), parent=clinic)
DESK_TOP = 0.788 * 0.95
chair = import_gltf(PH + "SchoolChair_01/SchoolChair_01.gltf", (0.1, 0.78, 0), (0, 0, 180), 1.0, parent=clinic)
import_gltf(PH + "medical_box/medical_box.gltf", (-0.38, -0.12, DESK_TOP), (0, 0, 12), 0.7, parent=clinic)
import_gltf(PH + "clipboard/clipboard.gltf", (0.42, 0.12, DESK_TOP + 0.004), (0, 0, -15), 1.0, parent=clinic)
BUN = V(0.32, -0.2, DESK_TOP)
import_gltf(PH + "bunsen_burner/bunsen_burner.gltf", tuple(BUN), (0, 0, 0), 1.0, parent=clinic)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-1.7, -1.4, 0), (0, 0, 0), 1.0, parent=clinic)
import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (0.3, -1.74, 1.6), (0, 0, 0), 1.2, parent=clinic)
drape_m = mat("drape", (0.12, 0.42, 0.55), 0.85, sss=0.05)
plane("c_drape", (0.34, 0.3), (0.05, 0.22, DESK_TOP + 0.003), drape_m, parent=clinic)
# deraza o'rnida yorug' panel (orqa devor)
plane("c_window", (1.3, 1.0), (-1.0, -1.74, 1.6), mat("cwin", (1, 1, 1), emit=3.0, emit_col=(0.85, 0.93, 1.0)), rot=(90, 0, 0), parent=clinic)

# ======================================================================
# 3) ALANGA (Bunsen) materiali va qisqich + omburcha (asbob)
# ======================================================================
def flame_material(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    nz.noise_dimensions = "4D"; nz.inputs["W"].default_value = 0.0
    nz.inputs["W"].keyframe_insert("default_value", frame=1); nz.inputs["W"].default_value = 60.0; nz.inputs["W"].keyframe_insert("default_value", frame=END)
    cr = N.new("ShaderNodeValToRGB"); L.new(sp.outputs["Z"], cr.inputs[0])
    e = cr.color_ramp.elements; e[0].color = (0.15, 0.35, 1.0, 1); e[1].color = (0.6, 0.3, 0.9, 1); e[0].position = 0.3
    em = N.new("ShaderNodeEmission"); L.new(cr.outputs[0], em.inputs["Color"])
    fac = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.3), P.math_n(N, L, "ADD", nz.outputs["Fac"], 0.4))
    fac = P.math_n(N, L, "MULTIPLY", fac, P.math_n(N, L, "SUBTRACT", 1.0, sp.outputs["Z"], clamp=True))
    L.new(P.math_n(N, L, "MULTIPLY", fac, 5.0), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], out.inputs[0])
    return m
FLM = flame_material("flame")
def flame(name, loc, parent, h=0.07, r=0.009):
    o = uvsphere(name, (0, 0, 0), (1, 1, 1), FLM, parent=parent, seg=32, rings=16)
    for v in o.data.vertices:
        z = (v.co.z + 1) / 2                         # 0..1
        k = math.sin(math.pi * min(1.0, z * 0.9 + 0.1)) ** 0.8 * (1 - 0.6 * z)
        v.co.x *= r * max(k, 0.05) / 1.0; v.co.y *= r * max(k, 0.05); v.co.z = z * h
    o.location = loc
    inner = uvsphere(name + "_in", (0, 0, 0), (1, 1, 1), FLM, parent=parent, seg=24, rings=12)
    for v in inner.data.vertices:
        z = (v.co.z + 1) / 2; k = math.sin(math.pi * min(1.0, z)) * (1 - 0.7 * z)
        v.co.x *= r * 0.5 * max(k, 0.05); v.co.y *= r * 0.5 * max(k, 0.05); v.co.z = z * h * 0.45
    inner.location = loc
    wv = o.modifiers.new("wv", "WAVE"); wv.height = r * 0.08; wv.width = h * 0.4; wv.speed = 0.02; wv.use_normal = True
    return o

CLIP_M = clip_material("clip")
def build_tool(name, scale=1.0, parent=None):
    """asbob: qog'oz qisqichi uchi = (0,0,0), to'g'ri qismi +Z bo'ylab; tepasida omburcha (pliers) ushlab turadi"""
    root = empty(name, (0, 0, 0), parent)
    s = 0.001 * scale
    pts = [(0, 0, 0), (0, 0, 12 * s), (0, 0, 24 * s), (0, 0, 32 * s), (0, 2.2 * s, 35.6 * s), (0, 5 * s, 36.4 * s), (0, 7.8 * s, 35.6 * s),
           (0, 10 * s, 32 * s), (0, 10 * s, 20 * s), (0, 10 * s, 10 * s), (0, 8.5 * s, 7.5 * s), (0, 6.5 * s, 6.5 * s), (0, 4.5 * s, 7.5 * s),
           (0, 3.2 * s, 10 * s), (0, 3.2 * s, 26 * s)]
    clip = P.tube(name + "_clip", pts, 0.00048 * scale, CLIP_M, root, res=16)
    pl = import_gltf(PH + "pliers/pliers.gltf", (0, 6.6 * s, 34 * s + 0.046 * scale), (180, 0, 0), scale, parent=root)
    return root, clip, pl

# ======================================================================
# 4) MAKRO A — ISH STOLI (0,30,0): bolg'a, qon dog'i
# ======================================================================
MW = V(0, 30, 0)
mw = empty("MACRO_W", tuple(MW))
wood_m = pbr("wood", "wood_table_001", 3.0)
box("w_top", (0.9, 0.7, 0.05), (0, 0.15, -0.025), wood_m, parent=mw)
NAIL_W = nail_blood_material("nail_w")
handW, fingW, nailW = build_hand("handW", (0, 0, 0), NAIL_W); handW.parent = mw
# bolg'a: dasta +X bo'ylab, boshi tirnoq ustida; G (bilak) atrofida aylanadi
NAIL_TOP = 0.0079 * 0.93 + 0.0079 * 0.8
G = empty("hammer_grip", (-0.275, 0.013, NAIL_TOP + 0.05), mw)
hm = import_gltf(PH + "cross_pein_hammer/cross_pein_hammer.gltf", (0.125, 0, 0), (0, 90, 0), 1.0, parent=G)
H0, H1 = S["hammer"]
for f, a in ((H0, -38), (H0 + 10, -46), (F_HIT - 6, -40), (F_HIT, 0.5), (F_HIT + 2, -2.5), (F_HIT + 7, -1.5), (H1, -6)):
    key(G, f, rot=(0, a, 0))
for fc in fcurves(G):
    for k in fc.keyframe_points: k.interpolation = "BEZIER"
# zarbadan keyin barmoq biroz yassilanadi
idxW = fingW["idx"]
for f, s in ((F_HIT - 1, 1.0), (F_HIT, 0.86), (F_HIT + 3, 0.97), (F_HIT + 8, 1.0)):
    key(idxW, f, scale=(1.0, 1.0, s))
# qon dog'i (time-lapse) + yurak urishida "tepish"
B0, B1 = S["blood"]
val_key(NAIL_W, "blood", 1, 0.0); val_key(NAIL_W, "blood", F_HIT + 2, 0.0); val_key(NAIL_W, "blood", F_HIT + 10, 0.12)
val_key(NAIL_W, "blood", B0, 0.18); val_key(NAIL_W, "blood", B0 + 60, 0.78); val_key(NAIL_W, "blood", B1, 0.85)
val_key(NAIL_W, "throb", 1, 0.0)
for b in BEATS:
    if B0 <= b <= B1:
        val_key(NAIL_W, "throb", b - 1, 0.0); val_key(NAIL_W, "throb", b + 1, 1.0); val_key(NAIL_W, "throb", b + 6, 0.0)
        key(idxW, b - 1, scale=(1, 1, 1)); key(idxW, b + 1, scale=(1.025, 1.0, 1.04)); key(idxW, b + 6, scale=(1, 1, 1))
# qizargan teri (barmoq uchi) — kuchsiz qizil nuqta yorug'lik emas, rang: skin material o'zgarmaydi

# ======================================================================
# 5) MAKRO B — KLINIKA STOLI (0,40,0): alanga, qisqich, teshish, favvora
# ======================================================================
MCv = V(0, 40, 0)
mcs = empty("MACRO_C", tuple(MCv))
box("m_desk", (1.2, 1.0, 0.04), (0, 0.15, -0.02), mat("m_desk_m", (0.55, 0.57, 0.58), 0.35, metal=0.6), parent=mcs)
dr = plane("m_drape", (0.3, 0.32), (-0.015, 0.06, 0.0008), drape_m, parent=mcs)
NAIL_C = nail_blood_material("nail_c")
handC, fingC, nailC = build_hand("handC", (0, 0, 0), NAIL_C); handC.parent = mcs
val_key(NAIL_C, "blood", 1, 0.85)
BUNM = V(0.11, -0.07, 0)
bunM = import_gltf(PH + "bunsen_burner/bunsen_burner.gltf", tuple(BUNM), (0, 0, 0), 1.0, parent=mcs)
FL_Z = 0.173
flM = flame("m_flame", tuple(BUNM + V(0, 0, FL_Z - 0.002)), mcs, h=0.06, r=0.0065)
import_gltf(PH + "medical_box/medical_box.gltf", (-0.2, -0.28, 0), (0, 0, 20), 0.7, parent=mcs)
toolM, clipM, plM = build_tool("toolM", 1.0, mcs)
# nail markazi (mcs mahalliy): tirnoq sharining tepasi
sc.frame_set(1); bpy.context.view_layer.update()
NC = mcs.matrix_world.inverted() @ (nailC.matrix_world @ V(0, 0.1, 1.0)); print("NC", NC)
FLAME_PT = BUNM + V(0, 0, FL_Z + 0.032)
HE0, HE1 = S["heat"]; TO0, TO1 = S["touch"]; ME0, ME1 = S["melt"]; FO0, FO1 = S["fountain"]
# isitish: uch alangada, biroz aylanadi
key(toolM, 1, loc=tuple(FLAME_PT + V(-0.006, 0, 0.012)), rot=(-20, 14, 0))
key(toolM, HE0, loc=tuple(FLAME_PT + V(-0.006, 0, 0.012)), rot=(-20, 14, 0))
key(toolM, HE1, loc=tuple(FLAME_PT + V(0.0, 0, 0.0)), rot=(-24, 10, 0))
# tirnoqqa: tepadan tushadi, tegadi, botadi, chiqadi
key(toolM, TO0, loc=tuple(NC + V(0.002, -0.006, 0.05)), rot=(-14, 10, 0))
key(toolM, F_TOUCH, loc=tuple(NC + V(0, 0, 0.0002)), rot=(-12, 8, 0))
key(toolM, ME0, loc=tuple(NC + V(0, 0, 0.0001)), rot=(-12, 8, 0))
key(toolM, F_PIERCE, loc=tuple(NC + V(0, 0, -0.0011)), rot=(-12, 8, 0))
key(toolM, F_OUT - 3, loc=tuple(NC + V(0, 0, -0.0012)), rot=(-12, 8, 0))
key(toolM, F_OUT + 5, loc=tuple(NC + V(-0.004, -0.012, 0.035)), rot=(-30, 8, 0))
key(toolM, FO1, loc=tuple(NC + V(-0.01, -0.03, 0.08)), rot=(-40, 8, 0))
interp(toolM, "LINEAR")
# qizish: isitishda 0 -> 1, keyin ozgina soviydi
val_key(CLIP_M, "heat", 1, 0.0); val_key(CLIP_M, "heat", HE0 + 8, 0.05); val_key(CLIP_M, "heat", HE1 - 8, 1.0)
val_key(CLIP_M, "heat", F_PIERCE, 0.85); val_key(CLIP_M, "heat", FO1, 0.55)
# teshik va cho'g' chekka
val_key(NAIL_C, "hole", 1, 0.0); val_key(NAIL_C, "hole", F_TOUCH, 0.0); val_key(NAIL_C, "hole", F_TOUCH + 4, 0.03)
val_key(NAIL_C, "hole", F_PIERCE, 0.07); val_key(NAIL_C, "hole", F_OUT, 0.075)
val_key(NAIL_C, "burn", 1, 0.0); val_key(NAIL_C, "burn", F_TOUCH, 0.0); val_key(NAIL_C, "burn", F_TOUCH + 3, 1.0)
val_key(NAIL_C, "burn", F_PIERCE, 1.0); val_key(NAIL_C, "burn", F_OUT + 10, 0.2); val_key(NAIL_C, "burn", FO1, 0.0)
val_key(NAIL_C, "blood", F_OUT + 4, 0.85); val_key(NAIL_C, "blood", FO1, 0.45)
# tutun (hajmli)
SMK = smoke_material("smoke")
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); smoke = bpy.context.object; smoke.name = "smoke"
smoke.scale = (0.012, 0.012, 0.03); bpy.ops.object.transform_apply(scale=True)
for v in smoke.data.vertices: v.co.z += 0.03
smoke.data.materials.append(SMK); smoke.parent = mcs; smoke.location = tuple(NC)
val_key(SMK, "dens", 1, 0.0); val_key(SMK, "dens", F_TOUCH, 0.0); val_key(SMK, "dens", F_TOUCH + 6, 0.6); val_key(SMK, "dens", F_PIERCE, 1.0)
val_key(SMK, "dens", F_OUT + 6, 0.5); val_key(SMK, "dens", FO1, 0.15)
val_key(SMK, "rise", 1, 0.0); val_key(SMK, "rise", END, 0.0035 * (END - 1))
interp(SMK.node_tree, "LINEAR")
# qon favvorasi: teshikdan otiladigan tomchilar (sekinlashtirilgan ballistika) + markaziy oqim
NCW = mcs.matrix_world @ NC
rnd = random.Random(5)
SLOW = 0.35; GR = 9.81 * SLOW * SLOW
drops = []
for i in range(80):
    t0 = F_JET + rnd.uniform(0, 30) * (0.4 + 0.6 * (i / 80))
    sp_ = rnd.uniform(0.55, 1.15) * (1.1 - 0.5 * ((t0 - F_JET) / 30)) * SLOW
    ang = rnd.uniform(0, 2 * math.pi); tilt = R(rnd.uniform(0, 16))
    vel = V(math.sin(tilt) * math.cos(ang), math.sin(tilt) * math.sin(ang), math.cos(tilt)) * sp_
    r_ = rnd.uniform(0.00035, 0.0011)
    d = sphere(f"jet{i}", r_, (0, 0, 0), blood_m, sub=2, parent=mcs)
    drops.append((d, t0, vel, r_))
    p = NC.copy(); landed = False
    for f in range(int(t0) - 1, FO1 + 2):
        if f < t0:
            key(d, f, loc=tuple(NC + V(0, 0, -0.002)), scale=0.001); continue
        dt = (f - t0) / 24.0
        if not landed:
            p = NC + vel * dt + V(0, 0, -0.5 * GR * dt * dt)
            v_ = vel + V(0, 0, -GR * dt)
            if p.z < NC.z - 0.004 and v_.z < 0:
                landed = True; p.z = max(p.z, 0.0006)
            st = 1.0 + min(2.2, v_.length / (0.25 * SLOW))
            # tomchini tezlik bo'ylab cho'zish
            d.rotation_mode = "QUATERNION"; d.rotation_quaternion = v_.normalized().to_track_quat("Z", "Y")
            d.keyframe_insert("rotation_quaternion", frame=f)
            key(d, f, loc=tuple(p), scale=(1, 1, st))
        else:
            key(d, f, loc=tuple(p), scale=(1.6, 1.6, 0.35))
    interp(d, "LINEAR")
    vis(d, [(FO0, FO1)], recursive=False)
jet = cyl("jet_core", 0.0009, 1.0, (0, 0, 0.5), blood_m, parent=mcs, verts=16)
for v in jet.data.vertices: v.co.z += 0.5; v.co.x *= (1.0 - 0.6 * v.co.z); v.co.y *= (1.0 - 0.6 * v.co.z)
jet.location = tuple(NC + V(0, 0, -0.0005))
for f, h in ((F_JET - 1, 0.0001), (F_JET + 3, 0.035), (F_JET + 14, 0.05), (F_JET + 30, 0.03), (FO1, 0.004)):
    key(jet, f, scale=(1, 1, h))
vis(jet, [(F_JET - 1, FO1)], recursive=False)
dome = sphere("blood_dome", 0.0028, tuple(NC), blood_m, scale=(1, 1, 0.01), parent=mcs)
for f, s in ((F_OUT, 0.01), (F_JET - 1, 0.5), (F_JET + 6, 0.7), (FO1, 0.55)):
    key(dome, f, scale=(1 if s > 0.05 else 0.3, 1.25 if s > 0.05 else 0.3, s))
vis(dome, [(F_OUT, FO1)], recursive=False)
# tirnoq ustiga oqib tushgan qon ko'lmagi
pool = sphere("blood_pool", 0.006, tuple(NC + V(0, 0.002, -0.0004)), blood_m, scale=(0.2, 0.2, 0.05), parent=mcs)
for f, s in ((F_JET, 0.2), (F_JET + 20, 1.0), (FO1, 1.5)):
    key(pool, f, scale=(s * 0.95, s * 1.3, 0.06))
vis(pool, [(F_JET, FO1)], recursive=False)
# cho'g' uchidan yorug'lik
glowL = point("tip_glow", (0, 0, 0.002), 0.002, (1.0, 0.35, 0.05), [(1, 0.0), (HE0 + 20, 0.03), (HE1 - 8, 0.25), (F_PIERCE, 0.2), (FO1, 0.06)], const=False, parent=toolM)
flameL = point("flame_glow", tuple(BUNM + V(0, 0, FL_Z + 0.03)), 0.01, (0.4, 0.55, 1.0), lights_for(rng("heat", "touch"), 0.6), parent=mcs)

# ======================================================================
# 6) KESIM (cutaway) — 10x barmoq uchi (0,60,0); kamera +X dan qaraydi
# ======================================================================
CUT = V(0, 60, 0.6)
flesh_m = mat("flesh", (0.5, 0.07, 0.06), 0.45, sss=0.2, coat=0.3)
fat_m = mat("fat", (0.9, 0.62, 0.18), 0.4, sss=0.2, coat=0.3)
bone_m = mat("bone", (0.9, 0.84, 0.7), 0.55, sss=0.1)
bone_cut = mat("bone_cut", (0.8, 0.74, 0.62), 0.8)
bed_m = mat("nailbed", (0.75, 0.03, 0.05), 0.35, sss=0.2, coat=0.4)
nailcut_m = mat("nail_cut", (0.75, 0.62, 0.5), 0.25, coat=0.6, sss=0.2)
def nail_glass(name):
    m = mat(name, (0.95, 0.85, 0.78), 0.18, coat=0.8, sss=0.3)
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (0.25, 0.6, 1.0, 1)
    v = value_node(m, "cool", 0.0); m.node_tree.links.new(P.math_n(m.node_tree.nodes, m.node_tree.links, "MULTIPLY", v, 2.0), b.inputs["Emission Strength"])
    return m
NAILX = nail_glass("nail_x")
blood_cut = mat("blood_cut", (0.2, 0.005, 0.01), 0.15, coat=0.7)
cutp = empty("CUT", tuple(CUT)); bpy.context.view_layer.update()
K = 10.0
def cutter(name, m, off=0.0):
    # ichki qatlamlar kesim yuzasidan biroz oldinda (off) — ustma-ust yuzlar qorayib ketmasin
    c = box(name, (4, 4, 4), tuple(CUT + V(2.0 + off, 0, 0)), m)
    c.hide_render = True; c.hide_viewport = True; c.display_type = "WIRE"
    return c
CUT_FLESH = cutter("cutter_flesh", flesh_m); CUT_BONE = cutter("cutter_bone", bone_cut, 0.003)
CUT_NAIL = cutter("cutter_nail", nailcut_m, 0.002); CUT_BLOOD = cutter("cutter_blood", blood_cut, 0.006); CUT_BED = cutter("cutter_bed", bed_m, 0.0045)
CUT_FAT = cutter("cutter_fat", fat_m, 0.0015)
fx = P.build_finger("cut_finger", r=0.0079, length=0.06, skin=SKIN, knuckle=False)
fx.modifiers.remove(fx.modifiers["wr"])
bm = bmesh.new(); bm.from_mesh(fx.data); bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0); bm.to_mesh(fx.data); bm.free()
fnail = next(c for c in fx.children if c.name.endswith("_nail"))
fnail.parent = None; fnail.data.materials.clear(); fnail.data.materials.append(NAILX)
# real o'lchamdagi qismlarni CUT ga K masshtab bilan joylash (boolean'dan OLDIN dunyo o'lchamiga keltiramiz)
def place_cut(o):
    bpy.context.view_layer.update()
    o.matrix_world = Matrix.Translation(CUT) @ Matrix.Scale(K, 4) @ o.matrix_world
    return o
place_cut(fx); place_cut(fnail)
boolean_cut(fx, CUT_FLESH, flesh_m); boolean_cut(fnail, CUT_NAIL, nailcut_m)
fx.data.materials.append(flesh_m); fnail.data.materials.append(nailcut_m)
bone = uvsphere("cut_bone", (0, 0.017, 0.0009), (0.0026, 0.012, 0.0021), bone_m); place_cut(bone)
bone.data.materials.append(bone_cut); boolean_cut(bone, CUT_BONE, bone_cut)
tuft = uvsphere("cut_tuft", (0, 0.0062, 0.0012), (0.0032, 0.0022, 0.0017), bone_m); place_cut(tuft)
tuft.data.materials.append(bone_cut); boolean_cut(tuft, CUT_BONE, bone_cut)
bone2 = uvsphere("cut_bone2", (0, 0.04, 0.0003), (0.0029, 0.0115, 0.0025), bone_m); place_cut(bone2)
bone2.data.materials.append(bone_cut); boolean_cut(bone2, CUT_BONE, bone_cut)
pad = uvsphere("cut_fat", (0, 0.014, -0.0026), (0.0036, 0.011, 0.0022), fat_m); place_cut(pad)
boolean_cut(pad, CUT_FAT, fat_m)
nb = uvsphere("cut_bed", (0, 0.0128, 0.0037), (0.0058, 0.0112, 0.00045), bed_m); nb.rotation_euler = (R(-3), 0, 0); place_cut(nb)
boolean_cut(nb, CUT_BED, bed_m)
pk = uvsphere("cut_pocket", (0, 0.013, 0.00405), (0.0035, 0.0068, 0.0003), blood_m); place_cut(pk)
pk.data.materials.append(blood_cut); boolean_cut(pk, CUT_BLOOD, blood_cut)
cut_objs = [fx, fnail, bone, tuft, bone2, pad, nb, pk]
for o in cut_objs: o.parent = cutp; o.matrix_parent_inverse = cutp.matrix_world.inverted()
for c in (CUT_FLESH, CUT_BONE, CUT_NAIL, CUT_BLOOD, CUT_BED, CUT_FAT): c.hide_viewport = False
# asab tolalari (sariq) — kesim yuzasida yarmi chiqib turadi; "pain" -> qizil miltillash
def nerve_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.5
    pain = value_node(m, "pain", 0.0); glow = value_node(m, "glow", 0.6)
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; c.inputs[6].default_value = (1.0, 0.78, 0.2, 1); c.inputs[7].default_value = (1.0, 0.05, 0.02, 1)
    L.new(pain, c.inputs["Factor"]); L.new(c.outputs[2], b.inputs["Base Color"]); L.new(c.outputs[2], b.inputs["Emission Color"])
    L.new(P.math_n(N, L, "ADD", glow, P.math_n(N, L, "MULTIPLY", pain, 2.2)), b.inputs["Emission Strength"])
    return m
NERVE = nerve_mat("nerve")
nerves = []
rn = random.Random(3)
for i in range(4):
    z0 = 0.00335 + 0.00012 * i; ys = 0.006 + 0.0035 * i
    pts = [(0.0, 0.05, 0.0029 + 0.0001 * i), (0.0, 0.035, 0.0031 + 0.0001 * i), (0.0, 0.024, z0), (0.0, ys + 0.004, z0 + 0.00008),
           (0.0, ys, z0 + 0.00012 + rn.uniform(-0.00005, 0.00005))]
    pts = [tuple(CUT + V(*p) * K + V(0.007, 0, 0)) for p in pts]
    t = P.tube(f"nerve{i}", pts, 0.0022, NERVE, None, res=12)
    t.parent = cutp; t.matrix_parent_inverse = cutp.matrix_world.inverted(); nerves.append(t)
# kichik tomirlar (qizil)
VES = mat("vessel", (0.6, 0.03, 0.03), 0.3, coat=0.5, emit=0.3)
for i in range(0):
    pts = [(0.0, 0.05, -0.0035 + 0.001 * i), (0.0, 0.03, -0.0025 + 0.0012 * i), (0.0, 0.012, -0.0018 + 0.0018 * i), (0.0, 0.005, 0.0005 + 0.0008 * i)]
    t = P.tube(f"vessel{i}", [tuple(CUT + V(*p) * K + V(0.005, 0, 0)) for p in pts], 0.0032, VES, None); t.parent = cutp
    t.matrix_parent_inverse = cutp.matrix_world.inverted()
# katta qisqich (kesimda): uchi tirnoq markazida
toolX, clipX, plX = build_tool("toolX", K, None)
NCX = CUT + V(0, 0.0125, 0.0066) * K
TX0, TX1 = S["nonerve"]; RE0, RE1 = S["release"]
toolX.rotation_euler = (R(-8), 0, 0)
key(toolX, 1, loc=tuple(NCX + V(0, 0, 0.0)))
key(toolX, RE0, loc=tuple(NCX + V(0, 0, -0.013)))
key(toolX, RE0 + 10, loc=tuple(NCX + V(0, -0.02, 0.12)))
interp(toolX, "LINEAR")
vis(toolX, rng("nonerve", "release"))
# teshik (release): kesim tirnog'ida silindr boolean
holeC = cyl("hole_cutter", 0.0035, 0.06, tuple(NCX), None); holeC.hide_render = True; holeC.display_type = "WIRE"
hb = fnail.modifiers.new("hole", "BOOLEAN"); hb.operation = "DIFFERENCE"; hb.object = holeC; hb.solver = "EXACT"
hb.show_render = False; hb.keyframe_insert("show_render", frame=1); hb.show_render = True; hb.keyframe_insert("show_render", frame=RE0)
hb.show_viewport = False
# qon cho'ntagi: o'sadi (press), qoladi, bo'shaydi (release)
TI0, TI1 = S["tight"]; PR0, PR1 = S["press"]
PK_S = pk.scale.copy()
for f, s in ((1, 0.3), (TI1, 0.4), (PR0 + 4, 0.5), (PR1 - 10, 2.6), (RE0 + 3, 2.6), (RE0 + 30, 0.6), (RE1, 0.35)):
    key(pk, f, scale=(PK_S.x, PK_S.y, PK_S.z * s))
interp(pk, "LINEAR")
# asab bosilishi: tolalar pastga siqiladi va qizil miltillaydi
for t in nerves:
    for f, dz in ((1, 0.0), (PR0 + 4, 0.0), (PR1 - 10, -0.0035), (RE0 + 3, -0.0035), (RE0 + 30, 0.0)):
        key(t, f, loc=(0, 0, dz))
    interp(t, "LINEAR")
val_key(NERVE, "pain", 1, 0.0); val_key(NERVE, "pain", PR0 + 10, 0.1)
for f in range(PR0 + 20, PR1 + 1, 14):
    val_key(NERVE, "pain", f, 0.55); val_key(NERVE, "pain", f + 4, 1.0); val_key(NERVE, "pain", f + 10, 0.6)
val_key(NERVE, "pain", TX0, 0.25); val_key(NERVE, "pain", TX1, 0.25)
val_key(NERVE, "pain", RE0, 1.0); val_key(NERVE, "pain", RE0 + 26, 0.0)
val_key(NERVE, "glow", 1, 0.6); val_key(NERVE, "glow", TX0, 0.3); val_key(NERVE, "glow", RE0, 0.6)
val_key(NAILX, "cool", 1, 0.0); val_key(NAILX, "cool", TX0 + 6, 0.0); val_key(NAILX, "cool", TX0 + 18, 1.0); val_key(NAILX, "cool", TX1, 1.0); val_key(NAILX, "cool", TX1 + 1, 0.0)
# bo'shayotgan qon: teshikdan yuqoriga chiqadigan tomchilar
rel_drops = []
for i in range(14):
    d = sphere(f"rel_drop{i}", 0.0025 + 0.0015 * rnd.random(), tuple(NCX), blood_m, sub=2, parent=None)
    t0 = RE0 + 2 + i * 1.6
    for f in range(RE0, RE1 + 1, 2):
        if f < t0: key(d, f, loc=tuple(NCX + V(0, 0, -0.01)), scale=0.01); continue
        dt = (f - t0) / 24.0
        key(d, f, loc=tuple(NCX + V(rnd.uniform(-0.002, 0.002), 0.003, 0.12 * dt - 0.08 * dt * dt)), scale=1.0)
    vis(d, [(RE0, RE1)], recursive=False)

# ======================================================================
# 7) MEGAN (yo'lak -> klinika) va OLIVIA (shifokor)
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
oroot, oli, omeshes = mc.load_character("oli", "Olivia.fbx"); sc.render.fps = 24
soften(omeshes, 0.55)
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
LOWER = ("Hips", "UpLeg", "Leg", "Foot", "ToeBase", "Toe_End")
def upper(act, drop=()):
    a = act.copy(); a.name = act.name + "_upper" + "".join(drop); a.use_fake_user = True
    for fc in list(mc._fcurves(a)):
        b = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        if any(b.endswith(s) for s in LOWER) or any(d in b for d in drop): mc._channelbag_remove(a, fc)
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

MEG_H = V(0.86, -0.36, 0.0)
place(mroot, 1, tuple(MEG_H), float(os.environ.get("MEG_ROT", -90)))
MEG_C = CL + V(0.1, 0.72, float(os.environ.get("SEAT_Z", 0.0)))
place(mroot, S["clinic"][0], tuple(MEG_C), 0.0)
interp(mroot, "CONSTANT")
BRE = A_("Breathing_Idle.fbx")
strip(meg, BRE, -30, repeat=span(BRE, 90))
SHK = A_("Shaking_It_Off.fbx")
strip(meg, SHK, F_SLAM - 2, speed=0.82, bi=3, bo=6)
INJ = A_("Injured_Idle.fbx")
strip(meg, INJ, S["xray"][0] - 6, repeat=span(INJ, 90), bi=6)
SEAT = A_("Seated_Idle.fbx")
strip(meg, SEAT, S["clinic"][0] - 10, repeat=span(SEAT, END - S["clinic"][0] + 20))
REL = upper(A_("Relieved_Sigh.fbx"))
strip(meg, REL, S["relief"][0] - 6, speed=0.9, bi=5, bo=8)
# eshik oldida: o'ng qo'l kesakiga (jamb) tayangan — IK
jamb_t = empty("jamb_wrist", (DW / 2 + 0.11, -0.07, 1.06))
ikR = meg.pose.bones["mixamorig:RightForeArm"].constraints.new("IK"); ikR.target = jamb_t; ikR.use_tail = True; ikR.chain_count = 2
for f, v in ((1, 1.0), (F_SLAM + 1, 1.0), (F_SLAM + 5, 0.0)):
    ikR.influence = v; ikR.keyframe_insert("influence", frame=f)
# Olivia: stol ortida, omburchani gorelka ustida ushlab turadi
OLI = CL + V(0.38, -0.6, 0.0)
place(oroot, 1, tuple(OLI), 180.0)
STI = A_("Standing_Idle_2.fbx")
strip(oli, STI, 1, repeat=span(STI, END + 2))
toolC, clipC, plC = build_tool("toolC", 1.0, clinic)
toolC.location = tuple(BUN + V(0, 0.0, 0.2)); toolC.rotation_euler = (R(-30), 0, R(-10))
grip = empty("oli_grip", (0, 0.025, 0.2), toolC)
ikO = oli.pose.bones["mixamorig:RightForeArm"].constraints.new("IK"); ikO.target = grip; ikO.use_tail = True; ikO.chain_count = 2
flC = flame("c_flame", tuple(BUN + V(0, 0, FL_Z - 0.002)), clinic, h=0.06, r=0.0065)
for o in omeshes: vis(o, CL_R, recursive=False)
for o in mmeshes: vis(o, HALL_R + CL_R, recursive=False)

# --- rentgen: shaffof nusxa + yurak + og'riq impulsi (barmoq -> miya) ---
xbody = P.xray_material("xr_body", (0.35, 0.75, 1.0), 1.2, 0.03)
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    g.animation_data_clear()            # nusxa asl ob'ektning hide_render harakatini ulashmasin
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR_R, recursive=False)
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
chestE = child_of_bone("meg_chest", meg, "Spine2")
heart_m = mat("heart", (0.8, 0.03, 0.03), 0.3, emit=2.0, emit_col=(1.0, 0.06, 0.03))
heart = empty("heart", (0.03, 0.02, 0.06), chestE)
sphere("heart_a", 0.035, (0.012, 0.01, 0), heart_m, (1, 1.1, 0.9), parent=heart)
sphere("heart_b", 0.033, (-0.014, 0.012, 0), heart_m, (1, 1.05, 0.9), parent=heart)
sphere("heart_c", 0.03, (0.0, -0.025, 0), heart_m, (0.9, 1.3, 0.85), parent=heart)
for b in BEATS_X:
    key(heart, b - 1, scale=1.0); key(heart, b + 1, scale=1.3); key(heart, b + 5, scale=0.95); key(heart, b + 10, scale=1.0)
vis(heart, XR_R)
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
brain_m = mat("xbrain_m", (0.85, 0.45, 0.5), 0.4, emit=0.6, emit_col=(1.0, 0.5, 0.6), sss=0.3)
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(brain_m)
bb = brain_m.node_tree.nodes["Principled BSDF"]
for b in BEATS_X:
    for f, e, c in ((b + 11, 0.6, (1.0, 0.5, 0.6)), (b + 14, 6.0, (1.0, 0.08, 0.03)), (b + 22, 0.6, (1.0, 0.5, 0.6))):
        bb.inputs["Emission Strength"].default_value = e; bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
        bb.inputs["Emission Color"].default_value = (*c, 1); bb.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
vis(xbrain, XR_R)
def W(arm, b, f):
    sc.frame_set(f); return arm.matrix_world @ arm.pose.bones["mixamorig:" + b].head
REFX = 242
PATH_B = ("RightHandIndex4", "RightHandIndex2", "RightHand", "RightForeArm", "RightArm", "RightShoulder", "Neck", "Head")
pts = [W(meg, b, REFX).copy() for b in PATH_B]
pts[-1] = pts[-1] + V(0, 0, 0.09)
PAIN = P.pulse_material("pain_pulse", (0.9, 0.08, 0.04), base_emit=0.4, pulse_col=(1.0, 0.1, 0.02), width=0.09)
ppath = P.tube("pain_path", [tuple(p) for p in pts], 0.004, PAIN, None)
for b in BEATS_X:
    val_key(PAIN, "pos", b, -0.1); val_key(PAIN, "pos", b + 13, 1.1)
interp(PAIN.node_tree, "LINEAR")
vis(ppath, XR_R)

# ======================================================================
# 8) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
def rig(name, target):
    e = empty(name + "_rig"); c = e.constraints.new("COPY_LOCATION"); c.target = target; return e
def rel_cam(name, target, lens, fstop, offsets, clip=0.01):
    r_ = rig(name, target)
    c = shot_cam(name, (0, 0, 0), target, lens, fstop, focus=target, clip=clip)
    c.parent = r_
    path_keys(c, offsets)
    return c
HAND_H = V(DW / 2 + 0.0, -0.04, 1.06)
D0, D1 = S["door"]
c = abs_cam("door", [(D0, V(-0.25, -2.0, 0.2)), (F_SLAM, V(0.0, -1.6, 0.3)), (F_SLAM + 3, V(0.12, -1.2, 0.55)), (D1, V(0.14, -1.12, 0.6))],
            [(D0, V(0.3, -0.2, 1.05)), (F_SLAM, HAND_H + V(-0.05, 0, 0)), (D1, HAND_H)], 16, 4.0, clip=0.05)
lens_keys(c, [(D0, 15), (F_SLAM, 17), (F_SLAM + 3, 32), (D1, 34)])
shake(c, F_SLAM, F_SLAM + 10, 0.03, seed=2)
# makro A
sc.frame_set(1); bpy.context.view_layer.update()
NWW = nailW.matrix_world @ V(0, 0.1, 1.0)
HM0, HM1 = S["hammer"]
c = abs_cam("hammer", [(HM0, NWW + V(0.02, -0.34, 0.07)), (F_HIT, NWW + V(0.03, -0.26, 0.045)), (HM1, NWW + V(0.03, -0.24, 0.04))],
            [(HM0, NWW + V(-0.06, 0.02, 0.06)), (F_HIT, NWW + V(-0.02, 0.01, 0.02)), (HM1, NWW + V(-0.01, 0.01, 0.01))], 34, 5.6)
shake(c, F_HIT, F_HIT + 9, 0.006, seed=3)
c = abs_cam("blood", [(B0, NWW + V(0.06, -0.08, 0.06)), (B1, NWW + V(0.03, -0.045, 0.035))], [(B0, NWW + V(0, 0.002, 0)), (B1, NWW + V(0, 0.003, 0))], 50, 16.0)
for b in BEATS:
    if B0 <= b <= B1: shake(c, b, b + 4, 0.0007, seed=b)
# yuz (yo'lak): qiz qo'lini silkitadi
F0, F1 = S["face"]
c = rel_cam("face", faceT, 35, 2.0, [(F0, V(-0.55, -0.3, -0.04)), (F1, V(-0.42, -0.2, -0.02))], clip=0.05)
for b in BEATS:
    if F0 <= b <= F1: shake(c, b, b + 5, 0.012, seed=b)
X0, X1 = S["xray"]
sc.frame_set(REFX); bpy.context.view_layer.update()
CH = (W(meg, "Spine2", REFX) + W(meg, "RightHand", REFX)) / 2
c = abs_cam("xray", [(X0, CH + V(-1.6, -1.0, 0.2)), (X1, CH + V(-1.1, -0.85, 0.15))], [(X0, CH + V(0, 0, 0.05)), (X1, CH + V(0, 0, 0.15))], 30, 0, clip=0.05)
c.data.dof.use_dof = False
# kesim
CF = CUT + V(0, 0.0125, 0.0045) * K
c = abs_cam("tight", [(TI0, CF + V(0.75, -0.3, 0.16)), (TI1, CF + V(0.4, -0.05, 0.04))], [(TI0, CF + V(0, 0.01, -0.01)), (TI1, CF + V(0, 0.0, -0.005))], 30, 8.0)
c = abs_cam("press", [(PR0, CF + V(0.55, 0.2, 0.14)), (PR1, CF + V(0.42, -0.1, 0.06))], [(PR0, CF + V(0, 0.0, -0.01)), (PR1, CF + V(0, 0.0, -0.01))], 32, 8.0)
for f in range(PR0 + 20, PR1 - 5, 14): shake(c, f + 2, f + 7, 0.004, seed=f)
c = abs_cam("nonerve", [(TX0, CF + V(0.34, -0.22, 0.16)), (TX1, CF + V(0.3, -0.12, 0.1))], [(TX0, CF + V(0, 0, 0.02)), (TX1, CF + V(0, 0, 0.01))], 30, 8.0)
c = abs_cam("release", [(RE0, CF + V(0.26, -0.18, 0.12)), (RE1, CF + V(0.4, -0.28, 0.2))], [(RE0, CF + V(0, 0, 0.02)), (RE1, CF + V(0, 0, 0.03))], 30, 8.0)
shake(c, RE0, RE0 + 8, 0.006, seed=9)
# klinika keng plan (pastdan)
C0, C1 = S["clinic"]
c = abs_cam("clinic", [(C0, CL + V(2.1, 0.25, 0.7)), (C1, CL + V(1.9, 0.1, 0.85))], [(C0, CL + V(0.2, 0.05, 1.0)), (C1, CL + V(0.25, 0.0, 1.0))], 13, 4.0, clip=0.05)
# makro B
FP = MCv + FLAME_PT
c = abs_cam("heat", [(HE0, FP + V(0.07, -0.1, 0.06)), (HE1, FP + V(-0.02, -0.09, 0.05))], [(HE0, FP + V(0, 0, 0.004)), (HE1, FP + V(0, 0, 0.0))], 55, 11.0)
NCW = MCv + NC
c = abs_cam("touch", [(TO0, NCW + V(0.05, -0.08, 0.08)), (TO1, NCW + V(0.035, -0.06, 0.045))], [(TO0, NCW + V(0, 0, 0.01)), (TO1, NCW + V(0, 0, 0.004))], 45, 14.0)
c = abs_cam("melt", [(ME0, NCW + V(0.06, -0.05, 0.012)), (ME1, NCW + V(0.035, -0.03, 0.01))], [(ME0, NCW + V(0, 0, 0.006)), (ME1, NCW + V(0, 0, 0.003))], 50, 16.0)
shake(c, F_PIERCE - 2, F_PIERCE + 6, 0.0008, seed=12)
c = abs_cam("fountain", [(FO0, NCW + V(0.08, -0.09, 0.012)), (FO1, NCW + V(0.07, -0.1, 0.03))], [(FO0, NCW + V(0, 0, 0.012)), (FO1, NCW + V(0, 0, 0.02))], 40, 14.0)
shake(c, F_JET, F_JET + 8, 0.0015, seed=13)
# yuz (klinika)
CA0, CA1 = S["calm"]
c = rel_cam("calm", faceT, 40, 2.0, [(CA0, V(-0.3, -0.42, -0.02)), (CA1, V(-0.2, -0.36, -0.01))], clip=0.05)
RL0, RL1 = S["relief"]
c = rel_cam("relief", faceT, 38, 2.4, [(RL0, V(0.25, -0.38, -0.03)), (RL1, V(0.45, -0.75, 0.05))], clip=0.05)
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["door"]

# ======================================================================
# 9) YORUG'LIK va DUNYO
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
def env_bg(img, rotz=0.0):
    env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + img)
    mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(rotz))
    L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
    bg = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg.inputs[0]); return bg
bgH = env_bg("kloofendal_48d_partly_cloudy_puresky.hdr", 120)
bgC = env_bg("hospital_room.hdr", 0)
bgS = env_bg("studio_small_09.hdr", 30)
bgK = N.new("ShaderNodeBackground"); bgK.inputs[0].default_value = (0.006, 0.008, 0.014, 1)
a1 = N.new("ShaderNodeAddShader"); a2 = N.new("ShaderNodeAddShader"); a3 = N.new("ShaderNodeAddShader")
L.new(bgH.outputs[0], a1.inputs[0]); L.new(bgC.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], a2.inputs[0]); L.new(bgS.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], a3.inputs[0]); L.new(bgK.outputs[0], a3.inputs[1]); L.new(a3.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    vals = {"H": 0.35 if n in HALLN else 0.0, "C": (0.8 if n in CLN else 0.6 if n in MCN else 0.0), "S": 0.7 if n in MWN else 0.0,
            "K": 1.0 if n in CUTN + XRN else 0.0}
    for bg, k in ((bgH, "H"), (bgC, "C"), (bgS, "S"), (bgK, "K")):
        bg.inputs[1].default_value = vals[k]; bg.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
HT = empty("hallT", (0.4, -0.3, 1.0))
area("H_ceil", (0.3, -1.2, 2.6), 1.2, (1.0, 0.88, 0.72), lights_for(HALL_R, 120.0), target=HT)
area("H_key", (1.6, -1.6, 1.9), 0.8, (1.0, 0.92, 0.82), lights_for(HALL_R, 90.0), target=HT)
area("H_back", (0.0, 1.8, 2.3), 1.5, (0.9, 0.95, 1.0), lights_for(HALL_R, 120.0), target=empty("hbT", (0, 0, 0.8)))
area("H_rim", (-0.6, -0.9, 1.9), 0.5, (1.0, 0.7, 0.45), lights_for(rng("face"), 40.0), target=faceT)
CT = empty("clinT", tuple(CL + V(0.1, 0.1, 0.9)))
area("C_ceil", tuple(CL + V(0, 0.2, 2.7)), 1.4, (0.95, 0.98, 1.0), lights_for(CL_R, 220.0), target=CT)
area("C_key", tuple(CL + V(-1.0, -1.2, 1.9)), 0.9, (0.9, 0.95, 1.0), lights_for(CL_R, 90.0), target=CT)
area("C_face", tuple(CL + V(0.6, -0.4, 1.4)), 0.4, (1.0, 0.9, 0.82), lights_for(rng("calm", "relief"), 25.0), target=faceT)
MWT = empty("mwT", tuple(MW + V(0, 0.01, 0.01)))
area("W_key", tuple(MW + V(-0.15, -0.25, 0.3)), 0.25, (1.0, 0.93, 0.85), lights_for(MW_R, 9.0), target=MWT)
area("W_fill", tuple(MW + V(0.25, -0.1, 0.12)), 0.2, (0.85, 0.92, 1.0), lights_for(MW_R, 5.0), target=MWT)
area("W_rim", tuple(MW + V(0.05, 0.3, 0.2)), 0.2, (1.0, 0.8, 0.6), lights_for(MW_R, 8.0), target=MWT)
MCT = empty("mcT", tuple(MCv + V(0.03, 0.0, 0.05)))
area("M_key", tuple(MCv + V(-0.2, -0.25, 0.4)), 0.3, (0.95, 0.97, 1.0), lights_for(MC_R, 10.0), target=MCT)
area("M_fill", tuple(MCv + V(0.3, -0.1, 0.15)), 0.2, (1.0, 0.92, 0.85), lights_for(MC_R, 5.0), target=MCT)
area("M_rim", tuple(MCv + V(0.0, 0.35, 0.25)), 0.2, (0.6, 0.8, 1.0), lights_for(MC_R, 9.0), target=MCT)
CTT = empty("cutT", tuple(CF))
area("K_key", tuple(CF + V(0.6, -0.45, 0.45)), 0.7, (1.0, 0.95, 0.9), lights_for(CUT_R, 22.0), target=CTT)
area("K_fill", tuple(CF + V(0.5, 0.3, -0.35)), 0.6, (1.0, 0.85, 0.7), lights_for(CUT_R, 7.0), target=CTT)
area("K_rim", tuple(CF + V(-0.25, -0.55, 0.35)), 0.5, (0.35, 0.6, 1.0), lights_for(CUT_R, 14.0), target=CTT)

# ko'rinish: to'plamlar faqat o'z kadrlarida
vis(hall, HALL_R); vis(clinic, CL_R); vis(mw, MW_R)
vis(cutp, CUT_R, recursive=False)
for o in cut_objs + nerves: vis(o, CUT_R, recursive=False)
for o in cutp.children:
    if o not in cut_objs and o not in nerves: vis(o, CUT_R, recursive=False)
# makro B: tomchilar/oqim allaqachon alohida; qolganlari
for o in [mcs] + [c for c in mcs.children_recursive if not (c.name.startswith("jet") or c.name.startswith("blood_"))]:
    vis(o, MC_R, recursive=False)
vis(smoke, rng("touch", "melt", "fountain"), recursive=False)
vis(toolC, rng("clinic"))
vis(flC, CL_R, recursive=False)

# ======================================================================
# 10) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
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
