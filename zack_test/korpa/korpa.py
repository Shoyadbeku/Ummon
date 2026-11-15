# Ko'rpani boshga yopib uxlash (CO2 bilan zaharlanish) — Zack D. Films uslubida 44.7 s video (1072 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; yordamchilar: zack_test/paxta/parts.py (quvur, rentgen, miya).
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/korpa/korpa.py --render
# Sinov:  FRAMES=20,90,140 PCT=30 OUT=/tmp/claude-0/test/
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "paxta"))
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1072
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan) ----------------
SHOTS = [(1, "hook"), (48, "cover"), (116, "cozy"), (165, "wasteA"), (215, "wasteB"), (269, "exhale"), (309, "lungs"),
         (342, "four"), (376, "co2"), (425, "cave"), (471, "bounce"), (510, "fill"), (560, "o2"), (604, "gauge"),
         (640, "blood"), (690, "brainx"), (730, "choke"), (771, "wake"), (797, "ache"), (846, "mouth"), (870, "ten"),
         (913, "beaten"), (960, "push"), (1002, "poison")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM = rng("hook", "cover", "wake", "ache", "ten", "beaten", "push")
MORN = rng("wake", "ache", "beaten", "push")
CAVE = rng("cozy", "wasteA", "wasteB", "cave", "bounce", "fill", "o2", "gauge", "brainx", "poison")
XRAY = rng("exhale", "lungs", "brainx", "poison")
REAL = rng("hook", "cover", "cozy", "wasteA", "wasteB", "cave", "bounce", "fill", "o2", "gauge", "wake", "ache", "ten", "beaten", "push")
CLOSED = rng("cozy", "wasteA", "wasteB", "cave", "bounce", "fill", "o2", "gauge")

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

def emis(name, col, strength=3.0, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    sv = N.new("ShaderNodeValue"); sv.name = "glow"; sv.outputs[0].default_value = strength; L.new(sv.outputs[0], em.inputs["Strength"])
    if alpha is None:
        L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    else:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha
        L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
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
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if parent: o.parent = parent
    return o

def torus(name, R_, r, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R_, minor_radius=r, major_segments=48, minor_segments=10)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); o.location = loc; o.rotation_euler = [R(a) for a in rot]
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

_font = None
def text(name, body, size, loc, rot, m, parent=None, align="CENTER", extrude=0.0):
    global _font
    if _font is None: _font = bpy.data.fonts.load(FONT)
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.font = _font; cu.size = size
    cu.align_x = align; cu.align_y = "CENTER"; cu.extrude = extrude
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(m)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
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

def noisy(o, strength=0.05, scale=0.5, sub=0):
    t = bpy.data.textures.new(o.name + "_n", "CLOUDS"); t.noise_scale = scale
    if sub:
        s = o.modifiers.new("s", "SUBSURF"); s.levels = sub; s.render_levels = sub; s.show_viewport = False
    d = o.modifiers.new("d", "DISPLACE"); d.texture = t; d.strength = strength; d.texture_coords = "LOCAL"
    d.show_viewport = False
    return o

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.01, parent=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 400
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if parent: c.parent = parent
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

def area(name, loc, size, col, keys, target=None, shape=None, cam_vis=False, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    else: interp(l.data, "LINEAR")
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
    else: interp(l.data, "LINEAR")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def at(name, p, parent=None): return empty(name, tuple(p), parent)

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value
def lin(m):
    for fc in fcurves(m.node_tree):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"

# ======================================================================
# 1) YOTOQXONA (dunyo markazi)
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.62, 0.72, 0.82))
X0, X1, Y0, Y1, HZ_ = -2.4, 2.0, -1.75, 1.6, 2.6
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.85, 0.85, 0.85), 0.8)))
R_(box("wall_L", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_F", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
WX0, WX1, WZ0, WZ1 = 0.0, 1.2, 1.0, 2.1
R_(box("wall_B1", (WX0 - X0, 0.1, HZ_), ((X0 + WX0) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
R_(box("wall_B2", (X1 - WX1, 0.1, HZ_), ((WX1 + X1) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
R_(box("wall_B3", (WX1 - WX0, 0.1, WZ0), ((WX0 + WX1) / 2, Y0 - 0.05, WZ0 / 2), wall_m))
R_(box("wall_B4", (WX1 - WX0, 0.1, HZ_ - WZ1), ((WX0 + WX1) / 2, Y0 - 0.05, (WZ1 + HZ_) / 2), wall_m))
frame_m = mat("win_frame", (0.92, 0.92, 0.9), 0.4)
WC = Vector(((WX0 + WX1) / 2, Y0 - 0.05, (WZ0 + WZ1) / 2))
for nm, sz, off in (("wf_t", (1.24, 0.12, 0.05), (0, 0, 0.55)), ("wf_b", (1.24, 0.16, 0.06), (0, 0.03, -0.55)),
                    ("wf_l", (0.05, 0.12, 1.1), (-0.6, 0, 0)), ("wf_r", (0.05, 0.12, 1.1), (0.6, 0, 0)),
                    ("wf_m", (0.04, 0.08, 1.1), (0, 0, 0)), ("wf_h", (1.2, 0.08, 0.04), (0, 0, 0.12))):
    R_(box(nm, sz, tuple(WC + Vector(off)), frame_m))
sky_m = bpy.data.materials.new("sky"); sky_m.use_nodes = True
N = sky_m.node_tree.nodes; L = sky_m.node_tree.links; N.remove(N["Principled BSDF"])
dayv = value_node(sky_m, "day", 0.0)
tcs = N.new("ShaderNodeTexCoord"); grad = N.new("ShaderNodeSeparateXYZ"); L.new(tcs.outputs["Generated"], grad.inputs[0])
cn = N.new("ShaderNodeMix"); cn.data_type = "RGBA"; cn.inputs[6].default_value = (0.008, 0.015, 0.05, 1); cn.inputs[7].default_value = (0.45, 0.68, 1.0, 1)
L.new(dayv, cn.inputs["Factor"])
hor = N.new("ShaderNodeMix"); hor.data_type = "RGBA"; hor.inputs[7].default_value = (1.0, 0.75, 0.5, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, grad.outputs["Y"], clamp=True), 0.5), hor.inputs["Factor"])
L.new(cn.outputs[2], hor.inputs[6])
em = N.new("ShaderNodeEmission"); L.new(hor.outputs[2], em.inputs["Color"])
L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", dayv, 5.0), 0.6), em.inputs["Strength"])
L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
R_(plane("sky", (6, 4), (0.6, Y0 - 1.2, 1.6), sky_m, rot=(90, 0, 0)))
star_m = mat("star", (1, 1, 1), emit=6.0)
stars = empty("stars"); R_(stars)
for i in range(30):
    sphere(f"star{i}", random.uniform(0.004, 0.009), (random.uniform(-1.4, 2.6), Y0 - 1.15, random.uniform(1.0, 3.4)), star_m, sub=1, parent=stars)
sphere("moon", 0.11, (1.05, Y0 - 1.1, 2.55), mat("moon_m", (0.9, 0.93, 1.0), emit=8.0), sub=3, parent=stars)

plant = R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.55, -1.3, 0), 30, 0.9))
shelf = R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X1 - 0.02, 0.55, 0), -90, 1.0))
books = R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X1 - 0.15, 0.82, 1.03), -90, 1.0))
chair = R_(import_gltf(PH + "modern_arm_chair_01/modern_arm_chair_01.gltf", (1.1, 0.9, 0), -140, 1.0))

# --- karavot ---
BEDC = Vector((-1.6, 0.2, 0))
MT = 0.55                                          # matras usti
wood_m = mat("bed_wood", (0.33, 0.2, 0.12), 0.45, coat=0.2)
sheet_m = mat("sheet", (0.88, 0.9, 0.95), 0.75, sss=0.05)
foam_m = mat("foam", (0.95, 0.85, 0.55), 0.9)
fill_m = mat("duvet_fill", (0.93, 0.93, 0.9), 0.95)
duvet_m = bpy.data.materials.new("duvet"); duvet_m.use_nodes = True
N = duvet_m.node_tree.nodes; L = duvet_m.node_tree.links; b = N["Principled BSDF"]
tcd = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 6.0
L.new(tcd.outputs["Object"], wv.inputs["Vector"])
dmx = N.new("ShaderNodeMix"); dmx.data_type = "RGBA"; dmx.inputs[6].default_value = (0.12, 0.2, 0.45, 1); dmx.inputs[7].default_value = (0.2, 0.32, 0.6, 1)
L.new(P.math_n(N, L, "GREATER_THAN", wv.outputs["Fac"], 0.5), dmx.inputs["Factor"]); L.new(dmx.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.85; b.inputs["Sheen Weight"].default_value = 0.6
R_(box("bed_frame", (1.5, 2.1, 0.22), tuple(BEDC + Vector((0, 0, 0.22))), wood_m, bevel=0.02))
R_(box("bed_head", (1.55, 0.08, 1.05), tuple(BEDC + Vector((0, 1.09, 0.525))), wood_m, bevel=0.02))
R_(box("mattress", (1.42, 2.0, 0.22), tuple(BEDC + Vector((0, 0.0, MT - 0.11))), sheet_m, bevel=0.06))
pl = R_(box("pillow", (0.75, 0.4, 0.12), tuple(BEDC + Vector((0, 0.86, MT + 0.02))), sheet_m, bevel=0.06)); noisy(pl, 0.02, 0.2)
MEG_BED = BEDC + Vector((0.0, 0.25, MT - 0.95))
DUV0 = BEDC + Vector((0, -0.29, MT + 0.15))
duv = R_(box("duvet", (1.56, 1.5, 0.34), (0, 0, 0), duvet_m, bevel=0.1))
_bm = bmesh.new(); _bm.from_mesh(duv.data)
bmesh.ops.subdivide_edges(_bm, edges=_bm.edges[:], cuts=10, use_grid_fill=True); _bm.to_mesh(duv.data); _bm.free()
for v in duv.data.vertices:
    if abs(v.co.x) > 0.7: v.co.z -= 0.16
    if v.co.y < -0.7: v.co.z -= 0.08
    v.co.y += 0.75                                 # origin oyoq tomondagi chetda: Y bo'yicha cho'zilib boshni yopadi
sub = duv.modifiers.new("s", "SUBSURF"); sub.levels = 1; sub.render_levels = 2; sub.show_viewport = False
noisy(duv, 0.06, 0.25)
DUVL = DUV0 + Vector((0, -0.75, 0))
CV0, CV1 = S["cover"]
key(duv, 1, loc=tuple(DUVL), scale=(1, 1, 1)); key(duv, CV0 + 10, scale=(1, 1, 1)); key(duv, CV0 + 26, scale=(1, 1.42, 1))
interp(duv, "BEZIER")
key(duv, S["wake"][0], loc=tuple(DUVL + Vector((-0.42, 0, 0))), scale=(0.55, 1.0, 1.15))       # ertalab: chetga surilgan
key(duv, S["ten"][0], loc=tuple(DUVL), scale=(1, 1.42, 1))
key(duv, S["beaten"][0], loc=tuple(DUVL + Vector((-0.42, 0, 0))), scale=(0.55, 1.0, 1.15))
for fc in fcurves(duv):
    for k in fc.keyframe_points:
        if k.co.x >= S["wake"][0] - 1 or k.co.x == CV0 + 26: k.interpolation = "CONSTANT"
NS = BEDC + Vector((1.05, 0.85, 0))
R_(box("nightstand", (0.45, 0.4, 0.5), tuple(NS + Vector((0, 0, 0.25))), wood_m, bevel=0.01))
CLK = NS + Vector((0.0, -0.02, 0.5))
clock = R_(import_gltf(PH + "alarm_clock_01/alarm_clock_01.gltf", tuple(CLK), -60, 1.3))
rug = R_(plane("rug", (1.4, 1.0), (-0.1, -0.3, 0.004), mat("rug", (0.45, 0.14, 0.12), 0.95)))

# ======================================================================
# 2) KO'RPA OSTI KESIMI (CV): matras, yostiq, kesilgan ko'rpa "g'ori"
# ======================================================================
CV = Vector((30, 0, 0))
cave = empty("cave_grp", tuple(CV))
CUTX = 0.34
def tent_z(x, y):
    px = max(0.0, 1 - abs((x + 0.05) / 0.76) ** 3)
    hy = 0.31 + 0.13 * ease((y - 0.22) / 0.26)
    if y > 0.74: hy *= math.sqrt(max(0.0, 1 - ((y - 0.74) / 0.34) ** 2))
    if y < -0.85: hy *= math.sqrt(max(0.0, 1 - ((-0.85 - y) / 0.3) ** 2))
    return MT + 0.012 + hy * px
def tent_mesh():
    nx, ny = 44, 90; bm = bmesh.new(); vs = []
    for j in range(ny + 1):
        y = -1.15 + (1.08 + 1.15) * j / ny
        for i in range(nx + 1):
            x = -0.81 + (CUTX + 0.81) * i / nx
            vs.append(bm.verts.new((x, y, tent_z(x, y))))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            bm.faces.new((vs[a], vs[a + 1], vs[a + nx + 2], vs[a + nx + 1]))
    bm.normal_update()
    if sum(f.normal.z for f in bm.faces) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("tent"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new("tent", me); sc.collection.objects.link(o); o.parent = cave
    me.materials.append(duvet_m); me.materials.append(fill_m)
    so = o.modifiers.new("so", "SOLIDIFY"); so.thickness = 0.035; so.offset = 1.0; so.material_offset_rim = 1; so.show_viewport = False
    return o
tent = tent_mesh()
box("cv_mattress", (CUTX + 0.82, 2.45, 0.22), ((CUTX - 0.82) / 2, -0.02, MT - 0.11), sheet_m, parent=cave)
box("cv_foam", (0.004, 2.43, 0.2), (CUTX + 0.001, -0.02, MT - 0.11), foam_m, parent=cave)
box("cv_frame", (CUTX + 0.86, 2.5, 0.22), ((CUTX - 0.86) / 2, -0.02, 0.22), wood_m, parent=cave)
box("cv_head", (CUTX + 0.86, 0.08, 1.05), ((CUTX - 0.86) / 2, 1.27, 0.525), wood_m, parent=cave)
cpl = box("cv_pillow", (0.6, 0.4, 0.12), (0.03, 0.66, MT + 0.02), sheet_m, parent=cave, bevel=0.05)
box("cv_wall", (0.1, 8, 4), (-0.92, 0, 1.5), mat("cv_wall_m", (0.08, 0.1, 0.16), 0.9), parent=cave)
plane("cv_floor", (8, 8), (0, 0, 0), mat("cv_floor_m", (0.05, 0.05, 0.06), 0.8), parent=cave)
MEG_CV = CV + Vector((0, 0, MT - 0.95))
HC = Vector((0.06, 0.63, MT + 0.10))                 # bosh markazi (CV fazosi)
NP = Vector((0.165, 0.566, MT + 0.17))               # burun uchi
MOUTH = Vector((0.14, 0.535, MT + 0.155))
# bo'shliq chegarasi (sariq chiziq)
out_m = emis("outline", (1.0, 0.8, 0.1), 5.0)
opts = [(CUTX + 0.004, 0.24 + 0.84 * k / 30, 0) for k in range(31)]
opts = [(x, y, tent_z(CUTX, y) - 0.004) for x, y, _ in opts] + [(CUTX + 0.004, 1.08, MT + 0.01), (CUTX + 0.004, 0.9, MT + 0.085), (CUTX + 0.004, 0.75, MT + 0.085)]
outline = P.tube("cv_outline", opts, 0.005, out_m, cave)
vis(cave, CAVE)
vis(outline, rng("cave"), recursive=False)

# ======================================================================
# 3) MEGAN
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
shv = empty("shiver", (0, 0, 0), mroot); meg.parent = shv
def soften(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.45
                    n.inputs["Coat Weight"].default_value = 0.0
soften(mmeshes)
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
SIT = Vector((-1.02, 0.0, 0.03))
def place(f, loc, rot=0.0):
    mroot.location = loc; mroot.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): mroot.keyframe_insert(p, frame=f)
place(1, tuple(MEG_BED)); place(S["cozy"][0], tuple(MEG_CV)); place(S["wake"][0], tuple(SIT), 90)
place(S["ten"][0], tuple(MEG_BED)); place(S["beaten"][0], tuple(SIT), 90); place(S["poison"][0], tuple(MEG_CV))
interp(mroot, "CONSTANT")
def strip(act, start, repeat=1.0, speed=1.0):
    s = mc.add_strip(meg, act, start, repeat=repeat, speed=speed, blend=0, hold=False)
    s.blend_in = s.blend_out = 0; s.use_auto_blend = False
    return s
def chain(act, f0, f1, speed=0.6):                  # oldinga/orqaga zanjir (sakrashsiz)
    st, k = f0, 0
    while st <= f1:
        s = strip(act, st, speed=speed); s.use_reverse = (k % 2 == 1)
        st = int(s.frame_end); k += 1
        if s.frame_end > f1 + 1: s.frame_end = f1 + 1
lay = A_("Laying_Sleeping.fbx")
chain(lay, 1, S["wake"][0] - 1)
strip(A_("Sitting_Disbelief_3.fbx"), S["wake"][0] - 2)
chain(lay, S["ten"][0], S["ten"][1])
_s = mc.add_strip(meg, A_("Sitting_Disbelief_2.fbx"), S["beaten"][0], speed=0.34, blend=0, hold=False, src=(44, 82))
_s.blend_in = _s.blend_out = 0; _s.use_auto_blend = False
chain(lay, S["poison"][0], END)
# ilgak: sovqotib titrash
rs_ = random.Random(2)
for f in range(1, S["hook"][1] + 1):
    key(shv, f, loc=(rs_.uniform(-1, 1) * 0.004, rs_.uniform(-1, 1) * 0.003, rs_.uniform(-1, 1) * 0.002))
key(shv, S["hook"][1] + 1, loc=(0, 0, 0))
# beaten: og'ir nafas (root yengil tebranadi)
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.07, 0.1), headE)          # ko'zlar oldi (Head fazosi: X chap, Y tepa, Z old)
noseT = empty("noseT", (0, 0.045, 0.15), headE)
browT = empty("browT", (0, 0.11, 0.1), headE)

# yopiq ko'zlar: ko'z soqqasi orollarini teri rangida biroz kattalashtirilgan nusxa + kiprik chizig'i
body = next(o for o in mmeshes if o.name.endswith("Body"))
lashes = next(o for o in mmeshes if "Eyelash" in o.name)
def islands(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    seen = [-1] * len(bm.verts); isl = 0
    for v in bm.verts:
        if seen[v.index] >= 0: continue
        st = [v]; seen[v.index] = isl
        while st:
            a = st.pop()
            for e in a.link_edges:
                b_ = e.other_vert(a)
                if seen[b_.index] < 0: seen[b_.index] = isl; st.append(b_)
        isl += 1
    bm.free(); return seen
_seen = islands(body.data); _cnt = {}
for i in _seen: _cnt[i] = _cnt.get(i, 0) + 1
_big = max(_cnt, key=_cnt.get)
bpy.context.view_layer.update()
Wb = mroot.matrix_world.inverted() @ body.matrix_world; Wbi = Wb.inverted()
ECS = [Vector((0.0324, -0.1185, 1.6211)), Vector((-0.0324, -0.1185, 1.6211))]
eye_isl = {}
for i, v in enumerate(body.data.vertices):
    if _seen[i] == _big: continue
    p = Wb @ v.co
    for k, ec in enumerate(ECS):
        if (p - ec).length < 0.022: eye_isl[_seen[i]] = k
print("eye islands:", eye_isl, "Wb scale", Wb.to_scale())
lidcap = body.copy(); lidcap.data = body.data.copy(); lidcap.name = "meg_lidcap"; sc.collection.objects.link(lidcap)
lidcap.animation_data_clear()
bm = bmesh.new(); bm.from_mesh(lidcap.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if _seen[v.index] not in eye_isl], context="VERTS")
keep = [i for i in range(len(_seen)) if _seen[i] in eye_isl]
for v, i in zip(bm.verts, keep):
    ec = ECS[eye_isl[_seen[i]]]; p = Wb @ v.co; v.co = Wbi @ (ec + (p - ec) * 1.13)
bm.to_mesh(lidcap.data); bm.free()
lid_skin = mat("lidcap_skin", (0.47, 0.26, 0.2), 0.5, sss=0.1, sss_scale=0.002)
lidcap.data.materials.clear(); lidcap.data.materials.append(lid_skin)
lline_m = mat("lidline", (0.05, 0.03, 0.02), 0.4)
llines = []
for sx in (1, -1):
    lpts = []
    for k in range(9):
        x = 0.019 + 0.027 * k / 8; u = (x - 0.0325) / 0.0135
        lpts.append((sx * x, 0.088 - 0.0045 - 0.0016 * (1 - u * u), 0.135 + 0.0055 - 0.0045 * u * u))
    llines.append(P.tube(f"meg_lidline{sx}", lpts, 0.0007, lline_m, headE))

# rentgen nusxasi
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.4, base=0.015)
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g); g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, XRAY, recursive=False)
for o in mmeshes:
    if any(k in o.name for k in ("Pants", "Sneakers")): vis(o, MORN, recursive=False)
    elif "Eyelash" in o.name: vis(o, [r_ for r_ in REAL if r_ not in CLOSED], recursive=False)
    else: vis(o, REAL, recursive=False)
vis(lidcap, CLOSED, recursive=False)
for o in llines: vis(o, CLOSED, recursive=False)
for o in room_objs: vis(o, ROOM)
vis(stars, rng("hook", "cover"))

# ======================================================================
# 4) GAZ MOLEKULALARI (CO2: kulrang C + 2 qizil O; O2: 2 ko'k shar)
# ======================================================================
c_m = mat("mol_C", (0.03, 0.03, 0.035), 0.25, coat=0.6, emit=0.25, emit_col=(0.5, 0.9, 0.3))
o_m = mat("mol_O", (0.75, 0.04, 0.03), 0.22, coat=0.8, emit=0.9, emit_col=(1.0, 0.1, 0.04))
b_m = mat("mol_O2", (0.1, 0.45, 1.0), 0.2, coat=0.8, emit=2.2, emit_col=(0.15, 0.55, 1.0))
bond_m = mat("mol_bond", (0.6, 0.6, 0.62), 0.3, metal=0.6)
def mol_mesh(name, kind, seg=14, bonds=False):
    bm = bmesh.new()
    def ball(r, x, mi):
        g = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation((x, 0, 0)))
        fs = {f for v in g["verts"] for f in v.link_faces}
        for f in fs: f.material_index = mi; f.smooth = True
    if kind == "co2":
        ball(1.0, 0, 0); ball(0.86, 1.55, 1); ball(0.86, -1.55, 1)
        if bonds:
            for sx in (-1, 1):
                for dz in (-0.25, 0.25):
                    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.13, radius2=0.13, depth=1.0,
                                              matrix=Matrix.Translation((sx * 0.95, 0, dz)) @ Matrix.Rotation(R(90), 4, "Y"))
                    for f in {f for v in g["verts"] for f in v.link_faces}: f.material_index = 2; f.smooth = True
    else:
        ball(0.9, 0.62, 0); ball(0.9, -0.62, 0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if kind == "co2": me.materials.append(c_m); me.materials.append(o_m); me.materials.append(bond_m)
    else: me.materials.append(b_m)
    return me
CO2_ME = mol_mesh("co2_lo", "co2", 12); O2_ME = mol_mesh("o2_lo", "o2", 12); CO2_HI = mol_mesh("co2_hi", "co2", 40, bonds=True)
def mol(name, me, parent, s=1.0, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = parent; o.location = loc; o.scale = (s,) * 3
    return o

# --- g'or ichidagi bulut ---
gas = empty("gas_grp", tuple(CV))
NCO, NO2, MS = 120, 30, 0.0105
rg = random.Random(11)
def in_cave(p, margin=0.03):
    if p.x > CUTX - 0.03 or p.z < MT + 0.105: return False
    if (p - HC).length < 0.14: return False
    if p.y < 0.36 and p.z < MT + 0.33: return False            # yelka / ko'krak ustida emas
    return p.z < tent_z(p.x, p.y) - margin
def sample(near=None, rad=0.0):
    while True:
        if near is not None:
            p = near + Vector((rg.uniform(0.01, rad), rg.uniform(-rad, rad), rg.uniform(-rad * 0.6, rad)))
        else:
            p = Vector((rg.uniform(-0.2, CUTX), rg.uniform(0.3, 1.04), rg.uniform(MT + 0.1, MT + 0.45)))
        if in_cave(p): return p
bases = [sample(NP, 0.085) for _ in range(25)] + [sample() for _ in range(NCO - 25)]
obase = [sample() for _ in range(NO2)]
phs = [[rg.uniform(0, 6.28) for _ in range(3)] + [rg.uniform(0.07, 0.15) for _ in range(3)] for _ in range(NCO + NO2)]
def wpos(b, ph, f, amp=0.022):
    return b + Vector((amp * math.sin(f * ph[3] + ph[0]), amp * math.sin(f * ph[4] + ph[1]), amp * 0.6 * math.sin(f * ph[5] + ph[2])))
GR = [(S["wasteA"][0], S["wasteB"][1]), (S["cave"][0], S["gauge"][1]), S["brainx"], S["poison"]]
WA0, WA1 = S["wasteA"]; WB0, WB1 = S["wasteB"]; BO0, BO1 = S["bounce"]; FI0, FI1 = S["fill"]; OX0, OX1 = S["o2"]
ring_m = emis("ring_red", (1.0, 0.12, 0.05), 2.4)
ESC = list(range(25, 37)); impacts = []
co2s = []
for i in range(NCO):
    o = mol(f"co2_{i}", CO2_ME, gas, MS); co2s.append(o); b_ = bases[i]; ph = phs[i]
    r0 = Euler((rg.uniform(0, 6), rg.uniform(0, 6), rg.uniform(0, 6))); rr = Vector((rg.uniform(-1, 1), rg.uniform(-1, 1), rg.uniform(-1, 1))) * 0.06
    o.rotation_euler = r0; o.keyframe_insert("rotation_euler", frame=1)
    o.rotation_euler = (r0.x + rr.x * END, r0.y + rr.y * END, r0.z + rr.z * END); o.keyframe_insert("rotation_euler", frame=END)
    for a, b in GR:
        fs = sorted(set(list(range(a, b + 1, 3)) + [b]))
        if i < 25 and a == WA0: fs = list(range(a, b + 1))
        for f in fs:
            p = wpos(b_, ph, f)
            if i < 25 and WA0 <= f <= WA1:
                sp = WA0 + 3 + i * 1.7
                p = NP.lerp(p, 1 - (1 - ease((f - sp) / 16)) ** 2)
            if i < 25 and WB0 <= f <= WB1:
                k = (0.5 - 0.5 * math.cos(2 * math.pi * (f - WB0 - i * 0.25) / 27)) ** 2
                p = p.lerp(NP + Vector((0.004, 0, 0)), 0.86 * k)
            if i in ESC and BO0 <= f <= BO1:
                fi = BO0 + 8 + ESC.index(i) * 3
                top = Vector((b_.x, b_.y, tent_z(b_.x, b_.y) - 0.022))
                if f <= fi: p = p.lerp(top, ((f - BO0) / (fi - BO0)) ** 2)
                else: p = top.lerp(p + Vector((0, 0, -0.04)), 1 - (1 - min(1, (f - fi) / 16)) ** 2)
            o.location = p; o.keyframe_insert("location", frame=f)
        if i in ESC and a == S["cave"][0]:
            fi = BO0 + 8 + ESC.index(i) * 3
            top = Vector((b_.x, b_.y, tent_z(b_.x, b_.y) - 0.022))
            for f in range(fi - 6, fi + 8):
                if f <= fi: p = wpos(b_, ph, f).lerp(top, ((f - BO0) / (fi - BO0)) ** 2)
                else: p = top.lerp(wpos(b_, ph, f) + Vector((0, 0, -0.04)), 1 - (1 - min(1, (f - fi) / 16)) ** 2)
                o.location = p; o.keyframe_insert("location", frame=f)
            impacts.append((fi, top))
    interp(o, "LINEAR")
    # ko'rinish (masshtab)
    if i < 25:
        sp = int(WA0 + 3 + i * 1.7)
        key(o, 1, scale=0.0); key(o, sp, scale=0.0); key(o, sp + 4, scale=MS)
        for f in range(WB0, WB1 + 1, 1):
            k = (0.5 - 0.5 * math.cos(2 * math.pi * (f - WB0 - i * 0.25) / 27)) ** 2
            key(o, f, scale=MS * (1 - 0.8 * k))
        key(o, WB1 + 1, scale=MS)
    elif i < 44:
        key(o, 1, scale=MS)
        if i >= 25: key(o, WA0, scale=0.0); key(o, S["cave"][0], scale=MS); interp(o, "CONSTANT", "scale")
    else:
        sp = int(FI0 + 2 + (i - 44) * 0.52)
        key(o, 1, scale=0.0); key(o, sp, scale=0.0); key(o, sp + 3, scale=MS * 1.5); key(o, sp + 6, scale=MS)
for k, (fi, top) in enumerate(impacts):
    rgo = torus(f"imp{k}", 0.02, 0.0028, tuple(top - Vector((0, 0, 0.006))), ring_m, parent=gas)
    key(rgo, 1, scale=0.0); key(rgo, fi - 1, scale=0.0); key(rgo, fi, scale=0.6); key(rgo, fi + 7, scale=3.2); key(rgo, fi + 8, scale=0.0)
o2s = []
for i in range(NO2):
    o = mol(f"o2_{i}", O2_ME, gas, MS * 0.95); o2s.append(o); b_ = obase[i]; ph = phs[NCO + i]
    o.rotation_euler = (rg.uniform(0, 6), rg.uniform(0, 6), rg.uniform(0, 6))
    a, b = GR[1]
    for f in sorted(set(list(range(a, b + 1, 3)) + [b])):
        o.location = wpos(b_, ph, f); o.keyframe_insert("location", frame=f)
    interp(o, "LINEAR")
    sp = int(OX0 + 2 + i * (OX1 - OX0 - 8) / NO2)
    key(o, 1, scale=MS); key(o, sp, scale=MS); key(o, sp + 2, scale=MS * 1.5); key(o, sp + 5, scale=0.0)
o2g = empty("o2_grp", (0, 0, 0), gas)
for o in o2s: o.parent = o2g
vis(gas, GR)
vis(o2g, [GR[1]])

# --- HUD: taymer va O2 o'lchagichi (ko'krak ustidagi bo'sh joyda, kesim tekisligida) ---
hud = empty("hud", tuple(CV + Vector((CUTX + 0.03, 0.5, MT + 0.74))))
hud_w = emis("hud_white", (1, 1, 1), 2.6); hud_b = emis("hud_blue", (0.12, 0.5, 1.0), 1.6); hud_d = mat("hud_dark", (0.01, 0.012, 0.02), 0.4)
timer = text("timer", "00:00", 0.13, (0, 0.0, 0.02), (90, 0, 90), hud_w, parent=hud)
tlabel = text("tlabel", "DAQIQA", 0.04, (0, 0.0, -0.085), (90, 0, 90), emis("hud_yel", (1.0, 0.8, 0.1), 3.0), parent=hud)
gau = empty("gauge", (0, 0, 0), hud)
BARL = 0.46
box("g_back", (0.012, BARL + 0.03, 0.085), (-0.012, 0.0, 0.0), hud_d, parent=gau, bevel=0.005)
gbar = box("g_bar", (0.012, BARL, 0.055), (0, 0, 0), hud_b, parent=gau)
for v in gbar.data.vertices: v.co.y += BARL / 2
gbar.location = (0, -BARL / 2, 0)
glab = text("g_lab", "O₂", 0.085, (0, -BARL / 2 + 0.01, 0.11), (90, 0, 90), hud_b, parent=gau, align="LEFT")
gpct = text("g_pct", "21%", 0.105, (0, BARL / 2, 0.115), (90, 0, 90), hud_w, parent=gau, align="RIGHT")
GA0, GA1 = S["gauge"]
def o2_level(f):
    if f < OX0: return 21.0
    if f <= OX1: return 21.0 - 3.0 * (f - OX0) / (OX1 - OX0)
    return 18.0 - 6.5 * ease((f - GA0) / 20.0) - 0.5 * min(1, max(0, (f - GA0 - 20) / 16))
for f in range(OX0, GA1 + 1):
    key(gbar, f, scale=(1, o2_level(f) / 21.0, 1))
interp(gbar, "LINEAR")
for f, (c_, g_) in ((1, ((0.12, 0.5, 1.0), 1.6)), (GA0 + 4, ((0.12, 0.5, 1.0), 1.6)), (GA0 + 18, ((1.0, 0.1, 0.04), 2.0))):
    em_ = hud_b.node_tree.nodes["Emission"]; em_.inputs["Color"].default_value = (*c_, 1); em_.inputs["Color"].keyframe_insert("default_value", frame=f)
    val_key(hud_b, "glow", f, g_)
lin(hud_b)
vis(hud, rng("fill", "o2", "gauge"))
for o in (timer, tlabel): vis(o, rng("fill"), recursive=False)
vis(gau, rng("o2", "gauge"))
def on_frame(scene, *a):
    f = scene.frame_current
    sec = int(300 * ease((f - FI0) / (FI1 - FI0 - 6)) ** 1.0) if f >= FI0 else 0
    timer.data.body = f"{sec // 60:02d}:{sec % 60:02d}"
    gpct.data.body = f"{o2_level(f):.0f}%"
bpy.app.handlers.frame_change_pre.append(on_frame)

# ======================================================================
# 5) RENTGEN: o'pka, traxeya, chiqayotgan gaz; miya
# ======================================================================
xr = empty("xr_grp", (0, 0, 0), mroot)                # root fazosi (yotgan holat: bosh +Y, ko'krak +Z)
lung_m = mat("lung", (0.8, 0.25, 0.3), 0.4, sss=0.4, sss_scale=0.004, emit=0.45, emit_col=(1.0, 0.3, 0.38), coat=0.5)
lungs = []
for sx in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=1); l = bpy.context.object; l.name = f"lung{sx}"
    for v in l.data.vertices:
        x, y, z = v.co
        k = 1 - 0.42 * max(0, z)                      # tepasi torayadi (mahalliy Z = umurtqa bo'ylab)
        v.co = (x * 0.046 * k + (0.01 * sx if z < 0 else 0), y * 0.045 * k, z * 0.09)
    for p in l.data.polygons: p.use_smooth = True
    l.data.materials.append(lung_m); noisy(l, 0.006, 0.03, sub=1)
    l.parent = xr; l.location = (sx * 0.06 + 0.01, 0.29, 1.075); l.rotation_euler = (R(-90), 0, 0)
    lungs.append(l)
EX0, EX1 = S["exhale"]; LU0, LU1 = S["lungs"]
for l in lungs:
    for f, s in ((1, 1.0), (EX0, 1.08), (EX0 + 12, 1.1), (EX0 + 34, 0.8), (LU0 + 6, 0.78), (LU0 + 26, 1.05), (LU1, 0.86)):
        key(l, f, scale=(s, s, 1 - (1 - s) * 0.5))
tr_m = P.xray_material("xray_tr", col=(0.7, 0.95, 1.0), strength=2.2, base=0.05)
CAR = Vector((0.01, 0.375, 1.075))
TRP = [CAR, Vector((0.012, 0.44, 1.08)), Vector((0.02, 0.5, 1.085)), Vector((0.06, 0.535, 1.095)), Vector((0.135, 0.537, 1.108))]
P.tube("trachea", [tuple(p) for p in TRP], 0.0085, tr_m, xr)
for sx in (-1, 1):
    P.tube(f"bronch{sx}", [tuple(CAR), (sx * 0.035 + 0.01, 0.35, 1.075), (sx * 0.062 + 0.01, 0.31, 1.075)], 0.006, tr_m, xr)
FZ = Vector((0.83, -0.09, 0.55))
puff_m = emis("puff", (0.7, 1.0, 0.12), 5.0)
rp = random.Random(5)
NPF, TRIP = 80, 40
for i in range(NPF):
    sx = rp.choice((-1, 1))
    st = Vector((sx * 0.068 + 0.01 + rp.uniform(-0.03, 0.03), 0.285 + rp.uniform(-0.07, 0.05), 1.075 + rp.uniform(-0.025, 0.025)))
    en = TRP[-1] + FZ * rp.uniform(0.1, 0.24) + Vector((rp.uniform(-1, 1), rp.uniform(-1, 1), rp.uniform(-1, 1))) * 0.045
    pts = [st, Vector((sx * 0.05 + 0.01, 0.33, 1.075)), CAR] + TRP[1:] + [en]
    seg = [(pts[k + 1] - pts[k]).length for k in range(len(pts) - 1)]; tot = sum(seg)
    def along(u):
        d = u * tot
        for k, s_ in enumerate(seg):
            if d <= s_: return pts[k].lerp(pts[k + 1], d / s_)
            d -= s_
        return pts[-1]
    p_ = sphere(f"puff{i}", rp.uniform(0.003, 0.0055), (0, 0, 0), puff_m, sub=1, parent=xr)
    f0 = EX0 + 10 + rp.uniform(0, TRIP)
    key(p_, 1, scale=0.0)
    while f0 < LU1 + 2:
        for j in range(0, TRIP + 1, 2):
            u = j / TRIP; f = f0 + j
            key(p_, f, loc=tuple(along(u ** 0.8)), scale=0.0 if j in (0, TRIP) else (1.0 if u < 0.85 else 1.5))
        f0 += TRIP + 1
    interp(p_, "LINEAR")
vis(xr, rng("exhale", "lungs"))

# miya (rentgen bosh ichida): "tox" 0..1 — pushti -> zaharli yashil
def brain_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Roughness"].default_value = 0.35
    gl = value_node(m, "glow", 1.0); tox = value_node(m, "tox", 0.0)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bc = N.new("ShaderNodeMix"); bc.data_type = "RGBA"; bc.inputs[6].default_value = (0.85, 0.5, 0.52, 1); bc.inputs[7].default_value = (0.3, 0.55, 0.1, 1)
    L.new(tox, bc.inputs["Factor"]); L.new(bc.outputs[2], b.inputs["Base Color"])
    ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; ec.inputs[6].default_value = (1.0, 0.5, 0.6, 1); ec.inputs[7].default_value = (0.45, 1.0, 0.08, 1)
    L.new(tox, ec.inputs["Factor"]); L.new(ec.outputs[2], b.inputs["Emission Color"])
    fl = P.math_n(N, L, "POWER", nz.outputs["Fac"], 3.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", fl, 0.2), gl), b.inputs["Emission Strength"])
    return m
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
xb_m = brain_mat("xbrain_m")
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, rng("brainx", "poison"))
BX0, BX1 = S["brainx"]; PO0, PO1 = S["poison"]
val_key(xb_m, "tox", 1, 0.0); val_key(xb_m, "glow", 1, 3.0)
for k, f in enumerate(range(BX0, BX1 + 1, 6)):
    t = (f - BX0) / (BX1 - BX0)
    val_key(xb_m, "glow", f, (1.8 if k % 2 == 0 else 0.7) * (1 - 0.6 * t)); val_key(xb_m, "tox", f, 0.45 * t)
val_key(xb_m, "tox", PO0 - 1, 0.45); val_key(xb_m, "tox", PO0, 0.75); val_key(xb_m, "tox", PO0 + 30, 1.0)
for k, f in enumerate(range(PO0, PO1 + 1, 7)):
    val_key(xb_m, "glow", f, 2.6 if k % 2 == 0 else 1.0)
lin(xb_m)

# ======================================================================
# 6) MOLEKULA MAKRO DUNYOSI (MM): "4%" va CO2
# ======================================================================
MM = Vector((60, 0, 0))
mm = empty("MM_grp", tuple(MM))
F40, F41 = S["four"]; C20, C21 = S["co2"]
txt_y = emis("txt_yel", (1.0, 0.78, 0.08), 1.8)
t4 = text("t_four", "4%", 2.6, (0, 2.2, 0.7), (90, 0, 0), txt_y, parent=mm, extrude=0.12)
key(t4, F40, scale=0.2); key(t4, F40 + 5, scale=1.12); key(t4, F40 + 8, scale=1.0); key(t4, F41, scale=1.06)
ZH = 361                                              # "zaharli"
for f, c_ in ((1, (1.0, 0.78, 0.08)), (ZH - 1, (1.0, 0.78, 0.08)), (ZH + 2, (0.35, 1.0, 0.08))):
    e_ = txt_y.node_tree.nodes["Emission"]; e_.inputs["Color"].default_value = (*c_, 1); e_.inputs["Color"].keyframe_insert("default_value", frame=f)
rm = random.Random(8); stream = empty("stream", (0, 0, 0), mm)
for i in range(34):
    o = mol(f"mm_co2_{i}", CO2_HI, stream, rm.uniform(0.2, 0.34))
    x = rm.uniform(-2.6, 2.6); z = rm.uniform(-3.6, 4.6); y0 = rm.uniform(-4, 16); v = rm.uniform(0.1, 0.19)
    if abs(x) < 0.9 and abs(z - 0.7) < 1.2: x += 1.6 * (1 if x > 0 else -1)
    key(o, F40, loc=(x, y0, z)); key(o, C21, loc=(x + rm.uniform(-0.6, 0.6), y0 - v * (C21 - F40), z + rm.uniform(-0.5, 0.5)))
    r0 = [rm.uniform(0, 6) for _ in range(3)]; o.rotation_euler = r0; o.keyframe_insert("rotation_euler", frame=F40)
    o.rotation_euler = [a + rm.uniform(-4, 4) for a in r0]; o.keyframe_insert("rotation_euler", frame=C21)
    interp(o, "LINEAR")
vis(stream, rng("four"))
vis(t4, rng("four"), recursive=False)
# qahramon molekula
MH = Vector((0, -40, 0))
hero_g = empty("hero_grp", tuple(MH), mm)
hero = mol("hero_co2", CO2_HI, hero_g, 0.62)
key(hero, C20, rot=(20, -15, 25)); key(hero, C21, rot=(38, 20, 75)); interp(hero, "LINEAR")
tco = text("t_co2", "CO₂", 1.15, (0, -0.3, -1.45), (90, 0, 0), emis("txt_grn", (0.4, 1.0, 0.08), 3.0), parent=hero_g, extrude=0.06)
key(tco, C20, scale=0.0); key(tco, C20 + 3, scale=0.0); key(tco, C20 + 8, scale=1.15); key(tco, C20 + 11, scale=1.0)
rh = random.Random(4)
for i in range(26):
    p = Vector((rh.uniform(-4.5, 4.5), rh.uniform(1.5, 12), rh.uniform(-5, 6)))
    o = mol(f"bg_co2_{i}", CO2_HI, hero_g, rh.uniform(0.16, 0.3), tuple(p))
    o.rotation_euler = [rh.uniform(0, 6) for _ in range(3)]; o.keyframe_insert("rotation_euler", frame=C20)
    o.rotation_euler = [a + rh.uniform(-2, 2) for a in o.rotation_euler]; o.keyframe_insert("rotation_euler", frame=C21)
    key(o, C20, loc=tuple(p)); key(o, C21, loc=tuple(p + Vector((rh.uniform(-0.5, 0.5), -rh.uniform(0.5, 2), rh.uniform(-0.4, 0.4)))))
    interp(o, "LINEAR")
vis(hero_g, rng("co2"))
plane("mm_back", (90, 60), (0, 26, 0), mat("mm_back_m", (0.012, 0.03, 0.035), 0.9, emit=0.05, emit_col=(0.1, 0.5, 0.4)), rot=(90, 0, 0), parent=mm)
plane("mh_back", (90, 60), (0, 22, 0), mat("mh_back_m", (0.02, 0.035, 0.02), 0.9, emit=0.06, emit_col=(0.3, 0.6, 0.1)), rot=(90, 0, 0), parent=hero_g)
vis(mm.children[-1] if False else bpy.data.objects["mm_back"], rng("four"), recursive=False)

# ======================================================================
# 7) QON TOMIRI (BV)
# ======================================================================
BV = Vector((90, 0, 0))
bv = empty("BV_grp", tuple(BV))
BL0, BL1 = S["blood"]
def vessel():
    bm = bmesh.new(); rings = []
    for j in range(140):
        y = -6 + j * 0.45; ring = []
        for i in range(36):
            a = 2 * math.pi * i / 36
            r = 1.25 + 0.09 * math.sin(3 * a + y * 0.7) + 0.06 * math.sin(y * 1.3 + a) + 0.04 * math.sin(7 * a - y * 2.1)
            ring.append(bm.verts.new((r * math.cos(a) + 0.25 * math.sin(y * 0.16), y, r * math.sin(a) + 0.18 * math.sin(y * 0.11))))
        rings.append(ring)
    for j in range(139):
        for i in range(36):
            f = bm.faces.new((rings[j][i], rings[j][(i + 1) % 36], rings[j + 1][(i + 1) % 36], rings[j + 1][i])); f.smooth = True
    me = bpy.data.meshes.new("vessel"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("vessel", me); sc.collection.objects.link(o); o.parent = bv
    return o
ves = vessel()
ves_m = bpy.data.materials.new("vessel_m"); ves_m.use_nodes = True
N = ves_m.node_tree.nodes; L = ves_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.3, 0.025, 0.025, 1); b.inputs["Roughness"].default_value = 0.4
b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.2; b.inputs["Coat Weight"].default_value = 0.5
tcv = N.new("ShaderNodeTexCoord"); nzv = N.new("ShaderNodeTexNoise"); nzv.inputs["Scale"].default_value = 2.5; nzv.inputs["Detail"].default_value = 5
L.new(tcv.outputs["Object"], nzv.inputs["Vector"]); bpv = N.new("ShaderNodeBump"); bpv.inputs["Strength"].default_value = 0.6
L.new(nzv.outputs["Fac"], bpv.inputs["Height"]); L.new(bpv.outputs["Normal"], b.inputs["Normal"])
b.inputs["Emission Color"].default_value = (0.5, 0.02, 0.02, 1); b.inputs["Emission Strength"].default_value = 0.03
ves.data.materials.append(ves_m)
rbc_m = bpy.data.materials.new("rbc"); rbc_m.use_nodes = True
N = rbc_m.node_tree.nodes; L = rbc_m.node_tree.links; b = N["Principled BSDF"]
deox = value_node(rbc_m, "deox", 0.0)
cmx = N.new("ShaderNodeMix"); cmx.data_type = "RGBA"; cmx.inputs[6].default_value = (0.85, 0.04, 0.03, 1); cmx.inputs[7].default_value = (0.2, 0.03, 0.32, 1)
L.new(deox, cmx.inputs["Factor"]); L.new(cmx.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.5
b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.05
b.inputs["Emission Color"].default_value = (1.0, 0.1, 0.05, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, deox), 0.5), b.inputs["Emission Strength"])
val_key(rbc_m, "deox", BL0, 0.0); val_key(rbc_m, "deox", BL0 + 12, 0.0); val_key(rbc_m, "deox", BL1 - 6, 1.0); lin(rbc_m)
bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=16, radius=1); rb0 = bpy.context.object
for v in rb0.data.vertices:
    r = math.hypot(v.co.x, v.co.y); v.co.z *= 0.16 + 0.26 * min(1.0, r / 0.8) ** 2
for p in rb0.data.polygons: p.use_smooth = True
rb0.data.materials.append(rbc_m); RB_ME = rb0.data; bpy.data.objects.remove(rb0)
o2dot_m = emis("o2dot", (0.1, 0.5, 1.0), 2.2)
rb_ = random.Random(21)
for i in range(110):
    a = rb_.uniform(0, 6.28); rr = rb_.uniform(0.48, 0.97)
    y0 = rb_.uniform(-5, 13); s = rb_.uniform(0.24, 0.33); v = rb_.uniform(0.2, 0.3)
    o = bpy.data.objects.new(f"rbc{i}", RB_ME); sc.collection.objects.link(o); o.parent = bv; o.scale = (s,) * 3
    key(o, BL0, loc=(rr * math.cos(a), y0, rr * math.sin(a))); key(o, BL1 + 1, loc=(rr * math.cos(a), y0 + v * (BL1 + 1 - BL0), rr * math.sin(a)))
    r0 = [rb_.uniform(0, 6) for _ in range(3)]; o.rotation_euler = r0; o.keyframe_insert("rotation_euler", frame=BL0)
    o.rotation_euler = [q + rb_.uniform(-3, 3) for q in r0]; o.keyframe_insert("rotation_euler", frame=BL1 + 1)
    interp(o, "LINEAR")
    for k in range(4):                                # kislorod nuqtalari: birin-ketin so'nadi
        ang = k * 1.57 + rb_.uniform(0, 1)
        d = sphere(f"o2d{i}_{k}", 0.16, (0.62 * math.cos(ang), 0.62 * math.sin(ang), 0.3 * (1 if k % 2 else -1)), o2dot_m, sub=1, parent=o)
        fo = BL0 + 10 + rb_.uniform(0, BL1 - BL0 - 22)
        key(d, BL0, scale=1.0); key(d, fo, scale=1.0); key(d, fo + 2, scale=1.5); key(d, fo + 5, scale=0.0)
vis(bv, rng("blood"))

# ======================================================================
# 8) NEYRONLAR (NW): bo'g'ilish
# ======================================================================
NW = Vector((120, 0, 0))
nw = empty("NW_grp")
CH0, CH1 = S["choke"]
def neuron_pulse(name, col, pcol, phase, period=30, base=0.5, width=0.08):
    m = P.pulse_material(name, col, base_emit=base, pulse_col=pcol, width=width)
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 0.5
    for n in m.node_tree.nodes:
        if n.type == "MATH" and n.operation == "MULTIPLY" and abs(n.inputs[1].default_value - 4.0) < 1e-6 and not n.inputs[1].links:
            n.inputs[1].default_value = 0.0
    f = CH0 - phase
    while f < CH1 + period:
        val_key(m, "pos", f, -0.15); val_key(m, "pos", f + period - 1, 1.15); f += period
    lin(m)
    return m
BLUE = [neuron_pulse(f"nrn{i}", (0.08, 0.22, 0.85), (0.15, 0.5, 1.0), i * 9, 22 + i * 5, base=0.5) for i in range(3)]
soma_m = mat("soma", (0.1, 0.25, 0.9), 0.35, sss=0.7, sss_scale=0.1, emit=1.5, emit_col=(0.12, 0.35, 1.0), coat=0.5)
def wander(p0, d, steps, step, rnd, wig=0.55):
    pts = [p0.copy()]; p = p0.copy(); d = d.normalized()
    for _ in range(steps):
        d = (d + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * wig).normalized()
        p = p + d * step; pts.append(p.copy())
    return pts
def taper(n, a=1.0, b=0.15): return [a + (b - a) * i / (n - 1) for i in range(n)]
def neuron(name, c, parent, seed, mats, smat, n_dend=6, axon=None, r=0.38, dl=(4, 6)):
    rnd = random.Random(seed); c = Vector(c)
    so = sphere(name + "_soma", r, tuple(c), smat, scale=(1.0, 0.85, 1.1), sub=4, parent=parent)
    so.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)); noisy(so, 0.08, 0.35)
    for k in range(n_dend):
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.8, 0.8))).normalized()
        pts = wander(c + d * r * 0.8, d, rnd.randint(*dl), 0.5, rnd)
        P.tube(f"{name}_d{k}", [tuple(p) for p in pts], 0.075, rnd.choice(mats), parent, taper=taper(len(pts), 1.0, 0.2))
        if len(pts) > 3:
            bd = (pts[3] - pts[2]).normalized() + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
            bp_ = wander(pts[2], bd, rnd.randint(2, 4), 0.4, rnd)
            P.tube(f"{name}_b{k}", [tuple(p) for p in bp_], 0.04, rnd.choice(mats), parent, taper=taper(len(bp_), 1.0, 0.25))
    if axon:
        pts = wander(c + Vector(axon).normalized() * r * 0.8, Vector(axon), 12, 0.7, rnd, wig=0.25)
        P.tube(f"{name}_ax", [tuple(p) for p in pts], 0.06, rnd.choice(mats), parent, taper=taper(len(pts), 1.0, 0.6))
    return so
neuron("N0", NW, nw, 1, BLUE, soma_m, n_dend=7, axon=(1, 0.3, -0.2))
for i, (p, ax) in enumerate([((-3.5, 2.5, 1.0), (1, -0.5, 0)), ((3.0, 3.0, -1.2), (-1, 0, 0.3)), ((-2.5, 5.5, -1.5), (1, 1, 0)),
                             ((4.5, 4.0, 1.8), (0, 1, 0)), ((0.5, 6.5, 2.4), (0, -1, -0.5)), ((-5, 6, 2.5), (1, 0, 0))]):
    neuron(f"N{i + 1}", NW + Vector(p), nw, 10 + i, BLUE, soma_m, n_dend=5, axon=ax)
rs2 = random.Random(2)
for i in range(22):                                    # neyronlar orasida suzib yurgan CO2
    p = NW + Vector((rs2.uniform(-4, 4), rs2.uniform(-2.5, 5), rs2.uniform(-2.5, 3)))
    o = mol(f"nw_co2_{i}", CO2_ME, nw, rs2.uniform(0.07, 0.12), tuple(p)); o.rotation_euler = [rs2.uniform(0, 6) for _ in range(3)]
    key(o, CH0, loc=tuple(p)); key(o, CH1, loc=tuple(p + Vector((rs2.uniform(-0.5, 0.5), rs2.uniform(-0.6, 0.2), rs2.uniform(-0.4, 0.4))))); interp(o, "LINEAR")
for m in BLUE + [soma_m]:
    tgt = m.node_tree.nodes["glow"].outputs[0] if "glow" in m.node_tree.nodes else m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    rk = random.Random(m.name)
    for f in range(CH0, CH1 + 1, 2):
        t = (f - CH0) / (CH1 - CH0)
        tgt.default_value = max(0.03, (1.4 - 1.3 * t) * (1.0 if rk.random() > 0.35 * (0.4 + t) else 0.1)); tgt.keyframe_insert("default_value", frame=f)
    for fc in fcurves(m.node_tree):
        for k in fc.keyframe_points:
            if "glow" in fc.data_path or "Emission" in fc.data_path or "inputs" in fc.data_path: k.interpolation = "CONSTANT"
vis(nw, rng("choke"))

# ======================================================================
# 9) OG'IZ MAKROSI (MO): qurib yorilgan til
# ======================================================================
MO = Vector((150, 0, 0))
mo = empty("MO_grp", tuple(MO))
def crack_mat(name, col, dark, scale=55.0, w=0.045, sss=0.2):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = scale
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    cr = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", vo.outputs["Distance"], w), clamp=True)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale * 6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    c0 = N.new("ShaderNodeMix"); c0.data_type = "RGBA"; c0.inputs[6].default_value = (*col, 1); c0.inputs[7].default_value = (*[min(1, c * 1.25) for c in col], 1)
    L.new(nz.outputs["Fac"], c0.inputs["Factor"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(cr, mx.inputs["Factor"]); L.new(c0.outputs[2], mx.inputs[6]); mx.inputs[7].default_value = (*dark, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.85
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.002
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 1.0; bp.inputs["Distance"].default_value = 0.002
    L.new(P.math_n(N, L, "MULTIPLY", cr, -1.0), bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
tongue_m = crack_mat("tongue", (0.62, 0.36, 0.33), (0.16, 0.03, 0.03), 70.0, 0.06)
lip_m = crack_mat("lip", (0.55, 0.27, 0.25), (0.22, 0.06, 0.05), 160.0, 0.07, sss=0.1)
skin_m = mat("mo_skin", (0.52, 0.3, 0.24), 0.55, sss=0.15, sss_scale=0.003)
tooth_m = mat("tooth", (0.85, 0.82, 0.72), 0.25, coat=0.5, sss=0.2, sss_scale=0.002)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=1); tg = bpy.context.object; tg.name = "tongue"
for v in tg.data.vertices:
    x, y, z = v.co
    z2 = z * (0.3 if z > 0 else 0.5) - 0.22 * math.exp(-(x * 3.2) ** 2) * (1 if z > 0 else 0) * 0.35
    v.co = (x * 0.025 * (1 - 0.25 * max(0, -y)), y * 0.036, z2 * 0.024)
for p in tg.data.polygons: p.use_smooth = True
tg.data.materials.append(tongue_m); tg.parent = mo; tg.location = (0, 0.027, -0.007)
def annulus(name, a, b_, rout, m, n=64):
    bm = bmesh.new(); inner = []; outer = []
    for i in range(n):
        t = 2 * math.pi * i / n
        inner.append(bm.verts.new((a * math.cos(t), 0, b_ * math.sin(t)))); outer.append(bm.verts.new((rout * math.cos(t), 0.02, rout * 1.4 * math.sin(t))))
    for i in range(n):
        f = bm.faces.new((inner[i], inner[(i + 1) % n], outer[(i + 1) % n], outer[i])); f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = mo; return o
annulus("mo_face", 0.031, 0.0225, 0.3, skin_m)
lips = torus("lips", 0.03, 0.0065, (0, -0.001, 0), lip_m, rot=(90, 0, 0), parent=mo); lips.scale = (1.0, 0.78, 1.25)
cav = sphere("cavity", 0.05, (0, 0.048, 0), mat("cavity_m", (0.05, 0.004, 0.004), 0.6), scale=(0.9, 1.0, 0.6), sub=4, parent=mo)
for sgn, zz in ((1, 0.0135), (-1, -0.0155)):
    for k in range(-4, 5):
        a = k * 0.19
        t_ = box(f"tooth{sgn}_{k}", (0.0052, 0.003, 0.0075), (0.024 * math.sin(a), 0.024 * (1 - math.cos(a)) * 0.7 + 0.006, zz), tooth_m, rot=(0, 0, -math.degrees(a) * 0.6), parent=mo, bevel=0.001)
vis(mo, rng("mouth"))

# ======================================================================
# 10) OG'RIQ HALQALARI, "10 SOAT"
# ======================================================================
AC0, AC1 = S["ache"]
pain_m = emis("pain", (1.0, 0.1, 0.04), 2.4)
painE = empty("painE", (0, 0.23, 0.0), headE)
for k in range(3):
    t_ = torus(f"pain{k}", 0.075, 0.0028, (0, 0, 0), pain_m, rot=(90, 0, 0), parent=painE)
    key(t_, 1, scale=0.0)
    f = AC0 + 4 + k * 5
    while f < AC1:
        key(t_, f, scale=0.0); key(t_, f + 1, scale=0.9); key(t_, f + 14, scale=1.9); key(t_, f + 15, scale=0.0); f += 16
    interp(t_, "LINEAR")
vis(painE, rng("ache"))
TE0, TE1 = S["ten"]
t10 = text("t_ten", "10 SOAT", 0.075, tuple(CLK + Vector((0, 0, 0.3))), (90, 0, 0), emis("txt_ten", (1.0, 0.85, 0.3), 3.0), extrude=0.004)
key(t10, TE0, scale=0.0); key(t10, TE0 + 8, scale=0.0); key(t10, TE0 + 13, scale=1.15); key(t10, TE0 + 16, scale=1.0)
vis(t10, rng("ten"), recursive=False)
SPIN = {"minute_hand": -360 * 10, "houd_hand": -300, "second_hand": -360 * 40}
for o in clock.children_recursive:
    pre = next((k for k in SPIN if o.name.startswith(k)), None)
    if not pre: continue
    o.rotation_mode = "XYZ"; r0 = o.rotation_euler.copy()
    o.keyframe_insert("rotation_euler", frame=TE0)
    o.rotation_euler = (r0.x, r0.y + R(SPIN[pre]), r0.z); o.keyframe_insert("rotation_euler", frame=TE1)
    interp(o, "LINEAR")

# ======================================================================
# 11) KAMERALAR
# ======================================================================
def cv(*p): return CV + Vector(p)
# 1 ILGAK: titrayotgan yuzga crash zoom
H0, H1 = S["hook"]
c = shot_cam("hook", (0, 0, 0), faceT, 20, 2.0, focus=faceT)
path_keys(c, [(H0, MEG_BED + Vector((0.95, 0.2, 1.42))), (H0 + 9, MEG_BED + Vector((0.5, 0.42, 1.27))), (H1, MEG_BED + Vector((0.4, 0.47, 1.24)))])
lens_keys(c, [(H0, 18), (H0 + 9, 30), (H1, 34)]); shake(c, H0 + 8, H0 + 22, 0.012, seed=2)
# 2 ko'rpa boshga yopiladi: tepadan aylanib tushuvchi kran
cvT = at("coverT", MEG_BED + Vector((0, 0.45, 1.15)))
c = shot_cam("cover", (0, 0, 0), cvT, 14, 4.0, focus=cvT)
orbit(c, CV0, CV1, MEG_BED + Vector((0.25, 0.3, 0)), 1.5, 1.0, 50, 115, 2.85, 2.5)
shake(c, CV0 + 24, CV0 + 36, 0.012, seed=3)
# 3 issiq va xavfsiz: g'or ichida yuzga sekin yaqinlashish
CZ0, CZ1 = S["cozy"]
c = shot_cam("cozy", (0, 0, 0), faceT, 24, 2.2, focus=faceT, clip=0.001)
path_keys(c, [(CZ0, cv(0.33, 0.36, MT + 0.36)), (CZ1, cv(0.31, 0.47, MT + 0.3))]); lens_keys(c, [(CZ0, 22), (CZ1, 28)])
# 4 chiqindi gaz: yuzdan orqaga keskin chekinish (qiya kadr)
c = shot_cam("wasteA", (0, 0, 0), noseT, 24, 3.2, focus=noseT, clip=0.001)
path_keys(c, [(WA0, cv(0.33, 0.5, MT + 0.26)), (WA0 + 8, cv(0.62, 0.42, MT + 0.36)), (WA1, cv(0.86, 0.3, MT + 0.42))])
lens_keys(c, [(WA0, 30), (WA0 + 8, 24), (WA1, 26)]); shake(c, WA0 + 6, WA0 + 20, 0.012, seed=5)
# 5 burun oldida: gaz chiqib yana ichkariga tortiladi (makro aylanma)
wbT = at("wasteBT", cv(*(NP + Vector((0.03, 0.0, 0.01)))))
c = shot_cam("wasteB", (0, 0, 0), wbT, 50, 8.0, focus=wbT, clip=0.001)
path_keys(c, [(WB0, cv(0.5, 0.36, MT + 0.24)), (WB0 + 27, cv(0.52, 0.53, MT + 0.33)), (WB1, cv(0.48, 0.7, MT + 0.27))])
# 6 rentgen: ko'krak ustidan o'pkaga yaqinlashish
chT = at("chestT", MEG_CV + Vector((0.01, 0.3, 1.07)))
c = shot_cam("exhale", (0, 0, 0), chT, 28, 4.0, focus=chT, clip=0.001)
path_keys(c, [(EX0, MEG_CV + Vector((0.55, -0.05, 1.85))), (EX1, MEG_CV + Vector((0.38, 0.1, 1.6)))])
# 7 traxeya bo'ylab og'izgacha ergashish
luT = empty("lungsT"); path_keys(luT, [(LU0, MEG_CV + Vector((0.01, 0.36, 1.08))), (LU1, MEG_CV + Vector((0.14, 0.54, 1.12)))])
c = shot_cam("lungs", (0, 0, 0), luT, 35, 4.0, focus=luT, clip=0.001)
path_keys(c, [(LU0, MEG_CV + Vector((0.42, 0.2, 1.42))), (LU1, MEG_CV + Vector((0.47, 0.5, 1.3)))])
# 8 "4%": molekulalar oqimi ichidan matnga
f4T = at("fourT", MM + Vector((0, 2.2, 0.7)))
c = shot_cam("four", (0, 0, 0), f4T, 24, 5.6, focus=f4T)
path_keys(c, [(F40, MM + Vector((1.6, -9.5, -0.6))), (F40 + 6, MM + Vector((1.0, -7.2, -0.2))), (ZH, MM + Vector((0.2, -6.4, 0.2))),
              (ZH + 4, MM + Vector((-0.2, -5.0, 0.3))), (F41, MM + Vector((-0.6, -4.6, 0.4)))])
shake(c, ZH, ZH + 12, 0.07, seed=6)
# 9 CO2 molekulasi atrofida past aylanma
hT = at("heroT", MM + MH + Vector((0, 0, -0.45)))
c = shot_cam("co2", (0, 0, 0), hT, 26, 5.6, focus=at("heroF", MM + MH))
orbit(c, C20, C21, MM + MH, 5.6, 4.3, -28, 24, -1.6, -0.9)
# 10 kichik bo'shliq: kesim bo'ylab yonlama surilish
caT = at("caveT", cv(0, 0.62, MT + 0.2))
c = shot_cam("cave", (0, 0, 0), caT, 30, 5.6, focus=caT)
path_keys(c, [(S["cave"][0], cv(1.75, -0.25, MT + 0.5)), (S["cave"][1], cv(1.45, 0.7, MT + 0.36))])
# 11 gaz chiqib ketolmaydi: ichkaridan shiftga qarab (past burchak, keng)
boT = at("bounceT", cv(0.1, 0.72, MT + 0.42))
c = shot_cam("bounce", (0, 0, 0), boT, 16, 4.0, focus=boT, clip=0.001)
path_keys(c, [(BO0, cv(0.33, 0.33, MT + 0.14)), (BO1, cv(0.3, 0.4, MT + 0.17))])
shake(c, BO0 + 8, BO1 - 4, 0.004, seed=7, decay=False)
# 12 sanoqli daqiqalarda yig'iladi: kesim atrofida aylanma, taymer
fiT = at("fillT", cv(0.1, 0.5, MT + 0.46))
c = shot_cam("fill", (0, 0, 0), fiT, 26, 5.6, focus=fiT)
orbit(c, FI0, FI1, cv(0.1, 0.5, 0), 1.75, 1.45, 62, 104, MT + 0.75, MT + 0.5)
# 13 kislorod yo'qoladi: bo'shliqqa yaqinlashish
oxT = at("o2T", cv(0.1, 0.5, MT + 0.46))
c = shot_cam("o2", (0, 0, 0), oxT, 32, 5.6, focus=oxT)
path_keys(c, [(OX0, cv(1.95, 0.8, MT + 0.5)), (OX1, cv(1.5, 0.5, MT + 0.5))])
# 14 keskin tushadi: o'lchagichga crash zoom + silkinish
gaT = at("gaugeT", cv(CUTX, 0.5, MT + 0.7))
c = shot_cam("gauge", (0, 0, 0), gaT, 30, 5.6, focus=gaT)
path_keys(c, [(GA0, cv(2.3, 0.75, MT + 0.5)), (GA0 + 6, cv(1.65, 0.58, MT + 0.64)), (GA1, cv(1.5, 0.54, MT + 0.66))])
lens_keys(c, [(GA0, 24), (GA0 + 6, 32), (GA1, 34)]); shake(c, GA0 + 6, GA1, 0.014, seed=8, decay=False)
# 15 qon tomiri ichida uchish
c = shot_cam("blood", (0, 0, 0), None, 16, 2.8, focus=3.0)
c.rotation_euler = (R(90), 0, 0)
for f in range(BL0, BL1 + 2, 4):
    y = 1.0 + 0.12 * (f - BL0)
    key(c, f, loc=tuple(BV + Vector((0.0, y, 0.0))),
        rot=(90 + 3 * math.sin(f * 0.1), 6 * math.sin(f * 0.07), -4 + 3 * math.sin(f * 0.05)))
point("bv_l1", (0, 0, 0.3), 0.2, (1.0, 0.85, 0.8), [(BL0, 14), (BL1, 10)], const=False, parent=c)
point("bv_l2", (0.3, 0.3, -5), 0.4, (1.0, 0.6, 0.55), [(BL0, 70), (BL1, 45)], const=False, parent=c)
# 16 rentgen bosh: miya atrofida aylanma
bxT = at("brainxT", cv(*(HC + Vector((0, 0.02, 0.01)))))
c = shot_cam("brainx", (0, 0, 0), bxT, 35, 3.2, focus=bxT, clip=0.001)
orbit(c, BX0, BX1, cv(HC.x, HC.y, 0), 0.6, 0.42, 65, 112, MT + 0.4, MT + 0.3)
# 17 bo'g'ilish: neyronlarga crash zoom + silkinish
chkT = at("chokeT", NW + Vector((0, 0.3, 0.1)))
c = shot_cam("choke", (0, 0, 0), chkT, 18, 3.5, focus=chkT)
path_keys(c, [(CH0, NW + Vector((-2.2, -6.5, 1.6))), (CH0 + 7, NW + Vector((-1.4, -4.3, 1.0))), (CH1, NW + Vector((-0.8, -3.5, 0.7)))])
lens_keys(c, [(CH0, 18), (CH0 + 7, 28), (CH1, 32)]); shake(c, CH0 + 6, CH1, 0.045, seed=12, decay=False)
# 18 ertalab: past burchak, keng, tez yaqinlashish
WK0, WK1 = S["wake"]
wkT = at("wakeT", SIT + Vector((0.12, 0, 1.0)))
c = shot_cam("wake", (0, 0, 0), wkT, 17, 4.0, focus=wkT)
path_keys(c, [(WK0, SIT + Vector((2.3, -0.9, 0.3))), (WK1, SIT + Vector((1.55, -0.55, 0.42)))])
# 19 bosh og'rig'i: yuzga crash zoom
c = shot_cam("ache", (0, 0, 0), faceT, 24, 2.2, focus=faceT)
path_keys(c, [(AC0, SIT + Vector((1.3, -0.4, 0.95))), (AC0 + 7, SIT + Vector((0.78, -0.16, 1.08))), (AC1, SIT + Vector((0.66, -0.08, 1.1)))])
lens_keys(c, [(AC0, 22), (AC0 + 7, 40), (AC1, 46)]); shake(c, AC0 + 6, AC1, 0.008, seed=3, decay=False)
# 20 og'iz qurishi: makro, ichkariga
MU0, MU1 = S["mouth"]
moT = at("mouthT", MO + Vector((0, 0.02, -0.004)))
c = shot_cam("mouth", (0, 0, 0), moT, 50, 11.0, focus=moT, clip=0.001)
path_keys(c, [(MU0, MO + Vector((0.05, -0.34, 0.04))), (MU1, MO + Vector((-0.015, -0.17, 0.015)))])
# 21 10 soat: soat atrofida aylanma (time-lapse)
clT = at("clockT", CLK + Vector((0, 0, 0.13)))
c = shot_cam("ten", (0, 0, 0), clT, 28, 3.2, focus=clT)
orbit(c, TE0, TE1, CLK + Vector((0, 0, 0)), 0.78, 0.6, 50, 100, 0.2, 0.26)
tc_ = t10.constraints.new("COPY_ROTATION"); tc_.target = c
# 22 kaltaklangandek: past burchakdan keng aylanma
BE0, BE1 = S["beaten"]
beT = at("beatenT", SIT + Vector((0.28, -0.05, 0.72)))
c = shot_cam("beaten", (0, 0, 0), beT, 17, 4.0, focus=beT)
orbit(c, BE0, BE1, SIT + Vector((0.2, 0, 0)), 1.75, 1.35, 48, 100, 0.22, 0.4)
# 23 asl sababi: peshonaga crash zoom
PU0, PU1 = S["push"]
c = shot_cam("push", (0, 0, 0), browT, 28, 2.4, focus=browT)
path_keys(c, [(PU0, SIT + Vector((1.5, -0.25, 0.35))), (PU1 - 8, SIT + Vector((1.0, -0.12, 0.42))), (PU1, SIT + Vector((0.88, -0.1, 0.45)))])
lens_keys(c, [(PU0, 26), (PU1 - 8, 34), (PU1, 52)])
# 24 zaharlangan miya: boshdan orqaga chekinish
poT = at("poisonT", cv(*(HC + Vector((0, -0.03, 0.03)))))
c = shot_cam("poison", (0, 0, 0), poT, 35, 4.0, focus=poT, clip=0.001)
path_keys(c, [(PO0, cv(0.62, 0.74, MT + 0.3)), (PO0 + 30, cv(0.9, 0.56, MT + 0.42)), (PO1, cv(1.9, 0.1, MT + 0.75))])
lens_keys(c, [(PO0, 40), (PO1, 30)])
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
# 12) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.006, 0.012, 0.03, 1)
WL = {"hook": 0.25, "cover": 0.3, "wake": 1.0, "ache": 1.0, "ten": 0.6, "beaten": 1.0, "push": 1.0, "four": 0.5, "co2": 0.5, "blood": 0.0,
      "choke": 0.4, "mouth": 0.3}
for f, n in SHOTS:
    bg.inputs[1].default_value = WL.get(n, 0.5); bg.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# kun / tun (deraza)
sun = area("sun", (0.6, Y0 - 1.0, 2.5), 1.2, (1.0, 0.86, 0.68), [(1, 0)], shape=(1.2, 1.0), const=False)
sunT = empty("sunT", (-0.9, 0.1, 0.8)); tr_ = sun.constraints.new("TRACK_TO"); tr_.target = sunT; tr_.track_axis = "TRACK_NEGATIVE_Z"; tr_.up_axis = "UP_Y"
def daykey(f, d):
    val_key(sky_m, "day", f, d); sun.data.energy = 2600 * d; sun.data.keyframe_insert("energy", frame=f)
daykey(1, 0.0); daykey(WK0 - 1, 0.0); daykey(WK0, 1.0); daykey(TE0 - 1, 1.0); daykey(TE0, 0.0); daykey(TE0 + 6, 0.0); daykey(TE1 - 4, 1.0); daykey(END, 1.0)
for idb in (sun.data, sky_m.node_tree):
    for fc in fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT" if k.co.x in (WK0 - 1, TE0 - 1) else "LINEAR"
bedT = at("bedT", MEG_BED + Vector((0, 0.5, 1.1)))
area("moon_bed", (0.6, Y0 + 0.1, 2.2), 1.0, (0.45, 0.6, 1.0), lights_for(rng("hook", "cover"), 110.0) + [(TE0, 110), (TE1 - 6, 0)], target=bedT)
area("hook_rim", tuple(MEG_BED + Vector((-0.5, 1.0, 1.9))), 0.5, (0.5, 0.7, 1.0), lights_for(rng("hook", "cover"), 14.0), target=faceT)
area("hook_key", tuple(MEG_BED + Vector((0.9, 0.0, 1.7))), 0.6, (0.6, 0.75, 1.0), lights_for(rng("hook"), 9.0), target=faceT)
area("room_fill", (0.0, 0.4, 2.45), 2.0, (0.5, 0.6, 0.9), lights_for(rng("hook", "cover"), 22.0), target=at("rfT", (-0.6, 0.2, 0.5)))
area("morn_fill", (0.6, 0.2, 2.45), 2.2, (1.0, 0.92, 0.82), lights_for(MORN, 190.0) + [(TE0, 0), (TE1 - 4, 150), (TE1 + 1, 0)], target=at("mfT", (-0.7, 0.0, 0.6)), const=False)
for fc in fcurves(bpy.data.lights["morn_fill"]):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if TE0 <= k.co.x < TE1 - 4 else "CONSTANT"
area("morn_face", tuple(SIT + Vector((1.6, -0.9, 1.5))), 0.8, (1.0, 0.9, 0.8), lights_for(MORN, 28.0), target=wkT)
area("ache_red", tuple(SIT + Vector((0.6, 0.7, 1.7))), 0.6, (1.0, 0.08, 0.04), lights_for(rng("ache"), 18.0), target=faceT)
point("clock_glow", tuple(CLK + Vector((0.3, -0.35, 0.25))), 0.06, (1.0, 0.85, 0.6), lights_for(rng("ten"), 7.0))
# g'or
INL = cv(0.27, 0.6, MT + 0.36)
point("cv_warm", tuple(INL), 0.04, (1.0, 0.62, 0.3), lights_for(rng("cozy"), 1.6) + [(WA0, 1.6), (WA0 + 10, 0.25), (WA1 + 1, 0)], const=False)
point("cv_green", tuple(INL), 0.04, (0.5, 1.0, 0.2), [(1, 0), (WA0, 0), (WA0 + 10, 1.5), (WB1, 1.5), (WB1 + 1, 0), (BO0, 1.2), (BO1 + 1, 0)], const=False)
for l_ in ("cv_warm", "cv_green"):
    for fc in fcurves(bpy.data.lights[l_]):
        for k in fc.keyframe_points: k.interpolation = "LINEAR" if WA0 <= k.co.x < WA0 + 10 else "CONSTANT"
WIDE = rng("cave", "fill", "o2", "gauge")
area("cv_key", tuple(cv(1.8, -0.4, MT + 1.5)), 1.2, (0.6, 0.75, 1.0), lights_for(WIDE, 90.0) + [(BX0, 14), (BX1 + 1, 0), (PO0, 22), (PO1 - 14, 22), (PO1, 2)], target=caT)
area("cv_rim", tuple(cv(-0.3, 1.2, MT + 1.6)), 1.0, (0.4, 0.55, 1.0), lights_for(WIDE, 70.0), target=caT)
point("cv_in", tuple(INL), 0.05, (1.0, 0.72, 0.45), lights_for(WIDE, 1.1) + [(GA0 + 6, 0.2)])
point("cv_red", tuple(INL), 0.05, (1.0, 0.1, 0.04), [(1, 0), (BO0, 0.5), (BO1 + 1, 0), (GA0 + 6, 1.6), (GA1 + 1, 0)])
# rentgen
area("X_rim", tuple(MEG_CV + Vector((-0.8, 0.9, 1.9))), 0.8, (0.3, 0.6, 1.0), lights_for(XRAY, 30.0), target=chT)
# molekula dunyosi
m4T = at("m4T", MM + Vector((0, 1, 0)))
area("MM_key", tuple(MM + Vector((-5, -7, 6))), 4.0, (1.0, 0.95, 0.9), lights_for(rng("four"), 2600.0), target=m4T)
area("MM_rim", tuple(MM + Vector((5, 8, 3))), 4.0, (0.3, 0.9, 0.7), lights_for(rng("four"), 2200.0), target=m4T)
area("MM_tox", tuple(MM + Vector((3, -5, -4))), 3.0, (0.35, 1.0, 0.08), [(1, 0), (ZH, 3500.0), (F41 + 1, 0)], target=m4T)
area("MH_key", tuple(MM + MH + Vector((-4, -5, 5))), 3.0, (1.0, 0.95, 0.9), lights_for(rng("co2"), 1500.0), target=hT)
area("MH_rim", tuple(MM + MH + Vector((4, 5, -2))), 3.0, (0.35, 1.0, 0.1), lights_for(rng("co2"), 2400.0), target=hT)
area("MH_rim2", tuple(MM + MH + Vector((-5, 3, -3))), 3.0, (0.6, 0.2, 1.0), lights_for(rng("co2"), 900.0), target=hT)
# neyronlar
n0T = at("n0T", NW)
area("NW_key", tuple(NW + Vector((-3, -3, 5))), 3.0, (0.75, 0.88, 1.0), [(1, 0), (CH0, 800), (CH0 + 8, 250), (CH1 + 1, 0)], target=n0T)
area("NW_rim", tuple(NW + Vector((3, 4, 2))), 3.0, (0.2, 0.5, 1.0), lights_for(rng("choke"), 700.0), target=n0T)
area("NW_red", tuple(NW + Vector((-3, -2, 4))), 3.0, (1.0, 0.06, 0.03), [(1, 0), (CH0 + 6, 6000), (CH1 + 1, 0)], target=n0T)
# og'iz
area("MO_key", tuple(MO + Vector((0.12, -0.3, 0.2))), 0.2, (1.0, 0.95, 0.9), lights_for(rng("mouth"), 1.3), target=moT)
area("MO_fill", tuple(MO + Vector((-0.15, -0.25, -0.05))), 0.2, (1.0, 0.8, 0.7), lights_for(rng("mouth"), 0.4), target=moT)

# ======================================================================
# 13) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
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
