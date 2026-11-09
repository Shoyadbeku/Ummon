# Zack D. Films uslubi: "Uyqudagi tepish" — uxlayotganda nega qulayotgandek bo'lib, silkinib uyg'onamiz (43.8 s, 9:16).
# Asos: scene_bosliq.py (rentgen, yashin, kameralar, render) + mixchar.py (Mixamo). Ovoz: foydalanuvchi bergan wav.
# Megan tunda karavotda uxlaydi; tushida osmondan va daraxtdan qulaydi; rentgen: miya "omon qolish markazi"
# (bodomsimon tana) qizil chaqnaydi, yurak sekinlashadi, yashin asab bo'ylab oyoqlarga yuguradi — oyoq tepadi.
# Kadr rejasi: zack_test/tepish_storyboard.md
import bpy, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_tepish/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
EV = lambda k, d: float(os.environ.get(k, d))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
END = 1053
sc.frame_start, sc.frame_end, sc.render.fps = 1, END, 24
random.seed(7)

# kadrlar (storyboard bilan bir xil)
SH = dict(s1=1, s2=71, s3=132, s4=207, s5=278, s6=361, s7=428, s8=512, s9=567, s10=675, s11=786, s12=865,
          s13=961, s14=1024)
JERK = 169                      # "silkinib"
XF0, XF1 = 247, 262             # "miyangiz": teri shaffoflashadi, so'ng rentgen bo'shlig'iga kesma
XR = [(XF1, SH["s7"] - 1), (SH["s9"], SH["s10"] - 1), (SH["s11"], SH["s13"] - 1)]   # rentgen kadrlari
DREAM = [(SH["s2"], SH["s3"] - 1)]
TREE = [(SH["s10"], SH["s11"] - 1)]
DROP = 738                      # "yiqilyapti": shoxdan qo'l sirg'aladi
BOLT0 = 842                     # "yashin"
ADR0 = 921                      # "adrenalin"
KICK = 1007                     # "tepib"
WAKE = 1027                     # "ko'zingiz ochiladi"

def in_ranges(f, rs): return any(a <= f <= b for a, b in rs)
ROOM_RANGES = [(1, XF1 - 1), (SH["s7"], SH["s9"] - 1), (SH["s13"], END)]

# ---------------- yordamchilar ----------------
def mat(name, col, rough=0.5, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def glow_mat(name, col, strength, alpha=1.0, rim=False, blend=0.35):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    if rim:
        lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = blend
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

def plane(name, size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = (scale,)*3 if isinstance(scale, (int, float)) else scale; o.keyframe_insert("scale", frame=f)

def vis(o, ranges, rec=True):
    objs = [o] + (list(o.children_recursive) if rec else [])
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

def set_interp(idb, mode="BEZIER", path=None):
    for fc in all_fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode

def keyval(sock, f, v, attr="default_value"):
    setattr(sock, attr, v); sock.keyframe_insert(attr, frame=f)

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

def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi

def import_model(path, name, loc=(0, 0, 0), rot_z=0.0, height=None, scale=None):
    """glTF ni yuklab, bitta ildizga bog'laydi: pastki markazi loc da, balandligi height (yoki scale)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    lo, hi = bbox(new)
    s = (height / (hi.z - lo.z)) if height else (scale or 1.0)
    inner = empty(name + "_c"); inner.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
    for o in new:
        if o.parent is None: o.parent = inner
    root = empty(name); inner.parent = root
    root.location = loc; root.rotation_euler.z = R(rot_z); root.scale = (s,) * 3
    bpy.context.view_layer.update()
    return root, [o for o in new if o.type == "MESH"], (hi - lo) * s

# ================= XONA =================
room = []
FLOOR = pbr("floor", "laminate_floor_02", 0.45)
WALL = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.62, 0.68, 0.78))
WOOD = mat("frame_white", (0.85, 0.85, 0.82), 0.4)
X0, X1, Y0, Y1, HZ = -2.4, 2.4, -3.2, 1.65, 2.7          # xona chegaralari
WY0, WY1, WZ0, WZ1 = -1.55, 0.25, 0.85, 2.3                # oyna (chap devorda, -X)
room.append(box("floor", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.025), FLOOR))
room.append(box("ceiling", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ + 0.025), WALL))
room.append(box("wall_back", (X1 - X0, 0.1, HZ), ((X0 + X1) / 2, Y1 + 0.05, HZ / 2), WALL))
room.append(box("wall_front", (X1 - X0, 0.1, HZ), ((X0 + X1) / 2, Y0 - 0.05, HZ / 2), WALL))
room.append(box("wall_right", (0.1, Y1 - Y0, HZ), (X1 + 0.05, (Y0 + Y1) / 2, HZ / 2), WALL))
# chap devor oyna bilan (4 bo'lak)
room.append(box("wl_low", (0.1, Y1 - Y0, WZ0), (X0 - 0.05, (Y0 + Y1) / 2, WZ0 / 2), WALL))
room.append(box("wl_top", (0.1, Y1 - Y0, HZ - WZ1), (X0 - 0.05, (Y0 + Y1) / 2, (HZ + WZ1) / 2), WALL))
room.append(box("wl_a", (0.1, WY0 - Y0, WZ1 - WZ0), (X0 - 0.05, (Y0 + WY0) / 2, (WZ0 + WZ1) / 2), WALL))
room.append(box("wl_b", (0.1, Y1 - WY1, WZ1 - WZ0), (X0 - 0.05, (WY1 + Y1) / 2, (WZ0 + WZ1) / 2), WALL))
for (sy, sz, y, z) in ((WY1 - WY0 + 0.1, 0.06, (WY0 + WY1) / 2, WZ0), (WY1 - WY0 + 0.1, 0.06, (WY0 + WY1) / 2, WZ1),
                       (0.06, WZ1 - WZ0, WY0, (WZ0 + WZ1) / 2), (0.06, WZ1 - WZ0, WY1, (WZ0 + WZ1) / 2),
                       (0.04, WZ1 - WZ0, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2), (WY1 - WY0, 0.04, (WY0 + WY1) / 2, 1.75)):
    room.append(box("wframe", (0.12, sy, sz), (X0 - 0.03, y, z), WOOD))
room.append(box("sill", (0.25, WY1 - WY0 + 0.3, 0.04), (X0 + 0.08, (WY0 + WY1) / 2, WZ0 - 0.02), WOOD))
# parda (yupqa, yorug'lik o'tkazadi)
CURT = mat("curtain", (0.55, 0.6, 0.75), 0.9)
CURT.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.3
for i, y in enumerate((WY0 - 0.25, WY1 + 0.25)):
    c = box(f"curtain{i}", (0.03, 0.42, 2.3), (X0 + 0.14, y, 1.4), CURT)
    sd = c.modifiers.new("w", "WAVE"); sd.use_x = False; sd.use_y = True; sd.height = 0.04; sd.width = 0.18; sd.speed = 0
    room.append(c)
RUG = mat("rug", (0.25, 0.22, 0.3), 0.95)
room.append(box("rug", (2.6, 1.6, 0.012), (0.0, -1.55, 0.006), RUG))

# karavot (BlenderKit Ultima King Bed): bosh tomoni +Y devorga
bed, bed_ms, bed_dim = import_model(BK + "9d002926_u.glb", "bed", (0, 0, 0))
names = {o.name: o for o in bed_ms}
back = next((o for o in bed_ms if "back" in o.name.lower()), None)
if back:
    lo, hi = bbox([back])
    if (lo.y + hi.y) / 2 < 0: bed.rotation_euler.z = R(180)
bed.location = (0, Y1 - bed_dim.y / 2 - 0.02, 0)
for o in list(bed_ms):                        # old yostiqlar qizning boshiga kirib qolmasin
    if any(k in o.name.lower() for k in ("orange", "cylinder", "mid white")):
        bed_ms.remove(o); bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()
room.append(bed)
BED_LO, BED_HI = bbox(bed_ms)
BED_CX, BED_CY = (BED_LO.x + BED_HI.x) / 2, (BED_LO.y + BED_HI.y) / 2
def ray_top(x, y):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = sc.ray_cast(dg, Vector((x, y, 1.8)), Vector((0, 0, -1)))
    return loc.z if hit else None
# tumbochkalar, chiroq, budilnik, kitoblar
ns1, _, ns1d = import_model(BK + "fbb98c0b_u.glb", "nightstand_r", (BED_HI.x + 0.32, Y1 - 0.3, 0), 0)
NS_TOP = ns1d.z
ns2, _, _ = import_model(PH + "painted_wooden_nightstand/painted_wooden_nightstand.gltf", "nightstand_l",
                         (BED_LO.x - 0.3, Y1 - 0.3, 0), 0, height=0.55)
lamp, lamp_ms, lampd = import_model(BK + "4e0605de_u.glb", "lamp", (BED_HI.x + 0.32, Y1 - 0.26, NS_TOP), 200, height=0.45)
clock, _, _ = import_model(PH + "alarm_clock_01/alarm_clock_01.gltf", "clock", (BED_LO.x - 0.3, Y1 - 0.38, 0.55), 160, height=0.11)
room += [ns1, ns2, lamp, clock]

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
                        n.inputs["Roughness"].default_value = 0.6
                    n.inputs["Coat Weight"].default_value = 0.0

groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
fix_skin(gmesh)
P = "mixamorig:"
AR = lambda f: mc.load_action(f, False)
SLEEP = AR("Laying_Sleeping.fbx")
mc.add_strip(girl, SLEEP, 1, repeat=30.0)
bpy.context.view_layer.update()

def bw(bn, f=None):
    if f is not None: sc.frame_set(f)
    return girl.matrix_world @ girl.pose.bones[P + bn].head

# yotgan Megan'ni karavotga joylash: o'ng yelka karavotning -X chetiga yaqin, bosh yostiqda
sc.frame_set(20)
dg = bpy.context.evaluated_depsgraph_get()
body = next(o for o in gmesh if o.name.endswith("Body"))
eb = body.evaluated_get(dg); me = eb.to_mesh()
hips = bw("Hips")
zs = [(eb.matrix_world @ v.co).z for v in me.vertices if abs((eb.matrix_world @ v.co).y - hips.y) < 0.35]
BACK_Z = min(zs); eb.to_mesh_clear()
rsh = bw("RightArm")
MATT = ray_top(BED_CX - 0.3, BED_CY) or 0.6
GROOM = Vector((BED_LO.x + EV("EDGE_IN", 0.15) - rsh.x, BED_HI.y - EV("HEAD_IN", 0.66) - bw("Head").y, MATT - BACK_Z - EV("SINK", 0.05)))
print("bed", BED_LO, BED_HI, "matt", MATT, "back", BACK_Z, "groom", GROOM)
GDREAM = Vector((3000, 0, 400))
GTREE = Vector((-3000, 0, -40))
BRANCH_Z = EV("BRANCH_Z", 5.2)

# ildiz joylashuvi (CONSTANT): xona / tush (osmon) / daraxt
def groot_key(f, loc, rz=0.0, rx=0.0):
    groot.location = loc; groot.rotation_euler = (R(rx), 0, R(rz))
    groot.keyframe_insert("location", frame=f); groot.keyframe_insert("rotation_euler", frame=f)
groot_key(1, GROOM)
FALL_V = 1.6                                     # m/kadr (~38 m/s)
groot_key(SH["s2"], GDREAM, 180, EV("DRX", 180))
groot_key(SH["s3"] - 1, GDREAM - Vector((0, 0, FALL_V * (SH["s3"] - 1 - SH["s2"]))), 180, EV("DRX", 180))
groot_key(SH["s3"], GROOM)
# daraxt: osilib turadi, DROP da qulaydi
sc.frame_set(1)
HANG = AR("Hanging_Idle_2.fbx")
FALL = AR("Falling_2.fbx")
# 30 fps manba: kadr soni = (tugash - boshlanish) / 0.8 — bo'laklar keyingi kadrga oshib ketmasin
def strip_to(act, f0, f1, blend=0):
    s_ = mc.add_strip(girl, act, f0, blend=blend, hold=False)
    s_.action_frame_end = s_.action_frame_start + (f1 - f0) / s_.scale
    if abs(s_.frame_end - f1) > 0.5: s_.frame_end_ui = f1
    return s_
strip_to(FALL, SH["s2"], SH["s3"] - 1)
strip_to(HANG, SH["s10"], DROP + 4)
strip_to(FALL, DROP, SH["s11"] - 1, blend=5)
TREE_ROOT = GTREE + Vector((0.0, 0.0, BRANCH_Z - 2.19 - 0.04))
groot_key(SH["s10"], TREE_ROOT, 15)
groot_key(DROP, TREE_ROOT, 15)
for k in range(1, SH["s11"] - DROP):
    t = k / 24.0
    groot.location = TREE_ROOT - Vector((0, 0.04 * k, 0.5 * 9.81 * 0.25 * t * t)); groot.rotation_euler = (0, 0, R(15))
    groot.keyframe_insert("location", frame=DROP + k); groot.keyframe_insert("rotation_euler", frame=DROP + k)
groot_key(SH["s11"], GROOM)
set_interp(groot, "CONSTANT")
for fc in all_fcurves(groot):            # tushdagi qulash chiziqli
    for k_ in fc.keyframe_points:
        if abs(k_.co[0] - SH["s2"]) < 0.5 and fc.data_path == "location": k_.interpolation = "LINEAR"

# ---- kod bilan poza o'zgarishlari (NLA ustiga REPLACE strip): silkinish, qo'l tushishi, tepish, uyg'onish
def overlay(name, frames, order, influence=None):
    """frames: [(f, {suyak: [(o'q_dunyo, gradus) | ("aim", yo'nalish_dunyo)]})]; order: kalitlanadigan suyaklar (ota birinchi)."""
    ad = girl.animation_data
    store = []
    for f, ops in frames:
        sc.frame_set(f)
        for bn in order:
            for op in ops.get(bn, []):
                pb = girl.pose.bones[P + bn]
                Mw = girl.matrix_world @ pb.matrix
                head = Mw.translation.copy()
                if op[0] == "aim":
                    cur = (Mw.to_3x3() @ Vector((0, 1, 0))).normalized()
                    q = cur.rotation_difference(Vector(op[1]).normalized()); Rm = q.to_matrix().to_4x4()
                else:
                    Rm = Matrix.Rotation(R(op[1]), 4, Vector(op[0]).normalized())
                Mw2 = Matrix.Translation(head) @ Rm @ Matrix.Translation(-head) @ Mw
                pb.matrix = girl.matrix_world.inverted() @ Mw2
                bpy.context.view_layer.update()
        qs = {bn: girl.pose.bones[P + bn].rotation_quaternion.copy() for bn in order}
        if store:                                   # kvaternion belgisi almashmasin (interpolatsiya buzilmasin)
            for bn in order: qs[bn].make_compatible(store[-1][1][bn])
        store.append((f, qs))
    act = bpy.data.actions.new(name); act.use_fake_user = True
    ad.action = act
    for f, qs in store:
        for bn, q in qs.items():
            pb = girl.pose.bones[P + bn]; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f)
    ad.action = None
    tr = ad.nla_tracks.new(); tr.name = name
    s = tr.strips.new(name, int(frames[0][0]), act)
    if act.slots: s.action_slot = act.slots[0]
    s.blend_type = "REPLACE"; s.extrapolation = "NOTHING"; s.blend_in = s.blend_out = 0
    if influence:
        s.use_animated_influence = True
        for f, v in influence:
            s.influence = v; s.keyframe_insert("influence", frame=f)
        for fc in s.fcurves:
            for k_ in fc.keyframe_points: k_.interpolation = "CONSTANT"
    return s

X = (1, 0, 0); Y = (0, 1, 0); Z = (0, 0, 1)
def jerk_pose(a):
    return {"Spine": [(X, 7 * a)], "Spine1": [(X, 5 * a)], "Neck": [(X, 6 * a)], "Head": [(X, 8 * a)],
            "LeftUpLeg": [(X, -16 * a)], "RightUpLeg": [(X, -12 * a)], "LeftLeg": [(X, 22 * a)], "RightLeg": [(X, 16 * a)],
            "LeftArm": [(X, -14 * a)], "RightArm": [(X, -18 * a)], "LeftForeArm": [(X, -10 * a)], "RightForeArm": [(X, -10 * a)]}
JORD = ["Spine", "Spine1", "Neck", "Head", "LeftArm", "LeftForeArm", "RightArm", "RightForeArm",
        "LeftUpLeg", "LeftLeg", "RightUpLeg", "RightLeg"]
overlay("jerk", [(JERK - 3, {}), (JERK, jerk_pose(1.0)), (JERK + 2, jerk_pose(1.15)), (JERK + 5, jerk_pose(0.55)),
                 (JERK + 9, jerk_pose(0.75)), (JERK + 16, jerk_pose(0.25)), (JERK + 26, jerk_pose(0.12)), (SH["s4"] - 1, {})], JORD)
# mushaklar bo'shashadi: o'ng qo'l karavot chetidan shalvirab tushadi (keyingi xona/rentgen kadrlarida ham shunday qoladi)
AF = 528
def arm_drop(a):
    d1 = Vector((-0.85, -0.1, -0.15 - 0.55 * a)); d2 = Vector((-0.3, -0.08, -1.0))
    return {"RightArm": [("aim", tuple(d1))], "RightForeArm": [("aim", tuple(d2.lerp(d1, 1 - a)))], "RightHand": [("aim", (-0.1, -0.05, -1))] if a > 0.5 else []}
overlay("arm_drop", [(AF - 1, {}), (AF + 4, arm_drop(0.55)), (AF + 7, arm_drop(1.0)), (AF + 10, arm_drop(0.92)), (AF + 13, arm_drop(1.0)), (END, arm_drop(1.0))],
        ["RightArm", "RightForeArm", "RightHand"], influence=[(1, 1.0), (AF - 1, 1.0), (SH["s10"], 0.0), (SH["s11"], 1.0)])
# tepish: chap oyoq keskin tepadi
def kick_pose(a):
    return {"LeftUpLeg": [(X, -38 * a)], "LeftLeg": [(X, 30 * a)], "RightUpLeg": [(X, -10 * a)], "RightLeg": [(X, 12 * a)],
            "Spine": [(X, 4 * a)], "Head": [(X, 5 * a)]}
overlay("kick", [(KICK - 2, {}), (KICK + 1, kick_pose(1.0)), (KICK + 3, kick_pose(1.1)), (KICK + 7, kick_pose(0.45)),
                 (KICK + 11, kick_pose(0.6)), (KICK + 19, kick_pose(0.2)), (WAKE - 2, {})],
        ["Spine", "Head", "LeftUpLeg", "LeftLeg", "RightUpLeg", "RightLeg"])
# uyg'onish: bosh va ko'krak keskin ko'tariladi
def wake_pose(a):
    return {"Spine": [(X, 10 * a)], "Spine1": [(X, 9 * a)], "Spine2": [(X, 6 * a)], "Neck": [(X, 8 * a)], "Head": [(X, 10 * a)]}
overlay("wake", [(WAKE - 2, {}), (WAKE + 2, wake_pose(1.0)), (WAKE + 5, wake_pose(1.12)), (WAKE + 12, wake_pose(0.95)), (END, wake_pose(1.0))],
        ["Spine", "Spine1", "Spine2", "Neck", "Head"])
sc.frame_set(20)

# ---- ko'z qovoqlari (Megan'da shape key yo'q): uxlaganda yopiq, WAKE da ochiladi
def follow(obj, bone):
    c = obj.constraints.new("CHILD_OF"); c.target = girl; c.subtarget = P + bone
    bpy.context.view_layer.update()
    c.inverse_matrix = (girl.matrix_world @ girl.data.bones[P + bone].matrix_local).inverted()
    return c
groot_rest = groot.matrix_world.copy()
def RL(x, y, z):
    """Megan dam olish (tik turgan) pozasidagi mahalliy koordinata -> dunyo (hozirgi ildiz bo'yicha)."""
    return groot.matrix_world @ Vector((x, y, z))
sc.frame_set(1)
fx = empty("fx_head"); follow(fx, "Head")
fxc = empty("fx_chest"); follow(fxc, "Spine2")
SKIN = mat("lid", tuple(map(float, os.environ.get("LIDC", "0.34,0.2,0.15").split(","))), 0.55)
SKIN.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.15
_N = SKIN.node_tree.nodes; _L = SKIN.node_tree.links
_tc = _N.new("ShaderNodeTexCoord"); _sep = _N.new("ShaderNodeSeparateXYZ"); _L.new(_tc.outputs["Object"], _sep.inputs[0])
_mr = _N.new("ShaderNodeMapRange"); _mr.inputs[1].default_value = -0.45; _mr.inputs[2].default_value = -0.25
_L.new(_sep.outputs["Z"], _mr.inputs[0])
_mx = _N.new("ShaderNodeMix"); _mx.data_type = "RGBA"; _mx.inputs[6].default_value = (0.05, 0.03, 0.025, 1)
_mx.inputs[7].default_value = SKIN.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:]
_L.new(_mr.outputs[0], _mx.inputs["Factor"]); _L.new(_mx.outputs[2], SKIN.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
EYE = tuple(map(float, os.environ.get("EYE", "0.032,-0.123,1.624").split(",")))
lids = []
for sx in (-1, 1):
    l = sphere(f"lid{sx}", 1.0, tuple(RL(sx * EYE[0], EYE[1], EYE[2])), SKIN, sub=3)
    l.scale = (EV("LIDX", 0.021), EV("LIDY", 0.0175), EV("LIDZ", 0.019)); l.parent = fx; lids.append(l)
    vis(l, [(1, SH["s2"] - 1), (SH["s3"], XF1 - 1), (SH["s7"], SH["s9"] - 1), (SH["s13"], WAKE)])

# ================= RENTGEN =================
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
XR_ALL = [(XF0, XR[0][1])] + XR[1:]
for s in xr_vals:
    keyval(s, 1, 0); keyval(s, XF0, 0); keyval(s, XF1, 1)
    for a, b in XR:
        keyval(s, a, 1); keyval(s, b, 1); keyval(s, b + 1, 0)
        if a > XF1: keyval(s, a - 1, 0)
for o in gmesh:
    for m in o.data.materials:
        nt = m.node_tree
        if nt.animation_data and nt.animation_data.action:
            for fc in all_fcurves(nt):
                for k_ in fc.keyframe_points:
                    k_.interpolation = "LINEAR" if XF0 <= k_.co[0] <= XF1 else "CONSTANT"

def fit_import(path, name, parent, height=None, length=None, drop_text=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    if drop_text:
        for o in list(new):
            if o.type == "MESH" and o.name.startswith("Text"): new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    root = empty(name + "_root")
    for o in new:
        if o.parent is None: o.parent = root
    lo, hi = bbox(new)
    s = height / (hi.z - lo.z) if height else length / (hi.y - lo.y)
    root.matrix_basis = Matrix.Translation(-(lo + hi) / 2)
    fit = empty(name + "_fit"); fit.parent = parent; root.parent = fit
    return fit, [o for o in new if o.type == "MESH"], s

def placed(fit, s, center, rotz=0.0, extra=Matrix.Identity(4)):
    fit.matrix_basis = groot.matrix_world @ Matrix.Translation(Vector(center)) @ Matrix.Rotation(R(rotz), 4, "Z") @ extra @ Matrix.Scale(s, 4)

sk, skp, sks = fit_import(BK + "49c13194_u.glb", "skull", fx, height=EV("SKS", 0.215))
SKC = tuple(map(float, os.environ.get("SKC", "0,-0.012,1.585").split(",")))
placed(sk, sks, SKC, 0)
SKM = glow_mat("skull_x", (0.85, 0.92, 1.0), 1.3, alpha=0.6, rim=True)
for o in skp: o.data.materials.clear(); o.data.materials.append(SKM)
br, brp, brs = fit_import(BK + "1d697a0b_u.glb", "brain", fx, length=EV("BRL", 0.148), drop_text=False)
BRC = tuple(map(float, os.environ.get("BRC", "0,-0.02,1.618").split(",")))
placed(br, brs, BRC, 0)
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
for o in (sk, br): vis(o, XR_ALL)

# bodomsimon tana (amigdala) — "qadimgi omon qolish markazi"
def W(x, y, z): return tuple(RL(x, y, z))
RED = glow_mat("amyg", (1.0, 0.06, 0.02), 0.0)
red_em = RED.node_tree.nodes[RED["em"]].inputs["Strength"]
AMY_C = (0, BRC[1] + 0.002, BRC[2] - 0.042)
amyg = []
for i, sx in enumerate((-1, 1)):
    a = sphere(f"amyg{i}", 0.0065, W(sx * 0.02, AMY_C[1], AMY_C[2]), RED, sub=2); a.parent = fx; a.scale = (1, 1.4, 1)
    vis(a, XR_ALL); amyg.append(a)
keyval(red_em, 1, 0.0)
def pulse(f0, f1, period, hi_v, lo_v):
    f = f0
    while f < f1:
        keyval(red_em, f, hi_v); keyval(red_em, min(f + 4, f1), lo_v); f += period
pulse(SH["s5"] + 6, SH["s6"] - 1, 10, 60.0, 10.0)          # "o'lib qoldi" — vahima
keyval(red_em, SH["s6"], 2.0)
pulse(SH["s9"] + 8, SH["s10"] - 1, 12, 55.0, 8.0)          # qadimgi markaz
keyval(red_em, SH["s11"], 6.0)
pulse(SH["s11"] + 20, SH["s13"] - 1, 8, 70.0, 16.0)        # qutqarish signali
halo = sphere("amyg_halo", 1.0, W(*AMY_C), glow_mat("halo", (1, 0.08, 0.02), 4.0, alpha=0.5, rim=True), sub=3)
halo.parent = fx
HR = [(SH["s5"] + 6, SH["s6"] - 1), (SH["s9"] + 8, SH["s10"] - 1), (SH["s11"] + 20, SH["s13"] - 1)]
vis(halo, HR)
for a, b in HR:
    f = a
    while f + 18 <= b:
        key(halo, f, scale=0.008); key(halo, f + 18, scale=0.09); f += 18

# yurak va o'pkalar (ko'krak rentgeni)
hfit, hp, hs = fit_import(BK + "652dce3c_u.glb", "heart", fxc, height=EV("HEARTH", 0.12))
HC = tuple(map(float, os.environ.get("HC", "0.018,-0.045,1.2").split(",")))
HM = glow_mat("heart_x", (1.0, 0.12, 0.1), 6.0, alpha=0.9, rim=True, blend=0.6)
hem = HM.node_tree.nodes[HM["em"]].inputs["Strength"]
for o in hp: o.data.materials.clear(); o.data.materials.append(HM)
vis(hfit, XR_ALL)
# yurak urishi: avval 72/min, so'ng sekinlashadi (S6)
hb = empty("heart_beat", (0, 0, 0), fxc)
hb.matrix_basis = groot.matrix_world @ Matrix.Translation(Vector(HC)) @ Matrix.Rotation(R(200), 4, "Z") @ Matrix.Rotation(R(-20), 4, "X")
hfit.parent = hb; hfit.matrix_basis = Matrix.Scale(hs, 4)
hb_s = hb.scale.copy()
f = 1; per = 20.0
while f < END:
    if f >= SH["s6"]: per = min(38.0, per + 2.2)
    hb.scale = hb_s; hb.keyframe_insert("scale", frame=int(f))
    hb.scale = hb_s * 1.16; hb.keyframe_insert("scale", frame=int(f + 3))
    hb.scale = hb_s * 0.97; hb.keyframe_insert("scale", frame=int(f + 6))
    hb.scale = hb_s; hb.keyframe_insert("scale", frame=int(f + 9))
    keyval(hem, int(f), 3.0); keyval(hem, int(f + 3), 14.0); keyval(hem, int(f + 9), 3.0)
    f += per
LUNG = glow_mat("lung_x", (0.45, 0.75, 1.0), 1.6, alpha=0.45, rim=True, blend=0.5)
lungs = []
for sx in (-1, 1):
    l = sphere(f"lung{sx}", 1.0, W(sx * 0.07, -0.02, 1.2), LUNG, sub=3); l.parent = fxc
    l.scale = (0.055, 0.06, 0.11); lungs.append(l); vis(l, XR_ALL)
    f = 1
    while f < END:                                          # nafas: sekin, chuqur
        per = 96 if f < SH["s6"] else 130
        l.scale = (0.055, 0.06, 0.11); l.keyframe_insert("scale", frame=int(f))
        l.scale = (0.062, 0.068, 0.118); l.keyframe_insert("scale", frame=int(f + per / 2))
        f += per

# asab tizimi: ko'k tolalar suyaklar bo'ylab, yashin qizil (scene_bosliq.py dan)
def has(bn): return bn in girl.data.bones
def bpos(bn): return girl.matrix_world @ girl.data.bones[bn].head_local
sc.frame_set(1)
chains = [[P + "Head", P + "Neck", P + "Spine2", P + "Spine1", P + "Spine", P + "Hips"]]
for s in ("Left", "Right"):
    chains.append([P + "Hips", P + s + "UpLeg", P + s + "Leg", P + s + "Foot", P + s + "ToeBase"])
    chains.append([P + "Spine2", P + s + "Shoulder", P + s + "Arm", P + s + "ForeArm", P + s + "Hand"])
segs = []; depth = {P + "Head": 1}
for ch in chains:
    for a_, b_ in zip(ch, ch[1:]):
        if not (has(a_) and has(b_)): continue
        d = depth.get(a_, 1); depth[b_] = d + 1
        segs.append((a_, bpos(a_), bpos(b_), d))
amy_w = Vector(W(*AMY_C))
segs.insert(0, (P + "Head", amy_w, bpos(P + "Neck"), 0))
def follow_rest(o, bn):
    c = o.constraints.new("CHILD_OF"); c.target = girl; c.subtarget = bn
    c.inverse_matrix = (girl.matrix_world @ girl.data.bones[bn].matrix_local).inverted()
def bolt_curve(name, a, b, jitter, depth_=0.0035, n=7):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth_; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); sp.points.add(n - 1)
    d = (b - a); ax = d.normalized(); p1 = ax.orthogonal().normalized(); p2 = ax.cross(p1)
    for i in range(n):
        t = i / (n - 1); p = a.lerp(b, t)
        if 0 < i < n - 1:
            p = p + p1 * random.uniform(-1, 1) * jitter * d.length + p2 * random.uniform(-1, 1) * jitter * d.length
        sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); return o
NERVE = glow_mat("nerve", (0.3, 0.65, 1.0), 2.5)
for si, (bn, a, b, d) in enumerate(segs):
    o = bolt_curve(f"nerve{si}", a, b, 0.03, 0.0018, 4); o.data.materials.append(NERVE); follow_rest(o, bn)
    vis(o, [(SH["s11"], SH["s13"] - 1)])
BOLT = glow_mat("bolt", (1.0, 0.12, 0.04), 45.0)
BOLT2 = glow_mat("bolt_core", (1.0, 0.5, 0.18), 50.0)
WAVES = list(range(BOLT0, SH["s13"] - 6, 9))
for wi, w0 in enumerate(WAVES):
    for si, (bn, a, b, d) in enumerate(segs):
        o = bolt_curve(f"bolt{wi}_{si}", a, b, 0.18)
        o.data.materials.append(BOLT2 if wi % 2 else BOLT); follow_rest(o, bn)
        t = w0 + d; vis(o, [(t, t + 3)], rec=False)
# adrenalin: sariq-to'q sariq zarrachalar buyrak usti bezidan (bel) oyoq-qo'llarga oqadi (poza statik)
sc.frame_set(SH["s12"] + 10)
ADM = glow_mat("adrenalin", (1.0, 0.65, 0.05), 30.0)
def wpos(bn): return girl.matrix_world @ girl.pose.bones[bn].head
paths = []
for s in ("Left", "Right"):
    paths.append([wpos(P + "Spine"), wpos(P + "Hips"), wpos(P + s + "UpLeg"), wpos(P + s + "Leg"), wpos(P + s + "Foot")])
    paths.append([wpos(P + "Spine"), wpos(P + "Spine2"), wpos(P + s + "Arm"), wpos(P + s + "ForeArm"), wpos(P + s + "Hand")])
paths.append([wpos(P + "Spine"), wpos(P + "Spine2"), wpos(P + "Neck"), wpos(P + "Head")])
def polyline(pts, t):
    seg = [(pts[i+1] - pts[i]).length for i in range(len(pts) - 1)]; tot = sum(seg); d = t * tot
    for i, s in enumerate(seg):
        if d <= s or i == len(seg) - 1:
            u = min(1.0, d / s if s else 0); return pts[i].lerp(pts[i+1], u)
        d -= s
for j in range(40):
    pth = paths[j % len(paths)]
    p = sphere(f"adr{j}", random.uniform(0.006, 0.011), (0, 0, 0), ADM, sub=1)
    t0 = ADR0 + random.uniform(0, 22); dur = random.uniform(16, 26)
    jit = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * 0.025
    for f in range(int(t0) - 1, min(SH["s13"], int(t0 + dur) + 2), 2):
        t = max(0.0, min(1.0, (f - t0) / dur))
        p.location = polyline(pth, t) + jit; p.keyframe_insert("location", frame=f)
    vis(p, [(int(t0), min(SH["s13"] - 1, int(t0 + dur)))])

# rentgen foni: to'q ko'k sfera + pastda yupqa to'r (karavot o'rni)
BGM = bpy.data.materials.new("xray_bg"); BGM.use_nodes = True
bg = sphere("xray_bg", 6.0, tuple(GROOM + Vector((0, 0, 0.5))), BGM, sub=4)
N = BGM.node_tree.nodes; L = BGM.node_tree.links; N.clear()
o_ = N.new("ShaderNodeOutputMaterial"); e_ = N.new("ShaderNodeEmission")
gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], gr.inputs[0])
mc_ = N.new("ShaderNodeMix"); mc_.data_type = "RGBA"; mc_.inputs[6].default_value = (0.002, 0.006, 0.02, 1); mc_.inputs[7].default_value = (0.012, 0.03, 0.08, 1)
L.new(gr.outputs["Fac"], mc_.inputs["Factor"]); L.new(mc_.outputs[2], e_.inputs["Color"]); e_.inputs["Strength"].default_value = 1.0
L.new(e_.outputs[0], o_.inputs[0])
bg.visible_shadow = False
vis(bg, XR)
GRID = glow_mat("bed_g", (0.08, 0.25, 0.6), 0.9, alpha=0.35)
gl = box("xr_bed", (BED_HI.x - BED_LO.x - 0.1, BED_HI.y - BED_LO.y - 0.1, 0.004), (BED_CX, BED_CY, MATT - 0.03), GRID)
w_ = gl.modifiers.new("wire", "WIREFRAME"); w_.thickness = 0.004
gl2 = box("xr_bed_fill", (BED_HI.x - BED_LO.x - 0.1, BED_HI.y - BED_LO.y - 0.1, 0.002), (BED_CX, BED_CY, MATT - 0.035), glow_mat("bed_f", (0.03, 0.1, 0.25), 0.5, alpha=0.4))
for o in (gl, gl2): vis(o, XR)
for o in room: vis(o, ROOM_RANGES)

# ================= TUSH 1: tungi osmonda qulash =================
dream = []
CITY = bpy.data.materials.new("city"); CITY.use_nodes = True
N = CITY.node_tree.nodes; L = CITY.node_tree.links; N.clear()
o_ = N.new("ShaderNodeOutputMaterial"); e_ = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord")
vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 0.06
vo2 = N.new("ShaderNodeTexVoronoi"); vo2.inputs["Scale"].default_value = 0.012
L.new(tc.outputs["Object"], vo.inputs["Vector"]); L.new(tc.outputs["Object"], vo2.inputs["Vector"])
r1 = N.new("ShaderNodeMapRange"); r1.inputs[1].default_value = 0.12; r1.inputs[2].default_value = 0.0
L.new(vo.outputs["Distance"], r1.inputs[0])
r2 = N.new("ShaderNodeMapRange"); r2.inputs[1].default_value = 0.08; r2.inputs[2].default_value = 0.0; r2.inputs[4].default_value = 0.35
L.new(vo2.outputs["Distance"], r2.inputs[0])
ad_ = N.new("ShaderNodeMath"); ad_.operation = "ADD"; L.new(r1.outputs[0], ad_.inputs[0]); L.new(r2.outputs[0], ad_.inputs[1])
ml = N.new("ShaderNodeMath"); ml.operation = "MULTIPLY"; ml.inputs[1].default_value = 12.0; L.new(ad_.outputs[0], ml.inputs[0])
e_.inputs["Color"].default_value = (1.0, 0.55, 0.2, 1); L.new(ml.outputs[0], e_.inputs["Strength"]); L.new(e_.outputs[0], o_.inputs[0])
city = plane("city", (9000, 9000), (0, 0, -40.5), CITY)
# tezlik chiziqlari (havo zarralari) — qulash tuyg'usi
STREAK = glow_mat("streak", (0.7, 0.8, 1.0), 3.0, alpha=0.7)
for i in range(70):
    a = random.uniform(0, 2 * math.pi); rr = random.uniform(1.2, 9)
    x, y = GDREAM.x + math.cos(a) * rr, GDREAM.y + math.sin(a) * rr
    s_ = cyl(f"streak{i}", 0.006, random.uniform(0.6, 1.6), (x, y, 0), STREAK, verts=6)
    z0 = GDREAM.z + random.uniform(-60, 10); per = random.uniform(30, 70)
    # zarra deyarli harakatsiz (havoda), qahramon va kamera ular orasidan pastga uchadi
    key(s_, SH["s2"], loc=(x, y, z0)); key(s_, SH["s3"] - 1, loc=(x, y, z0 + random.uniform(-2, 2)))
    dream.append(s_)
CLOUDM = bpy.data.materials.new("cloud"); CLOUDM.use_nodes = True
N = CLOUDM.node_tree.nodes; L = CLOUDM.node_tree.links; N.clear()
o_ = N.new("ShaderNodeOutputMaterial"); e_ = N.new("ShaderNodeEmission"); t_ = N.new("ShaderNodeBsdfTransparent"); m_ = N.new("ShaderNodeMixShader")
ns = N.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 1.6; ns.inputs["Detail"].default_value = 6
gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc = N.new("ShaderNodeTexCoord")
L.new(tc.outputs["Object"], ns.inputs["Vector"]); L.new(tc.outputs["Object"], gr.inputs["Vector"])
mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(ns.outputs["Fac"], mu.inputs[0]); L.new(gr.outputs["Fac"], mu.inputs[1])
mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.12; mr.inputs[2].default_value = 0.45; mr.inputs[4].default_value = 0.6
L.new(mu.outputs[0], mr.inputs[0]); L.new(mr.outputs[0], m_.inputs["Fac"])
e_.inputs["Color"].default_value = (0.35, 0.45, 0.7, 1); e_.inputs["Strength"].default_value = 0.35
L.new(t_.outputs[0], m_.inputs[1]); L.new(e_.outputs[0], m_.inputs[2]); L.new(m_.outputs[0], o_.inputs[0])
for i in range(9):
    c = plane(f"cloud{i}", (1, 1), (GDREAM.x + random.uniform(-25, 25), GDREAM.y + random.uniform(-25, 25), GDREAM.z - 30 - i * 9), CLOUDM)
    c.scale = (random.uniform(18, 30),) * 2 + (1,); dream.append(c)
for o in dream: vis(o, DREAM)

# ================= TUSH 2: daraxt (kunduz) =================
tree_objs = []
GRASS = pbr("grass", "aerial_grass_rock", 0.25)
tree_objs.append(box("grass", (300, 300, 0.1), (GTREE.x, GTREE.y, GTREE.z - 0.05), GRASS))
tr_, tr_ms, tr_dim = import_model(PH + "jacaranda_tree/jacaranda_tree.gltf", "tree", (GTREE.x - 0.6, GTREE.y + 3.2, GTREE.z), 0, height=EV("TREEH", 10.0))
tree_objs.append(tr_)
BARK = pbr("bark", "bark_brown_02", 3.0)
br_ = cyl("branch", 0.09, 2.4, (GTREE.x - 0.1, GTREE.y + 0.12, GTREE.z + BRANCH_Z + 0.06), BARK, rot=(0, 86, 15), verts=16)
tree_objs.append(cyl("limb", 0.13, 3.4, (GTREE.x - 0.45, GTREE.y + 1.75, GTREE.z + BRANCH_Z - 0.35), BARK, rot=(-78, 0, 8), verts=16))
tp = br_.modifiers.new("taper", "SIMPLE_DEFORM"); tp.deform_method = "TAPER"; tp.factor = 0.5; tp.deform_axis = "Z"
tree_objs.append(br_)
for i in range(6):
    b2 = cyl(f"twig{i}", 0.03, random.uniform(0.8, 1.6), (GTREE.x + 0.4 + i * 0.25, GTREE.y + 0.12 + random.uniform(-0.3, 0.3), GTREE.z + BRANCH_Z + 0.25),
             BARK, rot=(random.uniform(-40, 40), random.uniform(20, 60), random.uniform(0, 180)), verts=8)
    tree_objs.append(b2)
for o in tree_objs: vis(o, TREE)

# ================= KAMERALAR =================
cams = []
def camera(name, f0, f1, p0, p1, target, lens, fstop=None, ease="SINE", lens1=None, noise=0.012, parent=None, shake=()):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = 0.01; d.clip_end = 6000
    rig = empty(name + "_rig", (0, 0, 0), parent)
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.parent = rig
    t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop: d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = target
    key(c, f0, loc=tuple(p0)); key(c, f1, loc=tuple(p1))
    if lens1:
        d.lens = lens; d.keyframe_insert("lens", frame=f0); d.lens = lens1; d.keyframe_insert("lens", frame=f1)
    for fc in all_fcurves(c):
        for k in fc.keyframe_points: k.interpolation = ease; k.easing = "EASE_OUT"
        n = fc.modifiers.new("NOISE"); n.scale = 22; n.strength = noise; n.phase = random.uniform(0, 100)
    for (sf, amp, dur) in shake:                 # keskin silkinish (kamera ham "cho'chiydi")
        key(rig, sf - 1, loc=(0, 0, 0))
        for k in range(dur):
            a_ = amp * (1 - k / dur)
            key(rig, sf + k, loc=(random.uniform(-a_, a_), random.uniform(-a_, a_), random.uniform(-a_, a_)))
        key(rig, sf + dur, loc=(0, 0, 0))
    cams.append((f0, c)); return c

def tgt(name, p, parent=None):
    """parent (fx) bo'lsa, p — dam olish pozasidagi dunyo koordinatasi (W/RL), aks holda oddiy dunyo."""
    e = empty(name, (0, 0, 0)); e.location = p; e.parent = parent; return e

sc.frame_set(20)
H = bw("Head") + Vector((0, 0.04, 0.07)); NECK = bw("Neck"); CH = bw("Spine2"); HIP = bw("Hips")
LF = bw("LeftFoot"); RF = bw("RightFoot"); FEET = (LF + RF) / 2
face_t = tgt("t_face", H)
sc.frame_set(20); EYEW = bpy.data.objects["lid1"].matrix_world.translation.lerp(bpy.data.objects["lid-1"].matrix_world.translation, 0.5)
FDIR = (EYEW - bw("Head")).normalized()          # yuz qaragan tomon (+X, chiroq tomonga)
eyew_t = tgt("t_eyew", EYEW)
c1 = camera("c01_face", SH["s1"], SH["s2"] - 1, EYEW + Vector((0.62, -0.28, 0.62)), EYEW + Vector((0.3, -0.12, 0.3)), eyew_t, 50, 2.0, "QUART")
# tush: kamera qahramon bilan birga qulaydi (ildizga bog'langan)
dt = empty("t_dream", (0, 0.1, 0.9), groot)
camera("c02_dream", SH["s2"], SH["s3"] - 1, Vector((0.6, -0.9, -2.3)), Vector((0.35, -0.5, -1.55)), dt, 16, None, "SINE", noise=0.04, parent=groot)
mid_t = tgt("t_mid", (HIP + CH) / 2 + Vector((0, 0, 0.05)))
camera("c03_jerk", SH["s3"], SH["s4"] - 1, Vector((HIP.x + 0.55, BED_LO.y - 0.85, 0.42)), Vector((HIP.x + 0.4, BED_LO.y - 0.6, 0.5)), mid_t, 18, 5.6,
       shake=[(JERK, 0.03, 10)])
bed_t = tgt("t_bed", (BED_CX, BED_CY - 0.2, MATT))
camera("c04_room", SH["s4"], SH["s5"] - 1, Vector((X1 - 0.35, Y0 + 0.35, 2.25)), Vector((X1 - 0.6, Y0 + 0.9, 1.95)), bed_t, 17, None, "SINE")
skc = tgt("t_skull", W(0, -0.01, 1.6), fx)
camera("c05_xray_head", SH["s5"], SH["s6"] - 1, H + Vector((-0.6, 0.02, 0.06)), H + Vector((-0.42, -0.28, 0.3)), skc, 42, 5.6, "QUART")
heart_t = tgt("t_heart", W(*HC), fxc)
camera("c06_heart", SH["s6"], SH["s7"] - 1, CH + Vector((0.3, -0.42, 0.75)), CH + Vector((0.18, -0.26, 0.5)), heart_t, 40, 8.0)
chest_t = tgt("t_chest", CH + Vector((0, 0, 0.08)))
camera("c07_breath", SH["s7"], SH["s8"] - 1, CH + Vector((-1.25, -0.75, -0.18)), CH + Vector((-1.0, -0.35, -0.1)), chest_t, 28, 2.8)
hand_t = tgt("t_hand", (BED_LO.x - 0.12, bw("RightArm").y - 0.12, 0.42))
camera("c08_hand", SH["s8"], SH["s9"] - 1, Vector((BED_LO.x - 0.95, bw("RightArm").y - 0.85, 0.12)), Vector((BED_LO.x - 0.8, bw("RightArm").y - 0.6, 0.16)), hand_t, 24, 2.8)
brain_t = tgt("t_brain", W(0, -0.01, 1.61), fx)
camera("c09_brain", SH["s9"], SH["s10"] - 1, H + Vector((0.42, 0.22, 0.22)), H + Vector((-0.38, 0.12, 0.34)), brain_t, 40, 8.0)
# daraxt: yerdan yuqoriga qarab, son suyagini kuzatadi
hip_t = empty("t_hips"); cl = hip_t.constraints.new("COPY_LOCATION"); cl.target = girl; cl.subtarget = P + "Spine"
camera("c10_tree", SH["s10"], SH["s11"] - 1, GTREE + Vector((1.3, -2.3, 2.3)), GTREE + Vector((1.0, -1.8, 2.6)), hip_t, 20, None, "SINE", noise=0.02)
body_t = tgt("t_body", (CH + HIP) / 2)
camera("c11_xray_top", SH["s11"], SH["s12"] - 1, (CH + HIP) / 2 + Vector((0.12, -0.35, 1.9)), (CH + HIP) / 2 + Vector((0.05, -0.15, 1.45)), body_t, 22, 8.0)
camera("c12_xray_feet", SH["s12"], SH["s13"] - 1, FEET + Vector((0.35, -0.95, 0.02)), FEET + Vector((0.2, -0.65, 0.1)), tgt("t_up", (CH + HIP) / 2), 24, 8.0)
feet_t = tgt("t_feet", FEET + Vector((0, 0.15, 0.1)))
camera("c13_kick", SH["s13"], SH["s14"] - 1, FEET + Vector((1.05, -0.85, 0.42)), FEET + Vector((0.9, -0.7, 0.36)), feet_t, 26, 4.0,
       shake=[(KICK + 1, 0.025, 9)])
eye_t = tgt("t_eye", W(0, EYE[1], EYE[2]), fx)
camera("c14_wake", SH["s14"], END, EYEW + Vector((0.3, -0.14, 0.22)), EYEW + Vector((0.24, -0.1, 0.18)), eye_t, 50, 2.4, shake=[(WAKE + 1, 0.012, 8)])
for f, c in cams: sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = cams[0][1]

# ================= YORUG'LIK =================
w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
bgn = N["Background"]
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Generated"], mp.inputs[0])
mp.inputs["Rotation"].default_value = (0, 0, R(EV("HDRI_ROT", 120)))
night = N.new("ShaderNodeTexEnvironment"); night.image = bpy.data.images.load(PH + "rogland_clear_night.hdr"); L.new(mp.outputs[0], night.inputs[0])
day = N.new("ShaderNodeTexEnvironment"); day.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mp.outputs[0], day.inputs[0])
nb = N.new("ShaderNodeBackground"); db = N.new("ShaderNodeBackground"); L.new(night.outputs[0], nb.inputs[0]); L.new(day.outputs[0], db.inputs[0])
nb.inputs[1].default_value = EV("NIGHT", 2.5); db.inputs[1].default_value = EV("DAY", 1.0)
wm = N.new("ShaderNodeMixShader"); L.new(nb.outputs[0], wm.inputs[1]); L.new(db.outputs[0], wm.inputs[2])
L.new(wm.outputs[0], N["World Output"].inputs[0])
for f, v in ((1, 0), (SH["s10"], 1), (SH["s11"], 0)): keyval(wm.inputs["Fac"], f, v)
for fc in all_fcurves(w.node_tree):
    for k_ in fc.keyframe_points: k_.interpolation = "CONSTANT"
moon = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN")); sc.collection.objects.link(moon)
moon.data.energy = EV("MOON", 1.2); moon.data.angle = R(2.0); moon.data.color = (0.55, 0.68, 1.0)
moon.rotation_euler = (R(58), 0, R(-62))
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = EV("SUN", 3.5); sun.data.angle = R(1.5); sun.data.color = (1.0, 0.88, 0.72); sun.rotation_euler = (R(45), 0, R(EV("SUN_Z", -25)))
for f, e in ((1, 0.0), (SH["s10"], EV("SUN", 3.5)), (SH["s11"], 0.0)): keyval(sun.data, f, e, "energy")
for f, e in ((1, EV("MOON", 1.2)), (SH["s10"], 0.0), (SH["s11"], EV("MOON", 1.2))): keyval(moon.data, f, e, "energy")
for idb in (sun.data, moon.data):
    for fc in all_fcurves(idb):
        for k_ in fc.keyframe_points: k_.interpolation = "CONSTANT"
lamp_lo, lamp_hi = bbox(lamp_ms)
bulb = bpy.data.objects.new("bulb", bpy.data.lights.new("bulb", "POINT")); sc.collection.objects.link(bulb)
bulb.data.energy = EV("BULB", 28); bulb.data.color = (1.0, 0.62, 0.32); bulb.data.shadow_soft_size = 0.06
bulb.location = ((lamp_lo.x + lamp_hi.x) / 2, (lamp_lo.y + lamp_hi.y) / 2, lamp_lo.z + (lamp_hi.z - lamp_lo.z) * 0.72)
def area(name, loc, target, energy, size, col):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.energy = energy; l.data.size = size; l.data.color = col; l.location = loc
    t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l
win = area("window_fill", (X0 + 0.2, (WY0 + WY1) / 2, 1.6), mid_t, EV("WIN", 18), 1.4, (0.55, 0.68, 1.0))
warm = area("face_warm", tuple(H + Vector((0.9, 0.2, 0.9))), face_t, EV("WARM", 6), 0.6, (1.0, 0.7, 0.45))
for l in (bulb, win, warm): vis(l, ROOM_RANGES)
tfill = area("tree_fill", tuple(GTREE + Vector((2.5, -3.5, 3.0))), hip_t, EV("TFILL", 400), 2.5, (1.0, 0.9, 0.8)); vis(tfill, TREE)
for nm, loc, e, col in (("dream_key", (2, -3, 6), EV("DKEY", 900), (0.6, 0.7, 1.0)), ("dream_rim", (-2, 2, -4), EV("DRIM", 700), (1.0, 0.55, 0.3))):
    l = area(nm, loc, dt, e, 3.0, col); l.parent = groot; vis(l, DREAM)

# ================= RENDER =================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 14)); sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 24
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.cycles.blur_glossy = 1.0
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = EV("EXPOSURE", 0.0)
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("DBG_CAM"):                 # sozlash uchun: "x,y,z;tx,ty,tz;lens" (dunyo koordinatasi)
    pc, pt, ln = os.environ["DBG_CAM"].split(";")
    sc.timeline_markers.clear()
    dtg = empty("dbg_t", tuple(map(float, pt.split(","))))
    d = bpy.data.cameras.new("dbg"); d.lens = float(ln); d.clip_start = 0.01; d.clip_end = 6000
    dc = bpy.data.objects.new("dbg", d); sc.collection.objects.link(dc); dc.location = tuple(map(float, pc.split(",")))
    t = dc.constraints.new("TRACK_TO"); t.target = dtg; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    sc.camera = dc

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
