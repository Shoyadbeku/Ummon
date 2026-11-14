# "Quloqni paxtali cho'p bilan tozalash — oltingugurt tiqini" — Zack D. Films uslubida 40.9 s video (982 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, quloq/quloq.py (quloq yo'li kesimi, parda, tayoqcha, rentgen bosh).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_paxta.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 python3 -I zack_test/paxta/paxta.py --render
# Sinov: FRAMES=20,60,130,200 PCT=30   |   Bo'lak: RANGE=a,b
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 982
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper so'z vaqtlari) ----------------
SHOTS = [(1, "hook"), (39, "box"), (86, "label"), (172, "xhead"), (253, "jaw"), (309, "convey"), (381, "insert"),
         (441, "little"), (498, "push"), (534, "musket"), (582, "pack"), (678, "harden"), (753, "block"),
         (803, "shower"), (843, "swell"), (900, "deaf")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
def T(sec): return int(round(sec * 24)) + 1           # ovoz vaqti -> kadr

ROOM_SHOTS = rng("hook", "box", "label", "insert", "shower", "deaf")
BATH_SHOTS = rng("shower", "deaf")
X_SHOTS = rng("xhead", "jaw")
STUD_SHOTS = rng("convey", "little", "push", "pack", "harden", "block", "swell")

# ---------------- yordamchilar (quloq.py / aksirish.py dan) ----------------
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

# --- primitivlar: (0,0,0) da yasab, keyin joylashtiramiz (transform_apply tuzog'idan qochish) ---
def _fin(o, name, loc, rot, m, parent):
    o.name = name; o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if m: o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    sx, sy = size[0] / 2, size[1] / 2
    me = bpy.data.meshes.new(name); me.from_pydata([(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)], [], [(0, 1, 2, 3)]); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return _fin(o, name, loc, rot, m, parent)
def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(); o = bpy.context.object
    for v in o.data.vertices: v.co = Vector((v.co.x * size[0] / 2, v.co.y * size[1] / 2, v.co.z * size[2] / 2))
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL"); bv.width = bevel; bv.segments = 3
    return _fin(o, name, loc, rot, m, parent)
def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth); o = bpy.context.object
    for p in o.data.polygons: p.use_smooth = len(p.vertices) == 4
    return _fin(o, name, loc, rot, m, parent)
def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None, world=True):
    if sub >= 4: bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r)
    else: bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r)
    o = bpy.context.object; o.scale = scale
    for p in o.data.polygons: p.use_smooth = True
    return _fin(o, name, loc, (0, 0, 0), m, parent)
FONT = bpy.data.fonts.load("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf")
def text(name, body, size, loc, rot, m, parent=None, align="CENTER", extrude=0.0):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.font = FONT; cu.size = size
    cu.align_x = align; cu.align_y = "CENTER"; cu.extrude = extrude
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o)
    return _fin(o, name, loc, rot, m, parent)
def frame_q(fwd, up):
    y = Vector(fwd).normalized(); z = Vector(up); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_quaternion()
def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def tile_mat(name, c1, c2, grout=(0.5, 0.5, 0.5), scale=3.3, rough=0.08):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.5
    br.inputs["Color1"].default_value = (*c1, 1); br.inputs["Color2"].default_value = (*c2, 1); br.inputs["Mortar"].default_value = (*grout, 1)
    br.inputs["Scale"].default_value = scale; br.inputs["Mortar Size"].default_value = 0.012
    L.new(tc.outputs["Object"], br.inputs["Vector"]); L.new(br.outputs["Color"], b.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange"); L.new(br.outputs["Fac"], mr.inputs["Value"]); mr.inputs["To Min"].default_value = rough
    mr.inputs["To Max"].default_value = 0.8; L.new(mr.outputs[0], b.inputs["Roughness"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.004
    L.new(P.math_n(N, L, "SUBTRACT", 1.0, br.outputs["Fac"]), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

# ======================================================================
# 1) HAMMOM (0,0,0): oyna + lavabo -Y devorda, dush +X/+Y burchakda
# ======================================================================
room = empty("room", (0, 0, 0))
X0_, X1_, Y0_, Y1_, H_ = -2.0, 2.7, -1.25, 1.65, 2.6
white_t = tile_mat("tile_white", (0.92, 0.93, 0.92), (0.86, 0.88, 0.88))
teal_t = tile_mat("tile_teal", (0.03, 0.30, 0.33), (0.02, 0.22, 0.27), grout=(0.75, 0.78, 0.78))
floor_m = pbr("floor", "interior_tiles", 0.8)
plane("floor", (X1_ - X0_, Y1_ - Y0_), ((X0_ + X1_) / 2, (Y0_ + Y1_) / 2, 0), floor_m, parent=room)
plane("ceiling", (X1_ - X0_, Y1_ - Y0_), ((X0_ + X1_) / 2, (Y0_ + Y1_) / 2, H_), mat("ceil", (0.9, 0.9, 0.9), 0.8), rot=(180, 0, 0), parent=room)
plane("wall_mirror", (X1_ - X0_, H_), ((X0_ + X1_) / 2, Y0_, H_ / 2), white_t, rot=(-90, 0, 0), parent=room)
plane("wall_back", (X1_ - X0_, H_), ((X0_ + X1_) / 2, Y1_, H_ / 2), teal_t, rot=(90, 0, 0), parent=room)
plane("wall_left", (Y1_ - Y0_, H_), (X0_, (Y0_ + Y1_) / 2, H_ / 2), white_t, rot=(90, 0, 90), parent=room)
plane("wall_right", (Y1_ - Y0_, H_), (X1_, (Y0_ + Y1_) / 2, H_ / 2), teal_t, rot=(90, 0, -90), parent=room)
# lavabo stoli
cab_m = mat("cabinet", (0.82, 0.78, 0.7), 0.4, coat=0.3); stone_m = mat("stone", (0.06, 0.065, 0.07), 0.12, coat=0.6)
cer_m = mat("ceramic", (0.95, 0.95, 0.94), 0.06, coat=1.0); chrome_m = mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0)
box("cabinet", (2.0, 0.48, 0.84), (-0.2, -1.0, 0.42), cab_m, parent=room)
box("counter", (2.06, 0.54, 0.04), (-0.2, -0.99, 0.86), stone_m, parent=room, bevel=0.006)
CT = 0.88                                                  # stol usti
cyl("basin", 0.2, 0.11, (0.3, -1.0, CT + 0.055), cer_m, parent=room, verts=48)
cyl("basin_in", 0.18, 0.004, (0.3, -1.0, CT + 0.111), mat("basin_in", (0.75, 0.8, 0.82), 0.05, coat=1.0), parent=room, verts=48)
cyl("faucet", 0.014, 0.26, (0.3, -1.19, CT + 0.13), chrome_m, parent=room)
cyl("faucet_arm", 0.012, 0.14, (0.3, -1.13, CT + 0.25), chrome_m, rot=(90, 0, 0), parent=room)
# oyna + chiroq
mir_m = mat("mirror", (0.95, 0.96, 0.97), 0.02, metal=1.0)
plane("mirror", (1.3, 0.95), (-0.1, Y0_ + 0.012, 1.58), mir_m, rot=(-90, 0, 0), parent=room)
box("mirror_frame", (1.36, 0.02, 1.01), (-0.1, Y0_ + 0.006, 1.58), mat("mframe", (0.03, 0.03, 0.03), 0.3), parent=room)
box("mirror_lamp", (1.1, 0.05, 0.05), (-0.1, Y0_ + 0.06, 2.16), mat("mlamp", (1, 0.95, 0.85), 0.5, emit=6.0), parent=room)
# sochiq, o'simlik, javon
towel_m = mat("towel", (0.85, 0.5, 0.12), 0.95, sss=0.1)
box("towel", (0.03, 0.42, 0.7), (X0_ + 0.05, 0.3, 1.2), towel_m, parent=room, bevel=0.012)
cyl("towel_bar", 0.012, 0.6, (X0_ + 0.07, 0.3, 1.56), chrome_m, rot=(90, 0, 0), parent=room)
plantR = empty("plantR", (-1.55, 1.15, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR)
plantR.scale = (1.3, 1.3, 1.3)
rug_m = mat("rug", (0.75, 0.75, 0.72), 0.95)
box("rug", (1.1, 0.6, 0.015), (0.0, -0.3, 0.008), rug_m, parent=room, bevel=0.005)
# dush: taglik, oyna to'siq, quvur, kallak
SHW = Vector((1.9, 0.85, 0.0))
box("tray", (1.6, 1.6, 0.06), (1.9, 0.85, 0.03), cer_m, parent=room, bevel=0.01)
glass_m = mat("glass", (0.9, 0.97, 0.96), 0.0, trans=1.0, ior=1.45)
box("glass", (0.012, 1.6, 2.0), (1.09, 0.85, 1.06), glass_m, parent=room)
cyl("sh_pipe", 0.014, 1.2, (1.9, Y1_ - 0.04, 1.65), chrome_m, parent=room)
cyl("sh_arm", 0.012, 0.36, (1.9, Y1_ - 0.2, 2.24), chrome_m, rot=(90, 0, 0), parent=room)
SH_HEAD = Vector((1.9, 1.28, 2.2))
cyl("sh_head", 0.12, 0.025, tuple(SH_HEAD), chrome_m, rot=(-18, 0, 0), parent=room, verts=48)
box("shelf", (0.5, 0.12, 0.02), (2.4, Y1_ - 0.07, 1.25), stone_m, parent=room)
for i, c_ in enumerate(((0.9, 0.3, 0.1), (0.15, 0.4, 0.8), (0.95, 0.95, 0.95))):
    cyl(f"bottle{i}", 0.032, 0.17, (2.26 + i * 0.12, Y1_ - 0.07, 1.345), mat(f"bottle{i}", c_, 0.25, coat=0.6), parent=room)

# ---- paxtali cho'plar qutisi (old tomoni mahalliy -Y, orqasi +Y) ----
BOXP = Vector((-0.48, -0.9, CT + 0.058))
BW, BD, BH = 0.078, 0.036, 0.112
pack = empty("pack", tuple(BOXP)); pack.rotation_euler = (0, 0, R(180))
blue_m = mat("pk_blue", (0.008, 0.07, 0.42), 0.35, coat=0.4); white_m = mat("pk_white", (0.96, 0.96, 0.95), 0.5)
ink_m = mat("pk_ink", (0.03, 0.03, 0.04), 0.5); grey_m = mat("pk_grey", (0.45, 0.45, 0.47), 0.5)
yel_m = mat("pk_yellow", (1.0, 0.8, 0.05), 0.4)
warn_m = mat("pk_red", (0.85, 0.02, 0.02), 0.4, emit=0.01)
for m_ in (blue_m, white_m, ink_m, grey_m, yel_m, warn_m):
    m_.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.12; m_.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.75; m_.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.0
box("pk_body", (BW, BD, BH), (0, 0, 0), blue_m, parent=pack, bevel=0.0015)
EPS = 0.0005
plane("pk_back", (BW - 0.008, BH - 0.008), (0, BD / 2 + EPS, 0), white_m, rot=(-90, 0, 0), parent=pack)
plane("pk_win", (0.05, 0.03), (0, -BD / 2 - EPS, -0.025), white_m, rot=(90, 0, 0), parent=pack)
text("pk_t1", "PAXTALI", 0.0125, (0, -BD / 2 - 2 * EPS, 0.034), (90, 0, 0), white_m, pack)
text("pk_t2", "CHO'PLAR", 0.0125, (0, -BD / 2 - 2 * EPS, 0.018), (90, 0, 0), yel_m, pack)
text("pk_t3", "200 dona", 0.007, (0, -BD / 2 - 3 * EPS, -0.025), (90, 0, 0), blue_m, pack)
text("pk_t4", "100% paxta", 0.0055, (0, -BD / 2 - 2 * EPS, -0.046), (90, 0, 0), white_m, pack)
# orqa tomoni: mayda matn qatorlari, ogohlantirish, shtrix-kod
BY = BD / 2 + 2 * EPS
def bk(name, body, size, x, z, m, align="CENTER"):
    return text(name, body, size, (x, BY, z), (90, 0, 180), m, pack, align=align)
bk("bk_h", "FOYDALANISH QOIDALARI", 0.0042, 0, 0.045, ink_m)
rl = random.Random(3)
for i in range(4):
    w_ = rl.uniform(0.045, 0.062); plane(f"bk_l{i}", (w_, 0.0012), ((0.062 - w_) / 2, BY, 0.038 - i * 0.0036), grey_m, rot=(-90, 0, 0), parent=pack)
warnR = empty("warnR", (0, BY, 0.004), pack)
for nm_, sz, lc in (("t", (0.068, 0.0016), (0, 0, 0.0185)), ("b", (0.068, 0.0016), (0, 0, -0.0185)), ("l", (0.0016, 0.037), (0.0332, 0, 0)), ("r", (0.0016, 0.037), (-0.0332, 0, 0))):
    plane("warn_" + nm_, sz, lc, warn_m, rot=(-90, 0, 0), parent=warnR)
text("warn_t1", "DIQQAT!", 0.0078, (0, EPS, 0.0105), (90, 0, 180), warn_m, warnR)
text("warn_t2", "Quloq ichiga", 0.0068, (0, EPS, 0.0005), (90, 0, 180), ink_m, warnR)
text("warn_t3", "tiqilmasin!", 0.0068, (0, EPS, -0.0085), (90, 0, 180), ink_m, warnR)
for i in range(3):
    w_ = rl.uniform(0.04, 0.06); plane(f"bk_m{i}", (w_, 0.0012), ((0.062 - w_) / 2, BY, -0.021 - i * 0.0036), grey_m, rot=(-90, 0, 0), parent=pack)
for i in range(22):
    plane(f"bar{i}", (rl.choice((0.0005, 0.0009, 0.0014)), 0.011), (0.03 - i * 0.0014, BY, -0.042), ink_m, rot=(-90, 0, 0), parent=pack)

# ======================================================================
# 2) BRIAN (yigit)
# ======================================================================
broot, bri, bmeshes = mc.load_character("bri", "Brian.fbx"); sc.render.fps = 24
soften(bmeshes)
headE = child_of_bone("bri_head", bri, "Head")
# o'ng quloq (Head fazosi: X chap, Y tepa, Z old) — o'lchangan: chig'anoq tubi (-0.059, 0.053, 0.022)
EAR = Vector((-0.06, 0.053, 0.021))
earE = empty("earE", tuple(EAR), headE)
faceT = empty("faceT", (0, 0.06, 0.06), headE)
COLLAR_Z = float(os.environ.get("COLLAR_Z", 1.41))
MIRROR_ROOT = (0.0, -0.42, 0.0); SHOWER_ROOT = (1.9, 0.8, 0.06)
place(broot, 1, MIRROR_ROOT, rot=0); place(broot, S["shower"][0], SHOWER_ROOT, rot=0)
interp(broot, "CONSTANT")
BI = A_("Breathing_Idle.fbx")
mc.add_strip(bri, BI, -20, blend=0, repeat=(END + 40) / 239.0)
DF0, DF1 = S["deaf"]
strip(bri, A_("Head_Gesture.fbx"), DF0 + 8, blend=5, bout=0, speed=1.3)
sc.frame_set(20); bpy.context.view_layer.update()

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
# quloq teshigi (qorong'i chuqurlik)
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
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.0062, fill_type="TRIFAN")
hole = bpy.context.object; hole.name = "ear_hole"; hole.data.materials.append(hole_m)
hole.parent = headE; hole.rotation_mode = "QUATERNION"
hole.location = HOLE_P + HOLE_N * 0.0006
hole.rotation_quaternion = frame_q(Vector((0, 1, 0)), HOLE_N)
hole.scale = (1.0, 0.8, 1.0)

# ---- tayoqcha (real o'lcham) + o'ng qo'l IK ----
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
def arm_ik(arm, side, name, pole=None, pole_ang=-90):
    tgt = empty(f"{name}_{side}_ik")
    c = arm.pose.bones[f"mixamorig:{side}ForeArm"].constraints.new("IK")
    c.target = tgt; c.use_tail = True; c.chain_count = 2; c.influence = 0.0
    if pole is not None: c.pole_target = pole; c.pole_angle = R(pole_ang)
    return tgt, c
def key_inf(cs, pairs):
    for c in cs:
        for f, v in pairs: c.influence = v; c.keyframe_insert("influence", frame=f)

CANAL_X = [HOLE_P + Vector((-0.002, 0, 0)), HOLE_P + Vector((0.008, -0.001, 0.003)), HOLE_P + Vector((0.017, -0.003, 0.006)),
           HOLE_P + Vector((0.025, -0.004, 0.008))]
CANAL_DIR = (CANAL_X[-1] - CANAL_X[0]).normalized()           # Head fazosida, ichkariga
HK0, HK1 = S["hook"]; BX0, BX1 = S["box"]; LB0, LB1 = S["label"]; XH0, XH1 = S["xhead"]; JW0, JW1 = S["jaw"]
CV0, CV1 = S["convey"]; IN0, IN1 = S["insert"]; LI0, LI1 = S["little"]; PU0, PU1 = S["push"]; MU0, MU1 = S["musket"]
PK0, PK1 = S["pack"]; HD0, HD1 = S["harden"]; BL0, BL1 = S["block"]; SH0, SH1 = S["shower"]; SW0, SW1 = S["swell"]
SWAB_RANGES = [(1, LB1), (IN0, IN1)]
swR = empty("swab_head", (0, 0, 0), headE); swR.rotation_mode = "QUATERNION"
swR.rotation_quaternion = Vector((0, 0, 1)).rotation_difference((-CANAL_DIR + Vector((0, -0.3, 0.3))).normalized())
swabB = make_swab("swabB", 1.0, swR)
for f, d in ((1, -0.045), (22, -0.004), (30, 0.005), (LB1, 0.005), (IN0, -0.03), (IN0 + 16, 0.004), (IN0 + 25, -0.002), (IN0 + 34, 0.007),
             (IN0 + 44, 0.0), (IN1, 0.007)):
    key(swR, f, loc=tuple(HOLE_P + CANAL_DIR * d))
vis(swabB, SWAB_RANGES)
gripB = empty("swab_grip", (0, 0, 0.064), swabB)
tipB = empty("swab_tipaim", (0, 0, -0.05), swabB)
poleB = empty("bri_poleR", (-0.35, -0.45, -0.1), headE)
RT_, RIK = arm_ik(bri, "Right", "bri", pole=poleB, pole_ang=-90)
for a_, b_ in SWAB_RANGES:
    for f in range(a_ - 2, b_ + 3, 2):
        g_ = wpos(gripB, f); sh_ = bri.matrix_world @ bri.pose.bones["mixamorig:RightShoulder"].head
        key(RT_, f, loc=tuple(g_ + (sh_ - g_).normalized() * 0.07))
hbR = bri.pose.bones["mixamorig:RightHand"]
dtr = hbR.constraints.new("DAMPED_TRACK"); dtr.target = tipB; dtr.track_axis = "TRACK_Y"
key_inf([RIK, dtr], [(1, 1.0), (LB1, 1.0), (LB1 + 1, 0.0), (IN0 - 1, 0.0), (IN0, 1.0), (IN1, 1.0), (IN1 + 1, 0.0)])
interp(bri, "CONSTANT", "pose.bones")

# stakandagi cho'plar
cup_m = mat("cup", (0.9, 0.9, 0.88), 0.15, coat=0.8)
cyl("cup", 0.036, 0.09, (-0.68, -1.02, CT + 0.045), cup_m, parent=room)
rc = random.Random(4)
for i in range(9):
    s_ = make_swab(f"cupswab{i}", 1.0, room)
    s_.location = (-0.68 + rc.uniform(-0.02, 0.02), -1.02 + rc.uniform(-0.02, 0.02), CT + 0.03)
    s_.rotation_euler = (R(rc.uniform(-14, 14)), R(rc.uniform(-14, 14)), 0)
# quti: stoldan sakrab, havoda 180° aylanadi (orqa tomoni kameraga)
for f, z, rz in ((1, 0, 180), (BX0 + 4, 0, 180), (BX0 + 16, 0.17, 250), (BX0 + 30, 0.22, 352), (BX1, 0.225, 366), (LB0, 0.225, 364),
                 (LB1, 0.235, 356)):
    key(pack, f, loc=tuple(BOXP + Vector((0, 0, z))), rot=(4 * math.sin(f * 0.2) if z else 0, 0, rz))
for f, e in ((1, 0.01), (LB0 + 22, 0.01), (LB0 + 28, 3.0), (LB0 + 40, 0.6), (LB0 + 52, 3.0), (LB0 + 64, 0.8), (LB1, 2.0)):
    b_ = warn_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]; b_.default_value = e; b_.keyframe_insert("default_value", frame=f)
for f, s_ in ((1, 1.0), (LB0 + 22, 1.0), (LB0 + 27, 1.22), (LB0 + 34, 1.05), (LB1, 1.1)):
    key(warnR, f, scale=(s_, 1, s_))

# ======================================================================
# 3) RENTGEN BOSH: shaffof Brian + quloq yo'li, parda, chig'anoq, miya, jag' suyagi
# ======================================================================
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.1, base=0.01)
ghosts = []
for o in bmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
# dushda futbolka o'rniga teri (alohida nusxa)
shirt = next(m for m in bmeshes if m.name.endswith("Shirt"))
skin_m = mat("wet_skin", (0.74, 0.55, 0.45), 0.3, sss=0.3, sss_scale=0.01, coat=0.5)
shirt2 = shirt.copy(); shirt2.name = "bri_Shirt_skin"; sc.collection.objects.link(shirt2)
shirt2.data = shirt.data.copy()                      # yoqani olib tashlaymiz (yalang'och yelka ko'rinishi)
import bmesh
bm_ = bmesh.new(); bm_.from_mesh(shirt2.data); mw_ = shirt.matrix_world
bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if (mw_ @ v.co).z > COLLAR_Z], context="VERTS"); bm_.to_mesh(shirt2.data); bm_.free()
for slot in shirt2.material_slots: slot.link = "OBJECT"; slot.material = skin_m
for g in ghosts: vis(g, X_SHOTS, recursive=False)
real_ranges = [(1, XH0 - 1), (JW1 + 1, END)]
for o in bmeshes: vis(o, real_ranges, recursive=False)
vis(shirt, [(1, XH0 - 1), (JW1 + 1, SH0 - 1)], recursive=False)
vis(shirt2, [(SH0, END)], recursive=False)
# yelka/ko'krak usti: silliq teri ellipsoidi (yoqa kesilgan joyni yopadi), bo'yin suyagiga ergashadi
neckE = child_of_bone("bri_neck", bri, "Neck")
chest = sphere("bare_chest", 1.0, (0, 0.012, -0.105), skin_m, scale=(0.2, 0.112, 0.1), sub=4)
cl_ = chest.constraints.new("COPY_LOCATION"); cl_.target = neckE; cl_.use_offset = True
vis(chest, [(SH0, END)], recursive=False)
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
canalX = P.tube("canal_x", catmull(CANAL_X, 0.002), 0.0042, canal_x_m, xh)
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
P.mat_value(brain_m, "glow", 1, 0.3)
# jag' suyagi (pastki jag'): bo'g'im quloq yo'li oldida; chaynaganda yo'l devorini qimirlatadi
JAWP = Vector((0.0, 0.047, 0.036))
jawP = empty("jawP", tuple(JAWP), xh)
bone_m = organ_mat("jaw_bone", (1.0, 0.82, 0.55), emit=0.5, alpha_mix=0.12)
def jaw_half(s): return [Vector((s * 0.054, 0.047, 0.034)), Vector((s * 0.055, 0.018, 0.026)), Vector((s * 0.052, -0.016, 0.024)),
                         Vector((s * 0.044, -0.03, 0.062)), Vector((s * 0.026, -0.038, 0.098))]
jpts = jaw_half(-1) + [Vector((0, -0.04, 0.11))] + jaw_half(1)[::-1]
P.tube("mandible", [p - JAWP for p in catmull(jpts, 0.004)], 0.0044, bone_m, jawP)
tpts = [Vector((-0.036, -0.02, 0.07)), Vector((-0.022, -0.024, 0.096)), Vector((0, -0.026, 0.106)), Vector((0.022, -0.024, 0.096)), Vector((0.036, -0.02, 0.07))]
P.tube("teeth_low", [p - JAWP for p in catmull(tpts, 0.003)], 0.0036, organ_mat("teeth", (1, 1, 1), emit=1.4, alpha_mix=0.05), jawP)
tup = empty("teeth_upR", (0, 0, 0), xh)
P.tube("teeth_up", [p + Vector((0, 0.0085, 0.002)) for p in catmull(tpts, 0.003)], 0.0036, organ_mat("teeth2", (1, 1, 1), emit=1.4, alpha_mix=0.05), tup)
CHEWS = list(range(XH0 + 30, JW1 + 2, 13))
key(jawP, 1, rot=(0, 0, 0))
for c_ in CHEWS:
    key(jawP, c_, rot=(0, 0, 0)); key(jawP, c_ + 5, rot=(13, 0, 0)); key(jawP, c_ + 11, rot=(0, 0, 0))
    P.tube_r(canalX, c_, 0.0042); P.tube_r(canalX, c_ + 5, 0.0034); P.tube_r(canalX, c_ + 11, 0.0042)
# rentgendagi oltingugurt bo'lakchalari: har chaynashda tashqariga siljiydi
waxx_m = mat("wax_x", (1.0, 0.6, 0.05), 0.3, emit=6.0)
CPATH = catmull([CANAL_X[3], CANAL_X[2], CANAL_X[1], CANAL_X[0], HOLE_P + HOLE_N * 0.006 + Vector((0, -0.004, 0)),
                 HOLE_P + HOLE_N * 0.01 + Vector((0, -0.03, 0))], 0.0005)
for i in range(7):
    w_ = sphere(f"waxx{i}", 0.0014, (0, 0, 0), waxx_m, sub=2, parent=xh)
    u0 = 0.05 + i * 0.09
    key(w_, 1, loc=tuple(CPATH[int(u0 * (len(CPATH) - 1))]))
    for k, c_ in enumerate(CHEWS):
        for f, u in ((c_, u0 + k * 0.1), (c_ + 9, u0 + (k + 1) * 0.1)):
            key(w_, f, loc=tuple(CPATH[min(len(CPATH) - 1, int(u * (len(CPATH) - 1)))]))
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


def tissue(name):
    bpy.ops.mesh.primitive_cube_add(); o = bpy.context.object; o.name = name
    for v in o.data.vertices: v.co = Vector((v.co.x * 0.75, v.co.y * 0.75, v.co.z * 0.8 + 0.2))
    o.location = C0; o.data.materials.append(sect_m)
    m1 = o.modifiers.new("canal", "BOOLEAN"); m1.object = canal_cut; m1.operation = "DIFFERENCE"; m1.solver = "EXACT"
    m1.material_mode = "TRANSFER"
    bpy.ops.mesh.primitive_cube_add(); h = bpy.context.object; h.name = name + "_half"
    for v in h.data.vertices: v.co = Vector((v.co.x * 1.5, v.co.y - 1.0, v.co.z * 1.5 + 0.2))
    h.location = C0; h.data.materials.append(sect_m); h.hide_render = True; h.display_type = "WIRE"
    m2 = o.modifiers.new("half", "BOOLEAN"); m2.object = h; m2.operation = "DIFFERENCE"; m2.solver = "EXACT"; m2.material_mode = "TRANSFER"
    return o, h
tis_cut, half_cut = tissue("tissue_cut")
# tukchalar (kirish qismida)
hair_m = mat("canal_hair", (0.08, 0.05, 0.035), 0.45, coat=0.3)
bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.0028, radius2=0.0003, depth=1.0, location=(0, 0, 0.5))
hair_mesh = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object); hair_mesh.materials.append(hair_m)
hairs = empty("hairs", (0, 0, 0)); rh = random.Random(11)
for i in range(240):
    z = rh.uniform(0.45, 0.98); a = rh.uniform(0.15, math.pi - 0.15)
    base = wall(z, a, 0.004); r_, xo = prof_at(z)
    inward = (Vector((C0.x + xo, C0.y, base.z)) - base).normalized()
    d_ = (inward * 0.8 + Vector((0, 0, rh.uniform(0.3, 0.9)))).normalized()
    o = bpy.data.objects.new(f"hair{i}", hair_mesh); sc.collection.objects.link(o); o.parent = hairs
    o.location = base; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d_)
    o.scale = (1, 1, rh.uniform(0.03, 0.08))

# ---- oltingugurt materiali: "hard" (qotish: to'q, g'adir-budur, yoriqlar), "wet" (shishgan, och) ----
def wax_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    hard = value_node(m, "hard", 0.0); wet = value_node(m, "wet", 0.0)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 14; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs[0])
    fresh = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], fresh.inputs[0])
    fresh.color_ramp.elements[0].color = (0.4, 0.16, 0.01, 1); fresh.color_ramp.elements[1].color = (0.8, 0.42, 0.04, 1)
    old = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], old.inputs[0])
    old.color_ramp.elements[0].color = (0.02, 0.009, 0.003, 1); old.color_ramp.elements[1].color = (0.13, 0.06, 0.02, 1)
    vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = 9; L.new(tc.outputs["Object"], vor.inputs["Vector"])
    crack = N.new("ShaderNodeMapRange"); L.new(vor.outputs["Distance"], crack.inputs["Value"]); crack.inputs["From Min"].default_value = 0.0
    crack.inputs["From Max"].default_value = 0.06                                   # 0 = yoriq chizig'i
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(hard, c1.inputs["Factor"]); L.new(fresh.outputs[0], c1.inputs[6]); L.new(old.outputs[0], c1.inputs[7])
    ck = N.new("ShaderNodeMix"); ck.data_type = "RGBA"; ck.blend_type = "MULTIPLY"
    L.new(P.math_n(N, L, "MULTIPLY", hard, P.math_n(N, L, "SUBTRACT", 1.0, crack.outputs[0])), ck.inputs["Factor"])
    L.new(c1.outputs[2], ck.inputs[6]); ck.inputs[7].default_value = (0.05, 0.02, 0.01, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", wet, 0.55), c2.inputs["Factor"])
    L.new(ck.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.62, 0.42, 0.16, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"])
    L.new(P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", hard, 0.5), 0.25), P.math_n(N, L, "MULTIPLY", wet, 0.4), clamp=True),
          b.inputs["Roughness"])
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, hard), 0.7), wet, clamp=True), b.inputs["Coat Weight"])
    b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Scale"].default_value = 0.015
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.15)
    bp = N.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = 0.012
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", hard, 0.9), 0.25), bp.inputs["Strength"])
    L.new(P.math_n(N, L, "ADD", nz.outputs["Fac"], P.math_n(N, L, "MULTIPLY", crack.outputs[0], hard)), bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    return m
wax_m = wax_mat("wax"); waxw_m = wax_mat("wax_wall")
# devordagi bo'lakchalar: "convey" kadrida tashqariga (tepaga) siljiydi
blobs = empty("wall_wax", (0, 0, 0)); rb = random.Random(5)
STEPS = list(range(CV0, CV1 + 1, 14))                 # har chaynashda bir qadam
def conv_dz(f):
    d = 0.0
    for s_ in STEPS:
        d += 0.085 * ease(min(1.0, max(0.0, (f - s_) / 9.0)))
    return d
for i in range(34):
    z0 = rb.uniform(-0.3, 0.75); a = rb.uniform(0.25, math.pi - 0.25)
    o = sphere(f"waxw{i}", rb.uniform(0.012, 0.03), (0, 0, 0), waxw_m, scale=(1.5, 1.5, 0.55), sub=2, parent=blobs)
    o.rotation_mode = "QUATERNION"
    def put(f, z):
        p_ = wall(z, a, -0.004); r_, xo = prof_at(z)
        o.location = p_; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference((Vector((C0.x + xo, C0.y, p_.z)) - p_).normalized())
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
    put(1, z0)
    for f in range(CV0, CV1 + 1, 2): put(f, z0 + conv_dz(f))
    put(CV1 + 1, z0 if z0 > -0.05 else z0 + 0.45)      # keyingi kadrlarda chuqurdagilar tiqin ostida qolmasin
    interp(o, "CONSTANT" if False else "LINEAR")
# yashil strelkalar (tashqariga yo'nalish)
arrow_m = mat("arrow", (0.02, 0.9, 0.12), 0.4, emit=1.6)
arrows = empty("arrows", (0, 0, 0))
for i in range(3):
    a_ = empty(f"arrow{i}", (0, 0, 0), arrows)
    cyl(f"arrow{i}_s", 0.012, 0.13, (0, 0, 0), arrow_m, parent=a_, verts=12)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.036, radius2=0.0, depth=0.075); c_ = bpy.context.object
    c_.location = (0, 0, 0.1); c_.data.materials.append(arrow_m); c_.parent = a_
    for f in range(CV0, CV1 + 1, 2):
        z = -0.12 + i * 0.36 + conv_dz(f) * 1.6; r_, xo = prof_at(z)
        key(a_, f, loc=tuple(C0 + Vector((xo + (0.5 - i % 2) * 0.1, 0.03, z))))
vis(arrows, rng("convey"))

# ---- asosiy massa -> tiqin: shape key "blob" (boshlang'ich, devorda), Basis = pardaga zichlangan, "swell" = shishgan ----
TILT = 0.6
def plug_co(u, a, mode):
    if mode == "blob":
        cz = 0.32; r_, xo = prof_at(cz); cx = xo - 0.052
        s = math.sin(math.pi * u); w = 1 + 0.08 * math.sin(3 * a + u * 9)
        return Vector((cx + 0.09 * s * w * math.cos(a), 0.012 + 0.098 * s * w * math.sin(a), cz - 0.125 * math.cos(math.pi * u)))
    top = 0.02 if mode == "swell" else -0.10
    zc = -0.41 + (top + 0.41) * u
    r_, xo = prof_at(zc)
    cap = (1 - (2 * u - 1) ** 6) ** 0.5
    r = r_ * (1.0 if mode == "swell" else 0.93) * cap * (1 + 0.035 * math.sin(3 * a + u * 7))
    if mode != "swell": r *= 1 - 0.36 * max(0.0, math.cos(a)) ** 2
    x = xo + r * math.cos(a); y = r * math.sin(a)
    return Vector((x, y, zc + TILT * (x + 0.02) * (1 - u) ** 2 + 0.02))
NZ_, SEG_ = 28, 44
def plug_verts(mode):
    vs = [plug_co(0.0, 0.0, mode)]
    for i in range(1, NZ_):
        for j in range(SEG_): vs.append(plug_co(i / NZ_, 2 * math.pi * j / SEG_, mode))
    vs.append(plug_co(1.0, 0.0, mode)); return vs
pv = plug_verts("pack"); pf = []
for j in range(SEG_): pf.append((0, 1 + (j + 1) % SEG_, 1 + j))
for i in range(NZ_ - 2):
    for j in range(SEG_):
        a_, b_ = 1 + i * SEG_ + j, 1 + i * SEG_ + (j + 1) % SEG_; pf.append((a_, b_, b_ + SEG_, a_ + SEG_))
last = len(pv) - 1
for j in range(SEG_): pf.append((last, 1 + (NZ_ - 2) * SEG_ + j, 1 + (NZ_ - 2) * SEG_ + (j + 1) % SEG_))
pme = bpy.data.meshes.new("plug"); pme.from_pydata([tuple(v) for v in pv], [], pf); pme.update()
for p_ in pme.polygons: p_.use_smooth = True
plug = bpy.data.objects.new("plug", pme); sc.collection.objects.link(plug); plug.location = C0; pme.materials.append(wax_m)
plug.shape_key_add(name="Basis", from_mix=False)
for nm_ in ("blob", "swell"):
    kb = plug.shape_key_add(name=nm_, from_mix=False); kb.value = 0.0
    for i, v in enumerate(plug_verts(nm_)): kb.data[i].co = v
ptex = bpy.data.textures.new("plug_lump", "CLOUDS"); ptex.noise_scale = 0.09
pd = plug.modifiers.new("lump", "DISPLACE"); pd.texture = ptex; pd.strength = 0.03; pd.texture_coords = "LOCAL"
KB = plug.data.shape_keys.key_blocks
def blob_key(f, v): KB["blob"].value = v; KB["blob"].keyframe_insert("value", frame=f)
def ztop(v): return -0.10 + 0.545 * v
vis(plug, STUD_SHOTS, recursive=False)

# ---- studiya tayoqchasi (40x) ----
swabC = make_swab("swabC", 40.0); swabC.rotation_euler = (R(-2), R(2), 0)
smear = sphere("smear", 0.05, (0.055, -0.07, -0.02), waxw_m, scale=(1.0, 0.8, 1.3), sub=3, parent=swabC)
smd = smear.modifiers.new("lump", "DISPLACE"); smd.texture = ptex; smd.strength = 0.02
def swab_key(f, z, v=1.0, dx=0.0):
    key(swabC, f, loc=tuple(C0 + Vector((0.04 * v + dx, -0.01, z))))
# 8 "ozgina qismini olasiz": kiradi, tegadi, buraladi, chiqadi (uchida ozgina)
blob_key(1, 1.0); blob_key(PU0 + 7, 1.0)
swab_key(LI0, 1.55); swab_key(LI0 + 15, ztop(1) + 0.075); swab_key(LI0 + 20, ztop(1) + 0.06, dx=0.02); swab_key(LI0 + 25, ztop(1) + 0.07, dx=-0.02)
swab_key(LI0 + 30, ztop(1) + 0.06); swab_key(LI1 - 6, 1.05); swab_key(LI1, 1.2)
# 9 "qolgan 80%": qayta kirib, massani ichkariga itaradi
V_PUSH = 0.6
swab_key(PU0, 1.25); swab_key(PU0 + 7, ztop(1) + 0.06)
for f in range(PU0 + 7, PU0 + 23, 2):
    v = 1 - (1 - V_PUSH) * ease((f - PU0 - 7) / 15.0); blob_key(f, v); swab_key(f, ztop(v) + 0.06, v)
blob_key(PU0 + 22, V_PUSH); swab_key(PU0 + 22, ztop(V_PUSH) + 0.06, V_PUSH); swab_key(PK0, ztop(V_PUSH) + 0.06, V_PUSH)
# 11 "zichlab tiqib qo'yasiz": 4 zarba
HITS = [T(24.62), T(25.5), T(26.45), T(27.3)]; VH = [0.4, 0.22, 0.08, 0.0]; BULGE = [0.2, 0.4, 0.65, 1.0]
v_prev = V_PUSH
for h, v in zip(HITS, VH):
    blob_key(h - 3, v_prev); swab_key(h - 12, ztop(v_prev) + 0.06, v_prev); swab_key(h - 3, ztop(v_prev) + 0.27, v_prev)
    blob_key(h, v); swab_key(h, ztop(v) + 0.055, v); swab_key(h + 3, ztop(v) + 0.07, v)
    v_prev = v
swab_key(HITS[-1] + 6, ztop(0) + 0.07, 0); swab_key(PK1, 1.5, 0)
vis(swabC, rng("little", "push", "pack")); vis(smear, [(LI0 + 21, LI1)], recursive=False)
# parda bo'rtishi
kb_ = drum.data.shape_keys.key_blocks["bulge"]
bk_ = [(1, 0.0), (HITS[0] - 1, 0.0)]
for h, b_ in zip(HITS, BULGE): bk_ += [(h, b_ * 1.25), (h + 4, b_ * 0.8)]
bk_ += [(PK1, 0.7), (END, 0.7)]
for f, v in bk_: kb_.value = v; kb_.keyframe_insert("value", frame=f)
for h in HITS:
    for k, v in ((h - 1, 0.0), (h + 1, 1.0), (h + 14, 0.0)): val_key(drum_m, "ripa", k, v)
for k, v in ((1, 0.0), (HITS[-1] - 2, 0.0), (HITS[-1] + 1, 0.55), (PK1, 0.3), (HD1, 0.15), (END, 0.15)): val_key(drum_m, "red", k, v)
# "80%" yozuvi
txt_m = mat("txt80", (1.0, 0.85, 0.05), 0.4, emit=4.0)
t80 = text("t80", "80%", 0.2, tuple(C0 + Vector((0.37, -0.3, 0.08))), (90, 0, 0), txt_m, extrude=0.02)
for f, s_ in ((1, 0.001), (PU0 + 9, 0.001), (PU0 + 14, 1.25), (PU0 + 18, 1.0), (PU1, 1.06)): key(t80, f, scale=(s_,) * 3)
vis(t80, rng("push"), recursive=False)
# 12 qotish (timelapse)
for f, v in ((1, 0.0), (HD0, 0.0), (HD1 - 8, 1.0), (END, 1.0)): val_key(wax_m, "hard", f, v)
for f, v in ((1, 0.25), (END, 0.25)): val_key(waxw_m, "hard", f, v)
pd.strength = 0.03
# 13 tovush halqalari: tepadan tushadi (ko'k), tiqinga urilib qizarib qaytadi
def ring_mat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    a = value_node(m, "a", 0.0); L.new(P.math_n(N, L, "MULTIPLY", a, 14.0), em.inputs["Strength"])
    trn = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "SUBTRACT", 1.0, a, clamp=True), mx.inputs[0])
    L.new(em.outputs[0], mx.inputs[1]); L.new(trn.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs[0])
    return m
RING_F = [BL0 - 6 + i * 9 for i in range(6)]
BOUNCES = []
for i, f0 in enumerate(RING_F):
    for kind, col in (("dn", (0.15, 0.55, 1.0)), ("up", (1.0, 0.12, 0.05))):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05, major_segments=48, minor_segments=8)
        t_ = bpy.context.object; t_.name = f"ring_{kind}{i}"; m_ = ring_mat(f"ring_{kind}{i}", col); t_.data.materials.append(m_)
        fa, fb, za, zb = (f0, f0 + 15, 1.25, 0.0) if kind == "dn" else (f0 + 15, f0 + 27, 0.0, 0.5)
        for f in range(fa, fb + 1):
            z = za + (zb - za) * (f - fa) / (fb - fa); r_, xo = prof_at(z)
            key(t_, f, loc=tuple(C0 + Vector((xo, 0, z))), scale=(r_ * 0.8,) * 3)
        al = [(1, 0), (fa - 1, 0), (fa, 1.0), (fb, 1.0 if kind == "dn" else 0.0), (fb + 1, 0)]
        for f, a in al: val_key(m_, "a", f, a)
        vis(t_, rng("block"), recursive=False)
    BOUNCES.append(f0 + 15)
# 15 suv: yo'lga oqib kiradi (sath ko'tariladi), tiqin shishib yo'lni to'liq yopadi
water_m = mat("water", (0.45, 0.75, 1.0), 0.02, trans=0.95, ior=1.33)
water_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.3, 0.6, 1.0, 1)
water_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.12
waterC = lathe("water_canal", -0.2, 1.0, rscale=0.985, seed=2); waterC.data.materials.append(water_m)
bpy.ops.mesh.primitive_cube_add(); lvl = bpy.context.object; lvl.name = "water_level"
for v in lvl.data.vertices: v.co = Vector((v.co.x, v.co.y, v.co.z * 0.5))
lvl.hide_render = True; lvl.display_type = "WIRE"
bo = waterC.modifiers.new("lvl", "BOOLEAN"); bo.object = lvl; bo.operation = "INTERSECT"; bo.solver = "EXACT"
bp_ = waterC.modifiers.new("half", "BOOLEAN"); bp_.object = half_cut; bp_.operation = "DIFFERENCE"; bp_.solver = "EXACT"
for m_ in waterC.modifiers: m_.show_viewport = False
F_WAT = SW0 + 8
for f, top in ((1, -0.3), (F_WAT, -0.3), (F_WAT + 4, -0.02), (SW0 + 34, 0.72), (SW1, 0.8)): key(lvl, f, loc=tuple(C0 + Vector((0, 0, top - 0.5))))
vis(waterC, rng("swell"), recursive=False)
drop_m = mat("drop", (0.8, 0.92, 1.0), 0.03, trans=0.8, ior=1.33, emit=0.25, emit_col=(0.5, 0.75, 1.0))
for i in range(9):
    d_ = sphere(f"cdrop{i}", 0.035, (0, 0, 0), drop_m, scale=(0.8, 0.8, 1.8), sub=3)
    f0 = SW0 - 4 + i * 3; x_ = (i % 3 - 1) * 0.07
    key(d_, f0, loc=tuple(C0 + Vector((x_, -0.03, 2.2)))); key(d_, f0 + 9, loc=tuple(C0 + Vector((x_ * 0.6, -0.03, -0.1 + i * 0.07))))
    interp(d_, "LINEAR"); vis(d_, [(max(SW0, f0), f0 + 9)], recursive=False)
F_SWELL = T(36.6)
for f, v in ((1, 0.0), (F_SWELL - 16, 0.0), (F_SWELL + 6, 1.0), (END, 1.0)): KB["swell"].value = v; KB["swell"].keyframe_insert("value", frame=f)
for f, v in ((1, 0.0), (F_WAT + 4, 0.0), (F_SWELL + 6, 1.0), (END, 1.0)): val_key(wax_m, "wet", f, v)

# ======================================================================
# 5) TO'PPONCHA STVOLI KESIMI (o'xshatish): shompol o'qni porox ustiga zichlaydi — (120,0,0)
# ======================================================================
C1 = Vector((120.0, 0.0, 0.0))
gun = empty("gun", tuple(C1))
steel_m = mat("gun_steel", (0.12, 0.12, 0.14), 0.3, metal=1.0); brass_m = mat("brass", (0.85, 0.6, 0.2), 0.25, metal=1.0)
wood_m = mat("gun_wood", (0.22, 0.09, 0.035), 0.35, coat=0.6); lead_m = mat("lead", (0.45, 0.46, 0.5), 0.35, metal=0.9)
powder_m = mat("powder", (0.015, 0.015, 0.018), 0.9); bore_m = mat("bore", (0.07, 0.07, 0.08), 0.5, metal=0.9)
barrel = cyl("barrel", 0.17, 1.95, (0, 0, 0.275), steel_m, parent=gun, verts=64)
bore = cyl("bore_cut", 0.1, 1.9, (0, 0, 0.5), bore_m, parent=gun, verts=48); bore.hide_render = True; bore.display_type = "WIRE"
hb = box("gun_half", (2, 2, 4), (0, -1.0, 0), bore_m, parent=gun); hb.hide_render = True; hb.display_type = "WIRE"
for nm_, ob in (("bore", bore), ("half", hb)):
    m_ = barrel.modifiers.new(nm_, "BOOLEAN"); m_.object = ob; m_.operation = "DIFFERENCE"; m_.solver = "EXACT"; m_.material_mode = "TRANSFER"
    m_.show_viewport = False
barrel.data.materials.append(bore_m)
stock = box("stock", (0.36, 0.26, 1.7), (0, 0.2, 0.05), wood_m, parent=gun, bevel=0.05)
box("grip", (0.3, 0.24, 0.85), (-0.2, 0.2, -1.05), wood_m, rot=(0, -38, 0), parent=gun, bevel=0.08)
for z in (-0.35, 0.75):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.19, minor_radius=0.022); t_ = bpy.context.object; t_.location = (0, 0.06, z)
    t_.scale = (1.0, 1.25, 1.0); t_.data.materials.append(brass_m); t_.parent = gun
box("lock", (0.05, 0.2, 0.34), (0.2, 0.12, -0.5), brass_m, parent=gun, bevel=0.01)
box("hammer", (0.04, 0.07, 0.26), (0.24, 0.1, -0.3), steel_m, rot=(25, 0, 0), parent=gun, bevel=0.01)
powder = cyl("powder", 0.098, 0.2, (0, 0, -0.35), powder_m, parent=gun)
pt = bpy.data.textures.new("powder_n", "CLOUDS"); pt.noise_scale = 0.02
ball = sphere("ball", 0.094, (0, 0, 0.9), lead_m, sub=4, parent=gun)
rod = empty("rod", (0, 0, 0), gun)
cyl("rod_s", 0.03, 1.9, (0, 0, 1.0), wood_m, parent=rod, verts=16); cyl("rod_tip", 0.07, 0.07, (0, 0, 0.035), brass_m, parent=rod, verts=24)
BALL_Z = -0.25 + 0.094 + 0.0
GUN_HITS = [MU0 + 14, MU0 + 30, MU0 + 41]
for f, z in ((MU0 - 1, 0.95), (MU0 + 3, 0.9), (GUN_HITS[0], 0.15), (GUN_HITS[0] + 8, 0.15), (GUN_HITS[1], BALL_Z + 0.02), (GUN_HITS[2], BALL_Z), (MU1, BALL_Z)):
    key(ball, f, loc=(0, 0, z))
for f, z in ((MU0 - 1, 1.1), (MU0 + 3, 0.995), (GUN_HITS[0], 0.245), (GUN_HITS[0] + 8, 0.55), (GUN_HITS[1], BALL_Z + 0.115), (GUN_HITS[1] + 6, BALL_Z + 0.4),
             (GUN_HITS[2], BALL_Z + 0.095), (MU1, BALL_Z + 0.5)):
    key(rod, f, loc=(0, 0, z))
plane("gun_bg", (8, 6), tuple(C1 + Vector((0, 1.6, 0.3))), mat("gun_bg", (0.16, 0.07, 0.03), 0.9), rot=(90, 0, 0))

# ======================================================================
# 6) DUSH TOMCHILARI (har biri tsiklik tushadi)
# ======================================================================
rain = empty("rain", (0, 0, 0)); rr = random.Random(9)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0); dm = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
dm.materials.append(drop_m)
for p_ in dm.polygons: p_.use_smooth = True
for i in range(320):
    a = rr.uniform(0, 6.283); r_ = 0.11 * math.sqrt(rr.random())
    p0 = SH_HEAD + Vector((r_ * math.cos(a), r_ * math.sin(a) - 0.01, -0.03))
    p1 = p0 + Vector((math.cos(a) * r_ * 3.2, math.sin(a) * r_ * 3.2 - 0.62, -2.1))
    o = bpy.data.objects.new(f"rain{i}", dm); sc.collection.objects.link(o); o.parent = rain
    o.scale = (0.0035, 0.0035, 0.022); o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference((p0 - p1).normalized())
    f0 = SH0 - 20 + rr.uniform(0, 13)
    o.location = p0; o.keyframe_insert("location", frame=f0); o.location = p1; o.keyframe_insert("location", frame=f0 + 13)
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
vis(rain, BATH_SHOTS)

# ======================================================================
# 7) KAMERALAR (har kadrda harakat: push-in, aylanma, ergashish, crash zoom, silkinish)
# ======================================================================
def aim(c, tgt, focus=None):
    t = c.constraints.new("TRACK_TO"); t.target = tgt; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if c.data.dof.use_dof: c.data.dof.focus_object = focus or tgt
def path(c, keys, base=Vector((0, 0, 0)), lin=False):
    for f, p in keys: key(c, f, loc=tuple(Vector(base) + Vector(p)))
    if lin: interp(c, "LINEAR", "location")
def tgt_path(name, keys, base=Vector((0, 0, 0))):
    t = empty(name, (0, 0, 0)); path(t, keys, base); return t
def orbit_cam(name, f0, f1, center, r0, r1, a0, a1, z0, z1, lens, tgt, fstop=None):
    c = shot_cam(name, (0, 0, 0), tgt, lens, clip=0.002, fstop=fstop)
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / max(1, f1 - f0); a = R(a0 + (a1 - a0) * t); rr_ = r0 + (r1 - r0) * t
        key(c, f, loc=tuple(Vector(center) + Vector((rr_ * math.cos(a), rr_ * math.sin(a), z0 + (z1 - z0) * t))))
    interp(c, "LINEAR", "location"); return c
EW = wpos(earE, 12)
# 1 ilgak: o'ng quloq makro, crash zoom + silkinish
c = shot_cam("hook", (0, 0, 0), earE, 32, fstop=5.6, clip=0.005)
path(c, [(HK0, (-0.62, -0.34, 0.14)), (HK0 + 20, (-0.3, -0.16, 0.05)), (HK1, (-0.25, -0.13, 0.04))], EW)
lens_keys(c, [(HK0, 28), (HK0 + 20, 40), (HK1, 44)])
shake(c, HK0 + 22, HK0 + 32, 0.006, seed=1)
# 2 quti: havoda aylanadi, kamera qarshi tomonga aylanadi
c = shot_cam("box", (0, 0, 0), pack, 30, fstop=2.8, clip=0.005)
path(c, [(BX0, (0.3, 0.3, 0.02)), (BX0 + 20, (0.1, 0.34, 0.18)), (BX1, (-0.05, 0.3, 0.24))], BOXP)
lens_keys(c, [(BX0, 24), (BX1, 36)])
# 3 yozuv: makro push-in
c = shot_cam("label", (0, 0, 0), warnR, 50, fstop=5.6, clip=0.005)
path(c, [(LB0, (-0.08, 0.5, 0.27)), (LB0 + 24, (-0.02, 0.4, 0.238)), (LB1, (0.03, 0.31, 0.23))], BOXP)
shake(c, LB0 + 24, LB0 + 34, 0.004, seed=2)
# 4 rentgen bosh: tez aylanma
xt = empty("x_tgt", tuple(DRUM_X), headE)
EAR_X = wpos(xt, XH0 + 10)
orbit_cam("xhead", XH0, XH1, EAR_X, 0.55, 0.36, 205, 262, 0.14, 0.03, 35, xt)
# 5 jag': o'ng-old tomondan, past burchak
jt = empty("jaw_tgt", (-0.035, 0.012, 0.05), headE)
c = orbit_cam("jaw", JW0, JW1, EAR_X, 0.48, 0.4, 250, 222, -0.08, -0.03, 35, jt)
# 6 konveyer: kesim, tepaga ergashadi
t_ = tgt_path("cv_tgt", [(CV0, (0, 0, 0.05)), (CV1, (0, 0, 0.62))], C0)
c = shot_cam("convey", (0, 0, 0), t_, 26, fstop=5.6, clip=0.01)
path(c, [(CV0, (0.5, -1.75, -0.25)), (CV1, (0.15, -1.45, 0.8))], C0)
# 7 tiqish: past burchak, keng ob'ektiv, yuz
EW2 = wpos(earE, IN0 + 10)
c = shot_cam("insert", (0, 0, 0), faceT, 22, fstop=2.8, clip=0.01)
path(c, [(IN0, (-0.34, -0.52, -0.3)), (IN1, (-0.2, -0.4, -0.18))], EW2)
shake(c, IN0, IN1, 0.003, seed=3, decay=False)
# 8 ozgina: tayoqcha uchiga ergashadi, oxirida uchidagi bo'lakka yaqin
tipC = empty("tipC", (0.03, -0.05, 0.05), swabC)
c = shot_cam("little", (0, 0, 0), tipC, 28, fstop=5.6, clip=0.01)
path(c, [(LI0, (0.45, -2.0, 1.2)), (LI0 + 18, (0.3, -1.5, 0.65)), (LI0 + 32, (0.22, -1.2, 0.55)), (LI1, (0.2, -0.95, 1.1))], C0)
# 9 80%: itarish, silkinish
t_ = tgt_path("pu_tgt", [(PU0, (0.1, 0, 0.5)), (PU1, (0.15, 0, 0.2))], C0)
c = shot_cam("push", (0, 0, 0), t_, 24, fstop=5.6, clip=0.01)
path(c, [(PU0, (-0.45, -2.3, 0.75)), (PU1, (-0.15, -1.85, 0.3))], C0)
shake(c, PU0 + 8, PU0 + 22, 0.012, seed=4)
# 10 to'pponcha: past burchak, aylanma, zarbada silkinish
t_ = tgt_path("gun_tgt", [(MU0, (0, 0, 0.45)), (MU1, (0, 0, -0.1))], C1)
c = shot_cam("musket", (0, 0, 0), t_, 22, fstop=5.6, clip=0.01)
path(c, [(MU0, (1.1, -2.6, -0.7)), (MU1, (-0.5, -2.2, -0.4))], C1)
for h in GUN_HITS: shake(c, h, h + 7, 0.025, seed=h)
# 11 zichlash: keng -> har zarbada yaqinroq, oxirida pardaga crash zoom
t_ = tgt_path("pk_tgt", [(PK0, (0.03, 0, 0.15)), (HITS[2], (0.02, 0, -0.1)), (HITS[3] + 2, (0, 0.02, -0.3)), (PK1, (0, 0.02, -0.33))], C0)
c = shot_cam("pack", (0, 0, 0), t_, 24, fstop=5.6, clip=0.01)
path(c, [(PK0, (0.5, -2.5, 0.55)), (HITS[2], (0.3, -2.0, 0.0)), (HITS[3] - 3, (0.28, -1.9, -0.1)), (HITS[3] + 2, (0.3, -1.55, -0.3)), (PK1, (0.2, -1.4, -0.4))], C0)
lens_keys(c, [(PK0, 24), (HITS[3] - 3, 26), (HITS[3] + 2, 32)])
for i, h in enumerate(HITS): shake(c, h, h + 9, 0.012 + 0.008 * i, seed=h)
# 12 qotish: sekin aylanma
t_ = empty("hd_tgt", tuple(C0 + Vector((0, 0, -0.24))))
c = shot_cam("harden", (0, 0, 0), t_, 32, fstop=5.6, clip=0.01)
path(c, [(HD0, (-0.55, -1.25, 0.05)), (HD1, (0.5, -1.05, -0.3))], C0)
# 13 to'siq: halqalar bilan birga pastga
t_ = tgt_path("bl_tgt", [(BL0, (0, 0, 0.55)), (BL1, (0, 0, 0.0))], C0)
c = shot_cam("block", (0, 0, 0), t_, 24, fstop=5.6, clip=0.01)
path(c, [(BL0, (0.25, -2.3, 0.95)), (BL1, (-0.1, -1.75, 0.2))], C0)
for bf in BOUNCES:
    if BL0 <= bf <= BL1: shake(c, bf, bf + 5, 0.008, seed=bf)
# 14 dush: past burchak, keng
HW = wpos(headE, SH0 + 10)
c = shot_cam("shower", (0, 0, 0), empty("sh_ct", (0, 0.17, 0.03), headE), 32, fstop=2.8, clip=0.02)
path(c, [(SH0, (-0.36, -0.78, -0.2)), (SH1, (-0.2, -0.56, -0.14))], HW)
# 15 shishish: suv bilan birga, oxirida tirqish yopilishiga yaqin
t_ = tgt_path("sw_tgt", [(SW0, (0, 0, 0.45)), (F_SWELL - 10, (0.04, 0, -0.02)), (SW1, (0.05, 0, -0.08))], C0)
c = shot_cam("swell", (0, 0, 0), t_, 26, fstop=5.6, clip=0.01)
path(c, [(SW0, (-0.3, -2.2, 0.8)), (F_SWELL - 10, (0.2, -1.5, 0.15)), (SW1, (0.3, -1.05, 0.05))], C0)
shake(c, F_SWELL, F_SWELL + 10, 0.01, seed=6)
# 16 bitib qoldi: yuz/quloq, push-in, silkinish
HW2 = wpos(headE, DF0 + 30)
dft = empty("deaf_tgt", (-0.02, 0.1, 0.06), headE)
c = shot_cam("deaf", (0, 0, 0), dft, 35, fstop=2.4, clip=0.02)
path(c, [(DF0, (-0.4, -0.62, 0.12)), (DF0 + 30, (-0.33, -0.52, 0.11)), (DF1, (-0.26, -0.42, 0.1))], HW2)
lens_keys(c, [(DF0, 38), (DF0 + 14, 40), (DF0 + 20, 48), (DF1, 54)])
shake(c, DF0 + 14, DF0 + 28, 0.012, seed=7)

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 8) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.02, 0.03, 0.06, 1); bg.inputs["Strength"].default_value = 1.0
midT = empty("mid_tgt", (0.3, 0.0, 0.9))
area("ceil_l", (0.2, 0.0, 2.55), 1.6, (1.0, 0.95, 0.88), lights_for(ROOM_SHOTS, 260.0), target=midT)
area("mirror_l", (-0.1, Y0_ + 0.12, 2.12), 0.3, (1.0, 0.93, 0.82), lights_for(ROOM_SHOTS, 70.0), target=empty("ml_t", (0, -0.42, 1.5)), shape=(1.1, 0.12))
area("shower_l", (1.9, 0.5, 2.5), 1.0, (0.85, 0.95, 1.0), lights_for(ROOM_SHOTS, 80.0), target=empty("sh_t", (1.9, 0.8, 1.2)))
earL = empty("earL", tuple(HOLE_P + HOLE_N * 0.3 + Vector((0.0, 0.12, 0.12))), headE)
l_ = area("ear_key", (0, 0, 0), 0.25, (1.0, 0.9, 0.8), lights_for(rng("hook", "insert"), 3.0), target=earE); l_.parent = earL
area("face_key", tuple(HW + Vector((-0.7, -1.0, 0.3))), 0.7, (1.0, 0.92, 0.85), lights_for(BATH_SHOTS, 12.0), target=faceT)
area("box_key", tuple(BOXP + Vector((-0.6, 0.35, 0.7))), 0.4, (1.0, 0.96, 0.9), lights_for(rng("box", "label"), 3.0), target=pack)
area("x_dim", (0.2, 0, 2.5), 2.5, (0.3, 0.45, 0.9), lights_for(X_SHOTS, 45.0), target=midT)
# studiya
stT = empty("stud_tgt", tuple(C0 + Vector((0, 0.1, 0.0))))
area("st_key", tuple(C0 + Vector((-1.2, -2.0, 1.8))), 1.5, (1.0, 0.92, 0.85), lights_for(STUD_SHOTS, 350.0), target=stT)
area("st_rim", tuple(C0 + Vector((1.6, 0.5, 1.2))), 1.0, (0.85, 0.9, 1.0), lights_for(STUD_SHOTS, 160.0), target=stT)
area("st_in", tuple(C0 + Vector((0.0, -0.6, 0.6))), 0.4, (1.0, 0.8, 0.65), lights_for(STUD_SHOTS, 40.0), target=empty("dr_t", tuple(DRUM_C)))
point("st_cav", tuple(DRUM_C + Vector((0.05, -0.1, -0.2))), 0.05, (1.0, 0.45, 0.35), lights_for(STUD_SHOTS, 15.0))
# qotish: kun/tun almashinuvi (timelapse)
day = area("tl_day", tuple(C0 + Vector((-1.6, -1.6, 0.8))), 1.0, (1.0, 0.75, 0.4), [(1, 0)], target=stT)
night = area("tl_night", tuple(C0 + Vector((1.6, -1.6, 0.4))), 1.0, (0.3, 0.45, 1.0), [(1, 0)], target=stT)
for i, f in enumerate(range(HD0, HD1 + 1, 6)):
    for l_, e in ((day, 420.0 if i % 2 == 0 else 0.0), (night, 0.0 if i % 2 == 0 else 260.0)):
        l_.data.energy = e; l_.data.keyframe_insert("energy", frame=f)
for l_ in (day, night):
    l_.data.energy = 0; l_.data.keyframe_insert("energy", frame=HD0 - 1); l_.data.keyframe_insert("energy", frame=HD1 + 1); interp(l_.data, "LINEAR")
fl2 = point("pack_flash", tuple(DRUM_C + Vector((0, -0.25, 0.25))), 0.1, (1.0, 0.2, 0.08), [(1, 0)], const=False)
for h, e in zip(HITS, (120, 180, 260, 600)):
    for f, v in ((h - 1, 0), (h, e), (h + 5, e * 0.12), (h + 12, 0)): fl2.data.energy = v; fl2.data.keyframe_insert("energy", frame=f)
# to'pponcha
gT = empty("gun_lt", tuple(C1 + Vector((0, 0, 0.2))))
area("gun_key", tuple(C1 + Vector((-1.4, -2.2, 1.4))), 1.4, (1.0, 0.85, 0.65), lights_for(rng("musket"), 650.0), target=gT)
area("gun_rim", tuple(C1 + Vector((1.7, 0.2, 1.0))), 1.0, (0.6, 0.75, 1.0), lights_for(rng("musket"), 260.0), target=gT)
area("gun_in", tuple(C1 + Vector((0.0, -0.9, 0.3))), 0.5, (1.0, 0.8, 0.6), lights_for(rng("musket"), 40.0), target=gT)

# tovush effektlari uchun voqea kadrlari
if os.environ.get("EVENTS"):
    import json
    json.dump({"shots": SHOTS, "hits": HITS, "gun": GUN_HITS, "chews": CHEWS, "steps": STEPS, "bounces": BOUNCES, "push": PU0 + 7,
               "swell": F_SWELL, "water": F_WAT, "warn": LB0 + 27, "hook_in": 24, "end": END}, open(os.environ["EVENTS"], "w"))

# ======================================================================
# 9) RENDER
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
