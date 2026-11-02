# Vannada barmoqlar nega burishadi — Zack D. Films uslubida 35.4 s video (850 kadr, 24 fps, 9:16).
# Asos: zack_test/ebbi/ebbi.py + mixchar.py; procedural modellar: burish/parts.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/burish/burish.py --render
# Sinov: FRAMES=10,60,150,230,400 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
random.seed(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 850
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan) ----------------
SHOTS = [(1, "hook"), (20, "bath_wide"), (46, "timelapse"), (87, "hand_look"), (115, "myth"), (163, "wrong"),
         (199, "brain"), (247, "under"), (314, "nerve_arm"), (361, "vessels"), (407, "shrink"), (456, "folds"),
         (506, "orbit"), (563, "nerve_cut"), (631, "two"), (685, "lab"), (739, "tire"), (780, "glass"), (818, "duck")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

# ---------------- yordamchilar ----------------
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
    for x in objs:                                   # oldingi ko'rinish kalitlarini tozalash (qayta chaqirish mumkin)
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def pbr(name, folder, scale=1.0, tint=None, proj="BOX", rough_mul=None):
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
    r = img("rough.jpg", True)
    if rough_mul is not None:
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        L.new(r.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], b.inputs["Roughness"])
    else:
        L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

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

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
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
    rnd = random.Random(seed)
    sc.frame_set(f0); base = cam.location.copy()
    for f in range(f0, f1):
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)
    cam.location = base; cam.keyframe_insert("location", frame=f1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

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

def point(name, loc, r, col, keys):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)

WORLD_PARENTS = {"bath", "lab", "road"}
def _par(o, parent):
    o.parent = parent
    if parent.name in WORLD_PARENTS:
        bpy.context.view_layer.update(); o.matrix_parent_inverse = parent.matrix_world.inverted()

CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c

# ======================================================================
# 1) MAKRO A: SUV (ilgak, suv osti) — dunyo markazi
# ======================================================================
skin_wet = P.skin_material("skin_wet", wet=0.85)
skin_dry = P.skin_material("skin_dry", wet=0.15)
drop_m = P.water_material("drop", rough=0.0)

A0 = Vector((0, 0, 0))
# suv: to'lqinli sirt + qalinlik (ichida yutilish hajmi) -> kamera suv ostiga tusha oladi
bpy.ops.mesh.primitive_grid_add(x_subdivisions=360, y_subdivisions=360, size=0.36, location=(0, 0.02, 0))
water = bpy.context.object; water.name = "waterA"
wm = P.water_material("waterA_mat", tint=(0.92, 0.97, 1.0), rough=0.01)
vol = wm.node_tree.nodes.new("ShaderNodeVolumeAbsorption"); vol.inputs["Color"].default_value = (0.55, 0.82, 0.9, 1)
vol.inputs["Density"].default_value = 3.0
vs = wm.node_tree.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.7, 0.9, 1.0, 1)
vs.inputs["Density"].default_value = 0.25; vs.inputs["Anisotropy"].default_value = 0.5
va = wm.node_tree.nodes.new("ShaderNodeAddShader"); wm.node_tree.links.new(vol.outputs[0], va.inputs[0]); wm.node_tree.links.new(vs.outputs[0], va.inputs[1])
wm.node_tree.links.new(va.outputs[0], wm.node_tree.nodes["Material Output"].inputs["Volume"])
water.data.materials.append(wm)
wv = water.modifiers.new("ripple", "WAVE"); wv.time_offset = 3; wv.height = 0.0009; wv.width = 0.0035; wv.narrowness = 1.2
wv.speed = 0.0016; wv.use_normal = False; wv.falloff_radius = 0.12; wv.start_position_x = 0.0; wv.start_position_y = -0.02
wv.damping_time = 60
ripple_tex = bpy.data.textures.new("ripple_noise", "CLOUDS"); ripple_tex.noise_scale = 0.02
noise_e = empty("ripple_drift", (0, 0, 0))
dsp = water.modifiers.new("noise", "DISPLACE"); dsp.texture = ripple_tex; dsp.strength = 0.0006; dsp.texture_coords = "OBJECT"
dsp.texture_coords_object = noise_e
key(noise_e, 1, loc=(0, 0, 0)); key(noise_e, END, loc=(0.03, 0.05, 0.02)); interp(noise_e, "LINEAR")
so = water.modifiers.new("th", "SOLIDIFY"); so.thickness = 0.16; so.offset = -1.0
for _m in water.modifiers: _m.show_viewport = False
for p in water.data.polygons: p.use_smooth = True
# vanna tubi va devori (oq emal), orqada xira kafel
enamel = mat("enamel", (0.92, 0.93, 0.94), 0.12, coat=0.6)
plane("A_floor", (0.5, 0.5), (0, 0.02, -0.15), enamel)
tiles_m = pbr("tiles", "long_white_tiles", 4.0)
plane("A_back", (0.8, 0.8), (0, 0.32, 0.1), tiles_m, rot=(90, 0, 0))
_bk = mat("bokeh_warmA", (1.0, 0.72, 0.42), emit=6.0)
for i, (x, z) in enumerate(((-0.1, 0.14), (0.12, 0.2), (0.16, 0.06), (-0.17, 0.04), (0.02, 0.24))):
    sphere(f"A_bokeh{i}", 0.011, (x, 0.31, z), _bk)
# ilgak barmoqlari: uchi tepaga, yostiqcha -Y (kameraga)
hookR = empty("hookR", (0, 0, 0))
fA = P.build_finger("fA", hookR, strength=1.0, skin=skin_wet); fA.rotation_euler = (R(-78), 0, R(4))
fA2 = P.build_finger("fA2", hookR, strength=1.0, seed=2.0, skin=skin_wet); fA2.location = (0.0185, 0.006, -0.004); fA2.rotation_euler = (R(-80), R(4), R(-3))
fA3 = P.build_finger("fA3", hookR, strength=1.0, seed=4.0, skin=skin_wet); fA3.location = (-0.0175, 0.007, -0.011); fA3.rotation_euler = (R(-80), R(-6), R(6))
for f_ in (fA, fA2, fA3):
    P.drops_on(f_, 22, 0.00025, 0.0009, drop_m, seed=len(f_.name) * 7, region=lambda c: c.y < 0.035 and c.z < 0.002)
# oqib tushayotgan katta tomchi (yostiqcha bo'ylab)
runner = P.droplet("runner", (0, 0, 0), 0.0016, fA, drop_m, squash=0.5)
for f, y in ((1, 0.006), (19, 0.02)):
    runner.location = (0.0005, y, -0.0089); runner.keyframe_insert("location", frame=f)
runner.rotation_euler = (R(180), 0, 0)
key(hookR, 1, loc=(0, 0, 0.004)); key(hookR, 14, loc=(0, 0, 0.03)); key(hookR, 19, loc=(0, 0, 0.032))
vis(hookR, rng("hook"))
# suv ostidagi barmoq (8-kadr): gorizontal, yostiqcha pastga-kameraga
underR = empty("underR", (0.06, 0.0, -0.055))
fU = P.build_finger("fU", underR, strength=0.2, seed=6.0, skin=skin_wet); fU.rotation_euler = (R(18), 0, R(-25))
fU2 = P.build_finger("fU2", underR, strength=0.2, seed=8.0, skin=skin_wet); fU2.location = (0.012, 0.012, 0.004); fU2.rotation_euler = (R(16), 0, R(-25))
P.set_wrinkle(fU, S["under"][0], 0.15); P.set_wrinkle(fU, S["under"][1], 0.6)
P.set_wrinkle(fU2, S["under"][0], 0.15); P.set_wrinkle(fU2, S["under"][1], 0.6)
vis(underR, rng("under"))
bub_m = P.bubble_material(); bubbles = []
rb = random.Random(11)
for i in range(46):
    r_ = rb.uniform(0.0003, 0.0016)
    b = sphere(f"bub{i}", r_, (0, 0, 0), bub_m, sub=3)
    x0, y0 = 0.06 + rb.uniform(-0.035, 0.03), rb.uniform(-0.02, 0.05); z0 = rb.uniform(-0.12, -0.05)
    sp = 0.0007 + r_ * 0.6; ph = rb.uniform(0, 6)
    for f in range(S["under"][0], S["under"][1] + 1, 3):
        t = f - S["under"][0]
        z = z0 + sp * t
        if z > -0.002: z = -0.002 - (z % 0.0001)
        b.location = (x0 + 0.0015 * math.sin(t * 0.4 + ph), y0 + 0.0015 * math.cos(t * 0.3 + ph), z); b.keyframe_insert("location", frame=f)
    bubbles.append(b)
for i in range(30):                                     # teriga yopishgan pufakchalar
    b = sphere(f"sbub{i}", rb.uniform(0.0002, 0.0006), (0, 0, 0), bub_m, sub=2)
    b.parent = fU; ang = rb.uniform(-2.2, 2.2); y = rb.uniform(0.0, 0.03)
    b.location = (0.0079 * math.sin(ang), y, -0.0079 * math.cos(ang)); bubbles.append(b)
for b in bubbles: vis(b, rng("under"), recursive=False)

# ======================================================================
# 2) MAKRO B: QURUQ (time-lapse, aylanma, ikki barmoq) — (1,0,0)
# ======================================================================
B0 = Vector((1, 0, 0))
handB = empty("handB", tuple(B0))
fB = P.build_finger("fB", handB, strength=0.0, skin=skin_dry); fB.rotation_euler = (R(-74), 0, R(3))
fB2 = P.build_finger("fB2", handB, strength=0.0, seed=2.0, skin=skin_dry); fB2.location = (0.0185, 0.008, -0.002); fB2.rotation_euler = (R(-76), R(3), R(-4))
fB3 = P.build_finger("fB3", handB, strength=0.0, seed=4.0, skin=skin_dry); fB3.location = (-0.0178, 0.009, -0.009); fB3.rotation_euler = (R(-77), R(-5), R(6))
T0, T1 = S["timelapse"]
for f_ in (fB, fB2, fB3):
    P.set_wrinkle(f_, 1, 0.0); P.set_wrinkle(f_, T0 + 3, 0.0)
    for i in range(1, 9):                               # time-lapse: pog'onama-pog'ona o'sish
        P.set_wrinkle(f_, T0 + 3 + i * 4, ease(i / 8))
    P.set_wrinkle(f_, T1, 1.0)
# ikkinchi qo'l: asabi shikastlangan barmoq (silliq) + chandiq
fS = P.build_finger("fS", None, strength=0.0, seed=9.0, skin=skin_dry); fS.location = tuple(B0 + Vector((0.026, 0.004, -0.003)))
fS.rotation_euler = (R(-74), 0, R(-4))
scar = mat("scar", (0.62, 0.3, 0.28), 0.35, sss=0.4)
bpy.ops.mesh.primitive_torus_add(major_radius=0.0079, minor_radius=0.0006, location=(0, 0.045, 0), rotation=(R(90), 0, 0))
sc_o = bpy.context.object; sc_o.name = "scar"; sc_o.scale = (1.08, 1, 0.9); sc_o.data.materials.append(scar); sc_o.parent = fS
vis(handB, rng("timelapse", "orbit", "two"))
vis(fB2, rng("timelapse", "orbit")); vis(fB3, rng("timelapse", "orbit"))
vis(fS, rng("two"))
plane("B_back", (1.0, 1.0), tuple(B0 + Vector((0, 0.3, 0.1))), tiles_m, rot=(90, 0, 0))
bath_bokeh = mat("bokeh_warm", (1.0, 0.75, 0.45), emit=6.0)
for i, (x, z) in enumerate(((-0.12, 0.16), (0.1, 0.22), (0.16, 0.05), (-0.18, 0.02))):
    sphere(f"B_bokeh{i}", 0.012, tuple(B0 + Vector((x, 0.29, z))), bath_bokeh)

# ======================================================================
# 3) SHISHA ostidan (2,0,0)
# ======================================================================
C0 = Vector((2, 0, 0))
glass_m = mat("glass", (0.95, 0.97, 0.98), 0.0, trans=1.0)
box("glass_plate", (0.14, 0.14, 0.006), tuple(C0 + Vector((0, 0.01, -0.003))), glass_m)
glassR = empty("glassR", tuple(C0))
fC = P.build_finger("fC", glassR, strength=1.0, seed=1.5, skin=skin_wet); fC.rotation_euler = (R(28), 0, R(-8))
G0, G1 = S["glass"]; TOUCH = G0 + 16
key(glassR, G0, loc=tuple(C0 + Vector((0, 0, 0.022)))); key(glassR, TOUCH, loc=tuple(C0 + Vector((0, 0, 0.0071))))
key(glassR, TOUCH + 6, loc=tuple(C0 + Vector((0, 0, 0.0061)))); key(glassR, G1, loc=tuple(C0 + Vector((0, 0, 0.006))))
rg = random.Random(21); gdrops = []
for i in range(48):
    r_ = rg.uniform(0.0006, 0.0028)
    p = Vector((rg.uniform(-0.04, 0.04), rg.uniform(-0.03, 0.05), 0))
    d = P.droplet(f"gdrop{i}", tuple(C0 + p + Vector((0, 0, r_ * 0.25))), r_, None, drop_m, squash=0.42)
    d.keyframe_insert("location", frame=G0); d.keyframe_insert("scale", frame=G0)
    cdist = (p.xy - Vector((0.0, 0.009))).length
    if cdist < 0.016:                                   # barmoq ostidagi suv chetga siqib chiqariladi
        dirv = (p.xy - Vector((0.0, 0.009))).normalized() if cdist > 1e-4 else Vector((1, 0))
        q = Vector((0.0, 0.009)) + dirv * (0.017 + rg.uniform(0, 0.004))
        d.keyframe_insert("location", frame=TOUCH - 1)
        d.location = tuple(C0 + Vector((q.x, q.y, r_ * 0.2))); d.scale = (1.5, 1.5, 0.35)
        d.keyframe_insert("location", frame=TOUCH + 5); d.keyframe_insert("scale", frame=TOUCH + 5)
    gdrops.append(d)
for d in gdrops: vis(d, rng("glass"), recursive=False)
vis(glassR, rng("glass"))

# ======================================================================
# 4) RENTGEN BARMOQ (katta masshtab) (5,0,0): tomirlar, asab, signal
# ======================================================================
X0 = Vector((5, 0, 0))
xr_root = empty("xr_root", tuple(X0 + Vector((0, 0, 0.88)))); xr_root.rotation_euler = (R(-90), 0, R(12))
xr_skin = P.xray_material("xray_skin", col=(1.0, 0.62, 0.55), strength=1.6, base=0.02)
fX = P.build_finger("fX", xr_root, r=0.078, length=0.8, strength=0.0, skin=xr_skin, knuckle=False)
for ch in fX.children:
    ch.data.materials[0] = xr_skin
bone_m = P.xray_material("xray_bone", col=(0.85, 0.92, 1.0), strength=2.2, base=0.15)
cyl("xbone1", 0.026, 0.25, (0, 0.18, 0.01), bone_m, rot=(90, 0, 0), parent=fX)
cyl("xbone2", 0.03, 0.3, (0, 0.47, 0.01), bone_m, rot=(90, 0, 0), parent=fX)
sphere("xbone_tip", 0.03, (0, 0.05, 0.008), bone_m, scale=(1.2, 1.0, 0.6), parent=fX)
for y in (0.31, 0.63):
    sphere(f"xjoint{y}", 0.036, (0, y, 0.01), bone_m, scale=(1.0, 0.7, 0.9), parent=fX)
art_m = P.pulse_material("artery", (0.75, 0.04, 0.03), base_emit=0.6, pulse_col=(1.0, 0.25, 0.15))
nrv_m = P.pulse_material("nerve", (0.9, 0.75, 0.15), base_emit=0.4, pulse_col=(1.0, 0.85, 0.3), width=0.08)
nrv_cut_m = P.pulse_material("nerve_cut", (0.9, 0.75, 0.15), base_emit=0.4, pulse_col=(1.0, 0.85, 0.3), width=0.08)
nrv_dead_m = P.pulse_material("nerve_dead", (0.35, 0.3, 0.12), base_emit=0.05)
arteries, nerves, nerves_cut = [], [], []
ra = random.Random(4)
def wob(y, a=0.004, k=40.0, ph=0.0): return a * math.sin(y * k + ph)
for sx in (-1, 1):
    pts = [(sx * (0.048 + wob(y, ph=sx)), y, -0.022 + wob(y, 0.003, 25)) for y in [0.85, 0.7, 0.55, 0.4, 0.25, 0.12]]
    pts += [(sx * 0.03, 0.04, -0.03), (0.0, 0.025, -0.035)]
    a_ = P.tube(f"art{sx}", pts, 0.0075, art_m, fX); arteries.append(a_)
    # kapillyar shoxlar yostiqcha tomon
    for i in range(9):
        y = ra.uniform(0.02, 0.26); x = sx * (0.045 - 0.0001 * i)
        bp = [(x, y, -0.024), (x * 0.8 + ra.uniform(-0.01, 0.01), y - 0.01, -0.045), (x * 0.5 + ra.uniform(-0.015, 0.015), y - 0.02 + ra.uniform(-0.01, 0.01), -0.062),
              (x * 0.3, y - 0.01, -0.066)]
        arteries.append(P.tube(f"cap{sx}_{i}", bp, 0.0028, art_m, fX))
    # asab
    npts = [(sx * (0.032 + wob(y, 0.003, 30, 1)), y, -0.038) for y in [0.85, 0.65, 0.45, 0.3, 0.16, 0.06]]
    nerves.append(P.tube(f"nrv{sx}", npts, 0.0055, nrv_m, fX))
    for i in range(6):
        y = 0.03 + i * 0.035; x = sx * 0.028
        bp = [(x, y, -0.04), (x * 0.7 + ra.uniform(-0.012, 0.012), y - 0.012, -0.055), (x * 0.4 + ra.uniform(-0.012, 0.012), y - 0.02, -0.068)]
        nerves.append(P.tube(f"nbr{sx}_{i}", bp, 0.0022, nrv_m, fX))
        sphere(f"nend{sx}_{i}", 0.0042, bp[-1], nrv_m, parent=fX)
    # shikastlangan asab: 0.42 da uzilgan
    base_pts = [(sx * (0.032 + wob(y, 0.003, 30, 1)), y, -0.038) for y in [0.85, 0.7, 0.55, 0.43]]
    nerves_cut.append(P.tube(f"nrvc{sx}", base_pts, 0.0055, nrv_cut_m, fX))
    dist_pts = [(sx * (0.032 + wob(y, 0.003, 30, 1)), y, -0.038) for y in [0.37, 0.28, 0.16, 0.06]]
    nerves_cut.append(P.tube(f"nrvd{sx}", dist_pts, 0.0055, nrv_dead_m, fX))
    for i in range(6):
        y = 0.03 + i * 0.035; x = sx * 0.028
        bp = [(x, y, -0.04), (x * 0.7, y - 0.012, -0.055), (x * 0.4, y - 0.02, -0.068)]
        nerves_cut.append(P.tube(f"nbrd{sx}_{i}", bp, 0.0022, nrv_dead_m, fX))
for n in nerves: vis(n, rng("vessels"), recursive=False)
for o in fX.children:
    if o.name.startswith("nend"): vis(o, rng("vessels"), recursive=False)
for n in nerves_cut: vis(n, rng("nerve_cut"), recursive=False)
V0, V1 = S["vessels"]
P.mat_value(nrv_m, "pos", 1, -0.2); P.mat_value(nrv_m, "pos", V0, -0.1); P.mat_value(nrv_m, "pos", V0 + 22, 1.2)
P.mat_value(art_m, "glow", 1, 0.6); P.mat_value(art_m, "glow", V0 + 20, 0.6); P.mat_value(art_m, "glow", V0 + 24, 4.0)
P.mat_value(art_m, "glow", V0 + 30, 1.2)
for a_ in arteries:                                     # signal kelgach tomirlar torayadi
    d0 = a_["r0"]
    P.tube_r(a_, 1, d0); P.tube_r(a_, V0 + 24, d0); P.tube_r(a_, V1, d0 * 0.55); P.tube_r(a_, V1 + 1, d0)
NC0, NC1 = S["nerve_cut"]
P.mat_value(nrv_cut_m, "pos", 1, -0.2); P.mat_value(nrv_cut_m, "pos", NC0, -0.1); P.mat_value(nrv_cut_m, "pos", NC0 + 18, 1.3)
for f in range(NC0 + 18, NC1, 6):                       # uzilgan joyda miltillash
    P.mat_value(nrv_cut_m, "glow", f, 2.5); P.mat_value(nrv_cut_m, "glow", f + 3, 0.4)
# uchqunlar uzilish joyida
spark_m = mat("spark", (1.0, 0.18, 0.05), emit=30.0)
sparks = []
for i in range(26):
    sx = -1 if i % 2 else 1
    s_ = sphere(f"spark{i}", 0.0018, (0, 0, 0), spark_m, sub=1, parent=fX)
    c0 = Vector((sx * 0.032, 0.40, -0.038))
    for f in range(NC0 + 16, NC1 + 1, 2):
        t = (f + i * 3) % 14 / 14.0
        dirv = Vector((ra.uniform(-1, 1), ra.uniform(-1, 1), ra.uniform(-1, 1))).normalized()
        s_.location = c0 + dirv * 0.03 * t; s_.keyframe_insert("location", frame=f)
        s_.scale = (1 - t,) * 3; s_.keyframe_insert("scale", frame=f)
    sparks.append(s_)
for s_ in sparks: vis(s_, [(NC0 + 16, NC1)], recursive=False)
vis(xr_root, rng("vessels", "nerve_cut"))
for n in nerves + [o for o in fX.children if o.name.startswith("nend")]: vis(n, rng("vessels"), recursive=False)
for n in nerves_cut: vis(n, rng("nerve_cut"), recursive=False)
for s_ in sparks: vis(s_, [(NC0 + 16, NC1)], recursive=False)

# ======================================================================
# 5) TERI KESIMI (0,50,0)
# ======================================================================
SEC0 = Vector((0, 50, 0))
secR, sparts, (epi_m, der_m, fat_m) = P.build_section("sec", tuple(SEC0))
# tomirlar: shish/cho'kishga moslab z bo'yicha masshtablanadi
vroot = empty("sec_vessels", (0, 0, 0), secR)
sec_art = P.pulse_material("sec_art", (0.7, 0.03, 0.03), base_emit=0.3, pulse_col=(1, 0.2, 0.1))
sec_vein = P.pulse_material("sec_vein", (0.12, 0.1, 0.45), base_emit=0.2)
sec_nrv = P.pulse_material("sec_nrv", (0.95, 0.8, 0.2), base_emit=0.5, pulse_col=(1, 0.9, 0.4), width=0.1)
svs = []
rs = random.Random(8)
for j, (yy, zz, mm) in enumerate(((-0.25, 0.62, sec_art), (0.3, 0.58, sec_vein), (0.05, 0.72, sec_art))):
    pts = [(x, yy + 0.05 * math.sin(x * 2.2 + j), zz + 0.03 * math.sin(x * 3 + j)) for x in (-1.1, -0.6, -0.1, 0.4, 0.9, 1.1)]
    svs.append(P.tube(f"svA{j}", pts, 0.06, mm, vroot))
for j, xx in enumerate((-0.75, -0.35, 0.15, 0.45, 0.8)):             # old kesimdan chiqadigan tomirlar (dumaloq kesim ko'rinadi)
    pts = [(xx + 0.05 * math.sin(y * 3), y, (0.6, 0.74, 0.66, 0.56, 0.7)[j] + 0.04 * math.cos(y * 2 + j)) for y in (-0.72, -0.4, 0.0, 0.4, 0.72)]
    svs.append(P.tube(f"svB{j}", pts, 0.065, sec_art if j != 1 else sec_vein, vroot))
for i in range(9):                                      # kapillyar halqalar yuqoriga
    x = -0.85 + i * 0.21 + rs.uniform(-0.04, 0.04); y = rs.uniform(-0.5, 0.5)
    pts = [(x - 0.05, y, 0.64), (x - 0.04, y, 0.8), (x, y, 0.86), (x + 0.04, y, 0.8), (x + 0.05, y, 0.64)]
    svs.append(P.tube(f"svC{i}", pts, 0.015, sec_art, vroot))
snrv = P.tube("sec_nerve", [(x, 0.1 + 0.03 * math.sin(x * 4), 0.5) for x in (-1.1, -0.5, 0.0, 0.5, 1.1)], 0.03, sec_nrv, vroot)
for i in range(4):
    x = -0.7 + i * 0.45
    P.tube(f"sec_nbr{i}", [(x, 0.1, 0.5), (x + 0.05, 0.05, 0.65), (x + 0.1, 0.0, 0.82)], 0.012, sec_nrv, vroot)
MY0, MY1 = S["myth"]; WR0, WR1 = S["wrong"]; SH0, SH1 = S["shrink"]; FO0, FO1 = S["folds"]
def sec_state(f, fold, swell, sink):
    P.section_key(sparts, f, fold=fold, swell=swell, sink=sink)
    vroot.scale = (1, 1, 1 + 0.18 * swell - 0.12 * sink); vroot.keyframe_insert("scale", frame=f)
sec_state(1, 0, 0, 0); sec_state(MY0 + 4, 0, 0, 0); sec_state(MY1, 0, 1, 0); sec_state(WR0 + 1, 0, 1, 0); sec_state(WR0 + 6, 0, 0, 0)
sec_state(SH0 + 4, 0, 0, 0); sec_state(SH1 - 4, 0, 0, 1); sec_state(FO0 + 3, 0, 0, 1); sec_state(FO1 - 4, 1, 0, 1)
P.mat_value(epi_m, "blue", 1, 0); P.mat_value(epi_m, "blue", MY0 + 4, 0); P.mat_value(epi_m, "blue", MY1, 0.55)
P.mat_value(epi_m, "blue", WR0 + 1, 0.55); P.mat_value(epi_m, "blue", WR0 + 6, 0.0)
P.mat_value(sec_nrv, "pos", 1, -0.2); P.mat_value(sec_nrv, "pos", SH0, -0.2); P.mat_value(sec_nrv, "pos", SH0 + 16, 1.2)
for t_ in svs:                                          # tomirlar torayadi
    d0 = t_["r0"]
    P.tube_r(t_, 1, d0); P.tube_r(t_, SH0 + 8, d0); P.tube_r(t_, SH1 - 6, d0 * 0.45)
# tomchilar: afsona (singib ketadi) va "noto'g'ri" (sakrab ketadi)
sdrop_m = P.water_material("sdrop", tint=(0.6, 0.85, 1.0), rough=0.0)
rd = random.Random(3); sdrops = []
for i in range(12):
    r_ = rd.uniform(0.045, 0.08); x, y = rd.uniform(-0.8, 0.8), rd.uniform(-0.5, 0.5)
    d = P.droplet(f"sdrop{i}", (0, 0, 0), r_, secR, sdrop_m, squash=1.0)
    t_hit = MY0 + 6 + i * 3
    for f in range(MY0, t_hit + 1, 2):
        tt = (f - MY0) / max(1, t_hit - MY0)
        d.location = (x, y, 1.0 + r_ + (1 - tt) * 1.4); d.keyframe_insert("location", frame=f)
    d.scale = (1, 1, 1); d.keyframe_insert("scale", frame=t_hit)
    d.location = (x, y, 1.02); d.scale = (1.3, 1.3, 0.3); d.keyframe_insert("location", frame=t_hit + 3); d.keyframe_insert("scale", frame=t_hit + 3)
    d.location = (x, y, 0.95); d.scale = (0.01, 0.01, 0.01); d.keyframe_insert("location", frame=t_hit + 7); d.keyframe_insert("scale", frame=t_hit + 7)
    d["vr"] = [(MY0, t_hit + 7)]; sdrops.append(d)
for i in range(9):
    r_ = rd.uniform(0.05, 0.08); x, y = rd.uniform(-0.7, 0.7), rd.uniform(-0.45, 0.45)
    d = P.droplet(f"bdrop{i}", (0, 0, 0), r_, secR, sdrop_m, squash=1.0)
    t_hit = WR0 + 8 + i * 2; vx, vy = rd.uniform(-0.04, 0.04), rd.uniform(-0.05, -0.01)
    for f in range(WR0 + 2, WR1 + 1):
        if f <= t_hit:
            tt = (f - WR0 - 2) / max(1, t_hit - WR0 - 2); z = 1.0 + r_ + (1 - tt) * 1.2; sq = 1.0
        else:
            k = f - t_hit; z = 1.0 + r_ + 0.07 * k - 0.0035 * k * k; sq = 1.0
            x += vx; y += vy
            if z < 1.0 + r_: z = 1.0 + r_
        d.location = (x, y, z); d.keyframe_insert("location", frame=f)
    d["vr"] = [(WR0 + 2, WR1)]; sdrops.append(d)
vis(secR, rng("myth", "wrong", "shrink", "folds"))
for d in sdrops:
    vis(d, d["vr"], recursive=False)

# ======================================================================
# 6) HAMMOM + MEGAN (20,0,0)
# ======================================================================
BA = Vector((20, 0, 0))
bath = empty("bath", tuple(BA))
floor_m = pbr("marble", "marble_tiles", 1.2)
wall_t = pbr("wall_tiles", "long_white_tiles", 0.9)
plaster = pbr("plaster", "painted_plaster_wall", 0.8, tint=(0.95, 0.9, 0.84))
plane("bath_floor", (3.4, 4.4), tuple(BA + Vector((0, 0.6, 0))), floor_m, parent=bath)
for nm, sz, loc, rot in (("wall_back", (3.4, 1.4), (0, -0.85, 0.7), (90, 0, 0)), ("wall_left", (4.4, 1.4), (-1.7, 0.6, 0.7), (90, 0, 90)),
                         ("wall_right", (4.4, 1.4), (1.3, 0.6, 0.7), (90, 0, -90)), ("wall_front", (3.4, 1.4), (0, 2.8, 0.7), (90, 0, 180))):
    plane(nm, sz, tuple(BA + Vector(loc)), wall_t, rot=rot, parent=bath)
    plane(nm + "_up", (sz[0], 1.4), tuple(BA + Vector((loc[0], loc[1], 2.1))), plaster, rot=rot, parent=bath)
plane("bath_ceiling", (3.4, 4.4), tuple(BA + Vector((0, 0.6, 2.8))), mat("ceil", (0.9, 0.9, 0.88), 0.8), rot=(180, 0, 0), parent=bath)
# deraza (o'ng devorda, xira oyna orqali yorug'lik)
win_m = mat("window", (1.0, 0.96, 0.9), 0.3, emit=7.0)
plane("window", (1.0, 1.1), tuple(BA + Vector((1.29, 0.2, 1.6))), win_m, rot=(90, 0, -90), parent=bath)
frame_m = mat("wframe", (0.95, 0.95, 0.95), 0.4)
for dz in (-0.56, 0.56):
    box("wf_h" + str(dz), (0.04, 1.08, 0.05), tuple(BA + Vector((1.28, 0.2, 1.6 + dz))), frame_m, parent=bath)
box("wf_m", (0.04, 0.03, 1.1), tuple(BA + Vector((1.28, 0.2, 1.6))), frame_m, parent=bath)
# vanna (BlenderKit, erkin turuvchi oval), uzun o'qi Y bo'ylab
tubR = empty("tub", tuple(BA + Vector((0, 0.45, 0))), bath); tubR.rotation_euler = (0, 0, R(90))
tub_objs = import_gltf(BK + "16bfcc74_u.glb", tubR)
lo, hi = bbox(tub_objs)
_c = (lo + hi) / 2; tubR.location += Vector((BA.x - _c.x, BA.y + 0.45 - _c.y, -lo.z))
lo, hi = bbox(tub_objs)
print("TUB bbox", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
_body = max((o for o in tub_objs if o.type == "MESH"), key=lambda o: o.dimensions.x * o.dimensions.y)
blo, bhi = bbox([_body]); print("TUB body", tuple(round(v, 3) for v in blo), tuple(round(v, 3) for v in bhi))
TUB_TOP = bhi.z; lo, hi = blo, bhi
TUB_FLOOR = lo.z + 0.07
WATER_Z = TUB_TOP - 0.13
TUBC = (lo + hi) / 2
# sut-ko'pikli suv (tanani yashiradi)
foam_m = bpy.data.materials.new("bathwater"); foam_m.use_nodes = True
N = foam_m.node_tree.nodes; L = foam_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.86, 0.9, 0.92, 1); b.inputs["Roughness"].default_value = 0.05
b.inputs["Subsurface Weight"].default_value = 1.0; b.inputs["Subsurface Scale"].default_value = 0.05
b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.02
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0; nz.inputs["Detail"].default_value = 8
L.new(tc.outputs["Object"], nz.inputs["Vector"])
crm = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], crm.inputs[0])
crm.color_ramp.elements[0].position = 0.45; crm.color_ramp.elements[1].position = 0.6
vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 260.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
fb = N.new("ShaderNodeBump"); fb.inputs["Strength"].default_value = 0.6; L.new(vo.outputs["Distance"], fb.inputs["Height"])
mxr = N.new("ShaderNodeMix"); mxr.data_type = "FLOAT"; L.new(crm.outputs[0], mxr.inputs["Factor"])
mxr.inputs[2].default_value = 0.03; mxr.inputs[3].default_value = 0.6; L.new(mxr.outputs[0], b.inputs["Roughness"])
mxc = N.new("ShaderNodeMix"); mxc.data_type = "RGBA"; L.new(crm.outputs[0], mxc.inputs["Factor"])
mxc.inputs[6].default_value = (0.75, 0.84, 0.88, 1); mxc.inputs[7].default_value = (0.98, 0.98, 0.97, 1); L.new(mxc.outputs[2], b.inputs["Base Color"])
mxn = N.new("ShaderNodeMix"); mxn.data_type = "FLOAT"; L.new(crm.outputs[0], mxn.inputs["Factor"])
L.new(fb.outputs[0], b.inputs["Normal"])
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=1, fill_type="NGON", location=(TUBC.x, TUBC.y, WATER_Z))
bw = bpy.context.object; bw.name = "bathwater"; bw.scale = ((hi.x - lo.x) * 0.45, (hi.y - lo.y) * 0.46, 1)
bw.data.materials.append(foam_m); _par(bw, bath)
# ko'pik pufakchalari
foam_b = mat("foam_bub", (0.97, 0.97, 0.97), 0.15, coat=1.0, sss=0.3)
rf = random.Random(17)
fcl = []
for i in range(220):
    ang = rf.uniform(0, 2 * math.pi); rr = math.sqrt(rf.uniform(0.0, 1.0))
    x = math.cos(ang) * rr * (hi.x - lo.x) * 0.42; y = math.sin(ang) * rr * (hi.y - lo.y) * 0.44
    s_ = rf.uniform(0.006, 0.03)
    fcl.append(sphere(f"foam{i}", s_, (TUBC.x + x, TUBC.y + y, WATER_Z + s_ * 0.2), foam_b, scale=(1, 1, 0.6), sub=2, parent=None))
foamR = empty("foamR", (0, 0, 0))
for o in fcl: o.parent = foamR
# sochiqlar, shamlar
twl = empty("towels", (-1.25, 1.6, 0), bath)
stool = box("stool", (0.45, 0.45, 0.45), tuple(BA + Vector((-1.25, 1.6, 0.225))), mat("stool_m", (0.45, 0.32, 0.22), 0.5), parent=bath)
tw_objs = import_gltf(BK + "6647001a_u.glb", twl); twl.location.z = 0.45
candle_m = mat("candle", (0.95, 0.92, 0.85), 0.5, sss=0.6); flame_m = mat("flame", (1.0, 0.6, 0.2), emit=40.0)
for i, (x, y) in enumerate(((0.33, -0.45), (0.28, -0.5), (-0.33, -0.45))):
    p = BA + Vector((x, 0.45 + y + (hi.y - lo.y) * 0.0, TUB_TOP))
    cyl(f"candle{i}", 0.025, 0.08 + 0.03 * i, tuple(p + Vector((0, -0.12, 0.04 + 0.015 * i))), candle_m, parent=bath)
    sphere(f"flame{i}", 0.008, tuple(p + Vector((0, -0.12, 0.095 + 0.03 * i))), flame_m, scale=(0.7, 0.7, 1.6), parent=bath)
    point(f"candle_l{i}", tuple(p + Vector((0, -0.12, 0.13 + 0.03 * i))), 0.02, (1.0, 0.6, 0.25), lights_for(rng("bath_wide", "hand_look", "duck"), 2.0))
# rezina o'rdak (Poly Haven)
duckR = empty("duckR", (0, 0, 0))
duck_objs = import_gltf(PH + "rubber_duck_toy/rubber_duck_toy.gltf", duckR)
duckR.scale = (0.4, 0.4, 0.4)

# --- Megan ---
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
# futbolka -> teri (vannada yelkalar ochiq ko'rinadi; badan kiyim ostida modellashtirilmagan)
shirt = next(o for o in mmeshes if "Shirt" in o.name)
skin_top = mat("meg_skin_top", (0.78, 0.55, 0.45), 0.42, sss=0.6, coat=0.6)
skin_top.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.01
skin_top.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.08
shirt.data.materials[0] = skin_top
for o in mmeshes:
    if any(k in o.name for k in ("Pants", "Sneakers")): o.hide_render = True
MEG = Vector((TUBC.x, lo.y + 0.38, TUB_FLOOR))
mroot.location = MEG; mroot.rotation_euler = (0, 0, R(180))
megF = empty("megF", tuple(MEG))
A_ = lambda f: mc.load_action(f, True)
mc.add_strip(meg, A_("Sitting_Idle.fbx"), 1, blend=0, repeat=4.0)
# qo'l boshqaruvi: IK (bilak), kaft yo'nalishi, barmoq bukilishi
fa = meg.pose.bones["mixamorig:RightForeArm"]; hb = meg.pose.bones["mixamorig:RightHand"]
ikT = empty("ikT", (0.12, 0.4, 0.62), megF); poleT = empty("poleT", (0.7, 0.0, 0.15), megF)
ik = fa.constraints.new("IK"); ik.target = ikT; ik.chain_count = 2; ik.use_tail = True; ik.pole_target = poleT; ik.pole_angle = 0.0
upT = empty("upT", (0.12, 0.4, 1.3), megF); faceT = empty("faceT", (0.0, 0.1, 0.62), megF)
dt = hb.constraints.new("DAMPED_TRACK"); dt.target = upT; dt.track_axis = "TRACK_Y"
lt = hb.constraints.new("LOCKED_TRACK"); lt.target = faceT; lt.lock_axis = "LOCK_Y"; lt.track_axis = "TRACK_Z"
headT = empty("headT", (0.15, 0.45, 0.52), megF)
hd = meg.pose.bones["mixamorig:Head"].constraints.new("DAMPED_TRACK"); hd.target = headT; hd.track_axis = "TRACK_Z"
curlE = empty("curlE", (0, 0, 0))
for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
    for i in (1, 2, 3):
        pbn = meg.pose.bones.get(f"mixamorig:RightHand{fn}{i}")
        if not pbn: continue
        c = pbn.constraints.new("TRANSFORM"); c.target = curlE; c.map_from = "LOCATION"; c.from_min_x = 0; c.from_max_x = 1
        c.map_to = "ROTATION"; c.owner_space = "LOCAL"; c.target_space = "WORLD"; c.mix_mode_rot = "AFTER"
        c.map_to_x_from = "X"; c.to_min_x_rot = 0; c.to_max_x_rot = R(35 if fn == "Thumb" else 65)
HL0, HL1 = S["hand_look"]; DU0, DU1 = S["duck"]
for con in (ik, dt, lt, hd):
    for f, v in ((1, 0.0), (HL0 - 1, 0.0), (HL0, 1.0), (HL1 + 1, 0.0), (DU0 - 1, 0.0), (DU0, 1.0)):
        con.influence = v if con is not hd else v * 0.7; con.keyframe_insert("influence", frame=f)
for o in (meg,):
    for fcu in fcurves(o):
        if "constraints" in fcu.data_path:
            for k in fcu.keyframe_points: k.interpolation = "CONSTANT"
# 4-kadr: qo'l yuz oldida biroz ko'tariladi, barmoqlar ochiq
key(ikT, HL0, loc=(0.16, 0.4, 0.42)); key(ikT, HL0 + 8, loc=(0.15, 0.44, 0.5)); key(ikT, HL1, loc=(0.145, 0.45, 0.52))
key(curlE, 1, loc=(0.05, 0, 0)); key(curlE, DU0 + 9, loc=(0.05, 0, 0)); key(curlE, DU0 + 12, loc=(0.85, 0, 0))
# 19-kadr: o'rdakni ushlash — kaft pastga, barmoqlar oldinga
DUCK_L = Vector((0.2, 0.5, WATER_Z - TUB_FLOOR + 0.02))
key(ikT, DU0, loc=tuple(DUCK_L + Vector((0.0, -0.13, 0.17)))); key(ikT, DU0 + 9, loc=tuple(DUCK_L + Vector((-0.0, -0.11, 0.07))))
key(ikT, DU0 + 13, loc=tuple(DUCK_L + Vector((0.0, -0.11, 0.075)))); key(ikT, DU0 + 26, loc=tuple(DUCK_L + Vector((-0.04, -0.08, 0.2))))
key(ikT, DU1, loc=tuple(DUCK_L + Vector((-0.05, -0.08, 0.21))))
key(upT, DU0 - 1, loc=(0.12, 0.4, 1.3)); key(upT, DU0, loc=tuple(DUCK_L + Vector((0.0, 0.3, 0.05))))
key(faceT, DU0 - 1, loc=(0.0, 0.1, 0.62)); key(faceT, DU0, loc=tuple(DUCK_L + Vector((0, 0.0, -0.4))))
key(headT, DU0 - 1, loc=(0.15, 0.45, 0.52)); key(headT, DU0, loc=tuple(DUCK_L))
for o in (upT, faceT, headT):
    interp(o, "CONSTANT")
# o'rdak: suvda chayqaladi, ushlangach qo'l bilan ko'tariladi
GRAB = DU0 + 12
for f in range(1, END + 1, 4):
    if f >= DU0: break
    duckR.location = MEG + DUCK_L + Vector((0.01 * math.sin(f * 0.1), 0.01 * math.cos(f * 0.07), 0.003 * math.sin(f * 0.3)))
    duckR.rotation_euler = (R(3 * math.sin(f * 0.2)), R(3 * math.cos(f * 0.17)), R(200 + 6 * math.sin(f * 0.05)))
    duckR.keyframe_insert("location", frame=f); duckR.keyframe_insert("rotation_euler", frame=f)
duckR.location = MEG + DUCK_L; duckR.rotation_euler = (0, 0, R(200))
duckR.keyframe_insert("location", frame=GRAB); duckR.keyframe_insert("rotation_euler", frame=GRAB)
for f in range(GRAB + 1, DU1 + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    hm = meg.matrix_world @ meg.pose.bones["mixamorig:RightHand"].matrix
    palm = hm.to_3x3() @ Vector((0, 0, 1)); fing = hm.to_3x3() @ Vector((0, 1, 0))
    duckR.location = hm.translation + fing.normalized() * 0.06 + palm.normalized() * 0.05 + Vector((0, 0, -0.03))
    duckR.keyframe_insert("location", frame=f)
    duckR.rotation_euler = (R(-10), R(5), R(200)); duckR.keyframe_insert("rotation_euler", frame=f)
# suv sachrashi (o'rdak ko'tarilganda)
splash = []
for i in range(40):
    s_ = P.droplet(f"splash{i}", (0, 0, 0), rf.uniform(0.002, 0.006), None, drop_m, squash=1.0)
    v = Vector((rf.uniform(-0.6, 0.6), rf.uniform(-0.6, 0.6), rf.uniform(0.8, 1.6))) * 0.012
    p0 = MEG + DUCK_L + Vector((rf.uniform(-0.04, 0.04), rf.uniform(-0.04, 0.04), 0))
    for k in range(0, DU1 - GRAB + 2):
        f = GRAB + k; p = p0 + v * k + Vector((0, 0, -0.0012 * k * k))
        s_.location = p; s_.keyframe_insert("location", frame=f)
    vis(s_, [(GRAB + 1, DU1)], recursive=False); splash.append(s_)

# rentgen nusxasi (shaffof Megan + miya + asab yo'li)
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.4, base=0.015)
ghosts = []
for o in mmeshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    g.hide_render = False; ghosts.append(g)
X_SHOTS = rng("brain", "nerve_arm")
BATH_SHOTS = rng("bath_wide", "hand_look", "duck")
for g in ghosts: vis(g, X_SHOTS, recursive=False)
for o in mmeshes:
    if not any(k in o.name for k in ("Pants", "Sneakers")): vis(o, BATH_SHOTS, recursive=False)
    else: vis(o, [], recursive=False)
headE = empty("meg_head")
c = headE.constraints.new("CHILD_OF"); c.target = meg; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
brain, brain_m = P.build_brain("brain", headE, size=0.074)
brain.location = (0, 0.11, 0.03); brain.rotation_euler = (R(-90), 0, 0)
vis(brain, X_SHOTS)
BR0, BR1 = S["brain"]
P.mat_value(brain_m, "glow", 1, 0.0); P.mat_value(brain_m, "glow", BR0, 0.4)
for f in range(BR0 + 6, BR1, 7):
    P.mat_value(brain_m, "glow", f, 6.0); P.mat_value(brain_m, "glow", f + 3, 1.5)
NA0, NA1 = S["nerve_arm"]
P.mat_value(brain_m, "glow", NA0, 3.0); P.mat_value(brain_m, "glow", NA0 + 6, 1.0)
# asab yo'li: miyadan qo'l uchigacha (suyak boshlari bo'ylab, har kadr yangilanadi)
BONES = ["Head", "Neck", "Spine2", "RightShoulder", "RightArm", "RightForeArm", "RightHand", "RightHandIndex1", "RightHandIndex2",
         "RightHandIndex3", "RightHandIndex4"]
arm_nrv_m = P.pulse_material("arm_nerve", (0.95, 0.8, 0.2), base_emit=0.6, pulse_col=(1.0, 0.9, 0.35), width=0.07)
cu = bpy.data.curves.new("arm_nerve", "CURVE"); cu.dimensions = "3D"; cu.resolution_u = 16
sp = cu.splines.new("NURBS"); sp.points.add(len(BONES)); sp.use_endpoint_u = True; sp.order_u = 3
anerve = bpy.data.objects.new("arm_nerve", cu); sc.collection.objects.link(anerve); cu.materials.append(arm_nrv_m)
_m = anerve.modifiers.new("tube", "NODES"); _m.node_group = P.tube_group()
P.set_mod(anerve, "tube", next(it.identifier for it in P.tube_group().interface.items_tree if getattr(it, "name", "") == "Radius"), 0.0045)
for f in range(NA0 - 1, NA1 + 2):
    sc.frame_set(f); bpy.context.view_layer.update()
    pts = [brain.matrix_world.translation.copy()]
    for bn in BONES:
        pts.append(meg.matrix_world @ meg.pose.bones["mixamorig:" + bn].head)
    pts[1] = pts[0] * 0.5 + pts[1] * 0.5
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1.0); sp.points[i].keyframe_insert("co", frame=f)
vis(anerve, rng("nerve_arm"), recursive=False)
P.mat_value(arm_nrv_m, "pos", 1, -0.1); P.mat_value(arm_nrv_m, "pos", NA0 + 4, -0.05); P.mat_value(arm_nrv_m, "pos", NA1 - 4, 1.15)
hand_glow = P.pulse_material("hand_glow", (1.0, 0.85, 0.3), base_emit=0.0)
P.mat_value(hand_glow, "glow", 1, 0.0); P.mat_value(hand_glow, "glow", NA1 - 6, 0.0); P.mat_value(hand_glow, "glow", NA1 - 2, 25.0)
handE = empty("meg_hand")
c = handE.constraints.new("CHILD_OF"); c.target = meg; c.subtarget = "mixamorig:RightHandIndex3"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
sphere("hand_flash", 0.012, (0, 0, 0), hand_glow, parent=handE)
vis(handE, rng("nerve_arm"))
vis(bath, BATH_SHOTS); vis(foamR, BATH_SHOTS); vis(duckR, BATH_SHOTS)

# ======================================================================
# 7) LABORATORIYA + OLIVIA (40,0,0)
# ======================================================================
LB = Vector((40, 0, 0))
lab = empty("lab", tuple(LB))
plane("lab_floor", (6, 6), tuple(LB), pbr("lab_floor_m", "laminate_floor_02", 1.0, tint=(0.8, 0.82, 0.85)), parent=lab)
lab_wall = pbr("lab_wall_m", "painted_plaster_wall", 0.7, tint=(0.82, 0.9, 0.95))
for nm, sz, loc, rot in (("lw_back", (6, 3), (0, 2.4, 1.5), (90, 0, 180)), ("lw_left", (6, 3), (-2.2, 0, 1.5), (90, 0, 90)),
                         ("lw_right", (6, 3), (2.2, 0, 1.5), (90, 0, -90)), ("lw_front", (6, 3), (0, -1.8, 1.5), (90, 0, 0))):
    plane(nm, sz, tuple(LB + Vector(loc)), lab_wall, rot=rot, parent=lab)
table_m = mat("table", (0.92, 0.93, 0.95), 0.25, coat=0.4)
box("lab_table", (2.2, 0.8, 0.06), tuple(LB + Vector((0, 0.75, 0.9))), table_m, parent=lab)
box("lab_table_base", (2.1, 0.7, 0.86), tuple(LB + Vector((0, 0.78, 0.44))), mat("cab", (0.25, 0.35, 0.45), 0.4), parent=lab)
mic = empty("micro", (-0.45, 0.72, 0.93), lab); mic.rotation_euler = (0, 0, R(160))
import_gltf(PH + "vintage_microscope/vintage_microscope.gltf", mic); mic.scale = (1.6, 1.6, 1.6)
liq_cols = [(0.2, 0.6, 1.0), (0.3, 1.0, 0.5), (1.0, 0.4, 0.2), (0.9, 0.2, 0.6)]
gl_m = mat("labglass", (0.95, 0.98, 1.0), 0.02, trans=1.0)
for i in range(7):
    x = 0.15 + i * 0.12; h = 0.12 + 0.05 * (i % 3)
    cyl(f"beaker{i}", 0.035, h, tuple(LB + Vector((x, 0.85 + 0.08 * (i % 2), 0.93 + h / 2))), gl_m, parent=lab)
    lm = mat(f"liq{i}", liq_cols[i % 4], 0.05, trans=0.6, emit=0.8)
    cyl(f"liquid{i}", 0.031, h * 0.5, tuple(LB + Vector((x, 0.85 + 0.08 * (i % 2), 0.93 + h * 0.25 + 0.003))), lm, parent=lab)
shelf_m = mat("shelf", (0.85, 0.85, 0.85), 0.4)
for k in range(3):
    box(f"shelf{k}", (2.0, 0.3, 0.03), tuple(LB + Vector((0, 2.2, 1.35 + k * 0.42))), shelf_m, parent=lab)
    for i in range(12):
        hh = 0.12 + 0.12 * random.random()
        cyl(f"bottle{k}_{i}", 0.04, hh, tuple(LB + Vector((-0.9 + i * 0.16, 2.2, 1.365 + k * 0.42 + hh / 2))),
            mat(f"bm{k}{i}", liq_cols[(i + k) % 4], 0.1, trans=0.5, emit=0.3), parent=lab)
scr_m = mat("screen", (0.25, 0.65, 1.0), 0.2, emit=3.0)
box("monitor", (0.62, 0.04, 0.38), tuple(LB + Vector((0.7, 1.05, 1.25))), scr_m, parent=lab)
oroot, oliv, omeshes = mc.load_character("oliv", "Olivia.fbx")
soften(omeshes)
oroot.location = LB + Vector((0.05, 0.0, 0)); oroot.rotation_euler = (0, 0, R(180))
LA0, LA1 = S["lab"]
mc.add_strip(oliv, A_("Lifting.fbx"), LA0 - 78, blend=0)
tube_m = mat("ttube", (0.95, 0.98, 1.0), 0.02, trans=1.0)
ttE = empty("olv_hand")
c = ttE.constraints.new("CHILD_OF"); c.target = oliv; c.subtarget = "mixamorig:RightHand"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
tt = cyl("testtube", 0.012, 0.15, (0.0, 0.09, 0.03), tube_m, parent=ttE)
cyl("testtube_liq", 0.0105, 0.07, (0.0, 0.055, 0.03), mat("tt_liq", (0.2, 0.7, 1.0), 0.05, trans=0.5, emit=1.5), parent=ttE)
vis(lab, rng("lab")); vis(oroot, rng("lab")); vis(ttE, rng("lab"))

# ======================================================================
# 8) HO'L ASFALT + SHINA (0,-80,0)
# ======================================================================
RD = Vector((0, -80, 0))
road = empty("road", tuple(RD))
asph = pbr("asphalt_wet", "asphalt_02", 0.6, tint=(0.55, 0.55, 0.58), rough_mul=0.25)
bpy.ops.mesh.primitive_plane_add(size=1, location=tuple(RD)); rp = bpy.context.object; rp.name = "asphalt"
rp.scale = (40, 12, 1); bpy.ops.object.transform_apply(scale=True); rp.data.materials.append(asph); _par(rp, road)
puddle = P.water_material("puddle", tint=(0.9, 0.93, 0.95), rough=0.07)
bpy.ops.mesh.primitive_plane_add(size=1, location=tuple(RD + Vector((0, 0, 0.004)))); pd = bpy.context.object; pd.name = "puddle"
pd.scale = (40, 3.0, 1); bpy.ops.object.transform_apply(scale=True)
pnz = bpy.data.textures.new("puddle_nz", "CLOUDS"); pnz.noise_scale = 0.03
for _ in range(1): pd.modifiers.new("sub", "SUBSURF").levels = 0
pd.data.materials.append(puddle); _par(pd, road)
tireP = empty("tireP", tuple(RD))
tire_objs = import_gltf(BK + "08efeffa_u.glb", tireP)
tlo, thi = bbox(tire_objs)
TR = (thi.z - tlo.z) / 2
tire_c = (tlo + thi) / 2
print("TIRE", tuple(round(v, 3) for v in tlo), tuple(round(v, 3) for v in thi))
# shinani markazga keltirish: o'qi Y bo'ylab
for o in tire_objs:
    if o.parent == tireP: o.location -= (tire_c - tireP.location)
TI0, TI1 = S["tire"]
SPEED = 0.19
for f in range(TI0 - 2, TI1 + 3):
    t = f - TI0
    x = 3.0 - SPEED * t
    tireP.location = RD + Vector((x, 0, TR + 0.002)); tireP.keyframe_insert("location", frame=f)
    tireP.rotation_euler = (0, -(-SPEED * t) / TR * -1, 0); tireP.keyframe_insert("rotation_euler", frame=f)
# sachratqilar: g'ildirak ostidan orqaga va yonga
spray = []; rr_ = random.Random(9)
for i in range(120):
    r_ = rr_.uniform(0.004, 0.012)
    s_ = P.droplet(f"spray{i}", (0, 0, 0), r_, None, drop_m, squash=1.0)
    t0 = TI0 + rr_.randint(-6, TI1 - TI0 - 4)
    v = Vector((rr_.uniform(0.04, 0.14), rr_.choice((-1, 1)) * rr_.uniform(0.02, 0.09), rr_.uniform(0.04, 0.12)))
    for f in range(max(TI0, t0), TI1 + 1):
        k = f - t0
        if k < 0: continue
        x0 = 3.0 - SPEED * (t0 - TI0) + 0.25
        p = RD + Vector((x0 + v.x * k, v.y * k, 0.01 + v.z * k - 0.008 * k * k))
        if p.z < 0.005: p.z = 0.005
        s_.location = p; s_.keyframe_insert("location", frame=f)
    s_.scale = (0.001,) * 3; s_.keyframe_insert("scale", frame=max(TI0, t0) - 1)
    s_.scale = (1, 1, 1); s_.keyframe_insert("scale", frame=max(TI0, t0))
    interp(s_, "CONSTANT", "scale")
    spray.append(s_)
for s_ in spray: vis(s_, rng("tire"), recursive=False)
vis(road, rng("tire")); vis(tireP, rng("tire"))

# ======================================================================
# 9) KAMERALAR
# ======================================================================
# 1 ilgak
hT = empty("hookT", (0.0, -0.008, 0.017))
c = shot_cam("hook", (0.004, -0.095, 0.004), hT, 50, 22.0, focus=hT)
key(c, 1, loc=(0.008, -0.105, 0.0025)); key(c, S["hook"][1], loc=(0.003, -0.075, 0.004))
# 2 hammom keng, past burchak
bwT = empty("bwT", tuple(MEG + Vector((0, 0.05, 0.55))))
c = shot_cam("bath_wide", tuple(BA + Vector((0.95, 2.3, 0.85))), bwT, 16, 5.6, focus=bwT)
key(c, S["bath_wide"][0], loc=tuple(BA + Vector((1.0, 2.4, 0.8)))); key(c, S["bath_wide"][1], loc=tuple(BA + Vector((0.8, 1.95, 0.88))))
# 3 time-lapse makro + crash zoom
tlT = empty("tlT", tuple(B0 + Vector((0.0, -0.008, -0.012))))
c = shot_cam("timelapse", tuple(B0 + Vector((0.006, -0.09, -0.006))), tlT, 35, 22.0, focus=tlT)
lens_keys(c, ((T0, 26), (T0 + 5, 44), (T1, 48)))
key(c, T0, loc=tuple(B0 + Vector((0.006, -0.09, -0.006)))); key(c, T1, loc=tuple(B0 + Vector((0.004, -0.08, -0.004))))
# 4 qo'lga qaraydi: yuzga yaqin, DOF
megFace = empty("megFace", (0, 0, 0))
c2 = megFace.constraints.new("CHILD_OF"); c2.target = meg; c2.subtarget = "mixamorig:Head"
c2.use_scale_x = c2.use_scale_y = c2.use_scale_z = False; c2.inverse_matrix = Matrix.Identity(4)
megFace2 = empty("megFace2", (0, 0.09, 0.07), megFace)
c = shot_cam("hand_look", tuple(MEG + Vector((0.5, 0.78, 0.5))), megFace2, 45, 2.0, focus=megFace2)
key(c, HL0, loc=tuple(MEG + Vector((0.52, 0.8, 0.48)))); key(c, HL1, loc=tuple(MEG + Vector((0.45, 0.72, 0.52))))
# 5-6 teri kesimi: afsona va "noto'g'ri"
sT = empty("secT", tuple(SEC0 + Vector((0, 0, 0.75))))
c = shot_cam("myth", tuple(SEC0 + Vector((1.5, -2.6, 2.3))), sT, 30, 6.0, focus=sT)
key(c, MY0, loc=tuple(SEC0 + Vector((1.6, -2.7, 2.4)))); key(c, MY1, loc=tuple(SEC0 + Vector((1.3, -2.3, 2.1))))
wT = empty("wrongT", tuple(SEC0 + Vector((0.0, -0.1, 1.0))))
c = shot_cam("wrong", tuple(SEC0 + Vector((-1.0, -2.3, 2.3))), wT, 24, 6.0, focus=wT)
lens_keys(c, ((WR0, 22), (WR0 + 5, 40), (WR1, 44)))
shake(c, WR0, WR0 + 14, 0.06, 3)
# 7 rentgen: miya, crash zoom
c = shot_cam("brain", tuple(MEG + Vector((0.32, 0.85, 0.78))), megFace2, 30, 4.0, focus=megFace2)
lens_keys(c, ((BR0, 28), (BR0 + 6, 55), (BR1, 62)))
shake(c, BR0 + 5, BR0 + 15, 0.008, 4)
# 8 suv osti
uT = empty("underT", (0.06, -0.004, -0.058))
c = shot_cam("under", (0.035, -0.075, -0.085), uT, 40, 14.0, focus=uT)
key(c, S["under"][0], loc=(0.032, -0.08, -0.088)); key(c, S["under"][1], loc=(0.04, -0.06, -0.08))
# 9 asab signali miya -> qo'l
naT = empty("naT", tuple(MEG + Vector((0.12, 0.15, 0.42))))
c = shot_cam("nerve_arm", tuple(MEG + Vector((0.75, 1.05, 0.62))), naT, 24, 5.0, focus=naT)
key(c, NA0, loc=tuple(MEG + Vector((0.8, 1.1, 0.65)))); key(c, NA1, loc=tuple(MEG + Vector((0.65, 0.95, 0.58))))
# 10 barmoq ichi (rentgen)
xT = empty("xT", tuple(X0 + Vector((0, 0.0, 0.64))))
c = shot_cam("vessels", tuple(X0 + Vector((0.35, -0.6, 0.66))), xT, 30, 8.0, focus=xT)
key(c, V0, loc=tuple(X0 + Vector((0.4, -0.68, 0.62)))); key(c, V1, loc=tuple(X0 + Vector((0.28, -0.5, 0.7))))
# 11 tomirlar torayadi (old kesimga yaqin)
sT2 = empty("secT2", tuple(SEC0 + Vector((0.0, -0.6, 0.6))))
c = shot_cam("shrink", tuple(SEC0 + Vector((0.9, -2.7, 1.5))), sT2, 30, 6.0, focus=sT2)
key(c, SH0, loc=tuple(SEC0 + Vector((1.0, -2.8, 1.55)))); key(c, SH1, loc=tuple(SEC0 + Vector((0.75, -2.4, 1.35))))
# 12 burmalar: pastroqdan, yuqori qatlam silueti
sT3 = empty("secT3", tuple(SEC0 + Vector((0.0, -0.3, 0.95))))
c = shot_cam("folds", tuple(SEC0 + Vector((-0.4, -2.3, 1.45))), sT3, 32, 5.0, focus=sT3)
key(c, FO0, loc=tuple(SEC0 + Vector((-0.5, -2.4, 1.5)))); key(c, FO1, loc=tuple(SEC0 + Vector((-0.2, -1.9, 1.35))))
# 13 aylanma makro
O0, O1 = S["orbit"]
oT = empty("orbT", tuple(B0 + Vector((0.0, -0.004, -0.012))))
c = shot_cam("orbit", (0, 0, 0), oT, 45, 22.0, focus=oT)
for f in range(O0, O1 + 1, 2):
    a = R(-55 + 85 * (f - O0) / (O1 - O0))
    key(c, f, loc=tuple(B0 + Vector((0.075 * math.sin(a), -0.075 * math.cos(a), -0.004))))
# 14 uzilgan asab
c = shot_cam("nerve_cut", tuple(X0 + Vector((-0.4, -0.6, 0.55))), empty("xT2", tuple(X0 + Vector((0, 0.0, 0.58)))), 30, 8.0)
key(c, NC0, loc=tuple(X0 + Vector((-0.45, -0.68, 0.56)))); key(c, NC1, loc=tuple(X0 + Vector((-0.3, -0.48, 0.55))))
shake(c, NC0 + 18, NC0 + 28, 0.02, 6)
# 15 ikki barmoq
twT = empty("twT", tuple(B0 + Vector((0.013, -0.006, -0.012))))
c = shot_cam("two", tuple(B0 + Vector((0.0, -0.11, -0.004))), twT, 40, 22.0, focus=twT)
key(c, S["two"][0], loc=tuple(B0 + Vector((-0.004, -0.11, -0.004)))); key(c, S["two"][1], loc=tuple(B0 + Vector((0.03, -0.1, -0.002))))
# 16 laboratoriya: pastdan
olvF = empty("olvFace", (0, 0, 0))
c2 = olvF.constraints.new("CHILD_OF"); c2.target = oliv; c2.subtarget = "mixamorig:Head"
c2.use_scale_x = c2.use_scale_y = c2.use_scale_z = False; c2.inverse_matrix = Matrix.Identity(4)
olvF2 = empty("olvFace2", (0, 0.06, 0.06), olvF)
labT = empty("labT", tuple(LB + Vector((0.0, 0.05, 1.32))))
c = shot_cam("lab", tuple(LB + Vector((-1.5, 1.0, 1.0))), labT, 22, 4.0, focus=olvF2)
key(c, LA0, loc=tuple(LB + Vector((-1.55, 1.05, 0.98)))); key(c, LA1, loc=tuple(LB + Vector((-1.35, 0.9, 1.05))))
# 17 shina: asfalt sathida, g'ildirakni kuzatadi
tT = empty("tireT", (0, 0, 0), None)
for f in range(TI0, TI1 + 1):
    sc.frame_set(f); key(tT, f, loc=tuple(tireP.location + Vector((0, 0, -TR * 0.55))))
c = shot_cam("tire", tuple(RD + Vector((-5.4, -0.32, 0.06))), tT, 22, 5.6, focus=tT)
key(c, TI0, loc=tuple(RD + Vector((-5.4, -0.32, 0.06)))); key(c, TI1, loc=tuple(RD + Vector((-5.6, -0.42, 0.08))))
# 18 shisha ostidan
gT = empty("glassT", tuple(C0 + Vector((0.0, 0.006, 0.006))))
c = shot_cam("glass", tuple(C0 + Vector((0.06, -0.035, 0.006))), gT, 40, 22.0, focus=gT)
key(c, G0, loc=tuple(C0 + Vector((0.065, -0.04, 0.008)))); key(c, G1, loc=tuple(C0 + Vector((0.05, -0.03, 0.005))))
shake(c, TOUCH, TOUCH + 8, 0.0012, 2)
# 19 o'rdak: suv sathidan, crash zoom ushlaganda
dkT = empty("duckT", tuple(MEG + DUCK_L + Vector((-0.02, -0.05, 0.12))))
c = shot_cam("duck", tuple(MEG + DUCK_L + Vector((0.5, 0.6, 0.24))), dkT, 26, 3.5, focus=duckR)
lens_keys(c, ((DU0, 24), (GRAB, 26), (GRAB + 4, 40), (DU1, 44)))
shake(c, GRAB, GRAB + 10, 0.01, 8)

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 10) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
def env_bg(file, rot):
    mp = N.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, R(rot)); L.new(tcw.outputs["Generated"], mp.inputs[0])
    e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + file); L.new(mp.outputs[0], e.inputs[0])
    bgn = N.new("ShaderNodeBackground"); L.new(e.outputs[0], bgn.inputs[0]); return bgn
bg_st = env_bg("studio_small_09.hdr", 40); bg_oc = env_bg("kloofendal_overcast_puresky.hdr", 120)
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.012, 0.03, 1)
a1 = N.new("ShaderNodeAddShader"); a2 = N.new("ShaderNodeAddShader")
L.new(bg_st.outputs[0], a1.inputs[0]); L.new(bg_oc.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], a2.inputs[0]); L.new(bg_dk.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], out.inputs["Surface"])
# (studio, osmon, qorong'i)
WL = {"hook": (0.55, 0, 0), "bath_wide": (0.25, 0, 0), "timelapse": (0.5, 0, 0), "hand_look": (0.25, 0, 0), "myth": (0, 0, 1.0),
      "wrong": (0, 0, 1.0), "brain": (0, 0, 1.0), "under": (0.3, 0, 0), "nerve_arm": (0, 0, 1.0), "vessels": (0, 0, 1.0),
      "shrink": (0, 0, 1.0), "folds": (0, 0, 1.0), "orbit": (0.5, 0, 0), "nerve_cut": (0, 0, 1.0), "two": (0.5, 0, 0),
      "lab": (0.35, 0, 0), "tire": (0, 1.0, 0), "glass": (0.6, 0, 0), "duck": (0.25, 0, 0)}
for f, n in SHOTS:
    s1, s2, s3 = WL[n]
    for bgn, v in ((bg_st, s1), (bg_oc, s2), (bg_dk, s3)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# makro A
A_on = rng("hook")
area("A_key", (-0.12, -0.12, 0.16), 0.12, (1, 0.96, 0.9), lights_for(A_on, 4.0), target=hT)
area("A_rim", (0.1, 0.12, 0.08), 0.06, (1.0, 0.75, 0.5), lights_for(A_on, 3.0), target=hT)
area("A_fill", (0.1, -0.15, 0.03), 0.1, (0.8, 0.9, 1.0), lights_for(A_on, 1.2), target=hT)
area("U_key", (0.02, -0.02, -0.01), 0.08, (0.85, 0.95, 1.0), lights_for(rng("under"), 1.6), target=uT)
area("U_rim", (0.1, 0.06, -0.03), 0.05, (0.5, 0.85, 1.0), lights_for(rng("under"), 1.5), target=uT)
area("U_low", (0.03, -0.06, -0.13), 0.08, (0.4, 0.7, 0.9), lights_for(rng("under"), 0.8), target=uT)
# makro B
B_on = rng("timelapse", "orbit", "two")
area("B_key", tuple(B0 + Vector((-0.12, -0.12, 0.15))), 0.12, (1, 0.95, 0.88), lights_for(B_on, 4.0), target=tlT)
area("B_rim", tuple(B0 + Vector((0.08, 0.14, 0.1))), 0.06, (1.0, 0.7, 0.45), lights_for(B_on, 3.5), target=tlT)
area("B_fill", tuple(B0 + Vector((0.14, -0.1, 0.0))), 0.1, (0.8, 0.88, 1.0), lights_for(B_on, 1.0), target=tlT)
area("B_back", tuple(B0 + Vector((0, 0.15, 0.4))), 0.4, (1, 0.85, 0.7), lights_for(B_on, 8.0), target=empty("bbT", tuple(B0 + Vector((0, 0.3, 0.1)))))
# shisha
area("C_key", tuple(C0 + Vector((-0.08, 0.05, 0.2))), 0.15, (1, 0.95, 0.9), lights_for(rng("glass"), 5.0), target=gT)
area("C_under", tuple(C0 + Vector((0.06, -0.08, -0.05))), 0.08, (1.0, 0.92, 0.85), lights_for(rng("glass"), 3.5), target=gT)
# rentgen barmoq
area("X_rim", tuple(X0 + Vector((-0.6, 0.6, 0.6))), 0.6, (0.3, 0.6, 1.0), lights_for(rng("vessels", "nerve_cut"), 30.0), target=xT)
# teri kesimi
SEC_on = rng("myth", "wrong", "shrink", "folds")
area("S_key", tuple(SEC0 + Vector((-2.0, -2.0, 3.0))), 2.0, (1, 0.95, 0.9), lights_for(SEC_on, 900.0), target=sT)
area("S_rim", tuple(SEC0 + Vector((1.5, 2.5, 2.0))), 1.5, (0.4, 0.65, 1.0), lights_for(SEC_on, 700.0), target=sT)
area("S_red", tuple(SEC0 + Vector((-2.2, -1.8, 1.4))), 1.5, (1.0, 0.08, 0.04), lights_for(rng("wrong"), 2200.0), target=sT)
area("S_red2", tuple(SEC0 + Vector((1.5, 2.0, 2.5))), 1.5, (1.0, 0.1, 0.05), lights_for(rng("wrong"), 1500.0), target=sT)
area("S_blue", tuple(SEC0 + Vector((2.5, -1.0, 2.0))), 1.5, (0.3, 0.6, 1.0), lights_for(rng("myth"), 600.0), target=sT)
# hammom
BT_on = BATH_SHOTS
area("bath_ceil", tuple(BA + Vector((0, 0.6, 2.7))), 1.0, (1.0, 0.9, 0.8), lights_for(BT_on, 120.0), target=bwT)
area("bath_win", tuple(BA + Vector((1.1, 0.2, 1.6))), 1.0, (1.0, 0.96, 0.92), lights_for(BT_on, 220.0), target=bwT)
area("face_key", tuple(MEG + Vector((0.6, 0.6, 1.0))), 0.6, (1.0, 0.92, 0.85), lights_for(rng("hand_look", "duck"), 30.0), target=megFace2)
area("face_rim", tuple(MEG + Vector((-0.5, -0.1, 1.1))), 0.4, (1.0, 0.7, 0.45), lights_for(rng("hand_look", "duck"), 40.0), target=megFace2)
# rentgen tana
area("X_body_rim", tuple(MEG + Vector((-0.8, -0.4, 1.2))), 0.8, (0.3, 0.6, 1.0), lights_for(X_SHOTS, 40.0), target=megFace2)
# laboratoriya
area("lab_back", tuple(LB + Vector((-0.5, -0.6, 2.5))), 1.5, (0.75, 0.88, 1.0), lights_for(rng("lab"), 250.0), target=empty("lbT", tuple(LB + Vector((0, -1.8, 1.2)))))
area("lab_ceil", tuple(LB + Vector((0, 0.6, 2.8))), 1.6, (0.9, 0.95, 1.0), lights_for(rng("lab"), 300.0), target=labT)
area("lab_rim", tuple(LB + Vector((1.2, -1.0, 2.0))), 0.8, (0.4, 0.7, 1.0), lights_for(rng("lab"), 150.0), target=olvF2)
area("lab_face", tuple(LB + Vector((-0.6, 1.4, 1.6))), 0.6, (1.0, 0.95, 0.9), lights_for(rng("lab"), 60.0), target=olvF2)
# yo'l
area("road_rim", tuple(RD + Vector((-3, 3, 2.0))), 2.0, (0.8, 0.9, 1.0), lights_for(rng("tire"), 600.0), target=tT)

# ======================================================================
# 11) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 8; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 8
sc.cycles.volume_bounces = 1
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.35
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
