# Zack D. Films uslubi: "Nega o'z ovozingiz yozuvda xunuk eshitiladi?" (49 s, 12 kadr, 9:16).
# Asos: scene3.py (xona, Poly Haven, render sozlamalari) + mixchar.py (Mixamo qahramonlar).
# Megan telefonda ovozini eshitadi, Kate va Remy tinglaydi, rentgen: havo va suyak orqali eshitish.
import bpy, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_ovoz/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
END = 1190
sc.frame_start, sc.frame_end, sc.render.fps = 1, END, 24
random.seed(7)

# kadrlar (storyboard bilan bir xil)
SH = dict(s1=1, s2=91, s3=187, s4=271, s5=346, s6=466, s7=552, s8=648, s9=744, s10=864, s11=991, s12=1101)
XR0, XR1, XR_END = 400, 416, 863          # rentgen o'tishi va tugashi

# ---------------- yordamchilar ----------------
def mat(name, col, rough=0.5, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def glow_mat(name, col, strength, alpha=1.0, rim=False):
    """Emissiya + shaffoflik (tovush halqalari, impulslar, rentgen)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    if rim:
        lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = alpha
        L.new(lw.outputs["Facing"], mul.inputs[0]); L.new(mul.outputs[0], mx.inputs["Fac"])
    else:
        mx.inputs["Fac"].default_value = alpha
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
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

def torus(name, m, minor=0.08):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=minor, major_segments=40, minor_segments=8)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o); return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = (scale,)*3 if isinstance(scale, (int, float)) else scale; o.keyframe_insert("scale", frame=f)

def vis(o, ranges):
    objs = [o] + list(o.children_recursive)
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

def set_interp(idb, mode="BEZIER", path=None, easing=None):
    for fc in all_fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points:
            k.interpolation = mode
            if easing: k.easing = easing

def keyval(socket_owner, f, v, attr="default_value"):
    setattr(socket_owner, attr, v); socket_owner.keyframe_insert(attr, frame=f)

# ================= XONA (scene3.py dagi ichki qism) =================
M = dict(
    trim=mat("trim", (0.92, 0.92, 0.9), 0.4), darkwood=mat("darkwood", (0.15, 0.08, 0.04), 0.4, coat=0.4),
    winlight=mat("winlight", (1.0, 0.95, 0.85), 0.5, emit=6.0), lampshade=mat("lampshade", (1.0, 0.85, 0.6), 0.6, emit=3.0),
    curtain=mat("curtain", (0.85, 0.82, 0.72), 0.9), brass=mat("brass", (0.85, 0.65, 0.3), 0.25, metal=1.0),
    door=mat("door", (0.35, 0.08, 0.06), 0.35, coat=0.5), rug=mat("rug", (0.55, 0.18, 0.12), 0.95),
    art=mat("art", (0.2, 0.45, 0.6), 0.5),
)
def pbr(name, folder, scale=1.0, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = "BOX"; t.projection_blend = 0.2
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
FLOOR = pbr("ph_floor", "laminate_floor_02", 0.5)
WALL = pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.82, 0.88, 0.95))
room = []
room += [box("floor", (6, 5, 0.06), (0, 2.5, -0.03), FLOOR), box("ceiling", (6, 5, 0.06), (0, 2.5, 2.73), M["trim"])]
room += [box("wall_back_l", (2.2, 0.12, 2.7), (-1.9, 5.0, 1.35), WALL), box("wall_back_r", (2.2, 0.12, 2.7), (1.9, 5.0, 1.35), WALL),
         box("wall_back_b", (1.6, 0.12, 0.85), (0, 5.0, 0.425), WALL), box("wall_back_t", (1.6, 0.12, 0.45), (0, 5.0, 2.475), WALL),
         box("window_glow", (1.8, 0.02, 1.6), (0, 5.4, 1.6), M["winlight"])]
for x in (-0.78, 0.78): room.append(box("wframe", (0.06, 0.16, 1.4), (x, 5.0, 1.55), M["trim"]))
room.append(box("wframe_m", (1.6, 0.16, 0.06), (0, 5.0, 1.55), M["trim"]))
for x in (-1.1, 1.1):
    c = box("curtain", (0.5, 0.06, 2.3), (x, 4.88, 1.4), M["curtain"])
    d = c.modifiers.new("wave", "WAVE"); d.height = 0.04; d.width = 0.15; d.narrowness = 1; d.use_y = False; d.speed = 0
    room.append(c)
room += [box("wall_left", (0.12, 5, 2.7), (-3.0, 2.5, 1.35), WALL), box("wall_right", (0.12, 5, 2.7), (3.0, 2.5, 1.35), WALL)]
for x in (-1.75, 1.75): room.append(box("wall_front", (2.5, 0.2, 2.7), (x, 0.0, 1.35), WALL))
room.append(box("wall_front_t", (1.0, 0.2, 0.55), (0, 0.0, 2.425), WALL))
room.append(box("door", (0.92, 0.05, 2.12), (0.0, 0.0, 1.06), M["door"]))
for x, y, l, a in ((0, 4.93, 6, 0), (-2.93, 2.5, 5, 90), (2.93, 2.5, 5, 90)):
    room.append(box("baseboard", (l, 0.03, 0.12), (x, y, 0.06), M["trim"], rot=(0, 0, a)))
room.append(box("rug", (2.8, 1.9, 0.01), (0.1, 2.9, 0.005), M["rug"]))
room += [cyl("lamp_base", 0.12, 0.03, (2.4, 4.4, 0.015), M["brass"]), cyl("lamp_pole", 0.015, 1.5, (2.4, 4.4, 0.75), M["brass"]),
         cyl("lamp_shade", 0.22, 0.32, (2.4, 4.4, 1.55), M["lampshade"])]
room.append(box("shelf", (0.08, 1.4, 0.03), (2.92, 2.0, 1.5), M["darkwood"]))
for i in range(6):
    room.append(box("book", (0.16, 0.05, 0.22 + 0.03*(i % 3)), (2.86, 1.5 + i*0.08, 1.63),
                    mat(f"book{i}", [(0.6, 0.1, 0.1), (0.1, 0.3, 0.5), (0.8, 0.7, 0.3)][i % 3], 0.6)))
room.append(box("pic2", (0.5, 0.035, 0.5), (2.0, 4.915, 1.7), M["art"]))

def import_gltf(path, loc, rot_z=0.0, scale=1.0, name=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(name or os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler.z = R(rot_z); root.scale = (scale,) * 3
    return root, new
for args in ((PH + "Sofa_01/Sofa_01.gltf", (-0.2, 4.35, 0), 0), (PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.2, 3.2, 0), 0),
             (PH + "potted_plant_01/potted_plant_01.gltf", (-2.5, 4.5, 0), 0, 1.2),
             (PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-2.0, 4.92, 1.5), 0)):
    room.append(import_gltf(*args)[0])

# ================= QAHRAMONLAR =================
def fix_skin(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.25
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.62
                    n.inputs["Coat Weight"].default_value = 0.0

groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
kroot, kate, kmesh = mc.load_character("kate", "Kate.fbx")
rroot, remy, rmesh = mc.load_character("josh", "Josh.fbx")
fix_skin(gmesh + kmesh + rmesh)

G0 = Vector(tuple(map(float, os.environ.get("G0", "1.2,2.4,0").split(","))))
GROT = float(os.environ.get("GROT", -142))
groot.location = G0; groot.rotation_euler.z = R(GROT)
KPOS = tuple(map(float, os.environ.get("KPOS", "-0.75,3.98,0").split(",")))
RPOS = tuple(map(float, os.environ.get("RPOS", "0.35,3.98,0").split(",")))
kroot.location = KPOS; kroot.rotation_euler.z = R(float(os.environ.get("KROT", 8)))
rroot.location = RPOS; rroot.rotation_euler.z = R(float(os.environ.get("RROT", 18)))
bpy.context.view_layer.update()
GM = groot.matrix_world.copy()
def ML(x, y, z):
    """Megan'ning mahalliy koordinatasi (old tomoni -Y, chap qo'li +X) -> dunyo."""
    return GM @ Vector((x, y, z))

A = lambda f: mc.load_action(f, True)
mc.add_strip(girl, A("Texting_While_Standing.fbx"), 1, src=(40, 400))
mc.add_strip(girl, A("Annoyed_Head_Shake.fbx"), 100, speed=1.0, blend=8)
mc.add_strip(girl, A("Talking_2.fbx"), SH["s3"] - 4, repeat=3.0, speed=1.0, blend=5)
mc.add_strip(girl, A("Talking_5.fbx"), SH["s10"], speed=1.0, blend=0)
mc.add_strip(girl, A("Texting_While_Standing.fbx"), SH["s11"], blend=0, src=(40, 400))
mc.add_strip(girl, A("Annoyed_Head_Shake.fbx"), SH["s12"] - 6, speed=0.9, blend=6)
mc.add_strip(kate, A("Sitting_Talking.fbx"), 1, src=(200, 1300))
mc.add_strip(remy, A("Sitting_Idle_5.fbx"), 1, repeat=3.0)
for r_, ms in ((kroot, kmesh), (rroot, rmesh)):
    vis(r_, [(SH["s3"], SH["s5"] - 1)])
    for o in ms: vis(o, [(SH["s3"], SH["s5"] - 1)])

def bone_world(arm, bone, f=None, rest=False):
    if f is not None: sc.frame_set(f)
    bpy.context.view_layer.update()
    if rest: return arm.matrix_world @ arm.data.bones[bone].matrix_local
    return arm.matrix_world @ arm.pose.bones[bone].matrix

def follow(obj, arm, bone, ref_frame=None):
    """obj suyakka ergashadi; obj'ning hozirgi dunyo joyi ref kadrdagi (yoki dam holatdagi) suyakka nisbatan saqlanadi."""
    c = obj.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = bone
    H = bone_world(arm, bone, rest=True) if ref_frame is None else bone_world(arm, bone, ref_frame)
    c.inverse_matrix = H.inverted()
    return c

HEAD = "mixamorig:Head"
fx = empty("fx_head")                      # bosh suyagiga ergashuvchi hamma narsaning ota-onasi (dam holat koordinatasida)
follow(fx, girl, HEAD)

# ================= TELEFON (BlenderKit, brendsiz) =================
phone, pparts = import_gltf(BK + "a6d503d4_u.glb", (0, 0, 0), 0, 1.0, name="phone")
for o in pparts:
    if o.type == "MESH" and o.name.startswith("screen"):
        o.data.materials.clear(); o.data.materials.append(glow_mat("screen", (0.02, 0.03, 0.07), 1.0))
bars_root = empty("bars", (0, 0, 0), phone)
BAR = glow_mat("bar", (0.25, 0.75, 1.0), 12.0)
REC = glow_mat("rec", (1.0, 0.08, 0.05), 10.0)
bars = []
for i in range(23):
    x = -0.031 + i * 0.0028
    b = box(f"bar{i}", (0.0017, 0.02, 0.0006), (x, -0.005, 0.0122), BAR); b.parent = bars_root; bars.append(b)
dot = cyl("recdot", 0.0035, 0.0006, (0, 0.055, 0.0122), REC, verts=16); dot.parent = bars_root
ph_pl = box("playhead", (0.07, 0.0007, 0.0006), (0, -0.035, 0.0122), BAR); ph_pl.parent = bars_root
def bars_anim(f0, f1):
    for f in range(f0, f1 + 1, 2):
        for i, b in enumerate(bars):
            env = 0.35 + 0.65 * math.sin(math.pi * (i + 1) / (len(bars) + 1))
            b.scale = (1, max(0.08, env * random.uniform(0.15, 1.6)), 1); b.keyframe_insert("scale", frame=f)
bars_anim(1, SH["s3"]); bars_anim(SH["s11"], END)
PREF = int(os.environ.get("PREF", 60))
PLOC = Vector(tuple(map(float, os.environ.get("PLOC", "-0.03,-0.245,1.19").split(","))))
PR = tuple(map(float, os.environ.get("PROT", "-21,0,180").split(",")))
phone.matrix_world = GM @ Matrix.Translation(PLOC) @ Euler([R(a) for a in PR]).to_matrix().to_4x4()
follow(phone, girl, os.environ.get("PBONE", "mixamorig:LeftHand"), PREF)
vis(phone, [(1, SH["s3"] - 1), (SH["s11"], END)])

# ================= RENTGEN: teri materiali + bosh suyagi =================
xr_vals = []                                # har bir materialdagi rentgen omili (bitta qiymat bilan boshqariladi)
for o in gmesh:
    for m in o.data.materials:
        if not m or not m.use_nodes or m.get("xr"): continue
        m["xr"] = 1
        N = m.node_tree.nodes; L = m.node_tree.links
        out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
        src = out.inputs["Surface"].links[0].from_socket
        em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.6, 1.0, 1); em.inputs["Strength"].default_value = 2.5
        tr = N.new("ShaderNodeBsdfTransparent"); lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
        pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.6
        L.new(lw.outputs["Facing"], pw.inputs[0])
        mx1 = N.new("ShaderNodeMixShader"); L.new(pw.outputs[0], mx1.inputs["Fac"]); L.new(tr.outputs[0], mx1.inputs[1]); L.new(em.outputs[0], mx1.inputs[2])
        v = N.new("ShaderNodeValue"); v.outputs[0].default_value = 0.0
        mx2 = N.new("ShaderNodeMixShader"); L.new(v.outputs[0], mx2.inputs["Fac"]); L.new(src, mx2.inputs[1]); L.new(mx1.outputs[0], mx2.inputs[2])
        L.new(mx2.outputs[0], out.inputs["Surface"])
        xr_vals.append(v.outputs[0])
for s in xr_vals:
    for f, val in ((1, 0), (XR0, 0), (XR1, 1), (XR_END, 1), (XR_END + 1, 0)): keyval(s, f, val)

# bosh suyagi
sk_root, skp = import_gltf(BK + "49c13194_u.glb", (0, 0, 0), 0, 1.0, name="skull")
for o in list(skp):
    if o.type == "MESH" and o.name.startswith("Text"): bpy.data.objects.remove(o, do_unlink=True)
skp = [o for o in sk_root.children_recursive if o.type == "MESH"]
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in skp for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
SKS = float(os.environ.get("SKS", 0.215)) / (hi.z - lo.z)
SKC = Vector(tuple(map(float, os.environ.get("SKC", "0,-0.012,1.585").split(","))))
SKR = float(os.environ.get("SKR", 0))
ctr = (lo + hi) / 2
SKM = mat("skullbase", (1, 1, 1))
SKM.node_tree.nodes.clear()
N = SKM.node_tree.nodes; L = SKM.node_tree.links
out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent")
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
mxc = N.new("ShaderNodeMix"); mxc.data_type = "RGBA"; mxc.inputs[6].default_value = (0.85, 0.92, 1.0, 1); mxc.inputs[7].default_value = (1.0, 0.45, 0.08, 1)
orange = N.new("ShaderNodeValue"); L.new(orange.outputs[0], mxc.inputs["Factor"])
strength = N.new("ShaderNodeValue")
add = N.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; L.new(lw.outputs["Facing"], add.inputs[0]); add.inputs[1].default_value = 1.4; add.inputs[2].default_value = 0.35
mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(add.outputs[0], mul.inputs[0]); L.new(strength.outputs[0], mul.inputs[1])
L.new(mxc.outputs[2], em.inputs["Color"]); L.new(mul.outputs[0], em.inputs["Strength"])
mxs = N.new("ShaderNodeMixShader"); mxs.inputs["Fac"].default_value = 0.88
L.new(tr.outputs[0], mxs.inputs[1]); L.new(em.outputs[0], mxs.inputs[2]); L.new(mxs.outputs[0], out.inputs[0])
for o in skp: o.data.materials.clear(); o.data.materials.append(SKM)
sk = empty("skull_fit"); sk.parent = fx
sk_root.parent = sk
sk_root.matrix_basis = Matrix.Translation(-ctr)
sk.matrix_basis = GM @ Matrix.Translation(SKC) @ Matrix.Rotation(R(SKR), 4, "Z") @ Matrix.Scale(SKS, 4)
vis(sk, [(XR0, XR_END)])
keyval(strength.outputs[0], 1, 0.0); keyval(strength.outputs[0], XR0, 0.0); keyval(strength.outputs[0], XR1 + 6, 1.4)
keyval(orange.outputs[0], 1, 0.0); keyval(orange.outputs[0], SH["s7"] + 10, 0.0)
# suyak tebranishi: to'q sariq pulsatsiya (s7-s9), s9 da kuchli
f = SH["s7"] + 12
while f < XR_END:
    big = f >= SH["s9"]
    keyval(orange.outputs[0], f, 1.0 if big else 0.75); keyval(strength.outputs[0], f, 3.4 if big else 2.4)
    keyval(orange.outputs[0], f + (9 if big else 4), 0.35); keyval(strength.outputs[0], f + (9 if big else 4), 1.6)
    f += 18 if big else 8

# ================= TOVUSH: halqalar va impulslar =================
BLUE = glow_mat("soundring", (0.3, 0.7, 1.0), 9.0, alpha=0.85)
ORNG = glow_mat("bonepulse", (1.0, 0.45, 0.06), 16.0)
SHELL = glow_mat("bassshell", (1.0, 0.42, 0.05), 3.0, alpha=0.55, rim=True)

def polyline(pts, t):
    seg = [(pts[i+1] - pts[i]).length for i in range(len(pts) - 1)]; tot = sum(seg); d = t * tot
    for i, s in enumerate(seg):
        if d <= s or i == len(seg) - 1:
            u = min(1.0, d / s if s else 0); p = pts[i].lerp(pts[i+1], u); return p, (pts[i+1] - pts[i]).normalized()
        d -= s

def ring_stream(name, pts, f0, f1, every, travel, r0, r1, parent=None, matl=BLUE, minor=0.08):
    pts = [Vector(p) for p in pts]; f = f0; i = 0
    while f + travel <= f1:
        o = torus(f"{name}{i}", matl, minor); o.parent = parent
        for k in range(0, travel + 1, 3):
            t = k / travel; p, dvec = polyline(pts, t)
            o.location = p; o.rotation_euler = dvec.to_track_quat("Z", "Y").to_euler()
            r = r0 + (r1 - r0) * t; fade = min(1.0, 4 * t, 4 * (1 - t) + 0.25)
            o.scale = (r * fade, r * fade, r * fade)
            o.keyframe_insert("location", frame=f + k); o.keyframe_insert("rotation_euler", frame=f + k); o.keyframe_insert("scale", frame=f + k)
        vis(o, [(f, f + travel)]); f += every; i += 1

def pulse_stream(name, pts, f0, f1, every, travel, r, parent):
    pts = [Vector(p) for p in pts]; f = f0; i = 0
    while f + travel <= f1:
        o = sphere(f"{name}{i}", r, (0, 0, 0), ORNG, sub=2); o.parent = parent
        for k in range(0, travel + 1, 2):
            p, _ = polyline(pts, k / travel); o.location = p; o.keyframe_insert("location", frame=f + k)
        vis(o, [(f, f + travel)]); f += every; i += 1

def W(x, y, z):            # dam holatdagi Megan koordinatasi -> fx_head ichidagi mahalliy (dunyo) koordinata
    return tuple(ML(x, y, z))

# s3-s4: Megan og'zidan Kate va Remy quloqlariga (dunyo koordinatasi)
kh = bone_world(kate, HEAD, 300).translation + Vector((0, 0, 0.08)); rh = bone_world(remy, HEAD, 300).translation + Vector((0, 0, 0.08))
mouth = bone_world(girl, HEAD, 300) @ Vector((0, 0, 0))
mouth = Vector(ML(0, -0.13, 1.53))
ring_stream("ringK", [mouth, mouth.lerp(kh, 0.5) + Vector((0, 0, 0.12)), kh], SH["s3"] + 6, SH["s5"] - 1, 9, 30, 0.04, 0.09)
ring_stream("ringR", [mouth, mouth.lerp(rh, 0.5) + Vector((0, 0, 0.1)), rh], SH["s3"] + 10, SH["s5"] - 1, 9, 30, 0.04, 0.09)

# s6: havo yo'li — og'izdan tashqariga, aylanib chap quloq teshigiga (bosh suyagiga ergashadi)
EAR = (0.078, 0.004, 1.585)
air = [W(0, -0.12, 1.525), W(0.05, -0.24, 1.54), W(0.17, -0.16, 1.57), W(0.18, -0.02, 1.585), W(*EAR)]
ring_stream("air", air, SH["s5"] + 70, SH["s7"] + 20, 7, 34, 0.012, 0.03, parent=fx, minor=0.12)
drum = cyl("eardrum", 0.011, 0.002, W(0.066, 0.004, 1.585), glow_mat("drum", (0.4, 0.8, 1.0), 6.0), rot=(0, 90, GROT), verts=24)
drum.parent = fx; vis(drum, [(XR0, XR_END)])
for f in range(SH["s6"] + 20, XR_END, 3):
    key(drum, f, scale=(1, 1, 1)); key(drum, f + 1, scale=(1.25, 1.25, 1.25))

# s7-s9: suyak yo'li — ovoz paychalari -> jag' -> bosh suyagi -> ichki quloq
vc = sphere("vocalcords", 0.016, W(0, -0.035, 1.43), ORNG, sub=2); vc.parent = fx; vc.scale = (1.4, 0.7, 0.5)
vis(vc, [(SH["s7"], XR_END)])
for f in range(SH["s7"], XR_END, 4):
    key(vc, f, scale=(1.4, 0.7, 0.5)); key(vc, f + 2, scale=(1.8, 0.9, 0.7))
bone_paths = [
    [W(0, -0.035, 1.43), W(0.03, -0.07, 1.47), W(0.05, -0.04, 1.5), W(0.055, -0.005, 1.545), W(0.045, 0.004, 1.585)],
    [W(0, -0.035, 1.43), W(-0.03, -0.07, 1.47), W(-0.05, -0.04, 1.5), W(-0.055, -0.005, 1.545), W(-0.045, 0.004, 1.585)],
    [W(0, -0.035, 1.43), W(0, -0.06, 1.5), W(0.03, -0.075, 1.58), W(0.04, -0.03, 1.66), W(0.045, 0.004, 1.585)],
]
for j, pth in enumerate(bone_paths):
    pulse_stream(f"pulse{j}_", pth, SH["s7"] + 6 + 2*j, XR_END, 5, 26, 0.0055, fx)
# s9: past chastota — jag'dan katta, sekin kengayuvchi sferalar
f = SH["s9"]; i = 0
while f + 40 <= XR_END:
    s_ = sphere(f"bass{i}", 1.0, W(0.0, -0.03, 1.5), SHELL, sub=3); s_.parent = fx
    key(s_, f, scale=0.02); key(s_, f + 40, scale=0.11); vis(s_, [(f, f + 40)]); f += 14; i += 1

# rentgen fon (qorong'i ko'k sfera) — xonani yashiradi, render arzonlashadi
BGM = bpy.data.materials.new("xray_bg"); BGM.use_nodes = True
bg = sphere("xray_bg", 2.2, tuple(ML(0, 0, 1.55)), BGM, sub=4)
N = BGM.node_tree.nodes; L = BGM.node_tree.links; N.clear()
o_ = N.new("ShaderNodeOutputMaterial"); e_ = N.new("ShaderNodeEmission"); t_ = N.new("ShaderNodeBsdfTransparent"); m_ = N.new("ShaderNodeMixShader")
gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], gr.inputs[0])
mc_ = N.new("ShaderNodeMix"); mc_.data_type = "RGBA"; mc_.inputs[6].default_value = (0.002, 0.006, 0.02, 1); mc_.inputs[7].default_value = (0.01, 0.03, 0.08, 1)
L.new(gr.outputs["Fac"], mc_.inputs["Factor"]); L.new(mc_.outputs[2], e_.inputs["Color"]); e_.inputs["Strength"].default_value = 1.0
L.new(t_.outputs[0], m_.inputs[1]); L.new(e_.outputs[0], m_.inputs[2]); L.new(m_.outputs[0], o_.inputs[0])
bg.visible_shadow = False
for f, v in ((1, 0), (XR0, 0), (XR1, 1)): keyval(m_.inputs["Fac"], f, v)
vis(bg, [(XR0, XR_END)])
# rentgen paytida xona va yorug'lik ishlamaydi
for o in room: vis(o, [(1, XR1 + 2), (XR_END + 1, END)])

# ================= KAMERALAR =================
cams = []
def camera(name, f0, f1, p0, p1, target, lens, fstop=None, ease="QUART", lens1=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = 0.01
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c)
    t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop: d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = target
    key(c, f0, loc=tuple(p0)); key(c, f1, loc=tuple(p1))
    if lens1:
        d.lens = lens; d.keyframe_insert("lens", frame=f0); d.lens = lens1; d.keyframe_insert("lens", frame=f1)
    for fc in all_fcurves(c):
        for k in fc.keyframe_points: k.interpolation = ease; k.easing = "EASE_OUT"
        n = fc.modifiers.new("NOISE"); n.scale = 22; n.strength = 0.012; n.phase = random.uniform(0, 100)
    cams.append((f0, c)); return c

def tgt(name, x, y, z, head=True):
    return empty(name, W(x, y, z), fx if head else None)

face = tgt("t_face", 0, -0.05, 1.6)
camera("c01_phone", SH["s1"], SH["s2"] - 1, ML(-0.32, -0.2, 1.48), ML(-0.12, -0.2, 1.36), phone, 35, 2.0, "EXPO")
camera("c02_cringe", SH["s2"], SH["s3"] - 1, ML(0.32, -0.72, 1.55), ML(-0.12, -0.62, 1.6), face, 55, 2.0, "SINE")
t3 = empty("t3", (0.4, 3.3, 0.9))
camera("c03_wide", SH["s3"], SH["s4"] - 1, (2.75, 1.75, 0.3), (2.55, 1.25, 0.45), t3, 16, 5.6, "SINE")
gh = Vector(ML(0, -0.05, 1.6)); dd = (kh - gh); dd.z = 0; dd.normalize(); side = Vector((-dd.y, dd.x, 0))
camera("c04_ots", SH["s4"], SH["s5"] - 1, kh + dd*0.55 + side*0.22 + Vector((0, 0, 0.05)), kh + dd*0.48 + side*0.2 + Vector((0, 0, 0.06)), face, 40, 2.8, "SINE")
ear_t = tgt("t_ear", 0.04, -0.02, 1.57)
camera("c05_profile", SH["s5"], SH["s6"] - 1, ML(1.0, -0.15, 1.62), ML(0.42, -0.05, 1.6), ear_t, 45, 4.0, "QUART")
ear2 = tgt("t_ear2", 0.08, -0.08, 1.56)
camera("c06_ear", SH["s6"], SH["s7"] - 1, ML(0.36, -0.36, 1.64), ML(0.26, -0.2, 1.6), ear2, 40, 5.6, "SINE")
jaw = tgt("t_jaw", 0.02, -0.04, 1.5)
camera("c07_jaw", SH["s7"], SH["s8"] - 1, ML(0.16, -0.42, 1.3), ML(0.24, -0.34, 1.42), jaw, 30, 5.6, "SINE")
skc = tgt("t_skull", 0.02, -0.01, 1.56)
camera("c08_orbit", SH["s8"], SH["s9"] - 1, ML(0.12, -0.45, 1.62), ML(0.45, 0.02, 1.62), skc, 35, 5.6, "SINE")
camera("c09_bass", SH["s9"], SH["s10"] - 1, ML(-0.3, -0.36, 1.5), ML(-0.18, -0.24, 1.52), jaw, 30, 5.6, "QUART")
camera("c10_warm", SH["s10"], SH["s11"] - 1, ML(-0.45, -1.0, 1.42), ML(0.3, -0.95, 1.52), face, 42, 2.2, "SINE")
camera("c11_phone", SH["s11"], SH["s12"] - 1, ML(0.2, 0.0, 1.55), ML(0.06, -0.12, 1.37), phone, 35, 2.0, "EXPO")
camera("c12_push", SH["s12"], END, ML(0.05, -1.3, 1.55), ML(0.0, -0.58, 1.58), face, 50, 2.8, "CUBIC")
for f, c in cams: sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = cams[0][1]

# ================= YORUG'LIK =================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; env = N.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(120))
w.node_tree.links.new(tc.outputs["Generated"], mp.inputs[0]); w.node_tree.links.new(mp.outputs[0], env.inputs[0])
w.node_tree.links.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 2.5; sun.data.angle = R(2); sun.data.color = (1.0, 0.93, 0.82); sun.rotation_euler = (R(-60), 0, R(15))
def area(name, loc, target, energy, size, col=(1, 0.9, 0.78)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.energy = energy; l.data.size = size; l.data.color = col; l.location = loc
    t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l
area("ceiling_light", (0.3, 2.8, 2.6), t3, 90, 1.4)
area("window_key", (0.1, 4.7, 1.8), face, 220, 1.6, (0.92, 0.96, 1.0))
area("face_fill", tuple(ML(0.7, -1.1, 1.9)), face, 45, 0.9, (1.0, 0.85, 0.7))
rim = area("rim", tuple(ML(-0.6, 0.9, 2.0)), face, 60, 0.6, (0.8, 0.9, 1.0))
warm = area("warm", tuple(ML(0.3, -0.9, 1.3)), face, 0, 1.0, (1.0, 0.6, 0.25))
for f, e in ((1, 0), (SH["s10"] - 1, 0), (SH["s10"], 110), (SH["s11"] - 1, 110), (SH["s11"], 0)):
    warm.data.energy = e; warm.data.keyframe_insert("energy", frame=f)
for f, e in ((1, 1.0), (SH["s10"] - 1, 1.0), (SH["s10"], 0.6), (SH["s11"] - 1, 0.6), (SH["s11"], 1.0)):
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = e
    sc.world.node_tree.nodes["Background"].inputs[1].keyframe_insert("default_value", frame=f)
for o in bpy.data.objects:                   # yorug'lik keyframe'lari silliq emas, sakrab o'tsin
    if o.type == "LIGHT": set_interp(o.data, "CONSTANT")
set_interp(sc.world.node_tree, "CONSTANT")

# ================= RENDER =================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 14)); sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPOSURE", -0.3))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True    # to'xtab qolsa, qayta ishga tushirib davom ettirish mumkin

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
