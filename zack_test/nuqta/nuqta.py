# Oq ko'ylakdagi qora nuqta — Zack D. Films uslubida 41.6 s video (998 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py (yordamchilar tirnoq_osishi.py dan), parts.py = tirnoq_osishi/parts.py (miya, rentgen).
# Assetlar: zack_test/tools/get_nuqta.sh ; kadr rejasi: STORYBOARD.md
# 1) Pufak rasmlari:  STILLS=1 OUT=/tmp/claude-0/stills/ /tmp/claude-0/bvenv/bin/python -I zack_test/nuqta/nuqta.py --render
# 2) Render:          OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/nuqta/nuqta.py --render
#    Sinov:           FRAMES=20,90,200,530,800 PCT=30 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
STILL_DIR = os.environ.get("STILL_DIR", "/tmp/claude-0/stills/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 998
sc.frame_start, sc.frame_end = 1, END
V = lambda *a: Vector(a)
empty = P.empty

# ---------------- yordamchilar ----------------
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale if isinstance(scale, (tuple, list, Vector)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)

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
    if m: o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def uvsphere(name, loc, r, m, parent=None, seg=32, rings=16, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.location = loc; o.scale = scale
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if m: o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def import_gltf(path, loc, rot=(0, 0, 0), scale=1.0, parent=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc, parent)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler = [R(a) for a in rot]; root.scale = scale if isinstance(scale, tuple) else (scale,) * 3
    return root, new

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value
mn = P.math_n

def child_of_bone(name, arm, bone):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    return e

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.01):
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

def path_keys(o, pts):
    for f, p in pts: key(o, f, loc=tuple(p))

def cam(name, pts, tgt_pts, lens, fstop=None, clip=0.01, focus=None, parent=None):
    t = empty(name + "_t", (0, 0, 0), parent); path_keys(t, tgt_pts)
    c = camera("cam_" + name, tuple(pts[0][1]), t, lens, fstop, focus=focus or t, clip=clip)
    if parent: c.parent = parent
    path_keys(c, pts)
    CAMS[name] = c
    return c

def lens_keys(c, pairs):
    for f, l in pairs: c.data.lens = l; c.data.keyframe_insert("lens", frame=f)

def shake(c, f0, f1, amp, seed=1):
    rnd = random.Random(seed); base = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); p = c.location.copy()
        k = amp * (1 - (f - f0) / max(1, f1 - f0)) ** 2
        base[f] = p + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
    for f, p in base.items():
        c.location = p; c.keyframe_insert("location", frame=f)

def area(name, loc, size, col, keys, target=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    l.visible_camera = False
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else float(x >= a); return t * t * (3 - 2 * t)

# ---------------- kadrlar (ovoz so'zlariga bog'langan; kadr = soniya*24 + 1) ----------------
SHOTS = [(1, "wide"), (32, "shirt"), (62, "dot"), (111, "class"), (147, "ask"), (184, "point"), (208, "redot"),
         (230, "look"), (290, "rest"), (344, "white"), (410, "nobody"), (469, "explain"),
         (506, "kind"), (568, "hurt"), (630, "memory"), (727, "brain"), (790, "bias"), (863, "dotend"), (936, "end")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
STUDN = ("kind", "hurt", "memory", "brain", "bias", "end")
CLASSN = tuple(n for f, n in SHOTS if n not in STUDN)
CLASS_R = rng(*CLASSN); STUD_R = rng(*STUDN)
F_DOT = 83            # "nuqta" — marker ko'ylakka tegadi
F_HEART0 = 516        # "o'n marta" — yuraklar
F_SAD = 607           # "qoldirishi"

# ======================================================================
# 1) SINF (0,0,0): old devor y=-4.5 (doska), deraza x=+4, o'qituvchi (0,-3.3) +Y ga qaraydi
# ======================================================================
room = empty("CLASS")
floor_m = pbr("floor", "laminate_floor_02", 0.45, tint=(0.95, 0.88, 0.8))
wall_m = pbr("wall", "painted_plaster_wall", 0.5, tint=(0.62, 0.8, 0.86))
wain_m = pbr("wain", "painted_plaster_wall", 0.5, tint=(0.16, 0.3, 0.48))
ceil_m = mat("ceil", (0.85, 0.86, 0.86), 0.9)
plane("floor", (8.4, 9.4), (0, 0, 0), floor_m, parent=room)
plane("ceiling", (8.4, 9.4), (0, 0, 3.0), ceil_m, rot=(180, 0, 0), parent=room)
# devorlar (deraza devori bo'laklardan: 3 ta deraza x=+4, y=-2.6, 0, 2.6, z 0.95..2.45)
box("w_front", (8.4, 0.12, 3.0), (0, -4.56, 1.5), wall_m, parent=room)
box("w_back", (8.4, 0.12, 3.0), (0, 4.56, 1.5), wall_m, parent=room)
box("w_left", (0.12, 9.4, 3.0), (-4.06, 0, 1.5), wall_m, parent=room)
box("wr_low", (0.12, 9.4, 0.95), (4.06, 0, 0.475), wall_m, parent=room)
box("wr_top", (0.12, 9.4, 0.55), (4.06, 0, 2.725), wall_m, parent=room)
for i, y in enumerate((-4.15, -1.3, 1.3, 4.15)):
    w = 0.9 if abs(y) > 4 else 0.8
    box(f"wr_pier{i}", (0.12, w, 1.5), (4.06, y, 1.7), wall_m, parent=room)
win_frame = mat("winframe", (0.92, 0.92, 0.9), 0.4)
for i, y in enumerate((-2.6, 0.0, 2.6)):
    box(f"win_sill{i}", (0.3, 1.9, 0.05), (3.95, y, 0.95), win_frame, parent=room)
    box(f"win_mul{i}", (0.06, 0.05, 1.5), (4.04, y, 1.7), win_frame, parent=room)
    box(f"win_tr{i}", (0.06, 1.9, 0.05), (4.04, y, 1.75), win_frame, parent=room)
# panel (pastki to'q ko'k qism)
for nm_, sz, lc in (("wn_l", (0.03, 9.3, 1.0), (-3.99, 0, 0.5)), ("wn_b", (8.3, 0.03, 1.0), (0, 4.49, 0.5)), ("wn_f", (8.3, 0.03, 1.0), (0, -4.49, 0.5))):
    box(nm_, sz, lc, wain_m, parent=room)
# doska
board_m = bpy.data.materials.new("board"); board_m.use_nodes = True
_N = board_m.node_tree.nodes; _L = board_m.node_tree.links; _b = _N["Principled BSDF"]
_nz = _N.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 3.0; _nz.inputs["Detail"].default_value = 6
_cr = _N.new("ShaderNodeValToRGB"); _cr.color_ramp.elements[0].color = (0.035, 0.14, 0.08, 1); _cr.color_ramp.elements[1].color = (0.09, 0.26, 0.16, 1)
_L.new(_nz.outputs["Fac"], _cr.inputs[0]); _L.new(_cr.outputs[0], _b.inputs["Base Color"]); _b.inputs["Roughness"].default_value = 0.85
box("board", (3.6, 0.04, 1.25), (0, -4.48, 1.55), board_m, parent=room)
wood_m = mat("wood", (0.36, 0.2, 0.09), 0.45)
for nm_, sz, lc in (("bf_t", (3.72, 0.06, 0.06), (0, -4.46, 2.2)), ("bf_b", (3.72, 0.1, 0.05), (0, -4.42, 0.9)),
                    ("bf_l", (0.06, 0.06, 1.3), (-1.83, -4.46, 1.55)), ("bf_r", (0.06, 0.06, 1.3), (1.83, -4.46, 1.55))):
    box(nm_, sz, lc, wood_m, parent=room)
chalk_m = mat("chalk", (0.95, 0.95, 0.92), 0.9)
for i in range(3): cyl(f"chalk{i}", 0.006, 0.07, (-1.2 + i * 0.12, -4.39, 0.94), chalk_m, rot=(0, 90, 0), parent=room)
# doskadagi bo'r yozuvlari (oddiy chiziqlar)
for i, (x, z, w) in enumerate(((-1.2, 1.95, 0.9), (-1.25, 1.8, 0.6), (0.6, 1.95, 0.7), (0.55, 1.78, 1.0), (0.5, 1.62, 0.5))):
    box(f"chalk_line{i}", (w, 0.004, 0.018), (x, -4.455, z), mat(f"cl{i}", (0.8, 0.85, 0.8), 0.9, emit=0.05), parent=room)
# soat
cyl("clock", 0.18, 0.04, (2.6, -4.48, 2.35), mat("clockface", (0.95, 0.95, 0.93), 0.4), rot=(90, 0, 0), parent=room)
cyl("clock_rim", 0.195, 0.035, (2.6, -4.49, 2.35), mat("clockrim", (0.08, 0.08, 0.1), 0.3), rot=(90, 0, 0), parent=room)
for i, (a, l) in enumerate(((60, 0.12), (200, 0.08))):
    box(f"hand{i}", (0.008, 0.005, l), (2.6 + math.sin(R(a)) * l / 2, -4.455, 2.35 + math.cos(R(a)) * l / 2), mat(f"hd{i}", (0.05, 0.05, 0.05), 0.4), rot=(0, a, 0), parent=room)
# devor plakatlari (chap va orqa devor)
for i, (lc, rot, col) in enumerate((((-3.98, -2.2, 1.8), (90, 0, 90), (0.95, 0.75, 0.45)), ((-3.98, 0.2, 1.75), (90, 0, 90), (0.55, 0.78, 0.95)),
                                    ((-3.98, 2.4, 1.8), (90, 0, 90), (0.95, 0.6, 0.62)), ((-1.5, 4.48, 1.8), (90, 0, 180), (0.7, 0.9, 0.6)),
                                    ((1.5, 4.48, 1.8), (90, 0, 180), (0.98, 0.9, 0.55)))):
    plane(f"poster{i}", (0.75, 1.0), lc, mat(f"poster{i}", col, 0.7), rot=rot, parent=room)
    plane(f"poster_in{i}", (0.5, 0.35), (lc[0] + (0.005 if lc[0] < 0 else 0), lc[1] - (0.005 if lc[1] > 4 else 0), lc[2] + 0.15), mat(f"pin{i}", tuple(c * 0.55 for c in col), 0.7), rot=rot, parent=room)
# shiftdagi lampalar (ko'rinadigan)
lamp_m = mat("lamp", (1, 1, 1), 0.5, emit=6.0, emit_col=(1.0, 0.97, 0.9))
for i, (x, y) in enumerate(((-1.6, -2.4), (1.6, -2.4), (-1.6, 0.6), (1.6, 0.6), (-1.6, 3.2), (1.6, 3.2))):
    box(f"lamp{i}", (0.6, 1.2, 0.04), (x, y, 2.98), lamp_m, parent=room)
# shkaf (orqa devor)
cab_m = mat("cab", (0.22, 0.22, 0.24), 0.5)
for i, x in enumerate((-3.2, -2.5)):
    box(f"cab{i}", (0.68, 0.5, 1.9), (x, 4.2, 0.95), cab_m, parent=room, bevel=0.01)
# o'qituvchi stoli
box("tdesk_top", (1.4, 0.7, 0.05), (-2.3, -3.2, 0.74), wood_m, parent=room, bevel=0.005)
box("tdesk_body", (1.36, 0.6, 0.7), (-2.3, -3.2, 0.36), mat("tdesk", (0.25, 0.26, 0.3), 0.5), parent=room)
_, bk = import_gltf(PH + "decorative_book_set_01/decorative_book_set_01.gltf", (-2.6, -3.2, 0.765), (0, 0, 20), 1.0, room) if os.path.exists(PH + "decorative_book_set_01/decorative_book_set_01.gltf") else (None, [])
# partalar va stullar (Poly Haven), 3 qator x 4 ustun
_, dk = import_gltf(PH + "SchoolDesk_01/SchoolDesk_01.gltf", (0, 0, 0)); desk_src = [o for o in dk if o.type == "MESH"][0]
_, ch = import_gltf(PH + "SchoolChair_01/SchoolChair_01.gltf", (0, 0, 0)); chair_src = [o for o in ch if o.type == "MESH"][0]
COLS = (-2.6, -1.0, 1.0, 2.6); ROWS = (-1.3, 0.2, 1.7)
SEATS = {}
for r_, y in enumerate(ROWS):
    for c_, x in enumerate(COLS):
        d = desk_src.copy(); sc.collection.objects.link(d); d.parent = room
        d.location = (x, y - 0.55, 0); d.rotation_euler = (0, 0, R(random.uniform(-2, 2))); d.scale = (1, 1, 0.82)
        cc = chair_src.copy(); sc.collection.objects.link(cc); cc.parent = room
        cc.location = (x, y - 0.02, 0); cc.rotation_euler = (0, 0, R(random.uniform(-4, 4)))
        SEATS[(r_, c_)] = V(x, y, 0)
for o in dk + ch:
    if o.type == "MESH": o.hide_render = True; o.hide_viewport = True
# deraza tashqarisi: daraxt va bino siluetlari (HDRI osmon ostida)
tree_m = mat("tree", (0.12, 0.3, 0.1), 0.8); trunk_m = mat("trunk", (0.25, 0.17, 0.1), 0.8)
for i, (y, s) in enumerate(((-3.5, 1.2), (-0.8, 1.5), (2.0, 1.1), (4.5, 1.4))):
    cyl(f"trunk{i}", 0.12, 3, (9 + i % 2, y, 1.5), trunk_m, parent=room)
    uvsphere(f"crown{i}", (9 + i % 2, y, 3.4), 1.6 * s, tree_m, parent=room, scale=(1, 1, 0.85))
plane("grass", (30, 40), (14, 0, -0.02), mat("grass", (0.18, 0.32, 0.12), 0.9), parent=room)

# ======================================================================
# 2) MOVIY STUDIYA (50,0,0) — namuna videodagi teal fon
# ======================================================================
S0 = V(50, 0, 0)
stud = empty("STUDIO", tuple(S0))
teal = bpy.data.materials.new("teal"); teal.use_nodes = True
_N = teal.node_tree.nodes; _L = teal.node_tree.links; _b = _N["Principled BSDF"]
_b.inputs["Base Color"].default_value = (0.03, 0.42, 0.5, 1); _b.inputs["Roughness"].default_value = 0.9
# yorqin markaz (orqa fonda yumshoq dog')
_g = _N.new("ShaderNodeNewGeometry")
_d = mn(_N, _L, "LENGTH", mn(_N, _L, "SUBTRACT", _g.outputs["Position"], tuple(S0 + V(0, 3.0, 1.4)), vec=True), vec=True)
_f = mn(_N, _L, "SUBTRACT", 1.0, mn(_N, _L, "DIVIDE", _d, 3.2), clamp=True)
_L.new(mn(_N, _L, "MULTIPLY", mn(_N, _L, "POWER", _f, 1.6), 0.9), _b.inputs["Emission Strength"])
_b.inputs["Emission Color"].default_value = (0.35, 0.85, 0.92, 1)
# siklorama: pol + egilgan orqa devor
bm = bmesh.new()
prof = [(-3.0, 0.0)] + [(3.0 + 1.2 * math.sin(R(a)), 1.2 - 1.2 * math.cos(R(a))) for a in range(0, 91, 10)] + [(4.2, 8.0)]
W2 = 9.0
rows_ = []
for y, z in prof:
    rows_.append([bm.verts.new((sx * W2, y, z)) for sx in (-1, 1)])
for a, b in zip(rows_, rows_[1:]): bm.faces.new((a[0], a[1], b[1], b[0]))
me = bpy.data.meshes.new("cyc"); bm.to_mesh(me); cyc = bpy.data.objects.new("cyc", me); sc.collection.objects.link(cyc)
cyc.parent = stud; cyc.data.materials.append(teal)
for p in cyc.data.polygons: p.use_smooth = True

# ======================================================================
# 3) QAHRAMONLAR
# ======================================================================
def soften(meshes, rough=0.55):
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
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo
    return s
def seg(arm, act, f0, f1, offset=0, speed=1.0, bi=0):
    """act'ni f0..f1 oralig'ini to'liq qoplaydigan qilib qo'yadi (offset: harakatning boshidan necha sahna kadrini tashlab yuborish)"""
    a, b = act.frame_range
    a2 = min(b - 4, a + offset * 30 / 24 * speed)
    n = (f1 + 1) - f0
    rep = max(1.0, n / ((b - a2) * 0.8 / speed))
    return strip(arm, act, f0, repeat=rep, speed=speed, bi=bi, src=(a2, b) if offset else None)
def char(name, file, rough=0.55):
    root, arm, meshes = mc.load_character(name, file); sc.render.fps = 24
    soften(meshes, rough); return root, arm, meshes
def rkey(root, f, loc, rz):
    root.location = tuple(loc); root.rotation_euler = (0, 0, R(rz))
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
def const(o):
    interp(o, "CONSTANT")

# --- o'qituvchi (Megan) ---
TPOS = V(0, -3.3, 0)
troot, tarm, tmeshes = char("teach", "Megan.fbx", 0.6)
rkey(troot, 1, TPOS, 180)
shirt = next(o for o in tmeshes if "Shirt" in o.name)
hair = next(o for o in tmeshes if o.name.endswith("Hair"))
# sochni mis-qizg'ish qil (namuna videodagi o'qituvchi kabi)
for m in hair.data.materials:
    N = m.node_tree.nodes; L = m.node_tree.links; b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    if b.inputs["Base Color"].links:
        src = b.inputs["Base Color"].links[0].from_socket
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "SCREEN"; mx.inputs["Factor"].default_value = 0.55
        L.new(src, mx.inputs[6]); mx.inputs[7].default_value = (0.55, 0.16, 0.04, 1)
        mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; mx2.blend_type = "MULTIPLY"; mx2.inputs["Factor"].default_value = 1.0
        L.new(mx.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = (1.0, 0.62, 0.42, 1)
        L.new(mx2.outputs[2], b.inputs["Base Color"])
# nuqta, qizil nur, oq to'lqin — futbolka materialida (Generated = deformatsiyasiz koordinata, mato bilan yuradi)
sm = shirt.data.materials[0].copy(); sm.name = "teacher_shirt"; shirt.data.materials[0] = sm
bpy.context.view_layer.update()
# old tomon, ko'krak o'rtasi (dam holatida)
_wv = [(i, shirt.matrix_world @ v.co) for i, v in enumerate(shirt.data.vertices)]
_cand = [(i, p) for i, p in _wv if abs(p.z - (TPOS.z + 1.30)) < 0.02 and abs(p.x - TPOS.x + 0.02) < 0.02]
DOT_I, _p = max(_cand, key=lambda t: t[1].y)                 # 180° burilgan: old = +Y
DOT_LOCAL = shirt.data.vertices[DOT_I].co.copy()
tl = Vector(shirt.data.texspace_location); ts = Vector(shirt.data.texspace_size)
G0 = Vector([(DOT_LOCAL[k] - (tl[k] - ts[k])) / (2 * ts[k]) for k in range(3)])
print("DOT local", DOT_LOCAL, "gen", G0)
N = sm.node_tree.nodes; L = sm.node_tree.links; b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
tc = N.new("ShaderNodeTexCoord")
g = mn(N, L, "SUBTRACT", tc.outputs["Generated"], tuple(G0), vec=True)
g = mn(N, L, "MULTIPLY", g, tuple(2 * ts[k] for k in range(3)), vec=True)          # mahalliy birlik (sm)
dist = mn(N, L, "LENGTH", g, vec=True)
nzd = N.new("ShaderNodeTexNoise"); nzd.inputs["Scale"].default_value = 0.9; L.new(g, nzd.inputs["Vector"])
dot_r = value_node(sm, "dot_r", 0.0)
rr = mn(N, L, "MULTIPLY", dot_r, mn(N, L, "ADD", 0.85, mn(N, L, "MULTIPLY", nzd.outputs["Fac"], 0.3)))
inside = mn(N, L, "SUBTRACT", 1.0, mn(N, L, "DIVIDE", mn(N, L, "SUBTRACT", dist, rr), 0.12), clamp=True)
inside = mn(N, L, "MULTIPLY", inside, mn(N, L, "GREATER_THAN", dot_r, 0.01))
src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
white = N.new("ShaderNodeMix"); white.data_type = "RGBA"
if src: L.new(src, white.inputs[6])
white.inputs[7].default_value = (0.93, 0.93, 0.92, 1); white.inputs["Factor"].default_value = 0.6     # yanada oppoq
mxd = N.new("ShaderNodeMix"); mxd.data_type = "RGBA"; L.new(white.outputs[2], mxd.inputs[6]); mxd.inputs[7].default_value = (0.002, 0.002, 0.003, 1)
L.new(inside, mxd.inputs["Factor"]); L.new(mxd.outputs[2], b.inputs["Base Color"])
L.new(mn(N, L, "ADD", 0.6, mn(N, L, "MULTIPLY", inside, 0.3)), b.inputs["Roughness"])
# qizil nur (nuqta atrofida, "ko'rsatdi") va yorug' to'lqin ("butunlay oppoq")
red = value_node(sm, "red", 0.0)
halo = mn(N, L, "SUBTRACT", 1.0, mn(N, L, "DIVIDE", dist, 11.0), clamp=True)
halo = mn(N, L, "MULTIPLY", mn(N, L, "MULTIPLY", mn(N, L, "POWER", halo, 0.8), red), mn(N, L, "SUBTRACT", 1.0, inside))
wave = value_node(sm, "wave", -0.3)            # 0..1 (pastdan tepaga, Generated Y)
glow = value_node(sm, "glow", 0.0)             # to'lqindan keyingi umumiy yorug'lik
sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
band = mn(N, L, "SUBTRACT", 1.0, mn(N, L, "DIVIDE", mn(N, L, "ABSOLUTE", mn(N, L, "SUBTRACT", sep.outputs["Y"], wave)), 0.16), clamp=True)
below = mn(N, L, "MULTIPLY", mn(N, L, "LESS_THAN", sep.outputs["Y"], wave), glow)
wv = mn(N, L, "MULTIPLY", mn(N, L, "MAXIMUM", band, below), mn(N, L, "SUBTRACT", 1.0, inside))
rmx = N.new("ShaderNodeMix"); rmx.data_type = "RGBA"; L.new(mxd.outputs[2], rmx.inputs[6]); rmx.inputs[7].default_value = (0.9, 0.04, 0.03, 1)
L.new(mn(N, L, "MINIMUM", mn(N, L, "MULTIPLY", halo, 1.6), 0.9), rmx.inputs["Factor"]); L.new(rmx.outputs[2], b.inputs["Base Color"])
ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; ec.inputs[6].default_value = (1.0, 0.05, 0.03, 1); ec.inputs[7].default_value = (0.55, 1.0, 0.6, 1)
L.new(mn(N, L, "DIVIDE", wv, mn(N, L, "ADD", mn(N, L, "ADD", wv, halo), 0.0001)), ec.inputs["Factor"])
L.new(ec.outputs[2], b.inputs["Emission Color"])
L.new(mn(N, L, "ADD", mn(N, L, "MULTIPLY", halo, 2.2), mn(N, L, "MULTIPLY", wv, 3.0)), b.inputs["Emission Strength"])
# nuqta chizilishi
val_key(sm, "dot_r", 1, 0.0); val_key(sm, "dot_r", F_DOT - 2, 0.0); val_key(sm, "dot_r", F_DOT + 1, 0.55); val_key(sm, "dot_r", F_DOT + 14, 1.05)
for f, v in ((1, 0), (S["redot"][0] - 1, 0), (S["redot"][0], 0.0), (S["redot"][0] + 4, 1.0), (S["redot"][0] + 9, 0.45), (S["redot"][0] + 14, 1.0), (S["redot"][1], 0.6), (S["redot"][1] + 1, 0)):
    val_key(sm, "red", f, v)
W0, W1 = S["white"]
val_key(sm, "wave", 1, -0.3); val_key(sm, "wave", W0 + 4, -0.3); val_key(sm, "wave", W0 + 44, 1.25)
val_key(sm, "glow", 1, 0.0); val_key(sm, "glow", W0 + 4, 0.0); val_key(sm, "glow", W0 + 30, 0.55); val_key(sm, "glow", W1 - 6, 0.4); val_key(sm, "glow", W1 + 1, 0.0)
interp(sm.node_tree, "LINEAR")

# ko'zoynak (Head fazosi: X chap, Y tepa, Z old)
hd = child_of_bone("glasses", tarm, "Head")
gl_m = mat("glasses", (0.02, 0.03, 0.06), 0.25, coat=0.5)
lens_m = mat("glens", (0.9, 0.95, 1.0), 0.02, trans=1.0, alpha=0.25)
for sx in (-1, 1):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.024, minor_radius=0.0022, major_segments=40, minor_segments=8, location=(0, 0, 0))
    t = bpy.context.object; t.name = f"rim{sx}"; t.scale = (1.15, 0.82, 1.0); bpy.ops.object.transform_apply(scale=True)
    t.location = (sx * 0.033, 0.089, 0.148); t.parent = hd; t.data.materials.append(gl_m)
    for p in t.data.polygons: p.use_smooth = True
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.024, fill_type="NGON", location=(0, 0, 0))
    l_ = bpy.context.object; l_.name = f"glens{sx}"; l_.scale = (1.15, 0.82, 1); bpy.ops.object.transform_apply(scale=True)
    l_.location = (sx * 0.033, 0.089, 0.149); l_.parent = hd; l_.data.materials.append(lens_m)
    cyl(f"temple{sx}", 0.0018, 0.12, (sx * 0.062, 0.092, 0.09), gl_m, rot=(0, 0, 0), parent=hd).rotation_euler = (R(90), 0, 0)
cyl("bridge", 0.0018, 0.016, (0, 0.094, 0.151), gl_m, parent=hd).rotation_euler = (0, R(90), 0)

# marker (o'ng qo'lda, qo'l suyagi Y = barmoqlar)
hb_e = child_of_bone("marker_hand", tarm, "RightHand")
mk = empty("marker", (0.0, 0.085, 0.012), hb_e)
cyl("mk_body", 0.008, 0.11, (0, 0, 0), mat("mk_body", (0.95, 0.95, 0.95), 0.4), parent=mk).rotation_euler = (R(-90), 0, 0)
cyl("mk_cap", 0.0085, 0.03, (0, -0.055, 0), mat("mk_cap", (0.02, 0.02, 0.02), 0.35), parent=mk).rotation_euler = (R(-90), 0, 0)
cyl("mk_tip", 0.004, 0.02, (0, 0.063, 0), mat("mk_tip", (0.01, 0.01, 0.01), 0.6), parent=mk).rotation_euler = (R(-90), 0, 0)
MK_TIP = 0.085 + 0.073                                      # qo'l boshidan marker uchigacha (Y)
# harakatlar
IDLE = A_("Happy_Idle.fbx"); ASK = A_("Talking_7.fbx"); LOOK = A_("Looking_Around.fbx")
HANDS = A_("Hands_Forward_Gesture.fbx"); TALK = A_("Talking_2.fbx"); SAD = A_("Sad_Idle.fbx")
seg(tarm, SAD, 1, 125)                       # tinch turish (chizish paytida kam tebranadi)
seg(tarm, ASK, 126, 183, offset=0)
seg(tarm, IDLE, 184, 229)
seg(tarm, LOOK, 230, 289, offset=10)
seg(tarm, HANDS, 290, 343, offset=0)
seg(tarm, IDLE, 344, 445)
seg(tarm, TALK, 446, 520, offset=10)
seg(tarm, SAD, 840, END)
# chizish: IK (o'ng bilak) + DAMPED_TRACK (marker nuqtaga qaraydi) + barmoqlar marker ushlaydi
sc.frame_set(60); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
_se = shirt.evaluated_get(dg)
DOTW = shirt.matrix_world @ _se.data.vertices[DOT_I].co
print("DOT world @60", DOTW)
dotE = empty("dot_follow"); dotE.parent = shirt; dotE.parent_type = "VERTEX"; dotE.parent_vertices[0] = DOT_I
dotRig = empty("dot_rig"); _cl = dotRig.constraints.new("COPY_LOCATION"); _cl.target = dotE
O = V(0, 0, 0)
# chizish nishonlari Spine2 bilan yuradi (60-kadrdagi holatga nisbatan)
sp = tarm.pose.bones["mixamorig:Spine2"]
spM = tarm.matrix_world @ sp.matrix
loc_, rot_, _sc = spM.decompose()
spM_ns = Matrix.Translation(loc_) @ rot_.to_matrix().to_4x4()
chest = empty("chest_rig")
cc_ = chest.constraints.new("CHILD_OF"); cc_.target = tarm; cc_.subtarget = "mixamorig:Spine2"
cc_.use_scale_x = cc_.use_scale_y = cc_.use_scale_z = False; cc_.inverse_matrix = spM_ns.inverted()
FWD = V(0, 1, 0); RGT = V(1, 0, 0)                            # o'qituvchi +Y ga qaraydi, o'ng qo'li +X da
pinchE = empty("pinchE", tuple(DOTW + FWD * 0.004), chest)
DIRW = (RGT * 0.5 + FWD * 0.65 + V(0, 0, -0.55)).normalized()
wristE = empty("wristE", tuple(DOTW + DIRW * (MK_TIP + 0.004)), chest)
poleE = empty("poleE", tuple(DOTW + RGT * 0.5 + FWD * -0.1 + V(0, 0, -0.6)), chest)
fa = tarm.pose.bones["mixamorig:RightForeArm"]; hbn = tarm.pose.bones["mixamorig:RightHand"]
ik = fa.constraints.new("IK"); ik.target = wristE; ik.chain_count = 2; ik.use_tail = True
ik.pole_target = poleE; ik.pole_angle = R(90)
dt = hbn.constraints.new("DAMPED_TRACK"); dt.target = pinchE; dt.track_axis = "TRACK_Y"
curlE = empty("curlE", (1.0, 0, 0))
curls = []
for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
    for i in (1, 2, 3):
        pbn = tarm.pose.bones.get(f"mixamorig:RightHand{fn}{i}")
        if not pbn: continue
        c_ = pbn.constraints.new("TRANSFORM"); c_.target = curlE; c_.map_from = "LOCATION"; c_.from_min_x = 0; c_.from_max_x = 1
        c_.map_to = "ROTATION"; c_.owner_space = "LOCAL"; c_.target_space = "WORLD"; c_.mix_mode_rot = "AFTER"
        c_.map_to_x_from = "X"; c_.to_min_x_rot = 0
        c_.to_max_x_rot = R({"Index": 30, "Thumb": 20}.get(fn, 70))
        curls.append(c_)
def infl(cons, f, v):
    for con in cons: con.influence = v; con.keyframe_insert("influence", frame=f)
infl([ik, dt], 1, 0.0); infl([ik, dt], 14, 0.0); infl([ik, dt], 44, 1.0); infl([ik, dt], 100, 1.0); infl([ik, dt], 122, 0.0)
infl(curls, 1, 1.0)
# chizish harakati: uch tegadi (F_DOT), kichik aylana chizadi, ortga tortiladi
for f, off in ((14, 0.12), (44, 0.05), (F_DOT - 3, 0.012), (F_DOT, 0.0), (F_DOT + 12, 0.0), (F_DOT + 20, 0.05)):
    wristE.location = DOTW + DIRW * (MK_TIP + 0.004 + off); wristE.keyframe_insert("location", frame=f)
    pinchE.location = DOTW + FWD * 0.004 - DIRW * 0.0; pinchE.keyframe_insert("location", frame=f)
for k in range(1, 12):
    a = k / 12 * 2 * math.pi * 1.5
    wristE.location = DOTW + DIRW * (MK_TIP + 0.004) + V(math.cos(a) * 0.004, 0, math.sin(a) * 0.004)
    wristE.keyframe_insert("location", frame=F_DOT + k)
# marker: chizishdan keyin ham qo'lda (sinf kadrlarida); studiya kadrlarida ko'rinmaydi
vis(mk, rng("wide", "shirt", "dot", "class", "ask", "point", "redot", "look", "rest", "white", "nobody", "explain"))
vis(hd, CLASS_R)
vis(troot, CLASS_R)

# --- o'quvchilar ---
SEAT_IDLE = A_("Seated_Idle.fbx", inplace=False); POINTA = A_("Sitting_And_Pointing.fbx", inplace=False)
WRITE = A_("Writing.fbx", inplace=False); SIDE = A_("Sitting_5.fbx", inplace=False); DISB = A_("Sitting_Disbelief_2.fbx", inplace=False)
SEAT_Z = {SEAT_IDLE.name: 0.0, POINTA.name: 0.07, WRITE.name: 0.01, SIDE.name: 0.03, DISB.name: 0.04}
STUDENTS = [("jody", "Jody.fbx", (0, 1)), ("leonard", "Leonard.fbx", (0, 2)), ("sophie", "Sophie.fbx", (0, 0)), ("martha", "Martha.fbx", (0, 3)),
            ("josh", "Josh.fbx", (1, 1)), ("suzie", "Suzie.fbx", (1, 2)), ("shannon", "Shannon.fbx", (1, 0)), ("bryce", "Bryce.fbx", (1, 3))]
CH = {}
for i, (nm_, fl, seat) in enumerate(STUDENTS):
    r_, a_, ms = char(nm_, fl)
    CH[nm_] = (r_, a_, ms)
    base = SEATS[seat]
    rz = random.uniform(-6, 6)
    plan = [(1, WRITE if i % 3 == 1 else SEAT_IDLE, 0), (170, POINTA, -2 - (i % 4) * 2), (230, SEAT_IDLE, 0),
            (400, SIDE if i % 2 == 0 else DISB, 4 + (i % 3) * 3), (469, SEAT_IDLE, 0)]
    for k, (f0, act, off) in enumerate(plan):
        f1 = plan[k + 1][0] - 1 if k + 1 < len(plan) else S["explain"][1]
        seg(a_, act, f0, f1, offset=-off if off < 0 else off)
        rkey(r_, f0, base + V(0, 0, SEAT_Z[act.name]), rz)
    const(r_)
    if nm_ not in ("jody", "leonard"): vis(r_, CLASS_R)

# --- qiz (Jody) va bola (Bryce) studiyada ---
jr, ja, jm = CH["jody"]; br, ba, bmz = CH["leonard"]          # qiz va bola (Leonard)
GPOS = S0 + V(0.27, 0.0, 0); BPOS = S0 + V(-0.33, 0.06, 0)
HAPPY = A_("Happy_Idle.fbx"); GIVE = A_("Happy_Hand_Gesture.fbx"); DISM = A_("Dismissing_Gesture_2.fbx")
AWAY = A_("Look_Away_Gesture.fbx")
K0, K1 = S["kind"]; H0, H1 = S["hurt"]; M0, M1 = S["memory"]; B0, B1 = S["bias"]; E0, E1 = S["end"]
# qiz
rkey(jr, K0, GPOS, -32); rkey(jr, M0, GPOS, -8); rkey(jr, S["brain"][0], GPOS, -8); rkey(jr, E0, GPOS + V(0.05, 0, 0), -150)
const(jr)
seg(ja, TALK, K0, H0 + 12, offset=40)
seg(ja, SAD, H0 + 13, E0 - 1, offset=0, bi=6)
seg(ja, SAD, E0, E1)
# bola
rkey(br, K0, BPOS, 40)
rkey(br, M0, S0 + V(-40, 0, 0), 0); rkey(br, E0, S0 + V(-0.38, 0.3, 0), 25)
interp(br, "CONSTANT")
seg(ba, GIVE, K0, K0 + 30, offset=0)
seg(ba, GIVE, K0 + 31, H0 - 1, offset=0)
seg(ba, DISM, H0, M0 - 1, offset=4)
seg(ba, GIVE, E0, E1, offset=6)
# olma (bolaning o'ng qo'lida, "yaxshilik")
ah = child_of_bone("apple_hand", ba, "RightHand")
apr, apo = import_gltf(PH + "food_apple_01/food_apple_01.gltf", (0.0, 0.09, 0.05), (90, 0, 0), 1.0, ah)
vis(apr, [S["kind"]])

# ======================================================================
# 4) STUDIYA EFFEKTLARI: yuraklar (x10), fikr pufagi, rentgen + miya, pufaklar orbitasi
# ======================================================================
def heart_mesh(name, size, m, parent=None):
    bm = bmesh.new(); vs = []
    for k in range(48):
        t = 2 * math.pi * k / 48
        x = 16 * math.sin(t) ** 3; z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        vs.append(bm.verts.new((x * size / 32, 0, z * size / 32)))
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f]);
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.y += size * 0.35
    me = bpy.data.meshes.new(name); bm.to_mesh(me); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(m); o.parent = parent
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = size * 0.12; bv.segments = 4
    sub = o.modifiers.new("s", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    for p in o.data.polygons: p.use_smooth = True
    return o
heart_m = mat("heart", (1.0, 0.18, 0.35), 0.3, emit=1.5, emit_col=(1.0, 0.25, 0.4), coat=1.0)
hearts = empty("hearts", tuple(S0))
for k in range(10):
    a = R(-70 + k * 140 / 9)
    pos = V(math.sin(a) * 0.62, -0.25, 1.62 + math.cos(a) * 0.36)
    h = heart_mesh(f"heart{k}", 0.13, heart_m, hearts); h.location = pos; h.rotation_euler = (0, R(-math.degrees(a) * 0.3), 0)
    f = F_HEART0 + k * 3
    key(h, K0, scale=0.0); key(h, f, scale=0.0); key(h, f + 4, scale=1.25); key(h, f + 7, scale=1.0)
    key(h, H0 + 2, scale=1.0); key(h, H0 + 7, scale=0.0)
txt_c = bpy.data.curves.new("x10", "FONT"); txt_c.body = "x10"; txt_c.align_x = "CENTER"; txt_c.extrude = 0.025; txt_c.bevel_depth = 0.006; txt_c.size = 0.28
fp = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
if os.path.exists(fp): txt_c.font = bpy.data.fonts.load(fp)
x10 = bpy.data.objects.new("x10", txt_c); sc.collection.objects.link(x10); x10.parent = hearts
x10.location = (0, -0.3, 2.06); x10.rotation_euler = (R(90), 0, 0)
x10.data.materials.append(mat("x10", (1.0, 0.85, 0.2), 0.3, emit=2.0, emit_col=(1.0, 0.8, 0.2)))
key(x10, K0, scale=0.0); key(x10, F_HEART0 + 27, scale=0.0); key(x10, F_HEART0 + 31, scale=1.3); key(x10, F_HEART0 + 34, scale=1.0)
key(x10, H0 + 2, scale=1.0); key(x10, H0 + 7, scale=0.0)
vis(hearts, rng("kind", "hurt"))

# yomon lahza: bolaning qo'l siltashi paytida qizil chaqnash (qiz ko'kragida yorilish o'rniga — qizil halqa)
def image_mat(name, path, rim_col, rim_w=0.08, emit=1.0):
    """yumaloq pufak ichida rasm (emission) + yumshoq oq/rangli chekka; alfa doiradan tashqarida 0"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord")
    im = N.new("ShaderNodeTexImage")
    if os.path.exists(path):
        im.image = bpy.data.images.load(path)
    mp = N.new("ShaderNodeMapping"); 
    L.new(tc.outputs["UV"], mp.inputs[0]); L.new(mp.outputs[0], im.inputs[0])
    d = mn(N, L, "LENGTH", mn(N, L, "SUBTRACT", tc.outputs["UV"], (0.5, 0.5, 0), vec=True), vec=True)
    a = mn(N, L, "LESS_THAN", d, 0.5)
    rim = mn(N, L, "MULTIPLY", mn(N, L, "SUBTRACT", 1.0, mn(N, L, "DIVIDE", mn(N, L, "ABSOLUTE", mn(N, L, "SUBTRACT", d, 0.5 - rim_w / 2)), rim_w / 2), clamp=True), a)
    e1 = N.new("ShaderNodeEmission"); L.new(im.outputs[0], e1.inputs["Color"])
    k = value_node(m, "k", emit); L.new(k, e1.inputs["Strength"])
    if not os.path.exists(path): e1.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
    e2 = N.new("ShaderNodeEmission"); e2.inputs["Color"].default_value = (*rim_col, 1); L.new(mn(N, L, "MULTIPLY", k, 2.5), e2.inputs["Strength"])
    mx = N.new("ShaderNodeMixShader"); L.new(rim, mx.inputs[0]); L.new(e1.outputs[0], mx.inputs[1]); L.new(e2.outputs[0], mx.inputs[2])
    tr = N.new("ShaderNodeBsdfTransparent")
    al = value_node(m, "alpha", 1.0)
    mx2 = N.new("ShaderNodeMixShader"); L.new(mn(N, L, "MULTIPLY", a, al), mx2.inputs[0]); L.new(tr.outputs[0], mx2.inputs[1]); L.new(mx.outputs[0], mx2.inputs[2])
    L.new(mx2.outputs[0], out.inputs[0])
    return m
def bubble(name, path, size, rim_col, parent, emit=1.0, rim_w=0.08):
    o = plane(name, (size, size), (0, 0, 0), image_mat(name + "_m", path, rim_col, rim_w, emit), rot=(0, 0, 0), parent=parent)
    o.data.uv_layers.active.name = "UVMap"
    return o
def billboard(o, camobj):
    t = o.constraints.new("TRACK_TO"); t.target = camobj; t.track_axis = "TRACK_Z"; t.up_axis = "UP_Y"

# qizning boshi (studiyada, harakatdan mustaqil — bosh suyagiga bog'langan)
jhead = child_of_bone("jody_head", ja, "Head")
# fikr pufagi (memory): boshdan tepada
mem = empty("memory", tuple(GPOS + V(-0.05, -0.05, 2.12)))
# kameralar keyin yaratiladi — billboard uchun oldindan bo'sh joy
# ======================================================================
# 5) KAMERALAR
# ======================================================================
T = TPOS
TH = T + V(0, 0, 1.52)                   # o'qituvchi boshi
cam("wide", [(1, T + V(0.55, 1.75, 0.75)), (31, T + V(0.38, 1.45, 0.85))], [(1, T + V(0, 0, 1.15)), (31, T + V(0, 0, 1.22))], 22, 5.6)
cam("shirt", [(32, V(-0.3, 0.6, 0.06)), (61, V(-0.2, 0.5, 0.04))], [(32, V(0, 0, 0.04)), (61, V(0, 0, 0.01))], 45, 2.8, parent=dotRig)
c = cam("dot", [(62, V(-0.15, 0.29, 0.02)), (110, V(-0.12, 0.25, 0.015))], [(62, V(0.0, 0, 0.0)), (110, O)], 60, 7.0, clip=0.003, parent=dotRig)
shake(c, F_DOT, F_DOT + 6, 0.004, seed=3)
cam("class", [(111, V(0.35, 4.0, 1.75)), (146, V(0.3, 3.1, 1.6))], [(111, V(0, -3.2, 1.15)), (146, V(0, -3.2, 1.2))], 20, 8.0)
cam("ask", [(147, T + V(-0.45, 1.45, 0.65)), (183, T + V(-0.35, 1.25, 0.7))], [(147, T + V(0, 0, 1.3)), (183, T + V(0, 0, 1.33))], 28, 4.0)
c = cam("point", [(184, T + V(0.42, -0.42, 1.5)), (207, T + V(0.36, -0.3, 1.47))], [(184, V(-0.3, -0.9, 0.95)), (207, V(-0.2, -0.9, 0.98))], 15, 8.0)
c = cam("redot", [(208, V(0.06, 0.55, 0.06)), (229, V(0.04, 0.45, 0.04))], [(208, O), (229, O)], 35, 4.0, parent=dotRig)
lens_keys(c, [(208, 26), (213, 52), (229, 56)]); shake(c, 213, 220, 0.006, seed=5)
cam("look", [(230, T + V(-0.65, -0.75, 1.25)), (289, T + V(-0.5, -0.8, 1.3))], [(230, V(-2.5, 0.0, 1.0)), (289, V(2.3, 0.2, 1.0))], 26, 5.6)
cam("rest", [(290, T + V(0.2, 1.0, 1.35)), (343, T + V(0.12, 0.85, 1.33))], [(290, T + V(0, 0, 1.3)), (343, T + V(0, 0, 1.3))], 30, 3.5)
cam("white", [(344, T + V(0.0, 0.72, 1.12)), (409, T + V(0.05, 0.6, 1.15))], [(344, T + V(0, 0, 1.15)), (409, T + V(0, 0, 1.17))], 35, 4.0)
cam("nobody", [(410, V(-3.5, -2.3, 1.15)), (468, V(-3.4, -1.7, 1.2))], [(410, V(0.2, -0.3, 0.95)), (468, V(0.4, 0.0, 0.95))], 22, 5.6)
cam("explain", [(469, T + V(0.75, 1.15, 0.55)), (505, T + V(0.55, 0.95, 0.6))], [(469, T + V(0, 0, 1.4)), (505, T + V(0, 0, 1.42))], 24, 4.0)
G = GPOS; BP = BPOS
cam("kind", [(K0, S0 + V(0.1, -3.1, 1.2)), (K1, S0 + V(0.05, -2.75, 1.2))], [(K0, S0 + V(0, 0, 1.2)), (K1, S0 + V(0, 0, 1.25))], 28, 5.6)
c = cam("hurt", [(H0, S0 + V(-0.6, -2.0, 1.35)), (F_SAD - 6, S0 + V(-0.45, -1.8, 1.35)), (H1, S0 + V(-0.2, -1.4, 1.42))],
        [(H0, S0 + V(0, 0, 1.25)), (F_SAD - 6, S0 + V(0.2, 0, 1.3)), (F_SAD, G + V(-0.05, -0.05, 1.45)), (H1, G + V(-0.05, -0.05, 1.47))], 32, 4.0)
lens_keys(c, [(H0, 32), (F_SAD - 6, 34), (F_SAD, 62), (H1, 66)]); shake(c, F_SAD, F_SAD + 5, 0.01, seed=9)
c = cam("memory", [(M0, G + V(0.05, -1.05, 1.35)), (M0 + 30, G + V(0.0, -1.55, 1.55)), (M1, G + V(-0.05, -1.75, 1.75))],
        [(M0, G + V(0, 0, 1.42)), (M0 + 30, G + V(-0.03, 0, 1.75)), (M1, G + V(-0.05, 0, 1.9))], 30, 4.0)
BR0, BR1 = S["brain"]
brainRig = empty("brain_rig"); _cl = brainRig.constraints.new("COPY_LOCATION"); _cl.target = jhead
c = cam("brain", [(BR0, V(0.5, -0.85, 0.12)), (BR1, V(0.3, -0.6, 0.1))], [(BR0, V(0, -0.05, 0.08)), (BR1, V(0, -0.06, 0.08))], 38, 5.6, parent=brainRig)
orb = []
for k in range(5):
    a = R(-40 + k * 20)
    orb.append((B0 + k * 18, V(math.sin(a) * -1.05, math.cos(a) * -1.05, 0.15)))
c = cam("bias", orb, [(B0, V(0, -0.05, 0.08)), (B1, V(0, -0.05, 0.08))], 30, 8.0, parent=brainRig)
DT = DOTW - V(0, 0, 0)
c = cam("dotend", [(863, V(0.02, 0.16, 0.02)), (880, V(0.03, 0.24, 0.02)), (935, T - DT + V(0.15, 1.9, 1.1))],
        [(863, O), (880, O), (935, T - DT + V(0, 0, 1.15))], 70, 8.0, clip=0.003, parent=dotRig)
lens_keys(c, [(863, 70), (880, 70), (935, 26)])
cam("end", [(E0, S0 + V(0.1, -2.9, 1.2)), (E1, S0 + V(0.05, -2.35, 1.2))], [(E0, S0 + V(0, 0, 1.1)), (E1, S0 + V(0, 0, 1.15))], 28, 5.6)
for n, cc in CAMS.items():
    for fc in fcurves(cc):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["wide"]

# --- fikr pufagi (memory) ---
img_hurt = STILL_DIR + "hurt.png"; img_kind = STILL_DIR + "kind.png"
mb = bubble("mem_bubble", img_hurt, 0.62, (1.0, 1.0, 1.0), mem, emit=1.1, rim_w=0.06)
billboard(mb, CAMS["memory"])
key(mem, M0, scale=0.0); key(mem, M0 + 34, scale=0.0); key(mem, M0 + 40, scale=1.15); key(mem, M0 + 44, scale=1.0)
puff_m = mat("puff", (0.95, 0.97, 1.0), 0.4, emit=0.8, emit_col=(1, 1, 1))
for k, (dz, r) in enumerate(((1.68, 0.025), (1.78, 0.038), (1.9, 0.055))):
    p = uvsphere(f"puff{k}", tuple(GPOS + V(-0.03, -0.06, dz)), r, puff_m)
    f = M0 + 12 + k * 7
    key(p, M0, scale=0.0); key(p, f, scale=0.0); key(p, f + 4, scale=1.3); key(p, f + 6, scale=1.0)
    vis(p, [S["memory"]])
vis(mem, [S["memory"]])

# --- rentgen + miya (brain, bias) ---
XR_R = rng("brain", "bias")
xr_m = P.xray_material("xray_jody", (0.35, 0.85, 1.0), 1.4, 0.03)
for o in jm:
    for i, m in enumerate(o.data.materials):
        if not m: continue
        m2 = m.copy(); o.data.materials[i] = m2
        N = m2.node_tree.nodes; L = m2.node_tree.links; out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
        src = out.inputs["Surface"].links[0].from_socket
        # rentgen qatlami (xray_material nodlarini nusxalash o'rniga: Layer Weight + emission + transparent)
        lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
        fac = mn(N, L, "POWER", lw.outputs["Facing"], 1.6)
        em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.85, 1.0, 1)
        L.new(mn(N, L, "ADD", mn(N, L, "MULTIPLY", fac, 1.4), 0.03), em.inputs["Strength"])
        tr = N.new("ShaderNodeBsdfTransparent")
        mx = N.new("ShaderNodeMixShader"); L.new(mn(N, L, "ADD", mn(N, L, "MULTIPLY", fac, 0.7), 0.05, clamp=True), mx.inputs[0])
        L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
        xv = value_node(m2, "xr", 0.0)
        mx2 = N.new("ShaderNodeMixShader"); L.new(xv, mx2.inputs[0]); L.new(src, mx2.inputs[1]); L.new(mx.outputs[0], mx2.inputs[2])
        L.new(mx2.outputs[0], out.inputs["Surface"])
        for f, v in ((1, 0.0), (BR0, 0.0), (BR0 + 14, 1.0), (B1, 1.0), (B1 + 1, 0.0)):
            val_key(m2, "xr", f, v)
        interp(m2.node_tree, "LINEAR")
brainE = empty("brain_off", (0.0, 0.105, 0.015), jhead); brainE.rotation_euler = (R(-90), 0, 0)
brain, brain_m = P.build_brain("brain", brainE, size=0.088)
val_key(brain_m, "glow", 1, 0.0); val_key(brain_m, "glow", BR0 + 10, 0.0); val_key(brain_m, "glow", BR0 + 24, 0.6)
val_key(brain_m, "glow", B0 + 30, 0.6); val_key(brain_m, "glow", B0 + 40, 2.2); val_key(brain_m, "glow", B1, 2.6)
# miya rangi: salbiy lahzada qizaradi
_bN = brain_m.node_tree.nodes; _bb = _bN["Principled BSDF"]
_bb.inputs["Emission Color"].default_value = (1.0, 0.55, 0.65, 1); _bb.inputs["Emission Color"].keyframe_insert("default_value", frame=B0 + 30)
_bb.inputs["Emission Color"].default_value = (1.0, 0.12, 0.1, 1); _bb.inputs["Emission Color"].keyframe_insert("default_value", frame=B0 + 42)
vis(brainE, XR_R)
# pufaklar orbitasi: 4 ta yaxshi (yashil, xira, kichik) va 1 ta yomon (qizil, katta)
orbit = empty("orbit", tuple(GPOS + V(0, 0, 1.55)))
key(orbit, B0, rot=(0, 0, 0)); key(orbit, B1, rot=(0, 0, 95)); interp(orbit, "LINEAR")
for k in range(5):
    a = R(k * 72 + 20)
    bad = (k == 0)
    e = empty(f"ob{k}", (math.cos(a) * 0.42, math.sin(a) * 0.42, 0.12 * math.sin(a * 2)), orbit)
    o = bubble(f"ob_img{k}", img_hurt if bad else img_kind, 0.24 if not bad else 0.3, (1.0, 0.1, 0.08) if bad else (0.4, 1.0, 0.55), e, emit=1.0 if bad else 0.75)
    billboard(o, CAMS["bias"])
    m_ = o.data.materials[0]
    if bad:
        key(e, B0, scale=0.0); key(e, B0 + 6, scale=1.0); key(e, B0 + 30, scale=1.0); key(e, B0 + 42, scale=1.9); key(e, B1, scale=2.0)
        val_key(m_, "k", B0 + 30, 1.0); val_key(m_, "k", B0 + 40, 1.8)
    else:
        key(e, B0, scale=0.0); key(e, B0 + 4 + k * 3, scale=0.0); key(e, B0 + 9 + k * 3, scale=1.0); key(e, B0 + 30, scale=1.0); key(e, B0 + 44, scale=0.7)
        val_key(m_, "k", B0 + 30, 0.75); val_key(m_, "k", B0 + 44, 0.3); val_key(m_, "alpha", B0 + 30, 1.0); val_key(m_, "alpha", B0 + 44, 0.45)
vis(orbit, [S["bias"]])

# ======================================================================
# 6) YORUG'LIK va DUNYO
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bgH = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bgH.inputs[0])
bgT = N.new("ShaderNodeBackground"); bgT.inputs[0].default_value = (0.05, 0.4, 0.46, 1)
add = N.new("ShaderNodeAddShader"); L.new(bgH.outputs[0], add.inputs[0]); L.new(bgT.outputs[0], add.inputs[1]); L.new(add.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    st = n in STUDN
    bgH.inputs[1].default_value = 0.0 if st else 0.8; bgH.inputs[1].keyframe_insert("default_value", frame=f)
    bgT.inputs[1].default_value = (0.25 if n not in ("brain", "bias") else 0.12) if st else 0.0; bgT.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# sinf: quyosh (derazadan), shift lampalari, doska tomondan yumshoq yorug'lik
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(52), 0, R(90 + 18)); sun.data.angle = R(2.0); sun.data.color = (1.0, 0.93, 0.82)
for f, e in lights_for(CLASS_R, 4.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
CT = empty("classT", (0, -1.5, 1.0))
for i, (x, y) in enumerate(((-1.6, -2.4), (1.6, -2.4), (-1.6, 0.6), (1.6, 0.6))):
    l = area(f"C_ceil{i}", (x, y, 2.9), 1.2, (1.0, 0.96, 0.9), lights_for(CLASS_R, 140.0)); l.rotation_euler = (0, 0, 0)
area("C_key", (1.2, -1.4, 2.2), 1.5, (1.0, 0.95, 0.88), lights_for(CLASS_R, 180.0), target=empty("tkT", tuple(T + V(0, 0, 1.3))))
area("C_rim", (-1.2, -4.2, 2.4), 0.8, (0.8, 0.9, 1.0), lights_for(CLASS_R, 70.0), target=empty("trT", tuple(T + V(0, 0, 1.4))))
# makro (nuqta) uchun yumshoq oldingi yorug'lik
area("C_macro", tuple(DOTW + V(0.25, 0.45, 0.35)), 0.4, (1.0, 0.97, 0.92), lights_for(rng("dot", "redot", "dotend", "white", "shirt"), 18.0), target=empty("dmT", tuple(DOTW)))
# studiya
ST_T = empty("studT", tuple(S0 + V(0, 0, 1.2)))
area("S_key", tuple(S0 + V(-1.8, -2.2, 2.8)), 2.0, (1.0, 0.96, 0.9), lights_for(STUD_R, 420.0), target=ST_T)
area("S_fill", tuple(S0 + V(2.2, -1.8, 1.6)), 2.0, (0.85, 0.95, 1.0), lights_for(STUD_R, 160.0), target=ST_T)
area("S_rim", tuple(S0 + V(0.5, 2.0, 2.6)), 1.2, (1.0, 0.92, 0.85), lights_for(STUD_R, 260.0), target=ST_T)
# ko'rinish: har dunyo faqat o'z kadrlarida
def has_vis(o): return any(fc.data_path == "hide_render" for fc in fcurves(o))
def vis_world(objs, ranges):
    for o in objs:
        if not has_vis(o): vis(o, ranges, recursive=False)
vis_world([room] + list(room.children_recursive), CLASS_R)
vis_world([stud] + list(stud.children_recursive), STUD_R)

# ======================================================================
# 7) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 4
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
    os.makedirs(OUT, exist_ok=True)
    fs = os.environ.get("FRAMES")
    if os.environ.get("STILLS"):
        for mk_ in sc.timeline_markers: mk_.camera = None
        # pufak rasmlari: yaxshilik (olma) va yomon lahza (qo'l siltash) — kvadrat, 40%
        r.resolution_x, r.resolution_y = 1080, 1080
        for name, f in (("kind", 523), ("hurt", 584)):
            sc.frame_set(f); sc.camera = CAMS["kind"]
            r.filepath = f"{OUT}{name}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    elif fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
