# Har kuni 40 daqiqa ko'r bo'lasiz (sakkadik niqoblash + to'xtagan soat) — Zack D. Films uslubida 35.9 s video
# (862 kadr, 24 fps, 9:16). Kadr rejasi: STORYBOARD.md
# Asos: zack_test/scene3.py + mixchar.py, zack_test/ishqalash/ishqalash.py (xona, rentgen bosh, kamera yordamchilari),
# zack_test/yelim/eye.py (makro ko'z), zack_test/burish/parts.py (egri chiziqlar, miya)
# Assetlar: zack_test/tools/get_sakkada.sh
# POV suratlari (kino lentasi uchun, bir marta): STILLS=1 PCT=25 /tmp/claude-0/bvenv/bin/python -I zack_test/sakkada/sakkada.py --render
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/sakkada/sakkada.py --render
# Sinov:  FRAMES=30,100,230,360,680 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, os.path.join(ZT, "qovoq"))
sys.path.insert(0, os.path.join(ZT, "yelim")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
STILL_DIR = os.environ.get("STILL_DIR", "/tmp/claude-0/assets/pov/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
import twitch as TW
import eye as EY
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 862
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (61, "blind"), (144, "mirror"), (202, "look"), (272, "saw"), (334, "jump"), (394, "blur"),
         (467, "brain"), (522, "off"), (553, "povoff"), (589, "gap"), (649, "fill"), (736, "clock"), (775, "tick"),
         (817, "fake")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("blind", "mirror", "look", "saw", "blur", "povoff", "clock", "tick", "fake")
XRN = ("jump", "brain", "off")
MACN = ("hook",)
FILMN = ("gap", "fill")
ROOM = rng(*ROOMN); XR = rng(*XRN); MACR = rng(*MACN); FILMR = rng(*FILMN)
MEGR = rng("blind", "mirror", "look", "saw", "blur", "povoff", "clock", "fake")   # Megan ko'rinadigan kadrlar
F_NO = 318          # "Yo'q"
F_SLIDE0, F_SLIDE1 = 664, 700     # "orqaga surib"
F_JOIN = 711        # "ulab"
F_STUCK1 = 806      # soat mili "qotib" turgandan keyingi birinchi chiqillash

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

# ======================================================================
# 1) XONA (kunduz): o'ng devorda oyna va soat, deraza, divan, javon
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.88, 0.9, 0.86))
X0, X1, Y0, Y1, HZ_ = -2.6, 2.4, -1.8, 2.6, 2.7
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.9, 0.9, 0.88), 0.8)))
R_(box("wall_L", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_F", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
WX0, WX1, WZ0, WZ1 = -1.2, 0.8, 0.85, 2.3
R_(box("wall_B1", (WX0 - X0, 0.1, HZ_), ((X0 + WX0) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
R_(box("wall_B2", (X1 - WX1, 0.1, HZ_), ((WX1 + X1) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
R_(box("wall_B3", (WX1 - WX0, 0.1, WZ0), ((WX0 + WX1) / 2, Y0 - 0.05, WZ0 / 2), wall_m))
R_(box("wall_B4", (WX1 - WX0, 0.1, HZ_ - WZ1), ((WX0 + WX1) / 2, Y0 - 0.05, (WZ1 + HZ_) / 2), wall_m))
frame_m = mat("win_frame", (0.93, 0.93, 0.9), 0.4)
WC = Vector(((WX0 + WX1) / 2, Y0 - 0.05, (WZ0 + WZ1) / 2)); WW, WH = WX1 - WX0, WZ1 - WZ0
for nm, sz, off in (("wf_t", (WW + 0.04, 0.12, 0.05), (0, 0, WH / 2)), ("wf_b", (WW + 0.04, 0.2, 0.06), (0, 0.05, -WH / 2)),
                    ("wf_l", (0.05, 0.12, WH), (-WW / 2, 0, 0)), ("wf_r", (0.05, 0.12, WH), (WW / 2, 0, 0)),
                    ("wf_m", (0.04, 0.08, WH), (0, 0, 0))):
    R_(box(nm, sz, tuple(WC + Vector(off)), frame_m))
for x in (WX0 - 0.25, WX1 + 0.25):
    c_ = R_(box("curtain", (0.45, 0.06, 2.4), (x, Y0 + 0.08, 1.3), mat("curtain_m", (0.86, 0.8, 0.68), 0.9, sss=0.1)))
    d_ = c_.modifiers.new("wave", "WAVE"); d_.height = 0.04; d_.width = 0.12; d_.narrowness = 1; d_.use_y = False; d_.speed = 0
R_(box("baseboard", (X1 - X0, 0.03, 0.1), ((X0 + X1) / 2, Y1 - 0.015, 0.05), frame_m))
R_(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X1 - 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
# tashqarida: maysa va daraxtlar (derazadan)
R_(plane("out_ground", (40, 30), (0, Y0 - 16, -0.3), mat("out_grass", (0.12, 0.2, 0.06), 0.9)))
rw = random.Random(3)
leaf_m = mat("leaf", (0.1, 0.25, 0.06), 0.8, sss=0.1); trunk_m = mat("trunk", (0.12, 0.08, 0.05), 0.9)
for i in range(6):
    x = -6 + i * 2.4 + rw.uniform(-0.5, 0.5); y = -7 - rw.uniform(0, 5)
    R_(cyl(f"trunk{i}", 0.12, 2.5, (x, y, 0.95), trunk_m))
    R_(sphere(f"crown{i}", rw.uniform(1.1, 1.6), (x, y, 2.9), leaf_m, scale=(1, 1, 0.85), sub=2))
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.9, 2.15, 0), 0, 1.0))
R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.9, 1.35, 0), 0, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.2, 2.2, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (2.0, -1.35, 0), 70, 1.1))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.9, Y1 - 0.03, 1.45), 0, 1.3))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, -0.9, 0), 90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, -1.1, 1.03), 90, 1.0))
R_(plane("rug", (2.4, 1.7), (-0.2, 0.7, 0.004), mat("rug", (0.5, 0.36, 0.28), 0.95)))

# oyna (o'ng devor, x = X1): ramka + toza ko'zgu
MIR = Vector((X1 - 0.012, 0.5, 1.5)); MW_, MH_ = 0.8, 1.15
mirror_m = mat("mirror", (0.9, 0.9, 0.9), 0.0, metal=1.0)
R_(plane("mirror_glass", (MW_, MH_), tuple(MIR), mirror_m, rot=(90, 0, 90)))
mfr_m = mat("mirror_frame", (0.55, 0.4, 0.22), 0.35, metal=0.6)
for nm, sz, off in (("mf_t", (0.04, MW_ + 0.08, 0.04), (0, 0, MH_ / 2 + 0.02)), ("mf_b", (0.04, MW_ + 0.08, 0.04), (0, 0, -MH_ / 2 - 0.02)),
                    ("mf_l", (0.04, 0.04, MH_), (0, -MW_ / 2 - 0.02, 0)), ("mf_r", (0.04, 0.04, MH_), (0, MW_ / 2 + 0.02, 0))):
    R_(box(nm, sz, tuple(MIR + Vector((-0.008, 0, 0)) + Vector(off)), mfr_m, bevel=0.008))
# devor soati (o'ng devor): mahalliy old = -Y, tepa = +Z; mil burilishi +Y atrofida = soat yo'nalishi
CLK = Vector((X1 - 0.025, -0.62, 1.95)); CR = 0.17
clk = R_(empty("clock", tuple(CLK))); clk.rotation_euler = (0, 0, R(-90))
cyl("clk_rim", CR + 0.018, 0.045, (0, 0, 0), mat("clk_rim_m", (0.05, 0.05, 0.055), 0.3, metal=0.7), rot=(90, 0, 0), parent=clk, verts=96)
cyl("clk_face", CR, 0.05, (0, -0.002, 0), mat("clk_face_m", (0.95, 0.94, 0.9), 0.4), rot=(90, 0, 0), parent=clk, verts=96)
ink_m = mat("clk_ink", (0.02, 0.02, 0.02), 0.4)
for i in range(60):
    a = R(6 * i); big = i % 5 == 0
    L_ = 0.026 if big else 0.011; W_ = 0.007 if big else 0.0025; rr = CR - 0.012 - L_ / 2
    t_ = box(f"clk_tick{i}", (W_, 0.002, L_), (rr * math.sin(a), -0.0265, rr * math.cos(a)), ink_m, parent=clk)
    t_.rotation_euler = (0, a, 0)
for h in range(1, 13):
    a = R(30 * h); rr = CR - 0.06
    text_obj(f"clk_num{h}", str(h), (rr * math.sin(a), -0.027, rr * math.cos(a)), (90, 0, 0), 0.034, ink_m, parent=clk)
hands = {}
for nm, ln, w, th, col, y in (("hour", 0.085, 0.011, 0.003, (0.02, 0.02, 0.02), -0.029), ("min", 0.125, 0.008, 0.003, (0.02, 0.02, 0.02), -0.032),
                              ("sec", 0.14, 0.0028, 0.002, (0.75, 0.02, 0.02), -0.035)):
    pv = empty(f"clk_{nm}", (0, y, 0), clk)
    hm = mat(f"clk_{nm}_m", col, 0.35)
    box(f"clk_{nm}_b", (w, th, ln), (0, 0, ln / 2 - 0.018), hm, parent=pv)
    hands[nm] = pv
cyl("clk_pin", 0.007, 0.012, (0, -0.037, 0), mat("clk_pin_m", (0.75, 0.02, 0.02), 0.3), rot=(90, 0, 0), parent=clk)
hands["hour"].rotation_euler = (0, R(30 * 10 + 5), 0); hands["min"].rotation_euler = (0, R(6 * 10), 0)
# sekund mili: har 24 kadrda chiqillaydi; "tick" kadrida birinchi soniya ~1.3 s "qotib" turadi
TICKS = [f for f in range(5, END, 24) if f <= S["tick"][0]] + list(range(F_STUCK1, END + 24, 24))
sec = hands["sec"]; s_ = 12
sec.rotation_euler = (0, R(6 * s_), 0); sec.keyframe_insert("rotation_euler", frame=1)
for f in TICKS:
    sec.rotation_euler = (0, R(6 * s_), 0); sec.keyframe_insert("rotation_euler", frame=f)
    s_ += 1
    sec.rotation_euler = (0, R(6 * s_ + 1.2), 0); sec.keyframe_insert("rotation_euler", frame=f + 1)
    sec.rotation_euler = (0, R(6 * s_), 0); sec.keyframe_insert("rotation_euler", frame=f + 2)
interp(sec, "LINEAR")
print("TICKS", TICKS)

# ======================================================================
# 2) MEGAN: yuradi (Female_Walk) -> to'xtaydi (Catwalk_Walk_Stop_2) -> oyna oldida turadi (Catwalk_Idle),
#    "Yo'q" da boshini chayqaydi, soatga qaraydi (Looking_Right). Ko'z harakati: Body ko'z orollariga shape key.
# ======================================================================
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
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften(mmeshes, 0.48)
body = next(o for o in mmeshes if o.name.endswith("Body"))
# --- ko'z soqqalari (dam holatida, dunyo koordinatasi): x ±0.0171..0.0461, y -0.1356..-0.123, z 1.6064..1.6356
bpy.context.view_layer.update()
MWB = mroot.matrix_world.inverted() @ body.matrix_world; MWBi = MWB.inverted()
seen, _n = TW._islands(body.data)
from collections import defaultdict
_isl = defaultdict(list)
for i, s in enumerate(seen): _isl[s].append(i)
EYE_PIV = {}
for s, idx in _isl.items():
    pts = [MWB @ body.data.vertices[i].co for i in idx]
    c = sum(pts, Vector()) / len(pts)
    if len(idx) < 1000 and 1.6 < c.z < 1.64 and 0.015 < abs(c.x) < 0.05 and c.y < -0.11:
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        a_ = (max(xs) - min(xs)) / 2; h_ = max(ys) - min(ys); r_ = (a_ * a_ + h_ * h_) / (2 * h_)
        EYE_PIV[s] = (Vector(((max(xs) + min(xs)) / 2, min(ys) + r_, (max(zs) + min(zs)) / 2)), idx)
print("EYE_PIV", {k: tuple(round(x, 4) for x in v[0]) for k, v in EYE_PIV.items()})
GZ_MAX = 22.0
body.shape_key_add(name="Basis")
GZK = {}
for nm, sgn in (("gazeL", 1), ("gazeR", -1)):
    kb = body.shape_key_add(name=nm, from_mix=False); kb.value = 0.0
    rot = Matrix.Rotation(R(GZ_MAX * sgn), 4, "Z")
    for s, (pv, idx) in EYE_PIV.items():
        for i in idx:
            pw = MWB @ body.data.vertices[i].co
            kb.data[i].co = MWBi @ (pv + (rot @ (pw - pv).to_4d()).to_3d())
    GZK[nm] = kb
# sakrashlar: (kadr, burchak°) — kadrda boshlanib 2 kadrda yetadi (+ = Megan'ning chapi)
GAZE = [(217, 15), (246, -15), (292, 0), (347, 18), (361, -18), (374, 12), (386, 0), (498, 9), (540, -17),
        (562, 14), (575, -14), (586, 0), (739, -21), (826, -8), (838, -21)]
def gaze_val(y):
    return max(0.0, y) / GZ_MAX, max(0.0, -y) / GZ_MAX
def gkey(f, y):
    l, r = gaze_val(y)
    GZK["gazeL"].value = l; GZK["gazeL"].keyframe_insert("value", frame=f)
    GZK["gazeR"].value = r; GZK["gazeR"].keyframe_insert("value", frame=f)
cur = 0.0; gkey(1, 0.0)
for f, y in GAZE:
    gkey(f, cur); gkey(f + 2, y); cur = y
interp(body.data.shape_keys, "LINEAR")
def gaze_at(f):
    """kadrdagi burchak (rentgen ko'z olmalari uchun)"""
    y = 0.0
    for g, v in GAZE:
        if f >= g + 2: y = v
        elif f > g: y = y + (v - y) * (f - g) / 2.0
    return y

def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
LOWER = ("Hips", "UpLeg", "Leg", "Foot", "ToeBase", "Toe_End")
def upper(act, drop=()):
    a = act.copy(); a.name = act.name + "_upper" + "".join(drop); a.use_fake_user = True
    for fc in list(mc._fcurves(a)):
        b = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        if any(b.endswith(s) for s in LOWER) or any(d in b for d in drop): mc._channelbag_remove(a, fc)
    return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0, infl=None, rev=False, hold=False):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=hold, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo; s.use_reverse = rev
    if infl is not None:
        s.use_animated_influence = True; s.influence = infl; s.keyframe_insert("influence", frame=start)
    return s
def hips_fwd(act):
    """Hips oldinga siljishi (asl harakatdan, metr) — root'ni oyoq sirpanmasligi uchun shu bilan suramiz"""
    fc = next(fc for fc in mc._fcurves(act) if fc.data_path == 'pose.bones["mixamorig:Hips"].location' and fc.array_index == 2)
    return lambda s: fc.evaluate(s) * 0.01

MY = 0.5                       # yurish chizig'i (y)
X_END = 1.80                   # oyna oldida to'xtash joyi (root x)
WSPD = 0.7
W0, W1 = 55, 131               # yurish, keyin to'xtash
WALK = A_("Female_Walk.fbx"); WALK_F = hips_fwd(A_("Female_Walk.fbx", inplace=False))
STOP = A_("Catwalk_Walk_Stop_2.fbx"); STOP_F = hips_fwd(A_("Catwalk_Walk_Stop_2.fbx", inplace=False))
IDLE = A_("Catwalk_Idle.fbx")
SHAKE = upper(A_("Annoyed_Head_Shake.fbx"))
LOOKR = upper(A_("Looking_Right.fbx"))
wa, wb = WALK.frame_range; sa, sb = STOP.frame_range
cyc = (WALK_F(wb) - WALK_F(wa))
def walk_d(f):
    s = (f - W0) * WSPD * 30.0 / 24.0
    k, r_ = divmod(s, wb - wa)
    return k * cyc + WALK_F(wa + r_) - WALK_F(wa)
STOP_LEN = int(round((sb - sa) * 0.8))
def stop_d(f):
    s = min(sb, sa + (f - W1) * 30.0 / 24.0)
    return STOP_F(s) - STOP_F(sa)
D_TOT = walk_d(W1) + stop_d(W1 + STOP_LEN)
X_START = X_END - D_TOT
print("WALK", round(cyc, 3), "D_TOT", round(D_TOT, 3), "X_START", round(X_START, 3))
def root_x(f):
    if f <= W0: return X_START
    if f <= W1: return X_START + walk_d(f)
    return X_START + walk_d(W1) + stop_d(min(f, W1 + STOP_LEN))
mroot.rotation_euler = (0, 0, R(90)); mroot.keyframe_insert("rotation_euler", frame=1)
for f in range(1, W1 + STOP_LEN + 2):
    mroot.location = (root_x(f), MY, 0.0); mroot.keyframe_insert("location", frame=f)
interp(mroot, "LINEAR")
strip(meg, IDLE, -40, src=(1, 60), hold=True)
strip(meg, WALK, W0, repeat=(W1 - W0 + 4) / ((wb - wa) * 0.8 / WSPD), speed=WSPD, bi=8)
strip(meg, STOP, W1, bi=4)
ID0 = W1 + STOP_LEN
strip(meg, IDLE, ID0, repeat=(END - ID0 + 10) / ((300) * 0.8), bi=6)
strip(meg, SHAKE, 297, bi=8, bo=8)
strip(meg, LOOKR, 735, bi=5, hold=True)
for o in mmeshes: vis(o, MEGR, recursive=False)

headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
eyeMid = empty("eyeMid", (0.0, 0.088, 0.135), headE)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items()}
FACE0 = {n: wpos(faceT, a) for n, (a, b) in S.items()}
print("FACE", {k: tuple(round(x, 3) for x in v) for k, v in FACE.items()})
def mirror_pt(p):
    return Vector((2 * MIR.x - p.x, p.y, p.z))

# ======================================================================
# 3) RENTGEN: shaffof Megan, bosh suyagi, ko'z olmalari (sakraydi), ko'rish nurlari, nervlar, miya, ko'rish qobig'i
# ======================================================================
xbody = xr_mat("xr_body")
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name or "Sneakers" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
for o in mmeshes: vis(o, MEGR, recursive=False)
def bone_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.2)
    gl = value_node(m, "glow", 1.4)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.82, 0.92, 1.0, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.06), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.6), 0.08, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
skullE = empty("skullE", (0, -0.012, 0.034), headE); skullE.rotation_euler = (R(-90), 0, 0); skullE.scale = (0.8,) * 3
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=BK + "49c13194_u.glb")
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.type == "MESH" and o.name.startswith("Text"): bpy.data.objects.remove(o, do_unlink=True)
skm = bone_mat("xr_bone")
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.parent is None: o.parent = skullE
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(skm)
vis(skullE, XR)
EYEB = []
beam_m = mat("gaze_beam", (0.4, 0.9, 1.0), 0.5, emit=3.0, alpha=0.5)
for sx_, nm in ((1, "L"), (-1, "R")):
    c = empty(f"xeye{nm}", (sx_ * TW.EYE_H[0], TW.EYE_H[1], TW.EYE_H[2] - 0.0125), headE)
    b_, red_ = EY.build_eyeball(f"xeyeball{nm}", 0.0122, "human", c)
    b_.rotation_euler = (R(-90), 0, 0)
    bm_ = cyl(f"xbeam{nm}", 0.0012, 0.6, (0, 0, 0.312), beam_m, parent=c, verts=12)
    EYEB.append((c, b_, bm_))
xeye_m = EYEB[0][1].data.materials[0]
for c, b_, bm_ in EYEB:
    b_.data.materials.clear(); b_.data.materials.append(xeye_m)
_bb = xeye_m.node_tree.nodes.get("Principled BSDF")
if _bb: _bb.inputs["Emission Color"].default_value = (1, 1, 1, 1); _bb.inputs["Emission Strength"].default_value = 0.6
X_SPAN = (S["jump"][0], S["off"][1])
for f in range(X_SPAN[0] - 1, X_SPAN[1] + 2):
    y = gaze_at(f)
    for c, b_, bm_ in EYEB:
        c.rotation_euler = (0, R(y), 0); c.keyframe_insert("rotation_euler", frame=f)
for c, b_, bm_ in EYEB:
    vis(c, XR)
    vis(bm_, [S["jump"]], recursive=False)
# nishon nuqtalari (oyna tomonda, ko'z oldida): sakrash nuqtalari
tgt_m = mat("gaze_tgt", (1.0, 0.8, 0.3), 0.5, emit=6.0)
for k, y in enumerate((18, -18, 12)):
    t_ = sphere(f"gtgt{k}", 0.006, (0.6 * math.sin(R(y)), 0.088, 0.135 + 0.6 * math.cos(R(y))), tgt_m, sub=2, parent=headE)
    vis(t_, [S["jump"]])
xb_m = brain_mat2("xbrain_m", 0.7)
xbrain, _ = P.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, XR)
# ko'rish qobig'i (ensa): yonadi / o'chadi
vc_m = mat("vcortex", (1.0, 0.55, 0.2), 0.5, emit=0.0)
vcb = vc_m.node_tree.nodes["Principled BSDF"]
vcx = sphere("vcortex", 0.03, (0, 0.105, -0.055), vc_m, scale=(1.3, 0.8, 0.45), sub=3, parent=headE)
vis(vcx, XR)
def vc_key(f, e):
    vcb.inputs["Emission Strength"].default_value = e; vcb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
nerve_ms = []; nerves = []
for sx_ in (1, -1):
    pts = [(sx_ * 0.033, 0.088, 0.104), (sx_ * 0.026, 0.084, 0.085), (sx_ * 0.008, 0.08, 0.07), (sx_ * 0.012, 0.085, 0.045),
           (sx_ * 0.026, 0.095, 0.01), (sx_ * 0.03, 0.105, -0.03), (sx_ * 0.02, 0.108, -0.055)]
    m = train_mat(f"onerve{sx_}", col=(0.9, 0.75, 0.4), pcol=(1.0, 0.6, 0.25)); nerve_ms.append(m)
    t_ = P.tube(f"onerve{sx_}", pts, 0.0024, m, headE, taper=[1.0] * len(pts)); nerves.append(t_)
for t_ in nerves: vis(t_, XR, recursive=False)
# impulslar: "brain" va "off" kadrlarida uzluksiz oqadi; ko'z sakraganda (540) 14 kadr uziladi
SACC_OFF = (540, 554)
BR0 = S["brain"][0]
for m in nerve_ms:
    val_key(m, "count", 1, 5.0); val_key(m, "glow", 1, 0.5)
    val_key(m, "phase", 1, 0.0); val_key(m, "phase", END, (END - 1) / 7.0)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        if "phase" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
    val_key(m, "amp", 1, 6.0); val_key(m, "amp", BR0 - 1, 6.0); val_key(m, "amp", BR0, 22.0)
    val_key(m, "amp", SACC_OFF[0], 0.0); val_key(m, "glow", SACC_OFF[0], 0.05)
    val_key(m, "amp", SACC_OFF[1], 22.0); val_key(m, "glow", SACC_OFF[1], 0.5)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        if "amp" in fc.data_path or "glow" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
vc_key(1, 2.0); vc_key(BR0, 4.0)
for f in range(BR0 + 2, SACC_OFF[0], 6): vc_key(f, 5.0); vc_key(f + 3, 3.0)
vc_key(SACC_OFF[0], 0.0); vc_key(SACC_OFF[1], 4.0)
interp(vc_m.node_tree, "CONSTANT")
val_key(xb_m, "glow", 1, 0.7); val_key(xb_m, "glow", SACC_OFF[0], 0.15); val_key(xb_m, "glow", SACC_OFF[1], 0.9)
interp(xb_m.node_tree, "CONSTANT")

# ======================================================================
# 4) MAKRO KO'Z (real o'lcham): qorachiq chapga-o'ngga sakraydi
# ======================================================================
MAC = V(0.0, 30.0, 1.2)
eye = EY.build_eye("meye", tuple(MAC))
eroot = eye["root"]; eball = eye["ball"]
bskin = mat("macro_skin", (0.56, 0.33, 0.25), 0.5, sss=0.3)
bskin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.002
mback = plane("macro_back", (0.5, 0.5), tuple(MAC + V(0, -0.0045, 0)), bskin, rot=(90, 0, 0))
def EL(p): return MAC + Vector(p)
cur = 0.0
eball.rotation_euler = (0, 0, 0); eball.keyframe_insert("rotation_euler", frame=1)
for f, y in ((9, 20), (20, -18), (30, 16), (41, -20), (51, 8)):
    eball.rotation_euler = (0, 0, R(cur)); eball.keyframe_insert("rotation_euler", frame=f)
    eball.rotation_euler = (0, 0, R(y)); eball.keyframe_insert("rotation_euler", frame=f + 2); cur = y
interp(eball, "LINEAR")
EY.set_key(eye, "blink", 1, 0.0); EY.set_key(eye, "blink", 56, 0.0); EY.set_key(eye, "blink", 59, 1.0); EY.set_key(eye, "blink", 61, 1.0)
vis(eroot, MACR); vis(mback, MACR)

# ======================================================================
# 5) VAQT LENTASI: qorong'i bo'shliqda kino lentasi; A kadrlar | bo'shliq | B kadrlar -> B orqaga surilib bo'shliqni to'ldiradi
# ======================================================================
FS = V(0.0, 60.0, 1.5)
film_objs = []
def F_(o): film_objs.append(o); return o
def img_mat(name, path, fallback, strength=1.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = strength
    if os.path.exists(path):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.extension = "CLIP"
        tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["UV"], t.inputs[0]); L.new(t.outputs[0], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = (*fallback, 1)
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    gl = value_node(m, "gain", 1.0); L.new(gl, em.inputs["Strength"])
    return m
FW, FH_, PITCH = 0.27, 0.48, 0.32
strip_m = mat("film_base", (0.015, 0.012, 0.01), 0.35, coat=0.6)
hole_m = mat("film_hole", (0.9, 0.85, 0.7), 0.5, emit=0.8)
NFR = 12
F_(box("film_strip", (PITCH * (NFR + 4), 0.006, FH_ + 0.16), tuple(FS + V(0, 0.004, 0)), strip_m))
for k in range(-(NFR + 4) * 2, (NFR + 4) * 2):
    for zz in (FH_ / 2 + 0.045, -FH_ / 2 - 0.045):
        F_(box(f"film_hole{k}_{zz:.2f}", (0.032, 0.002, 0.03), tuple(FS + V(k * PITCH / 4, -0.0005, zz)), hole_m))
A_m = img_mat("povA", STILL_DIR + "pov_A.png", (0.6, 0.55, 0.5))
B_m = img_mat("povB", STILL_DIR + "pov_B.png", (0.4, 0.5, 0.6))
def slot_x(i): return (i - 0.5) * PITCH
frames_ = {}
for i in range(-6, 0):
    frames_[("A", i)] = F_(plane(f"fA{i}", (FW, FH_), tuple(FS + V(slot_x(i), -0.002, 0)), A_m, rot=(90, 0, 0)))
for i in range(2, 8):
    frames_[("B", i)] = F_(plane(f"fB{i}", (FW, FH_), tuple(FS + V(slot_x(i), -0.002, 0)), B_m, rot=(90, 0, 0)))
# bo'shliq (0, 1): qora kadr + qizil yonuvchi ramka
gap_m = mat("gap_black", (0.0, 0.0, 0.0), 0.9)
gapr_m = mat("gap_red", (1.0, 0.05, 0.03), 0.5, emit=2.0)
gb_ = gapr_m.node_tree.nodes["Principled BSDF"]
gap_parts = []
for i in (0, 1):
    gap_parts.append(F_(plane(f"fgap{i}", (FW, FH_), tuple(FS + V(slot_x(i), -0.002, 0)), gap_m, rot=(90, 0, 0))))
    for nm, sz, off in (("t", (FW, 0.004, 0.008), (0, 0, FH_ / 2)), ("b", (FW, 0.004, 0.008), (0, 0, -FH_ / 2)),
                        ("l", (0.008, 0.004, FH_), (-FW / 2, 0, 0)), ("r", (0.008, 0.004, FH_), (FW / 2, 0, 0))):
        gap_parts.append(F_(box(f"fgapr{i}{nm}", sz, tuple(FS + V(slot_x(i), -0.004, 0) + V(*off)), gapr_m)))
GA0, GA1 = S["gap"]; FI0, FI1 = S["fill"]
def gr_key(f, e): gb_.inputs["Emission Strength"].default_value = e; gb_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
gr_key(1, 0.0); gr_key(GA0, 0.0)
for f in range(GA0 + 4, F_SLIDE1, 10): gr_key(f, 3.0); gr_key(f + 5, 0.6)
gr_key(F_SLIDE1, 0.0)
interp(gapr_m.node_tree, "LINEAR")
# yangi kadrning nusxalari B2 ortidan chiqib, orqaga (chapga) sirpanib 1 va 0 o'rinlarni egallaydi
fill_ = []
for i, tgt in ((0, 1), (1, 0)):
    o = F_(plane(f"fBfill{i}", (FW, FH_), tuple(FS + V(slot_x(2), -0.007 - 0.0005 * i, 0)), B_m, rot=(90, 0, 0)))
    key(o, 1, loc=tuple(FS + V(slot_x(2), -0.007 - 0.0005 * i, 0)))
    key(o, F_SLIDE0 + 6 * i, loc=tuple(FS + V(slot_x(2), -0.007 - 0.0005 * i, 0)))
    key(o, F_SLIDE1 - 6 * (1 - i), loc=tuple(FS + V(slot_x(tgt), -0.007 - 0.0005 * i, 0)))
    fill_.append(o)
for o in fill_:
    for fc in fcurves(o):
        for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "AUTO"
# "orqaga" o'qi (lenta ostida, chapga)
arrow_m = mat("arrow", (0.3, 0.8, 1.0), 0.4, emit=0.0)
ab_ = arrow_m.node_tree.nodes["Principled BSDF"]
arr = F_(empty("arrow", tuple(FS + V(slot_x(1), -0.01, -FH_ / 2 - 0.16))))
cyl("arrow_shaft", 0.008, 0.5, (0.05, 0, 0), arrow_m, rot=(0, 90, 0), parent=arr)
bpy.ops.mesh.primitive_cone_add(radius1=0.03, depth=0.07, location=(-0.235, 0, 0), rotation=(0, R(-90), 0))
_c = bpy.context.object; _c.data.materials.append(arrow_m); _c.parent = arr
def ar_key(f, e): ab_.inputs["Emission Strength"].default_value = e; ab_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
ar_key(1, 0.0); ar_key(F_SLIDE0 - 4, 0.0); ar_key(F_SLIDE0, 5.0); ar_key(F_SLIDE1 + 4, 5.0); ar_key(F_SLIDE1 + 10, 0.0)
interp(arrow_m.node_tree, "LINEAR")
# ulanishda butun lenta chaqnaydi
for m in (A_m, B_m):
    val_key(m, "gain", 1, 1.4); val_key(m, "gain", F_JOIN - 1, 1.4); val_key(m, "gain", F_JOIN + 1, 4.0); val_key(m, "gain", F_JOIN + 10, 1.5)
    interp(m.node_tree, "LINEAR")
# fon: uchib yuruvchi chang zarralari
dust_m = mat("dust", (0.6, 0.75, 1.0), 0.5, emit=2.0)
rd = random.Random(11)
for k in range(120):
    F_(sphere(f"dust{k}", rd.uniform(0.002, 0.006), tuple(FS + V(rd.uniform(-3, 3), rd.uniform(0.3, 3.0), rd.uniform(-1.5, 1.5))), dust_m, sub=1))
for o in film_objs: vis(o, FILMR)
for o in gap_parts: vis(o, [(GA0, F_SLIDE1 + 2)])

for o in room_objs: vis(o, ROOM)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def rig(name, target):
    e = empty(name + "_rig"); c = e.constraints.new("COPY_LOCATION"); c.target = target; return e
def rel_cam(name, target, lens, fstop, offsets, track=None, clip=0.003):
    r_ = rig(name, target)
    c = shot_cam(name, (0, 0, 0), track or target, lens, fstop, focus=track or target, clip=clip)
    c.parent = r_
    path_keys(c, offsets)
    return c
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002, focus=None):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    if focus is not None: c.data.dof.focus_object = None; c.data.dof.focus_distance = focus
    return c
def chest(f): return Vector((root_x(f), MY, 1.15))
# 1 ILGAK: makro ko'z, tez push-in
H0, H1 = S["hook"]
c = abs_cam("hook", [(H0, EL((0.035, -0.16, 0.012))), (H0 + 10, EL((0.02, -0.095, 0.006))), (H1, EL((0.012, -0.07, 0.004)))],
            [(H0, EL((0, -0.012, 0.0))), (H1, EL((0.0, -0.012, 0.001)))], 40, 16.0)
lens_keys(c, [(H0, 30), (H0 + 10, 40), (H1, 44)])
# 2 ko'r: poldan, keng ob'ektiv, oldidan ergashish (orqaga yuradi)
BL0, BL1 = S["blind"]
c = abs_cam("blind", [(f, chest(f) + V(0.9 - 0.3 * (f - BL0) / (BL1 - BL0), -0.95, -0.95)) for f in (BL0, (BL0 + BL1) // 2, BL1)],
            [(f, chest(f) + V(0, 0, 0.15)) for f in (BL0, (BL0 + BL1) // 2, BL1)], 16, 3.2)
shake(c, BL0, BL1, 0.006, seed=2, decay=False)
# 3 oyna: yelka ortidan push-in, oynadagi yuz aksi
MI0, MI1 = S["mirror"]
VF = mirror_pt(FACE["mirror"])
c = abs_cam("mirror", [(MI0, V(0.45, -0.05, 1.45)), (MI1, V(1.05, 0.22, 1.6))], [(MI0, VF + V(0, 0, -0.25)), (MI1, VF)], 24, 2.8)
# 4 oynadagi aksga yaqin plan: yonlama siljish
LO0, LO1 = S["look"]
FL = FACE["look"]; VL = mirror_pt(FL)
c = abs_cam("look", [(LO0, FL + V(-0.16, -0.2, 0.03)), (LO1, FL + V(-0.14, -0.13, 0.01))], [(LO0, VL + V(0, 0, 0.01)), (LO1, VL + V(0, 0, 0.01))], 70, 2.4)
# 5 yon tomondan yuz (oyna fonda), "Yo'q" da bosh chayqaladi
SA0, SA1 = S["saw"]
c = rel_cam("saw", faceT, 40, 2.0, [(SA0, V(0.3, -0.35, 0.0)), (SA1, V(0.36, -0.15, 0.02))])
# 6 rentgen: sakrash, aylanma
JU0, JU1 = S["jump"]; FJ = FACE["jump"]
c = abs_cam("jump", [(JU0, FJ + V(0.0, -0.62, 0.1)), (JU0 + 30, FJ + V(0.32, -0.52, 0.1)), (JU1, FJ + V(0.6, -0.2, 0.06))],
            [(JU0, FJ + V(0.05, 0, 0.0)), (JU1, FJ + V(0.12, 0.0, 0.0))], 28, 5.6)
# 7 POV: Megan ko'zidan (bosh ichi oldida), oyna -> soat -> divan -> oyna whip-pan
BU0, BU1 = S["blur"]
POVP = FACE["blur"] + V(0.07, 0.0, 0.01)
c = shot_cam("blur", tuple(POVP), None, 24)
YAWS = [(BU0, 0), (409, 0), (413, -69), (436, -69), (440, 72), (458, 72), (462, 0)]
for f, y in YAWS:
    c.rotation_euler = (R(90), 0, R(y - 90)); c.keyframe_insert("rotation_euler", frame=f)
# 10 POV: sakrashda qop-qora (montajda)
PO0, PO1 = S["povoff"]
c2 = shot_cam("povoff", tuple(FACE["povoff"] + V(0.07, 0.0, 0.01)), None, 26)
for f, y in ((PO0, 0), (562, 4), (565, -40), (575, -38), (578, 30), (PO1, 34)):
    c2.rotation_euler = (R(90 + 1.5 * math.sin(f * 0.7)), R(1.5 * math.sin(f * 0.5)), R(y - 90)); c2.keyframe_insert("rotation_euler", frame=f)
# 8 miya: yondan yonlama siljish, biroz qiyshayadi
BR0_, BR1 = S["brain"]; FB = FACE["brain"]
c = abs_cam("brain", [(BR0_, FB + V(0.5, -0.3, 0.14)), (BR1, FB + V(0.52, 0.22, 0.12))], [(BR0_, FB + V(0.0, 0.0, 0.02)), (BR1, FB + V(0.0, 0.0, 0.02))], 30, 5.6)
# 9 o'chish: yaqin, crash zoom
OF0, OF1 = S["off"]; FO_ = FACE["off"]
c = abs_cam("off", [(OF0, FO_ + V(0.45, -0.32, 0.08)), (539, FO_ + V(0.33, -0.25, 0.06)), (542, FO_ + V(0.24, -0.18, 0.05)), (OF1, FO_ + V(0.22, -0.16, 0.05))],
            [(OF0, FO_ + V(0.0, 0.0, 0.0)), (OF1, FO_ + V(0.02, -0.01, 0.0))], 30, 5.6)
lens_keys(c, [(OF0, 28), (539, 32), (542, 44), (OF1, 46)]); shake(c, 541, 551, 0.008, seed=9)
# 11 bo'shliq: lenta bo'ylab siljish
c = abs_cam("gap", [(GA0, FS + V(slot_x(-4), -0.85, 0.12)), (GA1, FS + V(slot_x(0.2), -0.62, 0.05))],
            [(GA0, FS + V(slot_x(-3), 0, 0)), (GA1, FS + V(slot_x(0.6), 0, 0))], 28, 4.0)
# 12 to'ldirish: crash zoom, keyin orqaga chekinish
c = abs_cam("fill", [(FI0, FS + V(slot_x(0.5) + 0.35, -0.95, 0.2)), (FI0 + 10, FS + V(slot_x(0.5) + 0.15, -0.6, 0.08)), (F_SLIDE1, FS + V(slot_x(0.8), -1.0, 0.04)),
                     (FI1, FS + V(slot_x(0.5) - 0.3, -1.25, -0.1))],
            [(FI0, FS + V(slot_x(0.5), 0, 0)), (F_SLIDE1, FS + V(slot_x(0.6), 0, 0)), (FI1, FS + V(slot_x(0.5), 0, 0))], 30, 4.0)
lens_keys(c, [(FI0, 22), (FI0 + 10, 30), (F_SLIDE1, 26), (FI1, 22)]); shake(c, F_JOIN, F_JOIN + 10, 0.01, seed=12)
# 13 soatga qarash: past burchak, yelka ortidan push-in
CL0, CL1 = S["clock"]; FC_ = FACE["clock"]
c = abs_cam("clock", [(CL0, FC_ + V(-0.75, 0.55, -0.55)), (CL1, FC_ + V(-0.5, 0.36, -0.3))], [(CL0, (CLK + FC_) / 2 + V(0, 0, -0.05)), (CL1, CLK * 0.6 + FC_ * 0.4)], 20, 3.2)
# 14 makro soat: juda yaqin, keng ob'ektiv
TI0, TI1 = S["tick"]
bpy.context.view_layer.update()
def CL(p): return clk.matrix_world @ Vector(p)      # soat mahalliy (-Y old, +Z tepa) -> dunyo
c = abs_cam("tick", [(TI0, CL((0.09, -0.13, -0.08))), (TI1, CL((0.05, -0.085, -0.045)))], [(TI0, CL((0.0, -0.03, 0.02))), (TI1, CL((0.0, -0.03, 0.03)))], 18, 6.0)
shake(c, F_STUCK1, F_STUCK1 + 5, 0.003, seed=14)
# 15 soxta vaqt: yuzga yaqin, oldingi planda xira soat; ko'zga crash zoom
FK0, FK1 = S["fake"]; FF = FACE["fake"]
dirc = (CLK - FF).normalized()
c = rel_cam("fake", faceT, 45, 2.0, [(FK0, dirc * 0.55 + V(0, 0, -0.05)), (845, dirc * 0.42 + V(0, 0, -0.03)), (849, dirc * 0.24 + V(0, 0, -0.01)), (FK1, dirc * 0.22)],
            track=eyeMid)
lens_keys(c, [(FK0, 42), (845, 46), (849, 70), (FK1, 75)]); shake(c, 849, 860, 0.005, seed=15)
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        if "rotation" in fc.data_path and n in ("blur", "povoff"): continue
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
for n in ("blur", "povoff"):
    for fc in fcurves(CAMS[n]):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 7) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_env = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_env.inputs[0])
bg_col = N.new("ShaderNodeBackground")
a1 = N.new("ShaderNodeAddShader"); L.new(bg_env.outputs[0], a1.inputs[0]); L.new(bg_col.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WORLD = {"room": (1.0, (0, 0, 0), 0.0), "xr": (0.0, (0.004, 0.01, 0.028), 1.0), "mac": (0.0, (0.0, 0.0, 0.0), 0.0),
         "film": (0.0, (0.005, 0.008, 0.018), 1.0)}
def world_of(n):
    return "room" if n in ROOMN else "xr" if n in XRN else "mac" if n in MACN else "film"
for f, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
# xona (kunduz): deraza ortidan quyosh, derazadan yumshoq yorug'lik, shift, yuz uchun to'ldiruvchi
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(52), 0, R(200)); sun.data.angle = R(2.5); sun.data.color = (1.0, 0.93, 0.82)
for f, e in lights_for(ROOM, 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("win_soft", (WC.x, Y0 + 0.15, WC.z), 2.0, (0.85, 0.92, 1.0), lights_for(ROOM, 120.0), target=empty("wsT", (0.5, 1.0, 1.0)))
area("ceil_fill", (0.0, 0.5, 2.6), 2.2, (1.0, 0.95, 0.88), lights_for(ROOM, 40.0), target=empty("cfT", (0, 0.5, 0)))
area("face_fill", (1.2, -0.6, 1.9), 0.6, (1.0, 0.95, 0.9), lights_for(rng("mirror", "look", "saw", "clock", "fake"), 18.0), target=FT)
area("face_rim", (0.9, 1.4, 2.0), 0.6, (0.85, 0.92, 1.0), lights_for(rng("look", "saw", "fake"), 14.0), target=FT)
# rentgen
HT = empty("xrT"); clh = HT.constraints.new("COPY_LOCATION"); clh.target = headE
MEG_ST = V(X_END, MY, 0)
area("X_key", tuple(MEG_ST + V(-0.6, -1.5, 2.0)), 1.0, (0.8, 0.9, 1.0), lights_for(XR, 25.0), target=HT)
area("X_rim", tuple(MEG_ST + V(-1.0, 1.0, 1.8)), 1.0, (0.3, 0.55, 1.0), lights_for(XR, 30.0), target=HT)
# makro
MT = empty("macroT", tuple(EL((0, -0.012, 0))))
area("M_key", tuple(EL((-0.12, -0.2, 0.16))), 0.18, (1.0, 0.95, 0.9), lights_for(MACR, 5.0), target=MT)
area("M_fill", tuple(EL((0.16, -0.18, -0.06))), 0.2, (0.9, 0.93, 1.0), lights_for(MACR, 2.0), target=MT)
area("M_top", tuple(EL((0.02, -0.1, 0.2))), 0.1, (1.0, 0.97, 0.92), lights_for(MACR, 2.5), target=MT)
# lenta
FTT = empty("filmT", tuple(FS))
area("F_key", tuple(FS + V(0.4, -1.2, 1.0)), 1.2, (0.85, 0.9, 1.0), lights_for(FILMR, 30.0), target=FTT)
area("F_rim", tuple(FS + V(-0.8, 0.8, 0.8)), 1.0, (0.3, 0.5, 1.0), lights_for(FILMR, 25.0), target=FTT)

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
sc.cycles.glossy_bounces = 4; sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
# POV whip-pan: kuchliroq xiralik
try:
    for f, v in ((1, 0.5), (BU0, 1.4), (BU1 + 1, 0.5), (PO0, 1.2), (PO1 + 1, 0.5)):
        r.motion_blur_shutter = v; r.keyframe_insert("motion_blur_shutter", frame=f)
    interp(sc, "CONSTANT", "render.motion_blur_shutter")
except Exception as e:
    print("shutter keyframe yo'q:", e)
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = False
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("PROBE"): exec(open(os.environ["PROBE"]).read())
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    if os.environ.get("STILLS"):
        os.makedirs(STILL_DIR, exist_ok=True); r.use_motion_blur = False; r.use_overwrite = True
        for nm, f in (("pov_A", 400), ("pov_B", 425)):
            sc.frame_set(f); sc.camera = CAMS["blur"]; r.filepath = STILL_DIR + nm + ".png"; bpy.ops.render.render(write_still=True)
        sys.exit(0)
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
