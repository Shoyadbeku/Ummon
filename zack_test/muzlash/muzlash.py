# Muzqaymoq "miyani muzlatadi" — Zack D. Films uslubida 40 s video (960 kadr, 24 fps, 9:16).
# Asos: zack_test/burish/burish.py + parts.py, mixchar.py. Kadr rejasi: STORYBOARD.md
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/muzlash/muzlash.py --render
# Sinov: FRAMES=20,60,100,180,300 PCT=35
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 960
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (47, "face"), (82, "xflash"), (125, "brain_ice"), (209, "touch"), (266, "constrict"), (335, "warm"),
         (413, "dilate"), (479, "nerve"), (560, "signal"), (622, "confused"), (698, "pain_wide"), (755, "close"),
         (789, "tongue"), (844, "calm"), (909, "relief")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

# ---------------- yordamchilar (burish.py dan) ----------------
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

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, sss_scale=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if sss_scale is not None: b.inputs["Subsurface Scale"].default_value = sss_scale
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
    L.new(img("rough.jpg", True).outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def _par(o, parent):
    o.parent = parent
    if parent.name in WORLD_PARENTS:
        bpy.context.view_layer.update(); o.matrix_parent_inverse = parent.matrix_world.inverted()
WORLD_PARENTS = {"street", "mouth", "bstudio"}

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
    sc.frame_set(f0); base = cam.location.copy()
    pts = [(f, base) for f in (f0, f1)]
    for f in range(f0, f1):
        k = amp * ((1 - (f - f0) / (f1 - f0)) ** 2 if decay else 1.0)
        sc.frame_set(f)
        cam.delta_location = Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("delta_location", frame=f)
    cam.delta_location = (0, 0, 0); cam.keyframe_insert("delta_location", frame=f1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def path_keys(cam, pts, ease=True):
    for f, p in pts: key(cam, f, loc=p)
    if not ease: interp(cam, "LINEAR", "location")

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

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

STREET_SHOTS = rng("hook", "face", "pain_wide", "close", "relief")
XRAY_SHOTS = rng("xflash", "nerve", "signal")
MOUTH_SHOTS = rng("touch")
BRAIN_SHOTS = rng("brain_ice", "confused")

# ======================================================================
# 1) KO'CHA (0,0,0): yo'lak, yo'l, Audi, daraxtlar, muzqaymoq soyaboni
# ======================================================================
street = empty("street", (0, 0, 0))
pave = pbr("pavement", "concrete_pavement", 0.45, tint=(1.0, 0.97, 0.93))
asph = pbr("asphalt", "asphalt_02", 0.3)
plane("pavement", (16, 7.0), (0, -0.5, 0), pave, parent=street)
plane("road", (40, 9), (0, 7.5, -0.12), asph, parent=street)
box("curb", (16, 0.25, 0.16), (0, 3.05, -0.05), pave, parent=street)
plane("pave_far", (40, 4), (0, 13.9, 0.0), pave, parent=street)
# Audi (BlenderKit) yo'l chetida
carR = empty("carR", (-1.6, 4.5, -0.12), street); carR.rotation_euler = (0, 0, R(-90))
car_objs = import_gltf(BK + "c3c28d91_u.glb", carR)
lo, hi = bbox(car_objs); carR.location.z += -0.12 - lo.z
# daraxtlar va uylar (orqa fon, DOF bilan xiralashadi)
bark = mat("bark", (0.22, 0.15, 0.1), 0.9)
leaves = mat("leaves", (0.18, 0.38, 0.12), 0.7, sss=0.3)
cl = bpy.data.textures.new("crown_cl", "CLOUDS"); cl.noise_scale = 0.4
def tree(x, y, s=1.0):
    cyl("trunk", 0.12 * s, 2.4 * s, (x, y, 1.2 * s), bark, verts=12, parent=street)
    for dx, dy, dz, r in ((0, 0, 3.0, 1.3), (0.7, 0.2, 2.6, 0.9), (-0.6, -0.3, 2.7, 1.0), (0.1, 0.4, 3.7, 0.9)):
        o = sphere("crown", r * s, (x + dx * s, y + dy * s, dz * s), leaves, sub=3, parent=street)
        dm = o.modifiers.new("d", "DISPLACE"); dm.strength = 0.4 * s; dm.texture = cl
for x, y, s in ((-4.5, 2.4, 1.0), (3.8, 2.5, 1.1), (9, 2.5, 1.0), (-10, 2.4, 1.2), (-2, 14.5, 1.3), (6, 14.5, 1.2), (14, 14.5, 1.0)):
    tree(x, y, s)
hcols = [(0.85, 0.72, 0.55), (0.62, 0.72, 0.78), (0.9, 0.88, 0.82), (0.78, 0.55, 0.45), (0.7, 0.75, 0.62)]
win = mat("bwin", (0.25, 0.35, 0.45), 0.08, metal=0.3)
for i, x in enumerate(range(-24, 25, 8)):
    h = 6 + 3 * (i % 3)
    box(f"house{i}", (7.5, 6, h), (x, 19, h / 2), pbr(f"hs{i}", "painted_plaster_wall", 0.3, tint=hcols[i % 5]), parent=street)
    for fl in range(int(h // 3)):
        for dx in (-2.2, 0, 2.2):
            box("hwin", (1.1, 0.05, 1.3), (x + dx, 15.97, 1.7 + fl * 3), win, parent=street)
# muzqaymoq soyaboni (pushti-oq yo'l-yo'l) va do'kon aravachasi
stripe = bpy.data.materials.new("umbrella"); stripe.use_nodes = True
N = stripe.node_tree.nodes; L = stripe.node_tree.links
tc = N.new("ShaderNodeTexCoord"); grd = N.new("ShaderNodeTexGradient"); grd.gradient_type = "RADIAL"; L.new(tc.outputs["Object"], grd.inputs[0])
mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = 12.0; L.new(grd.outputs[0], mm.inputs[0])
fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"; L.new(mm.outputs[0], fr.inputs[0])
gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5; L.new(fr.outputs[0], gt.inputs[0])
mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(gt.outputs[0], mx.inputs["Factor"])
mx.inputs[6].default_value = (0.95, 0.35, 0.5, 1); mx.inputs[7].default_value = (0.97, 0.95, 0.92, 1)
L.new(mx.outputs[2], N["Principled BSDF"].inputs["Base Color"]); N["Principled BSDF"].inputs["Roughness"].default_value = 0.6
for (ux, uy) in ((2.3, 2.2),):
    cyl("pole", 0.025, 2.4, (ux, uy, 1.2), mat("pole_m", (0.9, 0.9, 0.9), 0.3, metal=0.8), parent=street)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=1.3, radius2=0.02, depth=0.45, location=(ux, uy, 2.45))
    um = bpy.context.object; um.name = "umbrella"; um.data.materials.append(stripe); _par(um, street)
    cartm = mat("cart", (0.35, 0.75, 0.9), 0.35, coat=0.5)
    box("cart", (1.4, 0.7, 0.9), (ux + 0.2, uy + 0.4, 0.55), cartm, parent=street)
    box("cart_top", (1.45, 0.75, 0.05), (ux + 0.2, uy + 0.4, 1.02), mat("cart_top", (0.95, 0.95, 0.95), 0.2), parent=street)
    for wx in (-0.45, 0.45):
        cyl("cwheel", 0.13, 0.06, (ux + 0.2 + wx, uy + 0.02, 0.13), mat("tyre", (0.03, 0.03, 0.03), 0.6), rot=(90, 0, 0), parent=street)
# Poly Haven gul tuvaklari
for i, (px, py) in enumerate(((-1.3, 1.6), (1.1, 2.6))):
    pr = empty(f"plant{i}", (px, py, 0), street); pr.scale = (1.3, 1.3, 1.3)
    import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", pr)

# ======================================================================
# 2) MEGAN + muzqaymoq
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
mroot.location = (0, 0, 0); mroot.rotation_euler = (0, 0, 0)       # -Y ga (kameraga) qaraydi
A_ = lambda f: mc.load_action(f, True)
mc.add_strip(meg, A_("Breathing_Idle.fbx"), -40, blend=0, repeat=5.0)
def strip(act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(meg, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
strip(A_("Drinking.fbx"), -8, src=(40, 112), blend=0, bout=5)       # muzqaymoqni og'ziga olib boradi
strip(A_("Agony.fbx"), 44, blend=4, bout=8)                          # boshini changallaydi
strip(A_("Agony.fbx"), 690, blend=6, bout=8)
strip(A_("Focus.fbx"), 748, src=(0, 75), blend=6, bout=8)            # tik turib boshini ushlaydi (yuz ko'rinadi)
strip(A_("Focus.fbx"), 893, src=(50, 166), blend=6, bout=0)          # og'riqni silkitib tashlaydi
headE = child_of_bone("meg_head", meg, "Head")
faceT = empty("faceT", (0, 0.09, 0.08), headE)          # yuz markazi (Head: X chap, Y tepa, Z old)
palmE = child_of_bone("meg_palm", meg, "LeftHand", loc=(0, 0.075, 0.0))     # Drinking chap qo'l bilan

# muzqaymoq (procedural): vafli kesik konus + ikki shar
coneR = empty("coneR", (0, 0, 0.035))              # kaftga ergashadi, lekin tik turadi (og'izga biroz qiyshaygan)
_cl = coneR.constraints.new("COPY_LOCATION"); _cl.target = palmE; _cl.use_offset = True
coneR.rotation_euler = (R(12), R(-14), 0)
waf = bpy.data.materials.new("waffle"); waf.use_nodes = True
N = waf.node_tree.nodes; L = waf.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord")
w1 = N.new("ShaderNodeTexWave"); w1.bands_direction = "DIAGONAL"; w1.inputs["Scale"].default_value = 140
w2 = N.new("ShaderNodeTexWave"); w2.bands_direction = "DIAGONAL"; w2.inputs["Scale"].default_value = 140
mp2 = N.new("ShaderNodeMapping"); mp2.inputs["Scale"].default_value = (-1, 1, 1)
L.new(tc.outputs["Object"], w1.inputs[0]); L.new(tc.outputs["Object"], mp2.inputs[0]); L.new(mp2.outputs[0], w2.inputs[0])
mn = N.new("ShaderNodeMath"); mn.operation = "MINIMUM"; L.new(w1.outputs["Fac"], mn.inputs[0]); L.new(w2.outputs["Fac"], mn.inputs[1])
cr = N.new("ShaderNodeValToRGB"); L.new(mn.outputs[0], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.32, 0.14, 0.04, 1); cr.color_ramp.elements[1].color = (0.85, 0.55, 0.22, 1)
cr.color_ramp.elements[0].position = 0.15; cr.color_ramp.elements[1].position = 0.5
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.6
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.002
L.new(mn.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.004, radius2=0.03, depth=0.13, location=(0, 0, -0.03))
cone = bpy.context.object; cone.name = "cone"; cone.data.materials.append(waf); cone.parent = coneR
for p in cone.data.polygons: p.use_smooth = True
def scoop_mat(name, col):
    m = mat(name, col, 0.38, sss=0.8, sss_scale=0.004, coat=0.35)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 160; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs[0])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.001
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
scoop_tex = bpy.data.textures.new("scoop_cl", "CLOUDS"); scoop_tex.noise_scale = 0.012
mint = scoop_mat("mint", (0.45, 0.88, 0.72)); vanil = scoop_mat("vanilla", (0.96, 0.9, 0.75))
for i, (z, r, m) in enumerate(((0.04, 0.033, vanil), (0.083, 0.031, mint))):
    s_ = sphere(f"scoop{i}", r, (0, 0, z), m, scale=(1, 1, 0.85), sub=5, parent=coneR)
    d = s_.modifiers.new("lump", "DISPLACE"); d.texture = scoop_tex; d.strength = 0.006; d.texture_coords = "LOCAL"
    bpy.ops.mesh.primitive_torus_add(major_radius=r * 0.95, minor_radius=r * 0.18, location=(0, 0, z - r * 0.55))
    rim = bpy.context.object; rim.name = f"scoop_rim{i}"; rim.data.materials.append(m); rim.parent = coneR
    d = rim.modifiers.new("lump", "DISPLACE"); d.texture = scoop_tex; d.strength = 0.005
cone_on = rng("hook", "face", "pain_wide", "close", "relief")
vis(coneR, cone_on)

# ---- rentgen nusxa: shaffof Megan + miya + uch shoxli asab + og'riq nuqtasi ----
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.4, base=0.015)
ghosts = []
for o in mmeshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
for g in ghosts: vis(g, XRAY_SHOTS + rng("constrict", "warm", "dilate", "tongue", "calm"), recursive=False)
for o in mmeshes: vis(o, STREET_SHOTS, recursive=False)
hbrain, hbrain_m = P.build_brain("hbrain", headE, size=0.074)
hbrain.location = (0, 0.11, 0.03); hbrain.rotation_euler = (R(-90), 0, 0)
vis(hbrain, XRAY_SHOTS + rng("constrict", "warm", "dilate", "tongue", "calm"))
XF0, XF1 = S["xflash"]; NV0, NV1 = S["nerve"]; SG0, SG1 = S["signal"]
val_key(hbrain_m, "glow", 1, 0.3)
for f in range(SG0 + 30, SG1, 6):
    val_key(hbrain_m, "glow", f, 5.0); val_key(hbrain_m, "glow", f + 3, 1.2)
# peshonadagi og'riq (qizil chaqnash)
pain_m = mat("pain", (0.25, 0.01, 0.01), emit=0.0); pain_m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1)
pain_b = pain_m.node_tree.nodes["Principled BSDF"]
pain = sphere("pain_glow", 0.032, (0, 0.165, 0.075), pain_m, scale=(1.4, 0.8, 0.7), parent=headE)
def pain_key(f, v):
    pain_b.inputs["Emission Strength"].default_value = v; pain_b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
pain_key(1, 0)
for f in range(XF0 + 4, XF1, 8):
    pain_key(f, 0.5); pain_key(f + 2, 14.0); pain_key(f + 5, 4.0)
pain_key(XF1 + 1, 0)
vis(pain, rng("xflash"))
pl = point("pain_light", (0, 0.0, 0.0), 0.02, (1.0, 0.1, 0.05), [(1, 0)], parent=pain, const=False)
for f in range(XF0 + 4, XF1, 8):
    for ff, e in ((f, 0.2), (f + 2, 6.0), (f + 5, 1.0)): pl.data.energy = e; pl.data.keyframe_insert("energy", frame=ff)
pl.data.energy = 0; pl.data.keyframe_insert("energy", frame=XF1 + 1)
# tanglaydagi sovuq nuqta
cold_m = mat("cold_spot", (0.15, 0.55, 1.0), emit=3.0)
cold = sphere("cold_spot", 0.012, (0, 0.035, 0.075), cold_m, scale=(1.6, 0.5, 1.2), parent=headE)
vis(cold, rng("nerve", "signal"))
# uch shoxli asab (trigeminal): tanglay -> yuz shoxlari -> tugun -> miya
nrv_m = P.pulse_material("tri_nerve", (0.95, 0.8, 0.2), base_emit=0.6, pulse_col=(1.0, 0.9, 0.35), width=0.09)
sig_m = P.pulse_material("tri_signal", (1.0, 0.5, 0.15), base_emit=0.0, pulse_col=(1.0, 0.35, 0.1), width=0.07)
tri = []
for sx in (-1, 1):
    g = (sx * 0.038, 0.075, 0.035)                                  # tugun
    tri.append(P.tube(f"V1_{sx}", [g, (sx * 0.042, 0.11, 0.075), (sx * 0.035, 0.145, 0.095), (sx * 0.02, 0.17, 0.09)], 0.0022, nrv_m, headE))
    tri.append(P.tube(f"V2_{sx}", [g, (sx * 0.048, 0.07, 0.085), (sx * 0.04, 0.06, 0.105), (sx * 0.015, 0.045, 0.08)], 0.0022, nrv_m, headE))
    tri.append(P.tube(f"V3_{sx}", [g, (sx * 0.05, 0.04, 0.06), (sx * 0.045, 0.0, 0.08), (sx * 0.02, -0.01, 0.1)], 0.0022, nrv_m, headE))
    sphere(f"gang{sx}", 0.006, g, nrv_m, scale=(1.3, 1, 1), parent=headE)
sig = P.tube("tri_sig", [(0, 0.035, 0.075), (0.02, 0.045, 0.08), (0.04, 0.06, 0.1), (0.048, 0.07, 0.085), (0.038, 0.075, 0.035),
                         (0.02, 0.09, 0.02), (0.0, 0.11, 0.03)], 0.0032, sig_m, headE)
for t_ in tri + [sig]: vis(t_, rng("nerve", "signal"), recursive=False)
for o in headE.children:
    if o.name.startswith("gang"): vis(o, rng("nerve", "signal"), recursive=False)
val_key(nrv_m, "pos", 1, -0.2); val_key(nrv_m, "pos", NV0 + 10, 1.25); val_key(nrv_m, "pos", NV0 + 40, -0.2)
val_key(nrv_m, "pos", NV0 + 41, 1.25)      # hamma shoxlar yonib qoladi
val_key(nrv_m, "glow", 1, 0.6); val_key(nrv_m, "glow", NV0 + 40, 0.6); val_key(nrv_m, "glow", NV0 + 48, 3.0)
val_key(sig_m, "pos", 1, -0.2); val_key(sig_m, "pos", SG0 + 2, -0.1); val_key(sig_m, "pos", SG0 + 30, 1.2)
val_key(sig_m, "glow", 1, 0.0); val_key(sig_m, "glow", SG0 + 28, 0.0); val_key(sig_m, "glow", SG0 + 34, 2.0)

# ======================================================================
# 3) MIYA STUDIYASI (0,60,0): muz qoplaydi -> sinadi; adashgan signal
# ======================================================================
B0 = Vector((0, 60, 1.0))
bstudio = empty("bstudio", tuple(B0))
brain, brain_m = P.build_brain("brain", None, size=0.6)
brain.location = B0; brain.rotation_euler = (0, 0, 0)
# muz qatlami (frost) brain materialiga
N = brain_m.node_tree.nodes; L = brain_m.node_tree.links; bb = N["Principled BSDF"]
frost = value_node(brain_m, "frost", 0.0)
fm = N.new("ShaderNodeMix"); fm.data_type = "RGBA"; L.new(frost, fm.inputs["Factor"])
fm.inputs[6].default_value = (0.85, 0.45, 0.5, 1); fm.inputs[7].default_value = (0.72, 0.88, 1.0, 1); L.new(fm.outputs[2], bb.inputs["Base Color"])
fr_r = N.new("ShaderNodeMix"); fr_r.data_type = "FLOAT"; L.new(frost, fr_r.inputs["Factor"]); fr_r.inputs[2].default_value = 0.35; fr_r.inputs[3].default_value = 0.12
L.new(fr_r.outputs[0], bb.inputs["Roughness"])
BI0, BI1 = S["brain_ice"]; CF0, CF1 = S["confused"]
BURST = 181                                    # "muzlamaydi" (7.44 s)
val_key(brain_m, "frost", 1, 0.0); val_key(brain_m, "frost", BI0 + 8, 0.0); val_key(brain_m, "frost", BURST - 3, 0.85)
val_key(brain_m, "frost", BURST, 0.0)
val_key(brain_m, "glow", 1, 0.25); val_key(brain_m, "glow", BURST - 1, 0.1); val_key(brain_m, "glow", BURST + 1, 5.0)
val_key(brain_m, "glow", BURST + 12, 0.6); val_key(brain_m, "glow", CF0, 0.4)
# muz parchalari
ice_m = bpy.data.materials.new("ice"); ice_m.use_nodes = True
N = ice_m.node_tree.nodes; L = ice_m.node_tree.links; ib = N["Principled BSDF"]
ib.inputs["Base Color"].default_value = (0.75, 0.9, 1.0, 1); ib.inputs["Transmission Weight"].default_value = 0.9
ib.inputs["Roughness"].default_value = 0.08; ib.inputs["IOR"].default_value = 1.31
ib.inputs["Emission Color"].default_value = (0.4, 0.75, 1.0, 1); ib.inputs["Emission Strength"].default_value = 0.6
ri = random.Random(3); shards = []
SH_N = 140
for i in range(SH_N):
    # ellipsoid sirtidagi nuqta (miya mahalliy koordinatasi, masshtabsiz): x ±0.55, y ±0.85, z -0.2..0.6
    u = ri.uniform(0, 2 * math.pi); v = math.acos(ri.uniform(-0.35, 1.0))
    n = Vector((math.sin(v) * math.cos(u), math.sin(v) * math.sin(u), math.cos(v)))
    p = Vector((n.x * 0.76, n.y * 0.84, n.z * 0.56 + 0.02))
    nn = Vector((n.x / 0.76, n.y / 0.84, n.z / 0.56)).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.05, radius2=0.0, depth=ri.uniform(0.12, 0.3))
    s_ = bpy.context.object; s_.name = f"shard{i}"; s_.data.materials.append(ice_m)
    s_.parent = brain
    s_.rotation_euler = Vector((0, 0, 1)).rotation_difference(nn).to_euler()
    s_.rotation_euler.z += ri.uniform(0, 6)
    w0 = BI0 + 10 + int(ri.uniform(0, 40))
    s_.location = p; s_.scale = (0.001,) * 3
    s_.keyframe_insert("location", frame=w0); s_.keyframe_insert("scale", frame=w0)
    s_.scale = (1, 1, 1); s_.keyframe_insert("scale", frame=w0 + 8)
    s_.keyframe_insert("location", frame=BURST - 1)
    sp = ri.uniform(0.04, 0.09)
    for k in range(1, BI1 - BURST + 2, 2):
        s_.location = p + nn * sp * k + Vector((0, 0, -0.0012 * k * k)); s_.keyframe_insert("location", frame=BURST + k)
        s_.rotation_euler.x += 0.25; s_.keyframe_insert("rotation_euler", frame=BURST + k)
    shards.append(s_)
for s_ in shards: vis(s_, rng("brain_ice"), recursive=False)
# muz changi (sinish paytida) — mayda bo'laklar
dust = []
for i in range(70):
    d = sphere(f"icedust{i}", ri.uniform(0.008, 0.02), (0, 0, 0), ice_m, sub=1, parent=brain)
    u = ri.uniform(0, 2 * math.pi); v = math.acos(ri.uniform(-0.3, 1.0))
    n = Vector((math.sin(v) * math.cos(u), math.sin(v) * math.sin(u), math.cos(v)))
    p = Vector((n.x * 0.76, n.y * 0.84, n.z * 0.56)); sp = ri.uniform(0.06, 0.14)
    for k in range(0, BI1 - BURST + 2, 2):
        d.location = p + n * sp * k + Vector((0, 0, -0.002 * k * k)); d.keyframe_insert("location", frame=BURST + k)
    vis(d, [(BURST, BI1)], recursive=False); dust.append(d)
# adashgan signal yo'llari (miya sirtida)
paths = []
rp = random.Random(12)
path_m = []
for j in range(7):
    m = P.pulse_material(f"bpath{j}", (0.95, 0.75, 0.2), base_emit=0.15, pulse_col=(1.0, 0.8, 0.3), width=0.12)
    path_m.append(m)
    u0 = rp.uniform(0, 2 * math.pi); v0 = rp.uniform(0.6, 1.4); du = rp.uniform(-1.6, 1.6); dv = rp.uniform(-0.6, 0.6)
    pts = []
    for k in range(9):
        t = k / 8; u = u0 + du * t; v = v0 + dv * t + 0.15 * math.sin(t * 9 + j)
        n = Vector((math.sin(v) * math.cos(u), math.sin(v) * math.sin(u), math.cos(v)))
        pts.append(tuple(Vector((n.x * 0.8, n.y * 0.87, n.z * 0.59 + 0.03))))
    paths.append(P.tube(f"bpath{j}", pts, 0.012, m, brain))
stem_m = P.pulse_material("bstem", (0.95, 0.75, 0.2), base_emit=0.3, pulse_col=(1.0, 0.85, 0.35), width=0.1)
stem = P.tube("bstem", [(0, 0.5, -1.4), (0, 0.42, -0.9), (0, 0.3, -0.45), (0, 0.15, -0.15), (0, 0.0, 0.1)], 0.025, stem_m, brain)
val_key(stem_m, "pos", 1, -0.2); val_key(stem_m, "pos", CF0 + 2, -0.1); val_key(stem_m, "pos", CF0 + 16, 1.2)
for j, m in enumerate(path_m):
    t0 = CF0 + 14 + j * 7
    val_key(m, "pos", 1, -0.2); val_key(m, "pos", t0, -0.15); val_key(m, "pos", t0 + 12, 1.2)
    t1 = t0 + 26
    if t1 + 10 < CF1:
        val_key(m, "pos", t1, -0.15); val_key(m, "pos", t1 + 10, 1.2)
for p_ in paths + [stem]: vis(p_, rng("confused"), recursive=False)
# peshona qismidagi (old tomon -Y) qizil "og'riq" — adashish natijasi
fpain_m = mat("fpain", (1.0, 0.08, 0.04), emit=0.0); fpb = fpain_m.node_tree.nodes["Principled BSDF"]
fpain = sphere("fpain", 0.22, (0, -0.72, 0.32), fpain_m, scale=(1.4, 0.5, 0.9), parent=brain)
for f, v in ((1, 0), (CF1 - 22, 0), (CF1 - 18, 25), (CF1 - 14, 5), (CF1 - 10, 25), (CF1 - 6, 8), (CF1, 25)):
    fpb.inputs["Emission Strength"].default_value = v; fpb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
vis(fpain, [(CF1 - 22, CF1)], recursive=False)
vis(brain, BRAIN_SHOTS)
for s_ in shards: vis(s_, rng("brain_ice"), recursive=False)
for d in dust: vis(d, [(BURST, BI1)], recursive=False)
for p_ in paths + [stem]: vis(p_, rng("confused"), recursive=False)
vis(fpain, [(CF1 - 22, CF1)], recursive=False)
# brain studiya poli (qora yaltiroq)
plane("bfloor", (12, 12), tuple(B0 + Vector((0, 0, -0.75))), mat("bfloor_m", (0.01, 0.012, 0.02), 0.15, coat=1.0), parent=bstudio)
vis(bstudio, BRAIN_SHOTS)
vis(street, STREET_SHOTS)

# ======================================================================
# 4) OG'IZ ICHI (30,0,0) — masshtab x10: tanglay, tishlar, til, tomirlar
# ======================================================================
M0 = Vector((30, 0, 0))
mouth = empty("mouth", tuple(M0))
PA, PB, PC = 0.30, 0.42, 0.18                 # tanglay gumbazi yarim o'qlari
def zdome(x, y):
    q = 1 - (x / PA) ** 2 - (y / PB) ** 2
    return PC * math.sqrt(max(0.0, q))
CONTACT = Vector((0.0, -0.17, zdome(0, -0.17)))
TCONTACT = Vector((0.0, -0.05, zdome(0, -0.05)))      # til tegadigan joy
# --- tanglay materiali: ho'l pushti + qirov + rentgen + issiqlik ---
pal_m = bpy.data.materials.new("palate"); pal_m.use_nodes = True
N = pal_m.node_tree.nodes; L = pal_m.node_tree.links; pb_ = N["Principled BSDF"]; outp = N["Material Output"]
tc = N.new("ShaderNodeTexCoord")
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs[0])
crp = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], crp.inputs[0])
crp.color_ramp.elements[0].color = (0.62, 0.2, 0.24, 1); crp.color_ramp.elements[1].color = (0.9, 0.48, 0.5, 1)
frost_r = value_node(pal_m, "frost", 0.0); warm_r = value_node(pal_m, "warm", 0.0); xr = value_node(pal_m, "xr", 0.0)
def radial(center, radius_sock, soft=0.08):
    vm = N.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"; L.new(tc.outputs["Object"], vm.inputs[0]); vm.inputs[1].default_value = tuple(center)
    nzv = N.new("ShaderNodeTexNoise"); nzv.inputs["Scale"].default_value = 9; L.new(tc.outputs["Object"], nzv.inputs[0])
    dd = N.new("ShaderNodeMath"); dd.operation = "ADD"; L.new(vm.outputs["Value"], dd.inputs[0])
    nm_ = N.new("ShaderNodeMath"); nm_.operation = "MULTIPLY"; nm_.inputs[1].default_value = 0.08; L.new(nzv.outputs["Fac"], nm_.inputs[0]); L.new(nm_.outputs[0], dd.inputs[1])
    mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"; L.new(dd.outputs[0], mr.inputs["Value"])
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; L.new(radius_sock, sub.inputs[0]); sub.inputs[1].default_value = soft
    L.new(sub.outputs[0], mr.inputs["From Min"]); L.new(radius_sock, mr.inputs["From Max"])
    mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
    return mr.outputs[0]
fmask = radial(CONTACT, frost_r, 0.1); wmask = radial(TCONTACT, warm_r, 0.12)
cmx = N.new("ShaderNodeMix"); cmx.data_type = "RGBA"; L.new(fmask, cmx.inputs["Factor"]); L.new(crp.outputs[0], cmx.inputs[6])
cmx.inputs[7].default_value = (0.78, 0.9, 1.0, 1); L.new(cmx.outputs[2], pb_.inputs["Base Color"])
rmx = N.new("ShaderNodeMix"); rmx.data_type = "FLOAT"; L.new(fmask, rmx.inputs["Factor"]); rmx.inputs[2].default_value = 0.12; rmx.inputs[3].default_value = 0.45
L.new(rmx.outputs[0], pb_.inputs["Roughness"])
pb_.inputs["Subsurface Weight"].default_value = 0.6; pb_.inputs["Subsurface Scale"].default_value = 0.01
pb_.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
pb_.inputs["Coat Weight"].default_value = 1.0; pb_.inputs["Coat Roughness"].default_value = 0.03
# qirov kristallari (bump) + emissiya: sovuq ko'k, issiq to'q sariq
vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 90; L.new(tc.outputs["Object"], vor.inputs[0])
fbm = N.new("ShaderNodeMath"); fbm.operation = "MULTIPLY"; L.new(vor.outputs["Distance"], fbm.inputs[0]); L.new(fmask, fbm.inputs[1])
bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.6; bmp.inputs["Distance"].default_value = 0.004
L.new(fbm.outputs[0], bmp.inputs["Height"]); L.new(bmp.outputs[0], pb_.inputs["Normal"])
emc = N.new("ShaderNodeMix"); emc.data_type = "RGBA"; L.new(wmask, emc.inputs["Factor"])
emc.inputs[6].default_value = (0.35, 0.7, 1.0, 1); emc.inputs[7].default_value = (1.0, 0.45, 0.1, 1)
L.new(emc.outputs[2], pb_.inputs["Emission Color"])
ems = N.new("ShaderNodeMath"); ems.operation = "ADD"
e1 = N.new("ShaderNodeMath"); e1.operation = "MULTIPLY"; e1.inputs[1].default_value = 0.6; L.new(fmask, e1.inputs[0])
e2 = N.new("ShaderNodeMath"); e2.operation = "MULTIPLY"; e2.inputs[1].default_value = 3.0; L.new(wmask, e2.inputs[0])
L.new(e1.outputs[0], ems.inputs[0]); L.new(e2.outputs[0], ems.inputs[1]); L.new(ems.outputs[0], pb_.inputs["Emission Strength"])
# rentgen aralashmasi
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
xem = N.new("ShaderNodeEmission"); xem.inputs["Color"].default_value = (1.0, 0.45, 0.5, 1)
xs = N.new("ShaderNodeMath"); xs.operation = "MULTIPLY"; xs.inputs[1].default_value = 0.8; L.new(lw.outputs["Facing"], xs.inputs[0]); L.new(xs.outputs[0], xem.inputs["Strength"])
xtr = N.new("ShaderNodeBsdfTransparent")
xmx = N.new("ShaderNodeMixShader"); xmx.inputs[0].default_value = 0.25; L.new(xtr.outputs[0], xmx.inputs[1]); L.new(xem.outputs[0], xmx.inputs[2])
wglow = N.new("ShaderNodeEmission"); wglow.inputs["Color"].default_value = (1.0, 0.45, 0.1, 1)
wgs = N.new("ShaderNodeMath"); wgs.operation = "MULTIPLY"; wgs.inputs[1].default_value = 2.5; L.new(wmask, wgs.inputs[0]); L.new(wgs.outputs[0], wglow.inputs["Strength"])
xadd = N.new("ShaderNodeAddShader"); L.new(xmx.outputs[0], xadd.inputs[0]); L.new(wglow.outputs[0], xadd.inputs[1])
fin = N.new("ShaderNodeMixShader"); L.new(xr, fin.inputs[0]); L.new(pb_.outputs[0], fin.inputs[1]); L.new(xadd.outputs[0], fin.inputs[2])
L.new(fin.outputs[0], outp.inputs["Surface"])
# --- og'iz qismlari uchun materiallar ---
cheek_m = mat("cheek", (0.45, 0.1, 0.12), 0.25, sss=0.5, sss_scale=0.02, coat=0.8)
tooth_m = mat("tooth", (0.95, 0.93, 0.86), 0.18, sss=0.3, sss_scale=0.005, coat=0.9)
gum_m = mat("gum", (0.78, 0.32, 0.36), 0.3, sss=0.6, sss_scale=0.01, coat=0.8)
tng_m = bpy.data.materials.new("tongue"); tng_m.use_nodes = True
N = tng_m.node_tree.nodes; L = tng_m.node_tree.links; tb = N["Principled BSDF"]
tb.inputs["Base Color"].default_value = (0.82, 0.32, 0.36, 1); tb.inputs["Roughness"].default_value = 0.3
tb.inputs["Subsurface Weight"].default_value = 0.7; tb.inputs["Subsurface Scale"].default_value = 0.01
tb.inputs["Coat Weight"].default_value = 0.8; tb.inputs["Coat Roughness"].default_value = 0.1
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 70; L.new(tc.outputs["Object"], vo.inputs[0])
tbp = N.new("ShaderNodeBump"); tbp.inputs["Strength"].default_value = 0.5; tbp.inputs["Distance"].default_value = 0.003
L.new(vo.outputs["Distance"], tbp.inputs["Height"]); L.new(tbp.outputs[0], tb.inputs["Normal"])
twarm = value_node(tng_m, "warm", 0.0)
tb.inputs["Emission Color"].default_value = (1.0, 0.4, 0.08, 1); L.new(twarm, tb.inputs["Emission Strength"])
mt_b = mint.node_tree.nodes["Principled BSDF"]; mt_b.inputs["Emission Color"].default_value = (0.3, 0.7, 1.0, 1)
mt_b.inputs["Emission Strength"].default_value = 0.0
# tomir materiali: sovuq (ko'k), issiq (to'q sariq), egri bo'ylab issiqlik to'lqini
ves_m = bpy.data.materials.new("vessel"); ves_m.use_nodes = True
N = ves_m.node_tree.nodes; L = ves_m.node_tree.links; vb = N["Principled BSDF"]
vb.inputs["Roughness"].default_value = 0.35; vb.inputs["Subsurface Weight"].default_value = 0.3; vb.inputs["Coat Weight"].default_value = 0.6
v_cold = value_node(ves_m, "cold", 0.0); v_hot = value_node(ves_m, "hot", 0.0); v_pos = value_node(ves_m, "pos", -1.0)
ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
vc = N.new("ShaderNodeMix"); vc.data_type = "RGBA"; L.new(v_cold, vc.inputs["Factor"])
vc.inputs[6].default_value = (0.75, 0.02, 0.02, 1); vc.inputs[7].default_value = (0.12, 0.12, 0.6, 1); L.new(vc.outputs[2], vb.inputs["Base Color"])
ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; L.new(v_cold, ec.inputs["Factor"])
ec.inputs[6].default_value = (1.0, 0.04, 0.02, 1); ec.inputs[7].default_value = (0.1, 0.3, 1.0, 1)
ds = N.new("ShaderNodeMath"); ds.operation = "SUBTRACT"; L.new(ua.outputs["Fac"], ds.inputs[0]); L.new(v_pos, ds.inputs[1])
ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(ds.outputs[0], ab.inputs[0])
pl_ = N.new("ShaderNodeMapRange"); L.new(ab.outputs[0], pl_.inputs["Value"]); pl_.inputs["From Min"].default_value = 0.0; pl_.inputs["From Max"].default_value = 0.15
pl_.inputs["To Min"].default_value = 1.0; pl_.inputs["To Max"].default_value = 0.0
ec2 = N.new("ShaderNodeMix"); ec2.data_type = "RGBA"; L.new(pl_.outputs[0], ec2.inputs["Factor"]); L.new(ec.outputs[2], ec2.inputs[6])
ec2.inputs[7].default_value = (1.0, 0.35, 0.02, 1); L.new(ec2.outputs[2], vb.inputs["Emission Color"])
es = N.new("ShaderNodeMath"); es.operation = "MULTIPLY_ADD"; L.new(v_hot, es.inputs[0]); es.inputs[1].default_value = 1.6; es.inputs[2].default_value = 0.5
es2 = N.new("ShaderNodeMath"); es2.operation = "MULTIPLY_ADD"; L.new(pl_.outputs[0], es2.inputs[0]); es2.inputs[1].default_value = 6.0; L.new(es.outputs[0], es2.inputs[2])
L.new(es2.outputs[0], vb.inputs["Emission Strength"])
scoop_tex2 = bpy.data.textures.new("mscoop_cl", "CLOUDS"); scoop_tex2.noise_scale = 0.06
import bmesh

def build_mouth(tag, root, interior):
    """og'iz qismlari root ichida mahalliy koordinatada (x10 masshtab: tanglay eni 0.6). interior=True: lunj devori ham."""
    parts = {"vessels": []}
    # tanglay gumbazi (ichki sirt), ko'ndalang burmalar (rugae)
    SEGU, SEGV = 160, 60
    verts, faces = [], []
    for i in range(SEGV + 1):
        th = (i / SEGV) * (math.pi / 2)
        for j in range(SEGU):
            ph = 2 * math.pi * j / SEGU
            x = PA * math.sin(th) * math.cos(ph); y = PB * math.sin(th) * math.sin(ph); z = PC * math.cos(th)
            front = max(0.0, min(1.0, (-y - 0.02) / 0.1)) * max(0.0, 1 - abs(x) / (PA * 0.75))
            rug = max(0.0, math.sin(y * 70 + 2.5 * math.sin(x * 22))) ** 2
            z -= 0.011 * rug * front
            z -= 0.004 * math.exp(-(x / 0.012) ** 2) * (1 if y < 0.2 else 0.3)
            verts.append((x, y, z))
    for i in range(SEGV):
        for j in range(SEGU):
            a = i * SEGU + j; b2 = i * SEGU + (j + 1) % SEGU
            faces.append((a, b2, b2 + SEGU, a + SEGU))
    me = bpy.data.meshes.new(tag + "palate"); me.from_pydata(verts, [], faces); me.update()
    pal = bpy.data.objects.new(tag + "palate", me); sc.collection.objects.link(pal); pal.parent = root
    pal.data.materials.append(pal_m); pal.data.shade_smooth(); parts["palate"] = pal
    if interior:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1, location=(0, 0, 0))
        ch = bpy.context.object; ch.name = tag + "cheeks"; ch.scale = (0.4, 0.6, 0.38); bpy.ops.object.transform_apply(scale=True)
        bm = bmesh.new(); bm.from_mesh(ch.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.36], context="VERTS"); bm.to_mesh(ch.data); bm.free()
        ch.data.materials.append(cheek_m); ch.data.shade_smooth(); ch.parent = root; ch.location = (0, 0.05, -0.12)
    # tishlar
    def arch_teeth(prefix, a, b, z, down=True, n=16):
        for k in range(n):
            ang = math.radians(195 + (k + 0.5) / n * 150)
            x = a * math.cos(ang); y = b * math.sin(ang)
            front = max(0.0, -math.sin(ang))
            w = 0.05 if front > 0.85 else 0.065
            h = 0.08 if front > 0.85 else 0.06
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(0, 0, 0))
            t = bpy.context.object; t.name = f"{tag}{prefix}{k}"
            t.scale = (w / 2, 0.02 if front > 0.85 else 0.032, h / 2); bpy.ops.object.transform_apply(scale=True)
            for v in t.data.vertices:                     # tekisroq tish (to'rtburchak-yumaloq)
                v.co.x = math.copysign(abs(v.co.x / (w / 2)) ** 0.6 * (w / 2), v.co.x)
                v.co.z = math.copysign(abs(v.co.z / (h / 2)) ** 0.5 * (h / 2), v.co.z)
            t.location = (x, y, z + (-h / 2 if down else h / 2)); t.rotation_euler = (0, 0, math.atan2(y / b, x / a) + math.pi / 2)
            t.data.materials.append(tooth_m); t.data.shade_smooth(); t.parent = root
    arch_teeth("utooth", PA * 0.93, PB * 0.93, 0.0, True)
    arch_teeth("ltooth", PA * 0.9, PB * 0.9, -0.32, False)
    for nm_, z in (("ugum", 0.0), ("lgum", -0.32)):
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.05, major_segments=96, location=(0, 0, 0))
        g = bpy.context.object; g.name = tag + nm_; g.scale = (PA * 0.93, PB * 0.93, 0.6); g.location = (0, 0, z)
        g.data.materials.append(gum_m); g.data.shade_smooth(); g.parent = root
    # til
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1, location=(0, 0, 0))
    tng = bpy.context.object; tng.name = tag + "tongue"; tng.scale = (0.24, 0.36, 0.11); bpy.ops.object.transform_apply(scale=True)
    for v in tng.data.vertices:
        if v.co.z > 0: v.co.z -= 0.012 * math.exp(-(v.co.x / 0.03) ** 2)
    tng.data.materials.append(tng_m); tng.data.shade_smooth()
    tngR = empty(tag + "tongueR", (0, 0.04, -0.2), root); tng.parent = tngR
    parts["tng"], parts["tngR"] = tng, tngR
    # muzqaymoq sharchasi (yalpizli)
    scoopR = empty(tag + "scoopR", (0, 0, 0), root)
    s_ = sphere(tag + "mscoop", 0.12, (0, 0, 0), mint, scale=(1, 1, 0.8), sub=5)
    d = s_.modifiers.new("lump", "DISPLACE"); d.texture = scoop_tex2; d.strength = 0.025; s_.parent = scoopR
    parts["scoopR"], parts["scoop"] = scoopR, s_
    # tomirlar (tanglay to'qimasi ichida, gumbazdan 1.2 sm yuqorida)
    rv = random.Random(5)
    def on_dome(x, y, off=0.012): return (x, y, zdome(x, y) + off)
    V = parts["vessels"]
    for sx in (-1, 1):
        main = [on_dome(sx * (0.19 - 0.05 * t), 0.3 - 0.58 * t) for t in [k / 8 for k in range(9)]]
        V.append(P.tube(f"{tag}ves_main{sx}", main, 0.016, ves_m, root))
        for k in range(7):
            t = (k + 0.5) / 7; x0, y0 = sx * (0.19 - 0.05 * t), 0.3 - 0.58 * t
            pts = [on_dome(x0, y0)]
            for s in range(1, 5):
                pts.append(on_dome(x0 - sx * 0.045 * s + rv.uniform(-0.012, 0.012), y0 + rv.uniform(-0.025, 0.025) - 0.008 * s))
            V.append(P.tube(f"{tag}ves_b{sx}_{k}", pts, 0.009, ves_m, root))
            for q in range(2):
                c0 = Vector(pts[2 + q]); pts2 = [tuple(c0)]
                for s in range(1, 4):
                    nx = max(-PA * 0.8, min(PA * 0.8, c0.x + rv.uniform(-0.035, 0.035)))
                    pts2.append(on_dome(nx, c0.y + rv.uniform(-0.04, 0.04) * s))
                V.append(P.tube(f"{tag}ves_c{sx}_{k}_{q}", pts2, 0.0045, ves_m, root))
    return parts

mouth = empty("mouth", tuple(M0))
MA = build_mouth("A_", mouth, True)                         # alohida makro (og'iz ichidan)
mouthH = empty("mouthH", (0, 0.028, 0.047), headE)          # rentgen boshning ichida, haqiqiy o'lcham
mouthH.rotation_euler = (R(-90), 0, 0); mouthH.scale = (0.1, 0.1, 0.1)
MB = build_mouth("B_", mouthH, False)
vessels = MA["vessels"] + MB["vessels"]
TO0, TO1 = S["touch"]; CO0, CO1 = S["constrict"]; WA0, WA1 = S["warm"]; DI0, DI1 = S["dilate"]
TG0, TG1 = S["tongue"]; CA0, CA1 = S["calm"]
HIT = TO0 + 20                                 # "tanglayingizga tekkanda" (10.1 s -> 243)
sc_hit = CONTACT + Vector((0, -0.01, -0.095))
for M in (MA, MB):
    key(M["scoopR"], TO0, loc=tuple(sc_hit + Vector((0, -0.6, -0.04))))
    key(M["scoopR"], HIT, loc=tuple(sc_hit)); key(M["scoopR"], CA1, loc=tuple(sc_hit + Vector((0, 0.0, 0.004))))
    key(M["scoop"], TO0, scale=(1, 1, 0.8)); key(M["scoop"], HIT, scale=(1, 1, 0.8)); key(M["scoop"], HIT + 3, scale=(1.12, 1.12, 0.66))
    key(M["scoop"], HIT + 8, scale=(1.08, 1.08, 0.7))
    # til ko'tariladi va tanglayga bosiladi
    key(M["tngR"], 1, loc=(0, 0.04, -0.2), rot=(0, 0, 0)); key(M["tngR"], TG0 + 6, loc=(0, 0.04, -0.2), rot=(0, 0, 0))
    key(M["tngR"], TG0 + 30, loc=(0, 0.02, -0.035), rot=(-9, 0, 0)); key(M["tngR"], CA1, loc=(0, 0.02, -0.032), rot=(-9, 0, 0))
    key(M["tng"], TG0 + 26, scale=(1, 1, 1)); key(M["tng"], TG0 + 34, scale=(1.06, 1.04, 0.9))
val_key(pal_m, "frost", 1, 0.0); val_key(pal_m, "frost", HIT, 0.0); val_key(pal_m, "frost", HIT + 18, 0.2)
val_key(pal_m, "frost", CO1, 0.26); val_key(pal_m, "frost", DI1, 0.3); val_key(pal_m, "frost", CA0 + 6, 0.3); val_key(pal_m, "frost", CA1 - 10, 0.0)
val_key(pal_m, "xr", 1, 0.0); val_key(pal_m, "xr", CO0 - 1, 0.0); val_key(pal_m, "xr", CO0, 0.7)
val_key(pal_m, "warm", 1, 0.0); val_key(pal_m, "warm", CA0 + 4, 0.0); val_key(pal_m, "warm", CA1 - 6, 0.55)
SQ = 297                                       # "birdan torayadi" (12.4 s)
DIL = 437                                      # "kengaytirib" (18.2 s)
def ves_r(f, k):
    for t_ in vessels: P.tube_r(t_, f, t_["r0"] * k)
ves_r(1, 1.0); ves_r(SQ - 3, 1.0); ves_r(SQ + 5, 0.38); ves_r(WA1, 0.4); ves_r(DIL - 2, 0.42); ves_r(DIL + 4, 1.75)
for f in range(DIL + 8, DI1 + 1, 9):
    ves_r(f, 1.55); ves_r(f + 4, 1.8)
ves_r(TG0, 1.7); ves_r(CA0 + 8, 1.7); ves_r(CA1 - 8, 1.0)
val_key(ves_m, "cold", 1, 0.0); val_key(ves_m, "cold", SQ - 3, 0.0); val_key(ves_m, "cold", SQ + 6, 1.0)
val_key(ves_m, "cold", WA0 + 20, 1.0); val_key(ves_m, "cold", WA1, 0.3); val_key(ves_m, "cold", DIL, 0.0)
val_key(ves_m, "hot", 1, 0.0); val_key(ves_m, "hot", WA0 + 10, 0.0); val_key(ves_m, "hot", WA1, 0.5); val_key(ves_m, "hot", DIL + 4, 1.6)
for f in range(DIL + 8, DI1 + 1, 9):
    val_key(ves_m, "hot", f, 1.0); val_key(ves_m, "hot", f + 4, 1.8)
val_key(ves_m, "hot", CA0 + 8, 1.4); val_key(ves_m, "hot", CA1 - 8, 0.15)
val_key(ves_m, "pos", 1, -0.3); val_key(ves_m, "pos", WA0 + 8, -0.25); val_key(ves_m, "pos", WA0 + 44, 1.25)
val_key(ves_m, "pos", WA0 + 45, -0.25); val_key(ves_m, "pos", WA1, 1.25)
val_key(tng_m, "warm", 1, 0.0); val_key(tng_m, "warm", TG0 + 26, 0.0); val_key(tng_m, "warm", TG1, 0.8); val_key(tng_m, "warm", CA0 + 20, 2.0)
MOUTH_X = rng("constrict", "warm", "dilate", "tongue", "calm")
vis(mouth, rng("touch"))
for t_ in MA["vessels"]: vis(t_, [], recursive=False)
vis(mouthH, MOUTH_X)
vis(MB["scoopR"], rng("constrict", "warm", "dilate"))

# ======================================================================
# 5) KAMERALAR
# ======================================================================
HO0, HO1 = S["hook"]; FA0, FA1 = S["face"]; PW0, PW1 = S["pain_wide"]; CL0, CL1 = S["close"]; RE0, RE1 = S["relief"]
mouthT = empty("mouthT", (0, 0.03, 0.1), headE)
# 1 ilgak: pastdan, muzqaymoqqa juda yaqin
coneT = empty("coneT", (0, 0, 0.06), coneR)
c = shot_cam("hook", (0.3, -0.55, 1.2), mouthT, 26, 2.8, focus=coneT)
path_keys(c, ((HO0, (0.34, -0.62, 1.12)), (HO1, (0.16, -0.36, 1.3))))
lens_keys(c, ((HO0, 24), (HO1, 34)))
# 2 yuzga crash zoom
c = shot_cam("face", (0.15, -1.3, 1.45), faceT, 20, 2.2, focus=faceT)
lens_keys(c, ((FA0, 18), (FA0 + 5, 55), (FA1, 62)))
path_keys(c, ((FA0, (0.18, -1.35, 1.42)), (FA1, (0.05, -1.2, 1.5))))
shake(c, FA0 + 4, FA0 + 16, 0.02, 2)
# 3 rentgen chaqnash
c = shot_cam("xflash", (-0.4, -0.75, 1.62), faceT, 40, 4.0, focus=faceT)
path_keys(c, ((XF0, (-0.42, -0.85, 1.12)), (XF1, (-0.2, -0.7, 1.2))))
lens_keys(c, ((XF0, 34), (XF1, 48)))
shake(c, XF0 + 4, XF0 + 14, 0.012, 3)
# 4 miya + muz
bT = empty("brainT", tuple(B0 + Vector((0, 0, 0.12))))
c = shot_cam("brain_ice", (0, 0, 0), bT, 40, 5.6, focus=bT)
for f in range(BI0, BI1 + 1, 3):
    a = R(-70 + 50 * (f - BI0) / (BI1 - BI0)); rr = 2.2 - 0.5 * (f - BI0) / (BI1 - BI0)
    key(c, f, loc=tuple(B0 + Vector((rr * math.sin(a), -rr * math.cos(a), 0.35 + 0.1 * (f - BI0) / (BI1 - BI0)))))
interp(c, "LINEAR", "location")
shake(c, BURST, BURST + 14, 0.08, 4)
# 5 og'iz ichidan (makro)
palT = empty("palT", tuple(M0 + Vector((0, -0.12, 0.1))))
c = shot_cam("touch", (0, 0, 0), palT, 16, 8.0, focus=palT)
path_keys(c, ((TO0, tuple(M0 + Vector((0.05, 0.16, -0.035)))), (HIT, tuple(M0 + Vector((0.02, 0.11, -0.03)))),
              (TO1, tuple(M0 + Vector((0.0, 0.08, -0.025))))))
shake(c, HIT, HIT + 10, 0.012, 5)
# 6-8, 14-15 rentgen bosh ichidagi tanglay (boshga bog'langan kameralar)
mC = empty("mouthC", (0, 0.04, 0.05), headE)
def head_cam(name, keys, lens, fstop=6.0, target=mC):
    rig = empty("rig_" + name, (0, 0, 0))
    c_ = rig.constraints.new("COPY_LOCATION"); c_.target = headE
    c = shot_cam(name, (0, 0, 0), target, lens, fstop, focus=target); c.parent = rig
    for f, p in keys: key(c, f, loc=p)
    return c
c = head_cam("constrict", ((CO0, (0.2, -0.22, 0.12)), (CO1, (0.14, -0.17, 0.09))), 40)
shake(c, SQ, SQ + 8, 0.004, 6)
c = head_cam("warm", [(f, (0.24 * math.sin(R(-50 + 90 * (f - WA0) / (WA1 - WA0))), -0.24 * math.cos(R(-50 + 90 * (f - WA0) / (WA1 - WA0))), 0.1))
                      for f in range(WA0, WA1 + 1, 3)], 42)
interp(c, "LINEAR", "location")
c = head_cam("dilate", ((DI0, (-0.2, -0.2, 0.1)), (DIL, (-0.17, -0.17, 0.08)), (DI1, (-0.15, -0.15, 0.07))), 40)
lens_keys(c, ((DI0, 38), (DIL - 1, 38), (DIL + 3, 58), (DI1, 62)))
shake(c, DIL, DIL + 12, 0.005, 7)
c = head_cam("tongue", ((TG0, (0.15, -0.25, -0.05)), (TG1, (0.12, -0.2, -0.03))), 40)
c = head_cam("calm", ((CA0, (0.18, -0.22, 0.1)), (CA1, (0.12, -0.18, 0.08))), 42)
# 9-10 rentgen yuz: asab, signal
c = shot_cam("nerve", (0, 0, 0), faceT, 45, 4.0, focus=faceT)
path_keys(c, ((NV0, (0.55, -0.55, 1.5)), (NV1, (0.3, -0.62, 1.55))))
sigT = empty("sigT", (0.03, 0.08, 0.05), headE)
c = shot_cam("signal", (0, 0, 0), sigT, 50, 4.0, focus=sigT)
path_keys(c, ((SG0, (0.45, -0.25, 1.48)), (SG1, (0.42, 0.05, 1.62))))
# 11 adashgan miya: aylanma
c = shot_cam("confused", (0, 0, 0), bT, 35, 5.6, focus=bT)
for f in range(CF0, CF1 + 1, 3):
    a = R(30 + 110 * (f - CF0) / (CF1 - CF0))
    key(c, f, loc=tuple(B0 + Vector((2.0 * math.sin(a), -2.0 * math.cos(a), 0.6 - 0.3 * (f - CF0) / (CF1 - CF0)))))
interp(c, "LINEAR", "location")
# 12 pastdan keng plan
chestT = empty("chestT", (0, 0, 1.15))
c = shot_cam("pain_wide", (0, 0, 0), chestT, 16, 5.6, focus=faceT)
path_keys(c, ((PW0, (0.75, -1.75, 0.22)), (PW1, (0.45, -1.35, 0.3))))
shake(c, PW0, PW0 + 10, 0.03, 8)
# 13 yuzga yaqin, DOF
c = shot_cam("close", (0, 0, 0), faceT, 45, 2.0, focus=faceT)
path_keys(c, ((CL0, (-0.3, -0.9, 1.4)), (CL1, (-0.2, -0.66, 1.48))))
# 16 yengillik: orqaga va tepaga
c = shot_cam("relief", (0, 0, 0), faceT, 30, 4.0, focus=faceT)
path_keys(c, ((RE0, (0.2, -0.9, 1.45)), (RE1, (1.1, -2.9, 2.3))))
lens_keys(c, ((RE0, 32), (RE1, 24)))
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 6) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Rotation"].default_value = (0, 0, R(200)); L.new(tcw.outputs["Generated"], mpw.inputs[0])
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
bg_sky = N.new("ShaderNodeBackground"); L.new(env.outputs[0], bg_sky.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.003, 0.008, 0.02, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_sky.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1]); L.new(a1.outputs[0], out.inputs["Surface"])
WL = {n: ((1.0, 0.0) if (f, n) and n in ("hook", "face", "pain_wide", "close", "relief") else (0.0, 1.0)) for f, n in SHOTS}
for f, n in SHOTS:
    s1, s2 = WL[n]
    for bgn, v in ((bg_sky, s1), (bg_dk, s2)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(50), 0, R(150))
for f, e in lights_for(STREET_SHOTS, 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("face_fill", (-0.8, -1.4, 1.7), 0.8, (1.0, 0.92, 0.85), lights_for(STREET_SHOTS, 60.0), target=faceT)
area("face_rim", (0.6, 1.0, 2.0), 0.6, (1.0, 0.8, 0.6), lights_for(STREET_SHOTS, 80.0), target=faceT)
area("pain_red", (0.9, -1.0, 0.8), 1.0, (1.0, 0.08, 0.04), [(1, 0), (PW0, 400), (PW0 + 3, 120), (PW0 + 12, 0)], target=faceT)
# rentgen
area("x_rim", (-0.8, 0.4, 2.0), 0.8, (0.3, 0.6, 1.0), lights_for(XRAY_SHOTS, 40.0), target=faceT)
# miya studiyasi
B_on = BRAIN_SHOTS
area("b_key", tuple(B0 + Vector((-1.6, -1.8, 1.8))), 1.2, (1.0, 0.9, 0.85), lights_for(B_on, 260.0), target=bT)
area("b_rim", tuple(B0 + Vector((1.5, 1.6, 1.2))), 1.2, (0.3, 0.6, 1.0), lights_for(B_on, 400.0), target=bT)
area("b_rim2", tuple(B0 + Vector((-1.5, 1.4, 0.4))), 1.0, (0.5, 0.75, 1.0), lights_for(B_on, 250.0), target=bT)
point("b_burst", tuple(B0 + Vector((0, -0.6, 0.3))), 0.3, (1.0, 0.6, 0.35), [(1, 0), (BURST, 300), (BURST + 4, 120), (BURST + 14, 0)], const=False)
# og'iz: tashqaridan (og'iz teshigidan) iliq nur + ichki to'ldiruvchi
area("m_front", tuple(M0 + Vector((0.1, -0.95, -0.1))), 0.4, (1.0, 0.9, 0.8), lights_for(MOUTH_SHOTS, 35.0), target=palT)
area("m_fill", tuple(M0 + Vector((-0.15, -0.3, -0.22))), 0.15, (1.0, 0.75, 0.7), lights_for(MOUTH_SHOTS, 6.0), target=palT)
area("m_blue", tuple(M0 + Vector((0.2, -0.2, -0.25))), 0.15, (0.4, 0.7, 1.0), lights_for(rng("touch"), 6.0), target=palT)
area("mx_key", (0.5, -0.9, 1.9), 0.6, (1.0, 0.93, 0.88), lights_for(MOUTH_X, 30.0), target=mC)
area("mx_rim", (-0.6, 0.3, 1.9), 0.6, (0.3, 0.6, 1.0), lights_for(MOUTH_X, 40.0), target=mC)
point("m_cold", tuple(M0 + CONTACT + Vector((0, 0, -0.06))), 0.05, (0.4, 0.75, 1.0), [(1, 0), (HIT, 0.5), (HIT + 6, 2.0), (CO1 + 1, 0)], const=False)
point("m_warm", tuple(M0 + TCONTACT + Vector((0, 0, -0.07))), 0.08, (1.0, 0.5, 0.15), [(1, 0), (CA0, 0.5), (CA1, 6.0), (CA1 + 1, 0)], const=False)

# ======================================================================
# 7) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 8
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
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
