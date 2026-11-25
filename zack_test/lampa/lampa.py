# Qorong'ida (stol lampasi / telefon yorug'ida) o'qish ko'zga nima qiladi — Zack D. Films uslubida 41.8 s video (1004 kadr).
# Asos: zack_test/scene3.py (xona), mixchar.py (Mixamo), gazli/gazli.py (yordamchilar, rentgen), gazli/eye.py (makro ko'z, barmoq).
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/lampa/lampa.py --render
# Sinov: FRAMES=12,40,300,450,620 PCT=35
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
import eye as E
sc = bpy.context.scene
sc.render.fps = 24
END = 1004
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "switch"), (25, "room_off"), (56, "lamp"), (102, "phone"), (136, "clock"), (172, "eye_strain"),
         (239, "dark_wide"), (269, "page"), (336, "eye_dark"), (390, "eye_bright"), (430, "pupil_pump"),
         (492, "focus_pov"), (560, "lens"), (599, "muscles"), (664, "tired"), (694, "rub_eyes"), (718, "pain_xray"),
         (758, "blur_pov"), (796, "dry_eye"), (851, "keep_reading"), (909, "yawn"), (938, "text_swim"), (960, "sleep")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
LIGHT_OFF = 15            # shift chirog'i o'chadi (o'chirgich bosilgan kadr)

# ---------------- yordamchilar ----------------
def link(o, parent=None):
    sc.collection.objects.link(o)
    if parent: o.parent = parent
    return o
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); link(o, parent); o.location = loc; return o
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale; o.keyframe_insert("scale", frame=f)
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
def smooth(o):
    if o.type == "MESH":
        for p in o.data.polygons: p.use_smooth = True
def mat(name, col, rough=0.5, metal=0.0, emit=0.0, coat=0.0, alpha=1.0, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    if sss: b.inputs["Subsurface Weight"].default_value = sss
    return m
def emission_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"]); return m
def rim_mat(name, col, strength, core=0.0, power=2.0, alpha_core=0.0):
    """chekkasi yonadigan (fresnel) shaffof material: pufakcha, rentgen a'zosi, zarra"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = power; L.new(lw.outputs["Facing"], pw.inputs[0])
    ad = N.new("ShaderNodeMath"); ad.operation = "ADD"; ad.use_clamp = True; ad.inputs[1].default_value = alpha_core; L.new(pw.outputs[0], ad.inputs[0])
    em = N.new("ShaderNodeEmission"); em.name = "EM"; em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(ad.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs["Surface"]); return m
def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n
def key_value(node, f, v):
    node.outputs[0].default_value = v; node.outputs[0].keyframe_insert("default_value", frame=f)
def box(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); o.parent = parent; return o
def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o); o.parent = parent; return o
def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m); smooth(o); o.parent = parent; return o
def inst(src, name, loc, scale=1.0, parent=None):
    o = bpy.data.objects.new(name, src.data); link(o, parent); o.location = loc
    o.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale; return o
def tube(name, pts, m, res=12, sides=24):
    """[(x,y,z,r), ...] egri chiziq bo'ylab o'zgaruvchan radiusli mesh (oshqozon, bez, qizilo'ngach)"""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = sides // 4
    cu.resolution_u = res; cu.use_fill_caps = True
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = 3
    for p, (x, y, z, r) in zip(sp.points, pts): p.co = (x, y, z, 1); p.radius = r
    o = bpy.data.objects.new(name, cu); link(o)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    with bpy.context.temp_override(active_object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.convert(target="MESH")
    o = bpy.data.objects[name]; o.data.materials.clear(); o.data.materials.append(m); smooth(o); return o
def import_gltf(path, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler.z = R(rot_z); root.scale = (scale,) * 3
    return root, new
def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
def backdrop(name, center, radius, c_top, c_bot, strength=1.0):
    """set atrofidagi yopiq fon (quyosh va HDRI ni to'sadi): tepadan pastga gradient"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -radius * 0.6; mr.inputs[2].default_value = radius * 0.6
    L.new(sx.outputs[2], mr.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(mr.outputs[0], mx.inputs["Factor"])
    mx.inputs[6].default_value = (*c_bot, 1); mx.inputs[7].default_value = (*c_top, 1)
    em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = strength; L.new(mx.outputs[2], em.inputs[0])
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    o = sphere(name, radius, center, m, sub=4)
    for p in o.data.polygons: p.use_smooth = True
    return o
# ======================================================================
# 0) Poly Haven PBR material
# ======================================================================
def pbr(name, folder, scale=1.0, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, nc=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = "BOX"; t.projection_blend = 0.2
        if nc: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = img("diff.jpg")
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        L.new(d.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    else: L.new(d.outputs[0], b.inputs["Base Color"])
    r = img("rough.jpg", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

# ======================================================================
# 1) XONA (tungi xona: scene3.py ichki qismi + Poly Haven)
# ======================================================================
M = dict(floor=pbr("ph_floor", "laminate_floor_02", 0.5), wall=pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.85, 0.86, 0.88)),
         trim=mat("trim", (0.92, 0.92, 0.9), 0.4), night=emission_mat("night", (0.05, 0.09, 0.22), 1.2),
         curtain=mat("curtain", (0.16, 0.2, 0.3), 0.9), darkwood=mat("darkwood", (0.15, 0.08, 0.04), 0.4, coat=0.4),
         door=mat("door", (0.35, 0.22, 0.14), 0.35, coat=0.3), rug=mat("rug", (0.25, 0.28, 0.35), 0.95))
box("floor", (6, 5, 0.06), (0, 2.5, -0.03), M["floor"])
box("ceiling", (6, 5, 0.06), (0, 2.5, 2.73), M["trim"])
# orqa devor (deraza chapda: x -2.4..-1.0)
box("wall_back_r", (4.0, 0.12, 2.7), (1.0, 5.0, 1.35), M["wall"]); box("wall_back_l", (0.6, 0.12, 2.7), (-2.7, 5.0, 1.35), M["wall"])
box("wall_back_b", (1.4, 0.12, 0.9), (-1.7, 5.0, 0.45), M["wall"]); box("wall_back_t", (1.4, 0.12, 0.5), (-1.7, 5.0, 2.45), M["wall"])
box("window_night", (1.4, 0.02, 1.3), (-1.7, 5.35, 1.55), M["night"])
for x in (-2.38, -1.02): box("wframe", (0.05, 0.16, 1.3), (x, 5.0, 1.55), M["trim"])
box("wframe_m", (1.4, 0.16, 0.05), (-1.7, 5.0, 1.55), M["trim"]); box("wframe_v", (0.05, 0.16, 1.3), (-1.7, 5.0, 1.55), M["trim"])
for x in (-2.55, -0.85): box("curtain", (0.45, 0.06, 2.3), (x, 4.86, 1.4), M["curtain"])
box("wall_left", (0.12, 5, 2.7), (-3.0, 2.5, 1.35), M["wall"]); box("wall_right", (0.12, 5, 2.7), (3.0, 2.5, 1.35), M["wall"])
box("wall_front", (6, 0.12, 2.7), (0, 0.0, 1.35), M["wall"])
box("door", (0.9, 0.04, 2.08), (3.0 - 0.08, 0.9, 1.04), M["door"], rot=(0, 0, 90))
for x, y, l, a in ((0, 4.93, 6, 0), (-2.93, 2.5, 5, 90), (2.93, 2.5, 5, 90), (0, 0.07, 6, 0)):
    box("baseboard", (l, 0.03, 0.12), (x, y, 0.06), M["trim"], rot=(0, 0, a))
box("rug", (2.2, 1.6, 0.01), (0.2, 2.6, 0.005), M["rug"])
# shift chirog'i (o'chadi)
fix_m = mat("ceiling_fix", (1.0, 0.95, 0.85), 0.4, emit=8.0)
cyl("ceiling_fix", 0.24, 0.05, (0, 2.5, 2.68), fix_m)
EM_FIX = fix_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
EM_FIX.default_value = 8.0; EM_FIX.keyframe_insert("default_value", frame=1)
EM_FIX.default_value = 8.0; EM_FIX.keyframe_insert("default_value", frame=LIGHT_OFF - 1)
EM_FIX.default_value = 0.0; EM_FIX.keyframe_insert("default_value", frame=LIGHT_OFF)
# mebel (Poly Haven)
DESK = Vector((0.0, 4.49, 0.0))
_, desk = import_gltf(PH + "metal_office_desk/metal_office_desk.gltf", tuple(DESK), 0, 0.95)
TOP = bbox(desk)[1].z
print("stol balandligi", TOP)
MEG = Vector((-0.25, 3.74, 0.0))
_, chair = import_gltf(PH + "dining_chair_02/dining_chair_02.gltf", tuple(MEG + Vector((0, -0.04, 0))), float(os.environ.get("CHAIR_ROT", 180)))
_, shelf = import_gltf(PH + "wooden_bookshelf_worn/wooden_bookshelf_worn.gltf", (-2.62, 2.9, 0), -90)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.55, 4.45, 0), 0, 1.2)
import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (1.55, 4.93, 1.55), 0)
_, encyc = import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (0.55, 4.72, TOP), 180, 0.9)
CLK = Vector((0.75, 4.935, 1.85))
_, clock = import_gltf(PH + "wall_clock/wall_clock.gltf", tuple(CLK), 0)
hands = {k: next(o for o in clock if o.name.endswith(k + "_hand")) for k in ("hours", "minute", "second")}

# ---------------- stol lampasi: boshini topib, kitobga buramiz ----------------
BOOK = Vector((MEG.x, 4.23, TOP))
LAMP = Vector((0.2, 4.62, TOP))
lamp_root, lamp = import_gltf(PH + "desk_lamp_arm_01/desk_lamp_arm_01.gltf", tuple(LAMP), 0)
def lamp_head():
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in lamp if o.type == "MESH" for v in o.data.vertices]
    zt = max(p.z for p in pts); top = [p for p in pts if p.z > zt - 0.12]
    return sum(top, Vector()) / len(top)
h = lamp_head(); d = (h - LAMP); want = (BOOK - LAMP)
lamp_root.rotation_euler.z = math.atan2(want.y, want.x) - math.atan2(d.y, d.x)
LH = lamp_head()
print("lampa boshi", LH)
bulb_m = emission_mat("bulb", (1.0, 0.82, 0.55), 30.0)
bulb = sphere("bulb", 0.018, tuple(LH + Vector((0, 0, -0.035))), bulb_m, sub=2)
BULB_EM = bulb_m.node_tree.nodes["Emission"].inputs["Strength"]

# ---------------- ochiq kitob (sahifada matn, procedural) ----------------
def page_material():
    m = bpy.data.materials.new("page"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.75
    b.inputs["Subsurface Weight"].default_value = 0.08; b.inputs["Subsurface Scale"].default_value = 0.001
    def M_(op, a, bb=None, clamp=False):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, bb)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    tc = N.new("ShaderNodeTexCoord")
    swim = value_node(m, "SWIM", 0.0)
    wob = N.new("ShaderNodeTexNoise"); wob.inputs["Scale"].default_value = 22.0; L.new(tc.outputs["Object"], wob.inputs["Vector"])
    wv = N.new("ShaderNodeVectorMath"); wv.operation = "SUBTRACT"; L.new(wob.outputs["Color"], wv.inputs[0]); wv.inputs[1].default_value = (0.5, 0.5, 0.5)
    ws = N.new("ShaderNodeVectorMath"); ws.operation = "SCALE"; L.new(wv.outputs[0], ws.inputs[0])
    L.new(M_("MULTIPLY", swim.outputs[0], 0.02), ws.inputs["Scale"])
    va = N.new("ShaderNodeVectorMath"); va.operation = "ADD"; L.new(tc.outputs["Object"], va.inputs[0]); L.new(ws.outputs[0], va.inputs[1])
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(va.outputs[0], sx.inputs[0]); X, Y = sx.outputs[0], sx.outputs[1]
    LH_ = 0.0056
    yl = M_("DIVIDE", Y, LH_)
    band = M_("LESS_THAN", M_("FRACT", yl), 0.42)
    row = M_("FLOOR", yl)
    cw = N.new("ShaderNodeCombineXYZ"); L.new(M_("MULTIPLY", X, 55.0), cw.inputs[0]); L.new(M_("MULTIPLY", row, 7.31), cw.inputs[1])
    wn = N.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 1.0; wn.inputs["Detail"].default_value = 0.0; L.new(cw.outputs[0], wn.inputs["Vector"])
    word = M_("GREATER_THAN", wn.outputs["Fac"], 0.43)
    cl = N.new("ShaderNodeCombineXYZ"); L.new(M_("MULTIPLY", X, 1400.0), cl.inputs[0]); L.new(M_("MULTIPLY", Y, 900.0), cl.inputs[1])
    ln = N.new("ShaderNodeTexNoise"); ln.inputs["Scale"].default_value = 1.0; ln.inputs["Detail"].default_value = 1.0; L.new(cl.outputs[0], ln.inputs["Vector"])
    letter = M_("GREATER_THAN", ln.outputs["Fac"], 0.42)
    ax = M_("ABSOLUTE", X)
    region = M_("MULTIPLY", M_("MULTIPLY", M_("GREATER_THAN", ax, 0.024), M_("LESS_THAN", ax, 0.15)), M_("LESS_THAN", M_("ABSOLUTE", Y), 0.094))
    nrm = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Normal"], nrm.inputs[0])
    topf = M_("GREATER_THAN", nrm.outputs[2], 0.6)
    ink = M_("MULTIPLY", M_("MULTIPLY", M_("MULTIPLY", band, word), M_("MULTIPLY", letter, region)), topf)
    # sahifa chetiga qarab biroz sarg'ish, umurtqaga yaqin soya
    shade = M_("MULTIPLY", M_("SUBTRACT", 1.0, M_("MULTIPLY", M_("SUBTRACT", 1.0, M_("DIVIDE", ax, 0.03), clamp=True), 0.35)), 1.0)
    pc = N.new("ShaderNodeMix"); pc.data_type = "RGBA"; L.new(shade, pc.inputs["Factor"])
    pc.inputs[6].default_value = (0.55, 0.5, 0.42, 1); pc.inputs[7].default_value = (0.93, 0.9, 0.82, 1)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(M_("MULTIPLY", ink, 0.92), mx.inputs["Factor"])
    L.new(pc.outputs[2], mx.inputs[6]); mx.inputs[7].default_value = (0.03, 0.03, 0.035, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    return m, swim
PAGE_M, SWIM = page_material()
cover_m = mat("cover", (0.35, 0.05, 0.04), 0.5, coat=0.2)
def make_book(name, loc):
    root = empty(name, loc)
    W2, D2, nx, ny = 0.165, 0.115, 36, 14
    bm = bmesh.new()
    for side in (-1, 1):
        top, bot = [], []
        for j in range(ny + 1):
            y = -D2 + 2 * D2 * j / ny
            rt, rb = [], []
            for i in range(nx + 1):
                u = i / nx; x = side * (0.003 + u * (W2 - 0.003))
                z = 0.007 + 0.013 * (1 - (1 - u) ** 3) - 0.003 * u ** 8
                rt.append(bm.verts.new((x, y, z))); rb.append(bm.verts.new((x, y, 0.0)))
            top.append(rt); bot.append(rb)
        for j in range(ny):
            for i in range(nx):
                bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
                bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
        for i in range(nx):
            bm.faces.new((top[0][i], bot[0][i], bot[0][i + 1], top[0][i + 1]))
            bm.faces.new((top[ny][i], top[ny][i + 1], bot[ny][i + 1], bot[ny][i]))
        for j in range(ny):
            for i in (0, nx):
                bm.faces.new((top[j][i], top[j + 1][i], bot[j + 1][i], bot[j][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + "_pages"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name + "_pages", me); link(o, root); o.data.materials.append(PAGE_M)
    for p in me.polygons: p.use_smooth = True
    box(name + "_cover", (2 * W2 + 0.02, 2 * D2 + 0.014, 0.004), (0, 0, 0), cover_m, parent=root).location = (0, 0, -0.002)
    return root, o
book, pages = make_book("book", tuple(BOOK + Vector((0, 0, 0.004))))

# ---------------- telefon (tayanchga suyangan, ekrani Megan tomonga) ----------------
PHONE = Vector((MEG.x + 0.16, 4.47, TOP))
ph_root = empty("phone", tuple(PHONE + Vector((0, 0, 0.078)))); ph_root.rotation_euler = (R(-14), 0, R(-12))
ph_body = box("phone_body", (0.074, 0.008, 0.152), (0, 0, 0), mat("phone_body", (0.02, 0.02, 0.025), 0.25, metal=0.6, coat=0.8), parent=ph_root)
bv = ph_body.modifiers.new("bev", "BEVEL"); bv.width = 0.006; bv.segments = 4
scr_m = bpy.data.materials.new("screen"); scr_m.use_nodes = True; N = scr_m.node_tree.nodes; Lk = scr_m.node_tree.links
N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Object"], sx.inputs[0])
mth = N.new("ShaderNodeMath"); mth.operation = "MULTIPLY"; mth.inputs[1].default_value = 220; Lk.new(sx.outputs[2], mth.inputs[0])
fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"; Lk.new(mth.outputs[0], fr.inputs[0])
lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.35; Lk.new(fr.outputs[0], lt.inputs[0])
cr = N.new("ShaderNodeMix"); cr.data_type = "RGBA"; Lk.new(lt.outputs[0], cr.inputs["Factor"])
cr.inputs[6].default_value = (0.75, 0.86, 1.0, 1); cr.inputs[7].default_value = (0.15, 0.18, 0.25, 1)
em = N.new("ShaderNodeEmission"); Lk.new(cr.outputs[2], em.inputs[0]); Lk.new(em.outputs[0], N["Material Output"].inputs["Surface"])
SCR_EM = em.inputs["Strength"]
box("phone_screen", (0.066, 0.001, 0.142), (0, 0, 0), scr_m, parent=ph_root).location = (0, -0.0045, 0)
box("phone_stand", (0.06, 0.05, 0.012), tuple(PHONE + Vector((0, 0.02, 0.006))), mat("stand", (0.1, 0.1, 0.11), 0.4))

# ---------------- devordagi o'chirgich + barmoq (ilgak) ----------------
SW = Vector((2.94, 1.72, 1.25))
plate_m = mat("plate", (0.9, 0.9, 0.88), 0.3, coat=0.4)
box("sw_plate", (0.008, 0.08, 0.12), tuple(SW), plate_m)
rock = box("sw_rocker", (0.008, 0.032, 0.05), (0, 0, 0), plate_m)
rock.location = SW + Vector((-0.008, 0, 0))
key(rock, 1, rot=(0, -7, 0)); key(rock, 13, rot=(0, -7, 0)); key(rock, 15, rot=(0, 7, 0))
interp(rock, "CONSTANT")
finger = E.build_finger("finger", None, r=0.0085, length=0.15)
at = finger.data.attributes.new("lidt", "FLOAT", "POINT")
for a in at.data: a.value = 1.0
finger.rotation_euler = (R(0), R(-8), R(90 + 28))
PRESS = SW + Vector((-0.014, 0.0, -0.012))
key(finger, 1, loc=tuple(PRESS + Vector((-0.08, -0.042, -0.012))))
key(finger, 12, loc=tuple(PRESS + Vector((-0.003, 0.0, 0.0))))
key(finger, 15, loc=tuple(PRESS + Vector((0.002, 0.0, -0.002))))
key(finger, 24, loc=tuple(PRESS + Vector((-0.05, -0.027, -0.01))))
vis(finger, [(1, 24)])

# ======================================================================
# 2) MEGAN (Mixamo): o'tirib o'qiydi (Writing) + yuqori tanaga qatlamlar (Crying, Yawn) + bosh egilishi
# ======================================================================
groot, meg, gmesh = mc.load_character("meg", "Megan.fbx")
groot.location = MEG; groot.rotation_euler = (0, 0, R(180))
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
soften(gmesh)
A = lambda f, inplace=True: mc.load_action(f, inplace)
LEGS = ("Hips", "UpLeg", "Leg", "Foot", "Toe")
def upper(name):
    """faqat tananing yuqori qismi (o'tirgan pozaga qatlam qilish uchun)"""
    act = A(name + ".fbx").copy(); act.name = name + "_upper"
    for fc in list(mc._fcurves(act)):
        if '"' in fc.data_path and any(k in fc.data_path.split('"')[1] for k in LEGS):
            mc._channelbag_remove(act, fc)
    return act
mc.add_strip(meg, A("Writing.fbx"), 1, repeat=9.0, speed=1.0)
cr_ = mc.add_strip(meg, upper("Crying"), S["rub_eyes"][0] - 30, src=(1, 125), speed=1.0, blend=10, hold=False); cr_.blend_out = 8
yw = mc.add_strip(meg, upper("Yawn"), S["yawn"][0] - 9, src=(110, 175), speed=1.0, blend=8, hold=False); yw.blend_out = 8
# uxlab qolish: bosh va umurtqa oldinga egiladi (COMBINE qatlami, mahalliy X o'qi = oldinga egilish)
nod = bpy.data.actions.new("nod"); meg.animation_data.action = nod
NOD0 = S["sleep"][0] + 14
for f, ah, an, asp in ((NOD0, 0, 0, 0), (NOD0 + 7, 10, 6, 3), (NOD0 + 11, 40, 22, 12), (NOD0 + 14, 46, 26, 14), (NOD0 + 18, 43, 24, 13)):
    for bn, a in (("Head", ah), ("Neck", an), ("Spine2", asp)):
        pb = meg.pose.bones["mixamorig:" + bn]; pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = Quaternion((1, 0, 0), R(a * float(os.environ.get("NOD_SIGN", 1))))
        pb.keyframe_insert("rotation_quaternion", frame=f)
meg.animation_data.action = None
tr = meg.animation_data.nla_tracks.new(); tr.name = "nod"
ns = tr.strips.new("nod", NOD0, nod)
if hasattr(ns, "action_slot") and nod.slots: ns.action_slot = nod.slots[0]
ns.blend_type = "COMBINE"; ns.extrapolation = "HOLD_FORWARD"

def bw(name): return meg.matrix_world @ meg.pose.bones["mixamorig:" + name].head
headE = empty("meg_head")
c = headE.constraints.new("CHILD_OF"); c.target = meg; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
faceT = empty("faceT", (0, 0.09, 0.08), headE)

# ---------------- rentgen bosh (17-kadr): tana shaffof ko'k, peshona va ko'z ortida qizil og'riq ----------------
XRAY = rng("pain_xray")
def add_xray(objs):
    done = set()
    for o in objs:
        if o.type != "MESH": continue
        for m in o.data.materials:
            if not m or m.name in done: continue
            done.add(m.name); N = m.node_tree.nodes; L = m.node_tree.links
            out = next(n for n in N if n.type == "OUTPUT_MATERIAL"); lk = out.inputs["Surface"].links[0]; orig = lk.from_socket
            L.remove(lk)
            lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
            cr = N.new("ShaderNodeMath"); cr.operation = "POWER"; cr.inputs[1].default_value = 1.6
            L.new(lw.outputs["Facing"], cr.inputs[0])
            em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.65, 1.0, 1); em.inputs["Strength"].default_value = 2.2
            tr = N.new("ShaderNodeBsdfTransparent")
            xm = N.new("ShaderNodeMixShader"); L.new(cr.outputs[0], xm.inputs[0]); L.new(tr.outputs[0], xm.inputs[1]); L.new(em.outputs[0], xm.inputs[2])
            mix = N.new("ShaderNodeMixShader"); mix.name = "XRAY_MIX"
            L.new(orig, mix.inputs[1]); L.new(xm.outputs[0], mix.inputs[2]); L.new(mix.outputs[0], out.inputs["Surface"])
            fac = mix.inputs[0]; keys = [(1, 0.0)]
            for a, b in XRAY: keys += [(a, 1.0), (b + 1, 0.0)]
            for f, v in keys: fac.default_value = v; fac.keyframe_insert("default_value", frame=f)
            for fc in mc._fcurves(m.node_tree.animation_data.action):
                for k in fc.keyframe_points: k.interpolation = "CONSTANT"
add_xray(gmesh)
sc.frame_set(S["pain_xray"][0] + 10); bpy.context.view_layer.update()
HEADW = headE.matrix_world.translation.copy()
xbg = backdrop("xray_bg", HEADW + Vector((0, 0.05, 0.05)), 0.75, (0.02, 0.05, 0.12), (0.0, 0.005, 0.015), 1.0)
vis(xbg, XRAY)
skull_m = rim_mat("skull", (0.55, 0.85, 1.0), 2.5, power=2.2, alpha_core=0.03)
skull = sphere("skull", 0.085, (0, 0.1, 0.02), skull_m, scale=(0.95, 1.05, 1.15), sub=4, parent=headE)
eyes_x = []
for sx_ in (-1, 1):
    eyes_x.append(sphere("xeye", 0.012, (sx_ * 0.032, 0.088, 0.082), rim_mat("xeye", (0.6, 0.9, 1.0), 4.0, power=1.5, alpha_core=0.1), sub=3, parent=headE))
pain_m = emission_mat("pain", (1.0, 0.08, 0.02), 6.0); PAIN = pain_m.node_tree.nodes["Emission"].inputs["Strength"]
pains = [sphere("pain_fore", 0.03, (0, 0.135, 0.07), pain_m, scale=(1.6, 0.7, 0.5), sub=3, parent=headE)]
for sx_ in (-1, 1):
    pains.append(sphere("pain_eye", 0.016, (sx_ * 0.032, 0.088, 0.058), pain_m, scale=(1, 1, 1.2), sub=3, parent=headE))
p0, p1 = S["pain_xray"]
PAIN.default_value = 0.0; PAIN.keyframe_insert("default_value", frame=1)
for f in range(p0, p1 + 1, 10):
    PAIN.default_value = 14.0; PAIN.keyframe_insert("default_value", frame=f + 1)
    PAIN.default_value = 2.0; PAIN.keyframe_insert("default_value", frame=f + 6)
for o in [skull] + eyes_x + pains:
    vis(o, XRAY, recursive=False)
for o in pains:
    base = tuple(o.scale)
    for f in range(p0, p1 + 1, 10):
        key(o, f + 1, scale=base); key(o, f + 5, scale=tuple(x * 1.35 for x in base)); key(o, f + 9, scale=base)

# ======================================================================
# 3) KO'Z ANATOMIYASI STUDIYASI (6, 13, 14, 15): ko'z olmasi + 6 ta mushak; kesim: gavhar, kiprikli mushak, nurlar
# ======================================================================
AS = Vector((0, -200, 1.0)); EB = AS + Vector((0.12, 0, 0))
backdrop("anat_bg", AS + Vector((0.06, 0, 0)), 0.6, (0.05, 0.04, 0.06), (0.004, 0.003, 0.006), 1.0)
def muscle_material(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.4
    b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Radius"].default_value = (1, 0.25, 0.15); b.inputs["Subsurface Scale"].default_value = 0.0006
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2500, 2500, 2500)
    L.new(tc.outputs["Object"], mp.inputs[0])
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.0; wv.inputs["Distortion"].default_value = 4.0; wv.inputs["Detail"].default_value = 3.0
    wv.bands_direction = "DIAGONAL"; L.new(mp.outputs[0], wv.inputs["Vector"])
    crm = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], crm.inputs[0])
    crm.color_ramp.elements[0].color = (0.22, 0.015, 0.015, 1); crm.color_ramp.elements[1].color = (0.55, 0.07, 0.05, 1)
    L.new(crm.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.inputs["Distance"].default_value = 0.0001
    L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (1.0, 0.06, 0.02, 1)
    return m, b.inputs["Emission Strength"]
MUS_M, STRAIN = muscle_material("muscle")
STRAIN.default_value = 0.0; STRAIN.keyframe_insert("default_value", frame=1)
nerve_m = mat("nerve", (0.85, 0.78, 0.6), 0.4, sss=0.3)
def eye_muscles(center, angles, parent_name):
    out = []
    Rr = 0.012
    for i, a in enumerate(angles):
        d = Vector((math.cos(R(a)), 0, math.sin(R(a))))
        pts = [center + d * 0.0118 + Vector((0, -0.0045, 0)), center + d * 0.0133 + Vector((0, 0.003, 0)),
               center + d * 0.0115 + Vector((0, 0.013, 0)), center + d * 0.006 + Vector((0, 0.027, 0)), center + d * 0.0015 + Vector((0, 0.038, 0))]
        rad = [0.0009, 0.0015, 0.0016, 0.0012, 0.0008]
        o = tube(f"{parent_name}_rect{i}", [(*p, r) for p, r in zip(pts, rad)], MUS_M)
        o.scale = (1, 1, 1); out.append(o)
    return out
# A: butun ko'z olmasi (eye.py) + 4 to'g'ri + 2 qiyshiq mushak + ko'ruv nervi
anat_root = empty("anatA", tuple(AS))
ballA, redA = E.build_eyeball("anatA_ball", 0.012, "human", anat_root)
musA = eye_muscles(AS, [0, 90, 180, 270], "A")
for a, z in ((40, 1), (220, -1)):
    d = Vector((math.cos(R(a)), 0, math.sin(R(a))))
    pts = [AS + d * 0.0125 + Vector((0, 0.004, 0)), AS + d * 0.0145 + Vector((0, -0.002, 0)) + Vector((0, 0, z * 0.003)),
           AS + Vector((0.004 * z, -0.006, 0.016 * z)), AS + Vector((0.0, 0.01, 0.02 * z)), AS + Vector((-0.002, 0.035, 0.006 * z))]
    musA.append(tube(f"A_obl{a}", [(*p, r) for p, r in zip(pts, [0.0008, 0.0011, 0.0009, 0.0008, 0.0006])], MUS_M))
tube("A_nerve", [(*(AS + Vector(p)), 0.0017) for p in ((0, 0.010, 0), (0, 0.022, 0.0), (0, 0.04, -0.002))], nerve_m)

# B: kesim (x>0 yarmi olib tashlangan): sklera qobig'i, to'r parda, gavhar, kiprikli mushak, nurlar
_b0 = set(bpy.data.objects)
def bisect_half(o, fill=False):
    bm = bmesh.new(); bm.from_mesh(o.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    if fill:
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        bmesh.ops.edgeloop_fill(bm, edges=edges)
    bm.to_mesh(o.data); bm.free()
sclera_m = mat("sclera", (0.85, 0.8, 0.76), 0.25, sss=0.1, coat=0.6)
retina_m = bpy.data.materials.new("retina"); retina_m.use_nodes = True; N = retina_m.node_tree.nodes; Lk = retina_m.node_tree.links
rb = N["Principled BSDF"]; rb.inputs["Roughness"].default_value = 0.35
nzr = N.new("ShaderNodeTexNoise"); nzr.inputs["Scale"].default_value = 1800; nzr.inputs["Distortion"].default_value = 0.6; nzr.inputs["Detail"].default_value = 4
tcr = N.new("ShaderNodeTexCoord"); Lk.new(tcr.outputs["Object"], nzr.inputs["Vector"])
crr = N.new("ShaderNodeValToRGB"); Lk.new(nzr.outputs["Fac"], crr.inputs[0])
crr.color_ramp.elements[0].position = 0.47; crr.color_ramp.elements[0].color = (0.6, 0.16, 0.06, 1)
crr.color_ramp.elements[1].position = 0.5; crr.color_ramp.elements[1].color = (0.25, 0.01, 0.01, 1)
e3 = crr.color_ramp.elements.new(0.53); e3.color = (0.6, 0.16, 0.06, 1)
Lk.new(crr.outputs[0], rb.inputs["Base Color"])
rb.inputs["Emission Color"].default_value = (0.9, 0.3, 0.1, 1); rb.inputs["Emission Strength"].default_value = 0.15
rim_cut_m = mat("cut_rim", (0.9, 0.55, 0.5), 0.4, sss=0.3)
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=0.012, location=(0, 0, 0))
shell = bpy.context.object; shell.name = "B_shell"
bisect_half(shell)
shell.data.materials.append(sclera_m); shell.data.materials.append(retina_m); shell.data.materials.append(rim_cut_m)
so = shell.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.0009; so.offset = -1; so.material_offset = 1; so.material_offset_rim = 2
smooth(shell); shell.location = EB
# shox parda (shaffof) va kamalak parda
glass_m = bpy.data.materials.new("cornea"); glass_m.use_nodes = True; gb = glass_m.node_tree.nodes["Principled BSDF"]
gb.inputs["Roughness"].default_value = 0.0; gb.inputs["Transmission Weight"].default_value = 1.0; gb.inputs["IOR"].default_value = 1.376
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.0078, location=(0, 0, 0))
cor = bpy.context.object; cor.name = "B_cornea"
bm = bmesh.new(); bm.from_mesh(cor.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > -0.0052], context="VERTS"); bm.to_mesh(cor.data); bm.free()
bisect_half(cor); cor.data.materials.append(glass_m); smooth(cor); cor.location = EB + Vector((0, -0.0058, 0))
cs = cor.modifiers.new("solid", "SOLIDIFY"); cs.thickness = 0.0005
iris_m = mat("iris", (0.12, 0.25, 0.3), 0.5)
bm = bmesh.new(); NI = 64
outer = [bm.verts.new((0.0058 * math.cos(2 * math.pi * k / NI), 0, 0.0058 * math.sin(2 * math.pi * k / NI))) for k in range(NI)]
inner = [bm.verts.new((0.0019 * math.cos(2 * math.pi * k / NI), 0, 0.0019 * math.sin(2 * math.pi * k / NI))) for k in range(NI)]
for k in range(NI): bm.faces.new((outer[k], outer[(k + 1) % NI], inner[(k + 1) % NI], inner[k]))
me = bpy.data.meshes.new("B_iris"); bm.to_mesh(me); bm.free()
ir = bpy.data.objects.new("B_iris", me); link(ir)
bisect_half(ir); ir.data.materials.append(iris_m); ir.location = EB + Vector((0, -0.0092, 0))
ir.modifiers.new("solid", "SOLIDIFY").thickness = 0.0004
# gavhar (linza): qalinligi LT bilan o'zgaradi
lens_m = rim_mat("lens", (0.65, 0.9, 1.0), 2.5, power=1.6, alpha_core=0.25)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.0046, location=(0, 0, 0))
lens = bpy.context.object; lens.name = "B_lens"; bisect_half(lens, fill=True); lens.data.materials.append(lens_m); smooth(lens)
lens.location = EB + Vector((0, -0.0062, 0))
cil_m, CIL = muscle_material("ciliary")
bpy.ops.mesh.primitive_torus_add(major_radius=0.0062, minor_radius=0.0011, major_segments=64, minor_segments=16, rotation=(R(90), 0, 0))
cil = bpy.context.object; cil.name = "B_ciliary"; bisect_half(cil, fill=True); cil.data.materials.append(cil_m); smooth(cil)
cil.location = EB + Vector((0, -0.0062, 0))
zon_m = mat("zonule", (0.9, 0.85, 0.7), 0.4, emit=0.5)
for k in range(9):
    a = R(95 + k * 170 / 8)
    p0_ = EB + Vector((0.0046 * math.cos(a), -0.0062, 0.0046 * math.sin(a))); p1_ = EB + Vector((0.0056 * math.cos(a), -0.0062, 0.0056 * math.sin(a)))
    tube(f"zon{k}", [(*p0_, 0.00012), (*(p0_.lerp(p1_, 0.5)), 0.00012), (*p1_, 0.00012)], zon_m)
musB = eye_muscles(EB, [90, 180, 270], "B")
tube("B_nerve", [(*(EB + Vector(p)), 0.0017) for p in ((0, 0.010, 0), (0, 0.022, 0.0), (0, 0.04, -0.002))], nerve_m)
# nurlar: oldinda parallel, gavhardan keyin to'r pardada (fokus) yoki undan orqada (xira) yig'iladi
ray_m = emission_mat("ray", (1.0, 0.85, 0.4), 12.0)
def seg_verts(a, b, r=0.00012, n=8):
    d = (b - a).normalized(); u = d.orthogonal().normalized(); v = d.cross(u)
    vs = []
    for p in (a, b):
        for k in range(n):
            t = 2 * math.pi * k / n; vs.append(tuple(p + (u * math.cos(t) + v * math.sin(t)) * r))
    return vs
def seg_obj(name, a, b, b2=None, r=0.00012, n=8):
    vs = seg_verts(a, b, r, n); fs = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); o = bpy.data.objects.new(name, me); link(o)
    o.data.materials.append(ray_m)
    if b2 is not None:
        o.shape_key_add(name="Basis"); kb = o.shape_key_add(name="blur", from_mix=False); kb.value = 0.0
        for i, co in enumerate(seg_verts(a, b2, r, n)): kb.data[i].co = co
        return o, kb
    return o, None
RAY_KB = []
FOC = EB + Vector((-0.0003, 0.0112, 0))
for zz in (-0.0026, 0.0, 0.0026):
    a = EB + Vector((-0.0003, -0.06, zz)); l_ = EB + Vector((-0.0003, -0.0062, zz))
    seg_obj("ray_in", a, l_)
    if zz != 0.0:
        _, kb = seg_obj("ray_out", l_, FOC, FOC + Vector((0, -0.0003, zz * 0.4))); RAY_KB.append(kb)
    else:
        seg_obj("ray_out", l_, FOC + Vector((0, 0.0, 0)))
# kesimni tik qo'yamiz: shox parda tepada, nur yuqoridan tushadi (9:16 kadrga to'liq sig'adi)
bE = empty("B_root", tuple(EB)); bpy.context.view_layer.update()
for o in set(bpy.data.objects) - _b0 - {bE}:
    if o.parent is None:
        o.parent = bE; o.matrix_parent_inverse = bE.matrix_world.inverted()
bE.rotation_euler.x = R(-90)
# gavhar qalinligi / fokus / kiprikli mushak pulsi (13, 14)
l0, l1 = S["lens"][0] - 1, S["muscles"][1] + 1
CIL.default_value = 0.0; CIL.keyframe_insert("default_value", frame=1)
for i, f in enumerate(range(l0, l1, 9)):
    thick = i % 2 == 0
    key(lens, f, scale=(1.0, 0.82 if thick else 0.5, 1.0)); key(lens, f + 6, scale=(1.0, 0.82 if thick else 0.5, 1.0))
    for kb in RAY_KB:
        kb.value = 0.0 if thick else 1.0; kb.keyframe_insert("value", frame=f + 3)
    CIL.default_value = 3.0 if thick else 0.3; CIL.keyframe_insert("default_value", frame=f + 3)
# mushaklar zo'riqishi (qizil yonish)
for f, v in ((S["eye_strain"][0], 0.0), (S["eye_strain"][0] + 22, 1.5), (S["eye_strain"][1], 3.0)):
    STRAIN.default_value = v; STRAIN.keyframe_insert("default_value", frame=f)
f0, f1 = S["eye_strain"]
for f in range(f0 + 26, f1, 12):
    STRAIN.default_value = 4.5; STRAIN.keyframe_insert("default_value", frame=f); STRAIN.default_value = 2.0; STRAIN.keyframe_insert("default_value", frame=f + 6)
STRAIN.default_value = 1.0; STRAIN.keyframe_insert("default_value", frame=S["muscles"][0])
STRAIN.default_value = 2.5; STRAIN.keyframe_insert("default_value", frame=S["muscles"][1])
f0, f1 = S["tired"]
for f in range(f0, f1 + 1, 6):
    STRAIN.default_value = 9.0; STRAIN.keyframe_insert("default_value", frame=f); STRAIN.default_value = 3.0; STRAIN.keyframe_insert("default_value", frame=f + 3)
# A mushaklar: zo'riqqanda biroz qisqaradi (ko'z orqaga tortiladi)
for f, s in ((S["eye_strain"][0], 1.0), (S["eye_strain"][1], 0.97)):
    key(anat_root, f, loc=tuple(AS + Vector((0, 0.0012 * (1 - s) / 0.03, 0))))

# ======================================================================
# 4) MAKRO KO'Z (9, 10, 11, 19): qorachiq kengayadi / torayadi, oxirida qizarish va quruqlik
# ======================================================================
ES = Vector((0, -300, 1.0))
eyeM = E.build_eye("eyeM", tuple(ES))
PUP = eyeM["ball"].data.materials[0].node_tree.nodes["PUPIL"]
for f, v in ((1, 0.13), (S["eye_dark"][0] + 4, 0.13), (S["eye_dark"][0] + 30, 0.36), (S["eye_bright"][0] + 8, 0.36), (S["eye_bright"][0] + 12, 0.11),
             (S["pupil_pump"][0], 0.12), (447, 0.37), (458, 0.36), (471, 0.11), (480, 0.32), (489, 0.12),
             (S["dry_eye"][0], 0.2)):
    E.key_value(PUP, f, v)
red = eyeM["red"]
E.key_value(red, 1, 0.0); E.key_value(red, S["dry_eye"][0], 0.15); E.key_value(red, S["dry_eye"][0] + 34, 1.0)
E.set_key(eyeM, "squint", 1, 0.0); E.set_key(eyeM, "squint", S["dry_eye"][0] + 10, 0.0); E.set_key(eyeM, "squint", S["dry_eye"][0] + 30, 0.6)
b0 = S["dry_eye"][0] + 40
for f, v in ((b0, 0.0), (b0 + 3, 1.0), (b0 + 6, 0.0)): E.set_key(eyeM, "blink", f, v)
E.set_key(eyeM, "wide", 1, 0.0); E.set_key(eyeM, "wide", S["eye_dark"][0] + 4, 0.0); E.set_key(eyeM, "wide", S["eye_dark"][0] + 26, 0.5)
E.set_key(eyeM, "wide", S["eye_bright"][0] + 8, 0.5); E.set_key(eyeM, "wide", S["eye_bright"][0] + 14, 0.0)

# ======================================================================
# 5) LAMPA NURIDAGI CHANG ZARRALARI (3-kadr)
# ======================================================================
dust_m = emission_mat("dust", (1.0, 0.85, 0.6), 3.0)
dsrc = sphere("dust_src", 1.0, (0, 0, -50), dust_m, sub=1)
d0, d1 = S["lamp"]
for i in range(140):
    t = random.uniform(0.15, 0.95); base = LH.lerp(BOOK + Vector((0, 0, 0.02)), t)
    p = base + Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.5, 0.5))) * (0.03 + 0.12 * t)
    o = inst(dsrc, "dust", tuple(p), random.uniform(0.0006, 0.0014))
    dv = Vector((random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), random.uniform(-0.01, 0.03)))
    key(o, d0 - 1, loc=tuple(p)); key(o, d1 + 1, loc=tuple(p + dv)); interp(o)
    vis(o, [(d0, d1)])

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.01):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 500
    c = bpy.data.objects.new(name, d); link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c
def shake(cam, f0, f1, amp, seed=1):
    rnd = random.Random(seed); fc = {fc_.array_index: fc_ for fc_ in fcurves(cam) if fc_.data_path == "location"}
    base = {f: Vector([fc[i].evaluate(f) for i in range(3)]) for f in range(f0, f1)}
    for f in range(f0, f1):
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base[f] + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)
CAMS = {}
def shot(name, a, b, target, lens, fstop=None, focus=None, clip=0.01, ease=True):
    f0, f1 = S[name]
    c = camera("cam_" + name, tuple(a), target, lens, fstop, focus, clip); CAMS[name] = c
    key(c, f0, loc=tuple(a)); key(c, f1 + 1, loc=tuple(b))
    if not ease: interp(c, "LINEAR")
    return c
def lens_key(c, pairs):
    for f, l in pairs: c.data.lens = l; c.data.keyframe_insert("lens", frame=f)
def tgt(name, p): return empty(name, tuple(p))
FACE = MEG + Vector((0, 0.27, 1.1))          # taxminiy yuz (Writing pozasida)

# 1 ILGAK: o'chirgich makrosi
swT = tgt("swT", SW + Vector((-0.01, 0, -0.005)))
c = shot("switch", SW + Vector((-0.36, -0.2, 0.06)), SW + Vector((-0.27, -0.15, 0.03)), swT, 45, 2.8, ease=False)
# 2 keng, past burchak: chiroq o'chgan xona, tez itarish
roomT = tgt("roomT", MEG + Vector((0.2, 0.55, 0.85)))
c = shot("room_off", Vector((1.7, 1.2, 0.32)), Vector((1.05, 2.1, 0.45)), roomT, 16, 5.6, focus=faceT, ease=False)
# 3 lampa: past burchak, orbit
lampT = tgt("lampT", LH.lerp(BOOK, 0.35))
c = shot("lamp", LH + Vector((0.38, -0.38, -0.6)), LH + Vector((-0.05, -0.5, -0.62)), lampT, 24, 2.8, focus=bulb)
key(c, (S["lamp"][0] + S["lamp"][1]) // 2, loc=tuple(LH + Vector((0.18, -0.5, -0.6))))
# 4 telefon yorug'ida yuz
c = shot("phone", PHONE + Vector((0.07, 0.14, 0.32)), PHONE + Vector((0.03, 0.1, 0.3)), faceT, 50, 2.0)
# 5 devor soati: millar aylanadi
clkT = tgt("clkT", CLK + Vector((0, -0.05, 0)))
c = shot("clock", CLK + Vector((-0.25, -0.85, -0.25)), CLK + Vector((-0.06, -0.42, -0.06)), clkT, 40, 2.8, ease=False)
# 6 anatomiya: ko'z mushaklari, orbit
anT = tgt("anT", AS + Vector((0, 0.008, 0)))
c = shot("eye_strain", AS + Vector((0.05, -0.075, 0.03)), AS + Vector((0.08, -0.01, 0.04)), anT, 50, 8.0, clip=0.001)
key(c, (S["eye_strain"][0] + S["eye_strain"][1]) // 2, loc=tuple(AS + Vector((0.072, -0.05, 0.035))))
# 7 qorong'i xona: orqa-yondan, yon dolly
c = shot("dark_wide", Vector((-1.75, 2.35, 1.35)), Vector((-1.3, 2.15, 1.3)), tgt("dwT", MEG + Vector((0.1, 0.55, 0.9))), 24, 4.0, focus=faceT, ease=False)
# 8 yelka ortidan sahifaga: satrlar bo'ylab
pgT = empty("pgT"); key(pgT, S["page"][0], loc=tuple(BOOK + Vector((-0.09, 0.04, 0.02)))); key(pgT, S["page"][1] + 1, loc=tuple(BOOK + Vector((0.07, -0.01, 0.02)))); interp(pgT)
c = shot("page", MEG + Vector((0.2, 0.05, 1.32)), MEG + Vector((0.08, 0.28, 1.05)), pgT, 35, 2.8)
# 9-11, 19 makro ko'z
eyeT = tgt("eyeT", ES + Vector((0, -0.012, 0)))
shot("eye_dark", ES + Vector((0.012, -0.12, 0.008)), ES + Vector((0.004, -0.088, 0.002)), eyeT, 50, 10.0, clip=0.001)
shot("eye_bright", ES + Vector((-0.035, -0.08, -0.012)), ES + Vector((-0.022, -0.072, -0.006)), eyeT, 60, 12.0, clip=0.001)
c = shot("pupil_pump", ES + Vector((0.0, -0.085, 0.0)), ES + Vector((0.0, -0.062, 0.0)), eyeT, 50, 16.0, clip=0.001, ease=False)
lens_key(c, [(S["pupil_pump"][0], 45), (S["pupil_pump"][0] + 8, 68)])
shot("dry_eye", ES + Vector((0.025, -0.09, 0.012)), ES + Vector((0.01, -0.062, 0.005)), eyeT, 50, 12.0, clip=0.001)
# 12 POV: fokus qayta-qayta xiralashadi
povT = tgt("povT", BOOK + Vector((0.0, 0.0, 0.02)))
POV0 = MEG + Vector((0.0, 0.3, 1.16))
for o in gmesh:          # POV kadrlarida Megan ko'rinmaydi (kamera uning ko'zi o'rnida)
    vis(o, [(1, S["focus_pov"][0] - 1), (S["focus_pov"][1] + 1, S["blur_pov"][0] - 1), (S["blur_pov"][1] + 1, END)], recursive=False)
c = shot("focus_pov", POV0, POV0 + Vector((0.02, 0.02, -0.04)), povT, 35, 1.4, focus=0.45)
c.data.dof.focus_object = None
for i, f in enumerate(range(S["focus_pov"][0], S["focus_pov"][1] + 2, 8)):
    c.data.dof.focus_distance = 0.45 if i % 2 == 0 else (0.12 if i % 4 == 1 else 2.0); c.data.dof.keyframe_insert("focus_distance", frame=f)
# 18 POV: xiralashuv va ikkilanish
c = shot("blur_pov", POV0 + Vector((-0.02, 0, 0)), POV0 + Vector((0.01, 0.03, -0.03)), povT, 35, 1.2, focus=0.45)
c.data.dof.focus_object = None
for f, d in ((S["blur_pov"][0], 0.45), (S["blur_pov"][0] + 14, 0.2), (S["blur_pov"][0] + 24, 0.16), (S["blur_pov"][1], 0.3)):
    c.data.dof.focus_distance = d; c.data.dof.keyframe_insert("focus_distance", frame=f)
shake(c, S["blur_pov"][0] + 10, S["blur_pov"][1] + 1, 0.006, 4)
# 13-15 ko'z kesimi va mushaklar
lnT = tgt("lnT", EB + Vector((-0.001, 0.0, 0)))
shot("lens", EB + Vector((0.095, 0.006, 0.004)), EB + Vector((0.072, 0.0, 0.002)), lnT, 50, 11.0, clip=0.001)
c = shot("muscles", EB + Vector((0.07, -0.05, 0.02)), EB + Vector((0.06, 0.05, 0.03)), lnT, 45, 11.0, clip=0.001)
key(c, (S["muscles"][0] + S["muscles"][1]) // 2, loc=tuple(EB + Vector((0.088, 0.0, 0.03))))
c = shot("tired", AS + Vector((0.07, -0.04, 0.05)), AS + Vector((0.035, -0.02, 0.025)), anT, 35, 16.0, clip=0.001, ease=False)
lens_key(c, [(S["tired"][0], 35), (S["tired"][0] + 6, 55)])
shake(c, S["tired"][0], S["tired"][1] + 1, 0.0025, 7)
# 16 ko'zini ishqalaydi (yuzga yaqin, stol tomondan)
shot("rub_eyes", MEG + Vector((-0.17, 0.72, 1.2)), MEG + Vector((-0.11, 0.62, 1.17)), faceT, 50, 2.0)
# 17 rentgen bosh
shot("pain_xray", HEADW + Vector((0.3, 0.38, 0.1)), HEADW + Vector((0.18, 0.3, 0.07)), faceT, 35, None)
# 20 yondan o'rta plan
shot("keep_reading", MEG + Vector((-0.95, 0.35, 1.05)), MEG + Vector((-0.72, 0.38, 1.08)), tgt("krT", MEG + Vector((0, 0.38, 0.95))), 35, 2.8, focus=faceT)
# 21 esnash: past burchak, old tomondan
shot("yawn", MEG + Vector((0.38, 0.72, 0.86)), MEG + Vector((0.3, 0.64, 0.9)), faceT, 24, 2.8)
# 22 satrlar suzadi
shot("text_swim", BOOK + Vector((0.06, -0.14, 0.16)), BOOK + Vector((-0.04, -0.11, 0.12)), tgt("tsT", BOOK + Vector((0, 0.01, 0.015))), 50, 4.0)
# 23 uyqu: keng
shot("sleep", MEG + Vector((0.95, 0.95, 1.2)), MEG + Vector((0.8, 0.85, 1.08)), tgt("slT", MEG + Vector((0.0, 0.35, 0.92))), 28, 4.0, focus=faceT)
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["switch"]

# ======================================================================
# 7) YORUG'LIK: tun, shift chirog'i o'chadi, faqat lampa / telefon
# ======================================================================
w = bpy.data.worlds.new("night"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.026, 0.05, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
def area(name, loc, rot, energy, size, col=(1, 0.9, 0.78), target=None, keys=None, kind="AREA"):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); link(l)
    l.data.energy = energy; l.data.color = col; l.location = loc; l.rotation_euler = [R(a) for a in rot]
    if kind == "AREA": l.data.size = size
    elif kind == "SPOT": l.data.shadow_soft_size = size
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if keys:
        for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
        interp(l.data, "CONSTANT")
    return l
def on(ranges, e):
    k = [(1, 0)]
    for a, b in ranges: k += [(a, e), (b + 1, 0)]
    return k
# shift chirog'i (1-kadrda yoniq, LIGHT_OFF da o'chadi)
area("ceiling", (0, 2.5, 2.62), (0, 0, 0), 260, 1.0, (1.0, 0.92, 0.8), keys=[(1, 260), (LIGHT_OFF, 0)])
area("ceiling_sw", tuple(SW + Vector((-0.6, -0.4, 0.9))), (0, 0, 0), 25, 0.6, (1.0, 0.9, 0.78), target=swT, keys=[(1, 25), (LIGHT_OFF, 0)])
area("sw_night", tuple(SW + Vector((-0.5, -0.3, -0.1))), (0, 0, 0), 0.8, 0.5, (0.5, 0.6, 1.0), target=swT, keys=[(1, 0), (LIGHT_OFF, 0.8), (S["switch"][1] + 1, 0)])
# oy nuri (deraza)
area("moon", (-1.7, 5.7, 1.9), (-75, 0, 0), 25, 1.3, (0.55, 0.65, 1.0))
# stol lampasi: telefon kadrida o'chiq, oxirida lip-lip qilib o'chadi
lampT2 = tgt("lampT2", BOOK + Vector((0, 0.02, 0)))
LE = 70.0
ON = [(1, LE), (S["phone"][0], 0), (S["phone"][1] + 1, LE)]
fl0 = S["sleep"][0] + 26
ON += [(fl0, LE * 0.35), (fl0 + 2, LE), (fl0 + 5, LE * 0.2), (fl0 + 6, LE * 0.8), (fl0 + 9, LE * 0.1), (fl0 + 11, 0)]
spot = area("lamp_spot", tuple(LH + Vector((0, 0, -0.03))), (0, 0, 0), LE, 0.02, (1.0, 0.8, 0.55), target=lampT2, keys=ON, kind="SPOT")
spot.data.spot_size = R(95); spot.data.spot_blend = 0.6
for f, e in ON:
    BULB_EM.default_value = 30.0 * e / LE; BULB_EM.keyframe_insert("default_value", frame=f)
fill = area("lamp_bounce", tuple(BOOK + Vector((0, 0, 0.35))), (0, 0, 0), 6.0, 0.4, (1.0, 0.82, 0.6), target=faceT,
            keys=[(f, e * 6.0 / LE) for f, e in ON])
# telefon ekrani: telefon kadrida yorqin, yuzni ko'k yoritadi
SCR_EM.default_value = 0.0; SCR_EM.keyframe_insert("default_value", frame=1)
SCR_EM.default_value = 4.0; SCR_EM.keyframe_insert("default_value", frame=S["phone"][0])
SCR_EM.default_value = 0.0; SCR_EM.keyframe_insert("default_value", frame=S["phone"][1] + 1)
area("phone_light", tuple(PHONE + Vector((0, -0.02, 0.09))), (0, 0, 0), 2.2, 0.08, (0.6, 0.75, 1.0), target=faceT, keys=on(rng("phone"), 2.2))
# yuz va qahramon uchun yumshoq kontur nurlari (faqat kerakli kadrlarda)
area("face_rim", tuple(MEG + Vector((-0.7, -0.4, 1.7))), (0, 0, 0), 6, 0.5, (0.55, 0.65, 1.0), target=faceT,
     keys=on(rng("rub_eyes", "keep_reading", "yawn", "sleep", "dark_wide", "phone"), 6))
area("face_key", tuple(MEG + Vector((0.5, 0.8, 1.35))), (0, 0, 0), 3.5, 0.35, (1.0, 0.8, 0.6), target=faceT,
     keys=on(rng("rub_eyes", "yawn", "keep_reading"), 3.5))
area("clock_fill", tuple(CLK + Vector((-0.4, -0.6, -0.3))), (0, 0, 0), 4, 0.4, (1.0, 0.82, 0.6), target=clkT, keys=on(rng("clock"), 4))
# anatomiya studiyasi
for n_, off, e, col in (("an_key", (0.15, -0.15, 0.18), 6.0, (1, 0.95, 0.9)), ("an_rim", (-0.1, 0.15, 0.12), 5.0, (0.6, 0.75, 1.0)),
                        ("an_red", (0.12, 0.1, -0.12), 2.5, (1.0, 0.3, 0.2))):
    area(n_, tuple(AS + Vector(off)), (0, 0, 0), e, 0.12, col, target=anT)
    area(n_ + "B", tuple(EB + Vector(off) + Vector((0.05, 0, 0))), (0, 0, 0), e, 0.12, col, target=lnT)
# makro ko'z: qorong'ida sovuq, yorug'da iliq
eye_rng = rng("eye_dark", "eye_bright", "pupil_pump", "dry_eye")
area("eye_cool", tuple(ES + Vector((-0.09, -0.14, 0.11))), (0, 0, 0), 0.6, 0.09, (0.55, 0.65, 1.0), target=eyeM["root"], keys=on(eye_rng, 0.6))
area("eye_warm", tuple(ES + Vector((0.05, -0.14, -0.08))), (0, 0, 0), 0.0, 0.1, (1.0, 0.82, 0.55), target=eyeM["root"],
     keys=[(1, 0), (S["eye_bright"][0] + 8, 3.0), (S["pupil_pump"][0], 1.2), (447 - 6, 0.15), (471 - 6, 3.0), (480 - 4, 0.3), (489 - 4, 2.5),
           (S["dry_eye"][0], 1.6), (S["dry_eye"][1] + 1, 0)])
area("eye_red", tuple(ES + Vector((0.09, 0.0, 0.05))), (0, 0, 0), 0.6, 0.05, (1.0, 0.2, 0.1), target=eyeM["root"], keys=on(rng("dry_eye"), 0.8))

# ======================================================================
# 8) SOAT, SAHIFA SUZISHI
# ======================================================================
c0, c1 = S["clock"]
for nm_, base, turns in (("minute", 0, 3.0), ("hours", 40, 0.25), ("second", 0, 18.0)):
    o = hands[nm_]
    o.rotation_mode = "XYZ"; r0 = o.rotation_euler.copy()
    o.rotation_euler = (r0.x, r0.y - R(base), r0.z); o.keyframe_insert("rotation_euler", frame=c0 - 1)
    o.rotation_euler = (r0.x, r0.y - R(base) - turns * 2 * math.pi, r0.z); o.keyframe_insert("rotation_euler", frame=c1 + 1)
    interp(o, "LINEAR")
for f, v in ((1, 0.0), (S["text_swim"][0], 0.0), (S["text_swim"][0] + 10, 0.6), (S["text_swim"][1], 1.0), (S["sleep"][0], 0.0)):
    key_value(SWIM, f, v)

# ======================================================================
# 9) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 5; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.6))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True
for o in bpy.data.objects:            # og'ir modifikatorlar viewportda o'chiq (frame_set tezroq)
    for md in o.modifiers:
        if md.type in ("SUBSURF", "DISPLACE", "SOLIDIFY"): md.show_viewport = False

if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
