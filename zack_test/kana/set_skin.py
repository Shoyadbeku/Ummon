# Teri makro sahnasi (kadrlar 2-10 va 12): teri yuzasi, kesim (epidermis/derma/yog'), tomirlar, nervlar,
# protsedural kana, pinset (BlenderKit), baliq ilmog'i, sement, so'lak, shishish.
# 1 birlik ~ 2.5 mm. Kana og'zi (0,0,0) atrofida, boshi +X ga qaragan.
import bpy, bmesh, math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import common as C
import tick as T

R = math.radians
random.seed(7)
s = C.reset()
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
CUTY = 0.012           # kesim yuzasi (y = CUTY), x > CUTX qismida
CUTX = -0.25

# kadrlar
S2, S3, S4, S5, S6, S7, S8, S9, S10, S12a, S12b = (63, 134), (135, 232), (233, 300), (301, 374), (375, 415), \
    (416, 460), (461, 535), (536, 624), (625, 682), (740, 810), (811, 888)
CUT_RANGES = [(S3[0], S10[1])]
FULL_RANGES = [S2, (S12a[0], S12b[1])]
RANGES = [(S2[0], S10[1]), (S12a[0], S12b[1])]

# ================= materiallar =================
def skin_mat():
    m = C.mat("skin", (0.8, 0.5, 0.38), 0.55, sss=0.5, sss_r=(1.0, 0.4, 0.22), sss_scale=0.08, coat=0.0)
    N = m.node_tree.nodes; L = m.node_tree.links; b = C.principled(m)
    tc = N.new("ShaderNodeTexCoord")
    # rang dog'lari
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.8; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(nz.outputs["Fac"], mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.82, 0.5, 0.37, 1); mx.inputs[7].default_value = (0.7, 0.38, 0.28, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    # teri chiziqlari (ajinlar): voronoi chegaralari
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 2.6; vo.inputs["Randomness"].default_value = 1.0
    nd = N.new("ShaderNodeTexNoise"); nd.inputs["Scale"].default_value = 3; L.new(tc.outputs["Object"], nd.inputs["Vector"])
    mv = N.new("ShaderNodeMix"); mv.data_type = "VECTOR"; mv.inputs["Factor"].default_value = 0.25
    L.new(tc.outputs["Object"], mv.inputs[4]); L.new(nd.outputs["Color"], mv.inputs[5]); L.new(mv.outputs[1], vo.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.06
    L.new(vo.outputs["Distance"], mr.inputs["Value"])
    # teshikchalar (poralar)
    vp = N.new("ShaderNodeTexVoronoi"); vp.inputs["Scale"].default_value = 9; L.new(tc.outputs["Object"], vp.inputs["Vector"])
    mp = N.new("ShaderNodeMapRange"); mp.inputs["From Min"].default_value = 0.0; mp.inputs["From Max"].default_value = 0.1
    L.new(vp.outputs["Distance"], mp.inputs["Value"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(mr.outputs[0], mul.inputs[0]); L.new(mp.outputs[0], mul.inputs[1])
    fine = N.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 30; L.new(tc.outputs["Object"], fine.inputs["Vector"])
    add = N.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; L.new(fine.outputs["Fac"], add.inputs[0])
    add.inputs[1].default_value = 0.15; L.new(mul.outputs[0], add.inputs[2])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; bp.inputs["Distance"].default_value = 0.01
    L.new(add.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    # ajin ichida biroz qizilroq
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; L.new(mr.outputs[0], mx2.inputs["Factor"])
    mx2.inputs[6].default_value = (0.66, 0.36, 0.3, 1); L.new(mx.outputs[2], mx2.inputs[7]); L.new(mx2.outputs[2], b.inputs["Base Color"])
    return m

def section_mat():
    """Kesim: chuqurlikka (z) qarab qatlamlar: shox qavat, epidermis, derma (tolali), yog'."""
    m = C.mat("section", (0.7, 0.3, 0.3), 0.45, sss=0.35, sss_r=(1, 0.3, 0.2), sss_scale=0.05, coat=0.25)
    N = m.node_tree.nodes; L = m.node_tree.links; b = C.principled(m)
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ad = N.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"; L.new(nz.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 0.08
    L.new(sep.outputs["Z"], ad.inputs[2])
    ramp = N.new("ShaderNodeValToRGB"); L.new(ad.outputs[0], ramp.inputs[0])
    cr = ramp.color_ramp; cr.interpolation = "EASE"
    # ad = z + 0.08*noise (≈ z + 0.04); ramp 0..1 ni z [-2..0] ga moslash uchun MapRange
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -2.0; mr.inputs["From Max"].default_value = 0.04
    L.new(ad.outputs[0], mr.inputs["Value"]); L.new(mr.outputs[0], ramp.inputs[0])
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.92, 0.72, 0.28, 1)        # yog'
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.95, 0.85, 0.72, 1)        # shox qavat
    for pos, col in ((0.52, (0.93, 0.74, 0.3)), (0.56, (0.62, 0.16, 0.16)), (0.9, (0.72, 0.26, 0.24)),
                     (0.935, (0.85, 0.55, 0.45)), (0.975, (0.86, 0.6, 0.5))):
        e = cr.elements.new(pos); e.color = (*col, 1)
    # tolalar (derma kollageni) va yog' bo'laklari
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 4; wv.inputs["Distortion"].default_value = 12
    wv.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 5; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    vf = N.new("ShaderNodeTexVoronoi"); vf.feature = "DISTANCE_TO_EDGE"; vf.inputs["Scale"].default_value = 5
    L.new(tc.outputs["Object"], vf.inputs["Vector"])
    fat_mask = N.new("ShaderNodeMapRange"); fat_mask.inputs["From Min"].default_value = -0.85; fat_mask.inputs["From Max"].default_value = -0.95
    L.new(ad.outputs[0], fat_mask.inputs["Value"])
    h = N.new("ShaderNodeMix"); h.data_type = "FLOAT"; L.new(fat_mask.outputs[0], h.inputs["Factor"])
    L.new(wv.outputs["Fac"], h.inputs[2]); L.new(vf.outputs["Distance"], h.inputs[3])
    dk = N.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"; dk.inputs["Factor"].default_value = 0.35
    L.new(ramp.outputs[0], dk.inputs[6]); L.new(wv.outputs["Color"], dk.inputs[7])
    L.new(dk.outputs[2], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.02
    L.new(h.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

M = dict(skin=skin_mat(), section=section_mat(),
         vessel=C.mat("vessel", (0.42, 0.015, 0.02), 0.25, coat=0.8, sss=0.4, sss_r=(1, 0.1, 0.1), sss_scale=0.05),
         vein=C.mat("vein", (0.18, 0.04, 0.12), 0.3, coat=0.8, sss=0.3, sss_r=(0.6, 0.2, 0.6), sss_scale=0.05),
         nerve=C.mat("nerve", (0.95, 0.75, 0.15), 0.35, emit=1.5, emit_col=(1.0, 0.75, 0.1)),
         hair=C.mat("hair", (0.09, 0.055, 0.035), 0.35, coat=0.3, sss=0.2, sss_r=(1, 0.6, 0.3), sss_scale=0.01),
         steel=C.mat("steel", (0.8, 0.8, 0.82), 0.12, metal=1.0),
         cement=C.mat("cement", (0.9, 0.86, 0.72), 0.08, coat=1.0, sss=0.3, sss_r=(1, 0.9, 0.6), sss_scale=0.03),
         wound=C.mat("wound", (0.25, 0.01, 0.01), 0.15, coat=1.0),
         blood=C.mat("blood", (0.3, 0.0, 0.01), 0.1, coat=1.0))
# so'lak: kesim yuzasida tarqaluvchi ko'k dog' (markazdan chetga qarab shaffoflashadi)
sal = bpy.data.materials.new("saliva"); sal.use_nodes = True
N = sal.node_tree.nodes; L = sal.node_tree.links; out = N["Material Output"]
for n in list(N):
    if n != out: N.remove(n)
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.1, 0.5, 1.0, 1); em.inputs["Strength"].default_value = 4.0
tr = N.new("ShaderNodeBsdfTransparent"); mxs = N.new("ShaderNodeMixShader")
tc = N.new("ShaderNodeTexCoord"); vl = N.new("ShaderNodeVectorMath"); vl.operation = "LENGTH"; L.new(tc.outputs["Object"], vl.inputs[0])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 8; L.new(tc.outputs["Object"], nz.inputs["Vector"])
ad = N.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"; L.new(nz.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 0.6
L.new(vl.outputs["Value"], ad.inputs[2])
mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 1.2; mr.inputs["From Max"].default_value = 0.4
L.new(ad.outputs[0], mr.inputs["Value"])
ml = N.new("ShaderNodeMath"); ml.operation = "MULTIPLY"; L.new(mr.outputs[0], ml.inputs[0]); ml.inputs[1].default_value = 0.85
gm = N.new("ShaderNodeNewGeometry"); sz = N.new("ShaderNodeSeparateXYZ"); L.new(gm.outputs["Position"], sz.inputs[0])
lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; L.new(sz.outputs["Z"], lt.inputs[0]); lt.inputs[1].default_value = -0.04
m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; L.new(ml.outputs[0], m2.inputs[0]); L.new(lt.outputs[0], m2.inputs[1])
L.new(m2.outputs[0], mxs.inputs[0]); L.new(tr.outputs[0], mxs.inputs[1]); L.new(em.outputs[0], mxs.inputs[2])
L.new(mxs.outputs[0], out.inputs["Surface"])
M["saliva"] = sal

# ================= teri bloki =================
cutter = C.box("cutter", (14, 14, 6), (CUTX + 7, CUTY - 7, -1.0), None)
cutter.hide_render = True; cutter.hide_viewport = True; cutter.display_type = "WIRE"

def add_cut(o):
    bo = o.modifiers.new("cut", "BOOLEAN"); bo.object = cutter; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"
    marks = sorted({1} | {a for a, b in CUT_RANGES} | {b + 1 for a, b in CUT_RANGES})
    for f in marks:
        on = any(a <= f <= b for a, b in CUT_RANGES)
        bo.show_render = on; bo.keyframe_insert("show_render", frame=f)
        bo.show_viewport = on; bo.keyframe_insert("show_viewport", frame=f)
    return bo

block = C.box("block", (14, 14, 2.6), (0, 0, -1.3 - 0.003), M["section"])
add_cut(block)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=220, y_subdivisions=220, size=14, location=(0, 0, 0))
skin = bpy.context.object; skin.name = "skin"; skin.data.materials.append(M["skin"]); C.smooth(skin)
# teri ostidagi mayda notekisliklar
dsp = skin.modifiers.new("disp", "DISPLACE"); tx = bpy.data.textures.new("skinbump", "CLOUDS"); tx.noise_scale = 1.2
dsp.texture = tx; dsp.strength = 0.04; dsp.mid_level = 0.5; dsp.texture_coords = "GLOBAL"
so = skin.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.03; so.offset = -1
add_cut(skin)

# ================= kana =================
def leg_fn(side, i, base, tip, lift):
    # yaqin tomondagi oyoqlar kesilgan chorakka tushmasin
    if side < 0 and tip.x > CUTX - 0.05 and tip.y < CUTY + 0.15:
        a = math.atan2(tip.y - base.y, tip.x - base.x) - R(40 + 15 * (3 - i))
        L_ = (tip - base).length
        tip = base + Vector((math.cos(a), math.sin(a), 0)) * L_; tip.z = 0.012
    return tip, lift
tk = T.build("tick", tilt=38, leg_tip_fn=leg_fn, loc=(0, 0, 0.045))
ROOT0 = Vector(tk["root"].location)
# xipostom: S3 da qisqa (yuzada), S4 da kiradi
hg = tk["hypo_grp"]
C.key(hg, 1, scale=(0.2, 1, 1)); C.key(hg, S4[0] + 6, scale=(0.2, 1, 1)); C.key(hg, S4[1] - 8, scale=(1, 1, 1))
# xelitseralar: S3 da navbat bilan kesadi
for e in (tk["cheL"], tk["cheR"]):
    C.key(e, 1, loc=tuple(e.location))
for k, f in enumerate(range(S3[0], S4[0] + 30, 6)):
    for j, e in enumerate((tk["cheL"], tk["cheR"])):
        x0 = -0.02 - 0.12 if (k + j) % 2 == 0 else -0.02 + 0.02
        e.location.x = x0; e.keyframe_insert("location", index=0, frame=f)
        e.rotation_euler.z = R(6 if (k + j) % 2 else -6) * (1 if j else -1); e.keyframe_insert("rotation_euler", index=2, frame=f)
# oyoqlarning mayda qimirlashi (pinset tortganda kuchli)
for n, e in enumerate(tk["legs"]):
    e.rotation_mode = "XYZ"; e.keyframe_insert("rotation_euler", frame=1)
    for fc in C.fcurves(e):
        if fc.data_path != "rotation_euler": continue
        nm = fc.modifiers.new("NOISE"); nm.scale = 6; nm.strength = 0.05; nm.phase = n * 3 + fc.array_index
    for f, a in ((S2[0] + 20, 0), (S2[0] + 26, 1), (S2[1], 1), (S2[1] + 1, 0)):
        for fc in C.fcurves(e):
            pass
# tishlash joyidagi kesik (S3)
entry = Vector((0.06, 0, 0.0))
wound = C.sphere("wound", 1.0, tuple(entry), M["wound"], seg=24, ring=12)
C.key(wound, 1, scale=(0.001, 0.001, 0.001)); C.key(wound, S3[0] + 10, scale=(0.001, 0.001, 0.001))
C.key(wound, S3[1] - 10, scale=(0.11, 0.035, 0.01))

chan = C.box("cut_channel", (0.16, 0.004, 0.035), (0, 0, 0), M["wound"])
chan.location = Vector((0.045, CUTY - 0.006, 0.045)) + Vector((math.cos(R(38)), 0, -math.sin(R(38)))) * 0.13
chan.rotation_euler.y = R(38)
C.key(chan, 1, scale=(0.01, 1, 0.01)); C.key(chan, S3[0] + 12, scale=(0.01, 1, 0.01)); C.key(chan, S3[1] - 6, scale=(1, 1, 1))
C.vis(chan, CUT_RANGES)

# teri "chodiri": kana tortilganda teri ko'tariladi (Hook, yumshoq so'nish)
hook_e = C.empty("tent", tuple(entry), None)
C.parent_keep(hook_e, tk["root"])
hk = skin.modifiers.new("tent", "HOOK"); hk.object = hook_e
hk.vertex_indices_set(list(range(len(skin.data.vertices))))
hk.falloff_type = "SMOOTH"; hk.falloff_radius = 0.9; hk.center = entry
hk.matrix_inverse = hook_e.matrix_world.inverted()
skin.modifiers.move(skin.modifiers.find("tent"), 0)

# kana ildizi harakati: S2 tortish, S7 orqaga tortilish
rt = tk["root"]
def rk(f, d=(0, 0, 0)):
    rt.location = ROOT0 + Vector(d); rt.keyframe_insert("location", frame=f)
pull = Vector((-0.45, 0, 0.9)).normalized()
rk(1); rk(S2[0] + 22)
for f, a in ((S2[0] + 30, 0.16), (S2[0] + 37, 0.07), (S2[0] + 46, 0.24), (S2[0] + 52, 0.12), (S2[0] + 62, 0.3), (S2[1], 0.27)):
    rk(f, pull * a)
rk(S2[1] + 1)
rk(S7[0] + 4); rk(S7[0] + 14, pull * 0.09); rk(S7[0] + 19, pull * 0.03); rk(S7[0] + 28, pull * 0.1); rk(S7[1], pull * 0.04)
rk(S7[1] + 1)

# ================= pinset (BlenderKit a4d63c90) =================
def import_glb(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]
tw_new = import_glb(BK + "a4d63c90_u.glb")
tw_root = next(o for o in tw_new if o.type == "EMPTY")
twg = C.empty("tweezers_grp", (0, 0, 0))
TS = 60.0
tw_root.parent = twg; tw_root.location = (0.085 * TS, 0, -0.0007 * TS); tw_root.scale = (TS,) * 3; tw_root.rotation_euler = (0, 0, 0)
arms = {o.name: o for o in tw_new if o.type == "MESH"}
for o in tw_new:
    if o.type == "MESH":
        o.rotation_mode = "XYZ"
d = Vector((0.5, 0.12, 0.86)).normalized(); zax = Vector((0, 1, 0)); yax = zax.cross(d).normalized(); zax = d.cross(yax)
twg.matrix_world = Matrix.Translation((0, 0, 0)) @ Matrix((d, yax, zax)).transposed().to_4x4()
grip = Vector((-0.02, 0, 0.1))
far = grip + d * 4.0
twg.keyframe_insert("rotation_euler", frame=1)
def tk_tw(f, p): twg.location = p; twg.keyframe_insert("location", frame=f)
tk_tw(1, far); tk_tw(S2[0], far); tk_tw(S2[0] + 14, grip + d * 0.05); tk_tw(S2[0] + 20, grip)
for f, a in ((S2[0] + 30, 0.16), (S2[0] + 37, 0.07), (S2[0] + 46, 0.24), (S2[0] + 52, 0.12), (S2[0] + 62, 0.3), (S2[1], 0.27)):
    tk_tw(f, grip + pull * a)
for nm, o in arms.items():
    sgn = 1 if "down" in nm else -1
    C.key(o, 1, rot=(0, 0, 0)); C.key(o, S2[0] + 16, rot=(0, 0, 0)); C.key(o, S2[0] + 21, rot=(0, sgn * -1.6, 0))
C.vis(twg, [S2])

# ================= tomirlar va nervlar (kesim yuzasida) =================
vessels = []
for zc, r, mm, wig in ((-0.45, 0.045, "vessel", 0.03), (-0.64, 0.06, "vein", 0.04), (-0.32, 0.028, "vessel", 0.05)):
    pts = [(x, CUTY + r * 0.15, zc + wig * math.sin(x * 2.3 + zc * 7)) for x in [CUTX + 0.02 + i * 0.35 for i in range(14)]]
    vessels.append(C.tube("vessel", pts, r, M[mm]))
# kapillyarlar xipostom uchi tomon
for k in range(5):
    x0 = 0.15 + k * 0.25
    pts = [(x0, CUTY + 0.01, -0.42), (x0 - 0.05, CUTY + 0.01, -0.3), (x0 - 0.08 + 0.02 * k, CUTY + 0.008, -0.16), (x0 - 0.04, CUTY + 0.006, -0.07)]
    vessels.append(C.tube("capillary", pts, 0.012, M["vessel"]))
nerves = []
for k, (zc, x0) in enumerate(((-0.2, CUTX + 0.02), (-0.5, CUTX + 0.02))):
    pts = [(x, CUTY + 0.008, zc + 0.03 * math.sin(3 * x + k)) for x in [x0 + i * 0.3 for i in range(16)]]
    nerves.append(C.tube("nerve", pts, 0.018, M["nerve"]))
for k in range(6):
    x0 = 0.05 + k * 0.32
    pts = [(x0, CUTY + 0.006, -0.2), (x0 + 0.05, CUTY + 0.006, -0.13), (x0 + 0.02, CUTY + 0.005, -0.06), (x0 + 0.06, CUTY + 0.004, -0.02)]
    nerves.append(C.tube("nerve_end", pts, 0.008, M["nerve"]))
for o in vessels + nerves:
    C.vis(o, CUT_RANGES)
# nervlar so'lakdan keyin o'chadi
ne = C.principled(M["nerve"]).inputs["Emission Strength"]
C.keyval(ne, 1, 1.5); C.keyval(ne, S10[0] + 10, 1.5); C.keyval(ne, S10[1] - 8, 0.0)
nc = C.principled(M["nerve"]).inputs["Base Color"]
C.keyval(nc, S10[0] + 10, (0.95, 0.75, 0.15, 1)); C.keyval(nc, S10[1] - 8, (0.35, 0.3, 0.22, 1))

# ================= baliq ilmog'i (S6) =================
HX = 1.9
HY = -0.09
hook_pts = [(HX - 0.35, HY, 0.9), (HX - 0.35, HY, -0.02), (HX - 0.33, HY, -0.2), (HX - 0.17, HY, -0.28),
            (HX - 0.02, HY, -0.2), (HX + 0.0, HY, -0.02)]
fh = C.tube("fishhook", hook_pts, 0.035, M["steel"], radii=[1, 1, 1, 1, 0.9, 0.5])
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.035, radius2=0.0, depth=0.16, location=(HX + 0.0, HY, 0.06))
pt = bpy.context.object; pt.data.materials.append(M["steel"]); C.smooth(pt); pt.parent = fh
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.022, radius2=0.0, depth=0.13, location=(HX - 0.045, HY, 0.0),
                                rotation=(0, R(-152), 0))
bb = bpy.context.object; bb.data.materials.append(M["steel"]); C.smooth(bb); bb.parent = fh
eye = bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.025, location=(HX - 0.35, HY, 0.95), rotation=(R(90), 0, 0))
ey = bpy.context.object; ey.data.materials.append(M["steel"]); C.smooth(ey); ey.parent = fh
C.vis(fh, [S6])

# ================= sement (S8-S9) =================
cem = []
bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.07, major_segments=48, minor_segments=16, location=(0.04, 0, 0.0))
col = bpy.context.object; col.name = "cement_collar"; col.data.materials.append(M["cement"]); C.smooth(col)
col.scale = (1.15, 1.0, 0.7)
dm = col.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("cm", "CLOUDS"); t.noise_scale = 0.08; dm.texture = t; dm.strength = 0.04
sb = col.modifiers.new("s", "SUBSURF"); sb.render_levels = 2
cem.append(col)
# ichkaridagi sement qini: xipostom bo'ylab
ax = Vector((math.cos(R(38)), 0, -math.sin(R(38))))
sheath = C.cyl("cement_sheath", 0.075, 0.17, tuple(Vector((0.04, 0, 0.0)) + ax * 0.04), M["cement"], verts=32, r2=0.045)
sheath.rotation_mode = "QUATERNION"; sheath.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(ax)
dm = sheath.modifiers.new("d", "DISPLACE"); dm.texture = t; dm.strength = 0.025
cem.append(sheath)
for o in cem:
    o.rotation_mode = o.rotation_mode
    C.key(o, 1, scale=tuple(v * 0.001 for v in o.scale))
    full = (1.15, 1.0, 0.7) if o is col else (1, 1, 1)
    C.key(o, S8[0] + 8, scale=tuple(v * 0.001 for v in full)); C.key(o, S8[1] - 10, scale=full)
    C.vis(o, [(S8[0], S10[1]), (S12a[0], S12b[1])])
cr = C.principled(M["cement"]).inputs["Roughness"]; C.keyval(cr, S9[0] + 10, 0.08); C.keyval(cr, S9[1] - 20, 0.75)
cc = C.principled(M["cement"]).inputs["Coat Weight"]; C.keyval(cc, S9[0] + 10, 1.0); C.keyval(cc, S9[1] - 20, 0.0)
cb = C.principled(M["cement"]).inputs["Base Color"]; C.keyval(cb, S9[0] + 10, (0.9, 0.86, 0.72, 1)); C.keyval(cb, S9[1] - 20, (0.78, 0.7, 0.55, 1))

# ================= so'lak (S10) =================
tipw = Vector((0.0, 0, 0.045)) + ax * 0.3
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type="TRIFAN", location=(tipw.x, CUTY - 0.004, tipw.z), rotation=(R(90), 0, 0))
sali = bpy.context.object; sali.name = "saliva"; sali.data.materials.append(M["saliva"])
C.key(sali, 1, scale=(0.01, 0.01, 0.01)); C.key(sali, S10[0], scale=(0.01, 0.01, 0.01)); C.key(sali, S10[1] - 4, scale=(0.75, 0.42, 1.0))
C.vis(sali, [S10])

# ================= tuklar =================
def hair(x, y, h):
    a = random.uniform(0, 2 * math.pi); lean = random.uniform(0.5, 0.9)
    d = Vector((math.cos(a) * lean, math.sin(a) * lean, 1 - lean * 0.6)).normalized()
    pts = []; p = Vector((x, y, -0.02))
    for i in range(6):
        pts.append(tuple(p)); p = p + d * (h / 5); d = (d + Vector((math.cos(a), math.sin(a), -0.3)) * 0.15).normalized()
    return C.tube("hair", pts, 0.013, M["hair"], radii=[1.2, 1, 0.9, 0.8, 0.6, 0.3])
hairs_in, hairs_out = [], []
for i in range(90):
    x, y = random.uniform(-6, 6), random.uniform(-6, 6)
    if math.hypot(x + 0.4, y) < 1.3 or (0.1 < x < 3.0 and -2.0 < y < 1.0): continue
    hgt = random.uniform(1.0, 2.4)
    o = hair(x, y, hgt)
    (hairs_in if (x > CUTX - 0.3 and y < CUTY + 0.4) else hairs_out).append(o)
for o in hairs_in: C.vis(o, FULL_RANGES)

# ================= shishish (S12) =================
T.engorge(tk, 1, 0.0); T.engorge(tk, S12a[0] + 6, 0.0)
for f, e in ((S12a[0] + 40, 0.25), (S12a[1], 0.5), (S12b[0] + 25, 0.8), (S12b[0] + 55, 1.0), (S12b[1], 1.04)):
    T.engorge(tk, f, e)
tl = tk["tilt"]
C.key(tl, 1, rot=(0, 38, 0)); C.key(tl, S12a[0] + 6, rot=(0, 38, 0)); C.key(tl, S12b[0] + 55, rot=(0, 52, 0))

# ================= yorug'lik =================
w, _ = C.world_hdri(os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/") + "meadow_2.hdr", 0.35, 40)
WN = w.node_tree.nodes; WL = w.node_tree.links
lp = WN.new("ShaderNodeLightPath"); bgd = WN.new("ShaderNodeBackground"); bgd.inputs[0].default_value = (0.03, 0.026, 0.026, 1)
mxw = WN.new("ShaderNodeMixShader"); WL.new(lp.outputs["Is Camera Ray"], mxw.inputs[0])
WL.new(WN["Background"].outputs[0], mxw.inputs[1]); WL.new(bgd.outputs[0], mxw.inputs[2]); WL.new(mxw.outputs[0], WN["World Output"].inputs[0])
key_l = C.light("key", "AREA", (-1.5, -2.6, 3.2), (40, 0, -30), 600, 2.5, (1.0, 0.93, 0.85))
rim = C.light("rim", "AREA", (1.5, 3.0, 1.4), (-70, 0, 160), 260, 1.5, (1.0, 0.85, 0.7))
fill = C.light("fill", "AREA", (3.0, -1.0, 1.0), (70, 0, 70), 90, 2.0, (0.75, 0.85, 1.0))
# S12: vaqt o'tishi (kun-tun) — kalit chiroq aylanadi, yorqinligi o'zgaradi
pivot = C.empty("sunpivot", (0, 0, 0)); C.parent_keep(key_l, pivot)
C.key(pivot, 1, rot=(0, 0, 0)); C.key(pivot, S12a[0], rot=(0, 0, 0)); C.key(pivot, S12b[0] + 60, rot=(0, 0, 720))
C.interp(pivot, "LINEAR")
en = key_l.data
for f, v in ((1, 600), (S12a[0], 600), (S12a[0] + 18, 160), (S12a[0] + 36, 600), (S12a[0] + 54, 160), (S12b[0], 600),
             (S12b[0] + 18, 180), (S12b[0] + 40, 650)):
    C.keyval(en, f, v, "energy")

# ================= kameralar =================
cams = []
def cam(name, f0, f1, p0, p1, t0, t1, lens, fstop=None, shake=0.0, focus=None):
    tg = C.empty(name + "_t", t0)
    c = C.camera(name, p0, tg, lens, fstop, focus=focus, clip=0.005)
    C.key(c, f0, loc=p0); C.key(c, f1, loc=p1); C.key(tg, f0, loc=t0); C.key(tg, f1, loc=t1)
    if shake: C.shake(c, f0, f1, amp=shake, freq=0.3, seed=len(cams))
    C.cut(f0, c); cams.append(c); return c, tg

mouth = (0.05, 0, 0.0)
# S2: pinset, yon past burchak, kuchli qo'l silkinishi, zoom
c2, _ = cam("c2_tweezers", S2[0], S2[1], (2.0, -2.1, 0.55), (1.35, -1.55, 0.42), (-0.25, 0, 0.25), (-0.2, 0, 0.38), 32, 2.8, shake=0.03)
# S3: old tomondan, juda past, xelitseralar
c3, _ = cam("c3_cheli", S3[0], S3[1], (0.75, -0.95, 0.12), (0.45, -0.7, 0.0), (0.12, 0, -0.04), (0.12, 0, -0.07), 45, 3.2)
# S4: kesim, yon tomondan dolly
c4, _ = cam("c4_insert", S4[0], S4[1], (0.65, -1.75, -0.05), (0.42, -1.3, -0.12), (0.12, 0, -0.08), (0.18, 0, -0.14), 32, 4.0)
# S5: tikanlar bo'ylab tracking
c5, t5 = cam("c5_barbs", S5[0], S5[1], (-0.05, -0.62, -0.1), (0.42, -0.55, -0.3), (0.1, 0, -0.06), (0.24, 0, -0.17), 50, 2.0)
# S6: baliq ilmog'i, tez orbit
c6, _ = cam("c6_hook", S6[0], S6[1], (HX + 0.9, -1.4, 0.15), (HX - 0.9, -1.35, -0.05), (HX - 0.15, 0, -0.18), (HX - 0.15, 0, -0.2), 30, 2.8)
# S7: whip-pan + silkinish, xipostom ilinadi
c7, t7 = cam("c7_snag", S7[0], S7[1], (0.55, -1.05, -0.05), (0.5, -0.95, -0.06), (1.4, 0, -0.15), (0.12, 0, -0.1), 35, 3.2, shake=0.02)
C.key(t7, S7[0] + 6, loc=(0.14, 0, -0.1))
# S8: sement chiqadi, push-in
c8, _ = cam("c8_cement", S8[0], S8[1], (0.75, -1.45, 0.2), (0.38, -0.85, 0.08), (0.0, 0, 0.0), (0.05, 0, -0.02), 30, 3.5)
# S9: sement qotadi, 90° orbit (kesimdan ustki ko'rinishgacha)
c9, t9 = cam("c9_orbit", S9[0], S9[1], (0.3, -1.35, 0.25), (1.25, -0.1, 0.9), (0.0, 0, 0.0), (-0.25, 0, 0.1), 35, 4.0)
orb = [(0.3, -1.35, 0.25), (1.0, -1.0, 0.45), (1.3, -0.45, 0.7), (1.25, -0.1, 0.9)]
for k, p in enumerate(orb): C.key(c9, int(S9[0] + (S9[1] - S9[0]) * k / 3), loc=p)
# S10: so'lak, sekin dolly
c10, _ = cam("c10_saliva", S10[0], S10[1], (0.55, -1.85, -0.25), (0.4, -1.45, -0.2), (0.25, 0, -0.25), (0.25, 0, -0.22), 30, 5.0)
# S12a: shishish, orbit
c12a, t12 = cam("c12_swell", S12a[0], S12a[1], (1.2, -3.1, 0.7), (-1.0, -3.0, 0.8), (-0.6, 0, 0.35), (-0.9, 0, 0.45), 35, 4.0)
# S12b: past burchak, keng ob'ektiv, "qahramon" kadri
c12b, _ = cam("c12_hero", S12b[0], S12b[1], (1.15, -1.25, 0.06), (0.75, -0.95, 0.05), (-0.6, 0, 0.6), (-0.7, 0, 0.75), 16, 5.6)
s.camera = c2

C.setup_render(samples=14, exposure=-0.2)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    C.render_ranges(RANGES)
