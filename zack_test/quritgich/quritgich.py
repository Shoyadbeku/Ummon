# "Qo'l quritgich — bakteriyalar" — Zack D. Films uslubida 40.5 s video (973 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py, mixchar.py, ogri/lib.py (yordamchilar), gemorroy.py (hojatxona, unitaz), aksirish.py (qo'l IK).
# Kadr rejasi: STORYBOARD.md. Assetlar: zack_test/tools/get_quritgich.sh
# Render: OUT=/tmp/claude-0/frames_q/ SAMPLES=8 PCT=40 python3 -I zack_test/quritgich/quritgich.py --render
# Sinov: FRAMES=20,60,130,200 PCT=30   |   Bo'lak: RANGE=a,b
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from lib import *            # sahnani tozalaydi; bpy, math, random, Vector, R, sc, mc ...
import numpy as np
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_q/")
random.seed(11)
END = 973
sc.frame_start, sc.frame_end = 1, END
def T(sec): return int(round(sec * 24)) + 1

# ---------------- kadrlar (Whisper so'z vaqtlari) ----------------
SHOTS = [(1, "hook"), (T(1.38), "wash"), (T(2.86), "walk"), (T(4.24), "dryer"), (T(5.94), "spray"), (T(9.24), "intake"),
         (T(13.58), "flush"), (T(15.02), "plume"), (T(17.62), "drift"), (T(18.86), "filter"), (T(20.74), "button"),
         (T(22.36), "fan"), (T(24.42), "speed"), (T(27.56), "hit"), (T(30.72), "study"), (T(33.96), "grow"),
         (T(35.90), "towel"), (T(37.86), "x27")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
def F0(n): return S[n][0]
def F1(n): return S[n][1]
F_PURK = T(8.44); F_PRESS = T(21.7); F_HIT = T(30.18); F_FLUSH = T(14.0); F_200 = T(25.4); F_27 = T(37.9)

def bool_solver():
    for s in ("EXACT", "MANIFOLD", "FLOAT", "FAST"):
        try:
            m = bpy.data.objects.new("_t", bpy.data.meshes.new("_t")).modifiers.new("b", "BOOLEAN"); m.solver = s; return s
        except Exception: pass
    return None
SOLVER = bool_solver()

# ======================================================================
# 1) JAMOAT HOJATXONASI: kabinalar chap devorda (x=-3.2), rakovinalar va quritgich orqa devorda (y=2.4)
# ======================================================================
room = empty("room")
X0_, X1_, Y0_, Y1_, H_ = -3.2, 3.2, -2.6, 2.4, 2.8
wall_t = tile_mat("tile_white", (0.86, 0.88, 0.88), (0.80, 0.83, 0.84), grout=(0.42, 0.44, 0.45), scale=3.0)
dark_t = tile_mat("tile_dark", (0.07, 0.10, 0.11), (0.05, 0.08, 0.09), grout=(0.5, 0.52, 0.52), scale=3.0)
floor_m = pbr("floor", "interior_tiles", 0.7, tint=(0.75, 0.75, 0.78))
plane("floor", (X1_ - X0_, Y1_ - Y0_), ((X0_ + X1_) / 2, (Y0_ + Y1_) / 2, 0), floor_m, parent=room)
plane("ceiling", (X1_ - X0_, Y1_ - Y0_), ((X0_ + X1_) / 2, (Y0_ + Y1_) / 2, H_), mat("ceil", (0.85, 0.86, 0.86), 0.8), rot=(180, 0, 0), parent=room)
plane("wall_back", (X1_ - X0_, H_), ((X0_ + X1_) / 2, Y1_, H_ / 2), wall_t, rot=(90, 0, 0), parent=room)
plane("wall_front", (X1_ - X0_, H_), ((X0_ + X1_) / 2, Y0_, H_ / 2), wall_t, rot=(-90, 0, 0), parent=room)
plane("wall_left", (Y1_ - Y0_, H_), (X0_, (Y0_ + Y1_) / 2, H_ / 2), dark_t, rot=(90, 0, 90), parent=room)
plane("wall_right", (Y1_ - Y0_, H_), (X1_, (Y0_ + Y1_) / 2, H_ / 2), wall_t, rot=(90, 0, -90), parent=room)
# qora kafel belbog'i orqa devorda
box("band", (X1_ - X0_, 0.01, 0.12), ((X0_ + X1_) / 2, Y1_ - 0.005, 1.95), dark_t, parent=room)
# kabinalar (3 ta, chuqurligi 1.5 m)
hpl = mat("hpl", (0.05, 0.17, 0.20), 0.35, coat=0.3)
steel = mat("steel", (0.75, 0.76, 0.78), 0.25, metal=1.0)
SX = X0_ + 1.5
for yp in (1.4, 0.4, -0.6):
    box(f"part_{yp}", (1.5, 0.025, 1.85), (X0_ + 0.75, yp, 0.15 + 0.925), hpl, parent=room)
for i, (ya, yb) in enumerate(((1.4, 2.4), (0.4, 1.4), (-0.6, 0.4))):
    yc = (ya + yb) / 2
    box(f"front_a{i}", (0.025, 0.17, 1.85), (SX, ya + 0.085, 1.075), hpl, parent=room)
    box(f"front_b{i}", (0.025, 0.17, 1.85), (SX, yb - 0.085, 1.075), hpl, parent=room)
    hinge = empty(f"hinge{i}", (SX, ya + 0.17, 0), room)
    box(f"door{i}", (0.025, 0.66, 1.75), (0, 0.33, 1.05), hpl, parent=hinge)
    cyl(f"knob{i}", 0.012, 0.06, (0.03, 0.6, 1.0), steel, rot=(0, 90, 0), parent=hinge, verts=12)
    hinge.rotation_euler = (0, 0, R(-100 if i == 1 else 0))
    for yl in (ya + 0.04, yb - 0.04):
        cyl(f"leg{i}_{yl}", 0.012, 0.15, (SX, yl, 0.075), steel, parent=room, verts=12)
    te = empty(f"toilet{i}", (X0_ + 0.02, yc, 0), room); te.rotation_euler = (0, 0, R(90))
    import_gltf(BK + "6a342733_u.glb", te)
    cyl(f"roll{i}", 0.055, 0.1, (X0_ + 0.5, ya + 0.08, 0.72), mat(f"paper{i}", (0.95, 0.95, 0.93), 0.9), rot=(90, 0, 0), parent=room)
TOILET_C = Vector((X0_ + 0.02 + 0.42, 0.9, 0.36))              # o'rta kabina unitazi kosasi
# yuqori to'siq (kabina tepasi)
box("stall_top", (0.04, 3.0, 0.05), (SX, 0.9, 2.02), steel, parent=room)
# rakovinalar peshtaxtasi (orqa devor)
stone = mat("stone", (0.05, 0.055, 0.06), 0.15, coat=0.6)
cer = mat("ceramic", (0.95, 0.95, 0.94), 0.06, coat=1.0)
chrome = mat("chrome", (0.92, 0.92, 0.95), 0.06, metal=1.0)
box("counter", (2.2, 0.55, 0.05), (0.4, Y1_ - 0.275, 0.84), stone, parent=room, bevel=0.008)
box("counter_skirt", (2.2, 0.03, 0.18), (0.4, Y1_ - 0.535, 0.74), stone, parent=room)
BASINS = (-0.15, 0.95)
for bx in BASINS:
    prof = [(0.0, 0.0), (0.06, 0.004), (0.12, 0.025), (0.16, 0.07), (0.18, 0.12), (0.185, 0.125)]
    bw_ = sweep(f"basin{bx}", [(r_, z) for r_, z in prof], 0.0, 0.0, cer, a0=0, a1=2 * math.pi, n=48, closed=False,
                parent=room, loc=(bx, Y1_ - 0.27, 0.865))
    bw_.scale = (1.0, 0.85, 1.0)
    so = bw_.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.01; so.offset = 1
    cyl(f"drain{bx}", 0.022, 0.004, (bx, Y1_ - 0.27, 0.868), chrome, parent=room, verts=24)
    # kran: tik ustun + egilgan jo'mrak
    cyl(f"tap{bx}", 0.016, 0.28, (bx, Y1_ - 0.06, 1.0), chrome, parent=room)
    cyl(f"spout{bx}", 0.012, 0.17, (bx, Y1_ - 0.14, 1.13), chrome, rot=(90, 0, 0), parent=room)
    sphere(f"tapk{bx}", 0.018, (bx, Y1_ - 0.06, 1.14), chrome, parent=room)
    cyl(f"lever{bx}", 0.006, 0.08, (bx + 0.03, Y1_ - 0.06, 1.17), chrome, rot=(0, 60, 0), parent=room, verts=12)
mir = plane("mirror", (2.1, 0.85), (0.4, Y1_ - 0.008, 1.5), mat("mirror", (0.93, 0.94, 0.95), 0.02, metal=1.0), rot=(90, 0, 0), parent=room)
box("mirror_fr", (2.16, 0.012, 0.91), (0.4, Y1_ - 0.004, 1.5), steel, parent=room)
# sovun dispenseri
box("soap", (0.09, 0.07, 0.16), (1.55, Y1_ - 0.04, 1.18), mat("soap_m", (0.9, 0.9, 0.92), 0.3), parent=room, bevel=0.01)
# qog'oz sochiq dispenseri (o'ng devor)
TOW = Vector((X1_ - 0.06, 1.1, 1.35))
box("towel_box", (0.12, 0.3, 0.38), tuple(TOW), mat("towel_box_m", (0.92, 0.93, 0.94), 0.25, coat=0.4), parent=room, bevel=0.015)
box("towel_slot", (0.02, 0.2, 0.05), tuple(TOW + Vector((-0.06, 0, -0.17))), mat("slot", (0.02, 0.02, 0.02), 0.5), parent=room)
paper_m = mat("paper_t", (0.93, 0.92, 0.88), 0.85, sss=0.1)
box("towel_tail", (0.004, 0.18, 0.1), tuple(TOW + Vector((-0.07, 0, -0.23))), paper_m, parent=room)
# axlat qutisi, o'simlik, eshik, ventilyatsiya
cyl("bin", 0.17, 0.62, (X1_ - 0.3, 0.3, 0.31), mat("bin_m", (0.7, 0.71, 0.73), 0.25, metal=1.0), parent=room)
plantE = empty("plant", (X1_ - 0.35, -2.2, 0), room); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plantE); plantE.scale = (1.3,) * 3
box("door_main", (0.95, 0.05, 2.1), (1.6, Y0_ + 0.03, 1.05), hpl, parent=room)
box("vent", (0.5, 0.5, 0.01), (-0.5, -0.5, H_ - 0.006), mat("vent_m", (0.5, 0.5, 0.52), 0.4, metal=0.5), parent=room)
# shiftdagi LED panellar
panel_m = mat("panel_m", (1, 1, 1), 0.5, emit=6.0, emit_col=(0.95, 0.97, 1.0))
for (px, py) in ((-2.2, 0.9), (-0.4, 1.4), (1.6, 1.4), (-0.4, -1.2), (1.6, -1.2)):
    box(f"panel{px}{py}", (0.6, 0.6, 0.02), (px, py, H_ - 0.011), panel_m, parent=room)

# ======================================================================
# 2) ISSIQ HAVO QURITGICHI (orqa devorda, old tomoni -Y) + ichki qismlar (kesim uchun)
# ======================================================================
DX, DY0, DY1, DZ0, DZ1 = 2.30, 2.20, 2.40, 1.25, 1.51        # korpus: x 2.13..2.47
DW = 0.34
NOZ = Vector((2.21, 2.30, 1.18))                               # soplo uchi
IN_P = Vector((2.39, 2.30, 1.235))                             # havo kirish panjarasi (pastda, o'ngda)
HC = Vector((2.21, 2.25, 0.99))                                # qo'llar markazi soplo ostida
BTN = Vector((2.385, DY0 - 0.006, 1.33))                       # tugma
shell_m = mat("shell", (0.93, 0.94, 0.95), 0.22, coat=0.5)
cutface_m = mat("cutface", (0.95, 0.35, 0.08), 0.4, emit=0.6)
dark_m = mat("dark", (0.015, 0.015, 0.017), 0.4)
dry = empty("dryer", (0, 0, 0))
def rbox(name, size, loc, m, bev, parent):
    o = box(name, size, loc, m, parent=parent)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = bev; bv.segments = 5; bv.limit_method = "ANGLE"
    return o
body = rbox("dr_body", (DW, DY1 - DY0, DZ1 - DZ0), (DX, (DY0 + DY1) / 2, (DZ0 + DZ1) / 2), shell_m, 0.035, dry)
for p in body.data.polygons: p.use_smooth = True
# kesim korpusi: ichi bo'sh (Solidify) + old yarmi olib tashlangan (Boolean)
cut = rbox("dr_cut", (DW, DY1 - DY0, DZ1 - DZ0), (DX, (DY0 + DY1) / 2, (DZ0 + DZ1) / 2), shell_m, 0.035, dry)
cut.data.materials.append(cutface_m)
for p in cut.data.polygons: p.use_smooth = True
so = cut.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.006; so.offset = -1; so.material_offset_rim = 1; so.use_rim = True
cutter = box("dr_cutter", (0.6, 0.2, 0.6), (DX, 2.18, (DZ0 + DZ1) / 2), None)
cutter.data.materials.append(cutface_m); cutter.hide_render = True; cutter.hide_viewport = True
bo = cut.modifiers.new("cut", "BOOLEAN"); bo.object = cutter; bo.operation = "DIFFERENCE"
if SOLVER: bo.solver = SOLVER
try: bo.material_mode = "TRANSFER"
except Exception: pass
# soplo (konus) — ikkala variantda
bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.026, radius2=0.036, depth=0.08); noz = bpy.context.object
noz.name = "dr_nozzle"; noz.location = (NOZ.x, NOZ.y, NOZ.z + 0.04); noz.data.materials.append(chrome); noz.parent = dry
for p in noz.data.polygons: p.use_smooth = len(p.vertices) == 4
cyl("dr_noz_hole", 0.022, 0.004, (NOZ.x, NOZ.y, NOZ.z - 0.001), dark_m, parent=dry)
# tugma + chiroqcha
cyl("dr_btn_ring", 0.026, 0.008, tuple(BTN + Vector((0, 0.006, 0))), chrome, rot=(90, 0, 0), parent=dry)
btn = cyl("dr_btn", 0.019, 0.014, tuple(BTN), chrome, rot=(90, 0, 0), parent=dry)
led_m = mat("led", (0.2, 1.0, 0.25), 0.3, emit=0.0)
cyl("dr_led", 0.005, 0.004, (BTN.x, DY0 - 0.002, 1.40), led_m, rot=(90, 0, 0), parent=dry, verts=16)
text("dr_label", "PUSH", 0.022, (BTN.x, DY0 - 0.002, 1.37), (90, 0, 0), mat("lbl", (0.25, 0.27, 0.3), 0.5), parent=dry)
# pastki havo kirish panjarasi
for i in range(6):
    box(f"dr_slot{i}", (0.008, 0.12, 0.004), (2.34 + i * 0.022, 2.30, DZ0 + 0.001), dark_m, parent=dry)
# ichki qismlar: fan, isitgich spirali, filtr, orqa plastina
inner = empty("dr_inner", (0, 0, 0), dry)
box("dr_back", (DW - 0.02, 0.005, DZ1 - DZ0 - 0.02), (DX, DY1 - 0.01, (DZ0 + DZ1) / 2), mat("back_m", (0.25, 0.27, 0.3), 0.5, metal=0.3), parent=inner)
FANC = Vector((2.27, 2.335, 1.405))
fan = empty("dr_fan", tuple(FANC), inner)
fan_m = mat("fan_m", (0.07, 0.08, 0.09), 0.35)
cyl("fan_hub", 0.022, 0.03, (0, 0, 0), mat("hub_m", (0.6, 0.6, 0.62), 0.3, metal=1.0), rot=(90, 0, 0), parent=fan)
for k in range(9):
    a = 360 / 9 * k
    bl_ = box(f"fan_bl{k}", (0.05, 0.004, 0.022), (0, 0, 0), fan_m, parent=fan)
    bl_.location = (0.045 * math.cos(R(a)), 0, 0.045 * math.sin(R(a))); bl_.rotation_euler = (R(25), -R(a), 0)
sweep("fan_ring", [(0.0, -0.016), (0.004, -0.016), (0.004, 0.016), (0.0, 0.016)], 0.07, 0.07, fan_m, a0=0, a1=2 * math.pi, n=48,
      parent=inner, loc=tuple(FANC)).rotation_euler = (R(90), 0, 0)
# isitgich spirali (helix) soplo ustida
coil_m = mat("coil_m", (0.35, 0.33, 0.3), 0.35, metal=1.0, emit=0.0, emit_col=(1.0, 0.32, 0.05))
pts = []
for i in range(260):
    t = i / 259; a = t * 2 * math.pi * 9
    pts.append((NOZ.x + 0.019 * math.cos(a), NOZ.y + 0.019 * math.sin(a), 1.265 + 0.075 * t))
cu = bpy.data.curves.new("coil", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0022; cu.bevel_resolution = 3
sp_ = cu.splines.new("POLY"); sp_.points.add(len(pts) - 1)
for p_, c_ in zip(sp_.points, pts): p_.co = (*c_, 1)
coil = bpy.data.objects.new("dr_coil", cu); sc.collection.objects.link(coil); coil.data.materials.append(coil_m); coil.parent = inner
# filtr: gorizontal to'r plastina panjara ustida
def filter_mat():
    m = bpy.data.materials.new("filter_m"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); w1 = N.new("ShaderNodeTexWave"); w1.inputs["Scale"].default_value = 160; w1.wave_profile = "SAW"
    w2 = N.new("ShaderNodeTexWave"); w2.inputs["Scale"].default_value = 160; w2.bands_direction = "Y"
    L.new(tc.outputs["Object"], w1.inputs["Vector"]); L.new(tc.outputs["Object"], w2.inputs["Vector"])
    grid = P.math_n(N, L, "MAXIMUM", w1.outputs["Fac"], w2.outputs["Fac"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    dirt = value_node(m, "dirt", 0.0)
    dm = P.math_n(N, L, "MULTIPLY", dirt, P.math_n(N, L, "ADD", nz.outputs["Fac"], 0.35), clamp=True)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(grid, c1.inputs["Factor"])
    c1.inputs[6].default_value = (0.75, 0.76, 0.74, 1); c1.inputs[7].default_value = (0.45, 0.46, 0.45, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(dm, c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.13, 0.17, 0.04, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8
    return m
filt_m = filter_mat()
FILT = Vector((2.39, 2.30, 1.272))
box("dr_filter", (0.13, 0.17, 0.006), tuple(FILT), filt_m, parent=inner)
box("dr_filter_fr", (0.14, 0.18, 0.004), tuple(FILT + Vector((0, 0, -0.004))), mat("ffr", (0.2, 0.2, 0.22), 0.4), parent=inner)
CUT_SHOTS = rng("filter", "fan", "speed")
vis(body, [(1, F0("filter") - 1), (F0("button"), F0("fan") - 1), (F0("hit"), END)], recursive=False)
vis(cut, CUT_SHOTS, recursive=False)
vis(inner, CUT_SHOTS)
# fan aylanishi: tugmadan keyin tezlashadi
fan.rotation_mode = "XYZ"
ang = 0.0; spd = 0.0
for f in range(1, END + 1):
    tgt_ = 1.0 if f >= F_PRESS else 0.0
    spd += (tgt_ - spd) * 0.12; ang += spd * R(47)
    if f % 2 == 1 or f == END:
        fan.rotation_euler = (0, ang, 0); fan.keyframe_insert("rotation_euler", frame=f)
interp(fan, "LINEAR")
# tugma bosilishi, chiroqcha, spiral qizishi
for f, d in ((1, 0.0), (F_PRESS - 2, 0.0), (F_PRESS, 0.008), (F_PRESS + 4, 0.0)):
    btn.location = tuple(BTN + Vector((0, d, 0))); btn.keyframe_insert("location", frame=f)
led_n = led_m.node_tree.nodes["Principled BSDF"]
for f, e in ((1, 0.0), (F_PRESS, 0.0), (F_PRESS + 1, 2.5)):
    led_n.inputs["Emission Strength"].default_value = e; led_n.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
cn = coil_m.node_tree.nodes["Principled BSDF"]
for f, e in ((1, 0.0), (F_PRESS, 0.0), (F_PRESS + 20, 4.0)):
    cn.inputs["Emission Strength"].default_value = e; cn.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
for f, v in ((1, 0.08), (F0("filter") - 20, 0.1), (F1("filter"), 0.95), (END, 0.95)):
    val_key(filt_m, "dirt", f, v)
# issiq havo titrashi (shaffof konus) quritgich ishlaganda
heat_m = glow_mat("heat", (1.0, 0.75, 0.5))
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.09, radius2=0.025, depth=0.18); heat = bpy.context.object
heat_m.node_tree.nodes["a"].outputs[0].default_value = 0.35
heat.name = "heat_cone"; heat.location = (NOZ.x, NOZ.y, NOZ.z - 0.09); heat.data.materials.append(heat_m)
for p in heat.data.polygons: p.use_smooth = True

# ======================================================================
# 3) BRIAN: rakovinada, quritgichga yuradi, quritgich ostida qo'l ishqalaydi, tugmani bosadi, qog'oz sochiq
# ======================================================================
broot, bri, bmeshes = mc.load_character("bri", "Brian.fbx"); sc.render.fps = 24
soften(bmeshes)
IDLE = A_("Idle_14.fbx"); WALK = A_("Walking_21.fbx")
strip(bri, IDLE, -30, blend=0, bout=0, repeat=6.0)
strip(bri, WALK, F0("walk") - 6, blend=4, bout=4, repeat=1.4)
SINK_ROOT = (BASINS[1], 1.86, 0.0); DRY_ROOT = (HC.x, 1.93, 0.0); TOW_ROOT = (TOW.x - 0.52, TOW.y + 0.05, 0.0)
WALK_A = Vector((BASINS[1] + 0.05, 1.70, 0.0)); WALK_B = Vector((HC.x - 0.05, 1.78, 0.0))
def stage(f, loc, rot):
    place(broot, f, tuple(loc), rot)
stage(1, SINK_ROOT, 180); stage(F0("walk"), WALK_A, 90); stage(F1("walk"), WALK_B, 90)
stage(F0("dryer"), DRY_ROOT, 180); stage(F0("towel"), TOW_ROOT, 90)
for fc in fcurves(broot):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if int(k.co.x) == F0("walk") else "CONSTANT"
def bw(b): return (bri.matrix_world @ bri.pose.bones["mixamorig:" + b].head).copy()
headE = child_of_bone("bri_head", bri, "Head"); faceT = empty("faceT", (0, 0.06, 0.08), headE)
handRE = child_of_bone("bri_handR", bri, "RightHand"); handLE = child_of_bone("bri_handL", bri, "LeftHand")

# ---- qo'llar IK: nishonlar har kadr hisoblanadi ----
def arm_ik(side):
    tgt = empty(f"ik_{side}"); aimE = empty(f"aim_{side}"); palmE = empty(f"palm_{side}")
    c = bri.pose.bones[f"mixamorig:{side}ForeArm"].constraints.new("IK")
    c.target = tgt; c.use_tail = True; c.chain_count = 2; c.influence = 0.0
    hb = bri.pose.bones[f"mixamorig:{side}Hand"]
    d = hb.constraints.new("DAMPED_TRACK"); d.target = aimE; d.track_axis = "TRACK_Y"; d.influence = 0.0
    l = hb.constraints.new("LOCKED_TRACK"); l.target = palmE; l.track_axis = "TRACK_Z" if side == "Right" else "TRACK_NEGATIVE_Z"
    l.lock_axis = "LOCK_Y"; l.influence = 0.0
    return tgt, aimE, palmE, [c, d, l]
IKR = arm_ik("Right"); IKL = arm_ik("Left")
SG = float(os.environ.get("PALM_SIGN", 1.0))
def rub_pose(center, f, side, fwd=Vector((0, 1, 0)), amp=1.0, spread=0.045, tilt=-0.25):
    """ikki kaft bir-biriga qaragan, oldinga-orqaga ishqalanadi. side: +1 o'ng (Brian +Y ga qaraganda o'ng = +X)"""
    w = 2 * math.pi / 9.0
    off = Vector((0, 0.028 * math.sin(w * f), 0.012 * math.cos(w * f))) * amp * side
    right = fwd.cross(Vector((0, 0, 1))).normalized()          # fwd=+Y -> right=+X
    wrist = center - fwd * 0.07 + right * (spread * side) + off
    aimp = wrist + (fwd + Vector((0, 0, tilt))).normalized() * 0.2 - right * (0.03 * side)
    palmp = wrist - right * (0.3 * side * SG) + fwd * 0.05
    return wrist, aimp, palmp
PLAN = []      # (f0, f1, funksiya(f) -> {"R": (w,a,p) | None, "L": ...})
def ik_bake(f0, f1, fn, ramp=8, ramp_out=8):
    for side, (tgt, aimE, palmE, cons) in (("R", IKR), ("L", IKL)):
        on_any = False
        for f in range(f0 - ramp, f1 + 1):
            r_ = fn(max(f, f0))[side]
            if r_ is None: continue
            on_any = True
            w_, a_, p_ = r_
            key(tgt, f, loc=tuple(w_)); key(aimE, f, loc=tuple(a_)); key(palmE, f, loc=tuple(p_))
        if not on_any: continue
        for c in cons:
            for f, v in ((f0 - ramp - 1, 0.0), (f0, 1.0), (f1, 1.0), (f1 + ramp_out, 0.0)):
                c.influence = v; c.keyframe_insert("influence", frame=f)
SINK_C = Vector((BASINS[1], Y1_ - 0.30, 1.0))
def sink_fn(f): return {"R": rub_pose(SINK_C, f, 1), "L": rub_pose(SINK_C, f + 4, -1)}
def dry_fn(f): return {"R": rub_pose(HC, f, 1, amp=1.3), "L": rub_pose(HC, f + 4, -1, amp=1.3)}
def btn_fn(f):
    t = min(1.0, max(0.0, (f - (F_PRESS - 14)) / 14.0)); push = 0.008 if F_PRESS - 2 <= f <= F_PRESS + 3 else 0.0
    tip = BTN + Vector((0, -0.01 + push, -0.012))
    wrist = tip + Vector((-0.03, -0.17, -0.05)); wrist = Vector(lerp3(wrist + Vector((0.05, -0.15, -0.25)), wrist, t))
    return {"R": (wrist, wrist + Vector((0.03, 0.2, 0.06)), wrist + Vector((0, 0.05, -0.3 * SG))), "L": None}
TOW_C = Vector((TOW_ROOT[0] + 0.33, TOW_ROOT[1], 1.05))
def tow_fn(f): return {"R": rub_pose(TOW_C, f, 1, fwd=Vector((1, 0, 0)), amp=1.1, spread=0.04),
                       "L": rub_pose(TOW_C, f + 4, -1, fwd=Vector((1, 0, 0)), amp=1.1, spread=0.04)}
ik_bake(1, F1("wash") + 2, sink_fn, ramp=0)
ik_bake(F0("dryer") + 8, F1("drift"), dry_fn, ramp=10)
ik_bake(F0("button") - 6, F1("button"), btn_fn, ramp=0, ramp_out=1)
ik_bake(F0("speed"), F1("hit"), dry_fn, ramp=2)
ik_bake(F0("towel"), END, tow_fn, ramp=0)
for o in (IKR[0], IKR[1], IKR[2], IKL[0], IKL[1], IKL[2]):
    interp(o, "LINEAR")
for fc in fcurves(bri):
    if "constraints" in fc.data_path:
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
# tugma uchun ko'rsatkich barmoq: qolgan barmoqlar bukiladi
curlE = empty("curlE", (0.0, 0, 0))
for fn in ("Middle", "Ring", "Pinky", "Thumb"):
    for i in (1, 2, 3):
        pbn = bri.pose.bones.get(f"mixamorig:RightHand{fn}{i}")
        if not pbn: continue
        c_ = pbn.constraints.new("TRANSFORM"); c_.target = curlE; c_.map_from = "LOCATION"; c_.from_min_x = 0; c_.from_max_x = 1
        c_.map_to = "ROTATION"; c_.owner_space = "LOCAL"; c_.target_space = "WORLD"; c_.mix_mode_rot = "AFTER"
        c_.map_to_x_from = "X"; c_.to_min_x_rot = 0; c_.to_max_x_rot = R(35 if fn == "Thumb" else 75)
for f, v in ((1, 0.0), (F0("button") - 1, 0.0), (F0("button"), 1.0), (F1("button") + 1, 0.0)):
    curlE.location = (v, 0, 0); curlE.keyframe_insert("location", frame=f)
interp(curlE, "CONSTANT")
# qog'oz sochiq qo'llar orasida
towel = empty("towel_p", (0, 0, 0))
cpL = towel.constraints.new("COPY_LOCATION"); cpL.target = bri; cpL.subtarget = "mixamorig:LeftHand"
cpR = towel.constraints.new("COPY_LOCATION"); cpR.target = bri; cpR.subtarget = "mixamorig:RightHand"; cpR.influence = 0.5
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0); tw = bpy.context.object; tw.name = "towel_crumple"
for v in tw.data.vertices:
    n_ = v.co.normalized(); v.co = n_ * (1 + 0.25 * math.sin(7 * n_.x + 3) * math.cos(5 * n_.y) + 0.15 * math.sin(11 * n_.z))
tw.scale = (0.07, 0.05, 0.06); tw.data.materials.append(paper_m); tw.parent = towel; tw.location = (0.09, 0.0, 0.0)
for p in tw.data.polygons: p.use_smooth = False
vis(towel, rng("towel", "x27"))
# ho'l qo'llar: suv tomchilari (kaft atrofida)
water_m = mat("water", (0.8, 0.9, 1.0), 0.02, trans=1.0, ior=1.33)
rd = random.Random(5)
for hE, nm in ((handRE, "R"), (handLE, "L")):
    dg = empty(f"drops_{nm}", (0, 0, 0), hE)
    for i in range(26):
        u = rd.uniform(-1, 1); a = rd.uniform(0, 2 * math.pi)
        p_ = Vector((0.04 * math.cos(a), 0.02 + 0.13 * rd.random(), 0.022 * math.sin(a)))
        sphere(f"drop_{nm}{i}", rd.uniform(0.0016, 0.0035), tuple(p_), water_m, scale=(1, 1, 0.6), sub=2, parent=dg)
    vis(dg, [(1, F1("dryer")), (F0("hit"), F1("hit"))])

# ======================================================================
# 4) ZARRALAR (bakteriyalar, najas zarralari, havo oqimi): har kadr numpy bilan hisoblanadi
# ======================================================================
bact_m = mat("bact", (0.35, 0.95, 0.12), 0.35, emit=1.6, emit_col=(0.35, 1.0, 0.1), sss=0.3)
bact2_m = mat("bact2", (0.85, 0.95, 0.2), 0.35, emit=1.2, emit_col=(0.8, 1.0, 0.15))
poo_m = mat("poo", (0.20, 0.10, 0.03), 0.6, emit=0.35, emit_col=(0.45, 0.25, 0.05))
air_m = mat("air", (0.6, 0.8, 1.0), 0.3, emit=1.4, emit_col=(0.55, 0.78, 1.0))
TEMPL = empty("templates", (0, 0, -50))
def capsule(name, m, elong=2.4):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1.0); o = bpy.context.object; o.name = name
    for v in o.data.vertices: v.co.z *= elong
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(m); o.parent = TEMPL; return o
cap_b = capsule("cap_bact", bact_m); cap_b2 = capsule("cap_bact2", bact2_m, 1.0)
cap_p = capsule("cap_poo", poo_m, 1.3); cap_a = capsule("cap_air", air_m, 14.0)
def inst_group(inst, aligned):
    ng = bpy.data.node_groups.new("I_" + inst.name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = inst
    iop = N.new("GeometryNodeInstanceOnPoints")
    L.new(gi.outputs[0], iop.inputs["Points"]); L.new(oi.outputs["Geometry"], iop.inputs["Instance"])
    na = N.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"; na.inputs["Name"].default_value = "s"
    L.new(na.outputs["Attribute"], iop.inputs["Scale"])
    if aligned:
        nv = N.new("GeometryNodeInputNamedAttribute"); nv.data_type = "FLOAT_VECTOR"; nv.inputs["Name"].default_value = "v"
        al = N.new("FunctionNodeAlignRotationToVector"); al.axis = "Z"
        L.new(nv.outputs["Attribute"], al.inputs["Vector"]); L.new(al.outputs[0], iop.inputs["Rotation"])
    else:
        rv = N.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT_VECTOR"
        for s_ in rv.inputs:
            if s_.name == "Max" and s_.type == "VECTOR": s_.default_value = (6.3, 6.3, 6.3)
        L.new(next(o for o in rv.outputs if o.type == "VECTOR"), iop.inputs["Rotation"])
    L.new(iop.outputs[0], go.inputs[0])
    return ng
SWARMS = []
class Swarm:
    def __init__(self, name, n, inst, fn, ranges, aligned=False, parent=None):
        me = bpy.data.meshes.new(name); me.vertices.add(n); me.attributes.new("s", "FLOAT", "POINT")
        if aligned: me.attributes.new("v", "FLOAT_VECTOR", "POINT")
        self.o = bpy.data.objects.new(name, me); sc.collection.objects.link(self.o)
        if parent: self.o.parent = parent
        md = self.o.modifiers.new("inst", "NODES"); md.node_group = inst_group(inst, aligned)
        self.n, self.fn, self.ranges, self.aligned = n, fn, ranges, aligned
        vis(self.o, ranges, recursive=False); SWARMS.append(self); self.update(1)
    def update(self, f):
        me = self.o.data
        live = any(a - 1 <= f <= b + 1 for a, b in self.ranges)
        if live:
            r_ = self.fn(f); co, s = r_[0], r_[1]
        else:
            co = np.zeros((self.n, 3)); s = np.zeros(self.n); r_ = (co, s, np.tile([0, 0, 1.0], (self.n, 1)))
        me.vertices.foreach_set("co", np.asarray(co, dtype=np.float32).ravel())
        me.attributes["s"].data.foreach_set("value", np.asarray(s, dtype=np.float32))
        if self.aligned: me.attributes["v"].data.foreach_set("vector", np.asarray(r_[2], dtype=np.float32).ravel())
        me.update()
def sstep(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def V(v): return np.array(tuple(v), dtype=np.float64)

# quritgich ishlayotgan oraliqlar (soplodan purkash)
DRY_ON = [(1, F1("hook")), (F0("dryer") + 10, F1("intake")), (F_PRESS + 4, F1("hit"))]
def dry_on(f):
    return max((sstep((f - a) / 6.0) * (1 - sstep((f - b) / 3.0)) for a, b in DRY_ON), default=0.0)
def spray_fn_factory(n, seed, size, miss=0.22, life=14.0, tr=7.0):
    g = np.random.default_rng(seed)
    ph = g.uniform(0, life, n); rr = np.sqrt(g.uniform(0, 1, n)) * 0.075; aa = g.uniform(0, 2 * np.pi, n)
    tgt = np.stack([HC.x + rr * np.cos(aa), HC.y + 0.01 + rr * np.sin(aa) * 0.8, np.full(n, HC.z + 0.02)], 1)
    ms = g.uniform(0, 1, n) < miss
    tgt[ms, 2] = 0.55; tgt[ms, 0] += (tgt[ms, 0] - HC.x) * 2.5; tgt[ms, 1] += (tgt[ms, 1] - HC.y) * 2.5
    sz = size * g.uniform(0.6, 1.4, n); start = np.tile(V(NOZ), (n, 1)) + g.normal(0, 0.006, (n, 3))
    def fn(f):
        on = dry_on(f)
        sp = 1.6 if F0("speed") <= f <= F1("hit") else 1.0
        age = np.mod(f - ph, life); t = age / (tr / sp)
        tt = np.where(ms, age / (life * 0.9), t)
        co = start + (tgt - start) * np.clip(tt, 0, 1.05)[:, None]
        co[:, 0] += 0.004 * np.sin(age * 1.7 + ph); co[:, 1] += 0.004 * np.cos(age * 1.3 + ph)
        s = sz * on * sstep(age / 1.2) * np.where(tt < 1.0, 1.0, 0.0)
        return co, s
    return fn
sprayG = Swarm("sw_spray", 1400, cap_b, spray_fn_factory(1400, 1, 0.0026), DRY_ON)
sprayY = Swarm("sw_spray2", 600, cap_b2, spray_fn_factory(600, 2, 0.0022), DRY_ON)
# qo'lga yopishgan bakteriyalar (kaft atrofida, Hand suyagi fazosida)
def stuck_factory(n, seed, t0, t1, size):
    g = np.random.default_rng(seed)
    a = g.uniform(0, 2 * np.pi, n); yy = g.uniform(0.0, 0.17, n)
    co = np.stack([0.043 * np.cos(a), yy, 0.021 * np.sin(a)], 1)
    ta = t0 + (t1 - t0) * g.uniform(0, 1, n) ** 0.7; sz = size * g.uniform(0.6, 1.3, n)
    def fn(f): return co, sz * sstep((f - ta) / 3.0)
    return fn
STUCK_R = [(F0("dryer"), F1("drift")), (F0("speed"), F1("hit"))]
for hE, nm, sd in ((handRE, "R", 3), (handLE, "L", 4)):
    Swarm(f"sw_stuck_{nm}", 260, cap_b, stuck_factory(260, sd, F0("dryer") + 14, F1("hit") - 6, 0.0019), STUCK_R, parent=hE)
# xona havosi quritgich panjarasiga so'riladi
def intake_factory(n, seed, size, life=(45, 80)):
    g = np.random.default_rng(seed)
    p0 = np.stack([g.uniform(-2.6, 3.0, n), g.uniform(-2.2, 2.2, n), g.uniform(0.2, 2.6, n)], 1)
    L_ = g.uniform(*life, n); ph = g.uniform(0, 1, n) * L_
    sz = size * g.uniform(0.7, 1.3, n); IN = V(IN_P)
    ctrl = (p0 + IN) / 2 + np.stack([np.zeros(n), np.zeros(n), g.uniform(-0.6, 0.3, n)], 1)
    jit = g.normal(0, 0.012, (n, 3))
    def fn(f):
        t = np.mod(f - ph, L_) / L_; u = t ** 1.7
        a_, b_, c_ = (1 - u) ** 2, 2 * (1 - u) * u, u * u
        co = a_[:, None] * p0 + b_[:, None] * ctrl + c_[:, None] * (IN + jit)
        du = 1.7 * np.maximum(t, 1e-3) ** 0.7
        v = (2 * (1 - u))[:, None] * (ctrl - p0) + (2 * u)[:, None] * (IN - ctrl); v = v * du[:, None]
        s = sz * np.sin(np.pi * t) ** 0.5 * (0.4 + 0.6 * t)
        return co, s, v
    return fn
INTAKE_R = rng("intake")
Swarm("sw_air", 1400, cap_a, intake_factory(1400, 5, 0.006), INTAKE_R, aligned=True)
Swarm("sw_air_b", 900, cap_b, intake_factory(900, 6, 0.008), INTAKE_R, aligned=True)
# unitazdan ko'tarilgan "fontan", keyin quritgich tomon suzadi
def plume_factory(n, seed, size):
    g = np.random.default_rng(seed)
    l0 = F_FLUSH + 34 * g.uniform(0, 1, n) ** 1.6
    vz = g.uniform(0.025, 0.085, n); vh = g.normal(0, 0.012, (n, 2)); tau = g.uniform(14, 26, n)
    st = np.tile(V(TOILET_C), (n, 1)) + np.stack([g.normal(0, 0.07, n), g.normal(0, 0.07, n), np.zeros(n)], 1)
    sz = size * g.uniform(0.5, 1.5, n); ph = g.uniform(0, 6.3, n)
    IN = V(IN_P); dest = IN + g.normal(0, 0.03, (n, 3)); dd = g.uniform(0, 30, n)
    def fn(f):
        t = np.maximum(f - l0, 0); e = tau * (1 - np.exp(-t / tau))
        co = st.copy(); co[:, 2] += vz * e; co[:, 0] += vh[:, 0] * e + 0.03 * np.sin(0.09 * t + ph); co[:, 1] += vh[:, 1] * e + 0.03 * np.cos(0.07 * t + ph)
        w = sstep((f - F0("drift") + 10 - dd) / 55.0)[:, None]
        co = co * (1 - w) + dest * w
        s = sz * sstep(t / 3.0) * (1 - sstep((f - F0("drift") - 15 - dd) / 40.0))
        return co, s
    return fn
PLUME_R = rng("flush", "plume", "drift")
Swarm("sw_poo", 2200, cap_p, plume_factory(2200, 7, 0.006), PLUME_R)
Swarm("sw_plume_b", 800, cap_b, plume_factory(800, 8, 0.006), PLUME_R)
# kesim: zarralar filtrga yopishadi, keyin fan bilan uzilib soploga
FIL_PTS = None
def filter_factory(n, seed, size):
    g = np.random.default_rng(seed)
    fp = np.stack([FILT.x + g.uniform(-0.06, 0.06, n), FILT.y + g.uniform(-0.08, 0.08, n), np.full(n, FILT.z + 0.004)], 1)
    src = fp + np.stack([g.normal(0, 0.02, n), g.normal(0, 0.02, n), np.full(n, -0.12)], 1)
    ta = F0("filter") - 15 + (F1("filter") - F0("filter") + 10) * g.uniform(0, 1, n); tr_ = 10.0
    rel = F_PRESS + 18 + (F1("fan") - F_PRESS - 25) * g.uniform(0, 1, n); tl = g.uniform(14, 22, n)
    path = [V((2.32, 2.32, 1.33)), V(FANC) + V((0.0, -0.02, -0.05)), V((NOZ.x, NOZ.y, 1.36)), V((NOZ.x, NOZ.y, 1.26)), V((NOZ.x, NOZ.y, 1.15))]
    jit = g.normal(0, 0.008, (n, 3)); sz = size * g.uniform(0.6, 1.4, n)
    def fn(f):
        u = np.clip((f - ta) / tr_, 0, 1); co = src + (fp - src) * sstep(u)[:, None]
        q = np.clip((f - rel) / tl, 0, 1); seg = np.minimum((q * 5).astype(int), 4); fr = q * 5 - seg
        pts_ = [fp] + [np.tile(p, (n, 1)) + jit for p in path]
        PA = np.stack(pts_, 0); P0 = PA[seg, np.arange(n)]; P1 = PA[np.minimum(seg + 1, 5), np.arange(n)]
        mv = P0 + (P1 - P0) * fr[:, None]
        co = np.where((q > 0)[:, None], mv, co)
        s = sz * sstep((f - ta) / 2.0) * (1 - sstep((q - 0.95) / 0.05))
        return co, s
    return fn
FILT_R = rng("filter", "fan")
Swarm("sw_filt_b", 420, cap_b, filter_factory(420, 9, 0.0024), FILT_R)
Swarm("sw_filt_p", 420, cap_p, filter_factory(420, 10, 0.0022), FILT_R)
# tezlik: soplo ichida oqim chiziqlari (speed kadri)
def streak_factory(n, seed):
    g = np.random.default_rng(seed); ph = g.uniform(0, 8, n); rr = np.sqrt(g.uniform(0, 1, n)) * 0.02; aa = g.uniform(0, 6.3, n)
    sp_ = np.sqrt(g.uniform(0, 1, n)) * 0.09
    def fn(f):
        age = np.mod(f - ph, 8.0) / 8.0
        co = np.stack([NOZ.x + rr * np.cos(aa) + sp_ * np.cos(aa) * age, NOZ.y + rr * np.sin(aa) + sp_ * np.sin(aa) * age,
                       1.34 - 0.36 * age], 1)
        v = np.tile([0, 0, -1.0], (n, 1)); s = 0.0009 * np.sin(np.pi * age) ** 0.5
        return co, s, v
    return fn
Swarm("sw_streak", 260, cap_a, streak_factory(260, 11), rng("speed"), aligned=True)

# ======================================================================
# 5) LABORATORIYA (LAB): Petri idishlari, koloniyalar o'sadi
# ======================================================================
LAB = Vector((40.0, 0.0, 0.0))
lab = empty("lab", (0, 0, 0))            # bolalar dunyo koordinatasida (ota (0,0,0) da)
BZ = 0.9
box("bench", (2.4, 1.0, 0.05), tuple(LAB + Vector((0, 0.1, BZ - 0.025))), mat("bench_m", (0.32, 0.36, 0.40), 0.35, coat=0.3), parent=lab, bevel=0.01)
plane("lab_floor", (8, 8), tuple(LAB), mat("lab_fl", (0.3, 0.32, 0.35), 0.5), parent=lab)
plane("lab_wall", (8, 4), tuple(LAB + Vector((0, 1.2, 2.0))), mat("lab_wall_m", (0.05, 0.09, 0.14), 0.6), rot=(90, 0, 0), parent=lab)
glass_m = mat("glass", (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=1.45)
agar_m = mat("agar", (0.55, 0.36, 0.1), 0.15, sss=0.4, sss_scale=0.002, coat=0.6)
DISH_R = 0.045
DA = LAB + Vector((-0.07, 0, BZ)); DB = LAB + Vector((0.07, 0, BZ))
for nm, c in (("A", DA), ("B", DB)):
    sweep(f"dish_{nm}", [(0.0, 0.0), (0.0, 0.013)], DISH_R, DISH_R, glass_m, a0=0, a1=2 * math.pi, n=64, closed=False, parent=lab,
          loc=tuple(c)).modifiers.new("sol", "SOLIDIFY").thickness = 0.0012
    cyl(f"dish_bot_{nm}", DISH_R, 0.0012, tuple(c + Vector((0, 0, 0.0006))), glass_m, parent=lab, verts=64)
    cyl(f"agar_{nm}", DISH_R - 0.0012, 0.006, tuple(c + Vector((0, 0, 0.0042))), agar_m, parent=lab, verts=64)
lbl_m = mat("lbl_m", (1.0, 1.0, 1.0), 0.5, emit=1.5)
text("lbl_A", "QURITGICH", 0.016, tuple(DA + Vector((0, -0.062, 0.0005))), (0, 0, 0), lbl_m, parent=lab)
text("lbl_B", "QOG'OZ SOCHIQ", 0.012, tuple(DB + Vector((0, -0.062, 0.0005))), (0, 0, 0), lbl_m, parent=lab)
for i, xo in enumerate((-0.45, -0.38, 0.4, 0.47)):
    cyl(f"tube{i}", 0.008, 0.15, tuple(LAB + Vector((xo, 0.3, BZ + 0.075))), glass_m, parent=lab, verts=24)
box("rack", (0.3, 0.06, 0.04), tuple(LAB + Vector((-0.41, 0.3, BZ + 0.05))), mat("rack_m", (0.1, 0.35, 0.8), 0.4), parent=lab)
box("rack2", (0.3, 0.06, 0.04), tuple(LAB + Vector((0.43, 0.3, BZ + 0.05))), mat("rack_m2", (0.1, 0.35, 0.8), 0.4), parent=lab)
col_m = mat("colony", (0.95, 0.9, 0.7), 0.25, coat=0.8, sss=0.3, sss_scale=0.002)
colg_m = mat("colony_g", (0.6, 0.85, 0.25), 0.25, coat=0.8, emit=0.25, emit_col=(0.5, 0.9, 0.1))
def dome(name, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0); o = bpy.context.object; o.name = name
    for v in o.data.vertices: v.co.z = max(0.0, v.co.z) * 0.45
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(m); o.parent = TEMPL; return o
dom_w = dome("dome_w", col_m); dom_g = dome("dome_g", colg_m)
def colony_factory(n, seed, c, t0, t1, size, frac=1.0):
    g = np.random.default_rng(seed)
    r_ = np.sqrt(g.uniform(0, 1, n)) * (DISH_R - 0.004); a = g.uniform(0, 6.3, n)
    co = np.stack([c.x + r_ * np.cos(a), c.y + r_ * np.sin(a), np.full(n, c.z + 0.0072)], 1)
    ta = t0 + (t1 - t0) * g.uniform(0, 1, n) ** 0.8; sz = size * g.uniform(0.4, 1.4, n)
    keep = np.arange(n) < int(n * frac)
    up = np.tile([0, 0, 1.0], (n, 1))
    def fn(f): return co, sz * sstep((f - ta) / 10.0) * keep, up
    return fn
LAB_R = rng("study", "grow", "x27")
G0 = F0("grow")
Swarm("col_A1", 900, dom_w, colony_factory(900, 21, DA, G0, F_27 + 30, 0.0016), LAB_R, aligned=True)
Swarm("col_A2", 500, dom_g, colony_factory(500, 22, DA, G0 + 10, F_27 + 40, 0.0013), LAB_R, aligned=True)
Swarm("col_B1", 40, dom_w, colony_factory(40, 23, DB, G0, F_27 + 30, 0.0015), LAB_R, aligned=True)
vis(lab, LAB_R)
# yozuvlar
txt_m = mat("txt", (1.0, 0.82, 0.05), 0.3, emit=2.0, emit_col=(1.0, 0.8, 0.05))
txt_k = mat("txt_k", (0.01, 0.01, 0.01), 0.5)
t200 = text("t200", "200 km/soat", 0.035, (0, 0, 0), (90, 0, 0), txt_m, extrude=0.004)
t27 = text("t27", "27x", 0.04, tuple(DA + Vector((0.0, 0.03, 0.035))), (65, 0, 0), txt_m, extrude=0.006)
vis(t27, [(F_27 + 2, END)])
for f, s in ((F_27 + 2, 0.01), (F_27 + 6, 1.25), (F_27 + 10, 1.0)):
    t27.scale = (s,) * 3; t27.keyframe_insert("scale", frame=f)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def cam_path(name, keys, tgt, lens, fstop=None, focus=None, lin=False, tgt_keys=None):
    c = shot_cam(name, keys[0][1], None, lens if not isinstance(lens, list) else lens[0][1], clip=0.004, fstop=fstop)
    path(c, keys, lin=lin)
    if isinstance(lens, list): lens_keys(c, lens)
    t_ = tgt if not isinstance(tgt, (tuple, Vector)) else empty(name + "_t", tuple(tgt))
    if tgt_keys: path(t_, tgt_keys)
    aim(c, t_, focus); return c
hipsE = child_of_bone("bri_hips", bri, "Hips")
handsT = empty("handsT", (0, 0, 0))
c1 = handsT.constraints.new("COPY_LOCATION"); c1.target = bri; c1.subtarget = "mixamorig:RightHand"
c2 = handsT.constraints.new("COPY_LOCATION"); c2.target = bri; c2.subtarget = "mixamorig:LeftHand"; c2.influence = 0.5
f0, f1 = S["hook"]
c = cam_path("hook", [(f0, (NOZ.x - 0.03, NOZ.y - 0.1, 0.9)), (f0 + 13, (NOZ.x - 0.03, NOZ.y - 0.11, 0.95)),
                      (f1, (2.75, -1.6, 0.32))], (NOZ.x, NOZ.y, 1.2), [(f0, 16), (f0 + 13, 16), (f1, 14)],
             tgt_keys=[(f0, (NOZ.x, NOZ.y, 1.2)), (f0 + 13, (NOZ.x, NOZ.y, 1.2)), (f1, (0.2, 1.3, 1.25))])
shake(c, f0, f0 + 13, 0.006, seed=1, decay=False)
f0, f1 = S["wash"]
cam_path("wash", [(f0, (SINK_C.x + 0.42, SINK_C.y - 0.2, 1.17)), (f1, (SINK_C.x + 0.36, SINK_C.y + 0.02, 1.24))], handsT, 32, fstop=2.2)
f0, f1 = S["walk"]
cam_path("walk", [(f0, (1.0, 0.25, 0.28)), (f1, (2.0, 0.45, 0.32))], hipsE, 18,
         tgt_keys=None)
f0, f1 = S["dryer"]
cam_path("dryer", [(f0, (2.85, 1.6, 0.62)), (f1, (2.6, 1.92, 0.88))], (HC.x, 2.25, 1.13), [(f0, 18), (f1, 22)], fstop=4.0)
f0, f1 = S["spray"]
orbit_cam("spray", f0, f1, (HC.x, HC.y, 1.0), 0.36, 0.3, -32, 12, 0.0, 0.05, 30, empty("spray_t", (HC.x, HC.y - 0.01, 1.05)), fstop=3.2)
shake(CAMS["spray"], F_PURK - 2, F_PURK + 10, 0.008, seed=3)
f0, f1 = S["intake"]
cam_path("intake", [(f0, (0.2, -1.9, 2.5)), (f1, (0.9, -1.2, 2.3))], (1.2, 1.2, 1.1), [(f0, 14), (f1, 16)],
         tgt_keys=[(f0, (1.6, 1.6, 1.0)), (f1, (2.1, 2.0, 1.15))])
f0, f1 = S["flush"]
c = cam_path("flush", [(f0, (TOILET_C.x + 0.75, TOILET_C.y - 0.36, 0.22)), (f1, (TOILET_C.x + 0.6, TOILET_C.y - 0.33, 0.3))],
             (TOILET_C.x - 0.05, TOILET_C.y, 0.45), 16)
shake(c, F_FLUSH, F_FLUSH + 12, 0.01, seed=4)
f0, f1 = S["plume"]
cam_path("plume", [(f0, (TOILET_C.x + 0.85, TOILET_C.y - 0.38, 0.55)), (f1, (TOILET_C.x + 1.0, TOILET_C.y - 0.4, 1.45))], (TOILET_C.x, TOILET_C.y, 0.9),
         [(f0, 16), (f1, 15)], tgt_keys=[(f0, (TOILET_C.x, TOILET_C.y, 0.75)), (f1, (TOILET_C.x + 0.1, TOILET_C.y, 1.5))])
f0, f1 = S["drift"]
cam_path("drift", [(f0, (0.3, -2.3, 2.5)), (f1, (0.6, -2.1, 2.4))], (0.0, 1.2, 1.3), 14, tgt_keys=[(f0, (-0.4, 1.0, 1.3)), (f1, (0.6, 1.4, 1.3))])
f0, f1 = S["filter"]
cam_path("filter", [(f0, (2.72, 1.78, 1.62)), (f1, (2.52, 2.05, 1.42))], (FILT.x, FILT.y - 0.02, 1.3), [(f0, 24), (f1, 30)], fstop=5.6)
f0, f1 = S["button"]
c = cam_path("button", [(f0, (BTN.x + 0.2, BTN.y - 0.3, BTN.z + 0.05)), (f1, (BTN.x + 0.12, BTN.y - 0.2, BTN.z + 0.03))], tuple(BTN), 45, fstop=2.8)
shake(c, F_PRESS, F_PRESS + 10, 0.006, seed=5)
f0, f1 = S["fan"]
orbit_cam("fan", f0, f1, (2.3, 2.30, 1.36), 0.42, 0.33, -60, -110, 0.08, 0.02, 26, empty("fan_t", (2.3, 2.31, 1.33)), fstop=6.0)
f0, f1 = S["speed"]
c = cam_path("speed", [(f0, (NOZ.x + 0.06, 2.12, 1.40)), (f0 + 40, (NOZ.x + 0.07, 2.10, 1.17)), (f1, (NOZ.x + 0.2, 1.95, 1.0))],
             (NOZ.x, NOZ.y, 1.25), [(f0, 16), (f1, 18)], tgt_keys=[(f0, (NOZ.x, NOZ.y, 1.25)), (f0 + 40, (NOZ.x, NOZ.y, 1.1)), (f1, (HC.x, HC.y, 0.99))])
shake(c, f0, f1, 0.003, seed=6, decay=False)
t200.parent = c; t200.location = (0.0, 0.07, -0.35); t200.rotation_euler = (0, 0, 0)
vis(t200, [(F_200 - 4, F1("speed"))])
for f, s in ((F_200 - 4, 0.01), (F_200, 1.2), (F_200 + 4, 1.0)):
    t200.scale = (s,) * 3; t200.keyframe_insert("scale", frame=f)
f0, f1 = S["hit"]
c = orbit_cam("hit", f0, f1, (HC.x, HC.y, 0.98), 0.4, 0.32, 15, -25, 0.02, 0.06, 30, handsT, fstop=5.6)
shake(c, F_HIT - 1, F_HIT + 12, 0.012, seed=7)
f0, f1 = S["study"]
cam_path("study", [(f0, tuple(LAB + Vector((0.14, -0.55, BZ + 0.36)))), (f1, tuple(LAB + Vector((0.03, -0.36, BZ + 0.2))))],
         tuple(LAB + Vector((0, -0.01, BZ))), [(f0, 24), (f1, 26)], fstop=5.6)
f0, f1 = S["grow"]
cam_path("grow", [(f0, tuple(DA + Vector((0.02, -0.06, 0.2)))), (f1, tuple(DA + Vector((-0.01, -0.05, 0.15))))], tuple(DA), 40, fstop=8.0)
f0, f1 = S["towel"]
orbit_cam("towel", f0, f1, (TOW_C.x - 0.2, TOW_C.y, 1.3), 0.85, 0.72, -105, -72, 0.0, -0.05, 28, handsT, fstop=2.4)
f0, f1 = S["x27"]
c = cam_path("x27", [(f0, tuple(LAB + Vector((0, -0.6, BZ + 0.35)))), (f0 + 5, tuple(LAB + Vector((-0.03, -0.3, BZ + 0.2)))),
                     (f1, tuple(LAB + Vector((-0.05, -0.24, BZ + 0.17))))], tuple(LAB + Vector((-0.04, 0, BZ + 0.02))),
             [(f0, 30), (f0 + 5, 36), (f1, 40)], fstop=4.0)
shake(c, F_27 + 4, F_27 + 18, 0.006, seed=8)
for n, (f, _) in S.items():
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]
# Brian faqat hojatxona kadrlarida
BR_SHOTS = rng("hook", "wash", "walk", "dryer", "spray", "intake", "drift", "button", "speed", "hit", "towel")
for o in bmeshes: vis(o, BR_SHOTS, recursive=False)
vis(heat, [(a, b) for a, b in DRY_ON])

# ======================================================================
# 7) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.025, 0.03, 1)
ROOM_SHOTS = [(1, F0("study") - 1), (F0("towel"), F1("towel"))]
midT = empty("mid_tgt", (0.0, 0.5, 0.8))
for (px, py) in ((-2.2, 0.9), (-0.4, 1.4), (1.6, 1.4), (-0.4, -1.2), (1.6, -1.2)):
    area(f"ceil_{px}{py}", (px, py, H_ - 0.03), 0.6, (0.95, 0.97, 1.0), lights_for(ROOM_SHOTS, 120.0))
area("sink_l", (0.4, 1.6, 2.2), 1.2, (1.0, 0.95, 0.88), lights_for(ROOM_SHOTS, 90.0), target=empty("sink_t", (0.4, 2.1, 0.9)))
area("dry_key", (HC.x + 0.6, 1.5, 1.6), 0.5, (1.0, 0.95, 0.9), lights_for(rng("spray", "button", "hit", "dryer"), 30.0), target=empty("dry_t", (HC.x, HC.y, 1.1)))
area("dry_rim", (HC.x - 0.5, 2.0, 1.5), 0.4, (0.7, 0.85, 1.0), lights_for(rng("spray", "hit"), 18.0), target=empty("dry_t2", (HC.x, HC.y, 1.0)))
area("cut_key", (2.6, 1.8, 1.7), 0.4, (1.0, 0.95, 0.9), lights_for(CUT_SHOTS, 22.0), target=empty("cut_t", (2.3, 2.3, 1.35)))
area("cut_fill", (2.0, 1.9, 1.2), 0.3, (0.6, 0.8, 1.0), lights_for(CUT_SHOTS, 8.0), target=empty("cut_t2", (2.3, 2.3, 1.35)))
area("stall_l", (TOILET_C.x + 0.6, TOILET_C.y, 2.4), 0.6, (0.95, 0.97, 1.0), lights_for(rng("flush", "plume"), 60.0), target=empty("st_t", tuple(TOILET_C)))
glow_t = point("coil_glow", (NOZ.x, NOZ.y - 0.03, 1.29), 0.02, (1.0, 0.4, 0.1), [(1, 0)], const=False)
for f, e in ((F_PRESS, 0), (F_PRESS + 20, 1.2)): glow_t.data.energy = e; glow_t.data.keyframe_insert("energy", frame=f)
glow_t.visible_camera = False
area("lab_key", tuple(LAB + Vector((-0.6, -0.7, BZ + 1.0))), 1.0, (1.0, 0.95, 0.9), lights_for(LAB_R, 70.0), target=empty("lab_t", tuple(LAB + Vector((0, 0, BZ)))))
area("lab_rim", tuple(LAB + Vector((0.7, 0.6, BZ + 0.6))), 0.8, (0.5, 0.75, 1.0), lights_for(LAB_R, 60.0), target=empty("lab_t2", tuple(LAB + Vector((0, 0, BZ)))))
area("lab_under", tuple(LAB + Vector((0.0, -0.4, BZ + 0.25))), 0.3, (1.0, 0.9, 0.7), lights_for(LAB_R, 10.0), target=empty("lab_t3", tuple(LAB + Vector((0, 0, BZ)))))
fl = point("hit_flash", (HC.x, HC.y - 0.2, 1.05), 0.05, (0.5, 1.0, 0.3), [(1, 0)], const=False)
for f, e in ((F_HIT - 1, 0), (F_HIT, 25), (F_HIT + 6, 0)): fl.data.energy = e; fl.data.keyframe_insert("energy", frame=f)
fl.visible_camera = False

# ======================================================================
# 8) HANDLER + RENDER
# ======================================================================
def on_frame(scene, *a):
    f = scene.frame_current + scene.frame_subframe
    for sw in SWARMS: sw.update(f)
bpy.app.handlers.frame_change_pre.append(on_frame)

if os.environ.get("DBG"):
    for f in map(int, os.environ["DBG"].split(",")):
        sc.frame_set(f); print("DBG", f, [(b_, tuple(round(v, 2) for v in bw(b_))) for b_ in ("Hips", "Head", "RightHand", "LeftHand")])
if os.environ.get("EVENTS"):
    import json
    json.dump({"shots": SHOTS, "purk": F_PURK, "press": F_PRESS, "hit": F_HIT, "flush": F_FLUSH, "t200": F_200, "x27": F_27,
               "dry_on": DRY_ON, "end": END}, open(os.environ["EVENTS"], "w"))

r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = os.environ.get("MB", "1") == "1"; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = 0.0
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = False
r.use_overwrite = False; r.use_placeholder = True
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        os.makedirs(OUT, exist_ok=True)
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
