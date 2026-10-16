"""
Zack D. Films uslubidagi qisqa video: "Havoda suzuvchi" 3D piyodalar o'tish joyi.
Ishga tushirish:  python3 build_scene.py   (pip install bpy)
Natija: video/scene.blend  +  video/proj.png (anamorfik proyeksiya rasmi)
"""
import bpy, bmesh, math, os, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_IMG = os.path.join(HERE, "proj.png")
FPS = 30
END = 885
random.seed(7)

# ------------------------------------------------------------------ asosiy
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, END

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.32, 0.55, 1.0, 1)
bg.inputs["Strength"].default_value = 0.55


def link(obj):
    scene.collection.objects.link(obj)
    return obj


def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def box(name, size, loc, mat=None, bevel=0.0, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    o = mesh_obj(name, bm)
    o.location = loc
    if bevel:
        m = o.modifiers.new("Bevel", 'BEVEL')
        m.width, m.segments = bevel, 3
        smooth(o)
    if mat:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def ellipsoid(name, radii, loc, mat=None, parent=None, seg=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    bmesh.ops.scale(bm, vec=radii, verts=bm.verts)
    o = mesh_obj(name, bm)
    o.location = loc
    smooth(o)
    if mat:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def cylinder(name, r, depth, loc, rot=(0, 0, 0), mat=None, parent=None, seg=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    o = mesh_obj(name, bm)
    o.location, o.rotation_euler = loc, rot
    if mat:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    e = link(bpy.data.objects.new(name, None))
    e.location = loc
    e.parent = parent
    return e


def mat(name, color, rough=0.5, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def noisy_mat(name, c1, c2, scale, rough=0.9, bump=0.3):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 8
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (*c1, 1)
    r.color_ramp.elements[1].color = (*c2, 1)
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    return m


def look(obj, target):
    d = Vector(target) - obj.matrix_world.translation if obj.parent else Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camera(name, loc, target, lens=35):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = 'AUTO'
    c = link(bpy.data.objects.new(name, cd))
    c.location = loc
    look(c, target)
    return c


def kf(obj, path, frame, value=None, index=-1):
    if value is not None:
        if index >= 0:
            getattr(obj, path)[index] = value
        else:
            setattr(obj, path, value)
    obj.keyframe_insert(path, frame=frame, index=index)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


# ------------------------------------------------------------------ materiallar
M_ASPH = noisy_mat("Asphalt", (0.025, 0.025, 0.028), (0.075, 0.075, 0.08), 260)
M_CONC = noisy_mat("Concrete", (0.42, 0.41, 0.39), (0.6, 0.59, 0.56), 40, 0.85, 0.15)
M_CURB = mat("Curb", (0.7, 0.7, 0.68), 0.7)
M_GRASS = noisy_mat("Grass", (0.10, 0.25, 0.05), (0.2, 0.42, 0.08), 30, 0.95, 0.4)
M_WHITE = mat("WhitePaint", (0.92, 0.92, 0.9), 0.55)
M_YELLOW = mat("YellowPaint", (0.9, 0.65, 0.05), 0.55)
M_SKIN = mat("Skin", (0.80, 0.55, 0.42), 0.45)
M_SKIN2 = mat("Skin2", (0.55, 0.36, 0.25), 0.45)
M_EYE = mat("EyeWhite", (0.95, 0.95, 0.95), 0.2)
M_PUPIL = mat("Pupil", (0.02, 0.02, 0.02), 0.1)
M_HAIR = mat("Hair", (0.08, 0.05, 0.03), 0.6)
M_HAIR2 = mat("Hair2", (0.35, 0.2, 0.08), 0.6)
M_ORANGE = mat("Vest", (1.0, 0.35, 0.02), 0.5)
M_HELMET = mat("Helmet", (1.0, 0.8, 0.05), 0.3)
M_JEANS = mat("Jeans", (0.08, 0.13, 0.3), 0.8)
M_GRAYPANTS = mat("Pants", (0.18, 0.18, 0.2), 0.8)
M_SHOE = mat("Shoe", (0.04, 0.04, 0.04), 0.5)
M_SHIRT = mat("Shirt", (0.15, 0.55, 0.85), 0.7)
M_SHIRT2 = mat("Shirt2", (0.9, 0.9, 0.85), 0.7)
M_TIRE = mat("Tire", (0.02, 0.02, 0.02), 0.8)
M_RIM = mat("Rim", (0.7, 0.7, 0.72), 0.25, 1.0)
M_GLASS = mat("Glass", (0.02, 0.04, 0.07), 0.05)
M_HEAD = mat("Headlight", (1.0, 0.95, 0.8), 0.1, emit=4)
M_TAIL = mat("Taillight", (0.9, 0.02, 0.02), 0.2, emit=2)
M_TRUNK = mat("Trunk", (0.25, 0.15, 0.08), 0.9)
M_LEAF = noisy_mat("Leaves", (0.08, 0.3, 0.06), (0.2, 0.5, 0.1), 8, 0.8, 0.5)
M_ROLLER = mat("Roller", (0.95, 0.95, 0.95), 0.9)
M_HANDLE = mat("Handle", (0.85, 0.1, 0.1), 0.4)

# ------------------------------------------------------------------ geometriya
# Yo'l Y o'qi bo'ylab yo'nalgan. O'tish joyi y = 0 atrofida. Yo'l kengligi 14 m (x: -7..7)
ROAD_W = 14.0
EYE = Vector((1.6, -21.2, 1.25))       # haydovchi ko'zi: illyuziya aynan shu nuqtadan to'g'ri
EYE_TARGET = Vector((0.0, 0.0, 0.3))

# Haqiqiy bloklar (faqat proyeksiya rasmi uchun)
BLOCK_X = [-3.5 + i for i in range(8)]
blocks = []
for i, x in enumerate(BLOCK_X):
    blocks.append(box(f"Block_{i}", (0.5, 3.0, 0.35), (x, 0, 0.275), M_WHITE))

sun_d = bpy.data.lights.new("Sun", 'SUN')
sun_d.energy = 5.0
sun_d.angle = math.radians(1.5)
sun = link(bpy.data.objects.new("Sun", sun_d))
# yorug'lik orqa-chapdan keladi -> soyalar o'ng tomonga va oldinga tushadi
sun.rotation_euler = (math.radians(53), 0, math.radians(-68))

bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
catcher = mesh_obj("ShadowCatcher", bm)
catcher.is_shadow_catcher = True

# ---- 1-bosqich: proyeksiya rasmini render qilish
pcd = bpy.data.cameras.new("ProjCam")
pcd.lens = 70
pcd.sensor_fit = 'HORIZONTAL'
proj_cam = link(bpy.data.objects.new("ProjCam", pcd))
proj_cam.location = EYE
look(proj_cam, EYE_TARGET)

scene.camera = proj_cam
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 4096, 1024
scene.render.resolution_percentage = 100
scene.cycles.samples = 256
scene.cycles.use_denoising = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = PROJ_IMG
if not os.environ.get("SKIP_PROJ"):
    bpy.ops.render.render(write_still=True)

for b in blocks:
    b.hide_render = b.hide_viewport = True
bpy.data.objects.remove(catcher, do_unlink=True)
scene.render.film_transparent = False

# ---- yo'l, trotuar, o't
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1)
road = mesh_obj("Road", bm)
road.scale = (ROAD_W, 220, 1)
road.data.materials.append(M_ASPH)

for s in (-1, 1):
    box("Curb", (0.25, 220, 0.16), (s * (ROAD_W / 2 + 0.125), 0, 0.08), M_CURB)
    box("Sidewalk", (3.2, 220, 0.14), (s * (ROAD_W / 2 + 0.25 + 1.6), 0, 0.07), M_CONC)
    box("Grass", (60, 220, 0.1), (s * (ROAD_W / 2 + 3.45 + 30), 0, 0.05), M_GRASS)

# yo'l chiziqlari (o'tish joyi va proyeksiya zonasidan tashqarida)
for y in range(-100, 100, 6):
    if -8 < y < 18:
        continue
    for x in (-3.5, 3.5):
        box("LaneDash", (0.15, 3.0, 0.004), (x, y + 1.5, 0.002), M_WHITE)
    box("Center", (0.12, 6.0, 0.004), (-0.1, y + 3, 0.002), M_YELLOW)
    box("Center", (0.12, 6.0, 0.004), (0.1, y + 3, 0.002), M_YELLOW)

# daraxtlar va binolar
for s in (-1, 1):
    for y in range(-90, 100, 9):
        x = s * (ROAD_W / 2 + 4.6 + random.uniform(0, 1.2))
        h = random.uniform(2.2, 3.2)
        cylinder("Trunk", 0.15, h, (x, y + random.uniform(-1, 1), h / 2), mat=M_TRUNK)
        ellipsoid("Leaves", (1.6, 1.6, 1.9), (x, y, h + 1.2), M_LEAF, seg=16)
    y = -110
    while y < 120:
        w = random.uniform(8, 16)
        h = random.uniform(6, 22)
        c = random.choice([(0.85, 0.75, 0.6), (0.7, 0.55, 0.45), (0.8, 0.8, 0.78), (0.6, 0.65, 0.7)])
        box("Building", (10, w - 1.0, h), (s * (ROAD_W / 2 + 15), y + w / 2, h / 2), mat("Bld", c, 0.8))
        y += w

# ---- 2-bosqich: anamorfik "bo'yoq" (decal) yerga proyeksiya qilinadi
bm = bmesh.new()
bm.loops.layers.uv.new("UVMap")
bmesh.ops.create_grid(bm, x_segments=280, y_segments=420, size=1, calc_uvs=True)
decal = mesh_obj("Crosswalk_3D_Paint", bm)
decal.scale = (ROAD_W, 21.0, 1)
decal.location = (0, 6.0, 0.004)          # y: -4.5 .. 16.5
uvp = decal.modifiers.new("Projector", 'UV_PROJECT')
uvp.uv_layer = decal.data.uv_layers[0].name
uvp.projector_count = 1
uvp.projectors[0].object = proj_cam
uvp.aspect_x, uvp.aspect_y = 4.0, 1.0

dm = bpy.data.materials.new("PaintDecal")
dm.use_nodes = True
nt = dm.node_tree
N, L = nt.nodes, nt.links
pb = N["Principled BSDF"]
pb.inputs["Roughness"].default_value = 0.6
tex = N.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(PROJ_IMG, check_existing=True)
tex.extension = 'CLIP'
L.new(tex.outputs["Color"], pb.inputs["Base Color"])

# bo'yash animatsiyasi uchun niqob (mask): har bir chiziq navbat bilan, oldidan orqaga bo'yaladi
geo = N.new("ShaderNodeNewGeometry")
sep = N.new("ShaderNodeSeparateXYZ")
L.new(geo.outputs["Position"], sep.inputs[0])
PAINT_T = N.new("ShaderNodeValue")
PAINT_T.name = "PaintProgress"
PAINT_T.outputs[0].default_value = 99.0
REV_Y0, REV_LEN = -2.6, 17.6


def mnode(op, a, b=None, clamp=False):
    n = N.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L.new(v, n.inputs[i])
    return n.outputs[0]


# u = EYE.x + (x - EYE.x) * dist0 / (y - EYE.y)  -> bloklar tekisligidagi x
dist0 = -EYE.y
yy = mnode('SUBTRACT', sep.outputs["Y"], EYE.y)
xx = mnode('SUBTRACT', sep.outputs["X"], EYE.x)
u = mnode('ADD', mnode('MULTIPLY', mnode('DIVIDE', xx, yy), dist0), EYE.x)
idx = mnode('FLOOR', mnode('ADD', u, 4.0))
prog = mnode('SUBTRACT', PAINT_T.outputs[0], idx, clamp=True)            # 0..1
front = mnode('ADD', mnode('MULTIPLY', prog, REV_LEN), REV_Y0)
mask = mnode('GREATER_THAN', front, sep.outputs["Y"])
alpha = mnode('MULTIPLY', mask, tex.outputs["Alpha"])
L.new(alpha, pb.inputs["Alpha"])
decal.data.materials.append(dm)

# oddiy (eski) zebra – 4-kadr uchun
normal_zebra = []
for x in BLOCK_X:
    normal_zebra.append(box("FlatZebra", (0.5, 3.0, 0.004), (x, 0, 0.004), M_WHITE))

# ------------------------------------------------------------------ odamlar


def person(name, shirt, pants, skin=M_SKIN, hair=M_HAIR, helmet=False, vest=False):
    root = empty(name)
    hips = empty(name + "_hips", (0, 0, 0.92), root)
    ellipsoid(name + "_torso", (0.2, 0.13, 0.33), (0, 0, 0.3), shirt, hips)
    if vest:
        ellipsoid(name + "_vest", (0.215, 0.145, 0.25), (0, 0, 0.36), M_ORANGE, hips)
    ellipsoid(name + "_pelvis", (0.18, 0.12, 0.12), (0, 0, 0.0), pants, hips)
    neck = empty(name + "_neck", (0, 0, 0.6), hips)
    head = ellipsoid(name + "_head", (0.115, 0.125, 0.14), (0, 0.0, 0.17), skin, neck)
    ellipsoid(name + "_nose", (0.02, 0.03, 0.03), (0, 0.125, -0.0), skin, head)
    eyes = []
    for s in (-1, 1):
        ew = ellipsoid(name + "_eye", (0.026, 0.018, 0.026), (s * 0.045, 0.105, 0.03), M_EYE, head, 16)
        ellipsoid(name + "_pupil", (0.012, 0.008, 0.012), (0, 0.016, 0), M_PUPIL, ew, 12)
        eyes.append(ew)
    brows = [box(name + "_brow", (0.045, 0.01, 0.01), (s * 0.045, 0.115, 0.07), hair, parent=head) for s in (-1, 1)]
    mouth = box(name + "_mouth", (0.045, 0.01, 0.008), (0, 0.118, -0.06), M_PUPIL, parent=head)
    if helmet:
        ellipsoid(name + "_helmet", (0.135, 0.145, 0.1), (0, 0, 0.08), M_HELMET, head)
        box(name + "_brim", (0.24, 0.1, 0.012), (0, 0.11, 0.06), M_HELMET, parent=head)
    else:
        ellipsoid(name + "_hair", (0.12, 0.13, 0.09), (0, -0.015, 0.08), hair, head)
    legs, arms = [], []
    for s in (-1, 1):
        lp = empty(name + "_legP", (s * 0.09, 0, 0.0), hips)
        ellipsoid(name + "_leg", (0.075, 0.075, 0.44), (0, 0, -0.44), pants, lp)
        box(name + "_shoe", (0.1, 0.22, 0.07), (0, 0.05, -0.88), M_SHOE, 0.02, lp)
        legs.append(lp)
        ap = empty(name + "_armP", (s * 0.235, 0, 0.53), hips)
        ellipsoid(name + "_arm", (0.055, 0.055, 0.31), (0, 0, -0.3), shirt, ap)
        ellipsoid(name + "_hand", (0.045, 0.05, 0.06), (0, 0, -0.63), skin, ap)
        arms.append(ap)
    return dict(root=root, hips=hips, neck=neck, head=head, eyes=eyes, brows=brows,
                mouth=mouth, legs=legs, arms=arms)


def walk_pose(p, f, phase, amp=0.45, arm_amp=0.4, base_arm=0.0, arms=True):
    s = math.sin(phase)
    for i, lp in enumerate(p["legs"]):
        kf(lp, "rotation_euler", f, s * amp * (1 if i == 0 else -1), 0)
    for i, ap in enumerate(p["arms"] if arms else []):
        kf(ap, "rotation_euler", f, base_arm - s * arm_amp * (1 if i == 0 else -1), 0)
    kf(p["hips"], "location", f, 0.92 + 0.025 * abs(math.cos(phase)), 2)


# ---- Ishchi (bo'yoqchi) + valik
worker = person("Worker", M_SHIRT2, M_GRAYPANTS, M_SKIN2, helmet=True, vest=True)
roller_rig = empty("RollerRig", (0, 1.15, 0.0), worker["root"])
handle = cylinder("Handle", 0.018, 1.12, (0, -0.33, 0.51), (math.radians(36.5), 0, 0), M_HANDLE, roller_rig)
roller = cylinder("Roller", 0.07, 0.42, (0, 0, 0.07), (0, math.radians(90), 0), M_ROLLER, roller_rig)
bucket = cylinder("Bucket", 0.17, 0.35, (-7.6, -2.6, 0.32), mat=M_WHITE)
cylinder("BucketLid", 0.172, 0.02, (0, 0, 0.18), mat=M_HANDLE, parent=bucket)

# ---- Piyoda
ped = person("Pedestrian", M_SHIRT, M_JEANS, M_SKIN, M_HAIR2)

# ---- Haydovchi (mashina ichida)


def car(name, color):
    root = empty(name)
    body_m = mat(name + "_paint", color, 0.25, 0.3)
    box(name + "_body", (1.9, 4.3, 0.62), (0, 0, 0.62), body_m, 0.12, root)
    # salon: tepasi torayadigan quti
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(1.62, 2.15, 0.56), verts=bm.verts)
    top = [v for v in bm.verts if v.co.z > 0]
    for v in top:
        v.co.x *= 0.86
        v.co.y = v.co.y * 0.62 - 0.12
    cab = mesh_obj(name + "_cabin", bm)
    cab.location = (0, -0.25, 1.2)
    cab.parent = root
    bev = cab.modifiers.new("Bevel", 'BEVEL')
    bev.width, bev.segments = 0.06, 2
    cab.data.materials.append(M_GLASS)
    box(name + "_roof", (1.36, 1.28, 0.05), (0, -0.35, 1.49), body_m, 0.02, root)
    wheels = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            w = empty(name + "_wheelP", (sx * 0.86, sy * 1.35, 0.36), root)
            cylinder(name + "_tire", 0.36, 0.28, (0, 0, 0), (0, math.radians(90), 0), M_TIRE, w)
            cylinder(name + "_rim", 0.22, 0.3, (0, 0, 0), (0, math.radians(90), 0), M_RIM, w, 6)
            wheels.append(w)
    for sx in (-1, 1):
        box(name + "_hl", (0.38, 0.06, 0.12), (sx * 0.62, 2.14, 0.72), M_HEAD, parent=root)
        box(name + "_tl", (0.38, 0.06, 0.12), (sx * 0.62, -2.14, 0.74), M_TAIL, parent=root)
    box(name + "_grill", (0.7, 0.04, 0.14), (0, 2.15, 0.55), M_TIRE, parent=root)
    return dict(root=root, wheels=wheels)


hero = car("HeroCar", (0.75, 0.04, 0.03))
hero["root"].location = (2.0, -60, 0)
driver = person("Driver", M_SHIRT2, M_JEANS, M_SKIN, M_HAIR)
driver["root"].parent = hero["root"]
driver["root"].location = (-0.4, -0.3, -0.44)
for ap in driver["arms"]:
    ap.rotation_euler = (math.radians(70), 0, 0)
for lp in driver["legs"]:
    lp.rotation_euler = (math.radians(80), 0, 0)

traffic = [car("Car_B", (0.1, 0.3, 0.75)), car("Car_C", (0.9, 0.85, 0.85)), car("Car_D", (0.95, 0.6, 0.05))]
for t in traffic:
    t["root"].location = (0, -300, 0)

# ------------------------------------------------------------------ kameralar
cam_main = camera("Cam_Main", (-6, -6, 0.6), (-3.4, -2, 0.2), 32)
cam_side = camera("Cam_Street", (-9.4, -4.6, 1.0), (-5.6, 2.2, 0.95), 24)
cam_drv = camera("Cam_DriverPOV", (0, 0, 0), (0, 1, 0), 55)
cam_drv.parent = hero["root"]
DRV_OFF = Vector((EYE.x - 2.0, 0.8, EYE.z))      # ko'z = mashina + DRV_OFF
cam_drv.location = DRV_OFF
cam_drv.rotation_euler = (EYE_TARGET - EYE).to_track_quat('-Z', 'Y').to_euler()
cam_face = camera("Cam_Face", (0, 0, 0), (0, 1, 0), 42)
cam_face.parent = hero["root"]
cam_face.location = (-0.12, 0.45, 1.3)
cam_face.rotation_euler = (Vector((-0.4, -0.3, 1.25)) - cam_face.location).to_track_quat('-Z', 'Y').to_euler()
cam_end = camera("Cam_End", (-5.8, 5.2, 0.85), (3.5, -2.5, 0.8), 20)

face_light_d = bpy.data.lights.new("FaceLight", 'AREA')
face_light_d.energy = 40
face_light_d.size = 0.4
face_light = link(bpy.data.objects.new("FaceLight", face_light_d))
face_light.parent = hero["root"]
face_light.location = (0.1, 0.5, 1.38)

# ------------------------------------------------------------------ TIMELINE
# A   1-150  : ishchi chiziq bo'yaydi (yaqin plan)
# B 151-255  : kamera tepaga ko'tariladi, bo'yash tezlashadi (time-lapse)
# C 256-505  : tepadan ko'rinish -> haydovchi ko'zi nuqtasiga sho'ng'ish -> 3D bloklar
# D 506-700  : oddiy zebra: hech kim to'xtamaydi
# E 701-805  : haydovchi nigohi, keyin yuzi yaqin plan (ko'zlari kattalashadi)
# F 806-885  : mashina keskin to'xtaydi, piyoda xotirjam o'tadi

for name, f, cam in [("A", 1, cam_main), ("D", 506, cam_side), ("E", 701, cam_drv),
                     ("E2", 776, cam_face), ("F", 806, cam_end)]:
    scene.timeline_markers.new(name, frame=f).camera = cam
scene.camera = cam_main

# ---- paint progress T (ishchi pozitsiyasi ham shu bilan hisoblanadi)


def paint_T(f):
    if f <= 150:
        return lerp(0.0, 0.45, (f - 1) / 149)
    if f <= 240:
        t = (f - 150) / 90
        return lerp(0.45, 8.0, t ** 1.6)
    return 99.0


def stripe_front(T):
    i = min(int(T), 7)
    p = max(0.0, min(1.0, T - i))
    y = REV_Y0 + p * REV_LEN
    xb = BLOCK_X[i]
    x = EYE.x + (xb - EYE.x) * (y - EYE.y) / dist0
    return i, x, y


pt_out = PAINT_T.outputs[0]
prev_y = None
for f in range(1, 261):
    T = paint_T(f)
    pt_out.default_value = T
    pt_out.keyframe_insert("default_value", frame=f)
    if f <= 245:
        i, x, y = stripe_front(min(T, 7.999))
        wr = worker["root"]
        kf(wr, "location", f, (x, y - 1.15, 0.0))
        kf(wr, "rotation_euler", f, (0, 0, 0))
        phase = f * 0.32 if f <= 150 else f * 1.1
        walk_pose(worker, f, phase, 0.3, 0.05, math.radians(48))
# ishchi ishini tugatib chetga chiqadi
kf(worker["root"], "location", 252, (-8.0, -3.4, 0.14))
kf(worker["root"], "rotation_euler", 252, (0, 0, math.radians(90)))
for f in (252, 885):
    walk_pose(worker, f, 0, 0, 0, 0)

# tushirilgan shot A kamerasi: ishchini kuzatadi (har kadrda)
TOP_POS = Vector((0.0, 5.5, 33.0))
TOP_TGT = Vector((0.0, 5.5, 0.0))
for f in range(1, 506):
    if f <= 150:
        _, x, y = stripe_front(paint_T(f))
        pos = Vector((x - 2.8, y - 3.4, 0.75 + 0.15 * (f / 150)))
        tgt = Vector((x - 0.2, y - 0.6, 0.35))
    elif f <= 255:
        t = ease((f - 150) / 105)
        _, x, y = stripe_front(paint_T(150))
        p0 = Vector((x - 2.8, y - 3.4, 0.9))
        t0 = Vector((x - 0.2, y - 0.6, 0.35))
        pos = vlerp(p0, TOP_POS, t)
        pos.z = lerp(p0.z, TOP_POS.z, t ** 0.8)
        tgt = vlerp(t0, TOP_TGT, t)
    elif f <= 300:
        pos, tgt = TOP_POS.copy(), TOP_TGT.copy()
        pos.z -= (f - 255) * 0.03
    elif f <= 390:
        t = ease((f - 300) / 90)
        p0 = TOP_POS - Vector((0, 0, 45 * 0.03))
        pos = vlerp(p0, EYE, t)
        # yoy shaklida: avval orqaga, keyin pastga
        pos.z = lerp(p0.z, EYE.z, t ** 0.6)
        tgt = vlerp(TOP_TGT, EYE_TARGET, ease(min(1, t * 1.15)))
    else:
        t = (f - 390) / 115
        pos = EYE + Vector((0.0, 0.25 * t, 0.0))
        tgt = EYE_TARGET.copy()
    cam_main.location = pos
    cam_main.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cam_main.keyframe_insert("location", frame=f)
    cam_main.keyframe_insert("rotation_euler", frame=f)
    lens = 32 if f <= 300 else lerp(32, 78, ease((f - 300) / 90))
    cam_main.data.lens = lens
    cam_main.data.keyframe_insert("lens", frame=f)

# ---- decal / zebra ko'rinishi
for o in [decal]:
    kf(o, "hide_render", 1, False)
    kf(o, "hide_render", 506, True)
    kf(o, "hide_render", 701, False)
for o in normal_zebra:
    kf(o, "hide_render", 1, True)
    kf(o, "hide_render", 506, False)
    kf(o, "hide_render", 701, True)
for o in list(worker["root"].children_recursive) + [worker["root"], bucket] + list(bucket.children):
    kf(o, "hide_render", 1, False)
    kf(o, "hide_render", 506, True)

# ---- D: oddiy zebra, mashinalar to'xtamaydi
pr = ped["root"]
kf(pr, "location", 1, (-7.35, 0.2, 0.15))
kf(pr, "rotation_euler", 1, (0, 0, math.radians(-90)))
walk_pose(ped, 1, 0, 0, 0, 0)
# 560: bir qadam oldinga -> mashina -> orqaga sakraydi
kf(pr, "location", 548, (-7.35, 0.2, 0.15))
walk_pose(ped, 548, 0, 0, 0, 0)
kf(pr, "location", 562, (-6.75, 0.2, 0.0))
walk_pose(ped, 556, math.pi / 2, 0.35, 0.25)
walk_pose(ped, 562, 0, 0, 0, 0)
kf(pr, "location", 572, (-6.75, 0.2, 0.0))
kf(pr, "location", 580, (-7.4, 0.2, 0.15))
kf(ped["hips"], "rotation_euler", 572, 0, 0)
kf(ped["hips"], "rotation_euler", 578, math.radians(-12), 0)
kf(ped["hips"], "rotation_euler", 600, 0, 0)
for ap in ped["arms"]:
    kf(ap, "rotation_euler", 572, 0, 1)
for s, ap in zip((-1, 1), ped["arms"]):
    kf(ap, "rotation_euler", 578, s * math.radians(-35), 1)
    kf(ap, "rotation_euler", 598, s * math.radians(-35), 1)
    kf(ap, "rotation_euler", 610, 0, 1)
# 655: qo'llarini yoyadi (g'azab)
for s, ap in zip((-1, 1), ped["arms"]):
    kf(ap, "rotation_euler", 648, 0, 1)
    kf(ap, "rotation_euler", 660, s * math.radians(-70), 1)
    kf(ap, "rotation_euler", 700, s * math.radians(-70), 1)
    kf(ap, "rotation_euler", 701, 0, 1)
kf(ped["neck"], "rotation_euler", 640, 0, 2)
kf(ped["neck"], "rotation_euler", 650, math.radians(25), 2)
kf(ped["neck"], "rotation_euler", 662, math.radians(-25), 2)
kf(ped["neck"], "rotation_euler", 674, math.radians(20), 2)
kf(ped["neck"], "rotation_euler", 686, 0, 2)


def drive(c, f0, f1, y0, y1, x, heading=0.0):
    prefs = bpy.context.preferences.edit
    prefs.keyframe_new_interpolation_type = 'LINEAR'
    r = c["root"]
    kf(r, "location", f0 - 1, (x, -300, 0))
    for f in (f0, f1):
        t = (f - f0) / (f1 - f0)
        kf(r, "location", f, (x, lerp(y0, y1, t), 0))
        kf(r, "rotation_euler", f, (0, 0, heading))
    kf(r, "location", f1 + 1, (x, -300, 0))
    dist = abs(y1 - y0)
    for w in c["wheels"]:
        kf(w, "rotation_euler", f0, 0, 0)
        kf(w, "rotation_euler", f1, dist / 0.36 * (1 if y1 > y0 else -1), 0)
    prefs.keyframe_new_interpolation_type = 'BEZIER'


# chap qatorda (x=-3.5) kamera tomonga keluvchi mashinalar: yuqoridan pastga
drive(traffic[0], 530, 620, 30, -32, -5.25, math.pi)
drive(traffic[1], 600, 690, 40, -25, -1.75, math.pi)
drive(traffic[2], 620, 700, -40, 40, 1.75, 0)

# ---- E/F: qahramon mashina yaqinlashadi va to'xtaydi
STOP_Y = -6.6
V0 = 10.6 / FPS            # m/kadr
F_BRAKE, F_STOP = 790, 835


def hero_y(f):
    # tormozdan oldin doimiy tezlik, keyin chiziqli sekinlashish
    if f >= F_STOP:
        return STOP_Y
    if f >= F_BRAKE:
        rem = F_STOP - f
        return STOP_Y - 0.5 * V0 / (F_STOP - F_BRAKE) * rem * rem
    return STOP_Y - 0.5 * V0 * (F_STOP - F_BRAKE) - V0 * (F_BRAKE - f)


hr = hero["root"]
for f in range(1, 886):
    if f < 700:
        if f in (1, 699):
            kf(hr, "location", f, (2.0, -300, 0))
        continue
    y = hero_y(f)
    kf(hr, "location", f, (2.0, y, 0))
    for w in hero["wheels"]:
        kf(w, "rotation_euler", f, (y - STOP_Y) / 0.36, 0)
# tormozda burni pastga egiladi
for f, d in [(788, 0), (798, -2.8), (835, -2.2), (845, 1.3), (856, -0.4), (866, 0)]:
    kf(hr, "rotation_euler", f, math.radians(d), 0)

# haydovchi yuzi: 782 da ko'zlar kattalashadi
for e in driver["eyes"]:
    kf(e, "scale", 776, (1, 1, 1))
    kf(e, "scale", 781, (1, 1, 1))
    kf(e, "scale", 785, (1.7, 1.3, 1.9))
    kf(e, "scale", 805, (1.6, 1.3, 1.8))
for b in driver["brows"]:
    kf(b, "location", 781, b.location.z, 2)
    kf(b, "location", 785, b.location.z + 0.04, 2)
m = driver["mouth"]
kf(m, "scale", 781, (1, 1, 1))
kf(m, "scale", 786, (0.6, 1, 4.0))
kf(driver["neck"], "rotation_euler", 781, 0, 0)
kf(driver["neck"], "rotation_euler", 786, math.radians(-10), 0)
for ap in driver["arms"]:
    kf(ap, "rotation_euler", 781, math.radians(70), 0)
    kf(ap, "rotation_euler", 787, math.radians(85), 0)

# F: piyoda o'ng tomondan xotirjam o'tadi va qo'l silkitadi
kf(pr, "location", 700, (-7.4, 0.2, 0.15))
kf(pr, "rotation_euler", 700, (0, 0, math.radians(-90)))
kf(pr, "location", 701, (7.4, 0.3, 0.15))
kf(pr, "rotation_euler", 701, (0, 0, math.radians(90)))
kf(pr, "location", 838, (7.4, 0.3, 0.15))
walk_pose(ped, 701, 0, 0, 0, 0)
walk_pose(ped, 838, 0, 0, 0, 0)
for f in range(840, 886, 2):
    t = (f - 840) / 45.0
    kf(pr, "location", f, (lerp(6.8, 3.5, t), 0.3, 0.0))
    walk_pose(ped, f, (f - 840) * 0.38, 0.4, 0.3, arms=f < 854)
# o'ng qo'li bilan silkitish (haydovchiga)
wave_arm = ped["arms"][1]
for f in range(856, 886, 5):
    kf(wave_arm, "rotation_euler", f, math.radians(-160), 1)
    kf(wave_arm, "rotation_euler", f, math.radians(-15 if (f // 5) % 2 else 15), 0)
kf(ped["neck"], "rotation_euler", 850, 0, 2)
kf(ped["neck"], "rotation_euler", 858, math.radians(50), 2)

# F kamerasi sekin yaqinlashadi
kf(cam_end, "location", 806, (-5.8, 5.2, 0.85))
kf(cam_end, "location", 885, (-5.3, 4.4, 0.8))

# ------------------------------------------------------------------ render sozlamalari
scene.render.resolution_x, scene.render.resolution_y = 720, 1280
scene.render.resolution_percentage = 75
scene.cycles.samples = 14
scene.cycles.adaptive_threshold = 0.05
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 2
scene.cycles.transmission_bounces = 2
scene.render.use_persistent_data = True
scene.render.use_motion_blur = False
scene.render.motion_blur_shutter = 0.25
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = os.path.join(HERE, "frames", "f_")
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - High Contrast'
except Exception:
    pass

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "scene.blend"))
print("SCENE SAVED")
