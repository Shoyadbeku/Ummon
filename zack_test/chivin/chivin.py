# Chivin chaqishi — Zack D. Films uslubida 36 s video (18 ta kesish).
# Asos: zack_test/ebbi/ebbi.py (yordamchilar) + mixchar.py; procedural modellar: mosquito.py, ../ebbi/eye.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=12 /tmp/claude-0/bvenv/bin/python -I zack_test/chivin/chivin.py --render
# Sinov: FRAMES=10,30,170,300,440,690 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "ebbi")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Quaternion, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import eye as E
import mosquito as M
sc = bpy.context.scene
sc.render.fps = 24
END = 871
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (Whisper so'z vaqtlariga bog'langan) ----------------
SHOTS = [(1, "hook"), (22, "room_in"), (43, "pierce"), (87, "xs_six"), (137, "bend"), (200, "stylets"),
         (264, "saw"), (334, "hold"), (407, "search"), (472, "enter"), (514, "saliva"), (573, "vessel"),
         (619, "face"), (648, "fill"), (716, "room_out"), (769, "welt"), (797, "immune"), (831, "scratch")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
KIND = {"hook": "macro", "room_in": "room", "pierce": "macro", "xs_six": "xsec", "bend": "macro", "stylets": "macro",
        "saw": "xsec", "hold": "xsec", "search": "xsec", "enter": "xsec", "saliva": "xsec", "vessel": "xsec",
        "face": "room", "fill": "macro", "room_out": "room", "welt": "macro", "immune": "xsec", "scratch": "room"}
def kind_ranges(k): return [S[n] for n, _ in [(n, 0) for _, n in SHOTS] if KIND[n] == k]

# ---------------- yordamchilar (ebbi.py dan) ----------------
empty = E.empty
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

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
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
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
    r = img("rough.jpg", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def box(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
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

def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.0005):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 300
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c

def shake(cam, f0, f1, amp, seed=1):
    """kameraning hozirgi harakatiga silkinish qo'shadi (delta_location)"""
    rnd = random.Random(seed)
    for f in range(f0, f1 + 1):
        k = amp * (1 - (f - f0) / max(1, f1 - f0)) ** 2
        cam.delta_location = (rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k))
        cam.keyframe_insert("delta_location", frame=f)
    cam.delta_location = (0, 0, 0); cam.keyframe_insert("delta_location", frame=f1 + 1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None, kind="AREA"):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); sc.collection.objects.link(l)
    if kind == "AREA": l.data.size = size
    else: l.data.shadow_soft_size = size
    l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None: l.constraints.new("TRACK_TO").target = target
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def hold_end(o, f):
    """kesish oldidan: keyingi kadrga o'tishda motion blur chizig'i qolmasin"""
    for fc in fcurves(o):
        fc.keyframe_points.insert(f + 0.6, fc.evaluate(f))

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

MACRO = kind_ranges("macro"); XSEC = kind_ranges("xsec"); ROOM = kind_ranges("room")

# ======================================================================
# 1) MAKRO: bilak terisi va chivin (dunyo markazi)
# ======================================================================
skin, skin_red = M.skin_patch("skin", arm_r=0.06)
mq = M.build_mosquito("mq", 1.0); mq["curv"] = 0.06
Q_MACRO = Euler((0, 0, R(-90))).to_quaternion()            # chivin boshi +X ga (qo'lga ko'ndalang)
mq["root"].rotation_mode = "QUATERNION"; mq["root"].rotation_quaternion = Q_MACRO

# chuqurlik (h) va stiletlar yoyilishi (spread) jadvali: (kadr, h, spread)
HTAB = [(1, 0.0, 0), (21, 0.00012, 0), (43, 0.00012, 0), (86, 0.00055, 0), (137, 0.00055, 0), (199, 0.00112, 0),
        (200, 0.00112, 0), (228, 0.00112, 1), (263, 0.00112, 1), (264, 0.00112, 0), (871, 0.00112, 0)]
def h_at(f):
    for (f0, h0, _), (f1, h1, _) in zip(HTAB, HTAB[1:]):
        if f0 <= f <= f1: return h0 + (h1 - h0) * ease((f - f0) / max(1, f1 - f0))
    return HTAB[-1][1]
def chord(h): return M.LP - h / abs(M.D0.z)
def contact_local(h): return M.H0 + M.D0 * chord(h)
for f, h, sp in HTAB:
    M.pose(mq, f, h, spread=sp)
    mq["root"].location = -(Q_MACRO @ contact_local(h)); mq["root"].keyframe_insert("location", frame=f)
# qorin qonga to'ladi (fill kadri), keyin to'la qoladi
M.set_fill(mq, 1, 0.0); M.set_fill(mq, S["fill"][0] + 6, 0.0); M.set_fill(mq, S["fill"][1] - 6, 1.0)
# qorin nafas oladi (pompalaydi)
for f in range(S["fill"][0], S["fill"][1] + 1, 3):
    mq["abd_piv"].rotation_euler = (R(6 + 2.5 * math.sin(f * 0.9)), 0, 0); mq["abd_piv"].keyframe_insert("rotation_euler", frame=f)
vis(mq["root"], rng("hook", "pierce", "bend", "stylets", "fill"))
# qichishgan do'mboq
M.welt_key(skin, 1, 0.0); M.welt_key(skin, S["welt"][0], 0.05); M.welt_key(skin, S["welt"][0] + 16, 1.0)
E.key_value(skin_red, 1, 0.0); E.key_value(skin_red, S["welt"][0], 0.15); E.key_value(skin_red, S["welt"][0] + 18, 1.0)
bite = empty("bite", (0, 0, 0))

# ======================================================================
# 2) TERI KESIMI (x = 10). Sxema masshtabi: 1 sm ~ 0.2 mm
# ======================================================================
X0 = Vector((10.0, 0.0, 0.0))
xroot = empty("xsec", tuple(X0))
def xm(name, fn):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    fn(m, N, L, b, tc); return m
def _epi(m, N, L, b, tc):
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    wv = E._node(N, "ShaderNodeTexWave", **{"Scale": 60.0, "Distortion": 3.0, "Detail": 3.0}); wv.bands_direction = "Z"
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.72, 0.52, 0.42, 1); cr.color_ramp.elements[1].color = (0.88, 0.7, 0.58, 1)
    basal = E._math(N, L, "LESS_THAN", sep.outputs["Z"], -0.0033)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(basal, mx.inputs["Factor"]); L.new(cr.outputs[0], mx.inputs[6])
    mx.inputs[7].default_value = (0.42, 0.24, 0.18, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.45; b.inputs["Subsurface Weight"].default_value = 0.3
    b.inputs["Subsurface Scale"].default_value = 0.001
def _derm(m, N, L, b, tc):
    wv = E._node(N, "ShaderNodeTexWave", **{"Scale": 90.0, "Distortion": 14.0, "Detail": 6.0, "Detail Scale": 2.0})
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.5, 0.13, 0.15, 1); cr.color_ramp.elements[1].color = (0.86, 0.48, 0.47, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.4; b.inputs["Subsurface Weight"].default_value = 0.4
    b.inputs["Subsurface Radius"].default_value = (1, 0.3, 0.25); b.inputs["Subsurface Scale"].default_value = 0.002
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.inputs["Distance"].default_value = 0.0004
    L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
def _fat(m, N, L, b, tc):
    vo = E._node(N, "ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 260.0; vo.feature = "DISTANCE_TO_EDGE"
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(vo.outputs["Distance"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.55, 0.22, 0.12, 1); cr.color_ramp.elements[1].position = 0.08
    cr.color_ramp.elements[1].color = (0.95, 0.72, 0.3, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.25
    b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.002
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.0006
    L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
M_epi, M_derm, M_fat = xm("epidermis", _epi), xm("dermis", _derm), xm("fat", _fat)
XW, XD = 0.24, 0.07                                   # eni (x), chuqurligi (y: 0 = kesim yuzasi)
VZ, VR_IN, VR_OUT = -0.02, 0.0045, 0.0056             # qon tomiri
box("x_epi", (XW, XD, 0.004), (0, XD / 2, -0.002), M_epi, parent=xroot)
derm = box("x_derm", (XW, XD, 0.026), (0, XD / 2, -0.017), M_derm, parent=xroot)
box("x_fat", (XW, XD, 0.03), (0, XD / 2, -0.045), M_fat, parent=xroot)
# epidermis usti: makro teri materiali (g'ovaklar)
xtop = plane("x_top", (XW, XD), (0, XD / 2, 0.00002), skin.data.materials[0], parent=xroot)
cutter = cyl("x_cutter", VR_OUT, XW * 1.2, (0, 0, VZ), M_derm, rot=(0, 90, 0), parent=xroot, verts=64)
cutter.hide_render = True; cutter.hide_viewport = True
bm_ = derm.modifiers.new("vessel_hole", "BOOLEAN"); bm_.operation = "DIFFERENCE"; bm_.object = cutter; bm_.solver = "EXACT"

def half_tube(name, r_in, r_out, length, a0, a1, m_out, m_in, segs=48, nx=40):
    """X o'qi bo'ylab quvur bo'lagi; burchak a: y = r cos a, z = r sin a"""
    vs, fs, mi = [], [], []
    def ring(r):
        base = len(vs)
        for i in range(nx + 1):
            x = -length / 2 + length * i / nx
            for j in range(segs + 1):
                a = a0 + (a1 - a0) * j / segs
                vs.append((x, r * math.cos(a), r * math.sin(a)))
        return base
    bo, bi = ring(r_out), ring(r_in)
    W = segs + 1
    for i in range(nx):
        for j in range(segs):
            p = i * W + j
            fs.append((bo + p, bo + p + W, bo + p + W + 1, bo + p + 1)); mi.append(0)
            fs.append((bi + p, bi + p + 1, bi + p + W + 1, bi + p + W)); mi.append(1)
    for i in range(nx):                                      # kesilgan qirralar
        for j in (0, segs):
            p = i * W + j
            fs.append((bo + p, bi + p, bi + p + W, bo + p + W)); mi.append(0)
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(m_out); o.data.materials.append(m_in)
    for p, k in zip(o.data.polygons, mi): p.material_index = k; p.use_smooth = True
    return o
M_vwall = mat("vessel_wall", (0.5, 0.04, 0.05), 0.35)
b_ = M_vwall.node_tree.nodes["Principled BSDF"]; b_.inputs["Subsurface Weight"].default_value = 0.6
b_.inputs["Subsurface Radius"].default_value = (1, 0.2, 0.15); b_.inputs["Subsurface Scale"].default_value = 0.002
M_lumen = mat("vessel_lumen", (0.25, 0.01, 0.015), 0.12, emit=0.0)
b_ = M_lumen.node_tree.nodes["Principled BSDF"]; b_.inputs["Coat Weight"].default_value = 0.8
b_.inputs["Emission Color"].default_value = (0.5, 0.02, 0.02, 1); b_.inputs["Emission Strength"].default_value = 0.15
v_back = half_tube("vessel_back", VR_IN, VR_OUT, XW, R(-90), R(90), M_vwall, M_lumen); v_back.parent = xroot; v_back.location = (0, 0, VZ)
v_front = half_tube("vessel_front", VR_IN, VR_OUT, XW, R(90), R(270), M_vwall, M_lumen); v_front.parent = xroot; v_front.location = (0, 0, VZ)
vis(v_front, rng("vessel"))

# eritrotsitlar: oqim +X tomonga
M_rbc = mat("rbc", (0.6, 0.015, 0.02), 0.25)
b_ = M_rbc.node_tree.nodes["Principled BSDF"]; b_.inputs["Subsurface Weight"].default_value = 0.7
b_.inputs["Subsurface Radius"].default_value = (1, 0.15, 0.1); b_.inputs["Subsurface Scale"].default_value = 0.0008
b_.inputs["Coat Weight"].default_value = 0.6
rbc0 = M.rbc_mesh("rbc_proto", 0.0016); rbc0.data.materials.append(M_rbc); rbc0.hide_render = True; rbc0.hide_viewport = True
VFLOW = 0.00055                                       # m / kadr
XRANGES = [S[n] for _, n in SHOTS if KIND[n] == "xsec"]
rnd = random.Random(11)
rbcs = []
for i in range(110):
    front = i >= 70
    o = bpy.data.objects.new(f"rbc{i}", rbc0.data); sc.collection.objects.link(o); o.parent = xroot
    a = rnd.uniform(R(95), R(265)) if front else rnd.uniform(R(-80), R(80)); rr = rnd.uniform(0.0021, VR_IN - 0.0011)
    y, z = rr * math.cos(a), VZ + rr * math.sin(a)
    if not front: y = max(y, 0.0009)
    x0 = rnd.uniform(-XW / 2, XW / 2); rot0 = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
    spin = (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 0)
    for a_, b2 in XRANGES:
        for f, interp_mode in ((a_, "LINEAR"), (b2 + 1, "CONSTANT")):
            x = (x0 + VFLOW * f + XW / 2) % XW - XW / 2
            if f == b2 + 1: x = ((x0 + VFLOW * a_ + XW / 2) % XW - XW / 2) + VFLOW * (b2 + 1 - a_)
            o.location = (x, y, z + 0.0004 * math.sin(f * 0.1 + i)); o.keyframe_insert("location", frame=f)
            o.rotation_euler = (rot0[0] + spin[0] * f, rot0[1] + spin[1] * f, rot0[2]); o.keyframe_insert("rotation_euler", frame=f)
    for fc in fcurves(o):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR" if any(int(k.co[0]) == a_ for a_, _ in XRANGES) else "CONSTANT"
    if front: vis(o, rng("vessel"))
    rbcs.append(o)

# --- 6 ta stilet (sxema) ---
SX = 12.0                                              # kesimdagi chivin masshtabi
mqx = M.build_mosquito("mqx", SX)
Q_X = (Vector((0, 0, -1)).rotation_difference(Vector((0, 0, -1)))) @ Euler((0, 0, R(-90))).to_quaternion()
d_w = Q_X @ M.D0
Q_X = d_w.rotation_difference(Vector((0, 0, -1))) @ Q_X       # tumshuq vertikal pastga
mqx["root"].rotation_mode = "QUATERNION"; mqx["root"].rotation_quaternion = Q_X
for s in mqx["stylets"]: s.hide_render = True
XKEYS = sorted({1, 87, 110, 136, 137, 199, 264, 572, 797})
for f in XKEYS:
    h = h_at(f)
    M.pose(mqx, f, h)
    mqx["root"].location = tuple(X0 - SX * (Q_X @ contact_local(h))); mqx["root"].keyframe_insert("location", frame=f)
vis(mqx["root"], rng("xs_six", "saw", "hold", "search", "enter", "saliva"))

def ztop(f): return SX * chord(h_at(f)) * 0.96
M_sty = M.pmat("xs_stylet", (0.45, 0.22, 0.07), 0.2, 1.0, **{"Subsurface Weight": 0.4, "Subsurface Radius": (1.0, 0.5, 0.2),
                                                             "Subsurface Scale": 0.0006})
HL = {}
def stylet_mat(name, col):
    m = M.pmat(name, col, 0.22, 1.0, **{"Subsurface Weight": 0.35, "Subsurface Radius": (1.0, 0.6, 0.3), "Subsurface Scale": 0.0006})
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (1.0, 0.75, 0.3, 1)
    HL[name] = b; return m
def hl(name, pairs):
    b = HL[name]
    for f, v in pairs: b.inputs["Emission Strength"].default_value = v; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
def scurve(name, r, m, n=3, kind="POLY"):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 4
    cu.use_fill_caps = True; cu.resolution_u = 10; cu.materials.append(m)
    sp = cu.splines.new(kind); sp.points.add(n - 1)
    if kind == "NURBS": sp.order_u = 4; sp.use_endpoint_u = True
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.parent = xroot
    return o
def set_pts(o, f, pts, radii=None):
    sp = o.data.splines[0]
    for i, (p, q) in enumerate(zip(sp.points, pts)):
        p.co = (q[0], q[1], q[2], 1); p.keyframe_insert("co", frame=f)
        if radii: p.radius = radii[i]

YS = -0.0013                                           # stiletlar kesim yuzasi oldida
m_max, m_man = stylet_mat("maxilla", (0.45, 0.22, 0.07)), stylet_mat("mandible", (0.4, 0.2, 0.07))
m_lab, m_hyp = stylet_mat("labrum", (0.5, 0.25, 0.08)), stylet_mat("hypopharynx", (0.42, 0.24, 0.1))
maxl = [scurve(f"maxilla{s}", 0.00048, m_max) for s in (-1, 1)]
mand = [scurve(f"mandible{s}", 0.0005, m_man) for s in (-1, 1)]
labr = scurve("labrum", 0.0008, m_lab, 12, "NURBS")
hypo = scurve("hypopharynx", 0.00036, m_hyp, 12, "NURBS")
for o in maxl + mand + [labr, hypo]:
    o.data.splines[0].points[-1].radius = 0.45
# arra tishlari (maxilla uchida)
teeth = []
M_tooth = m_max
for s in (-1, 1):
    tp = empty(f"teeth{s}", (0, 0, 0), xroot)
    for k in range(7):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.00028, radius2=0.0, depth=0.0009,
                                        location=(s * 0.00055, 0, 0.0005 + k * 0.00062), rotation=(0, R(s * 120), 0))
        t = bpy.context.object; t.parent = tp; t.data.materials.append(M_tooth)
    teeth.append(tp)
# yara (mandibulalar ochib turgan kesik)
M_wound = mat("wound", (0.18, 0.005, 0.01), 0.1)
me = bpy.data.meshes.new("wound"); me.from_pydata([(-1, 0, 0), (1, 0, 0), (0, 0, -1)], [], [(0, 1, 2)]); me.update()
wound = bpy.data.objects.new("wound", me); sc.collection.objects.link(wound); wound.parent = xroot
wound.data.materials.append(M_wound); wound.location = (0, YS + 0.0006, 0.0001)

def dep(f, a, b, d0, d1):
    return d0 + (d1 - d0) * ease((f - a) / max(1, b - a))
XS_FRAMES = [f for a, b in rng("xs_six", "saw", "hold", "search", "enter", "saliva") for f in range(a, b + 1)]
TIP_SEARCH = None
def labrum_tip(f):
    if f <= S["xs_six"][1]: return Vector((-0.0002, YS, -dep(f, *S["xs_six"], 0.0, 0.0055)))
    if f <= S["hold"][1]: return Vector((-0.0002, YS, -dep(f, S["saw"][0], S["hold"][1], 0.0055, 0.0095)))
    if f <= S["search"][1]:
        t = (f - S["search"][0]) / (S["search"][1] - S["search"][0])
        return Vector((-0.0002 + 0.0065 * math.sin(t * 2 * math.pi * 1.25) * math.sin(t * math.pi) ** 0.5,
                       YS, -0.0095 - 0.0035 * t - 0.0012 * math.sin(t * 9)))
    t = ease((f - S["enter"][0]) / 20.0)
    a = labrum_tip(S["search"][1]); b = Vector((0.0035, 0.0012, VZ + 0.0016))
    return a.lerp(b, t)
for f in XS_FRAMES:
    top = Vector((0.0, YS, ztop(f)))
    # mandibulalar va maxillalar
    d_all = dep(f, *S["xs_six"], 0.0, 0.0055)
    if f >= S["saw"][0]:
        dmx = dep(f, *S["saw"], 0.0055, 0.0105); dmn = dep(f, *S["saw"], 0.0055, 0.0075)
    else:
        dmx = dmn = d_all
    osc = 0.0013 * math.sin(2 * math.pi * (f - S["saw"][0]) / 7.0) if S["saw"][0] <= f <= S["hold"][1] else 0.0
    if f > S["saw"][1]: osc *= 0.35
    spread = ease((f - S["hold"][0]) / 26.0) if f >= S["hold"][0] else 0.0
    for s, o in zip((-1, 1), maxl):
        tip = Vector((s * 0.0016, YS, -(dmx + s * osc)))
        set_pts(o, f, [top, Vector((s * 0.0016, YS, 0.003)), tip])
        tp = teeth[(s + 1) // 2]; tp.location = tip; tp.keyframe_insert("location", frame=f)
    for s, o in zip((-1, 1), mand):
        xt = s * (0.0029 + 0.0042 * spread)
        set_pts(o, f, [top, Vector((s * 0.0029, YS, 0.003)), Vector((xt, YS, -dmn))])
    wound.scale = (0.0012 + 0.0045 * spread + 0.0004 * (d_all > 0.001), 1, max(0.0005, dmn * 0.95))
    wound.keyframe_insert("scale", frame=f)
    # labrum (egiluvchan) + gipofarinks
    tip = labrum_tip(f); p2 = Vector((-0.0002, YS, min(-0.003, tip.z + 0.004))) if tip.z < -0.006 else None
    pts = []
    for i in range(12):
        u = i / 11
        if p2 is None:
            q = top.lerp(Vector((-0.0002, YS, 0.003)), min(1, u * 3)) if u < 0.34 else Vector((-0.0002, YS, 0.003)).lerp(tip, (u - 0.34) / 0.66)
        else:
            if u < 0.34: q = top.lerp(Vector((-0.0002, YS, 0.003)), u / 0.34)
            else:
                t = (u - 0.34) / 0.66; c0 = Vector((-0.0002, YS, 0.003))
                q = c0 * (1 - t) ** 2 + p2 * 2 * t * (1 - t) + tip * t * t
        pts.append(q)
    set_pts(labr, f, pts)
    inj = ease((f - S["saliva"][0]) / 10.0) if f >= S["saliva"][0] else 0.0
    hp = [q + Vector((0.0009, 0, 0.0)) for q in pts]
    hp[-1] = hp[-1] + Vector((0.0, 0.0, 0.0008)) + Vector((0.0007, 0.0004, -0.0016)) * inj
    hp[-2] = hp[-2] + Vector((0.0, 0.0, 0.0004))
    set_pts(hypo, f, hp)
for o in maxl + mand + [labr, hypo, wound] + teeth:
    vis(o, rng("xs_six", "saw", "hold", "search", "enter", "saliva"))
vis(wound, [(S["xs_six"][0] + 20, S["saliva"][1])])
# hikoyadagi stiletni yoritib ko'rsatish
for nm in HL: hl(nm, [(1, 0.0)])
hl("maxilla", [(S["saw"][0], 0.6), (S["saw"][1] + 1, 0.0)])
hl("mandible", [(S["hold"][0], 0.6), (S["hold"][1] + 1, 0.0)])
hl("labrum", [(S["search"][0], 0.5), (S["enter"][1] + 1, 0.0)])
hl("hypopharynx", [(S["saliva"][0], 0.8), (S["saliva"][1] + 1, 0.0)])

# --- so'lak (yashil, yonuvchi) ---
M_sal = mat("saliva", (0.25, 1.0, 0.35), 0.2, emit=4.0)
b_ = M_sal.node_tree.nodes["Principled BSDF"]; b_.inputs["Transmission Weight"].default_value = 0.5
sal = []
rnd = random.Random(3)
SA0, SA1 = S["saliva"]; VS0, VS1 = S["vessel"]
for i in range(46):
    o = sphere(f"saliva{i}", 1.0, (0, 0, 0), M_sal, sub=2, parent=xroot)
    born = SA0 + 6 + i * 1.1
    dirv = Vector((rnd.uniform(0.2, 1.0), rnd.uniform(-0.6, 0.6), rnd.uniform(-1.0, 0.2))).normalized()
    size = rnd.uniform(0.00035, 0.0009)
    src = Vector((0.0035 + 0.0016, 0.0016, VZ + 0.0008))
    for f in list(range(SA0, VS1 + 2, 2)):
        age = max(0.0, f - born)
        p = src + dirv * min(0.0036, 0.00028 * age) + Vector((VFLOW * 0.08 * age, 0, 0))
        r_ = math.hypot(p.y, p.z - VZ)
        if r_ > VR_IN - 0.0006:
            k = (VR_IN - 0.0006) / r_; p = Vector((p.x, p.y * k, VZ + (p.z - VZ) * k))
        p.y = max(p.y, 0.0007)
        s_ = 0.0 if f < born else size * min(1.0, age / 5.0) * (1 + 0.6 * min(1, age / 40))
        key(o, f, loc=tuple(p), scale=(s_, s_, s_))
    vis(o, rng("saliva", "vessel"))
    sal.append(o)

# --- immun javob (immune kadri): so'lak qoldiqlari, oq hujayralar, gistamin ---
IM0, IM1 = S["immune"]
M_wbc = mat("wbc", (0.85, 0.85, 0.8), 0.45)
b_ = M_wbc.node_tree.nodes["Principled BSDF"]; b_.inputs["Subsurface Weight"].default_value = 0.8
b_.inputs["Subsurface Scale"].default_value = 0.001; b_.inputs["Subsurface Radius"].default_value = (1, 0.9, 0.8)
N_ = M_wbc.node_tree.nodes; L_ = M_wbc.node_tree.links
nzw = E._node(N_, "ShaderNodeTexNoise", **{"Scale": 1500.0, "Detail": 4.0}); bpw = N_.new("ShaderNodeBump")
bpw.inputs["Strength"].default_value = 0.8; bpw.inputs["Distance"].default_value = 0.0002
L_.new(nzw.outputs["Fac"], bpw.inputs["Height"]); L_.new(bpw.outputs[0], b_.inputs["Normal"])
M_hist = mat("histamine", (1.0, 0.75, 0.15), 0.3, emit=5.0)
rnd = random.Random(21)
blobs = []
for i in range(22):
    p = Vector((rnd.uniform(-0.009, 0.009), YS * 0.5, rnd.uniform(-0.016, -0.005)))
    o = sphere(f"sal_rem{i}", 1.0, tuple(p), M_sal, sub=2, parent=xroot)
    s0 = rnd.uniform(0.0005, 0.0011)
    key(o, IM0, scale=(s0,) * 3); key(o, IM0 + 18 + rnd.randint(0, 10), scale=(s0,) * 3); key(o, IM1 + 1, scale=(s0 * 0.25,) * 3)
    vis(o, rng("immune")); blobs.append(p)
for i in range(11):
    tgt = blobs[i * 2]
    a = rnd.uniform(0, 2 * math.pi)
    st = tgt + Vector((0.016 * math.cos(a), 0, 0.01 * math.sin(a) - 0.004))
    o = sphere(f"wbc{i}", 0.0018, tuple(st), M_wbc, sub=3, parent=xroot)
    o.scale = (1.0, 0.6, 0.9)
    key(o, IM0, loc=tuple(st)); key(o, IM0 + 16, loc=tuple(tgt + (st - tgt) * 0.25)); key(o, IM1 + 1, loc=tuple(tgt + (st - tgt) * 0.12))
    vis(o, rng("immune"))
    for k in range(6):                                  # gistamin donachalari
        g = sphere(f"hist{i}_{k}", 1.0, (0, 0, 0), M_hist, sub=1, parent=xroot)
        c0 = tgt + (st - tgt) * 0.25; dv = Vector((rnd.uniform(-1, 1), 0, rnd.uniform(-1, 1))).normalized() * rnd.uniform(0.002, 0.005)
        key(g, IM0, loc=tuple(c0), scale=(0, 0, 0)); key(g, IM0 + 15, loc=tuple(c0), scale=(0, 0, 0))
        key(g, IM0 + 18, loc=tuple(c0 + dv * 0.3), scale=(0.00045,) * 3); key(g, IM1 + 1, loc=tuple(c0 + dv), scale=(0.0003,) * 3)
        vis(g, rng("immune"))
# do'mboq: teri yuzasi ko'tariladi
welt_x = sphere("x_welt", 1.0, (0, XD / 2, 0.0), M_epi, sub=4, parent=xroot)
key(welt_x, 1, scale=(0.02, XD / 2 * 0.98, 0.0)); key(welt_x, IM0, scale=(0.02, XD / 2 * 0.98, 0.0005))
key(welt_x, IM1 + 1, scale=(0.026, XD / 2 * 0.98, 0.0042))
vis(welt_x, rng("immune"))

# ======================================================================
# 3) MEHMONXONA (x = 100): divan, stol, gul, rasm, chiroq, Megan
# ======================================================================
RM = Vector((100.0, 0.0, 0.0))
rroot = empty("room", tuple(RM))
M_floor = pbr("floor", "laminate_floor_02", 0.5)
M_wall = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.93, 0.86, 0.76))
plane("floor", (8, 8), (0, 0, 0), M_floor, parent=rroot)
plane("wall_back", (8, 3.2), (0, 0.62, 1.6), M_wall, rot=(90, 0, 0), parent=rroot)
plane("wall_left", (8, 3.2), (-2.3, 0, 1.6), M_wall, rot=(90, 0, 90), parent=rroot)
plane("ceiling", (8, 8), (0, 0, 2.75), mat("ceil", (0.85, 0.83, 0.8), 0.8), parent=rroot)
def place(nm, loc, rotz=0.0, s=1.0):
    p = empty(nm + "_piv", loc, rroot); p.rotation_euler = (0, 0, R(rotz)); p.scale = (s, s, s)
    import_gltf(f"{PH}{nm}/{nm}.gltf", p); return p
place("Sofa_01", (0, 0.2, 0))
place("modern_coffee_table_01", (-0.6, -0.85, 0), 90)
place("potted_plant_01", (-1.25, 0.25, 0))
place("fancy_picture_frame_01", (0.0, 0.6, 1.45), 0, 1.4)
# torsher (procedural)
M_metal = mat("lamp_metal", (0.05, 0.05, 0.05), 0.3, metal=1.0)
cyl("lamp_base", 0.14, 0.02, (1.15, 0.3, 0.01), M_metal, parent=rroot)
cyl("lamp_pole", 0.012, 1.5, (1.15, 0.3, 0.76), M_metal, parent=rroot)
M_shade = mat("lamp_shade", (1.0, 0.85, 0.6), 0.6, emit=2.0)
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.24, radius2=0.15, depth=0.3, location=(1.15, 0.3, 1.55), end_fill_type="NOTHING")
sh = bpy.context.object; sh.parent = rroot; sh.data.materials.append(M_shade)
for p in sh.data.polygons: p.use_smooth = True

# Megan
megan_root, megan, megan_meshes = mc.load_character("Megan", "Megan.fbx")
megan_root.parent = rroot; megan_root.location = (0.0, 0.08, -0.07)
A = lambda n: mc.load_action(n)
mc.add_strip(megan, A("Sitting_Idle_5.fbx"), 1, blend=0, repeat=6.0)
mc.add_strip(megan, A("Sitting_Idle_3.fbx"), S["face"][0] - 10, blend=8, repeat=2.0)
mc.add_strip(megan, A("Sitting_Idle_5.fbx"), S["room_out"][0] - 20, blend=8, repeat=2.0)
mc.add_strip(megan, A("Sitting_Rubbing_Arm.fbx"), S["scratch"][0] - 62, blend=8, repeat=1.0)
def bone_empty(name, bone, loc=(0, 0, 0)):
    e = empty(name, loc)
    c = e.constraints.new("CHILD_OF"); c.target = megan; c.subtarget = bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    return e
for o in megan_meshes:
    for ms in o.material_slots:
        if not ms.material or not ms.material.node_tree: continue
        for nd in ms.material.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                body = "Body" in o.name
                nd.inputs["Roughness"].default_value = 0.5 if body else 0.75
                for lk in list(nd.inputs["Roughness"].links): ms.material.node_tree.links.remove(lk)
                nd.inputs["Specular IOR Level"].default_value = 0.4 if body else 0.25
                if body:
                    nd.inputs["Subsurface Weight"].default_value = 0.2; nd.inputs["Subsurface Scale"].default_value = 0.004
faceT = bone_empty("megan_face", "mixamorig:Head", (0, 0.09, 0.08))
armT = bone_empty("megan_arm", "mixamorig:LeftForeArm", (0, 0.14, 0.0))
chestT = bone_empty("megan_chest", "mixamorig:Spine2", (0, 0.0, 0.0))

# xonadagi chivin (3x kattalashtirilgan, ko'rinsin)
mqr = M.build_mosquito("mqr", 8.0)
mqr["root"].rotation_mode = "QUATERNION"
def mq_at(f, loc, fwd, up=(0, 0, 1)):
    fwd = Vector(fwd).normalized(); up = Vector(up)
    x = fwd.cross(up).normalized(); z = x.cross(fwd).normalized()
    m = Matrix((x, fwd, z)).transposed()
    mqr["root"].location = loc; mqr["root"].rotation_quaternion = m.to_quaternion()
    mqr["root"].keyframe_insert("location", frame=f); mqr["root"].keyframe_insert("rotation_quaternion", frame=f)
    M.wings_flap(mqr, f)
M.set_fill(mqr, 1, 0.0); M.set_fill(mqr, S["room_out"][0], 1.0)
vis(mqr["root"], rng("room_in", "room_out"))

def world_of(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()

# ======================================================================
# 4) KAMERALAR
# ======================================================================
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c
def cam_path(c, pts):
    for f, p in pts: key(c, f, loc=tuple(p))

# 1 HOOK: past burchak, oldidan 3/4, tez yaqinlashish
headT = empty("mq_headT", (-0.0016, 0.0, 0.0009))
c = shot_cam("hook", (0, 0, 0), headT, 55, 9.0)
cam_path(c, [(1, (0.007, -0.021, 0.0011)), (S["hook"][1], (0.0035, -0.0135, 0.0009))])
lens_keys(c, [(1, 50), (S["hook"][1], 56)])
# 2 xona: oldinda uchayotgan chivin fokusda, orqada Megan
F0, F1 = S["room_in"]
camP = RM + Vector((0.55, -1.75, 0.38))
c = shot_cam("room_in", tuple(camP), chestT, 24, 2.8, focus=mqr["root"])
key(c, F0, loc=tuple(camP)); key(c, F1, loc=tuple(camP + Vector((-0.08, 0.16, 0.03))))
dirv_in = (world_of(chestT, F0) - camP).normalized()
side_in = dirv_in.cross(Vector((0, 0, 1))).normalized()
for f in range(F0, F1 + 1):
    t = (f - F0) / (F1 - F0)
    p = camP + dirv_in * (0.22 + 0.2 * t) + side_in * (0.05 - 0.07 * t) + Vector((0, 0, -0.03 + 0.02 * t)) \
        + Vector((0.01 * math.sin(f * 1.3), 0.006 * math.sin(f * 0.9), 0.008 * math.sin(f * 1.7)))
    mq_at(f, tuple(p), dirv_in + side_in * -0.5)
hold_end(mqr["root"], F1)
# 3 PIERCE: yon profil, crash zoom
P0_, P1_ = S["pierce"]
pT = empty("pierceT", (-0.0005, 0.0, 0.0007))
c = shot_cam("pierce", (0, 0, 0), pT, 45, 10.0)
cam_path(c, [(P0_, (-0.0015, -0.026, 0.0012)), (P1_, (-0.0008, -0.022, 0.001))])
lens_keys(c, [(P0_, 45), (P0_ + 17, 48), (P0_ + 22, 95), (P1_, 105)])
shake(c, P0_ + 21, P0_ + 32, 0.0007, 3)
# 4 XS_SIX: kesim, kamera pastga suriladi (chivin boshidan teri ichigacha)
X60, X61 = S["xs_six"]
xT = empty("xs_sixT", tuple(X0 + Vector((0, 0, 0.004))))
key(xT, X60, loc=tuple(X0 + Vector((0, 0, 0.016)))); key(xT, X61, loc=tuple(X0 + Vector((0, 0, -0.008))))
c = shot_cam("xs_six", (0, 0, 0), xT, 32, 6.0, focus=0.11)
cam_path(c, [(X60, X0 + Vector((0.025, -0.11, 0.03))), (X61, X0 + Vector((0.008, -0.1, -0.006)))])
# 5 BEND: makro, chivin atrofida aylanish
B0, B1 = S["bend"]
bT = empty("bendT", (-0.0009, 0.0, 0.0008))
c = shot_cam("bend", (0, 0, 0), bT, 50, 11.0)
for f in range(B0, B1 + 1, 4):
    a = R(-100 + 55 * (f - B0) / (B1 - B0)); rr = 0.022
    key(c, f, loc=(-0.0009 + rr * math.cos(a) * 0.9, rr * math.sin(a), 0.0012 + 0.0015 * (f - B0) / (B1 - B0)))
# 6 STYLETS: o'ta makro, fokus labiumdan stiletlarga o'tadi
T0_, T1_ = S["stylets"]
sT = empty("stylT", (-0.0003, 0.0, 0.0005))
c = shot_cam("stylets", (0, 0, 0), sT, 100, 18.0, focus=sT)
cam_path(c, [(T0_, (0.004, -0.019, 0.0012)), (T1_, (0.0025, -0.015, 0.001))])
# 7 SAW: kesim yaqin, silkinish
W0, W1 = S["saw"]
wT = empty("sawT", tuple(X0 + Vector((0, 0, -0.0085))))
c = shot_cam("saw", (0, 0, 0), wT, 50, 7.0, focus=wT)
cam_path(c, [(W0, X0 + Vector((-0.006, -0.05, -0.004))), (W1, X0 + Vector((0.004, -0.04, -0.007)))])
for f0 in range(W0 + 4, W1 - 10, 14): shake(c, f0, f0 + 6, 0.0006, f0)
# 8 HOLD: kesim, yoy bo'ylab
H0_, H1_ = S["hold"]
hT = empty("holdT", tuple(X0 + Vector((0, 0, -0.005))))
c = shot_cam("hold", (0, 0, 0), hT, 42, 7.0, focus=hT)
cam_path(c, [(H0_, X0 + Vector((0.012, -0.05, 0.002))), (H1_, X0 + Vector((-0.01, -0.045, -0.004)))])
# 9 SEARCH: labrum uchini kuzatuvchi kamera
Q0, Q1 = S["search"]
srT = empty("searchT", (0, 0, 0))
c = shot_cam("search", (0, 0, 0), srT, 45, 6.0, focus=srT)
for f in range(Q0, Q1 + 1, 2):
    tp = X0 + labrum_tip(f)
    key(srT, f, loc=tuple(tp + Vector((0, 0, 0.002))))
    key(c, f, loc=tuple(X0 + Vector(((tp.x - X0.x) * 0.5 + 0.003, -0.042, tp.z - X0.z + 0.004))))
# 10 ENTER: qon tomiriga sanchiladi, crash zoom
N0, N1 = S["enter"]
nT = empty("enterT", tuple(X0 + Vector((0.003, 0, VZ + 0.003))))
c = shot_cam("enter", (0, 0, 0), nT, 30, 6.0, focus=nT)
cam_path(c, [(N0, X0 + Vector((0.012, -0.048, -0.008))), (N1, X0 + Vector((0.009, -0.042, -0.01)))])
lens_keys(c, [(N0, 30), (N0 + 14, 33), (N0 + 18, 70), (N1, 76)])
shake(c, N0 + 17, N0 + 29, 0.0012, 9)
# 11 SALIVA: so'lak purkaladi, sekin aylanish
A0_, A1_ = S["saliva"]
aT = empty("salT", tuple(X0 + Vector((0.0048, 0.001, VZ + 0.0005))))
c = shot_cam("saliva", (0, 0, 0), aT, 55, 5.6, focus=aT)
cam_path(c, [(A0_, X0 + Vector((0.016, -0.032, -0.012))), (A1_, X0 + Vector((-0.004, -0.03, -0.014)))])
# 12 VESSEL: qon tomiri ichida, hujayralar kameraga oqib keladi
V0, V1 = S["vessel"]
vT = empty("vesT", tuple(X0 + Vector((-0.03, 0.0, VZ))))
c = shot_cam("vessel", (0, 0, 0), vT, 18, 16.0, focus=0.02)
cam_path(c, [(V0, X0 + Vector((0.045, 0.0, VZ - 0.0008))), (V1, X0 + Vector((0.03, 0.0008, VZ - 0.0004)))])
# 13 FACE: Megan yuzi, DOF
FC0, FC1 = S["face"]
c = shot_cam("face", (0, 0, 0), faceT, 75, 2.0)
fp = world_of(faceT, FC0)
cam_path(c, [(FC0, fp + Vector((0.22, -0.62, -0.06))), (FC1, fp + Vector((0.19, -0.5, -0.05)))])
# 14 FILL: makro, orqadan-yondan, orqa yorug'lik
L0_, L1_ = S["fill"]
fT = empty("fillT", (-0.0042, 0.0, 0.0013))
c = shot_cam("fill", (0, 0, 0), fT, 55, 9.0)
for f in range(L0_, L1_ + 1, 4):
    a = R(-145 + 30 * (f - L0_) / (L1_ - L0_))
    key(c, f, loc=(-0.0042 + 0.017 * math.cos(a), 0.017 * math.sin(a), 0.0032 + 0.001 * (f - L0_) / (L1_ - L0_)))
# 15 ROOM_OUT: chivin qo'ldan uchib kameraga keladi; fokus Megan'dan chivinga
O0, O1 = S["room_out"]
camO = RM + Vector((0.5, -1.05, 0.42))
c = shot_cam("room_out", tuple(camO), armT, 26, 2.8, focus=1.0)
key(c, O0, loc=tuple(camO)); key(c, O1, loc=tuple(camO + Vector((0.03, 0.12, 0.0))))
arm0 = world_of(armT, O0) + Vector((0.0, -0.035, 0.035))
viewO = (world_of(armT, O0) - camO).normalized()
for f in range(O0, O1 + 1):
    t = (f - O0) / (O1 - O0)
    camf = camO + Vector((0.03, 0.12, 0.0)) * t
    tgt = camf + viewO * 0.2 + Vector((-0.015, 0, 0.0))
    tt = ease(max(0, (t - 0.12) / 0.88))
    p = arm0.lerp(tgt, tt) + Vector((0.01 * math.sin(f * 1.4), 0.006 * math.sin(f), 0.012 * math.sin(f * 1.9))) * tt
    if t < 0.12: p = arm0
    mq_at(f, tuple(p), (tgt - arm0) if t >= 0.12 else (0.3, -1.0, 0.0))
    d = (p - camf).length
    fa = (world_of(armT, f) - camf).length if f in (O0, O0 + 10) else None
    c.data.dof.focus_distance = d if t > 0.3 else (p - camf).length * (t / 0.3) + 1.05 * (1 - t / 0.3) * (camO - arm0).length
    c.data.dof.keyframe_insert("focus_distance", frame=f)
hold_end(mqr["root"], O1)
# 16 WELT: makro, terida do'mboq, crash zoom
WL0, WL1 = S["welt"]
weltT = empty("weltT", (0, 0, 0.0008))
c = shot_cam("welt", (0, 0, 0), weltT, 35, 22.0, focus=weltT)
cam_path(c, [(WL0, (0.012, -0.045, 0.017)), (WL1, (0.01, -0.04, 0.015))])
lens_keys(c, [(WL0, 30), (WL0 + 3, 32), (WL0 + 7, 50), (WL1, 54)])
shake(c, WL0 + 6, WL0 + 16, 0.0008, 13)
# 17 IMMUNE: kesim, yaqinlashish
I0, I1 = S["immune"]
iT = empty("immT", tuple(X0 + Vector((0, 0, -0.008))))
c = shot_cam("immune", (0, 0, 0), iT, 40, 6.0, focus=iT)
cam_path(c, [(I0, X0 + Vector((-0.012, -0.075, 0.004))), (I1, X0 + Vector((-0.006, -0.058, 0.0)))])
# 18 SCRATCH: past burchak, yaqin, push-in
SC0, SC1 = S["scratch"]
scT = empty("scratchT", (0, 0, 0))
c = shot_cam("scratch", (0, 0, 0), scT, 28, 2.8, focus=faceT)
fp = world_of(chestT, SC0)
key(scT, SC0, loc=tuple(fp + Vector((0, 0, 0.05))))
cam_path(c, [(SC0, fp + Vector((0.42, -0.85, -0.45))), (SC1, fp + Vector((0.3, -0.6, -0.38)))])
lens_keys(c, [(SC0, 28), (SC1 - 8, 32), (SC1, 40)])

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 5) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
tcw = N.new("ShaderNodeTexCoord"); mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(120))
L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
L.new(mpw.outputs[0], env.inputs[0])
tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs["Factor"].default_value = 1.0
L.new(env.outputs[0], tint.inputs[6])
bg = N["Background"]; L.new(tint.outputs[2], bg.inputs[0])
WL = {"macro": ((1.0, 0.78, 0.6), 0.18), "room": ((0.75, 0.82, 1.0), 0.15), "xsec": ((0.25, 0.35, 0.6), 0.03)}
for f, n in SHOTS:
    col, st = WL[KIND[n]]
    tint.inputs[7].default_value = (*col, 1); tint.inputs[7].keyframe_insert("default_value", frame=f)
    bg.inputs[1].default_value = st; bg.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

root_m = mq["root"]
# makro: issiq asosiy yorug'lik, sovuq kontur, orqa yorug'lik (qorin uchun)
area("m_key", (-0.06, -0.09, 0.11), 0.08, (1, 0.9, 0.78), lights_for(MACRO, 0.9), target=bite)
area("m_rim", (0.05, 0.11, 0.05), 0.05, (0.55, 0.72, 1.0), lights_for(MACRO, 1.0), target=bite)
area("m_back", (-0.06, 0.03, 0.02), 0.03, (1.0, 0.75, 0.6), lights_for(rng("fill"), 1.5), target=fT)
# kesim: tibbiy illyustratsiya yorug'ligi
area("x_key", tuple(X0 + Vector((-0.06, -0.22, 0.12))), 0.2, (1, 0.95, 0.9), lights_for(XSEC, 3.5), target=xroot)
area("x_fill", tuple(X0 + Vector((0.12, -0.15, -0.06))), 0.2, (0.7, 0.8, 1.0), lights_for(XSEC, 1.0), target=xroot)
area("x_rim", tuple(X0 + Vector((0.0, 0.12, 0.1))), 0.15, (0.4, 0.6, 1.0), lights_for(XSEC, 4.0), target=xroot)
area("x_vessel", tuple(X0 + Vector((0.025, 0.0, VZ))), 0.003, (1.0, 0.5, 0.45), lights_for(rng("vessel"), 0.02), kind="POINT")
# xona: torsher, deraza, televizor (miltillaydi), to'ldiruvchi
area("r_lamp", tuple(RM + Vector((1.15, 0.3, 1.5))), 0.08, (1.0, 0.72, 0.45), lights_for(ROOM, 60), kind="POINT")
area("r_window", tuple(RM + Vector((-2.0, -1.2, 2.2))), 1.5, (0.75, 0.85, 1.0), lights_for(ROOM, 160), target=chestT)
tv = area("r_tv", tuple(RM + Vector((0.0, -2.6, 0.95))), 0.9, (0.5, 0.7, 1.0), [(1, 0)], target=chestT)
rnd = random.Random(4)
for f in range(1, END + 1, 3):
    on = any(a <= f <= b for a, b in ROOM)
    tv.data.energy = (45 + 25 * rnd.random()) if on else 0; tv.data.keyframe_insert("energy", frame=f)
interp(tv.data, "CONSTANT")
area("r_fill", tuple(RM + Vector((0.8, -1.6, 1.3))), 0.8, (1.0, 0.9, 0.8), lights_for(ROOM, 35), target=chestT)
area("r_rim", tuple(RM + Vector((-0.6, 0.45, 1.9))), 0.4, (1.0, 0.8, 0.6), lights_for(ROOM, 30), target=faceT)

# ======================================================================
# 6) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 12)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.1
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
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
