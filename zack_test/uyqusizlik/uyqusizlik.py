# Uch kun uxlamasangiz, miya o'zini o'zi yeydi — Zack D. Films uslubida 43.5 s video (1044 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; procedural yordamchilar: zack_test/burish/parts.py (miya, quvur, impuls, rentgen)
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/uyqusizlik/uyqusizlik.py --render
# Sinov: FRAMES=15,50,90,140 PCT=35 OUT=/tmp/claude-0/test/
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
END = 1044
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan) ----------------
SHOTS = [(1, "hook"), (34, "lapse"), (66, "xray"), (109, "eat"), (157, "sleep"), (206, "cells"), (270, "toxin"),
         (342, "wash"), (408, "nod"), (467, "crazy"), (528, "astro"), (624, "cut"), (695, "synapse"), (773, "scary"),
         (817, "lapse2"), (883, "dead"), (976, "holes")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM = rng("hook", "lapse", "sleep", "nod", "scary", "lapse2")
XH = rng("xray", "holes")
EAT = rng("eat")
M0_SH = rng("cells", "toxin", "wash", "crazy")
M1_SH = rng("astro", "cut", "synapse")
M2_SH = rng("dead")
CUT_F = 668            # asab tolasi uziladigan kadr ("tolalarini" ~27.8 s)

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
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
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
hor = N.new("ShaderNodeMix"); hor.data_type = "RGBA"; hor.inputs[7].default_value = (1.0, 0.75, 0.5, 1)
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
LAP = Vector((0.6, -1.17, DESK_TOP))
R_(box("lap_base", (0.33, 0.23, 0.014), tuple(LAP + Vector((0, 0, 0.007))), lap_m, bevel=0.004))
R_(box("lap_kb", (0.28, 0.1, 0.002), tuple(LAP + Vector((0, -0.04, 0.0145))), key_m))
HINGE = LAP + Vector((0, -0.115, 0.014))
scr_par = empty("scr_par", tuple(HINGE)); scr_par.rotation_euler = (R(-12), 0, 0); R_(scr_par)
lid = box("lap_lid", (0.33, 0.008, 0.22), (0, -0.004, 0.11), lap_m, parent=scr_par, bevel=0.003)
screen_m = bpy.data.materials.new("screen"); screen_m.use_nodes = True
N = screen_m.node_tree.nodes; L = screen_m.node_tree.links; N.remove(N["Principled BSDF"])
tcs = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tcs.outputs["Object"], sep.inputs[0])
lines = P.math_n(N, L, "GREATER_THAN", P.math_n(N, L, "SINE", P.math_n(N, L, "MULTIPLY", sep.outputs["Y"], 260.0)), 0.1)
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
cmb = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "MULTIPLY", sep.outputs["X"], 18.0), cmb.inputs[0])
L.new(P.math_n(N, L, "FLOOR", P.math_n(N, L, "MULTIPLY", sep.outputs["Y"], 41.0)), cmb.inputs[1]); L.new(cmb.outputs[0], nz.inputs["Vector"])
txt = P.math_n(N, L, "MULTIPLY", lines, P.math_n(N, L, "GREATER_THAN", nz.outputs["Fac"], 0.5))
emc = N.new("ShaderNodeMix"); emc.data_type = "RGBA"; emc.inputs[6].default_value = (0.25, 0.42, 0.95, 1); emc.inputs[7].default_value = (0.9, 0.97, 1.0, 1)
L.new(txt, emc.inputs["Factor"])
em = N.new("ShaderNodeEmission"); L.new(emc.outputs[2], em.inputs["Color"]); em.inputs["Strength"].default_value = 3.0
L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
scr = plane("lap_screen", (0.30, 0.19), (0, 0.0005, 0.115), screen_m, rot=(90, 0, 0), parent=scr_par)
scr.rotation_euler = (R(90), 0, R(180))
# krujkalar va energetik ichimlik bankalari (time-lapse'da ko'payadi)
cups = []
cer = [mat("cer_w", (0.9, 0.9, 0.88), 0.25, coat=0.6), mat("cer_r", (0.6, 0.06, 0.05), 0.3, coat=0.6), mat("cer_k", (0.03, 0.03, 0.03), 0.3, coat=0.6),
       mat("cer_y", (0.85, 0.6, 0.15), 0.3, coat=0.6)]
coffee_m = mat("coffee", (0.05, 0.02, 0.008), 0.08)
can_m = [mat("can_g", (0.15, 0.75, 0.2), 0.25, metal=0.8), mat("can_b", (0.1, 0.25, 0.85), 0.25, metal=0.8), mat("can_s", (0.75, 0.75, 0.8), 0.2, metal=1.0)]
spots = []
rr_ = random.Random(3)
while len(spots) < 18:
    p = Vector((rr_.uniform(-0.2, 1.4), rr_.uniform(-1.58, -1.02), DESK_TOP))
    if 0.36 < p.x < 0.84 and p.y > -1.38: continue
    if (p - Vector((1.25, -1.45, DESK_TOP))).length < 0.17: continue
    if any((p - q).length < 0.1 for q in spots): continue
    spots.append(p)
for i, p in enumerate(spots):
    g = empty(f"cup{i}", tuple(p)); R_(g)
    if i % 3 == 2:
        cyl(f"can{i}", 0.033, 0.122, (0, 0, 0.061), can_m[i % 3], parent=g)
        cyl(f"can{i}_t", 0.029, 0.004, (0, 0, 0.123), can_m[2], parent=g)
    else:
        cyl(f"mug{i}", 0.041, 0.095, (0, 0, 0.0475), cer[i % 4], parent=g)
        cyl(f"mug{i}_c", 0.037, 0.003, (0, 0, 0.085), coffee_m, parent=g)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.007, location=(0.045, 0, 0.05), rotation=(R(90), 0, 0))
        h = bpy.context.object; h.name = f"mug{i}_h"; h.data.materials.append(cer[i % 4]); h.parent = g
        for pp in h.data.polygons: pp.use_smooth = True
    g.rotation_euler.z = rr_.uniform(0, 6.28)
    cups.append(g)

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
duv = R_(box("duvet", (1.56, 1.5, 0.34), tuple(BEDC + Vector((0, -0.29, MT + 0.15))), duvet_m, bevel=0.1))
import bmesh
_bm = bmesh.new(); _bm.from_mesh(duv.data)
bmesh.ops.subdivide_edges(_bm, edges=_bm.edges[:], cuts=10, use_grid_fill=True); _bm.to_mesh(duv.data); _bm.free()
for v in duv.data.vertices:                         # chetlari pastga osiladi (8 burchakli kubni emas, bo'laklanganini egamiz)
    if abs(v.co.x) > 0.7: v.co.z -= 0.16
    if v.co.y < -0.75: v.co.z -= 0.08
sub = duv.modifiers.new("s", "SUBSURF"); sub.levels = 1; sub.render_levels = 2; sub.show_viewport = False
noisy(duv, 0.06, 0.25)
NS = BEDC + Vector((1.05, 0.85, 0))
R_(box("nightstand", (0.45, 0.4, 0.5), tuple(NS + Vector((0, 0, 0.25))), wood_m, bevel=0.01))
clock = R_(import_gltf(PH + "alarm_clock_01/alarm_clock_01.gltf", tuple(NS + Vector((0.0, 0.0, 0.5))), -35, 1.3))
point("clock_glow", tuple(NS + Vector((0.0, -0.15, 0.62))), 0.05, (1.0, 0.8, 0.5), lights_for(rng("lapse2", "sleep"), 0.6))
rug = R_(plane("rug", (1.4, 1.0), (-0.3, -0.3, 0.004), mat("rug", (0.45, 0.14, 0.12), 0.95)))
noisy(rug, 0.004, 0.05)

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
MEG_DESK = Vector((0.6, -0.6, float(os.environ.get("CHAIR_DZ", 0.0))))
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)
place(mroot, 1, tuple(MEG_DESK))
place(mroot, S["sleep"][0], tuple(MEG_BED))
place(mroot, S["cells"][0], tuple(MEG_DESK))
place(mroot, S["lapse2"][0], tuple(MEG_BED))
interp(mroot, "CONSTANT")
def strip(act, start, repeat=1.0, speed=1.0):
    s = mc.add_strip(meg, act, start, repeat=repeat, speed=speed, blend=0, hold=False)
    s.blend_in = s.blend_out = 0; s.use_auto_blend = False
    return s
strip(A_("Typing.fbx"), 1, repeat=1.52)
strip(A_("Sitting_Disbelief_3.fbx"), S["scary"][0] - 12)
strip(A_("Laying_Sleeping.fbx"), S["sleep"][0] - 6, repeat=2.0)
strip(A_("Laying_Sleeping.fbx"), S["lapse2"][0], repeat=(END - S["lapse2"][0] + 4) / 32.8)
# mudrash: bosh sekin tushadi, keyin cho'chib ko'tariladi (COMBINE)
BB = {n: meg.pose.bones["mixamorig:" + n] for n in ("Spine2", "Neck", "Head")}
def pq(o, f, rot):
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Euler([R(a) for a in rot]).to_quaternion(); o.keyframe_insert("rotation_quaternion", frame=f)
NOD_SIGN = float(os.environ.get("NOD_SIGN", 1.0))
def bend(f, sp, nk, hd):
    pq(BB["Spine2"], f, (NOD_SIGN * sp, 0, 0)); pq(BB["Neck"], f, (NOD_SIGN * nk, 0, 0)); pq(BB["Head"], f, (NOD_SIGN * hd, 0, 0))
N0_, N1_ = S["nod"]
bend(1, 0, 0, 0); bend(N0_, 2, 4, 6); bend(N0_ + 30, 10, 18, 30); bend(N0_ + 34, 11, 20, 34)
bend(N0_ + 37, -3, -6, -12); bend(N0_ + 42, 0, -2, -4); bend(N1_, 1, 2, 3); bend(N1_ + 1, 0, 0, 0)
ov = meg.animation_data.action; ov.name = "nod_overlay"; ov.use_fake_user = True
meg.animation_data.action = None
_tr = meg.animation_data.nla_tracks.new(); _tr.name = "nod_overlay"
_st = _tr.strips.new("nod_overlay", 1, ov)
if hasattr(_st, "action_slot") and ov.slots: _st.action_slot = ov.slots[0]
_st.blend_type = "COMBINE"; _st.extrapolation = "HOLD"; _st.blend_in = _st.blend_out = 0

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.07, 0.1), headE)          # ko'zlar oldi (Head fazosi: Y tepa, Z old)
# rentgen nusxasi (shaffof Megan)
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.4, base=0.015)
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, XH, recursive=False)
for o in mmeshes:                                   # karavotda shim/krossovka ko'rpa ostidan chiqmasin
    vis(o, rng("hook", "lapse", "nod", "scary") if any(k in o.name for k in ("Pants", "Sneakers")) else ROOM, recursive=False)
for o in room_objs: vis(o, ROOM)

# ======================================================================
# 3) MIYA MATERIALI (yeyilish chuqurchalari: "eat" 0..1)
# ======================================================================
def brain_mat(name, glow=0.0, cell=7.0, rim_str=8.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15
    eat = value_node(m, "eat", 0.0); gl = value_node(m, "glow", glow)
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = cell; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    sp = N.new("ShaderNodeSeparateColor"); L.new(vo.outputs["Color"], sp.inputs[0])
    on = P.math_n(N, L, "GREATER_THAN", sp.outputs[0], 0.35)
    rr = P.math_n(N, L, "MULTIPLY", eat, P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sp.outputs[1], 0.5), 0.3))
    d = vo.outputs["Distance"]
    hole = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "DIVIDE", P.math_n(N, L, "SUBTRACT", rr, d), 0.03), 1.0, clamp=True)
    hole = P.math_n(N, L, "MULTIPLY", hole, on)
    rim = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", d, rr)), 0.045), clamp=True)
    rim = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", rim, on), P.math_n(N, L, "GREATER_THAN", eat, 0.01))
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs[6].default_value = (0.78, 0.42, 0.45, 1); base.inputs[7].default_value = (0.92, 0.6, 0.6, 1)
    L.new(nz.outputs["Fac"], base.inputs["Factor"])
    bc = N.new("ShaderNodeMix"); bc.data_type = "RGBA"; L.new(hole, bc.inputs["Factor"]); L.new(base.outputs[2], bc.inputs[6])
    bc.inputs[7].default_value = (0.02, 0.0, 0.0, 1); L.new(bc.outputs[2], b.inputs["Base Color"])
    rough = N.new("ShaderNodeMix"); rough.inputs[2].default_value = 0.35; rough.inputs[3].default_value = 0.95
    L.new(hole, rough.inputs[0]); L.new(rough.outputs[0], b.inputs["Roughness"])
    fl = P.math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)
    ge = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", fl, 0.15), gl), P.math_n(N, L, "SUBTRACT", 1.0, hole))
    L.new(P.math_n(N, L, "ADD", ge, P.math_n(N, L, "MULTIPLY", rim, rim_str)), b.inputs["Emission Strength"])
    ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; ec.inputs[6].default_value = (1.0, 0.55, 0.65, 1); ec.inputs[7].default_value = (1.0, 0.12, 0.02, 1)
    L.new(P.math_n(N, L, "MULTIPLY", rim, 1.0, clamp=True), ec.inputs["Factor"]); L.new(ec.outputs[2], b.inputs["Emission Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.06
    L.new(P.math_n(N, L, "MULTIPLY", hole, -1.0), bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def assign(root, m):
    for o in root.children_recursive:
        if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(m)

# rentgen boshidagi miya
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
xb_m = brain_mat("xbrain_m", glow=0.4, rim_str=14.0); assign(xbrain, xb_m)
vis(xbrain, XH)
XR0, XR1 = S["xray"]; HO0, HO1 = S["holes"]
val_key(xb_m, "glow", 1, 0.4); val_key(xb_m, "eat", 1, 0.0)
for f in range(XR0 + 4, XR1, 8):
    val_key(xb_m, "glow", f, 5.0); val_key(xb_m, "glow", f + 4, 1.2)
val_key(xb_m, "glow", HO0, 1.0); val_key(xb_m, "eat", HO0 - 1, 0.0); val_key(xb_m, "eat", HO0, 0.42); val_key(xb_m, "eat", HO1, 0.5)
for f in range(HO0 + 6, HO1 - 10, 14):
    val_key(xb_m, "glow", f, 2.2); val_key(xb_m, "glow", f + 6, 0.8)
val_key(xb_m, "glow", HO1 - 4, 0.6)

# makro miya (yeyilish boshlanadi)
MB = Vector((30, 0, 0))
mbr_grp = empty("macro_brain_grp")
mbrain, _ = P.build_brain("mbrain", mbr_grp, size=1.0)
mbrain.location = MB
mb_m = brain_mat("mbrain_m", glow=0.25, rim_str=10.0); assign(mbrain, mb_m)
EA0, EA1 = S["eat"]
val_key(mb_m, "eat", EA0, 0.02); val_key(mb_m, "eat", EA0 + 10, 0.12); val_key(mb_m, "eat", EA1, 0.62)
interp(mb_m.node_tree, "LINEAR")
vis(mbr_grp, EAT)

# ======================================================================
# 4) MIKRO DUNYO: neyronlar, tozalovchi hujayralar, astrotsit
# ======================================================================
def neuron_pulse(name, col, pcol, phase, period=30, base=0.5, width=0.08):
    m = P.pulse_material(name, col, base_emit=base, pulse_col=pcol, width=width)
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 0.5
    for n in m.node_tree.nodes:                        # impuls ortidagi doimiy "iz"ni o'chirish (oq yuvilib ketmasin)
        if n.type == "MATH" and n.operation == "MULTIPLY" and abs(n.inputs[1].default_value - 4.0) < 1e-6 and not n.inputs[1].links:
            n.inputs[1].default_value = 0.0
    f = 1 - phase
    while f < END + period:
        val_key(m, "pos", f, -0.15); val_key(m, "pos", f + period - 1, 1.15)
        f += period
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
    return m
BLUE = [neuron_pulse(f"nrn{i}", (0.08, 0.22, 0.85), (0.15, 0.5, 1.0), i * 9, 34 + i * 5, base=0.35) for i in range(3)]
soma_m = mat("soma", (0.1, 0.25, 0.9), 0.35, sss=0.7, sss_scale=0.1, emit=1.5, emit_col=(0.12, 0.35, 1.0), coat=0.5)
gold_m = neuron_pulse("axon_gold", (0.95, 0.6, 0.12), (1.0, 0.9, 0.5), 0, 20, base=1.6, width=0.05)
dead_m = mat("dead", (0.22, 0.22, 0.24), 0.6, sss=0.3, sss_scale=0.05)
dead_soma = mat("dead_soma", (0.26, 0.25, 0.27), 0.55, sss=0.4, sss_scale=0.05)

def wander(p0, d, steps, step, rnd, wig=0.55):
    pts = [p0.copy()]; p = p0.copy(); d = d.normalized()
    for _ in range(steps):
        d = (d + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * wig).normalized()
        p = p + d * step; pts.append(p.copy())
    return pts
def taper(n, a=1.0, b=0.15): return [a + (b - a) * i / (n - 1) for i in range(n)]

def neuron(name, c, parent, seed, mats, smat, n_dend=6, axon=None, r=0.38, dl=(4, 6), stub=False):
    rnd = random.Random(seed); c = Vector(c); objs = []
    so = sphere(name + "_soma", r, tuple(c), smat, scale=(1.0, 0.85, 1.1), sub=4, parent=parent)
    so.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)); noisy(so, 0.08, 0.35)
    for k in range(n_dend):
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.8, 0.8))).normalized()
        steps = rnd.randint(*dl) if not stub else rnd.randint(1, 2)
        pts = wander(c + d * r * 0.8, d, steps, 0.5, rnd)
        objs.append(P.tube(f"{name}_d{k}", [tuple(p) for p in pts], 0.075, rnd.choice(mats), parent, taper=taper(len(pts), 1.0, 0.2 if not stub else 0.75)))
        if not stub and len(pts) > 3:
            b0 = pts[2]; bd = (pts[3] - pts[2]).normalized() + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
            bp = wander(b0, bd, rnd.randint(2, 4), 0.4, rnd)
            objs.append(P.tube(f"{name}_b{k}", [tuple(p) for p in bp], 0.04, rnd.choice(mats), parent, taper=taper(len(bp), 1.0, 0.25)))
    if axon:
        pts = wander(c + Vector(axon).normalized() * r * 0.8, Vector(axon), 12 if not stub else 2, 0.7, rnd, wig=0.25)
        objs.append(P.tube(f"{name}_ax", [tuple(p) for p in pts], 0.06, rnd.choice(mats), parent, taper=taper(len(pts), 1.0, 0.6)))
    return so, objs

def specks(name, c, n, spread, parent, seed, col=(0.5, 0.7, 1.0)):
    rnd = random.Random(seed); m = mat(name + "_m", col, emit=4.0)
    for i in range(n):
        p = Vector(c) + Vector((rnd.uniform(-1, 1) * spread, rnd.uniform(-1, 1) * spread, rnd.uniform(-0.6, 0.6) * spread))
        sphere(f"{name}{i}", rnd.uniform(0.01, 0.03), tuple(p), m, sub=1, parent=parent)

def blob_mat(name, col, emit_col, emit=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.3
    b.inputs["Subsurface Weight"].default_value = 0.8; b.inputs["Subsurface Scale"].default_value = 0.15
    b.inputs["Coat Weight"].default_value = 0.7; b.inputs["Coat Roughness"].default_value = 0.1
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.0; nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    g = value_node(m, "glow", emit); rage = value_node(m, "rage", 0.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", nz.outputs["Fac"], 2.0), P.math_n(N, L, "ADD", g, P.math_n(N, L, "MULTIPLY", rage, 6.0))), b.inputs["Emission Strength"])
    ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; ec.inputs[6].default_value = (*emit_col, 1); ec.inputs[7].default_value = (1.0, 0.08, 0.03, 1)
    L.new(rage, ec.inputs["Factor"]); L.new(ec.outputs[2], b.inputs["Emission Color"])
    return m

# ---------- M0: tozalovchi hujayralar maydoni ----------
M0 = Vector((60, 0, 0))
m0 = empty("M0_grp")
soma0, _ = neuron("N0", M0, m0, 1, BLUE, soma_m, n_dend=7, axon=(1, 0.3, -0.2))
for i, (p, ax) in enumerate([((-3.5, 2.5, 1.0), (1, -0.5, 0)), ((3.0, 3.0, -1.2), (-1, 0, 0.3)), ((-2.5, -5.5, -1.5), (1, 1, 0)),
                             ((4.5, -2.0, 1.8), (0, 1, 0)), ((0.5, 5.5, 2.0), (0, -1, -0.5)), ((-6, -1, -0.5), (1, 0, 0)),
                             ((6.5, 3.5, 0.5), (-1, -0.4, 0)), ((-1.5, 4.0, -2.4), (0.4, -1, 0.5))]):
    neuron(f"N0_{i}", M0 + Vector(p), m0, 10 + i, BLUE, soma_m, n_dend=5, axon=ax)
specks("sp0_", M0, 120, 9, m0, 2)
green_m = blob_mat("glia_m", (0.25, 0.8, 0.3), (0.4, 1.0, 0.45), emit=0.8)
def glia(name, c, parent, seed, r=0.33):
    rnd = random.Random(seed); g = empty(name, tuple(c), parent)
    b = sphere(name + "_body", r, (0, 0, 0), green_m, scale=(1.15, 0.9, 0.85), sub=4, parent=g); noisy(b, 0.12, 0.3)
    for k in range(7):
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        pts = wander(d * r * 0.7, d, 3, 0.18, rnd, wig=0.7)
        P.tube(f"{name}_p{k}", [tuple(p) for p in pts], 0.05, green_m, g, taper=taper(len(pts), 1.0, 0.1))
    return g
def wobble(o, f0, f1, amp=6.0, seed=1, step=3, jitter=0.0):
    rnd = random.Random(seed)
    for f in range(f0, f1 + 1, step):
        t = f * 0.15
        o.rotation_euler = (R(amp * math.sin(t + seed)), R(amp * math.cos(t * 0.8 + seed)), R(amp * 0.5 * math.sin(t * 0.6)))
        o.keyframe_insert("rotation_euler", frame=f)
        s = 1 + 0.05 * math.sin(t * 1.7 + seed)
        o.scale = (s, 1 / s, s); o.keyframe_insert("scale", frame=f)
TOX_C = M0 + Vector((0.95, -0.85, 0.25))
G = [glia(f"G{i}", M0 + Vector(p), m0, 30 + i) for i, p in enumerate([(-3.5, -2.0, 1.8), (2.8, -3.2, -0.6), (-1.0, 2.6, 1.2), (3.6, 1.2, 1.4), (-3.0, 0.6, -1.4)])]
C0_, C1_ = S["cells"][0], S["crazy"][1]
for i, g in enumerate(G): wobble(g, 1, END, 8, 3 + i)
# G0: chiqindilarga suzib boradi
path_keys(G[0], [(S["cells"][0], M0 + Vector((-3.5, -2.0, 1.8))), (S["cells"][1], M0 + Vector((-0.6, -1.7, 0.85))),
                 (S["toxin"][0] + 26, TOX_C + Vector((-0.42, -0.1, 0.05))), (S["toxin"][1], TOX_C + Vector((-0.2, -0.05, 0.02)))])
path_keys(G[1], [(S["cells"][0], M0 + Vector((2.8, -3.2, -0.6))), (S["toxin"][1], M0 + Vector((1.9, -2.0, -0.2)))])
path_keys(G[2], [(S["cells"][0], M0 + Vector((-1.0, 2.6, 1.2))), (S["toxin"][1], M0 + Vector((-0.2, 1.5, 0.9)))])
# zaharli chiqindilar
tox_m = bpy.data.materials.new("tox"); tox_m.use_nodes = True
N = tox_m.node_tree.nodes; L = tox_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.7, 0.75, 0.05, 1); b.inputs["Roughness"].default_value = 0.4
tcx = N.new("ShaderNodeTexCoord"); vx = N.new("ShaderNodeTexVoronoi"); vx.inputs["Scale"].default_value = 30
L.new(tcx.outputs["Object"], vx.inputs["Vector"])
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", vx.outputs["Distance"], 0.5), 3.0), b.inputs["Emission Strength"])
b.inputs["Emission Color"].default_value = (0.75, 1.0, 0.1, 1)
debris_m = mat("debris", (0.32, 0.26, 0.22), 0.7, sss=0.3, sss_scale=0.05)
rt = random.Random(11); tox = []
for i in range(46):
    p = TOX_C + Vector((rt.gauss(0, 0.45), rt.gauss(0, 0.4), rt.gauss(0, 0.3)))
    if i % 4 == 3: p = M0 + Vector((rt.uniform(-3, 3), rt.uniform(-3, 2), rt.uniform(-1.2, 1.2)))
    deb = i % 5 == 4
    o = sphere(f"tox{i}", rt.uniform(0.05, 0.11) * (1.6 if deb else 1), tuple(p), debris_m if deb else tox_m, sub=2, parent=m0)
    noisy(o, 0.04, 0.05); o.rotation_euler = (rt.uniform(0, 3), rt.uniform(0, 3), rt.uniform(0, 3)); o["deb"] = deb
    tox.append(o)
# yutilish (toxin kadri): G0 yaqinidagilar unga tortiladi
TX0, TX1 = S["toxin"]; WA0, WA1 = S["wash"]
eaten = sorted([o for o in tox if (o.location - TOX_C).length < 0.9 and not o["deb"]], key=lambda o: (o.location - TOX_C).length)[:14]
for k, o in enumerate(eaten):
    f0 = TX0 + 22 + k * 3; p0 = o.location.copy()
    key(o, f0, loc=tuple(p0), scale=1.0)
    for j in range(1, 9):
        f = f0 + j; sc.frame_set(f); bpy.context.view_layer.update()
        gp = G[0].matrix_world.translation
        t = ease(j / 8)
        key(o, f, loc=tuple(p0.lerp(gp, t)), scale=max(0.0, 1 - t * 1.05))
    vis(o, [(1, f0 + 8)], recursive=False)
# yuvilish (wash kadri): qolganlar +X bo'ylab oqim bilan ketadi
for o in tox:
    if o in eaten: continue
    p0 = o.location.copy(); dl = random.Random(o.name).uniform(0, 12)
    key(o, WA0 + int(dl), loc=tuple(p0))
    for j in range(1, 50, 3):
        f = WA0 + int(dl) + j; t = j / 49
        key(o, f, loc=tuple(p0 + Vector((7.0 * t * t + 2.5 * t, 0.4 * math.sin(j * 0.3), 0.3 * math.sin(j * 0.2)))))
    vis(o, [(1, WA1)], recursive=False)
# oqim chiziqlari (glimfatik suyuqlik)
flow_m = bpy.data.materials.new("flow"); flow_m.use_nodes = True
N = flow_m.node_tree.nodes; L = flow_m.node_tree.links; N.remove(N["Principled BSDF"])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.75, 1.0, 1); em.inputs["Strength"].default_value = 4.0
trn = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.55
L.new(trn.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
flow_grp = empty("flow_grp", (0, 0, 0), m0)
rf = random.Random(21)
for i in range(110):
    y = rf.uniform(-4.5, 3.0); z = rf.uniform(-2.0, 2.0); ln = rf.uniform(0.8, 2.2)
    st = P.tube(f"flow{i}", [(0, 0, 0), (ln * 0.5, 0, 0.02), (ln, 0, 0)], 0.012, flow_m, flow_grp, taper=[0.2, 1.0, 0.2])
    x0 = rf.uniform(-14, -4); sp_ = rf.uniform(0.22, 0.38); f0 = WA0 - 4
    key(st, f0, loc=tuple(M0 + Vector((x0, y, z)))); key(st, WA1 + 2, loc=tuple(M0 + Vector((x0 + sp_ * (WA1 + 6 - f0), y, z))))
    interp(st, "LINEAR", "location")
vis(flow_grp, [(WA0, WA1)])
# aqldan ozish (crazy): qo'shimcha hujayralar paydo bo'ladi, hammasi titraydi, qizaradi
CR0, CR1 = S["crazy"]
extra = [glia(f"Gx{i}", M0 + Vector(p), m0, 60 + i, r=0.28) for i, p in enumerate([(0.6, -1.2, 1.0), (-0.9, -1.0, -0.3), (1.6, 0.4, 0.9), (0.2, -2.2, -0.8), (-1.8, -0.4, 0.8), (1.2, -1.8, 0.2)])]
for k, g in enumerate(extra):
    fpop = CR0 + 8 + k * 6
    key(g, 1, scale=0.0); key(g, fpop, scale=0.0); key(g, fpop + 5, scale=1.15); key(g, fpop + 8, scale=1.0)
for k, g in enumerate(G + extra):
    rj = random.Random(90 + k); base = None
    for f in range(CR0, CR1 + 1, 2):
        sc.frame_set(f); p = g.location.copy() if base is None else base
        base = p
        g.location = p + Vector((rj.uniform(-1, 1), rj.uniform(-1, 1), rj.uniform(-1, 1))) * 0.06; g.keyframe_insert("location", frame=f)
        g.rotation_euler = (rj.uniform(-0.5, 0.5), rj.uniform(-0.5, 0.5), rj.uniform(-0.5, 0.5)); g.keyframe_insert("rotation_euler", frame=f)
val_key(green_m, "rage", 1, 0.0); val_key(green_m, "rage", CR0 - 1, 0.0); val_key(green_m, "rage", CR0 + 6, 1.0); val_key(green_m, "rage", CR1 + 1, 0.0)
vis(m0, M0_SH)

# ---------- M1: astrotsit, asab tolasi, sinapslar ----------
M1 = Vector((60, 20, 0))
m1 = empty("M1_grp")
for i, (p, ax) in enumerate([((-4, 3, 1.5), (1, -0.4, 0)), ((4, 3.5, -1), (-1, 0, 0)), ((-5, -2, -2), (1, 0.5, 0.5)), ((5, -1, 2.5), (-1, 0.3, -0.2)),
                             ((0, 5.5, -2), (0, -1, 0.4)), ((-1.5, -6, 2.6), (0.5, 1, 0))]):
    neuron(f"N1_{i}", M1 + Vector(p), m1, 40 + i, BLUE, soma_m, n_dend=5, axon=ax)
specks("sp1_", M1, 110, 9, m1, 3, col=(0.75, 0.6, 1.0))
astro_m = blob_mat("astro_m", (0.5, 0.22, 0.85), (0.65, 0.35, 1.0), emit=1.0)
AST = M1 + Vector((0, 0, -0.3))
astro = empty("astro", tuple(AST), m1)
ab = sphere("astro_body", 0.42, (0, 0, 0), astro_m, scale=(1.0, 1.0, 0.9), sub=4, parent=astro); noisy(ab, 0.1, 0.3)
ra = random.Random(5); procs = []
for k in range(14):
    d = Vector((ra.uniform(-1, 1), ra.uniform(-1, 1), ra.uniform(-0.7, 0.9))).normalized()
    pe = empty(f"astro_pe{k}", (0, 0, 0), astro)
    pts = wander(d * 0.3, d, 5, 0.32, ra, wig=0.45)
    t_ = P.tube(f"astro_p{k}", [tuple(p) for p in pts], 0.07, astro_m, pe, taper=taper(len(pts), 1.0, 0.12))
    if k % 2 == 0:
        bp = wander(pts[3], pts[3] - pts[2] + Vector((ra.uniform(-1, 1), ra.uniform(-1, 1), ra.uniform(-1, 1))), 3, 0.25, ra)
        P.tube(f"astro_pb{k}", [tuple(p) for p in bp], 0.035, astro_m, pe, taper=taper(len(bp), 1.0, 0.15))
    procs.append(pe)
AS0, AS1 = S["astro"]
for k, pe in enumerate(procs):
    key(pe, 1, scale=0.55); key(pe, AS0 + 4, scale=0.55); key(pe, AS0 + 50 + k * 2, scale=1.25); key(pe, AS1, scale=1.35)
    for f in range(AS0, S["synapse"][1] + 1, 4):
        pe.rotation_euler = (R(7 * math.sin(f * 0.13 + k)), R(7 * math.cos(f * 0.11 + k * 1.3)), 0); pe.keyframe_insert("rotation_euler", frame=f)
wobble(astro, 1, END, 4, 7, step=4)
val_key(astro_m, "rage", 1, 0.0); val_key(astro_m, "rage", AS0 + 20, 0.0); val_key(astro_m, "rage", AS1 - 10, 0.85)
for f in range(AS1, S["synapse"][1], 10):
    val_key(astro_m, "rage", f, 0.65); val_key(astro_m, "rage", f + 5, 1.0)
# sog'lom asab tolasi (oltin) — astrotsit oldidan o'tadi, CUT_F da uziladi
K = M1 + Vector((0.15, -1.45, -0.55))
ax_l = P.tube("axon_L", [(-6.5, 0.6, 0.5), (-4.5, -0.3, -0.35), (-2.6, 0.35, 0.3), (-1.2, -0.15, -0.1), (0, 0, 0)], 0.06, gold_m, m1)
ax_r = P.tube("axon_R", [(0, 0, 0), (1.2, 0.15, 0.12), (2.7, -0.35, -0.3), (4.6, 0.3, 0.35), (6.5, -0.5, -0.4)], 0.06, gold_m, m1)
for o in (ax_l, ax_r): o.location = K
for o, sgn, idx in ((ax_l, -1, 4), (ax_r, 1, 0)):
    key(o, CUT_F, loc=tuple(K)); key(o, CUT_F + 10, loc=tuple(K + Vector((sgn * 0.45, 0, -0.05)))); key(o, CUT_F + 40, loc=tuple(K + Vector((sgn * 0.6, 0, -0.1))))
    pt = o.data.splines[0].points[idx]
    pt.radius = 1.0; pt.keyframe_insert("radius", frame=CUT_F); pt.radius = 0.35; pt.keyframe_insert("radius", frame=CUT_F + 6)
gold_glow = gold_m.node_tree.nodes["glow"].outputs[0]
val_key(gold_m, "glow", CUT_F, 1.6); val_key(gold_m, "glow", CUT_F + 2, 6.0); val_key(gold_m, "glow", CUT_F + 14, 0.3)
# astrotsit "qo'li": tolaga cho'zilib, o'rab, uzadi
arm_m = astro_m
grab = P.tube("astro_grab", [(0, 0, 0)] * 6, 0.07, arm_m, m1, taper=[1.0, 0.9, 0.8, 0.7, 0.6, 0.5])
gsp = grab.data.splines[0]
CU0 = S["cut"][0]
def grab_pts(f):
    t = ease(min(1.0, max(0.0, (f - CU0 - 4) / 28.0)))
    a = AST + (K - AST).normalized() * 0.35
    tip = a.lerp(K + Vector((0, -0.05, 0.12)), t)
    pts = [a.lerp(tip, i / 4) + Vector((0, 0, 0.15 * math.sin(i / 4 * math.pi) * (1 - t))) for i in range(5)]
    w = min(1.0, max(0.0, (f - CU0 - 30) / 12.0))          # o'rash: uchi tola atrofida aylanadi
    ang = w * 5.0
    pts.append(K + Vector((0.08 * math.sin(ang * 2), -0.13 * math.cos(ang), 0.13 * math.sin(ang))) if w > 0 else pts[-1] + (pts[-1] - pts[-2]) * 0.3)
    if f > CUT_F:                                             # uzgach tortib oladi
        bk = ease(min(1.0, (f - CUT_F) / 16.0)) * 0.5
        pts = [p.lerp(AST, bk * (i / 5)) for i, p in enumerate(pts)]
    return pts
for f in range(CU0 - 2, S["synapse"][1] + 1):
    for i, p in enumerate(grab_pts(f)):
        gsp.points[i].co = (*p, 1.0); gsp.points[i].keyframe_insert("co", frame=f)
vis(grab, [(CU0 - 2, S["synapse"][1])], recursive=False)
# sinapslar (xotira bog'lamlari): ikki neyron tolalari orasidagi yonuvchi ko'priklar
syn_m = mat("syn", (1.0, 0.8, 0.3), 0.3, emit=5.0, emit_col=(1.0, 0.8, 0.35))
bulb_m = mat("bulb", (1.0, 0.85, 0.4), 0.25, emit=9.0, emit_col=(1.0, 0.82, 0.4))
SY = M1 + Vector((0.0, -1.3, 1.25))
m1s = empty("M1s_grp")
nA, _ = neuron("NA", SY + Vector((-2.4, 0.6, 0.3)), m1s, 71, BLUE, soma_m, n_dend=4)
nB, _ = neuron("NB", SY + Vector((2.4, 0.6, -0.2)), m1s, 72, BLUE, soma_m, n_dend=4)
rs = random.Random(8)
SYN0 = S["synapse"][0]; SY0 = SYN0
for k in range(8):
    x = -2.0 + k * 0.55; yz = Vector((x, rs.uniform(-0.35, 0.35), rs.uniform(-0.35, 0.35)))
    pa = SY + yz + Vector((0, 0, 0.55)); pb = SY + yz + Vector((0.05, 0.1, -0.5))
    wa = [pa + Vector((rs.uniform(-0.25, 0.25), rs.uniform(-0.2, 0.2), 0.45 * j)) for j in (4, 3, 2, 1)]
    wb = [pb + Vector((rs.uniform(-0.25, 0.25), rs.uniform(-0.2, 0.2), -0.45 * j)) for j in (4, 3, 2, 1)]
    P.tube(f"synT{k}a", [tuple(p) for p in wa + [pa]], 0.04, BLUE[k % 3], m1s, taper=[1, 0.9, 0.8, 0.7, 0.6])
    P.tube(f"synT{k}b", [tuple(p) for p in wb + [pb]], 0.04, BLUE[(k + 1) % 3], m1s, taper=[1, 0.9, 0.8, 0.7, 0.6])
    br = P.tube(f"syn{k}", [tuple(pa), tuple((pa + pb) / 2 + Vector((0.05, 0, 0))), tuple(pb)], 0.022, syn_m, None, taper=[1, 0.6, 1])
    bu = sphere(f"bulb{k}", 0.07, tuple((pa + pb) / 2), bulb_m, sub=3)
    fs = SYN0 + 8 + k * 8
    vis(br, [(SY0, fs)], recursive=False)
    p0 = bu.location.copy(); tgt = AST + Vector((0, -0.2, 0.25))
    key(bu, fs, loc=tuple(p0), scale=1.0); key(bu, fs + 2, scale=1.6)
    for j in range(1, 13):
        t = ease(j / 12); mid = p0.lerp(tgt, t) + Vector((0, -0.2, 0.3)) * math.sin(t * math.pi)
        key(bu, fs + 2 + j, loc=tuple(mid), scale=max(0.0, 1.6 * (1 - t)))
    vis(bu, [(SY0, fs + 14)], recursive=False)
    point(f"synfl{k}", tuple((pa + pb) / 2), 0.05, (1.0, 0.8, 0.4), [(1, 0), (fs, 60), (fs + 4, 0)])
point("cut_flash", tuple(K + Vector((0, -0.3, 0.1))), 0.1, (1.0, 0.85, 0.5), [(1, 0), (CUT_F, 400), (CUT_F + 2, 160), (CUT_F + 6, 0)], const=False)
vis(m1, M1_SH)
vis(m1s, rng("synapse"))

# ---------- M2: o'lik neyronlar, bo'shliq ----------
M2 = Vector((60, 40, 0))
m2 = empty("M2_grp")
for i, p in enumerate([(0, 0, 0), (-3, 2.5, 1), (3.5, 2, -1), (-2, -3.5, -1.5), (2.5, -3, 1.6), (0.5, 4.5, 2.4), (-5, 0, -0.5)]):
    neuron(f"N2_{i}", M2 + Vector(p), m2, 80 + i, [dead_m], dead_soma, n_dend=5, axon=(1, 0.2, 0), r=0.34, stub=True)
rd = random.Random(13)
for i in range(26):                                   # uzilgan bo'laklar suzib yuradi
    c = M2 + Vector((rd.uniform(-4, 4), rd.uniform(-4, 4), rd.uniform(-2, 2)))
    d = Vector((rd.uniform(-1, 1), rd.uniform(-1, 1), rd.uniform(-1, 1))).normalized()
    fr = P.tube(f"frag{i}", [tuple(c), tuple(c + d * 0.25 + Vector((0, 0, 0.05))), tuple(c + d * 0.5)], 0.035, dead_m, m2, taper=[0.6, 1, 0.5])
specks("sp2_", M2, 70, 9, m2, 4, col=(0.6, 0.6, 0.7))
# uchqun: tola bo'ylab yuguradi, uzilgan joyda so'nadi
DE0, DE1 = S["dead"]
sp_m = mat("spark", (0.6, 0.85, 1.0), emit=40.0)
spark = sphere("spark", 0.05, tuple(M2), sp_m, sub=2, parent=m2)
s_path = [M2 + Vector((0.3, -0.25, 0.1)), M2 + Vector((0.9, -0.55, 0.15)), M2 + Vector((1.4, -0.9, 0.25)), M2 + Vector((1.7, -1.05, 0.3))]
P.tube("dead_stub", [tuple(p) for p in s_path], 0.06, dead_m, m2, taper=[1, 0.8, 0.6, 0.45])
P.tube("dead_far", [tuple(M2 + Vector((2.6, -1.4, 0.45))), tuple(M2 + Vector((3.4, -1.6, 0.6))), tuple(M2 + Vector((4.4, -1.5, 0.9)))], 0.05, dead_m, m2, taper=[0.5, 0.8, 1])
for j, f in enumerate(range(DE0 + 14, DE0 + 44, 10)): key(spark, f, loc=tuple(s_path[j]), scale=1.0)
key(spark, DE0 + 52, loc=tuple(s_path[3] + Vector((0.25, -0.1, 0.05))), scale=0.9)
key(spark, DE0 + 58, loc=tuple(s_path[3] + Vector((0.35, -0.14, 0.07))), scale=0.0)
for f, s_ in ((DE0 + 62, 0.0), (DE0 + 64, 0.6), (DE0 + 66, 0.0), (DE0 + 71, 0.35), (DE0 + 72, 0.0)):
    key(spark, f, scale=s_)
spl = point("spark_l", tuple(M2), 0.05, (0.5, 0.8, 1.0), [(1, 0), (DE0 + 12, 0), (DE0 + 14, 40), (DE0 + 52, 40), (DE0 + 58, 0), (DE0 + 64, 15), (DE0 + 66, 0)], const=False)
c_ = spl.constraints.new("COPY_LOCATION"); c_.target = spark
vis(m2, M2_SH)

# ======================================================================
# 5) KAMERALAR
# ======================================================================
def at(name, p, parent=None): return empty(name, tuple(p), parent)
# 1 ILGAK: noutbuk tomonidan yuzga tez push-in
H0, H1 = S["hook"]
c = shot_cam("hook", tuple(MEG_DESK + Vector((0.06, -0.62, 0.92))), faceT, 26, 2.0, focus=faceT)
path_keys(c, [(H0, MEG_DESK + Vector((0.07, -0.62, 0.9))), (H1, MEG_DESK + Vector((0.02, -0.4, 1.0)))])
lens_keys(c, [(H0, 26), (H1, 40)])
# 2 time-lapse: stol atrofida aylanma (deraza fonida)
LA0, LA1 = S["lapse"]
lT = at("lapseT", MEG_DESK + Vector((0, -0.6, 0.9)))
c = shot_cam("lapse", (0, 0, 0), lT, 16, 5.6, focus=lT)
orbit(c, LA0, LA1, MEG_DESK + Vector((0, -0.45, 0)), 1.25, 1.05, -125, -85, 1.45, 1.2)
# 3 rentgen: yon tomondan boshga push-in
c = shot_cam("xray", (0, 0, 0), faceT, 32, 2.8, focus=faceT)
path_keys(c, [(XR0, MEG_DESK + Vector((0.95, -0.55, 1.15))), (XR1, MEG_DESK + Vector((0.42, -0.42, 1.12)))])
lens_keys(c, [(XR0, 30), (XR1, 42)])
# 4 makro miya: past burchak, crash zoom + silkinish
eT = at("eatT", MB + Vector((0.2, -0.35, 0.52)))
c = shot_cam("eat", (0, 0, 0), eT, 18, 2.8, focus=eT)
path_keys(c, [(EA0, MB + Vector((1.2, -1.6, 0.55))), (EA0 + 6, MB + Vector((0.75, -1.05, 0.6))), (EA1, MB + Vector((0.55, -0.82, 0.62)))])
lens_keys(c, [(EA0, 18), (EA0 + 6, 30), (EA1, 36)])
shake(c, EA0 + 6, EA0 + 22, 0.025, seed=4)
# 5 uyqu: tepadan aylanib tushuvchi kran
SL0, SL1 = S["sleep"]
sT = at("sleepT", MEG_BED + Vector((0.0, 0.62, 0.98)))
c = shot_cam("sleep", (0, 0, 0), sT, 22, 3.5, focus=sT)
orbit(c, SL0, SL1, MEG_BED + Vector((0, 0.3, 0)), 1.0, 0.6, -20, 15, 2.3, 1.75)
# 6 hujayralar: neyron tarmog'i ichidan uchib kirish
c0T = empty("cellsT")
path_keys(c0T, [(C0_, M0 + Vector((-1.2, -1.0, 0.8))), (S["cells"][1], M0 + Vector((-0.4, -1.4, 0.6)))])
c = shot_cam("cells", (0, 0, 0), c0T, 24, 4.0, focus=G[0])
path_keys(c, [(C0_, M0 + Vector((-6.5, -8.0, 2.6))), (S["cells"][1], M0 + Vector((-2.4, -4.4, 1.3)))])
# 7 chiqindi: G0 atrofida past aylanma
tT = empty("toxT"); c_ = tT.constraints.new("COPY_LOCATION"); c_.target = G[0]
c = shot_cam("toxin", (0, 0, 0), tT, 30, 3.2, focus=tT)
orbit(c, TX0, TX1, TOX_C + Vector((-0.25, 0, 0)), 2.6, 2.0, -35, 5, -0.35, 0.15)
# 8 yuvilish: oqim bilan yonlama ergashish
wT = empty("washT"); path_keys(wT, [(WA0, M0 + Vector((0.2, -0.8, 0.2))), (WA1, M0 + Vector((4.2, -0.8, 0.3)))])
c = shot_cam("wash", (0, 0, 0), wT, 24, 3.5, focus=wT)
path_keys(c, [(WA0, M0 + Vector((-1.2, -4.6, 0.8))), (WA1, M0 + Vector((3.2, -4.0, 0.6)))])
# 9 mudrash: past burchak, sekin yaqinlashish
c = shot_cam("nod", (0, 0, 0), faceT, 24, 2.4, focus=faceT)
path_keys(c, [(N0_, MEG_DESK + Vector((-1.05, -0.5, 0.85))), (N1_, MEG_DESK + Vector((-0.72, -0.38, 0.97)))])
lens_keys(c, [(N0_, 24), (N0_ + 36, 30), (N0_ + 38, 40), (N1_, 42)])
shake(c, N0_ + 36, N0_ + 48, 0.02, seed=9)
# 10 aqldan ozish: crash zoom + kuchli silkinish
crT = empty("crazyT"); c_ = crT.constraints.new("COPY_LOCATION"); c_.target = G[0]
c = shot_cam("crazy", (0, 0, 0), crT, 16, 3.0, focus=crT)
path_keys(c, [(CR0, M0 + Vector((-1.0, -4.8, 1.6))), (CR0 + 7, M0 + Vector((-0.9, -3.4, 1.1))), (CR1, M0 + Vector((-0.6, -3.0, 0.9)))])
lens_keys(c, [(CR0, 16), (CR0 + 7, 30), (CR1, 34)])
shake(c, CR0 + 6, CR1, 0.05, seed=12, decay=False)
# 11 astrotsit: aylanma
aT = at("astroT", AST + Vector((0, 0, 0.1)))
c = shot_cam("astro", (0, 0, 0), aT, 28, 3.5, focus=aT)
orbit(c, AS0, AS1, AST, 4.6, 3.4, -60, 25, 1.4, 0.5)
# 12 uzish: tola va qo'l, chaqnashda silkinish
CU1 = S["cut"][1]
kT = at("cutT", K + Vector((-0.05, 0.45, 0.3)))
c = shot_cam("cut", (0, 0, 0), kT, 30, 3.0, focus=at("cutF", K))
path_keys(c, [(CU0, K + Vector((0.9, -3.2, 0.8))), (CUT_F, K + Vector((0.45, -2.5, 0.5))), (CU1, K + Vector((0.35, -2.2, 0.45)))])
shake(c, CUT_F, CUT_F + 14, 0.05, seed=5)
# 13 sinapslar: yonlama ergashish
SY0, SY1 = S["synapse"]
syT = empty("synT"); path_keys(syT, [(SY0, SY + Vector((-1.5, 0, -0.1))), (SY1, SY + Vector((1.6, 0, -0.3)))])
c = shot_cam("synapse", (0, 0, 0), syT, 28, 3.2, focus=syT)
path_keys(c, [(SY0, SY + Vector((-2.3, -3.6, 0.5))), (SY1, SY + Vector((1.0, -3.2, 0.2)))])
# 14 qo'rqinchli: yuzga crash zoom
SC0, SC1 = S["scary"]
c = shot_cam("scary", (0, 0, 0), faceT, 18, 2.2, focus=faceT)
path_keys(c, [(SC0, MEG_DESK + Vector((0.35, -0.95, 0.85))), (SC0 + 6, MEG_DESK + Vector((0.22, -0.7, 0.98))), (SC1, MEG_DESK + Vector((0.2, -0.64, 1.0)))])
lens_keys(c, [(SC0, 18), (SC0 + 6, 45), (SC1, 50)])
shake(c, SC0 + 5, SC0 + 20, 0.02, seed=3)
# 15 yigirma soat uxlash: time-lapse, karavot atrofida aylanma
LB0, LB1 = S["lapse2"]
l2T = at("lapse2T", MEG_BED + Vector((0.3, 0.45, 0.85)))
c = shot_cam("lapse2", (0, 0, 0), l2T, 18, 5.0, focus=l2T)
orbit(c, LB0, LB1, MEG_BED + Vector((0.3, 0.3, 0)), 2.1, 1.9, 125, 80, 1.75, 1.55)
# 16 o'lik neyronlar: sekin push-in
dT = at("deadT", s_path[3] + Vector((0.1, 0, 0)))
c = shot_cam("dead", (0, 0, 0), dT, 30, 3.0, focus=dT)
path_keys(c, [(DE0, M2 + Vector((-0.4, -4.6, 1.1))), (DE1, M2 + Vector((0.6, -2.9, 0.7)))])
# 17 bo'shliqlar: rentgen, boshdan orqaga chekinish
hT = empty("holesT", (0, 0.1, 0.02), headE)
c = shot_cam("holes", (0, 0, 0), hT, 35, 3.2, focus=hT)
path_keys(c, [(HO0, MEG_BED + Vector((0.32, 0.55, 1.55))), (HO1, MEG_BED + Vector((0.6, -0.4, 2.15)))])
lens_keys(c, [(HO0, 40), (HO1, 28)])
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
# 6) YORUG'LIK VA TIME-LAPSE
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mp = N.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, R(30)); L.new(tcw.outputs["Generated"], mp.inputs[0])
e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + "studio_small_09.hdr"); L.new(mp.outputs[0], e.inputs[0])
bg_st = N.new("ShaderNodeBackground"); L.new(e.outputs[0], bg_st.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.008, 0.02, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_st.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WL = {"hook": (0.02, 0.3), "lapse": (0.08, 0.3), "xray": (0, 1.0), "eat": (0.03, 0.6), "sleep": (0.02, 0.4), "cells": (0, 1.0), "toxin": (0, 1.0),
      "wash": (0, 1.0), "nod": (0.02, 0.3), "crazy": (0, 0.6), "astro": (0, 1.0), "cut": (0, 1.0), "synapse": (0, 1.0), "scary": (0.02, 0.3),
      "lapse2": (0.08, 0.4), "dead": (0, 0.5), "holes": (0, 1.0)}
for f, n in SHOTS:
    for bgn, v in zip((bg_st, bg_dk), WL[n]):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

# time-lapse: deraza (osmon) kun/tun, quyosh nuri xona bo'ylab suriladi
sun = area("sun", (0.6, Y0 - 1.0, 2.6), 1.2, (1.0, 0.82, 0.62), [(1, 0)], shape=(1.2, 1.0))
sunT = empty("sunT", (0.2, -0.2, 0.3)); tr_ = sun.constraints.new("TRACK_TO"); tr_.target = sunT; tr_.track_axis = "TRACK_NEGATIVE_Z"; tr_.up_axis = "UP_Y"
def daykey(f, d):
    val_key(sky_m, "day", f, d); sun.data.energy = 1600 * d; sun.data.keyframe_insert("energy", frame=f)
for f in (1,): daykey(f, 0.0)
for (a, b), per in ((S["lapse"], 11), (S["lapse2"], 9)):
    daykey(a - 1, 0.0)
    for f in range(a, b + 1):
        d = 0.5 - 0.5 * math.cos(2 * math.pi * (f - a) / per)
        daykey(f, d)
        sunT.location = (0.6 + 1.8 * math.sin(2 * math.pi * (f - a) / per / 2), -0.2 + 0.6 * math.cos(2 * math.pi * (f - a) / per), 0.2)
        sunT.keyframe_insert("location", frame=f)
    daykey(b + 1, 0.0)
for fc in mc._fcurves(sun.data.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
for fc in mc._fcurves(sky_m.node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
# krujkalar time-lapse'da birma-bir paydo bo'ladi
for i, g in enumerate(cups):
    f_on = 1 if i < 2 else LA0 + 2 + int(i * 1.7)
    vis(g, [(max(a, f_on), b) for a, b in ROOM if b >= f_on])
# soat millari time-lapse'da aylanadi
SPIN = {"minute_hand": -360 * 7, "houd_hand": -360 * 7 / 12, "second_hand": -360 * 30}
for o in clock.children_recursive:
    pre = next((k for k in SPIN if o.name.startswith(k)), None)
    if not pre: continue
    o.rotation_mode = "XYZ"; r0 = o.rotation_euler.copy()
    o.keyframe_insert("rotation_euler", frame=LB0)
    o.rotation_euler = (r0.x, r0.y + R(SPIN[pre]), r0.z); o.keyframe_insert("rotation_euler", frame=LB1)
    interp(o, "LINEAR")
# xona chiroqlari
LAP_SCR = HINGE + Vector((0, -0.02, 0.12))
meg_face_T = faceT
area("lap_light", tuple(LAP_SCR + Vector((0, 0.03, 0))), 0.3, (0.35, 0.55, 1.0), lights_for(rng("hook", "lapse", "nod", "scary"), 9.0), target=faceT)
area("moon_bed", (0.6, Y0 + 0.1, 2.2), 1.0, (0.45, 0.6, 1.0), lights_for(rng("sleep", "lapse2"), 70.0), target=sT)
area("moon_desk", (-0.4, Y0 + 0.4, 2.4), 1.2, (0.4, 0.55, 1.0), lights_for(rng("hook", "nod", "scary", "lapse"), 25.0), target=at("mdT", MEG_DESK + Vector((0, 0, 1.0))))
point("lamp_bulb", (1.12, -1.3, DESK_TOP + 0.42), 0.04, (1.0, 0.62, 0.32), lights_for(rng("nod", "scary", "lapse", "hook"), 18.0))
area("rim_hook", tuple(MEG_DESK + Vector((-0.7, 0.6, 1.5))), 0.5, (1.0, 0.55, 0.3), lights_for(rng("hook", "nod"), 25.0), target=faceT)
area("scary_red", tuple(MEG_DESK + Vector((0.8, 0.3, 1.6))), 0.6, (1.0, 0.08, 0.04), lights_for(rng("scary"), 80.0), target=faceT)
area("room_fill", (0.0, 0.8, 2.4), 2.0, (0.5, 0.6, 0.9), lights_for(rng("lapse", "lapse2", "sleep"), 45.0), target=at("rfT", (-0.3, -0.3, 0.5)))
# rentgen
area("X_rim", tuple(MEG_DESK + Vector((-0.8, 0.5, 1.6))), 0.8, (0.3, 0.6, 1.0), lights_for(XH, 40.0), target=headE)
# makro miya
area("MB_key", tuple(MB + Vector((-1.2, -1.5, 2.2))), 1.2, (1.0, 0.9, 0.85), lights_for(EAT, 260.0), target=eT)
area("MB_rim", tuple(MB + Vector((1.0, 1.4, 1.4))), 1.0, (1.0, 0.2, 0.08), lights_for(EAT, 420.0), target=eT)
# mikro dunyo
area("M0_key", tuple(M0 + Vector((-3, -3, 5))), 3.0, (0.75, 0.88, 1.0), lights_for(rng("cells", "toxin", "wash"), 900.0), target=at("m0T", M0))
area("M0_rim", tuple(M0 + Vector((3, 4, 2))), 3.0, (0.2, 0.5, 1.0), lights_for(M0_SH, 1100.0), target=at("m0T2", M0 + Vector((0, -1, 0))))
area("M0_red", tuple(M0 + Vector((-3, -2, 4))), 3.0, (1.0, 0.06, 0.03), lights_for(rng("crazy"), 4000.0), target=at("m0T3", M0))
area("M0_red2", tuple(M0 + Vector((2, -5, -1))), 2.0, (1.0, 0.15, 0.05), lights_for(rng("crazy"), 900.0), target=at("m0T4", M0))
area("M1_key", tuple(M1 + Vector((-3, -4, 4))), 3.0, (0.85, 0.85, 1.0), lights_for(M1_SH, 900.0), target=at("m1T", M1))
area("M1_rim", tuple(M1 + Vector((3, 4, 2.5))), 3.0, (0.7, 0.3, 1.0), lights_for(M1_SH, 1200.0), target=at("m1T2", M1))
area("M1_red", tuple(M1 + Vector((3, -3, -2))), 2.5, (1.0, 0.1, 0.05), lights_for([(AS1 - 30, S["synapse"][1])], 700.0), target=at("m1T3", M1))
area("M2_key", tuple(M2 + Vector((-3, -4, 4))), 3.0, (0.6, 0.65, 0.8), lights_for(M2_SH, 450.0), target=at("m2T", M2))
area("M2_rim", tuple(M2 + Vector((3, 4, 2))), 3.0, (0.35, 0.4, 0.6), lights_for(M2_SH, 500.0), target=at("m2T2", M2))

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
