# Phineas Gage (1848) — Zack D. Films uslubida 55 s video. Asos: zack_test/scene3.py + mixchar.py
# Ishga tushirish: OUT=/tmp/claude-0/frames/ SAMPLES=12 /tmp/claude-0/bvenv/bin/python -I zack_test/gage/gage.py --render
# Sinov: FRAMES=100,330,520,700,960,1290 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from mathutils import Vector, Matrix, Quaternion
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24
F = dict(s1=1, s2=203, s3=369, s4=579, s5=846, s6a=1047, s6b=1179, end=1325)   # ovoz vaqtlariga mos
sc.frame_start, sc.frame_end = 1, F["end"]
SPARK, BOOM = 313, 344            # "uchqun" 13.0 s, "portlash" 14.3 s

# ---------------- yordamchilar ----------------
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

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
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def emission_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    e = N.new("ShaderNodeEmission"); o = N.new("ShaderNodeOutputMaterial")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    L.new(e.outputs[0], o.inputs[0]); return m, e

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
    r = img("rough.jpg", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def box(name, size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def import_gltf(path, loc, rot_z=0.0, scale=1.0, rot_x=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler = (R(rot_x), 0, R(rot_z)); root.scale = (scale,) * 3
    return root, new

def ph_model(n, loc, rz=0, s=1.0, rx=0):
    return import_gltf(f"{PH}{n}/{n}.gltf", loc, rz, s, rx)[0]

def look_quat(d):
    return Vector((0, 1, 0)).rotation_difference(Vector(d).normalized())

# ================= MUHIT: temir yo'l qurilishi, qoyali o'yiq =================
M_ground = pbr("ph_ground", "rocky_terrain_02", 0.35)
M_dirt = pbr("ph_dirt", "dirt", 0.5)
M_rock = pbr("ph_rockface", "rock_face", 0.25, tint=(0.95, 0.85, 0.72))
M_plank = pbr("ph_planks", "weathered_planks", 0.8)
M_rail = mat("rail_iron", (0.22, 0.18, 0.15), 0.45, metal=0.9)
M_iron = mat("tamping_iron", (0.32, 0.30, 0.28), 0.32, metal=1.0)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); g = bpy.context.object; g.name = "ground"
g.scale = (70, 40, 1); bpy.ops.object.transform_apply(scale=True); g.data.materials.append(M_ground)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-6, -1.0, 0.004)); bed = bpy.context.object; bed.name = "railbed"
bed.scale = (40, 3.4, 1); bpy.ops.object.transform_apply(scale=True); bed.data.materials.append(M_dirt)

def cliff(name, y, rz, height=5.5, disp=1.3):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=36, size=1, location=(0, y, height / 2 - 0.6))
    o = bpy.context.object; o.name = name; o.scale = (70, height, 1); o.rotation_euler = (R(90), 0, R(rz))
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    for p in o.data.polygons: p.use_smooth = True
    for i, (ns, st) in enumerate(((2.2, disp), (0.6, disp * 0.35))):
        t = bpy.data.textures.new(f"{name}_t{i}", "CLOUDS"); t.noise_scale = ns; t.noise_depth = 3
        d = o.modifiers.new(f"disp{i}", "DISPLACE"); d.texture = t; d.strength = st; d.mid_level = 0.5
    o.data.materials.append(M_rock); return o
cliff("cliff_back", 5.6, 0)
cliff("cliff_front", -8.5, 180)

# shpallar va relslar (qurilish shu yerda tugaydi: x<1)
for i in range(60):
    x = 0.6 - i * 0.62
    sl = box(f"sleeper{i}", (0.22, 2.5, 0.14), (x, -1.0, 0.05), M_plank, rot=(0, 0, random.uniform(-2, 2)))
for y in (-1.0 - 0.72, -1.0 + 0.72):
    box("rail", (37.0, 0.07, 0.13), (-17.8, y, 0.18), M_rail)
for i in range(4):                         # hali yotqizilmagan shpallar uyumi
    box(f"pile{i}", (2.5, 0.22, 0.14), (-3.5, -3.4 + (i % 2) * 0.05, 0.07 + i * 0.145), M_plank, rot=(0, 0, 90 + random.uniform(-4, 4)))

ph_model("wooden_barrels_01", (1.2, 2.7, 0), 20)
ph_model("wooden_crate_01", (7.6, 2.6, 0), 15, 1.0)
ph_model("wooden_crate_01", (7.9, 2.0, 0), -20, 0.8)
ph_model("wooden_lantern_01", (7.6, 2.6, 0.55), 0)
ph_model("wooden_bucket_01", (3.1, 1.9, 0), 0)
ph_model("sledgehammer_01", (5.1, 1.6, 0.02), 70, 1.0, 0)
big_rock = ph_model("boulder_01", (2.4, 3.6, -0.2), 30, 1.6)
ph_model("namaqualand_boulder_02", (8.8, 0.8, -0.1), 120, 1.4)
ph_model("boulder_01", (-6.5, 3.4, -0.3), -50, 2.2)
ph_model("namaqualand_boulder_02", (-3.0, -4.6, -0.2), 40, 1.8)
ph_model("wooden_barrels_01", (-5.4, 2.6, 0), -40)
ph_model("wooden_crate_01", (-1.8, 2.8, 0), 30, 1.1)
# portlatiladigan qoya: tuynuk shu tosh ustida
G = Vector((4.0, 1.2, 0.0))                 # Gage S1-S3 da shu yerda turadi (yuzi -Y ga)
HOLE = G + Vector((0.08, -0.64, 0.0))
slab = ph_model("namaqualand_boulder_02", tuple(HOLE + Vector((0.05, -0.45, -0.62))), 10, 0.75)
bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.05, location=tuple(HOLE + Vector((0, 0, 0.01))))
hole = bpy.context.object; hole.name = "drillhole"; hole.data.materials.append(mat("holeblack", (0.01, 0.01, 0.01), 1.0))

# ================= QAHRAMONLAR =================
groot, gage, gmesh = mc.load_character("gage", "Pete.fbx")
croot, cow, cmesh = mc.load_character("cow", "Peasant_Man.fbx")
droot, doc, dmesh = mc.load_character("doc", "Josh.fbx")
croot.scale = (0.9,) * 3
for o in [o for o in gmesh if "Helmet" in o.name]:
    gmesh.remove(o); bpy.data.objects.remove(o, do_unlink=True)          # 1848: kaska yo'q

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
                        n.inputs["Roughness"].default_value = 0.65
                    n.inputs["Coat Weight"].default_value = 0.0
soften(gmesh + cmesh + dmesh)

# to'q sariq zamonaviy jiletni eski charm jiletga aylantirish
vest = next(o for o in gmesh if "Vest" in o.name)
vm = vest.data.materials[0].copy(); vm.name = "Ch17_vest"; vest.data.materials[0] = vm
N = vm.node_tree.nodes; L = vm.node_tree.links; bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
lk = bsdf.inputs["Base Color"].links[0]; src = lk.from_socket; L.remove(lk)
hs_node = N.new("ShaderNodeHueSaturation"); hs_node.inputs["Saturation"].default_value = 0.25; hs_node.inputs["Value"].default_value = 0.35
L.new(src, hs_node.inputs["Color"]); mt = N.new("ShaderNodeMix"); mt.data_type = "RGBA"; mt.blend_type = "MULTIPLY"
mt.inputs["Factor"].default_value = 1.0; mt.inputs[7].default_value = (0.55, 0.36, 0.22, 1)
L.new(hs_node.outputs[0], mt.inputs[6]); L.new(mt.outputs[2], bsdf.inputs["Base Color"])

# ---- rentgen (S4): har bir material uchun Mix(asl, rentgen), omil kadrlarga qarab ----
XRAY_ON = [(F["s4"], F["s5"] - 1)]
def add_xray(meshes):
    done = set()
    for o in meshes:
        for m in o.data.materials:
            if not m or m.name in done: continue
            done.add(m.name); N = m.node_tree.nodes; L = m.node_tree.links
            out = next(n for n in N if n.type == "OUTPUT_MATERIAL"); lk = out.inputs["Surface"].links[0]; orig = lk.from_socket
            L.remove(lk)
            lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
            cr = N.new("ShaderNodeMath"); cr.operation = "POWER"; cr.inputs[1].default_value = 1.6
            L.new(lw.outputs["Facing"], cr.inputs[0])
            em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.65, 1.0, 1); em.inputs["Strength"].default_value = 2.5
            tr = N.new("ShaderNodeBsdfTransparent")
            xm = N.new("ShaderNodeMixShader"); L.new(cr.outputs[0], xm.inputs[0]); L.new(tr.outputs[0], xm.inputs[1]); L.new(em.outputs[0], xm.inputs[2])
            mix = N.new("ShaderNodeMixShader"); mix.name = "XRAY_MIX"
            L.new(orig, mix.inputs[1]); L.new(xm.outputs[0], mix.inputs[2]); L.new(mix.outputs[0], out.inputs["Surface"])
            fac = mix.inputs[0]
            for f, v in ((1, 0.0), (XRAY_ON[0][0] - 1, 0.0), (XRAY_ON[0][0], 1.0), (XRAY_ON[0][1], 1.0), (XRAY_ON[0][1] + 1, 0.0)):
                fac.default_value = v; fac.keyframe_insert("default_value", frame=f)
            for fc in mc._fcurves(m.node_tree.animation_data.action):
                for k in fc.keyframe_points: k.interpolation = "CONSTANT"
add_xray(gmesh)

A = lambda f, inplace=True: mc.load_action(f, inplace)
def at(root, f, loc, rz):
    root.location = loc; root.rotation_euler = (0, 0, R(rz))
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)

# ---------- GAGE ----------
XR = Vector((60.0, 0.0, 0.0))               # rentgen kadri uchun alohida joy (qorong'i)
S5A, S5B = Vector((2.0, 0.85, 0)), Vector((-0.35, 0.75, 0))
S6G, S6C = Vector((-4.0, 1.5, 0)), Vector((-2.85, 1.5, 0))
at(groot, 1, tuple(G), 0)
at(groot, F["s4"], tuple(XR), 0)
at(groot, F["s5"], tuple(S5A), -90)
WALK0, WALK1 = 930, 1046
at(groot, WALK0, tuple(S5A), -90); at(groot, WALK1, tuple(S5B), -90)
at(groot, F["s6a"], tuple(S6G), 90)
for fc in mc._fcurves(groot.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if WALK0 <= k.co.x < WALK1 else "CONSTANT"

DIG_START = -7                               # urish (tayoq tuynuk tubiga tegishi) SPARK kadriga to'g'ri keladi
mc.add_strip(gage, A("Digging.fbx"), DIG_START, repeat=3.0)
s3 = mc.add_strip(gage, A("Idle_14.fbx"), F["s3"], speed=0.3, blend=0)        # tik turgan, sekinlashgan
mc.add_strip(gage, A("Big_Hit_To_Head.fbx"), 548, speed=0.25, blend=10)
mc.add_strip(gage, A("Breathing_Idle.fbx"), F["s4"], repeat=2.0, blend=0)
mc.add_strip(gage, A("Getting_Up.fbx"), F["s5"], speed=0.9, blend=0)
mc.add_strip(gage, A("Injured_Walk.fbx"), WALK0 - 4, repeat=3.2, speed=1.0, blend=6)
mc.add_strip(gage, A("Breathing_Idle.fbx"), F["s6a"], blend=0)
mc.add_strip(gage, A("Annoyed_Head_Shake.fbx"), 1092, speed=0.8, blend=8)
mc.add_strip(gage, A("Idle_14.fbx"), F["s6b"], blend=0)
mc.add_strip(gage, A("Angry_Gesture.fbx"), 1236, speed=1.1, blend=5)
mc.add_strip(gage, A("Angry_Point.fbx"), 1290, speed=1.0, blend=5)

# ---------- HAMKASB (Peasant Man) ----------
at(croot, 1, (6.7, 0.5, 0), -110)
at(croot, F["s6a"], tuple(S6C), -90)
interp(croot, "CONSTANT")
mc.add_strip(cow, A("Look_Around.fbx"), 1, repeat=3.0)
mc.add_strip(cow, A("Terrified.fbx"), BOOM + 2, blend=3)
mc.add_strip(cow, A("Idle_14.fbx"), F["s6a"], blend=0)
mc.add_strip(cow, A("Agreeing.fbx"), F["s6b"] + 6, blend=6)
mc.add_strip(cow, A("Walk_Backwards.fbx"), 1262, speed=1.2, blend=5)
vis(croot, [(1, 845), (F["s6a"], F["end"])])
# ---------- SHIFOKOR (Josh) ----------
at(droot, 1, (-1.55, 0.75, 0), 90); interp(droot, "CONSTANT")
mc.add_strip(doc, A("Idle_14.fbx"), 1, repeat=6.0)
vis(droot, [(F["s5"], F["s6a"] - 1)])

# Gage sochi rentgen kadrida yashiriladi
for o in gmesh:
    if any(k in o.name for k in ("Hair", "Eyelashes")): vis(o, [(1, F["s4"] - 1), (F["s5"], F["end"])], False)

# ================= TEMIR TAYOQ =================
def make_rod(name):
    """uchi (0,0,0) da, tanasi -Y bo'ylab 1.09 m (asl tayoq: 109 sm, 3.2 sm, bir uchi o'tkir)."""
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.016, radius2=0.003, depth=0.30, location=(0, -0.15, 0), rotation=(R(-90), 0, 0))
    a = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.016, depth=0.79, location=(0, -0.30 - 0.395, 0), rotation=(R(90), 0, 0))
    b = bpy.context.object
    bpy.ops.object.select_all(action="DESELECT")
    a.select_set(True); b.select_set(True); bpy.context.view_layer.objects.active = a; bpy.ops.object.join()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)     # uchi = origin, tanasi -Y
    a.name = name; a.data.materials.append(M_iron)
    for p in a.data.polygons: p.use_smooth = True
    bv = a.modifiers.new("bev", "BEVEL"); bv.width = 0.003; bv.limit_method = "ANGLE"
    return a

# qo'ldagi tayoq (S1-S2): o'ng qo'ldan chap qo'l tomon, pastga; uchi tuynukda
rod_hand = make_rod("rod_hand")
bpy.ops.object.select_all(action="DESELECT")
rh = empty("rod_hand_pivot")
c = rh.constraints.new("COPY_LOCATION"); c.target = gage; c.subtarget = "mixamorig:RightHand"
hole_t = empty("hole_target", tuple(HOLE + Vector((0, 0, -0.1))))
d = rh.constraints.new("DAMPED_TRACK"); d.target = hole_t; d.track_axis = "TRACK_Y"      # o'ng qo'ldan tuynuk tomon
rod_hand.parent = rh; rod_hand.location = (0, float(os.environ.get("ROD_OFF", 1.03)), 0)       # uchi o'ng qo'ldan 1.12 m pastda
rod_hand.rotation_euler = (0, 0, 0)
vis(rod_hand, [(1, F["s3"] - 1)])
if os.environ.get("PROBE"):
    for f in range(1, 369, 3):
        sc.frame_set(f); print("TIP", f, tuple(round(x, 3) for x in rod_hand.matrix_world.translation))
    sys.exit()

# bosh fazosi: Gage boshiga yopishgan, X=chap, Y=tepa, Z=old (metrda; T-pozada tekshirilgan)
head = empty("headspace")
c = head.constraints.new("CHILD_OF"); c.target = gage; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False
c.inverse_matrix = Matrix.Identity(4)
CHEEK = Vector((0.042, 0.06, 0.085)); TOP = Vector((0.006, 0.215, 0.06))
DIRH = (TOP - CHEEK).normalized()
rod_fly = make_rod("rod_fly"); rod_fly.parent = head
rod_fly.rotation_mode = "QUATERNION"; rod_fly.rotation_quaternion = look_quat(DIRH)
for f, p in ((F["s3"], CHEEK - DIRH * 1.25), (478, CHEEK), (560, TOP + DIRH * 0.06), (F["s4"] - 1, TOP + DIRH * 1.6)):
    rod_fly.location = p; rod_fly.keyframe_insert("location", frame=f)
fcs = [fc for fc in fcurves(rod_fly) if fc.data_path == "location"]
for fc in fcs:
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
vis(rod_fly, [(F["s3"], F["s4"] - 1)])

# qon tomchilari va suyak parchalari (chiqish nuqtasida, sekinlashgan)
M_blood = mat("blood", (0.18, 0.005, 0.005), 0.15)
for i in range(16):
    dr = sphere(f"drop{i}", random.uniform(0.004, 0.009), (0, 0, 0), M_blood, sub=2, parent=head)
    v = (DIRH + Vector((random.uniform(-.5, .5), random.uniform(-.2, .4), random.uniform(-.5, .5)))).normalized() * random.uniform(0.25, 0.6)
    t0 = 552 + random.randint(0, 10)
    for f in (F["s3"], t0 - 1):
        dr.location = TOP; dr.keyframe_insert("location", frame=f)
    for j in range(1, 6):
        ff = t0 + j * 4; tt = j * 4 / 24 * 0.35
        dr.location = TOP + v * tt + Vector((0, -0.4 * tt * tt, 0)); dr.keyframe_insert("location", frame=ff)
    vis(dr, [(t0, F["s4"] - 1)])

# ================= UCHQUN VA PORTLASH (S2) =================
sc.frame_set(SPARK); bpy.context.view_layer.update()
TIP = rod_hand.matrix_world.translation.copy()
print("TIP@SPARK", tuple(round(x, 3) for x in TIP), "HOLE", tuple(HOLE))
M_spark, _ = emission_mat("spark", (1.0, 0.55, 0.15), 60)
for i in range(36):
    s = sphere(f"spark{i}", 0.004, tuple(TIP), M_spark, scale=(1, 1, 4), sub=1)
    v = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.3, 1.6))).normalized() * random.uniform(1.2, 3.0)
    t0 = SPARK + random.randint(0, 3)
    s.rotation_mode = "QUATERNION"
    for j in range(0, 7):
        tt = j / 24; p = TIP + v * tt + Vector((0, 0, -4.9 * tt * tt))
        s.location = p; s.keyframe_insert("location", frame=t0 + j)
        vel = v + Vector((0, 0, -9.8 * tt)); s.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(vel.normalized())
        s.keyframe_insert("rotation_quaternion", frame=t0 + j)
    vis(s, [(t0, t0 + random.randint(4, 7))])
spl = bpy.data.objects.new("spark_light", bpy.data.lights.new("spark_light", "POINT")); sc.collection.objects.link(spl)
spl.location = TIP + Vector((0, 0, 0.05)); spl.data.color = (1, 0.6, 0.25); spl.data.shadow_soft_size = 0.02
for f, e in ((1, 0), (SPARK - 1, 0), (SPARK, 60), (SPARK + 3, 25), (SPARK + 7, 0)):
    spl.data.energy = e; spl.data.keyframe_insert("energy", frame=f)

# olov shari: shovqinli emissiya, tez kengayadi, keyin tutunga aylanadi
fb = sphere("fireball", 1.0, tuple(HOLE + Vector((0, 0, 0.05))), mat("fb_tmp", (1, 1, 1)), sub=5)
fbm = bpy.data.materials.new("fireball"); fbm.use_nodes = True; N = fbm.node_tree.nodes; L = fbm.node_tree.links
for n in list(N): N.remove(n)
out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 8; L.new(tc.outputs["Object"], nz.inputs["Vector"])
ramp = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (0.6, 0.08, 0.0, 1)
ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (1.0, 0.85, 0.4, 1)
em = N.new("ShaderNodeEmission"); L.new(ramp.outputs[0], em.inputs["Color"]); em.inputs["Strength"].default_value = 0
smoke = N.new("ShaderNodeBsdfPrincipled"); smoke.inputs["Base Color"].default_value = (0.12, 0.11, 0.1, 1); smoke.inputs["Roughness"].default_value = 1
mx = N.new("ShaderNodeMixShader"); L.new(smoke.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
fb.data.materials.clear(); fb.data.materials.append(fbm)
dsp = fb.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("fbn", "CLOUDS"); t.noise_scale = 0.35; dsp.texture = t; dsp.strength = 0.45
for f, s, e, m in ((BOOM - 1, 0.02, 0, 1), (BOOM, 0.12, 14, 1), (BOOM + 4, 0.7, 10, 1), (BOOM + 10, 1.3, 4, 0.7), (BOOM + 24, 2.2, 0, 0.0)):
    fb.scale = (s, s, s * 0.8); fb.keyframe_insert("scale", frame=f)
    em.inputs["Strength"].default_value = e; em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    mx.inputs[0].default_value = m; mx.inputs[0].keyframe_insert("default_value", frame=f)
vis(fb, [(BOOM, F["s3"] - 1)])
bl = bpy.data.objects.new("boom_light", bpy.data.lights.new("boom_light", "POINT")); sc.collection.objects.link(bl)
bl.location = HOLE + Vector((0, -0.3, 0.6)); bl.data.color = (1, 0.55, 0.2); bl.data.shadow_soft_size = 0.5
for f, e in ((1, 0), (BOOM - 1, 0), (BOOM + 1, 9000), (BOOM + 8, 2500), (BOOM + 22, 0)):
    bl.data.energy = e; bl.data.keyframe_insert("energy", frame=f)

# chang va tosh bo'laklari (portlashdan keyin, S3 davomida sekin uchadi)
M_dust = mat("dust", (0.45, 0.4, 0.33), 1.0)
for i in range(40):
    r0 = random.uniform(0.01, 0.035)
    s = sphere(f"chip{i}", r0, tuple(HOLE), M_ground if i % 3 else M_dust, scale=(1, random.uniform(.5, 1), random.uniform(.5, 1)), sub=1)
    s.modifiers.new("d", "DISPLACE").strength = 0.0
    v = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.8, 2.5))).normalized() * random.uniform(2, 5)
    # S2 da tez (real vaqt), S3 da 0.12x sekin
    pts = []
    for f in range(BOOM, F["s4"], 6):
        tt = (min(f, F["s3"]) - BOOM) / 24 + max(0, f - F["s3"]) / 24 * 0.12
        p = HOLE + v * tt + Vector((0, 0, -4.9 * tt * tt)); p.z = max(p.z, 0.02)
        s.location = p; s.keyframe_insert("location", frame=f)
        s.rotation_euler = (tt * 9 + i, tt * 7, tt * 5); s.keyframe_insert("rotation_euler", frame=f)
    vis(s, [(BOOM, F["s4"] - 1)])

# ================= MIYA (S4, rentgen) =================
M_brain = bpy.data.materials.new("brain"); M_brain.use_nodes = True
N = M_brain.node_tree.nodes; L = M_brain.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.85, 0.45, 0.5, 1); b.inputs["Roughness"].default_value = 0.35
b.inputs["Subsurface Weight"].default_value = 0.2
b.inputs["Emission Color"].default_value = (0.9, 0.35, 0.45, 1); b.inputs["Emission Strength"].default_value = 0.6
wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 9; wv.inputs["Distortion"].default_value = 12; wv.inputs["Detail"].default_value = 3
tcb = N.new("ShaderNodeTexCoord"); L.new(tcb.outputs["Object"], wv.inputs["Vector"])
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.9; bp.inputs["Distance"].default_value = 0.01
L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
brain = empty("brain_grp", (0, 0, 0), head)
for sx in (-1, 1):
    hemi = sphere("hemi", 1.0, (sx * 0.029, 0.112, 0.035), M_brain, scale=(0.028, 0.048, 0.07), sub=4, parent=brain)
    d = hemi.modifiers.new("d", "DISPLACE"); tt = bpy.data.textures.new("gyri", "CLOUDS"); tt.noise_scale = 0.012; d.texture = tt; d.strength = 0.004
sphere("cerebellum", 1.0, (0, 0.07, -0.015), M_brain, scale=(0.04, 0.022, 0.026), sub=3, parent=brain)
M_stem = bpy.data.materials.new("stem"); M_stem.use_nodes = True; bs = M_stem.node_tree.nodes["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.8, 0.5, 0.5, 1); bs.inputs["Emission Color"].default_value = (0.1, 1.0, 0.3, 1)
es = bs.inputs["Emission Strength"]
for f, v in ((1, 0.0), (735, 0.0), (750, 9.0), (765, 4.0), (780, 9.0), (795, 4.0), (810, 9.0), (845, 9.0)):
    es.default_value = v; es.keyframe_insert("default_value", frame=f)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.013, depth=0.11, location=(0, 0.04, 0.01), rotation=(R(-80), 0, 0))
stem = bpy.context.object; stem.name = "brainstem"; stem.data.materials.append(M_stem); stem.parent = brain
for p in stem.data.polygons: p.use_smooth = True
# tayoq yo'li (qizil) va shikastlangan peshona qismi
M_path, e_path = emission_mat("rodpath", (1.0, 0.08, 0.04), 0)
for f, v in ((1, 0), (600, 0), (618, 14), (845, 14)):
    e_path.inputs["Strength"].default_value = v; e_path.inputs["Strength"].keyframe_insert("default_value", frame=f)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0165, depth=1.0, location=(0, 0, 0))
ghost = bpy.context.object; ghost.name = "rodpath"; ghost.data.materials.append(M_path); ghost.parent = head
mid = (CHEEK + TOP) / 2; ghost.location = mid; ghost.rotation_mode = "QUATERNION"
ghost.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(DIRH)
ln = (TOP - CHEEK).length + 0.08
for f, s in ((600, 0.001), (630, ln)):
    ghost.scale = (1, 1, s); ghost.keyframe_insert("scale", frame=f)
M_dmg, e_dmg = emission_mat("damage", (1.0, 0.15, 0.05), 0)
for f, v in ((1, 0), (625, 0), (640, 3), (700, 1.5), (720, 3), (845, 3)):
    e_dmg.inputs["Strength"].default_value = v; e_dmg.inputs["Strength"].keyframe_insert("default_value", frame=f)
dmg = sphere("damage", 1.0, (0.026, 0.128, 0.075), M_dmg, scale=(0.02, 0.028, 0.024), sub=3, parent=head)
dmg.visible_shadow = False
for o in [brain] + list(brain.children) + [ghost, dmg]: pass
vis(brain, [XRAY_ON[0]]); vis(ghost, [XRAY_ON[0]]); vis(dmg, [XRAY_ON[0]])

# ================= KAMERALAR =================
def camera(name, loc, target, lens, fstop=None, focus=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop: d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = focus or target
    return c

def shake(cam, f0, f1, amp):
    base = cam.location.copy()
    for f in range(f0, f1):
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((random.uniform(-k, k), random.uniform(-k, k), random.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)

# S1: keng plan, past burchak, sekin oldinga
t1 = empty("t1", (4.2, 0.9, 1.0)); key(t1, F["s1"], loc=(4.6, 1.0, 1.2)); key(t1, F["s2"] - 1, loc=(4.2, 0.8, 1.0))
c1 = camera("cam1_wide", (2.4, -2.2, 0.3), t1, 16, 8.0)
key(c1, F["s1"], loc=(2.2, -2.5, 0.3)); key(c1, F["s2"] - 1, loc=(2.9, -1.5, 0.4))
# S2: tuynuk va tayoqqa yaqin plan, DOF
t2 = empty("t2", tuple(HOLE + Vector((0.0, 0.05, 0.4))))
c2 = camera("cam2_tamp", tuple(HOLE + Vector((0.75, -0.45, 0.35))), t2, 28, 2.2, focus=empty("f2", tuple(HOLE + Vector((0, 0, 0.12)))))
key(c2, F["s2"], loc=tuple(HOLE + Vector((0.8, -0.5, 0.36)))); key(c2, BOOM - 1, loc=tuple(HOLE + Vector((0.66, -0.4, 0.32))))
shake(c2, BOOM, F["s3"], 0.05)
# S3: sekinlashgan, past burchak, chap yonoq tomondan (bosh holati kadr boshida hisoblanadi)
sc.frame_set(500); bpy.context.view_layer.update()
HW = head.matrix_world.copy()
hpos = HW @ Vector((0, 0.1, 0.05)); hleft = (HW.to_3x3() @ Vector((1, 0, 0))).normalized(); hfwd = (HW.to_3x3() @ Vector((0, 0, 1))).normalized()
print("HEAD@500", tuple(round(x, 2) for x in hpos))
t3 = empty("t3", (0, 0, 0), head)          # bosh bilan birga harakatlanadi (zarbadan keyin ham kadrda qoladi)
key(t3, F["s3"], loc=(0, -0.12, 0.05)); key(t3, 478, loc=(0, 0.06, 0.05)); key(t3, F["s4"] - 1, loc=(0, 0.16, 0.05))
c3p = hpos + hleft * 0.62 + hfwd * 0.62 + Vector((0, 0, -0.3))
c3 = camera("cam3_slowmo", tuple(c3p), t3, 24, 2.8, focus=head)
key(c3, F["s3"], loc=tuple(c3p)); key(c3, F["s4"] - 1, loc=tuple(c3p + hleft * -0.12 + Vector((0, 0, 0.05))))
# S4: rentgen, bosh atrofida aylanadi
sc.frame_set(650); bpy.context.view_layer.update()
BC = head.matrix_world @ Vector((0, 0.1, 0.04))
pv = empty("xray_pivot", tuple(BC)); bt = empty("brain_t", (0, 0.1, 0.04), head)
c4 = camera("cam4_xray", (0, 0, 0), bt, 50, 5.6); c4.parent = pv
c4.location = (0, -0.62, 0.06)
key(pv, F["s4"], rot=(0, 0, 35)); key(pv, F["s5"] - 1, rot=(0, 0, 105)); interp(pv, "BEZIER")
# S5: keng plan, past burchak, Gage bilan birga suriladi
# shifokor yelkasi ortidan: Gage kameraga (shifokorga) qarab yuradi
t5 = empty("t5"); key(t5, F["s5"], loc=tuple(S5A + Vector((0, 0, 0.35)))); key(t5, WALK0, loc=tuple(S5A + Vector((-0.2, 0, 0.9))))
key(t5, F["s6a"] - 1, loc=tuple(S5B + Vector((0.3, 0, 1.0))))
c5 = camera("cam5_walk", (-3.1, 1.9, 0.4), t5, 20, 5.6)
key(c5, F["s5"], loc=(-3.3, 2.0, 0.38)); key(c5, F["s6a"] - 1, loc=(-2.9, 1.85, 0.45))
# S6a: yuzga yaqin plan, DOF
gh = empty("gage_face_t", (0, 0.11, 0.07), head)
c6a = camera("cam6_face", tuple(S6G + Vector((0.7, -0.25, 1.5))), gh, 55, 1.6)
key(c6a, F["s6a"], loc=tuple(S6G + Vector((0.78, -0.28, 1.48)))); key(c6a, F["s6b"] - 1, loc=tuple(S6G + Vector((0.6, -0.2, 1.52))))
# S6b: past burchakdan ikki kishilik plan
t6 = empty("t6", tuple((S6G + S6C) / 2 + Vector((-0.1, 0, 1.15))))
c6b = camera("cam6_two", tuple((S6G + S6C) / 2 + Vector((0.1, -2.5, 0.38))), t6, 18, 5.6, focus=gh)
key(c6b, F["s6b"], loc=tuple((S6G + S6C) / 2 + Vector((0.15, -2.6, 0.36)))); key(c6b, F["end"], loc=tuple((S6G + S6C) / 2 + Vector((0.0, -2.2, 0.42))))
# ---- qo'shimcha burchaklar (Zack D. tezligi: har 1.5–3 s da kesish) ----
# c1b: relslar bo'ylab yer sathidan, Gage orqada
c1b = camera("cam1b_rails", (-0.9, -0.5, 0.28), t1, 24, 4.0, focus=gh)
key(c1b, 71, loc=(-1.1, -0.55, 0.26)); key(c1b, 130, loc=(-0.3, -0.4, 0.32))
# c2b: Gage yuzi pastdan, diqqat bilan ishlayapti
c2b = camera("cam2b_face", tuple(G + Vector((0.75, -0.95, 0.75))), gh, 50, 2.0)
key(c2b, 261, loc=tuple(G + Vector((0.78, -0.98, 0.72)))); key(c2b, 300, loc=tuple(G + Vector((0.68, -0.88, 0.78))))
# c2c: portlash uzoqdan (keng)
t2c = empty("t2c", tuple(HOLE + Vector((0, 0, 0.9))))
c2c = camera("cam2c_boom", (0.6, -3.6, 1.1), t2c, 20, 8.0)
key(c2c, BOOM, loc=(0.6, -3.6, 1.1)); shake(c2c, BOOM, F["s3"], 0.12)
# c3b: tuynuk yonidan yuqoriga: tayoq tutun ichidan ko'tariladi
c3b = camera("cam3b_low", tuple(HOLE + Vector((0.4, -0.55, 0.08))), t3, 18, 2.8, focus=rod_fly)
key(c3b, F["s3"], loc=tuple(HOLE + Vector((0.4, -0.55, 0.08)))); key(c3b, 440, loc=tuple(HOLE + Vector((0.32, -0.5, 0.12))))
# c4b: rentgen, miya ustuniga yaqin (chap pastdan)
stem_t = empty("stem_t", (0, 0.05, 0.01), head)
c4b = camera("cam4b_stem", (0, 0, 0), stem_t, 60, 4.0); c4b.parent = head
c4b.data.lens = 50
key(c4b, 701, loc=(0.58, -0.08, 0.26)); key(c4b, 770, loc=(0.5, -0.05, 0.3))
# c5b: yurayotgan Gage oldidan, orqaga suriladigan kamera
c5b = camera("cam5b_track", (0, 0, 0), gh, 40, 2.2); c5b.parent = groot
c5b.location = (0.3, -1.7, 1.3)
# c6c: ko'zlarga juda yaqin, qizil kontur yonadi
eyes_t = empty("gage_eyes_t", (0, 0.105, 0.11), head)
c6c = camera("cam6c_eyes", tuple(S6G + Vector((0.85, -0.15, 1.6))), eyes_t, 70, 2.8)
key(c6c, 1111, loc=tuple(S6G + Vector((0.9, -0.16, 1.6)))); key(c6c, 1178, loc=tuple(S6G + Vector((0.75, -0.12, 1.61))))
# c6d: jahldor Gage, pastdan yaqin plan
c6d = camera("cam6d_angry", tuple(S6G + Vector((0.8, -0.6, 1.15))), gh, 35, 2.0)
key(c6d, 1239, loc=tuple(S6G + Vector((0.85, -0.62, 1.12)))); key(c6d, 1280, loc=tuple(S6G + Vector((0.72, -0.5, 1.2))))
# c6e: hamkasbning qo'rqqan yuzi, Gage yelkasi ortidan
ch = empty("cow_head")
cc = ch.constraints.new("CHILD_OF"); cc.target = cow; cc.subtarget = "mixamorig:Head"
cc.use_scale_x = cc.use_scale_y = cc.use_scale_z = False; cc.inverse_matrix = Matrix.Identity(4)
cht = empty("cow_face_t", (0, 0.1, 0.06), ch)
c6e = camera("cam6e_cow", tuple(S6G + Vector((-0.2, -0.4, 1.62))), cht, 50, 2.2)
key(c6e, 1281, loc=tuple(S6G + Vector((-0.2, -0.4, 1.62)))); key(c6e, 1300, loc=tuple(S6G + Vector((-0.1, -0.38, 1.6))))

CUTS = [(1, c1), (71, c1b), (131, c1), (F["s2"], c2), (261, c2b), (301, c2), (BOOM, c2c),
        (F["s3"], c3b), (441, c3), (F["s4"], c4), (701, c4b), (771, c4),
        (F["s5"], c5), (931, c5b), (991, c5), (F["s6a"], c6a), (1111, c6c),
        (F["s6b"], c6b), (1239, c6d), (1281, c6e), (1301, c6b)]
for f, c in CUTS:
    sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = c1
if os.environ.get("CUTS_OUT"):                  # qaysi kadrlar qayta render qilinishi kerakligini hisoblash uchun
    open(os.environ["CUTS_OUT"], "w").write("\n".join(f"{f} {c.name}" for f, c in CUTS))

# ================= YORUG'LIK =================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links; env = N.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
bg = N["Background"]; L.new(env.outputs[0], bg.inputs[0])
wst = bg.inputs[1]
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5)
# kadrlar bo'yicha: (kadr, osmon kuchi, quyosh kuchi, quyosh rangi, quyosh burchagi)
LIGHT = [(1, 1.0, 3.2, (1.0, 0.93, 0.82), (32, 0, 150)),
         (F["s4"], 0.0, 0.0, (1, 1, 1), (48, 0, 150)),
         (F["s5"], 1.0, 3.2, (1.0, 0.93, 0.82), (34, 0, 130)),
         (F["s6a"], 0.55, 3.5, (1.0, 0.6, 0.35), (66, 0, 265))]
for f, ws, se, scol, srot in LIGHT:
    wst.default_value = ws; wst.keyframe_insert("default_value", frame=f)
    sun.data.energy = se; sun.data.keyframe_insert("energy", frame=f)
    sun.data.color = scol; sun.data.keyframe_insert("color", frame=f)
    sun.rotation_euler = [R(a) for a in srot]; sun.keyframe_insert("rotation_euler", frame=f)
interp(sun, "CONSTANT"); interp(sun.data, "CONSTANT"); interp(w.node_tree, "CONSTANT")
def area(name, loc, rot, size, col, keys):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc; l.rotation_euler = [R(a) for a in rot]
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT"); return l
# rentgen: orqadan ko'k kontur
area("xray_rim", tuple(XR + Vector((0.0, 1.2, 1.9))), (-60, 0, 0), 1.0, (0.4, 0.7, 1.0), [(1, 0), (F["s4"], 60), (F["s5"], 0)])
# yaqin planlar uchun yuz yorug'ligi
area("face_fill_s3", tuple(hpos + hfwd * 0.8 + hleft * 0.4 + Vector((0, 0, 0.3))), (0, 0, 0), 0.8, (1, 0.9, 0.8), [(1, 0), (F["s3"], 70), (F["s4"], 0)])
f5 = area("fill_s5", (0.0, 3.0, 1.8), (0, 0, 0), 2.0, (1.0, 0.92, 0.82), [(1, 0), (F["s5"], 250), (F["s6a"], 0)])
f5.constraints.new("TRACK_TO").target = t5
f2b = area("fill_s2b", tuple(G + Vector((0.5, -1.3, 0.6))), (0, 0, 0), 1.2, (1.0, 0.9, 0.8), [(1, 0), (261, 120), (301, 0)])
f2b.constraints.new("TRACK_TO").target = gh
fl = area("face_fill_s6", tuple(S6G + Vector((0.9, -0.9, 1.9))), (0, 0, 0), 1.0, (1.0, 0.75, 0.55), [(1, 0), (F["s6a"], 50), (F["end"], 50)])
fl.constraints.new("TRACK_TO").target = gh
rim = area("rim_red_s6", tuple(S6G + Vector((-1.2, 1.0, 2.0))), (0, 0, 0), 0.8, (1.0, 0.15, 0.08),
           [(1, 0), (F["s6a"], 0), (1110, 0), (1112, 120), (F["s6b"], 0), (1236, 0), (1238, 180), (F["end"], 180)])
rim.constraints.new("TRACK_TO").target = gh

vis(big_rock, [(1, F["s5"] - 1), (F["s6a"], F["end"])])     # S5 da Gage'ni to'smasin

# ================= RENDER =================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 12)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.3
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True      # to'xtab qolsa, qayta ishga tushirish mumkin

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{F['end']}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
