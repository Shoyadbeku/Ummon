# 1-kadr (HOOK, 1-62): o't bargi uchida kana oldingi oyoqlarini cho'zib "ov qilyapti",
# orqada qiz (Mixamo Megan, Happy_Walk) kamera tomon yurib keladi. Fokus qizdan kanaga o'tadi.
import bpy, math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mathutils import Vector, Matrix
import common as C
import tick as T
import mixchar as mc

R = math.radians
random.seed(3)
s = C.reset()
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
S1 = (1, 62)

# ================= yer va o't =================
ground = C.plane("ground", (30, 30), (0, 0, 0), C.pbr("forest", "forrest_ground_01", 0.6))
grass_m = C.mat("grass", (0.09, 0.22, 0.04), 0.45, sss=0.3, sss_r=(0.4, 1.0, 0.2), sss_scale=0.01)
C.noise_color(grass_m, (0.2, 0.3, 0.06), scale=4, detail=3)
dry_m = C.mat("grass_dry", (0.35, 0.3, 0.12), 0.55, sss=0.2, sss_r=(1, 0.8, 0.3), sss_scale=0.01)

def blade_mesh(name, h, w, bend, segs=8):
    verts, faces = [], []
    for i in range(segs + 1):
        t = i / segs
        ww = w * (1 - t) ** 0.8 + 0.0002
        y = bend * h * t * t; z = h * t * (1 - 0.25 * bend * t)
        verts += [(-ww / 2, y, z), (ww / 2, y, z)]
        if i: faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for p in me.polygons: p.use_smooth = True
    return me

variants = [blade_mesh(f"bl{i}", random.uniform(0.1, 0.36), random.uniform(0.006, 0.014), random.uniform(0.1, 0.8)) for i in range(14)]
for i, me in enumerate(variants): me.materials.append(dry_m if i % 5 == 4 else grass_m)
col = bpy.data.collections.new("grass"); s.collection.children.link(col)
n = 0
for k in range(26000):
    # kamera yaqinida zich, uzoqda siyrak
    y = random.uniform(-0.3, 7.0)
    x = random.uniform(-0.8 - 0.4 * y, 0.8 + 0.4 * y)
    if random.random() > 1.0 / (1 + 0.6 * y): continue
    if -0.08 < x < 0.12 and -0.25 < y < 0.3: continue      # kamera va kana atrofi bo'sh
    o = bpy.data.objects.new("blade", random.choice(variants)); col.objects.link(o)
    o.location = (x, y, 0); o.rotation_euler = (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.uniform(0, 2 * math.pi))
    sc_ = random.uniform(0.7, 1.4); o.scale = (sc_, sc_, sc_); n += 1
print("blades", n)
# tezlik uchun hamma o'tni bitta meshga birlashtiramiz
bpy.ops.object.select_all(action="DESELECT")
objs = list(col.objects)
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.join()

# asosiy barg: kamera oldida egilib, uchi gorizontal
hero_pts = [(0.0, 0.0, 0.0), (0.0, 0.01, 0.08), (0.0, 0.03, 0.15), (0.0, 0.07, 0.19), (0.0, 0.12, 0.205), (0.0, 0.16, 0.2)]
hb = C.tube("hero_blade", hero_pts, 0.0035, grass_m, radii=[1.4, 1.2, 1.0, 0.9, 0.8, 0.5])
hb.data.bevel_resolution = 2
# yassi barg: tube'ni X bo'ylab kengaytirish
hb.scale = (2.6, 1.0, 1.0)

# ================= kana (masshtab: 1 birlik = 6 mm) =================
SC = 0.012
TOP = Vector((0.0, 0.135, 0.2105))           # barg ustidagi nuqta (og'iz)
def quest_legs(side, i, base, tip, lift):
    if i == 0:                                # oldingi oyoqlar havoda (questing)
        d = Vector((0.55, side * 0.6, 0.0)).normalized()
        return base + d * 0.55 + Vector((0, 0, 0.55)), 0.15
    tip = Vector((base.x - 0.05 * i, base.y + side * 0.18, -0.05))
    return tip, 0.2
tk = T.build("qtick", tilt=-12, leg_tip_fn=quest_legs, loc=(0, 0, 0))
scaler = C.empty("tick_scaler", tuple(TOP))
scaler.scale = (SC, SC, SC); scaler.rotation_euler.z = R(-90)        # boshi -Y ga (kameraga) qaragan
tk["root"].parent = scaler
# oldingi oyoqlar to'lqinlanadi
for e in tk["legs"]:
    if e.name.endswith("0"):
        e.rotation_mode = "XYZ"
        for f in range(1, 64, 8):
            ph = (f // 8) % 2
            e.rotation_euler = (R(18 if ph else -12), R(-10 if ph else 12), R(10 if ph else -10)); e.keyframe_insert("rotation_euler", frame=f)
        C.interp(e, "BEZIER")

# ================= qiz =================
groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
for o in gmesh:
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                nd.inputs["Coat Weight"].default_value = 0.0
                if "hair" not in m.name.lower():
                    for l in list(nd.inputs["Roughness"].links): m.node_tree.links.remove(l)
                    nd.inputs["Roughness"].default_value = 0.6
act = mc.load_action("Happy_Walk.fbx", True)
# bir siklda bosib o'tilgan masofa (oyoq sirpanmasligi uchun)
raw = mc.load_action("Happy_Walk.fbx", False)
fr = raw.frame_range
def hips_at(f):
    girl.animation_data.action = raw
    if hasattr(girl.animation_data, "action_slot") and raw.slots: girl.animation_data.action_slot = raw.slots[0]
    s.frame_set(int(f)); bpy.context.view_layer.update()
    return girl.matrix_world @ girl.pose.bones["mixamorig:Hips"].head
SPEED = 1.0
# NLA vaqti: strip scale = 0.8/speed => sikl uzunligi (24fps) = (fr[1]-fr[0])*0.8/speed
s.frame_set(1)
d_cycle = (hips_at(fr[1]) - hips_at(fr[0])).length
girl.animation_data.action = None
cyc = (fr[1] - fr[0]) * 0.8 / SPEED
v = d_cycle / cyc                                # m / kadr
print("walk cycle", d_cycle, cyc, v)
mc.add_strip(girl, act, -10, repeat=6.0, speed=SPEED)
X0 = -0.42
start = Vector((X0, 0.3 + v * 63, 0)); end = Vector((X0, 0.3 - v * 17, 0))
groot.location = start; groot.keyframe_insert("location", frame=-5)
groot.location = end; groot.keyframe_insert("location", frame=75)
C.interp(groot, "LINEAR")

# ================= yorug'lik =================
C.world_hdri(PH + "meadow_2.hdr", 1.0, 200)
sun = C.light("sun", "SUN", (0, 0, 10), (50, 0, 150), 3.0, 1.5, (1.0, 0.9, 0.75))

# ================= kamera =================
tg = C.empty("cam_t", tuple(TOP + Vector((0, 0, 0.004))))
cam = C.camera("c1_hook", (0.03, -0.09, 0.2), tg, 28, 2.0, clip=0.002)
cam.data.dof.focus_object = None
C.key(cam, 1, loc=(0.04, 0.02, 0.205)); C.key(cam, 30, loc=(0.035, 0.085, 0.226)); C.key(cam, 62, loc=(0.022, 0.112, 0.228))
C.shake(cam, 1, 62, amp=0.0006, freq=0.25, seed=1)
fd = cam.data.dof
# rack focus: avval qiz (uzoq), keyin kana
for f, dist in ((1, 2.6), (12, 1.9), (22, 0.06), (30, 0.058), (62, 0.034)):
    fd.focus_distance = dist; fd.keyframe_insert("focus_distance", frame=f)
C.key(tg, 1, loc=(0.1, 1.4, 0.35)); C.key(tg, 22, loc=tuple(TOP + Vector((0, 0.004, 0.004)))); C.key(tg, 62, loc=tuple(TOP + Vector((0, 0.005, 0.003))))
C.cut(1, cam); s.camera = cam

C.setup_render(samples=12, exposure=-0.35)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    C.render_ranges([S1])
