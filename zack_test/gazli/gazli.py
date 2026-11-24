# Muzdek gazli ichimlik ichgandan keyin tanada nima bo'ladi — Zack D. Films uslubida 43.6 s video (1048 kadr).
# Asos: zack_test/scene3.py (xona), mixchar.py (Mixamo), gage.py (rentgen), ebbi/eye.py (makro ko'z).
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=12 /tmp/claude-0/bvenv/bin/python -I zack_test/gazli/gazli.py --render
# Sinov: FRAMES=10,70,140,600,640 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import eye as E
sc = bpy.context.scene
sc.render.fps = 24
END = 1048
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "can_hook"), (25, "lift_wide"), (53, "drink_face"), (87, "xray_drink"), (119, "xray_fill"),
         (169, "sugar_glass"), (221, "xray_alarm"), (269, "nausea"), (319, "inside"), (375, "acid"),
         (417, "xray_calm"), (471, "relief_face"), (519, "vessel_sugar"), (585, "eye_in"), (621, "eye_dilate"),
         (651, "vessel_pulse"), (683, "xray_panc"), (741, "panc_alarm"), (781, "panc_spray"), (819, "vessel_insulin"),
         (863, "dizzy_wide"), (919, "annoyed_face"), (967, "reach"), (1011, "can_end")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
XRAY = rng("xray_drink", "xray_fill", "xray_alarm", "xray_calm", "xray_panc")

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
# 1) XONA (scene3.py ichki qismi + Poly Haven)
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
M = dict(floor=pbr("ph_floor", "laminate_floor_02", 0.5), wall=pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.95, 0.88, 0.78)),
         trim=mat("trim", (0.92, 0.92, 0.9), 0.4), winlight=mat("winlight", (1.0, 0.95, 0.85), 0.5, emit=6.0),
         curtain=mat("curtain", (0.85, 0.82, 0.72), 0.9), lampshade=mat("lampshade", (1.0, 0.85, 0.6), 0.6, emit=3.0),
         brass=mat("brass", (0.85, 0.65, 0.3), 0.25, metal=1.0), door=mat("door", (0.35, 0.08, 0.06), 0.35, coat=0.5),
         rug=mat("rug", (0.55, 0.18, 0.12), 0.95), darkwood=mat("darkwood", (0.15, 0.08, 0.04), 0.4, coat=0.4))
box("floor", (6, 5, 0.06), (0, 2.5, -0.03), M["floor"])
box("ceiling", (6, 5, 0.06), (0, 2.5, 2.73), M["trim"])
box("wall_back_l", (2.2, 0.12, 2.7), (-1.9, 5.0, 1.35), M["wall"]); box("wall_back_r", (2.2, 0.12, 2.7), (1.9, 5.0, 1.35), M["wall"])
box("wall_back_b", (1.6, 0.12, 0.85), (0, 5.0, 0.425), M["wall"]); box("wall_back_t", (1.6, 0.12, 0.45), (0, 5.0, 2.475), M["wall"])
box("window_glow", (1.8, 0.02, 1.6), (0, 5.4, 1.6), M["winlight"])
for x in (-0.78, 0.78): box("wframe", (0.06, 0.16, 1.4), (x, 5.0, 1.55), M["trim"])
box("wframe_m", (1.6, 0.16, 0.06), (0, 5.0, 1.55), M["trim"])
for x in (-1.1, 1.1): box("curtain", (0.5, 0.06, 2.3), (x, 4.88, 1.4), M["curtain"])
box("wall_left", (0.12, 5, 2.7), (-3.0, 2.5, 1.35), M["wall"]); box("wall_right", (0.12, 5, 2.7), (3.0, 2.5, 1.35), M["wall"])
for x in (-1.75, 1.75): box("wall_front", (2.5, 0.2, 2.7), (x, 0.0, 1.35), M["wall"])
box("wall_front_t", (1.0, 0.2, 0.55), (0, 0.0, 2.425), M["wall"])
box("door", (0.92, 0.05, 2.12), (0.0, 0.0, 1.06), M["door"])
for x in (-0.53, 0.53): box("dframe", (0.08, 0.26, 2.2), (x, 0, 1.1), M["trim"])
for x, y, l, a in ((0, 4.93, 6, 0), (-2.93, 2.5, 5, 90), (2.93, 2.5, 5, 90)):
    box("baseboard", (l, 0.03, 0.12), (x, y, 0.06), M["trim"], rot=(0, 0, a))
box("rug", (2.8, 1.9, 0.01), (-0.1, 2.9, 0.005), M["rug"])
cyl("lamp_base", 0.12, 0.03, (2.4, 4.4, 0.015), M["brass"]); cyl("lamp_pole", 0.015, 1.5, (2.4, 4.4, 0.75), M["brass"])
cyl("lamp_shade", 0.22, 0.32, (2.4, 4.4, 1.55), M["lampshade"])
box("shelf", (0.08, 1.4, 0.03), (-2.92, 2.0, 1.5), M["darkwood"])
for i in range(6):
    box("book", (0.16, 0.05, 0.22 + 0.03 * (i % 3)), (-2.86, 1.5 + i * 0.08, 1.63),
        mat(f"book{i}", [(0.6, 0.1, 0.1), (0.1, 0.3, 0.5), (0.8, 0.7, 0.3)][i % 3], 0.6))
import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.2, 4.35, 0), 0)
_, table = import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.2, 3.35, 0), 0)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.5, 4.5, 0), 0, 1.2)
import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-2.0, 4.92, 1.5), 0)
TOP = bbox(table)[1].z
print("stol balandligi", TOP)

# ======================================================================
# 2) BANKA (brendsiz qizil kola bankasi, terlagan)
# ======================================================================
def can_materials():
    m = bpy.data.materials.new("can_body"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    X, Y, Z = sx.outputs
    def M_(op, a, bb=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, bb)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    ang = M_("ARCTAN2", Y, X)
    wave = M_("ADD", M_("MULTIPLY", M_("SINE", M_("MULTIPLY", ang, 1.0)), 0.018), 0.004)       # oq to'lqin lenta
    d = M_("ABSOLUTE", M_("SUBTRACT", Z, wave))
    band = M_("LESS_THAN", d, 0.0075)
    band2 = M_("MULTIPLY", M_("LESS_THAN", M_("ABSOLUTE", M_("SUBTRACT", Z, M_("ADD", wave, -0.016))), 0.0018), 1.0)
    white = M_("MAXIMUM", band, band2)
    ends = M_("GREATER_THAN", M_("ABSOLUTE", Z), 0.052)          # yuqori/pastki kumush qism
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(white, mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.55, 0.012, 0.015, 1); mx.inputs[7].default_value = (0.92, 0.92, 0.9, 1)
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; L.new(ends, mx2.inputs["Factor"])
    L.new(mx.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = (0.8, 0.8, 0.82, 1)
    L.new(mx2.outputs[2], b.inputs["Base Color"])
    met = N.new("ShaderNodeMix"); L.new(ends, met.inputs["Factor"]); met.inputs[2].default_value = 0.55; met.inputs[3].default_value = 1.0
    L.new(met.outputs[0], b.inputs["Metallic"])
    # sovuqdan xira (muzlagan) dog'lar
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    rr = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], rr.inputs[0]); rr.inputs[3].default_value = 0.12; rr.inputs[4].default_value = 0.45
    L.new(rr.outputs[0], b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.08
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    drop = bpy.data.materials.new("droplet"); drop.use_nodes = True; db = drop.node_tree.nodes["Principled BSDF"]
    db.inputs["Base Color"].default_value = (1, 1, 1, 1); db.inputs["Roughness"].default_value = 0.0
    db.inputs["Transmission Weight"].default_value = 1.0; db.inputs["IOR"].default_value = 1.33
    alu = mat("can_alu", (0.82, 0.82, 0.84), 0.22, metal=1.0)
    return m, drop, alu
CAN_M, DROP_M, ALU_M = can_materials()
def make_can(name, droplets=0):
    """mahalliy: markaz (0,0,0), balandlik 0.122 (Z), radius 0.033"""
    root = empty(name)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.033, depth=0.122)
    body = bpy.context.object; body.name = name + "_body"; body.data.materials.append(CAN_M); smooth(body); body.parent = root
    for v in body.data.vertices:                       # yelka va pastki torayish
        if v.co.z > 0: v.co.x *= 0.82; v.co.y *= 0.82; v.co.z = 0.061
        else: v.co.x *= 0.85; v.co.y *= 0.85
    bpy.context.view_layer.objects.active = body
    lc = body.modifiers.new("loops", "BEVEL"); lc.width = 0.012; lc.segments = 6; lc.limit_method = "ANGLE"
    body.modifiers.new("wn", "WEIGHTED_NORMAL")
    # tanadagi silindr (kesishmasiz): yon devor
    side = cyl(name + "_side", 0.0331, 0.104, (0, 0, -0.004), CAN_M, parent=root, verts=64)
    lid = cyl(name + "_lid", 0.0262, 0.003, (0, 0, 0.0605), ALU_M, parent=root)
    rim = bpy.ops.mesh.primitive_torus_add(major_radius=0.0268, minor_radius=0.0014, location=(0, 0, 0.0625))
    rim = bpy.context.object; rim.name = name + "_rim"; rim.data.materials.append(ALU_M); smooth(rim); rim.parent = root
    tab = box(name + "_tab", (0.02, 0.011, 0.0012), (0.006, 0, 0.0628), ALU_M, parent=root)
    hole = box(name + "_hole", (0.012, 0.009, 0.0008), (-0.011, 0, 0.0624), mat("can_hole", (0.01, 0.005, 0.003), 0.4), parent=root)
    if droplets:
        src = sphere(name + "_drop_src", 1.0, (0, 0, -50), DROP_M, scale=(1, 1, 0.55), sub=2)
        rnd = random.Random(5)
        for i in range(droplets):
            a = rnd.uniform(0, 2 * math.pi); z = rnd.uniform(-0.05, 0.048); s = rnd.uniform(0.0005, 0.0016)
            d = inst(src, f"{name}_drop", (0.0336 * math.cos(a), 0.0336 * math.sin(a), z), (s, s, s * 0.4), root)
            d.rotation_euler = (0, R(90), a)
        bpy.data.objects.remove(src, do_unlink=True)
    return root
CAN_T = Vector((0.12, 3.18, TOP + 0.061))
can_table = make_can("can_table", droplets=260); can_table.location = CAN_T
can_hand = make_can("can_hand", droplets=80)

# ======================================================================
# 3) MEGAN (Mixamo) + harakatlar
# ======================================================================
MEG = Vector((0.35, 2.42, 0.0))
groot, meg, gmesh = mc.load_character("meg", "Megan.fbx")
groot.location = MEG
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
def at(f, loc, rz):
    groot.location = loc; groot.rotation_euler = (0, 0, R(rz))
    groot.keyframe_insert("location", frame=f); groot.keyframe_insert("rotation_euler", frame=f)
at(1, tuple(MEG), 0)
REACH = Vector((CAN_T.x - 0.13, CAN_T.y - 0.5, 0)); at(S["reach"][0], tuple(REACH), 180)
interp(groot, "CONSTANT")
mc.add_strip(meg, A("Drinking.fbx"), 1, src=(60, 267), speed=1.0, hold=False)
idle = mc.add_strip(meg, A("Breathing_Idle.fbx"), 150, repeat=4.0, speed=1.0, blend=14)
st = mc.add_strip(meg, A("Big_Stomach_Hit.fbx"), 262, speed=0.55, blend=6, hold=False); st.blend_out = 12
dz = mc.add_strip(meg, A("Dizzy_Idle.fbx"), 840, speed=1.0, blend=10, hold=False, repeat=1.0); dz.blend_out = 6
an = mc.add_strip(meg, A("Annoyed_Head_Shake.fbx"), 914, speed=1.0, blend=6, hold=False); an.blend_out = 6
mc.add_strip(meg, A("Picking_Up.fbx"), S["reach"][0] - 7, src=(20, 288), speed=1.0, blend=4)

def follow(obj, bone, frames, fn):
    """obj ni har kadrda suyak(lar)dan hisoblangan dunyo matritsasiga qo'yadi (fn(pb_world) -> Matrix)"""
    obj.rotation_mode = "QUATERNION"
    for f in frames:
        sc.frame_set(f)
        mw = fn(f)
        loc, rot, _ = mw.decompose()
        obj.location = loc; obj.rotation_quaternion = rot
        obj.keyframe_insert("location", frame=f); obj.keyframe_insert("rotation_quaternion", frame=f)
def bw(name): return meg.matrix_world @ meg.pose.bones["mixamorig:" + name].head
def bmat(name):
    m = meg.matrix_world @ meg.pose.bones["mixamorig:" + name].matrix
    loc, rot, _ = m.decompose(); return Matrix.LocRotScale(loc, rot, None)

# yuz nishoni (kameralar uchun)
headE = empty("meg_head")
c = headE.constraints.new("CHILD_OF"); c.target = meg; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
faceT = empty("faceT", (0, 0.09, 0.08), headE)
mouthT = empty("mouthT", (0, 0.035, 0.095), headE)

# banka chap qo'lda (Drinking): kaft markazi, o'qi ko'rsatkich barmoq tomonga
PALM = float(os.environ.get("PALM", 1.0))
def can_in_hand(f):
    H, I, P, Mi = bw("LeftHand"), bw("LeftHandIndex1"), bw("LeftHandPinky1"), bw("LeftHandMiddle1")
    ax = (I - P).normalized(); fwd = (Mi - H).normalized()
    n = ax.cross(fwd).normalized() * PALM
    c = (H + Mi) * 0.5 + n * 0.038 + fwd * 0.015
    # og'izga yaqinlashganda banka lablarga tortiladi va qiyshayadi (Mixamo harakati stakan uchun)
    hm = headE.matrix_world; mouth = mouthT.matrix_world.translation
    fz = hm.col[2].xyz.normalized(); fy = hm.col[1].xyz.normalized()
    w = max(0.0, min(1.0, (0.30 - (H - mouth).length) / 0.12)); w = w * w * (3 - 2 * w)
    ax2 = -(fz * 0.1 + fy * 0.055).normalized()
    c = c.lerp(mouth + fz * 0.012 - ax2 * 0.058, w); ax = ax.lerp(ax2, w).normalized()
    x = (n - ax * n.dot(ax)).normalized(); z = ax; y = z.cross(x).normalized(); x = y.cross(z)
    rot = Matrix((x, y, z)).transposed().to_quaternion()
    return Matrix.LocRotScale(c, rot, None)
CAN_FR = list(range(1, 168))
follow(can_hand, "LeftHand", CAN_FR, can_in_hand)
vis(can_hand, [(1, 166)])


# ======================================================================
# 4) RENTGEN: tana shaffof ko'k, ichida qizilo'ngach, oshqozon, oshqozon osti bezi
# ======================================================================
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
add_xray(gmesh + list(can_hand.children))

XC = MEG + Vector((0, 0, 1.12))
xbg = backdrop("xray_bg", XC, 0.95, (0.02, 0.05, 0.12), (0.0, 0.005, 0.015), 1.0)
vis(xbg, XRAY)

# a'zolar: tayanch kadrda (Breathing_Idle) dunyo koordinatasida yasaladi, keyin Spine1 ga ergashadi
REF = 200
sc.frame_set(REF)
torso = empty("torso")
TFR = sorted({f for a, b in XRAY for f in range(a - 1, b + 2)})
follow(torso, "Spine1", [REF], lambda f: bmat("Spine1"))
bpy.context.view_layer.update()
SP1, SP2, NECK = bw("Spine1"), bw("Spine2"), bw("Neck")
FW = Vector((0, -1, 0)); LEFT = Vector((1, 0, 0)); UP = Vector((0, 0, 1))
SC = SP1.lerp(SP2, 0.25) + LEFT * 0.045 + FW * 0.05             # oshqozon markazi
def W(x, y, z): return SC + LEFT * x + FW * y + UP * z
organ = rim_mat("stomach", (0.3, 0.85, 1.0), 4.0, power=1.6, alpha_core=0.12)
ALARM = value_node(organ, "ALARM", 0.0)
N = organ.node_tree.nodes; Lk = organ.node_tree.links
mxc = N.new("ShaderNodeMix"); mxc.data_type = "RGBA"; Lk.new(ALARM.outputs[0], mxc.inputs["Factor"])
mxc.inputs[6].default_value = (0.3, 0.85, 1.0, 1); mxc.inputs[7].default_value = (1.0, 0.08, 0.03, 1)
Lk.new(mxc.outputs[2], N["EM"].inputs["Color"])
GLOW = value_node(organ, "GLOW", 4.0); Lk.new(GLOW.outputs[0], N["EM"].inputs["Strength"])
stp = [(0.0, 0.0, 0.085, 0.016), (0.035, 0.0, 0.06, 0.04), (0.05, 0.0, 0.01, 0.052), (0.035, 0.0, -0.045, 0.048),
       (-0.01, 0.0, -0.07, 0.038), (-0.055, 0.0, -0.05, 0.022), (-0.075, 0.0, -0.025, 0.014)]
stomach = tube("stomach", [(*W(x, y, z), r) for x, y, z, r in stp], organ)
# ichimlik: oshqozon ichida sath ko'tariladi (LEVEL), gaz pufakchalari
fill_m = bpy.data.materials.new("fill"); fill_m.use_nodes = True; N = fill_m.node_tree.nodes; Lk = fill_m.node_tree.links
N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Object"], sx.inputs[0])
LEVEL = value_node(fill_m, "LEVEL", -0.1)
lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; Lk.new(sx.outputs[2], lt.inputs[0]); Lk.new(LEVEL.outputs[0], lt.inputs[1])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 160; Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
cr = N.new("ShaderNodeValToRGB"); Lk.new(nz.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].position = 0.55; cr.color_ramp.elements[0].color = (0.45, 0.12, 0.02, 1)
cr.color_ramp.elements[1].position = 0.75; cr.color_ramp.elements[1].color = (1.0, 0.6, 0.3, 1)
em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.5; Lk.new(cr.outputs[0], em.inputs[0])
tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
Lk.new(lt.outputs[0], mx.inputs[0]); Lk.new(tr.outputs[0], mx.inputs[1]); Lk.new(em.outputs[0], mx.inputs[2])
Lk.new(mx.outputs[0], N["Material Output"].inputs["Surface"])
fill = tube("stomach_fill", [(*W(x, y, z), r * 0.85) for x, y, z, r in stp], fill_m)
# fill ob'ekti koordinatasi: markazini SC ga qo'yamiz (LEVEL nisbiy)
bpy.context.view_layer.objects.active = fill
fill.select_set(True)
sc.cursor.location = SC
with bpy.context.temp_override(active_object=fill, selected_objects=[fill], selected_editable_objects=[fill]):
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
sc.cursor.location = (0, 0, 0)     # aks holda keyingi primitivlar (ko'z olmasi) shu yerda yaratiladi
for f, v in ((1, -0.1), (96, -0.1), (165, 0.035), (200, 0.045)): key_value(LEVEL, f, v)
# qizilo'ngach
eso_pts = [NECK + FW * 0.03 + UP * 0.02, NECK.lerp(SP2, 0.5) + FW * 0.035, SP2 + FW * 0.04 + LEFT * 0.01, W(0.0, 0.0, 0.1), W(0.0, 0.0, 0.08)]
eso = tube("esophagus", [(*p, 0.011) for p in eso_pts], rim_mat("eso", (0.35, 0.85, 1.0), 3.0, power=1.4, alpha_core=0.08))
# yutilgan ichimlik "bo'laklari" qizilo'ngach bo'ylab tushadi
blob_m = emission_mat("blob", (0.9, 0.35, 0.08), 6.0)
def along(pts, t):
    seg = t * (len(pts) - 1); i = min(int(seg), len(pts) - 2); return pts[i].lerp(pts[i + 1], seg - i)
blobs = []
for i in range(7):
    b = sphere("blob", 0.009, tuple(eso_pts[0]), blob_m, scale=(1, 1, 1.8), sub=2)
    t0 = S["xray_drink"][0] + i * 4 - 2
    for k in range(0, 15):
        key(b, t0 + k, loc=tuple(along(eso_pts, k / 14)))
    blobs.append(b)
# oshqozon osti bezi (pankreas): oshqozon ostida, ko'ndalang
panc_m = rim_mat("panc", (1.0, 0.75, 0.25), 3.0, power=1.4, alpha_core=0.2)
PANIC = value_node(panc_m, "PANIC", 0.0); N = panc_m.node_tree.nodes; Lk = panc_m.node_tree.links
mxp = N.new("ShaderNodeMix"); mxp.data_type = "RGBA"; Lk.new(PANIC.outputs[0], mxp.inputs["Factor"])
mxp.inputs[6].default_value = (1.0, 0.75, 0.25, 1); mxp.inputs[7].default_value = (1.0, 0.05, 0.02, 1)
Lk.new(mxp.outputs[2], N["EM"].inputs["Color"])
PGLOW = value_node(panc_m, "PGLOW", 2.0); Lk.new(PGLOW.outputs[0], N["EM"].inputs["Strength"])
pp = [(0.07, -0.025, -0.075, 0.012), (0.03, -0.03, -0.095, 0.016), (-0.02, -0.03, -0.105, 0.019), (-0.06, -0.025, -0.1, 0.024), (-0.075, -0.02, -0.12, 0.02)]
panc = tube("pancreas", [(*W(x, y, z), r) for x, y, z, r in pp], panc_m)
dm = panc.modifiers.new("lumps", "DISPLACE"); t = bpy.data.textures.new("pl", "VORONOI"); t.noise_scale = 0.012; dm.texture = t; dm.strength = 0.004
# kislota zarralari (yashil) oshqozon atrofida aylanadi
acid_m = emission_mat("acid_x", (0.3, 1.0, 0.2), 8.0)
acids = []
for i in range(36):
    a0 = random.uniform(0, 2 * math.pi); rr = random.uniform(0.06, 0.085); zz = random.uniform(-0.05, 0.06)
    b = sphere("acid_x", random.uniform(0.002, 0.0045), (0, 0, 0), acid_m, sub=1)
    f0, f1 = S["xray_calm"]
    for k, f in enumerate(range(f0 - 1, f1 + 2, 4)):
        a = a0 + k * 0.35; r2 = rr * (1 - 0.35 * (f - f0) / (f1 - f0))
        key(b, f, loc=tuple(W(r2 * math.cos(a) - 0.005, r2 * math.sin(a) * 0.6, zz)))
    acids.append(b)
for o in [stomach, fill, eso, panc] + blobs + acids:
    o.parent = torso; o.matrix_parent_inverse = torso.matrix_world.inverted()
for o in [stomach, fill, eso, panc]:
    vis(o, XRAY, recursive=False)
for b in blobs: vis(b, rng("xray_drink"), recursive=False)
for b in acids: vis(b, rng("xray_calm"), recursive=False)
# torso endi rentgen kadrlarida Spine1 ga ergashadi
torso.animation_data_clear()
follow(torso, "Spine1", TFR, lambda f: bmat("Spine1"))
interp(torso, "LINEAR")
# oshqozon xavf signali (7-kadr) va tinchlanishi (11), bez vahimasi (17)
f0, f1 = S["xray_alarm"]
key_value(ALARM, 1, 0.0); key_value(ALARM, f0 - 1, 0.0); key_value(ALARM, f0 + 6, 1.0); key_value(ALARM, S["xray_calm"][0], 1.0)
key_value(ALARM, S["xray_calm"][0] + 34, 0.0)
key_value(GLOW, 1, 4.0)
for f in range(f0, f1 + 1, 12): key_value(GLOW, f, 9.0); key_value(GLOW, f + 6, 4.0)
f0, f1 = S["xray_calm"]
key_value(GLOW, f0, 7.0); key_value(GLOW, f0 + 34, 3.5)
f0, f1 = S["xray_panc"]
key_value(PANIC, 1, 0.0); key_value(PANIC, f0 - 1, 0.0); key_value(PANIC, f0 + 4, 1.0)
key_value(PGLOW, 1, 2.0); key_value(PGLOW, f0 - 1, 2.0)
for f in range(f0, f1 + 1, 10): key_value(PGLOW, f, 12.0); key_value(PGLOW, f + 5, 3.0)
key_value(GLOW, f0 - 1, 1.5)

# ======================================================================
# 5) KOLA STAKANI STUDIYASI (6-kadr): 10 ta qand tushadi
# ======================================================================
GS = Vector((-60, 200, 0))
backdrop("glass_bg", GS + Vector((0, 0, 0.3)), 3.0, (0.45, 0.16, 0.06), (0.01, 0.005, 0.003), 1.0)
floor_m = mat("studio_floor", (0.01, 0.008, 0.007), 0.15, coat=1.0)
box("studio_floor", (4, 4, 0.02), GS + Vector((0, 0, -0.01)), floor_m)
glass_m = bpy.data.materials.new("glass"); glass_m.use_nodes = True; gb = glass_m.node_tree.nodes["Principled BSDF"]
gb.inputs["Roughness"].default_value = 0.0; gb.inputs["Transmission Weight"].default_value = 1.0; gb.inputs["IOR"].default_value = 1.5
gl = cyl("glass", 0.042, 0.13, GS + Vector((0, 0, 0.065)), glass_m, verts=64)
for v in gl.data.vertices:
    if v.co.z < 0: v.co.x *= 0.85; v.co.y *= 0.85
bpy.context.view_layer.objects.active = gl
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
for p in gl.data.polygons: p.select = p.normal.z > 0.9
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
so = gl.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.0025
cola_m = mat("cola", (0.05, 0.012, 0.004), 0.03, coat=1.0)
cola = cyl("cola_liquid", 0.0395, 0.1, GS + Vector((0, 0, 0.053)), cola_m, verts=64)
for v in cola.data.vertices:
    if v.co.z < 0: v.co.x *= 0.86; v.co.y *= 0.86
foam_m = mat("foam", (0.75, 0.55, 0.38), 0.5)
fs_src = sphere("foam_src", 1.0, (0, 0, -60), foam_m, sub=1)
for i in range(90):
    a = random.uniform(0, 2 * math.pi); r = 0.0385 * math.sqrt(random.uniform(0.75, 1.0)) if i < 60 else 0.037 * math.sqrt(random.random())
    inst(fs_src, "foam", GS + Vector((r * math.cos(a), r * math.sin(a), 0.1035)), random.uniform(0.0008, 0.002))
sugar_m = bpy.data.materials.new("sugar"); sugar_m.use_nodes = True; N = sugar_m.node_tree.nodes; Lk = sugar_m.node_tree.links
sb = N["Principled BSDF"]; sb.inputs["Base Color"].default_value = (0.95, 0.94, 0.9, 1); sb.inputs["Roughness"].default_value = 0.55
sb.inputs["Subsurface Weight"].default_value = 0.4; sb.inputs["Subsurface Scale"].default_value = 0.002
vn = N.new("ShaderNodeTexVoronoi"); vn.inputs["Scale"].default_value = 900; bpn = N.new("ShaderNodeBump"); bpn.inputs["Strength"].default_value = 0.6
Lk.new(vn.outputs["Distance"], bpn.inputs["Height"]); Lk.new(bpn.outputs[0], sb.inputs["Normal"])
def sugar_cube(name, s, loc):
    o = box(name, (s, s, s), loc, sugar_m)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = s * 0.08; bv.segments = 2
    return o
drop_m = mat("cola_drop", (0.06, 0.015, 0.005), 0.02, coat=1.0)
f0, f1 = S["sugar_glass"]
SURF = GS.z + 0.103
for i in range(10):
    c = sugar_cube("cube", 0.012, (0, 0, 0))
    t_hit = f0 + 6 + i * 4.4
    x0 = GS + Vector((random.uniform(-0.012, 0.012), random.uniform(-0.012, 0.012), 0))
    for f in range(f0 - 1, int(t_hit) + 1):
        tt = (t_hit - f) / 24.0 * 0.45                 # sekinlashtirilgan erkin tushish
        key(c, f, loc=tuple(x0 + Vector((0, 0, SURF - GS.z + 9.8 * tt * tt * 0.5 + 0.005))),
            rot=(i * 37 + f * 4, i * 21 + f * 3, i * 13))
    key(c, int(t_hit) + 8, loc=tuple(x0 + Vector((0, 0, SURF - GS.z - 0.03))))
    vis(c, [(f0, int(t_hit) + 3)])
    for k in range(5):                                   # sachrash tomchilari
        d = sphere("splash", random.uniform(0.0015, 0.003), (0, 0, 0), drop_m, sub=1)
        a = random.uniform(0, 2 * math.pi); v = random.uniform(0.25, 0.45); up = random.uniform(0.6, 1.1)
        h0 = int(t_hit)
        for j in range(0, 11):
            t = j / 24.0 * 0.45
            key(d, h0 + j, loc=tuple(x0 + Vector((math.cos(a) * v * t * 1.6, math.sin(a) * v * t * 1.6, SURF - GS.z + up * t - 4.9 * t * t))))
        vis(d, [(h0 + 1, h0 + 9)])

# ======================================================================
# 6) ICHIMLIK ICHIDA (9, 10): pufakchalar, qand cho'kadi, yashil kislota
# ======================================================================
IS = Vector((-60, 240, 0))
backdrop("inside_bg", IS, 8.0, (0.55, 0.18, 0.04), (0.04, 0.008, 0.002), 1.0)
bub_m = rim_mat("bubble", (1.0, 0.85, 0.65), 6.0, power=3.0)
bsrc = sphere("bub_src", 1.0, (0, 0, -80), bub_m, sub=3)
f0, f1 = S["inside"][0], S["acid"][1]
for i in range(140):
    p = IS + Vector((random.uniform(-2.2, 2.2), random.uniform(-1.5, 3.5), random.uniform(-4, 3)))
    r = random.choice([0.02, 0.03, 0.05, 0.08, 0.12]) * random.uniform(0.7, 1.2)
    v = 0.6 + r * 10
    b = inst(bsrc, "bubble", tuple(p), r)
    key(b, f0 - 1, loc=tuple(p)); key(b, f1 + 1, loc=tuple(p + Vector((random.uniform(-.2, .2), 0, v * (f1 - f0 + 2) / 24))))
    interp(b)
cubes_in = []
CUBE_P = [Vector((0.0, 0.6, 0.2)), Vector((-0.9, 1.8, 0.9)), Vector((1.0, 2.4, -0.4)), Vector((-0.6, 3.2, -1.0))]
for i, p in enumerate(CUBE_P):
    c = sugar_cube("cube_in", 0.6, tuple(IS + p))
    key(c, f0 - 1, loc=tuple(IS + p + Vector((0, 0, 0.4))), rot=(10 + i * 20, 15, i * 30))
    key(c, f1 + 1, loc=tuple(IS + p + Vector((0, 0, -0.5))), rot=(40 + i * 20, 55, i * 30 + 40))
    interp(c)
    a0 = S["acid"][0]
    key(c, a0, scale=1.0); key(c, f1 + 1, scale=0.35 if i == 0 else 0.5)
    cubes_in.append(c)
acid2 = emission_mat("acid", (0.35, 1.0, 0.15), 10.0)
asrc = sphere("acid_src", 1.0, (0, 0, -80), acid2, sub=2)
a0, a1 = S["acid"]
for i in range(160):
    tgt = IS + CUBE_P[0] if i < 110 else IS + CUBE_P[1 + i % 3]
    ang = random.uniform(0, 2 * math.pi); rad0 = random.uniform(1.0, 2.5); h = random.uniform(-0.8, 0.8)
    o = inst(asrc, "acid", (0, 0, 0), random.uniform(0.012, 0.03))
    for k, f in enumerate(range(a0 - 1, a1 + 3, 3)):
        u = (f - a0) / (a1 - a0); rad = rad0 * (1 - 0.72 * u); a = ang + u * 4.0
        key(o, f, loc=tuple(tgt + Vector((rad * math.cos(a), rad * math.sin(a) * 0.7, h * (1 - 0.5 * u)))))
    vis(o, [(a0, a1)])

# ======================================================================
# 7) QON TOMIRI (13, 16, 20): eritrotsitlar, qand kristallari, insulin
# ======================================================================
VS = Vector((0, 300, 0)); VL = 70.0
vessel_m = bpy.data.materials.new("vessel"); vessel_m.use_nodes = True; N = vessel_m.node_tree.nodes; Lk = vessel_m.node_tree.links
vb = N["Principled BSDF"]; vb.inputs["Base Color"].default_value = (0.45, 0.03, 0.03, 1); vb.inputs["Roughness"].default_value = 0.3
vb.inputs["Coat Weight"].default_value = 0.6; vb.inputs["Subsurface Weight"].default_value = 0.3; vb.inputs["Subsurface Radius"].default_value = (1, 0.2, 0.1)
vb.inputs["Subsurface Scale"].default_value = 0.2
vb.inputs["Emission Color"].default_value = (0.6, 0.05, 0.03, 1); vb.inputs["Emission Strength"].default_value = 0.25
nzv = N.new("ShaderNodeTexNoise"); nzv.inputs["Scale"].default_value = 1.2; nzv.inputs["Detail"].default_value = 8
tcv = N.new("ShaderNodeTexCoord"); Lk.new(tcv.outputs["Object"], nzv.inputs["Vector"])
bpv = N.new("ShaderNodeBump"); bpv.inputs["Strength"].default_value = 0.5; Lk.new(nzv.outputs["Fac"], bpv.inputs["Height"]); Lk.new(bpv.outputs[0], vb.inputs["Normal"])
vessel = cyl("vessel", 1.0, VL, tuple(VS), vessel_m, rot=(90, 0, 0), verts=64)
bpy.context.view_layer.objects.active = vessel
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.subdivide(number_cuts=40)
bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode="OBJECT")
dv = vessel.modifiers.new("d", "DISPLACE"); tv = bpy.data.textures.new("vd", "CLOUDS"); tv.noise_scale = 1.5; dv.texture = tv; dv.strength = 0.12
# eritrotsit: ikki tomoni botiq disk
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 0, -90))
rbc = bpy.context.object; rbc.name = "rbc_src"
for v in rbc.data.vertices:
    rr2 = v.co.x ** 2 + v.co.y ** 2
    v.co.z *= 0.18 + 0.32 * rr2
smooth(rbc)
rbc_m = mat("rbc", (0.6, 0.02, 0.02), 0.35, sss=0.5, coat=0.3)
rbc_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (1, 0.15, 0.1)
rbc_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.08
rbc.data.materials.append(rbc_m)
VR = [S["vessel_sugar"], S["vessel_pulse"], S["vessel_insulin"]]
V0, V1 = VR[0][0] - 2, VR[-1][1] + 2
for i in range(170):
    a = random.uniform(0, 2 * math.pi); r = 0.72 * math.sqrt(random.random())
    p = VS + Vector((r * math.cos(a), random.uniform(-VL / 2 + 4, VL / 2 - 12), r * math.sin(a)))
    o = inst(rbc, "rbc", tuple(p), random.uniform(0.15, 0.19))
    v = random.uniform(1.2, 2.2)
    o.rotation_euler = (random.uniform(0, 6.3), random.uniform(0, 6.3), 0)
    key(o, V0, loc=tuple(p), rot=[math.degrees(x) for x in o.rotation_euler])
    key(o, V1, loc=tuple(p + Vector((0, v * (V1 - V0) / 24 * 0.25, 0))),
        rot=[math.degrees(x) + random.uniform(-200, 200) for x in o.rotation_euler])
    interp(o)
# qand kristallari: 13-kadrda ko'payadi, 20-kadrda insulin ularni yo'q qiladi
crys_m = rim_mat("crystal", (1.0, 1.0, 1.0), 3.0, power=1.2, alpha_core=0.55)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, -95)); csrc = bpy.context.object; csrc.name = "crys_src"; csrc.data.materials.append(crys_m)
cr0 = S["vessel_sugar"][0]
crystals = []
for i in range(130):
    a = random.uniform(0, 2 * math.pi); r = 0.78 * math.sqrt(random.random())
    p = VS + Vector((r * math.cos(a), random.uniform(-VL / 2 + 6, VL / 2 - 12), r * math.sin(a)))
    s = random.uniform(0.035, 0.07)
    o = inst(csrc, "crystal", tuple(p), 0.0001)
    o.rotation_euler = (random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0, 6.3))
    appear = cr0 + int(60 * (i / 130) ** 0.7)
    key(o, 1, scale=0.0001); key(o, appear, scale=0.0001); key(o, appear + 4, scale=s)
    gone = random.randint(S["vessel_insulin"][0] + 6, S["vessel_insulin"][1] - 6)
    key(o, gone, scale=s); key(o, gone + 3, scale=0.0001)
    key(o, V0, loc=tuple(p)); key(o, V1, loc=tuple(p + Vector((0, 1.6 * (V1 - V0) / 24 * 0.25, 0))))
    interp(o, "LINEAR", "location")
    crystals.append(o)
ins_m = emission_mat("insulin", (1.0, 0.65, 0.12), 12.0)
isrc = sphere("ins_src", 1.0, (0, 0, -100), ins_m, sub=2)
i0, i1 = S["vessel_insulin"]
VCAM = {}       # tomir kameralari Y yo'li
for i in range(220):
    a = random.uniform(0, 2 * math.pi); r = 0.8 * math.sqrt(random.random())
    o = inst(isrc, "insulin", (0, 0, 0), random.uniform(0.018, 0.035))
    y0 = random.uniform(-14, -6); y1 = y0 + random.uniform(10, 18)
    key(o, i0 - 1, loc=tuple(VS + Vector((r * math.cos(a), y0, r * math.sin(a)))))
    key(o, i1 + 1, loc=tuple(VS + Vector((r * math.cos(a) * 0.8, y1, r * math.sin(a) * 0.8))))
    interp(o)
    vis(o, [(i0, i1)])
# qon bosimi: tomir urib kengayadi (16)
p0, p1 = S["vessel_pulse"]
key(vessel, 1, scale=1.0); key(vessel, p0, scale=1.0)
for f in range(p0, p1 + 1, 11):
    for ff, s in ((f, 1.0), (f + 3, 1.18), (f + 8, 1.03)):
        vessel.scale = (s, s, 1.0); vessel.keyframe_insert("scale", frame=ff)
vessel.scale = (1, 1, 1); vessel.keyframe_insert("scale", frame=p1 + 2)

# ======================================================================
# 8) MAKRO KO'Z (14, 15): qorachiq kengayadi
# ======================================================================
ES = Vector((0, -300, 1.0))
eyeM = E.build_eye("eyeM", tuple(ES))
eye_skin = bpy.data.materials.get("eyeM_lids_skin")
PUP = eyeM["ball"].data.materials[0].node_tree.nodes["PUPIL"]
e0, e1 = S["eye_dilate"]
key_value(PUP, 1, 0.12); key_value(PUP, e0 + 2, 0.12); key_value(PUP, e0 + 14, 0.36)
E.set_key(eyeM, "wide", 1, 0.0); E.set_key(eyeM, "wide", e0 + 2, 0.0); E.set_key(eyeM, "wide", e0 + 10, 0.8)

# ======================================================================
# 9) OSHQOZON OSTI BEZI MAKRO (18, 19): signal va insulin otilishi
# ======================================================================
PS = Vector((60, 300, 0))
backdrop("panc_bg", PS, 9.0, (0.12, 0.02, 0.02), (0.01, 0.0, 0.0), 1.0)
pm = bpy.data.materials.new("panc_macro"); pm.use_nodes = True; N = pm.node_tree.nodes; Lk = pm.node_tree.links
pb_ = N["Principled BSDF"]; pb_.inputs["Base Color"].default_value = (0.92, 0.68, 0.42, 1); pb_.inputs["Roughness"].default_value = 0.35
pb_.inputs["Subsurface Weight"].default_value = 0.6; pb_.inputs["Subsurface Radius"].default_value = (1, 0.4, 0.25); pb_.inputs["Subsurface Scale"].default_value = 0.15
pb_.inputs["Coat Weight"].default_value = 0.5
pb_.inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1)
PEM = pb_.inputs["Emission Strength"]
vn2 = N.new("ShaderNodeTexVoronoi"); vn2.inputs["Scale"].default_value = 3.0; bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = 0.9
tc2 = N.new("ShaderNodeTexCoord"); Lk.new(tc2.outputs["Object"], vn2.inputs["Vector"])
Lk.new(vn2.outputs["Distance"], bp2.inputs["Height"]); Lk.new(bp2.outputs[0], pb_.inputs["Normal"])
pmac = tube("panc_macro", [(*(PS + Vector(p)), r) for p, r in (((-2.6, 0, 0.1), 0.35), ((-1.2, 0.1, -0.05), 0.5),
                                                                 ((0.3, 0, 0.05), 0.62), ((1.6, -0.15, 0.25), 0.78), ((2.6, -0.3, 0.1), 0.6))], pm)
dmm = pmac.modifiers.new("lumps", "DISPLACE"); tt2 = bpy.data.textures.new("pm", "VORONOI"); tt2.noise_scale = 0.35; dmm.texture = tt2; dmm.strength = 0.3
sm_ = pmac.modifiers.new("sub", "SUBSURF"); sm_.levels = 1; sm_.render_levels = 2
# tomir bezga tegib o'tadi
vseg = cyl("panc_vessel", 0.45, 9, tuple(PS + Vector((0, 1.4, 1.1))), vessel_m, rot=(0, 90, 0), verts=48)
q0, q1 = S["panc_alarm"][0], S["panc_spray"][1]
PEM.default_value = 0.0; PEM.keyframe_insert("default_value", frame=1)
for f in range(q0, q1 + 1, 12):
    PEM.default_value = 2.5; PEM.keyframe_insert("default_value", frame=f)
    PEM.default_value = 0.2; PEM.keyframe_insert("default_value", frame=f + 6)
s0, s1 = S["panc_spray"]
for i in range(260):
    st0 = random.randint(s0 - 2, s1 - 6)
    a = random.uniform(-2.4, 2.4)
    p = PS + Vector((a, random.uniform(-0.2, 0.3), 0.55 + random.uniform(-0.1, 0.2)))
    d = Vector((random.uniform(-0.4, 0.4), random.uniform(0.3, 1.0), random.uniform(0.8, 1.6))).normalized() * random.uniform(3.5, 6.0)
    o = inst(isrc, "ins_spray", tuple(p), random.uniform(0.03, 0.06))
    key(o, st0, loc=tuple(p)); key(o, st0 + 14, loc=tuple(p + d))
    interp(o)
    vis(o, [(st0, min(st0 + 14, s1))])

# ======================================================================
# 10) KAMERALAR
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
    rnd = random.Random(seed); base = cam.location.copy()
    for f in range(f0, f1):
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)
CAMS = {}
def shot(name, a, b, target, lens, fstop=None, focus=None, clip=0.01, ease=True):
    """a -> b ga harakatlanuvchi kamera (kadr davomida)"""
    f0, f1 = S[name]
    c = camera("cam_" + name, tuple(a), target, lens, fstop, focus, clip); CAMS[name] = c
    key(c, f0, loc=tuple(a)); key(c, f1 + 1, loc=tuple(b))
    if not ease: interp(c, "LINEAR")
    return c
def lens_key(c, pairs):
    for f, l in pairs: c.data.lens = l; c.data.keyframe_insert("lens", frame=f)

# 1 ilgak: muzdek banka, pastdan tez yaqinlashish (orqada deraza nuri)
canT = empty("canT", tuple(CAN_T + Vector((0, 0, 0.01))))
c = shot("can_hook", CAN_T + Vector((-0.15, -0.55, -0.03)), CAN_T + Vector((-0.05, -0.27, 0.0)), canT, 40, 2.8, ease=False)
lens_key(c, [(1, 40), (24, 50)])
# 2 keng, past burchak: banka og'izga
liftT = empty("liftT", tuple(MEG + Vector((0, 0, 1.2))))
shot("lift_wide", MEG + Vector((0.55, -1.15, 0.35)), MEG + Vector((0.4, -0.95, 0.42)), liftT, 16, 5.6, focus=faceT)
# 3 yuzga yaqin
shot("drink_face", MEG + Vector((-0.2, -0.62, 1.55)), MEG + Vector((-0.12, -0.5, 1.58)), faceT, 55, 2.0)
# 4 rentgen: bosh va ko'krak, ichimlik qizilo'ngachdan tushadi
xT = empty("xT", (0, 0, 0)); key(xT, S["xray_drink"][0], loc=tuple(MEG + Vector((0.02, 0, 1.38)))); key(xT, S["xray_drink"][1], loc=tuple(MEG + Vector((0.04, 0, 1.18))))
key(xT, S["xray_fill"][0], loc=tuple(SC)); key(xT, S["xray_calm"][1], loc=tuple(SC))
key(xT, S["xray_panc"][0], loc=tuple(SC + Vector((0, 0, -0.02)))); key(xT, S["xray_panc"][1], loc=tuple(SC + Vector((-0.01, 0, -0.08))))
interp(xT, "CONSTANT")
shot("xray_drink", MEG + Vector((0.45, -0.6, 1.25)), MEG + Vector((0.35, -0.55, 1.15)), xT, 24, None)
# 5 oshqozon to'ladi: orbit
c = shot("xray_fill", SC + Vector((-0.4, -0.45, 0.05)), SC + Vector((0.25, -0.5, 0.0)), xT, 30, None)
key(c, (S["xray_fill"][0] + S["xray_fill"][1]) // 2, loc=tuple(SC + Vector((-0.1, -0.6, 0.03))))
# 6 kola stakani: past burchak, qand tushadi
gT = empty("gT", tuple(GS + Vector((0, 0, 0.11))))
shot("sugar_glass", GS + Vector((0.1, -0.5, 0.05)), GS + Vector((0.05, -0.36, 0.07)), gT, 45, 4.0, ease=False)
# 7 oshqozon xavf: tez yaqinlashish
shot("xray_alarm", SC + Vector((0.3, -0.7, 0.12)), SC + Vector((0.08, -0.3, 0.03)), xT, 35, None)
# 8 ko'ngil aynishi: past burchak, silkinish
nT = empty("nT", tuple(MEG + Vector((0, 0, 1.0))))
c = shot("nausea", MEG + Vector((-0.7, -1.2, 0.5)), MEG + Vector((-0.55, -1.0, 0.55)), nT, 20, 4.0, focus=faceT)
shake(c, S["nausea"][0] + 26, S["nausea"][1] + 1, 0.03, 3)
# 9 ichimlik ichida: yuqoriga suzish
iT = empty("iT", tuple(IS + CUBE_P[0])); key(iT, S["inside"][0], loc=tuple(IS + CUBE_P[0] + Vector((0, 0, 0.6)))); key(iT, S["inside"][1], loc=tuple(IS + CUBE_P[0]))
shot("inside", IS + Vector((0.6, -2.4, -0.8)), IS + Vector((0.3, -1.9, 0.2)), iT, 28, 2.8)
# 10 kislota: kub atrofida aylanish
c = shot("acid", IS + CUBE_P[0] + Vector((1.7, -1.6, 0.4)), IS + CUBE_P[0] + Vector((-1.3, -1.6, 0.2)), cubes_in[0], 30, 4.0)
key(c, (S["acid"][0] + S["acid"][1]) // 2, loc=tuple(IS + CUBE_P[0] + Vector((0.2, -2.2, 0.5))))
# 11 oshqozon tinchlanadi: sekin orbit
shot("xray_calm", SC + Vector((-0.3, -0.35, 0.15)), SC + Vector((0.1, -0.42, 0.08)), xT, 32, None)
# 12 yengil tortish: yuzga yaqin
shot("relief_face", MEG + Vector((0.25, -0.75, 1.5)), MEG + Vector((0.18, -0.55, 1.56)), faceT, 60, 2.0)
# 13 tomir ichida uchish
vT = empty("vT", tuple(VS));
def vessel_cam(name, y0, y1, off0, off1, lens):
    f0, f1 = S[name]
    t = empty(name + "_t", (0, 0, 0)); key(t, f0, loc=tuple(VS + Vector((0, y0 + 4, 0)))); key(t, f1 + 1, loc=tuple(VS + Vector((0, y1 + 4, 0)))); interp(t)
    c = camera("cam_" + name, (0, 0, 0), t, lens, None); CAMS[name] = c
    key(c, f0, loc=tuple(VS + Vector((off0[0], y0, off0[1])))); key(c, f1 + 1, loc=tuple(VS + Vector((off1[0], y1, off1[1])))); interp(c)
    return c
vessel_cam("vessel_sugar", -16, -9, (0.25, -0.2), (-0.2, 0.1), 18)
c = vessel_cam("vessel_pulse", -4, -1.5, (-0.3, 0.25), (0.2, 0.3), 18)
shake(c, S["vessel_pulse"][0], S["vessel_pulse"][1] + 1, 0.05, 5)
vessel_cam("vessel_insulin", -12, -5, (0.2, 0.3), (-0.15, -0.2), 20)
# 14-15 makro ko'z
eyeT = empty("eyeT", tuple(ES + Vector((0, -0.012, 0))))
shot("eye_in", ES + Vector((0.01, -0.12, 0.006)), ES + Vector((0.004, -0.095, 0.002)), eyeT, 50, 10.0, clip=0.001)
c = shot("eye_dilate", ES + Vector((0.002, -0.085, 0.0)), ES + Vector((0.0, -0.05, 0.0)), eyeT, 50, 14.0, clip=0.001)
lens_key(c, [(S["eye_dilate"][0], 50), (S["eye_dilate"][0] + 6, 70)])
# 17 bez vahimasi: rentgen torso, tez itarish
shot("xray_panc", SC + Vector((0.35, -0.75, -0.2)), SC + Vector((0.05, -0.28, -0.1)), xT, 30, None)
# 18-19 makro bez
pT = empty("pT", tuple(PS + Vector((0.3, 0, 0.3))))
c = shot("panc_alarm", PS + Vector((-3.0, -3.0, 0.6)), PS + Vector((0.5, -3.4, 1.3)), pT, 24, 4.0)
c = shot("panc_spray", PS + Vector((1.6, -3.0, -0.2)), PS + Vector((0.8, -2.2, 0.4)), pT, 20, 5.6)
# 21 boshi aylanadi: keng, past burchak, egilgan kamera
dT = empty("dT", tuple(MEG + Vector((0, 0, 1.1))))
c = shot("dizzy_wide", MEG + Vector((0.9, -1.6, 0.25)), MEG + Vector((0.7, -1.3, 0.3)), dT, 16, 5.6, focus=faceT)
# 22 asabiy: yuzga yaqin
shot("annoyed_face", MEG + Vector((-0.3, -0.55, 1.62)), MEG + Vector((-0.22, -0.48, 1.6)), faceT, 50, 2.0)
# 23 yangi bankaga qo'l cho'zadi (oldinda banka, orqada Megan)
rT = empty("rT", tuple(CAN_T.lerp(REACH + Vector((0, 0, 1.25)), 0.62) + Vector((-0.07, 0, 0))))
shot("reach", CAN_T + Vector((0.02, 0.32, -0.02)), CAN_T + Vector((0.0, 0.24, -0.01)), rT, 18, 2.8, focus=can_table)
# 24 banka makrosiga crash zoom
c = shot("can_end", CAN_T + Vector((0.05, 0.42, 0.04)), CAN_T + Vector((0.01, 0.13, 0.01)), canT, 30, 3.2, ease=False)
lens_key(c, [(S["can_end"][0], 30), (S["can_end"][0] + 8, 50)])
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["can_hook"]

# ======================================================================
# 11) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; env = N.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tcw = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(120))
w.node_tree.links.new(tcw.outputs["Generated"], mp.inputs[0]); w.node_tree.links.new(mp.outputs[0], env.inputs[0])
w.node_tree.links.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 0.8
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); link(sun)
sun.data.energy = 2.0; sun.data.angle = R(2); sun.data.color = (1.0, 0.93, 0.82); sun.rotation_euler = (R(55), 0, R(160))
def area(name, loc, rot, energy, size, col=(1, 0.9, 0.78), target=None, keys=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); link(l)
    l.data.energy = energy; l.data.size = size; l.data.color = col; l.location = loc; l.rotation_euler = [R(a) for a in rot]
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
area("ceiling_light", (0, 2.6, 2.65), (0, 0, 0), 120, 1.2)
area("window_key", (0.0, 4.7, 1.7), (-80, 0, 0), 220, 1.6, (0.95, 0.97, 1.0))
area("face_key", tuple(MEG + Vector((-0.8, -1.0, 1.9))), (0, 0, 0), 70, 0.9, (1.0, 0.88, 0.75), target=faceT)
area("face_rim", tuple(MEG + Vector((0.7, 0.9, 1.9))), (0, 0, 0), 60, 0.6, (0.75, 0.85, 1.0), target=faceT)
area("can_key", tuple(CAN_T + Vector((-0.35, -0.2, 0.35))), (0, 0, 0), 12, 0.25, (1, 0.95, 0.9), target=canT,
     keys=on(rng("can_hook", "reach", "can_end"), 12))
area("can_rim", tuple(CAN_T + Vector((0.25, 0.35, 0.15))), (0, 0, 0), 10, 0.2, (0.7, 0.85, 1.0), target=canT,
     keys=on(rng("can_hook", "reach", "can_end"), 10))
# sovuq yashil-ko'k ohang (qand tushib ketganda)
area("dizzy_rim", tuple(MEG + Vector((-0.8, 0.8, 1.8))), (0, 0, 0), 90, 0.8, (0.4, 0.6, 1.0), target=faceT,
     keys=on(rng("dizzy_wide", "annoyed_face"), 90))
area("nausea_rim", tuple(MEG + Vector((0.9, 0.6, 1.6))), (0, 0, 0), 110, 0.6, (0.5, 1.0, 0.3), target=faceT,
     keys=on(rng("nausea"), 110))
# stakan studiyasi
area("glass_back", tuple(GS + Vector((0, 0.35, 0.18))), (0, 0, 0), 70, 0.25, (1.0, 0.75, 0.45), target=gT)
area("glass_key", tuple(GS + Vector((-0.3, -0.2, 0.35))), (0, 0, 0), 45, 0.3, (1, 0.96, 0.92), target=gT)
area("glass_rim", tuple(GS + Vector((0.3, 0.05, 0.12))), (0, 0, 0), 30, 0.1, (0.7, 0.85, 1.0), target=gT)
# ichimlik ichi: yuqoridan yorug'lik
area("inside_top", tuple(IS + Vector((0, 1.0, 4.0))), (0, 0, 0), 900, 4, (1.0, 0.6, 0.3), target=iT)
area("inside_fill", tuple(IS + Vector((-2, -3, 0))), (0, 0, 0), 200, 2, (1.0, 0.45, 0.2), target=iT)
# tomir: kamera bilan yuruvchi nur
for n in ("vessel_sugar", "vessel_pulse", "vessel_insulin"):
    pl = bpy.data.objects.new(n + "_lamp", bpy.data.lights.new(n + "_lamp", "POINT")); link(pl, CAMS[n])
    pl.data.energy = 140; pl.data.color = (1.0, 0.85, 0.75); pl.data.shadow_soft_size = 0.3; pl.location = (0.1, 0.15, 0.0)
    pl.data.energy = 0; pl.data.keyframe_insert("energy", frame=1)
    pl.data.energy = 140; pl.data.keyframe_insert("energy", frame=S[n][0]); pl.data.energy = 0; pl.data.keyframe_insert("energy", frame=S[n][1] + 1)
    interp(pl.data, "CONSTANT")
# makro ko'z
eye_rng = rng("eye_in", "eye_dilate")
area("eye_key", tuple(ES + Vector((-0.09, -0.14, 0.11))), (0, 0, 0), 1.6, 0.09, (1, 0.95, 0.9), target=eyeM["root"], keys=on(eye_rng, 1.6))
area("eye_fill", tuple(ES + Vector((0.12, -0.1, -0.03))), (0, 0, 0), 0.5, 0.12, (0.85, 0.9, 1.0), target=eyeM["root"], keys=on(eye_rng, 0.5))
area("eye_red", tuple(ES + Vector((0.09, 0.0, 0.05))), (0, 0, 0), 1.0, 0.05, (1.0, 0.2, 0.1), target=eyeM["root"], keys=on(rng("eye_dilate"), 1.2))
# bez makro: qizil signal
area("panc_key", tuple(PS + Vector((-2, -3, 3))), (0, 0, 0), 600, 2.5, (1.0, 0.85, 0.75), target=pT)
pr = area("panc_red", tuple(PS + Vector((2.5, -1, 2))), (0, 0, 0), 0, 2.0, (1.0, 0.08, 0.04), target=pT)
for f in range(q0, q1 + 1, 12):
    pr.data.energy = 1500; pr.data.keyframe_insert("energy", frame=f); pr.data.energy = 150; pr.data.keyframe_insert("energy", frame=f + 6)

# ======================================================================
# 12) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 12)); sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 5; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
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
