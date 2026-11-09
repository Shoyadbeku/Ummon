# Zack D. Films uslubi: "Bo'shliq chaqiruvi" — baland bino chetida "sakrash" fikri nega paydo bo'ladi (52.9 s, 9:16).
# Asos: scene_ovoz.py (rentgen, kameralar, render) + mixchar.py (Mixamo). Ovoz: foydalanuvchi bergan ElevenLabs mp3.
# Megan tom chetida turadi, pastda shahar; rentgen: miyadagi "omon qolish markazi" (bodomsimon tana) qizil chaqnaydi,
# yashin tanadan oyoqlargacha yuguradi, ongli fikr (peshona qismi, ko'k) bir soniya kechikadi.
import bpy, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_bosliq/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
END = 1270
sc.frame_start, sc.frame_end, sc.render.fps = 1, END, 24
random.seed(11)

# kadrlar (storyboard bilan bir xil: zack_test/bosliq_storyboard.md)
SH = dict(s1=1, s2=45, s3=95, s4=152, s5=227, s6=330, s7=416, s8=483, s9=574, s10=625, s10b=681,
          s11=752, s12=891, s13=987, s14=1083, s15=1143)
XR0, XR1, XR_END = 576, 592, SH["s13"] - 1          # rentgen o'tishi va tugashi

# ---------------- yordamchilar ----------------
def mat(name, col, rough=0.5, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def glow_mat(name, col, strength, alpha=1.0, rim=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    if rim:
        lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = alpha
        L.new(lw.outputs["Facing"], mul.inputs[0]); L.new(mul.outputs[0], mx.inputs["Fac"])
    else:
        mx.inputs["Fac"].default_value = alpha
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    m["em"] = em.name
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(name, size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s/2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o); return o

def sphere(name, r, loc, m, sub=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o); return o

def torus(name, m, minor=0.08):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=minor, major_segments=40, minor_segments=8)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o); return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = (scale,)*3 if isinstance(scale, (int, float)) else scale; o.keyframe_insert("scale", frame=f)

def vis(o, ranges):
    objs = [o] + list(o.children_recursive)
    marks = sorted({1} | {a for a, b in ranges} | {b+1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)

def all_fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "layers") and act.layers:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return list(act.fcurves)

def set_interp(idb, mode="BEZIER", path=None, easing=None):
    for fc in all_fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points:
            k.interpolation = mode
            if easing: k.easing = easing

def keyval(socket_owner, f, v, attr="default_value"):
    setattr(socket_owner, attr, v); socket_owner.keyframe_insert(attr, frame=f)

def pbr(name, folder, scale=1.0, tint=None, proj="BOX"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = proj; t.projection_blend = 0.2
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

def import_collection(path, name):
    """glTF ni alohida kolleksiyaga yuklaydi (sahnadan ajratilgan) — keyin instans sifatida ko'p marta qo'yiladi."""
    col = bpy.data.collections.new(name); sc.collection.children.link(col)
    lc = bpy.context.view_layer.layer_collection.children[col.name]
    bpy.context.view_layer.active_layer_collection = lc
    bpy.ops.import_scene.gltf(filepath=path)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
    bpy.context.view_layer.update()
    ms = [o for o in col.all_objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    col.instance_offset = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)
    sc.collection.children.unlink(col)
    return col, hi - lo

def instance(col, loc, rot_z=0.0, scale=1.0, name=None):
    e = bpy.data.objects.new(name or col.name + "_i", None); sc.collection.objects.link(e)
    e.instance_type = "COLLECTION"; e.instance_collection = col
    e.location = loc; e.rotation_euler.z = R(rot_z); e.scale = (scale,) * 3
    return e

# ================= SHAHAR =================
city = []                                   # rentgen paytida yashiriladigan narsalar
BLD = {k: import_collection(BK + f"{k}_u.glb", "b_" + k) for k in
       ("4fad1459", "27d361b4", "ce863085", "1b352849", "ce9c7ef6", "1690b78f")}
home_col, home_dim = BLD["4fad1459"]
H = home_dim.z                              # Megan turgan bino balandligi (~98 m)
HX, HY = home_dim.x / 2, home_dim.y / 2
city.append(instance(home_col, (0, 0, 0), 0, 1.0, "home"))
ROOF = H + 0.15
EDGE_Y = -HY                                # Megan old tomondagi (-Y) chetda turadi

ASPH = pbr("asphalt", "asphalt_02", 0.25)
PAVE = pbr("pavement", "concrete_pavement", 0.5)
ROOFM = pbr("roof", "concrete_pavement", 0.9, tint=(0.75, 0.73, 0.7))
city.append(box("ground", (900, 900, 0.1), (0, 0, -0.05), PAVE))
ROAD_Y, ROAD_W = -HY - 13.0, 16.0           # bino oldidagi katta ko'cha (X bo'ylab)
ROAD_X = HX + 22.0                          # yon ko'cha (Y bo'ylab)
city.append(box("road_x", (900, ROAD_W, 0.04), (0, ROAD_Y, 0.0), ASPH))
city.append(box("road_y", (ROAD_W, 900, 0.04), (ROAD_X, 0, 0.005), ASPH))
LINE = mat("line", (0.9, 0.9, 0.85), 0.6)
YEL = mat("yline", (0.95, 0.7, 0.1), 0.6)
city.append(box("center_x", (900, 0.25, 0.05), (0, ROAD_Y, 0.0), YEL))
for x in range(-300, 300, 9):
    for dy in (-ROAD_W / 4, ROAD_W / 4):
        city.append(box("dash", (3.5, 0.15, 0.05), (x, ROAD_Y + dy, 0.0), LINE))
for i in range(10):                         # piyodalar o'tish joyi
    city.append(box("zebra", (0.6, ROAD_W - 1, 0.05), (ROAD_X - ROAD_W / 2 - 4 - i * 1.2, ROAD_Y, 0.002), LINE))
# boshqa binolar: ko'chaning ikki tomoni va uzoqroq kvartallar
keys = ["27d361b4", "ce863085", "1b352849", "ce9c7ef6", "1690b78f", "4fad1459"]
slots = []
for gx in range(-6, 7):
    for gy in range(-6, 6):
        x = gx * 46.0; y = gy * 46.0
        if abs(x) < 30 and abs(y) < 30: continue                        # Megan binosi
        if abs(y - ROAD_Y) < ROAD_W / 2 + 14: continue                   # ko'cha
        if abs(x - ROAD_X) < ROAD_W / 2 + 14: continue
        slots.append((x + random.uniform(-4, 4), y + random.uniform(-4, 4)))
for x, y in slots:
    k = random.choice(keys); col, dim = BLD[k]
    s = random.uniform(0.35, 0.75) if k in ("1b352849", "ce9c7ef6") else random.uniform(0.5, 1.1)
    if math.hypot(x, y) < 90 and abs(y - ROAD_Y) < 40: s *= 0.75     # yaqin binolar Megan'nikidan pastroq
    city.append(instance(col, (x, y, 0), random.choice((0, 90, 180, 270)), s))
# mashinalar (BlenderKit Audi, instans) ko'chada harakatlanadi
car_col, _ = import_collection(BK + "c3c28d91_u.glb", "car")
for i in range(14):
    lane = ROAD_Y + (-ROAD_W / 4 if i % 2 else ROAD_W / 4)
    d = 1 if i % 2 else -1
    x0 = random.uniform(-160, 160); v = random.uniform(0.35, 0.55) * d
    c = instance(car_col, (x0, lane, 0.03), 90 if d > 0 else -90, 1.0, f"car{i}")
    key(c, 1, loc=(x0, lane, 0.03)); key(c, END, loc=(x0 + v * END, lane, 0.03))
    for fc in all_fcurves(c):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
    city.append(c)
for i in range(8):
    x0 = ROAD_X + (-ROAD_W / 4 if i % 2 else ROAD_W / 4); d = 1 if i % 2 else -1
    y0 = random.uniform(-200, 200); v = random.uniform(0.35, 0.5) * d
    c = instance(car_col, (x0, y0, 0.03), 0 if d > 0 else 180, 1.0, f"carY{i}")
    key(c, 1, loc=(x0, y0, 0.03)); key(c, END, loc=(x0, y0 + v * END, 0.03))
    for fc in all_fcurves(c):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
    city.append(c)

# ================= TOM =================
METAL = mat("galv", (0.55, 0.56, 0.58), 0.35, metal=0.9)
DARKM = mat("darkmetal", (0.08, 0.08, 0.09), 0.4, metal=0.8)
city.append(box("roof_slab", (home_dim.x + 0.1, home_dim.y + 0.1, 0.5), (0, 0, ROOF - 0.25), ROOFM))
for (sx, sy, x, y) in ((home_dim.x + 0.16, 0.08, 0, -HY - 0.03), (home_dim.x + 0.16, 0.08, 0, HY + 0.03),
                       (0.08, home_dim.y + 0.16, -HX - 0.03, 0), (0.08, home_dim.y + 0.16, HX + 0.03, 0)):
    city.append(box("flashing", (sx, sy, 0.1), (x, y, ROOF - 0.03), DARKM))          # chetdagi metall tasma
for i, (x, y) in enumerate(((-6, 4), (-2.5, 4), (1, 4), (6, 6), (9, 2))):              # konditsionerlar
    city.append(box(f"ac{i}", (2.2, 1.4, 1.3), (x, y, ROOF + 0.65), METAL))
    city.append(cyl(f"fan{i}", 0.5, 0.06, (x, y, ROOF + 1.33), DARKM))
city.append(cyl("tank", 1.6, 3.2, (-9, 8, ROOF + 1.6), METAL))
city.append(cyl("mast", 0.05, 6.0, (10, 9, ROOF + 3.0), METAL))
city.append(sphere("mast_light", 0.12, (10, 9, ROOF + 6.0), mat("red", (1, 0.05, 0.02), 0.4, emit=20)))
city.append(box("stair_hut", (3.5, 3.0, 2.6), (-3, 9.5, ROOF + 1.3), ROOFM))
city.append(box("hut_door", (0.9, 0.05, 2.0), (-3, 7.97, ROOF + 1.0), DARKM))
for i in range(5):                                                                    # quvurlar
    city.append(cyl(f"pipe{i}", 0.08, 0.8, (-11 + i * 1.3, -2, ROOF + 0.4), METAL))

# ================= QAHRAMON =================
def fix_skin(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.25
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.62
                    n.inputs["Coat Weight"].default_value = 0.0

groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
fix_skin(gmesh)
GX = float(os.environ.get("GX", 2.0))
G0 = Vector((GX, EDGE_Y + float(os.environ.get("GEDGE", 0.24)), ROOF))
groot.location = G0
bpy.context.view_layer.update()
GM = groot.matrix_world.copy()
def ML(x, y, z):
    """Megan'ning mahalliy koordinatasi (old tomoni -Y = jarlik tomon, chap qo'li +X) -> dunyo."""
    return GM @ Vector((x, y, z))

A = lambda f: mc.load_action(f, True)
AR = lambda f: mc.load_action(f, False)        # ildiz harakati bilan (orqaga yurish)
mc.add_strip(girl, A("Breathing_Idle.fbx"), 1, repeat=2.0)
mc.add_strip(girl, A("Looking_Down.fbx"), SH["s3"] - 30, blend=8)
mc.add_strip(girl, A("Agony.fbx"), SH["s5"] - 2, blend=4)
mc.add_strip(girl, A("Thinking.fbx"), SH["s6"], blend=0, repeat=1.5)
mc.add_strip(girl, A("Looking_Down.fbx"), SH["s8"] - 20, blend=8)
ESLIP = int(os.environ.get("ESLIP", 644))
mc.add_strip(girl, AR("Edge_Slip.fbx"), ESLIP, blend=4)
mc.add_strip(girl, A("Terrified.fbx"), SH["s11"], blend=0, src=(1, 400))
mc.add_strip(girl, A("Looking_Down.fbx"), SH["s13"], blend=0)
mc.add_strip(girl, A("Relieved_Sigh.fbx"), SH["s14"] - 4, blend=4)
mc.add_strip(girl, AR("Walk_Backwards.fbx"), SH["s15"] + 6, blend=6)
# Agony: qo'rqib bir oz orqaga chekinadi (ildizni siljitamiz), keyingi kesmada yana chetda
for f, dy in ((1, 0), (SH["s5"] + 2, 0), (SH["s5"] + 16, 0.45), (SH["s6"] - 1, 0.45), (SH["s6"], 0)):
    key(groot, f, loc=tuple(G0 + Vector((0, dy, 0))))
ESLIP_DZ = float(os.environ.get("ESLIP_DZ", -0.684))
if ESLIP_DZ:
    for f, dz in ((ESLIP - 1, 0), (ESLIP, ESLIP_DZ), (SH["s11"] - 1, ESLIP_DZ), (SH["s11"], 0)):
        key(groot, f, loc=tuple(G0 + Vector((0, 0, dz))))
set_interp(groot, "CONSTANT")
for fc in all_fcurves(groot):
    for k_ in fc.keyframe_points:
        if abs(k_.co[0] - (SH["s5"] + 16)) < 0.5: k_.interpolation = "CONSTANT"
    for i, k_ in enumerate(fc.keyframe_points):
        if abs(k_.co[0] - (SH["s5"] + 2)) < 0.5: k_.interpolation = "BEZIER"

# shag'al toshchalar: S8 da chetdan pastga tushib ketadi
PEB = mat("pebble", (0.35, 0.33, 0.3), 0.8)
for i in range(9):
    p = sphere(f"peb{i}", random.uniform(0.012, 0.025), (0, 0, 0), PEB, sub=1)
    p.scale = (1, random.uniform(0.6, 0.9), random.uniform(0.5, 0.8))
    p0 = Vector(ML(random.uniform(-0.25, 0.3), random.uniform(-0.22, -0.05), 0.012))
    key(p, 1, loc=tuple(p0), rot=(0, 0, random.uniform(0, 360)))
    if i < 4:                                     # chetga surilib, tushib ketadi
        t0 = SH["s8"] + 22 + i * 9
        edge = Vector((p0.x, EDGE_Y - 0.02, p0.z))
        key(p, t0, loc=tuple(p0)); key(p, t0 + 6, loc=tuple(edge), rot=(40, 0, 60))
        for k in range(1, 20):
            t = k / 24.0
            key(p, t0 + 6 + k, loc=tuple(edge + Vector((0, -0.4 * t, -4.9 * t * t))), rot=(40 + 160 * k, 30 * k, 60 + 90 * k))
    city.append(p)

# ================= RENTGEN: teri + bosh suyagi + miya =================
def bone_world(arm, bone, f=None, rest=False):
    if f is not None: sc.frame_set(f)
    bpy.context.view_layer.update()
    if rest: return arm.matrix_world @ arm.data.bones[bone].matrix_local
    return arm.matrix_world @ arm.pose.bones[bone].matrix

def follow(obj, arm, bone):
    c = obj.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = bone
    c.inverse_matrix = bone_world(arm, bone, rest=True).inverted()
    return c

HEAD = "mixamorig:Head"
fx = empty("fx_head"); follow(fx, girl, HEAD)
def W(x, y, z): return tuple(ML(x, y, z))

xr_vals = []
for o in gmesh:
    for m in o.data.materials:
        if not m or not m.use_nodes or m.get("xr"): continue
        m["xr"] = 1
        N = m.node_tree.nodes; L = m.node_tree.links
        out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
        src = out.inputs["Surface"].links[0].from_socket
        em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.6, 1.0, 1); em.inputs["Strength"].default_value = 2.5
        tr = N.new("ShaderNodeBsdfTransparent"); lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
        pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.6
        L.new(lw.outputs["Facing"], pw.inputs[0])
        mx1 = N.new("ShaderNodeMixShader"); L.new(pw.outputs[0], mx1.inputs["Fac"]); L.new(tr.outputs[0], mx1.inputs[1]); L.new(em.outputs[0], mx1.inputs[2])
        v = N.new("ShaderNodeValue"); v.outputs[0].default_value = 0.0
        mx2 = N.new("ShaderNodeMixShader"); L.new(v.outputs[0], mx2.inputs["Fac"]); L.new(src, mx2.inputs[1]); L.new(mx1.outputs[0], mx2.inputs[2])
        L.new(mx2.outputs[0], out.inputs["Surface"])
        xr_vals.append(v.outputs[0])
for s in xr_vals:
    for f, val in ((1, 0), (XR0, 0), (XR1, 1), (XR_END, 1), (XR_END + 1, 0)): keyval(s, f, val)

def fit_import(path, name, height=None, length=None, drop_text=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    if drop_text:
        for o in list(new):
            if o.type == "MESH" and o.name.startswith("Text"): new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    root = empty(name + "_root")
    for o in new:
        if o.parent is None: o.parent = root
    bpy.context.view_layer.update()
    ms = [o for o in new if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    s = height / (hi.z - lo.z) if height else length / (hi.y - lo.y)
    root.matrix_basis = Matrix.Translation(-(lo + hi) / 2)
    fit = empty(name + "_fit"); fit.parent = fx; root.parent = fit
    return fit, ms, s

def placed(fit, s, center, rotz=0.0, extra=Matrix.Identity(4)):
    fit.matrix_basis = GM @ Matrix.Translation(Vector(center)) @ Matrix.Rotation(R(rotz), 4, "Z") @ extra @ Matrix.Scale(s, 4)

# bosh suyagi (BlenderKit Female skull) — shaffof oq-ko'k
sk, skp, sks = fit_import(BK + "49c13194_u.glb", "skull", height=float(os.environ.get("SKS", 0.215)))
SKC = tuple(map(float, os.environ.get("SKC", "0,-0.012,1.585").split(",")))
placed(sk, sks, SKC, float(os.environ.get("SKR", 0)))
SKM = glow_mat("skull_x", (0.85, 0.92, 1.0), 1.3, alpha=0.6, rim=True)
for o in skp: o.data.materials.clear(); o.data.materials.append(SKM)
vis(sk, [(XR0, XR_END)])

# miya (BlenderKit Human Brain) — pushti, yarim shaffof
br, brp, brs = fit_import(BK + "1d697a0b_u.glb", "brain", length=float(os.environ.get("BRL", 0.148)), drop_text=False)
BRC = tuple(map(float, os.environ.get("BRC", "0,-0.02,1.618").split(",")))
BRR = float(os.environ.get("BRR", 0))
placed(br, brs, BRC, BRR)
BRM = bpy.data.materials.new("brain_x"); BRM.use_nodes = True
N = BRM.node_tree.nodes; L = BRM.node_tree.links; N.clear()
o_ = N.new("ShaderNodeOutputMaterial"); e_ = N.new("ShaderNodeEmission"); t_ = N.new("ShaderNodeBsdfTransparent")
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
mxs = N.new("ShaderNodeMixShader"); add = N.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"
L.new(lw.outputs["Facing"], add.inputs[0]); add.inputs[1].default_value = 0.6; add.inputs[2].default_value = 0.3
L.new(add.outputs[0], mxs.inputs["Fac"])
e_.inputs["Color"].default_value = (1.0, 0.42, 0.5, 1); e_.inputs["Strength"].default_value = 1.6
L.new(t_.outputs[0], mxs.inputs[1]); L.new(e_.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], o_.inputs[0])
for o in brp: o.data.materials.clear(); o.data.materials.append(BRM)
vis(br, [(XR0, XR_END)])

# bodomsimon tana (amigdala) — "omon qolish markazi": qizil chaqnash
RED = glow_mat("amyg", (1.0, 0.06, 0.02), 0.0)
red_em = RED.node_tree.nodes[RED["em"]].inputs["Strength"]
AMY = [W(sx * 0.02, BRC[1] + 0.002, BRC[2] - 0.042) for sx in (-1, 1)]
amyg = []
for i, p in enumerate(AMY):
    a = sphere(f"amyg{i}", 0.0065, p, RED, sub=2); a.parent = fx; a.scale = (1, 1.4, 1); vis(a, [(XR0, XR_END)]); amyg.append(a)
AMYG_ON = int(os.environ.get("AMYG_ON", 594))
keyval(red_em, 1, 0.0); keyval(red_em, AMYG_ON - 1, 0.0)
f = AMYG_ON
while f < XR_END:
    keyval(red_em, f, 60.0); keyval(red_em, f + 4, 14.0); f += 9
halo = sphere("amyg_halo", 1.0, W(0, BRC[1] + 0.002, BRC[2] - 0.042), glow_mat("halo", (1, 0.08, 0.02), 4.0, alpha=0.5, rim=True), sub=3)
halo.parent = fx; vis(halo, [(AMYG_ON, XR_END)])
f = AMYG_ON
while f + 18 <= XR_END:
    key(halo, f, scale=0.008); key(halo, f + 18, scale=0.09); f += 18
halo_marks = [o for o in [halo]]

# peshona qismi (ongli fikr) — ko'k, kechikib yonadi
PFC_M = glow_mat("pfc", (0.05, 0.35, 1.0), 0.0, alpha=0.8, rim=True)
pfc_em = PFC_M.node_tree.nodes[PFC_M["em"]].inputs["Strength"]
pfc = sphere("pfc", 1.0, W(0, BRC[1] - 0.045, BRC[2] + 0.01), PFC_M, sub=3); pfc.parent = fx
pfc.scale = (0.04, 0.022, 0.03); vis(pfc, [(XR0, XR_END)])
PFC_ON = int(os.environ.get("PFC_ON", 866))
keyval(pfc_em, 1, 0.0); keyval(pfc_em, PFC_ON - 1, 0.0); keyval(pfc_em, PFC_ON + 4, 5.0)
f = PFC_ON + 8                                          # tushunolmay "miltillaydi"
while f < XR_END:
    keyval(pfc_em, f, random.choice((0.6, 1.5, 4.0, 6.0, 0.3))); f += random.choice((3, 4, 6))

# sekin ko'k signal: amigdaladan peshonaga (kechikish)
BLUE = glow_mat("bluesig", (0.3, 0.7, 1.0), 25.0)
sig_path = [Vector(W(0.02, BRC[1] + 0.002, BRC[2] - 0.042)), Vector(W(0.03, BRC[1] - 0.02, BRC[2] - 0.02)),
            Vector(W(0.014, BRC[1] - 0.04, BRC[2] + 0.0)), Vector(W(0, BRC[1] - 0.048, BRC[2] + 0.01))]
def polyline(pts, t):
    seg = [(pts[i+1] - pts[i]).length for i in range(len(pts) - 1)]; tot = sum(seg); d = t * tot
    for i, s in enumerate(seg):
        if d <= s or i == len(seg) - 1:
            u = min(1.0, d / s if s else 0); p = pts[i].lerp(pts[i+1], u); return p, (pts[i+1] - pts[i]).normalized()
        d -= s
SIG0 = int(os.environ.get("SIG0", 772))
for j in range(6):                                      # bosh sharcha + izi
    b = sphere(f"sig{j}", 0.0055 * (1 - j * 0.13), (0, 0, 0), BLUE, sub=2); b.parent = fx
    for f in range(SIG0, PFC_ON + 1, 2):
        t = max(0.0, min(1.0, (f - SIG0 - j * 2.5) / (PFC_ON - SIG0)))
        t = t * t * (3 - 2 * t)
        b.location = polyline(sig_path, t)[0]; b.keyframe_insert("location", frame=f)
    vis(b, [(SIG0, PFC_ON + 2)])

# yashin: bodomsimon tanadan umurtqa bo'ylab oyoq-qo'llarga (har segment o'z suyagiga bog'langan)
def bpos(bn): return girl.matrix_world @ girl.data.bones[bn].head_local
def has(bn): return bn in girl.data.bones
P = "mixamorig:"
chains = [[P + "Head", P + "Neck", P + "Spine2", P + "Spine1", P + "Spine", P + "Hips"]]
for s in ("Left", "Right"):
    chains.append([P + "Hips", P + s + "UpLeg", P + s + "Leg", P + s + "Foot", P + s + "ToeBase"])
    chains.append([P + "Spine2", P + s + "Shoulder", P + s + "Arm", P + s + "ForeArm", P + s + "Hand"])
segs = []                                               # (start_bone, a, b, depth)
depth = {P + "Head": 1}
for ch in chains:
    for a_, b_ in zip(ch, ch[1:]):
        if not (has(a_) and has(b_)): continue
        d = depth.get(a_, 1); depth[b_] = d + 1
        segs.append((a_, bpos(a_), bpos(b_), d))
amy_c = Vector(W(0, BRC[1] + 0.002, BRC[2] - 0.042))
segs.insert(0, (HEAD, amy_c, bpos(P + "Neck") if has(P + "Neck") else bpos(HEAD), 0))
BOLT = glow_mat("bolt", (1.0, 0.12, 0.04), 45.0)
BOLT2 = glow_mat("bolt_core", (1.0, 0.45, 0.15), 50.0)
def bolt_curve(name, a, b, jitter):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0035; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); n = 7; sp.points.add(n - 1)
    d = (b - a); ax = d.normalized(); perp1 = ax.orthogonal().normalized(); perp2 = ax.cross(perp1)
    for i in range(n):
        t = i / (n - 1); p = a.lerp(b, t)
        if 0 < i < n - 1:
            p = p + perp1 * random.uniform(-1, 1) * jitter * d.length + perp2 * random.uniform(-1, 1) * jitter * d.length
        sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); return o
WAVES = [int(x) for x in os.environ.get("WAVES", "626,634,644,652,662,672,684,696,708,720,734,746").split(",")]
for wi, w0 in enumerate(WAVES):
    for si, (bn, a, b, d) in enumerate(segs):
        o = bolt_curve(f"bolt{wi}_{si}", a, b, 0.18)
        o.data.materials.append(BOLT2 if wi % 2 else BOLT)
        follow(o, girl, bn)
        t = w0 + d                                      # yashin tezligi: har bo'g'in 1 kadr
        vis(o, [(t, t + 3)])

# rentgen foni (to'q ko'k sfera) — shahar yashiriladi
BGM = bpy.data.materials.new("xray_bg"); BGM.use_nodes = True
bg = sphere("xray_bg", 6.0, tuple(ML(0, 0, 1.2)), BGM, sub=4)
N = BGM.node_tree.nodes; L = BGM.node_tree.links; N.clear()
o_ = N.new("ShaderNodeOutputMaterial"); e_ = N.new("ShaderNodeEmission"); t_ = N.new("ShaderNodeBsdfTransparent"); m_ = N.new("ShaderNodeMixShader")
gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], gr.inputs[0])
mc_ = N.new("ShaderNodeMix"); mc_.data_type = "RGBA"; mc_.inputs[6].default_value = (0.002, 0.006, 0.02, 1); mc_.inputs[7].default_value = (0.012, 0.03, 0.08, 1)
L.new(gr.outputs["Fac"], mc_.inputs["Factor"]); L.new(mc_.outputs[2], e_.inputs["Color"]); e_.inputs["Strength"].default_value = 1.0
L.new(t_.outputs[0], m_.inputs[1]); L.new(e_.outputs[0], m_.inputs[2]); L.new(m_.outputs[0], o_.inputs[0])
bg.visible_shadow = False
for f, v in ((1, 0), (XR0, 0), (XR1, 1)): keyval(m_.inputs["Fac"], f, v)
vis(bg, [(XR0, XR_END)])
# tom cheti: rentgen paytida ko'k chiziq bo'lib qoladi
edge_line = box("edge_line", (6, 0.02, 0.01), W(0, -0.24, 0.0), glow_mat("edge_g", (0.2, 0.6, 1.0), 8.0))
grid = box("xr_floor", (6, 3, 0.002), W(0, 1.27, -0.002), glow_mat("floor_g", (0.05, 0.15, 0.35), 0.4, alpha=0.6))
for o in (edge_line, grid): vis(o, [(XR1, SH["s11"] - 1)])
for o in city: vis(o, [(1, XR1 + 2), (XR_END + 1, END)])

# ================= KAMERALAR =================
cams = []
def camera(name, f0, f1, p0, p1, target, lens, fstop=None, ease="QUART", lens1=None, noise=0.012, rot=None, rot1=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = 0.01; d.clip_end = 3000
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c)
    if rot:                                   # tik pastga qaraganda TRACK_TO aylanib ketadi: burchakni qo'lda beramiz
        key(c, f0, rot=rot); key(c, f1, rot=rot1 or rot)
    else:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop: d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = target
    key(c, f0, loc=tuple(p0)); key(c, f1, loc=tuple(p1))
    if lens1:
        d.lens = lens; d.keyframe_insert("lens", frame=f0); d.lens = lens1; d.keyframe_insert("lens", frame=f1)
        for fc in all_fcurves(d):
            for k in fc.keyframe_points: k.interpolation = ease; k.easing = "EASE_IN_OUT"
    for fc in all_fcurves(c):
        for k in fc.keyframe_points: k.interpolation = ease; k.easing = "EASE_OUT"
        n = fc.modifiers.new("NOISE"); n.scale = 22; n.strength = noise; n.phase = random.uniform(0, 100)
    cams.append((f0, c)); return c

def tgt(name, x, y, z, head=True):
    return empty(name, W(x, y, z), fx if head else None)

face = tgt("t_face", 0, -0.05, 1.6)
street = empty("t_street", W(0.2, -3.5, -H), None)
c1 = camera("c01_drop", SH["s1"], SH["s2"] - 1, ML(0.7, -1.9, 9.0), ML(0.45, -1.35, 3.2), street, 17, None, "EXPO", noise=0.03,
            rot=(14, 0, -8), rot1=(12, 0, 4))
feet_t = empty("t_feet", W(0, -6, -2.0))
side_t = empty("t_side", W(0, -0.3, 0.55))
camera("c02_side", SH["s2"], SH["s3"] - 1, ML(3.0, -2.7, -1.3), ML(2.3, -2.1, -0.7), side_t, 18, None, "SINE")
camera("c03_face", SH["s3"], SH["s4"] - 1, ML(0.25, -0.95, 1.42), ML(0.1, -0.62, 1.5), face, 50, 2.0, "SINE")
camera("c04_vertigo", SH["s4"], SH["s5"] - 1, ML(0.5, -0.5, 1.8), ML(0.4, -0.72, 1.6), street, 40, None, "SINE", lens1=14,
       rot=(16, 0, 4), rot1=(18, 0, -6))
body_t = empty("t_body", W(0, 0.35, 1.15))
camera("c05_low", SH["s5"], SH["s6"] - 1, ML(1.6, -0.6, 0.22), ML(1.1, -0.95, 0.3), body_t, 16, 5.6, "SINE")
roof_t = empty("t_roof", W(0, 0, 0.5))
camera("c06_drone", SH["s6"], SH["s7"] - 1, ML(-16, -22, 10), ML(10, -24, 16), roof_t, 24, None, "SINE", noise=0.05)
sil_t = empty("t_sil", W(0, -0.2, 1.2))
camera("c07_side", SH["s7"], SH["s8"] - 1, ML(2.6, -0.45, 0.35), ML(2.1, -0.15, 0.55), sil_t, 20, 4.0, "SINE")
toe_t = empty("t_toe", W(0.05, -0.2, 0.05))
camera("c08_toes", SH["s8"], SH["s9"] - 1, ML(0.6, -0.75, 0.22), ML(0.42, -0.62, 0.13), toe_t, 32, 2.8, "SINE")
skc = tgt("t_skull", 0, -0.01, 1.6)
camera("c09_xray", SH["s9"], SH["s10"] - 1, ML(1.0, -0.2, 1.62), ML(0.48, -0.08, 1.6), skc, 45, 5.6, "QUART")
neck_t = tgt("t_neck", 0, -0.02, 1.42)
camera("c10_bolt", SH["s10"], SH["s10b"] - 1, ML(-0.55, -0.85, 1.55), ML(-0.38, -0.62, 1.4), neck_t, 26, 5.6, "SINE")
full_t = empty("t_full", W(0, 0.1, 0.9))
camera("c10b_body", SH["s10b"], SH["s11"] - 1, ML(1.05, -1.15, 0.35), ML(0.8, -0.95, 0.5), full_t, 18, 8.0, "SINE")
brain_t = tgt("t_brain", 0, -0.01, 1.61)
camera("c11_orbit", SH["s11"], SH["s12"] - 1, ML(0.42, 0.12, 1.66), ML(-0.2, -0.36, 1.64), brain_t, 40, 8.0, "SINE")
camera("c12_front", SH["s12"], SH["s13"] - 1, ML(0.3, -0.7, 1.86), ML(0.16, -0.42, 1.8), brain_t, 40, 8.0, "QUART")
camera("c13_vertigo", SH["s13"], SH["s14"] - 1, ML(-0.45, -1.0, 1.55), ML(-0.5, -0.8, 1.8), street, 14, None, "SINE", lens1=36,
       rot=(8, 0, -10), rot1=(6, 0, 6))
camera("c14_face", SH["s14"], SH["s15"] - 1, ML(-0.55, -0.8, 1.5), ML(0.15, -0.85, 1.58), face, 50, 2.0, "SINE")
end_t = empty("t_end", W(0, 0.9, 1.0))
camera("c15_rise", SH["s15"], END, ML(0.3, -1.5, 1.4), ML(1.0, -4.2, 3.0), end_t, 30, 4.0, "SINE", noise=0.03)
for f, c in cams: sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = cams[0][1]

# ================= YORUG'LIK =================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; env = N.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(float(os.environ.get("HDRI_ROT", 200))))
w.node_tree.links.new(tc.outputs["Generated"], mp.inputs[0]); w.node_tree.links.new(mp.outputs[0], env.inputs[0])
w.node_tree.links.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = float(os.environ.get("SKY", 1.0))
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = float(os.environ.get("SUN", 3.5)); sun.data.angle = R(1.5); sun.data.color = (1.0, 0.86, 0.68)
sun.rotation_euler = (R(62), 0, R(float(os.environ.get("SUN_Z", 25))))
def area(name, loc, target, energy, size, col=(1, 0.9, 0.78)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.energy = energy; l.data.size = size; l.data.color = col; l.location = loc
    t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l
area("face_fill", tuple(ML(0.8, -1.4, 2.0)), face, 70, 1.2, (1.0, 0.9, 0.8))
area("rim", tuple(ML(-0.8, 1.0, 2.2)), face, 90, 0.8, (0.85, 0.92, 1.0))

# ================= RENDER =================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 14)); sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 24
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPOSURE", -0.4))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("DBG_CAM"):                 # sozlash uchun: "x,y,z;tx,ty,tz;lens" (Megan mahalliy koordinatasida)
    pc, pt, ln = os.environ["DBG_CAM"].split(";")
    sc.timeline_markers.clear()
    dt = empty("dbg_t", W(*map(float, pt.split(","))), fx)
    dc = camera("dbg", 1, 2, ML(*map(float, pc.split(","))), ML(*map(float, pc.split(","))), dt, float(ln), None, noise=0)
    dc.constraints[0].target = dt; sc.camera = dc
    dc.animation_data_clear(); dc.location = ML(*map(float, pc.split(",")))

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; bpy.ops.render.render(write_still=True)
    else:
        sc.frame_start = int(os.environ.get("START", 1)); sc.frame_end = int(os.environ.get("STOP", END))
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
