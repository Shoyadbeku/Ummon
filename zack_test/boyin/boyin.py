# "Bo'yinni qirsillatish -> insult" — Zack D. Films uslubida 41.4 s video (993 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, aksirish/aksirish.py (yordamchilar, mehmonxona, rentgen), burish/parts.py (miya, quvur, impuls).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_boyin.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/boyin/boyin.py --render
# Sinov: FRAMES=20,70,90,180,280,480,560,650,720,860,950 PCT=30
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler
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
END = 993
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (46, "twist"), (83, "qirs"), (99, "relief"), (152, "rv1"), (201, "rv2"), (242, "xneck"), (319, "xart"),
         (398, "xtwist"), (450, "pinch"), (519, "tear"), (584, "unaware"), (610, "clot"), (696, "walk"), (750, "brk"),
         (829, "xbrain"), (880, "face"), (919, "collapse")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
ROOM_N = ("hook", "twist", "relief", "unaware")
X_N = ("qirs", "xneck", "xart", "xtwist", "xbrain")
RV_N = ("rv1", "rv2")
AS_N = ("pinch", "tear", "clot", "brk")
ST_N = ("walk", "face", "collapse")
ROOM_SHOTS, X_SHOTS, RV_SHOTS, AS_SHOTS, ST_SHOTS = (rng(*g) for g in (ROOM_N, X_N, RV_N, AS_N, ST_N))

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

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, sss_scale=None, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
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

def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL"); bv.width = bevel; bv.segments = 3
        for p in o.data.polygons: p.use_smooth = True
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
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
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

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

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

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

def ease(t): return t * t * (3 - 2 * t)
def lerp3(a, b_, t, e=True):
    t = ease(t) if e else t; return tuple(Vector(a).lerp(Vector(b_), t))

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def val_key(m, name, f, v): P.mat_value(m, name, f, v)
def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]

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

def tube_mesh(name, pts, r, m, res=14, arc=None, parent=None, taper=None):
    """o'z quvur mesh'imiz: 'u' (egri bo'ylab 0..1) atributi bilan. arc=(a0,a1) gradus — kesim (C shakli)."""
    pts = [Vector(p) for p in pts]; n = len(pts)
    T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    up = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    Nn = (up - T[0] * up.dot(T[0])).normalized(); frames = []
    for i in range(n):                                      # parallel transport
        if i: Nn = (Nn - T[i] * Nn.dot(T[i])).normalized()
        frames.append((Nn.copy(), T[i].cross(Nn)))
    L = [0.0]
    for i in range(1, n): L.append(L[-1] + (pts[i] - pts[i - 1]).length)
    closed = arc is None
    a0, a1 = (0, 360) if closed else arc
    k = res if closed else res + 1
    verts = []; us = []
    for i in range(n):
        Nv, Bv = frames[i]; rr = r * (taper[i] if taper else 1.0)
        for j in range(k):
            a = R(a0 + (a1 - a0) * j / (res if not closed else res))
            verts.append(pts[i] + rr * (math.cos(a) * Nv + math.sin(a) * Bv)); us.append(L[i] / L[-1])
    faces = []
    for i in range(n - 1):
        for j in range(k if closed else k - 1):
            j2 = (j + 1) % k
            faces.append((i * k + j, i * k + j2, (i + 1) * k + j2, (i + 1) * k + j))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    for p in me.polygons: p.use_smooth = True
    at = me.attributes.new("u", "FLOAT", "POINT")
    for i, u in enumerate(us): at.data[i].value = u
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    if parent: o.parent = parent
    me.materials.append(m)
    return o

def pq(o, f, rot):
    """qo'shimcha (COMBINE) suyak burilishi: rot = (x, y, z) gradus, suyak mahalliy o'qlarida"""
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Euler([R(a) for a in rot]).to_quaternion(); o.keyframe_insert("rotation_quaternion", frame=f)

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
                        n.inputs["Roughness"].default_value = 0.5
                    n.inputs["Coat Weight"].default_value = 0.0

def wpos(o, f, local=(0, 0, 0)):
    sc.frame_set(f); return o.matrix_world @ Vector(local)
def follow_target(name, src, f0, f1, local=(0, 0, 0), step=2):
    t = empty(name, (0, 0, 0))
    for f in range(f0, f1 + 1, step): key(t, f, loc=tuple(wpos(src, f, local)))
    interp(t, "LINEAR", "location"); return t
def cam_rel(c, f0, f1, ref, f_ref, offs, step=3, local=(0, 0, 0)):
    base = wpos(ref, f_ref, local)
    for f in range(f0, f1 + 1, step):
        t = (f - f0) / max(1, f1 - f0); key(c, f, loc=tuple(base + Vector(offs(t))))
    interp(c, "BEZIER", "location")

# ======================================================================
# 1) XONA (0,0,0) — kechqurun, noutbuk oldida
# ======================================================================
room = empty("room", (0, 0, 0))
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.4, tint=(0.78, 0.84, 0.9))
plane("floor", (7, 7), (0, 0.5, 0), floor_m, parent=room)
plane("wall_back", (7, 3), (0, 2.25, 1.5), wall_m, rot=(90, 0, 0), parent=room)
plane("wall_left", (7, 3), (-2.4, 0.5, 1.5), wall_m, rot=(90, 0, 90), parent=room)
plane("wall_right", (7, 3), (2.6, 0.5, 1.5), wall_m, rot=(90, 0, -90), parent=room)
plane("ceiling", (7, 7), (0, 0.5, 2.8), mat("ceil", (0.9, 0.9, 0.88), 0.8), rot=(180, 0, 0), parent=room)
box("skirting", (7, 0.02, 0.08), (0, 2.24, 0.04), mat("skirt", (0.95, 0.95, 0.93), 0.4), parent=room)
win_m = mat("win_night", (0.05, 0.08, 0.2), 0.0, emit=0.6, emit_col=(0.15, 0.25, 0.6))
plane("window", (1.4, 1.5), (-2.39, 0.6, 1.5), win_m, rot=(90, 0, 90), parent=room)
frame_m = mat("win_frame", (0.95, 0.95, 0.95), 0.35)
for dz in (-0.76, 0.76): box("wframe", (0.08, 1.5, 0.06), (-2.36, 0.6, 1.5 + dz), frame_m, parent=room)
for dy in (-0.73, 0.0, 0.73): box("wframe", (0.08, 0.06, 1.55), (-2.36, 0.6 + dy, 1.5), frame_m, parent=room)
sofaR = empty("sofaR", (0, 1.85, 0), room); import_gltf(PH + "Sofa_01/Sofa_01.gltf", sofaR); sofaR.scale = (1.15, 1.15, 1.0)
tableR = empty("tableR", (0.15, 1.15, 0), room); tableR.rotation_euler = (0, 0, R(90))
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", tableR)
plantR = empty("plantR", (-1.55, 1.85, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR)
plantR2 = empty("plantR2", (1.6, 1.95, 0), room); plantR2.scale = (0.8,) * 3; import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR2)
picR = empty("picR", (0.0, 2.24, 1.55), room); picR.scale = (1.6,) * 3; import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR)
picR2 = empty("picR2", (-0.9, 2.24, 1.35), room); import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR2)
lamp_m = mat("lamp_shade", (1.0, 0.85, 0.6), 0.6, emit=3.0, emit_col=(1.0, 0.72, 0.42))
dark_m = mat("lamp_pole_m", (0.08, 0.08, 0.08), 0.3, metal=0.8)
cyl("lamp_pole", 0.015, 1.5, (1.05, 1.9, 0.75), dark_m, parent=room)
cyl("lamp_shade", 0.18, 0.28, (1.05, 1.9, 1.55), lamp_m, parent=room)
cyl("lamp_base", 0.14, 0.03, (1.05, 1.9, 0.015), dark_m, parent=room)
# yozuv stoli + stul + noutbuk (Typing: qo'llar ~0.76 m balandda, y ~ -0.45..-0.53)
ROOMP = Vector((0.0, 0.3, 0.0))
desk_m = pbr("desk", "laminate_floor_02", 1.2, tint=(1.15, 1.05, 0.95))
DESK_Z = 0.73
box("desk_top", (1.3, 0.62, 0.035), (0, -0.55 + ROOMP.y - 0.3, DESK_Z - 0.0175), desk_m, parent=room, bevel=0.006)
for dx in (-0.6, 0.6):
    for dy in (-0.25, 0.25):
        box("desk_leg", (0.04, 0.04, DESK_Z - 0.035), (dx, -0.55 + dy, (DESK_Z - 0.035) / 2), dark_m, parent=room)
chair_m = mat("chair", (0.12, 0.13, 0.16), 0.75)
box("chair_seat", (0.46, 0.44, 0.07), (0, ROOMP.y + 0.02, 0.455), chair_m, parent=room, bevel=0.02)
box("chair_back", (0.44, 0.06, 0.5), (0, ROOMP.y + 0.27, 0.78), chair_m, rot=(-8, 0, 0), parent=room, bevel=0.02)
cyl("chair_post", 0.025, 0.4, (0, ROOMP.y + 0.02, 0.22), dark_m, parent=room)
for a in range(5):
    box("chair_foot", (0.3, 0.04, 0.03), (0.15 * math.cos(R(a * 72)), ROOMP.y + 0.02 + 0.15 * math.sin(R(a * 72)), 0.03),
        dark_m, rot=(0, 0, a * 72), parent=room)
alu_m = mat("alu", (0.55, 0.56, 0.58), 0.3, metal=1.0)
LAP = Vector((0.0, -0.55, DESK_Z))
box("lap_base", (0.32, 0.22, 0.014), tuple(LAP + Vector((0, 0, 0.007))), alu_m, parent=room, bevel=0.003)
box("lap_keys", (0.27, 0.1, 0.002), tuple(LAP + Vector((0, 0.03, 0.0145))), mat("keys", (0.03, 0.03, 0.03), 0.6), parent=room)
lid = empty("lap_lid", tuple(LAP + Vector((0, -0.11, 0.014))), room); lid.rotation_euler = (R(12), 0, 0)
scr_m = bpy.data.materials.new("screen"); scr_m.use_nodes = True
N = scr_m.node_tree.nodes; L = scr_m.node_tree.links; b = N["Principled BSDF"]
tcs = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
wv.inputs["Scale"].default_value = 9.0; L.new(tcs.outputs["Object"], wv.inputs[0])
crs = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], crs.inputs[0])
crs.color_ramp.elements[0].color = (0.75, 0.85, 1.0, 1); crs.color_ramp.elements[1].color = (0.95, 0.97, 1.0, 1)
L.new(crs.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 2.2
b.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
lb = box("lap_lid_b", (0.32, 0.008, 0.21), (0, -0.004, 0.105), alu_m, bevel=0.003); lb.parent = lid
ls = box("lap_screen", (0.29, 0.002, 0.18), (0, 0.001, 0.11), scr_m); ls.parent = lid
cyl("mug", 0.04, 0.1, (-0.36, -0.62, DESK_Z + 0.05), mat("mug_m", (0.85, 0.3, 0.15), 0.3, coat=0.6), parent=room)
box("papers", (0.21, 0.3, 0.01), (0.36, -0.62, DESK_Z + 0.005), mat("paper", (0.92, 0.92, 0.9), 0.8), rot=(0, 0, 12), parent=room)
cyl("dlamp_base", 0.07, 0.02, (0.55, -0.78, DESK_Z + 0.01), dark_m, parent=room)
cyl("dlamp_arm", 0.01, 0.42, (0.55, -0.74, DESK_Z + 0.22), dark_m, rot=(-12, 0, 0), parent=room)
cyl("dlamp_head", 0.06, 0.1, (0.52, -0.66, DESK_Z + 0.42), mat("dlamp_h", (1.0, 0.85, 0.6), 0.5, emit=4.0, emit_col=(1.0, 0.75, 0.45)),
    rot=(-60, 0, 0), parent=room)

# ======================================================================
# 2) MEGAN
# ======================================================================
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
groot, meg, gmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften(gmeshes)
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)
def strip(arm, act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
ST0 = Vector((0, -60, 0))                       # ko'cha
WALK0, WALK1 = 650, 868                         # yurish (kadrlar)
WALK_X0 = float(os.environ.get("WALK_X0", -6.0)); WALK_V = float(os.environ.get("WALK_V", 0.04))   # m/kadr
SW_Y = ST0.y + 1.0                              # trotuar chizig'i
SW_Z = 0.14
place(groot, 1, tuple(ROOMP), rot=0)
place(groot, WALK0, (WALK_X0, SW_Y, SW_Z), rot=90)
place(groot, WALK1, (WALK_X0 + WALK_V * (WALK1 - WALK0), SW_Y, SW_Z), rot=90)
for fc in fcurves(groot):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if WALK0 <= k.co.x < WALK1 else "CONSTANT"
FALL0 = 922
mc.add_strip(meg, A_("Typing.fbx"), -60, blend=0, repeat=(WALK0 + 60) / (495 * 0.8))
strip(meg, A_("Texting_And_Walking.fbx"), WALK0 - 2, blend=0, bout=10, repeat=(WALK1 - WALK0 + 14) / 80.0)
strip(meg, A_("Dizzy_Idle.fbx"), WALK1 - 6, blend=10, bout=6, src=(1, 100))
strip(meg, A_("Dying_9.fbx", inplace=False), FALL0, blend=6, bout=0).extrapolation = "HOLD_FORWARD"
headE = child_of_bone("meg_head", meg, "Head")
neckE = child_of_bone("meg_neck", meg, "Neck")
chestE = child_of_bone("meg_chest", meg, "Spine2")
handR = child_of_bone("meg_handR", meg, "RightHand")
faceT = empty("faceT", (0, 0.09, 0.11), headE)
# telefon (ko'cha): o'ng qo'lda
PH_OFF = tuple(map(float, os.environ.get("PHONE", "0.0,0.07,0.03").split(",")))
phone = empty("phone", PH_OFF, handR); phone.rotation_euler = [R(a) for a in map(float, os.environ.get("PHONE_R", "90,0,0").split(","))]
box("phone_body", (0.072, 0.008, 0.15), (0, 0, 0), mat("phone_b", (0.03, 0.03, 0.035), 0.25, coat=0.8), parent=None, bevel=0.004).parent = phone
pscr = box("phone_scr", (0.066, 0.001, 0.142), (0, 0.0045, 0), mat("phone_s", (0.02, 0.02, 0.03), 0.1, emit=1.6, emit_col=(0.6, 0.75, 1.0)))
pscr.parent = phone
vis(phone, [(WALK0, END)])

# ---- bo'yin burilishi: qo'shimcha suyak burilishlari (COMBINE) ----
B = {n: meg.pose.bones["mixamorig:" + n] for n in ("Spine1", "Spine2", "Neck", "Head")}
TS = float(os.environ.get("TWIST_SIGN", 1.0))   # +Y = chapga burilish (Head o'qi: Y tepa)
def neck(f, yaw=0.0, tilt=0.0, nod=0.0, sp=0.0):
    pq(B["Neck"], f, (nod * 0.4, TS * yaw * 0.42, tilt * 0.4)); pq(B["Head"], f, (nod * 0.6, TS * yaw * 0.58, tilt * 0.6))
    pq(B["Spine2"], f, (sp, 0, 0)); pq(B["Spine1"], f, (sp * 0.6, 0, 0))
CRACK1, CRACK2, CRACK3 = 66, 85, 424                       # "keskin", "qirsillatish", "kuch bilan buraganingizda"
neck(1)
neck(48); neck(58, yaw=-40, tilt=-12); neck(CRACK1 - 2, yaw=-46, tilt=-14); neck(CRACK1, yaw=-66, tilt=-18)
neck(CRACK1 + 6, yaw=-62, tilt=-15); neck(74, yaw=0, tilt=0)
neck(80, yaw=42, tilt=12); neck(CRACK2 - 2, yaw=46, tilt=14); neck(CRACK2, yaw=68, tilt=18); neck(CRACK2 + 8, yaw=64, tilt=15)
neck(108, yaw=0, tilt=0); neck(118, nod=-16, sp=-6); neck(142, nod=-20, sp=-8); neck(160, nod=0, sp=0)
neck(400); neck(414, yaw=-30, tilt=-8); neck(CRACK3 - 2, yaw=-38, tilt=-10); neck(CRACK3 + 1, yaw=-78, tilt=-20)
neck(CRACK3 + 14, yaw=-74, tilt=-18); neck(452, yaw=0)
ov = meg.animation_data.action; ov.name = "neck_overlay"; ov.use_fake_user = True
meg.animation_data.action = None
_tr = meg.animation_data.nla_tracks.new(); _tr.name = "neck_overlay"
_st = _tr.strips.new("neck_overlay", 1, ov)
if hasattr(_st, "action_slot") and ov.slots: _st.action_slot = ov.slots[0]
_st.blend_type = "COMBINE"; _st.extrapolation = "HOLD"; _st.blend_in = _st.blend_out = 0

# ======================================================================
# 3) RENTGEN: shaffof Megan + umurtqalar + arteriyalar + miya
#    Qurollangan mesh'lar armatura fazosida (sm, Y tepa, Z old); bosh fazosi (m): X chap, Y tepa, Z old.
# ======================================================================
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.0, base=0.01)
ghosts = []
for o in gmeshes:
    if any(k in o.name for k in ("Eyelash", "Hair", "Sneakers")): continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, X_SHOTS, recursive=False)
real_ranges = [(1, S["qirs"][0] - 1), (S["relief"][0], S["xneck"][0] - 1), (S["pinch"][0], S["xbrain"][0] - 1), (S["face"][0], END)]
for o in gmeshes: vis(o, real_ranges, recursive=False)
for o in gmeshes:
    if "Hair" in o.name: vis(o, real_ranges, recursive=False)

HB = Vector((0.0, 153.314, 0.203))               # Head suyagi boshi (armatura fazosi, sm)
def h2a(p):   # bosh fazosi (m) -> armatura fazosi (sm)
    return Vector((p[0] * 100.0, p[1] * 100.0 + HB.y, p[2] * 100.0 + HB.z))
def weights(y):
    if y >= 153.0: return {"Head": 1.0}
    if y >= 145.0: t = (y - 145.0) / 8.0; return {"Head": t, "Neck": 1 - t}
    if y >= 141.0: t = (y - 141.0) / 4.0; return {"Neck": t, "Spine2": 1 - t}
    return {"Spine2": 1.0}
def skin(o):
    """o (armatura fazosidagi mesh) suyaklarga bog'lanadi"""
    o.parent = meg; o.matrix_parent_inverse = Matrix.Identity(4)
    vg = {n: o.vertex_groups.new(name="mixamorig:" + n) for n in ("Spine2", "Neck", "Head")}
    for v in o.data.vertices:
        for n, w in weights(v.co.y).items():
            if w > 0: vg[n].add([v.index], w, "REPLACE")
    md = o.modifiers.new("arm", "ARMATURE"); md.object = meg
    return o

def glow_mat(name, col, strength, alpha=1.0, rim=1.5):
    """rentgen uchun yonuvchi (emissiya + chetlari yorqin) material"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    stv = value_node(m, "glow", strength)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], rim), 0.6), stv), em.inputs["Strength"])
    if alpha < 1.0:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
        L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 1 - alpha), alpha, clamp=True), mx.inputs[0])
        L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    else:
        L.new(em.outputs[0], out.inputs[0])
    return m

bone_m = glow_mat("xbone", (0.85, 0.93, 1.0), 1.6)
disc_m = glow_mat("xdisc", (0.3, 0.6, 1.0), 0.9, alpha=0.5)
# umurtqalar C7..C1 (armatura fazosi, sm): tana old tomonda (z ~ +1.6), o'simtalar orqada
VERT_Y = [141.6, 143.4, 145.2, 147.0, 148.8, 150.5, 152.2]
VZ = 1.6
def vertebra(i, y):
    bm = bmesh.new()
    def add_cyl(r, h, loc, axis="Y", segs=20, sx=1.0, sz=1.0):
        mtx = Matrix.Translation(loc)
        if axis == "Y": mtx = mtx @ Matrix.Rotation(R(90), 4, "X")
        elif axis == "X": mtx = mtx @ Matrix.Rotation(R(90), 4, "Y")
        mtx = mtx @ Matrix.Diagonal((sx, sz, 1, 1))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h, matrix=mtx)
    def add_box(size, loc, rx=0.0):
        mtx = Matrix.Translation(loc) @ Matrix.Rotation(R(rx), 4, "X") @ Matrix.Diagonal((*size, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mtx)
    def add_ring(R_, r, loc):
        mtx = Matrix.Translation(loc) @ Matrix.Rotation(R(90), 4, "X")
        res = bmesh.ops.create_circle(bm, cap_ends=False, segments=16, radius=R_, matrix=mtx)
        # halqa: aylana bo'ylab kichik kublar (torus o'rniga, bmesh'da oddiy)
        for k in range(10):
            a = R(k * 36)
            add_box((r * 2.2, r * 2.2, r * 2.2), loc + Vector((R_ * math.cos(a), 0, R_ * math.sin(a))))
        bmesh.ops.delete(bm, geom=res["verts"], context="VERTS")
    atlas = (i == 6)
    if not atlas:
        add_cyl(0.85, 1.15, Vector((0, y, VZ)), sx=1.25, sz=1.0)                      # tana
    for sx in (-1, 1):
        add_ring(0.5, 0.17, Vector((sx * 2.05, y, VZ - 0.2)))                          # ko'ndalang teshik (arteriya o'tadi)
        add_box((1.3, 0.55, 0.6), Vector((sx * 2.75, y, VZ - 0.35)))                   # ko'ndalang o'simta uchi
        add_box((0.7, 0.9, 1.6), Vector((sx * 1.35, y, VZ - 1.2)))                     # bo'g'im ustuni
        add_box((0.45, 0.55, 1.9), Vector((sx * 0.75, y, VZ - 2.3)), rx=0)             # ravoq
    if atlas:
        add_box((1.6, 0.6, 0.55), Vector((0, y, VZ + 0.5)))                              # old ravoq
        add_cyl(0.32, 1.6, Vector((0, y - 0.9, VZ - 0.1)), segs=12)                      # tish (dens) — pastda C2 da
    add_box((0.5, 0.55, 1.8 if not atlas else 0.9), Vector((0, y - 0.35, VZ - 3.2 + (0.6 if atlas else 0))), rx=25)   # o'tkir o'simta
    me = bpy.data.meshes.new(f"C{7 - i}"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(f"C{7 - i}", me); sc.collection.objects.link(o); me.materials.append(bone_m)
    sub = o.modifiers.new("s", "SUBSURF"); sub.levels = 0; sub.render_levels = 1
    return skin(o)
VERTS = [vertebra(i, y) for i, y in enumerate(VERT_Y)]
for i in range(len(VERT_Y) - 1):
    yd = (VERT_Y[i] + VERT_Y[i + 1]) / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.8, depth=0.45, location=(0, yd, VZ), rotation=(R(90), 0, 0))
    d = bpy.context.object; d.name = f"disc{i}"; d.scale = (1.2, 1, 1); bpy.ops.object.transform_apply(scale=True, rotation=True, location=True)
    d.data.materials.append(disc_m); skin(d); VERTS.append(d)
# arteriyalar: o'mrov osti -> ko'ndalang teshiklar -> atlas halqasi -> katta teshik -> asosiy (basilar) arteriya
art_m = P.pulse_material("artery_m", (0.9, 0.02, 0.02), base_emit=1.2, pulse_col=(1.0, 0.06, 0.02), width=0.05)
ART = {}
for sx in (-1, 1):
    pts = [(sx * 3.6, 133.0, 2.2), (sx * 2.9, 137.5, 0.9), (sx * 2.15, 140.5, VZ - 0.2)] + \
          [(sx * 2.05, y, VZ - 0.2) for y in VERT_Y[1:6]] + \
          [(sx * 2.4, 151.4, VZ - 0.3), (sx * 2.7, 152.3, VZ - 0.9), (sx * 2.0, 153.0, VZ - 1.7), (sx * 1.0, 153.8, VZ - 1.4),
           (sx * 0.45, 155.6, VZ + 0.4), (sx * 0.12, 157.5, VZ + 1.4)]
    o = tube_mesh(f"vert_art{sx}", catmull(pts, 0.4), 0.33, art_m, res=12)
    ART[sx] = skin(o)
# miya + bosh suyagi + miya tomirlari (bosh fazosi, m; Head ga bog'langan)
brain_root, brain_m = P.build_brain("brain", None, 0.085)
brain_root.parent = headE; brain_root.location = (0, 0.118, 0.06); brain_root.rotation_euler = (R(-90), 0, 0)
# miya: o'lik qism (insult) — miya fazosidagi nuqta atrofida qorayadi
N = brain_m.node_tree.nodes; L = brain_m.node_tree.links; bb = N["Principled BSDF"]
tcb = N.new("ShaderNodeTexCoord"); tcb.object = brain_root
DEAD_C = (0.32, 0.55, 0.05)                          # chap orqa (ensa) bo'lagi
dead_r = value_node(brain_m, "dead_r", 0.0)
dd = P.math_n(N, L, "DISTANCE", tcb.outputs["Object"], DEAD_C, vec=True)
nzb = N.new("ShaderNodeTexNoise"); nzb.inputs["Scale"].default_value = 4.0; L.new(tcb.outputs["Object"], nzb.inputs[0])
dd = P.math_n(N, L, "ADD", dd, P.math_n(N, L, "MULTIPLY", nzb.outputs["Fac"], 0.25))
mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"; L.new(dd, mr.inputs["Value"])
L.new(P.math_n(N, L, "SUBTRACT", dead_r, 0.12), mr.inputs["From Min"]); L.new(dead_r, mr.inputs["From Max"])
mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
dmask = P.math_n(N, L, "MULTIPLY", mr.outputs[0], P.math_n(N, L, "GREATER_THAN", dead_r, 0.01))
cm_ = N.new("ShaderNodeMix"); cm_.data_type = "RGBA"; L.new(dmask, cm_.inputs["Factor"])
cm_.inputs[6].default_value = bb.inputs["Base Color"].default_value[:]; cm_.inputs[7].default_value = (0.05, 0.03, 0.07, 1)
L.new(cm_.outputs[2], bb.inputs["Base Color"])
em_src = bb.inputs["Emission Strength"].links[0].from_socket
L.new(P.math_n(N, L, "MULTIPLY", em_src, P.math_n(N, L, "SUBTRACT", 1.0, dmask)), bb.inputs["Emission Strength"])
# chegarada qizil halqa
rim_ = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", dmask, P.math_n(N, L, "SUBTRACT", 1.0, dmask)), 4.0)
emc = N.new("ShaderNodeMix"); emc.data_type = "RGBA"; L.new(P.math_n(N, L, "MINIMUM", rim_, 1.0), emc.inputs["Factor"])
emc.inputs[6].default_value = (1.0, 0.55, 0.65, 1); emc.inputs[7].default_value = (1.0, 0.05, 0.02, 1)
L.new(emc.outputs[2], bb.inputs["Emission Color"])
L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", em_src, P.math_n(N, L, "SUBTRACT", 1.0, dmask)), P.math_n(N, L, "MULTIPLY", rim_, 6.0)),
      bb.inputs["Emission Strength"])
skull_m = P.xray_material("xskull", col=(0.85, 0.92, 1.0), strength=0.3, base=0.002)
skull = sphere("skull", 1.0, (0, 0, 0), skull_m, sub=4, parent=headE, world=False)
skull.location = (0, 0.112, 0.06); skull.scale = (0.072, 0.085, 0.098)
# miya tomirlari (bosh fazosi): basilar -> orqa miya arteriyalari (chap tomondagisi tiqiladi)
bv_m = P.pulse_material("bvessel_m", (0.85, 0.02, 0.02), base_emit=1.0, pulse_col=(1.0, 0.08, 0.03), width=0.08)
BAS = [(0, 0.042, 0.03), (0, 0.062, 0.036), (0, 0.08, 0.04)]
P.tube("basilar", catmull([(0, 0.042, 0.03), (0, 0.08, 0.04)], 0.004), 0.0035, bv_m, headE)
PCA = {}
for sx in (-1, 1):
    PCA[sx] = [(0, 0.08, 0.04), (sx * 0.014, 0.084, 0.034), (sx * 0.03, 0.09, 0.02), (sx * 0.04, 0.1, 0.0), (sx * 0.035, 0.115, -0.015)]
    P.tube(f"pca{sx}", catmull(PCA[sx], 0.003), 0.0024, bv_m, headE)
    for j, (a, b_) in enumerate(((2, (0.05, 0.118, 0.04)), (3, (0.05, 0.13, 0.0)), (1, (0.045, 0.12, 0.075)))):
        p0 = Vector(PCA[sx][a]); p1 = Vector((sx * b_[0], b_[1], b_[2]))
        P.tube(f"pcab{sx}{j}", catmull([tuple(p0), tuple((p0 + p1) / 2 + Vector((sx * 0.01, 0.01, 0))), tuple(p1)], 0.003), 0.0016, bv_m, headE)
    mca = [(0, 0.08, 0.04), (sx * 0.02, 0.086, 0.06), (sx * 0.045, 0.1, 0.075), (sx * 0.058, 0.13, 0.06)]
    P.tube(f"mca{sx}", catmull(mca, 0.003), 0.0022, bv_m, headE)
XRAY_OBJS = VERTS + list(ART.values()) + [skull]
xgroup = [brain_root] + [o for o in headE.children_recursive if o.type in ("MESH", "CURVE")]
for o in XRAY_OBJS: vis(o, X_SHOTS, recursive=False)
for o in set(xgroup) - {brain_root}:
    if o.name.startswith(("basilar", "pca", "mca")): vis(o, X_SHOTS, recursive=False)
vis(brain_root, X_SHOTS)
# yurak urishi impulslari (arteriyalar bo'ylab yuqoriga)
def heartbeat(m, f0, f1, period=17, dur=10, glow=None):
    val_key(m, "pos", f0 - 1, -0.2)
    for f in range(f0, f1, period):
        val_key(m, "pos", f, -0.15); val_key(m, "pos", f + dur, 1.15); val_key(m, "pos", f + dur + 1, -0.15)
    nt = m.node_tree
    for fc in (nt.animation_data.action and mc._fcurves(nt.animation_data.action)) or []:
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
heartbeat(art_m, S["xneck"][0], S["xtwist"][1], period=18)
heartbeat(bv_m, S["xneck"][0], S["xtwist"][1], period=18, dur=8)
val_key(art_m, "glow", 1, 1.2); val_key(art_m, "glow", 330, 1.2); val_key(art_m, "glow", 340, 3.0); val_key(art_m, "glow", 397, 3.0)
val_key(art_m, "glow", 398, 1.4)
# qirs: bo'g'imlarda uchqun (C1-C2 orasida)
spark_m = mat("spark", (1, 1, 1), emit=60.0, emit_col=(1.0, 0.95, 0.85))
sparks = empty("sparks", (0, 0, 0), headE)
rs = random.Random(3)
for i in range(14):
    s_ = sphere(f"spark{i}", 0.0012, (0, 0, 0), spark_m, sub=1, parent=sparks, world=False)
    d0 = Vector((rs.uniform(-1, 1), rs.uniform(-0.5, 0.5), rs.uniform(-1, 0.3))).normalized()
    p0 = Vector((rs.choice((-1, 1)) * 0.016, -0.012, -0.004))
    for f, k in ((1, 0.0), (CRACK2 - 1, 0.0), (CRACK2, 0.0)):
        key(s_, f, loc=tuple(p0), scale=(0.001,) * 3)
    for j in range(1, 8):
        key(s_, CRACK2 + j, loc=tuple(p0 + d0 * 0.006 * j), scale=(max(0.001, 1 - j / 8),) * 3)
    interp(s_, "LINEAR")
vis(sparks, rng("qirs"))
# insult: tromb miyaga keladi (bosh fazosi), chap PCA da tiqiladi
TIQ = 852
clot_m = mat("clot_x", (0.25, 0.0, 0.02), 0.4, emit=8.0, emit_col=(1.0, 0.1, 0.03))
xclot = sphere("xclot", 0.0042, (0, 0, 0), clot_m, sub=2, parent=headE, world=False)
cpath = catmull([h2a((0, 0, 0)) * 0 + Vector((0.0, 0.025, 0.026)), Vector((0.0, 0.042, 0.03)), Vector((0, 0.08, 0.04))] +
                [Vector(p) for p in PCA[1][1:4]], 0.004)
X0 = S["xbrain"][0]
for i, f in enumerate(range(X0, TIQ + 1)):
    t = ease(i / (TIQ - X0)); p = cpath[min(len(cpath) - 1, int(t * (len(cpath) - 1)))]
    key(xclot, f, loc=tuple(p))
interp(xclot, "LINEAR", "location")
vis(xclot, rng("xbrain"), recursive=False)
val_key(brain_m, "dead_r", 1, 0.0); val_key(brain_m, "dead_r", TIQ, 0.0); val_key(brain_m, "dead_r", TIQ + 4, 0.15)
val_key(brain_m, "dead_r", S["xbrain"][1], 0.62)
val_key(brain_m, "glow", 1, 0.6); val_key(brain_m, "glow", X0, 0.6)

# ======================================================================
# 4) REVOLVER STUDIYASI (0,120,1): rus ruletkasi
# ======================================================================
RV = Vector((0, 120, 1.0))
rvs = empty("rv_studio", (0, 0, 0))
gun_m = mat("gunmetal", (0.11, 0.115, 0.13), 0.22, metal=1.0, coat=0.3)
brass_m = mat("brass", (0.85, 0.6, 0.25), 0.2, metal=1.0)
prim_m = mat("primer", (0.75, 0.75, 0.78), 0.25, metal=1.0)
felt = mat("felt", (0.05, 0.12, 0.08), 0.95)
plane("rv_table", (8, 8), tuple(RV + Vector((0, 0, -0.205))), felt, parent=rvs)
plane("rv_bg", (8, 6), tuple(RV + Vector((0, 2.5, 1.0))), mat("rv_bgm", (0.02, 0.02, 0.025), 0.9), rot=(90, 0, 0), parent=rvs)
drum = empty("drum", tuple(RV), rvs)
bpy.ops.mesh.primitive_cylinder_add(vertices=72, radius=0.2, depth=0.36, location=(0, 0, 0), rotation=(0, R(90), 0))
cyl_o = bpy.context.object; cyl_o.name = "drum_body"; bpy.ops.object.transform_apply(rotation=True)
cyl_o.data.materials.append(gun_m); cyl_o.parent = drum
cut = []
for k in range(6):
    a = R(k * 60)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.043, depth=0.5, location=(0, 0.12 * math.sin(a), 0.12 * math.cos(a)), rotation=(0, R(90), 0))
    cut.append(bpy.context.object)
    a2 = R(k * 60 + 30)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.032, depth=0.22, location=(0.04, 0.222 * math.sin(a2), 0.222 * math.cos(a2)), rotation=(0, R(90), 0))
    cut.append(bpy.context.object)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.026, depth=0.5, location=(0, 0, 0), rotation=(0, R(90), 0)); cut.append(bpy.context.object)
bpy.ops.object.select_all(action="DESELECT")
for c in cut: c.select_set(True)
bpy.context.view_layer.objects.active = cut[0]; bpy.ops.object.join(); cutter = bpy.context.object; cutter.name = "drum_cutter"
bpy.ops.object.transform_apply(rotation=True)
cutter.hide_render = True; cutter.display_type = "WIRE"
bo = cyl_o.modifiers.new("holes", "BOOLEAN"); bo.object = cutter; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
bv = cyl_o.modifiers.new("bev", "BEVEL"); bv.width = 0.006; bv.segments = 3; bv.limit_method = "ANGLE"
for p in cyl_o.data.polygons: p.use_smooth = True
cyl_o.modifiers.new("wn", "WEIGHTED_NORMAL")
cyl("drum_pin", 0.02, 0.44, (0, 0, 0), mat("pin", (0.6, 0.6, 0.62), 0.2, metal=1.0), rot=(0, 90, 0), parent=None).parent = drum
# o'q: faqat bitta uyada (tepada, k=0)
bul = empty("bullet", (0, 0, 0.12), drum)
for nm_, r_, d_, x_, m_ in (("case", 0.04, 0.34, 0.0, brass_m), ("rim", 0.047, 0.012, -0.178, brass_m), ("prim", 0.012, 0.004, -0.185, prim_m)):
    o = cyl("b_" + nm_, r_, d_, (x_, 0, 0), m_, rot=(0, 90, 0), verts=32); o.parent = bul
rvf = empty("rv_frame", tuple(RV), rvs)       # ramka (qo'zg'almas): yon plastinkalar
box("rv_plate", (0.05, 0.5, 0.12), (-0.215, 0, -0.18), gun_m, bevel=0.01).parent = rvf
box("rv_strap", (0.6, 0.06, 0.05), (0.0, 0, -0.235), gun_m, bevel=0.01).parent = rvf
cut_hide = cutter; cutter.parent = drum
# aylanish: tez -> sekinlashadi -> "chiq" (o'q tepada to'xtaydi)
RV0_, CLICK = S["rv1"][0], 217
TOT = 17.0; END_A = 2 * math.pi * 3
for f in range(RV0_ - 2, CLICK + 1):
    u = min(1.0, max(0.0, (f - RV0_) / (CLICK - RV0_)))
    rem = TOT * (1 - u) ** 3
    drum.rotation_euler = (END_A - rem, 0, 0); drum.keyframe_insert("rotation_euler", frame=f)
for f, d in ((CLICK + 1, R(4)), (CLICK + 3, R(-2)), (CLICK + 5, 0.0)):
    drum.rotation_euler = (END_A + d, 0, 0); drum.keyframe_insert("rotation_euler", frame=f)
interp(drum, "LINEAR", "rotation_euler")
vis(rvs, RV_SHOTS)
cutter.animation_data_clear(); cutter.hide_render = True

# ======================================================================
# 5) TOMIR STUDIYASI (0,60,1): kesilgan arteriya, qon tanachalari, yirtilish, tromb
# ======================================================================
AS = Vector((0, 60, 1.0))
ast = empty("artery_studio", tuple(AS))
RA = 0.36
ZC = 0.0                                             # yirtilish markazi (z)
def vessel_material(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); obj = tc.outputs["Object"]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 5.0; nz.inputs["Detail"].default_value = 6; L.new(obj, nz.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.45, 0.05, 0.06, 1); cr.color_ramp.elements[1].color = (0.85, 0.32, 0.3, 1)
    # ichki devor chiziqlari (bo'ylama burmalar)
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"; wv.inputs["Scale"].default_value = 2.5
    wv.inputs["Distortion"].default_value = 3.0; L.new(obj, wv.inputs[0])
    tear = value_node(m, "tear", 0.0); infl = value_node(m, "infl", 0.0)
    # yoriq: orqa devorda (y>0) x~0, z~ZC atrofida, egri-bugri chiziq
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(obj, sep.inputs[0])
    nzt = N.new("ShaderNodeTexNoise"); nzt.inputs["Scale"].default_value = 3.0; nzt.inputs["Detail"].default_value = 8; L.new(obj, nzt.inputs[0])
    xw = P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "ADD", sep.outputs["X"], P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", nzt.outputs["Fac"], 0.5), 0.18)))
    zl = P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", sep.outputs["Z"], ZC))
    half = P.math_n(N, L, "MULTIPLY", tear, 0.55)
    zin = P.math_n(N, L, "LESS_THAN", zl, half)
    taper = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", zl, P.math_n(N, L, "ADD", half, 0.001)), clamp=True)
    width = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", taper, tear), 0.045)
    back = P.math_n(N, L, "GREATER_THAN", sep.outputs["Y"], 0.05)
    core = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", xw, width), zin), back)
    edge = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", xw, P.math_n(N, L, "ADD", width, 0.025)), zin), back)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(core, c1.inputs["Factor"]); L.new(cr.outputs[0], c1.inputs[6])
    c1.inputs[7].default_value = (0.04, 0.0, 0.005, 1)
    L.new(c1.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.8; b.inputs["Coat Roughness"].default_value = 0.05
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.05
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.03, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", edge, core), 8.0),
                   P.math_n(N, L, "MULTIPLY", infl, P.math_n(N, L, "ADD", nz.outputs["Fac"], 0.1))), b.inputs["Emission Strength"])
    bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.35; bmp.inputs["Distance"].default_value = 0.02
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", wv.outputs["Fac"], 0.5), P.math_n(N, L, "MULTIPLY", edge, 2.0)), bmp.inputs["Height"])
    L.new(bmp.outputs[0], b.inputs["Normal"])
    return m
ves_m = vessel_material("vessel")
VZ0, VZ1 = -4.0, 9.0
vpts = [(0.04 * math.sin(z * 0.7), 0.0, z) for z in [VZ0 + i * 0.25 for i in range(int((VZ1 - VZ0) / 0.25) + 1)]]
ves = tube_mesh("vessel", vpts, RA, ves_m, res=40, arc=(-60, 240))     # old tomoni (-Y) ochiq: kesim
ves.parent = ast
sol = ves.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.06; sol.offset = -1.0
cut_m = mat("vessel_cut", (0.95, 0.55, 0.5), 0.4, sss=0.3, sss_scale=0.05)
ves.data.materials.append(cut_m); sol.material_offset_rim = 1
# qisilish: shape key (x bo'yicha siqiladi)
ves.shape_key_add(name="basis", from_mix=False)
kpinch = ves.shape_key_add(name="pinch", from_mix=False); kpinch.value = 0.0
for v, kv in zip(ves.data.vertices, kpinch.data):
    g = math.exp(-((v.co.z - ZC) / 0.55) ** 2)
    kv.co = (v.co.x * (1 - 0.55 * g), v.co.y * (1 + 0.12 * g), v.co.z)
# orqa fondagi boshqa tomirlar va to'qima
bgv_m = vessel_material("vessel_bg")
rb = random.Random(5)
for j in range(7):
    y = 1.3 + j * 0.55; x0 = rb.uniform(-2.2, 2.2)
    pts = [(x0 + 0.5 * math.sin(k * 1.1 + j), y + rb.uniform(-0.3, 0.3), -4.0 + k * 1.6) for k in range(9)]
    o = tube_mesh(f"bg_v{j}", catmull(pts, 0.2), rb.uniform(0.18, 0.34), bgv_m, res=16); o.parent = ast
cav_m = mat("cavity", (0.25, 0.04, 0.05), 0.35, sss=0.3, sss_scale=0.1, coat=1.0)
cav = sphere("cavity", 9.0, (0, 0, 0), cav_m, sub=4, parent=ast, world=False); cav.location = (0, 3.0, 2.0); cav.scale = (1, 1, 1.4)
# umurtqa bo'laklari (qisish): ikki tomondan keladi
bonep_m = mat("bone_piece", (0.88, 0.82, 0.68), 0.6, sss=0.2, sss_scale=0.05)
nzbone = bpy.data.textures.new("bone_n", "CLOUDS"); nzbone.noise_scale = 0.08
PIN0, PINCH = S["pinch"][0], 481
bones_ = []
for sx in (-1, 1):
    bp_ = sphere(f"vbone{sx}", 1.0, (0, 0, 0), bonep_m, sub=4, parent=ast, world=False)
    bp_.scale = (0.5, 0.6, 0.5)
    dm = bp_.modifiers.new("d", "DISPLACE"); dm.texture = nzbone; dm.strength = 0.08
    for f, x in ((1, 1.6), (PIN0, 1.6), (PINCH - 10, 1.15), (PINCH, 0.72), (PINCH + 18, 0.75), (S["pinch"][1], 1.0)):
        key(bp_, f, loc=(sx * x, 0.25, ZC + 0.05))
    bones_.append(bp_)
    vis(bp_, rng("pinch"), recursive=False)
for f, v in ((1, 0.0), (PIN0, 0.0), (PINCH - 6, 0.15), (PINCH, 1.0), (PINCH + 18, 0.92), (S["pinch"][1], 0.4), (S["tear"][0], 0.0)):
    kpinch.value = v; kpinch.keyframe_insert("value", frame=f)
def pinch_at(f):
    """qon tanachalari uchun: shu kadrdagi qisilish (0..1)"""
    pts_ = [(1, 0.0), (PIN0, 0.0), (PINCH - 6, 0.15), (PINCH, 1.0), (PINCH + 18, 0.92), (S["pinch"][1], 0.4), (S["tear"][0], 0.0)]
    for (fa, va), (fb, vb) in zip(pts_, pts_[1:]):
        if fa <= f <= fb: return va + (vb - va) * (f - fa) / max(1, fb - fa)
    return 0.0
# yirtilish
TEAR_F = 550
val_key(ves_m, "tear", 1, 0.0); val_key(ves_m, "tear", TEAR_F - 2, 0.0); val_key(ves_m, "tear", TEAR_F + 3, 0.7)
val_key(ves_m, "tear", TEAR_F + 20, 0.85); val_key(ves_m, "tear", S["tear"][1], 0.95)
val_key(ves_m, "infl", 1, 0.0); val_key(ves_m, "infl", PINCH - 2, 0.0); val_key(ves_m, "infl", PINCH + 2, 1.5)
val_key(ves_m, "infl", PINCH + 20, 0.4); val_key(ves_m, "infl", TEAR_F - 1, 0.3); val_key(ves_m, "infl", TEAR_F + 2, 2.0)
val_key(ves_m, "infl", TEAR_F + 18, 0.5); val_key(ves_m, "infl", S["clot"][0], 0.3)
# qon tanachalari (eritrotsitlar): disk shaklida, oqim +Z (miyaga)
rbc_m = mat("rbc", (0.75, 0.04, 0.03), 0.3, sss=0.5, sss_scale=0.03, coat=0.6)
plt_m = mat("platelet", (0.95, 0.75, 0.5), 0.4, sss=0.4, sss_scale=0.02)
cells = empty("cells", (0, 0, 0), ast)
rc = random.Random(21)
C0, C1 = S["pinch"][0] - 2, S["brk"][1] + 2
VEL = 0.045
NC = int(os.environ.get("NCELLS", 170))
for i in range(NC):
    plate = i % 9 == 0
    s_ = sphere(f"rbc{i}", 1.0, (0, 0, 0), plt_m if plate else rbc_m, sub=4 if not plate else 2, parent=cells, world=False)
    if not plate:
        for v in s_.data.vertices:                                   # bikonkav disk
            rr = math.hypot(v.co.x, v.co.y); v.co.z *= 0.35 * (0.45 + 0.9 * rr * rr)
    sz = rc.uniform(0.045, 0.06) if not plate else rc.uniform(0.018, 0.026)
    s_.scale = (sz,) * 3
    s_.rotation_euler = (rc.uniform(0, 6.3), rc.uniform(0, 6.3), rc.uniform(0, 6.3)); s_.keyframe_insert("rotation_euler", frame=C0)
    s_.rotation_euler = (s_.rotation_euler.x + rc.uniform(-6, 6), s_.rotation_euler.y + rc.uniform(-6, 6), 0)
    s_.keyframe_insert("rotation_euler", frame=C1)
    rr = RA * 0.78 * math.sqrt(rc.random()); aa = rc.uniform(0, 6.283)
    x0, y0 = rr * math.cos(aa), rr * math.sin(aa)
    ph = rc.uniform(0, VZ1 - VZ0); v_ = VEL * rc.uniform(0.75, 1.25)
    prev = None
    for f in range(C0, C1 + 1, 4):
        z = VZ0 + (ph + v_ * (f - C0)) % (VZ1 - VZ0 - 0.4)
        g = math.exp(-((z - ZC) / 0.55) ** 2) * pinch_at(f)
        key(s_, f, loc=(x0 * (1 - 0.6 * g) + 0.04 * math.sin(z * 0.7), y0 * (1 - 0.3 * g), z))
    fcz = [fc for fc in fcurves(s_) if fc.data_path == "location"]
    for fc in fcz:
        kp = fcurves(s_)
    zc_ = next(fc for fc in fcurves(s_) if fc.data_path == "location" and fc.array_index == 2)
    ks = zc_.keyframe_points
    wrap = set(j for j in range(len(ks) - 1) if ks[j + 1].co.y < ks[j].co.y)
    for fc in fcz:
        for j, k in enumerate(fc.keyframe_points): k.interpolation = "CONSTANT" if j in wrap else "LINEAR"
vis(cells, AS_SHOTS)
# tromb: yirtilgan joyda o'sadi, keyin uzilib oqim bilan ketadi
CL0, CL1 = S["clot"]; BR0, BR1 = S["brk"]
clotE = empty("clotE", (0, RA - 0.06, ZC), ast)
clotg_m = mat("clot", (0.22, 0.01, 0.02), 0.35, sss=0.3, sss_scale=0.02, coat=0.7)
fib_m = mat("fibrin", (0.95, 0.88, 0.7), 0.5, sss=0.4, sss_scale=0.02, emit=0.3, emit_col=(1.0, 0.85, 0.6))
rcl = random.Random(9)
for i in range(34):
    p = Vector((rcl.gauss(0, 0.06), rcl.uniform(-0.12, 0.0), rcl.gauss(0, 0.16)))
    o = sphere(f"clotb{i}", rcl.uniform(0.035, 0.07), (0, 0, 0), rbc_m if i % 3 else clotg_m, sub=3, parent=clotE, world=False)
    o.location = p
    dm = o.modifiers.new("d", "DISPLACE"); dm.texture = nzbone; dm.strength = 0.02
    t0 = CL0 + 6 + int(i * (CL1 - CL0 - 18) / 34)
    s0 = o.scale.copy()
    for f, k in ((1, 0.001), (t0, 0.001), (t0 + 8, 1.0)): key(o, f, scale=(k, k, k))
for i in range(12):
    a0 = Vector((rcl.gauss(0, 0.07), rcl.uniform(-0.1, 0.0), rcl.gauss(0, 0.18)))
    a1 = a0 + Vector((rcl.uniform(-0.15, 0.15), rcl.uniform(-0.08, 0.02), rcl.uniform(-0.2, 0.2)))
    o = tube_mesh(f"fib{i}", [a0, (a0 + a1) / 2 + Vector((0, -0.03, 0)), a1], 0.006, fib_m, res=6); o.parent = clotE
    t0 = CL0 + 20 + i * 4
    for f, k in ((1, 0.001), (t0, 0.001), (t0 + 10, 1.0)): key(o, f, scale=(k, k, k))
UZ = 758                                            # "uzilib"
key(clotE, 1, loc=(0, RA - 0.06, ZC), rot=(0, 0, 0))
key(clotE, UZ - 6, loc=(0, RA - 0.06, ZC), rot=(0, 0, 0))
for j, f in enumerate(range(UZ - 6, UZ)):
    key(clotE, f, loc=(0.01 * math.sin(j * 2.3), RA - 0.06 + 0.008 * math.cos(j * 3.1), ZC))
key(clotE, UZ + 4, loc=(0.02, RA - 0.2, ZC + 0.15), rot=(10, 0, 15))
for k, f in enumerate(range(UZ + 6, BR1 + 3, 2)):
    t = (f - UZ - 6)
    key(clotE, f, loc=(0.03 * math.sin(t * 0.2), 0.12 - 0.04 * math.sin(t * 0.1), ZC + 0.15 + 0.0022 * t * t + 0.02 * t), rot=(10 + t * 6, t * 3, 15 + t * 4))
interp(clotE, "BEZIER")
vis(ast, AS_SHOTS)

# ======================================================================
# 6) KO'CHA (0,-60,0): kunduz, trotuar, Audi
# ======================================================================
street = empty("street", (0, 0, 0))
asph = pbr("asphalt", "asphalt_02", 0.25)
conc = pbr("concrete", "concrete_pavement", 0.4)
grass_m = mat("grass", (0.13, 0.28, 0.07), 0.9)
plane("road", (80, 8), tuple(ST0 + Vector((0, -4.0, 0))), asph, parent=street)
box("sidewalk", (80, 2.4, SW_Z), tuple(ST0 + Vector((0, 1.2, SW_Z / 2))), conc, parent=street)
box("curb", (80, 0.15, 0.16), tuple(ST0 + Vector((0, 0.0, 0.08))), conc, parent=street)
plane("lawn", (80, 4), tuple(ST0 + Vector((0, 4.4, 0.12))), grass_m, parent=street)
plane("ground", (300, 300), tuple(ST0 + Vector((0, 0, -0.02))), grass_m, parent=street)
line_m = mat("lines", (0.9, 0.9, 0.85), 0.6)
for x in range(-40, 41, 6): box("line", (3, 0.15, 0.01), tuple(ST0 + Vector((x, -4.0, 0.005))), line_m, parent=street)
house_cols = [(0.82, 0.74, 0.6), (0.65, 0.72, 0.78), (0.88, 0.86, 0.82), (0.72, 0.56, 0.46), (0.68, 0.72, 0.62)]
roof_m = mat("roof", (0.2, 0.18, 0.18), 0.8)
glass_m = mat("glass", (0.03, 0.04, 0.05), 0.05, coat=1.0)
trim_m = mat("trim", (0.94, 0.94, 0.92), 0.4)
for i, x in enumerate(range(-24, 25, 8)):
    hm = pbr(f"house{i}", "painted_plaster_wall", 0.4, tint=house_cols[i % 5])
    box(f"house{i}", (6.5, 6, 3.6), tuple(ST0 + Vector((x, 9.5, 1.8))), hm, parent=street)
    box(f"hroof{i}", (7.0, 6.6, 0.4), tuple(ST0 + Vector((x, 9.5, 3.8))), roof_m, parent=street)
    for dx in (-1.8, 1.8):
        box("hw", (1.2, 0.06, 1.3), tuple(ST0 + Vector((x + dx, 6.47, 1.8))), glass_m, parent=street)
        box("hwf", (1.35, 0.04, 1.45), tuple(ST0 + Vector((x + dx, 6.49, 1.8))), trim_m, parent=street)
    box("hdoor", (1.0, 0.06, 2.1), tuple(ST0 + Vector((x, 6.47, 1.05))), mat(f"hd{i}", house_cols[(i + 2) % 5], 0.4, coat=0.4), parent=street)
leaves_m = mat("leaves", (0.1, 0.25, 0.06), 0.7)
bark_m = mat("bark", (0.2, 0.13, 0.08), 0.9)
for x in (-14, -5, 7, 16):
    cyl("trunk", 0.12, 2.4, tuple(ST0 + Vector((x, 2.9, 1.2))), bark_m, parent=street, verts=12)
    for dx, dy, dz, r in ((0, 0, 3.0, 1.2), (0.6, 0.2, 2.6, 0.8), (-0.5, -0.3, 2.7, 0.9), (0.1, 0.4, 3.6, 0.8)):
        o = sphere("crown", r, tuple(ST0 + Vector((x + dx, 2.9 + dy, dz))), leaves_m, sub=3, parent=street)
        dm = o.modifiers.new("d", "DISPLACE"); dm.strength = 0.35
        t = bpy.data.textures.new("cl", "CLOUDS"); t.noise_scale = 0.4; dm.texture = t
pole_m = mat("pole", (0.05, 0.05, 0.055), 0.4, metal=0.6)
for x in (-12, 12, 24):
    cyl("lamppost", 0.06, 4.5, tuple(ST0 + Vector((x, 0.35, 2.25))), pole_m, parent=street, verts=12)
carR = empty("carR", tuple(ST0 + Vector((-9.5, -1.15, 0.0))), street)
car_objs = import_gltf(BK + "c3c28d91_u.glb", carR)
bpy.context.view_layer.update()
mins = Vector((1e9,) * 3); maxs = Vector((-1e9,) * 3)
for o in car_objs:
    if o.type != "MESH": continue
    for c_ in o.bound_box:
        w_ = o.matrix_world @ Vector(c_); mins = Vector(map(min, mins, w_)); maxs = Vector(map(max, maxs, w_))
if (maxs - mins).y > (maxs - mins).x: carR.rotation_euler.z = R(90)
bpy.context.view_layer.update()
carR.location.z -= mins.z
vis(street, ST_SHOTS)
vis(room, ROOM_SHOTS)

# ======================================================================
# 7) KAMERALAR
# ======================================================================
# 1 ilgak: stol sathidan, past burchak 16 mm, push-in
HO0, HO1 = S["hook"]
hT = follow_target("hookT", headE, HO0, HO1 + 2, local=(0, 0.06, 0.06))
c = shot_cam("hook", (0, 0, 0), hT, 16, 3.5, focus=hT)
key(c, HO0, loc=(-0.85, -1.55, 0.78)); key(c, HO1, loc=(-0.55, -1.05, 0.84))
lens_keys(c, ((HO0, 16), (HO1, 21)))
# 2 burish: yuzga yaqin, f/2, yonga suriladi
TW0, TW1 = S["twist"]
tT = follow_target("twistT", faceT, TW0, TW1 + 2)
c = shot_cam("twist", (0, 0, 0), tT, 55, 2.0, focus=tT)
cam_rel(c, TW0, TW1, faceT, TW0, lambda t: lerp3((0.32, -0.62, -0.02), (0.08, -0.55, 0.0), t))
shake(c, CRACK1, CRACK1 + 8, 0.008, 2)
# 3 qirs: rentgen bo'yin, crash zoom
Q0, Q1 = S["qirs"]
qT = follow_target("qirsT", headE, Q0, Q1 + 2, local=(0, -0.01, 0.0))
c = shot_cam("qirs", (0, 0, 0), qT, 32, 4.0, focus=qT)
cam_rel(c, Q0, Q1, headE, Q0, lambda t: lerp3((-0.3, -0.26, 0.04), (-0.24, -0.2, 0.03), t))
lens_keys(c, ((Q0, 30), (CRACK2 - 1, 34), (CRACK2 + 2, 60), (Q1, 64)))
shake(c, CRACK2, CRACK2 + 12, 0.012, 3)
# 4 yengillik: o'rta plan, aylanma
RL0, RL1 = S["relief"]
rT = follow_target("reliefT", chestE, RL0, RL1 + 2, local=(0, 0.25, 0.05))
c = shot_cam("relief", (0, 0, 0), rT, 30, 2.8, focus=faceT)
pc = Vector(ROOMP) + Vector((0, 0, 1.0))
for f in range(RL0, RL1 + 1, 3):
    t = (f - RL0) / (RL1 - RL0); a = R(25 - 40 * t); rr = 1.4 - 0.15 * t
    key(c, f, loc=tuple(pc + Vector((rr * math.sin(a), -rr * math.cos(a), 0.15 + 0.04 * t))))
# 5 revolver: past aylanma
R10, R11 = S["rv1"]
rvT = empty("rvT", tuple(RV + Vector((0.0, 0, 0.0))))
c = shot_cam("rv1", (0, 0, 0), rvT, 40, 2.8, focus=rvT)
for f in range(R10, R11 + 1, 2):
    t = (f - R10) / (R11 - R10); a = R(-35 + 50 * t); rr = 1.55 - 0.2 * t
    key(c, f, loc=tuple(RV + Vector((rr * math.sin(a), -rr * math.cos(a), 0.02 + 0.06 * t))))
interp(c, "LINEAR", "location")
# 6 revolver: orqa yuzdan, crash zoom ("chiq")
R20, R21 = S["rv2"]
rv2T = empty("rv2T", tuple(RV + Vector((-0.18, 0, 0.08))))
c = shot_cam("rv2", (0, 0, 0), rv2T, 32, 3.5, focus=rv2T)
key(c, R20, loc=tuple(RV + Vector((-0.95, -0.42, 0.2)))); key(c, CLICK, loc=tuple(RV + Vector((-0.8, -0.32, 0.18))))
key(c, R21, loc=tuple(RV + Vector((-0.72, -0.26, 0.17))))
lens_keys(c, ((R20, 32), (CLICK, 36), (CLICK + 2, 50), (R21, 55)))
shake(c, CLICK, CLICK + 10, 0.01, 6)
# 7 rentgen: bo'yindan miyaga kran
XN0, XN1 = S["xneck"]
xnT = empty("xneckT", (0, 0, 0))
c = shot_cam("xneck", (0, 0, 0), xnT, 30, 4.0, focus=xnT)
for f in range(XN0, XN1 + 2, 2):
    t = ease((f - XN0) / (XN1 - XN0))
    p = wpos(neckE, f, (0, 0.0, 0.0)).lerp(wpos(headE, f, (0, 0.12, 0.06)), t)
    key(xnT, f, loc=tuple(p))
    key(c, f, loc=tuple(p + Vector((-0.55 + 0.1 * t, -0.42 + 0.05 * t, -0.05 + 0.12 * t))))
# 8 ikki arteriya: orqadan yaqin, aylanma
XA0, XA1 = S["xart"]
xaT = follow_target("xartT", neckE, XA0, XA1 + 2, local=(0, 0.04, -0.01))
c = shot_cam("xart", (0, 0, 0), xaT, 40, 4.0, focus=xaT)
nc = wpos(neckE, XA0, (0, 0.04, -0.01))
for f in range(XA0, XA1 + 1, 3):
    t = (f - XA0) / (XA1 - XA0); a = R(150 + 60 * t); rr = 0.42 - 0.08 * t
    key(c, f, loc=tuple(nc + Vector((rr * math.sin(a), -rr * math.cos(a), 0.06 - 0.03 * t))))
# 9 rentgen burilish: yondan-orqadan, silkinish
XT0, XT1 = S["xtwist"]
xtT = follow_target("xtwT", neckE, XT0, XT1 + 2, local=(0, 0.06, 0.0))
c = shot_cam("xtwist", (0, 0, 0), xtT, 32, 4.0, focus=xtT)
cam_rel(c, XT0, XT1, neckE, XT0, lambda t: lerp3((0.5, 0.3, 0.12), (0.4, 0.22, 0.1), t), local=(0, 0.06, 0.0))
shake(c, CRACK3, CRACK3 + 12, 0.015, 9)
lens_keys(c, ((XT0, 30), (CRACK3 - 1, 34), (CRACK3 + 2, 44), (XT1, 46)))
# 10 qisish: tomir studiyasi
PI0, PI1 = S["pinch"]
pT = empty("pinchT", tuple(AS + Vector((0, 0.1, ZC))))
c = shot_cam("pinch", (0, 0, 0), pT, 26, 4.0, focus=pT)
key(c, PI0, loc=tuple(AS + Vector((0.5, -2.7, 0.9)))); key(c, PI1, loc=tuple(AS + Vector((0.25, -2.1, 0.6))))
shake(c, PINCH - 2, PINCH + 10, 0.05, 10)
# 11 yirtilish: tomir ichi, crash zoom
TE0, TE1 = S["tear"]
teT = empty("tearT", tuple(AS + Vector((0, RA - 0.05, ZC))))
c = shot_cam("tear", (0, 0, 0), teT, 24, 3.5, focus=teT)
key(c, TE0, loc=tuple(AS + Vector((-0.5, -1.6, 0.7)))); key(c, TEAR_F, loc=tuple(AS + Vector((-0.3, -1.25, 0.45))))
key(c, TE1, loc=tuple(AS + Vector((-0.12, -0.85, 0.25))))
lens_keys(c, ((TE0, 24), (TEAR_F - 1, 28), (TEAR_F + 2, 48), (TE1, 52)))
shake(c, TEAR_F, TEAR_F + 12, 0.04, 11)
# 12 sezmaysiz: yon tomondan push-in
UN0, UN1 = S["unaware"]
uT = follow_target("unawareT", faceT, UN0, UN1 + 2)
c = shot_cam("unaware", (0, 0, 0), uT, 35, 2.4, focus=uT)
cam_rel(c, UN0, UN1, faceT, UN0, lambda t: lerp3((-0.85, -0.75, -0.18), (-0.62, -0.55, -0.14), t, e=False))
# 13 tromb: tomir bo'ylab suriladi
CLT = empty("clotT", tuple(AS + Vector((0, RA - 0.12, ZC))))
c = shot_cam("clot", (0, 0, 0), CLT, 34, 3.2, focus=CLT)
key(c, CL0, loc=tuple(AS + Vector((0.55, -1.25, -0.9)))); key(c, CL1, loc=tuple(AS + Vector((0.15, -0.95, 0.2))))
# 14 ko'cha: past burchak, ergashadi
WK0, WK1 = S["walk"]
wT = follow_target("walkT", chestE, WK0, WK1 + 2, local=(0, -0.1, 0))
c = shot_cam("walk", (0, 0, 0), wT, 18, 5.6, focus=wT)
for f in range(WK0, WK1 + 2, 2):
    p = wpos(chestE, f); t = (f - WK0) / (WK1 - WK0)
    key(c, f, loc=(p.x + 2.6 - 0.6 * t, ST0.y - 0.6, 0.4 + 0.08 * t))
interp(c, "LINEAR", "location")
# 15 tromb uziladi: ergashuvchi kamera
B0_, B1_ = S["brk"]
bT = empty("brkT", (0, 0, 0))
c = shot_cam("brk", (0, 0, 0), bT, 30, 3.2, focus=bT)
for f in range(B0_, B1_ + 2, 2):
    pw = wpos(clotE, f); key(bT, f, loc=tuple(pw))
    t = (f - B0_) / (B1_ - B0_)
    lag = Vector((0.45 - 0.2 * t, -1.35 + 0.25 * t, -0.35 - 0.2 * min(1, max(0, (f - UZ) / 20))))
    key(c, f, loc=tuple(pw + lag))
interp(c, "LINEAR", "location"); interp(bT, "LINEAR", "location")
shake(c, UZ, UZ + 10, 0.03, 15)
# 16 rentgen miya: tromb tiqiladi
XB0, XB1 = S["xbrain"]
xbT = follow_target("xbrainT", headE, XB0, XB1 + 2, local=(0, 0.1, 0.03))
c = shot_cam("xbrain", (0, 0, 0), xbT, 38, 4.0, focus=xbT)
cam_rel(c, XB0, XB1, headE, XB0, lambda t: lerp3((-0.2, 0.42, 0.32), (-0.14, 0.3, 0.24), t), local=(0, 0.1, 0.03))
lens_keys(c, ((XB0, 36), (TIQ - 1, 40), (TIQ + 2, 58), (XB1, 62)))
shake(c, TIQ, TIQ + 12, 0.012, 16)
# 17 yuz: yaqin plan
FA0, FA1 = S["face"]
fT = follow_target("faceT2", faceT, FA0, FA1 + 2)
c = shot_cam("face", (0, 0, 0), fT, 70, 1.8, focus=fT)
cam_rel(c, FA0, FA1, faceT, FA0, lambda t: lerp3((0.95, -0.45, -0.06), (0.8, -0.3, -0.04), t))
# 18 yiqilish: past burchak keng, kran
CO0, CO1 = S["collapse"]
coT = follow_target("collapseT", chestE, CO0, CO1 + 2, local=(0, 0.0, 0))
c = shot_cam("collapse", (0, 0, 0), coT, 20, 4.0, focus=coT)
cp = wpos(groot, CO0)
key(c, CO0, loc=tuple(cp + Vector((2.5, -1.7, 0.3)))); key(c, CO1, loc=tuple(cp + Vector((2.2, -1.5, 1.2))))
shake(c, FALL0 + 40, FALL0 + 52, 0.02, 18)
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 8) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(120)); L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
bg_sky = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_sky.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.002, 0.004, 0.012, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_sky.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
for f, n in SHOTS:
    s1, s2 = (0.03, 0.0) if n in ROOM_N else ((1.0, 0.0) if n in ST_N else (0.0, 1.0))
    for bgn, v in ((bg_sky, s1), (bg_dk, s2)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.0); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(50), 0, R(-140))
for f, n in SHOTS:
    sun.data.energy = 4.0 if n in ST_N else 0.0; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
# xona (kechqurun): noutbuk ekrani (sovuq), chiroq (iliq), kontur
chestT = empty("chestT", tuple(ROOMP + Vector((0, 0, 1.0))))
scrT = empty("scrT", tuple(ROOMP + Vector((0, 0, 1.1))))
area("laptop_glow", tuple(LAP + Vector((0, -0.05, 0.16))), 0.3, (0.7, 0.82, 1.0), lights_for(ROOM_SHOTS, 22.0), target=scrT)
area("room_key", (-1.3, -1.2, 1.9), 1.2, (1.0, 0.75, 0.5), lights_for(ROOM_SHOTS, 70.0), target=chestT)
area("room_rim", (0.9, 1.4, 2.0), 0.8, (1.0, 0.65, 0.4), lights_for(ROOM_SHOTS, 120.0), target=chestT)
area("room_fill", (1.6, -1.4, 1.2), 1.5, (0.4, 0.5, 0.9), lights_for(ROOM_SHOTS, 25.0), target=chestT)
point("lamp_light", (1.05, 1.9, 1.5), 0.15, (1.0, 0.65, 0.35), lights_for(ROOM_SHOTS, 80.0))
point("dlamp_light", (0.5, -0.6, DESK_Z + 0.35), 0.06, (1.0, 0.7, 0.4), lights_for(ROOM_SHOTS, 25.0))
# rentgen
xT_ = empty("xlightT", tuple(ROOMP + Vector((0, 0, 1.4))))
area("x_rim", (0.8, 1.8, 1.9), 1.0, (0.3, 0.6, 1.0), lights_for(X_SHOTS, 25.0), target=xT_)
point("x_qirs", (0, -0.01, -0.005), 0.01, (1.0, 1.0, 1.0), [(1, 0), (CRACK2 - 1, 0), (CRACK2, 30), (CRACK2 + 4, 4), (CRACK2 + 10, 0)], parent=headE, const=False)
point("x_twist", (0, -0.02, 0.0), 0.01, (1.0, 0.15, 0.05), [(1, 0), (CRACK3, 0), (CRACK3 + 1, 15), (CRACK3 + 8, 2), (XT1, 2), (XT1 + 1, 0)], parent=headE, const=False)
pl = point("x_stroke", (0, 0, 0), 0.02, (1.0, 0.08, 0.03), [(1, 0)], parent=brain_root, const=False); pl.location = DEAD_C
for f in range(TIQ, XB1 + 1, 8):
    pl.data.energy = 12.0; pl.data.keyframe_insert("energy", frame=f); pl.data.energy = 3.0; pl.data.keyframe_insert("energy", frame=f + 4)
pl.data.energy = 0; pl.data.keyframe_insert("energy", frame=XB1 + 1); pl.data.keyframe_insert("energy", frame=TIQ - 1)
# revolver
area("rv_key", tuple(RV + Vector((-0.6, -0.8, 1.2))), 0.8, (1.0, 0.9, 0.8), lights_for(RV_SHOTS, 160.0), target=rvT)
area("rv_rim", tuple(RV + Vector((0.6, 1.0, 0.5))), 1.0, (1.0, 0.1, 0.05), lights_for(RV_SHOTS, 160.0), target=rvT)
area("rv_fill", tuple(RV + Vector((0.9, -0.9, 0.1))), 0.8, (0.4, 0.55, 1.0), lights_for(RV_SHOTS, 20.0), target=rvT)
point("rv_click", tuple(RV + Vector((-0.4, -0.2, 0.3))), 0.1, (1.0, 0.1, 0.03), [(1, 0), (CLICK, 0), (CLICK + 1, 60), (CLICK + 6, 8), (R21 + 1, 0)], const=False)
# tomir studiyasi
asT = empty("asT", tuple(AS + Vector((0, 0.2, 0.5))))
area("a_key", tuple(AS + Vector((-1.6, -2.6, 1.8))), 1.5, (1.0, 0.88, 0.82), lights_for(AS_SHOTS, 300.0), target=asT)
area("a_rim", tuple(AS + Vector((1.8, 0.8, 1.2))), 1.2, (1.0, 0.4, 0.35), lights_for(AS_SHOTS, 200.0), target=asT)
area("a_fill", tuple(AS + Vector((1.4, -2.0, -1.2))), 1.0, (0.55, 0.7, 1.0), lights_for(AS_SHOTS, 80.0), target=asT)
fl = area("a_follow", (0, 0, 0), 0.8, (1.0, 0.85, 0.8), lights_for(rng("brk"), 160.0), target=bT)
fl.parent = CAMS["brk"]; fl.location = (0.4, 0.3, 0.2)
point("a_pinch", tuple(AS + Vector((0, -0.5, ZC))), 0.2, (1.0, 0.2, 0.08), [(1, 0), (PINCH - 1, 0), (PINCH + 1, 200), (PINCH + 8, 30), (PI1 + 1, 0)], const=False)
point("a_tear", tuple(AS + Vector((0, -0.2, ZC))), 0.2, (1.0, 0.25, 0.1), [(1, 0), (TEAR_F - 1, 0), (TEAR_F + 1, 250), (TEAR_F + 6, 40), (TE1 + 1, 0)], const=False)

# ======================================================================
# 9) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.1
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
