# Ko'zdagi "suzuvchi" nuqtalar (vitreous floaters) — Zack D. Films uslubida 43.5 s video.
# Asos: zack_test/scene3.py + mixchar.py (qahramon), ebbi/eye.py (makro ko'z), ebbi/ebbi.py (kadr tizimi).
# Assetlar: zack_test/tools/get_suzuvchi.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/suzuvchi/suzuvchi.py --render
# Sinov: FRAMES=30,80,300,450,760 PCT=30
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "ebbi"))
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import eye as E
sc = bpy.context.scene
sc.render.fps = 24
END = 1044
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan) ----------------
SHOTS = [(1, "pov_sky"), (50, "look_sky"), (100, "eye_dart"), (131, "rub_dust"), (177, "room_tired"),
         (227, "eye_dive"), (287, "section"), (378, "gel_inside"), (484, "liquefy"), (546, "clump"),
         (614, "beam"), (731, "retina"), (801, "pov_sky2"), (843, "rub_hard"), (878, "wash"),
         (924, "eye_wet"), (990, "section_end")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

# ---------------- yordamchilar ----------------
empty = E.empty
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return mc._fcurves(ad.action)

def interp(idb, mode="LINEAR", path=None, easing=None):
    for fc in fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points:
            k.interpolation = mode
            if easing: k.easing = easing

def vis(o, ranges, recursive=True):
    objs = [o] + (list(o.children_recursive) if recursive else [])
    for x in objs:                                   # oldingi (ota) vis() kalitlarini tozalash
        ad = x.animation_data
        if ad and ad.action:
            for fc in [fc for fc in mc._fcurves(ad.action) if fc.data_path == "hide_render"]:
                mc._channelbag_remove(ad.action, fc)
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.02
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def glass(name, col=(1, 1, 1), ior=1.33, rough=0.02):
    m = mat(name, col, rough)
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = ior
    shadow_clear(m); return m

def shadow_clear(m):
    """shaffof narsa soyasi qop-qora bo'lmasin (kaustika o'chiq): soya nuriga Transparent"""
    N = m.node_tree.nodes; L = m.node_tree.links
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    lp = N.new("ShaderNodeLightPath"); tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(lp.outputs["Is Shadow Ray"], mx.inputs[0]); L.new(src, mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])

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

def box(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def import_glb(path, parent):
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

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 2000
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c

def shake(cam, f0, f1, amp, seed=1, decay=True):
    """kalitlangan harakat ustiga tasodifiy silkinish qo'shadi"""
    rnd = random.Random(seed); fr = list(range(f0, f1 + 1)); bases = []
    for f in fr: sc.frame_set(f); bases.append(cam.location.copy())
    for f, b in zip(fr, bases):
        k = amp * ((1 - (f - f0) / (f1 - f0)) ** 2 if decay else 1.0)
        cam.location = b + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None, spot=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "SPOT" if spot else "AREA")); sc.collection.objects.link(l)
    if spot: l.data.shadow_soft_size = size
    else: l.data.size = size
    l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def curve_obj(name, pts, radius, m, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = radius; cu.bevel_resolution = 2; cu.resolution_u = 8
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    sp.use_endpoint_u = True; sp.order_u = 4
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(m)
    if parent: o.parent = parent
    return o

def set_curve(o, f, pts):
    for p, q in zip(o.data.splines[0].points, pts):
        p.co = (*q, 1); p.keyframe_insert("co", frame=f)

def emit_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    o = N.new("ShaderNodeOutputMaterial"); e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    L.new(e.outputs[0], o.inputs[0]); return m, N, L, e

def _m(N, L, op, a, b=None, clamp=False):
    return E._math(N, L, op, a, b, clamp=clamp)

# ======================================================================
# 1) MAKRO KO'Z (dunyo markazida)
# ======================================================================
EYE_SHOTS = ["eye_dart", "eye_dive", "eye_wet"]
eA = E.build_eye("eyeA", (0, 0, 0))
vis(eA["root"], rng(*EYE_SHOTS))
W = eA["shape"].W
for f, v in ((1, 0.15), (S["eye_dive"][0], 0.1), (S["eye_wet"][0], 0.45)):
    E.key_value(eA["red"], f, v)
def keyset(k, pairs):
    for f, v in pairs: E.set_key(eA, k, f, v)
keyset("blink", [(1, 0.0), (S["eye_wet"][0], 1.0), (S["eye_wet"][0] + 5, 0.0), (S["eye_wet"][0] + 38, 0.0),
                 (S["eye_wet"][0] + 41, 1.0), (S["eye_wet"][0] + 45, 0.0)])
keyset("wide", [(1, 0.0), (S["eye_dart"][0], 0.3), (S["eye_dive"][0], 0.5), (S["eye_wet"][0], 0.0)])
keyset("squint", [(1, 0.0), (S["eye_wet"][0], 0.0), (S["eye_wet"][0] + 8, 0.25)])
ball = eA["ball"]
D0 = S["eye_dart"][0]
for f, rx, rz in ((1, 0, 0), (D0, 0, 12), (D0 + 7, 0, 12), (D0 + 9, 6, -10), (D0 + 17, 6, -10), (D0 + 19, -3, 4),
                  (S["eye_dive"][0], 0, 0), (S["eye_wet"][0], 0, 0), (S["eye_wet"][0] + 20, 0, 0), (S["eye_wet"][0] + 22, 4, -9)):
    key(ball, f, rot=(rx, 0, rz))
interp(ball, "LINEAR")
# ho'l ko'z: qovoq va kipriklardagi tomchilar
M_water = glass("water", (0.95, 0.98, 1.0), 1.33, 0.0)
drops = empty("eye_drops", (0, 0, 0), eA["root"])
for i in range(26):
    a = random.uniform(0, 2 * math.pi)
    x = random.uniform(-W * 1.1, W * 1.1); z = random.choice((-1, 1)) * random.uniform(0.0055, 0.011)
    y = eA["shape"].depth(x, z) - 0.0004
    r = random.uniform(0.0005, 0.0015)
    sphere(f"edrop{i}", r, (x, y, z), M_water, scale=(1, 0.55, 1), sub=3, parent=drops)
vis(drops, rng("eye_wet"))

# ======================================================================
# 2) KESIM KO'Z (x = 20), R = 1 m, old tomoni -Y, kesim tekisligi x = 0 (x<=0 qoladi)
# ======================================================================
CB = Vector((20.0, 0, 0)); sec = empty("section", CB)
def half(name, r, m, center=(0, 0, 0), scale=(1, 1, 1), cut_front=None, fill=False, thick=0.0, seg=128, rings=64):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    if cut_front is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < cut_front], context="VERTS")
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    if fill: bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = abs(p.normal.x) < 0.98
    me.materials.append(m)
    o.location = center; o.parent = sec
    if thick:
        so = o.modifiers.new("solid", "SOLIDIFY"); so.thickness = thick; so.offset = -1.0; so.use_rim = True
    return o

def vein_mat(name, base, vein, emit=0.0, scale=3.0, width=0.025):
    m = mat(name, base, 0.45, sss=0.15)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    def vline(sc_, w, dist):
        nn = E._node(N, "ShaderNodeTexNoise", **{"Scale": sc_, "Detail": 4.0, "Distortion": dist, "Roughness": 0.55})
        L.new(tc.outputs["Object"], nn.inputs["Vector"])
        d = _m(N, L, "ABSOLUTE", _m(N, L, "SUBTRACT", nn.outputs["Fac"], 0.5))
        return _m(N, L, "SUBTRACT", 1.0, _m(N, L, "DIVIDE", d, w), clamp=True)
    v = _m(N, L, "MAXIMUM", vline(scale, width, 0.5), _m(N, L, "MULTIPLY", vline(scale * 2.7, width * 0.7, 0.8), 0.7))
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(v, mx.inputs["Factor"])
    mx.inputs[6].default_value = (*base, 1); mx.inputs[7].default_value = (*vein, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    if emit:
        L.new(mx.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m

M_sclera = vein_mat("sclera", (0.86, 0.8, 0.74), (0.6, 0.12, 0.1), 0.0, 2.0, 0.012)
M_choroid = mat("choroid", (0.28, 0.05, 0.035), 0.5, sss=0.2)
M_retina = vein_mat("retina", (0.85, 0.32, 0.14), (0.42, 0.03, 0.03), 0.06, 2.5, 0.03)
M_cornea = glass("cornea", (0.97, 0.99, 1.0), 1.376, 0.0)
M_lens = glass("lens", (1.0, 0.96, 0.85), 1.42, 0.02)
M_gel = glass("gel", (0.88, 0.95, 1.0), 1.03, 0.12)
gb = M_gel.node_tree.nodes["Principled BSDF"]
gb.inputs["Emission Color"].default_value = (0.5, 0.75, 1.0, 1); gb.inputs["Emission Strength"].default_value = 0.04
sclera = half("sclera", 1.0, M_sclera, cut_front=-0.92, thick=0.06)
choroid = half("choroid", 0.94, M_choroid, cut_front=-0.72, thick=0.02)
retina = half("retina", 0.92, M_retina, cut_front=-0.6, thick=0.012)
cornea = half("cornea", 0.5, M_cornea, center=(0, -0.6, 0), thick=0.03)
bm_ = bmesh.new(); bm_.from_mesh(cornea.data)
bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.y > -0.28], context="VERTS"); bm_.to_mesh(cornea.data); bm_.free()
lens = half("lens", 1.0, M_lens, center=(0, -0.68, 0), scale=(0.3, 0.13, 0.3), fill=True, seg=64, rings=32)
gel = half("gel", 0.9, M_gel, center=(0, 0.1, 0), scale=(1, 0.85, 1), fill=True, seg=96, rings=48)
# kamalak parda (iris): yarim halqa
def iris_mesh():
    me = bpy.data.meshes.new("iris"); vs = []; fs = []; n = 48
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n             # x<=0 yarmi
        for r in (0.2, 0.41):
            vs.append((r * math.cos(a), 0, r * math.sin(a)))
    for i in range(n): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    me.from_pydata(vs, [], fs)
    o = bpy.data.objects.new("iris", me); sc.collection.objects.link(o); o.parent = sec; o.location = (0, -0.84, 0)
    m = mat("iris_m", (0.12, 0.22, 0.3), 0.4)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    ang = _m(N, L, "ARCTAN2", sx.outputs[2], sx.outputs[0])
    cv = N.new("ShaderNodeCombineXYZ"); L.new(_m(N, L, "MULTIPLY", ang, 14.0), cv.inputs[0])
    nz = E._node(N, "ShaderNodeTexNoise", **{"Scale": 2.0, "Detail": 8.0}); L.new(cv.outputs[0], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.05, 0.1, 0.14, 1); cr.color_ramp.elements[1].color = (0.35, 0.55, 0.6, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    me.materials.append(m)
    so = o.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.035; so.offset = 0
    for p in me.polygons: p.use_smooth = True
    return o
iris = iris_mesh()
# optik asab (orqada)
on = cyl("optic_nerve", 0.17, 1.2, (-0.05, 1.62, -0.05), mat("nerve", (0.85, 0.75, 0.6), 0.6, sss=0.2), rot=(90, 0, 0), parent=sec)
bm_ = bmesh.new(); bm_.from_mesh(on.data)
bmesh.ops.bisect_plane(bm_, geom=bm_.verts[:] + bm_.edges[:] + bm_.faces[:], plane_co=(0.05, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
bmesh.ops.holes_fill(bm_, edges=bm_.edges[:], sides=0); bm_.to_mesh(on.data); bm_.free()

# shishasimon tana tolalari (gel ichida)
M_fiber = mat("fiber", (0.92, 0.95, 1.0), 0.35, emit=0.25, alpha=0.55)
M_fiber.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.8, 0.9, 1.0, 1)
fib = empty("fibers", (0, 0, 0), sec)
for i in range(34):
    x = random.uniform(-0.65, -0.05); z = random.uniform(-0.6, 0.6)
    if x * x + z * z > 0.62: continue
    pts = []
    for j in range(7):
        y = -0.45 + j * 0.2
        pts.append(Vector((x + 0.05 * math.sin(j * 1.3 + i), y, z + 0.06 * math.sin(j * 0.9 + i * 2))))
    curve_obj(f"fiberB{i}", pts, 0.0035, M_fiber, fib)
# tugun (suzuvchi): to'q, yarim shaffof chigal tolalar
M_clump = mat("clump", (0.06, 0.055, 0.05), 0.5, alpha=0.85)
clumpB = empty("clumpB", (-0.1, 0.15, 0.06), sec)
for i in range(9):
    pts = []
    ph = random.uniform(0, 6.28)
    for j in range(8):
        t = j / 7
        pts.append(Vector((0.05 * math.sin(t * 7 + ph), -0.17 + 0.34 * t + 0.02 * math.sin(t * 9 + i), 0.05 * math.cos(t * 6 + ph * 1.3))))
    curve_obj(f"clumpfiber{i}", pts, 0.009, M_clump, clumpB)
for j in range(6):
    sphere(f"clumpdot{j}", random.uniform(0.012, 0.025), (random.uniform(-0.04, 0.04), random.uniform(-0.15, 0.15), random.uniform(-0.04, 0.04)),
           M_clump, parent=clumpB)
for f in range(1, END + 1, 12):                      # sekin suzish
    key(clumpB, f, loc=(-0.1 + 0.02 * math.sin(f * 0.02), 0.15 + 0.05 * math.sin(f * 0.013), 0.06 + 0.04 * math.sin(f * 0.017)),
        rot=(8 * math.sin(f * 0.01), 0, 12 * math.sin(f * 0.008)))
# kiruvchi nur: qorachiqdan to'r pardaga yig'iluvchi konus (qo'shimcha nur)
def beam_mesh():
    me = bpy.data.meshes.new("beam"); vs = []; fs = []; n = 32
    prof = [(-3.0, 0.12), (-0.84, 0.12), (-0.68, 0.11), (0.9, 0.05)]
    for y, r in prof:
        for i in range(n):
            a = 2 * math.pi * i / n; vs.append((r * math.cos(a), y, r * math.sin(a)))
    for k in range(len(prof) - 1):
        for i in range(n):
            j = (i + 1) % n; fs.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
    me.from_pydata(vs, [], fs)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new("beam", me); sc.collection.objects.link(o); o.parent = sec; o.location = (-0.1, 0, 0.06)
    m = bpy.data.materials.new("beam_m"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for x in list(N): N.remove(x)
    out = N.new("ShaderNodeOutputMaterial"); lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.92, 0.75, 1)
    s_ = _m(N, L, "ADD", 0.08, _m(N, L, "MULTIPLY", _m(N, L, "POWER", _m(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"]), 2.0), 1.5))
    L.new(s_, em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs[0])
    me.materials.append(m)
    return o
beam = beam_mesh()
# fon: qorong'i studiya sferasi
def backdrop(name, r, parent, colA, colB, axis=2, disc=None):
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for x in list(N): N.remove(x)
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission")
    tc = N.new("ShaderNodeTexCoord"); nv = N.new("ShaderNodeVectorMath"); nv.operation = "NORMALIZE"; L.new(tc.outputs["Object"], nv.inputs[0])
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(nv.outputs[0], sx.inputs[0])
    mr = N.new("ShaderNodeMapRange"); L.new(sx.outputs[axis], mr.inputs[0]); mr.inputs[1].default_value = -1; mr.inputs[2].default_value = 1
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(mr.outputs[0], mx.inputs["Factor"])
    mx.inputs[6].default_value = (*colA, 1); mx.inputs[7].default_value = (*colB, 1)
    col = mx.outputs[2]
    if disc:                                             # oldingi yorug' dog' (qorachiqdan kiruvchi nur)
        dcol, dpow, dk = disc
        p = _m(N, L, "POWER", _m(N, L, "MAXIMUM", _m(N, L, "MULTIPLY", sx.outputs[1], -1.0), 0.0), dpow)
        ad = N.new("ShaderNodeMix"); ad.data_type = "RGBA"; ad.blend_type = "ADD"; L.new(_m(N, L, "MULTIPLY", p, dk), ad.inputs["Factor"])
        L.new(col, ad.inputs[6]); ad.inputs[7].default_value = (*dcol, 1); col = ad.outputs[2]
    L.new(col, em.inputs["Color"]); L.new(em.outputs[0], out.inputs[0])
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.data.materials.append(m); o.parent = parent
    for p in o.data.polygons: p.use_smooth = True
    o.visible_shadow = False
    return o
backdrop("sec_bg", 14, sec, (0.004, 0.006, 0.012), (0.03, 0.045, 0.08))
vis(sec, rng("section", "beam", "retina", "section_end"))
vis(beam, rng("beam", "retina"))          # bola: ota vis() dan keyin

# ======================================================================
# 3) GEL ICHIDA (x = 40): tolalar to'ri, suyuq pufakchalar, tugun
# ======================================================================
CC = Vector((40.0, 0, 0)); gin = empty("gel_in", CC)
backdrop("gel_bg", 6, gin, (0.006, 0.01, 0.02), (0.02, 0.03, 0.05), axis=2)
gel_bg = bpy.data.objects["gel_bg"]
# orqa (to'r parda) iliq rang, old tomonda qorachiq nuri: alohida gradient (y o'qi bo'ylab)
gm = gel_bg.data.materials[0]; N = gm.node_tree.nodes; L = gm.node_tree.links
mr = next(n for n in N if n.type == "MAP_RANGE"); sx = next(n for n in N if n.type == "SEPXYZ")
L.new(sx.outputs[1], mr.inputs[0])
mx = next(n for n in N if n.type == "MIX" and n.blend_type == "MIX")
mx.inputs[6].default_value = (0.9, 0.85, 0.75, 1); mx.inputs[7].default_value = (0.5, 0.13, 0.05, 1)
crv = N.new("ShaderNodeFloatCurve")
L.new(mr.outputs[0], crv.inputs["Value"]); L.new(crv.outputs[0], mx.inputs["Factor"])
cm_ = crv.mapping; cm_.curves[0].points[0].location = (0, 0); cm_.curves[0].points[1].location = (1, 1)
cm_.curves[0].points.new(0.25, 0.75); cm_.update()
em_ = next(n for n in N if n.type == "EMISSION"); em_.inputs["Strength"].default_value = 1.0
M_fib2 = mat("fiber_in", (0.95, 0.97, 1.0), 0.3, emit=0.35, alpha=0.5)
M_fib2.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.9, 0.95, 1.0, 1)
M_fib2.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.5
M_clf = mat("fiber_clump", (0.95, 0.97, 1.0), 0.3, emit=0.35, alpha=0.6)
cb_ = M_clf.node_tree.nodes["Principled BSDF"]
for f, col, em, al in ((1, (0.95, 0.97, 1.0), 0.35, 0.6), (S["clump"][0] + 20, (0.95, 0.97, 1.0), 0.35, 0.6),
                       (S["clump"][1] - 8, (0.05, 0.045, 0.04), 0.0, 0.95)):
    cb_.inputs["Base Color"].default_value = (*col, 1); cb_.inputs["Base Color"].keyframe_insert("default_value", frame=f)
    cb_.inputs["Emission Strength"].default_value = em; cb_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    cb_.inputs["Alpha"].default_value = al; cb_.inputs["Alpha"].keyframe_insert("default_value", frame=f)
CLUMP_C = Vector((0.0, 0.6, 0.0))
G0, G1 = S["gel_inside"][0], S["clump"][1]
NP = 7
fibers_in = []
for i in range(46):
    c = Vector((random.uniform(-1.4, 1.4), random.uniform(-1.2, 2.4), random.uniform(-1.3, 1.3)))
    d = Vector((random.uniform(-0.35, 0.35), 1.0, random.uniform(-0.35, 0.35))).normalized()
    ln = random.uniform(1.2, 2.4)
    base = [c + d * (ln * (j / (NP - 1) - 0.5)) for j in range(NP)]
    near = (c - CLUMP_C).length < 1.25 and len([f_ for f_ in fibers_in if f_[2]]) < 14
    o = curve_obj(f"fiberC{i}", base, random.uniform(0.004, 0.009), M_clf if near else M_fib2, gin)
    fibers_in.append((o, base, near, random.uniform(0, 6.28)))
def ease(t): t = min(1, max(0, t)); return t * t * (3 - 2 * t)
CL0, CL1 = S["clump"][0] + 6, S["clump"][1] - 6
for o, base, near, ph in fibers_in:
    tw = random.uniform(0, 6.28); k = 0
    for f in list(range(G0, G1 + 1, 6)) + [G1]:
        w = 0.035 * math.sin(f * 0.05 + ph)
        pts = [p + Vector((w * math.sin(j + ph), 0.0, w * math.cos(j * 1.3 + ph))) for j, p in enumerate(base)]
        if near:
            t = ease((f - CL0) / (CL1 - CL0))
            tgt = []
            for j in range(NP):
                s = j / (NP - 1) - 0.5
                a = tw + s * 5.0
                tgt.append(CLUMP_C + Vector((0.06 * math.cos(a) + 0.03 * math.sin(s * 9), s * 0.7, 0.06 * math.sin(a))))
            pts = [p.lerp(q, t) for p, q in zip(pts, tgt)]
        set_curve(o, f, pts)
# mayda zarralar (chuqurlik hissi)
M_spec = mat("speck", (1, 0.97, 0.9), 0.5, emit=1.5, alpha=0.7)
for i in range(120):
    p = Vector((random.uniform(-1.6, 1.6), random.uniform(-1.5, 3.0), random.uniform(-1.6, 1.6)))
    s = sphere(f"speck{i}", random.uniform(0.002, 0.006), tuple(p), M_spec, sub=1, parent=gin)
# suyuq pufakchalar (gel suyuqlashadi)
M_pocket = glass("pocket", (0.92, 0.97, 1.0), 1.12, 0.0)
pb_ = M_pocket.node_tree.nodes["Principled BSDF"]
pb_.inputs["Emission Color"].default_value = (0.6, 0.8, 1.0, 1); pb_.inputs["Emission Strength"].default_value = 0.05
L0 = S["liquefy"][0]
POCKETS = [((0.15, 0.55, 0.05), 0.32, 0), ((-0.45, 0.9, 0.35), 0.22, 6), ((0.55, 0.2, -0.3), 0.18, 10), ((-0.2, 0.3, -0.45), 0.15, 14),
           ((0.4, 1.2, 0.45), 0.26, 4), ((-0.6, 0.0, 0.0), 0.12, 18), ((0.05, 1.5, -0.4), 0.2, 8)]
pockets = []
for k, (p, r, d) in enumerate(POCKETS):
    o = sphere(f"pocket{k}", 1.0, p, M_pocket, sub=4, parent=gin)
    for f, s in ((1, 0.001), (L0 + d, 0.001), (L0 + d + 30, r * 0.8), (L0 + d + 60, r), (S["clump"][1], r * 1.08)):
        key(o, f, scale=(s, s * 0.92, s))
    interp(o, "BEZIER", "scale")
    pockets.append(o)
vis(gin, rng("gel_inside", "liquefy", "clump"))

# ======================================================================
# 4) KO'CHA / BOG' (x = -100): POV osmon, osmonga qarash, chang, ishqalash
# ======================================================================
CE = Vector((-100.0, 0, 0)); park = empty("park", CE)
M_grass = pbr("grass", "sparse_grass", 0.35, tint=(0.8, 0.95, 0.65))
M_conc = pbr("conc", "concrete_pavement", 0.5)
plane("park_ground", (300, 300), (0, 0, -0.01), M_grass, parent=park)
box("park_path", (40, 2.2, 0.04), (0, 0.4, 0.0), M_conc, parent=park)
M_bark = mat("bark", (0.2, 0.13, 0.08), 0.9); M_leaf = mat("leaves", (0.12, 0.3, 0.08), 0.7, sss=0.1)
def tree(x, y, s=1.0):
    cyl("trunk", 0.14 * s, 2.6 * s, (x, y, 1.3 * s), M_bark, parent=park, verts=16)
    for dx, dy, dz, r in ((0, 0, 3.2, 1.4), (0.8, 0.3, 2.8, 1.0), (-0.7, -0.3, 2.9, 1.1), (0.1, 0.5, 4.0, 1.0), (-0.3, 0.6, 3.6, 0.9)):
        o = sphere("crown", r * s, (x + dx * s, y + dy * s, dz * s), M_leaf, sub=3, parent=park)
        dm = o.modifiers.new("d", "DISPLACE"); dm.strength = 0.45 * s
        t = bpy.data.textures.new("cl", "CLOUDS"); t.noise_scale = 0.35; dm.texture = t
for x, y, s in ((2.6, 2.6, 1.2), (-3.5, 3.5, 1.1), (-8, 9, 1.4), (7, 10, 1.3), (12, 4, 1.0), (-13, 5, 1.2), (4, 16, 1.5),
                (-6, -9, 1.2), (6, -12, 1.4), (-1, 22, 1.6)):
    tree(x, y, s)
for i in range(7):                                       # butalar
    o = sphere("bush", 0.6, (-6 + i * 2.1, 2.2 + 0.4 * (i % 2), 0.35), M_leaf, scale=(1.3, 1, 0.7), sub=3, parent=park)
    dm = o.modifiers.new("d", "DISPLACE"); dm.strength = 0.25; t = bpy.data.textures.new("cb", "CLOUDS"); t.noise_scale = 0.3; dm.texture = t
# chang zarralari (quyosh nurida)
M_dust = mat("dust", (1.0, 0.85, 0.6), 0.5, emit=3.0)
dust = empty("dust", (0, 0, 0), park)
dps = []
for i in range(90):
    p0 = Vector((random.uniform(-0.6, 0.6), random.uniform(-1.0, 0.2), random.uniform(1.0, 2.0)))
    d = sphere(f"dust{i}", random.uniform(0.0008, 0.002), tuple(p0), M_dust, sub=1, parent=dust)
    v = Vector((random.uniform(-0.004, 0.004), random.uniform(-0.002, 0.002), random.uniform(-0.003, 0.001)))
    for f in (S["rub_dust"][0], S["rub_dust"][1]):
        key(d, f, loc=tuple(p0 + v * (f - S["rub_dust"][0])))
    interp(d, "LINEAR")
vis(park, rng("pov_sky", "look_sky", "rub_dust", "pov_sky2", "rub_hard"))
vis(dust, rng("rub_dust"))

# ======================================================================
# 5) MEHMONXONA (x = -150): Poly Haven mebel, kechqurun
# ======================================================================
CF = Vector((-150.0, 0, 0)); room = empty("room", CF)
M_floor = pbr("ph_floor", "laminate_floor_02", 0.5)
M_wall = pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.95, 0.86, 0.74))
plane("r_floor", (6, 6), (0, 1.5, 0), M_floor, parent=room)
plane("r_ceil", (6, 6), (0, 1.5, 2.7), mat("r_ceil", (0.85, 0.83, 0.8), 0.9), rot=(180, 0, 0), parent=room)
for nm, sz, loc, rot in (("rw_s", (6, 2.7), (0, -1.5, 1.35), (90, 0, 0)), ("rw_e", (6, 2.7), (3, 1.5, 1.35), (90, 0, 90)),
                         ("rw_w", (6, 2.7), (-3, 1.5, 1.35), (90, 0, 90))):
    plane(nm, sz, loc, M_wall, rot=rot, parent=room)
# orqa devor derazasi bilan
for nm, sz, loc in (("rw_nl", (2.1, 2.7), (-1.95, 4.5, 1.35)), ("rw_nr", (2.1, 2.7), (1.95, 4.5, 1.35)),
                    ("rw_nb", (1.8, 0.9), (0, 4.5, 0.45)), ("rw_nt", (1.8, 0.5), (0, 4.5, 2.45))):
    plane(nm, sz, loc, M_wall, rot=(90, 0, 0), parent=room)
plane("r_window", (1.8, 1.3), (0, 4.65, 1.55), mat("dusk", (0.25, 0.4, 0.8), emit=4.0), rot=(90, 0, 0), parent=room)
M_trim = mat("trim", (0.92, 0.92, 0.9), 0.4)
for x in (-0.9, 0.0, 0.9): box("wframe", (0.05, 0.12, 1.3), (x, 4.5, 1.55), M_trim, parent=room)
box("wframe_h", (1.8, 0.12, 0.05), (0, 4.5, 1.55), M_trim, parent=room)
for x in (-1.15, 1.15):
    c = box("curtain", (0.5, 0.06, 2.3), (x, 4.38, 1.4), mat("curtain", (0.8, 0.72, 0.6), 0.9), parent=room)
    d = c.modifiers.new("wave", "WAVE"); d.height = 0.04; d.width = 0.15; d.narrowness = 1; d.use_y = False; d.speed = 0
def ph_model(nm, loc, rz=0.0, s=1.0):
    r_ = empty(nm + "_grp", loc, room); r_.rotation_euler.z = R(rz); r_.scale = (s,) * 3
    import_glb(PH + f"{nm}/{nm}.gltf", r_); return r_
ph_model("Sofa_01", (-0.3, 3.75, 0), 0)
ph_model("modern_coffee_table_01", (-0.3, 2.85, 0), 0)
ph_model("potted_plant_01", (-2.4, 3.9, 0), 0, 1.3)
ph_model("fancy_picture_frame_01", (-2.2, 4.42, 1.5), 0)
cyl("lamp_pole", 0.015, 1.5, (2.2, 3.9, 0.75), mat("brass", (0.85, 0.65, 0.3), 0.25, metal=1.0), parent=room)
cyl("lamp_shade", 0.22, 0.32, (2.2, 3.9, 1.55), mat("shade", (1.0, 0.8, 0.55), 0.6, emit=4.0), parent=room)
box("rug", (2.8, 1.9, 0.01), (-0.2, 2.4, 0.005), mat("rug", (0.5, 0.18, 0.12), 0.95), parent=room)
area("room_lamp", tuple(CF + Vector((2.0, 3.6, 1.7))), 0.6, (1.0, 0.72, 0.45), lights_for(rng("room_tired"), 120))
area("room_window", tuple(CF + Vector((0, 4.3, 1.6))), 1.6, (0.55, 0.7, 1.0), lights_for(rng("room_tired"), 60))
vis(room, rng("room_tired"))

# ======================================================================
# 6) HAMMOM (x = -50)
# ======================================================================
CG = Vector((-50.0, 0, 0)); bath = empty("bath", CG)
M_tile = pbr("tiles", "long_white_tiles", 0.8, tint=(0.95, 0.95, 0.92))
plane("bath_floor", (3.2, 3.2), (0, 0, 0), pbr("marble", "marble_tiles", 0.7), parent=bath)
plane("bath_ceil", (3.2, 3.2), (0, 0, 2.6), mat("ceil", (0.8, 0.8, 0.78), 0.9), rot=(180, 0, 0), parent=bath)
for nm, sz, loc, rot in (("wall_n", (3.2, 2.6), (0, 1.6, 1.3), (90, 0, 0)), ("wall_s", (3.2, 2.6), (0, -1.6, 1.3), (90, 0, 0)),
                         ("wall_e", (3.2, 2.6), (1.6, 0, 1.3), (90, 0, 90)), ("wall_w", (3.2, 2.6), (-1.6, 0, 1.3), (90, 0, 90))):
    plane(nm, sz, loc, M_tile, rot=rot, parent=bath)
sink_root = empty("sink_root", (0, 1.32, 0), bath)
sk = import_glb(BK + "a541b293_u.glb", sink_root)
sink_root.rotation_euler = (0, 0, R(180)); sink_root.scale = (0.85, 0.85, 1.0)
plane("mirror", (1.0, 0.85), (0, 1.578, 1.55), mat("mirror", (0.92, 0.92, 0.92), 0.0, metal=1.0), rot=(90, 0, 0), parent=bath)
box("mirror_frame", (1.06, 0.02, 0.91), (0, 1.595, 1.55), mat("frame", (0.05, 0.05, 0.05), 0.4), parent=bath)
box("mirror_lamp", (0.7, 0.05, 0.05), (0, 1.55, 2.05), mat("lamp", (1, 0.85, 0.65), emit=12), parent=bath)
area("bath_ceil_light", tuple(CG + Vector((0, 0.2, 2.5))), 1.0, (1, 0.9, 0.78), lights_for(rng("wash"), 300))
vis(bath, rng("wash"))

# ======================================================================
# 7) QAHRAMON: Megan
# ======================================================================
groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
sc.render.fps = 24
for o in gmesh:
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                n.inputs["Specular IOR Level"].default_value = 0.3
                for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                n.inputs["Roughness"].default_value = 0.6       # sochda ham: quyoshda oq dog' bo'lmasin
                n.inputs["Coat Weight"].default_value = 0.0
A = lambda f, inplace=True: mc.load_action(f, inplace)
def at(f, loc, rz):
    groot.location = loc; groot.rotation_euler = (0, 0, R(rz))
    groot.keyframe_insert("location", frame=f); groot.keyframe_insert("rotation_euler", frame=f)
at(1, tuple(CE + Vector((0, 0.4, 0.04))), 0)
at(S["room_tired"][0], tuple(CF + Vector((0.35, 2.15, 0))), 0)
at(S["rub_hard"][0], tuple(CE + Vector((0, 0.4, 0.04))), 0)
at(S["wash"][0], tuple(CG + Vector((0, 0.86, 0))), 180)
interp(groot, "CONSTANT")
LOOK_OFF = int(os.environ.get("LOOK_OFF", 30))
mc.add_strip(girl, A("Looking_3.fbx"), S["look_sky"][0] - LOOK_OFF, blend=0, speed=0.9)
# Crying: qo'llar ko'zda, yuz oldinga qaragan bo'lak asl ~45-80-kadr (90+ da bosh buriladi) -> sekinlashtirib qo'yamiz
mc.add_strip(girl, A("Crying.fbx"), S["rub_dust"][0], blend=0, speed=0.55, src=(48, 78))
mc.add_strip(girl, A("Crying.fbx"), S["room_tired"][0], blend=0, speed=0.8, src=(40, 90))
mc.add_strip(girl, A("Crying.fbx"), S["rub_hard"][0], blend=0, speed=0.65, src=(52, 80))
mc.add_strip(girl, A("Crying.fbx"), S["wash"][0], blend=0, speed=0.55, src=(48, 80))
sc.render.fps = 24
vis(groot, rng("look_sky", "rub_dust", "room_tired", "rub_hard", "wash"))
headE = empty("girl_head")
c = headE.constraints.new("CHILD_OF"); c.target = girl; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
faceT = empty("girl_face_t", (0, 0.09, 0.09), headE)
eyeT_g = empty("girl_eye_t", (-0.032, 0.1, 0.1), headE)

# suv sachrashi (hammom): tomchilar yuzdan rakovinaga
WS0, WS1 = S["wash"]
splash = empty("splash", (0, 0, 0))
sc.frame_set(WS0 + 8); bpy.context.view_layer.update()
face_w = faceT.matrix_world.translation.copy()
for i in range(55):
    t0 = WS0 + random.randint(0, 30)
    p0 = face_w + Vector((random.uniform(-0.07, 0.07), random.uniform(0.0, 0.06), random.uniform(-0.1, 0.03)))
    v = Vector((random.uniform(-0.9, 0.9), random.uniform(0.3, 1.2), random.uniform(-0.3, 1.0)))
    d = sphere(f"wdrop{i}", random.uniform(0.002, 0.005), tuple(p0), M_water, sub=2, parent=splash)
    for f in range(WS0, WS1 + 1, 2):
        tt = max(0, (f - t0) / 24)
        p = p0 + v * tt + Vector((0, 0, -4.9 * tt * tt))
        if p.z < face_w.z - 0.75: p.z = face_w.z - 0.75
        key(d, f, loc=tuple(p))
    vis(d, [(t0, WS1)], False)
vis(splash, rng("wash"), False)

# ======================================================================
# 8) KAMERALAR
# ======================================================================
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c

# --- POV osmon + suzuvchilar (kamera bolasi) ---
M_float = mat("floater", (0.03, 0.035, 0.04), 0.6, alpha=0.42)
def pov_cam(name, f0, f1, yaw_keys, pitch=52, seed=1):
    c = shot_cam(name, tuple(CE + Vector((0, 0.4, 1.62))), None, 26, 2.0, focus=1.1)
    c.rotation_mode = "XYZ"
    for f, yaw, pt in yaw_keys:
        key(c, f, rot=(90 + pitch + pt, 0, yaw))
    interp(c, "LINEAR", "rotation")
    grp = empty(name + "_floaters", (0, 0, 0), c)
    rnd = random.Random(seed)
    for i in range(7):                                 # iplar
        x0, y0 = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.55, 0.55); ln = rnd.uniform(0.15, 0.45); a0 = rnd.uniform(0, 6.28)
        pts = [Vector((x0 + ln * (j / 6) * math.cos(a0) + 0.03 * math.sin(j * 1.7 + i), y0 + ln * (j / 6) * math.sin(a0) + 0.03 * math.cos(j * 1.3 + i), -1.4))
               for j in range(7)]
        curve_obj(f"{name}_str{i}", pts, rnd.uniform(0.003, 0.007), M_float, grp)
    for i in range(16):                                # nuqtalar
        sphere(f"{name}_dot{i}", rnd.uniform(0.004, 0.014), (rnd.uniform(-0.38, 0.38), rnd.uniform(-0.65, 0.65), -1.4), M_float,
               scale=(1, 1, 0.3), sub=2, parent=grp)
    # ko'z sakraganda suzuvchilar ortda qolib, keyin yetib keladi (inersiya)
    prev = yaw_keys[0][1]; key(grp, f0, loc=(0, 0, 0))
    for f, yaw, pt in yaw_keys[1:]:
        dy = yaw - prev
        if abs(dy) > 0.5:
            key(grp, f, loc=(0.012 * dy, 0.004 * pt, 0)); key(grp, f + 8, loc=(-0.004 * dy, 0, 0)); key(grp, f + 16, loc=(0, -0.01, 0))
        prev = yaw
    key(grp, f1, loc=(0.01, -0.06, 0))
    interp(grp, "BEZIER", "location")
    vis(grp, [(f0, f1)])
    return c
P0, P1 = S["pov_sky"]
pov_cam("pov_sky", P0, P1, [(1, 6, 0), (16, 6, 0), (19, -6, 3), (34, -6, 3), (37, 2, -2), (49, 3, -2)], seed=3)
P0, P1 = S["pov_sky2"]
pov_cam("pov_sky2", P0, P1, [(P0, -4, 0), (P0 + 14, -4, 0), (P0 + 17, 7, 2), (P1, 8, 2)], seed=5)
# 2 osmonga qarash: pastdan 16 mm
c = shot_cam("look_sky", (0, 0, 0), faceT, 16, 5.6)
key(c, S["look_sky"][0], loc=tuple(CE + Vector((0.55, -0.85, 0.28)))); key(c, S["look_sky"][1], loc=tuple(CE + Vector((0.3, -0.7, 0.4))))
# 3 makro ko'z sakrashi
eyeT = empty("eyeT", (0, -0.012, 0))
c = shot_cam("eye_dart", (0, 0, 0), eyeT, 50, 8.0, focus=eyeT)
key(c, S["eye_dart"][0], loc=(0.006, -0.1, 0.004)); key(c, S["eye_dart"][1], loc=(0.002, -0.075, 0.002))
# 4 chang: yuzga yaqin, DOF
c = shot_cam("rub_dust", (0, 0, 0), faceT, 70, 2.0)
key(c, S["rub_dust"][0], loc=tuple(CE + Vector((-0.3, -0.75, 1.2)))); key(c, S["rub_dust"][1], loc=tuple(CE + Vector((-0.2, -0.6, 1.25))))
# 5 mehmonxona: pastdan keng
c = shot_cam("room_tired", (0, 0, 0), faceT, 20, 4.0)
key(c, S["room_tired"][0], loc=tuple(CF + Vector((-1.3, -0.7, 0.6)))); key(c, S["room_tired"][1], loc=tuple(CF + Vector((-0.95, -0.15, 0.7))))
# 6 qorachiqqa sho'ng'ish
DV0, DV1 = S["eye_dive"]
c = shot_cam("eye_dive", (0, 0, 0), eyeT, 50, 9.0, focus=eyeT)
key(c, DV0, loc=(0.0, -0.11, 0.003)); key(c, DV0 + 30, loc=(0.0, -0.06, 0.001)); key(c, DV1, loc=(0.0, -0.0145, 0.0))
fc_ = [fc for fc in fcurves(c)]
for fc in fc_:
    for k in fc.keyframe_points: k.interpolation = "EXPO"; k.easing = "EASE_IN"
# 7 kesim ko'z: oldidan yon tomonga aylanib
secT = empty("secT", tuple(CB + Vector((-0.1, 0.0, 0.0))))
SC0, SC1 = S["section"]
c = shot_cam("section", (0, 0, 0), secT, 32, 5.6, focus=secT)
for f, p in ((SC0, (0.02, -2.0, 0.02)), (SC0 + 30, (1.4, -2.2, 0.5)), (SC1, (2.9, -0.7, 0.9))):
    key(c, f, loc=tuple(CB + Vector(p)))
interp(c, "BEZIER", "location")
# 8 gel ichida suzish
gT = empty("gT", tuple(CC + Vector((0.0, 1.6, 0.0))))
c = shot_cam("gel_inside", (0, 0, 0), gT, 24, 2.2, focus=1.0)
key(c, S["gel_inside"][0], loc=tuple(CC + Vector((0.35, -2.0, 0.15)))); key(c, S["gel_inside"][1], loc=tuple(CC + Vector((0.05, -0.6, -0.05))))
# 9 suyuqlashish
lT = empty("lT", tuple(CC + Vector((0.12, 0.55, 0.05))))
c = shot_cam("liquefy", (0, 0, 0), lT, 32, 2.8, focus=lT)
key(c, S["liquefy"][0], loc=tuple(CC + Vector((1.4, -0.5, 0.5)))); key(c, S["liquefy"][1], loc=tuple(CC + Vector((1.0, -0.15, 0.35))))
# 10 tugun
cT = empty("cT", tuple(CC + CLUMP_C))
c = shot_cam("clump", (0, 0, 0), cT, 40, 2.8, focus=cT)
key(c, S["clump"][0], loc=tuple(CC + Vector((-1.2, -0.3, 0.45)))); key(c, S["clump"][1], loc=tuple(CC + Vector((-0.6, 0.25, 0.2))))
# 11 nur: yon tomondan
bT = empty("bT", tuple(CB + Vector((-0.1, -0.2, 0.0))))
c = shot_cam("beam", (0, 0, 0), bT, 30, 5.6, focus=bT)
key(c, S["beam"][0], loc=tuple(CB + Vector((3.1, -1.2, 0.7)))); key(c, S["beam"][1], loc=tuple(CB + Vector((2.6, 0.2, 0.45))))
# 12 to'r pardadagi soya
rT = empty("rT", tuple(CB + Vector((-0.12, 0.86, 0.06))))
c = shot_cam("retina", (0, 0, 0), rT, 30, 4.0, focus=rT)
key(c, S["retina"][0], loc=tuple(CB + Vector((0.7, 0.05, 0.3)))); key(c, S["retina"][1], loc=tuple(CB + Vector((0.4, 0.3, 0.15))))
# 14 qattiq ishqalash: o'ta yaqin, silkinish
c = shot_cam("rub_hard", (0, 0, 0), faceT, 45, 4.0)
key(c, S["rub_hard"][0], loc=tuple(CE + Vector((0.22, -0.32, 1.2)))); key(c, S["rub_hard"][1], loc=tuple(CE + Vector((0.15, -0.24, 1.24))))
shake(c, S["rub_hard"][0], S["rub_hard"][1], 0.006, 4, decay=False)
# 15 yuz yuvish
c = shot_cam("wash", (0, 0, 0), faceT, 24, 3.2)
key(c, S["wash"][0], loc=tuple(CG + Vector((0.8, 1.2, 1.3)))); key(c, S["wash"][1], loc=tuple(CG + Vector((0.62, 1.15, 1.38))))
# 16 ho'l ko'z
c = shot_cam("eye_wet", (0, 0, 0), eyeT, 55, 9.0, focus=eyeT)
key(c, S["eye_wet"][0], loc=(-0.025, -0.085, 0.006)); key(c, S["eye_wet"][1], loc=(0.012, -0.08, 0.002))
# 17 yakun: kesim, orqaga chekinish
c = shot_cam("section_end", (0, 0, 0), secT, 40, 5.6, focus=secT)
key(c, S["section_end"][0], loc=tuple(CB + Vector((1.9, -0.25, 0.35)))); key(c, S["section_end"][1], loc=tuple(CB + Vector((3.4, -0.9, 1.0))))
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["pov_sky"]

# ======================================================================
# 9) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
tcw = N.new("ShaderNodeTexCoord"); mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
L.new(mpw.outputs[0], env.inputs[0]); L.new(env.outputs[0], N["Background"].inputs[0])
bg = N["Background"]
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2); sun.data.color = (1.0, 0.94, 0.85); sun.rotation_euler = (R(42), 0, R(-150))
OUTDOOR = {"pov_sky", "look_sky", "rub_dust", "pov_sky2", "rub_hard"}
for f, n in SHOTS:
    ws = 1.0 if n in OUTDOOR else (0.45 if n.startswith("eye") else 0.0)
    bg.inputs[1].default_value = ws; bg.inputs[1].keyframe_insert("default_value", frame=f)
    sun.data.energy = 3.5 if n in OUTDOOR else 0.0; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT"); interp(w.node_tree, "CONSTANT")
# makro ko'z
eye_on = rng(*EYE_SHOTS)
area("eye_key", (-0.09, -0.14, 0.11), 0.09, (1, 0.95, 0.9), lights_for(eye_on, 1.6), target=eA["root"])
area("eye_fill", (0.12, -0.1, -0.03), 0.12, (0.85, 0.9, 1.0), lights_for(eye_on, 0.5), target=eA["root"])
area("eye_rim", (0.05, 0.06, 0.09), 0.06, (0.6, 0.8, 1.0), lights_for(rng("eye_dive"), 1.5), target=eA["root"])
# kesim ko'z
sec_on = rng("section", "beam", "retina", "section_end")
secC = empty("secC", tuple(CB))
area("sec_key", tuple(CB + Vector((3.0, -2.5, 3.0))), 2.0, (1, 0.95, 0.9), lights_for(sec_on, 260), target=secC)
area("sec_rim", tuple(CB + Vector((-1.5, 2.8, 2.0))), 1.5, (0.5, 0.7, 1.0), lights_for(sec_on, 220), target=secC)
area("sec_fill", tuple(CB + Vector((3.0, 1.0, -1.5))), 1.5, (1.0, 0.85, 0.75), lights_for(sec_on, 60), target=secC)
spT = empty("spT", tuple(CB + Vector((-0.1, 1.0, 0.06))))
area("pupil_spot", tuple(CB + Vector((-0.1, -3.2, 0.06))), 0.01, (1.0, 0.93, 0.8),
     lights_for(rng("beam", "retina", "section_end"), 900), target=spT, spot=True)
sp_ = bpy.data.objects["pupil_spot"]; sp_.data.spot_size = R(9); sp_.data.spot_blend = 0.3
# gel ichida: oldingi yorug'lik (qorachiq) va iliq orqa
gel_on = rng("gel_inside", "liquefy", "clump")
area("gel_front", tuple(CC + Vector((0.0, -3.0, 0.3))), 1.5, (1.0, 0.95, 0.85), lights_for(gel_on, 260), target=gin)
area("gel_back", tuple(CC + Vector((0.5, 3.0, -0.5))), 2.0, (1.0, 0.35, 0.18), lights_for(gel_on, 160), target=gin)
# ko'cha: yuzga yumshoq to'ldiruvchi
area("face_fill", tuple(CE + Vector((-0.8, -1.2, 1.9))), 0.8, (1, 0.92, 0.85), lights_for(rng("rub_dust", "rub_hard", "look_sky"), 35), target=faceT)

# ======================================================================
# 10) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = False
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
