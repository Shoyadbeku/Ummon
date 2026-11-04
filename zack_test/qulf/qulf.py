# Qulf tagidagi kichik teshik — Zack D. Films uslubida 40 s video (963 kadr, 24 fps, 9:16).
# Asos: zack_test/hiqichoq/hiqichoq.py, scene3.py, mixchar.py. Kadr rejasi: STORYBOARD.md
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=45 /tmp/claude-0/bvenv/bin/python -I zack_test/qulf/qulf.py --render
# Sinov: FRAMES=20,70,240,420,650 PCT=35
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix
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
END = 963
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (46, "hole"), (91, "think"), (146, "keytry"), (207, "rain"), (273, "snow"), (323, "enter"),
         (382, "pool"), (444, "stay"), (484, "rust"), (579, "freeze"), (630, "stuck"), (693, "drain"), (749, "drip"),
         (799, "oilmeg"), (857, "oildrop"), (910, "mech"), (937, "pop")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
EXT = ["hook", "hole", "think", "keytry", "rain", "snow", "enter", "stuck", "drip", "oilmeg", "oildrop", "pop"]
STUDIO = ["pool", "stay", "rust", "freeze", "drain", "mech"]
MEG = ["hook", "think", "stuck", "oilmeg", "pop"]
WINTER = ["snow", "stuck"]
WET = ["rain", "enter", "drip"]
BUMP = 178            # kalit teshikka tiqiladi ("vazifasi")
CRASH = 662           # muzlagan qulfga crash zoom
POP = 944             # qulf ochiladi ("jonlantirish")
FLIP = 799            # qulf teskari (moy tomizish)

# ---------------- yordamchilar ----------------
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

def tex_img(N, L, folder, fn, vec, non_color=False, proj="BOX"):
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn), check_existing=True)
    t.projection = proj; t.projection_blend = 0.25
    if non_color: t.image.colorspace_settings.name = "Non-Color"
    L.new(vec, t.inputs[0]); return t

def pbr(name, folder, scale=1.0, tint=None, proj="BOX", wet=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    d = tex_img(N, L, folder, "diff.jpg", mp.outputs[0], proj=proj)
    col = d.outputs[0]
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); col = mx.outputs[2]
    rough = tex_img(N, L, folder, "rough.jpg", mp.outputs[0], True, proj).outputs[0]
    if wet:                                    # 'wet' qiymati: ho'l yuza (qoraroq, yaltiroq)
        w = value_node(m, "wet", 0.0)
        dk = N.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"; L.new(w, dk.inputs["Factor"])
        L.new(col, dk.inputs[6]); dk.inputs[7].default_value = (0.45, 0.45, 0.47, 1); col = dk.outputs[2]
        rm = N.new("ShaderNodeMix"); rm.data_type = "FLOAT"; L.new(w, rm.inputs["Factor"])
        L.new(rough, rm.inputs[2]); rm.inputs[3].default_value = 0.06; rough = rm.outputs[0]
        L.new(w, b.inputs["Coat Weight"])
    L.new(col, b.inputs["Base Color"]); L.new(rough, b.inputs["Roughness"])
    n = tex_img(N, L, folder, "nor.jpg", mp.outputs[0], True, proj)
    nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value

def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    if m: o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3
        for p in o.data.polygons: p.use_smooth = True
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name
    if m: o.data.materials.append(m)
    if smooth:
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

def bake(o):
    """modifikatorlarni qo'llash (boolean va h.k.)"""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear(); old = o.data; o.data = me
    if old.users == 0: bpy.data.meshes.remove(old)
    return o

def cut(o, cutters, bake_now=True):
    for c in cutters:
        b = o.modifiers.new("cut", "BOOLEAN"); b.operation = "DIFFERENCE"; b.object = c; b.solver = "EXACT"
        b.material_mode = "TRANSFER"
    if bake_now: bake(o)
    return o

def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def ph_model(name, loc, rotz=0, scale=1.0, parent=None):
    e = empty(name, loc, parent); e.rotation_euler = (0, 0, R(rotz)); e.scale = (scale,) * 3
    return e, import_gltf(PH + f"{name}/{name}.gltf", e)

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

def area(name, loc, size, col, keys, target=None, parent=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, parent=None, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
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

def scale_vis(o, f0, f1):
    """kichik ob'ektlar uchun: f0..f1 da ko'rinadi (masshtab 0 <-> 1, CONSTANT)"""
    s0 = o.scale.copy()
    o.scale = (0.0001,) * 3; o.keyframe_insert("scale", frame=1); o.keyframe_insert("scale", frame=f1 + 1)
    o.scale = s0; o.keyframe_insert("scale", frame=f0)
    interp(o, "CONSTANT", "scale")

def state_keys(m, name, mapping, default=0.0):
    """har kadr boshida materialdagi qiymat (CONSTANT)"""
    for f, n in SHOTS: val_key(m, name, f, mapping.get(n, default))
    interp(m.node_tree, "CONSTANT")

# ======================================================================
# MATERIALLAR
# ======================================================================
RUST_MATS = []
def metal_mat(name, col, rough=0.25, rust_scale=600.0, frost=False, oil=False, metal=1.0):
    """metall + 'rust' (zang, 0..1) + ixtiyoriy 'frost' (qirov) va 'oil' (moy) qiymatlari"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = rust_scale; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs[0])
    sm = N.new("ShaderNodeTexNoise"); sm.inputs["Scale"].default_value = rust_scale * 4; L.new(tc.outputs["Object"], sm.inputs[0])
    rv = value_node(m, "rust", 0.0)
    # maska: noise > 1 - rust  (zang dog'lari kengayib boradi)
    th = P.math_n(N, L, "SUBTRACT", 1.0, rv)
    mk = P.math_n(N, L, "SUBTRACT", nz.outputs["Fac"], th)
    mk = P.math_n(N, L, "MULTIPLY", mk, 6.0, clamp=True)
    mk = P.math_n(N, L, "MULTIPLY", mk, P.math_n(N, L, "MINIMUM", P.math_n(N, L, "MULTIPLY", rv, 3.0), 1.0))
    rcol = N.new("ShaderNodeMix"); rcol.data_type = "RGBA"; L.new(sm.outputs["Fac"], rcol.inputs["Factor"])
    rcol.inputs[6].default_value = (0.16, 0.05, 0.015, 1); rcol.inputs[7].default_value = (0.45, 0.16, 0.04, 1)
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; L.new(mk, c.inputs["Factor"])
    c.inputs[6].default_value = (*col, 1); L.new(rcol.outputs[2], c.inputs[7])
    met = P.math_n(N, L, "SUBTRACT", metal, P.math_n(N, L, "MULTIPLY", mk, metal))
    rgh = P.math_n(N, L, "ADD", rough, P.math_n(N, L, "MULTIPLY", mk, 0.75))
    # mayda chiziqlar (eskirgan metall)
    sc_ = N.new("ShaderNodeTexNoise"); sc_.inputs["Scale"].default_value = 80; sc_.inputs["Detail"].default_value = 12
    L.new(tc.outputs["Object"], sc_.inputs[0])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; bp.inputs["Distance"].default_value = 0.0004
    L.new(P.math_n(N, L, "ADD", sc_.outputs["Fac"], P.math_n(N, L, "MULTIPLY", mk, 1.5)), bp.inputs["Height"])
    colout = c.outputs[2]
    if oil:
        ov = value_node(m, "oil", 0.0)
        oc = N.new("ShaderNodeMix"); oc.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", ov, 0.55), oc.inputs["Factor"])
        L.new(colout, oc.inputs[6]); oc.inputs[7].default_value = (0.55, 0.28, 0.02, 1); colout = oc.outputs[2]
        rgh = P.math_n(N, L, "SUBTRACT", rgh, P.math_n(N, L, "MULTIPLY", ov, 0.6))
        L.new(ov, b.inputs["Coat Weight"])
    if frost:
        fv = value_node(m, "frost", 0.0)
        fn = N.new("ShaderNodeTexVoronoi"); fn.inputs["Scale"].default_value = 2500
        L.new(tc.outputs["Object"], fn.inputs[0])
        fm = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fn.outputs["Distance"], 0.5), P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.7)), P.math_n(N, L, "SUBTRACT", 1.0, fv)), 3.0, clamp=True)
        fm = P.math_n(N, L, "MULTIPLY", fm, P.math_n(N, L, "MINIMUM", P.math_n(N, L, "MULTIPLY", fv, 4.0), 1.0))
        fc = N.new("ShaderNodeMix"); fc.data_type = "RGBA"; L.new(fm, fc.inputs["Factor"])
        L.new(colout, fc.inputs[6]); fc.inputs[7].default_value = (0.85, 0.92, 1.0, 1); colout = fc.outputs[2]
        met = P.math_n(N, L, "SUBTRACT", met, fm, clamp=True)
        rgh = P.math_n(N, L, "ADD", rgh, P.math_n(N, L, "MULTIPLY", fm, 0.6))
        L.new(P.math_n(N, L, "ADD", sc_.outputs["Fac"], P.math_n(N, L, "MULTIPLY", fm, 2.0)), bp.inputs["Height"])
        wv = value_node(m, "wet", 0.0)
        L.new(wv, b.inputs["Coat Weight"])
    L.new(colout, b.inputs["Base Color"]); L.new(met, b.inputs["Metallic"])
    L.new(P.math_n(N, L, "MAXIMUM", rgh, 0.03), b.inputs["Roughness"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    RUST_MATS.append(m)
    return m

M = dict(
    brass=metal_mat("brass", (0.62, 0.38, 0.1), 0.3, frost=True),
    brass_cut=metal_mat("brass_cut", (0.75, 0.5, 0.18), 0.35, oil=True, metal=0.35),
    steel=metal_mat("steel", (0.75, 0.76, 0.78), 0.12, frost=True),
    steel_in=metal_mat("steel_in", (0.72, 0.73, 0.75), 0.15, oil=True),
    pin_brass=metal_mat("pin_brass", (0.85, 0.6, 0.25), 0.2, oil=True),
    spring=metal_mat("spring", (0.7, 0.72, 0.74), 0.15, oil=True),
    keymat=metal_mat("keymat", (0.78, 0.66, 0.42), 0.18),
    dark=mat("dark", (0.01, 0.01, 0.01), 0.6),
)
water_m = bpy.data.materials.new("water_in"); water_m.use_nodes = True
N = water_m.node_tree.nodes; L = water_m.node_tree.links
wb = N["Principled BSDF"]; wb.inputs["Base Color"].default_value = (0.03, 0.3, 0.9, 1); wb.inputs["Roughness"].default_value = 0.03
wb.inputs["Alpha"].default_value = 0.75; wb.inputs["Emission Color"].default_value = (0.05, 0.4, 1.0, 1); wb.inputs["Emission Strength"].default_value = 1.2
ib = N.new("ShaderNodeBsdfPrincipled"); ib.inputs["Base Color"].default_value = (0.82, 0.92, 1.0, 1); ib.inputs["Roughness"].default_value = 0.3
ib.inputs["Subsurface Weight"].default_value = 0.5; ib.inputs["Subsurface Scale"].default_value = 0.002
ib.inputs["Emission Color"].default_value = (0.6, 0.85, 1.0, 1); ib.inputs["Emission Strength"].default_value = 0.25
tcw = N.new("ShaderNodeTexCoord"); vn = N.new("ShaderNodeTexVoronoi"); vn.inputs["Scale"].default_value = 900; L.new(tcw.outputs["Object"], vn.inputs[0])
bpi = N.new("ShaderNodeBump"); bpi.inputs["Strength"].default_value = 0.6; bpi.inputs["Distance"].default_value = 0.0005
L.new(vn.outputs["Distance"], bpi.inputs["Height"]); L.new(bpi.outputs[0], ib.inputs["Normal"])
mxs = N.new("ShaderNodeMixShader"); L.new(value_node(water_m, "ice", 0.0), mxs.inputs[0])
L.new(wb.outputs[0], mxs.inputs[1]); L.new(ib.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], N["Material Output"].inputs[0])
drop_m = mat("drop", (0.75, 0.88, 1.0), 0.0, trans=1.0, coat=1.0, emit=0.25, ecol=(0.6, 0.8, 1.0))
oil_m = mat("oil", (0.75, 0.42, 0.03), 0.02, coat=1.0, trans=0.6, emit=0.4, ecol=(0.9, 0.5, 0.05))

# ======================================================================
# OSMA QULF (mahalliy koordinata, metrda; korpus tagi markazi = (0,0,0); old tomoni -Y, kalit teshigi old yuzada)
# ======================================================================
W, D, H = 0.050, 0.028, 0.042
PZ = 0.016                      # silindr (plug) o'qi balandligi
PR = 0.0065                     # silindr radiusi
SL = PZ + PR                    # kesish chizig'i (shear line)
PIN_Y = (-0.0085, -0.0035, 0.0015, 0.0065)
PIN_L = (0.006, 0.0075, 0.005, 0.007)    # kalit pinlari uzunligi
DRV_L = 0.0055
CH_TOP = 0.036                  # pin kanali tepasi
LOCKED = -0.0028                # kalitsiz holat: pinlar pastda
SX, SZ, SRA, SWR = 0.0155, 0.060, 0.0155, 0.0042    # kamon: oyoqlar x=±SX, yoy markazi SZ, radius SRA, sim radiusi SWR
DRAIN = Vector((0.0, 0.006, 0.0))

def shackle_mesh(name, m, parent):
    """U shaklidagi kamon: uzun oyoq x=-SX (korpusga z=0.010 gacha), qisqa oyoq x=+SX (z=0.030 gacha)"""
    pts = []
    for i in range(10): pts.append(Vector((-SX, 0, 0.010 + (SZ - 0.010) * i / 9)))
    for i in range(1, 24):
        a = math.pi - math.pi * i / 24
        pts.append(Vector((SRA * math.cos(a), 0, SZ + SRA * math.sin(a))))
    for i in range(10): pts.append(Vector((SX, 0, SZ - (SZ - 0.030) * i / 9)))
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = SWR; cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts): p.co = (*v, 1)
    o = bpy.data.objects.new(name + "_c", cu); sc.collection.objects.link(o); o.data.materials.append(m)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); bpy.data.objects.remove(o)
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    if parent: ob.parent = parent
    for p in me.polygons: p.use_smooth = True
    return ob

def spring(name, z0, z1, m, parent, y):
    """prujina: tepada (CH_TOP) mahkam, pastga cho'ziladi; masshtab z bilan siqiladi"""
    turns = 7; n = turns * 16; r = 0.0011; L0 = z1 - z0
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.00028; cu.bevel_resolution = 3
    sp = cu.splines.new("POLY"); sp.points.add(n)
    for i, p in enumerate(sp.points):
        t = i / n; a = 2 * math.pi * turns * t
        p.co = (r * math.cos(a), r * math.sin(a), -L0 * t, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.data.materials.append(m)
    o.parent = parent; o.location = (0, y, z1)
    return o, L0

def build_key(name, parent, m):
    """kalit: yelka (0,0,0), tig' +Y bo'ylab (uchi y=0.022), kesik tishlar tepada; halqa -Y da"""
    g = empty(name, (0, 0, 0), parent)
    bow = cyl(name + "_bow", 0.011, 0.0022, (0, -0.016, 0), m, rot=(0, 90, 0), verts=48)
    hole = cyl("kh_cut", 0.003, 0.01, (0, -0.022, 0), None, rot=(0, 90, 0))
    cut(bow, [hole]); bpy.data.objects.remove(hole); bow.parent = g
    b = bow.modifiers.new("bev", "BEVEL"); b.width = 0.0005; b.segments = 2
    box(name + "_sh", (0.0024, 0.006, 0.010), (0, -0.003, -0.001), m, parent=g, bevel=0.0006)
    box(name + "_bl", (0.0021, 0.0225, 0.0045), (0, 0.0112, -0.0022), m, parent=g, bevel=0.0003)
    for py, pl in zip(PIN_Y, PIN_L):            # tishlar: har pin ostida balandlik
        top = (SL - pl) - PZ                      # pin tagi (mahalliy, kalit o'qiga nisbatan)
        h = top - 0.0001
        if h > -0.0001:
            box(name + "_t", (0.0021, 0.0028, h + 0.0002), (0, py + 0.0142, h / 2), m, parent=g, bevel=0.0003)
    return g

def build_lock(name, parent, cutaway=False):
    root = empty(name, (0, 0, 0), parent)
    body = box(name + "_body", (W, D, H), (0, 0, H / 2), M["brass"] if not cutaway else M["brass_cut"], bevel=0.0035)
    bake(body)
    for p in body.data.polygons: p.use_smooth = True
    cm = M["brass_cut"]
    cutters = []
    cutters.append(cyl("c_bore", PR + 0.0003, 0.03, (0, -0.0055, PZ), cm, rot=(90, 0, 0)))          # silindr teshigi
    cutters.append(box("c_cav", (0.014, 0.022, 0.0075), (0, -0.0005, 0.004 + 0.00375), cm))           # suv yig'iladigan bo'shliq
    cutters.append(cyl("c_drain", 0.0015, 0.012, tuple(DRAIN + Vector((0, 0, 0.002))), cm, verts=24))  # drenaj kanali
    for py in PIN_Y: cutters.append(cyl("c_pin", 0.0015, CH_TOP - PZ, (0, py, (PZ + CH_TOP) / 2), cm, verts=20))
    for sx, z0 in ((-SX, 0.008), (SX, 0.028)): cutters.append(cyl("c_sh", SWR + 0.0004, H, (sx, 0, z0 + H / 2), cm, verts=24))
    if cutaway: cutters.append(box("c_half", (0.1, 0.1, 0.2), (-0.05, 0, 0.05), cm))
    cut(body, cutters)
    for c in cutters: bpy.data.objects.remove(c)
    body.parent = root
    # silindr (plug) + kalit yo'li + pin teshiklari
    plugp = empty(name + "_plugpiv", (0, 0, PZ), root)
    plug = cyl(name + "_plug", PR, 0.0232, (0, -0.0026, 0), M["brass_cut"] if cutaway else M["brass"], rot=(90, 0, 0), verts=48)
    pc = [box("c_kw", (0.0024, 0.03, 0.0095), (0, -0.0026, -0.0005), M["dark"])]
    for py in PIN_Y: pc.append(cyl("c_kp", 0.0015, 0.012, (0, py, 0.006), cm, verts=20))
    if cutaway: pc.append(box("c_half", (0.1, 0.1, 0.1), (-0.05, 0, 0), cm))
    cut(plug, pc); [bpy.data.objects.remove(c) for c in pc]
    plug.parent = plugp
    if not cutaway:      # old yuzadagi kalit yo'li (qorong'i tirqish) va gardish
        box(name + "_kslot", (0.0022, 0.0004, 0.0085), (0, -D / 2 - 0.0001, PZ - 0.0005), M["dark"], parent=root)
        bpy.ops.mesh.primitive_torus_add(major_radius=PR + 0.0006, minor_radius=0.0007, location=(0, -D / 2, PZ), rotation=(R(90), 0, 0))
        rim = bpy.context.object; rim.name = name + "_rim"; rim.data.materials.append(M["brass"]); rim.parent = root
    sh = shackle_mesh(name + "_shackle", M["steel"] if not cutaway else M["steel_in"], None)
    if cutaway:
        ch = box("c_half", (0.1, 0.1, 0.2), (-0.05, 0, 0.05), cm); cut(sh, [ch]); bpy.data.objects.remove(ch)
    sh.parent = root
    parts = dict(root=root, body=body, plugp=plugp, plug=plug, shackle=sh, pins=[])
    if cutaway:
        for i, (py, pl) in enumerate(zip(PIN_Y, PIN_L)):
            stack = empty(f"{name}_stack{i}", (0, py, 0), root)
            kp = cyl(f"{name}_kpin{i}", 0.0013, pl, (0, 0, SL - pl / 2), M["pin_brass"], parent=stack, verts=24)
            dp = cyl(f"{name}_dpin{i}", 0.0013, DRV_L, (0, 0, SL + DRV_L / 2), M["steel_in"], parent=stack, verts=24)
            for o in (kp, dp):
                b = o.modifiers.new("bev", "BEVEL"); b.width = 0.0003; b.segments = 2
            sp, L0 = spring(f"{name}_spring{i}", SL + DRV_L, CH_TOP, M["spring"], root, py)
            parts["pins"].append((stack, sp, L0))
    return parts

# ======================================================================
# 1) HOVLI (ombor eshigi, osma qulf) — dunyo markazi
# ======================================================================
GY = -0.56                                         # eshik/devor yuzasi (Megan +Y tomonda, -Y ga qaraydi)
yard = empty("yard", (0, 0, 0))
planks = pbr("planks", "weathered_planks", 1.2, proj="BOX")
door_m = pbr("door", "weathered_planks", 1.2, tint=(0.75, 0.62, 0.5))
brick = pbr("brick", "red_brick_03", 0.6)
pave = pbr("pave", "concrete_pavement", 0.5, wet=True)
grav = pbr("grav", "gravel", 0.7, wet=True)
box("shed_wall", (6.0, 0.1, 2.7), (0, GY - 0.05, 1.35), planks, parent=yard)
dr = box("shed_door", (0.92, 0.04, 2.02), (-0.5, GY + 0.005, 1.01), door_m, parent=yard)
trim_m = mat("trim", (0.25, 0.18, 0.12), 0.7)
for x, w in ((-0.98, 0.07), (0.03, 0.07)): box("dframe", (w, 0.05, 2.08), (x, GY - 0.002, 1.04), door_m, parent=yard)
box("dframe_t", (1.08, 0.05, 0.07), (-0.47, GY + 0.01, 2.07), trim_m, parent=yard)
for z in (0.35, 1.65): box("hinge", (0.28, 0.006, 0.035), (-0.84, GY + 0.028, z), M["steel"], parent=yard)
# taqa (hasp) va halqa (staple)
P0 = Vector((0.0, GY + 0.022, 1.074))              # qulf osilgan nuqta
box("hasp_plate", (0.04, 0.003, 0.065), (0.0, GY + 0.0245, 1.08), M["steel"], parent=yard, bevel=0.001)
box("hasp_strap", (0.2, 0.003, 0.036), (-0.105, GY + 0.029, 1.083), M["steel"], parent=yard, bevel=0.001)
bpy.ops.mesh.primitive_torus_add(major_radius=0.009, minor_radius=0.0025, location=(0, GY + 0.04, 1.083), rotation=(0, R(90), 0))
st = bpy.context.object; st.name = "staple"; st.data.materials.append(M["steel"]); st.parent = yard
P0 = Vector((0.0, GY + 0.04, 1.0745))
# yer, devorlar, fon
plane("pavement", (8, 6), (0, GY + 3.0, 0), pave, parent=yard)
plane("gravel", (8, 0.5), (0, GY + 0.25, 0.002), grav, parent=yard)
plane("lawn", (60, 60), (0, 20, -0.01), mat("lawn", (0.12, 0.25, 0.06), 0.9), parent=yard)
box("brick_wall_l", (0.25, 6.0, 1.9), (-3.0, GY + 3.0, 0.95), brick, parent=yard)
box("brick_wall_r", (0.25, 6.0, 1.9), (3.0, GY + 3.0, 0.95), brick, parent=yard)
box("brick_wall_b", (6.25, 0.25, 1.9), (0, GY + 6.0, 0.95), brick, parent=yard)
box("roof_edge", (6.4, 0.6, 0.12), (0, GY - 0.05, 2.75), trim_m, parent=yard)
leaves = mat("leaves", (0.1, 0.24, 0.06), 0.7)
bark = mat("bark", (0.2, 0.13, 0.08), 0.9)
def tree(x, y, s=1.0):
    cyl("trunk", 0.12 * s, 2.4 * s, (x, y, 1.2 * s), bark, parent=yard, verts=16)
    for dx, dy, dz, r in ((0, 0, 2.9, 1.3), (0.7, 0.2, 2.5, 0.9), (-0.6, -0.3, 2.6, 1.0), (0.1, 0.4, 3.5, 0.9)):
        o = sphere("crown", r * s, (x + dx * s, y + dy * s, dz * s), leaves, sub=3, parent=yard)
        dm = o.modifiers.new("d", "DISPLACE"); dm.strength = 0.4 * s
        t = bpy.data.textures.new("cl", "CLOUDS"); t.noise_scale = 0.4; dm.texture = t
for x, y, s in ((-2.2, 7.5, 1.2), (1.8, 8.5, 1.4), (4.5, 6.5, 1.0), (-5.0, 5.0, 1.3), (5.5, 2.0, 1.1), (-5.5, 0.5, 1.0)): tree(x, y, s)
ph_model("planter_box_01", (1.35, GY + 0.35, 0), 0, 1.0, yard)
ph_model("watering_can_metal_01", (0.55, GY + 0.25, 0.0), 120, 1.0, yard)
spd, _ = ph_model("rusted_spade_01", (-1.25, GY + 0.12, 0.5), 0, 1.0, yard); spd.rotation_euler = (R(-12), 0, R(10))
# qish: qor qatlami (yer, eshik ustidagi tokcha), faqat qish kadrlarida
snow_m = pbr("snowm", "snow_02", 0.8)
snowg = empty("snow_set", (0, 0, 0), yard)
o = plane("snow_ground", (8, 6), (0, GY + 3.0, 0.012), snow_m, parent=snowg)
dsp = o.modifiers.new("sub", "SUBSURF"); dsp.levels = dsp.render_levels = 3; dsp.subdivision_type = "SIMPLE"
tx = bpy.data.textures.new("snowclouds", "CLOUDS"); tx.noise_scale = 0.35
dd = o.modifiers.new("d", "DISPLACE"); dd.texture = tx; dd.strength = 0.05
box("snow_ledge", (6.4, 0.6, 0.05), (0, GY - 0.05, 2.83), snow_m, parent=snowg)
sphere("snow_hasp", 0.03, (-0.08, GY + 0.032, 1.103), snow_m, scale=(1.8, 0.35, 0.18), parent=snowg)

# ---- tashqi qulf ----
lockE = empty("lockE", tuple(P0), yard); lockE.rotation_euler = (0, 0, R(180))
lockL = empty("lockL", (0, 0, -(SZ + SRA - SWR) - 0.0025), lockE)
LK = build_lock("lk", lockL)
drainE = empty("drainE", tuple(DRAIN + Vector((0, 0, -0.0005))), LK["root"])
keyholeE = empty("keyholeE", (0, -D / 2, PZ), LK["root"])
lockC = empty("lockC", (0, 0, H / 2), LK["root"])
# qor: qulf ustida
snowcap = sphere("snowcap", 0.026, (0, 0, H + 0.002), snow_m, scale=(1.0, 0.6, 0.18), parent=LK["root"])
vis(yard, rng(*EXT))
vis(snowcap, rng(*WINTER))
vis(snowg, rng(*WINTER))
# tomchilar (ho'l qulf)
for d in P.drops_on(LK["body"], 70, 0.0005, 0.0013, drop_m, seed=3, region=lambda p: p.z > 0.004): vis(d, rng(*WET), False)
# qulf teskari (moy tomizish): osilgan nuqta atrofida
key(lockE, 1, rot=(0, 0, 180)); key(lockE, FLIP - 1, rot=(0, 0, 180)); key(lockE, FLIP, rot=(0, 180, 180))
key(lockE, S["mech"][0], rot=(0, 180, 180)); key(lockE, S["pop"][0], rot=(0, 0, 180))
interp(lockE, "CONSTANT")
# kamon ochiladi
shk = LK["shackle"]
key(shk, 1, loc=(0, 0, 0), rot=(0, 0, 0)); key(shk, POP, loc=(0, 0, 0), rot=(0, 0, 0))
key(shk, POP + 2, loc=(0, 0, 0.013)); key(shk, POP + 4, loc=(0, 0, 0.011)); key(shk, POP + 6, loc=(0, 0, 0.012))
key(shk, POP + 12, rot=(0, 0, 0)); key(shk, POP + 18, rot=(0, 0, 0))

# ---- kalitlar: qo'lda (o'ylash), erkin (teshikka tiqish), qulfda (muzlagan / ochish) ----
keyLock = empty("keyLock_p", (0, -D / 2 - 0.0002, PZ), LK["root"])
kL = build_key("keyLock", keyLock, M["keymat"])
vis(keyLock, rng("stuck", "pop"))
key(keyLock, 1, rot=(0, 0, 0)); key(keyLock, POP - 6, rot=(0, 0, 0)); key(keyLock, POP - 1, rot=(0, 85, 0))
# erkin kalit: uchi yuqoriga (drenaj teshigi tomon)
keyFree = empty("keyFree", (0, 0, 0))
kF = build_key("keyF", keyFree, M["keymat"])
keyFree.rotation_euler = (R(90), R(0), R(15))
vis(keyFree, rng("keytry"))

# ---- moy: qo'lda moydon + makro moydon ----
oilmac = empty("oilmac", (0, 0, 0))
ocan2 = import_gltf(PH + "small_oil_can_01/small_oil_can_01.gltf", oilmac)
oilmac.scale = (1, 1, 1)
vis(oilmac, rng("oildrop"))

# ======================================================================
# 2) MEGAN
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx")
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
soften(mmeshes)
sc.render.fps = 24                               # FBX importi sahnani 30 fps ga o'zgartiradi
def A_(f):
    a = mc.load_action(f, True); sc.render.fps = 24; return a
mc.add_strip(meg, A_("Breathing_Idle.fbx"), -40, blend=0, repeat=12.0)
def strip(act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(meg, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
OPEN = A_("Opening_2.fbx")
strip(OPEN, -15, blend=0, bout=6)                                 # 1: qulfni ushlaydi
strip(A_("Thinking.fbx"), 75, blend=0, bout=6)                    # 3: o'ylaydi
strip(A_("Pull_Heavy_Object.fbx"), 615, blend=0, bout=4, repeat=4.0)   # 12: tortadi
strip(OPEN, 778, blend=0, bout=6)                                 # 15: moy
strip(A_("Happy.fbx"), 925, blend=0, bout=6, speed=1.2)           # 18: quvonadi
ROOT = {"hook": ((0.0, 0.0, 0), 0), "think": ((0.05, 0.12, 0), -8), "stuck": ((-0.12, 0.09, 0), 0),
        "oilmeg": ((0.03, 0.04, 0), 0), "pop": ((0.12, 0.28, 0), 12)}
for f, n in SHOTS:
    p, rz = ROOT.get(n, ((0, 0, 0), 0)); key(mroot, f, loc=p, rot=(0, 0, rz))
interp(mroot, "CONSTANT")
vis(mroot, rng(*MEG))
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.09, 0.08), headE)
palmR = child_of_bone("meg_palmR", meg, "RightHand")
palmL = child_of_bone("meg_palmL", meg, "LeftHand")
keyHand = empty("keyHand", (0, 0.07, 0.03), palmL)            # Hand: Y barmoqlar, Z kaft
kH = build_key("keyH", keyHand, M["keymat"]); keyHand.rotation_euler = (R(90), 0, R(90))
vis(keyHand, rng("think"))
oilR = empty("oilR", (0, 0.06, 0.03), palmR)
ocan = import_gltf(PH + "small_oil_can_01/small_oil_can_01.gltf", oilR)
oilR.rotation_euler = (R(-90), R(-90), 0); oilR.scale = (0.85,) * 3
for o in ocan:
    if o.parent == oilR: o.location = (0.06, 0, -0.12)
vis(oilR, rng("oilmeg"))

# ======================================================================
# 3) KESIM STUDIYASI (qulf x10)
# ======================================================================
SO = Vector((40.0, 0.0, 0.5))
studio = empty("studio", tuple(SO))
cutS = empty("cutS", (0, 0, 0), studio); cutS.scale = (10, 10, 10)
LC = build_lock("lc", cutS, cutaway=True)
plane("studio_floor", (8, 8), (0, 0, -0.02), mat("sfloor", (0.02, 0.025, 0.03), 0.35, coat=0.5), parent=studio)
vis(studio, rng(*STUDIO))
cavT = empty("cavT", (0.003, 0.0, 0.010), LC["root"])
sprT = empty("sprT", (0.0, -0.001, 0.031), LC["root"])
drT = empty("drT", (0.0, DRAIN.y, 0.002), LC["root"])
plugT = empty("plugT", (0.0, -0.002, PZ), LC["root"])
# pinlar: kalitsiz pastda; 'mech' da kalit kiradi -> pinlar tekislanadi, silindr buriladi
ME0, ME1 = S["mech"]
KIN = ME0 + 8
for stack, sp, L0 in LC["pins"]:
    for f, dz in ((1, LOCKED), (ME0, LOCKED), (KIN, 0.0)):
        key(stack, f, loc=(0, stack.location.y, dz))
        sp.scale = (1, 1, (CH_TOP - (SL + DRV_L + dz)) / L0); sp.keyframe_insert("scale", frame=f)
keyS = empty("keyS_p", (0, -D / 2 - 0.0002, 0), LC["plugp"])
kS = build_key("keyS", keyS, M["keymat"])
key(keyS, 1, loc=(0, -D / 2 - 0.022, 0)); key(keyS, ME0, loc=(0, -D / 2 - 0.022, 0)); key(keyS, KIN, loc=(0, -D / 2 - 0.0002, 0))
vis(keyS, rng("mech"))
# pinlar tekislangach kamon ko'tariladi (qulf ochiladi)
shc = LC["shackle"]
key(shc, 1, loc=(0, 0, 0)); key(shc, ME0 + 16, loc=(0, 0, 0)); key(shc, ME0 + 19, loc=(0, 0, 0.009)); key(shc, ME0 + 21, loc=(0, 0, 0.0075))
# suv: bo'shliqda sath ko'tariladi -> muzlaydi -> drenajdan chiqadi
water = box("water", (0.0067, 0.0215, 1.0), (0.0002 + 0.00335, -0.0005, 0.5), water_m)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
water.parent = LC["root"]; water.location = (0, 0, 0.004)
PO0, PO1 = S["pool"]; FR0, FR1 = S["freeze"]; DR0, DR1 = S["drain"]
LV = 0.0115
for f, h in ((1, 0.0001), (PO0, 0.0001), (PO0 + 10, 0.0004), (PO1 - 4, LV), (S["drain"][0] + 6, LV), (DR1 - 4, 0.0004), (DR1, 0.0001)):
    key(water, f, scale=(1, 1, h))
vis(water, rng("pool", "stay", "rust", "freeze", "drain"))
for f, v in ((1, 0.0), (FR0 + 4, 0.0), (FR0 + 34, 1.0), (FR1 + 1, 0.0)): val_key(water_m, "ice", f, v)
interp(water_m.node_tree, "LINEAR")
for fc in mc._fcurves(water_m.node_tree.animation_data.action):
    for k in fc.keyframe_points:
        if k.co.x >= FR1: k.interpolation = "CONSTANT"
# muz kristallari
crys = empty("crystals", (0, 0, 0), LC["root"])
ice_c = mat("ice_c", (0.85, 0.95, 1.0), 0.15, emit=0.6, ecol=(0.6, 0.85, 1.0), coat=1.0)
rc = random.Random(4)
for i in range(46):
    p = (rc.uniform(0.0006, 0.0062), rc.uniform(-0.011, 0.0095), rc.uniform(0.0045, 0.0045 + LV - 0.001))
    s_ = sphere(f"crys{i}", 1.0, p, ice_c, scale=(0.0006, 0.0006, rc.uniform(0.0015, 0.003)), sub=1, parent=crys)
    s_.rotation_euler = (rc.uniform(-1.2, 1.2), rc.uniform(-1.2, 1.2), rc.uniform(0, 6.3))
    s1 = s_.scale.copy(); a = FR0 + 6 + rc.randint(0, 22)
    s_.scale = (0.00001,) * 3; s_.keyframe_insert("scale", frame=a)
    s_.scale = s1; s_.keyframe_insert("scale", frame=a + 10)
vis(crys, rng("freeze"))
# kalit teshigidan kiruvchi tomchilar ('pool')
def drops_path(name, pts, n, f0, f1, dur, m, parent, r, seed=1):
    rp = random.Random(seed); out = []
    for i in range(n):
        s_ = sphere(f"{name}{i}", r * rp.uniform(0.7, 1.2), pts[0], m, scale=(1, 1, 1.3), sub=2, parent=parent)
        a = f0 + int((f1 - f0 - dur) * i / max(1, n - 1)) + rp.randint(-2, 2); b = a + dur
        for f in range(a, b + 1):
            t = (f - a) / dur; seg = t * (len(pts) - 1); k = min(int(seg), len(pts) - 2); u = seg - k
            u = u * u if k == len(pts) - 2 else u
            s_.location = Vector(pts[k]).lerp(Vector(pts[k + 1]), u); s_.keyframe_insert("location", frame=f)
        scale_vis(s_, max(1, a), b); out.append(s_)
    return out
win = [(0.0012, -D / 2 - 0.002, PZ + 0.003), (0.0012, -D / 2 + 0.003, PZ - 0.0035), (0.0015, -0.006, 0.0085), (0.0018, -0.004, 0.0045)]
drops_path("indrop", win, 9, PO0, PO1 + 30, 16, water_m, LC["root"], 0.0009, 2)
# drenaj: suv kanaldan pastga oqadi
dout = [(0.0006, DRAIN.y, 0.0045), (0.0006, DRAIN.y, -0.001), (0.0006, DRAIN.y, -0.02), (0.0006, DRAIN.y, -0.05)]
drops_path("outdrop", dout, 22, DR0 + 4, DR1 + 2, 14, water_m, LC["root"], 0.0009, 3)
# zang: 'rust' kadrida 0 -> 1 (timelapse); 'mech' da qisman zang + moy
RU0, RU1 = S["rust"]
for m in RUST_MATS:
    for f, v in ((1, 0.0), (RU0, 0.0), (RU0 + 8, 0.08), (RU1 - 6, 1.0), (RU1 + 1, 0.0), (ME0 - 1, 0.0), (ME0, 0.18), (S["pop"][0], 0.0)):
        val_key(m, "rust", f, v)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR" if RU0 <= k.co.x < RU1 - 6 else "CONSTANT"
    if "oil" in m.node_tree.nodes:
        for f, v in ((1, 0.0), (ME0, 0.2), (ME0 + 16, 1.0), (S["pop"][0], 0.0)): val_key(m, "oil", f, v)
# qirov va namlik (tashqi qulf)
for nm in ("brass", "steel"):
    m = M[nm]
    for f, n in SHOTS:
        val_key(m, "frost", f, {"snow": 0.3, "stuck": 0.55}.get(n, 0.0))
        val_key(m, "wet", f, 1.0 if n in WET else 0.0)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        if "frost" in fc.data_path or "wet" in fc.data_path:
            for k in fc.keyframe_points: k.interpolation = "CONSTANT"
for m in (pave, grav): state_keys(m, "wet", {n: 1.0 for n in WET})
# moy tomchilari ichkarida ('mech')
oin = [(0.0012, DRAIN.y, -0.004), (0.0012, DRAIN.y, 0.004), (0.0014, 0.0, 0.0085), (0.0016, -0.004, PZ - PR - 0.0003)]
drops_path("oilin", oin, 6, ME0 - 4, ME1, 12, oil_m, LC["root"], 0.0009, 5)

# ======================================================================
# 4) MAKRO: tomchilar (tashqi qulf)
# ======================================================================
EN0, EN1 = S["enter"]; DP0, DP1 = S["drip"]; OD0, OD1 = S["oildrop"]
# 7: old yuzadan oqib kalit teshigiga kiradi
paths = [[(0.006, -D / 2 - 0.0004, 0.039), (0.004, -D / 2 - 0.0005, 0.030), (0.0012, -D / 2 - 0.0005, PZ + 0.0045), (0.0, -D / 2 + 0.003, PZ)],
         [(-0.008, -D / 2 - 0.0004, 0.037), (-0.004, -D / 2 - 0.0005, 0.027), (-0.001, -D / 2 - 0.0005, PZ + 0.004), (0.0, -D / 2 + 0.003, PZ - 0.001)]]
dd = []
for j, pth in enumerate(paths):
    dd += drops_path(f"endrop{j}_", pth, 3, EN0 - 6 + j * 9, EN1, 30, drop_m, LK["root"], 0.0028, 7 + j)
# 14: drenaj teshigidan tomchilar tushadi (sekin)
for i in range(5):
    d = sphere(f"drip{i}", 0.0017, tuple(DRAIN), drop_m, scale=(1, 1, 1), sub=3, parent=LK["root"])
    a = DP0 - 8 + i * 11; grow = a + 7
    key(d, a, loc=tuple(DRAIN + Vector((0, 0, -0.0004))), scale=(0.3, 0.3, 0.2))
    key(d, grow, loc=tuple(DRAIN + Vector((0, 0, -0.0012))), scale=(1, 1, 1.25))
    for k in range(1, 12):
        t = k / 11; key(d, grow + k * 2, loc=tuple(DRAIN + Vector((0, 0, -0.0012 - 0.09 * t * t))), scale=(0.9, 0.9, 1.5))
    d.hide_render = True; d.keyframe_insert("hide_render", frame=1)
    d.hide_render = False; d.keyframe_insert("hide_render", frame=DP0)
    d.hide_render = True; d.keyframe_insert("hide_render", frame=DP1 + 1)
    interp(d, "CONSTANT", "hide_render")
# 16: moy tomchilari (qulf teskari: drenaj tepada)
OILTIP = Vector((0.1754, 0.0, 0.2332))
oilmac.parent = LK["root"]
oilmac.location = tuple(DRAIN + Vector((0.0, 0.0, -0.022)) - Matrix.Rotation(R(200), 3, "X") @ (OILTIP * 0.0))
# moydon: uchi drenaj teshigi ustida (qulf mahalliy koordinatasida drenaj -Z da, chunki qulf teskari)
oilmac.rotation_euler = (R(180), R(25), R(90))
bpy.context.view_layer.update()
tipw = oilmac.matrix_world @ OILTIP; want = LK["root"].matrix_world @ (DRAIN + Vector((0, 0, -0.016)))
# nozzle uchini kerakli joyga siljitamiz (lokal koordinatada)
inv = LK["root"].matrix_world.inverted()
oilmac.location = Vector(oilmac.location) + (inv @ want - inv @ tipw)
for i in range(4):
    d = sphere(f"oild{i}", 0.0011, tuple(DRAIN), oil_m, scale=(1, 1, 1), sub=3, parent=LK["root"])
    a = OD0 + 6 + i * 11
    start = DRAIN + Vector((0, 0, -0.0155)); endp = DRAIN + Vector((0, 0, -0.0004))
    key(d, a, loc=tuple(start), scale=(0.4, 0.4, 0.4)); key(d, a + 5, loc=tuple(start), scale=(1, 1, 1.3))
    for k in range(1, 7):
        t = k / 6; key(d, a + 5 + k, loc=tuple(start.lerp(endp, t * t)), scale=(0.85, 0.85, 1.6))
    key(d, a + 13, loc=tuple(endp + Vector((0, 0, 0.001))), scale=(0.2, 0.2, 0.2))
    d.hide_render = True; d.keyframe_insert("hide_render", frame=1)
    d.hide_render = False; d.keyframe_insert("hide_render", frame=a)
    d.hide_render = True; d.keyframe_insert("hide_render", frame=a + 14)
    interp(d, "CONSTANT", "hide_render")

# ======================================================================
# 5) YOMG'IR VA QOR (Geometry Nodes, qayta aylanmaydi: har tomchi bir marta tushadi)
# ======================================================================
def precip(name, region, count, speed, shape, m, t0, dur, sway=0.0, seed=1):
    (x0, x1), (y0, y1), (z0, z1) = region
    Hc = (z1 - z0) + speed * dur
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pts = N.new("GeometryNodePoints"); pts.inputs["Count"].default_value = count
    idx = N.new("GeometryNodeInputIndex")
    rv = N.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT_VECTOR"
    vin = [s for s in rv.inputs if s.type == "VECTOR"]
    vin[0].default_value = (x0, y0, 0.0); vin[1].default_value = (x1, y1, 1.0)
    L.new(idx.outputs[0], rv.inputs["ID"]); rv.inputs["Seed"].default_value = seed
    vout = [s for s in rv.outputs if s.type == "VECTOR"][0]
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(vout, sep.inputs[0])
    tm = N.new("GeometryNodeInputSceneTime")
    def M_(op, a, b):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    t = M_("SUBTRACT", tm.outputs["Seconds"], t0)
    z = M_("SUBTRACT", M_("ADD", z0, M_("MULTIPLY", sep.outputs["Z"], Hc)), M_("MULTIPLY", t, speed))
    x = sep.outputs["X"]; y = sep.outputs["Y"]
    if sway:
        ph = M_("MULTIPLY", sep.outputs["Z"], 40.0)
        x = M_("ADD", x, M_("MULTIPLY", M_("SINE", M_("ADD", M_("MULTIPLY", t, 1.7), ph), 0), sway))
        y = M_("ADD", y, M_("MULTIPLY", M_("COSINE", M_("ADD", M_("MULTIPLY", t, 1.3), ph), 0), sway))
    cb = N.new("ShaderNodeCombineXYZ"); L.new(x, cb.inputs[0]); L.new(y, cb.inputs[1]); L.new(z, cb.inputs[2])
    L.new(cb.outputs[0], pts.inputs["Position"])
    if shape[0] == "cyl":
        sh = N.new("GeometryNodeMeshCylinder"); sh.inputs["Vertices"].default_value = 6
        sh.inputs["Radius"].default_value = shape[1]; sh.inputs["Depth"].default_value = shape[2]
    else:
        sh = N.new("GeometryNodeMeshIcoSphere"); sh.inputs["Radius"].default_value = shape[1]; sh.inputs["Subdivisions"].default_value = 1
    ins = N.new("GeometryNodeInstanceOnPoints"); L.new(pts.outputs[0], ins.inputs["Points"]); L.new(sh.outputs["Mesh"], ins.inputs["Instance"])
    rs = N.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"
    fin = [s for s in rs.inputs if s.type == "VALUE"]; fin[0].default_value = 0.5; fin[1].default_value = 1.3
    L.new(idx.outputs[0], rs.inputs["ID"])
    L.new([s for s in rs.outputs if s.type == "VALUE"][0], ins.inputs["Scale"])
    re = N.new("GeometryNodeRealizeInstances"); L.new(ins.outputs[0], re.inputs[0])
    smn = N.new("GeometryNodeSetMaterial"); smn.inputs["Material"].default_value = m; L.new(re.outputs[0], smn.inputs["Geometry"])
    L.new(smn.outputs[0], go.inputs[0])
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    mod = o.modifiers.new("gn", "NODES"); mod.node_group = ng
    return o
rain_m = mat("rain", (0.9, 0.95, 1.0), 0.05, trans=0.7, emit=3.0, ecol=(0.8, 0.88, 1.0))
flake_m = mat("flake", (1.0, 1.0, 1.0), 0.6, sss=0.4, sss_scale=0.002, emit=0.3, ecol=(0.9, 0.95, 1.0))
RA0, RA1 = S["rain"]; SN0, SN1 = S["snow"]; ST0, ST1 = S["stuck"]
rain = precip("rain", ((-1.2, 1.6), (GY + 0.02, 1.6), (0.0, 2.6)), 16000, 8.0, ("cyl", 0.0014, 0.09), rain_m,
              (RA0 - 1) / 24.0, (RA1 - RA0 + 2) / 24.0, seed=3)
vis(rain, rng("rain"))
snow = precip("snow", ((-1.4, 1.4), (GY + 0.03, 1.6), (0.3, 2.6)), 3500, 0.55, ("ico", 0.0035), flake_m,
              (SN0 - 1) / 24.0, (SN1 - SN0 + 2) / 24.0, sway=0.03, seed=5)
vis(snow, rng("snow"))
snow2 = precip("snow2", ((-1.6, 1.6), (GY + 0.03, 2.4), (0.2, 2.8)), 4500, 0.7, ("ico", 0.004), flake_m,
               (ST0 - 1) / 24.0, (ST1 - ST0 + 2) / 24.0, sway=0.03, seed=8)
vis(snow2, rng("stuck"))

# ======================================================================
# 6) KAMERALAR
# ======================================================================
bpy.context.view_layer.update()
LCw = lockC.matrix_world.translation.copy()           # qulf markazi (dunyo)
def W_(e, f=1):
    sc.frame_set(f); return e.matrix_world.translation.copy()
DRw = W_(drainE)
KHw = W_(keyholeE)
print("LOCK", tuple(round(v, 3) for v in LCw), "DRAIN", tuple(round(v, 3) for v in DRw), "KEYHOLE", tuple(round(v, 3) for v in KHw))
def V(*a): return Vector(a)
# 1 ilgak: pastdan keng plan -> qulfga tez push-in
HO0, HO1 = S["hook"]
hookT = empty("hookT", (0, 0, 0))
key(hookT, HO0, loc=tuple(LCw + V(0.0, 0.18, 0.2))); key(hookT, HO0 + 20, loc=tuple(LCw + V(0.0, 0.08, 0.06))); key(hookT, HO1, loc=tuple(LCw))
c = shot_cam("hook", (0, 0, 0), hookT, 16, 4.0, focus=lockC)
path_keys(c, ((HO0, tuple(LCw + V(0.3, 0.3, -0.34))), (HO0 + 20, tuple(LCw + V(0.2, 0.22, -0.18))), (HO1, tuple(LCw + V(0.1, 0.12, -0.04)))))
lens_keys(c, ((HO0, 16), (HO0 + 20, 20), (HO1, 30)))
# 2 makro: qulf tagi, teshik atrofida aylanadi
HL0, HL1 = S["hole"]
c = shot_cam("hole", (0, 0, 0), drainE, 32, 18.0, focus=drainE, clip=0.001)
for f in range(HL0, HL1 + 1, 3):
    t = (f - HL0) / (HL1 - HL0); a = R(-40 + 80 * t); rr = 0.05 - 0.012 * t
    key(c, f, loc=tuple(DRw + V(rr * math.sin(a), rr * math.cos(a), -0.085 + 0.022 * t)))
interp(c, "LINEAR", "location")
# 3 o'ylash: yuzga yaqin
TH0, TH1 = S["think"]
c = shot_cam("think", (0, 0, 0), faceT, 48, 2.0, focus=faceT)
path_keys(c, ((TH0, (0.62, -0.42, 1.38)), (TH1, (0.5, -0.36, 1.43))))
# 4 kalit teshikka sig'maydi
KT0, KT1 = S["keytry"]
kp0 = DRw + V(0.0, 0.0, -0.045); kp1 = DRw + V(0.0, 0.0, -0.0225)
key(keyFree, KT0, loc=tuple(kp0)); key(keyFree, BUMP - 6, loc=tuple(kp1 - V(0, 0, 0.004))); key(keyFree, BUMP, loc=tuple(kp1))
key(keyFree, BUMP + 3, loc=tuple(kp1 - V(0.0, 0.0, 0.003))); key(keyFree, BUMP + 6, loc=tuple(kp1))
key(keyFree, BUMP + 9, loc=tuple(kp1 - V(0.001, 0, 0.002))); key(keyFree, BUMP + 12, loc=tuple(kp1 + V(0.0015, 0, 0)))
key(keyFree, KT1, loc=tuple(kp1 - V(0, 0, 0.02)))
for f, rz in ((KT0, 15), (BUMP + 6, 15), (BUMP + 9, 22), (BUMP + 12, 8), (KT1, 15)): key(keyFree, f, rot=(90, 0, rz))
ktT = empty("ktT", tuple(DRw + V(0, 0, -0.008)))
c = shot_cam("keytry", (0, 0, 0), ktT, 34, 16.0, focus=drainE, clip=0.001)
path_keys(c, ((KT0, tuple(DRw + V(0.095, 0.045, -0.022))), (KT1, tuple(DRw + V(0.075, 0.03, -0.016)))))
shake(c, BUMP, BUMP + 10, 0.002, 2)
# 5 yomg'ir: keng plan, sekin dolly
c = shot_cam("rain", (0, 0, 0), lockC, 22, 4.0, focus=lockC)
path_keys(c, ((RA0, tuple(LCw + V(0.65, 0.85, -0.3))), (RA1, tuple(LCw + V(0.35, 0.5, -0.15)))))
# 6 qor: past burchak
snT = empty("snT", tuple(LCw + V(0, 0, 0.03)))
c = shot_cam("snow", (0, 0, 0), snT, 20, 5.6, focus=lockC)
path_keys(c, ((SN0, tuple(LCw + V(0.28, 0.24, -0.27))), (SN1, tuple(LCw + V(0.18, 0.18, -0.2)))))
# 7 makro: tomchi kalit teshigiga kiradi
enT = empty("enT", tuple(KHw + V(0, 0, 0.008)))
c = shot_cam("enter", (0, 0, 0), enT, 40, 16.0, focus=keyholeE, clip=0.001)
path_keys(c, ((EN0, tuple(KHw + V(0.05, 0.11, 0.025))), (EN1, tuple(KHw + V(0.025, 0.075, 0.012)))))
# 8-11, 13, 17: studiya
def SW(e): return W_(e)
cav = SW(cavT); spr = SW(sprT); drs = SW(drT); plg = SW(plugT)
PO0, PO1 = S["pool"]; SY0, SY1 = S["stay"]
c = shot_cam("pool", (0, 0, 0), cavT, 32, 5.6, focus=cavT)
path_keys(c, ((PO0, tuple(cav + V(-1.05, -0.6, 0.35))), (PO1, tuple(cav + V(-0.8, -0.42, 0.22)))))
c = shot_cam("stay", (0, 0, 0), cavT, 36, 5.6, focus=cavT)
for f in range(SY0, SY1 + 1, 2):
    t = (f - SY0) / (SY1 - SY0); a = R(-35 + 50 * t)
    key(c, f, loc=tuple(cav + V(-0.75 * math.cos(a), 0.75 * math.sin(a), 0.12 - 0.08 * t)))
interp(c, "LINEAR", "location")
c = shot_cam("rust", (0, 0, 0), sprT, 50, 8.0, focus=sprT)
path_keys(c, ((RU0, tuple(spr + V(-0.42, -0.3, 0.12))), (RU1, tuple(spr + V(-0.33, -0.12, 0.02)))))
c = shot_cam("freeze", (0, 0, 0), cavT, 30, 5.6, focus=cavT)
path_keys(c, ((FR0, tuple(cav + V(-0.75, -0.5, -0.12))), (FR1, tuple(cav + V(-0.58, -0.38, -0.05)))))
shake(c, FR0 + 30, FR0 + 40, 0.006, 3)
drT2 = empty("drT2", tuple(drs + V(0, 0, -0.12)))
c = shot_cam("drain", (0, 0, 0), drT2, 30, 5.6, focus=drT)
path_keys(c, ((DR0, tuple(drs + V(-0.85, -0.55, 0.05))), (DR1, tuple(drs + V(-0.7, -0.4, -0.08)))))
c = shot_cam("mech", (0, 0, 0), plugT, 34, 5.6, focus=plugT)
path_keys(c, ((ME0, tuple(plg + V(-0.6, -0.45, 0.3))), (ME1, tuple(plg + V(-0.5, -0.3, 0.2)))))
lens_keys(c, ((ME0, 32), (ME1, 40)))
# 12 muzlagan qulf: tortadi -> crash zoom
stT = empty("stT", (0, 0, 0))
key(stT, ST0, loc=tuple(LCw + V(0.0, 0.3, 0.15))); key(stT, CRASH - 1, loc=tuple(LCw + V(0.0, 0.2, 0.1))); key(stT, CRASH + 2, loc=tuple(LCw))
interp(stT, "LINEAR")
c = shot_cam("stuck", (0, 0, 0), stT, 18, 4.0, focus=lockC)
path_keys(c, ((ST0, tuple(LCw + V(0.9, 0.55, -0.55))), (CRASH - 1, tuple(LCw + V(0.75, 0.45, -0.45))), (CRASH + 3, tuple(LCw + V(0.2, 0.17, -0.07))), (ST1, tuple(LCw + V(0.17, 0.15, -0.05)))))
lens_keys(c, ((ST0, 18), (CRASH - 1, 20), (CRASH + 3, 45), (ST1, 50)))
shake(c, ST0 + 4, CRASH, 0.01, 4, decay=False); shake(c, CRASH + 3, ST1, 0.004, 5, decay=False)
# 14 makro: tomchilar teshikdan tushadi (pastdan)
dpT = empty("dpT", tuple(DRw + V(0, 0, -0.025)))
c = shot_cam("drip", (0, 0, 0), dpT, 45, 16.0, focus=drainE, clip=0.001)
path_keys(c, ((DP0, tuple(DRw + V(0.06, 0.08, -0.06))), (DP1, tuple(DRw + V(0.045, 0.065, -0.05)))))
# 15 moy: qiz moydon bilan
OM0, OM1 = S["oilmeg"]
omT = empty("omT", (0, 0, 0)); key(omT, OM0, loc=tuple(LCw + V(0.05, 0.25, 0.15))); key(omT, OM1, loc=tuple(LCw + V(0.0, 0.15, 0.12)))
c = shot_cam("oilmeg", (0, 0, 0), omT, 22, 4.0, focus=lockC)
path_keys(c, ((OM0, tuple(LCw + V(0.75, 0.5, -0.45))), (OM1, tuple(LCw + V(0.55, 0.38, -0.32)))))
# 16 makro: teskari qulf, moy tomchilari teshikka
DRf = W_(drainE, OD0)
odT = empty("odT", tuple(DRf + V(0, 0, 0.008)))
c = shot_cam("oildrop", (0, 0, 0), odT, 40, 16.0, focus=odT, clip=0.001)
path_keys(c, ((OD0, tuple(DRf + V(0.11, 0.075, 0.03))), (OD1, tuple(DRf + V(0.09, 0.06, 0.025)))))
# 18 ochiladi: yon tomondan, qulf + qiz
PP0, PP1 = S["pop"]
FACEw = W_(faceT, PP1 - 4)
ppT = empty("ppT", (0, 0, 0)); key(ppT, PP0, loc=tuple(LCw + V(0, 0.0, 0.01))); key(ppT, POP + 5, loc=tuple(LCw + V(0, 0.0, 0.015)))
key(ppT, POP + 12, loc=tuple(FACEw)); key(ppT, PP1, loc=tuple(FACEw))
ppF = empty("ppF", (0, 0, 0)); key(ppF, PP0, loc=tuple(LCw)); key(ppF, POP + 6, loc=tuple(LCw)); key(ppF, POP + 12, loc=tuple(FACEw)); key(ppF, PP1, loc=tuple(FACEw))
c = shot_cam("pop", (0, 0, 0), ppT, 35, 4.0, focus=ppF)
path_keys(c, ((PP0, tuple(LCw + V(0.2, 0.2, -0.04))), (POP + 5, tuple(LCw + V(0.22, 0.24, -0.03))), (PP1, tuple(LCw + V(0.3, 0.3, 0.0)))))
lens_keys(c, ((PP0, 38), (POP + 5, 40), (PP1, 30)))
shake(c, POP, POP + 10, 0.006, 6)
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
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(110)); L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; L.new(env.outputs[0], tint.inputs[6])
sat = N.new("ShaderNodeHueSaturation"); L.new(tint.outputs[2], sat.inputs["Color"])
bg_sky = N.new("ShaderNodeBackground"); L.new(sat.outputs[0], bg_sky.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.006, 0.012, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_sky.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WEATHER = {}
for n in EXT: WEATHER[n] = (1.0, (1, 1, 1), 1.0)
for n in ("rain",): WEATHER[n] = (0.22, (0.55, 0.62, 0.75), 0.25)
for n in ("enter", "drip"): WEATHER[n] = (0.55, (0.8, 0.85, 0.95), 0.6)
for n in WINTER: WEATHER[n] = (0.75, (0.75, 0.85, 1.0), 0.35)
for f, n in SHOTS:
    s1, tc_, st_ = WEATHER.get(n, (0.0, (1, 1, 1), 1.0))
    bg_sky.inputs[1].default_value = s1; bg_sky.inputs[1].keyframe_insert("default_value", frame=f)
    bg_dk.inputs[1].default_value = 0.0 if n in EXT else 1.0; bg_dk.inputs[1].keyframe_insert("default_value", frame=f)
    tint.inputs[7].default_value = (*tc_, 1); tint.inputs[7].keyframe_insert("default_value", frame=f)
    tint.inputs["Factor"].default_value = 1.0
    sat.inputs["Saturation"].default_value = st_; sat.inputs["Saturation"].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
SUNNY = [n for n in EXT if n not in WET and n not in WINTER]
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.9, 0.78); sun.rotation_euler = (R(50), 0, R(140))
for f, n in SHOTS:
    sun.data.energy = 4.0 if n in SUNNY else (1.2 if n in WINTER else 0.0); sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("face_fill", (0.9, -0.9, 1.7), 0.8, (1.0, 0.9, 0.8), lights_for(rng(*MEG), 40.0), target=faceT)
area("lock_fill", tuple(LCw + V(0.25, 0.35, 0.15)), 0.25, (1.0, 0.95, 0.9), lights_for(rng(*EXT), 6.0), target=lockC)
area("macro_under", tuple(DRw + V(0.05, 0.08, -0.08)), 0.08, (1.0, 0.95, 0.9), lights_for(rng("hole", "keytry", "drip"), 1.2), target=drainE)
# yomg'ir: orqadan yorug'lik (tomchilar ko'rinishi uchun) + sovuq to'ldiruvchi
area("rain_back", tuple(LCw + V(-1.2, -0.0, 1.4)), 1.5, (0.75, 0.85, 1.0), lights_for(rng("rain"), 120.0), target=lockC)
area("rain_fill", tuple(LCw + V(1.5, 2.0, 0.8)), 2.0, (0.6, 0.7, 0.9), lights_for(rng("rain"), 60.0), target=lockC)
area("winter_fill", tuple(LCw + V(1.0, 1.4, 0.6)), 1.5, (0.8, 0.88, 1.0), lights_for(rng(*WINTER), 50.0), target=lockC)
# studiya
cavW = cav
area("s_key", tuple(cavW + V(-1.6, -1.4, 1.4)), 1.2, (1.0, 0.92, 0.85), lights_for(rng(*STUDIO), 220.0), target=cavT)
area("s_rim", tuple(cavW + V(0.8, 1.6, 1.2)), 1.2, (0.35, 0.6, 1.0), lights_for(rng(*STUDIO), 350.0), target=cavT)
area("s_low", tuple(cavW + V(-1.2, 0.8, -0.6)), 0.8, (1.0, 0.55, 0.35), lights_for(rng(*STUDIO), 90.0), target=cavT)
# zang timelapse: yorug'lik miltillashi
tl = area("s_time", tuple(cavW + V(-0.9, -0.2, 0.9)), 0.6, (1.0, 0.8, 0.6), [(1, 0)], target=sprT)
for f in range(RU0, RU1 + 1, 3):
    tl.data.energy = 60.0 * (0.5 + 0.5 * math.sin((f - RU0) * 0.9)); tl.data.keyframe_insert("energy", frame=f)
tl.data.energy = 0; tl.data.keyframe_insert("energy", frame=RU1 + 1)
interp(tl.data, "CONSTANT")
# muzlash: ko'k yorug'lik kuchayadi
fb = point("s_ice", tuple(cavW + V(-0.25, -0.1, -0.02)), 0.15, (0.4, 0.75, 1.0), [(1, 0), (FR0, 2.0), (FR0 + 34, 30.0), (FR1 + 1, 0)], const=False)
for fc in mc._fcurves(fb.data.animation_data.action):
    for k in fc.keyframe_points:
        if k.co.x >= FR1: k.interpolation = "CONSTANT"
point("s_oil", tuple(plg + V(-0.3, -0.1, 0.1)), 0.1, (1.0, 0.7, 0.3), lights_for(rng("mech"), 25.0))

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 45))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.1
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
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
