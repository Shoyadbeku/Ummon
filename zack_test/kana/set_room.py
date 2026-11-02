# 11-kadr (683-739): "...siz hech narsa sezmaysiz." Qiz (Megan) divanda kulib o'tiribdi,
# kamera keng plandan uning bilagidagi kichkina kanaga suriladi. Xona: scene3.py interyeri + Poly Haven.
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mathutils import Vector
import common as C
import tick as T
import mixchar as mc

R = math.radians
s = C.reset()
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
S11 = (683, 739)

# ================= xona =================
floor = C.box("floor", (6, 5, 0.06), (0, 2.5, -0.03), C.pbr("ph_floor", "laminate_floor_02", 0.5))
wall = C.pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.95, 0.88, 0.78))
trim = C.mat("trim", (0.92, 0.92, 0.9), 0.4)
C.box("ceiling", (6, 5, 0.06), (0, 2.5, 2.73), trim)
C.box("wall_back_l", (2.2, 0.12, 2.7), (-1.9, 5.0, 1.35), wall)
C.box("wall_back_r", (2.2, 0.12, 2.7), (1.9, 5.0, 1.35), wall)
C.box("wall_back_b", (1.6, 0.12, 0.85), (0, 5.0, 0.425), wall)
C.box("wall_back_t", (1.6, 0.12, 0.45), (0, 5.0, 2.475), wall)
C.box("window_glow", (1.8, 0.02, 1.6), (0, 5.4, 1.6), C.mat("winlight", (1.0, 0.95, 0.85), 0.5, emit=6.0))
for x in (-0.78, 0.78): C.box("wframe", (0.06, 0.16, 1.4), (x, 5.0, 1.55), trim)
C.box("wframe_m", (1.6, 0.16, 0.06), (0, 5.0, 1.55), trim)
C.box("wall_left", (0.12, 5, 2.7), (-3.0, 2.5, 1.35), wall)
C.box("wall_right", (0.12, 5, 2.7), (3.0, 2.5, 1.35), wall)
C.box("wall_front", (6, 0.12, 2.7), (0, 0.0, 1.35), wall)
rug = C.mat("rug", (0.55, 0.18, 0.12), 0.95); C.noise_color(rug, (0.75, 0.6, 0.4), scale=12, kind="voronoi")
C.box("rug", (2.8, 1.9, 0.01), (-0.1, 2.9, 0.005), rug)
brass = C.mat("brass", (0.85, 0.65, 0.3), 0.25, metal=1.0)
C.cyl("lamp_base", 0.12, 0.03, (2.0, 4.4, 0.015), brass)
C.cyl("lamp_pole", 0.015, 1.5, (2.0, 4.4, 0.75), brass)
C.cyl("lamp_shade", 0.22, 0.32, (2.0, 4.4, 1.55), C.mat("lampshade", (1.0, 0.85, 0.6), 0.6, emit=3.0))

def import_gltf(path, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = C.empty(os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler.z = R(rot_z); root.scale = (scale,) * 3
    return root, new
import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.2, 4.35, 0), 0)
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.2, 3.2, 0), 0)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.3, 4.5, 0), 0, 1.2)
import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-1.9, 4.92, 1.5), 0)

# ================= qiz: divanda kulib o'tiradi =================
groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
for o in gmesh:
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                nd.inputs["Coat Weight"].default_value = 0.0
                for k in ("Specular IOR Level",):
                    for l in list(nd.inputs[k].links): m.node_tree.links.remove(l)
                    nd.inputs[k].default_value = 0.25
                if "hair" not in m.name.lower():
                    for l in list(nd.inputs["Roughness"].links): m.node_tree.links.remove(l)
                    nd.inputs["Roughness"].default_value = 0.6
SEAT = tuple(map(float, os.environ.get("SEAT", "-0.15,4.2,-0.03").split(",")))
groot.location = SEAT; groot.rotation_euler.z = R(0)
mc.add_strip(girl, mc.load_action("Sitting_Laughing.fbx", True), S11[0] - 40, speed=1.0)

# ================= bilakdagi kana (suyakka biriktirilgan) =================
tk = T.build("armtick", tilt=30, loc=(0, 0, 0))
T.engorge(tk, 1, 0.12)
holder = C.empty("tick_holder", (0, 0, 0))
holder.parent = girl; holder.parent_type = "BONE"
BONE = os.environ.get("TBONE", "mixamorig:LeftForeArm")
holder.parent_bone = BONE
TOFF = tuple(map(float, os.environ.get("TOFF", "0.0,-12.0,-3.3").split(",")))
TROT = tuple(map(float, os.environ.get("TROT", "0,180,90").split(",")))
holder.location = TOFF; holder.rotation_euler = [R(a) for a in TROT]
tk["root"].parent = holder; tk["root"].location = (0, 0, 0)
TS = 0.009
tk["root"].scale = (TS / 0.01, TS / 0.01, TS / 0.01)   # qahramon armaturasi 0.01 masshtabda

# ================= yorug'lik =================
C.world_color((0.6, 0.7, 0.85), 0.4)
C.light("ceiling_light", "AREA", (0, 2.6, 2.65), (0, 0, 0), 120, 1.2, (1, 0.9, 0.78))
C.light("window_key", "AREA", (0.0, 4.7, 1.7), (-80, 0, 0), 220, 1.6, (0.95, 0.97, 1.0))
C.light("face_fill", "AREA", (0.8, 2.2, 1.6), (70, 0, 160), 70, 1.0, (1.0, 0.85, 0.7))

# ================= kamera: keng plan -> bilakka push-in =================
tgt = C.empty("c11_t", (0, 0, 0))
cam = C.camera("c11_room", (1.6, 1.0, 1.0), tgt, 22, 2.8, clip=0.005)
C.key(cam, S11[0], loc=(1.5, 1.2, 0.95))
C.key(cam, S11[0] + 22, loc=(0.9, 2.4, 0.9))
C.key(cam, S11[1], loc=(0.35, 3.5, 0.82))
C.shake(cam, S11[0], S11[1], amp=0.01, freq=0.3, seed=5)
# nishon: avval qizning ko'kragi, keyin kana
bpy.context.view_layer.update()
ct = C.empty("chest_t", (0, 0, 0)); cc = ct.constraints.new("COPY_LOCATION"); cc.target = girl; cc.subtarget = "mixamorig:Spine2"
kt = C.empty("tick_t", (0, 0, 0)); kc = kt.constraints.new("COPY_LOCATION"); kc.target = tk["body"]
for c, (a, b) in ((tgt.constraints.new("COPY_LOCATION"), (1.0, 0.0)), (tgt.constraints.new("COPY_LOCATION"), (0.0, 1.0))):
    pass
tgt.constraints.clear()
c1 = tgt.constraints.new("COPY_LOCATION"); c1.target = ct
c2 = tgt.constraints.new("COPY_LOCATION"); c2.target = kt
for f, inf in ((S11[0], 0.0), (S11[0] + 18, 0.0), (S11[0] + 34, 1.0)):
    c2.influence = inf; c2.keyframe_insert("influence", frame=f)
cam.data.dof.focus_object = tgt
fl = cam.data
for f, l in ((S11[0], 22), (S11[0] + 20, 24), (S11[1], 75)):
    fl.lens = l; fl.keyframe_insert("lens", frame=f)
C.cut(S11[0], cam); s.camera = cam

C.setup_render(samples=14, exposure=-0.3)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    C.render_ranges([S11])
