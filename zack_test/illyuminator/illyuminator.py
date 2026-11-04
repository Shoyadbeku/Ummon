# "Illyuminatorni sindirsangiz nima bo'ladi?" — Zack D. Films uslubida 54.5 s (1308 kadr, 24 fps, 9:16).
# Sahnalar bitta faylda, turli joylarda: salon (0,0,0), osmon/A320 (2000,0,0), kabina (0,80,0), studiya (0,-120,10).
# Salon, A320 va yordamchilar samolyot/ loyihasidan (samolyot/parts.py).
# Render: OUT=... SAMPLES=8 PCT=45 python -I illyuminator.py --render   (FRAMES=60,98 sinov uchun)
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "samolyot")); sys.path.insert(0, os.path.dirname(HERE))
from mathutils import Vector, Matrix
import parts as P
from parts import R, box, cyl, sphere, empty, key, par, mat, bsdf, vis, cam_move, camera
import mixchar as mc

OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
NF = 1308
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, NF, 24

# kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md)
S = {1: (1, 53), 2: (54, 111), 3: (112, 147), 4: (148, 191), 5: (192, 239), 6: (240, 304), 7: (305, 372),
     8: (373, 444), 9: (445, 514), 10: (515, 570), 11: (571, 624), 12: (625, 696), 13: (697, 775), 14: (776, 825),
     15: (826, 874), 16: (875, 918), 17: (919, 984), 18: (985, 1033), 19: (1034, 1123), 20: (1124, 1201),
     21: (1202, 1256), 22: (1257, NF)}
IMP1 = 98          # bolg'acha oynaga tegadi
BURST = 152        # oyna portlaydi
PUNCH = 1148       # musht oynaga tegadi (sinmaydi)
EMERG = (BURST, S[17][0] - 1)   # favqulodda holat (tuman, qirov, niqoblar)
CAB = Vector((0, 0, 0)); SKY = Vector((2000, 0, 0)); COC = Vector((0, 80, 0)); STU = Vector((0, -120, 10))

def fix_fps(): sc.render.fps = 24     # CLAUDE.md: Mixamo FBX importi sahnani 30 fps ga o'tkazadi

M = dict(
    alu=mat("alu", (0.8, 0.81, 0.83), 0.22, metal=1.0),
    darkglass=mat("darkglass", (0.01, 0.012, 0.016), 0.05, coat=1.0),
    black=mat("black", (0.01, 0.01, 0.01), 0.6),
    fabric=mat("fabric", (0.05, 0.09, 0.2), 0.95),
    cover=mat("cover", (0.85, 0.85, 0.82), 0.8),
    carpet=mat("carpet", (0.12, 0.13, 0.17), 1.0),
    cove=mat("cove", (1.0, 0.85, 0.65), 0.5, emit=6.0),
    steel=mat("steel", (0.32, 0.33, 0.35), 0.45, metal=1.0),
    yellow=mat("yellow", (0.95, 0.72, 0.02), 0.45),
    red=mat("red", (0.75, 0.02, 0.02), 0.35),
    paper=mat("paper", (0.9, 0.9, 0.86), 0.8),
    leather=mat("leather", (0.25, 0.1, 0.04), 0.5),
    screen=mat("screen", (0.01, 0.01, 0.012), 0.15, coat=1.0),
    tube=mat("tube", (0.85, 0.9, 0.9), 0.3, alpha=0.6),
    dark=mat("dark", (0.004, 0.008, 0.02), 1.0, emit=1.0, emit_col=(0.004, 0.01, 0.03)),
)

# --------------------------------------------------------------- qirov (frost): plastik/mato ustida teshikdan tarqaladi
def glass_mat(name, tint=(0.92, 0.96, 1.0), rough=0.02):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = bsdf(m)
    b.inputs["Base Color"].default_value = (*tint, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.5
    return m
M["glass"] = glass_mat("glass"); M["acryl"] = glass_mat("acryl", (0.95, 0.97, 1.0), 0.06)

FROST_R = []          # (material, "FR" qiymat tuguni)
def frost_mat(name, col, rough, hole):
    """Oddiy material + qirov: world pozitsiya teshikdan FR radius ichida bo'lsa oq-ko'k qirov."""
    m = mat(name, col, rough); nt = m.node_tree; g = P.G(nt); b = bsdf(m)
    FR = g.value("FR", 0.0)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    vd = nt.nodes.new("ShaderNodeVectorMath"); vd.operation = "DISTANCE"
    g.L.new(geo.outputs["Position"], vd.inputs[0]); vd.inputs[1].default_value = hole
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0; nz.inputs["Detail"].default_value = 12
    g.L.new(geo.outputs["Position"], nz.inputs["Vector"])
    d = g.add(vd.outputs["Value"], g.mul(nz.outputs["Fac"], 0.35))
    f = g.maprange(g.sub(FR.outputs[0], d), 0.0, 0.08, 0.0, 1.0)
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 140
    g.L.new(geo.outputs["Position"], vor.inputs["Vector"])
    cr = g.maprange(vor.outputs["Distance"], 0.0, 0.35, 1.0, 0.75)
    frost_col = g.mixcol(cr, (0.62, 0.72, 0.85), (0.95, 0.98, 1.0))
    g.L.new(g.mixcol(f, col, frost_col), b.inputs["Base Color"])
    g.L.new(g.maprange(f, 0, 1, rough, 0.35), b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = 0.002
    g.L.new(g.mul(f, 0.6), bp.inputs["Strength"]); g.L.new(vor.outputs["Distance"], bp.inputs["Height"])
    g.L.new(bp.outputs[0], b.inputs["Normal"])
    FROST_R.append(m)
    return m

# =================================================================== SALON (A320 ichi; samolyot.py dan)
# o'q X bo'ylab, oldi -X; chap (deraza) tomoni -Y. Pol z=0, fyuzelyaj markazi z=0.6, ichki radius 1.85
RC, ZC = 1.85, 0.6
ROWS = [0.12 + 0.82 * (k - 6) for k in range(15)]
MEG_X = ROWS[6]
PHI = math.asin((1.05 - ZC) / RC)
def basis(X, Y, Z, pos):
    m = Matrix.Identity(4)
    for i, v in enumerate((X, Y, Z, pos)):
        for j in range(3): m[j][i] = v[j]
    return m
def win_frame(side):
    d = Vector((0, side * math.cos(PHI), math.sin(PHI))); t = Vector((0, -side * math.sin(PHI), math.cos(PHI)))
    return d, t, t.cross(d)
# Meganning oynasi (sinadigan)
HD, HT, HW = win_frame(-1)
HOLE = Vector((MEG_X - 0.28, 0, ZC)) + HD * RC      # teshik markazi (ichki qobiq sirtida)
HOLE_OUT = HOLE + HD * 0.1

M["plastic"] = frost_mat("plastic", (0.86, 0.85, 0.82), 0.45, HOLE)
M["fabric"] = frost_mat("fabric_f", (0.05, 0.09, 0.2), 0.95, HOLE)
M["cover"] = frost_mat("cover_f", (0.85, 0.85, 0.82), 0.8, HOLE)

def cabin_tube(name, r, x0, x1, m, nx=40):
    bm = bmesh.new(); seg = 96; xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]
    rings = [[bm.verts.new((x, r * math.cos(2 * math.pi * j / seg), ZC + r * math.sin(2 * math.pi * j / seg))) for j in range(seg)] for x in xs]
    for i in range(len(xs) - 1):
        for j in range(seg):
            k = (j + 1) % seg; bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]))
    o = P.mesh_obj(name, bm, m); P.smooth(o); return o
shell = cabin_tube("cabin_shell", RC, -7, 7, M["plastic"])
sol = shell.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.08

# tashqi korpus (5-kadr va boshqa tashqi ko'rinishlar uchun): oq bo'yoq, deraza ostida ko'k chiziq
skin_m = bpy.data.materials.new("skin"); skin_m.use_nodes = True; nt = skin_m.node_tree; g = P.G(nt); b = bsdf(skin_m)
geo = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); g.L.new(geo.outputs["Position"], sp.inputs[0])
z = sp.outputs[2]
blue = g.mul(g.maprange(z, 0.6, 0.62, 0, 1), g.maprange(z, 0.76, 0.78, 1, 0))
belly = g.maprange(z, 0.05, 0.0, 0, 1)
c_ = g.mixcol(blue, (0.92, 0.93, 0.94), (0.02, 0.08, 0.32)); c_ = g.mixcol(belly, c_, (0.55, 0.57, 0.6))
g.L.new(c_, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.22; b.inputs["Coat Weight"].default_value = 0.6
br = nt.nodes.new("ShaderNodeTexBrick"); g.L.new(geo.outputs["Position"], br.inputs["Vector"]); br.inputs["Scale"].default_value = 0.45
br.inputs["Mortar Size"].default_value = 0.004; br.inputs["Brick Width"].default_value = 1.8; br.inputs["Row Height"].default_value = 0.7
bpn = nt.nodes.new("ShaderNodeBump"); bpn.inputs["Strength"].default_value = 0.2; bpn.inputs["Distance"].default_value = 0.003
g.L.new(br.outputs["Fac"], bpn.inputs["Height"]); g.L.new(bpn.outputs[0], b.inputs["Normal"])
skin = cabin_tube("outer_skin", RC + 0.1, -40, 40, skin_m, nx=120)

cut_bm = bmesh.new(); win_mats = []
for side in (-1, 1):
    d, t, w = win_frame(side)
    for x in ROWS:
        wx = x - 0.28
        c = Vector((wx, 0, ZC)) + d * RC
        r = bmesh.ops.create_cone(cut_bm, cap_ends=True, segments=32, radius1=1, radius2=1, depth=1)
        bmesh.ops.transform(cut_bm, matrix=basis(w, t, d, c) @ Matrix.Diagonal((0.125, 0.18, 0.5, 1)), verts=r["verts"])
        win_mats.append((c, w, t, d, side, wx))
    for k in list(range(-30, -6)) + list(range(9, 45)):        # tashqi korpusdagi qo'shimcha derazalar
        wx = 0.12 + 0.82 * (k - 6) - 0.28
        if -7.2 < wx < 7.2: continue
        c = Vector((wx, 0, ZC)) + d * (RC + 0.1)
        r = bmesh.ops.create_cone(cut_bm, cap_ends=True, segments=24, radius1=1, radius2=1, depth=0.4)
        bmesh.ops.transform(cut_bm, matrix=basis(w, t, d, c) @ Matrix.Diagonal((0.125, 0.18, 0.5, 1)), verts=r["verts"])
cutter = P.mesh_obj("win_cutter", cut_bm)
for o in (shell, skin):
    bo = o.modifiers.new("win", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cutter; bo.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    for mod in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter, do_unlink=True)
# qo'shimcha tashqi derazalar ichi: qorong'i oyna
for side in (-1, 1):
    d, t, w = win_frame(side)
    for k in list(range(-30, -6)) + list(range(9, 45)):
        wx = 0.12 + 0.82 * (k - 6) - 0.28
        if -7.2 < wx < 7.2: continue
        c = Vector((wx, 0, ZC)) + d * (RC + 0.05)
        bmw = bmesh.new(); bmesh.ops.create_cone(bmw, cap_ends=True, segments=24, radius1=1, radius2=1, depth=1)
        bmesh.ops.transform(bmw, matrix=basis(w, t, d, c) @ Matrix.Diagonal((0.13, 0.185, 0.01, 1)), verts=bmw.verts)
        P.mesh_obj("dark_win", bmw, M["darkglass"])
def is_cover(o):
    """ichki oq qopqoq: import qayta nomlaydi (Circle.008...), shuning uchun material nomi bo'yicha aniqlanadi"""
    return any(m and m.name.startswith("Circle.002") for m in o.data.materials)
# illyuminator ramkasi (BlenderKit 7250f009): Blender'da X = en, Y = bo'y, Z = qalinlik
for c, w, t, d, side, wx in win_mats:
    root, new = P.import_gltf(BK + "7250f009_u.glb", name="bezel")
    for o in new:
        if o.type == "MESH" and (is_cover(o) or max(o.dimensions) > 1.0): bpy.data.objects.remove(o, do_unlink=True)
    root.matrix_world = basis(w, t, d, c - d * 0.085) @ Matrix.Diagonal((0.95, 0.95, 1, 1))
box("cabin_floor", (14, 3.6, 0.1), (0, 0, -0.05), M["carpet"])
box("aisle", (14, 0.5, 0.012), (0, 0, 0.006), mat("aislecarpet", (0.25, 0.05, 0.06), 1.0))
for side in (-1, 1):
    box("bins", (14, 0.72, 0.42), (0, side * 1.22, 1.86), M["plastic"], 0.04, rot=(side * -18, 0, 0))
    box("cove", (14, 0.03, 0.03), (0, side * 0.86, 2.08), M["cove"])
    box("sidewall_lo", (14, 0.05, 0.42), (0, side * 1.72, 0.21), M["plastic"])
for x in (-7.0, 7.0): box("bulkhead", (0.1, 3.8, 3.0), (x, 0, 1.0), M["plastic"])
def seat(x, y):
    box("seat_pan", (0.48, 0.46, 0.12), (x + 0.02, y, 0.44), M["fabric"], 0.04)
    box("seat_back", (0.1, 0.46, 0.62), (x + 0.27, y, 0.79), M["fabric"], 0.04, rot=(0, -10, 0))
    box("seat_head", (0.12, 0.4, 0.18), (x + 0.31, y, 1.0), M["cover"], 0.03, rot=(0, -10, 0))
    box("seat_leg", (0.05, 0.05, 0.38), (x, y, 0.19), M["steel"])
    box("seat_screen", (0.012, 0.2, 0.13), (x + 0.33, y, 0.84), M["screen"], 0.004, rot=(0, -10, 0))
    for dy in (-0.25, 0.25): box("arm", (0.42, 0.05, 0.05), (x + 0.05, y + dy, 0.64), M["plastic"], 0.015)
for x in ROWS:
    for y in (-1.3, -0.82, -0.34, 0.34, 0.82, 1.3): seat(x, y)
ceil_l = bpy.data.objects.new("cabin_light", bpy.data.lights.new("cabin_light", "AREA")); P.link(ceil_l)
ceil_l.data.shape = "RECTANGLE"; ceil_l.data.size = 10; ceil_l.data.size_y = 0.6; ceil_l.data.energy = 900
ceil_l.data.color = (1.0, 0.88, 0.72); ceil_l.location = (0, 0, 2.3)
fill = bpy.data.objects.new("win_fill", bpy.data.lights.new("win_fill", "AREA")); P.link(fill)
fill.data.size = 0.6; fill.data.energy = 25; fill.data.color = (0.85, 0.92, 1.0)
fill.location = (MEG_X - 0.3, -1.55, 1.15); fill.rotation_euler = (R(-80), 0, 0); fill.visible_camera = False; fill.visible_glossy = False
# favqulodda holat: chiroq miltillaydi, sovuq ko'k tus
for f, e, col in ((1, 900, (1, .88, .72)), (BURST - 1, 900, (1, .88, .72)), (BURST, 150, (1, .88, .72)), (BURST + 2, 1100, (1, .88, .72)),
                  (BURST + 4, 80, (1, .88, .72)), (BURST + 7, 650, (.8, .88, 1)), (EMERG[1], 650, (.8, .88, 1)),
                  (EMERG[1] + 1, 900, (1, .88, .72))):
    ceil_l.data.energy = e; ceil_l.data.color = col
    ceil_l.data.keyframe_insert("energy", frame=f); ceil_l.data.keyframe_insert("color", frame=f)
for fc in P.all_fcurves(ceil_l.data):
    for k in fc.keyframe_points: k.interpolation = "CONSTANT"

# --------------------------------------------------------------- sinadigan oyna, yoriqlar, parchalar
pane_fr = empty("pane_frame"); pane_fr.matrix_world = basis(HW, HT, HD, HOLE + HD * 0.03)
bmp = bmesh.new(); bmesh.ops.create_cone(bmp, cap_ends=True, segments=48, radius1=1, radius2=1, depth=1)
bmesh.ops.scale(bmp, vec=(0.13, 0.185, 0.008), verts=bmp.verts)
pane = P.mesh_obj("pane", bmp, M["glass"]); P.smooth(pane); pane.parent = pane_fr
crack_m = bpy.data.materials.new("crack_glass"); crack_m.use_nodes = True; nt = crack_m.node_tree; g = P.G(nt); b = bsdf(crack_m)
PROG = g.value("PROG", 0.0).outputs[0]
uvn = nt.nodes.new("ShaderNodeUVMap"); spx = nt.nodes.new("ShaderNodeSeparateXYZ"); g.L.new(uvn.outputs[0], spx.inputs[0])
b.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1); b.inputs["Roughness"].default_value = 0.3
b.inputs["Emission Color"].default_value = (0.9, 0.95, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.6
g.L.new(g.math("LESS_THAN", spx.outputs[0], PROG), b.inputs["Alpha"])
rnd = random.Random(5); IMPACT = (0.03, -0.04)
for i in range(14):
    a = 2 * math.pi * i / 14 + rnd.uniform(-0.2, 0.2)
    # 3x kattalikda yasab, 1/3 ga kichraytiriladi: crack_strip ning 1.2 sm zigzagi 4 mm bo'ladi
    cr = P.crack_strip(f"crack{i}", crack_m, (IMPACT[0] * 3, IMPACT[1] * 3), (math.cos(a), math.sin(a)), length=rnd.uniform(0.27, 0.66),
                       width=0.0036, seed=i + 3, segs=30)
    cr.parent = pane_fr; cr.location = (0, 0, -0.0045); cr.scale = (1 / 3, 1 / 3, 1)
for k, rr_ in enumerate((0.03, 0.06, 0.1)):        # o'rgimchak to'ri halqalari
    bmr = bmesh.new(); uv = bmr.loops.layers.uv.new(); n = 40; vs = []
    for j in range(n + 1):
        a = 2 * math.pi * j / n; q = rr_ * (1 + rnd.uniform(-0.15, 0.15))
        for s_ in (-1, 1):
            vs.append(bmr.verts.new((IMPACT[0] + (q + s_ * 0.0012) * math.cos(a), IMPACT[1] + (q + s_ * 0.0012) * math.sin(a) * 1.2, 0)))
    for j in range(n):
        f = bmr.faces.new((vs[2 * j], vs[2 * j + 1], vs[2 * j + 3], vs[2 * j + 2]))
        for lp in f.loops: lp[uv].uv = (0.15 + 0.25 * k, 0)
    o = P.mesh_obj(f"crack_ring{k}", bmr, crack_m); o.parent = pane_fr; o.location = (0, 0, -0.0045)
for f, v in ((1, 0), (IMP1 - 1, 0), (IMP1, 0.35), (IMP1 + 6, 0.5), (S[3][0], 0.5), (S[3][1], 1.0), (S[18][0] - 1, 1.0), (S[18][0], 0.0)):
    P.key_value(crack_m, "PROG", f, v)
for fc in P.all_fcurves(crack_m.node_tree):
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
# 3-kadr: oyna tashqariga bo'rtadi (tebranish)
for f, s_ in ((S[3][0], 0.0), (S[3][0] + 12, 0.004), (S[3][0] + 16, 0.001), (S[3][0] + 24, 0.006), (BURST - 1, 0.009)):
    key(pane, f, loc=(0, 0, s_))
vis(pane_fr, [(1, BURST - 1), (S[18][0], NF)])
# parchalar va qog'ozlar: salondan teshikka, keyin tashqariga va orqaga (+X) uchadi
deb_root = empty("debris_root")
rnd = random.Random(21); DEB = []
def fly(o, tb, p0, t_in, out_v, spin, f_end, shrink_in=False):
    """tb: tug'ilish kadri; p0 -> teshik (t_in kadr, tezlanib), keyin tashqariga out_v va oqim bilan orqaga."""
    hole_in = HOLE - HD * 0.02
    for f in range(max(1, tb - 1), f_end + 1, 2):
        if f < tb:
            key(o, f, loc=tuple(p0), scale=(0, 0, 0)); continue
        tt = f - tb
        if tt <= t_in:
            u = (tt / max(1, t_in)) ** 2.2; p = p0.lerp(hole_in, u)
        else:
            s_ = (tt - t_in) / 24.0
            p = hole_in + HD * (out_v * s_ + 0.6) + Vector((1, 0, 0)) * (14 * s_ * s_ + 1.5 * s_)
        sc_ = 1.0
        if s_out_far(p): sc_ = 0.0
        key(o, f, loc=tuple(p), rot=tuple(Vector(spin) * tt), scale=(sc_, sc_, sc_))
def s_out_far(p): return (p - HOLE).length > 30
for i in range(70):          # shisha parchalari (portlash)
    sz = rnd.uniform(0.008, 0.03)
    bm_ = bmesh.new(); vv = [bm_.verts.new((rnd.uniform(-sz, sz), rnd.uniform(-sz, sz), 0)) for _ in range(3)]; bm_.faces.new(vv)
    o = P.mesh_obj(f"shard{i}", bm_, M["glass"]); o.parent = deb_root
    p0 = HOLE + HD * 0.03 + HW * rnd.uniform(-0.12, 0.12) + HT * rnd.uniform(-0.16, 0.16)
    fly(o, BURST, p0, 0, rnd.uniform(3, 9), (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)), S[5][1])
for i in range(46):          # qog'ozlar, salfetkalar
    o = box(f"paper{i}", (rnd.uniform(0.06, 0.14), rnd.uniform(0.05, 0.1), 0.002), (0, 0, 0), M["paper"]); o.parent = deb_root
    tb = BURST + rnd.randint(0, 80)
    p0 = Vector((MEG_X + rnd.uniform(-2.5, 2.5), rnd.uniform(-1.2, 1.2), rnd.uniform(0.3, 1.6)))
    fly(o, tb, p0, rnd.randint(8, 22), rnd.uniform(2, 5), (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6)), S[6][1])
vis(deb_root, [(BURST, S[6][1])])
# telefon va sumka (6-kadr)
phone = box("phone", (0.075, 0.15, 0.009), (0, 0, 0), M["black"], 0.004)
phs = box("phone_scr", (0.068, 0.14, 0.002), (0, 0, 0.0052), mat("phscr", (0.1, 0.3, 0.6), 0.1, emit=3.0)); phs.parent = phone
bag = box("bag", (0.36, 0.14, 0.26), (0, 0, 0), M["leather"], 0.02)
strap = cyl("strap", 0.012, 0.32, (0, 0, 0.16), M["black"], rot=(90, 0, 0), verts=8); strap.parent = bag
def path_keys(o, keys):
    for f, p, r_ in keys: key(o, f, loc=tuple(p), rot=r_)
F6 = S[6][0]
X4 = ROWS[4]      # bo'sh qator: telefon o'rindiqda, sumka yo'lakda
path_keys(phone, [(1, Vector((X4 + 0.02, -0.82, 0.512)), (0, 0, 20)), (F6 + 2, Vector((X4 + 0.02, -0.82, 0.512)), (0, 0, 20)),
                  (F6 + 16, Vector((X4 + 0.05, -1.15, 0.53)), (5, 10, 110)), (F6 + 28, Vector((X4 + 0.55, -1.45, 1.05)), (80, 60, 300)),
                  (F6 + 38, HOLE - HD * 0.05, (160, 120, 520)), (F6 + 40, HOLE + HD * 0.6 + Vector((0.5, 0, 0)), (200, 140, 600))])
path_keys(bag, [(1, Vector((X4 - 0.38, -0.05, 0.13)), (0, 0, 70)), (F6 + 8, Vector((X4 - 0.38, -0.05, 0.13)), (0, 0, 70)),
                (F6 + 24, Vector((X4 - 0.3, -0.45, 0.25)), (-10, 25, 40)), (F6 + 42, Vector((X4 + 0.3, -1.0, 1.1)), (-60, 70, -10)),
                (F6 + 56, Vector((MEG_X - 0.55, -1.5, 1.08)), (-90, 110, -40)), (S[6][1], Vector((MEG_X - 0.45, -1.6, 1.05)), (-95, 115, -45))])
for o in (phone, bag):
    for fc in P.all_fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "QUAD"
vis(phone, [(S[6][0], S[6][0] + 39)]); vis(bag, [S[6]])
# bug' oqimi (tashqaridan, 5-kadr) — hajmli konus, oqim orqaga bukiladi
def vol_mat(name, dens, col=(0.95, 0.97, 1.0), noise=True, scale=3.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1)
    D = N.new("ShaderNodeValue"); D.name = D.label = "DENS"; D.outputs[0].default_value = dens
    if noise:
        nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 4
        nz.name = "NZ"
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.75
        L.new(nz.outputs["Fac"], mr.inputs["Value"])
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(mr.outputs["Result"], mul.inputs[0]); L.new(D.outputs[0], mul.inputs[1])
        L.new(mul.outputs[0], pv.inputs["Density"])
        P.key_input(nz.inputs["W"], 1, 0.0); P.key_input(nz.inputs["W"], NF, 160.0)
        for fc in P.all_fcurves(nt):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"
    else:
        L.new(D.outputs[0], pv.inputs["Density"])
    L.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
    return m
jet_m = vol_mat("jet", 18.0, col=(0.88, 0.9, 0.93), scale=5.0)
bmj = bmesh.new(); nseg = 30; rings = []
for i in range(nseg + 1):
    s_ = i / nseg; r_ = 0.1 + 0.5 * s_ ** 0.8; ctr = HD * (2.6 * s_) + Vector((1, 0, 0)) * (3.2 * s_ ** 2)
    rings.append([bmj.verts.new(HOLE_OUT - HD * 0.05 + ctr + HW * (r_ * math.cos(2 * math.pi * j / 16)) + HT * (r_ * math.sin(2 * math.pi * j / 16)))
                  for j in range(16)])
for i in range(nseg):
    for j in range(16):
        k = (j + 1) % 16; bmj.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
bmj.faces.new(rings[0][::-1]); bmj.faces.new(rings[-1]); bmesh.ops.recalc_face_normals(bmj, faces=bmj.faces)
jet = P.mesh_obj("jet", bmj, jet_m)
vis(jet, [(BURST, S[5][1])])
# salon tumani
fog_m = vol_mat("fog", 0.0, noise=True, scale=1.4)
fog = box("fog", (13.8, 3.5, 2.6), (0, 0, 1.25), fog_m)
for f, v in ((1, 0), (BURST, 0), (BURST + 3, 0.5), (BURST + 30, 0.18), (S[9][0], 0.15), (S[9][1], 0.9), (S[10][0], 0.35),
             (S[16][0], 0.35), (S[17][0], 0.0)):
    P.key_value(fog_m, "DENS", f, v)
vis(fog, [(BURST, S[16][1])])
# qirov radiusi
for m_ in FROST_R:
    for f, v in ((1, 0), (S[8][0], 0.0), (S[8][1], 1.6), (S[16][1], 1.8), (S[17][0], 0)):
        P.key_value(m_, "FR", f, v)
    for fc in P.all_fcurves(m_.node_tree):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
# o'rindiq ekrani: harorat
scr_pos = Vector((ROWS[5] + 0.33 + 0.012, -1.3, 0.84))
temp_txt = bpy.data.curves.new("temp", "FONT"); temp_txt.body = "+22°C"; temp_txt.align_x = "CENTER"; temp_txt.align_y = "CENTER"
temp_txt.size = 0.045; temp_txt.extrude = 0.0005
tt_o = P.link(bpy.data.objects.new("temp_txt", temp_txt)); tt_o.location = scr_pos + Vector((0.004, 0, 0.005))
tt_o.rotation_euler = (R(90), R(-10), R(90))
tmat = mat("tempm", (1, 1, 1), 0.3, emit=6.0); temp_txt.materials.append(tmat)
TEMP_K = [(1, 22), (S[8][0] + 4, 22), (S[8][1] - 14, -50), (S[17][0] - 1, -50), (S[17][0], 22)]
def temp_at(f):
    for (f0, v0), (f1, v1) in zip(TEMP_K, TEMP_K[1:]):
        if f0 <= f <= f1: return v0 + (v1 - v0) * (f - f0) / max(1, f1 - f0)
    return TEMP_K[-1][1]
for f, c_ in ((1, (0.3, 1, 0.4)), (S[8][0] + 10, (0.3, 1, 0.4)), (S[8][0] + 30, (0.3, 0.7, 1)), (S[8][1] - 14, (0.2, 0.55, 1))):
    P.key_input(bsdf(tmat).inputs["Emission Color"], f, (*c_, 1))
def _temp(scene, *a):
    v = int(round(temp_at(scene.frame_current)))
    temp_txt.body = ("+" if v > 0 else ("-" if v < 0 else "")) + f"{abs(v)}°C"
bpy.app.handlers.frame_change_pre.append(_temp)

# --------------------------------------------------------------- kislorod niqoblari
def mask_mesh(name):
    """sariq niqob: yarim shar (ochiq tomoni -Z), rezina tasma; origin = niqob markazi."""
    rootm = empty(name)
    cup = sphere(name + "_cup", 0.055, (0, 0, -0.01), M["yellow"], scale=(1, 1, 0.75), seg=20); cup.parent = rootm
    bmc = bmesh.new(); bmesh.ops.create_cone(bmc, cap_ends=False, segments=24, radius1=0.06, radius2=0.06, depth=0.012)
    rim = P.mesh_obj(name + "_rim", bmc, M["yellow"]); rim.parent = rootm; rim.location = (0, 0, -0.045)
    bag_ = sphere(name + "_bag", 0.05, (0, -0.1, 0.04), mat(name + "_bm", (0.92, 0.85, 0.5), 0.6, alpha=0.8), scale=(0.8, 1.2, 0.7), seg=12)
    bag_.parent = rootm
    return rootm
MASKS = []
anchors = []
rnd = random.Random(8)
for x in ROWS[3:11]:
    for y in (-1.3, -0.82, -0.34, 0.34, 0.82, 1.3):
        side = -1 if y < 0 else 1
        anc = Vector((x - 0.3, y * 0.88 + side * 0.02, 1.64 - (abs(y) - 0.34) * 0.12))
        flap = box("flap", (0.24, 0.15, 0.01), tuple(anc + Vector((0, 0, 0.006))), M["plastic"])
        mk = mask_mesh(f"mask_{x:.2f}_{y:.2f}")
        hang = anc + Vector((0, 0, -0.42 - rnd.uniform(0, 0.06)))
        f0 = S[10][0] + 4 + rnd.randint(0, 8)
        key(mk, 1, loc=tuple(anc - Vector((0, 0, 0.03))), rot=(0, -90, 0))
        key(mk, f0, loc=tuple(anc - Vector((0, 0, 0.03))), rot=(0, -90, 0))
        key(flap, 1, loc=tuple(anc + Vector((0, 0, 0.006))), rot=(0, 0, 0)); key(flap, f0 - 1, rot=(0, 0, 0))
        key(flap, f0 + 3, loc=tuple(anc + Vector((0, side * 0.07, -0.07))), rot=(side * 80, 0, 0))
        vis(flap, [(S[10][0], EMERG[1])])
        for i in range(0, 44, 2):          # tushish + so'nuvchi sakrash
            tt = i / 24
            dz = -(hang - anc).length * min(1, (tt / 0.28) ** 2) if tt < 0.28 else -(hang - anc).length + 0.07 * math.exp(-tt * 4) * math.cos(tt * 28)
            key(mk, f0 + i, loc=tuple(anc + Vector((0.01 * math.sin(tt * 9), 0, dz - 0.03))),
                rot=(8 * math.sin(tt * 11) * math.exp(-tt * 2), -90 + 12 * math.sin(tt * 7) * math.exp(-tt * 2), 0))
        for f in range(f0 + 46, EMERG[1], 24):
            key(mk, f, loc=tuple(hang + Vector((0.015 * math.sin(f * 0.2), 0.01 * math.cos(f * 0.17), 0))), rot=(3 * math.sin(f * 0.13), -90, 0))
        tb_ = cyl("mtube", 0.005, 1.0, tuple(anc), M["tube"], verts=8, bevel=False)
        tb_.data.transform(Matrix.Translation((0, 0, -0.5)))
        st = tb_.constraints.new("STRETCH_TO"); st.target = mk; st.rest_length = 1.0
        vis(mk, [(S[10][0], EMERG[1])]); vis(tb_, [(S[10][0], EMERG[1])])
        MASKS.append((mk, x, y, hang, flap))

# =================================================================== QAHRAMONLAR
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
def A(f):
    a = mc.load_action(f, True); fix_fps(); return a
def CH(n, f):
    r = mc.load_character(n, f); fix_fps(); return r
groot, girl, gm = CH("girl", "Megan.fbx")
kroot, kate, km = CH("kate", "Kate.fbx")
droot, dav, dm = CH("david", "David.fbx")
jroot, josh, jm = CH("josh", "Josh.fbx")
proot, pete, pm = CH("pete", "Pete.fbx")
tame(gm + km + dm + jm + pm)
groot.location = (MEG_X + 0.08, -1.3, 0.02); groot.rotation_euler.z = R(-90)
kroot.location = (MEG_X + 0.08, -0.82, 0.02); kroot.rotation_euler.z = R(-90)
droot.location = (ROWS[8] + 0.08, 0.82, 0.02); droot.rotation_euler.z = R(-90)
# Megan
SI5, SI3 = A("Sitting_Idle_5.fbx"), A("Sitting_Idle_3.fbx")
JOS = A("Jostled_Passenger.fbx")
mc.add_strip(girl, SI5, -20, repeat=12.0, blend=0)
mc.add_strip(girl, JOS, BURST - 2, repeat=6.0, blend=3)
mc.add_strip(girl, A("Sitting_Disbelief_3.fbx"), S[11][0] - 30, blend=6)
mc.add_strip(girl, A("Knocked_Unconscious.fbx"), S[12][0] - int(os.environ.get("KU_OFF", 40)), blend=0)
mc.add_strip(girl, SI5, S[13][0] - 2, repeat=2.0, blend=0)
mc.add_strip(girl, SI3, S[17][0] - 10, repeat=1.0, blend=0)
mc.add_strip(girl, SI5, S[18][0] - 1, repeat=3.0, blend=0)
mc.add_strip(girl, A("Sitting_Rubbing_Arm.fbx"), PUNCH + 12, blend=8)
mc.add_strip(girl, SI5, S[21][0] - 1, repeat=2.0, blend=0)
# Kate
mc.add_strip(kate, SI5, -60, repeat=12.0, blend=0)
mc.add_strip(kate, JOS, BURST, repeat=6.0, blend=3)
mc.add_strip(kate, A("Knocked_Unconscious.fbx"), S[11][0] - 30, blend=4)
mc.add_strip(kate, SI3, S[17][0] - 30, repeat=2.0, blend=0)
mc.add_strip(kate, SI5, S[18][0] - 1, repeat=3.0, blend=0)
# David (orqa qatorda)
mc.add_strip(dav, SI5, -80, repeat=12.0, blend=0)
mc.add_strip(dav, JOS, BURST + 1, repeat=8.0, blend=3)
mc.add_strip(dav, SI5, S[17][0] - 1, repeat=3.0, blend=0)
# Josh — yo'lakda turibdi, deraza tomon tortiladi
jroot.location = (ROWS[5] - 0.05, 0.05, 0.0); jroot.rotation_euler.z = R(float(os.environ.get("JROT", 0)))
# Edge_Slip: sirpanib muvozanatni yo'qotadi (bosh -Y tomonga, deraza tomon); harakat 0.55 m baland chetda yozilgan
mc.add_strip(josh, A("Edge_Slip.fbx"), S[7][0] - int(os.environ.get("JOFF", 2)), speed=1.0, blend=0)
for f, y in ((S[7][0], 0.05), (S[7][0] + 12, -0.02), (S[7][1], -0.3)):
    key(jroot, f, loc=(ROWS[5] - 0.05, y, -0.55))
vis(jroot, [S[7]])

# qo'llar: IK (bolg'acha, musht, niqob)
def arm_ik(arm, side, name):
    tgt = empty(f"{name}_{side}_ik")
    c = arm.pose.bones[f"mixamorig:{side}ForeArm"].constraints.new("IK")
    c.target = tgt; c.use_tail = True; c.chain_count = 2; c.influence = 0.0
    return tgt, c
def key_inf(c, pairs):
    for f, v in pairs: c.influence = v; c.keyframe_insert("influence", frame=f)
L_T, L_IK = arm_ik(girl, "Left", "girl")
R_T, R_IK = arm_ik(girl, "Right", "girl")
SH_L = Vector((MEG_X + 0.08, -1.48, 1.12))
WIN_IN = HOLE - HD * 0.11
# 2-kadr: bolg'acha bilan zarba
for f, p in ((S[2][0], SH_L + Vector((-0.22, -0.02, -0.25))), (S[2][0] + 22, SH_L + Vector((0.12, -0.04, 0.24))),
             (IMP1 - 5, SH_L + Vector((0.16, -0.02, 0.28))), (IMP1, WIN_IN + HW * 0.03), (IMP1 + 4, WIN_IN - HD * 0.06 + Vector((0.02, 0, -0.02))),
             (S[3][0], SH_L + Vector((-0.2, 0.05, -0.1)))):
    key(L_T, f, loc=tuple(p))
# 20-kadr: musht
for f, p in ((S[20][0], SH_L + Vector((-0.2, 0.02, -0.2))), (PUNCH - 14, SH_L + Vector((0.14, -0.02, 0.1))),
             (PUNCH - 4, SH_L + Vector((0.17, -0.0, 0.12))), (PUNCH, WIN_IN + HW * 0.02), (PUNCH + 3, WIN_IN - HD * 0.1),
             (PUNCH + 12, SH_L + Vector((-0.15, 0.1, -0.15)))):
    key(L_T, f, loc=tuple(p))
key_inf(L_IK, [(1, 0), (S[2][0] - 1, 0), (S[2][0], 1), (S[3][0] + 2, 1), (S[3][0] + 3, 0), (S[20][0] - 1, 0), (S[20][0], 1),
               (PUNCH + 10, 1), (PUNCH + 16, 0)])
hammer = empty("hammer")
hh = cyl("hammer_handle", 0.014, 0.16, (0, 0, 0), M["red"], verts=12); hh.parent = hammer
hd_ = cyl("hammer_head", 0.012, 0.09, (0, 0, 0.085), M["steel"], rot=(0, 90, 0), verts=12); hd_.parent = hammer
for s_ in (-1, 1):
    tip = P.mesh_obj("hammer_tip", (lambda bm_: (bmesh.ops.create_cone(bm_, cap_ends=True, segments=10, radius1=0.012, radius2=0.0, depth=0.03), bm_)[1])(bmesh.new()), M["steel"])
    tip.parent = hammer; tip.location = (s_ * 0.06, 0, 0.085); tip.rotation_euler = (0, R(s_ * 90), 0)
cc = hammer.constraints.new("CHILD_OF"); cc.target = girl; cc.subtarget = "mixamorig:LeftHand"
cc.use_scale_x = cc.use_scale_y = cc.use_scale_z = False; cc.set_inverse_pending = False
hammer.location = (0, 0.07, 0.02); hammer.rotation_euler = (R(float(os.environ.get("HRX", 90))), 0, 0)
vis(hammer, [(S[2][0], S[3][1])])
# barmoqlarni musht qilib bukish (TRANSFORM)
fist = empty("fist_ctl")
for fn in ("Index", "Middle", "Ring", "Pinky"):
    for k in (1, 2, 3):
        pb = girl.pose.bones.get(f"mixamorig:LeftHand{fn}{k}")
        if not pb: continue
        c = pb.constraints.new("TRANSFORM"); c.target = fist; c.map_from = "LOCATION"; c.map_to = "ROTATION"
        c.from_max_x = 1.0; c.to_max_x_rot = R(float(os.environ.get("FIST", 75))); c.owner_space = "LOCAL"; c.target_space = "WORLD"
        c.mix_mode_rot = "AFTER"
for f, v in ((1, 0), (S[2][0], 1), (S[3][1], 1), (S[4][0], 0), (S[20][0] - 1, 0), (S[20][0], 1), (PUNCH + 14, 1), (PUNCH + 20, 0)):
    key(fist, f, loc=(v, 0, 0))
P.set_interp(fist, "CONSTANT")
# bosh qarashi
look = empty("girl_look")
LKC = []
for bn, inf in (("mixamorig:Neck", 0.35), ("mixamorig:Head", 0.6)):
    c = girl.pose.bones[bn].constraints.new("DAMPED_TRACK"); c.target = look; c.track_axis = "TRACK_Z"; LKC.append((c, inf))
def look_at(f, p, w=1.0):
    key(look, f, loc=tuple(p))
    for c, inf in LKC: c.influence = inf * w; c.keyframe_insert("influence", frame=f)
look_at(1, WIN_IN, 1); look_at(S[3][1], WIN_IN, 1); look_at(BURST - 1, WIN_IN, 1); look_at(BURST + 6, WIN_IN, 0)
look_at(S[11][0], WIN_IN, 0); look_at(S[13][0], Vector((MEG_X - 0.6, -1.3, 1.25)), 0.4); look_at(S[14][0] - 4, Vector((MEG_X - 0.6, -1.3, 1.25)), 0.4)
look_at(S[14][0] + 4, Vector((MEG_X - 0.3, -0.7, 1.0)), 0.8); look_at(S[14][1], Vector((MEG_X - 0.3, -0.7, 1.0)), 0.8)
look_at(S[17][0], Vector((MEG_X - 1.0, -1.1, 1.25)), 0.2); look_at(S[18][0], WIN_IN, 0.8); look_at(S[20][0], WIN_IN, 1.0)
look_at(PUNCH + 16, WIN_IN, 0.0); look_at(S[21][0], Vector((MEG_X - 1.2, -0.3, 1.3)), 0.7); look_at(S[21][0] + 18, Vector((MEG_X - 1.2, -0.3, 1.3)), 0.7)
look_at(S[21][1] - 8, WIN_IN + Vector((0, -0.5, 0)), 1.0)
# Meganning va Keytning niqoblari: osilgan joyidan yuzga (COPY_TRANSFORMS, ta'sir kaliti)
def face_target(arm, name):
    ft = empty(name)
    c = ft.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:Head"
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.set_inverse_pending = False
    ft.location = (0, float(os.environ.get("FACE_Y", 0.105)), float(os.environ.get("FACE_Z", 0.1)))
    return ft
def nearest_mask(x, y): return min(MASKS, key=lambda m: abs(m[1] - x) + abs(m[2] - y))
mg = nearest_mask(MEG_X, -1.3)[0]; mk_k = nearest_mask(MEG_X, -0.82)[0]
for mk, arm, n, (f0, f1, f2, f3) in ((mg, girl, "gface", (S[13][0] + 8, S[13][0] + 40, S[17][0] + 8, S[17][0] + 30)),
                                     (mk_k, kate, "kface", (S[14][0] + 6, S[14][0] + 34, S[17][0] - 2, S[17][0]))):
    ft = face_target(arm, n)
    c = mk.constraints.new("COPY_TRANSFORMS"); c.target = ft
    key_inf(c, [(1, 0), (f0, 0), (f1, 1), (f2, 1), (f3, 0)])
    for fc in P.all_fcurves(mk):
        if "influence" in fc.data_path:
            for k in fc.keyframe_points: k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"
# qo'l niqobni ushlaydi
gR = empty("grip_R"); gR.parent = mg; gR.location = (0.0, -0.06, 0.0)
gL = empty("grip_L"); gL.parent = mk_k; gL.location = (0.0, 0.06, 0.0)
R_IK.target = gR
c2 = girl.pose.bones["mixamorig:LeftForeArm"].constraints.new("IK"); c2.target = gL; c2.use_tail = True; c2.chain_count = 2
key_inf(R_IK, [(1, 0), (S[13][0] + 2, 0), (S[13][0] + 10, 1), (S[13][0] + 48, 1), (S[13][0] + 58, 0),
               (S[17][0] + 2, 0), (S[17][0] + 8, 1), (S[17][0] + 30, 1), (S[17][0] + 38, 0)])
key_inf(c2, [(1, 0), (S[14][0], 0), (S[14][0] + 8, 1), (S[14][1] - 2, 1), (S[14][1] + 4, 0)])
vis(groot, [(S[2][0], S[14][1]), (S[17][0], S[18][1]), (S[20][0], S[21][1])])
vis(kroot, [(S[2][0], S[14][1]), (S[17][0], S[18][1]), (S[20][0], S[21][1])])
vis(droot, [(S[2][0], S[14][1]), (S[17][0], S[18][1]), (S[20][0], S[21][1])])

# =================================================================== OSMON: bulutlar, A320
cl_mats = []
for zz, sc_, th in ((-45, 0.012, 0.5), (-160, 0.005, 0.46)):
    cm = P.cloud_material(f"clouds{zz}", sc_, th); cl_mats.append(cm)
    box(f"clouds{zz}", (9000, 9000, 0.01), (SKY.x, 0, zz), cm)
for cm in cl_mats:
    mp = cm.node_tree.nodes["MAP"]
    P.key_input(mp.inputs["Location"], 1, (0, 0, 0)); P.key_input(mp.inputs["Location"], NF, (-6.0 * (NF - 1), 0, 0))
    for fc in P.all_fcurves(cm.node_tree):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
a320, a_parts = P.import_gltf(BK + "536fac67_u.glb", name="a320")
a320.scale = (0.5,) * 3
bpy.context.view_layer.update()
body = next(o for o in a_parts if o.name.startswith("plane body"))
rud = next(o for o in a_parts if o.name.startswith("rodder"))
bc = sum((body.matrix_world @ Vector(v) for v in body.bound_box), Vector()) / 8
rc = sum((rud.matrix_world @ Vector(v) for v in rud.bound_box), Vector()) / 8
if rc.x < bc.x: a320.rotation_euler.z = R(180)
bpy.context.view_layer.update()
bb = [body.matrix_world @ Vector(v) for v in body.bound_box]
AMIN = Vector([min(v[i] for v in bb) for i in range(3)]); AMAX = Vector([max(v[i] for v in bb) for i in range(3)])
a320.location = SKY - Vector(((AMIN.x + AMAX.x) / 2 - 14, (AMIN.y + AMAX.y) / 2, (AMIN.z + AMAX.z) / 2))
bpy.context.view_layer.update()
bb = [body.matrix_world @ Vector(v) for v in body.bound_box]
AMIN = Vector([min(v[i] for v in bb) for i in range(3)]); AMAX = Vector([max(v[i] for v in bb) for i in range(3)])
ACEN = (AMIN + AMAX) / 2
apiv = empty("a320_piv", tuple(ACEN)); par(a320, apiv)
# 16-kadr: sho'ng'ish (burun pastga, pastga tushadi)
def dive(f):
    u = P.ease((f - S[16][0]) / (S[16][1] - S[16][0]), "in")
    return -14 * min(1, (f - S[16][0] + 6) / 12) if f >= S[16][0] - 6 else 0, -32 * u if f >= S[16][0] else 0
for f in (1, S[16][0] - 7) + tuple(range(S[16][0] - 6, S[16][1] + 1, 2)) + (S[16][1] + 1,):
    pr, dz = dive(min(f, S[16][1]))
    if f > S[16][1]: pr, dz = 0, 0
    key(apiv, f, loc=tuple(ACEN + Vector((0, 0, dz))), rot=(0, pr, 0))
vis(apiv, [S[1], S[16], S[22]])

# =================================================================== KABINA
cock = empty("cockpit", tuple(COC))
def cbox(n, size, loc, m, bev=0.0, rot=(0, 0, 0)):
    o = box(n, size, tuple(COC + Vector(loc)), m, bev, rot); par(o, cock); return o
panel_m = mat("cpanel", (0.06, 0.065, 0.07), 0.6)
cbox("c_floor", (3, 2.4, 0.1), (0.2, 0, -0.05), M["carpet"])
cbox("c_dash", (0.5, 2.0, 0.55), (-1.25, 0, 0.72), panel_m, 0.02)
cbox("c_glare", (0.35, 2.0, 0.08), (-1.15, 0, 1.06), panel_m, 0.02)
cbox("c_ped", (0.8, 0.45, 0.6), (-0.6, 0, 0.45), panel_m, 0.02)
cbox("c_over", (1.0, 1.6, 0.12), (-0.5, 0, 2.05), panel_m, 0.02, rot=(0, 18, 0))
cbox("c_wall_l", (2.4, 0.08, 1.4), (0.0, -1.05, 1.0), M["plastic"])
cbox("c_wall_r", (2.4, 0.08, 1.4), (0.0, 1.05, 1.0), M["plastic"])
cbox("c_back", (0.08, 2.2, 2.2), (1.25, 0, 1.0), M["plastic"])
cbox("c_roof", (2.0, 2.2, 0.08), (0.2, 0, 2.15), M["plastic"])
for y in (-0.95, -0.35, 0.35, 0.95):
    cbox("c_post", (0.08, 0.06, 0.95), (-1.25 + 0.25 * abs(y), y, 1.55), panel_m, rot=(0, -25, 0))
cbox("c_sill", (0.1, 2.0, 0.06), (-1.05, 0, 1.12), panel_m)
rnd = random.Random(3)
for i, y in enumerate((-0.75, -0.42, 0.42, 0.75)):          # ekranlar (PFD/ND)
    sm = bpy.data.materials.new(f"pfd{i}"); sm.use_nodes = True; nt = sm.node_tree; g = P.G(nt); b = bsdf(sm)
    xx, yy, zz = g.objxyz("Generated")
    col = g.mixcol(g.maprange(zz, 0.48, 0.52, 0, 1), (0.35, 0.18, 0.05), (0.05, 0.35, 0.9)) if i % 2 == 0 else \
        g.mixcol(g.maprange(g.fr(g.mul(g.add(g.mul(xx, xx), g.mul(zz, zz)), 6.0)), 0.0, 0.08, 1, 0), (0.0, 0.03, 0.05), (0.2, 1.0, 0.4))
    b.inputs["Base Color"].default_value = (0, 0, 0, 1); g.L.new(col, b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 2.5
    cbox(f"c_scr{i}", (0.01, 0.24, 0.2), (-0.995, y, 0.78), sm)
cbox("c_roof_f", (0.7, 2.0, 0.08), (-1.0, 0, 2.02), panel_m, 0.02, rot=(0, 22, 0))
for i in range(60):
    cbox("c_btn", (0.012, 0.025, 0.012), (-0.995, rnd.uniform(-0.95, 0.95), 0.56 + rnd.uniform(-0.04, 0.04)),
         mat(f"btn{i}", (0.1, 0.1, 0.1), 0.5, emit=rnd.choice((0, 0, 2.0)), emit_col=rnd.choice(((1, 0.7, 0.2), (0.3, 1, 0.4), (1, 1, 1)))))
for y in (-0.55, 0.55):
    cbox("c_seat", (0.55, 0.55, 0.12), (0.15, y, 0.45), M["fabric"], 0.04)
    cbox("c_seatb", (0.12, 0.55, 0.85), (0.47, y, 0.9), M["fabric"], 0.04, rot=(0, -12, 0))
yoke = empty("yoke", tuple(COC + Vector((-0.62, -0.55, 0.8)))); par(yoke, cock)
for o in (cyl("y_col", 0.02, 0.3, tuple(COC + Vector((-0.62, -0.55, 0.65))), panel_m, verts=12),
          cyl("y_bar", 0.016, 0.3, tuple(COC + Vector((-0.62, -0.55, 0.8))), panel_m, rot=(90, 0, 0), verts=12)):
    par(o, yoke)
proot.location = COC + Vector((0.23, -0.55, 0.02)); proot.rotation_euler.z = R(-90); par(proot, cock)
mc.add_strip(pete, A("Piloting.fbx"), S[15][0] - 60, blend=0)
for side, dy in (("Left", -0.13), ("Right", 0.13)):
    t_ = empty(f"pete_{side}_grip", tuple(COC + Vector((-0.62, -0.55 + dy, 0.8)))); par(t_, yoke)
    c = pete.pose.bones[f"mixamorig:{side}ForeArm"].constraints.new("IK"); c.target = t_; c.use_tail = True; c.chain_count = 2
for f, dx in ((1, 0), (S[15][0] + 6, 0), (S[15][0] + 22, -0.09), (S[15][1], -0.1)):
    key(yoke, f, loc=tuple(COC + Vector((-0.62 + dx, -0.55, 0.8))))
for f in range(1, NF + 1, 4):
    u = P.ease((f - S[15][0] - 10) / 30.0, "inout") if f >= S[15][0] else 0
    key(cock, f, rot=(0.6 * math.sin(f * 0.9) * u, -12 * u + 0.4 * math.sin(f * 1.3) * u, 0))
vis(cock, [S[15]])

# =================================================================== STUDIYA: qatlamli illyuminator
box("void", (30, 30, 30), tuple(STU), M["dark"])
bpy.data.objects["void"].modifiers.new("flip", "SOLIDIFY").thickness = 0.5
stu = empty("stu_root", tuple(STU))
def pane_obj(n, a, b_, th, m, y):
    bm_ = bmesh.new(); bmesh.ops.create_cone(bm_, cap_ends=True, segments=64, radius1=1, radius2=1, depth=1)
    bmesh.ops.scale(bm_, vec=(a, b_, th), verts=bm_.verts)
    o = P.mesh_obj(n, bm_, m); P.smooth(o); o.rotation_euler = (R(90), 0, 0); o.location = STU + Vector((0, y, 0))
    bev = o.modifiers.new("bev", "BEVEL"); bev.width = th * 0.35; bev.segments = 2
    par(o, stu); return o
skin_s = P.panel_with_hole("st_skin", M["alu"], "round", a=0.2, size=0.85, thick=0.02, rivet_m=mat("rivet", (0.7, 0.72, 0.75), 0.3, metal=1.0))
skin_s.scale = (0.72, 1, 1); skin_s.location = STU + Vector((0, 0.04, 0)); par(skin_s, stu)
outer = pane_obj("st_outer", 0.16, 0.215, 0.014, glass_mat("g_outer", (0.85, 0.93, 1.0)), 0.02)
inner = pane_obj("st_inner", 0.15, 0.205, 0.009, glass_mat("g_inner", (0.9, 0.95, 1.0)), 0.0)
dot = cyl("st_hole", 0.004, 0.012, tuple(STU + Vector((0, 0.0, -0.15))), M["black"], rot=(90, 0, 0), verts=12, bevel=False); par(dot, inner)
scratch = pane_obj("st_scratch", 0.14, 0.195, 0.004, M["acryl"], -0.02)
bz, bzn = P.import_gltf(BK + "7250f009_u.glb", name="st_bezel")
for o in bzn:
    if o.type == "MESH" and (is_cover(o) or max(o.dimensions) > 1.0): bpy.data.objects.remove(o, do_unlink=True)
bz.matrix_world = basis(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)), STU + Vector((0, -0.04, 0)))
par(bz, stu)
LAY = [(skin_s, 0.04, 0.42), (outer, 0.02, 0.24), (inner, 0.0, 0.06), (scratch, -0.02, -0.12), (bz, -0.04, -0.3)]
E0, E1 = S[19][0] + 6, S[19][0] + 40
for o, y0, y1 in LAY:
    base = o.location.copy()
    for f in range(E0, E1 + 1, 2):
        u = P.ease((f - E0) / (E1 - E0), "out")
        key(o, f, loc=tuple(base + Vector((0, (y1 - y0) * u, 0))))
for loc, en, col, rot in (((1.2, 0.8, 0.9), 60, (0.6, 0.8, 1.0), (R(-60), 0, R(130))), ((-1.3, -0.4, 0.6), 40, (1.0, 0.7, 0.4), (R(70), 0, R(-60))),
                          ((0.0, -1.4, 1.2), 30, (1, 1, 1), (R(50), 0, 0))):
    l = bpy.data.objects.new("stu_l", bpy.data.lights.new("stu_l", "AREA")); P.link(l)
    l.data.size = 1.2; l.data.energy = en * 2.5; l.data.color = col; l.location = STU + Vector(loc); l.rotation_euler = rot
for y in (-1.5, 1.5):                       # aks uchun yorug' chiziqlar
    box("stu_strip", (3, 0.02, 0.06), tuple(STU + Vector((0, y, 0.9))), mat("strip", (1, 1, 1), 0.5, emit=6.0))

# =================================================================== KAMERALAR
cams = {}
def C(n, lens, fstop=None, focus=None):
    c, t = camera(f"cam{n:02d}", lens, fstop, focus); cams[n] = c; return c, t
K = lambda v: tuple(v)
ay, az = AMIN.y, ACEN.z + 0.35
# 1: ILGAK — A320 bo'ylab bitta illyuminatorga uchib borish
c, t = C(1, 16, 4.0)
cam_move(c, t, *S[1], (AMIN.x + 32, ay - 7, az - 3.2), (AMIN.x + 12.9, ay - 0.75, az + 0.05),
         (AMIN.x + 14, ay, az - 0.5), (AMIN.x + 12.3, ay, az), "in", lens=(16, 26, "in"))
# 2: salon — qiz bolg'acha bilan uradi
c, t = C(2, 22, 2.8)
cam_move(c, t, S[2][0], IMP1 - 1, (MEG_X - 0.75, -0.55, 1.5), (MEG_X - 0.66, -0.72, 1.44),
         (MEG_X - 0.05, -1.45, 1.1), (MEG_X - 0.15, -1.6, 1.07), "inout")
cam_move(c, t, IMP1, S[2][1], (MEG_X - 0.64, -0.76, 1.42), (MEG_X - 0.55, -0.98, 1.32),
         (MEG_X - 0.17, -1.62, 1.06), (MEG_X - 0.17, -1.68, 1.05), "out", shake=[(IMP1, IMP1 + 10, 0.03)], lens=(22, 40, "out"))
# 3: makro — yoriqlar
P0 = HOLE - HD * 0.03
pfoc = empty("pane_focus", tuple(P0))
c, t = C(3, 40, 5.6, focus=pfoc)
cam_move(c, t, *S[3], K(P0 - HD * 0.36 + HW * 0.07 - HT * 0.04), K(P0 - HD * 0.22 + HW * 0.03 - HT * 0.02), K(P0 + HD * 0.5 + HT * 0.1),
         K(P0 + HD * 0.5 + HT * 0.08), "inout")
# 4: keng plan, yo'lakdan — portlash
c, t = C(4, 16)
cam_move(c, t, *S[4], (MEG_X - 0.3, 0.3, 0.75), (MEG_X - 0.26, 0.18, 0.82), (MEG_X - 0.12, -1.5, 1.1), (MEG_X - 0.12, -1.55, 1.05), "lin",
         shake=[(BURST, S[4][1], 0.07)])
# 5: tashqaridan — bug' oqimi
c, t = C(5, 20, 4.0)
cam_move(c, t, *S[5], K(HOLE_OUT + HD * 3.2 + Vector((-4.2, 0, 0.9))), K(HOLE_OUT + HD * 3.6 + Vector((-2.6, 0, 1.4))),
         K(HOLE_OUT + Vector((0.6, 0, 0))), K(HOLE_OUT + HD * 0.8 + Vector((2.0, 0, 0))), "inout", shake=[(S[5][0], S[5][1], 0.03)])
# 6: pol sathidan — telefon va sumka
c, t = C(6, 20, 4.0)
cam_move(c, t, *S[6], (X4 - 0.2, 0.12, 1.3), (X4 + 0.15, 0.05, 1.4), (X4 + 0.02, -0.85, 0.5), (MEG_X - 0.3, -1.6, 1.05), "inout",
         shake=[(S[6][0], S[6][1], 0.015)])
# 7: Josh tortiladi
c, t = C(7, 26)
cam_move(c, t, *S[7], (ROWS[5] - 1.9, 0.1, 1.35), (ROWS[5] - 1.6, 0.05, 1.25), (ROWS[5], -0.1, 1.3), (ROWS[5], -0.4, 1.1), "inout",
         shake=[(S[7][0], S[7][1], 0.03)])
# 8: harorat ekrani + qirov
c, t = C(8, 40, 2.8)
cam_move(c, t, *S[8], K(scr_pos + Vector((0.42, 0.12, 0.14))), K(scr_pos + Vector((0.28, 0.06, 0.06))), K(scr_pos), K(scr_pos), "inout")
# 9: yo'lak bo'ylab — tuman
c, t = C(9, 20)
cam_move(c, t, *S[9], (-3.6, 0.1, 1.45), (-5.6, 0.15, 1.6), (2.0, -0.2, 1.0), (2.0, -0.2, 1.1), "out")
# 10: pastdan yuqoriga — niqoblar tushadi
c, t = C(10, 16)
cam_move(c, t, *S[10], (MEG_X - 1.4, -0.1, 0.7), (MEG_X - 1.2, -0.15, 0.85), (MEG_X - 0.2, -0.9, 1.75), (MEG_X - 0.1, -0.8, 1.55), "inout",
         shake=[(S[10][0] + 4, S[10][0] + 20, 0.02)])
# 11: o'rta plan — qiz va osilgan niqob
c, t = C(11, 26, 2.8)
cam_move(c, t, *S[11], (MEG_X - 0.95, -0.8, 1.55), (MEG_X - 0.85, -1.1, 1.48), (MEG_X - 0.1, -1.3, 1.1), (MEG_X - 0.05, -1.3, 1.08), "inout")
# 12: yuz, hushdan ketish (gandiraklaydi)
head_t = empty("girl_head_t"); cc = head_t.constraints.new("COPY_LOCATION"); cc.target = girl; cc.subtarget = "mixamorig:Head"; cc.head_tail = 0.5
c, t = C(12, 30, 2.0, focus=head_t); c.constraints["Track To"].target = head_t
for f in range(S[12][0], S[12][1] + 1):
    u = (f - S[12][0]) / (S[12][1] - S[12][0])
    c.location = (MEG_X - 0.44 + 0.05 * u + 0.02 * math.sin(f * 0.25), -1.12 + 0.04 * math.sin(f * 0.18), 1.28 - 0.1 * u + 0.025 * math.cos(f * 0.21))
    c.keyframe_insert("location", frame=f)
    c.data.lens = 30 + 6 * math.sin(f * 0.15) * u; c.data.keyframe_insert("lens", frame=f)
# 13: niqobni taqish
c, t = C(13, 24, 2.8, focus=head_t); c.constraints["Track To"].target = head_t
cam_move(c, t, *S[13], (MEG_X - 0.45, -0.8, 1.4), (MEG_X - 0.42, -1.0, 1.3), (0, 0, 0), (0, 0, 0), "out", tgt_obj_follow=True)
# 14: qizdan ayolga
c, t = C(14, 22, 2.8)
cam_move(c, t, *S[14], (MEG_X - 0.44, -1.0, 1.38), (MEG_X - 0.44, -0.5, 1.38), (MEG_X, -1.3, 1.1), (MEG_X, -0.82, 1.05), "inout")
# 15: kabina — uchuvchi yelkasi ortidan (kamera kabina bilan birga)
c, t = C(15, 18)
c.parent = cock; t.parent = cock
cam_move(c, t, *S[15], (0.85, -0.05, 1.5), (0.6, -0.1, 1.45), (-2.0, -0.6, 1.0), (-2.0, -0.6, 0.95), "inout",
         shake=[(S[15][0], S[15][1], 0.012)])
# 16: A320 sho'ng'iydi — kamera ergashadi
c, t = C(16, 24)
for f in range(S[16][0], S[16][1] + 1):
    pr, dz = dive(f); u = (f - S[16][0]) / (S[16][1] - S[16][0])
    ctr = ACEN + Vector((0, 0, dz))
    c.location = ctr + Vector((-34 + 10 * u, -26 + 4 * u, 6 - 2 * u)); c.keyframe_insert("location", frame=f)
    t.location = ctr + Vector((-4, 0, -2)); t.keyframe_insert("location", frame=f)
# 17: yengillik — niqobni oladi
c, t = C(17, 30, 2.0, focus=head_t); c.constraints["Track To"].target = head_t
cam_move(c, t, *S[17], (MEG_X - 0.45, -0.95, 1.3), (MEG_X - 0.42, -1.05, 1.24), (0, 0, 0), (0, 0, 0), "inout", tgt_obj_follow=True)
# 18: tinch salon, derazaga tez yaqinlashish
c, t = C(18, 20, 4.0)
cam_move(c, t, *S[18], (MEG_X + 1.4, 0.2, 1.45), (MEG_X - 0.45, -1.05, 1.2), (MEG_X - 0.2, -1.6, 1.0), (MEG_X - 0.17, -1.75, 1.05), "in",
         lens=(20, 30, "in"))
# 19: studiya — qatlamlar
c, t = C(19, 40, 5.6)
for f in range(S[19][0], S[19][1] + 1):
    u = P.ease((f - S[19][0]) / (S[19][1] - S[19][0]), "inout")
    a = R(-15 - 40 * u); r_ = 1.35 - 0.2 * u
    c.location = STU + Vector((r_ * math.sin(a) * -1, -r_ * math.cos(a), 0.25 - 0.1 * u)); c.keyframe_insert("location", frame=f)
    t.location = STU + Vector((0, 0.05, 0)); t.keyframe_insert("location", frame=f)
# 20: musht
c, t = C(20, 22, 2.8)
cam_move(c, t, S[20][0], PUNCH - 1, (MEG_X - 0.75, -0.55, 1.5), (MEG_X - 0.66, -0.72, 1.44), (MEG_X - 0.1, -1.5, 1.08), (MEG_X - 0.15, -1.6, 1.06), "inout")
cam_move(c, t, PUNCH, S[20][1], (MEG_X - 0.66, -0.72, 1.44), (MEG_X - 0.72, -0.6, 1.5), (MEG_X - 0.15, -1.6, 1.06), (MEG_X - 0.0, -1.4, 1.05),
         "out", shake=[(PUNCH, PUNCH + 12, 0.035)], lens=(22, 30, "out"))
# 21: yuz, derazaga o'giriladi
c, t = C(21, 30, 2.0, focus=head_t); c.constraints["Track To"].target = head_t
cam_move(c, t, *S[21], (MEG_X - 0.45, -0.92, 1.3), (MEG_X - 0.42, -1.04, 1.26), (0, 0, 0), (0, 0, 0), "inout", tgt_obj_follow=True)
# 22: A320 illyuminatoridan orqaga — butun samolyot
c, t = C(22, 30)
cam_move(c, t, *S[22], (AMIN.x + 12.3, ay - 0.9, az), (AMIN.x + 2, ay - 42, az + 9), (AMIN.x + 12.3, ay, az), (ACEN.x, ACEN.y, ACEN.z), "out",
         lens=(30, 20, "out"))
for n, c in cams.items():
    sc.timeline_markers.new(c.name, frame=S[n][0]).camera = c
sc.camera = cams[1]

# =================================================================== OSMON YORUG'LIGI
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; env = N.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(20))   # HDRI quyoshi Megan derazasiga tushmasin
w.node_tree.links.new(tc.outputs["Generated"], mp.inputs[0]); w.node_tree.links.new(mp.outputs[0], env.inputs[0])
w.node_tree.links.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); P.link(sun)
sun.data.energy = 4.0; sun.data.angle = R(1.5); sun.data.color = (1.0, 0.92, 0.8); sun.rotation_euler = (R(48), 0, R(-25))
# portlash chaqnashi
flash = bpy.data.objects.new("flash", bpy.data.lights.new("flash", "POINT")); P.link(flash)
flash.location = HOLE - HD * 0.3; flash.data.shadow_soft_size = 0.3; flash.data.color = (0.9, 0.95, 1)
for f, e in ((1, 0), (BURST - 1, 0), (BURST, 3000), (BURST + 2, 800), (BURST + 6, 0), (IMP1 - 1, 0), (IMP1, 400), (IMP1 + 3, 0)):
    flash.data.energy = e; flash.data.keyframe_insert("energy", frame=f)

# =================================================================== RENDER
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 12
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 45))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", -0.3))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True
            bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{NF}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
