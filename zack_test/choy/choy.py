# Qaynoq choy qizilo'ngachni kuydiradi — Zack D. Films uslubida 42.3 s video (1016 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, hiqichoq.py (yordamchilar), burish/parts.py. Kadr rejasi: STORYBOARD.md
# Render: OUT=/tmp/claude-0/frames_c/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/choy/choy.py --render
# Sinov: FRAMES=20,70,160,320,560 PCT=30
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_c/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
import models as M
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1016
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper large-v3) ----------------
SHOTS = [(1, "hook"), (41, "tea"), (96, "sip"), (126, "xburn"), (206, "xmouth"), (261, "gulp"), (301, "wall"), (384, "temp"),
         (435, "flow"), (472, "cells"), (541, "kill"), (589, "calm"), (637, "nerves"), (685, "daily"), (735, "regen"),
         (813, "dna"), (914, "tumor"), (967, "outro")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM_N = ("hook", "tea", "sip", "gulp", "calm", "daily")
XRAY_N = ("xburn", "xmouth", "nerves", "outro")
STUDIO_N = ("wall", "temp", "dna", "tumor")
MICRO_N = ("cells", "kill", "regen")
ROOM_SHOTS = rng(*ROOM_N); XRAY_SHOTS = rng(*XRAY_N); STUDIO_SHOTS = rng(*STUDIO_N); MICRO_SHOTS = rng(*MICRO_N)
TUNNEL_SHOTS = rng("flow")
BURN = 175        # "kuydirish" (7.28 s)
HOT65 = 400       # "darajadan" — ustun 65 ga yetadi
SCORCH = 556      # "kuyishga" (23.16 s)
ERR = 889         # "xatolik" (37.04 s)
EIGHT = 967       # "sakkiz" (40.28 s)

# ---------------- yordamchilar (hiqichoq.py dan) ----------------
empty = P.empty
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
    for x in objs:
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, sss_scale=None, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if sss_scale is not None: b.inputs["Subsurface Scale"].default_value = sss_scale
    if emit or ecol:
        b.inputs["Emission Color"].default_value = (*(ecol or col), 1); b.inputs["Emission Strength"].default_value = emit
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

WORLD_PARENTS = {"room"}
def _par(o, parent):
    o.parent = parent
    if parent.name in WORLD_PARENTS:
        bpy.context.view_layer.update(); o.matrix_parent_inverse = parent.matrix_world.inverted()

def box(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if parent: _par(o, parent)
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: _par(o, parent)
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: _par(o, parent)
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if parent: _par(o, parent)
    return o

def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.005):
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
    for f in range(f0, f1):
        k = amp * ((1 - (f - f0) / (f1 - f0)) ** 2 if decay else 1.0)
        cam.delta_location = Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("delta_location", frame=f)
    cam.delta_location = (0, 0, 0); cam.keyframe_insert("delta_location", frame=f1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def path_keys(cam, pts):
    for f, p in pts: key(cam, f, loc=p)

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def area(name, loc, size, col, keys, target=None, parent=None, shape=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc; l.visible_camera = False
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, parent=None, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc; l.visible_camera = False
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

val_key = P.mat_value
def scale_vis(o, f0, f1):
    s0 = o.scale.copy()
    o.scale = (0.0001,) * 3; o.keyframe_insert("scale", frame=1); o.keyframe_insert("scale", frame=f1 + 1)
    o.scale = s0; o.keyframe_insert("scale", frame=f0)
    interp(o, "CONSTANT", "scale")

def polyline(pts, t):
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]; tot = sum(seg); d = t * tot
    for i, s in enumerate(seg):
        if d <= s or i == len(seg) - 1:
            return pts[i].lerp(pts[i + 1], min(1.0, d / s if s else 0))
        d -= s

def smooth01(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# ======================================================================
# 1) MEHMONXONA (0,0,0)
# ======================================================================
room = empty("room", (0, 0, 0))
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.5, tint=(0.93, 0.86, 0.76))
plane("floor", (9, 9), (0, 0, 0), floor_m, parent=room)
WY = 2.55
box("wb_l", (4.0, 0.12, 2.9), (-1.45, WY, 1.45), wall_m, parent=room)
box("wb_r", (1.4, 0.12, 2.9), (2.75, WY, 1.45), wall_m, parent=room)
box("wb_b", (1.5, 0.12, 0.85), (1.3, WY, 0.425), wall_m, parent=room)
box("wb_t", (1.5, 0.12, 0.6), (1.3, WY, 2.6), wall_m, parent=room)
frame_m = mat("winframe", (0.92, 0.92, 0.9), 0.35)
for (sx, sz, x, z) in ((1.56, 0.07, 1.3, 0.85), (1.56, 0.07, 1.3, 2.3), (0.07, 1.5, 0.55, 1.575), (0.07, 1.5, 2.05, 1.575),
                       (0.05, 1.5, 1.3, 1.575), (1.56, 0.05, 1.3, 1.6)):
    box("wframe", (sx, 0.09, sz), (x, WY - 0.02, z), frame_m, parent=room)
box("sill", (1.7, 0.25, 0.05), (1.3, WY - 0.1, 0.83), frame_m, parent=room)
glass = mat("glass", (0.9, 0.95, 1.0), 0.02, trans=1.0)
box("glass", (1.5, 0.01, 1.45), (1.3, WY, 1.575), glass, parent=room)
box("w_left", (0.12, 7, 2.9), (-3.4, -0.9, 1.45), wall_m, parent=room)
box("w_right", (0.12, 7, 2.9), (3.4, -0.9, 1.45), wall_m, parent=room)
plane("ceiling", (7, 7), (0, -0.9, 2.9), mat("ceil", (0.92, 0.9, 0.86), 0.8), rot=(180, 0, 0), parent=room)
box("skirting", (6.8, 0.03, 0.09), (0, WY - 0.07, 0.045), frame_m, parent=room)
# gilam (o'zbekona qizil naqsh)
rug = bpy.data.materials.new("rug"); rug.use_nodes = True
N = rug.node_tree.nodes; L = rug.node_tree.links; rb = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; L.new(tc.outputs["Object"], wv.inputs[0])
cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.5, 0.06, 0.05, 1); cr.color_ramp.elements[1].color = (0.85, 0.62, 0.35, 1)
L.new(cr.outputs[0], rb.inputs["Base Color"]); rb.inputs["Roughness"].default_value = 0.95
box("rug", (2.6, 1.8, 0.012), (0.1, -0.2, 0.006), rug, parent=room)
def ph_model(name, loc, rotz=0, scale=1.0):
    e = empty(name, loc, room); e.rotation_euler = (0, 0, R(rotz)); e.scale = (scale,) * 3
    objs = import_gltf(PH + f"{name}/{name}.gltf", e)
    return e, objs
ph_model("Sofa_01", (-0.25, 1.95, 0), 0)
table, tobjs = ph_model("modern_coffee_table_01", (-0.95, -0.75, 0), 90)
TT = bbox(tobjs)[1].z
print("TABLE TOP", TT)
ph_model("potted_plant_01", (-2.6, 2.0, 0), 0, 1.5)
ph_model("potted_plant_01", (2.7, 1.9, 0), 40, 1.2)

# choy: piyola + choynak stol ustida
PAX = M.paxta_mat("paxta")
TEA = M.tea_mat("tea"); M.time_driver(TEA, "boil", 1.0 / 30.0)
TBL = Vector((-0.78, -0.85, TT))
pcup, ptea = M.piyola("piy_table", None, PAX, TEA, tea_level=0.0)
pcup.location = TBL
pot, spout_local = M.choynak("choynak", None, None)
pot.location = TBL + Vector((0.2, 0.06, 0.0)); pot.rotation_euler = (0, 0, R(180 + 15))
TE0, TE1 = S["tea"]
# quyish: choynak ko'tarilib, jo'mrak piyolaga egiladi
POUR0, POUR1 = TE0 + 4, TE1 - 4
POT_UP = TBL + Vector((0.17, 0.05, 0.11))
key(pot, 1, loc=tuple(TBL + Vector((0.2, 0.06, 0.0))), rot=(0, 0, 180 + 15))
key(pot, TE0, loc=tuple(POT_UP), rot=(0, 34, 180 + 15))
key(pot, TE1, loc=tuple(POT_UP + Vector((0.005, 0.0, 0.01))), rot=(0, 38, 180 + 15))
key(pot, TE1 + 1, loc=tuple(TBL + Vector((0.2, 0.06, 0.0))), rot=(0, 0, 180 + 15))
interp(pot, "CONSTANT")
for k_ in [k for fc in fcurves(pot) for k in fc.keyframe_points if TE0 <= k.co.x < TE1]: k_.interpolation = "LINEAR"
# choy oqimi (jo'mrakdan piyolaga)
bpy.context.view_layer.update(); sc.frame_set(TE0 + 10)
sp_w = pot.matrix_world @ Vector(spout_local)
stream_m = mat("stream", (0.45, 0.12, 0.02), 0.03, trans=0.75, coat=1.0)
stream = P.tube("stream", [tuple(sp_w), tuple(sp_w + Vector((-0.04, -0.012, -0.03))), tuple(TBL + Vector((0.01, 0.0, 0.035))),
                           tuple(TBL + Vector((0.0, 0.0, 0.012)))], 0.0045, stream_m, None)
vis(stream, [(POUR0, POUR1)])
# choy sathi ko'tariladi
for f, lv in ((1, 0.15), (POUR0, 0.15), (POUR1, 0.8)):
    ptea.location.z = (0.011 + 0.044 * lv); ptea.keyframe_insert("location", frame=f)
    s_ = 0.55 + 0.45 * lv; ptea.scale = (s_, s_, 1); ptea.keyframe_insert("scale", frame=f)
# qaynash pufakchalari
bub_m = mat("bub", (0.5, 0.2, 0.06), 0.02, trans=0.6, coat=1.0)
rb_ = random.Random(4)
for i in range(18):
    a = rb_.uniform(0, 6.28); rr = rb_.uniform(0, 0.028)
    b_ = sphere(f"bub{i}", rb_.uniform(0.0018, 0.004), (rr * math.cos(a), rr * math.sin(a), 0.0), bub_m, scale=(1, 1, 0.6), sub=2)
    b_.parent = ptea
    st = TE0 + rb_.randint(0, 40); scale_vis(b_, st, st + rb_.randint(4, 10))
steam_tbl, steam_tbl_m = M.steam("steam_tbl", tuple(TBL + Vector((0, 0, 0.04))), 0.06, 0.35, None, density=40.0, seed=1.0)
M.time_driver(steam_tbl_m, "t")
vis(steam_tbl, [S["tea"], S["daily"]])
# timelapse uchun ko'payadigan piyolalar
DA0, DA1 = S["daily"]
extra = []
rp = random.Random(11)
spots = [(-0.55, -0.6), (-0.95, -0.55), (-1.15, -0.8), (-0.6, -1.05), (-1.0, -1.05), (-1.25, -0.5), (-0.75, -0.45), (-1.3, -1.0),
         (-0.45, -0.85), (-0.85, -0.7), (-1.1, -0.65), (-0.5, -1.1)]
for i, (x, y) in enumerate(spots):
    c_, t_ = M.piyola(f"piy_x{i}", None, PAX, M.tea_mat(f"tea_x{i}"), tea_level=rp.uniform(0.0, 0.25))
    c_.location = (x + rp.uniform(-0.03, 0.03), y + rp.uniform(-0.03, 0.03), TT); c_.rotation_euler = (0, 0, rp.uniform(0, 6))
    a = DA0 + 4 + int(i * (DA1 - DA0 - 10) / len(spots))
    scale_vis(c_, a, DA1)
    extra.append(c_)
vis(pcup, rng("tea", "daily")); vis(pot, rng("tea", "daily", "hook", "calm"))
vis(room, ROOM_SHOTS)

# ======================================================================
# 2) BRIAN: bosh barmoq, ho'plash
# ======================================================================
broot, br, bmeshes = mc.load_character("br", "Brian.fbx"); sc.render.fps = 24
def soften(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.45
                    n.inputs["Coat Weight"].default_value = 0.0
soften(bmeshes)
broot.location = (0, 0, 0); broot.rotation_euler = (0, 0, 0)                 # -Y ga (kameraga) qaraydi
A_ = lambda f: mc.load_action(f, True)
IDLE = A_("Breathing_Idle.fbx"); DRINK = A_("Drinking.fbx"); sc.render.fps = 24
# anatomiya nuqtalari suyaklarga bog'lanadi: dunyo koordinatalari Drinking'ning 1-kadri pozasida o'lchangan,
# shuning uchun suyak matritsalari ham shu pozada olinadi (Breathing_Idle da bosh ~3 sm past)
_tmp = mc.add_strip(br, DRINK, 1, blend=0); _tr = br.animation_data.nla_tracks[-1]
sc.frame_set(2); sc.frame_set(1); bpy.context.view_layer.update()
def bone_mat(b):
    m = br.matrix_world @ br.pose.bones["mixamorig:" + b].matrix
    loc, rot, _ = m.decompose()
    return Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
BM = {b: bone_mat(b) for b in ("Head", "Neck", "Spine2", "Spine1", "Spine")}
br.animation_data.nla_tracks.remove(_tr)
mc.add_strip(br, IDLE, -40, blend=0, repeat=12.0)
HEAD_FIX = Vector((0, 0.028, 0))      # sinov renderida og'iz labdan ~3 sm past chiqdi: bosh fazosida tepaga tuzatish
def anchor(name, bone, world):
    loc = BM[bone].inverted() @ Vector(world)
    if bone == "Head": loc += HEAD_FIX
    return child_of_bone(name, br, bone, tuple(loc))
COCKY = A_("Being_Cocky.fbx"); sc.render.fps = 24
def strip(act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(br, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
strip(DRINK, 20, blend=0, bout=10)
strip(COCKY, -6, blend=0, bout=10)                     # "mendan hech narsa o'tmaydi"
for st in (225, 560, 935):
    strip(DRINK, st, src=(30, 200), blend=8, bout=10)

headE = child_of_bone("br_head", br, "Head")
faceT = empty("faceT", (0, 0.07, 0.1), headE)          # yuz markazi (Head: X chap, Y tepa, Z old)
# piyola chap qo'lda
palmE = child_of_bone("br_palm", br, "LeftHand")
cupR = empty("cupR", (0.0, 0.085, 0.04), palmE)
cupR.rotation_euler = (0, R(90), 0)
hcup, htea = M.piyola("piy_hand", None, PAX, TEA, tea_level=0.75)
hcup.parent = cupR; hcup.location = (0, 0, -0.03)
steamR = empty("steamR"); cl = steamR.constraints.new("COPY_LOCATION"); cl.target = hcup
steam_h, steam_h_m = M.steam("steam_hand", (0, 0, 0.045), 0.07, 0.4, steamR, density=30.0, seed=7.0)
M.time_driver(steam_h_m, "t")
CUP_SHOTS = rng("hook", "sip", "xburn", "xmouth", "gulp", "calm", "nerves", "outro")
vis(hcup, CUP_SHOTS); vis(steam_h, rng("hook", "sip", "gulp", "calm"))

# ---- rentgen nusxa ----
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.3, base=0.012)
ghosts = []
for o in bmeshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g); g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, XRAY_SHOTS, recursive=False)
for o in bmeshes: vis(o, [r for r in ROOM_SHOTS if r != S["daily"] and r != S["tea"]], recursive=False)

# qizilo'ngach yo'li: og'izdan oshqozongacha (dunyo, dam holati) -> suyaklarga bog'langan nuqtalar
ESO = [("Head", (0.012, -0.052, 1.574)), ("Head", (0.012, -0.03, 1.566)), ("Neck", (0.012, 0.0, 1.52)),
       ("Neck", (0.012, 0.012, 1.44)), ("Spine2", (0.012, 0.022, 1.33)), ("Spine1", (0.014, 0.02, 1.22)),
       ("Spine", (0.03, 0.005, 1.13)), ("Spine", (0.055, -0.02, 1.095))]
eso_anc = [anchor(f"eso{i}", b, p) for i, (b, p) in enumerate(ESO)]
TRA = [("Neck", (0.012, -0.045, 1.50)), ("Neck", (0.012, -0.04, 1.42)), ("Spine2", (0.012, -0.03, 1.31))]
tra_anc = [anchor(f"tra{i}", b, p) for i, (b, p) in enumerate(TRA)]
eso_m = M.pulse_mat("x_eso", (0.75, 0.25, 0.28), base_emit=0.2, pulse_col=(1.0, 0.18, 0.01), width=0.1, trail=0.9, pulse=14.0)
eso = P.tube("x_esophagus", [p for b, p in ESO], 0.0085, eso_m, None, res=16)
tra_m = M.base_mat("x_trachea", (0.7, 0.85, 1.0), 0.4); tra_m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
tra_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.5, 0.8, 1.0, 1)
tra_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.6
tra = P.tube("x_trachea", [p for b, p in TRA], 0.008, tra_m, None)
# oshqozon
st_m = M.tissue_mat("x_stomach", (0.75, 0.3, 0.32), (0.95, 0.5, 0.5), 30.0, 0.3, coat=0.6, sss=0.4, glow_col=(1.0, 0.4, 0.1))
st_m.node_tree.nodes["glow"].outputs[0].default_value = 0.6
stomR = anchor("stomR", "Spine", (0.085, -0.035, 1.035))
stom = sphere("x_stomach", 1.0, (0, 0, 0), st_m, scale=(0.05, 0.068, 0.036), sub=4); stom.parent = stomR
stom.rotation_euler = (0, 0, R(35))
# og'iz bo'shlig'i, ichida choy, og'riq retseptorlari
mouthR = anchor("mouthR", "Head", (0.012, -0.034, 1.574))
mouth_m = M.tissue_mat("x_mouth", (0.8, 0.35, 0.4), (0.95, 0.55, 0.55), 40.0, 0.3, coat=0.5, sss=0.3, glow_col=(0.25, 0.65, 1.0))
mouth_m.node_tree.nodes["glow"].outputs[0].default_value = 0.4
mouth_m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.4
mouth = sphere("x_mouth", 1.0, (0, 0, 0), mouth_m, scale=(0.021, 0.009, 0.03), sub=4); mouth.parent = mouthR
# (Head fazosi suyak o'qlari dunyoga mos emas — mouthR anchor dunyo yo'nalishini saqlaydi: rotatsiya bosh bilan)
# Head bone matritsasi: X chap, Y tepa, Z old => og'iz ellipsoidi: X eni 3 sm, Y (balandlik) 1.2 sm, Z (chuqurlik) 4.5 sm
hot_m = mat("x_hot", (1.0, 0.4, 0.05), 0.2, emit=6.0, ecol=(1.0, 0.38, 0.04))
mtea = sphere("x_mtea", 1.0, (0, -0.002, 0.005), hot_m, scale=(0.015, 0.0055, 0.022), sub=3); mtea.parent = mouthR
rec_m = mat("rec", (1.0, 0.85, 0.2), emit=0.0, ecol=(1.0, 0.85, 0.2))
rec_n = rec_m.node_tree.nodes["Principled BSDF"]
rec_m.node_tree.links.new(M.value(rec_m, "glow", 0.0), rec_n.inputs["Emission Strength"])
rr_ = random.Random(21); recs = []
for i in range(46):
    u = rr_.uniform(0, 2 * math.pi); v = rr_.uniform(0.2, 2.9)
    n = Vector((math.sin(v) * math.cos(u), math.sin(v) * math.sin(u), math.cos(v)))
    p = Vector((n.x * 0.022, n.y * 0.0095, n.z * 0.031))
    s_ = sphere(f"rec{i}", 0.0012, tuple(p), rec_m, sub=1); s_.parent = mouthR; recs.append(s_)
NE0, NE1 = S["nerves"]
# qizilo'ngachda faqat 3 ta xira retseptor
rec_dim = mat("rec_dim", (1.0, 0.85, 0.2), emit=0.0, ecol=(1.0, 0.85, 0.2))
rdn = rec_dim.node_tree.nodes["Principled BSDF"]
rec_dim.node_tree.links.new(M.value(rec_dim, "glow", 0.0), rdn.inputs["Emission Strength"])
dims = []
for i, k in enumerate((3, 4, 5)):
    s_ = sphere(f"recd{i}", 0.0018, (0.009, -0.004, 0.0), rec_dim, sub=1); s_.parent = eso_anc[k]; dims.append(s_)
# rentgendagi o'sma (yakun)
tumx, tumx_m = M.tumor("x_tumor", None, r=0.016)
tumR = anchor("tumR", "Spine2", (0.014, 0.012, 1.285)); tumx.parent = tumR; tumx.location = (0, 0, 0)
OU0, OU1 = S["outro"]
key(tumx, 1, scale=(0.001,) * 3); key(tumx, OU0 - 1, scale=(0.001,) * 3); key(tumx, OU0, scale=(1, 1, 1))
interp(tumx, "CONSTANT", "scale")
for f in range(OU0, OU1 + 2, 8):
    val_key(tumx_m, "glow", f, 9.0); val_key(tumx_m, "glow", f + 4, 2.5)
X_OBJS = [eso, tra, stom, mouth, mtea, tumx] + recs + dims
for o in X_OBJS: vis(o, XRAY_SHOTS, recursive=False)
vis(mtea, rng("xmouth"))

# qizilo'ngach egri chizig'i nuqtalari suyaklar bilan birga harakatlanadi (har 2 kadrda kalit)
def follow_curve(curve_obj, anchors, ranges):
    sp = curve_obj.data.splines[0]
    frames = sorted({f for a, b in ranges for f in list(range(a - 2, b + 3, 2)) + [b + 1]})
    for f in frames:
        sc.frame_set(f)
        for i, a_ in enumerate(anchors):
            sp.points[i].co = (*a_.matrix_world.translation, 1.0); sp.points[i].keyframe_insert("co", frame=f)
follow_curve(eso, eso_anc, XRAY_SHOTS); follow_curve(tra, tra_anc, XRAY_SHOTS)
# choy impulsi: og'izdan oshqozonga (xburn), "kuydirish"da qizarib yonadi
XB0, XB1 = S["xburn"]
val_key(eso_m, "pos", 1, -0.3); val_key(eso_m, "pos", XB0, -0.15); val_key(eso_m, "pos", XB0 + 50, 1.15)
val_key(eso_m, "pos", XB1, 1.2); val_key(eso_m, "pos", XB1 + 1, -0.3)
val_key(eso_m, "glow", 1, 0.2); val_key(eso_m, "glow", BURN - 2, 0.3); val_key(eso_m, "glow", BURN + 1, 2.5)
val_key(eso_m, "glow", BURN + 14, 1.5); val_key(eso_m, "glow", XB1, 1.2); val_key(eso_m, "glow", XB1 + 1, 0.2)
val_key(st_m, "glow", XB0 + 40, 0.6); val_key(st_m, "glow", XB0 + 55, 2.0); val_key(st_m, "glow", XB1, 1.2); val_key(st_m, "glow", XB1 + 1, 0.6)
# og'iz "qalqoni" (xmouth): ko'k porlash
XM0, XM1 = S["xmouth"]
val_key(mouth_m, "glow", XM0, 0.4); val_key(mouth_m, "glow", XM0 + 12, 3.5)
for f in range(XM0 + 18, XM1, 10): val_key(mouth_m, "glow", f, 2.2); val_key(mouth_m, "glow", f + 5, 3.5)
val_key(mouth_m, "glow", XM1 + 1, 0.4)
# retseptorlar: og'izda chaqnaydi, qizilo'ngachda deyarli yo'q
val_key(rec_m, "glow", 1, 0.0); val_key(rec_m, "glow", NE0, 0.0)
for f in range(NE0 + 2, NE1, 6): val_key(rec_m, "glow", f, 30.0); val_key(rec_m, "glow", f + 3, 10.0)
val_key(rec_m, "glow", NE1 + 1, 0.0)
val_key(rec_dim, "glow", 1, 0.0); val_key(rec_dim, "glow", NE0 + 20, 0.0); val_key(rec_dim, "glow", NE0 + 30, 3.0); val_key(rec_dim, "glow", NE1 + 1, 0.0)
val_key(eso_m, "glow", NE0, 0.2); val_key(eso_m, "glow", NE1, 0.2)
# yakun: yana qaynoq choy oqadi
val_key(eso_m, "pos", OU0, -0.2); val_key(eso_m, "pos", OU1, 1.1)
val_key(eso_m, "glow", OU0, 0.6)

# ×8 yozuvi (kameraga bog'lanadi)
red_txt = mat("red_txt", (1.0, 0.05, 0.03), 0.3, emit=7.0, ecol=(1.0, 0.06, 0.03))

# ======================================================================
# 3) STUDIYA (0,60,0): qizilo'ngach kesimi, termometr, DNK
# ======================================================================
B0 = Vector((0, 60, 0))
studio = empty("studio", tuple(B0))
sfloor = plane("sfloor", (60, 60), tuple(B0), mat("sfloor_m", (0.012, 0.012, 0.018), 0.25, coat=0.4))
vis(sfloor, STUDIO_SHOTS)
S0 = B0 + Vector((0, 0, 1.45))
secR = empty("secR", tuple(S0))
sec, sec_m = M.esophagus_section("sec", secR)
WA0, WA1 = S["wall"]; TU0, TU1 = S["tumor"]
val_key(sec_m["muc"], "glow", 1, 0.0); val_key(sec_m["muc"], "glow", WA0 + 36, 0.0)
for f in range(WA0 + 40, WA1, 12): val_key(sec_m["muc"], "glow", f, 2.5); val_key(sec_m["muc"], "glow", f + 6, 0.8)
val_key(sec_m["muc"], "glow", WA1 + 1, 0.0)
tum, tum_m = M.tumor("tumor", secR, r=0.3)
tum.location = (0.0, 0.42, 0.0)
key(tum, 1, scale=(0.01,) * 3); key(tum, TU0 + 2, scale=(0.02,) * 3); key(tum, TU0 + 40, scale=(1, 1, 0.9)); key(tum, TU1, scale=(1.08, 1.08, 0.97))
for f in range(TU0, TU1 + 2, 10): val_key(tum_m, "glow", f, 6.0); val_key(tum_m, "glow", f + 5, 1.5)
vis(secR, rng("wall", "tumor"))
# termometr
TH = B0 + Vector((8, 0, 0.35))
thR = empty("thR", tuple(TH))
th_root, th_col, th_red, zt = M.thermometer("thermo", thR)
TM0, TM1 = S["temp"]
def col_c(f, c): th_col.scale = (1, 1, zt(c) - 0.1); th_col.keyframe_insert("scale", frame=f)
col_c(1, 22); col_c(TM0, 22); col_c(TM0 + 6, 30); col_c(HOT65 - 2, 69); col_c(HOT65 + 4, 64); col_c(HOT65 + 10, 65.5); col_c(TM1, 65)
val_key(th_red, "glow", TM0, 0.3); val_key(th_red, "glow", HOT65, 4.0); val_key(th_red, "glow", TM1, 2.0)
t65 = M.text("t65", "65°C", 0.3, red_txt, thR, loc=(-0.62, -0.05, zt(65)), rot=(90, 0, 0), extrude=0.03)
key(t65, 1, scale=(0.001,) * 3); key(t65, HOT65 - 1, scale=(0.001,) * 3); key(t65, HOT65 + 3, scale=(1.25,) * 3); key(t65, HOT65 + 7, scale=(1, 1, 1))
th_steam, th_steam_m = M.steam("th_steam", (0, 0.05, zt(65) - 0.1), 0.35, 1.3, thR, density=6.0, seed=3.0)
M.time_driver(th_steam_m, "t", 1.0 / 14.0)
vis(thR, rng("temp"))
# DNK
D0 = B0 + Vector((16, 0, 0.25))
dnaR = empty("dnaR", tuple(D0))
dna_root, rungs, err_m = M.dna("dna", dnaR, n=40)
DN0, DN1 = S["dna"]
key(dna_root, DN0, rot=(0, 0, 0)); key(dna_root, DN1, rot=(0, 0, 160)); interp(dna_root, "LINEAR")
EI = 27                                                     # xato juftlik
vis(dnaR, rng("dna"))
errs = []
for j, h in enumerate(rungs[EI]):
    e = h.copy(); e.data = h.data.copy(); e.data.materials.clear(); e.data.materials.append(err_m); e.name = f"err{j}"
    sc.collection.objects.link(e); e.parent = dna_root; errs.append(e)
    vis(h, [(DN0, ERR - 9)], recursive=False)
    # sinish: yarimlar ajralib, aylanadi
    d = (h.location - Vector((0, 0, h.location.z))).normalized()
    key(e, ERR - 1, loc=tuple(h.location), rot=tuple(math.degrees(a) for a in h.rotation_euler))
    key(e, ERR + 8, loc=tuple(h.location + d * 0.12 + Vector((0, 0, 0.05 * (1 if j else -1)))),
        rot=tuple(math.degrees(a) + (25 if j else -25) for a in h.rotation_euler))
    key(e, DN1, loc=tuple(h.location + d * 0.16 + Vector((0, 0, 0.07 * (1 if j else -1)))),
        rot=tuple(math.degrees(a) + (35 if j else -35) for a in h.rotation_euler))
val_key(err_m, "glow", 1, 0.5); val_key(err_m, "glow", ERR - 8, 1.0); val_key(err_m, "glow", ERR, 12.0); val_key(err_m, "glow", ERR + 12, 5.0)
errT = empty("errT", tuple(rungs[EI][0].location.lerp(rungs[EI][1].location, 0.5)), dna_root)
for e in errs: vis(e, [(max(DN0, ERR - 8), DN1)], recursive=False)

# ======================================================================
# 4) MIKRO DUNYO (30,0,0): hujayralar
# ======================================================================
M0 = Vector((30, 0, 0))
micro = empty("micro", tuple(M0))
cells, cell_m = M.cell_field("cell", micro, nx=24, ny=26, sp=0.17)
plane("mfloor", (8, 8), (0, 0, -0.02), M.tissue_mat("mfloor_m", (0.35, 0.06, 0.08), (0.6, 0.15, 0.17), 4.0, 0.3, coat=0.4, sss=0.3),
      parent=None).parent = micro
# qaynoq choy to'lqini (front x bo'yicha siljiydi)
wave = empty("wave", (0, 0, 0), micro)
wave_m = mat("wave_m", (0.8, 0.3, 0.06), 0.03, trans=0.92, coat=1.0, emit=0.5, ecol=(1.0, 0.4, 0.05))
wb = box("wave_body", (1.1, 5.0, 0.07), (-0.55, 0.0, 0.11), wave_m); wb.parent = wave
wx = wb.modifiers.new("sub", "SUBSURF"); wx.levels = wx.render_levels = 3
tx_w = bpy.data.textures.new("wave_t", "CLOUDS"); tx_w.noise_scale = 0.18
dw = wb.modifiers.new("d", "DISPLACE"); dw.texture = tx_w; dw.strength = 0.05
CE0, CE1 = S["cells"]; KI0, KI1 = S["kill"]; RG0, RG1 = S["regen"]
XMIN, XMAX = -2.4, 2.4
def wave_pass(f0, f1):
    key(wave, f0 - 1, loc=(XMIN - 0.3, 0, -1.0)); key(wave, f0, loc=(XMIN, 0, 0)); key(wave, f1, loc=(XMAX + 2.5, 0, 0))
    key(wave, f1 + 1, loc=(XMAX + 2.5, 0, -1.0))
key(wave, 1, loc=(XMIN - 0.3, 0, -1.0))
PASSES = [(KI0 + 2, KI0 + 40), (RG0 + 26, RG0 + 36), (RG0 + 56, RG0 + 64)]
for a, b in PASSES: wave_pass(a, b)
for fc in fcurves(wave):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
def t_hit(c, a, b):
    """to'lqin old qismi hujayraga yetadigan kadr"""
    return a + (c.location.x - XMIN) / (XMAX + 2.5 - XMIN) * (b - a)
# tutun (kuygan hujayralardan)
smoke_m = bpy.data.materials.new("smoke"); smoke_m.use_nodes = True
Ns = smoke_m.node_tree.nodes; Ls = smoke_m.node_tree.links; Ns.remove(Ns["Principled BSDF"])
pv = Ns.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (0.25, 0.22, 0.2, 1); pv.inputs["Density"].default_value = 6.0
Ls.new(pv.outputs[0], Ns["Material Output"].inputs["Volume"])
rs_ = random.Random(31)
vis(micro, MICRO_SHOTS)
# hujayra holatlari
for c in cells:
    rr = random.Random(int(c.location.x * 1000) * 7 + int(c.location.y * 1000))
    ev = [(1, 0, 0, 0, 1.0)]
    # 1-o'tish (kill)
    t = t_hit(c, *PASSES[0]); t = int(t)
    ev += [(t, 0, 0, 0, 1.0), (t + 3, 0.5, 0, 0, 0.95), (t + 10, 1.0, 0, 0, 0.82)]
    # regen: kuyganlar tushib, yangisi o'sadi (2 marta), keyin oxirgisi
    def regrow(a, kill_pass=None, mut=0.0):
        d1 = a + rr.randint(0, 10); d2 = d1 + 5; g = d2 + rr.randint(2, 8)
        return [(d1, 1.0, 0, 0, 0.8), (d2, 1.0, 0, 0, 0.0), (d2 + 1, 0.0, 1.0, mut, 0.0), (g, 0.0, 1.0, mut, 1.08), (g + 4, 0.0, 0.0, mut, 1.0)]
    ev += regrow(RG0 + 2)
    t2 = int(t_hit(c, *PASSES[1])); ev += [(max(t2, ev[-1][0] + 1), 0, 0, 0, 1.0), (max(t2, ev[-1][0] + 1) + 3, 0.6, 0, 0, 0.92),
                                           (max(t2, ev[-1][0] + 1) + 7, 1.0, 0, 0, 0.82)]
    ev += regrow(ev[-1][0] + 2)
    t3 = int(t_hit(c, *PASSES[2])); t3 = max(t3, ev[-1][0] + 1)
    ev += [(t3, 0, 0, 0, 1.0), (t3 + 3, 0.6, 0, 0, 0.92), (t3 + 7, 1.0, 0, 0, 0.82)]
    mut = 1.0 if rr.random() < 0.05 else 0.0
    ev += regrow(ev[-1][0] + 1, mut=mut)
    last = -1
    for f, b, fr, mu, s in ev:
        f = max(f, last + 1); last = f
        M.cell_state(c, f, burn=b, fresh=fr, mut=mu, scale=s)
    # tutun: 1-o'tishda ba'zi hujayralardan
    if rs_.random() < 0.06:
        sm = sphere(f"smoke{c.name}", 0.05, (c.location.x, c.location.y, 0.08), smoke_m, sub=2); sm.parent = micro
        key(sm, t + 2, loc=(c.location.x, c.location.y, 0.08), scale=(0.3, 0.3, 0.3))
        key(sm, t + 30, loc=(c.location.x + 0.05, c.location.y, 0.6), scale=(1.6, 1.6, 2.2))
        scale_vis_on = (t + 2, min(KI1, t + 30))
        vis(sm, [scale_vis_on], recursive=False)

# ======================================================================
# 5) QIZILO'NGACH ICHI (-30,0,0): endoskop
# ======================================================================
T0 = Vector((-30, 0, 0))
tun = empty("tun", tuple(T0))
tube_in, tun_m = M.tunnel("tunnel", tun, length=3.2)
FL0, FL1 = S["flow"]
plug_m = mat("plug", (0.7, 0.22, 0.03), 0.03, trans=0.4, coat=1.0, emit=1.0, ecol=(1.0, 0.4, 0.05))
plug = sphere("plug", 1.0, (0, 0, 0), plug_m, scale=(0.19, 0.19, 0.35), sub=5); plug.parent = tun
tx_p = bpy.data.textures.new("plug_t", "CLOUDS"); tx_p.noise_scale = 0.4
dp = plug.modifiers.new("d", "DISPLACE"); dp.texture = tx_p; dp.strength = 0.1
key(plug, FL0 - 1, loc=(0, 0, 3.0)); key(plug, FL1, loc=(0, 0, 1.45))
for f, z in ((1, 9.0), (FL0 - 1, 3.0 + 0.35), (FL1, 1.45 + 0.3)): val_key(tun_m, "wz", f, z)
plug_light = point("plug_light", (0, 0, -1.6), 0.1, (1.0, 0.45, 0.1), [(1, 0), (FL0, 2.5), (FL1 + 1, 0)], parent=plug)
vis(tun, TUNNEL_SHOTS)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
HO0, HO1 = S["hook"]; SI0, SI1 = S["sip"]; GU0, GU1 = S["gulp"]; CA0, CA1 = S["calm"]
# 1 ilgak: pastdan keng plan, push-in
hookT = empty("hookT", (0.05, 0, 1.05))
c = shot_cam("hook", (0, 0, 0), hookT, 16, 4.0, focus=faceT)
path_keys(c, ((HO0, (0.55, -2.0, 0.28)), (HO1, (0.35, -1.45, 0.42))))
# 2 choy quyish: makro aylanma
teaT = empty("teaT", tuple(TBL + Vector((0.02, 0, 0.04))))
c = shot_cam("tea", (0, 0, 0), teaT, 42, 2.8, focus=teaT, clip=0.01)
for f in range(TE0, TE1 + 1, 3):
    u = (f - TE0) / (TE1 - TE0); a = R(-150 + 55 * u); rr = 0.36 - 0.06 * u
    key(c, f, loc=tuple(TBL + Vector((rr * math.cos(a), rr * math.sin(a), 0.07 + 0.03 * u))))
interp(c, "LINEAR", "location")
# 3 ho'plash: yuzga yaqin
c = shot_cam("sip", (0, 0, 0), faceT, 50, 2.0, focus=faceT)
path_keys(c, ((SI0, (0.42, -0.85, 1.6)), (SI1, (0.3, -0.7, 1.62))))
# 4 rentgen: bo'yindan ko'krakka kran, "kuydirish"da crash zoom
xbT = empty("xbT", (0, 0, 0))
cl_ = xbT.constraints.new("COPY_LOCATION"); cl_.target = eso_anc[2]
cl2 = xbT.constraints.new("COPY_LOCATION"); cl2.target = eso_anc[6]
for f, inf in ((XB0, 0.0), (XB0 + 55, 1.0), (XB1, 1.0)): cl2.influence = inf; cl2.keyframe_insert("influence", frame=f)
c = shot_cam("xburn", (0, 0, 0), xbT, 30, 5.0, focus=xbT)
path_keys(c, ((XB0, (0.7, -0.95, 1.62)), (XB0 + 55, (0.66, -0.95, 1.3)), (XB1, (0.58, -0.88, 1.25))))
lens_keys(c, ((XB0, 28), (BURN - 2, 30), (BURN + 3, 40), (XB1, 43)))
shake(c, BURN, BURN + 16, 0.03, 3)
# 5 rentgen og'iz: yondan aylanma
c = shot_cam("xmouth", (0, 0, 0), mouthR, 55, 4.0, focus=mouthR)
for f in range(XM0, XM1 + 1, 3):
    u = (f - XM0) / (XM1 - XM0); a = R(-95 + 30 * u)
    key(c, f, loc=(0.55 * math.sin(a) + 0.01, -0.55 * math.cos(a) - 0.03, 1.6 - 0.02 * u))
interp(c, "LINEAR", "location")
# 6 yutish: profildan yaqin plan
c = shot_cam("gulp", (0, 0, 0), faceT, 50, 2.2, focus=faceT)
path_keys(c, ((GU0, (0.85, -0.35, 1.55)), (GU1, (0.68, -0.3, 1.6))))
# 7 studiya: kesim bo'ylab dolly
secT = empty("secT", tuple(S0 + Vector((0.3, 0.0, 0))))
c = shot_cam("wall", (0, 0, 0), secT, 26, 5.6, focus=secT)
key(secT, WA0, loc=tuple(S0 + Vector((0, 0, 0.5)))); key(secT, WA0 + 38, loc=tuple(S0 + Vector((0.15, -0.1, 0.8))))
key(secT, WA1, loc=tuple(S0 + Vector((0.42, -0.36, 1.05))))
path_keys(c, ((WA0, tuple(S0 + Vector((1.6, -3.4, 3.0)))), (WA0 + 38, tuple(S0 + Vector((1.3, -2.7, 2.5)))),
              (WA1, tuple(S0 + Vector((1.05, -1.5, 1.9))))))
lens_keys(c, ((WA0, 26), (WA0 + 38, 28), (WA1, 34)))
# 8 termometr: past burchakdan push-in, ustunga ergashadi
tmT = empty("tmT", (0, 0, 0), thR)
key(tmT, TM0, loc=(-0.2, 0, 0.9)); key(tmT, HOT65, loc=(-0.25, 0, zt(65) - 0.1)); key(tmT, TM1, loc=(-0.25, 0, zt(65) - 0.05))
c = shot_cam("temp", (0, 0, 0), tmT, 26, 4.0, focus=tmT)
path_keys(c, ((TM0, tuple(TH + Vector((0.5, -2.8, 0.2)))), (TM1, tuple(TH + Vector((0.05, -2.0, 0.9))))))
shake(c, HOT65 - 2, HOT65 + 12, 0.04, 4)
# 9 qizilo'ngach ichi: kamera orqaga chekinadi, to'lqin yopiriladi
flT = empty("flT", (0, 0, 3.2), tun)
c = shot_cam("flow", (0, 0, 0), flT, 15, None, clip=0.005)
path_keys(c, ((FL0, tuple(T0 + Vector((0.02, 0.0, 0.95)))), (FL1, tuple(T0 + Vector((0.0, 0.03, 0.3))))))
shake(c, FL0 + 18, FL1 + 1, 0.004, 5, decay=False)
point("scope", (0, 0, 0), 0.02, (1.0, 0.92, 0.85), [(1, 0), (FL0, 4.0), (FL1 + 1, 0)], parent=c)
# 10 hujayralar: past uchish
ceT = empty("ceT", (0, 0, 0), micro)
key(ceT, CE0, loc=(0.2, 0.4, 0.0)); key(ceT, CE1, loc=(0.9, 0.55, 0.0))
c = shot_cam("cells", (0, 0, 0), ceT, 22, 2.8, focus=ceT)
path_keys(c, ((CE0, tuple(M0 + Vector((-1.3, -1.1, 0.42)))), (CE1, tuple(M0 + Vector((-0.1, -0.85, 0.3))))))
# 11 kuyish: yon tomondan
kiT = empty("kiT", (0, 0, 0), micro)
key(kiT, KI0, loc=(-1.1, 0.2, 0.0)); key(kiT, KI1, loc=(1.6, 0.2, 0.0))
c = shot_cam("kill", (0, 0, 0), kiT, 26, 3.5, focus=kiT)
path_keys(c, ((KI0, tuple(M0 + Vector((-1.6, -1.3, 0.55)))), (KI1, tuple(M0 + Vector((1.2, -1.15, 0.45))))))
shake(c, SCORCH, SCORCH + 16, 0.03, 6)
# 12 xotirjam: o'rta plan aylanma
calmT = empty("calmT", (0.03, 0, 1.35))
c = shot_cam("calm", (0, 0, 0), calmT, 32, 3.2, focus=faceT)
for f in range(CA0, CA1 + 1, 3):
    u = (f - CA0) / (CA1 - CA0); a = R(-35 + 30 * u)
    key(c, f, loc=(1.55 * math.sin(a), -1.55 * math.cos(a), 1.45))
interp(c, "LINEAR", "location")
# 13 rentgen: og'izdan pastga tilt
neT = empty("neT", (0, 0, 0))
c1 = neT.constraints.new("COPY_LOCATION"); c1.target = mouthR
c2 = neT.constraints.new("COPY_LOCATION"); c2.target = eso_anc[5]
for f, inf in ((NE0, 0.0), (NE0 + 18, 0.0), (NE0 + 40, 1.0), (NE1, 1.0)): c2.influence = inf; c2.keyframe_insert("influence", frame=f)
c = shot_cam("nerves", (0, 0, 0), neT, 40, 4.0, focus=neT)
path_keys(c, ((NE0, (0.45, -0.5, 1.66)), (NE0 + 18, (0.45, -0.52, 1.62)), (NE0 + 40, (0.48, -0.55, 1.32)), (NE1, (0.44, -0.52, 1.25))))
# 14 timelapse: stol ustiga sekin push-in
daT = empty("daT", tuple(Vector((-0.9, -0.8, TT + 0.03))))
c = shot_cam("daily", (0, 0, 0), daT, 30, 4.0, focus=daT)
path_keys(c, ((DA0, (0.0, -1.85, 0.95)), (DA1, (-0.15, -1.6, 0.85))))
# 15 qayta tiklanish: tepadan aylanma
rgT = empty("rgT", (0.0, 0.2, 0.0), micro)
c = shot_cam("regen", (0, 0, 0), rgT, 30, 4.0, focus=rgT)
for f in range(RG0, RG1 + 1, 3):
    u = (f - RG0) / (RG1 - RG0); a = R(-20 + 60 * u)
    key(c, f, loc=tuple(M0 + Vector((1.25 * math.sin(a), -1.25 * math.cos(a), 1.05 - 0.15 * u))))
interp(c, "LINEAR", "location")
# 16 DNK: kran tepaga, "xatolik"da crash zoom
dnT = empty("dnT", (0, 0, 0))
cd1 = dnT.constraints.new("COPY_LOCATION"); cd1.target = errT
key(dnT, DN0, loc=tuple(D0 + Vector((0, 0, 0.6)))); key(dnT, ERR - 25, loc=tuple(D0 + Vector((0, 0, 2.2))))
for f, inf in ((DN0, 0.0), (ERR - 25, 0.0), (ERR - 6, 1.0), (DN1, 1.0)): cd1.influence = inf; cd1.keyframe_insert("influence", frame=f)
c = shot_cam("dna", (0, 0, 0), dnT, 30, 4.0, focus=dnT)
path_keys(c, ((DN0, tuple(D0 + Vector((1.9, -2.4, 0.3)))), (ERR - 25, tuple(D0 + Vector((1.7, -2.3, 2.3)))),
              (DN1, tuple(D0 + Vector((1.5, -2.1, errT.location.z + 0.35))))))
lens_keys(c, ((DN0, 26), (ERR - 2, 28), (ERR + 3, 42), (DN1, 46)))
shake(c, ERR, ERR + 14, 0.03, 7)
# 17 o'sma: kesimga push-in
tuT = empty("tuT", (0, 0.42, 0.0), secR)
c = shot_cam("tumor", (0, 0, 0), tuT, 34, 4.0, focus=tuT)
path_keys(c, ((TU0, tuple(S0 + Vector((0.6, -2.4, 0.45)))), (TU1, tuple(S0 + Vector((0.12, -1.25, 0.12))))))
# 18 yakun: o'smadan tez orqaga chekinish
c = shot_cam("outro", (0, 0, 0), tumR, 55, 4.0, focus=tumR)
path_keys(c, ((OU0, (0.18, -0.32, 1.32)), (OU0 + 6, (0.3, -0.6, 1.36)), (OU1, (1.0, -2.7, 1.5))))
lens_keys(c, ((OU0, 55), (OU1, 26)))
shake(c, EIGHT, EIGHT + 10, 0.02, 8)
t8 = M.text("t8", "×8", 0.08, red_txt, c, loc=(0.0, 0.135, -0.5), rot=(0, 0, 0), extrude=0.006)
key(t8, 1, scale=(0.001,) * 3); key(t8, EIGHT + 1, scale=(0.001,) * 3); key(t8, EIGHT + 5, scale=(1.3,) * 3); key(t8, EIGHT + 9, scale=(1, 1, 1))
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 7) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(200)); L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
bg_sky = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_sky.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.003, 0.008, 0.02, 1)
bg_mi = N.new("ShaderNodeBackground"); bg_mi.inputs[0].default_value = (0.09, 0.015, 0.02, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_sky.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1])
a2 = N.new("ShaderNodeAddShader"); L.new(a1.outputs[0], a2.inputs[0]); L.new(bg_mi.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    vals = (1.0, 0.0, 0.0) if n in ROOM_N else ((0.0, 0.0, 1.0) if n in MICRO_N else (0.0, 1.0, 0.0))
    for bgn, v in zip((bg_sky, bg_dk, bg_mi), vals):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.0); sun.data.color = (1.0, 0.9, 0.78); sun.rotation_euler = (R(62), 0, R(160))
for f, e in lights_for(ROOM_SHOTS, 4.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
# timelapse: quyosh tez aylanadi, kun-tun
for f, rz, e in ((DA0, 120, 4.5), (DA0 + 16, 200, 6.0), (DA0 + 30, 250, 0.4), (DA0 + 38, 120, 0.3), (DA1, 170, 5.0)):
    sun.rotation_euler = (R(62), 0, R(rz)); sun.keyframe_insert("rotation_euler", frame=f)
    sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
for fc in fcurves(sun.data):
    for k in fc.keyframe_points:
        if DA0 <= k.co.x < DA1: k.interpolation = "LINEAR"
area("win_key", (1.3, WY - 0.3, 1.6), 1.4, (0.92, 0.96, 1.0), lights_for(ROOM_SHOTS, 260.0), target=faceT, shape=(1.4, 1.4))
area("face_fill", (-0.9, -1.5, 1.8), 0.9, (1.0, 0.9, 0.8), lights_for(ROOM_SHOTS, 70.0), target=faceT)
area("face_rim", (-0.8, 1.2, 2.1), 0.6, (1.0, 0.82, 0.62), lights_for(ROOM_SHOTS, 90.0), target=faceT)
area("ceil_bounce", (0, -0.6, 2.75), 2.5, (1.0, 0.93, 0.85), lights_for(ROOM_SHOTS, 120.0), target=hookT)
area("tea_key", tuple(TBL + Vector((-0.4, -0.3, 0.5))), 0.4, (1.0, 0.9, 0.8), lights_for(rng("tea"), 25.0), target=teaT)
area("tea_rim", tuple(TBL + Vector((0.3, 0.45, 0.35))), 0.4, (1.0, 0.7, 0.45), lights_for(rng("tea"), 30.0), target=teaT)
# rentgen
area("x_rim", (-0.8, 0.4, 2.0), 0.8, (0.3, 0.6, 1.0), lights_for(XRAY_SHOTS, 40.0), target=faceT)
area("x_key", (0.6, -0.9, 1.6), 0.5, (1.0, 0.9, 0.9), lights_for(XRAY_SHOTS, 12.0), target=hookT)
# studiya
for nm, T_, rngs in (("sec", secT, rng("wall", "tumor")), ("th", tmT, rng("temp")), ("dn", dnT, rng("dna"))):
    base = {"sec": S0, "th": TH + Vector((0, 0, 1.2)), "dn": D0 + Vector((0, 0, 2.0))}[nm]
    area(f"{nm}_key", tuple(base + Vector((-2.0, -2.2, 1.8))), 1.6, (1.0, 0.93, 0.88), lights_for(rngs, 420.0), target=T_)
    area(f"{nm}_rim", tuple(base + Vector((2.0, 1.8, 1.4))), 1.6, (0.3, 0.6, 1.0), lights_for(rngs, 650.0), target=T_)
    area(f"{nm}_rim2", tuple(base + Vector((-1.8, 1.6, -0.6))), 1.2, (1.0, 0.45, 0.4), lights_for(rngs, 280.0), target=T_)
point("sec_in", tuple(S0 + Vector((0, -0.2, 0.0))), 0.2, (1.0, 0.85, 0.8), lights_for(rng("wall", "tumor"), 30.0))
point("tum_burst", tuple(S0 + Vector((0, 0.1, 0.0))), 0.2, (1.0, 0.15, 0.08), lights_for(rng("tumor"), 25.0))
point("err_burst", (0, 0, 0), 0.1, (1.0, 0.1, 0.05), [(1, 0), (ERR, 120.0), (ERR + 6, 30.0), (DN1 + 1, 0)], parent=errT, const=False)
# mikro
mT = empty("mT", tuple(M0))
area("m_key", tuple(M0 + Vector((-1.5, -1.8, 2.2))), 2.0, (1.0, 0.9, 0.88), lights_for(MICRO_SHOTS, 200.0), target=mT)
area("m_rim", tuple(M0 + Vector((1.8, 2.0, 1.0))), 2.0, (1.0, 0.5, 0.45), lights_for(MICRO_SHOTS, 260.0), target=mT)
area("m_top", tuple(M0 + Vector((0, 0, 3.0))), 3.0, (1.0, 0.85, 0.85), lights_for(MICRO_SHOTS, 120.0), target=mT)
wl = point("wave_light", (0.15, 0, 0.25), 0.3, (1.0, 0.45, 0.1), lights_for(rng("kill", "regen"), 25.0), parent=wave)

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.1
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    os.makedirs(OUT, exist_ok=True)
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
