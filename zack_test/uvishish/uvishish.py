# Oyoq uvishishi — Zack D. Films uslubida 45.2 s video (1085 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, zack_test/falaj/falaj.py (rentgen tana, kamera yordamchilari),
# procedural yordamchilar: zack_test/burish/parts.py (teri kesimi, quvur, miya, rentgen)
# Assetlar: zack_test/tools/get_uvishish.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/uvishish/uvishish.py --render
# Sinov: FRAMES=30,100,190,400,740 PCT=35 OUT=/tmp/claude-0/test/
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler, Quaternion
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
END = 1085
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (72, "numb"), (120, "stand"), (160, "needles"), (217, "pain"), (264, "blood"), (336, "pinch"),
         (414, "path"), (520, "hose"), (575, "squeeze"), (621, "release"), (695, "wake"), (759, "chaos"),
         (860, "ants"), (949, "reboot"), (1031, "short")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM = rng("hook", "stand", "pain", "short")
XR = rng("numb", "blood", "pinch", "path", "chaos", "reboot")
XR_SIT = rng("numb", "blood", "pinch", "path")
SKIN = rng("needles", "ants")
CABLE = rng("squeeze", "release", "wake")
YARD = rng("hose")
F_NUMB = 87            # "birdan"
F_STEP = 536           # "bosib (olingan)": krossovka shlangga tushadi
F_WAKE = 733           # "birdaniga"
F_ANT_N = 908          # "igna sanchilishi"
F_SHORT = 1043         # "qisqa tutashuv"

# ---------------- yordamchilar ----------------
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

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=24):
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
def ease(t): return t * t * (3 - 2 * t)

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def point(name, loc, r, col, keys, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc; l.visible_camera = False
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def area(name, loc, size, col, keys, target=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT"); l.visible_camera = False
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

# ---------------- impuls (asab) materiali ----------------
def nerve_mat(name, col=(0.95, 0.55, 0.05), pcol=(1.0, 0.62, 0.08), dead_col=(0.25, 0.25, 0.27)):
    """'u' bo'ylab impulslar poyezdi. count/phase/amp/glow; dead: u<dead qismi o'lik (kulrang),
    stop: u>stop da impuls ko'rinmaydi (qisilgan joydan o'tmaydi)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.2; b.inputs["Subsurface Scale"].default_value = 0.002
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"; u = ua.outputs["Fac"]
    cnt = value_node(m, "count", 3.0); ph = value_node(m, "phase", 0.0); amp = value_node(m, "amp", 0.0); gl = value_node(m, "glow", 0.6)
    dead = value_node(m, "dead", -1.0); stop = value_node(m, "stop", 2.0)
    x = P.math_n(N, L, "FRACT", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", u, cnt), ph))
    d = P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", x, 0.5))
    p = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", d, 0.1), clamp=True), 2.0)
    alive = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", u, dead), 0.03, clamp=True)
    pm = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", u, stop), 0.01, clamp=True), clamp=True)
    e = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", p, amp), pm), gl)
    L.new(P.math_n(N, L, "MULTIPLY", e, alive), b.inputs["Emission Strength"])
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; cm.inputs[6].default_value = (*dead_col, 1); cm.inputs[7].default_value = (*col, 1)
    L.new(alive, cm.inputs["Factor"]); L.new(cm.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (*pcol, 1)
    return m

def keys_linear(m, names=("phase",)):
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        lin = any(f'"{n}"' in fc.data_path for n in names)
        for k in fc.keyframe_points: k.interpolation = "LINEAR" if lin else "CONSTANT"

# ---------------- mesh chiziq -> quvur (armaturaga bog'lanadigan asab/tomir) ----------------
_MT = None
def mesh_tube_group():
    global _MT
    if _MT: return _MT
    ng = bpy.data.node_groups.new("MeshTube", "GeometryNodeTree"); I = ng.interface
    I.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    s = I.new_socket("Radius", in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = 0.004
    I.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")
    I.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    m2c = N.new("GeometryNodeMeshToCurve"); L.new(gi.outputs[0], m2c.inputs["Mesh"])
    sm0 = N.new("GeometryNodeCurveSplineType"); sm0.spline_type = "CATMULL_ROM"; L.new(m2c.outputs[0], sm0.inputs["Curve"])
    rs = N.new("GeometryNodeResampleCurve"); rs.inputs["Count"].default_value = 120; L.new(sm0.outputs[0], rs.inputs["Curve"])
    par = N.new("GeometryNodeSplineParameter")
    st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = "FLOAT"; st.domain = "POINT"; st.inputs["Name"].default_value = "u"
    L.new(rs.outputs[0], st.inputs["Geometry"]); L.new(par.outputs["Factor"], st.inputs["Value"])
    circ = N.new("GeometryNodeCurvePrimitiveCircle"); circ.inputs["Resolution"].default_value = 8; circ.inputs["Radius"].default_value = 1.0
    cm = N.new("GeometryNodeCurveToMesh"); L.new(st.outputs[0], cm.inputs["Curve"]); L.new(circ.outputs["Curve"], cm.inputs["Profile Curve"])
    L.new(gi.outputs["Radius"], cm.inputs["Scale"]); cm.inputs["Fill Caps"].default_value = True
    ss = N.new("GeometryNodeSetShadeSmooth"); L.new(cm.outputs[0], ss.inputs["Geometry"])
    sm = N.new("GeometryNodeSetMaterial"); L.new(ss.outputs[0], sm.inputs["Geometry"]); L.new(gi.outputs["Material"], sm.inputs["Material"])
    L.new(sm.outputs[0], go.inputs[0])
    _MT = ng
    return ng

_PN = None
def pinch_group():
    """mahalliy koordinatada x=CX atrofida (kenglik W) z ni yassilaydi, y ni kengaytiradi: S (0..1)"""
    global _PN
    if _PN: return _PN
    ng = bpy.data.node_groups.new("Pinch", "GeometryNodeTree"); I = ng.interface
    I.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm, dv in (("S", 0.0), ("W", 0.3), ("CX", 0.0), ("Z0", 0.0)):
        s = I.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = dv
    I.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pos = N.new("GeometryNodeInputPosition"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sp.inputs[0])
    x, y, z = sp.outputs
    dx = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", x, gi.outputs["CX"]), gi.outputs["W"])
    g = P.math_n(N, L, "EXPONENT", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", dx, dx), -1.0))
    sg = P.math_n(N, L, "MULTIPLY", g, gi.outputs["S"])
    zr = P.math_n(N, L, "SUBTRACT", z, gi.outputs["Z0"])
    nz = P.math_n(N, L, "ADD", gi.outputs["Z0"], P.math_n(N, L, "MULTIPLY", zr, P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", sg, 0.8))))
    ny = P.math_n(N, L, "MULTIPLY", y, P.math_n(N, L, "ADD", 1.0, P.math_n(N, L, "MULTIPLY", sg, 0.55)))
    cb = N.new("ShaderNodeCombineXYZ"); L.new(x, cb.inputs[0]); L.new(ny, cb.inputs[1]); L.new(nz, cb.inputs[2])
    setp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], setp.inputs["Geometry"]); L.new(cb.outputs[0], setp.inputs["Position"])
    L.new(setp.outputs[0], go.inputs[0])
    _PN = ng
    return ng

def add_pinch(o, w, cx=0.0, z0=0.0):
    m = o.modifiers.new("pinch", "NODES"); m.node_group = pinch_group(); m.show_viewport = False
    ids = {it.name: it.identifier for it in pinch_group().interface.items_tree if getattr(it, "in_out", "") == "INPUT"}
    o["pid"] = ids["S"]
    P.set_mod(o, "pinch", ids["W"], w); P.set_mod(o, "pinch", ids["CX"], cx); P.set_mod(o, "pinch", ids["Z0"], z0)
def pinch_key(o, f, v): P.key_mod(o, "pinch", o["pid"], f, v)

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
    c = camera("cam_" + name, (0, 0, 0), *a, **k); CAMS[name] = c; return c

def shake(cam, f0, f1, amp, seed=1, decay=True):
    rnd = random.Random(seed); base = {}
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
def V(*a): return Vector(a)
def at(name, p, parent=None): return empty(name, tuple(p), parent)

# ======================================================================
# 1) MEHMONXONA (dunyo markazi; Megan divanda, -Y tomonga qaraydi)
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.93, 0.86, 0.76))
X0, X1, Y0, Y1, HZ_ = -2.6, 2.6, -4.0, 0.75, 2.7
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
R_(box("wall_L", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_F", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
# orqa devor (+Y): deraza teshigi x 0.9..2.1, z 0.9..2.2
WX0, WX1, WZ0, WZ1 = 0.9, 2.1, 0.9, 2.2
R_(box("wall_B1", (WX0 - X0, 0.1, HZ_), ((X0 + WX0) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
R_(box("wall_B2", (X1 - WX1, 0.1, HZ_), ((WX1 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
R_(box("wall_B3", (WX1 - WX0, 0.1, WZ0), ((WX0 + WX1) / 2, Y1 + 0.05, WZ0 / 2), wall_m))
R_(box("wall_B4", (WX1 - WX0, 0.1, HZ_ - WZ1), ((WX0 + WX1) / 2, Y1 + 0.05, (WZ1 + HZ_) / 2), wall_m))
trim_m = mat("trim", (0.93, 0.93, 0.9), 0.4)
WC = Vector(((WX0 + WX1) / 2, Y1 + 0.05, (WZ0 + WZ1) / 2))
for nm, sz, off in (("wf_t", (1.24, 0.14, 0.05), (0, 0, 0.65)), ("wf_b", (1.3, 0.2, 0.06), (0, -0.03, -0.65)),
                    ("wf_l", (0.05, 0.14, 1.3), (-0.6, 0, 0)), ("wf_r", (0.05, 0.14, 1.3), (0.6, 0, 0)),
                    ("wf_m", (0.04, 0.08, 1.3), (0, 0, 0))):
    R_(box(nm, sz, tuple(WC + Vector(off)), trim_m))
for x, y, l, a in ((0, Y1 - 0.015, X1 - X0, 0), (X0 + 0.015, (Y0 + Y1) / 2, Y1 - Y0, 90), (X1 - 0.015, (Y0 + Y1) / 2, Y1 - Y0, 90)):
    R_(box("baseboard", (l, 0.03, 0.1), (x, y, 0.05), trim_m, rot=(0, 0, a)))
# parda
cur_m = mat("curtain", (0.82, 0.78, 0.68), 0.9, sss=0.1)
for x in (WX0 - 0.2, WX1 + 0.2):
    c = R_(box("curtain", (0.4, 0.05, 2.4), (x, Y1 - 0.1, 1.3), cur_m))
    w_ = c.modifiers.new("wave", "WAVE"); w_.height = 0.03; w_.width = 0.12; w_.narrowness = 1; w_.use_y = False; w_.speed = 0
SOFA = Vector((0.0, 0.32, 0.0))
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", tuple(SOFA), 0, 1.15))
R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.85, -1.0, 0), 90, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-1.45, 0.4, 0), 20, 1.2))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.1, Y1 - 0.02, 1.5), 0, 1.0))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, -1.2, 0), -90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, -1.0, 1.03), -90, 1.0))
rug = R_(plane("rug", (2.6, 1.8), (-0.3, -0.8, 0.004), mat("rug", (0.5, 0.16, 0.12), 0.95)))
brass = mat("brass", (0.85, 0.65, 0.3), 0.25, metal=1.0)
R_(cyl("lamp_base", 0.14, 0.03, (1.25, 0.35, 0.015), brass))
R_(cyl("lamp_pole", 0.015, 1.5, (1.25, 0.35, 0.75), brass))
R_(cyl("lamp_shade", 0.22, 0.32, (1.25, 0.35, 1.55), mat("shade", (1.0, 0.86, 0.62), 0.6, emit=2.5)))
# stol ustida telefon va krujka
R_(box("phone", (0.075, 0.155, 0.009), (-0.72, -0.95, 0.395), mat("phone_m", (0.02, 0.02, 0.025), 0.15, coat=1.0), rot=(0, 0, 18), bevel=0.003))
R_(cyl("mug", 0.04, 0.1, (-1.0, -0.9, 0.44), mat("mug_m", (0.9, 0.9, 0.88), 0.3)))

# ======================================================================
# 2) MEGAN
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
for o in mmeshes:
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                n.inputs["Specular IOR Level"].default_value = 0.35
                if "hair" not in m.name.lower():
                    for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                    n.inputs["Roughness"].default_value = 0.5
                n.inputs["Coat Weight"].default_value = 0.0
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(act, start, n, speed=1.0, src=None, hold=False):
    s = mc.add_strip(meg, act, start, speed=speed, blend=0, hold=hold, src=src)
    s.blend_in = s.blend_out = 0; s.use_auto_blend = False
    if not hold:
        L_ = (s.action_frame_end - s.action_frame_start) * s.scale
        s.repeat = max(1.0, n / max(1.0, L_))
    return s

# --- asab va tomirlar: dam holatidagi (T-poza) suyak koordinatalari, armaturaga bog'lanadi ---
bpy.context.view_layer.update()
M0 = meg.matrix_parent_inverse @ meg.matrix_basis      # ildiz (0,0,0) dagi armatura matritsasi
def BH(b): return M0 @ meg.data.bones["mixamorig:" + b].head_local
def BT(b): return M0 @ meg.data.bones["mixamorig:" + b].tail_local
LEGB = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
        "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand"]
SEG = {b: (BH(b), BT(b)) for b in LEGB}
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab)))); return (a + ab * t - p).length
def skinned_tube(name, pts, radius, m, bones):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [(i, i + 1) for i in range(len(pts) - 1)], [])
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    groups = {b: o.vertex_groups.new(name="mixamorig:" + b) for b in bones}
    for i, p in enumerate(pts):
        ds = sorted((seg_dist(p, *SEG[b]), b) for b in bones)[:2]
        ws = [1.0 / (d + 0.004) ** 4 for d, _ in ds]; s_ = sum(ws)
        for (d, b), w in zip(ds, ws): groups[b].add([i], w / s_, "REPLACE")
    o.parent = meg; o.matrix_parent_inverse = M0.inverted()
    am = o.modifiers.new("arm", "ARMATURE"); am.object = meg
    gn = o.modifiers.new("tube", "NODES"); gn.node_group = mesh_tube_group(); gn.show_viewport = False
    rid = next(it.identifier for it in mesh_tube_group().interface.items_tree if getattr(it, "name", "") == "Radius")
    P.set_mod(o, "tube", rid, radius)
    mid = next(it.identifier for it in mesh_tube_group().interface.items_tree if getattr(it, "name", "") == "Material")
    P.set_mod(o, "tube", mid, m)
    me.materials.append(m)
    return o
def polyline(ctrl, step=0.025):
    out = [ctrl[0]]
    for a, b in zip(ctrl, ctrl[1:]):
        n = max(1, int((b - a).length / step))
        for k in range(1, n + 1): out.append(a.lerp(b, k / n))
    return out
def lens_of(pts):
    L_ = [0.0]
    for a, b in zip(pts, pts[1:]): L_.append(L_[-1] + (b - a).length)
    return L_
BACK = V(0, 0.035, 0)                                   # T-pozada orqa tomon = +Y
FRONT = V(0, -0.03, 0)
HEADC = BH("Head") + V(0, 0, 0.1)
NERVES = {}; NMATS = {}
def leg_nerve(side):
    sx = 1 if side == "Left" else -1
    ctrl = [BH(side + "ToeBase") + V(0, -0.02, 0.0), BH(side + "Foot") + V(0, 0.02, -0.05),
            BH(side + "Leg").lerp(BH(side + "Foot"), 0.5) + BACK, BH(side + "Leg") + BACK * 1.2 + V(sx * 0.02, 0, 0),
            BH(side + "UpLeg").lerp(BH(side + "Leg"), 0.5) + BACK * 1.3, BH(side + "UpLeg") + BACK * 1.2,
            BH("Hips") + V(sx * 0.03, 0.05, 0.02), BH("Spine") + V(0, 0.06, 0), BH("Spine1") + V(0, 0.07, 0),
            BH("Spine2") + V(0, 0.07, 0), BH("Neck") + V(0, 0.04, 0), HEADC]
    return polyline(ctrl)
def arm_nerve(side):
    ctrl = [BH(side + "Hand") + V(0, 0, -0.01), BH(side + "ForeArm") + V(0, 0, -0.02), BH(side + "Arm") + V(0, 0, -0.02),
            BH(side + "Shoulder") + V(0, 0.03, 0), BH("Spine2") + V(0, 0.07, 0.05), BH("Neck") + V(0, 0.04, 0), HEADC]
    return polyline(ctrl)
KNEE_U = {}
for side in ("Left", "Right"):
    pts = leg_nerve(side); Ls = lens_of(pts)
    m = nerve_mat(f"nerve_{side}"); NMATS[side] = m
    NERVES[side] = skinned_tube(f"nerve_{side}", pts, 0.0058, m, LEGB)
    kn = min(range(len(pts)), key=lambda i: (pts[i] - BH(side + "Leg")).length)
    KNEE_U[side] = Ls[kn] / Ls[-1]
    NERVES[side]["len"] = Ls[-1]
for side in ("LeftArm_", "RightArm_"):
    sd = side[:-4]
    m = nerve_mat(f"nerve_{side}"); NMATS[side] = m
    NERVES[side] = skinned_tube(f"nerve_{side}", polyline(arm_nerve(sd)), 0.0042, m, LEGB)
# mayda tarmoqlar (oyoqdagi tolalar)
rb = random.Random(5)
BR = []
for side in ("Left", "Right"):
    sx = 1 if side == "Left" else -1
    for i in range(7):
        t = rb.uniform(0.1, 0.9); seg = rb.choice(("UpLeg", "Leg"))
        a = BH(side + seg).lerp(BT(side + seg), t) + BACK
        d = V(sx * rb.uniform(0.02, 0.06), rb.uniform(-0.07, 0.0), rb.uniform(-0.08, -0.02))
        pts = polyline([a, a + d * 0.5 + V(0, 0, 0.01), a + d], 0.01)
        m = NMATS[side]
        BR.append(skinned_tube(f"branch_{side}{i}", pts, 0.0026, m, LEGB))
# qon tomirlari (oldingi tomonda): yurakdan oyoq uchiga, qon oqimi pastga
VMATS = []
VESSELS = []
for side in ("Left", "Right"):
    sx = 1 if side == "Left" else -1
    ctrl = [BH("Spine2") + V(sx * 0.03, -0.04, 0.05), BH("Spine") + V(sx * 0.02, -0.05, 0), BH("Hips") + V(sx * 0.05, -0.06, -0.03),
            BH(side + "UpLeg") + FRONT + V(-sx * 0.02, 0, -0.04), BH(side + "UpLeg").lerp(BH(side + "Leg"), 0.5) + FRONT + V(-sx * 0.025, 0, 0),
            BH(side + "Leg") + V(-sx * 0.02, 0.03, 0.0), BH(side + "Leg").lerp(BH(side + "Foot"), 0.5) + V(-sx * 0.015, 0.0, 0),
            BH(side + "Foot") + V(0, -0.02, 0.0), BH(side + "ToeBase") + V(0, 0, 0.01)]
    m = nerve_mat(f"vessel_{side}", col=(0.55, 0.02, 0.02), pcol=(1.0, 0.08, 0.04)); VMATS.append(m)
    VESSELS.append(skinned_tube(f"vessel_{side}", polyline(ctrl), 0.0062, m, LEGB))

# --- rentgen nusxalar ---
xbody = P.xray_material("xr_body", col=(0.35, 0.75, 1.0), strength=1.1, base=0.02)
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
for o in mmeshes: vis(o, ROOM + YARD, recursive=False)
for o in list(NERVES.values()) + BR: vis(o, XR, recursive=False)
for o in VESSELS: vis(o, rng("blood"), recursive=False)

# --- harakatlar va joylashuv ---
SIT = A_("Sitting_7.fbx", inplace=False)
STS = A_("Sit_To_Stand.fbx", inplace=False)
HURT = A_("Injured_Hurting_Idle.fbx", inplace=False)
STUM = A_("Injured_Stumble_Idle.fbx", inplace=False)
SHAKE = A_("Shaking_It_Off.fbx", inplace=False)
WALK = A_("Female_Walk.fbx", inplace=False)
SEATZ = float(os.environ.get("SEATZ", -0.05))
SIT_P = SOFA + V(0.18, -0.06, SEATZ)
STAND_P = SIT_P + V(0, -0.45, -SEATZ)
YD = V(-40, 0, 0)                                       # hovli
HOSE_C = YD + V(0, 0, 0.0)                              # krossovka tushadigan nuqta
def place(f, loc, rot=0.0):
    mroot.location = loc; mroot.rotation_euler = (0, 0, R(rot))
    for p_ in ("location", "rotation_euler"): mroot.keyframe_insert(p_, frame=f)
H0 = S["hose"][0]
# --- hovlidagi qadam: yurish (ildiz harakati bilan) F_STEP da oyoq shlangga tushadi.
# O'lchash ildiz (0,0,0) da, boshqa strip yo'q paytda qilinadi.
WALK_SPEED = 0.7
def foot_at(f, bone="RightFoot"):
    sc.frame_set(f); bpy.context.view_layer.update()
    return meg.matrix_world @ meg.pose.bones["mixamorig:" + bone].head
tmp = mc.add_strip(meg, WALK, 1, speed=WALK_SPEED, blend=0, hold=False)
W_AFS, W_SCALE = tmp.action_frame_start, tmp.scale
Lw = int((tmp.action_frame_end - tmp.action_frame_start) * tmp.scale)
zs = [(f, b, foot_at(f, b)) for f in range(1, Lw + 1) for b in ("LeftFoot", "RightFoot")]
cands = []
for b in ("LeftFoot", "RightFoot"):
    zmin = min(p.z for f, bb, p in zs if bb == b)
    cands += [(f, b, p) for f, bb, p in zs if bb == b and p.z < zmin + 0.006 and f >= 18]
fplant, bplant, pplant = min(cands, key=lambda c: c[0])
meg.animation_data.nla_tracks.remove(meg.animation_data.nla_tracks[-1])
W_START = F_STEP - (fplant - 1)
print("WALK plant", fplant, bplant, pplant, "Lw", Lw, "start", W_START)
place(1, tuple(SIT_P))
place(119, tuple(SIT_P)); place(132, tuple(SIT_P)); place(142, tuple(SIT_P + V(0, 0, -SEATZ)))
place(200, tuple(STAND_P))
place(S["blood"][0] - 1, tuple(STAND_P)); place(S["blood"][0], tuple(SIT_P))
place(S["path"][1], tuple(SIT_P))
HROOT = HOSE_C - V(pplant.x, pplant.y, 0)
place(H0, tuple(HROOT)); place(S["hose"][1], tuple(HROOT))
place(S["hose"][1] + 1, tuple(STAND_P))
place(S["chaos"][0] - 11, tuple(STAND_P)); place(END, tuple(STAND_P))
interp(mroot, "CONSTANT")
for fc in fcurves(mroot):
    for k in fc.keyframe_points:
        if 132 <= k.co.x < 142: k.interpolation = "LINEAR"
# NLA (pastdan tepaga, yuqoridagisi ustun)
s1 = strip(SIT, 1, 132)
s2 = strip(STS, 118, 60, speed=1.3, src=(1, 69), hold=True)
s3 = strip(HURT, 200, 70)
s5 = mc.add_strip(meg, WALK, W_START, speed=WALK_SPEED, blend=0, hold=True, src=(W_AFS, W_AFS + (fplant - 1) / W_SCALE))
s5.blend_in = s5.blend_out = 0; s5.use_auto_blend = False
s4 = strip(SIT, S["blood"][0], S["path"][1] - S["blood"][0])
s6 = strip(HURT, S["chaos"][0] - 10, 120)
s7 = strip(STUM, S["reboot"][0] - 6, 100)
s8 = strip(SHAKE, S["short"][0] - 22, 90, speed=1.15)
for s_ in (s1, s3, s4, s6, s7, s8): s_.extrapolation = "NOTHING"
for s_ in (s2, s5): s_.extrapolation = "HOLD_FORWARD"

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.07, 0.1), headE)
kneeL = child_of_bone("meg_kneeL", meg, "LeftLeg")
calfL = child_of_bone("meg_calfL", meg, "LeftLeg"); calfLo = empty("calfLo", (0, 0.2, 0), calfL)
footL = child_of_bone("meg_footL", meg, "LeftFoot")
spine2 = child_of_bone("meg_spine2", meg, "Spine2")
hipsE = child_of_bone("meg_hips", meg, "Hips")

# --- miya ---
def brain_mat2(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Roughness"].default_value = 0.4
    gl = value_node(m, "glow", 0.8); wh = value_node(m, "white", 0.0)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs[6].default_value = (0.78, 0.42, 0.45, 1); base.inputs[7].default_value = (0.92, 0.6, 0.6, 1)
    L.new(nz.outputs["Fac"], base.inputs["Factor"]); L.new(base.outputs[2], b.inputs["Base Color"])
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"; c3.inputs[6].default_value = (1.0, 0.55, 0.65, 1); c3.inputs[7].default_value = (1.0, 0.92, 0.55, 1)
    L.new(wh, c3.inputs["Factor"]); L.new(c3.outputs[2], b.inputs["Emission Color"])
    fl = P.math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", fl, 0.15), gl), b.inputs["Emission Strength"])
    return m
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
xb_m = brain_mat2("xbrain_m")
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, XR)

# --- qisilish halqasi (chap tizza orti) ---
pinch_m = mat("pinch_m", (1, 0.02, 0.0), emit=0.0, emit_col=(1.0, 0.03, 0.0))
# halqa dam holatida (T-poza) asab tizzadan o'tgan nuqtada yasalib, LeftLeg suyagiga bog'lanadi
RING_P = BH("LeftLeg") + BACK * 1.2 + V(0.02, 0, -0.02)
bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.0028, location=tuple(RING_P))
ring = bpy.context.object; ring.name = "pinch_ring"; ring.data.materials.append(pinch_m)
bpy.ops.object.transform_apply(location=True)
for p_ in ring.data.polygons: p_.use_smooth = True
vg_ = ring.vertex_groups.new(name="mixamorig:LeftLeg"); vg_.add(list(range(len(ring.data.vertices))), 1.0, "REPLACE")
bpy.context.view_layer.update()
ring.parent = meg; ring.matrix_parent_inverse = M0.inverted()
ring.modifiers.new("arm", "ARMATURE").object = meg
sc.frame_set(1); bpy.context.view_layer.update()
ps_ = pinch_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
def psk(f, v): ps_.default_value = v; ps_.keyframe_insert("default_value", frame=f)
PI0, PI1 = S["pinch"]
psk(1, 0.0); psk(PI0 + 10, 0.0); psk(PI0 + 14, 9.0); psk(PI0 + 20, 2.5)
for f in range(PI0 + 26, PI1, 10): psk(f, 6.0); psk(f + 5, 2.0)
psk(PI1 + 1, 2.0)
interp(pinch_m.node_tree, "LINEAR")
vis(ring, rng("numb", "pinch", "path"), recursive=False)
ring_l = point("ring_l", (0, 0, 0), 0.01, (1.0, 0.08, 0.02), lights_for(rng("pinch"), 0.6))


# --- asab impulslari (vaqt bo'yicha) ---
NU0, NU1 = S["numb"]; BL0, BL1 = S["blood"]; PA0, PA1 = S["path"]; CH0, CH1 = S["chaos"]; RB0, RB1 = S["reboot"]
ALLN = [NMATS[k] for k in NMATS]
for k, m in NMATS.items():
    leg = k in ("Left", "Right")
    val_key(m, "count", 1, 3.0); val_key(m, "amp", 1, 60.0 if leg else 30.0); val_key(m, "glow", 1, 3.0)
    val_key(m, "phase", 1, 0.0); val_key(m, "dead", 1, -1.0); val_key(m, "stop", 1, 2.0)
    # numb: chap oyoq tizzadan pastda o'chadi ("birdan")
    if k == "Left":
        val_key(m, "dead", F_NUMB - 1, -1.0); val_key(m, "dead", F_NUMB + 4, KNEE_U["Left"] + 0.02)
        val_key(m, "stop", 1, KNEE_U["Left"] + 0.02)          # impulslar tizzadan o'tmaydi
        val_key(m, "dead", NU1 + 1, KNEE_U["Left"] + 0.02)
    val_key(m, "phase", NU0, NU0 * 0.035); val_key(m, "phase", CH0 - 1, (CH0 - 1) * 0.035)
    # blood/pinch/path: oyoq tizzagacha o'lik, impuls qisilgan joyda to'xtaydi
    if k == "Left":
        val_key(m, "count", PA0 - 1, 3.0); val_key(m, "count", PA0, 2.0)
        val_key(m, "dead", PA0 - 1, KNEE_U["Left"] + 0.02)
        val_key(m, "stop", PA0 - 1, KNEE_U["Left"] + 0.02); val_key(m, "dead", PA0, -1.0); val_key(m, "stop", PA0, 2.0)
        val_key(m, "amp", PA0, 80.0); val_key(m, "glow", PA0, 3.5)
    # chaos: tartibsiz, kuchli
    rr = random.Random(sum(map(ord, k)))
    val_key(m, "count", CH0 - 1, 3.0 if leg else 2.0); val_key(m, "count", CH0, 7.0 if leg else 4.0)
    val_key(m, "amp", CH0, 120.0 if leg else 50.0); val_key(m, "glow", CH0, 4.0 if leg else 2.5)
    ph = (CH0 - 1) * 0.035
    for f in range(CH0, CH1 + 1, 3):
        ph += rr.uniform(0.05, 0.5); val_key(m, "phase", f, ph)
        val_key(m, "amp", f, (rr.choice((60.0, 150.0, 250.0)) if leg else rr.choice((30.0, 80.0))))
    # reboot: oyoqdan boshga ketma-ket yoqiladi (dead -> stop yuqoriga ko'tariladi)
    val_key(m, "count", RB0, 4.0); val_key(m, "amp", RB0, 120.0 if leg else 80.0); val_key(m, "glow", RB0, 0.05)
    val_key(m, "dead", RB0 - 1, -1.0)
    val_key(m, "stop", RB0, 0.0); val_key(m, "stop", RB0 + (50 if leg else 62), 1.05); val_key(m, "glow", RB0 + 40, 0.05)
    val_key(m, "glow", RB0 + (52 if leg else 64), 6.0); val_key(m, "glow", RB1, 3.5)
    val_key(m, "phase", RB0, ph + 0.1); val_key(m, "phase", RB1 + 1, ph + 0.1 + (RB1 + 1 - RB0) * 0.04)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR" if ('"phase"' in fc.data_path or ('"stop"' in fc.data_path and kp.co.x >= RB0)) else "CONSTANT"
        if '"dead"' in fc.data_path:
            for kp in fc.keyframe_points:
                if F_NUMB - 1 <= kp.co.x <= F_NUMB + 4: kp.interpolation = "LINEAR"
for m in VMATS:
    val_key(m, "count", 1, 5.0); val_key(m, "amp", 1, 60.0); val_key(m, "glow", 1, 2.5)
    val_key(m, "phase", BL0, 0.0); val_key(m, "phase", BL1 + 1, 3.0)
    keys_linear(m)
# miya: path da impuls yetganda, chaos da miltillaydi, reboot da yonadi
val_key(xb_m, "glow", 1, 0.8)
for f in range(CH0, CH1, 4): val_key(xb_m, "glow", f, random.choice((1.0, 4.0, 7.0))); val_key(xb_m, "white", f, random.choice((0.0, 0.6, 1.0)))
val_key(xb_m, "glow", CH1, 0.8); val_key(xb_m, "white", CH1, 0.0)
val_key(xb_m, "glow", RB0, 0.3); val_key(xb_m, "glow", RB0 + 60, 0.3); val_key(xb_m, "glow", RB0 + 64, 5.0); val_key(xb_m, "glow", RB1, 3.0)
val_key(xb_m, "white", RB0 + 63, 0.0); val_key(xb_m, "white", RB0 + 64, 1.0); val_key(xb_m, "white", RB1, 0.4)
interp(xb_m.node_tree, "CONSTANT")
# rentgen divan (o'tirgan kadrlarda)
xsofa_m = P.xray_material("xr_sofa", col=(0.3, 0.55, 0.85), strength=0.5, base=0.01)
bpy.context.view_layer.update()
sofa_grp = [o for o in bpy.data.objects if o.name.startswith("Sofa_01_grp")][0]
for o in sofa_grp.children_recursive:
    if o.type != "MESH": continue
    g = o.copy(); g.name = o.name + "_xr"; sc.collection.objects.link(g); g.parent = None
    g.matrix_world = o.matrix_world.copy()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xsofa_m
    vis(g, XR_SIT, recursive=False)

# ======================================================================
# 3) MAKRO: TERI KESIMI (ignalar, chumolilar, asab uchlari)
# ======================================================================
SK = V(40, 0, 0)
skin_root, skin_parts, (epi_m, der_m, fat_m) = P.build_section("skin", tuple(SK), size=(2.0, 1.4))
val_key(epi_m, "wet", 1, 0.15)
# asab uchlari: old kesim yuzasida (y=-0.7) teri ostida
end_m = nerve_mat("endings", col=(0.95, 0.75, 0.2), pcol=(1.0, 0.9, 0.5))
ends = []
re_ = random.Random(3)
for i in range(13):
    x = -0.95 + i * 0.155 + re_.uniform(-0.03, 0.03)
    pts = [SK + V(x, -0.703, 0.2), SK + V(x + re_.uniform(-0.05, 0.05), -0.703, 0.5), SK + V(x + re_.uniform(-0.08, 0.08), -0.703, 0.78),
           SK + V(x + re_.uniform(-0.1, 0.1), -0.703, 0.93)]
    t_ = P.tube(f"ending{i}", [tuple(p) for p in pts], 0.011, end_m, None, taper=[1.4, 1.0, 0.8, 0.5]); ends.append(t_)
    for j in range(2):
        a = pts[2] + V(0, 0, re_.uniform(-0.1, 0.05))
        b = a + V(re_.uniform(-0.12, 0.12), 0, re_.uniform(0.1, 0.17))
        ends.append(P.tube(f"ending{i}_{j}", [tuple(a), tuple(a.lerp(b, 0.5) + V(0.02, 0, 0)), tuple(b)], 0.006, end_m, None, taper=[1.0, 0.8, 0.5]))
# asosiy nerv: yog' qatlamida bo'ylab
ends.append(P.tube("ending_main", [tuple(SK + V(-1.05, -0.69, 0.22)), tuple(SK + V(0, -0.69, 0.2)), tuple(SK + V(1.05, -0.69, 0.23))], 0.03, end_m, None))
NE0, NE1 = S["needles"]; AN0, AN1 = S["ants"]
val_key(end_m, "count", 1, 2.0); val_key(end_m, "amp", 1, 0.0); val_key(end_m, "glow", 1, 0.4); val_key(end_m, "phase", 1, 0.0)
re2 = random.Random(8)
for a, b in ((NE0 + 8, NE1), (F_ANT_N, AN1)):
    for f in range(a, b + 1, 2):
        val_key(end_m, "amp", f, re2.choice((20.0, 45.0, 70.0))); val_key(end_m, "glow", f, re2.choice((0.8, 2.5, 4.0)))
        val_key(end_m, "phase", f, (f - a) * 0.09)
    val_key(end_m, "amp", b + 1, 0.0); val_key(end_m, "glow", b + 1, 0.4)
for f in range(AN0, F_ANT_N, 3):                       # chumolilar paytida mayin chaqnash
    val_key(end_m, "glow", f, re2.choice((0.5, 1.0, 1.6))); val_key(end_m, "amp", f, 10.0); val_key(end_m, "phase", f, (f - AN0) * 0.05)
keys_linear(end_m)
skin_grp = [skin_root] + ends
# ignalar
steel = mat("steel", (0.85, 0.86, 0.88), 0.12, metal=1.0)
needles = []
rn = random.Random(21)
def needle(i):
    g = empty(f"needle{i}")
    c = cyl(f"needle{i}_b", 0.0085, 1.3, (0, 0, 0.7), steel, parent=g, verts=10)
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.0085, radius2=0.0004, depth=0.07, location=(0, 0, 0.035))
    t_ = bpy.context.object; t_.name = f"needle{i}_t"; t_.data.materials.append(steel); t_.parent = g
    t_.rotation_euler = (R(180), 0, 0); t_.location = (0, 0, 0.035)
    for p_ in t_.data.polygons: p_.use_smooth = True
    return g
NN = int(os.environ.get("NEEDLES", 150))
for i in range(NN):
    g = needle(i)
    x, y = rn.uniform(-0.95, 0.95), rn.uniform(-0.62, 0.62)
    tilt = (rn.uniform(-14, 14), rn.uniform(-14, 14), rn.uniform(0, 360))
    g.rotation_euler = [R(a) for a in tilt]
    base = SK + V(x, y, 1.0)
    up = (g.rotation_euler.to_matrix() @ V(0, 0, 1))
    depth = rn.uniform(0.12, 0.3)
    waves = [NE0 + int((x + 1) / 2 * 30) + rn.randint(0, 10), F_ANT_N + int((y + 0.7) / 1.4 * 18) + rn.randint(0, 12)]
    key(g, 1, loc=tuple(base + up * 2.5))
    for w0 in waves:
        key(g, w0 - 3, loc=tuple(base + up * 2.5)); key(g, w0, loc=tuple(base - up * depth))
        key(g, w0 + 5, loc=tuple(base - up * depth)); key(g, w0 + 9, loc=tuple(base + up * 2.5))
    interp(g, "LINEAR", "location")
    needles.append(g)
# chumolilar
ant_m = mat("ant_m", (0.03, 0.012, 0.006), 0.25, coat=0.7)
ANTS = []
ra = random.Random(33)
def make_ant(i, s=2.2):
    g = empty(f"ant{i}")
    sphere(f"ant{i}_gaster", 0.04, (0, -0.07, 0.03), ant_m, scale=(0.85, 1.35, 0.85), sub=3, parent=g)
    sphere(f"ant{i}_pet", 0.012, (0, -0.025, 0.03), ant_m, sub=2, parent=g)
    sphere(f"ant{i}_thx", 0.02, (0, 0.005, 0.034), ant_m, scale=(0.8, 1.7, 0.85), sub=3, parent=g)
    sphere(f"ant{i}_head", 0.022, (0, 0.05, 0.036), ant_m, scale=(1.0, 1.1, 0.9), sub=3, parent=g)
    legs = []
    for j, ly in enumerate((-0.01, 0.006, 0.022)):
        for sx in (-1, 1):
            pv = empty(f"ant{i}_lp{j}{sx}", (sx * 0.012, ly, 0.03), g)
            l1 = cyl(f"ant{i}_l{j}{sx}", 0.0032, 0.065, (sx * 0.03, 0, -0.008), ant_m, rot=(0, 90 - sx * 35 + 90, 0), parent=pv, verts=6)
            l1.rotation_euler = (0, R(sx * 62), R(sx * (j - 1) * 30))
            legs.append((pv, j, sx))
    for sx in (-1, 1):
        cyl(f"ant{i}_an{sx}", 0.002, 0.06, (sx * 0.012, 0.085, 0.06), ant_m, rot=(-55, 0, -sx * 25), parent=g, verts=6)
    g.scale = (s, s, s)
    return g, legs
for i in range(int(os.environ.get("ANTS", 24))):
    g, legs = make_ant(i, ra.uniform(1.4, 1.8))
    x0, y0 = ra.uniform(-1.1, 0.9), ra.uniform(-0.75, 0.6)
    hd = ra.uniform(0, 360); spd = ra.uniform(0.018, 0.03); wob = ra.uniform(2, 5); ph = ra.uniform(0, 6)
    x, y = x0, y0
    for f in range(AN0 - 2, AN1 + 2, 2):
        hd += math.sin(f / wob + ph) * 14
        x += -math.sin(R(hd)) * spd * 2; y += math.cos(R(hd)) * spd * 2
        if abs(x) > 1.0: hd = 360 - hd; x = max(-1.0, min(1.0, x))
        if abs(y) > 0.68: hd = 180 - hd; y = max(-0.68, min(0.68, y))
        key(g, f, loc=tuple(SK + V(x, y, 1.0)), rot=(0, 0, hd))
    for pv, j, sx in legs:
        for f in range(AN0 - 2, AN1 + 2, 2):
            ph_ = ((f // 2) + j + (0 if sx > 0 else 1)) % 2
            key(pv, f, rot=(0, 0, 18 if ph_ else -18))
    ANTS.append(g)
for g in ANTS: vis(g, rng("ants"))
for g in needles: vis(g, SKIN)
for o in skin_grp: vis(o, SKIN)
# makro studiya fon
studio_m = mat("studio", (0.035, 0.04, 0.06), 0.6)
st_floor = plane("skin_floor", (14, 14), tuple(SK + V(0, 0, -0.02)), studio_m); vis(st_floor, SKIN)

# ======================================================================
# 4) MAKRO: ASAB KABELI (qisilish, uyg'onish)
# ======================================================================
CB = V(80, 0, 0)
cab = empty("cable", tuple(CB))
fib_ms = []
fibers = []
NF = 0
rf = random.Random(4)
rings = [(0, 0)] + [(0.13 * math.cos(R(a)), 0.13 * math.sin(R(a))) for a in range(0, 360, 60)] + \
        [(0.25 * math.cos(R(a + 15)), 0.25 * math.sin(R(a + 15))) for a in range(0, 360, 30)]
for i, (yy, zz) in enumerate(rings):
    pts = []
    for k in range(9):
        x = -2.4 + k * 0.6
        pts.append((x, yy + rf.uniform(-0.012, 0.012), zz + rf.uniform(-0.012, 0.012)))
    m = nerve_mat(f"fiber{i}", col=(0.95, 0.78, 0.25), pcol=(0.7, 0.85, 1.0), dead_col=(0.35, 0.33, 0.3)); fib_ms.append(m)
    t_ = P.tube(f"fiber{i}", pts, 0.055, m, cab, res=8, taper=[1.0] * len(pts))
    add_pinch(t_, 0.45); fibers.append(t_)
sheath_m = bpy.data.materials.new("sheath"); sheath_m.use_nodes = True
N = sheath_m.node_tree.nodes; L = sheath_m.node_tree.links; N.remove(N["Principled BSDF"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.85, 0.55, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 2.0), 0.7), em.inputs["Strength"])
trn = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 2.0), 0.55), 0.04), mx.inputs[0])
L.new(trn.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
sheath = P.tube("sheath", [(-2.6, 0, 0), (0, 0, 0), (2.6, 0, 0)], 0.36, sheath_m, cab, res=8)
add_pinch(sheath, 0.45)
# bosuvchi suyak (tepadan) va o'rindiq (pastdan)
bone_m = mat("bone_m", (0.86, 0.8, 0.66), 0.45, sss=0.2)
press = empty("press", tuple(CB + V(0, 0, 0.95)))
pb = sphere("press_bone", 1.0, (0, 0, 0.0), bone_m, scale=(0.55, 0.9, 0.55), sub=4, parent=press)
bpy.ops.object.select_all(action="DESELECT")
mus_m = mat("muscle", (0.55, 0.1, 0.1), 0.45, sss=0.4)
under = box("cable_under", (6, 2.2, 0.6), tuple(CB + V(0, 0, -0.68)), mus_m, bevel=0.15)
SQ0, SQ1 = S["squeeze"]; RL0, RL1 = S["release"]; WK0, WK1 = S["wake"]
# bosim: SQ boshida tushadi, RL da ko'tariladi
SQZ = [(1, 0.0), (SQ0, 0.55), (SQ0 + 10, 1.0), (RL0 + 8, 1.0), (RL0 + 30, 0.0)]
for o in fibers + [sheath]:
    for f, v in SQZ: pinch_key(o, f, v)
for f, v in SQZ: key(press, f, loc=tuple(CB + V(0, 0, 0.95 - 0.33 * v + (0.9 if f >= RL0 + 30 else 0))))
key(press, RL0 + 50, loc=tuple(CB + V(0, 0, 2.6)))
interp(press, "LINEAR")
for i, m in enumerate(fib_ms):
    val_key(m, "count", 1, 4.0); val_key(m, "amp", 1, 30.0); val_key(m, "glow", 1, 0.5); val_key(m, "dead", 1, -1.0)
    val_key(m, "stop", 1, 0.47); val_key(m, "phase", 1, i * 0.07)
    val_key(m, "phase", SQ1 + 1, i * 0.07 + 2.2)
    # release: uxlab yotgan (kulrang), impulssiz
    val_key(m, "amp", RL0, 0.0); val_key(m, "glow", RL0, 0.12); val_key(m, "dead", RL0, 2.0); val_key(m, "stop", RL0, 2.0)
    # wake: "birdaniga" hamma tola yonadi, impulslar tartibsiz
    val_key(m, "dead", F_WAKE - 1, 2.0); val_key(m, "dead", F_WAKE, -1.0)
    val_key(m, "glow", F_WAKE - 1, 0.12); val_key(m, "glow", F_WAKE, 9.0); val_key(m, "glow", F_WAKE + 6, 2.0)
    val_key(m, "count", F_WAKE, 6.0); val_key(m, "amp", F_WAKE, 60.0)
    ph = 0.0; rr = random.Random(i)
    val_key(m, "phase", F_WAKE, ph)
    for f in range(F_WAKE + 2, WK1 + 2, 2):
        ph += rr.uniform(0.04, 0.35); val_key(m, "phase", f, ph); val_key(m, "glow", f, rr.choice((1.0, 2.5, 4.0)))
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR" if ('"phase"' in fc.data_path or False) else "CONSTANT"
# qisilgan joyda qizil chaqnash (impuls urilganda)
hit_m = mat("hit_m", (1, 0.05, 0.02), emit=0.0, emit_col=(1.0, 0.1, 0.02))
hit = sphere("hit_glow", 0.12, (0, 0, 0), hit_m, scale=(0.6, 1.6, 0.4), sub=3, parent=cab); hit.location = (-0.12, 0, 0)
hs = hit_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f in range(1, SQ0): pass
hs.default_value = 0; hs.keyframe_insert("default_value", frame=1)
for f in range(SQ0 + 6, SQ1, 7):
    hs.default_value = 0.4; hs.keyframe_insert("default_value", frame=f - 1)
    hs.default_value = 6.0; hs.keyframe_insert("default_value", frame=f)
    hs.default_value = 0.4; hs.keyframe_insert("default_value", frame=f + 3)
hs.default_value = 0.0; hs.keyframe_insert("default_value", frame=SQ1 + 1)
vis(hit, rng("squeeze"), recursive=False)
# uchqunlar (wake): kabel atrofida elektr yoylari
arc_m = mat("arc", (0.6, 0.85, 1.0), emit=14.0, emit_col=(0.6, 0.85, 1.0))
def arc_curve(name, a, b, n=10, jit=0.06, rnd=random, parent=None, r=0.008):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); sp.points.add(n - 1)
    for k in range(n):
        t = k / (n - 1); p = a.lerp(b, t)
        if 0 < k < n - 1: p = p + V(rnd.uniform(-jit, jit), rnd.uniform(-jit, jit), rnd.uniform(-jit, jit))
        sp.points[k].co = (*p, 1.0)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(arc_m)
    if parent: o.parent = parent
    return o
rk = random.Random(77)
arcs_c = []
for i in range(14):
    x = rk.uniform(-2.0, 2.0); a0 = rk.uniform(0, 6.28)
    a = CB + V(x, 0.37 * math.cos(a0), 0.37 * math.sin(a0))
    b = a + V(rk.uniform(-0.3, 0.3), 0.3 * math.cos(a0), 0.3 * math.sin(a0))
    o = arc_curve(f"carc{i}", a, b, 8, 0.05, rk)
    fs = sorted(rk.sample(range(F_WAKE, WK1), 7))
    vis(o, [(f, f + 1) for f in fs], recursive=False); arcs_c.append(o)
cable_objs = [cab, press, under]
for o in cable_objs: vis(o, CABLE)
cab_floor = plane("cable_floor", (20, 20), tuple(CB + V(0, 0, -1.0)), studio_m); vis(cab_floor, CABLE)

# ======================================================================
# 5) HOVLI: SUV SHLANGI
# ======================================================================
grass_m = pbr("grass", "aerial_grass_rock", 0.6, tint=(0.55, 0.9, 0.45))
yg = plane("yard_ground", (60, 60), tuple(YD), grass_m)
hose_m = mat("hose_m", (0.08, 0.45, 0.12), 0.35, coat=0.6)
hose_pts = [(-3.0, 1.4, 0.035), (-1.6, 0.6, 0.035), (-0.6, 0.06, 0.035), (0.0, 0.0, 0.035), (0.3, 0.01, 0.035),
            (0.5, 0.04, 0.04), (0.62, 0.08, 0.05)]
hose_grp = empty("hose_grp", tuple(YD + V(0, 0, 0)))
hose = P.tube("hose", hose_pts, 0.032, hose_m, hose_grp, res=10)
add_pinch(hose, 0.07, cx=0.0, z0=0.0)
nozzle = cyl("nozzle", 0.04, 0.16, tuple(YD + V(0.68, 0.16, 0.08)), mat("nozzle_m", (0.9, 0.55, 0.05), 0.3), rot=(-60, 0, -20))
water_m = P.water_material("water_jet", tint=(0.8, 0.92, 1.0), rough=0.05)
# suv oqimi: parabola
JD = V(0.35, 0.94, 0.0).normalized()
nz0 = YD + V(0.71, 0.24, 0.13)
def jet_pt(t, v0=3.4):
    return nz0 + JD * (v0 * 0.6 * t) + V(0, 0, v0 * 0.75 * t - 4.9 * t * t)
jet = P.tube("jet", [tuple(jet_pt(t)) for t in [i * 0.06 for i in range(10)]], 0.022, water_m, None, res=10, taper=[1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 1.9, 2.1, 2.3, 2.5])
HS0, HS1 = S["hose"]
P.tube_r(jet, 1, 0.022); P.tube_r(jet, F_STEP + 1, 0.022); P.tube_r(jet, F_STEP + 6, 0.0)
for fc in fcurves(jet):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
drops = []
rd = random.Random(9)
for i in range(46):
    d = P.droplet(f"jdrop{i}", (0, 0, 0), rd.uniform(0.008, 0.02), None, water_m, squash=1.0)
    t0 = rd.uniform(0, 0.6); jit = V(rd.uniform(-0.05, 0.05), rd.uniform(-0.05, 0.05), rd.uniform(-0.04, 0.04))
    born = HS0 - 30 + int(rd.uniform(0, 1) * (F_STEP + 4 - (HS0 - 30)))
    for f in range(HS0 - 1, HS1 + 2):
        age = ((f - born) / 24.0 + t0) % 0.62 if f <= F_STEP + 4 else ((F_STEP + 4 - born) / 24.0 + t0) % 0.62 + (f - F_STEP - 4) / 24.0
        p_ = jet_pt(age) + jit * age * 2
        if p_.z < YD.z: p_.z = YD.z - 0.2
        key(d, f, loc=tuple(p_))
    interp(d, "CONSTANT")
    drops.append(d)
# shlang qisilishi: krossovka tushgan kadrda
pinch_key(hose, 1, 0.0); pinch_key(hose, F_STEP - 1, 0.0); pinch_key(hose, F_STEP + 2, 1.0)
yard_objs = [yg, hose_grp, nozzle, jet] + drops
for o in yard_objs: vis(o, YARD)
# maysa tutamlari (oldingi plan)
tuft_m = mat("tuft", (0.12, 0.32, 0.06), 0.6, sss=0.1)
rt = random.Random(12)
tufts = []
for i in range(130):
    x, y = rt.uniform(-1.0, 1.6), rt.uniform(-0.9, 1.6)
    if abs(y - 0.0) < 0.12 and -0.6 < x < 0.8: continue
    if abs(x - 0.3) < 0.35 and -1.2 < y < -0.3: continue
    for k in range(5):
        h = rt.uniform(0.05, 0.12)
        o = cyl(f"blade{i}_{k}", 0.004, h, tuple(YD + V(x + rt.uniform(-0.02, 0.02), y + rt.uniform(-0.02, 0.02), h / 2)), tuft_m,
                rot=(rt.uniform(-25, 25), rt.uniform(-25, 25), 0), verts=4)
        tufts.append(o)
tuftg = empty("tufts")
for o in tufts: o.parent = tuftg
vis(tuftg, YARD)

# ======================================================================
# 6) QISQA TUTASHUV: boldir atrofida uchqunlar (xonada)
# ======================================================================
SH0, SH1 = S["short"]
sparks = []
rs_ = random.Random(55)
for i in range(16):
    a0 = rs_.uniform(0, 6.28); z0 = rs_.uniform(-0.05, 0.38)
    a = V(0.07 * math.cos(a0), z0, 0.07 * math.sin(a0))
    b = a + V(0.12 * math.cos(a0 + rs_.uniform(-0.6, 0.6)), rs_.uniform(-0.06, 0.06), 0.12 * math.sin(a0 + rs_.uniform(-0.6, 0.6)))
    o = arc_curve(f"spark{i}", a, b, 7, 0.02, rs_, parent=calfL, r=0.0025)
    fs = sorted(rs_.sample(range(F_SHORT - 4, SH1), 9))
    vis(o, [(f, f + 1) for f in fs], recursive=False); sparks.append(o)
for o in sparks:
    for fc in fcurves(o):
        pass

for o in room_objs: vis(o, ROOM)

# ======================================================================
# 7) KAMERALAR
# ======================================================================
sc.frame_set(60); bpy.context.view_layer.update()
def W(o): bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
KNEE_SIT = W(kneeL); FACE_SIT = W(faceT); HIPS_SIT = W(hipsE); FOOT_SIT = W(footL)
print("SIT knee", KNEE_SIT, "face", FACE_SIT, "hips", HIPS_SIT, "foot", FOOT_SIT)
sc.frame_set(S["pain"][0] + 25); bpy.context.view_layer.update(); FACE_PAIN = W(faceT); KNEE_PAIN = W(kneeL)
sc.frame_set(CH0 + 30); bpy.context.view_layer.update(); FACE_CH = W(faceT); KNEE_CH = W(kneeL); HIPS_CH = W(hipsE); FOOT_CH = W(footL)
sc.frame_set(SH0 + 15); bpy.context.view_layer.update(); CALF_SH = W(calfLo); HIPS_SH = W(hipsE)
sc.frame_set(F_STEP); bpy.context.view_layer.update(); FOOT_STEP = foot_at(F_STEP)
print("pain face", FACE_PAIN, "chaos face", FACE_CH, "step foot", FOOT_STEP, "hose C", HOSE_C)

# 1 ILGAK: poldan chalishgan tizzaga tez push-in
f0, f1 = S["hook"]
hkT = at("hookT", KNEE_SIT + V(0, 0, 0.05))
c = shot_cam("hook", hkT, 14, 2.4, focus=hkT)
path_keys(c, [(f0, KNEE_SIT + V(0.95, -2.3, -0.42)), (f0 + 20, KNEE_SIT + V(0.6, -1.5, -0.36)), (f1, KNEE_SIT + V(0.32, -0.62, -0.18))])
lens_keys(c, [(f0, 14), (f1, 22)])
# 2 hissiz: rentgen, chap oyoq atrofida aylanma
f0, f1 = S["numb"]
nmT = at("numbT", KNEE_SIT.lerp(FOOT_SIT, 0.35))
c = shot_cam("numb", nmT, 30, 2.8, focus=nmT)
orbit(c, f0, f1, nmT.location, 0.95, 0.75, -40, 10, nmT.location.z + 0.25, nmT.location.z + 0.15)
shake(c, F_NUMB, F_NUMB + 10, 0.01, seed=3)
# 3 turish: past burchak, keng
f0, f1 = S["stand"]
stT = empty("standT"); cl = stT.constraints.new("COPY_LOCATION"); cl.target = spine2
c = shot_cam("stand", stT, 16, 4.0, focus=stT)
path_keys(c, [(f0, SIT_P + V(0.95, -1.75, 0.16)), (f1, SIT_P + V(0.7, -1.45, 0.2))])
# 4 ignalar: makro, crash zoom
f0, f1 = S["needles"]
nT = at("needT", SK + V(0.0, -0.3, 0.95))
c = shot_cam("needles", nT, 22, 5.6, focus=nT)
path_keys(c, [(f0, SK + V(1.6, -3.4, 2.6)), (f0 + 8, SK + V(1.0, -2.5, 2.0)), (f0 + 12, SK + V(0.55, -1.7, 1.6)), (f1, SK + V(0.3, -1.45, 1.5))])
lens_keys(c, [(f0, 22), (f0 + 8, 24), (f0 + 12, 32), (f1, 34)])
shake(c, f0 + 12, f1, 0.02, seed=4, decay=False)
# 5 og'riq: yuzga yaqin, qizil chaqnash
f0, f1 = S["pain"]
pfT = empty("painT"); cl = pfT.constraints.new("COPY_LOCATION"); cl.target = faceT
c = shot_cam("pain", pfT, 30, 2.0, focus=pfT)
path_keys(c, [(f0, FACE_PAIN + V(-0.55, -0.85, -0.2)), (f0 + 6, FACE_PAIN + V(-0.42, -0.62, -0.2)), (f1, FACE_PAIN + V(-0.36, -0.5, -0.22))])
lens_keys(c, [(f0, 26), (f0 + 6, 34), (f1, 38)])
shake(c, f0 + 4, f1, 0.012, seed=5, decay=False)
# 6 qon: rentgen oyoq bo'ylab yonlama slayd (oyoqdan sondan)
f0, f1 = S["blood"]
blT = empty("bloodT"); path_keys(blT, [(f0, FOOT_SIT + V(0, 0, 0.1)), (f1, HIPS_SIT.lerp(KNEE_SIT, 0.4))])
c = shot_cam("blood", blT, 26, 3.2, focus=blT)
path_keys(c, [(f0, FOOT_SIT + V(-0.9, -0.55, 0.35)), (f1, HIPS_SIT.lerp(KNEE_SIT, 0.4) + V(-0.95, -0.6, 0.45))])
# 7 qisilish: halqaga crash zoom
f0, f1 = S["pinch"]
sc.frame_set(PI0 + 10); bpy.context.view_layer.update()
_dg = bpy.context.evaluated_depsgraph_get(); _re = ring.evaluated_get(_dg)
rpos = _re.matrix_world @ (sum((v.co for v in _re.data.vertices), Vector()) / len(_re.data.vertices))
print("RING", rpos)
rT = at("pinchT", rpos); ring_l.location = rpos
c = shot_cam("pinch", rT, 30, 2.8, focus=rT)
path_keys(c, [(f0, rpos + V(1.2, -0.9, 0.5)), (f0 + 10, rpos + V(0.9, -0.7, 0.38)), (f0 + 14, rpos + V(0.38, -0.3, 0.17)), (f1, rpos + V(0.32, -0.26, 0.16))])
lens_keys(c, [(f0, 26), (f0 + 10, 28), (f0 + 14, 40), (f1, 44)])
shake(c, f0 + 13, f0 + 26, 0.01, seed=7)
# 8 yo'l: oyoqdan boshga kran
f0, f1 = S["path"]
ptT = empty("pathT"); path_keys(ptT, [(f0, FOOT_SIT.lerp(KNEE_SIT, 0.3)), (f0 + 30, KNEE_SIT), (f0 + 70, HIPS_SIT + V(0, 0.05, 0.2)), (f1, FACE_SIT + V(0, 0.08, 0.1))])
c = shot_cam("path", ptT, 24, 4.0, focus=ptT)
path_keys(c, [(f0, FOOT_SIT + V(0.95, -0.75, 0.25)), (f0 + 30, KNEE_SIT + V(1.05, -0.7, 0.2)), (f0 + 70, HIPS_SIT + V(1.1, -0.75, 0.45)), (f1, FACE_SIT + V(0.8, -0.65, 0.3))])
# 9 shlang: maysa sathidan
f0, f1 = S["hose"]
hT = at("hoseT", HOSE_C + V(0.18, 0.1, 0.28))
c = shot_cam("hose", hT, 16, 4.0, focus=at("hoseF", HOSE_C + V(0.05, 0, 0.06)))
path_keys(c, [(f0, HOSE_C + V(0.3, -1.3, 0.1)), (f1, HOSE_C + V(0.24, -1.0, 0.12))])
lens_keys(c, [(f0, 16), (F_STEP, 17), (F_STEP + 3, 21), (f1, 22)])
shake(c, F_STEP, F_STEP + 10, 0.012, seed=9)
# 10 ezilish: kabel 3/4
f0, f1 = S["squeeze"]
sqT = at("sqT", CB + V(-0.15, 0, 0.1))
c = shot_cam("squeeze", sqT, 24, 4.0, focus=sqT)
path_keys(c, [(f0, CB + V(-2.4, -3.0, 1.4)), (f1, CB + V(-1.6, -2.2, 1.0))])
# 11 bosim ko'tariladi: yonlama slayd
f0, f1 = S["release"]
rlT = empty("rlT"); path_keys(rlT, [(f0, CB + V(-0.6, 0, 0.2)), (f1, CB + V(0.6, 0, 0.0))])
c = shot_cam("release", rlT, 22, 4.0, focus=rlT)
path_keys(c, [(f0, CB + V(-1.4, -3.0, 0.5)), (f1, CB + V(1.2, -2.8, 0.7))])
# 12 uyg'onish: crash zoom + silkinish
f0, f1 = S["wake"]
wkT = at("wkT", CB + V(0.2, 0, 0))
c = shot_cam("wake", wkT, 20, 4.0, focus=wkT)
path_keys(c, [(f0, CB + V(2.2, -3.2, 1.6)), (F_WAKE - 1, CB + V(1.9, -2.8, 1.4)), (F_WAKE + 3, CB + V(1.0, -1.5, 0.75)), (f1, CB + V(0.85, -1.3, 0.65))])
lens_keys(c, [(f0, 20), (F_WAKE - 1, 21), (F_WAKE + 3, 30), (f1, 32)])
shake(c, F_WAKE, f1, 0.03, seed=12, decay=False)
# 13 tartibsiz impulslar: tik turgan rentgen, oyoqdan boshga tez kran
f0, f1 = S["chaos"]
chT = empty("chaosT"); path_keys(chT, [(f0, KNEE_CH), (f0 + 35, HIPS_CH + V(0, 0, 0.2)), (f1, FACE_CH)])
c = shot_cam("chaos", chT, 22, 3.2, focus=chT)
path_keys(c, [(f0, KNEE_CH + V(0.7, -1.0, -0.2)), (f0 + 35, HIPS_CH + V(0.8, -1.1, 0.1)), (f1, FACE_CH + V(0.45, -0.75, 0.15))])
lens_keys(c, [(f0, 22), (f1 - 30, 24), (f1, 32)])
shake(c, f0, f1, 0.006, seed=13, decay=False)
# 14 chumolilar: makro, past va yonlama
f0, f1 = S["ants"]
anT = empty("antsT"); path_keys(anT, [(f0, SK + V(-0.4, -0.1, 1.0)), (F_ANT_N, SK + V(0.1, 0.0, 1.0)), (f1, SK + V(0.2, -0.2, 0.95))])
c = shot_cam("ants", anT, 26, 5.6, focus=anT)
path_keys(c, [(f0, SK + V(-1.6, -1.5, 1.45)), (F_ANT_N, SK + V(-0.7, -1.4, 1.5)), (F_ANT_N + 6, SK + V(0.6, -2.4, 2.1)), (f1, SK + V(0.8, -2.2, 1.95))])
lens_keys(c, [(f0, 26), (F_ANT_N, 30), (F_ANT_N + 6, 24), (f1, 26)])
shake(c, F_ANT_N + 4, f1, 0.015, seed=14, decay=False)
# 15 qayta ishga tushish: butun tana atrofida aylanma
f0, f1 = S["reboot"]
rbT = empty("rebootT"); path_keys(rbT, [(f0, KNEE_CH + V(0, 0, -0.15)), (f0 + 55, HIPS_CH + V(0, 0, 0.25)), (f1, FACE_CH + V(0, 0, -0.1))])
c = shot_cam("reboot", rbT, 20, 4.0, focus=rbT)
orbit(c, f0, f1, V(HIPS_CH.x, HIPS_CH.y, 0), 1.6, 1.25, 30, 110, 0.55, 1.45)
# 16 qisqa tutashuv: boldirga past burchak
f0, f1 = S["short"]
shT = empty("shortT"); cl = shT.constraints.new("COPY_LOCATION"); cl.target = calfLo
c = shot_cam("short", shT, 18, 2.8, focus=shT)
path_keys(c, [(f0, CALF_SH + V(-0.6, -0.95, -0.15)), (F_SHORT, CALF_SH + V(-0.5, -0.8, -0.12)), (F_SHORT + 3, CALF_SH + V(-0.35, -0.55, -0.08)), (f1, CALF_SH + V(-0.45, -0.75, 0.1))])
lens_keys(c, [(f0, 18), (F_SHORT, 20), (F_SHORT + 3, 26), (f1, 22)])
shake(c, F_SHORT, F_SHORT + 16, 0.02, seed=16)
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
# 8) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_h = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_h.inputs[0])
bg_d = N.new("ShaderNodeBackground"); bg_d.inputs[0].default_value = (0.004, 0.008, 0.022, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_h.outputs[0], a1.inputs[0]); L.new(bg_d.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    h, d = (1.0, 0.0) if n in ("hook", "stand", "pain", "short") else ((1.2, 0.0) if n == "hose" else (0.0, 1.0))
    bg_h.inputs[1].default_value = h; bg_h.inputs[1].keyframe_insert("default_value", frame=f)
    bg_d.inputs[1].default_value = d; bg_d.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2); sun.data.color = (1.0, 0.93, 0.82); sun.rotation_euler = (R(50), 0, R(160))
for f, n in SHOTS:
    sun.data.energy = 3.0 if n in ("hook", "stand", "pain", "short", "hose") else 0.0
    sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
RM = ROOM
area("win_key", (1.5, 1.6, 1.7), 1.6, (0.95, 0.97, 1.0), lights_for(RM, 220.0), target=at("wkT2", (0.2, 0.0, 0.8)))
area("ceil", (0.2, -0.8, 2.6), 1.6, (1.0, 0.9, 0.78), lights_for(RM, 90.0), target=at("ceT", (0.2, -0.6, 0.0)))
area("face_fill", (-0.9, -1.6, 1.5), 0.9, (1.0, 0.82, 0.68), lights_for(RM, 50.0), target=at("ffT", (0.2, 0.0, 0.9)))
point("lamp_glow", (1.25, 0.35, 1.5), 0.15, (1.0, 0.75, 0.45), lights_for(RM, 25.0))
red = area("pain_red", (0.9, -0.8, 1.8), 0.6, (1.0, 0.06, 0.03), [(1, 0)], target=faceT)
PN0, PN1 = S["pain"]
for f in range(PN0, PN1 + 1, 6):
    red.data.energy = 120 if (f - PN0) // 6 % 2 else 25; red.data.keyframe_insert("energy", frame=f)
red.data.energy = 0; red.data.keyframe_insert("energy", frame=PN1 + 1)
spk = point("spark_l", (0, 0, 0), 0.02, (0.55, 0.8, 1.0), [(1, 0)])
cl = spk.constraints.new("COPY_LOCATION"); cl.target = calfLo
rq = random.Random(4)
for f in range(F_SHORT - 4, SH1 + 1, 2): spk.data.energy = rq.choice((0, 5, 25, 60)); spk.data.keyframe_insert("energy", frame=f)
# rentgen
XRall = XR
area("X_rim", (-1.2, 1.4, 2.2), 1.0, (0.3, 0.6, 1.0), lights_for(XRall, 40.0), target=hipsE)
area("X_fill", (1.4, -1.6, 1.2), 1.0, (0.4, 0.5, 1.0), lights_for(XRall, 10.0), target=hipsE)
# makro teri
area("SK_key", tuple(SK + V(-1.8, -2.2, 3.0)), 1.6, (1.0, 0.9, 0.82), lights_for(SKIN, 450.0), target=at("skT", SK + V(0, 0, 0.8)))
area("SK_rim", tuple(SK + V(2.0, 2.2, 2.0)), 1.4, (0.45, 0.65, 1.0), lights_for(SKIN, 380.0), target=at("skT2", SK + V(0, 0, 0.8)))
area("SK_front", tuple(SK + V(0.3, -3.0, 0.6)), 1.2, (1.0, 0.85, 0.75), lights_for(SKIN, 120.0), target=at("skT3", SK + V(0, -0.7, 0.5)))
# makro kabel
area("CB_key", tuple(CB + V(-1.5, -2.5, 2.8)), 1.8, (1.0, 0.9, 0.85), lights_for(CABLE, 90.0), target=cab)
area("CB_rim", tuple(CB + V(1.8, 2.4, 1.6)), 1.6, (0.4, 0.6, 1.0), lights_for(CABLE, 180.0), target=cab)
cbl = point("cb_flash", tuple(CB + V(0, -0.8, 0.6)), 0.3, (0.6, 0.85, 1.0), [(1, 0), (F_WAKE, 400.0), (F_WAKE + 6, 60.0), (WK1 + 1, 0.0)], const=False)
for f in range(F_WAKE + 8, WK1, 4): cbl.data.energy = random.choice((30.0, 80.0, 160.0)); cbl.data.keyframe_insert("energy", frame=f)
hl = point("hit_l", tuple(CB + V(-0.1, -0.5, 0.2)), 0.1, (1.0, 0.1, 0.03), lights_for(rng("squeeze"), 20.0))

# ======================================================================
# 9) RENDER
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
