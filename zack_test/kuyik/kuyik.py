# Kuyikka tish pastasi — Zack D. Films uslubida 39.5 s video (948 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, zack_test/ishqalash/ishqalash.py (xona, kamera/yorug'lik yordamchilari),
# teri kesimi / barmoq / teri materiali / quvurlar: zack_test/burish/parts.py
# Assetlar: zack_test/tools/get_kuyik.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/kuyik/kuyik.py --render
# Sinov:  FRAMES=40,70,130,200,280 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 948
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (63, "touch"), (85, "paste"), (165, "deeper"), (243, "trapped"), (311, "escape"), (377, "smear"),
         (458, "film"), (559, "down"), (677, "cook"), (759, "menthol"), (832, "nerve"), (911, "scar")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOMN = ("hook", "smear")
MACN = ("touch", "paste", "scar")
CUTN = ("deeper", "trapped", "escape", "film", "down", "menthol", "nerve")
CELLN = ("cook",)
ROOM = rng(*ROOMN); MACR = rng(*MACN); CUTR = rng(*CUTN); CELLR = rng(*CELLN)
F_CONTACT = 68      # "kuydirib" — dazmol qo'lga tegadi
F_DEEP = 205        # "chuqurlashtirib"
F_FILM = 474        # "plyonka" atrofida (21.7 s)
F_COOK = 717        # "pishirish"
F_BURN = 899        # "kuydirib" (37.4 s)

# ---------------- yordamchilar (ishqalash.py dan) ----------------
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
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3
        for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.scale = scale; o.location = loc; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
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
def ckey(idb, mode="CONSTANT", path=None): interp(idb, mode, path)
def V(*a): return Vector(a)
def ease(t): return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def clamp01(x): return max(0.0, min(1.0, x))

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

def bake_path(o, frames, fn, scale_fn=None):
    """o.location (va scale) ni har kadr uchun fn(f) dan tez yozish (foreach_set)"""
    o.location = fn(frames[0]); o.keyframe_insert("location", frame=frames[0])
    if scale_fn: o.scale = (scale_fn(frames[0]),) * 3; o.keyframe_insert("scale", frame=frames[0])
    fcs = {(fc.data_path, fc.array_index): fc for fc in fcurves(o)}
    pts = [fn(f) for f in frames]
    for i in range(3):
        fc = fcs[("location", i)]; fc.keyframe_points.clear(); fc.keyframe_points.add(len(frames))
        co = []
        for f, p in zip(frames, pts): co += [f, p[i]]
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * len(frames))   # LINEAR
        fc.update()
    if scale_fn:
        ss = [scale_fn(f) for f in frames]
        for i in range(3):
            fc = fcs[("scale", i)]; fc.keyframe_points.clear(); fc.keyframe_points.add(len(frames))
            co = []
            for f, s in zip(frames, ss): co += [f, s]
            fc.keyframe_points.foreach_set("co", co)
            fc.keyframe_points.foreach_set("interpolation", [1] * len(frames))
            fc.update()

def outline_mesh(name, pts2d, z0, z1, m, parent=None, bevel=0.0):
    """2D kontur (x, y) dan z0..z1 qalinlikdagi prizma (dazmol tagligi, taxta)"""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts2d]
    top = [bm.verts.new((x, y, z1)) for x, y in pts2d]
    bm.faces.new(list(reversed(bot))); bm.faces.new(top)
    n = len(pts2d)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((bot[i], bot[j], top[j], top[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3; bv.limit_method = "ANGLE"
        for p in me.polygons: p.use_smooth = True
        o.data.shade_auto_smooth() if hasattr(o.data, "shade_auto_smooth") else None
    if parent: o.parent = parent
    return o

def iron_outline(L=0.26, W=0.13, n=40):
    """dazmol tagligi: orqasi to'g'ri, oldi uchli (uchi +X da)"""
    pts = []
    for i in range(n + 1):
        t = i / n                                   # 0 orqa-o'ng .. 1 uch
        x = -L * 0.42 + L * t
        w = W / 2 * (1 - t ** 2.2) ** 0.55
        pts.append((x, -w))
    for i in range(n - 1, -1, -1):
        t = i / n; x = -L * 0.42 + L * t; w = W / 2 * (1 - t ** 2.2) ** 0.55
        pts.append((x, w))
    return pts[:-1] if pts[0] == pts[-1] else pts

def curve_tube(name, pts, r, m, parent=None, res=12):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 4
    cu.resolution_u = res; cu.use_fill_caps = True
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1.0)
    sp.use_endpoint_u = True; sp.order_u = 3
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(m)
    if parent: o.parent = parent
    return o

def build_iron(name, parent=None, hot=None):
    g = empty(name, (0, 0, 0), parent)
    sole_m = mat(name + "_sole", (0.8, 0.8, 0.82), 0.12, metal=1.0)
    if hot is not None:      # qizigan taglik: chetida to'q sariq emissiya
        b = sole_m.node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Color"].default_value = (1.0, 0.35, 0.08, 1); b.inputs["Emission Strength"].default_value = hot
    body_m = mat(name + "_body", (0.06, 0.28, 0.7), 0.25, coat=0.8)
    white_m = mat(name + "_white", (0.9, 0.9, 0.92), 0.3, coat=0.5)
    ol = iron_outline()
    outline_mesh(name + "_sole", ol, 0.0, 0.012, sole_m, g, bevel=0.003)
    ol2 = [(x * 0.97, y * 0.97) for x, y in ol]
    outline_mesh(name + "_body", ol2, 0.012, 0.05, body_m, g, bevel=0.012)
    ol3 = [(x * 0.8 - 0.01, y * 0.75) for x, y in ol]
    outline_mesh(name + "_top", ol3, 0.05, 0.062, white_m, g, bevel=0.005)
    curve_tube(name + "_handle", [(-0.1, 0, 0.055), (-0.1, 0, 0.12), (-0.04, 0, 0.13), (0.06, 0, 0.12), (0.1, 0, 0.06)], 0.013, white_m, g)
    for i in range(6):          # bug' teshiklari
        a = i / 5
        cyl(f"{name}_hole{i}", 0.003, 0.002, (-0.05 + 0.12 * a, (0.025 if i % 2 else -0.025) * (1 - a * 0.6), -0.0005), mat(name + "_hole", (0.02, 0.02, 0.02), 0.5), parent=g, verts=12)
    curve_tube(name + "_cord", [(-0.11, 0, 0.06), (-0.2, 0.02, 0.05), (-0.32, 0.06, 0.0), (-0.5, 0.1, -0.05)], 0.004, mat(name + "_cord_m", (0.85, 0.85, 0.85), 0.5), g)
    return g, sole_m

# ======================================================================
# 1) XONA (kunduzi): dazmol taxtasi, dazmol, ko'ylak, divan, deraza
# ======================================================================
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.95, 0.9, 0.82))
X0, X1, Y0, Y1, HZ_ = -2.4, 2.4, -2.2, 2.4, 2.7
room_objs = []
def R_(o): room_objs.append(o); return o
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.92, 0.92, 0.9), 0.8)))
R_(box("wall_L", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_B", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
# old devorda (Megan orqasida, +Y) deraza: kunduzgi yorug'lik
WX0, WX1, WZ0, WZ1 = -1.1, 0.9, 0.9, 2.3
R_(box("wall_F1", (WX0 - X0, 0.1, HZ_), ((X0 + WX0) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
R_(box("wall_F2", (X1 - WX1, 0.1, HZ_), ((WX1 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
R_(box("wall_F3", (WX1 - WX0, 0.1, WZ0), ((WX0 + WX1) / 2, Y1 + 0.05, WZ0 / 2), wall_m))
R_(box("wall_F4", (WX1 - WX0, 0.1, HZ_ - WZ1), ((WX0 + WX1) / 2, Y1 + 0.05, (WZ1 + HZ_) / 2), wall_m))
frame_m = mat("win_frame", (0.94, 0.94, 0.92), 0.4)
WC = Vector(((WX0 + WX1) / 2, Y1 + 0.05, (WZ0 + WZ1) / 2)); WW, WH = WX1 - WX0, WZ1 - WZ0
for nm, sz, off in (("wf_t", (WW + 0.04, 0.12, 0.05), (0, 0, WH / 2)), ("wf_b", (WW + 0.04, 0.2, 0.06), (0, -0.05, -WH / 2)),
                    ("wf_l", (0.05, 0.12, WH), (-WW / 2, 0, 0)), ("wf_r", (0.05, 0.12, WH), (WW / 2, 0, 0)),
                    ("wf_m", (0.04, 0.08, WH), (0, 0, 0))):
    R_(box(nm, sz, tuple(WC + Vector(off)), frame_m))
for x in (WX0 - 0.25, WX1 + 0.25):
    c_ = R_(box("curtain", (0.45, 0.06, 2.4), (x, Y1 - 0.08, 1.3), mat("curtain_m", (0.88, 0.84, 0.72), 0.9, sss=0.1)))
    d_ = c_.modifiers.new("wave", "WAVE"); d_.height = 0.04; d_.width = 0.12; d_.narrowness = 1; d_.use_y = False; d_.speed = 0
R_(box("baseboard", (X1 - X0, 0.03, 0.1), (0, Y0 + 0.015, 0.05), frame_m))
R_(import_gltf(PH + "Sofa_01/Sofa_01.gltf", (1.3, Y0 + 0.55, 0), 180, 1.0))
R_(import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (1.3, -0.9, 0), 0, 1.0))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.0, Y0 + 0.4, 0), 20, 1.25))
R_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (1.6, Y1 - 0.4, 0), 70, 1.0))
R_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-1.0, Y0 + 0.03, 1.5), 180, 1.3))
R_(import_gltf(PH + "Shelf_01/Shelf_01.gltf", (X0 + 0.02, 0.6, 0), 90, 1.0))
R_(import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X0 + 0.15, 0.4, 1.03), 90, 1.0))
R_(plane("rug", (2.2, 1.6), (0.9, -1.0, 0.004), mat("rug", (0.55, 0.42, 0.3), 0.95)))

# dazmol taxtasi: uzun o'qi X bo'ylab, uchi +X da
BRD = Vector((0.0, -0.42, 0.88))
cover_m = bpy.data.materials.new("board_cover"); cover_m.use_nodes = True
N = cover_m.node_tree.nodes; L = cover_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 60.0
ck.inputs["Color1"].default_value = (0.55, 0.6, 0.65, 1); ck.inputs["Color2"].default_value = (0.75, 0.78, 0.8, 1)
L.new(tc.outputs["Object"], ck.inputs["Vector"]); L.new(ck.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.9
bol = [(x * 4.6, y * 2.8) for x, y in iron_outline(0.26, 0.13, 30)]
board = R_(outline_mesh("board", bol, -0.025, 0.0, cover_m, bevel=0.01)); board.location = BRD + V(0.05, 0, 0)
leg_m = mat("leg_m", (0.75, 0.75, 0.78), 0.3, metal=0.9)
for sx in (-1, 1):
    for sy in (-1, 1):
        R_(cyl(f"bleg{sx}{sy}", 0.011, 1.25, (BRD.x + 0.05 + sx * 0.0, BRD.y + sy * 0.1, 0.44), leg_m, rot=(0, sx * 38, 0)))
# ko'ylak (taxta ustida)
shirt_m = bpy.data.materials.new("shirt"); shirt_m.use_nodes = True
N = shirt_m.node_tree.nodes; L = shirt_m.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.42, 0.62, 0.86, 1); b.inputs["Roughness"].default_value = 0.85; b.inputs["Sheen Weight"].default_value = 0.6
tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 900.0; wv.bands_direction = "X"
L.new(tc.outputs["Object"], wv.inputs["Vector"]); bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15
L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=40, size=1); shirt = bpy.context.object; shirt.name = "shirt"
for v in shirt.data.vertices:
    v.co.x *= 0.62; v.co.y *= 0.4
    v.co.z = 0.004 + 0.003 * math.sin(v.co.x * 40 + v.co.y * 13) * math.sin(v.co.y * 30)
shirt.data.materials.append(shirt_m); shirt.location = BRD + V(0.02, 0, 0.0)
for p in shirt.data.polygons: p.use_smooth = True
R_(shirt)
# dazmol (xona)
IRON0 = BRD + V(-0.2, 0.0, 0.004)
iron, _ = build_iron("iron")
R_(iron)
IRON_X = [(1, -0.26), (14, -0.06), (27, -0.24), (40, -0.04), (52, -0.2), (62, 0.02)]
for f, dx in IRON_X: key(iron, f, loc=tuple(IRON0 + V(dx, 0.01 * math.sin(f), 0)))
key(iron, 1, rot=(0, 0, 6)); key(iron, 62, rot=(0, 0, -4))
SM0, SM1 = S["smear"]
key(iron, SM0, loc=tuple(BRD + V(-0.25, 0.04, 0.004)), rot=(0, 0, 12))    # 7-kadrda dazmol taxtada turibdi
for fc in fcurves(iron):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
    if fc.data_path == "location":
        for k in fc.keyframe_points:
            if k.co[0] >= SM0: k.interpolation = "CONSTANT"
# bug' (xona)
steam_m = bpy.data.materials.new("steam"); steam_m.use_nodes = True
N = steam_m.node_tree.nodes; L = steam_m.node_tree.links; N.remove(N["Principled BSDF"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.6
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 3
tcs = N.new("ShaderNodeTexCoord"); L.new(tcs.outputs["Object"], nz.inputs["Vector"])
dens = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"], clamp=True), 2.5), P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.5))
tr = N.new("ShaderNodeBsdfTransparent"); df = N.new("ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (1, 1, 1, 1)
mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "SUBTRACT", 1.0, dens, clamp=True), mx.inputs[0])
L.new(df.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs[0])
def puffs(name, origin_fn, frames, n, size, rise, seed, parent=None, spread=0.04):
    rnd = random.Random(seed); objs = []
    f0, f1 = frames
    for i in range(n):
        s = sphere(f"{name}{i}", 1.0, (0, 0, 0), steam_m, sub=2, parent=parent)
        b0 = f0 + rnd.uniform(-20, (f1 - f0)); life = rnd.uniform(18, 34)
        dx, dy = rnd.uniform(-spread, spread), rnd.uniform(-spread, spread)
        def pos(f, b0=b0, life=life, dx=dx, dy=dy):
            t = clamp01((f - b0) / life)
            o = origin_fn(min(max(f, f0), f1) if callable(origin_fn) else f) if callable(origin_fn) else origin_fn
            return tuple(Vector(o) + V(dx * (0.3 + t), dy * (0.3 + t), rise * t))
        def scl(f, b0=b0, life=life):
            t = (f - b0) / life
            return 0.0 if t < 0 or t > 1 else size * (0.3 + 1.2 * t) * math.sin(math.pi * min(1, t * 1.1)) ** 0.5
        bake_path(s, list(range(f0, f1 + 1)), pos, scl)
        vis(s, [(f0, f1)], recursive=False)
        objs.append(s)
    return objs
def iron_world(f):
    sc.frame_set(f); bpy.context.view_layer.update(); return iron.matrix_world.translation.copy()
IRON_W = {f: iron_world(f) for f in range(1, 63)}
room_steam = puffs("rsteam", lambda f: IRON_W[max(1, min(62, f))] + V(0.0, 0, 0.13), (1, 62), 10, 0.05, 0.35, 5)
for s in room_steam: R_(s)

# ======================================================================
# 2) MEGAN: tik turadi (Breathing_Idle), qo'llar IK bilan (dazmol / taxta, 7-kadrda pasta surtish)
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
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
MEG = Vector((-0.02, -0.05, 0.0))
mroot.location = MEG; mroot.rotation_euler = (0, 0, 0)
IDL = A_("Breathing_Idle.fbx")
s_ = mc.add_strip(meg, IDL, 1, repeat=END / ((IDL.frame_range[1] - IDL.frame_range[0]) * 0.8) + 1, blend=0)
for o in mmeshes: vis(o, ROOM, recursive=False)

def bone(n): return "mixamorig:" + n
def ik_arm(side, wrist_t, pole_t, fing_t, palm_t, palm_axis):
    pb = meg.pose.bones
    c = pb[bone(side + "ForeArm")].constraints.new("IK"); c.target = wrist_t; c.use_tail = True; c.chain_count = 2
    c.pole_target = pole_t; c.pole_angle = R(-90 if side == "Right" else -90)
    h = pb[bone(side + "Hand")]
    d = h.constraints.new("DAMPED_TRACK"); d.target = fing_t; d.track_axis = "TRACK_Y"
    lt = h.constraints.new("LOCKED_TRACK"); lt.target = palm_t; lt.lock_axis = "LOCK_Y"; lt.track_axis = palm_axis
    return c
PALM_R = os.environ.get("PALM_R", "TRACK_Z"); PALM_L = os.environ.get("PALM_L", "TRACK_NEGATIVE_Z")
TG = {}
for side in ("Right", "Left"):
    for k in ("wrist", "pole", "fing", "palm"):
        TG[side, k] = empty(f"{side}_{k}")
ik_arm("Right", TG["Right", "wrist"], TG["Right", "pole"], TG["Right", "fing"], TG["Right", "palm"], PALM_R)
ik_arm("Left", TG["Left", "wrist"], TG["Left", "pole"], TG["Left", "fing"], TG["Left", "palm"], PALM_L)
def arm_key(side, f, wrist, fing_dir, palm_dir, pole):
    w = Vector(wrist)
    key(TG[side, "wrist"], f, loc=tuple(w))
    key(TG[side, "fing"], f, loc=tuple(w + Vector(fing_dir).normalized() * 0.2))
    key(TG[side, "palm"], f, loc=tuple(w + Vector(palm_dir).normalized() * 0.2))
    key(TG[side, "pole"], f, loc=tuple(Vector(pole)))
# 1-kadr: o'ng qo'l dazmol dastasida, chap qo'l taxtada (ko'ylakni tekislaydi)
for f in range(1, 63, 3):
    sc.frame_set(f)
    hw = IRON_W[f] + V(-0.03, 0.0, 0.135)
    arm_key("Right", f, hw + V(0, 0.03, 0.02), (0.6, -0.8, -0.3), (0, 0, -1), MEG + V(-0.6, 0.2, 1.0))
    lx = 0.2 + 0.03 * math.sin(f / 5)
    arm_key("Left", f, BRD + V(lx, 0.06, 0.05), (0.3, -0.9, -0.25), (0, 0, -1), MEG + V(0.6, 0.2, 1.0))
# 7-kadr: chap qo'l ko'krak oldida (orqasi tepaga), o'ng ko'rsatkich barmoq uning ustida pastani suradi
LH7 = MEG + V(0.06, -0.33, 1.08)
for f in range(SM0, SM1 + 2, 2):
    t = (f - SM0) / (SM1 - SM0)
    arm_key("Left", f, LH7 + V(0, 0, 0.005 * math.sin(f / 7)), (-0.8, -0.55, 0.05), (0, 0, -1), MEG + V(0.5, 0.2, 0.9))
    rub = 0.022 * math.sin(f * 0.55)
    arm_key("Right", f, LH7 + V(-0.13 + rub, 0.0 + 0.6 * rub, 0.095), (0.75, -0.3, -0.6), (0.2, -0.2, -1.0), MEG + V(-0.5, 0.2, 0.9))
for side in ("Right", "Left"):
    for k in ("wrist", "fing", "palm", "pole"):
        for fc in fcurves(TG[side, k]):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT" if kp.co[0] in (SM0,) else "LINEAR"
# bosh qo'llarga qaraydi
headE = empty("meg_head"); c_ = headE.constraints.new("CHILD_OF"); c_.target = meg; c_.subtarget = bone("Head")
c_.use_scale_x = c_.use_scale_y = c_.use_scale_z = False; c_.inverse_matrix = Matrix.Identity(4)
lookT = empty("lookT")
for f, p in ((1, BRD + V(-0.05, 0, 0)), (40, BRD + V(0.05, 0, 0)), (62, BRD + V(0.1, 0, 0)), (SM0, LH7 + V(-0.03, 0, 0)), (SM1, LH7 + V(-0.05, 0, 0))):
    key(lookT, f, loc=tuple(p))
hd = meg.pose.bones[bone("Head")].constraints.new("DAMPED_TRACK"); hd.target = lookT; hd.track_axis = "TRACK_Z"; hd.influence = 0.55
nk = meg.pose.bones[bone("Neck")].constraints.new("DAMPED_TRACK"); nk.target = lookT; nk.track_axis = "TRACK_Z"; nk.influence = 0.3
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
FACE = {n: wpos(faceT, (a + b) // 2) for n, (a, b) in S.items() if n in ROOMN}
lhandE = empty("lhandE"); c_ = lhandE.constraints.new("CHILD_OF"); c_.target = meg; c_.subtarget = bone("LeftHand")
c_.use_scale_x = c_.use_scale_y = c_.use_scale_z = False; c_.inverse_matrix = Matrix.Identity(4)
HAND7 = wpos(lhandE, (SM0 + SM1) // 2)
print("FACE", {k: tuple(round(x, 3) for x in v) for k, v in FACE.items()}, "HAND7", tuple(round(x, 3) for x in HAND7))
# pasta (7-kadr): chap qo'l orqasida oq dog'
paste_m = bpy.data.materials.new("paste"); paste_m.use_nodes = True
b = paste_m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.93, 0.95, 0.96, 1); b.inputs["Roughness"].default_value = 0.22
b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.002; b.inputs["Coat Weight"].default_value = 0.4
PB_OFF = tuple(float(x) for x in os.environ.get("PB_OFF", "0,0.06,0.022").split(","))
pblob = sphere("paste_on_meg", 1.0, PB_OFF, paste_m, scale=(0.022, 0.026, 0.004), parent=lhandE)
vis(pblob, [S["smear"]])

# ======================================================================
# 3) MAKRO QO'L (real o'lcham): kaft pastda, barmoqlar -Y tomonda, bilak +Y da
# ======================================================================
MAC = Vector((30.0, 0.0, 0.0))
mac_root = empty("mac_root", tuple(MAC))
def M_(p): return MAC + Vector(p)
mshirt = shirt.copy(); mshirt.data = shirt.data.copy(); sc.collection.objects.link(mshirt)
mshirt.scale = (1.0, 1.0, 1.0); mshirt.location = MAC + V(0, 0, -0.004); mshirt.parent = None
mshirt.scale = (1.6, 1.6, 1.0)
bboard = box("mac_board", (1.2, 0.8, 0.02), tuple(MAC + V(0, 0, -0.016)), cover_m)
# teri + kuyik materiali
def hand_skin(name, burn=True):
    m = P.skin_material(name, base=(0.78, 0.53, 0.42), prints=False)
    if not burn: return m
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    cur = b.inputs["Base Color"].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord")
    bc = value_node(m, "bc_x", 0.0); bcy = value_node(m, "bc_y", 0.0)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    dx = P.math_n(N, L, "SUBTRACT", sep.outputs["X"], bc); dy = P.math_n(N, L, "SUBTRACT", sep.outputs["Y"], bcy)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180.0; nz.inputs["Detail"].default_value = 5
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    dist = P.math_n(N, L, "ADD", P.math_n(N, L, "SQRT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", dx, dx),
                                                                    P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", dy, dy), 0.7))),
                    P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.006))
    burn_v = value_node(m, "burn", 0.0); scar_v = value_node(m, "scar", 0.0)
    rad = P.math_n(N, L, "MULTIPLY", burn_v, 0.019)
    # qizil halqa (tashqi) va oqargan pufak (ichki)
    red = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", dist, P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", rad, 1.8), 0.0001)), clamp=True)
    red = P.math_n(N, L, "POWER", red, 0.45)
    core = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", dist, P.math_n(N, L, "ADD", rad, 0.0001)), clamp=True)
    core = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", core, 0.35), 1.0)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(red, c1.inputs["Factor"])
    L.new(cur, c1.inputs[6]); c1.inputs[7].default_value = (0.5, 0.035, 0.025, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(core, c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.86, 0.6, 0.5, 1)
    # chandiq: yaltiroq pushti, notekis
    scar = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", dist, 0.024), clamp=True), scar_v)
    scar = P.math_n(N, L, "MINIMUM", P.math_n(N, L, "MULTIPLY", scar, 4.0), 1.0)
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"; L.new(scar, c3.inputs["Factor"])
    L.new(c2.outputs[2], c3.inputs[6]); c3.inputs[7].default_value = (0.72, 0.22, 0.27, 1)
    L.new(c3.outputs[2], b.inputs["Base Color"])
    wet = P.math_n(N, L, "MAXIMUM", P.math_n(N, L, "MULTIPLY", core, 0.9), P.math_n(N, L, "MULTIPLY", scar, 0.25))
    L.new(wet, b.inputs["Coat Weight"]); b.inputs["Coat Roughness"].default_value = 0.08
    # pufak / chandiq bo'rtig'i (bump)
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 260.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    hgt = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", core, 0.6), P.math_n(N, L, "MULTIPLY", scar, P.math_n(N, L, "MULTIPLY", vo.outputs["Distance"], 1.5)))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.0008
    L.new(hgt, bp.inputs["Height"]); old = b.inputs["Normal"].links[0].from_socket; L.new(old, bp.inputs["Normal"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
hskin = hand_skin("hand_skin")
fskin = hand_skin("finger_skin", burn=False)
hand = empty("hand", tuple(MAC))
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=1.0); palm = bpy.context.object; palm.name = "palm"
for v in palm.data.vertices:
    x, y, z = v.co
    sx = 0.043 * (1 + 0.08 * (-y)); z = z * 0.017
    if z < 0: z *= 0.55
    v.co = Vector((x * sx, y * 0.052, z + 0.014))
palm.data.materials.append(hskin); palm.parent = hand
for p in palm.data.polygons: p.use_smooth = True
s_ = palm.modifiers.new("s", "SUBSURF"); s_.levels = 1; s_.render_levels = 2
# bilak
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1, depth=0.22, location=(0, 0, 0), rotation=(R(90), 0, 0))
fa = bpy.context.object; fa.name = "forearm"; bpy.ops.object.transform_apply(rotation=True)
for v in fa.data.vertices:
    t = (v.co.y + 0.11) / 0.22
    v.co.x *= 0.033 + 0.006 * t; v.co.z = v.co.z * (0.022 + 0.004 * t) + 0.016; v.co.y += 0.155
fa.data.materials.append(fskin); fa.parent = hand
for p in fa.data.polygons: p.use_smooth = True
# barmoqlar (uchi -Y da): build_finger uchi (0,0,0), tanasi +Y, tirnoq +Z
FING = [(-0.03, 0.0072, 0.062, -4), (-0.011, 0.0082, 0.074, -1), (0.009, 0.0081, 0.07, 1), (0.027, 0.0073, 0.058, 4)]
fingers = []
for i, (x, r, ln, rz) in enumerate(FING):
    fo = P.build_finger(f"mfinger{i}", parent=hand, r=r, length=ln, skin=fskin, knuckle=True)
    fo.location = (x - math.sin(R(rz)) * ln, -0.045 - ln, 0.011); fo.rotation_euler = (R(-6), 0, R(rz))
    fingers.append(fo)
th = P.build_finger("mthumb", parent=hand, r=0.0092, length=0.05, skin=fskin, knuckle=True)
th.location = (-0.072, -0.03, 0.012); th.rotation_euler = (R(-10), R(-25), R(-55))
BURN_C = V(0.004, -0.008, 0.031)     # qo'l orqasidagi kuyik markazi (mahalliy)
hand.location = MAC
# kuyik qiymatlari
val_key(hskin, "burn", 1, 0.0); val_key(hskin, "burn", F_CONTACT, 0.0); val_key(hskin, "burn", F_CONTACT + 10, 0.85)
val_key(hskin, "burn", S["touch"][1], 1.0); val_key(hskin, "burn", S["scar"][0] - 1, 1.0); val_key(hskin, "burn", S["scar"][0], 0.0)
val_key(hskin, "scar", 1, 0.0); val_key(hskin, "scar", S["scar"][0] - 1, 0.0); val_key(hskin, "scar", S["scar"][0], 1.0)
interp(hskin.node_tree, "LINEAR")
for fc in fcurves(hskin.node_tree):
    for k in fc.keyframe_points:
        if k.co[0] >= S["scar"][0] - 1: k.interpolation = "CONSTANT"
# makro dazmol (qizigan taglik)
miron, msole = build_iron("miron", hot=0.0)
TC0, TC1 = S["touch"]
# dazmol +X tomondan sirpanib keladi, uchi qo'l orqasiga (kuyik markaziga) tegadi
IR_T = MAC + BURN_C + V(0.148, 0.0, -0.002)    # dazmol 180° burilgan: uchi (mahalliy +0.151) -X tomonda, kuyik markazida
key(miron, TC0, loc=tuple(IR_T + V(0.09, 0.03, 0.012)), rot=(0, 4, 188))
key(miron, F_CONTACT, loc=tuple(IR_T), rot=(0, 4, 182))
key(miron, F_CONTACT + 6, loc=tuple(IR_T + V(-0.004, 0, -0.001)), rot=(0, 4, 182))
key(miron, TC1, loc=tuple(IR_T + V(0.02, 0.0, 0.03)), rot=(0, 10, 182))
vis(miron, [S["touch"]])
b = msole.node_tree.nodes["Principled BSDF"]
b.inputs["Emission Strength"].default_value = 0.6; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=1)
# qo'l kontaktdan keyin tortib olinadi
key(hand, 1, loc=tuple(MAC)); key(hand, F_CONTACT + 3, loc=tuple(MAC))
key(hand, F_CONTACT + 9, loc=tuple(MAC + V(-0.035, 0.02, 0.025)), rot=(0, 4, -6)); key(hand, F_CONTACT + 3, rot=(0, 0, 0))
key(hand, TC1, loc=tuple(MAC + V(-0.04, 0.025, 0.03)), rot=(0, 5, -7))
key(hand, S["paste"][0], loc=tuple(MAC), rot=(0, 0, 0))
for fc in fcurves(hand):
    for k in fc.keyframe_points:
        if k.co[0] == TC1: k.interpolation = "CONSTANT"
mac_steam = puffs("msteam", MAC + BURN_C + V(0.0, 0.0, 0.004), (F_CONTACT - 2, TC1), 12, 0.012, 0.06, 9, spread=0.025)
for s in mac_steam: vis(s, [S["touch"]])
# tish pastasi tubasi (3-kadr): uchi kuyik ustida, pasta "chuvalchangi" o'sadi
tube_m = mat("tube_m", (0.92, 0.94, 0.96), 0.35, coat=0.6)
stripe_m = mat("tube_stripe", (0.05, 0.35, 0.85), 0.35, coat=0.6)
red_m = mat("tube_red", (0.75, 0.05, 0.06), 0.35, coat=0.6)
tubeG = empty("ptube")
cyl("ptube_body", 0.016, 0.11, (0, 0, 0.075), tube_m, parent=tubeG, verts=48)
cyl("ptube_stripe", 0.0162, 0.025, (0, 0, 0.06), stripe_m, parent=tubeG, verts=48)
cyl("ptube_stripe2", 0.0162, 0.008, (0, 0, 0.09), red_m, parent=tubeG, verts=48)
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.016, radius2=0.005, depth=0.015, location=(0, 0, 0.0125), rotation=(R(180), 0, 0))
cn = bpy.context.object; cn.name = "ptube_cone"; cn.data.materials.append(tube_m); cn.parent = tubeG
cyl("ptube_nozzle", 0.0042, 0.008, (0, 0, 0.002), tube_m, parent=tubeG, verts=32)
box("ptube_crimp", (0.034, 0.004, 0.012), (0, 0, 0.134), tube_m, parent=tubeG)
PA0, PA1 = S["paste"]
BW = MAC + BURN_C
key(tubeG, PA0, loc=tuple(BW + V(0.03, 0.02, 0.05)), rot=(-35, 30, 0))
key(tubeG, PA0 + 14, loc=tuple(BW + V(0.008, 0.004, 0.009)), rot=(-30, 25, 0))
key(tubeG, PA0 + 50, loc=tuple(BW + V(-0.008, -0.004, 0.009)), rot=(-30, 25, 0))
key(tubeG, PA0 + 62, loc=tuple(BW + V(-0.01, -0.006, 0.04)), rot=(-30, 25, 0))
key(tubeG, PA1, loc=tuple(BW + V(-0.02, -0.01, 0.09)), rot=(-30, 25, 0))
vis(tubeG, [S["paste"]])
# pasta chuvalchangi: kuyik ustida spiral (bevel_factor_end o'sadi)
wpts = []
for i in range(40):
    a = i / 39 * 2.6 * math.pi; rr = 0.011 * (1 - i / 50)
    wpts.append(tuple(BURN_C + V(rr * math.cos(a), rr * math.sin(a), 0.0035 + 0.0006 * i / 39)))
worm = curve_tube("paste_worm", wpts, 0.0038, paste_m, parent=hand, res=6)
worm.data.bevel_factor_mapping_end = "SPLINE"
worm.data.bevel_factor_end = 0.0; worm.data.keyframe_insert("bevel_factor_end", frame=PA0 + 14)
worm.data.bevel_factor_end = 1.0; worm.data.keyframe_insert("bevel_factor_end", frame=PA0 + 52)
vis(worm, [S["paste"]])
# o'simlik yog'i tomchilari (3-kadr oxiri, "o'simlik yog'i")
oil_m = mat("oil", (0.85, 0.6, 0.08), 0.03, trans=0.85, coat=1.0)
oil_m.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.47
for i in range(3):
    d_ = sphere(f"oil_drop{i}", 0.0032, (0, 0, 0), oil_m, scale=(1, 1, 1.4), parent=hand)
    fx = PA0 + 52 + i * 7
    tgt = BURN_C + V(0.016 - 0.01 * i, 0.012 - 0.008 * i, 0.002)
    key(d_, fx, loc=tuple(tgt + V(0, 0, 0.08)), scale=(1, 1, 1.4)); key(d_, fx + 8, loc=tuple(tgt + V(0, 0, 0.002)), scale=(1, 1, 1.4))
    key(d_, fx + 11, loc=tuple(tgt), scale=(2.6, 2.6, 0.35)); key(d_, PA1, scale=(3.4, 3.4, 0.3))
    vis(d_, [(fx, PA1)])
mac_all = [palm, fa, th] + fingers + [mshirt, bboard]
for o in mac_all: vis(o, MACR, recursive=True)

# ======================================================================
# 4) TERI KESIMI (10x+): epidermis, dermis, yog' qatlami; kuyik zonasi, issiqlik zarralari, plyonka, asab uchlari
# ======================================================================
CUT = Vector((60.0, 0.0, 0.0))
sec, sparts, (epi_m, der_m, fat_m) = P.build_section("skin_sec", tuple(CUT), size=(2.0, 1.4))
# old (kesim) yuza: y = -0.7; tepasi z = 1.0
FY = -0.7
# kuyik zonasi: ellipsoid, blok chegarasi bilan kesilgan (INTERSECT)
bz_m = bpy.data.materials.new("burnzone"); bz_m.use_nodes = True
N = bz_m.node_tree.nodes; L = bz_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0; nz.inputs["Detail"].default_value = 6
L.new(tc.outputs["Object"], nz.inputs["Vector"])
cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.16, 0.01, 0.005, 1); cr.color_ramp.elements[1].color = (0.5, 0.04, 0.015, 1)
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.5; b.inputs["Coat Weight"].default_value = 0.5
heat = value_node(bz_m, "heat", 0.6)
b.inputs["Emission Color"].default_value = (1.0, 0.22, 0.02, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", nz.outputs["Fac"], 3.0), heat), b.inputs["Emission Strength"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0); bz = bpy.context.object; bz.name = "burnzone"
bz.data.materials.append(bz_m)
for p in bz.data.polygons: p.use_smooth = True
bz.location = CUT + V(0, FY, 1.0)
clipb = box("bz_clip", (2.0, 1.404, 1.004), tuple(CUT + V(0, 0.0, 0.502)), mat("clip", (1, 1, 1)))
clipb.hide_render = True
bo = bz.modifiers.new("clip", "BOOLEAN"); bo.operation = "INTERSECT"; bo.object = clipb; bo.solver = "EXACT"
RX, RYD = 0.45, 0.42
def depth_key(f, d):
    bz.scale = (RX, RYD, d); bz.keyframe_insert("scale", frame=f)
DE0, DE1 = S["deeper"]; DN0, DN1 = S["down"]
depth_key(1, 0.18); depth_key(DE0 + 10, 0.18); depth_key(F_DEEP + 14, 0.36); depth_key(DN0 + 6, 0.36); depth_key(DN1 - 10, 0.74)
val_key(bz_m, "heat", DE0, 0.8); val_key(bz_m, "heat", F_DEEP, 2.0); val_key(bz_m, "heat", F_DEEP + 20, 1.2)
val_key(bz_m, "heat", DN0, 1.2); val_key(bz_m, "heat", DN1, 2.2); val_key(bz_m, "heat", S["menthol"][0], 1.0)
interp(bz_m.node_tree, "LINEAR")
# asl chuqurlik sharpa chizig'i (4-kadr): oq yarim ellips
gpts = [tuple(CUT + V(RX * math.cos(a), FY - 0.012, 1.0 + 0.18 * math.sin(a)))
        for a in [math.pi + i / 30 * math.pi for i in range(31)]]
ghost_m = mat("ghostline", (1, 1, 1), 0.5, emit=2.5)
ghost = curve_tube("ghostline", gpts, 0.004, ghost_m)
vis(ghost, [(DE0 + 12, DE1)])
cut_objs = [sec, bz]
# issiqlik zarralari
heatp_m = mat("heatp", (1.0, 0.3, 0.03), 0.4, emit=2.5, emit_col=(1.0, 0.28, 0.02))
NP = 150
rp = random.Random(4)
PART = []
for i in range(NP):
    u = rp.uniform(-1, 1); v = rp.random() ** 0.7
    PART.append(dict(u=u, v=v, ph=rp.uniform(0, 6.28), w=rp.uniform(0.15, 0.35), launch=rp.uniform(S["escape"][0] - 2, S["escape"][0] + 40),
                     sp=rp.uniform(0.018, 0.03), dx=rp.uniform(-0.004, 0.004), bph=rp.uniform(0, 3.14), bw=rp.uniform(0.18, 0.3),
                     deep_v=rp.uniform(0.3, 1.0), dstart=rp.uniform(S["down"][0], S["down"][0] + 60), yy=rp.uniform(-0.012, -0.03),
                     r=rp.uniform(0.008, 0.016)))
sc.frame_set(1)
def bz_depth(f):
    fc = next(fc for fc in fcurves(bz) if fc.data_path == "scale" and fc.array_index == 2)
    return fc.evaluate(f)
def trapped_pos(p, f, d):
    rr = 0.85 * math.sqrt(1 - p["v"] ** 2) if p["v"] < 1 else 0.0
    x = RX * 0.9 * p["u"] * math.sqrt(max(0.0, 1 - (p["v"] * 0.9) ** 2))
    z = 1.0 - 0.06 - (d - 0.06) * p["v"] * 0.88
    x += 0.025 * math.sin(f * p["w"] + p["ph"]); z += 0.02 * math.sin(f * p["w"] * 1.3 + p["ph"] * 2)
    return x, z
E0, E1 = S["escape"]; FI0, FI1 = S["film"]
def ppos(i, f):
    p = PART[i]; d = bz_depth(f)
    x, z = trapped_pos(p, f, d)
    y = FY + p["yy"]
    if E0 <= f <= E1 and f > p["launch"]:
        t = f - p["launch"]
        z = z + p["sp"] * t + 0.0004 * t * t; x = x + p["dx"] * t + 0.01 * math.sin(t * 0.3 + p["ph"])
    elif FI0 <= f <= FI1:
        top = 0.985
        b_ = abs(math.sin(f * p["bw"] * 0.5 + p["bph"]))
        z = z + (top - z) * b_ ** 0.6
    elif f >= S["down"][0]:
        t = clamp01((f - p["dstart"]) / 50.0); t = ease(t)
        zd = 1.0 - 0.1 - (0.74 - 0.1) * p["deep_v"]
        xd = x * (1.0 + 0.25 * p["deep_v"])
        x = lerp(x, xd, t); z = lerp(z, zd, t)
    return (CUT.x + x, CUT.y + y, CUT.z + z)
def pscale(i, f):
    p = PART[i]
    if E0 <= f <= E1 and f > p["launch"]:
        t = f - p["launch"]
        return p["r"] * max(0.0, 1 - t / 40.0)
    if f >= S["menthol"][0]: return p["r"] * 0.7
    return p["r"]
cut_frames = sorted({f for a, b in CUTR for f in range(a, b + 1)})
heatG = empty("heatG", (0, 0, 0))
for i in range(NP):
    s = sphere(f"hp{i}", 1.0, (0, 0, 0), heatp_m, sub=2, parent=heatG)
    bake_path(s, cut_frames, lambda f, i=i: ppos(i, f), lambda f, i=i: pscale(i, f))
vis(heatG, CUTR)
hb = heatp_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 2.5), (S["down"][1], 2.5), (S["menthol"][0], 1.0)):
    hb.default_value = v; hb.keyframe_insert("default_value", frame=f)
# issiqlik sarobi (6-kadr): sirt ustida yuqoriga ko'tariluvchi to'lqin chiziqlari
# plyonka (pasta/yog'): 8-kadrdan boshlab
film_m = bpy.data.materials.new("film"); film_m.use_nodes = True
b = film_m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.93, 0.95, 0.97, 1)
b.inputs["Roughness"].default_value = 0.2; b.inputs["Subsurface Weight"].default_value = 0.7; b.inputs["Subsurface Scale"].default_value = 0.05
b.inputs["Coat Weight"].default_value = 0.6
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=32, radius=1.0); film = bpy.context.object; film.name = "film"
for v in film.data.vertices:
    v.co.z = max(v.co.z, 0.0) * 0.06 + 0.0
film.data.materials.append(film_m)
for p in film.data.polygons: p.use_smooth = True
fd = film.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new("film_n", "CLOUDS"); tx.noise_scale = 0.3; fd.texture = tx; fd.strength = 0.02
film.location = CUT + V(0, FY + 0.0, 1.0)
# plyonka faqat blok ichida: y >= FY bo'lgan yarmi (old yuzada kesim ko'rinadi)
film_clip = box("film_clip", (2.4, 1.4, 0.4), tuple(CUT + V(0, 0.0, 1.1)), mat("clip2", (1, 1, 1))); film_clip.hide_render = True
fb = film.modifiers.new("clip", "BOOLEAN"); fb.operation = "INTERSECT"; fb.object = film_clip; fb.solver = "EXACT"
def film_key(f, s):
    film.scale = (max(0.001, RX * 1.35 * s), max(0.001, 0.5 * s), 1.0); film.keyframe_insert("scale", frame=f)
film_key(1, 0.0); film_key(FI0 + 2, 0.02); film_key(F_FILM + 6, 1.0); film_key(END, 1.0)
# kimyoviy zarralar (mentol, oqartiruvchi): ko'k-yashil, plyonkadan pastga sizadi
MT0, MT1 = S["menthol"]; NV0, NV1 = S["nerve"]
chem_m = mat("chem", (0.1, 0.95, 0.75), 0.3, emit=3.0, emit_col=(0.15, 1.0, 0.7))
chem_m2 = mat("chem2", (0.3, 0.6, 1.0), 0.3, emit=3.0, emit_col=(0.35, 0.65, 1.0))
NERVE_X = [-0.33, -0.2, -0.07, 0.06, 0.19, 0.31]
rc = random.Random(8)
chemG = empty("chemG")
NC = 70
chem_frames = list(range(MT0, NV1 + 1))
for i in range(NC):
    tgt_n = NERVE_X[i % len(NERVE_X)]
    x0 = rc.uniform(-0.45, 0.45); z0 = rc.uniform(1.005, 1.04); st = rc.uniform(MT0 + 4, MT0 + 55); dur = rc.uniform(40, 70)
    xt = tgt_n + rc.uniform(-0.04, 0.04); zt = rc.uniform(0.86, 0.95); ph = rc.uniform(0, 6.28); yy = rc.uniform(-0.015, -0.03)
    def cp(f, x0=x0, z0=z0, st=st, dur=dur, xt=xt, zt=zt, ph=ph, yy=yy):
        t = ease(clamp01((f - st) / dur))
        return (CUT.x + lerp(x0, xt, t) + 0.01 * math.sin(f * 0.2 + ph), CUT.y + FY + yy, CUT.z + lerp(z0, zt, t) + 0.008 * math.sin(f * 0.27 + ph))
    s = sphere(f"chem{i}", 1.0, (0, 0, 0), chem_m if i % 3 else chem_m2, sub=2, parent=chemG)
    s.scale = (0.008,) * 3
    bake_path(s, chem_frames, cp)
vis(chemG, rng("menthol", "nerve"))
# asab uchlari: yog' qatlamidan epidermisgacha, sariq; impulslar uchidan pastga yuguradi
def train_mat(name, col=(0.9, 0.62, 0.18), pcol=(1.0, 0.12, 0.05)):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.02
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    cnt = value_node(m, "count", 4.0); ph = value_node(m, "phase", 0.0); amp = value_node(m, "amp", 0.0); gl = value_node(m, "glow", 0.1)
    x = P.math_n(N, L, "FRACT", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", ua.outputs["Fac"], cnt), ph))
    d = P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", x, 0.5))
    p = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", d, 0.12), clamp=True), 2.0)
    pe = P.math_n(N, L, "MULTIPLY", p, amp)
    L.new(P.math_n(N, L, "ADD", pe, gl), b.inputs["Emission Strength"])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; L.new(P.math_n(N, L, "MINIMUM", pe, 1.0), mix.inputs["Factor"])
    mix.inputs[6].default_value = (*col, 1); mix.inputs[7].default_value = (*pcol, 1); L.new(mix.outputs[2], b.inputs["Emission Color"])
    return m
nerve_m = train_mat("nerve_m")
tip_m = bpy.data.materials.new("nerve_tip"); tip_m.use_nodes = True
N = tip_m.node_tree.nodes; L = tip_m.node_tree.links; b = N["Principled BSDF"]
burnt = value_node(tip_m, "burnt", 0.0)
cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(burnt, cm.inputs["Factor"])
cm.inputs[6].default_value = (0.9, 0.62, 0.18, 1); cm.inputs[7].default_value = (0.02, 0.015, 0.01, 1); L.new(cm.outputs[2], b.inputs["Base Color"])
b.inputs["Emission Color"].default_value = (1.0, 0.1, 0.02, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", burnt, 0.5)), clamp=False), 3.0), b.inputs["Emission Strength"])
nerveG = empty("nerveG")
rn = random.Random(21)
for k, x in enumerate(NERVE_X):
    yy = FY - 0.008
    base = V(x * 1.3 + rn.uniform(-0.05, 0.05), yy, 0.08)
    pts = [base, V(x * 1.15, yy, 0.35), V(x * 1.05 + rn.uniform(-0.04, 0.04), yy, 0.62), V(x, yy, 0.8), V(x + rn.uniform(-0.03, 0.03), yy, 0.9)]
    t_ = P.tube(f"nerve{k}", [tuple(CUT + p) for p in pts], 0.011, nerve_m, parent=nerveG)
    sphere(f"ntip{k}", 0.02, tuple(CUT + pts[-1]), tip_m, parent=nerveG)
    for side in (-1, 1):       # shoxchalar
        bp_ = pts[3]; e_ = bp_ + V(side * rn.uniform(0.05, 0.09), 0, rn.uniform(0.08, 0.12))
        P.tube(f"nerveb{k}{side}", [tuple(CUT + bp_), tuple(CUT + (bp_ + e_) / 2 + V(side * 0.01, 0, 0.0)), tuple(CUT + e_)], 0.006, nerve_m, parent=nerveG)
        sphere(f"ntipb{k}{side}", 0.012, tuple(CUT + e_), tip_m, parent=nerveG)
vis(nerveG, rng("menthol", "nerve"))
val_key(nerve_m, "phase", NV0, 0.0); val_key(nerve_m, "phase", NV1, 12.0)
val_key(nerve_m, "amp", 1, 0.0); val_key(nerve_m, "amp", NV0 + 18, 0.0); val_key(nerve_m, "amp", NV0 + 30, 12.0); val_key(nerve_m, "amp", F_BURN, 25.0)
val_key(tip_m, "burnt", 1, 0.0); val_key(tip_m, "burnt", NV0 + 14, 0.0); val_key(tip_m, "burnt", F_BURN - 6, 0.5); val_key(tip_m, "burnt", NV1, 1.0)
interp(nerve_m.node_tree, "LINEAR"); interp(tip_m.node_tree, "LINEAR")
# kesim fonidagi qorong'i "stol" (aks)
for o in [sec, bz]: vis(o, CUTR, recursive=True)
vis(film, rng("film", "down", "menthol", "nerve"))
# 6-kadr: sirt ustidagi issiqlik sarobi — yarim shaffof to'q sariq "tutun" puflari


# ======================================================================
# 5) HUJAYRALAR (mikro): pushti hujayralar "pishadi" (qorayadi, pufaklanadi)
# ======================================================================
CELL = Vector((90.0, 0.0, 0.0))
CK0, CK1 = S["cook"]
cell_m = bpy.data.materials.new("cell"); cell_m.use_nodes = True
N = cell_m.node_tree.nodes; L = cell_m.node_tree.links; b = N["Principled BSDF"]
cook = value_node(cell_m, "cook", 0.0)
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 5
L.new(tc.outputs["Object"], nz.inputs["Vector"])
ob = N.new("ShaderNodeObjectInfo")
lag = P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", cook, 2.4), P.math_n(N, L, "MULTIPLY", ob.outputs["Random"], 0.6))
lag = P.math_n(N, L, "ADD", lag, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", nz.outputs["Fac"], 0.5), 0.6))
lag = P.math_n(N, L, "MINIMUM", P.math_n(N, L, "MAXIMUM", lag, 0.0), 1.0)
c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(lag, c1.inputs["Factor"])
c1.inputs[6].default_value = (0.9, 0.42, 0.5, 1); c1.inputs[7].default_value = (0.07, 0.025, 0.012, 1)
L.new(c1.outputs[2], b.inputs["Base Color"])
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, lag), 0.8), b.inputs["Subsurface Weight"]); b.inputs["Subsurface Scale"].default_value = 0.05; b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.3)
b.inputs["Coat Weight"].default_value = 0.7; b.inputs["Roughness"].default_value = 0.35
b.inputs["Emission Color"].default_value = (1.0, 0.3, 0.05, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", lag, P.math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)), 6.0), b.inputs["Emission Strength"])
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
nuc_m = mat("nucleus", (0.35, 0.12, 0.4), 0.4, sss=0.5)
cellG = empty("cellG", tuple(CELL))
rcl = random.Random(31); cells = []
for i in range(9):
    for j in range(7):
        x = (i - 4) * 0.21 + rcl.uniform(-0.04, 0.04) + (0.1 if j % 2 else 0); y = (j - 3) * 0.2 + rcl.uniform(-0.03, 0.03)
        r = rcl.uniform(0.1, 0.13)
        s = sphere(f"cell{i}_{j}", r, (x, y, rcl.uniform(-0.02, 0.02)), cell_m, scale=(1.0, 1.0, 0.75), sub=4, parent=cellG)
        dm = s.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new(f"cn{i}{j}", "CLOUDS"); tx.noise_scale = 0.2; dm.texture = tx; dm.strength = 0.03
        cells.append(s)
val_key(cell_m, "cook", 1, 0.0); val_key(cell_m, "cook", CK0 + 6, 0.05); val_key(cell_m, "cook", CK1, 1.0)
interp(cell_m.node_tree, "LINEAR")
bub_m = mat("bubble", (1.0, 0.95, 0.85), 0.02, trans=0.9, coat=1.0)
for k in range(45):
    c = rcl.choice(cells); a = rcl.uniform(0, 6.28)
    loc = Vector(c.location) + V(0.09 * math.cos(a), 0.09 * math.sin(a), 0.07)
    bb = sphere(f"cbub{k}", 0.025, tuple(loc), bub_m, sub=2, parent=cellG)
    f0 = int(rcl.uniform(CK0 + 15, CK1 - 12)); f1 = f0 + int(rcl.uniform(8, 20))
    key(bb, CK0, scale=0.0); key(bb, f0, scale=0.0); key(bb, f1, scale=rcl.uniform(0.6, 1.3)); key(bb, f1 + 1, scale=0.0)
vis(cellG, CELLR)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
# 1 ILGAK: poldan, keng ob'ektiv, tez push-in (dazmol va Megan)
H0, H1 = S["hook"]; FH = FACE["hook"]
c = abs_cam("hook", [(H0, BRD + V(0.75, -0.95, -0.05)), (H1, BRD + V(0.38, -0.5, 0.06))],
            [(H0, BRD + V(-0.12, 0.12, 0.32)), (H1, BRD + V(-0.15, 0.05, 0.12))], 16, 2.8)
lens_keys(c, [(H0, 15), (H1, 19)])
# 2 tegish: makro, past burchak, crash zoom + silkinish
c = abs_cam("touch", [(TC0, BW + V(-0.1, -0.36, 0.24)), (F_CONTACT - 1, BW + V(-0.08, -0.32, 0.21)), (F_CONTACT + 2, BW + V(-0.06, -0.27, 0.18)), (TC1, BW + V(-0.055, -0.26, 0.175))],
            [(TC0, BW + V(0.07, 0.0, 0.0)), (TC1, BW + V(0.03, 0.0, 0.005))], 26, 11.0)
lens_keys(c, [(TC0, 24), (F_CONTACT - 1, 27), (F_CONTACT + 2, 36), (TC1, 37)]); shake(c, F_CONTACT, F_CONTACT + 12, 0.006, seed=2)
# 3 pasta: yuqoridan-yondan sekin push-in
c = abs_cam("paste", [(PA0, BW + V(0.06, -0.17, 0.12)), (PA1, BW + V(0.035, -0.11, 0.08))],
            [(PA0, BW + V(0, 0, 0.004)), (PA1, BW + V(0, 0, 0.006))], 45, 11.0)
# 4 chuqurlashish: kesim, crash zoom
CF = CUT + V(0, FY, 0.82)
c = abs_cam("deeper", [(DE0, CF + V(0.743, -2.84, 0.945)), (F_DEEP - 1, CF + V(0.54, -2.29, 0.675)), (F_DEEP + 2, CF + V(0.338, -1.42, 0.405)), (DE1, CF + V(0.27, -1.32, 0.338))],
            [(DE0, CF + V(0, 0, -0.02)), (DE1, CF + V(0, 0, -0.04))], 28, 8.0)
lens_keys(c, [(DE0, 24), (F_DEEP - 1, 28), (F_DEEP + 2, 40), (DE1, 42)]); shake(c, F_DEEP, F_DEEP + 12, 0.02, seed=4)
# 5 qamalish: sekin aylanma
TR0, TR1 = S["trapped"]
c = abs_cam("trapped", [(TR0, CF + V(-0.945, -1.62, 0.472)), (TR1, CF + V(0.675, -1.69, 0.27))], [(TR0, CF + V(0, 0, 0.0)), (TR1, CF + V(0, 0, 0.0))], 36, 8.0)
# 6 chiqib ketish: kamera zarralar bilan tepaga
c = abs_cam("escape", [(E0, CF + V(0.405, -2.16, 0.135)), (E1, CF + V(0.27, -2.16, 1.15))], [(E0, CF + V(0, 0, 0.12)), (E1, CF + V(0, 0, 0.6))], 30, 8.0)
# 7 surtish: Megan, yuzga yaqin, yonlama siljish, DOF
FS_ = FACE["smear"]; HC = HAND7
c = abs_cam("smear", [(SM0, HC + V(-0.45, -0.85, 0.3)), (SM1, HC + V(-0.2, -0.8, 0.28))], [(SM0, HC + V(-0.04, 0, 0.21)), (SM1, HC + V(-0.04, 0, 0.21))], 30, 2.8)
c.data.dof.focus_object = None; c.data.dof.focus_distance = 0.0
fT = empty("smear_focus"); fc_ = fT.constraints.new("COPY_LOCATION"); fc_.target = lhandE; c.data.dof.focus_object = fT
# 8 plyonka: crash zoom
c = abs_cam("film", [(FI0, CF + V(-0.54, -2.56, 1.01)), (F_FILM - 1, CF + V(-0.405, -1.96, 0.743)), (F_FILM + 2, CF + V(-0.203, -1.08, 0.432)), (FI1, CF + V(0.0675, -1.01, 0.378))],
            [(FI0, CF + V(0, 0, 0.1)), (FI1, CF + V(0, 0, 0.12))], 28, 8.0)
lens_keys(c, [(FI0, 24), (F_FILM - 1, 28), (F_FILM + 2, 40), (FI1, 42)]); shake(c, F_FILM, F_FILM + 10, 0.02, seed=8)
# 9 pastga: kamera pastga tushadi (yog' qatlamigacha)
c = abs_cam("down", [(DN0, CF + V(0.608, -1.76, 0.405)), (DN1, CF + V(0.405, -1.69, -0.608))], [(DN0, CF + V(0, 0, 0.02)), (DN1, CF + V(0, 0, -0.4))], 32, 8.0)
# 10 hujayralar: aylanma + push-in
c = abs_cam("cook", [(CK0, CELL + V(0.9, -1.0, 0.75)), (F_COOK, CELL + V(0.5, -0.75, 0.5)), (CK1, CELL + V(-0.1, -0.55, 0.38))],
            [(CK0, CELL + V(0, 0, 0)), (CK1, CELL + V(0, 0.05, 0))], 32, 4.0)
shake(c, F_COOK, F_COOK + 10, 0.015, seed=10)
# 11 mentol: plyonka yaqinidan, yonlama siljish
c = abs_cam("menthol", [(MT0, CF + V(-0.608, -1.28, 0.54)), (MT1, CF + V(0.405, -1.28, 0.405))], [(MT0, CF + V(-0.1, 0, 0.12)), (MT1, CF + V(0.08, 0, 0.08))], 36, 8.0)
# 12 asab uchlari: push-in, "kuydirib" da qizil chaqnash + silkinish
c = abs_cam("nerve", [(NV0, CF + V(0.472, -2.03, 0.203)), (F_BURN - 1, CF + V(0.203, -1.35, 0.135)), (F_BURN + 2, CF + V(0.108, -0.945, 0.081)), (NV1, CF + V(0.081, -0.891, 0.0675))],
            [(NV0, CF + V(0, 0, -0.15)), (NV1, CF + V(0, 0, 0.0))], 30, 8.0)
lens_keys(c, [(NV0, 28), (F_BURN - 1, 32), (F_BURN + 2, 42), (NV1, 44)]); shake(c, F_BURN, F_BURN + 11, 0.018, seed=12)
# 13 chandiq: makro, sekin push-in
SC0, SC1 = S["scar"]
c = abs_cam("scar", [(SC0, BW + V(0.06, -0.2, 0.12)), (SC1, BW + V(0.04, -0.14, 0.085))], [(SC0, BW + V(0, 0, 0)), (SC1, BW)], 45, 11.0)
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
# 7) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(30))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_env = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_env.inputs[0])
bg_col = N.new("ShaderNodeBackground")
a1 = N.new("ShaderNodeAddShader"); L.new(bg_env.outputs[0], a1.inputs[0]); L.new(bg_col.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WORLD = {"room": (0.9, (0, 0, 0), 0.0), "mac": (0.12, (0.03, 0.03, 0.035), 0.3), "cut": (0.0, (0.03, 0.012, 0.01), 1.0),
         "cell": (0.0, (0.06, 0.012, 0.005), 1.0)}
def world_of(n):
    return "room" if n in ROOMN else "mac" if n in MACN else "cut" if n in CUTN else "cell"
for f, n in SHOTS:
    es, col, cs = WORLD[world_of(n)]
    bg_env.inputs[1].default_value = es; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (*col, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = cs; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# xona: derazadan quyosh, shift, iliq to'ldiruvchi
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceT
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(55), 0, R(160)); sun.data.angle = R(2)
for f, e in lights_for(ROOM, 3.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("win_light", tuple(WC + V(0, -0.3, 0)), 1.8, (0.85, 0.92, 1.0), lights_for(ROOM, 120.0), target=FT)
area("ceil_fill", (0.4, -0.8, 2.6), 2.0, (1.0, 0.92, 0.82), lights_for(ROOM, 60.0), target=empty("cfT", (0, -0.4, 0.9)))
area("key_front", tuple(MEG + V(-0.9, -1.4, 1.7)), 0.8, (1.0, 0.9, 0.8), lights_for(ROOM, 45.0), target=FT)
# makro: studiya
MT = empty("macroT", tuple(BW))
area("M_key", tuple(BW + V(-0.15, -0.2, 0.25)), 0.2, (1.0, 0.95, 0.9), lights_for(MACR, 3.0), target=MT)
area("M_fill", tuple(BW + V(0.25, -0.15, 0.12)), 0.25, (0.85, 0.9, 1.0), lights_for(MACR, 1.2), target=MT)
area("M_rim", tuple(BW + V(0.05, 0.25, 0.15)), 0.15, (1.0, 0.9, 0.8), lights_for(MACR, 2.0), target=MT)
point("M_hot", tuple(BW + V(0.02, -0.01, 0.02)), 0.01, (1.0, 0.4, 0.1), [(1, 0), (F_CONTACT, 0.6), (S["touch"][1] + 1, 0)])
# kesim: iliq studiya
CT_ = empty("cutT", tuple(CF))
area("C_key", tuple(CF + V(-1.0, -1.5, 1.4)), 1.4, (1.0, 0.95, 0.9), lights_for(CUTR, 55.0), target=CT_)
area("C_fill", tuple(CF + V(1.3, -1.2, 0.2)), 1.2, (1.0, 0.85, 0.75), lights_for(CUTR, 18.0), target=CT_)
area("C_rim", tuple(CF + V(0.0, 1.2, 1.4)), 1.0, (1.0, 0.75, 0.5), lights_for(CUTR, 35.0), target=CT_)
point("C_hot", tuple(CF + V(0, -0.15, 0.0)), 0.2, (1.0, 0.35, 0.08), lights_for(CUTR, 8.0))
# hujayralar
CL_ = empty("cellT", tuple(CELL))
area("CE_key", tuple(CELL + V(-0.8, -1.0, 1.2)), 1.0, (1.0, 0.9, 0.85), lights_for(CELLR, 70.0), target=CL_)
area("CE_rim", tuple(CELL + V(0.6, 1.0, 0.8)), 1.0, (1.0, 0.5, 0.2), lights_for(CELLR, 60.0), target=CL_)
point("CE_under", tuple(CELL + V(0, 0, -0.4)), 0.5, (1.0, 0.3, 0.05), [(1, 0), (CK0, 20.0), (CK1, 80.0), (CK1 + 1, 0)], const=False)

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
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
