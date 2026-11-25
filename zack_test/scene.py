# Zack D. Films uslubidagi 10 soniyalik test: qiz onasi bilan urushib, uydan chiqib, mashinada ketadi.
# Ishlatish: Blender > Scripting > Run  (yoki: python scene.py, bpy moduli bilan)
import bpy, math, sys, os
from mathutils import Vector

OUT = os.environ.get("OUT", "/tmp/zack_frames/")
FPS, END = 24, 240
R = math.radians

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, END
sc.render.fps = FPS

# ---------- yordamchi funksiyalar ----------
def mat(name, color, rough=0.5, sss=0.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.03
    return m

def finish(o, m, bevel=0.0, smooth=True):
    o.data.materials.append(m)
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    if bevel:
        mod = o.modifiers.new("bev", "BEVEL"); mod.width = bevel; mod.segments = 4
    return o

def box(name, size, loc, m, bevel=0.03, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object
    o.name = name; o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    finish(o, m, bevel, smooth=False); o.parent = parent; return o

def ell(name, r, loc, m, parent=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg//2, location=loc)
    o = bpy.context.object; o.name = name; o.scale = r
    bpy.ops.object.transform_apply(scale=True)
    finish(o, m); o.parent = parent; return o

def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o)
    o.parent = parent; o.location = loc; return o

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

# ---------- materiallar ----------
skin   = mat("skin", (0.85, 0.6, 0.48), 0.45, sss=0.4)
skin2  = mat("skin2", (0.78, 0.55, 0.43), 0.5, sss=0.4)
dark   = mat("eye", (0.02, 0.02, 0.02), 0.2)
hairG  = mat("hairG", (0.12, 0.06, 0.03), 0.4)
hairM  = mat("hairM", (0.25, 0.15, 0.08), 0.5)
shirtG = mat("shirtG", (0.85, 0.2, 0.3), 0.6)
shirtM = mat("shirtM", (0.25, 0.4, 0.6), 0.6)
jeans  = mat("jeans", (0.12, 0.18, 0.35), 0.7)
pantsM = mat("pantsM", (0.2, 0.2, 0.22), 0.7)
wall   = mat("wall", (0.92, 0.86, 0.76), 0.8)
floor  = mat("floor", (0.55, 0.36, 0.22), 0.5)
door   = mat("door", (0.4, 0.22, 0.12), 0.5)
asph   = mat("asphalt", (0.09, 0.09, 0.1), 0.9)
walk   = mat("sidewalk", (0.55, 0.55, 0.53), 0.85)
grass  = mat("grass", (0.25, 0.5, 0.15), 0.9)
carP   = mat("carpaint", (0.75, 0.75, 0.78), 0.2, metal=0.6)
glass  = mat("glass", (0.05, 0.08, 0.1), 0.05)
tire   = mat("tire", (0.03, 0.03, 0.03), 0.8)
white  = mat("white", (0.95, 0.95, 0.95), 0.4)
sofaM  = mat("sofa", (0.3, 0.45, 0.35), 0.8)

# ---------- odam (gil-shaklli stil) ----------
def person(name, skinm, shirt, pants, hairm, s=1.0, girl=True):
    root = empty(name, (0, 0, 0))
    root.scale = (s, s, s)
    ell(name+"_torso", (0.21, 0.13, 0.33), (0, 0, 1.15), shirt, root)
    p = {"root": root}
    for side, x in (("L", 0.1), ("R", -0.1)):
        hip = empty(f"{name}_hip{side}", (x, 0, 0.88), root)
        ell(f"{name}_leg{side}", (0.085, 0.085, 0.44), (0, 0, -0.42), pants, hip)
        ell(f"{name}_shoe{side}", (0.07, 0.12, 0.05), (0, -0.04, -0.84), dark, hip)
        sh = empty(f"{name}_sh{side}", (x*2.6, 0, 1.4), root)
        ell(f"{name}_arm{side}", (0.06, 0.06, 0.32), (0, 0, -0.3), shirt, sh)
        ell(f"{name}_hand{side}", (0.055, 0.055, 0.065), (0, 0, -0.62), skinm, sh)
        p["hip"+side], p["sh"+side] = hip, sh
    neck = empty(name+"_neck", (0, 0, 1.47), root)
    ell(name+"_neckm", (0.055, 0.055, 0.07), (0, 0, 0.03), skinm, neck)
    ell(name+"_head", (0.14, 0.15, 0.16), (0, 0, 0.2), skinm, neck)
    for x in (0.05, -0.05):
        ell(name+"_eye", (0.018, 0.012, 0.022), (x, -0.135, 0.22), dark, neck, 12)
        b = box(name+"_brow", (0.05, 0.01, 0.012), (x, -0.14, 0.265), hairm, 0, neck)
        b.rotation_euler.y = R(-20 if x > 0 else 20)   # jahl qilgan qoshlar
    box(name+"_mouth", (0.05, 0.01, 0.01), (0, -0.14, 0.13), dark, 0, neck)
    ell(name+"_hairtop", (0.15, 0.16, 0.12), (0, 0.02, 0.28), hairm, neck)
    if girl:
        ell(name+"_hairback", (0.14, 0.06, 0.28), (0, 0.11, 0.08), hairm, neck)
    else:
        ell(name+"_bun", (0.07, 0.07, 0.07), (0, 0.13, 0.33), hairm, neck)
    p["neck"] = neck
    return p

# ---------- uy ichi (kesim ko'rinishi) ----------
box("floor", (5, 5, 0.1), (-2.5, 0, -0.05), floor, 0)
box("wall_back", (5, 0.15, 2.8), (-2.5, 2.5, 1.4), wall, 0)
box("wall_left", (0.15, 5, 2.8), (-5, 0, 1.4), wall, 0)
box("wall_r1", (0.15, 2.0, 2.8), (0, -1.5, 1.4), wall, 0)   # o'ng devor + eshik teshigi
box("wall_r2", (0.15, 2.0, 2.8), (0, 1.5, 1.4), wall, 0)
box("wall_r3", (0.15, 1.0, 0.7), (0, 0, 2.45), wall, 0)
front = box("wall_front", (5.15, 0.15, 2.8), (-2.5, -2.5, 1.4), wall, 0)
for f, v in ((1, True), (85, False)):          # 1-kadrda old devor yashirin (kesim)
    front.hide_render = v; front.keyframe_insert("hide_render", frame=f)
roof = box("roof", (5.6, 5.6, 0.2), (-2.5, 0, 2.9), mat("roofm", (0.5, 0.2, 0.15), 0.7), 0.02)
for f, v in ((1, True), (85, False)):
    roof.hide_render = v; roof.keyframe_insert("hide_render", frame=f)
hinge = empty("door_hinge", (0.05, -0.5, 0))
box("door", (0.06, 1.0, 2.1), (0, 0.5, 1.05), door, 0.01, hinge)
key(hinge, 92, rot=(0, 0, 0)); key(hinge, 100, rot=(0, 0, -95)); key(hinge, 135, rot=(0, 0, -95)); key(hinge, 145, rot=(0, 0, 0))
box("sofa", (0.9, 2.2, 0.5), (-4.4, 0.8, 0.25), sofaM, 0.08)
box("sofaback", (0.25, 2.2, 0.6), (-4.8, 0.8, 0.75), sofaM, 0.08)
box("table", (0.7, 0.7, 0.05), (-2.5, 1.6, 0.75), door, 0.01)
box("tleg", (0.08, 0.08, 0.72), (-2.5, 1.6, 0.36), door, 0)
bpy.ops.mesh.primitive_plane_add(size=0.9, location=(-2.5, 2.42, 1.7), rotation=(R(90), 0, 0))
finish(bpy.context.object, mat("pic", (0.3, 0.55, 0.8), 0.3), smooth=False)

# ---------- ko'cha ----------
box("grass", (80, 80, 0.1), (0, 0, -0.07), grass, 0)
box("sidewalk", (3.5, 80, 0.12), (1.85, 0, -0.04), walk, 0)
box("road", (6, 80, 0.1), (6.6, 0, -0.06), asph, 0)
for y in range(-40, 41, 4):
    box("line", (0.15, 2, 0.02), (6.6, y, 0.0), white, 0)
for i, y in enumerate((-9, 9, 18)):
    ell(f"tree{i}", (1.1, 1.1, 1.4), (2.6, y, 3.0), grass)
    box(f"trunk{i}", (0.25, 0.25, 2.0), (2.6, y, 1.0), door, 0.02)

# ---------- mashina ----------
car = empty("car", (4.7, 1.0, 0))
box("body", (1.8, 4.2, 0.7), (0, 0, 0.6), carP, 0.18, car)
box("cabin", (1.6, 2.3, 0.6), (0, 0.2, 1.15), glass, 0.15, car)
for x in (-0.82, 0.82):
    for y in (-1.3, 1.3):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.33, depth=0.3, location=(x, y, 0.33), rotation=(0, R(90), 0))
        w = bpy.context.object; finish(w, tire, 0.05); w.parent = car
for x in (-0.6, 0.6):
    ell("light", (0.18, 0.05, 0.08), (x, 2.1, 0.7), mat("hl", (1, 1, 0.8), 0.1), car, 12)
    ell("tail", (0.18, 0.05, 0.08), (x, -2.1, 0.7), mat("tl", (0.9, 0.05, 0.05), 0.2), car, 12)
key(car, 165, loc=(4.7, 1.0, 0)); key(car, 240, loc=(4.7, 45, 0))
for fc in car.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if hasattr(car.animation_data.action, "layers") else car.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = "QUAD"; kp.easing = "EASE_IN"

# ---------- qahramonlar ----------
mom  = person("mom", skin2, shirtM, pantsM, hairM, 1.05, girl=False)
girl = person("girl", skin, shirtG, jeans, hairG, 0.95, girl=True)
mom["root"].location = (-3.3, 0.2, 0); mom["root"].rotation_euler.z = R(90)
G = girl["root"]

# 1-SAHNA (1-84): janjal
key(G, 1, loc=(-1.7, 0.2, 0), rot=(0, 0, -90))
for f in range(1, 85, 6):           # onasi qo'lini silkitib, barmog'ini ko'rsatadi
    a = -80 if (f // 6) % 2 == 0 else -55
    key(mom["shR"], f, rot=(a, 0, 0)); key(mom["shL"], f, rot=(-10, 0, 15 if (f//6)%2 else 5))
    key(mom["neck"], f, rot=(5 if (f//6) % 2 else -5, 0, 0))
for f in range(1, 70, 8):           # qiz bosh chayqaydi, qo'llarini yoyadi
    key(girl["neck"], f, rot=(0, 0, 18 if (f//8) % 2 else -18))
key(girl["shL"], 1, rot=(0, 0, 10)); key(girl["shR"], 1, rot=(0, 0, -10))
key(girl["shL"], 40, rot=(-40, 0, 35)); key(girl["shR"], 40, rot=(-40, 0, -35))
key(girl["shL"], 60, rot=(0, 0, 10)); key(girl["shR"], 60, rot=(0, 0, -10))
key(girl["neck"], 70, rot=(0, 0, 0))
for f in (1, 84):
    key(girl["hipL"], f, rot=(0, 0, 0)); key(girl["hipR"], f, rot=(0, 0, 0))
key(G, 70, rot=(0, 0, -90)); key(G, 84, rot=(0, 0, 90))   # orqasiga o'giriladi

# 2-SAHNA (85-160): eshikdan chiqib mashinaga yuradi
path = [(85, (-1.7, 0.2)), (100, (-0.6, 0.0)), (118, (1.4, 0.0)), (150, (3.75, 0.6))]
for f, (x, y) in path:
    key(G, f, loc=(x, y, 0))
key(G, 118, rot=(0, 0, 90)); key(G, 126, rot=(0, 0, 70)); key(G, 150, rot=(0, 0, 70))
for f in range(85, 152, 6):         # yurish sikli
    s = 28 if (f // 6) % 2 else -28
    key(girl["hipL"], f, rot=(s, 0, 0)); key(girl["hipR"], f, rot=(-s, 0, 0))
    key(girl["shL"], f, rot=(-s*0.8, 0, 5)); key(girl["shR"], f, rot=(s*0.8, 0, -5))
key(girl["hipL"], 152, rot=(0, 0, 0)); key(girl["hipR"], 152, rot=(0, 0, 0))
# mashinaga o'tiradi va yo'qoladi
key(G, 152, loc=(3.75, 0.6, 0)); key(G, 160, loc=(4.5, 0.6, 0.25))
G.hide_render = False; G.keyframe_insert("hide_render", frame=160)
G.hide_render = True;  G.keyframe_insert("hide_render", frame=161)
for c in G.children_recursive:
    c.hide_render = False; c.keyframe_insert("hide_render", frame=160)
    c.hide_render = True;  c.keyframe_insert("hide_render", frame=161)

# ---------- kameralar (3 ta kadr) ----------
def camera(name, loc, target, lens=32, dof=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c); c.location = loc
    t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if dof:
        cd.dof.use_dof = True; cd.dof.focus_object = target; cd.dof.aperture_fstop = dof
    return c
t1 = empty("t1", (-2.5, 0.2, 1.35))
c1 = camera("cam1", (-2.5, -6.0, 1.5), t1, 42, 2.8)
key(c1, 1, loc=(-2.5, -6.0, 1.5)); key(c1, 84, loc=(-2.4, -4.6, 1.45))   # sekin yaqinlashish
t2 = empty("t2", (0, 0, 1.0), G); t2.parent = None
key(t2, 85, loc=(-1.0, 0.1, 1.2)); key(t2, 150, loc=(3.6, 0.5, 1.1)); key(t2, 160, loc=(4.2, 0.8, 1.0))
c2 = camera("cam2", (9.0, -8.5, 2.6), t2, 30, 4)
t3 = empty("t3", (4.7, 1, 0.8)); t3.parent = car
t3.location = (0, 0, 0.8)
c3 = camera("cam3", (3.0, -6.0, 1.3), t3, 40, 5)
key(c3, 161, loc=(3.0, -6.0, 1.3)); key(c3, 240, loc=(3.2, -4.5, 1.5))
for f, c in ((1, c1), (85, c2), (161, c3)):
    sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = c1

# ---------- yorug'lik va dunyo ----------
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3.5; sun.data.angle = R(8); sun.rotation_euler = (R(50), R(10), R(35))
sun.data.color = (1, 0.93, 0.82)
ia = bpy.data.objects.new("ia", bpy.data.lights.new("ia", "AREA")); sc.collection.objects.link(ia)
ia.data.energy = 250; ia.data.size = 3; ia.location = (-2.5, -1.0, 2.6); ia.data.color = (1, 0.85, 0.7)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.72, 0.95, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# ---------- render ----------
r = sc.render
r.engine = "CYCLES"
sc.cycles.device = "CPU"; sc.cycles.samples = int(os.environ.get("SAMPLES", 24))
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4
r.resolution_x, r.resolution_y = 1080, 1920
r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
r.image_settings.file_format = "PNG"; r.filepath = OUT

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
