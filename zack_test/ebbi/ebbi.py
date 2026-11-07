# Ebbi va sigir chuvalchangi (Thelazia gulosa) — Zack D. Films uslubida 55 s video.
# Asos: zack_test/gage/gage.py + mixchar.py; makro modellar: eye.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=12 /tmp/claude-0/bvenv/bin/python -I zack_test/ebbi/ebbi.py --render
# Sinov: FRAMES=20,100,380,450,900 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Quaternion, noise
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
import eye as E
sc = bpy.context.scene
sc.render.fps = 24
END = 1320
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan) ----------------
SHOTS = [(1, "eye_hook"), (41, "boat_rub"), (89, "boat_face"), (123, "aerial"), (155, "cast"),
         (184, "eye_red"), (231, "rub_close"), (278, "bath_wide"), (341, "eye_pull"), (428, "finger_worm"),
         (469, "scared"), (507, "mirror"), (546, "eye_lid"), (589, "eye_lid2"), (623, "clinic_doc"),
         (659, "dish1"), (717, "cows"), (747, "cow_eye"), (775, "cow_fly"), (841, "fly_air"),
         (871, "eye_land"), (916, "xray"), (981, "clinic_tweezer"), (1033, "dish14"), (1096, "dusk"),
         (1190, "eye_healthy"), (1244, "fly_approach"), (1287, "eye_shut")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

# ---------------- yordamchilar ----------------
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

def import_glb(path, parent):
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

def look_quat(d, axis=(0, 1, 0)):
    return Vector(axis).rotation_difference(Vector(d).normalized())

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 6000
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
    base = cam.location.copy()
    for f in range(f0, f1):
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None: l.constraints.new("TRACK_TO").target = target
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

# ======================================================================
# 1) MAKRO: EBBI KO'ZI (dunyo markazida), barmoq, chuvalchanglar, pashsha
# ======================================================================
EYE_SHOTS = ["eye_hook", "eye_red", "eye_pull", "eye_lid", "eye_lid2", "eye_land", "xray", "eye_healthy", "fly_approach", "eye_shut"]
eA = E.build_eye("eyeA", (0, 0, 0))
vis(eA["root"], rng(*EYE_SHOTS))
W = eA["shape"].W

def red_keys(eye, pairs):
    for f, v in pairs: E.key_value(eye["red"], f, v)
red_keys(eA, [(1, 0.15), (S["eye_red"][0], 0.1), (S["eye_red"][0] + 30, 1.0), (S["eye_pull"][0], 0.9), (S["eye_land"][0], 0.05),
              (S["xray"][0], 0.2), (S["xray"][1], 0.6), (S["eye_healthy"][0], 0.0)])
def keyset(eye, k, pairs):
    for f, v in pairs: E.set_key(eye, k, f, v)
blinkA = [(1, 0.0)]
for fb in (26, 205, 1214, 1290):                 # pirpirash: 0 -> 1 -> 0
    if fb == 1290: blinkA += [(fb - 1, 0.0), (fb + 2, 1.0)]
    else: blinkA += [(fb - 1, 0.0), (fb + 2, 1.0), (fb + 5, 0.0)]
keyset(eA, "blink", blinkA)
keyset(eA, "squint", [(1, 0), (S["eye_red"][0] + 20, 0), (S["eye_red"][0] + 34, 0.6), (S["eye_red"][1], 0.5), (S["eye_pull"][0], 0.0),
                      (S["eye_shut"][0], 0.0), (S["eye_shut"][0] + 5, 0.0), (S["eye_shut"][0] + 9, 0.0)])
keyset(eA, "pull", [(1, 0), (S["eye_pull"][0], 0.0), (360, 0.35), (S["eye_pull"][1], 0.2), (S["eye_lid"][0], 1.0), (S["eye_lid2"][1], 1.0),
                    (S["eye_land"][0], 0.0)])
keyset(eA, "wide", [(1, 0), (S["eye_land"][0], 0.0), (S["eye_land"][0] + 14, 0.0), (S["eye_land"][0] + 20, 0.5), (S["xray"][0], 0.0),
                    (S["fly_approach"][0], 0.0), (S["fly_approach"][0] + 25, 0.6), (S["eye_shut"][0], 0.0)])
# ko'z olmasi harakati (sakkada)
ball = eA["ball"]
for f, rx, rz in ((1, 0, 0), (14, 0, 0), (16, -4, 8), (S["eye_red"][0], 0, -5), (S["eye_pull"][0], 6, 10), (S["eye_lid"][0], 10, 0),
                  (S["eye_land"][0], 3, -6), (S["eye_land"][0] + 12, 5, -14), (S["xray"][0], 0, 0), (S["eye_healthy"][0], 0, 0),
                  (S["fly_approach"][0], 0, 0), (S["fly_approach"][0] + 18, 0, 0), (S["fly_approach"][0] + 21, -3, -12), (S["eye_shut"][0], -3, -12)):
    key(ball, f, rot=(rx, 0, rz))
interp(ball, "CONSTANT")

# --- barmoq ---
finger = E.build_finger("fingerA")
finger.rotation_mode = "QUATERNION"
fdir = Vector((0.55, -0.45, -0.7)).normalized()
q0 = look_quat(fdir) @ Quaternion((0, 1, 0), R(160))
finger.rotation_quaternion = q0
EXIT = E.on_eye(eA, W * 0.55, -0.0037, 0.0)          # pastki qovoq chetidagi chiqish nuqtasi (tashqi burchakka yaqin)
def fin_key(f, tip):
    finger.location = tip; finger.keyframe_insert("location", frame=f)
P0 = S["eye_pull"][0]
fin_key(P0, EXIT + Vector((0.016, -0.02, -0.02)))
fin_key(P0 + 16, EXIT + Vector((0.0012, -0.0011, -0.0018)))
fin_key(P0 + 24, EXIT + Vector((0.0011, -0.0012, -0.0016)))
fin_key(S["eye_pull"][1], EXIT + Vector((0.009, -0.022, -0.013)))
# pastki qovoqni tortib turgan barmoq (eye_lid, eye_lid2)
fin_key(S["eye_lid"][0], Vector((0.001, -0.0085, -0.0165)))
fin_key(S["eye_lid2"][1], Vector((0.0013, -0.0085, -0.0168)))
interp(finger, "LINEAR")
vis(finger, rng("eye_pull", "eye_lid", "eye_lid2"))

# --- chuvalchanglar ---
NW = 22
def path_worm(name, frames, fn):
    w = E.make_worm(name, eA["root"], NW)
    for f in frames: E.set_worm(w, f, fn(f))
    return w
# ilgak: pastki qovoq ostidan dumi chiqib turadi va qimirlaydi
def hook_pts(f):
    head = (W * 0.18 + 0.0004 * math.sin(f * 0.15), -0.0048 + 0.0006 * math.sin(f * 0.1))
    return [E.on_eye(eA, x, z) for x, z in E.wiggle_path(NW, 0.012, f, head, R(-160), amp=0.0008, w=0.35)]
w_hook = path_worm("worm_hook", range(*[S["eye_hook"][0], S["eye_hook"][1] + 1]), hook_pts)
vis(w_hook, rng("eye_hook"))
# tortib chiqarish
LW = 0.013
def pull_pts(f):
    fp = finger.location if False else None
    sc.frame_set(f); tip = finger.matrix_world.translation.copy() + Vector((-0.0003, -0.0008, 0.0006))
    e = min(1.0, max(0.0, (f - (P0 + 24)) / 46.0)) * LW           # tashqariga chiqqan uzunlik
    pts = []
    exit_p = EXIT + Vector((0, -0.0003, 0))
    for i in range(NW):
        l = i / (NW - 1) * LW
        wig = 0.0007 * math.sin(i * 0.9 - f * 0.6)
        if f > P0 + 72:                                             # butunlay chiqdi: barmoqdan osilib turadi
            s = l / LW; p = tip + Vector((0.0025 * s + wig * 0.6, -0.0012 * s, -0.009 * s)) + Vector((0.0015 * math.sin(s * 5 - f * 0.4), 0, 0))
        elif l < e or e > LW * 0.99:
            s = l / max(e, 1e-5)
            p = tip.lerp(exit_p, s) + Vector((wig, -0.0004 * math.sin(math.pi * s), -0.0012 * math.sin(math.pi * s)))
        else:
            d = l - e
            p = E.on_eye(eA, EXIT.x - d * 0.55, EXIT.z - d * 0.15 - 0.0002, 0.0003) + Vector((0, 0, wig * 0.3))
        pts.append(p)
    return pts
w_pull = path_worm("worm_pull", range(P0 + 10, S["eye_pull"][1] + 1), pull_pts)
vis(w_pull, [(P0 + 10, S["eye_pull"][1])])
# qovoq ostidagi chuvalchang (eye_lid) va ikkinchisi (eye_lid2)
def lid_pts(f):
    head = (-0.002 + 0.0005 * math.sin(f * 0.11), -0.0072)
    return [E.on_eye(eA, x, z) for x, z in E.wiggle_path(NW, 0.011, f, head, R(-10), amp=0.0009, w=0.45)]
w_lid = path_worm("worm_lid", range(S["eye_lid"][0], S["eye_lid2"][1] + 1), lid_pts)
vis(w_lid, rng("eye_lid", "eye_lid2"))
def lid2_pts(f):
    t = (f - S["eye_lid2"][0]) / 30
    head = (0.0045 - 0.004 * min(1, t), -0.0085 + 0.0035 * min(1, t))
    return [E.on_eye(eA, x, z) for x, z in E.wiggle_path(NW, 0.012, f, head, R(-75), amp=0.0009, w=0.5, phase=1.3)]
w_lid2 = path_worm("worm_lid2", range(S["eye_lid2"][0], S["eye_lid2"][1] + 1), lid2_pts)
vis(w_lid2, rng("eye_lid2"))
# rentgen: yuqori qovoq ostida lichinkalar o'sadi
XR0, XR1 = S["xray"]
larvae_x = []
for k in range(5):
    cx = -0.006 + k * 0.003; cz = 0.0068 + 0.0007 * (k % 2)
    def lx(f, cx=cx, cz=cz, k=k):
        g = 0.25 + 0.75 * min(1, max(0, (f - XR0) / (XR1 - XR0 - 10)))
        return [E.on_eye(eA, x, z, 0.0003) for x, z in E.wiggle_path(NW, 0.009 * g, f, (cx + 0.004 * g, cz), R(180 + (k - 2) * 8), amp=0.0005 * g, w=0.4, phase=k)]
    w = path_worm(f"larva_x{k}", range(XR0, XR1 + 1, 2), lx)
    lm_ = bpy.data.materials.new(f"larva_glow{k}"); lm_.use_nodes = True; lb_ = lm_.node_tree.nodes["Principled BSDF"]
    lb_.inputs["Base Color"].default_value = (1, 0.95, 0.9, 1); lb_.inputs["Emission Color"].default_value = (1, 0.85, 0.75, 1)
    lb_.inputs["Emission Strength"].default_value = 3.0; w.data.materials[0] = lm_
    larvae_x.append(w)
    vis(w, rng("xray"))
    sc.frame_set(XR0); w.scale = (1, 1, 1)
for f, v in ((1, 0.0), (XR0, 1.0), (XR1 + 1, 0.0)):
    E.key_value(eA["xray"], f, v)
interp(bpy.data.materials["eyeA_lids_skin"].node_tree, "CONSTANT")
# pashsha qo'ndirgan mayda lichinkalar (eye_land)
LAND = S["eye_land"][0] + 17
larv = []
for k in range(6):
    w = E.make_worm(f"larva_s{k}", eA["root"], 8, 0.00012)
    cx, cz = 0.0045 + random.uniform(-0.0012, 0.0012), -0.0026 + random.uniform(-0.0008, 0.0008)
    for f in range(LAND + 4, S["eye_land"][1] + 1, 2):
        E.set_worm(w, f, [E.on_eye(eA, x, z, 0.00015) for x, z in E.wiggle_path(8, 0.0018, f, (cx, cz), R(random.uniform(0, 360)), amp=0.0002, w=0.6, phase=k)])
    vis(w, [(LAND + 4 + k, S["eye_land"][1])])

# --- pashsha ---
fly, wings = E.build_fly("fly")
fly.rotation_mode = "QUATERNION"
FLY_KEYS = []
def fly_at(f, loc, fwd, up=(0, 0, 1), flap=True):
    fwd = Vector(fwd).normalized(); up = Vector(up)
    x = fwd.cross(up).normalized(); z = x.cross(fwd).normalized()
    m = Matrix((x, fwd, z)).transposed()
    fly.location = loc; fly.rotation_quaternion = m.to_quaternion()
    fly.keyframe_insert("location", frame=f); fly.keyframe_insert("rotation_quaternion", frame=f)
    for piv, sx in wings:
        if flap:
            up_ = (f % 2 == 0)
            piv.rotation_euler = (0, R(sx * (-60 if up_ else 45)), R(sx * (-15 if up_ else -30)))
        else:
            piv.rotation_euler = (0, R(sx * -8), R(sx * -68))
        piv.keyframe_insert("rotation_euler", frame=f)
def fly_hold_end(f):
    """kesish oldidan: keyingi kadrga o'tishda motion blur chizig'i qolmasin"""
    for fc in fcurves(fly):
        fc.keyframe_points.insert(f + 0.6, fc.evaluate(f))

# ======================================================================
# 2) BARMOQDAGI CHUVALCHANG (o'ta makro), x = 0.4
# ======================================================================
FW = Vector((0.4, 0, 0))
fw_root = empty("fw_root", FW)
fing2 = E.build_finger("fingerB", fw_root)
fing2.rotation_euler = (R(90 + 15), R(180), 0)         # yostiqcha tepaga, tanasi orqaga
fing2.location = (0, 0, 0)
wb = E.make_worm("worm_finger", fw_root, NW, 0.00034)
F0, F1 = S["finger_worm"]
for f in range(F0, F1 + 1):
    pts = []
    for i in range(NW):
        s = i / (NW - 1)
        x = -0.004 + 0.009 * s + 0.0003 * (f - F0) / 40
        y = 0.002 + 0.0045 * math.sin(s * 7 - f * 0.45) * (0.4 + 0.6 * s)
        zz = 0.0072 + 0.0005 * math.sin(math.pi * s) + (0.004 * max(0, s - 0.8) ** 1.5 if s > 0.8 else 0)
        if s < 0.25: zz += 0.003 * (0.25 - s) * (1 + math.sin(f * 0.5))        # boshi havoga ko'tarilib qimirlaydi
        pts.append(Vector((x, y - 0.006, zz)))
    E.set_worm(wb, f, pts)
for i, (x, z, c) in enumerate(((0.25, 0.1, (1, .75, .45)), (-0.2, 0.25, (1, .85, .6)), (0.05, -0.15, (.9, .6, .4)), (0.35, 0.3, (1, .9, .7)))):
    b = sphere(f"bokeh{i}", 0.02, (x, 1.2, z), mat(f"bk{i}", c, emit=25), parent=fw_root)
bd_m = bpy.data.materials.new("fw_backdrop"); bd_m.use_nodes = True
Nb = bd_m.node_tree.nodes; Lb = bd_m.node_tree.links
for n in list(Nb): Nb.remove(n)
ob = Nb.new("ShaderNodeOutputMaterial"); emb = Nb.new("ShaderNodeEmission"); nzb = Nb.new("ShaderNodeTexNoise"); nzb.inputs["Scale"].default_value = 6
crb = Nb.new("ShaderNodeValToRGB"); Lb.new(nzb.outputs["Fac"], crb.inputs[0])
crb.color_ramp.elements[0].color = (0.05, 0.03, 0.02, 1); crb.color_ramp.elements[1].color = (0.9, 0.6, 0.35, 1)
Lb.new(crb.outputs[0], emb.inputs["Color"]); emb.inputs["Strength"].default_value = 0.8; Lb.new(emb.outputs[0], ob.inputs[0])
bdp = plane("fw_backdrop", (1.5, 1.5), (-0.25, 0.3, -0.2), bd_m, parent=fw_root)
bdp.rotation_mode = "QUATERNION"; bdp.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector((0.035, -0.045, 0.03)).normalized())
vis(fw_root, rng("finger_worm"))

# ======================================================================
# 3) SIGIR KO'ZI (x = 1)
# ======================================================================
eC = E.build_eye("eyeC", (1.0, 0, 0), kind="cow", R=0.017)
vis(eC["root"], rng("cow_eye", "cow_fly"))
red_keys(eC, [(1, 0.35)])
keyset(eC, "blink", [(1, 0), (S["cow_fly"][1] - 6, 0), (S["cow_fly"][1] - 3, 0.9), (S["cow_fly"][1], 0.1)])
WC = eC["shape"].W
cw = []
for k, (hx, hz, hd) in enumerate(((-0.005, -0.0032, 10), (0.008, -0.0022, 165), (0.002, 0.0045, 195))):
    w = E.make_worm(f"cowworm{k}", eC["root"], NW, 0.0004)
    for f in range(S["cow_eye"][0], S["cow_fly"][1] + 1, 1):
        head = (hx + 0.0012 * math.sin(f * 0.05 + k), hz + 0.0005 * math.sin(f * 0.07))
        E.set_worm(w, f, [E.on_eye(eC, x, z, 0.0004) for x, z in E.wiggle_path(NW, 0.014, f, head, R(hd), amp=0.0012, w=0.35, phase=k)])
    cw.append(w)
    vis(w, rng("cow_eye", "cow_fly"))

# ======================================================================
# 4) PETRI IDISHI (x = 2)
# ======================================================================
DS = Vector((2.0, 0, 0))
d_root = empty("dish_root", DS)
M_glass = bpy.data.materials.new("glass"); M_glass.use_nodes = True; gb = M_glass.node_tree.nodes["Principled BSDF"]
gb.inputs["Transmission Weight"].default_value = 1.0; gb.inputs["Roughness"].default_value = 0.02; gb.inputs["IOR"].default_value = 1.45
bench = plane("bench", (0.6, 0.6), (0, 0, -0.001), mat("bench", (0.75, 0.78, 0.8), 0.35), parent=d_root)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.045, depth=0.012, location=(0, 0, 0.006))
dish = bpy.context.object; dish.name = "dish"; dish.parent = d_root
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
for p in dish.data.polygons:
    if p.normal.z > 0.9: p.select = True
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
so = dish.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.0012; dish.data.materials.append(M_glass)
M_liq = bpy.data.materials.new("saline"); M_liq.use_nodes = True; lb = M_liq.node_tree.nodes["Principled BSDF"]
lb.inputs["Transmission Weight"].default_value = 1.0; lb.inputs["Roughness"].default_value = 0.0; lb.inputs["IOR"].default_value = 1.33
lb.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1)
liq = None
dish_worms = []
rd = random.Random(14)
for k in range(14):
    w = E.make_worm(f"dishworm{k}", d_root, NW, 0.00036)
    cx, cz = (0, 0) if k == 0 else (rd.uniform(-0.03, 0.03), rd.uniform(-0.03, 0.03))
    hd = rd.uniform(0, 6.28); ph = rd.uniform(0, 6)
    frames = list(range(S["dish1"][0], S["dish1"][1] + 1)) if k == 0 else []
    frames += list(range(S["dish14"][0], S["dish14"][1] + 1))
    for f in frames:
        sz = 1.25 if f < S["dish14"][0] else 1.0
        P = E.wiggle_path(NW, 0.013 * sz, f, (cx + 0.004 * math.sin(f * 0.02 + ph), cz), hd + 0.4 * math.sin(f * 0.03 + ph), amp=0.0018, k=1.6, w=0.3, phase=ph)
        E.set_worm(w, f, [Vector((x, z, 0.0017 + 0.00025 * math.sin(i * 0.7 + f * 0.3))) for i, (x, z) in enumerate(P)])
    vis(w, rng("dish1", "dish14") if k == 0 else rng("dish14"))
    dish_worms.append(w)
# qisqich (tweezers) idish chetida
M_steel = mat("steel", (0.8, 0.8, 0.82), 0.18, metal=1.0)
for sx in (-1, 1):
    tw = box(f"tweezer{sx}", (0.0035, 0.11, 0.0012), (0.05 + sx * 0.0025, -0.03, 0.0015), M_steel, rot=(0, 0, 25 + sx * 2), parent=d_root)
vis(d_root, rng("dish1", "dish14"))

# ======================================================================
# 5) KEMA, DENGIZ, TOG'LAR (x = 100)
# ======================================================================
BT = Vector((100.0, 0, 0))
boat_world = empty("boat_world", BT)
M_water = bpy.data.materials.new("sea"); M_water.use_nodes = True; wb_ = M_water.node_tree.nodes["Principled BSDF"]
wb_.inputs["Base Color"].default_value = (0.012, 0.03, 0.035, 1); wb_.inputs["Roughness"].default_value = 0.06
wb_.inputs["IOR"].default_value = 1.33; wb_.inputs["Specular IOR Level"].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=1, location=BT); ocean = bpy.context.object; ocean.name = "ocean"
om = ocean.modifiers.new("ocean", "OCEAN"); om.geometry_mode = "GENERATE"; om.size = 1.0; om.spatial_size = 60
om.resolution = 10; om.repeat_x = om.repeat_y = 5; om.wave_scale = 1.1; om.choppiness = 1.2; om.wind_velocity = 9
om.time = 0; om.keyframe_insert("time", frame=1); om.time = END / 24; om.keyframe_insert("time", frame=END)
for fc in fcurves(ocean):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
ocean.data.materials.append(M_water); ocean.parent = boat_world; ocean.location = (0, 0, 0)
for p in ocean.data.polygons: p.use_smooth = True
far_sea = plane("far_sea", (6000, 6000), (0, 0, -0.15), M_water, parent=boat_world)
# tog'lar: ridged fraktal shovqin, qorli cho'qqilar, uzoqlik tumani
M_mtn = bpy.data.materials.new("mountain"); M_mtn.use_nodes = True
N = M_mtn.node_tree.nodes; L = M_mtn.node_tree.links; mb = N["Principled BSDF"]
geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], sep.inputs[0])
tcm = N.new("ShaderNodeTexCoord"); sepp = N.new("ShaderNodeSeparateXYZ"); L.new(tcm.outputs["Object"], sepp.inputs[0])
nzm = N.new("ShaderNodeTexNoise"); nzm.inputs["Scale"].default_value = 0.02; nzm.inputs["Detail"].default_value = 8; L.new(tcm.outputs["Object"], nzm.inputs["Vector"])
snowf = N.new("ShaderNodeMath"); snowf.operation = "ADD"; L.new(sep.outputs["Z"], snowf.inputs[0])
hgt = N.new("ShaderNodeMath"); hgt.operation = "MULTIPLY"; hgt.inputs[1].default_value = 0.004; L.new(sepp.outputs["Z"], hgt.inputs[0])
L.new(hgt.outputs[0], snowf.inputs[1])
snz = N.new("ShaderNodeMath"); snz.operation = "ADD"; L.new(snowf.outputs[0], snz.inputs[0]); L.new(nzm.outputs["Fac"], snz.inputs[1])
sr = N.new("ShaderNodeMapRange"); sr.inputs[1].default_value = 1.35; sr.inputs[2].default_value = 1.5; L.new(snz.outputs[0], sr.inputs[0])
cm_ = N.new("ShaderNodeMix"); cm_.data_type = "RGBA"; L.new(sr.outputs[0], cm_.inputs["Factor"])
cm_.inputs[6].default_value = (0.05, 0.05, 0.055, 1); cm_.inputs[7].default_value = (0.85, 0.88, 0.92, 1)
cam_d = N.new("ShaderNodeCameraData"); fog = N.new("ShaderNodeMapRange"); fog.inputs[1].default_value = 600; fog.inputs[2].default_value = 7000
L.new(cam_d.outputs["View Distance"], fog.inputs[0])
fm = N.new("ShaderNodeMix"); fm.data_type = "RGBA"; L.new(fog.outputs[0], fm.inputs["Factor"]); L.new(cm_.outputs[2], fm.inputs[6])
fm.inputs[7].default_value = (0.5, 0.56, 0.63, 1); L.new(fm.outputs[2], mb.inputs["Base Color"]); mb.inputs["Roughness"].default_value = 0.8
for k, (cy, cx, sx, h) in enumerate(((1500, 300, 4200, 1500), (2400, -1500, 4000, 2000), (-1900, 800, 5000, 1700))):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=60, size=1, location=(cx, cy, 0))
    mt = bpy.context.object; mt.name = f"mountains{k}"; mt.scale = (sx, 900, 1); bpy.ops.object.transform_apply(scale=True)
    for v in mt.data.vertices:
        p = v.co + Vector((cx, cy, 0))
        edge = math.sin(math.pi * min(1, max(0, (v.co.y + 450) / 900)))
        n = noise.ridged_multi_fractal(p * (1 / 900) + Vector((k * 7.3, 0, 0)), 1.0, 2.0, 6, 1.0, 2.0)
        v.co.z = max(-5, h * edge * (0.25 + 0.75 * n) - 30)
    for p in mt.data.polygons: p.use_smooth = True
    mt.data.materials.append(M_mtn); mt.parent = boat_world
# --- kema (bow +X, deck z=1.3) ---
boat = empty("boat", (0, 0, 0), boat_world)
DECK = 1.3
def halfw(x):
    if x > 2.0: return 2.5 * math.sqrt(max(0.0, 1 - ((x - 2.0) / 6.2) ** 2))
    return 2.5 - 0.15 * ((x - 2.0) / 9.0) ** 2
def sheer(x): return DECK + 0.55 * max(0.0, (x - 2.5) / 5.7) ** 2
XS = [-7.0 + i * 0.25 for i in range(61)]          # -7 .. 8
prof = [(0.0, -1.3), (0.35, -1.15), (0.75, -0.75), (0.95, -0.15), (1.0, 0.4), (1.0, 1.0)]
hv, hf = [], []
for xi, x in enumerate(XS):
    w = max(halfw(x), 0.02); zt = sheer(x) + 0.9
    pts = [(fy * w, fz if fz < 1.0 else zt) for fy, fz in prof]
    pts[-2] = (pts[-2][0], 0.4)
    ring = [(-y, z) for y, z in reversed(pts)] + [(y, z) for y, z in pts[1:]]
    for y, z in ring: hv.append((x, y, z))
nr = len(prof) * 2 - 1
for xi in range(len(XS) - 1):
    for j in range(nr - 1):
        a = xi * nr + j; hf.append((a, a + 1, a + 1 + nr, a + nr))
hf.append(tuple(range(nr - 1, -1, -1)))                  # transom (orqa devor)
me = bpy.data.meshes.new("hull"); me.from_pydata(hv, [], hf); hull = bpy.data.objects.new("hull", me); sc.collection.objects.link(hull)
hull.parent = boat
for p in hull.data.polygons: p.use_smooth = True
hull.modifiers.new("s", "SOLIDIFY").thickness = 0.06
M_hull = bpy.data.materials.new("hull_paint"); M_hull.use_nodes = True
N = M_hull.node_tree.nodes; L = M_hull.node_tree.links; hb = N["Principled BSDF"]
tch = N.new("ShaderNodeTexCoord"); sph = N.new("ShaderNodeSeparateXYZ"); L.new(tch.outputs["Object"], sph.inputs[0])
cr = N.new("ShaderNodeValToRGB"); L.new(sph.outputs["Z"], cr.inputs[0])
cr.color_ramp.interpolation = "CONSTANT"
E_ = cr.color_ramp.elements; E_[0].position = 0.0; E_[0].color = (0.32, 0.03, 0.02, 1)
E_[1].position = 0.22; E_[1].color = (0.02, 0.025, 0.04, 1)
e3 = E_.new(0.38); e3.color = (0.72, 0.72, 0.68, 1)
e4 = E_.new(1.95); e4.color = (0.05, 0.12, 0.3, 1)
mprc = N.new("ShaderNodeMapRange"); mprc.inputs[1].default_value = -1.5; mprc.inputs[2].default_value = 3.0
L.new(sph.outputs["Z"], mprc.inputs[0]); L.new(mprc.outputs[0], cr.inputs[0])
cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[1].position = (0.15 + 1.5) / 4.5
cr.color_ramp.elements[2].position = (0.35 + 1.5) / 4.5; cr.color_ramp.elements[3].position = (1.95 + 1.5) / 4.5
grime = N.new("ShaderNodeTexNoise"); grime.inputs["Scale"].default_value = 3; grime.inputs["Detail"].default_value = 10
mpg = N.new("ShaderNodeMapping"); mpg.inputs["Scale"].default_value = (1, 1, 6); L.new(tch.outputs["Object"], mpg.inputs[0]); L.new(mpg.outputs[0], grime.inputs["Vector"])
gm = N.new("ShaderNodeMix"); gm.data_type = "RGBA"; gm.blend_type = "MULTIPLY"; gm.inputs["Factor"].default_value = 0.45
L.new(cr.outputs[0], gm.inputs[6]); L.new(grime.outputs["Color"], gm.inputs[7]); L.new(gm.outputs[2], hb.inputs["Base Color"])
hb.inputs["Roughness"].default_value = 0.45
hull.data.materials.append(M_hull)
# paluba
dv = [(x, -max(halfw(x), 0.02) * 0.97, sheer(x) - 0.02) for x in XS] + [(x, max(halfw(x), 0.02) * 0.97, sheer(x) - 0.02) for x in reversed(XS)]
me = bpy.data.meshes.new("deck"); me.from_pydata(dv, [], [tuple(range(len(dv)))]); deck = bpy.data.objects.new("deck", me)
sc.collection.objects.link(deck); deck.parent = boat
M_deck = pbr("deck_wood", "wood_floor_deck", 0.5, tint=(0.75, 0.7, 0.65)); deck.data.materials.append(M_deck)
M_white = mat("white_paint", (0.75, 0.76, 0.74), 0.4)
M_dark = mat("dark_glass", (0.01, 0.012, 0.015), 0.05)
M_orange = mat("orange", (0.9, 0.22, 0.02), 0.45)
M_yellow = mat("yellow_rain", (0.9, 0.55, 0.02), 0.5)
# rubka (wheelhouse)
box("wheelhouse", (3.0, 3.0, 2.3), (2.6, 0, DECK + 1.15), M_white, parent=boat)
box("wh_roof", (3.4, 3.4, 0.12), (2.6, 0, DECK + 2.36), M_white, parent=boat)
box("wh_win_front", (0.05, 2.6, 0.75), (4.11, 0, DECK + 1.75), M_dark, parent=boat)
for sy in (-1, 1):
    box("wh_win_side", (2.2, 0.05, 0.6), (2.6, sy * 1.51, DECK + 1.8), M_dark, parent=boat)
box("wh_door", (0.05, 0.8, 1.9), (1.09, 0.6, DECK + 0.95), M_dark, parent=boat)
cyl("mast", 0.07, 6.0, (2.0, 0, DECK + 2.4 + 3.0), M_white, parent=boat)
box("radar", (1.2, 0.18, 0.1), (2.0, 0, DECK + 2.4 + 2.2), M_dark, parent=boat)
cyl("boom", 0.06, 6.5, (-1.0, 0, DECK + 3.6), M_white, rot=(0, -65, 0), parent=boat)
bpy.ops.mesh.primitive_torus_add(major_radius=0.33, minor_radius=0.07, location=(1.08, -0.7, DECK + 1.3), rotation=(0, R(90), 0))
lr = bpy.context.object; lr.name = "lifering"; lr.data.materials.append(M_orange); lr.parent = boat
# krab qafaslari, buyalar, arqonlar
M_cage = mat("cage", (0.25, 0.27, 0.28), 0.4, metal=0.6)
M_rope = mat("rope", (0.55, 0.45, 0.25), 0.8)
for i, (cx, cy, cz) in enumerate(((-6.0, -1.1, 0), (-6.0, 0.0, 0), (-5.0, -1.1, 0), (-6.0, -1.1, 1), (-5.0, -1.1, 1), (-6.0, 0.0, 1))):
    c = box(f"crabpot{i}", (0.9, 0.9, 0.75), (cx, cy, DECK + 0.38 + cz * 0.76), M_cage, rot=(0, 0, random.uniform(-4, 4)), parent=boat)
    wf = c.modifiers.new("w", "WIREFRAME"); wf.thickness = 0.025
    sub = c.modifiers.new("sub", "SUBSURF"); sub.levels = 0
for i, (bx, by) in enumerate(((-4.4, -1.6), (-4.0, -1.9), (-3.6, -1.75))):
    sphere(f"buoy{i}", 0.28, (bx, by, DECK + 0.28), M_orange, sub=3, parent=boat)
for i, (rx, ry) in enumerate(((-2.2, -1.7), (-1.8, -1.6))):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.05, location=(rx, ry, DECK + 0.06 + i * 0.1))
    t = bpy.context.object; t.name = f"rope{i}"; t.data.materials.append(M_rope); t.parent = boat
# kemaning chayqalishi
for f in range(1, END + 1, 6):
    t = f / 24
    boat.location = (0, 0, 0.12 * math.sin(t * 1.3)); boat.rotation_euler = (R(2.2 * math.sin(t * 1.1)), R(1.2 * math.sin(t * 0.8 + 1)), 0)
    boat.keyframe_insert("location", frame=f); boat.keyframe_insert("rotation_euler", frame=f)
for fc in fcurves(boat):
    for k in fc.keyframe_points: k.interpolation = "BEZIER"
BOAT_SHOTS = ["boat_rub", "boat_face", "aerial", "cast", "rub_close", "fly_air", "dusk"]
vis(boat_world, rng(*BOAT_SHOTS))

# ======================================================================
# 6) HAMMOM (x = -50) va KLINIKA (x = -80), YAYLOV (x = 300)
# ======================================================================
BA = Vector((-50.0, 0, 0)); bath = empty("bath", BA)
M_tile = pbr("tiles", "long_white_tiles", 0.8, tint=(0.95, 0.95, 0.92))
M_floor = pbr("marble", "marble_tiles", 0.7)
plane("bath_floor", (3.2, 3.2), (0, 0, 0), M_floor, parent=bath)
plane("bath_ceil", (3.2, 3.2), (0, 0, 2.6), mat("ceil", (0.8, 0.8, 0.78), 0.9), rot=(180, 0, 0), parent=bath)
for nm, sz, loc, rot in (("wall_n", (3.2, 2.6), (0, 1.6, 1.3), (90, 0, 0)), ("wall_s", (3.2, 2.6), (0, -1.6, 1.3), (90, 0, 0)),
                         ("wall_e", (3.2, 2.6), (1.6, 0, 1.3), (90, 0, 90)), ("wall_w", (3.2, 2.6), (-1.6, 0, 1.3), (90, 0, 90))):
    plane(nm, sz, loc, M_tile, rot=rot, parent=bath)
sink_root = empty("sink_root", (0, 1.32, 0), bath)
sk = import_glb(BK + "a541b293_u.glb", sink_root)
mn, mx_ = bbox(sk)
sink_root.rotation_euler = (0, 0, R(180)); sink_root.scale = (0.85, 0.85, 1.0)
M_mirror = mat("mirror", (0.92, 0.92, 0.92), 0.0, metal=1.0)
mirror = plane("mirror", (1.0, 0.85), (0, 1.578, 1.55), M_mirror, rot=(90, 0, 0), parent=bath)
box("mirror_frame", (1.06, 0.02, 0.91), (0, 1.595, 1.55), mat("frame", (0.05, 0.05, 0.05), 0.4), parent=bath)
box("mirror_lamp", (0.7, 0.05, 0.05), (0, 1.55, 2.05), mat("lamp", (1, 0.85, 0.65), emit=12), parent=bath)
area("bath_ceil_light", BA + Vector((0, 0.2, 2.5)), 1.0, (1, 0.9, 0.78), [(1, 300)], parent=None)
plant = None
vis(bath, rng("bath_wide", "scared", "mirror"))

CL = Vector((-80.0, 0, 0)); clinic = empty("clinic", CL)
M_wallc = pbr("clinic_wall", "painted_plaster_wall", 0.6, tint=(0.78, 0.9, 0.88))
plane("cl_floor", (5, 5), (0, 0, 0), pbr("cl_floor", "laminate_floor_02", 0.6, tint=(0.8, 0.8, 0.8)), parent=clinic)
plane("cl_ceil", (5, 5), (0, 0, 2.8), mat("cl_ceil", (0.85, 0.85, 0.85), 0.9), rot=(180, 0, 0), parent=clinic)
for nm, sz, loc, rot in (("cw_n", (5, 2.8), (0, 2.5, 1.4), (90, 0, 0)), ("cw_s", (5, 2.8), (0, -2.5, 1.4), (90, 0, 0)),
                         ("cw_e", (5, 2.8), (2.5, 0, 1.4), (90, 0, 90)), ("cw_w", (5, 2.8), (-2.5, 0, 1.4), (90, 0, 90))):
    plane(nm, sz, loc, M_wallc, rot=rot, parent=clinic)
M_leather = mat("leather", (0.02, 0.12, 0.13), 0.35)
CHAIR = Vector((0.0, 0.6, 0))
box("chair_seat", (0.6, 0.55, 0.12), CHAIR + Vector((0, 0, 0.47)), M_leather, parent=clinic)
box("chair_back", (0.6, 0.12, 0.85), CHAIR + Vector((0, 0.33, 0.92)), M_leather, rot=(-12, 0, 0), parent=clinic)
box("chair_base", (0.25, 0.25, 0.42), CHAIR + Vector((0, 0.05, 0.21)), mat("chrome", (0.7, 0.7, 0.7), 0.2, metal=1), parent=clinic)
for sx in (-1, 1):
    box("armrest", (0.08, 0.5, 0.06), CHAIR + Vector((sx * 0.34, 0.02, 0.66)), M_leather, parent=clinic)
box("cabinet", (1.2, 0.45, 0.9), (-1.6, 2.2, 0.45), mat("cab", (0.85, 0.86, 0.85), 0.3), parent=clinic)
box("counter", (1.25, 0.5, 0.04), (-1.6, 2.2, 0.92), mat("ctop", (0.2, 0.22, 0.25), 0.2), parent=clinic)
box("poster", (0.6, 0.02, 0.8), (1.2, 2.48, 1.6), mat("poster", (0.9, 0.9, 0.85), 0.6), parent=clinic)
for i in range(6):
    box(f"chartline{i}", (0.42 - i * 0.06, 0.01, 0.06 - i * 0.007), (1.2, 2.465, 1.88 - i * 0.11), mat("ink", (0.02, 0.02, 0.02), 0.6), parent=clinic)
cyl("lamp_pole", 0.02, 1.9, (0.7, 0.2, 0.95), mat("chrome2", (0.7, 0.7, 0.7), 0.2, metal=1), parent=clinic)
lamp_head = cyl("lamp_head", 0.14, 0.06, (0.45, 0.35, 1.85), mat("lamp_c", (1, 0.97, 0.9), emit=30), rot=(35, 0, -50), parent=clinic)
area("clinic_light", CL + Vector((0, 0, 2.7)), 2.0, (0.92, 0.97, 1.0), [(1, 450)])
vis(clinic, rng("clinic_doc", "clinic_tweezer"))

FD = Vector((300.0, 0, 0)); field = empty("field", FD)
M_grass = pbr("grass", "sparse_grass", 0.35, tint=(0.75, 0.9, 0.6))
gp = plane("pasture", (400, 400), (0, 0, 0), M_grass, parent=field)
cows_bg = empty("cows_bg", (-2.0, 14.0, 0), field); cows_bg.scale = (1.3,) * 3; cows_bg.rotation_euler = (0, 0, R(20))
import_glb(BK + "3bf2e12b_u.glb", cows_bg)
cow_root = empty("cow_root", (0, 0, 0), field)
cobjs = import_glb(BK + "b349a5ee_u.glb", cow_root)
for o in list(cobjs):
    if o.name.startswith("Icosphere"): bpy.data.objects.remove(o, do_unlink=True); cobjs.remove(o)
mn, mx_ = bbox(cobjs)
M_cow = bpy.data.materials.new("holstein"); M_cow.use_nodes = True
N = M_cow.node_tree.nodes; L = M_cow.node_tree.links; cb_ = N["Principled BSDF"]
nzc = N.new("ShaderNodeTexNoise"); nzc.inputs["Scale"].default_value = 1.6; nzc.inputs["Detail"].default_value = 3
tcc = N.new("ShaderNodeTexCoord"); L.new(tcc.outputs["Object"], nzc.inputs["Vector"])
crc = N.new("ShaderNodeValToRGB"); L.new(nzc.outputs["Fac"], crc.inputs[0])
crc.color_ramp.elements[0].position = 0.5; crc.color_ramp.elements[0].color = (0.015, 0.012, 0.01, 1)
crc.color_ramp.elements[1].position = 0.53; crc.color_ramp.elements[1].color = (0.75, 0.72, 0.68, 1)
L.new(crc.outputs[0], cb_.inputs["Base Color"]); cb_.inputs["Roughness"].default_value = 0.7
for o in cobjs:
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(M_cow)
        for p in o.data.polygons: p.use_smooth = True
cow_h = mx_.z - mn.z
cs = 1.45 / cow_h
cow_root.scale = (cs,) * 3; cow_root.location = (0.6, 3.0, -mn.z * cs); cow_root.rotation_euler = (0, 0, R(-35))
for k, (x, y, rz) in enumerate(((4.5, 7.0, 60), (-4.0, 9.5, -120), (7.5, 12.0, 10))):
    cr_ = empty(f"cow_extra{k}", (x, y, -mn.z * cs), field); cr_.scale = (cs,) * 3; cr_.rotation_euler = (0, 0, R(rz))
    for o in import_glb(BK + "b349a5ee_u.glb", cr_):
        if o.name.startswith("Icosphere"): bpy.data.objects.remove(o, do_unlink=True); continue
        if o.type == "MESH":
            o.data.materials.clear(); o.data.materials.append(M_cow)
for i in range(14):
    box(f"fence{i}", (0.1, 0.1, 1.2), (-12 + i * 2.5, 9.0, 0.6), mat("post", (0.25, 0.18, 0.12), 0.8), parent=field)
box("fence_wire", (35, 0.02, 0.02), (4.25, 9.0, 0.95), mat("wire", (0.3, 0.3, 0.3), 0.4, metal=1), parent=field)
vis(field, rng("cows"))

# ======================================================================
# 7) QAHRAMONLAR
# ======================================================================
aroot, abby, ameshes = mc.load_character("abby", "Megan.fbx")
droot, doc, dmeshes = mc.load_character("doc", "Olivia.fbx")
def soften(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.3
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.6
                    n.inputs["Coat Weight"].default_value = 0.0
soften(ameshes + dmeshes)
# Ebbi: oq futbolka -> sariq baliqchi kurtkasi rangi
shirt = next(o for o in ameshes if "Shirt" in o.name)
sm = shirt.data.materials[0].copy(); sm.name = "abby_shirt"; shirt.data.materials[0] = sm
N = sm.node_tree.nodes; L = sm.node_tree.links; bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
lk = bsdf.inputs["Base Color"].links[0]; src = lk.from_socket; L.remove(lk)
mt = N.new("ShaderNodeMix"); mt.data_type = "RGBA"; mt.blend_type = "MULTIPLY"; mt.inputs["Factor"].default_value = 1.0
mt.inputs[7].default_value = (0.95, 0.42, 0.04, 1); L.new(src, mt.inputs[6]); L.new(mt.outputs[2], bsdf.inputs["Base Color"])

A = lambda f, inplace=True: mc.load_action(f, inplace)
def at(root, f, loc, rz):
    root.location = loc; root.rotation_euler = (0, 0, R(rz))
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)

# Ebbi kemada: palubaning orqa qismi (kema bilan birga chayqaladi)
abby_boat = empty("abby_boat_anchor", (-3.0, 0.6, DECK - 0.02), boat)
AB_ON = rng("boat_rub", "boat_face", "cast", "rub_close", "fly_air", "dusk")
c = aroot.constraints.new("CHILD_OF"); c.target = abby_boat; c.inverse_matrix = Matrix.Identity(4)
c.use_scale_x = c.use_scale_y = c.use_scale_z = False
for f, v in ((1, 0.0),) + tuple(x for a, b in AB_ON for x in ((a, 1.0), (b + 1, 0.0))):
    c.influence = v; c.keyframe_insert("influence", frame=f)
for fc in fcurves(aroot):
    if fc.data_path.startswith("constraints"):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
# root joylashuvi: kemada mahalliy (0,0,0) + burilish; hammom va klinikada dunyo koordinatasi
at(aroot, 1, (0, 0, 0), 180)
at(aroot, S["bath_wide"][0], tuple(BA + Vector((0, 0.82, 0))), 180)
at(aroot, S["finger_worm"][0], tuple(BA + Vector((0, 0.82, 0))), 180)
at(aroot, S["scared"][0], tuple(BA + Vector((0, 0.7, 0))), 180)
at(aroot, S["mirror"][0], tuple(BA + Vector((0, 0.9, 0))), 180)
at(aroot, S["clinic_doc"][0], tuple(CL + CHAIR + Vector((0, -0.12, 0))), 0)
at(aroot, S["fly_air"][0], (0, 0, 0), 180)
at(aroot, S["clinic_tweezer"][0], tuple(CL + CHAIR + Vector((0, -0.12, 0))), 0)
at(aroot, S["dusk"][0], (0, 0, 0), 180)
interp(aroot, "CONSTANT")
vis(aroot, rng("boat_rub", "boat_face", "cast", "rub_close", "bath_wide", "scared", "mirror", "clinic_doc", "fly_air", "clinic_tweezer", "dusk"))

mc.add_strip(abby, A("Crying.fbx"), 1, repeat=3.0, blend=0)
mc.add_strip(abby, A("Breathing_Idle.fbx"), S["boat_face"][0], blend=0)
mc.add_strip(abby, A("Fishing_Cast.fbx"), S["cast"][0] - 20, blend=0)
mc.add_strip(abby, A("Crying.fbx"), S["rub_close"][0] - 30, blend=0)
mc.add_strip(abby, A("Crying.fbx"), S["bath_wide"][0] - 22, blend=0)
mc.add_strip(abby, A("Terrified.fbx"), S["scared"][0] - 4, blend=0, speed=1.15)
mc.add_strip(abby, A("Crying.fbx"), S["mirror"][0] - 24, blend=0)
mc.add_strip(abby, A("Sitting_Idle_5.fbx"), S["clinic_doc"][0], blend=0, repeat=2.0)
mc.add_strip(abby, A("Look_Around_2.fbx"), S["fly_air"][0] - 10, blend=0)
mc.add_strip(abby, A("Sitting_Idle_5.fbx"), S["clinic_tweezer"][0], blend=0, repeat=2.0)
mc.add_strip(abby, A("Looking_Down.fbx"), S["dusk"][0], blend=0, repeat=2.0)

at(droot, 1, tuple(CL + Vector((0.85, -0.25, 0))), -135)
at(droot, S["clinic_tweezer"][0], tuple(CL + Vector((0.5, 0.12, 0))), -125)
interp(droot, "CONSTANT")
mc.add_strip(doc, A("Annoyed_Head_Shake.fbx"), S["clinic_doc"][0] - 8, blend=0)
mc.add_strip(doc, A("Pick_Fruit.fbx"), S["clinic_tweezer"][0] - 12, blend=0, speed=0.7)
vis(droot, rng("clinic_doc", "clinic_tweezer"))
# qisqich shifokor qo'lida
twz = empty("doc_tweezer_piv")
c = twz.constraints.new("CHILD_OF"); c.target = doc; c.subtarget = "mixamorig:RightHandIndex1"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
for sx in (-1, 1):
    t = box(f"doc_tweezer{sx}", (0.004, 0.12, 0.0015), (sx * 0.003, 0.06, 0.0), M_steel, rot=(0, 0, sx * 2))
    t.parent = twz
vis(twz, rng("clinic_tweezer"))
# qarmoq Ebbi qo'lida
rodp = empty("rod_piv")
c = rodp.constraints.new("CHILD_OF"); c.target = abby; c.subtarget = "mixamorig:RightHand"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
rod = cyl("fishing_rod", 0.009, 2.4, (0, 0, 0), mat("rod", (0.05, 0.05, 0.06), 0.3), verts=12)
rod.parent = rodp; rod.location = (0.0, 0.06, 1.0); rod.rotation_euler = (R(-90 + 10), 0, 0)
vis(rodp, rng("cast"))

# Ebbining ko'zi (kemadagi pashsha kadri uchun) — bosh fazosi
headA = empty("abby_head")
c = headA.constraints.new("CHILD_OF"); c.target = abby; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
faceA = empty("abby_face_t", (0, 0.1, 0.08), headA)
eyeA_t = empty("abby_eye_t", (-0.032, 0.105, 0.1), headA)

# ======================================================================
# 8) KAMERALAR va pashsha yo'llari
# ======================================================================
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c

eyeT = empty("eyeT", (0, -0.012, 0))
# 1 ilgak: makro, sekin yaqinlashish
c = shot_cam("eye_hook", (0.0, -0.11, 0.004), eyeT, 50, 8.0, focus=0.1)
key(c, 1, loc=(0.004, -0.12, 0.003)); key(c, S["eye_hook"][1], loc=(0.002, -0.075, -0.002))
c.data.dof.focus_object = eyeT
# 2 kemada ko'zini ishqalaydi
c = shot_cam("boat_rub", (0, 0, 0), faceA, 45, 2.4)
c.parent = abby_boat; key(c, S["boat_rub"][0], loc=(-0.3, 1.55, 1.35)); key(c, S["boat_rub"][1], loc=(-0.25, 1.35, 1.38))
# 3 yuzga yaqin, past burchak
c = shot_cam("boat_face", (0, 0, 0), faceA, 60, 2.0)
c.parent = abby_boat; key(c, S["boat_face"][0], loc=(0.35, 0.8, 1.15)); key(c, S["boat_face"][1], loc=(0.3, 0.68, 1.2))
# 4 havodan
boatT = empty("boatT", (0.5, 0, 1.5), boat)
c = shot_cam("aerial", BT + Vector((-28, -26, 16)), boatT, 32, None)
key(c, S["aerial"][0], loc=tuple(BT + Vector((-30, -24, 17)))); key(c, S["aerial"][1], loc=tuple(BT + Vector((-22, -27, 13))))
# 5 qarmoq tashlash: pastdan keng
castT = empty("castT", (0.0, 0.6, 1.25), abby_boat)
c = shot_cam("cast", (0, 0, 0), castT, 16, 6.0, focus=faceA)
c.parent = abby_boat; key(c, S["cast"][0], loc=(1.7, -1.6, 0.45)); key(c, S["cast"][1], loc=(1.5, -1.45, 0.5))
# 6 qizargan ko'z: yon tomondan sekin
c = shot_cam("eye_red", (0, 0, 0), eyeT, 55, 8.0, focus=eyeT)
key(c, S["eye_red"][0], loc=(-0.03, -0.095, 0.01)); key(c, S["eye_red"][1], loc=(-0.015, -0.07, 0.006))
# 7 ko'zini ishqalaydi, yaqin
c = shot_cam("rub_close", (0, 0, 0), faceA, 80, 2.0)
c.parent = abby_boat; key(c, S["rub_close"][0], loc=(-0.15, 1.3, 1.55)); key(c, S["rub_close"][1], loc=(-0.12, 1.15, 1.55))
# 8 hammom keng
bathT = empty("bathT", tuple(BA + Vector((0, 1.0, 1.3))))
c = shot_cam("bath_wide", tuple(BA + Vector((1.35, -1.3, 0.5))), bathT, 18, 5.6, focus=faceA)
key(c, S["bath_wide"][0], loc=tuple(BA + Vector((1.35, -1.35, 0.45)))); key(c, S["bath_wide"][1], loc=tuple(BA + Vector((1.1, -1.0, 0.55))))
# 9 tortib chiqarish (makro)
pullT = empty("pullT", tuple(EXIT + Vector((0.002, -0.004, -0.002))))
c = shot_cam("eye_pull", (-0.03, -0.085, -0.01), pullT, 50, 9.0, focus=pullT)
key(c, P0, loc=(-0.032, -0.088, -0.008)); key(c, S["eye_pull"][1], loc=(-0.024, -0.08, -0.016))
# 10 barmoqdagi chuvalchang
fwT = empty("fwT", tuple(FW + Vector((0.0005, -0.006, 0.0075))))
c = shot_cam("finger_worm", tuple(FW + Vector((0.035, -0.045, 0.03))), fwT, 60, 6.0, focus=fwT)
key(c, F0, loc=tuple(FW + Vector((0.035, -0.045, 0.03)))); key(c, F1, loc=tuple(FW + Vector((0.028, -0.036, 0.026))))
# 11 qo'rqib ketdi: past burchak, crash zoom
c = shot_cam("scared", tuple(BA + Vector((0.25, 1.45, 0.75))), faceA, 18, 4.0)
for f, l in ((S["scared"][0], 18), (S["scared"][0] + 5, 34), (S["scared"][1], 38)):
    c.data.lens = l; c.data.keyframe_insert("lens", frame=f)
shake(c, S["scared"][0], S["scared"][0] + 14, 0.02, 5)
# 12 yelka ortidan ko'zgu
mirT = empty("mirT", tuple(BA + Vector((0.0, 1.585, 1.5))))
c = shot_cam("mirror", tuple(BA + Vector((0.32, 0.25, 1.62))), mirT, 40, 2.8, focus=1.95)
key(c, S["mirror"][0], loc=tuple(BA + Vector((0.32, 0.22, 1.62)))); key(c, S["mirror"][1], loc=tuple(BA + Vector((0.27, 0.35, 1.6))))
# 13-14 qovoq ostida
lidT = empty("lidT", (0.0, -0.011, -0.006))
c = shot_cam("eye_lid", (0, 0, 0), lidT, 60, 9.0, focus=lidT)
key(c, S["eye_lid"][0], loc=(-0.012, -0.085, -0.004)); key(c, S["eye_lid"][1], loc=(-0.008, -0.075, -0.004))
c = shot_cam("eye_lid2", (0, 0, 0), lidT, 50, 10.0, focus=lidT)
key(c, S["eye_lid2"][0], loc=(0.012, -0.08, -0.006))
for f, l in ((S["eye_lid2"][0], 40), (S["eye_lid2"][0] + 5, 95), (S["eye_lid2"][1], 105)):
    c.data.lens = l; c.data.keyframe_insert("lens", frame=f)
shake(c, S["eye_lid2"][0] + 4, S["eye_lid2"][0] + 14, 0.0012, 7)
# 15 klinika: shifokor bosh chayqaydi
docF = empty("doc_face", (0, 0.1, 0.06))
c2 = docF.constraints.new("CHILD_OF"); c2.target = doc; c2.subtarget = "mixamorig:Head"
c2.use_scale_x = c2.use_scale_y = c2.use_scale_z = False; c2.inverse_matrix = Matrix.Identity(4)
clT = empty("clT", tuple(CL + Vector((0.3, 0.2, 1.2))))
c = shot_cam("clinic_doc", tuple(CL + Vector((-1.2, -1.9, 0.6))), clT, 22, 4.0, focus=docF)
key(c, S["clinic_doc"][0], loc=tuple(CL + Vector((-1.3, -2.0, 0.55)))); key(c, S["clinic_doc"][1], loc=tuple(CL + Vector((-1.05, -1.7, 0.65))))
# 16 Petri idishi: bitta chuvalchang
dT = empty("dT", tuple(DS + Vector((0, 0, 0.0017))))
c = shot_cam("dish1", tuple(DS + Vector((0.01, -0.05, 0.09))), dT, 60, 8.0, focus=dT)
key(c, S["dish1"][0], loc=tuple(DS + Vector((0.012, -0.055, 0.095)))); key(c, S["dish1"][1], loc=tuple(DS + Vector((0.006, -0.035, 0.065))))
# 17 yaylov
cowT = empty("cowT", tuple(FD + Vector((0.3, 4.0, 1.1))))
c = shot_cam("cows", tuple(FD + Vector((-2.2, -1.5, 0.3))), cowT, 16, 6.0, focus=cow_root)
key(c, S["cows"][0], loc=tuple(FD + Vector((-2.3, -1.6, 0.3)))); key(c, S["cows"][1], loc=tuple(FD + Vector((-1.8, -0.9, 0.35))))
# 18-19 sigir ko'zi
cET = empty("cET", (1.0, -0.017, 0.0))
c = shot_cam("cow_eye", (1.0, -0.13, 0.01), cET, 50, 8.0, focus=cET)
key(c, S["cow_eye"][0], loc=(1.0, -0.14, 0.012)); key(c, S["cow_eye"][1], loc=(1.0, -0.115, 0.008))
cFT = empty("cFT", (1.0 - WC * 0.85, -0.012, 0.001))
c = shot_cam("cow_fly", (0, 0, 0), cFT, 60, 7.0, focus=cFT)
key(c, S["cow_fly"][0], loc=(1.0 - 0.025, -0.095, 0.02)); key(c, S["cow_fly"][1], loc=(1.0 - 0.02, -0.085, 0.024))
# pashsha: sigir ko'zi ichki burchagida ichadi, 818 da uchib ketadi
CF0, CF1 = S["cow_fly"]
corner = Vector((1.0 - WC * 0.92, -0.0105, -0.0005))
for f in range(CF0, CF1 + 1):
    if f < 818:
        fly_at(f, corner + Vector((0.0008 * math.sin(f * 0.3), -0.004, 0.003)), (1, 0.25, -0.35), flap=False)
    else:
        t = (f - 818) / 22
        fly_at(f, corner + Vector((-0.004 - 0.02 * t, -0.006 - 0.03 * t, 0.003 + 0.03 * t * t)), (-0.6, -0.5, 0.6), flap=True)
fly_hold_end(CF1)
# 20 kema ustida uchayotgan pashsha (sekinlashgan), orqada Ebbi xira
FA0, FA1 = S["fly_air"]
flyA_T = empty("flyA_T", (-0.05, 0.0, 1.5), abby_boat)
c = shot_cam("fly_air", (0, 0, 0), flyA_T, 70, 7.0, focus=fly)
c.parent = abby_boat; c.location = (0.15, 1.9, 1.45)
for f in range(FA0, FA1 + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    cm = c.matrix_world; fwd = -(cm.to_3x3() @ Vector((0, 0, 1))).normalized()
    t = (f - FA0) / (FA1 - FA0)
    p = cm.translation + fwd * 0.16 + (cm.to_3x3() @ Vector((0.012 - 0.024 * t, 0.006 * math.sin(t * 6), 0)))
    fly_at(f, p, (cm.to_3x3() @ Vector((-1, 0, -0.2))), flap=(f % 4 < 2) or True)
fly_hold_end(FA1)
# 21 pashsha ko'zga qo'nadi
FL0, FL1 = S["eye_land"]
lspot = E.on_eye(eA, 0.0055, -0.0038, 0.0)
for f in range(FL0, FL1 + 1):
    if f < LAND:
        t = (f - FL0) / (LAND - FL0)
        p = lspot + Vector((0.03 * (1 - t), -0.03 * (1 - t) ** 1.5 - 0.0035, 0.025 * (1 - t) + 0.0014))
        fly_at(f, p, (-1, 0.35, -0.3 * (1 - t)), flap=True)
    elif f < FL1 - 8:
        fly_at(f, lspot + Vector((0.0004 * math.sin(f), -0.0035, 0.0014)), (-1, 0.25, -0.15), flap=False)
    else:
        t = (f - (FL1 - 8)) / 8
        fly_at(f, lspot + Vector((0.01 * t, -0.0035 - 0.02 * t, 0.0014 + 0.015 * t)), (0.3, -0.5, 0.8), flap=True)
fly_hold_end(FL1)
landT = empty("landT", tuple(lspot + Vector((0, -0.002, 0.001))))
c = shot_cam("eye_land", (0.03, -0.085, 0.012), landT, 55, 9.0, focus=landT)
key(c, FL0, loc=(0.032, -0.09, 0.014)); key(c, FL1, loc=(0.024, -0.075, 0.01))
# 22 rentgen: old tomondan, biroz yuqoridan
c = shot_cam("xray", (0, 0, 0), empty("xrT", (0, -0.01, 0.004)), 50, 11.0, focus=0.08)
key(c, XR0, loc=(-0.012, -0.085, 0.02)); key(c, XR1, loc=(0.012, -0.075, 0.016))
# 23 klinika: qisqich bilan
abF = faceA
c = shot_cam("clinic_tweezer", tuple(CL + CHAIR + Vector((-0.7, -0.75, 1.15))), abF, 40, 2.8)
key(c, S["clinic_tweezer"][0], loc=tuple(CL + CHAIR + Vector((-0.75, -0.8, 1.12)))); key(c, S["clinic_tweezer"][1], loc=tuple(CL + CHAIR + Vector((-0.6, -0.65, 1.15))))
# 24 Petri: 14 ta, tepadan aylanib
c = shot_cam("dish14", (0, 0, 0), dT, 35, 8.0, focus=dT)
for f in range(S["dish14"][0], S["dish14"][1] + 1, 4):
    a = R(-60 + (f - S["dish14"][0]) * 0.6)
    key(c, f, loc=tuple(DS + Vector((0.1 * math.sin(a), -0.1 * math.cos(a), 0.12))))
# 25 shom: Ebbi yolg'iz, past burchakdan aylanma
pv = empty("dusk_piv", (0, 0, 0), abby_boat)
c = shot_cam("dusk", (0, 0, 0), faceA, 24, 4.0)
c.parent = pv; c.location = (0.0, 1.5, 0.25)
key(pv, S["dusk"][0], rot=(0, 0, -40)); key(pv, S["dusk"][1], rot=(0, 0, 25))
# 26 sog' ko'z
c = shot_cam("eye_healthy", (0, 0, 0), eyeT, 50, 9.0, focus=eyeT)
key(c, S["eye_healthy"][0], loc=(0.0, -0.07, 0.002)); key(c, S["eye_healthy"][1], loc=(0.002, -0.095, 0.004))
# 27 pashsha yaqinlashadi (fokus pashshaga o'tadi)
FP0, FP1 = S["fly_approach"]
CAMP = Vector((-0.035, -0.085, 0.006)); AX = (eyeT.location - CAMP).normalized()
SIDE = AX.cross(Vector((0, 0, 1))).normalized()
c = shot_cam("fly_approach", tuple(CAMP), eyeT, 50, 6.0, focus=0.09)
for f in range(FP0, FP1 + 1):
    t = (f - FP0) / (FP1 - FP0)
    d = 0.012 + 0.05 * t
    p = CAMP + AX * d + SIDE * (0.004 * (1 - t) + 0.0015 * math.sin(t * 11)) + Vector((0, 0, -0.002 + 0.0012 * math.sin(t * 7)))
    fly_at(f, p, AX + Vector((0, 0, 0.1)), flap=True)
    c.data.dof.focus_distance = d if t < 0.85 else d + (t - 0.85) / 0.15 * (0.081 - d)
    c.data.dof.keyframe_insert("focus_distance", frame=f)
# 28 ko'z keskin yumiladi, pashsha qovoqqa urilib qaytadi
FS0, FS1 = S["eye_shut"]
for f in range(FS0, FS1 + 1):
    t = (f - FS0)
    if t < 4: p = Vector((0.006 - 0.0012 * t, -0.03 + 0.0035 * t, 0.006))
    else: p = Vector((0.0012 + 0.003 * (t - 4), -0.016 - 0.0035 * (t - 4), 0.006 + 0.0015 * (t - 4)))
    fly_at(f, p, (-1, 0.6, 0.1) if t < 4 else (0.6, -0.6, 0.4), flap=True)
c = shot_cam("eye_shut", (0.004, -0.075, 0.003), eyeT, 55, 8.0, focus=eyeT)
shake(c, FS0 + 4, FS0 + 14, 0.0015, 9)
vis(fly, rng("cow_fly", "fly_air", "eye_land", "fly_approach", "eye_shut"))

# kesish markerlari
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["eye_hook"]

# ======================================================================
# 9) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
tcw = N.new("ShaderNodeTexCoord"); mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(120))
L.new(tcw.outputs["Generated"], mpw.inputs[0])
envs = []
for nm in ("kloofendal_overcast_puresky", "kloofendal_48d_partly_cloudy_puresky"):
    e_ = N.new("ShaderNodeTexEnvironment"); e_.image = bpy.data.images.load(PH + nm + ".hdr"); L.new(mpw.outputs[0], e_.inputs[0]); envs.append(e_)
mxw = N.new("ShaderNodeMix"); mxw.data_type = "RGBA"; L.new(envs[0].outputs[0], mxw.inputs[6]); L.new(envs[1].outputs[0], mxw.inputs[7])
tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs["Factor"].default_value = 1.0
L.new(mxw.outputs[2], tint.inputs[6]); tint.inputs[7].default_value = (1, 1, 1, 1)
bg = N["Background"]; L.new(tint.outputs[2], bg.inputs[0])
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.angle = R(2)
# (kadr, hdri tanlash 0/1, osmon kuchi, rang, quyosh kuchi, quyosh rangi, quyosh burchagi)
DAY = (1.0, 0.98, 0.95)
LIGHT = {"eye_hook": (0, 0.45, DAY, 0.0), "boat_rub": (0, 1.0, DAY, 1.5), "eye_red": (0, 0.45, DAY, 0.0), "rub_close": (0, 1.0, DAY, 1.5),
         "bath_wide": (0, 0.0, DAY, 0.0), "eye_pull": (0, 0.35, (1, 0.9, 0.8), 0.0), "finger_worm": (0, 0.0, DAY, 0.0),
         "scared": (0, 0.0, DAY, 0.0), "eye_lid": (0, 0.35, (1, 0.9, 0.8), 0.0), "clinic_doc": (0, 0.0, DAY, 0.0),
         "dish1": (0, 0.25, (0.9, 0.95, 1.0), 0.0), "cows": (1, 1.0, DAY, 3.5), "cow_eye": (1, 0.8, DAY, 2.5),
         "fly_air": (0, 1.0, DAY, 1.5), "eye_land": (0, 0.45, DAY, 0.0), "xray": (0, 0.0, DAY, 0.0),
         "clinic_tweezer": (0, 0.0, DAY, 0.0), "dish14": (0, 0.25, (0.9, 0.95, 1.0), 0.0),
         "dusk": (0, 0.6, (1.0, 0.6, 0.4), 4.0), "eye_healthy": (1, 0.6, DAY, 0.0)}
cur = None
for f, n in SHOTS:
    cur = LIGHT.get(n, cur)
    hd, ws, col, se = cur
    mxw.inputs["Factor"].default_value = hd; mxw.inputs["Factor"].keyframe_insert("default_value", frame=f)
    bg.inputs[1].default_value = ws; bg.inputs[1].keyframe_insert("default_value", frame=f)
    tint.inputs[7].default_value = (*col, 1); tint.inputs[7].keyframe_insert("default_value", frame=f)
    sun.data.energy = se; sun.data.keyframe_insert("energy", frame=f)
    if n == "dusk":
        sun.data.color = (1.0, 0.5, 0.22); sun.rotation_euler = (R(83), 0, R(200))
    else:
        sun.data.color = (1.0, 0.95, 0.88); sun.rotation_euler = (R(40), 0, R(150))
    sun.data.keyframe_insert("color", frame=f); sun.keyframe_insert("rotation_euler", frame=f)
interp(sun, "CONSTANT"); interp(sun.data, "CONSTANT"); interp(w.node_tree, "CONSTANT")

# makro ko'z: softboks (ko'zda aks etadi), to'ldiruvchi, kontur
eye_on = rng(*EYE_SHOTS)
area("eye_key", (-0.09, -0.14, 0.11), 0.09, (1, 0.95, 0.9), lights_for(eye_on, 1.6), target=eA["root"])
area("eye_fill", (0.12, -0.1, -0.03), 0.12, (0.85, 0.9, 1.0), lights_for(eye_on, 0.5), target=eA["root"])
area("eye_xray_rim", (0.0, 0.05, 0.12), 0.08, (0.4, 0.7, 1.0), lights_for(rng("xray"), 3.0), target=eA["root"])
area("eye_red_rim", (0.09, 0.0, 0.05), 0.05, (1.0, 0.2, 0.1), lights_for(rng("eye_shut", "eye_lid2"), 1.2), target=eA["root"])
area("fw_key", tuple(FW + Vector((-0.08, -0.06, 0.12))), 0.08, (1, 0.9, 0.78), lights_for(rng("finger_worm"), 2.0), target=fw_root)
area("fw_rim", tuple(FW + Vector((0.05, 0.1, 0.06))), 0.05, (1, 0.6, 0.35), lights_for(rng("finger_worm"), 1.5), target=fw_root)
area("cow_key", (1.0 - 0.1, -0.15, 0.12), 0.12, (1, 0.95, 0.88), lights_for(rng("cow_eye", "cow_fly"), 2.5), target=eC["root"])
area("dish_key", tuple(DS + Vector((0.0, 0.0, 0.35))), 0.25, (0.95, 0.98, 1.0), lights_for(rng("dish1", "dish14"), 12), target=d_root)
area("dish_rim", tuple(DS + Vector((0.0, 0.2, 0.08))), 0.1, (0.6, 0.8, 1.0), lights_for(rng("dish1", "dish14"), 3), target=d_root)
area("scared_rim", tuple(BA + Vector((-0.6, 0.1, 2.0))), 0.6, (1.0, 0.15, 0.08), lights_for(rng("scared"), 120), target=faceA)
area("face_fill_boat", (0, 0, 0), 0.8, (1, 0.92, 0.85), lights_for(rng("boat_face", "rub_close"), 40), target=faceA,
     parent=abby_boat).location = (0.4, 1.4, 1.6)
area("tweezer_fill", tuple(CL + CHAIR + Vector((-0.5, -0.6, 1.6))), 0.5, (1, 0.95, 0.9), lights_for(rng("clinic_tweezer"), 60), target=faceA)

# ======================================================================
# 10) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 12)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
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
