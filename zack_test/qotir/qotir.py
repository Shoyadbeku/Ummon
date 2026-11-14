# Qo'tir (yara po'sti) nega qichishadi — Zack D. Films uslubida 39.8 s video (954 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; yordamchilar tirnoq_osishi/tirnoq_osishi.py dan; parts.py = burish/parts.py
# Assetlar: zack_test/tools/get_qotir.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 python3 -I zack_test/qotir/qotir.py --render
# Sinov:  FRAMES=20,50,100,150 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(17)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 954
sc.frame_start, sc.frame_end = 1, END
V = lambda *a: Vector(a)
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


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else float(x >= a); return t * t * (3 - 2 * t)

from mathutils import noise as mnoise
from mathutils.bvhtree import BVHTree
mn = P.math_n
# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "fall"), (37, "scrape"), (63, "scab"), (116, "itch"), (176, "scratch"), (230, "noinf"), (287, "heal"), (345, "reveal"),
         (404, "under"), (457, "crawl"), (512, "link"), (559, "pull"), (627, "tension"), (675, "hist"), (744, "nerve"),
         (784, "tickle"), (862, "brain"), (916, "end")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
MACN = ("scrape", "scab", "scratch", "noinf", "heal")
CUTN = ("reveal", "under", "crawl", "link", "pull", "tension", "hist", "nerve", "tickle")
ROOMN = ("itch", "end"); STRN = ("fall",); XRN = ("brain",)
MAC_R = rng(*MACN); CUT_R = rng(*CUTN); ROOM_R = rng(*ROOMN); STR_R = rng(*STRN); XR_R = rng(*XRN)
F_IMPACT = 24                    # yerga uriladi
F_ITCH = 147                     # "qichish" — crash zoom
F_TOUCH = 204                    # tirnoq qo'tirga tegadi
F_NO = 262                       # "infeksiya emas" — taqiq belgisi
F_LINK = 549                     # "ulanadi" — ikki front uchrashadi
F_ARRIVE = 896                   # signal miyaga yetadi

def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.01):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
def emis(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission"); e.name = "E"
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    L.new(e.outputs[0], N["Material Output"].inputs[0]); return m
def obj_new(name, me, parent=None, m=None):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    if parent: o.parent = parent
    if m: o.data.materials.append(m)
    return o
def maprange(N, L, src, a, b, c=1.0, d=0.0):
    n = N.new("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"
    n.inputs["From Min"].default_value = a; n.inputs["From Max"].default_value = b
    n.inputs["To Min"].default_value = c; n.inputs["To Max"].default_value = d
    L.new(src, n.inputs["Value"]); return n.outputs["Result"]
def mixc(N, L, fac, a, b):
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    for sock, x in ((mx.inputs["Factor"], fac), (mx.inputs[6], a), (mx.inputs[7], b)):
        if isinstance(x, (int, float)): sock.default_value = x
        elif isinstance(x, tuple): sock.default_value = (*x, 1)
        else: L.new(x, sock)
    return mx.outputs[2]

floor_m = pbr("floor", "laminate_floor_02", 0.5)

# ======================================================================
# QO'TIR materiali (makro va kesimda): "dry" 0 = yangi qon, 1 = qotgan qora qo'tir
# ======================================================================
def scab_mat(name, vscale=45.0, dry=1.0, bump_d=0.006):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); O = tc.outputs["Object"]
    dv = value_node(m, "dry", dry)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = vscale * 0.55; nz.inputs["Detail"].default_value = 5.0; L.new(O, nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.004, 0.002, 0.002, 1)
    cr.color_ramp.elements[1].position = 0.8; cr.color_ramp.elements[1].color = (0.04, 0.011, 0.007, 1)
    L.new(mixc(N, L, dv, (0.36, 0.006, 0.006), cr.outputs[0]), b.inputs["Base Color"])
    L.new(mn(N, L, "ADD", mn(N, L, "MULTIPLY", dv, 0.72), 0.1), b.inputs["Roughness"])
    L.new(mn(N, L, "MULTIPLY", mn(N, L, "SUBTRACT", 1.0, dv), 0.7), b.inputs["Coat Weight"]); b.inputs["Coat Roughness"].default_value = 0.05
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = vscale; L.new(O, vo.inputs["Vector"])
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = vscale * 3; L.new(O, nz2.inputs["Vector"])
    h = mn(N, L, "ADD", mn(N, L, "MINIMUM", vo.outputs["Distance"], 0.12), mn(N, L, "MULTIPLY", nz2.outputs["Fac"], 0.05))
    bp = N.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = bump_d; L.new(h, bp.inputs["Height"])
    L.new(mn(N, L, "MULTIPLY", dv, 0.55), bp.inputs["Strength"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
RING_M = emis("itch_ring", (1.0, 0.07, 0.04), 2.3)
def itch_rings(name, parent, frames, s0, s1, loc=(0, 0, 0), dur=14, aspect=(1.0, 1.0), minor=0.04):
    for i, f in enumerate(frames):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=minor, major_segments=64, minor_segments=8)
        o = bpy.context.object; o.name = f"{name}{i}"; o.data.materials.append(RING_M); o.parent = parent; o.location = loc
        key(o, f, scale=(s0 * aspect[0], s0 * aspect[1], s0)); key(o, f + dur, scale=(s1 * aspect[0], s1 * aspect[1], s0 * 0.25))
        interp(o, "LINEAR"); vis(o, [(f, f + dur)])

# ======================================================================
# 1) MAKRO TERI (10x): bilak terisi, shilinish -> qon -> qora qo'tir, barmoq, bakteriya
# ======================================================================
MF = V(-30, -40, 0)
mf = empty("MACRO", tuple(MF))
RAD = 0.45; WA, WB = 0.125, 0.062
def skin_z(x): return math.sqrt(max(1e-6, RAD * RAD - x * x)) - RAD
def macro_skin():
    m = bpy.data.materials.new("mskin"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); O = tc.outputs["Object"]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0; nz.inputs["Detail"].default_value = 5.0; L.new(O, nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = (0.6, 0.33, 0.25, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (0.72, 0.43, 0.34, 1)
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / WA, 1 / WB, 0.0); L.new(O, mp.inputs[0])
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 16.0; L.new(O, nz2.inputs["Vector"])
    w = mn(N, L, "MULTIPLY", mn(N, L, "SUBTRACT", nz2.outputs["Color"], (0.5, 0.5, 0.5), vec=True), (0.55, 0.55, 0.0), vec=True)
    d = mn(N, L, "LENGTH", mn(N, L, "ADD", mp.outputs[0], w, vec=True), vec=True)
    redv = value_node(m, "red", 0.0); rawv = value_node(m, "raw", 0.0)
    red = mn(N, L, "MULTIPLY", maprange(N, L, d, 0.7, 2.6), redv)
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Y"; wv.inputs["Scale"].default_value = 26.0
    wv.inputs["Distortion"].default_value = 2.5; wv.inputs["Detail"].default_value = 2.0; L.new(O, wv.inputs["Vector"])
    raw = mn(N, L, "MULTIPLY", mn(N, L, "MULTIPLY", maprange(N, L, d, 0.8, 1.12), rawv), mn(N, L, "ADD", mn(N, L, "MULTIPLY", wv.outputs["Fac"], 0.6), 0.4), clamp=True)
    c1 = mixc(N, L, mn(N, L, "MULTIPLY", red, 0.75), cr.outputs[0], (0.80, 0.24, 0.2))
    L.new(mixc(N, L, raw, c1, (0.42, 0.012, 0.012)), b.inputs["Base Color"])
    L.new(mn(N, L, "SUBTRACT", 0.5, mn(N, L, "MULTIPLY", raw, 0.33)), b.inputs["Roughness"])
    L.new(mn(N, L, "MULTIPLY", raw, 0.5), b.inputs["Coat Weight"])
    b.inputs["Subsurface Weight"].default_value = 0.25; b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.18)
    b.inputs["Subsurface Scale"].default_value = 0.008
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 75.0; L.new(O, vo.inputs["Vector"])
    h = mn(N, L, "SUBTRACT", mn(N, L, "MINIMUM", vo.outputs["Distance"], 0.1), mn(N, L, "MULTIPLY", raw, 0.12))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.45; bp.inputs["Distance"].default_value = 0.008
    L.new(h, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
MSKIN = macro_skin()
NA, NY = 121, 81
vs = []; fs = []
for j in range(NY):
    y = -1.4 + 2.8 * j / (NY - 1)
    for i in range(NA):
        a = R(-115 + 230 * i / (NA - 1)); vs.append((RAD * math.sin(a), y, RAD * math.cos(a) - RAD))
for j in range(NY - 1):
    for i in range(NA - 1):
        k = j * NA + i; fs.append((k, k + 1, k + NA + 1, k + NA))
me = bpy.data.meshes.new("arm_skin"); me.from_pydata(vs, [], fs); me.update(); me.shade_smooth()
arm_skin = obj_new("arm_skin", me, mf, MSKIN)
plane("m_cloth", (12, 12), (0, 0, -0.62), mat("cloth", (0.62, 0.66, 0.7), 0.9), parent=mf)
box("m_back", (14, 0.1, 8), (0, 4.5, 2.0), mat("mback", (0.5, 0.6, 0.66), 0.9), parent=mf)
box("m_backL", (0.1, 12, 8), (-5.5, 0, 2.0), mat("mback2", (0.5, 0.6, 0.66), 0.9), parent=mf)
box("m_backR", (0.1, 12, 8), (5.5, 0, 2.0), mat("mback3", (0.5, 0.6, 0.66), 0.9), parent=mf)

def disk_mesh(name, hfun, sx=1.0, NR=28, NT=96):
    """qo'tir shakli: notekis ellips; hfun(r, x, y) -> balandlik (teri ustidan)"""
    vs = [(0, 0, hfun(0, 0, 0))]; fs = []
    for i in range(1, NR + 1):
        r = i / NR
        for j in range(NT):
            t = 2 * math.pi * j / NT
            ro = 1 + 0.07 * math.sin(3 * t + 1) + 0.06 * math.sin(7 * t + 2) + 0.04 * math.sin(13 * t) + 0.03 * math.sin(23 * t + 1)
            x = WA * sx * ro * r * math.cos(t); y = WB * sx * ro * r * math.sin(t)
            vs.append((x, y, skin_z(x) + hfun(r, x, y)))
    for j in range(NT): fs.append((0, 1 + j, 1 + (j + 1) % NT))
    for i in range(NR - 1):
        b0 = 1 + i * NT; b1 = b0 + NT
        for j in range(NT): fs.append((b0 + j, b1 + j, b1 + (j + 1) % NT, b0 + (j + 1) % NT))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.shade_smooth()
    return me
def h_scab(r, x, y): return 0.015 * (1 - r ** 4) ** 0.7 + 0.005 * mnoise.noise(V(x * 50, y * 50, 1.7)) * (1 - r ** 4) + 0.006 * mnoise.noise(V(x * 22, y * 22, 0.3)) * (1 - r * r) - 0.0015
def h_blood(r, x, y): return 0.007 * (1 - r ** 4) - 0.0015
MSCAB_M = scab_mat("mscab", 80.0, dry=0.0, bump_d=0.004)
mscab = obj_new("mscab", disk_mesh("mscab", h_scab), mf, MSCAB_M)
mscab.shape_key_add(name="Basis"); kb = mscab.shape_key_add(name="blood", from_mix=False); kb.value = 0.0
_bm = disk_mesh("tmp_blood", h_blood)
for i, v in enumerate(_bm.vertices): kb.data[i].co = v.co
bpy.data.meshes.remove(_bm)
def kbv(f, v): kb.value = v; kb.keyframe_insert("value", frame=f)
NEW_M = mat("newskin", (0.9, 0.42, 0.42), 0.4, coat=0.1, sss=0.3)
NEW_M.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.006
newskin = obj_new("newskin", disk_mesh("newskin", lambda r, x, y: 0.0025 * (1 - r ** 6), sx=1.02), mf, NEW_M)
vis(newskin, rng("heal"))
SR0, SR1 = S["scrape"]; SB0, SB1 = S["scab"]; HE0, HE1 = S["heal"]
for f, v in ((1, 0.0), (SR0, 0.0), (SR0 + 7, 1.0), (SB0, 1.0), (SB0 + 30, 0.35), (END, 0.35)): val_key(MSKIN, "raw", f, v)
for f, v in ((1, 0.0), (SR0, 0.1), (SR1, 0.6), (SB1, 0.95), (HE0, 0.95), (HE1, 0.4)): val_key(MSKIN, "red", f, v)
for f, v in ((1, 0.0), (SB0 + 3, 0.0), (SB0 + 42, 1.0)): val_key(MSCAB_M, "dry", f, v)
for f, v in ((1, 1.0), (SB0, 1.0), (SB0 + 32, 0.0)): kbv(f, v)
for f, s in ((1, 0.0), (SR0 + 5, 0.0), (SR0 + 7, 0.3), (SR1, 0.82), (SB0, 0.86), (SB0 + 30, 1.0), (HE0, 1.0), (HE1, 0.8)):
    key(mscab, f, scale=(max(s, 0.001), max(s, 0.001), 1.0))
for idb in (MSKIN.node_tree, MSCAB_M.node_tree, mscab, mscab.data.shape_keys): interp(idb, "LINEAR")
# qon tomchilari (shilingan zahoti)
BLOOD_M = mat("blood", (0.4, 0.006, 0.006), 0.08, coat=0.8, sss=0.1)
rb = random.Random(3)
for i in range(11):
    t = rb.uniform(0, 2 * math.pi); rr = rb.uniform(0.25, 0.95)
    x = WA * rr * math.cos(t); y = WB * rr * math.sin(t); r_ = rb.uniform(0.007, 0.014)
    d = P.droplet(f"bead{i}", (x, y, skin_z(x) + r_ * 0.3), r_, mf, BLOOD_M, squash=0.6)
    f0 = SR0 + 6 + i
    key(d, 1, scale=(0.001,) * 3); key(d, f0, scale=(0.001,) * 3); key(d, f0 + 9, scale=(1, 1, 0.6)); interp(d, "LINEAR"); vis(d, rng("scrape"))
# qichish halqalari (makro)
ringE = empty("m_ringE", (0, 0, 0.03), mf)
itch_rings("mring", ringE, [SB1 - 22, SB1 - 10] + list(range(S["scratch"][0], S["scratch"][1] - 10, 13)), 0.9, 2.1, aspect=(WA * 1.25, WB * 1.9), minor=0.016)
for o in ringE.children:
    o.scale.z = 0.15
# barmoqlar (qashish): uchi (0,0,0), tanasi +Y, tirnoq +Z; 10x
SC0, SC1 = S["scratch"]
fingE = empty("fingers", (0, 0, 0), mf); fingE.rotation_euler = (R(52), 0, R(-28))
FSKIN = P.skin_material("fing_skin", (0.78, 0.5, 0.4), prints=False)
for i, (dx, dz, ln) in enumerate(((0.0, 0.0, 0.085), (0.19, 0.035, 0.09))):
    fe = empty(f"fing{i}_e", (dx, 0, dz), fingE); fe.scale = (10, 10, 10)
    fg = P.build_finger(f"fing{i}", fe, r=0.0078, length=ln, skin=FSKIN)
TIP = V(WA * 0.55, -WB * 0.75, skin_z(WA * 0.55) + 0.024)
fk = [(SC0, TIP + V(0.25, 0.2, 0.42)), (SC0 + 16, TIP + V(0.06, 0.03, 0.08)), (F_TOUCH - 6, TIP + V(0.04, 0.02, 0.05)), (F_TOUCH, TIP)]
for k, f in enumerate(range(F_TOUCH + 4, SC1 + 2, 4)):
    fk.append((f, TIP + V(-0.07 if k % 2 == 0 else 0.0, 0.012 if k % 2 == 0 else 0.0, 0.0)))
path_keys(fingE, fk); interp(fingE, "BEZIER")
rs = random.Random(8)
for f in range(SC0 + 17, F_TOUCH - 6, 2):                       # ikkilanib titrash
    key(fingE, f, loc=tuple(TIP + V(0.05, 0.025, 0.06) + V(rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(-1, 1)) * 0.006))
vis(fingE, rng("scratch"))
# bakteriyalar + taqiq belgisi ("infeksiya emas")
NI0, NI1 = S["noinf"]
BACT_M = mat("bact", (0.3, 0.75, 0.15), 0.45, emit=0.5, emit_col=(0.35, 0.9, 0.15), sss=0.2)
bactE = empty("bactE", (0, 0, 0), mf)
for i in range(16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0)
    o = bpy.context.object; o.name = f"bact{i}"; o.data.materials.append(BACT_M); o.parent = bactE
    for p in o.data.polygons: p.use_smooth = True
    p0 = V(rs.uniform(-0.17, 0.17), rs.uniform(-0.1, 0.06), rs.uniform(0.07, 0.24)); dr = V(rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(-0.5, 0.5)) * 0.03
    s = rs.uniform(0.011, 0.017); o.rotation_euler = (rs.uniform(0, 3), rs.uniform(0, 3), rs.uniform(0, 3))
    key(o, NI0, loc=tuple(p0 - dr), scale=(s, s, s * 2.6)); key(o, F_NO + 4, loc=tuple(p0 + dr * 0.4), scale=(s, s, s * 2.6))
    key(o, F_NO + 14 + i % 5, loc=tuple(p0 + dr + V(dr.x, dr.y, 0.0) * 4), scale=(0.0005,) * 3); interp(o, "LINEAR")
NO_M = emis("no_sign", (1.0, 0.06, 0.04), 2.4)
noE = empty("noE", (0, -0.06, 0.15), mf)
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.02, major_segments=64, minor_segments=10)
o = bpy.context.object; o.name = "no_ring"; o.data.materials.append(NO_M); o.parent = noE
o = box("no_bar", (0.4, 0.04, 0.03), (0, 0, 0), NO_M, parent=noE); o.rotation_euler = (0, 0, R(-45))
key(noE, 1, scale=0.001); key(noE, F_NO - 1, scale=0.001); key(noE, F_NO + 3, scale=0.62); key(noE, F_NO + 6, scale=0.5); key(noE, NI1, scale=0.54)
interp(noE, "LINEAR")
vis(bactE, rng("noinf")); vis(noE, [(F_NO, NI1)])

# ======================================================================
# 2) TERI KESIMI (CUT): epidermis, derma, yog'; yara, qo'tir, o'rmalovchi hujayralar, tolalar, gistamin, asab
# ======================================================================
CUT = V(40, -80, 0)
cutp = empty("CUTP", tuple(CUT))
W0 = 0.5; DEP = 1.0
def tissue(name, c1, c2, nscale=8.0, vscale=30.0, coat=0.3, rough=0.45, bump=0.3, edge=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); O = tc.outputs["Object"]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = nscale; nz.inputs["Detail"].default_value = 4.0; L.new(O, nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = (*c1, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (*c2, 1)
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = vscale; L.new(O, vo.inputs["Vector"])
    col = cr.outputs[0]
    if edge: col = mixc(N, L, maprange(N, L, vo.outputs["Distance"], 0.0, 0.07), col, edge)
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough; b.inputs["Coat Weight"].default_value = coat
    b.inputs["Subsurface Weight"].default_value = 0.2; b.inputs["Subsurface Scale"].default_value = 0.04
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.02
    L.new(mn(N, L, "MINIMUM", vo.outputs["Distance"], 0.15), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
DERM_M = tissue("dermis", (0.7, 0.24, 0.26), (0.84, 0.4, 0.4), 5.0, 22.0, bump=0.2)
FAT_M = tissue("fat", (0.93, 0.72, 0.28), (0.97, 0.82, 0.42), 3.0, 5.5, coat=0.5, bump=0.8, edge=(0.8, 0.5, 0.2))
EPI_M = tissue("epi", (0.86, 0.6, 0.5), (0.92, 0.7, 0.6), 6.0, 34.0, coat=0.15, bump=0.35, edge=(0.66, 0.38, 0.32))
BED_M = tissue("bed", (0.5, 0.04, 0.05), (0.72, 0.12, 0.12), 9.0, 26.0, coat=0.8, rough=0.25, bump=0.7)
box("c_fat", (4.6, DEP, 0.95), (0, DEP / 2, -1.425), FAT_M, parent=cutp)
box("c_musc", (4.6, DEP, 0.9), (0, DEP / 2, -2.35), tissue("muscle", (0.42, 0.06, 0.07), (0.6, 0.13, 0.12), 3.0, 14.0, coat=0.4, bump=0.5), parent=cutp)
box("c_derm", (4.6, DEP, 0.95), (0, DEP / 2, -0.475), DERM_M, parent=cutp)
EL = empty("epiL", (0, 0, 0), cutp); ER = empty("epiR", (0, 0, 0), cutp); WG = empty("woundG", (0, 0, 0), cutp); SCG = empty("scabG", (0, 0, 0), cutp)
box("c_epiL", (1.8, DEP, 0.13), (-W0 - 0.9, DEP / 2, 0.065), EPI_M, parent=EL, bevel=0.03)
box("c_epiR", (1.8, DEP, 0.13), (W0 + 0.9, DEP / 2, 0.065), EPI_M, parent=ER, bevel=0.03)
box("c_bed", (2 * W0 + 0.5, DEP - 0.002, 0.14), (0, DEP / 2 + 0.001, -0.05), BED_M, parent=WG)
# qo'tir (kesilgan gumbaz)
CSCAB_M = scab_mat("cscab", 11.0, 1.0, bump_d=0.025)
CSCAB_IN = tissue("cscab_in", (0.05, 0.004, 0.004), (0.13, 0.014, 0.01), 14.0, 40.0, coat=0.1, rough=0.7, bump=0.6)
CSCAB_IN.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.0
WS = W0 + 0.2
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=72, v_segments=36, radius=1.0)
for v in bm.verts:
    if v.co.z < -0.3: v.co.z = -0.3 + (v.co.z + 0.3) * 0.2
    n = mnoise.noise(v.co * 5.0) * 0.07 + mnoise.noise(v.co * 13.0) * 0.03
    v.co += v.co.normalized() * n * (1.0 if v.co.z > -0.25 else 0.2)
    v.co.x *= WS; v.co.y = v.co.y * 0.62 + 0.5; v.co.z = 0.19 + v.co.z * 0.16
res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0.03, 0), plane_no=(0, -1, 0), clear_outer=True)
ed = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
for f in bm.faces: f.smooth = True
ff = bmesh.ops.edgeloop_fill(bm, edges=ed, mat_nr=1)
for f in ff["faces"]: f.smooth = False
me = bpy.data.meshes.new("cscab"); bm.to_mesh(me); bm.free()
for p_ in me.polygons: p_.use_smooth = (p_.material_index == 0)
cscab = obj_new("cscab", me, SCG, CSCAB_M); cscab.data.materials.append(CSCAB_IN)
# yangi hujayralar: ikki chetdan konveyerdek chiqib, o'rtada uchrashadi
CELL_M = mat("cell", (0.95, 0.56, 0.55), 0.3, coat=0.4, sss=0.4, emit=0.04, emit_col=(1.0, 0.6, 0.55))
CELL_M.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.01
NUC_M = mat("nucleus", (0.45, 0.12, 0.4), 0.35, coat=0.3)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0); _c = bpy.context.object; cell_me = _c.data; cell_me.shade_smooth()
bpy.data.objects.remove(_c)
NCOL = 12; STEP = W0 / NCOL; CR = 0.0235
CR0, LK1 = S["crawl"][0], S["link"][1]
def sheet(f): return (W0 - 0.5 * STEP) * (0.08 * smooth(440, CR0, f) + 0.92 * ((f - CR0) / (F_LINK - CR0) if CR0 <= f <= F_LINK else float(f > F_LINK)))
rc = random.Random(11); CELLS = []
for side in (-1, 1):
    for row, y in enumerate((-0.03, 0.035)):
        for lay, z in enumerate((0.045, 0.088)):
            for j in range(NCOL):
                o = obj_new(f"cell{side}_{row}{lay}_{j}", cell_me, WG); 
                if not cell_me.materials: cell_me.materials.append(CELL_M)
                nu = obj_new(o.name + "n", cell_me, o); nu.location = (rc.uniform(-0.25, 0.25), -0.72, rc.uniform(-0.2, 0.2)); nu.scale = (0.42,) * 3
                nu.material_slots[0].link = "OBJECT"; nu.material_slots[0].material = NUC_M
                CELLS.append((o, side, y + rc.uniform(-0.006, 0.006), z, j + (0.5 if lay else 0.0), rc.uniform(0, 6.28)))
for o, side, y, z, jb, ph in CELLS:
    for f in list(range(436, F_LINK + 8, 2)) + [END]:
        x = W0 - sheet(f) + jb * STEP
        out = x > W0 + 0.01
        wob = 0.0 if f > F_LINK + 4 else 1.0
        s = 0.001 if out else CR
        o.location = (side * x, y, z + wob * 0.005 * math.sin(f * 0.7 + ph)); o.keyframe_insert("location", frame=f)
        o.scale = (s * (1.12 + wob * 0.22 * math.sin(f * 0.55 + ph)), s, s * (0.88 - wob * 0.12 * math.sin(f * 0.55 + ph))); o.keyframe_insert("scale", frame=f)
    interp(o, "LINEAR")
# uchrashganda chaqnash
FL_M = emis("flash", (1.0, 0.85, 0.7), 6.0)
flash = sphere("link_flash", 1.0, (0, -0.05, 0.065), FL_M, parent=WG)
key(flash, F_LINK - 1, scale=0.001); key(flash, F_LINK + 2, scale=(0.09, 0.03, 0.09)); key(flash, F_LINK + 8, scale=(0.5, 0.01, 0.012)); interp(flash, "LINEAR")
vis(flash, [(F_LINK, F_LINK + 8)])
# tortilish: yara 38% qisqaradi
PU0, PU1 = S["pull"]; PE = PU1 - 6; SHR = 0.62
for f, k in ((1, 0.0), (PU0 + 4, 0.0), (PE, 1.0)):
    key(WG, f, scale=(1 - (1 - SHR) * k, 1, 1)); key(SCG, f, scale=(1 - 0.27 * k, 1, 1 + 0.12 * k))
    key(EL, f, loc=(W0 * (1 - SHR) * k, 0, 0)); key(ER, f, loc=(-W0 * (1 - SHR) * k, 0, 0))
ARR_M = emis("arrow", (1.0, 0.9, 0.55), 2.2)
for side in (-1, 1):
    ae = empty(f"arrow{side}", (0, 0, 0), cutp); ae.rotation_euler = (0, 0, 0 if side < 0 else R(180))
    box(f"arr_s{side}", (0.3, 0.06, 0.06), (-0.15, 0, 0), ARR_M, parent=ae)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.11, depth=0.18); c = bpy.context.object; c.name = f"arr_h{side}"
    c.data.materials.append(ARR_M); c.parent = ae; c.rotation_euler = (0, R(90), 0); c.location = (0.07, 0, 0)
    for k in range(3):
        f0 = PU0 + 4 + k * 20
        key(ae, f0, loc=(side * 0.62, -0.12, 0.52)); key(ae, f0 + 19, loc=(side * 0.34, -0.12, 0.52))
    interp(ae, "LINEAR"); vis(ae, [(PU0 + 4, PU1)])
# tortuvchi tolalar (miofibroblast): osilib turadi -> taranglashadi -> titraydi
TE0, TE1 = S["tension"]
FIB_M = mat("fibre", (0.95, 0.5, 0.45), 0.3, coat=0.4, emit=0.25, emit_col=(1.0, 0.45, 0.3))
_fe = FIB_M.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.25), (PU0, 0.25), (PE, 0.9), (TE0, 0.9), (TE0 + 10, 2.0), (TE1, 2.2), (TE1 + 1, 0.6)): P.key_socket(_fe, f, v)
FIBS = []
for i in range(11):
    z0 = -0.16 - 0.035 * i + rc.uniform(-0.01, 0.01); Lh = W0 + 0.42 - 0.02 * i; sag = rc.uniform(0.07, 0.13)
    pts = [(-Lh, 0, 0), (-Lh * 0.5, 0, -sag * 0.8), (0, 0, -sag), (Lh * 0.5, 0, -sag * 0.8), (Lh, 0, 0)]
    t = P.tube(f"fibre{i}", pts, 0.013, FIB_M, cutp); t.location = (0, -0.02 - 0.004 * (i % 3), z0)
    key(t, 1, scale=(1, 1, 1)); key(t, PU0 + 4, scale=(1, 1, 1)); key(t, PE, scale=(0.82, 1, 0.06)); interp(t, "LINEAR")
    for f in range(TE0, TE1 + 1):
        a = 0.009 * (1 if (f + i) % 2 else -1) * (0.4 + 0.6 * abs(math.sin((f - TE0) * 0.25 + i)))
        t.location.z = z0 + a; t.keyframe_insert("location", index=2, frame=f)
    t.location.z = z0; t.keyframe_insert("location", index=2, frame=TE0 - 1); t.keyframe_insert("location", index=2, frame=TE1 + 1)
    FIBS.append(t)
# qon tomirlari
VES_R = mat("vessel_r", (0.7, 0.04, 0.05), 0.3, coat=0.5); VES_B = mat("vessel_b", (0.2, 0.25, 0.65), 0.3, coat=0.5)
P.tube("art", [(-2.3, -0.03, -0.78), (-1.0, -0.05, -0.72), (0.2, -0.05, -0.82), (1.2, -0.04, -0.74), (2.3, -0.03, -0.8)], 0.035, VES_R, cutp)
P.tube("vein", [(-2.3, -0.03, -0.9), (-0.8, -0.04, -0.93), (0.4, -0.04, -0.88), (2.3, -0.03, -0.92)], 0.04, VES_B, cutp)
for i, x in enumerate((-1.25, -0.82, 0.86, 1.3)):
    P.tube(f"cap{i}", [(x, -0.04, -0.75), (x + 0.06, -0.04, -0.4), (x - 0.03, -0.04, -0.1), (x + 0.07, -0.04, -0.08), (x + 0.1, -0.04, -0.42), (x + 0.12, -0.04, -0.75)], 0.012, VES_R, cutp)
# semiz hujayralar (gistamin manbai) + gistamin donachalari
HI0, HI1 = S["hist"]; NV0, NV1 = S["nerve"]; TK0, TK1 = S["tickle"]
MAST_M = tissue("mast", (0.5, 0.28, 0.7), (0.72, 0.5, 0.88), 20.0, 60.0, coat=0.5, rough=0.3, bump=0.9)
NERVE_X = (-0.2, 0.06, 0.3)
NEND = [V(x, -0.05, -0.26 - 0.03 * (i % 2)) for i, x in enumerate(NERVE_X)]
MASTS = [V(-0.42, -0.03, -0.38), (V(-0.07, -0.03, -0.5)), V(0.18, -0.03, -0.44), V(0.48, -0.03, -0.33), V(-0.3, -0.03, -0.62), V(0.4, -0.03, -0.6)]
HIST_M = emis("histamine", (1.0, 0.8, 0.12), 5.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0); _c = bpy.context.object; gr_me = _c.data; gr_me.shade_smooth(); gr_me.materials.append(HIST_M)
bpy.data.objects.remove(_c)
histE = empty("histE", (0, 0, 0), cutp)
for i, c in enumerate(MASTS):
    ms = sphere(f"mast{i}", 0.07, tuple(c), MAST_M, parent=cutp)
    for f in range(HI0, TK1 + 1, 6):
        s = 1.0 + 0.1 * math.sin(f * 0.5 + i); key(ms, f, scale=(s, s, s))
    for g in range(13):
        tgt = min(NEND, key=lambda p: (p - c).length) if g % 2 == 0 else c + V(rc.uniform(-1, 1), 0, rc.uniform(-0.6, 1)).normalized() * 0.35
        d = tgt - c + V(rc.uniform(-0.04, 0.04), 0, rc.uniform(-0.04, 0.04)); d.y = -0.03 + rc.uniform(-0.02, 0.01)
        o = obj_new(f"gran{i}_{g}", gr_me, histE); ph = rc.random(); per = rc.uniform(30, 44); r_ = rc.uniform(0.014, 0.022)
        for f in range(HI0 - 2, TK1 + 2, 3):
            t = ((f - HI0) / per + ph) % 1.0
            tn = ((f + 3 - HI0) / per + ph) % 1.0
            s = r_ * max(0.02, math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6)
            o.location = c + d * t + V(0, 0, 0.012 * math.sin(t * 9 + g)); o.keyframe_insert("location", frame=f)
            o.scale = (s, s, s) if tn > t else (0.0001,) * 3; o.keyframe_insert("scale", frame=f)
        interp(o, "LINEAR")
vis(histE, [(HI0, TK1)])
# asab tolalari: uzilgan uchlar (yara ostida), impuls pastga (miyaga) qarab yuradi
NPLAIN = mat("nerve_plain", (1.0, 0.62, 0.08), 0.35, coat=0.3, emit=0.3, emit_col=(1.0, 0.6, 0.1))
SPARK_M = emis("spark", (1.0, 0.95, 0.6), 14.0)
NMATS = []
for i, (x0, e) in enumerate(zip(NERVE_X, NEND)):
    nm = P.pulse_material(f"nerve{i}", (1.0, 0.62, 0.08), 0.3, (1.0, 0.8, 0.3), width=0.07); NMATS.append(nm)
    pts = [tuple(e), (x0 + 0.06, -0.05, -0.5), (x0 - 0.07, -0.05, -0.82), (x0 + 0.03, -0.05, -1.12), (x0 - 0.02, -0.04, -1.7), (x0 + 0.04, -0.04, -2.8)]
    P.tube(f"nerve{i}", pts, 0.022, nm, cutp)
    for k in range(5):                                         # titilgan (uzilgan) uch
        a = R(-60 + 30 * k + rc.uniform(-8, 8)); ln = rc.uniform(0.045, 0.075)
        P.tube(f"fray{i}_{k}", [tuple(e + V(0, 0, -0.01)), tuple(e + V(math.sin(a) * ln * 0.5, -0.01, ln * 0.6)), tuple(e + V(math.sin(a) * ln, -0.02 * (k % 2), ln))], 0.006, NPLAIN, cutp)
    top = V(x0 + 0.015, -0.05, -0.115)
    P.tube(f"stub{i}", [tuple(top), tuple(top + V(0.01, 0, -0.03)), tuple(top + V(-0.005, 0, -0.055))], 0.018, NPLAIN, cutp)
    for k in range(3):
        a = R(-40 + 40 * k); b_ = top + V(-0.005, 0, -0.05)
        P.tube(f"sfray{i}_{k}", [tuple(b_), tuple(b_ + V(math.sin(a) * 0.03, -0.01, -0.035))], 0.005, NPLAIN, cutp)
    sp = sphere(f"spark{i}", 1.0, tuple(e + V(0, -0.02, 0.07)), SPARK_M, sub=2, parent=cutp)
    key(sp, 1, scale=0.0001)
    f = NV0 + 4 + i * 5
    while f < TK1 - 4:
        big = f >= TK0
        key(sp, f - 1, scale=0.0001); key(sp, f + 1, scale=(0.05 if big else 0.028)); key(sp, f + 4, scale=0.0001)
        if big:
            for ff_, v in ((f, -0.08), (f + 15, 1.1), (f + 16, -1.0)): val_key(nm, "pos", ff_, v)
        f += (17 if big else 11) + (i * 3) % 5
    interp(sp, "LINEAR"); interp(nm.node_tree, "LINEAR")
for i, x in enumerate((-1.5, -1.05, 1.1, 1.6)):
    P.tube(f"nerve_ok{i}", [(x, -0.04, 0.02), (x + 0.05, -0.04, -0.3), (x - 0.05, -0.04, -0.7), (x + 0.02, -0.04, -1.6), (x - 0.03, -0.04, -2.8)], 0.02, NPLAIN, cutp)

# ======================================================================
# 3) XONA (0,0,0): divan; Megan o'tirib bilagini qashiydi
# ======================================================================
room = empty("ROOM")
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.88, 0.84, 0.78))
plane("r_floor", (7, 7), (0, -1.0, 0), floor_m, parent=room)
box("r_wallB", (7, 0.12, 2.8), (0, 0.85, 1.4), wall_m, parent=room)
box("r_wallL", (0.12, 6, 2.8), (-2.4, -1.5, 1.4), wall_m, parent=room)
box("r_wallR", (0.12, 6, 2.8), (2.6, -1.5, 1.4), wall_m, parent=room)
box("r_ceil", (7, 7, 0.05), (0, -1.0, 2.82), mat("ceil", (0.9, 0.9, 0.88), 0.8), parent=room)
box("r_base", (7, 0.02, 0.1), (0, 0.78, 0.05), mat("trim", (0.92, 0.92, 0.9), 0.35), parent=room)
plane("r_window", (1.2, 1.3), (-2.33, -0.9, 1.5), mat("rwin", (1, 1, 1), emit=4.0, emit_col=(0.9, 0.95, 1.0)), rot=(90, 0, 90), parent=room)
sofa = import_gltf(PH + "Sofa_01/Sofa_01.gltf", (0, 0.33, 0), (0, 0, 0), 1.22, parent=room)
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-1.25, -0.9, 0), (0, 0, 90), 1.0, parent=room)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-1.5, 0.45, 0), (0, 0, 20), 1.1, parent=room)
plane("r_rug", (2.2, 1.6), (0.2, -0.75, 0.002), mat("rug", (0.36, 0.42, 0.5), 0.95), parent=room)
sc.frame_set(1); bpy.context.view_layer.update()
SEAT_Z = 0.5
hit = sc.ray_cast(bpy.context.view_layer.depsgraph, V(0.0, 0.1, 0.8), V(0, 0, -1))
if hit[0]: SEAT_Z = hit[1].z
print("SEAT_Z", SEAT_Z)

# ======================================================================
# 4) KO'CHA (20,0,0): yo'l, trotuar, binolar — Megan yugurib kelib yiqiladi
# ======================================================================
ST = V(20, 0, 0)
street = empty("STREET", tuple(ST))
plane("s_walk", (4.0, 160), (0, 0, 0.14), pbr("pav", "concrete_pavement", 0.35), parent=street)
plane("s_road", (40, 160), (22.0, 0, 0.0), pbr("asph", "asphalt_02", 0.3), parent=street)
box("s_curb", (0.16, 160, 0.16), (2.05, 0, 0.08), pbr("curb", "concrete_pavement", 0.6), parent=street)
for i, y in enumerate((-9, -3, 3, 9, 15, 21, 27, 33)):
    box(f"s_bld{i}", (0.4, 5.8, 7 + 2 * (i % 2)), (-2.4, y, 3.5), pbr(f"bw{i}", "painted_plaster_wall", 0.5, tint=((0.85, 0.75, 0.62), (0.7, 0.72, 0.75))[i % 2]), parent=street)
    for z in (1.2, 3.6, 5.8):
        plane(f"s_win{i}_{z}", (1.3, 1.2), (-2.19, y, z), mat(f"swin{i}{z}", (0.05, 0.07, 0.09), 0.05, metal=0.6), rot=(90, 0, 90), parent=street)

# ======================================================================
# 5) MEGAN
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
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo
    return s
FALL = A_("Fall_Flat.fbx", inplace=False); RUB = A_("Sitting_Rubbing_Arm.fbx", inplace=False)
strip(meg, FALL, -1)
IT0, IT1 = S["itch"]; BR0, BR1 = S["brain"]; EN0, EN1 = S["end"]
strip(meg, RUB, IT0, src=(56, 133))
strip(meg, RUB, BR0, src=(100, 102), repeat=(EN0 - BR0) / 1.6)
strip(meg, RUB, EN0, src=(100, 152))
FALL_P = ST + V(8.0, 3.6, 0.0)
SIT_P = V(0.0, 0.02, SEAT_Z - 0.6 + float(os.environ.get("SEAT_DZ", 0.0)))
for f, p in ((1, FALL_P), (IT0, SIT_P)):
    mroot.location = p; mroot.keyframe_insert("location", frame=f)
interp(mroot, "CONSTANT")
BODY = next(o for o in mmeshes if o.name.endswith("Body"))
# bilakdagi qo'tir: teri sirtidagi nuqtani topib, suyakka bog'lash
sc.frame_set(IT0 + 30); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); bo = BODY.evaluated_get(dg); bme = bo.to_mesh()
bvh = BVHTree.FromPolygons([bo.matrix_world @ v.co for v in bme.vertices], [p.vertices[:] for p in bme.polygons]); bo.to_mesh_clear()
pb = meg.pose.bones["mixamorig:LeftForeArm"]; Mw = meg.matrix_world @ pb.matrix
bone_dir = (Mw.to_3x3() @ V(0, 1, 0)).normalized(); blen = ((meg.matrix_world @ pb.tail) - (meg.matrix_world @ pb.head)).length
mid = (meg.matrix_world @ pb.head) + bone_dir * blen * 0.45
want = V(0.25, -1.0, 0.9).normalized(); want = (want - bone_dir * want.dot(bone_dir)).normalized()
hloc, hnrm, _i, _d = bvh.ray_cast(mid + want * 0.3, -want)
print("SCAB on arm", hloc, hnrm, "bone len", blen)
xax = (bone_dir - hnrm * bone_dir.dot(hnrm)).normalized(); yax = hnrm.cross(xax)
Wm = Matrix((xax, yax, hnrm)).transposed().to_4x4(); Wm.translation = hloc
Mb = Matrix.LocRotScale(Mw.to_translation(), Mw.to_quaternion(), None)
armE = child_of_bone("meg_lfa", meg, "LeftForeArm")
scabE = empty("arm_scabE", (0, 0, 0), armE); scabE.matrix_local = Mb.inverted() @ Wm
ASCAB_M = scab_mat("ascab", 420.0, 1.0, bump_d=0.0006)
uvsphere("arm_scab", (0, 0, 0.0004), (0.015, 0.0085, 0.0024), ASCAB_M, parent=scabE, seg=32, rings=12)
HALO_M = mat("halo", (0.8, 0.22, 0.2), 0.5, alpha=0.45)
uvsphere("arm_halo", (0, 0, -0.0006), (0.027, 0.018, 0.0016), HALO_M, parent=scabE, seg=32, rings=12)
ringR = empty("a_ringE", (0, 0, 0.004), scabE)
itch_rings("aring", ringR, list(range(F_ITCH - 14, IT1, 8)) + list(range(EN0, EN1 - 8, 8)), 0.014, 0.075, minor=0.07)
# rentgen tana + asab yo'li + miya
XR_M = P.xray_material("xr_body", (0.35, 0.75, 1.0), 1.3, 0.02)
GHOSTS = []
for o in mmeshes:
    if o.name.endswith("Eyelashes") or o.name.endswith("Hair"): continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g); g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = XR_M
    GHOSTS.append(g)
sc.frame_set(BR0 + 20); bpy.context.view_layer.update()
def BW(b): return meg.matrix_world @ meg.pose.bones["mixamorig:" + b].head
SCABW = scabE.matrix_world.translation.copy()
HEADW = BW("Head"); HUP = (meg.matrix_world @ meg.pose.bones["mixamorig:Head"].matrix).to_3x3() @ V(0, 1, 0); HUP.normalize()
NPTS = [SCABW, BW("LeftForeArm"), BW("LeftArm"), BW("LeftShoulder") * 0.5 + BW("Neck") * 0.5, BW("Neck"), HEADW, HEADW + HUP * 0.09]
NPTS = [q for a_, b_ in zip(NPTS, NPTS[1:]) for q in (a_, a_.lerp(b_, 0.5))] + [NPTS[-1]]
XN_M = P.pulse_material("xnerve", (1.0, 0.6, 0.08), 0.6, (1.0, 0.85, 0.35), width=0.08)
xnerve = P.tube("xnerve", [tuple(p) for p in NPTS], 0.0045, XN_M)
for f, v in ((BR0, -0.1), (BR0 + 4, -0.05), (F_ARRIVE, 1.05), (F_ARRIVE + 1, -1.0), (F_ARRIVE + 3, -0.05), (BR1, 1.05)): val_key(XN_M, "pos", f, v)
interp(XN_M.node_tree, "LINEAR")
xdot = sphere("xscab", 0.014, tuple(SCABW), emis("xscab", (1.0, 0.1, 0.05), 2.4))
for f in range(BR0, BR1 + 1, 6): key(xdot, f, scale=1.0); key(xdot, f + 3, scale=1.5)
headE = child_of_bone("meg_head", meg, "Head")
brainE = empty("brain_off", (0.0, 0.105, 0.015), headE); brainE.rotation_euler = (R(-90), 0, 0)
brain, brain_m = P.build_brain("brain", brainE, size=0.088)
for f, v in ((BR0, 0.0), (F_ARRIVE - 2, 0.0), (F_ARRIVE + 2, 9.0), (F_ARRIVE + 8, 2.5), (BR1 - 4, 2.5), (BR1, 7.0)): val_key(brain_m, "glow", f, v)
interp(brain_m.node_tree, "LINEAR")
for o in mmeshes: vis(o, ROOM_R + STR_R, recursive=False)
for g in GHOSTS: vis(g, XR_R, recursive=False)
vis(xnerve, XR_R); vis(xdot, XR_R); vis(brainE, XR_R); vis(scabE, ROOM_R)
for o in list(ringR.children): pass

# ======================================================================
# 6) KAMERALAR — hech biri bir joyda turmaydi
# ======================================================================
M = lambda *a: MF + V(*a)
C = lambda *a: CUT + V(*a)
S0 = M(0, 0, 0.012)
FA0, FA1 = S["fall"]
fallT = empty("fall_t"); _cl = fallT.constraints.new("COPY_LOCATION"); _cl.target = child_of_bone("meg_spine", meg, "Spine2")
c = shot_cam("fall", tuple(FALL_P + V(0.5, -5.0, 0.14)), fallT, 16, 4.0, focus=fallT, clip=0.03)
path_keys(c, [(FA0, FALL_P + V(0.7, -5.9, 0.16)), (F_IMPACT, FALL_P + V(0.55, -5.0, 0.12)), (FA1, FALL_P + V(0.45, -4.75, 0.1))])
lens_keys(c, [(FA0, 16), (F_IMPACT, 17), (F_IMPACT + 4, 22), (FA1, 24)])
shake(c, F_IMPACT, F_IMPACT + 9, 0.035, seed=3)
c = abs_cam("scrape", [(SR0, M(0.5, -0.95, 0.36)), (SR0 + 8, M(0.3, -0.55, 0.24)), (SR1, M(0.2, -0.45, 0.2))], [(SR0, S0), (SR1, S0)], 24, 9.0, clip=0.005)
shake(c, SR0, SR0 + 7, 0.012, seed=5)
c = abs_cam("scab", [(SB0, M(-0.42, -0.5, 0.36)), ((SB0 + SB1) // 2, M(0.0, -0.62, 0.3)), (SB1, M(0.4, -0.46, 0.26))], [(SB0, S0), (SB1, S0)], 26, 10.0, clip=0.005)
ithT = empty("itch_t"); _cl = ithT.constraints.new("COPY_LOCATION"); _cl.target = scabE
c = shot_cam("itch", (1.2, -1.9, 0.4), ithT, 18, 3.2, focus=ithT, clip=0.03)
path_keys(c, [(IT0, V(1.25, -1.95, 0.38)), (F_ITCH - 3, V(0.9, -1.75, 0.5)), (F_ITCH + 2, V(0.62, -1.45, 0.62)), (IT1, V(0.5, -1.35, 0.66))])
lens_keys(c, [(IT0, 18), (F_ITCH - 3, 20), (F_ITCH + 2, 62), (IT1, 68)])
shake(c, F_ITCH, F_ITCH + 8, 0.012, seed=9)
c = abs_cam("scratch", [(SC0, M(0.42, -0.72, 0.2)), (F_TOUCH, M(0.3, -0.6, 0.16)), (SC1, M(0.22, -0.55, 0.15))], [(SC0, S0 + V(0.04, 0, 0.06)), (SC1, S0 + V(0.03, 0, 0.03))], 24, 9.0, clip=0.005)
for f in range(F_TOUCH, SC1 - 3, 8): shake(c, f, f + 4, 0.006, seed=f)
c = abs_cam("noinf", [(NI0, M(-0.4, -0.9, 0.3)), (F_NO - 2, M(-0.2, -0.78, 0.26)), (F_NO + 3, M(-0.12, -0.66, 0.24)), (NI1, M(-0.05, -0.62, 0.23))], [(NI0, S0 + V(0, 0, 0.08)), (NI1, S0 + V(0, 0, 0.11))], 24, 9.0, clip=0.005)
lens_keys(c, [(NI0, 24), (F_NO - 2, 25), (F_NO + 3, 32), (NI1, 33)])
shake(c, F_NO, F_NO + 7, 0.008, seed=13)
c = abs_cam("heal", [(HE0, M(0.3, -0.5, 0.5)), (HE1 - 12, M(-0.12, -0.38, 0.5)), (HE1, M(-0.03, -0.1, 0.2))], [(HE0, S0), (HE1, S0)], 26, 9.0, clip=0.005)
lens_keys(c, [(HE0, 26), (HE1 - 12, 30), (HE1, 44)])
RV0, RV1 = S["reveal"]
c = abs_cam("reveal", [(RV0, C(-1.5, -3.9, 2.3)), (RV1, C(0.9, -3.1, 1.2))], [(RV0, C(0, 0, -0.75)), (RV1, C(0, 0.2, -0.6))], 28, 5.6)
lens_keys(c, [(RV0, 20), (RV0 + 10, 28), (RV1, 30)])
UN0, UN1 = S["under"]
c = abs_cam("under", [(UN0, C(0.45, -2.3, 0.95)), (UN1, C(-0.05, -1.15, 0.13))], [(UN0, C(0, 0, 0.25)), (UN1, C(0, 0, 0.07))], 35, 5.6)
CW0, CW1 = S["crawl"]
c = abs_cam("crawl", [(CW0, C(-0.82, -0.85, 0.2)), (CW1, C(-0.32, -0.75, 0.13))], [(CW0, C(-0.5, 0, 0.07)), (CW1, C(-0.2, 0, 0.07))], 32, 5.6)
LK0 = S["link"][0]
c = abs_cam("link", [(LK0, C(0.36, -1.05, 0.24)), (F_LINK, C(0.02, -0.66, 0.12)), (LK1, C(-0.03, -0.6, 0.11))], [(LK0, C(0.05, 0, 0.07)), (LK1, C(0, 0, 0.07))], 32, 5.6)
shake(c, F_LINK, F_LINK + 8, 0.012, seed=21)
c = abs_cam("pull", [(PU0, C(0.25, -2.9, 0.62)), (PU1, C(-0.1, -2.3, 0.45))], [(PU0, C(0, 0, 0.05)), (PU1, C(0, 0, 0.0))], 30, 5.6)
c = abs_cam("tension", [(TE0, C(-0.62, -1.0, 0.0)), (TE1, C(-0.2, -0.8, -0.2))], [(TE0, C(-0.05, 0, -0.26)), (TE1, C(0.02, 0, -0.3))], 32, 5.6)
for f in range(TE0 + 2, TE1 - 3, 5): shake(c, f, f + 4, 0.007, seed=f)
c = abs_cam("hist", [(HI0, C(0.95, -1.55, -0.05)), (HI1, C(0.4, -1.05, -0.3))], [(HI0, C(0.15, 0, -0.42)), (HI1, C(0.12, 0, -0.42))], 32, 5.6)
c = abs_cam("nerve", [(NV0, C(-0.6, -1.25, -0.95)), (NV1, C(-0.15, -0.85, -0.5))], [(NV0, C(0.05, 0, -0.32)), (NV1, C(0.05, 0, -0.26))], 32, 5.6)
c = abs_cam("tickle", [(TK0, C(0.42, -0.72, -0.12)), (TK0 + 30, C(0.3, -0.9, -0.3)), (TK1, C(0.1, -1.75, -0.75))], [(TK0, C(0.05, 0, -0.26)), (TK0 + 30, C(0.05, 0, -0.3)), (TK1, C(0.05, 0, -0.75))], 32, 5.6)
for f in range(TK0 + 4, TK1 - 5, 17): shake(c, f, f + 5, 0.008, seed=f)
c = abs_cam("brain", [(BR0, SCABW + V(0.35, -0.75, 0.05)), (F_ARRIVE, HEADW + V(0.3, -0.95, 0.0)), (BR1, HEADW + V(0.15, -0.6, 0.08))],
            [(BR0, SCABW), (BR0 + 5, SCABW), (F_ARRIVE, HEADW + HUP * 0.08), (BR1, HEADW + HUP * 0.09)], 35, 4.0, clip=0.03)
shake(c, F_ARRIVE, F_ARRIVE + 8, 0.012, seed=31)
c = shot_cam("end", (-0.5, -1.2, 1.0), ithT, 30, 2.8, focus=ithT, clip=0.03)
path_keys(c, [(EN0, HEADW + V(-0.55, -1.25, -0.02)), (EN1, HEADW + V(-0.3, -0.95, -0.08))])
lens_keys(c, [(EN0, 28), (EN0 + 6, 40), (EN1, 46)])
_cr = noE.constraints.new("COPY_ROTATION"); _cr.target = CAMS["noinf"]
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["fall"]

# ======================================================================
# 7) YORUG'LIK va DUNYO
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
bgS = env_bg("studio_small_09.hdr", 30)
bgK = N.new("ShaderNodeBackground"); bgK.inputs[0].default_value = (0.006, 0.004, 0.008, 1)
a1 = N.new("ShaderNodeAddShader"); a2 = N.new("ShaderNodeAddShader")
L.new(bgH.outputs[0], a1.inputs[0]); L.new(bgS.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], a2.inputs[0]); L.new(bgK.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    vals = {"H": 0.35 if n in ROOMN else 1.0 if n in STRN else 0.0, "S": 0.3 if n in MACN else 0.0, "K": 1.0 if (n in CUTN or n in XRN) else 0.0}
    for bg, k in ((bgH, "H"), (bgS, "S"), (bgK, "K")):
        bg.inputs[1].default_value = vals[k]; bg.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
RT = empty("roomT", (0.1, -0.1, 0.8))
area("R_ceil", (0.3, -1.0, 2.7), 1.4, (1.0, 0.9, 0.78), lights_for(ROOM_R, 170.0), target=RT)
area("R_win", (-2.1, -0.9, 1.5), 1.2, (0.9, 0.95, 1.0), lights_for(ROOM_R, 280.0), target=RT)
area("R_rim", (1.4, 0.3, 1.9), 0.6, (1.0, 0.75, 0.5), lights_for(ROOM_R, 70.0), target=RT)
area("R_front", (0.6, -2.2, 1.4), 1.0, (1.0, 0.95, 0.9), lights_for(ROOM_R, 60.0), target=RT)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(50), 0, R(35)); sun.data.angle = R(1.5)
for f, e in lights_for(STR_R, 6.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
MT = empty("macT", tuple(S0))
area("M_key", tuple(M(-1.4, -1.8, 2.6)), 2.2, (1.0, 0.94, 0.86), lights_for(MAC_R, 210.0), target=MT)
area("M_fill", tuple(M(2.4, -1.2, 1.2)), 2.0, (0.85, 0.92, 1.0), lights_for(MAC_R, 110.0), target=MT)
area("M_rim", tuple(M(0.4, 2.6, 1.6)), 2.0, (1.0, 0.8, 0.6), lights_for(MAC_R, 240.0), target=MT)
CTT = empty("cutT", tuple(C(0, 0, -0.3)))
area("K_key", tuple(C(2.2, -2.8, 2.2)), 2.5, (1.0, 0.95, 0.9), lights_for(CUT_R, 210.0), target=CTT)
area("K_fill", tuple(C(-2.6, -2.0, -0.6)), 2.5, (1.0, 0.85, 0.75), lights_for(CUT_R, 75.0), target=CTT)
area("K_rim", tuple(C(-1.2, 2.2, 2.2)), 2.0, (0.35, 0.6, 1.0), lights_for(CUT_R, 120.0), target=CTT)
area("K_low", tuple(C(0.0, -1.2, 0.05)), 0.8, (1.0, 0.8, 0.7), lights_for(rng("under", "crawl", "link"), 30.0), target=empty("cutT2", tuple(C(0, 0, 0.07))))
def has_vis(o): return any(fc.data_path == "hide_render" for fc in fcurves(o))
def vis_world(objs, ranges):
    for o in objs:
        if not has_vis(o): vis(o, ranges, recursive=False)
vis_world([mf] + list(mf.children_recursive), MAC_R)
vis_world([cutp] + list(cutp.children_recursive), CUT_R)
vis_world([room] + list(room.children_recursive), ROOM_R)
vis_world([street] + list(street.children_recursive), STR_R)

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
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
        sc.frame_set(a); sc.frame_start, sc.frame_end = a, b; sc.frame_step = int(os.environ.get("STEP", 1))
        bpy.ops.render.render(animation=True)
