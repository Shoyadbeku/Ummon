# Tish sug'urilgach jag' suyagi yemiriladi — Zack D. Films uslubida 43.75 s video (1050 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py + burish/burish.py; procedural modellar: tish/teeth.py, tish/parts.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/tish/tish.py --render
# Sinov: FRAMES=30,80,180,330,700 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
import teeth as T
sc = bpy.context.scene
sc.render.fps = 24
END = 1050
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan) ----------------
SHOTS = [(1, "hook"), (51, "pull"), (111, "tray"), (144, "xjaw"), (231, "root"), (295, "bite"), (364, "signal"),
         (466, "empty"), (552, "think"), (629, "calcium"), (713, "shrink"), (829, "tilt"), (913, "sink"), (977, "old")]
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
    for x in objs:
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

mat = lambda *a, **k: T._pm(*a, **k)

def pbr(name, folder, scale=1.0, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = "BOX"; t.projection_blend = 0.25
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

def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3
        for p in o.data.polygons: p.use_smooth = True
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 3000
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

def area(name, loc, size, col, keys, target=None, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c

def mv(m, name, f, v):                       # material qiymatini keyframe qilish
    P.mat_value(m, name, f, v)

# ======================================================================
# 1) JAG' KESIMI (dunyo markazi, 1 birlik = 1 sm)
# ======================================================================
SECR = rng("root", "bite", "signal", "empty", "calcium")       # tish uyasi bor kesim
SECH = rng("shrink")                                            # bitgan (uyasiz), cho'kadigan kesim
SEC_ALL = SECR + SECH
cort, spongy = T.bone_materials()
secA = T.build_section("secA", socket=True)
secB = T.build_section("secB", socket=False)
for o in secB.values(): T.sink_shapekey(o, depth=0.75, sigma=0.9)
for o in secA.values(): vis(o, SECR, recursive=False)
for o in secB.values(): vis(o, SECH, recursive=False)
SH0, SH1 = S["shrink"]
for o in secB.values():
    kb = o.data.shape_keys.key_blocks["sink"]
    for f, v in ((SH0, 0.0), (SH0 + 10, 0.0), (SH1 - 12, 1.0)):
        kb.value = v; kb.keyframe_insert("value", frame=f)
# pastki tish (kesimdagi)
toothS, toothS_parts = T.build_tooth("toothS", "molar")
# yuqori blok: teskari tish + milk
upE = empty("upper_unit", (0, 0, 3.4))
toothU, _ = T.build_tooth("toothU", "molar", upE); toothU.rotation_euler = (R(180), 0, R(180))
box("upper_gum", (2.6, 1.4, 0.9), (0, 0.55, 0.42), T.gum_material(), parent=upE, bevel=0.15)
# ovqat bo'lagi (olma)
apple_m = T._pm("apple", (0.95, 0.88, 0.62), 0.35, sss=0.6, coat=0.6, sss_scale=0.05)
T._noise_col(apple_m, 12.0, (0.9, 0.8, 0.5), (0.98, 0.94, 0.75), bump=0.2)
food = box("food", (0.85, 0.7, 0.45), (0, 0.0, 0.88), apple_m, bevel=0.12)
food.location = (0, 0, 0.88)

UP_OPEN, UP_TOUCH = 3.4, 1.27
BI0, BI1 = S["bite"]; SI0, SI1 = S["signal"]; EM0, EM1 = S["empty"]
key(upE, 1, loc=(0, 0, UP_OPEN)); key(upE, BI0, loc=(0, 0, UP_OPEN)); key(upE, BI0 + 30, loc=(0, 0, 2.2))
CONTACT1 = BI0 + 46                                 # "bosim" (14.6 s)
key(upE, CONTACT1 - 4, loc=(0, 0, 1.72)); key(upE, CONTACT1, loc=(0, 0, 1.42)); key(upE, BI1, loc=(0, 0, 1.4))
# ovqat eziladi
key(food, BI0, scale=(1, 1, 1)); key(food, CONTACT1 - 4, scale=(1, 1, 1)); key(food, CONTACT1, scale=(1.45, 1.25, 0.28))
key(food, BI0, loc=(0, 0, 0.88)); key(food, CONTACT1 - 4, loc=(0, 0, 0.88)); key(food, CONTACT1, loc=(0, 0, 0.7))
vis(food, rng("bite"))
# chaynash (signal): 3 marta
CHEW = [SI0 + 8, SI0 + 40, SI0 + 72]
key(upE, SI0, loc=(0, 0, 1.6))
for c in CHEW:
    key(upE, c - 9, loc=(0, 0, 2.3)); key(upE, c, loc=(0, 0, UP_TOUCH)); key(upE, c + 3, loc=(0, 0, UP_TOUCH + 0.02))
key(upE, SI1, loc=(0, 0, 2.2))
# tish sug'uriladi (empty), keyin bo'shliqqa tishlash
PULL0 = EM0 + 4
key(toothS, 1, loc=(0, 0, 0), rot=(0, 0, 0)); key(toothS, PULL0, loc=(0, 0, 0), rot=(0, 0, 0))
key(toothS, PULL0 + 5, loc=(0, 0, 0.05), rot=(0, 6, 0)); key(toothS, PULL0 + 9, loc=(0, 0, 0.12), rot=(0, -7, 0))
key(toothS, PULL0 + 13, loc=(0, 0, 0.3), rot=(0, 4, 0)); key(toothS, PULL0 + 24, loc=(0.4, -0.3, 6.5), rot=(0, -25, 30))
key(upE, EM0, loc=(0, 0, 4.5)); key(upE, EM0 + 40, loc=(0, 0, 4.5))
EMPTY_BITE = EM0 + 62                               # "yuk tushmay qoladi" (22.4 s)
key(upE, EMPTY_BITE - 12, loc=(0, 0, 2.4)); key(upE, EMPTY_BITE, loc=(0, 0, 0.62)); key(upE, EM1, loc=(0, 0, 0.6))
vis(toothS, rng("root", "bite", "signal", "empty"))
vis(upE, rng("bite", "signal", "empty"))

# bosim to'lqinlari (halqalar) va signallar
ring_objs = []
APEX = [Vector((-0.42, -0.02, -1.25)), Vector((0.36, -0.02, -1.15))]
sig_m_base = T.glow_material("sig_dot", (1.0, 0.75, 0.25), 0.0)
for ci, c in enumerate(CHEW):
    for ai, ap in enumerate(APEX):
        for ri in range(2):
            f0 = c + ri * 5
            bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.025, major_segments=64, minor_segments=8,
                                             location=tuple(ap), rotation=(R(90), 0, 0))
            tr = bpy.context.object; tr.name = f"ring{ci}{ai}{ri}"
            m = T.glow_material(f"ring_m{ci}{ai}{ri}", (1.0, 0.78, 0.3), 0.0); tr.data.materials.append(m)
            for f, s_, g in ((f0 - 1, 0.05, 0.0), (f0, 0.05, 12.0), (f0 + 20, 1.6, 0.0)):
                tr.scale = (s_, s_, s_ * 0.6); tr.keyframe_insert("scale", frame=f); mv(m, "glow", f, g)
            ring_objs.append(tr)
    # signal nuqtalari: ildizdan suyakka
    rnd = random.Random(ci)
    for k in range(16):
        ap = APEX[k % 2]; a = rnd.uniform(0, 2 * math.pi); dist = rnd.uniform(0.6, 1.3)
        d = sphere(f"sig{ci}_{k}", 0.035, tuple(ap), sig_m_base, sub=2)
        p1 = ap + Vector((math.cos(a) * dist, -0.03, math.sin(a) * dist * 0.8))
        key(d, c - 1, loc=tuple(ap), scale=(0, 0, 0)); key(d, c, loc=tuple(ap), scale=(1, 1, 1))
        key(d, c + 16, loc=tuple(p1), scale=(1, 1, 1)); key(d, c + 20, loc=tuple(p1), scale=(0, 0, 0))
        ring_objs.append(d)
sig_m_base.node_tree.nodes["glow"].outputs[0].default_value = 10.0
for o in ring_objs: vis(o, rng("signal"), recursive=False)
# suyak "tirikligi": oltin nur, keyin qizarish
mv(spongy, "alive", 1, 0.0); mv(spongy, "alive", SI0, 0.0)
for c in CHEW:
    mv(spongy, "alive", c - 1, 0.6); mv(spongy, "alive", c + 2, 4.0); mv(spongy, "alive", c + 14, 1.0)
mv(spongy, "alive", SI1, 1.2); mv(spongy, "alive", EM0, 0.0)
mv(spongy, "sick", 1, 0.0); mv(spongy, "sick", EMPTY_BITE, 0.0); mv(spongy, "sick", EMPTY_BITE + 10, 0.35)
CA0, CA1 = S["calcium"]
mv(spongy, "sick", CA0, 0.4); mv(spongy, "sick", SH1, 0.75)
mv(spongy, "pores", 1, 0.0); mv(spongy, "pores", CA0, 0.15); mv(spongy, "pores", SH0, 0.25); mv(spongy, "pores", SH1 - 10, 1.0)

# qon tomiri va kalsiy zarrachalari
VZ = -2.0
vessel_m = P.pulse_material("vessel", (0.55, 0.03, 0.03), base_emit=0.2, pulse_col=(1.0, 0.15, 0.1), width=0.1)
vessel = P.tube("vessel", [(-2.4, -0.06, VZ), (-1.0, -0.08, VZ - 0.08), (0.4, -0.08, VZ + 0.05), (2.4, -0.06, VZ - 0.04)], 0.13, vessel_m)
vis(vessel, rng("calcium"))
mv(vessel_m, "pos", CA0, -0.1); mv(vessel_m, "pos", CA1, 1.2)
cal_m = T.glow_material("calcium", (0.95, 0.97, 1.0), 6.0)
rc = random.Random(3)
for k in range(46):
    f0 = CA0 + 4 + int(k * 1.4)
    p0 = Vector((rc.uniform(-1.0, 1.0), -0.05, rc.uniform(-1.3, -0.25)))
    pv = Vector((p0.x * 0.7 + rc.uniform(-0.2, 0.2), -0.12, VZ + 0.02))
    pe = Vector((2.8, -0.12, VZ))
    d = sphere(f"cal{k}", rc.uniform(0.03, 0.055), tuple(p0), cal_m, sub=2)
    key(d, f0 - 1, loc=tuple(p0), scale=(0, 0, 0)); key(d, f0 + 3, loc=tuple(p0), scale=(1, 1, 1))
    t1 = f0 + 18 + rc.randint(0, 6)
    key(d, t1, loc=tuple(pv), scale=(1, 1, 1))
    t2 = t1 + int((pe.x - pv.x) * 9)
    key(d, t2, loc=tuple(pe), scale=(1, 1, 1))
    vis(d, rng("calcium"), recursive=False)

# ======================================================================
# 2) OG'IZ ICHI: tish qatorlari (100,0,0) sm
# ======================================================================
AR = Vector((100, 0, 0))
archE = empty("arch_root", tuple(AR))
arch, ateeth, agum = T.build_arch("low", archE)
uarchE = empty("uarch_root", tuple(AR + Vector((0, 0, 2.25))))
uarch, uteeth, ugum = T.build_arch("up", uarchE, upper=True)
centers = arch["centers"]
pR5 = AR + Vector(centers["R5"][0]); tR5 = Vector(centers["R5"][1])
lingual = Vector((0, 0, 1)).cross(tR5).normalized()                 # arch markaziga qarab
if (Vector((AR.x, AR.y + 2.5, 0)) - pR5).dot(lingual) < 0: lingual = -lingual
# til, lunj, tanglay
mucosa = T.gum_material("mucosa", (0.72, 0.28, 0.3))
tongue = sphere("tongue", 1.0, tuple(AR + Vector((0, 2.6, -0.2))), T.gum_material("tongue_m", (0.78, 0.36, 0.38)), scale=(1.9, 2.6, 0.75), sub=4)
dt = tongue.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new("pap", "CLOUDS"); tx.noise_scale = 0.08; dt.texture = tx; dt.strength = 0.04
for sg in (1, -1):
    ch = sphere(f"cheek{sg}", 1.0, tuple(AR + Vector((sg * 3.9, 3.0, 1.0))), mucosa, scale=(0.6, 4.5, 2.2), sub=4)
sphere("throat", 1.0, tuple(AR + Vector((0, 7.5, 1.0))), T._pm("throat", (0.15, 0.02, 0.02), 0.5), scale=(3.5, 0.5, 3.5), sub=3)
# qon laxtasi (tish chiqqan joyda)
blood_m = T._pm("blood", (0.35, 0.01, 0.01), 0.08, coat=1.0)
clot = sphere("clot", 0.3, tuple(pR5 + Vector((0, 0, -0.03))), blood_m, scale=(1.0, 1.0, 0.25))
# qisqich
pullE = empty("pullE", tuple(pR5))
fc, (hgA, hgB) = T.build_forceps("forceps", pullE)
fc.rotation_euler = (0, 0, math.atan2(tR5.y, tR5.x))
ateeth["R5"].parent = pullE; ateeth["R5"].location = (0, 0, 0); ateeth["R5"].rotation_euler = (0, 0, math.atan2(tR5.y, tR5.x))
PU0, PU1 = S["pull"]
key(fc, 1, loc=(0, 0, 7.0)); key(fc, PU0, loc=(0, 0, 6.0)); key(fc, PU0 + 12, loc=(0, 0, 0.45))
for hg, sg in ((hgA, 1), (hgB, -1)):
    key(hg, 1, rot=(sg * -12, 0, 0)); key(hg, PU0 + 12, rot=(sg * -12, 0, 0)); key(hg, PU0 + 18, rot=(sg * 4.5, 0, 0))
GRIP = PU0 + 18
key(pullE, 1, loc=tuple(pR5), rot=(0, 0, 0)); key(pullE, GRIP, loc=tuple(pR5), rot=(0, 0, 0))
ax = tR5                                            # chayqatish o'qi: yoy urinmasi atrofida (lunj-til tomonga)
for i, a in enumerate((9, -9, 11, -6)):
    e = Euler((ax.x * R(a), ax.y * R(a), 0)); key(pullE, GRIP + 5 + i * 5, loc=tuple(pR5), rot=tuple(math.degrees(v) for v in e))
YANK = GRIP + 26                                    # "sug'urib" (3.2 s) dan keyin, "tashlash" bilan
key(pullE, YANK + 1, loc=tuple(pR5 + Vector((0, 0, 0.25))), rot=(0, 0, 4))
key(pullE, PU1, loc=tuple(pR5 + Vector((-0.3, -0.5, 4.2))), rot=(0, 0, 10))
for fcu in fcurves(pullE):
    for k in fcu.keyframe_points: k.interpolation = "BEZIER"
# milkda tish chiqqan joyning cho'kishi (tilt kadri uchun shape key)
def gum_dip(o, center_world, rad=0.85, depth=0.4):
    if not o.data.shape_keys: o.shape_key_add(name="Basis", from_mix=False)
    kb = o.shape_key_add(name="dip", from_mix=False); kb.value = 0.0
    inv = o.matrix_world.inverted(); bpy.context.view_layer.update(); cl = o.matrix_world.inverted() @ center_world
    for i, v in enumerate(o.data.vertices):
        d = math.hypot(v.co.x - cl.x, v.co.y - cl.y); g = math.exp(-(d / rad) ** 2)
        if v.co.z > cl.z - 0.6: kb.data[i].co = v.co - Vector((0, 0, depth * g))
    return kb
bpy.context.view_layer.update()
dip = gum_dip(agum, pR5)
TI0, TI1 = S["tilt"]
dip.value = 0; dip.keyframe_insert("value", frame=TI0 + 4); dip.value = 1; dip.keyframe_insert("value", frame=TI1 - 18)
# qo'shni tishlar bo'sh joyga og'adi, yuqoridagi tish pastga tushadi
for k, sg in (("R4", 1), ("R6", -1)):
    t = ateeth[k]; base = t.rotation_euler.copy()
    t.keyframe_insert("rotation_euler", frame=TI0 + 6)
    e = base.copy(); tiltax = Vector((0, 0, 1)).cross(tR5).normalized()
    m_ = Matrix.Rotation(R(17) * sg, 4, tiltax) @ base.to_matrix().to_4x4()
    t.rotation_euler = m_.to_euler(); t.keyframe_insert("rotation_euler", frame=TI1 - 14)
    t.rotation_euler = base; t.keyframe_insert("rotation_euler", frame=1); t.keyframe_insert("rotation_euler", frame=TI0 + 6)
u5 = uteeth["R5"]; z0 = u5.location.copy()
key(u5, 1, loc=tuple(z0)); key(u5, TI0 + 10, loc=tuple(z0)); key(u5, TI1 - 12, loc=tuple(z0 + Vector((0, 0, -0.45))))
# R5 (lunj-til) tishi tilt kadrida yo'q
vis(pullE, rng("pull"))
vis(clot, rng("pull"), recursive=False)
ARCH_SH = rng("pull", "tilt")
vis(archE, ARCH_SH); vis(uarchE, rng("tilt"))
vis(pullE, rng("pull"))
for o in ("tongue", "cheek1", "cheek-1", "throat"): vis(bpy.data.objects[o], rng("pull"), recursive=False)

# ======================================================================
# 3) LAGAN (200,0,0) sm: sug'urilgan tish tushadi
# ======================================================================
TRY = Vector((200, 0, 0))
trayE = empty("tray_root", (0, 0, 0))
tray = T.build_tray("tray", trayE); tray.location = tuple(TRY)
toothT, _ = T.build_tooth("toothT", "molar", None, root_mat=T.dentin_material("dentin_blood", blood=1.0))
TR0, TR1 = S["tray"]
FLOOR = TRY.z - 0.85 + 0.05 + 1.4          # tish ildizi uchi lagan tubiga tegadi (yonboshlab yotadi)
land = TRY + Vector((0.6, 0.4, -0.85 + 0.62))
key(toothT, TR0, loc=tuple(land + Vector((-0.8, -0.3, 7.5))), rot=(40, 20, 0))
key(toothT, TR0 + 9, loc=tuple(land), rot=(80, 60, 30))
key(toothT, TR0 + 14, loc=tuple(land + Vector((0.5, 0.2, 1.3))), rot=(110, 80, 70))
key(toothT, TR0 + 20, loc=tuple(land + Vector((0.9, 0.3, 0.0))), rot=(90, 95, 100))
key(toothT, TR0 + 24, loc=tuple(land + Vector((1.0, 0.32, 0.25))), rot=(90, 92, 105))
key(toothT, TR0 + 27, loc=tuple(land + Vector((1.05, 0.33, 0.0))), rot=(90, 90, 108))
interp(toothT, "LINEAR")
# qon tomchilari laganda
for k in range(5):
    sphere(f"tdrop{k}", random.uniform(0.08, 0.16), tuple(TRY + Vector((random.uniform(-2, 3), random.uniform(-1.5, 2), -0.84))),
           blood_m, scale=(1, 1, 0.2), parent=trayE)
# asboblar: oyna va zond, paxta
steel = T.steel_material()
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.12, depth=9.0, location=tuple(TRY + Vector((-2.5, -1.8, -0.7))), rotation=(0, R(90), R(12)))
tool1 = bpy.context.object; tool1.data.materials.append(steel); tool1.parent = trayE
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.9, depth=0.1, location=tuple(TRY + Vector((2.0, -2.5, -0.7))), rotation=(0, R(8), 0))
mirr = bpy.context.object; mirr.data.materials.append(T._pm("mirror", (0.95, 0.95, 0.95), 0.02, metal=1.0)); mirr.parent = trayE
for k in range(3):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.45, depth=1.9, location=tuple(TRY + Vector((-3.0 + k * 1.0, 2.2, -0.35))), rotation=(R(90), 0, R(10 * k)))
    cot = bpy.context.object; cot.data.materials.append(T._pm("cotton", (0.97, 0.97, 0.96), 0.9, sss=0.4)); cot.parent = trayE
    b = cot.modifiers.new("b", "BEVEL"); b.width = 0.3; b.segments = 4
    for p in cot.data.polygons: p.use_smooth = True
plane_m = T._pm("table_top", (0.85, 0.88, 0.9), 0.35)
box("tray_table", (80, 60, 1.0), tuple(TRY + Vector((0, 0, -1.5))), plane_m)
vis(trayE, rng("tray")); vis(toothT, rng("tray")); vis(bpy.data.objects["tray_table"], rng("tray"), recursive=False)

# ======================================================================
# 4) XONA + MEGAN (1000,0,0) m
# ======================================================================
RM = Vector((1000, 0, 0))
room = empty("room", tuple(RM))
floor_m = pbr("ph_floor", "laminate_floor_02", 0.5)
wall_m = pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.93, 0.86, 0.76))
box("r_floor", (8, 8, 0.05), tuple(RM + Vector((0, 1.0, -0.025))), floor_m, parent=room)
box("r_wall_b", (8, 0.1, 3.0), tuple(RM + Vector((0, 2.4, 1.5))), wall_m, parent=room)
box("r_wall_l", (0.1, 6, 3.0), tuple(RM + Vector((-2.6, 0.5, 1.5))), wall_m, parent=room)
box("r_wall_r", (0.1, 6, 3.0), tuple(RM + Vector((2.6, 0.5, 1.5))), wall_m, parent=room)
win_m = T._pm("r_window", (1.0, 0.96, 0.9), 0.3); win_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 6.0
win_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.95, 0.88, 1)
box("r_window", (0.02, 1.4, 1.5), tuple(RM + Vector((2.54, 1.0, 1.6))), win_m, parent=room)
def place(path, loc, rz=0, s=1.0):
    e = empty(os.path.basename(path).split(".")[0], tuple(loc), room); e.rotation_euler.z = R(rz); e.scale = (s, s, s)
    import_gltf(path, e); return e
place(PH + "Sofa_01/Sofa_01.gltf", RM + Vector((-0.4, 1.95, 0)), 0)
place(PH + "potted_plant_01/potted_plant_01.gltf", RM + Vector((1.6, 1.9, 0)), 0, 1.3)
place(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", RM + Vector((-0.6, 2.33, 1.55)), 0, 1.2)
ROOM_SH = rng("hook", "sink", "old")
vis(room, ROOM_SH)

mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx")
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
body = next(o for o in mmeshes if o.name.endswith("Body"))
hair = next(o for o in mmeshes if o.name.endswith("Hair"))
# qarish: tana materiali nusxasi (ajinlar, oqarish), soch kulrang
AGE_V = []
def age_material(o, kind):
    m0 = o.data.materials[0]; m = m0.copy(); m.name = m0.name + "_" + kind; o.data.materials[0] = m
    N = m.node_tree.nodes; L = m.node_tree.links; b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    age = N.new("ShaderNodeValue"); age.name = "age"; age.outputs[0].default_value = 0.0
    src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(age.outputs[0], mx.inputs["Factor"])
    if src: L.new(src, mx.inputs[6])
    else: mx.inputs[6].default_value = b.inputs["Base Color"].default_value
    if kind == "hair":
        mx.inputs[7].default_value = (0.62, 0.6, 0.58, 1)
    else:
        hsv = N.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 0.75; hsv.inputs["Value"].default_value = 1.02
        if src: L.new(src, hsv.inputs["Color"])
        L.new(hsv.outputs[0], mx.inputs[7])
        tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 260.0
        wv.inputs["Distortion"].default_value = 9.0; wv.inputs["Detail"].default_value = 3.0; wv.bands_direction = "Z"
        L.new(tc.outputs["Object"], wv.inputs["Vector"])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900.0; L.new(tc.outputs["Object"], nz.inputs["Vector"])
        h = P.math_n(N, L, "ADD", wv.outputs["Fac"], P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.5))
        bp = N.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = 0.002
        L.new(P.math_n(N, L, "MULTIPLY", age.outputs[0], 0.55), bp.inputs["Strength"]); L.new(h, bp.inputs["Height"])
        if b.inputs["Normal"].links: L.new(b.inputs["Normal"].links[0].from_socket, bp.inputs["Normal"])
        L.new(bp.outputs[0], b.inputs["Normal"])
        b.inputs["Roughness"].default_value = 0.55
    L.new(mx.outputs[2], b.inputs["Base Color"])
    AGE_V.append(m)
    return m
age_material(body, "body"); age_material(hair, "hair")
MEG = RM + Vector((0.05, 0.6, 0))
mroot.location = MEG; mroot.rotation_euler = (0, 0, 0)          # -Y (kameraga) qaraydi
A_ = lambda f: mc.load_action(f, True)
mc.add_strip(meg, A_("Idle_9.fbx"), 1, blend=0, repeat=5.0, speed=0.9)
# yuz: pastki qism ichkariga botadi (shape key, rest pozada bosh suyagi koordinatasida)
bpy.context.view_layer.update()
hb = meg.data.bones["mixamorig:Head"]
_hm = meg.matrix_world @ hb.matrix_local                      # rest: X chap, Y tepa, Z old (masshtabsiz)
HM = Matrix.LocRotScale(_hm.translation, _hm.to_quaternion(), None)
HMi = HM.inverted()
bw = body.matrix_world
hp = [(i, HMi @ (bw @ v.co)) for i, v in enumerate(body.data.vertices)]
front = [(i, p) for i, p in hp if -0.05 < p.y < 0.25 and p.z > 0.0 and abs(p.x) < 0.09]
nose = max(front, key=lambda ip: ip[1].z)[1]
chin_c = [p for i, p in front if p.y < nose.y - 0.03 and abs(p.x) < 0.012]
chin = min(chin_c, key=lambda p: p.y) if chin_c else nose - Vector((0, 0.09, 0.02))
print("FACE nose", tuple(round(v, 3) for v in nose), "chin", tuple(round(v, 3) for v in chin))
FACE = dict(nose=nose, chin=chin)
body.shape_key_add(name="Basis", from_mix=False)
sk = body.shape_key_add(name="sink", from_mix=False); sk.value = 0.0
mouth_y = (nose.y + chin.y) / 2 - 0.005
hm3 = HM.to_3x3(); bw3i = bw.to_3x3().inverted()
for i, p in hp:
    if p.y < chin.y - 0.05 or p.y > nose.y + 0.01 or p.z < nose.z - 0.13: continue
    gy = math.exp(-((p.y - mouth_y) / 0.032) ** 2)
    gz = max(0.0, min(1.0, (p.z - (nose.z - 0.11)) / 0.06))
    gx = math.exp(-(p.x / 0.055) ** 2)
    # lablar va iyak ichkariga, iyak biroz yuqoriga; yonoqlar botadi
    d = Vector((0, 0.004, -0.017)) * gy * gz * gx
    cheek = math.exp(-((abs(p.x) - 0.045) / 0.02) ** 2) * math.exp(-((p.y - (nose.y - 0.015)) / 0.03) ** 2) * gz
    d += Vector((-math.copysign(0.006, p.x), 0, -0.004)) * cheek
    lo = bw3i @ (hm3 @ d)
    sk.data[i].co = body.data.vertices[i].co + lo
SK0, SK1 = S["sink"]; OL0, OL1 = S["old"]
for f, v in ((1, 0.0), (SK0 + 6, 0.0), (SK1 - 6, 1.0), (OL0, 1.25), (END, 1.25)):
    sk.value = v; sk.keyframe_insert("value", frame=f)
for m in AGE_V:
    mv(m, "age", 1, 0.0); mv(m, "age", OL0 - 1, 0.0); mv(m, "age", OL0, 1.0)
# bosh suyagiga bog'langan bo'sh ob'ekt (rentgen jag', og'riq nuri)
headE = empty("meg_head")
c = headE.constraints.new("CHILD_OF"); c.target = meg; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
# og'riq nuri (o'ng yonoq: bosh koordinatasida -X)
pain_m = T.soft_glow_material("pain", (1.0, 0.08, 0.03), 0.0)
pain = sphere("pain", 0.035, (0, 0, 0), pain_m, scale=(1, 1.2, 1), sub=3, parent=headE)
pain.location = (-0.045, chin.y + 0.035, nose.z - 0.06)
pain_l = point("pain_light", (0, 0, 0), 0.02, (1.0, 0.1, 0.03), [(1, 0)], parent=headE)
pain_l.location = (-0.07, chin.y + 0.035, nose.z - 0.03)
HK0, HK1 = S["hook"]
for f in range(HK0, HK1 + 1, 6):
    mv(pain_m, "glow", f, 0.4); mv(pain_m, "glow", f + 2, 5.0)
    pain_l.data.energy = 0.3; pain_l.data.keyframe_insert("energy", frame=f)
    pain_l.data.energy = 3.0; pain_l.data.keyframe_insert("energy", frame=f + 2)
pain_l.data.energy = 0; pain_l.data.keyframe_insert("energy", frame=HK1 + 1)
vis(pain, rng("hook"), recursive=False)
# qo'l yonoqda (hook): IK
megF = empty("megF", tuple(MEG))
fa = meg.pose.bones["mixamorig:RightForeArm"]; hbp = meg.pose.bones["mixamorig:RightHand"]
sc.frame_set(25); bpy.context.view_layer.update()
HW = meg.matrix_world @ meg.pose.bones["mixamorig:Head"].matrix
HW = Matrix.LocRotScale(HW.translation, HW.to_quaternion(), None)
cheekW = HW @ Vector((-0.085, chin.y + 0.03, nose.z - 0.07))
ikT = empty("ikT", tuple(cheekW + Vector((0, 0.0, -0.02)))); poleT = empty("poleT", tuple(MEG + Vector((-0.6, 0.4, 0.6))))
ik = fa.constraints.new("IK"); ik.target = ikT; ik.chain_count = 2; ik.use_tail = True; ik.pole_target = poleT; ik.pole_angle = R(-90)
upT = empty("upT", tuple(cheekW + Vector((0.02, 0.05, 0.4))))
faceT = empty("faceT", tuple(HW.translation + Vector((0.0, -0.02, 0.05))))
dt_ = hbp.constraints.new("DAMPED_TRACK"); dt_.target = upT; dt_.track_axis = "TRACK_Y"
lt_ = hbp.constraints.new("LOCKED_TRACK"); lt_.target = faceT; lt_.lock_axis = "LOCK_Y"; lt_.track_axis = "TRACK_Z"
for con in (ik, dt_, lt_):
    for f, v in ((1, 1.0), (HK1, 1.0), (HK1 + 1, 0.0)):
        con.influence = v; con.keyframe_insert("influence", frame=f)
for fcu in fcurves(meg):
    if "constraints" in fcu.data_path:
        for k in fcu.keyframe_points: k.interpolation = "CONSTANT"

# rentgen nusxasi (shaffof Megan + jag' + miya)
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.3, base=0.012)
ghosts = []
for o in mmeshes:
    if any(k in o.name for k in ("Pants", "Sneakers", "Eyelashes")): continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    if g.data.shape_keys: pass
    ghosts.append(g)
X_SH = rng("xjaw", "think")
for g in ghosts: vis(g, X_SH, recursive=False)
for o in mmeshes: vis(o, ROOM_SH, recursive=False)
jaw_m = P.xray_material("xray_bone", col=(0.85, 0.95, 1.0), strength=3.0, base=0.35)
tooth_xm = P.xray_material("xray_tooth", col=(1.0, 1.0, 0.95), strength=3.5, base=0.6)
gap_m = T.soft_glow_material("gap_glow", (1.0, 0.05, 0.02), 0.0)
jawE = empty("jawE", (0, 0, 0), headE)
jaw, jarch, juarch, gap = T.build_xray_jaw("xjaw", jawE, jaw_m, tooth_xm, gap_m)
# jag' joylashuvi: burun va iyakka nisbatan (bosh koordinatasi)
jawE.location = (0, chin.y + 0.06 - (-0.06 + 0.0), nose.z - 0.085 - 0.075 + 0.015)
vis(jawE, X_SH)
XJ0, XJ1 = S["xjaw"]; TH0, TH1 = S["think"]
mv(gap_m, "glow", 1, 0.0); mv(gap_m, "glow", XJ0 + 10, 0.0)
for f in range(XJ0 + 14, XJ1, 12):
    mv(gap_m, "glow", f, 6.0); mv(gap_m, "glow", f + 6, 1.5)
mv(gap_m, "glow", TH0, 1.0)
brain, brain_m = P.build_brain("brain", headE, size=0.06)
brain.location = (0, 0.105, 0.025); brain.rotation_euler = (R(-90), 0, 0)
vis(brain, rng("think"))
P.mat_value(brain_m, "glow", 1, 0.0); P.mat_value(brain_m, "glow", TH0, 0.5)
for f in range(TH0 + 4, TH0 + 40, 7):
    P.mat_value(brain_m, "glow", f, 6.0); P.mat_value(brain_m, "glow", f + 3, 1.5)
# miyadan jag'dagi bo'sh joyga signal
sig_m = P.pulse_material("brain_sig", (1.0, 0.25, 0.1), base_emit=0.3, pulse_col=(1.0, 0.3, 0.1), width=0.12)
bpy.context.view_layer.update()
gp_local = (headE.matrix_world.inverted() @ gap.matrix_world).translation
sigc = P.tube("brain_sig", [(0, 0.1, 0.0), (-0.035, 0.05, 0.03), (-0.045, -0.0, 0.05), tuple(gp_local)], 0.0025, sig_m, parent=headE)
vis(sigc, rng("think"))
mv(sig_m, "pos", TH0 + 36, -0.1); mv(sig_m, "pos", TH1 - 14, 1.1)
mv(gap_m, "glow", TH1 - 16, 1.0); mv(gap_m, "glow", TH1 - 12, 8.0); mv(gap_m, "glow", TH1, 4.0)

# ======================================================================
# 5) KAMERALAR
# ======================================================================
def headpos(f, off=(0, 0, 0)):
    sc.frame_set(f); bpy.context.view_layer.update()
    m_ = meg.matrix_world @ meg.pose.bones["mixamorig:Head"].matrix
    return Matrix.LocRotScale(m_.translation, m_.to_quaternion(), None) @ Vector(off)
FOC = (0, chin.y + 0.05, nose.z - 0.02)           # yuz markazi (bosh koordinatasi)
faceT_c = empty("faceT_c", (0, 0, 0), headE); faceT_c.location = FOC
# 1 ILGAK: yuzga tez yaqinlashish
c = shot_cam("hook", (0, 0, 0), faceT_c, 50, 2.0)
hf = headpos(HK0, FOC)
key(c, HK0, loc=tuple(hf + Vector((0.3, -1.3, -0.12)))); key(c, HK0 + 8, loc=tuple(hf + Vector((0.14, -0.75, -0.07))))
key(c, HK1, loc=tuple(hf + Vector((0.08, -0.6, -0.05))))
lens_keys(c, [(HK0, 30), (HK0 + 8, 42), (HK1, 48)])
# 2 OG'IZ ICHI
tgt = empty("t_pull", tuple(pR5 + Vector((0, 0, 0.6))))
c = shot_cam("pull", (0, 0, 0), tgt, 20, 5.6, focus=tgt)
key(c, PU0, loc=tuple(pR5 - tR5 * 3.4 + lingual * 2.6 + Vector((0, 0, 3.6))))
key(c, YANK, loc=tuple(pR5 - tR5 * 2.6 + lingual * 2.2 + Vector((0, 0, 2.8))))
key(c, PU1, loc=tuple(pR5 - tR5 * 2.8 + lingual * 2.6 + Vector((0, 0, 2.4))))
key(tgt, PU0, loc=tuple(pR5 + Vector((0, 0, 0.6)))); key(tgt, YANK, loc=tuple(pR5 + Vector((0, 0, 0.8))))
key(tgt, PU1, loc=tuple(pR5 + Vector((0, 0, 2.6))))
shake(c, YANK, YANK + 10, 0.12, 3)
# 3 LAGAN: past burchak, crash zoom
tgt = empty("t_tray", tuple(land + Vector((0.5, 0.2, 0.2))))
c = shot_cam("tray", tuple(land + Vector((-5.5, -9.0, 1.2))), tgt, 28, 2.8, focus=tgt)
key(c, TR0, loc=tuple(land + Vector((-5.5, -9.0, 2.2)))); key(c, TR1, loc=tuple(land + Vector((-4.5, -7.6, 1.3))))
lens_keys(c, [(TR0, 28), (TR0 + 9, 30), (TR0 + 13, 62), (TR1, 70)])
shake(c, TR0 + 9, TR0 + 16, 0.25, 5)
# 4 RENTGEN JAG': bosh atrofida aylanish
xjT = empty("t_xjaw", (0, 0, 0), headE); xjT.location = (0, chin.y + 0.05, nose.z - 0.06)
c = shot_cam("xjaw", (0, 0, 0), xjT, 45, 4.0)
for f in range(XJ0, XJ1 + 1, 6):
    t = (f - XJ0) / (XJ1 - XJ0); a = R(lerp(-35, 50, ease(t)))
    hp_ = headpos(f, (0, chin.y + 0.05, nose.z - 0.06))
    rdist = lerp(0.55, 0.34, ease(t))
    c.location = hp_ + Vector((math.sin(a) * rdist, -math.cos(a) * rdist, lerp(0.12, 0.04, t))); c.keyframe_insert("location", frame=f)
# 5 ILDIZ: kamera ildiz bo'ylab pastga sirpanadi
RO0, RO1 = S["root"]
tgt = empty("t_root", (0, 0, 0.3))
c = shot_cam("root", (1.2, -4.0, 0.9), tgt, 40, 4.0, focus=tgt)
key(c, RO0, loc=(1.4, -4.2, 1.2)); key(c, RO1, loc=(0.6, -3.4, -1.5))
key(tgt, RO0, loc=(0, 0, 0.4)); key(tgt, RO1, loc=(0, 0, -1.0))
# 6 TISHLASH: past burchakdan yaqinlashish
tgt = empty("t_bite", (0, 0, 0.6))
c = shot_cam("bite", (-2.2, -6.0, -0.4), tgt, 32, 5.6, focus=tgt)
key(c, BI0, loc=(-2.6, -7.0, -0.6)); key(c, CONTACT1, loc=(-1.4, -4.6, 0.0)); key(c, BI1, loc=(-1.2, -4.3, 0.1))
key(tgt, BI0, loc=(0, 0, 1.0)); key(tgt, BI1, loc=(0, 0, 0.5))
shake(c, CONTACT1, CONTACT1 + 9, 0.12, 7)
# 7 SIGNAL: keng plan, sekin orbit
tgt = empty("t_sig", (0, 0, -0.7))
c = shot_cam("signal", (0, 0, 0), tgt, 30, 8.0, focus=tgt)
for f in range(SI0, SI1 + 1, 6):
    t = (f - SI0) / (SI1 - SI0); a = R(lerp(25, -20, ease(t)))
    c.location = Vector((math.sin(a) * 7.0, -math.cos(a) * 7.0, lerp(0.6, -0.2, t))); c.keyframe_insert("location", frame=f)
for cc in CHEW: shake(c, cc, cc + 6, 0.06, cc)
# 8 BO'SH: tish chiqib ketadi, bo'shliqqa tishlash
tgt = empty("t_empty", (0, 0, 0.0))
c = shot_cam("empty", (1.5, -5.2, 0.4), tgt, 24, 5.6, focus=tgt)
key(c, EM0, loc=(2.4, -7.5, 1.0)); key(c, EMPTY_BITE - 4, loc=(1.6, -6.4, 0.4)); key(c, EM1, loc=(1.0, -5.4, 0.0))
key(tgt, EM0, loc=(0, 0, 0.3)); key(tgt, EM1, loc=(0, 0, -0.6))
shake(c, EMPTY_BITE, EMPTY_BITE + 8, 0.1, 9)
lens_keys(c, [(EM0, 24), (EMPTY_BITE, 24), (EMPTY_BITE + 3, 34)])
# 9 MIYA "o'ylaydi": yonidan, sekin aylanish
thT = empty("t_think", (0, 0, 0), headE); thT.location = (0, 0.05, 0.03)
c = shot_cam("think", (0, 0, 0), thT, 40, 4.0)
for f in range(TH0, TH1 + 1, 6):
    t = (f - TH0) / (TH1 - TH0); a = R(lerp(70, 35, ease(t)))
    hp_ = headpos(f, (0, 0.05, 0.03)); rdist = lerp(0.62, 0.48, t)
    c.location = hp_ + Vector((math.sin(a) * rdist, -math.cos(a) * rdist, lerp(0.1, 0.02, t))); c.keyframe_insert("location", frame=f)
# 10 KALSIY: oqimga ergashish
tgt = empty("t_cal", (0, 0, -0.9))
c = shot_cam("calcium", (-1.5, -4.5, -0.3), tgt, 35, 5.6, focus=tgt)
key(c, CA0, loc=(-1.8, -6.0, 0.0)); key(c, CA1, loc=(1.2, -5.4, -1.4))
key(tgt, CA0, loc=(-0.2, 0, -0.7)); key(tgt, CA1, loc=(1.6, 0, -1.9))
# 11 CHO'KISH: time-lapse, sekin orbit
tgt = empty("t_shrink", (0, 0.2, -0.9))
c = shot_cam("shrink", (0, 0, 0), tgt, 34, 8.0, focus=tgt)
for f in range(SH0, SH1 + 1, 6):
    t = (f - SH0) / (SH1 - SH0); a = R(lerp(-30, 28, ease(t)))
    c.location = Vector((math.sin(a) * 6.8, 0.3 - math.cos(a) * 6.8, lerp(1.8, 0.6, t))); c.keyframe_insert("location", frame=f)
# 12 QIYSHAYISH: lunj tomondan (lunj yashiringan), past burchak
buccal = -lingual
tgt = empty("t_tilt", tuple(pR5 + Vector((0, 0, 1.0))))
c = shot_cam("tilt", tuple(pR5 + buccal * 6.0 + Vector((0, 0, 0.3))), tgt, 30, 5.6, focus=tgt)
key(c, TI0, loc=tuple(pR5 + buccal * 6.5 - tR5 * 1.0 + Vector((0, 0, 0.0))))
key(c, TI1, loc=tuple(pR5 + buccal * 5.0 + tR5 * 0.8 + Vector((0, 0, 0.6))))
# 13 YUZ CHO'KISHI: yon profil, sekin push-in
c = shot_cam("sink", (0, 0, 0), faceT_c, 55, 2.2)
for f in range(SK0, SK1 + 1, 4):
    t = (f - SK0) / (SK1 - SK0); hf = headpos(f, FOC); a = R(lerp(72, 58, t)); rdist = lerp(0.85, 0.6, ease(t))
    c.location = hf + Vector((math.sin(a) * rdist, -math.cos(a) * rdist, 0.02)); c.keyframe_insert("location", frame=f)
# 14 QARIGAN: old tomondan, yaqinlashish
c = shot_cam("old", (0, 0, 0), faceT_c, 50, 2.0)
for f in range(OL0, OL1 + 1, 4):
    t = (f - OL0) / (OL1 - OL0); hf = headpos(f, FOC); rdist = lerp(0.62, 0.42, ease(t))
    rdist = lerp(0.8, 0.55, ease(t))
    c.location = hf + Vector((0.1 - 0.07 * t, -rdist, -0.02)); c.keyframe_insert("location", frame=f)
shake(c, OL0, OL0 + 8, 0.012, 11)
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
def env_bg(file, rot):
    mp = N.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, R(rot)); L.new(tcw.outputs["Generated"], mp.inputs[0])
    e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + file); L.new(mp.outputs[0], e.inputs[0])
    bgn = N.new("ShaderNodeBackground"); L.new(e.outputs[0], bgn.inputs[0]); return bgn
bg_st = env_bg("studio_small_09.hdr", 40)
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.006, 0.014, 0.03, 1)
bg_rd = N.new("ShaderNodeBackground"); bg_rd.inputs[0].default_value = (0.06, 0.008, 0.006, 1)
a1 = N.new("ShaderNodeAddShader"); a2 = N.new("ShaderNodeAddShader")
L.new(bg_st.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], a2.inputs[0]); L.new(bg_rd.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], out.inputs["Surface"])
WL = {"hook": (0.35, 0, 0), "pull": (0.0, 0, 1.0), "tray": (0.8, 0, 0), "xjaw": (0, 1.0, 0), "root": (0, 1.0, 0), "bite": (0, 1.0, 0),
      "signal": (0, 1.0, 0), "empty": (0, 1.0, 0), "think": (0, 1.0, 0), "calcium": (0, 1.0, 0), "shrink": (0, 1.0, 0),
      "tilt": (0.0, 0.0, 1.0), "sink": (0.35, 0, 0), "old": (0.3, 0, 0)}
for f, n in SHOTS:
    for bgn, v in zip((bg_st, bg_dk, bg_rd), WL[n]):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# kesim (sm) — studiya: kalit, kontur, pastdan
secT = empty("secT", (0, 0.3, -0.6))
area("S_key", (-5.0, -6.0, 5.0), 4.0, (1.0, 0.95, 0.88), lights_for(SEC_ALL, 900.0), target=secT)
area("S_rim", (4.5, 4.0, 3.0), 3.0, (0.4, 0.65, 1.0), lights_for(SEC_ALL, 900.0), target=secT)
area("S_fill", (6.0, -4.0, -2.0), 3.0, (0.75, 0.85, 1.0), lights_for(SEC_ALL, 250.0), target=secT)
area("S_red", (-4.0, -4.0, 1.0), 3.0, (1.0, 0.06, 0.03), [(1, 0), (EMPTY_BITE, 0), (EMPTY_BITE + 1, 1600), (EMPTY_BITE + 8, 500),
                                                          (EM1 + 1, 0), (CA0, 250), (CA1 + 1, 0), (SH0, 350), (SH1 + 1, 0)], target=secT)
area("S_gold", (0.0, -5.0, -2.0), 3.0, (1.0, 0.7, 0.3), [(1, 0)] + [k for cc in CHEW for k in ((cc, 700), (cc + 8, 100))] + [(SI1 + 1, 0)], target=secT)
# og'iz ichi (dental chiroq)
mT = empty("mouthT", tuple(pR5 + Vector((0, 0, 0.5))))
area("M_lamp", tuple(pR5 - tR5 * 5.0 + lingual * 2.0 + Vector((0, 0, 5.0))), 3.0, (1.0, 0.97, 0.92), lights_for(rng("pull"), 700.0), target=mT)
area("M_rim", tuple(pR5 + tR5 * 4.0 - lingual * 1.0 + Vector((0, 0, 3.0))), 2.0, (1.0, 0.75, 0.6), lights_for(rng("pull"), 250.0), target=mT)
area("T_key", tuple(pR5 + buccal * 6.0 + Vector((-2.0, 0, 5.0))), 4.0, (1.0, 0.95, 0.9), lights_for(rng("tilt"), 900.0), target=mT)
area("T_rim", tuple(pR5 - buccal * 4.0 + Vector((0, 0, 4.0))), 3.0, (0.45, 0.7, 1.0), lights_for(rng("tilt"), 600.0), target=mT)
# lagan
trT = empty("trT", tuple(land))
area("TR_key", tuple(TRY + Vector((-6, -6, 12))), 8.0, (1.0, 0.96, 0.9), lights_for(rng("tray"), 4000.0), target=trT)
area("TR_rim", tuple(TRY + Vector((8, 8, 6))), 5.0, (0.6, 0.8, 1.0), lights_for(rng("tray"), 1500.0), target=trT)
# xona
rT = empty("roomT", tuple(MEG + Vector((0, 0, 1.5))))
area("R_win", tuple(RM + Vector((2.3, 1.0, 1.7))), 1.4, (1.0, 0.95, 0.88), lights_for(ROOM_SH, 300.0), target=rT)
area("R_key", tuple(MEG + Vector((-0.9, -1.1, 2.0))), 0.9, (1.0, 0.92, 0.85), lights_for(ROOM_SH, 90.0), target=rT)
area("R_rim", tuple(MEG + Vector((0.8, 0.9, 1.9))), 0.6, (1.0, 0.75, 0.5), lights_for(ROOM_SH, 70.0), target=rT)
area("R_bg", tuple(RM + Vector((0.5, -0.5, 2.6))), 2.0, (1.0, 0.9, 0.8), lights_for(rng("sink"), 250.0), target=empty("rbgT", tuple(RM + Vector((-2.6, 0.8, 1.2)))))
area("R_ceil", tuple(RM + Vector((0, 0.5, 2.9))), 1.5, (1.0, 0.9, 0.8), lights_for(ROOM_SH, 150.0), target=rT)
# rentgen: qorong'ida ko'k kontur
area("X_rim", tuple(MEG + Vector((-0.8, 0.6, 2.0))), 0.8, (0.3, 0.6, 1.0), lights_for(X_SH, 30.0), target=rT)

# ======================================================================
# 7) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.3
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = os.environ.get("PERSIST", "1") == "1"
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
