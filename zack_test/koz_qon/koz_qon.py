# Ko'zdagi qizil dog' (subkonyunktival qon quyilishi) — Zack D. Films uslubida 37 s video.
# Asos: zack_test/ebbi/ebbi.py + scene3.py + mixchar.py; makro ko'z: eye.py; tomir/rentgen: burish/parts.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=12 /tmp/claude-0/bvenv/bin/python -I zack_test/koz_qon/koz_qon.py --render
# Sinov: FRAMES=10,30,60,200,400 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "burish"))
from mathutils import Vector, Matrix, Quaternion, noise
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
random.seed(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
import eye as E
import parts as P
sc = bpy.context.scene
sc.render.fps = 24
END = 895
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, kadr = t*24+1) ----------------
SHOTS = [(1, "hook"), (19, "sneeze"), (47, "squat"), (82, "strain"), (113, "mirror_walk"), (142, "mirror_close"),
         (169, "eye_burst"), (216, "spot_orbit"), (248, "scared"), (294, "dive"), (365, "vessel_burst"), (411, "xray"),
         (473, "gauge"), (535, "eye_orbit"), (621, "vessel_burst2"), (689, "layers"), (769, "relief"), (827, "heal")]
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

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, sss=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
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

def import_ph(model, parent, loc=(0, 0, 0), rz=0.0, scale=1.0):
    root = empty(model + "_root", loc, parent); root.rotation_euler = (0, 0, R(rz)); root.scale = (scale,) * 3
    import_glb(os.path.join(PH, model, model + ".gltf"), root)
    return root

def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 600
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c

def shake(cam, f0, f1, amp, seed=1):
    rnd = random.Random(seed)
    fc = [fc for fc in fcurves(cam) if fc.data_path == "location"]
    for f in range(f0, f1):
        base = Vector([c.evaluate(f) for c in sorted(fc, key=lambda c: c.array_index)]) if fc else cam.location.copy()
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)

def lens_keys(cam, pairs):
    for f, l in pairs:
        cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None: l.constraints.new("TRACK_TO").target = target
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def bone_empty(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if loc != (0, 0, 0):
        e2 = empty(name + "_off", loc, e); return e2
    return e

def fit_on_floor(root, objs, target_h=None, target_w=None):
    mn, mx = bbox(objs)
    return mn, mx

# ======================================================================
# 1) MAKRO KO'Z (dunyo markazi), ko'z oqidagi 3D tomirlar
# ======================================================================
EYE_SHOTS = ["hook", "eye_burst", "spot_orbit", "dive", "eye_orbit", "heal"]
eA = E.build_eye("eyeA", (0, 0, 0))
vis(eA["root"], rng(*EYE_SHOTS))
W = eA["shape"].W; RE = eA["R"]
C = Vector(E.HEMO_C).normalized()
SPOT = C * (RE * 1.002)                         # dog' markazi (ko'z mahalliy, sirtda)

def hemo(pairs):
    """(kadr, radius, alfa, sariqlik)"""
    for f, r, a, y in pairs:
        E.key_value(eA["hemo_r"], f, r); E.key_value(eA["hemo_a"], f, a); E.key_value(eA["hemo_y"], f, y)
B0 = S["eye_burst"][0] + 9                     # "to'satdan" (7.02 s)
H0, H1 = S["heal"]
hemo([(1, 0.30, 1.0, 0.0), (S["hook"][1], 0.30, 1.0, 0.0),
      (S["eye_burst"][0], 0.0, 0.0, 0.0), (B0, 0.0, 0.0, 0.0), (B0 + 2, 0.10, 1.0, 0.0), (B0 + 7, 0.24, 1.0, 0.0),
      (B0 + 22, 0.30, 1.0, 0.0), (S["spot_orbit"][1], 0.33, 1.0, 0.0),
      (S["dive"][0], 0.0, 0.0, 0.0), (S["eye_orbit"][1], 0.0, 0.0, 0.0),
      (H0, 0.33, 1.0, 0.0), (H0 + 14, 0.31, 1.0, 0.15), (H0 + 30, 0.24, 0.85, 0.55), (H0 + 48, 0.15, 0.5, 0.9), (H1 - 8, 0.0, 0.0, 1.0)])
E.key_value(eA["red"], 1, 0.25); E.key_value(eA["red"], S["dive"][0], 0.55); E.key_value(eA["red"], S["heal"][0], 0.3)
E.key_value(eA["red"], H1, 0.12)

def keyset(eye, k, pairs):
    for f, v in pairs: E.set_key(eye, k, f, v)
blink = [(1, 0.0)]
for fb in (S["eye_burst"][0] + 4, S["eye_orbit"][0] + 40, H1 - 12):
    blink += [(fb - 1, 0.0), (fb + 2, 1.0), (fb + 5, 0.0)]
keyset(eA, "blink", blink)
keyset(eA, "wide", [(1, 0.0), (B0, 0.0), (B0 + 4, 0.7), (S["spot_orbit"][1], 0.5), (S["dive"][0], 0.2), (S["heal"][0], 0.0)])
ball = eA["ball"]
# ko'z olmasi qorachig'i biroz ichkariga (burun tomonga) qaraydi: dog' ko'proq ko'rinadi
for f, rx, rz in ((1, 0, -12), (S["eye_burst"][0], 0, -6), (B0 + 3, -3, -14), (S["dive"][0], 0, -14), (S["eye_orbit"][0], 0, -10),
                  (S["eye_orbit"][0] + 50, 3, -16), (S["heal"][0], 0, -12), (H0 + 30, 2, -8), (H0 + 45, 0, -12)):
    key(ball, f, rot=(rx, 0, rz))
interp(ball, "CONSTANT")

# 3D kapillyarlar (ko'z olmasiga yopishgan ingichka quvurlar)
M_cap = mat("capillary", (0.42, 0.02, 0.025), 0.35, sss=0.4, coat=0.5)
M_cap.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.0002
def on_ball(d, lift):
    d = d.normalized(); return d * (RE + lift)
rnd = random.Random(21)
def walk(start, heading, n, step, r0, depth=0):
    pts = [start]; p = start.copy(); h = heading.normalized()
    for i in range(n):
        nrm = p.normalized(); h = (h - nrm * h.dot(nrm)).normalized()
        side = nrm.cross(h)
        h = (h + side * rnd.uniform(-0.45, 0.45)).normalized()
        p = on_ball(p + h * step, 0.00005); pts.append(p)
        if p.y > -0.15 * RE: break
    tp = [max(0.25, 1 - i / len(pts)) for i in range(len(pts))]
    t = P.tube(f"cap_{len(bpy.data.objects)}", [tuple(x) for x in pts], r0, M_cap, parent=ball, taper=tp)
    if depth < 2:
        for k in range(rnd.randint(1, 2)):
            j = rnd.randint(2, max(2, len(pts) - 3))
            if j < len(pts) - 1:
                nh = (pts[j + 1] - pts[j]).normalized(); side = pts[j].normalized().cross(nh)
                walk(pts[j], nh + side * rnd.choice((-1, 1)) * 0.9, n // 2, step * 0.8, r0 * 0.6, depth + 1)
    return pts
VESSELS = []
for k in range(9):           # tashqi (temporal) tomondan qorachiq tomonga yo'nalgan asosiy tomirlar
    a = R(-40 + k * 10)
    d0 = Vector((math.cos(a) * 0.98, -0.2, math.sin(a) * 0.98))
    st = on_ball(d0 + Vector((0, -0.05, 0)), 0.00005)
    VESSELS.append(walk(st, Vector((-1, -0.6, -st.z * 30)), 26, 0.00055, 0.000085))
for k in range(5):           # ichki (burun) tomon
    a = R(160 + k * 12)
    d0 = Vector((math.cos(a) * 0.98, -0.2, math.sin(a) * 0.98))
    st = on_ball(d0, 0.00005)
    walk(st, Vector((1, -0.6, -st.z * 30)), 20, 0.00055, 0.00007)
# sho'ng'ish nishoni: dog' markaziga eng yaqin tomir nuqtasi
best = min((p for v in VESSELS for p in v), key=lambda p: (p.normalized() - C).length)
DIVE_PT = best.copy()

# ======================================================================
# 2) TOMIR KESIMI (x = 5): katta qilib ko'rsatilgan kapillyar, qon tanachalari, yorilish
# ======================================================================
VX = Vector((5.0, 0, 0)); vroot = empty("vessel_root", tuple(VX))
VR = 0.05; VL = 3.0
M_wall = bpy.data.materials.new("vessel_wall"); M_wall.use_nodes = True
N = M_wall.node_tree.nodes; L = M_wall.node_tree.links; b = N["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.95, 0.42, 0.38, 1); b.inputs["Roughness"].default_value = 0.15
b.inputs["Coat Weight"].default_value = 0.8; b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.01
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 8.0
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
# devor kuchlanishi: VSTRESS qiymati bilan qizarib yonadi
vstress = E.value_node(M_wall, "VSTRESS", 0.0)
b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.05, 1)
L.new(E._math(N, L, "MULTIPLY", vstress.outputs[0], 0.6), b.inputs["Emission Strength"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
opac = E._math(N, L, "ADD", 0.08, E._math(N, L, "MULTIPLY", lw.outputs["Facing"], 0.8), clamp=True)
trn = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader")
L.new(opac, ms.inputs[0]); L.new(trn.outputs[0], ms.inputs[1]); L.new(b.outputs[0], ms.inputs[2])
out = next(n for n in N if n.type == "OUTPUT_MATERIAL"); L.new(ms.outputs[0], out.inputs["Surface"])

def tube_mesh(name, r, length, nx=160, nr=48):
    V = []; F = []
    for i in range(nx + 1):
        x = -length / 2 + length * i / nx
        for j in range(nr):
            a = 2 * math.pi * j / nr; V.append((x, r * math.cos(a), r * math.sin(a)))
    for i in range(nx):
        for j in range(nr):
            a = i * nr + j; b_ = i * nr + (j + 1) % nr
            F.append((a, b_, b_ + nr, a + nr))
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o, nx, nr
wall, NXW, NRW = tube_mesh("vessel_wall", VR, VL)
wall.parent = vroot; wall.data.materials.append(M_wall)
wall.shape_key_add(name="Basis")
kb_b = wall.shape_key_add(name="bulge", from_mix=False); kb_b.value = 0.0
for i, v in enumerate(wall.data.vertices):
    x = v.co.x; w = math.exp(-(x / 0.16) ** 2)
    rr = Vector((0, v.co.y, v.co.z)); up = max(0.0, v.co.z / VR)
    kb_b.data[i].co = v.co + rr.normalized() * VR * w * (0.55 + 0.45 * up)
so = wall.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.004; so.offset = 0
# yirtilgan nusxa: tepa markazida notekis teshik, chetlari tashqariga qayrilgan
torn = wall.copy(); torn.data = wall.data.copy(); torn.name = "vessel_torn"; sc.collection.objects.link(torn); torn.parent = vroot
torn.shape_key_clear()
rnd2 = random.Random(7)
for i, v in enumerate(torn.data.vertices):
    v.co = kb_b.data[i].co.copy()
import bmesh
bm = bmesh.new(); bm.from_mesh(torn.data)
def hole_r(a): return 0.07 * (1 + 0.35 * math.sin(5 * a + 1.3) + 0.2 * math.sin(11 * a))
dele = []
for fce in bm.faces:
    c_ = fce.calc_center_median()
    if c_.z <= 0: continue
    a = math.atan2(c_.y, c_.x); d = math.hypot(c_.x, c_.y)
    if d < hole_r(a): dele.append(fce)
bmesh.ops.delete(bm, geom=dele, context="FACES")
for v in bm.verts:
    if v.co.z > 0:
        a = math.atan2(v.co.y, v.co.x); d = math.hypot(v.co.x, v.co.y); h = hole_r(a)
        if d < h * 1.6:
            k = (1 - (d - h) / (h * 0.6)) ** 2
            v.co += Vector((v.co.x, v.co.y, 0)).normalized() * k * 0.035 + Vector((0, 0, k * 0.03))
bm.to_mesh(torn.data); bm.free()

# qon tanachalari (eritrotsitlar): botiq disk
M_rbc = mat("rbc", (0.5, 0.012, 0.01), 0.3, sss=0.5, coat=0.4)
M_rbc.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.004
bpy.ops.mesh.primitive_torus_add(major_radius=0.0105, minor_radius=0.0062, major_segments=32, minor_segments=14)
rbc_proto = bpy.context.object; rbc_proto.name = "rbc_proto"; rbc_proto.scale = (1, 1, 0.75); bpy.ops.object.transform_apply(scale=True)
for p in rbc_proto.data.polygons: p.use_smooth = True
rbc_proto.data.materials.append(M_rbc)
bpy.ops.mesh.primitive_cylinder_add(radius=0.0105, depth=0.003, vertices=32)
mid = bpy.context.object; mid.data.materials.append(M_rbc)
mid.select_set(True); rbc_proto.select_set(True); bpy.context.view_layer.objects.active = rbc_proto; bpy.ops.object.join()
rbc_proto.hide_render = True; rbc_proto.hide_viewport = True
cells = []
VB1 = S["vessel_burst"][0] + 30                 # "yorilishidir" (16.08 s ~ kadr 387)
VB2 = S["vessel_burst2"][0] + 46                # "yorilib" (27.7 s ~ kadr 666)
HOLE = Vector((0, 0, VR * 1.5))
for k in range(70):
    o = bpy.data.objects.new(f"rbc{k}", rbc_proto.data); sc.collection.objects.link(o); o.parent = vroot
    o.rotation_mode = "XYZ"
    y = rnd2.uniform(-0.6, 0.6) * VR; z = rnd2.uniform(-0.6, 0.6) * VR
    x0 = rnd2.uniform(-1.45, 0.6); sp_ = rnd2.uniform(0.006, 0.009); rot0 = Vector((rnd2.uniform(0, 6), rnd2.uniform(0, 6), rnd2.uniform(0, 6)))
    spin = Vector((rnd2.uniform(-.06, .06), rnd2.uniform(-.06, .06), rnd2.uniform(-.06, .06)))
    escape = (abs(x0 + sp_ * 23) < 0.25) and k % 2 == 0            # yorilishda teshikdan otilib chiqadigan
    vel = Vector((rnd2.uniform(-0.25, 0.25), rnd2.uniform(-0.25, 0.25), rnd2.uniform(0.5, 1.0))) * 0.012
    for (s0, s1), burst in ((S["vessel_burst"], VB1), (S["vessel_burst2"], VB2)):
        for f in range(s0 - 1, s1 + 2, 2):
            t = f - s0
            p = Vector((x0 + sp_ * t, y, z))
            if f > burst and escape:
                tt = f - burst; p = Vector((x0 + sp_ * (burst - s0), y, z)) + vel * tt * (1 + 0.6 * tt / 20) + Vector((0, 0, VR * 0.8 * min(1, tt / 4)))
            o.location = p; o.keyframe_insert("location", frame=f)
            o.rotation_euler = rot0 + spin * t; o.keyframe_insert("rotation_euler", frame=f)
    cells.append(o)
# yorilishda sachragan qon tomchilari
M_blood = mat("blood", (0.5, 0.01, 0.01), 0.08, sss=0.3, coat=1.0)
drops = []
for k in range(90):
    o = sphere(f"vdrop{k}", rnd2.uniform(0.002, 0.006), (0, 0, 0), M_blood, sub=2, parent=vroot)
    d = Vector((rnd2.uniform(-1, 1), rnd2.uniform(-1, 1), rnd2.uniform(0.6, 2.0))).normalized() * rnd2.uniform(0.006, 0.02)
    st = Vector((rnd2.uniform(-0.04, 0.04), rnd2.uniform(-0.04, 0.04), VR * 1.4))
    for burst, s1 in ((VB1, S["vessel_burst"][1]), (VB2, S["vessel_burst2"][1])):
        o.location = st; o.keyframe_insert("location", frame=burst)
        for f in range(burst + 1, s1 + 2, 2):
            tt = f - burst; o.location = st + d * tt - Vector((0, 0, 0.00025 * tt * tt)); o.keyframe_insert("location", frame=f)
    drops.append(o)
# fon: pushti to'qima va mayda tomirlar (DOF da xira)
M_tis = bpy.data.materials.new("tissue_bg"); M_tis.use_nodes = True
N = M_tis.node_tree.nodes; L = M_tis.node_tree.links; b = N["Principled BSDF"]
wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 12.0; wv.inputs["Detail"].default_value = 6.0
cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.25, 0.03, 0.03, 1); cr.color_ramp.elements[1].color = (0.6, 0.18, 0.15, 1)
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.35
b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.02
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
plane("vessel_floor", (4, 3), tuple(VX + Vector((0, 0, -VR - 0.006))), M_tis)
plane("vessel_back", (4, 2), tuple(VX + Vector((0, 1.0, 0.3))), M_tis, rot=(90, 0, 0))
for k in range(10):
    yy = rnd2.uniform(-1.2, -0.25) * (1 if k % 2 else -1); x0 = rnd2.uniform(-1.5, 1.5)
    pts = [tuple(VX + Vector((x0 + t * 0.5, yy + 0.15 * math.sin(t * 2 + k), -VR + 0.01 + 0.02 * math.sin(t * 3)))) for t in range(-3, 4)]
    P.tube(f"vbg{k}", pts, rnd2.uniform(0.012, 0.03), M_wall)
vessel_objs = [vroot]
VBR = rng("vessel_burst", "vessel_burst2")
vis(vroot, VBR, False)
for o in vroot.children_recursive:
    if o not in [wall, torn] + drops: vis(o, VBR, False)
for o in [x for x in bpy.data.objects if x.name.startswith("vbg") or x.name in ("vessel_floor", "vessel_back")]: vis(o, VBR, False)
# shish va yorilish ketma-ketligi
def wall_keys(s0, burst, s1):
    for f, v in ((s0, 0.0), (burst - 22, 0.25), (burst - 16, 0.15), (burst - 10, 0.6), (burst - 6, 0.45), (burst - 1, 1.0)):
        kb_b.value = v; kb_b.keyframe_insert("value", frame=f)
        E.key_value(vstress, f, v * 2.5)
    E.key_value(vstress, burst + 1, 4.0); E.key_value(vstress, burst + 8, 0.6)
wall_keys(*S["vessel_burst"][:1], VB1, S["vessel_burst"][1])
wall_keys(S["vessel_burst2"][0], VB2, S["vessel_burst2"][1])
vis(wall, [(S["vessel_burst"][0], VB1), (S["vessel_burst2"][0], VB2)], False)
vis(torn, [(VB1 + 1, S["vessel_burst"][1]), (VB2 + 1, S["vessel_burst2"][1])], False)
for o in drops: vis(o, [(VB1 + 1, S["vessel_burst"][1]), (VB2 + 1, S["vessel_burst2"][1])], False)

# ======================================================================
# 3) QATLAM KESIMI (x = 10): ko'z oqi (sklera) + shaffof shilliq parda, orasiga qon yoyiladi
# ======================================================================
LX = Vector((10.0, 0, 0)); lroot = empty("layers_root", tuple(LX))
M_scl = bpy.data.materials.new("sclera_block"); M_scl.use_nodes = True
N = M_scl.node_tree.nodes; L = M_scl.node_tree.links; b = N["Principled BSDF"]
wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 9.0; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 8.0
cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.78, 0.7, 0.64, 1); cr.color_ramp.elements[1].color = (0.95, 0.92, 0.88, 1)
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.45
b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.01
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
box("sclera_block", (0.9, 0.6, 0.16), (0, 0, -0.08), M_scl, parent=lroot)      # parent fazosida (mahalliy)
M_conj = mat("conjunctiva", (0.98, 0.9, 0.9), 0.04, coat=1.0)
bc = M_conj.node_tree.nodes["Principled BSDF"]; bc.inputs["Transmission Weight"].default_value = 1.0; bc.inputs["IOR"].default_value = 1.1
bc.inputs["Alpha"].default_value = 0.55
conj = box("conjunctiva", (0.9, 0.6, 0.022), (0, 0, 0.022), M_conj, parent=lroot)
bv = conj.modifiers.new("bevel", "BEVEL"); bv.width = 0.004; bv.segments = 3
# parda va sklera orasidagi kapillyarlar
lv = []
for k in range(6):
    yy = -0.25 + k * 0.1; pts = [tuple(LX + Vector((x, yy + 0.03 * math.sin(x * 9 + k), 0.007))) for x in (-0.5, -0.3, -0.1, 0.1, 0.3, 0.5)]
    lv.append(P.tube(f"lcap{k}", pts, 0.0045 if k != 3 else 0.006, M_cap))
M_cap_big = M_cap.copy(); M_cap_big.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.004
for o in lv: o.data.materials[0] = M_cap_big
# qon dog'i: notekis chekkali yassi disk, kattalashadi
def blob_mesh(name, n=96):
    V = [(0, 0, 0)]; F = []
    for i in range(n):
        a = 2 * math.pi * i / n; r = 1 + 0.18 * math.sin(3 * a + 0.4) + 0.1 * math.sin(7 * a + 2) + 0.05 * math.sin(13 * a)
        V.append((r * math.cos(a), r * math.sin(a), 0))
    for i in range(n): F.append((0, 1 + i, 1 + (i + 1) % n))
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F)
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = 2; sd.render_levels = 2
    so = o.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.008; so.offset = 0
    for p in me.polygons: p.use_smooth = True
    return o
blob = blob_mesh("blood_blob"); blob.parent = lroot; blob.location = (0.02, 0.02, 0.006); blob.data.materials.append(M_blood)
L0, L1 = S["layers"]
for f, s_ in ((L0, 0.01), (L0 + 10, 0.02), (L0 + 30, 0.11), (L0 + 55, 0.2), (L1 + 1, 0.24)):
    blob.scale = (s_, s_ * 0.85, 1); blob.keyframe_insert("scale", frame=f)
    blob.rotation_euler = (0, 0, R((f - L0) * 0.15)); blob.keyframe_insert("rotation_euler", frame=f)
# sizib chiqayotgan tomchilar (yirtilgan tomirdan)
for k in range(24):
    o = sphere(f"ldrop{k}", rnd2.uniform(0.003, 0.006), (0, 0, 0), M_blood, scale=(1, 1, 0.5), sub=2, parent=lroot)
    a = rnd2.uniform(0, 6.283); d0 = rnd2.uniform(0.0, 0.02)
    for f, rr in ((L0, d0), (L1 + 1, d0 + rnd2.uniform(0.12, 0.2))):
        o.location = (0.02 + rr * math.cos(a), 0.02 + rr * math.sin(a) * 0.85, 0.007); o.keyframe_insert("location", frame=f)
plane("layers_back", (4, 3), tuple(LX + Vector((0, 1.2, 0.5))), mat("lback", (0.35, 0.22, 0.24), 0.8), rot=(90, 0, 0))
plane("layers_floor", (4, 4), tuple(LX + Vector((0, 0, -0.161))), mat("lfloor", (0.3, 0.2, 0.22), 0.8))
vis(lroot, rng("layers"))
for nm in ("layers_back", "layers_floor"): vis(bpy.data.objects[nm], rng("layers"), False)
for o in lv: vis(o, rng("layers"), False)

# ======================================================================
# 4) MANOMETR (x = 15)
# ======================================================================
GX = Vector((15.0, 0, 0)); groot = empty("gauge_root", tuple(GX))
groot.rotation_euler = (R(90), 0, 0)                 # yuzi -Y ga qaraydi
M_chrome = mat("chrome", (0.9, 0.9, 0.92), 0.12, metal=1.0)
M_face = mat("gauge_face", (0.95, 0.95, 0.93), 0.4)
M_black = mat("gauge_black", (0.02, 0.02, 0.02), 0.4)
M_redz = mat("gauge_red", (0.85, 0.03, 0.02), 0.35, emit=0.0)
M_glass = mat("gauge_glass", (1, 1, 1), 0.02); M_glass.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
GR = 0.1
bpy.ops.mesh.primitive_torus_add(major_radius=GR + 0.008, minor_radius=0.012, major_segments=96, minor_segments=24)
rim = bpy.context.object; rim.name = "gauge_rim"; rim.data.materials.append(M_chrome); rim.parent = groot
for p in rim.data.polygons: p.use_smooth = True
cyl("gauge_body", GR + 0.012, 0.05, (0, 0, -0.03), M_chrome, parent=groot, verts=96)
cyl("gauge_face", GR, 0.002, (0, 0, 0.0), M_face, parent=groot, verts=96)
cyl("gauge_glass", GR + 0.002, 0.004, (0, 0, 0.014), M_glass, parent=groot, verts=96)
A0, A1 = R(225), R(-45)                  # 0 .. 300 mmHg (soat yo'nalishida)
def ang(v): return A0 + (A1 - A0) * v / 300.0
for v in range(0, 301, 10):
    a = ang(v); big = v % 50 == 0
    l = 0.016 if big else 0.008
    t = box(f"tick{v}", (0.0025 if big else 0.0012, l, 0.001), (math.cos(a) * (GR - 0.01 - l / 2), math.sin(a) * (GR - 0.01 - l / 2), 0.0016),
            M_redz if v >= 200 else M_black, rot=(0, 0, math.degrees(a) - 90), parent=groot)
    if big:
        cu = bpy.data.curves.new(f"num{v}", "FONT"); cu.body = str(v); cu.size = 0.014; cu.align_x = "CENTER"; cu.align_y = "CENTER"
        cu.extrude = 0.0004
        to = bpy.data.objects.new(f"num{v}", cu); sc.collection.objects.link(to); to.parent = groot
        to.location = (math.cos(a) * (GR - 0.04), math.sin(a) * (GR - 0.04), 0.0016); cu.materials.append(M_redz if v >= 200 else M_black)
# qizil zona yoyi
bpy.ops.curve.primitive_bezier_circle_add(radius=GR - 0.006)
arc = bpy.context.object; arc.name = "red_arc"; arc.parent = groot; arc.location = (0, 0, 0.0014)
arc.data.bevel_depth = 0.0025; arc.data.materials.append(M_redz)
arc.data.bevel_factor_mapping_start = "SPLINE"; arc.data.bevel_factor_mapping_end = "SPLINE"
# bezier aylana 0 burchakdan soat strelkasiga qarshi boradi: -45..15 (200..300) zonasi
arc.data.bevel_factor_start = (360 - 45) / 360.0; arc.data.bevel_factor_end = 1.0
arc2 = arc.copy(); arc2.data = arc.data.copy(); sc.collection.objects.link(arc2); arc2.parent = groot
arc2.data.bevel_factor_start = 0.0; arc2.data.bevel_factor_end = 0.0            # 200 -> -45..(-45+...)
arc.data.bevel_factor_start = (360 - 45) / 360.0; arc.data.bevel_factor_end = 1.0
arc2.data.bevel_factor_start = 0.0; arc2.data.bevel_factor_end = 15.0 / 360.0
# 200 mmHg = ang(200) = 225 - 270*200/300 = 45 daraja -> 45..-45 oralig'i: arc (315..360) + arc2 (0..45)
arc2.data.bevel_factor_end = 45.0 / 360.0
cu = bpy.data.curves.new("mmhg", "FONT"); cu.body = "mmHg"; cu.size = 0.012; cu.align_x = "CENTER"
to = bpy.data.objects.new("mmhg", cu); sc.collection.objects.link(to); to.parent = groot; to.location = (0, -0.045, 0.0016)
cu.materials.append(M_black)
needle_piv = empty("needle_piv", (0, 0, 0.006), groot)
nd = box("needle", (0.0032, GR * 0.82, 0.0015), (0, GR * 0.82 / 2 - 0.012, 0), M_redz, parent=needle_piv)
nd.data.vertices[0].co.x *= 0.3
cyl("needle_cap", 0.009, 0.006, (0, 0, 0.007), M_black, parent=groot)
G0, G1 = S["gauge"]
GJ = G0 + 42                           # "keskin sakraydi" (21.4-21.7 s)
needle_piv.rotation_mode = "XYZ"
def needle(f, v):
    needle_piv.rotation_euler = (0, 0, ang(v) - R(90)); needle_piv.keyframe_insert("rotation_euler", frame=f)
for f, v in ((1, 120), (G0, 118), (G0 + 10, 124), (G0 + 20, 117), (G0 + 30, 126), (GJ - 3, 120), (GJ, 120), (GJ + 3, 290),
             (GJ + 5, 262), (GJ + 7, 284), (GJ + 9, 272), (GJ + 12, 280), (G1 + 1, 278)):
    needle(f, v)
b = M_redz.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (1, 0.05, 0.02, 1)
for f, e in ((1, 0.0), (GJ + 2, 0.0), (GJ + 3, 6.0), (GJ + 12, 1.5), (G1 + 1, 1.5)):
    b.inputs["Emission Strength"].default_value = e; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
# fon: qorong'i qizg'ish
plane("gauge_bg", (3, 3), tuple(GX + Vector((0, 0.6, 0))), mat("gbg", (0.08, 0.02, 0.02), 0.8), rot=(90, 0, 0))
vis(groot, rng("gauge"))
vis(bpy.data.objects["gauge_bg"], rng("gauge"), False)

# ======================================================================
# 5) XONALAR: mehmonxona (x=-30), sport zal (x=-60), hammom (x=-90)
# ======================================================================
M_plaster = pbr("plaster", "painted_plaster_wall", 0.6, tint=(0.93, 0.86, 0.76))
M_lam = pbr("laminate", "laminate_floor_02", 0.5)
LR = Vector((-30.0, 0, 0)); lroom = empty("living", tuple(LR))
plane("lr_floor", (6, 6), (0, 0, 0), M_lam, parent=lroom)
plane("lr_ceil", (6, 6), (0, 0, 2.7), mat("lr_ceil", (0.85, 0.84, 0.8), 0.9), rot=(180, 0, 0), parent=lroom)
for nm, sz, loc, rot in (("lr_n", (6, 2.7), (0, 2.2, 1.35), (90, 0, 0)), ("lr_s", (6, 2.7), (0, -2.6, 1.35), (90, 0, 0)),
                         ("lr_e", (6, 2.7), (2.4, 0, 1.35), (90, 0, 90)), ("lr_w", (6, 2.7), (-2.4, 0, 1.35), (90, 0, 90))):
    plane(nm, sz, loc, M_plaster, parent=lroom)
sofa = import_ph("Sofa_01", lroom, (0, 1.6, 0), 0)
plant = import_ph("potted_plant_01", lroom, (1.3, 1.75, 0), 0, 1.2)
frame_ = import_ph("fancy_picture_frame_01", lroom, (-0.2, 2.17, 1.55), 0, 1.6)
frame_.rotation_euler = (R(90), 0, 0)
table = import_ph("modern_coffee_table_01", lroom, (0.1, 0.75, 0), 0)
# deraza (yorug'lik manbai)
box("lr_window", (1.4, 0.02, 1.4), (-2.39, 0.3, 1.5), mat("win", (1, 0.97, 0.9), emit=6.0), rot=(0, 0, 90), parent=lroom)
vis(lroom, rng("sneeze"))

GY = Vector((-60.0, 0, 0)); gym = empty("gym", tuple(GY))
plane("gym_floor", (10, 10), (0, 0, 0), pbr("gym_floor_m", "concrete_floor_02", 0.4, tint=(0.55, 0.55, 0.58)), parent=gym)
box("gym_mat", (2.6, 2.6, 0.03), (0, 0.2, 0.015), mat("rubber", (0.03, 0.03, 0.035), 0.85), parent=gym)
M_gwall = pbr("gym_wall", "painted_plaster_wall", 0.5, tint=(0.25, 0.27, 0.3))
for nm, sz, loc, rot in (("gw_n", (10, 4), (0, 3.0, 2.0), (90, 0, 0)), ("gw_s", (10, 4), (0, -4.0, 2.0), (90, 0, 0)),
                         ("gw_e", (10, 4), (3.5, 0, 2.0), (90, 0, 90)), ("gw_w", (10, 4), (-3.5, 0, 2.0), (90, 0, 90))):
    plane(nm, sz, loc, M_gwall, parent=gym)
plane("gym_ceil", (10, 10), (0, 0, 4), mat("gceil", (0.1, 0.1, 0.1), 0.9), rot=(180, 0, 0), parent=gym)
M_led = mat("led", (1.0, 0.95, 0.9), emit=18.0)
for k in range(4):
    box(f"gym_led{k}", (0.12, 3.0, 0.04), (-1.5 + k, 0.0, 3.95), M_led, parent=gym)
M_steel = mat("steel", (0.6, 0.6, 0.62), 0.25, metal=1.0)
M_plate = mat("plate", (0.02, 0.02, 0.02), 0.5)
M_plate_red = mat("plate_red", (0.6, 0.03, 0.02), 0.4)
# shtanga stoyka va gantellar (fon)
for sx in (-1, 1):
    box(f"rack{sx}", (0.08, 0.08, 2.4), (sx * 0.8, 2.3, 1.2), M_steel, parent=gym)
for k in range(8):
    cyl(f"dumb{k}", 0.05 + 0.005 * k, 0.05, (-2.6 + k * 0.32, 2.6, 0.08), M_plate, rot=(90, 0, 0), parent=gym)
box("gym_mirror", (5, 0.02, 2.0), (0, 2.97, 1.4), mat("gmirror", (0.9, 0.9, 0.9), 0.02, metal=1.0), parent=gym)
vis(gym, rng("squat", "strain"))

BA = Vector((-90.0, 0, 0)); bath = empty("bath", tuple(BA))
M_tile = pbr("tiles", "long_white_tiles", 0.8, tint=(0.95, 0.95, 0.92))
M_floor = pbr("marble", "marble_tiles", 0.7)
plane("bath_floor", (3.2, 3.2), (0, 0, 0), M_floor, parent=bath)
plane("bath_ceil", (3.2, 3.2), (0, 0, 2.6), mat("ceil", (0.8, 0.8, 0.78), 0.9), rot=(180, 0, 0), parent=bath)
for nm, sz, loc, rot in (("wall_n", (3.2, 2.6), (0, 1.6, 1.3), (90, 0, 0)), ("wall_s", (3.2, 2.6), (0, -1.6, 1.3), (90, 0, 0)),
                         ("wall_e", (3.2, 2.6), (1.6, 0, 1.3), (90, 0, 90)), ("wall_w", (3.2, 2.6), (-1.6, 0, 1.3), (90, 0, 90))):
    plane(nm, sz, loc, M_tile, rot=rot, parent=bath)
sink_root = empty("sink_root", (0, 1.32, 0), bath)
sk = import_glb(BK + "a541b293_u.glb", sink_root)
sink_root.rotation_euler = (0, 0, R(180)); sink_root.scale = (0.85, 0.85, 1.0)
M_mirror = mat("mirror", (0.92, 0.92, 0.92), 0.0, metal=1.0)
mirror = plane("mirror", (1.0, 0.85), (0, 1.578, 1.55), M_mirror, rot=(90, 0, 0), parent=bath)
box("mirror_frame", (1.06, 0.02, 0.91), (0, 1.595, 1.55), mat("frame", (0.05, 0.05, 0.05), 0.4), parent=bath)
box("mirror_lamp", (0.7, 0.05, 0.05), (0, 1.55, 2.05), mat("lamp", (1, 0.85, 0.65), emit=12), parent=bath)
BATH_SHOTS = rng("mirror_walk", "mirror_close", "scared", "relief")
vis(bath, BATH_SHOTS)

XR = Vector((-120.0, 0, 0))                     # rentgen sahnasi (qora fon)

# ======================================================================
# 6) QAHRAMONLAR
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx")
aroot, adam, ameshes = mc.load_character("adam", "Adam.fbx")
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
                        n.inputs["Roughness"].default_value = 0.6
                    n.inputs["Coat Weight"].default_value = 0.0
soften(mmeshes + ameshes)
A = lambda f, inplace=True: mc.load_action(f, inplace)
def at(root, f, loc, rz):
    root.location = loc; root.rotation_euler = (0, 0, R(rz))
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)

# --- Megan ---
at(mroot, 1, tuple(LR + Vector((0.2, 0.55, 0))), 0)
at(mroot, S["mirror_walk"][0], tuple(BA + Vector((0.05, -0.35, 0))), 180)
at(mroot, S["mirror_close"][0], tuple(BA + Vector((0, 0.95, 0))), 180)
at(mroot, S["scared"][0], tuple(BA + Vector((0, 0.8, 0))), 180)
at(mroot, S["relief"][0], tuple(BA + Vector((0, 0.9, 0))), 180)
interp(mroot, "CONSTANT")
# ko'zgu tomon yurish (root harakati kod bilan)
MW0, MW1 = S["mirror_walk"]
mroot.location = BA + Vector((0.05, -0.35, 0)); mroot.keyframe_insert("location", frame=MW0)
mroot.location = BA + Vector((0.02, 0.85, 0)); mroot.keyframe_insert("location", frame=MW1 - 2)
for fc in fcurves(mroot):
    for k in fc.keyframe_points:
        if MW0 <= k.co.x < MW1 - 2: k.interpolation = "LINEAR"
MEG_SHOTS = rng("sneeze", "mirror_walk", "mirror_close", "scared", "relief")
vis(mroot, MEG_SHOTS)
mc.add_strip(meg, A("Breathing_Idle.fbx"), 1, blend=0, repeat=1.0)
mc.add_strip(meg, A("Female_Walk.fbx"), MW0 - 6, blend=0, repeat=2.0)
mc.add_strip(meg, A("Breathing_Idle.fbx"), MW1 - 4, blend=4)
mc.add_strip(meg, A("Terrified.fbx"), S["scared"][0] - 6, blend=0, speed=1.1)
mc.add_strip(meg, A("Relieved_Sigh.fbx"), S["relief"][0] - 4, blend=0)

def pose_layer(arm, name, keys, start):
    """Bo'g'imlar ustiga qo'shimcha burilish (COMBINE NLA). keys: {bone: [(f, (rx, ry, rz)), ...]} (gradus, mahalliy)"""
    ad = arm.animation_data; prev = ad.action
    act = bpy.data.actions.new(name); ad.action = act
    for bn, ks in keys.items():
        pb = arm.pose.bones["mixamorig:" + bn]; pb.rotation_mode = "QUATERNION"
        for f, e in ks:
            from mathutils import Euler
            pb.rotation_quaternion = Euler([R(a) for a in e]).to_quaternion()
            pb.keyframe_insert("rotation_quaternion", frame=f)
            pb.rotation_quaternion = (1, 0, 0, 0)
    ad.action = prev
    tr = ad.nla_tracks.new(); tr.name = name
    s = tr.strips.new(name, int(start), act)
    if hasattr(s, "action_slot") and act.slots: s.action_slot = act.slots[0]
    s.action_frame_start = start
    s.blend_type = "COMBINE"; s.extrapolation = "HOLD"
    s.frame_start = start
    return s
SN = S["sneeze"][0] + 9               # aksirish lahzasi (~0.9 s)
z = (0, 0, 0)
sneeze_keys = {
    "Spine1": [(1, z), (SN - 9, z), (SN - 2, (-6, 0, 0)), (SN + 1, (7, 0, 0)), (SN + 6, (6, 0, 0)), (SN + 22, (2, 0, 0)), (S["sneeze"][1] + 1, z)],
    "Spine2": [(1, z), (SN - 9, z), (SN - 2, (-5, 0, 0)), (SN + 1, (5, 0, 0)), (SN + 6, (4, 0, 0)), (SN + 22, (2, 0, 0)), (S["sneeze"][1] + 1, z)],
    "Neck":   [(1, z), (SN - 9, z), (SN - 2, (-10, 0, 0)), (SN + 1, (6, 0, 0)), (SN + 6, (5, 0, 0)), (SN + 22, (3, 0, 0)), (S["sneeze"][1] + 1, z)],
    "Head":   [(1, z), (SN - 9, z), (SN - 2, (-14, 0, 0)), (SN + 1, (10, 0, 0)), (SN + 6, (8, 0, 0)), (SN + 22, (4, 0, 0)), (S["sneeze"][1] + 1, z)],
}
# ko'zgu oldida engashish (mirror_close) va dog'ni ko'rish
MC0 = S["mirror_close"][0]
lean = {
    "Spine1": [(MC0 - 1, z), (MC0 + 12, (10, 0, 0)), (S["mirror_close"][1] + 1, (12, 0, 0)), (S["mirror_close"][1] + 2, z)],
    "Head":   [(MC0 - 1, z), (MC0 + 12, (-6, 6, 0)), (S["mirror_close"][1] + 1, (-8, 8, 0)), (S["mirror_close"][1] + 2, z)],
}
for bn, ks in lean.items(): sneeze_keys[bn] += ks
pose_layer(meg, "meg_extra", sneeze_keys, 1)

# --- Adam ---
SQ0 = S["squat"][0]
at(aroot, 1, tuple(GY + Vector((0, 0.2, 0.03))), 25)
at(aroot, S["xray"][0], tuple(XR), 20)
interp(aroot, "CONSTANT")
vis(aroot, rng("squat", "strain", "xray"), False); vis(adam, rng("squat", "strain", "xray"), False)
sq = A("Back_Squat_3.fbx")
mc.add_strip(adam, sq, SQ0 - 20, blend=0, repeat=3.0, speed=0.8)
# rentgenda pastki nuqtada qotib turadi
hold = mc.add_strip(adam, sq, S["xray"][0] - 1, blend=0, src=(30, 31), hold=True)
# shtanga: bo'yin ortida (Spine2/Neck ga yopishgan)
bar = bone_empty("barbell", adam, "Neck")
bar_o = empty("barbell_o", (0, -0.02, -0.09), bar)
cyl("bar", 0.014, 2.1, (0, 0, 0), M_steel, rot=(0, 90, 0), parent=bar_o, verts=24)
for sx in (-1, 1):
    for k, (rr, w, m_) in enumerate(((0.225, 0.05, M_plate_red), (0.225, 0.05, M_plate_red), (0.17, 0.035, M_plate))):
        cyl(f"plate{sx}{k}", rr, w, (sx * (0.62 + k * 0.055), 0, 0), m_, rot=(0, 90, 0), parent=bar_o, verts=48)
    cyl(f"collar{sx}", 0.03, 0.03, (sx * 0.58, 0, 0), M_steel, rot=(0, 90, 0), parent=bar_o)
vis(bar, rng("squat", "strain"))
# kuchanganda yuz qizaradi (teri materialiga ko'paytiriladigan rang)
def redden(meshes, pairs):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.name.lower().endswith("_body"): continue
            Nn = m.node_tree.nodes; Ll = m.node_tree.links
            bs = next((n for n in Nn if n.type == "BSDF_PRINCIPLED"), None)
            if not bs or not bs.inputs["Base Color"].links: continue
            lk = bs.inputs["Base Color"].links[0]; src = lk.from_socket; Ll.remove(lk)
            mx_ = Nn.new("ShaderNodeMix"); mx_.data_type = "RGBA"; mx_.blend_type = "MULTIPLY"
            Ll.new(src, mx_.inputs[6]); mx_.inputs[7].default_value = (1.0, 0.45, 0.4, 1); Ll.new(mx_.outputs[2], bs.inputs["Base Color"])
            for f, v in pairs:
                mx_.inputs["Factor"].default_value = v; mx_.inputs["Factor"].keyframe_insert("default_value", frame=f)
ST0, ST1 = S["strain"]
redden(ameshes, [(1, 0.0), (ST0, 0.15), (ST0 + 20, 0.7), (ST1 + 1, 0.0)])

# --- rentgen: Adam shaffof, yurak va bo'yin tomirlari ---
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.4, base=0.015)
ghosts = []
for o in ameshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
X0, X1 = S["xray"]
for g in ghosts: vis(g, rng("xray"), False)
for o in ameshes: vis(o, rng("squat", "strain"), False)
sc.frame_set(X0 + 2); bpy.context.view_layer.update()
def bh(bn): return adam.matrix_world @ adam.pose.bones["mixamorig:" + bn].head
def bt(bn): return adam.matrix_world @ adam.pose.bones["mixamorig:" + bn].tail
fwd = (adam.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()          # Mixamo: lokal +Z old
fwd = (adam.matrix_world.to_3x3() @ adam.pose.bones["mixamorig:Spine2"].matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
side = (adam.matrix_world.to_3x3() @ adam.pose.bones["mixamorig:Spine2"].matrix.to_3x3() @ Vector((1, 0, 0))).normalized()
heart_p = bh("Spine2") + fwd * 0.05 + side * 0.03
neck_p = bh("Neck"); head_p = bh("Head"); top_p = bt("Head")
M_vein = P.pulse_material("xray_vessel", (0.9, 0.05, 0.04), base_emit=1.5, pulse_col=(1.0, 0.25, 0.1), width=0.12)
M_heart = mat("heart", (0.8, 0.04, 0.03), 0.3, emit=3.0)
heart = sphere("heart", 0.055, tuple(heart_p), M_heart, scale=(1, 0.85, 1.15))
for f in range(X0, X1 + 2, 8):
    heart.scale = (1.25, 1.1, 1.4); heart.keyframe_insert("scale", frame=f)
    heart.scale = (1, 0.85, 1.15); heart.keyframe_insert("scale", frame=f + 4)
xv = []
for sx in (-1, 1):
    pts = [heart_p, heart_p + Vector((0, 0, 0.08)) + side * sx * 0.02, neck_p + side * sx * 0.035 + fwd * 0.03,
           head_p + side * sx * 0.045 + fwd * 0.05, head_p + Vector((0, 0, 0.06)) + side * sx * 0.05 + fwd * 0.07,
           (head_p + top_p) / 2 + fwd * 0.06 + side * sx * 0.035]
    xv.append(P.tube(f"carotid{sx}", [tuple(p) for p in pts], 0.009, M_vein, taper=[1, 1, 0.9, 0.8, 0.6, 0.4]))
    # ko'z atrofidagi mayda tomirlar
    eye_p = head_p + Vector((0, 0, 0.075)) + fwd * 0.09 + side * sx * 0.032
    for k in range(4):
        a = k * 1.57 + 0.4
        xv.append(P.tube(f"eyecap{sx}{k}", [tuple(head_p + Vector((0, 0, 0.05)) + side * sx * 0.05 + fwd * 0.07),
                                            tuple(eye_p + Vector((math.cos(a) * 0.012, 0, math.sin(a) * 0.012)) - fwd * 0.005),
                                            tuple(eye_p + Vector((math.cos(a + 0.8) * 0.018, 0, math.sin(a + 0.8) * 0.018)))], 0.0025, M_vein))
for f in range(X0, X1 + 2, 8):
    P.mat_value(M_vein, "pos", f, -0.1); P.mat_value(M_vein, "pos", f + 7, 1.1)
P.mat_value(M_vein, "glow", X0, 1.0); P.mat_value(M_vein, "glow", X0 + 40, 5.0); P.mat_value(M_vein, "glow", X1 + 1, 6.0)
for o in xv + [heart]: vis(o, rng("xray"), False)
EYE_X = head_p + Vector((0, 0, 0.075)) + fwd * 0.09
sc.frame_set(1)

# sneeze: og'izdan sachragan mayda tomchilar
mhead = bone_empty("meg_head", meg, "Head")
mouth = empty("meg_mouth", (0, 0.04, 0.115), mhead)
faceM = empty("meg_face", (0, 0.1, 0.09), mhead)
eyeM = empty("meg_eye", (-0.032, 0.1, 0.1), mhead)
M_spray = mat("spray", (0.9, 0.95, 1.0), 0.05, alpha=0.6); M_spray.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
sc.frame_set(SN); bpy.context.view_layer.update()
mpos = mouth.matrix_world.translation.copy()
mfwd = (mhead.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
sprays = []
for k in range(70):
    o = sphere(f"spray{k}", rnd2.uniform(0.0008, 0.002), tuple(mpos), M_spray, sub=1)
    d = (mfwd + Vector((rnd2.uniform(-0.35, 0.35), rnd2.uniform(-0.35, 0.35), rnd2.uniform(-0.3, 0.25)))).normalized() * rnd2.uniform(0.04, 0.09)
    o.location = mpos; o.keyframe_insert("location", frame=SN)
    for f in range(SN + 1, S["sneeze"][1] + 2):
        tt = f - SN; o.location = mpos + d * tt * (1 - tt / 60) - Vector((0, 0, 0.0004 * tt * tt)); o.keyframe_insert("location", frame=f)
    vis(o, [(SN, S["sneeze"][1])], False)
sc.frame_set(1)

# ======================================================================
# 7) KAMERALAR
# ======================================================================
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c
def cam_path(c, pairs):
    for f, loc in pairs: key(c, f, loc=tuple(loc))

spotT = empty("spotT", tuple(SPOT * 0.6 + Vector((0, -0.006, 0))))
eyeT = empty("eyeT", (0.002, -0.012, 0))
# 1 ilgak: dog'li ko'z, crash zoom
c = shot_cam("hook", (0, 0, 0), spotT, 40, 9.0, focus=spotT)
cam_path(c, [(1, (0.03, -0.12, 0.01)), (5, (0.014, -0.07, 0.004)), (S["hook"][1] + 1, (0.012, -0.062, 0.003))])
lens_keys(c, [(1, 30), (4, 55), (S["hook"][1] + 1, 60)])
shake(c, 4, 14, 0.0012, 2)
# 2 aksirish: yuzga yaqin, DOF
c = shot_cam("sneeze", (0, 0, 0), faceM, 55, 2.0)
cam_path(c, [(S["sneeze"][0], LR + Vector((0.5, -0.5, 1.42))), (S["sneeze"][1] + 1, LR + Vector((0.45, -0.4, 1.42)))])
shake(c, SN, SN + 12, 0.025, 3)
# 3 shtanga: pastdan keng
gT = empty("gymT", tuple(GY + Vector((0, 0.2, 1.2))))
c = shot_cam("squat", (0, 0, 0), gT, 16, 5.6, focus=gT)
cam_path(c, [(S["squat"][0], GY + Vector((1.2, -1.7, 0.25))), (S["squat"][1] + 1, GY + Vector((0.8, -1.5, 0.3)))])
# 4 kuchanish: yuz yaqin, silkinish
aface = bone_empty("adam_face", adam, "Head", (0, 0.1, 0.09))
c = shot_cam("strain", (0, 0, 0), aface, 70, 2.0)
cam_path(c, [(ST0, GY + Vector((0.65, -0.85, 1.25))), (ST1 + 1, GY + Vector((0.55, -0.7, 1.1)))])
shake(c, ST0 + 6, ST1, 0.008, 4)
# 5 ko'zgu tomon yurish: yelka ortidan
mirT = empty("mirT", tuple(BA + Vector((0.0, 1.585, 1.45))))
c = shot_cam("mirror_walk", (0, 0, 0), mirT, 28, 4.0, focus=faceM)
cam_path(c, [(MW0, BA + Vector((0.45, -0.9, 1.45))), (MW1 + 1, BA + Vector((0.35, 0.2, 1.6)))])
# 6 ko'zgudagi aks, yaqin (fokus: kamera -> ko'zgu -> yuz)
mir2 = empty("mir2T", tuple(BA + Vector((-0.04, 1.585, 1.58))))
c = shot_cam("mirror_close", (0, 0, 0), mir2, 70, 2.8, focus=1.25)
cam_path(c, [(MC0, BA + Vector((0.22, 0.55, 1.68))), (S["mirror_close"][1] + 1, BA + Vector((0.2, 0.62, 1.66)))])
# 7 dog' paydo bo'ladi: crash zoom
c = shot_cam("eye_burst", (0, 0, 0), spotT, 45, 9.0, focus=spotT)
cam_path(c, [(S["eye_burst"][0], (0.025, -0.11, 0.008)), (B0, (0.022, -0.1, 0.007)), (B0 + 4, (0.012, -0.055, 0.003)),
             (S["eye_burst"][1] + 1, (0.011, -0.05, 0.003))])
lens_keys(c, [(S["eye_burst"][0], 45), (B0, 45), (B0 + 3, 70)])
shake(c, B0 + 1, B0 + 14, 0.0015, 5)
# 8 dog' ustida aylanma, o'ta makro
sp2 = empty("spot2T", tuple(SPOT + Vector((0, -0.0004, 0))))
c = shot_cam("spot_orbit", (0, 0, 0), sp2, 60, 14.0, focus=sp2)
O0, O1 = S["spot_orbit"]
for f in range(O0, O1 + 2, 4):
    t = (f - O0) / (O1 - O0); a = R(-20 + 40 * t)
    d = (Quaternion((0, 0, 1), a) @ (C + Vector((0, -0.6, 0.15)))).normalized()
    key(c, f, loc=tuple(SPOT + d * (0.03 - 0.006 * t)))
# 9 qo'rqib ketdi: past burchak, qizil kontur, crash zoom
c = shot_cam("scared", tuple(BA + Vector((0.25, 1.45, 0.75))), faceM, 18, 4.0)
lens_keys(c, [(S["scared"][0], 18), (S["scared"][0] + 5, 34), (S["scared"][1], 38)])
shake(c, S["scared"][0], S["scared"][0] + 14, 0.02, 5)
# 10 sho'ng'ish: ko'zdan kapillyar tomon
D0, D1 = S["dive"]
divT = empty("diveT", tuple(DIVE_PT), ball)
c = shot_cam("dive", (0, 0, 0), divT, 50, 10.0, focus=divT)
nrm = DIVE_PT.normalized()
for f in range(D0, D1 + 2, 2):
    t = (f - D0) / (D1 - D0); e_ = t ** 2.2
    dist = 0.09 * (1 - e_) + 0.0018 * e_
    dirv = (nrm + Vector((-0.25, -0.3, 0.12)) * (1 - t)).normalized()
    key(c, f, loc=tuple(DIVE_PT + dirv * dist))
    c.data.dof.aperture_fstop = 10 + 12 * e_; c.data.dof.keyframe_insert("aperture_fstop", frame=f)
# 11 / 15 tomir kesimi
vT = empty("vesselT", tuple(VX + Vector((0, 0, 0.03))))
c = shot_cam("vessel_burst", (0, 0, 0), vT, 35, 4.0, focus=vT)
VS0, VS1 = S["vessel_burst"]
cam_path(c, [(VS0, VX + Vector((-0.35, -0.6, 0.2))), (VB1, VX + Vector((-0.2, -0.45, 0.17))), (VB1 + 3, VX + Vector((-0.1, -0.32, 0.2))),
             (VS1 + 1, VX + Vector((-0.08, -0.3, 0.22)))])
shake(c, VB1, VB1 + 14, 0.012, 6)
c = shot_cam("vessel_burst2", (0, 0, 0), vT, 24, 3.2, focus=vT)
V20, V21 = S["vessel_burst2"]
cam_path(c, [(V20, VX + Vector((0.45, -0.3, 0.03))), (VB2, VX + Vector((0.3, -0.26, 0.07))), (VB2 + 3, VX + Vector((0.18, -0.22, 0.13))),
             (V21 + 1, VX + Vector((0.16, -0.21, 0.14)))])
lens_keys(c, [(V20, 24), (VB2, 24), (VB2 + 3, 32)])
shake(c, VB2, VB2 + 16, 0.014, 7)
# 12 rentgen
xT = empty("xrayT", tuple(heart_p * 0.4 + EYE_X * 0.6))
c = shot_cam("xray", (0, 0, 0), xT, 35, 4.0, focus=xT)
fdir = (fwd * 1.0 + side * 0.6).normalized()
cam_path(c, [(X0, xT.location + fdir * 1.3 + Vector((0, 0, -0.2))), (X1 + 1, xT.location + fdir * 0.75 + Vector((0, 0, -0.05)))])
# 13 manometr: past burchak, crash zoom
gaT = empty("gaugeT", tuple(GX + Vector((0, 0, 0.0))))
c = shot_cam("gauge", (0, 0, 0), gaT, 50, 5.6, focus=gaT)
cam_path(c, [(G0, GX + Vector((0.1, -0.6, -0.16))), (GJ, GX + Vector((0.07, -0.5, -0.13))), (GJ + 3, GX + Vector((0.04, -0.4, -0.09))),
             (G1 + 1, GX + Vector((0.035, -0.38, -0.085)))])
lens_keys(c, [(G0, 40), (GJ, 40), (GJ + 3, 52)])
shake(c, GJ, GJ + 14, 0.006, 8)
# 14 ko'z, yon tomondan sekin aylanma
EO0, EO1 = S["eye_orbit"]
c = shot_cam("eye_orbit", (0, 0, 0), eyeT, 55, 8.0, focus=eyeT)
for f in range(EO0, EO1 + 2, 4):
    t = (f - EO0) / (EO1 - EO0); a = R(35 - 45 * t)
    key(c, f, loc=(math.sin(a) * 0.085, -math.cos(a) * 0.085, 0.012 - 0.01 * t))
# 16 qatlam kesimi
lT = empty("layersT", tuple(LX + Vector((0.02, 0.0, 0.0))))
c = shot_cam("layers", (0, 0, 0), lT, 35, 8.0, focus=lT)
cam_path(c, [(L0, LX + Vector((0.25, -0.85, 0.42))), (L1 + 1, LX + Vector((0.12, -0.62, 0.3)))])
# 17 yengil tin olish: ko'zgu tomondan
c = shot_cam("relief", (0, 0, 0), faceM, 50, 2.4)
cam_path(c, [(S["relief"][0], BA + Vector((-0.15, 1.5, 1.52))), (S["relief"][1] + 1, BA + Vector((-0.12, 1.45, 1.55)))])
# 18 time-lapse: dog' yo'qoladi
c = shot_cam("heal", (0, 0, 0), eyeT, 50, 9.0, focus=eyeT)
cam_path(c, [(H0, (0.02, -0.095, 0.008)), (H1 + 1, (0.012, -0.075, 0.004))])

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 8) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
tcw = N.new("ShaderNodeTexCoord"); mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(120))
L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "studio_small_09.hdr"); L.new(mpw.outputs[0], env.inputs[0])
tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs["Factor"].default_value = 1.0
L.new(env.outputs[0], tint.inputs[6]); tint.inputs[7].default_value = (1, 1, 1, 1)
bg = N["Background"]; L.new(tint.outputs[2], bg.inputs[0])
# (osmon kuchi, rang)
WL = {"hook": (0.35, (1, 0.95, 0.9)), "sneeze": (0.0, (1, 1, 1)), "squat": (0.0, (1, 1, 1)), "mirror_walk": (0.0, (1, 1, 1)),
      "eye_burst": (0.35, (1, 0.95, 0.9)), "scared": (0.0, (1, 1, 1)), "dive": (0.35, (1, 0.95, 0.9)), "vessel_burst": (0.25, (1, 0.6, 0.55)),
      "xray": (0.0, (1, 1, 1)), "gauge": (0.15, (1, 0.8, 0.75)), "eye_orbit": (0.35, (1, 0.95, 0.9)), "vessel_burst2": (0.25, (1, 0.6, 0.55)),
      "layers": (0.3, (1, 0.85, 0.85)), "relief": (0.0, (1, 1, 1)), "heal": (0.35, (1, 0.95, 0.9))}
cur = None
for f, n in SHOTS:
    cur = WL.get(n, cur)
    bg.inputs[1].default_value = cur[0]; bg.inputs[1].keyframe_insert("default_value", frame=f)
    tint.inputs[7].default_value = (*cur[1], 1); tint.inputs[7].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

eye_on = rng(*EYE_SHOTS)
ek = area("eye_key", (-0.09, -0.14, 0.11), 0.09, (1, 0.95, 0.9), lights_for(eye_on, 1.6), target=eA["root"])
area("eye_fill", (0.12, -0.1, -0.03), 0.12, (0.85, 0.9, 1.0), lights_for(eye_on, 0.5), target=eA["root"])
area("eye_red_rim", (0.09, 0.02, 0.05), 0.05, (1.0, 0.2, 0.1), lights_for(rng("eye_burst", "spot_orbit"), 1.0), target=eA["root"])
# time-lapse: kun-tun almashinuvi (kalit yorug'lik rangi va kuchi)
for i, f in enumerate(range(H0, H1 + 1, 6)):
    day = i % 2 == 0
    ek.data.energy = 1.8 if day else 0.35; ek.data.keyframe_insert("energy", frame=f)
    ek.data.color = (1, 0.95, 0.88) if day else (0.45, 0.6, 1.0); ek.data.keyframe_insert("color", frame=f)
ek.data.energy = 1.6; ek.data.keyframe_insert("energy", frame=H1 - 14); ek.data.color = (1, 0.95, 0.9); ek.data.keyframe_insert("color", frame=H1 - 14)
ek.data.energy = 0; ek.data.keyframe_insert("energy", frame=H1 + 1)
interp(ek.data, "CONSTANT")
# mehmonxona
area("lr_win", tuple(LR + Vector((-2.2, 0.3, 1.5))), 1.4, (1, 0.95, 0.88), lights_for(rng("sneeze"), 300), target=faceM)
area("lr_fill", tuple(LR + Vector((1.5, -1.2, 2.0))), 1.0, (1, 0.9, 0.8), lights_for(rng("sneeze"), 120), target=faceM)
# sport zal
area("gym_top", tuple(GY + Vector((0, 0.0, 3.8))), 3.0, (1, 0.97, 0.92), lights_for(rng("squat", "strain"), 3500))
area("gym_fill", tuple(GY + Vector((1.5, -2.5, 1.6))), 1.5, (1, 0.93, 0.85), lights_for(rng("squat", "strain"), 500), target=gT)
area("gym_rim", tuple(GY + Vector((-1.2, 1.6, 2.2))), 0.8, (0.6, 0.75, 1.0), lights_for(rng("squat", "strain"), 300), target=aface)
area("gym_red", tuple(GY + Vector((1.0, 0.8, 1.6))), 0.5, (1.0, 0.25, 0.15), lights_for(rng("strain"), 120), target=aface)
# hammom
area("bath_ceil_light", tuple(BA + Vector((0, 0.2, 2.5))), 1.0, (1, 0.9, 0.78), lights_for(BATH_SHOTS, 300))
area("bath_face", tuple(BA + Vector((0.0, 1.45, 2.0))), 0.5, (1, 0.92, 0.85), lights_for(rng("mirror_close", "relief"), 40), target=faceM)
area("scared_rim", tuple(BA + Vector((-0.6, 0.1, 2.0))), 0.6, (1.0, 0.15, 0.08), lights_for(rng("scared"), 120), target=faceM)
# tomir kesimi, qatlamlar, manometr
area("v_key", tuple(VX + Vector((-0.4, -0.5, 0.6))), 0.6, (1, 0.92, 0.88), lights_for(VBR, 25), target=vT)
area("v_rim", tuple(VX + Vector((0.3, 0.6, 0.3))), 0.4, (1, 0.45, 0.35), lights_for(VBR, 20), target=vT)
area("l_key", tuple(LX + Vector((-0.4, -0.5, 0.7))), 0.6, (1, 0.95, 0.92), lights_for(rng("layers"), 30), target=lT)
area("l_rim", tuple(LX + Vector((0.4, 0.5, 0.25))), 0.4, (1, 0.5, 0.4), lights_for(rng("layers"), 15), target=lT)
area("g_key", tuple(GX + Vector((-0.3, -0.4, 0.35))), 0.3, (1, 0.95, 0.9), lights_for(rng("gauge"), 30), target=gaT)
area("g_rim", tuple(GX + Vector((0.3, -0.1, -0.2))), 0.2, (1, 0.2, 0.1), lights_for(rng("gauge"), 8), target=gaT)

# ======================================================================
# 9) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 12)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b_ = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b_
        bpy.ops.render.render(animation=True)
