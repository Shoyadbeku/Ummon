# "5 soniya qoidasi" — Zack D. Films uslubida 41.7 s video (1000 kadr, 24 fps, 9:16).
# Ovoz (Whisper): polga tushgan ovqat, "5 soniya o'tmadi" yolg'oni, bakteriyalar nam ovqatga bir zumda yopishadi.
# Asos: zack_test/scene3.py + mixchar.py, kamera/yorug'lik yordamchilari zack_test/ishqalash/ishqalash.py dan.
# Assetlar: zack_test/tools/get_besh_soniya.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/besh_soniya/besh_soniya.py --render
# Sinov:  FRAMES=30,100,250,420,700 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT)
from mathutils import Vector, Matrix, noise
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
PH4 = os.environ.get("PH4_DIR", "/tmp/claude-0/assets/ph4k/")
random.seed(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24
END = 1000
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (so'z vaqtlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (72, "pick"), (127, "eat"), (188, "lie"), (232, "legs"), (287, "land"), (377, "stick"),
         (441, "wet"), (489, "three"), (591, "magnet"), (654, "uv"), (728, "gut"), (792, "timer"), (865, "time"),
         (910, "moist"), (945, "dirty")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
KITN = ("hook", "pick", "eat", "lie", "land", "wet", "three", "uv", "timer", "time", "moist", "dirty")
MICN = ("legs", "stick", "magnet", "gut")
KIT = rng(*KITN); MIC = rng(*MICN)
F_LAND0 = 54        # "tushib ketganida" — bo'lak polga tegadi
F_GRAB = 101        # Megan bo'lakni oladi
F_LAND = 312        # "tushgan" — ho'l bo'lak polga tegadi (makro)
F_STICK = 420       # "yopishib" — ovqat bakteriyalarga tegadi
F_MEVA, F_GOSHT, F_SOS = 515, 529, 545     # "meva", "go'sht", "sous"
F_SPLAT = 560       # "polga tushgan zahoti"
F_EMAS = 845        # "emas" — qizil chaqnash
TIMER0 = 796

# ---------------- yordamchilar ----------------
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

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

def math_n(N, L, op, a, b=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L.new(v, n.inputs[i])
    return n.outputs[0]

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, emit_col=None, coat_r=0.03):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = coat_r
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    return m

def obj_attr(m, name):
    a = m.node_tree.nodes.new("ShaderNodeAttribute"); a.attribute_type = "OBJECT"; a.attribute_name = name
    return a.outputs["Fac"]

def pbr(name, folder, scale=1.0, tint=None, proj="BOX", root=None):
    root = root or PH
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(root, folder, fn))
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

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3; smooth(o)
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m); smooth(o)
    o.location = loc
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

def apply_mods(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    o.modifiers.clear(); old = o.data; o.data = me
    if old.users == 0: bpy.data.meshes.remove(old)

def capsule_mesh(name, r, length, segs=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=segs // 2 + 2, radius=r, location=(0, 0, 0))
    o = bpy.context.object; me = o.data; me.name = name
    for v in me.vertices:
        v.co.x += (length / 2 - r) * (1 if v.co.x > 1e-6 else -1 if v.co.x < -1e-6 else 0)
    for p in me.polygons: p.use_smooth = True
    bpy.data.objects.remove(o); return me

def prop_key(o, prop, f, v):
    o[prop] = float(v); o.keyframe_insert(f'["{prop}"]', frame=f)

def V(*a): return Vector(a)
def ease(t): return t * t * (3 - 2 * t)

# ======================================================================
# 1) OSHXONA (kunduzi): laminat pol, stol, shkaflar, deraza
# ======================================================================
kit_objs = []
def K_(o): kit_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 1.0, root=PH4)
# changli/yog'li dog'lar (realizm uchun)
_N = floor_m.node_tree.nodes; _L = floor_m.node_tree.links; _b = _N["Principled BSDF"]
X0, X1, Y0, Y1, HZ_ = -2.6, 2.6, -2.6, 2.6, 2.7
K_(plane("floor", (X1 - X0, Y1 - Y0), (0, 0, 0), floor_m))
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.95, 0.92, 0.86))
K_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), (0, 0, HZ_ + 0.025), mat("ceil_m", (0.92, 0.92, 0.9), 0.8)))
K_(box("wall_L", (0.1, Y1 - Y0, HZ_), (X0 - 0.05, 0, HZ_ / 2), wall_m))
K_(box("wall_B", (X1 - X0, 0.1, HZ_), (0, Y1 + 0.05, HZ_ / 2), wall_m))
K_(box("wall_F", (X1 - X0, 0.1, HZ_), (0, Y0 - 0.05, HZ_ / 2), wall_m))
# o'ng devor derazali: y [-0.7, 1.3], z [0.9, 2.2]
WY0, WY1, WZ0, WZ1 = -0.7, 1.3, 0.9, 2.2
K_(box("wall_R1", (0.1, WY0 - Y0, HZ_), (X1 + 0.05, (Y0 + WY0) / 2, HZ_ / 2), wall_m))
K_(box("wall_R2", (0.1, Y1 - WY1, HZ_), (X1 + 0.05, (WY1 + Y1) / 2, HZ_ / 2), wall_m))
K_(box("wall_R3", (0.1, WY1 - WY0, WZ0), (X1 + 0.05, (WY0 + WY1) / 2, WZ0 / 2), wall_m))
K_(box("wall_R4", (0.1, WY1 - WY0, HZ_ - WZ1), (X1 + 0.05, (WY0 + WY1) / 2, (WZ1 + HZ_) / 2), wall_m))
frame_m = mat("win_frame", (0.93, 0.93, 0.9), 0.4)
WCy, WCz = (WY0 + WY1) / 2, (WZ0 + WZ1) / 2
for nm, sz, off in (("wf_t", (0.12, WY1 - WY0 + 0.04, 0.05), (0, 0, (WZ1 - WZ0) / 2)), ("wf_b", (0.22, WY1 - WY0 + 0.04, 0.05), (-0.05, 0, -(WZ1 - WZ0) / 2)),
                    ("wf_l", (0.12, 0.05, WZ1 - WZ0), (0, -(WY1 - WY0) / 2, 0)), ("wf_r", (0.12, 0.05, WZ1 - WZ0), (0, (WY1 - WY0) / 2, 0)),
                    ("wf_m", (0.08, 0.04, WZ1 - WZ0), (0, 0, 0))):
    K_(box(nm, sz, (X1 + 0.05 + off[0], WCy + off[1], WCz + off[2]), frame_m))
for nm, sz, loc in (("base_B", (X1 - X0, 0.03, 0.1), (0, Y1 - 0.015, 0.05)), ("base_F", (X1 - X0, 0.03, 0.1), (0, Y0 + 0.015, 0.05)),
                    ("base_L", (0.03, Y1 - Y0, 0.1), (X0 + 0.015, 0, 0.05))):
    K_(box(nm, sz, loc, frame_m))
# tashqarida: maysa va daraxtlar (derazadan)
K_(plane("out_ground", (30, 30), (X1 + 15, 0, -0.4), mat("out_grass", (0.1, 0.22, 0.06), 0.9)))
leaf_m = mat("out_leaf", (0.08, 0.2, 0.05), 0.7, sss=0.1)
for i, (dy, dx, s) in enumerate(((-2.5, 6, 2.2), (1.5, 8, 3.0), (4.5, 5.5, 1.8))):
    K_(sphere(f"tree{i}", s, (X1 + dx, dy, s + 0.6), leaf_m, scale=(1, 1, 1.2), sub=3))
# mebel
K_(import_gltf(PH + "dining_table/dining_table.gltf", (-1.55, -0.1, 0), 90, (0.85, 0.85, 0.86)))
TABLE_TOP = 0.873 * 0.86
for i, (x, y, rz) in enumerate(((-0.95, -0.55, 90), (-0.95, 0.4, 90), (-2.15, -0.3, -90))):
    K_(import_gltf(PH + "dining_chair_02/dining_chair_02.gltf", (x, y, 0), rz, 1.0))
K_(import_gltf(PH + "modern_wooden_cabinet/modern_wooden_cabinet.gltf", (-0.9, Y1 - 0.28, 0), 0, 1.0))
K_(import_gltf(PH + "drawer_cabinet/drawer_cabinet.gltf", (1.55, Y1 - 0.26, 0), 0, 1.0))
K_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (2.1, -2.05, 0), 30, 1.1))
K_(import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (0.55, Y1 - 0.3, 0), 160, 0.9))
K_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-0.9, Y1 - 0.01, 1.45), 0, 1.2))
K_(import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (X0 + 0.01, -0.3, 1.5), -90, 1.0))
K_(import_gltf(PH + "wooden_cutting_board/wooden_cutting_board.gltf", (-1.45, -0.35, TABLE_TOP), 80, 1.0))
K_(import_gltf(PH + "food_apple_01/food_apple_01.gltf", (-1.42, -0.42, TABLE_TOP + 0.041), 0, 1.0))
K_(import_gltf(PH + "food_kiwi_01/food_kiwi_01.gltf", (-1.6, 0.2, TABLE_TOP), 0, 1.0))
K_(import_gltf(PH + "food_kiwi_01/food_kiwi_01.gltf", (-1.66, 0.27, TABLE_TOP), 70, 1.0))
K_(import_gltf(PH + "carved_wooden_plate/carved_wooden_plate.gltf", (-1.35, 0.05, TABLE_TOP), 0, 1.0))
# shiftdagi lampa
lamp_m = mat("ceil_lamp", (1.0, 0.95, 0.85), 0.5, emit=8.0)
K_(cyl("ceil_lamp", 0.25, 0.05, (0, 0.2, HZ_ - 0.03), lamp_m, verts=48))

# ======================================================================
# 2) OVQATLAR: olma bo'lagi (boolean), kolbasa, sous
# ======================================================================
def flesh_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.01
    b.inputs["Subsurface Weight"].default_value = 0.2; b.inputs["Subsurface Scale"].default_value = 0.002
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 700.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90.0; nz.inputs["Detail"].default_value = 5; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; cm.inputs[6].default_value = (0.92, 0.74, 0.36, 1); cm.inputs[7].default_value = (0.8, 0.6, 0.26, 1)
    L.new(nz.outputs["Fac"], cm.inputs["Factor"]); L.new(cm.outputs[2], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.inputs["Distance"].default_value = 0.0004
    L.new(math_n(N, L, "ADD", vo.outputs["Distance"], math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.5)), bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    germ_emit(m, b, tc, 1100.0)
    return m

def germ_emit(m, b, tc, scale):
    """ob'ekt xususiyati 'germ' (0..1) — yashil yonuvchi mikrob nuqtalari"""
    N = m.node_tree.nodes; L = m.node_tree.links
    g = obj_attr(m, "germ")
    v2 = N.new("ShaderNodeTexVoronoi"); v2.inputs["Scale"].default_value = scale; L.new(tc.outputs["Object"], v2.inputs["Vector"])
    cl = N.new("ShaderNodeTexNoise"); cl.inputs["Scale"].default_value = scale / 25; L.new(tc.outputs["Object"], cl.inputs["Vector"])
    dots = math_n(N, L, "LESS_THAN", v2.outputs["Distance"], 0.22)
    clus = math_n(N, L, "GREATER_THAN", cl.outputs["Fac"], 0.47)
    e = math_n(N, L, "MULTIPLY", math_n(N, L, "MULTIPLY", dots, clus), math_n(N, L, "MULTIPLY", g, 6.0))
    b.inputs["Emission Color"].default_value = (0.35, 1.0, 0.15, 1)
    L.new(e, b.inputs["Emission Strength"])

def skin_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.32; b.inputs["Coat Weight"].default_value = 0.5
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (40, 40, 6)
    L.new(tc.outputs["Object"], mp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.0; nz.inputs["Detail"].default_value = 6; L.new(mp.outputs[0], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.42, 0.015, 0.02, 1); cr.color_ramp.elements[1].color = (0.85, 0.28, 0.04, 1)
    cr.color_ramp.elements[0].position = 0.4; cr.color_ramp.elements[1].position = 0.7
    L.new(nz.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"])
    germ_emit(m, b, tc, 900.0)
    return m

FLESH = flesh_mat("apple_flesh"); SKIN = skin_mat("apple_skin")
def apple_slice_mesh():
    Ra, Ha, ang, r0 = 0.04, 0.072, 52.0, 0.009
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(0, 0, 0))
    ap = bpy.context.object; ap.name = "apple_tmp"
    for v in ap.data.vertices:
        x, y, z = v.co
        k = 1.0 - 0.18 * (abs(z) ** 6)                     # tepa/past yassi
        dimple = 0.25 * math.exp(-((x * x + y * y) / 0.04)) if abs(z) > 0.6 else 0
        v.co = Vector((x * Ra * k, y * Ra * k, (z - math.copysign(dimple, z)) * Ha / 2))
    smooth(ap); ap.data.materials.append(SKIN)
    bm = bmesh.new(); h = Ha
    pts = [(r0, 0.0)] + [(0.1 * math.cos(R(a)), 0.1 * math.sin(R(a))) for a in (0, ang / 3, 2 * ang / 3, ang)] + [(r0 * math.cos(R(ang)), r0 * math.sin(R(ang)))]
    vb = [bm.verts.new((x, y, -h)) for x, y in pts]; vt = [bm.verts.new((x, y, h)) for x, y in pts]
    bm.faces.new(vb[::-1]); bm.faces.new(vt)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    me = bpy.data.meshes.new("wedge_cut"); bm.to_mesh(me); bm.free()
    cut = bpy.data.objects.new("wedge_cut", me); sc.collection.objects.link(cut); me.materials.append(FLESH)
    md = ap.modifiers.new("b", "BOOLEAN"); md.operation = "INTERSECT"; md.solver = "EXACT"; md.object = cut
    md.material_mode = "TRANSFER"
    apply_mods(ap)
    bpy.data.objects.remove(cut)
    me = ap.data; me.name = "apple_slice"
    # ob'ekt boshi: kesim yuzi yerda yotganda pastki markaz
    for v in me.vertices: v.co.x -= 0.024
    bpy.data.objects.remove(ap)
    return me
SLICE_ME = apple_slice_mesh()
# kesim yuzi (y=0) pastga: X bo'yicha +90° -> yuz z=0 ga tushadi
def slice_obj(name, loc=(0, 0, 0), rot=(90, 0, 0), parent=None, germ=0.0):
    o = bpy.data.objects.new(name, SLICE_ME); sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]; o.parent = parent
    o["germ"] = float(germ)
    return o

meat_m = bpy.data.materials.new("sausage"); meat_m.use_nodes = True
_N = meat_m.node_tree.nodes; _L = meat_m.node_tree.links; _b = _N["Principled BSDF"]
_tc = _N.new("ShaderNodeTexCoord"); _nz = _N.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 300; _nz.inputs["Detail"].default_value = 6
_L.new(_tc.outputs["Object"], _nz.inputs["Vector"])
_cr = _N.new("ShaderNodeValToRGB"); _cr.color_ramp.elements[0].color = (0.32, 0.07, 0.04, 1); _cr.color_ramp.elements[1].color = (0.55, 0.2, 0.13, 1)
_L.new(_nz.outputs["Fac"], _cr.inputs[0]); _L.new(_cr.outputs[0], _b.inputs["Base Color"])
_b.inputs["Roughness"].default_value = 0.35; _b.inputs["Coat Weight"].default_value = 1.0; _b.inputs["Coat Roughness"].default_value = 0.02
_b.inputs["Subsurface Weight"].default_value = 0.2; _b.inputs["Subsurface Scale"].default_value = 0.002
_bp = _N.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.2; _bp.inputs["Distance"].default_value = 0.0005
_L.new(_nz.outputs["Fac"], _bp.inputs["Height"]); _L.new(_bp.outputs[0], _b.inputs["Normal"])
germ_emit(meat_m, _b, _tc, 900.0)
SAUS_ME = capsule_mesh("sausage", 0.012, 0.075, 32); SAUS_ME.materials.append(meat_m)
def sausage(name, loc, rz=0):
    o = bpy.data.objects.new(name, SAUS_ME); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, R(rz)); o["germ"] = 0.0; return o
ketchup_m = mat("ketchup", (0.42, 0.015, 0.008), 0.12, coat=1.0, sss=0.3, coat_r=0.01)
ketchup_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.002
def sauce(name, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.016, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; smooth(o); o.data.materials.append(ketchup_m)
    d = o.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new(name + "_t", "CLOUDS"); t.noise_scale = 0.012; d.texture = t
    d.strength = 0.0; d.texture_coords = "LOCAL"
    o.location = loc; o["germ"] = 0.0
    return o, d
water_m = mat("water_drop", (0.95, 0.97, 1.0), 0.0, trans=1.0)
juice_m = mat("juice_drop", (0.97, 0.9, 0.62), 0.02, coat=1.0, coat_r=0.0)

def droplets(name, parent, n, rmin, rmax, area, zoff, seed=1, m=None):
    """kesim yuzidagi sharbat tomchilari (yarim sferalar)"""
    rd = random.Random(seed); out = []
    for i in range(n):
        r = rd.uniform(rmin, rmax)
        o = sphere(f"{name}{i}", r, (rd.uniform(*area[0]), rd.uniform(*area[1]), zoff), m or juice_m, scale=(1, 1, 0.45), sub=3, parent=parent)
        out.append(o)
    return out

# ---------------- poldagi joylar (Megan oldida) ----------------
MEG = V(0.0, 0.6, 0.0)
G = MEG + V(0.22, -0.88, 0)              # 1-2: Megan tushirgan bo'lak
G3 = V(-0.3, -0.95, 0)                  # 6, 15: ho'l bo'lak tushishi (makro)
G4 = V(1.05, -0.95, 0)                   # 8: ho'l/yog'li ovqatlar yotibdi
G5 = V(-0.35, -1.55, 0)                  # 9: meva, go'sht, sous navbat bilan tushadi
G6 = V(0.95, 0.05, 0)                    # 13-14: sekundomer + bo'lak

# 1) ilgak: bo'lak Megan qo'lidan sekin harakatda uchib tushadi
sl_fall = slice_obj("slice_fall", germ=0.0)
HAND0 = MEG + V(0.27, -0.12, 0.88)
pts = [(1, HAND0, (60, 20, 30)), (18, HAND0 + V(-0.02, -0.25, -0.18), (75, 80, 90)), (36, HAND0 + V(-0.04, -0.6, -0.55), (95, 160, 160)),
       (F_LAND0, V(G.x, G.y + 0.04, 0.0), (90, 180, 205)), (F_LAND0 + 5, V(G.x, G.y + 0.015, 0.012), (88, 186, 214)),
       (F_LAND0 + 10, V(G.x, G.y, 0.0), (90, 180, 220))]
for f, p, r in pts: key(sl_fall, f, loc=tuple(p), rot=r)
vis(sl_fall, [(1, F_GRAB - 1)])

# qo'ldagi bo'lak (chap kaft)
def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    return e

# 6/15) ho'l bo'lak makro tushishi + sachrash
sl_land = slice_obj("slice_land", germ=0.0)
key(sl_land, S["land"][0], loc=tuple(G3 + V(0.03, 0.05, 0.42)), rot=(40, 30, 10))
key(sl_land, F_LAND - 2, loc=tuple(G3 + V(0.005, 0.01, 0.03)), rot=(84, 8, 38))
key(sl_land, F_LAND, loc=tuple(G3), rot=(90, 0, 40))
key(sl_land, F_LAND + 4, loc=tuple(G3 + V(0, 0, 0.006)), rot=(88, 2, 41))
key(sl_land, F_LAND + 8, loc=tuple(G3), rot=(90, 0, 42))
interp(sl_land, "LINEAR")
land_drops = []
for side in (1, -1):
    for i, (u, v) in enumerate(((0.3, 0.2), (0.6, 0.35), (0.8, 0.15))):
        pass
SL_ANG = 52.0
def face2_drops(name, parent, n, seed):
    rd = random.Random(seed); a = R(SL_ANG); nrm = Vector((-math.sin(a), math.cos(a), 0))
    return
    for i in range(n):
        r_ = rd.uniform(0.014, 0.034); zl = rd.uniform(-0.026, 0.026); rad = rd.uniform(0.0011, 0.0028)
        p = Vector((r_ * math.cos(a) - 0.024, r_ * math.sin(a), zl)) + nrm * rad * 0.25
        sphere(f"{name}{i}", rad, tuple(p), juice_m, sub=3, parent=parent)
juice_ofs = [(-0.012, 0.005, 0.006, 0.0022), (0.0, 0.0, 0.007, 0.0025), (0.011, -0.004, 0.006, 0.002), (0.022, 0.006, 0.005, 0.0018), (-0.004, -0.008, 0.007, 0.0016)]
face2_drops("jd_on", sl_land, 14, 3)
# sachrayotgan tomchilar
rsp = random.Random(4)
splash = []
for i in range(26):
    d = sphere(f"splash{i}", rsp.uniform(0.0008, 0.0022), tuple(G3), juice_m, sub=2)
    a = rsp.uniform(0, 2 * math.pi); sp = rsp.uniform(0.04, 0.12); up = rsp.uniform(0.02, 0.07)
    for k in range(0, 22, 2):
        t = k / 24.0 * 0.35                                # sekin harakat
        p = G3 + V(math.cos(a) * sp * t + 0.01 * math.cos(a), math.sin(a) * sp * t + 0.01 * math.sin(a), max(0.0006, 0.004 + up * t - 4.9 * t * t * 0.35))
        key(d, F_LAND + k, loc=tuple(p))
    splash.append(d)
    vis(d, [(F_LAND, F_LAND + 22)])
vis(sl_land, [S["land"], S["moist"]])

# 8) poldagi ho'l/yog'li ovqatlar
wet_grp = empty("wet_grp", tuple(G4))
s8 = slice_obj("slice_wet", (0.0, 0.0, 0.0), (90, 0, -20), parent=wet_grp)
face2_drops("jd8_", s8, 10, 8)
sausage("saus_wet", (0.06, 0.06, 0.012), 35).parent = wet_grp
pud, _ = sauce("sauce_wet", (-0.065, 0.05, 0.0)); pud.parent = wet_grp; pud.scale = (2.4, 1.9, 0.22)
pud.modifiers["d"].strength = 0.006
vis(wet_grp, [S["wet"]])

# 9) meva, go'sht, sous navbat bilan tushadi
three = empty("three_grp", tuple(G5))
s9 = slice_obj("slice9", parent=three)
for f, p, r in ((F_MEVA - 14, (-0.16, 0.0, 0.45), (40, 10, 0)), (F_MEVA, (-0.16, 0.0, 0.0), (90, 0, 25)),
                (F_MEVA + 4, (-0.16, 0.0, 0.008), (87, 3, 27)), (F_MEVA + 8, (-0.16, 0.0, 0.0), (90, 0, 28))):
    key(s9, f, loc=p, rot=r)
sa9 = sausage("saus9", (0, 0, 0)); sa9.parent = three
for f, p, r in ((F_GOSHT - 14, (0.0, 0.0, 0.45), (0, 40, 0)), (F_GOSHT, (0.0, 0.0, 0.012), (0, 0, 70)),
                (F_GOSHT + 4, (0.004, 0.0, 0.03), (0, -12, 74)), (F_GOSHT + 9, (0.008, 0.0, 0.012), (0, 0, 78))):
    key(sa9, f, loc=p, rot=r)
so9, sod = sauce("sauce9", (0, 0, 0)); so9.parent = three
for f, p, s in ((F_SOS - 2, (0.16, 0.0, 0.5), (0.8, 0.8, 1.5)), (F_SPLAT - 1, (0.16, 0.0, 0.018), (0.9, 0.9, 1.25)),
                (F_SPLAT + 1, (0.16, 0.0, 0.0), (2.0, 2.0, 0.35)), (F_SPLAT + 4, (0.16, 0.0, 0.0), (2.7, 2.5, 0.2)),
                (F_SPLAT + 10, (0.16, 0.0, 0.0), (2.9, 2.6, 0.2))):
    key(so9, f, loc=p, scale=s)
sod.strength = 0.0; sod.keyframe_insert("strength", frame=F_SPLAT - 1); sod.strength = 0.008; sod.keyframe_insert("strength", frame=F_SPLAT + 2)
for i in range(14):
    d = sphere(f"ksp{i}", rsp.uniform(0.0015, 0.0035), (0.16, 0, 0.004), ketchup_m, scale=(1, 1, 0.5), sub=2, parent=three)
    a = rsp.uniform(0, 2 * math.pi); r_ = rsp.uniform(0.035, 0.075)
    key(d, F_SPLAT, loc=(0.16, 0, 0.004), scale=0.3); key(d, F_SPLAT + 5, loc=(0.16 + r_ * math.cos(a), r_ * math.sin(a), 0.002), scale=1.0)
    vis(d, [(F_SPLAT, S["three"][1])])
vis(three, [S["three"]])
for o in (s9, sa9, so9): interp(o, "LINEAR")

# 13-14) sekundomer (raqamli taymer) va bo'lak
tim = empty("timer", tuple(G6 + V(0.0, 0.09, 0)))
tim.rotation_euler = (0, 0, R(-15))
body_m = mat("timer_body", (0.9, 0.9, 0.88), 0.35, coat=0.6)
box("tim_body", (0.11, 0.035, 0.08), (0, 0, 0.04), body_m, parent=tim, bevel=0.01)
box("tim_scr", (0.085, 0.004, 0.038), (0, -0.0175, 0.048), mat("timer_lcd", (0.02, 0.025, 0.02), 0.2, coat=1.0), parent=tim, bevel=0.002)
for i, x in enumerate((-0.03, 0.0, 0.03)):
    cyl(f"tim_btn{i}", 0.008, 0.01, (x, 0, 0.082), mat(f"tim_btn{i}", ((0.8, 0.1, 0.08), (0.15, 0.15, 0.15), (0.15, 0.15, 0.15))[i], 0.4), parent=tim)
lcd_m = mat("lcd_text", (1.0, 0.25, 0.08), 0.5, emit=4.0)
cu = bpy.data.curves.new("tim_txt", "FONT"); cu.body = "0.0"; cu.size = 0.03; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.0003
tt = bpy.data.objects.new("tim_txt", cu); sc.collection.objects.link(tt); tt.parent = tim
tt.location = (0, -0.0198, 0.048); tt.rotation_euler = (R(90), 0, 0); cu.materials.append(lcd_m)
s13 = slice_obj("slice13", tuple(G6 + V(0.0, -0.04, 0)), (90, 0, 160))
face2_drops("jd13_", s13, 6, 13)
prop_key(s13, "germ", S["time"][0], 0.0); prop_key(s13, "germ", S["time"][1], 1.0)
vis(tim, rng("timer", "time")); vis(s13, rng("timer", "time"))
def timer_val(f):
    if f < TIMER0: return 0.0
    if f <= F_EMAS: return 5.0 * (f - TIMER0) / (F_EMAS - TIMER0)
    if f < S["time"][0]: return 5.0
    return 5.0 + (f - S["time"][0]) * 0.35
def on_frame(scene, *a):
    f = scene.frame_current
    tt.data.body = f"{timer_val(f):.1f}"
    blink = F_EMAS <= f < S["timer"][1] and ((f - F_EMAS) // 4) % 2 == 1
    lcd_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.2 if blink else 4.0
bpy.app.handlers.frame_change_pre.append(on_frame)

# poldagi mayda chang/ushoqlar (makro realizm)
crumb_m = mat("crumb", (0.45, 0.4, 0.33), 0.8)
dust_m = mat("dust", (0.55, 0.55, 0.55), 0.9, sss=0.2)
rc = random.Random(9)
for spot, n in ((G, 40), (G3, 45), (G4, 40), (G5, 55), (G6, 40)):
    for i in range(n):
        p = spot + V(rc.uniform(-0.25, 0.25), rc.uniform(-0.25, 0.25), 0)
        r_ = rc.uniform(0.0004, 0.0016)
        o = sphere(f"crumb{i}", r_, tuple(p + V(0, 0, r_ * 0.4)), crumb_m if rc.random() < 0.6 else dust_m, scale=(1, rc.uniform(0.6, 1.4), 0.6), sub=1)
        kit_objs.append(o)
    for i in range(3):     # tola/soch
        p0 = spot + V(rc.uniform(-0.2, 0.2), rc.uniform(-0.2, 0.2), 0.0004)
        cu_ = bpy.data.curves.new("fib", "CURVE"); cu_.dimensions = "3D"; cu_.bevel_depth = 0.00018
        sp = cu_.splines.new("NURBS"); sp.points.add(4); a0 = rc.uniform(0, 6.3)
        for k in range(5):
            a0 += rc.uniform(-0.8, 0.8)
            sp.points[k].co = (p0.x + 0.012 * k * math.cos(a0), p0.y + 0.012 * k * math.sin(a0), 0.0004, 1)
        sp.use_endpoint_u = True
        fo = bpy.data.objects.new("fiber", cu_); sc.collection.objects.link(fo); cu_.materials.append(dust_m); kit_objs.append(fo)

# ---------------- poldagi va stoldagi "ko'rinmas" mikroblar (yashil UV nur) ----------------
def uv_mat(name, center):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    geo = N.new("ShaderNodeNewGeometry")
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 45.0; L.new(geo.outputs["Position"], vo.inputs["Vector"])
    cl = N.new("ShaderNodeTexNoise"); cl.inputs["Scale"].default_value = 2.2; cl.inputs["Detail"].default_value = 3; L.new(geo.outputs["Position"], cl.inputs["Vector"])
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.inputs["Scale"].default_value = 260.0; L.new(geo.outputs["Position"], vo2.inputs["Vector"])
    d1 = math_n(N, L, "LESS_THAN", vo.outputs["Distance"], 0.17)
    d2 = math_n(N, L, "LESS_THAN", vo2.outputs["Distance"], 0.16)
    dots = math_n(N, L, "MAXIMUM", math_n(N, L, "MULTIPLY", d1, math_n(N, L, "GREATER_THAN", cl.outputs["Fac"], 0.5)),
                  math_n(N, L, "MULTIPLY", d2, math_n(N, L, "GREATER_THAN", cl.outputs["Fac"], 0.42)))
    vm = N.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"; L.new(geo.outputs["Position"], vm.inputs[0]); vm.inputs[1].default_value = center
    rev = obj_attr(m, "rev")
    mask = math_n(N, L, "DIVIDE", math_n(N, L, "SUBTRACT", rev, vm.outputs["Value"]), 0.35, clamp=False)
    mask = math_n(N, L, "MINIMUM", math_n(N, L, "MAXIMUM", mask, 0.0), 1.0)
    fac = math_n(N, L, "MULTIPLY", dots, mask)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.3, 1.0, 0.12, 1); em.inputs["Strength"].default_value = 14.0
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(fac, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0])
    return m
uvm = uv_mat("uv_germs", tuple(MEG + V(0.2, -0.9, 0)))
uv_floor = plane("uv_floor", (X1 - X0 - 0.02, Y1 - Y0 - 0.02), (0, 0, 0.0008), uvm)
uv_table = plane("uv_table", (1.15, 1.9), (-1.55, -0.1, TABLE_TOP + 0.0015), uvm)
for o in (uv_floor, uv_table):
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
    prop_key(o, "rev", 1, 0.0); prop_key(o, "rev", S["uv"][0], 0.0); prop_key(o, "rev", S["uv"][0] + 50, 3.8)
    prop_key(o, "rev", S["timer"][0] - 1, 3.8); prop_key(o, "rev", S["timer"][0], 0.0)
    prop_key(o, "rev", S["dirty"][0], 6.0)
    interp(o, "LINEAR");
    for fc in fcurves(o):
        for k in fc.keyframe_points:
            if k.co[0] in (S["timer"][0] - 1, S["timer"][0], S["dirty"][0]): k.interpolation = "CONSTANT"
    vis(o, rng("uv", "dirty"))

# ======================================================================
# 3) MEGAN: tik turadi, poldan oladi (Unarmed_Grab_Torch_From_Floor), yeydi (Drinking, chap qo'l)
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
soften(mmeshes, 0.5)
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0, ext="HOLD_FORWARD"):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=True, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo; s.extrapolation = ext
    return s
mroot.location = tuple(MEG)
GRAB_ACT = A_("Unarmed_Grab_Torch_From_Floor.fbx", inplace=False)
GRAB_S0 = F_GRAB - 39
strip(meg, GRAB_ACT, GRAB_S0, ext="HOLD")
DRINK = A_("Drinking.fbx")
strip(meg, DRINK, S["eat"][0], src=(78, 98), speed=0.8)
strip(meg, DRINK, S["lie"][0], src=(92, 99), speed=0.25)
strip(meg, A_("Idle_9.fbx"), S["uv"][0] - 20, src=(1, 200), ext="NOTHING")
strip(meg, DRINK, S["dirty"][0] - 40, src=(53, 91), speed=0.8)
handE = child_of_bone("meg_lhand", meg, "LeftHand")
HAND_OFF = tuple(float(x) for x in os.environ.get("HAND_OFF", "-0.027,0.105,0.008").split(","))
HAND_ROLL = float(os.environ.get("HAND_ROLL", "0"))
_q = Vector((-0.11, 0.73, -0.68)).normalized().to_track_quat("Z", "Y")
sl_hand = slice_obj("slice_hand", HAND_OFF, (0, 0, 0), parent=handE)
sl_hand.rotation_mode = "QUATERNION"; from mathutils import Quaternion
sl_hand.rotation_quaternion = _q @ Quaternion((0, 0, 1), R(HAND_ROLL))
vis(sl_hand, [(F_GRAB, S["lie"][1]), S["dirty"]])
prop_key(sl_hand, "germ", 1, 0.0); prop_key(sl_hand, "germ", S["lie"][0] + 8, 0.0); prop_key(sl_hand, "germ", S["lie"][0] + 22, 1.0)
prop_key(sl_hand, "germ", S["uv"][0], 0.0); prop_key(sl_hand, "germ", S["uv"][0] + 40, 1.0)
prop_key(sl_hand, "germ", S["dirty"][0], 1.0)
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0.0, 0.075, 0.11), headE)
sliceT = empty("sliceT", (0, 0, 0), sl_hand)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()

# ======================================================================
# 4) MIKRO DUNYO: pol yuzasi (laminat) 1 m = ~10 mkm, bakteriyalar, chang, ovqat "devori"
# ======================================================================
MC = V(100.0, 0.0, 0.0)
mic_objs = []
def M_(o): mic_objs.append(o); return o
GROOVES = [((-10, -1.2), (1, 0.15), 0.35, 0.22), ((-10, 2.5), (1, -0.1), 0.25, 0.18), ((-3, -6), (0.2, 1), 0.3, 0.2),
           ((4, -6), (-0.15, 1), 0.22, 0.15), ((-10, 7.5), (1, 0.05), 0.3, 0.2)]
def Hmic(x, y):
    h = 0.16 * noise.fractal(Vector((x * 0.32, y * 0.32, 0.3)), 1.0, 2.0, 4) + 0.035 * noise.noise(Vector((x * 2.5, y * 2.5, 1.7)))
    for (px, py), (dx, dy), w, d in GROOVES:
        l = math.hypot(dx, dy); dx, dy = dx / l, dy / l
        dist = abs((x - px) * dy - (y - py) * dx)
        h -= d * math.exp(-(dist / w) ** 2)
    return h
def mic_z(p): return Hmic(p.x - MC.x, p.y - MC.y)
nx_, ny_ = 420, 340; W_, D_ = 30.0, 24.0; ox_, oy_ = -15.0, -8.0
verts = [(ox_ + W_ * i / nx_, oy_ + D_ * j / ny_, 0) for j in range(ny_ + 1) for i in range(nx_ + 1)]
verts = [(x, y, Hmic(x, y)) for x, y, _ in verts]
faces = [(j * (nx_ + 1) + i, j * (nx_ + 1) + i + 1, (j + 1) * (nx_ + 1) + i + 1, (j + 1) * (nx_ + 1) + i) for j in range(ny_) for i in range(nx_)]
tme = bpy.data.meshes.new("micro_floor"); tme.from_pydata(verts, [], faces); tme.update()
for p in tme.polygons: p.use_smooth = True
terr = bpy.data.objects.new("micro_floor", tme); sc.collection.objects.link(terr); terr.location = tuple(MC); M_(terr)
tm = bpy.data.materials.new("micro_floor_m"); tm.use_nodes = True
_N = tm.node_tree.nodes; _L = tm.node_tree.links; _b = _N["Principled BSDF"]
_tc = _N.new("ShaderNodeTexCoord")
_nz = _N.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 0.6; _nz.inputs["Detail"].default_value = 8; _nz.inputs["Roughness"].default_value = 0.6
_L.new(_tc.outputs["Object"], _nz.inputs["Vector"])
_cr = _N.new("ShaderNodeValToRGB"); _cr.color_ramp.elements[0].color = (0.1, 0.06, 0.035, 1); _cr.color_ramp.elements[1].color = (0.45, 0.31, 0.18, 1)
_L.new(_nz.outputs["Fac"], _cr.inputs[0]); _L.new(_cr.outputs[0], _b.inputs["Base Color"])
_b.inputs["Roughness"].default_value = 0.55; _b.inputs["Coat Weight"].default_value = 0.15
_nz2 = _N.new("ShaderNodeTexNoise"); _nz2.inputs["Scale"].default_value = 14.0; _nz2.inputs["Detail"].default_value = 6; _L.new(_tc.outputs["Object"], _nz2.inputs["Vector"])
_bp = _N.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.7; _L.new(_nz2.outputs["Fac"], _bp.inputs["Height"]); _L.new(_bp.outputs[0], _b.inputs["Normal"])
_nz3 = _N.new("ShaderNodeTexNoise"); _nz3.inputs["Scale"].default_value = 90.0; _nz3.inputs["Detail"].default_value = 4; _L.new(_tc.outputs["Object"], _nz3.inputs["Vector"])
_bp2 = _N.new("ShaderNodeBump"); _bp2.inputs["Strength"].default_value = 0.4; _L.new(_nz3.outputs["Fac"], _bp2.inputs["Height"]); _L.new(_bp2.outputs[0], _bp.inputs["Normal"])
tme.materials.append(tm)
M_(plane("micro_far", (220, 220), tuple(MC + V(0, 0, -0.25)), tm))

def bact_mat(name, col, rim):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.25
    b.inputs["Subsurface Weight"].default_value = 0.7; b.inputs["Subsurface Scale"].default_value = 0.04
    b.inputs["Coat Weight"].default_value = 0.7
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
    gl = obj_attr(m, "glow")
    b.inputs["Emission Color"].default_value = (*rim, 1)
    L.new(math_n(N, L, "MULTIPLY", math_n(N, L, "POWER", lw.outputs["Facing"], 2.0), math_n(N, L, "ADD", gl, 0.6)), b.inputs["Emission Strength"])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18.0; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
GREEN = bact_mat("bact_green", (0.2, 0.55, 0.08), (0.5, 1.0, 0.3))
PINK = bact_mat("bact_pink", (0.7, 0.12, 0.28), (1.0, 0.45, 0.7))
BME = capsule_mesh("bact", 0.07, 0.36, 20)
fl_curves = []
for k in range(3):
    cu_ = bpy.data.curves.new(f"flag{k}", "CURVE"); cu_.dimensions = "3D"; cu_.bevel_depth = 0.006; cu_.bevel_resolution = 2
    sp = cu_.splines.new("NURBS"); n = 12; sp.points.add(n - 1)
    for i in range(n):
        t = i / (n - 1)
        sp.points[i].co = (-0.17 - 0.45 * t, 0.05 * math.sin(t * 9 + k * 2) * t, 0.03 * math.cos(t * 7 + k) * t, 1)
    sp.use_endpoint_u = True; fl_curves.append(cu_)
def bacterium(name, loc, rz, m, flag=True, scale=1.0):
    o = bpy.data.objects.new(name, BME); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (R(random.uniform(-8, 8)), R(random.uniform(-10, 10)), R(rz)); o.scale = (scale,) * 3
    o.material_slots and None
    o.data.materials.clear() if False else None
    o["glow"] = 0.0
    if not BME.materials: BME.materials.append(GREEN)
    o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = m
    if flag:
        for j in range(random.randint(1, 3)):
            f_ = bpy.data.objects.new(name + f"_fl{j}", random.choice(fl_curves)); sc.collection.objects.link(f_)
            f_.parent = o; f_.rotation_euler = (R(random.uniform(-40, 40)), 0, R(random.uniform(-35, 35)))
            if not f_.data.materials: f_.data.materials.append(m)
            f_.material_slots[0].link = "OBJECT"; f_.material_slots[0].material = m
    return o
def wiggle(o, amp_rot=6, amp_loc=0.0, seed=0):
    o.keyframe_insert("rotation_euler", frame=1)
    if amp_loc: o.keyframe_insert("location", frame=1)
    for fc in fcurves(o):
        if fc.data_path == "rotation_euler" and fc.array_index == 2 or (amp_loc and fc.data_path == "location" and fc.array_index < 2):
            md = fc.modifiers.new("NOISE"); md.scale = 10; md.strength = R(amp_rot) if fc.data_path == "rotation_euler" else amp_loc
            md.phase = seed * 7.3 + fc.array_index
def zone_bacteria(tag, center, n, rad, m, seed, flag=True):
    rd = random.Random(seed); out = []
    for i in range(n):
        a = rd.uniform(0, 2 * math.pi); r_ = rad * math.sqrt(rd.random())
        p = center + V(r_ * math.cos(a), r_ * math.sin(a), 0)
        p.z = mic_z(p) + 0.06
        random.seed(seed * 100 + i)
        o = bacterium(f"{tag}{i}", tuple(p), rd.uniform(0, 360), m, flag, rd.uniform(0.8, 1.25))
        out.append(o)
    return out
Z5, Z7, Z10, Z12 = MC + V(-6.5, 0, 0), MC + V(0, 0, 0), MC + V(6.5, 0, 0), MC + V(0, 7.0, 0)
B5 = zone_bacteria("b5_", Z5, 70, 3.0, GREEN, 5)
for i, o in enumerate(B5): wiggle(o, 10, 0.03, i)
B7 = zone_bacteria("b7_", Z7, 55, 2.2, GREEN, 7)
B10 = zone_bacteria("b10_", Z10, 70, 2.4, GREEN, 10)
B12 = zone_bacteria("b12_", Z12, 90, 3.2, PINK, 12)
for i, o in enumerate(B12): wiggle(o, 8, 0.02, i + 300)
# chang tolalari va zarralari (hamma mikro kadrlarda)
mdust_m = mat("mdust", (0.3, 0.29, 0.27), 0.7, sss=0.2)
mdirt_m = mat("mdirt", (0.28, 0.22, 0.16), 0.8)
rdu = random.Random(21)
for i in range(260):
    zc_ = rdu.choice((Z5, Z7, Z10, Z12)); c = zc_ + V(rdu.uniform(-4.5, 4.5), rdu.uniform(-4.5, 4.5), 0)
    if i % 9 == 0:
        cu_ = bpy.data.curves.new("mfib", "CURVE"); cu_.dimensions = "3D"; cu_.bevel_depth = rdu.uniform(0.012, 0.028); cu_.bevel_resolution = 3
        sp = cu_.splines.new("NURBS"); sp.points.add(6); a0 = rdu.uniform(0, 6.3); p = c.copy()
        for k in range(7):
            a0 += rdu.uniform(-0.7, 0.7); p = p + V(0.35 * math.cos(a0), 0.35 * math.sin(a0), 0)
            sp.points[k].co = (p.x - MC.x, p.y - MC.y, mic_z(p) + 0.05 + rdu.uniform(0, 0.15), 1)
        sp.use_endpoint_u = True
        fo = bpy.data.objects.new("mfiber", cu_); sc.collection.objects.link(fo); fo.location = tuple(MC); cu_.materials.append(mdust_m); M_(fo)
    else:
        r_ = rdu.uniform(0.03, 0.22)
        o = sphere("mgrain", r_, tuple(c + V(0, 0, mic_z(c) + r_ * 0.3)), mdirt_m if rdu.random() < 0.6 else mdust_m,
                   scale=(1, rdu.uniform(0.6, 1.3), rdu.uniform(0.5, 0.9)), sub=3)
        d = o.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("grain_t", "CLOUDS"); t.noise_scale = 0.15; d.texture = t; d.strength = r_ * 0.5
        M_(o)

# ovqat "devori" (olma to'qimasi pastdan): katakli, ho'l
def tissue_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.2; b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.02
    b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.3
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 1.2; vo.feature = "DISTANCE_TO_EDGE"
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.75, 0.62, 0.3, 1); cr.color_ramp.elements[1].color = (0.98, 0.93, 0.7, 1)
    cr.color_ramp.elements[1].position = 0.12
    L.new(vo.outputs["Distance"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"]); L.new(cr.outputs[0], b.inputs["Subsurface Radius"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.08
    L.new(math_n(N, L, "MINIMUM", vo.outputs["Distance"], 0.12), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (1.0, 0.9, 0.6, 1); b.inputs["Emission Strength"].default_value = 0.05
    return m
TISSUE = tissue_mat("tissue")
def slab(name, center):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=110, y_subdivisions=110, size=6.5, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        v.co.z = -0.12 * noise.noise(Vector((v.co.x * 0.7, v.co.y * 0.7, 3.1))) - 0.06 * noise.noise(Vector((v.co.x * 2.2, v.co.y * 2.2, 5.0)))
    smooth(o); o.data.materials.append(TISSUE)
    s = o.modifiers.new("s", "SOLIDIFY"); s.thickness = 1.5; s.offset = 1.0
    o.location = tuple(center); M_(o)
    rd = random.Random(len(name))
    for i in range(18):        # osilib turgan sharbat tomchilari
        r_ = rd.uniform(0.05, 0.14)
        d = sphere(name + f"_drop{i}", r_, (rd.uniform(-2.2, 2.2), rd.uniform(-2.2, 2.2), -r_ * 0.6), water_m, scale=(1, 1, 1.15), sub=3, parent=o)
    return o
slab7 = slab("slab7", Z7 + V(0, 0, 4.0))
SL_TOUCH = 0.42                                           # tegish payti pastki sirt balandligi
key(slab7, S["stick"][0], loc=tuple(Z7 + V(0, 0, 3.2)))
key(slab7, F_STICK - 4, loc=tuple(Z7 + V(0, 0, 1.1)))
key(slab7, F_STICK, loc=tuple(Z7 + V(0, 0, SL_TOUCH)))
key(slab7, F_STICK + 8, loc=tuple(Z7 + V(0, 0, SL_TOUCH)))
key(slab7, S["stick"][1] + 1, loc=tuple(Z7 + V(0, 0, 1.4)))
interp(slab7, "LINEAR")
rs7 = random.Random(77)
for i, o in enumerate(B7):
    p0 = o.location.copy()
    jump = rs7.randint(0, 2)
    key(o, F_STICK - 2, loc=tuple(p0)); prop_key(o, "glow", F_STICK - 2, 0.0)
    top = V(p0.x, p0.y, Z7.z + SL_TOUCH - 0.08)
    key(o, F_STICK + 1 + jump, loc=tuple(top)); prop_key(o, "glow", F_STICK + 1 + jump, 4.0)
    key(o, F_STICK + 8, loc=tuple(top)); prop_key(o, "glow", F_STICK + 12, 1.2)
    key(o, S["stick"][1] + 1, loc=tuple(top + V(0, 0, 1.4 - SL_TOUCH)))
    interp(o, "LINEAR")
wiggle_list = B7
slab10 = slab("slab10", Z10 + V(0, 0, 1.9))
key(slab10, S["magnet"][0], loc=tuple(Z10 + V(0, 0, 2.1))); key(slab10, S["magnet"][1], loc=tuple(Z10 + V(0, 0, 1.6))); interp(slab10, "LINEAR")
rs10 = random.Random(10)
M0, M1 = S["magnet"]
for i, o in enumerate(B10):
    p0 = o.location.copy()
    t0 = M0 + 4 + int((M1 - M0 - 22) * rs10.random()); t1 = t0 + rs10.randint(6, 10)
    key(o, t0, loc=tuple(p0)); prop_key(o, "glow", t0, 0.0)
    top = V(p0.x * 0.85 + Z10.x * 0.15, p0.y * 0.85 + Z10.y * 0.15, 0)
    zt = Z10.z + 1.6 + (2.1 - 1.6) * (1 - (t1 - M0) / (M1 - M0)) - 0.08
    key(o, t1, loc=(top.x, top.y, zt)); prop_key(o, "glow", t1 - 3, 3.0); prop_key(o, "glow", t1 + 6, 1.5)
    key(o, M1 + 1, loc=(top.x, top.y, zt - 0.02))
    interp(o, "LINEAR")
    o.rotation_euler.x = R(rs10.uniform(-60, 60))
for o in B5: vis(o, [S["legs"]])
for o in B7: vis(o, [S["stick"]])
for o in B10: vis(o, [S["magnet"]])
for o in B12: vis(o, [S["gut"]])
vis(slab7, [S["stick"]]); vis(slab10, [S["magnet"]])
for o in mic_objs:
    if o not in (slab7, slab10): vis(o, MIC)

for o in kit_objs: vis(o, KIT)

# ======================================================================
# 5) KAMERALAR
# ======================================================================
CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.005):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip; d.clip_end = 300
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    CAMS[name] = c
    return c
def path_keys(o, pts):
    for f, p in pts: key(o, f, loc=tuple(p))
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002, focus=None):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = camera(name, (0, 0, 0), t, lens, fstop, focus=focus or t, clip=clip); path_keys(c, pts)
    return c
def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)
def shake(cam, f0, f1, amp, seed=1, decay=True):
    rnd = random.Random(seed); base = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); p = cam.location.copy()
        k = amp * ((1 - (f - f0) / max(1, f1 - f0)) ** 2 if decay else 1.0)
        base[f] = p + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
    for f, p in base.items(): cam.location = p; cam.keyframe_insert("location", frame=f)
def orbit_pts(f0, f1, center, r0, r1, a0, a1, z0, z1, step=3):
    out = []
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = (f - f0) / max(1, f1 - f0); a = R(a0 + (a1 - a0) * t); rr = r0 + (r1 - r0) * t
        out.append((f, Vector(center) + Vector((rr * math.sin(a), -rr * math.cos(a), z0 + (z1 - z0) * t))))
    return out

# 1 ILGAK: poldan, keng ob'ektiv, bo'lak kameraga qarab tushadi, orqada xira Megan
H0, H1 = S["hook"]
def fall_p(f): sc.frame_set(f); return sl_fall.matrix_world.translation.copy()
hk = []
for f in (1, 12, 24, 36, 46):
    p = fall_p(f); hk.append((f, V(p.x - 0.07, p.y - 0.34 - 0.002 * f, max(0.045, p.z - 0.07))))
hk += [(F_LAND0, G + V(-0.07, -0.27, 0.04)), (H1, G + V(-0.05, -0.17, 0.03))]
c = abs_cam("hook", hk, [(H0, V(0, 0, 0))], 18, 2.2, focus=sl_fall)
c.constraints[0].target = sl_fall
lens_keys(c, [(H0, 16), (H1, 22)]); shake(c, F_LAND0, F_LAND0 + 8, 0.005, seed=1)
# 2 olish: yondan, past, yonlama siljish
P0, P1 = S["pick"]
c = abs_cam("pick", [(P0, G + V(0.6, -0.5, 0.1)), (F_GRAB, G + V(0.62, -0.32, 0.16)), (P1, G + V(0.66, -0.1, 0.42))],
            [(P0, G + V(0.0, 0.1, 0.22)), (F_GRAB, G + V(0.0, 0.05, 0.08)), (P1, MEG + V(0.15, -0.3, 1.0))], 20, 2.8)
# 3 yeyish: yuzga yaqin, sekin push-in
E0, E1 = S["eat"]
FE = wpos(faceT, (E0 + E1) // 2)
c = abs_cam("eat", [(E0, FE + V(0.32, -0.62, -0.08)), (E1, FE + V(0.2, -0.42, -0.04))], [(E0, FE + V(0, 0, -0.06)), (E1, FE + V(0, 0, -0.03))], 40, 2.0, focus=faceT)
# 4 yolg'on: qo'ldagi bo'lakka crash zoom, mikroblar yonadi
L0, L1 = S["lie"]
SLp = wpos(sliceT, L0 + 10)
c = abs_cam("lie", [(L0, SLp + V(0.12, -0.55, -0.12)), (L0 + 7, SLp + V(0.06, -0.26, -0.06)), (L0 + 10, SLp + V(0.035, -0.14, -0.03)), (L1, SLp + V(0.03, -0.11, -0.02))],
            [(L0, SLp)], 30, 6.0, focus=sliceT)
c.constraints[0].target = sliceT
lens_keys(c, [(L0, 26), (L0 + 7, 34), (L0 + 10, 48), (L1, 52)]); shake(c, L0 + 9, L0 + 20, 0.006, seed=4)
# 5 mikro: oyoqsiz bakteriyalar, past yonlama siljish
LG0, LG1 = S["legs"]
c = abs_cam("legs", [(LG0, Z5 + V(-1.7, -2.2, 1.15)), (LG1, Z5 + V(0.8, -2.0, 0.95))], [(LG0, Z5 + V(-0.9, 0, 0.0)), (LG1, Z5 + V(0.9, 0.2, 0.0))], 30, 1.4)
# 6 ho'l bo'lak tushadi: makro aylanma
LA0, LA1 = S["land"]
c = abs_cam("land", orbit_pts(LA0, LA1, G3 + V(0, 0, 0.0), 0.3, 0.17, -50, 35, 0.07, 0.05),
            [(LA0, G3 + V(0, 0, 0.12)), (F_LAND, G3 + V(0, 0, 0.012)), (LA1, G3 + V(0.0, 0, 0.012))], 32, 7.0)
shake(c, F_LAND, F_LAND + 10, 0.004, seed=6)
# 7 yopishish: past burchak, crash zoom
ST0, ST1 = S["stick"]
c = abs_cam("stick", [(ST0, Z7 + V(-1.0, -5.6, 0.3)), (F_STICK - 1, Z7 + V(-0.8, -5.0, 0.24)), (F_STICK + 2, Z7 + V(-0.7, -4.7, 0.22)), (ST1, Z7 + V(-0.6, -4.6, 0.22))],
            [(ST0, Z7 + V(0, 0, 0.7)), (F_STICK, Z7 + V(0, -1.0, 0.25)), (ST1, Z7 + V(0, -1.0, 0.3))], 24, 3.5)
lens_keys(c, [(ST0, 20), (F_STICK - 1, 24), (F_STICK + 2, 40), (ST1, 42)]); shake(c, F_STICK, F_STICK + 14, 0.05, seed=7)
# 8 ho'l/yog'li ovqat: sekin push-in
W0, W1 = S["wet"]
c = abs_cam("wet", [(W0, G4 + V(0.08, -0.36, 0.1)), (W1, G4 + V(0.04, -0.24, 0.065))], [(W0, G4 + V(0.0, 0.03, 0.01)), (W1, G4 + V(-0.005, 0.03, 0.01))], 36, 10.0)
# 9 uchtasi tushadi: pol darajasida yonlama ergashish
T0, T1 = S["three"]
c = abs_cam("three", [(T0, G5 + V(-0.3, -0.34, 0.06)), (F_MEVA, G5 + V(-0.2, -0.32, 0.06)), (F_GOSHT, G5 + V(-0.05, -0.3, 0.06)),
                      (F_SPLAT, G5 + V(0.1, -0.28, 0.065)), (T1, G5 + V(0.18, -0.22, 0.07))],
            [(T0, G5 + V(-0.16, 0, 0.03)), (F_MEVA + 4, G5 + V(-0.12, 0, 0.02)), (F_GOSHT + 3, G5 + V(0.0, 0, 0.02)), (F_SPLAT, G5 + V(0.15, 0, 0.01)), (T1, G5 + V(0.16, 0, 0.0))], 30, 6.0)
shake(c, F_SPLAT, F_SPLAT + 8, 0.004, seed=9)
# 10 magnit: devor ostida aylanma
MG0, MG1 = S["magnet"]
c = abs_cam("magnet", orbit_pts(MG0, MG1, Z10, 2.6, 2.2, -40, 40, 0.25, 0.3), [(MG0, Z10 + V(0, 0, 1.3)), (MG1, Z10 + V(0, 0, 1.4))], 17, 2.4)
# 11 UV: keng plan, past burchak, yashil dog'lar to'lqini
U0, U1 = S["uv"]
c = abs_cam("uv", [(U0, MEG + V(1.0, -1.75, 0.16)), (U1, MEG + V(0.45, -1.9, 0.26))], [(U0, MEG + V(-0.2, 0.0, 0.6)), (U1, MEG + V(-0.3, 0.0, 0.75))], 16, 4.0)
# 12 ichak bakteriyalari va chang: oldinga uchish
GU0, GU1 = S["gut"]
c = abs_cam("gut", [(GU0, Z12 + V(-0.4, -3.6, 0.8)), (GU1, Z12 + V(0.3, -1.3, 0.55))], [(GU0, Z12 + V(0, 0, 0.15)), (GU1, Z12 + V(0.4, 1.0, 0.1))], 22, 1.6)
# 13 taymer: push-in, "emas" da crash zoom
TM0, TM1 = S["timer"]
TP = G6 + V(0, 0.09, 0.05)
c = abs_cam("timer", [(TM0, TP + V(-0.22, -0.42, 0.04)), (F_EMAS - 1, TP + V(-0.12, -0.28, 0.02)), (F_EMAS + 2, TP + V(-0.06, -0.16, 0.005)), (TM1, TP + V(-0.05, -0.15, 0.005))],
            [(TM0, TP + V(0, -0.05, -0.02)), (TM1, TP)], 32, 8.0)
lens_keys(c, [(TM0, 30), (F_EMAS - 1, 34), (F_EMAS + 2, 44), (TM1, 46)]); shake(c, F_EMAS, F_EMAS + 12, 0.005, seed=13)
# 14 vaqt muhim emas: tez aylanma
TI0, TI1 = S["time"]
c = abs_cam("time", orbit_pts(TI0, TI1, G6 + V(0, -0.04, 0), 0.24, 0.2, 60, 175, 0.08, 0.05), [(TI0, G6 + V(0, -0.02, 0.015)), (TI1, G6 + V(0, -0.03, 0.015))], 30, 8.0)
# 15 namlik: juda yaqin push-in
MO0, MO1 = S["moist"]
sc.frame_set(MO0); _a = R(SL_ANG); _Mw = sl_land.matrix_world
FCn = _Mw @ Vector((0.024 * math.cos(_a) - 0.024, 0.024 * math.sin(_a), 0.0)); FNn = (_Mw.to_3x3() @ Vector((-math.sin(_a), math.cos(_a), 0))).normalized()
c = abs_cam("moist", [(MO0, FCn + FNn * 0.13 + V(0, 0, 0.03)), (MO1, FCn + FNn * 0.065 + V(0, 0, 0.012))], [(MO0, FCn), (MO1, FCn + V(0, 0, -0.002))], 50, 16.0)
# 16 iflos sirt: yashil poldan Megan'gacha ko'tarilish
D0, D1 = S["dirty"]
FD = wpos(faceT, D1)
c = abs_cam("dirty", [(D0, MEG + V(0.45, -1.45, 0.08)), (D0 + 20, MEG + V(0.5, -1.3, 0.5)), (D1, FD + V(0.3, -0.62, -0.08))],
            [(D0, MEG + V(0.1, -0.9, 0.0)), (D0 + 20, MEG + V(0.05, -0.5, 0.4)), (D1, FD + V(0, -0.08, -0.12))], 18, 3.2)
lens_keys(c, [(D0, 16), (D1, 26)])

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
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(90))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg_env = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_env.inputs[0])
bg_col = N.new("ShaderNodeBackground")
a1 = N.new("ShaderNodeAddShader"); L.new(bg_env.outputs[0], a1.inputs[0]); L.new(bg_col.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    k = n in KITN
    bg_env.inputs[1].default_value = 1.0 if k else 0.0; bg_env.inputs[1].keyframe_insert("default_value", frame=f)
    bg_col.inputs[0].default_value = (0.035, 0.08, 0.09, 1); bg_col.inputs[0].keyframe_insert("default_value", frame=f)
    bg_col.inputs[1].default_value = 0.0 if k else 1.0; bg_col.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys
def area(name, loc, size, col, keys, target=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT"); l.visible_camera = cam_vis
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.0); sun.data.color = (1.0, 0.93, 0.82); sun.rotation_euler = (R(52), 0, R(-75))
for f, e in lights_for(KIT, 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("win_fill", (X1 - 0.3, WCy, WCz), 1.8, (0.85, 0.92, 1.0), lights_for(KIT, 120.0), target=empty("winT", (0, 0.2, 0.8)))
area("ceil_fill", (0, 0.2, HZ_ - 0.1), 1.6, (1.0, 0.9, 0.78), lights_for(KIT, 90.0), target=empty("ceilT", (0, 0.2, 0)))
area("front_fill", (0.6, -2.2, 1.6), 1.2, (1.0, 0.95, 0.9), lights_for(KIT, 50.0), target=empty("frT", tuple(MEG + V(0, 0, 0.9))))
# makro: yaltiroq yorug'lik (ho'l sirtlarga blik)
for nm, spot, rr in (("land", G3, rng("land", "moist")), ("wet", G4, rng("wet")), ("three", G5, rng("three")), ("timer", G6, rng("timer", "time")), ("hook", G, rng("hook", "pick"))):
    tg = empty(f"mac_{nm}_T", tuple(spot))
    area(f"mac_{nm}_key", tuple(spot + V(-0.35, 0.25, 0.4)), 0.25, (1.0, 0.95, 0.88), lights_for(rr, 6.0), target=tg)
    area(f"mac_{nm}_rim", tuple(spot + V(0.3, 0.45, 0.2)), 0.2, (0.85, 0.92, 1.0), lights_for(rr, 4.0), target=tg)
# mikro
for nm, zc, rr in (("legs", Z5, rng("legs")), ("stick", Z7, rng("stick")), ("magnet", Z10, rng("magnet")), ("gut", Z12, rng("gut"))):
    tg = empty(f"mic_{nm}_T", tuple(zc))
    area(f"mic_{nm}_key", tuple(zc + V(-3.0, -2.0, 4.0)), 3.0, (1.0, 0.92, 0.8), lights_for(rr, 380.0), target=tg)
    area(f"mic_{nm}_rim", tuple(zc + V(2.5, 4.0, 1.5)), 3.0, (0.3, 0.75, 1.0), lights_for(rr, 700.0), target=tg)
    area(f"mic_{nm}_fill", tuple(zc + V(2.0, -4.0, 1.0)), 4.0, (0.6, 0.8, 0.9), lights_for(rr, 70.0), target=tg)
# devor ostidan iliq nur (ovqat devori)
area("slab_glow", tuple(Z10 + V(0, 0, 0.9)), 2.5, (1.0, 0.85, 0.55), lights_for(rng("magnet"), 500.0), target=empty("sgT", tuple(Z10)))
area("slab_side", tuple(Z10 + V(0.5, -4.0, 0.7)), 2.0, (0.9, 0.95, 1.0), lights_for(rng("magnet"), 900.0), target=empty("ssT", tuple(Z10 + V(0, 0, 0.7))))
area("slab_side7", tuple(Z7 + V(4.5, -2.0, 0.5)), 2.0, (0.9, 0.95, 1.0), lights_for(rng("stick"), 900.0), target=empty("ss7T", tuple(Z7 + V(0, 0, 0.4))))

# ======================================================================
# 7) RENDER
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
