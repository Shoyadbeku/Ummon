# Hiqichoq qanday paydo bo'ladi — Zack D. Films uslubida 40 s video (960 kadr, 24 fps, 9:16).
# Asos: zack_test/muzlash/muzlash.py, burish/parts.py, mixchar.py. Kadr rejasi: STORYBOARD.md
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=45 /tmp/claude-0/bvenv/bin/python -I zack_test/hiqichoq/hiqichoq.py --render
# Sinov: FRAMES=12,140,250,400,730 PCT=35
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix
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
END = 960
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (47, "face"), (105, "xlungs"), (134, "xdia"), (216, "breath"), (280, "air"), (323, "eat"),
         (380, "soda"), (426, "nerve"), (497, "spasm"), (576, "gulp"), (631, "xthroat"), (676, "glottis"),
         (741, "impact"), (783, "hik"), (845, "outro")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM_SHOTS = rng("hook", "face", "eat", "soda", "gulp", "hik", "outro")
XRAY_SHOTS = rng("xlungs", "xdia", "nerve", "xthroat")
STUDIO_SHOTS = rng("breath", "air", "spasm")
THROAT_SHOTS = rng("glottis", "impact")
SPASM = 543            # "birdan" (22.6 s)
CLOSE = 728            # "yopiladi" (30.28 s)
IMPACT = 758           # "urilib" (31.6 s)

# ---------------- yordamchilar (muzlash.py dan) ----------------
empty = P.empty
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
    for x in objs:
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, sss_scale=None, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if sss_scale is not None: b.inputs["Subsurface Scale"].default_value = sss_scale
    if emit or ecol:
        b.inputs["Emission Color"].default_value = (*(ecol or col), 1); b.inputs["Emission Strength"].default_value = emit
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

WORLD_PARENTS = {"room", "throat"}
def _par(o, parent):
    o.parent = parent
    if parent.name in WORLD_PARENTS:
        bpy.context.view_layer.update(); o.matrix_parent_inverse = parent.matrix_world.inverted()

def box(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if parent: _par(o, parent)
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: _par(o, parent)
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: _par(o, parent)
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if parent: _par(o, parent)
    return o

def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.005):
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
    for f in range(f0, f1):
        k = amp * ((1 - (f - f0) / (f1 - f0)) ** 2 if decay else 1.0)
        cam.delta_location = Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("delta_location", frame=f)
    cam.delta_location = (0, 0, 0); cam.keyframe_insert("delta_location", frame=f1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def path_keys(cam, pts):
    for f, p in pts: key(cam, f, loc=p)

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def area(name, loc, size, col, keys, target=None, parent=None, shape=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, parent=None, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

val_key = P.mat_value
def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]

def glow_mat(name, col, ecol, rough=0.4, sss=0.0, base_glow=0.0, coat=0.3, bump=0.0, bscale=30.0, vor=False):
    """Organ materiali: 'glow' qiymati (keyframe) emissiya kuchini boshqaradi."""
    m = mat(name, col, rough, sss=sss, sss_scale=0.01, coat=coat, ecol=ecol)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    L.new(value_node(m, "glow", base_glow), b.inputs["Emission Strength"])
    if bump:
        tc = N.new("ShaderNodeTexCoord")
        t = N.new("ShaderNodeTexVoronoi" if vor else "ShaderNodeTexNoise"); t.inputs["Scale"].default_value = bscale
        L.new(tc.outputs["Object"], t.inputs[0])
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.002
        L.new(t.outputs["Distance" if vor else "Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def scale_vis(o, f0, f1):
    """kichik ob'ektlar uchun: f0..f1 da ko'rinadi (masshtab 0 <-> 1, CONSTANT)"""
    s0 = o.scale.copy()
    o.scale = (0.0001,) * 3; o.keyframe_insert("scale", frame=1); o.keyframe_insert("scale", frame=f1 + 1)
    o.scale = s0; o.keyframe_insert("scale", frame=f0)
    interp(o, "CONSTANT", "scale")

def polyline(pts, t):
    """pts bo'ylab t (0..1) dagi nuqta (uzunlik bo'yicha)"""
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]; tot = sum(seg); d = t * tot
    for i, s in enumerate(seg):
        if d <= s or i == len(seg) - 1:
            return pts[i].lerp(pts[i + 1], min(1.0, d / s if s else 0))
        d -= s

def flow(name, paths, n, f0, f1, dur, m, parent, r, seed=1, jitter=0.0):
    """havo zarralari: har biri tasodifiy yo'l bo'ylab 'dur' kadrda o'tadi"""
    rp = random.Random(seed); out = []
    for i in range(n):
        pts = [Vector(p) for p in rp.choice(paths)]
        off = Vector((rp.uniform(-1, 1), rp.uniform(-1, 1), rp.uniform(-1, 1))) * jitter
        s = sphere(f"{name}{i}", r * rp.uniform(0.6, 1.2), tuple(pts[0]), m, scale=(1, 1, 1.8), sub=1)
        s.parent = parent
        a = f0 + int((f1 - f0 - dur) * i / max(1, n - 1)) if f1 - f0 > dur else f0
        a += rp.randint(-2, 2); b = a + dur
        for f in range(a, b + 1, 2):
            p = polyline(pts, (f - a) / dur) + off * min(1.0, (f - a) / 6)
            s.location = p; s.keyframe_insert("location", frame=f)
        nxt = polyline(pts, min(1, 0.05 + (1 / dur)))
        s.rotation_euler = Vector((0, 0, 1)).rotation_difference(pts[0] - pts[-1]).to_euler(); s.keyframe_insert("rotation_euler", frame=a)
        scale_vis(s, max(1, a), b)
        out.append(s)
    return out

# ======================================================================
# 1) MEHMONXONA (0,0,0)
# ======================================================================
room = empty("room", (0, 0, 0))
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.5, tint=(0.93, 0.86, 0.76))
plane("floor", (9, 9), (0, 0, 0), floor_m, parent=room)
WY = 2.55                                                 # orqa devor
# orqa devor deraza bilan (deraza x 0.55..2.05, z 0.85..2.3)
box("wb_l", (4.0, 0.12, 2.9), (-1.45, WY, 1.45), wall_m, parent=room)
box("wb_r", (1.4, 0.12, 2.9), (2.75, WY, 1.45), wall_m, parent=room)
box("wb_b", (1.5, 0.12, 0.85), (1.3, WY, 0.425), wall_m, parent=room)
box("wb_t", (1.5, 0.12, 0.6), (1.3, WY, 2.6), wall_m, parent=room)
frame_m = mat("winframe", (0.92, 0.92, 0.9), 0.35)
for (sx, sz, x, z) in ((1.56, 0.07, 1.3, 0.85), (1.56, 0.07, 1.3, 2.3), (0.07, 1.5, 0.55, 1.575), (0.07, 1.5, 2.05, 1.575),
                       (0.05, 1.5, 1.3, 1.575), (1.56, 0.05, 1.3, 1.6)):
    box("wframe", (sx, 0.09, sz), (x, WY - 0.02, z), frame_m, parent=room)
box("sill", (1.7, 0.25, 0.05), (1.3, WY - 0.1, 0.83), frame_m, parent=room)
glass = mat("glass", (0.9, 0.95, 1.0), 0.02, trans=1.0)
box("glass", (1.5, 0.01, 1.45), (1.3, WY, 1.575), glass, parent=room)
box("w_left", (0.12, 7, 2.9), (-3.4, -0.9, 1.45), wall_m, parent=room)
box("w_right", (0.12, 7, 2.9), (3.4, -0.9, 1.45), wall_m, parent=room)
plane("ceiling", (7, 7), (0, -0.9, 2.9), mat("ceil", (0.92, 0.9, 0.86), 0.8), rot=(180, 0, 0), parent=room)
box("skirting", (6.8, 0.03, 0.09), (0, WY - 0.07, 0.045), frame_m, parent=room)
# gilam
rug = bpy.data.materials.new("rug"); rug.use_nodes = True
N = rug.node_tree.nodes; L = rug.node_tree.links; rb = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; L.new(tc.outputs["Object"], wv.inputs[0])
cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.55, 0.16, 0.1, 1); cr.color_ramp.elements[1].color = (0.85, 0.7, 0.5, 1)
L.new(cr.outputs[0], rb.inputs["Base Color"]); rb.inputs["Roughness"].default_value = 0.95
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 400; L.new(tc.outputs["Object"], nz.inputs[0])
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], rb.inputs["Normal"])
box("rug", (2.6, 1.8, 0.012), (0.1, -0.2, 0.006), rug, parent=room)
# Poly Haven mebel
def ph_model(name, loc, rotz=0, scale=1.0):
    e = empty(name, loc, room); e.rotation_euler = (0, 0, R(rotz)); e.scale = (scale,) * 3
    objs = import_gltf(PH + f"{name}/{name}.gltf", e)
    lo, hi = bbox(objs); print("BBOX", name, tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
    return e, objs
sofa, _ = ph_model("Sofa_01", (-0.25, 1.95, 0), 0)
table, tobjs = ph_model("modern_coffee_table_01", (-0.95, -0.75, 0), 90)
TT = bbox(tobjs)[1].z                                    # stol usti balandligi
ph_model("potted_plant_01", (-2.6, 2.0, 0), 0, 1.5)
ph_model("potted_plant_01", (2.7, 1.9, 0), 40, 1.2)
pic, _ = ph_model("fancy_picture_frame_01", (-1.2, WY - 0.07, 1.55), 0, 1.4)
pic.rotation_euler = (R(90), 0, 0)

# burger (procedural) stol ustida
BG = Vector((-0.62, -0.9, TT))
bun_m = mat("bun", (0.78, 0.45, 0.16), 0.45, sss=0.3, sss_scale=0.005, coat=0.4)
plate_m = mat("plate", (0.95, 0.95, 0.93), 0.15, coat=0.6)
cyl("plate", 0.13, 0.012, tuple(BG + Vector((0, 0, 0.006))), plate_m, parent=room, verts=48)
burger = empty("burger", tuple(BG + Vector((0, 0, 0.012))), room)
def bpart(name, r, h, z, m, disp=0.0, sq=1.0):
    o = sphere(name, r, (0, 0, z), m, scale=(1, 1, h / r), sub=4); o.parent = burger
    if disp:
        tx = bpy.data.textures.new(name + "_t", "CLOUDS"); tx.noise_scale = 0.02
        d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = disp
    return o
bpart("bun_b", 0.058, 0.018, 0.016, bun_m)
bpart("patty", 0.062, 0.014, 0.038, mat("patty", (0.2, 0.09, 0.04), 0.7), disp=0.006)
ch = box("cheese", (0.11, 0.11, 0.005), (0, 0, 0.053), mat("cheese", (1.0, 0.68, 0.1), 0.3, sss=0.5, sss_scale=0.005), rot=(0, 0, 30)); ch.parent = burger
bpart("lettuce", 0.068, 0.008, 0.06, mat("lettuce", (0.25, 0.6, 0.12), 0.5, sss=0.4, sss_scale=0.005), disp=0.008)
bpart("tomato", 0.05, 0.007, 0.068, mat("tomato", (0.8, 0.08, 0.04), 0.25, coat=0.6))
top = bpart("bun_t", 0.06, 0.04, 0.074, bun_m)
seed_m = mat("sesame", (0.95, 0.88, 0.7), 0.5)
rs = random.Random(5)
for i in range(26):
    u = rs.uniform(0, 2 * math.pi); v = rs.uniform(0.15, 1.1)
    n = Vector((math.sin(v) * math.cos(u), math.sin(v) * math.sin(u), math.cos(v)))
    p = Vector((n.x * 0.06, n.y * 0.06, 0.074 + n.z * 0.04))
    s_ = sphere("sesame", 0.004, tuple(p), seed_m, scale=(1, 0.5, 0.35), sub=1); s_.parent = burger
    s_.rotation_euler = Vector((0, 0, 1)).rotation_difference(n).to_euler(); s_.rotation_euler.z += u
burger.rotation_euler = (0, 0, R(20))
# ikkinchi banka va kartoshka qopchasi
def can_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"; wv.inputs["Scale"].default_value = 1.2
    wv.inputs["Distortion"].default_value = 6.0; L.new(tc.outputs["Generated"], wv.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.72; L.new(wv.outputs["Fac"], gt.inputs[0])
    band = N.new("ShaderNodeMapRange"); band.interpolation_type = "STEPPED"; band.inputs["Steps"].default_value = 1
    L.new(sep.outputs["Z"], band.inputs["Value"]); band.inputs["From Min"].default_value = 0.08; band.inputs["From Max"].default_value = 1.84
    lid = N.new("ShaderNodeMath"); lid.operation = "LESS_THAN"; lid.inputs[1].default_value = 0.5; L.new(band.outputs[0], lid.inputs[0])
    lid2 = N.new("ShaderNodeMath"); lid2.operation = "LESS_THAN"; lid2.inputs[1].default_value = 0.08; L.new(sep.outputs["Z"], lid2.inputs[0])
    lid3 = N.new("ShaderNodeMath"); lid3.operation = "GREATER_THAN"; lid3.inputs[1].default_value = 0.92; L.new(sep.outputs["Z"], lid3.inputs[0])
    metal = N.new("ShaderNodeMath"); metal.operation = "MAXIMUM"; L.new(lid2.outputs[0], metal.inputs[0]); L.new(lid3.outputs[0], metal.inputs[1])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(gt.outputs[0], c1.inputs["Factor"])
    c1.inputs[6].default_value = (0.75, 0.02, 0.03, 1); c1.inputs[7].default_value = (0.95, 0.95, 0.95, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(metal.outputs[0], c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.8, 0.8, 0.82, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"]); L.new(metal.outputs[0], b.inputs["Metallic"])
    b.inputs["Roughness"].default_value = 0.22; b.inputs["Coat Weight"].default_value = 0.7
    return m
canM = can_mat("can")
def make_can(name, parent=None, loc=(0, 0, 0)):
    o = cyl(name, 0.033, 0.122, loc, canM, verts=48)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:                                   # yuqori va pastki torayish
        if abs(v.co.z) > 0.055: v.co.x *= 0.88; v.co.y *= 0.88
    bm.to_mesh(o.data); bm.free()
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = 0.004; bv.segments = 3
    if parent: o.parent = parent
    return o
c2 = make_can("can_table", loc=tuple(BG + Vector((0.22, 0.06, 0.061)))); _par(c2, room)
drop_m = P.water_material("cond", rough=0.02)
for o in P.drops_on(c2, 40, 0.0012, 0.0028, drop_m, seed=4, region=lambda p: abs(p.z) < 0.05): pass

# ======================================================================
# 2) MEGAN: hiqichoq, ichish, yelka qisish
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx")
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
mroot.location = (0, 0, 0); mroot.rotation_euler = (0, 0, 0)       # -Y ga (kameraga) qaraydi
A_ = lambda f: mc.load_action(f, True)
mc.add_strip(meg, A_("Breathing_Idle.fbx"), -40, blend=0, repeat=5.0)
def strip(act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(meg, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
HIC = A_("Drunk_Idle_Variation.fbx")
JOLTS = []
for st in (-3, 53, 588, 783, 921):                      # hiqichoq: harakat ichidagi silkinish ~13 kadrdan keyin
    strip(HIC, st, src=(0, 62), blend=0 if st < 0 else 5, bout=6)
    JOLTS.append(st + 13)
strip(A_("Drinking.fbx"), 185, speed=0.6, blend=8, bout=10)          # bankani og'ziga ko'tarib, shoshib ichadi
strip(A_("Shrugging.fbx"), 852, blend=6, bout=8)                     # "aniq bilishmaydi"
# hiqichoq silkinishi (qo'shimcha): tana keskin tepaga va orqaga
for j in JOLTS:
    key(mroot, j - 1, loc=(0, 0, 0), rot=(0, 0, 0))
    key(mroot, j + 1, loc=(0, 0.015, 0.03), rot=(-5.0, 0, 0))
    key(mroot, j + 4, loc=(0, 0.006, 0.01), rot=(-2.0, 0, 0))
    key(mroot, j + 10, loc=(0, 0, 0), rot=(0, 0, 0))
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.09, 0.08), headE)          # yuz markazi (Head: X chap, Y tepa, Z old)
chestB = child_of_bone("meg_chest", meg, "Spine2")
chest = empty("chest", (0, 0, 0), chestB); chest.rotation_euler = (R(-90), 0, 0)   # ichida: Z tepa, -Y old (sahna o'qlari)
palmE = child_of_bone("meg_palm", meg, "LeftHand")
canR = empty("canR", (0, 0.075, 0.035), palmE)          # kaft ichida (Hand: Y barmoqlar, Z kaft)
can = make_can("can_hand"); can.parent = canR; can.rotation_euler = (0, R(90), 0)
for o in P.drops_on(can, 60, 0.0012, 0.0028, drop_m, seed=6, region=lambda p: abs(p.z) < 0.05): pass
vis(canR, rng("eat", "soda"))

# ---- rentgen nusxa: shaffof Megan + o'pka, diafragma, traxeya, asab ----
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.3, base=0.012)
ghosts = []
for o in mmeshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, XRAY_SHOTS, recursive=False)
for o in mmeshes: vis(o, ROOM_SHOTS, recursive=False)

def dome_mesh(name, a, b, h, m, parent, res=48):
    """diafragma: ikki gumbazli (o'rtasi botiq) yupqa mushak qatlami, asosi z=0"""
    bm = bmesh.new()
    rings = res // 2
    verts = [[None] * res for _ in range(rings + 1)]
    top = bm.verts.new((0, 0, h * 0.78))
    for i in range(1, rings + 1):
        r = i / rings
        for j in range(res):
            t = 2 * math.pi * j / res; x, y = r * math.cos(t), r * math.sin(t)
            z = h * (1 - r * r) ** 0.55 * (1 - 0.22 * math.exp(-(x / 0.28) ** 2)) * (1.0 + 0.08 * x)
            verts[i][j] = bm.verts.new((x * a, y * b, z))
    for j in range(res):
        bm.faces.new((top, verts[1][j], verts[1][(j + 1) % res]))
    for i in range(1, rings):
        for j in range(res):
            bm.faces.new((verts[i][j], verts[i + 1][j], verts[i + 1][(j + 1) % res], verts[i][(j + 1) % res]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = parent
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m)
    so = o.modifiers.new("sol", "SOLIDIFY"); so.thickness = a * 0.04; so.offset = 0
    return o

def dia_material(name, xr=False):
    m = glow_mat(name, (0.55, 0.06, 0.06), (1.0, 0.12, 0.08), 0.35, sss=0.4, base_glow=0.0, coat=0.6)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); grd = N.new("ShaderNodeTexGradient"); grd.gradient_type = "RADIAL"
    L.new(tc.outputs["Object"], grd.inputs[0])
    mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = 90.0; L.new(grd.outputs[0], mm.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = "SINE"; L.new(mm.outputs[0], sn.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(sn.outputs[0], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.35, 0.03, 0.04, 1); cr.color_ramp.elements[1].color = (0.75, 0.12, 0.1, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.003
    L.new(sn.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    # markaziy pay (oq tendon)
    ds = N.new("ShaderNodeVectorMath"); ds.operation = "LENGTH"; L.new(tc.outputs["Object"], ds.inputs[0])
    # (Object koordinatasi masshtabsiz, shuning uchun tendon kichik radiusda)
    return m

def build_chest(tag, parent, xr):
    """O'pkalar, yurak, diafragma, traxeya, bronxlar, frenik asab — real o'lchamda (m), chest koordinatasida."""
    g = 1.6 if xr else 0.0
    lung_m = glow_mat(tag + "lung", (0.72, 0.22, 0.27), (1.0, 0.35, 0.45), 0.4, sss=0.35, base_glow=g, coat=0.5, bump=0.4, bscale=60.0)
    heart_m = glow_mat(tag + "heart", (0.5, 0.05, 0.06), (1.0, 0.15, 0.15), 0.3, sss=0.5, base_glow=g * 0.6, coat=0.7, bump=0.3)
    tr_m = glow_mat(tag + "trachea", (0.88, 0.75, 0.72), (0.8, 0.9, 1.0), 0.35, sss=0.3, base_glow=g * 0.5, coat=0.5)
    tr_m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.4   # ichidagi havo ko'rinsin
    dia_m = dia_material(tag + "dia")
    lungs = []
    lt = bpy.data.textures.new(tag + "lung_t", "CLOUDS"); lt.noise_scale = 0.05
    for sx in (-1, 1):
        o = sphere(f"{tag}lung{sx}", 1.0, (sx * 0.068, -0.045, 0.0), lung_m, scale=(0.058, 0.06, 0.115), sub=4)
        o.parent = parent
        d = o.modifiers.new("d", "DISPLACE"); d.texture = lt; d.strength = 0.08; d.texture_coords = "LOCAL"
        lungs.append(o)
    heart = sphere(tag + "heart", 1.0, (0.018, -0.088, -0.06), heart_m, scale=(0.042, 0.036, 0.048), sub=4); heart.parent = parent
    heart.rotation_euler = (0, R(-25), R(20))
    diaR = empty(tag + "diaR", (0, -0.045, -0.168), parent)
    dia = dome_mesh(tag + "dia", 0.145, 0.098, 0.06, dia_m, diaR)
    trach = P.tube(tag + "trachea", [(0, -0.07, 0.205), (0, -0.066, 0.13), (0, -0.06, 0.05)], 0.0085, tr_m, parent)
    br = [P.tube(f"{tag}bronch{sx}", [(0, -0.06, 0.052), (sx * 0.03, -0.058, 0.03), (sx * 0.058, -0.05, 0.005)], 0.0058, tr_m, parent)
          for sx in (-1, 1)]
    # traxeya halqalari
    for k in range(9):
        z = 0.19 - k * 0.016
        bpy.ops.mesh.primitive_torus_add(major_radius=0.0088, minor_radius=0.0016, location=(0, -0.069 + 0.004 * k / 8, z))
        t_ = bpy.context.object; t_.name = f"{tag}ring{k}"; t_.data.materials.append(tr_m); t_.parent = parent
    larynx = cyl(tag + "larynx", 0.014, 0.03, (0, -0.074, 0.215), tr_m); larynx.parent = parent
    nrv_m = P.pulse_material(tag + "phrenic", (0.95, 0.8, 0.2), base_emit=0.5 if xr else 0.3, pulse_col=(1.0, 0.9, 0.35), width=0.1)
    nerves = [P.tube(f"{tag}phren{sx}", [(sx * 0.024, -0.06, 0.215), (sx * 0.036, -0.082, 0.1), (sx * 0.045, -0.098, -0.02),
                                         (sx * 0.062, -0.085, -0.112)], 0.0017, nrv_m, parent) for sx in (-1, 1)]
    return dict(lungs=lungs, heart=heart, diaR=diaR, dia=dia, lung_m=lung_m, dia_m=dia_m, tr_m=tr_m, nrv_m=nrv_m,
                nerves=nerves, trach=trach)

XC = build_chest("x_", chest, True)
# rentgen havo zarralari (bo'yinda yuqoriga) va asab uchqunlari
air_x = mat("air_x", (0.4, 0.8, 1.0), emit=8.0)
TH0, TH1 = S["xthroat"]
air_up = flow("xair", [[(0, -0.062, 0.06), (0, -0.066, 0.13), (0, -0.07, 0.2), (0, -0.074, 0.222)]], 26, TH0 - 4, TH1, 18,
              air_x, chest, 0.0035, seed=3, jitter=0.003)
spark_m = mat("spark", (1.0, 0.9, 0.4), emit=25.0)
NV0, NV1 = S["nerve"]
rs = random.Random(9); sparks = []
for i in range(24):
    sx = rs.choice((-1, 1)); t = rs.uniform(0.05, 0.95)
    pts = [Vector((sx * 0.024, -0.06, 0.215)), Vector((sx * 0.036, -0.082, 0.1)), Vector((sx * 0.045, -0.098, -0.02)), Vector((sx * 0.062, -0.085, -0.112))]
    p = polyline(pts, t) + Vector((rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(-1, 1))) * 0.006
    s_ = sphere(f"spark{i}", 0.0016, tuple(p), spark_m, scale=(1, 1, 3), sub=1); s_.parent = chest
    s_.rotation_euler = (rs.uniform(0, 3), rs.uniform(0, 3), 0)
    a = NV0 + 14 + rs.randint(0, NV1 - NV0 - 20); scale_vis(s_, a, a + rs.randint(1, 3)); sparks.append(s_)
# rentgen animatsiyalari
XL0, XL1 = S["xlungs"]; XD0, XD1 = S["xdia"]
val_key(XC["lung_m"], "glow", XL0, 0.3); val_key(XC["lung_m"], "glow", XL0 + 10, 1.6); val_key(XC["lung_m"], "glow", XD0 + 6, 0.8)
val_key(XC["dia_m"], "glow", 1, 0.4); val_key(XC["dia_m"], "glow", XD0 + 4, 0.4)
for f in range(XD0 + 10, XD1, 16):
    val_key(XC["dia_m"], "glow", f, 6.0); val_key(XC["dia_m"], "glow", f + 8, 1.5)
val_key(XC["dia_m"], "glow", NV0 + 30, 1.0)
for f in range(NV0 + 40, NV1, 7):
    val_key(XC["dia_m"], "glow", f, 6.0); val_key(XC["dia_m"], "glow", f + 3, 1.0)
val_key(XC["nrv_m"], "pos", 1, -0.2); val_key(XC["nrv_m"], "pos", NV0 + 4, -0.15); val_key(XC["nrv_m"], "pos", NV0 + 34, 1.2)
val_key(XC["nrv_m"], "pos", NV0 + 35, -0.15); val_key(XC["nrv_m"], "pos", NV0 + 58, 1.2)
val_key(XC["nrv_m"], "glow", 1, 0.5); val_key(XC["nrv_m"], "glow", NV0 + 30, 0.8); val_key(XC["nrv_m"], "glow", NV0 + 40, 4.0)
val_key(XC["tr_m"], "glow", TH0, 1.0); val_key(XC["tr_m"], "glow", TH1, 3.0)
vis(chestB, XRAY_SHOTS)

# ======================================================================
# 3) ANATOMIYA STUDIYASI (0,60,1): katta o'pka + diafragma (x5)
# ======================================================================
B0 = Vector((0, 60, 1.0))
studio = empty("studio", tuple(B0)); studio.scale = (5, 5, 5)
SC_ = build_chest("s_", studio, False)
bone_m = mat("rib", (0.92, 0.88, 0.78), 0.35, sss=0.2, sss_scale=0.005, coat=0.3)
for k in range(7):                                      # qovurg'alar (orqadan old tomonga)
    z = 0.12 - k * 0.04; w = 0.12 + 0.025 * math.sin(math.pi * (k + 1) / 8)
    for sx in (-1, 1):
        pts = [(sx * 0.02, 0.035, z + 0.01), (sx * w * 0.8, 0.02, z), (sx * w, -0.05, z - 0.02), (sx * w * 0.8, -0.12, z - 0.04),
               (sx * 0.035, -0.14, z - 0.035 - 0.004 * k)]
        P.tube(f"rib{k}{sx}", pts, 0.0035, bone_m, studio)
for k in range(14):                                     # umurtqa
    cyl(f"vert{k}", 0.014, 0.014, (0, 0.045, 0.2 - k * 0.022), bone_m).parent = studio
# nafas: diafragma pastga, o'pka kengayadi
BR0, BR1 = S["breath"]; AI0, AI1 = S["air"]; SP0, SP1 = S["spasm"]
dR = SC_["diaR"]; d0 = dR.location.copy()
def dia_key(f, dz, sz, lung):
    key(dR, f, loc=tuple(d0 + Vector((0, 0, dz))), scale=(1, 1, sz))
    for o in SC_["lungs"]:
        o.scale = (0.058 * (1 + 0.5 * (lung - 1)), 0.06 * (1 + 0.5 * (lung - 1)), 0.115 * lung)
        o.location.z = 0.0 + (lung - 1) * -0.05; o.keyframe_insert("scale", frame=f); o.keyframe_insert("location", frame=f)
dia_key(1, 0, 1, 1.0); dia_key(BR0 + 8, 0, 1, 1.0); dia_key(AI1, -0.03, 0.55, 1.12)
dia_key(SP0, 0.0, 1.0, 1.0); dia_key(SPASM - 1, 0.0, 1.0, 1.0)
dia_key(SPASM + 2, -0.042, 0.4, 1.16); dia_key(SPASM + 5, -0.036, 0.5, 1.13); dia_key(SPASM + 9, -0.04, 0.45, 1.15)
dia_key(SP1, -0.038, 0.47, 1.14)
val_key(SC_["dia_m"], "glow", 1, 0.0); val_key(SC_["dia_m"], "glow", SPASM - 1, 0.0); val_key(SC_["dia_m"], "glow", SPASM + 1, 8.0)
val_key(SC_["dia_m"], "glow", SPASM + 14, 0.6)
# asab: kasilishdan oldin uchqun
val_key(SC_["nrv_m"], "pos", 1, -0.2); val_key(SC_["nrv_m"], "pos", SPASM - 18, -0.15); val_key(SC_["nrv_m"], "pos", SPASM, 1.2)
val_key(SC_["nrv_m"], "glow", 1, 0.3); val_key(SC_["nrv_m"], "glow", SPASM - 2, 0.3); val_key(SC_["nrv_m"], "glow", SPASM, 5.0)
val_key(SC_["nrv_m"], "glow", SPASM + 20, 1.0)
# havo zarralari: traxeya -> bronx -> o'pka
air_s = mat("air_s", (0.45, 0.8, 1.0), emit=12.0)
paths = []
for sx in (-1, 1):
    for k in range(4):
        end = (sx * (0.05 + 0.02 * k / 3), -0.045 + 0.01 * (k % 2), 0.03 - 0.03 * k)
        paths.append([(0, -0.072, 0.26), (0, -0.07, 0.2), (0, -0.064, 0.11), (0, -0.06, 0.052), (sx * 0.03, -0.058, 0.03), end])
air1 = flow("sair", paths, 46, AI0 - 6, AI1, 22, air_s, studio, 0.0055, seed=5, jitter=0.002)
air2 = flow("sair2", paths, 30, SPASM - 2, SP1, 12, air_s, studio, 0.006, seed=8, jitter=0.002)
plane("sfloor", (14, 14), tuple(B0 + Vector((0, 0, -1.25))), mat("sfloor_m", (0.01, 0.012, 0.02), 0.4, coat=0.3))
vis(studio, STUDIO_SHOTS)
vis(bpy.data.objects["sfloor"], STUDIO_SHOTS)

# ======================================================================
# 4) TOMOQ ICHI (30,0,0) — makro (x10): traxeya ichidan ovoz paychalari
# ======================================================================
M0 = Vector((30, 0, 0))
throat = empty("throat", tuple(M0))
wall_t = bpy.data.materials.new("throat_wall"); wall_t.use_nodes = True
N = wall_t.node_tree.nodes; L = wall_t.node_tree.links; tb = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
rm = N.new("ShaderNodeMath"); rm.operation = "MULTIPLY"; rm.inputs[1].default_value = 55.0; L.new(sep.outputs["Z"], rm.inputs[0])
rsn = N.new("ShaderNodeMath"); rsn.operation = "SINE"; L.new(rm.outputs[0], rsn.inputs[0])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 14; L.new(tc.outputs["Object"], nz.inputs[0])
crt = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], crt.inputs[0])
crt.color_ramp.elements[0].color = (0.4, 0.06, 0.08, 1); crt.color_ramp.elements[1].color = (0.75, 0.28, 0.3, 1)
L.new(crt.outputs[0], tb.inputs["Base Color"])
tb.inputs["Roughness"].default_value = 0.25; tb.inputs["Coat Weight"].default_value = 1.0; tb.inputs["Coat Roughness"].default_value = 0.04
tb.inputs["Subsurface Weight"].default_value = 0.5; tb.inputs["Subsurface Scale"].default_value = 0.01
tb.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
bpt = N.new("ShaderNodeBump"); bpt.inputs["Strength"].default_value = 0.5; bpt.inputs["Distance"].default_value = 0.006
L.new(rsn.outputs[0], bpt.inputs["Height"]); L.new(bpt.outputs[0], tb.inputs["Normal"])
# traxeya (ichi), yuqorida hiqildoq kengayadi
bm = bmesh.new()
RES, ROWS = 48, 40
rows = []
for i in range(ROWS + 1):
    z = -0.2 + 1.1 * i / ROWS
    rr = 0.13 if z < 0.42 else 0.13 + 0.12 * min(1, (z - 0.42) / 0.2)
    row = []
    for j in range(RES):
        t = 2 * math.pi * j / RES
        flat = 0.82 if math.sin(t) > 0.6 else 1.0                 # orqa devor biroz tekis
        row.append(bm.verts.new((rr * math.cos(t), rr * math.sin(t) * (0.9 + 0.1 * flat), z)))
    rows.append(row)
for i in range(ROWS):
    for j in range(RES):
        bm.faces.new((rows[i][j], rows[i][(j + 1) % RES], rows[i + 1][(j + 1) % RES], rows[i + 1][j]))
me = bpy.data.meshes.new("trachea_in"); bm.to_mesh(me); bm.free()
tin = bpy.data.objects.new("trachea_in", me); sc.collection.objects.link(tin); tin.parent = throat
for p in me.polygons: p.use_smooth = True
me.materials.append(wall_t)
# ovoz paychalari: old tomondan (+Y) birlashgan V shakli
fold_m = mat("vfold", (0.9, 0.72, 0.68), 0.2, sss=0.8, sss_scale=0.01, coat=1.0)
FZ = 0.5; FOLD_L = 0.21
folds = []
for sx in (-1, 1):
    piv = empty(f"fpiv{sx}", tuple(M0 + Vector((0, 0.11, FZ))))
    f_ = sphere(f"vfold{sx}", 1.0, (sx * 0.026, -FOLD_L / 2, 0), fold_m, scale=(0.028, FOLD_L / 2, 0.014), sub=4); f_.parent = piv
    sphere(f"aryt{sx}", 0.03, (sx * 0.045, -FOLD_L - 0.01, 0.01), fold_m, scale=(1, 1, 1.3), sub=3).parent = piv
    # yonidagi qalin burma (vestibulyar)
    sphere(f"vband{sx}", 1.0, (sx * 0.09, -FOLD_L / 2 + 0.01, 0.06), mat(f"vband_m{sx}", (0.75, 0.3, 0.32), 0.25, sss=0.5, sss_scale=0.01, coat=0.9),
           scale=(0.05, FOLD_L / 2 + 0.03, 0.04), sub=4).parent = piv
    folds.append((sx, piv))
GL0, GL1 = S["glottis"]; IM0, IM1 = S["impact"]
OPEN = 17.0
for sx, piv in folds:
    def fk(f, a): key(piv, f, rot=(0, 0, sx * a))
    fk(1, OPEN); fk(GL0, OPEN)
    for f in range(GL0 + 8, CLOSE - 6, 12): fk(f, OPEN - 2.5); fk(f + 6, OPEN)
    fk(CLOSE - 1, OPEN); fk(CLOSE + 2, -0.6); fk(CLOSE + 4, 0.4); fk(CLOSE + 6, 0.0)
    fk(IMPACT - 1, 0.0); fk(IMPACT + 1, 1.2); fk(IMPACT + 3, -0.3); fk(IMPACT + 5, 0.6); fk(IMPACT + 8, 0.0); fk(END, 0.0)
    # zarbada paychalar biroz tepaga bukiladi
    key(piv, IMPACT - 1, loc=tuple(M0 + Vector((0, 0.11, FZ)))); key(piv, IMPACT + 2, loc=tuple(M0 + Vector((0, 0.11, FZ + 0.012))))
    key(piv, IMPACT + 8, loc=tuple(M0 + Vector((0, 0.11, FZ))))
# havo: pastdan tepaga, yopiq paychalarga uriladi
air_t = mat("air_t", (0.5, 0.85, 1.0), emit=5.0)
tp = []
for k in range(10):
    a = 2 * math.pi * k / 10; rr = 0.07
    tp.append([tuple(M0 + Vector((rr * math.cos(a), rr * math.sin(a), -0.15))), tuple(M0 + Vector((rr * 0.6 * math.cos(a), rr * 0.6 * math.sin(a), FZ - 0.04)))])
air3 = flow("tair", tp, 40, IM0 - 16, IMPACT + 12, 16, air_t, None, 0.008, seed=11, jitter=0.02)
# zarba to'lqini (halqa)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.04, location=tuple(M0 + Vector((0, 0, FZ - 0.025))))
ring = bpy.context.object; ring.name = "shock"; ring.data.materials.append(mat("shock_m", (0.6, 0.9, 1.0), emit=12.0))
for f, s in ((IMPACT, 0.02), (IMPACT + 10, 0.14)): key(ring, f, scale=(s, s, s * 0.6))
vis(ring, [(IMPACT, IMPACT + 9)])
vis(throat, THROAT_SHOTS); vis(tin, THROAT_SHOTS)
for sx, piv in folds: vis(piv, THROAT_SHOTS)
vis(room, ROOM_SHOTS)

# ======================================================================
# 5) KAMERALAR
# ======================================================================
HO0, HO1 = S["hook"]; FA0, FA1 = S["face"]; EA0, EA1 = S["eat"]; SO0, SO1 = S["soda"]; GU0, GU1 = S["gulp"]
HK0, HK1 = S["hik"]; OU0, OU1 = S["outro"]
chestT = empty("chestT", (0, 0, 1.12))
# 1 ilgak: pastdan keng plan
hookT = empty("hookT", (0, 0, 0.95))
c = shot_cam("hook", (0, 0, 0), hookT, 16, 4.0, focus=faceT)
path_keys(c, ((HO0, (0.7, -2.1, 0.32)), (HO1, (0.45, -1.6, 0.4))))
shake(c, JOLTS[0], JOLTS[0] + 12, 0.035, 1)
# 2 yuzga crash zoom
c = shot_cam("face", (0, 0, 0), faceT, 20, 2.2, focus=faceT)
lens_keys(c, ((FA0, 18), (FA0 + 5, 52), (FA1, 62)))
path_keys(c, ((FA0, (0.22, -1.4, 1.42)), (FA1, (0.1, -1.22, 1.5))))
shake(c, JOLTS[1], JOLTS[1] + 12, 0.02, 2)
# 3 rentgen: o'pka atrofida aylanma
lungT = empty("lungT", (0, -0.05, 0.0), chest)
c = shot_cam("xlungs", (0, 0, 0), lungT, 34, 5.6, focus=lungT)
for f in range(XL0, XL1 + 1, 2):
    a = R(-50 + 35 * (f - XL0) / (XL1 - XL0)); rr = 0.85 - 0.12 * (f - XL0) / (XL1 - XL0)
    key(c, f, loc=(rr * math.sin(a), -rr * math.cos(a), 1.38))
interp(c, "LINEAR", "location")
# 4 rentgen: pastga — diafragma
xdT = empty("xdT", (0, 0, 0)); xdT.parent = chest
key(xdT, XD0, loc=(0, -0.05, -0.02)); key(xdT, XD0 + 30, loc=(0, -0.05, -0.12)); key(xdT, XD1, loc=(0, -0.05, -0.13))
c = shot_cam("xdia", (0, 0, 0), xdT, 36, 5.6, focus=xdT)
path_keys(c, ((XD0, (-0.4, -0.7, 1.4)), (XD0 + 30, (-0.35, -0.62, 1.12)), (XD1, (-0.22, -0.52, 1.1))))
# 5 studiya: nafas — yon tomondan dolly
sT = empty("sT", tuple(B0 + Vector((0, -0.2, -0.35))))
c = shot_cam("breath", (0, 0, 0), sT, 32, 5.6, focus=sT)
path_keys(c, ((BR0, tuple(B0 + Vector((2.9, -2.6, 0.6)))), (BR1, tuple(B0 + Vector((2.4, -2.2, 0.15))))))
# 6 studiya: havo traxeyadan tushadi (tepadan ergashadi)
aT = empty("aT", (0, 0, 0))
key(aT, AI0, loc=tuple(B0 + Vector((0, -0.35, 1.0)))); key(aT, AI1, loc=tuple(B0 + Vector((0, -0.25, 0.1))))
c = shot_cam("air", (0, 0, 0), aT, 28, 4.0, focus=aT)
path_keys(c, ((AI0, tuple(B0 + Vector((1.5, -2.4, 2.1)))), (AI1, tuple(B0 + Vector((1.15, -2.0, 0.9))))))
# 7 ovqat: past burchak, oldinda burger
eatT = empty("eatT", (-0.2, -0.45, 1.0))
c = shot_cam("eat", (0, 0, 0), eatT, 20, 2.8, focus=faceT)
path_keys(c, ((EA0, (-0.6, -1.7, 0.5)), (EA1, (-0.5, -1.5, 0.56))))
# 8 gazli ichimlik: bankaga yaqin
canT = empty("canT", (0, 0, 0), can)
c = shot_cam("soda", (0, 0, 0), canT, 45, 2.0, focus=canT)
path_keys(c, ((SO0, (0.55, -0.7, 1.48)), (SO1, (0.4, -0.58, 1.55))))
# 9 rentgen: asab bo'ylab pastga
nT = empty("nT", (0, 0, 0)); nT.parent = chest
key(nT, NV0, loc=(0.03, -0.08, 0.2)); key(nT, NV0 + 36, loc=(0.045, -0.095, 0.0)); key(nT, NV1, loc=(0.05, -0.085, -0.1))
c = shot_cam("nerve", (0, 0, 0), nT, 44, 4.0, focus=nT)
path_keys(c, ((NV0, (0.42, -0.5, 1.55)), (NV0 + 36, (0.42, -0.5, 1.3)), (NV1, (0.36, -0.48, 1.18))))
# 10 studiya: kasilish — pastdan oldindan
spT = empty("spT", tuple(B0 + Vector((0, -0.25, -0.6))))
c = shot_cam("spasm", (0, 0, 0), spT, 30, 5.6, focus=spT)
path_keys(c, ((SP0, tuple(B0 + Vector((1.5, -2.5, -0.35)))), (SP1, tuple(B0 + Vector((1.1, -2.1, -0.45))))))
lens_keys(c, ((SP0, 24), (SPASM - 1, 26), (SPASM + 3, 32), (SP1, 33)))
shake(c, SPASM, SPASM + 16, 0.08, 3)
# 11 havo yutish: yuzga yaqin
c = shot_cam("gulp", (0, 0, 0), faceT, 50, 2.0, focus=faceT)
path_keys(c, ((GU0, (-0.38, -0.9, 1.48)), (GU1, (-0.26, -0.74, 1.54))))
shake(c, JOLTS[2], JOLTS[2] + 12, 0.015, 4)
# 12 rentgen bo'yin (yon tomondan)
neckT = empty("neckT", (0, -0.07, 0.17), chest)
c = shot_cam("xthroat", (0, 0, 0), neckT, 50, 4.0, focus=neckT)
path_keys(c, ((TH0, (0.6, -0.3, 1.5)), (TH1, (0.44, -0.24, 1.49))))
# 13 tomoq ichi: pastdan paychalarga
gT = empty("gT", tuple(M0 + Vector((0, 0.0, FZ))))
c = shot_cam("glottis", (0, 0, 0), gT, 18, 11.0, focus=gT, clip=0.001)
path_keys(c, ((GL0, tuple(M0 + Vector((0.03, -0.02, 0.0)))), (GL1, tuple(M0 + Vector((0.0, -0.01, 0.16))))))
shake(c, CLOSE, CLOSE + 12, 0.012, 5)
# 14 zarba: qiya burchak
c = shot_cam("impact", (0, 0, 0), gT, 20, 11.0, focus=gT, clip=0.001)
path_keys(c, ((IM0, tuple(M0 + Vector((0.06, -0.07, 0.2)))), (IM1, tuple(M0 + Vector((0.035, -0.05, 0.27))))))
shake(c, IMPACT, IMPACT + 12, 0.015, 6)
# 15 "hik": yuzga crash zoom
c = shot_cam("hik", (0, 0, 0), faceT, 18, 2.2, focus=faceT)
lens_keys(c, ((HK0, 18), (JOLTS[3] - 6, 22), (JOLTS[3] - 1, 62), (HK1, 70)))
path_keys(c, ((HK0, (0.05, -1.45, 1.42)), (HK1, (0.0, -1.25, 1.52))))
shake(c, JOLTS[3], JOLTS[3] + 14, 0.025, 7)
# 16 yakun: orqaga-tepaga chekinish
c = shot_cam("outro", (0, 0, 0), faceT, 32, 4.0, focus=faceT)
path_keys(c, ((OU0, (0.25, -0.95, 1.45)), (OU1, (1.25, -3.0, 2.25))))
lens_keys(c, ((OU0, 34), (OU1, 22)))
shake(c, JOLTS[4], JOLTS[4] + 10, 0.02, 8)
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 6) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(200)); L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
bg_sky = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_sky.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.003, 0.008, 0.02, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_sky.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
ROOM_N = {"hook", "face", "eat", "soda", "gulp", "hik", "outro"}
for f, n in SHOTS:
    s1, s2 = (1.0, 0.0) if n in ROOM_N else (0.0, 1.0)
    for bgn, v in ((bg_sky, s1), (bg_dk, s2)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.0); sun.data.color = (1.0, 0.9, 0.78); sun.rotation_euler = (R(62), 0, R(160))   # derazadan ichkariga
for f, e in lights_for(ROOM_SHOTS, 4.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("win_key", (1.3, WY - 0.3, 1.6), 1.4, (0.92, 0.96, 1.0), lights_for(ROOM_SHOTS, 260.0), target=faceT, shape=(1.4, 1.4))
area("face_fill", (-0.9, -1.5, 1.8), 0.9, (1.0, 0.9, 0.8), lights_for(ROOM_SHOTS, 70.0), target=faceT)
area("face_rim", (-0.8, 1.2, 2.1), 0.6, (1.0, 0.82, 0.62), lights_for(ROOM_SHOTS, 90.0), target=faceT)
area("ceil_bounce", (0, -0.6, 2.75), 2.5, (1.0, 0.93, 0.85), lights_for(ROOM_SHOTS, 120.0), target=chestT)
# rentgen
area("x_rim", (-0.8, 0.4, 2.0), 0.8, (0.3, 0.6, 1.0), lights_for(XRAY_SHOTS, 40.0), target=faceT)
area("x_key", (0.6, -0.9, 1.6), 0.5, (1.0, 0.9, 0.9), lights_for(XRAY_SHOTS, 12.0), target=chestT)
# studiya
area("s_key", tuple(B0 + Vector((-1.8, -2.0, 1.6))), 1.4, (1.0, 0.92, 0.88), lights_for(STUDIO_SHOTS, 260.0), target=sT)
area("s_rim", tuple(B0 + Vector((1.8, 1.6, 1.2))), 1.4, (0.3, 0.6, 1.0), lights_for(STUDIO_SHOTS, 600.0), target=sT)
area("s_rim2", tuple(B0 + Vector((-1.6, 1.4, -0.4))), 1.0, (1.0, 0.45, 0.4), lights_for(STUDIO_SHOTS, 300.0), target=sT)
area("s_low", tuple(B0 + Vector((0.6, -2.2, -1.1))), 1.0, (1.0, 0.9, 0.85), lights_for(rng("spasm"), 160.0), target=spT)
point("s_burst", tuple(B0 + Vector((0, -0.6, -0.8))), 0.3, (1.0, 0.25, 0.15), [(1, 0), (SPASM, 600), (SPASM + 4, 200), (SPASM + 16, 0)], const=False)
# tomoq: kamera yonidagi "endoskop" chirog'i + yuqoridan zaif nur
area("t_scope", tuple(M0 + Vector((0.0, -0.03, -0.12))), 0.05, (1.0, 0.88, 0.8), lights_for(THROAT_SHOTS, 2.5), target=gT)
point("t_top", tuple(M0 + Vector((0, 0, 0.75))), 0.1, (1.0, 0.7, 0.6), lights_for(THROAT_SHOTS, 3.0))
point("t_shock", tuple(M0 + Vector((0, 0, FZ - 0.06))), 0.05, (0.5, 0.85, 1.0), [(1, 0), (IMPACT, 4.0), (IMPACT + 3, 1.5), (IMPACT + 10, 0)], const=False)

# ======================================================================
# 7) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 45))
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
