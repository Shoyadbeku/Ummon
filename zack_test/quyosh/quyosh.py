# Quyoshga tikilish ko'zni kuydiradi (solar retinopatiya) — Zack D. Films uslubida 41.7 s video.
# Asos: zack_test/scene3.py + mixchar.py + koz_qon/koz_qon.py; makro ko'z: quyosh/eye.py; quvurlar: burish/parts.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/quyosh/quyosh.py --render
# Sinov: FRAMES=10,40,150,380,620 PCT=35
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "burish"))
from mathutils import Vector, Matrix, Euler
import mixchar as mc
import time, faulthandler
T0 = time.time()
def tick(msg): print(f"[{time.time() - T0:5.0f}s] {msg}", flush=True)
if os.environ.get("TRACE"): faulthandler.dump_traceback_later(int(os.environ["TRACE"]), repeat=True)

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import eye as E
import parts as P
sc = bpy.context.scene
sc.render.fps = 24
END = 1001
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, kadr = t*24+1) ----------------
SHOTS = [(1, "hook"), (21, "stare"), (68, "lupa"), (125, "burn"), (168, "lens"), (255, "uv"), (328, "focus"),
         (409, "face"), (463, "nerves"), (549, "cells"), (598, "cellburn"), (648, "nopain"), (697, "hours"),
         (781, "spot"), (847, "read"), (934, "glasses")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
F_HIT = 390          # "uradi" (16.2 s)
F_BURN = 131         # qog'oz tutay boshlaydi
F_CELL = 612         # "kuyib" (25.5 s)
F_SPOT = 806         # "qora dog'" (33.5 s)

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
    # har doim barcha kadr chegaralarida kalit qo'yiladi: keyingi chaqiruv oldingisini to'liq bosib yozadi
    marks = sorted({1, END + 1} | {f for f, _ in SHOTS} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, sss=0.0, coat=0.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def glow_mat(name, col, strength, alpha=1.0):
    """faqat nur sochadigan (soyasiz) material; alpha < 1 bo'lsa shaffof aralash"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (*col, 1); em.inputs[1].default_value = strength
    em.name = "EM"
    tr = N.new("ShaderNodeBsdfTransparent")
    ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(tr.outputs[0], ad.inputs[1])
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha; mx.name = "MIX"
    L.new(tr.outputs[0], mx.inputs[1]); L.new(ad.outputs[0] if alpha < 1 else em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0])
    return m

def key_em(m, f, v):
    s = m.node_tree.nodes["EM"].inputs[1]; s.default_value = v; s.keyframe_insert("default_value", frame=f)

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

def uvsphere(name, r, loc, m, seg=96, ring=64, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
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

def area(name, loc, size, col, keys, target=None, parent=None, kind="AREA"):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); sc.collection.objects.link(l)
    if kind == "AREA": l.data.size = size
    else: l.data.shadow_soft_size = size
    l.data.color = col; l.location = loc
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
        return empty(name + "_off", loc, e)
    return e

def value_key(node, f, v):
    node.outputs[0].default_value = v; node.outputs[0].keyframe_insert("default_value", frame=f)

def nodes_of(m): return m.node_tree.nodes, m.node_tree.links
def mth(N, L, op, a, b=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0]
def vnode(N, name, v):
    n = N.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n
def maprange(N, L, x, a, b, c=0.0, d=1.0):
    n = N.new("ShaderNodeMapRange"); L.new(x, n.inputs[0])
    for i, v in zip((1, 2, 3, 4), (a, b, c, d)):
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L.new(v, n.inputs[i])
    return n.outputs[0]

def curve_ray(name, pts, r, m, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 2
    cu.use_fill_caps = True; cu.bevel_factor_mapping_end = "SPLINE"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1.0)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(m)
    if parent: o.parent = parent
    return o

def grow(o, pairs):
    for f, v in pairs:
        o.data.bevel_factor_end = v; o.data.keyframe_insert("bevel_factor_end", frame=f)

def smoke_volume(name, loc, size, parent=None, col=(0.25, 0.24, 0.23), scale=18.0, rise=0.6, widen=0.5):
    """kichik tutun: kub ichida shovqinli zichlik, pastki markazdan yuqoriga kengayib ko'tariladi. SMOKE qiymati = umumiy zichlik"""
    o = box(name, size, loc, bpy.data.materials.new(name + "_m"), parent=parent)
    m = o.data.materials[0]; m.use_nodes = True; N, L = nodes_of(m)
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1)
    L.new(pv.outputs[0], out.inputs["Volume"])
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sx.inputs[0])
    X, Y, Z = sx.outputs
    # o'qdan masofa (Generated 0..1, markaz 0.5)
    dx = mth(N, L, "SUBTRACT", X, 0.5); dy = mth(N, L, "SUBTRACT", Y, 0.5)
    rr = mth(N, L, "SQRT", mth(N, L, "ADD", mth(N, L, "MULTIPLY", dx, dx), mth(N, L, "MULTIPLY", dy, dy)))
    lim = mth(N, L, "ADD", 0.05, mth(N, L, "MULTIPLY", Z, 0.4 * widen))
    radial = mth(N, L, "SUBTRACT", 1.0, mth(N, L, "DIVIDE", rr, lim), clamp=True)
    vert = mth(N, L, "MULTIPLY", mth(N, L, "SUBTRACT", 1.0, Z, clamp=True), mth(N, L, "MULTIPLY", Z, 12.0, clamp=True))
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Generated"], mp.inputs[0])
    mp.inputs["Scale"].default_value = (1, 1, 0.6); mp.name = "MAP"
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = scale * 0.3
    nz.inputs["Detail"].default_value = 6; nz.inputs["Roughness"].default_value = 0.6; nz.name = "NZ"
    L.new(mp.outputs[0], nz.inputs["Vector"])
    dens = mth(N, L, "MULTIPLY", mth(N, L, "MULTIPLY", radial, vert), mth(N, L, "MAXIMUM", mth(N, L, "SUBTRACT", nz.outputs["Fac"], 0.42), 0.0))
    sm = vnode(N, "SMOKE", 0.0)
    L.new(mth(N, L, "MULTIPLY", dens, sm.outputs[0]), pv.inputs["Density"])
    o["rise"] = rise
    return o, m

def smoke_anim(m, f0, f1, pairs):
    N = m.node_tree.nodes
    for f in (f0, f1):
        loc = N["MAP"].inputs["Location"]; loc.default_value = (0, 0, -(f - f0) * 0.03); loc.keyframe_insert("default_value", frame=f)
        w = N["NZ"].inputs["W"]; w.default_value = (f - f0) * 0.04; w.keyframe_insert("default_value", frame=f)
    for fc in mc._fcurves(m.node_tree.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
    for f, v in pairs: value_key(N["SMOKE"], f, v)

def burn_material(name, base, char_w, ember_w, noise_scale, paper=True, nz_amp=1.2):
    """kuyish: BURN radiusi (Object koordinatasida XY masofa) ichida teshik, chekkada cho'g', tashqarida qoraygan halqa.
    SCORCH: markazdagi sarg'ish iz; HOT: markazdagi yorqin nuqta"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N, L = nodes_of(m); b = N["Principled BSDF"]
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    d = mth(N, L, "SQRT", mth(N, L, "ADD", mth(N, L, "MULTIPLY", sx.outputs[0], sx.outputs[0]), mth(N, L, "MULTIPLY", sx.outputs[1], sx.outputs[1])))
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise_scale; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    d = mth(N, L, "ADD", d, mth(N, L, "MULTIPLY", mth(N, L, "SUBTRACT", nz.outputs["Fac"], 0.5), char_w * nz_amp))
    burn = vnode(N, "BURN", -1.0); scorch = vnode(N, "SCORCH", 0.0); hot = vnode(N, "HOT", 0.0)
    rel = mth(N, L, "SUBTRACT", d, burn.outputs[0])                       # 0 = kuyish chegarasi
    hole = mth(N, L, "LESS_THAN", rel, 0.0)
    ember = mth(N, L, "MULTIPLY", mth(N, L, "SUBTRACT", 1.0, mth(N, L, "DIVIDE", rel, ember_w), clamp=True), mth(N, L, "GREATER_THAN", rel, 0.0))
    charf = mth(N, L, "SUBTRACT", 1.0, mth(N, L, "DIVIDE", rel, char_w), clamp=True)
    charf = mth(N, L, "MULTIPLY", charf, mth(N, L, "GREATER_THAN", burn.outputs[0], 0.0))
    sc_ = mth(N, L, "MULTIPLY", mth(N, L, "SUBTRACT", 1.0, mth(N, L, "DIVIDE", d, char_w * 2.5), clamp=True), scorch.outputs[0])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(mth(N, L, "MAXIMUM", charf, sc_), c1.inputs["Factor"])
    c1.inputs[6].default_value = (*base, 1); c1.inputs[7].default_value = (0.02, 0.012, 0.008, 1)
    sc2 = N.new("ShaderNodeMix"); sc2.data_type = "RGBA"; L.new(mth(N, L, "MULTIPLY", sc_, 0.8), sc2.inputs["Factor"])
    L.new(c1.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    if paper:
        b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Scale"].default_value = 0.002
    # cho'g' + markazdagi yorqin nuqta
    spot = mth(N, L, "MULTIPLY", mth(N, L, "SUBTRACT", 1.0, mth(N, L, "DIVIDE", d, char_w * 0.25), clamp=True), hot.outputs[0])
    emi = mth(N, L, "ADD", mth(N, L, "MULTIPLY", mth(N, L, "POWER", ember, 2.0), 40.0), spot)
    L.new(emi, b.inputs["Emission Strength"]); b.inputs["Emission Color"].default_value = (1.0, 0.38, 0.06, 1)
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(hole, mx.inputs[0]); L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0])
    return m

tick("1) MAKRO KO'Z (dunyo markazi): qorachiqd")
# ======================================================================
# 1) MAKRO KO'Z (dunyo markazi): qorachiqda Quyosh aksi
# ======================================================================
eA = E.build_eye("eyeA", (0, 0, 0))
vis(eA["root"], rng("hook"))
for f, v in ((1, 0.0), (S["hook"][1] + 1, 0.0)): E.key_value(eA["hemo_a"], f, v)
E.key_value(eA["red"], 1, 0.35)
eA["ball"].data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.0
for f, v in ((1, 0.24), (4, 0.24), (10, 0.1), (S["hook"][1] + 1, 0.085)): E.key_value(eA["pupil"], f, v)
for f, v in ((1, 0.0), (6, 0.0), (12, 0.45), (S["hook"][1] + 1, 0.55)): E.set_key(eA, "squint", f, v)
key(eA["ball"], 1, rot=(-8, 0, -4))
M_sunref = glow_mat("sun_reflect", (1.0, 0.92, 0.75), 120.0)
sun_ref = sphere("sun_ref", 0.006, (-0.02, -0.2, 0.025), M_sunref, sub=2)
vis(sun_ref, rng("hook"))

tick("2) KO'CHA (x = -30): asfalt yo'l, trotua")
# ======================================================================
# 2) KO'CHA (x = -30): asfalt yo'l, trotuar, binolar, Quyosh
# ======================================================================
ST = Vector((-30.0, 0, 0)); street = empty("street", tuple(ST))
plane("pave", (14, 40), (0, 0, 0), pbr("pave_m", "concrete_pavement", 0.5), parent=street)
plane("road", (16, 40), (-11, 0, -0.12), pbr("road_m", "asphalt_02", 0.3), parent=street)
box("curb", (0.25, 40, 0.14), (-4.0, 0, -0.05), mat("curb", (0.55, 0.54, 0.52), 0.8), parent=street)
M_bld = pbr("bld_m", "painted_plaster_wall", 0.25, tint=(0.95, 0.88, 0.78))
M_glass = mat("bld_glass", (0.15, 0.2, 0.25), 0.05, metal=0.6)
rb = random.Random(3)
for k in range(9):
    h = rb.uniform(8, 22); w = rb.uniform(5, 9)
    y = -26 + k * 7.0
    box(f"bld{k}", (6, w, h), (7.5, y, h / 2), M_bld, parent=street)
    for j in range(int(h // 3)):
        box(f"win{k}_{j}", (0.05, w * 0.8, 1.3), (4.48, y, 1.8 + j * 3), M_glass, parent=street)
for k in range(5):           # yo'l bo'yi ustunlar
    cyl(f"pole{k}", 0.06, 5.5, (-3.7, -16 + k * 8, 2.75), mat("pole", (0.2, 0.2, 0.22), 0.4, metal=0.8), parent=street)
STREET_SHOTS = rng("stare", "face", "nopain", "glasses")
vis(street, STREET_SHOTS)
# Quyosh: Megan +Y tomonga, ~40 daraja balandlikka qaraydi
SUN_DIR = Vector((0.0, math.cos(R(40)), math.sin(R(40))))
M_sundisk = glow_mat("sun_disk", (1.0, 0.95, 0.85), 400.0)
sun_disk = sphere("sun_disk", 24.0, tuple(ST + Vector((0, 0, 1.6)) + SUN_DIR * 900), M_sundisk, sub=3)
sun_disk.visible_shadow = False; sun_disk.visible_diffuse = False; sun_disk.visible_glossy = False
vis(sun_disk, STREET_SHOTS)

tick("3) LUPA VA QOG'OZ (x = -60)")
# ======================================================================
# 3) LUPA VA QOG'OZ (x = -60)
# ======================================================================
LU = Vector((-60.0, 0, 0)); lupa_s = empty("lupa_scene", tuple(LU))
plane("lu_ground", (6, 6), (0, 0, 0), pbr("lu_ground_m", "concrete_pavement", 1.0), parent=lupa_s)
M_paper = burn_material("paper", (0.7, 0.68, 0.63), 0.01, 0.0015, 90.0, nz_amp=0.6)
paper = plane("paper", (0.21, 0.297), (0, -0.01, 0.003), M_paper, parent=lupa_s); paper.rotation_euler = (0, 0, R(12))
pn = M_paper.node_tree.nodes
LZ = 0.2
lup = empty("lupa", (0.0, -0.01, LZ), lupa_s); lup.rotation_euler = (R(6), R(-4), 0)
M_lglass = mat("lupa_glass", (0.95, 0.98, 1.0), 0.0, trans=1.0, ior=1.5)
sphere("lupa_lens", 0.055, (0, 0, 0), M_lglass, scale=(1, 1, 0.13), sub=4, parent=lup)
bpy.ops.mesh.primitive_torus_add(major_radius=0.056, minor_radius=0.0045, location=(0, 0, 0))
rim = bpy.context.object; rim.name = "lupa_rim"; rim.parent = lup; rim.scale = (1, 1, 1.6)
rim.data.materials.append(mat("lupa_rim_m", (0.75, 0.6, 0.3), 0.25, metal=1.0))
for p in rim.data.polygons: p.use_smooth = True
hd = cyl("lupa_handle", 0.009, 0.16, (0.13, 0.03, 0.01), mat("lupa_handle_m", (0.03, 0.02, 0.015), 0.35), rot=(0, 90, 15), parent=lup)
# yig'ilgan nur konusi
M_cone = glow_mat("light_cone", (1.0, 0.93, 0.75), 0.5, alpha=0.35)
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.0015, radius2=0.052, depth=LZ - 0.004, location=(0, -0.01, (LZ + 0.004) / 2), end_fill_type="NOTHING")
cone = bpy.context.object; cone.name = "light_cone"; cone.parent = lupa_s; cone.data.materials.append(M_cone)
cone.visible_shadow = False; cone.visible_diffuse = False
M_hot = glow_mat("hot_spot", (1.0, 0.85, 0.55), 60.0)
hot = sphere("hot_spot", 0.0022, (0, -0.01, 0.0035), M_hot, scale=(1, 1, 0.3), sub=2, parent=lupa_s)
smoke_p, M_smoke_p = smoke_volume("paper_smoke", (0, -0.01, 0.1), (0.12, 0.12, 0.2), parent=lupa_s, col=(0.12, 0.115, 0.11), scale=30)
LUPA_SHOTS = rng("lupa", "burn")
vis(lupa_s, LUPA_SHOTS)
vis(cone, rng("lupa"), False)
# kuyish ketma-ketligi (qog'ozning o'z koordinatasida, markaz = nur nuqtasi; qog'oz markazi (0,0) ga yaqin)
value_key(pn["BURN"], 1, -1.0); value_key(pn["BURN"], F_BURN + 4, -0.004); value_key(pn["BURN"], F_BURN + 10, 0.002)
value_key(pn["BURN"], S["burn"][1] + 1, 0.02)
value_key(pn["SCORCH"], 1, 0.0); value_key(pn["SCORCH"], S["lupa"][0] + 30, 0.0); value_key(pn["SCORCH"], F_BURN, 1.0)
value_key(pn["HOT"], 1, 0.0); value_key(pn["HOT"], S["lupa"][0] + 10, 25.0); value_key(pn["HOT"], F_BURN + 8, 30.0); value_key(pn["HOT"], F_BURN + 14, 0.0)
key_em(M_hot, 1, 20.0); key_em(M_hot, S["lupa"][0] + 20, 60.0); key_em(M_hot, F_BURN + 6, 60.0); key_em(M_hot, F_BURN + 12, 0.0)
key(hot, F_BURN + 6, scale=(1, 1, 0.3)); key(hot, F_BURN + 12, scale=(0.01, 0.01, 0.01))
smoke_anim(M_smoke_p, S["lupa"][0], S["burn"][1] + 1, [(1, 0.0), (S["lupa"][0] + 35, 0.0), (F_BURN, 8.0), (F_BURN + 15, 35.0), (S["burn"][1], 50.0)])

tick("4) KO'Z KESIMI (x = 30), R = 1 m; ko'z o")
# ======================================================================
# 4) KO'Z KESIMI (x = 30), R = 1 m; ko'z oldi mahalliy -Y, root -90 X bilan oldini tepaga (+Z) buradi
# ======================================================================
XS = Vector((30.0, 0, 0)); xs_root = empty("xsec", tuple(XS)); xs_root.rotation_euler = (R(-90), 0, 0)
def half_shell(name, r, thick, m, front_cut=None, back_cut=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=96, radius=r)
    kill = [v for v in bm.verts if v.co.x > 1e-4 or (front_cut is not None and v.co.y < front_cut) or (back_cut is not None and v.co.y > back_cut)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = xs_root
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m)
    so = o.modifiers.new("solid", "SOLIDIFY"); so.thickness = thick; so.offset = -1.0; so.use_rim = True; so.use_even_offset = True
    return o
M_sclera = mat("x_sclera", (0.92, 0.86, 0.82), 0.45, sss=0.3); M_sclera.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.05
M_choroid = mat("x_choroid", (0.35, 0.04, 0.04), 0.5, sss=0.3)
M_retina = mat("x_retina", (0.95, 0.42, 0.28), 0.35, sss=0.4, coat=0.4)
M_retina.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.03
sclera = half_shell("x_sclera", 1.0, 0.07, M_sclera, front_cut=-0.865)
choroid = half_shell("x_choroid", 0.93, 0.025, M_choroid, front_cut=-0.70)
retina = half_shell("x_retina", 0.905, 0.02, M_retina, front_cut=-0.66)
# shox parda (cornea): kichikroq sfera qalpog'i
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=64, radius=0.62)
for v in bm.verts: v.co.y -= 0.5
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 1e-4 or v.co.y > -0.855], context="VERTS")
me = bpy.data.meshes.new("x_cornea"); bm.to_mesh(me); bm.free()
cornea = bpy.data.objects.new("x_cornea", me); sc.collection.objects.link(cornea); cornea.parent = xs_root
for p in me.polygons: p.use_smooth = True
M_cornea = mat("x_cornea_m", (0.95, 0.98, 1.0), 0.02, trans=1.0, ior=1.376); me.materials.append(M_cornea)
so = cornea.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.03; so.offset = -1.0
# rangdor parda (iris): yarim halqa
def ring(name, r0, r1, y, m, thick):
    bm = bmesh.new(); n = 64; vs = []
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n          # x <= 0 yarmi
        vs.append((bm.verts.new((r0 * math.cos(a), y, r0 * math.sin(a))), bm.verts.new((r1 * math.cos(a), y, r1 * math.sin(a)))))
    for i in range(n):
        bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = xs_root; me.materials.append(m)
    s_ = o.modifiers.new("solid", "SOLIDIFY"); s_.thickness = thick; s_.offset = 0.0
    return o
M_iris = mat("x_iris", (0.12, 0.25, 0.32), 0.5)
iris = ring("x_iris", 0.17, 0.62, -0.72, M_iris, 0.04)
# gavhar (lens): shaffof, ichidan yonadi
M_lens = mat("x_lens", (0.85, 0.95, 1.0), 0.02, trans=1.0, ior=1.42)
lb = M_lens.node_tree.nodes["Principled BSDF"]; lb.inputs["Emission Color"].default_value = (0.65, 0.85, 1.0, 1)
lens_glow = M_lens.node_tree.nodes.new("ShaderNodeValue"); lens_glow.name = "GLOW"
M_lens.node_tree.links.new(lens_glow.outputs[0], lb.inputs["Emission Strength"])
lens = sphere("x_lens", 0.33, (0, -0.52, 0), M_lens, scale=(1, 0.48, 1), sub=5, parent=xs_root)
# shishasimon tana (vitreous) — juda xira
# ko'rish nervi (orqada)
M_nerve = mat("x_nerve", (0.95, 0.85, 0.55), 0.5, sss=0.3)
cyl("x_optic", 0.17, 0.8, (0, 1.3, 0), M_nerve, rot=(90, 0, 0), parent=xs_root, verts=48)
# to'r pardadagi qon tomirlari (kesim ichki yuzasi bo'ylab)
M_xv = mat("x_vessel", (0.45, 0.02, 0.02), 0.3, sss=0.3)
rv = random.Random(4)
for k in range(9):
    a0 = R(rv.uniform(-170, -10)); pts = []
    for j in range(7):
        th = R(15 + j * 11)            # orqa qutbdan burchak
        a = a0 + rv.uniform(-0.15, 0.15) * j
        d = Vector((math.sin(th) * math.cos(a), math.cos(th), math.sin(th) * math.sin(a)))
        if d.x > -0.03: d.x = -0.03 - rv.uniform(0, 0.1)
        pts.append(tuple(d.normalized() * 0.875))
    P.tube(f"x_vessel{k}", pts, 0.012, M_xv, parent=xs_root, taper=[1.4, 1.2, 1, 0.9, 0.7, 0.5, 0.3])
# fovea (sariq dog')
M_fovea = mat("x_fovea", (0.75, 0.35, 0.1), 0.3)
fov_b = M_fovea.node_tree.nodes["Principled BSDF"]; fov_b.inputs["Emission Color"].default_value = (1.0, 0.55, 0.15, 1)
fovea = sphere("x_fovea", 0.06, (0, 0.88, 0), M_fovea, scale=(1, 0.3, 1), sub=3, parent=xs_root)
# nurlar: oldindan (-Y) kelib, gavhardan o'tib, foveaga yig'iladi
M_ray = glow_mat("uv_ray", (0.35, 0.08, 1.0), 5.0)
FOC = Vector((0, 0.87, 0))
rays = []
for i in range(9):
    x0 = -0.03; z0 = -0.15 + i * 0.0375
    p0 = Vector((x0, -4.0, z0)); p1 = Vector((x0, -1.1, z0)); p2 = Vector((x0, -0.52, z0 * 0.85))
    rays.append(curve_ray(f"ray{i}", [tuple(p0), tuple(p1), tuple(p2), tuple(FOC)], 0.012, M_ray, parent=xs_root))
F0, F1 = S["focus"]
for i, o in enumerate(rays):
    grow(o, [(1, 0.0), (F0 + 2 + i, 0.0), (F0 + 34 + i, 0.55), (F_HIT, 1.0)])
    vis(o, rng("focus"), False)
M_flash = glow_mat("hit_flash", (0.6, 0.3, 1.0), 0.0)
flash = sphere("hit_flash", 0.07, tuple(FOC), M_flash, sub=3, parent=xs_root)
key_em(M_flash, 1, 0.0); key_em(M_flash, F_HIT - 1, 0.0); key_em(M_flash, F_HIT + 1, 30.0); key_em(M_flash, F_HIT + 10, 8.0); key_em(M_flash, F1 + 1, 6.0)
key(flash, F_HIT - 1, scale=(0.2, 0.2, 0.2)); key(flash, F_HIT + 2, scale=(1.6, 1.6, 1.6)); key(flash, F1, scale=(1.0, 1.0, 1.0))
vis(flash, rng("focus"), False)
value_key(lens_glow, 1, 0.0); value_key(lens_glow, S["lens"][0] + 30, 0.0); value_key(lens_glow, S["lens"][0] + 50, 2.5)
value_key(lens_glow, S["lens"][1], 2.5); value_key(lens_glow, F0, 0.6); value_key(lens_glow, F0 + 30, 3.0); value_key(lens_glow, F1 + 1, 1.5)
value_key(lens_glow, S["nerves"][0], 0.0)
# fovea kuyishi
fs = fov_b.inputs["Emission Strength"]
for f, v in ((1, 0.0), (F_HIT, 0.0), (F_HIT + 2, 15.0), (F1 + 1, 6.0), (S["nerves"][0], 0.0)):
    fs.default_value = v; fs.keyframe_insert("default_value", frame=f)
# asab tolalari (sariq, yonib turadi) faqat oldingi qismda: shox parda va rangdor parda atrofida
M_nf = P.pulse_material("nerve_fiber", (0.95, 0.8, 0.2), base_emit=1.5, pulse_col=(1.0, 0.85, 0.3), width=0.1)
nfs = []
rn = random.Random(11)
def cut_fiber(name, center, rad, th0, th1, side, r_):
    pts = []
    for j in range(7):
        th = R(th0 + (th1 - th0) * j / 6 + rn.uniform(-1.5, 1.5)); rr = rad + rn.uniform(-0.006, 0.006)
        pts.append(tuple(Vector(center) + Vector((0.006, -math.cos(th) * rr, side * math.sin(th) * rr))))
    return P.tube(name, pts, r_ * 1.8, M_nf, parent=xs_root, taper=[0.3, 0.8, 1, 1, 1, 0.8, 0.3])
for side in (-1, 1):
    for k in range(7):          # sklera devori ichida, old qismda
        t0 = rn.uniform(36, 48); nfs.append(cut_fiber(f"nfib{side}{k}", (0, 0, 0), 0.935 + 0.009 * k, t0, t0 + rn.uniform(25, 45), side, 0.006))
    for k in range(5):          # shox parda ichida
        nfs.append(cut_fiber(f"cfib{side}{k}", (0, -0.5, 0), 0.596 + 0.006 * k, rn.uniform(0, 4), rn.uniform(26, 34), side, 0.004))
    for k in range(3):          # rangdor parda (iris) bo'ylab
        z0 = 0.2 + 0.12 * k
        nfs.append(P.tube(f"ifib{side}{k}", [(0.006, -0.72, side * z0), (0.006, -0.73, side * (z0 + 0.06)), (0.006, -0.74, side * (z0 + 0.12))],
                          0.004, M_nf, parent=xs_root))
N0, N1 = S["nerves"]
for f in range(N0, N1 + 2, 10):
    P.mat_value(M_nf, "pos", f, -0.1); P.mat_value(M_nf, "pos", f + 9, 1.1)
P.mat_value(M_nf, "glow", N0, 6.0); P.mat_value(M_nf, "glow", N1 + 1, 6.0)
for o in nfs: vis(o, rng("nerves"), False)
XS_SHOTS = rng("lens", "focus", "nerves")
vis(xs_root, XS_SHOTS)
for o in rays + [flash]: vis(o, rng("focus"), False)
for o in nfs: vis(o, rng("nerves"), False)

tick("5) QUYOSH (koinot, x = 60)")
# ======================================================================
# 5) QUYOSH (koinot, x = 60)
# ======================================================================
SP = Vector((60.0, 0, 0)); space = empty("space", tuple(SP))
M_sun = bpy.data.materials.new("sun_surface"); M_sun.use_nodes = True; N, L = nodes_of(M_sun)
for n in list(N):
    if n.type != "OUTPUT_MATERIAL": N.remove(n)
out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
tc = N.new("ShaderNodeTexCoord")
nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 12
nz.inputs["Roughness"].default_value = 0.65; L.new(tc.outputs["Object"], nz.inputs["Vector"])
vor = N.new("ShaderNodeTexVoronoi"); vor.voronoi_dimensions = "4D"; vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = 9.0
L.new(tc.outputs["Object"], vor.inputs["Vector"])
mix_ = mth(N, L, "ADD", nz.outputs["Fac"], mth(N, L, "MULTIPLY", vor.outputs["Distance"], 0.8))
cr = N.new("ShaderNodeValToRGB"); L.new(mix_, cr.inputs[0])
cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.6, 0.08, 0.0, 1)
cr.color_ramp.elements[1].position = 0.95; cr.color_ramp.elements[1].color = (1.0, 0.85, 0.45, 1)
e_ = cr.color_ramp.elements.new(0.6); e_.color = (1.0, 0.4, 0.03, 1)
lw = N.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
limb = mth(N, L, "SUBTRACT", 1.0, mth(N, L, "MULTIPLY", lw.outputs["Facing"], 0.7))
em = N.new("ShaderNodeEmission"); L.new(cr.outputs[0], em.inputs[0]); L.new(mth(N, L, "MULTIPLY", limb, 12.0), em.inputs[1])
L.new(em.outputs[0], out.inputs[0])
for f, w in ((S["uv"][0], 0.0), (S["uv"][1] + 1, 0.6)):
    nz.inputs["W"].default_value = w; nz.inputs["W"].keyframe_insert("default_value", frame=f)
    vor.inputs["W"].default_value = w * 1.5; vor.inputs["W"].keyframe_insert("default_value", frame=f)
for fc in mc._fcurves(M_sun.node_tree.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
SUNC = SP + Vector((0, 45, 2))
sun_ball = uvsphere("sun_ball", 7.0, tuple(SUNC), M_sun, 128, 96)
# toj (korona): shaffof qobiq, chetida yonadi
M_cor = bpy.data.materials.new("corona"); M_cor.use_nodes = True; N, L = nodes_of(M_cor)
for n in list(N):
    if n.type != "OUTPUT_MATERIAL": N.remove(n)
out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
lw = N.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.5
fac = mth(N, L, "POWER", mth(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"], clamp=True), 3.0)
em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (1.0, 0.55, 0.15, 1); L.new(mth(N, L, "MULTIPLY", fac, 3.0), em.inputs[1])
tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(tr.outputs[0], ad.inputs[1])
L.new(ad.outputs[0], out.inputs[0])
corona = uvsphere("sun_corona", 9.5, tuple(SUNC), M_cor, 64, 48)
# yulduzlar
M_star = glow_mat("star", (0.9, 0.92, 1.0), 6.0)
rs_ = random.Random(8)
stars = []
for k in range(160):
    p = SP + Vector((rs_.uniform(-120, 120), 260, rs_.uniform(-200, 200)))
    stars.append(sphere(f"star{k}", rs_.uniform(0.15, 0.45), tuple(p), M_star, sub=1))
# ultrabinafsha nurlar: Quyoshdan kamera tomon uchadigan chiziqlar
M_uv = glow_mat("uv_streak", (0.35, 0.08, 1.0), 6.0)
U0, U1 = S["uv"]
streaks = []
for k in range(46):
    a = rs_.uniform(0, 2 * math.pi); rr = rs_.uniform(0.5, 6.5)
    st = SUNC + Vector((math.cos(a) * rr, -7.2, math.sin(a) * rr))
    en = SP + Vector((math.cos(a) * rr * 0.25 + rs_.uniform(-1, 1), -6, math.sin(a) * rr * 0.25 + rs_.uniform(-1.5, 1.5)))
    o = cyl(f"streak{k}", rs_.uniform(0.03, 0.07), 4.0, (0, 0, 0), M_uv, verts=8)
    d = (en - st).normalized(); o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    t0 = U0 + rs_.randint(-30, 50); dur = rs_.randint(28, 45)
    o.location = st; o.keyframe_insert("location", frame=t0)
    o.location = en; o.keyframe_insert("location", frame=t0 + dur)
    for fc in fcurves(o):
        for kk in fc.keyframe_points: kk.interpolation = "LINEAR"
        fc.extrapolation = "LINEAR"
    streaks.append(o)
SPACE_SHOTS = rng("uv")
for o in [sun_ball, corona] + stars + streaks: vis(o, SPACE_SHOTS, False)

tick("6) TO'R PARDA HUJAYRALARI (mikro, x = 90")
# ======================================================================
# 6) TO'R PARDA HUJAYRALARI (mikro, x = 90): tayoqcha va kolbachalar
# ======================================================================
CE = Vector((90.0, 0, 0)); cells_root = empty("cells", tuple(CE))
rc = random.Random(13)
def proto(r_top):
    """birlik hujayra (r=1, h=1): yon devor + tepa yarim sfera; (verts, faces)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=1.0, radius2=r_top, depth=1.0, matrix=Matrix.Translation((0, 0, 0.5)))
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r_top, matrix=Matrix.Translation((0, 0, 1.0)))
    vs = [v.co.copy() for v in bm.verts]; fs = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
    return vs, fs
PROTO = {False: proto(0.95), True: proto(0.45)}
SPC = 0.085; NC = 30
V_, F_ = [], []
for i in range(-NC, NC + 1):
    for j in range(-NC, NC + 1):
        x = i * SPC + (j % 2) * SPC * 0.5 + rc.uniform(-0.012, 0.012); y = j * SPC * 0.87 + rc.uniform(-0.012, 0.012)
        if math.hypot(x, y) > NC * SPC: continue
        cone_ = rc.random() < 0.18
        h = rc.uniform(0.55, 0.65) if not cone_ else rc.uniform(0.38, 0.44)
        r0 = 0.028 if not cone_ else 0.038
        vs, fs = PROTO[cone_]; o_ = len(V_)
        # tepa yarim sfera radiusi r0*r_top bo'lishi uchun XY = r0, Z = h; sfera qismi Z da ham r0 bilan
        for v in vs:
            zz = v.z * h if v.z <= 1.0 + 1e-6 else h + (v.z - 1.0) * r0
            V_.append((x + v.x * r0, y + v.y * r0, zz))
        F_ += [[k + o_ for k in f] for f in fs]
me = bpy.data.meshes.new("cells"); me.from_pydata(V_, [], F_)
cells = bpy.data.objects.new("cells", me); sc.collection.objects.link(cells); cells.parent = cells_root
for p in me.polygons: p.use_smooth = True
M_cell = burn_material("cell_m", (0.75, 0.32, 0.45), 0.5, 0.12, 2.5, paper=False)
cb_ = M_cell.node_tree.nodes["Principled BSDF"]
cb_.inputs["Subsurface Weight"].default_value = 0.6; cb_.inputs["Subsurface Scale"].default_value = 0.05
cb_.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.6); cb_.inputs["Roughness"].default_value = 0.35; cb_.inputs["Coat Weight"].default_value = 0.5
me.materials.append(M_cell)
cn = M_cell.node_tree.nodes
# kuyganda hujayralar cho'kadi: markazga yaqin uchlar pastga (shape key)
cells.shape_key_add(name="Basis"); kb = cells.shape_key_add(name="melt", from_mix=False); kb.value = 0.0
for i, v in enumerate(me.vertices):
    d = math.hypot(v.co.x, v.co.y); w = max(0.0, 1 - d / 0.9) ** 1.5
    kb.data[i].co = Vector((v.co.x * (1 + 0.15 * w), v.co.y * (1 + 0.15 * w), v.co.z * (1 - 0.75 * w)))
plane("cells_base", (6, 6), (0, 0, 0), mat("rpe", (0.08, 0.03, 0.02), 0.6), parent=cells_root)
C0, C1 = S["cells"]; CB0, CB1 = S["cellburn"]
value_key(cn["BURN"], 1, -1.0); value_key(cn["BURN"], F_CELL, -0.05); value_key(cn["BURN"], F_CELL + 8, 0.12); value_key(cn["BURN"], CB1 + 1, 0.75)
value_key(cn["SCORCH"], 1, 0.0); value_key(cn["SCORCH"], CB0, 0.0); value_key(cn["SCORCH"], F_CELL, 1.0)
value_key(cn["HOT"], 1, 0.0); value_key(cn["HOT"], CB0, 0.0); value_key(cn["HOT"], CB0 + 6, 6.0); value_key(cn["HOT"], F_CELL + 20, 0.0)
kb.keyframe_insert("value", frame=F_CELL); kb.value = 1.0; kb.keyframe_insert("value", frame=CB1 + 1)
M_beam = glow_mat("cell_beam", (0.35, 0.08, 1.0), 2.0, alpha=0.5)
beam = cyl("cell_beam", 0.16, 4.0, (0, 0, 2.6), M_beam, parent=cells_root, verts=32)
beam.visible_shadow = False
key_em(M_beam, CB0, 0.0); key_em(M_beam, CB0 + 4, 2.0); key_em(M_beam, CB1, 3.0)
key(beam, CB0, scale=(0.4, 0.4, 1)); key(beam, F_CELL, scale=(1, 1, 1)); key(beam, CB1, scale=(1.6, 1.6, 1))
smoke_c, M_smoke_c = smoke_volume("cell_smoke", (0, 0, 1.2), (2.0, 2.0, 1.8), parent=cells_root, col=(0.3, 0.27, 0.27), scale=6, widen=1.0)
smoke_anim(M_smoke_c, CB0, CB1 + 1, [(1, 0.0), (F_CELL, 0.0), (F_CELL + 10, 6.0), (CB1, 14.0)])
# cho'g' uchqunlari
M_emb = glow_mat("ember", (1.0, 0.4, 0.05), 40.0)
re_ = random.Random(17)
embers = []
for k in range(40):
    a = re_.uniform(0, 6.28); rr = re_.uniform(0, 0.5); t0 = re_.randint(F_CELL, CB1 - 8)
    p0 = Vector((math.cos(a) * rr, math.sin(a) * rr, 0.3))
    o = sphere(f"ember{k}", re_.uniform(0.006, 0.014), tuple(p0), M_emb, sub=1, parent=cells_root)
    o.location = p0; o.keyframe_insert("location", frame=t0)
    o.location = p0 + Vector((re_.uniform(-0.3, 0.3), re_.uniform(-0.3, 0.3), re_.uniform(0.6, 1.4))); o.keyframe_insert("location", frame=t0 + 30)
    o["rng"] = (t0, min(t0 + 30, CB1)); embers.append(o)
CELL_SHOTS = rng("cells", "cellburn")
vis(cells_root, CELL_SHOTS)
for o in [beam, smoke_c]: vis(o, rng("cellburn"), False)
for o in embers: vis(o, [tuple(o["rng"])], False)

tick("7) MEHMONXONA (x = -90): time-lapse, POV")
# ======================================================================
# 7) MEHMONXONA (x = -90): time-lapse, POV, kitob
# ======================================================================
M_plaster = pbr("plaster", "painted_plaster_wall", 0.6, tint=(0.93, 0.86, 0.76))
M_lam = pbr("laminate", "laminate_floor_02", 0.5)
LR = Vector((-90.0, 0, 0)); lroom = empty("living", tuple(LR))
plane("lr_floor", (6, 6), (0, 0, 0), M_lam, parent=lroom)
plane("lr_ceil", (6, 6), (0, 0, 2.7), mat("lr_ceil", (0.85, 0.84, 0.8), 0.9), rot=(180, 0, 0), parent=lroom)
for nm, sz, loc, rot in (("lr_n", (6, 2.7), (0, 2.2, 1.35), (90, 0, 0)), ("lr_s", (6, 2.7), (0, -2.6, 1.35), (90, 0, 0)),
                         ("lr_e", (6, 2.7), (2.4, 0, 1.35), (90, 0, 90))):
    plane(nm, sz, loc, M_plaster, rot=rot, parent=lroom)
# g'arbiy devor derazali (o'rtada teshik): 4 bo'lak
for nm, sz, loc in (("lr_w1", (6, 0.9), (-2.4, 0, 0.45)), ("lr_w2", (6, 0.6), (-2.4, 0, 2.4)),
                    ("lr_w3", (1.8, 1.2), (-2.4, -1.7, 1.5)), ("lr_w4", (1.4, 1.2), (-2.4, 1.5, 1.5))):
    plane(nm, (sz[0], sz[1]), loc, M_plaster, rot=(90, 0, 90), parent=lroom)
M_wframe = mat("wframe", (0.9, 0.9, 0.88), 0.4)
for nm, sz, loc in (("wf_t", (0.08, 1.6, 0.08), (-2.4, 0.0, 2.1)), ("wf_b", (0.12, 1.6, 0.08), (-2.4, 0.0, 0.9)),
                    ("wf_m", (0.08, 0.06, 1.2), (-2.4, 0.0, 1.5))):
    box(nm, sz, loc, M_wframe, parent=lroom)
M_winsky = glow_mat("win_sky", (1.0, 0.95, 0.88), 3.0)
win_sky = plane("win_sky", (1.6, 1.2), (-2.6, 0.0, 1.5), M_winsky, rot=(90, 0, 90), parent=lroom)
sofa = import_ph("Sofa_01", lroom, (0, 1.6, 0), 0)
plant = import_ph("potted_plant_01", lroom, (1.3, 1.75, 0), 0, 1.2)
frame_ = import_ph("fancy_picture_frame_01", lroom, (-0.2, 2.17, 1.55), 0, 1.6)
frame_.rotation_euler = (R(90), 0, 0)
table = import_ph("modern_coffee_table_01", lroom, (0.1, 0.75, 0), 0)
ROOM_SHOTS = rng("hours", "spot", "read")
vis(lroom, ROOM_SHOTS)
# ochiq kitob (stol ustida)
BOOK = LR + Vector((0.1, 0.72, 0.43))
book = empty("book", tuple(BOOK)); book.rotation_euler = (0, 0, R(4))
M_page = mat("page", (0.93, 0.9, 0.82), 0.85)
M_cover = mat("cover", (0.35, 0.08, 0.06), 0.5)
box("book_cover", (0.32, 0.23, 0.012), (0, 0, 0.006), M_cover, parent=book)
for sx in (-1, 1):
    pg = box(f"pages{sx}", (0.15, 0.215, 0.018), (sx * 0.077, 0, 0.021), M_page, rot=(0, sx * -4, 0), parent=book)
M_ink = mat("ink", (0.02, 0.02, 0.025), 0.6)
TEXT = ("Quyosh nuri hayot manbai, lekin unga to'g'ridan-to'g'ri qarash ko'z uchun juda xavfli. Ko'z gavhari nurni "
        "yig'ib, to'r pardaning kichik bir nuqtasiga jamlaydi. Bu nuqtada harorat keskin ko'tariladi va ko'rish hujayralari "
        "shikastlanadi. Shikast ko'pincha darhol sezilmaydi, chunki to'r pardada og'riq retseptorlari yo'q. Bir necha soatdan "
        "so'ng ko'rish maydonining markazida xira yoki qora dog' paydo bo'ladi. Bunday holat solar retinopatiya deb ataladi. "
        "Quyosh tutilishini kuzatishda faqat maxsus filtrli ko'zoynakdan foydalanish kerak, oddiy qora ko'zoynak himoya qilmaydi. "
        "Ko'zingizni asrang va Quyoshga hech qachon tikilib qaramang. ") * 2
words = TEXT.split(); lines = []; cur = ""
for w_ in words:
    if len(cur) + len(w_) + 1 > 34: lines.append(cur); cur = w_
    else: cur = (cur + " " + w_).strip()
TXT_OBJS = []
li = 0
for sx in (-1, 1):
    for k in range(22):
        if li >= len(lines): break
        cu = bpy.data.curves.new(f"txt{sx}{k}", "FONT"); cu.body = lines[li]; li += 1
        cu.size = 0.0062; cu.align_x = "LEFT"
        o = bpy.data.objects.new(f"txt{sx}{k}", cu); sc.collection.objects.link(o); o.parent = book
        o.location = (sx * 0.077 - 0.066, 0.094 - k * 0.0089, 0.0306 + (0.0045 if sx > 0 else 0.0045) - abs(sx * 0.077 - 0.0) * 0.0)
        o.rotation_euler = (0, R(sx * -4), 0)
        cu.materials.append(M_ink); TXT_OBJS.append(o)
vis(book, rng("read"))

tick("8) QAHRAMON: Megan")
# ======================================================================
# 8) QAHRAMON: Megan
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx")
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
soften(mmeshes)
A = lambda f, inplace=True: mc.load_action(f, inplace)
def at(root, f, loc, rz):
    root.location = loc; root.rotation_euler = (0, 0, R(rz))
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
MEG_ST = ST + Vector((0.0, 0.0, 0.0))
at(mroot, 1, tuple(MEG_ST), 180)                         # +Y ga qaraydi (Quyosh tomon)
at(mroot, S["hours"][0], tuple(LR + Vector((-1.3, 0.2, 0))), 55)      # deraza oldida, kamera tomon qaraydi
at(mroot, S["spot"][0], tuple(MEG_ST), 180)
interp(mroot, "CONSTANT")
MEG_SHOTS = rng("stare", "face", "nopain", "hours", "glasses")
vis(mroot, MEG_SHOTS)
mc.add_strip(meg, A("Idle_9.fbx"), 1, blend=0, repeat=4.0)
mc.add_strip(meg, A("Happy_Idle.fbx"), S["nopain"][0] - 10, blend=0, repeat=2.0)
mc.add_strip(meg, A("Crying.fbx"), S["hours"][0], blend=0, speed=1.15)
mc.add_strip(meg, A("Idle_9.fbx"), S["glasses"][0] - 2, blend=0, repeat=2.0, src=(60, 200))

def pose_layer(arm, name, keys, start):
    """Bo'g'imlar ustiga qo'shimcha burilish (COMBINE NLA). keys: {bone: [(f, (rx, ry, rz)), ...]} (gradus, mahalliy)"""
    ad = arm.animation_data; prev = ad.action
    act = bpy.data.actions.new(name); ad.action = act
    for bn, ks in keys.items():
        pb = arm.pose.bones["mixamorig:" + bn]; pb.rotation_mode = "QUATERNION"
        for f, e in ks:
            pb.rotation_quaternion = Euler([R(a) for a in e]).to_quaternion()
            pb.keyframe_insert("rotation_quaternion", frame=f)
            pb.rotation_quaternion = (1, 0, 0, 0)
    ad.action = prev
    tr = ad.nla_tracks.new(); tr.name = name
    s = tr.strips.new(name, int(start), act)
    if hasattr(s, "action_slot") and act.slots: s.action_slot = act.slots[0]
    s.blend_type = "COMBINE"; s.extrapolation = "HOLD"
    return s
z = (0, 0, 0)
UP_N, UP_H, UP_S = (-14, 0, 0), (-24, 0, 0), (-5, 0, 0)
def up_keys(on_ranges):
    ks = {"Spine2": [(1, z)], "Neck": [(1, z)], "Head": [(1, z)]}
    for a, b in on_ranges:
        for bn, v in (("Spine2", UP_S), ("Neck", UP_N), ("Head", UP_H)):
            ks[bn] += [(a - 1, z if a > 2 else v), (a, v), (b, v), (b + 1, z)]
    return ks
uk = up_keys(rng("stare", "face", "glasses"))
for bn, v in up_keys(rng("nopain")).items(): uk[bn] += [(f, tuple(a * 0.45 for a in e)) for f, e in v[1:]]
# "stare" boshida bosh asta ko'tariladi
for bn, v in (("Spine2", UP_S), ("Neck", UP_N), ("Head", UP_H)):
    lst = [(f, e) for f, e in uk[bn] if not (S["stare"][0] - 1 <= f <= S["stare"][0])]
    lst += [(S["stare"][0], z), (S["stare"][0] + 16, v)]
    uk[bn] = sorted(lst, key=lambda x: x[0])
pose_layer(meg, "meg_lookup", uk, 1)
mhead = bone_empty("meg_head", meg, "Head")
faceM = empty("meg_face", (0, 0.1, 0.09), mhead)
eyeM = empty("meg_eye", (-0.032, 0.1, 0.1), mhead)
# qora ko'zoynak (faqat oxirgi kadrda)
glasses = empty("glasses", (0, 0.1, 0.142), mhead)
M_sg = mat("sg_lens", (0.01, 0.01, 0.012), 0.05, coat=1.0, alpha=0.82)
M_sgf = mat("sg_frame", (0.01, 0.01, 0.01), 0.3)
for sx in (-1, 1):
    l_ = cyl(f"sg_lens{sx}", 0.027, 0.003, (sx * 0.033, 0, 0), M_sg, parent=glasses, verts=40); l_.scale = (1, 0.78, 1)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.0022, location=(sx * 0.033, 0, 0))
    t_ = bpy.context.object; t_.name = f"sg_rim{sx}"; t_.parent = glasses; t_.scale = (1, 0.78, 1); t_.data.materials.append(M_sgf)
    box(f"sg_temple{sx}", (0.003, 0.004, 0.12), (sx * 0.066, 0.004, -0.06), M_sgf, parent=glasses)
box("sg_bridge", (0.016, 0.003, 0.003), (0, 0.008, 0), M_sgf, parent=glasses)
vis(glasses, rng("glasses"))
G0, G1 = S["glasses"]
# ko'zoynakdan o'tib ketadigan binafsha nurlar (dunyo koordinatasida, kadr o'rtasida bosh holatiga qarab)
sc.frame_set(G0 + 20); bpy.context.view_layer.update()
eye_w = eyeM.matrix_world.translation.copy()
M_ray2 = glow_mat("uv_ray2", (0.35, 0.08, 1.0), 4.0)
grays = []
for k in range(7):
    off = Vector(((k - 3) * 0.012, 0, (k % 3 - 1) * 0.01))
    p0 = eye_w + SUN_DIR * 1.6 + off * 3; p1 = eye_w + off * 0.3 + Vector((0.0, -0.02, 0))
    o = curve_ray(f"gray{k}", [tuple(p0), tuple(p1)], 0.0025, M_ray2)
    grow(o, [(1, 0.0), (G0 + 4 + k * 2, 0.0), (G0 + 26 + k * 2, 1.0)])
    vis(o, rng("glasses"), False); grays.append(o)
sc.frame_set(1)

tick("9) KAMERALAR")
# ======================================================================
# 9) KAMERALAR
# ======================================================================
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c
def cam_path(c, pairs):
    for f, loc in pairs: key(c, f, loc=tuple(loc))

# 1 ilgak: makro ko'z, crash zoom
eyeT = empty("eyeT", (0.0, -0.012, 0.0))
c = shot_cam("hook", (0, 0, 0), eyeT, 30, 8.0, focus=eyeT)
cam_path(c, [(1, (0.02, -0.13, 0.012)), (5, (0.008, -0.07, 0.004)), (S["hook"][1] + 1, (0.006, -0.06, 0.003))])
lens_keys(c, [(1, 30), (5, 60), (S["hook"][1] + 1, 66)])
shake(c, 4, 16, 0.0012, 2)
# 2 tikilish: pastdan 16 mm, orqa-yon tomondan, Quyosh kadrda
headT = empty("headT", tuple(MEG_ST + Vector((0, 0.9, 2.4))))
c = shot_cam("stare", (0, 0, 0), headT, 16, 5.6, focus=faceM)
cam_path(c, [(S["stare"][0], MEG_ST + Vector((0.9, -1.4, 0.25))), (S["stare"][1] + 1, MEG_ST + Vector((0.75, -1.05, 0.3)))])
# 3 lupa: past burchak, yon tomonga suriladi
luT = empty("lupaT", tuple(LU + Vector((0, -0.01, 0.08))))
c = shot_cam("lupa", (0, 0, 0), luT, 24, 5.6, focus=luT)
cam_path(c, [(S["lupa"][0], LU + Vector((0.32, -0.36, 0.07))), (S["lupa"][1] + 1, LU + Vector((0.12, -0.42, 0.11)))])
# 4 kuyish: makro, crash zoom
spT = empty("spotT", tuple(LU + Vector((0, -0.01, 0.004))))
c = shot_cam("burn", (0, 0, 0), spT, 40, 14.0, focus=spT)
B0_, B1_ = S["burn"]
cam_path(c, [(B0_, LU + Vector((0.1, -0.18, 0.13))), (F_BURN + 8, LU + Vector((0.08, -0.15, 0.11))),
             (F_BURN + 12, LU + Vector((0.075, -0.14, 0.1))), (B1_ + 1, LU + Vector((0.07, -0.13, 0.1)))])
lens_keys(c, [(B0_, 40), (F_BURN + 8, 40), (F_BURN + 11, 52)])
shake(c, F_BURN + 9, F_BURN + 22, 0.003, 3)
# 5 ko'z kesimi: sekin aylanma (kesim yuzasi +X tomonda, ko'z oldi tepada)
xsT = empty("xsT", tuple(XS + Vector((0, 0, 0.15))))
c = shot_cam("lens", (0, 0, 0), xsT, 35, 8.0, focus=xsT)
L0, L1 = S["lens"]
for f in range(L0, L1 + 2, 4):
    t = (f - L0) / (L1 - L0); a = R(-30 + 40 * t)
    key(c, f, loc=tuple(XS + Vector((math.cos(a) * (5.6 - 1.2 * t), math.sin(a) * (5.6 - 1.2 * t), 0.9 - 0.5 * t))))
# 6 Quyosh: kamera orqaga, ozgina burilish
uvT = empty("uvT", tuple(SUNC))
c = shot_cam("uv", (0, 0, 0), uvT, 28, None)
cam_path(c, [(U0, SP + Vector((1.5, 18, -2.5))), (U1 + 1, SP + Vector((0.5, 2, -1.0)))])
# 7 nurlar yig'iladi: kesimga yaqinroq, "uradi"da silkinish + zoom
foT = empty("focusT", tuple(XS + Vector((0, 0, -0.2))))
c = shot_cam("focus", (0, 0, 0), foT, 30, 8.0, focus=foT)
cam_path(c, [(F0, XS + Vector((4.8, -1.2, 0.6))), (F_HIT, XS + Vector((4.2, -0.9, 0.2))), (F_HIT + 3, XS + Vector((3.0, -0.6, -0.3))),
             (F1 + 1, XS + Vector((2.9, -0.55, -0.35)))])
lens_keys(c, [(F0, 30), (F_HIT, 30), (F_HIT + 3, 38)])
shake(c, F_HIT, F_HIT + 16, 0.08, 4)
# 8 yuz yaqin: DOF, issiq kontur
c = shot_cam("face", (0, 0, 0), faceM, 60, 2.0)
FA0, FA1 = S["face"]
cam_path(c, [(FA0, MEG_ST + Vector((0.3, 0.95, 1.5))), (FA1 + 1, MEG_ST + Vector((0.22, 0.72, 1.52)))])
# 9 asab tolalari: kamera old qismdan to'r parda tomon suriladi
nT = empty("nervesT", tuple(XS + Vector((0, 0, 0.6))))
c = shot_cam("nerves", (0, 0, 0), nT, 28, 6.0, focus=nT)
cam_path(c, [(N0, XS + Vector((2.6, -0.6, 1.4))), (N0 + 40, XS + Vector((2.4, -0.4, 0.6))), (N1 + 1, XS + Vector((1.8, -0.2, -0.4)))])
nT.location = XS + Vector((0, 0, 0.75)); nT.keyframe_insert("location", frame=N0)
nT.location = XS + Vector((-0.1, 0, 0.4)); nT.keyframe_insert("location", frame=N0 + 40)
nT.location = XS + Vector((-0.2, 0, -0.75)); nT.keyframe_insert("location", frame=N1 + 1)
# 10 hujayralar: past burchak, sekin uchish
ceT = empty("cellsT", tuple(CE + Vector((0, 0, 0.45))))
c = shot_cam("cells", (0, 0, 0), ceT, 24, 2.8, focus=ceT)
cam_path(c, [(C0, CE + Vector((1.9, -1.7, 0.75))), (C1 + 1, CE + Vector((1.2, -1.2, 0.68)))])
# 11 hujayralar kuyadi: tepadan pastga, silkinish
c = shot_cam("cellburn", (0, 0, 0), ceT, 26, 3.5, focus=ceT)
cam_path(c, [(CB0, CE + Vector((-1.4, -1.5, 1.25))), (CB1 + 1, CE + Vector((-1.0, -1.15, 1.0)))])
shake(c, F_CELL, F_CELL + 18, 0.06, 5)
# 12 og'riq sezmaysiz: past burchak orbit, oldidan
NP0, NP1 = S["nopain"]
c = shot_cam("nopain", (0, 0, 0), faceM, 20, 4.0)
for f in range(NP0, NP1 + 2, 4):
    t = (f - NP0) / (NP1 - NP0); a = R(-35 + 50 * t)
    key(c, f, loc=tuple(MEG_ST + Vector((math.sin(a) * 1.2, math.cos(a) * 1.2, 0.8 + 0.15 * t))))
# 13 soatlar o'tib: time-lapse, sekin yaqinlashish
H0, H1 = S["hours"]
c = shot_cam("hours", (0, 0, 0), faceM, 35, 2.8)
cam_path(c, [(H0, LR + Vector((0.2, -1.2, 1.35))), (H1 + 1, LR + Vector((-0.4, -0.5, 1.5)))])
# 14 POV: xona, qora dog' paydo bo'ladi
SPo0, SPo1 = S["spot"]
povT = empty("povT", tuple(LR + Vector((-0.2, 2.1, 1.35))))
c = shot_cam("spot", (0, 0, 0), povT, 26, None)
cam_path(c, [(SPo0, LR + Vector((0.1, -1.3, 1.6))), (SPo1 + 1, LR + Vector((0.0, -0.8, 1.58)))])
povT.location = LR + Vector((-0.6, 2.1, 1.3)); povT.keyframe_insert("location", frame=SPo0)
povT.location = LR + Vector((0.1, 2.1, 1.45)); povT.keyframe_insert("location", frame=SPo1 + 1)
# 15 POV: kitob o'qish, ko'z satrlar bo'ylab yuradi
RD0, RD1 = S["read"]
bkT = empty("bookT", (0, 0, 0))
c = shot_cam("read", (0, 0, 0), bkT, 32, None)
for f in range(RD0, RD1 + 2, 2):
    t = (f - RD0) / (RD1 - RD0)
    line = t * 3.0; frac = line - int(line)
    tx = -0.13 + 0.11 * frac; ty = 0.06 - 0.02 * line
    key(c, f, loc=tuple(BOOK + Vector((tx * 0.6, ty - 0.2, 0.3))))
    bkT.location = BOOK + Vector((tx, ty, 0.03)); bkT.keyframe_insert("location", frame=f)
# 16 ko'zoynak: yon tomondan profil, nurlar oynadan o'tadi
c = shot_cam("glasses", (0, 0, 0), faceM, 32, 3.2)
cam_path(c, [(G0, MEG_ST + Vector((0.55, 0.75, 1.35))), (G1 + 1, MEG_ST + Vector((0.4, 0.62, 1.42)))])

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# --- qora dog' (kameraga yopishgan yarim shaffof disk, markazda) ---
def blind_spot(cam, name, pairs):
    M = bpy.data.materials.new(name); M.use_nodes = True; N, L = nodes_of(M)
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    d = mth(N, L, "SQRT", mth(N, L, "ADD", mth(N, L, "MULTIPLY", sx.outputs[0], sx.outputs[0]), mth(N, L, "MULTIPLY", sx.outputs[1], sx.outputs[1])))
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    rad = vnode(N, "RAD", 0.0)
    d = mth(N, L, "ADD", d, mth(N, L, "MULTIPLY", mth(N, L, "SUBTRACT", nz.outputs["Fac"], 0.5), 0.12))
    a = maprange(N, L, mth(N, L, "DIVIDE", d, mth(N, L, "MAXIMUM", rad.outputs[0], 0.001)), 1.0, 0.35, 0.0, 0.96)
    em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.01, 0.008, 0.012, 1); em.inputs[1].default_value = 0.0
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(a, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=2); o = bpy.context.object; o.name = name; o.data.materials.append(M)
    hw = 0.02 * 6.75 / cam.data.lens              # kadrning yarim kengligi 0.02 m masofada
    o.parent = cam; o.location = (0, 0.0, -0.02); o.scale = (hw, hw, 1)
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
    for f, v in pairs: value_key(rad, f, v)
    return o
blind_spot(CAMS["spot"], "spot_blind", [(SPo0, 0.0), (F_SPOT - 4, 0.03), (F_SPOT + 10, 0.5), (SPo1 + 1, 0.58)])
blind_spot(CAMS["read"], "read_blind", [(RD0, 0.55), (RD1 + 1, 0.6)])

tick("10) YORUG'LIK")
# ======================================================================
# 10) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
tcw = N.new("ShaderNodeTexCoord"); mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(-90))
L.new(tcw.outputs["Generated"], mpw.inputs[0])
env1 = N.new("ShaderNodeTexEnvironment"); env1.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env1.inputs[0])
env2 = N.new("ShaderNodeTexEnvironment"); env2.image = bpy.data.images.load(PH + "studio_small_09.hdr"); L.new(mpw.outputs[0], env2.inputs[0])
wm = N.new("ShaderNodeMix"); wm.data_type = "RGBA"; L.new(env1.outputs[0], wm.inputs[6]); L.new(env2.outputs[0], wm.inputs[7])
bg = N["Background"]; L.new(wm.outputs[2], bg.inputs[0])
# (osmon kuchi, studio aralashmasi)
WL = {"hook": (0.06, 1.0), "stare": (1.0, 0.0), "lupa": (1.0, 0.0), "burn": (1.0, 0.0), "lens": (0.15, 1.0), "uv": (0.0, 1.0),
      "focus": (0.12, 1.0), "face": (1.0, 0.0), "nerves": (0.12, 1.0), "cells": (0.0, 1.0), "cellburn": (0.0, 1.0),
      "nopain": (1.0, 0.0), "hours": (0.0, 0.0), "spot": (0.0, 0.0), "read": (0.0, 0.0), "glasses": (1.0, 0.0)}
for f, n in SHOTS:
    s_, m_ = WL[n]
    bg.inputs[1].default_value = s_; bg.inputs[1].keyframe_insert("default_value", frame=f)
    wm.inputs["Factor"].default_value = m_; wm.inputs["Factor"].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

# Quyosh (ko'cha va lupa kadrlari)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.94, 0.85)
sun.rotation_euler = Vector((0, 0, -1)).rotation_difference(-SUN_DIR).to_euler()
for f, e in lights_for(rng("stare", "lupa", "burn", "face", "nopain", "glasses"), 4.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
for f in (S["lupa"][0], S["burn"][0]): sun.data.energy = 2.2; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
street_rot = sun.rotation_euler.copy()
for f, n in SHOTS:
    sun.rotation_euler = (0, 0, 0) if n in ("lupa", "burn") else street_rot; sun.keyframe_insert("rotation_euler", frame=f)
interp(sun, "CONSTANT")
# makro ko'z
area("eye_key", (-0.09, -0.14, 0.11), 0.09, (1, 0.95, 0.88), lights_for(rng("hook"), 1.6), target=eA["root"])
area("eye_fill", (0.12, -0.1, -0.03), 0.12, (0.85, 0.9, 1.0), lights_for(rng("hook"), 0.4), target=eA["root"])
# ko'cha: yuzga issiq kontur
area("face_warm", tuple(MEG_ST + Vector((-0.6, 1.4, 2.2))), 0.6, (1.0, 0.6, 0.3), lights_for(rng("face", "glasses", "nopain"), 60), target=faceM)
area("stare_fill", tuple(MEG_ST + Vector((1.5, -1.5, 1.2))), 1.2, (0.75, 0.85, 1.0), lights_for(rng("stare"), 80), target=faceM)
# lupa: nur nuqtasidan issiq yorug'lik
pl = area("hot_light", tuple(LU + Vector((0, -0.01, 0.01))), 0.003, (1.0, 0.7, 0.35), [(1, 0), (S["lupa"][0], 0.05), (F_BURN, 0.1), (F_BURN + 10, 0.3), (B1_ + 1, 0)], kind="POINT")
for f, e in ((S["lupa"][0], 0.05), (F_BURN, 0.1), (F_BURN + 10, 0.3), (B1_, 0.35)): pl.data.energy = e; pl.data.keyframe_insert("energy", frame=f)
# ko'z kesimi: studiya yorug'ligi
xk = area("xs_key", tuple(XS + Vector((4, -3, 3))), 3.0, (1, 0.95, 0.9), lights_for(XS_SHOTS, 900), target=xsT)
area("xs_rim", tuple(XS + Vector((-3, 3, 2))), 2.0, (0.6, 0.5, 1.0), lights_for(XS_SHOTS, 500), target=xsT)
area("xs_fill", tuple(XS + Vector((3, 2, -3))), 2.5, (1.0, 0.75, 0.6), lights_for(XS_SHOTS, 300), target=xsT)
area("hit_light", tuple(XS + Vector((0.3, 0, -0.85))), 0.1, (0.7, 0.45, 1.0), [(1, 0), (F_HIT, 0), (F_HIT + 1, 300), (F_HIT + 12, 80), (F1 + 1, 0)], kind="POINT")
# hujayralar
area("cell_top", tuple(CE + Vector((0, 0, 3.5))), 1.0, (0.65, 0.45, 1.0), lights_for(CELL_SHOTS, 400), target=cells_root)
area("cell_rim", tuple(CE + Vector((-2.5, 2.5, 1.2))), 1.5, (1.0, 0.55, 0.65), lights_for(CELL_SHOTS, 250), target=ceT)
area("cell_fill", tuple(CE + Vector((2.5, -2.0, 1.0))), 1.5, (0.75, 0.8, 1.0), lights_for(CELL_SHOTS, 120), target=ceT)
area("cell_fire", tuple(CE + Vector((0, 0, 0.5))), 0.2, (1.0, 0.45, 0.1), [(1, 0), (F_CELL, 0), (F_CELL + 6, 60), (CB1 + 1, 0)], kind="POINT")
# mehmonxona: deraza (time-lapse) + ichki chiroq
win = area("lr_win", tuple(LR + Vector((-2.3, 0.0, 1.5))), 1.4, (1, 0.95, 0.88), lights_for(ROOM_SHOTS, 350), target=faceM)
win.rotation_euler = (0, R(-90), 0); win.constraints.clear()
lamp = area("lr_lamp", tuple(LR + Vector((1.2, 0.2, 2.5))), 0.6, (1, 0.8, 0.55), lights_for(ROOM_SHOTS, 120))
# time-lapse: kunduz -> kech -> kechki chiroq (har 3 kadrda sakraydi)
day = (1.0, 0.95, 0.88); dusk = (1.0, 0.5, 0.2); night = (0.35, 0.45, 0.9)
steps = list(range(H0, H1 + 1, 3))
for i, f in enumerate(steps):
    t = i / max(1, len(steps) - 1)
    col = [day[j] * (1 - t) + dusk[j] * t for j in range(3)] if t < 0.6 else [dusk[j] * (1 - (t - 0.6) / 0.4) + night[j] * (t - 0.6) / 0.4 for j in range(3)]
    flick = 1.0 if i % 2 == 0 else 0.75
    win.data.energy = 350 * (1 - 0.8 * t) * flick; win.data.keyframe_insert("energy", frame=f)
    win.data.color = col; win.data.keyframe_insert("color", frame=f)
    win.location = LR + Vector((-2.3, -0.6 + 1.2 * t, 1.9 - 0.7 * t)); win.keyframe_insert("location", frame=f)
    key_em(M_winsky, f, 3.0 * (1 - 0.85 * t) * flick)
    lamp.data.energy = 0 if t < 0.55 else 140; lamp.data.keyframe_insert("energy", frame=f)
win.data.energy = 60; win.data.keyframe_insert("energy", frame=SPo0); win.data.color = night; win.data.keyframe_insert("color", frame=SPo0)
lamp.data.energy = 140; lamp.data.keyframe_insert("energy", frame=SPo0)
key_em(M_winsky, SPo0, 0.4)
for f, e in ((END + 1, 0),): win.data.energy = e; win.data.keyframe_insert("energy", frame=S["glasses"][0])
lamp.data.energy = 0; lamp.data.keyframe_insert("energy", frame=S["glasses"][0])
interp(win.data, "CONSTANT"); interp(lamp.data, "CONSTANT"); interp(win, "CONSTANT")
area("read_lamp", tuple(BOOK + Vector((0.35, -0.3, 0.6))), 0.4, (1, 0.85, 0.65), lights_for(rng("read"), 25), target=book)

tick("11) RENDER")
# ======================================================================
# 11) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.cycles.volume_step_rate = 4.0
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
