# Zack D. Films uslubi: "Kesilgan joyga peroksid" — nega yaraga vodorod peroksid quymaslik kerak (36.7 s, 9:16).
# Asos: scene3.py / scene_tepish.py (yordamchilar, kameralar, render) + mixchar.py (Mixamo). Ovoz: foydalanuvchi bergan wav.
# Megan oshxonada barmog'ini kesadi, peroksid quyadi, ko'pik chiqadi; mikro olamda teri hujayralari, bakteriya,
# yangi hujayralar va qon tanachalari oksidlanib eriydi; yara sekin bitib, chandiq qoladi; shifokor "yo'q" deydi.
# Kadr rejasi: zack_test/peroksid_storyboard.md
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_peroksid/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
EV = lambda k, d: float(os.environ.get(k, d))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
END = 882
sc.frame_start, sc.frame_end, sc.render.fps = 1, END, 24
random.seed(11)

# kadrlar (storyboard bilan bir xil)
SH = dict(s1=1, s2=43, s3=90, s4=133, s5=173, s6=205, s7=303, s8=368, s9=435, s10=483, s11=561, s12=625,
          s13=722, s14=808)
CUT = 24            # pichoq barmoqqa tegadi
POUR = 56           # "quysangiz": oqim tushadi
FOAM0 = 70          # "vishillab": ko'pik boshlanadi
BURN0 = 263         # "yoqib": teri hujayralari oksidlanadi
HIT_B, HIT_C = 392, 401   # bakteriya / sog'lom hujayra yoriladi
NEW_D = 530         # yangi nozik hujayralar eriy boshlaydi
RBC_D = 594         # "parchalanib"
HEAL0, HEAL_FAST, HEAL_SLOW = 632, 690, 721
SCAR0 = 735
PUNCH = 783         # "keskin"
DISMISS = 846       # "bu usuldan voz kechgan"
def in_ranges(f, rs): return any(a <= f <= b for a, b in rs)
# ---------------- yordamchilar ----------------
def mat(name, col, rough=0.5, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def glow_mat(name, col, strength, alpha=1.0, rim=False, blend=0.35):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    if rim:
        lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = blend
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = alpha
        L.new(lw.outputs["Facing"], mul.inputs[0]); L.new(mul.outputs[0], mx.inputs["Fac"])
    else:
        mx.inputs["Fac"].default_value = alpha
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    m["em"] = em.name
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(name, size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s/2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o); return o

def sphere(name, r, loc, m, sub=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o); return o

def plane(name, size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = (scale,)*3 if isinstance(scale, (int, float)) else scale; o.keyframe_insert("scale", frame=f)

def vis(o, ranges, rec=True):
    objs = [o] + (list(o.children_recursive) if rec else [])
    marks = sorted({1} | {a for a, b in ranges} | {b+1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)

def all_fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "layers") and act.layers:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return list(act.fcurves)

def set_interp(idb, mode="BEZIER", path=None):
    for fc in all_fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode

def keyval(sock, f, v, attr="default_value"):
    setattr(sock, attr, v); sock.keyframe_insert(attr, frame=f)

def pbr(name, folder, scale=1.0, tint=None, proj="BOX"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = proj; t.projection_blend = 0.2
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

def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi

def import_model(path, name, loc=(0, 0, 0), rot_z=0.0, height=None, scale=None):
    """glTF ni yuklab, bitta ildizga bog'laydi: pastki markazi loc da, balandligi height (yoki scale)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    lo, hi = bbox(new)
    s = (height / (hi.z - lo.z)) if height else (scale or 1.0)
    inner = empty(name + "_c"); inner.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
    for o in new:
        if o.parent is None: o.parent = inner
    root = empty(name); inner.parent = root
    root.location = loc; root.rotation_euler.z = R(rot_z); root.scale = (s,) * 3
    bpy.context.view_layer.update()
    return root, [o for o in new if o.type == "MESH"], (hi - lo) * s


def follow(obj, arm, bone):
    """obj ni suyakka bog'laydi; obj dam olish (T-poza) dunyo koordinatasida joylashtirilgan bo'lishi kerak."""
    c = obj.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = bone
    bpy.context.view_layer.update()
    c.inverse_matrix = (arm.matrix_world @ arm.data.bones[bone].matrix_local).inverted()
    return c

def const_interp(idb):
    for fc in all_fcurves(idb):
        for k_ in fc.keyframe_points: k_.interpolation = "CONSTANT"

def wet_mat(name, col, rough=0.25, sss=0.0, coat=0.0, alpha=1.0, trans=0.0, ior=1.45):
    m = mat(name, col, rough)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.25)
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha
    return m

def attr_mix(m, attr, col_b, rough_b=None, emit_col=None, emit_k=0.0):
    """Ob'ekt xususiyati (attr, 0..1) bo'yicha rangni col_b ga o'tkazadi; o'rtada emit_col bilan chaqnaydi."""
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = attr
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    mx.inputs[6].default_value = b.inputs["Base Color"].default_value[:]; mx.inputs[7].default_value = (*col_b, 1)
    L.new(at.outputs["Fac"], mx.inputs["Factor"]); L.new(mx.outputs[2], b.inputs["Base Color"])
    if rough_b is not None:
        mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = b.inputs["Roughness"].default_value; mr.inputs[4].default_value = rough_b
        L.new(at.outputs["Fac"], mr.inputs[0]); L.new(mr.outputs[0], b.inputs["Roughness"])
    if emit_col:
        # chaqnash: 4*t*(1-t)
        m1 = N.new("ShaderNodeMath"); m1.operation = "SUBTRACT"; m1.inputs[0].default_value = 1.0; L.new(at.outputs["Fac"], m1.inputs[1])
        m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; L.new(at.outputs["Fac"], m2.inputs[0]); L.new(m1.outputs[0], m2.inputs[1])
        m3 = N.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.inputs[1].default_value = 4.0 * emit_k; L.new(m2.outputs[0], m3.inputs[0])
        b.inputs["Emission Color"].default_value = (*emit_col, 1); L.new(m3.outputs[0], b.inputs["Emission Strength"])
    return m

def keyprop(o, prop, f, v):
    o[prop] = v; o.keyframe_insert(f'["{prop}"]', frame=f)

def inst(name, me, loc, scale, m, rot=None):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.location = loc; o.scale = scale
    o.rotation_euler = rot if rot else (random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0, 6.3))
    if not o.data.materials: o.data.materials.append(m)
    o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = m
    return o


# ================= OSHXONA =================
FLOOR = pbr("floor", "laminate_floor_02", 0.5)
WALL = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.93, 0.9, 0.84))
TILE = pbr("tiles", "long_white_tiles", 1.6)
WOOD = pbr("cab", "kitchen_wood", 1.2)
MARBLE = pbr("marble", "marble_01", 0.9)
BOARD = pbr("board", "kitchen_wood", 3.0, tint=(1.0, 0.85, 0.65))
CT = EV("CT", 0.96)                         # orol stol usti balandligi
X0, X1, Y0, Y1, HZ = -3.0, 3.0, -3.5, 2.4, 2.8
kitchen = []
kitchen.append(box("floor", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.025), FLOOR))
kitchen.append(box("ceiling", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ + 0.025), WALL))
kitchen.append(box("wall_back", (X1 - X0, 0.1, HZ), (0, Y1 + 0.05, HZ / 2), TILE))
kitchen.append(box("wall_front", (X1 - X0, 0.1, HZ), (0, Y0 - 0.05, HZ / 2), WALL))
kitchen.append(box("wall_l", (0.1, Y1 - Y0, HZ), (X0 - 0.05, (Y0 + Y1) / 2, HZ / 2), WALL))
kitchen.append(box("wall_r", (0.1, Y1 - Y0, HZ), (X1 + 0.05, (Y0 + Y1) / 2, HZ / 2), WALL))
# orqa devor bo'ylab pastki va yuqori shkaflar, stol usti
kitchen.append(box("back_cab", (4.6, 0.6, 0.86), (0.3, Y1 - 0.3, 0.43), WOOD))
kitchen.append(box("back_top", (4.64, 0.64, 0.04), (0.3, Y1 - 0.32, 0.88), MARBLE))
for i, x in enumerate((-1.6, -0.8, 1.4, 2.2)):
    kitchen.append(box(f"up_cab{i}", (0.78, 0.36, 0.75), (x, Y1 - 0.18, 1.95), WOOD))
for i in range(5):                            # shkaf eshigi chiziqlari va tutqichlar
    x = -1.9 + i * 1.05
    kitchen.append(box(f"seam{i}", (0.01, 0.005, 0.8), (x, Y1 - 0.6, 0.45), mat("seam", (0.05, 0.04, 0.03))))
    kitchen.append(cyl(f"handle{i}", 0.008, 0.18, (x + 0.12, Y1 - 0.625, 0.72), mat("steel", (0.8, 0.8, 0.8), 0.25, 1.0), rot=(0, 0, 0)))
# oyna (orqa devorda, ikki yuqori shkaf orasida): yorug' kunduz
WIN = mat("win", (1.0, 0.97, 0.92), emit=EV("WINE", 6.0))
kitchen.append(plane("window", (1.3, 0.9), (0.3, Y1 - 0.005, 1.75), WIN, rot=(90, 0, 0)))
for (sx, sz, x, z) in ((1.42, 0.06, 0.3, 1.3), (1.42, 0.06, 0.3, 2.2), (0.06, 0.96, -0.36, 1.75), (0.06, 0.96, 0.96, 1.75), (0.04, 0.9, 0.3, 1.75)):
    kitchen.append(box("wframe", (sx, 0.06, sz), (x, Y1 - 0.03, z), mat("wf", (0.92, 0.92, 0.9), 0.4)))
# orol stol (Megan uning ortida turadi)
ISL_Y = -0.2
kitchen.append(box("island", (2.2, 0.8, CT - 0.04), (0, ISL_Y, (CT - 0.04) / 2), WOOD))
kitchen.append(box("island_top", (2.3, 0.88, 0.04), (0, ISL_Y, CT - 0.02), MARBLE))
plant, plant_ms, _ = import_model(PH + "potted_plant_01/potted_plant_01.gltf", "plant", (-1.7, Y1 - 0.35, 0.9), 20, height=0.55)
box_root, box_ms, _ = import_model(PH + "medical_box/medical_box.gltf", "medbox", (-0.75, ISL_Y + 0.05, CT), -15, scale=0.8)
apple, _, _ = import_model(PH + "food_apple_01/food_apple_01.gltf", "apple", (1.75, Y1 - 0.4, 0.9), 0, height=0.08)
# taxta
BRD = box("board", (0.42, 0.3, 0.022), (0.12, ISL_Y + 0.02, CT + 0.011), BOARD, rot=(0, 0, -8))
BT = CT + 0.022
vis(BRD, [(1, SH['s12'] - 1)])

# ================= MEGAN =================
def fix_skin(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.3
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.55
                        n.inputs["Subsurface Weight"].default_value = 0.12
                        n.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25)
                        n.inputs["Subsurface Scale"].default_value = 0.004
                    n.inputs["Coat Weight"].default_value = 0.0

P = "mixamorig:"
groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
fix_skin(gmesh)
AR = lambda f: mc.load_action(f, True)
IDLE = AR("Breathing_Idle.fbx")
NOD = AR("Head_Nod_Yes.fbx")
mc.add_strip(girl, IDLE, 1, repeat=40.0)
def strip_to(arm, act, f0, f1, blend=0):
    s_ = mc.add_strip(arm, act, f0, blend=blend, hold=False)
    s_.action_frame_end = min(s_.action_frame_end, s_.action_frame_start + (f1 - f0) / s_.scale)
    s_.blend_out = blend
    return s_
strip_to(girl, NOD, SH["s4"] - 6, SH["s5"] - 1, blend=6)
GPOS = Vector((0.0, EV("GY", 0.36), 0.0))
groot.location = GPOS; groot.rotation_euler = (R(EV("LEAN", 4)), 0, 0)
bpy.context.view_layer.update()

def rest_w(arm, bn, tail=False):
    b = arm.data.bones[bn]; return arm.matrix_world @ (b.tail_local if tail else b.head_local)
def rest_rot(arm, bn):
    return (arm.matrix_world @ arm.data.bones[bn].matrix_local).to_3x3().normalized()

# ---- qo'llar: IK (bilak nishoni) + Copy Rotation (kaft yo'nalishi), ikkalasi ham shot bo'yicha kalitlanadi
def frame_from(f_rest, p_rest, f_new, p_new):
    """dam olishdagi (barmoq yo'nalishi, kaft normali) -> yangi yo'nalishlarga aylantiruvchi matritsa."""
    a = Matrix((f_rest, p_rest, f_rest.cross(p_rest))).transposed()
    fn = Vector(f_new).normalized(); pn = Vector(p_new); pn = (pn - fn * pn.dot(fn)).normalized()
    b = Matrix((fn, pn, fn.cross(pn))).transposed()
    return b @ a.inverted()

hands = {}
for side, sx in (("Left", 1), ("Right", -1)):
    fr = (rest_w(girl, P + side + "HandMiddle1") - rest_w(girl, P + side + "Hand")).normalized()
    wt = empty(f"ik_{side}"); rt = empty(f"rot_{side}"); pole = empty(f"pole_{side}")
    ik = girl.pose.bones[P + side + "ForeArm"].constraints.new("IK")
    ik.target = wt; ik.chain_count = 2; ik.pole_target = pole; ik.pole_angle = R(EV("POLE", -90)); ik.influence = 0.0
    cr = girl.pose.bones[P + side + "Hand"].constraints.new("COPY_ROTATION")
    cr.target = rt; cr.target_space = cr.owner_space = "WORLD"; cr.influence = 0.0
    fing = []
    for bn in ("Index1", "Index2", "Index3"):
        fe = empty(f"rot_{side}{bn}")
        c2 = girl.pose.bones[P + side + "Hand" + bn].constraints.new("COPY_ROTATION")
        c2.target = fe; c2.target_space = c2.owner_space = "WORLD"; c2.influence = 0.0
        fing.append((fe, c2, rest_rot(girl, P + side + "Hand" + bn)))
    hands[side] = dict(ik=ik, cr=cr, wt=wt, rt=rt, pole=pole, fr=fr, R0=rest_rot(girl, P + side + "Hand"), sx=sx, fing=fing)

def hand_key(side, f, wrist=None, fingers=None, palm=None, pole=None, on=True):
    h = hands[side]
    if on:
        Rm = frame_from(h["fr"], Vector((0, 0, -1)), fingers, palm) @ h["R0"]
        h["rt"].rotation_mode = "QUATERNION"; h["rt"].rotation_quaternion = Rm.to_quaternion()
        h["rt"].keyframe_insert("rotation_quaternion", frame=f)
        h["wt"].location = wrist; h["wt"].keyframe_insert("location", frame=f)
        h["pole"].location = pole; h["pole"].keyframe_insert("location", frame=f)
        Rd = frame_from(h["fr"], Vector((0, 0, -1)), fingers, palm)
        for k_, (fe, c2, R0f) in enumerate(h["fing"]):
            bend = Matrix.Rotation(R(EV("FBEND", 6)) * (k_ + 1), 3, Rd @ h["fr"].cross(Vector((0, 0, -1))))
            fe.rotation_mode = "QUATERNION"; fe.rotation_quaternion = (bend @ Rd @ R0f).to_quaternion(); fe.keyframe_insert("rotation_quaternion", frame=f)
    for c in [h["ik"], h["cr"]] + [x[1] for x in h["fing"]]:
        c.influence = 1.0 if on else 0.0; c.keyframe_insert("influence", frame=f)

SHO_L = rest_w(girl, P + "LeftArm"); SHO_R = rest_w(girl, P + "RightArm")
BOARD_C = Vector((0.12, ISL_Y + 0.02, BT))
WR_BOARD = Vector((EV("WRX", 0.2), EV("WRY", 0.03), BT + EV("WRZ", 0.036)))
F_BOARD = (EV("FBX", -0.35), -1.0, -0.12)
POLE_L = Vector((0.75, 0.75, 1.05)); POLE_R = Vector((-0.75, 0.75, 1.05))
WR_UP = Vector((EV("UPX", 0.02), EV("UPY", -0.1), EV("UPZ", 1.18)))
for f in (1, SH["s5"], SH["s9"]):
    hand_key("Left", f, WR_BOARD, F_BOARD, (0, 0, -1), POLE_L)
look = empty("look_t")
hd = girl.pose.bones[P + "Head"].constraints.new("DAMPED_TRACK"); hd.target = look; hd.track_axis = EV and os.environ.get("HEADAX", "TRACK_Z")
for f, v in ((1, 0.0), (SH["s4"], EV("LOOK", 0.0)), (SH["s5"], 0.0)):
    hd.influence = v; hd.keyframe_insert("influence", frame=f)
hand_key("Right", 1, on=False)
# shot 12-13: ikki qo'l stol ustida (yaralar tepadan ko'rinadi)
WR_FLAT_L = Vector((EV("FLX", 0.17), EV("FLY", 0.06), CT + 0.034)); WR_FLAT_R = Vector((-WR_FLAT_L.x, WR_FLAT_L.y, WR_FLAT_L.z))
hand_key("Left", SH["s12"], WR_FLAT_L, (-0.2, -1.0, -0.1), (0, 0, -1), POLE_L)
hand_key("Right", SH["s12"], WR_FLAT_R, (0.2, -1.0, -0.1), (0, 0, -1), POLE_R)
for side in hands:
    for o in [hands[side]["wt"], hands[side]["rt"], hands[side]["pole"]] + [x[0] for x in hands[side]["fing"]]: const_interp(o)
for c in (hands["Left"]["ik"], hands["Left"]["cr"], hands["Right"]["ik"], hands["Right"]["cr"]): pass
const_interp(girl)
look.location = WR_BOARD + Vector((-0.03, -0.12, -0.02))
bpy.context.view_layer.update()

def pose_w(bn, f):
    sc.frame_set(f); return girl.matrix_world @ girl.pose.bones[bn].head
def pose_tail(bn, f):
    sc.frame_set(f); return girl.matrix_world @ girl.pose.bones[bn].tail

# ---- yara (ko'rsatkich barmoq, 2-bo'g'in, ustki tomonda) — dam olish pozasida o'lchab, suyakka bog'lanadi
def finger_surface(side):
    """T-pozada ko'rsatkich barmoq 2-bo'g'inining ustki (+Z) yuzasidagi nuqta."""
    a = rest_w(girl, P + side + "HandIndex2"); b = rest_w(girl, P + side + "HandIndex3")
    mid = (a + b) / 2
    girl.data.pose_position = "REST"; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    body = next(o for o in gmesh if o.name.endswith("Body"))
    eb = body.evaluated_get(dg); me = eb.to_mesh()
    top = max(((eb.matrix_world @ v.co) for v in me.vertices if (Vector(((eb.matrix_world @ v.co).x - mid.x, (eb.matrix_world @ v.co).y - mid.y, 0))).length < 0.006), key=lambda p: p.z)
    eb.to_mesh_clear(); girl.data.pose_position = "POSE"; bpy.context.view_layer.update()
    return Vector((mid.x, mid.y, top.z)), (b - a).normalized()

BLOOD = wet_mat("blood", (0.25, 0.008, 0.01), 0.12, coat=0.6)
WOUND = wet_mat("wound", (0.42, 0.04, 0.05), 0.3, sss=0.3)
WOUND = attr_mix(WOUND, "heal", (0.75, 0.42, 0.38), 0.5)
SCAR = wet_mat("scar", (0.74, 0.42, 0.4), 0.42, sss=0.5, coat=0.1)
FOAM = wet_mat("foam", (0.95, 0.95, 0.93), 0.15, sss=0.6, coat=0.5)
FOAM.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (0.5, 0.5, 0.5)
wounds = {}
for side in ("Left", "Right"):
    s_, fdir = finger_surface(side)
    w = sphere(f"wound_{side}", 1.0, tuple(s_ + Vector((0, 0, -0.0009))), WOUND, sub=3)
    w.scale = (0.0044, 0.0022, 0.0014)            # barmoq bo'ylab ko'ndalang chiziq emas: kesik barmoqqa ko'ndalang
    w.rotation_euler = (0, 0, math.atan2(fdir.y, fdir.x) + R(90))
    follow(w, girl, P + side + "HandIndex2")
    wounds[side] = (w, s_, fdir)
wl, WS, FD = wounds["Left"]
wr = wounds["Right"][0]
# chap yara: CUT da ochiladi
for f, s in ((1, 0.0), (CUT - 1, 0.0), (CUT + 2, 1.0)):
    wl.scale = (0.0044 * max(s, 0.001), 0.0022 * max(s, 0.001), 0.0014); wl.keyframe_insert("scale", frame=f)
keyprop(wl, "heal", 1, 0.0); keyprop(wl, "heal", HEAL0, 0.0); keyprop(wl, "heal", HEAL_SLOW, 0.35); keyprop(wl, "heal", SCAR0, 0.5)
keyprop(wr, "heal", 1, 0.0); keyprop(wr, "heal", HEAL0, 0.0); keyprop(wr, "heal", HEAL_FAST, 1.0)
for f, s in ((HEAL0, 1.0), (HEAL_FAST, 0.05)):
    wr.scale = (0.0044 * s, 0.0022 * s, 0.0014 * s); wr.keyframe_insert("scale", frame=f)
vis(wr, [(SH["s12"], SH["s13"] - 1)])
# qon tomchilari
drops = []
for i in range(3):
    d = sphere(f"drop{i}", 1.0, tuple(WS + Vector((random.uniform(-0.003, 0.003), random.uniform(-0.002, 0.002), 0.0012))), BLOOD, sub=3)
    follow(d, girl, P + "LeftHandIndex2")
    f0 = CUT + 2 + i * 5
    for f, s in ((1, 0.0001), (f0, 0.0001), (f0 + 8, 0.0018 + 0.0008 * i), (FOAM0 + 10, 0.0018 + 0.0008 * i), (FOAM0 + 25, 0.0001)):
        d.scale = (s, s, s * 0.7); d.keyframe_insert("scale", frame=f)
    drops.append(d)
# chandiq (shot 13): bo'rtib chiqadi
scar = sphere("scar", 1.0, tuple(WS + Vector((0, 0, -0.0008))), SCAR, sub=4)
scar.rotation_euler = wl.rotation_euler; follow(scar, girl, P + "LeftHandIndex2")
for f, s in ((1, 0.0), (SCAR0, 0.0), (SCAR0 + 30, 1.0), (PUNCH, 1.15)):
    scar.scale = (0.0044 * max(s, 0.01), 0.0024 * max(s, 0.01), 0.0009 * max(s, 0.01)); scar.keyframe_insert("scale", frame=f)
vis(scar, [(SH["s13"], SH["s14"] - 1)])
for f, s in ((SCAR0, 1.0), (SCAR0 + 30, 0.6)):
    wl.scale = (0.0044 * s, 0.0022 * s, 0.0014); wl.keyframe_insert("scale", frame=f)

# ---- ko'pik: yara ustida mayda pufakchalar o'sadi
foam = []
FOAM_ME = bpy.data.meshes.new('foamme')
_bm = bmesh.new(); bmesh.ops.create_icosphere(_bm, subdivisions=2, radius=1.0); _bm.to_mesh(FOAM_ME); _bm.free()
for p_ in FOAM_ME.polygons: p_.use_smooth = True
fx_, fy_ = FD, Vector((-FD.y, FD.x, 0))
for i in range(int(EV("NFOAM", 420))):
    u = random.gauss(0, 0.45); v = random.gauss(0, 0.5)
    r = random.uniform(0.0005, 0.0019) * (1.3 - min(abs(u), 1.0) * 0.5)
    h = abs(random.gauss(0, 0.6)) * 0.005
    p = WS + fx_ * (v * 0.009) + fy_ * (u * 0.008) + Vector((0, 0, h + r * 0.4))
    b = inst(f"foam{i}", FOAM_ME, p, (1, 1, 1), FOAM)
    follow(b, girl, P + "LeftHandIndex2")
    f0 = FOAM0 + int(abs(u) * 14 + h * 2400 + random.uniform(0, 14))
    f1 = f0 + random.randint(10, 26)
    for f, s in ((1, 0.0), (f0, 0.0), (f1, r), (SH["s9"] + 30, r * 1.08)):
        b.scale = (max(s, 1e-5),) * 3; b.keyframe_insert("scale", frame=f)
    foam.append(b)
for o in foam: vis(o, [(FOAM0 - 2, SH["s10"] - 1)])

# ---- pichoq va limon (shot 1), shisha (shot 2)
sc.frame_set(10)
TIP = pose_tail(P + "LeftHandIndex3", 10); IDX2 = pose_w(P + "LeftHandIndex2", 10)
WS_POSE = wl.matrix_world.translation.copy()
lemon, lemon_ms, lemon_dim = import_model(PH + "lemon/lemon.gltf", "lemon", tuple(TIP + Vector((-0.05, -0.04, 0)) * 1.0), 70, height=0.07)
lemon.rotation_euler = (R(90), 0, R(70))
lemon.location = (TIP.x - 0.01, TIP.y - 0.06, BT + 0.025)
knife, knife_ms, _ = import_model(PH + "fish_knife/fish_knife.gltf", "knife", (0, 0, 0), 0, scale=1.7)
kp = empty("knife_path")
knife.parent = kp
# pichoq: chap barmoq yonida, tig' pastga; limondan sirpanib barmoqqa tushadi
K_A = WS_POSE + Vector((-0.03, -0.03, 0.05)); K_B = WS_POSE + Vector((-0.012, -0.012, 0.02)); K_C = WS_POSE + Vector((0.0, 0.0, 0.002))
kp.rotation_euler = (R(EV("KRX", 0)), R(EV("KRY", 0)), R(EV("KRZ", 15)))
STEEL = mat("blade", (0.85, 0.86, 0.88), 0.18, 1.0); KWOOD = mat("khandle", (0.08, 0.05, 0.035), 0.4)
for o in knife_ms:
    o.data.materials.clear(); o.data.materials.append(STEEL if "blade" in o.name else KWOOD)
for f, p in ((1, K_A + Vector((0, 0, 0.03))), (12, K_A), (18, K_B), (CUT, K_C), (CUT + 6, K_C + Vector((0.02, 0.01, 0.03))),
             (SH["s2"] - 1, K_C + Vector((0.08, 0.04, 0.12)))):
    key(kp, f, loc=tuple(p))
vis(knife, [(1, SH["s2"] - 1)])
vis(lemon, [(1, SH["s12"] - 1)])
GLASS_BR = wet_mat("amber", (0.32, 0.12, 0.03), 0.05, trans=0.9, ior=1.5)
LABEL = mat("label", (0.95, 0.95, 0.95), 0.6)
bot = empty("bottle")
bm_ = cyl("b_body", 0.03, 0.12, (0, 0, 0.06 - 0.15), GLASS_BR, verts=48); bm_.parent = bot
bn_ = cyl("b_neck", 0.012, 0.03, (0, 0, 0.135 - 0.15), GLASS_BR, verts=32); bn_.parent = bot
bl_ = cyl("b_label", 0.0305, 0.06, (0, 0, 0.06 - 0.15), LABEL, verts=48); bl_.parent = bot
bpy.ops.object.text_add(location=(0, -0.031, 0.06 - 0.15), rotation=(R(90), 0, 0)); tx = bpy.context.object
tx.data.body = "H2O2 3%"; tx.data.size = 0.014; tx.data.align_x = "CENTER"; tx.data.align_y = "CENTER"; tx.data.extrude = 0.0003
tx.data.materials.append(mat("ink", (0.05, 0.12, 0.45), 0.5)); tx.parent = bot
stream = cyl("stream", 0.0016, 1.0, (0, 0, -0.5), wet_mat("liquid", (0.9, 0.95, 1.0), 0.02, trans=1.0, ior=1.33), verts=12)
mouth = empty("mouth", (0, 0, 0.0), bot); stream.parent = None
BOT_P = WS_POSE + Vector((-0.012, 0.0, 0.085))
for f, a, dz in ((SH["s2"], 25, 0.05), (POUR - 4, 112, 0.0), (SH["s3"] - 1, 118, 0.0)):
    key(bot, f, loc=tuple(BOT_P + Vector((0, 0, dz))), rot=(0, a, 0))
vis(bot, [(SH["s2"], SH["s3"] - 1)])
# oqim: shisha og'zidan yaraga
sc.frame_set(POUR); bpy.context.view_layer.update()
M = mouth.matrix_world.translation.copy()
L_ = (M - WS_POSE).length
stream.location = (M + WS_POSE) / 2; stream.rotation_euler = (M - WS_POSE).to_track_quat("Z", "Y").to_euler()
for f, s in ((POUR - 2, 0.0), (POUR + 2, L_), (SH["s3"] - 1, L_)):
    stream.scale = (1, 1, max(s, 1e-4)); stream.keyframe_insert("scale", frame=f)
vis(stream, [(POUR - 2, SH["s3"] - 1)])

# ================= MIKRO OLAM =================
MX = Vector((80.0, 0.0, 0.0))
CELL = wet_mat("cell", (0.8, 0.22, 0.3), 0.32, sss=0.85, coat=0.4)
_N = CELL.node_tree.nodes; _L = CELL.node_tree.links
_nz = _N.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 9.0; _nz.inputs["Detail"].default_value = 4
_bp = _N.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.35; _bp.inputs["Distance"].default_value = 0.02
_L.new(_nz.outputs["Fac"], _bp.inputs["Height"]); _L.new(_bp.outputs["Normal"], _N["Principled BSDF"].inputs["Normal"])
CELL.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.4)
CELL.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.15
CELL = attr_mix(CELL, "burn", (0.09, 0.035, 0.02), 0.8, emit_col=(1.0, 0.45, 0.12), emit_k=EV("BURNE", 3.0))
NEWC = wet_mat("newcell", (1.0, 0.72, 0.72), 0.25, sss=1.0, coat=0.5)
NEWC.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.6, 0.6, 1)
NEWC.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.25
NEWC = attr_mix(NEWC, "burn", (0.12, 0.05, 0.03), 0.8, emit_col=(1.0, 0.5, 0.15), emit_k=3.0)
NUC = wet_mat("nucleus", (0.35, 0.08, 0.2), 0.4, sss=0.5)
BACT = wet_mat("bact", (0.12, 0.62, 0.05), 0.45, sss=0.3, coat=0.5)
BACT.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (0.5, 1.0, 0.3)
BACT = attr_mix(BACT, "burn", (0.08, 0.06, 0.02), 0.8, emit_col=(1.0, 0.6, 0.15), emit_k=3.0)
RBC = wet_mat("rbc", (0.62, 0.02, 0.03), 0.3, sss=0.7, coat=0.5)
RBC.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (1.0, 0.2, 0.15)
RBC = attr_mix(RBC, "burn", (0.12, 0.03, 0.02), 0.8, emit_col=(1.0, 0.4, 0.1), emit_k=2.5)
BUB = wet_mat("bubble", (1.0, 1.0, 1.0), 0.02, trans=1.0, ior=1.33)
OX = mat("oxy", (0.85, 0.06, 0.05), 0.25); HY = mat("hyd", (0.95, 0.95, 0.95), 0.25)
OXGLOW = mat("oxyglow", (0.5, 0.9, 1.0), 0.3, emit=2.0)

def lumpy_mesh(name, sub=3, amp=0.12, seed=0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1.0); o = bpy.context.object; o.name = name
    tex = bpy.data.textures.new(name + "_n", "CLOUDS"); tex.noise_scale = 0.6
    d = o.modifiers.new("d", "DISPLACE"); d.texture = tex; d.strength = amp; d.mid_level = 0.5
    bpy.ops.object.modifier_apply(modifier="d"); smooth(o)
    me = o.data; bpy.data.objects.remove(o, do_unlink=True); return me

CELL_ME = [lumpy_mesh(f"cellme{i}", 3, 0.18) for i in range(4)]
BUB_ME = bpy.data.meshes.new("bubme")
_bm = bmesh.new(); bmesh.ops.create_icosphere(_bm, subdivisions=3, radius=1.0); _bm.to_mesh(BUB_ME); _bm.free()
for p in BUB_ME.polygons: p.use_smooth = True
def bubble(loc, f0, r, rise=0.6, dur=24, wob=0.15, end=None):
    o = inst("bub", BUB_ME, loc, (0.0001,) * 3, BUB, rot=(0, 0, 0))
    key(o, 1, loc=tuple(loc), scale=0.0001); key(o, f0, loc=tuple(loc), scale=0.0001)
    p1 = Vector(loc) + Vector((random.uniform(-wob, wob), random.uniform(-wob, wob), rise))
    key(o, f0 + dur, loc=tuple(p1), scale=r)
    key(o, f0 + dur * 3, loc=tuple(p1 + Vector((0, 0, rise * 1.5))), scale=r * 1.15)
    return o

def burn_obj(o, f0, dur=12, shrink=0.72, flash=True):
    keyprop(o, "burn", 1, 0.0); keyprop(o, "burn", f0, 0.0); keyprop(o, "burn", f0 + dur, 1.0)
    s0 = tuple(o.scale)
    key(o, f0, scale=s0); key(o, f0 + dur + 6, scale=(s0[0] * shrink, s0[1] * shrink, s0[2] * shrink * 0.8))

# --- A: teri hujayralari maydoni (shot 6, 7, 8)
cells = []
for j in range(-11, 12):
    for i in range(-10, 11):
        p = MX + Vector((i * 0.5 + (j % 2) * 0.25 + random.uniform(-0.04, 0.04), j * 0.433 + random.uniform(-0.04, 0.04), 0))
        s = random.uniform(0.25, 0.3)
        c = inst("cell", random.choice(CELL_ME), p, (s, s, s * 0.62), CELL)
        c["burn"] = 0.0
        cells.append((c, p, s))
BURN_C = MX + Vector((0.4, 0.0, 0))
for c, p, s in cells:
    d = (p - BURN_C).length
    if d < 2.6:
        f0 = BURN0 + int(d * 9 + random.uniform(0, 5))
        burn_obj(c, f0)
        for k in range(2):
            bubble(p + Vector((random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), s * 0.5)), f0 + 4 + k * 5,
                   random.uniform(0.05, 0.11), rise=random.uniform(0.4, 0.9))
# H2O2 molekulalari
MOL_ME = None
MOL_T = None
def _mol_template():
    root = empty("molT", (0, 0, -500))
    parts = []
    for sx in (-1, 1):
        parts.append(sphere("mT_o", 0.075, (sx * 0.07, 0, -500), OX, sub=3))
        parts.append(sphere("mT_h", 0.048, (sx * 0.13, sx * 0.04, 0.07 * sx - 500), HY, sub=2))
        parts.append(cyl("mT_b", 0.016, 0.1, (sx * 0.1, sx * 0.02, 0.035 * sx - 500), HY, rot=(R(45 * sx), R(60), 0), verts=10))
    parts.append(cyl("mT_oo", 0.02, 0.14, (0, 0, -500), OX, rot=(0, R(90), 0), verts=12))
    parts.append(sphere("mT_g", 0.16, (0, 0, -500), glow_mat("mg", (0.4, 0.85, 1.0), 1.2, alpha=0.5, rim=True, blend=0.2), sub=2))
    for o in parts: o.parent = root; o.location.z += 500
    return root, parts
def molecule(name):
    global MOL_T
    if MOL_T is None: MOL_T = _mol_template()
    root = empty(name)
    for o in MOL_T[1]:
        c = o.copy(); sc.collection.objects.link(c); c.parent = root
    return root
def fly(o, f0, f1, p0, p1, spin=360):
    key(o, 1, loc=tuple(p0), rot=(0, 0, 0)); key(o, f0, loc=tuple(p0), rot=(0, 0, 0))
    key(o, f1, loc=tuple(p1), rot=(random.uniform(-1, 1) * spin, random.uniform(-1, 1) * spin, random.uniform(-1, 1) * spin))
    for fc in all_fcurves(o):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
mols = []
for i in range(int(EV("NMOL", 70))):            # A maydoniga yog'adi (shot 6-8)
    m_ = molecule(f"mol{i}")
    x, y = random.uniform(-3.5, 3.5), random.uniform(-3.0, 4.0)
    f0 = random.randint(230, 420); f1 = f0 + random.randint(40, 70)
    fly(m_, f0, f1, MX + Vector((x, y, 4.5)), MX + Vector((x + random.uniform(-0.5, 0.5), y + random.uniform(-0.5, 0.5), 0.25)))
    mols.append(m_)
# shot 7: kameraga to'g'ri uchadiganlar
CAM7 = MX + Vector((-2.9, -2.1, 0.38))
for i in range(14):
    m_ = molecule(f"molc{i}")
    src = MX + Vector((-2.4 + random.uniform(-1.2, 1.2), -1.0 + random.uniform(-0.8, 1.5), 3.5 + random.uniform(0, 1.5)))
    f0 = SH["s7"] - 30 + i * 5; f1 = f0 + 45
    dst = CAM7 + Vector((random.uniform(-0.6, 0.6), random.uniform(-0.3, 0.6), random.uniform(-0.2, 0.4)))
    fly(m_, f0, f1, src, dst + (dst - src).normalized() * 0.6)
# bakteriya + sog'lom hujayra (shot 8)
C8 = MX + Vector((0.2, 3.2, 0.0))
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0); bac = bpy.context.object; bac.name = "bacteria"
for v in bac.data.vertices:
    if v.co.x > 0: v.co.x += 1.2
    else: v.co.x -= 1.2
smooth(bac); bac.data.materials.append(BACT)
bac.location = C8 + Vector((-0.3, -0.1, 0.5)); bac.scale = (0.2, 0.2, 0.2); bac.rotation_euler = (0, R(-10), R(25))
bac["burn"] = 0.0
for k in range(10):                              # xivchinlar
    bpy.ops.curve.primitive_bezier_curve_add(); cu = bpy.context.object; cu.name = "flag"
    cu.data.bevel_depth = 0.04; cu.data.materials.append(BACT)
    a = random.uniform(0, 6.28)
    for idx, bp in enumerate(cu.data.splines[0].bezier_points):
        bp.co = (math.cos(a) * (1 + idx * 1.4) + (2.2 if k < 5 else -2.2) * (1 if idx else 0.9), math.sin(a) * (1 + idx * 1.2), random.uniform(-0.5, 0.5))
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.parent = bac
healthy = min(cells, key=lambda t: (t[1] - (C8 + Vector((0.35, 0.05, 0)))).length)
hc, hp, hs = healthy
for o, f0, cen in ((bac, HIT_B, bac.location.copy()), (hc, HIT_C, hp)):
    s0 = tuple(o.scale)
    keyprop(o, "burn", 1, 0.0); keyprop(o, "burn", f0 - 2, 0.0); keyprop(o, "burn", f0 + 8, 1.0)
    key(o, f0 - 3, scale=s0); key(o, f0 + 1, scale=tuple(x * 1.15 for x in s0)); key(o, f0 + 12, scale=tuple(x * 0.25 for x in s0))
    for k in range(9):
        bubble(cen + Vector((random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), 0.2)), f0 + random.randint(0, 8),
               random.uniform(0.05, 0.12), rise=random.uniform(0.5, 1.2), dur=16)
    m_ = molecule(f"hit{f0}")
    fly(m_, f0 - 26, f0, cen + Vector((random.uniform(-1, 1), -1.5, 2.5)), cen + Vector((0, 0, 0.15)))
    vis(m_, [(1, f0 + 1)])

# --- B: yara chekkasi, yangi nozik hujayralar (shot 10)
MB = MX + Vector((0, 14, 0))
for j in range(-6, 7):
    for i in range(-8, 9):
        x = i * 0.5 + (j % 2) * 0.25
        if abs(x) < 0.7: continue
        p = MB + Vector((x, j * 0.433, -0.05 + abs(x) * 0.05)); s = random.uniform(0.25, 0.3)
        inst("cellB", random.choice(CELL_ME), p, (s, s, s * 0.62), CELL)["burn"] = 0.0
newcells = []
for k in range(26):
    p = MB + Vector((random.uniform(-0.65, 0.65), random.uniform(-2.4, 2.4), random.uniform(-0.15, 0.05)))
    s = random.uniform(0.11, 0.17)
    c = inst("newcell", random.choice(CELL_ME), p, (s, s, s * 0.7), NEWC); c["burn"] = 0.0
    # avval ko'prik quradi (o'sadi), so'ng eriydi
    key(c, 1, scale=(s * 0.7, s * 0.7, s * 0.5)); key(c, SH["s10"] + 30, scale=(s, s, s * 0.7))
    f0 = NEW_D + int(abs(p.y - MB.y) * 5 + random.uniform(0, 8))
    keyprop(c, "burn", 1, 0.0); keyprop(c, "burn", f0, 0.0); keyprop(c, "burn", f0 + 10, 1.0)
    key(c, f0 + 4, scale=(s, s, s * 0.7)); key(c, f0 + 16, scale=(0.0001,) * 3)
    for q in range(2):
        bubble(p + Vector((random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), 0.08)), f0 + 4 + q * 4, random.uniform(0.04, 0.09), rise=0.7, dur=14)
for i in range(22):
    m_ = molecule(f"molB{i}")
    x, y = random.uniform(-1.5, 1.5), random.uniform(-2.5, 2.5)
    f0 = random.randint(SH["s10"] - 20, NEW_D + 10); fly(m_, f0, f0 + 50, MB + Vector((x, y, 3.5)), MB + Vector((x * 0.3, y, 0.1)))

# --- C: qon tanachalari (shot 11)
MC_ = MX + Vector((0, -14, 0))
def rbc_mesh():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0); o = bpy.context.object
    for v in o.data.vertices:
        r2 = min(v.co.x ** 2 + v.co.y ** 2, 0.999)
        z = 0.5 * math.sqrt(1 - r2) * (0.207 + 2.003 * r2 - 1.123 * r2 * r2)
        v.co.z = math.copysign(max(z, 0.02), v.co.z if v.co.z else 1)
    smooth(o); me = o.data; bpy.data.objects.remove(o, do_unlink=True); return me
RBC_ME = rbc_mesh()
rbcs = []
for k in range(int(EV("NRBC", 30))):
    p = MC_ + Vector((random.uniform(-1.8, 1.8), random.uniform(-1.5, 2.5), random.uniform(-1.2, 1.4)))
    s = random.uniform(0.3, 0.36)
    c = inst("rbc", RBC_ME, p, (s, s, s), RBC); c["burn"] = 0.0
    r0 = Vector((random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6)))
    drift = Vector((random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(-0.2, 0.2)))
    key(c, SH["s11"], loc=tuple(p), rot=tuple(math.degrees(a) for a in r0))
    key(c, SH["s12"], loc=tuple(p + drift), rot=tuple(math.degrees(a) + random.uniform(-90, 90) for a in r0))
    for fc in all_fcurves(c):
        for k_ in fc.keyframe_points: k_.interpolation = "LINEAR"
    f0 = RBC_D + int(random.uniform(-6, 20))
    keyprop(c, "burn", 1, 0.0); keyprop(c, "burn", f0, 0.0); keyprop(c, "burn", f0 + 10, 1.0)
    key(c, f0, scale=s); key(c, f0 + 3, scale=s * 1.08); key(c, f0 + 16, scale=0.0001)
    for q in range(3):
        bubble(p + drift * ((f0 - SH["s11"]) / 64) + Vector((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), 0)),
               f0 + 3 + q * 3, random.uniform(0.04, 0.1), rise=0.6, dur=14)
    rbcs.append(c)
for i in range(16):
    m_ = molecule(f"molC{i}")
    p = MC_ + Vector((random.uniform(-2, 2), random.uniform(-1.5, 2.5), random.uniform(-1, 1.2)))
    f0 = random.randint(SH["s11"] - 20, RBC_D); fly(m_, f0, f0 + 40, p + Vector((random.uniform(-2, 2), random.uniform(-2, 0), 2.5)), p)

# ================= SHIFOKOR (shot 14) =================
DX = Vector((-80.0, 0.0, 0.0))
droot, doc, dmesh = mc.load_character("doc", "Josh.fbx")
fix_skin(dmesh)
COAT = mat("labcoat", (0.88, 0.9, 0.92), 0.6)
SHIRT = mat("docshirt", (0.45, 0.6, 0.78), 0.6)
for o in dmesh:
    if o.name.endswith("Suit"): o.data.materials.clear(); o.data.materials.append(COAT)
    elif o.name.endswith("Shirt"): o.data.materials.clear(); o.data.materials.append(SHIRT)
droot.location = DX
mc.add_strip(doc, AR("Breathing_Idle.fbx"), 1, repeat=40.0)
strip_to(doc, AR("Shaking_Head_No.fbx"), SH["s14"] - 12, DISMISS + 4, blend=4)
strip_to(doc, AR("Dismissing_Gesture_2.fbx"), DISMISS - 6, END + 20, blend=6)
# stetoskop (bo'yin atrofida)
NK = rest_w(doc, P + "Neck")
pts = [NK + Vector(v) for v in ((-0.075, -0.13, -0.32), (-0.085, -0.07, -0.12), (-0.06, 0.04, 0.0), (0.0, 0.07, 0.02), (0.06, 0.04, 0.0), (0.085, -0.07, -0.12), (0.07, -0.12, -0.3))]
cd = bpy.data.curves.new("steth", "CURVE"); cd.dimensions = "3D"; cd.bevel_depth = 0.0045
sp = cd.splines.new("NURBS"); sp.points.add(len(pts) - 1)
for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
sp.use_endpoint_u = True; sp.order_u = 3
steth = bpy.data.objects.new("steth", cd); sc.collection.objects.link(steth); cd.materials.append(mat("rubber", (0.04, 0.04, 0.05), 0.4))
follow(steth, doc, P + "Spine2")
disc = cyl("steth_disc", 0.018, 0.008, tuple(pts[0] + Vector((0, -0.005, -0.015))), mat("steel2", (0.85, 0.85, 0.87), 0.2, 1.0), rot=(R(80), 0, 0))
follow(disc, doc, P + "Spine2")
# oldinda: peroksid shishasi stolchada (xira)
bot2 = empty("bottle2")
for nm, r_, d_, z_, m_ in (("b2_body", 0.03, 0.12, 0.06, GLASS_BR), ("b2_neck", 0.012, 0.03, 0.135, GLASS_BR), ("b2_label", 0.0305, 0.06, 0.06, LABEL),
                           ("b2_cap", 0.014, 0.025, 0.16, mat("cap", (0.95, 0.95, 0.95), 0.4))):
    o = cyl(nm, r_, d_, (0, 0, z_), m_, verts=40); o.parent = bot2
tx2 = tx.copy(); tx2.data = tx.data.copy(); sc.collection.objects.link(tx2); tx2.parent = bot2; tx2.location.z += 0.15
TRAY_P = DX + Vector((-0.12, -0.62, 0.0))
box("doc_table", (0.3, 0.3, 0.8), tuple(TRAY_P + Vector((0, 0, 0.4))), mat("steel3", (0.7, 0.72, 0.74), 0.3, 1.0))
bot2.location = TRAY_P + Vector((-0.05, 0.0, 0.8)); bot2.rotation_euler = (0, 0, R(-20))
dfloor = box("doc_floor", (8, 8, 0.02), tuple(DX + Vector((0, 0, -0.01))), mat("vinyl", (0.55, 0.6, 0.6), 0.35))

# ================= KAMERALAR =================
cams = []
def camera(name, f0, f1, p0, p1, target, lens, fstop=None, ease="SINE", lens1=None, noise=0.012, parent=None, shake=(), rot=None, lens_keys=(), easing="EASE_OUT"):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = 0.002; d.clip_end = 600
    rig = empty(name + "_rig", (0, 0, 0), parent)
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.parent = rig
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    else:
        c.rotation_euler = [R(a) for a in rot]
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if target is not None: d.dof.focus_object = target
        else: d.dof.focus_distance = (Vector(p0) - Vector(p1)).length + abs(p1[2] - WS_FLAT.z)
    key(c, f0, loc=tuple(p0)); key(c, f1, loc=tuple(p1))
    if lens1:
        d.lens = lens; d.keyframe_insert("lens", frame=f0); d.lens = lens1; d.keyframe_insert("lens", frame=f1)
    for (lf, lv) in lens_keys:
        d.lens = lv; d.keyframe_insert("lens", frame=lf)
    for fc in all_fcurves(c):
        for k in fc.keyframe_points: k.interpolation = ease; k.easing = easing
        n = fc.modifiers.new("NOISE"); n.scale = 22; n.strength = noise; n.phase = random.uniform(0, 100)
    for (sf, amp, dur) in shake:
        key(rig, sf - 1, loc=(0, 0, 0))
        for k in range(dur):
            a_ = amp * (1 - k / dur)
            key(rig, sf + k, loc=(random.uniform(-a_, a_), random.uniform(-a_, a_), random.uniform(-a_, a_)))
        key(rig, sf + dur, loc=(0, 0, 0))
    cams.append((f0, c)); return c

def tgt(name, p, parent=None):
    e = empty(name, (0, 0, 0)); e.location = p; e.parent = parent; return e
def tgt_follow(name, obj):
    e = empty(name); cl = e.constraints.new("COPY_LOCATION"); cl.target = obj; return e

W = WS_POSE
wt_ = tgt_follow("t_wound", wl)
sc.frame_set(150); HEAD4 = girl.matrix_world @ girl.pose.bones[P + "Head"].head; HAND4 = girl.matrix_world @ girl.pose.bones[P + "LeftHand"].head
sc.frame_set(660); WS_FLAT = wl.matrix_world.translation.copy(); WR_FLAT = wr.matrix_world.translation.copy()
sc.frame_set(10)
camera("c01_cut", SH["s1"], SH["s2"] - 1, W + Vector((-0.07, -0.17, 0.035)), W + Vector((-0.045, -0.12, 0.03)), wt_, 35, 4.0, "QUART", shake=[(CUT + 1, 0.004, 8)])
camera("c02_pour", SH["s2"], SH["s3"] - 1, W + Vector((0.12, -0.2, 0.08)), W + Vector((0.09, -0.15, 0.065)), tgt("t_pour", W + Vector((-0.01, 0.0, 0.035))), 32, 5.6)
camera("c03_foam", SH["s3"], SH["s4"] - 1, W + Vector((0.06, -0.06, 0.06)), W + Vector((-0.05, -0.06, 0.065)), wt_, 85, 11.0, noise=0.002)
mid4 = tgt("t_mid4", Vector((0.06, 0.15, 1.25)))
camera("c04_nod", SH["s4"], SH["s5"] - 1, Vector((0.42, -0.95, 1.0)), Vector((0.3, -0.75, 1.06)), mid4, 26, 2.8)
camera("c05_dive", SH["s5"], SH["s6"] - 1, W + Vector((-0.02, -0.08, 0.11)), W + Vector((-0.002, -0.006, 0.014)), wt_, 45, 32.0, "EXPO", lens1=70, noise=0.002, easing="EASE_IN")
camera("c06_cells", SH["s6"], SH["s7"] - 1, MX + Vector((-2.2, -3.1, 0.95)), MX + Vector((-0.7, -1.5, 0.6)), tgt("t6", MX + Vector((0.5, 0.3, 0.1))), 24, 2.8, noise=0.03)
camera("c07_mol", SH["s7"], SH["s8"] - 1, CAM7, CAM7 + Vector((0.25, 0.25, 0.05)), tgt("t7", MX + Vector((-2.3, -1.2, 2.2))), 18, 4.0, noise=0.03)
c8t = tgt("t8", C8 + Vector((0.0, 0, 0.42)))
camera("c08_bact", SH["s8"], SH["s9"] - 1, C8 + Vector((0.05, -1.3, 1.0)), C8 + Vector((-0.3, -1.05, 0.88)), c8t, 30, 4.0, noise=0.02)
camera("c09_foam", SH["s9"], SH["s10"] - 1, W + Vector((-0.07, -0.05, 0.075)), W + Vector((-0.04, -0.07, 0.06)), wt_, 70, 11.0, noise=0.002)
camera("c10_new", SH["s10"], SH["s11"] - 1, MB + Vector((-1.3, -2.3, 1.5)), MB + Vector((-0.45, -1.6, 1.0)), tgt("t10", MB), 26, 4.0, noise=0.03)
camera("c11_rbc", SH["s11"], SH["s12"] - 1, MC_ + Vector((0.0, -3.0, 0.35)), MC_ + Vector((0.6, -2.2, 0.05)), tgt("t11", MC_ + Vector((0, 0.3, 0))), 32, 4.0, noise=0.03)
MID12 = (WS_FLAT + WR_FLAT) / 2
camera("c12_heal", SH["s12"], SH["s13"] - 1, MID12 + Vector((0.0, -0.02, 0.6)), MID12 + Vector((0.0, -0.01, 0.48)), None, 32, None, rot=(0, 0, -90), noise=0.004)
wt2 = tgt("t_scar", WS_FLAT)
camera("c13_scar", SH["s13"], SH["s14"] - 1, WS_FLAT + Vector((-0.03, -0.08, 0.11)), WS_FLAT + Vector((-0.02, -0.06, 0.08)), wt2, 60, 11.0,
       lens_keys=[(SH["s13"], 60), (PUNCH, 70), (PUNCH + 3, 100), (SH["s14"] - 1, 105)], shake=[(PUNCH, 0.003, 6)], noise=0.002)
dt_ = tgt("t_doc", DX + Vector((0, 0.0, 1.45)))
camera("c14_doc", SH["s14"], END, DX + Vector((0.3, -1.3, 0.95)), DX + Vector((0.18, -1.0, 1.05)), dt_, 22, 2.8, noise=0.01)
for f, c in cams: sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = cams[0][1]
REAL = [(1, SH["s6"] - 1), (SH["s9"], SH["s10"] - 1), (SH["s12"], SH["s14"] - 1)]
MICRO = [(SH["s6"], SH["s9"] - 1), (SH["s10"], SH["s12"] - 1)]
DOC = [(SH["s14"], END)]

# ================= YORUG'LIK / OSMON =================
w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Generated"], mp.inputs[0])
mp.inputs["Rotation"].default_value = (0, 0, R(EV("HDRI_ROT", 100)))
kit = N.new("ShaderNodeTexEnvironment"); kit.image = bpy.data.images.load(PH + "comfy_cafe.hdr"); L.new(mp.outputs[0], kit.inputs[0])
hos = N.new("ShaderNodeTexEnvironment"); hos.image = bpy.data.images.load(PH + "hospital_room.hdr"); L.new(mp.outputs[0], hos.inputs[0])
kb = N.new("ShaderNodeBackground"); L.new(kit.outputs[0], kb.inputs[0]); kb.inputs[1].default_value = EV("KITW", 0.5)
hb = N.new("ShaderNodeBackground"); L.new(hos.outputs[0], hb.inputs[0]); hb.inputs[1].default_value = EV("HOSW", 1.0)
mb = N.new("ShaderNodeBackground"); mb.inputs[0].default_value = (0.16, 0.012, 0.02, 1); mb.inputs[1].default_value = EV("MICW", 1.0)
m1 = N.new("ShaderNodeMixShader"); L.new(kb.outputs[0], m1.inputs[1]); L.new(mb.outputs[0], m1.inputs[2])
m2 = N.new("ShaderNodeMixShader"); L.new(m1.outputs[0], m2.inputs[1]); L.new(hb.outputs[0], m2.inputs[2])
L.new(m2.outputs[0], N["World Output"].inputs[0])
for f in sorted({a for a, b in REAL + MICRO + DOC}):
    keyval(m1.inputs["Fac"], f, 1.0 if in_ranges(f, MICRO) else 0.0)
    keyval(m2.inputs["Fac"], f, 1.0 if in_ranges(f, DOC) else 0.0)
const_interp(w.node_tree)

def area(name, loc, target, energy, size, col):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.energy = energy; l.data.size = size; l.data.color = col; l.location = loc
    t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l
ctr = tgt("t_counter", (0.1, ISL_Y, CT))
area("win_light", (0.3, Y1 - 0.25, 1.75), ctr, EV("WINL", 260), 1.3, (0.85, 0.92, 1.0))
area("ceil", (0.0, -0.6, HZ - 0.15), ctr, EV("CEIL", 160), 1.6, (1.0, 0.82, 0.62))
area("macro_key", tuple(W + Vector((0.25, -0.3, 0.35))), wt_, EV("MKEY", 9), 0.25, (1.0, 0.9, 0.8))
area("macro_rim", tuple(W + Vector((-0.2, 0.35, 0.2))), wt_, EV("MRIM", 6), 0.2, (0.8, 0.9, 1.0))
area("face4", (0.9, -1.0, 2.0), mid4, EV("FACE", 60), 1.0, (1.0, 0.86, 0.72))
tl = bpy.data.objects.new("timelapse_sun", bpy.data.lights.new("timelapse_sun", "SUN")); sc.collection.objects.link(tl)
tl.data.angle = R(1.0); tl.data.color = (1.0, 0.85, 0.65)
for f, e, rz in ((1, 0.0, 0), (SH["s12"] - 1, 0.0, 0), (SH["s12"], 3.5, -60), (SH["s12"] + 24, 0.4, 60), (SH["s12"] + 25, 3.5, -60),
                 (SH["s12"] + 50, 0.4, 60), (SH["s12"] + 51, 3.5, -60), (SH["s12"] + 76, 0.4, 60), (SH["s12"] + 77, 3.5, -60),
                 (SH["s13"] - 1, 1.5, 20), (SH["s13"], 0.0, 0)):
    tl.data.energy = e; tl.data.keyframe_insert("energy", frame=f)
    tl.rotation_euler = (R(35), 0, R(rz)); tl.keyframe_insert("rotation_euler", frame=f)
for f_ in all_fcurves(tl.data):
    for k_ in f_.keyframe_points: k_.interpolation = "LINEAR"
for nm, loc, e, col in (("mic_key", (-3, -4, 5), 2600, (1.0, 0.85, 0.85)), ("mic_rim", (3, 5, 2.5), 1800, (1.0, 0.45, 0.25)), ("mic_fill", (0, -6, 1), 500, (0.5, 0.6, 1.0))):
    for off in (Vector((0, 0, 0)), Vector((0, 14, 0)), Vector((0, -14, 0))):
        area(nm, tuple(MX + off + Vector(loc)), tgt("t_" + nm, MX + off), EV("MICL", 1.0) * e, 4.0, col)
area("doc_key", tuple(DX + Vector((1.6, -1.8, 2.6))), dt_, EV("DKEY", 380), 1.5, (1.0, 0.95, 0.9))
area("doc_rim", tuple(DX + Vector((-1.2, 1.4, 2.4))), dt_, EV("DRIM", 300), 1.2, (0.8, 0.9, 1.0))

# ================= RENDER =================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 14)); sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 6; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.cycles.blur_glossy = 1.0
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = EV("EXPOSURE", 0.0)
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("DBG_CAM"):
    pc, pt, ln = os.environ["DBG_CAM"].split(";")
    sc.timeline_markers.clear()
    dtg = empty("dbg_t", tuple(map(float, pt.split(","))))
    d = bpy.data.cameras.new("dbg"); d.lens = float(ln); d.clip_start = 0.002; d.clip_end = 600
    dc = bpy.data.objects.new("dbg", d); sc.collection.objects.link(dc); dc.location = tuple(map(float, pc.split(",")))
    t = dc.constraints.new("TRACK_TO"); t.target = dtg; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    sc.camera = dc

print("WOUND", tuple(W), "FLAT", tuple(WS_FLAT), "HEAD4", tuple(HEAD4))
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; bpy.ops.render.render(write_still=True)
    else:
        sc.frame_start = int(os.environ.get("START", 1)); sc.frame_end = int(os.environ.get("STOP", END))
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
