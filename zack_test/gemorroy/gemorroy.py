# "Hojatxonada telefon bilan o'tirish — gemorroy" — Zack D. Films uslubida 42.6 s video (1024 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, paxta/paxta.py (yordamchilar, kamera, yorug'lik), burish/parts.py (quvur, impuls, rentgen).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_gemorroy.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 python3 -I zack_test/gemorroy/gemorroy.py --render
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
END = 1024
sc.frame_start, sc.frame_end = 1, END
def T(sec): return int(round(sec * 24)) + 1           # ovoz vaqti -> kadr

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper so'z vaqtlari) ----------------
SHOTS = [(1, "hook"), (T(1.6), "timer"), (T(3.55), "xray"), (T(7.2), "seat"), (T(9.8), "gravity"), (T(13.1), "sag"),
         (T(17.75), "legs"), (T(19.7), "backflow"), (T(21.6), "pool"), (T(24.5), "balloon"), (T(25.7), "swell"),
         (T(26.48), "thin"), (T(29.3), "bulge"), (T(31.05), "burst"), (T(33.1), "bowl"), (T(34.3), "normal"),
         (T(37.35), "infect"), (T(40.4), "surgery")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

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

def aim(c, tgt, focus=None):
    t = c.constraints.new("TRACK_TO"); t.target = tgt; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if c.data.dof.use_dof: c.data.dof.focus_object = focus or tgt
def path(c, keys, base=Vector((0, 0, 0)), lin=False):
    for f, p in keys: key(c, f, loc=tuple(Vector(base) + Vector(p)))
    if lin: interp(c, "LINEAR", "location")
def tgt_path(name, keys, base=Vector((0, 0, 0))):
    t = empty(name, (0, 0, 0)); path(t, keys, base); return t
def orbit_cam(name, f0, f1, center, r0, r1, a0, a1, z0, z1, lens, tgt, fstop=None):
    c = shot_cam(name, (0, 0, 0), tgt, lens, clip=0.01, fstop=fstop)
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / max(1, f1 - f0); a = R(a0 + (a1 - a0) * t); rr_ = r0 + (r1 - r0) * t
        key(c, f, loc=tuple(Vector(center) + Vector((rr_ * math.cos(a), rr_ * math.sin(a), z0 + (z1 - z0) * t))))
    interp(c, "LINEAR", "location"); return c
def glow_mat(name, col):
    """yumshoq nur: Transparent + Emission (Add); 'a' = kuch"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    a = value_node(m, "a", 0.0); lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    c_ = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"], clamp=True), 2.5)
    L.new(P.math_n(N, L, "MULTIPLY", a, c_), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
    return m
def emit_mat(name, col, s):
    return mat(name, col, 0.5, emit=s)
def smooth(o):
    for p in o.data.polygons: p.use_smooth = True
def mesh_obj(name, verts, faces, m=None, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc
    if m: me.materials.append(m)
    if parent: o.parent = parent
    return o
def rrect(w, h, zc=0.0, n=20, p=0.4):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n; c_, s_ = math.cos(t), math.sin(t)
        out.append((w / 2 * math.copysign(abs(c_) ** p, c_), zc + h / 2 * math.copysign(abs(s_) ** p, s_)))
    return out
def sweep(name, prof, ax, ay, m, a0=0.0, a1=math.pi, n=48, closed=True, parent=None, loc=(0, 0, 0)):
    """profil (r_off, z) ni ellips bo'ylab aylantirish; closed=True: yopiq profil (halqa), aks holda ochiq (kosa devori)"""
    vs = []; fs = []; k = len(prof)
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n; ca, sa = math.cos(a), math.sin(a)
        for ro, z in prof: vs.append(((ax + ro) * ca, (ay + ro) * sa, z))
    for i in range(n):
        for j in range(k if closed else k - 1):
            fs.append((i * k + j, i * k + (j + 1) % k, (i + 1) * k + (j + 1) % k, (i + 1) * k + j))
    if closed: fs.append(tuple(range(k))[::-1]); fs.append(tuple(range(n * k, n * k + k)))
    o = mesh_obj(name, vs, fs, m, parent, loc); smooth(o)
    if closed:
        o.data.polygons[-1].use_smooth = o.data.polygons[-2].use_smooth = False
    return o
def arrow(name, m, parent=None, s=1.0):
    e = empty(name, (0, 0, 0), parent)
    cyl(name + "_s", 0.014 * s, 0.13 * s, (0, 0, 0.115 * s), m, parent=e, verts=12)
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.04 * s, depth=0.08 * s); c_ = bpy.context.object
    c_.rotation_euler = (math.pi, 0, 0); c_.location = (0, 0, 0.04 * s); c_.data.materials.append(m); c_.parent = e
    return e
def cyc(o):
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
def skey(kb, pairs):
    for f, v in pairs: kb.value = v; kb.keyframe_insert("value", frame=f)

BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
XR0, XR1 = S["xray"]; TM0, TM1 = S["timer"]; ST0, ST1 = S["seat"]; GR0, GR1 = S["gravity"]; SG0, SG1 = S["sag"]
LG0, LG1 = S["legs"]; BF0, BF1 = S["backflow"]; PL0, PL1 = S["pool"]; BA0, BA1 = S["balloon"]; SW0, SW1 = S["swell"]
TH0, TH1 = S["thin"]; BG0, BG1 = S["bulge"]; BU0, BU1 = S["burst"]; BW0, BW1 = S["bowl"]; NM0, NM1 = S["normal"]
IF0, IF1 = S["infect"]; OP0, OP1 = S["surgery"]

# ======================================================================
# 1) HOJATXONA (0,0,0): unitaz +Y devorda, yigit -Y ga qarab o'tiradi
# ======================================================================
room = empty("room", (0, 0, 0))
X0_, X1_, Y0_, Y1_, H_ = -1.05, 1.35, -2.1, 0.68, 2.5
TY = 0.66                                                   # unitaz orqasi (model: orqa y=0, old y=-0.675, o'rindiq z=0.467)
white_t = tile_mat("tile_white", (0.9, 0.91, 0.9), (0.84, 0.86, 0.86))
teal_t = tile_mat("tile_teal", (0.03, 0.30, 0.33), (0.02, 0.22, 0.27), grout=(0.75, 0.78, 0.78))
floor_m = pbr("floor", "interior_tiles", 0.8)
plane("floor", (X1_ - X0_, Y1_ - Y0_), ((X0_ + X1_) / 2, (Y0_ + Y1_) / 2, 0), floor_m, parent=room)
plane("ceiling", (X1_ - X0_, Y1_ - Y0_), ((X0_ + X1_) / 2, (Y0_ + Y1_) / 2, H_), mat("ceil", (0.9, 0.9, 0.9), 0.8), rot=(180, 0, 0), parent=room)
plane("wall_door", (X1_ - X0_, H_), ((X0_ + X1_) / 2, Y0_, H_ / 2), white_t, rot=(-90, 0, 0), parent=room)
plane("wall_back", (X1_ - X0_, H_), ((X0_ + X1_) / 2, Y1_, H_ / 2), teal_t, rot=(90, 0, 0), parent=room)
plane("wall_left", (Y1_ - Y0_, H_), (X0_, (Y0_ + Y1_) / 2, H_ / 2), white_t, rot=(90, 0, 90), parent=room)
plane("wall_right", (Y1_ - Y0_, H_), (X1_, (Y0_ + Y1_) / 2, H_ / 2), white_t, rot=(90, 0, -90), parent=room)
toiletE = empty("toilet", (0, TY, 0), room); import_gltf(BK + "6a342733_u.glb", toiletE)
SEAT_Z = 0.467; HOLE = Vector((0, TY - 0.44, SEAT_Z))
cab_m = mat("cabinet", (0.82, 0.78, 0.7), 0.4, coat=0.3); stone_m = mat("stone", (0.06, 0.065, 0.07), 0.12, coat=0.6)
cer_m = mat("ceramic", (0.95, 0.95, 0.94), 0.06, coat=1.0); chrome_m = mat("chrome", (0.9, 0.9, 0.92), 0.08, metal=1.0)
box("cabinet", (0.44, 0.8, 0.8), (X1_ - 0.22, -0.95, 0.4), cab_m, parent=room)
box("counter", (0.5, 0.86, 0.04), (X1_ - 0.25, -0.95, 0.82), stone_m, parent=room, bevel=0.006)
cyl("basin", 0.17, 0.1, (X1_ - 0.25, -0.95, 0.89), cer_m, parent=room, verts=48)
cyl("faucet", 0.013, 0.24, (X1_ - 0.06, -0.95, 0.96), chrome_m, parent=room)
plane("mirror", (0.7, 0.9), (X1_ - 0.012, -0.95, 1.55), mat("mirror", (0.95, 0.96, 0.97), 0.02, metal=1.0), rot=(90, 0, -90), parent=room)
box("mirror_lamp", (0.05, 0.6, 0.05), (X1_ - 0.05, -0.95, 2.1), mat("mlamp", (1, 0.95, 0.85), 0.5, emit=6.0), parent=room)
box("door", (0.86, 0.04, 2.05), (0.1, Y0_ + 0.02, 1.025), mat("door", (0.42, 0.26, 0.14), 0.4, coat=0.3), parent=room)
paper_m = mat("paper", (0.96, 0.96, 0.94), 0.9, sss=0.1)
cyl("roll", 0.055, 0.1, (X0_ + 0.085, -0.05, 0.72), paper_m, rot=(90, 0, 0), parent=room)
cyl("roll_bar", 0.008, 0.14, (X0_ + 0.085, -0.05, 0.72), chrome_m, rot=(90, 0, 0), parent=room, verts=12)
box("roll_tail", (0.004, 0.1, 0.12), (X0_ + 0.14, -0.05, 0.665), paper_m, parent=room)
cyl("bin", 0.11, 0.3, (0.62, 0.48, 0.15), mat("bin", (0.1, 0.1, 0.11), 0.3, metal=0.6), parent=room)
plantR = empty("plantR", (-0.72, 0.38, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR)
plantR.scale = (1.15, 1.15, 1.15)
box("rug", (0.8, 0.55, 0.015), (0.0, -0.45, 0.008), mat("rug", (0.2, 0.42, 0.45), 0.95), parent=room, bevel=0.005)
plane("window", (0.62, 0.5), (0.0, Y1_ - 0.012, 1.85), mat("window", (0.8, 0.9, 1.0), 0.5, emit=4.0), rot=(90, 0, 0), parent=room)
box("window_fr", (0.7, 0.03, 0.58), (0.0, Y1_ - 0.005, 1.85), mat("wfr", (0.95, 0.95, 0.95), 0.3), parent=room)

# ======================================================================
# 2) BRIAN: unitazda (Sitting), ko'chada (Texting_And_Walking), operatsiya stolida (Laying_Idle)
# ======================================================================
broot, bri, bmeshes = mc.load_character("bri", "Brian.fbx"); sc.render.fps = 24
soften(bmeshes)
SIT = A_("Sitting.fbx", inplace=False); WALK = A_("Texting_And_Walking.fbx"); LAY = A_("Laying_Idle.fbx", inplace=False)
strip(bri, SIT, -6, src=(28, 62), speed=0.8 / (36 / 34.0), blend=0, bout=0)                 # ilgak: telefonga engashadi
strip(bri, SIT, 30, src=(62, 100), speed=0.8 / ((NM0 - 30) / 38.0), blend=0, bout=0)        # deyarli qimirlamay o'tiradi
strip(bri, WALK, NM0 - 12, blend=0, bout=0, repeat=3.0)
strip(bri, LAY, OP0 - 4, blend=0, bout=0, repeat=3.0)
STREET = Vector((200.0, 0.0, 0.0)); ORC = Vector((250.0, 0.0, 0.0))
headE = child_of_bone("bri_head", bri, "Head"); faceT = empty("faceT", (0, 0.06, 0.08), headE)
hipsE = child_of_bone("bri_hips", bri, "Hips")
place(broot, 1, (0, 0, float(os.environ.get("SITZ", 0.0))))
def bw(b): return (bri.matrix_world @ bri.pose.bones["mixamorig:" + b].head).copy()
# yurish tezligi: tayanch oyoqning tanaga nisbatan orqaga siljishidan
sc.frame_set(NM0); ys = []
for f in range(NM0, NM0 + 40):
    sc.frame_set(f); ys.append(bw("LeftFoot").y)
dy = sorted(b_ - a_ for a_, b_ in zip(ys, ys[1:])); WSPD = sum(dy[-10:-2]) / 8.0
print("walk speed m/frame", round(WSPD, 4))
W_START = STREET + Vector((0, 2.4, 0)); W_END = W_START + Vector((0, -WSPD * (NM1 - NM0), 0))
place(broot, NM0, tuple(W_START)); place(broot, NM1, tuple(W_END)); place(broot, OP0, tuple(ORC + Vector((0, -0.2, -0.1))))
for fc in fcurves(broot):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if int(k.co.x) == NM0 else "CONSTANT"

# rentgen nusxa
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.1, base=0.01)
ghosts = []
for o in bmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g); g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
X_SHOTS = rng("xray", "gravity", "legs", "backflow")
REAL = rng("hook", "timer", "normal", "surgery")
for g in ghosts: vis(g, X_SHOTS, recursive=False)
for o in bmeshes: vis(o, REAL, recursive=False)

# ---- telefon: ekranda aylanadigan lenta ----
phone_m = mat("phone_body", (0.02, 0.02, 0.025), 0.25, metal=0.6)
screen_m = bpy.data.materials.new("screen"); screen_m.use_nodes = True
N = screen_m.node_tree.nodes; L = screen_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.name = "scroll"; L.new(tc.outputs["Object"], mp.inputs[0])
mp.inputs["Location"].default_value = (0.05, 0, 0)
br = N.new("ShaderNodeTexBrick"); br.offset = 0.0; br.inputs["Scale"].default_value = 5.5; br.inputs["Mortar Size"].default_value = 0.035
br.inputs["Color1"].default_value = (0.95, 0.25, 0.3, 1); br.inputs["Color2"].default_value = (0.15, 0.5, 0.95, 1)
br.inputs["Mortar"].default_value = (0.01, 0.01, 0.015, 1); br.inputs["Bias"].default_value = 0.0
L.new(mp.outputs[0], br.inputs["Vector"])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60.0; L.new(mp.outputs[0], nz.inputs["Vector"])
mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "OVERLAY"; mx.inputs["Factor"].default_value = 0.8
L.new(br.outputs["Color"], mx.inputs[6]); L.new(nz.outputs["Color"], mx.inputs[7])
L.new(mx.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 2.5
b.inputs["Base Color"].default_value = (0, 0, 0, 1); b.inputs["Roughness"].default_value = 0.05
def scroll_key(f, y):
    mp.inputs["Location"].default_value = (0.05, y, 0); mp.inputs["Location"].keyframe_insert("default_value", frame=f)
for f, y in ((1, 0.0), (TM0, 0.1), (TM1, 0.75), (XR0, 0.8), (NM0, 1.0), (NM1, 1.4)): scroll_key(f, y)
def make_phone(name, parent):
    e = empty(name, (0, 0, 0), parent)
    box(name + "_b", (0.074, 0.154, 0.008), (0, 0, 0), phone_m, parent=e, bevel=0.003)
    plane(name + "_s", (0.068, 0.146), (0, 0, 0.0046), screen_m, parent=e)
    return e
phE = empty("phone_hands")
c1 = phE.constraints.new("COPY_LOCATION"); c1.target = bri; c1.subtarget = "mixamorig:LeftHand"
c2 = phE.constraints.new("COPY_LOCATION"); c2.target = bri; c2.subtarget = "mixamorig:RightHand"; c2.influence = 0.5
phone = make_phone("phone", phE); phone.location = (0.0, -0.045, 0.05); phone.rotation_euler = (R(28), 0, R(180))
vis(phone, rng("hook", "timer") + X_SHOTS)
phW = child_of_bone("phone_walk", bri, "RightHand")
phone2 = make_phone("phone2", phW)
phone2.location = [float(v) for v in os.environ.get("PH2", "0.0,0.09,0.035").split(",")]
phone2.rotation_euler = [R(float(v)) for v in os.environ.get("PH2R", "0,0,0").split(",")]
vis(phone2, rng("normal"))
# taymer (ekran ustida, kameraga qaraydi)
timer_m = emit_mat("timer", (1.0, 1.0, 1.0), 4.0)
timerE = empty("timerE", (0, 0, 0.0), phE); timerE.location = (0.0, -0.17, 0.105)
timerT = text("timer", "00:00", 0.05, (0, 0, 0), (0, 0, 0), timer_m, timerE, extrude=0.002)
vis(timerT, rng("timer"), recursive=False)
def _timer(scene, *a):
    f = scene.frame_current
    t = min(1.0, max(0.0, (f - TM0 - 4) / float(TM1 - TM0 - 14)))
    secs = int(900 * t ** 1.4)
    timerT.data.body = f"{secs // 60:02d}:{secs % 60:02d}"
bpy.app.handlers.frame_change_pre.append(_timer)
eb = timer_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]
for f, c_ in ((TM0, (1, 1, 1, 1)), (TM0 + 26, (1, 1, 1, 1)), (TM0 + 36, (1.0, 0.08, 0.03, 1)), (TM1, (1.0, 0.08, 0.03, 1))):
    eb.default_value = c_; eb.keyframe_insert("default_value", frame=f)
for f, s_ in ((TM0, 0.6), (TM0 + 5, 1.0), (TM1 - 12, 1.0), (TM1 - 8, 1.35), (TM1 - 4, 1.15), (TM1, 1.2)): key(timerE, f, scale=(s_,) * 3)

# ======================================================================
# 3) RENTGEN: ichak, to'g'ri ichak, vena chigali, oyoq venalari, yurak; bosim o'lchagich; og'irlik strelkalari
# ======================================================================
sc.frame_set(XR0 + 10); bpy.context.view_layer.update()
H = bw("Hips"); SP2 = bw("Spine2")
UP = (SP2 - H).normalized(); XA = Vector((1, 0, 0)); FW = XA.cross(UP).normalized()
def TP(u, r, f): return H + UP * u + XA * r + FW * f
ANUS = H + Vector((0, 0.035, -0.115))
xr = empty("xr_parts")
rect_m = mat("x_rectum", (0.95, 0.45, 0.4), 0.35, emit=0.7, sss=0.2)
colon_m = mat("x_colon", (0.85, 0.5, 0.45), 0.4, emit=0.22)
P.tube("x_rectum", [TP(0.20, 0.05, 0.04), TP(0.14, 0.06, 0.03), TP(0.09, -0.03, 0.01), H + Vector((0, 0.035, 0.0)), ANUS + Vector((0, 0, 0.03)), ANUS],
       0.024, rect_m, xr, taper=[1, 1, 1, 1.15, 0.75, 0.45])
P.tube("x_colon", [TP(0.20, 0.05, 0.04), TP(0.17, 0.11, 0.05), TP(0.30, 0.125, 0.06), TP(0.37, 0.06, 0.07), TP(0.37, -0.06, 0.07),
                   TP(0.30, -0.125, 0.06), TP(0.17, -0.12, 0.05), TP(0.11, -0.07, 0.05)], 0.021, colon_m, xr)
legv_m = P.pulse_material("x_legvein", (0.05, 0.15, 0.9), base_emit=0.35, pulse_col=(0.35, 0.65, 1.0), width=0.05)
cava_m = P.pulse_material("x_cava", (0.08, 0.2, 0.9), base_emit=0.8, pulse_col=(0.35, 0.65, 1.0), width=0.05)
plex_m = mat("x_plexus", (0.9, 0.08, 0.1), 0.3, emit=1.6)
JN = TP(0.05, 0.0, -0.035)                                    # venalar qo'shiladigan joy (chanoq)
HEART = TP(0.43, 0.035, 0.05)
P.tube("x_cava", [JN, TP(0.16, 0.012, -0.045), TP(0.3, 0.015, -0.03), HEART], 0.0095, cava_m, xr)
for sd, sg in (("Left", 1), ("Right", -1)):
    toe, ank, knee, hip = bw(sd + "ToeBase"), bw(sd + "Foot"), bw(sd + "Leg"), bw(sd + "UpLeg")
    P.tube(f"x_leg{sd}", [toe + Vector((0, 0, 0.02)), ank + Vector((-sg * 0.02, 0.02, 0.0)), (ank + knee) / 2 + Vector((-sg * 0.025, 0.03, 0)),
                          knee + Vector((-sg * 0.02, 0.03, -0.02)), (knee + hip) / 2 + Vector((-sg * 0.03, 0, -0.03)), hip + Vector((-sg * 0.02, 0, -0.01)), JN],
           0.006, legv_m, xr, taper=[0.5, 0.7, 0.85, 0.95, 1.1, 1.2, 1.2])
    P.tube(f"x_hem{sd}", [ANUS + Vector((sg * 0.022, 0, 0.0)), ANUS + Vector((sg * 0.04, 0.0, 0.035)), H + Vector((sg * 0.035, 0.03, 0.0)), JN],
           0.0055, plex_m, xr)
for i, (dz, rr_) in enumerate(((0.004, 0.03), (0.03, 0.026))):
    bpy.ops.mesh.primitive_torus_add(major_radius=rr_, minor_radius=0.0065, major_segments=32, minor_segments=10)
    t_ = bpy.context.object; t_.name = f"x_plexring{i}"; t_.location = ANUS + Vector((0, 0, dz)); t_.data.materials.append(plex_m); t_.parent = xr; smooth(t_)
heart = sphere("x_heart", 0.05, tuple(HEART), mat("x_heartm", (0.9, 0.08, 0.08), 0.3, emit=1.2), scale=(1, 0.8, 1.15), sub=3, parent=xr)
for f in range(XR0, BF1 + 1, 10):
    key(heart, f, scale=(1, 0.8, 1.15)); key(heart, f + 3, scale=(1.22, 0.98, 1.38))
press_m = glow_mat("x_press", (1.0, 0.1, 0.05))
press = sphere("x_pressglow", 0.085, tuple(ANUS + Vector((0, 0, 0.02))), press_m, sub=4, parent=xr)
for f in range(XR0, BF1 + 1, 8):
    k_ = 0.5 + 2.0 * min(1.0, (f - XR0) / 80.0)
    val_key(press_m, "a", f, k_); val_key(press_m, "a", f + 4, k_ * 1.9)
for f, v in ((1, 0.3), (LG0, 0.18), (LG0 + 16, 0.33), (LG0 + 32, 0.22), (LG1, 0.3), (BF0, 0.28), (BF0 + 17, 0.86), (BF0 + 24, 0.8),
             (BF0 + 33, 0.26), (BF0 + 39, 0.4), (BF1, 0.27)): val_key(legv_m, "pos", f, v)
for f, v in ((1, 0.15), (BF0, 0.1), (BF0 + 20, 0.1), (BF0 + 26, 0.3), (BF0 + 34, 0.05), (BF1, 0.1)): val_key(cava_m, "pos", f, v)
vis(xr, X_SHOTS)
# og'irlik strelkalari
arr_m = emit_mat("arrow", (1.0, 0.6, 0.02), 2.6)
for i, (x_, d_) in enumerate(((-0.2, 0), (-0.07, 7), (0.07, 3), (0.2, 10), (0.0, 14))):
    a_ = arrow(f"garrow{i}", arr_m, s=1.15)
    y_ = H.y - 0.07 + (0.06 if i == 4 else 0)
    key(a_, GR0 - 30 + d_, loc=(x_, y_, 1.42)); key(a_, GR0 - 30 + d_ + 22, loc=(x_, y_, 0.7)); cyc(a_)
    vis(a_, rng("gravity"))
# o'rindiq teshigi: sariq halqa + strelka
ring_m = emit_mat("hole_ring", (1.0, 0.8, 0.05), 6.0)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.07, major_segments=64, minor_segments=10)
hring = bpy.context.object; hring.name = "hole_ring"; hring.data.materials.append(ring_m); smooth(hring)
HR = [float(v) for v in os.environ.get("HRING", "0.105,0.145").split(",")]
for f, s_ in ((ST0, 0.3), (ST0 + 8, 1.12), (ST0 + 12, 1.0), (ST0 + 24, 1.1), (ST0 + 36, 1.0), (ST0 + 48, 1.1), (ST1, 1.0)):
    key(hring, f, loc=tuple(HOLE + Vector((0, 0, 0.012))), scale=(HR[0] * s_, HR[1] * s_, 0.1 * s_))
vis(hring, rng("seat"), recursive=False)
sarrow = arrow("seat_arrow", arr_m, s=1.5)
for f, z in ((ST0 + 30, 0.55), (ST0 + 40, 0.12), (ST0 + 46, 0.2), (ST0 + 54, 0.1), (ST1, 0.16)): key(sarrow, f, loc=tuple(HOLE + Vector((0, 0, z))))
vis(sarrow, [(ST0 + 30, ST1)])
# bosim o'lchagich (kameraga bog'lanadi)
gauge = empty("gauge")
g_face = cyl("g_face", 0.1, 0.006, (0, 0, 0), mat("g_face", (0.02, 0.02, 0.025), 0.4), parent=gauge, verts=64)
bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.008, major_segments=64, minor_segments=10)
t_ = bpy.context.object; t_.name = "g_rim"; t_.data.materials.append(chrome_m); t_.parent = gauge; smooth(t_)
def sector(name, a0, a1, r0, r1, m):
    n = 24; vs = []; fs = []
    for i in range(n + 1):
        a = R(a0 + (a1 - a0) * i / n); vs += [(r0 * math.cos(a), r0 * math.sin(a), 0.004), (r1 * math.cos(a), r1 * math.sin(a), 0.004)]
    for i in range(n): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    return mesh_obj(name, vs, fs, m, gauge)
sector("g_green", 210, 115, 0.066, 0.09, emit_mat("g_green", (0.1, 0.9, 0.2), 1.5))
sector("g_yellow", 112, 38, 0.066, 0.09, emit_mat("g_yellow", (1.0, 0.75, 0.05), 1.8))
sector("g_red", 35, -30, 0.066, 0.09, emit_mat("g_red", (1.0, 0.05, 0.03), 2.2))
needle = mesh_obj("g_needle", [(-0.012, -0.005, 0.008), (0.082, -0.0015, 0.008), (0.082, 0.0015, 0.008), (-0.012, 0.005, 0.008)], [(0, 1, 2, 3)],
                  emit_mat("g_needle", (1, 1, 1), 3.0), gauge)
cyl("g_hub", 0.011, 0.012, (0, 0, 0.006), chrome_m, parent=gauge, verts=24)
text("g_text", "BOSIM", 0.024, (0, -0.048, 0.005), (0, 0, 0), emit_mat("g_text", (1, 1, 1), 2.5), gauge)
G0 = T(5.3)
rg = random.Random(5)
nk = [(G0 - 2, 210), (G0 + 8, 190), (T(6.25), 95), (T(6.7), -8)] + [(f, rg.uniform(-22, -4)) for f in range(T(6.7) + 2, XR1 + 1, 2)]
for f, a in nk: needle.rotation_euler = (0, 0, R(a)); needle.keyframe_insert("rotation_euler", frame=f)
vis(gauge, [(G0, XR1)])

# ======================================================================
# 4) KESIM STUDIYASI (60,0,0): o'rindiq halqasi, kosa, to'qima (teshikka osiladi), anal kanal, vena chigali, tugunlar
#    1 birlik ~ 10 sm. Kesim tekisligi y=0, kamera -Y tomonda.
# ======================================================================
C0 = Vector((60.0, 0.0, 0.0))
stud = empty("cut_studio", tuple(C0))
HWD = 0.62                                                   # teshik yarim kengligi
SAGD = 0.34                                                  # to'liq osilish chuqurligi
ZA = -0.10                                                   # anal teshik (dam holatida)
def hump(x): return math.cos(math.pi * x / (2 * HWD)) ** 2 if abs(x) < HWD else 0.0
def gs(x, c, w): return math.exp(-((x - c) / w) ** 2)
def zb(x, sag=0.0, lump=0.0):
    return -(0.10 + SAGD * sag) * hump(x) - lump * 0.2 * (gs(x, 0.18, 0.14) + 0.8 * gs(x, -0.18, 0.13))
TOP, XW, NXt, NZt, DEP = 2.4, 2.1, 168, 30, 1.6
def tissue_co(sag, lump):
    cs = []
    for i in range(NXt + 1):
        x = -XW + 2 * XW * i / NXt; b_ = zb(x, sag, lump)
        for j in range(NZt + 1): cs.append((x, 0.0, b_ + (TOP - b_) * (j / NZt) ** 1.8))
    for i in range(NXt + 1):
        x = -XW + 2 * XW * i / NXt; cs.append((x, DEP, zb(x, sag, lump)))
    return cs
base = tissue_co(0, 0); fs = []; nb = (NXt + 1) * (NZt + 1)
for i in range(NXt):
    for j in range(NZt):
        a_ = i * (NZt + 1) + j; fs.append((a_, a_ + NZt + 1, a_ + NZt + 2, a_ + 1))
    fs.append((i * (NZt + 1), nb + i, nb + i + 1, (i + 1) * (NZt + 1)))
flesh_m = bpy.data.materials.new("flesh"); flesh_m.use_nodes = True
N = flesh_m.node_tree.nodes; L = flesh_m.node_tree.links; b = N["Principled BSDF"]
at = N.new("ShaderNodeAttribute"); at.attribute_name = "d"
rp = N.new("ShaderNodeValToRGB"); L.new(P.math_n(N, L, "DIVIDE", at.outputs["Fac"], 0.7, clamp=True), rp.inputs["Fac"])
els = rp.color_ramp.elements
els[0].position = 0.0; els[0].color = (0.78, 0.5, 0.4, 1); els[1].position = 0.028; els[1].color = (0.8, 0.52, 0.42, 1)
for p_, c_ in ((0.04, (0.95, 0.74, 0.32, 1)), (0.3, (0.93, 0.66, 0.28, 1)), (0.4, (0.62, 0.14, 0.12, 1)), (1.0, (0.5, 0.1, 0.09, 1))):
    e_ = els.new(p_); e_.color = c_
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 16.0
L.new(tc.outputs["Object"], vo.inputs["Vector"])
mr = N.new("ShaderNodeMapRange"); L.new(vo.outputs["Distance"], mr.inputs["Value"]); mr.inputs["From Max"].default_value = 0.6
mr.inputs["To Min"].default_value = 0.72; mr.inputs["To Max"].default_value = 1.08
mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
L.new(rp.outputs["Color"], mx.inputs[6]); L.new(mr.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.42; b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Scale"].default_value = 0.03
b.inputs["Coat Weight"].default_value = 0.25
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.02
L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
tissue = mesh_obj("tissue", base, fs, flesh_m, stud); smooth(tissue)
da = tissue.data.attributes.new("d", "FLOAT", "POINT")
for i, v in enumerate(tissue.data.vertices):
    da.data[i].value = 0.0 if i >= nb else max(0.0, v.co.z - zb(v.co.x))
tissue.shape_key_add(name="Basis")
TK = {}
for nm_, (s_, l_) in (("sag", (1, 0)), ("lump", (0, 1))):
    kb = tissue.shape_key_add(name=nm_, from_mix=False); kb.value = 0.0; TK[nm_] = kb
    for v, c_ in zip(kb.data, tissue_co(s_, l_)): v.co = c_
F_SAG = T(16.95); F_POP = T(30.2); F_BURST = T(32.78)
SAGK = [(1, 0.0), (SG0 + 20, 0.0), (T(16.2), 0.3), (F_SAG, 1.08), (F_SAG + 5, 0.96), (F_SAG + 10, 1.0), (END, 1.0)]
LUMPK = [(1, 0.0), (BG0 + 6, 0.05), (F_POP - 6, 0.35), (F_POP, 1.1), (F_POP + 5, 0.94), (F_POP + 10, 1.0), (END, 1.0)]
skey(TK["sag"], SAGK); skey(TK["lump"], LUMPK)
core = empty("core", (0, 0, 0), stud)
for f, v in SAGK: key(core, f, loc=(0, 0, -SAGD * v))
# o'rindiq halqasi (orqa yarmi) + kosa + suv
seat_m = mat("seat_plastic", (0.93, 0.93, 0.92), 0.18, coat=0.6)
sweep("seat_ring", rrect(0.4, 0.15, -0.075), HWD + 0.2, 1.05, seat_m, parent=stud)
BOWLP = [(0.86, -0.15), (0.86, -0.32), (0.8, -0.72), (0.66, -1.15), (0.5, -1.5), (0.36, -1.8), (0.3, -2.1), (0.3, -2.6)]
bowl_b = sweep("bowl_back", BOWLP, 0.0, 0.25, cer_m, closed=False, parent=stud)
bowl_f = sweep("bowl_front", BOWLP, 0.0, 0.25, cer_m, a0=math.pi, a1=2 * math.pi, closed=False, parent=stud)
for o in (bowl_b, bowl_f):
    sm_ = o.modifiers.new("sol", "SOLIDIFY"); sm_.thickness = 0.08; sm_.offset = 1.0
WZ = -1.42                                                   # suv sathi
water_m = mat("bowl_water", (0.7, 0.9, 1.0), 0.02, trans=0.85, ior=1.33, emit=0.08, emit_col=(0.3, 0.6, 0.9))
def wdisc(name, a0, a1):
    n = 40; vs = [(0, 0, 0)]; fs_ = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n; vs.append((0.56 * math.cos(a), 0.81 * math.sin(a), 0))
    for i in range(n): fs_.append((0, i + 1, i + 2))
    return mesh_obj(name, vs, fs_, water_m, stud, (0, 0, WZ))
wat_b = wdisc("water_back", 0, math.pi); wat_f = wdisc("water_front", math.pi, 2 * math.pi)
vis(bowl_f, [], recursive=False); vis(wat_f, rng("bowl"), recursive=False)
plane("cut_bg", (16, 12), tuple(C0 + Vector((0, 2.6, 0))), mat("cut_bg", (0.015, 0.05, 0.07), 0.9), rot=(90, 0, 0))
# kanal + to'g'ri ichak (kesimda)
OUTL = [(0.02, ZA - 0.01), (0.028, ZA + 0.2), (0.035, ZA + 0.42), (0.12, ZA + 0.56), (0.24, ZA + 0.8), (0.27, ZA + 1.1), (0.21, ZA + 1.5), (0.19, ZA + 2.6)]
vs = []; fs = []
for x, z in OUTL: vs += [(-x, -0.004, z), (x, -0.004, z)]
for i in range(len(OUTL) - 1): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
mesh_obj("lumen", vs, fs, mat("lumen", (0.22, 0.04, 0.045), 0.6), core)
muc_m = mat("mucosa", (0.92, 0.5, 0.5), 0.3, sss=0.3, sss_scale=0.02, coat=0.5)
for sg in (1, -1):
    P.tube(f"mucosa{sg}", [(sg * x, -0.012, z) for x, z in OUTL], 0.016, muc_m, core)
    smus = mat("sphincter", (0.42, 0.07, 0.06), 0.5) if sg == 1 else bpy.data.materials["sphincter"]
    sphere(f"sph_in{sg}", 1.0, (sg * 0.125, 0.0, ZA + 0.15), smus, scale=(0.035, 0.012, 0.13), sub=3, parent=core)
    sphere(f"sph_out{sg}", 1.0, (sg * 0.215, 0.0, ZA + 0.12), smus, scale=(0.03, 0.012, 0.1), sub=3, parent=core)
# venalar
cvein_m = P.pulse_material("cut_vein", (0.2, 0.12, 0.62), base_emit=0.25, pulse_col=(0.5, 0.4, 1.0), width=0.05)
for n_ in cvein_m.node_tree.nodes:                        # impuls ortidagi "iz" kerak emas (tomir oqarib ketadi)
    if n_.type == "MATH" and n_.operation == "MULTIPLY" and abs(n_.inputs[1].default_value - 0.25) < 1e-6: n_.inputs[1].default_value = 0.0
VEINS = []
for sg in (1, -1):
    for nm_, pts, r_ in (
        ("main", [(0.07, ZA + 0.03), (0.1, ZA + 0.2), (0.085, ZA + 0.42), (0.2, ZA + 0.6), (0.33, ZA + 0.9), (0.37, ZA + 1.3), (0.31, ZA + 2.6)], 0.02),
        ("a", [(0.1, ZA + 0.2), (0.19, ZA + 0.3), (0.26, ZA + 0.55), (0.33, ZA + 0.9)], 0.014),
        ("b", [(0.07, ZA + 0.03), (0.17, ZA + 0.06), (0.22, ZA + 0.2), (0.19, ZA + 0.3)], 0.013),
        ("c", [(0.085, ZA + 0.42), (0.15, ZA + 0.46), (0.2, ZA + 0.6)], 0.012),
        ("d", [(0.26, ZA + 0.55), (0.4, ZA + 0.75), (0.5, ZA + 1.2), (0.52, ZA + 2.6)], 0.012)):
        t_ = P.tube(f"cvein_{nm_}{sg}", [(sg * x, -0.02, z) for x, z in pts], r_, cvein_m, core); VEINS.append((t_, r_))
for t_, r_ in VEINS:
    for f, k_ in ((1, 1.0), (SG1, 1.0), (BG0, 1.35), (F_POP, 1.6), (END, 1.6)): P.tube_r(t_, f, r_ * k_)
for f, v in ((1, -0.2), (SG0, -0.2), (SG0 + 40, 1.2), (SG0 + 41, -0.2), (SG1, 0.9), (BG0, 0.0), (BG1, 0.2), (END, 0.2)): val_key(cvein_m, "pos", f, v)
interp(cvein_m.node_tree, "LINEAR")
# tugunlar (gemorroy): ichki, o'rta, tashqi
def bulge_mat(name):
    m = mat(name, (0.3, 0.035, 0.1), 0.22, coat=0.7, sss=0.25, sss_scale=0.02, emit=0.06, emit_col=(0.5, 0.05, 0.1))
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; inf = value_node(m, "inf", 0.0)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(inf, mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.3, 0.035, 0.1, 1); mx.inputs[7].default_value = (0.62, 0.6, 0.12, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    return m
bulge_m = bulge_mat("bulge"); bulgeR_m = bulge_mat("bulge_inf")
BUL = {}
for sg in (1, -1):
    for nm_, p0, r0, p1, r1 in (("I", (0.085, ZA + 0.42), 0.036, (0.1, ZA + 0.42), 0.085),
                                ("M", (0.1, ZA + 0.2), 0.036, (0.115, ZA + 0.2), 0.09),
                                ("E", (0.16, ZA + 0.02), 0.03, (0.18, ZA - 0.07), 0.15 if sg == 1 else 0.125)):
        s_ = sphere(f"bulge_{nm_}{sg}", 1.0, (0, 0, 0), bulgeR_m if (nm_ == "E" and sg == 1) else bulge_m, sub=4, parent=core)
        BUL[(nm_, sg)] = s_
        for f, t_ in ((1, 0.0), (SG1, 0.0), (BG0, 0.3), (F_POP - 6, 0.5), (F_POP, 1.12), (F_POP + 5, 0.95), (F_POP + 10, 1.0), (END, 1.0)):
            r_ = r0 + (r1 - r0) * t_
            key(s_, f, loc=(sg * (p0[0] + (p1[0] - p0[0]) * t_), -0.03, p0[1] + (p1[1] - p0[1]) * t_), scale=(r_, r_ * 0.8, r_ * 1.08))
BR = BUL[("E", 1)]
for f, k_ in ((IF0 + 20, 1.0), (IF0 + 40, 1.12), (IF0 + 48, 1.06), (IF0 + 58, 1.2), (IF0 + 66, 1.14), (IF1, 1.25)):
    key(BR, f, scale=(0.15 * k_, 0.12 * k_, 0.162 * k_))
for f, v in ((1, 0.0), (IF0 + 22, 0.0), (IF1 - 6, 1.0), (END, 1.0)): val_key(bulgeR_m, "inf", f, v)
# yara + qon tomchilari
WOUND = Vector((0.2, -0.1, ZA - 0.07 - 0.165 - SAGD))           # stud koordinatasida (to'liq osilgan holatda)
wound = sphere("wound", 1.0, tuple(WOUND + Vector((0, -0.02, 0.035))), mat("wound", (0.5, 0.0, 0.0), 0.2, emit=1.2, coat=1.0), scale=(0.045, 0.03, 0.02), sub=3, parent=stud)
vis(wound, [(F_BURST, END)])
blood_m = mat("blood", (0.55, 0.0, 0.0), 0.1, coat=1.0, emit=0.5, emit_col=(0.8, 0.0, 0.0))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0); dm = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
dm.materials.append(blood_m)
for p_ in dm.polygons: p_.use_smooth = True
rd = random.Random(3); DROPS = []
for i in range(16):
    o = bpy.data.objects.new(f"bdrop{i}", dm); sc.collection.objects.link(o); o.parent = stud
    s_ = rd.uniform(0.022, 0.034); o.scale = (s_, s_, s_ * 1.7)
    f0 = F_BURST + i * 3 + rd.uniform(0, 2); dx, dy_ = rd.uniform(-0.03, 0.03), rd.uniform(-0.04, 0.04)
    p0 = WOUND + Vector((dx, dy_, 0)); n_ = 11
    for k_ in range(n_ + 1):
        tt = k_ / n_; o.location = p0 + Vector((dx * tt, dy_ * tt, (WZ - p0.z) * tt * tt)); o.keyframe_insert("location", frame=f0 + k_)
    cyc(o)
    for fc in fcurves(o): fc.modifiers[0].frame_start = F_BURST
    vis(o, [(int(f0) + 1, END)], recursive=False); DROPS.append(int(f0) + n_)
# suvda qon buluti + halqalar
for i in range(7):
    cm_ = mat(f"cloud{i}", (0.45, 0.0, 0.0), 0.3, alpha=0.9, emit=0.15, emit_col=(0.6, 0, 0))
    f0 = F_BURST + 12 + i * 8; ang = i * 2.4
    c_ = sphere(f"cloud{i}", 1.0, (0, 0, 0), cm_, sub=3, parent=stud)
    px = WOUND.x + 0.06 * math.cos(ang); py = WOUND.y + 0.08 * math.sin(ang)
    key(c_, f0, loc=(px, py, WZ - 0.01), scale=(0.02, 0.02, 0.01)); key(c_, f0 + 50, loc=(px + 0.1 * math.cos(ang), py + 0.12 * math.sin(ang), WZ - 0.06), scale=(0.36, 0.4, 0.09))
    al = cm_.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    for f, a in ((f0, 0.95), (f0 + 50, 0.5), (END, 0.4)): al.default_value = a; al.keyframe_insert("default_value", frame=f)
    vis(c_, [(f0, END)], recursive=False)
    rm_ = emit_mat(f"ripple{i}", (0.9, 0.95, 1.0), 1.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=48, minor_segments=6)
    r_ = bpy.context.object; r_.name = f"ripple{i}"; r_.data.materials.append(rm_); r_.parent = stud
    key(r_, f0, loc=(px, py, WZ + 0.004), scale=(0.03, 0.03, 0.03)); key(r_, f0 + 16, loc=(px, py, WZ + 0.004), scale=(0.3, 0.3, 0.06))
    vis(r_, [(f0, f0 + 16)], recursive=False)
# kesimdagi og'irlik strelkalari
for i, x_ in enumerate((-0.42, 0.42)):
    a_ = arrow(f"carrow{i}", arr_m, s=3.2); a_.parent = stud
    key(a_, SG0 - 26 + i * 9, loc=(x_, -0.12, 1.75)); key(a_, SG0 - 26 + i * 9 + 26, loc=(x_, -0.12, 0.55)); cyc(a_)
    vis(a_, [(SG0, F_SAG + 8)])
# infeksiya: bakteriyalar yaraga yopiriladi
bact_m = mat("bacteria", (0.12, 0.6, 0.05), 0.35, emit=0.45, coat=0.5)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1.0); bm_ = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
bm_.materials.append(bact_m)
for p_ in bm_.polygons: p_.use_smooth = True
rb = random.Random(11)
for i in range(90):
    o = bpy.data.objects.new(f"bact{i}", bm_); sc.collection.objects.link(o); o.parent = stud
    s_ = rb.uniform(0.008, 0.013); o.scale = (s_, s_, s_ * 2.6)
    p0 = Vector((rb.uniform(-1.3, 1.5), rb.uniform(-0.5, 0.2), rb.uniform(-1.9, -1.2)))
    d_ = Vector((rb.gauss(0, 1), rb.gauss(0, 0.6), rb.gauss(0, 1))).normalized() * rb.uniform(0.02, 0.17)
    p2 = WOUND + Vector((0, -0.03, 0.09)) + Vector((d_.x, -abs(d_.y) - 0.02, d_.z))
    pm = p0.lerp(p2, 0.55) + Vector((rb.uniform(-0.3, 0.3), 0, rb.uniform(-0.2, 0.2)))
    f0 = IF0 - 6 + rb.uniform(0, 30); f2 = f0 + rb.uniform(22, 40)
    for f, p_ in ((f0, p0), ((f0 + f2) / 2, pm), (f2, p2), (END, p2 + Vector((rb.uniform(-0.02, 0.02), 0, rb.uniform(-0.02, 0.02))))):
        o.location = p_; o.rotation_euler = (rb.uniform(0, 6.28), rb.uniform(0, 6.28), rb.uniform(0, 6.28))
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    vis(o, rng("infect"), recursive=False)
pus_m = glow_mat("pus_glow", (0.75, 0.9, 0.1))
pus = sphere("pus_glow", 1.0, tuple(WOUND + Vector((0, -0.08, 0.1))), pus_m, sub=4, parent=stud)
for f, s_, a in ((IF0 + 24, 0.1, 0.0), (IF0 + 50, 0.3, 0.7), (IF0 + 58, 0.34, 0.4), (IF1, 0.45, 1.1)):
    key(pus, f, scale=(s_,) * 3); val_key(pus_m, "a", f, a)
vis(pus, [(IF0 + 24, IF1)], recursive=False)

# ======================================================================
# 5) VENA STUDIYASI (120,0,0): yarim quvur (kameraga ochiq), qon tanachalari uyuladi, shardek shishadi, devori yupqalashadi
# ======================================================================
C2 = Vector((120.0, 0.0, 0.0))
vst = empty("vein_studio", tuple(C2))
def vr(z, bal=0.0, more=0.0): return 0.2 + (0.52 * bal + 0.17 * more) * math.exp(-(z / 0.5) ** 2)
NZv, NAv, VZ0, VZ1 = 110, 44, -1.5, 2.9
def vein_co(bal, more):
    cs = []
    for i in range(NZv + 1):
        z = VZ0 + (VZ1 - VZ0) * i / NZv; r_ = vr(z, bal, more)
        for j in range(NAv + 1):
            a = math.pi * j / NAv; cs.append((r_ * math.cos(a), r_ * math.sin(a), z))
    return cs
fs = []
for i in range(NZv):
    for j in range(NAv):
        a_ = i * (NAv + 1) + j; fs.append((a_, a_ + NAv + 1, a_ + NAv + 2, a_ + 1))
vwall_m = mat("vein_wall", (0.62, 0.22, 0.36), 0.32, coat=0.5, sss=0.3, sss_scale=0.03)
vrim_m = mat("vein_rim", (0.97, 0.72, 0.72), 0.4, sss=0.2, sss_scale=0.02)
vein = mesh_obj("vein", vein_co(0, 0), fs, vwall_m, vst); smooth(vein); vein.data.materials.append(vrim_m)
vein.shape_key_add(name="Basis"); VK = {}
for nm_, (b_, m_) in (("bal", (1, 0)), ("more", (0, 1))):
    kb = vein.shape_key_add(name=nm_, from_mix=False); kb.value = 0.0; VK[nm_] = kb
    for v, c_ in zip(kb.data, vein_co(b_, m_)): v.co = c_
nrm = vein.data.polygons[0].normal; ctr = vein.data.polygons[0].center
vsol = vein.modifiers.new("sol", "SOLIDIFY"); vsol.thickness = 0.065; vsol.material_offset_rim = 1
vsol.offset = 1.0 if nrm.dot(Vector((ctr.x, ctr.y, 0))) > 0 else -1.0
F_BAL = SW0 + 13
skey(VK["bal"], [(1, 0.0), (PL1 - 22, 0.0), (PL1, 0.1), (SW0, 0.12), (F_BAL, 1.1), (F_BAL + 4, 0.95), (SW1, 1.0), (END, 1.0)])
skey(VK["more"], [(1, 0.0), (TH0, 0.0), (TH1, 1.0), (END, 1.0)])
for f, v in ((1, 0.065), (TH0 + 4, 0.065), (TH1 - 8, 0.011), (END, 0.011)): vsol.thickness = v; vsol.keyframe_insert("thickness", frame=f)
cell_m = mat("blood_cell", (0.5, 0.012, 0.012), 0.28, coat=0.5, sss=0.2, sss_scale=0.01, emit=0.05, emit_col=(0.6, 0, 0))
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0); cmesh = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
cmesh.materials.append(cell_m)
for p_ in cmesh.polygons: p_.use_smooth = True
rc = random.Random(21); NC = 250
def cpos(z, r_, u, a): rr_ = r_ * math.sqrt(u); return Vector((rr_ * math.cos(a), max(-0.3 * r_, rr_ * math.sin(a)), z))
zs = []
while len(zs) < NC:
    z = rc.uniform(-1.35, 1.2)
    if rc.random() < (vr(z, 1) / vr(0, 1)) ** 2: zs.append(z)
zs.sort()
for i in range(NC):
    o = bpy.data.objects.new(f"cell{i}", cmesh); sc.collection.objects.link(o); o.parent = vst
    s_ = rc.uniform(0.04, 0.052); o.scale = (s_, s_, s_ * 0.36)
    o.rotation_euler = (rc.uniform(0, 6.28), rc.uniform(0, 6.28), rc.uniform(0, 6.28))
    u, a = rc.random(), rc.uniform(-0.6, 3.74)
    pcol = cpos(-1.4 + 2.5 * i / NC, 0.15, u, a); pbal = cpos(zs[i], 0.84 * vr(zs[i], 1), u, a); pmore = cpos(zs[i] * 1.03, 0.86 * vr(zs[i], 1, 1), u, a)
    f0 = PL0 - 16 + (i / NC) * (PL1 - PL0 - 6) + rc.uniform(-2, 2)
    for f, p_ in ((f0, Vector((pcol.x * 0.5, pcol.y * 0.5, 3.2))), (f0 + 17, pcol), (SW0 + 1, pcol), (F_BAL, pbal * 1.04), (F_BAL + 5, pbal), (TH0, pbal), (TH1, pmore)):
        o.location = p_; o.keyframe_insert("location", frame=f)
    o.keyframe_insert("rotation_euler", frame=f0); o.rotation_euler.x += rc.uniform(-3, 3); o.rotation_euler.y += rc.uniform(-3, 3)
    o.keyframe_insert("rotation_euler", frame=f0 + 17)
    o.rotation_euler.x += rc.uniform(-0.6, 0.6); o.keyframe_insert("rotation_euler", frame=TH1)
plane("vein_bg", (14, 12), tuple(C2 + Vector((0, 2.2, 0.5))), mat("vein_bg", (0.2, 0.035, 0.04), 0.85), rot=(90, 0, 0))

# ======================================================================
# 6) SHAR (o'xshatish) — (150,0,0)
# ======================================================================
C3 = Vector((150.0, 0.0, 0.0))
bal = empty("balloon", tuple(C3))
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0); bo = bpy.context.object; bo.name = "balloon_m"
for v in bo.data.vertices:
    z = v.co.z; k_ = 1.0 - 0.42 * z * z if z < 0 else 1.0
    v.co = Vector((v.co.x * k_, v.co.y * k_, (z * 1.22 if z < 0 else z) + 1.22))
smooth(bo); bal_m = mat("balloon_red", (0.85, 0.015, 0.02), 0.1, coat=1.0, trans=0.2, sss=0.2, sss_scale=0.05)
bo.data.materials.append(bal_m); bo.parent = bal
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.09, radius2=0.03, depth=0.14); kn = bpy.context.object; kn.name = "balloon_knot"
kn.location = (0, 0, -0.05); kn.data.materials.append(bal_m); kn.parent = bal; smooth(kn)
PUFFS = [BA0 + 2, BA0 + 11, BA0 + 20]
for f, s_ in ((BA0 - 1, 0.1), (PUFFS[0], 0.11), (PUFFS[0] + 5, 0.27), (PUFFS[0] + 8, 0.25), (PUFFS[1], 0.25), (PUFFS[1] + 5, 0.43), (PUFFS[1] + 8, 0.41),
              (PUFFS[2], 0.41), (PUFFS[2] + 5, 0.63), (BA1, 0.6)):
    key(bal, f, scale=(s_, s_, s_))
plane("bal_bg", (14, 12), tuple(C3 + Vector((0, 3.0, 0.8))), mat("bal_bg", (0.02, 0.28, 0.33), 0.8), rot=(90, 0, 0))

# ======================================================================
# 7) KO'CHA (200,0,0)
# ======================================================================
street = empty("street", tuple(STREET))
plane("pavement", (5.0, 90), tuple(STREET + Vector((0.2, 0, 0))), pbr("pavement", "concrete_pavement", 0.5))
box("curb", (0.16, 90, 0.14), tuple(STREET + Vector((2.7, 0, -0.07 + 0.0))), mat("curb", (0.5, 0.5, 0.5), 0.8))
plane("road", (9.0, 90), tuple(STREET + Vector((7.2, 0, -0.14))), pbr("road", "asphalt_02", 0.4))
box("wall_st", (0.3, 90, 3.4), tuple(STREET + Vector((-2.3, 0, 1.7))), pbr("plaster", "painted_plaster_wall", 0.5, tint=(1.0, 0.86, 0.7)))
rs = random.Random(8)
for i in range(7):
    box(f"shopwin{i}", (0.06, 1.5, 1.5), tuple(STREET + Vector((-2.14, 6 - i * 3.2, 1.45))), mat(f"shopwin{i}", (0.05, 0.08, 0.1), 0.05, metal=0.8))
    box(f"bld{i}", (7, 7.5, rs.uniform(8, 15)), tuple(STREET + Vector((15.5, 20 - i * 8.0, 4))),
        pbr(f"bld{i}", "painted_plaster_wall", 0.25, tint=rs.choice(((0.9, 0.7, 0.55), (0.7, 0.8, 0.85), (0.95, 0.9, 0.8)))))
for i in range(4):
    pe = empty(f"st_plant{i}", tuple(STREET + Vector((-1.75, 4.2 - i * 2.9, 0)))); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", pe); pe.scale = (1.7,) * 3
pain_m = glow_mat("pain", (1.0, 0.06, 0.03))
painE = child_of_bone("bri_pain", bri, "Hips")
pain = sphere("pain_glow", 0.13, [float(v) for v in os.environ.get("PAIN", "0,-0.1,-0.11").split(",")], pain_m, sub=4, parent=painE)
for f in range(NM0, NM1 + 1, 9):
    val_key(pain_m, "a", f, 0.6); val_key(pain_m, "a", f + 4, 4.0)
vis(pain, rng("normal"), recursive=False)

# ======================================================================
# 8) OPERATSIYA XONASI (250,0,0)
# ======================================================================
orr = empty("or_room", tuple(ORC))
plane("or_floor", (8, 8), tuple(ORC), tile_mat("or_tile", (0.55, 0.68, 0.66), (0.5, 0.63, 0.62), scale=2.0, rough=0.15))
plane("or_wall_b", (8, 3.2), tuple(ORC + Vector((0, 3.0, 1.6))), teal_t, rot=(90, 0, 0))
plane("or_wall_l", (8, 3.2), tuple(ORC + Vector((-3.0, 0, 1.6))), teal_t, rot=(90, 0, 90))
plane("or_ceil", (8, 8), tuple(ORC + Vector((0, 0, 3.2))), mat("or_ceil", (0.8, 0.85, 0.85), 0.8), rot=(180, 0, 0))
steel_m = mat("steel", (0.75, 0.77, 0.8), 0.18, metal=1.0)
box("or_table", (0.66, 2.0, 0.09), tuple(ORC + Vector((0, -0.25, 0.84))), mat("or_pad", (0.05, 0.06, 0.08), 0.5), bevel=0.02)
cyl("or_ped", 0.13, 0.8, tuple(ORC + Vector((0, -0.25, 0.4))), steel_m)
box("or_base", (0.6, 1.0, 0.06), tuple(ORC + Vector((0, -0.25, 0.03))), steel_m, bevel=0.01)
drape = box("or_drape", (0.78, 1.5, 0.24), tuple(ORC + Vector((0, -0.62, 0.99))), mat("drape", (0.03, 0.36, 0.33), 0.95), bevel=0.11)
LAMP = ORC + Vector((0.1, -0.35, 2.25))
lampE = empty("or_lamp", tuple(LAMP)); lampE.rotation_euler = (R(-14), R(8), 0)
cyl("lamp_body", 0.46, 0.09, (0, 0, 0), mat("lamp_body", (0.85, 0.87, 0.88), 0.3), parent=lampE, verts=64)
cyl("lamp_arm", 0.03, 1.0, (0, 0, 0.5), steel_m, parent=lampE)
led_m = mat("lamp_led", (1.0, 0.97, 0.9), 0.3, emit=0.0)
for i in range(7):
    a = i * math.pi / 3; rr_ = 0.0 if i == 6 else 0.27
    cyl(f"lamp_led{i}", 0.105 if i < 6 else 0.13, 0.01, (rr_ * math.cos(a), rr_ * math.sin(a), -0.048), led_m, parent=lampE, verts=32)
F_LAMP = OP0 + 16
le = led_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((OP0, 0.0), (F_LAMP - 1, 0.0), (F_LAMP, 14.0), (F_LAMP + 3, 3.0), (F_LAMP + 6, 22.0), (END, 40.0)): le.default_value = v; le.keyframe_insert("default_value", frame=f)
TRAY = ORC + Vector((0.72, -1.05, 0.98))
box("tray", (0.46, 0.32, 0.014), tuple(TRAY), steel_m, bevel=0.004)
cyl("tray_leg", 0.018, 0.97, tuple(TRAY + Vector((0.12, 0.05, -0.49))), steel_m, verts=12)
box("tray_cloth", (0.42, 0.28, 0.004), tuple(TRAY + Vector((0, 0, 0.009))), mat("tray_cloth", (0.05, 0.3, 0.5), 0.9))
scal = empty("scalpel", tuple(TRAY + Vector((-0.06, -0.02, 0.016)))); scal.rotation_euler = (0, 0, R(24))
box("scal_h", (0.115, 0.009, 0.004), (0, 0, 0), steel_m, parent=scal, bevel=0.0015)
mesh_obj("scal_b", [(0.057, -0.0045, 0), (0.1, -0.004, 0), (0.106, 0.004, 0), (0.057, 0.0045, 0), (0.057, -0.0045, 0.0012), (0.1, -0.004, 0.0012), (0.106, 0.004, 0.0012), (0.057, 0.0045, 0.0012)],
         [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3)], mat("blade", (0.9, 0.92, 0.95), 0.05, metal=1.0), scal)
for i, (dx, dy_, rz) in enumerate(((0.08, 0.07, -12), (0.1, -0.08, 8), (-0.1, 0.09, 35))):
    fe = empty(f"forceps{i}", tuple(TRAY + Vector((dx, dy_, 0.016)))); fe.rotation_euler = (0, 0, R(rz))
    box(f"fc_a{i}", (0.13, 0.005, 0.004), (0, 0.004, 0), steel_m, rot=(0, 0, 2), parent=fe); box(f"fc_b{i}", (0.13, 0.005, 0.004), (0, -0.004, 0), steel_m, rot=(0, 0, -2), parent=fe)
box("monitor", (0.5, 0.06, 0.36), tuple(ORC + Vector((-0.95, 0.75, 1.55))), mat("monitor", (0.03, 0.03, 0.035), 0.3))
ecg = [(-0.2 + 0.4 * i / 40.0, -0.035, (0.09 if i % 10 == 5 else (-0.04 if i % 10 == 6 else 0.0))) for i in range(41)]
et = P.tube("ecg", ecg, 0.004, emit_mat("ecg", (0.1, 1.0, 0.3), 5.0), None); et.location = ORC + Vector((-0.95, 0.75, 1.55)); et.data.splines[0].order_u = 2

# ======================================================================
# 9) KAMERALAR (har kadrda harakat: crash zoom, aylanma, ergashish, silkinish)
# ======================================================================
HK1 = S["hook"][1]
ht = tgt_path("hook_tgt", [(1, (0, -0.1, 0.86)), (20, (0, -0.14, 0.78)), (HK1, (0, -0.15, 0.76))])
c = shot_cam("hook", (0, 0, 0), ht, 20, fstop=2.8, clip=0.02)
path(c, [(1, (0.35, -1.98, 1.4)), (20, (0.3, -1.3, 0.62)), (HK1, (0.26, -1.18, 0.6))])
lens_keys(c, [(1, 18), (20, 24), (HK1, 26)]); shake(c, 20, 30, 0.012, seed=1)
c = shot_cam("timer", (0, 0, 0), phone, 32, fstop=5.6, clip=0.02)                    # POV: uning ko'zidan telefonga
sc.frame_set(TM0 + 10); FP = faceT.matrix_world.translation.copy(); PP = phone.matrix_world.translation.copy()
path(c, [(TM0, tuple(FP + Vector((-0.24, 0.12, 0.06)))), (TM1, tuple(FP.lerp(PP, 0.35) + Vector((-0.17, 0.06, 0.02))))]); lens_keys(c, [(TM0, 30), (TM1, 34)])
timerE.parent = c; timerE.location = (0.0, 0.085, -0.4)
shake(c, TM1 - 9, TM1, 0.006, seed=2)
tx = empty("x_tgt", tuple(ANUS + Vector((0, 0, 0.1))))
c = orbit_cam("xray", XR0, XR1, H, 1.5, 0.72, -58, -118, 0.45, 0.02, 30, tx)
gauge.parent = c; gauge.location = (0.058, 0.128, -0.6)
for f, s_ in ((G0 - 1, 0.01), (G0 + 5, 0.66), (G0 + 9, 0.55), (T(6.7), 0.55), (T(6.7) + 3, 0.64), (XR1, 0.6)): key(gauge, f, scale=(s_,) * 3)
st_ = tgt_path("seat_tgt", [(ST0, tuple(HOLE)), (ST1, tuple(HOLE + Vector((0, 0, -0.12))))])
c = shot_cam("seat", (0, 0, 0), st_, 24, clip=0.02)
path(c, [(ST0, (0.75, -1.15, 1.45)), (ST0 + 34, (0.3, -0.5, 1.25)), (ST1, (0.03, HOLE.y - 0.1, 0.86))])
gt = tgt_path("grav_tgt", [(GR0, tuple(H + Vector((0, -0.12, 0.42)))), (GR1, tuple(ANUS + Vector((0, 0, 0.05))))])
orbit_cam("gravity", GR0, GR1, H, 1.25, 1.05, -25, -62, 0.75, 0.0, 26, gt)
lt = tgt_path("legs_tgt", [(LG0, (0.0, -0.2, 0.2)), (LG1, (0.0, -0.08, 0.5))])
c = shot_cam("legs", (0, 0, 0), lt, 20, clip=0.02)
path(c, [(LG0, (0.55, -0.85, 0.1)), (LG1, (0.38, -0.62, 0.42))])
bt = tgt_path("bf_tgt", [(BF0, tuple(H + Vector((0.12, -0.3, -0.1)))), (BF0 + 18, tuple(H + Vector((0.05, -0.05, 0.02)))), (BF0 + 34, tuple(ANUS)), (BF1, tuple(ANUS))])
c = shot_cam("backflow", (0, 0, 0), bt, 30, clip=0.02)
path(c, [(BF0, (0.85, -0.78, 0.45)), (BF1, (0.62, -0.5, 0.66))]); shake(c, BF0 + 24, BF0 + 34, 0.008, seed=3)
# kesim
t_ = tgt_path("sag_tgt", [(SG0, (0, 0, 0.35)), (F_SAG, (0, 0, -0.3)), (SG1, (0, 0, -0.32))], C0)
c = shot_cam("sag", (0, 0, 0), t_, 28, fstop=8, clip=0.05)
path(c, [(SG0, (0.35, -5.4, 0.7)), (T(16.2), (0.2, -3.8, 0.2)), (F_SAG + 4, (0.1, -2.7, -0.3)), (SG1, (0.05, -2.5, -0.32))], C0)
shake(c, F_SAG, F_SAG + 9, 0.03, seed=4)
t_ = empty("bulge_tgt", tuple(C0 + Vector((0.05, -0.03, ZA - SAGD - 0.04))))
c = shot_cam("bulge", (0, 0, 0), t_, 24, fstop=8, clip=0.05)
path(c, [(BG0, (0.6, -2.3, -1.25)), (F_POP, (0.35, -1.7, -1.0)), (BG1, (0.3, -1.6, -0.95))], C0); shake(c, F_POP, F_POP + 9, 0.03, seed=5)
t_ = tgt_path("burst_tgt", [(BU0, tuple(WOUND + Vector((-0.02, 0.07, 0.17)))), (F_BURST, tuple(WOUND + Vector((0, 0, 0.08)))), (BU1, tuple(WOUND + Vector((0, 0, -0.3))))], C0)
c = shot_cam("burst", (0, 0, 0), t_, 28, fstop=8, clip=0.05)
path(c, [(BU0, (0.75, -1.6, -0.42)), (F_BURST, (0.5, -1.15, -0.55)), (BU1, (0.5, -1.35, -0.9))], C0); shake(c, F_BURST, F_BURST + 10, 0.035, seed=6)
t_ = empty("bowl_tgt", tuple(C0 + WOUND + Vector((0, 0, -0.3))))
c = shot_cam("bowl", (0, 0, 0), t_, 22, clip=0.02)
path(c, [(BW0, (0.75, -1.5, WZ + 0.3)), (BW1, (0.6, -1.3, WZ + 0.18))], C0)
t_ = tgt_path("inf_tgt", [(IF0, (0.1, 0, -0.9)), (IF0 + 36, tuple(WOUND + Vector((0, 0, 0.06)))), (IF1, tuple(WOUND + Vector((0, 0, 0.08))))], C0)
c = shot_cam("infect", (0, 0, 0), t_, 26, fstop=8, clip=0.05)
path(c, [(IF0, (-0.6, -2.5, -1.3)), (IF0 + 40, (0.35, -1.2, -0.85)), (IF1, (0.27, -0.74, -0.66))], C0)
lens_keys(c, [(IF0, 24), (IF0 + 40, 28), (IF1, 34)]); shake(c, IF0 + 40, IF0 + 50, 0.02, seed=7)
# vena
t_ = tgt_path("pool_tgt", [(PL0, (0, 0, 1.2)), (PL1, (0, 0.05, -0.6))], C2)
c = shot_cam("pool", (0, 0, 0), t_, 26, fstop=5.6, clip=0.05)
path(c, [(PL0, (0.45, -2.3, 1.8)), (PL1, (-0.25, -1.7, -0.6))], C2)
t_ = empty("swell_tgt", tuple(C2 + Vector((0, 0.1, 0.0))))
c = shot_cam("swell", (0, 0, 0), t_, 24, fstop=5.6, clip=0.05)
path(c, [(SW0, (-0.25, -2.1, -0.35)), (F_BAL, (0.05, -2.7, 0.0)), (SW1, (0.12, -2.9, 0.08))], C2); shake(c, F_BAL - 2, F_BAL + 6, 0.03, seed=8)
t_ = tgt_path("thin_tgt", [(TH0, (0.72, 0, 0.1)), (TH1, (0.9, 0, 0.0))], C2)
c = shot_cam("thin", (0, 0, 0), t_, 34, fstop=8, clip=0.05)
path(c, [(TH0, (1.2, -1.7, 0.6)), (TH1, (0.98, -1.05, 0.2))], C2)
t_ = tgt_path("bal_tgt", [(BA0, (0, 0, 0.15)), (BA1, (0, 0, 0.75))], C3)
c = shot_cam("balloon", (0, 0, 0), t_, 22, fstop=4, clip=0.05)
path(c, [(BA0, (0.25, -0.9, 0.08)), (BA1, (0.1, -1.85, 0.5))], C3)
for pf in PUFFS: shake(c, pf, pf + 6, 0.02, seed=pf)
# ko'cha
t_ = tgt_path("walk_tgt", [(NM0, tuple(W_START + Vector((0, 0, 0.95)))), (NM1, tuple(W_END + Vector((0, 0, 1.25))))]); interp(t_, "LINEAR")
c = shot_cam("normal", (0, 0, 0), t_, 26, fstop=2.8, clip=0.05)
path(c, [(NM0, tuple(W_START + Vector((0.5, 1.7, 0.3)))), (NM0 + 36, tuple(W_START + Vector((1.4, 0.3 - WSPD * 36, 0.6)))), (NM1, tuple(W_END + Vector((0.9, -1.5, 1.05))))])
lens_keys(c, [(NM0, 24), (NM1, 32)])
# operatsiya
t_ = tgt_path("op_tgt", [(OP0, tuple(TRAY + Vector((-0.03, 0, 0.02)))), (OP0 + 22, tuple(ORC + Vector((0, 0.0, 1.05)))), (OP1, tuple(ORC + Vector((0.0, 0.1, 1.05))))])
c = shot_cam("surgery", (0, 0, 0), t_, 30, fstop=2.4, clip=0.02)
path(c, [(OP0, tuple(TRAY + Vector((0.2, -0.3, 0.14)))), (OP0 + 22, tuple(ORC + Vector((0.95, -1.5, 1.9)))), (OP1, tuple(ORC + Vector((0.6, -1.05, 1.75))))])
lens_keys(c, [(OP0, 30), (OP0 + 22, 24), (OP1, 22)])

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 10) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
WN = w.node_tree.nodes; WL = w.node_tree.links
bg = WN["Background"]; bg.inputs["Color"].default_value = (0.02, 0.03, 0.06, 1); bg.inputs["Strength"].default_value = 1.0
env = WN.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
bg2 = WN.new("ShaderNodeBackground"); WL.new(env.outputs[0], bg2.inputs["Color"]); bg2.inputs["Strength"].default_value = 1.0
mixw = WN.new("ShaderNodeMixShader"); hv = WN.new("ShaderNodeValue"); hv.name = "hdri"
WL.new(hv.outputs[0], mixw.inputs[0]); WL.new(bg.outputs[0], mixw.inputs[1]); WL.new(bg2.outputs[0], mixw.inputs[2])
WL.new(mixw.outputs[0], WN["World Output"].inputs["Surface"])
for f, v in ((1, 0.0), (NM0, 1.0), (NM1 + 1, 0.0)): hv.outputs[0].default_value = v; hv.outputs[0].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(34), 0, R(-125)); sun.data.angle = R(2)
for f, e in lights_for(rng("normal"), 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
LIT = rng("hook", "timer", "seat")
midT = empty("mid_tgt", (0.0, -0.2, 0.8))
area("ceil_l", (0.15, -0.6, 2.42), 1.2, (1.0, 0.95, 0.88), lights_for(LIT, 190.0), target=midT)
area("window_l", (0.0, 0.55, 1.85), 0.5, (0.8, 0.9, 1.0), lights_for(LIT, 45.0), target=empty("win_t", (0, -1.0, 0.9)))
area("face_fill", (0.7, -1.3, 1.3), 0.6, (1.0, 0.93, 0.85), lights_for(rng("hook"), 28.0), target=faceT)
area("x_dim", (0.15, -0.6, 2.42), 1.6, (0.3, 0.45, 0.9), lights_for(X_SHOTS, 24.0), target=midT)
l_ = area("phone_l", (0, 0, 0), 0.08, (0.6, 0.75, 1.0), lights_for(rng("hook", "timer"), 2.2), target=faceT)
l_.parent = phE; l_.location = (0, -0.05, 0.1)
# kesim studiyasi
CUT_SHOTS = rng("sag", "bulge", "burst", "bowl", "infect")
stT = empty("cut_lt", tuple(C0 + Vector((0, 0.1, -0.3))))
area("st_key", tuple(C0 + Vector((-1.5, -2.8, 1.7))), 1.6, (1.0, 0.93, 0.86), lights_for(CUT_SHOTS, 480.0), target=stT)
area("st_rim", tuple(C0 + Vector((1.9, 0.5, 0.5))), 1.0, (0.8, 0.9, 1.0), lights_for(CUT_SHOTS, 200.0), target=stT)
area("st_low", tuple(C0 + Vector((0.2, -1.7, -1.3))), 0.6, (1.0, 0.85, 0.75), lights_for(CUT_SHOTS, 70.0), target=empty("cut_lt2", tuple(C0 + Vector((0, 0, -0.5)))))
area("st_bowl", tuple(C0 + Vector((0.0, -0.1, -0.8))), 0.5, (1.0, 0.97, 0.92), lights_for(rng("bowl"), 30.0), target=empty("cut_lt3", tuple(C0 + Vector((0, 0, WZ)))))
fl = point("burst_flash", tuple(C0 + WOUND + Vector((0, -0.3, 0.05))), 0.1, (1.0, 0.1, 0.05), [(1, 0)], const=False)
for f, v in ((F_BURST - 1, 0), (F_BURST, 140), (F_BURST + 5, 30), (F_BURST + 14, 0)): fl.data.energy = v; fl.data.keyframe_insert("energy", frame=f)
gl = point("infect_l", tuple(C0 + WOUND + Vector((0, -0.35, 0.1))), 0.1, (0.6, 1.0, 0.1), [(1, 0)], const=False)
for f, v in ((IF0 + 20, 0), (IF0 + 50, 10), (IF1, 22), (IF1 + 1, 0)): gl.data.energy = v; gl.data.keyframe_insert("energy", frame=f)
# vena studiyasi
vT = empty("vein_lt", tuple(C2 + Vector((0, 0.1, 0.2))))
area("v_key", tuple(C2 + Vector((-1.4, -2.4, 1.7))), 1.5, (1.0, 0.92, 0.86), lights_for(rng("pool", "swell"), 420.0), target=vT)
area("v_rim", tuple(C2 + Vector((1.7, 0.3, 0.9))), 1.0, (0.8, 0.88, 1.0), lights_for(rng("pool", "swell", "thin"), 170.0), target=vT)
area("v_in", tuple(C2 + Vector((0.0, -1.0, 0.2))), 0.5, (1.0, 0.8, 0.7), lights_for(rng("pool", "swell", "thin"), 35.0), target=vT)
day = area("tl_day", tuple(C2 + Vector((-1.2, -2.0, 1.2))), 1.0, (1.0, 0.75, 0.4), [(1, 0)], target=vT)
night = area("tl_night", tuple(C2 + Vector((2.2, -1.8, 0.4))), 1.0, (0.3, 0.45, 1.0), [(1, 0)], target=vT)
for i, f in enumerate(range(TH0, TH1 + 1, 6)):
    for l_, e in ((day, 420.0 if i % 2 == 0 else 0.0), (night, 0.0 if i % 2 == 0 else 280.0)):
        l_.data.energy = e; l_.data.keyframe_insert("energy", frame=f)
for l_ in (day, night):
    l_.data.energy = 0; l_.data.keyframe_insert("energy", frame=TH0 - 1); l_.data.keyframe_insert("energy", frame=TH1 + 1); interp(l_.data, "LINEAR")
# shar
bT = empty("bal_lt", tuple(C3 + Vector((0, 0, 0.6))))
area("b_key", tuple(C3 + Vector((-1.4, -2.2, 1.9))), 1.4, (1.0, 0.95, 0.9), lights_for(rng("balloon"), 380.0), target=bT)
area("b_rim", tuple(C3 + Vector((1.6, 0.6, 1.0))), 1.0, (0.7, 0.85, 1.0), lights_for(rng("balloon"), 240.0), target=bT)
# operatsiya
area("or_ceil_l", tuple(ORC + Vector((0, -0.6, 3.1))), 2.0, (0.75, 0.88, 1.0), lights_for(rng("surgery"), 140.0), target=empty("or_t", tuple(ORC + Vector((0, -0.4, 1.0)))))
area("tray_l", tuple(TRAY + Vector((0.25, -0.35, 0.5))), 0.3, (1.0, 0.95, 0.9), lights_for(rng("surgery"), 9.0), target=scal)
ol = area("or_lamp_l", tuple(LAMP + Vector((0, 0, -0.08))), 0.7, (1.0, 0.97, 0.92), [(1, 0)], target=empty("or_t2", tuple(ORC + Vector((0, -0.3, 1.0)))))
for f, v in ((F_LAMP - 1, 0), (F_LAMP, 250), (F_LAMP + 3, 60), (F_LAMP + 6, 420), (END, 700)): ol.data.energy = v; ol.data.keyframe_insert("energy", frame=f)

# tovush effektlari uchun voqea kadrlari
if os.environ.get("DBG"):
    for f in map(int, os.environ["DBG"].split(",")):
        sc.frame_set(f); print("DBG", f, [(b_, tuple(round(v, 2) for v in bw(b_))) for b_ in ("Hips", "Head", "LeftFoot", "RightHand")], tuple(round(v, 2) for v in broot.location))
if os.environ.get("EVENTS"):
    import json
    json.dump({"shots": SHOTS, "sag": F_SAG, "pop": F_POP, "burst": F_BURST, "bal": F_BAL, "puffs": PUFFS, "drops": DROPS, "gauge": G0, "gauge_max": T(6.7),
               "lamp": F_LAMP, "hook_in": 20, "timer_end": TM1 - 8, "seat_arrow": ST0 + 40, "infect": IF0 + 40, "end": END}, open(os.environ["EVENTS"], "w"))

# ======================================================================
# 11) RENDER
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
