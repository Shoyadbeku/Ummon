# "Oshqozon nega o'zini hazm qilmaydi?" — Zack D. Films uslubida 33 s video (792 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, magnit/magnit.py (xona, rentgen organlar), burish/parts.py. Kadr rejasi: STORYBOARD.md
# Assetlar: zack_test/tools/get_oshqozon.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/oshqozon/oshqozon.py --render
# Sinov: FRAMES=20,50,100,250,350,560,690,780 PCT=30
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
END = 792
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (32, "xacid"), (69, "blade"), (135, "think"), (169, "xwall"), (216, "cave"), (276, "mucus"),
         (312, "armor"), (388, "erode"), (469, "days"), (520, "regrow"), (613, "xshield"), (659, "clock"), (709, "digest"),
         (750, "final")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
XSW = 769                                    # final kadrida rentgenga o'tish (32.0 s)
IMPACT = 92                                  # tig' kislotaga tushadi ("lezvieni", 3.82 s)
ZIRH = 334                                   # "zirhli" (13.88 s)
STOP = 686                                   # "to'xtab" (28.54 s)

# ---------------- yordamchilar (magnit.py dan) ----------------
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
    l.visible_camera = False                 # Blender 5: POINT chiroq kameraga oq shar bo'lib ko'rinadi
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

def glow_mat(name, col, strength=3.0, alpha=1.0):
    """emissiya + shaffoflik (kislota tomchilari, zarralar)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    if alpha < 1.0:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha
        L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    else:
        L.new(em.outputs[0], out.inputs[0])
    return m

def acid_mat(name, strength=1.4, alpha=0.55, scale=8.0):
    """yashil kislota: qaynayotgan (4D noise, W kalitlanadi) emissiya + yaltiroq + shaffof"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; out = N["Material Output"]
    b.inputs["Base Color"].default_value = (0.25, 0.9, 0.08, 1); b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 1.0
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 4; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    nz.name = "boil"
    for f, w in ((1, 0.0), (END, 60.0)):
        nz.inputs["W"].default_value = w; nz.inputs["W"].keyframe_insert("default_value", frame=f)
    interp(m.node_tree, "LINEAR")
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.1, 0.55, 0.02, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (0.75, 1.0, 0.2, 1)
    L.new(cr.outputs[0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha
    L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m

ROOM_SHOTS = rng("hook", "think", "days", "clock") + [(S["final"][0], XSW - 1)]
X_SHOTS = rng("xacid", "xwall", "xshield") + [(XSW, END)]
LAB_SHOTS = rng("blade")
CAVE_SHOTS = rng("cave")
SEC_SHOTS = rng("mucus", "armor", "erode", "regrow", "digest")

# ======================================================================
# 1) MEHMONXONA (0,0,0) — magnit.py dagi xona + devor soati
# ======================================================================
room = empty("room", (0, 0, 0))
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.4, tint=(0.93, 0.86, 0.76))
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
cr.color_ramp.elements[0].color = (0.55, 0.18, 0.12, 1); cr.color_ramp.elements[1].color = (0.85, 0.7, 0.5, 1)
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
plane("rug", (2.6, 1.8), (0.1, 0.7, 0.004), rug_m, parent=room)
sofaR = empty("sofaR", (0, 1.85, 0), room); import_gltf(PH + "Sofa_01/Sofa_01.gltf", sofaR)
sofaR.scale = (1.15, 1.15, 1.0)
tableR = empty("tableR", (0, 0.85, 0), room); tableR.rotation_euler = (0, 0, R(90))
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", tableR)
plantR = empty("plantR", (-1.55, 1.85, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR)
plantR2 = empty("plantR2", (1.6, 1.95, 0), room); plantR2.scale = (0.8, 0.8, 0.8); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR2)
picR = empty("picR", (0.0, 2.24, 1.55), room); picR.scale = (1.6, 1.6, 1.6); import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR)
picR2 = empty("picR2", (-0.9, 2.24, 1.35), room); import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR2)
lamp_m = mat("lamp_shade", (1.0, 0.85, 0.6), 0.6, emit=2.5, emit_col=(1.0, 0.75, 0.45))
cyl("lamp_pole", 0.015, 1.5, (1.05, 1.9, 0.75), mat("lamp_pole_m", (0.1, 0.1, 0.1), 0.3, metal=0.8), parent=room)
cyl("lamp_shade", 0.18, 0.28, (1.05, 1.9, 1.55), lamp_m, parent=room)
cyl("lamp_base", 0.14, 0.03, (1.05, 1.9, 0.015), mat("lamp_base_m", (0.1, 0.1, 0.1), 0.3, metal=0.8), parent=room)
# devor soati (o'ng tomonda, orqa devorda)
CLK = Vector((1.8, 2.205, 1.85))
CR = 0.17
cyl("clk_rim", CR + 0.018, 0.05, tuple(CLK), mat("clk_rim_m", (0.03, 0.03, 0.035), 0.3, metal=0.6), rot=(90, 0, 0), parent=room, verts=64)
cyl("clk_face", CR, 0.052, tuple(CLK + Vector((0, -0.001, 0))), mat("clk_face_m", (0.92, 0.91, 0.86), 0.5), rot=(90, 0, 0), parent=room, verts=64)
cyl("clk_glass", CR, 0.004, tuple(CLK + Vector((0, -0.048, 0))), mat("clk_glass_m", (0.9, 0.95, 1.0), 0.02, alpha=0.08, coat=1.0), rot=(90, 0, 0), parent=room, verts=64)
tick_m = mat("clk_tick", (0.03, 0.03, 0.03), 0.4)
for i in range(60):
    a = i * math.pi / 30; big = i % 5 == 0
    l_ = 0.026 if big else 0.01
    rr = CR - 0.016 - l_ / 2
    box("clk_tick", (0.007 if big else 0.0025, 0.004, l_), tuple(CLK + Vector((rr * math.sin(a), -0.027, rr * math.cos(a)))),
        tick_m, rot=(0, math.degrees(a), 0), parent=room)
def hand(name, length, width, col, back=0.02, dy=0.0):
    piv = empty(name + "_piv", tuple(CLK + Vector((0, -0.03 - dy, 0))))
    bm = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, bm); sc.collection.objects.link(o); o.parent = piv
    w = width / 2; t = 0.002
    vs = [(-w, -t, -back), (w, -t, -back), (w * 0.6, -t, length), (-w * 0.6, -t, length),
          (-w, t, -back), (w, t, -back), (w * 0.6, t, length), (-w * 0.6, t, length)]
    fs = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    bm.from_pydata(vs, [], fs); bm.update(); bm.materials.append(mat(name + "_m", col, 0.35, metal=0.3))
    return piv
hpiv = hand("clk_hour", 0.085, 0.012, (0.02, 0.02, 0.02))
mpiv = hand("clk_min", 0.135, 0.008, (0.02, 0.02, 0.02), dy=0.003)
spiv = hand("clk_sec", 0.145, 0.0025, (0.8, 0.05, 0.03), back=0.04, dy=0.006)
cyl("clk_cap", 0.008, 0.012, tuple(CLK + Vector((0, -0.04, 0))), mat("clk_cap_m", (0.7, 0.05, 0.03), 0.3, metal=0.5), rot=(90, 0, 0), parent=room)
CL0, CL1 = S["clock"]
def clock_angles(f):
    """(soat, minut, sekund) burchaklari (gradus, +Y atrofida = soat yo'nalishi)"""
    base_m = 60.0; base_h = 300.0
    if f <= CL0: return base_h, base_m, 0.0
    tt = min(f, STOP) - CL0
    m = base_m + 360.0 * (tt / 6.0) ** 1.35 * 1.0      # tezlashib aylanadi
    return base_h + (m - base_m) / 12.0, m, m * 4.0
for f in list(range(CL0 - 1, STOP + 1)) + [STOP + 2, STOP + 4, STOP + 7, END]:
    h_, m_, s_ = clock_angles(f)
    jolt = {STOP + 2: 9.0, STOP + 4: -4.0, STOP + 7: 1.0}.get(f, 0.0)
    for piv, a in ((hpiv, h_), (mpiv, m_ + jolt), (spiv, s_ + jolt * 2)):
        piv.rotation_euler = (0, R(a), 0); piv.keyframe_insert("rotation_euler", frame=f)
for piv in (hpiv, mpiv, spiv):
    interp(piv, "LINEAR")
    piv.parent = room
TABLE_Z = 0.395
vis(room, ROOM_SHOTS)

# ======================================================================
# 2) MEGAN
# ======================================================================
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
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
def A_(f):
    a = mc.load_action(f, True); sc.render.fps = 24; return a

STAND = (0.75, 1.05, 0.0); STAND_ROT = -12
SOFA = (0, 1.66, -0.02)
def place(root, f, loc, rot=0.0, scale=1.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
    for p in ("location", "rotation_euler", "scale"): root.keyframe_insert(p, frame=f)
DA0, DA1 = S["days"]
place(mroot, 1, STAND, rot=STAND_ROT)
place(mroot, DA0, SOFA, rot=0)
place(mroot, DA1 + 1, STAND, rot=STAND_ROT)
interp(mroot, "CONSTANT")

def strip(arm, act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
mc.add_strip(meg, A_("Breathing_Idle.fbx"), -60, blend=0, repeat=6.0)
TH0, TH1 = S["think"]
strip(meg, A_("Thinking.fbx"), TH0 - 26, blend=0, bout=0)
strip(meg, A_("Sitting_Idle_3.fbx"), DA0 - 4, blend=0, bout=0, repeat=2.0)
FI0, FI1 = S["final"]
strip(meg, A_("Big_Stomach_Hit.fbx"), FI0 - 14, src=(1, 60), speed=0.45, blend=0, bout=0)
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.09, 0.08), headE)
hipsE = child_of_bone("meg_hips", meg, "Hips")

# ---- rentgen nusxa + organlar (Hips fazosi: X chap, Y tepa, Z old) ----
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.2, base=0.012)
ghosts = []
for o in mmeshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, X_SHOTS, recursive=False)
MEG_ON = rng("hook", "think", "days", "clock") + [(S["final"][0], XSW - 1)]
for o in mmeshes: vis(o, MEG_ON, recursive=False)
org = empty("organs", (0, 0, 0), hipsE)
def organ_mat(name, col, emit=0.35, transp=0.5):
    m = mat(name, col, 0.3, sss=0.4, sss_scale=0.005, coat=0.8, emit=emit)
    nm = m.node_tree.nodes; L_ = m.node_tree.links; b = nm["Principled BSDF"]
    lw = nm.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    mm_ = nm.new("ShaderNodeMath"); mm_.operation = "MULTIPLY"; mm_.inputs[1].default_value = emit * 2.5
    L_.new(lw.outputs["Facing"], mm_.inputs[0])
    # "shield" (ko'k zirh) va "burn" (qizil, o'zini hazm qilish)
    shield = value_node(m, "shield", 0.0); burn = value_node(m, "burn", 0.0)
    c1 = nm.new("ShaderNodeMix"); c1.data_type = "RGBA"; L_.new(shield, c1.inputs["Factor"])
    c1.inputs[6].default_value = (*col, 1); c1.inputs[7].default_value = (0.25, 0.65, 1.0, 1)
    c2 = nm.new("ShaderNodeMix"); c2.data_type = "RGBA"; L_.new(burn, c2.inputs["Factor"])
    L_.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (1.0, 0.07, 0.02, 1)
    L_.new(c2.outputs[2], b.inputs["Base Color"]); L_.new(c2.outputs[2], b.inputs["Emission Color"])
    boost = P.math_n(nm, L_, "ADD", 1.0, P.math_n(nm, L_, "MULTIPLY", P.math_n(nm, L_, "ADD", shield, burn), 4.0))
    L_.new(P.math_n(nm, L_, "MULTIPLY", mm_.outputs[0], boost), b.inputs["Emission Strength"])
    tr = nm.new("ShaderNodeBsdfTransparent"); mx = nm.new("ShaderNodeMixShader"); mx.inputs[0].default_value = transp
    L_.new(b.outputs[0], mx.inputs[1]); L_.new(tr.outputs[0], mx.inputs[2])
    L_.new(mx.outputs[0], nm["Material Output"].inputs["Surface"])
    return m
eso_m = organ_mat("eso_m", (0.85, 0.42, 0.42))
sto_m = organ_mat("sto_m", (0.9, 0.5, 0.48), emit=0.45, transp=0.55)
si_m = organ_mat("si_m", (0.95, 0.6, 0.55), emit=0.15, transp=0.75)
ESO = [(0.0, 0.50, 0.0), (0.0, 0.44, 0.01), (0.005, 0.38, 0.025), (0.015, 0.33, 0.035), (0.03, 0.295, 0.045)]
STO = [(0.03, 0.295, 0.045), (0.06, 0.275, 0.055), (0.075, 0.235, 0.06), (0.065, 0.19, 0.065), (0.03, 0.17, 0.065),
       (-0.01, 0.175, 0.06), (-0.035, 0.185, 0.055)]
SI = [(-0.035, 0.185, 0.055), (-0.06, 0.165, 0.06)]
for r_ in range(5):
    y = 0.14 - r_ * 0.028
    xs = [-0.07, -0.035, 0.0, 0.035, 0.07]
    if r_ % 2: xs = xs[::-1]
    for j, x in enumerate(xs):
        SI.append((x, y + 0.004 * math.sin(j * 1.7 + r_), 0.07 + 0.008 * math.sin(j * 2.3 + r_ * 1.3)))
eso = P.tube("esophagus", catmull(ESO, 0.01), 0.008, eso_m, org)
sto_pts = catmull(STO, 0.008)
sto_tp = [0.3 + 0.7 * math.sin(math.pi * min(1.0, max(0.0, i / (len(sto_pts) - 1)))) ** 0.6 for i in range(len(sto_pts))]
sto = P.tube("stomach", sto_pts, 0.042, sto_m, org, taper=sto_tp)
si = P.tube("small_int", catmull(SI, 0.004), 0.0105, si_m, org)
# kislota: oshqozon ichida, kichikroq radius
xacid_m = acid_mat("xacid", strength=3.0, alpha=0.8, scale=60.0)
xacid = P.tube("stomach_acid", sto_pts[2:-2], 0.03, xacid_m, org, taper=sto_tp[2:-2])
# kislota pufakchalari (oshqozon ichida)
bub_m = glow_mat("xbub", (0.8, 1.0, 0.5), 4.0, alpha=0.7)
rb = random.Random(3)
xbubs = []
for i in range(26):
    p0 = sto_pts[rb.randint(6, len(sto_pts) - 8)]
    o = sphere(f"xbub{i}", rb.uniform(0.0015, 0.0035), (0, 0, 0), bub_m, sub=2, parent=org, world=False)
    ph = rb.uniform(0, 1); per = rb.randint(14, 26)
    for f in range(1, END + 1, 4):
        t = ((f / per) + ph) % 1.0
        key(o, f, loc=tuple(Vector(p0) + Vector((rb.uniform(-0.002, 0.002) + 0.01 * math.sin(i), -0.012 + 0.03 * t, 0.006 * math.cos(i)))))
    xbubs.append(o)
tg = P.tube_group()
for n in tg.nodes:
    if n.bl_idname == "GeometryNodeResampleCurve": n.inputs["Count"].default_value = 220
    if n.bl_idname == "GeometryNodeCurvePrimitiveCircle": n.inputs["Resolution"].default_value = 28
vis(org, X_SHOTS)
XS0, XS1 = S["xshield"]
for m_ in (sto_m,):
    val_key(m_, "shield", 1, 0.0); val_key(m_, "shield", XS0, 0.0); val_key(m_, "shield", XS0 + 8, 1.0)
    val_key(m_, "shield", XS1, 1.0); val_key(m_, "shield", XS1 + 1, 0.0)
    val_key(m_, "burn", 1, 0.0); val_key(m_, "burn", XSW, 0.0); val_key(m_, "burn", XSW + 2, 0.9); val_key(m_, "burn", END, 1.0)
for m_ in (eso_m, si_m):
    val_key(m_, "burn", 1, 0.0); val_key(m_, "burn", XSW, 0.0); val_key(m_, "burn", END, 0.25)

# ======================================================================
# 3) LABORATORIYA (-40,0,0): stakan + kislota + ustara tig'i
# ======================================================================
LAB = Vector((-40, 0, 0))
lab = empty("lab", tuple(LAB))
lfloor_m = mat("lab_floor", (0.012, 0.012, 0.014), 0.15, coat=1.0)
plane("lab_floor", (8, 8), tuple(LAB), lfloor_m, parent=lab)
plane("lab_back", (8, 3), tuple(LAB + Vector((0, 1.2, 1.5))), mat("lab_back_m", (0.01, 0.012, 0.012), 0.6), rot=(90, 0, 0), parent=lab)
BR_, BH = 0.045, 0.11
LIQ_H = 0.074
def fake_glass(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.02
    tr = N.new("ShaderNodeBsdfTransparent")
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.15
    mx = N.new("ShaderNodeMixShader")
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 0.7), 0.08, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=BR_, depth=BH, location=tuple(LAB + Vector((0, 0, BH / 2))))
beaker = bpy.context.object; beaker.name = "beaker"
bm_ = bmesh.new(); bm_.from_mesh(beaker.data)
top = [f_ for f_ in bm_.faces if f_.normal.z > 0.9]
bmesh.ops.delete(bm_, geom=top, context="FACES"); bm_.to_mesh(beaker.data); bm_.free()
for p_ in beaker.data.polygons: p_.use_smooth = True
so = beaker.modifiers.new("th", "SOLIDIFY"); so.thickness = 0.0018
beaker.data.materials.append(fake_glass("beaker_glass")); _par(beaker, lab)
# stakandagi o'lchov chiziqlari
grad_m = mat("grad", (0.9, 0.9, 0.9), 0.4, emit=0.3)
for i in range(5):
    z = 0.025 + i * 0.016
    box("grad", (0.012 if i % 2 else 0.02, 0.0006, 0.0012), tuple(LAB + Vector((0.012, -BR_ - 0.0012, z))), grad_m, parent=lab)
lacid_m = acid_mat("lab_acid", strength=0.3, alpha=0.18, scale=90.0)
lacid_m.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.0
liq = cyl("lab_liquid", BR_ - 0.0004, LIQ_H, tuple(LAB + Vector((0, 0, 0.0015 + LIQ_H / 2))), lacid_m, parent=lab, verts=96)
# yuza to'lqini: tig' tushganda halqa
ripple_m = glow_mat("ripple", (0.8, 1.0, 0.5), 3.0, alpha=0.6)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.04, major_segments=64, minor_segments=8,
                                 location=tuple(LAB + Vector((0, 0, 0.0015 + LIQ_H + 0.0005))))
rip = bpy.context.object; rip.name = "ripple"; rip.data.materials.append(ripple_m); _par(rip, lab)
key(rip, 1, scale=(0.001, 0.001, 0.001)); key(rip, IMPACT, scale=(0.002, 0.002, 0.03)); key(rip, IMPACT + 10, scale=(0.04, 0.04, 0.05))
key(rip, IMPACT + 11, scale=(0.001, 0.001, 0.001))
# ustara tig'i (43 x 22 mm, markazida teshik)
def blade_mesh():
    W, H, nx, ny = 0.043, 0.022, 86, 44
    vs = []; idx = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -W / 2 + W * i / nx; y = -H / 2 + H * j / ny
            idx[(i, j)] = len(vs); vs.append((x, y, 0.0))
    fs = []
    for j in range(ny):
        for i in range(nx):
            cx = -W / 2 + W * (i + 0.5) / nx; cy = -H / 2 + H * (j + 0.5) / ny
            slot = abs(cx) < 0.0145 and abs(cy) < 0.0016
            holes = any(math.hypot(cx - hx, cy) < 0.0033 for hx in (-0.0145, 0.0, 0.0145))
            corner = any(abs(cx) > W / 2 - 0.0025 and abs(cy) > H / 2 - 0.0025 for _ in [0]) and \
                math.hypot(abs(cx) - (W / 2 - 0.0025), abs(cy) - (H / 2 - 0.0025)) > 0.0025
            notch = abs(cx) > W / 2 - 0.0035 and abs(cy) < 0.0015
            if slot or holes or corner or notch: continue
            fs.append((idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]))
    me = bpy.data.meshes.new("blade"); me.from_pydata(vs, [], fs); me.update()
    return me
blade = bpy.data.objects.new("blade", blade_mesh()); sc.collection.objects.link(blade); blade.parent = lab
sb = blade.modifiers.new("th", "SOLIDIFY"); sb.thickness = 0.00025; sb.offset = 0.0
def blade_material():
    m = bpy.data.materials.new("blade_steel"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; out = N["Material Output"]
    b.inputs["Base Color"].default_value = (0.82, 0.83, 0.86, 1); b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.18; b.inputs["Anisotropic"].default_value = 0.6
    tc = N.new("ShaderNodeTexCoord"); obj = tc.outputs["Object"]
    eat = value_node(m, "eat", 0.0)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 260; nz.inputs["Detail"].default_value = 6; L.new(obj, nz.inputs[0])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(obj, sep.inputs[0])
    dx = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", sep.outputs[0]), 0.0215)
    dy = P.math_n(N, L, "DIVIDE", P.math_n(N, L, "ABSOLUTE", sep.outputs[1]), 0.011)
    d = P.math_n(N, L, "MAXIMUM", dx, dy)
    field = P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, d), 0.55), P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.5))
    gone = P.math_n(N, L, "LESS_THAN", field, eat)
    edge = P.math_n(N, L, "LESS_THAN", field, P.math_n(N, L, "ADD", eat, 0.05))
    # korroziya rangi: erish chekkasida qoraygan dog'lar
    rust = P.math_n(N, L, "LESS_THAN", field, P.math_n(N, L, "ADD", eat, 0.14))
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", rust, P.math_n(N, L, "GREATER_THAN", eat, 0.001)), c1.inputs["Factor"])
    c1.inputs[6].default_value = (0.82, 0.83, 0.86, 1); c1.inputs[7].default_value = (0.12, 0.16, 0.05, 1)
    L.new(c1.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (0.8, 1.0, 0.3, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", edge, P.math_n(N, L, "GREATER_THAN", eat, 0.001)), 12.0), b.inputs["Emission Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(gone, mx.inputs[0]); L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m
blade_m = blade_material(); blade.data.materials.append(blade_m)
BL0, BL1 = S["blade"]
SURF = 0.0015 + LIQ_H
# tushish: tepadan aylanib, IMPACT da yuzaga, keyin sekin cho'kadi
for f, z, rx, rz in ((BL0, 0.20, 70, -30), (BL0 + 10, 0.16, 55, -10), (IMPACT, SURF, 25, 5), (IMPACT + 8, SURF - 0.016, 35, 0),
                     (IMPACT + 22, 0.034, 42, -8), (BL1, 0.022, 48, -18)):
    key(blade, f, loc=(0.004, 0.0, z), rot=(rx, 12, rz))
for fc in fcurves(blade):
    for k in fc.keyframe_points:
        if k.co.x < IMPACT: k.interpolation = "QUAD"; k.easing = "EASE_IN"
val_key(blade_m, "eat", 1, 0.0); val_key(blade_m, "eat", IMPACT + 4, 0.0); val_key(blade_m, "eat", IMPACT + 18, 0.35)
val_key(blade_m, "eat", BL1 - 6, 0.98); val_key(blade_m, "eat", BL1, 1.08)
# sachrash tomchilari
spl_m = glow_mat("splash", (0.55, 1.0, 0.25), 3.5, alpha=0.75)
rs = random.Random(11)
splash = []
for i in range(16):
    o = sphere(f"spl{i}", rs.uniform(0.0012, 0.0028), (0, 0, 0), spl_m, sub=2, parent=lab, world=False)
    a = rs.uniform(0, 2 * math.pi); v = rs.uniform(0.25, 0.55); vz = rs.uniform(0.6, 1.1)
    p0 = Vector((0.004 + 0.008 * math.cos(a), 0.008 * math.sin(a), SURF))
    key(o, 1, loc=tuple(p0), scale=(0.01,) * 3); key(o, IMPACT, loc=tuple(p0), scale=(0.01,) * 3)
    for k in range(1, 22):
        t = k / 24.0
        p = p0 + Vector((math.cos(a) * v * t * 0.3, math.sin(a) * v * t * 0.3, vz * t - 4.9 * t * t))
        if p.z < SURF and k > 3: key(o, IMPACT + k, loc=tuple(p), scale=(0.01,) * 3); break
        key(o, IMPACT + k, loc=tuple(p), scale=(1, 1, 1.4))
    splash.append(o)
# pufakchalar: tig'dan ko'tariladi
bubl_m = glow_mat("lab_bubble", (0.85, 1.0, 0.6), 2.0, alpha=0.55)
for i in range(60):
    o = sphere(f"lbub{i}", rs.uniform(0.0006, 0.0018), (0, 0, 0), bubl_m, sub=2, parent=lab, world=False)
    t0 = IMPACT + 4 + rs.randint(0, BL1 - IMPACT - 10)
    x0 = rs.uniform(-0.015, 0.02); y0 = rs.uniform(-0.008, 0.008)
    sc.frame_set(t0); z0 = blade.matrix_world.translation.z - LAB.z
    key(o, 1, loc=(x0, y0, z0), scale=(0.01,) * 3); key(o, t0 - 1, loc=(x0, y0, z0), scale=(0.01,) * 3)
    key(o, t0, loc=(x0, y0, z0), scale=(1, 1, 1))
    tt = int((SURF - z0) / 0.0025) + 2
    key(o, t0 + tt, loc=(x0 + rs.uniform(-0.004, 0.004), y0, SURF - 0.001), scale=(1, 1, 1))
    key(o, t0 + tt + 1, scale=(0.01,) * 3)
    interp(o, "LINEAR", "location")
vis(lab, LAB_SHOTS)

# ======================================================================
# 4) OSHQOZON ICHI (0,80,0): burmali g'or + kislota ko'li + shilliq qavat
# ======================================================================
CAVE = Vector((0, 80, 0))
cave_root = empty("cave_root", tuple(CAVE))
bpy.ops.mesh.primitive_uv_sphere_add(segments=200, ring_count=100, radius=1.0, location=(0, 0, 0))
cave = bpy.context.object; cave.name = "cave"
cave.scale = (3.2, 1.7, 1.5); bpy.ops.object.transform_apply(scale=True)
bm_ = bmesh.new(); bm_.from_mesh(cave.data); bmesh.ops.reverse_faces(bm_, faces=bm_.faces); bm_.to_mesh(cave.data); bm_.free()
for p_ in cave.data.polygons: p_.use_smooth = True
ruga = bpy.data.textures.new("rugae", "MARBLE"); ruga.marble_type = "SHARPER"; ruga.noise_basis_2 = "SIN"
ruga.turbulence = 6.0; ruga.noise_scale = 0.55; ruga.noise_depth = 2
def rugae_mods(o, extra=0.0):
    d = o.modifiers.new("rug", "DISPLACE"); d.texture = ruga; d.texture_coords = "LOCAL"; d.strength = -0.32; d.mid_level = 0.5
    if extra:
        d2 = o.modifiers.new("off", "DISPLACE"); d2.strength = extra; d2.mid_level = 0.0
rugae_mods(cave)
def cave_material():
    m = bpy.data.materials.new("cave_wall"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); obj = tc.outputs["Object"]
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 6; L.new(obj, nz.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.55, 0.12, 0.12, 1); cr.color_ramp.elements[1].color = (0.95, 0.45, 0.42, 1)
    vn = N.new("ShaderNodeTexNoise"); vn.inputs["Scale"].default_value = 1.6; vn.inputs["Distortion"].default_value = 0.8; L.new(obj, vn.inputs[0])
    vr = N.new("ShaderNodeMapRange"); L.new(vn.outputs["Fac"], vr.inputs["Value"]); vr.inputs["From Min"].default_value = 0.48; vr.inputs["From Max"].default_value = 0.5
    vr2 = N.new("ShaderNodeMapRange"); L.new(vn.outputs["Fac"], vr2.inputs["Value"]); vr2.inputs["From Min"].default_value = 0.52; vr2.inputs["From Max"].default_value = 0.5
    vein = P.math_n(N, L, "MULTIPLY", vr.outputs[0], vr2.outputs[0])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(vein, c1.inputs["Factor"]); L.new(cr.outputs[0], c1.inputs[6])
    c1.inputs[7].default_value = (0.35, 0.02, 0.04, 1)
    L.new(c1.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.03
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.03
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    bn = N.new("ShaderNodeTexNoise"); bn.inputs["Scale"].default_value = 30; bn.inputs["Detail"].default_value = 8; L.new(obj, bn.inputs[0])
    bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.25; bmp.inputs["Distance"].default_value = 0.01
    L.new(bn.outputs["Fac"], bmp.inputs["Height"]); L.new(bmp.outputs[0], b.inputs["Normal"])
    return m
cave.data.materials.append(cave_material())
cave.parent = cave_root
# shilliq qavat: o'sha mesh, ichkariga 3 sm siljigan, ko'k gel
def gel_material(name, glow0=0.08):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; out = N["Material Output"]
    b.inputs["Base Color"].default_value = (0.45, 0.72, 1.0, 1); b.inputs["Roughness"].default_value = 0.06
    b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.02
    glow = value_node(m, "glow", glow0); flash = value_node(m, "flash", 0.0); sweep = value_node(m, "sweep", 10.0)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    sw = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", sweep, sep.outputs[0]), 2.0, clamp=True)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 14; L.new(tc.outputs["Object"], nz.inputs[0])
    e = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 1.5), P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.6)),
                 P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", glow, sw), flash))
    b.inputs["Emission Color"].default_value = (0.2, 0.6, 1.0, 1); L.new(e, b.inputs["Emission Strength"])
    bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.3; L.new(nz.outputs["Fac"], bmp.inputs["Height"]); L.new(bmp.outputs[0], b.inputs["Normal"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    a_ = value_node(m, "alpha", 0.45)
    L.new(P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "ADD", a_, P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 0.3)), clamp=True), mx.inputs[0])
    L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m
cgel_m = gel_material("cave_gel", 0.05); cgel_m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.15, 0.45, 1.0, 1)
cgel = bpy.data.objects.new("cave_gel", cave.data); sc.collection.objects.link(cgel); cgel.parent = cave_root
rugae_mods(cgel, extra=0.035)
cgel.material_slots[0].link = "OBJECT"; cgel.material_slots[0].material = cgel_m
# kislota ko'li
POOL_Z = -0.85
pool_m = acid_mat("pool_acid", strength=1.0, alpha=0.9, scale=3.0)
pool = plane("pool", (6.5, 3.6), (0, 0, 0), pool_m); pool.parent = cave_root; pool.location = (0, 0, POOL_Z)
rc = random.Random(5)
pbub_m = glow_mat("pool_bub", (0.8, 1.0, 0.4), 3.0, alpha=0.6)
for i in range(40):
    p0 = Vector((rc.uniform(-2.4, 2.4), rc.uniform(-1.0, 1.0), POOL_Z))
    o = sphere(f"pbub{i}", rc.uniform(0.02, 0.06), (0, 0, 0), pbub_m, sub=2, parent=cave_root, world=False)
    per = rc.randint(10, 20); ph = rc.randint(0, per)
    for f in range(S["cave"][0] - 2, S["mucus"][1] + 2, 2):
        t = ((f + ph) % per) / per
        key(o, f, loc=tuple(p0 + Vector((0, 0, 0.02 * t))), scale=(1, 1, 0.5 + 0.8 * math.sin(math.pi * t)))
# kislota bug'i / zarralar
for i in range(50):
    o = sphere(f"cfog{i}", rc.uniform(0.006, 0.014), (0, 0, 0), glow_mat("cfog_m", (0.6, 1.0, 0.3), 5.0) if i == 0 else bpy.data.materials["cfog_m"], sub=1, parent=cave_root, world=False)
    p0 = Vector((rc.uniform(-2.6, 2.6), rc.uniform(-1.1, 1.1), rc.uniform(-0.8, 0.6)))
    key(o, S["cave"][0], loc=tuple(p0)); key(o, S["mucus"][1], loc=tuple(p0 + Vector((rc.uniform(-0.1, 0.1), 0, 0.25))))
    interp(o, "LINEAR", "location")
vis(cave_root, CAVE_SHOTS)
MU0, MU1 = S["mucus"]
val_key(cgel_m, "glow", 1, 0.0); val_key(cgel_m, "glow", MU0, 0.0); val_key(cgel_m, "glow", MU0 + 3, 0.7); val_key(cgel_m, "glow", MU1, 0.45)
val_key(cgel_m, "sweep", 1, 10.0); val_key(cgel_m, "sweep", MU0, -1.0); val_key(cgel_m, "sweep", MU0 + 14, 3.5)
val_key(cgel_m, "alpha", 1, 0.03); val_key(cgel_m, "alpha", MU0, 0.03); val_key(cgel_m, "alpha", MU0 + 6, 0.1)

# ======================================================================
# 5) DEVOR KESIMI (60,0,0): mushak, shilliq osti, hujayralar, shilliq "zirh", kislota
# ======================================================================
SEC = Vector((60, 0, 0))
sec = empty("sec", tuple(SEC))
SX, SY = 1.3, 0.65
Z_MUS, Z_SUB, Z_CELL0, Z_CELLT, Z_GEL = 0.32, 0.48, 0.48, 0.78, 0.98
def striated(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.bands_direction = "Y"
    wv.inputs["Scale"].default_value = 9.0; wv.inputs["Distortion"].default_value = 4.0; wv.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.45, 0.06, 0.06, 1); cr.color_ramp.elements[1].color = (0.8, 0.25, 0.22, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.45
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.02
    b.inputs["Coat Weight"].default_value = 0.4
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
box("sec_muscle", (2 * SX, 2 * SY, Z_MUS), tuple(SEC + Vector((0, 0, Z_MUS / 2))), striated("muscle"), parent=sec)
sub_m = mat("submucosa", (0.92, 0.66, 0.6), 0.5, sss=0.4, sss_scale=0.02, coat=0.3)
box("sec_sub", (2 * SX, 2 * SY, Z_SUB - Z_MUS), tuple(SEC + Vector((0, 0, (Z_MUS + Z_SUB) / 2))), sub_m, parent=sec)
# qon tomirlari (shilliq osti qavatida, old yuzada ko'rinadi)
vess_m = mat("vessel", (0.55, 0.02, 0.03), 0.3, coat=0.8, sss=0.3, sss_scale=0.01)
rv = random.Random(4)
for j in range(4):
    zc = Z_MUS + 0.04 + j * 0.035
    pts = [(-SX + k * 0.26, -SY + 0.02 + rv.uniform(0, 0.25), zc + rv.uniform(-0.02, 0.02)) for k in range(11)]
    P.tube(f"vessel{j}", pts, rv.uniform(0.012, 0.02), vess_m, sec)
# hujayralar: ikki qator (A = eski, B = yangi o'sadigan)
def cell_material():
    m = bpy.data.materials.new("cell"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    oi = N.new("ShaderNodeObjectInfo")
    burn = value_node(m, "burn", 0.0)
    # har hujayra o'z vaqtida kuyadi: burn*1.5 - random*0.5
    bf = P.math_n(N, L, "SUBTRACT", P.math_n(N, L, "MULTIPLY", burn, 1.5), P.math_n(N, L, "MULTIPLY", oi.outputs["Random"], 0.5), clamp=True)
    c0 = N.new("ShaderNodeMix"); c0.data_type = "RGBA"; L.new(oi.outputs["Random"], c0.inputs["Factor"])
    c0.inputs[6].default_value = (0.9, 0.42, 0.42, 1); c0.inputs[7].default_value = (0.82, 0.32, 0.38, 1)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(bf, c1.inputs["Factor"]); L.new(c0.outputs[2], c1.inputs[6])
    c1.inputs[7].default_value = (0.12, 0.02, 0.015, 1)
    tcn = N.new("ShaderNodeTexCoord")
    nd = P.math_n(N, L, "DISTANCE", tcn.outputs["Object"], (0.0, -0.065, -0.03), vec=True)
    nuc = N.new("ShaderNodeMapRange"); L.new(nd, nuc.inputs["Value"]); nuc.inputs["From Min"].default_value = 0.04
    nuc.inputs["From Max"].default_value = 0.03; nuc.interpolation_type = "SMOOTHSTEP"
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", nuc.outputs[0], P.math_n(N, L, "SUBTRACT", 1.0, bf)), c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.3, 0.08, 0.4, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.4; b.inputs["Coat Weight"].default_value = 0.3
    b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.3)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.02, 1)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "MULTIPLY", bf, P.math_n(N, L, "SUBTRACT", 1.0, bf)), P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 14.0), 1.0)), b.inputs["Emission Strength"])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; L.new(tc.outputs["Object"], nz.inputs[0])
    bp = N.new("ShaderNodeBump"); L.new(P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], P.math_n(N, L, "ADD", 0.2, bf)), bp.inputs["Height"])
    bp.inputs["Strength"].default_value = 0.6; L.new(bp.outputs[0], b.inputs["Normal"])
    return m
cell_m = cell_material()
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
cmesh_o = bpy.context.object; CW = 0.13
for v in cmesh_o.data.vertices:
    v.co.x *= CW * 0.95; v.co.y *= CW * 0.95; v.co.z *= (Z_CELLT - Z_CELL0)
bm_ = bmesh.new(); bm_.from_mesh(cmesh_o.data)
bmesh.ops.bevel(bm_, geom=list(bm_.edges), offset=0.02, segments=4, affect="EDGES", profile=0.5)
bm_.to_mesh(cmesh_o.data); bm_.free()
for p_ in cmesh_o.data.polygons: p_.use_smooth = True
cmesh = cmesh_o.data; cmesh.materials.append(cell_m); bpy.data.objects.remove(cmesh_o)
# yadro (old qatorda ko'rinadi)
nuc_m = mat("nucleus", (0.35, 0.12, 0.45), 0.35, sss=0.3, sss_scale=0.01, coat=0.5)
cells_A, cells_B = [], []
rcell = random.Random(8)
NX, NY = 20, 10
ZC = (Z_CELL0 + Z_CELLT) / 2
for j in range(NY):
    for i in range(NX):
        x = -SX + CW * (i + 0.5); y = -SY + CW * (j + 0.5)
        for lst, tag in ((cells_A, "A"), (cells_B, "B")):
            o = bpy.data.objects.new(f"cell{tag}_{i}_{j}", cmesh); sc.collection.objects.link(o); o.parent = sec
            o.location = (x + rcell.uniform(-0.004, 0.004), y + rcell.uniform(-0.004, 0.004), ZC)
            o.rotation_euler = (0, 0, rcell.uniform(-0.05, 0.05))
            o["ij"] = (i, j); lst.append(o)
# shilliq "zirh" (gel): tepa yuzasi shape key bilan yupqalashadi
def gel_slab(name, nx=104, ny=52):
    vs = []; fs = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            vs.append((-SX + 2 * SX * i / nx, -SY + 2 * SY * j / ny, Z_GEL))
    nt = len(vs)
    for j in range(ny + 1):
        for i in range(nx + 1):
            vs.append((-SX + 2 * SX * i / nx, -SY + 2 * SY * j / ny, Z_CELLT - 0.07))
    I_ = lambda i, j, b=0: b * nt + j * (nx + 1) + i
    for j in range(ny):
        for i in range(nx):
            fs.append((I_(i, j), I_(i + 1, j), I_(i + 1, j + 1), I_(i, j + 1)))
            fs.append((I_(i, j + 1, 1), I_(i + 1, j + 1, 1), I_(i + 1, j, 1), I_(i, j, 1)))
    for i in range(nx):
        fs.append((I_(i, 0, 1), I_(i + 1, 0, 1), I_(i + 1, 0), I_(i, 0)))
        fs.append((I_(i, ny), I_(i + 1, ny), I_(i + 1, ny, 1), I_(i, ny, 1)))
    for j in range(ny):
        fs.append((I_(0, j), I_(0, j + 1), I_(0, j + 1, 1), I_(0, j, 1)))
        fs.append((I_(nx, j, 1), I_(nx, j + 1, 1), I_(nx, j + 1), I_(nx, j)))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    for p_ in me.polygons: p_.use_smooth = True
    o.shape_key_add(name="Basis")
    er = o.shape_key_add(name="erode", from_mix=False); er.value = 0.0
    rr_ = random.Random(2)
    pits = [(rr_.uniform(-SX, SX), rr_.uniform(-SY, SY), rr_.uniform(0.05, 0.16), rr_.uniform(0.03, 0.08)) for _ in range(38)]
    for k in range(nt):
        x, y, z = vs[k]
        d = 0.09 + 0.02 * math.sin(x * 7.0) * math.cos(y * 6.0)
        for px, py, pr, pd in pits:
            q = math.hypot(x - px, y - py)
            if q < pr: d += pd * (1 - (q / pr) ** 2)
        er.data[k].co.z = max(Z_CELLT - 0.06, z - d)
    return o
gel = gel_slab("sec_gel"); gel.parent = sec
gel_m = gel_material("sec_gel_m", 0.6); gel_m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.5, 1.0, 1)
val_key(gel_m, "alpha", 1, 0.22); gel.data.materials.append(gel_m)
erk = gel.data.shape_keys.key_blocks["erode"]
AR0, AR1 = S["armor"]; ER0, ER1 = S["erode"]; RG0, RG1 = S["regrow"]; DG0, DG1 = S["digest"]
for f, v in ((1, 0.0), (ER0 + 4, 0.0), (ER1, 1.0), (RG0 + 10, 1.0), (RG1 - 10, 0.0)):
    erk.value = v; erk.keyframe_insert("value", frame=f)
# kislota tomchilari: tepadan tushib "zirh"ga uriladi
drop_m = glow_mat("acid_drop", (0.45, 1.0, 0.12), 4.0, alpha=0.85)
rd = random.Random(13)
DROP_V = 0.06                      # m/kadr
def gel_top(f, x, y):
    """taxminiy shilliq yuzasi (erode qiymati bo'yicha)"""
    sc.frame_set(f); v = erk.value
    return Z_GEL - v * 0.11
impacts = []
def drop(i, t_hit, x, y, z_hit, r=None):
    r = r or rd.uniform(0.018, 0.032)
    o = sphere(f"drop{i}", r, (0, 0, 0), drop_m, sub=3, parent=sec, world=False)
    n_fall = 26
    key(o, 1, loc=(x, y, z_hit + DROP_V * n_fall), scale=(0.01,) * 3)
    key(o, t_hit - n_fall - 1, loc=(x, y, z_hit + DROP_V * n_fall), scale=(0.01,) * 3)
    key(o, t_hit - n_fall, loc=(x, y, z_hit + DROP_V * n_fall), scale=(0.9, 0.9, 1.25))
    key(o, t_hit, loc=(x, y, z_hit + r * 0.6), scale=(0.9, 0.9, 1.25))
    key(o, t_hit + 2, loc=(x, y, z_hit + r * 0.2), scale=(1.8, 1.8, 0.35))
    key(o, t_hit + 5, loc=(x, y, z_hit), scale=(0.01, 0.01, 0.01))
    interp(o, "LINEAR", "location")
    impacts.append(t_hit)
    return o
di = 0
for (a, b_), n_, zfn in (((AR0 + 4, AR1), 16, None), ((ER0, ER1), 14, None), ((RG0, RG1), 10, None), ((DG0 - 6, DG1 + 4), 18, "cell")):
    for k in range(n_):
        t_hit = a + int((b_ - a) * (k + rd.uniform(0.1, 0.9)) / n_)
        x = rd.uniform(-SX * 0.75, SX * 0.75); y = rd.uniform(-SY * 0.8, SY * 0.4)
        z = (Z_CELLT - 0.02) if zfn else gel_top(t_hit, x, y)
        drop(di, t_hit, x, y, z); di += 1
# urilishda ko'k chaqnash (armor) — gel "flash"
val_key(gel_m, "flash", 1, 0.0)
for t_hit in sorted(impacts):
    if AR0 <= t_hit <= ER1:
        k_ = 2.5 if t_hit <= AR1 else 0.8
        val_key(gel_m, "flash", t_hit - 1, 0.0); val_key(gel_m, "flash", t_hit, k_); val_key(gel_m, "flash", t_hit + 4, 0.0)
val_key(gel_m, "flash", ZIRH - 1, 0.0); val_key(gel_m, "flash", ZIRH + 1, 4.0); val_key(gel_m, "flash", ZIRH + 8, 0.3)
val_key(gel_m, "glow", 1, 0.6); val_key(gel_m, "glow", ER0, 0.6); val_key(gel_m, "glow", ER1, 0.15); val_key(gel_m, "glow", RG1, 0.6)
val_key(gel_m, "sweep", 1, 10.0); val_key(gel_m, "sweep", MU0, -1.6); val_key(gel_m, "sweep", MU0 + 22, 1.6); val_key(gel_m, "sweep", AR0, 10.0)
val_key(gel_m, "glow", MU0, 2.0); val_key(gel_m, "glow", MU1, 1.4)
# vodorod ionlari (H+) — kislotada suzadigan mayda yashil zarralar
hp_m = glow_mat("hplus", (0.55, 1.0, 0.2), 6.0)
for i in range(90):
    o = sphere(f"hp{i}", rd.uniform(0.004, 0.009), (0, 0, 0), hp_m, sub=1, parent=sec, world=False)
    p0 = Vector((rd.uniform(-SX, SX), rd.uniform(-SY, SY * 2.5), rd.uniform(1.05, 2.3)))
    key(o, AR0, loc=tuple(p0)); key(o, DG1, loc=tuple(p0 + Vector((rd.uniform(-0.2, 0.2), 0, -0.35))))
    interp(o, "LINEAR", "location")
# yangilanish: eski hujayralar (A) ko'tarilib eriydi, yangilari (B) ostidan o'sadi
for o in cells_A + cells_B:
    o.scale = (1, 1, 1)
for a_, b__ in zip(cells_A, cells_B):
    i, j = a_["ij"]
    t_i = RG0 + 6 + int((i / NX) * 50 + rcell.uniform(0, 26))
    loc = Vector(a_.location)
    key(a_, 1, loc=tuple(loc), scale=(1, 1, 1)); key(a_, t_i, loc=tuple(loc), scale=(1, 1, 1))
    key(a_, t_i + 26, loc=tuple(loc + Vector((rcell.uniform(-0.05, 0.05), rcell.uniform(-0.05, 0.05), 0.55))),
        scale=(0.05, 0.05, 0.05))
    a_.rotation_euler = (0, 0, a_.rotation_euler.z); a_.keyframe_insert("rotation_euler", frame=t_i)
    a_.rotation_euler = (R(rcell.uniform(-90, 90)), R(rcell.uniform(-90, 90)), a_.rotation_euler.z); a_.keyframe_insert("rotation_euler", frame=t_i + 26)
    lb = Vector(b__.location)
    key(b__, 1, loc=(lb.x, lb.y, Z_CELL0 + 0.01), scale=(0.3, 0.3, 0.02)); key(b__, t_i - 4, loc=(lb.x, lb.y, Z_CELL0 + 0.01), scale=(0.3, 0.3, 0.02))
    key(b__, t_i + 20, loc=tuple(lb), scale=(1, 1, 1))
    # o'zini hazm qilish: kichrayib, cho'kadi
    sq = rcell.uniform(0.25, 0.6)
    key(b__, DG0 + 2, loc=tuple(lb), scale=(1, 1, 1))
    key(b__, DG1 + 2, loc=(lb.x, lb.y, ZC - (1 - sq) * 0.13), scale=(0.75 + 0.2 * sq, 0.75 + 0.2 * sq, sq))
    vis(a_, [(1, t_i + 26)], recursive=True); vis(b__, [(t_i - 4, END)], recursive=True)
val_key(cell_m, "burn", 1, 0.0); val_key(cell_m, "burn", DG0, 0.0); val_key(cell_m, "burn", DG0 + 22, 1.0)
# fon: qorong'i yashil kislota "tuman" devori
bg_m = mat("sec_bg", (0.0, 0.0, 0.0), 1.0, emit=0.25, emit_col=(0.08, 0.35, 0.05))
plane("sec_bg", (24, 14), tuple(SEC + Vector((0, 3.5, 3.0))), bg_m, rot=(90, 0, 0), parent=sec)
plane("sec_floor", (10, 10), tuple(SEC + Vector((0, 0, -0.001))), mat("sec_floor_m", (0.01, 0.02, 0.01), 0.3, coat=1.0), parent=sec)
# sahna ko'rinishi (bolalardan keyin alohida vis — tuzoq)
SEC_ON = SEC_SHOTS
for o in [sec] + [c for c in sec.children_recursive if not (c.name.startswith("cellA") or c.name.startswith("cellB") or c.name.startswith("nuc"))]:
    vis(o, SEC_ON, recursive=False)
def and_ranges(r1, r2):
    out = []
    for a, b in r1:
        for c, d in r2:
            lo, hi = max(a, c), min(b, d)
            if lo <= hi: out.append((lo, hi))
    return out
for a_, b__ in zip(cells_A, cells_B):
    ra = [(1, max(1, int([k.co.x for fc in fcurves(a_) if fc.data_path == "location" for k in fc.keyframe_points][-1])))]
    vis(a_, and_ranges(ra, SEC_ON), recursive=True)
    t_b = int([k.co.x for fc in fcurves(b__) if fc.data_path == "location" for k in fc.keyframe_points][1])
    vis(b__, and_ranges([(t_b, END)], SEC_ON), recursive=True)
vis(gel, and_ranges(SEC_ON, [(1, DG0 - 1)]), recursive=False)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def hips_world(f, local):
    sc.frame_set(f); return Vector(tuple(hipsE.matrix_world @ Vector(local)))
def head_world(f, local=(0, 0.09, 0.08)):
    sc.frame_set(f); return Vector(tuple(headE.matrix_world @ Vector(local)))
BELLY = (0.03, 0.22, 0.13)                   # Hips fazosida qorin oldi
STOMACH = (0.04, 0.23, 0.06)                 # oshqozon markazi
HO0, HO1 = S["hook"]; XA0, XA1 = S["xacid"]; XW0, XW1 = S["xwall"]; CA0, CA1 = S["cave"]
# 1 ilgak: poldan qoringa tez push-in
bT = empty("bellyT", (0, 0, 0))
for f in range(HO0, HO1 + 1, 3): key(bT, f, loc=tuple(hips_world(f, BELLY)))
b0 = hips_world(HO0, BELLY)
c = shot_cam("hook", (0, 0, 0), bT, 16, 4.0, focus=bT)
path_keys(c, ((HO0, tuple(b0 + Vector((0.55, -2.3, -0.85)))), (HO1, tuple(b0 + Vector((0.12, -0.55, -0.3))))))
for fc in fcurves(c):
    for k in fc.keyframe_points: k.interpolation = "QUAD"; k.easing = "EASE_IN"
lens_keys(c, ((HO0, 15), (HO1, 22)))
# 2 rentgen: oshqozon, crash zoom
sT = empty("stoT", (0, 0, 0))
for f in range(XA0, XA1 + 1, 3): key(sT, f, loc=tuple(hips_world(f, STOMACH)))
s0 = hips_world(XA0, STOMACH)
c = shot_cam("xacid", (0, 0, 0), sT, 28, 4.0, focus=sT)
path_keys(c, ((XA0, tuple(s0 + Vector((0.25, -0.75, 0.05)))), (XA1, tuple(s0 + Vector((0.12, -0.55, 0.02))))))
lens_keys(c, ((XA0, 24), (XA0 + 3, 42), (XA0 + 6, 58), (XA1, 64)))
shake(c, XA0 + 3, XA0 + 14, 0.012, 2)
# 3 laboratoriya: past burchak, IMPACT da crash zoom, keyin aylanma
lT = empty("labT", (0, 0, 0))
for f, z in ((BL0, 0.15), (IMPACT - 4, SURF + 0.01), (IMPACT + 10, 0.05), (BL1, 0.03)):
    key(lT, f, loc=tuple(LAB + Vector((0.004, 0, z))))
c = shot_cam("blade", (0, 0, 0), lT, 24, 11.0, focus=lT, clip=0.001)
path_keys(c, ((BL0, tuple(LAB + Vector((0.16, -0.26, 0.06)))), (IMPACT, tuple(LAB + Vector((0.11, -0.19, 0.12))))))
for f in range(IMPACT + 2, BL1 + 1, 2):
    t = (f - IMPACT) / (BL1 - IMPACT); a = R(30 - 75 * t); rr = 0.24 - 0.04 * t
    key(c, f, loc=tuple(LAB + Vector((rr * math.sin(a), -rr * math.cos(a), 0.16 - 0.03 * t))))
lens_keys(c, ((BL0, 24), (IMPACT - 1, 28), (IMPACT + 2, 36), (BL1, 42)))
shake(c, IMPACT, IMPACT + 10, 0.004, 3)
# 4 o'ylanish: yuzga yaqin plan
fT = empty("faceT2", (0, 0, 0))
for f in range(TH0, TH1 + 1, 2): key(fT, f, loc=tuple(head_world(f)))
h0 = head_world(TH0)
c = shot_cam("think", (0, 0, 0), fT, 55, 2.0, focus=fT)
path_keys(c, ((TH0, tuple(h0 + Vector((0.22, -0.62, 0.03)))), (TH1, tuple(h0 + Vector((0.12, -0.46, 0.0))))))
# 5 rentgen: yondan aylanma
s1 = hips_world((XW0 + XW1) // 2, STOMACH)
sT2 = empty("stoT2", tuple(s1))
c = shot_cam("xwall", (0, 0, 0), sT2, 50, 4.0, focus=sT2)
orbit(c, XW0, XW1, tuple(s1), 0.62, 0.5, 65, 15, 0.08, 0.0)
# 6 g'or: bo'ylab uchish
cT = empty("caveT", (0, 0, 0))
c = shot_cam("cave", (0, 0, 0), cT, 18, 8.0, focus=2.0, clip=0.01)
for f, p, t_ in ((CA0, (-2.35, -0.15, 0.25), (0.5, 0.1, -0.35)), (CA1, (-0.2, 0.05, 0.05), (2.4, 0.4, -0.25))):
    key(c, f, loc=tuple(CAVE + Vector(p))); key(cT, f, loc=tuple(CAVE + Vector(t_)))
interp(c, "LINEAR", "location")
lens_keys(c, ((CA0, 16), (CA1, 20)))
# 7 shilliq: devorga yaqin (ray cast bilan devor nuqtasi)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
o_ = CAVE + Vector((0.4, 0.0, 0.1)); d_ = Vector((0.15, 1.0, 0.05)).normalized()
hit, loc_, nrm_, *_ = sc.ray_cast(dg, o_, d_)
WALLP = loc_ if hit else CAVE + Vector((0.6, 1.4, 0.15))
print('WALLP', hit, WALLP, (WALLP - o_).length)
mT = empty("mucusT", tuple(SEC + Vector((0.1, -SY, Z_GEL - 0.08))))
c = shot_cam("mucus", (0, 0, 0), mT, 20, 4.0, focus=mT, clip=0.005)
path_keys(c, ((MU0, tuple(SEC + Vector((-0.7, -2.7, 1.7)))), (MU1, tuple(SEC + Vector((-0.25, -1.5, 1.05))))))
lens_keys(c, ((MU0, 18), (MU0 + 3, 30), (MU1, 34)))
shake(c, MU0, MU0 + 8, 0.02, 7)
# 8 zirh: past burchak, yonlama siljish
gT = empty("gelT", tuple(SEC + Vector((0.0, 0.0, Z_GEL))))
c = shot_cam("armor", (0, 0, 0), gT, 24, 5.6, focus=gT)
path_keys(c, ((AR0, tuple(SEC + Vector((-1.25, -2.05, 0.62)))), (AR1, tuple(SEC + Vector((0.35, -1.85, 0.72))))))
interp(c, "LINEAR", "location")
shake(c, ZIRH, ZIRH + 10, 0.03, 8)
# 9 yemirilish: aylanma + qo'l kamerasi
eT = empty("erodeT", tuple(SEC + Vector((0.15, 0.0, Z_CELLT + 0.1))))
c = shot_cam("erode", (0, 0, 0), eT, 32, 4.0, focus=eT)
orbit(c, ER0, ER1, tuple(SEC + Vector((0.15, 0, 0))), 1.55, 1.2, -35, 15, 1.65, 1.4)
shake(c, ER0, ER1, 0.008, 9, decay=False)
# 10 kunlar: divanda, kun-tun
dT = empty("daysT", (SOFA[0], SOFA[1] - 0.1, 0.8))
c = shot_cam("days", (0, 0, 0), dT, 20, 4.0, focus=dT)
path_keys(c, ((DA0, (-1.7, -0.55, 1.05)), (DA1, (-1.05, -0.85, 1.12))))
interp(c, "LINEAR", "location")
# 11 yangilanish: push-in
rT = empty("regrowT", tuple(SEC + Vector((0.2, 0.0, Z_CELLT))))
c = shot_cam("regrow", (0, 0, 0), rT, 28, 4.5, focus=rT)
path_keys(c, ((RG0, tuple(SEC + Vector((0.95, -2.25, 1.35)))), (RG1, tuple(SEC + Vector((0.45, -1.45, 1.0))))))
interp(c, "LINEAR", "location")
# 12 rentgen zirh: past burchakdan ko'tariladi
s2 = hips_world((XS0 + XS1) // 2, STOMACH)
sT3 = empty("stoT3", tuple(s2))
c = shot_cam("xshield", (0, 0, 0), sT3, 38, 4.0, focus=sT3)
path_keys(c, ((XS0, tuple(s2 + Vector((-0.2, -0.62, -0.32)))), (XS1, tuple(s2 + Vector((-0.12, -0.5, -0.12))))))
interp(c, "LINEAR", "location")
# 13 soat: makro, STOP da silkinish
kT = empty("clockT", tuple(CLK + Vector((0, -0.03, 0))))
c = shot_cam("clock", (0, 0, 0), kT, 50, 4.0, focus=kT, clip=0.005)
path_keys(c, ((CL0, tuple(CLK + Vector((0.3, -1.15, -0.15)))), (STOP, tuple(CLK + Vector((0.12, -0.9, -0.06)))), (CL1, tuple(CLK + Vector((0.1, -0.85, -0.05))))))
lens_keys(c, ((CL0, 30), (STOP - 1, 34), (STOP + 2, 48), (CL1, 52)))
shake(c, STOP, STOP + 12, 0.012, 13)
# 14 hazm: crash zoom, qizil
hT = empty("digestT", tuple(SEC + Vector((0.0, -0.2, Z_CELLT - 0.05))))
c = shot_cam("digest", (0, 0, 0), hT, 22, 4.0, focus=hT)
path_keys(c, ((DG0, tuple(SEC + Vector((-0.55, -1.75, 1.45)))), (DG1, tuple(SEC + Vector((-0.35, -1.35, 1.2))))))
lens_keys(c, ((DG0, 20), (DG0 + 3, 34), (DG0 + 6, 44), (DG1, 48)))
shake(c, DG0 + 3, DG1, 0.015, 14, decay=False)
# 15 final: past burchak, XSW da rentgen + crash zoom
fT2 = empty("finalT", (0, 0, 0))
for f in range(FI0, FI1 + 1, 2): key(fT2, f, loc=tuple(hips_world(f, (0.02, 0.22, 0.08))))
b1 = hips_world(FI0, BELLY)
c = shot_cam("final", (0, 0, 0), fT2, 18, 4.0, focus=fT2)
path_keys(c, ((FI0, tuple(b1 + Vector((0.55, -1.25, -0.6)))), (XSW, tuple(b1 + Vector((0.42, -1.0, -0.48)))), (FI1, tuple(b1 + Vector((0.3, -0.8, -0.35))))))
lens_keys(c, ((FI0, 17), (XSW - 1, 20), (XSW + 2, 26), (FI1, 28)))
shake(c, FI0 + 4, FI0 + 18, 0.03, 15); shake(c, XSW, XSW + 12, 0.02, 16)
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
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(120)); L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
bg_sky = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_sky.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.002, 0.004, 0.012, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_sky.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WCOL = {"x": (0.002, 0.004, 0.012), "lab": (0.0006, 0.0008, 0.001), "cave": (0.02, 0.003, 0.003), "sec": (0.002, 0.01, 0.004)}
KIND = {"hook": "room", "think": "room", "days": "room", "clock": "room", "final": "room", "xacid": "x", "xwall": "x", "xshield": "x",
        "blade": "lab", "cave": "cave", "mucus": "sec", "armor": "sec", "erode": "sec", "regrow": "sec", "digest": "sec"}
def set_world(f, kind):
    s1, s2 = (0.35, 0.0) if kind == "room" else (0.0, 1.0)
    for bgn, v in ((bg_sky, s1), (bg_dk, s2)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
    bg_dk.inputs[0].default_value = (*WCOL.get(kind, (0, 0, 0)), 1); bg_dk.inputs[0].keyframe_insert("default_value", frame=f)
for f, n in SHOTS: set_world(f, KIND[n])
set_world(XSW, "x")
interp(w.node_tree, "CONSTANT")
# xona: deraza quyoshi + iliq to'ldiruvchi
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.0); sun.data.color = (1.0, 0.9, 0.78); sun.rotation_euler = (R(55), 0, R(-62))
for f, e in lights_for(ROOM_SHOTS, 3.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
for f in range(DA0, DA1 + 1, 8):
    for ff, e, col in ((f, 4.5, (1.0, 0.85, 0.65)), (f + 4, 0.05, (0.4, 0.5, 1.0))):
        sun.data.energy = e; sun.data.keyframe_insert("energy", frame=ff)
        sun.data.color = col; sun.data.keyframe_insert("color", frame=ff)
sun.data.energy = 0; sun.data.keyframe_insert("energy", frame=DA1 + 1); sun.data.color = (1.0, 0.9, 0.78); sun.data.keyframe_insert("color", frame=DA1 + 1)
sun.data.energy = 3.5; sun.data.keyframe_insert("energy", frame=CL0); sun.data.energy = 0.0; sun.data.keyframe_insert("energy", frame=CL1 + 1)
sun.data.energy = 3.5; sun.data.keyframe_insert("energy", frame=FI0); sun.data.energy = 0.0; sun.data.keyframe_insert("energy", frame=XSW)
interp(sun.data, "CONSTANT")
chestT = empty("chestT", (STAND[0], STAND[1] - 0.1, 1.0))
area("room_key", (-0.6, -0.9, 2.3), 1.5, (1.0, 0.88, 0.75), lights_for(ROOM_SHOTS, 260.0), target=chestT)
area("room_fill", (2.2, -0.6, 1.4), 1.2, (0.85, 0.9, 1.0), lights_for(ROOM_SHOTS, 90.0), target=chestT)
area("room_rim", (0.4, 2.1, 2.2), 0.8, (1.0, 0.75, 0.5), lights_for(ROOM_SHOTS, 140.0), target=chestT)
point("lamp_light", (1.05, 1.9, 1.5), 0.15, (1.0, 0.7, 0.4), lights_for(ROOM_SHOTS, 60.0))
area("clock_key", tuple(CLK + Vector((-0.4, -0.7, 0.5))), 0.6, (1.0, 0.92, 0.85), lights_for(rng("clock"), 40.0), target=kT)
area("clock_red", tuple(CLK + Vector((0.5, -0.5, -0.2))), 0.6, (1.0, 0.05, 0.02), [(1, 0), (STOP, 0), (STOP + 1, 45), (STOP + 6, 15), (CL1 + 1, 0)], target=kT)
area("final_red", (STAND[0] + 0.9, STAND[1] - 0.9, 0.6), 1.0, (1.0, 0.06, 0.03), [(1, 0), (FI0 + 6, 500), (FI0 + 10, 150), (XSW, 0)], target=chestT)
# rentgen
area("x_rim", (STAND[0] - 0.8, STAND[1] + 1.4, 1.5), 1.0, (0.3, 0.6, 1.0), lights_for(X_SHOTS, 30.0), target=chestT)
area("x_key", (STAND[0] + 0.6, STAND[1] - 0.8, 1.4), 0.8, (1.0, 0.92, 0.88), lights_for(X_SHOTS, 18.0), target=chestT)
area("x_red", (STAND[0] + 0.4, STAND[1] - 0.6, 1.1), 0.8, (1.0, 0.08, 0.03), [(1, 0), (XSW, 60), (END + 1, 0)], target=chestT)
# laboratoriya
area("lab_strip", tuple(LAB + Vector((-0.25, 0.25, 0.25))), 1.0, (0.9, 0.95, 1.0), lights_for(LAB_SHOTS, 15.0), target=lT, shape=(0.6, 0.06), cam_vis=False)
area("lab_strip2", tuple(LAB + Vector((0.3, 0.2, 0.15))), 1.0, (0.6, 1.0, 0.5), lights_for(LAB_SHOTS, 25.0), target=lT, shape=(0.5, 0.05))
area("lab_top", tuple(LAB + Vector((-0.1, 0.12, 0.45))), 0.8, (1.0, 0.97, 0.9), lights_for(LAB_SHOTS, 20.0), target=lT)
point("lab_glow", tuple(LAB + Vector((0.03, -0.03, 0.02))), 0.01, (0.4, 1.0, 0.15), lights_for(LAB_SHOTS, 0.15))
point("lab_flash", tuple(LAB + Vector((0.01, -0.02, SURF + 0.01))), 0.01, (0.6, 1.0, 0.4), [(1, 0), (IMPACT, 25), (IMPACT + 3, 6), (IMPACT + 8, 0)], const=False)
# g'or
area("cave_key", tuple(CAVE + Vector((-1.0, -0.6, 0.6))), 1.2, (1.0, 0.85, 0.8), lights_for(CAVE_SHOTS, 60.0), target=cT)
area("cave_key2", tuple(CAVE + Vector((1.2, -0.5, 0.6))), 1.0, (1.0, 0.7, 0.65), lights_for(CAVE_SHOTS, 40.0), target=mT)
point("cave_pool", tuple(CAVE + Vector((0.2, 0, POOL_Z + 0.25))), 0.6, (0.4, 1.0, 0.15), lights_for(CAVE_SHOTS, 90.0))
point("cave_pool2", tuple(CAVE + Vector((-1.6, 0, POOL_Z + 0.25))), 0.6, (0.4, 1.0, 0.15), lights_for(CAVE_SHOTS, 70.0))
point("cave_blue", tuple(WALLP - d_ * 0.3), 0.2, (0.3, 0.6, 1.0), [(1, 0), (MU0, 0), (MU0 + 3, 8), (MU1 + 1, 0)], const=False)
# kesim
area("sec_key", tuple(SEC + Vector((-1.2, -2.2, 2.4))), 2.0, (1.0, 0.92, 0.88), lights_for(SEC_SHOTS, 170.0), target=gT)
area("sec_rim", tuple(SEC + Vector((1.4, 1.6, 1.8))), 1.5, (0.4, 1.0, 0.3), lights_for(SEC_SHOTS, 260.0), target=gT)
area("sec_fill", tuple(SEC + Vector((1.8, -1.6, 0.6))), 1.2, (0.55, 0.7, 1.0), lights_for(SEC_SHOTS, 110.0), target=gT)
area("sec_red", tuple(SEC + Vector((0.6, -1.4, 1.6))), 1.4, (1.0, 0.06, 0.02),
     [(1, 0), (ER0 + 30, 0), (ER0 + 34, 160), (ER1 + 1, 0), (DG0, 450), (DG0 + 4, 200), (DG0 + 12, 500), (DG0 + 18, 220), (DG0 + 28, 520), (DG1 + 1, 0)], target=gT)
area("sec_blue", tuple(SEC + Vector((0, -0.6, 1.6))), 1.4, (0.3, 0.6, 1.0), [(1, 0), (ZIRH, 0), (ZIRH + 1, 300), (ZIRH + 8, 0)], target=gT)

# ======================================================================
# 8) RENDER
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
