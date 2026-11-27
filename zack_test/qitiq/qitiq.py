# Nega o'zingizni qitiqlay olmaysiz — Zack D. Films uslubida 31.5 s video (756 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; yordamchilar va rentgen/impuls materiallari zack_test/ishqalash/ishqalash.py dan;
# miya/quvurlar/barmoq: zack_test/burish/parts.py; makro teri va chivin: zack_test/chivin/mosquito.py
# Assetlar: zack_test/tools/get_qitiq.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/qitiq/qitiq.py --render
# Sinov:  FRAMES=20,90,240,400,620 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, os.path.join(ZT, "yelim"))
sys.path.insert(0, os.path.join(ZT, "chivin")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
import mosquito as M
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 756
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (37, "self"), (74, "bored"), (108, "other"), (146, "laugh"), (177, "why"), (202, "predict"),
         (271, "cereb"), (365, "ghost"), (465, "cancel"), (517, "touch"), (559, "attack"), (604, "bug"), (649, "panic"),
         (715, "defend")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "bored", "other", "laugh", "why", "touch", "defend")
XRN = ("predict", "cereb", "cancel", "attack", "panic")
MACN = ("self", "ghost", "bug")
ROOM = rng(*ROOMN); XR = rng(*XRN); MACR = rng(*MACN)
F_MOVE = 232        # "qimirlatishingizdan" — qo'l qimirlay boshlaydi (buyruq impulsi undan oldin)
F_OFF = 494         # "o'chirib"
F_TOUCH = 530       # Kate barmoqlari tegadi
F_ATTACK = 584      # "hujum"
F_LAND = 622        # chivin qo'nadi
F_PANIC = 692       # "vahima"

# ---------------- yordamchilar (qovoq.py dan) ----------------
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

def frames_vis(o, frames, lo=1, hi=END):
    """faqat berilgan kadrlarda ko'rinadi (chaqmoq/uchqun miltillashi)"""
    fs = set(frames)
    prev = None
    for f in range(lo, hi + 2):
        on = f in fs
        if on != prev:
            o.hide_render = not on; o.keyframe_insert("hide_render", frame=f); prev = on
    interp(o, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
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
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]     # transform_apply joylashuvni ham mesh'ga yozib yuboradi
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

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

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

def area(name, loc, size, col, keys, target=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
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

# ---------------- rentgen / impuls materiallari (qovoq.py dan) ----------------
def xr_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", 1.2)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.75, 1.0, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.015), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.6), 0.04, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
def brain_mat2(name, glow=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15; b.inputs["Roughness"].default_value = 0.4
    gl = value_node(m, "glow", glow); red = value_node(m, "red", 0.0)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs[6].default_value = (0.78, 0.42, 0.45, 1); base.inputs[7].default_value = (0.92, 0.6, 0.6, 1)
    L.new(nz.outputs["Fac"], base.inputs["Factor"]); L.new(base.outputs[2], b.inputs["Base Color"])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.inputs[6].default_value = (1.0, 0.55, 0.65, 1); c2.inputs[7].default_value = (1.0, 0.04, 0.02, 1)
    L.new(red, c2.inputs["Factor"]); L.new(c2.outputs[2], b.inputs["Emission Color"])
    fl = P.math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", fl, 0.15), gl), b.inputs["Emission Strength"])
    return m
def assign(root, m):
    for o in root.children_recursive:
        if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(m)
def train_mat(name, col=(0.25, 0.55, 1.0), pcol=(0.6, 0.85, 1.0)):
    """egri bo'ylab impulslar poyezdi: 'count' ta impuls, 'phase' oshgan sari oldinga yuradi, 'amp' yorqinlik"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.35
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    cnt = value_node(m, "count", 1.0); ph = value_node(m, "phase", -1.0); amp = value_node(m, "amp", 0.0); gl = value_node(m, "glow", 0.4)
    x = P.math_n(N, L, "FRACT", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", ua.outputs["Fac"], cnt), ph))
    d = P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", x, 0.5))
    p = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", d, 0.12), clamp=True), 2.0)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", p, amp), gl), b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (*pcol, 1)
    return m

def V(*a): return Vector(a)
def text_obj(name, body, loc, rot, size, m, parent=None):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = 0.00005; cu.space_line = 0.9
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.parent = parent
    o.location = loc; o.rotation_euler = [R(a) for a in rot]; cu.materials.append(m)
    return o
def ckey(idb, mode="CONSTANT", path=None): interp(idb, mode, path)

# ---------------- qahramon yordamchilari (ishqalash.py dan) ----------------
def soften(meshes, rough=0.5):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = rough
                    n.inputs["Coat Weight"].default_value = 0.0
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
LOWER = ("Hips", "UpLeg", "Leg", "Foot", "ToeBase", "Toe_End")
def upper(act, drop=()):
    a = act.copy(); a.name = act.name + "_upper" + "".join(drop); a.use_fake_user = True
    for fc in list(mc._fcurves(a)):
        b = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        if any(b.endswith(s) for s in LOWER) or any(d in b for d in drop): mc._channelbag_remove(a, fc)
    return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0, infl=None, rev=False):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo; s.use_reverse = rev
    if infl is not None:
        s.use_animated_influence = True; s.influence = infl; s.keyframe_insert("influence", frame=start)
    return s
def span(act, n, src=None):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8)
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)


def lin(idb):
    """material/ob'ekt harakatining barcha kalitlarini chiziqli qilish"""
    ad = idb.animation_data
    if ad and ad.action:
        for fc in mc._fcurves(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# ======================================================================
# 1) MEHMONXONA (kunduzi): divan, stolcha, o'simliklar, deraza (ishqalash.py xonasi asosida)
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.86, 0.9, 0.86))
X0, X1, Y0, Y1, HZ_ = -2.6, 2.4, -2.2, 2.6, 2.7
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_F", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
R_(box("wall_B", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
# chap devorda katta deraza (kunduzgi yorug'lik yondan tushadi)
WY0, WY1, WZ0, WZ1 = 0.6, 2.3, 0.75, 2.35
R_(box("wall_L1", (0.1, WY0 - Y0, HZ_), (X0 - 0.05, (Y0 + WY0) / 2, HZ_ / 2), wall_m))
R_(box("wall_L2", (0.1, Y1 - WY1, HZ_), (X0 - 0.05, (WY1 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_L3", (0.1, WY1 - WY0, WZ0), (X0 - 0.05, (WY0 + WY1) / 2, WZ0 / 2), wall_m))
R_(box("wall_L4", (0.1, WY1 - WY0, HZ_ - WZ1), (X0 - 0.05, (WY0 + WY1) / 2, (WZ1 + HZ_) / 2), wall_m))
frame_m = mat("win_frame", (0.93, 0.93, 0.9), 0.4)
WC = Vector((X0 - 0.05, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2)); WW, WH = WY1 - WY0, WZ1 - WZ0
for nm, sz, off in (("wf_t", (0.12, WW + 0.04, 0.05), (0, 0, WH / 2)), ("wf_b", (0.2, WW + 0.04, 0.06), (0.05, 0, -WH / 2)),
                    ("wf_l", (0.12, 0.05, WH), (0, -WW / 2, 0)), ("wf_r", (0.12, 0.05, WH), (0, WW / 2, 0)),
                    ("wf_m", (0.08, 0.04, WH), (0, 0, 0))):
    R_(box(nm, sz, tuple(WC + Vector(off)), frame_m))
for y in (WY0 - 0.2, WY1 + 0.2):
    c_ = R_(box("curtain", (0.06, 0.4, 2.45), (X0 + 0.08, y, 1.3), mat("curtain_m", (0.9, 0.86, 0.76), 0.9, sss=0.1)))
    d_ = c_.modifiers.new("wave", "WAVE"); d_.height = 0.04; d_.width = 0.12; d_.narrowness = 1; d_.use_x = False; d_.speed = 0
R_(box("baseboard", (X1 - X0, 0.03, 0.1), ((X0 + X1) / 2, Y1 - 0.015, 0.05), frame_m))
R_(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X1 - 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
# tashqarida: maysa va daraxtlar (derazadan ko'rinadi)
R_(plane("out_ground", (30, 40), (X0 - 15, 0, -0.3), mat("out_grass", (0.12, 0.25, 0.06), 0.9)))
tree_m = mat("tree", (0.08, 0.2, 0.05), 0.8, sss=0.1); trunk_m = mat("trunk", (0.15, 0.1, 0.06), 0.9)
rw = random.Random(3)
for i in range(6):
    p = Vector((X0 - rw.uniform(4, 12), rw.uniform(-3, 6), 0))
    R_(cyl(f"trunk{i}", 0.12, 2.6, tuple(p + Vector((0, 0, 1.0))), trunk_m))
    R_(sphere(f"crown{i}", rw.uniform(1.3, 2.0), tuple(p + Vector((0, 0, 3.0))), tree_m, scale=(1, 1, 0.85), sub=3))

SOFA = Vector((-0.6, 1.95, 0.0))
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", tuple(SOFA), 0, 1.0))
TABLE = R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.6, 1.05, 0), 0, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-1.75, 2.2, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (0.6, 2.25, 0), 70, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.6, Y1 - 0.03, 1.5), 0, 1.4))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X1 - 0.2, 1.6, 0), -90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X1 - 0.3, 1.6, 1.03), -90, 1.0))
CHAIR = R_(import_gltf(PH + "modern_arm_chair_01/modern_arm_chair_01.gltf", (1.1, 0.6, 0), 120, 1.0))
R_(plane("rug", (2.4, 1.7), (-0.6, 1.15, 0.004), mat("rug", (0.6, 0.36, 0.26), 0.95)))
cer = [mat("cer_w", (0.9, 0.9, 0.88), 0.25, coat=0.6), mat("cer_r", (0.7, 0.2, 0.08), 0.3, coat=0.6)]
for i, (x, y) in enumerate(((-0.75, 1.0), (-0.45, 1.12))):
    R_(cyl(f"cup{i}", 0.04, 0.09, (x, y, 0.45), cer[i]))

# ======================================================================
# 2) MEGAN (divanda) va KATE (onasi, yonida)
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften(mmeshes, 0.48)
kroot, kat, kmeshes = mc.load_character("kat", "Kate.fbx"); sc.render.fps = 24
soften(kmeshes, 0.5)
MEG = SOFA + V(0.32, 0.07, -0.12)
KAT = SOFA + V(-0.38, 0.03, -0.07)
place(mroot, 1, tuple(MEG), 0); ckey(mroot)
place(kroot, 1, tuple(KAT), 26); ckey(kroot)

IDLE = A_("Sitting_Idle_5.fbx")
strip(meg, IDLE, 1, repeat=span(IDLE, END + 4))
LAUGH = A_("Sitting_Laughing.fbx")
def laugh(f0, f1, src0=1, bi=6, bo=8, sp=1.0):
    n = f1 - f0
    strip(meg, LAUGH, f0, src=(src0, src0 + n / 0.8 * sp), speed=sp, bi=bi, bo=bo)
laugh(140, 202, 20, bi=5, bo=8, sp=1.15)
laugh(F_TOUCH - 2, 606, 1, bi=4, bo=6, sp=1.2)
laugh(640, END + 2, 60, bi=6, bo=0, sp=1.1)
SHAKE = upper(A_("Annoyed_Head_Shake.fbx"), drop=("Arm", "Hand", "Shoulder"))
strip(meg, SHAKE, 70, src=(5, 60), speed=1.0, bi=6, bo=6)
KTALK = A_("Sitting_Talking.fbx")
strip(kat, KTALK, 1, src=(1, 1 + (END + 4) / 0.8), repeat=1.0)

# --- IK: Megan o'zini qitiqlaydi (chap qo'l boshi ortida, o'ng qo'l chap qo'ltiqda)
def ik(arm, bone, target, pole=None, pole_angle=0.0):
    pb = arm.pose.bones["mixamorig:" + bone]
    c = pb.constraints.new("IK"); c.target = target; c.chain_count = 2; c.use_tail = True
    if pole is not None: c.pole_target = pole; c.pole_angle = R(pole_angle)
    c.influence = 0.0; c.keyframe_insert("influence", frame=1)
    return c
def infl(c, pairs):
    for f, v in pairs: c.influence = v; c.keyframe_insert("influence", frame=f)
spineE = child_of_bone("meg_spine2", meg, "Spine2")
headE = child_of_bone("meg_head", meg, "Head")
pitE = empty("armpitT", (0.13, 0.07, 0.07), spineE)          # o'ng qo'l bilagi (Spine2: X chap, Y tepa, Z old)
pitTip = empty("armpitTip", (0.2, 0.12, -0.02), spineE)       # barmoqlar yo'nalishi
lhE = empty("lhandT", (0.07, 0.12, -0.1), headE)             # chap bilak boshi ortida (Head: X chap, Y tepa, Z old)
lTip = empty("lhandTip", (-0.04, 0.2, -0.07), headE)        # barmoqlar boshning tepasi/orqasiga
rPole = empty("rPole", (-0.35, -0.25, 0.45), spineE)
lPole = empty("lPole", (0.45, 0.25, -0.05), headE)
IK_R = ik(meg, "RightForeArm", pitE, rPole, -90)
IK_L = ik(meg, "LeftForeArm", lhE, lPole, -90)
rh = meg.pose.bones["mixamorig:RightHand"]
DT_R = rh.constraints.new("DAMPED_TRACK"); DT_R.target = pitTip; DT_R.track_axis = "TRACK_Y"
DT_R.influence = 0.0; DT_R.keyframe_insert("influence", frame=1)
SELF = [(1, 0.0), (6, 0.0), (18, 1.0), (68, 1.0), (80, 0.0),
        (F_MOVE, 0.0), (F_MOVE + 20, 1.0), (364, 1.0), (365, 0.0), (S["cancel"][0], 1.0), (S["cancel"][1], 1.0), (S["cancel"][1] + 1, 0.0)]
SELF_L = [(1, 0.0), (2, 0.0), (14, 1.0), (68, 1.0), (80, 0.0),
          (F_MOVE - 14, 0.0), (F_MOVE + 6, 1.0), (364, 1.0), (365, 0.0), (S["cancel"][0], 1.0), (S["cancel"][1], 1.0), (S["cancel"][1] + 1, 0.0)]
DT_L = meg.pose.bones["mixamorig:LeftHand"].constraints.new("DAMPED_TRACK"); DT_L.target = lTip; DT_L.track_axis = "TRACK_Y"
infl(IK_R, SELF); infl(DT_R, SELF); infl(IK_L, SELF_L); infl(DT_L, SELF_L)
# qitiqlash: bilak tez-tez qimirlaydi
rj = random.Random(4)
for f in range(1, END + 1, 2):
    pitE.location = (0.13 + rj.uniform(-0.012, 0.012), 0.07 + rj.uniform(-0.015, 0.015), 0.07 + rj.uniform(-0.01, 0.01))
    pitE.keyframe_insert("location", frame=f)

# --- IK: Kate ikki qo'li bilan Megan biqinini qitiqlaydi
spine1E = child_of_bone("meg_spine1", meg, "Spine1")
kR = empty("kateR_T", (-0.15, -0.02, 0.0), spine1E)           # Megan o'ng biqini (Spine1: X chap)
kL = empty("kateL_T", (-0.08, -0.06, 0.13), spine1E)          # qorni oldi
kspE = child_of_bone("kat_spine", kat, "Spine")
kRP = empty("kRPole", (-0.4, -0.35, 0.1), kspE); kLP = empty("kLPole", (0.45, -0.35, 0.1), kspE)
kRtip = empty("kRtip", (-0.06, -0.02, 0.06), spine1E); kLtip = empty("kLtip", (-0.02, -0.06, 0.16), spine1E)
IK_KR = ik(kat, "RightForeArm", kR, kRP, -90)
IK_KL = ik(kat, "LeftForeArm", kL, kLP, -90)
OT0 = S["other"][0]
KATE = [(1, 0.0), (OT0 + 6, 0.0), (OT0 + 28, 1.0), (END, 1.0)]
infl(IK_KR, KATE); infl(IK_KL, KATE)
for bn, tg in (("RightHand", kRtip), ("LeftHand", kLtip)):
    c = kat.pose.bones["mixamorig:" + bn].constraints.new("DAMPED_TRACK"); c.target = tg; c.track_axis = "TRACK_Y"
    infl(c, KATE)
# qo'llar avval uzoqdan yaqinlashadi, keyin qitiqlaydi (tez qimirlash)
kj = random.Random(9)
for f in range(1, END + 1, 2):
    far = max(0.0, 1 - (f - OT0 - 4) / 26) if f < OT0 + 30 else 0.0
    if S["touch"][0] <= f < F_TOUCH: far = max(far, 0.6 * (F_TOUCH - f) / (F_TOUCH - S["touch"][0]))
    a = 0.014 if f >= OT0 + 26 else 0.004
    kR.location = (-0.15 - 0.16 * far + kj.uniform(-a, a), -0.02 + kj.uniform(-a, a), 0.0 + 0.1 * far + kj.uniform(-a, a))
    kL.location = (-0.08 - 0.12 * far + kj.uniform(-a, a), -0.06 + kj.uniform(-a, a), 0.13 + 0.12 * far + kj.uniform(-a, a))
    kR.keyframe_insert("location", frame=f); kL.keyframe_insert("location", frame=f)

faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items()}
HEADW = {n: wpos(headE, (a + b) // 2) for n, (a, b) in S.items()}
print("FACE", {k: tuple(round(x, 3) for x in v) for k, v in FACE.items()})
KATE_ON = [(S["other"][0], END)]

# ======================================================================
# 3) RENTGEN: shaffof tana, miya, miyacha, nervlar
# ======================================================================
def xr_mat2(name, col=(0.35, 0.75, 1.0), rcol=(1.0, 0.12, 0.06), base_alpha=0.04):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", 1.2); red = value_node(m, "red", 0.0)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; cm.inputs[6].default_value = (*col, 1); cm.inputs[7].default_value = (*rcol, 1)
    L.new(red, cm.inputs["Factor"])
    em = N.new("ShaderNodeEmission"); L.new(cm.outputs[2], em.inputs["Color"])
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.015), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.6), base_alpha, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
xbody = xr_mat2("xr_body")
xkate = xr_mat2("xr_kate", col=(1.0, 0.55, 0.2), base_alpha=0.03)
def ghostify(meshes, m):
    gs = []
    for o in meshes:
        if "Eyelash" in o.name: continue
        g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
        g.animation_data_clear()
        for slot in g.material_slots: slot.link = "OBJECT"; slot.material = m
        gs.append(g)
    return gs
mghost = ghostify(mmeshes, xbody); kghost = ghostify(kmeshes, xkate)
for g in mghost: vis(g, XR, recursive=False)
for g in kghost: vis(g, rng("attack", "panic"), recursive=False)
for o in mmeshes: vis(o, ROOM, recursive=False)
for o in kmeshes: vis(o, [r for r in ROOM if r[0] >= S["other"][0]], recursive=False)
val_key(xbody, "glow", 1, 1.2); val_key(xbody, "red", 1, 0.0)
for f in range(S["panic"][0], S["panic"][1] + 1, 5):
    strong = f >= F_PANIC
    val_key(xbody, "red", f, 1.0 if strong else 0.6); val_key(xbody, "glow", f, 3.2 if strong else 2.0)
    val_key(xbody, "glow", f + 2, 1.4)
val_key(xbody, "red", S["attack"][0], 0.0); val_key(xbody, "red", F_ATTACK, 0.0); val_key(xbody, "red", F_ATTACK + 1, 0.5)
val_key(xbody, "red", S["attack"][1], 0.5); val_key(xbody, "red", S["panic"][1] + 1, 0.0)
for fc in mc._fcurves(xbody.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

# miya (Head fazosida) va miyacha (alohida material: "hisoblash" paytida moviy yonadi)
xb_m = brain_mat2("xbrain_m", 0.6)
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
cer_m = brain_mat2("xcereb_m", 0.4)
_cb = cer_m.node_tree.nodes["Principled BSDF"]
_mix = [n for n in cer_m.node_tree.nodes if n.type == "MIX" and n.data_type == "RGBA"][1]
_mix.inputs[6].default_value = (0.3, 0.85, 1.0, 1)          # "red"=0 -> moviy, 1 -> qizil
for o in xbrain.children_recursive:
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(cer_m if o.name.endswith("_cereb") else xb_m)
vis(xbrain, XR)
CORTEX = (0.022, 0.14, 0.035); CEREB = (0.0, 0.083, -0.012); STEM = (0.0, 0.07, 0.005)

def train_mat2(name, col, pcol, rcol=(1.0, 0.08, 0.03)):
    m = train_mat(name, col, pcol)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    red = value_node(m, "red", 0.0)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; cm.inputs[6].default_value = (*pcol, 1); cm.inputs[7].default_value = (*rcol, 1)
    L.new(red, cm.inputs["Factor"]); L.new(cm.outputs[2], b.inputs["Emission Color"])
    return m
def pulse(m, f0, f1, u0, u1, amp=30.0, count=1.0):
    """bitta impuls: f0..f1 da u0 -> u1 (count=1)"""
    val_key(m, "count", f0 - 1, count)
    val_key(m, "amp", f0 - 2, 0.0); val_key(m, "amp", f0, amp); val_key(m, "amp", f1, amp); val_key(m, "amp", f1 + 2, 0.0)
    val_key(m, "phase", f0 - 2, u0 - 0.5); val_key(m, "phase", f1 + 2, u1 - 0.5)
def train(m, f0, f1, speed, amp=25.0, count=4.0):
    """uzluksiz impulslar poyezdi (speed: phase/kadr, manfiy = teskari)"""
    val_key(m, "count", f0 - 1, count); val_key(m, "amp", f0 - 1, 0.0); val_key(m, "amp", f0, amp); val_key(m, "amp", f1, amp)
    val_key(m, "amp", f1 + 1, 0.0)
    val_key(m, "phase", f0, 0.0); val_key(m, "phase", f1, speed * (f1 - f0))

# nervlar: suyaklar bo'ylab, har kadrda nuqtalar qayta hisoblanadi (rentgen kadrlarida)
HEADPTS = lambda: [headE.matrix_world @ Vector(STEM), headE.matrix_world @ Vector(CORTEX)]
def bones(arm, *names): return [arm.matrix_world @ arm.pose.bones["mixamorig:" + n].head for n in names]
NERVES = {
    "r_sens": (lambda: bones(meg, "RightHandIndex4", "RightHandIndex2", "RightHand", "RightForeArm", "RightArm", "RightShoulder", "Neck") + HEADPTS(),
               0.0032, (0.9, 0.8, 0.5), (1.0, 0.75, 0.15), V(0, 0, 0)),
    "r_mot": (lambda: bones(meg, "RightHandIndex4", "RightHandIndex2", "RightHand", "RightForeArm", "RightArm", "RightShoulder", "Neck") + HEADPTS(),
              0.0026, (0.5, 0.7, 0.95), (0.2, 0.75, 1.0), V(0.0, 0.0, 0.007)),
    "l_arm": (lambda: bones(meg, "LeftHandIndex4", "LeftHand", "LeftForeArm", "LeftArm", "LeftShoulder", "Neck") + HEADPTS(),
              0.003, (0.9, 0.8, 0.5), (1.0, 0.75, 0.15), V(0, 0, 0)),
    "spine": (lambda: bones(meg, "Hips", "Spine", "Spine1", "Spine2", "Neck") + [headE.matrix_world @ Vector(STEM)],
              0.005, (0.9, 0.8, 0.5), (1.0, 0.75, 0.15), V(0, 0, 0)),
    "r_leg": (lambda: bones(meg, "RightToeBase", "RightFoot", "RightLeg", "RightUpLeg", "Hips"), 0.0035, (0.9, 0.8, 0.5), (1.0, 0.75, 0.15), V(0, 0, 0)),
    "l_leg": (lambda: bones(meg, "LeftToeBase", "LeftFoot", "LeftLeg", "LeftUpLeg", "Hips"), 0.0035, (0.9, 0.8, 0.5), (1.0, 0.75, 0.15), V(0, 0, 0)),
}
NV = {}
for nm, (fn, rad, col, pcol, off) in NERVES.items():
    sc.frame_set(S["predict"][0]); bpy.context.view_layer.update()
    pts = [tuple(p + off) for p in fn()]
    m = train_mat2("nerve_" + nm, col, pcol)
    t_ = P.tube("nerve_" + nm, pts, rad, m, None, taper=[0.7] + [1.0] * (len(pts) - 1))
    NV[nm] = (t_, m, fn, off)
    val_key(m, "count", 1, 1.0); val_key(m, "amp", 1, 0.0); val_key(m, "phase", 1, 0.0); val_key(m, "glow", 1, 0.5); val_key(m, "red", 1, 0.0)
XRF = sorted({f for a, b in XR for f in range(a, b + 1)})
for f in XRF:
    sc.frame_set(f); bpy.context.view_layer.update()
    for nm, (t_, m, fn, off) in NV.items():
        for sp_pt, p in zip(t_.data.splines[0].points, fn()):
            q = p + off; sp_pt.co = (q.x, q.y, q.z, 1.0); sp_pt.keyframe_insert("co", frame=f)
for nm, (t_, m, fn, off) in NV.items():
    vis(t_, XR, recursive=False)
    ad = t_.data.animation_data
    if ad and ad.action:
        for fc in mc._fcurves(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
mS, mM, mL, mSp, mRL, mLL = (NV[k][1] for k in ("r_sens", "r_mot", "l_arm", "spine", "r_leg", "l_leg"))
for m in (mL, mSp, mRL, mLL): val_key(m, "glow", 1, 0.25)
# 7 predict: qo'l qimirlashidan OLDIN miyadan qo'lga ko'k buyruq impulsi
PD0, PD1 = S["predict"]
pulse(mM, F_MOVE - 24, F_MOVE - 2, 1.0, 0.0, amp=40.0)
pulse(mM, F_MOVE + 4, F_MOVE + 26, 1.0, 0.0, amp=25.0)
# 10 cancel: sariq qitiq signali tepaga, ko'k "o'chirish" impulsi pastga, o'rtada uchrashadi
CA0, CA1 = S["cancel"]
val_key(mS, "count", CA0, 1.0)
val_key(mS, "amp", CA0, 0.0); val_key(mS, "amp", CA0 + 3, 35.0); val_key(mS, "amp", F_OFF - 1, 35.0); val_key(mS, "amp", F_OFF + 1, 80.0)
val_key(mS, "amp", F_OFF + 4, 0.0)
val_key(mS, "phase", CA0, -0.5); val_key(mS, "phase", F_OFF, 0.42 - 0.5); val_key(mS, "phase", CA1 + 1, 0.45 - 0.5)
val_key(mM, "count", CA0, 1.0)
val_key(mM, "amp", CA0 + 8, 0.0); val_key(mM, "amp", CA0 + 10, 40.0); val_key(mM, "amp", F_OFF + 1, 80.0); val_key(mM, "amp", F_OFF + 4, 0.0)
val_key(mM, "phase", CA0 + 8, 0.5); val_key(mM, "phase", F_OFF, 0.42 - 0.5)
val_key(mS, "glow", CA0, 0.5); val_key(mS, "glow", F_OFF + 2, 0.5); val_key(mS, "glow", F_OFF + 8, 0.08)
val_key(mS, "glow", CA1 + 1, 0.5)
# 12 attack: Kate tegdi -> kuchli sariq impulslar miyaga, miya qizil
AT0, AT1 = S["attack"]
train(mS, AT0, AT1, 0.06, amp=40.0, count=3.0)
train(mL, AT0 + 4, AT1, 0.05, amp=25.0, count=3.0)
train(mSp, AT0 + 2, AT1, 0.05, amp=25.0, count=3.0)
# 14 panic: hamma nervlar qizil, tez impulslar
PA0, PA1 = S["panic"]
for k, m in enumerate((mS, mM, mL, mSp, mRL, mLL)):
    train(m, PA0, PA1, 0.07 + 0.01 * k, amp=30.0, count=4.0)
    val_key(m, "red", PA0 - 1, 0.0); val_key(m, "red", PA0, 1.0); val_key(m, "red", PA1 + 1, 0.0)
    val_key(m, "glow", PA0 - 1, 0.25); val_key(m, "glow", PA0, 1.2); val_key(m, "glow", PA1 + 1, 0.25)
for m in (mS, mM, mL, mSp, mRL, mLL):
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT" if ('"red"' in fc.data_path or '"glow"' in fc.data_path) else "LINEAR"
# miya yorqinligi
val_key(xb_m, "glow", 1, 0.6); val_key(xb_m, "red", 1, 0.0)
for f in range(F_MOVE - 30, F_MOVE - 20, 2): val_key(xb_m, "glow", f, 3.5 if f % 4 == 0 else 1.2)
val_key(xb_m, "glow", F_MOVE - 18, 0.6)
for f in range(F_ATTACK - 2, AT1 + 1, 4):
    val_key(xb_m, "glow", f, 6.0); val_key(xb_m, "glow", f + 2, 1.8)
val_key(xb_m, "red", F_ATTACK - 3, 0.0); val_key(xb_m, "red", F_ATTACK - 2, 1.0)
for f in range(PA0, PA1 + 1, 4):
    val_key(xb_m, "glow", f, 5.0); val_key(xb_m, "glow", f + 2, 1.5)
val_key(xb_m, "red", PA1 + 1, 0.0); val_key(xb_m, "glow", PA1 + 3, 0.6)
for fc in mc._fcurves(xb_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
# miyacha: "hisoblash" (cereb kadri) va bashorat (predict/cancel)
CE0, CE1 = S["cereb"]
val_key(cer_m, "glow", 1, 0.4); val_key(cer_m, "red", 1, 0.0)
for f in list(range(CE0 + 6, CE1, 5)) + list(range(F_MOVE - 26, F_MOVE - 6, 5)) + list(range(F_OFF - 14, F_OFF + 4, 4)):
    val_key(cer_m, "glow", f, 7.0); val_key(cer_m, "glow", f + 2, 3.0)
val_key(cer_m, "glow", CE1 + 1, 0.4); val_key(cer_m, "glow", F_MOVE - 4, 0.4); val_key(cer_m, "glow", F_OFF + 6, 0.4)
val_key(cer_m, "red", F_ATTACK - 2, 1.0); val_key(cer_m, "red", PA1 + 1, 0.0)
val_key(cer_m, "glow", F_ATTACK - 2, 2.0); val_key(cer_m, "glow", PA1 + 1, 0.4)
for fc in mc._fcurves(cer_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
# miya <-> miyacha halqalari (Head fazosida)
loop_ms = []
for k, (a, b) in enumerate(((CORTEX, CEREB), (CEREB, CORTEX))):
    A = Vector(a); Bv = Vector(b); mid = (A + Bv) / 2 + Vector((0.012 * (1 if k else -1), 0.012, -0.03 if k else -0.012))
    m = train_mat2(f"loop{k}", (0.4, 0.7, 1.0), (0.3, 0.85, 1.0)); loop_ms.append(m)
    t_ = P.tube(f"loop{k}", [tuple(A), tuple(mid), tuple(Bv)], 0.0012, m, headE)
    vis(t_, rng("cereb", "predict", "cancel"), recursive=False)
    val_key(m, "glow", 1, 0.6); train(m, CE0, CE1, 0.05, amp=30.0, count=3.0)
    train(m, PD0, PD1, 0.05, amp=20.0, count=3.0); train(m, CA0, CA1, 0.05, amp=20.0, count=3.0)
    lin(m.node_tree)
# "hisoblash" halqalari miyacha atrofida (giroskop)
ring_m = mat("calc_ring", (0.3, 0.85, 1.0), 0.4, emit=6.0)
ringE = empty("calcE", CEREB, headE)
for k in range(3):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035 + 0.006 * k, minor_radius=0.0006, major_segments=96, minor_segments=8)
    t_ = bpy.context.object; t_.name = f"calc_ring{k}"; t_.data.materials.append(ring_m); t_.parent = ringE
    for f, s in ((CE0, 0), (CE1 + 1, 1)):
        t_.rotation_euler = (R(60 * k + 200 * s * (1 if k % 2 else -1)), R(40 * k + 120 * s), R(30 * k)); t_.keyframe_insert("rotation_euler", frame=f)
    lin(t_)
vis(ringE, [S["cereb"]])
# hujum: qizil to'lqin halqalari (miyadan tashqariga)
alarm_m = mat("alarm", (1.0, 0.1, 0.05), 0.5, emit=8.0)
alE = empty("alarmE", (0, 0.11, 0.03), headE)
for k in range(4):
    sphere_ = sphere(f"alarm{k}", 1.0, (0, 0, 0), xr_mat2(f"alarm_m{k}", col=(1, 0.15, 0.05), base_alpha=0.0), sub=4, parent=alE)
    f0 = F_ATTACK - 2 + 6 * k
    key(sphere_, 1, scale=0.01); key(sphere_, f0, scale=0.04); key(sphere_, f0 + 14, scale=0.17)
    lin(sphere_)
    frames_vis(sphere_, range(f0, f0 + 14))

# ======================================================================
# 4) MAKRO TERI (real o'lcham): barmoqlar, sharpa barmoq, chivin
# ======================================================================
MAC = V(0.0, 30.0, 1.2)
macE = empty("macE", tuple(MAC))
skin, skin_red = M.skin_patch("skin", arm_r=0.06)
skin.parent = macE
def SZ(x, y): return -(x * x) / (2 * 0.06)          # teri sathi (mahalliy)
def EL(p): return MAC + Vector(p)
mskin = P.skin_material("mfinger_skin", base=(0.7, 0.44, 0.34))
def finger(name, skin_m=None):
    o = P.build_finger(name, macE, r=0.0085, length=0.09, skin=skin_m or mskin)
    return o
def fing_key(o, f, tip, tilt=38.0, yaw=0.0):
    """tip: barmoq uchi (mahalliy), tanasi +Y va tepaga qiya"""
    o.location = tip; o.rotation_euler = (R(tilt), 0, R(yaw))
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
# 2 self: uch barmoq teri ustida navbatma-navbat qimirlaydi
SE0, SE1 = S["self"]
fings = [finger(f"sf{i}") for i in range(3)]
for i, o in enumerate(fings):
    x = (i - 1) * 0.0185
    for f in range(SE0 - 2, SE1 + 3, 2):
        ph = f * 0.9 + i * 2.1
        lift = 0.0035 * (0.5 + 0.5 * math.sin(ph))
        fing_key(o, f, (x + 0.0015 * math.sin(ph * 0.5), 0.004 * (i - 1) + 0.0015 * math.cos(ph), SZ(x, 0) + 0.0022 + lift), tilt=40 - 6 * math.sin(ph), yaw=(1 - i) * 6)
    vis(o, [S["self"]])
# 9 ghost: avval shaffof moviy "bashorat" barmog'i, keyin haqiqiy barmoq aynan o'sha joyga
GH0, GH1 = S["ghost"]
ghost_m = bpy.data.materials.new("ghost_finger"); ghost_m.use_nodes = True
N = ghost_m.node_tree.nodes; L = ghost_m.node_tree.links; out = N["Material Output"]; N.remove(N["Principled BSDF"])
gfade = value_node(ghost_m, "fade", 1.0)
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.3)
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.75, 1.0, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 6.0), 0.4), gfade), em.inputs["Strength"])
tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.7), 0.12, clamp=True), gfade), mx.inputs[0])
L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
gf = finger("ghostf", ghost_m)
for ch in gf.children:
    ch.data.materials.clear(); ch.data.materials.append(ghost_m)
rf = finger("realf")
TOUCH = (0.0, 0.0, SZ(0, 0) + 0.0058)
T_G, T_R = GH0 + 32, GH0 + 70                          # sharpa tegadi, haqiqiy barmoq tegadi
for f, h in ((1, 1.0), (GH0, 1.0), (T_G, 0.0), (GH1 + 1, 0.0)):
    e = ease(min(1, max(0, h)))
    fing_key(gf, f, (TOUCH[0], TOUCH[1] + 0.012 * e, TOUCH[2] + 0.022 * e), tilt=36 + 10 * e)
for f, h in ((1, 1.0), (T_G - 6, 1.0), (T_R, 0.0), (T_R + 6, -0.03), (GH1 + 1, -0.03)):
    e = ease(min(1, max(0, h))) if h >= 0 else h
    fing_key(rf, f, (TOUCH[0], TOUCH[1] + 0.012 * max(e, 0) - 0.0003 * (h < 0), TOUCH[2] + 0.022 * e), tilt=36 + 10 * max(e, 0))
val_key(ghost_m, "fade", 1, 1.0); val_key(ghost_m, "fade", T_R - 2, 1.0); val_key(ghost_m, "fade", T_R + 12, 0.0)
lin(ghost_m.node_tree)
vis(gf, [S["ghost"]]); vis(rf, [S["ghost"]])
# tegish nuqtasida moviy halqa (bosim va vaqt "hisoblangan")
tring_m = mat("touch_ring", (0.3, 0.85, 1.0), 0.4, emit=5.0)
for k in range(2):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=96, minor_segments=8)
    t_ = bpy.context.object; t_.name = f"touch_ring{k}"; t_.data.materials.append(tring_m); t_.parent = macE
    t_.location = (0, -0.006, SZ(0, 0) + 0.0003)
    f0 = T_G + 10 * k
    key(t_, 1, scale=0.001); key(t_, f0, scale=0.004); key(t_, f0 + 22, scale=0.016)
    lin(t_); frames_vis(t_, range(f0, min(f0 + 22, T_R + 6)))
# 13 bug: chivin teriga qo'nadi
BU0, BU1 = S["bug"]
mq = M.build_mosquito("mq", 1.0); mq["curv"] = 0.06
mq["root"].parent = macE
Q_MACRO = Euler((0, 0, R(-120))).to_quaternion()
mq["root"].rotation_mode = "QUATERNION"; mq["root"].rotation_quaternion = Q_MACRO
def contact_local(h): return M.H0 + M.D0 * (M.LP - h / abs(M.D0.z))
BUGP = Vector((0.004, 0.006, SZ(0.004, 0)))
LANDL = BUGP - (Q_MACRO @ contact_local(0.0))
for f in range(BU0 - 2, F_LAND + 1):
    t = (f - (BU0 - 2)) / (F_LAND - BU0 + 2); e = 1 - ease(t)
    mq["root"].location = LANDL + Vector((0.004 * e, -0.007 * e, 0.009 * e + 0.0004 * math.sin(f * 1.7) * e))
    mq["root"].keyframe_insert("location", frame=f)
    M.wings_flap(mq, f)
M.pose(mq, BU0 - 2, 0.0, air=True); M.pose(mq, F_LAND - 4, 0.0, air=True); M.pose(mq, F_LAND, 0.0)
M.wings_rest(mq, F_LAND + 1)
for f in range(F_LAND + 1, BU1 + 3, 3):
    mq["root"].location = LANDL + Vector((0, 0, 0.00004 * math.sin(f))); mq["root"].keyframe_insert("location", frame=f)
vis(mq["root"], [S["bug"]])
vis(skin, MACR)

for o in room_objs: vis(o, ROOM)
# "touch" past burchakli kamerasi stol ichidan o'tadi: shu kadrda stol va krujkalarni yashir
for o in [TABLE] + [x for x in bpy.data.objects if x.name.startswith("cup")]:
    vis(o, [r for r in ROOM if r != S["touch"]])
# "other" aylanma kamerasi kreslo ichidan boshlanadi
vis(CHAIR, [r for r in ROOM if r != S["other"]])

# ======================================================================
# 5) KAMERALAR
# ======================================================================
def rig(name, target):
    e = empty(name + "_rig"); c = e.constraints.new("COPY_LOCATION"); c.target = target; return e
def rel_cam(name, target, lens, fstop, offsets, track=None, clip=0.003):
    r_ = rig(name, target)
    c = shot_cam(name, (0, 0, 0), track or target, lens, fstop, focus=track or target, clip=clip)
    c.parent = r_
    path_keys(c, offsets)
    return c
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
CHEST = {n: wpos(spineE, (a + b) // 2) for n, (a, b) in S.items()}
# 1 ILGAK: poldan, keng ob'ektiv, tez push-in
H0, H1 = S["hook"]; FP = FACE["hook"]; CP = CHEST["hook"]
c = abs_cam("hook", [(H0, CP + V(0.75, -1.35, -0.62)), (H1, CP + V(0.42, -0.78, -0.4))],
            [(H0, CP + V(-0.02, 0, 0.12)), (H1, CP + V(0.02, 0, 0.1))], 16, 2.8)
lens_keys(c, [(H0, 15), (H1, 19)])
# 3 bored: yuzga yaqin, yonlama dolly
BO0, BO1 = S["bored"]
c = rel_cam("bored", faceT, 50, 1.8, [(BO0, V(-0.32, -0.52, 0.0)), (BO1, V(-0.1, -0.6, 0.02))])
# 4 other: keng aylanma, ikkalasi kadrda
OT0, OT1 = S["other"]; MID = (CHEST["other"] + SOFA + V(-0.1, 0, 0.75)) / 2
c = abs_cam("other", [(OT0, MID + V(1.1, -1.5, 0.05)), (OT1, MID + V(0.3, -1.6, -0.1))], [(OT0, MID + V(0.1, 0, 0)), (OT1, MID + V(0, 0, 0))], 24, 3.2)
# 5 laugh: crash zoom + silkinish
LA0, LA1 = S["laugh"]
c = rel_cam("laugh", faceT, 24, 2.8, [(LA0, V(0.15, -0.95, -0.15)), (LA0 + 4, V(0.1, -0.55, -0.08)), (LA1, V(0.08, -0.48, -0.06))])
lens_keys(c, [(LA0, 20), (LA0 + 4, 32), (LA1, 36)]); shake(c, LA0 + 2, LA1, 0.012, seed=5, decay=False)
# 6 why: boshga tez push-in (oxirida oq chaqnash -> rentgen)
WH0, WH1 = S["why"]
c = rel_cam("why", headE, 28, 3.5, [(WH0, V(-0.5, -0.75, 0.15)), (WH1, V(-0.15, -0.25, 0.08))])
lens_keys(c, [(WH0, 26), (WH1, 40)])
# 7 predict: rentgen, butun yuqori tana, aylanma
PD0, PD1 = S["predict"]; CPd = CHEST["predict"]
c = abs_cam("predict", [(PD0, CPd + V(-0.9, -0.95, 0.25)), (PD1, CPd + V(0.15, -1.25, 0.18))], [(PD0, CPd + V(0, 0, 0.1)), (PD1, CPd + V(0, 0, 0.12))], 26, 5.6)
# 8 cereb: bosh, orqa-yondan, sekin aylanma
HC = HEADW["cereb"]
c = abs_cam("cereb", [(CE0, HC + V(0.45, 0.32, 0.18)), (CE0 + 50, HC + V(0.08, 0.42, 0.14)), (CE1, HC + V(-0.25, 0.3, 0.12))],
            [(CE0, HC + V(0, 0, 0.09)), (CE1, HC + V(0, 0, 0.08))], 40, 5.6)
lens_keys(c, [(CE0, 36), (CE1, 46)])
# 10 cancel: qo'l bo'ylab yonlama siljish (qo'ltiqdan boshga)
CC = CHEST["cancel"]
c = abs_cam("cancel", [(CA0, CC + V(-0.55, -0.6, 0.0)), (CA1, CC + V(-0.25, -0.62, 0.3))], [(CA0, CC + V(0.05, 0, 0.05)), (CA1, CC + V(0, 0, 0.3))], 28, 5.6)
# 11 touch: past burchak, push-in (Kate qo'llari)
TO0, TO1 = S["touch"]; CT = CHEST["touch"]
c = abs_cam("touch", [(TO0, CT + V(-0.55, -0.95, -0.4)), (TO1, CT + V(-0.35, -0.6, -0.25))], [(TO0, CT + V(-0.12, 0, -0.08)), (TO1, CT + V(-0.1, 0, 0.0))], 18, 2.8)
# 12 attack: rentgen bosh, crash zoom + silkinish
HA = HEADW["attack"]
c = rel_cam("attack", headE, 24, 5.6, [(AT0, V(0.35, -1.1, 0.25)), (F_ATTACK - 1, V(0.3, -0.95, 0.18)), (F_ATTACK + 2, V(0.2, -0.62, 0.12)), (AT1, V(0.18, -0.56, 0.1))],
            track=headE)
lens_keys(c, [(AT0, 22), (F_ATTACK - 1, 24), (F_ATTACK + 2, 34), (AT1, 36)]); shake(c, F_ATTACK, F_ATTACK + 14, 0.015, seed=12)
# 14 panic: butun tana rentgen, aylanma
CPa = CHEST["panic"]
c = abs_cam("panic", [(PA0, CPa + V(1.1, -1.4, 0.3)), (PA1, CPa + V(-0.6, -1.6, 0.1))], [(PA0, CPa + V(-0.15, 0, -0.1)), (PA1, CPa + V(-0.15, 0, -0.05))], 22, 5.6)
shake(c, F_PANIC, F_PANIC + 10, 0.012, seed=14)
# 15 defend: keng plan, past burchakdan orqaga tortilish
DE0, DE1 = S["defend"]; MD = (CHEST["defend"] + SOFA + V(-0.1, 0, 0.7)) / 2
c = abs_cam("defend", [(DE0, MD + V(0.35, -1.2, -0.45)), (DE1, MD + V(0.6, -2.3, -0.3))], [(DE0, MD + V(0, 0, 0.05)), (DE1, MD + V(0, 0, 0.05))], 18, 4.0)
# makro kameralar
MT_SELF = empty("mT_self", tuple(EL((0.0, 0.002, 0.002))))
c = shot_cam("self", tuple(EL((0.07, -0.085, 0.032))), MT_SELF, 40, 16.0, focus=MT_SELF, clip=0.002)
path_keys(c, [(SE0, EL((0.075, -0.085, 0.03))), (SE1, EL((0.025, -0.095, 0.026)))])
MT_G = empty("mT_ghost", tuple(EL((0.0, 0.004, 0.006))))
c = shot_cam("ghost", (0, 0, 0), MT_G, 45, 16.0, focus=MT_G, clip=0.002)
path_keys(c, [(GH0, EL((-0.07, -0.075, 0.04))), (GH1, EL((-0.035, -0.055, 0.018)))])
MT_B = empty("mT_bug", tuple(EL((0.004, 0.006, 0.001))))
c = shot_cam("bug", (0, 0, 0), MT_B, 50, 18.0, focus=MT_B, clip=0.001)
path_keys(c, [(BU0, EL((0.03, -0.035, 0.018))), (BU1, EL((0.016, -0.02, 0.009)))])
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
# 6) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(110))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_env = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_env.inputs[0])
bg_col = N.new("ShaderNodeBackground")
a1 = N.new("ShaderNodeAddShader"); L.new(bg_env.outputs[0], a1.inputs[0]); L.new(bg_col.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WORLD = {"room": (1.0, (0, 0, 0), 0.0), "xr": (0.0, (0.004, 0.01, 0.028), 1.0), "mac": (0.0, (0.0, 0.0, 0.0), 0.0)}
def world_of(n): return "room" if n in ROOMN else "xr" if n in XRN else "mac"
for f, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
# xona (kunduzi): deraza orqali quyosh, derazadan yumshoq yorug'lik, shiftdan to'ldirish
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.5); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(55), R(-42), R(-95))
for f, e in lights_for(ROOM, 4.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("win_soft", tuple(WC + V(0.35, 0, 0)), 1.6, (0.85, 0.92, 1.0), lights_for(ROOM, 160.0), target=FT)
area("ceil_fill", (-0.4, 0.4, 2.6), 2.2, (1.0, 0.93, 0.85), lights_for(ROOM, 60.0), target=empty("cfT", (-0.4, 1.2, 0)))
area("face_fill", tuple(SOFA + V(0.9, -1.4, 1.4)), 0.8, (1.0, 0.92, 0.85), lights_for(rng("bored", "laugh", "why", "touch"), 22.0), target=FT)
area("rim", tuple(SOFA + V(1.0, 0.5, 1.9)), 0.8, (1.0, 0.9, 0.75), lights_for(ROOM, 40.0), target=FT)
# rentgen
HT = empty("xrT"); clh = HT.constraints.new("COPY_LOCATION"); clh.target = headE
area("X_key", tuple(MEG + V(1.2, -1.4, 2.0)), 1.0, (0.8, 0.9, 1.0), lights_for(XR, 25.0), target=HT)
area("X_rim", tuple(MEG + V(-1.0, 0.8, 1.8)), 1.0, (0.3, 0.55, 1.0), lights_for(XR, 30.0), target=HT)
# makro
MT = empty("macroT", tuple(EL((0, 0, 0))))
area("M_key", tuple(EL((-0.12, -0.15, 0.2))), 0.2, (1.0, 0.95, 0.88), lights_for(MACR, 6.0), target=MT)
area("M_fill", tuple(EL((0.16, -0.14, 0.06))), 0.2, (0.9, 0.93, 1.0), lights_for(MACR, 2.5), target=MT)
area("M_rim", tuple(EL((0.02, 0.15, 0.12))), 0.12, (1.0, 0.85, 0.7), lights_for(MACR, 4.0), target=MT)

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

if os.environ.get("PROBE"): exec(open(os.environ["PROBE"]).read())
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
