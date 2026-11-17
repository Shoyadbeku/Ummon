# Uyqu falaji — Zack D. Films uslubida 49 s video (1176 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py va zack_test/uyqusizlik/uyqusizlik.py (yotoqxona, rentgen, miya);
# procedural yordamchilar: zack_test/burish/parts.py (miya, quvur, impuls, rentgen)
# Assetlar: zack_test/tools/get_falaj.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/falaj/falaj.py --render
# Sinov: FRAMES=20,150,380,700,1090 PCT=35 OUT=/tmp/claude-0/test/
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler
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
END = 1176
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (59, "see"), (126, "finger"), (207, "scream"), (275, "title"), (333, "glitch"), (420, "dream"),
         (464, "replay"), (545, "block"), (612, "off"), (693, "wake"), (787, "stuck"), (882, "panic"), (937, "mix"),
         (1001, "shadow"), (1051, "chest"), (1118, "halluc")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM = rng("hook", "see", "finger", "scream", "title", "mix", "shadow", "chest", "halluc")
XR = rng("glitch", "replay", "block", "off", "wake", "stuck")
PAN = rng("panic")
DRM = rng("dream")
F_JOLT = 15            # "to'satdan"
F_GLITCH = 363         # "kichik xatolik"
F_WAKE = 759           # "uyg'onib"
F_SHADOW = 1033        # "sharpa"
F_LEAN = 1122          # "gallyutsinatsiya": mavjudot engashadi

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

def noisy(o, strength=0.05, scale=0.5, sub=0, seed=0):
    t = bpy.data.textures.new(o.name + "_n", "CLOUDS"); t.noise_scale = scale
    if sub:
        s = o.modifiers.new("s", "SUBSURF"); s.levels = sub; s.render_levels = sub; s.show_viewport = False
    d = o.modifiers.new("d", "DISPLACE"); d.texture = t; d.strength = strength; d.texture_coords = "LOCAL"
    d.show_viewport = False
    return o

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
    sc.frame_set(f0); base = {f: None for f in range(f0, f1 + 1)}
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

def area(name, loc, size, col, keys, target=None, shape=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
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

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value

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
# orqa devor: deraza teshigi bilan (x 0..1.2, z 1.0..2.1)
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
# derazadan tashqari osmon (time-lapse: kun/tun)
sky_m = bpy.data.materials.new("sky"); sky_m.use_nodes = True
N = sky_m.node_tree.nodes; L = sky_m.node_tree.links; N.remove(N["Principled BSDF"])
dayv = value_node(sky_m, "day", 0.0)
tcs = N.new("ShaderNodeTexCoord"); grad = N.new("ShaderNodeSeparateXYZ"); L.new(tcs.outputs["Generated"], grad.inputs[0])
cn = N.new("ShaderNodeMix"); cn.data_type = "RGBA"; cn.inputs[6].default_value = (0.008, 0.015, 0.05, 1); cn.inputs[7].default_value = (0.45, 0.68, 1.0, 1)
L.new(dayv, cn.inputs["Factor"])
hor = N.new("ShaderNodeMix"); hor.data_type = "RGBA"; hor.inputs[7].default_value = (0.03, 0.05, 0.14, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, grad.outputs["Y"], clamp=True), 0.5), hor.inputs["Factor"])
L.new(cn.outputs[2], hor.inputs[6])
em = N.new("ShaderNodeEmission"); L.new(hor.outputs[2], em.inputs["Color"])
L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", dayv, 5.0), 0.6), em.inputs["Strength"])
L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
R_(plane("sky", (6, 4), (0.6, Y0 - 1.2, 1.6), sky_m, rot=(90, 0, 0)))
# oy/yulduzlar (tunda): kichik yorug' nuqtalar
star_m = mat("star", (1, 1, 1), emit=6.0)
for i in range(30):
    R_(sphere(f"star{i}", random.uniform(0.004, 0.009), (random.uniform(-1.4, 2.6), Y0 - 1.15, random.uniform(1.0, 3.4)), star_m, sub=1))
moon = R_(sphere("moon", 0.11, (1.05, Y0 - 1.1, 2.55), mat("moon_m", (0.9, 0.93, 1.0), emit=8.0), sub=3))

# --- stol, stul, noutbuk ---
DESK = Vector((0.6, -1.3, 0))
DESK_TOP = 0.715
desk = R_(import_gltf(PH + "WoodenTable_01/WoodenTable_01.gltf", tuple(DESK), 0, (1.0, 1.1, 1.3)))
chair = R_(import_gltf(PH + "modern_arm_chair_01/modern_arm_chair_01.gltf", (0.6, -0.5, 0), 0, 1.0))
lamp = R_(import_gltf(PH + "desk_lamp_arm_01/desk_lamp_arm_01.gltf", (1.25, -1.45, DESK_TOP), 200, 1.0))
plant = R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.65, -1.35, 0), 30, 0.9))
shelf = R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X1 - 0.02, 0.55, 0), -90, 1.0))
books = R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X1 - 0.15, 0.82, 1.03), -90, 1.0))
pic = R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (X0 + 0.03, 0.35, 1.45), 90, 1.0))
lap_m = mat("lap_alu", (0.55, 0.56, 0.6), 0.3, metal=0.9)
key_m = mat("lap_keys", (0.03, 0.03, 0.035), 0.6)

# --- karavot ---
BEDC = Vector((-1.6, 0.2, 0))
MT = 0.55                                          # matras usti
wood_m = mat("bed_wood", (0.33, 0.2, 0.12), 0.45, coat=0.2)
sheet_m = mat("sheet", (0.88, 0.9, 0.95), 0.75, sss=0.05)
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
for sx in (-0.33, 0.33):
    pl = R_(box(f"pillow{sx}", (0.6, 0.38, 0.12), tuple(BEDC + Vector((sx, 0.86, MT + 0.02))), sheet_m, bevel=0.06))
    noisy(pl, 0.02, 0.2)
MEG_BED = BEDC + Vector((0.05, 0.25, MT - 0.95))
duv = R_(box("duvet", (1.56, 1.22, 0.3), tuple(BEDC + Vector((0, -0.43, MT + 0.15))), duvet_m, bevel=0.08))   # bel/ko'krakgacha: qo'llar ustida
import bmesh
_bm = bmesh.new(); _bm.from_mesh(duv.data)
bmesh.ops.subdivide_edges(_bm, edges=_bm.edges[:], cuts=10, use_grid_fill=True); _bm.to_mesh(duv.data); _bm.free()
for v in duv.data.vertices:                         # chetlari pastga osiladi (8 burchakli kubni emas, bo'laklanganini egamiz)
    if abs(v.co.x) > 0.7: v.co.z -= 0.16
    if v.co.y < -0.5: v.co.z -= 0.08
    if v.co.y > 0.5: v.co.z -= 0.05
sub = duv.modifiers.new("s", "SUBSURF"); sub.levels = 1; sub.render_levels = 2; sub.show_viewport = False
noisy(duv, 0.06, 0.25)
NS = BEDC + Vector((1.05, 0.85, 0))
R_(box("nightstand", (0.45, 0.4, 0.5), tuple(NS + Vector((0, 0, 0.25))), wood_m, bevel=0.01))
clock = R_(import_gltf(PH + "alarm_clock_01/alarm_clock_01.gltf", tuple(NS + Vector((0.0, 0.0, 0.5))), -35, 1.3))
point("clock_glow", tuple(NS + Vector((0.0, -0.15, 0.62))), 0.05, (1.0, 0.8, 0.5), lights_for(ROOM, 0.6))
rug = R_(plane("rug", (1.4, 1.0), (-0.3, -0.3, 0.004), mat("rug", (0.45, 0.14, 0.12), 0.95)))
noisy(rug, 0.004, 0.05)

# ======================================================================
for o in (duv,): pass
R_(box("wall_door", (0.9, 0.04, 2.05), (-0.6, Y1 - 0.01, 1.025), mat("door", (0.5, 0.36, 0.25), 0.5, coat=0.2), bevel=0.01))

# ======================================================================
# 2) MEGAN
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
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
MEG_BED = BEDC + Vector((0.05, 0.25, MT - 0.95))
DR = Vector((0, 80, 0))                                 # tush dunyosi
RUN_V = 4.4                                             # m/s
D0, D1 = S["dream"]
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)
place(mroot, 1, tuple(MEG_BED))
place(mroot, D0, tuple(DR + Vector((0, 3.0, 0))))
interp(mroot, "CONSTANT")
place(mroot, D1 + 1, tuple(DR + Vector((0, 3.0 - RUN_V * (D1 + 1 - D0) / 24, 0))))
interp(mroot, "LINEAR", "location")
place(mroot, D1 + 2, tuple(MEG_BED))
for fc in fcurves(mroot):
    for k in fc.keyframe_points:
        if not (D0 <= k.co.x <= D1 + 1 and fc.data_path == "location"): k.interpolation = "CONSTANT"
def strip(arm, act, start, repeat=1.0, speed=1.0):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False)
    s.blend_in = s.blend_out = 0; s.use_auto_blend = False
    return s
def span(act, n): return n / ((act.frame_range[1] - act.frame_range[0]) * 0.8)     # 30 fps -> 24 fps
SLEEP = A_("Laying_Sleeping.fbx")
strip(meg, SLEEP, 1, repeat=span(SLEEP, D0 + 1))
RUN = A_("Running_8.fbx"); strip(meg, RUN, D0, repeat=span(RUN, D1 - D0 + 3))
strip(meg, SLEEP, D1 + 1, repeat=span(SLEEP, S["chest"][0] - D1 + 1))
BRE = A_("Laying_Breathless.fbx"); strip(meg, BRE, S["chest"][0], repeat=span(BRE, END - S["chest"][0] + 3))

def pq(arm, bone, f, rot):
    o = arm.pose.bones["mixamorig:" + bone]; o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Euler([R(a) for a in rot]).to_quaternion(); o.keyframe_insert("rotation_quaternion", frame=f)
def overlay(arm, name):
    ov = arm.animation_data.action; ov.name = name; ov.use_fake_user = True
    arm.animation_data.action = None
    tr = arm.animation_data.nla_tracks.new(); tr.name = name
    st = tr.strips.new(name, 1, ov)
    if hasattr(st, "action_slot") and ov.slots: st.action_slot = ov.slots[0]
    st.blend_type = "COMBINE"; st.extrapolation = "HOLD"; st.blend_in = st.blend_out = 0
# Megan: "to'satdan" boshi silkinadi, barmoq titraydi, ko'krak bosilganda boshi tipirchilaydi
for b in ("Neck", "Head", "LeftHandIndex1", "LeftHandIndex2", "LeftHandMiddle1"): pq(meg, b, 1, (0, 0, 0))
pq(meg, "Head", F_JOLT - 2, (0, 0, 0)); pq(meg, "Neck", F_JOLT - 2, (0, 0, 0))
pq(meg, "Head", F_JOLT + 1, (-14, 4, 0)); pq(meg, "Neck", F_JOLT + 1, (-8, 0, 0))
pq(meg, "Head", F_JOLT + 6, (-4, 2, 0)); pq(meg, "Neck", F_JOLT + 6, (-2, 0, 0))
pq(meg, "Head", F_JOLT + 14, (0, 0, 0)); pq(meg, "Neck", F_JOLT + 14, (0, 0, 0))
FI0, FI1 = S["finger"]
rt_ = random.Random(4)
for f in range(FI0, FI1 + 1, 3):
    a = 6 * (0.3 + 0.7 * max(0, math.sin((f - FI0) / (FI1 - FI0) * math.pi * 3))) * rt_.uniform(0.4, 1.0)
    pq(meg, "LeftHandIndex1", f, (a, 0, 0)); pq(meg, "LeftHandIndex2", f, (a * 0.6, 0, 0)); pq(meg, "LeftHandMiddle1", f, (a * 0.4, 0, 0))
for b in ("LeftHandIndex1", "LeftHandIndex2", "LeftHandMiddle1"): pq(meg, b, FI1 + 1, (0, 0, 0))
CH0 = S["chest"][0]
pq(meg, "Head", CH0 - 1, (0, 0, 0))
rh = random.Random(9)
for f in range(CH0, END + 1, 4):
    pq(meg, "Head", f, (rh.uniform(-3, 3), rh.uniform(-9, 9), rh.uniform(-3, 3)))
overlay(meg, "meg_overlay")

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.07, 0.1), headE)          # ko'zlar oldi (Head fazosi: Y tepa, Z old)
handE = child_of_bone("meg_lhand", meg, "LeftHandIndex1")
def W(arm, b, f):
    sc.frame_set(f); return arm.matrix_world @ arm.pose.bones["mixamorig:" + b].head
REF = 30
BW = {b: W(meg, b, REF).copy() for b in ("Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "HeadTop_End", "LeftShoulder", "LeftArm",
      "LeftForeArm", "LeftHand", "RightShoulder", "RightArm", "RightForeArm", "RightHand", "LeftUpLeg", "LeftLeg", "LeftFoot",
      "LeftToeBase", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase", "LeftHandIndex1")}
sc.frame_set(REF); bpy.context.view_layer.update()
FACE = faceT.matrix_world.translation.copy()
HEADC = headE.matrix_world @ Vector((0, 0.1, 0.02))
sc.frame_set(S["chest"][0] + 10); bpy.context.view_layer.update(); FACE2 = faceT.matrix_world.translation.copy(); sc.frame_set(REF)
print("FACE", FACE, "HEAD", BW["Head"], "HIPS", BW["Hips"], "LHAND", BW["LeftHandIndex1"], "FEET", BW["LeftFoot"])

# --- rentgen nusxasi: "thr" dan bosh tomoni (Y > thr) o'chadi (ko'k -> kulrang) ---
def xr_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    thr = value_node(m, "thr", 9.0); gl = value_node(m, "glow", 1.3)
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sp.inputs[0])
    off = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", sp.outputs["Y"], thr), 0.06, clamp=True)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; cm.inputs[6].default_value = (0.35, 0.75, 1.0, 1); cm.inputs[7].default_value = (0.42, 0.42, 0.48, 1)
    L.new(off, cm.inputs["Factor"])
    em = N.new("ShaderNodeEmission"); L.new(cm.outputs[2], em.inputs["Color"])
    k = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", off, 0.65))
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", fac, gl), k), 0.015), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.7), 0.06, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
xbody = xr_mat("xr_body")
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
for o in mmeshes: vis(o, DRM if "Sneakers" in o.name else ROOM + DRM, recursive=False)
OF0, OF1 = S["off"]
Y_HEAD = BW["HeadTop_End"].y + 0.05; Y_FEET = BW["LeftToeBase"].y - 0.15
val_key(xbody, "thr", 1, 9.0); val_key(xbody, "thr", OF0 + 6, Y_HEAD); val_key(xbody, "thr", OF1 - 8, Y_FEET); val_key(xbody, "thr", OF1, -9.0)
interp(xbody.node_tree, "LINEAR")

# --- miya (rentgen boshda) ---
def brain_mat2(name, glow=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15; b.inputs["Roughness"].default_value = 0.4
    gl = value_node(m, "glow", glow); red = value_node(m, "red", 0.0); wh = value_node(m, "white", 0.0); pu = value_node(m, "purple", 0.0)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs[6].default_value = (0.78, 0.42, 0.45, 1); base.inputs[7].default_value = (0.92, 0.6, 0.6, 1)
    L.new(nz.outputs["Fac"], base.inputs["Factor"]); L.new(base.outputs[2], b.inputs["Base Color"])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; c1.inputs[6].default_value = (1.0, 0.55, 0.65, 1); c1.inputs[7].default_value = (0.55, 0.25, 1.0, 1)
    L.new(pu, c1.inputs["Factor"])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (1.0, 0.06, 0.02, 1)
    L.new(red, c2.inputs["Factor"])
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"; L.new(c2.outputs[2], c3.inputs[6]); c3.inputs[7].default_value = (1.0, 0.95, 0.85, 1)
    L.new(wh, c3.inputs["Factor"]); L.new(c3.outputs[2], b.inputs["Emission Color"])
    fl = P.math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", fl, 0.15), gl), b.inputs["Emission Strength"])
    return m
def assign(root, m):
    for o in root.children_recursive:
        if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(m)
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
xb_m = brain_mat2("xbrain_m", 1.0); assign(xbrain, xb_m)
vis(xbrain, XR)
GL0, GL1 = S["glitch"]; RP0, RP1 = S["replay"]; BL0, BL1 = S["block"]; WK0, WK1 = S["wake"]; ST0, ST1 = S["stuck"]
val_key(xb_m, "glow", 1, 1.0)
for f in range(GL0, GL1, 10): val_key(xb_m, "glow", f, 1.6); val_key(xb_m, "glow", f + 5, 0.9)
val_key(xb_m, "glow", RP0, 3.0); val_key(xb_m, "glow", BL1, 2.2)
val_key(xb_m, "purple", RP0 - 1, 0.0); val_key(xb_m, "purple", RP0, 1.0); val_key(xb_m, "purple", F_WAKE, 1.0); val_key(xb_m, "purple", F_WAKE + 1, 0.0)
val_key(xb_m, "glow", OF1, 1.2); val_key(xb_m, "glow", F_WAKE - 1, 0.8); val_key(xb_m, "glow", F_WAKE + 1, 6.0); val_key(xb_m, "glow", F_WAKE + 12, 4.0)
val_key(xb_m, "white", 1, 0.0); val_key(xb_m, "white", F_WAKE, 0.0); val_key(xb_m, "white", F_WAKE + 1, 1.0); val_key(xb_m, "white", F_WAKE + 14, 0.35)
for f in range(ST0, ST1, 12): val_key(xb_m, "glow", f, 5.0); val_key(xb_m, "glow", f + 6, 3.0)
for n_ in ("glow", "purple", "white"): pass
interp(xb_m.node_tree, "LINEAR")
for fc in mc._fcurves(xb_m.node_tree.animation_data.action):
    if '"purple"' in fc.data_path or '"white"' in fc.data_path:
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
# kichik xatolik: miya ustunida qizil nuqta miltillaydi
glitch_m = mat("glitch", (1, 0.02, 0.0), emit=0.0, emit_col=(1.0, 0.02, 0.0))
gdot = sphere("glitch_dot", 0.004, (0, 0, 0), glitch_m, sub=3, parent=headE); gdot.location = (0, 0.075, 0.015)
gb = glitch_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
def gkey(f, v): gb.default_value = v; gb.keyframe_insert("default_value", frame=f)
gkey(1, 0.0); gkey(F_GLITCH - 8, 0.0)
rg = random.Random(2)
for f in range(F_GLITCH - 6, GL1 + 1, 2): gkey(f, rg.choice((0.0, 0.6, 1.2, 2.0)))
gkey(GL1 + 1, 0.0)
interp(glitch_m.node_tree, "CONSTANT")
vis(gdot, XR, recursive=False)

# --- asab tolalari: miyadan umurtqa, qo'l-oyoqqa ---
def nerve_mat(name, phase):
    m = P.pulse_material(name, (0.1, 0.3, 1.0), base_emit=0.3, pulse_col=(0.45, 0.8, 1.0), width=0.05)
    for n in m.node_tree.nodes:
        if n.type == "MATH" and n.operation == "MULTIPLY" and abs(n.inputs[1].default_value - 4.0) < 1e-6 and not n.inputs[1].links:
            n.inputs[1].default_value = 0.0
    return m
B_ = BW
NECK = B_["Neck"]
chains = [
    [HEADC, NECK, B_["Spine2"], B_["LeftShoulder"], B_["LeftArm"], B_["LeftForeArm"], B_["LeftHand"]],
    [HEADC, NECK, B_["Spine2"], B_["RightShoulder"], B_["RightArm"], B_["RightForeArm"], B_["RightHand"]],
    [HEADC, NECK, B_["Spine2"], B_["Spine1"], B_["Spine"], B_["Hips"], B_["LeftUpLeg"], B_["LeftLeg"], B_["LeftFoot"], B_["LeftToeBase"]],
    [HEADC, NECK, B_["Spine2"], B_["Spine1"], B_["Spine"], B_["Hips"], B_["RightUpLeg"], B_["RightLeg"], B_["RightFoot"], B_["RightToeBase"]],
]
nerves = []; nmats = []
for i, ch in enumerate(chains):
    pts = [ch[0]]
    for p in ch[1:]:                                     # oraliq nuqtalar: NURBS bo'g'imlarga yaqin o'tsin
        pts.append(pts[-1].lerp(p, 0.5)); pts.append(p)
    m = nerve_mat(f"nerve{i}", i * 3); nmats.append(m)
    t_ = P.tube(f"nerve{i}", [tuple(p) for p in pts], 0.0032, m, None, taper=[1.0] * len(pts))
    nerves.append(t_)
    L_ = [0.0]
    for a, b in zip(pts, pts[1:]): L_.append(L_[-1] + (b - a).length)
    t_["u_neck"] = L_[2] / L_[-1]                        # bo'yin (darvoza) parametri
U_GATE = sum(t["u_neck"] for t in nerves) / len(nerves)
NV = rng("replay", "block", "off", "wake", "stuck")
for t_ in nerves: vis(t_, NV, recursive=False)
GATE_HITS = []
for i, m in enumerate(nmats):
    val_key(m, "pos", 1, -0.2)
    # replay: to'liq yuguradi
    f = RP0 - 6 + i * 3
    while f < RP1:
        val_key(m, "pos", f, -0.08); val_key(m, "pos", f + 22, 1.12); f += 16
    # block/stuck: darvozagacha yetib to'xtaydi
    for a, b in ((BL0 - 4, BL1), (ST0, ST1)):
        f = a + i * 2
        while f < b:
            val_key(m, "pos", f, -0.08); val_key(m, "pos", f + 9, U_GATE - 0.01); val_key(m, "pos", f + 10, -0.3)
            if i == 0: GATE_HITS.append(f + 9)
            f += 14
    val_key(m, "pos", OF0, -0.3); val_key(m, "pos", ST0 - 1, -0.3); val_key(m, "pos", ST1 + 1, -0.3)
    val_key(m, "glow", 1, 0.3); val_key(m, "glow", OF0 + 10, 0.3); val_key(m, "glow", OF1 - 10, 0.08); val_key(m, "glow", ST1, 0.08)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
# darvoza (miya ustunidagi qizil halqa)
hd = (B_["Head"] - NECK).normalized()
bpy.ops.mesh.primitive_torus_add(major_radius=0.024, minor_radius=0.0022, location=tuple(NECK.lerp(B_["Head"], 0.35)))
gate = bpy.context.object; gate.name = "gate"
gate.rotation_mode = "QUATERNION"; gate.rotation_quaternion = hd.to_track_quat("Z", "Y")
gate_m = mat("gate_m", (1, 0.02, 0.0), emit=0.0, emit_col=(1.0, 0.02, 0.0)); gate.data.materials.append(gate_m)
for p in gate.data.polygons: p.use_smooth = True
gs = gate_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
def gsk(f, v): gs.default_value = v; gs.keyframe_insert("default_value", frame=f)
gsk(1, 0.0); gsk(BL0 - 1, 0.0); gsk(BL0 + 2, 2.0)
for f in GATE_HITS: gsk(f - 1, 2.0); gsk(f, 9.0); gsk(f + 4, 2.0)
gsk(END, 2.0)
vis(gate, rng("block", "off", "wake", "stuck"), recursive=False)
gate_l = point("gate_l", tuple(gate.location), 0.02, (1.0, 0.1, 0.03), [(1, 0)], const=False)
for f, v in ((BL0 - 1, 0), (BL0 + 2, 0.4)): gate_l.data.energy = v; gate_l.data.keyframe_insert("energy", frame=f)
for f in GATE_HITS: 
    for df, v in ((-1, 0.4), (0, 3.0), (4, 0.4)): gate_l.data.energy = v; gate_l.data.keyframe_insert("energy", frame=f + df)
for f, v in ((ST1 + 1, 0.0),): gate_l.data.energy = v; gate_l.data.keyframe_insert("energy", frame=f)

# ======================================================================
# 3) MAKRO MIYA (vahima)
# ======================================================================
MB = Vector((30, 0, 0))
mbr_grp = empty("macro_brain_grp")
mbrain, _ = P.build_brain("mbrain", mbr_grp, size=1.0)
mbrain.location = MB
mb_m = brain_mat2("mbrain_m", 0.6); assign(mbrain, mb_m)
PA0, PA1 = S["panic"]
val_key(mb_m, "red", 1, 1.0)
for f in range(PA0, PA1 + 1, 6): val_key(mb_m, "glow", f, 6.0); val_key(mb_m, "glow", f + 3, 1.5)
vis(mbr_grp, PAN)
# vahima to'lqinlari: miya atrofida kengayuvchi qizil halqalar
wave_m = bpy.data.materials.new("wave"); wave_m.use_nodes = True
N = wave_m.node_tree.nodes; L = wave_m.node_tree.links; N.remove(N["Principled BSDF"])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.08, 0.03, 1); em.inputs["Strength"].default_value = 6.0
trn = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.6
L.new(trn.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
for k in range(4):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.012, location=tuple(MB + Vector((0, 0, 0.05))), rotation=(R(k * 22), R(k * 17 - 20), 0))
    w_ = bpy.context.object; w_.name = f"wave{k}"; w_.data.materials.append(wave_m)
    f0 = PA0 + k * 12
    key(w_, 1, scale=0.4); key(w_, f0, scale=0.4); key(w_, f0 + 16, scale=1.6)
    vis(w_, [(f0, min(PA1, f0 + 16))], recursive=False)

# ======================================================================
# 4) TUSH DUNYOSI
# ======================================================================
dr_grp = empty("dream_grp")
dground_m = bpy.data.materials.new("dground"); dground_m.use_nodes = True
N = dground_m.node_tree.nodes; L = dground_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.12, 0.05, 0.22, 1); b.inputs["Roughness"].default_value = 0.08; b.inputs["Metallic"].default_value = 0.3
tcg = N.new("ShaderNodeTexCoord"); vg = N.new("ShaderNodeTexVoronoi"); vg.inputs["Scale"].default_value = 1.2; L.new(tcg.outputs["Object"], vg.inputs["Vector"])
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", vg.outputs["Distance"], 0.06), 4.0), b.inputs["Emission Strength"])
b.inputs["Emission Color"].default_value = (0.75, 0.4, 1.0, 1)
dg = plane("dream_ground", (60, 60), tuple(DR + Vector((0, -6, 0))), dground_m, parent=dr_grp)
orb_ms = [mat(f"orb{i}", c, emit=e) for i, (c, e) in enumerate((((1.0, 0.45, 0.85), 8.0), ((0.5, 0.6, 1.0), 10.0), ((0.8, 0.5, 1.0), 6.0), ((1.0, 0.8, 0.5), 9.0)))]
ro = random.Random(17)
for i in range(70):
    p = DR + Vector((ro.uniform(-7, 7), ro.uniform(-14, 6), ro.uniform(0.3, 5.5)))
    if abs(p.x - DR.x) < 0.8 and p.z < 2.2: p.x += 1.6 * (1 if ro.random() < 0.5 else -1)
    o = sphere(f"orb{i}", ro.uniform(0.03, 0.16), tuple(p), orb_ms[i % 4], sub=2, parent=dr_grp)
    key(o, D0, loc=tuple(p)); key(o, D1, loc=tuple(p + Vector((0, 0, ro.uniform(0.2, 0.6)))))
cloud_m = bpy.data.materials.new("cloud"); cloud_m.use_nodes = True
N = cloud_m.node_tree.nodes; L = cloud_m.node_tree.links; N.remove(N["Principled BSDF"])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.85, 0.55, 1.0, 1); em.inputs["Strength"].default_value = 1.2
trn = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"]), 0.8), mx.inputs[0])
L.new(trn.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
for i in range(14):
    p = DR + Vector((ro.choice((-1, 1)) * ro.uniform(3.5, 9), ro.uniform(-16, 4), ro.uniform(0.0, 4.0)))
    c_ = sphere(f"cloud{i}", ro.uniform(1.0, 2.2), tuple(p), cloud_m, scale=(1.4, 1.0, 0.7), sub=3, parent=dr_grp); noisy(c_, 0.5, 0.6)
# uzoqda katta oy (tush)
sphere("dream_moon", 2.5, tuple(DR + Vector((-4, -30, 6))), mat("dmoon", (1, 0.9, 1.0), emit=6.0, emit_col=(1.0, 0.8, 1.0)), sub=4, parent=dr_grp)
vis(dr_grp, DRM)

# ======================================================================
# 5) SHARPA / MAVJUDOT (Parasite, qop-qora)
# ======================================================================
proot, par, pmeshes = mc.load_character("par", "Parasite_L_Starkie.fbx"); sc.render.fps = 24
shadow_m = bpy.data.materials.new("shadow"); shadow_m.use_nodes = True
N = shadow_m.node_tree.nodes; L = shadow_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.002, 0.002, 0.003, 1); b.inputs["Roughness"].default_value = 0.8
b.inputs["Specular IOR Level"].default_value = 0.05; b.inputs["Roughness"].default_value = 1.0
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 3.0), 0.5), b.inputs["Emission Strength"])
b.inputs["Emission Color"].default_value = (0.35, 0.12, 0.6, 1)
for o in pmeshes:
    o.data.materials.clear(); o.data.materials.append(shadow_m)
PSC = 0.92
SH0, SH1 = S["shadow"]
SHADOW_P = Vector((-0.2, -1.25, 0))
CHEST_P = Vector((MEG_BED.x + 0.02, BW["Hips"].y + 0.02, MT - 0.22))
proot.scale = (PSC,) * 3
place(proot, 1, tuple(SHADOW_P), -147)
place(proot, CH0, tuple(CHEST_P), 180)
interp(proot, "CONSTANT")
ZI = A_("Zombie_Idle.fbx"); strip(par, ZI, 1, repeat=span(ZI, CH0 + 2))
CI = A_("Crouching_Idle.fbx"); strip(par, CI, CH0, repeat=span(CI, END - CH0 + 3))
HA0, HA1 = S["halluc"]
for b in ("Spine", "Spine1", "Spine2", "Neck", "Head", "JawDowm"): pq(par, b, 1, (0, 0, 0)); pq(par, b, F_LEAN, (0, 0, 0))
LEAN = float(os.environ.get("LEAN", 0.4))
for f, k in ((F_LEAN + 14, 1.0), (HA1, 1.15)):
    pq(par, "Spine", f, (LEAN * 10 * k, 0, 0)); pq(par, "Spine1", f, (LEAN * 12 * k, 0, 0)); pq(par, "Spine2", f, (LEAN * 12 * k, 0, 0))
    pq(par, "Neck", f, (LEAN * 10 * k, 0, 0)); pq(par, "Head", f, (LEAN * 8 * k, 0, 6))
JAW = float(os.environ.get("JAW", 1.0))
pq(par, "JawDowm", F_LEAN + 8, (0, 0, 0)); pq(par, "JawDowm", F_LEAN + 18, (JAW * 28, 0, 0)); pq(par, "JawDowm", HA1, (JAW * 34, 0, 0))
overlay(par, "par_overlay")
eye_m = mat("eye_red", (1, 0.0, 0.0), emit=0.0, emit_col=(1.0, 0.0, 0.0))
ee = eye_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.0), (SH0, 0.0), (F_SHADOW, 0.0), (F_SHADOW + 3, 2.5), (F_SHADOW + 8, 1.2), (CH0, 1.2), (F_LEAN + 10, 1.2), (F_LEAN + 16, 2.5)):
    ee.default_value = v; ee.keyframe_insert("default_value", frame=f)
interp(eye_m.node_tree, "CONSTANT")
eyes = []
for bn in ("LeftEye", "RightEye"):
    e_ = child_of_bone("par_" + bn, par, bn)
    eyes.append(sphere("pe_" + bn, 0.011, (0, 0, 0), eye_m, sub=2, parent=e_))
    eyes[-1].location = (0, 0, 0.012)
PV = rng("shadow", "chest", "halluc")
for o in pmeshes + eyes: vis(o, PV, recursive=False)
parHead = child_of_bone("par_head", par, "Head")
parFace = empty("parFace", (0, 0.06, 0.08), parHead)

# ======================================================================
# 6) TUSH TUMANI xonaga kiradi (mix)
# ======================================================================
MX0, MX1 = S["mix"]
fog_m = bpy.data.materials.new("fog"); fog_m.use_nodes = True
N = fog_m.node_tree.nodes; L = fog_m.node_tree.links; N.remove(N["Principled BSDF"])
tcf = N.new("ShaderNodeTexCoord"); nf = N.new("ShaderNodeTexNoise"); nf.inputs["Scale"].default_value = 2.0; nf.inputs["Detail"].default_value = 3
L.new(tcf.outputs["Object"], nf.inputs["Vector"])
fogv = value_node(fog_m, "amt", 0.0)
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.6, 0.3, 1.0, 1); em.inputs["Strength"].default_value = 0.5
trn = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", nf.outputs["Fac"], 3.0), fogv), mx.inputs[0])
L.new(trn.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
fog_grp = empty("fog_grp")
rf_ = random.Random(31)
for i in range(9):
    z = 0.05 + i * 0.12
    fp = plane(f"fog{i}", (4.2, 3.2), ((X0 + X1) / 2, (Y0 + Y1) / 2, z), fog_m, parent=fog_grp)
    fp.rotation_euler.z = rf_.uniform(0, 3)
    key(fp, MX0, loc=(fp.location.x, fp.location.y, z)); key(fp, MX1, loc=(fp.location.x + rf_.uniform(-0.4, 0.4), fp.location.y + 0.5, z + 0.05))
val_key(fog_m, "amt", MX0, 0.1); val_key(fog_m, "amt", MX1, 0.7)
for i in range(26):
    p = Vector((rf_.uniform(X0 + 0.3, X1 - 0.3), rf_.uniform(Y0 + 0.3, Y1 - 0.3), rf_.uniform(0.3, 2.2)))
    o = sphere(f"room_orb{i}", rf_.uniform(0.012, 0.04), tuple(p), orb_ms[i % 4], sub=2, parent=fog_grp)
    key(o, MX0, loc=tuple(p), scale=0.0); key(o, MX0 + 8 + i, scale=1.0); key(o, MX1, loc=tuple(p + Vector((0, 0, 0.3))))
vis(fog_grp, rng("mix"))
for o in room_objs: vis(o, ROOM)

# ======================================================================
# 7) KAMERALAR
# ======================================================================
from mathutils import Quaternion
def at(name, p, parent=None): return empty(name, tuple(p), parent)
def V(*a): return Vector(a)
HEAD = BW["Head"]; HIPS = BW["Hips"]; HAND = BW["LeftHandIndex1"]
FEETC = (BW["LeftFoot"] + BW["RightFoot"]) / 2
def look_keys(cam, f0, f1, posf, tgtf, rollf=lambda t: 0.0, step=1):
    cam.rotation_mode = "QUATERNION"
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = (f - f0) / max(1, f1 - f0); p = posf(t); d = tgtf(t) - p
        q = d.to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), R(rollf(t)))
        cam.location = p; cam.keyframe_insert("location", frame=f)
        cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
# 1 ILGAK: tepadan yuzga tez push-in, "to'satdan" da silkinish
H0, H1 = S["hook"]
c = shot_cam("hook", (0, 0, 0), faceT, 22, 2.2, focus=faceT)
path_keys(c, [(H0, FACE + V(0.2, -0.4, 0.8)), (F_JOLT, FACE + V(0.12, -0.24, 0.5)), (H1, FACE + V(0.06, -0.12, 0.32))])
lens_keys(c, [(H0, 22), (F_JOLT, 30), (H1, 40)])
shake(c, F_JOLT, F_JOLT + 14, 0.014, seed=2)
# 2 hamma narsani ko'rib: bosh ortidan qorong'u xonaga
SE0, SE1 = S["see"]
seeT = at("seeT", (0.55, Y0 + 0.2, 1.3))
c = shot_cam("see", (0, 0, 0), seeT, 18, 4.0, focus=at("seeF", (0.6, -1.0, 0.9)))
path_keys(c, [(SE0, HEAD + V(0.12, 0.2, 0.5)), (SE1, HEAD + V(0.22, 0.02, 0.56))])
lens_keys(c, [(SE0, 18), (SE1, 22)])
# 3 barmoq: makro slayd
handT = empty("handT", (0, 0, 0), handE)
c = shot_cam("finger", (0, 0, 0), handT, 50, 4.0, focus=handT)
path_keys(c, [(FI0, HAND + V(0.42, -0.3, 0.16)), (FI1, HAND + V(0.36, 0.16, 0.14))])
lens_keys(c, [(FI0, 40), (FI1, 48)])
# 4 baqira olmaydi: yondan past burchak, crash zoom
SC0, SC1 = S["scream"]; F_SCR = 219
c = shot_cam("scream", (0, 0, 0), faceT, 26, 2.2, focus=faceT)
path_keys(c, [(SC0, FACE + V(0.5, 0.12, 0.06)), (F_SCR, FACE + V(0.4, 0.08, 0.07)), (F_SCR + 4, FACE + V(0.3, 0.04, 0.08)), (SC1, FACE + V(0.28, 0.03, 0.08))])
lens_keys(c, [(SC0, 26), (F_SCR, 30), (F_SCR + 4, 42), (SC1, 46)])
shake(c, F_SCR + 3, SC1, 0.008, seed=6, decay=False)
# 5 uyqu falaji: tepadan aylanma kran
TI0, TI1 = S["title"]
tiT = at("titleT", BW["Spine1"])
c = shot_cam("title", (0, 0, 0), tiT, 14, 5.6, focus=tiT)
orbit(c, TI0, TI1, V(BW["Spine1"].x, BW["Spine1"].y, 0), 0.35, 0.25, 10, 80, 2.45, 1.95)
lens_keys(c, [(TI0, 14), (TI1, 17)])
# 6 rentgen bosh: kichik xatolik
brT = at("brainT", HEADC)
c = shot_cam("glitch", (0, 0, 0), brT, 30, 2.8, focus=brT)
path_keys(c, [(GL0, HEADC + V(0.95, -0.45, 0.5)), (F_GLITCH - 2, HEADC + V(0.7, -0.32, 0.38)), (F_GLITCH + 3, HEADC + V(0.42, -0.16, 0.22)), (GL1, HEADC + V(0.38, -0.14, 0.2))])
lens_keys(c, [(GL0, 30), (F_GLITCH - 2, 32), (F_GLITCH + 3, 42), (GL1, 44)])
shake(c, F_GLITCH + 2, F_GLITCH + 16, 0.01, seed=8)
# 7 tush: yuguruvchiga old-yondan past ergashish
def runner(f): return DR + V(0, 3.0 - RUN_V * (f - D0) / 24, 0)
drT = empty("dreamT"); path_keys(drT, [(D0, runner(D0) + V(0, -0.1, 1.15)), (D1, runner(D1) + V(0, -0.1, 1.15))]); interp(drT, "LINEAR")
c = shot_cam("dream", (0, 0, 0), drT, 20, 2.8, focus=drT)
path_keys(c, [(D0, runner(D0) + V(1.5, -2.6, 0.35)), (D1, runner(D1) + V(0.8, -1.7, 0.45))])
# 8 takrorlaydi: rentgen tana bo'ylab yonlama
rpT = empty("replayT"); path_keys(rpT, [(RP0, BW["Spine2"]), (RP1, HIPS)])
c = shot_cam("replay", (0, 0, 0), rpT, 24, 4.0, focus=rpT)
path_keys(c, [(RP0, BW["Spine2"] + V(1.1, 0.4, 0.75)), (RP1, HIPS + V(1.0, -0.3, 0.65))])
# 9 darvoza: bo'yin yaqin plan
gT = at("gateT", gate.location)
c = shot_cam("block", (0, 0, 0), gT, 36, 2.8, focus=gT)
path_keys(c, [(BL0, gate.location + V(0.34, 0.14, 0.2)), (BL1, gate.location + V(0.19, 0.04, 0.11))])
# 10 o'chirish: boshdan oyoqqa
ofT = empty("offT"); path_keys(ofT, [(OF0, HEADC), (OF0 + 8, HEADC), (OF1 - 6, FEETC), (OF1, FEETC)])
c = shot_cam("off", (0, 0, 0), ofT, 20, 5.0, focus=ofT)
path_keys(c, [(OF0, HEADC + V(0.8, 0.35, 0.95)), (OF0 + 8, HEADC + V(0.8, 0.3, 0.95)), (OF1 - 6, FEETC + V(0.8, -0.1, 0.95)), (OF1, FEETC + V(0.8, -0.15, 0.95))])
# 11 uyg'onib ketadi: crash zoom
c = shot_cam("wake", (0, 0, 0), brT, 30, 2.8, focus=brT)
path_keys(c, [(WK0, HEADC + V(0.5, -0.5, 0.75)), (F_WAKE - 1, HEADC + V(0.4, -0.38, 0.6)), (F_WAKE + 3, HEADC + V(0.22, -0.2, 0.34)), (WK1, HEADC + V(0.2, -0.18, 0.31))])
lens_keys(c, [(WK0, 30), (F_WAKE - 1, 32), (F_WAKE + 3, 40), (WK1, 42)])
shake(c, F_WAKE + 1, F_WAKE + 18, 0.012, seed=11)
# 12 tana qotib qoladi: yuzdan orqaga chekinish
stT = empty("stuckT"); path_keys(stT, [(ST0, HEADC), (ST1, BW["Spine1"])])
c = shot_cam("stuck", (0, 0, 0), stT, 30, 4.0, focus=stT)
path_keys(c, [(ST0, HEADC + V(0.14, -0.16, 0.3)), (ST1, BW["Spine1"] + V(0.9, -0.25, 1.7))])
lens_keys(c, [(ST0, 30), (ST1, 20)])
# 13 vahima: makro miya, crash zoom + silkinish
pT = at("panicT", MB + V(0.2, -0.35, 0.52))
c = shot_cam("panic", (0, 0, 0), pT, 18, 2.8, focus=pT)
path_keys(c, [(PA0, MB + V(2.4, -2.8, 1.5)), (PA0 + 5, MB + V(1.4, -1.8, 1.05)), (PA1, MB + V(1.2, -1.55, 0.95))])
lens_keys(c, [(PA0, 18), (PA0 + 5, 30), (PA1, 34)])
shake(c, PA0 + 4, PA1, 0.03, seed=13, decay=False)
# 14 tush + haqiqat: qiyshayib aylanuvchi kadr
c = shot_cam("mix", (0, 0, 0), None, 18, 4.0, focus=at("mixF", BW["Spine2"]))
look_keys(c, MX0, MX1, lambda t: V(-0.75, -1.05, 1.55).lerp(V(-0.95, -0.55, 1.35), ease(t)),
          lambda t: BW["Spine2"] + V(0, 0.1, 0.05), lambda t: -6 + 30 * ease(t))
# 15 sharpa: karavot sathidan, uning boshi ortidan
c = shot_cam("shadow", (0, 0, 0), parFace, 24, 2.8, focus=parFace)
path_keys(c, [(SH0, HEAD + V(0.32, 0.1, 0.24)), (SH1, HEAD + V(0.42, -0.12, 0.27))])
lens_keys(c, [(SH0, 24), (F_SHADOW, 28), (F_SHADOW + 4, 36), (SH1, 38)])
shake(c, F_SHADOW + 2, F_SHADOW + 12, 0.006, seed=15)
# 16 ko'krakda mavjudot: past yon burchak
CH1 = S["chest"][1]
chT = at("chestT", FACE2 + V(0, -0.2, 0.15))
c = shot_cam("chest", (0, 0, 0), chT, 20, 3.2, focus=parFace)
path_keys(c, [(CH0, FACE2 + V(0.98, 0.5, 0.98)), (CH1, FACE2 + V(0.82, 0.42, 0.82))])
lens_keys(c, [(CH0, 18), (CH1, 22)])
# 17 POV: mavjudot engashadi
haT = empty("hallucT"); cl_ = haT.constraints.new("COPY_LOCATION"); cl_.target = parFace
c = shot_cam("halluc", (0, 0, 0), haT, 18, 2.8, focus=parFace)
path_keys(c, [(HA0, FACE2 + V(0.3, 0.33, 0.17)), (HA1, FACE2 + V(0.22, 0.28, 0.2))])
lens_keys(c, [(HA0, 19), (F_LEAN + 10, 22), (F_LEAN + 16, 30), (HA1, 34)])
shake(c, F_LEAN + 14, HA1, 0.006, seed=17, decay=False)
for n, cam in CAMS.items():
    if n == "mix": continue
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 8) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.006, 0.01, 0.03, 1)
bg_dr = N.new("ShaderNodeBackground"); bg_dr.inputs[0].default_value = (0.2, 0.07, 0.35, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_dk.outputs[0], a1.inputs[0]); L.new(bg_dr.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    dk, dr = (0.0, 1.0) if n == "dream" else ((0.25, 0) if n in ("glitch", "replay", "block", "off", "wake", "stuck", "panic") else (0.15, 0))
    bg_dk.inputs[1].default_value = dk; bg_dk.inputs[1].keyframe_insert("default_value", frame=f)
    bg_dr.inputs[1].default_value = dr; bg_dr.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
NIGHT = ROOM
SPINE2 = at("spine2T", BW["Spine2"])
area("moon_key", (0.6, Y0 + 0.15, 2.0), 1.0, (0.5, 0.62, 1.0), lights_for([x for x in NIGHT if x != S["shadow"]], 70.0), target=SPINE2)
area("room_fill", (-0.4, 0.0, 2.5), 2.0, (0.35, 0.45, 0.85), lights_for(NIGHT, 4.0), target=at("rfT", (-0.6, -0.2, 0.4)))
area("face_fill", tuple(FACE + V(0.6, -0.7, 1.0)), 0.4, (0.55, 0.65, 1.0), lights_for(rng("hook", "scream", "finger", "chest", "halluc"), 5.0), target=faceT)
red = area("scream_red", tuple(FACE + V(-0.3, 0.5, 0.7)), 0.5, (1.0, 0.06, 0.03), [(1, 0)], target=faceT)
for f in range(SC0, SC1 + 1, 6):
    red.data.energy = 45 if (f - SC0) // 6 % 2 else 8; red.data.keyframe_insert("energy", frame=f)
red.data.energy = 0; red.data.keyframe_insert("energy", frame=SC1 + 1)
area("shadow_back", (0.1, Y0 + 0.35, 1.5), 0.8, (0.55, 0.65, 1.0), lights_for(rng("shadow"), 120.0), target=at("sbT", HEAD))
area("chest_rim", tuple(CHEST_P + V(-0.6, 1.4, 1.8)), 0.6, (0.7, 0.2, 1.0), lights_for(rng("chest", "halluc"), 70.0), target=at("crT", CHEST_P + V(0, 0, 0.8)))
for e_ in eyes:
    pl = point("eyeL_" + e_.name, (0, 0, 0), 0.01, (1.0, 0.08, 0.03), [(1, 0)], const=True)
    for f, v in ((F_SHADOW + 3, 0.4), (CH0, 0.25), (F_LEAN + 16, 0.8), (END, 0.8)): pl.data.energy = v; pl.data.keyframe_insert("energy", frame=f)
    cl = pl.constraints.new("COPY_LOCATION"); cl.target = e_
area("mix_purple", (-0.3, -0.8, 1.8), 1.5, (0.65, 0.25, 1.0), lights_for(rng("mix"), 35.0), target=SPINE2)
area("mix_pink", (-2.2, 1.2, 1.2), 1.0, (1.0, 0.35, 0.7), lights_for(rng("mix"), 20.0), target=SPINE2)
point("hand_fill", tuple(HAND + V(0.12, -0.08, 0.18)), 0.03, (0.6, 0.7, 1.0), lights_for(rng("finger"), 0.6))
# rentgen
area("X_rim", tuple(HEADC + V(-0.6, 0.6, 0.9)), 0.8, (0.3, 0.6, 1.0), lights_for(XR, 15.0), target=headE)
# makro miya
area("MB_key", tuple(MB + V(-1.2, -1.5, 2.2)), 1.2, (1.0, 0.85, 0.8), lights_for(PAN, 220.0), target=pT)
area("MB_rim", tuple(MB + V(1.0, 1.4, 1.4)), 1.0, (1.0, 0.1, 0.04), lights_for(PAN, 600.0), target=pT)
# tush
area("DR_key", tuple(DR + V(3.0, -6.0, 5.0)), 4.0, (1.0, 0.75, 0.9), lights_for(DRM, 900.0), target=drT)
area("DR_rim", tuple(DR + V(-3.0, 6.0, 3.0)), 3.0, (0.55, 0.35, 1.0), lights_for(DRM, 900.0), target=drT)

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
