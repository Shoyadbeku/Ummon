# Balkondan yiqilgan bola (kafe ayvoni + shifokor) — Zack D. Films uslubida 34.2 s video (822 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; yordamchilar tirnoq_osishi.py dan; chaqaloq: baby.py (protsedural).
# Assetlar: zack_test/tools/get_balkon.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/balkon/balkon.py --render
# Sinov:  FRAMES=20,60,140,230,300,400,500,560,640,700,780 PCT=30 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Quaternion, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import baby as BB
sc = bpy.context.scene
sc.render.fps = 24
END = 822
sc.frame_start, sc.frame_end = 1, END
V = lambda *a: Vector(a)


# ---------------- yordamchilar ----------------
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

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

def emis(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    m.node_tree.links.new(e.outputs[0], N["Material Output"].inputs[0])
    return m

def pbr(name, folder, scale=1.0, tint=None, proj="BOX", rough_mul=1.0):
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
    rr = img("rough.jpg", True)
    if rough_mul != 1.0:
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        L.new(rr.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], b.inputs["Roughness"])
    else:
        L.new(rr.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); o = bpy.context.object
    o.name = name
    for v in o.data.vertices: v.co = Vector((v.co.x * size[0] / 2, v.co.y * size[1] / 2, v.co.z * size[2] / 2))
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if m: o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 2
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.location = loc; o.scale = scale
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def rod(name, p0, p1, r, m, parent=None):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    c = cyl(name, r, d.length, (p0 + p1) / 2, m, parent=parent)
    c.rotation_mode = "QUATERNION"; c.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return c

def bool_solver(md):
    ids = [i.identifier for i in md.bl_rna.properties["solver"].enum_items]
    md.solver = "MANIFOLD" if "MANIFOLD" in ids else ("FLOAT" if "FLOAT" in ids else "FAST")

def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); o = bpy.context.object; o.name = name; return o

def import_gltf(path, loc, rot=(0, 0, 0), scale=1.0, parent=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc, parent)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler = [R(a) for a in rot]; root.scale = scale if isinstance(scale, tuple) else (scale,) * 3
    return root

def ph_model(mid, loc, rot=(0, 0, 0), scale=1.0, parent=None):
    return import_gltf(f"{PH}{mid}/{mid}.gltf", loc, rot, scale, parent)

def text_obj(name, body, size, loc, m, extrude=0.02, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = align; cu.align_y = "CENTER"
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.location = loc
    cu.materials.append(m); return o

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else float(x >= a); return t * t * (3 - 2 * t)

def lerp(a, b, t): return a + (b - a) * t

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.02):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 600
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

def area(name, loc, size, col, keys, target=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    l.visible_camera = cam_vis
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, const=True, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc; l.visible_camera = False
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys


# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "stand"), (37, "squeeze"), (73, "fall"), (111, "meter"), (163, "awning"), (221, "hit"), (247, "launch"),
         (275, "arc"), (331, "doctor"), (381, "face"), (426, "run"), (472, "catch"), (531, "cry"), (595, "sleep"),
         (671, "parents"), (733, "arrest")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

FLOOR6 = 18.0                 # balkon poli
F_HIT = 228                   # ayvonga tegish (hit kadrida)
F_LAUNCH = 240
F_CATCH = 486                 # quchoqqa tushish
G = 9.8

# ======================================================================
# 1) MATERIALLAR
# ======================================================================
M = dict(
    stucco_a=pbr("stucco_a", "white_stucco", 0.35, tint=(0.8, 0.68, 0.54)),
    stucco_b=pbr("stucco_b", "white_stucco", 0.35, tint=(0.82, 0.8, 0.78)),
    stucco_c=pbr("stucco_c", "white_stucco", 0.35, tint=(0.95, 0.75, 0.62)),
    stucco_d=pbr("stucco_d", "white_stucco", 0.35, tint=(0.78, 0.82, 0.86)),
    brick=pbr("brick", "red_brick_03", 0.5, tint=(0.9, 0.8, 0.75)),
    plaster=pbr("plaster", "painted_plaster_wall", 0.6, tint=(0.95, 0.9, 0.82)),
    asphalt=pbr("asphalt", "asphalt_02", 0.12),
    pave=pbr("pave", "concrete_pavement", 0.4),
    floor=pbr("floor", "laminate_floor_02", 0.5),
    stone=mat("stone", (0.82, 0.78, 0.7), 0.7),
    white=mat("white_paint", (0.9, 0.9, 0.88), 0.35),
    iron=mat("iron", (0.02, 0.02, 0.022), 0.35, metal=0.6),
    glass=mat("win_glass", (0.03, 0.035, 0.04), 0.04, coat=1.0),
    shopglass=mat("shop_glass", (0.08, 0.06, 0.04), 0.05, coat=1.0, emit=0.22, emit_col=(1.0, 0.72, 0.42)),
    green=mat("shop_green", (0.03, 0.12, 0.08), 0.35, coat=0.4),
    navy=mat("shop_navy", (0.03, 0.05, 0.14), 0.35, coat=0.4),
    gold=mat("gold", (0.9, 0.68, 0.3), 0.25, metal=1.0),
    curb=mat("curb", (0.55, 0.54, 0.52), 0.8),
    line=mat("line", (0.9, 0.9, 0.86), 0.6),
    roof=mat("roof", (0.18, 0.2, 0.24), 0.45, metal=0.5),
    door=mat("door_wood", (0.12, 0.06, 0.03), 0.35, coat=0.4),
    wood=mat("wood", (0.55, 0.36, 0.2), 0.45),
    dark=mat("dark", (0.01, 0.01, 0.012), 0.8),
)
# derazalar ortidagi pardalar (har derazada boshqacha)
def curtain_mat():
    m = bpy.data.materials.new("curtain"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    oi = N.new("ShaderNodeObjectInfo"); cr = N.new("ShaderNodeValToRGB")
    e = cr.color_ramp; e.interpolation = "CONSTANT"
    cols = [(0.75, 0.7, 0.6), (0.15, 0.12, 0.1), (0.6, 0.62, 0.66), (0.85, 0.82, 0.75), (0.08, 0.08, 0.1), (0.7, 0.55, 0.4)]
    e.elements[0].color = (*cols[0], 1); e.elements[1].position = 0.99; e.elements[1].color = (*cols[-1], 1)
    for i, c in enumerate(cols[1:-1]):
        p = e.elements.new((i + 1) / len(cols)); p.color = (*c, 1)
    L.new(oi.outputs["Random"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    return m
M["curtain"] = curtain_mat()

# ======================================================================
# 2) BINOLAR (protsedural Parij fasadi)
# ======================================================================
WIN_W, WIN_H = 1.1, 2.0

def window_unit(name, balconette=True):
    """deraza (lokal: pastki markaz fasad tekisligida, fasad -Y ga qaraydi)"""
    parts = []
    g = box("g", (WIN_W, 0.02, WIN_H), (0, 0.22, WIN_H / 2), M["glass"]); parts.append(g)
    fw = 0.07
    for x in (-WIN_W / 2 + fw / 2, WIN_W / 2 - fw / 2, 0):
        parts.append(box("f", (fw if x else 0.05, 0.08, WIN_H), (x, 0.2, WIN_H / 2), M["white"]))
    for z in (fw / 2, WIN_H - fw / 2, WIN_H * 0.72):
        parts.append(box("f", (WIN_W, 0.08, fw if z != WIN_H * 0.72 else 0.05), (0, 0.2, z), M["white"]))
    # deraza o'yig'i (reveal) devorlari
    for x in (-WIN_W / 2 - 0.01, WIN_W / 2 + 0.01):
        parts.append(box("rv", (0.02, 0.26, WIN_H), (x, 0.12, WIN_H / 2), M["stone"]))
    parts.append(box("rv", (WIN_W + 0.04, 0.26, 0.02), (0, 0.12, WIN_H + 0.01), M["stone"]))
    # tosh tokcha va ustidagi bezak
    parts.append(box("sill", (WIN_W + 0.3, 0.14, 0.08), (0, -0.03, -0.02), M["stone"]))
    parts.append(box("lint", (WIN_W + 0.36, 0.12, 0.22), (0, -0.04, WIN_H + 0.14), M["stone"]))
    parts.append(box("key", (0.2, 0.14, 0.3), (0, -0.05, WIN_H + 0.17), M["stone"]))
    # parda (ichkarida)
    c = box("cur", (WIN_W * 0.5, 0.02, WIN_H * 0.95), (-WIN_W * 0.22, 0.27, WIN_H / 2), M["curtain"]); parts.append(c)
    if balconette:
        ry = -0.16
        parts.append(box("rt", (WIN_W + 0.2, 0.05, 0.04), (0, ry, 1.0), M["iron"]))
        parts.append(box("rb", (WIN_W + 0.2, 0.04, 0.03), (0, ry, 0.12), M["iron"]))
        for i in range(13):
            x = -WIN_W / 2 - 0.05 + i * (WIN_W + 0.1) / 12
            parts.append(box("rbar", (0.014, 0.014, 0.88), (x, ry, 0.56), M["iron"]))
        for x in (-WIN_W / 2 - 0.08, WIN_W / 2 + 0.08):
            parts.append(box("rside", (0.03, 0.18, 0.03), (x, ry / 2 + 0.03, 1.0), M["iron"]))
    o = join(parts, name)
    return o

WU_BAL = window_unit("WU_bal", True)
WU_PLAIN = window_unit("WU_plain", False)
WU_BAL.location = (0, 0, -100); WU_PLAIN.location = (0, 0, -100)

def facade(name, x0, x1, floors, wall_m, parent, win_xs, ground=None, skip=(), roof_col=None):
    """fasad lokal koordinatada: y=0 tekislik, bino +Y tomonda, -Y ko'chaga qaraydi. 0..3 m — yer qavati."""
    H = 3.0 * (floors + 1)
    wall = box(name + "_wall", (x1 - x0, 0.5, H), ((x0 + x1) / 2, 0.25, H / 2), wall_m)
    cutters = []
    for k in range(1, floors + 1):
        for x in win_xs:
            if (k, x) in skip: continue
            cutters.append(box("cut", (WIN_W + 0.02, 0.6, WIN_H), (x, 0.0, 3.0 * k + 0.5 + WIN_H / 2), None))
    for (gx, gw, gh) in (ground or []):
        cutters.append(box("cut", (gw, 0.6, gh), (gx, 0.0, gh / 2 - 0.01), None))
    if cutters:
        ct = join(cutters, name + "_cut")
        bm_ = wall.modifiers.new("cut", "BOOLEAN"); bm_.operation = "DIFFERENCE"; bm_.object = ct; bool_solver(bm_)
        bpy.context.view_layer.objects.active = wall; bpy.ops.object.modifier_apply(modifier="cut")
        bpy.data.objects.remove(ct)
    wall.parent = parent
    objs = [wall]
    for k in range(1, floors + 1):
        for x in win_xs:
            if (k, x) in skip: continue
            w = (WU_BAL if k < floors else WU_PLAIN).copy(); sc.collection.objects.link(w)
            w.location = (x, 0, 3.0 * k + 0.5); w.parent = parent; objs.append(w)
        # qavat kornizi
        objs.append(box(name + "_cor", (x1 - x0 + 0.1, 0.18, 0.16), ((x0 + x1) / 2, -0.08, 3.0 * k + 0.02), M["stone"], parent=parent))
    objs.append(box(name + "_cor_top", (x1 - x0 + 0.3, 0.5, 0.35), ((x0 + x1) / 2, -0.2, H + 0.1), M["stone"], parent=parent))
    objs.append(box(name + "_cor_g", (x1 - x0 + 0.1, 0.3, 0.3), ((x0 + x1) / 2, -0.12, 3.0), M["stone"], parent=parent))
    # mansarda tomi
    rf = box(name + "_roof", (x1 - x0, 3.0, 2.6), ((x0 + x1) / 2, 1.6, H + 1.4), roof_col or M["roof"], parent=parent)
    rf.rotation_euler = (R(-22), 0, 0)
    objs.append(rf)
    for x in win_xs[::2]:
        objs.append(box(name + "_dormer", (1.0, 0.8, 1.3), (x, 0.9, H + 1.1), M["white"], parent=parent))
        objs.append(box(name + "_dormer_g", (0.6, 0.05, 0.8), (x, 0.48, H + 1.1), M["glass"], parent=parent))
    return objs

# --- A bino (fasad y=0) ---
A = empty("bldgA")
XS = [-12 + 2.4 * i for i in range(11)]
GROUND_A = [(-3.0, 1.9, 2.6), (0.0, 1.4, 2.6), (3.0, 1.9, 2.6), (7.5, 1.4, 2.6), (-9.0, 3.2, 2.5), (11.0, 2.6, 2.5)]
facade("A", -13.4, 13.4, 6, M["stucco_a"], A, XS, ground=GROUND_A, skip={(6, 0.0)})
# qo'shni binolar
AL = empty("bldgAL"); facade("AL", -30.0, -13.4, 5, M["stucco_c"], AL, [-28 + 2.3 * i for i in range(7)], ground=[(-22, 4, 2.5)])
AR = empty("bldgAR"); facade("AR", 13.4, 32.0, 7, M["stucco_d"], AR, [15.2 + 2.3 * i for i in range(8)], ground=[(22, 4, 2.5)])
for P_ in (AL, AR):
    pass
# --- B bino (narigi tomon, fasad y=-15, +Y ga qaraydi) ---
B = empty("bldgB", (0, -15.0, 0)); B.rotation_euler = (0, 0, R(180))
facade("B", -13.4, 13.4, 5, M["stucco_b"], B, [-12 + 2.4 * i for i in range(11)], ground=[(-5.0, 1.9, 2.6), (-2.0, 1.9, 2.6), (1.0, 1.4, 2.6), (-9.6, 2.4, 2.5), (9.0, 3.2, 2.5)])
BL = empty("bldgBL", (0, -15.0, 0)); BL.rotation_euler = (0, 0, R(180)); facade("BL", -32.0, -13.4, 6, M["stucco_a"], BL, [-30 + 2.3 * i for i in range(8)], ground=[(-22, 4, 2.5)])
BR = empty("bldgBR", (0, -15.0, 0)); BR.rotation_euler = (0, 0, R(180)); facade("BR", 13.4, 30.0, 6, M["stucco_c"], BR, [15.2 + 2.3 * i for i in range(7)], ground=[(22, 4, 2.5)])

# yer qavati to'ldirgichlari (o'yiqlarga vitrina/eshik)
def shopfront(x, w, h, frame_m, glass_m, parent, door=False):
    o = []
    o.append(box("sf_g", (w, 0.04, h), (x, 0.27, h / 2), glass_m, parent=parent))
    for xx in (x - w / 2 + 0.06, x + w / 2 - 0.06):
        o.append(box("sf_f", (0.12, 0.12, h), (xx, 0.26, h / 2), frame_m, parent=parent))
    o.append(box("sf_t", (w, 0.12, 0.14), (x, 0.26, h - 0.07), frame_m, parent=parent))
    o.append(box("sf_b", (w, 0.14, 0.45), (x, 0.24, 0.225), frame_m, parent=parent))
    if door:
        o.append(box("sf_d", (0.06, 0.12, h), (x, 0.26, h / 2), frame_m, parent=parent))
    return o
for gx, gw, gh in GROUND_A:
    if gx == 7.5:   # uy eshigi
        box("A_door", (gw, 0.1, gh), (gx, 0.25, gh / 2), M["door"], parent=A)
        box("A_knob", (0.05, 0.08, 0.05), (gx + 0.5, 0.22, 1.05), M["gold"], parent=A)
    elif abs(gx) <= 3.0:
        shopfront(gx, gw, gh, M["green"], M["shopglass"], A, door=(gx == 0.0))
    else:
        shopfront(gx, gw, gh, M["navy"], M["glass"], A)
for gx, gw, gh in [(-5.0, 1.9, 2.6), (-2.0, 1.9, 2.6), (1.0, 1.4, 2.6), (-9.6, 2.4, 2.5), (9.0, 3.2, 2.5)]:
    shopfront(gx, gw, gh, M["navy"] if gx > -8 else M["green"], M["shopglass"] if gx > -8 else M["glass"], B, door=(gx == 1.0))
# kafe peshtaxtasi (A) va yozuvi
box("A_sign", (7.6, 0.14, 0.42), (0, -0.07, 2.78), M["green"], parent=A)
t = text_obj("A_sign_t", "KAFE", 0.36, (0, -0.15, 2.78), M["gold"], 0.01); t.rotation_euler = (R(90), 0, 0); t.parent = A
box("B_sign", (8.0, 0.14, 0.42), (-2.0, -0.07, 2.78), M["navy"], parent=B)
t = text_obj("B_sign_t", "KAFE - NONVOYXONA", 0.3, (-2.0, -0.15, 2.78), M["gold"], 0.01); t.rotation_euler = (R(90), 0, 0); t.parent = B

# ======================================================================
# 3) KO'CHA
# ======================================================================
street = empty("street")
box("road", (140, 8.0, 0.1), (0, -7.5, -0.05), M["asphalt"], parent=street)
box("walkA", (140, 3.5, 0.14), (0, -1.75, 0.07), M["pave"], parent=street)
box("walkB", (140, 3.5, 0.14), (0, -13.25, 0.07), M["pave"], parent=street)
for y in (-3.55, -11.45):
    box("curb", (140, 0.12, 0.16), (0, y, 0.07), M["curb"], parent=street)
for i in range(-20, 21):
    box("dash", (1.8, 0.12, 0.004), (i * 3.6, -7.5, 0.002), M["line"], parent=street)
box("far_ground", (400, 400, 0.1), (0, 0, -0.12), M["asphalt"], parent=street)
# ko'cha jihozlari
for x in (-14.0, 12.0, 26.0):
    ph_model("street_lamp_01", (x, -3.15, 0.14), (0, 0, 90), parent=street)
for x in (-8.0, 16.0):
    ph_model("street_lamp_01", (x, -11.85, 0.14), (0, 0, -90), parent=street)
ph_model("fire_hydrant", (-6.2, -3.0, 0.14), (0, 0, 0), parent=street)
for x in (-4.2, 4.2):
    ph_model("planter_box_01", (x, -0.45, 0.14), (0, 0, 0), parent=street)
for x in (-5.4, 5.4, -10.5, 13.0):
    ph_model("potted_plant_01", (x, -0.45, 0.14), (0, 0, random.uniform(0, 180)), 0.9, parent=street)
# B kafe stollari (shifokor x=5.0 dagisida)
TABLES = [(-4.5, -12.7), (-1.5, -12.7), (5.0, -12.7), (8.0, -12.7)]
for tx, ty in TABLES:
    ph_model("outdoor_table_chair_set_01", (tx, ty, 0.14), (0, 0, 0), parent=street)
# kofe chashkasi (shifokor stolida)
CUP_M = mat("cup", (0.95, 0.95, 0.93), 0.25, coat=0.5)
cyl("cup", 0.04, 0.09, (4.85, -12.75, 0.14 + 0.73 + 0.045), CUP_M, parent=street)
cyl("saucer", 0.07, 0.01, (4.85, -12.75, 0.14 + 0.73 + 0.005), CUP_M, parent=street)
# parklangan mashina
CAR = BK + "c3c28d91_u.glb"
car1 = import_gltf(CAR, (-7.5, -10.6, 0.0), (0, 0, 0))

# ======================================================================
# 4) KAFE AYVONI (qizil, egiluvchan: shape key "dip")
# ======================================================================
AW_TOP, AW_BOT, AW_D = 2.5, 2.05, 2.4        # yuqori chet (devorda), old chet balandligi, chuqurlik
AW_X = 4.0
IMPACT = V(0.0, -1.05)
def aw_z(y): return AW_TOP + (AW_BOT - AW_TOP) * (-y / AW_D)
aw_m = bpy.data.materials.new("awning"); aw_m.use_nodes = True
_n = aw_m.node_tree.nodes; _l = aw_m.node_tree.links; _b = _n["Principled BSDF"]
_tc = _n.new("ShaderNodeTexCoord"); _w = _n.new("ShaderNodeTexWave"); _w.wave_type = "BANDS"; _w.bands_direction = "X"
_w.inputs["Scale"].default_value = 1.3; _w.inputs["Distortion"].default_value = 0.0
_l.new(_tc.outputs["Object"], _w.inputs["Vector"])
_cr = _n.new("ShaderNodeValToRGB"); _cr.color_ramp.interpolation = "CONSTANT"
_cr.color_ramp.elements[0].color = (0.55, 0.02, 0.025, 1); _cr.color_ramp.elements[1].position = 0.55; _cr.color_ramp.elements[1].color = (0.62, 0.04, 0.04, 1)
_l.new(_w.outputs["Fac"], _cr.inputs["Fac"]); _l.new(_cr.outputs["Color"], _b.inputs["Base Color"])
_b.inputs["Roughness"].default_value = 0.75; _b.inputs["Sheen Weight"].default_value = 0.4
_nz = _n.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 300; _l.new(_tc.outputs["Object"], _nz.inputs["Vector"])
_bp = _n.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.15; _l.new(_nz.outputs["Fac"], _bp.inputs["Height"]); _l.new(_bp.outputs[0], _b.inputs["Normal"])
bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=40, size=1, location=(0, 0, 0))
awn = bpy.context.object; awn.name = "awning"
for v in awn.data.vertices:
    x = v.co.x * 2 * AW_X; y = -(v.co.y + 0.5) * AW_D
    v.co = Vector((x, y, aw_z(y)))
awn.data.materials.append(aw_m)
for p in awn.data.polygons: p.use_smooth = True
awn.shape_key_add(name="Basis", from_mix=False)
kd = awn.shape_key_add(name="dip", from_mix=False); kd.value = 0.0
for i, v in enumerate(awn.data.vertices):
    d = (Vector((v.co.x, v.co.y)) - IMPACT)
    w = math.exp(-(d.x ** 2) / (2 * 0.9 ** 2) - (d.y ** 2) / (2 * 0.7 ** 2))
    edge = smooth(0.0, 0.35, -v.co.y) * smooth(0.0, 0.35, AW_D + v.co.y)     # devor va old chet mahkam
    kd.data[i].co = v.co + Vector((0, 0, -0.4 * w * edge))
so = awn.modifiers.new("so", "SOLIDIFY"); so.thickness = 0.012
# old osilib turgan qism (valans) + temir qo'llar
val = box("awn_val", (2 * AW_X, 0.02, 0.28), (0, -AW_D - 0.01, AW_BOT - 0.14), aw_m)
for x in (-AW_X + 0.1, AW_X - 0.1):
    rod("awn_arm", (x, 0.0, AW_TOP - 0.9), (x, -AW_D, AW_BOT), 0.022, M["iron"])
cyl("awn_bar", 0.03, 2 * AW_X, (0, -AW_D, AW_BOT), M["iron"], rot=(0, 90, 0))
tv = text_obj("awn_txt", "KAFE", 0.18, (0, -AW_D - 0.03, AW_BOT - 0.14), M["white"], 0.0); tv.rotation_euler = (R(90), 0, 0)
L0 = S["launch"][0]
DIP = [(1, 0.0), (F_HIT, 0.0), (F_HIT + 3, 0.65), (F_HIT + 7, 1.0), (F_LAUNCH, 0.35), (F_LAUNCH + 3, -0.3),
       # launch kadrida (takror) — urilishdan keyingi tebranish
       (L0, 0.35), (L0 + 3, -0.3), (L0 + 7, 0.18), (L0 + 11, -0.08), (L0 + 16, 0.03), (L0 + 21, 0.0)]
for f, v in DIP:
    kd.value = v; kd.keyframe_insert("value", frame=f)
for fc in fcurves(awn.data.shape_keys):
    for k in fc.keyframe_points: k.interpolation = "BEZIER"

# ======================================================================
# 5) BALKON + XONA (6-qavat, x=0)
# ======================================================================
BAL = empty("balcony")
box("bal_slab", (1.9, 0.98, 0.16), (0, -0.49, FLOOR6 - 0.08), M["stone"], parent=BAL)
box("bal_slab_edge", (1.96, 0.06, 0.2), (0, -0.98, FLOOR6 - 0.1), M["stone"], parent=BAL)
for s_ in (-1, 1):
    box("bal_cons", (0.14, 0.7, 0.35), (s_ * 0.8, -0.4, FLOOR6 - 0.32), M["stone"], parent=BAL)
RY = -0.92
box("bal_top", (1.9, 0.05, 0.05), (0, RY, FLOOR6 + 0.95), M["iron"], parent=BAL)
box("bal_bot", (1.9, 0.04, 0.04), (0, RY, FLOOR6 + 0.08), M["iron"], parent=BAL)
for s_ in (-1, 1):
    box("bal_side", (0.04, 0.92, 0.04), (s_ * 0.93, RY / 2, FLOOR6 + 0.95), M["iron"], parent=BAL)
    for j in range(7):
        box("bal_sbar", (0.016, 0.016, 0.88), (s_ * 0.93, -0.1 - j * 0.12, FLOOR6 + 0.5), M["iron"], parent=BAL)
BARS = [x for x in [-0.93 + 0.115 * i for i in range(17)] if abs(x) > 0.1] + [-0.1, 0.1]
for x in BARS:
    box("bal_bar", (0.016, 0.016, 0.88), (x, RY, FLOOR6 + 0.51), M["iron"], parent=BAL)
# eshik o'yig'i (fasadda) — balkon eshigi ichkariga ochiq
DOOR_W, DOOR_H = 1.3, 2.4
cutd = box("cut_door", (DOOR_W, 0.8, DOOR_H), (0, 0.2, FLOOR6 + DOOR_H / 2), None)
wallA = bpy.data.objects["A_wall"]
bmd = wallA.modifiers.new("door", "BOOLEAN"); bmd.operation = "DIFFERENCE"; bmd.object = cutd; bool_solver(bmd)
bpy.context.view_layer.objects.active = wallA; bpy.ops.object.modifier_apply(modifier="door"); bpy.data.objects.remove(cutd)
for s_ in (-1, 1):
    hin = empty("door_h", (s_ * DOOR_W / 2, 0.45, FLOOR6), BAL); hin.rotation_euler = (0, 0, R(s_ * 75))
    dp = box("door_leaf", (DOOR_W / 2 - 0.02, 0.05, DOOR_H - 0.05), (-s_ * (DOOR_W / 4), 0, DOOR_H / 2), M["white"], parent=hin)
    box("door_glass", (DOOR_W / 2 - 0.16, 0.06, DOOR_H - 0.4), (-s_ * (DOOR_W / 4), 0, DOOR_H / 2 + 0.05), M["glass"], parent=hin)
box("door_lint", (DOOR_W + 0.4, 0.14, 0.24), (0, -0.05, FLOOR6 + DOOR_H + 0.14), M["stone"], parent=BAL)
# xona
RM = empty("room")
box("rm_floor", (5.0, 4.4, 0.06), (0, 2.6, FLOOR6 - 0.03), M["floor"], parent=RM)
box("rm_ceil", (5.0, 4.4, 0.06), (0, 2.6, FLOOR6 + 2.83), M["white"], parent=RM)
box("rm_back", (5.0, 0.1, 2.9), (0, 4.8, FLOOR6 + 1.45), M["plaster"], parent=RM)
for s_ in (-1, 1):
    box("rm_side", (0.1, 4.4, 2.9), (s_ * 2.5, 2.6, FLOOR6 + 1.45), M["plaster"], parent=RM)
# beshik (yog'och panjarali), o'yinchoqlar
CRIB = empty("crib", (1.3, 2.4, FLOOR6), RM)
box("crib_base", (1.25, 0.7, 0.08), (0, 0, 0.3), M["wood"], parent=CRIB)
box("crib_mat", (1.18, 0.64, 0.1), (0, 0, 0.38), mat("mattress", (0.85, 0.88, 0.95), 0.9), parent=CRIB)
for s_ in (-1, 1):
    box("crib_rail", (1.3, 0.05, 0.05), (0, s_ * 0.36, 0.95), M["wood"], parent=CRIB)
    box("crib_end", (0.06, 0.76, 1.0), (s_ * 0.64, 0, 0.5), M["wood"], parent=CRIB)
    for i in range(12):
        box("crib_bar", (0.025, 0.025, 0.55), (-0.58 + i * 0.105, s_ * 0.36, 0.67), M["wood"], parent=CRIB)
ph_model("rubber_duck_toy", (-0.5, -0.35, FLOOR6), (0, 0, 30), 0.35, parent=BAL)
TOY = [mat("toy_r", (0.8, 0.1, 0.08), 0.4, coat=0.5), mat("toy_b", (0.1, 0.3, 0.8), 0.4, coat=0.5), mat("toy_y", (0.9, 0.7, 0.05), 0.4, coat=0.5)]
for i, (x, y) in enumerate([(0.55, -0.3), (0.35, -0.15), (-0.7, 1.4), (0.4, 1.9)]):
    box("block", (0.06, 0.06, 0.06), (x, y, FLOOR6 + 0.03), TOY[i % 3], rot=(0, 0, random.uniform(0, 90)))
box("rug", (2.0, 1.4, 0.01), (-0.2, 2.0, FLOOR6 + 0.005), mat("rug", (0.6, 0.45, 0.7), 0.95), parent=RM)
ROOM_R = rng("stand", "squeeze")

# ======================================================================
# 6) GRAFIKA (Zack D.: sariq o'lchov chizig'i, punktir traektoriya, qizil halqa)
# ======================================================================
YEL = emis("yellow", (1.0, 0.82, 0.05), 6.0)
GRN = emis("green", (0.1, 1.0, 0.2), 5.0)
RED = emis("red_ring", (1.0, 0.04, 0.03), 6.0)
OUTL = emis("black_o", (0.0, 0.0, 0.0), 0.0)
GFX_M = empty("gfx_meter")
MX, MY = -1.7, -1.6
cyl("m_line", 0.07, FLOOR6, (MX, MY, FLOOR6 / 2), YEL, parent=GFX_M)
for z in (0.0, FLOOR6):
    cyl("m_tick", 0.07, 1.2, (MX, MY, z + 0.04), YEL, rot=(0, 90, 0), parent=GFX_M)
mt = text_obj("m_txt", "18 m", 2.3, (MX - 2.6, MY - 0.4, 10.5), YEL, 0.12)
mt.parent = GFX_M
TEXT_TARGETS = [mt]

# traektoriya (sakrashdan keyin): z(t) = 2.8 + VZ t - g t^2 / 2
P0 = V(0.0, -1.05, AW_TOP + (AW_BOT - AW_TOP) * (1.05 / AW_D) + 0.1); VB = V(0.12, -3.5, 5.9)
def bounce_pos(b): return P0 + VB * b + V(0, 0, -0.5 * G * b * b)
T_GROUND = (VB.z + math.sqrt(VB.z ** 2 + 2 * G * P0.z)) / G
GFX_A = empty("gfx_arc")
n_d = 26
for i in range(n_d):
    b0 = T_GROUND * i / n_d; b1 = T_GROUND * (i + 0.55) / n_d
    rod("dash", bounce_pos(b0), bounce_pos(b1), 0.045, GRN if i < n_d * 0.45 else YEL, parent=GFX_A)
LAND = bounce_pos(T_GROUND)
bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.06, location=(LAND.x, LAND.y, 0.03))
ring = bpy.context.object; ring.name = "ring"; ring.data.materials.append(RED); ring.parent = GFX_A
for f in range(S["arc"][0], S["arc"][1] + 1, 6):
    key(ring, f, scale=1.0 + 0.12 * math.sin((f - S["arc"][0]) / 6 * math.pi))
vis(GFX_M, rng("meter")); vis(GFX_A, rng("arc"))

# ======================================================================
# 7) CHAQALOQ
# ======================================================================
broot, barm, bbody, bdia, bparts = BB.build(sc, "baby")
BP = empty("baby_pivot")                    # tana markazi (aylanish nuqtasi)
broot.parent = BP; broot.location = (0, 0, -0.4)
BP.rotation_mode = "QUATERNION"

def qe(x=0, y=0, z=0):
    return Euler((R(x), R(y), R(z)), "XYZ").to_quaternion()

# yiqilish vaqti (slow-mo, kesishlarda takrorlanadi): (kadr, tau)
T_HIT = math.sqrt(2 * (FLOOR6 + 0.32 - P0.z) / G)
FALL_K = [(72, 0.0), (110, 0.62), (111, 0.55), (162, 1.32), (163, 1.2), (218, T_HIT - 0.05), (221, T_HIT - 0.09), (F_HIT, T_HIT)]
def piece(knots, f):
    for (f0, v0), (f1, v1) in zip(knots, knots[1:]):
        if f0 <= f <= f1 and f1 > f0: return lerp(v0, v1, (f - f0) / (f1 - f0))
    return knots[-1][1] if f > knots[-1][0] else knots[0][1]
Z_TOP = FLOOR6 + 0.32
def fall_z(t): return Z_TOP - 0.5 * G * t * t
# sakrash vaqti
T_CATCH = (VB.z + math.sqrt(VB.z ** 2 + 2 * G * (P0.z - 1.47))) / G
BOUNCE_K = [(F_LAUNCH, 0.0), (246, 0.08), (247, 0.0), (274, 0.45), (275, 0.36), (330, 0.64), (425, 0.88), (471, T_CATCH - 0.17), (F_CATCH, T_CATCH)]

BABY_POSE = {}
def baby_world(f):
    """bola markazi va burilishi (dunyo), F_CATCH dan oldin"""
    if f <= 36:                                   # o'tirgan -> turadi (panjarani ushlaydi)
        u = smooth(8, 28, f)
        p = V(0, lerp(-0.5, -0.66, u), FLOOR6 + lerp(0.15, 0.40, u)); q = qe(0, 0, 0)
    elif f <= 72:                                 # panjara orasidan o'tadi
        u = smooth(37, 66, f); w = smooth(58, 72, f)
        p = V(0, lerp(-0.66, -1.05, u), FLOOR6 + 0.40 - 0.05 * w); q = qe(lerp(0, 55, w), 0, 0)
    elif f < F_HIT:                               # yiqilish: sekin salto, chalqancha tushadi
        t = piece(FALL_K, f); u = t / T_HIT
        p = V(0.02 * math.sin(t * 3), -1.05, fall_z(t))
        q = qe(lerp(55, 270, smooth(0, 1, u)), 12 * math.sin(t * 2.2), 8 * math.sin(t * 1.3))
    elif f < F_LAUNCH:
        dipv = piece(DIP[:6], f)
        zc = aw_z(-1.05) - 0.4 * dipv + 0.1
        p = V(0, -1.05, zc); q = qe(270, 0, 0)
    else:
        if f <= 246:
            b = piece([(F_LAUNCH, 0.0), (246, 0.08)], f)
        else:
            b = piece(BOUNCE_K[2:], f)
        p = bounce_pos(b)
        q = qe(270 - 260 * (b / T_CATCH), 10 * math.sin(b * 4), 20 * b)
    return p, q

for f in range(1, F_CATCH):
    p, q = baby_world(f); BABY_POSE[f] = (p, q)

# poza (suyaklar) va yuz
def baby_anim():
    for f in range(1, END + 1):
        ex = {}
        if f <= 30:
            w = {"sit": 1 - smooth(8, 28, f), "hold": smooth(8, 28, f)}
        elif f <= 72:
            w = {"hold": 1 - smooth(40, 66, f), "lean": smooth(40, 66, f)}
            if f > 66: w = {"lean": 1 - smooth(66, 80, f), "flail": smooth(66, 80, f)}
        elif f < F_CATCH - 6:
            w = {"flail": 1.0}
            if f < 80: w = {"lean": 1 - smooth(66, 80, f), "flail": smooth(66, 80, f)}
            ph = f * 0.42
            ex = {"upper_arm.L": [("y", 18 * math.sin(ph)), ("x", 10 * math.sin(ph * 0.7))],
                  "upper_arm.R": [("y", -18 * math.sin(ph + 1.3)), ("x", 10 * math.sin(ph * 0.8 + 1))],
                  "forearm.L": [("y", -15 * math.sin(ph * 1.3))], "forearm.R": [("y", 15 * math.sin(ph * 1.2 + 2))],
                  "thigh.L": [("x", 14 * math.sin(ph * 0.9))], "thigh.R": [("x", -14 * math.sin(ph * 0.9 + 0.5))],
                  "shin.L": [("x", 12 * math.sin(ph * 1.1))], "shin.R": [("x", 12 * math.sin(ph * 1.05 + 1))]}
            if F_HIT <= f <= F_LAUNCH + 4:
                ex = {}; w = {"flail": 0.4, "tpose": 0.6}
        else:
            u = smooth(F_CATCH - 6, F_CATCH + 10, f)
            w = {"flail": 1 - u, "cradle": u}
            if 531 <= f <= 600:                     # yig'lash: qo'l-oyoq silkinishi
                ph = f * 0.55; a = 1 - smooth(585, 600, f)
                ex = {"upper_arm.L": [("y", 12 * a * math.sin(ph))], "upper_arm.R": [("y", -12 * a * math.sin(ph + 1))],
                      "thigh.L": [("x", 10 * a * math.sin(ph * 0.8))], "thigh.R": [("x", -10 * a * math.sin(ph * 0.8 + 1))],
                      "head": [("z", 8 * a * math.sin(ph * 0.5))]}
        BB.apply_pose(barm, f, w, ex)
        # yuz
        if f < F_HIT:
            lids = 0.0; mouth = 0.0 if f < 60 else 0.45 * smooth(60, 90, f); tears = 0.0
            if 1 <= f % 70 <= 3 and f < 72: lids = 0.9    # ko'z pirpiratish
        elif f < 515:
            lids = 0.6 if f < F_LAUNCH + 6 else 0.1; mouth = 0.7 if f < F_LAUNCH + 6 else 0.5; tears = 0.0
        elif f < 600:
            sob = 0.5 + 0.5 * math.sin((f - 515) * 0.5)
            lids = 0.62 + 0.15 * sob; mouth = 0.75 + 0.25 * sob; tears = 1.0 if f >= 531 else 0.0
        else:
            mouth = 0.25 * (1 - smooth(600, 625, f)); tears = 0.0
            lids = 0.15 + 0.85 * smooth(620, 650, f)
            if 608 <= f <= 612: lids = 0.85
        BB.face(bparts, f, lids, mouth, tears)
    for fc in fcurves(barm):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"

# ======================================================================
# 8) SHIFOKOR (Brian, havorang kiyim)
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
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo
    return s
def tint_mesh(o, col):
    for i, slot in enumerate(o.material_slots):
        m = slot.material.copy(); slot.link = "OBJECT"; slot.material = m
        N = m.node_tree.nodes; L = m.node_tree.links; b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
        lk = b.inputs["Base Color"].links
        if lk:
            src = lk[0].from_socket
            mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
            L.new(src, mx.inputs[6]); mx.inputs[7].default_value = (*col, 1); L.new(mx.outputs[2], b.inputs["Base Color"])

droot, doc, dmeshes = mc.load_character("doc", "Brian.fbx"); sc.render.fps = 24
soften(dmeshes, 0.5)
tint_mesh(next(o for o in dmeshes if o.name.endswith("Shirt")), (0.55, 0.78, 1.0))
SD = A_("Sitting_Drinking.fbx", inplace=False)
SCARED = A_("Scared.fbx", inplace=False)
RUN = A_("Fast_Run.fbx")
CATCH = A_("Goalkeeper_Catch_4.fbx")
CARRY = A_("Carrying.fbx")
# vaqtlar
F_SCARED = 384; SCARED_SPD = 1.45
F_RUN0 = 426; F_RUN1 = F_CATCH - 12
F_CATCH_ANIM = F_CATCH - 12            # Goalkeeper_Catch_4: qo'llar eng yuqorida ~10-kadrda
F_CARRY = F_CATCH + 14
strip(doc, SD, 250, src=(150, 360), bo=0)
strip(doc, SCARED, F_SCARED, speed=SCARED_SPD, src=(1, 77), bi=2)
RUN_SPD = 0.76
strip(doc, RUN, F_RUN0, speed=RUN_SPD, repeat=(F_RUN1 - F_RUN0 + 4) / ((RUN.frame_range[1] - RUN.frame_range[0]) * 0.8 / RUN_SPD))
strip(doc, CATCH, F_CATCH_ANIM, src=(1, 36), bi=3)
strip(doc, CARRY, F_CARRY, repeat=2.0, bi=5)
# joylashuv: o'rindiq (stul_01, stol x=5.0) — o'tirgandagi son nuqtasi
HIP_SEAT = V(5.03, -13.33, 0.14 + 0.5)
SEAT_SD = HIP_SEAT - V(-0.33, -2.8, 0.5)                     # Sitting_Drinking (rot 0)
SEAT_SC = HIP_SEAT - V(0.0, 0.03, 0.55)                      # Scared (rot 180)
STAND = SEAT_SC + V(0, 0.33, 0)                              # turgandan keyin (Scared hips -Y 0.32 -> dunyo +Y)
D_POS = V(0.13, -6.29, 0.0)                                  # ushlash joyi
RK = []
def rkey(f, loc, rot, mode="LINEAR"):
    droot.location = loc; droot.rotation_euler = (0, 0, R(rot))
    droot.keyframe_insert("location", frame=f); droot.keyframe_insert("rotation_euler", frame=f); RK.append((f, mode))
run_dir = (D_POS - STAND); run_dir.z = 0
HEAD = math.degrees(math.atan2(run_dir.x, -run_dir.y)) % 360
rkey(1, tuple(SEAT_SD), 0, "CONSTANT")
rkey(F_SCARED, tuple(SEAT_SC), 180, "CONSTANT")
rkey(F_RUN0, tuple(V(STAND.x, STAND.y, 0.14)), 180)
rkey(F_RUN0 + 4, tuple(STAND.lerp(D_POS, 0.08) + V(0, 0, 0.14)), HEAD)
yc = -11.45
for k in range(1, 8):
    u = 0.08 + 0.92 * k / 7
    pp = STAND.lerp(D_POS, u); pz = 0.14 if pp.y < yc - 0.1 else 0.0
    rkey(int(round(lerp(F_RUN0 + 4, F_RUN1, k / 7))), (pp.x, pp.y, pz), HEAD if k < 7 else 180)
# tebratish (sleep kadri)
for f in range(F_CARRY, END + 1, 9):
    a = 0 if f < 560 else 7.0 * smooth(560, 600, f)
    rkey(f, tuple(D_POS), 180 + a * math.sin((f - 560) / 36 * 2 * math.pi))
for fc in fcurves(droot):
    for k in fc.keyframe_points:
        k.interpolation = "CONSTANT" if dict(RK).get(int(round(k.co.x))) == "CONSTANT" else "BEZIER"
# bolani ushlab turuvchi nuqta: ikki kaft o'rtasi, burilish — shifokor ildizidan
HOLD = empty("holder", (0, 0, 0), droot)
c1 = HOLD.constraints.new("COPY_LOCATION"); c1.target = doc; c1.subtarget = "mixamorig:LeftHand"
c2 = HOLD.constraints.new("COPY_LOCATION"); c2.target = doc; c2.subtarget = "mixamorig:RightHand"; c2.influence = 0.5
CRADLE = empty("cradle", (-0.02, 0.06, 0.08), HOLD)
CRADLE.rotation_mode = "QUATERNION"
CRADLE.rotation_quaternion = Matrix(((0, 0, 1), (-1, 0, 0), (0, -1, 0))).to_quaternion()
# bosh bolaga qaraydi
hb_t = empty("baby_head_t")
_ct = hb_t.constraints.new("CHILD_OF"); _ct.target = barm; _ct.subtarget = "head"; _ct.inverse_matrix = Matrix.Identity(4)
hd = doc.pose.bones["mixamorig:Head"].constraints.new("DAMPED_TRACK"); hd.target = hb_t; hd.track_axis = "TRACK_Z"
for f, v in ((1, 0.0), (F_CARRY + 10, 0.0), (F_CARRY + 25, 0.55), (END, 0.55)):
    hd.influence = v; hd.keyframe_insert("influence", frame=f)

# bola: F_CATCH dan keyin beshikka (CHILD_OF) o'tadi; oxirgi kadrlar silliq qo'shiladi
cof = BP.constraints.new("CHILD_OF"); cof.target = CRADLE; cof.inverse_matrix = Matrix.Identity(4)
cof.influence = 0.0; cof.keyframe_insert("influence", frame=1)
cof.influence = 1.0; cof.keyframe_insert("influence", frame=F_CATCH)
for fc in fcurves(BP):
    pass
CR_W = {}
for f in range(F_CATCH - 8, F_CATCH + 1):
    sc.frame_set(f); CR_W[f] = CRADLE.matrix_world.copy()
for f in range(1, F_CATCH):
    p, q = BABY_POSE[f]
    if f >= F_CATCH - 8:
        w = smooth(F_CATCH - 8, F_CATCH, f)
        mw = CR_W[f]; p = p.lerp(mw.to_translation(), w); q = q.slerp(mw.to_quaternion(), w)
    BP.location = p; BP.rotation_quaternion = q
    BP.keyframe_insert("location", frame=f); BP.keyframe_insert("rotation_quaternion", frame=f)
BP.location = (0, 0, 0); BP.rotation_quaternion = (1, 0, 0, 0)
BP.keyframe_insert("location", frame=F_CATCH); BP.keyframe_insert("rotation_quaternion", frame=F_CATCH)
for fc in fcurves(BP):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
for fc in fcurves(BP):
    if fc.data_path.startswith("constraints"):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
baby_anim()

# ======================================================================
# 9) OTA-ONA (James, Jody) va POLITSIYA (Swat x2) + mashina
# ======================================================================
jroot, jam, jmeshes = mc.load_character("dad", "James.fbx"); sc.render.fps = 24
wroot, jod, wmeshes = mc.load_character("mom", "Jody.fbx"); sc.render.fps = 24
p1root, pol1, p1meshes = mc.load_character("pol1", "Swat.fbx"); sc.render.fps = 24
p2root, pol2, p2meshes = mc.load_character("pol2", "Swat.fbx"); sc.render.fps = 24
for ms_ in (jmeshes, wmeshes, p1meshes, p2meshes): soften(ms_, 0.55)
WALKM = A_("Catwalk_Walk_Forward_01.fbx"); WALKF = A_("Female_Walk.fbx")
SAD = A_("Sad_Idle.fbx"); REACT = A_("Reacting.fbx"); POINT = A_("Angry_Point.fbx"); SHAKE = A_("Annoyed_Head_Shake.fbx")
LOOK = A_("Look_Around.fbx"); WALKP = A_("Catwalk_Walk_Forward_02.fbx")
PA0, PA1 = S["parents"]; AR0, AR1 = S["arrest"]
def span(act, n, src=None, speed=1.0):
    a, b = src or act.frame_range
    return n / ((b - a) * 0.8 / speed)
strip(jam, WALKM, PA0 - 20, repeat=span(WALKM, PA1 - PA0 + 21))
strip(jod, WALKF, PA0 - 20, repeat=span(WALKF, PA1 - PA0 + 21))
strip(jam, SAD, AR0, repeat=span(SAD, AR1 - AR0 + 2))
strip(jod, SAD, AR0, repeat=span(SAD, AR1 - AR0 + 2))
strip(pol1, SAD, AR0 - 2, repeat=span(SAD, AR1 - AR0 + 4))
strip(jam, SHAKE, AR0 + 4, repeat=span(SHAKE, 52), bi=4, bo=8)
strip(jod, REACT, AR0, repeat=span(REACT, 62), bo=8)
strip(pol1, POINT, AR0 + 6, repeat=span(POINT, 62), bi=4, bo=8)
strip(pol2, WALKP, AR0 - 30, repeat=span(WALKP, 50))
strip(pol2, LOOK, AR0 + 20, repeat=span(LOOK, AR1 - AR0), bi=8)
WSPD = 0.049
def walk(root, f0, f1, p0, rot, zf=0.14):
    d = V(math.sin(R(rot)), -math.cos(R(rot)), 0)
    root.location = (p0.x, p0.y, zf); root.rotation_euler = (0, 0, R(rot))
    root.keyframe_insert("location", frame=f0); root.keyframe_insert("rotation_euler", frame=f0)
    p1 = p0 + d * WSPD * (f1 - f0)
    root.location = (p1.x, p1.y, zf); root.keyframe_insert("location", frame=f1)
    for fc in fcurves(root):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
    return p1
walk(jroot, PA0 - 20, PA1, V(15.2, -2.0, 0), -90)
walk(wroot, PA0 - 20, PA1, V(15.4, -1.25, 0), -90)
def place(root, f, p, rot, zf=0.14):
    root.location = (p[0], p[1], zf); root.rotation_euler = (0, 0, R(rot))
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
    for fc in fcurves(root):
        for k in fc.keyframe_points:
            if int(round(k.co.x)) == f: k.interpolation = "CONSTANT"
place(jroot, AR0, (8.55, -1.75), 0); place(wroot, AR0, (9.45, -1.6), 10)
place(p1root, 1, (7.6, -2.55), 131)
p2s = walk(p2root, AR0 - 30, AR0 + 20, V(12.2, -3.84, 0), 231, 0.14)
root_p2 = p2root
# xarid sumkalari (kaftga COPY_LOCATION)
BAG_M = [mat("bag1", (0.85, 0.3, 0.45), 0.6), mat("bag2", (0.95, 0.75, 0.2), 0.6), mat("bag3", (0.2, 0.55, 0.75), 0.6)]
def bag(name, arm, bone, root, m, size=(0.32, 0.12, 0.36)):
    e = child_of_bone(name + "_e", arm, bone)
    g = empty(name + "_g")
    cl = g.constraints.new("COPY_LOCATION"); cl.target = e
    cr = g.constraints.new("COPY_ROTATION"); cr.target = root; cr.use_x = cr.use_y = False
    b = box(name, size, (0, 0, -0.06 - size[2] / 2), m, parent=g, bevel=0.005)
    for s_ in (-1, 1):
        cyl(name + "_h", 0.006, 0.12, (s_ * 0.06, 0, -0.03), M["dark"], rot=(0, s_ * 25, 0), parent=g)
    return g
bags = [bag("bagA", jam, "RightHand", jroot, BAG_M[0]), bag("bagB", jod, "LeftHand", wroot, BAG_M[1]),
        bag("bagC", jod, "RightHand", wroot, BAG_M[2], (0.26, 0.1, 0.3))]
# politsiya mashinasi (qora Audi + chiroqlar)
CARX = 13.6
car2 = import_gltf(CAR, (CARX, -4.75, 0.0), (0, 0, 180))
LB = empty("lightbar", (CARX, -4.75, 1.42))
box("lb_base", (0.25, 1.1, 0.07), (0, 0, 0), M["dark"], parent=LB)
LB_R = emis("lb_red", (1.0, 0.03, 0.02), 0.0); LB_B = emis("lb_blue", (0.05, 0.2, 1.0), 0.0)
box("lb_r", (0.2, 0.48, 0.09), (0, 0.27, 0.06), LB_R, parent=LB)
box("lb_b", (0.2, 0.48, 0.09), (0, -0.27, 0.06), LB_B, parent=LB)
ptR = point("pol_red", (CARX - 1.6, -4.0, 1.8), 0.2, (1.0, 0.05, 0.03), [])
ptB = point("pol_blue", (CARX - 1.0, -4.6, 1.8), 0.2, (0.1, 0.25, 1.0), [])
LIT0 = S["arrest"][0]
for node_m, lt in ((LB_R, ptR), (LB_B, ptB)):
    em = node_m.node_tree.nodes["Emission"]; em.inputs["Strength"].default_value = 0.0
    em.inputs["Strength"].keyframe_insert("default_value", frame=1); lt.data.energy = 0.0; lt.data.keyframe_insert("energy", frame=1)
for f in range(LIT0, END + 1, 4):
    on = (f // 4) % 2 == 0
    for node_m, lt, cond in ((LB_R, ptR, on), (LB_B, ptB, not on)):
        em = node_m.node_tree.nodes["Emission"]; em.inputs["Strength"].default_value = 14.0 if cond else 0.6
        em.inputs["Strength"].keyframe_insert("default_value", frame=f)
        lt.data.energy = 2500.0 if cond else 0.0; lt.data.keyframe_insert("energy", frame=f)
for idb in (LB_R.node_tree, LB_B.node_tree, ptR.data, ptB.data): interp(idb, "CONSTANT")

# ======================================================================
# 10) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop=None, clip=0.02):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
def follow(name, obj, off=(0, 0, 0)):
    e = empty(name); cl = e.constraints.new("COPY_LOCATION"); cl.target = obj
    o = empty(name + "_o", off, e); return o
s0, s1 = S["stand"]
abs_cam("stand", [(s0, V(0.42, 0.25, FLOOR6 + 2.0)), (s1, V(0.3, 0.0, FLOOR6 + 1.75))],
        [(s0, V(-0.05, -2.6, FLOOR6 - 4.0)), (s1, V(-0.05, -2.8, FLOOR6 - 4.4))], 15, 6.0)
CAMS["stand"].data.dof.focus_object = None; CAMS["stand"].data.dof.focus_distance = 2.0
s0, s1 = S["squeeze"]
bhead = empty("bhead_t"); _c = bhead.constraints.new("CHILD_OF"); _c.target = barm; _c.subtarget = "head"; _c.inverse_matrix = Matrix.Identity(4)
bhead_o = empty("bhead_o", (0, 0.07, 0.0), bhead)
c = shot_cam("squeeze", (0.6, -2.2, FLOOR6 - 0.05), bhead_o, 35, 2.8)
path_keys(c, [(s0, V(0.8, -2.7, FLOOR6 + 0.25)), (s1, V(0.4, -2.25, FLOOR6 + 0.4))])
s0, s1 = S["fall"]
bfol = follow("bfol", BP)
c = shot_cam("fall", (0.7, -2.9, 13.2), bfol, 18, 4.0)
path_keys(c, [(s0, V(0.8, -3.0, 13.4)), (s1, V(0.6, -2.6, 13.0))])
s0, s1 = S["meter"]
abs_cam("meter", [(s0, V(9.5, -12.5, 6.5)), (s1, V(8.6, -11.8, 6.0))], [(s0, V(-0.8, -1.2, 9.6)), (s1, V(-0.8, -1.2, 9.0))], 15)
for tt in TEXT_TARGETS:
    tr = tt.constraints.new("TRACK_TO"); tr.target = CAMS["meter"]; tr.track_axis = "TRACK_Z"; tr.up_axis = "UP_Y"
s0, s1 = S["awning"]
abs_cam("awning", [(s0, V(2.2, -6.0, 0.8)), (s1, V(1.7, -5.2, 0.9))], [(s0, V(0.0, -1.1, 9.5)), (s0 + 30, V(0.0, -1.1, 6.0)), (s1, V(0.0, -1.2, 3.3))], 24, 8.0)
s0, s1 = S["hit"]
c = abs_cam("hit", [(s0, V(1.9, -3.0, 4.4)), (s1, V(1.6, -2.7, 4.1))], [(s0, V(0.0, -1.05, 2.9)), (s1, V(0.0, -1.1, 2.8))], 26, 4.0)
shake(c, F_HIT + 2, F_HIT + 12, 0.06, seed=3)
s0, s1 = S["launch"]
blo = follow("blo", BP, (0, 0, -0.2))
c = shot_cam("launch", (1.1, -4.6, 1.0), blo, 20, 5.6)
path_keys(c, [(s0, V(1.2, -4.8, 0.95)), (s1, V(0.9, -4.3, 1.1))])
s0, s1 = S["arc"]
abs_cam("arc", [(s0, V(3.1, -6.3, 2.9)), (s1, V(2.7, -5.8, 3.1))], [(s0, V(0.05, -3.0, 3.2)), (s1, V(0.05, -3.4, 3.1))], 17)
s0, s1 = S["doctor"]
dhead = child_of_bone("dhead", doc, "Head")
abs_cam("doctor", [(s0, V(2.6, -9.7, 1.25)), (s1, V(3.1, -10.4, 1.15))], [(s0, V(5.0, -13.2, 0.95)), (s1, V(5.0, -13.2, 0.95))], 26, 4.0)
s0, s1 = S["face"]
dface = empty("dface_o", (0, 0.06, 0.08), dhead)
c = shot_cam("face", (4.75, -12.05, 1.0), dface, 50, 2.0)
path_keys(c, [(s0, V(4.8, -12.15, 0.98)), (S["face"][0] + 16, V(4.78, -12.05, 1.02)), (s1, V(4.7, -11.6, 1.5))])
s0, s1 = S["run"]
dhip = child_of_bone("dhip", doc, "Hips")
dhip_o = empty("dhip_o", (0, 0.35, 0), dhip)
c = shot_cam("run", (0, 0, 0), dhip_o, 18, 5.6)
rp0 = STAND.lerp(D_POS, 0.05); rp1 = STAND.lerp(D_POS, 0.95)
side = V(run_dir.y, -run_dir.x, 0).normalized()
path_keys(c, [(s0, rp0 + side * 2.6 + V(0, 0, 0.45)), (s1, rp1 + side * 2.8 + V(0, 0, 0.55))])
s0, s1 = S["catch"]
c = abs_cam("catch", [(s0, V(1.5, -4.1, 1.15)), (s1, V(1.05, -4.55, 1.3))], [(s0, V(0.1, -6.1, 1.55)), (s1, V(0.1, -6.15, 1.2))], 26, 4.0)
shake(c, F_CATCH, F_CATCH + 9, 0.035, seed=9)
s0, s1 = S["cry"]
bface = empty("bface_o", (0, 0.045, 0.065), bhead)
crc = follow("cry_rig", bface)
c = shot_cam("cry", (0, 0, 0), bface, 42, 2.4, clip=0.01)
c.parent = crc
path_keys(c, [(s0, V(0.17, 0.1, 0.46)), (s1, V(0.13, 0.08, 0.4))])
s0, s1 = S["sleep"]
dpos = V(D_POS.x, D_POS.y, 0)
pts = []
for i in range(5):
    a = R(lerp(-35, 25, i / 4)); r_ = lerp(1.9, 1.3, i / 4)
    pts.append((int(lerp(s0, s1, i / 4)), dpos + V(r_ * math.sin(a), r_ * math.cos(a), lerp(1.55, 1.45, i / 4))))
bmid = empty("bmid_o", (0, 0, 0), CRADLE)
c = shot_cam("sleep", (0, 0, 0), bmid, 35, 2.8)
path_keys(c, pts)
s0, s1 = S["parents"]
pmid = empty("pmid")
_c1 = pmid.constraints.new("COPY_LOCATION"); _c1.target = jroot
_c2 = pmid.constraints.new("COPY_LOCATION"); _c2.target = wroot; _c2.influence = 0.5
pmid_o = empty("pmid_o", (0, 0, 1.0), pmid)
c = shot_cam("parents", (0, 0, 0), pmid_o, 24, 4.0)
pp0 = V(15.2 - WSPD * (s0 - PA0 + 20), -1.6, 0); pp1 = V(15.2 - WSPD * (s1 - PA0 + 20), -1.6, 0)
path_keys(c, [(s0, pp0 + V(-3.2, -1.3, 0.55)), (s1, pp1 + V(-2.7, -1.5, 0.65))])
s0, s1 = S["arrest"]
abs_cam("arrest", [(s0, V(8.4, -7.6, 1.25)), (s0 + 50, V(8.7, -6.9, 1.3)), (s1, V(8.9, -6.2, 1.35))],
        [(s0, V(8.95, -2.1, 1.1)), (s1, V(8.95, -1.9, 1.25))], 20, 4.0)
lens_keys(CAMS["arrest"], [(s0, 20), (s0 + 40, 22), (s1, 30)])
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["stand"]

# ======================================================================
# 11) KO'RINISH (faqat kerakli kadrlarda)
# ======================================================================
BABY_R = rng("stand", "squeeze", "fall", "meter", "awning", "hit", "launch", "arc", "run", "catch", "cry", "sleep")
for o in [bbody, bdia] + [o for o in barm.children_recursive if o.type == "MESH" and "tear" not in o.name]:
    vis(o, BABY_R, recursive=False)
DOC_R = rng("doctor", "face", "run", "catch", "cry", "sleep")
for o in dmeshes: vis(o, DOC_R, recursive=False)
PAR_R = rng("parents", "arrest")
for o in jmeshes + wmeshes: vis(o, PAR_R, recursive=False)
for g in bags: vis(g, PAR_R)
POL_R = rng("arrest")
for o in p1meshes + p2meshes: vis(o, POL_R, recursive=False)
vis(car2, POL_R); vis(LB, POL_R)
vis(RM, ROOM_R); vis(CRIB, ROOM_R)

# ======================================================================
# 12) YORUG'LIK va DUNYO
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
bg = N["Background"]
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0]); L.new(env.outputs[0], bg.inputs[0])
bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(31.8), 0, R(49.4)); sun.data.angle = R(1.2); sun.data.energy = 4.2
sun.data.color = (1.0, 0.95, 0.88)
# xona ichi
RT = empty("roomT", (0, 1.0, FLOOR6 + 0.6))
area("R_ceil", (0.6, 2.0, FLOOR6 + 2.7), 1.5, (1.0, 0.88, 0.72), lights_for(ROOM_R, 180.0), target=RT)
# B kafe (soyada) — shifokorga yumshoq yorug'lik
DT = empty("docT", (5.0, -13.0, 1.1))
area("D_fill", (4.0, -10.0, 3.0), 2.0, (1.0, 0.95, 0.9), lights_for(rng("doctor", "face"), 260.0), target=DT)
CT = empty("catchT", tuple(D_POS + V(0, 0.1, 1.3)))
area("C_fill", tuple(D_POS + V(1.2, 3.0, 2.6)), 2.5, (1.0, 0.95, 0.88), lights_for(rng("catch", "cry", "sleep"), 380.0), target=CT)

# ======================================================================
# 13) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 12; sc.cycles.transmission_bounces = 4
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
