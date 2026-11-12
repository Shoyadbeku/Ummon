# "G'oz terisi" — Zack D. Films uslubida 41.7 s (1002 kadr, 24 fps, 9:16).
# Sahnalar bitta faylda, turli joylarda: ko'cha (0,0,0), teri makro (1000,0,0), teri kesimi (2000,0,0),
# rentgen (3000,0,0), qorli o'rmon (4000,0,0). Kesishlar kamera markerlari bilan (STORYBOARD.md).
# Render: OUT=... SAMPLES=12 PCT=50 python -I goz.py --render   (FRAMES=1,60 sinov uchun, RANGE=a,b qism)
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from mathutils import Vector
import numpy as np
import parts as P
from parts import R, box, cyl, sphere, empty, key, par, mat, bsdf, vis, cam_move, camera
import mixchar as mc

OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
NF = 1002
sc.frame_start, sc.frame_end, sc.render.fps = 1, NF, 24

# kadrlar (ovoz so'zlariga bog'langan)
S = {1: (1, 38), 2: (39, 62), 3: (63, 125), 4: (126, 166), 5: (167, 234), 6: (235, 295), 7: (296, 340),
     8: (341, 392), 9: (393, 440), 10: (441, 534), 11: (535, 602), 12: (603, 659), 13: (660, 724),
     14: (725, 777), 15: (778, 855), 16: (856, 913), 17: (914, NF)}
def rng(*shots): return [S[s] for s in shots]
ST = Vector((0, 0, 0)); SK = Vector((1000, 0, 0)); CX = Vector((2000, 0, 0)); XR = Vector((3000, 0, 0)); FO = Vector((4000, 0, 0))
K = lambda v: tuple(v)

def const_keys(sock_owner, path, f, v):
    setattr(sock_owner, path, v); sock_owner.keyframe_insert(path, frame=f)

def all_const(idb):
    for fc in P.all_fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"

def set_root(name):
    return empty(name)

def under(root, objs):
    for o in objs:
        if o.parent is None: par(o, root)

def snow_mat():
    m = mat("snowflake", (1, 1, 1), 0.5, emit=0.6, emit_col=(0.85, 0.9, 1.0)); return m

def tame(meshes, rough=0.6):
    """Mixamo materiallarining plastmassa yaltirashini kamaytirish."""
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

def head_target(name, arm, bone="mixamorig:Head", ht=0.55):
    t = empty(name); c = t.constraints.new("COPY_LOCATION"); c.target = arm; c.subtarget = bone; c.head_tail = ht
    return t

A = lambda f, inplace=True: mc.load_action(f, inplace)
def strip_at(arm, file, shot_start, src_frame=0, speed=1.0, **kw):
    """Harakatning src_frame (30fps) kadri shot_start ga to'g'ri kelsin."""
    st = shot_start - src_frame * (24 / 30) / speed
    return mc.add_strip(arm, A(file), st, speed=speed, **kw)

# =================================================================== 1) KO'CHA (qorli kechki ko'cha)
street = set_root("SET_street")
snowtex = P.tex_image_mat("ph_asphalt_snow", PH + "asphalt_snow", 0.35)
road = box("road", (60, 30, 0.1), (0, 6, -0.05), snowtex); par(road, street)
snowm = P.tex_image_mat("ph_snow", PH + "snow_02", 0.5)
walk = box("sidewalk", (60, 30, 0.16), (0, -10, 0.0), snowm)
par(walk, street)
for i, (x, y, sx, sy, sz) in enumerate(((-4, 2.6, 6, 1.2, 0.5), (5.5, 2.4, 7, 1.4, 0.6), (-9, -2.5, 6, 2, 0.7), (8, -2.8, 7, 2, 0.6))):
    b = P.sphere(f"snowbank{i}", 1.0, (x, y, 0.0), snowm, scale=(sx / 2, sy / 2, sz)); par(b, street)
    d = b.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("sbt", "CLOUDS"); t.noise_scale = 0.6; d.texture = t; d.strength = 0.25
for x in (-6, 6):   # ko'cha chiroqlari
    pole = cyl("lamp_pole", 0.06, 5.0, (x, 1.6, 2.5), mat("pole", (0.05, 0.05, 0.06), 0.4, metal=0.8)); par(pole, street)
    bulb = P.sphere("lamp_bulb", 0.18, (x, 1.6, 5.0), mat("bulb", (1.0, 0.8, 0.5), 0.3, emit=25.0)); par(bulb, street)
    pl = P.link(bpy.data.objects.new("lamp_light", bpy.data.lights.new("lamp_light", "POINT")))
    pl.data.energy = 900; pl.data.color = (1.0, 0.72, 0.4); pl.data.shadow_soft_size = 0.3; pl.location = (x, 1.6, 4.8); par(pl, street)
key_l = P.link(bpy.data.objects.new("street_fill", bpy.data.lights.new("street_fill", "AREA")))
key_l.data.size = 3; key_l.data.energy = 250; key_l.data.color = (0.6, 0.75, 1.0); key_l.location = (2.5, -3.5, 3.5)
key_l.rotation_euler = (R(50), 0, R(35)); par(key_l, street)
rim = P.link(bpy.data.objects.new("street_rim", bpy.data.lights.new("street_rim", "AREA")))
rim.data.size = 2; rim.data.energy = 300; rim.data.color = (1.0, 0.75, 0.45); rim.location = (-2.2, 2.5, 2.6)
rim.rotation_euler = (R(-60), 0, R(-140)); par(rim, street)
flash = P.link(bpy.data.objects.new("lightning", bpy.data.lights.new("lightning", "AREA")))
flash.data.size = 8; flash.data.color = (0.75, 0.85, 1.0); flash.location = (-3, -6, 9); flash.rotation_euler = (R(35), 0, R(-25))
for f, e in ((1, 0), (44, 0), (45, 9000), (46, 1500), (47, 0), (49, 6000), (51, 0)):
    flash.data.energy = e; flash.data.keyframe_insert("energy", frame=f)
all_const(flash.data); par(flash, street)
sn_street = P.mesh_obj("snow_street", bmesh.new()); par(sn_street, street)
sn_street.location = (0, -1.5, -0.2)
P.gn_modifier(sn_street, P.snow_gn("snow_st", 2600, (10, 10, 6), 0.8, 0.0065, snow_mat()))

# Megan (qiz)
groot, girl, gmesh = mc.load_character("girl", "Megan.fbx"); tame(gmesh)
groot.location = (0, 0, 0.08); groot.rotation_euler.z = R(-8)
strip_at(girl, "Shoulder_Rubbing.fbx", 1, src_frame=20, speed=1.1)
strip_at(girl, "Terrified.fbx", 39, src_frame=20, speed=1.3, blend=0)
strip_at(girl, "Look_Around_2.fbx", 856, src_frame=20, speed=1.15, blend=0)
for i in range(3):                          # qaltirash: ildizga mayda shovqin
    groot.keyframe_insert("rotation_euler", index=2, frame=1)
for fc in P.all_fcurves(groot):
    m_ = fc.modifiers.new("NOISE"); m_.scale = 1.2; m_.strength = 0.03; m_.phase = 3
par(groot, street)
vis(street, rng(1, 2, 16))

# =================================================================== 2) TERI MAKRO (1 birlik ~ 1 mm)
skin_root = set_root("SET_skin"); skin_root.location = SK
def skin_material(name, sss=0.35):
    m = mat(name, (0.78, 0.5, 0.4), 0.42)
    b = bsdf(m); nt = m.node_tree; N = nt.nodes; L = nt.links
    b.inputs["Subsurface Weight"].default_value = 0.6
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.38, 0.22); b.inputs["Subsurface Scale"].default_value = sss
    b.inputs["Coat Weight"].default_value = 0.15; b.inputs["Coat Roughness"].default_value = 0.35
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 1.1
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.feature = "DISTANCE_TO_EDGE"; vo2.inputs["Scale"].default_value = 4.5
    L.new(tc.outputs["Object"], vo2.inputs["Vector"])
    ns = N.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 9.0; ns.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], ns.inputs["Vector"])
    g = P.G(nt)
    cre = g.add(g.mul(g.maprange(vo.outputs["Distance"], 0.0, 0.08, 0, 1), 0.7), g.mul(g.maprange(vo2.outputs["Distance"], 0, 0.05, 0, 1), 0.3))
    h = g.add(cre, g.mul(ns.outputs["Fac"], 0.25))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.06
    L.new(h, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    colv = g.mixcol(g.maprange(ns.outputs["Fac"], 0.35, 0.65, 0, 1), (0.66, 0.36, 0.27), (0.76, 0.46, 0.34))
    colv = g.mixcol(g.maprange(cre, 0.0, 0.5, 0.35, 0.0), colv, (0.55, 0.3, 0.25))
    L.new(colv, b.inputs["Base Color"])
    rr = g.maprange(cre, 0, 1, 0.6, 0.38); L.new(rr, b.inputs["Roughness"])
    return m

SKIN = skin_material("skin_macro")
bsdf(SKIN)
hair_m = mat("hair_shaft", (0.05, 0.032, 0.02), 0.33, coat=0.4)
bsdf(hair_m).inputs["Subsurface Weight"].default_value = 0.0
W, RES = 30.0, 420
rr_ = random.Random(5)
fol = []
sp = 1.35
for i in range(int(W / sp) + 1):
    for j in range(int(W / sp) + 1):
        x = -W / 2 + 0.5 + i * sp + rr_.uniform(-0.45, 0.45); y = -W / 2 + 0.5 + j * sp + rr_.uniform(-0.45, 0.45)
        if abs(x) < W / 2 - 0.3 and abs(y) < W / 2 - 0.3: fol.append((x, y))
fol = np.array(fol)
def base_h(x, y): return 0.12 * np.sin(x * 0.45 + 1.0) * np.cos(y * 0.38) + 0.06 * np.sin(x * 1.3 + y * 0.9)
xs = np.linspace(-W / 2, W / 2, RES); X, Y = np.meshgrid(xs, xs, indexing="ij")
Z0 = base_h(X, Y)
# follikula atrofidagi chuqurcha (pora) va do'mboq (g'oz terisi)
bump = np.zeros_like(X); pore = np.zeros_like(X)
amp = np.array([rr_.uniform(0.75, 1.25) for _ in fol]); rad = np.array([rr_.uniform(0.42, 0.6) for _ in fol])
for (fx, fy), a, r_ in zip(fol, amp, rad):
    d2 = (X - fx) ** 2 + (Y - fy) ** 2
    bump += a * 0.42 * np.exp(-d2 / (r_ * r_)); pore -= 0.05 * np.exp(-d2 / 0.012)
bm = bmesh.new(); V = {}
for i in range(RES):
    for j in range(RES):
        V[i, j] = bm.verts.new((X[i, j], Y[i, j], Z0[i, j] + pore[i, j]))
for i in range(RES - 1):
    for j in range(RES - 1):
        bm.faces.new((V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]))
skin = P.mesh_obj("skin_patch", bm, SKIN); P.smooth(skin)
skin.shape_key_add(name="Basis", from_mix=False)
kb = skin.shape_key_add(name="goose", from_mix=False); kb.value = 0
flat = bump.reshape(-1)
for idx, v in enumerate(kb.data):
    v.co.z += flat[idx]
par(skin, skin_root); skin.location = SK
hair_obj = P.hair_strand_mesh("skin_hair_src", 3.8, 0.045, 0.012, 0.18); hair_obj.data.materials.append(hair_m)
hair_obj.location = (0, 0, -500); hair_obj.hide_render = True
bm = bmesh.new()
for (fx, fy) in fol: bm.verts.new((fx, fy, float(base_h(fx, fy)) - 0.03))
folo = P.mesh_obj("skin_follicles", bm); par(folo, skin_root); folo.location = SK
g_sh = P.skin_hair_gn("skin_hair", hair_obj, bump_h=0.4, tilt0=76, tilt1=14)
mod_sh = P.gn_modifier(folo, g_sh)
def goose(f, v): kb.value = v; kb.keyframe_insert("value", frame=f); P.gn_set(mod_sh, g_sh, "Goose", v, frame=f)
def lift(f, v): P.gn_set(mod_sh, g_sh, "Lift", v, frame=f)
# 3-kadr: tuklar ko'tariladi, teri do'mboqlanadi
for f, l, gz in ((63, 0.0, 0.0), (72, 0.0, 0.0), (100, 1.0, 0.75), (125, 1.0, 0.85),
                 (393, 0.05, 0.1), (404, 0.05, 0.1), (414, 1.0, 0.3), (440, 1.0, 0.35),
                 (441, 1.0, 0.25), (520, 1.0, 1.0),
                 (914, 0.0, 0.0), (928, 0.0, 0.0), (958, 1.0, 1.0)):
    lift(f, l); goose(f, gz)
for idb in (skin.data.shape_keys, folo):
    for fc in P.all_fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = "BEZIER"; k.easing = "AUTO"
for nm, loc, rot, en, size, col in (("skin_key", (-12, -9, 6), (R(62), 0, R(-53)), 9000, 8, (1.0, 0.92, 0.85)),
                                     ("skin_rim", (6, 14, 5), (R(-70), 0, R(20)), 7000, 8, (0.75, 0.85, 1.0)),
                                     ("skin_fill", (10, -6, 6), (R(60), 0, R(55)), 1500, 8, (1.0, 0.8, 0.7))):
    l = P.link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA"))); l.data.energy = en; l.data.size = size
    l.data.color = col; l.location = SK + Vector(loc); l.rotation_euler = rot; par(l, skin_root)
vis(skin_root, rng(3, 9, 10, 17))

# =================================================================== 3) TERI KESIMI (1 birlik ~ 1 mm)
cx_root = set_root("SET_cross"); cx_root.location = CX
def cmat(name, col, rough=0.5, emit=0.0, sss=0.0, tex=None, tex_scale=3.0, col2=None, bump=0.0):
    m = mat(name, col, rough, emit=emit)
    b = bsdf(m)
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.15
    if tex:
        nt = m.node_tree; N = nt.nodes; L = nt.links; g = P.G(nt)
        tc = N.new("ShaderNodeTexCoord")
        t = N.new("ShaderNodeTexWave" if tex == "wave" else "ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = tex_scale
        if tex == "wave": t.inputs["Distortion"].default_value = 9; t.inputs["Detail"].default_value = 6; t.inputs["Detail Scale"].default_value = 2
        L.new(tc.outputs["Object"], t.inputs["Vector"])
        L.new(g.mixcol(t.outputs["Fac"], col, col2 or tuple(c * 0.7 for c in col)), b.inputs["Base Color"])
        if bump:
            bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(t.outputs["Fac"], bp.inputs["Height"])
            L.new(bp.outputs[0], b.inputs["Normal"])
    return m
CM = dict(
    epi=cmat("epi", (0.86, 0.62, 0.5), 0.5, sss=0.3, tex="wave", tex_scale=6, col2=(0.7, 0.45, 0.35), bump=0.2),
    corneum=cmat("corneum", (0.9, 0.78, 0.65), 0.45, tex="noise", tex_scale=12, bump=0.3),
    dermis=cmat("dermis", (0.88, 0.5, 0.5), 0.6, sss=0.4, tex="wave", tex_scale=1.6, col2=(0.75, 0.38, 0.4), bump=0.25),
    fat=cmat("fat", (0.98, 0.8, 0.32), 0.25, sss=0.5, tex="noise", tex_scale=4, col2=(0.9, 0.68, 0.22), bump=0.1),
    sheath=cmat("sheath", (0.78, 0.45, 0.4), 0.4, sss=0.3),
    bulb=cmat("bulb", (0.7, 0.32, 0.3), 0.4, sss=0.3),
    gland=cmat("gland", (0.92, 0.7, 0.2), 0.3, sss=0.3, tex="noise", tex_scale=8, bump=0.3),
    artery=cmat("artery", (0.65, 0.04, 0.04), 0.3, sss=0.3),
    vein=cmat("vein", (0.12, 0.18, 0.55), 0.3, sss=0.3),
    nerve=mat("nerve", (0.95, 0.85, 0.3), 0.4, emit=0.6, emit_col=(1.0, 0.85, 0.3)),
    pulse=P.emit_mat("pulse", (1.0, 0.9, 0.5), 40.0),
)
MUS = mat("muscle", (0.62, 0.05, 0.05), 0.35, emit=0.0001, emit_col=(1.0, 0.1, 0.04))
bsdf(MUS).inputs["Subsurface Weight"].default_value = 0.3
musE = bsdf(MUS).inputs["Emission Strength"]
for f, v in ((1, 0.0), (196, 0.0), (210, 3.0), (234, 3.0), (341, 1.0), (351, 1.0), (355, 9.0), (392, 3.5)):
    musE.default_value = v; musE.keyframe_insert("default_value", frame=f)
CW = 16.0
def cbox(name, size, loc, m):
    o = box(name, size, K(CX + Vector(loc)), m); par(o, cx_root); return o
cbox("corneum", (CW, 8, 0.05), (0, 4, -0.025), CM["corneum"])
cbox("epidermis", (CW, 8, 0.2), (0, 4, -0.15), CM["epi"])
cbox("dermis", (CW, 8, 2.4), (0, 4, -1.45), CM["dermis"])
cbox("hypodermis", (CW, 8, 2.0), (0, 4, -3.65), CM["fat"])
rr2 = random.Random(9)
for i in range(70):                                   # kesimdagi yog' bo'lakchalari
    x = rr2.uniform(-CW / 2 + 0.3, CW / 2 - 0.3); z = rr2.uniform(-4.4, -2.9); r_ = rr2.uniform(0.3, 0.5)
    o = P.sphere("fatcell", r_, K(CX + Vector((x, rr2.uniform(-0.15, 0.05), z))), CM["fat"], scale=(1, 0.5, 0.85), seg=16); par(o, cx_root)
def tube(name, pts, r, m):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 4
    spl = cu.splines.new("BEZIER"); spl.bezier_points.add(len(pts) - 1)
    for bp_, p in zip(spl.bezier_points, pts):
        bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
    o = P.link(bpy.data.objects.new(name, cu)); cu.materials.append(m); par(o, cx_root); return o
tube("artery", [K(CX + Vector((x, -0.15, -2.55 + 0.12 * math.sin(x)))) for x in np.linspace(-CW / 2, CW / 2, 9)], 0.16, CM["artery"])
tube("vein", [K(CX + Vector((x, 0.35, -2.75 + 0.1 * math.cos(x)))) for x in np.linspace(-CW / 2, CW / 2, 9)], 0.2, CM["vein"])
nerve_main = tube("nerve_main", [K(CX + Vector((x, -0.12, -2.2 + 0.08 * math.sin(2 * x)))) for x in np.linspace(-CW / 2, CW / 2, 11)], 0.06, CM["nerve"])

cross_hair = P.hair_strand_mesh("cross_hair_src", 1.0, 0.06, 0.02, 0.06); cross_hair.data.materials.append(hair_m)
cross_hair.location = (0, 0, -600); cross_hair.hide_render = True
TH0, TH1, CON0, CON1 = 42.0, 9.0, 351, 359
pivots, muscles = [], []
for k_, fx in enumerate((-5.4, -1.8, 1.8, 5.4)):
    pv = empty(f"fol_pivot{k_}", K(CX + Vector((fx, -0.06, 0.0))))
    def ch(o): o.parent = pv; return o
    sh = P.cyl(f"sheath{k_}", 0.17, 2.1, (0, 0, -1.05), CM["sheath"], verts=24, bevel=False); ch(sh)
    P.sphere(f"bulb{k_}", 0.26, (0, 0, -2.12), CM["bulb"], scale=(1, 1, 1.15), seg=20).parent = pv
    ch(P.sphere(f"papilla{k_}", 0.12, (0, 0, -2.25), CM["artery"], seg=16))
    ch(P.cyl(f"shaft{k_}", 0.065, 6.4, (0, 0, 1.1), hair_m, verts=12, bevel=False))
    gl = P.sphere(f"gland{k_}", 0.22, (-0.3, 0, -0.65), CM["gland"], scale=(1, 0.8, 1.3), seg=16); ch(gl)
    gl2 = P.sphere(f"gland{k_}b", 0.16, (-0.42, 0, -0.95), CM["gland"], seg=16); ch(gl2)
    a_ = empty(f"musA{k_}", (0.19, 0, -1.3)); a_.parent = pv
    b_ = empty(f"musB{k_}", K(CX + Vector((fx + 1.05, -0.06, -0.33)))); par(b_, cx_root)
    # mushak: Y bo'ylab uzunligi 1 bo'lgan urchuq
    bm = bmesh.new(); rings = []
    for i in range(13):
        t = i / 12; rr_t = 0.025 + 0.12 * math.sin(math.pi * t) ** 0.8
        rings.append([bm.verts.new((rr_t * math.cos(2 * math.pi * j / 12), t, rr_t * math.sin(2 * math.pi * j / 12))) for j in range(12)])
    for i in range(12):
        for j in range(12):
            jj = (j + 1) % 12; bm.faces.new((rings[i][j], rings[i][jj], rings[i + 1][jj], rings[i + 1][j]))
    mu = P.mesh_obj(f"muscle{k_}", bm, MUS); P.smooth(mu)
    cl = mu.constraints.new("COPY_LOCATION"); cl.target = a_
    st_ = mu.constraints.new("STRETCH_TO"); st_.target = b_; st_.volume = "VOLUME_XZX"; st_.rest_length = 1.0; st_.bulge = 1.6
    muscles.append(mu); pivots.append(pv)
    # nerv shoxchasi asosiy nervdan mushakka
    tube(f"nerve_br{k_}", [K(CX + Vector((fx + 0.3, -0.12, -2.2))), K(CX + Vector((fx + 0.75, -0.12, -1.5))),
                           K(CX + Vector((fx + 0.62, -0.1, -0.95)))], 0.03, CM["nerve"])
    for f, th in ((1, TH0), (CON0, TH0), (CON1, TH1), (NF, TH1)):
        pv.rotation_euler = (0, R(th), 0); pv.keyframe_insert("rotation_euler", frame=f)
    for fc in P.all_fcurves(pv):
        for kp in fc.keyframe_points: kp.interpolation = "BEZIER"
    par(pv, cx_root)
# kesim ortidagi teri sirtidagi tuklar
bm = bmesh.new(); rr3 = random.Random(13)
for i in range(110): bm.verts.new((rr3.uniform(-CW / 2 + 0.4, CW / 2 - 0.4), rr3.uniform(0.5, 7.5), 0.0))
back = P.mesh_obj("cross_back_follicles", bm); back.location = CX; par(back, cx_root)
cross_hair5 = P.hair_strand_mesh("cross_hair5_src", 5.0, 0.065, 0.02, 0.1); cross_hair5.data.materials.append(hair_m)
cross_hair5.location = (0, 0, -700); cross_hair5.hide_render = True
g_cb = P.skin_hair_gn("cross_hair", cross_hair5, bump_h=0.0, tilt0=TH0 + 8, tilt1=TH1)
mod_cb = P.gn_modifier(back, g_cb)
P.gn_set(mod_cb, g_cb, "Lift", 0.0, frame=CON0); P.gn_set(mod_cb, g_cb, "Lift", 1.0, frame=CON1 + 4)
# nerv impulslari (8-kadr): asosiy nerv bo'ylab
for k_ in range(5):
    pu = P.sphere(f"pulse{k_}", 0.11, (0, 0, 0), CM["pulse"], scale=(2.2, 1, 1), seg=12)
    fp = pu.constraints.new("FOLLOW_PATH"); fp.target = nerve_main; fp.use_fixed_location = True; fp.use_curve_follow = True
    for f, v in ((1, -0.2), (338 + k_ * 2, -0.2), (352 + k_ * 2, 1.15)):
        fp.offset_factor = max(0.0, min(1.0, v)); fp.keyframe_insert("offset_factor", frame=f)
    vis(pu, [(338 + k_ * 2, 352 + k_ * 2)])
    pu.parent = None
nerve_main.data.use_path = True
for nm, loc, rot, en, size, col in (("cx_key", (-4, -14, 9), (R(55), 0, R(-15)), 12000, 12, (1.0, 0.95, 0.9)),
                                     ("cx_rim", (6, 6, 8), (R(-45), 0, R(150)), 5000, 8, (0.6, 0.75, 1.0)),
                                     ("cx_low", (5, -9, -6), (R(115), 0, R(30)), 2500, 8, (1.0, 0.7, 0.6))):
    l = P.link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA"))); l.data.energy = en; l.data.size = size
    l.data.color = col; l.location = CX + Vector(loc); l.rotation_euler = rot; par(l, cx_root)
vis(cx_root, rng(4, 5, 8))
for mu in muscles: vis(mu, rng(4, 5, 8))

# =================================================================== 4) RENTGEN (Megan, shaffof)
xr_root = set_root("SET_xray"); xr_root.location = XR
xroot, xgirl, xmesh = mc.load_character("xgirl", "Megan.fbx")
XB = P.xray_mat("xray_body", (0.25, 0.65, 1.0), 2.2, 0.03)
XC = P.xray_mat("xray_cloth", (0.2, 0.45, 0.9), 0.8, 0.0)
for o in xmesh:
    o.data.materials.clear(); o.data.materials.append(XB if o.name.endswith(("Body",)) else XC)
    pass
xroot.location = XR; xroot.rotation_euler.z = R(15)
mc.add_strip(xgirl, A("Breathing_Idle.fbx"), 200, repeat=2.0, speed=1.0)
sc.frame_set(318)
bpy.context.view_layer.update()
def bpos(nm, ht=0.0):
    pb = xgirl.pose.bones["mixamorig:" + nm]
    return (xgirl.matrix_world @ pb.head).lerp(xgirl.matrix_world @ pb.tail, ht)
BRAIN = mat("brain", (0.95, 0.45, 0.55), 0.35, emit=1.0, emit_col=(1.0, 0.35, 0.5))
brn = P.sphere("brain", 1.0, (0, 0, 0), BRAIN, scale=(0.072, 0.085, 0.064), seg=48)
dd = brn.modifiers.new("gyri", "DISPLACE"); tx = bpy.data.textures.new("gyri", "VORONOI"); tx.noise_scale = 0.18
tx.noise_scale = 0.28; dd.texture = tx; dd.strength = 0.11; dd.texture_coords = "LOCAL"
brn.modifiers.new("sub", "SUBSURF").levels = 1
hp = bpos("Head", 0.0); ht_ = bpos("Head", 1.0)
brn.location = hp.lerp(ht_, 0.62) + Vector((0, 0.005, 0))
cc_ = brn.constraints.new("CHILD_OF"); cc_.target = xgirl; cc_.subtarget = "mixamorig:Head"
bpy.context.view_layer.update()
cc_.inverse_matrix = (xgirl.matrix_world @ xgirl.pose.bones["mixamorig:Head"].matrix).inverted()
emB = bsdf(BRAIN).inputs["Emission Strength"]
for f, v in ((1, 0.3), (240, 0.3), (262, 2.2), (296, 1.0), (340, 1.0)):
    emB.default_value = v; emB.keyframe_insert("default_value", frame=f)
NRV = P.emit_mat("xnerve", (0.35, 0.8, 1.0), 1.2)
paths = [["Head", "Neck", "Spine2", "Spine1", "Spine", "Hips"],
         ["Spine2", "RightShoulder", "RightArm", "RightForeArm", "RightHand"],
         ["Spine2", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand"],
         ["Hips", "RightUpLeg", "RightLeg", "RightFoot"], ["Hips", "LeftUpLeg", "LeftLeg", "LeftFoot"]]
xcurves = []
for pi, chain in enumerate(paths):
    pts = []
    for bi, bn in enumerate(chain):
        p = bpos(bn, 0.35 if bn == "Head" else 0.0)
        pts.append(p + Vector((0, 0.03 if bn.startswith("Spine") or bn in ("Hips", "Neck") else 0.0, 0)))
    if pi in (1, 2): pts.append(bpos(chain[-1], 1.0))
    cu = bpy.data.curves.new(f"xn{pi}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0025 if pi else 0.0045
    spl = cu.splines.new("POLY"); spl.points.add(len(pts) - 1)
    for pt, p in zip(spl.points, pts): pt.co = (*p, 1)
    o = P.link(bpy.data.objects.new(f"xnerve{pi}", cu)); cu.materials.append(NRV); cu.use_path = True; par(o, xr_root)
    xcurves.append(o)
PUL = P.emit_mat("xpulse", (1.0, 0.85, 0.35), 120.0)
for pi, cuo in enumerate(xcurves):
    for k_ in range(3):
        pu = P.sphere(f"xpulse{pi}_{k_}", 0.016, (0, 0, 0), PUL, scale=(1, 1, 1), seg=12)
        fp = pu.constraints.new("FOLLOW_PATH"); fp.target = cuo; fp.use_fixed_location = True
        t0 = 298 + k_ * 9 + (12 if pi else 0)
        for f, v in ((1, 0.0), (t0, 0.0), (t0 + 16, 1.0)):
            fp.offset_factor = v; fp.keyframe_insert("offset_factor", frame=f)
        vis(pu, [(t0, t0 + 16)])
par(xroot, xr_root)
dark_floor = box("xr_floor", (12, 12, 0.02), K(XR + Vector((0, 0, -0.01))), mat("xr_floor", (0.004, 0.006, 0.01), 0.25, coat=0.6)); par(dark_floor, xr_root)
vis(xr_root, rng(6, 7))

# =================================================================== 5) QORLI O'RMON (ajdod)
fo_root = set_root("SET_forest"); fo_root.location = FO
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=200, y_segments=200, size=40)
ground = P.mesh_obj("fo_ground", bm, P.tex_image_mat("ph_snow2", PH + "snow_02", 0.6)); ground.location = FO
dm = ground.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new("gr", "CLOUDS"); tx.noise_scale = 3.0; dm.texture = tx
dm.strength = 0.35; dm.mid_level = 0.6; P.smooth(ground); par(ground, fo_root)
rockm = P.tex_image_mat("ph_rock", PH + "rock_face", 0.6, tint=(0.75, 0.75, 0.8))
for i, (x, y, s) in enumerate(((-2.6, 2.2, 0.9), (3.2, 3.5, 1.3), (-5, 8, 1.8), (6, 10, 2.2), (-1.8, -5.0, 0.5), (-3.5, -6, 0.7))):
    rk = P.sphere(f"rock{i}", s, K(FO + Vector((x, y, s * 0.25))), rockm, scale=(1.2, 1, 0.7), seg=32)
    d = rk.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("rk", "VORONOI"); t.noise_scale = 0.6 * s; d.texture = t; d.strength = 0.4 * s
    par(rk, fo_root)
    cap = P.sphere(f"rockcap{i}", s * 0.95, K(FO + Vector((x, y, s * 0.42))), snowm, scale=(1.15, 0.95, 0.35), seg=24); par(cap, fo_root)
pine_m = mat("pine", (0.03, 0.08, 0.04), 0.8)
pine_snow = mat("pine_snow", (0.85, 0.88, 0.95), 0.6)
rr4 = random.Random(3)
for i in range(40):
    ang = rr4.uniform(0, 2 * math.pi); dist = rr4.uniform(9, 24)
    x, y = dist * math.cos(ang), dist * math.sin(ang)
    if y < -6 and abs(x) < 5: continue
    h = rr4.uniform(6, 11)
    for lv in range(5):
        rr_l = h * 0.28 * (1 - lv / 5.5); z = h * 0.18 + lv * h * 0.16
        c = P.cyl("pine_c", 1, 1, (0, 0, 0), pine_m, verts=10, bevel=False)
        bmc = c.data; c.scale = (rr_l, rr_l, h * 0.3); c.location = FO + Vector((x, y, z))
        # konus: yuqori uchini qisish
        for v in bmc.vertices:
            if v.co.z > 0: v.co.x *= 0.05; v.co.y *= 0.05
        c.data.materials.append(pine_snow); c.data.polygons.foreach_set("material_index", [1 if p.normal.z > 0.97 else 0 for p in c.data.polygons])
        c.data.materials[0] = pine_m
        par(c, fo_root)
eyes_m = P.emit_mat("eyes", (0.9, 1.0, 0.3), 90.0)
for i, (x, y, z) in enumerate(((1.1, -8, 0.85), (-0.6, -9.5, 0.8), (2.6, -10.5, 0.95))):
    for s_ in (-0.08, 0.08):
        e = P.sphere(f"eye{i}", 0.045, K(FO + Vector((x + s_, y, z))), eyes_m, seg=12); par(e, fo_root)
        for f, sz in ((1, 0.05), (730 + i * 4, 0.05), (734 + i * 4, 1.0), (760 + i * 6, 1.0), (762 + i * 6, 0.1), (765 + i * 6, 1.0)):
            e.scale = (1, 1, sz); e.keyframe_insert("scale", frame=f)
    bush = P.sphere(f"bush{i}", 1.0, K(FO + Vector((x, y - 0.7, 0.3))), pine_m, scale=(1.4, 0.8, 0.8), seg=16); par(bush, fo_root)
sn_fo = P.mesh_obj("snow_forest", bmesh.new()); sn_fo.location = FO + Vector((0, -2, -0.3)); par(sn_fo, fo_root)
P.gn_modifier(sn_fo, P.snow_gn("snow_fo", 3000, (12, 12, 6), 0.7, 0.0075, snow_mat()))

aroot, anc, amesh = mc.load_character("anc", "Brute.fbx"); tame(amesh, 0.7)
for o in list(amesh):                       # bolta va sirg'alarni butunlay o'chirish (vis() hide_render ni qayta yoqadi)
    if o.name.endswith(("GEO", "Earrings")): amesh.remove(o); bpy.data.objects.remove(o, do_unlink=True)
FUR = mat("fur", (0.16, 0.09, 0.045), 0.55)
nt = FUR.node_tree; g_ = P.G(nt); oi = nt.nodes.new("ShaderNodeObjectInfo")
nt.links.new(g_.mixcol(oi.outputs["Random"], (0.1, 0.055, 0.03), (0.3, 0.19, 0.1)), bsdf(FUR).inputs["Base Color"])
fur_src = P.hair_strand_mesh("fur_src", 1.0, 0.032, 0.005, 0.38); fur_src.data.materials.append(FUR)
fur_src.location = (0, 0, -800); fur_src.hide_render = True
fur_mods = []
for o in amesh:
    if o.name.endswith(("Body", "Bottoms")):
        o.add_rest_position_attribute = True
        g = P.fur_gn("fur_" + o.name, fur_src, density=26000 if o.name.endswith("Body") else 16000, length=0.06, max_y=1.86)
        fur_mods.append((P.gn_modifier(o, g), g))
def fur(f, l, ln=1.0):
    for md, g in fur_mods:
        P.gn_set(md, g, "Lift", l, frame=f); P.gn_set(md, g, "Length", 6.0 * ln, frame=f)
for f, l, ln in ((535, 0.1, 1.0), (603, 0.1, 1.0), (612, 0.1, 1.0), (640, 0.55, 1.15), (724, 0.55, 1.15),
                 (725, 0.12, 1.0), (748, 0.12, 1.0), (758, 0.68, 1.45), (NF, 0.68, 1.45)):
    fur(f, l, ln)
aroot.location = FO; aroot.rotation_euler.z = R(0)
mc.add_strip(anc, A("Breathing_Idle.fbx"), 520, repeat=1.0, speed=1.0)
strip_at(anc, "Reacting.fbx", 742, src_frame=10, speed=1.2, blend=4)
strip_at(anc, "Roar.fbx", 778, src_frame=28, speed=1.0, blend=0)
par(aroot, fo_root)
for nm, loc, rot, en, size, col in (("fo_key", (-3, -4, 4), (R(55), 0, R(-35)), 450, 4, (0.85, 0.9, 1.0)),
                                     ("fo_rim", (2.5, 3, 3.2), (R(-55), 0, R(140)), 600, 3, (1.0, 0.8, 0.6))):
    l = P.link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA"))); l.data.energy = en; l.data.size = size
    l.data.color = col; l.location = FO + Vector(loc); l.rotation_euler = rot; par(l, fo_root)
    for f, k_ in ((1, 1.0), (725, 0.25), (778, 0.6)):
        l.data.energy = en * k_; l.data.keyframe_insert("energy", frame=f)
    all_const(l.data)
# issiqlik kamerasi (13-kadr)
TH = [S[13]]
for o in amesh:
    for m in o.data.materials:
        if m and "THERMAL" not in m.node_tree.nodes: P.thermal(m, TH, "body" if o.name.endswith("Body") or "Eye" in m.name else "fur")
P.thermal(FUR, TH, "fur")
for m in (bpy.data.materials["ph_snow2"], rockm, snowm, pine_m, pine_snow):
    P.thermal(m, TH, "cold")
vis(fo_root, rng(11, 12, 13, 14, 15))

# =================================================================== OSMON / DUNYO (har kadr uchun)
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
nt = w.node_tree; N = nt.nodes; L = nt.links
def envtex(fn, rot):
    e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + fn)
    mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(rot))
    L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], e.inputs[0]); return e
eA = envtex("winter_evening.hdr", 160); eB = envtex("snowy_forest.hdr", 30)
mixE = N.new("ShaderNodeMix"); mixE.data_type = "RGBA"; L.new(eA.outputs[0], mixE.inputs[6]); L.new(eB.outputs[0], mixE.inputs[7])
mixS = N.new("ShaderNodeMix"); mixS.data_type = "RGBA"; L.new(mixE.outputs[2], mixS.inputs[6])
bg = N["Background"]; L.new(mixS.outputs[2], bg.inputs[0])
WT = {  # kadr: (A/B, qattiq rang ulushi, qattiq rang, kuch)
    1: (0, 0, (0, 0, 0), 0.9), 2: (0, 0, (0, 0, 0), 0.5), 16: (0, 0, (0, 0, 0), 0.9),
    3: (0, 1, (0.03, 0.018, 0.014), 1), 9: (0, 1, (0.03, 0.018, 0.014), 1), 10: (0, 1, (0.03, 0.018, 0.014), 1), 17: (0, 1, (0.03, 0.018, 0.014), 1),
    4: (0, 1, (0.004, 0.003, 0.004), 1), 5: (0, 1, (0.004, 0.003, 0.004), 1), 8: (0, 1, (0.004, 0.003, 0.004), 1),
    6: (0, 1, (0.0, 0.004, 0.01), 1), 7: (0, 1, (0.0, 0.004, 0.01), 1),
    11: (1, 0, (0, 0, 0), 1.0), 12: (1, 0, (0, 0, 0), 1.0), 13: (1, 1, (0.03, 0.0, 0.12), 1),
    14: (1, 0.6, (0.002, 0.004, 0.012), 0.28), 15: (1, 0.5, (0.004, 0.008, 0.02), 0.35)}
for s_, (ab, so, col, stg) in WT.items():
    f = S[s_][0]
    mixE.inputs[0].default_value = ab; mixE.inputs[0].keyframe_insert("default_value", frame=f)
    mixS.inputs[0].default_value = so; mixS.inputs[0].keyframe_insert("default_value", frame=f)
    mixS.inputs[7].default_value = (*col, 1); mixS.inputs[7].keyframe_insert("default_value", frame=f)
    bg.inputs[1].default_value = stg; bg.inputs[1].keyframe_insert("default_value", frame=f)
all_const(nt)

# =================================================================== KAMERALAR
cams = {}
def C(n, lens, fstop=None, focus=None):
    c, t = camera(f"cam{n:02d}", lens, fstop, focus); cams[n] = c; return c, t
gh = head_target("girl_head_t", girl)
# 1: ILGAK — qorli ko'cha, pastdan keng ob'ektiv bilan tez push-in
c, t = C(1, 18, 4.0)
cam_move(c, t, *S[1], (0.9, -3.6, 0.3), (0.35, -1.55, 0.75), (0, 0, 1.15), (0, 0, 1.3), "out")
# 2: yuzga yaqin, chaqmoq, crash zoom
c, t = C(2, 50, 2.8, focus=gh)
c.constraints["Track To"].target = gh
cam_move(c, t, *S[2], (0.35, -1.55, 1.55), (0.2, -1.15, 1.5), (0, 0, 0), (0, 0, 0), "out", shake=[(45, 58, 0.025)],
         lens=(42, 62, "out"), tgt_obj_follow=True)
# 3: makro teri ustida sirpanish
c, t = C(3, 32, 5.6)
cam_move(c, t, *S[3], K(SK + Vector((-6.5, -5.5, 3.2))), K(SK + Vector((-1.5, -4.8, 2.4))),
         K(SK + Vector((-3.5, -1.0, 0.2))), K(SK + Vector((1.5, -0.5, 0.3))), "inout")
# 4: teri sirtidan kesimga sho'ng'ish
c, t = C(4, 24, 8.0)
cam_move(c, t, *S[4], K(CX + Vector((-0.5, -2.5, 5.5))), K(CX + Vector((0.4, -9.5, -1.0))),
         K(CX + Vector((0.0, 1.5, 0.0))), K(CX + Vector((0.2, 0, -1.4))), "inout")
# 5: follikula va mushak yaqin, aylanma
c, t = C(5, 40, 4.0)
cam_move(c, t, *S[5], K(CX + Vector((-0.8, -4.6, -0.4))), K(CX + Vector((3.6, -4.0, -1.3))),
         K(CX + Vector((1.6, 0, -0.9))), K(CX + Vector((1.9, 0, -0.85))), "inout")
# 6: rentgen bosh, push-in
xh = head_target("xgirl_head_t", xgirl, ht=0.5)
c, t = C(6, 35, 2.8, focus=xh)
c.constraints["Track To"].target = xh
cam_move(c, t, *S[6], K(XR + Vector((0.95, -1.35, 1.72))), K(XR + Vector((0.4, -0.62, 1.62))),
         (0, 0, 0), (0, 0, 0), "inout", lens=(30, 42, "inout"), tgt_obj_follow=True)
# 7: rentgen tana, signal pastga oqadi
c, t = C(7, 26, 4.0)
cam_move(c, t, *S[7], K(XR + Vector((-0.75, -1.35, 1.55))), K(XR + Vector((-0.35, -1.55, 0.95))),
         K(XR + Vector((0, 0, 1.35))), K(XR + Vector((0.05, 0, 0.95))), "inout")
# 8: kesim keng plan, hamma mushaklar qisqaradi
c, t = C(8, 24, 8.0)
cam_move(c, t, S[8][0], CON0 - 1, K(CX + Vector((-1.0, -14.0, 0.2))), K(CX + Vector((-0.4, -12.5, 0.0))),
         K(CX + Vector((0, 0, -1.0))), K(CX + Vector((0, 0, -0.9))), "inout")
cam_move(c, t, CON0, S[8][1], K(CX + Vector((-0.4, -12.5, 0.0))), K(CX + Vector((0.6, -11.0, 0.6))),
         K(CX + Vector((0, 0, -0.9))), K(CX + Vector((0.2, 0, -0.4))), "out", shake=[(CON0, CON0 + 14, 0.12)])
# 9: teri sathidan past burchak, tuklar "o'rmoni"
c, t = C(9, 16, 4.0)
cam_move(c, t, *S[9], K(SK + Vector((-7.5, -6.5, 0.75))), K(SK + Vector((-5.5, -4.8, 0.9))),
         K(SK + Vector((0, 0, 1.6))), K(SK + Vector((1, 1, 1.8))), "lin")
# 10: yuqoridan aylanib sirpanish, do'mboqlar o'sadi
c, t = C(10, 26, 5.6)
for f in range(S[10][0], S[10][1] + 1):
    u = (f - S[10][0]) / (S[10][1] - S[10][0]); a = R(-130 + 70 * P.ease(u, "inout"))
    rad_ = 6.2 - 1.6 * u
    c.location = SK + Vector((rad_ * math.cos(a), rad_ * math.sin(a), 4.6 - 1.6 * u)); c.keyframe_insert("location", frame=f)
    t.location = SK + Vector((0.3 * u, 0, 0.1)); t.keyframe_insert("location", frame=f)
# 11: ajdod, past burchakdan aylanma keng plan
c, t = C(11, 16)
for f in range(S[11][0], S[11][1] + 1):
    u = P.ease((f - S[11][0]) / (S[11][1] - S[11][0]), "inout"); a = R(-125 + 55 * u)
    c.location = FO + Vector((2.4 * math.cos(a), 2.4 * math.sin(a), 0.28 + 0.15 * u)); c.keyframe_insert("location", frame=f)
    t.location = FO + Vector((0, 0, 1.3)); t.keyframe_insert("location", frame=f)
# 12: jun makro (yelka)
ash = head_target("anc_shoulder_t", anc, "mixamorig:LeftArm", 0.25)
c, t = C(12, 55, 2.8, focus=ash)
c.constraints["Track To"].target = ash
cam_move(c, t, *S[12], K(FO + Vector((1.25, -0.75, 1.75))), K(FO + Vector((0.95, -0.55, 1.62))), (0, 0, 0), (0, 0, 0), "inout",
         tgt_obj_follow=True)
# 13: issiqlik kamerasi, o'rtacha plan
c, t = C(13, 30)
cam_move(c, t, *S[13], K(FO + Vector((-1.4, -3.0, 1.4))), K(FO + Vector((-0.9, -2.3, 1.45))),
         K(FO + Vector((0, 0, 1.25))), K(FO + Vector((0, 0, 1.3))), "inout")
# 14: yelka ortidan: qorong'ida ko'zlar, jun hurpayadi; crash zoom
ahd = head_target("anc_head_t", anc)
c, t = C(14, 24, 2.8)
cam_move(c, t, *S[14], K(FO + Vector((0.75, 1.2, 1.95))), K(FO + Vector((0.55, 0.9, 1.9))),
         K(FO + Vector((1.0, -8, 0.7))), K(FO + Vector((1.1, -8, 0.62))), "inout", shake=[(756, 770, 0.03)],
         lens=(24, 24, "lin"))
for f, l in ((725, 24), (752, 24), (760, 38)):
    c.data.lens = l; c.data.keyframe_insert("lens", frame=f)
c.data.dof.focus_object = None
for f, d_ in ((725, 9.5), (751, 9.5), (756, 1.1)):
    c.data.dof.focus_distance = d_; c.data.dof.keyframe_insert("focus_distance", frame=f)
# 15: juda past burchak, bo'kirish
c, t = C(15, 14, 5.6)
cam_move(c, t, *S[15], K(FO + Vector((0.6, -1.9, 0.12))), K(FO + Vector((0.25, -1.35, 0.22))),
         K(FO + Vector((0, 0, 1.75))), K(FO + Vector((0, 0, 1.85))), "out", shake=[(800, 850, 0.035)])
# 16: qiz o'z qo'llariga qaraydi
c, t = C(16, 28, 2.8, focus=gh)
cam_move(c, t, *S[16], (-1.5, -1.6, 1.25), (0.9, -1.85, 1.35), (0, 0, 1.2), (0, 0, 1.25), "inout")
# 17: makro: do'mboqlar qaytadi -> kamera ko'tariladi, qorong'ilik
c, t = C(17, 38, 5.6)
cam_move(c, t, *S[17], K(SK + Vector((2.5, -4.2, 1.6))), K(SK + Vector((1.2, -5.5, 6.2))),
         K(SK + Vector((0.6, -0.6, 0.2))), K(SK + Vector((0.2, -0.2, 0.0))), "inout")
for n, c in cams.items():
    sc.timeline_markers.new(c.name, frame=S[n][0]).camera = c
sc.camera = cams[1]

# =================================================================== RENDER
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 12)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", -0.2))
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
