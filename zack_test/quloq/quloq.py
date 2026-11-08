# "Quloqqa tarakan kirsa nima bo'ladi?" — Zack D. Films uslubida 47.4 s video (1138 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, aksirish/aksirish.py (yordamchilar, rentgen, render sozlamalari).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_quloq.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/quloq/quloq.py --render
# Sinov: FRAMES=20,70,250,520,700 PCT=30
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1138
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper: words.json) ----------------
SHOTS = [(1, "hook"), (41, "enter"), (93, "spider"), (152, "xhead"), (203, "canal"), (292, "back"), (364, "forward"),
         (469, "drum"), (561, "thunder"), (639, "wake"), (690, "swab"), (759, "tear"), (852, "oilwide"), (925, "drop"),
         (1000, "choke"), (1068, "out")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
def T(sec): return int(round(sec * 24)) + 1           # ovoz vaqti -> kadr

ROOM_SHOTS = rng("hook", "enter", "spider", "wake", "swab", "oilwide", "drop", "out")
X_SHOTS = rng("xhead", "thunder")
CANAL_SHOTS = rng("canal", "back", "forward", "drum", "tear", "choke")

# ---------------- yordamchilar (aksirish.py dan) ----------------
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

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, sss_scale=None, emit_col=None, ior=1.45):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["IOR"].default_value = ior
    if sss_scale is not None: b.inputs["Subsurface Scale"].default_value = sss_scale
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

def _par(o, parent):
    o.parent = parent
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

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None, world=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r, location=loc) if sub >= 4 else \
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent:
        if world: _par(o, parent)
        else: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if parent: _par(o, parent)
    return o

def import_gltf(path, parent):
    before = set(bpy.data.objects); ba = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.name.startswith("Icosphere"):          # BlenderKit yordamchi sferasi (2 m)
            new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    for o in new:
        if o.parent is None: o.parent = parent
    return new, [a for a in bpy.data.actions if a not in ba]

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

def area(name, loc, size, col, keys, target=None, parent=None, shape=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    l.visible_camera = cam_vis
    return l

def point(name, loc, r, col, keys, parent=None, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)
def lerp3(a, b_, t, e=True):
    t = ease(t) if e else t; return tuple(Vector(a).lerp(Vector(b_), t))

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
def val_key(m, name, f, v): P.mat_value(m, name, f, v)

def catmull(pts, step=0.004):
    P_ = [Vector(p) for p in pts]; P_ = [P_[0] * 2 - P_[1]] + P_ + [P_[-1] * 2 - P_[-2]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n = max(2, int((p2 - p1).length / step))
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P_[-2])
    return out

def wpos(o, f, local=(0, 0, 0)):
    sc.frame_set(f); return o.matrix_world @ Vector(local)

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

def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm, act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
def place(root, f, loc, rot=0.0, scale=1.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
    for p in ("location", "rotation_euler", "scale"): root.keyframe_insert(p, frame=f)

def ray_down(objs, x, y, z0=3.0):
    """ob'ektlar ustidagi eng baland nuqta (x, y) da"""
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    for o in objs:
        if o.type != "MESH": continue
        mi = o.matrix_world.inverted(); org = mi @ Vector((x, y, z0)); dr = (mi.to_3x3() @ Vector((0, 0, -1))).normalized()
        ok, loc, nor, idx = o.evaluated_get(dg).ray_cast(org, dr)
        if ok:
            z = (o.matrix_world @ loc).z
            best = z if best is None else max(best, z)
    return best

# ======================================================================
# 1) YOTOQXONA (0,0,0): tun, oy yorug'i + tungi chiroq. Karavot boshi +Y da.
# ======================================================================
room = empty("room", (0, 0, 0))
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.4, tint=(0.62, 0.7, 0.82))
plane("floor", (8, 8), (0, 0, 0), floor_m, parent=room)
plane("wall_back", (8, 3), (0, 1.45, 1.5), wall_m, rot=(90, 0, 0), parent=room)
plane("wall_left", (8, 3), (-2.6, 0, 1.5), wall_m, rot=(90, 0, 90), parent=room)
plane("wall_right", (8, 3), (2.8, 0, 1.5), wall_m, rot=(90, 0, -90), parent=room)
plane("wall_front", (8, 3), (0, -3.2, 1.5), wall_m, rot=(90, 0, 180), parent=room)
plane("ceiling", (8, 8), (0, 0, 2.7), mat("ceil", (0.85, 0.86, 0.88), 0.8), rot=(180, 0, 0), parent=room)
# deraza (chap devor): tungi osmon + oy
win_m = mat("win_night", (0.18, 0.3, 0.6), 0.0, emit=1.2)
plane("window", (1.3, 1.4), (-2.59, -0.3, 1.5), win_m, rot=(90, 0, 90), parent=room)
frame_m = mat("win_frame", (0.9, 0.9, 0.9), 0.35)
for dz in (-0.71, 0.71): box("wframe", (0.06, 1.36, 0.05), (-2.56, -0.3, 1.5 + dz), frame_m, parent=room)
for dy in (-0.66, 0.0, 0.66): box("wframe", (0.06, 0.05, 1.45), (-2.56, -0.3 + dy, 1.5), frame_m, parent=room)
cur_m = mat("curtain", (0.25, 0.32, 0.45), 0.9, sss=0.1)
for dy in (-1.0, 0.4):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=2, size=1, location=(-2.5, -0.3 + dy, 1.35), rotation=(R(90), 0, R(90)))
    c_ = bpy.context.object; c_.name = "curtain"; c_.scale = (0.45, 2.5, 1); bpy.ops.object.transform_apply(scale=True)
    for v in c_.data.vertices: v.co.z += 0.025 * math.sin(v.co.x * 55)
    c_.data.materials.append(cur_m); _par(c_, room)
    for p_ in c_.data.polygons: p_.use_smooth = True
# karavot (BlenderKit 9d002926) — o'lchami 1.96 x 2.09, boshi +Y
bedR = empty("bedR", (0, 0, 0), room)
bed_objs, _ = import_gltf(BK + "9d002926_u.glb", bedR)
for o in list(bed_objs):                          # o'rta yostiqlar boshni ko'mib yuboradi: olib tashlaymiz
    if o.name.startswith(("Mid White Pillow", "Orange Pillow")):
        bed_objs.remove(o); bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()
MAT_Z = ray_down(bed_objs, -0.4, -0.2) or 0.49          # matras usti
print("MAT_Z", MAT_Z)
# o'z yostig'imiz (bosh ostida, yumshoq)
pil_m = mat("pillow", (0.86, 0.88, 0.92), 0.85, sss=0.15, sss_scale=0.01)
pillow = box("pillow", (0.62, 0.42, 0.1), (-0.52, 0.43, MAT_Z + 0.05), pil_m, parent=room)
bv = pillow.modifiers.new("bev", "BEVEL"); bv.width = 0.045; bv.segments = 4
sb = pillow.modifiers.new("s", "SUBSURF"); sb.levels = 1; sb.render_levels = 2
for p_ in pillow.data.polygons: p_.use_smooth = True
pc_m = mat("pillow_case", (0.86, 0.88, 0.92), 0.9)
# tungi stol + chiroq (karavotning chap tomoni, x<0)
ns_m = mat("nightstand", (0.32, 0.2, 0.12), 0.45, coat=0.2)
box("nightstand", (0.45, 0.4, 0.55), (-1.35, 1.15, 0.275), ns_m, parent=room)
lampL_m = mat("lamp_shade2", (1.0, 0.8, 0.55), 0.6, emit=4.0, emit_col=(1.0, 0.7, 0.4), sss=0.2)
cyl("nlamp_base", 0.07, 0.25, (-1.35, 1.2, 0.675), mat("lamp_base2", (0.85, 0.82, 0.78), 0.3), parent=room)
cyl("nlamp_shade", 0.13, 0.2, (-1.35, 1.2, 0.9), lampL_m, parent=room)
box("phone", (0.075, 0.155, 0.009), (-1.27, 1.02, 0.555), mat("phone", (0.02, 0.02, 0.025), 0.15, coat=1.0), rot=(0, 0, 20), parent=room)
# quloq tayoqchalari qutisi + yog' shishasi (stol ustida)
plantR = empty("plantR", (2.2, 1.1, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR)
picR = empty("picR", (0.0, 1.44, 1.75), room); picR.scale = (1.8, 1.8, 1.8)
import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR)
rug_m = mat("rug", (0.5, 0.45, 0.4), 0.95)
plane("rug", (2.6, 1.6), (0.0, -1.5, 0.004), rug_m, parent=room)

# ======================================================================
# 2) BRIAN (yigit) va KATE (ayol)
# ======================================================================
broot, bri, bmeshes = mc.load_character("bri", "Brian.fbx"); sc.render.fps = 24
soften(bmeshes)
kroot, kat, kmeshes = mc.load_character("kat", "Kate.fbx"); sc.render.fps = 24
soften(kmeshes)
headE = child_of_bone("bri_head", bri, "Head")
# o'ng quloq (Head fazosi: X chap, Y tepa, Z old) — o'lchangan: chig'anoq tubi (-0.059, 0.053, 0.022)
EAR = Vector((-0.06, 0.053, 0.021))
earE = empty("earE", tuple(EAR), headE)
earOut = empty("earOut", tuple(EAR + Vector((-0.03, 0.0, 0.0))), headE)

# yotish: Laying_Sleeping (bosh +Y, yuz +X ga burilgan, o'ng quloq tepaga qaragan). Hips root dan ~1.06 m baland.
SLEEP_ROOT = (-0.55, -0.13, MAT_Z - 0.9)
SLEEP_TILT = 7.0                                # boshi yostiqqa ko'tarilsin (X o'qi atrofida)
SIT_ROOT = (0.62, -0.35, MAT_Z - 0.47)        # karavot chetida o'tirish (+X ga qaraydi)
def place_sleep(f):
    place(broot, f, SLEEP_ROOT); broot.rotation_euler = (R(SLEEP_TILT), 0, 0); broot.keyframe_insert("rotation_euler", frame=f)
place_sleep(1)
place(broot, S["wake"][0], SIT_ROOT, rot=90)
place_sleep(S["oilwide"][0])
interp(broot, "CONSTANT")
SL = A_("Laying_Sleeping.fbx")
mc.add_strip(bri, SL, -20, blend=0, repeat=(S["wake"][0] + 30) / 52.0 * 0.8)
strip(bri, A_("Sitting_Disbelief_3.fbx"), S["wake"][0] - 20, blend=0, bout=4, src=(20, 159))
strip(bri, A_("Sitting_Idle_4.fbx"), S["swab"][0] - 2, blend=0, bout=0, repeat=2.0)
strip(bri, SL, S["oilwide"][0], blend=0, bout=0, repeat=(END - S["oilwide"][0] + 10) / 52.0 * 0.8)

# Kate: faqat yog' kadrlarida, karavotning chap tomonida turadi (+X ga qaraydi)
KATE_ROOT = (-1.08, 0.58, 0.0)
place(kroot, 1, (0, -60, 0))
place(kroot, S["oilwide"][0], KATE_ROOT, rot=90)
interp(kroot, "CONSTANT")
mc.add_strip(kat, A_("Breathing_Idle.fbx"), S["oilwide"][0] - 30, blend=0, repeat=4.0)
vis(kroot, [(S["oilwide"][0], END)])

sc.frame_set(20); bpy.context.view_layer.update()

# ---- teri sirti (Head fazosida) — chig'anoq bo'ylab yo'l uchun ----
def head_bvh(f=20):
    sc.frame_set(f); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    body = next(m for m in bmeshes if m.name.endswith("Body"))
    e = body.evaluated_get(dg); me = e.to_mesh()
    inv = headE.matrix_world.inverted()
    vs = [inv @ (e.matrix_world @ v.co) for v in me.vertices]
    bvh = BVHTree.FromPolygons(vs, [p.vertices[:] for p in me.polygons]); e.to_mesh_clear()
    return bvh
HBVH = head_bvh(20)
def skin(y, z, lift=0.0):
    loc, nor, i, d = HBVH.ray_cast(Vector((-0.16, y, z)), Vector((1, 0, 0)))
    if loc is None: return Vector((-0.06, y, z)), Vector((-1, 0, 0))
    if nor.x > 0: nor = -nor
    return loc + nor * lift, nor.normalized()
HOLE_P, HOLE_N = skin(EAR.y, EAR.z)
print("HOLE", HOLE_P, HOLE_N)

# ---- hasharotlar ----
def frame_q(fwd, up):
    """+Y = oldinga, +Z = tepa"""
    y = Vector(fwd).normalized(); z = Vector(up); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_quaternion()

def bug(name, glb, scale, parent=None, speed=1.0, act_len=49.0):
    rootE = empty(name, (0, 0, 0), parent); rootE.rotation_mode = "QUATERNION"
    new, acts = import_gltf(BK + glb, rootE)
    rootE.scale = (scale,) * 3
    arm = next(o for o in new if o.type == "ARMATURE")
    ad = arm.animation_data; act = ad.action if ad else None
    if act:
        ad.action = None
        tr = ad.nla_tracks.new(); s_ = tr.strips.new(act.name, 1, act)
        if hasattr(s_, "action_slot") and act.slots: s_.action_slot = act.slots[0]
        s_.scale = 1.0 / speed; s_.repeat = (END + 10) / (act_len / speed); s_.extrapolation = "HOLD"
    for o in new:
        if o.type == "MESH":
            for p_ in o.data.polygons: p_.use_smooth = True
    rootE["arm"] = arm.name
    return rootE, arm, new

_LASTQ = {}
def bug_key(b, f, pos, fwd, up):
    b.location = pos; b.keyframe_insert("location", frame=f)
    q = frame_q(fwd, up); lq = _LASTQ.get(b.name)
    if lq is not None and lq.dot(q) < 0: q = -q             # kvaternion ishorasi sakramasin
    _LASTQ[b.name] = q.copy()
    b.rotation_quaternion = q; b.keyframe_insert("rotation_quaternion", frame=f)

def bug_path(b, f0, f1, pts, ups, step=2, ease_=False, wiggle=0.0, seed=1):
    """pts: nuqtalar (b ota-onasi fazosida), ups: har nuqta uchun tepa vektori"""
    rnd = random.Random(seed)
    dense = catmull(pts, 0.0005 * max(0.2, b.scale[0] / 0.1)); n = len(dense)
    L_ = [0.0]
    for i in range(1, n): L_.append(L_[-1] + (dense[i] - dense[i - 1]).length)
    tot = L_[-1] or 1e-6
    def at(s):
        for i in range(1, n):
            if L_[i] >= s:
                t = (s - L_[i - 1]) / max(1e-9, L_[i] - L_[i - 1]); return dense[i - 1].lerp(dense[i], t), i
        return dense[-1], n - 1
    def up_at(u):
        k = u * (len(ups) - 1); i = min(int(k), len(ups) - 2); t = k - i
        return Vector(ups[i]).lerp(Vector(ups[i + 1]), t)
    for f in list(range(f0, f1, step)) + [f1]:
        u = (f - f0) / max(1, f1 - f0); u = ease(u) if ease_ else u
        p, i = at(u * tot); p2, _ = at(min(tot, u * tot + tot * 0.03 + 1e-5))
        fwd = (p2 - p) if (p2 - p).length > 1e-7 else (dense[-1] - dense[-2])
        up = up_at(u)
        if wiggle: fwd = fwd.normalized() + up.cross(fwd.normalized()) * rnd.uniform(-wiggle, wiggle)
        bug_key(b, f, tuple(p), fwd, up)

# 1) yostiqdagi tarakan (dunyo) — ilgak
ROACH_S = 0.11                                       # ~1.6 sm
roachP, roachP_arm, _ = bug("roachP", "e34efe7c_u.glb", ROACH_S, speed=1.6)
EAR_W = wpos(earE, 20); EARN_W = (headE.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
PIL_TOP = ray_down([pillow], EAR_W.x - 0.12, EAR_W.y - 0.02) or (MAT_Z + 0.1)
print("EAR_W", EAR_W, "EARN_W", EARN_W, "PIL_TOP", PIL_TOP)
H0, H1 = S["hook"]
hook_pts = [(EAR_W.x - 0.24, EAR_W.y - 0.10, PIL_TOP), (EAR_W.x - 0.17, EAR_W.y - 0.05, PIL_TOP),
            (EAR_W.x - 0.11, EAR_W.y - 0.035, PIL_TOP), (EAR_W.x - 0.07, EAR_W.y - 0.02, PIL_TOP + 0.004)]
bug_path(roachP, H0, H1 + 3, hook_pts, [(0, 0, 1), (0, 0, 1)], wiggle=0.15)
vis(roachP, [S["hook"]])

# 2) quloqqa kirayotgan tarakan (Head fazosi)
roachE, roachE_arm, _ = bug("roachE", "e34efe7c_u.glb", ROACH_S, parent=headE, speed=1.8)
EN0, EN1 = S["enter"]
ear_path = [skin(0.098, -0.012, 0.0012), skin(0.088, 0.0, 0.0012), skin(0.075, 0.01, 0.0012), skin(0.064, 0.017, 0.001),
            skin(0.057, 0.02, 0.0008)]
P_ = [p for p, n in ear_path] + [HOLE_P + Vector((0.008, 0, 0.001)), HOLE_P + Vector((0.02, -0.001, 0.003)), HOLE_P + Vector((0.026, -0.001, 0.004))]
U_ = [n for p, n in ear_path] + [Vector((-0.3, 1, 0)), Vector((-0.2, 1, 0)), Vector((-0.2, 1, 0))]
bug_path(roachE, EN0, EN1 + 1, P_, U_, wiggle=0.1, seed=3)
# 16) yog' bilan qalqib chiqish: teskari yo'l (orqaga), keyin yostiqqa sirpanadi
OU0, OU1 = S["out"]
F_OUT = T(45.5)
out_pts = [HOLE_P + Vector((0.02, 0, 0.003)), HOLE_P + Vector((0.004, 0, 0.001)), HOLE_P + Vector((-0.006, 0.0, 0.0)),
           skin(0.045, 0.03, 0.004)[0], skin(0.03, 0.035, 0.01)[0] + Vector((-0.012, 0, 0))]
key(roachE, OU0, loc=tuple(out_pts[0]))
bug_path(roachE, F_OUT, OU1, out_pts, [Vector((-0.2, 1, 0)), HOLE_N, HOLE_N, Vector((-1, 0, 0)), Vector((-1, 0, 0))], ease_=True, seed=5)
vis(roachE, [S["enter"], S["drop"], S["out"]])

# quloq teshigi (qorong'i chuqurlik) — chig'anoq tubida
hole_m = bpy.data.materials.new("ear_hole"); hole_m.use_nodes = True
N = hole_m.node_tree.nodes; L = hole_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0 / 0.0055, 1.0 / 0.0042, 1.0)
L.new(tc.outputs["Object"], mp.inputs[0]); L.new(mp.outputs[0], gr.inputs[0])
cr = N.new("ShaderNodeValToRGB"); L.new(gr.outputs[0], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1); cr.color_ramp.elements[0].position = 0.0
cr.color_ramp.elements[1].color = (1, 1, 1, 1); cr.color_ramp.elements[1].position = 0.75
L.new(cr.outputs[0], b.inputs["Alpha"])
b.inputs["Base Color"].default_value = (0.05, 0.012, 0.01, 1); b.inputs["Roughness"].default_value = 0.4
b.inputs["Coat Weight"].default_value = 0.6
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.0062, fill_type="TRIFAN")
hole = bpy.context.object; hole.name = "ear_hole"; hole.data.materials.append(hole_m)
hole.parent = headE; hole.rotation_mode = "QUATERNION"
hole.location = HOLE_P + HOLE_N * 0.0006
hole.rotation_quaternion = frame_q(Vector((0, 1, 0)), HOLE_N)
hole.scale = (1.0, 0.8, 1.0)

# 3) o'rgimchak: shiftdan ip bilan tushadi (dunyo)
SP0, SP1 = S["spider"]
spid, spid_arm, _ = bug("spider", "72f27245_u.glb", 0.6, speed=1.0, act_len=16.0)
sp_top = EAR_W + EARN_W * 0.03 + Vector((0.01, -0.01, 0))
for f, h in ((SP0 - 2, 0.42), (SP0 + 30, 0.16), (SP0 + 44, 0.07), (SP1 + 2, 0.022)):
    bug_key(spid, f, tuple(sp_top + Vector((0, 0, h))), Vector((1, 0.3, 0)), Vector((0, 0, 1)))
silk_m = mat("silk", (0.95, 0.95, 1.0), 0.2, emit=0.6)
silk = cyl("silk", 0.00012, 1.0, (0, 0, 0), silk_m, verts=6)
silk.data.vertices.foreach_set("co", [c for v in silk.data.vertices for c in (v.co.x, v.co.y, v.co.z + 0.5)])
for f in range(SP0 - 2, SP1 + 3):
    p_ = wpos(spid, f); silk.location = p_; silk.scale = (1, 1, 2.7 - p_.z); silk.keyframe_insert("location", frame=f)
    silk.keyframe_insert("scale", frame=f)
vis(spid, [S["spider"]]); vis(silk, [S["spider"]])

# ======================================================================
# 3) RENTGEN BOSH: shaffof Brian + quloq yo'li, parda, chig'anoq, miya, tarakan
# ======================================================================
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.1, base=0.01)
ghosts = []
for o in bmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, X_SHOTS, recursive=False)
real_ranges = [(1, S["xhead"][0] - 1), (S["canal"][0], S["thunder"][0] - 1), (S["wake"][0], END)]
for o in bmeshes: vis(o, real_ranges, recursive=False)
vis(hole, real_ranges)
def organ_mat(name, col, emit=0.35, alpha_mix=0.5):
    m = mat(name, col, 0.3, sss=0.4, sss_scale=0.003, coat=0.8, emit=emit)
    nm = m.node_tree.nodes; b = nm["Principled BSDF"]
    lw = nm.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    mm_ = nm.new("ShaderNodeMath"); mm_.operation = "MULTIPLY"; mm_.inputs[1].default_value = emit * 2.5
    m.node_tree.links.new(lw.outputs["Facing"], mm_.inputs[0]); m.node_tree.links.new(mm_.outputs[0], b.inputs["Emission Strength"])
    tr = nm.new("ShaderNodeBsdfTransparent"); mx = nm.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha_mix
    m.node_tree.links.new(b.outputs[0], mx.inputs[1]); m.node_tree.links.new(tr.outputs[0], mx.inputs[2])
    m.node_tree.links.new(mx.outputs[0], nm["Material Output"].inputs["Surface"])
    return m
xh = empty("xhead", (0, 0, 0), headE)
canal_x_m = organ_mat("canal_x", (1.0, 0.6, 0.55), emit=0.5, alpha_mix=0.45)
CANAL_X = [HOLE_P + Vector((-0.002, 0, 0)), HOLE_P + Vector((0.008, -0.001, 0.003)), HOLE_P + Vector((0.017, -0.003, 0.006)),
           HOLE_P + Vector((0.025, -0.004, 0.008))]
P.tube("canal_x", catmull(CANAL_X, 0.002), 0.0042, canal_x_m, xh)
DRUM_X = HOLE_P + Vector((0.026, -0.004, 0.008))
drumx_m = organ_mat("drum_x", (1.0, 0.85, 0.75), emit=1.2, alpha_mix=0.15)
drumx = cyl("drum_x", 0.0052, 0.0006, (0, 0, 0), drumx_m, verts=32); drumx.parent = xh
drumx.location = DRUM_X; drumx.rotation_euler = (0, R(90), R(-25))
coch_m = organ_mat("cochlea", (0.95, 0.85, 0.55), emit=0.8, alpha_mix=0.2)
coch = [DRUM_X + Vector((0.006 + 0.0035 * math.cos(a) * (1 - a / 30), -0.002 + 0.0035 * math.sin(a) * (1 - a / 30), 0.008 + a * 0.0002))
        for a in [i * 0.4 for i in range(40)]]
P.tube("cochlea", coch, 0.0012, coch_m, xh)
P.tube("nerve", catmull([coch[-1], DRUM_X + Vector((0.025, 0.004, 0.012)), Vector((0.0, 0.06, 0.0))], 0.003), 0.0015,
       organ_mat("nerve", (1.0, 0.8, 0.4), emit=1.0, alpha_mix=0.2), xh)
brain, brain_m = P.build_brain("brain_x", parent=xh, size=0.074)
brain.location = (0.0, 0.085, 0.0); brain.rotation_euler = (R(-90), 0, 0)
# zarba to'lqinlari (halqalar): quloq pardadan miyaga
wave_m = bpy.data.materials.new("shock"); wave_m.use_nodes = True
N = wave_m.node_tree.nodes; L = wave_m.node_tree.links; N.remove(N["Principled BSDF"])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.25, 0.08, 1)
wv_s = value_node(wave_m, "a", 0.0); L.new(P.math_n(N, L, "MULTIPLY", wv_s, 25.0), em.inputs["Strength"])
trn = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "SUBTRACT", 1.0, wv_s, clamp=True), mx.inputs[0])
L.new(em.outputs[0], mx.inputs[1]); L.new(trn.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs[0])
TH0, TH1 = S["thunder"]
BOOMS = [T(23.5), T(24.6), T(25.45), T(26.1)]
rings = []
for i, fb in enumerate(BOOMS * 2):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.04, major_segments=48, minor_segments=8)
    t_ = bpy.context.object; t_.name = f"shock{i}"; m_ = wave_m.copy(); t_.data.materials.append(m_); t_.parent = xh
    t_.location = DRUM_X; t_.rotation_euler = (0, R(90), 0)
    fb = fb + (4 if i >= len(BOOMS) else 0)
    for f, s_, a in ((1, 0.001, 0.0), (fb - 1, 0.001, 0.0), (fb, 0.004, 1.0), (fb + 14, 0.09, 0.0)):
        t_.scale = (s_,) * 3; t_.keyframe_insert("scale", frame=f)
        n_ = m_.node_tree.nodes["a"].outputs[0]; n_.default_value = a; n_.keyframe_insert("default_value", frame=f)
    rings.append(t_)
for fb in BOOMS:
    for f, v in ((fb - 1, 0.2), (fb, 6.0), (fb + 8, 0.6)): val_key(brain_m, "glow", f, v)
    for f, v in ((fb - 1, 1.2), (fb, 8.0), (fb + 6, 1.2)): val_key(drumx_m, "infl", f, v) if False else None
val_key(brain_m, "glow", 1, 0.3)
# rentgen ichidagi tarakan (Head fazosida, quloq yo'lida)
roachX, roachX_arm, roachX_objs = bug("roachX", "e34efe7c_u.glb", 0.075, parent=xh, speed=2.5)
XA0, XA1 = S["xhead"]
bug_path(roachX, XA0, XA1, [HOLE_P + Vector((0.004, 0, 0.001)), HOLE_P + Vector((0.012, -0.002, 0.004)), HOLE_P + Vector((0.016, -0.003, 0.005))],
         [Vector((-0.2, 1, 0))] * 2, seed=7)
bug_path(roachX, TH0, TH1, [HOLE_P + Vector((0.015, -0.003, 0.005)), HOLE_P + Vector((0.017, -0.003, 0.006)), HOLE_P + Vector((0.016, -0.003, 0.005))],
         [Vector((-0.2, 1, 0))] * 2, seed=8)
for o in roachX_objs:                          # rentgenda ko'rinsin: to'q sariq porlash
    if o.type == "MESH":
        for slot in o.material_slots:
            m0 = slot.material
            if m0 and m0.use_nodes and "Principled BSDF" in m0.node_tree.nodes:
                m1 = m0.copy(); bb = m1.node_tree.nodes["Principled BSDF"]
                bb.inputs["Emission Color"].default_value = (1.0, 0.45, 0.1, 1); bb.inputs["Emission Strength"].default_value = 1.5
                slot.link = "OBJECT"; slot.material = m1
for o in [xh] + list(xh.children_recursive): pass
vis(xh, X_SHOTS)

# ======================================================================
# 4) QULOQ YO'LI KESIMI (studiya, 40x kattalashtirilgan): kirish tepada, parda pastda
# ======================================================================
C0 = Vector((60.0, 0.0, 0.0))
stud = empty("studio", tuple(C0))
PROF = [(1.05, 0.40, 0.0), (0.85, 0.30, 0.0), (0.68, 0.205, 0.0), (0.5, 0.165, 0.01), (0.3, 0.145, 0.02), (0.1, 0.125, 0.03),
        (-0.08, 0.108, 0.02), (-0.24, 0.118, 0.0), (-0.38, 0.135, -0.02), (-0.52, 0.14, -0.03), (-0.62, 0.13, -0.03)]
def prof_at(z):
    for (z0, r0, x0), (z1, r1, x1) in zip(PROF, PROF[1:]):
        if z1 <= z <= z0:
            t = (z0 - z) / (z0 - z1); t = ease(t)
            return r0 + (r1 - r0) * t, x0 + (x1 - x0) * t
    return (PROF[0][1], PROF[0][2]) if z > PROF[0][0] else (PROF[-1][1], PROF[-1][2])
def wall(z, a, inset=0.0):
    r, xo = prof_at(z); r -= inset
    return C0 + Vector((xo + r * math.cos(a), r * math.sin(a), z))
def lathe(name, z0, z1, nz=70, seg=64, rscale=1.0, seed=2):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    me = bpy.data.meshes.new(name); vs = []; fs = []
    for i in range(nz + 1):
        z = z0 + (z1 - z0) * i / nz; r, xo = prof_at(z)
        for j in range(seg):
            a = 2 * math.pi * j / seg
            w = 1 + 0.045 * math.sin(3 * a + ph[0] + z * 7) + 0.03 * math.sin(5 * a + ph[1] - z * 11)
            vs.append((xo + r * rscale * w * math.cos(a), r * rscale * w * math.sin(a), z))
    for i in range(nz):
        for j in range(seg):
            a_, b_ = i * seg + j, i * seg + (j + 1) % seg
            fs.append((a_, b_, b_ + seg, a_ + seg))
    fs.append(tuple(range(seg))[::-1]); fs.append(tuple(range(nz * seg, (nz + 1) * seg)))
    me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = C0
    return o

def canal_skin_mat():
    m = bpy.data.materials.new("canal_skin"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; nz.inputs["Detail"].default_value = 8; L.new(tc.outputs["Object"], nz.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.62, 0.3, 0.26, 1); cr.color_ramp.elements[1].color = (0.92, 0.62, 0.52, 1)
    # oltingugurt dog'lari (chuqurroqda ko'proq)
    wz = N.new("ShaderNodeTexNoise"); wz.inputs["Scale"].default_value = 4; wz.inputs["Detail"].default_value = 4; L.new(tc.outputs["Object"], wz.inputs[0])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    wm = N.new("ShaderNodeMapRange"); L.new(wz.outputs["Fac"], wm.inputs["Value"]); wm.inputs["From Min"].default_value = 0.56
    wm.inputs["From Max"].default_value = 0.64
    deep = N.new("ShaderNodeMapRange"); L.new(sep.outputs["Z"], deep.inputs["Value"]); deep.inputs["From Min"].default_value = 0.6
    deep.inputs["From Max"].default_value = -0.1
    wax = P.math_n(N, L, "MULTIPLY", wm.outputs[0], deep.outputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(wax, mx.inputs["Factor"]); L.new(cr.outputs[0], mx.inputs[6])
    mx.inputs[7].default_value = (0.55, 0.3, 0.06, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.03; b.inputs["Roughness"].default_value = 0.38
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", wax, 0.6), 0.25), b.inputs["Coat Weight"])
    bn = N.new("ShaderNodeTexVoronoi"); bn.inputs["Scale"].default_value = 60; L.new(tc.outputs["Object"], bn.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.004
    L.new(P.math_n(N, L, "ADD", bn.outputs["Distance"], P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 1.5)), bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def section_mat():
    m = bpy.data.materials.new("section"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs[0])
    d = P.math_n(N, L, "LENGTH", P.math_n(N, L, "MULTIPLY", tc.outputs["Object"], (1.0, 1.0, 0.0), vec=True), vec=True)
    d = P.math_n(N, L, "ADD", d, P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.08))
    flesh = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], flesh.inputs[0])
    flesh.color_ramp.elements[0].color = (0.45, 0.06, 0.06, 1); flesh.color_ramp.elements[1].color = (0.85, 0.32, 0.28, 1)
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 25; L.new(tc.outputs["Object"], vor.inputs["Vector"])
    bone = N.new("ShaderNodeMix"); bone.data_type = "RGBA"
    L.new(P.math_n(N, L, "LESS_THAN", vor.outputs["Distance"], 0.18), bone.inputs["Factor"])
    bone.inputs[6].default_value = (0.86, 0.8, 0.66, 1); bone.inputs[7].default_value = (0.55, 0.38, 0.25, 1)
    cart = (0.85, 0.85, 0.82, 1)
    lay = N.new("ShaderNodeMix"); lay.data_type = "RGBA"                     # yuqorida tog'ay, pastda suyak
    zsel = N.new("ShaderNodeMapRange"); L.new(sep.outputs["Z"], zsel.inputs["Value"]); zsel.inputs["From Min"].default_value = 0.05
    zsel.inputs["From Max"].default_value = 0.15
    L.new(zsel.outputs[0], lay.inputs["Factor"]); L.new(bone.outputs[2], lay.inputs[6]); lay.inputs[7].default_value = cart
    ring = N.new("ShaderNodeMapRange"); L.new(d, ring.inputs["Value"]); ring.inputs["From Min"].default_value = 0.3
    ring.inputs["From Max"].default_value = 0.33
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(ring.outputs[0], c1.inputs["Factor"])
    L.new(lay.outputs[2], c1.inputs[6]); L.new(flesh.outputs[0], c1.inputs[7])
    skin_t = N.new("ShaderNodeMapRange"); L.new(sep.outputs["Z"], skin_t.inputs["Value"]); skin_t.inputs["From Min"].default_value = 0.96
    skin_t.inputs["From Max"].default_value = 1.0
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(skin_t.outputs[0], c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.8, 0.55, 0.45, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.5
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.02
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

skin_c_m = canal_skin_mat(); sect_m = section_mat()
canal_cut = lathe("canal_cutter", -0.62, 1.25); canal_cut.data.materials.append(skin_c_m)
canal_cut.hide_render = True; canal_cut.display_type = "WIRE"
def tissue(name, cut_half):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); o = bpy.context.object; o.name = name   # (transform_apply joylashuvni ham yozib yuboradi)
    o.scale = (0.75, 0.75, 0.8); bpy.ops.object.transform_apply(scale=True)
    # sirt koordinatasi studiya markaziga nisbatan bo'lsin
    me = o.data
    for v in me.vertices: v.co += Vector((0, 0, 0.2))
    o.location = C0
    o.data.materials.append(sect_m)
    m1 = o.modifiers.new("canal", "BOOLEAN"); m1.object = canal_cut; m1.operation = "DIFFERENCE"; m1.solver = "EXACT"
    m1.material_mode = "TRANSFER"
    if cut_half:
        bpy.ops.mesh.primitive_cube_add(location=tuple(C0 + Vector((0, -1.0, 0.2)))); h = bpy.context.object; h.name = name + "_half"
        h.scale = (1.5, 1.0, 1.5); bpy.ops.object.transform_apply(scale=True); h.data.materials.append(sect_m)
        h.hide_render = True; h.display_type = "WIRE"
        m2 = o.modifiers.new("half", "BOOLEAN"); m2.object = h; m2.operation = "DIFFERENCE"; m2.solver = "EXACT"; m2.material_mode = "TRANSFER"
    return o
tis_cut = tissue("tissue_cut", True); tis_full = tissue("tissue_full", False)
SIDE_SHOTS = rng("canal", "back", "drum", "tear", "choke")
vis(tis_cut, SIDE_SHOTS, recursive=False); vis(tis_full, rng("forward"), recursive=False)
# tukchalar va oltingugurt (kirish qismida)
hair_m = mat("canal_hair", (0.08, 0.05, 0.035), 0.45, coat=0.3)
bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.0028, radius2=0.0003, depth=1.0, location=(0, 0, 0.5))
hair_mesh = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object); hair_mesh.materials.append(hair_m)
hairs = empty("hairs", (0, 0, 0)); rh = random.Random(11)
for i in range(260):
    z = rh.uniform(0.3, 0.95); a = rh.uniform(0.15, math.pi - 0.15) if i % 3 else rh.uniform(0, 2 * math.pi)
    base = wall(z, a, 0.004); r_, xo = prof_at(z)
    inward = (Vector((C0.x + xo, C0.y, base.z)) - base).normalized()
    d_ = (inward * 0.8 + Vector((0, 0, rh.uniform(0.3, 0.9)))).normalized()
    o = bpy.data.objects.new(f"hair{i}", hair_mesh); sc.collection.objects.link(o); o.parent = hairs
    o.location = base; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d_)
    ln = rh.uniform(0.03, 0.09) * (1.0 if z > 0.5 else 0.6); o.scale = (1, 1, ln)
wax_m = mat("wax", (0.5, 0.26, 0.04), 0.25, coat=0.8, sss=0.6, sss_scale=0.02)
for i in range(22):
    z = rh.uniform(-0.15, 0.55); a = rh.uniform(0.2, math.pi - 0.2)
    p_ = wall(z, a, -0.008); s_ = sphere(f"wax{i}", rh.uniform(0.01, 0.022), tuple(p_), wax_m, scale=(1.6, 1.6, 0.6), sub=2)
    s_.parent = hairs; s_.matrix_parent_inverse = Matrix.Identity(4)
vis(hairs, SIDE_SHOTS + rng("forward"))

# quloq pardasi: disk (halqalar), shakl kaliti "bulge" (ichkariga), material: to'lqin halqalari, yirtiq
DRUM_C = C0 + Vector((-0.02, 0.0, -0.44)); DRUM_R = 0.165
def drum_mat():
    m = bpy.data.materials.new("eardrum"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    rip = value_node(m, "rip", 0.0); ripa = value_node(m, "ripa", 0.0); hole_r = value_node(m, "hole", 0.0); red = value_node(m, "red", 0.0)
    d = P.math_n(N, L, "LENGTH", tc.outputs["Object"], vec=True)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs[0])
    # tomirlar (radial)
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 0.0
    vn = N.new("ShaderNodeTexNoise"); vn.inputs["Scale"].default_value = 9; vn.inputs["Distortion"].default_value = 1.2; L.new(tc.outputs["Object"], vn.inputs[0])
    vr = N.new("ShaderNodeMapRange"); L.new(vn.outputs["Fac"], vr.inputs["Value"]); vr.inputs["From Min"].default_value = 0.485
    vr.inputs["From Max"].default_value = 0.5
    vr2 = N.new("ShaderNodeMapRange"); L.new(vn.outputs["Fac"], vr2.inputs["Value"]); vr2.inputs["From Min"].default_value = 0.515
    vr2.inputs["From Max"].default_value = 0.5
    vein = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", vr.outputs[0], vr2.outputs[0]),
                    P.math_n(N, L, "MULTIPLY", d, 6.0, clamp=True))
    base = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], base.inputs[0])
    base.color_ramp.elements[0].color = (0.62, 0.55, 0.55, 1); base.color_ramp.elements[1].color = (0.86, 0.8, 0.78, 1)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(P.math_n(N, L, "ADD", vein, red, clamp=True), c1.inputs["Factor"])
    L.new(base.outputs[0], c1.inputs[6]); c1.inputs[7].default_value = (0.7, 0.05, 0.04, 1)
    L.new(c1.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.18; b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Transmission Weight"].default_value = 0.35; b.inputs["Subsurface Weight"].default_value = 0.4
    b.inputs["Subsurface Scale"].default_value = 0.01
    # to'lqin halqalari: sin(d*k - rip) * ripa  -> bump + yengil porlash
    ph = P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", d, 90.0), rip)
    sn = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SINE", ph), ripa)
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.01
    L.new(sn, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (1.0, 0.35, 0.2, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MAXIMUM", sn, 0.0), 1.5), P.math_n(N, L, "MULTIPLY", red, 2.0)),
          b.inputs["Emission Strength"])
    # yirtiq: chetlari qirrali teshik
    hn = N.new("ShaderNodeTexNoise"); hn.inputs["Scale"].default_value = 30; hn.inputs["Detail"].default_value = 5; L.new(tc.outputs["Object"], hn.inputs[0])
    hd = P.math_n(N, L, "ADD", P.math_n(N, L, "LENGTH", P.math_n(N, L, "SUBTRACT", tc.outputs["Object"], (0.03, -0.02, 0.0), vec=True), vec=True),
                  P.math_n(N, L, "MULTIPLY", hn.outputs["Fac"], 0.06))
    inside = P.math_n(N, L, "LESS_THAN", hd, hole_r)
    rim = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", hd, P.math_n(N, L, "ADD", hole_r, 0.025)), P.math_n(N, L, "GREATER_THAN", hole_r, 0.001))
    rs = N.new("ShaderNodeBsdfPrincipled"); rs.inputs["Base Color"].default_value = (0.35, 0.0, 0.0, 1); rs.inputs["Roughness"].default_value = 0.2
    rs.inputs["Coat Weight"].default_value = 1.0
    tr = N.new("ShaderNodeBsdfTransparent")
    m2 = N.new("ShaderNodeMixShader"); L.new(rim, m2.inputs[0]); L.new(b.outputs[0], m2.inputs[1]); L.new(rs.outputs[0], m2.inputs[2])
    m3 = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "MULTIPLY", inside, P.math_n(N, L, "GREATER_THAN", hole_r, 0.001)), m3.inputs[0])
    L.new(m2.outputs[0], m3.inputs[1]); L.new(tr.outputs[0], m3.inputs[2]); L.new(m3.outputs[0], N["Material Output"].inputs[0])
    return m
drum_m = drum_mat()
me = bpy.data.meshes.new("drum"); vs = [(0, 0, 0)]; fs = []; NR, NS = 24, 64
for i in range(1, NR + 1):
    for j in range(NS):
        a = 2 * math.pi * j / NS; r = DRUM_R * i / NR; vs.append((r * math.cos(a), r * math.sin(a) * 0.92, 0))
for j in range(NS): fs.append((0, 1 + j, 1 + (j + 1) % NS))
for i in range(NR - 1):
    for j in range(NS):
        a_ = 1 + i * NS + j; b_ = 1 + i * NS + (j + 1) % NS; fs.append((a_, b_, b_ + NS, a_ + NS))
me.from_pydata(vs, [], fs); me.update()
for p_ in me.polygons: p_.use_smooth = True
drum = bpy.data.objects.new("eardrum", me); sc.collection.objects.link(drum); drum.location = DRUM_C
drum.rotation_euler = (0, R(-32), 0); me.materials.append(drum_m)
drum.shape_key_add(name="Basis", from_mix=False)
for nm_, amp in (("bulge", -0.07), ("out", 0.05)):
    kb = drum.shape_key_add(name=nm_, from_mix=False); kb.value = 0.0
    for i, v in enumerate(me.vertices):
        rr = Vector((v.co.x, v.co.y / 0.92)).length / DRUM_R
        kb.data[i].co.z = v.co.z + amp * (1 - rr * rr) * (1 - 0.3 * rr)          # markaz (umbo) chuqurroq
# umbo/bolg'acha dastasi (pardaning orqasida oq chiziq)
mall = cyl("malleus", 0.009, 0.15, (0, 0, 0), mat("malleus", (0.95, 0.92, 0.85), 0.4, sss=0.3), verts=12)
mall.parent = drum; mall.location = (0.0, 0.065, -0.015); mall.rotation_euler = (R(90), 0, 0)
# o'rta quloq bo'shlig'i (pardaning orqasi) — qorong'i qizil
def drum_hit(f, amp=1.0, dur=6):
    for k, v in ((f - 1, 0.0), (f + 1, 0.9 * amp), (f + 3, 0.4 * amp), (f + dur, 0.0)):
        drum.data.shape_keys.key_blocks["bulge"].value = v; drum.data.shape_keys.key_blocks["bulge"].keyframe_insert("value", frame=k)
    for k, v in ((f - 1, 0.0), (f + 1, 1.0 * amp), (f + 14, 0.0)): val_key(drum_m, "ripa", k, v)
for k, v in ((1, 0.0), (END, 400.0)): val_key(drum_m, "rip", k, v)
for fc in mc._fcurves(drum_m.node_tree.animation_data.action):
    if '"rip"' in fc.data_path:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# studiya tarakani (40x)
ROACH_C = 3.3
roachC, roachC_arm, roachC_objs = bug("roachC", "e34efe7c_u.glb", ROACH_C, speed=2.4)
WALL_A = math.radians(90)                           # orqa devor (kesimdan ko'rinadi)
def rpos(z, a=WALL_A, lift=0.075):
    r, xo = prof_at(z); return C0 + Vector((xo + (r - lift) * math.cos(a), (r - lift) * math.sin(a), z))
def rup(a=WALL_A): return Vector((-math.cos(a), -math.sin(a), 0.25))
CA0, CA1 = S["canal"]; BA0, BA1 = S["back"]; FO0, FO1 = S["forward"]; DR0, DR1 = S["drum"]
TE0, TE1 = S["tear"]; CH0, CH1 = S["choke"]
def rkey(f, z, a=WALL_A, tilt=0.0):
    fwd = Vector((0, 0, -1)) + Vector((-math.sin(a), math.cos(a), 0)) * tilt
    bug_key(roachC, f, tuple(rpos(z, a)), fwd, rup(a))
# kanal: kirishdan pastga
for f in range(CA0, CA1 + 1, 3): rkey(f, 0.85 - 0.5 * ease((f - CA0) / (CA1 - CA0)), tilt=0.15 * math.sin(f * 0.3))
# orqaga urinadi: biroz tepaga sirpanadi, yana tushadi (burila olmaydi)
for f in range(BA0, BA1 + 1, 2):
    t = (f - BA0) / (BA1 - BA0)
    z = 0.35 + 0.07 * math.sin(t * math.pi * 2.5) * (1 - t) - 0.05 * t
    rkey(f, z, a=WALL_A + 0.12 * math.sin(f * 0.9), tilt=0.35 * math.sin(f * 0.7))
# oldinga, pardaga
for f in range(FO0, FO1 + 1, 3): rkey(f, 0.3 - 0.5 * ease((f - FO0) / (FO1 - FO0)), tilt=0.1 * math.sin(f * 0.4))
Z_DRUM = -0.205                                   # tarakan markazi: boshi pardaga tegadi
HITS = [T(19.95), T(20.45), T(20.95), T(21.6), T(22.1), T(22.55), T(23.0)]
for f in range(DR0, DR1 + 1):
    z = Z_DRUM + 0.012 * math.sin(f * 1.3)
    for h in HITS:
        if 0 <= f - h < 5: z -= 0.03 * (1 - (f - h) / 5)
    if f % 2 == 0 or f in HITS: rkey(f, z, tilt=0.06 * math.sin(f * 0.8))
for h in HITS: drum_hit(h, 1.0)
for h in BOOMS: drum_hit(h, 1.2)
# tayoqcha itaradi, parda yirtiladi
F_PUSH, F_TEAR = T(32.7), T(34.65)
for f in range(TE0, TE1 + 1, 2):
    z = Z_DRUM
    if f > F_PUSH: z -= 0.11 * ease(min(1.0, (f - F_PUSH) / max(1, F_TEAR - F_PUSH)))
    if f > F_TEAR: z -= 0.06 * ease(min(1.0, (f - F_TEAR) / 10))
    rkey(f, z, tilt=0.05 * math.sin(f))
kb_ = drum.data.shape_keys.key_blocks["bulge"]
for f, v in ((F_PUSH, 0.0), (F_TEAR - 2, 1.6), (F_TEAR, 1.9), (F_TEAR + 3, 0.9), (TE1, 0.8), (TE1 + 1, 0.0)):
    kb_.value = v; kb_.keyframe_insert("value", frame=f)
for f, v in ((1, 0.0), (F_TEAR, 0.0), (F_TEAR + 2, 0.06), (F_TEAR + 12, 0.1), (TE1, 0.11), (TE1 + 1, 0.0)): val_key(drum_m, "hole", f, v)
for f, v in ((1, 0.0), (F_TEAR - 6, 0.0), (F_TEAR, 1.0), (F_TEAR + 20, 0.5), (TE1 + 1, 0.0)): val_key(drum_m, "red", f, v)
# yog'da bo'g'ilish
for f in range(CH0, CH1 + 1, 2): rkey(f, Z_DRUM + 0.01 * math.sin(f * (0.9 - 0.6 * (f - CH0) / (CH1 - CH0))), tilt=0.15 * math.sin(f * 1.1) * (1 - (f - CH0) / (CH1 - CH0)))
vis(roachC, CANAL_SHOTS)

# tayoqcha (real o'lcham: uch 5x12 mm, tayoq 2.5 mm x 75 mm) — uchi (0,0,0) da, dastasi +Z
cotton_m = mat("cotton", (0.97, 0.97, 0.95), 0.95, sss=0.4, sss_scale=0.002)
stick_m = mat("stick", (0.92, 0.92, 0.96), 0.35, coat=0.3)
ctex = bpy.data.textures.new("cotton_fib", "CLOUDS"); ctex.noise_scale = 0.08
def make_swab(name, s, parent=None):
    r0 = empty(name, (0, 0, 0), parent)
    st = cyl(name + "_stick", 0.00125 * s, 0.075 * s, (0, 0, 0.0375 * s), stick_m, verts=16); st.parent = r0; st.matrix_parent_inverse = Matrix.Identity(4)
    for zz in (0.0045 * s, 0.0705 * s):
        ct = sphere(name + "_cot", 0.0026 * s, (0, 0, zz), cotton_m, scale=(1, 1, 2.3), sub=4); ct.parent = r0
        ct.matrix_parent_inverse = Matrix.Identity(4)
        d_ = ct.modifiers.new("fib", "DISPLACE"); d_.texture = ctex; d_.strength = 0.0006 * s; d_.texture_coords = "LOCAL"
    return r0
swabC = make_swab("swabC", 40.0)
swabC.location = tuple(rpos(1.6, 0, 0.0) * 0 + C0 + Vector((0.02, -0.02, 1.6)))
for f, z in ((TE0, 1.4), (F_PUSH - 8, 0.4), (F_PUSH, 0.05), (F_TEAR, Z_DRUM + 0.12), (F_TEAR + 10, Z_DRUM + 0.06), (TE1, Z_DRUM + 0.05)):
    key(swabC, f, loc=tuple(C0 + Vector((0.02, -0.0, z))))
swabC.rotation_euler = (R(-3), 0, 0)
vis(swabC, rng("tear"))

# yog' (kanal ichida ko'tariladi): kanal shakli ∩ sath qutisi
oil_m = mat("oil", (1.0, 0.72, 0.18), 0.03, trans=0.92, ior=1.47, coat=0.0)
oil_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.6, 0.1, 1)
oil_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.05
oilC = lathe("oil_canal", -0.62, 1.0, rscale=0.985, seed=2); oilC.data.materials.append(oil_m)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); lvl = bpy.context.object; lvl.name = "oil_level"
lvl.scale = (1.0, 1.0, 0.5); bpy.ops.object.transform_apply(scale=True); lvl.hide_render = True; lvl.display_type = "WIRE"
bo = oilC.modifiers.new("lvl", "BOOLEAN"); bo.object = lvl; bo.operation = "INTERSECT"; bo.solver = "EXACT"
for f, z in ((1, -1.2), (CH0, -1.05), (CH1, 0.15)): key(lvl, f, loc=tuple(C0 + Vector((0, 0, z))))
bp_ = oilC.modifiers.new("half", "BOOLEAN"); bp_.object = bpy.data.objects["tissue_cut_half"]; bp_.operation = "DIFFERENCE"; bp_.solver = "EXACT"
vis(oilC, rng("choke"))
bub_m = P.bubble_material()
bubs = empty("bubbles", (0, 0, 0)); rb = random.Random(5)
for i in range(26):
    s_ = sphere(f"bub{i}", rb.uniform(0.008, 0.022), (0, 0, 0), bub_m, sub=2, parent=bubs, world=False)
    f0 = rb.randint(CH0 + 8, CH1 - 10); a = WALL_A + rb.uniform(-0.5, 0.5)
    p0 = rpos(Z_DRUM + rb.uniform(-0.15, 0.2), a, 0.1)
    key(s_, 1, loc=tuple(p0), scale=(0.001,) * 3); key(s_, f0 - 1, loc=tuple(p0), scale=(0.001,) * 3)
    key(s_, f0, loc=tuple(p0), scale=(1, 1, 1))
    for k in range(2, 40, 3):
        lv = -1.05 + 1.2 * (min(f0 + k, CH1) - CH0) / (CH1 - CH0) - 0.03
        z = min(p0.z + 0.012 * k * k * 0.15 + 0.01 * k, lv)
        key(s_, f0 + k, loc=(p0.x + 0.01 * math.sin(k + i), p0.y - 0.004 * k, z), scale=(1, 1, 1) if z < lv else (0.001,) * 3)
    interp(s_, "LINEAR")
vis(bubs, rng("choke"))

# ======================================================================
# 5) TAYOQCHA (o'tirgan Brian, o'ng qo'l IK) va YOG' (Kate, shisha, tomchilar, chig'anoqdagi ko'lmak)
# ======================================================================
def arm_ik(arm, side, name, pole=None, pole_ang=-90):
    tgt = empty(f"{name}_{side}_ik")
    c = arm.pose.bones[f"mixamorig:{side}ForeArm"].constraints.new("IK")
    c.target = tgt; c.use_tail = True; c.chain_count = 2; c.influence = 0.0
    if pole is not None: c.pole_target = pole; c.pole_angle = R(pole_ang)
    return tgt, c
def key_inf(cs, pairs):
    for c in cs:
        for f, v in pairs: c.influence = v; c.keyframe_insert("influence", frame=f)
CANAL_DIR = (CANAL_X[-1] - CANAL_X[0]).normalized()           # Head fazosida, ichkariga
SW0, SW1 = S["swab"]
swR = empty("swab_head", (0, 0, 0), headE); swR.rotation_mode = "QUATERNION"
swR.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(-(CANAL_DIR + Vector((0, -0.35, 0.15))).normalized())
swabB = make_swab("swabB", 1.0, swR)
for f, d in ((SW0, -0.03), (SW0 + 14, -0.012), (T(30.4), 0.004), (SW1, 0.012)):
    key(swR, f, loc=tuple(HOLE_P + CANAL_DIR * d))
vis(swabB, rng("swab"))
gripB = empty("swab_grip", (0, 0, 0.062), swabB)
tipB = empty("swab_tipaim", (0, 0, -0.05), swabB)
poleB = empty("bri_poleR", (-0.35, -0.45, -0.1), headE)
RT_, RIK = arm_ik(bri, "Right", "bri", pole=poleB, pole_ang=-90)
for f in range(SW0 - 2, SW1 + 2, 2):
    g_ = wpos(gripB, f); sh_ = bri.matrix_world @ bri.pose.bones["mixamorig:RightShoulder"].head
    key(RT_, f, loc=tuple(g_ + (sh_ - g_).normalized() * 0.07))
hbR = bri.pose.bones["mixamorig:RightHand"]
dtr = hbR.constraints.new("DAMPED_TRACK"); dtr.target = tipB; dtr.track_axis = "TRACK_Y"
key_inf([RIK, dtr], [(1, 0.0), (SW0 - 1, 0.0), (SW0, 1.0), (SW1, 1.0), (SW1 + 1, 0.0)])

# yog' shishasi (o'simlik yog'i): shisha + ichida tilla rang yog', qopqoq-tomizgich. Uchi (0,0,0), tubi -Z da
glass_m = mat("bottle_glass", (0.95, 0.97, 0.95), 0.02, trans=1.0, ior=1.5)
oilB_m = mat("bottle_oil", (1.0, 0.68, 0.12), 0.05, trans=0.9, ior=1.47)
label_m = mat("label", (0.15, 0.45, 0.18), 0.6)
def make_bottle(name):
    r0 = empty(name, (0, 0, 0)); r0.rotation_mode = "QUATERNION"
    def add(o):
        o.parent = r0; o.matrix_parent_inverse = Matrix.Identity(4); return o
    add(cyl(name + "_body", 0.032, 0.13, (0, 0, -0.115), glass_m, verts=40))
    add(cyl(name + "_oil", 0.029, 0.1, (0, 0, -0.128), oilB_m, verts=40))
    add(cyl(name + "_label", 0.0325, 0.05, (0, 0, -0.12), label_m, verts=40))
    sh = add(sphere(name + "_sh", 0.032, (0, 0, -0.05), glass_m, scale=(1, 1, 0.55), sub=4))
    add(cyl(name + "_neck", 0.011, 0.04, (0, 0, -0.025), glass_m, verts=24))
    add(cyl(name + "_cap", 0.0075, 0.012, (0, 0, -0.004), mat("dropper", (0.95, 0.95, 0.95), 0.3), verts=20))
    return r0
bottle = make_bottle("bottle")
OW0, OW1 = S["oilwide"]; DP0, DP1 = S["drop"]
sc.frame_set(OW0 + 5); bpy.context.view_layer.update()
EAR_W2 = wpos(earE, OW0 + 5); EARN2 = (headE.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
TIP_POUR = EAR_W2 + EARN2 * 0.045 + Vector((0, 0, 0.02))
TIP_START = Vector(KATE_ROOT) + Vector((0.32, -0.28, 0.98))
def bottle_key(f, tip, tilt):
    """tilt: 0 = tik (uchi tepada), 1 = quyish (uchi pastga, quloqqa)"""
    up = Vector((0, 0, 1)); pour = (EAR_W2 - tip).normalized()
    d = up.lerp(pour, tilt).normalized()
    bottle.location = tip; bottle.keyframe_insert("location", frame=f)
    bottle.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d); bottle.keyframe_insert("rotation_quaternion", frame=f)
bottle_key(1, TIP_START, 0.0)
bottle_key(OW0 + 6, TIP_START, 0.0)
bottle_key(OW0 + 40, TIP_POUR + Vector((-0.06, 0, 0.09)), 0.3)
bottle_key(OW1 - 4, TIP_POUR + Vector((-0.02, 0, 0.03)), 0.85)
bottle_key(DP0, TIP_POUR, 1.0)
bottle_key(DP1, TIP_POUR + Vector((0.003, 0, 0.004)), 1.02)
bottle_key(S["out"][0], TIP_POUR + Vector((-0.12, -0.05, 0.15)), 0.2)
vis(bottle, [(OW0, DP1)])
gripK = empty("bottle_grip", (0.0, 0.0, -0.1), bottle)
poleK = empty("kat_pole", tuple(Vector(KATE_ROOT) + Vector((0.2, -0.9, 0.9))))
KT_, KIK = arm_ik(kat, "Right", "kat", pole=poleK, pole_ang=-90)
for f in range(OW0 - 2, DP1 + 2, 2):
    g_ = wpos(gripK, f); sh_ = kat.matrix_world @ kat.pose.bones["mixamorig:RightShoulder"].head
    key(KT_, f, loc=tuple(g_ + (sh_ - g_).normalized() * 0.075))
hbK = kat.pose.bones["mixamorig:RightHand"]
dtk = hbK.constraints.new("DAMPED_TRACK"); dtk.target = bottle; dtk.track_axis = "TRACK_Y"
key_inf([KIK, dtk], [(1, 1.0)])
# tomchilar
drop_m = mat("drop_oil", (1.0, 0.7, 0.15), 0.02, trans=0.85, ior=1.47, coat=0.5)
DROPS = [T(38.9), T(39.65), T(40.4)]
for i, fd in enumerate(DROPS):
    d_ = sphere(f"oil_drop{i}", 0.0028, (0, 0, 0), drop_m, sub=3)
    tip = TIP_POUR + (EAR_W2 - TIP_POUR).normalized() * 0.004
    hole_w = wpos(earE, fd + 8)
    for f, p, scl in ((1, tip, 0.001), (fd - 10, tip, 0.001), (fd - 2, tip, 0.9), (fd + 2, tip.lerp(hole_w, 0.25), 1.0), (fd + 8, hole_w, 1.0), (fd + 9, hole_w, 0.001)):
        key(d_, f, loc=tuple(p), scale=(scl, scl, scl * (1.6 if fd - 2 < f <= fd + 8 else 1.0)))
    interp(d_, "LINEAR")
    vis(d_, [S["drop"]])
pool_m = mat("oil_pool", (1.0, 0.66, 0.12), 0.02, trans=0.8, ior=1.47, coat=1.0)
pool = sphere("oil_pool", 0.0085, (0, 0, 0), pool_m, sub=4); pool.parent = headE
pool.rotation_mode = "QUATERNION"; pool.rotation_quaternion = frame_q(Vector((0, 1, 0)), HOLE_N)
pool.location = HOLE_P + HOLE_N * 0.0005
for f, s_ in ((1, 0.001), (DROPS[0] + 7, 0.001), (DROPS[0] + 10, 0.5), (DROPS[1] + 10, 0.8), (DROPS[2] + 10, 1.0), (END, 1.15)):
    pool.scale = (s_, s_ * 0.85, s_ * 0.22); pool.keyframe_insert("scale", frame=f)
vis(pool, rng("drop", "out"))
# salfetka yostiqda (tarakan shu yerga tushadi)
tissue_m = mat("tissue_w", (0.96, 0.96, 0.95), 0.9, sss=0.3)
tis = plane("tissue_paper", (0.16, 0.14), tuple(wpos(headE, OW0 + 5, tuple(skin(0.03, 0.035)[0] + Vector((-0.03, 0, 0)))) * 0 +
                                               Vector((EAR_W2.x - 0.09, EAR_W2.y + 0.0, PIL_TOP + 0.003))), tissue_m, rot=(0, 0, 15))
sb = tis.modifiers.new("s", "SUBSURF"); sb.levels = 2; sb.render_levels = 3
dsp = tis.modifiers.new("d", "DISPLACE"); dsp.texture = bpy.data.textures.new("tis_crumple", "CLOUDS"); dsp.texture.noise_scale = 0.03; dsp.strength = 0.008
vis(tis, rng("oilwide", "drop", "out"))

# ======================================================================
# 6) KAMERALAR (har kadrda harakat: push-in, ergashish, aylanma, crash zoom, silkinish)
# ======================================================================
def track_empty(name, src, f0, f1, local=(0, 0, 0), step=2):
    t = empty(name, (0, 0, 0))
    for f in range(f0, f1 + 1, step): key(t, f, loc=tuple(wpos(src, f, local)))
    interp(t, "LINEAR", "location"); return t
def hs(p):                                   # Head fazosi -> dunyo (sahna ilgagi kadrida)
    return headE.matrix_world @ Vector(p)

# 1 ilgak: yostiq sathida, tarakan ortida, oldinda bosh (xira)
c = shot_cam("hook", (0, 0, 0), None, 24, fstop=2.8, clip=0.002)
tgtH = empty("hook_tgt", (0, 0, 0))
for f in range(H0, H1 + 3, 2):
    key(tgtH, f, loc=tuple(wpos(roachP, f).lerp(Vector((EAR_W.x - 0.02, EAR_W.y - 0.03, PIL_TOP + 0.05)), 0.15)))
c.constraints.new("TRACK_TO").target = tgtH; c.constraints[0].track_axis = "TRACK_NEGATIVE_Z"; c.constraints[0].up_axis = "UP_Y"
c.data.dof.focus_object = roachP
for f in range(H0, H1 + 3, 2):
    p = wpos(roachP, f); t = (f - H0) / (H1 - H0)
    key(c, f, loc=tuple(p + Vector((-0.085 + 0.03 * t, -0.055 + 0.02 * t, 0.028 - 0.006 * t))))
interp(c, "LINEAR", "location")
# 2 quloqqa kirish: quloq makro, sekin push-in (Head fazosida)
c = shot_cam("enter", (0, 0, 0), roachE, 42, fstop=5.6, clip=0.002); c.parent = headE
c.data.dof.focus_object = roachE
for f, d, up in ((EN0, 0.15, 0.04), (EN1, 0.1, 0.025)):
    key(c, f, loc=tuple(HOLE_P + HOLE_N * d + Vector((0, up, -0.03))))
# 3 o'rgimchak: past burchak, tepadan tushadi, oxirida crash zoom
c = shot_cam("spider", tuple(EAR_W + Vector((-0.22, -0.16, -0.02))), spid, 20, fstop=4.0, clip=0.002)
key(c, SP0, loc=tuple(EAR_W + Vector((-0.24, -0.17, -0.03)))); key(c, SP1, loc=tuple(EAR_W + Vector((-0.16, -0.11, 0.0))))
lens_keys(c, [(SP0, 20), (SP1 - 14, 26), (SP1 - 6, 70), (SP1, 80)])
# 4 rentgen bosh: tez aylanma
def orbit_cam(name, f0, f1, center, r0, r1, a0, a1, z0, z1, lens, tgt):
    c = shot_cam(name, (0, 0, 0), tgt, lens, clip=0.002)
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / max(1, f1 - f0); a = R(a0 + (a1 - a0) * t); rr = r0 + (r1 - r0) * t
        key(c, f, loc=tuple(Vector(center) + Vector((rr * math.cos(a), rr * math.sin(a), z0 + (z1 - z0) * t))))
    interp(c, "LINEAR", "location"); return c
xt = empty("x_tgt", tuple(DRUM_X), headE)
EAR_X = wpos(xt, XA0)
orbit_cam("xhead", XA0, XA1, EAR_X, 0.42, 0.26, 200, 245, 0.16, 0.08, 35, xt)
# 9 momaqaldiroq: rentgen, aylanma + silkinish
c = orbit_cam("thunder", TH0, TH1, EAR_X, 0.3, 0.2, 140, 95, 0.12, 0.05, 30, xt)
for fb in BOOMS: shake(c, fb, fb + 9, 0.012, seed=fb)
# 5 kanal kesimi: kirishdan pastga uchadi
cf = track_empty("canal_tgt", roachC, CA0, CA1, (0, 0, 0))
c = shot_cam("canal", (0, 0, 0), cf, 24, fstop=5.6, clip=0.01)
for f, z, x in ((CA0, 1.75, 0.5), (CA1, 0.65, 0.25)): key(c, f, loc=tuple(C0 + Vector((x, -1.9, z))))
# 6 orqaga urinish: yon, past burchak, qo'l kamera
c = shot_cam("back", (0, 0, 0), roachC, 30, fstop=4.0, clip=0.01)
for f, p in ((BA0, (-0.45, -1.5, -0.05)), (BA1, (-0.3, -1.3, 0.05))): key(c, f, loc=tuple(C0 + Vector(p)))
shake(c, BA0, BA1, 0.006, seed=3, decay=False)
# 7 oldinga: tarakan ortidan (yopiq kanal ichida, endoskop chirog'i)
c = shot_cam("forward", (0, 0, 0), None, 22, fstop=8.0, clip=0.005)
ft = empty("fwd_tgt", tuple(DRUM_C))
tc_ = c.constraints.new("TRACK_TO"); tc_.target = ft; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
c.data.dof.focus_object = roachC
for f in range(FO0, FO1 + 1, 3):
    t = (f - FO0) / (FO1 - FO0); zc = 0.3 - 0.5 * ease(t) + 0.42 - 0.08 * t
    r_, xo = prof_at(zc); key(c, f, loc=tuple(C0 + Vector((xo, -0.03, zc))))
interp(c, "LINEAR", "location")
endo = point("endo", (0, 0, 0), 0.03, (1.0, 0.85, 0.7), lights_for(rng("forward"), 25.0), parent=c)
# 8 parda: yon, yaqin, har zarbada silkinish
c = shot_cam("drum", (0, 0, 0), None, 24, fstop=5.6, clip=0.01)
dt = empty("drum_tgt", tuple(DRUM_C))
tc_ = c.constraints.new("TRACK_TO"); tc_.target = dt; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
c.data.dof.focus_object = dt
for f, p in ((DR0, (0.2, -0.75, -1.05)), (DR1, (0.08, -0.45, -0.95))): key(c, f, loc=tuple(C0 + Vector(p)))   # pastdan (o'rta quloq tomondan)
for h in HITS: shake(c, h, h + 6, 0.012, seed=h)
# 10 uyg'onish: yuzga yaqin, past burchak, silkinish
WK0, WK1 = S["wake"]
faceT = empty("faceT", (0, 0.06, 0.06), headE)
c = shot_cam("wake", (0, 0, 0), faceT, 32, fstop=2.0, clip=0.01)
for f, p in ((WK0, (0.55, 0.12, -0.18)), (WK1, (0.38, 0.08, -0.1))):
    sc.frame_set(WK0 + 10); key(c, f, loc=tuple(Vector(SIT_ROOT) + Vector((0, 0, 0.47)) + Vector(p) + Vector((0, 0, 0.7))))
shake(c, WK0, WK0 + 20, 0.02, seed=4)
# 11 tayoqcha: o'ng yon, past, sekin aylanma
c = shot_cam("swab", (0, 0, 0), earE, 50, fstop=2.8, clip=0.01)
sc.frame_set(SW0 + 10); EW = wpos(earE, SW0 + 10)
for f, p in ((SW0, (0.36, -0.3, 0.06)), (SW1, (0.3, -0.2, 0.03))): key(c, f, loc=tuple(EW + Vector(p)))
# 12 yirtilish: kesim, keng -> crash zoom pardaga
c = shot_cam("tear", (0, 0, 0), None, 22, fstop=5.6, clip=0.01)
tt = empty("tear_tgt", (0, 0, 0))
for f, p in ((TE0, (0, 0, 0.45)), (F_PUSH, (0, 0, 0.0)), (F_TEAR, (0, 0.02, -0.3)), (TE1, (0, 0.02, -0.35))): key(tt, f, loc=tuple(C0 + Vector(p)))
tc_ = c.constraints.new("TRACK_TO"); tc_.target = tt; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
c.data.dof.focus_object = tt
for f, p in ((TE0, (0.25, -2.6, 0.5)), (F_TEAR - 4, (0.2, -2.1, 0.0)), (F_TEAR, (0.25, -1.3, -0.45)), (TE1, (0.22, -1.15, -0.5))):
    key(c, f, loc=tuple(C0 + Vector(p)))
lens_keys(c, [(TE0, 22), (F_TEAR - 3, 24), (F_TEAR + 1, 38)])
shake(c, F_TEAR, F_TEAR + 14, 0.03, seed=9)
# 13 yog' (keng): oyoq tomondan, past burchak, sekin aylanma
c = shot_cam("oilwide", (0, 0, 0), None, 22, fstop=4.0, clip=0.02)
ot = empty("oil_tgt", tuple(EAR_W2 + Vector((-0.25, -0.15, 0.15))))
tc_ = c.constraints.new("TRACK_TO"); tc_.target = ot; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
c.data.dof.focus_object = earE
for f, p in ((OW0, (0.75, -1.35, 0.55)), (OW1, (0.45, -1.0, 0.65))): key(c, f, loc=p)
# 14 tomchi makro (Head fazosida)
dpt = empty("drop_tgt", tuple(EAR_W2.lerp(TIP_POUR, 0.4)))
c = shot_cam("drop", (0, 0, 0), dpt, 50, fstop=6.3, clip=0.002)
for f, p in ((DP0, (0.03, -0.17, 0.06)), (DP1, (0.02, -0.12, 0.05))): key(c, f, loc=tuple(EAR_W2 + Vector(p)))
c.data.dof.focus_object = earE
# 15 bo'g'ilish: kesim, sath bilan birga ko'tariladi
c = shot_cam("choke", (0, 0, 0), roachC, 30, fstop=5.6, clip=0.01)
for f, p in ((CH0, (0.35, -1.6, -0.4)), (CH1, (0.2, -1.4, 0.05))): key(c, f, loc=tuple(C0 + Vector(p)))
# 16 chiqish: quloq makro -> orqaga tortiladi
c = shot_cam("out", (0, 0, 0), roachE, 50, fstop=9.0, clip=0.002); c.parent = headE
for f, p in ((OU0, HOLE_N * 0.075 + Vector((0, 0.03, -0.04))), (F_OUT + 10, HOLE_N * 0.085 + Vector((0, 0.03, -0.05))),
             (OU1, HOLE_N * 0.2 + Vector((0, 0.06, -0.12)))):
    key(c, f, loc=tuple(HOLE_P + p))
lens_keys(c, [(OU0, 50), (F_OUT + 10, 50), (OU1, 35)])

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 7) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.02, 0.03, 0.06, 1); bg.inputs["Strength"].default_value = 1.0
ROOM_ALL = ROOM_SHOTS
bedT = empty("bed_tgt", (-0.4, 0.3, 0.6))
area("moon", (-2.4, -0.3, 1.7), 1.3, (0.55, 0.7, 1.0), lights_for(ROOM_ALL, 260.0), target=bedT)
point("lamp", (-1.35, 1.2, 0.9), 0.12, (1.0, 0.68, 0.38), lights_for(ROOM_ALL, 55.0))
area("fill", (0.6, -0.8, 2.4), 2.0, (0.75, 0.82, 1.0), lights_for(ROOM_ALL, 45.0), target=bedT)
# makro kadrlar uchun quloq yonidagi yumshoq yorug'lik (kameraga ko'rinmaydi)
earL = empty("earL", tuple(HOLE_P + HOLE_N * 0.25 + Vector((0.0, 0.15, -0.1))), headE)
l_ = area("ear_key", (0, 0, 0), 0.25, (1.0, 0.85, 0.72), lights_for(rng("hook", "enter", "drop", "out"), 6.0), target=earE)
l_.parent = earL
sc.frame_set(S["wake"][0] + 10)
area("face_key", tuple(wpos(headE, S["wake"][0] + 10) + Vector((0.6, -0.4, 0.3))), 0.6, (1.0, 0.88, 0.78),
     lights_for(rng("wake", "swab"), 25.0), target=headE)
area("x_dim", (0, 0, 2.5), 3.0, (0.3, 0.45, 0.9), lights_for(X_SHOTS, 30.0), target=bedT)
# studiya
stT = empty("stud_tgt", tuple(C0 + Vector((0, 0.1, 0.0))))
area("st_key", tuple(C0 + Vector((-1.2, -2.0, 1.8))), 1.5, (1.0, 0.92, 0.85), lights_for(SIDE_SHOTS, 350.0), target=stT)
area("st_rim", tuple(C0 + Vector((1.6, 0.5, 1.2))), 1.0, (0.85, 0.9, 1.0), lights_for(SIDE_SHOTS, 160.0), target=stT)
area("st_in", tuple(C0 + Vector((0.0, -0.6, 0.6))), 0.4, (1.0, 0.8, 0.65), lights_for(SIDE_SHOTS, 40.0), target=empty("dr_t", tuple(DRUM_C)))
point("st_cav", tuple(DRUM_C + Vector((0.05, -0.1, -0.2))), 0.05, (1.0, 0.45, 0.35), lights_for(SIDE_SHOTS, 15.0))
# chaqnashlar (momaqaldiroq, yirtilish)
fl = point("flash", (0, 0, 0), 0.05, (1.0, 0.3, 0.15), [(1, 0)], parent=xt)
for fb in BOOMS:
    for f, e in ((fb - 1, 0), (fb, 40), (fb + 4, 5), (fb + 8, 0)): fl.data.energy = e; fl.data.keyframe_insert("energy", frame=f)
fl2 = point("tear_flash", tuple(DRUM_C + Vector((0, -0.2, 0.05))), 0.1, (1.0, 0.15, 0.05), [(1, 0)])
for f, e in ((F_TEAR - 1, 0), (F_TEAR, 600), (F_TEAR + 6, 80), (F_TEAR + 16, 0)): fl2.data.energy = e; fl2.data.keyframe_insert("energy", frame=f)

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = 0.0
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = os.environ.get("PERSIST", "0") == "1"
r.use_overwrite = False; r.use_placeholder = True

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
