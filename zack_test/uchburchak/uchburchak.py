# Yuzdagi "o'lim uchburchagi" — Zack D. Films uslubida 40.2 s video (966 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py + uyqusizlik.py yordamchilari; procedural: zack_test/burish/parts.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/uchburchak/uchburchak.py --render
# Sinov: FRAMES=20,60,140,200 PCT=35 OUT=/tmp/claude-0/test/
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.bvhtree import BVHTree
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
END = 966
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan) ----------------
SHOTS = [(1, "hook"), (36, "tri"), (76, "wide"), (119, "death"), (162, "fingers"), (224, "squeeze"), (285, "xveins"),
         (366, "xsinus"), (453, "valve"), (555, "press"), (619, "section"), (705, "xflow"), (768, "clot"), (837, "agony"),
         (898, "blind"), (916, "fall")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM = rng("hook", "tri", "wide", "death", "fingers", "squeeze", "press", "agony", "blind", "fall")
XH = rng("xveins", "xsinus", "xflow")
POP_F = 247                       # "nuqta" — husnbuzar yoriladi
VALVE_F = 520                     # "klapanlar" — klapanlar eriydi
NOVALVE_F = 536                   # "yo'q" — qizil chaqnash
TRI_DRAW = (38, 72)               # uchburchak chiziladi

# ---------------- yordamchilar (uyqusizlik.py dan) ----------------
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

def tiles(name, col_a, col_grout=(0.55, 0.55, 0.53), scale=6.0, rough=0.12):
    """procedural keramik plitka (Brick tekstura, kvadrat)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick")
    br.offset = 0.0; br.inputs["Scale"].default_value = scale; br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Brick Width"].default_value = 1.0; br.inputs["Row Height"].default_value = 1.0
    br.inputs["Color1"].default_value = (*col_a, 1); br.inputs["Color2"].default_value = (col_a[0] * 0.93, col_a[1] * 0.93, col_a[2] * 0.93, 1)
    br.inputs["Mortar"].default_value = (*col_grout, 1)
    L.new(tc.outputs["Object"], br.inputs["Vector"]); L.new(br.outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); L.new(br.outputs["Fac"], rr.inputs["Value"]); rr.inputs["To Min"].default_value = rough
    rr.inputs["To Max"].default_value = 0.8; L.new(rr.outputs[0], b.inputs["Roughness"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.002
    L.new(P.math_n(N, L, "SUBTRACT", 1.0, br.outputs["Fac"]), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = 0.4
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
    l.visible_camera = cam_vis
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, const=True, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)

def child_of_bone(name, arm, bone):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    return e

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value

def catmull(pts, step=0.004):
    P_ = [Vector(p) for p in pts]; P_ = [P_[0] * 2 - P_[1]] + P_ + [P_[-1] * 2 - P_[-2]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n = max(2, int((p2 - p1).length / step))
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P_[-2])
    return out

def along(pts, t):
    """egri chiziq (zich nuqtalar) bo'ylab 0..1 parametr -> nuqta (uzunlik bo'yicha)"""
    t = min(1.0, max(0.0, t))
    L_ = [0.0]
    for a, b in zip(pts, pts[1:]): L_.append(L_[-1] + (b - a).length)
    s = t * L_[-1]
    for i in range(len(pts) - 1):
        if L_[i + 1] >= s:
            u = (s - L_[i]) / max(1e-9, L_[i + 1] - L_[i]); return pts[i].lerp(pts[i + 1], u)
    return pts[-1].copy()

def pq(o, f, rot):
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Euler([R(a) for a in rot]).to_quaternion(); o.keyframe_insert("rotation_quaternion", frame=f)

def emit_alpha_mat(name, col, strength, alpha_name="a", alpha=1.0, extra=None):
    """emissiya + shaffoflik (alpha qiymati kalitlanadi)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); out = N["Material Output"]
    a = value_node(m, alpha_name, alpha); g = value_node(m, "glow", strength)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); L.new(g, em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    fac = a if extra is None else P.math_n(N, L, "MULTIPLY", a, extra(N, L))
    L.new(fac, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m

# ======================================================================
# 1) HAMMOM (dunyo markazi). Megan (0,0,0) da, -Y tomonga (oynaga) qaraydi.
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
X0, X1, Y0, Y1, HZ_ = -1.4, 1.4, -0.85, 1.7, 2.5
floor_m = tiles("floor_tile", (0.34, 0.33, 0.32), (0.18, 0.18, 0.18), scale=3.4, rough=0.25)
wall_t = tiles("wall_tile", (0.86, 0.9, 0.9), (0.62, 0.64, 0.64), scale=7.0, rough=0.06)
wall_p = pbr("wall_paint", "painted_plaster_wall", 0.6, tint=(0.58, 0.72, 0.74))
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
TZ = 1.25                                                     # plitka balandligi
for nm, sz, loc in (("wF", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y0 - 0.05, HZ_ / 2)), ("wB", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y1 + 0.05, HZ_ / 2)),
                    ("wL", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, (Y0 + Y1) / 2, HZ_ / 2)), ("wR", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2))):
    R_(box(nm + "_p", sz, loc, wall_p))
    s2 = list(sz); s2[2] = TZ; l2 = list(loc); l2[2] = TZ / 2
    if nm in ("wF", "wB"): s2[1] = 0.12
    else: s2[0] = 0.12
    R_(box(nm + "_t", s2, l2, wall_t))
R_(box("tile_cap", (X1 - X0, 0.03, 0.03), (0, Y0 + 0.02, TZ + 0.015), mat("cap", (0.92, 0.92, 0.9), 0.2)))
# lavabo stoli (vanity)
VY = -0.6                                                     # stol old qirrasi y = -0.35
wood_m = mat("vanity_wood", (0.3, 0.2, 0.13), 0.4, coat=0.3)
R_(box("vanity", (1.1, 0.5, 0.78), (0, VY, 0.39), wood_m, bevel=0.008))
for dx in (-0.27, 0.27):
    R_(box(f"door{dx}", (0.5, 0.01, 0.62), (dx, VY + 0.255, 0.4), mat("door_m", (0.36, 0.25, 0.17), 0.35, coat=0.4), bevel=0.004))
    R_(cyl(f"knob{dx}", 0.008, 0.03, (dx + (0.18 if dx < 0 else -0.18), VY + 0.27, 0.6), mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0), rot=(90, 0, 0)))
marble = bpy.data.materials.new("marble"); marble.use_nodes = True
N = marble.node_tree.nodes; L = marble.node_tree.links; b = N["Principled BSDF"]
tcm = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 2.0; wv.inputs["Distortion"].default_value = 14
wv.inputs["Detail"].default_value = 6; L.new(tcm.outputs["Object"], wv.inputs["Vector"])
crm = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], crm.inputs[0])
crm.color_ramp.elements[0].color = (0.93, 0.93, 0.92, 1); crm.color_ramp.elements[1].color = (0.7, 0.7, 0.72, 1)
crm.color_ramp.elements[0].position = 0.6; L.new(crm.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.08
b.inputs["Coat Weight"].default_value = 0.6
R_(box("counter", (1.16, 0.54, 0.04), (0, VY, 0.8), marble, bevel=0.004))
basin_m = mat("basin", (0.95, 0.95, 0.94), 0.06, coat=0.8)
basin = R_(sphere("basin", 0.2, (0, VY - 0.02, 0.86), basin_m, scale=(1.0, 0.75, 0.3), sub=4))
R_(cyl("faucet", 0.012, 0.22, (0, VY - 0.22, 0.93), mat("chrome2", (0.92, 0.92, 0.94), 0.05, metal=1.0)))
R_(cyl("spout", 0.01, 0.12, (0, VY - 0.17, 1.03), bpy.data.materials["chrome2"], rot=(90, 0, 0)))
# oyna
MIR_Z0, MIR_Z1 = 1.1, 1.95
mirror_m = mat("mirror", (0.92, 0.93, 0.95), 0.015, metal=1.0)
R_(box("mirror", (0.84, 0.01, MIR_Z1 - MIR_Z0), (0, Y0 + 0.012, (MIR_Z0 + MIR_Z1) / 2), mirror_m))
R_(box("mirror_frame", (0.9, 0.012, MIR_Z1 - MIR_Z0 + 0.06), (0, Y0 + 0.005, (MIR_Z0 + MIR_Z1) / 2), mat("mframe", (0.05, 0.05, 0.05), 0.3)))
bar_m = mat("vanity_bar", (1, 0.9, 0.75), 0.3, emit=12.0, emit_col=(1.0, 0.82, 0.6))
R_(box("light_bar", (0.7, 0.05, 0.05), (0, Y0 + 0.05, MIR_Z1 + 0.09), bar_m, bevel=0.01))
# stol ustidagi narsalar: sovun, shishalar, tish cho'tkasi stakani
bot_m = [mat("bot_a", (0.2, 0.55, 0.75), 0.15, coat=0.8), mat("bot_b", (0.95, 0.85, 0.75), 0.25, coat=0.5), mat("bot_c", (0.85, 0.3, 0.45), 0.2, coat=0.7)]
for i, (x, y, r, h) in enumerate([(0.38, VY - 0.12, 0.03, 0.17), (0.45, VY - 0.05, 0.025, 0.12), (-0.4, VY - 0.1, 0.035, 0.1)]):
    R_(cyl(f"bottle{i}", r, h, (x, y, 0.82 + h / 2), bot_m[i]))
    R_(cyl(f"cap{i}", r * 0.45, 0.03, (x, y, 0.82 + h + 0.015), mat(f"capm{i}", (0.1, 0.1, 0.1), 0.3)))
R_(cyl("cup", 0.035, 0.1, (-0.3, VY - 0.16, 0.87), mat("cup_m", (0.7, 0.85, 0.9), 0.05, trans=0.8)))
for k, c_ in enumerate(((0.9, 0.2, 0.2), (0.2, 0.5, 0.9))):
    R_(cyl(f"brush{k}", 0.005, 0.19, (-0.3 + 0.012 * (k - 0.5), VY - 0.16, 0.96), mat(f"brm{k}", c_, 0.3), rot=(8 * (k - 0.5) * 2, 0, 0)))
# sochiq ilgichi + sochiq, o'simlik
R_(cyl("towel_bar", 0.01, 0.6, (X1 - 0.04, 0.2, 1.2), bpy.data.materials["chrome2"], rot=(90, 0, 0)))
towel = R_(box("towel", (0.03, 0.45, 0.55), (X1 - 0.06, 0.2, 0.95), mat("towel_m", (0.85, 0.55, 0.45), 0.95), bevel=0.012))
noisy(towel, 0.01, 0.1)
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (X0 + 0.3, Y1 - 0.35, 0), 30, 0.8))
R_(box("bathmat", (0.7, 0.45, 0.012), (0, 0.05, 0.006), mat("bathmat_m", (0.25, 0.35, 0.45), 0.95), bevel=0.005))

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
MEG = Vector((0.0, 0.0, 0.0))
mroot.location = MEG
def strip(act, start, repeat=1.0, speed=1.0, blend=0, src=None):
    s = mc.add_strip(meg, act, start, repeat=repeat, speed=speed, blend=blend, hold=False, src=src)
    s.blend_out = 0; s.use_auto_blend = False
    return s
AG0 = S["agony"][0]
strip(A_("Breathing_Idle.fbx"), -20, repeat=(AG0 + 30) / 239.0)
strip(A_("Agony.fbx"), AG0 - 8, blend=6)
DEATH_START = int(os.environ.get("DEATH_START", 896))
strip(A_("Death.fbx", inplace=False), DEATH_START, blend=6).extrapolation = "HOLD_FORWARD"
# oynaga engashish (COMBINE): umurtqa oldinga, bosh biroz ko'tarilgan
BB = {n: meg.pose.bones["mixamorig:" + n] for n in ("Spine1", "Spine2", "Neck", "Head")}
LEAN = float(os.environ.get("LEAN", 1.0))
def bend(f, sp, nk, hd):
    pq(BB["Spine1"], f, (LEAN * sp * 0.5, 0, 0)); pq(BB["Spine2"], f, (LEAN * sp * 0.5, 0, 0))
    pq(BB["Neck"], f, (LEAN * nk, 0, 0)); pq(BB["Head"], f, (LEAN * hd, 0, 0))
bend(1, 14, 6, -6); bend(S["press"][1], 14, 6, -6); bend(AG0 - 4, 0, 0, 0)
ov = meg.animation_data.action; ov.name = "lean_overlay"; ov.use_fake_user = True
meg.animation_data.action = None
_tr = meg.animation_data.nla_tracks.new(); _tr.name = "lean_overlay"
_st = _tr.strips.new("lean_overlay", 1, ov)
if hasattr(_st, "action_slot") and ov.slots: _st.action_slot = ov.slots[0]
_st.blend_type = "COMBINE"; _st.extrapolation = "HOLD"; _st.blend_in = _st.blend_out = 0

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.065, 0.13), headE)          # yuz markazi (Head fazosi: X chap, Y tepa, Z old)
body = next(o for o in mmeshes if o.name.endswith("Body"))

# ---- yuz sirti (Head fazosida) — uchburchak va husnbuzarni sirtga yopishtirish uchun ----
F_SNAP = 30
sc.frame_set(F_SNAP); bpy.context.view_layer.update()
Hinv = headE.matrix_world.inverted()
_dg = bpy.context.evaluated_depsgraph_get(); _ev = body.evaluated_get(_dg); _me = _ev.to_mesh()
_vs = [Hinv @ (body.matrix_world @ v.co) for v in _me.vertices]
_bvh = BVHTree.FromPolygons(_vs, [tuple(p.vertices) for p in _me.polygons])
_ev.to_mesh_clear()
def snap(x, y):
    hit, nrm, _, _ = _bvh.ray_cast(Vector((x, y, 0.4)), Vector((0, 0, -1)))
    if hit is None: return Vector((x, y, 0.14)), Vector((0, 0, 1))
    if nrm.z < 0: nrm = -nrm
    return hit, nrm.normalized()
def HW(local, f):
    sc.frame_set(f); bpy.context.view_layer.update()
    return headE.matrix_world @ Vector(local)

# ---- uchburchak: chiziq (chiziladi) + qizil to'ldirish ----
TA, TB, TC = (0.0, 0.097), (-0.024, 0.028), (0.024, 0.028)
def edge(a, b, n=40):
    out = []
    for i in range(n):
        t = i / n; x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
        h, nr = snap(x, y); out.append(h + nr * 0.0013)
    return out
loop = edge(TA, TB) + edge(TB, TC, 30) + edge(TC, TA) + [snap(*TA)[0] + snap(*TA)[1] * 0.0013]
def line_extra(N, L):
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    rv = N.new("ShaderNodeValue"); rv.name = "reveal"; rv.outputs[0].default_value = 0.0
    return P.math_n(N, L, "LESS_THAN", ua.outputs["Fac"], rv.outputs[0])
line_m = emit_alpha_mat("tri_line", (1.0, 0.06, 0.02), 14.0, extra=line_extra)
tri_line = P.tube("tri_line", [tuple(p) for p in loop], 0.0007, line_m, headE)
tri_line.data.splines[0].use_endpoint_u = True
# to'ldirish: baritsentrik to'r, sirtga yopishtirilgan
NF = 26; fv = []; fidx = {}
for i in range(NF + 1):
    for j in range(NF + 1 - i):
        a_ = i / NF; b_ = j / NF; c_ = 1 - a_ - b_
        x = TA[0] * c_ + TB[0] * a_ + TC[0] * b_; y = TA[1] * c_ + TB[1] * a_ + TC[1] * b_
        h, nr = snap(x, y); fidx[(i, j)] = len(fv); fv.append(tuple(h + nr * 0.0007))
ff = []
for i in range(NF):
    for j in range(NF - i):
        ff.append((fidx[(i, j)], fidx[(i + 1, j)], fidx[(i, j + 1)]))
        if (i + 1, j + 1) in fidx: ff.append((fidx[(i + 1, j)], fidx[(i + 1, j + 1)], fidx[(i, j + 1)]))
_fme = bpy.data.meshes.new("tri_fill"); _fme.from_pydata(fv, [], ff); _fme.update()
tri_fill = bpy.data.objects.new("tri_fill", _fme); sc.collection.objects.link(tri_fill); tri_fill.parent = headE
for p in _fme.polygons: p.use_smooth = True
fill_m = emit_alpha_mat("tri_fill_m", (1.0, 0.02, 0.01), 2.0, alpha=0.0)
_fme.materials.append(fill_m)
T0_, T1_ = TRI_DRAW
val_key(line_m, "reveal", 1, 0.0); val_key(line_m, "reveal", T0_, 0.0); val_key(line_m, "reveal", T1_, 1.02)
val_key(fill_m, "a", 1, 0.0); val_key(fill_m, "a", T1_ - 8, 0.0); val_key(fill_m, "a", T1_ + 4, 0.16)
D0, D1 = S["death"]
for f in range(D0, D1, 10):                                   # "o'lim uchburchagi": qizil puls
    val_key(fill_m, "a", f, 0.34); val_key(fill_m, "glow", f, 6.0); val_key(line_m, "glow", f, 40.0)
    val_key(fill_m, "a", f + 6, 0.18); val_key(fill_m, "glow", f + 6, 2.0); val_key(line_m, "glow", f + 6, 14.0)
val_key(fill_m, "a", D1, 0.16); val_key(fill_m, "a", S["xveins"][0], 0.07)
interp(line_m.node_tree, "LINEAR")
TRI_ON = rng("tri", "wide", "death") + [(S["xveins"][0], S["xveins"][1])]
vis(tri_line, TRI_ON, recursive=False); vis(tri_fill, TRI_ON, recursive=False)

# ---- husnbuzar (o'ng burun qanoti yonida) ----
PIMP, PN = snap(-0.0175, 0.05)
pim_red = mat("pimple_red", (0.55, 0.08, 0.06), 0.35, sss=0.6, sss_scale=0.002, coat=0.4)
pim_head = mat("pimple_head", (0.92, 0.82, 0.45), 0.25, sss=0.5, sss_scale=0.001, coat=0.8)
pus_m = mat("pus", (0.93, 0.85, 0.45), 0.15, sss=0.7, sss_scale=0.002, coat=1.0)
q = Vector((0, 0, 1)).rotation_difference(PN)
pimE = empty("pimE", tuple(PIMP), headE); pimE.rotation_mode = "QUATERNION"; pimE.rotation_quaternion = q
bump = sphere("pimple", 0.0042, (0, 0, -0.0002), pim_red, scale=(1, 1, 0.5), sub=4, parent=pimE)
whead = sphere("pimple_head", 0.0015, (0, 0, 0.0015), pim_head, scale=(1, 1, 0.75), sub=3, parent=pimE)
blush = sphere("pimple_blush", 0.0068, (0, 0, -0.0028), mat("blush", (0.72, 0.2, 0.18), 0.45, sss=0.8, sss_scale=0.003), scale=(1, 1, 0.45), sub=4, parent=pimE)
drop = sphere("pus_drop", 0.0014, (0, 0, 0.0016), pus_m, scale=(1, 1, 0.8), sub=3, parent=pimE)
key(drop, 1, scale=0.001); key(drop, POP_F - 1, scale=0.001); key(drop, POP_F + 2, scale=(1.3, 1.3, 1.0)); key(drop, POP_F + 10, scale=(1.6, 1.6, 1.1))
key(whead, 1, scale=(1, 1, 0.75)); key(whead, POP_F - 4, scale=(1.15, 1.15, 1.0)); key(whead, POP_F, scale=0.001)
key(bump, 1, scale=(1, 1, 0.5)); key(bump, S["fingers"][1], scale=(1, 1, 0.5)); key(bump, POP_F - 3, scale=(0.85, 0.85, 0.7))
key(bump, POP_F + 1, scale=(1.05, 1.05, 0.35))
key(blush, 1, scale=(1, 1, 0.45)); key(blush, S["press"][0], scale=(1, 1, 0.45)); key(blush, S["press"][1], scale=(1.5, 1.5, 0.5))
PIM_ON = [(1, S["squeeze"][1]), S["press"]]
for o in (bump, whead, blush, drop): vis(o, PIM_ON, recursive=False)

# ---- procedural barmoq uchlari (makro kadrlar uchun) ----
skin_f = P.skin_material("finger_skin", base=(0.86, 0.62, 0.52), prints=True)
def finger_rig(name, tip, d, nail, r=0.0068):
    d = Vector(d).normalized(); z = (Vector(nail) - d * Vector(nail).dot(d)).normalized(); x = d.cross(z)
    M = Matrix((x, d, z)).transposed().to_4x4()
    e = empty(name, tuple(tip), headE); e.rotation_mode = "QUATERNION"; e.rotation_quaternion = M.to_quaternion()
    fo = P.build_finger(name + "_f", parent=e, r=r, length=0.085, skin=skin_f, knuckle=True)
    return e, fo
TA_L = PIMP + PN * 0.002 + Vector((-0.0105, -0.002, 0.0))
TB_L = PIMP + PN * 0.002 + Vector((0.0075, 0.0075, 0.002))
fA, fAo = finger_rig("fingerA", TA_L, (-0.45, -0.55, 0.7), (-1.0, 0.0, 0.25))
fB, fBo = finger_rig("fingerB", TB_L, (0.35, -0.5, 0.8), (0.7, 0.6, 0.25))
FI0, FI1 = S["fingers"]; PR0, PR1 = S["press"]
for e, tip, dd in ((fA, TA_L, Vector((-0.45, -0.55, 0.7)).normalized()), (fB, TB_L, Vector((0.35, -0.5, 0.8)).normalized())):
    toward = (PIMP - tip); toward.z = 0; toward = toward.normalized()
    key(e, FI0, loc=tuple(tip + dd * 0.05)); key(e, FI1 - 14, loc=tuple(tip + dd * 0.004)); key(e, FI1, loc=tuple(tip + toward * 0.0015))
    key(e, PR0, loc=tuple(tip + toward * 0.0015)); key(e, PR0 + 18, loc=tuple(tip + toward * 0.0035 - PN * 0.0015))
    key(e, PR1, loc=tuple(tip + toward * 0.0042 - PN * 0.002))
for o in (fA, fB): vis(o, rng("fingers", "press"))

# ---- haqiqiy qo'llar: IK (siqish kadri) ----
def arm_ik(side):
    tgt = empty(f"meg_{side}_ik")
    c = meg.pose.bones[f"mixamorig:{side}ForeArm"].constraints.new("IK")
    c.target = tgt; c.use_tail = True; c.chain_count = 2; c.influence = 0.0
    return tgt, c
def key_inf(cs, pairs):
    for c in cs:
        for f, v in pairs: c.influence = v; c.keyframe_insert("influence", frame=f)
HX = float(os.environ.get("HX", 1.0))
wR = empty("wristR", tuple(PIMP + Vector((-0.06 * HX, -0.085, 0.1))), headE)
wL = empty("wristL", tuple(PIMP + Vector((0.045 * HX, -0.08, 0.11))), headE)
aimR_ = empty("aimR", tuple(PIMP + Vector((-0.004, 0.0, 0.0))), headE); aimL_ = empty("aimL", tuple(PIMP + Vector((0.006, 0.006, 0.0))), headE)
palmC = empty("palmC", (0, 0.03, -0.02), headE)
RT_, RIK = arm_ik("Right"); LT_, LIK = arm_ik("Left")
for t_, w_ in ((RT_, wR), (LT_, wL)):
    c = t_.constraints.new("COPY_LOCATION"); c.target = w_
hcons = []
for side, aim in (("Right", aimR_), ("Left", aimL_)):
    hb = meg.pose.bones[f"mixamorig:{side}Hand"]
    d = hb.constraints.new("DAMPED_TRACK"); d.target = aim; d.track_axis = "TRACK_Y"; d.influence = 0.0
    l = hb.constraints.new("LOCKED_TRACK"); l.target = palmC; l.track_axis = "TRACK_Z" if side == "Right" else "TRACK_NEGATIVE_Z"
    l.lock_axis = "LOCK_Y"; l.influence = 0.0
    hcons += [d, l]
SQ0, SQ1 = S["squeeze"]
key_inf([RIK, LIK] + hcons, [(1, 0.0), (SQ0 - 12, 0.0), (SQ0 - 2, 1.0), (SQ1, 1.0), (SQ1 + 1, 0.0)])
# ko'rsatkich barmoqni to'g'rilash (qolganlari bukilgan) — faqat IK paytida
for side in ("Right", "Left"):
    for k in (1, 2, 3):
        bn = f"mixamorig:{side}HandIndex{k}"
        if bn in meg.pose.bones:
            c = meg.pose.bones[bn].constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            key_inf([c], [(1, 0.0), (SQ0 - 12, 0.0), (SQ0 - 2, 1.0), (SQ1, 1.0), (SQ1 + 1, 0.0)])

# ---- rentgen nusxasi ----
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.3, base=0.012)
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, XH, recursive=False)
for o in mmeshes: vis(o, ROOM, recursive=False)
for o in room_objs: vis(o, ROOM)

# ======================================================================
# 3) RENTGEN: miya, yuz venalari, kavernoz sinus (Head fazosi)
# ======================================================================
xbrain, xbm = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.112, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
bm_n = xbm.node_tree.nodes; bm_b = bm_n["Principled BSDF"]
# miya: 50% shaffof (sinus va venalar ko'rinsin)
_tr = bm_n.new("ShaderNodeBsdfTransparent"); _mx = bm_n.new("ShaderNodeMixShader"); _mx.inputs[0].default_value = 0.45
_out = bm_n["Material Output"]; xbm.node_tree.links.new(bm_b.outputs[0], _mx.inputs[1]); xbm.node_tree.links.new(_tr.outputs[0], _mx.inputs[2])
xbm.node_tree.links.new(_mx.outputs[0], _out.inputs["Surface"])
val_key(xbm, "glow", 1, 0.25)
XF0, XF1 = S["xflow"]
val_key(xbm, "glow", XF1 - 20, 0.25); val_key(xbm, "glow", XF1, 2.5)
vis(xbrain, XH)
# yuz venasi: jag' -> og'iz burchagi -> husnbuzar ostidan -> ko'z ichki burchagi -> ko'z kosasi -> sinus
VPTS = [(-0.058, -0.035, 0.07), (-0.046, 0.0, 0.112), (-0.033, 0.024, 0.134), (-0.022, 0.047, 0.142), (-0.016, 0.071, 0.142),
        (-0.014, 0.09, 0.134), (-0.02, 0.1, 0.118), (-0.023, 0.097, 0.095), (-0.019, 0.089, 0.075), (-0.014, 0.083, 0.058)]
VDENSE = catmull(VPTS, 0.002)
SIN_C = Vector((0.0, 0.083, 0.05))
vein_m = P.pulse_material("vein_m", (0.12, 0.25, 0.9), base_emit=1.2, pulse_col=(1.0, 0.15, 0.08), width=0.08)
vein_g = mat("vein_side", (0.15, 0.25, 0.85), 0.35, emit=1.0, emit_col=(0.2, 0.45, 1.0))
veinR = P.tube("veinR", [tuple(p) for p in VPTS], 0.0021, vein_m, headE, taper=[0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.3])
veinL = P.tube("veinL", [(-p[0], p[1], p[2]) for p in VPTS], 0.0021, vein_m, headE, taper=[0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.3])
# mayda shoxchalar (uchburchak ichida)
rb = random.Random(4)
for sgn in (-1, 1):
    for k, (a, b) in enumerate((((-0.03, 0.03, 0.14), (-0.012, 0.022, 0.15)), ((-0.022, 0.06, 0.145), (-0.008, 0.07, 0.155)),
                                ((-0.026, 0.04, 0.142), (-0.04, 0.05, 0.13)), ((-0.017, 0.08, 0.14), (-0.006, 0.088, 0.15)))):
        a = Vector((a[0] * -sgn, a[1], a[2])); b = Vector((b[0] * -sgn, b[1], b[2]))
        mid = (a + b) / 2 + Vector((rb.uniform(-0.003, 0.003), rb.uniform(-0.003, 0.003), 0.002))
        P.tube(f"vbr{sgn}_{k}", [tuple(a), tuple(mid), tuple(b)], 0.0011, vein_m, headE, taper=[1.0, 0.8, 0.5])
# kavernoz sinus (ikki tomonda, ko'ndalang ulangan)
sin_m = bpy.data.materials.new("sinus"); sin_m.use_nodes = True
N = sin_m.node_tree.nodes; L = sin_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.35, 0.1, 0.6, 1); b.inputs["Roughness"].default_value = 0.3
b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.002; b.inputs["Coat Weight"].default_value = 0.6
sg = value_node(sin_m, "glow", 1.5); inf = value_node(sin_m, "inf", 0.0)
nzs = N.new("ShaderNodeTexNoise"); nzs.inputs["Scale"].default_value = 600; tcs = N.new("ShaderNodeTexCoord"); L.new(tcs.outputs["Object"], nzs.inputs[0])
ecs = N.new("ShaderNodeMix"); ecs.data_type = "RGBA"; ecs.inputs[6].default_value = (0.55, 0.25, 1.0, 1); ecs.inputs[7].default_value = (0.4, 1.0, 0.15, 1)
L.new(inf, ecs.inputs["Factor"]); L.new(ecs.outputs[2], b.inputs["Emission Color"])
L.new(P.math_n(N, L, "MULTIPLY", sg, P.math_n(N, L, "ADD", 0.4, nzs.outputs["Fac"])), b.inputs["Emission Strength"])
sinus = empty("sinus", tuple(SIN_C), headE)
for sx in (-1, 1):
    s_ = sphere(f"sinus{sx}", 0.0065, (sx * 0.0135, 0, 0), sin_m, scale=(0.9, 0.85, 2.3), sub=4, parent=sinus); noisy(s_, 0.0015, 0.004)
P.tube("sinus_x", [(-0.013, 0.0, 0.012), (0, -0.002, 0.014), (0.013, 0.0, 0.012)], 0.0022, sin_m, sinus)
P.tube("sinus_x2", [(-0.013, 0.0, -0.012), (0, -0.003, -0.014), (0.013, 0.0, -0.012)], 0.0022, sin_m, sinus)
XV0, XV1 = S["xveins"]; XS0, XS1 = S["xsinus"]
# venadagi puls: 'pos' 0..1 (jag'dan sinusga)
f = XV0 - 10
while f < XS1 + 30:
    val_key(vein_m, "pos", f, -0.15); val_key(vein_m, "pos", f + 34, 1.15); f += 26
for fc in mc._fcurves(vein_m.node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
val_key(vein_m, "glow", 1, 1.0); val_key(vein_m, "glow", XV0 + 10, 1.0); val_key(vein_m, "glow", XV0 + 30, 2.6)
val_key(sin_m, "glow", 1, 1.0); val_key(sin_m, "glow", XS0 + 30, 1.0); val_key(sin_m, "glow", XS0 + 50, 5.0); val_key(sin_m, "glow", XS1, 3.5)
val_key(sin_m, "inf", 1, 0.0); val_key(sin_m, "inf", XF0 + 20, 0.0); val_key(sin_m, "inf", XF1, 1.0)
val_key(sin_m, "glow", XF0, 3.0); val_key(sin_m, "glow", XF1, 9.0)
XPARTS = [veinR, veinL, sinus] + [o for o in bpy.data.objects if o.name.startswith("vbr")]
for o in XPARTS: vis(o, XH)
# bakteriyalar oqimi (husnbuzardan sinusga)
bact_m = mat("bact", (0.3, 0.9, 0.15), 0.3, emit=6.0, emit_col=(0.45, 1.0, 0.2), sss=0.4, sss_scale=0.001)
i_p = min(range(len(VDENSE)), key=lambda i: (VDENSE[i] - Vector(PIMP)).length)
VUP = VDENSE[i_p:]
rbac = random.Random(9); bacts = []
for k in range(26):
    o = sphere(f"bx{k}", rbac.uniform(0.0007, 0.0013), (0, 0, 0), bact_m, scale=(1.0, 1.0, 1.6), sub=2, parent=headE)
    f0 = XF0 - 6 + k * 2; dur = 34 + rbac.randint(0, 8); off = Vector((rbac.uniform(-1, 1), rbac.uniform(-1, 1), rbac.uniform(-1, 1))) * 0.0008
    for j in range(0, dur + 1, 2):
        t = ease(j / dur); p = along(VUP, t) + off
        if j == dur: p = SIN_C + Vector((-0.0135, 0, 0)) + off * 4
        key(o, f0 + j, loc=tuple(p))
    interp(o, "LINEAR")
    vis(o, [(max(XF0, f0), XF1)], recursive=False); bacts.append(o)

# ======================================================================
# 4) TOMIR ICHI (klapan, tromb) — VS va VC studiyalari
# ======================================================================
def vein_wall_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.55, 0.06, 0.08, 1); b.inputs["Roughness"].default_value = 0.25
    b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 0.8; b.inputs["Coat Roughness"].default_value = 0.05
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs[0])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    # mayda kapillyarlar (emissiya)
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 3.0; L.new(tc.outputs["Object"], vo.inputs[0])
    ln = P.math_n(N, L, "LESS_THAN", vo.outputs["Distance"], 0.02)
    b.inputs["Emission Color"].default_value = (1.0, 0.15, 0.1, 1); L.new(P.math_n(N, L, "MULTIPLY", ln, 1.5), b.inputs["Emission Strength"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.5), 0.95), 0.06, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m
wall_vm = vein_wall_mat("vein_wall")
rbc_m = mat("rbc", (0.7, 0.03, 0.04), 0.3, sss=0.7, sss_scale=0.05, coat=0.5)
def rbc_mesh():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    o = bpy.context.object; me = o.data
    for v in me.vertices:                                       # bikonkav disk
        rr = math.hypot(v.co.x, v.co.y)
        v.co.z *= 0.32 * (0.35 + 0.65 * rr ** 2) / 0.9 + 0.08
    for p in me.polygons: p.use_smooth = True
    me.materials.append(rbc_m); me.name = "rbc_me"
    bpy.data.objects.remove(o, do_unlink=True)
    return me
RBC = rbc_mesh()
def cell(name, parent, r=0.12):
    o = bpy.data.objects.new(name, RBC); sc.collection.objects.link(o); o.parent = parent; o.scale = (r, r, r); return o

def build_vein(name, C, rad=0.5, length=14.0):
    g = empty(name, tuple(C))
    P.tube(name + "_wall", [(-length / 2, 0, 0), (-length / 4, 0, 0.05), (0, 0, 0), (length / 4, 0, -0.05), (length / 2, 0, 0)], rad, wall_vm, g)
    return g

def flow_x(x0, f0, f, segs):
    """segs: [(kadr, tezlik)] — bo'lakli tezlik bo'yicha integrallangan x"""
    x = x0; prev_f, prev_v = f0, segs[0][1]
    for fs, v in segs[1:]:
        if f <= fs: return x + prev_v * (f - prev_f)
        x += prev_v * (fs - prev_f); prev_f, prev_v = fs, v
    return x + prev_v * (f - prev_f)

# ---- VS: klapan kadri ----
VS = Vector((40, 0, 0))
vs = build_vein("VS_grp", VS)
VA0, VA1 = S["valve"]
valve_m = mat("valve", (0.95, 0.55, 0.55), 0.35, sss=0.8, sss_scale=0.05, coat=0.6, alpha=1.0)
flaps = []
for sz in (-1, 1):                                              # ikki qopqoq (yuqori va pastki devordan, +X ga qaragan)
    fe = empty(f"flapE{sz}", (0.0, 0, sz * 0.48), vs)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    fl = bpy.context.object; fl.name = f"flap{sz}"; fl.scale = (0.42, 0.46, 0.05); bpy.ops.object.transform_apply(scale=True)
    for v in fl.data.vertices:
        if v.co.x < 0: v.co.x *= 0.3
        v.co.z += -sz * 0.0 + (-sz) * 0.35 * max(0.0, v.co.x) * 1.0
    fl.data.materials.append(valve_m); fl.parent = fe; fl.location = (0.32, 0, -sz * 0.0)
    for p in fl.data.polygons: p.use_smooth = True
    fe.rotation_euler = (0, R(sz * 28), 0)
    flaps.append(fe)
for fe in flaps:
    key(fe, 1, scale=1.0); key(fe, VALVE_F - 2, scale=1.0); key(fe, VALVE_F + 12, scale=0.0)
    sz = 1 if fe.name.endswith("1") else -1
    for f in range(VA0, VALVE_F, 6):
        fe.rotation_euler = (0, R(sz * (28 + 8 * math.sin(f * 0.4))), 0); fe.keyframe_insert("rotation_euler", frame=f)
rv = random.Random(31); vcells = []
SEG_V = [(VA0, 0.055), (VALVE_F + 6, 0.055), (NOVALVE_F - 4, 0.0), (NOVALVE_F + 4, -0.06), (VA1 + 2, -0.075)]
for k in range(150):
    o = cell(f"vc{k}", vs, rv.uniform(0.09, 0.13)); vcells.append(o)
    x0 = rv.uniform(-11, 3); y = rv.uniform(-0.33, 0.33); z = rv.uniform(-0.33, 0.33)
    if y * y + z * z > 0.36 * 0.36: y *= 0.7; z *= 0.7
    rr = Vector((rv.uniform(0, 6), rv.uniform(0, 6), rv.uniform(0, 6))); dr = Vector((rv.uniform(-0.05, 0.05), rv.uniform(-0.05, 0.05), rv.uniform(-0.05, 0.05)))
    for f in range(VA0 - 2, VA1 + 3, 2):
        x = flow_x(x0, VA0, f, SEG_V)
        o.location = (x, y + 0.03 * math.sin(f * 0.1 + k), z + 0.03 * math.cos(f * 0.13 + k)); o.keyframe_insert("location", frame=f)
        o.rotation_euler = tuple(rr + dr * (f - VA0)); o.keyframe_insert("rotation_euler", frame=f)
    interp(o, "LINEAR")
vis(vs, rng("valve"))

# ---- VC: tromb kadri ----
VC = Vector((40, 10, 0))
vc = build_vein("VC_grp", VC, rad=0.55)
CL0, CL1 = S["clot"]
clot_m = bpy.data.materials.new("clot"); clot_m.use_nodes = True
N = clot_m.node_tree.nodes; L = clot_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.18, 0.01, 0.015, 1); b.inputs["Roughness"].default_value = 0.55
b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.3
tcc = N.new("ShaderNodeTexCoord"); vcn = N.new("ShaderNodeTexVoronoi"); vcn.inputs["Scale"].default_value = 9; L.new(tcc.outputs["Object"], vcn.inputs[0])
bpc = N.new("ShaderNodeBump"); bpc.inputs["Strength"].default_value = 0.9; L.new(vcn.outputs["Distance"], bpc.inputs["Height"]); L.new(bpc.outputs[0], b.inputs["Normal"])
clot = sphere("clot", 0.5, (0.6, 0, 0), clot_m, scale=(0.9, 1, 1), sub=5, parent=vc); noisy(clot, 0.18, 0.25)
key(clot, 1, scale=0.05); key(clot, CL0, scale=(0.1, 0.12, 0.12)); key(clot, CL0 + 34, scale=(0.6, 0.75, 0.75)); key(clot, CL1, scale=(0.95, 1.02, 1.02))
fib_m = mat("fibrin", (0.95, 0.85, 0.6), 0.4, sss=0.5, sss_scale=0.05)
rf = random.Random(17)
fibs = empty("fibs", (0.6, 0, 0), vc)
for k in range(40):
    a = Vector((rf.uniform(-1, 1), rf.uniform(-1, 1), rf.uniform(-1, 1))).normalized() * rf.uniform(0.1, 0.4)
    b_ = Vector((rf.uniform(-1, 1), rf.uniform(-1, 1), rf.uniform(-1, 1))).normalized() * rf.uniform(0.3, 0.55)
    P.tube(f"fib{k}", [tuple(a), tuple((a + b_) / 2 + Vector((0, 0, rf.uniform(-0.1, 0.1)))), tuple(b_)], 0.008, fib_m, fibs, taper=[1, 0.7, 0.4])
key(fibs, 1, scale=0.05); key(fibs, CL0, scale=0.15); key(fibs, CL1, scale=1.0)
# hujayralar oqib kelib trombga tiqiladi; bakteriyalar ichida yonadi
rc = random.Random(41)
for k in range(130):
    o = cell(f"cc{k}", vc, rc.uniform(0.09, 0.13))
    x0 = rc.uniform(-9.0, -0.4); y = rc.uniform(-0.35, 0.35); z = rc.uniform(-0.35, 0.35)
    stop = 0.6 - 0.45 - rc.uniform(0.0, 1.6) * (k / 130)
    rr = Vector((rc.uniform(0, 6), rc.uniform(0, 6), rc.uniform(0, 6)))
    for f in range(CL0 - 2, CL1 + 3, 2):
        x = min(x0 + 0.075 * (f - CL0), stop)
        o.location = (x, y, z); o.keyframe_insert("location", frame=f)
        o.rotation_euler = tuple(rr + Vector((0.02, 0.03, 0.01)) * (f - CL0) * (1 if x < stop else 0.2)); o.keyframe_insert("rotation_euler", frame=f)
    interp(o, "LINEAR")
for k in range(24):
    p = Vector((0.6, 0, 0)) + Vector((rc.uniform(-1, 1), rc.uniform(-1, 1), rc.uniform(-1, 1))).normalized() * rc.uniform(0.15, 0.45)
    o = sphere(f"cb{k}", rc.uniform(0.025, 0.04), tuple(p), bact_m, scale=(1, 1, 1.8), sub=2, parent=vc)
    o.rotation_euler = (rc.uniform(0, 3), rc.uniform(0, 3), 0)
    key(o, 1, scale=0.0); key(o, CL0 + 4 + k, scale=0.0); key(o, CL0 + 12 + k, scale=(1, 1, 1.8))
vis(vc, rng("clot"))

# ======================================================================
# 5) TERI KESIMI (SS)
# ======================================================================
SS = Vector((80, 0, 0))
sec, sparts, _smats = P.build_section("sec", tuple(SS), size=(2.6, 1.4))
SC0, SC1 = S["section"]
FR_ = SC0 + 18                       # sac yoriladi
sac_shell = mat("sac_shell", (0.7, 0.12, 0.1), 0.4, sss=0.6, sss_scale=0.05, emit=0.6, emit_col=(1.0, 0.2, 0.1))
pus2 = mat("pus2", (0.95, 0.85, 0.4), 0.2, sss=0.6, sss_scale=0.05, coat=0.8, emit=0.3, emit_col=(1.0, 0.85, 0.3))
SFY = -0.715                                          # kesim yuzi oldida (cutaway)
sacE = empty("sacE", (0, SFY, 0.72), sec)
shell = sphere("sac_shell", 0.24, (0, 0, 0), sac_shell, scale=(1.0, 0.08, 0.78), sub=4, parent=sacE)
core = sphere("sac_core", 0.19, (0, -0.012, 0), pus2, scale=(1.0, 0.08, 0.74), sub=4, parent=sacE)
noisy(core, 0.02, 0.05)
whit = sphere("sec_whitehead", 0.16, (0, -0.55, 1.0), pus2, scale=(1.0, 1.0, 0.45), sub=4, parent=sec)
redr = sphere("sec_redring", 0.34, (0, -0.55, 0.985), sac_shell, scale=(1.0, 1.0, 0.18), sub=4, parent=sec)
# vena (yog' qatlamida, kesim yuzida)
vsec_m = mat("vein_sec", (0.25, 0.08, 0.45), 0.3, sss=0.5, sss_scale=0.05, coat=0.6, emit=0.5, emit_col=(0.5, 0.2, 1.0))
vsec = P.tube("vein_sec", [(-1.35, SFY, 0.28), (-0.6, SFY, 0.32), (0.0, SFY, 0.3), (0.6, SFY, 0.27), (1.35, SFY, 0.3)], 0.11, vsec_m, sec)
# yoriq kanali: sac tubidan venagacha
chan = P.tube("sec_chan", [(0.0, SFY - 0.005, 0.56), (0.03, SFY - 0.005, 0.47), (-0.02, SFY - 0.005, 0.38)], 0.05, pus2, sec, taper=[1.0, 0.8, 1.0])
P.tube_r(chan, 1, 0.0); P.tube_r(chan, FR_, 0.0); P.tube_r(chan, FR_ + 8, 0.055)
key(sacE, 1, scale=1.0); key(sacE, SC0 + 4, scale=1.0); key(sacE, FR_, scale=(1.25, 1.0, 0.72)); key(sacE, SC1, scale=(1.3, 1.0, 0.55))
key(whit, 1, scale=(1.0, 1.0, 0.45)); key(whit, FR_, scale=(1.25, 1.25, 0.22))
# barmoqlar (katta masshtab) ustdan bosadi
sfx_skin = skin_f
fing = []
for sx in (-1, 1):
    e = empty(f"secF{sx}", (sx * 0.62, -0.3, 1.9), sec); e.scale = (28, 28, 28)
    e.rotation_euler = (R(90), R(sx * 25), 0)               # barmoq uchi pastga, tanasi tepaga-tashqariga
    P.build_finger(f"secF{sx}_f", parent=e, r=0.0072, length=0.08, skin=skin_f)
    key(e, SC0, loc=(sx * 0.75, -0.3, 1.7)); key(e, SC0 + 14, loc=(sx * 0.5, -0.3, 1.06)); key(e, SC1, loc=(sx * 0.44, -0.3, 1.0))
    fing.append(e)
# yiring va bakteriyalar: sac -> kanal -> vena -> chapga (miyaga)
rs_ = random.Random(23)
path_sec = [Vector((0, SFY - 0.03, 0.66)), Vector((0.02, SFY - 0.03, 0.5)), Vector((-0.02, SFY - 0.03, 0.36)), Vector((-0.3, SFY - 0.04, 0.31)),
            Vector((-0.8, SFY - 0.04, 0.3)), Vector((-1.4, SFY - 0.04, 0.28))]
psec = catmull(path_sec, 0.01)
for k in range(34):
    bac = k % 3 != 0
    o = sphere(f"sp{k}", rs_.uniform(0.022, 0.032) if bac else rs_.uniform(0.03, 0.05), (0, 0, 0), bact_m if bac else pus2,
               scale=(1, 1, 1.7) if bac else (1, 1, 1), sub=2, parent=sec)
    f0 = FR_ + 2 + k * 2; dur = 40 + rs_.randint(0, 10)
    off = Vector((rs_.uniform(-0.03, 0.03), -0.01, rs_.uniform(-0.03, 0.03)))
    key(o, 1, loc=tuple(psec[0] + off), scale=0.0); key(o, f0 - 1, loc=tuple(psec[0] + off), scale=0.0)
    for j in range(0, dur + 1, 2):
        key(o, f0 + j, loc=tuple(along(psec, ease(j / dur) * 0.75 + 0.25 * (j / dur)) + off), scale=1.0)
    interp(o, "LINEAR")
vis(sec, rng("section"))

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def at(name, p, parent=None): return empty(name, tuple(p), parent)
PI_ = Vector(PIMP)
# 1 ILGAK: yuzga tez push-in (o'ng-old tomondan, husnbuzar ko'rinadi)
H0, H1 = S["hook"]
hT = at("hookT", PI_ + Vector((0.01, 0.01, 0.0)), headE)
c = shot_cam("hook", (0, 0, 0), hT, 35, 2.0, focus=hT)
path_keys(c, [(H0, HW((-0.13, 0.07, 0.38), H0)), (H1, HW((-0.07, 0.06, 0.22), H1))])
lens_keys(c, [(H0, 32), (H1, 50)])
# 2 uchburchak: oldidan sekin aylanma
T0, T1 = S["tri"]
tT = at("triT", (0, 0.062, 0.14), headE)
c = shot_cam("tri", (0, 0, 0), tT, 42, 2.8, focus=tT)
path_keys(c, [(T0, HW((0.12, 0.09, 0.3), T0)), (T0 + 20, HW((0.03, 0.08, 0.32), T0 + 20)), (T1, HW((-0.07, 0.075, 0.3), T1))])
# 3 keng: past burchak, 16 mm, oyna va aksi
W0, W1 = S["wide"]
wT = at("wideT", (0.0, -0.45, 1.2))
c = shot_cam("wide", (0, 0, 0), wT, 16, 5.6, focus=at("wideF", (0.0, -0.15, 1.3)))
path_keys(c, [(W0, (0.95, 0.75, 0.32)), (W1, (0.85, 0.55, 0.7))])
# 4 o'lim uchburchagi: crash zoom + silkinish
c = shot_cam("death", (0, 0, 0), tT, 22, 2.4, focus=tT)
path_keys(c, [(D0, HW((0.0, 0.06, 0.75), D0)), (D0 + 6, HW((0.0, 0.065, 0.3), D0 + 6)), (D1, HW((0.0, 0.065, 0.26), D1))])
lens_keys(c, [(D0, 20), (D0 + 6, 42), (D1, 46)])
shake(c, D0 + 5, D0 + 22, 0.006, seed=4)
# 5 barmoqlar: makro, yondan
fT = at("fingT", PI_ + Vector((0.0, 0.0, 0.002)), headE)
c = shot_cam("fingers", (0, 0, 0), fT, 45, 9.0, focus=fT, clip=0.001)
path_keys(c, [(FI0, HW(tuple(PI_ + Vector((-0.035, -0.09, 0.1))), FI0)), (FI1, HW(tuple(PI_ + Vector((-0.028, -0.065, 0.075))), FI1))])
# 6 siqish: past burchak, o'ngdan push-in
Q0, Q1 = S["squeeze"]
qT = at("sqT", (-0.012, 0.045, 0.14), headE)
c = shot_cam("squeeze", (0, 0, 0), qT, 28, 2.8, focus=qT)
path_keys(c, [(Q0, HW((-0.3, -0.18, 0.32), Q0)), (Q1, HW((-0.2, -0.1, 0.24), Q1))])
lens_keys(c, [(Q0, 28), (Q1, 36)])
shake(c, POP_F, POP_F + 12, 0.006, seed=6)
# 7 rentgen venalar: old tomondan push-in
xT = at("xvT", (0, 0.06, 0.12), headE)
c = shot_cam("xveins", (0, 0, 0), xT, 35, 4.0, focus=xT)
path_keys(c, [(XV0, HW((0.03, 0.07, 0.5), XV0)), (XV1, HW((-0.02, 0.065, 0.32), XV1))])
# 8 sinus: o'ng yonga aylanib, ko'z orqasiga
sT = at("xsT", (-0.012, 0.087, 0.085), headE)
c = shot_cam("xsinus", (0, 0, 0), sT, 40, 4.0, focus=sT)
pts = []
for i, f in enumerate(range(XS0, XS1 + 1, 4)):
    t = ease((f - XS0) / (XS1 - XS0)); a = R(-25 - 60 * t); rr = 0.34 - 0.08 * t
    pts.append((f, HW((rr * math.sin(a), 0.1 + 0.03 * t, 0.085 + rr * math.cos(a)), f)))
path_keys(c, pts)
# 9 klapan: tomir bo'ylab yonlama ergashish
vT = empty("valveT"); path_keys(vT, [(VA0, VS + Vector((-1.2, 0, 0))), (VALVE_F, VS + Vector((0.0, 0, 0))), (VA1, VS + Vector((-0.6, 0, 0)))])
c = shot_cam("valve", (0, 0, 0), vT, 28, 4.0, focus=vT)
path_keys(c, [(VA0, VS + Vector((-2.4, -2.6, 0.7))), (VALVE_F, VS + Vector((-0.5, -2.2, 0.5))), (VA1, VS + Vector((-1.4, -1.9, 0.35)))])
shake(c, NOVALVE_F, NOVALVE_F + 14, 0.04, seed=8)
# 10 bosish: makro, push-in + silkinish
pT = at("pressT", PI_ + Vector((0.0, 0.0, 0.001)), headE)
c = shot_cam("press", (0, 0, 0), pT, 45, 9.0, focus=pT, clip=0.001)
path_keys(c, [(PR0, HW(tuple(PI_ + Vector((-0.07, -0.045, 0.085))), PR0)), (PR1, HW(tuple(PI_ + Vector((-0.05, -0.03, 0.06))), PR1))])
shake(c, PR0 + 16, PR1, 0.0012, seed=10, decay=False)
# 11 kesim: yonlama suriladi
seT = empty("secT"); path_keys(seT, [(SC0, SS + Vector((0.0, SFY, 0.75))), (FR_ + 10, SS + Vector((-0.05, SFY, 0.5))), (SC1, SS + Vector((-0.6, SFY, 0.38)))])
c = shot_cam("section", (0, 0, 0), seT, 26, 5.0, focus=seT)
path_keys(c, [(SC0, SS + Vector((0.9, -3.4, 1.35))), (SC1, SS + Vector((-0.5, -3.0, 0.75)))])
shake(c, FR_, FR_ + 12, 0.03, seed=11)
# 12 bakteriya oqimi: yetakchi bakteriyaga ergashish (yondan)
lead = bacts[4]
xfT = empty("xfT"); cf = xfT.constraints.new("COPY_LOCATION"); cf.target = lead
c = shot_cam("xflow", (0, 0, 0), xfT, 45, 4.0, focus=xfT)
path_keys(c, [(XF0, HW((-0.25, 0.03, 0.24), XF0)), (XF1, HW((-0.27, 0.09, 0.06), XF1))])
# 13 tromb: crash zoom + qizil puls
cT = at("clotT", VC + Vector((0.4, 0, 0.05)))
c = shot_cam("clot", (0, 0, 0), cT, 20, 3.5, focus=cT)
path_keys(c, [(CL0, VC + Vector((-1.6, -3.4, 0.6))), (CL0 + 6, VC + Vector((-0.9, -1.9, 0.35))), (CL1, VC + Vector((-0.6, -1.6, 0.25)))])
lens_keys(c, [(CL0, 18), (CL0 + 6, 30), (CL1, 34)])
shake(c, CL0 + 5, CL0 + 20, 0.05, seed=13)
# 14 falajlik: past burchak aylanma
AGA, AGB = S["agony"]
c = shot_cam("agony", (0, 0, 0), faceT, 20, 2.8, focus=faceT)
path_keys(c, [(AGA, (-0.4, -0.72, 0.98)), (AGB, (0.3, -0.7, 1.02))]); c.data.lens = 18
# 15 ko'rlik: ko'zga juda yaqin, fokus yo'qoladi
BL0, BL1 = S["blind"]
eyeT = at("eyeT", (-0.032, 0.095, 0.14), headE)
blF = empty("blindF"); cf = blF.constraints.new("COPY_LOCATION"); cf.target = eyeT
c = shot_cam("blind", (0, 0, 0), eyeT, 50, 2.0, focus=blF, clip=0.002)
c.parent = headE
path_keys(c, [(BL0, (-0.06, 0.1, 0.27)), (BL1, (-0.05, 0.098, 0.22))])
cf.use_offset = True
blF.location = (0, 0, 0); blF.keyframe_insert("location", frame=BL0 + 4); blF.location = (0, -0.25, 0); blF.keyframe_insert("location", frame=BL1)
# 16 yiqilish: past burchak keng
FA0, FA1 = S["fall"]
faT = empty("fallT"); cf = faT.constraints.new("COPY_LOCATION"); cf.target = meg; cf.subtarget = "mixamorig:Hips"
c = shot_cam("fall", (0, 0, 0), faT, 18, 4.0, focus=faT)
path_keys(c, [(FA0, (1.25, 0.15, 0.22)), (FA1, (1.15, 0.45, 0.32))])
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
# 7) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mp = N.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, R(30)); L.new(tcw.outputs["Generated"], mp.inputs[0])
e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + "studio_small_09.hdr"); L.new(mp.outputs[0], e.inputs[0])
bg_st = N.new("ShaderNodeBackground"); L.new(e.outputs[0], bg_st.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.008, 0.02, 1)
bg_rd = N.new("ShaderNodeBackground"); bg_rd.inputs[0].default_value = (0.03, 0.002, 0.003, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_st.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1])
a2 = N.new("ShaderNodeAddShader"); L.new(a1.outputs[0], a2.inputs[0]); L.new(bg_rd.outputs[0], a2.inputs[1]); L.new(a2.outputs[0], out.inputs["Surface"])
WL = {"hook": (0.25, 0, 0), "tri": (0.2, 0, 0), "wide": (0.3, 0, 0), "death": (0.08, 0, 0.5), "fingers": (0.25, 0, 0), "squeeze": (0.2, 0, 0),
      "xveins": (0, 1.0, 0), "xsinus": (0, 1.0, 0), "valve": (0, 0, 1.0), "press": (0.2, 0, 0), "section": (0.15, 0.6, 0), "xflow": (0, 1.0, 0),
      "clot": (0, 0, 1.2), "agony": (0.08, 0, 0.6), "blind": (0.08, 0, 0.3), "fall": (0.1, 0, 0.4)}
for f, n in SHOTS:
    for bgn, v in zip((bg_st, bg_dk, bg_rd), WL[n]):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

NORMAL = rng("hook", "tri", "wide", "fingers", "squeeze", "press")
RED = rng("death", "agony", "blind", "fall")
mT = at("mirT", (0, -0.1, 1.45))
area("vanity_key", (0.0, Y0 + 0.15, 2.0), 0.7, (1.0, 0.82, 0.62), lights_for(NORMAL, 70.0), target=faceT, shape=(0.7, 0.12))
area("vanity_key_r", (0.0, Y0 + 0.15, 2.0), 0.7, (1.0, 0.75, 0.55), lights_for(RED, 25.0), target=faceT, shape=(0.7, 0.12))
area("ceiling", (0.0, 0.5, HZ_ - 0.05), 1.0, (1.0, 0.92, 0.85), lights_for(ROOM, 90.0), target=at("ceilT", (0, 0.3, 0)))
area("fill_side", (1.0, -0.2, 1.6), 0.8, (0.75, 0.85, 1.0), lights_for(NORMAL, 35.0), target=faceT)
area("rim_back", (-0.7, 0.9, 1.9), 0.5, (1.0, 0.7, 0.5), lights_for(ROOM, 45.0), target=faceT)
area("red_key", (0.8, -0.5, 1.7), 0.6, (1.0, 0.06, 0.03), lights_for(RED, 70.0), target=faceT)
area("red_floor", (-0.9, -0.2, 0.6), 0.8, (1.0, 0.05, 0.03), lights_for(rng("fall", "agony"), 50.0), target=at("rfT", (0, 0.3, 0.2)))
# husnbuzar yorilganda chaqnash
point("pop_flash", (0, 0, 0), 0.01, (1.0, 0.95, 0.85), [(1, 0), (POP_F, 3.0), (POP_F + 2, 0.8), (POP_F + 5, 0)], const=False, parent=pimE).location = (0, 0, 0.02)
# rentgen
area("X_rim", (-0.8, 0.5, 1.8), 0.8, (0.3, 0.6, 1.0), lights_for(XH, 30.0), target=headE)
area("X_key", (0.6, -0.9, 1.6), 0.6, (0.5, 0.7, 1.0), lights_for(XH, 15.0), target=headE)
# tomir studiyalari
for nm, C in (("VS", VS), ("VC", VC)):
    rngs = rng("valve") if nm == "VS" else rng("clot")
    area(nm + "_key", tuple(C + Vector((-2, -3, 3))), 2.5, (1.0, 0.85, 0.8), lights_for(rngs, 700.0), target=at(nm + "T1", C))
    area(nm + "_rim", tuple(C + Vector((2, 3, 1.5))), 2.5, (1.0, 0.25, 0.15), lights_for(rngs, 900.0), target=at(nm + "T2", C))
    point(nm + "_in", tuple(C + Vector((0.0, 0, 0))), 0.2, (1.0, 0.3, 0.25), lights_for(rngs, 40.0))
point("novalve_flash", tuple(VS + Vector((0.3, -0.6, 0.2))), 0.2, (1.0, 0.1, 0.05), [(1, 0), (NOVALVE_F, 600), (NOVALVE_F + 3, 250), (NOVALVE_F + 10, 0)], const=False)
cpl = point("clot_pulse", tuple(VC + Vector((0.4, -0.9, 0.3))), 0.2, (1.0, 0.08, 0.04), [(1, 0)], const=False)
for f in range(CL0, CL1 + 1, 12):
    cpl.data.energy = 900; cpl.data.keyframe_insert("energy", frame=f); cpl.data.energy = 120; cpl.data.keyframe_insert("energy", frame=f + 6)
cpl.data.energy = 0; cpl.data.keyframe_insert("energy", frame=CL1 + 1)
# kesim studiyasi
area("SS_key", tuple(SS + Vector((-1.5, -3.0, 3.0))), 2.5, (1.0, 0.95, 0.9), lights_for(rng("section"), 500.0), target=at("ssT", SS + Vector((0, -0.7, 0.6))))
area("SS_rim", tuple(SS + Vector((2.0, -1.5, 2.0))), 2.0, (0.5, 0.75, 1.0), lights_for(rng("section"), 300.0), target=at("ssT2", SS + Vector((0, -0.7, 0.6))))
point("SS_burst", tuple(SS + Vector((0, SFY - 0.3, 0.5))), 0.1, (1.0, 0.85, 0.3), [(1, 0), (FR_, 120), (FR_ + 4, 30), (FR_ + 10, 0)], const=False)

# ======================================================================
# 8) RENDER
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
