# Aql tishlari — Zack D. Films uslubida 39.5 s video (948 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py (+ burish/burish.py yordamchilari); procedural tishlar: aql/teeth.py
# Assetlar: zack_test/tools/get_aql.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/aql/aql.py --render
# Sinov: FRAMES=20,100,200,400,560 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import teeth as T
sc = bpy.context.scene
sc.render.fps = 24
END = 948
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper vaqtlari) ----------------
SHOTS = [(1, "hook"), (51, "skull_wide"), (82, "skull_macro"), (113, "row"), (171, "sideways"), (232, "laugh"),
         (283, "xray_in"), (338, "dozer"), (366, "pressure"), (421, "melt"), (484, "mouth"), (531, "flap"),
         (592, "crumbs"), (641, "brush"), (695, "cyst"), (761, "erode"), (832, "eat_wide"), (863, "eat_close"), (894, "crack")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

def _par(o, parent):
    o.parent = parent
    bpy.context.view_layer.update(); o.matrix_parent_inverse = parent.matrix_world.inverted()

# ---------------- yordamchilar (burish.py dan) ----------------
# ---------------- yordamchilar ----------------
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
    for x in objs:                                   # oldingi ko'rinish kalitlarini tozalash (qayta chaqirish mumkin)
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def pbr(name, folder, scale=1.0, tint=None, proj="BOX", rough_mul=None):
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
    r = img("rough.jpg", True)
    if rough_mul is not None:
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        L.new(r.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], b.inputs["Roughness"])
    else:
        L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

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

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 300
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
    sc.frame_set(f0); base = cam.location.copy()
    for f in range(f0, f1):
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)
    cam.location = base; cam.keyframe_insert("location", frame=f1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None, shape=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)

sys.path.insert(0, os.path.join(os.path.dirname(HERE), "burish"))
import parts as P
P.VIEWPORT_OFF = True
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c

def fade_material(name, col, strength=8.0):
    """Faqat yorug'lik chiqaradigan, 'glow' qiymati 0 bo'lsa butunlay shaffof material (to'lqin halqalari, chaqnash)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    val = N.new("ShaderNodeValue"); val.name = "glow"; val.outputs[0].default_value = 0.0
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = strength
    L.new(val.outputs[0], mul.inputs[0]); L.new(mul.outputs[0], em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    cl = N.new("ShaderNodeMath"); cl.operation = "MINIMUM"; cl.inputs[1].default_value = 1.0; L.new(val.outputs[0], cl.inputs[0])
    L.new(cl.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m

SEC_SHOTS = rng("row", "sideways", "dozer", "pressure", "melt", "cyst", "erode")
MOUTH = rng("mouth", "flap", "crumbs", "brush")
CUT_ON = [(1, S["melt"][1]), (S["cyst"][0], END)]

# ======================================================================
# 1) JAG' KESIMI + OG'IZ ICHI (dunyo markazi, 10x masshtab: tish toji ~0.1 m)
# ======================================================================
enamel = T.enamel_material()
dentin = T.plain("dentin", (0.94, 0.82, 0.56), 0.5, sss=0.2, sss_scale=0.003, noise=0.18, nscale=90)
pulp_m = T.plain("pulp", (0.7, 0.07, 0.06), 0.35, sss=0.5, sss_scale=0.004, coat=0.4)
gum_m = T.plain("gum", (0.66, 0.2, 0.22), 0.3, sss=0.6, sss_scale=0.008, coat=0.9, noise=0.3, nscale=60)
bone_m = T.bone_material()
cut_out = T.cutter("cut_out", -0.0012); cut_den = T.cutter("cut_den", -0.0022); cut_pulp = T.cutter("cut_pulp", -0.0032)
cut_bone = T.cutter("cut_bone", 0.0); cut_gum = T.cutter("cut_gum", -0.0005); cut_cyst = T.cutter("cut_cyst", -0.0008)
sec = T.empty("sec", (0, 0, 0))

TEETH = {}
def make_tooth(name, x, z=0.0, roty=0.0, w=0.1, roots=2, seed=0, premolar=False):
    root = T.empty(name, (x, 0, z), sec); root.rotation_euler = (0, R(roty), 0)
    parts = T.tooth_shapes(name, w=w, roots=roots, seed=seed, premolar=premolar)
    for ob, m, c in zip(parts, (enamel, dentin, pulp_m), (cut_out, cut_den, cut_pulp)):
        ob.data.materials.append(m); ob.parent = root
        T.key_show(T.bool_diff(ob, c), CUT_ON, END)
    TEETH[name] = (root,) + tuple(parts)
    return root

make_tooth("P2", -0.5, w=0.085, roots=1, seed=1, premolar=True)
make_tooth("M1", -0.385, seed=2)
make_tooth("M2", -0.27, seed=3)
m3 = make_tooth("M3", -0.135, z=-0.115, roty=-70, seed=4)

# milk (gum): qirralari yumaloq, yuzasi notekis
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.25, 0, -0.024)); gum = bpy.context.object; gum.name = "gum"
gum.scale = (0.74, 0.25, 0.064); bpy.ops.object.transform_apply(scale=True)
b_ = gum.modifiers.new("bev", "BEVEL"); b_.width = 0.025; b_.segments = 5
s_ = gum.modifiers.new("sub", "SUBSURF"); s_.levels = s_.render_levels = 2
tx = bpy.data.textures.new("gum_n", "CLOUDS"); tx.noise_scale = 0.05
d_ = gum.modifiers.new("disp", "DISPLACE"); d_.texture = tx; d_.strength = 0.006; d_.texture_coords = "GLOBAL"
T.key_show(T.bool_diff(gum, cut_gum), CUT_ON, END)
gum.data.materials.append(gum_m); gum.parent = sec
for p in gum.data.polygons: p.use_smooth = True

# jag' suyagi: tana + orqada ko'tarilgan shox (ramus)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.25, 0, -0.17)); b1 = bpy.context.object; b1.scale = (0.76, 0.26, 0.31)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.2, 0, 0.0), rotation=(0, R(14), 0)); b2 = bpy.context.object; b2.scale = (0.2, 0.24, 0.62)
bone = T.remesh(T._join([b1, b2], "jaw_bone"), 0.006, 6)
bv = bone.modifiers.new("disp", "DISPLACE"); bv.texture = tx; bv.strength = 0.004; bv.texture_coords = "GLOBAL"
T.key_show(T.bool_diff(bone, cut_bone), CUT_ON, END)
bone.data.materials.append(bone_m); bone.parent = sec

# --- M3 harakati: yonboshlab yotadi -> titraydi -> buldozerdek suradi -> (og'iz ichi) yarim chiqqan ---
def m3_key(f, x, z, ry, jit=0.0, seed=0):
    rnd = random.Random(seed * 1000 + f)
    key(m3, f, loc=(x + rnd.uniform(-jit, jit), 0, z + rnd.uniform(-jit, jit)), rot=(0, ry + rnd.uniform(-jit, jit) * 300, 0))
m3_key(1, -0.132, -0.115, -70)
m3_key(S["sideways"][0] + 20, -0.132, -0.115, -70)
for f in range(S["sideways"][0] + 22, S["sideways"][1] + 1, 2):
    t = (f - S["sideways"][0] - 22) / (S["sideways"][1] - S["sideways"][0] - 22)
    m3_key(f, -0.132 - 0.008 * t, -0.115, -70, jit=0.0012 * (0.3 + t), seed=1)
DZ0, DZ1 = S["dozer"]
m3_key(DZ0, -0.141, -0.115, -70)
for f in range(DZ0 + 2, DZ1 + 1, 2):
    t = min(1.0, (f - DZ0) / 14)
    m3_key(f, -0.141 - 0.012 * ease(t), -0.115, -70 - 2 * ease(t), jit=0.0025, seed=2)
PR0, PR1 = S["pressure"]; ML0, ML1 = S["melt"]
for f in range(PR0, ML1 + 1, 3):
    t = (f - PR0) / (ML1 - PR0)
    m3_key(f, -0.153 - 0.016 * t, -0.115, -72, jit=0.0008, seed=3)
MO0 = S["mouth"][0]
m3_key(MO0, -0.13, -0.018, -35)
interp(m3, "CONSTANT")
for fc in fcurves(m3):                               # titrashlar orasida chiziqli
    for k in fc.keyframe_points:
        if PR0 <= k.co[0] < ML1 or S["sideways"][0] + 20 <= k.co[0] < S["sideways"][1] or DZ0 <= k.co[0] < DZ1:
            k.interpolation = "LINEAR"

# --- M2 ildizi yemiriladi (rezorbsiya) ---
RES_C = Vector((-0.236, 0.0, -0.085))
resorb = T.jagged_sphere("resorb", 0.04, tuple(RES_C), seed=3, amt=0.3); resorb.hide_render = True; resorb.display_type = "WIRE"
key(resorb, 1, scale=(0.05, 0.05, 0.05)); key(resorb, PR0 + 20, scale=(0.08, 0.15, 0.08))
key(resorb, ML0, scale=(0.3, 0.6, 0.35)); key(resorb, ML1, scale=(0.85, 1.0, 1.0))
for ob in TEETH["M2"][1:]:
    T.key_show(T.bool_diff(ob, resorb, "res"), [(PR0, S["melt"][1]), (S["cyst"][0], END)], END)

# bosim to'lqinlari (qizil halqalar) va yemirilish nuqtasi
CONTACT = Vector((-0.222, -0.012, -0.088))
rings = []
for i in range(4):
    rm = fade_material(f"ring_m{i}", (1.0, 0.08, 0.03), 10.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.0022, location=tuple(CONTACT), rotation=(R(90), 0, 0))
    ring = bpy.context.object; ring.name = f"ring{i}"; ring.data.materials.append(rm); rings.append(ring)
    for k in range(5):
        f0 = PR0 + 4 + i * 4 + k * 16
        if f0 > ML1: break
        key(ring, f0, scale=(0.3, 0.3, 0.3)); key(ring, f0 + 14, scale=(2.4, 2.4, 2.4))
        P.mat_value(rm, "glow", f0 - 1, 0.0); P.mat_value(rm, "glow", f0, 1.0); P.mat_value(rm, "glow", f0 + 14, 0.0)
    vis(ring, [(PR0, ML1)])
glow_ball_m = fade_material("hot_m", (1.0, 0.15, 0.03), 6.0)
hot = sphere("hot", 0.02, tuple(CONTACT + Vector((-0.01, 0.0, 0))), glow_ball_m, scale=(1, 0.2, 1.2))
P.mat_value(glow_ball_m, "glow", 1, 0.0); P.mat_value(glow_ball_m, "glow", PR0, 0.2)
for f in range(PR0 + 4, ML1, 8):
    P.mat_value(glow_ball_m, "glow", f, 0.8); P.mat_value(glow_ball_m, "glow", f + 4, 0.3)
vis(hot, [(PR0, ML1)])

# suyak/ildiz ushoqlari (buldozer va yemirilish)
chip_m = T.plain("chip", (0.88, 0.8, 0.62), 0.6)
rc = random.Random(11)
for i in range(34):
    ch = T.crumb(f"chip{i}", rc.uniform(0.002, 0.0055), chip_m, 100 + i)
    if i < 20:
        f0, f1 = DZ0 + 4 + rc.randint(0, 8), DZ1 + 1
        v = Vector((rc.uniform(-0.25, 0.12), rc.uniform(-0.6, -0.2), rc.uniform(0.0, 0.5))) * 0.012
        g = 0.0007
    else:
        f0, f1 = ML0 + rc.randint(0, 40), ML1 + 1
        v = Vector((rc.uniform(-0.2, 0.1), rc.uniform(-0.25, -0.08), rc.uniform(-0.1, 0.25))) * 0.004
        g = 0.00005
    p0 = CONTACT + Vector((rc.uniform(-0.01, 0.01), rc.uniform(-0.004, 0), rc.uniform(-0.02, 0.02)))
    for f in range(f0, f1 + 1, 2):
        k = f - f0
        key(ch, f, loc=tuple(p0 + v * k + Vector((0, 0, -g * k * k))), rot=(k * 9 + i, k * 7, k * 5))
    vis(ch, [(f0, f1)])

# --- og'iz ichi: til, lunj, milk qopqog'i (operkulum), cho'ntak ---
tongue_m = T.plain("tongue", (0.6, 0.15, 0.17), 0.45, sss=0.6, sss_scale=0.01, coat=0.7, noise=0.5, nscale=220)
tongue = sphere("tongue", 1.0, (-0.32, 0.27, -0.02), tongue_m, scale=(0.5, 0.13, 0.075), sub=5)
cheek_m = T.plain("cheek", (0.62, 0.2, 0.23), 0.35, sss=0.6, sss_scale=0.01, coat=0.5, noise=0.4, nscale=40)
cheek = sphere("cheek", 1.0, (-0.3, -0.23, 0.02), cheek_m, scale=(0.65, 0.07, 0.2), sub=5)
for o_, st in ((tongue, 0.012), (cheek, 0.02)):
    dd = o_.modifiers.new("disp", "DISPLACE"); dd.texture = tx; dd.strength = st; dd.texture_coords = "GLOBAL"
for m_, bs in ((tongue_m, 0.6), (cheek_m, 0.35), (gum_m, 0.3)):
    bsdf_ = m_.node_tree.nodes["Principled BSDF"]; bsdf_.inputs["Coat Roughness"].default_value = 0.12
    for n_ in m_.node_tree.nodes:
        if n_.type == "BUMP": n_.inputs["Strength"].default_value = bs
pocket = sphere("pocket", 1.0, (-0.162, 0.0, 0.044), T.plain("pocket", (0.08, 0.005, 0.005), 0.5), scale=(0.028, 0.045, 0.012))
pocket.rotation_euler = (0, R(-35), 0)
hinge = T.empty("flap_hinge", (-0.118, 0, 0.064))
flap = sphere("flap", 1.0, (-0.15, 0, 0.06), gum_m, scale=(0.042, 0.058, 0.014), sub=4)
flap.rotation_euler = (0, R(-35), 0); _par(flap, hinge)
FL0, FL1 = S["flap"]; CR0, CR1 = S["crumbs"]; BR0, BR1 = S["brush"]
key(hinge, 1, rot=(0, 0, 0)); key(hinge, FL0 + 18, rot=(0, 0, 0)); key(hinge, FL0 + 34, rot=(0, -26, 0))
key(hinge, CR1 - 6, rot=(0, -24, 0)); key(hinge, CR1 + 2, rot=(0, -4, 0))
for o in (tongue, cheek, pocket, flap): vis(o, MOUTH)

# ovqat qoldiqlari: tepadan tushib, cho'ntakka kirib qoladi
food_ms = [T.plain("bread", (0.82, 0.58, 0.3), 0.7, noise=0.3, nscale=200), T.plain("meat", (0.36, 0.17, 0.08), 0.5, coat=0.3)]
rf = random.Random(21)
POCKET = Vector((-0.16, 0.0, 0.052))
for i in range(26):
    cb = T.crumb(f"food{i}", rf.uniform(0.005, 0.012), food_ms[i % 2], 300 + i)
    f0 = CR0 + rf.randint(0, 16); land = f0 + 12
    tgt = POCKET + Vector((rf.uniform(-0.03, 0.02), rf.uniform(-0.035, 0.035), rf.uniform(-0.004, 0.01)))
    if i % 4 == 3: tgt = Vector((-0.27 + rf.uniform(-0.03, 0.03), rf.uniform(-0.03, 0.03), 0.082))
    top = tgt + Vector((rf.uniform(-0.05, 0.05), rf.uniform(-0.04, 0.04), 0.3))
    for f in range(f0, land + 1):
        t = (f - f0) / (land - f0)
        key(cb, f, loc=tuple(top.lerp(tgt, t * t)), rot=(t * 400 + i * 30, t * 250, i * 40))
    if i % 4 != 3:      # cho'ntak ichiga sirpanib kiradi
        key(cb, land + 10, loc=tuple(tgt + Vector((0.012, 0, -0.012))))
    vis(cb, [(f0, BR1)])

# tish cho'tkasi (BlenderKit), 10x
# tish cho'tkasi (procedural, 10x): dasta -X tomonga (og'izdan tashqariga), tuklar pastga; boshining markazi = brushE
brushE = T.empty("brushE", (0, 0, 0))
plast = T.plain("brush_plastic", (0.05, 0.42, 0.75), 0.18, coat=0.8)
grip = T.plain("brush_grip", (0.9, 0.9, 0.92), 0.4)
br_parts = []
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.02, 0, 0.0)); o = bpy.context.object; o.scale = (0.3, 0.12, 0.035); br_parts.append(o)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.3, 0, 0.012), rotation=(0, R(-4), 0)); o = bpy.context.object; o.scale = (0.4, 0.05, 0.03); br_parts.append(o)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.0, 0, 0.06), rotation=(0, R(-5), 0)); o = bpy.context.object; o.scale = (1.1, 0.12, 0.06); br_parts.append(o)
bhead = T.remesh(T._join(br_parts, "brush_body"), 0.008, 4); bhead.data.materials.append(plast); bhead.parent = brushE
bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.05, 0, 0.1)); g_ = bpy.context.object; g_.scale = (0.6, 0.1, 0.03)
gr = T.remesh(T._join([g_], "brush_grip"), 0.008, 4); gr.data.materials.append(grip); gr.parent = brushE
tuft_w = T.plain("tuft_w", (0.95, 0.95, 0.97), 0.35, sss=0.3, sss_scale=0.003)
tuft_b = T.plain("tuft_b", (0.1, 0.55, 0.95), 0.35, sss=0.3, sss_scale=0.003)
for i in range(10):
    for j in range(4):
        x = -0.15 + i * 0.03; y = -0.042 + j * 0.028
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.0115, depth=0.1, location=(x, y, -0.065))
        tt = bpy.context.object; tt.name = f"tuft{i}_{j}"
        tt.data.materials.append(tuft_b if (i in (0, 1, 8, 9) or j in (0, 3)) and (i + j) % 2 == 0 else tuft_w)
        for p_ in tt.data.polygons: p_.use_smooth = True
        tt.parent = brushE
vis(brushE, rng("brush"))

# --- kista (yiringli) va suyak yemirilishi ---
CY0, CY1 = S["cyst"]; ER0, ER1 = S["erode"]
cystE = T.empty("cystE", (-0.1, 0, -0.07))
cyst_m = T.plain("cyst", (0.86, 0.74, 0.22), 0.25, sss=0.7, sss_scale=0.02, coat=0.9, noise=0.25, nscale=25)
cyst = sphere("cyst", 0.075, (0, 0, 0), cyst_m, sub=5); cyst.parent = cystE
cd_ = cyst.modifiers.new("disp", "DISPLACE"); cd_.texture = tx; cd_.strength = 0.012; cd_.texture_coords = "GLOBAL"
T.key_show(T.bool_diff(cyst, cut_cyst), [(1, END)], END)
hole = sphere("cyst_hole", 0.079, (0, 0, 0), cyst_m, sub=4); hole.parent = cystE; hole.hide_render = True; hole.display_type = "WIRE"
T.key_show(T.bool_diff(bone, hole, "hole", "EXACT"), [(CY0, END)], END)
key(cystE, 1, scale=(0.05, 0.05, 0.05)); key(cystE, CY0, scale=(0.12, 0.12, 0.12)); key(cystE, CY1, scale=(0.72, 0.72, 0.72))
key(cystE, ER1, scale=(1.0, 1.0, 1.0))
vis(cyst, [(CY0, ER1)], recursive=False)
# yoriqlar (kesim yuzasida), kistadan tashqariga
crk_m = T.plain("crack", (0.03, 0.01, 0.01), 0.6, emit=1.5, emit_col=(0.6, 0.02, 0.0))
rk = random.Random(5)
for i, (ang, ln) in enumerate(((200, 0.2), (235, 0.24), (270, 0.16), (300, 0.22), (160, 0.14), (330, 0.12))):
    a = Vector((-0.1, -0.0016, -0.07)) + Vector((math.cos(R(ang)), 0, math.sin(R(ang)))) * 0.07
    b = a + Vector((math.cos(R(ang)), 0, math.sin(R(ang)))) * ln
    cr = T.crack_curve(f"crack{i}", T.jag_path(a, b, 9, 0.012, rk), 0.0016, crk_m)
    cr.data.bevel_factor_mapping_end = "SPLINE"
    f0 = ER0 + 8 + i * 6
    cr.data.bevel_factor_end = 0.0; cr.data.keyframe_insert("bevel_factor_end", frame=f0)
    cr.data.bevel_factor_end = 1.0; cr.data.keyframe_insert("bevel_factor_end", frame=f0 + 30)
    vis(cr, [(f0, ER1)])

SEC_ALL = SEC_SHOTS + MOUTH
vis(sec, SEC_ALL)

# ======================================================================
# 2) BOSH SUYAGI (studiya) (10,0,0)
# ======================================================================
SK = Vector((10, 0, 0))
def load_skull(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=BK + "49c13194_u.glb")
    new = [o for o in bpy.data.objects if o not in before]
    sk = None
    for o in new:
        if o.type == "MESH" and not o.name.startswith("Text"): sk = o
    mw = sk.matrix_world.copy(); sk.parent = None; sk.matrix_world = mw
    for o in new:
        if o is not sk: bpy.data.objects.remove(o, do_unlink=True)
    _active(sk); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    sk.name = name; return sk
def _active(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)

WT = Vector((0.05, -0.086, 0.046))         # chap pastki aql tishi (bosh suyagi modeli koordinatasida)
skull = load_skull("skull")
skR = T.empty("skullR", tuple(SK + Vector((0, 0, 0.0)))); skull.parent = skR
skR.scale = (0.62, 0.62, 0.62); skR.location = SK + Vector((0, 0, 0.008))
# aql tishi joyida qizil pulsatsiya (shader maskasi)
for m in skull.data.materials:
    N = m.node_tree.nodes; L = m.node_tree.links
    b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord"); dist = N.new("ShaderNodeVectorMath"); dist.operation = "DISTANCE"
    L.new(tc.outputs["Object"], dist.inputs[0]); dist.inputs[1].default_value = tuple(WT)
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.004; mr.inputs[2].default_value = 0.017
    mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0; L.new(dist.outputs["Value"], mr.inputs[0])
    val = N.new("ShaderNodeValue"); val.name = "glow"; val.outputs[0].default_value = 0.0
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(mr.outputs[0], mul.inputs[0]); L.new(val.outputs[0], mul.inputs[1])
    b.inputs["Emission Color"].default_value = (1.0, 0.06, 0.02, 1); L.new(mul.outputs[0], b.inputs["Emission Strength"])
    SW0, SW1 = S["skull_wide"]; SM0, SM1 = S["skull_macro"]
    P.mat_value(m, "glow", 1, 0.0); P.mat_value(m, "glow", SW0, 0.6)
    for f in range(SW0 + 4, SM1, 10):
        P.mat_value(m, "glow", f, 5.0); P.mat_value(m, "glow", f + 5, 1.2)
floor_k = plane("sk_floor", (4, 4), tuple(SK), mat("sk_floor_m", (0.015, 0.015, 0.018), 0.65))
floor_k.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.15
vis(skR, rng("skull_wide", "skull_macro")); vis(floor_k, rng("skull_wide", "skull_macro"))


# ======================================================================
# 3) OSHXONA + MEGAN (30,0,0)
# ======================================================================
KIT = Vector((30, 0, 0))
kit = T.empty("kit", tuple(KIT))
def kpar(o): _par(o, kit); return o
kpar(plane("k_floor", (7, 7), tuple(KIT), pbr("k_floor_m", "laminate_floor_02", 1.2)))
wall_m = pbr("k_wall_m", "painted_plaster_wall", 1.0, tint=(0.95, 0.86, 0.74))
kpar(plane("k_wall_back", (7, 3.2), tuple(KIT + Vector((0, 1.7, 1.6))), wall_m, rot=(90, 0, 0)))
kpar(plane("k_wall_left", (7, 3.2), tuple(KIT + Vector((-2.2, 0, 1.6))), wall_m, rot=(90, 0, 90)))
kpar(plane("k_wall_right", (7, 3.2), tuple(KIT + Vector((2.2, 0, 1.6))), wall_m, rot=(90, 0, 90)))
kpar(plane("k_wall_front", (7, 3.2), tuple(KIT + Vector((0, -3.2, 1.6))), wall_m, rot=(90, 0, 0)))
kpar(plane("k_ceil", (7, 7), tuple(KIT + Vector((0, 0, 3.0))), mat("ceil", (0.9, 0.88, 0.85), 0.8), rot=(180, 0, 0)))
# deraza (chap devorda): yorqin oyna + rom
win_m = mat("window", (1.0, 0.97, 0.9), emit=6.0)
kpar(plane("k_window", (1.2, 1.3), tuple(KIT + Vector((-2.19, -0.4, 1.55))), win_m, rot=(90, 0, 90)))
frame_m = mat("frame", (0.95, 0.95, 0.93), 0.4)
for dz in (-0.68, 0.0, 0.68):
    kpar(box(f"k_wf{dz}", (0.06, 1.3, 0.05), tuple(KIT + Vector((-2.17, -0.4, 1.55 + dz))), frame_m))
for dy in (-0.62, 0.0, 0.62):
    kpar(box(f"k_wfv{dy}", (0.06, 0.05, 1.4), tuple(KIT + Vector((-2.17, -0.4 + dy, 1.55))), frame_m))
# stol (BlenderKit), dasturxonsiz
tbl = T.empty("tableR", tuple(KIT + Vector((0, -0.78, 0)))); _par(tbl, kit)
for o in import_gltf(BK + "8c7111e8_u.glb", tbl):
    if "cloth" in o.name: bpy.data.objects.remove(o, do_unlink=True)
wood_m = pbr("wood_m", "wood_table_001", 2.0)
# stul
CH = KIT + Vector((0, 0.02, 0))
kpar(box("chair_seat", (0.46, 0.44, 0.04), tuple(CH + Vector((0, 0.0, 0.45))), wood_m))
for sx in (-0.2, 0.2):
    for sy in (-0.19, 0.19):
        kpar(box(f"chair_leg{sx}{sy}", (0.04, 0.04, 0.45), tuple(CH + Vector((sx, sy, 0.225))), wood_m))
    kpar(box(f"chair_post{sx}", (0.04, 0.04, 0.55), tuple(CH + Vector((sx, 0.2, 0.74))), wood_m))
kpar(box("chair_back", (0.44, 0.03, 0.2), tuple(CH + Vector((0, 0.2, 0.9))), wood_m))
# idish, non, choynak o'rniga oddiy buyumlar
TT = 0.786
plate_m = mat("plate", (0.95, 0.95, 0.93), 0.15, coat=0.6)
kpar(cyl("plate", 0.12, 0.014, tuple(KIT + Vector((-0.1, -0.4, TT + 0.007))), plate_m, verts=48))
kpar(cyl("cup", 0.04, 0.09, tuple(KIT + Vector((0.22, -0.45, TT + 0.045))), mat("cup", (0.75, 0.2, 0.15), 0.25, coat=0.5)))
kpar(cyl("tea", 0.036, 0.002, tuple(KIT + Vector((0.22, -0.45, TT + 0.08))), mat("tea_m", (0.35, 0.12, 0.03), 0.05)))
kpar(cyl("bowl", 0.09, 0.05, tuple(KIT + Vector((0.4, -0.85, TT + 0.025))), mat("bowl", (0.2, 0.35, 0.6), 0.2, coat=0.6), verts=48))
plant = T.empty("plantR", tuple(KIT + Vector((-1.6, 1.25, 0)))); _par(plant, kit)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plant); plant.scale = (1.6, 1.6, 1.6)
# osma chiroq
kpar(cyl("lamp_cord", 0.004, 1.0, tuple(KIT + Vector((0, -0.75, 2.5))), mat("cord", (0.02, 0.02, 0.02), 0.5)))
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.2, radius2=0.05, depth=0.18, location=tuple(KIT + Vector((0, -0.75, 1.95))))
shade = bpy.context.object; shade.name = "lamp_shade"; shade.data.materials.append(mat("shade", (0.1, 0.25, 0.2), 0.4)); kpar(shade)
bpy.ops.object.modifier_add(type="SOLIDIFY"); shade.modifiers[-1].thickness = 0.005
kpar(sphere("bulb", 0.04, tuple(KIT + Vector((0, -0.75, 1.88))), mat("bulb_m", (1.0, 0.85, 0.6), emit=30.0)))

# --- Megan ---
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
mroot.location = KIT + Vector((0, 0.0, -0.02))
megF = T.empty("megF", tuple(mroot.location))
A_ = lambda f: mc.load_action(f, True)
LA0, LA1 = S["laugh"]; EW0 = S["eat_wide"][0]; EC0, EC1 = S["eat_close"]; CK0, CK1 = S["crack"]
mc.add_strip(meg, A_("Sitting_Idle_4.fbx"), 1, blend=0, repeat=8.0)
_la = A_("Sitting_Talking.fbx"); _a0 = _la.frame_range[0] + 60
mc.add_strip(meg, A_("Sitting_Talking.fbx"), LA0 - 24, blend=6, hold=False, src=(_a0, _a0 + (LA1 + 6 - (LA0 - 24)) / 0.8))
mc.add_strip(meg, A_("Sitting_Yell.fbx"), CK1 - 16, blend=4, hold=True)
# o'ng qo'l: somsani og'izga olib boradi (IK)
fa = meg.pose.bones["mixamorig:RightForeArm"]; hb = meg.pose.bones["mixamorig:RightHand"]
ikT = T.empty("ikT", (0, 0, 0), megF); poleT = T.empty("poleT", (-0.55, 0.05, 0.6), megF)
ik = fa.constraints.new("IK"); ik.target = ikT; ik.chain_count = 2; ik.use_tail = True; ik.pole_target = poleT; ik.pole_angle = R(-90)
upT = T.empty("upT", (0.2, -0.5, 1.12), megF); faceT = T.empty("faceT", (-0.05, -0.35, 1.7), megF)
dt = hb.constraints.new("DAMPED_TRACK"); dt.target = upT; dt.track_axis = "TRACK_Y"
lt = hb.constraints.new("LOCKED_TRACK"); lt.target = faceT; lt.lock_axis = "LOCK_Y"; lt.track_axis = "TRACK_Z"
headT = T.empty("headT", (0.0, -0.8, 1.0), megF)
hd = meg.pose.bones["mixamorig:Head"].constraints.new("DAMPED_TRACK"); hd.target = headT; hd.track_axis = "TRACK_Z"
curlE = T.empty("curlE", (0.45, 0, 0))
for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
    for i in (1, 2, 3):
        pbn = meg.pose.bones.get(f"mixamorig:RightHand{fn}{i}")
        if not pbn: continue
        c_ = pbn.constraints.new("TRANSFORM"); c_.target = curlE; c_.map_from = "LOCATION"; c_.from_min_x = 0; c_.from_max_x = 1
        c_.map_to = "ROTATION"; c_.owner_space = "LOCAL"; c_.target_space = "WORLD"; c_.mix_mode_rot = "AFTER"
        c_.map_to_x_from = "X"; c_.to_min_x_rot = 0; c_.to_max_x_rot = R(35 if fn == "Thumb" else 70)
        for f, v in ((1, 0.0), (EW0 - 1, 0.0), (EW0, 1.0), (EC1 + 1, 0.0)):
            c_.influence = v; c_.keyframe_insert("influence", frame=f)
for con in (ik, dt, lt, hd):
    for f, v in ((1, 0.0), (EW0 - 1, 0.0), (EW0, 1.0), (EC1 + 1, 0.0)):
        con.influence = v if con is not hd else v * 0.6; con.keyframe_insert("influence", frame=f)
for fcu in fcurves(meg):
    if "constraints" in fcu.data_path:
        for k in fcu.keyframe_points: k.interpolation = "CONSTANT"
MOUTH_P = Vector((-0.02, -0.23, 1.15))
BITE = EC0 + 10
key(ikT, EW0, loc=(-0.14, -0.42, 0.86)); key(ikT, EW0 + 14, loc=(-0.12, -0.42, 0.95))
key(ikT, EC0 - 2, loc=tuple(MOUTH_P + Vector((-0.09, -0.12, -0.09)))); key(ikT, BITE, loc=tuple(MOUTH_P + Vector((-0.08, -0.03, -0.065))))
key(ikT, BITE + 6, loc=tuple(MOUTH_P + Vector((-0.085, -0.06, -0.07)))); key(ikT, EC1, loc=tuple(MOUTH_P + Vector((-0.09, -0.08, -0.08))))
key(headT, EW0, loc=(0.0, -0.8, 1.05)); key(headT, BITE - 4, loc=(-0.03, -0.8, 1.02)); key(headT, BITE + 2, loc=(-0.04, -0.8, 0.94))
key(headT, EC1, loc=(-0.04, -0.8, 0.98))
# somsa: stoldagi likopchada; yeyish kadrida qo'lda
pastry = T.empty("pastryR", tuple(KIT + Vector((-0.1, -0.4, TT + 0.016))))
import_gltf(BK + "f0052100_u.glb", pastry); pastry.scale = (0.42, 0.42, 0.42); pastry.rotation_euler = (0, 0, R(30))
key(pastry, 1, loc=tuple(pastry.location), rot=(0, 0, 30))
for f in range(EW0, EC1 + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    hm = meg.matrix_world @ meg.pose.bones["mixamorig:RightHand"].matrix
    palm = (hm.to_3x3() @ Vector((0, 0, 1))).normalized(); fing = (hm.to_3x3() @ Vector((0, 1, 0))).normalized()
    pastry.location = hm.translation + fing * 0.065 + palm * 0.04
    q = (MOUTH_P + megF.location - pastry.location).to_track_quat("X", "Z")
    pastry.rotation_euler = q.to_euler(); pastry.keyframe_insert("location", frame=f); pastry.keyframe_insert("rotation_euler", frame=f)
pastry.location = KIT + Vector((-0.1, -0.4, TT + 0.016)); pastry.rotation_euler = (0, 0, R(30))
pastry.keyframe_insert("location", frame=EC1 + 1); pastry.keyframe_insert("rotation_euler", frame=EC1 + 1)
pastry.keyframe_insert("location", frame=EW0 - 1); pastry.keyframe_insert("rotation_euler", frame=EW0 - 1)
interp(pastry, "CONSTANT")
for fc in fcurves(pastry):
    for k in fc.keyframe_points:
        if EW0 <= k.co[0] < EC1: k.interpolation = "LINEAR"

# rentgen nusxasi: shaffof Megan + bosh suyagi + qizil aql tishi
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.4, base=0.015)
def xray_solid(name, col, base, edge):
    """Shaffofliksiz rentgen: chetlari yorqin, o'rtasi xira (ko'p qatlamli skan uchun shaffoflik chegarasiga urilmaydi)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.5; L.new(lw.outputs["Facing"], pw.inputs[0])
    ma = N.new("ShaderNodeMath"); ma.operation = "MULTIPLY_ADD"; ma.inputs[1].default_value = edge; ma.inputs[2].default_value = base
    L.new(pw.outputs[0], ma.inputs[0])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); L.new(ma.outputs[0], em.inputs["Strength"])
    L.new(em.outputs[0], out.inputs["Surface"]); return m
xray_bone = xray_solid("xray_bone", (0.75, 0.88, 1.0), 0.35, 2.6)
ghosts = []
for o in mmeshes:
    if "Eyelashes" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
XR0 = S["xray_in"][0] + 18
X_SHOTS = [S["hook"], (XR0, S["xray_in"][1]), S["crack"]]
KIT_SHOTS = [S["laugh"], (S["xray_in"][0], XR0 - 1), (EW0, EC1)]
for g in ghosts: vis(g, X_SHOTS, recursive=False)
for o in mmeshes: vis(o, KIT_SHOTS, recursive=False)
vis(kit, KIT_SHOTS); vis(pastry, KIT_SHOTS)
headE = T.empty("meg_head")
c = headE.constraints.new("CHILD_OF"); c.target = meg; c.subtarget = "mixamorig:Head"
c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
skx = load_skull("skull_xray")
dm = skx.modifiers.new("dec", "DECIMATE"); dm.ratio = 0.12; _active(skx); bpy.ops.object.modifier_apply(modifier=dm.name)
skx.data.materials.clear(); skx.data.materials.append(xray_bone)
SKX_S = float(os.environ.get("SKX_S", 0.6))
skxR = T.empty("skullxR", (0, -0.006, 0.068), headE); skxR.rotation_euler = (R(-90), 0, 0); skxR.scale = (SKX_S,) * 3
skx.parent = skxR
wt_m = mat("wt_glow", (0.8, 0.02, 0.0), emit=0.0)
T.glow_value(wt_m, "glow", 0.0, (1.0, 0.03, 0.0))
wt = sphere("wt_glow", 0.0075, tuple(WT), wt_m, scale=(1.0, 1.0, 0.8)); wt.parent = skxR
for f0, f1 in X_SHOTS:
    P.mat_value(wt_m, "glow", f0, 2.0)
    for f in range(f0 + 3, f1, 9):
        P.mat_value(wt_m, "glow", f, 12.0); P.mat_value(wt_m, "glow", f + 4, 4.0)
vis(skxR, X_SHOTS)
# sinish: qizil yoriq (pastki jag'da), uchqunlar
SNAP1, SNAP2 = CK0 + 12, CK0 + 31
crack_x = mat("crack_x", (1.0, 0.05, 0.0), emit=18.0)
rk2 = random.Random(9)
cx_paths = [T.jag_path((0.058, -0.08, 0.052), (0.056, -0.07, -0.004), 10, 0.006, rk2, axis=(1, 0, 0)),
            T.jag_path((0.057, -0.075, 0.03), (0.055, -0.05, 0.012), 6, 0.004, rk2, axis=(1, 0, 0)),
            T.jag_path((0.057, -0.072, 0.02), (0.056, -0.1, 0.006), 6, 0.004, rk2, axis=(1, 0, 0))]
for i, pts in enumerate(cx_paths):
    cr = T.crack_curve(f"xcrack{i}", pts, 0.0006, crack_x, skxR); cr.data.bevel_factor_mapping_end = "SPLINE"
    f0 = SNAP1 if i == 0 else SNAP2
    cr.data.bevel_factor_end = 0.0; cr.data.keyframe_insert("bevel_factor_end", frame=f0 - 1)
    cr.data.bevel_factor_end = 1.0; cr.data.keyframe_insert("bevel_factor_end", frame=f0 + 3)
    vis(cr, [(f0 - 1, CK1)])
spark_m = mat("spark", (1.0, 0.35, 0.1), emit=80.0)
rs = random.Random(13)
for i in range(24):
    sp_ = sphere(f"spark{i}", 0.0016, (0, 0, 0), spark_m, sub=1)
    f0 = SNAP1 if i < 14 else SNAP2
    p0 = Vector((0.058, -0.076, 0.03)); v = Vector((rs.uniform(0.2, 1.0), rs.uniform(-0.7, 0.7), rs.uniform(-0.3, 0.9))) * 0.004
    for k in range(0, 14):
        sp_.parent = skxR; sp_.location = p0 + v * k + Vector((0, 0, -0.0002 * k * k)); sp_.keyframe_insert("location", frame=f0 + k)
    vis(sp_, [(f0, f0 + 10)])

# ======================================================================
# 4) KAMERALAR
# ======================================================================
def tgt(name, loc): return T.empty(name, tuple(loc))
# 1 ilgak: rentgen bosh, yon tomondan crash zoom jag'ga
H0, H1 = S["hook"]
sc.frame_set(H0); bpy.context.view_layer.update()
HEADW = headE.matrix_world.translation.copy()
wt_world = lambda: (skxR.matrix_world @ WT)
hT = tgt("hookT", HEADW)
c = shot_cam("hook", tuple(HEADW + Vector((0.95, -0.25, 0.08))), hT, 30, 2.8, focus=hT)
sc.frame_set(H0); bpy.context.view_layer.update(); WTW = wt_world()
key(hT, H0, loc=tuple(HEADW + Vector((0, 0, 0.02)))); key(hT, H0 + 16, loc=tuple(WTW))
key(c, H0, loc=tuple(HEADW + Vector((0.95, -0.25, 0.08)))); key(c, H0 + 16, loc=tuple(WTW + Vector((0.42, -0.12, 0.03)))); key(c, H1, loc=tuple(WTW + Vector((0.34, -0.1, 0.02))))
lens_keys(c, ((H0, 26), (H0 + 14, 26), (H0 + 18, 50), (H1, 55)))
shake(c, H0 + 17, H0 + 26, 0.006, 3)
# 2 bosh suyagi keng, pastdan
SW0, SW1 = S["skull_wide"]
skC = SK + Vector((0, -0.03, 0.09))
c = shot_cam("skull_wide", tuple(SK + Vector((0.3, -0.36, 0.02))), tgt("skwT", skC), 18, 3.2)
key(c, SW0, loc=tuple(SK + Vector((0.3, -0.36, 0.02)))); key(c, SW1, loc=tuple(SK + Vector((0.08, -0.43, 0.015))))
# 3 makro: jag'dagi tishlar
SM0, SM1 = S["skull_macro"]
wtS = SK + Vector((0, 0, 0.008)) + WT * 0.62
c = shot_cam("skull_macro", tuple(wtS + Vector((0.18, -0.14, 0.03))), tgt("skmT", wtS), 45, 8.0)
key(c, SM0, loc=tuple(wtS + Vector((0.2, -0.15, 0.035)))); key(c, SM1, loc=tuple(wtS + Vector((0.13, -0.1, 0.02))))
# 4 kesim: tishlar qatori bo'ylab
RW0, RW1 = S["row"]
rT = tgt("rowT", (-0.5, 0, -0.06))
c = shot_cam("row", (-0.62, -0.52, 0.02), rT, 30, 5.0, focus=rT)
key(rT, RW0, loc=(-0.5, 0, -0.06)); key(rT, RW1, loc=(-0.15, 0, -0.08))
key(c, RW0, loc=(-0.6, -0.55, 0.03)); key(c, RW1, loc=(-0.1, -0.5, -0.02)); interp(rT, "BEZIER")
# 5 yonboshlagan tish, yaqin
SD0, SD1 = S["sideways"]
m3T = tgt("m3T", (-0.18, 0, -0.1))
c = shot_cam("sideways", (-0.05, -0.36, -0.02), m3T, 40, 4.0, focus=m3T)
key(c, SD0, loc=(-0.04, -0.38, -0.01)); key(c, SD1, loc=(-0.1, -0.27, -0.06))
shake(c, SD1 - 20, SD1, 0.002, 4)
# 6 kulayotgan qiz (yuzga yaqin, DOF)
sc.frame_set(LA0 + 10); bpy.context.view_layer.update()
FACE = headE.matrix_world.translation.copy() + Vector((0, -0.08, 0.07))
fT = tgt("faceT_cam", FACE)
c = shot_cam("laugh", tuple(FACE + Vector((0.32, -0.8, 0.02))), fT, 40, 2.0, focus=fT)
key(c, LA0, loc=tuple(FACE + Vector((0.4, -0.95, 0.0)))); key(c, LA1, loc=tuple(FACE + Vector((0.28, -0.75, -0.02))))
# 7 yuzga yaqinlashib rentgenga o'tish
XI0, XI1 = S["xray_in"]
sc.frame_set(XI0); bpy.context.view_layer.update(); WTW2 = wt_world()
xT = tgt("xinT", WTW2)
c = shot_cam("xray_in", tuple(WTW2 + Vector((0.55, -0.55, 0.06))), xT, 32, 2.8, focus=xT)
key(c, XI0, loc=tuple(WTW2 + Vector((0.6, -0.6, 0.06)))); key(c, XR0, loc=tuple(WTW2 + Vector((0.35, -0.35, 0.03))))
key(c, XI1, loc=tuple(WTW2 + Vector((0.2, -0.17, 0.01))))
# 8 buldozer: past burchak, keng
dT = tgt("dozT", (-0.2, 0, -0.095))
c = shot_cam("dozer", (-0.36, -0.2, -0.24), dT, 16, 4.0, focus=dT)
key(c, DZ0, loc=(-0.37, -0.21, -0.24)); key(c, DZ1, loc=(-0.31, -0.17, -0.2))
shake(c, DZ0 + 4, DZ0 + 18, 0.006, 5)
# 9 bosim: ildiz makro
pT = tgt("prT", CONTACT + Vector((-0.005, 0.012, 0.0)))
c = shot_cam("pressure", tuple(CONTACT + Vector((0.08, -0.36, 0.06))), pT, 40, 8.0, focus=pT)
key(c, PR0, loc=tuple(CONTACT + Vector((0.1, -0.38, 0.07)))); key(c, PR1, loc=tuple(CONTACT + Vector((-0.03, -0.3, 0.04))))
# 10 yemirilish: yanada yaqin
c = shot_cam("melt", tuple(CONTACT + Vector((-0.08, -0.3, -0.05))), pT, 45, 8.0, focus=pT)
key(c, ML0, loc=tuple(CONTACT + Vector((-0.09, -0.3, -0.06)))); key(c, ML1, loc=tuple(CONTACT + Vector((-0.04, -0.2, -0.025))))
# 11 og'iz ichi: tishlar qatori ustidan, oxiriga sho'ng'iydi
MO0, MO1 = S["mouth"]
moT = tgt("moT", (-0.3, 0, 0.04))
c = shot_cam("mouth", (-0.75, 0.2, 0.3), moT, 20, 4.0, focus=moT)
key(moT, MO0, loc=(-0.35, 0, 0.04)); key(moT, MO1, loc=(-0.17, 0, 0.03))
key(c, MO0, loc=(-0.78, 0.22, 0.32)); key(c, MO1, loc=(-0.42, 0.14, 0.17))
# 12 qopqoq ko'tariladi
flT = tgt("flT", (-0.16, 0, 0.03))
c = shot_cam("flap", (-0.33, 0.16, 0.14), flT, 35, 5.6, focus=flT)
key(c, FL0, loc=(-0.34, 0.17, 0.15)); key(c, FL1, loc=(-0.27, 0.12, 0.1))
# 13 ushoqlar
c = shot_cam("crumbs", (-0.36, 0.08, 0.2), flT, 30, 5.6, focus=flT)
key(c, CR0, loc=(-0.37, 0.07, 0.22)); key(c, CR1, loc=(-0.31, 0.1, 0.15))
# 14 cho'tka
brT = tgt("brT", (-0.24, 0, 0.06))
c = shot_cam("brush", (-0.62, 0.45, 0.25), brT, 24, 5.0, focus=brT)
key(c, BR0, loc=(-0.64, 0.47, 0.27)); key(c, BR1, loc=(-0.5, 0.38, 0.2))
# 15 kista o'sadi
cyT = tgt("cyT", (-0.11, 0, -0.05))
c = shot_cam("cyst", (-0.02, -0.4, -0.04), cyT, 35, 5.0, focus=cyT)
key(c, CY0, loc=(-0.0, -0.42, -0.03)); key(c, CY1, loc=(-0.08, -0.32, -0.06))
# 16 suyak yemiriladi: orqaga chekinish
c = shot_cam("erode", (-0.12, -0.42, -0.08), cyT, 32, 6.0, focus=cyT)
key(c, ER0, loc=(-0.12, -0.4, -0.08)); key(c, ER1, loc=(-0.2, -0.75, -0.02))
shake(c, ER0 + 10, ER0 + 40, 0.002, 6)
# 17 ovqatlanish: keng, pastdan
eT = tgt("eatT", KIT + Vector((0, -0.25, 0.98)))
c = shot_cam("eat_wide", tuple(KIT + Vector((1.0, -0.95, 0.84))), eT, 16, 4.0, focus=eT)
key(c, EW0, loc=tuple(KIT + Vector((1.05, -1.0, 0.83)))); key(c, EC0 - 1, loc=tuple(KIT + Vector((0.85, -0.82, 0.86))))
sc.frame_set(BITE); bpy.context.view_layer.update()
FACE2 = headE.matrix_world.translation.copy() + Vector((0, -0.08, 0.04))
f2T = tgt("face2T", FACE2 + Vector((-0.03, -0.08, -0.03)))
c = shot_cam("eat_close", tuple(FACE2 + Vector((0.55, -0.4, -0.03))), f2T, 50, 2.0, focus=f2T)
key(c, EC0, loc=tuple(FACE2 + Vector((0.58, -0.42, -0.04)))); key(c, EC1, loc=tuple(FACE2 + Vector((0.42, -0.3, -0.03))))
lens_keys(c, ((EC0, 38), (BITE, 38), (BITE + 3, 48), (EC1, 52)))
# 18 sinish: rentgen, jag'ga yaqin
sc.frame_set(CK0); bpy.context.view_layer.update(); WTW3 = wt_world()
ckT = tgt("ckT", WTW3 + Vector((0, 0, -0.02)))
c = shot_cam("crack", tuple(WTW3 + Vector((0.4, -0.22, -0.02))), ckT, 40, 2.8, focus=ckT)
key(c, CK0, loc=tuple(WTW3 + Vector((0.42, -0.24, -0.02)))); key(c, CK1, loc=tuple(WTW3 + Vector((0.3, -0.16, -0.03))))
shake(c, SNAP1, SNAP1 + 10, 0.01, 7); shake(c, SNAP2, SNAP2 + 12, 0.014, 8)
lens_keys(c, ((CK0, 40), (SNAP1, 40), (SNAP1 + 2, 52), (SNAP2, 52), (SNAP2 + 2, 66)))

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# tish cho'tkasi harakati (kamera aniqlangach): M2/M1 ustida u yoq-bu yoq, qopqoqqa urilib qaytadi
BRUSH_X0 = float(os.environ.get("BRUSH_X0", -0.31))
for f in range(BR0, BR1 + 1, 2):
    t = (f - BR0) / (BR1 - BR0)
    x = BRUSH_X0 + 0.05 * math.sin((f - BR0) * 0.55) + 0.07 * min(1, t * 1.6)
    x = min(x, -0.205)
    brushE.location = (x, 0.0, 0.198); brushE.rotation_euler = (R(4 * math.sin(f * 0.5)), R(-3), 0)
    brushE.keyframe_insert("location", frame=f); brushE.keyframe_insert("rotation_euler", frame=f)
    if x >= -0.206: key(hinge, f, rot=(0, -6, 0))

# ======================================================================
# 5) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
def env_bg(file, rot):
    mp = N.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, R(rot)); L.new(tcw.outputs["Generated"], mp.inputs[0])
    e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + file); L.new(mp.outputs[0], e.inputs[0])
    bgn = N.new("ShaderNodeBackground"); L.new(e.outputs[0], bgn.inputs[0]); return bgn
bg_st = env_bg("studio_small_09.hdr", 40)
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.004, 0.012, 0.03, 1)
bg_rd = N.new("ShaderNodeBackground"); bg_rd.inputs[0].default_value = (0.06, 0.005, 0.006, 1)
a1 = N.new("ShaderNodeAddShader"); a2 = N.new("ShaderNodeAddShader")
L.new(bg_st.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], a2.inputs[0]); L.new(bg_rd.outputs[0], a2.inputs[1])
L.new(a2.outputs[0], out.inputs["Surface"])
# (studio, qorong'i ko'k, qorong'i qizil)
WL = {"hook": (0, 1, 0), "skull_wide": (0.05, 1, 0), "skull_macro": (0.08, 1, 0), "row": (0.08, 1.5, 0), "sideways": (0.08, 1.5, 0),
      "laugh": (0.35, 0, 0), "xray_in": (0.3, 0.6, 0), "dozer": (0.06, 1.5, 0), "pressure": (0.05, 0, 1.5), "melt": (0.05, 0, 1.5),
      "mouth": (0.0, 0, 1.0), "flap": (0.0, 0, 1.0), "crumbs": (0.0, 0, 1.0), "brush": (0.0, 0, 1.0), "cyst": (0.08, 1.5, 0),
      "erode": (0.06, 0, 1.2), "eat_wide": (0.35, 0, 0), "eat_close": (0.35, 0, 0), "crack": (0, 0.8, 0.5)}
for f, n in SHOTS:
    for bgn, v in zip((bg_st, bg_dk, bg_rd), WL[n]):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
secT = tgt("secT", (-0.2, 0, -0.08))
SEC_L = SEC_SHOTS
area("S_key", (-0.6, -0.9, 0.6), 0.8, (1, 0.95, 0.9), lights_for(SEC_L, 16.0), target=secT)
area("S_fill", (0.5, -0.8, -0.2), 0.8, (0.7, 0.85, 1.0), lights_for(SEC_L, 3.0), target=secT)
area("S_rim", (0.2, 0.7, 0.5), 0.6, (0.5, 0.7, 1.0), lights_for(SEC_L, 18.0), target=secT)
area("S_red", (-0.4, -0.5, -0.4), 0.5, (1.0, 0.1, 0.05), lights_for(rng("pressure", "melt", "erode"), 5.0), target=secT)
point("contact_red", tuple(CONTACT + Vector((0.0, -0.03, 0.0))), 0.01, (1.0, 0.12, 0.03), lights_for(rng("pressure", "melt"), 0.25))
area("S_cyst", (-0.1, -0.35, 0.15), 0.3, (1.0, 0.85, 0.4), lights_for(rng("cyst"), 6.0), target=cyT)
moC = tgt("moC", (-0.25, 0, 0.04))
area("M_key", (-0.35, 0.25, 0.6), 0.4, (1, 0.96, 0.9), lights_for(MOUTH, 10.0), target=moC)
area("M_fill", (-0.6, -0.1, 0.3), 0.4, (1.0, 0.8, 0.75), lights_for(MOUTH, 2.0), target=moC)
area("M_rim", (0.15, -0.05, 0.25), 0.3, (1.0, 0.6, 0.5), lights_for(MOUTH, 5.0), target=moC)
# bosh suyagi studiyasi
skT2 = tgt("skT2", skC)
area("K_key", tuple(SK + Vector((-0.4, -0.5, 0.6))), 0.5, (1, 0.93, 0.85), lights_for(rng("skull_wide", "skull_macro"), 12.0), target=skT2)
area("K_rim", tuple(SK + Vector((0.5, 0.4, 0.4))), 0.4, (0.4, 0.65, 1.0), lights_for(rng("skull_wide", "skull_macro"), 20.0), target=skT2)
area("K_rim2", tuple(SK + Vector((-0.5, 0.4, 0.3))), 0.4, (1.0, 0.5, 0.25), lights_for(rng("skull_wide", "skull_macro"), 10.0), target=skT2)
# oshxona
KL = KIT_SHOTS
kT = tgt("kT", KIT + Vector((0, -0.4, 1.0)))
area("k_win", tuple(KIT + Vector((-2.0, -0.4, 1.6))), 1.3, (1.0, 0.95, 0.88), lights_for(KL, 150.0), target=kT)
point("k_lamp", tuple(KIT + Vector((0, -0.75, 1.82))), 0.05, (1.0, 0.75, 0.45), lights_for(KL, 50.0))
area("k_face", tuple(KIT + Vector((0.9, -1.4, 1.5))), 0.8, (1.0, 0.9, 0.82), lights_for(KL, 25.0), target=kT)
area("k_rim", tuple(KIT + Vector((1.0, 1.0, 1.8))), 0.6, (1.0, 0.7, 0.45), lights_for(KL, 45.0), target=kT)
# rentgen
xT2 = tgt("xT2", HEADW)
area("X_rim", tuple(HEADW + Vector((-0.6, 0.5, 0.4))), 0.6, (0.3, 0.6, 1.0), lights_for(X_SHOTS, 20.0), target=xT2)
point("X_red", tuple(HEADW + Vector((0.08, -0.08, -0.08))), 0.02, (1.0, 0.1, 0.03), lights_for(X_SHOTS, 2.0))

# ======================================================================
# 6) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 8; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", -0.2))
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
