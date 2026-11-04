# Chaqmoq ursa, tanada nima bo'ladi — Zack D. Films uslubida 54.6 s video (1312 kadr, 24 fps, 9:16).
# Asos: zack_test/qulf/qulf.py, hiqichoq.py, scene3.py, mixchar.py. Kadr rejasi: STORYBOARD.md
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=45 /tmp/claude-0/bvenv/bin/python -I zack_test/chaqmoq/chaqmoq.py --render
# Sinov: FRAMES=20,150,470,640,1240 PCT=35
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish")); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
LICH = os.environ.get("LICH", "/tmp/claude-0/assets/lich.png")
LICH_ARM = os.environ.get("LICH_ARM_IMG", "/tmp/claude-0/assets/lich_arm.png")      # qalinroq chiziqlar (tana uchun)
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1312
sc.frame_start, sc.frame_end = 1, END
if not os.path.exists(LICH):
    import subprocess; subprocess.run([sys.executable, "-I", os.path.join(HERE, "lich.py"), LICH, "2048", "3"], check=True)
if not os.path.exists(LICH_ARM):
    import subprocess; subprocess.run([sys.executable, "-I", os.path.join(HERE, "lich.py"), LICH_ARM, "640", "5"], check=True)

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (32, "strike"), (62, "face"), (99, "volt"), (191, "plasma"), (266, "sun"), (337, "crawl"),
         (404, "tree"), (448, "lich"), (507, "arm"), (578, "steam"), (625, "steam2"), (674, "shoes"), (769, "ear"),
         (818, "heart"), (898, "wake"), (947, "ten"), (1056, "under"), (1120, "treehit"), (1178, "city"), (1263, "spire")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
FIELD = ["hook", "strike", "face", "tree", "arm", "steam", "steam2", "shoes", "wake", "under", "treehit"]
XRAY = ["volt", "heart"]
REMY = ["hook", "strike", "face", "volt", "arm", "steam", "steam2", "shoes", "heart", "wake", "under", "treehit"]
SKIN = ["crawl", "lich"]
HIT = 36              # chaqmoq Remyga uradi ("ursa")
SHOE = 735            # krossovkalar uchadi ("uchib")
STOP = 858            # yurak to'xtaydi ("to'xtab")
FALL = 1005           # 10-chi odam yiqiladi ("to'qqiztasi")
TREEHIT = 1131        # chaqmoq daraxtga uradi ("baland")
TOWER = (1215, 1240, 1250, 1290)   # minoraga zarbalar ("chaqmoq", "ikki", "marta", "yolg'on")

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
    d.clip_end = 6000
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
# CHAQMOQ (shoxlangan egri chiziqlar): o'sib tushadi (bevel_factor_end), miltillaydi
# ======================================================================
def bolt_paths(a, b, seed, rough=0.13, levels=7, branches=7, depth=2):
    rb = random.Random(seed)
    def mid(p, q, lv, rgh):
        pts = [Vector(p), Vector(q)]
        for _ in range(lv):
            new = [pts[0]]
            for i in range(len(pts) - 1):
                u, v = pts[i], pts[i + 1]; d = v - u; L = d.length
                n1 = d.orthogonal().normalized(); n2 = d.cross(n1).normalized()
                m = (u + v) / 2 + n1 * rb.gauss(0, rgh * L) + n2 * rb.gauss(0, rgh * L)
                new += [m, v]
            pts = new
        return pts
    out = []
    def grow(p, q, dep, rad):
        pts = mid(p, q, levels if dep == 0 else levels - 2, rough)
        out.append((pts, rad))
        if dep >= depth: return
        n = branches if dep == 0 else max(1, branches // 3)
        for _ in range(n):
            i = rb.randint(len(pts) // 12, int(len(pts) * 0.8))
            s = pts[i]; main = (Vector(q) - Vector(p)).normalized(); L = (Vector(q) - Vector(p)).length
            side = Vector((rb.uniform(-1, 1), rb.uniform(-1, 1), rb.uniform(-0.3, 0.3)))
            d = (main + side * rb.uniform(0.6, 1.3)).normalized()
            grow(s, s + d * L * rb.uniform(0.12, 0.35) * (0.6 ** dep), dep + 1, rad * 0.45)
    grow(a, b, 0, 1.0)
    return out

def bolt_mats(name, core=(0.75, 0.85, 1.0), halo=(0.45, 0.6, 1.0)):
    mc_ = bpy.data.materials.new(name + "_core"); mc_.use_nodes = True
    N = mc_.node_tree.nodes; L = mc_.node_tree.links; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*core, 1)
    g = value_node(mc_, "glow", 0.0); L.new(P.math_n(N, L, "MULTIPLY", g, 60.0), em.inputs["Strength"])
    L.new(em.outputs[0], N["Material Output"].inputs[0])
    mh = bpy.data.materials.new(name + "_halo"); mh.use_nodes = True
    N = mh.node_tree.nodes; L = mh.node_tree.links; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fac = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Fresnel"]), 3.0)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*halo, 1)
    g = value_node(mh, "glow", 0.0); L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", fac, g), 6.0), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
    return mc_, mh

def bolt(name, a, b, seed, radius, flashes, grow=3, halo_r=6.0, parent=None, **kw):
    """flashes: [(kadr, yorqinlik), ...] — birinchi kadrdan oldin 'grow' kadr davomida o'sib tushadi"""
    paths = bolt_paths(a, b, seed, **kw)
    mcore, mhalo = bolt_mats(name)
    objs = []
    for tag, r, m in (("core", radius, mcore), ("halo", radius * halo_r, mhalo)):
        cu = bpy.data.curves.new(name + tag, "CURVE"); cu.dimensions = "3D"
        cu.bevel_depth = r; cu.bevel_resolution = 2; cu.use_fill_caps = True
        cu.bevel_factor_mapping_end = "SPLINE"
        for pts, rad in paths:
            sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
            for i, p in enumerate(pts):
                sp.points[i].co = (*p, 1.0); sp.points[i].radius = rad * (1.0 - 0.6 * i / len(pts))
        o = bpy.data.objects.new(name + "_" + tag, cu); sc.collection.objects.link(o); o.data.materials.append(m)
        if parent: o.parent = parent
        objs.append(o)
    f0 = flashes[0][0]
    for cu in (objs[0].data, objs[1].data):
        cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=f0 - grow)
        cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=f0)
    for m in (mcore, mhalo):
        val_key(m, "glow", 1, 0.0); val_key(m, "glow", f0 - grow, 0.35)
        for f, v in flashes: val_key(m, "glow", f, v)
        val_key(m, "glow", flashes[-1][0] + 1, 0.0)
        interp(m.node_tree, "CONSTANT")
    on = (f0 - grow, flashes[-1][0])
    for o in objs: vis(o, [on], False)
    return objs, on

def flicker(f0, n=8, seed=1, hi=1.0):
    """chaqmoq miltillashi: [(kadr, yorqinlik)]"""
    rf = random.Random(seed); out = [(f0, hi)]
    for k in range(1, n):
        out.append((f0 + k, hi * (rf.choice((0.15, 0.5, 0.9, 1.0)) if k < n - 2 else 0.2)))
    return out

FLASH = {}                 # kadr -> osmon/yer yoritilishi (0..1)
def add_flash(fl, scale=1.0):
    for f, v in fl: FLASH[f] = max(FLASH.get(f, 0.0), v * scale)

# ======================================================================
# 1) DALA (momaqaldiroq, kecha, yomg'ir) — dunyo markazi
# ======================================================================
field = empty("field", (0, 0, 0))
ground_m = pbr("ground", "leafy_grass", 0.45, wet=True, tint=(0.4, 0.45, 0.35))
g = plane("ground", (240, 240), (0, 0, 0), ground_m, parent=field)
sub = g.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 4; sub.subdivision_type = "SIMPLE"
tx = bpy.data.textures.new("gclouds", "CLOUDS"); tx.noise_scale = 6.0
dd = g.modifiers.new("d", "DISPLACE"); dd.texture = tx; dd.strength = 0.35; dd.mid_level = 0.6
state_keys(ground_m, "wet", {n: 0.5 for n in FIELD + ["ten"]})
# o't to'plamlari (Poly Haven grass_medium_02), kameralar oldida
gtmp = empty("gtmp", (0, 0, -50))
grass_src = [o for o in import_gltf(PH + "grass_medium_02/grass_medium_02.gltf", gtmp) if o.type == "MESH"]
rg = random.Random(11)
GRASS_SPOTS = [((0, -1.0), 3.2, 70), ((-3.0, 9.0), 4.0, 50), ((0, 22), 6.0, 40)]
for (cx, cy), rad, n in GRASS_SPOTS:
    for i in range(n):
        src = rg.choice(grass_src)
        a_ = rg.uniform(0, 6.283); r_ = rad * math.sqrt(rg.random())
        x, y = cx + r_ * math.cos(a_), cy + r_ * math.sin(a_)
        if abs(x) < 0.45 and abs(y) < 0.45: continue
        o = src.copy(); sc.collection.objects.link(o); o.parent = field
        o.location = (x, y, 0.0); o.rotation_euler = (0, 0, rg.uniform(0, 6.283))
        o.scale = (rg.uniform(1.0, 1.8),) * 3
for o in grass_src: o.hide_render = True
# uzoqdagi daraxtlar qatori (qorong'i siluet)
far_m = mat("far_trees", (0.008, 0.014, 0.01), 0.95)
rt = random.Random(5)
for i in range(70):
    a_ = rt.uniform(0, 2 * math.pi); d_ = rt.uniform(70, 95); s_ = rt.uniform(3, 7)
    o = sphere("far", s_, (d_ * math.cos(a_), d_ * math.sin(a_), s_ * 0.7), far_m, scale=(1, 1, rt.uniform(1.0, 1.6)), sub=2, parent=field)
# baland daraxt (Poly Haven jacaranda_tree, ~15 m)
TREE = Vector((-4.0, 10.0, 0.0))
treeE, tree_objs = ph_model("jacaranda_tree", tuple(TREE), 30, 0.8, field)
TREETOP = TREE + Vector((0.3, 0.2, 13.8))
UNDER = TREE + Vector((1.1, -1.3, 0.0))           # Remy daraxt tagida
# daraxt yonishi: po'stloq uchqunlari va olov nuri
spark_m = mat("spark", (1.0, 0.7, 0.3), emit=40.0, ecol=(1.0, 0.65, 0.25))
rs = random.Random(21)
TH0, TH1 = S["treehit"]
for i in range(70):
    p0 = TREE + Vector((rs.uniform(-0.3, 0.3), rs.uniform(-0.3, 0.3), rs.uniform(2.0, 9.0)))
    v = Vector((rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(-0.2, 1.0))).normalized() * rs.uniform(3, 9)
    s_ = sphere(f"tspark{i}", 0.025, tuple(p0), spark_m, scale=(1, 1, 3), sub=1, parent=field)
    a = TREEHIT + rs.randint(0, 3); life = rs.randint(10, 30)
    for k in range(0, life + 1, 2):
        t = k / 24.0; p = p0 + v * t + Vector((0, 0, -4.9 * t * t)); key(s_, a + k, loc=tuple(p))
    scale_vis(s_, a, a + life)
bark_m = mat("bark_chip", (0.18, 0.12, 0.08), 0.8)
for i in range(30):
    p0 = TREE + Vector((rs.uniform(-0.2, 0.2), rs.uniform(-0.25, 0.0), rs.uniform(1.5, 6.0)))
    v = Vector((rs.uniform(-0.6, 0.6), rs.uniform(-1.0, -0.2), rs.uniform(0.0, 0.8))).normalized() * rs.uniform(3, 7)
    c_ = box(f"chip{i}", (0.06, 0.02, 0.15), tuple(p0), bark_m, parent=field)
    rv = Vector((rs.uniform(-20, 20), rs.uniform(-20, 20), rs.uniform(-20, 20)))
    for k in range(0, 41, 2):
        t = k / 24.0; p = p0 + v * t + Vector((0, 0, -4.9 * t * t))
        if p.z < 0.03: p.z = 0.03
        key(c_, TREEHIT + k, loc=tuple(p), rot=tuple(rv * k))
    scale_vis(c_, TREEHIT, TH1)

# ======================================================================
# 2) REMY (asosiy qahramon, 1.78 m)
# ======================================================================
rroot, remy, rmeshes = mc.load_character("remy", "Remy.fbx")
rroot.scale = (0.47,) * 3
RM = {o.name.split("_", 1)[1]: o for o in rmeshes}
def soften(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    n.inputs["Coat Weight"].default_value = 0.0
soften(rmeshes)
sc.render.fps = 24                               # FBX importi sahnani 30 fps ga o'zgartiradi
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm, act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0, hold=False):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=hold, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
mc.add_strip(remy, A_("Breathing_Idle.fbx"), -40, blend=0, repeat=8.0)
strip(remy, A_("Being_Electrocuted.fbx"), HIT - 1, src=(1, 128), speed=0.66, blend=0, bout=0)
strip(remy, A_("Getting_Bit.fbx"), S["arm"][0] - 35, blend=0, bout=8)
strip(remy, A_("Dizzy_Idle.fbx"), S["arm"][1] - 8, blend=8, bout=4, repeat=3.0)
strip(remy, A_("Getting_Up_3.fbx"), S["wake"][0], src=(40, 251), blend=0, bout=0)
strip(remy, A_("Catwalk_Idle_02.fbx"), S["under"][0] - 20, blend=0, bout=3, repeat=2.0)
strip(remy, A_("Flying_Back_Death.fbx", False), TREEHIT + 1, blend=2, bout=0, hold=True)
ROOT = {"under": (tuple(UNDER), 200), "treehit": (tuple(UNDER), 200)}
for f, n in SHOTS:
    p, rz = ROOT.get(n, ((0, 0, 0), 0)); key(rroot, f, loc=p, rot=(0, 0, rz))
interp(rroot, "CONSTANT")
headE = child_of_bone("remy_head", remy, "Head")
faceT = empty("faceT", (0, 0.09, 0.1), headE)          # yuz markazi (Head: X chap, Y tepa, Z old)
chestB = child_of_bone("remy_chest", remy, "Spine2")
chest = empty("chest", (0, 0, 0), chestB); chest.rotation_euler = (R(-90), 0, 0)   # ichida: Z tepa, -Y old
hipsE = child_of_bone("remy_hips", remy, "Hips")
ARM = os.environ.get("LICH_ARM", "LeftForeArm")
armE = child_of_bone("remy_arm", remy, ARM)
footL = child_of_bone("remy_footL", remy, "LeftFoot"); footR = child_of_bone("remy_footR", remy, "RightFoot")

# ---- Lichtenberg naqshi: teri materialiga (bilakka bog'langan proyeksiya) ----
lich_img = bpy.data.images.load(LICH, check_existing=True); lich_img.colorspace_settings.name = "Non-Color"
lich_arm_img = bpy.data.images.load(LICH_ARM, check_existing=True); lich_arm_img.colorspace_settings.name = "Non-Color"
def lich_nodes(m, vec, scale, offset=(0.0, 0.5), img=None):
    """I (chiziq), G (vaqt), H (halo) chiqishlari"""
    N = m.node_tree.nodes; L = m.node_tree.links
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(vec, sep.inputs[0])
    uv = N.new("ShaderNodeCombineXYZ")
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sep.outputs["Y"], 1.0 / scale), offset[0]), uv.inputs[0])
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sep.outputs["X"], 1.0 / scale), offset[1]), uv.inputs[1])
    t = N.new("ShaderNodeTexImage"); t.image = img or lich_img; t.extension = "CLIP"; t.interpolation = "Cubic"
    L.new(uv.outputs[0], t.inputs[0])
    rgb = N.new("ShaderNodeSeparateColor"); L.new(t.outputs["Color"], rgb.inputs[0])
    return rgb.outputs[0], rgb.outputs[1], rgb.outputs[2], sep

def lich_mix(m, I, G, H, grow, col_out_socket_src, b):
    """teri rangini qizil naqsh bilan aralashtiradi: 'grow' (0..1) gacha paydo bo'lgan qism"""
    N = m.node_tree.nodes; L = m.node_tree.links
    shown = P.math_n(N, L, "LESS_THAN", G, grow)
    line = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", I, shown), 0.9)
    halo = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", H, P.math_n(N, L, "LESS_THAN", G, P.math_n(N, L, "MULTIPLY", grow, 1.1))), 0.35)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(halo, c1.inputs["Factor"])
    L.new(col_out_socket_src, c1.inputs[6]); c1.inputs[7].default_value = (0.6, 0.16, 0.13, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(line, c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.62, 0.04, 0.035, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"])
    return line

bodym = RM["Body"].data.materials[0]
N = bodym.node_tree.nodes; L = bodym.node_tree.links
bb = next(n for n in N if n.type == "BSDF_PRINCIPLED")
src = bb.inputs["Base Color"].links[0].from_socket if bb.inputs["Base Color"].links else None
if src is None:
    rgbn = N.new("ShaderNodeRGB"); rgbn.outputs[0].default_value = bb.inputs["Base Color"].default_value; src = rgbn.outputs[0]
armE2 = child_of_bone("remy_arm2", remy, "RightForeArm" if ARM == "LeftForeArm" else "LeftForeArm")
acc = []
for ae in (armE, armE2):
    tcb = N.new("ShaderNodeTexCoord"); tcb.object = ae
    I_, G_, H_, sepb = lich_nodes(bodym, tcb.outputs["Object"], 0.22, offset=(0.0, 0.55), img=lich_arm_img)
    inbox = P.math_n(N, L, "LESS_THAN", P.math_n(N, L, "ABSOLUTE", sepb.outputs["Z"]), 0.09)
    inbox = P.math_n(N, L, "MULTIPLY", inbox, P.math_n(N, L, "LESS_THAN", P.math_n(N, L, "ABSOLUTE", sepb.outputs["X"]), 0.09))
    inbox = P.math_n(N, L, "MULTIPLY", inbox, P.math_n(N, L, "GREATER_THAN", sepb.outputs["Y"], 0.03))
    acc.append((P.math_n(N, L, "MULTIPLY", I_, inbox), P.math_n(N, L, "MULTIPLY", H_, inbox), G_, inbox))
I_ = P.math_n(N, L, "MAXIMUM", acc[0][0], acc[1][0]); H_ = P.math_n(N, L, "MAXIMUM", acc[0][1], acc[1][1])
G_ = P.math_n(N, L, "MINIMUM", P.math_n(N, L, "ADD", acc[0][2], P.math_n(N, L, "SUBTRACT", 1.0, acc[0][3])),
              P.math_n(N, L, "ADD", acc[1][2], P.math_n(N, L, "SUBTRACT", 1.0, acc[1][3])))
lg = value_node(bodym, "lich", 0.0)
lich_mix(bodym, I_, G_, H_, lg, src, bb)
for f, v in ((1, 0.0), (S["arm"][0], 1.0), (S["wake"][1] + 1, 0.0)): val_key(bodym, "lich", f, v)
interp(bodym.node_tree, "CONSTANT")
# ho'l teri (yomg'ir)
bb.inputs["Coat Weight"].default_value = 0.35; bb.inputs["Coat Roughness"].default_value = 0.1

# ---- rentgen nusxa: shaffof Remy + boshdan oyoqqa yuradigan tok to'lqinlari ----
def xray_current(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.3, 0.7, 1.0, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 1.3), 0.012), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.7), 0.06, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    # tok: dunyo Z bo'ylab pastga yuradigan yorqin to'lqinlar (shovqin bilan buzilgan)
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 6
    L.new(geo.outputs["Position"], nz.inputs[0])
    tt = value_node(m, "tt", 0.0); cur = value_node(m, "cur", 0.0)
    ph = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", sep.outputs["Z"], 9.0), P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 4.0))
    wave = P.math_n(N, L, "SINE", P.math_n(N, L, "ADD", ph, tt))
    band = P.math_n(N, L, "POWER", P.math_n(N, L, "MAXIMUM", wave, 0.0), 14.0)
    vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = 9.0
    L.new(geo.outputs["Position"], vor.inputs[0])
    vein = P.math_n(N, L, "LESS_THAN", vor.outputs["Distance"], 0.03)
    e = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", band, 25.0), P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", vein, band), 60.0)), cur)
    em2 = N.new("ShaderNodeEmission"); em2.inputs["Color"].default_value = (0.65, 0.85, 1.0, 1); L.new(e, em2.inputs["Strength"])
    ad = N.new("ShaderNodeAddShader"); L.new(mx.outputs[0], ad.inputs[0]); L.new(em2.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs[0])
    return m
xray_m = xray_current("xray_remy")
V0, V1 = S["volt"]
val_key(xray_m, "tt", V0, 0.0); val_key(xray_m, "tt", V1, 95.0)
for f, v in ((1, 0.0), (V0, 1.0), (V1 + 1, 0.0)): val_key(xray_m, "cur", f, v)
for fc in mc._fcurves(xray_m.node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if "tt" in fc.data_path else "CONSTANT"
ghosts = []
for nm in ("Body", "Tops", "Bottoms", "Shoes", "Hair"):
    o = RM[nm]; gh = o.copy(); gh.name = o.name + "_xray"; sc.collection.objects.link(gh)
    for slot in gh.material_slots: slot.link = "OBJECT"; slot.material = xray_m
    ghosts.append(gh)
for gh in ghosts: vis(gh, rng(*XRAY), False)
for o in rmeshes: vis(o, rng(*[n for n in REMY if n not in XRAY]), False)
vis(rroot, rng(*REMY), False)

# ---- yurak (rentgen ko'krak) ----
def glow_mat(name, col, ecol, rough=0.4, sss=0.3, base_glow=0.0, coat=0.5):
    m = mat(name, col, rough, sss=sss, sss_scale=0.004, coat=coat)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*ecol, 1)
    g = value_node(m, "glow", base_glow); L.new(g, b.inputs["Emission Strength"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40.0; nz.inputs["Detail"].default_value = 8
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    return m
heart_m = glow_mat("heart", (0.5, 0.04, 0.05), (1.0, 0.12, 0.1), 0.3, sss=0.5, base_glow=2.5, coat=0.8)
heartE = empty("heartE", (0.018, -0.07, -0.05), chest)
heart = sphere("heart", 1.0, (0, 0, 0), heart_m, scale=(0.045, 0.038, 0.055), sub=4, parent=heartE)
heart.rotation_euler = (0, R(-25), R(20))
ht = bpy.data.textures.new("heart_t", "CLOUDS"); ht.noise_scale = 0.4
dm = heart.modifiers.new("d", "DISPLACE"); dm.texture = ht; dm.strength = 0.12; dm.texture_coords = "LOCAL"
for dx, dz, r in ((-0.022, 0.035, 0.022), (0.02, 0.038, 0.02)):
    sphere("atrium", r, (dx, -0.005, dz), heart_m, sub=3, parent=heartE)
P.tube("aorta", [(0.0, 0.0, 0.03), (0.0, 0.0, 0.075), (-0.025, 0.005, 0.095), (-0.04, 0.01, 0.07)], 0.011, heart_m, heartE)
P.tube("vcava", [(0.028, 0.005, 0.03), (0.03, 0.0, 0.1)], 0.009, mat("vcava", (0.15, 0.1, 0.5), 0.4, emit=1.5, ecol=(0.3, 0.3, 1.0)), heartE)
HE0, HE1 = S["heart"]
f = HE0 - 10
while f < STOP:
    key(heartE, f, scale=(1, 1, 1)); key(heartE, f + 3, scale=(1.18, 1.14, 1.12)); key(heartE, f + 6, scale=(0.95, 0.95, 0.97))
    f += 12
key(heartE, STOP + 6, scale=(1, 1, 1))
for f_, v in ((1, 2.5), (STOP, 2.5), (STOP + 2, 6.0), (STOP + 12, 0.15), (HE1, 0.15)): val_key(heart_m, "glow", f_, v)
vis(heartE, rng("heart"))

# ---- tok yoylari tana atrofida (urilish, yuz, rentgen) ----
ARC_BONES = [("Head", (0, 0.12, 0.05)), ("Spine2", (0.18, 0.0, 0.1)), ("Spine2", (-0.18, 0.05, 0.1)),
             ("LeftForeArm", (0, 0.1, 0.05)), ("RightForeArm", (0, 0.1, 0.05)), ("LeftLeg", (0, 0.2, 0.08)),
             ("RightLeg", (0, 0.2, 0.08)), ("Hips", (0.15, 0, 0.1)), ("Head", (-0.1, 0.05, 0.08))]
ra = random.Random(31)
ARC_RANGE = (HIT, S["volt"][1])
for i, (bn, off) in enumerate(ARC_BONES):
    e = child_of_bone(f"arc{i}", remy, bn, off)
    a = Vector((0, 0, 0)); b = Vector((ra.uniform(-1, 1), ra.uniform(-1, 1), ra.uniform(-1, 1))).normalized() * ra.uniform(0.15, 0.35)
    fl = []
    for f in range(ARC_RANGE[0] + 1, ARC_RANGE[1]):
        fl.append((f, ra.choice((0.0, 0.0, 0.0, 0.25, 0.6, 1.0))))
    bolt(f"arc{i}", a, b, 100 + i, 0.002, fl, grow=1, halo_r=8.0, parent=e, rough=0.22, levels=5, branches=2, depth=1)

# ---- krossovkalar uchib ketadi ----
sc.frame_set(SHOE)
dg = bpy.context.evaluated_depsgraph_get()
sh = RM["Shoes"]
me = bpy.data.meshes.new_from_object(sh.evaluated_get(dg)); me.transform(sh.matrix_world)
bm = bmesh.new(); bm.from_mesh(me)
cx = rroot.matrix_world.translation.x
SH_OBJ = []
for side in (1, -1):
    b2 = bm.copy()
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if (v.co.x - cx) * side < 0], context="VERTS")
    c = sum((v.co for v in b2.verts), Vector()) / max(1, len(b2.verts))
    for v in b2.verts: v.co -= c
    m2 = bpy.data.meshes.new(f"shoe{side}"); b2.to_mesh(m2); b2.free()
    for mt in sh.data.materials: m2.materials.append(mt)
    o = bpy.data.objects.new(f"shoe{side}", m2); sc.collection.objects.link(o); o.location = c
    for p_ in m2.polygons: p_.use_smooth = True
    SH_OBJ.append((o, c.copy(), side))
bm.free(); bpy.data.meshes.remove(me)
SH0, SH1 = S["shoes"]
for o, c, side in SH_OBJ:
    v = Vector((side * 0.9, -2.2 if side > 0 else -0.6, 3.6 if side > 0 else 4.4)); spin = Vector((side * 540, 260, side * 180))
    key(o, 1, loc=tuple(c), rot=(0, 0, 0))
    key(o, SHOE, loc=tuple(c), rot=(0, 0, 0))
    for k in range(1, SH1 - SHOE + 2):
        t = k / 24.0 * 0.45                                 # slow-mo (0.45x)
        p = c + v * t + Vector((0, 0, -4.9 * t * t)); key(o, SHOE + k, loc=tuple(p), rot=tuple(spin * t))
    vis(o, [(SHOE, SH1)], False)
vis(sh, rng(*[n for n in REMY if n not in XRAY and n != "shoes"]) + [(SH0, SHOE - 1)], False)
sc.frame_set(1)

# ---- bug' (Geometry Nodes: kiyimdan ko'tariladigan hajmli bulutchalar) ----
def steam_obj(name, sources, t0, density=260.0, life=1.4, rise=1.1):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    go = N.new("NodeGroupOutput"); N.new("NodeGroupInput")
    j = N.new("GeometryNodeJoinGeometry")
    for s_ in sources:
        oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = s_; oi.transform_space = "RELATIVE"
        L.new(oi.outputs["Geometry"], j.inputs[0])
    dist = N.new("GeometryNodeDistributePointsOnFaces"); dist.inputs["Density"].default_value = density
    L.new(j.outputs[0], dist.inputs["Mesh"])
    idx = N.new("GeometryNodeInputIndex")
    def M_(op, a, b=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    rv = N.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT"; L.new(idx.outputs[0], rv.inputs["ID"])
    r1 = [s for s in rv.outputs if s.type == "VALUE"][0]
    tm = N.new("GeometryNodeInputSceneTime")
    t = M_("SUBTRACT", tm.outputs["Seconds"], t0)
    age = M_("FRACT", M_("ADD", M_("DIVIDE", t, life), r1))
    on = M_("MINIMUM", M_("MAXIMUM", M_("MULTIPLY", t, 2.0), 0.0), 1.0)
    on = M_("MULTIPLY", on, M_("LESS_THAN", M_("ADD", M_("MULTIPLY", r1, life), 0.0), M_("MAXIMUM", t, 0.0)))
    nzv = N.new("ShaderNodeTexNoise"); nzv.inputs["Scale"].default_value = 1.5
    pos = N.new("GeometryNodeInputPosition"); L.new(pos.outputs[0], nzv.inputs["Vector"])
    cx_ = N.new("ShaderNodeSeparateXYZ"); L.new(nzv.outputs["Color"], cx_.inputs[0])
    off = N.new("ShaderNodeCombineXYZ")
    L.new(M_("MULTIPLY", M_("SUBTRACT", cx_.outputs[0], 0.5), M_("MULTIPLY", age, 0.8)), off.inputs[0])
    L.new(M_("MULTIPLY", M_("SUBTRACT", cx_.outputs[1], 0.5), M_("MULTIPLY", age, 0.8)), off.inputs[1])
    L.new(M_("MULTIPLY", age, rise), off.inputs[2])
    sp = N.new("GeometryNodeSetPosition"); L.new(dist.outputs["Points"], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
    ico = N.new("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = 1.0; ico.inputs["Subdivisions"].default_value = 2
    ins = N.new("GeometryNodeInstanceOnPoints"); L.new(sp.outputs[0], ins.inputs["Points"]); L.new(ico.outputs["Mesh"], ins.inputs["Instance"])
    scl = M_("MULTIPLY", M_("MULTIPLY", M_("ADD", 0.03, M_("MULTIPLY", age, 0.16)), M_("SINE", M_("MULTIPLY", age, math.pi))), on)
    L.new(scl, ins.inputs["Scale"])
    re = N.new("GeometryNodeRealizeInstances"); L.new(ins.outputs[0], re.inputs[0])
    sm = N.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = steam_m; L.new(re.outputs[0], sm.inputs["Geometry"])
    L.new(sm.outputs[0], go.inputs[0])
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.modifiers.new("gn", "NODES").node_group = ng
    return o
steam_m = bpy.data.materials.new("steam"); steam_m.use_nodes = True
N = steam_m.node_tree.nodes; L = steam_m.node_tree.links; N.remove(N["Principled BSDF"])
vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.85, 0.88, 0.92, 1)
vol.inputs["Anisotropy"].default_value = 0.35
tcs = N.new("ShaderNodeTexCoord"); mps = N.new("ShaderNodeMapping"); L.new(tcs.outputs["Object"], mps.inputs[0])
nzs = N.new("ShaderNodeTexNoise"); nzs.inputs["Scale"].default_value = 7.0; nzs.inputs["Detail"].default_value = 4
L.new(mps.outputs[0], nzs.inputs[0])
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", nzs.outputs["Fac"], 0.45, clamp=True), 2.5), vol.inputs["Density"])
L.new(vol.outputs[0], N["Material Output"].inputs["Volume"])
ST0 = S["steam"][0]
mps.inputs["Location"].default_value = (0, 0, 0); mps.inputs["Location"].keyframe_insert("default_value", frame=ST0)
mps.inputs["Location"].default_value = (0, 0, -2.5); mps.inputs["Location"].keyframe_insert("default_value", frame=S["shoes"][1])
interp(steam_m.node_tree, "LINEAR")
steam = steam_obj("steam", [RM["Tops"], RM["Bottoms"], RM["Body"]], (ST0 - 6) / 24.0)
vis(steam, rng("steam", "steam2", "shoes"))

# ======================================================================
# 3) DALADAGI CHAQMOQLAR
# ======================================================================
sc.frame_set(HIT); bpy.context.view_layer.update()
HEADW = headE.matrix_world.translation.copy() + Vector((0, 0, 0.08))
sc.frame_set(1)
fl = flicker(HIT, 9, seed=2); add_flash(fl)
bolt("strike", Vector((-6, 30, 75)), HEADW, 7, 0.07, fl, grow=4, branches=9)
# uzoq chaqmoqlar (fon): ilgak, daraxt, "Lichtenberg", bug', 10 kishi, daraxt tagida
for i, (f0, a, b, sd, sc_) in enumerate([
        (12, (40, 120, 90), (55, 125, 0), 3, 0.5), (412, (-30, 70, 80), (-22, 72, 0), 4, 0.9), (431, (25, 60, 80), (18, 58, 0), 5, 0.8),
        (540, (-60, 110, 90), (-45, 105, 0), 6, 0.5), (600, (50, 90, 90), (42, 95, 0), 8, 0.6), (975, (-20, 140, 90), (-25, 150, 0), 9, 0.6),
        (1075, (30, 110, 90), (40, 100, 0), 10, 0.6), (1100, (-50, 90, 90), (-40, 95, 0), 11, 0.5)]):
    fl = flicker(f0, 6, seed=40 + i, hi=0.8); add_flash(fl, sc_)
    bolt(f"far{i}", Vector(a), Vector(b), sd, 0.3, fl, grow=3, branches=6)
fl = flicker(TREEHIT, 10, seed=3); add_flash(fl)
bolt("treebolt", TREETOP + Vector((8, 25, 70)), TREETOP, 12, 0.04, fl, grow=4, branches=9)
fl = flicker(SHOE, 5, seed=4, hi=0.7); add_flash(fl, 0.7)

# ======================================================================
# 4) OSMON: plazma kanali (yaqindan) — SKY markazi
# ======================================================================
SKY = Vector((600.0, 0.0, 0.0))
PL0, PL1 = S["plasma"]
pl_fl = [(f, 1.0 if (f // 3) % 4 else 0.75) for f in range(PL0, PL1 + 1)]
pls, _ = bolt("plasma", SKY + Vector((0, 0, 160)), SKY + Vector((0, 0, -10)), 21, 0.18, pl_fl, grow=1, halo_r=9.0, branches=10, rough=0.09)
for o in pls:
    for m in o.data.materials:
        m.node_tree.nodes["Emission"].inputs["Color"].default_value = (1.0, 0.95, 0.9, 1) if "core" in m.name else (0.55, 0.65, 1.0, 1)
add_flash([(f, 0.6) for f in range(PL0, PL1 + 1)])

# ======================================================================
# 5) KOINOT: quyosh yuzasi + oldida chaqmoq — SPACE markazi
# ======================================================================
SPACE = Vector((5000.0, 0.0, 0.0))
SU0, SU1 = S["sun"]
sun_m = bpy.data.materials.new("sun_surf"); sun_m.use_nodes = True
N = sun_m.node_tree.nodes; L = sun_m.node_tree.links; N.remove(N["Principled BSDF"])
tc = N.new("ShaderNodeTexCoord")
vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 0.6; L.new(tc.outputs["Object"], vo.inputs[0])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.01; nz.inputs["Detail"].default_value = 10; L.new(tc.outputs["Object"], nz.inputs[0])
cr = N.new("ShaderNodeValToRGB"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", vo.outputs["Distance"], 0.8), P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.6)), cr.inputs[0])
cr.color_ramp.elements[0].color = (1.0, 0.55, 0.08, 1); cr.color_ramp.elements[1].color = (0.35, 0.04, 0.0, 1)
em = N.new("ShaderNodeEmission"); L.new(cr.outputs[0], em.inputs["Color"]); em.inputs["Strength"].default_value = 3.5
L.new(em.outputs[0], N["Material Output"].inputs[0])
sunball = sphere("sun_ball", 400.0, tuple(SPACE + Vector((0, 0, -420))), sun_m, sub=6)
prom_m = mat("prom", (1, 0.4, 0.1), emit=6.0, ecol=(1.0, 0.35, 0.05))
rp = random.Random(8)
for i in range(7):
    a_ = rp.uniform(-0.7, 0.7); b_ = rp.uniform(-0.25, 0.25)
    base = SPACE + Vector((0, 0, -420)) + Vector((math.sin(a_) * 400, 60 + rp.uniform(0, 80) + math.sin(b_) * 0, math.cos(a_) * 400))
    out_ = (base - (SPACE + Vector((0, 0, -420)))).normalized()
    pts = [base + Vector((-8, 0, 0)), base + out_ * 18 + Vector((-5, 0, 0)), base + out_ * 26, base + out_ * 18 + Vector((5, 0, 0)), base + Vector((8, 0, 0))]
    P.tube(f"prom{i}", [tuple(p) for p in pts], rp.uniform(1.0, 2.2), prom_m)
sfl = [(f, 1.0 if (f // 2) % 5 else 0.5) for f in range(SU0, SU1 + 1)]
sbolt, _ = bolt("spacebolt", SPACE + Vector((-6, -30, 22)), SPACE + Vector((4, -26, -8)), 33, 0.06, sfl, grow=1, halo_r=7.0, branches=7)
space_objs = [sunball] + [o for o in bpy.data.objects if o.name.startswith("prom")]
for o in space_objs: vis(o, rng("sun"), False)
sunT = empty("sunT", tuple(SPACE + Vector((0, 0, -20))))

# ======================================================================
# 6) TERI MAKROSI (bilak bo'lagi, real o'lcham) — SKN markazi
# ======================================================================
SKN = Vector((0.0, -600.0, 0.5))
skin = P.skin_material("skin_macro", base=(0.74, 0.5, 0.4), prints=False)
N = skin.node_tree.nodes; L = skin.node_tree.links; bsk = N["Principled BSDF"]
tcs = N.new("ShaderNodeTexCoord"); mrot = N.new("ShaderNodeMapping"); mrot.inputs["Rotation"].default_value = (0, 0, R(90))
L.new(tcs.outputs["Object"], mrot.inputs[0])
I_, G_, H_, _ = lich_nodes(skin, mrot.outputs[0], 0.26, offset=(0.45, 0.5))
src_col = bsk.inputs["Base Color"].links[0].from_socket
lg2 = value_node(skin, "lich", 0.0)
line = lich_mix(skin, I_, G_, H_, lg2, src_col, bsk)
# tok: naqsh bo'ylab yuguradigan ko'k-oq yorug'lik ('zap' old cheti, 'zglow' umumiy)
zap = value_node(skin, "zap", -1.0)
front = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "SUBTRACT", G_, zap)), 0.08), clamp=True)
behind = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "LESS_THAN", G_, zap), 0.25)
ze = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", I_, P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", front, 1.0), behind)), 60.0)
zf = value_node(skin, "zon", 0.0); ze = P.math_n(N, L, "MULTIPLY", ze, zf)
bsk.inputs["Emission Color"].default_value = (0.55, 0.75, 1.0, 1); L.new(ze, bsk.inputs["Emission Strength"])
CR0, CR1 = S["crawl"]; LI0, LI1 = S["lich"]
for f, v in ((1, -0.05), (CR0, -0.05), (CR1 - 4, 1.15), (LI0, 1.2)): val_key(skin, "zap", f, v)
for f, v in ((1, 0.0), (CR0, 1.0), (CR1 + 1, 0.0)): val_key(skin, "zon", f, v)
for f, v in ((1, 0.0), (LI0, 0.0), (LI1 - 6, 1.0)): val_key(skin, "lich", f, v)
for f, v in ((1, 0.0),): val_key(skin, "wet", f, 0.25)
for fc in mc._fcurves(skin.node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if "zap" in fc.data_path or "lich" in fc.data_path else "CONSTANT"
skinset = empty("skinset", tuple(SKN))
fa = cyl("forearm", 0.045, 0.6, (0, 0, 0), skin, rot=(0, 90, 0), parent=skinset, verts=96)
fa.scale = (1.0, 1.25, 1.0); fa.parent = None; fa.location = tuple(SKN)
bpy.ops.object.select_all(action="DESELECT"); fa.select_set(True); bpy.context.view_layer.objects.active = fa
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); fa.parent = skinset; fa.location = (0, 0, 0)
sub = fa.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 2
# tuklar (mayda), yomg'ir tomchilari
hair_m = mat("armhair", (0.08, 0.05, 0.03), 0.5)
rh = random.Random(3)
for i in range(260):
    x = rh.uniform(-0.28, 0.28); a_ = rh.uniform(-1.2, 1.2)
    p0 = Vector((x, math.sin(a_) * 0.045 * 1.25, math.cos(a_) * 0.045))
    d = Vector((rh.uniform(0.6, 1.0), rh.uniform(-0.3, 0.3), 0.25)).normalized()
    P.tube(f"ah{i}", [tuple(p0), tuple(p0 + d * 0.004 + Vector((0, 0, 0.0015))), tuple(p0 + d * 0.008 + Vector((0, 0, 0.0006)))], 0.00009, hair_m, skinset, res=4)
drop_m = mat("drop", (0.75, 0.88, 1.0), 0.0, trans=1.0, coat=1.0)
for d in P.drops_on(fa, 60, 0.0008, 0.002, drop_m, seed=4, region=lambda p: p.z > 0.01): pass
vis(skinset, rng(*SKIN))
skinT = empty("skinT", (0.0, 0.0, 0.045), skinset)

# ======================================================================
# 7) QULOQ KANALI KESIMI (x8 masshtab) — EAR markazi
# ======================================================================
EAR = Vector((0.0, -900.0, 0.5))
earset = empty("earset", tuple(EAR))
flesh = glow_mat("flesh", (0.72, 0.36, 0.3), (1.0, 0.4, 0.3), 0.45, sss=0.6, base_glow=0.0)
cutm = glow_mat("cutface", (0.62, 0.12, 0.1), (1.0, 0.2, 0.15), 0.5, sss=0.3, base_glow=0.15)
blk = box("earblock", (0.5, 0.36, 0.32), (0, 0, 0), flesh)
canal = cyl("canalcut", 0.045, 0.62, (0, 0, 0), None, rot=(0, 90, 0), verts=64)
half = box("halfcut", (0.6, 0.2, 0.4), (0, -0.1, 0), None)
cut(blk, [canal, half])
for c_ in (canal, half): bpy.data.objects.remove(c_, do_unlink=True)
blk.parent = earset
# ichki kanal yuzasi biroz yaltiroq: kesim yuzasiga alohida material (y = 0 tekisligi)
blk.data.materials.append(cutm)
for p_ in blk.data.polygons:
    if abs(p_.center.y) < 0.002 and abs(p_.normal.y + 1) < 0.01: p_.material_index = 1
# nog'ora parda: 8 bo'lak (ildizi chetida)
drum_m = mat("drum", (0.85, 0.75, 0.7), 0.3, sss=0.5, sss_scale=0.01, emit=0.3, ecol=(1.0, 0.8, 0.7))
drum_m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.85
DX = 0.2
DR0, DR1 = S["ear"]; RUP = DR0 + 26
petals = []
for k in range(8):
    a0, a1 = k * math.pi / 4, (k + 1) * math.pi / 4
    bm = bmesh.new()
    ctr = bm.verts.new((0, 0, 0)); ring = []
    for j in range(5):
        a = a0 + (a1 - a0) * j / 4
        ring.append(bm.verts.new((0, math.cos(a) * 0.044, math.sin(a) * 0.044)))
    for j in range(4): bm.faces.new((ctr, ring[j], ring[j + 1]))
    # ildiz (o'q) — tashqi chetning o'rtasida
    am = (a0 + a1) / 2; hinge = Vector((0, math.cos(am) * 0.044, math.sin(am) * 0.044))
    for v in bm.verts: v.co -= hinge
    me = bpy.data.meshes.new(f"petal{k}"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(f"petal{k}", me); sc.collection.objects.link(o); o.parent = earset; me.materials.append(drum_m)
    o.location = (DX, hinge.y, hinge.z)
    so = o.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.003
    tang = Vector((0, -math.sin(am), math.cos(am)))
    o.rotation_mode = "AXIS_ANGLE"
    def ak(f, ang): o.rotation_axis_angle = (R(ang), *tang); o.keyframe_insert("rotation_axis_angle", frame=f)
    ak(1, 0); ak(RUP - 8, 0); ak(RUP - 3, 7); ak(RUP, 9); ak(RUP + 3, 62 + 10 * (k % 3)); ak(RUP + 9, 78 + 6 * (k % 2))
    petals.append(o)
# eshitish suyakchalari (parda ortida)
bone_m = mat("ossicle", (0.9, 0.85, 0.75), 0.4, sss=0.2)
sphere("malleus", 0.012, (DX + 0.03, 0.0, 0.01), bone_m, scale=(1, 0.8, 2.0), parent=earset)
sphere("incus", 0.01, (DX + 0.055, 0.01, 0.025), bone_m, scale=(1.4, 0.8, 1.0), parent=earset)
P.tube("stapes", [(DX + 0.065, 0.01, 0.02), (DX + 0.09, 0.01, 0.0), (DX + 0.1, 0.01, -0.01)], 0.004, bone_m, earset)
# zarba to'lqini (halqa) va havo zarralari
wave_m = mat("wave", (0.6, 0.8, 1.0), emit=4.0, ecol=(0.6, 0.8, 1.0))
bpy.ops.mesh.primitive_torus_add(major_radius=0.04, minor_radius=0.004, rotation=(0, R(90), 0)); ring_o = bpy.context.object
ring_o.name = "shock"; ring_o.data.materials.append(wave_m); ring_o.parent = earset
for f, x in ((1, -0.4), (DR0 + 2, -0.4), (RUP - 2, DX - 0.01)): key(ring_o, f, loc=(x, 0, 0))
scale_vis(ring_o, DR0 + 2, RUP - 2)
for i in range(3):
    r2 = ring_o.copy(); sc.collection.objects.link(r2); r2.animation_data_clear(); r2.parent = earset
    for f, x in ((DR0 + 6 + i * 5, -0.4), (RUP + i * 2, DX - 0.01)): key(r2, f, loc=(x, 0, 0))
    scale_vis(r2, DR0 + 6 + i * 5, RUP + i * 2)
earT = empty("earT", (DX, 0, 0), earset)
vis(earset, rng("ear"))

# ======================================================================
# 8) 10 KISHI QATORDA ("o'ndan to'qqiztasi tirik qoladi") — LINE markazi (dalada)
# ======================================================================
LINE = Vector((0.0, 40.0, 0.0))
CREW = [("Brian", "Catwalk_Idle_01"), ("Kate", "Happy_Idle"), ("Bryce", "Breathing_Idle"), ("Sophie", "Bored"),
        ("David", "Catwalk_Idle_02"), ("Josh", None), ("Megan", "Breathing_Idle"), ("Leonard", "Catwalk_Idle_01"),
        ("Jody", "Happy_Idle"), ("Louise", "Bored")]
TE0, TE1 = S["ten"]
crew_roots = []
for i, (nm, an) in enumerate(CREW):
    r_, a_, ms_ = mc.load_character("c_" + nm, nm + ".fbx"); sc.render.fps = 24
    soften(ms_)
    x = (i - 4.5) * 0.95
    r_.location = tuple(LINE + Vector((x, 0.15 * math.cos(i * 1.7), 0)))
    r_.rotation_euler = (0, 0, R(random.uniform(-12, 12)))
    if an:
        mc.add_strip(a_, A_(an + ".fbx"), TE0 - 30 - i * 7, blend=0, repeat=4.0)
    else:
        mc.add_strip(a_, A_("Breathing_Idle.fbx"), TE0 - 40, blend=0, repeat=4.0)
        strip(a_, A_("Falling_Down.fbx"), FALL, blend=3, bout=0, hold=True)
    vis(r_, rng("ten"))
    crew_roots.append(r_)
lineT = empty("lineT", tuple(LINE + Vector((0, 0, 1.1))))

# ======================================================================
# 9) TUNGI SHAHAR VA MINORA — CITY markazi
# ======================================================================
CITY = Vector((0.0, 3000.0, 0.0))
city = empty("city", tuple(CITY))
win_m = bpy.data.materials.new("windows"); win_m.use_nodes = True
N = win_m.node_tree.nodes; L = win_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord")
geo = N.new("ShaderNodeNewGeometry"); sepw = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sepw.inputs[0])
u = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ADD", sepw.outputs["X"], sepw.outputs["Y"]), 3.2)
zz = P.math_n(N, L, "DIVIDE", sepw.outputs["Z"], 3.6)
wx = P.math_n(N, L, "LESS_THAN", P.math_n(N, L, "FRACT", u), 0.62); wz = P.math_n(N, L, "LESS_THAN", P.math_n(N, L, "FRACT", zz), 0.55)
cell = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "FLOOR", u), cell.inputs[0]); L.new(P.math_n(N, L, "FLOOR", zz), cell.inputs[1])
wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"; L.new(cell.outputs[0], wn.inputs["Vector"])
lit = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", wx, wz), P.math_n(N, L, "GREATER_THAN", wn.outputs["Value"], 0.55))
b.inputs["Base Color"].default_value = (0.03, 0.035, 0.045, 1); b.inputs["Roughness"].default_value = 0.25; b.inputs["Metallic"].default_value = 0.4
b.inputs["Emission Color"].default_value = (1.0, 0.75, 0.45, 1)
L.new(P.math_n(N, L, "MULTIPLY", lit, 6.0), b.inputs["Emission Strength"])
rc = random.Random(17)
for gx in range(-9, 10):
    for gy in range(-9, 10):
        if abs(gx) <= 1 and abs(gy) <= 1: continue
        h = rc.uniform(15, 90) * (1.6 if abs(gx) + abs(gy) < 6 else 1.0)
        w_ = rc.uniform(18, 30)
        box("bld", (w_, w_, h), (gx * 42 + rc.uniform(-5, 5), gy * 42 + rc.uniform(-5, 5), h / 2), win_m, parent=city)
plane("cground", (900, 900), (0, 0, 0), mat("cground", (0.02, 0.02, 0.025), 0.3, coat=0.6), parent=city)
TW_H = 330.0
box("tower", (40, 40, TW_H), (0, 0, TW_H / 2), win_m, parent=city)
box("tower2", (28, 28, 50), (0, 0, TW_H + 25), win_m, parent=city)
steel_m = mat("steel", (0.6, 0.62, 0.65), 0.3, metal=1.0)
cyl("spire", 1.2, 90, (0, 0, TW_H + 50 + 45), steel_m, parent=city, verts=16)
SPIRE = CITY + Vector((0, 0, TW_H + 140))
redl = mat("redlight", (1, 0.1, 0.05), emit=30.0)
sphere("beacon", 1.8, tuple(SPIRE - CITY), redl, parent=city)
vis(city, rng("city", "spire"))
for i, f0 in enumerate(TOWER):
    fl = flicker(f0, 8, seed=60 + i)
    add_flash(fl)
    bolt(f"tower{i}", SPIRE + Vector((rc.uniform(-200, 200), rc.uniform(80, 300), 900)), SPIRE, 70 + i, 0.6, fl, grow=4, halo_r=7.0, branches=10)

# ======================================================================
# 10) YOMG'IR (Geometry Nodes, har tomchi bir marta tushadi) — har sahna guruhiga alohida
# ======================================================================
def precip(name, region, count, speed, shape, m, t0, dur, seed=1):
    (x0, x1), (y0, y1), (z0, z1) = region
    Hc = (z1 - z0) + speed * dur
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    go = N.new("NodeGroupOutput"); N.new("NodeGroupInput")
    pts = N.new("GeometryNodePoints"); pts.inputs["Count"].default_value = count
    idx = N.new("GeometryNodeInputIndex")
    rv = N.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT_VECTOR"
    vin = [s for s in rv.inputs if s.type == "VECTOR"]
    vin[0].default_value = (x0, y0, 0.0); vin[1].default_value = (x1, y1, 1.0)
    L.new(idx.outputs[0], rv.inputs["ID"]); rv.inputs["Seed"].default_value = seed
    sep = N.new("ShaderNodeSeparateXYZ"); L.new([s for s in rv.outputs if s.type == "VECTOR"][0], sep.inputs[0])
    tm = N.new("GeometryNodeInputSceneTime")
    def M_(op, a, b):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    t = M_("SUBTRACT", tm.outputs["Seconds"], t0)
    z = M_("SUBTRACT", M_("ADD", z0, M_("MULTIPLY", sep.outputs["Z"], Hc)), M_("MULTIPLY", t, speed))
    x = M_("ADD", sep.outputs["X"], M_("MULTIPLY", t, 0.8))                        # shamol
    cb = N.new("ShaderNodeCombineXYZ"); L.new(x, cb.inputs[0]); L.new(sep.outputs["Y"], cb.inputs[1]); L.new(z, cb.inputs[2])
    L.new(cb.outputs[0], pts.inputs["Position"])
    shp = N.new("GeometryNodeMeshCylinder"); shp.inputs["Vertices"].default_value = 5
    shp.inputs["Radius"].default_value = shape[0]; shp.inputs["Depth"].default_value = shape[1]
    ins = N.new("GeometryNodeInstanceOnPoints"); L.new(pts.outputs[0], ins.inputs["Points"]); L.new(shp.outputs["Mesh"], ins.inputs["Instance"])
    ins.inputs["Rotation"].default_value = (0, R(5), 0)
    re = N.new("GeometryNodeRealizeInstances"); L.new(ins.outputs[0], re.inputs[0])
    smn = N.new("GeometryNodeSetMaterial"); smn.inputs["Material"].default_value = m; L.new(re.outputs[0], smn.inputs["Geometry"])
    L.new(smn.outputs[0], go.inputs[0])
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.modifiers.new("gn", "NODES").node_group = ng
    return o
rain_m = mat("rain", (0.9, 0.95, 1.0), 0.05, trans=0.6, emit=0.25, alpha=0.35, ecol=(0.75, 0.85, 1.0))
RAIN = [(("hook", "strike", "face"), ((-6, 6), (-8, 5), (0, 7)), 26000),
        (("tree",), ((TREE.x - 5, TREE.x + 7), (TREE.y - 9, TREE.y + 2), (0, 9)), 9000),
        (("arm", "steam", "steam2", "shoes"), ((-5, 5), (-6, 4), (0, 6)), 60000),
        (("wake",), ((-4, 4), (-5, 4), (0, 5)), 6000),
        (("ten",), ((LINE.x - 7, LINE.x + 7), (LINE.y - 7, LINE.y + 2), (0, 6)), 18000),
        (("under", "treehit"), ((UNDER.x - 7, UNDER.x + 9), (UNDER.y - 12, UNDER.y + 3), (0, 9)), 30000)]
for i, (names, reg, n) in enumerate(RAIN):
    a, b = S[names[0]][0], S[names[-1]][1]
    o = precip(f"rain{i}", reg, n, 9.0, (0.002, 0.16), rain_m, (a - 2) / 24.0, (b - a + 4) / 24.0, seed=3 + i)
    vis(o, rng(*names))
vis(field, rng(*FIELD, "ten"))

# ======================================================================
# 11) KAMERALAR
# ======================================================================
def V(*a): return Vector(a)
def W_(e, f):
    sc.frame_set(f); return e.matrix_world.translation.copy()
def tgt(name, keys):
    t = empty("T_" + name, (0, 0, 0))
    for f, p in keys: key(t, f, loc=tuple(p))
    return t
def cam_path(name, keys_pos, keys_tgt, lens, fstop=None, focus=None):
    T = tgt(name, keys_tgt)
    c = shot_cam(name, (0, 0, 0), T, lens if isinstance(lens, (int, float)) else lens[0][1], fstop, focus=focus or T)
    path_keys(c, [(f, tuple(p)) for f, p in keys_pos])
    if not isinstance(lens, (int, float)): lens_keys(c, lens)
    return c
FACEW = W_(faceT, 20)
# 1 ilgak
a, b = S["hook"]
c = cam_path("hook", [(a, V(0.9, -2.6, 0.16)), (b, V(0.45, -1.6, 0.4))], [(a, V(0, 0, 2.1)), (b, FACEW)], [(a, 15), (b, 19)], 4.0, focus=faceT)
# 2 urilish
a, b = S["strike"]
c = cam_path("strike", [(a, V(4.0, -7.0, 0.45)), (b, V(3.3, -6.0, 0.6))], [(a, V(-0.8, 6, 7.5)), (HIT, V(-0.5, 4, 5.5)), (HIT + 6, V(0, 0, 1.3)), (b, V(0, 0, 1.2))],
             [(a, 15), (HIT, 15), (HIT + 6, 32), (b, 36)])
shake(c, HIT, HIT + 22, 0.08, seed=2)
# 3 yuz: kamera boshga ergashadi
a, b = S["face"]
rig = empty("faceRig", (0, 0, 0)); cl = rig.constraints.new("COPY_LOCATION"); cl.target = faceT
c = camera("cam_face", (0, 0, 0), faceT, 55, 2.0, focus=faceT); CAMS["face"] = c; c.parent = rig
path_keys(c, ((a, (0.3, -0.6, -0.42)), (b, (0.15, -0.42, -0.3))))
shake(c, a, b, 0.012, seed=3, decay=False)
# 4 rentgen: aylanma
a, b = S["volt"]
T = tgt("volt", [(a, V(0, 0, 1.05)), (b, V(0, -0.2, 0.7))])
c = shot_cam("volt", (0, 0, 0), T, 22)
for f in range(a, b + 1, 6):
    u = (f - a) / (b - a); ang = R(-60 + 85 * u); r_ = 3.2 - 0.6 * u
    key(c, f, loc=(math.sin(ang) * r_, -math.cos(ang) * r_, 0.5 + 0.6 * u))
# 5 plazma
a, b = S["plasma"]
c = cam_path("plasma", [(a, SKY + V(3.5, -7, 145)), (b, SKY + V(2.0, -5, 70))], [(a, SKY + V(0, 0, 128)), (b, SKY + V(0, 0, 55))], [(a, 18), (b, 22)])
shake(c, a, b, 0.05, seed=5, decay=False)
# 6 quyosh
a, b = S["sun"]
c = cam_path("sun", [(a, SPACE + V(0, -60, 8)), (b, SPACE + V(10, -125, 34))], [(a, SPACE + V(0, -20, 0)), (b, SPACE + V(0, 0, -10))], [(a, 20), (b, 24)])
# 7 tok teri ustida
a, b = S["crawl"]
c = cam_path("crawl", [(a, SKN + V(-0.12, -0.11, 0.13)), (b, SKN + V(0.06, -0.09, 0.1))], [(a, SKN + V(-0.07, 0, 0.04)), (b, SKN + V(0.06, 0, 0.04))], 30, 9.0)
# 8 daraxt siluetti
a, b = S["tree"]
c = cam_path("tree", [(a, TREE + V(2.5, -3.2, 1.0)), (b, TREE + V(1.6, -2.4, 1.6))], [(a, TREE + V(-3, 2, 8)), (b, TREE + V(2, 1, 13))], 14)
# 9 qizil naqsh
a, b = S["lich"]
c = cam_path("lich", [(a, SKN + V(0.1, -0.13, 0.09)), (b, SKN + V(0.02, -0.08, 0.075))], [(a, SKN + V(-0.02, 0, 0.04)), (b, SKN + V(-0.05, 0, 0.04))], 38, 9.0)
# 10 bilakdagi naqsh: yaqindan orqaga
a, b = S["arm"]
ARMW = W_(armE, 545)
c = cam_path("arm", [(a, ARMW + V(0.14, -0.34, 0.1)), (540, ARMW + V(0.22, -0.46, 0.15)), (b, ARMW + V(1.6, -2.0, 0.35))],
             [(a, ARMW), (540, ARMW), (b, W_(chest, b))], [(a, 40), (540, 40), (b, 26)], 2.8)
# 11 bug' (pastdan)
a, b = S["steam"]
c = cam_path("steam", [(a, V(1.3, -2.5, 0.3)), (b, V(0.9, -2.0, 0.45))], [(a, V(0, 0, 1.3)), (b, V(0, 0, 1.2))], 20, 5.0)
# 12 bug' (ko'krak, crash zoom)
a, b = S["steam2"]
CH = W_(chest, a + 10)
c = cam_path("steam2", [(a, CH + V(0.45, -1.1, 0.0)), (b, CH + V(0.3, -0.8, 0.05))], [(a, CH), (b, CH + V(0, 0, 0.1))], [(a, 30), (a + 14, 30), (a + 19, 52), (b, 56)], 2.8)
shake(c, a + 14, a + 30, 0.02, seed=12)
# 13 krossovkalar
a, b = S["shoes"]
c = cam_path("shoes", [(a, V(0.3, -1.15, 0.07)), (SHOE, V(0.2, -0.85, 0.08)), (b, V(0.1, -1.3, 0.25))],
             [(a, V(0, 0, 0.12)), (SHOE, V(0, 0, 0.14)), (SHOE + 14, V(0, -0.35, 0.6)), (b, V(0, -0.55, 0.9))], [(a, 18), (b, 18)])
shake(c, SHOE, SHOE + 18, 0.03, seed=13)
# 14 quloq
a, b = S["ear"]
c = cam_path("ear", [(a, EAR + V(-0.28, -0.55, 0.14)), (RUP, EAR + V(0.02, -0.4, 0.07)), (b, EAR + V(0.08, -0.36, 0.05))],
             [(a, EAR + V(-0.1, 0, 0)), (RUP, EAR + V(DX, 0, 0)), (b, EAR + V(DX, 0, 0))], 30, 8.0)
shake(c, RUP, RUP + 14, 0.012, seed=14)
# 15 yurak
a, b = S["heart"]
HW = W_(heartE, a + 20)
c = cam_path("heart", [(a, HW + V(0.7, -1.8, 0.0)), (b, HW + V(0.2, -0.65, 0.05))], [(a, HW), (b, HW)], [(a, 30), (b, 45)], 2.8, focus=heartE)
# 16 uyg'onish (yotgan joyidan)
a, b = S["wake"]
HD = W_(headE, a + 2); HP = W_(hipsE, a + 2)
c = cam_path("wake", [(a, HD + V(0.55, -0.85, 0.12)), (b, HD + V(0.75, -1.1, 0.35))], [(a, HD), (b, W_(headE, b))], 24, 3.5, focus=headE)
# 17 10 kishi
a, b = S["ten"]
c = cam_path("ten", [(a, LINE + V(-3.0, -9.5, 0.5)), (b, LINE + V(2.5, -8.8, 0.8))], [(a, LINE + V(-1.0, 0, 1.1)), (b, LINE + V(1.0, 0, 1.1))], 15)
# 18 daraxt tagida (kran)
a, b = S["under"]
c = cam_path("under", [(a, UNDER + V(2.0, -6.0, 0.35)), (b, UNDER + V(3.0, -8.5, 5.0))], [(a, UNDER + V(0, 0, 1.2)), (b, TREE + V(0, 0, 8))], 16)
# 19 daraxtga zarba
a, b = S["treehit"]
c = cam_path("treehit", [(a, UNDER + V(4.5, -8.5, 0.6)), (b, UNDER + V(5.5, -10.5, 0.9))], [(a, TREE + V(0, 0, 6)), (TREEHIT, TREE + V(0, 0, 6)), (b, TREE + V(0, -2, 3))],
             [(a, 16), (TREEHIT, 16), (TREEHIT + 5, 22), (b, 20)])
shake(c, TREEHIT, TREEHIT + 26, 0.12, seed=19)
# 20 shahar
a, b = S["city"]
c = cam_path("city", [(a, CITY + V(-300, -720, 50)), (b, CITY + V(-230, -620, 80))], [(a, SPIRE - V(0, 0, 160)), (b, SPIRE - V(0, 0, 110))], 30)
for f0 in TOWER[:3]: shake(c, f0, f0 + 10, 1.2, seed=f0)
# 21 minora uchi
a, b = S["spire"]
c = cam_path("spire", [(a, CITY + V(-70, -230, TW_H * 0.55)), (b, CITY + V(-60, -200, TW_H * 0.62))], [(a, SPIRE - V(0, 0, 40)), (b, SPIRE)],
             [(a, 24), (TOWER[3], 30), (TOWER[3] + 5, 75), (b, 80)])
shake(c, TOWER[3], TOWER[3] + 16, 1.0, seed=21)
sc.frame_set(1)
for f, n in SHOTS:
    mk = sc.timeline_markers.new(n, frame=f); mk.camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 12) OSMON (world) VA YORUG'LIK
# ======================================================================
OUTDOOR = FIELD + ["ten", "plasma", "city", "spire"]
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(200)); L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs["Factor"].default_value = 1.0
L.new(env.outputs[0], tint.inputs[6]); tint.inputs[7].default_value = (0.5, 0.58, 0.75, 1)
sat = N.new("ShaderNodeHueSaturation"); sat.inputs["Saturation"].default_value = 0.25; L.new(tint.outputs[2], sat.inputs["Color"])
# bulutlarni qalinlashtirish: yorqinlikni kontrast qilish
gam = N.new("ShaderNodeGamma"); gam.inputs["Gamma"].default_value = 1.6; L.new(sat.outputs[0], gam.inputs["Color"])
bg_sky = N.new("ShaderNodeBackground"); L.new(gam.outputs[0], bg_sky.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.003, 0.006, 0.014, 1)
# yulduzlar (koinot)
vw = N.new("ShaderNodeTexVoronoi"); vw.inputs["Scale"].default_value = 260.0; L.new(tcw.outputs["Generated"], vw.inputs[0])
star = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "MULTIPLY", vw.outputs["Distance"], 9.0), clamp=True), 6.0)
bg_st = N.new("ShaderNodeBackground"); L.new(star, bg_st.inputs[1]); bg_st.inputs[0].default_value = (0.9, 0.95, 1.0, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_sky.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1])
a2 = N.new("ShaderNodeAddShader"); L.new(a1.outputs[0], a2.inputs[0]); L.new(bg_st.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], out.inputs["Surface"])
SKY_BASE = {n: 0.03 for n in FIELD}; SKY_BASE.update({"ten": 0.025, "plasma": 0.06, "city": 0.03, "spire": 0.03})
FLASH_GAIN = {"plasma": 0.6, "city": 1.2, "spire": 1.4}
DK = {"volt": 1.0, "heart": 1.0, "crawl": 4.0, "lich": 4.0, "ear": 3.0}
shot_at = {}
for f, n in SHOTS:
    for k in range(S[n][0], S[n][1] + 1): shot_at[k] = n
prev = None
for f in range(1, END + 1):
    n = shot_at[f]
    sky = SKY_BASE.get(n, 0.0) + (FLASH.get(f, 0.0) * FLASH_GAIN.get(n, 0.55) if n in OUTDOOR else 0.0)
    st = (DK.get(n, 0.0), 1.0 if n == "sun" else 0.0, sky)
    if st != prev:
        bg_dk.inputs[1].default_value = st[0]; bg_dk.inputs[1].keyframe_insert("default_value", frame=f)
        bg_st.inputs[1].links and None
        bg_sky.inputs[1].default_value = st[2]; bg_sky.inputs[1].keyframe_insert("default_value", frame=f)
        prev = st
interp(w.node_tree, "CONSTANT")
# yulduzlar faqat 'sun' kadrida: stars kuchi = star * qiymat
sv = N.new("ShaderNodeValue"); sv.name = "stars"
L.new(P.math_n(N, L, "MULTIPLY", star, sv.outputs[0]), bg_st.inputs[1])
for f, n in SHOTS: P.mat_value(w, "stars", f, 0.6 if n == "sun" else 0.0) if False else None
sv.outputs[0].default_value = 0.0; sv.outputs[0].keyframe_insert("default_value", frame=1)
sv.outputs[0].default_value = 0.6; sv.outputs[0].keyframe_insert("default_value", frame=S["sun"][0])
sv.outputs[0].default_value = 0.0; sv.outputs[0].keyframe_insert("default_value", frame=S["sun"][1] + 1)
interp(w.node_tree, "CONSTANT")

# oy/bulut yorug'ligi (sovuq) + chaqnashlar
moon = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN")); sc.collection.objects.link(moon)
moon.data.angle = R(8); moon.data.color = (0.62, 0.72, 1.0); moon.rotation_euler = (R(35), 0, R(160))
prev = None
for f in range(1, END + 1):
    n = shot_at[f]
    e = (0.18 + FLASH.get(f, 0.0) * 2.5) if n in FIELD + ["ten"] else 0.0
    if e != prev: moon.data.energy = e; moon.data.keyframe_insert("energy", frame=f); prev = e
interp(moon.data, "CONSTANT")
FIELD_REMY = [n for n in REMY if n in FIELD]
area("rim", (0.5, 3.0, 3.2), 2.0, (0.6, 0.72, 1.0), lights_for(rng(*[n for n in FIELD_REMY if n not in ("under", "treehit")]), 260.0), target=hipsE)
area("face_fill", (1.6, -2.2, 2.0), 1.0, (1.0, 0.85, 0.7), lights_for(rng(*[n for n in FIELD_REMY if n not in ("under", "treehit")]), 22.0), target=faceT)
area("tree_rim", tuple(UNDER + V(-1.5, 3.5, 4.0)), 3.0, (0.6, 0.72, 1.0), lights_for(rng("under", "treehit"), 500.0), target=hipsE)
area("tree_fill", tuple(UNDER + V(3.0, -5.0, 3.0)), 3.0, (0.8, 0.85, 1.0), lights_for(rng("under", "treehit", "tree"), 120.0), target=hipsE)
# urilish nuri (bosh ustida)
sk = point("strike_light", tuple(HEADW + V(0, -0.3, 0.6)), 0.1, (0.7, 0.82, 1.0), [(1, 0)])
for f, v in flicker(HIT, 9, seed=2): sk.data.energy = v * 9000; sk.data.keyframe_insert("energy", frame=f)
sk.data.energy = 0; sk.data.keyframe_insert("energy", frame=HIT + 9)
# yuz kadri: ko'k miltillash
rf = random.Random(9)
fk = point("face_zap", (0, 0, 0), 0.05, (0.55, 0.75, 1.0), [(1, 0)]); fk.parent = rig; fk.location = (-0.25, -0.3, 0.15)
for f in range(S["face"][0], S["face"][1] + 1): fk.data.energy = rf.choice((0, 5, 20, 60, 120)); fk.data.keyframe_insert("energy", frame=f)
fk.data.energy = 0; fk.data.keyframe_insert("energy", frame=S["face"][1] + 1)
# daraxt: zarba va keyin olov nuri
tl = point("tree_light", tuple(TREE + V(0.4, -0.6, 7.0)), 0.3, (1.0, 0.85, 0.6), [(1, 0)])
for f, v in flicker(TREEHIT, 10, seed=3): tl.data.energy = v * 60000; tl.data.keyframe_insert("energy", frame=f)
for f in range(TREEHIT + 10, TH1 + 1, 2): tl.data.energy = 2500 + 1800 * rf.random(); tl.data.color = (1.0, 0.5, 0.18); tl.data.keyframe_insert("energy", frame=f)
tl.data.energy = 0; tl.data.keyframe_insert("energy", frame=TH1 + 1)
tl.data.color = (1.0, 0.6, 0.25)
interp(tl.data, "CONSTANT")
# krossovka chaqnashi
shl = point("shoe_flash", (0.0, -0.35, 0.25), 0.05, (0.7, 0.82, 1.0), [(1, 0), (SHOE, 600), (SHOE + 2, 150), (SHOE + 4, 40), (SHOE + 8, 0)])
# rentgen: sovuq to'ldiruvchi
area("x_fill", (2.0, -2.5, 2.5), 2.0, (0.5, 0.7, 1.0), lights_for(rng(*XRAY), 60.0), target=hipsE)
# teri makrosi
skw = Vector(SKN)
area("s_key", tuple(skw + V(-0.2, -0.25, 0.35)), 0.25, (1.0, 0.88, 0.75), lights_for(rng(*SKIN), 10.0), target=skinT)
area("s_rim", tuple(skw + V(0.3, 0.3, 0.2)), 0.2, (0.5, 0.65, 1.0), lights_for(rng(*SKIN), 14.0), target=skinT)
zl = point("s_zap", tuple(skw + V(0.0, -0.06, 0.09)), 0.02, (0.55, 0.75, 1.0), [(1, 0)])
for f in range(CR0, CR1 + 1): zl.data.energy = rf.choice((0.5, 1.5, 3.0)); zl.data.keyframe_insert("energy", frame=f)
zl.data.energy = 0; zl.data.keyframe_insert("energy", frame=CR1 + 1)
# quloq studiyasi
ew = Vector(EAR)
area("e_key", tuple(ew + V(-0.7, -0.9, 0.7)), 0.6, (1.0, 0.9, 0.8), lights_for(rng("ear"), 40.0), target=earT)
area("e_rim", tuple(ew + V(0.6, 0.4, 0.6)), 0.5, (0.4, 0.6, 1.0), lights_for(rng("ear"), 50.0), target=earT)
point("e_flash", tuple(ew + V(DX - 0.05, -0.08, 0.0)), 0.02, (0.7, 0.85, 1.0), [(1, 0), (RUP, 30), (RUP + 2, 8), (RUP + 5, 0)])
# 10 kishi: har biriga tepadan nur (9 tasi yonadi, 10-chisi qorong'ida)
for i, r_ in enumerate(crew_roots):
    sp_ = bpy.data.objects.new(f"spot{i}", bpy.data.lights.new(f"spot{i}", "SPOT")); sc.collection.objects.link(sp_)
    sp_.data.spot_size = R(32); sp_.data.spot_blend = 0.6; sp_.data.shadow_soft_size = 0.2; sp_.data.color = (1.0, 0.93, 0.8)
    sp_.location = tuple(Vector(r_.location) + V(0, -0.6, 4.0)); sp_.rotation_euler = (R(-8), 0, 0)
    on = (TE0 + 50 + [0, 3, 6, 9, 12, 15, 0, 18, 21, 24][i]) if CREW[i][1] else None
    keys = [(1, 0)] + ([(on, 900.0), (TE1 + 1, 0)] if on else [])
    for f, e in keys: sp_.data.energy = e; sp_.data.keyframe_insert("energy", frame=f)
    interp(sp_.data, "CONSTANT")
area("ten_fill", tuple(LINE + V(0, -6, 3)), 4.0, (0.55, 0.65, 1.0), lights_for(rng("ten"), 120.0), target=lineT)
# shahar: past yorug'lik
area("city_glow", tuple(CITY + V(0, -200, 30)), 200.0, (1.0, 0.6, 0.35), lights_for(rng("city", "spire"), 2.0e6), target=None)
for i, f0 in enumerate(TOWER):
    pl = point(f"tower_light{i}", tuple(SPIRE + V(0, -60, 40)), 5.0, (0.7, 0.8, 1.0), [(1, 0)])
    for f, v in flicker(f0, 8, seed=60 + i): pl.data.energy = v * 4.0e7; pl.data.keyframe_insert("energy", frame=f)
    pl.data.energy = 0; pl.data.keyframe_insert("energy", frame=f0 + 8)

# ======================================================================
# 13) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 12; sc.cycles.transmission_bounces = 4
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0; sc.cycles.volume_max_steps = 96
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 45))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
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
