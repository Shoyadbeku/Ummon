# Tirnoqning etga o'sib kirishi (ingrown toenail) — Zack D. Films uslubida 39.1 s video (938 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; yordamchilar zack_test/tirnoq/tirnoq.py dan; parts.py = burish/parts.py
# Assetlar: zack_test/tools/get_tirnoq_osishi.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/tirnoq_osishi/tirnoq_osishi.py --render
# Sinov:  FRAMES=20,70,150,300,520,600,710,920 PCT=35 OUT=/tmp/claude-0/test/ ... --render
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
END = 938
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

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (38, "clip"), (103, "room"), (126, "trap"), (178, "short"), (232, "fold"), (310, "grow"), (356, "blade"),
         (434, "inward"), (495, "pierce"), (555, "shoe"), (610, "bact"), (666, "swell"), (692, "pus"), (733, "limp"),
         (755, "nostop"), (786, "deeper"), (836, "scalpel"), (887, "extract")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
MACN = ("hook", "clip", "trap", "grow", "pierce", "bact", "swell", "pus", "scalpel", "extract")
CUTN = ("short", "fold", "blade", "inward", "nostop", "deeper")
ROOMN = ("room",); STRN = ("shoe", "limp")
MAC_R = rng(*MACN); CUT_R = rng(*CUTN); ROOM_R = rng(*ROOMN); STR_R = rng(*STRN)
SNAP_L, SNAP_R = 60, 86          # "chetini" / "qilib" — qaychi burchaklarni kesadi
F_TRAP = 145                     # "tuzoq" — qopqon yopiladi
F_PIERCE = 530                   # "teshib" — tirnoq terini yorib chiqadi
F_XRAY = 583                     # krossovka rentgenga aylanadi
BEATS = list(range(668, 732, 12))

# ======================================================================
# MATERIALLAR (umumiy)
# ======================================================================
blood_m = mat("blood", (0.07, 0.0, 0.002), 0.06, coat=1.0)
steel_m = mat("steel", (0.7, 0.7, 0.72), 0.18, metal=1.0)
dark_steel = mat("dark_steel", (0.25, 0.25, 0.27), 0.3, metal=1.0)

def world_dist(N, L, center):
    """dunyo koordinatasida center dan masofa (shader)"""
    g = N.new("ShaderNodeNewGeometry")
    sub = N.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = tuple(center)
    L.new(g.outputs["Position"], sub.inputs[0])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(sub.outputs[0], ln.inputs[0])
    return ln.outputs["Value"]

def toe_skin(name, center, base=(0.78, 0.5, 0.4)):
    """oyoq terisi: 'red' (0..1) — center atrofida qizarish/shish, 'throb' — yurak urishida, 'iodine' — yod (jarrohlik)"""
    m = P.skin_material(name, base=base, prints=False)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.14); b.inputs["Subsurface Scale"].default_value = 0.0007
    red = value_node(m, "red", 0.0); th = value_node(m, "throb", 0.0); io = value_node(m, "iodine", 0.0)
    d = world_dist(N, L, center)
    rad = P.math_n(N, L, "ADD", 0.004, P.math_n(N, L, "MULTIPLY", red, 0.022))
    f = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", d, rad), clamp=True)
    f = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", f, 0.7), P.math_n(N, L, "MINIMUM", P.math_n(N, L, "MULTIPLY", red, 3.0), 1.0))
    f = P.math_n(N, L, "MINIMUM", P.math_n(N, L, "ADD", f, P.math_n(N, L, "MULTIPLY", f, P.math_n(N, L, "MULTIPLY", th, 0.4))), 1.0)
    src = b.inputs["Base Color"].links[0].from_socket
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(src, mx.inputs[6]); mx.inputs[7].default_value = (0.62, 0.05, 0.05, 1)
    L.new(f, mx.inputs["Factor"])
    mi = N.new("ShaderNodeMix"); mi.data_type = "RGBA"; L.new(mx.outputs[2], mi.inputs[6])
    mi.inputs[7].default_value = (0.5, 0.17, 0.03, 1); L.new(P.math_n(N, L, "MULTIPLY", io, 0.7), mi.inputs["Factor"])
    L.new(mi.outputs[2], b.inputs["Base Color"])
    # yallig'langan teri yaltiroq va ichidan qizg'ish nur
    b.inputs["Emission Color"].default_value = (1.0, 0.1, 0.05, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", f, P.math_n(N, L, "ADD", 0.05, th)), 0.6), b.inputs["Emission Strength"])
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", f, 0.6), P.math_n(N, L, "MULTIPLY", io, 0.3)), b.inputs["Coat Weight"])
    return m

def toenail_material(name):
    """tirnoq: Y < 0.0045 (barmoq uchidan tashqarisi) oq; 'line' — skalpel chizig'i (x = LINE_X) ildiz tomonga qarab"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.38
    b.inputs["Coat Weight"].default_value = 0.35; b.inputs["Coat Roughness"].default_value = 0.12
    b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Scale"].default_value = 0.0004
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.35)
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900.0; nz.inputs["Detail"].default_value = 2.0
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 0.08, 1.0); L.new(tc.outputs["Object"], mp.inputs[0])
    L.new(mp.outputs[0], nz.inputs["Vector"])      # bo'ylama chiziqlar
    free = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", sp.outputs["Y"], 0.0035), 0.0012), clamp=True)
    lun = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", 0.0245, sp.outputs["Y"]), 0.002), clamp=True)
    c0 = N.new("ShaderNodeMix"); c0.data_type = "RGBA"; c0.inputs[6].default_value = (0.7, 0.36, 0.32, 1); c0.inputs[7].default_value = (0.93, 0.86, 0.76, 1)
    L.new(P.math_n(N, L, "MAXIMUM", free, P.math_n(N, L, "MULTIPLY", lun, 0.6)), c0.inputs["Factor"])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; c1.blend_type = "MULTIPLY"; L.new(c0.outputs[2], c1.inputs[6])
    L.new(P.math_n(N, L, "ADD", 0.86, P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.2)), c1.inputs[7])
    c1.inputs["Factor"].default_value = 1.0
    # skalpel chizig'i
    line = value_node(m, "line", 0.0)
    lx = P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", sp.outputs["X"], LINE_X))
    on = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", lx, 0.00045), clamp=True)
    reach = P.math_n(N, L, "LESS_THAN", sp.outputs["Y"], P.math_n(N, L, "ADD", 0.0, P.math_n(N, L, "MULTIPLY", line, 0.03)))
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.25, 0.0, 0.01, 1)
    L.new(P.math_n(N, L, "MULTIPLY", on, reach), c2.inputs["Factor"])
    L.new(c2.outputs[2], b.inputs["Base Color"])
    return m

# ======================================================================
# 1) MAKRO OYOQ (0,30,0): o'ng oyoq, barmoqlar -Y tomonga, bosh barmoq uchi (0,0,·)
# ======================================================================
MF = V(0, 30, 0)
mf = empty("MACRO", tuple(MF))
BRX, BRZ, BLC = 0.0125, 0.0105, 0.016          # bosh barmoq yarim eni, yarim balandligi, uchi (cap) uzunligi
ZC = BRZ                                        # barmoq o'qi balandligi (polga tegib turadi)
NW = 0.0088                                     # tirnoq yarim eni
LINE_X = -0.55 * NW                             # skalpel chizig'i
PW = V(-NW - 0.0012, 0.0115, 0.0)               # jarohat nuqtasi (chap yon burma), z keyin hisoblanadi

def kcap(y, lc):
    if y >= lc: return 1.0
    t = (lc - y) / lc; return math.sqrt(max(0.0, 1 - t * t))

def toe_surface_z(x, y, rx=BRX, rz=BRZ, lc=BLC, zc=ZC):
    k = kcap(max(y, 0.0005), lc); ax = rx * k
    if abs(x) >= ax: return zc
    return zc + rz * k * math.sqrt(1 - (x / ax) ** 2) * (1.0 - 0.06 * math.exp(-((y - 0.014) / 0.012) ** 2))

def toe_mesh(name, rx, rz, lc, length, zc, mtl, parent, squash_top=True):
    """parametrik barmoq: uchi (0,·,·), tanasi +Y bo'ylab; kesimi ellips, uchi yarim ellipsoid"""
    SEG = 96; prof = []
    for i in range(1, 25):
        th = (i / 24) * (math.pi / 2); prof.append((lc - lc * math.cos(th), math.sin(th)))
    for i in range(1, 41): prof.append((lc + length * i / 40, 1.0 + 0.25 * (i / 40) ** 2))
    verts = [(0.0, 0.0, zc - rz * 0.1)]
    for y, k in prof:
        for j in range(SEG):
            a = 2 * math.pi * j / SEG
            x = k * rx * math.sin(a); z = -k * rz * math.cos(a)
            if z < 0: z *= 0.92                                    # pastki yostiqcha yassi (polga tegadi)
            if squash_top and z > 0: z *= 1.0 - 0.06 * math.exp(-((y - 0.014) / 0.012) ** 2)
            verts.append((x, y, zc + z))
    faces = [(0, 1 + (j + 1) % SEG, 1 + j) for j in range(SEG)]
    for i in range(len(prof) - 1):
        b0 = 1 + i * SEG; b1 = b0 + SEG
        for j in range(SEG):
            j2 = (j + 1) % SEG; faces.append((b0 + j, b0 + j2, b1 + j2, b1 + j))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); P.link(o, parent); o.data.shade_smooth(); o.data.materials.append(mtl)
    return o

FOOT_SKIN = toe_skin("foot_skin", MF + PW + V(0, 0, 0.019), base=(0.7, 0.4, 0.3))
bigtoe = toe_mesh("bigtoe", BRX, BRZ, BLC, 0.05, ZC, FOOT_SKIN, mf)
PW.z = toe_surface_z(PW.x, PW.y) + 0.0012
# kichik barmoqlar (+X tomonda, orqaroq)
for i, (x, y0, r) in enumerate(((0.0225, 0.012, 0.0072), (0.0378, 0.02, 0.0066), (0.0512, 0.029, 0.0062), (0.0628, 0.04, 0.0056))):
    t = toe_mesh(f"toe{i}", r * 1.05, r * 0.95, r * 1.1, 0.05, r * 0.95, FOOT_SKIN, mf)
    t.location = (x, y0, 0); t.rotation_euler = (0, 0, R(-4 - 4 * i))
    nl = uvsphere(f"toe{i}_nail", (0, r * 0.75, r * 1.82), (r * 0.62, r * 0.62, r * 0.12), toenail_material(f"tn{i}"), parent=t)
    nl.rotation_euler = (R(-8), 0, 0)
# oyoq kafti (old qismi)
foot = uvsphere("foot_body", (0.03, 0.125, 0.02), (0.06, 0.095, 0.03), FOOT_SKIN, parent=mf, seg=64, rings=32)
for v in foot.data.vertices:
    if v.co.z < 0: v.co.z *= 0.75
    v.co.z += 0.5 * max(0.0, v.co.y) ** 2                          # to'piq tomonga ko'tariladi
# yon burmalar (tirnoq chetlari ustidagi teri) va orqa burma (kutikula)
def fold(name, x, side):
    o = uvsphere(name, (0, 0, 0), (0.0026, 0.0115, 0.0026), FOOT_SKIN, parent=mf, seg=32, rings=16)
    o.location = (x, 0.0175, toe_surface_z(x, 0.0175) - 0.0006); o.rotation_euler = (0, R(-25 * side), 0)
    return o
foldL = fold("foldL", -NW - 0.0006, -1); foldR = fold("foldR", NW + 0.0006, 1)
cuticle = uvsphere("cuticle", (0, 0.0285, toe_surface_z(0, 0.0285) - 0.0007), (NW + 0.002, 0.0042, 0.0024), FOOT_SKIN, parent=mf)

# ---------------- TIRNOQ: holatlar shape key zanjiri ----------------
Y_ROOT = 0.0265
def cornercut(u): return smooth(0.15, 1.0, abs(u)) ** 1.4
def edge_long(u): return -0.0012 + 0.0025 * u ** 4
def edge_cut(u):  return 0.0055 + 0.011 * cornercut(u)
def edge_grown(u): return 0.0005 + 0.0025 * u ** 4
STATES = {
    "base":   lambda u: (edge_long(u), 0.0),
    "cutL":   lambda u: ((edge_cut(u) if u < 0.08 else edge_long(u)), 0.0),
    "cutLR":  lambda u: (edge_cut(u), 0.0),
    "grown":  lambda u: (edge_grown(u), 0.0),
    "ingrown": lambda u: (edge_grown(u), 1.0),
}
NU, NV = 48, 36
def nail_pts(u0, u1, state):
    edge = STATES[state]; pts = []
    for j in range(NV + 1):
        v = j / NV
        for i in range(NU + 1):
            u = u0 + (u1 - u0) * i / NU
            yf, ing = edge(u)
            y = Y_ROOT - v * (Y_ROOT - yf)
            x = u * NW * (1.0 - 0.04 * v)
            z = toe_surface_z(x, max(y, 0.004)) + 0.00035
            if y < 0.004: z += (0.004 - y) * 0.15                      # o'sib chiqqan uchi biroz ko'tarilib qoladi
            if ing and u < -0.55:                                      # chap cheti etning ichiga egilib kiradi
                w = smooth(0.55, 1.0, -u) * smooth(0.35, 0.9, v)
                x -= 0.0028 * w; z -= 0.0026 * w
            pts.append((x, y, z))
    return pts
def nail_obj(name, u0, u1, mtl):
    base = nail_pts(u0, u1, "base")
    faces = []
    for j in range(NV):
        for i in range(NU):
            a = j * (NU + 1) + i; faces.append((a, a + 1, a + NU + 2, a + NU + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(base, [], faces); me.update()
    o = bpy.data.objects.new(name, me); P.link(o, mf); o.data.shade_smooth(); o.data.materials.append(mtl)
    sk0 = o.shape_key_add(name="Basis", from_mix=False)
    prev = sk0
    for st in ("cutL", "cutLR", "grown", "ingrown"):
        k = o.shape_key_add(name=st, from_mix=False); k.value = 0.0; k.relative_key = prev
        # zanjir: har kalit o'zidan oldingisiga nisbatan
        for vi, p in enumerate(nail_pts(u0, u1, st)): k.data[vi].co = p
        prev = k
    so = o.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.00055; so.offset = -1.0; so.use_even_offset = True
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = 1; sd.render_levels = 1
    return o
NAIL_M = toenail_material("toenail")
nailF = nail_obj("nail_full", -1.0, 1.0, NAIL_M)             # jarrohlikkacha butun tirnoq (chok ko'rinmasin)
nailA = nail_obj("nail_main", -0.55, 1.0, NAIL_M)
nailB = nail_obj("nail_strip", -1.0, -0.55, NAIL_M)          # jarroh kesib oladigan chap bo'lak
NAILS = (nailF, nailA, nailB)
vis(nailF, [(1, S["extract"][0] - 1)], recursive=False)
vis(nailA, [S["extract"]], recursive=False); vis(nailB, [S["extract"]], recursive=False)
def nail_state(name, f, v):
    for o in NAILS:
        kb = o.data.shape_keys.key_blocks[name]; kb.value = v; kb.keyframe_insert("value", frame=f)
for st, pts in (("cutL", ((SNAP_L - 1, 0), (SNAP_L + 1, 1))), ("cutLR", ((SNAP_R - 1, 0), (SNAP_R + 1, 1))),
                ("grown", ((S["grow"][0] + 2, 0), (S["grow"][1] - 2, 1))), ("ingrown", ((S["inward"][0], 0), (S["inward"][1], 1)))):
    for f, v in pts: nail_state(st, f, v)
# kesilgan bo'lakchalar (uchib tushadi)
clip_bits = []
for k, (f0, side) in enumerate(((SNAP_L, -1), (SNAP_R, 1))):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.005, depth=0.0005, location=(0, 0, 0))
    bit = bpy.context.object; bit.name = f"nail_bit{k}"; bit.data.materials.append(NAIL_M)
    for v in bit.data.vertices:
        if v.co.y > 0.0012: v.co.y = 0.0012 + (v.co.y - 0.0012) * 0.2
    bit.scale = (1.0, 0.6, 1.0); bit.parent = mf
    p0 = V(side * NW * 0.7, 0.003, toe_surface_z(side * NW * 0.7, 0.006) + 0.0003)
    key(bit, f0, loc=tuple(p0), rot=(0, 0, side * 40))
    for j in range(1, 14):
        t = j / 24.0
        q = p0 + V(side * 0.03 * t, -0.04 * t, 0.025 * t - 0.5 * 2.5 * t * t); q.z = max(q.z, 0.0004)
        key(bit, f0 + j, loc=tuple(q), rot=(j * 25, side * j * 18, side * 40))
    key(bit, f0 + 40, loc=tuple(p0 + V(side * 0.03, -0.035, -p0.z + 0.0004)), rot=(180, 0, side * 70))
    vis(bit, [(f0, S["clip"][1])], recursive=False); clip_bits.append(bit)

# ---------------- TIRNOQ QAYCHISI (procedural): kesuvchi qirra = (0,0,0) X bo'ylab, tanasi -Y ga ----------------
def build_clipper(name, parent=None, scale=1.0):
    root = empty(name, (0, 0, 0), parent); s = scale
    hinge = empty(name + "_hinge", (0, -0.05 * s, 0.0), root)
    def jaw(nm, up):
        o = box(nm, (0.013 * s, 0.056 * s, 0.0013 * s), (0, -0.026 * s, up * 0.0018 * s), steel_m, bevel=0.0004 * s)
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True); bm.to_mesh(o.data); bm.free()
        for v in o.data.vertices:
            yy = v.co.y + 0.026 * s
            v.co.z -= up * 0.0016 * s * smooth(-0.012 * s, 0.0, yy)        # old uchlari bir-biriga qarab egiladi
            v.co.x *= 1.0 - 0.25 * smooth(-0.006 * s, 0.0, yy) * (abs(v.co.x) / (0.0065 * s)) ** 2
        return o
    lo = jaw(name + "_lo", -1); lo.parent = root
    up = jaw(name + "_up", 1); up.parent = hinge; up.location = (0, 0.05 * s, 0.0)
    lever = box(name + "_lever", (0.011 * s, 0.05 * s, 0.0011 * s), (0, 0.022 * s, 0.0048 * s), dark_steel, rot=(-6, 0, 0), bevel=0.0004 * s)
    lever.parent = hinge
    cyl(name + "_pin", 0.0012 * s, 0.009 * s, (0, -0.012 * s, 0.0015 * s), steel_m, parent=root)
    return root, hinge
clipper, clip_hinge = build_clipper("clipper", mf)
# harakat: ilgak — o'ngdan kirib keladi; kesish — chap burchak, keyin o'ng burchak
def corner(side): return V(side * NW * 0.82, 0.0045, toe_surface_z(side * NW * 0.82, 0.006) + 0.0003)
CL0 = corner(-1); CR0 = corner(1)
H0, H1 = S["hook"]; C0, C1 = S["clip"]
for f, p, r in ((H0, CL0 + V(-0.13, -0.05, 0.04), (6, 0, -70)), (H1 - 4, CL0 + V(-0.01, -0.006, 0.003), (4, 0, -62)),
                (C0 + 6, CL0 + V(-0.003, -0.002, 0.0005), (3, 0, -62)), (SNAP_L, CL0, (3, 0, -62)), (SNAP_L + 6, CL0 + V(-0.006, -0.004, 0.002), (3, 0, -60)),
                (SNAP_L + 10, CL0 + V(-0.03, -0.02, 0.03), (3, 0, -40)), (SNAP_R - 10, CR0 + V(0.03, -0.02, 0.03), (3, 0, 40)),
                (SNAP_R - 4, CR0 + V(0.006, -0.004, 0.002), (3, 0, 62)), (SNAP_R, CR0, (3, 0, 62)), (SNAP_R + 5, CR0 + V(0.006, -0.004, 0.002), (3, 0, 62)),
                (C1, CR0 + V(0.08, -0.03, 0.03), (3, 0, 70))):
    key(clipper, f, loc=tuple(p), rot=r)
for f, a in ((H0, -9), (SNAP_L - 4, -9), (SNAP_L, 0), (SNAP_L + 3, 0), (SNAP_L + 8, -9), (SNAP_R - 4, -9), (SNAP_R, 0), (SNAP_R + 3, 0), (SNAP_R + 8, -9)):
    key(clip_hinge, f, rot=(a, 0, 0))
interp(clip_hinge, "LINEAR")

# ---------------- QOPQON (tuzoq): ikki yarim halqa jag', o'qi X bo'ylab (y = TY) ----------------
TY = 0.021; TRR = 0.0245
trap = empty("trap", (0, TY, 0.0012), mf)
def trap_jaw(name, side):
    piv = empty(name, (0, 0, 0), trap)
    pts = [(TRR * math.cos(math.pi * i / 24), side * TRR * math.sin(math.pi * i / 24), 0) for i in range(25)]
    P.tube(name + "_arc", pts, 0.0011, dark_steel, piv, res=24)
    for i in range(2, 23, 2):
        a = math.pi * i / 24; d = V(-math.cos(a), -side * math.sin(a), 0)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.0011, radius2=0.0, depth=0.0035)
        t = bpy.context.object; t.data.materials.append(steel_m); t.parent = piv
        t.location = V(TRR * math.cos(a), side * TRR * math.sin(a), 0) + d * 0.0018
        t.rotation_mode = "QUATERNION"; t.rotation_quaternion = d.to_track_quat("Z", "Y")
    return piv
jawA = trap_jaw("jawA", -1); jawB = trap_jaw("jawB", 1)
box("trap_plate", (0.012, 0.016, 0.0016), (0, 0, -0.0004), dark_steel, parent=trap, bevel=0.0005)
for sx in (-1, 1):
    cyl(f"trap_spring{sx}", 0.0018, 0.03, (sx * 0.042, 0, 0.0006), dark_steel, rot=(0, 90, 0), parent=trap)
    P.tube(f"trap_arm{sx}", [(sx * 0.026, 0, 0.0005), (sx * 0.04, -0.004, 0.0008), (sx * 0.058, 0, 0.0006)], 0.0009, dark_steel, trap)
T0, T1 = S["trap"]
for f, a in ((T0, 0), (F_TRAP - 3, 4), (F_TRAP, 92), (F_TRAP + 2, 84), (F_TRAP + 5, 90)):
    key(jawA, f, rot=(-a, 0, 0)); key(jawB, f, rot=(a, 0, 0))
interp(jawA, "LINEAR"); interp(jawB, "LINEAR")
vis(trap, [S["trap"]])

# ---------------- TESHIB CHIQQAN TIRNOQ UCHI, JAROHAT, QON, BAKTERIYA, YIRING ----------------
spike = empty("spike_root", tuple(PW + V(0.0012, 0.0, -0.0022)), mf)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.0017, radius2=0.0, depth=0.0062, location=(0, 0, 0.0031))
sp_o = bpy.context.object; sp_o.name = "spike"; sp_o.scale = (1.0, 0.35, 1.0); sp_o.data.materials.append(NAIL_M); sp_o.parent = spike
spike.rotation_euler = (0, R(-38), 0)
for f, s in ((F_PIERCE - 10, 0.05), (F_PIERCE - 2, 0.55), (F_PIERCE, 0.95), (S["swell"][0], 1.0), (S["pus"][1], 1.25)):
    key(spike, f, scale=(1, 1, s))
WOUND_M = mat("wound", (0.16, 0.005, 0.01), 0.15, coat=1.0)
wound = sphere("wound", 0.0019, tuple(PW + V(0, 0, -0.0009)), WOUND_M, scale=(0.05, 0.05, 0.02), parent=mf)
for f, s in ((F_PIERCE - 1, 0.05), (F_PIERCE + 3, 0.7), (S["bact"][1], 1.0), (S["pus"][1], 1.3)):
    key(wound, f, scale=(s, s * 1.5, 0.35))
drop = sphere("blood_drop", 0.0012, tuple(PW + V(-0.0006, -0.0004, 0.0004)), blood_m, parent=mf)
for f, s, dz in ((F_PIERCE + 1, 0.05, 0), (F_PIERCE + 8, 1.0, 0.0002), (S["pierce"][1], 1.25, -0.0012)):
    key(drop, f, loc=tuple(PW + V(-0.0008 - abs(dz), -0.0004, 0.0004 + dz)), scale=(s, s, s * 0.85))
vis(drop, [(F_PIERCE, S["swell"][1])], recursive=False)
# bakteriyalar: jarohatga yopirilib tushadi
BACT_M = mat("bact", (0.12, 0.6, 0.05), 0.3, emit=1.2, emit_col=(0.3, 1.0, 0.1), sss=0.2, coat=0.6)
BACT_M2 = mat("bact2", (0.45, 0.7, 0.03), 0.3, emit=1.0, emit_col=(0.6, 1.0, 0.1), sss=0.2, coat=0.6)
B0, B1 = S["bact"]
rb = random.Random(7)
for i in range(110):
    rod = i % 3 != 0
    b = uvsphere(f"bact{i}", (0, 0, 0), (0.00045, 0.00045, 0.0013 if rod else 0.00055), BACT_M if rod else BACT_M2, parent=mf, seg=16, rings=8)
    ang = rb.uniform(0, 2 * math.pi); rad = rb.uniform(0.01, 0.03)
    start = PW + V(math.cos(ang) * rad, math.sin(ang) * rad * 0.8 - 0.004, rb.uniform(0.004, 0.02))
    end = PW + V(rb.uniform(-0.0012, 0.0012), rb.uniform(-0.0016, 0.0016), rb.uniform(-0.0003, 0.0004))
    t0 = B0 - 8 + rb.uniform(0, 28); t1 = t0 + rb.uniform(16, 30)
    wob = rb.uniform(0, 6.28)
    for f in range(B0 - 1, S["pus"][1] + 2, 2):
        t = smooth(t0, t1, f)
        p = start.lerp(end, t) + V(0.0012 * math.sin(f * 0.4 + wob), 0.0012 * math.cos(f * 0.33 + wob), 0.0) * (1 - t)
        key(b, f, loc=tuple(p), rot=(R(f * 9 + wob * 50), R(wob * 30), R(f * 5)))
    vis(b, [(B0, S["swell"][1])], recursive=False)
# yiring pufagi
PUS_M = mat("pus", (0.9, 0.72, 0.18), 0.15, coat=1.0, sss=0.4)
PUS_M.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.001
pus = sphere("pus", 0.0048, tuple(PW + V(-0.0008, 0.0008, -0.0008)), PUS_M, scale=(0.05, 0.05, 0.05), sub=4, parent=mf)
for f, s in ((S["pus"][0] - 1, 0.05), (S["pus"][0] + 10, 0.55), (S["pus"][1] - 6, 1.0), (S["pus"][1], 1.05)):
    key(pus, f, scale=(s, s * 1.2, s * 0.8))
vis(pus, rng("pus"), recursive=False)
# shish va qizarish
for f, s in ((1, 1.0), (S["fold"][0], 1.0), (S["grow"][0], 1.2), (S["pierce"][0], 1.3), (S["swell"][0], 1.35), (S["swell"][0] + 18, 1.75)):
    key(foldL, f, scale=(s, 1.0 + (s - 1) * 0.3, s))
for f, s in ((S["swell"][0], 1.0), (S["swell"][0] + 20, 1.06)):
    key(bigtoe, f, scale=(s, 1.0, s))
val_key(FOOT_SKIN, "red", 1, 0.0); val_key(FOOT_SKIN, "red", F_PIERCE, 0.0); val_key(FOOT_SKIN, "red", F_PIERCE + 12, 0.25)
val_key(FOOT_SKIN, "red", B1, 0.4); val_key(FOOT_SKIN, "red", S["swell"][0] + 18, 1.0); val_key(FOOT_SKIN, "red", END, 0.8)
val_key(FOOT_SKIN, "throb", 1, 0.0)
for bt in BEATS:
    val_key(FOOT_SKIN, "throb", bt - 1, 0.0); val_key(FOOT_SKIN, "throb", bt + 1, 1.0); val_key(FOOT_SKIN, "throb", bt + 7, 0.0)
val_key(FOOT_SKIN, "iodine", 1, 0.0); val_key(FOOT_SKIN, "iodine", S["scalpel"][0] - 1, 0.0); val_key(FOOT_SKIN, "iodine", S["scalpel"][0], 1.0)

# ---------------- JARROHLIK: mato, skalpel, qisqich, ildiz ----------------
SC0, SC1 = S["scalpel"]; EX0, EX1 = S["extract"]
DRAPE_M = mat("drape", (0.08, 0.32, 0.5), 0.85, sss=0.05)
drape = empty("drape", (0, 0, 0), mf)
for nm, sz, lc in (("dL", (0.06, 0.2), (-0.045, 0.05, 0.0006)), ("dR", (0.06, 0.2), (0.075, 0.05, 0.0006)), ("dB", (0.2, 0.08), (0.02, 0.1, 0.03))):
    pl = plane(nm, sz, lc, DRAPE_M, parent=drape)
    if nm == "dB": pl.rotation_euler = (R(-25), 0, 0)
vis(drape, rng("scalpel", "extract"))
LINE_Y0, LINE_Y1 = 0.0, 0.03
scalpel = empty("scalpel", (0, 0, 0), mf)
blade = box("sc_blade", (0.0003, 0.005, 0.012), (0, 0.0015, 0.006), steel_m, parent=scalpel)
for v in blade.data.vertices:                     # uchi o'tkir (pastda, -Y tomonda)
    if v.co.z < 0.001 and v.co.y > 0: v.co.y = -0.0008; v.co.z = 0.0
box("sc_handle", (0.0032, 0.0045, 0.075), (0, 0.001, 0.049), dark_steel, parent=scalpel, bevel=0.0007)
scalpel.rotation_euler = (R(18), R(32), 0)
for f, y, dz in ((SC0, -0.004, 0.012), (SC0 + 8, 0.002, 0.001), (SC1 - 5, 0.028, 0.0008), (SC1, 0.03, 0.01)):
    key(scalpel, f, loc=(LINE_X, y, toe_surface_z(LINE_X, max(y, 0.004)) + dz))
interp(scalpel, "LINEAR")
vis(scalpel, rng("scalpel"))
val_key(NAIL_M, "line", 1, 0.0); val_key(NAIL_M, "line", SC0 + 8, 0.0); val_key(NAIL_M, "line", SC1 - 5, 1.0)
interp(NAIL_M.node_tree, "LINEAR", None)
# ildiz (oq "matriks") — bo'lakning ildiz uchiga yopishgan, burma ostida yashiringan
ROOT_M = mat("matrix", (0.92, 0.78, 0.74), 0.35, sss=0.5, coat=0.5)
GRIP = V((-1.0 - 0.55) / 2 * NW, 0.004, toe_surface_z(-0.7 * NW, 0.006) + 0.0006)
stripE = empty("strip_pull", tuple(GRIP), mf)
rootb = sphere("nail_root", 0.003, ((-1.0 - 0.55) / 2 * NW, Y_ROOT + 0.002, toe_surface_z(-0.7 * NW, Y_ROOT) - 0.0012), ROOT_M, scale=(0.75, 1.3, 0.45), parent=mf)
rootb2 = sphere("nail_root_b", 0.0016, ((-1.0 - 0.55) / 2 * NW, Y_ROOT + 0.0045, toe_surface_z(-0.7 * NW, Y_ROOT) - 0.0018), blood_m, scale=(1.0, 1.0, 0.6), parent=mf)
for o in (nailB, rootb, rootb2):
    o.parent = stripE; o.matrix_parent_inverse = Matrix.Translation(-GRIP)
vis(rootb, rng("extract"), recursive=False); vis(rootb2, rng("extract"), recursive=False)
# qisqich (forseps)
forceps = empty("forceps", (0, 0, 0), mf)
for sx in (-1, 1):
    arm_ = box(f"fc_arm{sx}", (0.0016, 0.09, 0.0012), (sx * 0.0012, -0.045, 0.0), steel_m, rot=(0, 0, -sx * 1.2), parent=forceps, bevel=0.0003)
forceps.rotation_euler = (R(25), 0, R(-35))
for f, d in ((EX0, V(-0.02, -0.03, 0.03)), (EX0 + 8, V(0, 0, 0)), (EX0 + 12, V(0, 0, 0))):
    key(forceps, f, loc=tuple(GRIP + d))
PULL = [(EX0 + 12, V(0, 0, 0), 0), (EX0 + 22, V(-0.002, -0.004, 0.006), 18), (EX1 - 6, V(-0.006, -0.03, 0.024), 32), (EX1, V(-0.007, -0.034, 0.026), 34)]
for f, d, a in PULL:
    key(stripE, f, loc=tuple(GRIP + d), rot=(a, 0, 0)); key(forceps, f, loc=tuple(GRIP + d + V(0, 0, 0.0)))
key(stripE, 1, loc=tuple(GRIP), rot=(0, 0, 0))
vis(forceps, rng("extract"))
# bo'lak sug'urilgandan keyin qonli ariqcha
groove = box("groove", (0.0034, 0.024, 0.0012), (-0.775 * NW, 0.015, toe_surface_z(-0.775 * NW, 0.015) - 0.0002), blood_m, parent=mf, bevel=0.0005)
vis(groove, [(EX0 + 14, EX1)], recursive=False)

# ======================================================================
# 2) KESIM (0,60,0): bosh barmoqning ko'ndalang kesimi, 10x. Kesim yuzasi y=0 da -Y ga qaraydi; profil XZ (real mm)
# ======================================================================
CUT = V(0, 60, 0)
cutp = empty("CUT", tuple(CUT))
U = 0.01                       # 1 real mm -> 1 sm (10x)
DEPTH = 30 * U
CRX, CRZ, CZC = 12.5, 10.5, 10.5
def gfun(x): return 1.0 - smooth(8.2, 9.6, abs(x))
def groove_z(x): return CZC + CRZ * math.sqrt(max(0.0, 1 - (x / CRX) ** 2)) - 1.1 * gfun(x)
def flesh_prof(fk=0.0, swell=0.0, n=180):
    pts = []
    for i in range(n):
        th = -math.pi / 2 + 2 * math.pi * i / n
        x = CRX * math.cos(th) * (1 + 0.05 * swell * max(0, -math.cos(th))); s_ = math.sin(th)
        z = CZC + CRZ * s_ * (0.92 if s_ < 0 else 1.0)
        if s_ > 0.15:
            z -= 1.1 * gfun(x)
            z += 1.3 * math.exp(-((x - 9.9) / 1.2) ** 2)
            z += (1.3 + 1.7 * fk + 1.0 * swell) * math.exp(-((x + 9.9 - 1.6 * fk) / (1.2 + 0.7 * fk + 0.5 * swell)) ** 2)
        pts.append((x, z))
    return pts
def offset_prof(pts, d):
    """CCW profilni ichkariga d mm siljitish"""
    out = []; n = len(pts)
    for i in range(n):
        t = (V(*pts[(i + 1) % n], 0) - V(*pts[i - 1], 0)).normalized()
        out.append((pts[i][0] - d * t.y, pts[i][1] + d * t.x))
    return out
def prism(name, prof_keys, y0, m_face, m_side, parent=cutp, depth=DEPTH):
    """prof_keys: [(nomi, [(x,z)...]), ...] — birinchisi Basis; keyingilari zanjir shape key"""
    base = prof_keys[0][1]; n = len(base)
    def vco(prof):
        return [(x * U, y0, z * U) for x, z in prof] + [(x * U, y0 + depth, z * U) for x, z in prof]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n; faces.append((i, j, n + j, n + i))
    me = bpy.data.meshes.new(name); me.from_pydata(vco(base), [], faces); me.update()
    o = bpy.data.objects.new(name, me); P.link(o, parent)
    me.materials.append(m_face); me.materials.append(m_side)
    for k, p in enumerate(me.polygons):
        p.material_index = 0 if k < 2 else 1; p.use_smooth = k >= 2
    if len(prof_keys) > 1:
        prev = o.shape_key_add(name="Basis", from_mix=False)
        for nm, prof in prof_keys[1:]:
            kb = o.shape_key_add(name=nm, from_mix=False); kb.value = 0.0; kb.relative_key = prev
            for vi, p in enumerate(vco(prof)): kb.data[vi].co = p
            prev = kb
    return o
def skey(o, name, pts):
    for f, v in pts:
        kb = o.data.shape_keys.key_blocks[name]; kb.value = v; kb.keyframe_insert("value", frame=f)

def tissue_mat(name, col, var=0.15, scale=40.0, inflam_pt=None, coat=0.4, sss=0.2):
    m = mat(name, col, 0.45, coat=coat, sss=sss); N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Subsurface Scale"].default_value = 0.004
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale * 0.6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; c.inputs[6].default_value = (*[x * (1 - var) for x in col], 1)
    c.inputs[7].default_value = (*[min(1, x * (1 + var)) for x in col], 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", vo.outputs["Distance"], nz.outputs["Fac"]), 0.8), c.inputs["Factor"])
    out = c.outputs[2]
    if inflam_pt is not None:
        inf = value_node(m, "inflam", 0.0)
        d = world_dist(N, L, inflam_pt)
        f = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", d, P.math_n(N, L, "ADD", 0.01, P.math_n(N, L, "MULTIPLY", inf, 0.06))), clamp=True)
        f = P.math_n(N, L, "MULTIPLY", f, P.math_n(N, L, "MINIMUM", P.math_n(N, L, "MULTIPLY", inf, 2.0), 1.0))
        c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(out, c2.inputs[6]); c2.inputs[7].default_value = (0.55, 0.0, 0.02, 1)
        L.new(f, c2.inputs["Factor"]); out = c2.outputs[2]
        b.inputs["Emission Color"].default_value = (1.0, 0.06, 0.02, 1)
        pul = value_node(m, "pulse", 0.0)
        L.new(P.math_n(N, L, "MULTIPLY", f, P.math_n(N, L, "ADD", 0.15, pul)), b.inputs["Emission Strength"])
    L.new(out, b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(vo.outputs["Distance"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    return m
INF_PT = CUT + V(-10.2, 0, 14.5) * U
SKIN_X = P.skin_material("cut_skin", base=(0.8, 0.52, 0.42), prints=False)
SKIN_X.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.004
EPI_M = tissue_mat("epi", (0.85, 0.58, 0.5), 0.08, 60)
DERM_M = tissue_mat("derm", (0.7, 0.2, 0.18), 0.2, 30, inflam_pt=INF_PT)
FAT_M = tissue_mat("fatx", (0.95, 0.72, 0.28), 0.18, 18, coat=0.5)
BONE_M = tissue_mat("bonex", (0.9, 0.85, 0.72), 0.08, 40, coat=0.1, sss=0.05)
MARROW_M = tissue_mat("marrow", (0.42, 0.1, 0.07), 0.45, 90)
BED_M = tissue_mat("bedx", (0.72, 0.06, 0.07), 0.15, 50, coat=0.6)
NAILCUT_M = mat("nailcut", (0.9, 0.8, 0.68), 0.2, coat=0.8, sss=0.3)
# go'sht (tashqi teri yuzasi + kesim)
fp0 = flesh_prof(); fp1 = flesh_prof(1.0); fp2 = flesh_prof(1.0, 1.0)
flesh = prism("x_flesh", [("b", fp0), ("fold", fp1), ("swell", fp2)], 0.0, EPI_M, SKIN_X)
derm = prism("x_derm", [("b", offset_prof(fp0, 0.9)), ("fold", offset_prof(fp1, 0.9)), ("swell", offset_prof(fp2, 0.9))], -0.0012, DERM_M, DERM_M)
def ell(cx, cz, rx, rz, n=64): return [(cx + rx * math.cos(2 * math.pi * i / n), cz + rz * math.sin(2 * math.pi * i / n)) for i in range(n)]
fat = prism("x_fat", [("b", [(x, z) for x, z in ell(0, 5.6, 9.2, 4.2, 96)])], -0.0024, FAT_M, FAT_M)
# yog' bo'lakchalari (septa) — kichik ellipslar
for i, (cx, cz, rx, rz) in enumerate(((-5, 5, 2.4, 1.8), (-1, 4, 2.6, 2.0), (3.6, 5.2, 2.4, 1.9), (6.5, 6.4, 1.6, 1.4), (-7.3, 6.6, 1.5, 1.3), (1.0, 7.6, 2.0, 1.2))):
    prism(f"x_lob{i}", [("b", ell(cx, cz, rx, rz, 40))], -0.0030, tissue_mat(f"lob{i}", (0.98, 0.8, 0.34), 0.12, 22, coat=0.6), FAT_M)
bone = prism("x_bone", [("b", ell(0, 11.6, 5.3, 3.3, 80))], -0.0036, BONE_M, BONE_M)
marrow = prism("x_marrow", [("b", ell(0, 11.6, 3.7, 2.0, 64))], -0.0042, MARROW_M, MARROW_M)
for i, (cx, cz, r, c) in enumerate(((-6.8, 3.4, 0.55, (0.6, 0.02, 0.03)), (6.6, 3.2, 0.5, (0.6, 0.02, 0.03)), (-7.6, 2.6, 0.38, (0.95, 0.88, 0.55)),
                                   (7.4, 2.4, 0.36, (0.95, 0.88, 0.55)), (-3.0, 1.7, 0.3, (0.6, 0.02, 0.03)), (3.2, 1.6, 0.3, (0.25, 0.15, 0.5)))):
    prism(f"x_vessel{i}", [("b", ell(cx, cz, r, r, 24))], -0.0045, mat(f"vx{i}", c, 0.3, coat=0.7, emit=0.15), mat(f"vxs{i}", c, 0.3))
# tirnoq plastinkasi va tirnoq o'rni (chap cheti qisqaradi: "retract")
def band_ccw(xl, xr, z0, z1, n=90):
    xs = [-xl + (xl + xr) * i / (n - 1) for i in range(n)]
    return [(x, groove_z(x) + z0) for x in xs] + [(x, groove_z(x) + z1) for x in reversed(xs)]
nailx = prism("x_nail", [("b", band_ccw(9.3, 9.3, 0.05, 1.05)), ("retract", band_ccw(6.0, 9.3, 0.05, 1.05))], -0.0050, NAILCUT_M, NAIL_M)
bed = prism("x_bed", [("b", band_ccw(8.8, 8.8, -0.45, 0.05)), ("retract", band_ccw(6.0, 8.8, -0.45, 0.05))], -0.0047, BED_M, BED_M)
S5, S5e = S["short"]; S6, S6e = S["fold"]
skey(nailx, "retract", ((1, 0.0), (S5 + 6, 0.0), (S5e - 4, 1.0))); skey(bed, "retract", ((1, 0.0), (S5 + 6, 0.0), (S5e - 4, 1.0)))
for o in (flesh, derm):
    skey(o, "fold", ((1, 0.0), (S6 + 4, 0.0), (S6e - 6, 1.0)))
    skey(o, "swell", ((1, 0.0), (S["nostop"][0], 0.2), (S["deeper"][1], 1.0)))
# tig' (o'sib kirayotgan tirnoq cheti): ildizi chap chetda, +X lokal bo'ylab etga kiradi
def blade_mat(name):
    m = mat(name, (0.92, 0.82, 0.72), 0.12, coat=1.0, sss=0.2); N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    gl = value_node(m, "glint", -1.0)
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    xx = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ADD", sp.outputs["X"], P.math_n(N, L, "MULTIPLY", sp.outputs["Z"], 0.6)), 6.5 * U)
    band_ = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", xx, gl)), 0.12), clamp=True)
    b.inputs["Emission Color"].default_value = (1, 0.97, 0.9, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", band_, 2.0), 9.0), b.inputs["Emission Strength"])
    return m
BLADE_M = blade_mat("blade")
BX = -6.0; BZ0 = groove_z(BX) + 0.05; BZ1 = groove_z(BX) + 1.05
bladeE = empty("blade_root", tuple(CUT + V(BX * U, -0.0052, (BZ0 + BZ1) / 2 * U)))
LB = 6.5
bl_prof = [(0, -0.35), (LB * 0.55, -0.3), (LB, 0.0), (LB * 0.55, 0.3), (0, 0.35)]
bl = prism("x_blade", [("b", bl_prof)], 0.0, BLADE_M, BLADE_M, parent=bladeE, depth=DEPTH * 0.6)
bladeE.rotation_euler = (0, R(132), 0)
BL0, BL1 = S["blade"]; IN0, IN1 = S["inward"]; NS0, NS1 = S["nostop"]; DP0, DP1 = S["deeper"]
for f, s in ((1, 0.001), (BL0 - 1, 0.001), (BL0, 0.42), (BL1, 0.5), (IN0, 0.5), (IN1, 1.0), (NS0, 1.0), (NS1, 1.22), (DP0, 1.22), (DP1, 1.42)):
    key(bladeE, f, scale=(s, 1, 1))
interp(bladeE, "LINEAR")
for f, g in ((BL0 + 4, -0.3), (BL0 + 40, 1.3), (BL0 + 41, -0.3), (BL1, 1.3), (NS0, -0.3), (NS0 + 16, 1.3)):
    val_key(BLADE_M, "glint", f, g)
interp(BLADE_M.node_tree, "LINEAR")
val_key(DERM_M, "inflam", 1, 0.0); val_key(DERM_M, "inflam", IN0 + 10, 0.0); val_key(DERM_M, "inflam", IN1, 0.35)
val_key(DERM_M, "inflam", NS1, 0.55); val_key(DERM_M, "inflam", DP1, 1.0)
val_key(DERM_M, "pulse", 1, 0.0)
for f in list(range(NS0 + 2, NS1, 10)) + list(range(DP0 + 2, DP1, 9)):
    val_key(DERM_M, "pulse", f, 0.0); val_key(DERM_M, "pulse", f + 2, 1.6); val_key(DERM_M, "pulse", f + 7, 0.1)
# yiring cho'ntagi (tig' uchi atrofida)
PUSX_M = tissue_mat("pusx", (0.95, 0.85, 0.35), 0.12, 30, coat=0.9)
pusE = empty("pus_x", tuple(CUT + V(-10.6 * U, -0.0058, 14.0 * U)))
prism("x_pus", [("b", ell(0, 0, 2.0, 1.4, 48))], 0.0, PUSX_M, PUSX_M, parent=pusE, depth=DEPTH * 0.4)
for f, s in ((1, 0.001), (DP0 + 4, 0.001), (DP1 - 6, 1.0), (DP1, 1.08)):
    key(pusE, f, scale=(s, 1, s))
rxb = random.Random(3)
for i in range(16):
    b_ = uvsphere(f"xbact{i}", (0, 0, 0), (0.0012, 0.0012, 0.0035), BACT_M, parent=None, seg=16, rings=8)
    c0 = CUT + V((-10.6 + rxb.uniform(-1.6, 1.6)) * U, -0.0075, (14.0 + rxb.uniform(-1.0, 1.0)) * U)
    ph_ = rxb.uniform(0, 6.3)
    for f in range(DP0, DP1 + 1, 3):
        key(b_, f, loc=tuple(c0 + V(0.002 * math.sin(f * 0.2 + ph_), 0, 0.002 * math.cos(f * 0.25 + ph_))), rot=(R(90), R(f * 6 + ph_ * 40), 0))
    vis(b_, [(DP0 + 18, DP1)], recursive=False)
CUT_OBJS = [o for o in bpy.data.objects if o.name.startswith("x_")] + [bladeE, pusE]

# makro fon: sochiq + laminat pol
towel_m = mat("towel", (0.78, 0.82, 0.8), 0.95, sss=0.05)
tn = towel_m.node_tree.nodes; tl = towel_m.node_tree.links
_tc = tn.new("ShaderNodeTexCoord"); _w = tn.new("ShaderNodeTexWave"); _w.inputs["Scale"].default_value = 900.0; _w.inputs["Distortion"].default_value = 6.0
tl.new(_tc.outputs["Object"], _w.inputs["Vector"]); _bp = tn.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.6
tl.new(_w.outputs["Fac"], _bp.inputs["Height"]); tl.new(_bp.outputs[0], tn["Principled BSDF"].inputs["Normal"])
plane("m_towel", (0.5, 0.45), (0.05, 0.12, 0.0), towel_m, parent=mf)
floor_m = pbr("floor", "laminate_floor_02", 0.5)
plane("m_floor", (2.0, 2.0), (0.0, 0.3, -0.003), floor_m, parent=mf)

# ======================================================================
# 3) XONA (0,0,0): divan, stol, o'simlik; Megan divanda engashib tirnoq oladi
# ======================================================================
room = empty("ROOM")
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.88, 0.84, 0.78))
plane("r_floor", (7, 7), (0, -1.0, 0), floor_m, parent=room)
box("r_wallB", (7, 0.12, 2.8), (0, 0.75, 1.4), wall_m, parent=room)
box("r_wallL", (0.12, 6, 2.8), (-2.4, -1.5, 1.4), wall_m, parent=room)
box("r_wallR", (0.12, 6, 2.8), (2.6, -1.5, 1.4), wall_m, parent=room)
box("r_ceil", (7, 7, 0.05), (0, -1.0, 2.82), mat("ceil", (0.9, 0.9, 0.88), 0.8), parent=room)
box("r_base", (7, 0.02, 0.1), (0, 0.68, 0.05), mat("trim", (0.92, 0.92, 0.9), 0.35), parent=room)
plane("r_window", (1.2, 1.3), (-2.33, -0.9, 1.5), mat("rwin", (1, 1, 1), emit=4.0, emit_col=(0.9, 0.95, 1.0)), rot=(90, 0, 90), parent=room)
sofa = import_gltf(PH + "Sofa_01/Sofa_01.gltf", (0, 0.3, 0), (0, 0, 0), 1.0, parent=room)
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-1.0, -1.1, 0), (0, 0, 90), 1.0, parent=room)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-1.25, 0.4, 0), (0, 0, 20), 1.1, parent=room)
plane("r_rug", (2.2, 1.6), (0.2, -0.75, 0.002), mat("rug", (0.55, 0.42, 0.33), 0.95), parent=room)
sc.frame_set(1); bpy.context.view_layer.update()
SEAT_Z = 0.42
hit = sc.ray_cast(bpy.context.view_layer.depsgraph, V(0.0, 0.15, 0.62), V(0, 0, -1))
if hit[0]: SEAT_Z = hit[1].z
print("SEAT_Z", SEAT_Z)

# ======================================================================
# 4) KO'CHA (20,0,0): trotuar, yo'l, bino devori
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
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)
SIT = A_("Female_Sitting_Pose_8.fbx", inplace=False)
strip(meg, SIT, S["room"][0] - 10, repeat=span(SIT, 50))
WALK = A_("Female_Walk.fbx"); strip(meg, WALK, S["shoe"][0] - 12, repeat=span(WALK, 90))
LIMP = A_("Injured_Walk.fbx"); strip(meg, LIMP, S["limp"][0] - 12, repeat=span(LIMP, 50))
WSPD = 1.22 / 24.0; LSPD = 1.22 / 24.0
SEAT_DZ = float(os.environ.get("SEAT_DZ", 0.0))
RK = []
def rkey(f, loc, rot, mode):
    mroot.location = loc; mroot.rotation_euler = (0, 0, R(rot))
    mroot.keyframe_insert("location", frame=f); mroot.keyframe_insert("rotation_euler", frame=f); RK.append((f, mode))
rkey(1, (0.0, -0.18, SEAT_Z - 0.5 + SEAT_DZ), -45, "CONSTANT")
SH0, SH1 = S["shoe"]; LI0, LI1 = S["limp"]
rkey(SH0 - 12, tuple(ST + V(0, 2.6 + 12 * WSPD, 0.14)), 0, "LINEAR")
rkey(SH1, tuple(ST + V(0, 2.6 - (SH1 - SH0) * WSPD, 0.14)), 0, "CONSTANT")
rkey(LI0 - 12, tuple(ST + V(0.2, 0.6 + 12 * LSPD, 0.14)), 0, "LINEAR")
rkey(LI1 + 2, tuple(ST + V(0.2, 0.6 - (LI1 + 2 - LI0) * LSPD, 0.14)), 0, "CONSTANT")
for fc in fcurves(mroot):
    for k in fc.keyframe_points:
        k.interpolation = dict(RK).get(int(round(k.co.x)), "CONSTANT")
# qo'lda qaychi (xona)
handE = child_of_bone("meg_rhand", meg, "RightHand")
mclip, _h = build_clipper("meg_clipper", None, 1.0)
mclip.parent = handE; mclip.location = (0.0, 0.1, 0.03); mclip.rotation_euler = (R(90), 0, 0)
vis(mclip, ROOM_R)
# krossovka rentgeni
SNK = next(o for o in mmeshes if o.name.endswith("Sneakers"))
xsh = P.xray_material("xr_shoe", (0.35, 0.75, 1.0), 1.4, 0.02)
gsn = SNK.copy(); gsn.name = "sneaker_xray"; sc.collection.objects.link(gsn); gsn.animation_data_clear()
for slot in gsn.material_slots: slot.link = "OBJECT"; slot.material = xsh
toeE = child_of_bone("meg_rtoe", meg, "RightToeBase")
HOT_M = mat("hot_toe", (0.9, 0.1, 0.05), 0.4, emit=3.0, emit_col=(1.0, 0.12, 0.03))
hot = sphere("hot_toe", 0.022, (0.0, 0.05, 0.0), HOT_M, scale=(1.0, 1.3, 0.7), parent=toeE)
HAZE_M = bpy.data.materials.new("haze"); HAZE_M.use_nodes = True
_hn = HAZE_M.node_tree.nodes; _hl = HAZE_M.node_tree.links; _hn.remove(_hn["Principled BSDF"])
_em = _hn.new("ShaderNodeEmission"); _em.inputs["Color"].default_value = (1.0, 0.35, 0.08, 1); _em.inputs["Strength"].default_value = 1.5
_tr = _hn.new("ShaderNodeBsdfTransparent"); _mx = _hn.new("ShaderNodeMixShader"); _mx.inputs[0].default_value = 0.12
_hl.new(_tr.outputs[0], _mx.inputs[1]); _hl.new(_em.outputs[0], _mx.inputs[2]); _hl.new(_mx.outputs[0], _hn["Material Output"].inputs[0])
sphere("haze_toe", 0.045, (0.0, 0.03, 0.0), HAZE_M, scale=(1.0, 1.5, 0.8), parent=toeE)
STEAM_M = mat("steam", (0.95, 0.97, 1.0), 0.1, alpha=0.35, emit=0.4)
rs = random.Random(4)
steamE = empty("steam_follow"); _cl = steamE.constraints.new("COPY_LOCATION"); _cl.target = toeE
for i in range(18):
    st_ = sphere(f"steam{i}", rs.uniform(0.006, 0.014), (0, 0, 0), STEAM_M, parent=steamE)
    ph_ = rs.uniform(0, 1); x0 = rs.uniform(-0.05, 0.05); y0 = rs.uniform(-0.04, 0.12)
    for f in range(F_XRAY, SH1 + 2, 3):
        t = ((f - F_XRAY) / 30.0 + ph_) % 1.0
        key(st_, f, loc=(x0 * (1 + t), y0 - 0.04, 0.03 + 0.16 * t), scale=0.4 + 1.2 * t)
vis(toeE, [(F_XRAY, SH1)]); vis(steamE, [(F_XRAY, SH1)])
mesh_on = ROOM_R + STR_R
for o in mmeshes:
    if o is SNK: vis(o, [(SH0, F_XRAY - 1), (LI0, LI1)], recursive=False)
    else: vis(o, mesh_on, recursive=False)
vis(gsn, [(F_XRAY, SH1)], recursive=False)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
M = lambda *a: MF + V(*a)
NC = V(0, 0.015, toe_surface_z(0, 0.015) + 0.0004)
HK0, HK1 = S["hook"]
c = abs_cam("hook", [(HK0, M(0.05, -0.2, 0.012)), (HK1, M(0.012, -0.07, 0.028))], [(HK0, MF + NC + V(0.01, 0, -0.006)), (HK1, MF + CL0)], 16, 5.6, clip=0.001)
lens_keys(c, [(HK0, 16), (HK1, 30)])
c = abs_cam("clip", [(C0, MF + NC + V(-0.035, -0.07, 0.06)), (C1, MF + NC + V(0.035, -0.068, 0.058))], [(C0, MF + NC + V(0, -0.007, 0)), (C1, MF + NC + V(0, -0.006, 0))], 45, 16.0, clip=0.001)
for f in (SNAP_L, SNAP_R): shake(c, f, f + 6, 0.0015, seed=f)
RM0, RM1 = S["room"]
c = abs_cam("room", [(RM0, V(1.35, -2.0, 0.22)), (RM1, V(0.7, -2.1, 0.2))], [(RM0, V(0.1, -0.3, 0.62)), (RM1, V(0.05, -0.3, 0.6))], 16, 4.0, clip=0.05)
TC = MF + V(0, TY, 0.012)
c = abs_cam("trap", [(T0, TC + V(0.1, -0.15, 0.06)), (F_TRAP, TC + V(0.07, -0.11, 0.045)), (F_TRAP + 4, TC + V(0.055, -0.085, 0.04)), (T1, TC + V(0.05, -0.08, 0.038))],
            [(T0, TC + V(0, 0, 0.004)), (T1, TC + V(0, 0, 0.006))], 24, 8.0, clip=0.001)
lens_keys(c, [(T0, 24), (F_TRAP, 28), (F_TRAP + 4, 40), (T1, 42)])
shake(c, F_TRAP, F_TRAP + 9, 0.004, seed=5)
CF = CUT + V(0, 0, 12.0 * U); EDGE = CUT + V(-8.0 * U, 0, 18.0 * U)
SH_0, SH_1 = S["short"]
c = abs_cam("short", [(SH_0, CF + V(-0.2, -0.78, -0.08)), (SH_1, CF + V(0.06, -0.7, -0.02))], [(SH_0, CF + V(0, 0, 0.01)), (SH_1, CF + V(-0.01, 0, 0.02))], 30, 8.0, clip=0.01)
FO0, FO1 = S["fold"]
c = abs_cam("fold", [(FO0, CF + V(-0.04, -0.66, 0.02)), (FO1, EDGE + V(0.04, -0.36, 0.02))], [(FO0, CF + V(-0.02, 0, 0.02)), (FO1, EDGE)], 30, 8.0, clip=0.01)
GR0, GR1 = S["grow"]
c = abs_cam("grow", [(GR0, MF + NC + V(-0.02, -0.04, 0.085)), (GR1, MF + NC + V(0.03, -0.03, 0.08))], [(GR0, MF + NC + V(0, -0.004, 0)), (GR1, MF + NC + V(0, -0.003, 0))], 50, 18.0, clip=0.001)
TIP1 = CUT + V(-8.4 * U, 0, 17.4 * U); TIP2 = CUT + V(-10.3 * U, 0, 14.9 * U); TIP3 = CUT + V(-11.2 * U, 0, 13.6 * U)
c = abs_cam("blade", [(BL0, TIP1 + V(0.13, -0.27, 0.1)), (BL1, TIP1 + V(-0.12, -0.25, 0.05))], [(BL0, TIP1), (BL1, TIP1 + V(0, 0, -0.005))], 40, 8.0, clip=0.01)
c = abs_cam("inward", [(IN0, TIP2 + V(0.09, -0.34, 0.07)), (IN1, TIP2 + V(0.03, -0.22, 0.03))], [(IN0, TIP1), (IN1, TIP2)], 35, 8.0, clip=0.01)
PI0, PI1 = S["pierce"]
PWW = MF + PW
c = abs_cam("pierce", [(PI0, PWW + V(-0.075, -0.05, 0.012)), (F_PIERCE, PWW + V(-0.058, -0.04, 0.013)), (PI1, PWW + V(-0.05, -0.035, 0.016))],
            [(PI0, PWW + V(0.002, 0.002, -0.001)), (PI1, PWW)], 55, 16.0, clip=0.001)
shake(c, F_PIERCE, F_PIERCE + 8, 0.0015, seed=7)
shoeT = empty("shoe_t"); _cl = shoeT.constraints.new("COPY_LOCATION"); _cl.target = toeE
c = shot_cam("shoe", tuple(ST + V(0.32, -1.5, 0.21)), shoeT, 16, 4.0, focus=shoeT, clip=0.02)
path_keys(c, [(SH0, ST + V(0.32, -1.5, 0.21)), (F_XRAY - 6, ST + V(0.3, -1.35, 0.2)), (SH1, ST + V(0.28, -1.2, 0.2))])
lens_keys(c, [(SH0, 16), (F_XRAY - 9, 18), (F_XRAY - 3, 50), (SH1, 58)])
shake(c, F_XRAY - 3, F_XRAY + 4, 0.006, seed=11)
BA0, BA1 = S["bact"]
c = abs_cam("bact", [(BA0, PWW + V(-0.05, -0.06, 0.05)), (BA1, PWW + V(-0.03, -0.035, 0.03))], [(BA0, PWW + V(0.003, 0.004, 0.002)), (BA1, PWW)], 50, 16.0, clip=0.001)
SW0, SW1 = S["swell"]
c = abs_cam("swell", [(SW0, PWW + V(-0.06, -0.1, 0.055)), (SW1, PWW + V(-0.05, -0.085, 0.045))], [(SW0, PWW + V(0.006, 0.006, -0.003)), (SW1, PWW + V(0.005, 0.005, -0.002))], 40, 14.0, clip=0.001)
for bt in BEATS:
    if SW0 <= bt <= SW1: shake(c, bt, bt + 4, 0.0012, seed=bt)
PU0, PU1 = S["pus"]
c = abs_cam("pus", [(PU0, PWW + V(-0.06, -0.06, 0.03)), (PU1, PWW + V(-0.05, -0.05, 0.026))], [(PU0, PWW + V(0, 0.002, -0.001)), (PU1, PWW + V(0, 0.001, 0))], 40, 16.0, clip=0.001)
lens_keys(c, [(PU0, 40), (PU0 + 8, 85), (PU1, 92)])
shake(c, PU0 + 6, PU0 + 12, 0.0012, seed=21)
for bt in BEATS:
    if PU0 + 12 <= bt <= PU1: shake(c, bt, bt + 4, 0.0006, seed=bt)
limpT = empty("limp_t"); _cl = limpT.constraints.new("COPY_LOCATION"); _cl.target = mroot
limpO = empty("limp_o", (0, 0, 0.55), limpT)
c = shot_cam("limp", tuple(ST + V(-1.3, -1.2, 0.3)), limpO, 16, 4.0, focus=limpO, clip=0.02)
path_keys(c, [(LI0, ST + V(-1.3, -1.0, 0.3)), (LI1, ST + V(-1.15, -1.5, 0.28))])
c = abs_cam("nostop", [(NS0, TIP3 + V(0.11, -0.3, 0.08)), (NS1, TIP3 + V(0.06, -0.25, 0.05))], [(NS0, TIP2), (NS1, TIP3)], 35, 8.0, clip=0.01)
c = abs_cam("deeper", [(DP0, TIP3 + V(-0.06, -0.24, 0.03)), (DP1, TIP3 + V(-0.03, -0.17, 0.015))], [(DP0, TIP3), (DP1, TIP3 + V(0.004, 0, 0.0))], 35, 8.0, clip=0.01)
for f in range(DP0 + 4, DP1 - 4, 9): shake(c, f, f + 4, 0.003, seed=f)
c = abs_cam("scalpel", [(SC0, MF + NC + V(-0.055, -0.075, 0.022)), (SC1, MF + NC + V(-0.04, -0.055, 0.028))],
            [(SC0, MF + V(LINE_X, 0.004, NC.z)), (SC1, MF + V(LINE_X, 0.024, NC.z))], 45, 14.0, clip=0.001)
c = abs_cam("extract", [(EX0, MF + NC + V(-0.075, -0.06, 0.04)), (EX1, MF + NC + V(-0.09, -0.085, 0.06))],
            [(EX0, MF + GRIP), (EX1, MF + GRIP + V(-0.004, -0.02, 0.018))], 40, 11.0, clip=0.001)
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

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
bgC = env_bg("hospital_room.hdr", 0)
bgS = env_bg("studio_small_09.hdr", 30)
bgK = N.new("ShaderNodeBackground"); bgK.inputs[0].default_value = (0.004, 0.005, 0.01, 1)
a1 = N.new("ShaderNodeAddShader"); a2 = N.new("ShaderNodeAddShader"); a3 = N.new("ShaderNodeAddShader")
L.new(bgH.outputs[0], a1.inputs[0]); L.new(bgC.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], a2.inputs[0]); L.new(bgS.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], a3.inputs[0]); L.new(bgK.outputs[0], a3.inputs[1]); L.new(a3.outputs[0], out.inputs["Surface"])
SURG = ("scalpel", "extract")
for f, n in SHOTS:
    vals = {"H": 0.35 if n in ROOMN else 1.0 if n in STRN else 0.0, "C": 0.35 if n in SURG else 0.0,
            "S": 0.28 if (n in MACN and n not in SURG) else 0.0, "K": 1.0 if n in CUTN else 0.0}
    for bg, k in ((bgH, "H"), (bgC, "C"), (bgS, "S"), (bgK, "K")):
        bg.inputs[1].default_value = vals[k]; bg.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# xona
RT = empty("roomT", (0.1, -0.3, 0.7))
area("R_ceil", (0.3, -1.0, 2.7), 1.4, (1.0, 0.9, 0.78), lights_for(ROOM_R, 160.0), target=RT)
area("R_win", (-2.1, -0.9, 1.5), 1.2, (0.9, 0.95, 1.0), lights_for(ROOM_R, 260.0), target=RT)
area("R_rim", (1.2, 0.4, 1.8), 0.6, (1.0, 0.75, 0.5), lights_for(ROOM_R, 60.0), target=RT)
# ko'cha: quyosh
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(48), 0, R(-25)); sun.data.angle = R(1.5)
for f, e in lights_for(STR_R, 6.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
# makro
MT = empty("macT", tuple(MF + V(0.0, 0.015, 0.015)))
area("M_key", tuple(MF + V(-0.15, -0.2, 0.3)), 0.25, (1.0, 0.94, 0.86), lights_for(MAC_R, 5.5), target=MT)
area("M_fill", tuple(MF + V(0.25, -0.12, 0.12)), 0.2, (0.85, 0.92, 1.0), lights_for(MAC_R, 2.2), target=MT)
area("M_rim", tuple(MF + V(0.05, 0.3, 0.2)), 0.2, (1.0, 0.8, 0.6), lights_for(MAC_R, 6.0), target=MT)
area("M_surg", tuple(MF + V(0.0, 0.0, 0.5)), 0.4, (0.95, 0.98, 1.0), lights_for(rng(*SURG), 9.0), target=MT)
# kesim
CTT = empty("cutT", tuple(CF))
area("K_key", tuple(CF + V(0.55, -0.6, 0.5)), 0.7, (1.0, 0.95, 0.9), lights_for(CUT_R, 26.0), target=CTT)
area("K_fill", tuple(CF + V(-0.6, -0.4, -0.2)), 0.6, (1.0, 0.85, 0.75), lights_for(CUT_R, 9.0), target=CTT)
area("K_rim", tuple(CF + V(-0.3, 0.5, 0.5)), 0.5, (0.35, 0.6, 1.0), lights_for(CUT_R, 20.0), target=CTT)
# ko'rinish: har dunyo faqat o'z kadrlarida (bolalarning o'z vis kalitlari saqlanadi)
def has_vis(o): return any(fc.data_path == "hide_render" for fc in fcurves(o))
def vis_world(objs, ranges):
    for o in objs:
        if not has_vis(o): vis(o, ranges, recursive=False)
vis_world([mf] + list(mf.children_recursive), MAC_R)
vis_world([cutp] + list(cutp.children_recursive) + [bladeE, pusE] + list(bladeE.children_recursive) + list(pusE.children_recursive), CUT_R)
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
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
