# Telefon fonari — Zack D. Films uslubida 35 s video (848 kadr, 24 fps, 9:16).
# Yigit telefonini topolmaydi, do'stiga qo'ng'iroq qilib "telefonim yo'q!" deydi; aslida uni o'sha telefonning fonari bilan qidirgan.
# Asos: zack_test/scene3.py + mixchar.py, yordamchilar zack_test/ishqalash/ishqalash.py dan.
# Assetlar: zack_test/tools/get_fonar.sh ; ekran rasmlari: python3 -I zack_test/fonar/screens.py /tmp/claude-0/assets/screens
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/fonar/fonar.py --render
# Sinov:  FRAMES=30,100,180,400,820 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
SCR = os.environ.get("SCR_DIR", "/tmp/claude-0/assets/screens/")
random.seed(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 848
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md) ----------------
SHOTS = [(1, "hook"), (45, "look"), (89, "pillow"), (123, "blanket"), (154, "fridge"), (202, "wide"), (246, "call"),
         (309, "answer"), (338, "yell"), (424, "silent"), (498, "ask"), (561, "glance"), (633, "face"), (666, "hangup"),
         (691, "search"), (777, "reveal")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
FRIENDN = ("answer", "silent", "ask")
STUDION = tuple(n for f, n in SHOTS if n not in FRIENDN)
F_END_CALL = 676          # ekran "Qo'ng'iroq tugadi"
F_SCREEN_OFF = 687

# ---------------- yordamchilar (ishqalash.py dan) ----------------
empty = P.empty
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale if isinstance(scale, (tuple, list)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)
def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return mc._fcurves(ad.action)
def interp(idb, mode="LINEAR", path=None):
    for fc in fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode
def ckey(idb, path=None): interp(idb, "CONSTANT", path)
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
def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    return m
def noise_mat(name, col, col2, rough=0.6, scale=20.0, bump=0.1, coat=0.0):
    m = mat(name, col, rough, coat=coat); N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    t = N.new("ShaderNodeTexNoise"); t.inputs["Scale"].default_value = scale; t.inputs["Detail"].default_value = 6
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], t.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(t.outputs["Fac"], mx.inputs["Factor"])
    mx.inputs[6].default_value = (*col, 1); mx.inputs[7].default_value = (*col2, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    if bump:
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        L.new(t.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
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
def smooth(o):
    for p in o.data.polygons: p.use_smooth = True
def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3; smooth(o)
    if parent: o.parent = parent
    return o
def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o)
    if parent: o.parent = parent
    return o
def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m); smooth(o)
    if parent: o.parent = parent
    return o
def import_gltf(path, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler.z = R(rot_z); root.scale = scale if isinstance(scale, tuple) else (scale,) * 3
    return root, new
def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value
def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e
def V(*a): return Vector(a)
def ease(t): return t * t * (3 - 2 * t)
def wpos(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()

# ---------------- materiallar ----------------
M = dict(
    trim=mat("trim", (0.85, 0.85, 0.82), 0.45),
    bedframe=noise_mat("bedframe", (0.33, 0.22, 0.14), (0.24, 0.15, 0.09), 0.45, scale=8, bump=0.05, coat=0.2),
    mattress=noise_mat("mattress", (0.85, 0.85, 0.83), (0.78, 0.78, 0.76), 0.85, scale=60, bump=0.05),
    sheet=noise_mat("sheet", (0.72, 0.78, 0.86), (0.62, 0.68, 0.78), 0.9, scale=40, bump=0.15),
    blanket=noise_mat("blanket", (0.16, 0.24, 0.42), (0.1, 0.16, 0.3), 0.95, scale=90, bump=0.25),
    pillow=noise_mat("pillow", (0.88, 0.88, 0.86), (0.8, 0.8, 0.78), 0.9, scale=40, bump=0.15),
    curtain=noise_mat("curtain", (0.32, 0.36, 0.42), (0.25, 0.28, 0.34), 0.95, scale=12, bump=0.2),
    winglow=mat("winglow", (0.6, 0.75, 1.0), 0.5, emit=3.5),
    fridge=mat("fridge", (0.86, 0.87, 0.88), 0.22, coat=0.6),
    fridge_in=mat("fridge_in", (0.95, 0.96, 0.97), 0.35, emit=0.0),
    steel=mat("steel", (0.7, 0.7, 0.72), 0.2, metal=1.0),
    shelfglass=mat("shelfglass", (0.85, 0.92, 0.95), 0.05, trans=0.9),
    counter=noise_mat("counter", (0.12, 0.12, 0.13), (0.18, 0.18, 0.19), 0.3, scale=120, bump=0.02, coat=0.4),
    cabinet=mat("cabinet", (0.78, 0.74, 0.66), 0.4, coat=0.2),
    rug=noise_mat("rug", (0.45, 0.3, 0.22), (0.6, 0.48, 0.35), 0.95, scale=30, bump=0.3),
    lampshade=mat("lampshade", (1.0, 0.86, 0.65), 0.6),
    black=mat("black", (0.02, 0.02, 0.02), 0.4),
    poster=noise_mat("poster", (0.75, 0.25, 0.15), (0.15, 0.25, 0.55), 0.5, scale=3, bump=0.0),
    milk=mat("milk", (0.92, 0.92, 0.9), 0.4), juice=mat("juice", (0.95, 0.5, 0.05), 0.15, trans=0.6),
    bottle=mat("bottleg", (0.2, 0.55, 0.25), 0.05, trans=0.8), apple=mat("apple", (0.6, 0.05, 0.04), 0.35, coat=0.5),
    egg=mat("egg", (0.92, 0.85, 0.72), 0.5), jar=mat("jar", (0.55, 0.15, 0.1), 0.2, trans=0.5),
    cheese=mat("cheese", (0.95, 0.75, 0.25), 0.5), box_r=mat("box_r", (0.75, 0.12, 0.1), 0.5),
)
floor_m = pbr("ph_floor", "laminate_floor_02", 0.5)
wall_m = pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.82, 0.86, 0.9))
wall2_m = pbr("ph_wall2", "painted_plaster_wall", 0.5, tint=(0.98, 0.9, 0.78))

# ======================================================================
# 1) STUDIYA-KVARTIRA (x [-3,3], y [-2.5,2.5]), tong, pardalar yopiq
# ======================================================================
H_ = 2.7
box("st_floor", (6, 5, 0.06), (0, 0, -0.03), floor_m)
box("st_ceil", (6, 5, 0.06), (0, 0, H_ + 0.03), M["trim"])
box("st_wall_b", (6, 0.12, H_), (0, 2.56, H_ / 2), wall_m)
box("st_wall_f", (6, 0.12, H_), (0, -2.56, H_ / 2), wall_m)
box("st_wall_r", (0.12, 5, H_), (3.06, 0, H_ / 2), wall_m)
# chap devor: deraza teshigi (y -0.3..1.3, z 0.8..2.3)
box("st_wall_l1", (0.12, 2.2, H_), (-3.06, -1.4, H_ / 2), wall_m)
box("st_wall_l2", (0.12, 1.2, H_), (-3.06, 1.9, H_ / 2), wall_m)
box("st_wall_l3", (0.12, 1.6, 0.8), (-3.06, 0.5, 0.4), wall_m)
box("st_wall_l4", (0.12, 1.6, 0.4), (-3.06, 0.5, 2.5), wall_m)
box("st_winglow", (0.02, 1.6, 1.5), (-3.2, 0.5, 1.55), M["winglow"])
for i, y in enumerate((0.05, 0.95)):                     # yopiq pardalar (orasida tirqish)
    c = box(f"st_curtain{i}", (0.05, 0.82, 2.35), (-2.9, y + (0.02 if i else -0.02), 1.3), M["curtain"])
    w = c.modifiers.new("wave", "WAVE"); w.height = 0.035; w.width = 0.12; w.narrowness = 1.0; w.use_x = False; w.use_normal = False
    w.time_offset = 0; w.speed = 0; w.start_position_y = y
box("st_crod", (0.03, 1.9, 0.03), (-2.86, 0.5, 2.5), M["steel"])
for x, y, l, a in ((0, 2.48, 6, 0), (0, -2.48, 6, 0), (2.98, 0, 5, 90), (-2.98, 0, 5, 90)):
    box("st_baseboard", (l, 0.025, 0.1), (x, y, 0.05), M["trim"], rot=(0, 0, a))
# karavot: x [-2.3,-0.9], y [0.4,2.45], matras usti 0.58
BX0, BX1, BY0, BY1, MT = -2.3, -0.9, 0.4, 2.45, 0.58
BCX = (BX0 + BX1) / 2
for x in (BX0 + 0.06, BX1 - 0.06):
    for y in (BY0 + 0.06, BY1 - 0.06): box("bed_leg", (0.07, 0.07, 0.28), (x, y, 0.14), M["bedframe"])
box("bed_base", (BX1 - BX0, BY1 - BY0, 0.12), (BCX, (BY0 + BY1) / 2, 0.33), M["bedframe"], bevel=0.01)
box("bed_head", (BX1 - BX0 + 0.06, 0.07, 0.75), (BCX, BY1 + 0.03, 0.72), M["bedframe"], bevel=0.015)
box("bed_mattress", (BX1 - BX0 - 0.04, BY1 - BY0 - 0.04, 0.2), (BCX, (BY0 + BY1) / 2, 0.48), M["sheet"], bevel=0.05)
# yostiq (yumshoq) — ob'ekt markazi o'zida
bpy.ops.mesh.primitive_cube_add(size=1); pil = bpy.context.object; pil.name = "pillow"
pil.scale = (0.62, 0.4, 0.14); bpy.ops.object.transform_apply(scale=True)
sd = pil.modifiers.new("sub", "SUBSURF"); sd.levels = 3; sd.render_levels = 3
cast = pil.modifiers.new("cast", "CAST"); cast.factor = 0.35
pil.data.materials.append(M["pillow"]); smooth(pil)
PIL0 = V(BCX, 2.25, MT + 0.07)
pil.location = PIL0
# ko'rpa: yaqin chekkasida (x = BX1) markaz; tana ustida do'nglik
def make_blanket():
    me = bpy.data.meshes.new("blanket"); bm = bmesh.new()
    nx, ny = 44, 36; X0_, X1_ = -1.62, 0.12; Y0_, Y1_ = -0.78, 0.6
    grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = X0_ + (X1_ - X0_) * i / nx; y = Y0_ + (Y1_ - Y0_) * j / ny
            wx = BX1 + x                                             # dunyo x
            z = 0.02
            hump = 0.2 * math.exp(-((wx - BCX) / 0.26) ** 2) * (1.0 if y < 0.35 else max(0.0, 1 - (y - 0.35) / 0.25))
            hump *= min(1.0, (y - Y0_) / 0.3 + 0.35)
            hump += 0.32 * math.exp(-((wx - BCX) / 0.3) ** 2) * max(0.0, min(1.0, (-0.1 - y) / 0.3))   # oyoq uchlari
            z += hump
            if wx > BX1 - 0.02: z -= min(0.32, (wx - (BX1 - 0.02)) * 3.0)          # chekkadan osilib tushadi
            if wx < BX0 + 0.02: z -= min(0.32, ((BX0 + 0.02) - wx) * 3.0)
            if y < Y0_ + 0.05: z -= 0.04
            z += 0.012 * math.sin(wx * 23 + y * 7) * math.sin(y * 17)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("blanket", me); sc.collection.objects.link(o)
    s = o.modifiers.new("solid", "SOLIDIFY"); s.thickness = 0.025; s.offset = 0
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = 1; sd.render_levels = 1
    me.materials.append(M["blanket"]); smooth(o); return o
bln = make_blanket()
BLN0 = V(BX1, 1.17, MT + 0.1)
bln.location = BLN0
# tungi tumba + soat (Poly Haven)
import_gltf(PH + "ClassicNightstand_01/ClassicNightstand_01.gltf", (-2.66, 2.18, 0), 0, 1.0)
import_gltf(PH + "alarm_clock_01/alarm_clock_01.gltf", (-2.66, 2.1, 0.6), -20, 1.0)
# oshxona burchagi: o'ng devor bo'ylab peshtaxta va javonlar
box("k_counter", (0.62, 2.2, 0.86), (2.73, 0.5, 0.43), M["cabinet"], bevel=0.005)
box("k_top", (0.66, 2.24, 0.04), (2.71, 0.5, 0.88), M["counter"], bevel=0.004)
for y in (-0.05, 0.5, 1.05):
    box("k_handle", (0.02, 0.18, 0.015), (2.41, y, 0.75), M["steel"])
box("k_upper", (0.36, 2.2, 0.7), (2.86, 0.5, 1.85), M["cabinet"], bevel=0.005)
box("k_kettle", (0.18, 0.18, 0.24), (2.7, 1.2, 1.02), M["steel"], bevel=0.04)
cyl("k_mug", 0.04, 0.1, (2.62, 0.2, 0.95), M["apple"])
# muzlatkich: oldi x = 2.3, y [-1.6,-0.9], balandlik 1.85; eshik ilmog'i y = -0.9 tomonda
FX0, FY0, FY1, FH = 2.3, -1.62, -0.88, 1.85
FD = 0.7
FCY = (FY0 + FY1) / 2
fw = FY1 - FY0
box("fr_back", (0.04, fw, FH), (FX0 + FD - 0.02, FCY, FH / 2), M["fridge"])
box("fr_top", (FD, fw, 0.04), (FX0 + FD / 2, FCY, FH - 0.02), M["fridge"])
box("fr_bot", (FD, fw, 0.08), (FX0 + FD / 2, FCY, 0.04), M["fridge"])
for y in (FY0 + 0.02, FY1 - 0.02):
    box("fr_side", (FD, 0.04, FH), (FX0 + FD / 2, y, FH / 2), M["fridge"])
box("fr_inner", (0.02, fw - 0.08, FH - 0.12), (FX0 + FD - 0.05, FCY, FH / 2), M["fridge_in"])
box("fr_mid", (FD - 0.04, fw - 0.08, 0.04), (FX0 + FD / 2, FCY, 0.62), M["fridge"])
for z in (0.98, 1.3, 1.62):
    box("fr_shelf", (FD - 0.1, fw - 0.08, 0.008), (FX0 + FD / 2 + 0.02, FCY, z), M["shelfglass"])
# ichidagi narsalar
cyl("fr_milk", 0.045, 0.24, (FX0 + 0.32, FCY + 0.2, 0.98 + 0.12), M["milk"])
cyl("fr_juice", 0.04, 0.26, (FX0 + 0.4, FCY - 0.22, 0.98 + 0.13), M["juice"])
cyl("fr_bottle", 0.035, 0.28, (FX0 + 0.45, FCY + 0.08, 1.3 + 0.14), M["bottle"])
cyl("fr_jar", 0.05, 0.12, (FX0 + 0.3, FCY - 0.15, 1.3 + 0.06), M["jar"])
for i in range(4): sphere(f"fr_apple{i}", 0.04, (FX0 + 0.25 + 0.07 * (i % 2), FCY + 0.1 - 0.08 * i, 1.62 + 0.04), M["apple"])
for i in range(6): sphere(f"fr_egg{i}", 0.022, (FX0 + 0.42 + 0.05 * (i % 2), FCY - 0.25 + 0.05 * (i // 2), 1.62 + 0.03), M["egg"], scale=(1, 1, 1.3))
box("fr_cheese", (0.12, 0.08, 0.06), (FX0 + 0.35, FCY + 0.05, 0.98 + 0.03), M["cheese"], bevel=0.005)
box("fr_box", (0.18, 0.12, 0.1), (FX0 + 0.45, FCY + 0.22, 0.62 + 0.07), M["box_r"], bevel=0.005)
hinge = empty("fr_hinge", (FX0 - 0.02, FY1, 0))
box("fr_door", (0.05, fw, FH - 0.02), (0, -fw / 2, FH / 2), M["fridge"], parent=hinge, bevel=0.012)
box("fr_door_in", (0.02, fw - 0.1, FH - 0.2), (0.035, -fw / 2, FH / 2), M["fridge_in"], parent=hinge)
for z in (0.75, 1.15, 1.5):
    box("fr_door_tray", (0.08, fw - 0.12, 0.05), (0.08, -fw / 2, z), M["fridge_in"], parent=hinge)
cyl("fr_door_bottle", 0.03, 0.24, (0.08, -fw / 2 + 0.15, 1.15 + 0.12), M["bottle"], parent=hinge)
cyl("fr_door_bottle2", 0.03, 0.2, (0.08, -fw / 2 - 0.05, 0.75 + 0.1), M["juice"], parent=hinge)
box("fr_handle", (0.03, 0.025, 0.55), (-0.05, -fw + 0.06, 1.15), M["steel"], parent=hinge, bevel=0.008)
# javon, kitoblar, poster, lampa, gilam
import_gltf(PH + "Shelf_01/Shelf_01.gltf", (0.9, 2.3, 0), 0, 1.0)
import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (0.75, 2.3, 1.03), 0, 1.0)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (2.55, 2.05, 0), 30, 1.0)
box("st_poster_f", (0.62, 0.02, 0.86), (-0.1, 2.49, 1.6), M["black"])
box("st_poster", (0.56, 0.02, 0.8), (-0.1, 2.48, 1.6), M["poster"])
box("st_rug", (2.0, 1.4, 0.01), (0.3, 0.0, 0.005), M["rug"])
cyl("st_pend_cord", 0.005, 0.5, (0.3, 0.1, H_ - 0.25), M["black"])
cyl("st_pend", 0.16, 0.18, (0.3, 0.1, H_ - 0.55), M["lampshade"])
# polda tartibsizlik: kiyim, kitob
box("st_tshirt", (0.4, 0.35, 0.02), (1.3, 1.6, 0.01), noise_mat("tsh", (0.2, 0.2, 0.22), (0.25, 0.25, 0.27), 0.95, 50, 0.3), rot=(0, 0, 25), bevel=0.01)
box("st_book", (0.16, 0.22, 0.03), (-0.4, -0.9, 0.015), M["box_r"], rot=(0, 0, -15))

# ======================================================================
# 2) DO'STNING MEHMONXONASI (FX = 20), yorug' kunduz
# ======================================================================
FRX = 20.0
def FP(x, y, z=0.0): return (FRX + x, y, z)
box("fr_floor", (6, 5, 0.06), FP(0, 0, -0.03), floor_m)
box("fr_ceil", (6, 5, 0.06), FP(0, 0, H_ + 0.03), M["trim"])
box("fr_wall_l", (0.12, 5, H_), FP(-3.06, 0, H_ / 2), wall2_m)
box("fr_wall_r", (0.12, 5, H_), FP(3.06, 0, H_ / 2), wall2_m)
box("fr_wall_f", (6, 0.12, H_), FP(0, -2.56, H_ / 2), wall2_m)
# orqa devorda katta deraza (x 0.4..2.4, z 0.7..2.3)
box("fr_wb1", (3.4, 0.12, H_), FP(-1.3, 2.56, H_ / 2), wall2_m)
box("fr_wb2", (0.6, 0.12, H_), FP(2.7, 2.56, H_ / 2), wall2_m)
box("fr_wb3", (2.0, 0.12, 0.7), FP(1.4, 2.56, 0.35), wall2_m)
box("fr_wb4", (2.0, 0.12, 0.4), FP(1.4, 2.56, 2.5), wall2_m)
day = mat("dayglow", (0.85, 0.92, 1.0), 0.5, emit=6.0)
box("fr_daylight", (2.2, 0.02, 1.8), FP(1.4, 2.8, 1.5), day)
for x in (0.42, 1.4, 2.38): box("fr_wframe", (0.05, 0.1, 1.6), FP(x, 2.56, 1.5), M["trim"])
box("fr_wframe_h", (2.0, 0.1, 0.05), FP(1.4, 2.56, 1.5), M["trim"])
for i, x in enumerate((0.15, 2.65)):
    c = box(f"fr_curt{i}", (0.42, 0.05, 2.35), FP(x, 2.42, 1.3), noise_mat(f"fcur{i}", (0.85, 0.82, 0.72), (0.78, 0.75, 0.66), 0.9, 12, 0.2))
    w = c.modifiers.new("wave", "WAVE"); w.height = 0.03; w.width = 0.1; w.narrowness = 1.0; w.use_y = False; w.use_normal = False; w.speed = 0
import_gltf(PH + "Sofa_01/Sofa_01.gltf", FP(-1.4, 1.85, 0), 0, 1.0)
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", FP(-1.4, 0.85, 0), 0, 1.0)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", FP(-2.55, 2.1, 0), 10, 1.25)
import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", FP(-1.4, 2.47, 1.5), 0, 1.3)
import_gltf(PH + "Shelf_01/Shelf_01.gltf", FP(2.95, -0.6, 0), -90, 1.0)
import_gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", FP(2.85, -0.4, 1.03), -90, 1.0)
box("fr_rug", (2.6, 1.8, 0.01), FP(-1.0, 0.8, 0.005), noise_mat("frug", (0.7, 0.62, 0.5), (0.6, 0.5, 0.4), 0.95, 25, 0.3))

# ======================================================================
# 3) QAHRAMONLAR: Bryce (yigit), Brian (do'sti)
# ======================================================================
def soften(meshes, rough=0.55):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.3
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = rough
                    n.inputs["Coat Weight"].default_value = 0.0
broot, bry, bmeshes = mc.load_character("bry", "Bryce.fbx"); sc.render.fps = 24
froot, fri, fmeshes = mc.load_character("fri", "Brian.fbx"); sc.render.fps = 24
soften(bmeshes); soften(fmeshes)
for o in bmeshes:
    if "Sneakers" in o.name: vis(o, [(S["look"][0], END)], recursive=False)
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo
    return s
def place(root, f, loc, rot=0.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    for p in ("location", "rotation_euler"): root.keyframe_insert(p, frame=f)

# --- Bryce: har kadr uchun joy va harakat
B = {}   # kadr -> (joy, burilish)
B["hook"] = (V(BCX, 1.45, MT + 0.06), 0)
B["look"] = (V(-0.35, 0.72, 0), 0)
B["pillow"] = (V(-0.72, 2.0, 0), -90)
B["blanket"] = (V(-0.72, 1.1, 0), -90)
B["fridge"] = (V(1.72, FCY, 0), 90)
B["wide"] = (V(0.3, 0.15, 0), 15)
B["call"] = (V(0.3, 0.15, 0), 20)
B["yell"] = (V(0.5, 0.3, 0), 25)
B["glance"] = (V(0.3, 0.15, 0), 20)
B["face"] = B["glance"]; B["hangup"] = B["glance"]
B["search"] = (V(-0.45, 0.25, 0), -55)
B["reveal"] = (V(0.6, -0.4, 0), 15)
for n in ("answer", "silent", "ask"): B[n] = (V(-10, 0, 0), 0)        # do'st kadrlarida ko'rinmaydi
for n, (loc, rz) in B.items(): place(broot, S[n][0], tuple(loc), rz)
ckey(broot)
LAY = A_("Laying_Idle_2.fbx", inplace=False)
strip(bry, LAY, -20, src=(60, 140))
LOOK = A_("Nervously_Look_Around.fbx")
strip(bry, LOOK, S["look"][0], src=(1, 170), speed=1.2)
THR = A_("Throw_Object.fbx")
strip(bry, THR, S["pillow"][0], src=(11, 70))
strip(bry, THR, S["blanket"][0], src=(9, 146), speed=2.0)
OPN = A_("Opening_3.fbx")
strip(bry, OPN, S["fridge"][0], src=(30, 140))
TOR = A_("Standing_Torch_Idle_02.fbx")
strip(bry, TOR, S["wide"][0], src=(20, 120))
PHN = A_("Talking_On_A_Cell_Phone.fbx")
strip(bry, PHN, S["call"][0], src=(30, 150), speed=1.3)
YEL = A_("Standing_Yell_2.fbx")
strip(bry, YEL, S["yell"][0], src=(12, 90), speed=0.72)
TXT = A_("Texting.fbx")
strip(bry, TXT, S["glance"][0], src=(20, 230), speed=1.15)
CRT = A_("Crouch_Torch_Idle_02.fbx", inplace=False)
strip(bry, CRT, S["search"][0], src=(9, 199), speed=0.9)
INS = A_("Standing_Torch_Inspect_Downward.fbx")
strip(bry, INS, S["reveal"][0], src=(5, 70), speed=0.62)

# --- Brian (do'stning xonasi)
FRI0 = V(FRX + 0.3, 0.55, 0)
place(froot, 1, tuple(FRI0), 0)
for n in ("silent",): place(froot, S[n][0], tuple(FRI0), 0)
place(froot, S["ask"][0], tuple(FRI0 + V(0.0, 0.0, 0)), 0)
ckey(froot)
strip(fri, PHN, S["answer"][0], src=(89, 150), speed=1.5)
strip(fri, PHN, 418, src=(150, 260), speed=0.85)
strip(fri, PHN, S["ask"][0], src=(380, 470), speed=1.0)

# ---------------- telefonlar (BlenderKit smartfon) ----------------
def phone(name, arm, bone, loc, rot, screen_imgs=None, black=True):
    hand = child_of_bone(name + "_hand", arm, bone)
    piv = empty(name + "_piv", loc, hand); piv.rotation_euler = [R(a) for a in rot]
    grp, new = import_gltf(BK + "a6d503d4_u.glb", (0, 0, 0), 0, 1.0)
    grp.name = name; grp.parent = piv; grp.location = (0, 0, 0)
    scr = next(o for o in new if o.name.startswith("screen"))
    body = next(o for o in new if o.name.startswith("body"))
    glass = next(o for o in new if o.name.startswith("glass"))
    return hand, piv, grp, scr, body, glass
PH_R = (tuple(map(float, os.environ.get("PHR_LOC", "0.0,0.085,0.035").split(","))), tuple(map(float, os.environ.get("PHR_ROT", "0,90,0").split(","))))
PH_L = (tuple(map(float, os.environ.get("PHL_LOC", "0.0,0.085,0.035").split(","))), tuple(map(float, os.environ.get("PHL_ROT", "90,0,180").split(","))))
phones = {}
phones["R"] = phone("phR", bry, "RightHand", *PH_R)
phones["L"] = phone("phL", bry, "LeftHand", *PH_L)
phones["F"] = phone("phF", fri, "RightHand", *PH_R)
# ekran materiali: rasm (UV o'rniga ob'ekt koordinatasi), "img" 0 = o'chiq, 1 = qo'ng'iroq, 2 = tugadi
def screen_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.005, 0.005, 0.006, 1); b.inputs["Roughness"].default_value = 0.08
    b.inputs["Coat Weight"].default_value = 1.0
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.5, 0); mp.inputs["Scale"].default_value = (1 / 0.0748, 1 / 0.1574, 1)
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(SCR + fn); t.extension = "CLIP"
        L.new(mp.outputs[0], t.inputs[0]); return t
    a, c = img("call.png"), img("ended.png")
    sel = value_node(m, "img", 0.0)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(P.math_n(N, L, "GREATER_THAN", sel, 1.5), mx.inputs["Factor"])
    L.new(a.outputs[0], mx.inputs[6]); L.new(c.outputs[0], mx.inputs[7])
    L.new(mx.outputs[2], b.inputs["Emission Color"])
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "GREATER_THAN", sel, 0.5), 2.2), b.inputs["Emission Strength"])
    return m
for k, (hand, piv, grp, scr, body, glass) in phones.items():
    sm = screen_mat("screen_" + k); scr.data = scr.data.copy(); scr.data.materials.clear(); scr.data.materials.append(sm)
    phones[k] = dict(hand=hand, piv=piv, grp=grp, scr=scr, body=body, glass=glass, sm=sm)
# ekran holatlari (Bryce o'ng qo'l telefoni)
smR = phones["R"]["sm"]
for f, v in ((1, 0), (S["call"][0] + 26, 1), (S["yell"][0], 1), (F_END_CALL, 2), (F_SCREEN_OFF, 0)):
    val_key(smR, "img", f, v)
ckey(smR.node_tree)
# fonar: telefon orqasidagi kamera oynasi yonida — chiroq + yaltiroq disk + yumshoq "gul" (glow) shari
glow_m = bpy.data.materials.new("flash_glow"); glow_m.use_nodes = True
N = glow_m.node_tree.nodes; L = glow_m.node_tree.links; N.remove(N["Principled BSDF"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
fac = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"]), 6.0)
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.97, 0.9, 1); L.new(P.math_n(N, L, "MULTIPLY", fac, 6.0), em.inputs["Strength"])
tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(tr.outputs[0], ad.inputs[1])
L.new(ad.outputs[0], N["Material Output"].inputs["Surface"])
led_m = mat("led", (1.0, 0.97, 0.92), 0.2, emit=60.0)
FLASH = {}
for k in ("R", "L"):
    g = phones[k]["glass"]
    bpy.context.view_layer.update()
    vs = [g.matrix_local @ v.co for v in g.data.vertices]          # telefon (grp) fazosida
    zmin = min(v.z for v in vs); zmax = max(v.z for v in vs)
    cx = sum(v.x for v in vs) / len(vs); cy = sum(v.y for v in vs) / len(vs)
    sv = [phones[k]["scr"].matrix_local @ v.co for v in phones[k]["scr"].data.vertices]
    back = -1.0 if (zmin + zmax) / 2 < sum(v.z for v in sv) / len(sv) else 1.0     # orqa tomon (kamera oynasi) — ekranga qarama-qarshi
    PB = float(os.environ.get("BACK", back))
    zb = zmin if PB < 0 else zmax
    led = cyl("led_" + k, 0.0035, 0.001, (cx + 0.012, cy - 0.006, zb + 0.0004 * PB), led_m, parent=phones[k]["grp"])
    glow = sphere("glow_" + k, 0.012, (cx + 0.012, cy - 0.006, zb + 0.002 * PB), glow_m, sub=3, parent=phones[k]["grp"])
    sp = bpy.data.objects.new("flash_" + k, bpy.data.lights.new("flash_" + k, "SPOT")); sc.collection.objects.link(sp)
    sp.parent = phones[k]["grp"]; sp.location = (cx + 0.012, cy - 0.006, zb + 0.004 * PB)
    sp.rotation_euler = (0, 0, 0) if PB < 0 else (0, R(180), 0)       # spot o'z -Z o'qiga qaraydi
    sp.data.spot_size = R(75); sp.data.spot_blend = 0.55; sp.data.shadow_soft_size = 0.004; sp.data.color = (1.0, 0.96, 0.9)
    sp.visible_camera = False
    FLASH[k] = (sp, led, glow)
    for o in (phones[k]["scr"], phones[k]["body"]):
        vv = [o.matrix_local @ v.co for v in o.data.vertices]; print("PHZ", o.name, round(min(v.z for v in vv), 4), round(max(v.z for v in vv), 4))
    print("PHONE", k, "glass z", round(zmin, 4), round(zmax, 4), "c", round(cx, 4), round(cy, 4), "back", PB)
FL_E = float(os.environ.get("FLASH_E", 12.0))
PHR_SHOTS = ("look", "call", "yell", "glance", "face", "hangup")
PHL_SHOTS = ("pillow", "blanket", "fridge", "wide", "search", "reveal")
def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys
for k, shots in (("R", PHR_SHOTS), ("L", PHL_SHOTS)):
    vis(phones[k]["piv"], rng(*shots))
    sp = FLASH[k][0]
    for f, e in lights_for(rng(*shots), FL_E): sp.data.energy = e; sp.data.keyframe_insert("energy", frame=f)
    ckey(sp.data)
vis(phones["F"]["piv"], rng(*FRIENDN))

# ---------------- yostiq va ko'rpa: qo'lga ergashadi (kadrma-kadr pishirilgan) ----------------
handR = phones["R"]["hand"]
def hand_track(f0, f1):
    return {f: wpos(handR, f) for f in range(f0, f1 + 1)}
# yostiq: qo'l pastdan ko'tarilib yostiq tagidan o'tganda ushlaydi
P0, P1 = S["pillow"]
ht = hand_track(P0, P1 + 2)
fmin = min(ht, key=lambda f: ht[f].z)
fgrab = next((f for f in sorted(ht) if f > fmin and ht[f].z > PIL0.z - 0.04), P1)
off = V(-0.2, -0.04, -0.06)                                # yostiqning o'ng chekkasi qo'lda
key(pil, 1, loc=tuple(PIL0), rot=(0, 0, 0)); key(pil, fgrab, loc=tuple(PIL0), rot=(0, 0, 0))
for f in range(fgrab + 1, P1 + 1):
    t = min(1.0, (f - fgrab) / 10); u = min(1.0, (f - fgrab) / 4)
    key(pil, f, loc=tuple(PIL0.lerp(ht[f] + off, ease(u))), rot=(0, -35 * t, 8 * t))
PIL_FLOOR = V(-0.55, 1.55, 0.07)
key(pil, P1 + 1, loc=tuple(PIL_FLOOR), rot=(4, 0, 35))
print("PILLOW grab", fmin, fgrab, tuple(round(x, 2) for x in ht[fgrab]))
# ko'rpa
B0, B1 = S["blanket"]
ht = hand_track(B0 - 6, B1 + 2)
fmin = min(ht, key=lambda f: ht[f].z)
fgrab = next((f for f in sorted(ht) if f > fmin and ht[f].z > MT + 0.02), B1)
frel = min(fgrab + 12, max(ht, key=lambda f: ht[f].z if f > fgrab else -9))
off = BLN0 - ht[fgrab]
key(bln, 1, loc=tuple(BLN0), rot=(0, 0, 0)); key(bln, fgrab, loc=tuple(BLN0), rot=(0, 0, 0))
for f in range(fgrab + 1, frel + 1):
    t = (f - fgrab) / max(1, frel - fgrab)
    key(bln, f, loc=tuple(ht[f] + off * (1 - t) + V(0, 0, 0.1 * t)), rot=(0, -60 * ease(t), 0))
BL_FLOOR = V(0.15, -0.25, 0.0)
rel = ht[frel]
key(bln, frel + 5, loc=tuple(rel.lerp(BL_FLOOR, 0.45) + V(0, 0, 0.55)), rot=(10, -110, 15))
key(bln, frel + 13, loc=tuple(BL_FLOOR), rot=(0, -180, 30))
interp(bln, "LINEAR")
print("BLANKET grab", fmin, fgrab, frel)
# ko'rpa yerda: osilib tushgan chekkalar polga kirmasin
# muzlatkich eshigi
DOOR_A, DOOR_B = 170, 184
key(hinge, 1, rot=(0, 0, 0)); key(hinge, DOOR_A, rot=(0, 0, 0)); key(hinge, DOOR_B, rot=(0, 0, -72))
key(hinge, S["wide"][1], rot=(0, 0, -72)); key(hinge, S["wide"][1] + 1, rot=(0, 0, 0))

# ======================================================================
# 4) KAMERALAR
# ======================================================================
CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.01):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 200
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
    rnd = random.Random(seed); base = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); p = cam.location.copy()
        k = amp * ((1 - (f - f0) / max(1, f1 - f0)) ** 2 if decay else 1.0)
        base[f] = p + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
    for f, p in base.items():
        cam.location = p; cam.keyframe_insert("location", frame=f)
def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)
def path_keys(o, pts):
    for f, p in pts: key(o, f, loc=tuple(p))
def abs_cam(name, pts, tgt_pts, lens, fstop=None, clip=0.01, focus=None):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=focus or t, clip=clip); path_keys(c, pts)
    return c
def rel_cam(name, target, lens, fstop, offsets, track=None, clip=0.005):
    r_ = empty(name + "_rig"); cl = r_.constraints.new("COPY_LOCATION"); cl.target = target
    c = shot_cam(name, (0, 0, 0), track or target, lens, fstop, focus=track or target, clip=clip)
    c.parent = r_; path_keys(c, offsets); return c
headB = child_of_bone("bry_head", bry, "Head")
faceB = empty("bry_face", (0.0, 0.07, 0.1), headB)       # Head fazosi: X chap, Y tepa, Z old
headF = child_of_bone("fri_head", fri, "Head")
faceF = empty("fri_face", (0.0, 0.07, 0.1), headF)
FB = {n: wpos(faceB, (a + b) // 2) for n, (a, b) in S.items()}
FF = {n: wpos(faceF, (a + b) // 2) for n, (a, b) in S.items()}
# 1 ILGAK: tepadan, aylanib pastga tushadi
a, b = S["hook"]; F_ = FB["hook"]
c = shot_cam("hook", tuple(F_ + V(0, -0.35, 1.7)), None, 18)
for f, z, rz, dy in ((a, 1.85, -25, -0.5), (b, 1.25, 20, -0.35)):
    c.location = tuple(F_ + V(0.0, dy, z)); c.keyframe_insert("location", frame=f)
    c.rotation_euler = (0, 0, R(rz)); c.keyframe_insert("rotation_euler", frame=f)
c.data.dof.use_dof = True; c.data.dof.aperture_fstop = 4.0; c.data.dof.focus_object = faceB
# 2 yuzga yaqin: past burchak, dolly-in
a, b = S["look"]
c = rel_cam("look", faceB, 45, 2.0, [(a, V(0.12, -0.85, -0.22)), (b, V(0.06, -0.55, -0.15))])
# 3 yostiq: matras sathida, yostiq yonidan
a, b = S["pillow"]
c = abs_cam("pillow", [(a, V(BCX + 0.05, 1.15, MT + 0.5)), (b, V(BCX + 0.15, 1.3, MT + 0.55))],
            [(a, V(BCX + 0.25, 2.2, MT + 0.12)), (b, V(-1.15, 2.2, MT + 0.45))], 20, 3.2, focus=None)
# 4 ko'rpa: poldan, keng ob'ektiv — ko'rpa kameraga uchadi
a, b = S["blanket"]
c = abs_cam("blanket", [(a, V(0.25, 0.2, 0.25)), (b, V(0.15, 0.05, 0.2))], [(a, V(-0.9, 1.15, 0.85)), (b, V(-0.7, 0.9, 0.9))], 14, 5.6)
# 5 muzlatkich ichidan
a, b = S["fridge"]
c = abs_cam("fridge", [(a, V(FX0 + FD - 0.12, FCY + 0.04, 1.46)), (b, V(FX0 + FD - 0.22, FCY + 0.02, 1.45))],
            [(a, V(1.6, FCY + 0.02, 1.48)), (b, V(1.6, FCY - 0.02, 1.5))], 20, 2.4, clip=0.01, focus=faceB)
# 6 keng plan: kran, yuqoriga ko'tariladi
a, b = S["wide"]
c = abs_cam("wide", [(a, V(2.2, -2.2, 1.0)), (b, V(1.9, -2.15, 2.35))], [(a, V(0.0, 0.6, 0.9)), (b, V(-0.1, 0.7, 0.4))], 13, 6.0)
# 7 qo'ng'iroq: bosh atrofida aylanma, past burchak
a, b = S["call"]; F_ = FB["call"]
c = shot_cam("call", tuple(F_), faceB, 26, 2.4, focus=faceB)
for f in range(a, b + 1, 2):
    t = ease((f - a) / (b - a)); ang = R(-70 + 95 * t); rr = 0.85 - 0.15 * t
    key(c, f, loc=tuple(F_ + V(rr * math.sin(ang), -rr * math.cos(ang), -0.32 + 0.1 * t)))
# 8 do'sti javob berdi: tez push-in
a, b = S["answer"]; F_ = FF["answer"]
c = abs_cam("answer", [(a, F_ + V(0.6, -1.9, -0.15)), (a + 8, F_ + V(0.35, -1.05, -0.08)), (b, F_ + V(0.3, -0.9, -0.06))],
            [(a, F_ + V(0, 0, -0.2)), (b, F_ + V(0, 0, -0.08))], 30, 2.8)
# 9 baqiradi: past burchak, 15 mm, titrash
a, b = S["yell"]; F_ = FB["yell"]
c = abs_cam("yell", [(a, F_ + V(0.35, -0.95, -1.05)), (b, F_ + V(0.22, -0.7, -0.9))], [(a, F_ + V(0, 0, -0.25)), (b, F_ + V(0, 0, -0.12))], 15, 4.0)
lens_keys(c, [(a, 15), (b, 18)]); shake(c, a, b, 0.012, seed=9, decay=False)
# 10 do'sti jim: yuzga juda yaqin
a, b = S["silent"]
c = rel_cam("silent", faceF, 70, 1.8, [(a, V(0.2, -0.95, 0.0)), (b, V(0.14, -0.7, 0.0))])
# 11 so'raydi: o'rta plan, yonlama siljish
a, b = S["ask"]; F_ = FF["ask"]
c = abs_cam("ask", [(a, F_ + V(-0.95, -1.25, -0.25)), (b, F_ + V(-0.45, -1.4, -0.2))], [(a, F_ + V(0, 0, -0.3)), (b, F_ + V(0, 0, -0.28))], 32, 2.8)
# 12 telefonga qaradi: yelka ortidan ekranga dolly-in
a, b = S["glance"]
scrR = phones["R"]["scr"]
c = shot_cam("glance", (0, 0, 0), scrR, 32, 2.8, focus=scrR, clip=0.005)
PG = wpos(scrR, b - 10); FG = FB["glance"]
path_keys(c, [(a, FG + V(-0.4, 0.45, 0.25)), (a + 30, FG + V(-0.3, 0.2, 0.18)), (b, PG + V(-0.13, 0.0, 0.2))])
# 13 yuz (ekran nurida), keyin makro: qizil tugma
a, b = S["face"]
c = rel_cam("face", faceB, 50, 2.0, [(a, V(0.1, -0.6, -0.28)), (b, V(0.07, -0.48, -0.24))])
a, b = S["hangup"]
c = rel_cam("hangup", scrR, 45, 8.0, [(a, V(-0.08, 0.1, 0.32)), (b, V(-0.06, 0.08, 0.25))], clip=0.002)
c.constraints[0].up_axis = "UP_Y"
# 14 qidirgan payt: poldan, fonar kameraga
a, b = S["search"]; F_ = FB["search"]
c = abs_cam("search", [(a, F_ + V(-1.1, -0.75, -0.82)), (b, F_ + V(-0.85, -0.95, -0.75))], [(a, F_ + V(0, 0, -0.2)), (b, F_ + V(0, 0, -0.25))], 18, 3.5)
# 15 ochilish: telefon fonaridan orqaga tortilib, yigitni ko'rsatadi
a, b = S["reveal"]
scrL = phones["L"]["grp"]
c = rel_cam("reveal", scrL, 35, 4.0, [(a, V(-0.06, -0.14, 0.04)), (a + 22, V(-0.2, -0.45, 0.1)), (b, V(-0.75, -1.5, 0.35))], clip=0.003)
lens_keys(c, [(a, 40), (b, 26)])
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]
# oxirgi kadrda telefonni qizil halqa bilan belgilash (Zack D. uslubi)
ring_m = mat("ring", (1.0, 0.05, 0.03), 0.4, emit=2.2)
bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.008, major_segments=64, minor_segments=8)
ring = bpy.context.object; ring.name = "ring"; ring.data.materials.append(ring_m)
ring.parent = phones["L"]["grp"]; ring.location = (0, 0, 0.0)
rt = ring.constraints.new("TRACK_TO"); rt.target = CAMS["reveal"]; rt.track_axis = "TRACK_Z"; rt.up_axis = "UP_Y"
RING_F = 812
key(ring, 1, scale=0.001); key(ring, RING_F, scale=0.001); key(ring, RING_F + 4, scale=1.15); key(ring, RING_F + 7, scale=1.0)
vis(ring, [(RING_F, END)])

# ======================================================================
# 5) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
L.new(env.outputs[0], N["Background"].inputs[0])
bgs = N["Background"].inputs[1]
for f, n in SHOTS:
    bgs.default_value = 0.6 if n in FRIENDN else 0.02; bgs.keyframe_insert("default_value", frame=f)
ckey(w.node_tree)
def area(name, loc, size, col, keys, target=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    ckey(l.data); l.visible_camera = cam_vis
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l
def point(name, loc, r, col, keys):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc; l.visible_camera = False
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    ckey(l.data); return l
STUDIO = rng(*STUDION); FRIEND = rng(*FRIENDN)
EK = float(os.environ.get("EK", 1.0))
# studiya: pardadan sovuq tong nuri, juda xira umumiy yorug'lik
area("st_window", (-2.75, 0.5, 1.55), 1.4, (0.6, 0.75, 1.0), lights_for(STUDIO, 70.0 * EK), target=empty("stwT", (0.5, 0.6, 0.6)))
area("st_ambient", (0.0, 0.0, 2.6), 3.0, (0.55, 0.65, 0.85), lights_for(STUDIO, 18.0 * EK), target=empty("stamT", (0, 0, 0)))
# yuzga yumshoq to'ldiruvchi: har kadrda kamera yonida (sovuq/iliq)
FT = empty("faceKeyT"); cl_ = FT.constraints.new("COPY_LOCATION"); cl_.target = faceB
fill = area("st_fill", (0, 0, 0), 0.6, (0.75, 0.85, 1.0), [(1, 0)], target=FT)
FILL = {"hook": (V(0.6, -0.5, 1.2), 10), "look": (V(-0.6, -0.8, 0.0), 14), "pillow": (V(-0.2, -0.6, 0.4), 6),
        "blanket": (V(0.2, -1.0, 0.2), 8), "fridge": (V(0.5, 0.6, 0.2), 6), "wide": (V(0.5, -1.0, 0.8), 10),
        "call": (V(-0.6, -0.8, 0.2), 14), "yell": (V(0.5, -0.8, -0.3), 14), "glance": (V(-0.5, -0.6, 0.4), 10),
        "face": (V(0.5, -0.7, 0.1), 10), "hangup": (V(0.4, -0.5, 0.3), 4), "search": (V(-0.6, -0.7, 0.2), 8),
        "reveal": (V(-0.6, -0.8, 0.3), 10)}
for n, (off, e) in FILL.items():
    f = S[n][0]
    fill.location = tuple(FB[n] + off); fill.keyframe_insert("location", frame=f)
    fill.data.energy = e * EK; fill.data.keyframe_insert("energy", frame=f)
for n in FRIENDN:
    fill.data.energy = 0; fill.data.keyframe_insert("energy", frame=S[n][0])
ckey(fill); ckey(fill.data)
# muzlatkich ichki chirog'i (eshik ochilganda yonadi)
FR_ON = DOOR_A + 2
frl = area("fr_light", (FX0 + FD - 0.1, FCY, 1.75), 0.35, (1.0, 0.97, 0.9), [(1, 0), (FR_ON, 45.0), (S["wide"][1] + 1, 0)], target=empty("frlT", (1.6, FCY, 1.3)))
frl2 = point("fr_bulb", (FX0 + 0.5, FCY, 1.7), 0.05, (1.0, 0.97, 0.9), [(1, 0), (FR_ON, 6.0), (S["wide"][1] + 1, 0)])
val_n = M["fridge_in"].node_tree.nodes["Principled BSDF"]
val_n.inputs["Emission Color"].default_value = (1.0, 0.98, 0.94, 1)
for f, e in ((1, 0.0), (FR_ON, 0.6), (S["wide"][1] + 1, 0.0)):
    val_n.inputs["Emission Strength"].default_value = e; val_n.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
ckey(M["fridge_in"].node_tree)
# telefon ekrani yuzni yoritadi (qo'ng'iroq / qarash kadrlari)
scr_light = area("scr_light", (0, 0, 0.02), 0.06, (0.55, 0.7, 1.0), [(1, 0), (S["glance"][0], 3.0), (F_SCREEN_OFF, 0)])
scr_light.parent = phones["R"]["grp"]; scr_light.location = (0, 0, 0.03); scr_light.rotation_euler = (R(180), 0, 0)
# do'stning xonasi: deraza (orqadan), old tomondan yumshoq kalit, ship
FT2 = empty("friKeyT"); cl2 = FT2.constraints.new("COPY_LOCATION"); cl2.target = faceF
area("f_window", FP(1.4, 2.3, 1.6), 2.0, (0.85, 0.92, 1.0), lights_for(FRIEND, 260.0), target=empty("fwT", FP(0.3, 0.0, 1.0)))
area("f_key", FP(-1.2, -1.2, 2.0), 1.2, (1.0, 0.92, 0.82), lights_for(FRIEND, 140.0), target=FT2)
area("f_ceil", FP(0, 0.3, 2.6), 2.5, (1.0, 0.95, 0.88), lights_for(FRIEND, 120.0), target=empty("fcT", FP(0, 0.3, 0)))

# ======================================================================
# 6) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 5; sc.cycles.transparent_max_bounces = 12; sc.cycles.transmission_bounces = 4
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = False
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("PROBE"): exec(open(os.environ["PROBE"]).read())
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
