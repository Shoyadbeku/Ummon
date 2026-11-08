# "Samolyot derazalari nega dumaloq?" — Zack D. Films uslubida 43 s (1036 kadr, 24 fps, 9:16).
# Sahnalar bitta faylda, turli joylarda: salon (0,0,0), osmon (2000,0,0), angar (4000,0,0), rentgen panel (6000,0,1.5).
# Kesishlar kamera markerlari bilan. Render: OUT=... SAMPLES=10 PCT=50 python -I samolyot.py --render  (FRAMES=1,60 sinov uchun)
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from mathutils import Vector, Matrix
import parts as P
from parts import R, box, cyl, sphere, empty, key, par, mat, bsdf, vis, cam_move, camera
import mixchar as mc

OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, 1036, 24

# kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md)
S = {1: (1, 46), 2: (47, 103), 3: (104, 201), 4: (202, 261), 5: (262, 314), 6: (315, 394), 7: (395, 443),
     8: (444, 518), 9: (519, 559), 10: (560, 598), 11: (599, 655), 12: (656, 711), 13: (712, 794),
     14: (795, 899), 15: (900, 972), 16: (973, 1036)}
CAB = Vector((0, 0, 0)); SKY = Vector((2000, 0, 0)); HAN = Vector((4000, 0, 0)); PAN = Vector((6000, 0, 1.5))

M = dict(
    alu=mat("alu", (0.8, 0.81, 0.83), 0.22, metal=1.0),
    darkglass=mat("darkglass", (0.01, 0.012, 0.016), 0.05, coat=1.0),
    black=mat("black", (0.01, 0.01, 0.01), 0.6),
    exhaust=mat("exhaust", (0.04, 0.035, 0.03), 0.4, metal=0.8, emit=0.08, emit_col=(1.0, 0.35, 0.08)),
    livery=P.comet_livery("livery"), livery_fin=P.comet_livery("livery_fin"),
    plastic=mat("plastic", (0.86, 0.85, 0.82), 0.45),
    fabric=mat("fabric", (0.05, 0.09, 0.2), 0.95),
    cover=mat("cover", (0.85, 0.85, 0.82), 0.8),
    carpet=mat("carpet", (0.12, 0.13, 0.17), 1.0),
    cove=mat("cove", (1.0, 0.85, 0.65), 0.5, emit=6.0),
    yellow=mat("yellow", (0.9, 0.6, 0.02), 0.5),
    steel=mat("steel", (0.32, 0.33, 0.35), 0.45, metal=1.0),
    rust=mat("girder", (0.25, 0.08, 0.05), 0.6, metal=0.3),
    tile=mat("tile", (0.55, 0.68, 0.72), 0.25),
    brass=mat("brass", (0.85, 0.62, 0.3), 0.25, metal=1.0),
    dial=mat("dial", (0.92, 0.9, 0.84), 0.5, emit=0.25),
    red=mat("red", (0.8, 0.02, 0.02), 0.4, emit=0.4),
    white=mat("white", (0.95, 0.95, 0.95), 0.3, emit=40.0),
    skylight=mat("skylight", (0.9, 0.95, 1.0), 0.5, emit=8.0),
    wall=mat("wall", (0.42, 0.44, 0.42), 0.7, metal=0.4),
    dark=mat("dark", (0.004, 0.008, 0.02), 1.0, emit=1.0, emit_col=(0.004, 0.01, 0.03)),
)
bsdf(M["livery_fin"]).inputs["Metallic"].default_value = 0.0

# =================================================================== SALON (A320 ichi)
# o'q X bo'ylab, oldi -X; chap (deraza) tomoni -Y. Pol z=0, fyuzelyaj markazi z=0.6, ichki radius 1.85
import bmesh
RC, ZC = 1.85, 0.6
bm = bmesh.new(); seg = 96; xs = [-7 + 14 * i / 40 for i in range(41)]
rings = [[bm.verts.new((x, RC * math.cos(2 * math.pi * j / seg), ZC + RC * math.sin(2 * math.pi * j / seg))) for j in range(seg)] for x in xs]
for i in range(len(xs) - 1):
    for j in range(seg):
        k = (j + 1) % seg; bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]))
shell = P.mesh_obj("cabin_shell", bm, M["plastic"]); P.smooth(shell)
sol = shell.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.08
ROWS = [0.12 + 0.82 * (k - 6) for k in range(15)]
MEG_X = ROWS[6]
PHI = math.asin((1.05 - ZC) / RC)
cut_bm = bmesh.new(); win_mats = []
def basis(X, Y, Z, pos):
    m = Matrix.Identity(4)
    for i, v in enumerate((X, Y, Z, pos)):
        for j in range(3): m[j][i] = v[j]
    return m
def win_frame(side):
    d = Vector((0, side * math.cos(PHI), math.sin(PHI))); t = Vector((0, -side * math.sin(PHI), math.cos(PHI)))
    w = t.cross(d); return d, t, w
for side in (-1, 1):
    d, t, w = win_frame(side)
    for x in ROWS:
        wx = x - 0.28
        c = Vector((wx, 0, ZC)) + d * RC
        mtx = basis(w, t, d, c)
        r = bmesh.ops.create_cone(cut_bm, cap_ends=True, segments=32, radius1=1, radius2=1, depth=1)
        bmesh.ops.transform(cut_bm, matrix=mtx @ Matrix.Diagonal((0.125, 0.18, 0.5, 1)), verts=r["verts"])
        win_mats.append((c, w, t, d, side, wx))
cutter = P.mesh_obj("win_cutter", cut_bm)
bo = shell.modifiers.new("win", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cutter; bo.solver = "EXACT"
bpy.context.view_layer.objects.active = shell
for mod in list(shell.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter, do_unlink=True)
# illyuminator ramkasi (BlenderKit 7250f009): Blender'da X = en, Y = bo'y, Z = qalinlik
BZX = float(os.environ.get("BZX", 1))
for c, w, t, d, side, wx in win_mats:
    root, new = P.import_gltf(BK + "7250f009_u.glb", name="bezel")
    for o in new:
        if o.type == "MESH" and o.name.startswith("Circle.002"): bpy.data.objects.remove(o, do_unlink=True)
    pos = c - d * 0.085
    root.matrix_world = basis(BZX * w, t, BZX * d, pos) @ Matrix.Diagonal((0.95, 0.95, 1, 1))
box("cabin_floor", (14, 3.6, 0.1), (0, 0, -0.05), M["carpet"])
box("aisle", (14, 0.5, 0.012), (0, 0, 0.006), mat("aislecarpet", (0.25, 0.05, 0.06), 1.0))
for side in (-1, 1):
    bins = box("bins", (14, 0.72, 0.42), (0, side * 1.22, 1.86), M["plastic"], 0.04, rot=(side * -18, 0, 0))
    box("cove", (14, 0.03, 0.03), (0, side * 0.86, 2.08), M["cove"])
    box("sidewall_lo", (14, 0.05, 0.42), (0, side * 1.72, 0.21), M["plastic"])
for x in (-7.0, 7.0): box("bulkhead", (0.1, 3.8, 3.0), (x, 0, 1.0), M["plastic"])
def seat(x, y):
    box("seat_pan", (0.48, 0.46, 0.12), (x + 0.02, y, 0.44), M["fabric"], 0.04)
    box("seat_back", (0.1, 0.46, 0.62), (x + 0.27, y, 0.79), M["fabric"], 0.04, rot=(0, -10, 0))
    box("seat_head", (0.12, 0.4, 0.18), (x + 0.31, y, 1.0), M["cover"], 0.03, rot=(0, -10, 0))
    box("seat_leg", (0.05, 0.05, 0.38), (x, y, 0.19), M["steel"])
    for dy in (-0.25, 0.25): box("arm", (0.42, 0.05, 0.05), (x + 0.05, y + dy, 0.64), M["plastic"], 0.015)
for x in ROWS:
    for y in (-1.3, -0.82, -0.34, 0.34, 0.82, 1.3): seat(x, y)
ceil_l = bpy.data.objects.new("cabin_light", bpy.data.lights.new("cabin_light", "AREA")); P.link(ceil_l)
ceil_l.data.shape = "RECTANGLE"; ceil_l.data.size = 10; ceil_l.data.size_y = 0.6; ceil_l.data.energy = 900
ceil_l.data.color = (1.0, 0.88, 0.72); ceil_l.location = (0, 0, 2.3)
fill = bpy.data.objects.new("win_fill", bpy.data.lights.new("win_fill", "AREA")); P.link(fill)
fill.data.size = 0.6; fill.data.energy = 25; fill.data.color = (0.85, 0.92, 1.0)
fill.location = (MEG_X - 0.3, -1.55, 1.15); fill.rotation_euler = (R(-80), 0, 0)

# =================================================================== OSMON: bulutlar, A320, "Comet"
cl_mats = []
for z, sc_, th in ((-45, 0.012, 0.5), (-160, 0.005, 0.46)):
    cm = P.cloud_material(f"clouds{z}", sc_, th); cl_mats.append(cm)
    o = box(f"clouds{z}", (9000, 9000, 0.01), (SKY.x, 0, z), cm)
for cm in cl_mats:
    mp = cm.node_tree.nodes["MAP"]
    P.key_input(mp.inputs["Location"], 1, (0, 0, 0)); P.key_input(mp.inputs["Location"], 1036, (-6.0 * 1035, 0, 0))
    for fc in P.all_fcurves(cm.node_tree):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"

a320, a_parts = P.import_gltf(BK + "536fac67_u.glb", name="a320")
a320.scale = (0.5,) * 3
bpy.context.view_layer.update()
body = next(o for o in a_parts if o.name.startswith("plane body"))
rud = next(o for o in a_parts if o.name.startswith("rodder"))
bc = sum((body.matrix_world @ Vector(v) for v in body.bound_box), Vector()) / 8
rc = sum((rud.matrix_world @ Vector(v) for v in rud.bound_box), Vector()) / 8
if rc.x < bc.x: a320.rotation_euler.z = R(180)   # burun -X ga
bpy.context.view_layer.update()
bb = [body.matrix_world @ Vector(v) for v in body.bound_box]
AMIN = Vector([min(v[i] for v in bb) for i in range(3)]); AMAX = Vector([max(v[i] for v in bb) for i in range(3)])
a320.location = SKY - Vector(((AMIN.x + AMAX.x) / 2 - 14, (AMIN.y + AMAX.y) / 2, (AMIN.z + AMAX.z) / 2))
bpy.context.view_layer.update()
bb = [body.matrix_world @ Vector(v) for v in body.bound_box]
AMIN = Vector([min(v[i] for v in bb) for i in range(3)]); AMAX = Vector([max(v[i] for v in bb) for i in range(3)])
print("A320 body", AMIN, AMAX)
vis(a320, [S[2]])

comet, cfr, crr, cwins = P.build_comet("comet", M, "square", split_x=12.0, wings=True)
comet.location = SKY
for f, rl in ((1, 0), (150, 2.5), (300, -1.5), (394, 0)):
    key(comet, f, rot=(rl, 0, 0))
vis(comet, [(S[3][0], S[6][1])])
# yoriq derazada (6-kadr boshida)
crm_w = P.crack_material("crack_win")
wx, ws, wgl = next(w for w in cwins if w[1] == -1 and abs(w[0] - 11.9) < 0.2)
cw = P.crack_strip("crack_win", crm_w, (0, 0), (1.0, 0.75), length=0.55, width=0.012, seed=5)
cw.rotation_euler = (R(90 - math.degrees(math.asin(0.46 / 1.5))), 0, 0)
cw.location = SKY + Vector((wx + 0.22, -1.512, 0.24 + 0.215))
par(cw, cfr)
P.key_value(crm_w, "PROG", S[6][0], 0.0); P.key_value(crm_w, "PROG", 332, 1.0)
# parchalanish: 333-kadrdan
BANG = 333
for o, l1, r1 in ((cfr, (12 - 2.5, -0.6, -3.5), (-5, -12, -4)), (crr, (12 + 9.5, 1.8, -7.5), (6, 30, 9))):
    key(o, 1, loc=(12, 0, 0), rot=(0, 0, 0)); key(o, BANG, loc=(12, 0, 0), rot=(0, 0, 0))
    key(o, S[6][1], loc=l1, rot=r1)
    for fc in P.all_fcurves(o):
        for k in fc.keyframe_points:
            k.interpolation = "QUAD"; k.easing = "EASE_OUT" if k.co.x > BANG else "AUTO"
rnd = random.Random(11); deb = empty("debris_root", SKY)
for i in range(140):
    a = rnd.uniform(0, 2 * math.pi); r0 = 1.5
    p0 = Vector((12 + rnd.uniform(-0.6, 0.6), r0 * math.cos(a), r0 * math.sin(a)))
    v = Vector((rnd.uniform(3, 14), math.cos(a) * rnd.uniform(3, 11), math.sin(a) * rnd.uniform(3, 11)))
    sz = rnd.uniform(0.06, 0.45)
    o = box(f"debris{i}", (sz, sz * rnd.uniform(0.4, 1.2), 0.012), tuple(p0), M["alu"] if i % 3 else M["plastic"])
    o.parent = deb
    w = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * rnd.uniform(200, 700)
    for f in range(BANG, S[6][1] + 1, 3):
        tt = (f - BANG) / 24
        p = p0 + v * tt + Vector((0.5 * 22 * tt * tt, 0, -0.5 * 9.8 * tt * tt))
        key(o, f, loc=tuple(p), rot=tuple(w * tt))
vis(deb, [(BANG, S[6][1])])
flash = bpy.data.objects.new("flash", bpy.data.lights.new("flash", "POINT")); P.link(flash)
flash.location = SKY + Vector((12, -2.2, 0.3)); flash.data.shadow_soft_size = 1.0; flash.data.color = (1, 0.9, 0.8)
for f, e in ((1, 0), (BANG - 1, 0), (BANG, 6e4), (BANG + 3, 2e4), (BANG + 12, 0)): flash.data.energy = e; flash.data.keyframe_insert("energy", frame=f)
burst = sphere("burst", 0.5, tuple(SKY + Vector((12, -1.6, 0.3))), mat("burstm", (1, 1, 1), 1.0, emit=12.0, alpha=0.35))
for f, s in ((BANG, 0.2), (BANG + 3, 1.3), (BANG + 6, 1.6)): key(burst, f, scale=(s, s, s))
burst.hide_render = True   # sharsimon chaqnash soxta ko'rindi: faqat yorug'lik qoldi

# =================================================================== ANGAR + SUV HAVZASI
H = HAN
PX, PY, PD, WZ = 16.0, 3.2, 4.5, -0.4
conc = P.tex_image_mat("hangar_floor", PH + "concrete_pavement", 0.35, tint=(0.75, 0.75, 0.72))
for loc, size in (((0, PY + 12.5, -0.1), (90, 25, 0.2)), ((0, -PY - 12.5, -0.1), (90, 25, 0.2)),
                  ((PX + 22.5, 0, -0.1), (45, 2 * PY, 0.2)), ((-PX - 22.5, 0, -0.1), (45, 2 * PY, 0.2))):
    box("hfloor", size, tuple(H + Vector(loc)), conc)
for loc, size in (((0, PY + 0.1, -PD / 2), (2 * PX + 0.4, 0.2, PD)), ((0, -PY - 0.1, -PD / 2), (2 * PX + 0.4, 0.2, PD)),
                  ((PX + 0.1, 0, -PD / 2), (0.2, 2 * PY, PD)), ((-PX - 0.1, 0, -PD / 2), (0.2, 2 * PY, PD)),
                  ((0, 0, -PD - 0.1), (2 * PX, 2 * PY, 0.2))):
    box("pit", size, tuple(H + Vector(loc)), M["tile"])
# suv: shaffof + yaltiroq sirt, ichida yutilish hajmi
wm = bpy.data.materials.new("water"); wm.use_nodes = True; nt = wm.node_tree; N = nt.nodes; L = nt.links
for n in list(N):
    if n.type != "OUTPUT_MATERIAL": N.remove(n)
outn = N["Material Output"]
tr = N.new("ShaderNodeBsdfTransparent"); tr.inputs[0].default_value = (0.75, 0.92, 0.95, 1)
gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.04
fr_ = N.new("ShaderNodeFresnel"); fr_.inputs["IOR"].default_value = 1.33
mix = N.new("ShaderNodeMixShader"); L.new(fr_.outputs[0], mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(gl.outputs[0], mix.inputs[2])
L.new(mix.outputs[0], outn.inputs["Surface"])
nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 6
wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 0.35; wv.name = "RING"
tcw = N.new("ShaderNodeTexCoord"); L.new(tcw.outputs["Object"], nz.inputs["Vector"]); L.new(tcw.outputs["Object"], wv.inputs["Vector"])
add = N.new("ShaderNodeMath"); add.operation = "ADD"; L.new(nz.outputs["Fac"], add.inputs[0]); L.new(wv.outputs["Fac"], add.inputs[1])
bp = N.new("ShaderNodeBump"); bp.name = "BUMP"; bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.05
L.new(add.outputs[0], bp.inputs["Height"])
L.new(bp.outputs[0], gl.inputs["Normal"]); L.new(bp.outputs[0], fr_.inputs["Normal"])
va = N.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (0.35, 0.75, 0.78, 1); va.inputs["Density"].default_value = 0.22
L.new(va.outputs[0], outn.inputs["Volume"])
P.key_input(nz.inputs["W"], 1, 0.0); P.key_input(nz.inputs["W"], 1036, 40.0)
P.key_input(wv.inputs["Phase Offset"], 1, 0.0); P.key_input(wv.inputs["Phase Offset"], 1036, -260.0)
for f, s in ((1, 0.06), (470, 0.06), (478, 0.6), (518, 0.22), (1036, 0.22)): P.key_input(bp.inputs["Strength"], f, s)
for fc in P.all_fcurves(nt):
    if "W" in fc.data_path or "Phase" in fc.data_path or fc.data_path.startswith('nodes["Texture') or True:
        pass
water = box("water", (2 * PX - 0.02, 2 * PY - 0.02, PD + WZ - 0.02), tuple(H + Vector((0, 0, (WZ - PD) / 2))), wm)
# fyuzelyaj (qanotsiz) krandan tushiriladi
hfus, hfr, hrr, _ = P.build_comet("hfus", M, "square", split_x=None, wings=False)
FZ0, FZ1 = 4.2, -1.75
hfus.location = H + Vector((-14, 0, FZ0))
key(hfus, 1, loc=tuple(H + Vector((-14, 0, FZ0)))); key(hfus, S[8][0] + 2, loc=tuple(H + Vector((-14, 0, FZ0))))
key(hfus, 506, loc=tuple(H + Vector((-14, 0, FZ1))))
for fc in P.all_fcurves(hfus):
    for k in fc.keyframe_points: k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"
# bosim impulslari: fyuzelyaj "nafas oladi" (Y/Z masshtab) — 9..11-kadrlar
PULSE = list(range(519, 656, 8))
for i, f in enumerate(PULSE):
    s = 1.045 if i % 2 else 1.0
    key(hfus, f, scale=(1, s, s))
# kran: ikki to'sin, aravacha, troslar
for y in (-PY - 1.2, PY + 1.2):
    box("crane_beam", (40, 0.5, 0.7), tuple(H + Vector((0, y, 9.4))), M["yellow"], 0.02)
    for x in (-19, 19): box("crane_col", (0.6, 0.6, 9.6), tuple(H + Vector((x, y, 4.8))), M["yellow"], 0.02)
cables = []
for x in (-7, 7):
    box("trolley", (1.2, 2 * PY + 3.2, 0.6), tuple(H + Vector((x, 0, 9.0))), M["yellow"], 0.02)
    for y in (-0.5, 0.5):
        bmc = bmesh.new(); bmesh.ops.create_cone(bmc, cap_ends=True, segments=10, radius1=0.035, radius2=0.035, depth=1.0)
        bmesh.ops.translate(bmc, vec=(0, 0, -0.5), verts=bmc.verts)
        cb = P.mesh_obj("cable", bmc, M["steel"], tuple(H + Vector((x, y, 8.8)))); cables.append(cb)
def cable_len(z): return 8.8 - (z + 1.45)
for cb in cables:
    for f, z in ((1, FZ0), (S[8][0] + 2, FZ0), (506, FZ1)):
        key(cb, f, scale=(1, 1, cable_len(z)))
    for fc in P.all_fcurves(cb):
        for k in fc.keyframe_points: k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"
    vis(cb, [(S[7][0], S[9][1])])
# temir panjara
for x in range(-15, 16, 2):
    cyl("rail_post", 0.03, 1.05, tuple(H + Vector((x, -PY - 0.3, 0.52))), M["yellow"], verts=12)
for z in (0.55, 1.05):
    cyl("rail", 0.025, 31, tuple(H + Vector((0, -PY - 0.3, z))), M["yellow"], rot=(0, 90, 0), verts=12)
# devorlar, tom, yorug'lik
hw = P.tex_image_mat("hangar_wall", PH + "painted_plaster_wall", 0.25, tint=(0.62, 0.66, 0.66))
box("hwall_b", (90, 0.3, 18), tuple(H + Vector((0, 25, 9))), hw)
box("hwall_f", (90, 0.3, 18), tuple(H + Vector((0, -25, 9))), hw)
box("hwall_l", (0.3, 50, 18), tuple(H + Vector((-45, 0, 9))), hw)
box("hwall_r", (0.3, 50, 18), tuple(H + Vector((45, 0, 9))), hw)
box("hroof", (90, 50, 0.3), tuple(H + Vector((0, 0, 18))), M["wall"])
for x in range(-36, 37, 12):
    box("skylight", (6, 30, 0.05), tuple(H + Vector((x, 0, 17.8))), M["skylight"])
    box("girder", (0.4, 50, 1.0), tuple(H + Vector((x + 6, 0, 17.2))), M["rust"])
for x in range(-40, 41, 8):
    box("hwin", (5, 0.05, 3), tuple(H + Vector((x, 24.8, 11))), M["skylight"])
    box("hwin", (5, 0.05, 3), tuple(H + Vector((x, -24.8, 11))), M["skylight"])
# yon devorda ish stoli, bochkalar (fon tafsilotlari)
for i, x in enumerate((-10, -8.8, 9, 10.3)):
    cyl("barrel", 0.3, 0.9, tuple(H + Vector((x, -9 + (i % 2) * 0.7, 0.45))), [M["rust"], M["steel"]][i % 2], verts=24)
box("bench", (3, 0.9, 0.9), tuple(H + Vector((-4, -12, 0.45))), M["rust"], 0.02)
for x in (-12, 0, 12):
    l = bpy.data.objects.new("hlamp", bpy.data.lights.new("hlamp", "AREA")); P.link(l)
    l.data.size = 8; l.data.energy = 9000; l.data.color = (1.0, 0.9, 0.75); l.location = H + Vector((x, 0, 16))
# manometr
gp = H + Vector((-12.5, -3.85, 1.15))
cyl("gauge_post", 0.04, 1.15, tuple(gp + Vector((0, 0.06, -0.6))), M["steel"], verts=16)
cyl("gauge_rim", 0.17, 0.06, tuple(gp), M["brass"], rot=(90, 0, 0), verts=48)
cyl("gauge_face", 0.15, 0.065, tuple(gp), M["dial"], rot=(90, 0, 0), verts=48, bevel=False)
for i in range(15):
    a = R(-135 + 270 * i / 14); rr = 0.12
    box("tick", (0.006, 0.004, 0.03 if i % 2 == 0 else 0.018), tuple(gp + Vector((rr * math.sin(a), -0.035, rr * math.cos(a)))),
        M["red"] if i >= 12 else M["black"], rot=(0, math.degrees(a), 0))
npiv = empty("needle_piv", tuple(gp + Vector((0, -0.04, 0))))
nd = box("needle", (0.008, 0.004, 0.11), tuple(gp + Vector((0, -0.04, 0.045))), M["red"]); par(nd, npiv)
sphere("needle_cap", 0.012, tuple(gp + Vector((0, -0.042, 0))), M["brass"])
for i, f in enumerate(PULSE):
    key(npiv, f, rot=(0, 70 if i % 2 else -100, 0))
# muhandislar (Mixamo)
def tame(meshes):
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
A = lambda f: mc.load_action(f, True)
jroot, josh, jm = mc.load_character("josh", "Josh.fbx")
proot, pete, pm = mc.load_character("pete", "Pete.fbx")
droot, dav, dm = mc.load_character("david", "David.fbx")
groot, girl, gm = mc.load_character("girl", "Megan.fbx")
tame(jm + pm + dm + gm)
JP = H + Vector((-3.0, -4.35, 0)); jroot.location = JP; jroot.rotation_euler.z = R(180)
proot.location = H + Vector((-1.5, -4.6, 0)); proot.rotation_euler.z = R(165)
droot.location = H + Vector((-4.7, -5.0, 0)); droot.rotation_euler.z = R(200)
mc.add_strip(josh, A("Pointing_Forward.fbx"), S[7][0] - 40, speed=1.0, blend=0)
mc.add_strip(josh, A("Reacting.fbx"), S[11][0] - 12, speed=1.0, blend=6)
mc.add_strip(pete, A("Looking_Down.fbx"), S[7][0] - 30, repeat=3.0, speed=1.0, blend=0)
mc.add_strip(dav, A("Idle_14.fbx"), S[7][0] - 30, repeat=2.0, speed=1.0, blend=0)
mc.add_strip(dav, A("Head_Nod_Yes.fbx"), S[8][0], speed=1.0, blend=5)
for r_ in (jroot, proot, droot): vis(r_, [(S[7][0], S[11][1])])
# qiz salonda (Megan), boshi derazaga buriladi
groot.location = (MEG_X + 0.08, -1.3, 0.02); groot.rotation_euler.z = R(-90)
mc.add_strip(girl, A("Sitting_Idle_5.fbx"), -20, repeat=12.0, speed=1.0, blend=0)
look = empty("girl_look", (MEG_X - 0.6, -2.6, 1.0))
for bn, inf in (("mixamorig:Neck", 0.35), ("mixamorig:Head", 0.55)):
    c = girl.pose.bones[bn].constraints.new("DAMPED_TRACK"); c.target = look; c.track_axis = "TRACK_Z"; c.influence = inf
vis(groot, [S[1], S[16]])

# =================================================================== RENTGEN PANEL (kuch chiziqlari)
box("void", (60, 60, 60), tuple(PAN + Vector((6, 8, 0))), M["dark"])
bpy.data.objects["void"].modifiers.new("flip", "SOLIDIFY").thickness = 0.5
sq_m = P.stress_material("stress_sq", "square", 0.25); rd_m = P.stress_material("stress_rd", "round", 0.25)
riv = mat("rivet", (0.7, 0.72, 0.75), 0.3, metal=1.0)
psq = P.panel_with_hole("panel_sq", sq_m, "square", 0.25, rivet_m=riv); psq.location = PAN
prd = P.panel_with_hole("panel_rd", rd_m, "round", 0.25, rivet_m=riv); prd.location = PAN + Vector((12, 0, 0))
for p_ in (psq, prd):
    box(p_.name + "_glass", (0.7, 0.01, 0.7), tuple(p_.location + Vector((0, 0.03, 0))), M["darkglass"])
crm = P.crack_material("crack_panel")
for i, (dirv, ln, sd) in enumerate((((1, 0.8), 0.5, 3), ((1, 0.25), 0.3, 8), ((0.35, 1), 0.26, 13))):
    cr = P.crack_strip(f"crack{i}", crm, (0.236, 0.236), dirv, length=ln, width=0.0045, seed=sd)
    cr.parent = psq; cr.location = (0, 0, 0.0215)
CRACK = 864
P.key_value(crm, "PROG", 1, 0.0); P.key_value(crm, "PROG", CRACK, 0.0)
P.key_value(crm, "PROG", CRACK + 3, 0.45); P.key_value(crm, "PROG", CRACK + 10, 0.6); P.key_value(crm, "PROG", S[14][1], 1.0)
for m_ in (sq_m, rd_m):
    P.key_value(m_, "T", 1, 0.0); P.key_value(m_, "T", 1036, -220.0)
    for i, f in enumerate(range(S[12][0], 1037, 12)):
        P.key_value(m_, "P", f, 1.0 if i % 2 else 0.15)
P.key_value(sq_m, "HOT", S[12][0], 0.55); P.key_value(sq_m, "HOT", S[13][0] + 30, 1.6); P.key_value(sq_m, "HOT", S[14][1], 2.0)
for m_ in (sq_m, rd_m, crm):
    for fc in P.all_fcurves(m_.node_tree):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
pl = bpy.data.objects.new("panel_key", bpy.data.lights.new("panel_key", "AREA")); P.link(pl)
pl.data.size = 3; pl.data.energy = 120; pl.data.color = (0.7, 0.85, 1.0); pl.location = PAN + Vector((5, -4, 3))
pl.rotation_euler = (R(55), 0, R(-30))

# =================================================================== KAMERALAR
SH = 0.0
cams = {}
def C(n, lens, fstop=None, focus=None):
    c, t = camera(f"cam{n:02d}", lens, fstop, focus); cams[n] = c; return c, t
K = lambda v: tuple(v)
# 1: ILGAK — salon, yelka ortidan derazaga push-in
c, t = C(1, 22, 2.8)
cam_move(c, t, *S[1], (MEG_X - 1.0, -0.15, 1.34), (MEG_X - 0.62, -0.88, 1.2), (MEG_X - 0.2, -1.6, 1.08), (MEG_X - 0.26, -1.75, 1.05),
         "out", lens=(20, 30, "inout"))
# 2: A320 derazalari bo'ylab
ay, az = AMIN.y, (AMIN.z + AMAX.z) / 2 + 0.35
c, t = C(2, 20, 5.6)
cam_move(c, t, *S[2], (AMIN.x + 5.5, ay - 2.4, az + 0.5), (AMIN.x + 12.5, ay - 1.6, az + 0.25),
         (AMIN.x + 9.5, ay + 0.2, az), (AMIN.x + 16.5, ay + 0.2, az), "inout")
# 3: Comet to'rtburchak derazalari bo'ylab
c, t = C(3, 22, 5.6)
cam_move(c, t, *S[3], K(SKY + Vector((4.2, -3.4, 0.75))), K(SKY + Vector((15.8, -2.9, 0.5))),
         K(SKY + Vector((7.4, -1.5, 0.24))), K(SKY + Vector((19.4, -1.5, 0.24))), "inout")
# 4: pastdan keng plan
c, t = C(4, 16)
cam_move(c, t, *S[4], K(SKY + Vector((-2, -30, -13))), K(SKY + Vector((20, -24, -11))),
         K(SKY + Vector((10, 0, 0))), K(SKY + Vector((15, 0, 0))), "inout")
# 5: oldindan-yondan kuzatish
c, t = C(5, 45)
cam_move(c, t, *S[5], K(SKY + Vector((-16, -26, 3))), K(SKY + Vector((-9, -27, 0.5))),
         K(SKY + Vector((9, 0, 0))), K(SKY + Vector((12, 0, -0.5))), "lin")
# 6: deraza burchagida yoriq -> portlash, orqaga keskin chekinish
c, t = C(6, 28, 4.0)
cam_move(c, t, S[6][0], BANG - 1, K(SKY + Vector((12.9, -3.6, 0.75))), K(SKY + Vector((12.45, -2.75, 0.55))),
         K(SKY + Vector((12.15, -1.5, 0.45))), K(SKY + Vector((12.2, -1.5, 0.48))), "inout")
cam_move(c, t, BANG, S[6][1], K(SKY + Vector((11.0, -4.6, 1.1))), K(SKY + Vector((2.0, -19, 3.2))),
         K(SKY + Vector((12.3, -1.4, 0.3))), K(SKY + Vector((15, 0, -2.0))), "out", shake=[(BANG, BANG + 30, 0.3)], lens=(26, 18, "out"))
# 7: angar, muhandislar ortidan past burchak
c, t = C(7, 20, 4.0)
cam_move(c, t, *S[7], K(H + Vector((-7.2, -8.6, 0.45))), K(H + Vector((-5.0, -9.2, 0.55))),
         K(H + Vector((-2.5, 0, 3.6))), K(H + Vector((-0.5, 0, 3.4))), "inout")
# 8: yuqoridan keng plan, fyuzelyaj suvga tushadi
c, t = C(8, 17)
cam_move(c, t, *S[8], K(H + Vector((-21, -13, 10))), K(H + Vector((-18, -11.5, 8.6))),
         K(H + Vector((-1, 0, 1.0))), K(H + Vector((0, 0, -0.8))), "inout", shake=[(476, 492, 0.06)])
# 9: suv sathidan past burchak
c, t = C(9, 17, 8.0)
cam_move(c, t, *S[9], K(H + Vector((-17.2, -2.6, 0.55))), K(H + Vector((-16.2, -2.2, 0.35))),
         K(H + Vector((-4, 0.2, -0.9))), K(H + Vector((-3, 0.2, -0.9))), "lin")
# 10: manometr (yaqin, fon xira)
c, t = C(10, 50, 2.0)
cam_move(c, t, *S[10], K(gp + Vector((0.18, -0.62, 0.06))), K(gp + Vector((0.06, -0.42, 0.02))),
         K(gp + Vector((0, -0.03, 0))), K(gp + Vector((0, -0.03, 0))), "inout", shake=[(S[10][0], S[10][1], 0.006)])
# 11: muhandis yuzi (bosh suyagiga ergashuvchi nishon)
head_t = empty("josh_head_t"); cc = head_t.constraints.new("COPY_LOCATION"); cc.target = josh; cc.subtarget = "mixamorig:Head"; cc.head_tail = 0.55
c, t = C(11, 50, 2.0, focus=head_t)
c.constraints["Track To"].target = head_t
cam_move(c, t, *S[11], K(JP + Vector((0.55, 1.2, 1.62))), K(JP + Vector((0.25, 0.68, 1.66))), (0, 0, 0), (0, 0, 0), "out",
         tgt_obj_follow=True)
# 12: rentgen panel, keng
c, t = C(12, 30)
cam_move(c, t, *S[12], K(PAN + Vector((-0.55, -2.6, 0.35))), K(PAN + Vector((0.2, -2.0, 0.15))),
         K(PAN + Vector((0, 0, 0))), K(PAN + Vector((0.05, 0, 0.03))), "inout")
# 13: burchakka aylanib yaqinlashish
c, t = C(13, 32, 2.8)
cam_move(c, t, *S[13], K(PAN + Vector((0.95, -1.25, 0.75))), K(PAN + Vector((0.42, -0.62, 0.42))),
         K(PAN + Vector((0.18, 0, 0.18))), K(PAN + Vector((0.24, 0, 0.24))), "inout")
# 14: makro burchak, yoriq; crash zoom
c, t = C(14, 40, 11.0)
cam_move(c, t, S[14][0], CRACK - 1, K(PAN + Vector((0.5, -0.55, 0.36))), K(PAN + Vector((0.42, -0.42, 0.32))),
         K(PAN + Vector((0.25, 0, 0.25))), K(PAN + Vector((0.27, 0, 0.27))), "inout")
cam_move(c, t, CRACK, S[14][1], K(PAN + Vector((0.42, -0.42, 0.32))), K(PAN + Vector((0.5, -0.34, 0.44))),
         K(PAN + Vector((0.29, 0, 0.29))), K(PAN + Vector((0.4, 0, 0.37))), "out", shake=[(CRACK, CRACK + 18, 0.025)],
         lens=(40, 58, "out"))
# 15: dumaloq deraza, aylanma
c, t = C(15, 28)
RP = PAN + Vector((12, 0, 0))
cam_move(c, t, *S[15], K(RP + Vector((1.3, -1.9, -0.4))), K(RP + Vector((-0.9, -1.75, 0.35))),
         K(RP + Vector((0.05, 0, 0))), K(RP + Vector((-0.05, 0, 0))), "inout")
# 16: salon, qiz derazaga qaraydi, kamera orqaga chekinadi
c, t = C(16, 30, 2.8)
cam_move(c, t, *S[16], (MEG_X - 0.72, -1.05, 1.32), (MEG_X - 2.3, -0.15, 1.72),
         (MEG_X - 0.02, -1.33, 1.18), (MEG_X - 0.1, -1.4, 1.1), "inout", lens=(30, 22, "inout"))
for n, c in cams.items():
    sc.timeline_markers.new(c.name, frame=S[n][0]).camera = c
sc.camera = cams[1]

# =================================================================== OSMON YORUG'LIGI
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; env = N.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(200))
w.node_tree.links.new(tc.outputs["Generated"], mp.inputs[0]); w.node_tree.links.new(mp.outputs[0], env.inputs[0])
w.node_tree.links.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); P.link(sun)
sun.data.energy = 4.0; sun.data.angle = R(1.5); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(48), 0, R(-25))

# =================================================================== RENDER
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 12
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", -0.3))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if os.environ.get("DBGCAM"):          # sinov: "x,y,z;tx,ty,tz;lens" erkin kamera
        p_, t_, l_ = os.environ["DBGCAM"].split(";")
        dc = P.link(bpy.data.objects.new("dbgcam", bpy.data.cameras.new("dbgcam"))); dc.data.lens = float(l_)
        dc.location = Vector(map(float, p_.split(",")))
        dc.rotation_euler = (Vector(map(float, t_.split(","))) - dc.location).to_track_quat("-Z", "Y").to_euler()
        sc.timeline_markers.clear(); sc.camera = dc
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True
            bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", "1,1036").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
