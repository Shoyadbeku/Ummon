# Keskin o'rindan turish (ortostatik gipotenziya) — Zack D. Films uslubida 34.2 s video (821 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py va zack_test/falaj/falaj.py (yotoqxona, rentgen, impulslar);
# procedural yordamchilar: zack_test/burish/parts.py (miya, matematik tugunlar)
# Assetlar: zack_test/tools/get_turish.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/turish/turish.py --render
# Sinov: FRAMES=20,100,180,270,420,520,600,720,800 PCT=35 OUT=/tmp/claude-0/test/
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
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
END = 821
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "alarm"), (45, "jolt"), (78, "up"), (121, "drop"), (156, "brainless"), (219, "lying"), (247, "heart"),
         (298, "even"), (341, "standx"), (390, "gravity"), (482, "vessel"), (558, "fallback"), (612, "brainflow"),
         (687, "pov"), (749, "fall")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM = rng("alarm", "jolt", "up", "pov", "fall")
XR = rng("drop", "brainless", "lying", "heart", "even", "standx", "gravity", "brainflow")
MAC = rng("vessel", "fallback")
F_JOLT = 47            # "cho'chib"
F_RISE = 84            # sakrab turish boshlanadi ("bir soniyada")
F_RISE2 = 349          # rentgen: keskin turish
F_KESKIN = 139         # "keskin tushib"
F_MIYA = 157           # "miyani"
F_QONSIZ = 177         # "qonsiz"
F_YURAK = 249          # "yurak"
F_OYOQ = 429           # "oyoqlarga"
F_QORIN = 447          # "qorin"
F_ULGUR = 592          # "ulgurmasa"
F_KAMAY = 673          # "kamayib"
F_YIQIL = 789          # "yiqilib"
F_HIT = 812            # yerga urilish

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

def noisy(o, strength=0.05, scale=0.5, sub=0):
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
def M_(N, L, op, a=None, b=None, clamp=False): return P.math_n(N, L, op, a, b, clamp=clamp)

# ======================================================================
# 1) YOTOQXONA (ertalab, deraza orqali quyosh)
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.95, 0.88, 0.78))
X0, X1, Y0, Y1, HZ_ = -2.4, 2.0, -1.75, 1.6, 2.6
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
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
# deraza tashqarisi: kunduzgi osmon (soya bermaydi)
sky_m = bpy.data.materials.new("sky"); sky_m.use_nodes = True
N = sky_m.node_tree.nodes; L = sky_m.node_tree.links; N.remove(N["Principled BSDF"])
tcs = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tcs.outputs["Generated"], sep.inputs[0])
hor = N.new("ShaderNodeMix"); hor.data_type = "RGBA"; hor.inputs[6].default_value = (0.95, 0.9, 0.8, 1); hor.inputs[7].default_value = (0.35, 0.6, 1.0, 1)
L.new(sep.outputs["Y"], hor.inputs["Factor"])
em = N.new("ShaderNodeEmission"); L.new(hor.outputs[2], em.inputs["Color"]); em.inputs["Strength"].default_value = 4.0
L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
skyp = R_(plane("sky", (6, 4), (0.6, Y0 - 1.2, 1.6), sky_m, rot=(90, 0, 0)))
skyp.visible_shadow = False
# parda (deraza yonida)
cur_m = mat("curtain", (0.92, 0.85, 0.7), 0.8, sss=0.2)
for cx in (WX0 - 0.22, WX1 + 0.22):
    c_ = R_(box(f"curtain{cx:.1f}", (0.35, 0.05, 2.2), (cx, Y0 + 0.06, 1.25), cur_m))
    noisy(c_, 0.03, 0.08, sub=0)

DESK = Vector((0.6, -1.3, 0)); DESK_TOP = 0.715
R_(import_gltf(PH + "WoodenTable_01/WoodenTable_01.gltf", tuple(DESK), 0, (1.0, 1.1, 1.3)))
R_(import_gltf(PH + "modern_arm_chair_01/modern_arm_chair_01.gltf", (0.6, -0.5, 0), 0, 1.0))
R_(import_gltf(PH + "desk_lamp_arm_01/desk_lamp_arm_01.gltf", (1.25, -1.45, DESK_TOP), 200, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.65, -1.35, 0), 30, 0.9))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X1 - 0.02, 0.55, 0), -90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X1 - 0.15, 0.82, 1.03), -90, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (X0 + 0.03, 0.35, 1.45), 90, 1.0))

# --- karavot ---
BEDC = Vector((-1.6, 0.2, 0))
MT = 0.5                                           # matras usti
wood_m = mat("bed_wood", (0.38, 0.24, 0.14), 0.45, coat=0.2)
sheet_m = mat("sheet", (0.92, 0.93, 0.96), 0.75, sss=0.05)
duvet_m = bpy.data.materials.new("duvet"); duvet_m.use_nodes = True
N = duvet_m.node_tree.nodes; L = duvet_m.node_tree.links; b = N["Principled BSDF"]
tcd = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 6.0
L.new(tcd.outputs["Object"], wv.inputs["Vector"])
dmx = N.new("ShaderNodeMix"); dmx.data_type = "RGBA"; dmx.inputs[6].default_value = (0.75, 0.5, 0.35, 1); dmx.inputs[7].default_value = (0.9, 0.78, 0.62, 1)
L.new(M_(N, L, "GREATER_THAN", wv.outputs["Fac"], 0.5), dmx.inputs["Factor"]); L.new(dmx.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.85; b.inputs["Sheen Weight"].default_value = 0.6
R_(box("bed_frame", (1.5, 2.1, 0.2), tuple(BEDC + Vector((0, 0, 0.18))), wood_m, bevel=0.02))
R_(box("bed_head", (1.55, 0.08, 1.0), tuple(BEDC + Vector((0, 1.09, 0.5))), wood_m, bevel=0.02))
R_(box("mattress", (1.42, 2.0, 0.22), tuple(BEDC + Vector((0, 0.0, MT - 0.11))), sheet_m, bevel=0.06))
for sx in (-0.33, 0.33):
    pl = R_(box(f"pillow{sx}", (0.6, 0.38, 0.12), tuple(BEDC + Vector((sx, 0.86, MT + 0.02))), sheet_m, bevel=0.06))
    noisy(pl, 0.02, 0.2)
# ko'rpa: yotganda (1–77) tanada, turgandan keyin chetga surilgan
duv = R_(box("duvet", (1.56, 1.22, 0.3), tuple(BEDC + Vector((0, -0.43, MT + 0.15))), duvet_m, bevel=0.08))
_bm = bmesh.new(); _bm.from_mesh(duv.data)
bmesh.ops.subdivide_edges(_bm, edges=_bm.edges[:], cuts=10, use_grid_fill=True); _bm.to_mesh(duv.data); _bm.free()
for v in duv.data.vertices:
    if abs(v.co.x) > 0.7: v.co.z -= 0.16
    if v.co.y < -0.5: v.co.z -= 0.08
    if v.co.y > 0.5: v.co.z -= 0.05
sub = duv.modifiers.new("s", "SUBSURF"); sub.levels = 1; sub.render_levels = 2; sub.show_viewport = False
noisy(duv, 0.06, 0.25)
key(duv, 1, loc=tuple(duv.location), rot=(0, 0, 0), scale=(1, 1, 1))
key(duv, 77, loc=tuple(duv.location), rot=(0, 0, 0), scale=(1, 1, 1))
key(duv, 78, loc=tuple(duv.location + Vector((-0.35, -0.2, -0.05))), rot=(0, 0, -8), scale=(0.75, 1.0, 0.8))
interp(duv, "CONSTANT")
NS = BEDC + Vector((1.05, 0.85, 0))
R_(box("nightstand", (0.45, 0.4, 0.5), tuple(NS + Vector((0, 0, 0.25))), wood_m, bevel=0.01))
CLOCK = NS + Vector((0.0, -0.02, 0.5))
clock = R_(import_gltf(PH + "alarm_clock_01/alarm_clock_01.gltf", tuple(CLOCK), 160, 1.3))
for m_ in bpy.data.materials:                     # oyna ciferblatni to'smasin
    if m_.name.startswith("alarm_clock_01_Glass"):
        bg_ = m_.node_tree.nodes["Principled BSDF"]
        for l_ in list(bg_.inputs["Alpha"].links): m_.node_tree.links.remove(l_)
        bg_.inputs["Alpha"].default_value = 0.06; bg_.inputs["Roughness"].default_value = 0.05
# budilnik jiringlaydi: titrash + sakrash (1–60)
rc = random.Random(3)
A0, A1 = S["alarm"]
for f in range(1, 70, 1):
    on = f < 66
    jx = rc.uniform(-1, 1) * 4.0 * on; jy = rc.uniform(-1, 1) * 3.0 * on
    hop = (0.004 if f % 2 == 0 else 0.0) * on
    key(clock, f, loc=tuple(CLOCK + Vector((rc.uniform(-0.002, 0.002) * on, rc.uniform(-0.002, 0.002) * on, hop))), rot=(jx, jy, 160 + rc.uniform(-3, 3) * on))
interp(clock, "LINEAR")
rug = R_(plane("rug", (1.6, 1.2), (-0.1, -0.2, 0.004), mat("rug", (0.55, 0.2, 0.14), 0.95)))
noisy(rug, 0.004, 0.05)
R_(box("wall_door", (0.9, 0.04, 2.05), (-0.6, Y1 - 0.01, 1.025), mat("door", (0.6, 0.45, 0.32), 0.5, coat=0.2), bevel=0.01))

for o in room_objs: vis(o, ROOM)

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

MEG_BED = BEDC + Vector((0.05, 0.28, MT - 0.95))
EDGE = Vector((BEDC.x + 0.62, BEDC.y - 0.05, MT - 0.53))      # karavot chetida o'tirish (yuzi +X)
FALL = Vector((-0.15, -0.25, 0.0))
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)

LAY = A_("Laying_Idle.fbx")
S2S = A_("Sit_To_Stand.fbx", inplace=False)
DIZ = A_("Dizzy_Idle.fbx")
STU = A_("Injured_Stumble_Idle.fbx")
DIE = A_("Dying_10.fbx")
def alen(act): return (act.frame_range[1] - act.frame_range[0])
def seg(act, f0, f1, speed=1.0, src0=None, cyc=False, blend=0):
    src = (act.frame_range[0] + src0, act.frame_range[1]) if src0 else None
    s = mc.add_strip(meg, act, f0, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = blend; s.blend_out = 0
    if cyc:
        s.repeat = (f1 + 1 - f0) / max(1e-3, (s.frame_end - s.frame_start))
    elif s.frame_end < f1 + 1:                                  # oxirgi pozani ushlab turish
        e = act.frame_range[1]
        h = mc.add_strip(meg, act, int(s.frame_end), hold=False, src=(e - 1, e))
        h.use_auto_blend = False; h.blend_in = h.blend_out = 0
        h.scale = max(0.01, (f1 + 1 - h.frame_start) / 1.0)
    return s
SPD = 1.35
def s2s_src(rise_frame, shot0):
    """Sit_To_Stand: ko'tarilish (asl 24fps-kadr ~15) rise_frame ga tushadigan qilib boshini kesish (aksiya kadrlarida)"""
    start = rise_frame - 15 / SPD
    return max(0.0, (shot0 - start) * SPD / 0.8)
place(mroot, 1, tuple(MEG_BED), 0)
seg(LAY, 1, 77, cyc=True)
place(mroot, 78, tuple(EDGE), 90)
seg(S2S, 78, 120, speed=SPD, src0=s2s_src(F_RISE, 78))
# rentgen tik turgan qism: turish oxiridagi joy (keyin hisoblanadi)
seg(DIZ, 121, 218, cyc=True, speed=0.8)
place(mroot, 219, tuple(MEG_BED), 0)
seg(LAY, 219, 340, cyc=True)
place(mroot, 341, tuple(EDGE), 90)
seg(S2S, 341, 389, speed=SPD, src0=s2s_src(F_RISE2, 341))
seg(DIZ, 390, 748, cyc=True, speed=0.8)
place(mroot, 749, tuple(FALL), 0)
seg(STU, 749, 782, cyc=True, speed=1.1)
seg(DIE, 777, END, speed=1.25, blend=6)
interp(mroot, "CONSTANT")
# turgandan keyingi joy (S2S oxiridagi Hips)
sc.frame_set(119); bpy.context.view_layer.update()
H_END = meg.matrix_world @ meg.pose.bones["mixamorig:Hips"].head
STAND = Vector((H_END.x, H_END.y, EDGE.z))
for f in (121, 390):
    place(mroot, f, tuple(STAND), 90)
interp(mroot, "CONSTANT")
print("STAND", STAND)

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
# cho'chish: bosh yostiqdan keskin ko'tariladi
JOLT = float(os.environ.get("JOLT", 1.0))
for b in ("Neck", "Head", "Spine2"): pq(meg, b, 1, (0, 0, 0)); pq(meg, b, F_JOLT - 1, (0, 0, 0))
pq(meg, "Spine2", F_JOLT + 3, (JOLT * 10, 0, 0)); pq(meg, "Neck", F_JOLT + 3, (JOLT * 22, 0, 0)); pq(meg, "Head", F_JOLT + 3, (JOLT * 14, -6, 0))
pq(meg, "Spine2", 77, (JOLT * 12, 0, 0)); pq(meg, "Neck", 77, (JOLT * 24, 0, 0)); pq(meg, "Head", 77, (JOLT * 12, 8, 0))
for b in ("Neck", "Head", "Spine2"): pq(meg, b, 78, (0, 0, 0))
overlay(meg, "meg_overlay")

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.07, 0.1), headE)
def W(b, f):
    sc.frame_set(f); return (meg.matrix_world @ meg.pose.bones["mixamorig:" + b].head).copy()
BONES = ("Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "HeadTop_End", "LeftFoot", "RightFoot", "LeftLeg", "LeftUpLeg", "LeftHand")
BL = {b: W(b, 260) for b in BONES}          # rentgen yotgan
BS = {b: W(b, 420) for b in BONES}          # rentgen tik
BR = {b: W(b, 30) for b in BONES}           # xonada yotgan
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE_BED = wpos(faceT, 30); FACE_JOLT = wpos(faceT, 70)
FACE_S = wpos(faceT, 420)
print("FACE_BED", FACE_BED, "STAND head", BS["Head"], "LAY head", BL["Head"])

# --- rentgen nusxa (shaffof ko'k tana) ---
def xr_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", 1.0)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = M_(N, L, "POWER", lw.outputs["Facing"], 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.7, 1.0, 1)
    L.new(M_(N, L, "ADD", M_(N, L, "MULTIPLY", fac, gl), 0.01), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(M_(N, L, "ADD", M_(N, L, "MULTIPLY", fac, 0.55), 0.03, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
xbody = xr_mat("xr_body")
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name or "Hair" in o.name or "hair" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
POV = rng("pov")
for o in mmeshes: vis(o, rng("alarm", "jolt", "up", "fall"), recursive=False)

# ======================================================================
# 3) ARTERIYALAR: Megan skeletiga bog'langan quvurlar (Armature), "s" = yurakdan masofa (m)
# ======================================================================
arm_d = meg.data
def bl(bone, off=(0, 0, 0)):
    """suyak fazosidagi siljish (metr; X chap, Y suyak bo'ylab, Z old) -> armatura fazosi (sm)"""
    b = arm_d.bones["mixamorig:" + bone]
    return b.matrix_local @ (Vector(off) * 100.0)
def catmull(pts, step=1.5):
    out = []
    P_ = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n = max(2, int((p2 - p1).length / step))
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1]); return out
DEF = [b for b in arm_d.bones if b.use_deform]
def nearest_bone(p):
    best = None; bd = 1e9
    for b in DEF:
        a, c = b.head_local, b.tail_local; ab = c - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
        d = (a + ab * t - p).length
        if d < bd: bd, best = d, b.name
    return best
VERTS = []; FACES = []; SVAL = []; GROUPS = []
def vessel(spec, r0, r1=None, s0=0.0, jitter=0.0, seed=0):
    """spec: [(bone, off), ...] -> quvur (armatura fazosida). r: metr."""
    rj = random.Random(seed)
    pts = [bl(b, o) for b, o in spec]
    pts = catmull(pts, 1.2)
    if jitter:
        pts = [p + Vector((rj.uniform(-1, 1), rj.uniform(-1, 1), rj.uniform(-1, 1))) * jitter * 100 * (0 < i < len(pts) - 1) for i, p in enumerate(pts)]
    n = len(pts); RES = 8
    L_ = [0.0]
    for a, b in zip(pts, pts[1:]): L_.append(L_[-1] + (b - a).length)
    tot = L_[-1] or 1.0
    t_prev = (pts[1] - pts[0]).normalized()
    nrm = t_prev.orthogonal().normalized()
    base = len(VERTS)
    for i, p in enumerate(pts):
        t = (pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
        if t.length < 1e-6: t = t_prev
        q = t_prev.rotation_difference(t); nrm = (q @ nrm); nrm = (nrm - t * nrm.dot(t)).normalized(); t_prev = t
        bnm = t.cross(nrm)
        rr = (r0 + ((r1 if r1 is not None else r0 * 0.55) - r0) * (L_[i] / tot)) * 100
        g = nearest_bone(p)
        for k in range(RES):
            a = 2 * math.pi * k / RES
            VERTS.append(p + (nrm * math.cos(a) + bnm * math.sin(a)) * rr); SVAL.append(s0 + L_[i] / 100.0); GROUPS.append(g)
    for i in range(n - 1):
        for k in range(RES):
            a = base + i * RES + k; b2 = base + i * RES + (k + 1) % RES
            FACES.append((a, b2, b2 + RES, a + RES))
HEART_OFF = ("Spine2", (0.025, 0.0, 0.035))
HEART = [HEART_OFF]
for sx in (-1, 1):
    side = "Left" if sx > 0 else "Right"
    # uyqu arteriyasi -> miya
    vessel(HEART + [("Spine2", (sx * 0.01, 0.1, 0.03)), ("Neck", (sx * 0.022, 0.0, 0.025)), ("Neck", (sx * 0.025, 0.07, 0.03)),
                    ("Head", (sx * 0.03, 0.03, 0.045)), ("Head", (sx * 0.04, 0.09, 0.04)), ("Head", (sx * 0.03, 0.15, 0.0)),
                    ("Head", (sx * 0.015, 0.17, -0.05))], 0.0042, 0.0025, seed=sx)
    vessel([("Head", (sx * 0.04, 0.09, 0.04)), ("Head", (sx * 0.06, 0.11, 0.0)), ("Head", (sx * 0.055, 0.12, -0.06))], 0.0025, 0.0015, s0=0.33)
    vessel([("Head", (sx * 0.03, 0.03, 0.045)), ("Head", (sx * 0.05, 0.05, 0.07)), ("Head", (sx * 0.03, 0.07, 0.1))], 0.0022, 0.0012, s0=0.27)
    # qo'l
    vessel(HEART + [("Spine2", (sx * 0.05, 0.13, 0.02)), (side + "Shoulder", (0, 0.07, 0.0)), (side + "Arm", (0, 0.0, 0.0)),
                    (side + "Arm", (0, 0.14, 0.01)), (side + "ForeArm", (0, 0.0, 0.01)), (side + "ForeArm", (0, 0.13, 0.01)),
                    (side + "Hand", (0, 0.0, 0.0)), (side + "HandMiddle1", (0, 0, 0)), (side + "HandMiddle3", (0, 0, 0))], 0.0045, 0.0018, seed=sx + 3)
    # oyoq (aorta pastga)
    vessel(HEART + [("Spine2", (0.0, -0.03, 0.03)), ("Spine1", (0.0, 0.0, 0.035)), ("Spine", (0.0, 0.0, 0.04)), ("Hips", (sx * 0.03, 0.02, 0.04)),
                    (side + "UpLeg", (0, 0.0, 0.03)), (side + "UpLeg", (0, 0.2, 0.025)), (side + "Leg", (0, 0.0, -0.01)),
                    (side + "Leg", (0, 0.2, 0.0)), (side + "Foot", (0, 0.0, 0.0)), (side + "ToeBase", (0, 0, 0))], 0.0062, 0.0028, seed=sx + 7)
    # qorin tomirlari (ichak, buyrak)
    for k, (yy, zz, ww) in enumerate(((0.04, 0.05, 0.07), (-0.02, 0.06, 0.1), (0.08, 0.02, 0.09))):
        vessel([("Spine1", (0.0, yy, 0.035)), ("Spine1", (sx * ww * 0.5, yy - 0.02, zz + 0.02)), ("Spine", (sx * ww, yy + 0.03, zz)),
                ("Spine", (sx * ww * 0.7, yy - 0.04, zz + 0.03)), ("Hips", (sx * ww * 0.4, 0.06 + yy * 0.3, zz + 0.04))], 0.003, 0.0018, s0=0.25 + k * 0.04, jitter=0.006, seed=k * 11 + sx)
    # son va boldirdagi shoxchalar
    for bn, s0 in ((side + "UpLeg", 0.55), (side + "Leg", 0.95)):
        vessel([(bn, (0, 0.05, 0.025)), (bn, (sx * 0.03, 0.15, 0.03)), (bn, (sx * 0.035, 0.3, 0.0))], 0.0028, 0.0014, s0=s0, jitter=0.004, seed=len(VERTS))
    for bn, s0 in ((side + "Arm", 0.3), (side + "ForeArm", 0.5)):
        vessel([(bn, (0, 0.04, 0.01)), (bn, (0.015, 0.12, 0.02)), (bn, (0.0, 0.22, 0.025))], 0.0022, 0.0012, s0=s0, jitter=0.003, seed=len(VERTS) + 1)
vme = bpy.data.meshes.new("arteries"); vme.from_pydata([tuple(v) for v in VERTS], [], FACES); vme.update()
for p in vme.polygons: p.use_smooth = True
att = vme.attributes.new("s", "FLOAT", "POINT")
for i, v in enumerate(SVAL): att.data[i].value = v
art = bpy.data.objects.new("arteries", vme); sc.collection.objects.link(art)
art.parent = meg; art.matrix_parent_inverse = Matrix.Identity(4)
vg = {}
for i, g in enumerate(GROUPS):
    if g not in vg: vg[g] = art.vertex_groups.new(name=g)
    vg[g].add([i], 1.0, "REPLACE")
am = art.modifiers.new("arm", "ARMATURE"); am.object = meg
print("arteries verts", len(VERTS))

def vessel_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.4
    sa = N.new("ShaderNodeAttribute"); sa.attribute_name = "s"; s = sa.outputs["Fac"]
    geo = N.new("ShaderNodeNewGeometry"); sz = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sz.inputs[0]); z = sz.outputs["Z"]
    phase = value_node(m, "phase", 0.0); dens = value_node(m, "dens", 5.0); flow = value_node(m, "flow", 6.0)
    glow = value_node(m, "glow", 0.6); lvl = value_node(m, "lvl", 9.0); drain = value_node(m, "drain", 0.0)
    low = value_node(m, "low", 0.0); lowz = value_node(m, "lowz", 0.0)
    p = M_(N, L, "FRACT", M_(N, L, "SUBTRACT", M_(N, L, "MULTIPLY", s, dens), phase))
    pulse = M_(N, L, "POWER", p, 7.0)
    filled = M_(N, L, "DIVIDE", M_(N, L, "SUBTRACT", lvl, z), 0.12, clamp=True)
    fill = M_(N, L, "SUBTRACT", 1.0, M_(N, L, "MULTIPLY", drain, M_(N, L, "SUBTRACT", 1.0, filled)))
    lowf = M_(N, L, "MULTIPLY", M_(N, L, "DIVIDE", M_(N, L, "SUBTRACT", lowz, z), 0.25, clamp=True), low)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; cm.inputs[6].default_value = (0.16, 0.13, 0.22, 1); cm.inputs[7].default_value = (0.75, 0.03, 0.02, 1)
    L.new(fill, cm.inputs["Factor"]); L.new(cm.outputs[2], b.inputs["Base Color"])
    ce = N.new("ShaderNodeMix"); ce.data_type = "RGBA"; ce.inputs[6].default_value = (0.25, 0.3, 0.55, 1); ce.inputs[7].default_value = (1.0, 0.07, 0.03, 1)
    L.new(fill, ce.inputs["Factor"]); L.new(ce.outputs[2], b.inputs["Emission Color"])
    e = M_(N, L, "ADD", glow, M_(N, L, "MULTIPLY", flow, pulse))
    e = M_(N, L, "MULTIPLY", e, M_(N, L, "ADD", 0.08, M_(N, L, "MULTIPLY", fill, 0.92)))
    e = M_(N, L, "ADD", e, M_(N, L, "MULTIPLY", lowf, M_(N, L, "ADD", 2.5, M_(N, L, "MULTIPLY", pulse, 6.0))))
    L.new(e, b.inputs["Emission Strength"])
    return m
vmat = vessel_mat("vessel_m"); vme.materials.append(vmat)
vis(art, XR, recursive=False)

# --- yurak (Spine2 ga bog'langan) ---
heartE = child_of_bone("heartE", meg, HEART_OFF[0], HEART_OFF[1])
heart_m = mat("heart_m", (0.5, 0.02, 0.015), 0.35, coat=0.6, sss=0.15, sss_scale=0.004, emit=0.0, emit_col=(1.0, 0.08, 0.04))
heart_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.06, 0.03, 1)
hb = heart_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
heart = sphere("heart", 0.042, (0, 0, 0), heart_m, scale=(0.95, 1.2, 0.85), sub=4, parent=heartE)
heart.rotation_euler = (R(-15), R(25), R(-20))
for v in heart.data.vertices:                     # cho'qqi (apex) pastga-chapga torayadi
    if v.co.y < 0: v.co.x *= 1 + v.co.y * 4; v.co.z *= 1 + v.co.y * 4
noisy(heart, 0.004, 0.02)
for sx_, sy_ in ((-0.018, 0.04), (0.012, 0.045)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.009, depth=0.04, location=(sx_, sy_ + 0.01, 0.0))
    co = bpy.context.object; co.name = "heart_vessel"; co.data.materials.append(heart_m); co.parent = heartE; co.rotation_euler = (R(-90), 0, 0)
    for p in co.data.polygons: p.use_smooth = True
    vis(co, XR, recursive=False)
vis(heart, XR, recursive=False)
# yurak urishi va impulslar: har urishda phase +1
BEATS = []
f = 2.0
while f < END:
    per = 19 if (S["lying"][0] <= f < S["standx"][0]) else 15
    BEATS.append(int(f)); f += per
ph = 0.0
val_key(vmat, "phase", 1, 0.0)
for fb in BEATS:
    heart.scale = (0.95, 1.2, 0.85); heart.keyframe_insert("scale", frame=fb)
    heart.scale = (1.08, 1.32, 0.97); heart.keyframe_insert("scale", frame=fb + 2)
    heart.scale = (0.9, 1.12, 0.8); heart.keyframe_insert("scale", frame=fb + 5)
    hb.default_value = 1.2; hb.keyframe_insert("default_value", frame=fb)
    hb.default_value = 5.0; hb.keyframe_insert("default_value", frame=fb + 2)
    hb.default_value = 1.2; hb.keyframe_insert("default_value", frame=fb + 8)
    val_key(vmat, "phase", fb, ph); val_key(vmat, "phase", fb + 6, ph + 0.85); ph += 1.0
interp(vmat.node_tree, "LINEAR")

# --- miya ---
def brain_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15; b.inputs["Roughness"].default_value = 0.4
    gl = value_node(m, "glow", 1.0); blood = value_node(m, "blood", 1.0)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; c.inputs[6].default_value = (0.32, 0.32, 0.38, 1); c.inputs[7].default_value = (0.85, 0.4, 0.45, 1)
    L.new(blood, c.inputs["Factor"]); L.new(c.outputs[2], b.inputs["Base Color"])
    ce = N.new("ShaderNodeMix"); ce.data_type = "RGBA"; ce.inputs[6].default_value = (0.3, 0.35, 0.5, 1); ce.inputs[7].default_value = (1.0, 0.35, 0.45, 1)
    L.new(blood, ce.inputs["Factor"]); L.new(ce.outputs[2], b.inputs["Emission Color"])
    fl = M_(N, L, "POWER", nz.outputs["Fac"], 4.0)
    k = M_(N, L, "ADD", 0.1, M_(N, L, "MULTIPLY", blood, 0.9))
    L.new(M_(N, L, "MULTIPLY", M_(N, L, "MULTIPLY", M_(N, L, "ADD", fl, 0.15), gl), k), b.inputs["Emission Strength"])
    return m
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
xb_m = brain_mat("xbrain_m")
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, XR)
# qon miqdori: tushish (drop/brainless), yotganda to'liq, turganda yana kamayadi
for f_, v in ((1, 1.0), (F_KESKIN, 1.0), (F_MIYA + 2, 0.45), (F_QONSIZ, 0.15), (S["lying"][0] - 1, 0.15), (S["lying"][0], 1.0),
              (F_RISE2 + 10, 1.0), (F_OYOQ, 0.35), (S["gravity"][1], 0.3), (S["brainflow"][0], 0.9), (F_KAMAY - 8, 0.6), (F_KAMAY + 6, 0.05), (END, 0.05)):
    val_key(xb_m, "blood", f_, v)
rf = random.Random(5)
for f_ in range(F_QONSIZ - 4, S["brainless"][1], 5): val_key(xb_m, "glow", f_, rf.choice((0.4, 1.2, 0.7)))
val_key(xb_m, "glow", S["lying"][0], 1.0)
for f_ in range(F_KAMAY - 6, S["brainflow"][1], 4): val_key(xb_m, "glow", f_, rf.choice((0.3, 1.0, 0.6)))
interp(xb_m.node_tree, "LINEAR")

# --- arteriya parametrlari kadrlar bo'yicha ---
def vk(name, pairs):
    for f_, v in pairs: val_key(vmat, name, f_, v)
HZ = BS["Head"].z
vk("drain", [(1, 1.0), (S["lying"][0] - 1, 1.0), (S["lying"][0], 0.0), (F_RISE2 + 6, 0.0), (F_RISE2 + 7, 1.0), (END, 1.0)])
vk("lvl", [(1, 2.2), (F_KESKIN - 2, 2.2), (F_KESKIN + 14, HZ - 0.12), (S["brainless"][1], HZ - 0.2), (S["lying"][0], 9.0),
           (F_RISE2 + 6, 2.2), (S["gravity"][0] + 4, 2.0), (F_OYOQ, 1.05), (S["gravity"][1], 0.95),
           (S["brainflow"][0], HZ + 0.25), (F_KAMAY - 10, HZ + 0.1), (F_KAMAY + 8, BS["Neck"].z - 0.05), (END, BS["Neck"].z - 0.05)])
vk("low", [(1, 0.0), (F_OYOQ - 14, 0.0), (F_OYOQ + 6, 1.0), (S["gravity"][1], 1.0), (S["gravity"][1] + 1, 0.0)])
vk("lowz", [(1, BS["LeftLeg"].z + 0.25), (F_QORIN - 2, BS["LeftLeg"].z + 0.25), (F_QORIN + 8, BS["Spine1"].z), (END, BS["Spine1"].z)])
vk("flow", [(1, 6.0), (S["lying"][0], 3.5), (S["standx"][0], 6.0), (S["brainflow"][0], 6.0), (F_KAMAY, 2.0), (END, 1.5)])
vk("dens", [(1, 5.0), (S["brainflow"][0], 5.0), (F_KAMAY, 2.0), (END, 2.0)])
interp(vmat.node_tree, "LINEAR")
xbody.node_tree.nodes["glow"].outputs[0].default_value = 0.9

# --- tortishish strelkalari (gravity) ---
arrow_m = bpy.data.materials.new("arrow"); arrow_m.use_nodes = True
N = arrow_m.node_tree.nodes; L = arrow_m.node_tree.links; N.remove(N["Principled BSDF"])
ae = N.new("ShaderNodeEmission"); ae.inputs["Color"].default_value = (1.0, 0.55, 0.08, 1); ae.inputs["Strength"].default_value = 3.5
L.new(ae.outputs[0], N["Material Output"].inputs["Surface"])
def chevron(name, w=0.12, h=0.07, t=0.03, d=0.01):
    pts = [(-w, h), (0, 0), (w, h), (w, h + t), (0, t), (-w, h + t)]
    me = bpy.data.meshes.new(name); verts = [(x, -d / 2, z) for x, z in pts] + [(x, d / 2, z) for x, z in pts]
    n = len(pts); faces = [list(range(n))[::-1], list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    me.from_pydata(verts, [], faces); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(arrow_m); return o
GV0, GV1 = S["gravity"]
ARROWS = []
for side, dx in (("L", -0.42), ("R", 0.42)):
    for k in range(4):
        a_ = chevron(f"arrow{side}{k}")
        a_.rotation_euler = (0, 0, R(90))                  # kameraga qarab (kamera +X tomonda)
        z0 = BS["Head"].z + 0.1 - k * 0.28
        f0 = GV0 + 6 + k * 3
        x0 = STAND.x; y0 = STAND.y + dx
        for cyc in range(4):
            fa = f0 + cyc * 22
            key(a_, fa, loc=(x0, y0, z0 + 0.1), scale=0.0); key(a_, fa + 4, scale=1.0)
            key(a_, fa + 18, loc=(x0, y0, z0 - 0.35), scale=1.0); key(a_, fa + 21, scale=0.0)
        interp(a_, "LINEAR")
        vis(a_, [(GV0 + 6, GV1)], recursive=False); ARROWS.append(a_)

# ======================================================================
# 4) MAKRO QON TOMIRI (kesim)
# ======================================================================
MV = Vector((40, 0, 0))
mac = empty("macro_grp")
wall_mm = bpy.data.materials.new("vwall"); wall_mm.use_nodes = True
N = wall_mm.node_tree.nodes; L = wall_mm.node_tree.links; b = N["Principled BSDF"]
tcw = N.new("ShaderNodeTexCoord"); nw = N.new("ShaderNodeTexNoise"); nw.inputs["Scale"].default_value = 3.0; nw.inputs["Detail"].default_value = 6
L.new(tcw.outputs["Object"], nw.inputs["Vector"])
wc = N.new("ShaderNodeMix"); wc.data_type = "RGBA"; wc.inputs[6].default_value = (0.55, 0.1, 0.12, 1); wc.inputs[7].default_value = (0.85, 0.35, 0.35, 1)
L.new(nw.outputs["Fac"], wc.inputs["Factor"]); L.new(wc.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.8; b.inputs["Coat Roughness"].default_value = 0.1
b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.05
bpw = N.new("ShaderNodeBump"); bpw.inputs["Strength"].default_value = 0.3; L.new(nw.outputs["Fac"], bpw.inputs["Height"]); L.new(bpw.outputs[0], b.inputs["Normal"])
VR = 0.5; VH = 9.0
def half_tube(name, r, z0, z1, rings, segs=72, amin=-25, amax=205, m=None):
    verts = []; faces = []
    for i in range(rings + 1):
        z = z0 + (z1 - z0) * i / rings
        for j in range(segs + 1):
            a = R(amin + (amax - amin) * j / segs)
            verts.append((r * math.cos(a), r * math.sin(a), z))
    W_ = segs + 1
    for i in range(rings):
        for j in range(segs): faces.append((i * W_ + j, i * W_ + j + 1, (i + 1) * W_ + j + 1, (i + 1) * W_ + j))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    if m: me.materials.append(m)
    return o
vt = half_tube("vtube", VR, -VH / 2, VH / 2, 90, m=wall_mm); vt.parent = mac; vt.location = MV
so = vt.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.06; so.offset = 1.0
noisy(vt, 0.025, 0.3)
mus_m = bpy.data.materials.new("muscle"); mus_m.use_nodes = True
N = mus_m.node_tree.nodes; L = mus_m.node_tree.links; b = N["Principled BSDF"]
tcm = N.new("ShaderNodeTexCoord"); wvm = N.new("ShaderNodeTexWave"); wvm.inputs["Scale"].default_value = 30.0; wvm.wave_type = "BANDS"
L.new(tcm.outputs["Object"], wvm.inputs["Vector"])
mc_ = N.new("ShaderNodeMix"); mc_.data_type = "RGBA"; mc_.inputs[6].default_value = (0.45, 0.06, 0.08, 1); mc_.inputs[7].default_value = (0.75, 0.2, 0.2, 1)
L.new(wvm.outputs["Fac"], mc_.inputs["Factor"]); L.new(mc_.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.5
b.inputs["Emission Color"].default_value = (1.0, 0.2, 0.1, 1)
mglow = b.inputs["Emission Strength"]
RINGS = []
for k in range(10):
    z = -VH / 2 + 0.5 + k * 0.85
    bpy.ops.mesh.primitive_torus_add(major_radius=VR + 0.08, minor_radius=0.065, major_segments=64, minor_segments=12, location=(0, 0, 0))
    t_ = bpy.context.object; t_.name = f"mring{k}"
    bm_ = bmesh.new(); bm_.from_mesh(t_.data)
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if -155 < math.degrees(math.atan2(v.co.y, v.co.x)) < -25], context="VERTS")
    bm_.to_mesh(t_.data); bm_.free()
    for p in t_.data.polygons: p.use_smooth = True
    t_.data.materials.append(mus_m); t_.parent = mac; t_.location = MV + Vector((0, 0, z)); RINGS.append(t_)
VE0, VE1 = S["vessel"]; FB0, FB1 = S["fallback"]
for k, t_ in enumerate(RINGS):
    key(t_, 1, scale=(1, 1, 1))
    f0 = VE0 + 4 + k * 5
    while f0 < VE1 + 10:
        key(t_, f0, scale=(1, 1, 1)); key(t_, f0 + 8, scale=(0.86, 0.86, 1.15)); key(t_, f0 + 18, scale=(1, 1, 1))
        f0 += 34
    f0 = FB0 + k * 6
    while f0 < FB1:
        key(t_, f0, scale=(1, 1, 1)); key(t_, f0 + 10, scale=(0.97, 0.97, 1.03)); key(t_, f0 + 22, scale=(1, 1, 1))
        f0 += 30
for f_, v in ((1, 0.0), (VE0, 0.3), (FB0, 0.3), (F_ULGUR, 0.05)): mglow.default_value = v; mglow.keyframe_insert("default_value", frame=f_)
# qizil qon tanachalari (bikonkav disk)
rbc_me = bpy.data.meshes.new("rbc")
bm_ = bmesh.new(); bmesh.ops.create_uvsphere(bm_, u_segments=32, v_segments=16, radius=1.0)
for v in bm_.verts:
    r = math.sqrt(v.co.x ** 2 + v.co.y ** 2)
    th = 0.42 * (0.28 + 0.72 * min(1.0, r) ** 2) * math.sqrt(max(0.0, 1 - min(1.0, r) ** 2)) + 0.02
    v.co.z = th if v.co.z > 0 else -th
bm_.to_mesh(rbc_me); bm_.free()
for p in rbc_me.polygons: p.use_smooth = True
rbc_m = mat("rbc_m", (0.6, 0.02, 0.02), 0.3, coat=0.7, sss=0.4, sss_scale=0.02)
rbc_me.materials.append(rbc_m)
rr_ = random.Random(21)
CELLS = []
for i in range(170):
    o = bpy.data.objects.new(f"rbc{i}", rbc_me); sc.collection.objects.link(o); o.parent = mac
    o.scale = (0.085,) * 3
    a = rr_.uniform(R(-20), R(200)); rad = rr_.uniform(0, VR - 0.12)
    x, y = rad * math.cos(a), rad * math.sin(a)
    z0 = rr_.uniform(-3.4, 2.2)
    up1 = rr_.uniform(1.1, 1.6); up2 = up1 + rr_.uniform(0.05, 0.2); dn = rr_.uniform(1.0, 1.6)
    r0 = (rr_.uniform(0, 360), rr_.uniform(0, 360), rr_.uniform(0, 360))
    def P_(z): return tuple(MV + Vector((x, y, z)))
    key(o, VE0, loc=P_(z0), rot=r0)
    key(o, VE1, loc=P_(z0 + up1), rot=(r0[0] + 90, r0[1] + 40, r0[2]))
    key(o, FB0 + 14, loc=P_(z0 + up2), rot=(r0[0] + 110, r0[1] + 50, r0[2]))
    key(o, FB1, loc=P_(z0 + up2 - dn), rot=(r0[0] + 200, r0[1] + 120, r0[2] + 40))
    for fc in fcurves(o):
        for k_ in fc.keyframe_points:
            k_.interpolation = "BEZIER"
    CELLS.append(o)
# plazmadagi mayda zarralar (trombotsit)
plt_m = mat("plt", (0.95, 0.75, 0.6), 0.4, emit=0.3, emit_col=(1, 0.6, 0.4))
for i in range(90):
    a = rr_.uniform(R(-20), R(200)); rad = rr_.uniform(0, VR - 0.08)
    p = MV + Vector((rad * math.cos(a), rad * math.sin(a), rr_.uniform(-3.5, 3.0)))
    o = sphere(f"plt{i}", rr_.uniform(0.008, 0.018), tuple(p), plt_m, sub=1, parent=mac)
    key(o, VE0, loc=tuple(p)); key(o, VE1, loc=tuple(p + Vector((0, 0, 1.3)))); key(o, FB1, loc=tuple(p + Vector((0, 0, 0.2))))
# makro: pastga strelka ("ulgurmasa")
MARROWS = []
for k in range(3):
    a_ = chevron(f"marrow{k}", 0.35, 0.2, 0.09, 0.03); a_.parent = mac
    a_.rotation_euler = (0, 0, 0)
    pz = 1.3 - k * 0.7
    key(a_, F_ULGUR - 8 + k * 3, loc=tuple(MV + Vector((0.95, -0.3, pz + 0.3))), scale=0.0)
    key(a_, F_ULGUR - 4 + k * 3, scale=1.0)
    key(a_, FB1, loc=tuple(MV + Vector((0.95, -0.3, pz - 0.6))), scale=1.0)
    MARROWS.append(a_)
vis(mac, MAC)
for a_ in MARROWS: vis(a_, [(F_ULGUR - 8, FB1)], recursive=False)

# ======================================================================
# 5) KAMERALAR  (POV qorong'ilashuvi montajda: ffmpeg vignette)
# ======================================================================
def V(*a): return Vector(a)
def at(name, p, parent=None): return empty(name, tuple(p), parent)
def look_keys(cam, f0, f1, posf, tgtf, rollf=lambda t: 0.0, step=1):
    cam.rotation_mode = "QUATERNION"
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = (f - f0) / max(1, f1 - f0); p = posf(t); d = tgtf(t) - p
        q = d.to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), R(rollf(t)))
        cam.location = p; cam.keyframe_insert("location", frame=f)
        cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
# 1 budilnik: makro, orqada karavot; crash zoom + silkinish
# kamera budilnik -> qiz yuzi chizig'ida: orqada xira yuz ko'rinadi
_dirc = (CLOCK - FACE_BED); _dirc.z = 0; _dirc.normalize(); _side = V(-_dirc.y, _dirc.x, 0)
c = shot_cam("alarm", (0, 0, 0), at("clockT", CLOCK + V(0, 0, 0.07)), 24, 2.0, focus=at("clockF", CLOCK + V(0, 0, 0.07)))
path_keys(c, [(A0, CLOCK + _dirc * 1.0 + _side * 0.28 + V(0, 0, 0.22)), (14, CLOCK + _dirc * 0.75 + _side * 0.2 + V(0, 0, 0.16)),
              (18, CLOCK + _dirc * 0.5 + _side * 0.13 + V(0, 0, 0.11)), (A1, CLOCK + _dirc * 0.45 + _side * 0.12 + V(0, 0, 0.1))])
lens_keys(c, [(A0, 20), (14, 24), (18, 32), (A1, 35)])
shake(c, 16, A1, 0.006, seed=1, decay=False)
# 2 cho'chish: tepadan yuzga push-in
J0, J1 = S["jolt"]
c = shot_cam("jolt", (0, 0, 0), faceT, 22, 2.0, focus=faceT)
path_keys(c, [(J0, FACE_BED + V(0.25, -0.35, 0.75)), (F_JOLT + 3, FACE_BED + V(0.18, -0.28, 0.6)), (J1, FACE_BED + V(0.12, -0.22, 0.48))])
lens_keys(c, [(J0, 24), (F_JOLT + 3, 30), (J1, 34)])
shake(c, F_JOLT + 2, F_JOLT + 18, 0.02, seed=2)
# 3 sakrab turish: poldan past burchak, kamera bosh ortidan whip-tilt
U0, U1 = S["up"]
upT = empty("upT"); cl = upT.constraints.new("COPY_LOCATION"); cl.target = headE
c = shot_cam("up", (0, 0, 0), upT, 15, 4.0, focus=upT)
path_keys(c, [(U0, EDGE + V(1.35, -0.85, 0.62)), (U1, EDGE + V(1.15, -0.65, 0.6))])
lens_keys(c, [(U0, 15), (U1, 17)])
shake(c, F_RISE + 14, F_RISE + 28, 0.012, seed=3)
# 4 bosim tushadi: rentgen to'liq tana, yondan, pastga tilt
D0, D1 = S["drop"]
dT = empty("dropT"); path_keys(dT, [(D0, BS["Spine2"] + V(0, 0, 0.1)), (D1, BS["Neck"] + V(0, 0, 0.05))])
c = shot_cam("drop", (0, 0, 0), dT, 20, 4.0, focus=dT)
path_keys(c, [(D0, BS["Spine1"] + V(1.6, -0.9, 0.2)), (D1, BS["Spine2"] + V(1.15, -0.55, 0.3))])
# 5 miya qonsiz: rentgen boshga crash zoom
B0, B1 = S["brainless"]
bT = at("brainT", BS["Head"] + V(0, 0, 0.09))
c = shot_cam("brainless", (0, 0, 0), bT, 28, 2.8, focus=bT)
path_keys(c, [(B0, bT.location + V(0.75, -0.55, 0.32)), (F_MIYA + 1, bT.location + V(0.6, -0.42, 0.26)),
              (F_MIYA + 6, bT.location + V(0.36, -0.25, 0.15)), (B1, bT.location + V(0.3, -0.18, 0.14))])
lens_keys(c, [(B0, 28), (F_MIYA + 1, 30), (F_MIYA + 6, 40), (B1, 44)])
shake(c, F_MIYA + 5, F_MIYA + 18, 0.008, seed=5)
# 6 yotgan: tepadan aylanma kran
L0, L1 = S["lying"]
lyT = at("lyingT", BL["Spine1"])
c = shot_cam("lying", (0, 0, 0), lyT, 16, 5.6, focus=lyT)
orbit(c, L0, L1, V(BL["Spine1"].x, BL["Spine1"].y, 0), 0.5, 0.35, -30, 40, BL["Spine1"].z + 2.0, BL["Spine1"].z + 1.7)
# 7 yurak: yaqin plan, orqaga chekinish
HE0, HE1 = S["heart"]
HEARTW = wpos(heartE, 270)
c = shot_cam("heart", (0, 0, 0), heartE, 40, 2.8, focus=heartE)
path_keys(c, [(HE0, HEARTW + V(0.18, -0.12, 0.2)), (HE1, HEARTW + V(0.36, -0.2, 0.42))])
lens_keys(c, [(HE0, 44), (HE1, 30)])
# 8 tekis oqim: yonlama slayd boshdan oyoqqa
E0, E1 = S["even"]
evT = empty("evenT"); path_keys(evT, [(E0, BL["Neck"]), (E1, BL["LeftLeg"])])
c = shot_cam("even", (0, 0, 0), evT, 22, 5.0, focus=evT)
path_keys(c, [(E0, BL["Head"] + V(0.95, 0.15, 0.55)), (E1, BL["LeftLeg"] + V(0.95, -0.25, 0.6))])
# 9 rentgen: keskin turish (old-pastdan)
X0_, X1_ = S["standx"]
sxT = empty("standxT"); cl = sxT.constraints.new("COPY_LOCATION"); cl.target = headE
c = shot_cam("standx", (0, 0, 0), sxT, 16, 5.0, focus=sxT)
path_keys(c, [(X0_, EDGE + V(1.6, 0.55, 0.45)), (X1_, EDGE + V(1.35, 0.45, 0.4))])
shake(c, F_RISE2 + 12, F_RISE2 + 26, 0.014, seed=9)
# 10 tortishish: boshdan oyoqqa tilt, keyin qorin
gT = empty("gravT"); path_keys(gT, [(GV0, BS["Head"]), (GV0 + 12, BS["Head"]), (F_OYOQ, BS["LeftLeg"] + V(0, 0, 0.1)),
                                    (F_QORIN - 2, BS["LeftLeg"] + V(0, 0, 0.15)), (F_QORIN + 10, BS["Spine"]), (GV1, BS["Spine"])])
c = shot_cam("gravity", (0, 0, 0), gT, 20, 5.0, focus=gT)
path_keys(c, [(GV0, BS["Head"] + V(1.45, -0.35, 0.15)), (F_OYOQ, BS["LeftLeg"] + V(1.5, -0.3, 0.55)),
              (F_QORIN + 10, BS["Spine"] + V(0.95, -0.25, 0.1)), (GV1, BS["Spine"] + V(0.8, -0.2, 0.05))])
# 11 makro tomir: tepaga suriladi
vT = empty("vesselT"); path_keys(vT, [(VE0, MV + V(0, 0.1, -0.9)), (VE1, MV + V(0, 0.1, 0.5))])
c = shot_cam("vessel", (0, 0, 0), vT, 24, 4.0, focus=vT)
path_keys(c, [(VE0, MV + V(0.6, -2.3, -1.4)), (VE1, MV + V(0.2, -1.9, 0.8))])
# 12 qaytib tushadi: yaqinroq, crash zoom
fT = empty("fallbackT"); path_keys(fT, [(FB0, MV + V(0, 0.1, 0.6)), (F_ULGUR, MV + V(0, 0.1, 0.3)), (FB1, MV + V(0, 0.1, -0.3))])
c = shot_cam("fallback", (0, 0, 0), fT, 30, 3.2, focus=fT)
path_keys(c, [(FB0, MV + V(-0.4, -1.6, 1.0)), (F_ULGUR - 2, MV + V(-0.35, -1.45, 0.75)), (F_ULGUR + 3, MV + V(-0.25, -1.05, 0.4)), (FB1, MV + V(-0.2, -1.0, 0.2))])
lens_keys(c, [(FB0, 30), (F_ULGUR - 2, 32), (F_ULGUR + 3, 42), (FB1, 44)])
shake(c, F_ULGUR + 2, F_ULGUR + 16, 0.02, seed=12)
# 13 miyaga oqim kamayadi: bo'yin+bosh aylanma push-in
BF0, BF1 = S["brainflow"]
bfT = at("bflowT", BS["Neck"].lerp(BS["Head"], 0.7) + V(0, 0, 0.04))
c = shot_cam("brainflow", (0, 0, 0), bfT, 30, 3.2, focus=bfT)
orbit(c, BF0, BF1, bfT.location + V(0, 0, -0.05), 0.75, 0.42, 120, 65, 0.15, 0.08)
lens_keys(c, [(BF0, 30), (BF1, 36)])
# 14 POV: ko'z oldi qorong'ilashadi
PV0, PV1 = S["pov"]
EYE = BS["Head"] + V(0.1, 0, 0.08)
c = shot_cam("pov", (0, 0, 0), None, 20, 6.0, focus=1.2)
look_keys(c, PV0, PV1, lambda t: EYE + V(0.03 * math.sin(t * 7), 0.04 * math.sin(t * 5 + 1), -0.06 * t),
          lambda t: V(0.9, -1.3, 1.25) + V(0.25 * math.sin(t * 6), 0.15 * math.cos(t * 4), -0.25 * t),
          lambda t: 8 * math.sin(t * 6.5) + 12 * t)
for f_, v in ((PV0, 6.0), (PV0 + 20, 2.0), (PV1, 0.6)): c.data.dof.aperture_fstop = v; c.data.dof.keyframe_insert("aperture_fstop", frame=f_)
# 15 yiqilish: poldan keng past burchak, aylanib qiyshayadi
FA0, FA1 = S["fall"]
FT = at("fallT", FALL + V(0, -0.15, 0.8))
c = shot_cam("fall", (0, 0, 0), None, 16, 4.0, focus=FT)
look_keys(c, FA0, FA1, lambda t: FALL + V(-0.95 + 0.25 * ease(t), -1.05 + 0.25 * ease(t), 0.22 - 0.1 * ease(t)),
          lambda t: FALL + V(0, -0.2, 0.95 - 0.7 * ease(max(0, (t - 0.45) / 0.55))), lambda t: 4 + 10 * ease(t))
shake(c, F_HIT, min(F_HIT + 9, FA1), 0.025, seed=15)
for n, cam in CAMS.items():
    if n in ("pov", "fall"): continue
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["alarm"]

# ======================================================================
# 6) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
bg_env = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_env.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.008, 0.02, 1)
bg_rd = N.new("ShaderNodeBackground"); bg_rd.inputs[0].default_value = (0.08, 0.004, 0.004, 1)
a1 = N.new("ShaderNodeAddShader"); a2 = N.new("ShaderNodeAddShader")
L.new(bg_env.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], a2.inputs[0]); L.new(bg_rd.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    room = any(a <= f <= b for a, b in ROOM); macro = any(a <= f <= b for a, b in MAC)
    for nd, v in ((bg_env, 0.6 if room else 0.0), (bg_dk, 0.0 if (room or macro) else 1.0), (bg_rd, 1.0 if macro else 0.0)):
        nd.inputs[1].default_value = v; nd.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# quyosh: deraza orqali (Y-), pastga
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(52), 0, R(-18)); sun.data.angle = R(1.5); sun.data.color = (1.0, 0.9, 0.75)
for f_, e in lights_for(ROOM, 6.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f_)
interp(sun.data, "CONSTANT")
area("win_fill", (0.6, Y0 + 0.3, 1.6), 1.2, (1.0, 0.95, 0.88), lights_for(ROOM, 120.0), target=at("wfT", (-0.8, 0.3, 0.6)), shape=(1.2, 1.1))
area("room_fill", (-0.4, 0.0, 2.5), 2.0, (1.0, 0.95, 0.9), lights_for(ROOM, 40.0), target=at("rfT", (-0.6, -0.2, 0.4)))
area("face_fill", tuple(FACE_BED + V(0.7, -0.6, 0.9)), 0.4, (1.0, 0.9, 0.8), lights_for(rng("jolt", "alarm"), 12.0), target=faceT)
area("clock_key", tuple(CLOCK + _dirc * 0.6 + _side * 0.3 + V(0, 0, 0.35)), 0.4, (1.0, 0.92, 0.8), lights_for(rng("alarm"), 25.0), target=at("ckT", CLOCK))
area("fall_rim", tuple(FALL + V(-1.2, 1.0, 1.8)), 1.0, (1.0, 0.85, 0.7), lights_for(rng("fall", "up"), 80.0), target=at("frT", FALL + V(0, 0, 0.8)))
# rentgen
area("X_rim", (STAND.x - 1.0, STAND.y + 1.2, 2.2), 1.0, (0.3, 0.55, 1.0), lights_for(XR, 60.0), target=at("xrT", BS["Spine2"]))
area("X_key", (STAND.x + 1.5, STAND.y - 1.0, 2.0), 1.0, (1.0, 0.85, 0.8), lights_for(XR, 40.0), target=at("xkT", BS["Spine2"]))
area("XL_key", (BL["Spine1"].x + 0.8, BL["Spine1"].y - 0.6, 2.2), 1.0, (1.0, 0.85, 0.8), lights_for(rng("lying", "heart", "even"), 40.0), target=at("xlT", BL["Spine1"]))
# makro
area("MV_key", tuple(MV + V(-1.6, -2.4, 1.2)), 1.5, (1.0, 0.85, 0.8), lights_for(MAC, 350.0), target=at("mvkT", MV))
area("MV_rim", tuple(MV + V(1.6, 1.2, 1.0)), 1.2, (1.0, 0.15, 0.08), lights_for(MAC, 500.0), target=at("mvrT", MV))
point("MV_in", tuple(MV + V(0, 0.15, 0.2)), 0.2, (1.0, 0.5, 0.4), lights_for(MAC, 60.0))
point("MV_in2", tuple(MV + V(0, 0.15, -1.6)), 0.2, (1.0, 0.5, 0.4), lights_for(MAC, 40.0))

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
