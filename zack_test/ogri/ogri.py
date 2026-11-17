# "O'g'ri va televizor" — Zack D. Films uslubida 46.3 s video (1112 kadr, 24 fps, 9:16).
# O'g'ri katta televizorni derazadan ham, eshikdan ham olib chiqolmaydi, uni qismlarga ajratmoqchi bo'ladi, lekin qorong'ida
# oshxonadagi eski mikroto'lqinli pechni buzib, sumkaga solib ketadi.
# Asos: zack_test/scene3.py, mixchar.py, gemorroy/gemorroy.py (yordamchilar: ogri/lib.py). Kadr rejasi: STORYBOARD.md.
# Assetlar: zack_test/tools/get_ogri.sh
# Render: OUT=/tmp/claude-0/frames_o/ SAMPLES=8 PCT=40 python3 -I zack_test/ogri/ogri.py --render
# Sinov: FRAMES=20,60,130 PCT=30   |   Bo'lak: RANGE=a,b
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *                      # sahnani tozalaydi
import bmesh
random.seed(11)

END = 1112
sc.frame_start, sc.frame_end = 1, END
def T(sec): return int(round(sec * 24)) + 1

# ---------------- kadrlar (Whisper so'z vaqtlari) ----------------
SHOTS = [(1, "hook"), (T(2.0), "tv"), (T(3.9), "greed"), (T(5.0), "big"), (T(7.4), "window"), (T(9.6), "nofit1"),
         (T(10.8), "door"), (T(12.4), "nofit2"), (T(13.6), "idea"), (T(16.6), "tool"), (T(18.2), "dark"), (T(19.6), "clock"),
         (T(21.9), "unscrew"), (T(23.6), "pile"), (T(25.0), "bag"), (T(27.3), "exit"), (T(29.2), "owner"), (T(31.2), "drop"),
         (T(32.5), "flee"), (T(33.8), "open"), (T(35.7), "nottv"), (T(37.8), "parts"), (T(39.7), "empty"),
         (T(41.9), "flashback"), (T(44.4), "street")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
def F0(n): return S[n][0]
def F1(n): return S[n][1]
ALL = [(1, END)]

def setkeys(o, path, pairs, mode="CONSTANT", data=False):
    tgt = o.data if data else o
    for f, v in pairs:
        setattr(tgt, path, v); tgt.keyframe_insert(path, frame=f)
    interp(tgt, mode, path)

# ======================================================================
# 1) MATERIALLAR
# ======================================================================
plaster = pbr("plaster", "painted_plaster_wall", 0.6, tint=(0.86, 0.8, 0.72))
outwall = pbr("outwall", "painted_plaster_wall", 0.5, tint=(0.72, 0.7, 0.66))
floor_m = pbr("laminate", "laminate_floor_02", 0.5)
paving = pbr("paving", "concrete_pavement", 0.4)
asph = pbr("asphalt", "asphalt_02", 0.25)
trim = mat("trim", (0.92, 0.91, 0.88), 0.4)
ceil_m = mat("ceil", (0.88, 0.87, 0.85), 0.85)
door_m = mat("door", (0.32, 0.18, 0.09), 0.35, coat=0.4)
dwood = mat("darkwood", (0.07, 0.045, 0.03), 0.35, coat=0.3)
brass = mat("brass", (0.85, 0.65, 0.3), 0.25, metal=1.0)
black = mat("black", (0.015, 0.015, 0.016), 0.45)
grass = mat("grass", (0.05, 0.1, 0.03), 0.95)
knit = mat("knit", (0.02, 0.02, 0.022), 0.95)
plastic = mat("plastic", (0.03, 0.03, 0.035), 0.3)
lens_m = emit_mat("lamp_lens", (1.0, 0.95, 0.85), 10.0)
fabric = mat("bagfab", (0.04, 0.06, 0.1), 0.85)
fabric_in = mat("bagin", (0.02, 0.022, 0.03), 0.95)
strap_m = mat("strap", (0.01, 0.01, 0.012), 0.6)
zip_m = mat("zip", (0.6, 0.6, 0.62), 0.25, metal=1.0)
steel = mat("steel", (0.75, 0.75, 0.77), 0.25, metal=1.0)
copper = mat("copper", (0.9, 0.45, 0.25), 0.3, metal=1.0)
pcb = mat("pcb", (0.02, 0.25, 0.08), 0.35, coat=0.5)
glass_m = mat("plate_glass", (0.85, 0.92, 0.9), 0.02, trans=1.0, ior=1.5)
win_glass = mat("win_glass", (0.6, 0.7, 0.75), 0.03, trans=1.0, ior=1.45)
bulb_m = emit_mat("bulb", (1.0, 0.85, 0.6), 12.0)
porch_m = emit_mat("porch", (1.0, 0.8, 0.5), 20.0)
winlit = emit_mat("winlit", (1.0, 0.72, 0.4), 3.5)
dust_m = mat("dust", (0.55, 0.53, 0.5), 0.95)

# ======================================================================
# 2) UY: mehmonxona x[-3,3] y[0,5.5]; oshxona x[-7.6,-3]; eshik y=0 devorda (x=-1.8), deraza x=3 devorda (y=2.5)
# ======================================================================
H = 2.7; WT = 0.15
house = empty("house")
LX0, LX1, LY0, LY1 = -7.6, 3.0, 0.0, 5.5
DOOR_X, DOOR_W, DOOR_H = -1.8, 0.92, 2.1
WIN_Y, WIN_W, WIN_Z0, WIN_Z1 = 2.5, 1.0, 0.95, 2.05
ARCH_Y0, ARCH_Y1, ARCH_H = 3.6, 5.0, 2.2

def wall_x(name, x, y0, y1, holes=()):
    """x = const devor (qalinlik WT), holes: [(y0, y1, z0, z1)]"""
    cuts = sorted(holes); ys = [y0]
    for a, b, za, zb in cuts: ys += [a, b]
    ys.append(y1)
    for i in range(0, len(ys), 2):
        if ys[i + 1] - ys[i] > 0.001:
            box(f"{name}_{i}", (WT, ys[i + 1] - ys[i], H), (x, (ys[i] + ys[i + 1]) / 2, H / 2), plaster, parent=house)
    for a, b, za, zb in cuts:
        if za > 0.001: box(f"{name}_lo{a}", (WT, b - a, za), (x, (a + b) / 2, za / 2), plaster, parent=house)
        box(f"{name}_hi{a}", (WT, b - a, H - zb), (x, (a + b) / 2, (H + zb) / 2), plaster, parent=house)
def wall_y(name, y, x0, x1, holes=()):
    cuts = sorted(holes); xs = [x0]
    for a, b, za, zb in cuts: xs += [a, b]
    xs.append(x1)
    for i in range(0, len(xs), 2):
        if xs[i + 1] - xs[i] > 0.001:
            box(f"{name}_{i}", (xs[i + 1] - xs[i], WT, H), ((xs[i] + xs[i + 1]) / 2, y, H / 2), plaster, parent=house)
    for a, b, za, zb in cuts:
        if za > 0.001: box(f"{name}_lo{a}", (b - a, WT, za), ((a + b) / 2, y, za / 2), plaster, parent=house)
        box(f"{name}_hi{a}", (b - a, WT, H - zb), ((a + b) / 2, y, (H + zb) / 2), plaster, parent=house)

wall_y("w_front", LY0 - WT / 2, LX0 - WT, LX1 + WT, [(DOOR_X - DOOR_W / 2, DOOR_X + DOOR_W / 2, 0, DOOR_H)])
wall_y("w_back", LY1 + WT / 2, LX0 - WT, LX1 + WT)
wall_x("w_right", LX1 + WT / 2, LY0, LY1, [(WIN_Y - WIN_W / 2, WIN_Y + WIN_W / 2, WIN_Z0, WIN_Z1)])
wall_x("w_left", LX0 - WT / 2, LY0, LY1)
wall_x("w_mid", -3.0, LY0, LY1, [(ARCH_Y0, ARCH_Y1, 0, ARCH_H)])
# tashqi suvoq (devor tashqi yuzasi) — eshik/deraza atrofida
for o in [o for o in house.children if o.name.startswith(("w_front", "w_right"))]:
    o.data.materials.clear(); o.data.materials.append(outwall)
plane("floor_lr", (LX1 - LX0, LY1 - LY0), ((LX0 + LX1) / 2, (LY0 + LY1) / 2, 0.0), floor_m, parent=house)
box("ceiling", (LX1 - LX0 + 0.4, LY1 - LY0 + 0.4, 0.12), ((LX0 + LX1) / 2, (LY0 + LY1) / 2, H + 0.06), ceil_m, parent=house)
box("roof", (LX1 - LX0 + 1.4, LY1 - LY0 + 1.4, 0.25), ((LX0 + LX1) / 2, (LY0 + LY1) / 2, H + 0.3), mat("roof", (0.12, 0.1, 0.09), 0.8), parent=house)
for x, y, l, rot in ((0.0, 0.05, 6.0, 0), (0.0, 5.45, 6.0, 0), (2.95, 2.75, 5.5, 90), (-2.9, 1.8, 3.6, 90)):
    box("baseboard", (l, 0.025, 0.1), (x, y, 0.05), trim, rot=(0, 0, rot), parent=house)
# eshik (ichkariga ochiladi: menteşe x = DOOR_X - W/2, +z burilish)
hinge = empty("door_hinge", (DOOR_X - DOOR_W / 2 + 0.02, 0.02, 0), house)
box("door", (DOOR_W - 0.04, 0.045, DOOR_H - 0.02), ((DOOR_W - 0.04) / 2, 0, DOOR_H / 2), door_m, parent=hinge, bevel=0.004)
sphere("knob", 0.03, (DOOR_W - 0.13, 0.05, 1.0), brass, parent=hinge)
sphere("knob2", 0.03, (DOOR_W - 0.13, -0.05, 1.0), brass, parent=hinge)
for dx in (-DOOR_W / 2 - 0.04, DOOR_W / 2 + 0.04):
    box("dframe", (0.08, WT + 0.04, DOOR_H + 0.04), (DOOR_X + dx, -WT / 2, DOOR_H / 2), trim, parent=house)
box("dframe_t", (DOOR_W + 0.16, WT + 0.04, 0.08), (DOOR_X, -WT / 2, DOOR_H + 0.04), trim, parent=house)
# deraza: ochiq ikki tabaqa (tashqariga ochilgan)
for dy in (-WIN_W / 2 - 0.03, WIN_W / 2 + 0.03):
    box("wframe", (WT + 0.05, 0.06, WIN_Z1 - WIN_Z0 + 0.06), (LX1 + WT / 2, WIN_Y + dy, (WIN_Z0 + WIN_Z1) / 2), trim, parent=house)
for z in (WIN_Z0 - 0.03, WIN_Z1 + 0.03):
    box("wframe_h", (WT + 0.12 if z < 1.5 else WT + 0.05, WIN_W + 0.12, 0.06), (LX1 + WT / 2 + (0.03 if z < 1.5 else 0), WIN_Y, z), trim, parent=house)
for s_ in (-1, 1):
    hg = empty(f"sash_h{s_}", (LX1 + WT, WIN_Y + s_ * WIN_W / 2, WIN_Z0), house)
    hg.rotation_euler = (0, 0, R(-s_ * 75))
    box("sash", (0.04, WIN_W / 2, WIN_Z1 - WIN_Z0), (0.02, -s_ * WIN_W / 4, (WIN_Z1 - WIN_Z0) / 2), trim, parent=hg)
    box("sash_g", (0.012, WIN_W / 2 - 0.08, WIN_Z1 - WIN_Z0 - 0.08), (0.025, -s_ * WIN_W / 4, (WIN_Z1 - WIN_Z0) / 2), win_glass, parent=hg)
# parda
for dy in (-0.85, 0.85):
    c = box("curtain", (0.06, 0.55, 2.3), (LX1 - 0.12, WIN_Y + dy, 1.3), mat("curtain", (0.55, 0.5, 0.42), 0.9), parent=house)
    wv = c.modifiers.new("wave", "WAVE"); wv.height = 0.03; wv.width = 0.12; wv.narrowness = 1.0; wv.use_y = False; wv.speed = 0
    c.modifiers.new("sub", "SUBSURF").levels = 1
# arka (oshxona) romi
for y in (ARCH_Y0, ARCH_Y1):
    box("arch_fr", (WT + 0.04, 0.06, ARCH_H), (-3.0, y, ARCH_H / 2), trim, parent=house)
box("arch_fr_t", (WT + 0.04, ARCH_Y1 - ARCH_Y0 + 0.12, 0.06), (-3.0, (ARCH_Y0 + ARCH_Y1) / 2, ARCH_H), trim, parent=house)

# --- mehmonxona mebeli ---
TVP = Vector((0.5, 5.2, 0.0))                       # televizor tumbasi markazi
box("tv_stand", (2.0, 0.45, 0.46), (TVP.x, TVP.y, 0.23), dwood, parent=house, bevel=0.01)
for dx in (-0.5, 0.5):
    box("tv_stand_dr", (0.95, 0.01, 0.36), (TVP.x + dx, TVP.y - 0.226, 0.23), mat("drawer", (0.05, 0.035, 0.025), 0.3, coat=0.4), parent=house)
sofa = empty("sofa", (0.5, 1.75, 0), house); import_gltf(PH + "Sofa_01/Sofa_01.gltf", sofa)
table = empty("ctable", (0.5, 3.15, 0), house); import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", table)
plant = empty("plant", (2.45, 4.95, 0), house); import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", plant); plant.scale = (1.3,) * 3
box("rug", (2.6, 1.9, 0.012), (0.5, 2.9, 0.006), mat("rug", (0.35, 0.12, 0.08), 0.95), parent=house, bevel=0.004)
cyl("lamp_shade", 0.25, 0.12, (0.5, 2.9, H - 0.12), mat("shade", (0.9, 0.88, 0.82), 0.6, sss=0.2), parent=house, verts=48)
bulb = sphere("bulb", 0.05, (0.5, 2.9, H - 0.2), bulb_m, parent=house)
# rasmlar (oyna yo'q — aks ettirish tuzog'i)
box("art1", (0.9, 0.03, 0.6), (-1.0, 5.43, 1.65), mat("art1", (0.2, 0.35, 0.5), 0.8), parent=house)
box("art2", (0.03, 0.7, 0.5), (-2.93, 1.6, 1.6), mat("art2", (0.55, 0.35, 0.2), 0.8), parent=house)

# --- oshxona ---
KIT = Vector((-5.25, LY1 - 0.31, 0.0))
kit = empty("kitchen", tuple(KIT), house); import_gltf(BK + "984fd8f8_u.glb", kit)
for o in kit.children_recursive:
    if o.type == "MESH" and o.name.startswith("BooleanReady"): o.hide_render = True
box("kit_floor", (4.6, 5.5, 0.004), (-5.3, 2.75, 0.002), mat("kfloor", (0.42, 0.4, 0.37), 0.4, coat=0.2), parent=house)
# soat (oshxona devorida, x=-3 devorning oshxona tomoni)
CLK = Vector((-3.0 - WT / 2 - 0.02, 2.3, 1.85))
clk = empty("clock", tuple(CLK), house); clk.rotation_euler = (0, R(-90), 0)          # mahalliy +Z -> dunyo -X
cyl("clk_body", 0.17, 0.04, (0, 0, 0.0), mat("clkb", (0.9, 0.9, 0.88), 0.4), parent=clk, verts=64)
cyl("clk_rim", 0.18, 0.03, (0, 0, -0.012), black, parent=clk, verts=64)
for i in range(12):
    a = 2 * math.pi * i / 12
    box("clk_tick", (0.012, 0.03 if i % 3 else 0.045, 0.004), (0.145 * math.sin(a), 0.145 * math.cos(a), 0.022), black, rot=(0, 0, -math.degrees(a)), parent=clk)
hand_m = empty("clk_min", (0, 0, 0.026), clk); box("min_hand", (0.008, 0.13, 0.003), (0, 0.055, 0), black, parent=hand_m)
hand_h = empty("clk_hr", (0, 0, 0.024), clk); box("hr_hand", (0.012, 0.085, 0.003), (0, 0.035, 0), black, parent=hand_h)
sphere("clk_pin", 0.008, (0, 0, 0.03), black, parent=clk)

# --- tashqari: yer, yo'lak, ayvon chirog'i ---
plane("ground", (80, 80), (0, 0, -0.005), grass)
plane("path", (1.4, 6.0), (DOOR_X, -3.1, 0.0), paving)
plane("side_path", (1.5, 9.0), (LX1 + 1.0, 2.5, 0.0), paving)
box("porch_lamp", (0.12, 0.08, 0.2), (DOOR_X + 0.75, -WT - 0.05, 2.15), porch_m)

# ======================================================================
# 3) ASSETLAR: televizor, mikroto'lqinli pech (butun + qismlar), sumka, otvyortka
# ======================================================================
tv = empty("tv"); import_gltf(BK + "5baba85b_u.glb", tv)
TV_W, TV_H = 1.67, 0.984
for o in tv.children_recursive:
    if o.type == "MESH":
        for i, m in enumerate(o.data.materials):
            if m and "screen" in m.name.lower():
                o.data.materials[i] = mat("tv_screen", (0.006, 0.006, 0.008), 0.07, coat=1.0)
            elif m:
                o.data.materials[i] = mat("tv_body", (0.045, 0.045, 0.05), 0.28, metal=0.3, coat=0.5)
led = sphere("tv_led", 0.004, (0.0, -0.11, 0.035), emit_mat("led", (1, 0.05, 0.02), 8.0), parent=tv)
TV_HOME = (TVP.x, TVP.y, 0.46)
def tv_home(f): key(tv, f, loc=TV_HOME, rot=(0, 0, 0))

def load_mw(name, parent, scale=0.5):
    """eski pech (BlenderKit cab01678, CC0): butun model; mahalliy old = -Y, 1 m eni -> scale 0.5"""
    e = empty(name, (0, 0, 0), parent); import_gltf(BK + "cab01678_u.glb", e); e.scale = (scale,) * 3; return e

def mw_parts(name):
    """pechni bo'laklarga ajratish: yupqa panellar guruhlab birlashtiriladi + Solidify (qalinlik)"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=BK + "cab01678_u.glb")
    new = [o for o in bpy.data.objects if o not in before]
    me = next(o for o in new if o.type == "MESH")
    bpy.ops.object.select_all(action="DESELECT"); bpy.context.view_layer.objects.active = me; me.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    isl = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    groups = {}
    for o in isl:
        pts = [Vector(c) for c in o.bound_box]; c = sum(pts, Vector()) / 8
        if c.y < -0.3: g = "door" if c.x < 0.28 else "panel"
        elif c.z > 0.505 and abs(c.x - 0.3) < 0.16: g = "cord"
        elif c.z > 0.48: g = "top"
        elif c.z < 0.045: g = "bottom"
        elif c.x < -0.48: g = "left"
        elif c.x > 0.49: g = "right"
        elif c.y > 0.3: g = "back"
        else: g = "inner"
        groups.setdefault(g, []).append(o)
    out = {}
    for g, obs in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs: o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join()
        j = bpy.context.object; j.name = f"{name}_{g}"; j.parent = None
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        j.scale = (0.5,) * 3; j.location = j.location * 0.5
        sd = j.modifiers.new("sol", "SOLIDIFY"); sd.thickness = 0.008; sd.offset = 0
        out[g] = j
    for o in new:
        if o.name in bpy.data.objects and o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
    return out

def extra_parts(name):
    """ichki qismlar (procedural): aylanuvchi shisha likopcha, magnetron, transformator, plata, vintlar"""
    d = {}
    pl = cyl(name + "_plate", 0.135, 0.012, (0, 0, 0), glass_m, verts=64); d["plate"] = pl
    mg = empty(name + "_magnetron"); d["magnetron"] = mg
    box(name + "_mg_body", (0.09, 0.09, 0.07), (0, 0, 0.035), steel, parent=mg, bevel=0.004)
    for i in range(6): box(name + "_mg_fin", (0.11, 0.11, 0.003), (0, 0, 0.012 * i + 0.005), mat("alu", (0.8, 0.8, 0.82), 0.35, metal=1.0), parent=mg)
    cyl(name + "_mg_ant", 0.012, 0.04, (0, 0, 0.09), copper, parent=mg)
    tr = empty(name + "_trafo"); d["trafo"] = tr
    box(name + "_tr_core", (0.1, 0.07, 0.08), (0, 0, 0.04), mat("iron", (0.2, 0.2, 0.22), 0.4, metal=1.0), parent=tr, bevel=0.003)
    for s_ in (-1, 1): box(name + "_tr_coil", (0.035, 0.075, 0.06), (s_ * 0.028, 0, 0.04), copper, parent=tr, bevel=0.006)
    pb = empty(name + "_pcb"); d["pcb"] = pb
    box(name + "_pcb_b", (0.16, 0.1, 0.004), (0, 0, 0), pcb, parent=pb)
    for i in range(7):
        box(name + "_chip", (0.015 + 0.01 * (i % 3), 0.012, 0.008), (-0.06 + 0.02 * i, 0.02 * ((i % 2) * 2 - 1), 0.006), black, parent=pb)
    cyl(name + "_cap", 0.008, 0.02, (0.05, -0.03, 0.012), mat("cap", (0.1, 0.15, 0.5), 0.3), parent=pb, verts=16)
    for i in range(3):
        sc_ = cyl(name + f"_screw{i}", 0.003, 0.012, (0, 0, 0), steel, verts=12); d[f"screw{i}"] = sc_
    return d

# oshxona peshtaxtasi (pech o'rni) — ray bilan topiladi
kit_meshes = [o for o in kit.children_recursive if o.type == "MESH"]
bpy.context.view_layer.update()
MWX = float(os.environ.get("MWX", -4.78)); MWY = 5.13
CZ = ray_down(kit_meshes, MWX, MWY, 1.3) or 0.9
print("counter z", CZ)
MW_COUNTER = Vector((MWX, MWY, CZ))
mw_counter = load_mw("mw_counter", None); mw_counter.location = MW_COUNTER
# pech polda (o'g'ri uni yerga tushirib buzadi)
MW_FLOOR = Vector((-4.45, 4.55, 0.0))
mw_floor = load_mw("mw_floor", None); mw_floor.location = MW_FLOOR; mw_floor.rotation_euler = (0, 0, R(90))
MP = mw_parts("mwp"); XP = extra_parts("xp")
# peshtaxtada chang izi + uzilgan sim
dust = empty("dust_print", (MWX, MWY, CZ + 0.001))
dmat = mat("dustm", (0.42, 0.4, 0.37), 0.95)
for (sx, sy, x, y) in ((0.56, 0.035, 0, 0.168), (0.56, 0.035, 0, -0.168), (0.035, 0.37, 0.263, 0), (0.035, 0.37, -0.263, 0)):
    plane("dust_e", (sx, sy), (x, y, 0), dmat, parent=dust)
for i in range(4): cyl("foot_mark", 0.018, 0.001, (0.2 * (1 if i % 2 else -1), 0.12 * (1 if i // 2 else -1), 0), mat("ring", (0.3, 0.28, 0.25), 0.9), parent=dust, verts=16)
cord_pts = [MW_COUNTER + Vector((0.2, 0.28, 0.25)), MW_COUNTER + Vector((0.2, 0.26, 0.02)), MW_COUNTER + Vector((0.1, 0.05, 0.004)), MW_COUNTER + Vector((-0.05, -0.1, 0.004)), MW_COUNTER + Vector((-0.12, -0.26, 0.004)), MW_COUNTER + Vector((-0.12, -0.3, -0.12))]
cord = bpy.data.curves.new("cord", "CURVE"); cord.dimensions = "3D"; cord.bevel_depth = 0.004
sp = cord.splines.new("POLY"); sp.points.add(len(cord_pts) - 1)
for p_, c_ in zip(sp.points, cord_pts): p_.co = (*c_, 1)
cord_o = bpy.data.objects.new("cord", cord); sc.collection.objects.link(cord_o); cord_o.data.materials.append(black)
box("socket", (0.08, 0.012, 0.12), tuple(MW_COUNTER + Vector((0.2, 0.355, 0.27))), trim, parent=cord_o)

# --- sumka (duffel): yopiq va ochiq variantlar ---
def bag_closed(name):
    e = empty(name)
    b = cyl(name + "_body", 0.16, 0.62, (0, 0, 0.16), fabric, rot=(0, 90, 0), parent=e, verts=48)
    b.scale = (1.0, 1.0, 1.0)
    bv = b.modifiers.new("bev", "BEVEL"); bv.width = 0.06; bv.segments = 6; bv.limit_method = "ANGLE"
    b.modifiers.new("sub", "SUBSURF").levels = 2
    box(name + "_zip", (0.5, 0.012, 0.01), (0, 0, 0.32), zip_m, parent=e)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.012); h_ = bpy.context.object
        h_.name = name + "_handle"; h_.rotation_euler = (R(90), 0, 0); h_.location = (s_ * 0.0, s_ * 0.03, 0.32)
        h_.scale = (1.0, 1.4, 1.0); h_.data.materials.append(strap_m); h_.parent = e
        for v in h_.data.vertices:
            if v.co.y < 0: v.co.y = 0
    box(name + "_band", (0.03, 0.33, 0.33), (-0.2, 0, 0.16), strap_m, parent=e, bevel=0.01)
    box(name + "_band2", (0.03, 0.33, 0.33), (0.2, 0, 0.16), strap_m, parent=e, bevel=0.01)
    return e
def bag_open(name):
    """yuqorisi ochiq: yarim silindr qobiq + ikki qopqoq (flap) tashqariga yotgan"""
    e = empty(name); n = 40; L_ = 0.62; r_ = 0.17; vs = []; fs = []
    for i in range(n + 1):
        a = math.pi * (0.06 + 0.88 * i / n)              # pastki yarim + biroz yuqoriga
        for x in (-L_ / 2, L_ / 2):
            vs.append((x, r_ * math.cos(a) * 1.0, 0.17 - r_ * math.sin(a)))
    for i in range(n): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    sh = mesh_obj(name + "_shell", vs, fs, fabric, parent=e); smooth(sh)
    sh.data.materials.append(fabric_in)
    sd = sh.modifiers.new("sol", "SOLIDIFY"); sd.thickness = 0.008; sd.material_offset = 1
    # uchlari (yon devorlar)
    for x in (-L_ / 2, L_ / 2):
        ring = [(x, r_ * math.cos(math.pi * (0.06 + 0.88 * i / n)), 0.17 - r_ * math.sin(math.pi * (0.06 + 0.88 * i / n))) for i in range(n + 1)]
        cap = mesh_obj(name + "_end", ring, [tuple(range(n + 1))], fabric, parent=e); cap.modifiers.new("sol", "SOLIDIFY").thickness = 0.008
    for s_ in (-1, 1):
        fl = box(name + "_flap", (0.6, 0.16, 0.008), (0, s_ * 0.24, 0.3), fabric, rot=(s_ * -35, 0, 0), parent=e, bevel=0.003)
        box(name + "_zipside", (0.58, 0.01, 0.01), (0, s_ * 0.17, 0.335), zip_m, parent=e)
    plane(name + "_inner", (0.58, 0.28), (0, 0, 0.012), fabric_in, parent=e)
    return e
bagC = bag_closed("bagC"); bagO = bag_open("bagO")
# sumka ichidagi qismlar (bagO ga nisbatan)
def put(o, parent, loc, rot):
    o.parent = parent; o.location = loc; o.rotation_euler = [R(a) for a in rot]
IN_BAG = [("door", (-0.12, 0.0, 0.12), (68, 8, 4)), ("panel", (0.17, 0.04, 0.12), (75, -10, 20)),
          ("left", (0.0, -0.05, 0.08), (12, 70, 90)), ("top", (0.05, 0.03, 0.2), (-15, 8, 0)), ("cord", (0.18, -0.05, 0.24), (0, 0, 40))]
for g, l_, r_ in IN_BAG:
    if g in MP: put(MP[g], bagO, l_, r_)
put(XP["plate"], bagO, (-0.08, 0.02, 0.24), (22, -10, 0)); put(XP["magnetron"], bagO, (0.12, -0.06, 0.2), (20, 15, 30))
put(XP["pcb"], bagO, (0.0, 0.07, 0.21), (-25, 5, 10)); put(XP["trafo"], bagO, (0.21, 0.06, 0.18), (0, 30, 0))
for i in range(3): put(XP[f"screw{i}"], bagO, (-0.2 + 0.07 * i, 0.06 - 0.04 * i, 0.255), (80, 0, 30 * i))
# qolgan pech qismlari: polda uyum (pile) uchun nusxalar
def dup_tree(o, name):
    c = o.copy(); c.name = name; sc.collection.objects.link(c); c.parent = None
    for ch in o.children:
        cc = dup_tree(ch, name + "_" + ch.name); cc.parent = c; cc.matrix_parent_inverse = ch.matrix_parent_inverse.copy()
    return c
PILE = []
for g in ("back", "right", "bottom", "inner", "door", "panel", "top", "left"):
    if g in MP: PILE.append(dup_tree(MP[g], "pile_" + g))
for k_ in ("plate", "magnetron", "pcb", "trafo"):
    PILE.append(dup_tree(XP[k_], "pile_" + k_))

scr = empty("screwdriver"); import_gltf(BK + "c0e7f651_u.glb", scr)

# ======================================================================
# 4) QAHRAMONLAR: David (o'g'ri), Brian (uy egasi)
# ======================================================================
troot, thief, tmeshes = mc.load_character("thief", "David.fbx"); sc.render.fps = 24
oroot, owner, omeshes = mc.load_character("owner", "Brian.fbx"); sc.render.fps = 24
soften(tmeshes); soften(omeshes)
def bwp(arm, b): return (arm.matrix_world @ arm.pose.bones["mixamorig:" + b].head).copy()

# qalpoq + peshona chirog'i (Head fazosi: X chap, Y tepa, Z old)
thead = child_of_bone("thief_head", thief, "Head")
def head_mesh(name, r, cy, sy, cut, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0); o = bpy.context.object; o.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < cut], context="VERTS"); bm.to_mesh(o.data); bm.free()
    o.scale = (r[0], r[2], sy); o.rotation_euler = (R(-90), 0, 0); o.location = (0, cy, r[3]); o.parent = thead
    o.data.materials.append(m); smooth(o); o.modifiers.new("sol", "SOLIDIFY").thickness = 0.01
    return o
beanie = head_mesh("beanie", (0.1, 0, 0.115, 0.012), 0.15, 0.09, -0.06, knit)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.12, major_segments=48); cuff = bpy.context.object
cuff.name = "beanie_cuff"; cuff.parent = thead; cuff.rotation_euler = (R(-90), 0, 0); cuff.location = (0, 0.153, 0.012)
cuff.scale = (0.101, 0.116, 0.2); cuff.data.materials.append(knit); smooth(cuff)
lamp = empty("headlamp", (0, 0.153, 0.128), thead); lamp.rotation_euler = (R(-12), 0, 0)
box("hl_body", (0.05, 0.035, 0.03), (0, 0, -0.004), plastic, parent=lamp, bevel=0.006)
cyl("hl_lens", 0.014, 0.006, (0, 0, 0.014), lens_m, parent=lamp, verts=24)
spot = bpy.data.objects.new("hl_spot", bpy.data.lights.new("hl_spot", "SPOT")); sc.collection.objects.link(spot)
spot.parent = lamp; spot.location = (0, 0, 0.02); spot.rotation_euler = (R(180), 0, 0)
spot.data.spot_size = R(48); spot.data.spot_blend = 0.45; spot.data.shadow_soft_size = 0.01; spot.data.color = (1.0, 0.93, 0.8)
spot.data.energy = 150.0
# nur konusi (yengil "hajm" effekti)
bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.0, radius2=0.62, depth=1.4, end_fill_type="NOTHING"); beam = bpy.context.object
beam.name = "hl_beam"; beam.parent = lamp; beam.location = (0, 0, 0.72)
beam_m = glow_mat("beam", (1.0, 0.9, 0.7)); beam.data.materials.append(beam_m); smooth(beam)
# Brian bosh/yuz nuqtasi
ohead = child_of_bone("owner_head", owner, "Head"); oface = empty("oface", (0, 0.07, 0.09), ohead)
tface = empty("tface", (0, 0.07, 0.1), thead)
# otvyortka o'ng qo'lda (Mixamo qo'l: Y = barmoqlar)
rhand = child_of_bone("thief_rh", thief, "RightHand")
scr.parent = rhand; scr.location = (0.0, 0.085, 0.03); scr.rotation_euler = (R(90), 0, R(90))

# ---------------- harakatlar ----------------
SNEAK = A_("Sneak_Walk.fbx"); LOOK = A_("Look_Around.fbx", False); LIFT = A_("Lifting_Object.fbx", False)
PUSH = A_("Push_2.fbx"); BOXW = A_("Jogging_With_Box.fbx"); BOXI = A_("Box_Idle.fbx", False)
THINK = A_("Thinking.fbx", False); POCKET = A_("Searching_Pockets.fbx", False); WORK = A_("Working_On_Device.fbx", False)
BAGW = A_("Walking_With_Shopping_Bag.fbx"); REACT = A_("Reacting.fbx", False); RUN2 = A_("Running_2.fbx", False)
KNEEL = A_("Kneeling_Down.fbx", False); SPRINT = A_("Sprint.fbx"); IDLE = A_("Idle.fbx", False); TERR = A_("Terrified.fbx", False)
sc.render.fps = 24

def act(arm, a, f0, f1, src=None, speed=None, blend=0):
    """kadr [f0, f1] ga strip; speed berilmasa src ni kadrga sig'diradi"""
    if src is None: src = (1, int(a.frame_range[1]))
    if speed is None: speed = (src[1] - src[0]) / ((f1 - f0 + 1) * 1.25)
    s = mc.add_strip(arm, a, f0, src=src, speed=speed, blend=blend, hold=True)
    s.blend_out = 0; s.use_auto_blend = False
    return s
RKEYS = {}
def stage(root, f, loc, rot, lin_to=None):
    """root ni f kadrda joylash; lin_to=(f2, loc2) bo'lsa chiziqli siljish"""
    place(root, f, loc, rot)
    RKEYS.setdefault(root.name, {})[f] = "LINEAR" if lin_to else "CONSTANT"
    if lin_to:
        place(root, lin_to[0], lin_to[1], rot); RKEYS[root.name].setdefault(lin_to[0], "CONSTANT")
def fix_root(root):
    for fc in fcurves(root):
        for k in fc.keyframe_points: k.interpolation = RKEYS.get(root.name, {}).get(int(round(k.co.x)), "CONSTANT")

STREET = Vector((60.0, 0.0, 0.0))
SP_SNEAK = 0.0586
# 1 hook: eshikdan kiradi (+Y ga qarab)
act(thief, SNEAK, F0("hook"), F1("hook"), speed=0.55, src=(1, 28))
thief.animation_data.nla_tracks[-1].strips[0].repeat = 3.0
stage(troot, F0("hook"), (DOOR_X + 0.05, -1.45, 0), 180, (F1("hook"), (DOOR_X + 0.05, -1.45 + SP_SNEAK * (F1("hook") - F0("hook")), 0)))
# 2-3 tv / greed: atrofga qaraydi
TPOS = Vector((0.05, 2.75, 0))
act(thief, LOOK, F0("tv"), F1("greed"), src=(10, 120))
stage(troot, F0("tv"), tuple(TPOS), 180)
# 4 big: televizorni ko'taradi (TV oldida, +Y ga qarab)
BIGP = Vector((1.75, 3.65, 0))
act(thief, LIFT, F0("big"), F1("big"), src=(62, 175))
stage(troot, F0("big"), tuple(BIGP), 180)
# 5-6 window: derazaga itaradi (+X ga qarab, rot 90)
PUSH_SPD = 0.026
F_HIT1 = F0("nofit1") + 3
HIT1_X = LX1 - 0.13 - 0.85                       # root x: TV old yuzi devorga tegadi
act(thief, PUSH, F0("window"), F1("nofit1"), src=(30, 30 + int((F1("nofit1") - F0("window") + 1) * 1.25)), speed=1.0)
stage(troot, F0("window"), (HIT1_X - PUSH_SPD * (F_HIT1 - F0("window")), WIN_Y, 0), 90, (F_HIT1, (HIT1_X, WIN_Y, 0)))
stage(troot, F_HIT1 + 3, (HIT1_X - 0.06, WIN_Y, 0), 90)
# 7-8 door: TV ni ko'tarib eshik tomon (-Y, rot 0)
SP_BOX = 0.062
F_HIT2 = F0("nofit2") + 3
HIT2_Y = 0.12 + 0.66
act(thief, BOXW, F0("door"), F_HIT2, src=(1, 24), speed=0.55); thief.animation_data.nla_tracks[-1].strips[0].repeat = 4.0
act(thief, BOXI, F_HIT2 + 1, F1("nofit2"), src=(1, 60))
stage(troot, F0("door"), (DOOR_X, HIT2_Y + SP_BOX * (F_HIT2 - F0("door")), 0), 0, (F_HIT2, (DOOR_X, HIT2_Y, 0)))
stage(troot, F_HIT2 + 1, (DOOR_X, HIT2_Y + 0.12, 0), 0)
# 9 idea: o'ylaydi (eshik yonida, -Y ga qarab)
IDP = Vector((-1.1, 1.5, 0))
act(thief, THINK, F0("idea"), F1("idea"), src=(1, 100))
stage(troot, F0("idea"), tuple(IDP), 0)
# 10 tool: cho'ntagidan otvyortka
act(thief, POCKET, F0("tool"), F1("tool"), src=(70, 140))
stage(troot, F0("tool"), tuple(IDP), 0)
# 11 dark: oshxona tomon yuradi (-X, rot -90)
DK0 = Vector((-1.0, 4.3, 0))
act(thief, SNEAK, F0("dark"), F1("dark"), src=(1, 28), speed=0.5); thief.animation_data.nla_tracks[-1].strips[0].repeat = 3.0
SPD_DK = 0.085 * 0.5 / 0.8 * 1.0
stage(troot, F0("dark"), tuple(DK0), -90, (F1("dark"), tuple(DK0 + Vector((-SPD_DK * (F1("dark") - F0("dark")), 0, 0)))))
# 12-14 clock/unscrew/pile + 24 flashback: polda pechni buzadi (+Y ga qarab)
WKP = MW_FLOOR + Vector((0, -0.47, 0))
act(thief, WORK, F0("clock"), F1("pile"), src=(33, 160))
stage(troot, F0("clock"), tuple(WKP), 180)
# 15 bag: (o'g'ri kadrda emas, faqat qo'llar) — tepadan
act(thief, WORK, F0("bag"), F1("bag"), src=(40, 100))
stage(troot, F0("bag"), tuple(WKP), 180)
# 16 exit: sumka bilan eshik tomon (-Y)
SP_BAG = 1.32 / 38 * 0.8                         # m / kadr (24 fps)
EX1 = Vector((DOOR_X, 1.05, 0))
act(thief, BAGW, F0("exit"), F0("owner") + 8, src=(1, 39), speed=1.0); thief.animation_data.nla_tracks[-1].strips[0].repeat = 3.0
stage(troot, F0("exit"), tuple(EX1 + Vector((0, SP_BAG * (F0("owner") + 8 - F0("exit")), 0))), 0, (F0("owner") + 8, tuple(EX1)))
# 17 owner: qotib qoladi
F_LIGHT = T(29.75)
act(thief, REACT, F0("owner") + 9, F1("drop"), src=(5, 70))
stage(troot, F0("owner") + 9, tuple(EX1), 0)
# 18-19 flee: burilib qochadi (Running_2, ildiz harakati bilan)
act(thief, RUN2, F0("flee"), F1("flee"), src=(5, 50), speed=1.25)
stage(troot, F0("flee"), tuple(EX1), 0)
# 22 flashback (yana pech yonida)
act(thief, WORK, F0("flashback"), F1("flashback"), src=(40, 150))
stage(troot, F0("flashback"), tuple(WKP), 180)
# 25 street: tungi ko'chada yuguradi (-Y)
SP_RUN = 0.19 * 0.8 * 0.75
act(thief, SPRINT, F0("street"), END, src=(1, 17), speed=0.75); thief.animation_data.nla_tracks[-1].strips[0].repeat = 8.0
ST0 = STREET + Vector((-0.9, 3.5, 0.14))
stage(troot, F0("street"), tuple(ST0), 0, (END, tuple(ST0 + Vector((0, -SP_RUN * (END - F0("street")), 0)))))
fix_root(troot)

# --- uy egasi ---
OWN = Vector((DOOR_X, -0.45, 0))
act(owner, REACT, F0("owner"), F1("flee"), src=(1, 80))
stage(oroot, 1, (0, -30, 0), 0)
stage(oroot, F0("owner"), tuple(OWN), 180)
OKN = Vector((DOOR_X + 0.02, 0.78, 0))
act(owner, KNEEL, F0("open"), F1("open"), src=(20, 84))
act(owner, KNEEL, F1("open") + 1, END, src=(80, 84))
stage(oroot, F0("open"), tuple(OKN), 180)
stage(oroot, F0("parts"), (0, -30, 0), 0)
fix_root(oroot)

# ko'rinish
vis(troot, rng("hook", "tv", "greed", "big", "window", "nofit1", "door", "nofit2", "idea", "tool", "dark", "clock", "unscrew",
               "pile", "bag", "exit", "owner", "drop", "flee", "flashback", "street"))
vis(thead, rng("hook", "tv", "greed", "big", "window", "nofit1", "door", "nofit2", "idea", "tool", "dark", "clock", "unscrew",
               "pile", "bag", "exit", "owner", "drop", "flee", "flashback", "street"))
vis(oroot, rng("owner", "drop", "flee", "open", "nottv"))
vis(scr, rng("tool", "dark", "clock", "unscrew", "pile", "flashback"))

# ======================================================================
# 5) OB'EKTLAR HARAKATI (TV, sumka, pech, qismlar) — qo'llardan "bake"
# ======================================================================
def tv_to_hands(frames, arm, root_rot, up=0.0, fwd=0.12, dz=0.0, extra=None):
    """TV ni ikki qo'l o'rtasiga (orqasi o'g'riga qaragan) — har kadr kalit"""
    for f in frames:
        sc.frame_set(f)
        mid = (bwp(arm, "LeftHand") + bwp(arm, "RightHand")) / 2
        fw = Matrix.Rotation(R(root_rot), 3, "Z") @ Vector((0, -1, 0))
        loc = mid + fw * fwd + Vector((0, 0, up + dz))
        if extra: loc += extra(f)
        tv.location = loc; tv.rotation_euler = (0, 0, R(root_rot + 180)); tv.keyframe_insert("location", frame=f); tv.keyframe_insert("rotation_euler", frame=f)
tv_home(1); tv_home(F1("greed"))
# big: polda turgan TV ni ko'taradi (pastki qirra = qo'llar - 0.41 m)
sc.frame_set(F0("big")); GRIP0 = ((bwp(thief, "LeftHand") + bwp(thief, "RightHand")) / 2).z
tv_to_hands(range(F0("big"), F1("big") + 1), thief, 180, up=-GRIP0, fwd=0.16)
for f in range(F0("big"), F1("big") + 1):                   # pastga tushmasin (pol)
    sc.frame_set(f)
    if tv.location.z < 0: tv.location.z = 0.0; tv.keyframe_insert("location", frame=f)
# window: TV qo'llar oldida, pastki qirra ~0.78 m; zarbadan keyin orqaga sakraydi
def jolt(fh):
    def g(f):
        d = f - fh
        if 0 <= d < 6: return Vector((0, 0, 0.02 * math.sin(d * 2.2) * (1 - d / 6)))
        return Vector()
    return g
tv_to_hands(range(F0("window"), F1("nofit1") + 1), thief, 90, up=-0.37, fwd=0.14, extra=jolt(F_HIT1))
for f in range(F_HIT1, F1("nofit1") + 1):                  # devordan o'tib ketmasin
    sc.frame_set(f)
    if tv.location.x > LX1 - 0.02 - 0.11: tv.location.x = LX1 - 0.02 - 0.11; tv.keyframe_insert("location", frame=f)
# door: ko'tarib yuradi (pastki qirra qo'llardan 0.08 pastda)
tv_to_hands(range(F0("door"), F1("nofit2") + 1), thief, 0, up=-0.5, fwd=0.14, extra=jolt(F_HIT2))
for f in range(F_HIT2, F1("nofit2") + 1):
    sc.frame_set(f)
    if tv.location.y < 0.12: tv.location.y = 0.12; tv.keyframe_insert("location", frame=f)
# idea/tool: TV eshik yonida devorga suyalgan
key(tv, F0("idea"), loc=(DOOR_X + 1.05, 0.2, 0.0), rot=(-8, 0, 0)); key(tv, F1("tool"), loc=(DOOR_X + 1.05, 0.2, 0.0), rot=(-8, 0, 0))
tv_home(F0("dark")); tv.rotation_euler = (0, 0, 0); tv.keyframe_insert("rotation_euler", frame=F0("dark"))
CUTS = {F1(n) for n in S}
def lin_cuts(o):
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT" if int(round(k.co.x)) in CUTS or fc.data_path == "hide_render" else "LINEAR"
lin_cuts(tv)
# window/door/idea kalitlari orasida chiziqli (har kadr kalit bor, shuning uchun CONSTANT ham bir xil)

# sumka: exit/owner da o'ng qo'lda; drop da qo'ldan tushadi; open da ochiq variant
F_DROP = T(31.85)
BAG_FLOOR = Vector((DOOR_X - 0.02, 1.2, 0.0))
for f in range(F0("exit"), F_DROP + 1):
    sc.frame_set(f); h_ = bwp(thief, "RightHand")
    bagC.location = h_ + Vector((0, 0, -0.42)); bagC.rotation_euler = (0, 0, R(90 + 4 * math.sin(f * 0.4)))
    bagC.keyframe_insert("location", frame=f); bagC.keyframe_insert("rotation_euler", frame=f)
p0 = bagC.location.copy(); nfall = 9
for i in range(1, nfall + 1):
    t = i / nfall; p = p0.lerp(BAG_FLOOR, t); p.z = p0.z * (1 - t * t)
    bagC.location = p; bagC.rotation_euler = (R(8 * t), 0, R(90 + 15 * t)); bagC.keyframe_insert("location", frame=F_DROP + i); bagC.keyframe_insert("rotation_euler", frame=F_DROP + i)
FB = F_DROP + nfall
for i, (dz, rx) in enumerate(((0.05, 4), (0.0, 0), (0.015, -2), (0.0, 0))):
    bagC.location = BAG_FLOOR + Vector((0, 0, dz)); bagC.rotation_euler = (R(rx), 0, R(105)); bagC.keyframe_insert("location", frame=FB + 2 * i + 1); bagC.keyframe_insert("rotation_euler", frame=FB + 2 * i + 1)
lin_cuts(bagC)
vis(bagC, [(F0("exit"), F1("flee"))])
# ochiq sumka: bag (stol ustidagi kabi polda, pech yonida), open/parts — eshik yonida polda
BAG_K = MW_FLOOR + Vector((0.55, -0.15, 0.0))
key(bagO, 1, loc=tuple(BAG_K), rot=(0, 0, 90))
key(bagO, F0("open"), loc=tuple(BAG_FLOOR), rot=(0, 0, 105))
interp(bagO, "CONSTANT")
vis(bagO, rng("bag", "open", "parts"))

# pech: peshtaxtada (ilgak..dark, flashback boshlanishida yo'q), polda (clock..pile, flashback)
vis(mw_counter, [(1, F1("dark"))])
vis(mw_floor, rng("clock", "unscrew", "flashback"))
vis(dust, rng("empty")); vis(cord_o, rng("empty"))
# unscrew: qismlar uchib chiqadi (vintlar, eshik paneli)
FLY = []
for i in range(6):
    s_ = cyl(f"fly_screw{i}", 0.003, 0.012, (0, 0, 0), steel, verts=10); FLY.append(s_)
    f0 = F0("unscrew") + 4 + i * 6; p0 = MW_FLOOR + Vector((0.18 - 0.07 * i, -0.17, 0.12 + 0.02 * (i % 3)))
    for k in range(0, 14):
        t = k / 13.0; s_.location = p0 + Vector((0.06 * t * (1 if i % 2 else -1), -0.25 * t, 0.25 * t - 0.4 * t * t))
        s_.rotation_euler = (k * 0.9, k * 0.6, 0); s_.keyframe_insert("location", frame=f0 + k); s_.keyframe_insert("rotation_euler", frame=f0 + k)
    key(s_, f0 - 1, loc=tuple(p0)); interp(s_, "LINEAR")
    vis(s_, [(F0("unscrew"), F1("unscrew"))])
# pile: polda qismlar uyumi, birin-ketin paydo bo'ladi
PILE_C = MW_FLOOR + Vector((0.6, -0.55, 0.0))
for i, o in enumerate(PILE):
    a = i * 2.4; r_ = 0.12 + 0.05 * (i % 4)
    o.location = PILE_C + Vector((r_ * math.cos(a), r_ * math.sin(a), 0.012 + 0.015 * (i // 4)))
    o.rotation_euler = (R(random.uniform(-20, 20)), R(random.uniform(-20, 20)), R(random.uniform(0, 360)))
    fa = F0("pile") + int(i * (F1("pile") - F0("pile") - 4) / len(PILE))
    o.scale = o.scale; s0 = tuple(o.scale)
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=fa - 1)
    o.scale = s0; o.keyframe_insert("scale", frame=fa + 2)
    vis(o, rng("pile"))
# bag: tepadan qismlar tushadi (bagO ichidagi qismlar ketma-ket paydo bo'ladi)
inbag = [c for c in bagO.children if c.name.startswith(("mwp", "xp"))]
for i, o in enumerate(inbag):
    fa = F0("bag") + 2 + int(i * (F1("bag") - F0("bag") - 14) / max(1, len(inbag)))
    L0 = o.location.copy()
    o.location = L0 + Vector((0, 0, 0.55)); o.keyframe_insert("location", frame=fa)
    o.location = L0; o.keyframe_insert("location", frame=fa + 6)
    o.location = L0 + Vector((0, 0, 0.012)); o.keyframe_insert("location", frame=fa + 8)
    o.location = L0; o.keyframe_insert("location", frame=fa + 10)
    interp(o, "LINEAR")
    vis(o, [(fa, F1("bag")), (F0("open"), F1("parts"))], recursive=True)

# eshik: ilgakda ochiladi, dark gacha ochiq, exit da yopiq, owner da ochiladi
F_DOOR_OPEN = F0("owner") + 2
setkeys(hinge, "rotation_euler", [(1, (0, 0, 0)), (6, (0, 0, R(30))), (16, (0, 0, R(95))), (F0("exit"), (0, 0, 0)),
                                  (F_DOOR_OPEN, (0, 0, 0)), (F_DOOR_OPEN + 7, (0, 0, R(100)))], "LINEAR")
for fc in fcurves(hinge):
    for k in fc.keyframe_points:
        if int(k.co.x) in (16, F_DOOR_OPEN + 7): k.interpolation = "CONSTANT"
        if int(k.co.x) == F0("exit"): k.interpolation = "CONSTANT"
# soat: 1 soat timelapse
CK0, CK1 = F0("clock"), F1("clock")
setkeys(hand_m, "rotation_euler", [(1, (0, 0, R(-60))), (CK0, (0, 0, R(-60))), (CK1, (0, 0, R(-60 - 360 * 1.1)))], "LINEAR")
setkeys(hand_h, "rotation_euler", [(1, (0, 0, R(-75))), (CK0, (0, 0, R(-75))), (CK1, (0, 0, R(-75 - 33)))], "LINEAR")

# ======================================================================
# 6) KO'CHA (oxirgi kadr): yo'l, trotuar, uylar, chiroqlar
# ======================================================================
st = empty("street", tuple(STREET))
plane("road", (7, 60), (3.8, 0, 0.0), asph, parent=st)
box("sidewalk", (2.6, 60, 0.14), (-0.9, 0, 0.07), paving, parent=st)
box("curb", (0.2, 60, 0.16), (0.45, 0, 0.08), mat("curb", (0.5, 0.5, 0.48), 0.8), parent=st)
for i, y in enumerate(range(-24, 26, 8)):
    hb = box(f"st_house{i}", (5.0, 6.5, 3.2 + (i % 3) * 0.8), (-5.5, y, 1.6 + (i % 3) * 0.4), outwall, parent=st)
    for j in range(2):
        box(f"st_win{i}{j}", (0.05, 1.0, 1.1), (-2.98, y - 1.5 + 3 * j, 1.5), winlit if (i + j) % 3 else black, parent=st)
for i, y in enumerate(range(-20, 24, 10)):
    cyl(f"pole{i}", 0.05, 4.2, (0.7, y, 2.1), black, parent=st, verts=12)
    box(f"pole_arm{i}", (0.8, 0.06, 0.06), (1.05, y, 4.15), black, parent=st)
    box(f"pole_lamp{i}", (0.35, 0.18, 0.06), (1.4, y, 4.1), porch_m, parent=st)

# ======================================================================
# 7) KAMERALAR
# ======================================================================
def cam_path(name, keys, tgt, lens, fstop=None, focus=None, lin=False, tgt_keys=None):
    t_ = tgt if tgt is not None else tgt_path(name + "_t", tgt_keys)
    c = shot_cam(name, keys[0][1], t_, lens, fstop=fstop, focus=focus, clip=0.01)
    path(c, keys, lin=lin)
    return c
def tgt_at(name, p): return empty(name, tuple(p))
TVC = Vector((TV_HOME[0], TV_HOME[1] - 0.02, TV_HOME[2] + TV_H / 2))
f0, f1 = S["hook"]
c = cam_path("hook", [(f0, (DOOR_X + 0.55, 3.1, 0.14)), (f1, (DOOR_X + 0.42, 2.65, 0.2))], None, 14, fstop=2.8,
             tgt_keys=[(f0, (DOOR_X, 0.0, 1.0)), (f1, (DOOR_X, 0.5, 0.9))])
lens_keys(c, [(f0, 14), (19, 14), (25, 24), (f1, 26)]); shake(c, 19, 34, 0.025, seed=1)
f0, f1 = S["tv"]
c = cam_path("tv", [(f0, (TPOS.x - 0.75, TPOS.y - 1.25, 1.6)), (f1, (TPOS.x - 0.6, TPOS.y - 0.45, 1.45))], None, 22, fstop=4.0,
             tgt_keys=[(f0, TVC + Vector((-0.6, 0, 0.1))), (f1, TVC)])
f0, f1 = S["greed"]
c = orbit_cam("greed", f0, f1, (TPOS.x, TPOS.y, 0), 0.75, 0.55, 60, 100, 1.3, 1.35, 50, tface, fstop=2.0)
f0, f1 = S["big"]
c = cam_path("big", [(f0, (BIGP.x + 0.95, BIGP.y - 0.55, 0.22)), (f1, (BIGP.x + 1.15, BIGP.y - 1.35, 0.3))], None, 14, fstop=5.6,
             tgt_keys=[(f0, BIGP + Vector((0.0, 0.5, 0.7))), (f1, BIGP + Vector((0.1, 0.45, 0.75)))])
f0, f1 = S["window"]
c = cam_path("window", [(f0, (0.9, 0.75, 0.35)), (f1, (1.35, 0.95, 0.4))], None, 16, fstop=5.6,
             tgt_keys=[(f0, (2.0, 2.5, 1.2)), (f1, (2.6, 2.5, 1.35))])
f0, f1 = S["nofit1"]
c = cam_path("nofit1", [(f0, (HIT1_X - 1.1, WIN_Y - 0.75, 1.75)), (f1, (HIT1_X - 0.85, WIN_Y - 0.65, 1.7))], None, 20, fstop=4.0,
             tgt_keys=[(f0, (LX1, WIN_Y, 1.35)), (f1, (LX1, WIN_Y, 1.35))])
shake(c, F_HIT1, F_HIT1 + 12, 0.03, seed=3)
f0, f1 = S["door"]
c = cam_path("door", [(f0, (DOOR_X + 1.0, 4.1, 1.65)), (f1, (DOOR_X + 0.75, 2.0, 1.55))], None, 20, fstop=4.0,
             tgt_keys=[(f0, (DOOR_X, 1.2, 1.1)), (f1, (DOOR_X, 0.0, 1.1))])
f0, f1 = S["nofit2"]
c = cam_path("nofit2", [(f0, (DOOR_X + 0.35, -1.6, 0.25)), (f1, (DOOR_X + 0.3, -1.3, 0.3))], None, 16, fstop=5.6,
             tgt_keys=[(f0, (DOOR_X, 0.0, 1.1)), (f1, (DOOR_X, 0.0, 1.15))])
shake(c, F_HIT2, F_HIT2 + 12, 0.035, seed=4)
f0, f1 = S["idea"]
F_IDEA = T(14.75)
c = orbit_cam("idea", f0, f1, (IDP.x, IDP.y, 0), 0.9, 0.7, -110, -70, 1.5, 1.55, 45, tface, fstop=2.0)
lens_keys(c, [(f0, 45), (F_IDEA, 45), (F_IDEA + 5, 70), (f1, 75)])
f0, f1 = S["tool"]
sc_t = empty("scr_tip", (0, 0, 0), scr)
c = cam_path("tool", [(f0, (IDP.x - 0.35, IDP.y - 0.55, 1.05)), (f1, (IDP.x - 0.25, IDP.y - 0.45, 1.15))], sc_t, 60, fstop=2.0)
f0, f1 = S["dark"]
c = cam_path("dark", [(f0, (DK0.x + 1.3, DK0.y - 0.25, 0.5)), (f1, (DK0.x - 0.7, DK0.y - 0.15, 0.7))], None, 20, fstop=4.0,
             tgt_keys=[(f0, (DK0.x - 1.0, DK0.y, 1.0)), (f1, (DK0.x - 3.0, DK0.y + 0.2, 0.9))])
f0, f1 = S["clock"]
c = cam_path("clock", [(f0, (-3.95, 1.35, 1.55)), (f1, (-3.55, 1.85, 1.75))], clk, 32, fstop=2.8)
f0, f1 = S["unscrew"]
c = orbit_cam("unscrew", f0, f1, tuple(MW_FLOOR + Vector((0, -0.15, 0))), 0.7, 0.55, 200, 235, 0.85, 0.75, 30,
              tgt_at("unscrew_t", MW_FLOOR + Vector((0.0, -0.12, 0.32))), fstop=2.8)
shake(c, f0, f1, 0.008, seed=5, decay=False)
f0, f1 = S["pile"]
c = orbit_cam("pile", f0, f1, tuple(PILE_C), 0.35, 0.3, 0, 70, 1.6, 1.3, 30, tgt_at("pile_t", PILE_C), fstop=4.0)
f0, f1 = S["bag"]
c = cam_path("bag", [(f0, BAG_K + Vector((0.02, -0.25, 1.4))), (f1, BAG_K + Vector((0.0, -0.08, 0.75)))], tgt_at("bag_t", BAG_K + Vector((0, 0, 0.1))), 28, fstop=4.0)
f0, f1 = S["exit"]
c = cam_path("exit", [(f0, (DOOR_X + 0.25, EX1.y - 0.6, 0.45)), (f1, (DOOR_X + 0.2, EX1.y - 0.75, 0.5))], None, 18, fstop=4.0,
             tgt_keys=[(f0, (DOOR_X, EX1.y + 1.7, 1.1)), (f1, (DOOR_X, EX1.y + 0.3, 1.2))])
f0, f1 = S["owner"]
c = cam_path("owner", [(f0, (DOOR_X + 0.35, -1.25, 1.62)), (f1, (DOOR_X + 0.3, -1.15, 1.6))], tface, 24, fstop=2.8)
lens_keys(c, [(f0, 24), (F_LIGHT, 24), (F_LIGHT + 5, 55), (f1, 60)]); shake(c, F_LIGHT, F_LIGHT + 10, 0.02, seed=6)
f0, f1 = S["drop"]
c = cam_path("drop", [(f0, (DOOR_X + 0.75, 0.65, 0.09)), (f1, (DOOR_X + 0.6, 0.75, 0.1))], tgt_at("drop_t", BAG_FLOOR + Vector((0, 0, 0.18))), 18, fstop=2.8)
shake(c, FB, FB + 10, 0.02, seed=7)
f0, f1 = S["flee"]
c = cam_path("flee", [(f0, (DOOR_X + 1.3, 3.3, 0.45)), (f1, (DOOR_X + 1.0, 3.6, 0.5))], tgt_path("flee_t", [(f0, (DOOR_X, 1.0, 1.1)), (f1, (DOOR_X, 3.2, 1.0))]), 14, fstop=5.6)
f0, f1 = S["open"]
c = cam_path("open", [(f0, BAG_FLOOR + Vector((0.0, -0.06, 0.3))), (f1, BAG_FLOOR + Vector((0.02, -0.04, 0.34)))], oface, 16, fstop=5.6)
f0, f1 = S["nottv"]
c = cam_path("nottv", [(f0, (TVP.x - 0.3, 1.2, 1.1)), (f0 + 10, (TVP.x - 0.1, 3.4, 1.0)), (f1, (TVP.x, 3.75, 0.98))], tgt_at("tv_t", TVC), 24, fstop=4.0)
lens_keys(c, [(f0, 18), (f0 + 10, 30), (f1, 32)])
f0, f1 = S["parts"]
BP = BAG_FLOOR
c = cam_path("parts", [(f0, BP + Vector((-0.25, -0.42, 1.2))), (f1, BP + Vector((0.06, -0.3, 1.0))) ], None, 30, fstop=5.6,
             tgt_keys=[(f0, BP + Vector((-0.05, 0.0, 0.14))), (f1, BP + Vector((0.05, 0.0, 0.14)))])
c.data.dof.aperture_fstop = 9.0
f0, f1 = S["empty"]
c = cam_path("empty", [(f0, MW_COUNTER + Vector((-0.25, -0.75, 0.95))), (f1, MW_COUNTER + Vector((-0.08, -0.45, 0.65)))], tgt_at("empty_t", MW_COUNTER + Vector((0, 0, 0.1))), 28, fstop=4.0)
f0, f1 = S["flashback"]
c = cam_path("flashback", [(f0, MW_FLOOR + Vector((0.95, 0.05, 0.38))), (f1, MW_FLOOR + Vector((1.12, -1.55, 1.15)))], tgt_path("fb_t", [(f0, MW_FLOOR + Vector((0, 0, 0.18))), (f1, MW_FLOOR + Vector((-0.1, -0.35, 0.45)))]), 24, fstop=4.0)
f0, f1 = S["street"]
c = shot_cam("street", (0, 0, 0), tface, 20, fstop=4.0, clip=0.01)
for f in range(f0, f1 + 1, 3):
    sc.frame_set(f); hp = bwp(thief, "Hips")
    key(c, f, loc=(hp.x + 0.55, hp.y - 2.2, 0.6))
interp(c, "LINEAR", "location")
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 8) YORUG'LIK: tun (oy, ko'k), peshona chirog'i, uy chirog'i (owner dan keyin)
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
WN = w.node_tree.nodes; WL = w.node_tree.links
env = WN.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mx = WN.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
WL.new(env.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.25, 0.4, 1.0, 1)
bg = WN["Background"]; WL.new(mx.outputs[2], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.08
moon = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN")); sc.collection.objects.link(moon)
moon.data.energy = 0.35; moon.data.color = (0.55, 0.68, 1.0); moon.data.angle = R(2); moon.rotation_euler = (R(55), 0, R(65))
# oy nuri derazadan
area("moon_win", (LX1 + 1.2, WIN_Y, 2.2), 1.2, (0.55, 0.7, 1.0), lights_for(ALL, 70.0), target=tgt_at("mw_t", (0.5, 2.6, 0.0)))
# xona umumiy xira to'ldiruvchi (qorong'ida ham shakllar ko'rinsin)
REALDARK = rng("hook", "tv", "greed", "big", "window", "nofit1", "door", "nofit2", "idea", "tool", "dark", "exit")
area("dark_fill", (0.5, 2.5, 2.55), 4.0, (0.45, 0.58, 1.0), lights_for(REALDARK + [(F0("owner"), F_LIGHT - 1)], 70.0))
area("kit_fill", (-5.3, 2.5, 2.55), 4.0, (0.45, 0.58, 1.0), lights_for(rng("dark", "clock", "unscrew", "pile", "bag", "flashback"), 45.0))
# ilgak: ochiq eshikdan ko'cha (ko'k) + ayvon chirog'i
point("porch", (DOOR_X + 0.75, -0.45, 2.1), 0.08, (1.0, 0.75, 0.45), lights_for(ALL, 60.0))
# uy chirog'i yonadi (owner, F_LIGHT) va qoladi
lr = area("ceiling_lr", (0.5, 2.6, H - 0.25), 1.6, (1.0, 0.85, 0.68), [(1, 0), (F_LIGHT, 0), (F_LIGHT + 1, 180), (F_LIGHT + 3, 120), (F_LIGHT + 5, 600), (F0("parts"), 600), (F0("empty"), 0), (F0("flashback"), 0)])
interp(lr.data, "LINEAR")
area("ceiling_kit", (-5.3, 3.4, H - 0.25), 1.6, (1.0, 0.87, 0.72), lights_for(rng("empty"), 450.0))
bk = bulb_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.0), (F_LIGHT, 0.0), (F_LIGHT + 1, 12.0), (F0("empty"), 0.0)): bk.default_value = v; bk.keyframe_insert("default_value", frame=f)
# yuz yaqin planlari uchun yumshoq to'ldiruvchi
area("greed_fill", (TPOS.x + 0.2, TPOS.y + 0.9, 1.6), 0.6, (1.0, 0.85, 0.7), lights_for(rng("greed"), 6.0), target=tface)
area("idea_rim", (IDP.x + 0.6, IDP.y + 0.8, 2.0), 0.8, (0.5, 0.65, 1.0), lights_for(rng("idea", "tool"), 25.0), target=tface)
ip = area("idea_ping", (IDP.x - 0.2, IDP.y - 0.7, 1.9), 0.5, (1.0, 0.75, 0.35), [(1, 0), (F_IDEA, 0), (F_IDEA + 1, 60), (F_IDEA + 8, 16), (F1("idea"), 16), (F1("idea") + 1, 0)], target=tface)
interp(ip.data, "LINEAR")
area("tool_fill", (IDP.x - 0.6, IDP.y - 0.9, 1.4), 0.4, (1.0, 0.9, 0.8), lights_for(rng("tool"), 8.0), target=sc_t)
# ichi qorong'i bo'lganda kesim yorug'i: bag/parts/open
area("bag_top", BAG_K + Vector((0.1, -0.3, 1.2)), 0.5, (1.0, 0.92, 0.8), lights_for(rng("bag"), 18.0), target=tgt_at("bagk_t", BAG_K))
area("parts_key", BAG_FLOOR + Vector((-0.4, -0.5, 1.0)), 0.6, (1.0, 0.95, 0.88), lights_for(rng("parts"), 30.0), target=tgt_at("parts_t", BAG_FLOOR))
# soat kadrida devordagi o'g'ri soyasi/nuri (miltillaydi)
fl = area("clock_flicker", tuple(MW_FLOOR + Vector((-0.6, 0.1, 0.45))), 0.15, (1.0, 0.9, 0.75), [(1, 0)], target=clk)
for f in range(F0("clock"), F1("clock") + 2, 3):
    fl.data.energy = 0 if f > F1("clock") else random.uniform(6, 22); fl.data.keyframe_insert("energy", frame=f)
# qora televizor qorong'ida ko'rinsin: orqa/yon yorug'lik
area("tv_rim_big", tuple(BIGP + Vector((-1.0, 1.25, 2.3))), 0.8, (0.6, 0.75, 1.0), lights_for(rng("big"), 90.0), target=tgt_at("trb_t", BIGP + Vector((0, 0.6, 0.6))))
area("tv_rim_win", (1.6, 1.0, 2.5), 0.8, (0.65, 0.78, 1.0), lights_for(rng("window", "nofit1"), 70.0), target=tgt_at("trw_t", (2.7, 2.5, 1.2)))
area("tv_rim_door", (DOOR_X + 1.3, 1.6, 2.5), 0.8, (0.65, 0.78, 1.0), lights_for(rng("door", "nofit2"), 90.0), target=tgt_at("trd_t", (DOOR_X, 0.7, 1.4)))
area("tv_out_door", (DOOR_X - 0.9, -1.4, 2.2), 0.6, (1.0, 0.8, 0.6), lights_for(rng("nofit2"), 60.0), target=tgt_at("tod_t", (DOOR_X, 0.1, 1.4)))
# ko'cha chiroqlari
for i, y in enumerate(range(-20, 24, 10)):
    point(f"st_light{i}", tuple(STREET + Vector((1.4, y, 3.9))), 0.2, (1.0, 0.7, 0.4), lights_for(rng("street"), 900.0), const=True)
# peshona chirog'i: TV kadrida nur TV ga qaratiladi (TRACK_TO influence)
tvt = tgt_path("tv_aim", [(F0("tv"), TVC + Vector((-1.6, 0.1, 0.4))), (F0("tv") + 26, TVC + Vector((0.05, 0, 0))), (F1("tv"), TVC)])
tc_ = lamp.constraints.new("TRACK_TO"); tc_.target = tvt; tc_.track_axis = "TRACK_Z"; tc_.up_axis = "UP_Y"
for f, v in ((1, 0.0), (F0("tv"), 1.0), (F1("tv") + 1, 0.0)): tc_.influence = v; tc_.keyframe_insert("influence", frame=f)
interp(lamp, "CONSTANT")
# owner (chiroq yongach) va keyin: peshona chirog'i o'chmaydi, lekin konus nuri xiralashadi
for f, v in ((1, 0.04), (F0("tv"), 0.03), (F1("tv") + 1, 0.15), (F0("exit"), 0.04), (F_LIGHT, 0.04), (F_LIGHT + 1, 0.03), (F0("flashback"), 0.15)): val_key(beam_m, "a", f, v)
for f, v in ((1, 150.0), (F0("greed"), 35.0), (F1("greed") + 1, 150.0)): spot.data.energy = v; spot.data.keyframe_insert("energy", frame=f)
interp(spot.data, "CONSTANT")

# tovush effektlari uchun voqea kadrlari
if os.environ.get("EVENTS"):
    import json
    json.dump({"shots": SHOTS, "hit1": F_HIT1, "hit2": F_HIT2, "idea": F_IDEA, "light": F_LIGHT, "drop": FB, "door_open": F_DOOR_OPEN,
               "clock": [F0("clock"), F1("clock")], "unscrew": [F0("unscrew"), F1("unscrew")], "pile": [F0("pile"), F1("pile")],
               "bag": [F0("bag"), F1("bag")], "end": END}, open(os.environ["EVENTS"], "w"))

# ======================================================================
# 9) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT if (OUT := os.environ.get("OUT", "/tmp/claude-0/frames_o/")) else ""
r.use_persistent_data = os.environ.get("PERSIST", "0") == "1"
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("DBG"):
    exec(open(os.environ["DBG"]).read())
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
