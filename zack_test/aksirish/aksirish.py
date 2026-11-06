# "Aksirishni ushlab qolsang nima bo'ladi?" — Zack D. Films uslubida 55.8 s video (1340 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, magnit/magnit.py (yordamchilar, mehmonxona, rentgen, ichak materiali).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_aksirish.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/aksirish/aksirish.py --render
# Sinov: FRAMES=20,80,240,520,940 PCT=30
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler, Quaternion
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
END = 1340
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (33, "cover"), (87, "jolt"), (147, "xlungs"), (194, "spray"), (252, "block"), (320, "pressure"),
         (396, "ears"), (425, "eyes"), (455, "throat"), (491, "street"), (574, "hold"), (612, "widen"), (652, "crack"),
         (725, "swollen"), (795, "swallow"), (848, "doctors"), (914, "tear"), (992, "air"), (1092, "bed"), (1198, "dont"),
         (1284, "elbow")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

# ---------------- yordamchilar (muzlash.py dan) ----------------
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

def path_keys(cam, pts):
    for f, p in pts: key(cam, f, loc=p)

def orbit(cam, f0, f1, center, r0, r1, a0, a1, z0, z1, step=2):
    for f in range(f0, f1 + 1, step):
        t = (f - f0) / max(1, f1 - f0); a = R(a0 + (a1 - a0) * t); rr = r0 + (r1 - r0) * t
        key(cam, f, loc=tuple(Vector(center) + Vector((rr * math.sin(a), -rr * math.cos(a), z0 + (z1 - z0) * t))))
    interp(cam, "LINEAR", "location")

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

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def val_key(m, name, f, v):
    P.mat_value(m, name, f, v)

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]

def catmull(pts, step=0.004):
    """Catmull-Rom orqali zich nuqtalar (magnit yo'li va quvur bir xil bo'lsin)"""
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

def chrome(name, tint=(0.85, 0.86, 0.9), glow=0.0, glow_col=(0.5, 0.8, 1.0)):
    m = mat(name, tint, 0.08, metal=1.0, coat=0.6)
    if glow:
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Color"].default_value = (*glow_col, 1); b.inputs["Emission Strength"].default_value = glow
    return m

def gut_material(name, hole=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; out = N["Material Output"]
    tc = N.new("ShaderNodeTexCoord"); obj = tc.outputs["Object"]
    blood = value_node(m, "blood", 1.0); pale = value_node(m, "pale", 0.0); dead_r = value_node(m, "dead_r", 0.0)
    hole_r = value_node(m, "hole_r", 0.0); xr = value_node(m, "xr", 0.0); infl = value_node(m, "infl", 0.0)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6; L.new(obj, nz.inputs[0])
    base = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], base.inputs[0])
    base.color_ramp.elements[0].color = (0.62, 0.22, 0.2, 1); base.color_ramp.elements[1].color = (0.92, 0.52, 0.45, 1)
    # tomirlar: noise (distortion) -> tor chiziq
    vn = N.new("ShaderNodeTexNoise"); vn.inputs["Scale"].default_value = 2.2; vn.inputs["Detail"].default_value = 3
    vn.inputs["Distortion"].default_value = 0.8; L.new(obj, vn.inputs[0])
    vr = N.new("ShaderNodeMapRange"); L.new(vn.outputs["Fac"], vr.inputs["Value"])
    vr.inputs["From Min"].default_value = 0.47; vr.inputs["From Max"].default_value = 0.5
    vr2 = N.new("ShaderNodeMapRange"); L.new(vn.outputs["Fac"], vr2.inputs["Value"])
    vr2.inputs["From Min"].default_value = 0.53; vr2.inputs["From Max"].default_value = 0.5
    vein = P.math_n(N, L, "MULTIPLY", vr.outputs[0], vr2.outputs[0])
    vein_b = P.math_n(N, L, "MULTIPLY", vein, blood)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(vein_b, c1.inputs["Factor"]); L.new(base.outputs[0], c1.inputs[6])
    c1.inputs[7].default_value = (0.45, 0.02, 0.03, 1)
    # kontakt (0,0,0) atrofida: oqarish, o'lim
    dist = P.math_n(N, L, "DISTANCE", obj, (0.0, 0.0, 0.0), vec=True)
    nzd = N.new("ShaderNodeTexNoise"); nzd.inputs["Scale"].default_value = 6; L.new(obj, nzd.inputs[0])
    dd = P.math_n(N, L, "ADD", dist, P.math_n(N, L, "MULTIPLY", nzd.outputs["Fac"], 0.15))
    def ring(radius_sock, soft):
        mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"; L.new(dd, mr.inputs["Value"])
        L.new(P.math_n(N, L, "SUBTRACT", radius_sock, soft), mr.inputs["From Min"]); L.new(radius_sock, mr.inputs["From Max"])
        mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
        return mr.outputs[0]
    pale_mask = P.math_n(N, L, "MULTIPLY", ring(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", pale, 0.35), 0.08), 0.15), pale)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(pale_mask, c2.inputs["Factor"]); L.new(c1.outputs[2], c2.inputs[6])
    c2.inputs[7].default_value = (0.92, 0.78, 0.74, 1)
    dmask = ring(dead_r, 0.18)
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"; L.new(dmask, c3.inputs["Factor"]); L.new(c2.outputs[2], c3.inputs[6])
    dcol = N.new("ShaderNodeValToRGB"); L.new(nzd.outputs["Fac"], dcol.inputs[0])
    dcol.color_ramp.elements[0].color = (0.06, 0.015, 0.03, 1); dcol.color_ramp.elements[1].color = (0.25, 0.05, 0.12, 1)
    L.new(dcol.outputs[0], c3.inputs[7])
    L.new(c3.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Scale"].default_value = 0.03
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.25)
    L.new(P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", dmask, 0.9)), b.inputs["Coat Weight"])
    b.inputs["Coat Roughness"].default_value = 0.04
    # yallig'lanish: qizil porlash
    b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.04, 1)
    L.new(P.math_n(N, L, "MULTIPLY", infl, P.math_n(N, L, "ADD", nz.outputs["Fac"], 0.2)), b.inputs["Emission Strength"])
    # sirt bo'rtiqlari
    bn = N.new("ShaderNodeTexNoise"); bn.inputs["Scale"].default_value = 12; bn.inputs["Detail"].default_value = 8; L.new(obj, bn.inputs[0])
    bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.25; bmp.inputs["Distance"].default_value = 0.01
    L.new(P.math_n(N, L, "ADD", bn.outputs["Fac"], P.math_n(N, L, "MULTIPLY", vein, 0.6)), bmp.inputs["Height"])
    L.new(bmp.outputs[0], b.inputs["Normal"])
    shader = b.outputs[0]
    # rentgen (magnit ko'rinsin): chetlari qalin, o'rtasi shaffof
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    xa = P.math_n(N, L, "MULTIPLY", xr, P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"]))
    tr = N.new("ShaderNodeBsdfTransparent")
    mx1 = N.new("ShaderNodeMixShader"); L.new(xa, mx1.inputs[0]); L.new(shader, mx1.inputs[1]); L.new(tr.outputs[0], mx1.inputs[2])
    shader = mx1.outputs[0]
    if hole:
        hd = P.math_n(N, L, "DISTANCE", obj, tuple(HOLE_C), vec=True)
        hn = N.new("ShaderNodeTexNoise"); hn.inputs["Scale"].default_value = 30; hn.inputs["Detail"].default_value = 4; L.new(obj, hn.inputs[0])
        hdd = P.math_n(N, L, "ADD", hd, P.math_n(N, L, "MULTIPLY", hn.outputs["Fac"], 0.045))
        inside = P.math_n(N, L, "LESS_THAN", hdd, P.math_n(N, L, "ADD", hole_r, 0.02))
        rim = P.math_n(N, L, "LESS_THAN", hdd, P.math_n(N, L, "ADD", hole_r, 0.06))
        rim_s = N.new("ShaderNodeBsdfPrincipled"); rim_s.inputs["Base Color"].default_value = (0.04, 0.01, 0.01, 1)
        rim_s.inputs["Roughness"].default_value = 0.6
        mx2 = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "MULTIPLY", rim, P.math_n(N, L, "GREATER_THAN", hole_r, 0.001)), mx2.inputs[0])
        L.new(shader, mx2.inputs[1]); L.new(rim_s.outputs[0], mx2.inputs[2])
        mx3 = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "MULTIPLY", inside, P.math_n(N, L, "GREATER_THAN", hole_r, 0.001)), mx3.inputs[0])
        L.new(mx2.outputs[0], mx3.inputs[1]); L.new(tr.outputs[0], mx3.inputs[2])
        shader = mx3.outputs[0]
    L.new(shader, out.inputs["Surface"])
    return m

def pq(o, f, rot):
    """qo'shimcha (COMBINE) suyak burilishi: rot = (x, y, z) gradus, suyak mahalliy o'qlarida"""
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Euler([R(a) for a in rot]).to_quaternion(); o.keyframe_insert("rotation_quaternion", frame=f)

def spray(name, origin, f0, n, direction, speed, spread, m, life=40, rmin=0.0015, rmax=0.004, grav=0.0006, seed=1,
          max_dist=None, ranges=None):
    """tomchilar buluti: origin dan f0 da otiladi (dunyo koordinatasi)"""
    rnd = random.Random(seed); root = empty(name, (0, 0, 0)); d0 = Vector(direction).normalized(); out = []
    for i in range(n):
        s_ = sphere(f"{name}{i}", rnd.uniform(rmin, rmax), (0, 0, 0), m, sub=1, parent=root, world=False)
        s_.scale = (1, 1, 1)
        v = (d0 + Vector((rnd.uniform(-spread, spread), rnd.uniform(-spread, spread), rnd.uniform(-spread, spread) * 0.7))).normalized()
        v *= speed * rnd.uniform(0.45, 1.25)
        t0 = f0 + rnd.randint(0, 5)
        key(s_, 1, loc=tuple(origin), scale=(0.001,) * 3); key(s_, t0 - 1, loc=tuple(origin), scale=(0.001,) * 3)
        dist_max = (max_dist or 99) * rnd.uniform(0.7, 1.0)
        for k in range(0, life, 2):
            dk = min(1.0, k / 5.0)
            trav = v * k * (1.0 - 0.012 * k)            # havo qarshiligi
            if trav.length > dist_max: trav = trav.normalized() * dist_max
            p = Vector(origin) + trav + Vector((0, 0, -grav * k * k))
            sc_ = dk * (1.0 if k < life * 0.6 else max(0.001, 1 - (k - life * 0.6) / (life * 0.4)))
            key(s_, t0 + k, loc=tuple(p), scale=(max(sc_, 0.001),) * 3)
        interp(s_, "LINEAR")
        out.append(s_)
    if ranges: vis(root, ranges)
    return root

ROOM_SHOTS = rng("hook", "cover", "jolt", "dont", "elbow")
X_SHOTS = rng("xlungs", "spray", "block", "pressure", "ears", "eyes", "throat", "crack", "swallow", "air")
STREET_SHOTS = rng("street", "hold", "widen", "swollen")
HOSP_SHOTS = rng("doctors", "bed")
TH_SHOTS = rng("tear")

# ======================================================================
# 1) MEHMONXONA (0,0,0) — magnit.py dan
# ======================================================================
room = empty("room", (0, 0, 0))
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.4, tint=(0.82, 0.88, 0.93))
plane("floor", (7, 7), (0, 0.5, 0), floor_m, parent=room)
plane("wall_back", (7, 3), (0, 2.25, 1.5), wall_m, rot=(90, 0, 0), parent=room)
plane("wall_left", (7, 3), (-2.4, 0.5, 1.5), wall_m, rot=(90, 0, 90), parent=room)
plane("wall_right", (7, 3), (2.6, 0.5, 1.5), wall_m, rot=(90, 0, -90), parent=room)
plane("ceiling", (7, 7), (0, 0.5, 2.8), mat("ceil", (0.9, 0.9, 0.88), 0.8), rot=(180, 0, 0), parent=room)
box("skirting", (7, 0.02, 0.08), (0, 2.24, 0.04), mat("skirt", (0.95, 0.95, 0.93), 0.4), parent=room)
win_glass = mat("win_sky", (0.75, 0.85, 1.0), 0.0, emit=3.0)
plane("window", (1.4, 1.5), (-2.39, 0.6, 1.5), win_glass, rot=(90, 0, 90), parent=room)
frame_m = mat("win_frame", (0.95, 0.95, 0.95), 0.35)
for dz in (-0.76, 0.76):
    box("wframe", (0.08, 1.5, 0.06), (-2.36, 0.6, 1.5 + dz), frame_m, parent=room)
for dy in (-0.73, 0.0, 0.73):
    box("wframe", (0.08, 0.06, 1.55), (-2.36, 0.6 + dy, 1.5), frame_m, parent=room)
rug_m = bpy.data.materials.new("rug"); rug_m.use_nodes = True
N = rug_m.node_tree.nodes; L = rug_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 300; L.new(tc.outputs["Object"], nz.inputs[0])
wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; L.new(tc.outputs["Object"], wv.inputs[0])
cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.12, 0.2, 0.42, 1); cr.color_ramp.elements[1].color = (0.8, 0.72, 0.55, 1)
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
plane("rug", (2.6, 1.8), (0.1, 0.5, 0.004), rug_m, parent=room)
sofaR = empty("sofaR", (0, 1.85, 0), room); import_gltf(PH + "Sofa_01/Sofa_01.gltf", sofaR)
sofaR.scale = (1.15, 1.15, 1.0)
tableR = empty("tableR", (0.15, 1.05, 0), room); tableR.rotation_euler = (0, 0, R(90))
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", tableR)
plantR = empty("plantR", (-1.55, 1.85, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR)
plantR2 = empty("plantR2", (1.6, 1.95, 0), room); plantR2.scale = (0.8, 0.8, 0.8); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR2)
picR = empty("picR", (0.0, 2.24, 1.55), room); picR.scale = (1.6, 1.6, 1.6); import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR)
picR2 = empty("picR2", (-0.9, 2.24, 1.35), room); import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR2)
lamp_m = mat("lamp_shade", (1.0, 0.85, 0.6), 0.6, emit=2.5, emit_col=(1.0, 0.75, 0.45))
cyl("lamp_pole", 0.015, 1.5, (1.05, 1.9, 0.75), mat("lamp_pole_m", (0.1, 0.1, 0.1), 0.3, metal=0.8), parent=room)
cyl("lamp_shade", 0.18, 0.28, (1.05, 1.9, 1.55), lamp_m, parent=room)
cyl("lamp_base", 0.14, 0.03, (1.05, 1.9, 0.015), mat("lamp_base_m", (0.1, 0.1, 0.1), 0.3, metal=0.8), parent=room)
# salfetka qutisi (stol ustida)
box("tissue_box", (0.24, 0.12, 0.1), (0.35, 1.0, 0.445), mat("tissue_b", (0.25, 0.55, 0.75), 0.5), parent=room)
box("tissue", (0.07, 0.05, 0.06), (0.35, 1.0, 0.52), mat("tissue_w", (0.95, 0.95, 0.95), 0.9, sss=0.3), rot=(0, 0, 15), parent=room)

# ======================================================================
# 2) BRIAN (yigit)
# ======================================================================
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
broot, bri, bmeshes = mc.load_character("bri", "Brian.fbx"); sc.render.fps = 24
soften(bmeshes)

ROOMP = (0.0, 0.3, 0.0)
HY = float(os.environ.get("HY", -0.03)); HZ = float(os.environ.get("HZ", 0.025))   # o'lchangan: burun uchi Head (0, 0.052, 0.15)
def hp(x, y, z): return (x, y + HY, z + HZ)
ST0 = Vector((0, -60, 0))                       # ko'cha
HOSP = Vector((40, 0, 0))                       # kasalxona xonasi
BED = HOSP + Vector((1.2, 1.0, 0))              # karavot markazi
BED_Z = 0.62
WALK_X0, WALK_X1 = -4.2, -0.2                   # ko'chada yurish (x)
STR_Y = ST0.y + 0.9                              # trotuar (yigit yuradigan chiziq)
def place(root, f, loc, rot=0.0, scale=1.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
    for p in ("location", "rotation_euler", "scale"): root.keyframe_insert(p, frame=f)
STR0, STR1 = S["street"]
place(broot, 1, ROOMP)
place(broot, STR0, (WALK_X0, STR_Y, 0.14), rot=90)
place(broot, STR1 - 6, (WALK_X1, STR_Y, 0.14), rot=90)
place(broot, S["doctors"][0], ROOMP)                       # rentgen (havo) kadrlari uchun xonada
place(broot, S["bed"][0], tuple(BED + Vector((0, 0, BED_Z))), rot=0)
place(broot, S["dont"][0], ROOMP)
for fc in fcurves(broot):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if STR0 <= k.co.x < STR1 - 6 else "CONSTANT"

def strip(arm, act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
mc.add_strip(bri, A_("Idle_14.fbx"), -40, blend=0, repeat=7.0)
strip(bri, A_("Walking.fbx"), STR0 - 10, blend=0, bout=8, repeat=4.0 * 0 + (STR1 - STR0 + 10) / 30.0)
strip(bri, A_("Laying_Idle.fbx"), S["bed"][0] - 4, blend=0, bout=0, repeat=(S["bed"][1] - S["bed"][0] + 6) / 52.0)
headE = child_of_bone("bri_head", bri, "Head")
neckE = child_of_bone("bri_neck", bri, "Neck")
chestE = child_of_bone("bri_chest", bri, "Spine2")
faceT = empty("faceT", (0, 0.07, 0.11), headE)
mouthE = empty("mouthE", (0, 0.012, 0.15), headE)

# ---- aksirish: qo'shimcha suyak burilishlari (aktiv harakat, COMBINE) ----
B = {n: bri.pose.bones["mixamorig:" + n] for n in ("Spine", "Spine1", "Spine2", "Neck", "Head")}
SX = float(os.environ.get("SNEEZE_SIGN", 1.0))       # +X = oldinga egilish (sinovda tekshiriladi)
def bend(f, sp, nk, hd):
    pq(B["Spine1"], f, (SX * sp * 0.5, 0, 0)); pq(B["Spine2"], f, (SX * sp * 0.5, 0, 0))
    pq(B["Neck"], f, (SX * nk, 0, 0)); pq(B["Head"], f, (SX * hd, 0, 0))
def sneeze(f_peak, inhale=18, back=12, fwd=16, hold=6, rec=12, suppressed=False):
    """inhale: orqaga, keyin keskin oldinga (ACHOO)"""
    a = f_peak - inhale
    bend(a, 0, 0, 0)
    bend(f_peak - 2, -back * 0.4, -back * 0.5, -back)
    if suppressed:
        bend(f_peak, fwd * 0.25, fwd * 0.2, fwd * 0.5); bend(f_peak + 2, -3, -2, -6); bend(f_peak + 5, 4, 3, 6)
        bend(f_peak + hold + 4, 2, 2, 3); bend(f_peak + hold + rec + 4, 0, 0, 0)
    else:
        bend(f_peak + 3, fwd * 0.7, fwd * 0.6, fwd); bend(f_peak + 3 + hold, fwd * 0.55, fwd * 0.5, fwd * 0.8)
        bend(f_peak + 3 + hold + rec, 0, 0, 0)
bend(1, 0, 0, 0)
SNZ_JOLT = 97                                          # "qolsang" — bostirilgan aksirish (silkinish)
SNZ_SPRAY = 200                                        # oddiy aksirish (100 km/soat)
SNZ_BLOCK = 292                                        # qo'l bilan yopilgan aksirish
SNZ_QIRS = 662                                         # "qirs"
SNZ_ELBOW = 1316                                       # tirsakka
sneeze(SNZ_JOLT, inhale=60, back=14, suppressed=True)
sneeze(SNZ_SPRAY, inhale=40, back=16, fwd=22)
sneeze(SNZ_BLOCK, inhale=30, back=10, suppressed=True)
sneeze(SNZ_QIRS, inhale=36, back=10, suppressed=True)
sneeze(SNZ_ELBOW, inhale=28, back=14, fwd=18, hold=8)
bend(S["dont"][0] + 20, 0, 0, 0); bend(S["dont"][0] + 40, -4, -5, -9); bend(S["dont"][0] + 64, -4, -5, -9); bend(S["dont"][0] + 80, 0, 0, 0)
# qo'shimcha harakatni NLA ga (COMBINE) o'tkazamiz; aktiv harakat constraint ta'sirlari uchun bo'sh qoladi
ov = bri.animation_data.action; ov.name = "sneeze_overlay"; ov.use_fake_user = True
bri.animation_data.action = None
_tr = bri.animation_data.nla_tracks.new(); _tr.name = "sneeze_overlay"
_st = _tr.strips.new("sneeze_overlay", 1, ov)
if hasattr(_st, "action_slot") and ov.slots: _st.action_slot = ov.slots[0]
_st.blend_type = "COMBINE"; _st.extrapolation = "HOLD"; _st.blend_in = _st.blend_out = 0

# ---- qo'llar: IK (burun-og'izni yopish, tomoqni ushlash, tirsak) ----
def arm_ik(arm, side, name, pole=None):
    tgt = empty(f"{name}_{side}_ik")
    c = arm.pose.bones[f"mixamorig:{side}ForeArm"].constraints.new("IK")
    c.target = tgt; c.use_tail = True; c.chain_count = 2; c.influence = 0.0
    if pole is not None:
        c.pole_target = pole; c.pole_angle = R(float(os.environ.get("POLE_ANG", -90)))
    return tgt, c
def key_inf(cs, pairs):
    for c in cs:
        for f, v in pairs: c.influence = v; c.keyframe_insert("influence", frame=f)
HX = float(os.environ.get("HX", 1.0))
# yuzni yopish nishonlari (Head fazosi: X chap, Y tepa, Z old)
coverR = empty("coverR", (-0.06 * HX, -0.075, 0.2), headE)       # o'ng bilak: burun ostida
coverL = empty("coverL", (0.065 * HX, -0.1, 0.18), headE)     # chap bilak: og'iz ostida
aimR = empty("aimR", (0.04 * HX, 0.08, 0.17), headE); aimL = empty("aimL", (-0.07 * HX, 0.0, 0.17), headE)
palmC = empty("palmC", (0, 0.03, -0.02), headE)
# tomoqni ushlash (Neck fazosi)
throatR = empty("throatR", (-0.06 * HX, -0.02, 0.13), neckE); throatL = empty("throatL", (0.06 * HX, -0.04, 0.12), neckE)
taimR = empty("taimR", (0.03 * HX, 0.06, 0.09), neckE); taimL = empty("taimL", (-0.03 * HX, 0.04, 0.09), neckE)
palmN = empty("palmN", (0, 0.05, 0.0), neckE)
# tirsak: o'ng bilak chap yelka tomonda, yuz oldida
elbR = empty("elbR", (0.16 * HX, 0.03, 0.12), headE); eaimR = empty("eaimR", (0.3 * HX, 0.06, 0.05), headE)
poleR = empty("poleR", (-0.25 * HX, -0.25, 0.5), headE)
RT_, RIK = arm_ik(bri, "Right", "bri"); LT_, LIK = arm_ik(bri, "Left", "bri")
def follow(tgt, src_list):
    """IK nishoni bir nechta bo'sh ob'ektdan birini kuzatadi (COPY_LOCATION, ta'sir kalitlanadi)"""
    cs = []
    for s_ in src_list:
        c = tgt.constraints.new("COPY_LOCATION"); c.target = s_; c.influence = 0.0; cs.append(c)
    return cs
RC = follow(RT_, [coverR, throatR, elbR]); LC = follow(LT_, [coverL, throatL])
# Damped/Locked track nishoni dinamik bo'lolmaydi (bitta target) — har rejim uchun alohida constraint juftligi
def hand_set(side, aims, palms):
    hb = bri.pose.bones[f"mixamorig:{side}Hand"]
    out = []
    for a_, p_ in zip(aims, palms):
        d = hb.constraints.new("DAMPED_TRACK"); d.target = a_; d.track_axis = "TRACK_Y"; d.influence = 0.0
        l = hb.constraints.new("LOCKED_TRACK"); l.target = p_; l.track_axis = "TRACK_Z" if side == "Right" else "TRACK_NEGATIVE_Z"
        l.lock_axis = "LOCK_Y"; l.influence = 0.0
        out.append((d, l))
    return out
RH = hand_set("Right", [aimR, taimR, eaimR], [palmC, palmN, palmC]); LH = hand_set("Left", [aimL, taimL], [palmC, palmN])
def drive(cs, ik, hs, plan, ramp=9):
    """plan: [(kadr, rejim)] — rejim 0: qo'l pastda, 1..n: nishon. Nishon (COPY_LOCATION) qo'l ko'tarilishidan oldin
    joyida turadi, faqat IK ta'siri silliq o'zgaradi."""
    allc = list(cs) + [ik] + [c for pair in hs for c in pair]
    def put(f, on, tgt):
        for i, c in enumerate(cs): c.influence = 1.0 if tgt == i + 1 else 0.0; c.keyframe_insert("influence", frame=f)
        for i, (d, l) in enumerate(hs):
            for c in (d, l): c.influence = on if tgt == i + 1 else 0.0; c.keyframe_insert("influence", frame=f)
        ik.influence = on; ik.keyframe_insert("influence", frame=f)
    put(1, 0.0, 1); prev = 0
    for f, mode in plan:
        if mode == prev: continue
        if prev and mode:
            put(f - 1, 1.0, prev); put(f, 1.0, mode)
        elif mode:
            put(f - ramp, 0.0, mode); put(f, 1.0, mode)
        else:
            put(f - ramp, 1.0, prev); put(f, 0.0, prev)
        prev = mode
    for c in [x for x in allc]:
        pass
    return allc
HOLD0 = S["hold"][0] + 14
R_PLAN = [(45, 1), (S["xlungs"][0], 0), (S["block"][0] + 30, 1), (S["throat"][1] + 1, 0), (HOLD0, 1), (S["crack"][1] - 4, 2),
          (S["swallow"][1] + 1, 0), (S["dont"][0] + 40, 1), (S["dont"][0] + 62, 0)]
L_PLAN = [(48, 1), (S["xlungs"][0], 0), (S["block"][0] + 32, 1), (S["throat"][1] + 1, 0), (HOLD0 + 3, 1), (S["crack"][1] - 2, 2),
          (S["swallow"][1] + 1, 0), (S["dont"][0] + 43, 1), (S["dont"][0] + 62, 0)]
drive(RC, RIK, RH, R_PLAN); drive(LC, LIK, LH, L_PLAN)
# tirsak: alohida IK (pole bilan), o'ng bilak yuz oldidan chap tomonga o'tadi
_fa = bri.pose.bones["mixamorig:RightForeArm"]
RIK2 = _fa.constraints.new("IK"); RIK2.target = elbR; RIK2.use_tail = True; RIK2.chain_count = 2
RIK2.pole_target = poleR; RIK2.pole_angle = R(float(os.environ.get("POLE_ANG", 90)))
ED, EL_ = RH[2]
EUP = S["elbow"][0] + 14
key_inf([RIK2, ED, EL_], [(1, 0.0), (EUP - 12, 0.0), (EUP, 1.0), (END, 1.0)])

# ======================================================================
# 3) RENTGEN: shaffof Brian + nafas yo'llari (Head / Spine2 fazosi: X chap, Y tepa, Z old)
# ======================================================================
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.2, base=0.012)
ghosts = []
for o in bmeshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, X_SHOTS, recursive=False)
real_ranges = [(1, S["xlungs"][0] - 1), (S["street"][0], S["crack"][0] - 1), (S["swollen"][0], S["swallow"][0] - 1),
               (S["doctors"][0], S["air"][0] - 1), (S["bed"][0], END)]
for o in bmeshes: vis(o, real_ranges, recursive=False)
def organ_mat(name, col, emit=0.35, alpha_mix=0.5):
    m = mat(name, col, 0.3, sss=0.4, sss_scale=0.005, coat=0.8, emit=emit)
    nm = m.node_tree.nodes; b = nm["Principled BSDF"]
    lw = nm.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    mm_ = nm.new("ShaderNodeMath"); mm_.operation = "MULTIPLY"; mm_.inputs[1].default_value = emit * 2.5
    m.node_tree.links.new(lw.outputs["Facing"], mm_.inputs[0]); m.node_tree.links.new(mm_.outputs[0], b.inputs["Emission Strength"])
    tr = nm.new("ShaderNodeBsdfTransparent"); mx = nm.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha_mix
    m.node_tree.links.new(b.outputs[0], mx.inputs[1]); m.node_tree.links.new(tr.outputs[0], mx.inputs[2])
    m.node_tree.links.new(mx.outputs[0], nm["Material Output"].inputs["Surface"])
    return m
def red_mix(m, col=(1.0, 0.08, 0.03)):
    """'infl' qiymati (0..1) bilan material qizaradi va yonadi"""
    nm = m.node_tree.nodes; b = nm["Principled BSDF"]; v = value_node(m, "infl", 0.0)
    mx = nm.new("ShaderNodeMix"); mx.data_type = "RGBA"; m.node_tree.links.new(v, mx.inputs["Factor"])
    mx.inputs[6].default_value = b.inputs["Base Color"].default_value[:]; mx.inputs[7].default_value = (*col, 1)
    m.node_tree.links.new(mx.outputs[2], b.inputs["Base Color"]); m.node_tree.links.new(mx.outputs[2], b.inputs["Emission Color"])
    return m
ax = empty("air_head", (0, 0, 0), headE); axc = empty("air_chest", (0, 0, 0), chestE)
lung_m = red_mix(organ_mat("lung_m", (0.95, 0.55, 0.6), emit=0.3))
airw_m = red_mix(organ_mat("airway_m", (0.95, 0.62, 0.62), emit=0.4, alpha_mix=0.35))
eye_m = organ_mat("eye_m", (0.95, 0.95, 0.97), emit=0.25, alpha_mix=0.3)
drum_m = red_mix(organ_mat("drum_m", (0.98, 0.8, 0.7), emit=0.5, alpha_mix=0.2))
# o'pkalar + bronxlar + traxeya (ko'krak)
lungs = [sphere(f"lung{i}", 1.0, (0, 0, 0), lung_m, sub=4, parent=axc, world=False) for i in range(2)]
for i, l_ in enumerate(lungs):
    sg = 1 if i == 0 else -1
    l_.location = (sg * 0.075, 0.07, 0.015); l_.scale = (0.062, 0.115, 0.06)
TRACH = [(0, 0.27, 0.035), (0, 0.2, 0.035), (0, 0.14, 0.03), (0, 0.1, 0.025)]
trach = P.tube("trachea", catmull(TRACH, 0.01), 0.0085, airw_m, axc)
for sg in (1, -1):
    P.tube(f"bronch{sg}", catmull([(0, 0.1, 0.025), (sg * 0.03, 0.085, 0.022), (sg * 0.06, 0.07, 0.018)], 0.01), 0.006, airw_m, axc)
# halqum, burun bo'shlig'i, og'iz, quloq yo'llari, ko'zlar (bosh)
PHAR = [hp(0, -0.11, 0.03), hp(0, -0.06, 0.02), hp(0, 0.0, 0.015), hp(0, 0.045, 0.012), hp(0, 0.075, 0.02)]
NASAL = [hp(0, 0.075, 0.02), hp(0, 0.088, 0.055), hp(0, 0.086, 0.09), hp(0, 0.072, 0.118)]
ORAL = [hp(0, 0.0, 0.015), hp(0, 0.012, 0.06), hp(0, 0.03, 0.095), hp(0, 0.035, 0.118)]
phar = P.tube("pharynx", catmull(PHAR, 0.006), 0.0095, airw_m, ax)
nasal = P.tube("nasal", catmull(NASAL, 0.006), 0.008, airw_m, ax)
oral = P.tube("oral", catmull(ORAL, 0.006), 0.009, airw_m, ax)
EARP = {}; EYEP = {}
for sg in (1, -1):
    EARP[sg] = [hp(0, 0.075, 0.02), hp(sg * 0.03, 0.08, 0.012), hp(sg * 0.055, 0.085, 0.004), hp(sg * 0.068, 0.088, 0.0)]
    P.tube(f"eust{sg}", catmull(EARP[sg], 0.005), 0.0035, airw_m, ax)
    EYEP[sg] = [hp(0, 0.088, 0.06), hp(sg * 0.014, 0.1, 0.07), hp(sg * 0.026, 0.11, 0.074)]
    P.tube(f"tear{sg}", catmull(EYEP[sg], 0.005), 0.0028, airw_m, ax)
drums = []; eyes = []
for sg in (1, -1):
    d_ = cyl(f"drum{sg}", 0.008, 0.002, hp(sg * 0.07, 0.088, 0.0), drum_m, rot=(0, 90, 0), parent=ax); d_.parent = ax
    d_.location = hp(sg * 0.07, 0.088, 0.0); d_.matrix_parent_inverse = Matrix.Identity(4); drums.append(d_)
    e_ = sphere(f"eye{sg}", 0.0125, (0, 0, 0), eye_m, sub=3, parent=ax, world=False); e_.location = hp(sg * 0.032, 0.112, 0.082); eyes.append(e_)
# havo oqimi impulslari (egri bo'ylab yuradigan yorug'lik)
def pulse_tube(name, pts, r, col=(0.4, 0.8, 1.0), parent=ax, width=0.12):
    m = P.pulse_material(name + "_m", col, base_emit=0.0, pulse_col=col, width=width)
    nt = m.node_tree; b_ = nt.nodes["Principled BSDF"]; src_ = b_.inputs["Emission Strength"].links[0].from_socket
    fa = P.math_n(nt.nodes, nt.links, "MULTIPLY", src_, 0.25, clamp=True)
    tr_ = nt.nodes.new("ShaderNodeBsdfTransparent"); mx_ = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fa, mx_.inputs[0]); nt.links.new(tr_.outputs[0], mx_.inputs[1]); nt.links.new(b_.outputs[0], mx_.inputs[2])
    nt.links.new(mx_.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    t = P.tube(name, catmull(pts, 0.005), r, m, parent); return t, m
def run_pulse(m, f0, f1, glow_after=0.0, stay=False):
    val_key(m, "pos", 1, -0.3); val_key(m, "pos", f0, -0.3); val_key(m, "pos", f1, 1.3 if not stay else 0.98)
    val_key(m, "glow", 1, 0.0)
    if glow_after: val_key(m, "glow", f1 - 2, 0.0); val_key(m, "glow", f1 + 4, glow_after)
    else: val_key(m, "glow", f1 - 1, 0.0); val_key(m, "glow", f1 + 3, -1.5)          # iz (trail) o'chadi
pT, pTm = pulse_tube("p_trach", list(reversed(TRACH)) + [], 0.0105, parent=axc)
pH, pHm = pulse_tube("p_phar", PHAR + [], 0.0115)
pO, pOm = pulse_tube("p_oral", ORAL, 0.011)
pN, pNm = pulse_tube("p_nasal", NASAL, 0.0098)
pE = {sg: pulse_tube(f"p_ear{sg}", EARP[sg], 0.0045, col=(1.0, 0.35, 0.12)) for sg in (1, -1)}
pY = {sg: pulse_tube(f"p_eye{sg}", EYEP[sg], 0.0038, col=(1.0, 0.35, 0.12)) for sg in (1, -1)}
pTh, pThm = pulse_tube("p_throat", list(reversed(PHAR)), 0.012, col=(1.0, 0.3, 0.1))
XL0, XL1 = S["xlungs"]; SP0, SP1 = S["spray"]; BL0, BL1 = S["block"]; PR0, PR1 = S["pressure"]
EA0, EA1 = S["ears"]; EY0, EY1 = S["eyes"]; TH0, TH1 = S["throat"]; CK0, CK1 = S["crack"]; SW0, SW1 = S["swallow"]; AI0, AI1 = S["air"]
# 4-5: oddiy aksirish: o'pka -> traxeya -> halqum -> og'iz/burun
for (f, v) in ((1, 0.0), (XL0 + 5, 0.0), (SNZ_SPRAY - 6, 0.0)):
    pass
run_pulse(pTm, XL0 + 14, SNZ_SPRAY - 6)
run_pulse(pHm, SNZ_SPRAY - 10, SNZ_SPRAY - 1)
run_pulse(pOm, SNZ_SPRAY - 3, SNZ_SPRAY + 4); run_pulse(pNm, SNZ_SPRAY - 3, SNZ_SPRAY + 4)
# 6: yopilgan aksirish — qayta impuls, og'izda to'xtaydi
for m_, a_, b_ in ((pTm, BL0 + 26, SNZ_BLOCK - 7), (pHm, SNZ_BLOCK - 8, SNZ_BLOCK - 1)):
    val_key(m_, "pos", a_ - 1, -0.3); val_key(m_, "pos", a_, -0.3); val_key(m_, "pos", b_, 1.3)
for m_ in (pOm, pNm):
    val_key(m_, "pos", SNZ_BLOCK - 2, -0.3); val_key(m_, "pos", SNZ_BLOCK + 3, 0.92)
    val_key(m_, "pos", SNZ_BLOCK + 8, 0.45); val_key(m_, "pos", PR0, 0.6)
    val_key(m_, "glow", SNZ_BLOCK + 1, 0.0); val_key(m_, "glow", SNZ_BLOCK + 4, 4.0); val_key(m_, "glow", SNZ_BLOCK + 14, -0.7)
    val_key(m_, "glow", TH1, -0.7); val_key(m_, "glow", TH1 + 1, 0.0); val_key(m_, "pos", TH1 + 1, -0.3)
# 7: bosim to'plami (halqum ichida)
press_m = mat("press_m", (0.5, 0.8, 1.0), emit=0.0, alpha=0.35)
pb_ = press_m.node_tree.nodes["Principled BSDF"]
press = sphere("pressure", 0.018, (0, 0, 0), press_m, sub=3, parent=ax, world=False); press.location = hp(0, 0.05, 0.03)
for f, sz, e, col in ((1, 0.2, 0.0, (0.5, 0.8, 1.0)), (SNZ_BLOCK, 0.2, 0.0, (0.5, 0.8, 1.0)), (SNZ_BLOCK + 4, 0.8, 8.0, (0.6, 0.85, 1.0)),
                      (PR0, 0.9, 6.0, (0.6, 0.85, 1.0)), (PR1, 1.5, 14.0, (1.0, 0.15, 0.05)), (TH1, 1.6, 14.0, (1.0, 0.15, 0.05)),
                      (TH1 + 1, 0.1, 0.0, (1.0, 0.15, 0.05))):
    key(press, f, scale=(sz, sz * 1.3, sz))
    pb_.inputs["Emission Strength"].default_value = e; pb_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    pb_.inputs["Emission Color"].default_value = (*col, 1); pb_.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
    pb_.inputs["Base Color"].default_value = (*col, 1); pb_.inputs["Base Color"].keyframe_insert("default_value", frame=f)
for f in range(PR0, TH1, 8):                         # pulsatsiya
    s_ = 1.0 + 0.35 * min(1.0, (f - PR0) / (PR1 - PR0)) + 0.4 * ((f - PR0) / (TH1 - PR0))
    key(press, f, scale=(s_, s_ * 1.3, s_)); key(press, f + 4, scale=(s_ * 1.18, s_ * 1.45, s_ * 1.18))
vis(press, rng("block", "pressure", "ears", "eyes", "throat"), recursive=False)
# 8-10: quloq, ko'z, tomoq
for sg in (1, -1):
    run_pulse(pE[sg][1], EA0 + 2, EA0 + 14, glow_after=3.0); val_key(pE[sg][1], "glow", EY0 + 4, 3.0); val_key(pE[sg][1], "glow", TH1 + 1, 0.0)
    run_pulse(pY[sg][1], EY0 + 2, EY0 + 14, glow_after=3.0); val_key(pY[sg][1], "glow", TH1 + 1, 0.0)
for i, d_ in enumerate(drums):
    for f, sx in ((1, 1.0), (EA0 + 13, 1.0), (EA0 + 17, 4.0), (EA0 + 21, 3.0), (EA1, 3.4), (TH1 + 1, 1.0)):
        key(d_, f, scale=(1.0, 1.0, sx))
for e_ in eyes:
    for f, s_ in ((1, 1.0), (EY0 + 13, 1.0), (EY0 + 18, 1.25), (EY1, 1.2), (TH1 + 1, 1.0)): key(e_, f, scale=(s_,) * 3)
    loc0 = Vector(e_.location)
    for f, dz in ((1, 0.0), (EY0 + 13, 0.0), (EY0 + 18, 0.006), (EY1, 0.005), (TH1 + 1, 0.0)): key(e_, f, loc=tuple(loc0 + Vector((0, 0, dz))))
val_key(drum_m, "infl", 1, 0.0); val_key(drum_m, "infl", EA0 + 14, 0.0); val_key(drum_m, "infl", EA0 + 18, 1.0); val_key(drum_m, "infl", TH1 + 1, 0.0)
run_pulse(pThm, TH0 + 4, TH0 + 18, glow_after=2.5); val_key(pThm, "glow", TH1 + 1, 0.0)
val_key(airw_m, "infl", 1, 0.0); val_key(airw_m, "infl", TH0 + 10, 0.0); val_key(airw_m, "infl", TH1, 0.5); val_key(airw_m, "infl", TH1 + 1, 0.0)
val_key(airw_m, "infl", CK0 + 8, 0.0); val_key(airw_m, "infl", SNZ_QIRS + 2, 0.45); val_key(airw_m, "infl", SW1, 0.7)
# 14: "qirs" — halqum devorida yoriq (yorug' qizil chiziq)
crack_m = mat("crack_m", (1.0, 0.1, 0.03), 0.4, emit=0.0, emit_col=(1.0, 0.12, 0.03))
cb_ = crack_m.node_tree.nodes["Principled BSDF"]
CRACK = Vector(hp(0.0075, -0.035, 0.022))
rk = random.Random(4); cpts = []
for i in range(9):
    t = i / 8; cpts.append(tuple(Vector((0.004 * math.sin(i * 2.7) + rk.uniform(-0.0015, 0.0015), -0.02 + 0.04 * t, 0.003 * math.cos(i * 1.9)))))
crack = P.tube("crack", cpts, 0.0016, crack_m, ax)
for f, sc_, e in ((1, 0.0, 0.0), (SNZ_QIRS - 1, 0.0, 0.0), (SNZ_QIRS + 1, 1.0, 40.0), (SNZ_QIRS + 6, 1.0, 12.0),
                  (CK1, 1.0, 10.0), (SW0, 1.0, 10.0), (SW0 + 16, 1.0, 30.0), (SW0 + 24, 1.0, 12.0), (AI0, 1.0, 10.0)):
    key(crack, f, scale=(1, max(sc_, 0.001), 1))
    cb_.inputs["Emission Strength"].default_value = e; cb_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
crack.location = CRACK
# 16: yutinish to'lqini
pSw, pSwm = pulse_tube("p_swallow", ORAL[::-1][:2] + [hp(0, 0.0, 0.015)] + PHAR[::-1][2:], 0.0125, col=(1.0, 0.45, 0.2), width=0.18)
run_pulse(pSwm, SW0 + 4, SW0 + 24)
# 19: havo pufakchalari bo'yin va ko'krakka tarqaladi
bub_m = mat("bub_m", (0.6, 0.85, 1.0), 0.1, emit=3.0, alpha=0.8, emit_col=(0.55, 0.85, 1.0))
rbu = random.Random(11); bubs = empty("bubbles", (0, 0, 0))
for i in range(150):
    if i < 60:                                       # bo'yin (Head fazosi)
        par_, p = ax, Vector(hp(rbu.uniform(-0.05, 0.05), rbu.uniform(-0.15, 0.0), rbu.uniform(-0.03, 0.06)))
        src = CRACK
    else:                                            # ko'krak (Spine2 fazosi)
        par_, p = axc, Vector((rbu.uniform(-0.13, 0.13), rbu.uniform(0.02, 0.26), rbu.uniform(0.0, 0.09)))
        src = Vector((0, 0.3, 0.04))
    s_ = sphere(f"bub{i}", rbu.uniform(0.003, 0.008), (0, 0, 0), bub_m, sub=2, parent=par_, world=False)
    d = (p - src).length; t0 = AI0 + 6 + int(d * (420 if i < 60 else 260)) + rbu.randint(0, 6)
    key(s_, 1, loc=tuple(src), scale=(0.001,) * 3); key(s_, min(t0, AI1 - 6), loc=tuple(src), scale=(0.001,) * 3)
    key(s_, min(t0, AI1 - 6) + 10, loc=tuple(p), scale=(1, 1, 1))
    vis(s_, rng("air"), recursive=False)
vis(ax, X_SHOTS); vis(axc, X_SHOTS)
for o in (crack,): vis(o, rng("crack", "swallow", "air"), recursive=False)
for t_, m_ in ((pSw, None),): vis(t_, rng("swallow"), recursive=False)
for d_ in drums: pass
# 5: aksirish tomchilari (havo oqimi)
drop_m = mat("drop_m", (0.75, 0.9, 1.0), 0.05, emit=2.5, alpha=0.85, emit_col=(0.6, 0.85, 1.0))
sc.frame_set(SNZ_SPRAY + 2); mw = mouthE.matrix_world.translation.copy(); fwd = (mouthE.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
fwd = (fwd + Vector((0, 0, 0.05))).normalized()
SPRAY_ORIGIN, SPRAY_DIR = mw, fwd
spray("sprayA", mw, SNZ_SPRAY + 1, 260, fwd, 0.04, 0.25, drop_m, life=44, seed=3, ranges=rng("spray"))

# ======================================================================
# 4) ANGLIYA KO'CHASI (0,-60,0): g'isht uylar, trotuar, Audi
# ======================================================================
street = empty("street", (0, 0, 0))
asph = pbr("asphalt", "asphalt_02", 0.25)
pave = pbr("pave", "concrete_pavement", 0.5)
plane("road", (60, 9), tuple(ST0 + Vector((0, -4.6, 0))), asph, parent=street)
box("pavement", (60, 3.0, 0.14), tuple(ST0 + Vector((0, 1.0, 0.07))), pave, parent=street)
box("kerb", (60, 0.2, 0.15), tuple(ST0 + Vector((0, -0.55, 0.075))), mat("kerb_m", (0.55, 0.55, 0.53), 0.7), parent=street)
plane("pave_far", (60, 3), tuple(ST0 + Vector((0, -10.5, 0.14))), pave, parent=street)
line_m = mat("roadline", (0.92, 0.92, 0.88), 0.6)
for i in range(-14, 15):
    plane("rline", (1.5, 0.12), tuple(ST0 + Vector((i * 3.0, -4.6, 0.005))), line_m, parent=street)
for i in range(-14, 15):                          # sariq qo'sh chiziq (Angliya)
    pass
plane("yline1", (60, 0.08), tuple(ST0 + Vector((0, -0.85, 0.005))), mat("yline", (0.95, 0.75, 0.1), 0.6), parent=street)
plane("yline2", (60, 0.08), tuple(ST0 + Vector((0, -0.75, 0.005))), mat("yline_", (0.95, 0.75, 0.1), 0.6), parent=street)
# g'isht material
brick = bpy.data.materials.new("brick"); brick.use_nodes = True
N = brick.node_tree.nodes; L = brick.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0
br.inputs["Color1"].default_value = (0.42, 0.14, 0.08, 1); br.inputs["Color2"].default_value = (0.55, 0.22, 0.12, 1)
br.inputs["Mortar"].default_value = (0.72, 0.7, 0.65, 1); br.inputs["Mortar Size"].default_value = 0.012
br.inputs["Brick Width"].default_value = 0.22; br.inputs["Row Height"].default_value = 0.075
mp_ = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp_.inputs[0])
# yuz X-Z tekisligida: (x, z) -> (u, v)
sep = N.new("ShaderNodeSeparateXYZ"); L.new(mp_.outputs[0], sep.inputs[0]); cmb = N.new("ShaderNodeCombineXYZ")
L.new(sep.outputs[0], cmb.inputs[0]); L.new(sep.outputs[2], cmb.inputs[1]); L.new(cmb.outputs[0], br.inputs["Vector"])
nzb = N.new("ShaderNodeTexNoise"); nzb.inputs["Scale"].default_value = 8; L.new(tc.outputs["Object"], nzb.inputs[0])
mxb = N.new("ShaderNodeMix"); mxb.data_type = "RGBA"; mxb.blend_type = "MULTIPLY"; mxb.inputs["Factor"].default_value = 0.35
L.new(br.outputs["Color"], mxb.inputs[6]); L.new(nzb.outputs["Color"], mxb.inputs[7]); L.new(mxb.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.85
bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.4; L.new(br.outputs["Fac"], bmp.inputs["Height"]); L.new(bmp.outputs[0], b.inputs["Normal"])
win_m = mat("st_window", (0.03, 0.04, 0.05), 0.04, coat=1.0)
wframe_m = mat("st_wframe", (0.93, 0.93, 0.9), 0.4)
doorcols = [(0.05, 0.15, 0.35), (0.45, 0.05, 0.05), (0.05, 0.25, 0.12), (0.08, 0.08, 0.08)]
FY = ST0.y + 2.5                                   # uy fasadi
for h in range(-4, 4):
    x0 = h * 5.0
    box("house", (5.0, 0.4, 7.5), (x0 + 2.5, FY + 0.2, 3.75), brick, parent=street)
    box("cornice", (5.0, 0.5, 0.2), (x0 + 2.5, FY + 0.15, 7.4), wframe_m, parent=street)
    box("sill", (5.0, 0.08, 0.5), (x0 + 2.5, FY - 0.02, 0.25), mat(f"plinth{h}", (0.3, 0.3, 0.3), 0.8), parent=street)
    box("door", (1.0, 0.06, 2.1), (x0 + 1.0, FY - 0.01, 1.2), mat(f"door{h}", doorcols[h % 4], 0.3, coat=0.6), parent=street)
    box("door_fr", (1.2, 0.04, 2.3), (x0 + 1.0, FY + 0.005, 1.2), wframe_m, parent=street)
    box("step", (1.3, 0.4, 0.15), (x0 + 1.0, FY - 0.2, 0.075), mat(f"step{h}", (0.6, 0.6, 0.58), 0.8), parent=street)
    for (wx, wz) in ((3.4, 1.6), (1.0, 4.6), (3.4, 4.6)):
        box("win_fr", (1.3, 0.05, 1.7), (x0 + wx, FY - 0.0, wz), wframe_m, parent=street)
        box("win", (1.15, 0.06, 1.55), (x0 + wx, FY - 0.01, wz), win_m, parent=street)
        box("win_bar", (1.15, 0.07, 0.05), (x0 + wx, FY - 0.015, wz), wframe_m, parent=street)
        box("win_sill", (1.4, 0.15, 0.06), (x0 + wx, FY - 0.08, wz - 0.86), wframe_m, parent=street)
# qizil telefon budkasi + chiroq ustunlari
red_m = mat("phone_red", (0.75, 0.03, 0.02), 0.35, coat=0.5)
pbx = ST0 + Vector((3.2, 1.9, 0.14))
box("phonebox", (0.9, 0.9, 2.5), tuple(pbx + Vector((0, 0, 1.25))), red_m, parent=street)
box("phonebox_top", (1.0, 1.0, 0.2), tuple(pbx + Vector((0, 0, 2.55))), red_m, parent=street)
for dz in (0.9, 1.3, 1.7, 2.1):
    box("pb_glass", (0.7, 0.92, 0.32), tuple(pbx + Vector((0, 0, dz))), mat("pb_g", (0.7, 0.75, 0.7), 0.1, emit=0.3), parent=street)
pole_m = mat("pole", (0.03, 0.03, 0.035), 0.4, metal=0.6)
for i in range(-3, 4):
    cyl("lamppost", 0.06, 4.5, tuple(ST0 + Vector((i * 8.0 + 1.5, -0.25, 2.25))), pole_m, parent=street, verts=12)
    box("lamphead", (0.5, 0.25, 0.15), tuple(ST0 + Vector((i * 8.0 + 1.5, -0.45, 4.5))), pole_m, parent=street)
# Audi (BlenderKit, Draco yechilgan)
carR = empty("carR", tuple(ST0 + Vector((2.6, -1.55, 0.0))), street)
car_objs = import_gltf(BK + "c3c28d91_u.glb", carR)
bpy.context.view_layer.update()
mins = Vector((1e9, 1e9, 1e9)); maxs = Vector((-1e9, -1e9, -1e9))
for o in car_objs:
    if o.type != "MESH": continue
    for c_ in o.bound_box:
        w_ = o.matrix_world @ Vector(c_); mins = Vector(map(min, mins, w_)); maxs = Vector(map(max, maxs, w_))
CAR_DIM = maxs - mins
if CAR_DIM.y > CAR_DIM.x: carR.rotation_euler.z = R(90)
bpy.context.view_layer.update()
carR.location.z -= (mins.z - 0.0)
# o'tib ketadigan qizil ikki qavatli avtobus o'rniga: oddiy qizil mashina kuzovi (uzoqda, xira)
bus = empty("bus", (0, 0, 0), street)
box("bus_body", (10.0, 2.5, 4.2), (0, 0, 2.3), red_m, parent=bus)
for z_ in (1.9, 3.6):
    box("bus_win", (9.2, 2.52, 0.8), (0, 0, z_), mat("bus_w", (0.05, 0.06, 0.07), 0.05, coat=1.0), parent=bus)
for xw in (-3.3, 3.3):
    for yw in (-1.2, 1.2):
        cyl("bus_wheel", 0.5, 0.3, (xw, yw, 0.5), mat("tyre", (0.02, 0.02, 0.02), 0.8), rot=(90, 0, 0), parent=bus, verts=16)
key(bus, STR0, loc=tuple(ST0 + Vector((-22, -6.6, 0)))); key(bus, STR1, loc=tuple(ST0 + Vector((-2, -6.6, 0))))
interp(bus, "LINEAR", "location")
vis(street, STREET_SHOTS)

# ======================================================================
# 5) KASALXONA XONASI (40,0,0): rentgen ekrani + karavot
# ======================================================================
hosp = empty("hosp", (0, 0, 0))
hfloor = pbr("hfloor", "concrete_pavement", 0.6, tint=(0.85, 0.9, 0.88))
hb_ = hfloor.node_tree.nodes["Principled BSDF"]
for l in list(hb_.inputs["Roughness"].links): hfloor.node_tree.links.remove(l)
hb_.inputs["Roughness"].default_value = 0.2
hwall = mat("hwall", (0.78, 0.86, 0.84), 0.6)
plane("hfloor", (10, 10), tuple(HOSP), hfloor, parent=hosp)
plane("hwall_b", (10, 3), tuple(HOSP + Vector((0, 2.5, 1.5))), hwall, rot=(90, 0, 0), parent=hosp)
plane("hwall_l", (10, 3), tuple(HOSP + Vector((-2.5, 0, 1.5))), hwall, rot=(90, 0, 90), parent=hosp)
plane("hwall_r", (10, 3), tuple(HOSP + Vector((3.0, 0, 1.5))), hwall, rot=(90, 0, -90), parent=hosp)
plane("hceil", (10, 10), tuple(HOSP + Vector((0, 0, 2.8))), mat("hceil_m", (0.9, 0.92, 0.92), 0.7), rot=(180, 0, 0), parent=hosp)
hpanel = mat("hpanel", (1, 1, 1), 0.5, emit=6.0, emit_col=(0.92, 0.97, 1.0))
for dx in (-1.0, 1.4):
    plane("hlight", (0.6, 1.2), tuple(HOSP + Vector((dx, 0.3, 2.79))), hpanel, rot=(180, 0, 0), parent=hosp)
box("hrail", (10, 0.04, 0.12), tuple(HOSP + Vector((0, 2.47, 0.95))), mat("hrail_w", (0.35, 0.55, 0.6), 0.5), parent=hosp)
# rentgen ekrani (devorga osilgan negatoskop): bo'yin rentgeni
LB = HOSP + Vector((-0.9, 2.45, 1.5))
box("lb_frame", (1.3, 0.08, 0.95), tuple(LB), mat("lb_fr", (0.85, 0.86, 0.88), 0.3, metal=0.3), parent=hosp)
lbg = mat("lb_glow", (0.03, 0.05, 0.08), 0.5, emit=1.5, emit_col=(0.35, 0.5, 0.65))
plane("lb_screen", (1.2, 0.85), tuple(LB + Vector((0, -0.045, 0))), lbg, rot=(90, 0, 0), parent=hosp)
bone_m = mat("xb", (0.9, 0.95, 1.0), 0.5, emit=4.0, emit_col=(0.85, 0.92, 1.0))
soft_m = mat("xs", (0.4, 0.55, 0.7), 0.5, emit=1.6, emit_col=(0.45, 0.6, 0.75))
sphere("x_skull", 0.2, tuple(LB + Vector((0.1, -0.05, 0.18))), soft_m, scale=(1.0, 0.05, 0.85), parent=hosp)
sphere("x_jaw", 0.12, tuple(LB + Vector((0.2, -0.052, 0.02))), bone_m, scale=(1.0, 0.05, 0.5), parent=hosp)
box("x_neck", (0.2, 0.01, 0.5), tuple(LB + Vector((0.0, -0.05, -0.15))), soft_m, parent=hosp)
for k in range(6):
    box("x_vert", (0.07, 0.01, 0.05), tuple(LB + Vector((-0.05, -0.053, -0.02 - k * 0.065))), bone_m, parent=hosp)
box("x_air", (0.045, 0.01, 0.5), tuple(LB + Vector((0.07, -0.055, -0.12))), mat("xair", (0.02, 0.02, 0.03), 0.5), parent=hosp)
rk2 = random.Random(8)
for i in range(30):   # rentgendagi havo (qora dog'lar) — teri ostidagi havo
    sphere("x_airb", rk2.uniform(0.008, 0.02), tuple(LB + Vector((rk2.uniform(-0.12, 0.2), -0.056, rk2.uniform(-0.38, 0.0)))),
           mat("xab", (0.0, 0.0, 0.0), 0.5), scale=(1, 0.2, 1), parent=hosp)
box("x_tear", (0.012, 0.012, 0.08), tuple(LB + Vector((0.095, -0.058, -0.06))), mat("xtear", (1, 0.1, 0.02), 0.5, emit=12.0), rot=(0, 20, 0), parent=hosp)
# karavot
bed = empty("bed", tuple(BED))
sheet_m = mat("sheet", (0.92, 0.94, 0.96), 0.7, sss=0.2)
blanket_m = mat("blanket", (0.55, 0.72, 0.85), 0.85)
rail_m = mat("rail", (0.6, 0.62, 0.65), 0.25, metal=0.9)
box("mattress", (0.95, 2.05, 0.16), (0, 0, BED_Z - 0.08), sheet_m, parent=bed)
box("bframe", (1.0, 2.1, 0.08), (0, 0, BED_Z - 0.2), rail_m, parent=bed)
box("pillow", (0.6, 0.35, 0.12), (0, 0.8, BED_Z + 0.04), sheet_m, parent=bed)
box("headboard", (1.0, 0.05, 0.6), (0, 1.05, BED_Z + 0.1), mat("hb_m", (0.4, 0.55, 0.6), 0.5), parent=bed)
for dx in (-0.45, 0.45):
    for dy in (-0.95, 0.95):
        cyl("bleg", 0.02, BED_Z - 0.2, (dx, dy, (BED_Z - 0.2) / 2), rail_m, parent=bed)
blanket = box("blanket", (1.0, 1.25, 0.2), (0, -0.42, BED_Z + 0.08), blanket_m, parent=bed)
# tomchilatgich ustuni + ovqat qopchasi
IVP = BED + Vector((-0.75, 0.75, 0))
cyl("iv_pole", 0.015, 1.9, tuple(IVP + Vector((0, 0, 0.95))), rail_m, parent=hosp)
cyl("iv_hook", 0.01, 0.3, tuple(IVP + Vector((0, 0, 1.88))), rail_m, rot=(0, 90, 0), parent=hosp)
bag_m = mat("bag", (0.95, 0.85, 0.55), 0.1, trans=0.4, alpha=0.8)
sphere("iv_bag", 0.1, tuple(IVP + Vector((0, 0, 1.68))), bag_m, scale=(0.9, 0.35, 1.3), parent=hosp)
mon_m = mat("monitor", (0.02, 0.02, 0.02), 0.2)
box("monitor", (0.4, 0.05, 0.3), tuple(BED + Vector((0.85, 1.0, 1.4))), mon_m, parent=hosp)
plane("monitor_scr", (0.36, 0.26), tuple(BED + Vector((0.85, 0.97, 1.4))), mat("mon_scr", (0.1, 1.0, 0.4), 0.3, emit=2.5), rot=(90, 0, 0), parent=hosp)
# deraza (kun-tun)
hwin_m = mat("hwin", (0.75, 0.85, 1.0), 0.0, emit=3.0)
hwb = hwin_m.node_tree.nodes["Principled BSDF"]
plane("hwindow", (1.4, 1.3), tuple(HOSP + Vector((2.99, 0.9, 1.6))), hwin_m, rot=(90, 0, -90), parent=hosp)
# shifokorlar
scrub_m = mat("scrubs", (0.12, 0.42, 0.45), 0.8)
croot, chad, cmesh = mc.load_character("chad", "Chad.fbx"); sc.render.fps = 24; soften(cmesh)
kroot, kate, kmesh = mc.load_character("kate", "Kate.fbx"); sc.render.fps = 24; soften(kmesh)
for o in kmesh:
    if any(k in o.name for k in ("Shirt", "Pants", "Suit", "Top", "Bottom", "Jacket")):
        for slot in o.material_slots: slot.link = "OBJECT"; slot.material = scrub_m
DO0, DO1 = S["doctors"]; BE0, BE1 = S["bed"]
strip(chad, A_("Idle_14.fbx"), DO0 - 40, blend=0, bout=0, repeat=2.0)
strip(kate, A_("Breathing_Idle.fbx"), DO0 - 40, blend=0, bout=0, repeat=2.0)
strip(chad, A_("Reacting.fbx"), DO0 + 10, blend=6, bout=0, src=(1, 111))
strip(kate, A_("Reacting.fbx"), DO0 + 18, blend=6, bout=0, src=(1, 111))
place(croot, 1, tuple(LB + Vector((-0.1, -1.15, -1.5))), rot=180)
place(kroot, 1, tuple(LB + Vector((0.55, -1.35, -1.5))), rot=200)
for o in cmesh + kmesh: vis(o, rng("doctors"), recursive=False)
vis(hosp, HOSP_SHOTS); vis(bed, rng("bed")); vis(room, ROOM_SHOTS)

# ======================================================================
# 6) TOMOQ STUDIYASI (0,60,1) — makro, halqum devori yirtiladi (magnit.py ichak materiali)
# ======================================================================
G0 = Vector((0, 60, 1.0))
gut = empty("throat_studio", tuple(G0))
RT = 0.36
HOLE_C = Vector((0.08, -0.35, 0.06))
thr_m = gut_material("throat_wall", hole=True); bg_m = gut_material("throat_bg")
for m_ in (thr_m, bg_m):
    cr_ = [n for n in m_.node_tree.nodes if n.bl_idname == "ShaderNodeValToRGB"][0]
    cr_.color_ramp.elements[0].color = (0.7, 0.25, 0.25, 1); cr_.color_ramp.elements[1].color = (0.95, 0.6, 0.58, 1)
thr = P.tube("throat_tube", [(0, 0, -2.6), (0.05, 0.0, -1.2), (0.0, 0.0, 0.0), (-0.05, 0.0, 1.2), (0.0, 0.0, 2.6)], RT, thr_m, gut)
# tog'ay halqalari (traxeya kabi)
ring_m = mat("cart", (0.95, 0.85, 0.8), 0.4, sss=0.4, sss_scale=0.02, coat=0.5)
for k in range(-6, 7):
    if abs(k) < 2: continue
    bpy.ops.mesh.primitive_torus_add(major_radius=RT * 1.01, minor_radius=0.035, location=(0, 0, 0))
    t_ = bpy.context.object; t_.name = "cart_ring"; t_.data.materials.append(ring_m); t_.parent = gut
    t_.location = (0.0, 0.0, k * 0.36); t_.scale = (1, 1, 1)
    for p_ in t_.data.polygons: p_.use_smooth = True
inner_m = mat("thr_inner", (0.05, 0.01, 0.015), 0.6)
inner = P.tube("throat_inner", [(0, 0, -2.6), (0.05, 0.0, -1.2), (0.0, 0.0, 0.0), (-0.05, 0.0, 1.2), (0.0, 0.0, 2.6)], RT * 0.8, inner_m, gut)
rb = random.Random(5)
for j in range(6):
    y = 1.0 + j * 0.5; x0 = rb.uniform(-2.0, 2.0)
    pts = [(x0 + 0.4 * math.sin(k * 1.3 + j), y + rb.uniform(-0.3, 0.3), -3.0 + k * 1.0) for k in range(7)]
    P.tube(f"thr_bg{j}", pts, rb.uniform(0.2, 0.32), bg_m, gut)
cav_m = mat("t_cavity", (0.32, 0.07, 0.07), 0.3, sss=0.3, sss_scale=0.05, coat=1.0)
cav = sphere("t_cavity", 7.0, (0, 0, 0), cav_m, sub=4, parent=gut, world=False); cav.location = (0, 2.0, 0)
TE0, TE1 = S["tear"]
TEAR_T = 930                                       # "yirtib" ~38.7 s
for m_ in (thr_m,):
    val_key(m_, "xr", 1, 0.0); val_key(m_, "pale", 1, 0.0)
    val_key(m_, "blood", 1, 1.0); val_key(m_, "dead_r", 1, 0.0)
    val_key(m_, "infl", 1, 0.0); val_key(m_, "infl", TEAR_T, 0.3); val_key(m_, "infl", TE1, 1.1)
val_key(thr_m, "hole_r", 1, 0.0); val_key(thr_m, "hole_r", TEAR_T - 2, 0.0); val_key(thr_m, "hole_r", TEAR_T + 6, 0.06)
val_key(thr_m, "hole_r", TEAR_T + 30, 0.1); val_key(thr_m, "hole_r", TE1, 0.13)
# yoriqdan havo pufakchalari otilib chiqadi
tb_m = mat("t_bub", (0.8, 0.9, 1.0), 0.05, trans=0.6, coat=1.0, emit=0.6, emit_col=(0.6, 0.8, 1.0))
rtb = random.Random(31); HW_ = HOLE_C + Vector((0, -0.03, 0))
for i in range(40):
    s_ = sphere(f"tbub{i}", rtb.uniform(0.02, 0.06), (0, 0, 0), tb_m, sub=3, parent=gut, world=False)
    t0 = TEAR_T + 6 + int(i * (TE1 - TEAR_T - 10) / 40)
    v = Vector((rtb.uniform(-0.5, 0.5), -1.0, rtb.uniform(-0.4, 0.6))).normalized() * rtb.uniform(0.02, 0.04)
    key(s_, 1, loc=tuple(HW_), scale=(0.001,) * 3); key(s_, t0, loc=tuple(HW_), scale=(0.001,) * 3)
    for k in range(2, 50, 4):
        key(s_, t0 + k, loc=tuple(HW_ + v * k), scale=(min(1.0, k / 6),) * 3)
    interp(s_, "LINEAR")
vis(gut, TH_SHOTS)

# ======================================================================
# 7) TIRSAKKA AKSIRISH tomchilari (mehmonxona) + naycha (kasalxona)
# ======================================================================
sc.frame_set(SNZ_ELBOW + 2)
mw2 = mouthE.matrix_world.translation.copy(); fwd2 = (mouthE.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
drop2_m = mat("drop2_m", (0.85, 0.92, 1.0), 0.02, trans=0.5, coat=1.0, emit=0.4, emit_col=(0.8, 0.9, 1.0))
spray("sprayE", mw2, SNZ_ELBOW + 1, 70, fwd2 + Vector((0.25, 0, 0)), 0.03, 0.5, drop2_m, life=24, rmin=0.001, rmax=0.0025,
      grav=0.0002, seed=8, max_dist=0.07, ranges=rng("elbow"))
# burundan oshqozonga naycha (karavot kadri)
sc.frame_set(BE0 + 10)
noseE = empty("noseE", hp(0.008, 0.07, 0.125), headE)
bpy.context.view_layer.update()
nose_w = noseE.matrix_world.translation.copy()
tube_m = mat("ng_tube", (0.9, 0.85, 0.7), 0.15, trans=0.3, coat=1.0, sss=0.2)
bagp = IVP + Vector((0, 0, 1.55))
mid1 = nose_w + Vector((0.08, 0.05, 0.12)); mid2 = (nose_w + bagp) / 2 + Vector((0, 0, -0.15))
ngt = P.tube("ng_tube", catmull([tuple(nose_w), tuple(mid1), tuple(mid2), tuple(bagp)], 0.02), 0.0035, tube_m, None)
vis(ngt, rng("bed"), recursive=False)

# ======================================================================
# 8) KAMERALAR
# ======================================================================
def wpos(o, f, local=(0, 0, 0)):
    sc.frame_set(f); return o.matrix_world @ Vector(local)
def head_dirs(f):
    sc.frame_set(f); m3 = headE.matrix_world.to_3x3().normalized()
    return m3 @ Vector((1, 0, 0)), m3 @ Vector((0, 1, 0)), m3 @ Vector((0, 0, 1))   # chap, tepa, old
def follow_target(name, src, f0, f1, local=(0, 0, 0), step=2, lag=0.0):
    t = empty(name, (0, 0, 0))
    for f in range(f0, f1 + 1, step): key(t, f, loc=tuple(wpos(src, f, local)))
    interp(t, "LINEAR", "location"); return t
def cam_rel(c, f0, f1, ref, f_ref, offs, step=3):
    """kamera pozitsiyasi = ref ob'ektning f_ref kadridagi joyi + offs(t) (dunyo)"""
    base = wpos(ref, f_ref)
    for f in range(f0, f1 + 1, step):
        t = (f - f0) / max(1, f1 - f0); key(c, f, loc=tuple(base + Vector(offs(t))))
    interp(c, "BEZIER", "location")
def lerp3(a, b_, t, e=True):
    t = ease(t) if e else t; return tuple(Vector(a).lerp(Vector(b_), t))
HO0, HO1 = S["hook"]; CO0, CO1 = S["cover"]; JO0, JO1 = S["jolt"]; ST_0, ST_1 = S["street"]; HL0, HL1 = S["hold"]
WI0, WI1 = S["widen"]; SN0, SN1 = S["swollen"]; DN0, DN1 = S["dont"]; EL0, EL1 = S["elbow"]
# 1 ilgak: yuzga juda yaqin, push-in
fT = follow_target("hookT", faceT, HO0, HO1 + 2)
c = shot_cam("hook", (0, 0, 0), fT, 50, 2.0, focus=fT)
cam_rel(c, HO0, HO1, faceT, HO0, lambda t: lerp3((0.1, -0.62, -0.06), (0.04, -0.3, -0.03), t, e=False))
lens_keys(c, ((HO0, 40), (HO1, 58)))
# 2 yopish: yon tomondan, past, aylanma
fT2 = follow_target("coverT", faceT, CO0, CO1 + 2, local=(0, -0.03, 0.03))
c = shot_cam("cover", (0, 0, 0), fT2, 40, 2.4, focus=fT2)
fc0 = wpos(faceT, CO0)
for f in range(CO0, CO1 + 1, 3):
    t = (f - CO0) / (CO1 - CO0); a = R(-55 + 25 * t); rr = 0.62 - 0.12 * t
    key(c, f, loc=tuple(fc0 + Vector((rr * math.sin(a), -rr * math.cos(a), -0.14 + 0.04 * t))))
# 3 silkinish: keng, past burchak 16 mm
chT = empty("joltT", (ROOMP[0], ROOMP[1], 1.05))
c = shot_cam("jolt", (0, 0, 0), chT, 16, 4.0, focus=faceT)
orbit(c, JO0, JO1, (ROOMP[0], ROOMP[1], 0), 1.7, 1.45, 22, 6, 0.32, 0.38)
lens_keys(c, ((JO0, 16), (SNZ_JOLT, 17), (SNZ_JOLT + 3, 22), (JO1, 23)))
shake(c, SNZ_JOLT, SNZ_JOLT + 16, 0.05, 3)
# 4 rentgen: ko'krakdan og'izga
xT = empty("xlungsT", (0, 0, 0))
c = shot_cam("xlungs", (0, 0, 0), xT, 32, 4.0, focus=xT)
for f in range(XL0, XL1 + 2, 2):
    t = ease((f - XL0) / (XL1 - XL0))
    a_ = wpos(chestE, f, (0, 0.1, 0.03)); b2 = wpos(headE, f, hp(0, 0.04, 0.08))
    p = a_.lerp(b2, t); key(xT, f, loc=tuple(p))
    key(c, f, loc=tuple(p + Vector((0.42 - 0.12 * t, -0.72 + 0.12 * t, -0.08 + 0.05 * t))))
# 5 aksirish oqimi: yonidan, ergashadi
spT = empty("sprayT", (0, 0, 0))
c = shot_cam("spray", (0, 0, 0), spT, 30, 5.6, focus=spT)
for f in range(SP0, SP1 + 2, 2):
    t = (f - SP0) / (SP1 - SP0); u = max(0.0, min(1.0, (f - SNZ_SPRAY) / 30.0))
    p = SPRAY_ORIGIN + SPRAY_DIR * (0.1 + 0.22 * ease(u)) + Vector((0, 0, -0.03))
    key(spT, f, loc=tuple(p)); key(c, f, loc=tuple(p + Vector((1.2 - 0.1 * t, 0.05 - 0.15 * t, 0.03))))
lens_keys(c, ((SP0, 34), (SNZ_SPRAY, 38), (SNZ_SPRAY + 3, 26), (SP1, 24)))
shake(c, SNZ_SPRAY, SNZ_SPRAY + 10, 0.02, 5)
# 6 yopilgan: yuz oldidan push-in
blT = follow_target("blockT", headE, BL0, BL1 + 2, local=hp(0, 0.05, 0.06))
c = shot_cam("block", (0, 0, 0), blT, 40, 4.0, focus=blT)
cam_rel(c, BL0, BL1, faceT, BL0, lambda t: lerp3((-0.35, -0.65, -0.05), (-0.2, -0.42, -0.03), t))
shake(c, SNZ_BLOCK, SNZ_BLOCK + 10, 0.012, 6)
# 7 bosim: bosh atrofida aylanma
prT = follow_target("pressT", headE, PR0, TH1 + 2, local=hp(0, 0.05, 0.03))
c = shot_cam("pressure", (0, 0, 0), prT, 35, 4.0, focus=prT)
pc = wpos(headE, PR0, hp(0, 0.05, 0.03))
for f in range(PR0, PR1 + 1, 3):
    t = (f - PR0) / (PR1 - PR0); a = R(70 - 55 * t); rr = 0.55 - 0.1 * t
    key(c, f, loc=tuple(pc + Vector((rr * math.sin(a), -rr * math.cos(a), 0.03))))
# 8 quloqlar: yondan, crash zoom
eaT = follow_target("earT", headE, EA0, EA1 + 2, local=hp(0.06, 0.085, 0.01))
c = shot_cam("ears", (0, 0, 0), eaT, 30, 4.0, focus=eaT)
cam_rel(c, EA0, EA1, headE, EA0, lambda t: lerp3((0.5, -0.32, 0.12), (0.4, -0.22, 0.13), t))
lens_keys(c, ((EA0, 28), (EA0 + 12, 32), (EA0 + 16, 55), (EA1, 60)))
shake(c, EA0, EA0 + 6, 0.02, 8); shake(c, EA0 + 16, EA0 + 24, 0.008, 9)
# 9 ko'zlar: old tomondan
eyT = follow_target("eyeT", headE, EY0, EY1 + 2, local=hp(0, 0.11, 0.08))
c = shot_cam("eyes", (0, 0, 0), eyT, 30, 4.0, focus=eyT)
cam_rel(c, EY0, EY1, headE, EY0, lambda t: lerp3((-0.12, -0.5, 0.2), (-0.08, -0.4, 0.18), t))
lens_keys(c, ((EY0, 28), (EY0 + 12, 32), (EY0 + 16, 58), (EY1, 62)))
shake(c, EY0, EY0 + 6, 0.02, 10)
# 10 tomoq: pastga tushadi
thT = empty("throatT", (0, 0, 0))
c = shot_cam("throat", (0, 0, 0), thT, 35, 4.0, focus=thT)
for f in range(TH0, TH1 + 2, 2):
    t = ease((f - TH0) / (TH1 - TH0))
    p = wpos(headE, f, hp(0, 0.09, 0.06)).lerp(wpos(headE, f, hp(0, -0.06, 0.02)), t); key(thT, f, loc=tuple(p))
    key(c, f, loc=tuple(p + Vector((0.32, -0.45, 0.05 - 0.08 * t))))
# 11 ko'cha: past burchak, keng, ergashadi
bT = empty("walkT", (0, 0, 0))
c = shot_cam("street", (0, 0, 0), bT, 18, 5.6, focus=bT)
for f in range(ST_0, ST_1 + 2, 2):
    p = wpos(chestE, f); key(bT, f, loc=tuple(p + Vector((0, 0, -0.1))))
    t = (f - ST_0) / (ST_1 - ST_0)
    key(c, f, loc=(p.x + 2.4 - 0.6 * t, ST0.y + 2.15, 0.42 + 0.1 * t))
interp(c, "LINEAR", "location"); interp(bT, "LINEAR", "location")
# 12 ushlab qoldi: yuzga yaqin, orqa fon xira
hoT = follow_target("holdT", faceT, HL0, HL1 + 2, local=(0, -0.03, 0.03))
c = shot_cam("hold", (0, 0, 0), hoT, 70, 1.8, focus=hoT)
cam_rel(c, HL0, HL1, faceT, HL0, lambda t: lerp3((0.85, 0.75, -0.08), (0.7, 0.55, -0.06), t))
# 13 ko'zlar katta ochiladi: juda yaqin
wiT = follow_target("widenT", faceT, WI0, WI1 + 2, local=(0, -0.04, 0.02))
c = shot_cam("widen", (0, 0, 0), wiT, 70, 2.2, focus=wiT)
cam_rel(c, WI0, WI1, faceT, WI0, lambda t: lerp3((0.6, 0.42, -0.1), (0.42, 0.28, -0.06), t, e=False))
# 14 qirs: rentgen bo'yin, crash zoom
ckT = follow_target("crackT", headE, CK0, CK1 + 2, local=tuple(CRACK))
c = shot_cam("crack", (0, 0, 0), ckT, 30, 4.0, focus=ckT)
cam_rel(c, CK0, CK1, headE, CK0, lambda t: lerp3((0.35, 0.3, -0.05), (0.26, 0.2, -0.06), t))
lens_keys(c, ((CK0, 30), (SNZ_QIRS - 1, 36), (SNZ_QIRS + 2, 62), (CK1, 66)))
shake(c, SNZ_QIRS, SNZ_QIRS + 14, 0.02, 14)
# 15 shishgan tomoq: past burchak, aylanma
swT = follow_target("swollenT", neckE, SN0, SN1 + 2, local=(0, 0.02, 0.06))
c = shot_cam("swollen", (0, 0, 0), swT, 24, 2.8, focus=swT)
scn = wpos(neckE, SN0)
for f in range(SN0, SN1 + 1, 3):
    t = (f - SN0) / (SN1 - SN0); a = R(-40 + 50 * t); rr = 1.0 - 0.25 * t
    key(c, f, loc=tuple(scn + Vector((rr * math.cos(a), rr * math.sin(a), -0.75 + 0.15 * t))))
# 16 yutinish: rentgen, yondan
swxT = follow_target("swallowT", headE, SW0, SW1 + 2, local=hp(0, -0.02, 0.03))
c = shot_cam("swallow", (0, 0, 0), swxT, 40, 4.0, focus=swxT)
cam_rel(c, SW0, SW1, headE, SW0, lambda t: lerp3((0.4, 0.38, 0.1), (0.32, 0.3, -0.02), t))
# 17 shifokorlar: ekran yonidan, past, push-in
dT = empty("docT", tuple(LB + Vector((0.15, -1.2, -0.05))))
c = shot_cam("doctors", (0, 0, 0), dT, 24, 2.8, focus=dT)
path_keys(c, ((DO0, tuple(LB + Vector((1.15, -0.25, -0.35)))), (DO1, tuple(LB + Vector((0.95, -0.45, -0.25))))))
# 18 yirtilish: tomoq studiyasi, crash zoom
tT = empty("tearT", tuple(G0 + HOLE_C))
c = shot_cam("tear", (0, 0, 0), tT, 28, 3.5, focus=tT)
path_keys(c, ((TE0, tuple(G0 + HOLE_C + Vector((-0.9, -2.2, 0.6)))), (TEAR_T, tuple(G0 + HOLE_C + Vector((-0.6, -1.7, 0.4)))),
              (TE1, tuple(G0 + HOLE_C + Vector((-0.3, -1.2, 0.2))))))
lens_keys(c, ((TE0, 26), (TEAR_T - 1, 30), (TEAR_T + 2, 50), (TE1, 56)))
shake(c, TEAR_T, TEAR_T + 12, 0.04, 18)
# 19 havo: bo'yindan ko'krakka
aiT = empty("airT", (0, 0, 0))
c = shot_cam("air", (0, 0, 0), aiT, 28, 4.0, focus=aiT)
for f in range(AI0, AI1 + 2, 3):
    t = ease((f - AI0) / (AI1 - AI0))
    p = wpos(headE, f, hp(0, -0.05, 0.03)).lerp(wpos(chestE, f, (0, 0.12, 0.05)), t); key(aiT, f, loc=tuple(p))
    key(c, f, loc=tuple(p + Vector((-0.3 + 0.1 * t, -0.62 - 0.15 * t, 0.12 - 0.04 * t))))
# 20 karavot: tepadan, aylanma
bdT = follow_target("bedT", chestE, BE0, BE1 + 2, local=(0, 0.25, 0.0))
c = shot_cam("bed", (0, 0, 0), bdT, 26, 4.0, focus=bdT)
orbit(c, BE0, BE1, tuple(BED + Vector((0, 0.25, 0))), 1.35, 1.1, 150, 205, 2.05, 1.85)
# 21 to'xtat: yuz oldidan
dnT = follow_target("dontT", faceT, DN0, DN1 + 2, local=(0, -0.04, 0.02))
c = shot_cam("dont", (0, 0, 0), dnT, 45, 2.2, focus=dnT)
cam_rel(c, DN0, DN1, faceT, DN0, lambda t: lerp3((0.28, -0.9, -0.12), (0.12, -0.62, -0.08), t))
# 22 tirsak: o'rta plan, push-in
elT = follow_target("elbowT", faceT, EL0, EL1 + 2, local=(0.05, -0.05, 0.05))
c = shot_cam("elbow", (0, 0, 0), elT, 28, 2.8, focus=elT)
cam_rel(c, EL0, EL1, faceT, EL0, lambda t: lerp3((0.75, -1.1, -0.35), (0.45, -0.6, -0.15), t))
shake(c, SNZ_ELBOW, SNZ_ELBOW + 10, 0.015, 22)
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 9) YORUG'LIK
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
ROOM_N = {"hook", "cover", "jolt", "dont", "elbow", "doctors", "bed"}
for f, n in SHOTS:
    s1, s2 = (0.35, 0.0) if n in ROOM_N else ((1.0, 0.0) if n in ("street", "hold", "widen", "swollen") else (0.0, 1.0))
    for bgn, v in ((bg_sky, s1), (bg_dk, s2)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.0); sun.data.color = (1.0, 0.9, 0.78); sun.rotation_euler = (R(55), 0, R(-62))
STREET_N = STREET_SHOTS
for f, n in SHOTS:
    e = 3.5 if n in ("hook", "cover", "jolt", "dont", "elbow") else (4.5 if n in ("street", "hold", "widen", "swollen") else 0.0)
    rot = (R(50), 0, R(-140)) if n in ("street", "hold", "widen", "swollen") else (R(55), 0, R(-62))
    sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
    sun.rotation_euler = rot; sun.keyframe_insert("rotation_euler", frame=f)
interp(sun.data, "CONSTANT"); interp(sun, "CONSTANT")
RS = ROOM_SHOTS
chestT = empty("chestT", (ROOMP[0], ROOMP[1], 1.3))
area("room_key", (-1.2, -0.9, 2.2), 1.5, (1.0, 0.88, 0.75), lights_for(RS, 260.0), target=chestT)
area("room_fill", (1.8, -1.0, 1.4), 1.2, (0.85, 0.9, 1.0), lights_for(RS, 90.0), target=chestT)
area("room_rim", (0.8, 1.6, 2.2), 0.8, (1.0, 0.75, 0.5), lights_for(RS, 140.0), target=chestT)
point("lamp_light", (1.05, 1.9, 1.5), 0.15, (1.0, 0.7, 0.4), lights_for(RS, 60.0))
point("jolt_flash", (0.0, -0.4, 1.6), 0.2, (1.0, 1.0, 1.0), [(1, 0), (SNZ_JOLT, 300), (SNZ_JOLT + 3, 40), (SNZ_JOLT + 8, 0)], const=False)
# rentgen
area("x_rim", (-0.8, 2.0, 1.8), 1.0, (0.3, 0.6, 1.0), lights_for(X_SHOTS, 30.0), target=chestT)
area("x_key", (0.8, -0.6, 1.8), 0.8, (1.0, 0.92, 0.88), lights_for(X_SHOTS, 18.0), target=chestT)
point("x_block", (0, 0, 0), 0.03, (1.0, 0.25, 0.08), [(1, 0), (SNZ_BLOCK + 2, 0), (SNZ_BLOCK + 4, 6.0), (SNZ_BLOCK + 14, 1.0), (PR0, 0)], parent=mouthE, const=False)
point("x_press", (0, 0, 0), 0.03, (1.0, 0.2, 0.06), [(1, 0), (PR0, 0.5), (PR1, 4.0), (TH1, 6.0), (TH1 + 1, 0)], parent=press, const=False)
point("x_qirs", (0, 0, 0), 0.02, (1.0, 0.15, 0.04), [(1, 0), (SNZ_QIRS, 0), (SNZ_QIRS + 1, 25), (SNZ_QIRS + 6, 5), (SW1, 5), (SW1 + 1, 0)], parent=crack, const=False)
# ko'cha: quyosh + osmon (yuqorida)
swl = point("swell_red", (0, 0, 0), 0.05, (1.0, 0.1, 0.04), [(1, 0)], parent=neckE, const=False)
swl.location = (0, 0.02, 0.35)
for f in range(SN0, SN1 + 1, 12): swl.data.energy = 2.0; swl.data.keyframe_insert("energy", frame=f); swl.data.energy = 12.0; swl.data.keyframe_insert("energy", frame=f + 6)
swl.data.energy = 0; swl.data.keyframe_insert("energy", frame=SN1 + 1); swl.data.keyframe_insert("energy", frame=SN0 - 1)
# kasalxona
area("h_fill", tuple(HOSP + Vector((0.5, -1.5, 2.4))), 2.0, (0.9, 0.97, 1.0), lights_for(HOSP_SHOTS, 160.0), target=dT)
area("h_key", tuple(HOSP + Vector((-0.5, 0.5, 2.6))), 1.2, (0.92, 0.97, 1.0), lights_for(HOSP_SHOTS, 120.0), shape=(0.6, 1.2))
area("lb_spill", tuple(LB + Vector((0, -0.3, 0))), 1.0, (0.55, 0.75, 1.0), lights_for(rng("doctors"), 60.0), target=dT)
hsun = area("h_window", tuple(HOSP + Vector((2.8, 0.9, 1.6))), 1.3, (1.0, 0.9, 0.75), [(1, 0)], target=bdT)
for f in range(BE0, BE1 + 1, 14):
    for ff, e, col in ((f, 250.0, (1.0, 0.85, 0.65)), (f + 7, 8.0, (0.35, 0.45, 1.0))):
        hsun.data.energy = e; hsun.data.keyframe_insert("energy", frame=ff); hsun.data.color = col; hsun.data.keyframe_insert("color", frame=ff)
        hwb.inputs["Emission Strength"].default_value = 3.0 if e > 100 else 0.15
        hwb.inputs["Emission Strength"].keyframe_insert("default_value", frame=ff)
hsun.data.energy = 0; hsun.data.keyframe_insert("energy", frame=BE1 + 1)
interp(hsun.data, "CONSTANT")
# tomoq studiyasi
TS = TH_SHOTS
area("t_key", tuple(G0 + Vector((-1.5, -2.4, 1.6))), 1.5, (1.0, 0.9, 0.85), lights_for(TS, 320.0), target=tT)
area("t_rim", tuple(G0 + Vector((1.6, 0.8, 1.2))), 1.2, (1.0, 0.45, 0.4), lights_for(TS, 260.0), target=tT)
area("t_fill", tuple(G0 + Vector((1.2, -1.8, -1.0))), 1.0, (0.55, 0.7, 1.0), lights_for(TS, 90.0), target=tT)
point("t_flash", tuple(G0 + HOLE_C + Vector((0, -0.4, 0))), 0.2, (1.0, 0.3, 0.15), [(1, 0), (TEAR_T, 0), (TEAR_T + 1, 300), (TEAR_T + 5, 60), (TEAR_T + 14, 20), (TE1 + 1, 0)], const=False)

# ======================================================================
# 10) RENDER
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
