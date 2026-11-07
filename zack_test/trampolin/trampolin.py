# "Batut qanday ixtiro qilingan" — Zack D. Films uslubida 55.5 s video (1332 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, aksirish/aksirish.py (yordamchilar, render sozlamalari).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_trampolin.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/trampolin/trampolin.py --render
# Sinov: FRAMES=40,100,160,230 PCT=30
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT)
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24
END = 1332
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (65, "pool"), (118, "sheet"), (197, "jumpon"), (249, "meh"), (314, "wall"), (406, "springs"),
         (483, "daha"), (509, "stretch"), (583, "launch"), (660, "butt"), (763, "steel"), (852, "bounce"), (936, "stuck"),
         (978, "pad"), (1073, "kid"), (1125, "flyoff"), (1173, "net"), (1237, "final")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
BREAK_F = 736          # "sinib" (30.62 s)
STUCK_F = 940          # "tiqilib" (39.08 s)

# ---------------- yordamchilar ----------------
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

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

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, ior=1.45, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    return m

def tex_mat(name, col, col2, rough, kind="noise", scale=10.0, bump=0.0, metal=0.0, coat=0.0, detail=2.0):
    m = mat(name, col, rough, metal=metal, coat=coat)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    t = N.new({"noise": "ShaderNodeTexNoise", "wave": "ShaderNodeTexWave", "voronoi": "ShaderNodeTexVoronoi",
               "checker": "ShaderNodeTexChecker"}[kind])
    L.new(tc.outputs["Object"], t.inputs["Vector"]); t.inputs["Scale"].default_value = scale
    if kind == "noise": t.inputs["Detail"].default_value = detail
    if kind == "wave": t.inputs["Distortion"].default_value = 3; t.inputs["Detail"].default_value = 3
    if kind == "checker":
        t.inputs["Color1"].default_value = (*col, 1); t.inputs["Color2"].default_value = (*col2, 1)
        L.new(t.outputs["Color"], b.inputs["Base Color"]); fac = t.outputs["Fac"]
    else:
        fac = t.outputs["Fac"] if "Fac" in t.outputs else t.outputs["Distance"]
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(fac, mx.inputs["Factor"])
        mx.inputs[6].default_value = (*col, 1); mx.inputs[7].default_value = (*col2, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    if bump:
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        L.new(fac, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
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
    if os.path.exists(os.path.join(PH, folder, "rough.jpg")):
        L.new(img("rough.jpg", True).outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(name, size, loc, m, rot=(0, 0, 0), bevel=0.0, origin_bottom=False):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    if origin_bottom:
        zmin = min(v.co.z for v in o.data.vertices)          # pastki yuz = origin
        for v in o.data.vertices: v.co.z -= zmin
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 2; b.limit_method = "ANGLE"
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o)
    bpy.ops.object.transform_apply(rotation=True)
    return o

def cyl_between(name, a, b, r, m, verts=16):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o)
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return o

def mesh_obj(name, verts, faces, m):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(m); smooth(o); return o

def import_gltf(path, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler.z = R(rot_z); root.scale = (scale,) * 3
    return root

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = 0.02
    d.clip_end = 500
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

def path_keys(o, pts):
    for f, p in pts: key(o, f, loc=p)

def orbit(cam, f0, f1, center, r0, r1, a0, a1, z0, z1, step=2):
    for f in range(f0, f1 + 1, step):
        t = (f - f0) / max(1, f1 - f0); t = t * t * (3 - 2 * t) * 0.5 + t * 0.5
        a = R(a0 + (a1 - a0) * t); rr = r0 + (r1 - r0) * t
        key(cam, f, loc=tuple(Vector(center) + Vector((rr * math.sin(a), -rr * math.cos(a), z0 + (z1 - z0) * t))))

def ease(t): return t * t * (3 - 2 * t)

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def follow(name, src, f0, f1, offset=(0, 0, 0), step=2, lerp=None):
    """src (bo'sh ob'ekt, suyakka bog'langan) dunyo joylashuvini kadrma-kadr nusxalab, silliq nishon yasaydi."""
    t = empty(name)
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); p = src.matrix_world.translation + Vector(offset)
        if lerp: p = p.lerp(Vector(lerp[0]), lerp[1](f))
        key(t, f, loc=tuple(p))
    return t

# ======================================================================
# 1) MATERIALLAR
# ======================================================================
M = dict(
    grass=pbr("ph_grass", "leafy_grass", 0.35),
    brick=pbr("ph_brick", "brick_wall_02", 0.45),
    tiles=pbr("ph_pooltiles", "blue_floor_tiles_01", 0.9),
    patio=pbr("ph_patio", "patio_tiles", 0.4),
    planks=pbr("ph_planks", "brown_planks_05", 0.5),
    plaster=pbr("ph_plaster", "painted_plaster_wall", 0.5, tint=(0.95, 0.9, 0.82)),
    roof=pbr("ph_roof", "clay_roof_tiles", 0.4),
    concrete=pbr("ph_concrete", "concrete_pavement", 0.4),
    coping=mat("coping", (0.82, 0.8, 0.75), 0.6),
    wood=tex_mat("post_wood", (0.45, 0.3, 0.17), (0.28, 0.17, 0.08), 0.7, "wave", 4.0, bump=0.3),
    wood_in=tex_mat("wood_inner", (0.78, 0.62, 0.4), (0.6, 0.45, 0.26), 0.8, "wave", 14.0, bump=0.5),
    sheet=tex_mat("bedsheet", (0.92, 0.93, 0.97), (0.45, 0.6, 0.85), 0.85, "wave", 3.0, bump=0.05),
    rope=tex_mat("rope", (0.75, 0.65, 0.45), (0.5, 0.42, 0.28), 0.9, "noise", 300.0, bump=0.4),
    jump_mat=tex_mat("jump_mat", (0.018, 0.018, 0.02), (0.05, 0.05, 0.055), 0.55, "checker", 180.0, bump=0.15),
    steel=mat("steel", (0.75, 0.76, 0.78), 0.22, metal=1.0),
    spring=mat("spring", (0.85, 0.86, 0.88), 0.18, metal=1.0),
    pad=tex_mat("pad", (0.03, 0.22, 0.75), (0.02, 0.17, 0.62), 0.35, "noise", 25.0, bump=0.05, coat=0.4),
    sleeve=mat("foam_sleeve", (0.03, 0.22, 0.75), 0.5),
    net=mat("net", (0.015, 0.015, 0.015), 0.6),
    glass=mat("window", (0.05, 0.07, 0.09), 0.03, coat=1.0),
    frame_w=mat("frame_white", (0.9, 0.9, 0.88), 0.4),
    door=mat("door", (0.3, 0.12, 0.06), 0.4, coat=0.3),
    leaves=tex_mat("leaves", (0.1, 0.26, 0.06), (0.2, 0.4, 0.1), 0.7, "voronoi", 9.0, bump=0.6),
    bark=tex_mat("bark", (0.2, 0.13, 0.08), (0.12, 0.08, 0.05), 0.9, "noise", 30.0, bump=0.5),
    hedge=tex_mat("hedge", (0.07, 0.2, 0.05), (0.15, 0.32, 0.08), 0.8, "voronoi", 14.0, bump=0.8),
)
# suv: shaffof, to'lqinli (Noise W vaqt bilan o'zgaradi)
water = mat("water", (0.55, 0.85, 0.95), 0.03, trans=1.0, ior=1.33)
Nw = water.node_tree.nodes; Lw = water.node_tree.links
nz = Nw.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 4
nz.inputs["W"].default_value = 0; nz.inputs["W"].keyframe_insert("default_value", frame=1)
nz.inputs["W"].default_value = 6; nz.inputs["W"].keyframe_insert("default_value", frame=END)
bpw = Nw.new("ShaderNodeBump"); bpw.inputs["Strength"].default_value = 0.12
Lw.new(nz.outputs["Fac"], bpw.inputs["Height"]); Lw.new(bpw.outputs[0], Nw["Principled BSDF"].inputs["Normal"])
lp_ = Nw.new("ShaderNodeLightPath"); trn = Nw.new("ShaderNodeBsdfTransparent"); trn.inputs[0].default_value = (0.75, 0.92, 1.0, 1)
mxs = Nw.new("ShaderNodeMixShader"); outw = Nw["Material Output"]
Lw.new(lp_.outputs["Is Shadow Ray"], mxs.inputs[0]); Lw.new(Nw["Principled BSDF"].outputs[0], mxs.inputs[1]); Lw.new(trn.outputs[0], mxs.inputs[2])
Lw.new(mxs.outputs[0], outw.inputs["Surface"])          # quyosh suv ostini yoritsin (kaustika o'chiq)
interp(water.node_tree, "LINEAR")
M["water"] = water

# ======================================================================
# 2) HOVLI: o'tloq, devor, qo'shnining basseyni, uylar
# ======================================================================
WALL_Y, WALL_H, WALL_H2 = 6.0, 2.2, 3.9
TC = Vector((0.0, 2.8, 0.0))                    # batut markazi
POOL = (-3.0, 3.0, 7.6, 12.4)                   # x0, x1, y0, y1
WZ = -0.12                                      # suv sathi

box("lawn", (40, 26, 0.1), (0, WALL_Y - 13.0, -0.05), M["grass"])
gfar = box("ground_far", (300, 300, 0.1), (0, 0, -0.12), M["grass"])
_cut = box("pool_cut", (6.0, 4.8, 1.0), (0, 10.0, 0), M["grass"]); _cut.hide_render = True; _cut.hide_viewport = True
_bo = gfar.modifiers.new("hole", "BOOLEAN"); _bo.object = _cut; _bo.operation = "DIFFERENCE"
box("wall", (24, 0.28, WALL_H), (0, WALL_Y, WALL_H / 2), M["brick"])
box("wall_cap", (24, 0.34, 0.06), (0, WALL_Y, WALL_H + 0.03), M["coping"])
wall_ext = box("wall_ext", (23.98, 0.26, WALL_H2 - WALL_H), (0, WALL_Y, WALL_H), M["brick"], origin_bottom=True)
wall_cap2 = box("wall_cap2", (24, 0.34, 0.06), (0, WALL_Y, WALL_H + 0.03), M["coping"])
# devor qator-qator o'sadi ("wall" kadri)
W0, W1 = S["wall"][0] + 14, S["wall"][1] - 16
EXT = WALL_H2 - WALL_H
wall_ext.location.z = WALL_H - EXT - 0.02; wall_ext.keyframe_insert("location", frame=1); wall_ext.keyframe_insert("location", frame=W0)
nrow = 10
for i in range(1, nrow + 1):
    f = W0 + int((W1 - W0) * i / nrow)
    wall_ext.location.z = WALL_H - EXT * (1 - i / nrow); wall_ext.keyframe_insert("location", frame=f)
    key(wall_cap2, f, loc=(0, WALL_Y, WALL_H + (WALL_H2 - WALL_H) * i / nrow + 0.03))
key(wall_cap2, 1, loc=(0, WALL_Y, WALL_H + 0.03)); key(wall_cap2, W0, loc=(0, WALL_Y, WALL_H + 0.03))
interp(wall_ext, "CONSTANT"); interp(wall_cap2, "CONSTANT")
vis(wall_cap2, [(W0 + 1, END)])

# qo'shni hovli: basseyn atrofidagi plitkalar
x0, x1, y0, y1 = POOL
box("deck_s", (24, y0 - WALL_Y - 0.14, 0.1), (0, (WALL_Y + 0.14 + y0) / 2, -0.05), M["patio"])
box("deck_n", (24, 6, 0.1), (0, y1 + 3, -0.05), M["patio"])
box("deck_w", (12 + x0, y1 - y0, 0.1), ((-12 + x0) / 2, (y0 + y1) / 2, -0.05), M["patio"])
box("deck_e", (12 - x1, y1 - y0, 0.1), ((12 + x1) / 2, (y0 + y1) / 2, -0.05), M["patio"])
for nm, s, l in (("cop_s", (x1 - x0 + 0.6, 0.3, 0.06), (0, y0 - 0.15, 0.02)), ("cop_n", (x1 - x0 + 0.6, 0.3, 0.06), (0, y1 + 0.15, 0.02)),
                 ("cop_w", (0.3, y1 - y0, 0.06), (x0 - 0.15, (y0 + y1) / 2, 0.02)), ("cop_e", (0.3, y1 - y0, 0.06), (x1 + 0.15, (y0 + y1) / 2, 0.02))):
    box(nm, s, l, M["coping"], bevel=0.015)
PD = 2.0
box("pool_floor", (x1 - x0, y1 - y0, 0.1), (0, (y0 + y1) / 2, -PD - 0.05), M["tiles"])
box("pool_w1", (x1 - x0, 0.1, PD), (0, y0 - 0.05, -PD / 2), M["tiles"])
box("pool_w2", (x1 - x0, 0.1, PD), (0, y1 + 0.05, -PD / 2), M["tiles"])
box("pool_w3", (0.1, y1 - y0, PD), (x0 - 0.05, (y0 + y1) / 2, -PD / 2), M["tiles"])
box("pool_w4", (0.1, y1 - y0, PD), (x1 + 0.05, (y0 + y1) / 2, -PD / 2), M["tiles"])
bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=1, location=(0, (y0 + y1) / 2, WZ))
wat = bpy.context.object; wat.name = "water"; wat.scale = (x1 - x0, y1 - y0, 1); wat.data.materials.append(M["water"])
box("pool_light", (0.3, 0.05, 0.2), (0, y1 - 0.01, -0.8), mat("plight", (0.7, 0.9, 1.0), 0.3, emit=4.0))
# qo'shni uyi
box("n_house", (16, 7, 6), (0, y1 + 9.5, 3), M["plaster"])
bpy.ops.mesh.primitive_cube_add(location=(0, y1 + 9.5, 6.9)); rf = bpy.context.object; rf.name = "n_roof"
rf.scale = (8.6, 4.0, 0.9); rf.data.materials.append(M["roof"])
bm = bmesh.new(); bm.from_mesh(rf.data)
for v in bm.verts:
    if v.co.z > 0: v.co.y *= 0.05
bm.to_mesh(rf.data); bm.free()
for dx in (-5, -1.6, 1.6, 5):
    box("n_win", (1.5, 0.06, 1.5), (dx, y1 + 5.98, 3.6), M["glass"]); box("n_winf", (1.7, 0.04, 1.7), (dx, y1 + 6.0, 3.6), M["frame_w"])
box("n_door", (2.4, 0.06, 2.2), (0, y1 + 5.98, 1.1), M["glass"]); box("n_doorf", (2.6, 0.04, 2.35), (0, y1 + 6.0, 1.15), M["frame_w"])
# bizning uy (orqada)
HY0 = -7.5
box("o_house", (18, 7, 6), (0, HY0 - 3.5, 3), M["plaster"])
for dx in (-5.5, 5.5):
    box("o_win", (1.6, 0.06, 1.4), (dx, HY0 + 0.02, 1.7), M["glass"]); box("o_winf", (1.8, 0.04, 1.6), (dx, HY0 + 0.04, 1.7), M["frame_w"])
    box("o_win2", (1.6, 0.06, 1.4), (dx, HY0 + 0.02, 4.4), M["glass"]); box("o_win2f", (1.8, 0.04, 1.6), (dx, HY0 + 0.04, 4.4), M["frame_w"])
box("o_slide", (3.2, 0.06, 2.3), (0, HY0 + 0.02, 1.15), M["glass"]); box("o_slidef", (3.4, 0.04, 2.45), (0, HY0 + 0.04, 1.2), M["frame_w"])
box("o_patio", (10, 3.2, 0.12), (0, HY0 + 1.6, 0.0), M["concrete"])
# yon panjaralar (taxta)
for sx in (-1, 1):
    box("fence", (0.08, WALL_Y - HY0, 1.9), (sx * 9.5, (WALL_Y + HY0) / 2, 0.95), M["planks"])
# butalar (devor bo'ylab) va daraxtlar
def shrub_blob(x, y, s=1.0):
    o = bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.6 * s, location=(x, y, 0.45 * s)); o = bpy.context.object
    o.name = "hedge"; o.scale = (1.3, 0.8, 0.85); o.data.materials.append(M["hedge"]); smooth(o)
    d = o.modifiers.new("d", "DISPLACE"); d.strength = 0.25 * s; t = bpy.data.textures.new("hc", "CLOUDS"); t.noise_scale = 0.25; d.texture = t
    return o
for x in (-7.5, -5.6, 5.8, 7.6):
    shrub_blob(x, WALL_Y - 0.75, 1.0)
for i, (x, y) in enumerate(((-8.2, 1.5), (8.0, -1.0), (-8.0, -4.5))):
    import_gltf(PH + ("shrub_01" if i % 2 == 0 else "shrub_02") + "/" + ("shrub_01" if i % 2 == 0 else "shrub_02") + ".gltf", (x, y, 0), 30 * i, 1.6)
def tree(x, y, s=1.0):
    cyl("trunk", 0.14 * s, 3.0 * s, (x, y, 1.5 * s), M["bark"], verts=12)
    for dx, dy, dz, r in ((0, 0, 3.6, 1.6), (0.9, 0.3, 3.1, 1.1), (-0.8, -0.4, 3.2, 1.2), (0.1, 0.5, 4.5, 1.1)):
        o = bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r * s, location=(x + dx * s, y + dy * s, dz * s)); o = bpy.context.object
        o.data.materials.append(M["leaves"]); smooth(o)
        d = o.modifiers.new("d", "DISPLACE"); d.strength = 0.45 * s; t = bpy.data.textures.new("cl", "CLOUDS"); t.noise_scale = 0.45; d.texture = t
for x, y, s in ((-7.0, 14.0, 1.4), (8.5, 15.0, 1.2), (-12, 3, 1.5), (12, 0, 1.3), (-11, -8, 1.2)):
    tree(x, y, s)
import_gltf(PH + "outdoor_table_chair_set_01/outdoor_table_chair_set_01.gltf", (-4.5, HY0 + 2.2, 0.06), 15)
import_gltf(PH + "garden_gnome/garden_gnome.gltf", (3.2, WALL_Y - 0.9, 0), -20, 1.3)
import_gltf(PH + "plastic_monobloc_chair_01/plastic_monobloc_chair_01.gltf", (x1 + 1.2, y0 + 1.0, 0), -110)
import_gltf(PH + "plastic_monobloc_chair_01/plastic_monobloc_chair_01.gltf", (x1 + 1.3, y0 + 2.2, 0), -80)

# ======================================================================
# 3) BATUT: A (ustun + choyshab), B (yog'och rama + prujina), C (temir rama + prujina + qoplama + to'r)
# ======================================================================
MZ_A, MZ_B, MZ_C = 0.78, 0.8, 0.88
def dip_mesh(name, verts2d, faces, mz, m, edge_drop, pull, rho):
    """verts2d: (x, y); rho(x, y) -> 0 markaz, 1 chekka. 'dip' shape key: qiymat = markaz chuqurligi (m)."""
    o = mesh_obj(name, [(x, y, 0) for x, y in verts2d], faces, m)
    o.location = (TC.x, TC.y, mz)
    o.shape_key_add(name="Basis", from_mix=False)
    k = o.shape_key_add(name="dip", from_mix=False); k.value = 0.0
    for i, (x, y) in enumerate(verts2d):
        r_ = rho(x, y)
        dz = -(edge_drop + (1 - edge_drop) * (1 - min(1, r_) ** 2))
        n = Vector((x, y, 0)); n = n.normalized() if n.length > 1e-6 else n
        k.data[i].co = Vector((x, y, dz)) - n * pull * r_
    return o

def key_dip(o, f, d, name="dip"):
    kb = o.data.shape_keys.key_blocks[name]; kb.value = d; kb.keyframe_insert("value", frame=f)

# --- A: to'rtta yog'och ustun va choyshab ---
HA = 1.3
nA = 36
vA = [(-HA + 2 * HA * i / nA, -HA + 2 * HA * j / nA) for j in range(nA + 1) for i in range(nA + 1)]
fA = [(j * (nA + 1) + i, j * (nA + 1) + i + 1, (j + 1) * (nA + 1) + i + 1, (j + 1) * (nA + 1) + i) for j in range(nA) for i in range(nA)]
sheetA = dip_mesh("sheetA", vA, fA, MZ_A, M["sheet"], 0.0, 0.0,
                  lambda x, y: math.sqrt(max(abs(x), abs(y)) ** 2 * 0.6 + (x * x + y * y) * 0.4) / HA)
# "g'ijim" holati: choyshab yerda yig'ilib yotadi -> burchaklarga tortiladi
kc = sheetA.shape_key_add(name="crumple", from_mix=False); kc.value = 0
rnd = random.Random(3)
for i, (x, y) in enumerate(vA):
    kc.data[i].co = Vector((x * 0.28 - 0.9, y * 0.22 - 1.0, -MZ_A + 0.05 + 0.08 * (math.sin(x * 9) * math.cos(y * 7) + 1) + rnd.uniform(0, 0.02)))
sheetA.modifiers.new("sol", "SOLIDIFY").thickness = 0.004
postsA = []
PP = 1.55
for sx in (-1, 1):
    for sy in (-1, 1):
        p = cyl("postA", 0.06, 1.05, (TC.x + sx * PP, TC.y + sy * PP, 0.52), M["wood"], verts=12); postsA.append(p)
        rp = cyl_between("ropeA", (TC.x + sx * HA, TC.y + sy * HA, MZ_A), (TC.x + sx * PP, TC.y + sy * PP, MZ_A + 0.12), 0.012, M["rope"], 8)
        postsA.append(rp)
SH0 = S["sheet"][0]
for f, v in ((1, 1.0), (SH0 + 12, 1.0), (SH0 + 52, 0.0)):
    kc.value = v; kc.keyframe_insert("value", frame=f)
ropes = [o for o in postsA if o.name.startswith("ropeA")]
for rp in ropes:
    rp.scale = (1, 1, 0.01); rp.keyframe_insert("scale", frame=SH0 + 30); rp.scale = (1, 1, 1); rp.keyframe_insert("scale", frame=SH0 + 54)
vis(sheetA, [(S["sheet"][0], S["wall"][1])])
for o in postsA: vis(o, [(S["sheet"][0], S["wall"][1])])

# --- B: yog'och rama (ustunlar ustida to'sinlar) + prujinalar + ichki choyshab ---
HB_IN, HB_FR = 1.12, 1.45          # choyshab yarim kengligi, rama ichki chekkasi
nB = 32
vB = [(-HB_IN + 2 * HB_IN * i / nB, -HB_IN + 2 * HB_IN * j / nB) for j in range(nB + 1) for i in range(nB + 1)]
fB = [(j * (nB + 1) + i, j * (nB + 1) + i + 1, (j + 1) * (nB + 1) + i + 1, (j + 1) * (nB + 1) + i) for j in range(nB) for i in range(nB)]
PULL_B, EDGE_B = 0.32, 0.22
sheetB = dip_mesh("sheetB", vB, fB, MZ_B, M["jump_mat"], EDGE_B, PULL_B, lambda x, y: max(abs(x), abs(y)) / HB_IN)
# sinish: old (y<0) chekka pastga tushadi
kbr = sheetB.shape_key_add(name="broken", from_mix=False); kbr.value = 0
BR_ANG = R(33)
def beam_drop(x):                          # old to'sin yarmi ilmoqdan (x=+-HB_FR) qancha pastga tushgan (to'liq sinishda)
    return (HB_FR - min(abs(x), HB_FR)) * math.sin(BR_ANG)
for i, (x, y) in enumerate(vB):
    t = max(0.0, -y / HB_IN)
    kbr.data[i].co = Vector((x, y, -beam_drop(x) * t ** 1.5 * 0.92))
beamsB, legsB = [], []
BW = 0.12
for sx in (-1, 1):                          # yon to'sinlar (x = +-)
    beamsB.append(box("beamB_side", (BW, 2 * HB_FR + 2 * BW, BW), (TC.x + sx * (HB_FR + BW / 2), TC.y, MZ_B - BW / 2 + 0.02), M["wood"]))
beamsB.append(box("beamB_back", (2 * HB_FR, BW, BW), (TC.x, TC.y + HB_FR + BW / 2, MZ_B - BW / 2 + 0.02), M["wood"]))
# old to'sin ikki yarmi (sinadigan), ilmoqlari chekkada
halves = []
for sx in (-1, 1):
    h = empty(f"hingeB_{sx}", (TC.x + sx * HB_FR, TC.y - HB_FR - BW / 2, MZ_B - BW / 2 + 0.02))
    b = box(f"beamB_front_{sx}", (HB_FR, BW, BW), (0, 0, 0), M["wood"]); b.parent = h; b.location = (-sx * HB_FR / 2, 0, 0)
    # singan uchi: ichki yog'och (sariq) tishli bo'lak
    sp = box(f"splinter_{sx}", (0.06, BW * 0.9, BW * 0.9), (0, 0, 0), M["wood_in"]); sp.parent = h; sp.location = (-sx * (HB_FR - 0.02), 0, 0)
    sp.rotation_euler = (0, R(20 * sx), R(10)); halves.append(h)
    key(h, 1, rot=(0, 0, 0)); key(h, BREAK_F, rot=(0, 0, 0))
    key(h, BREAK_F + 5, rot=(0, -sx * 36, 0)); key(h, BREAK_F + 9, rot=(0, -sx * 31, 0)); key(h, BREAK_F + 13, rot=(0, -sx * 33, 0))
for sx in (-1, 1):
    for sy in (-1, 1):
        legsB.append(box("legB", (0.1, 0.1, MZ_B), (TC.x + sx * (HB_FR + 0.06), TC.y + sy * (HB_FR + 0.06), MZ_B / 2 - 0.03), M["wood"]))
for kfb in ((1, 0.0), (BREAK_F, 0.0), (BREAK_F + 5, 1.1), (BREAK_F + 9, 0.94), (BREAK_F + 13, 1.0)):
    kbr.value = kfb[1]; kbr.keyframe_insert("value", frame=kfb[0])
B_RANGE = (S["springs"][0], S["butt"][1])
vis(sheetB, [B_RANGE])
for o in beamsB + legsB + halves: vis(o, [B_RANGE])
# singan yog'ochlar ("steel" kadrida chetda yotadi)
brk = []
for i, (x, y, a) in enumerate(((-3.6, 0.4, 20), (-3.3, 1.1, -35), (-4.0, 1.6, 70), (-3.1, 2.2, 5))):
    brk.append(box("broken_wood", (1.4 if i < 2 else 0.9, BW, BW), (x, y, BW / 2), M["wood"], rot=(0, 0, a)))
for o in brk: vis(o, [(S["steel"][0], END)])

# --- prujina (spiral egri chiziq) ---
L0 = 0.3
def make_spring(name, length=L0, r=0.016, turns=13):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0032; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); pts = []
    hook = 0.03
    pts.append((0, 0, 0)); pts.append((hook, 0, r * 0.3))
    n = turns * 16
    for i in range(n + 1):
        t = i / n; a = 2 * math.pi * turns * t
        pts.append((hook + (length - 2 * hook) * t, r * math.sin(a), r * math.cos(a)))
    pts.append((length, 0, 0))
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1)
    cu.materials.append(M["spring"])
    return cu
spring_data = make_spring("spring")
def spring_obj(name):
    o = bpy.data.objects.new(name, spring_data); sc.collection.objects.link(o); o.rotation_mode = "XYZ"; return o
def aim_spring(o, f, a, b):
    a, b = Vector(a), Vector(b); d = b - a; h = Vector((d.x, d.y, 0)).length
    o.location = a; o.rotation_euler = (0, math.atan2(-d.z, h), math.atan2(d.y, d.x)); o.scale = (d.length / L0, 1, 1)
    for p in ("location", "rotation_euler", "scale"): o.keyframe_insert(p, frame=f)

# B prujinalari: har tomonda 9 ta. (anchor_fn(f) -> rama nuqtasi, edge local (x, y) -> choyshab chekkasi)
springsB = []
for side in range(4):
    for s_ in [(-0.96 + 1.92 * i / 8) for i in range(9)]:
        if side == 0: ex, ey, ax, ay = s_, -HB_IN, s_, -HB_FR      # old (sinadi)
        elif side == 1: ex, ey, ax, ay = s_, HB_IN, s_, HB_FR
        elif side == 2: ex, ey, ax, ay = -HB_IN, s_, -HB_FR, s_
        else: ex, ey, ax, ay = HB_IN, s_, HB_FR, s_
        springsB.append((spring_obj("springB"), side, (ex, ey), (ax, ay)))

# --- C: dumaloq temir batut ---
RC_M, RC_F = 1.46, 1.8              # choyshab radiusi, rama radiusi
PULL_C, EDGE_C = 0.3, 0.2
ring_n, seg_n = 22, 72
vC = [(0.0, 0.0)]
for i in range(1, ring_n + 1):
    rr = RC_M * i / ring_n
    for j in range(seg_n): a = 2 * math.pi * j / seg_n; vC.append((rr * math.cos(a), rr * math.sin(a)))
fC = [(0, 1 + (j + 1) % seg_n, 1 + j) for j in range(seg_n)][::-1]
fC = [(0, 1 + j, 1 + (j + 1) % seg_n) for j in range(seg_n)]
for i in range(ring_n - 1):
    b0, b1 = 1 + i * seg_n, 1 + (i + 1) * seg_n
    for j in range(seg_n): fC.append((b0 + j, b0 + (j + 1) % seg_n, b1 + (j + 1) % seg_n, b1 + j))
matC = dip_mesh("matC", vC, fC, MZ_C, M["jump_mat"], EDGE_C, PULL_C, lambda x, y: math.hypot(x, y) / RC_M)
C_START = S["steel"][0]
vis(matC, [(C_START, END)])
partsC = []
bpy.ops.mesh.primitive_torus_add(major_radius=RC_F, minor_radius=0.032, major_segments=96, minor_segments=12, location=(TC.x, TC.y, MZ_C))
tor = bpy.context.object; tor.name = "frameC"; tor.data.materials.append(M["steel"]); smooth(tor); partsC.append(tor)
for j in range(6):                 # W shaklidagi oyoqlar
    a = 2 * math.pi * j / 6 + R(15); a2 = a + R(30)
    p1 = TC + Vector((RC_F * math.cos(a), RC_F * math.sin(a), MZ_C)); p2 = TC + Vector((RC_F * math.cos(a2), RC_F * math.sin(a2), MZ_C))
    g1 = TC + Vector((RC_F * math.cos(a), RC_F * math.sin(a), 0.02)); g2 = TC + Vector((RC_F * math.cos(a2), RC_F * math.sin(a2), 0.02))
    partsC += [cyl_between("legC", p1, g1, 0.025, M["steel"]), cyl_between("legC", p2, g2, 0.025, M["steel"]),
               cyl_between("footC", g1, g2, 0.025, M["steel"])]
for o in partsC: vis(o, [(C_START, END)])
springsC = []
for j in range(seg_n):
    a = 2 * math.pi * (j + 0.5) / seg_n
    springsC.append((spring_obj("springC"), a))
# yumshoq qoplama (ko'k halqa)
PAD0, PAD1 = S["pad"][0] + 12, S["pad"][0] + 44
rin, rout = RC_M - 0.06, RC_F + 0.14
pv, pf = [], []
for j in range(seg_n):
    a = 2 * math.pi * j / seg_n
    pv += [(rin * math.cos(a), rin * math.sin(a), 0), (rout * math.cos(a), rout * math.sin(a), 0)]
for j in range(seg_n):
    k = (j + 1) % seg_n; pf.append((2 * j, 2 * j + 1, 2 * k + 1, 2 * k))
pad = mesh_obj("pad", pv, pf, M["pad"])
so = pad.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.07; so.offset = 1.0
bv = pad.modifiers.new("bev", "BEVEL"); bv.width = 0.025; bv.segments = 3; bv.limit_method = "ANGLE"
for f, z in ((1, 3.2), (PAD0, 3.2), (PAD1, MZ_C + 0.01), (PAD1 + 4, MZ_C + 0.06), (PAD1 + 8, MZ_C + 0.01)):
    key(pad, f, loc=(TC.x, TC.y, z))
key(pad, PAD0, rot=(4, -3, 0)); key(pad, PAD1, rot=(0, 0, 0))
vis(pad, [(S["pad"][0], END)])
# to'r: 8 ta ustun + to'r silindr
NET0, NET1 = S["net"][0] + 6, S["net"][0] + 44
NH = 1.9
netgrp = []
for j in range(8):
    a = 2 * math.pi * j / 8 + R(11)
    base = TC + Vector(((RC_F + 0.05) * math.cos(a), (RC_F + 0.05) * math.sin(a), MZ_C))
    pole = cyl("net_pole", 0.03, NH, (0, 0, 0), M["sleeve"], verts=12)
    for v in pole.data.vertices: v.co.z += NH / 2
    pole.location = base
    f0 = NET0 + j * 2
    key(pole, 1, scale=(1, 1, 0.001)); key(pole, f0, scale=(1, 1, 0.001)); key(pole, f0 + 14, scale=(1, 1, 1.06)); key(pole, f0 + 18, scale=(1, 1, 1))
    netgrp.append(pole)
bpy.ops.mesh.primitive_cylinder_add(vertices=120, radius=RC_F + 0.04, depth=NH - 0.05, end_fill_type="NOTHING", location=(0, 0, 0))
net = bpy.context.object; net.name = "net"
for v in net.data.vertices: v.co.z += (NH - 0.05) / 2
net.location = (TC.x, TC.y, MZ_C + 0.05)
netm = M["net"]; Nn = netm.node_tree.nodes; Ln = netm.node_tree.links
tcn = Nn.new("ShaderNodeTexCoord"); mx_ = None
waves = []
for ang in (45, -45):
    mpn = Nn.new("ShaderNodeMapping"); mpn.inputs["Rotation"].default_value = (0, 0, 0)
    sep = Nn.new("ShaderNodeSeparateXYZ"); Ln.new(tcn.outputs["Object"], sep.inputs[0])
    # silindr atrofidagi burchak (u) va balandlik (z) bo'yicha diagonal chiziqlar
    at = Nn.new("ShaderNodeMath"); at.operation = "ARCTAN2"; Ln.new(sep.outputs[1], at.inputs[0]); Ln.new(sep.outputs[0], at.inputs[1])
    mu = Nn.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = 1.85 * (1 if ang > 0 else -1); Ln.new(at.outputs[0], mu.inputs[0])
    ad = Nn.new("ShaderNodeMath"); ad.operation = "ADD"; Ln.new(mu.outputs[0], ad.inputs[0]); Ln.new(sep.outputs[2], ad.inputs[1])
    fr_ = Nn.new("ShaderNodeMath"); fr_.operation = "PINGPONG"; fr_.inputs[1].default_value = 0.025; Ln.new(ad.outputs[0], fr_.inputs[0])
    lt = Nn.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.0035; Ln.new(fr_.outputs[0], lt.inputs[0])
    waves.append(lt)
mxn = Nn.new("ShaderNodeMath"); mxn.operation = "MAXIMUM"; Ln.new(waves[0].outputs[0], mxn.inputs[0]); Ln.new(waves[1].outputs[0], mxn.inputs[1])
Ln.new(mxn.outputs[0], Nn["Principled BSDF"].inputs["Alpha"])
net.data.materials.append(netm)
key(net, 1, scale=(1, 1, 0.001)); key(net, NET0 + 10, scale=(1, 1, 0.001)); key(net, NET1, scale=(1, 1, 1))
netgrp.append(net)
bpy.ops.mesh.primitive_torus_add(major_radius=RC_F + 0.04, minor_radius=0.02, major_segments=96, minor_segments=8, location=(TC.x, TC.y, MZ_C + NH))
top = bpy.context.object; top.name = "net_top"; top.data.materials.append(M["sleeve"])
key(top, 1, loc=(TC.x, TC.y, MZ_C + 0.05)); key(top, NET0 + 10, loc=(TC.x, TC.y, MZ_C + 0.05)); key(top, NET1, loc=(TC.x, TC.y, MZ_C + NH))
netgrp.append(top)
for o in netgrp: vis(o, [(S["net"][0], END)])

# ======================================================================
# 4) QAHRAMONLAR
# ======================================================================
def soften(meshes, rough=0.5):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = rough
                    n.inputs["Coat Weight"].default_value = 0.0
def A_(f, inplace=True, novert=False):
    a = mc.load_action(f, inplace); sc.render.fps = 24
    if novert:
        nm = a.name + "_nv"
        if nm in bpy.data.actions: return bpy.data.actions[nm]
        a = a.copy(); a.name = nm; a.use_fake_user = True
        for fc in list(mc._fcurves(a)):
            if fc.data_path == 'pose.bones["mixamorig:Hips"].location' and fc.array_index == 1:
                mc._channelbag_remove(a, fc)
    return a
def strip(arm, act, start, end, speed=1.0, blend=5, bout=5, src=None):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=False)
    ln = (s.action_frame_end - s.action_frame_start) * s.scale
    s.repeat = max(0.05, (end - start) / ln); s.blend_out = bout; s.use_auto_blend = False
    return s

rroot, remy, rmeshes = mc.load_character("remy", "Remy.fbx"); sc.render.fps = 24
broot, bri, bmeshes = mc.load_character("bri", "Brian.fbx"); sc.render.fps = 24
aroot, aj, ameshes = mc.load_character("aj", "Aj.fbx"); sc.render.fps = 24
soften(rmeshes); soften(bmeshes); soften(ameshes, 0.55)
RS, AS = 0.47, 0.72          # Remy 2.1x katta yozilgan; Aj — bola
VS = RS * 2.1                # Remy'da mocap Hips siljishi ~ yarmiga qisqaradi (o'tirishda root'ni qo'shimcha tushiramiz)

# "semiz dumba": Hips/Spine kengligi (COMBINE trek, aksirish.py dagi kabi)
fat = bpy.data.actions.new("remy_fat")
remy.animation_data.action = fat
for bn, s in (("Hips", (1.28, 1.0, 1.3)), ("Spine", (1.2, 1.0, 1.25))):
    pb = remy.pose.bones["mixamorig:" + bn]; pb.scale = s; pb.keyframe_insert("scale", frame=1)
    remy.data.bones["mixamorig:" + bn].inherit_scale = "FULL"
for bn in ("Spine1", "LeftUpLeg", "RightUpLeg"):
    remy.data.bones["mixamorig:" + bn].inherit_scale = "NONE"
remy.animation_data.action = None
for pb in remy.pose.bones: pb.scale = (1, 1, 1)

def place(root, f, loc, rot=0.0, scale=1.0, interp_mode=None):
    root.location = loc; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
    for p in ("location", "rotation_euler", "scale"): root.keyframe_insert(p, frame=f)

G = 9.81
def hop_track(f0, f1, hops, mz, slow=1.0, start_air=None):
    """Batutda sakrash fizikasi: hops = [(apex_h, contact_depth, contact_frames), ...] takrorlanadi.
    Qaytaradi: {kadr: (oyoq z (root), choyshab chuqurligi)}"""
    out = {}; f = f0; i = 0
    while f <= f1:
        h, d, tc = hops[min(i, len(hops) - 1)]
        tc = max(2, int(tc * slow))
        for k in range(tc + 1):
            dep = d * math.sin(math.pi * k / tc); out[f + k] = (mz - dep, dep)
        f += tc
        n = max(2, int(2 * math.sqrt(2 * h / G) * 24 * slow)) if h > 0 else 0
        for k in range(1, n):
            t = k / n; out[f + k] = (mz + 4 * h * t * (1 - t), 0.0)
        f += n; i += 1
    return {k: v for k, v in out.items() if f0 <= k <= f1}

DIP = {}          # kadr -> (ob'ekt, chuqurlik) — choyshab egilishi
def apply_hops(root, track, xy, rot, scale, mat_obj=None, extra_static=0.0):
    for f, (z, dep) in sorted(track.items()):
        root.location = (xy[0], xy[1], z); root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
        for p in ("location", "rotation_euler", "scale"): root.keyframe_insert(p, frame=f)
        if mat_obj is not None: DIP[f] = (mat_obj, dep + extra_static)

# ---------- REMY ----------
FACE_WALL = 180.0
base = mc.add_strip(remy, A_("Happy_Idle.fbx"), -30, blend=0, repeat=20.0)
h0, h1 = S["hook"][0], S["pool"][1]
# 1-2: devor oldida sakraydi (Jump mocap: havoda ~24..40 mocap kadr; o'z sakrashimizni shunga moslaymiz)
JS = 1.0
cyc = 66 * 0.8 / JS
WALLX = (0.35, WALL_Y - 0.75)
jump_s = strip(remy, A_("Jump.fbx", novert=True), h0 - 10, h1 + 2, speed=JS, blend=0)
for f in range(h0 - 10, h1 + 3):
    ph = ((f - (h0 - 10)) % cyc) / 0.8 * JS          # mocap kadri
    z = 0.0
    if 23 <= ph <= 41:
        t = (ph - 23) / 18; z = 0.62 * 4 * t * (1 - t)
    elif ph < 23 and ph > 8:
        z = -0.18 * math.sin(math.pi * (ph - 8) / 15)  # cho'kkalash
    elif 41 < ph < 52:
        z = -0.15 * math.sin(math.pi * (ph - 41) / 11)
    place(rroot, f, (WALLX[0], WALLX[1], z), FACE_WALL, RS)
# 3: cho'kkalab choyshab bog'laydi
SH0, SH1 = S["sheet"]
place(rroot, SH0, (TC.x - 1.25, TC.y - 1.85, -0.02), 40, RS)
strip(remy, A_("Plant_A_Plant.fbx"), SH0 - 4, SH1 + 2, blend=0, src=(60, 228))
# 4: choyshabga sakraydi
J0, J1 = S["jumpon"]
place(rroot, J0, (TC.x, TC.y - 2.2, 0), FACE_WALL, RS)
tr = {}
for f in range(J0, J0 + 9): tr[f] = (0.0 - 0.12 * math.sin(math.pi * (f - J0) / 9), 0.0)          # cho'kkalash
FL = 16
for k in range(FL + 1):                                               # yerdan choyshabga uchish
    t = k / FL; tr[J0 + 9 + k] = ((1 - t) * 0.0 + t * MZ_A + 0.9 * 4 * t * (1 - t), 0.0)
land = J0 + 9 + FL
tr.update(hop_track(land, J1 + 4, [(0.04, 0.62, 16), (0.03, 0.5, 14), (0.02, 0.45, 12)], MZ_A))
for f, (z, dep) in sorted(tr.items()):
    t = min(1.0, max(0.0, (f - J0 - 9) / FL))
    place(rroot, f, (TC.x, TC.y - 2.2 * (1 - ease(t)), z), FACE_WALL, RS); DIP[f] = (sheetA, dep)
strip(remy, A_("Jump.fbx", novert=True), J0 - 14, land + 6, blend=3, src=(1, 45))
strip(remy, A_("Joyful_Jump.fbx", novert=True), land + 2, J1 + 2, speed=1.0, blend=4)
# 5: deyarli sakramaydi — hafsalasi pir
M0, M1 = S["meh"]
apply_hops(rroot, hop_track(M0, M1, [(0.04, 0.42, 14)], MZ_A), (TC.x, TC.y), FACE_WALL, RS, sheetA)
strip(remy, A_("Disappointed.fbx"), M0 - 4, M1 + 2, blend=4)
# 6: devor o'sadi — choyshabda turib (egilgan), jahli chiqadi
W0s, W1s = S["wall"]
for f in range(W0s, W1s + 1, 2):
    place(rroot, f, (TC.x, TC.y, MZ_A - 0.36), FACE_WALL, RS); DIP[f] = (sheetA, 0.36)
strip(remy, A_("Angry.fbx"), W0s - 4, W1s + 2, blend=4, src=(40, 400))
# 7: prujina ulaydi (cho'kkalab, old chekkada)
P0, P1 = S["springs"]
place(rroot, P0, (TC.x + 1.95, TC.y - HB_FR - 0.45, -0.02), -135, RS)
strip(remy, A_("Plant_A_Plant.fbx"), P0 - 4, P1 + 2, blend=0, src=(70, 228))
# 8: "Dahaa!" — batut ustida qo'llarini ko'taradi
D0, D1 = S["daha"]
for f in range(D0, D1 + 1, 2):
    place(rroot, f, (TC.x, TC.y - 0.2, MZ_B - 0.16), 15, RS); DIP[f] = (sheetB, 0.16)
strip(remy, A_("Cheering.fbx"), D0 - 2, D1 + 3, blend=2, src=(10, 427))
# 9: qo'nganda prujinalar cho'ziladi (sekinlashtirilgan)
T0, T1 = S["stretch"]
apply_hops(rroot, hop_track(T0, T1, [(0.25, 0.42, 12)], MZ_B, slow=1.8), (TC.x, TC.y - 0.55), FACE_WALL, RS, sheetB)
strip(remy, A_("Joyful_Jump.fbx", novert=True), T0 - 4, T1 + 2, speed=0.6, blend=4)
# 10: baland otiladi
L0s, L1s = S["launch"]
apply_hops(rroot, hop_track(L0s - 6, L1s, [(0.0, 0.5, 14), (2.4, 0.55, 12), (1.0, 0.4, 10)], MZ_B), (TC.x, TC.y), FACE_WALL, RS, sheetB)
strip(remy, A_("Jump.fbx", novert=True), L0s - 8, L0s + 12, blend=0, src=(10, 40))
strip(remy, A_("Falling_Idle.fbx"), L0s + 10, L1s + 2, blend=5)
# 11: dumbasi bilan tushadi, old to'sin sinadi
B0, B1 = S["butt"]
SIT_FIX = -0.40 * (1 - VS) - 0.05     # Sitting_Idle_5 hips -40 sm (Remy'da yarmi): yetishmaganini root bilan
BX, BY = TC.x, TC.y - 0.55
fall0 = B0 + 6
tr = {}
for f in range(B0, BREAK_F - 14):                 # havoda: o'tirgan holatda pastga tushmoqda
    t = (f - B0) / (BREAK_F - 14 - B0); tr[f] = (MZ_B + 2.4 * (1 - t * t) + SIT_FIX + 0.25, 0.0)
for f in range(BREAK_F - 14, BREAK_F + 1):        # qo'nadi, choyshab chuqur egiladi
    t = (f - (BREAK_F - 14)) / 14
    dep = 0.55 * ease(min(1, max(0, (t - 0.25) / 0.75)))
    tr[f] = (MZ_B + SIT_FIX - dep + (1 - min(1, t / 0.3)) * 0.45, dep)
for f in range(BREAK_F + 1, B1 + 1):              # rama sinadi: yerga tushib o'tirib qoladi
    t = min(1, (f - BREAK_F) / 6)
    z = (MZ_B + SIT_FIX - 0.55) * (1 - t) + (-0.48 + 0.14) * t
    tr[f] = (z, 0.55 * (1 - t) + 0.35 * t)
for f, (z, dep) in sorted(tr.items()):
    place(rroot, f, (BX, BY, z), FACE_WALL, RS); DIP[f] = (sheetB, dep)
strip(remy, A_("Falling_Idle.fbx"), B0 - 4, B0 + 10, blend=0)
strip(remy, A_("Sitting_Idle_5.fbx"), B0 + 4, B1 + 2, blend=8)
# 12: temir batut yonida mag'rur turadi
E0, E1 = S["steel"]
place(rroot, E0, (TC.x + 2.35, TC.y - 1.25, 0), -60, RS)
strip(remy, A_("Happy_Idle.fbx"), E0 - 2, E1 + 2, blend=0)
# 13: temir batutda baland sakraydi
Q0, Q1 = S["bounce"]
apply_hops(rroot, hop_track(Q0, Q1, [(1.4, 0.5, 10)], MZ_C), (TC.x - 0.2, TC.y - 0.3), FACE_WALL, RS, matC)
strip(remy, A_("Joyful_Jump.fbx", novert=True), Q0 - 4, Q1 + 2, speed=0.55, blend=4)
# 14: oyog'i prujinalar orasiga tiqiladi
K0, K1 = S["stuck"]
SY = -(RC_M + RC_F) / 2
tr = {}
for f in range(K0, STUCK_F): t = (f - K0) / (STUCK_F - K0); tr[f] = (MZ_C + 0.9 * (1 - t * t), 0.0)
for f in range(STUCK_F, K1 + 1):
    t = min(1, (f - STUCK_F) / 3); tr[f] = (MZ_C - 0.5 * t + 0.03 * math.sin((f - STUCK_F) * 1.3) * (1 - t), 0.0)
for f, (z, d) in sorted(tr.items()): place(rroot, f, (TC.x + 0.08, TC.y + SY + 0.02, z), 0, RS)
strip(remy, A_("Falling_Idle.fbx"), K0 - 2, STUCK_F + 1, blend=0)
strip(remy, A_("Injured_Hurting_Idle.fbx"), STUCK_F - 1, K1 + 2, blend=3)
# 15-18: yonda turib kuzatadi
Y0, Y1 = S["pad"][0], S["net"][1]
place(rroot, Y0, (TC.x + 2.55, TC.y - 0.9, 0), -70, RS)
strip(remy, A_("Happy_Idle.fbx"), Y0 - 2, S["kid"][0] + 2, blend=0)
strip(remy, A_("Thinking.fbx"), S["kid"][0], S["flyoff"][0] + 4, blend=4)
strip(remy, A_("Excited.fbx"), S["net"][0] - 2, Y1 + 2, blend=4)
# 19: to'r ichida juda baland — devor ustidan qaraydi, qo'l silkitadi
F0, F1 = S["final"]
ftr = hop_track(F0 - 8, F1, [(0.0, 0.5, 12), (1.2, 0.45, 14), (4.0, 0.62, 16), (0.0, 0.5, 30)], MZ_C)
apply_hops(rroot, ftr, (TC.x, TC.y + 0.2), FACE_WALL, RS, matC)
APEX = max((z, f) for f, (z, d) in ftr.items())[1]
strip(remy, A_("Jump.fbx", novert=True), F0 - 10, F0 + 10, blend=0, src=(10, 40))
strip(remy, A_("Waving_2.fbx"), F0 + 8, F1 + 2, blend=6)
interp(rroot, "LINEAR")
for fc in fcurves(rroot):          # kadrlar orasida sakrab o'tish (joy almashganda)
    if fc.data_path in ("rotation_euler", "scale"):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
for fc in fcurves(rroot):
    if fc.data_path == "location":
        cuts = {f for f, n in SHOTS}
        for k in fc.keyframe_points:
            nxt = int(k.co.x) + 1
            if nxt in cuts or int(k.co.x) + 2 in cuts: k.interpolation = "CONSTANT"
# semiz trek (eng ustida)
trf = remy.animation_data.nla_tracks.new(); trf.name = "fat"
sf = trf.strips.new("fat", 1, fat)
if hasattr(sf, "action_slot") and fat.slots: sf.action_slot = fat.slots[0]
sf.blend_type = "COMBINE"; sf.extrapolation = "HOLD"; sf.frame_end = END

# ---------- BRIAN (basseynda) ----------
BPOS = (0.6, 9.2)
place(broot, 1, (BPOS[0], BPOS[1], WZ - 1.33), -8)
mc.add_strip(bri, A_("Treading_Water.fbx"), -20, blend=0, repeat=20.0)

# ---------- AJ (jiyan) ----------
K_0, K_1 = S["kid"]; FO0, FO1 = S["flyoff"]
atr = hop_track(K_0 - 6, FO0 + 4, [(0.7, 0.35, 9)], MZ_C)
apply_hops(aroot, atr, (TC.x + 0.3, TC.y - 0.2), 20, AS, matC)
LAST = max(f for f, (z, d) in atr.items() if d > 0 and f <= FO0 + 4) if any(d > 0 for z, d in atr.values()) else FO0
# so'nggi zarbadan keyin chetdan uchib ketadi (yoy), butaga tushadi
p0 = Vector((TC.x + 0.3, TC.y - 0.2, MZ_C)); p1 = Vector((TC.x + 2.6, TC.y - 4.4, 0.25))
lastc = max(f for f, (z, d) in atr.items())
for f in range(lastc + 1, FO1 + 4):
    t = min(1.0, (f - lastc) / 30.0)
    p = p0.lerp(p1, t); p.z = p0.z * (1 - t) + p1.z * t + 2.2 * 4 * t * (1 - t)
    aroot.location = p; aroot.rotation_euler = (R(-50 * t), R(25 * t), R(20 - 140 * t)); aroot.scale = (AS,) * 3
    for pth in ("location", "rotation_euler", "scale"): aroot.keyframe_insert(pth, frame=f)
interp(aroot, "LINEAR")
mc.add_strip(aj, A_("Happy_Idle.fbx"), -20, blend=0, repeat=40.0)
strip(aj, A_("Joyful_Jump.fbx", novert=True), K_0 - 10, lastc + 2, speed=0.8, blend=2)
strip(aj, A_("Floating.fbx"), lastc - 2, FO1 + 3, speed=1.6, blend=3)
vis(aroot, [(K_0, FO1)]);
for o in ameshes: vis(o, [(K_0, FO1)], recursive=False)
butaK = shrub_blob(TC.x + 2.7, TC.y - 4.6, 0.9)

# Remy ko'rinishi: hamma kadrda
# ======================================================================
# 5) CHOYSHAB EGILISHI va PRUJINALAR (kadrma-kadr)
# ======================================================================
for o in (sheetA, sheetB, matC): key_dip(o, 1, 0.0)
last_obj = None
for f in sorted(DIP):
    o, d = DIP[f]
    for oo in (sheetA, sheetB, matC):
        key_dip(oo, f, d if oo is o else 0.0)
for o in (sheetA, sheetB, matC):
    for fc in o.data.shape_keys.animation_data.action and mc._fcurves(o.data.shape_keys.animation_data.action) or []:
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
if os.environ.get("EVENTS"):                 # tovush effektlari uchun: choyshabga tegish kadrlari
    import json
    ev = []; prev_d = 0.0
    for f in range(1, END + 1):
        d = DIP[f][1] if f in DIP else 0.0
        if d > 0.02 and prev_d <= 0.02: ev.append([f, DIP[f][0].name, round(max(DIP.get(f + k, (None, 0))[1] for k in range(12)), 2)])
        prev_d = d
    json.dump(ev, open(os.environ["EVENTS"], "w"))
def dip_at(o, f):
    sc.frame_set(f); return o.data.shape_keys.key_blocks["dip"].value

def mat_edge_world(o, lx, ly, d, pull, edge, rho_edge=1.0, extra_z=0.0):
    n = Vector((lx, ly, 0)).normalized()
    p = Vector((lx, ly, 0)) - n * pull * d * rho_edge + Vector((0, 0, -edge * d + extra_z))
    return o.matrix_world @ Vector((p.x, p.y, p.z)) if False else Vector((o.location.x + p.x, o.location.y + p.y, o.location.z + p.z))

# B prujinalari: paydo bo'lish ("springs" kadri), cho'zilish, sinish
SP_APPEAR = {}
order = sorted(range(len(springsB)), key=lambda i: (springsB[i][1] != 0, springsB[i][2][0]))
for n_, i in enumerate(order):
    SP_APPEAR[i] = P0 + 10 + int(n_ * 0.9) if springsB[i][1] == 0 else P0 + 10 + int(9 * 6.5) + (n_ - 9) // 3
kv = sheetB.data.shape_keys.key_blocks
for f in range(B_RANGE[0], B_RANGE[1] + 1):
    sc.frame_set(f)
    d = kv["dip"].value; br = kv["broken"].value
    ang = [h.rotation_euler.y for h in halves]
    for i, (o, side, (ex, ey), (ax, ay)) in enumerate(springsB):
        e = Vector((TC.x + ex, TC.y + ey, MZ_B))
        nrm = Vector((ex if side >= 2 else 0, ey if side < 2 else 0, 0)).normalized()
        e = e - nrm * PULL_B * d + Vector((0, 0, -EDGE_B * d))
        a = Vector((TC.x + ax, TC.y + ay, MZ_B - 0.005))
        if side == 0:
            drop = beam_drop(ax) * br * 0.92
            e.z -= drop
            hs = 0 if ax < 0 else 1
            th = abs(ang[hs]); a.z -= (HB_FR - abs(ax)) * math.sin(th); a.x = TC.x + math.copysign(HB_FR - (HB_FR - abs(ax)) * math.cos(th), ax)
        if f < SP_APPEAR[i]:
            a2 = a.lerp(e, 0.999)
            aim_spring(o, f, a, a2); o.scale = (0.001, 0.001, 0.001); o.keyframe_insert("scale", frame=f)
        else:
            aim_spring(o, f, a, e)
for o, *_ in springsB:
    vis(o, [B_RANGE], recursive=False)
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
# C prujinalari
kvC = matC.data.shape_keys.key_blocks
for f in range(C_START, END + 1):
    sc.frame_set(f); d = kvC["dip"].value
    if f > C_START and abs(d - prev) < 1e-5 and f not in DIP:
        prev = d; continue
    prev = d
    for o, a_ in springsC:
        c, s_ = math.cos(a_), math.sin(a_)
        a = Vector((TC.x + RC_F * c, TC.y + RC_F * s_, MZ_C))
        rr = RC_M - PULL_C * d
        e = Vector((TC.x + rr * c, TC.y + rr * s_, MZ_C - EDGE_C * d))
        aim_spring(o, f, a, e)
for o, _ in springsC:
    vis(o, [(C_START, END)], recursive=False)
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"

# ======================================================================
# 6) KAMERALAR (har kadrda harakatda)
# ======================================================================
headR = child_of_bone("remy_head", remy, "Head")
hipsR = child_of_bone("remy_hips", remy, "Hips")
hipsA = child_of_bone("aj_hips", aj, "Hips")
headB = child_of_bone("bri_head", bri, "Head")
def T(name, pts):
    t = empty("t_" + name); path_keys(t, pts); return t
TCz = lambda dx, dy, z: (TC.x + dx, TC.y + dy, z)

# 1 hook: past burchak, Remy ortidan devor tepasiga, tez push-in
a, b = S["hook"]
c = shot_cam("hook", (0, 0, 0), T("hook", [(a, (0.15, 6.2, 1.5)), (b, (0.3, 6.0, 1.85))]), 14, 4.0)
path_keys(c, [(a, (1.9, 2.4, 0.22)), (b, (1.05, 3.9, 0.4))])
# 2 pool: kran — basseyndagi do'stdan devor ustiga (Remy boshi ko'rinadi)
a, b = S["pool"]
c = shot_cam("pool", (0, 0, 0), T("pool", [(a, (0.6, 9.2, WZ + 0.2)), (a + 20, (0.6, 8.6, 0.4)), (b, (0.35, 5.95, 2.1))]), 18, 5.6)
path_keys(c, [(a, (3.6, 12.6, 3.4)), (b, (1.6, 9.6, 3.0))])
# 3 sheet: past aylanma
a, b = S["sheet"]
c = shot_cam("sheet", (0, 0, 0), T("sheet", [(a, TCz(-0.4, -0.6, 0.4)), (b, TCz(0, 0, 0.7))]), 15, 5.6)
orbit(c, a, b, TC, 3.6, 3.2, -55, -15, 0.35, 0.75)
# 4 jumpon: yon tomondan, past
a, b = S["jumpon"]
c = shot_cam("jumpon", (0, 0, 0), T("jumpon", [(a, TCz(0, -1.8, 1.0)), (a + 26, TCz(0, -0.4, 1.4)), (b, TCz(0, 0, 0.9))]), 17, 5.6)
path_keys(c, [(a, TCz(3.6, -1.6, 0.3)), (b, TCz(3.1, -0.6, 0.4))])
# 5 meh: yuzga yaqin (Remy devorga qaraydi -> kamera devor tomonda), DOF
a, b = S["meh"]
fr = follow("t_meh", headR, a, b, (0, 0.02, 0.02), step=2)
c = shot_cam("meh", (0, 0, 0), fr, 55, 2.0)
path_keys(c, [(a, TCz(0.55, 1.45, 1.75)), (b, TCz(0.35, 1.15, 1.7))])
# 6 wall: devor tagidan tepaga
a, b = S["wall"]
c = shot_cam("wall", (0, 0, 0), T("wall", [(a, (0.8, WALL_Y, 1.6)), (W0, (0.8, WALL_Y, 2.2)), (W1, (0.8, WALL_Y, 3.5)), (b, (0.8, WALL_Y, 3.6))]), 13, 8.0)
path_keys(c, [(a, (-2.4, 4.4, 0.25)), (b, (-1.9, 4.8, 0.3))])
# 7 springs: makro, old chekka bo'ylab
a, b = S["springs"]
c = shot_cam("springs", (0, 0, 0), T("springs", [(a, TCz(-0.95, -1.3, MZ_B)), (b, TCz(0.9, -1.3, MZ_B))]), 26, 2.8)
path_keys(c, [(a, TCz(-1.35, -2.3, MZ_B + 0.55)), (b, TCz(0.4, -2.35, MZ_B + 0.6))])
# 8 daha: crash zoom (yaqindan uzoqqa) + chaqnash
a, b = S["daha"]
c = shot_cam("daha", (0, 0, 0), T("daha", [(a, TCz(0, -0.2, 1.7)), (b, TCz(0, -0.1, 1.3))]), 16, 5.6)
path_keys(c, [(a, TCz(0.5, -1.7, 0.6)), (a + 6, TCz(1.2, -3.8, 0.45)), (b, TCz(1.4, -4.6, 0.45))])
# 9 stretch: makro — prujinalar va qo'nayotgan oyoqlar
a, b = S["stretch"]
c = shot_cam("stretch", (0, 0, 0), T("stretch", [(a, TCz(-0.15, -1.1, MZ_B + 0.05)), (b, TCz(0.15, -1.0, MZ_B + 0.15))]), 22, 3.5)
path_keys(c, [(a, TCz(-0.85, -2.35, MZ_B + 0.12)), (b, TCz(-0.45, -2.3, MZ_B + 0.25))])
# 10 launch: yer sathidan, Remy'ga ergashib tepaga
a, b = S["launch"]
fr = follow("t_launch", hipsR, a, b, (0, 0, 0.2), step=2)
c = shot_cam("launch", (0, 0, 0), fr, 14, 8.0)
path_keys(c, [(a, TCz(1.3, -2.8, 0.15)), (b, TCz(1.0, -2.4, 0.2))])
# 11 butt: yon tomondan, sinishda silkinish
a, b = S["butt"]
c = shot_cam("butt", (0, 0, 0), T("butt", [(a, TCz(0, -0.6, 1.8)), (BREAK_F - 10, TCz(0, -0.8, 0.9)), (b, TCz(0, -0.9, 0.5))]), 18, 5.6)
path_keys(c, [(a, TCz(2.9, -2.5, 1.0)), (BREAK_F, TCz(2.4, -2.2, 0.7)), (b, TCz(2.2, -2.0, 0.55))])
shake(c, BREAK_F, BREAK_F + 14, 0.07, 3)
# 12 steel: kran aylanma
a, b = S["steel"]
c = shot_cam("steel", (0, 0, 0), T("steel", [(a, TCz(0, 0, 0.6)), (b, TCz(0.6, -0.4, 0.8))]), 18, 8.0)
orbit(c, a, b, TC, 5.6, 4.4, -70, -25, 3.8, 0.8)
# 13 bounce: yon, keng, past
a, b = S["bounce"]
fr = follow("t_bounce", hipsR, a, b, (0, 0, 0.0), step=2, lerp=(TCz(0, 0, 1.6), lambda f: 0.55))
c = shot_cam("bounce", (0, 0, 0), fr, 15, 8.0)
path_keys(c, [(a, TCz(4.3, -2.2, 0.3)), (b, TCz(3.8, -1.4, 0.35))])
# 14 stuck: past yaqin, silkinish
a, b = S["stuck"]
c = shot_cam("stuck", (0, 0, 0), T("stuck", [(a, TCz(0.05, SY, 1.3)), (STUCK_F + 2, TCz(0.05, SY, 0.75)), (b, TCz(0.05, SY, 0.85))]), 20, 4.0)
path_keys(c, [(a, TCz(0.9, SY - 1.5, 0.6)), (STUCK_F, TCz(0.75, SY - 1.25, 0.4)), (b, TCz(0.6, SY - 1.05, 0.32))])
shake(c, STUCK_F, STUCK_F + 12, 0.05, 5)
# 15 pad: tepadan aylanma
a, b = S["pad"]
c = shot_cam("pad", (0, 0, 0), T("pad", [(a, TCz(0, 0, 0.8)), (b, TCz(0, 0, 0.8))]), 16, 11.0)
for f in range(a, b + 1, 2):
    t = (f - a) / (b - a); ang = R(-20 + 70 * t)
    key(c, f, loc=TCz(1.1 * math.sin(ang) + 0.0, -1.1 * math.cos(ang) - 2.2 * (1 - t), 6.8 - 1.2 * t))
# 16 kid: keng past
a, b = S["kid"]
c = shot_cam("kid", (0, 0, 0), T("kid", [(a, TCz(0.4, 0, 1.4)), (b, TCz(0.6, -0.4, 1.6))]), 16, 8.0)
path_keys(c, [(a, TCz(-3.4, -2.8, 0.45)), (b, TCz(-2.8, -2.5, 0.55))])
# 17 flyoff: whip — jiyanga ergashadi
a, b = S["flyoff"]
fr = follow("t_flyoff", hipsA, a, b, (0, 0, 0), step=1)
c = shot_cam("flyoff", (0, 0, 0), fr, 16, 8.0)
path_keys(c, [(a, TCz(4.6, -1.2, 1.1)), (b, TCz(4.9, -2.4, 0.8))])
# 18 net: aylanma
a, b = S["net"]
c = shot_cam("net", (0, 0, 0), T("net", [(a, TCz(0, 0, 1.0)), (b, TCz(0, 0, 1.6))]), 15, 8.0)
orbit(c, a, b, TC, 4.8, 4.3, 25, 75, 0.35, 1.3)
# 19 final: Remy bilan birga ko'tarilib devordan oshadi — basseyndagi do'st
a, b = S["final"]
fr = follow("t_final_r", hipsR, a, b, (0, 0, 0.4), step=2)
tf = empty("t_final")
for f in range(a, b + 1, 2):
    sc.frame_set(f)
    t = ease(min(1, max(0, (f - (APEX - 26)) / 30)))
    p = fr.matrix_world.translation.lerp(Vector((BPOS[0], BPOS[1], WZ + 0.3)), t * 0.5)
    key(tf, f, loc=tuple(p))
c = shot_cam("final", (0, 0, 0), tf, 17, 8.0)
for f in range(a, b + 1, 2):
    sc.frame_set(f); hz = hipsR.matrix_world.translation.z
    key(c, f, loc=TCz(0.9, -2.2 + 0.4 * (f - a) / (b - a), max(0.5, hz * 0.95 + 0.3 + 0.5 * max(0, hz - 2.0) / 3.0)))
for n, c in CAMS.items():
    interp(c, "LINEAR", "location")
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 7) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mpw = N.new("ShaderNodeMapping"); tcw = N.new("ShaderNodeTexCoord"); mpw.inputs["Rotation"].default_value = (0, 0, R(200))
L.new(tcw.outputs["Generated"], mpw.inputs[0]); L.new(mpw.outputs[0], env.inputs[0])
L.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.data.angle = R(1.5); sun.data.color = (1.0, 0.93, 0.82)
sun.rotation_euler = (R(42), 0, R(-35))
def flash(name, loc, f, e=400):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.location = loc; l.data.shadow_soft_size = 0.5
    for ff, v in ((1, 0), (f - 1, 0), (f, e), (f + 3, e * 0.2), (f + 7, 0)):
        l.data.energy = v; l.data.keyframe_insert("energy", frame=ff)
flash("fl_daha", TCz(0.4, -2.0, 1.8), S["daha"][0] + 1, 900)
flash("fl_break", TCz(1.5, -2.0, 1.2), BREAK_F + 1, 700)
flash("fl_stuck", TCz(0.6, SY - 1.0, 1.0), STUCK_F + 1, 500)

# ======================================================================
# 8) RENDER
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
