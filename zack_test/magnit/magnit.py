# "Ikkita magnitni yutib yuborsang nima bo'ladi?" — Zack D. Films uslubida 54.2 s video (1302 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, muzlash/muzlash.py, burish/parts.py. Kadr rejasi: STORYBOARD.md
# Assetlar: zack_test/tools/get_magnit.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/magnit/magnit.py --render
# Sinov: FRAMES=20,80,240,520,940 PCT=30
import bpy, math, sys, os, random
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
END = 1302
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (35, "swallow"), (100, "xthroat"), (139, "calm"), (201, "xtravel"), (282, "xsplit"), (323, "loops"),
         (394, "pain"), (457, "pull"), (542, "squeeze"), (613, "dying"), (697, "days"), (737, "hole"), (798, "leak"),
         (863, "inflame"), (926, "gurney"), (1014, "surgery"), (1064, "one"), (1148, "two"), (1246, "kids")]
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

ROOM_SHOTS = rng("hook", "swallow", "calm", "pain", "days", "kids")
X_SHOTS = rng("xthroat", "xtravel", "xsplit", "inflame")
GUT_SHOTS = rng("loops", "pull", "squeeze", "dying", "hole", "leak")
HOSP_SHOTS = rng("gurney", "surgery")
MAG_SHOTS = rng("one", "two")

# ======================================================================
# 1) MEHMONXONA (0,0,0)
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
# deraza (chap devorda): osmon ko'rinadi + quyosh nuri
win_glass = mat("win_sky", (0.75, 0.85, 1.0), 0.0, emit=3.0)
plane("window", (1.4, 1.5), (-2.39, 0.6, 1.5), win_glass, rot=(90, 0, 90), parent=room)
frame_m = mat("win_frame", (0.95, 0.95, 0.95), 0.35)
for dz in (-0.76, 0.76):
    box("wframe", (0.08, 1.5, 0.06), (-2.36, 0.6, 1.5 + dz), frame_m, parent=room)
for dy in (-0.73, 0.0, 0.73):
    box("wframe", (0.08, 0.06, 1.55), (-2.36, 0.6 + dy, 1.5), frame_m, parent=room)
# gilam
rug_m = bpy.data.materials.new("rug"); rug_m.use_nodes = True
N = rug_m.node_tree.nodes; L = rug_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 300; L.new(tc.outputs["Object"], nz.inputs[0])
wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; L.new(tc.outputs["Object"], wv.inputs[0])
cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.55, 0.18, 0.12, 1); cr.color_ramp.elements[1].color = (0.85, 0.7, 0.5, 1)
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
plane("rug", (2.6, 1.8), (0.1, 0.7, 0.004), rug_m, parent=room)
# Poly Haven mebel
sofaR = empty("sofaR", (0, 1.85, 0), room); import_gltf(PH + "Sofa_01/Sofa_01.gltf", sofaR)
sofaR.scale = (1.15, 1.15, 1.0)
tableR = empty("tableR", (0, 0.85, 0), room); tableR.rotation_euler = (0, 0, R(90))
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", tableR)
plantR = empty("plantR", (-1.55, 1.85, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR)
plantR2 = empty("plantR2", (1.6, 1.95, 0), room); plantR2.scale = (0.8, 0.8, 0.8); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantR2)
picR = empty("picR", (0.0, 2.24, 1.55), room); picR.scale = (1.6, 1.6, 1.6); import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR)
picR2 = empty("picR2", (-0.9, 2.24, 1.35), room); picR2.scale = (1.0, 1.0, 1.0); import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", picR2)
# torshеr (pol chirog'i)
lamp_m = mat("lamp_shade", (1.0, 0.85, 0.6), 0.6, emit=2.5, emit_col=(1.0, 0.75, 0.45))
cyl("lamp_pole", 0.015, 1.5, (1.05, 1.9, 0.75), mat("lamp_pole_m", (0.1, 0.1, 0.1), 0.3, metal=0.8), parent=room)
cyl("lamp_shade", 0.18, 0.28, (1.05, 1.9, 1.55), lamp_m, parent=room)
cyl("lamp_base", 0.14, 0.03, (1.05, 1.9, 0.015), mat("lamp_base_m", (0.1, 0.1, 0.1), 0.3, metal=0.8), parent=room)
TABLE_Z = 0.395

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

SOFA = (0, 1.66, 0.0)                       # o'tirish joyi (root)
SOFA_Z = -0.02
LIE = (0.05, 1.68, -0.5)                    # divanda yotish (root), boshi +X tomonda
HOSP = Vector((40, 0, 0)); OR0 = Vector((40, 14, 0))
GZ = 0.92                                    # zambil matrasi balandligi
G_X0, G_X1 = HOSP.x - 1.0, HOSP.x + 4.2      # zambil harakati (gurney kadri)
def place(root, f, loc, rot=0.0, scale=1.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
    for p in ("location", "rotation_euler", "scale"): root.keyframe_insert(p, frame=f)
GU0, GU1 = S["gurney"]; SU0, SU1 = S["surgery"]
place(mroot, 1, (SOFA[0], SOFA[1], SOFA_Z), rot=180)          # Sitting_Drinking o'tirishda 180° buriladi
place(mroot, S["calm"][0], (SOFA[0], SOFA[1], SOFA_Z))
place(mroot, S["pain"][0], (1.05, 1.15, 0), rot=-15)
place(mroot, S["pain"][1] + 1, (SOFA[0], SOFA[1], SOFA_Z))
place(mroot, S["days"][0], LIE, rot=-90)
place(mroot, S["hole"][0], (SOFA[0], SOFA[1], SOFA_Z))
place(mroot, S["inflame"][0], LIE, rot=-90)
place(mroot, GU0, (G_X0, HOSP.y, GZ + 0.06), rot=-90)
interp(mroot, "CONSTANT")
place(mroot, GU1, (G_X1, HOSP.y, GZ + 0.06), rot=-90)
for fc in fcurves(mroot):
    for k in fc.keyframe_points:
        if GU0 <= k.co.x < GU1: k.interpolation = "LINEAR"
place(mroot, SU0, (OR0.x, OR0.y, GZ + 0.06), rot=-90)
place(mroot, SU1 + 1, (0.95, 0.75, 0.0), rot=-20, scale=0.62)       # "bola" — polda o'tiradi (kids)
for fc in fcurves(mroot):
    for k in fc.keyframe_points:
        if not (GU0 <= k.co.x < GU1): k.interpolation = "CONSTANT"

mc.add_strip(meg, A_("Sitting_Idle_3.fbx"), -60, blend=0, repeat=16.0)
def strip(arm, act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
DRINK_MOUTH = 300                           # Sitting_Drinking: o'ng qo'l og'izda (asl kadr)
SW0, SW1 = S["swallow"]
strip(meg, A_("Sitting_Drinking.fbx"), 80 - (DRINK_MOUTH - 150) * 0.8, src=(150, 362), blend=0, bout=8)
strip(meg, A_("Sitting_Laughing.fbx"), S["calm"][0] - 8, src=(30, 201), blend=8, bout=8)
strip(meg, A_("Big_Stomach_Hit.fbx"), S["pain"][0] + 2, src=(1, 34), speed=0.45, blend=0, bout=0)
strip(meg, A_("Laying_Moaning.fbx"), S["days"][0] - 4, blend=0, bout=0, repeat=4.0)
strip(meg, A_("Laying_Moaning.fbx"), S["inflame"][0] - 4, blend=0, bout=0, repeat=6.0)
strip(meg, A_("Laying_3.fbx"), GU0 - 4, blend=0, bout=0, repeat=2.0)
strip(meg, A_("Sitting_Idle.fbx"), S["kids"][0] - 4, blend=0, bout=0)
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.09, 0.08), headE)
hipsE = child_of_bone("meg_hips", meg, "Hips")
handE = child_of_bone("meg_rhand", meg, "RightHand")

# ---- magnitlar: stol ustida (ilgak) va qo'lda (yutish) ----
mag_m = chrome("magnet", (0.78, 0.79, 0.82))
MR = 0.0065
HO0, HO1 = S["hook"]
SNAP1 = 19
tm = [sphere(f"tmag{i}", MR, (0, 0, 0), mag_m, sub=4) for i in range(2)]
for i, s_ in enumerate(tm):
    sgn = -1 if i == 0 else 1
    for f, dx in ((1, 0.045), (10, 0.03), (SNAP1 - 2, 0.012), (SNAP1, MR)):
        key(s_, f, loc=(sgn * dx, 0.78, TABLE_Z + MR))
    s_.rotation_euler = (0, R(sgn * 0), 0)
    key(s_, 1, rot=(0, 0, 0)); key(s_, SNAP1, rot=(0, sgn * -260, 0))
    vis(s_, rng("hook"))
hm = []
for i in range(2):
    s_ = sphere(f"hmag{i}", MR, (0.0, 0.0, 0.0), mag_m, sub=4, parent=handE, world=False)
    s_.location = (0.012 * (1 if i else -1) + 0.0, 0.085, 0.035)
    hm.append(s_); vis(s_, rng("swallow"))

# ---- rentgen nusxa + organlar (Hips fazosi: X chap, Y tepa, Z old) ----
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.2, base=0.012)
ghosts = []
for o in mmeshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, X_SHOTS, recursive=False)
for o in mmeshes: vis(o, [(1, END)] and [(a, b) for a, b in
                         [(1, S["xthroat"][0] - 1), (S["calm"][0], S["xtravel"][0] - 1), (S["loops"][0], S["inflame"][0] - 1),
                          (S["gurney"][0], END)]], recursive=False)
org = empty("organs", (0, 0, 0), hipsE)
def organ_mat(name, col, emit=0.35):
    m = mat(name, col, 0.3, sss=0.4, sss_scale=0.005, coat=0.8, emit=emit)
    nm = m.node_tree.nodes; b = nm["Principled BSDF"]
    lw = nm.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    mm_ = nm.new("ShaderNodeMath"); mm_.operation = "MULTIPLY"; mm_.inputs[1].default_value = emit * 2.5
    m.node_tree.links.new(lw.outputs["Facing"], mm_.inputs[0]); m.node_tree.links.new(mm_.outputs[0], b.inputs["Emission Strength"])
    tr = nm.new("ShaderNodeBsdfTransparent"); mx = nm.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.5
    m.node_tree.links.new(b.outputs[0], mx.inputs[1]); m.node_tree.links.new(tr.outputs[0], mx.inputs[2])
    m.node_tree.links.new(mx.outputs[0], nm["Material Output"].inputs["Surface"])
    return m
eso_m = organ_mat("eso_m", (0.85, 0.42, 0.42))
sto_m = organ_mat("sto_m", (0.9, 0.5, 0.48))
si_m = organ_mat("si_m", (0.95, 0.6, 0.55))
co_m = organ_mat("co_m", (0.78, 0.45, 0.38))
infl_val = value_node(si_m, "infl", 0.0)
for m_ in (si_m, co_m):
    nm = m_.node_tree.nodes; b = nm["Principled BSDF"]
    if m_ is co_m: infl_val = value_node(co_m, "infl", 0.0)
    mx = nm.new("ShaderNodeMix"); mx.data_type = "RGBA"; m_.node_tree.links.new(nm["infl"].outputs[0], mx.inputs["Factor"])
    mx.inputs[6].default_value = b.inputs["Base Color"].default_value[:]; mx.inputs[7].default_value = (1.0, 0.08, 0.03, 1)
    m_.node_tree.links.new(mx.outputs[2], b.inputs["Base Color"]); m_.node_tree.links.new(mx.outputs[2], b.inputs["Emission Color"])
ESO = [(0.0, 0.50, 0.0), (0.0, 0.44, 0.01), (0.005, 0.38, 0.025), (0.015, 0.33, 0.035), (0.03, 0.295, 0.045)]
STO = [(0.03, 0.295, 0.045), (0.06, 0.275, 0.055), (0.075, 0.235, 0.06), (0.065, 0.19, 0.065), (0.03, 0.17, 0.065),
       (-0.01, 0.175, 0.06), (-0.035, 0.185, 0.055)]
SI = [(-0.035, 0.185, 0.055), (-0.06, 0.165, 0.06)]
ROWS = 6; RY0 = 0.14; RDY = 0.028
for r in range(ROWS):
    y = RY0 - r * RDY
    xs = [-0.07, -0.035, 0.0, 0.035, 0.07]
    if r % 2: xs = xs[::-1]
    for j, x in enumerate(xs):
        SI.append((x, y + 0.004 * math.sin(j * 1.7 + r), 0.07 + 0.008 * math.sin(j * 2.3 + r * 1.3)))
SI += [(0.075, RY0 - ROWS * RDY + 0.01, 0.06), (0.09, RY0 - ROWS * RDY - 0.005, 0.05)]
COLON = [(-0.105, -0.03, 0.045), (-0.11, 0.08, 0.05), (-0.105, 0.17, 0.055), (-0.05, 0.205, 0.065), (0.02, 0.2, 0.07),
         (0.085, 0.2, 0.06), (0.11, 0.15, 0.05), (0.11, 0.05, 0.05), (0.105, -0.03, 0.045), (0.05, -0.065, 0.035), (0.0, -0.075, 0.02)]
eso = P.tube("esophagus", catmull(ESO, 0.01), 0.008, eso_m, org)
sto_pts = catmull(STO, 0.008)
sto_tp = [0.3 + 0.7 * math.sin(math.pi * min(1.0, max(0.0, i / (len(sto_pts) - 1)))) ** 0.6 for i in range(len(sto_pts))]
sto = P.tube("stomach", sto_pts, 0.042, sto_m, org, taper=sto_tp)
si_pts = catmull(SI, 0.004)
si = P.tube("small_int", si_pts, 0.0105, si_m, org)
colon = P.tube("colon", catmull(COLON, 0.01), 0.017, co_m, org)
# quvur (tube) GN aniqligi
tg = P.tube_group()
for n in tg.nodes:
    if n.bl_idname == "GeometryNodeResampleCurve": n.inputs["Count"].default_value = 220
    if n.bl_idname == "GeometryNodeCurvePrimitiveCircle": n.inputs["Resolution"].default_value = 28
vis(org, X_SHOTS)
# magnitlar tanada: yo'l = qizilo'ngach + me'da + ingichka ichak
BODY_PATH = catmull(ESO, 0.003)[:-1] + catmull(STO, 0.003)[:-1] + si_pts
cum = [0.0]
for i in range(1, len(BODY_PATH)): cum.append(cum[-1] + (BODY_PATH[i] - BODY_PATH[i - 1]).length)
def at_s(s):
    s = max(0.0, min(cum[-1], s))
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cum[mid] <= s: lo = mid
        else: hi = mid
    t = (s - cum[lo]) / max(1e-9, cum[hi] - cum[lo])
    return BODY_PATH[lo].lerp(BODY_PATH[hi], t)
def s_near(p):
    i = min(range(len(BODY_PATH)), key=lambda k: (BODY_PATH[k] - Vector(p)).length); return cum[i]
S_ESO_END = s_near(ESO[-1]); S_STO_END = s_near(STO[-1])
S_A = s_near((0.0, RY0 - 2 * RDY, 0.07)); S_B = s_near((0.0, RY0 - 3 * RDY, 0.07))
bm_m = chrome("bmag", (0.8, 0.82, 0.86), glow=5.0, glow_col=(0.6, 0.85, 1.0))
bmag = [sphere(f"bmag{i}", 0.0062, (0, 0, 0), bm_m, sub=4, parent=org, world=False) for i in range(2)]
XT0, XT1 = S["xthroat"]; XV0, XV1 = S["xtravel"]; XS0, XS1 = S["xsplit"]; IN0, IN1 = S["inflame"]
def mag_track(o, keys):
    for f, s in keys: key(o, f, loc=tuple(at_s(s)))
    # oraliq kadrlarni yo'l bo'ylab to'ldirish
    ks = sorted(keys)
    for (f0, s0), (f1, s1) in zip(ks, ks[1:]):
        for f in range(f0 + 1, f1):
            t = ease((f - f0) / (f1 - f0)); key(o, f, loc=tuple(at_s(s0 + (s1 - s0) * t)))
mag_track(bmag[0], [(XT0, 0.0), (XT1, S_ESO_END + 0.02), (XV0, S_ESO_END + 0.03), (XV1, S_A - 0.03), (XS0 + 22, S_A)])
mag_track(bmag[1], [(XT0, -0.02), (XT1, S_ESO_END - 0.02), (XV0, S_ESO_END), (XV1, S_A - 0.08), (XS0 + 30, S_B)])
# yallig'lanish (inflame): qorin ichida qizil "olov"
for i, b_ in enumerate(bmag):
    mid = (at_s(S_A) + at_s(S_B)) / 2
    key(b_, IN0, loc=tuple(mid + Vector((0, 0.0065 * (1 if i == 0 else -1), 0))))
for b_ in bmag:
    for fc in fcurves(b_):
        if fc.data_path == "location":
            for k in fc.keyframe_points:
                if k.co.x >= IN0 - 1: k.interpolation = "CONSTANT"
    vis(b_, X_SHOTS, recursive=False)
infl_m = mat("infl_glow", (1.0, 0.1, 0.03), emit=0.0, alpha=0.5)
inb = infl_m.node_tree.nodes["Principled BSDF"]
infl = sphere("infl_glow", 0.1, (0.0, 0.06, 0.06), infl_m, scale=(1.1, 0.8, 0.45), parent=org, world=False)
for f in range(IN0, IN1 + 1, 10):
    inb.inputs["Emission Strength"].default_value = 3.0; inb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    inb.inputs["Emission Strength"].default_value = 9.0; inb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 5)
vis(infl, rng("inflame"), recursive=False)
for m_ in (si_m, co_m):
    val_key(m_, "infl", 1, 0.0); val_key(m_, "infl", IN0 - 1, 0.0); val_key(m_, "infl", IN0, 0.3); val_key(m_, "infl", IN1, 0.85)

# ======================================================================
# 3) SHIFOKORLAR (Josh, Kate) — kasalxona
# ======================================================================
scrub_m = mat("scrubs", (0.12, 0.42, 0.45), 0.8, sss=0.0)
cap_m = mat("cap", (0.15, 0.48, 0.52), 0.85)
def doctor(name, file):
    root, arm, meshes = mc.load_character(name, file); sc.render.fps = 24
    soften(meshes)
    for o in meshes:
        if any(k in o.name for k in ("Shirt", "Pants", "Suit", "Belt")):
            for slot in o.material_slots: slot.link = "OBJECT"; slot.material = scrub_m
    return root, arm, meshes
jroot, josh, jmesh = doctor("josh", "Josh.fbx")
kroot, kate, kmesh = doctor("kate", "Kate.fbx")
mc.add_strip(josh, A_("Walking.fbx"), GU0 - 30, blend=0, repeat=6.0)
mc.add_strip(kate, A_("Female_Walk.fbx"), GU0 - 30, blend=0, repeat=12.0)
strip(josh, A_("Bartending.fbx"), SU0 - 4, src=(40, 200), blend=0, bout=0)
strip(kate, A_("Looking_Down.fbx"), SU0 - 4, blend=0, bout=0)
# zambil bilan birga yuradi
place(jroot, 1, (G_X0 - 1.35, HOSP.y + 0.05, 0), rot=90)
place(jroot, GU0, (G_X0 - 1.35, HOSP.y + 0.05, 0), rot=90)
place(jroot, GU1, (G_X1 - 1.35, HOSP.y + 0.05, 0), rot=90)
place(jroot, SU0, (OR0.x + 0.1, OR0.y + 0.62, 0), rot=0)
place(kroot, 1, (G_X0 + 0.3, HOSP.y + 0.8, 0), rot=90)
place(kroot, GU0, (G_X0 + 0.3, HOSP.y + 0.8, 0), rot=90)
place(kroot, GU1, (G_X1 + 0.3, HOSP.y + 0.8, 0), rot=90)
place(kroot, SU0, (OR0.x - 0.15, OR0.y - 0.62, 0), rot=180)
for r_ in (jroot, kroot):
    for fc in fcurves(r_):
        for k in fc.keyframe_points: k.interpolation = "LINEAR" if GU0 <= k.co.x < GU1 else "CONSTANT"
# qalpoqlar
for nm_, arm_ in (("josh", josh), ("kate", kate)):
    hE = child_of_bone(nm_ + "_head", arm_, "Head")
    cp = sphere(nm_ + "_cap", 0.105, (0, 0.105, -0.005), cap_m, scale=(1.0, 0.75, 1.08), sub=3, parent=hE, world=False)
    vis(cp, HOSP_SHOTS, recursive=False)
for o in jmesh + kmesh:
    vis(o, HOSP_SHOTS, recursive=False)
    if "Hair" in o.name: vis(o, [], recursive=False)

# ======================================================================
# 4) KASALXONA YO'LAGI (40,0,0) va OPERATSIYA XONASI (40,14,0)
# ======================================================================
hosp = empty("hosp", (0, 0, 0))
hfloor = pbr("hfloor", "concrete_pavement", 0.6, tint=(0.85, 0.9, 0.88))
hb = hfloor.node_tree.nodes["Principled BSDF"]
for l in list(hb.inputs["Roughness"].links): hfloor.node_tree.links.remove(l)
hb.inputs["Roughness"].default_value = 0.18
hwall = mat("hwall", (0.78, 0.86, 0.84), 0.6)
plane("hfloor", (24, 3.0), (HOSP.x + 4, HOSP.y, 0), hfloor, parent=hosp)
plane("hwall_l", (24, 3), (HOSP.x + 4, HOSP.y + 1.5, 1.5), hwall, rot=(90, 0, 0), parent=hosp)
plane("hwall_r", (24, 3), (HOSP.x + 4, HOSP.y - 1.5, 1.5), hwall, rot=(-90, 0, 0), parent=hosp)
plane("hceil", (24, 3.0), (HOSP.x + 4, HOSP.y, 2.8), mat("hceil_m", (0.9, 0.92, 0.92), 0.7), rot=(180, 0, 0), parent=hosp)
hpanel = mat("hpanel", (1, 1, 1), 0.5, emit=9.0, emit_col=(0.92, 0.97, 1.0))
for i in range(12):
    plane("hlight", (0.5, 1.1), (HOSP.x - 6 + i * 2.0, HOSP.y, 2.79), hpanel, rot=(180, 0, 0), parent=hosp)
rail_m = mat("rail", (0.6, 0.62, 0.65), 0.25, metal=0.9)
box("hrail_l", (24, 0.04, 0.12), (HOSP.x + 4, HOSP.y + 1.47, 0.95), mat("hrail_w", (0.35, 0.55, 0.6), 0.5), parent=hosp)
box("hrail_r", (24, 0.04, 0.12), (HOSP.x + 4, HOSP.y - 1.47, 0.95), mat("hrail_w2", (0.35, 0.55, 0.6), 0.5), parent=hosp)
door_m = mat("hdoor", (0.55, 0.7, 0.75), 0.4)
for i in range(4):
    box("hdoor", (1.2, 0.04, 2.1), (HOSP.x - 3 + i * 4.5, HOSP.y + 1.48, 1.05), door_m, parent=hosp)
    box("hdoor2", (1.2, 0.04, 2.1), (HOSP.x - 1 + i * 4.5, HOSP.y - 1.48, 1.05), door_m, parent=hosp)
# zambil (gurney)
gur = empty("gurney", (0, 0, 0))
sheet_m = mat("sheet", (0.92, 0.94, 0.96), 0.7, sss=0.2)
blanket_m = mat("blanket", (0.55, 0.72, 0.85), 0.85)
box("mattress", (2.0, 0.7, 0.12), (0, 0, GZ - 0.06), sheet_m, parent=gur)
box("gframe", (2.05, 0.74, 0.05), (0, 0, GZ - 0.15), rail_m, parent=gur)
for dx in (-0.9, 0.9):
    for dy in (-0.3, 0.3):
        cyl("gleg", 0.02, GZ - 0.25, (dx, dy, (GZ - 0.15) / 2 + 0.05), rail_m, parent=gur)
        cyl("gwheel", 0.06, 0.04, (dx, dy, 0.06), mat("gwheel_m", (0.05, 0.05, 0.05), 0.5), rot=(90, 0, 0), parent=gur)
box("blanket", (1.25, 0.72, 0.16), (-0.45, 0, GZ + 0.1), blanket_m, parent=gur)
key(gur, 1, loc=(G_X0, HOSP.y, 0)); key(gur, GU0, loc=(G_X0, HOSP.y, 0)); key(gur, GU1, loc=(G_X1, HOSP.y, 0))
interp(gur, "LINEAR", "location")
# operatsiya xonasi
orr = empty("orroom", (0, 0, 0))
tile = bpy.data.materials.new("tile"); tile.use_nodes = True
N = tile.node_tree.nodes; L = tile.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 8.0
br.inputs["Color1"].default_value = (0.35, 0.62, 0.62, 1); br.inputs["Color2"].default_value = (0.38, 0.66, 0.66, 1)
br.inputs["Mortar"].default_value = (0.8, 0.85, 0.85, 1); br.inputs["Mortar Size"].default_value = 0.015; br.offset = 0.0
L.new(tc.outputs["Object"], br.inputs["Vector"]); L.new(br.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.2
plane("orfloor", (8, 8), tuple(OR0), mat("orfloor_m", (0.3, 0.42, 0.42), 0.25), parent=orr)
for (dx, dy, rz) in ((0, 3.5, 0), (0, -3.5, 180), (3.5, 0, -90), (-3.5, 0, 90)):
    plane("orwall", (8, 3.2), tuple(OR0 + Vector((dx, dy, 1.6))), tile, rot=(90, 0, rz), parent=orr)
plane("orceil", (8, 8), tuple(OR0 + Vector((0, 0, 3.2))), mat("orceil_m", (0.85, 0.9, 0.9), 0.6), rot=(180, 0, 0), parent=orr)
box("ortable", (2.0, 0.6, 0.1), tuple(OR0 + Vector((0, 0, GZ - 0.06))), mat("ortable_m", (0.15, 0.2, 0.22), 0.4), parent=orr)
cyl("orbase", 0.15, GZ - 0.1, tuple(OR0 + Vector((0, 0, (GZ - 0.1) / 2))), rail_m, parent=orr)
drape_m = mat("drape", (0.12, 0.38, 0.55), 0.9)
box("drape", (1.45, 0.95, 0.22), tuple(OR0 + Vector((-0.38, 0, GZ + 0.1))), drape_m, parent=orr)
box("drape_hang", (1.45, 0.02, 0.5), tuple(OR0 + Vector((-0.38, 0.47, GZ - 0.05))), drape_m, parent=orr)
box("drape_hang2", (1.45, 0.02, 0.5), tuple(OR0 + Vector((-0.38, -0.47, GZ - 0.05))), drape_m, parent=orr)
# jarrohlik chirog'i
orlamp_m = mat("orlamp", (1, 1, 1), 0.3, emit=0.0, emit_col=(0.95, 0.98, 1.0))
olb = orlamp_m.node_tree.nodes["Principled BSDF"]
for f, v in ((1, 0.3), (SU0 + 4, 0.3), (SU0 + 6, 60.0), (SU0 + 10, 25.0)):
    olb.inputs["Emission Strength"].default_value = v; olb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
for dx, dy in ((-0.35, -0.3), (0.35, 0.3)):
    c_ = OR0 + Vector((dx, dy, 2.15))
    cyl("orlamp_house", 0.36, 0.14, tuple(c_ + Vector((0, 0, 0.08))), mat("orlamp_h", (0.85, 0.87, 0.88), 0.3, metal=0.4), parent=orr)
    cyl("orlamp_face", 0.32, 0.02, tuple(c_), orlamp_m, parent=orr)
    cyl("orlamp_arm", 0.025, 1.0, tuple(c_ + Vector((0, 0, 0.6))), rail_m, parent=orr)
mon_m = mat("monitor", (0.02, 0.02, 0.02), 0.2)
box("monitor", (0.05, 0.45, 0.32), tuple(OR0 + Vector((1.4, 0.9, 1.5))), mon_m, parent=orr)
plane("monitor_scr", (0.42, 0.28), tuple(OR0 + Vector((1.37, 0.9, 1.5))), mat("mon_scr", (0.1, 1.0, 0.4), 0.3, emit=2.5), rot=(90, 0, 90), parent=orr)
cyl("monpole", 0.02, 1.4, tuple(OR0 + Vector((1.45, 0.9, 0.7))), rail_m, parent=orr)
# asboblar stoli
box("tray", (0.6, 0.4, 0.03), tuple(OR0 + Vector((0.2, -1.15, 1.0))), rail_m, parent=orr)
for i in range(6):
    box("tool", (0.18, 0.012, 0.006), tuple(OR0 + Vector((0.05 + i * 0.05 * 0.6, -1.15 + (i - 3) * 0.05, 1.02))), chrome("tool_m"), rot=(0, 0, 80), parent=orr)

# ======================================================================
# 5) ICHAK STUDIYASI (0,60,1) — masshtab x10
# ======================================================================
G0 = Vector((0, 60, 1.0))
gut = empty("gut", tuple(G0))
RT = 0.2
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
HOLE_C = Vector((0.06, -0.17, 0.32))         # yuqori ichak old sirtida (lokal)
gutU_m = gut_material("gut_upper", hole=True); gutL_m = gut_material("gut_lower"); gutBG_m = gut_material("gut_bg")
ZU, ZL = 0.27, -0.27
def loop_pts(z, sgn):
    return [(-2.6, 1.6, z + sgn * 0.7), (-1.8, 0.6, z + sgn * 0.35), (-1.0, 0.12, z + sgn * 0.06), (-0.4, 0.0, z), (0.0, 0.0, z),
            (0.4, 0.0, z), (1.0, 0.12, z + sgn * 0.05), (1.8, 0.7, z + sgn * 0.3), (2.6, 1.7, z + sgn * 0.75)]
gU = P.tube("gutU", loop_pts(ZU, 1), RT, gutU_m, gut); gL = P.tube("gutL", loop_pts(ZL, -1), RT, gutL_m, gut)
# ichidagi narsa (teshikdan ko'rinadi) — o'sha egri chiziq, kichikroq radius
cont_m = mat("contents", (0.28, 0.17, 0.05), 0.25, sss=0.4, sss_scale=0.02, coat=0.8)
gUc = bpy.data.objects.new("gutU_cont", gU.data); sc.collection.objects.link(gUc); gUc.parent = gut
mm_ = gUc.modifiers.new("tube", "NODES"); mm_.node_group = P.tube_group(); gUc["r_id"] = gU["r_id"]; P.set_mod(gUc, "tube", gU["r_id"], RT * 0.82)
gUc.material_slots[0].link = "OBJECT"; gUc.material_slots[0].material = cont_m
# fon: boshqa ichak halqalari + bo'shliq devori
rb = random.Random(5)
for j in range(7):
    y = 1.2 + j * 0.45; z0 = rb.uniform(-1.4, 1.4)
    pts = [(-3.5 + k * 1.0, y + rb.uniform(-0.3, 0.3), z0 + 0.5 * math.sin(k * 1.3 + j)) for k in range(8)]
    P.tube(f"gut_bg{j}", pts, rb.uniform(0.18, 0.26), gutBG_m, gut)
cav_m = mat("cavity", (0.35, 0.08, 0.07), 0.3, sss=0.3, sss_scale=0.05, coat=1.0)
cav = sphere("cavity", 7.0, (0, 0, 0), cav_m, sub=4, parent=gut, world=False); cav.location = (0, 2.0, 0)
# magnitlar ichak ichida
gm_m = chrome("gmag", (0.8, 0.82, 0.86), glow=0.6, glow_col=(0.55, 0.8, 1.0))
gmA = sphere("gmagA", 0.12, (0, 0, ZU), gm_m, sub=4, parent=gut, world=False)
gmB = sphere("gmagB", 0.12, (0, 0, ZL), gm_m, sub=4, parent=gut, world=False)
LO0, LO1 = S["loops"]; PU0, PU1 = S["pull"]; SQ0, SQ1 = S["squeeze"]; DY0, DY1 = S["dying"]; HL0, HL1 = S["hole"]; LK0, LK1 = S["leak"]
SNAP2 = 516                                     # "tortadi" (21.5 s)
ZC = 0.155                                      # yopishgandan keyin markaz balandligi (ichak devori qisiladi)
def gut_pose(f, zu, zl, pinch=1.0):
    for o, z, sgn in ((gU, zu, 1), (gL, zl, -1)):
        sp = o.data.splines[0]
        base = loop_pts(ZU if sgn > 0 else ZL, sgn)
        for i, p in enumerate(base):
            w = {3: 1.0, 4: 1.0, 5: 1.0, 2: 0.55, 6: 0.55, 1: 0.12, 7: 0.12}.get(i, 0.0)
            dz = (z - (ZU if sgn > 0 else ZL)) * w
            sp.points[i].co = (p[0], p[1], p[2] + dz, 1.0); sp.points[i].keyframe_insert("co", frame=f)
            sp.points[i].radius = pinch if i == 4 else (1.0 - (1.0 - pinch) * 0.5 if i in (3, 5) else 1.0)
            sp.points[i].keyframe_insert("radius", frame=f)
    key(gmA, f, loc=(0, 0, zu)); key(gmB, f, loc=(0, 0, zl))
gut_pose(1, ZU, ZL); gut_pose(PU0 + 8, ZU, ZL)
for f in range(PU0 + 10, SNAP2 + 1, 4):
    t = (f - PU0 - 8) / (SNAP2 - PU0 - 8); t = t ** 2.6
    gut_pose(f, ZU - (ZU - ZC) * t, ZL + (ZU - ZC) * t)
gut_pose(SNAP2, ZC, -ZC, 0.92); gut_pose(SNAP2 + 3, ZC - 0.015, -ZC + 0.015, 0.85); gut_pose(SNAP2 + 7, ZC, -ZC, 0.9)
gut_pose(SQ0 + 6, ZC, -ZC, 0.9); gut_pose(SQ1, ZC - 0.02, -ZC + 0.02, 0.72); gut_pose(END, ZC - 0.02, -ZC + 0.02, 0.72)
for o in (gU, gL):
    for fc in mc._fcurves(o.data.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
# magnit maydon chiziqlari (tortishish paytida)
fld_root = empty("fld_root", (0, 0, 0), gut)
fld_m = P.pulse_material("field", (0.35, 0.7, 1.0), base_emit=1.2, pulse_col=(0.6, 0.9, 1.0), width=0.15)
for j in range(8):
    a = j * math.pi / 4; d = Vector((math.cos(a), math.sin(a) * 0.6, 0))
    pts = [tuple(Vector((0, 0, 0.3)) + d * 0.05), tuple(Vector((0, 0, 0.2)) + d * 0.35), tuple(d * 0.5),
           tuple(Vector((0, 0, -0.2)) + d * 0.35), tuple(Vector((0, 0, -0.3)) + d * 0.05)]
    P.tube(f"field{j}", pts, 0.008, fld_m, fld_root)
for f in range(PU0, SNAP2 + 1, 4):
    t = (f - PU0 - 8) / (SNAP2 - PU0 - 8); t = max(0, t) ** 2.6
    key(fld_root, f, scale=(1, 1, (ZU - (ZU - ZC) * t) / ZU))
val_key(fld_m, "pos", 1, -0.2)
for f in range(PU0 + 4, SNAP2, 16): val_key(fld_m, "pos", f, -0.2); val_key(fld_m, "pos", f + 14, 1.2)
val_key(fld_m, "glow", 1, 0.0); val_key(fld_m, "glow", PU0 + 4, 0.0); val_key(fld_m, "glow", PU0 + 16, 1.5)
val_key(fld_m, "glow", SNAP2 - 2, 3.0); val_key(fld_m, "glow", SNAP2 + 6, 0.0)
vis(fld_root, [(PU0, SNAP2 + 8)])
# material animatsiyasi
for m_ in (gutU_m, gutL_m):
    val_key(m_, "xr", 1, 0.85); val_key(m_, "xr", SNAP2 + 10, 0.85); val_key(m_, "xr", SQ0, 0.0)
    val_key(m_, "pale", 1, 0.0); val_key(m_, "pale", SQ0 + 6, 0.0); val_key(m_, "pale", SQ1, 1.0); val_key(m_, "pale", DY1, 0.6)
    val_key(m_, "blood", 1, 1.0); val_key(m_, "blood", SQ0, 1.0); val_key(m_, "blood", SQ1, 0.55); val_key(m_, "blood", DY0 + 50, 0.0)
    val_key(m_, "dead_r", 1, 0.0); val_key(m_, "dead_r", DY0 + 10, 0.0); val_key(m_, "dead_r", DY1, 0.42); val_key(m_, "dead_r", HL1, 0.5)
    val_key(m_, "infl", 1, 0.0); val_key(m_, "infl", LK0 + 30, 0.0); val_key(m_, "infl", LK1, 1.5)
HOLE_T = 760                                    # "teshik" (31.6 s)
val_key(gutU_m, "hole_r", 1, 0.0); val_key(gutU_m, "hole_r", HOLE_T - 4, 0.0); val_key(gutU_m, "hole_r", HOLE_T + 10, 0.07)
val_key(gutU_m, "hole_r", HL1, 0.085); val_key(gutU_m, "hole_r", LK1, 0.1)
vis(gUc, rng("hole", "leak"), recursive=False)
for m_ in (gm_m,):
    pass
vis(gmA, rng("loops", "pull", "squeeze", "dying"), recursive=False); vis(gmB, rng("loops", "pull", "squeeze", "dying"), recursive=False)
# oqib chiqayotgan narsa (metaball "goo" oilasi qo'shilib ketadi)
goo_m = mat("goo", (0.11, 0.075, 0.02), 0.2, sss=0.15, sss_scale=0.01, coat=1.0)
mb0 = bpy.data.metaballs.new("goo"); mb0.resolution = 0.03; mb0.render_resolution = 0.012; mb0.materials.append(goo_m)
gooB = bpy.data.objects.new("goo", mb0); sc.collection.objects.link(gooB); gooB.parent = gut
el = mb0.elements.new(); el.radius = 0.001; gooB.location = tuple(HOLE_C)
HW = Vector(HOLE_C) + Vector((0, -0.02, 0))
nrm = Vector((0.15, -1.0, 0.25)).normalized()
rg = random.Random(21)
goos = [gooB]
for i in range(46):
    mb = bpy.data.metaballs.new(f"goo.{i + 1:03d}"); e = mb.elements.new(); e.radius = rg.uniform(0.045, 0.085)
    o = bpy.data.objects.new(f"goo.{i + 1:03d}", mb); sc.collection.objects.link(o); o.parent = gut
    t0 = HOLE_T + 14 + int(i * (LK1 - HOLE_T - 14) / 46) + rg.randint(-2, 2)
    v = nrm * rg.uniform(0.010, 0.022) + Vector((rg.uniform(-0.006, 0.006), 0, rg.uniform(-0.004, 0.006)))
    key(o, 1, loc=tuple(HW), scale=(0.01, 0.01, 0.01)); key(o, t0, loc=tuple(HW), scale=(0.01, 0.01, 0.01))
    for k in range(2, END - t0, 3):
        p = HW + v * k + Vector((0, 0, -0.00042 * k * k))
        if p.z < -1.2: p.z = -1.2
        sc_ = min(1.0, k / 10)
        key(o, t0 + k, loc=tuple(p), scale=(sc_,) * 3)
        if t0 + k > LK1 + 2: break
    goos.append(o)
for o in goos: vis(o, rng("hole", "leak"), recursive=False)
vis(gut, GUT_SHOTS)
for o in goos: vis(o, rng("hole", "leak"), recursive=False)
vis(gUc, rng("hole", "leak"), recursive=False)
vis(gmA, rng("loops", "pull", "squeeze", "dying"), recursive=False); vis(gmB, rng("loops", "pull", "squeeze", "dying"), recursive=False)
vis(fld_root, [(PU0, SNAP2 + 8)])

# ======================================================================
# 6) MAGNIT STUDIYASI (-40,0,0)
# ======================================================================
M0 = Vector((-40, 0, 0))
mstu = empty("mstudio", tuple(M0))
plane("mfloor", (30, 30), tuple(M0), mat("mfloor_m", (0.012, 0.012, 0.015), 0.12, coat=1.0), parent=mstu)
ON0, ON1 = S["one"]; TW0, TW1 = S["two"]
BR = 0.05
SNAP3 = 1166
smA = sphere("smagA", BR, (0, 0, 0), mag_m, sub=4)
smB = sphere("smagB", BR, (0, 0, 0), mag_m, sub=4)
for f in range(ON0, TW1 + 2, 2):
    t = min(1.0, (f - ON0) / (ON1 - ON0)); x = -0.9 + 0.9 * (1 - (1 - t) ** 1.6)
    key(smA, f, loc=tuple(M0 + Vector((x, 0, BR))), rot=(0, math.degrees(x / BR), 0))
for f in range(ON0, TW1 + 2, 1):
    if f < TW0 + 4: xb = 2.5
    elif f < SNAP3: t = (f - TW0 - 4) / (SNAP3 - TW0 - 4); xb = 2.5 - (2.5 - 2 * BR) * t ** 2.2
    else: xb = 2 * BR
    rb_ = -math.degrees((xb - 2.5) / BR)
    key(smB, f, loc=tuple(M0 + Vector((xb, 0, BR))), rot=(0, rb_, 0))
for o in (smA, smB): vis(o, MAG_SHOTS, recursive=False)
vis(mstu, MAG_SHOTS)
# rang-barang o'yinchoq magnitlar (kids) — gilam ustida
toy_cols = [(0.9, 0.1, 0.1), (0.1, 0.35, 0.95), (0.95, 0.75, 0.05), (0.1, 0.75, 0.25), (0.75, 0.2, 0.85), (0.9, 0.9, 0.9)]
toy_m = [mat(f"toy{i}", c, 0.12, metal=0.85, coat=0.8) for i, c in enumerate(toy_cols)]
toys = empty("toys", (0, 0, 0))
rt = random.Random(9); TR = 0.0075
for i in range(46):
    if i < 18:            # zanjir (ilon)
        a = i * 0.28; p = (0.62 + 0.11 * math.cos(a) + i * 0.004, 0.32 + 0.09 * math.sin(a), TR)
    elif i < 30:          # kub uyumi
        k = i - 18; p = (0.84 + (k % 3) * 2 * TR, 0.28 + ((k // 3) % 2) * 2 * TR, TR + (k // 6) * 2 * TR)
    else:
        p = (rt.uniform(0.45, 1.0), rt.uniform(0.15, 0.5), TR)
    s_ = sphere(f"toy{i}", TR, p, toy_m[i % 6], sub=4, parent=toys)
vis(toys, rng("kids"))
vis(room, ROOM_SHOTS)
for o in tm: vis(o, rng("hook"), recursive=False)
for o in hm: vis(o, rng("swallow"), recursive=False)
vis(toys, rng("kids"))
vis(hosp, rng("gurney")); vis(gur, rng("gurney")); vis(orr, rng("surgery"))

# ======================================================================
# 7) KAMERALAR
# ======================================================================
SWa, SWb = S["swallow"]; CA0, CA1 = S["calm"]; LP0, LP1 = S["loops"]; PA0, PA1 = S["pain"]; DA0, DA1 = S["days"]
IN0, IN1 = S["inflame"]; KI0, KI1 = S["kids"]
# 1 ilgak: stol ustida makro
tT = empty("tmagT", (0, 0.78, TABLE_Z + MR))
c = shot_cam("hook", (0, 0, 0), tT, 32, 3.2, focus=tT)
path_keys(c, ((HO0, (0.09, 0.56, TABLE_Z + 0.03)), (SNAP1, (0.05, 0.64, TABLE_Z + 0.022)), (HO1, (0.04, 0.67, TABLE_Z + 0.02))))
lens_keys(c, ((HO0, 30), (SNAP1 - 1, 38), (SNAP1 + 2, 62), (HO1, 66)))
shake(c, SNAP1, SNAP1 + 8, 0.004, 1)
# 2 yutish: yuzga yaqin plan
c = shot_cam("swallow", (0, 0, 0), faceT, 50, 2.0, focus=faceT)
path_keys(c, ((SWa, (-0.45, 0.95, 1.12)), (SWb, (-0.3, 1.08, 1.08))))
lens_keys(c, ((SWa, 42), (SWb, 55)))
# 3 rentgen: bo'yindan qoringa
xT = empty("xthroatT", (0, 0, 0));
c = shot_cam("xthroat", (0, 0, 0), xT, 40, 4.0, focus=xT)
def hips_world(f, local):
    sc.frame_set(f); return tuple(hipsE.matrix_world @ Vector(local))
for f in range(XT0, XT1 + 1, 3):
    t = (f - XT0) / (XT1 - XT0)
    key(xT, f, loc=hips_world(f, (0.01, 0.47 - 0.27 * ease(t), 0.04)))
    hp_ = Vector(hips_world(f, (0.01, 0.45 - 0.22 * ease(t), 0.04)))
    key(c, f, loc=tuple(hp_ + Vector((0.3 - 0.12 * t, -0.95 + 0.15 * t, 0.08))))
lens_keys(c, ((XT0, 30), (XT0 + 4, 45), (XT1, 50)))
shake(c, XT0, XT0 + 8, 0.01, 3)
# 4 xotirjam: keng, past burchak
chestT = empty("chestT", (SOFA[0], SOFA[1] - 0.15, 0.85))
c = shot_cam("calm", (0, 0, 0), chestT, 16, 5.6, focus=faceT)
orbit(c, CA0, CA1, (SOFA[0], SOFA[1], 0), 1.85, 1.6, 28, 8, 0.25, 0.32)
# 5 rentgen: ichak bo'ylab
mT = empty("xtravelT", (0, 0, 0))
c = shot_cam("xtravel", (0, 0, 0), mT, 50, 4.5, focus=mT)
for f in range(XV0, XV1 + 1, 2):
    sc.frame_set(f); p = bmag[0].matrix_world.translation.copy()
    key(mT, f, loc=tuple(p))
    hw = Vector(hips_world(f, (0.0, 0.1, 0.07)))
    key(c, f, loc=tuple(hw + Vector((0.16, -0.6, 0.1 - 0.06 * (f - XV0) / (XV1 - XV0)))))
# 6 rentgen: ikki xil joy, yon tomondan
sT = empty("xsplitT", (0, 0, 0))
c = shot_cam("xsplit", (0, 0, 0), sT, 60, 4.0, focus=sT)
for f in range(XS0, XS1 + 1, 2):
    sc.frame_set(f); p = (bmag[0].matrix_world.translation + bmag[1].matrix_world.translation) / 2
    key(sT, f, loc=tuple(p))
    t = (f - XS0) / (XS1 - XS0)
    key(c, f, loc=tuple(p + Vector((0.32 - 0.1 * t, -0.28 + 0.06 * t, 0.06))))
lens_keys(c, ((XS0, 36), (XS0 + 5, 62), (XS1, 70)))
# 7 ichak halqalari: push-in
gT = empty("gutT", tuple(G0))
c = shot_cam("loops", (0, 0, 0), gT, 32, 4.0, focus=gT)
path_keys(c, ((LP0, tuple(G0 + Vector((-1.3, -2.9, 0.55)))), (LP1, tuple(G0 + Vector((-0.75, -2.1, 0.25))))))
# 8 og'riq: past burchak
painT = empty("painT", (1.05, 1.12, 0.95))
c = shot_cam("pain", (0, 0, 0), painT, 16, 4.0, focus=faceT)
path_keys(c, ((PA0, (2.2, -0.75, 0.3)), (PA1, (2.0, -0.5, 0.36))))
lens_keys(c, ((PA0, 15), (PA0 + 10, 20), (PA1, 21)))
shake(c, PA0 + 2, PA0 + 22, 0.035, 8)
# 9 tortishish: yonidan, yopishganda crash zoom
c = shot_cam("pull", (0, 0, 0), gT, 30, 5.6, focus=gT)
path_keys(c, ((PU0, tuple(G0 + Vector((0.6, -2.5, 0.15)))), (SNAP2, tuple(G0 + Vector((0.35, -2.1, 0.08)))), (PU1, tuple(G0 + Vector((0.3, -1.9, 0.06))))))
lens_keys(c, ((PU0, 30), (SNAP2 - 1, 34), (SNAP2 + 2, 52), (PU1, 56)))
shake(c, SNAP2, SNAP2 + 14, 0.05, 9)
# 10 qisilish: makro
c = shot_cam("squeeze", (0, 0, 0), gT, 40, 4.0, focus=gT)
path_keys(c, ((SQ0, tuple(G0 + Vector((-0.9, -1.75, 0.35)))), (SQ1, tuple(G0 + Vector((-0.6, -1.35, 0.2))))))
# 11 o'lish: aylanma
c = shot_cam("dying", (0, 0, 0), gT, 40, 3.5, focus=gT)
orbit(c, DY0, DY1, tuple(G0), 1.9, 1.6, -35, 20, 0.55, 0.3)
# 12 kunlar: divanda yotadi, tepadan
lyT = empty("lieT", (LIE[0] + 0.25, LIE[1], 0.62))
c = shot_cam("days", (0, 0, 0), lyT, 24, 4.0, focus=lyT)
path_keys(c, ((DA0, (0.9, 0.4, 1.45)), (DA1, (0.75, 0.55, 1.35))))
# 13 teshik: crash zoom
hT = empty("holeT", tuple(G0 + HOLE_C))
c = shot_cam("hole", (0, 0, 0), hT, 30, 3.5, focus=hT)
path_keys(c, ((HL0, tuple(G0 + HOLE_C + Vector((-0.4, -1.3, 0.35)))), (HL1, tuple(G0 + HOLE_C + Vector((-0.2, -0.8, 0.18))))))
lens_keys(c, ((HL0, 28), (HOLE_T - 2, 34), (HOLE_T + 2, 55), (HL1, 60)))
shake(c, HOLE_T, HOLE_T + 10, 0.02, 13)
# 14 oqish: kamera pastga
lkT = empty("leakT", tuple(G0 + HOLE_C + Vector((0, -0.25, -0.3))))
c = shot_cam("leak", (0, 0, 0), lkT, 35, 4.0, focus=lkT)
path_keys(c, ((LK0, tuple(G0 + HOLE_C + Vector((0.5, -1.4, 0.1)))), (LK1, tuple(G0 + HOLE_C + Vector((0.4, -1.35, -0.45))))))
# 15 yallig'lanish (rentgen, yotgan)
iT = empty("inflT", (0, 0, 0))
c = shot_cam("inflame", (0, 0, 0), iT, 30, 4.0, focus=iT)
for f in range(IN0, IN1 + 1, 3):
    t = (f - IN0) / (IN1 - IN0)
    p = Vector(hips_world(f, (0.0, 0.08, 0.05))); key(iT, f, loc=tuple(p))
    key(c, f, loc=tuple(p + Vector((0.15, -0.75 + 0.1 * t, 0.25 + 0.45 * t))))
# 16 zambil: oldidan, past burchak, orqaga yuradi
gT2 = empty("gurT", (0, 0, 0))
c = shot_cam("gurney", (0, 0, 0), gT2, 18, 4.0, focus=gT2)
for f in range(GU0, GU1 + 1, 2):
    t = (f - GU0) / (GU1 - GU0); gx = G_X0 + (G_X1 - G_X0) * t
    key(gT2, f, loc=(gx + 0.55, HOSP.y, GZ + 0.15))
    key(c, f, loc=(gx + 1.9 - 0.35 * t, HOSP.y - 1.05, 1.25 + 0.08 * t))
interp(c, "LINEAR", "location"); interp(gT2, "LINEAR", "location")
# 17 operatsiya: tepadan crash zoom
oT = empty("orT", tuple(OR0 + Vector((0.2, 0, GZ + 0.1))))
c = shot_cam("surgery", (0, 0, 0), oT, 18, 5.6, focus=oT)
path_keys(c, ((SU0, tuple(OR0 + Vector((1.0, -0.95, 2.0)))), (SU1, tuple(OR0 + Vector((0.8, -0.8, 1.85))))))
lens_keys(c, ((SU0, 16), (SU0 + 5, 16), (SU0 + 9, 32), (SU1, 36)))
shake(c, SU0 + 5, SU0 + 15, 0.03, 17)
# 18 bitta magnit: past ergashadi
oneT = empty("oneT", (0, 0, 0)); cl_ = oneT.constraints.new("COPY_LOCATION"); cl_.target = smA
c = shot_cam("one", (0, 0, 0), oneT, 35, 2.8, focus=oneT)
for f in range(ON0, ON1 + 1, 4):
    sc.frame_set(f); p = smA.matrix_world.translation
    t = (f - ON0) / (ON1 - ON0)
    key(c, f, loc=(p.x - 0.25 + 0.15 * t, p.y - 0.6 + 0.12 * t, 0.06 + 0.02 * t))
# 19 ikkitasi: yopishganda crash zoom + qizil
twT = empty("twoT", tuple(M0 + Vector((BR, 0, BR))))
c = shot_cam("two", (0, 0, 0), twT, 28, 3.2, focus=twT)
path_keys(c, ((TW0, tuple(M0 + Vector((-0.35, -0.55, 0.1)))), (SNAP3, tuple(M0 + Vector((-0.25, -0.45, 0.09)))), (TW1, tuple(M0 + Vector((-0.12, -0.36, 0.12))))))
lens_keys(c, ((TW0, 28), (SNAP3 - 1, 30), (SNAP3 + 2, 60), (TW1, 66)))
shake(c, SNAP3, SNAP3 + 12, 0.012, 19)
# 20 bolalar: pol sathida, magnitlarga fokus
kT = empty("kidsT", (0.72, 0.32, 0.01))
c = shot_cam("kids", (0, 0, 0), kT, 45, 2.8, focus=kT)
path_keys(c, ((KI0, (0.55, -0.12, 0.05)), (KI1, (0.62, 0.02, 0.045))))
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 8) YORUG'LIK
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
ROOM_N = {"hook", "swallow", "calm", "pain", "days", "kids"}
for f, n in SHOTS:
    s1, s2 = (0.35, 0.0) if n in ROOM_N else (0.0, 1.0)
    for bgn, v in ((bg_sky, s1), (bg_dk, s2)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# xona: deraza quyoshi + iliq to'ldiruvchi
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(2.0); sun.data.color = (1.0, 0.9, 0.78); sun.rotation_euler = (R(55), 0, R(-62))
for f, e in lights_for(ROOM_SHOTS, 3.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
# "bir necha kun": kun-tun almashinuvi (12-kadr)
for f in range(DA0, DA1 + 1, 10):
    for ff, e, col in ((f, 4.5, (1.0, 0.85, 0.65)), (f + 5, 0.05, (0.4, 0.5, 1.0))):
        sun.data.energy = e; sun.data.keyframe_insert("energy", frame=ff)
        sun.data.color = col; sun.data.keyframe_insert("color", frame=ff)
sun.data.energy = 0; sun.data.keyframe_insert("energy", frame=DA1 + 1); sun.data.color = (1.0, 0.9, 0.78); sun.data.keyframe_insert("color", frame=DA1 + 1)
sun.data.energy = 3.5; sun.data.keyframe_insert("energy", frame=KI0)
sun.data.energy = 0.0; sun.data.keyframe_insert("energy", frame=END + 1)
interp(sun.data, "CONSTANT")
area("room_key", (-1.2, -0.6, 2.2), 1.5, (1.0, 0.88, 0.75), lights_for(ROOM_SHOTS, 260.0), target=chestT)
area("room_fill", (1.8, -0.8, 1.4), 1.2, (0.85, 0.9, 1.0), lights_for(ROOM_SHOTS, 90.0), target=chestT)
area("room_rim", (0.8, 2.1, 2.2), 0.8, (1.0, 0.75, 0.5), lights_for(ROOM_SHOTS, 120.0), target=faceT)
point("lamp_light", (1.05, 1.9, 1.5), 0.15, (1.0, 0.7, 0.4), lights_for(ROOM_SHOTS, 60.0))
area("pain_red", (1.8, 0.6, 0.6), 1.0, (1.0, 0.06, 0.03), [(1, 0), (PA0 + 8, 900), (PA0 + 12, 250), (PA0 + 30, 700), (PA0 + 36, 150), (PA1 + 1, 0)], target=painT)
area("hook_key", (0.25, 0.55, 0.75), 0.3, (1.0, 0.95, 0.9), lights_for(rng("hook"), 25.0), target=tT)
area("kids_key", (1.2, -0.3, 0.6), 0.6, (1.0, 0.9, 0.8), lights_for(rng("kids"), 60.0), target=kT)
# rentgen
xr_l = lights_for(X_SHOTS, 30.0)
area("x_rim", (-0.8, 2.6, 1.5), 1.0, (0.3, 0.6, 1.0), xr_l, target=chestT)
area("x_key", (0.8, 0.6, 1.4), 0.8, (1.0, 0.92, 0.88), lights_for(X_SHOTS, 18.0), target=chestT)
area("x_inf", (0.6, 1.2, 1.5), 1.0, (1.0, 0.1, 0.04), lights_for(rng("inflame"), 40.0), target=chestT)
# ichak studiyasi
G_on = GUT_SHOTS
area("g_key", tuple(G0 + Vector((-1.5, -2.2, 1.8))), 1.5, (1.0, 0.9, 0.85), lights_for(G_on, 320.0), target=gT)
area("g_rim", tuple(G0 + Vector((1.6, 0.8, 1.2))), 1.2, (1.0, 0.45, 0.4), lights_for(G_on, 260.0), target=gT)
area("g_fill", tuple(G0 + Vector((1.2, -1.8, -1.0))), 1.0, (0.55, 0.7, 1.0), lights_for(G_on, 90.0), target=gT)
gl = point("g_inflame", tuple(G0 + Vector((0.2, -0.8, 0.2))), 0.4, (1.0, 0.12, 0.04), [(1, 0)], const=False)
for f, e in ((LK0 + 20, 0), (LK0 + 40, 60), (LK1, 180), (LK1 + 1, 0)): gl.data.energy = e; gl.data.keyframe_insert("energy", frame=f)
for nm_, o in (("gA", gmA), ("gB", gmB)):
    pl = point("glow_" + nm_, (0, 0, 0), 0.05, (0.5, 0.8, 1.0), lights_for(rng("loops", "pull"), 4.0), parent=o)
point("snap_flash", tuple(G0 + Vector((0, -0.5, 0))), 0.2, (0.6, 0.85, 1.0), [(1, 0), (SNAP2, 400), (SNAP2 + 3, 80), (SNAP2 + 10, 0)], const=False)
# kasalxona
area("h_fill", (HOSP.x + 2, HOSP.y - 1.0, 2.2), 2.0, (0.9, 0.97, 1.0), lights_for(rng("gurney"), 150.0), target=gT2)
for i in range(6):
    area(f"h_pan{i}", (HOSP.x - 2 + i * 2.0, HOSP.y, 2.7), 0.5, (0.92, 0.97, 1.0), lights_for(rng("gurney"), 120.0), shape=(0.5, 1.1))
sp_ = bpy.data.objects.new("or_spot", bpy.data.lights.new("or_spot", "SPOT")); sc.collection.objects.link(sp_)
sp_.location = tuple(OR0 + Vector((0, 0, 2.1))); sp_.data.spot_size = R(55); sp_.data.spot_blend = 0.5; sp_.data.shadow_soft_size = 0.3
for f, e in ((1, 0), (SU0, 20), (SU0 + 6, 2500), (SU0 + 10, 1500), (SU1 + 1, 0)): sp_.data.energy = e; sp_.data.keyframe_insert("energy", frame=f)
interp(sp_.data, "CONSTANT")
area("or_amb", tuple(OR0 + Vector((1.5, -1.5, 2.8))), 2.0, (0.6, 0.85, 0.9), lights_for(rng("surgery"), 120.0), target=oT)
# magnit studiyasi: yorug' chiziqlar (xrom aksi uchun)
M_on = MAG_SHOTS
area("m_strip1", tuple(M0 + Vector((-0.6, -0.8, 1.2))), 1.0, (0.9, 0.95, 1.0), lights_for(M_on, 150.0), target=twT, shape=(3.0, 0.25))
area("m_strip2", tuple(M0 + Vector((1.2, 0.9, 0.8))), 1.0, (0.5, 0.7, 1.0), lights_for(M_on, 120.0), target=twT, shape=(2.5, 0.2))
area("m_top", tuple(M0 + Vector((0.2, 0, 2.0))), 1.2, (1.0, 0.95, 0.9), lights_for(M_on, 80.0), target=twT)
area("m_red", tuple(M0 + Vector((0.3, -0.9, 0.6))), 1.2, (1.0, 0.05, 0.02), [(1, 0), (SNAP3, 0), (SNAP3 + 2, 900), (SNAP3 + 8, 300),
     (SNAP3 + 30, 600), (SNAP3 + 40, 250), (SNAP3 + 60, 600), (TW1 + 1, 0)], target=twT)
point("m_flash", tuple(M0 + Vector((BR, -0.15, 0.12))), 0.05, (0.8, 0.9, 1.0), [(1, 0), (SNAP3, 120), (SNAP3 + 3, 20), (SNAP3 + 8, 0)], const=False)

# ======================================================================
# 9) RENDER
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
