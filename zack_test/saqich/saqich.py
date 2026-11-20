# "Saqich chaynash" (jag' bo'g'imi yeyilishi, jag' chiqib ketishi, gastrit) — Zack D. Films uslubida 35.8 s video (860 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py, telefon/telefon.py (rentgen bosh, bosh fazosidagi kameralar, chaqnash kartochkalari),
# burish/parts.py (miya, naycha, impuls materiali), lib.py (yordamchilar). Kadr rejasi: STORYBOARD.md.
# Assetlar: zack_test/tools/get_saqich.sh, so'ng: /tmp/claude-0/bvenv/bin/python -I zack_test/saqich/skull_split.py
# Render: OUT=/tmp/claude-0/frames_s/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/saqich/saqich.py --render
# Sinov:  FRAMES=20,60,100 PCT=30 OUT=/tmp/claude-0/test/ ... --render   |   Bo'lak: RANGE=a,b
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ZT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ZT)
from lib import *                     # sahnani tozalaydi; bpy, math, random, Vector, mc, sc, R, PH, BK, yordamchilar
import bmesh
from mathutils import Quaternion
sys.path.insert(0, os.path.join(ZT, "burish"))
import parts as PT
PT.VIEWPORT_OFF = True
OUT = os.environ.get("OUT", "/tmp/claude-0/frames_s/")
random.seed(7)
END = 860
sc.frame_start, sc.frame_end = 1, END
def V(*a): return Vector(a)
def ckey(idb, path=None): interp(idb, "CONSTANT", path)

# ---------------- kadrlar (ovoz so'zlariga bog'langan: words.json, kadr = t * 24 + 1) ----------------
SHOTS = [(1, "hook"), (46, "wide"), (109, "xbody"), (183, "xjaw"), (245, "muscle"), (313, "face"), (372, "ear"),
         (427, "disc"), (474, "wear"), (521, "yawn"), (571, "pop"), (613, "stuck"), (659, "chew2"), (698, "brain"),
         (753, "acid"), (808, "ulcer")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
F_EARX = 401        # "jag' suyagi" (16.5 s) — quloq kadri rentgenga o'tadi
F_CHID = 297        # "chidaydi" (12.32 s)
F_YAWN = 553        # "esnaganingizda" (23.0 s) — og'iz eng katta
F_QIRS = 592        # "qirs" (24.62 s) — jag' chiqib ketadi
F_GAST = 828        # "gastrit" (34.46 s)
ROOMN = ("hook", "wide", "face", "ear", "yawn", "stuck", "chew2")
XRN = ("xbody", "xjaw", "muscle", "pop", "brain")
ROOM = rng(*ROOMN); ROOM_REAL = [r for r in ROOM if r != S["ear"]] + [(S["ear"][0], F_EARX - 1)]
XR = rng(*XRN) + [(F_EARX, S["ear"][1])]
TMJR = rng("disc", "wear"); STOR = rng("acid", "ulcer")

# ======================================================================
# 1) MEHMONXONA (kunduz): divan, kofe stoli, gul, rasm, javon, devor soati, deraza (HDRI)
# ======================================================================
room_objs = []
def R_(o): room_objs.append(o); return o
floor_m = pbr("floor", "laminate_floor_02", 0.5)
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.95, 0.9, 0.82))
X0, X1, Y0, Y1, HZ_ = -3.0, 3.0, -3.2, 2.0, 2.8
R_(plane("floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
R_(box("ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ_ + 0.025), mat("ceil_m", (0.92, 0.92, 0.9), 0.8)))
R_(box("wall_B", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y1 + 0.05, HZ_ / 2), wall_m))
R_(box("wall_R", (0.1, Y1 - Y0, HZ_), (X1 + 0.05, (Y0 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_F", (X1 - X0, 0.1, HZ_), ((X0 + X1) / 2, Y0 - 0.05, HZ_ / 2), wall_m))
# chap devorda katta deraza (quyosh shu tomondan)
WY0, WY1, WZ0, WZ1 = -1.2, 1.1, 0.75, 2.35
R_(box("wall_L1", (0.1, WY0 - Y0, HZ_), (X0 - 0.05, (Y0 + WY0) / 2, HZ_ / 2), wall_m))
R_(box("wall_L2", (0.1, Y1 - WY1, HZ_), (X0 - 0.05, (WY1 + Y1) / 2, HZ_ / 2), wall_m))
R_(box("wall_L3", (0.1, WY1 - WY0, WZ0), (X0 - 0.05, (WY0 + WY1) / 2, WZ0 / 2), wall_m))
R_(box("wall_L4", (0.1, WY1 - WY0, HZ_ - WZ1), (X0 - 0.05, (WY0 + WY1) / 2, (WZ1 + HZ_) / 2), wall_m))
frame_m = mat("win_frame", (0.93, 0.93, 0.9), 0.4)
WC = V(X0 - 0.05, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2); WW, WH = WY1 - WY0, WZ1 - WZ0
for nm, sz, off in (("wf_t", (0.12, WW + 0.04, 0.05), (0, 0, WH / 2)), ("wf_b", (0.22, WW + 0.04, 0.06), (0.05, 0, -WH / 2)),
                    ("wf_l", (0.12, 0.05, WH), (0, -WW / 2, 0)), ("wf_r", (0.12, 0.05, WH), (0, WW / 2, 0)),
                    ("wf_m", (0.08, 0.04, WH), (0, 0, 0)), ("wf_h", (0.08, WW, 0.04), (0, 0, 0.2))):
    R_(box(nm, sz, tuple(WC + Vector(off)), frame_m))
cur_m = mat("curtain_m", (0.85, 0.8, 0.7), 0.9, sss=0.15)
for y in (WY0 - 0.28, WY1 + 0.28):
    R_(box("curtain", (0.06, 0.5, 2.5), (X0 + 0.1, y, 1.3), cur_m))
R_(box("baseboard", (X1 - X0, 0.03, 0.1), ((X0 + X1) / 2, Y1 - 0.015, 0.05), frame_m))
R_(box("baseboard2", (0.03, Y1 - Y0, 0.1), (X1 - 0.015, (Y0 + Y1) / 2, 0.05), frame_m))
R_(plane("out_ground", (40, 40), (X0 - 20, 0, -0.4), mat("out_grass", (0.12, 0.2, 0.06), 0.9)))
rw = random.Random(3)
for i in range(6):                                          # deraza ortidagi daraxtlar (yashil sharlar)
    x = X0 - rw.uniform(5, 12); y = rw.uniform(-6, 6); h = rw.uniform(2.5, 5)
    R_(cyl(f"trunk{i}", 0.12, h, (x, y, h / 2 - 0.4), mat("trunk", (0.2, 0.13, 0.08), 0.9)))
    R_(sphere(f"crown{i}", rw.uniform(1.4, 2.2), (x, y, h + 0.6), mat("crown", (0.1, 0.25, 0.06), 0.8), sub=3))
def gltf(path, loc, rot_z=0.0, scale=1.0):
    e = empty(os.path.basename(path).split(".")[0] + "_grp", loc); import_gltf(path, e)
    e.rotation_euler.z = R(rot_z); e.scale = (scale,) * 3 if not isinstance(scale, tuple) else scale
    return e
SOFA = V(0.0, 1.42, 0.0); SOFA_S = 1.45                  # Mixamo o'tirish harakati 0.45 m o'rindiqqa mo'ljallangan
R_(gltf(PH + "Sofa_01/Sofa_01.gltf", tuple(SOFA), 0, SOFA_S))
R_(gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (0.0, 0.25, 0), 0, 1.0))
R_(gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.4, 1.55, 0), 30, 1.3))
R_(gltf(PH + "potted_plant_01/potted_plant_01.gltf", (2.45, 1.5, 0), -60, 1.0))
R_(gltf(PH + "Shelf_01/Shelf_01.gltf", (X1 - 0.02, -0.6, 0), -90, 1.0))
R_(gltf(PH + "book_encyclopedia_set_01/book_encyclopedia_set_01.gltf", (X1 - 0.15, -0.4, 1.03), -90, 1.0))
art_m = bpy.data.materials.new("art"); art_m.use_nodes = True
_an = art_m.node_tree.nodes; _al = art_m.node_tree.links; _atc = _an.new("ShaderNodeTexCoord"); _anz = _an.new("ShaderNodeTexNoise")
_anz.inputs["Scale"].default_value = 2.2; _anz.inputs["Detail"].default_value = 2; _al.new(_atc.outputs["Object"], _anz.inputs["Vector"])
_ar = _an.new("ShaderNodeValToRGB"); _al.new(_anz.outputs["Fac"], _ar.inputs[0]); _ae = _ar.color_ramp.elements
_ae[0].position, _ae[0].color = 0.35, (0.05, 0.25, 0.45, 1); _ae[1].position, _ae[1].color = 0.65, (0.95, 0.6, 0.25, 1)
_e2 = _ae.new(0.5); _e2.color = (0.85, 0.85, 0.75, 1); _al.new(_ar.outputs[0], _an["Principled BSDF"].inputs["Base Color"])
R_(box("pic_frame", (1.3, 0.04, 0.85), (0.0, Y1 - 0.02, 1.75), mat("pic_frame_m", (0.12, 0.08, 0.05), 0.4), bevel=0.01))
R_(box("pic_art", (1.18, 0.01, 0.73), (0.0, Y1 - 0.045, 1.75), art_m))
rug_m = mat("rug", (0.62, 0.36, 0.26), 0.95)
_rn = rug_m.node_tree.nodes; _rl = rug_m.node_tree.links; _w = _rn.new("ShaderNodeTexWave"); _w.inputs["Scale"].default_value = 6.0
_mx = _rn.new("ShaderNodeMix"); _mx.data_type = "RGBA"; _mx.inputs[6].default_value = (0.62, 0.36, 0.26, 1); _mx.inputs[7].default_value = (0.85, 0.75, 0.6, 1)
_rl.new(P.math_n(_rn, _rl, "GREATER_THAN", _w.outputs["Fac"], 0.8), _mx.inputs["Factor"]); _rl.new(_mx.outputs[2], _rn["Principled BSDF"].inputs["Base Color"])
R_(box("rug", (2.6, 1.9, 0.012), (0.0, 0.4, 0.006), rug_m))
# devor soati (orqa devorda, o'ngda): "ikki-uch soat" da strelkalar tez aylanadi
CLK = V(1.45, Y1 - 0.02, 1.85)
clk = R_(empty("clock", tuple(CLK))); clk.rotation_euler = (R(90), 0, 0)       # mahalliy +Z -> dunyo -Y (xonaga qaraydi)
cyl("clk_body", 0.2, 0.04, (0, 0, 0.02), mat("clk_body_m", (0.08, 0.08, 0.09), 0.3), parent=clk, verts=48)
cyl("clk_face", 0.18, 0.005, (0, 0, 0.042), mat("clk_face_m", (0.95, 0.94, 0.9), 0.5), parent=clk, verts=48)
tick_m = mat("tick", (0.05, 0.05, 0.05), 0.5)
for k in range(12):
    a = 2 * math.pi * k / 12
    box(f"tick{k}", (0.009, 0.03 if k % 3 else 0.042, 0.004), (0.15 * math.sin(a), 0.15 * math.cos(a), 0.046), tick_m, rot=(0, 0, -math.degrees(a)), parent=clk)
hand_h = empty("hand_h", (0, 0, 0.048), clk); hand_m = empty("hand_m", (0, 0, 0.05), clk)
box("hh", (0.014, 0.09, 0.003), (0, 0.038, 0), tick_m, parent=hand_h)
box("hm", (0.009, 0.13, 0.003), (0, 0.06, 0), mat("hand_red", (0.7, 0.05, 0.03), 0.4), parent=hand_m)
W0_, W1_ = S["wide"]
def clock_keys(pairs):
    for f, mins in pairs:
        hand_m.rotation_euler = (0, 0, R(-mins / 60 * 360)); hand_m.keyframe_insert("rotation_euler", frame=f)
        hand_h.rotation_euler = (0, 0, R(-(2 + mins / 60) / 12 * 360)); hand_h.keyframe_insert("rotation_euler", frame=f)
clock_keys([(1, 5), (W0_, 5), (W1_, 5 + 165), (END, 5 + 175)])                 # 14:05 -> 16:50 (timelapse)
interp(hand_m, "LINEAR"); interp(hand_h, "LINEAR")
for o in room_objs: vis(o, ROOM)

# ======================================================================
# 2) MEGAN: divanda chaynaydi -> derazа oldida esnaydi -> vahima -> yana divan. Jag' uchun yangi "Jaw" bone.
# ======================================================================
def soften2(meshes, rough=0.48):
    soften(meshes)
    for o in meshes:
        for m in o.data.materials:
            if m and m.use_nodes and "hair" not in m.name.lower():
                for n in m.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED": n.inputs["Roughness"].default_value = rough
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften2(mmeshes)
BODY = next(o for o in mmeshes if o.name == "meg_Body")
# --- bosh suyagi (pastki jag' ajratilgan, skull_split.py) va jag' bo'g'imi nuqtasi (bosh fazosida) ---
SKULL_LOC, SKULL_ROT, SKULL_S = V(0, -0.012, 0.034), (R(-90), 0, 0), 0.8          # telefon.py dagi joylashuv
SKM = Matrix.LocRotScale(SKULL_LOC, Euler(SKULL_ROT), V(SKULL_S, SKULL_S, SKULL_S))
with bpy.data.libraries.load(BK + "skull_split.blend") as (src, dst):
    dst.objects = ["cranium", "mandible", "TMJ"]
cran, mand, tmj_e = dst.objects
TMJ_H = SKM @ tmj_e.location                       # bo'g'im (pivot) bosh fazosida: X chap, Y tepa, Z old
print("TMJ head-space", tuple(round(x, 4) for x in TMJ_H))
# --- Jaw bone: Head'ning bolasi, bosh bilan bir xil yo'nalishda, boshi TMJ da ---
bpy.context.view_layer.objects.active = meg; meg.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = meg.data.edit_bones; hb_ = eb["mixamorig:Head"]
ASC = meg.matrix_world.to_scale()[0]               # armatura masshtabi (0.01: bone'lar sm da)
HB_M = hb_.matrix.copy()                           # bone fazosi -> armatura fazosi (masshtabsiz)
jb = eb.new("mixamorig:Jaw"); jh = HB_M @ (TMJ_H / ASC)
jb.head = jh; jb.tail = jh + (hb_.tail - hb_.head).normalized() * 5.0; jb.roll = hb_.roll
jb.parent = hb_; jb.use_deform = True
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()
# --- og'irliklar: lab chizig'idan pastdagi yuz, iyak, og'iz ichi pastki yarmi -> Jaw ---
HREST = (meg.matrix_world @ meg.data.bones["mixamorig:Head"].matrix_local).normalized(); HRI = HREST.inverted()
me = BODY.data; MW = BODY.matrix_world
PH_ = [HRI @ (MW @ v.co) for v in me.vertices]
nbr = [[] for _ in me.vertices]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
gi = {g.name: g.index for g in BODY.vertex_groups}
HG, NG = BODY.vertex_groups["mixamorig:Head"], BODY.vertex_groups["mixamorig:Neck"]
JG = BODY.vertex_groups.new(name="mixamorig:Jaw")
from mathutils import kdtree
def sstep(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
# lab choki: ustma-ust turgan juft uchlar (yuqori lab / pastki lab). Har birining tomonini qo'shnilari aniqlaydi.
kd = kdtree.KDTree(len(PH_))
for i, p in enumerate(PH_): kd.insert(p, i)
kd.balance()
SEAM = {}                 # i -> True (pastki lab) / False (yuqori lab)
for i, p in enumerate(PH_):
    if not (abs(p.x) < 0.04 and 0.0 < p.y < 0.05 and p.z > 0.12): continue
    for (q, j, d) in kd.find_range(p, 7e-4):
        if j != i and j not in nbr[i] and nbr[i] and abs(PH_[j].y - p.y) < 4e-4:
            avg = sum((PH_[k] for k in nbr[i]), V(0, 0, 0)) / len(nbr[i]); SEAM[i] = avg.y < p.y
seam_pts = sorted((PH_[i].x, PH_[i].y) for i in SEAM)
XC = max(abs(x) for x, _ in seam_pts) if seam_pts else 0.024
print("SEAM verts", len(SEAM), "corner x", round(XC, 4), "y range", round(min(y for _, y in seam_pts), 4), round(max(y for _, y in seam_pts), 4), "lower", sum(SEAM.values()))
def seam_y(x):
    x = max(-XC, min(XC, x)); best = min(seam_pts, key=lambda a: abs(a[0] - x)); return best[1]
nj = 0; WMAP = {}
for v in me.vertices:
    gw = {g.group: g.weight for g in v.groups}
    hw, nw = gw.get(gi["mixamorig:Head"], 0.0), gw.get(gi["mixamorig:Neck"], 0.0)
    if hw + nw < 1e-4: continue
    p = PH_[v.index]
    out_ = max(0.0, abs(p.x) - XC)                                       # og'iz burchagidan tashqarida silliq o'tish
    yl = seam_y(p.x) + max(0.0, 0.135 - p.z) * 0.3 + out_ * 0.25
    if v.index in SEAM: wy = 1.0 if SEAM[v.index] else 0.0
    else:
        wid = 0.0006 + out_ * 0.4 + max(0.0, 0.13 - p.z) * 0.05
        wy = sstep((yl - p.y) / wid + 0.5)
    w = wy * sstep((p.z - 0.02) / 0.045) * sstep((p.y + 0.06) / 0.04)
    if w < 1e-3: continue
    w *= (hw + nw); JG.add([v.index], w, "REPLACE"); nj += 1; WMAP[v.index] = w
    k = 1 - w / (hw + nw)
    if hw: HG.add([v.index], hw * k, "REPLACE")
    if nw: NG.add([v.index], nw * k, "REPLACE")
print("JAW weighted verts", nj)
# og'iz ichi (lablar ortidagi xalta) — to'q qizil material
mouth_m = mat("mouth_in", (0.025, 0.004, 0.005), 1.0)
mouth_m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.0
BODY.data.materials.append(mouth_m); MI = len(BODY.data.materials) - 1
NRM = MW.to_3x3().inverted().transposed(); HR3 = HRI.to_3x3()
NH = [(HR3 @ (NRM @ v.normal)).normalized() for v in me.vertices]
seed = [i for i, p in enumerate(PH_) if abs(p.x) < 0.006 and 0.0 < p.y < 0.05 and 0.10 < p.z < 0.135]
inside = set(seed); stack = list(seed)
while stack:
    i = stack.pop()
    for j in nbr[i]:
        if j in inside: continue
        q = PH_[j]
        if q.z < 0.162 - 30 * q.x * q.x and -0.015 < q.y < 0.06 and abs(q.x) < 0.035 and NH[j].z < 0.45: inside.add(j); stack.append(j)
nm_ = 0
for pl in me.polygons:
    if all(i in inside for i in pl.vertices): pl.material_index = MI; nm_ += 1
# og'iz ochilganda cho'ziladigan yuzalar (bir uchi yuqorida, biri jag'da) — o'chiriladi: og'iz haqiqiy teshik bo'ladi
bm_ = bmesh.new(); bm_.from_mesh(me); bm_.faces.ensure_lookup_table()
kill = []
for f in bm_.faces:
    ws = [WMAP.get(v.index, 0.0) for v in f.verts]; c_ = sum((PH_[v.index] for v in f.verts), V(0, 0, 0)) / len(f.verts)
    if max(ws) - min(ws) > 0.45 and abs(c_.x) < XC * 0.92 and -0.01 < c_.y < 0.05 and c_.z > 0.085: kill.append(f)
for f in kill: f.material_index = MI                 # cho'zilgan yuzalar qora -> og'iz teshigidek ko'rinadi
bm_.to_mesh(me); bm_.free(); me.update()
print("MOUTH faces", nm_, "stretch faces -> dark", len(kill))

def strip2(arm, act, start, repeat=1.0, speed=1.0, src=None):
    s = mc.add_strip(arm, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = 0; s.blend_out = 0
    return s
SIT = A_("Sitting_Idle_5.fbx", inplace=False); YAWN = A_("Yawn.fbx", inplace=False); TERR = A_("Terrified.fbx", inplace=False)
def sit_strip(a, b):
    n = b - a + 1; L_ = (SIT.frame_range[1] - SIT.frame_range[0]) * 0.8
    strip2(meg, SIT, a, repeat=n / L_)
sit_strip(1, 520)
strip2(meg, YAWN, 521, src=(80, 80 + (612 - 521) / 0.8))
strip2(meg, TERR, 613, src=(21, 21 + (658 - 613) / 0.8))
sit_strip(659, END)
SITP = SOFA + V(0.0, 0.02, 0.0); STANDP = V(1.15, -0.55, 0.0)
place(mroot, 1, tuple(SITP), 0); place(mroot, 521, tuple(STANDP), 0); place(mroot, 659, tuple(SITP), 0)
ckey(mroot)
# --- jaw kalitlari: chaynash (X: ochilish, Z: yon tomonga ishqalanish), esnash, chiqib ketish ---
pbJ = meg.pose.bones["mixamorig:Jaw"]; pbJ.rotation_mode = "XYZ"
JK = {}
def jkey(f, op, side=0.0, fwd=0.0, down=0.0):
    JK[f] = (op, side, fwd, down)
def chew(a, b, per=17, amp=7.5, ph=0):
    f = a
    while f < b:
        k = (f - a + ph) % per; t = k / per
        jkey(f, amp * (0.5 - 0.5 * math.cos(2 * math.pi * t)), 1.6 * math.sin(2 * math.pi * t))
        f += 3
H0_, H1_ = S["hook"]
for f, v in ((1, 1.5), (6, 4.5), (14, 6.5), (19, 6.5), (23, 0.0), (27, 0.0)): jkey(f, v)
chew(30, 520, 17, 7.0)
jkey(521, 2.0); jkey(532, 4.0); jkey(F_YAWN - 6, 26.0); jkey(F_YAWN, 30.0); jkey(F_QIRS - 4, 31.0)
jkey(F_QIRS - 1, 31.5, 0, 0.0, 0.0); jkey(F_QIRS + 1, 36.0, 0, 1.25, 0.45)              # qirs: bo'g'im boshi oldinga sakraydi
for f in range(F_QIRS + 3, 613, 6): jkey(f, 35.0 + 1.2 * math.sin(f * 0.9), 0.8 * math.sin(f * 0.6), 1.25, 0.45)
for f in range(613, 659, 6): jkey(f, 27.0 + 1.0 * math.sin(f * 0.9), 0.8 * math.sin(f * 0.6), 1.25, 0.45)
jkey(658, 27.0, 0, 1.25, 0.45)
chew(659, END + 1, 15, 7.5)
for f in sorted(JK):
    op, side, fwd, down = JK[f]
    pbJ.rotation_euler = (R(op), 0.0, R(side)); pbJ.keyframe_insert("rotation_euler", frame=f)
    pbJ.location = (0.0, -down, fwd); pbJ.keyframe_insert("location", frame=f)       # bone fazosi (sm): Y tepa, Z old
for fc in fcurves(meg):
    if 'Jaw' in fc.data_path and fc.data_path.endswith("location"):
        for kp in fc.keyframe_points:
            if F_QIRS - 1 <= kp.co.x <= F_QIRS + 1: kp.interpolation = "LINEAR"

headE = child_of_bone("meg_head", meg, "Head")
jawE = child_of_bone("meg_jaw", meg, "Jaw")
def wp(o, f):
    sc.frame_set(f); bpy.context.view_layer.update(); return o.matrix_world.translation.copy()
def hmat(f):
    sc.frame_set(f); bpy.context.view_layer.update(); return headE.matrix_world.normalized()
for f_ in (60, 330, 553, 600, 640, 700):
    print("HEAD", f_, tuple(round(x, 3) for x in wp(headE, f_)), "HIPS", tuple(round(x, 3) for x in meg.matrix_world @ meg.pose.bones["mixamorig:Hips"].head))

# --- tishlar, til (real kadrlarda og'iz ochilganda ko'rinadi), saqich ---
tooth_m = mat("tooth", (0.93, 0.9, 0.82), 0.25, sss=0.2, sss_scale=0.001, coat=0.5)
tongue_m = mat("tongue", (0.75, 0.3, 0.32), 0.35, sss=0.4, sss_scale=0.002, coat=0.6)
teeth = empty("teeth_up", (0, 0, 0), headE); teeth_lo = empty("teeth_lo", tuple(-TMJ_H), jawE)
for k in range(10):
    x = -0.0225 + k * 0.005; z = 0.142 - 24 * x * x; rz = math.degrees(math.atan(48 * x))
    box(f"tu{k}", (0.0048, 0.0085, 0.004), (x, 0.0298, z), tooth_m, rot=(0, rz, 0), parent=teeth, bevel=0.0012)
    box(f"tl{k}", (0.0044, 0.0075, 0.0038), (x, 0.0205, z - 0.0015), tooth_m, rot=(0, rz, 0), parent=teeth_lo, bevel=0.0012)
tng = sphere("tongue", 1.0, (0, 0.0145, 0.12), tongue_m, scale=(0.019, 0.006, 0.028), sub=3, parent=teeth_lo)
cav_m = mat("mouth_cav", (0.02, 0.003, 0.004), 1.0); cav_m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.0
mcav = sphere("mouth_cav", 1.0, (0, 0.014, 0.1), cav_m, scale=(0.026, 0.03, 0.024), sub=3, parent=headE)
vis(mcav, ROOM_REAL)
for o in (teeth, teeth_lo): vis(o, ROOM_REAL)
gum_m = mat("gum", (0.95, 0.35, 0.6), 0.6, sss=0.3, sss_scale=0.001)
_gb = gum_m.node_tree.nodes["Principled BSDF"]; _gb.inputs["Sheen Weight"].default_value = 0.8          # shakar kukuni
gum = box("gum", (0.02, 0.0018, 0.07), (0, 0.0256, 0.32), gum_m, parent=headE, bevel=0.0006)
for f, z in ((1, 0.30), (8, 0.22), (17, 0.112), (20, 0.105)): key(gum, f, loc=(0, 0.0256, z))
vis(gum, [(1, 21)])

# ======================================================================
# 3) RENTGEN: shaffof Megan, bosh suyagi (pastki jag' Jaw bilan harakatlanadi), bo'g'im halqalari,
#    chaynash mushaklari, miya, adashgan nerv, qizilo'ngach, oshqozon
# ======================================================================
def xr_mat(name, col=(0.35, 0.75, 1.0), glow=1.2):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", glow)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.015), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.6), 0.04, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
def bone_mat(name, red=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.2)
    gl = value_node(m, "glow", 2.6); hot = value_node(m, "hot", 0.0)
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; L.new(hot, c.inputs["Factor"])
    c.inputs[6].default_value = (0.82, 0.92, 1.0, 1); c.inputs[7].default_value = (1.0, 0.12, 0.05, 1)
    em = N.new("ShaderNodeEmission"); L.new(c.outputs[2], em.inputs["Color"])
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, gl), 0.06), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.8), 0.2, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
def organ_mat(name, col, ecol, glow=0.4):
    """rentgendagi a'zo: yarim shaffof, 'glow' (yorqinlik) va 'hot' (qizil miltillash) kalitlanadi"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = value_node(m, "glow", glow); hot = value_node(m, "hot", 0.0)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    fac = P.math_n(N, L, "POWER", lw.outputs["Facing"], 1.3)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; L.new(hot, c.inputs["Factor"]); c.inputs[6].default_value = (*ecol, 1); c.inputs[7].default_value = (1.0, 0.08, 0.03, 1)
    em = N.new("ShaderNodeEmission"); L.new(c.outputs[2], em.inputs["Color"])
    k = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.8), 0.6), P.math_n(N, L, "ADD", fac, 0.25))
    L.new(P.math_n(N, L, "MULTIPLY", k, gl), em.inputs["Strength"])
    pb = N.new("ShaderNodeBsdfPrincipled"); pb.inputs["Base Color"].default_value = (*col, 1); pb.inputs["Roughness"].default_value = 0.3
    pb.inputs["Coat Weight"].default_value = 0.6
    ad = N.new("ShaderNodeAddShader"); L.new(pb.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", fac, 0.5), 0.35, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(ad.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
def nkeys(m, pairs, mode="LINEAR"):
    for name, f, v in pairs: val_key(m, name, f, v)
    interp(m.node_tree, mode)
def frames_vis(o, frames):
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    fs = sorted(set(frames)); prev = None
    for f in fs:
        if prev is None or f != prev + 1:
            o.hide_render = False; o.keyframe_insert("hide_render", frame=f)
        if f + 1 not in fs:
            o.hide_render = True; o.keyframe_insert("hide_render", frame=f + 1)
        prev = f
    ckey(o, "hide_render")

xbody = xr_mat("xr_body")
ghosts = []
for o in mmeshes:
    if "Eyelash" in o.name or "Sneakers" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xbody
    ghosts.append(g)
for g in ghosts: vis(g, XR, recursive=False)
for o in mmeshes: vis(o, ROOM_REAL, recursive=False)
skullE = empty("skullE", tuple(SKULL_LOC), headE); skullE.rotation_euler = SKULL_ROT; skullE.scale = (SKULL_S,) * 3
jskull = empty("jskullE", (0, 0, 0), jawE); jskull.matrix_basis = Matrix.Translation(-TMJ_H) @ SKM
skm = bone_mat("xr_bone"); jbm = bone_mat("xr_jaw")
for o, par, m in ((cran, skullE, skm), (mand, jskull, jbm)):
    sc.collection.objects.link(o); o.parent = par; o.data.materials.clear(); o.data.materials.append(m)
vis(skullE, XR); vis(jskull, XR)
# bo'g'im halqalari (quloq oldida, ikki tomonda)
tmj_m = glow_mat("tmj_glow", (0.3, 0.75, 1.0))
tmjs = []
for sx_ in (1, -1):
    t_ = sphere(f"tmj{sx_}", 0.0085, (sx_ * 0.052, TMJ_H.y, TMJ_H.z), tmj_m, sub=4, parent=headE)
    tmjs.append(t_); vis(t_, XR)
# chaynash mushaklari: tepasi bosh suyagida, pasti jag'da (STRETCH_TO) -> jag' ochilsa cho'ziladi, yopilsa qisqarib qalinlashadi
mus_m = bpy.data.materials.new("masseter"); mus_m.use_nodes = True
N = mus_m.node_tree.nodes; L = mus_m.node_tree.links; _mb = N["Principled BSDF"]
_mb.inputs["Base Color"].default_value = (0.55, 0.06, 0.05, 1); _mb.inputs["Roughness"].default_value = 0.35; _mb.inputs["Coat Weight"].default_value = 0.6
_mb.inputs["Alpha"].default_value = 0.55
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (160, 4, 160); L.new(tc.outputs["Object"], mp.inputs[0])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 3; L.new(mp.outputs[0], nz.inputs["Vector"])
mglow = value_node(mus_m, "glow", 0.6)
_mb.inputs["Emission Color"].default_value = (1.0, 0.12, 0.06, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", nz.outputs["Fac"], 0.3), mglow), _mb.inputs["Emission Strength"])
bp_ = N.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = 0.6; L.new(nz.outputs["Fac"], bp_.inputs["Height"]); L.new(bp_.outputs[0], _mb.inputs["Normal"])
muscles = []
for sx_ in (1, -1):
    top = V(sx_ * 0.06, 0.066, 0.078); bot = V(sx_ * 0.055, 0.012, 0.05); Lm = (top - bot).length
    vs, fs = [], []; nr, ns = 14, 18
    for i in range(nr + 1):
        t = i / nr; r_ = 0.003 + 0.0085 * math.sin(math.pi * t) ** 0.7
        for j in range(ns):
            a = 2 * math.pi * j / ns; vs.append((0.45 * r_ * math.cos(a), t * Lm, r_ * math.sin(a)))
    for i in range(nr):
        for j in range(ns): fs.append((i * ns + j, i * ns + (j + 1) % ns, (i + 1) * ns + (j + 1) % ns, (i + 1) * ns + j))
    mo = mesh_obj(f"masseter{sx_}", vs, fs, mus_m, headE, tuple(top)); smooth(mo)
    tgt = empty(f"mas_bot{sx_}", tuple(bot - TMJ_H), jawE)
    st = mo.constraints.new("STRETCH_TO"); st.target = tgt; st.rest_length = Lm; st.volume = "VOLUME_XZX"; st.bulge = 1.4
    muscles.append(mo); vis(mo, rng("xjaw", "muscle", "pop") + [(F_EARX, S["ear"][1])])
# miya (telefon.py dagi kabi)
def brain_mat2(name, glow=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15; b.inputs["Roughness"].default_value = 0.4
    gl = value_node(m, "glow", glow)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs[6].default_value = (0.78, 0.42, 0.45, 1); base.inputs[7].default_value = (0.92, 0.6, 0.6, 1)
    L.new(nz.outputs["Fac"], base.inputs["Factor"]); L.new(base.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (1.0, 0.55, 0.3, 1)
    fl = P.math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)
    L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", fl, 0.15), gl), b.inputs["Emission Strength"])
    return m
xb_m = brain_mat2("xbrain_m", 0.5)
xbrain, _ = PT.build_brain("xbrain", headE, size=0.074)
xbrain.location = (0, 0.11, 0.03); xbrain.rotation_euler = (R(-90), 0, 0)
for o in xbrain.children_recursive:
    if o.type == "MESH": o.data.materials.clear(); o.data.materials.append(xb_m)
vis(xbrain, XR)
# oshqozon (metaball, Spine bone fazosida: X chap, Y tepa, Z old) — J shakli
spineE = child_of_bone("meg_spine", meg, "Spine")
sto_m = organ_mat("stomach_xr", (0.85, 0.4, 0.42), (1.0, 0.55, 0.45), 0.5)
mb = bpy.data.metaballs.new("stomach"); mb.resolution = 0.008; mb.render_resolution = 0.004; mb.threshold = 0.6
for (x, y, z), r_ in (((0.06, 0.20, 0.03), 0.052), ((0.055, 0.155, 0.045), 0.062), ((0.04, 0.105, 0.055), 0.06),
                      ((0.015, 0.065, 0.062), 0.05), ((-0.02, 0.05, 0.065), 0.042), ((-0.05, 0.06, 0.06), 0.03), ((-0.065, 0.075, 0.055), 0.022)):
    el = mb.elements.new(); el.co = (x, y, z); el.radius = r_
mb.materials.append(sto_m)
stomach = bpy.data.objects.new("stomach", mb); sc.collection.objects.link(stomach); stomach.parent = spineE
vis(stomach, XR)
STO_TOP_L = V(0.05, 0.245, 0.03)
# qizilo'ngach va adashgan nerv: o'tirgan holatda dunyo fazosida (faqat o'tirgan rentgen kadrlarida ko'rinadi)
SITX = rng("xbody", "brain")
sc.frame_set(725); bpy.context.view_layer.update()
def bonew(n, off=(0, 0, 0)):
    pb = meg.pose.bones["mixamorig:" + n]; M = (meg.matrix_world @ pb.matrix).normalized(); return M @ V(*off)
HM_ = headE.matrix_world.normalized()
STO_TOP = spineE.matrix_world.normalized() @ STO_TOP_L
eso_pts = [HM_ @ V(0, 0.01, 0.04), bonew("Neck", (0, 0.02, 0.025)), bonew("Spine2", (0, 0.05, 0.02)), bonew("Spine1", (0.01, 0.06, 0.025)), STO_TOP]
eso_m = organ_mat("eso_xr", (0.8, 0.45, 0.45), (1.0, 0.6, 0.5), 0.35)
eso = PT.tube("esophagus", [tuple(p) for p in eso_pts], 0.009, eso_m, None, taper=[1.0] * len(eso_pts))
vag_m = PT.pulse_material("vagus", (0.95, 0.85, 0.4), 0.6, (1.0, 0.85, 0.3), 0.05)
vag_pts = [HM_ @ V(0, 0.035, -0.01), HM_ @ V(0.02, -0.01, 0.0), bonew("Neck", (0.025, 0.03, 0.0)), bonew("Spine2", (0.03, 0.05, 0.035)),
           bonew("Spine1", (0.035, 0.07, 0.045)), STO_TOP + V(0, -0.02, 0.0), spineE.matrix_world.normalized() @ V(0.05, 0.15, 0.1)]
vag = PT.tube("vagus", [tuple(p) for p in vag_pts], 0.0028, vag_m, None, taper=[1.0] * len(vag_pts))
for o in (eso, vag): vis(o, SITX, recursive=False)
B0, B1 = S["brain"]; XB0, XB1 = S["xbody"]
val_key(vag_m, "pos", 1, -0.1); val_key(vag_m, "pos", B0 + 8, -0.1); val_key(vag_m, "pos", B1 - 6, 1.1)
val_key(vag_m, "glow", 1, 0.5); interp(vag_m.node_tree, "LINEAR")
# rentgen kalitlari: "aldaydi" — jag' va oshqozon qizil miltillaydi; bo'g'im halqalari; mushak qizarib boradi; miya yonadi
nkeys(sto_m, [("glow", 1, 0.5), ("hot", 1, 0.0)])
for f in range(XB0 + 20, XB1, 10):
    val_key(sto_m, "glow", f, 2.4); val_key(sto_m, "glow", f + 5, 0.9); val_key(sto_m, "hot", f, 0.8); val_key(jbm, "hot", f, 0.75); val_key(jbm, "hot", f + 5, 0.15)
val_key(sto_m, "hot", XB1 + 1, 0.0); val_key(jbm, "hot", 1, 0.0); val_key(jbm, "hot", XB1 + 1, 0.0)
val_key(sto_m, "glow", XB1 + 1, 0.5); val_key(sto_m, "glow", B0, 0.5)
for f in range(B1 - 14, B1 + 1, 4): val_key(sto_m, "glow", f, 3.0); val_key(sto_m, "glow", f + 2, 1.6)
val_key(sto_m, "hot", B1 - 15, 0.0); val_key(sto_m, "hot", B1 - 10, 0.9)
interp(sto_m.node_tree, "LINEAR"); interp(jbm.node_tree, "LINEAR")
J0, J1 = S["xjaw"]
val_key(tmj_m, "a", 1, 0.0); val_key(tmj_m, "a", J0 + 6, 0.0); val_key(tmj_m, "a", J0 + 16, 2.5)
for f in range(J0 + 22, J1, 12): val_key(tmj_m, "a", f, 3.5); val_key(tmj_m, "a", f + 6, 1.6)
val_key(tmj_m, "a", S["muscle"][0], 0.6); val_key(tmj_m, "a", F_EARX, 0.6); val_key(tmj_m, "a", F_EARX + 10, 3.0)
val_key(tmj_m, "a", S["pop"][0], 1.2); val_key(tmj_m, "a", F_QIRS - 1, 1.2); val_key(tmj_m, "a", F_QIRS, 9.0); val_key(tmj_m, "a", F_QIRS + 10, 2.5)
interp(tmj_m.node_tree, "LINEAR")
M0, M1 = S["muscle"]
val_key(mus_m, "glow", 1, 0.5)
for i, f in enumerate(range(M0, M1 + 1, 17)):        # chaynash davri 17 kadr; har qisqarishda kuchliroq
    val_key(mus_m, "glow", f, 0.4 + 0.25 * i); val_key(mus_m, "glow", f + 9, 1.4 + 0.9 * i)
val_key(mus_m, "glow", F_CHID, 8.0); val_key(mus_m, "glow", M1, 9.0); val_key(mus_m, "glow", M1 + 1, 0.8)
interp(mus_m.node_tree, "LINEAR")
nkeys(xb_m, [("glow", 1, 0.5), ("glow", B0, 0.5), ("glow", B0 + 6, 4.0), ("glow", B0 + 12, 2.0)])
for f in range(B0 + 16, B1, 8): val_key(xb_m, "glow", f, 3.5); val_key(xb_m, "glow", f + 4, 1.8)
val_key(jbm, "hot", F_QIRS - 1, 0.0); val_key(jbm, "hot", F_QIRS, 1.0); val_key(jbm, "hot", F_QIRS + 14, 0.45); val_key(jbm, "hot", S["pop"][1] + 1, 0.0)

# ======================================================================
# 4) JAG' BO'G'IMI KESIMI (10x studiya): chakka suyagi chuqurchasi + bo'g'im do'mbog'i, bo'g'im boshi, tog'ay disk
#    mahalliy o'qlar: +X yon (kamera tomoni), +Y old, +Z tepa
# ======================================================================
CUT = V(40.0, 0.0, 1.5)
cutE = empty("cutE", tuple(CUT))
bone_cut_m = bpy.data.materials.new("cut_bone"); bone_cut_m.use_nodes = True
N = bone_cut_m.node_tree.nodes; L = bone_cut_m.node_tree.links; _bb = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18.0; nz.inputs["Detail"].default_value = 6
L.new(tc.outputs["Object"], nz.inputs["Vector"])
cr_ = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr_.inputs[0]); E_ = cr_.color_ramp.elements
E_[0].position, E_[0].color = 0.35, (0.72, 0.62, 0.48, 1); E_[1].position, E_[1].color = 0.65, (0.95, 0.9, 0.8, 1)
L.new(cr_.outputs[0], _bb.inputs["Base Color"]); _bb.inputs["Roughness"].default_value = 0.55
_bb.inputs["Subsurface Weight"].default_value = 0.2; _bb.inputs["Subsurface Scale"].default_value = 0.01
vr = N.new("ShaderNodeTexVoronoi"); vr.inputs["Scale"].default_value = 40.0; L.new(tc.outputs["Object"], vr.inputs["Vector"])
bp_ = N.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = 0.35; L.new(vr.outputs["Distance"], bp_.inputs["Height"]); L.new(bp_.outputs[0], _bb.inputs["Normal"])
def zb(y): return 0.20 + 0.075 * math.exp(-(y / 0.12) ** 2) - 0.085 * math.exp(-((y - 0.27) / 0.1) ** 2)
ny_ = 120; ZT_ = 0.7; prof_ = [(-0.6 + 1.3 * j / ny_) for j in range(ny_ + 1)]
vs = []; fs = []
for xs in (-0.32, 0.32):
    for y in prof_: vs.append((xs, y, zb(y)))
    for y in reversed(prof_): vs.append((xs, y, ZT_))
k_ = len(prof_) * 2
fs.append(tuple(range(k_))[::-1]); fs.append(tuple(range(k_, 2 * k_)))
for i in range(k_): fs.append((i, (i + 1) % k_, k_ + (i + 1) % k_, k_ + i))
tblk = mesh_obj("temporal", vs, fs, bone_cut_m, cutE)
for pl in tblk.data.polygons: pl.use_smooth = len(pl.vertices) == 4 and abs(pl.normal.z) > 0.2
tblk.data.update()
condE = empty("condE", (0, 0, -0.25), cutE)
cond = sphere("condyle", 1.0, (0, 0, 0.38), bone_cut_m, scale=(0.17, 0.095, 0.1), sub=4, parent=condE)
cneck = cyl("cneck", 0.065, 1.0, (0, -0.03, -0.1), bone_cut_m, rot=(-8, 0, 0), parent=condE, verts=40)
cart_m = mat("cart_cap", (0.86, 0.9, 0.96), 0.25, sss=0.5, sss_scale=0.01, coat=0.8)

disc_m = bpy.data.materials.new("disc"); disc_m.use_nodes = True
N = disc_m.node_tree.nodes; L = disc_m.node_tree.links; _db = N["Principled BSDF"]
_db.inputs["Base Color"].default_value = (0.78, 0.86, 1.0, 1); _db.inputs["Roughness"].default_value = 0.25
_db.inputs["Subsurface Weight"].default_value = 0.7; _db.inputs["Subsurface Scale"].default_value = 0.02; _db.inputs["Coat Weight"].default_value = 0.8
dhot = value_node(disc_m, "hot", 0.0); dglow = value_node(disc_m, "glow", 0.25)
c_ = N.new("ShaderNodeMix"); c_.data_type = "RGBA"; L.new(dhot, c_.inputs["Factor"]); c_.inputs[6].default_value = (0.45, 0.75, 1.0, 1); c_.inputs[7].default_value = (1.0, 0.1, 0.03, 1)
L.new(c_.outputs[2], _db.inputs["Emission Color"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "ADD", lw.outputs["Facing"], 0.3), dglow), _db.inputs["Emission Strength"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0)
disc = bpy.context.object; disc.name = "disc"
for v in disc.data.vertices:
    r2 = (v.co.x ** 2 + v.co.y ** 2); v.co.z *= 0.45 + 0.55 * r2       # ikki tomoni botiq (bikonkav)
for p_ in disc.data.polygons: p_.use_smooth = True
disc.data.materials.append(disc_m); disc.parent = cutE; disc.location = (0, 0.0, 0.252); disc.scale = (0.21, 0.14, 0.045)
dtex = bpy.data.textures.new("disc_wear", "VORONOI"); dtex.noise_scale = 0.18; dtex.distance_metric = "DISTANCE"
dsp = disc.modifiers.new("wear", "DISPLACE"); dsp.texture = dtex; dsp.strength = 0.0; dsp.texture_coords = "LOCAL"; dsp.mid_level = 0.8
disc.modifiers.new("sub", "SUBSURF").levels = 1
DC0, DC1 = S["disc"]; WE0, WE1 = S["wear"]
# harakat: sekin chaynash (disc kadri), keyin tez ishqalanish (wear) — bo'g'im boshi aylanadi va oldinga siljiydi
for f in range(1, END + 1, 2):
    if f < WE0: per, a_, s_ = 24, 7.0, 0.035
    else: per, a_, s_ = 7, 9.0, 0.05
    t = math.sin(2 * math.pi * f / per)
    condE.rotation_euler = (R(a_ * t), 0, 0); condE.location = (0, s_ * t, -0.25); condE.keyframe_insert("rotation_euler", frame=f); condE.keyframe_insert("location", frame=f)
    disc.location = (0, 0.6 * s_ * t, 0.252); disc.keyframe_insert("location", frame=f)
interp(condE, "LINEAR"); interp(disc, "LINEAR", "location")
for f, sz, st_ in ((1, 0.045, 0.0), (WE0, 0.045, 0.0), (WE0 + 30, 0.026, 0.02), (WE1, 0.02, 0.028)):
    disc.scale = (0.21, 0.14, sz); disc.keyframe_insert("scale", frame=f)
    dsp.strength = st_; dsp.keyframe_insert("strength", frame=f)
nkeys(disc_m, [("hot", 1, 0.0), ("glow", 1, 0.25), ("glow", DC0, 0.25), ("glow", DC0 + 12, 4.0), ("glow", WE0 - 1, 2.5), ("hot", WE0 + 6, 0.0),
               ("hot", WE1 - 6, 1.0), ("glow", WE0 + 8, 1.5), ("glow", WE1, 4.0)])
dust_m = mat("dust", (0.95, 0.95, 1.0), 0.4, emit=1.5, emit_col=(0.85, 0.9, 1.0))
rd = random.Random(21); dust = []
for k in range(70):
    o = sphere(f"dust{k}", rd.uniform(0.004, 0.011), (0, 0, 0), dust_m, sub=1, parent=cutE)
    f0 = rd.randint(WE0 + 2, WE1 - 6); life = rd.randint(8, 16)
    a = rd.uniform(0, 2 * math.pi); p0 = V(0.19 * math.cos(a) * 0.95, 0.125 * math.sin(a) * 0.95, 0.25)
    vel = V(math.cos(a) * rd.uniform(0.4, 1.0) + rd.uniform(0.3, 0.9), math.sin(a) * rd.uniform(0.4, 1.0), rd.uniform(-0.1, 0.5))
    for i in range(life + 1):
        t = i / 24; key(o, f0 + i, loc=tuple(p0 + vel * t + V(0, 0, -1.5 * t * t)))
    interp(o, "LINEAR"); frames_vis(o, range(f0, f0 + life))
vis(cutE, TMJR)

# ======================================================================
# 5) OSHQOZON ICHI (studiya): burmali devor, kislota ko'li, tomchilar, pufakchalar, yara (material maskasi)
# ======================================================================
STO = V(80.0, 0.0, 1.5); SX, SY, SZ = 2.2, 1.3, 1.1
bpy.ops.mesh.primitive_uv_sphere_add(segments=160, ring_count=96, radius=1.0, location=tuple(STO))
cav = bpy.context.object; cav.name = "stomach_in"; cav.scale = (SX, SY, SZ)
for p_ in cav.data.polygons: p_.use_smooth = True
rtex = bpy.data.textures.new("rugae", "WOOD"); rtex.wood_type = "BANDNOISE"; rtex.noise_scale = 0.35; rtex.turbulence = 9.0; rtex.noise_basis_2 = "SIN"
rd_ = cav.modifiers.new("rugae", "DISPLACE"); rd_.texture = rtex; rd_.strength = -0.09; rd_.texture_coords = "LOCAL"; rd_.mid_level = 0.5
# yara nuqtasi (mahalliy, birlik shar sirtida), dunyo va ichki normal
UD = V(0.38, -0.72, -0.42).normalized(); U_L = UD.copy()
ug = cav.vertex_groups.new(name="ulcer"); rg = cav.vertex_groups.new(name="rim")
for v in cav.data.vertices:
    d = (v.co - U_L).length / 0.2
    if d < 1.0: ug.add([v.index], (1 - d * d) ** 1.5, "REPLACE")
    if 0.7 < d < 1.6: rg.add([v.index], max(0.0, 1 - abs(d - 1.1) / 0.45), "REPLACE")
udsp = cav.modifiers.new("ulcer", "DISPLACE"); udsp.vertex_group = "ulcer"; udsp.mid_level = 0.0; udsp.strength = 0.0
rdsp = cav.modifiers.new("rim", "DISPLACE"); rdsp.vertex_group = "rim"; rdsp.mid_level = 0.0; rdsp.strength = 0.0
cav.modifiers.new("sub", "SUBSURF").levels = 2
U_W = STO + V(UD.x * SX, UD.y * SY, UD.z * SZ); U_N = -V(UD.x / SX, UD.y / SY, UD.z / SZ).normalized()
muc_m = bpy.data.materials.new("mucosa"); muc_m.use_nodes = True
N = muc_m.node_tree.nodes; L = muc_m.node_tree.links; _sb = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord")
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; L.new(nz.outputs["Fac"], base.inputs["Factor"])
base.inputs[6].default_value = (0.4, 0.05, 0.06, 1); base.inputs[7].default_value = (0.75, 0.2, 0.2, 1)
urad = value_node(muc_m, "rad", 0.0005)
dvec = P.math_n(N, L, "DISTANCE", tc.outputs["Generated"], tuple((U_L + V(1, 1, 1)) * 0.5), vec=True)   # orco: Displace'dan oldingi joy
d_ = P.math_n(N, L, "DIVIDE", dvec, P.math_n(N, L, "MULTIPLY", urad, 0.5))
fib = N.new("ShaderNodeTexNoise"); fib.inputs["Scale"].default_value = 45.0; fib.inputs["Detail"].default_value = 4; L.new(tc.outputs["Object"], fib.inputs["Vector"])
dj = P.math_n(N, L, "ADD", d_, P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", fib.outputs["Fac"], 0.5), 0.35))   # chetlari notekis
crater = P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "DIVIDE", dj, 0.95, clamp=True))
rim = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, P.math_n(N, L, "ABSOLUTE", P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", dj, 1.15), 2.6)), clamp=True),
               P.math_n(N, L, "GREATER_THAN", urad, 0.01))
ramp = N.new("ShaderNodeValToRGB"); L.new(P.math_n(N, L, "MULTIPLY", dj, 0.5, clamp=True), ramp.inputs[0]); RE = ramp.color_ramp.elements
RE[0].position, RE[0].color = 0.0, (0.16, 0.015, 0.01, 1); RE[1].position, RE[1].color = 0.8, (0.62, 0.17, 0.16, 1)
for pos_, col_ in ((0.18, (0.45, 0.08, 0.03, 1)), (0.3, (0.88, 0.76, 0.45, 1)), (0.44, (0.8, 0.6, 0.32, 1)), (0.55, (0.95, 0.05, 0.03, 1)), (0.68, (0.8, 0.12, 0.1, 1))):
    e_ = RE.new(pos_); e_.color = col_
c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(P.math_n(N, L, "LESS_THAN", dj, 1.6), c2.inputs["Factor"]); L.new(base.outputs[2], c2.inputs[6]); L.new(ramp.outputs[0], c2.inputs[7])
L.new(c2.outputs[2], _sb.inputs["Base Color"])
_sb.inputs["Roughness"].default_value = 0.22; _sb.inputs["Coat Weight"].default_value = 0.9; _sb.inputs["Coat Roughness"].default_value = 0.05
_sb.inputs["Subsurface Weight"].default_value = 0.4; _sb.inputs["Subsurface Scale"].default_value = 0.03
inf = value_node(muc_m, "inf", 0.0)
_sb.inputs["Emission Color"].default_value = (1.0, 0.08, 0.03, 1)
L.new(P.math_n(N, L, "MULTIPLY", rim, inf), _sb.inputs["Emission Strength"])
hgt = P.math_n(N, L, "ADD", P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", crater, -1.0), P.math_n(N, L, "MULTIPLY", rim, 0.35)), P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.15))
bpn = N.new("ShaderNodeBump"); bpn.inputs["Strength"].default_value = 0.8; bpn.inputs["Distance"].default_value = 0.06
L.new(hgt, bpn.inputs["Height"]); L.new(bpn.outputs[0], _sb.inputs["Normal"])
cav.data.materials.append(muc_m)
A0, A1 = S["acid"]; U0, U1 = S["ulcer"]
for f, a_, b_ in ((1, 0.0, 0.0), (U0 + 4, 0.0, 0.0), (F_GAST + 6, 0.07, -0.025), (U1, 0.11, -0.035)):   # normal tashqariga: + = devorga botadi
    udsp.strength = a_; udsp.keyframe_insert("strength", frame=f); rdsp.strength = b_; rdsp.keyframe_insert("strength", frame=f)
nkeys(muc_m, [("rad", 1, 0.0005), ("rad", U0 + 4, 0.0005), ("rad", F_GAST, 0.11), ("rad", U1, 0.2), ("inf", 1, 0.0), ("inf", U0 + 4, 0.0), ("inf", F_GAST + 4, 3.0), ("inf", U1, 4.5)])
# kislota ko'li
acid_m = bpy.data.materials.new("acid"); acid_m.use_nodes = True
N = acid_m.node_tree.nodes; L = acid_m.node_tree.links; _ab = N["Principled BSDF"]
_ab.inputs["Base Color"].default_value = (0.25, 0.75, 0.05, 1); _ab.inputs["Roughness"].default_value = 0.04
_ab.inputs["Transmission Weight"].default_value = 0.35; _ab.inputs["Coat Weight"].default_value = 1.0
_ab.inputs["Emission Color"].default_value = (0.3, 1.0, 0.05, 1); _ab.inputs["Emission Strength"].default_value = 0.6
tc = N.new("ShaderNodeTexCoord"); anz = N.new("ShaderNodeTexNoise"); anz.noise_dimensions = "4D"; anz.inputs["Scale"].default_value = 6.0
L.new(tc.outputs["Object"], anz.inputs["Vector"]); aw = value_node(acid_m, "w", 0.0); L.new(aw, anz.inputs["W"])
abp = N.new("ShaderNodeBump"); abp.inputs["Strength"].default_value = 0.3; L.new(anz.outputs["Fac"], abp.inputs["Height"]); L.new(abp.outputs[0], _ab.inputs["Normal"])
nkeys(acid_m, [("w", A0, 0.0), ("w", U1, 4.0)])
pool = plane("acid_pool", (6.0, 4.0), tuple(STO + V(0, 0, -0.95)), acid_m)
LV0 = STO.z - 0.97
for f, z in ((1, LV0), (A0, LV0 + 0.04), (U0, LV0 + 0.26), (U1, LV0 + 0.36)): key(pool, f, loc=(STO.x, STO.y, z))
interp(pool, "LINEAR")
def pool_z(f):
    pts_ = [(1, LV0), (A0, LV0 + 0.04), (U0, LV0 + 0.26), (U1, LV0 + 0.36)]
    for (fa, za), (fb, zb_) in zip(pts_, pts_[1:]):
        if fa <= f <= fb: return za + (zb_ - za) * (f - fa) / (fb - fa)
    return pts_[-1][1]
drop_m = mat("drop", (0.35, 0.9, 0.08), 0.05, emit=1.2, emit_col=(0.35, 1.0, 0.05), coat=1.0)
rdr = random.Random(33)
for k in range(46):
    th = rdr.uniform(-1.8, 1.8); ph = rdr.uniform(0.15, 0.95)
    d0 = V(math.cos(th) * math.cos(ph), math.sin(th) * math.cos(ph), math.sin(ph))
    p0 = STO + V(d0.x * SX, d0.y * SY, d0.z * SZ) * 0.93
    o = sphere(f"drop{k}", 0.028, tuple(p0), drop_m, scale=(1, 1, 1), sub=2)
    f0 = rdr.randint(A0 - 10, U1 - 12); grow = 6; on = []
    o.scale = (0.01, 0.01, 0.01); o.keyframe_insert("scale", frame=f0)
    o.scale = (0.8, 0.8, 1.1); o.keyframe_insert("scale", frame=f0 + grow)
    key(o, f0, loc=tuple(p0)); key(o, f0 + grow, loc=tuple(p0))
    t = 0; f = f0 + grow
    while True:
        t += 1 / 24; f += 1; z = p0.z - 3.5 * t * t
        if z < pool_z(f) or f > U1 + 1: break
        key(o, f, loc=(p0.x, p0.y, z)); o.scale = (0.6, 0.6, 1.6); o.keyframe_insert("scale", frame=f)
    frames_vis(o, range(max(f0, A0), f))
rbb = random.Random(5)
for k in range(40):
    x = STO.x + rbb.uniform(-0.2, 1.6); y = STO.y + rbb.uniform(-0.7, 0.7)
    o = sphere(f"bub{k}", rbb.uniform(0.015, 0.04), (x, y, LV0), drop_m, sub=2)
    f0 = rbb.randint(A0, U1 - 8); life = rbb.randint(8, 18)
    for f, s_ in ((f0, 0.05), (f0 + life - 2, 1.0), (f0 + life, 1.25)):
        o.scale = (s_, s_, s_ * 0.7); o.keyframe_insert("scale", frame=f); key(o, f, loc=(x, y, pool_z(f)))
    frames_vis(o, range(f0, f0 + life))
STO_OBJS = [cav, pool] + [o for o in bpy.data.objects if o.name.startswith(("drop", "bub"))]
for o in STO_OBJS: vis(o, STOR, recursive=False)

# ======================================================================
# 6) KAMERALAR (bosh fazosi: X chap, Y tepa, Z old; xona/studiyalar dunyo fazosida)
# ======================================================================
def look_rot(pos, tgt, up, roll=0.0):
    fw = (Vector(tgt) - Vector(pos)).normalized(); u = (Vector(up) - fw * Vector(up).dot(fw)).normalized()
    if roll: u = Quaternion(fw, R(roll)) @ u
    return Matrix((fw.cross(u), u, -fw)).transposed().to_euler()
def hcam(name, keys, lens, fstop=None, clip=0.004):
    """keys: [(f, pos_h, tgt_h[, roll])] bosh fazosida (yuz doim tik)"""
    c = shot_cam(name, (0, 0, 0), None, lens, None, clip=clip); c.parent = headE
    ft = empty(name + "_f", (0, 0, 0), headE)
    for k_ in keys:
        f, p_, t_ = k_[:3]; roll = k_[3] if len(k_) > 3 else 0.0
        c.location = p_; c.rotation_euler = look_rot(p_, t_, V(0, 1, 0), roll)
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        ft.location = t_; ft.keyframe_insert("location", frame=f)
    if fstop: c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop; c.data.dof.focus_object = ft
    return c
def wcam(name, keys, lens, fstop=None, clip=0.005, roll=0.0):
    c = shot_cam(name, (0, 0, 0), None, lens, None, clip=clip); ft = empty(name + "_f")
    for k_ in keys:
        f, p_, t_ = k_[:3]; rl = k_[3] if len(k_) > 3 else roll
        c.location = p_; c.rotation_euler = look_rot(p_, t_, V(0, 0, 1), rl)
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        ft.location = t_; ft.keyframe_insert("location", frame=f)
    if fstop: c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop; c.data.dof.focus_object = ft
    return c
MOUTH = V(0, 0.026, 0.15); TMJL = V(0.055, TMJ_H.y, TMJ_H.z)
HEADS = wp(headE, 80); HIPS_S = meg.matrix_world @ meg.pose.bones["mixamorig:Hips"].head
STOW = spineE.matrix_world.normalized() @ V(0.03, 0.12, 0.05)
print("HEADS", tuple(round(x, 3) for x in HEADS), "STOW", tuple(round(x, 3) for x in STOW))
# 1 ILGAK: lab sathida makro, saqich kiradi, crash zoom
c = hcam("hook", [(1, V(-0.11, -0.01, 0.62), MOUTH + V(0, 0, 0.02)), (16, V(-0.08, 0.0, 0.5), MOUTH), (45, V(-0.06, 0.01, 0.44), MOUTH + V(0, 0.004, 0))], 70, 2.8)
lens_keys(c, [(1, 55), (16, 70), (19, 100), (45, 105)]); shake(c, 19, 30, 0.003, seed=1)
# 2 KENG PLAN: pastdan 16 mm, dolly (timelapse)
W0, W1 = S["wide"]
c = wcam("wide", [(W0, V(2.35, -2.3, 0.38), V(0.0, 1.2, 0.95)), (W1, V(1.65, -1.75, 0.5), V(0.05, 1.25, 0.95))], 16)
# 3 RENTGEN TANA: jag'dan oshqozonga tushish
c = wcam("xbody", [(XB0, V(0.32, 0.62, 1.2), HEADS + V(0, -0.04, -0.03)), (XB0 + 26, V(0.36, 0.55, 1.08), HEADS + V(0, -0.02, -0.12)),
                   (XB1, V(0.42, 0.52, 0.86), STOW)], 28, 5.6)
# 4 RENTGEN BO'G'IM: yon tomondan aylanma + push-in
c = hcam("xjaw", [(J0, V(0.28, 0.02, 0.34), V(0.03, 0.05, 0.08)), (J0 + 30, V(0.34, 0.06, 0.15), TMJL), (J1, V(0.24, 0.07, 0.06), TMJL)], 35, 5.6)
# 5 MUSHAK: pastdan, "chidaydi" da crash zoom
c = hcam("muscle", [(M0, V(0.25, -0.07, 0.24), V(0.05, 0.04, 0.07)), (F_CHID - 1, V(0.2, -0.03, 0.2), V(0.055, 0.04, 0.065)), (M1, V(0.19, -0.02, 0.18), V(0.06, 0.04, 0.065))], 26, 5.6)
lens_keys(c, [(M0, 26), (F_CHID - 1, 28), (F_CHID + 3, 44), (M1, 46)]); shake(c, F_CHID, F_CHID + 14, 0.004, seed=5)
# 6 YUZ: 85 mm f/1.8, yonlama siljish
FA0, FA1 = S["face"]
c = hcam("face", [(FA0, V(-0.15, 0.075, 0.56), V(0, 0.055, 0.13)), (FA1, V(-0.08, 0.065, 0.47), V(0, 0.055, 0.13))], 85, 1.8)
# 7 QULOQ: quloq oldiga sho'ng'ish -> chaqnash -> rentgen
E0, E1 = S["ear"]
c = hcam("ear", [(E0, V(0.45, 0.09, 0.32), TMJL + V(0, 0, 0.03)), (F_EARX - 1, V(0.2, 0.075, 0.13), TMJL), (E1, V(0.17, 0.07, 0.1), TMJL)], 40, 4.0)
# 8-9 KESIM: pastdan makro, aylanma; ishqalanishda silkinish
c = wcam("disc", [(DC0, CUT + V(2.0, -0.95, 0.0), CUT + V(0, 0.05, 0.16)), (DC1, CUT + V(1.55, -0.45, 0.16), CUT + V(0, 0.03, 0.22))], 40, 8.0, clip=0.02)
c = wcam("wear", [(WE0, CUT + V(1.45, -0.55, 0.12), CUT + V(0, 0.02, 0.22)), (WE1, CUT + V(1.2, -0.3, 0.2), CUT + V(0, 0.0, 0.24))], 55, 8.0, clip=0.02)
shake(c, WE0, WE1, 0.01, seed=9, decay=False)
# 10 ESNASH: pastdan 18 mm, yuzga yaqinlashish
Y0_, Y1_ = S["yawn"]; HY = wp(headE, F_YAWN)
c = wcam("yawn", [(Y0_, V(1.6, -1.85, 0.42), HY + V(0, 0, -0.05)), (Y1_, V(1.38, -1.2, 0.95), HY + V(0, 0, 0.0))], 18, 4.0)
lens_keys(c, [(Y0_, 18), (Y1_, 26)])
# 11 RENTGEN: jag' chiqib ketadi (yondan), "qirs" da crash zoom + silkinish
P0, P1 = S["pop"]
c = hcam("pop", [(P0, V(0.62, 0.0, 0.2), V(0.02, 0.03, 0.07)), (F_QIRS - 1, V(0.58, 0.01, 0.18), V(0.02, 0.03, 0.07)), (P1, V(0.55, 0.02, 0.16), V(0.03, 0.04, 0.07))], 28, 5.6)
lens_keys(c, [(P0, 28), (F_QIRS - 1, 29), (F_QIRS + 3, 38), (P1, 40)]); shake(c, F_QIRS, F_QIRS + 16, 0.008, seed=11)
# 12 OG'IZ OCHIQ QOTDI: yuzga tez push-in, qiyshiq
T0, T1 = S["stuck"]
c = hcam("stuck", [(T0, V(-0.07, 0.03, 0.55), V(0, 0.04, 0.12), 6), (T1, V(-0.035, 0.035, 0.31), V(0, 0.04, 0.12), 9)], 35, 2.8)
# 13 YANA DIVAN: o'ng-oldindan past 16 mm
C0, C1 = S["chew2"]
c = wcam("chew2", [(C0, V(1.45, -0.35, 0.32), HEADS + V(0, 0, -0.2)), (C1, V(1.05, 0.15, 0.42), HEADS + V(0, 0, -0.12))], 16)
# 14 MIYA -> NERV -> OSHQOZON
c = wcam("brain", [(B0, V(0.3, 0.92, 1.3), HEADS + V(0, 0, 0.06)), (B0 + 14, V(0.32, 0.88, 1.22), HEADS + V(0, 0, 0.02)), (B1, V(0.44, 0.6, 0.86), STOW)], 30, 5.6)
# 15 OSHQOZON ICHI: keng 14 mm, sekin aylanma
c = wcam("acid", [(A0, STO + V(-1.25, -0.35, 0.25), STO + V(0.6, 0.0, -0.55)), (A1, STO + V(-0.85, 0.15, 0.1), STO + V(0.9, -0.3, -0.6))], 14, None, clip=0.02)
# 16 YARA: crash zoom + silkinish, qora bilan tugaydi
UT = U_W - U_N * 0.1
c = wcam("ulcer", [(U0, U_W + U_N * 1.2 + V(-0.2, 0, 0.2), UT), (F_GAST - 1, U_W + U_N * 1.0 + V(-0.1, 0, 0.12), UT), (F_GAST + 4, U_W + U_N * 0.75, UT), (U1, U_W + U_N * 0.68, UT)], 24, 11.0, clip=0.02)
lens_keys(c, [(U0, 22), (F_GAST - 1, 24), (F_GAST + 4, 32), (U1, 34)]); shake(c, F_GAST, F_GAST + 16, 0.012, seed=16)
for f_, n in SHOTS:
    sc.timeline_markers.new(n, frame=f_).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ---- chaqnash kartochkalari (kameraga bog'langan): 'a' 0..1 ----
def flash(cam, keys, col=(1, 1, 1), s=4.0):
    m = bpy.data.materials.new("flash_" + cam.name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    a = value_node(m, "a", 0.0); em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = s
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); L.new(a, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs[0])
    pl = plane("flash_" + cam.name + str(len(m.name)), (0.2, 0.3), (0, 0, -cam.data.clip_start * 1.5 - 0.002), m, parent=cam)
    for f, v in [(1, 0.0), (keys[0][0] - 1, 0.0)] + keys: val_key(m, "a", f, v)
    interp(m.node_tree, "LINEAR"); pl.visible_shadow = False
    sh = next(n for n, c_ in CAMS.items() if c_ == cam); vis(pl, [S[sh]])
    return pl
flash(CAMS["xbody"], [(XB0, 0.9), (XB0 + 4, 0.0)], (0.8, 0.92, 1.0))
flash(CAMS["ear"], [(F_EARX - 1, 0.0), (F_EARX, 0.95), (F_EARX + 4, 0.0)], (0.85, 0.95, 1.0))
flash(CAMS["disc"], [(DC0, 0.8), (DC0 + 4, 0.0)], (0.8, 0.9, 1.0))
flash(CAMS["pop"], [(F_QIRS - 1, 0.0), (F_QIRS, 0.9), (F_QIRS + 2, 0.0)], (1, 1, 1))
flash(CAMS["pop"], [(F_QIRS + 1, 0.0), (F_QIRS + 2, 0.6), (F_QIRS + 7, 0.0)], (1.0, 0.08, 0.04), 3.0)
flash(CAMS["brain"], [(B0, 0.7), (B0 + 3, 0.0)], (1.0, 0.9, 0.7))
flash(CAMS["acid"], [(A0, 0.6), (A0 + 4, 0.0)], (0.7, 1.0, 0.4), 3.0)
flash(CAMS["ulcer"], [(F_GAST - 1, 0.0), (F_GAST, 0.6), (F_GAST + 4, 0.0)], (1.0, 0.1, 0.05), 3.0)
flash(CAMS["ulcer"], [(U1 - 9, 0.0), (U1 - 2, 1.0)], (0, 0, 0), 0.0)

# ======================================================================
# 7) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links; bg = N["Background"]
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
wmap = N.new("ShaderNodeMapping"); wtc = N.new("ShaderNodeTexCoord"); L.new(wtc.outputs["Generated"], wmap.inputs[0]); L.new(wmap.outputs[0], env.inputs[0])
wmap.inputs["Rotation"].default_value = (0, 0, R(200))
wmx = N.new("ShaderNodeMix"); wmx.data_type = "RGBA"; L.new(env.outputs[0], wmx.inputs[6]); L.new(wmx.outputs[2], bg.inputs[0])
WORLD = {"room": ((0, 0, 0), 0.0, 0.9), "xr": ((0.0, 0.008, 0.025), 1.0, 1.0), "cut": ((0.006, 0.012, 0.03), 1.0, 1.0), "sto": ((0.02, 0.0, 0.0), 1.0, 1.0)}
def world_of(n):
    if n in ROOMN: return "room"
    if n in XRN: return "xr"
    return {"disc": "cut", "wear": "cut", "acid": "sto", "ulcer": "sto"}[n]
wkeys = [(f_, world_of(n)) for f_, n in SHOTS] + [(F_EARX, "xr")]
for f_, k in sorted(wkeys):
    col, fac, st = WORLD[k]
    wmx.inputs[7].default_value = (*col, 1); wmx.inputs[7].keyframe_insert("default_value", frame=f_)
    wmx.inputs["Factor"].default_value = fac; wmx.inputs["Factor"].keyframe_insert("default_value", frame=f_)
    bg.inputs[1].default_value = st; bg.inputs[1].keyframe_insert("default_value", frame=f_)
ckey(w.node_tree)
ROOMLIT = ROOM_REAL
# quyosh (deraza orqali): keng planda timelapse — nur xona bo'ylab suriladi
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.angle = R(1.5); sun.data.color = (1.0, 0.92, 0.8)
for f, e in lights_for(ROOMLIT, 4.5): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
ckey(sun.data)
for f, (el, az) in ((1, (36, 268)), (W0, (44, 250)), (W1, (20, 292)), (W1 + 1, (36, 268)), (END, (36, 268))):
    sun.rotation_euler = (R(90 - el), 0, R(az)); sun.keyframe_insert("rotation_euler", frame=f)
interp(sun, "LINEAR")
for fc in fcurves(sun):
    for kp in fc.keyframe_points:
        if kp.co.x in (W1, W1 + 1): kp.interpolation = "CONSTANT"
FT = empty("faceKeyT"); _cl = FT.constraints.new("COPY_LOCATION"); _cl.target = headE
area("room_fill", (0.0, -0.8, 2.6), 3.0, (1.0, 0.95, 0.88), lights_for(ROOMLIT, 120.0), target=empty("rfT", (0, 0.8, 0.5)))
area("win_bounce", (X0 + 0.3, 0.0, 1.5), 2.0, (0.8, 0.88, 1.0), lights_for(ROOMLIT, 60.0), target=empty("wbT", (0, 0.5, 1.0)))
area("face_key", (-0.9, -0.2, 1.7), 0.6, (1.0, 0.9, 0.8), lights_for(rng("hook", "face", "stuck") + [(S["ear"][0], F_EARX - 1)], 18.0), target=FT)
area("face_rim", (0.9, 2.3, 1.8), 0.5, (0.85, 0.9, 1.0), lights_for(rng("hook", "face", "chew2") + [(S["ear"][0], F_EARX - 1)], 25.0), target=FT)
area("yawn_key", tuple(STANDP + V(-1.0, -1.0, 2.0)), 1.0, (1.0, 0.93, 0.85), lights_for(rng("yawn", "stuck"), 40.0), target=FT)
# kesim studiyasi
CT_ = empty("cutT", tuple(CUT + V(0, 0, 0.22)))
area("C_key", tuple(CUT + V(1.4, -1.0, 1.2)), 1.0, (1.0, 0.95, 0.9), lights_for(TMJR, 90.0), target=CT_)
area("C_fill", tuple(CUT + V(1.5, 0.9, -0.6)), 1.0, (1.0, 0.8, 0.7), lights_for(TMJR, 30.0), target=CT_)
area("C_rim", tuple(CUT + V(-0.8, -1.2, 0.9)), 0.8, (0.35, 0.6, 1.0), lights_for(TMJR, 120.0), target=CT_)
pr = point("C_red", tuple(CUT + V(0.35, 0.0, 0.25)), 0.05, (1.0, 0.12, 0.04), [(1, 0), (WE0 + 10, 0.0), (WE1, 9.0), (WE1 + 1, 0)], const=False)
# oshqozon ichi: "endoskop" chirog'i + iliq/qizil to'ldiruvchilar
point("S_cam", tuple(STO + V(-0.9, -0.2, 0.3)), 0.03, (1.0, 0.95, 0.85), lights_for(STOR, 60.0))
point("S_fill", tuple(STO + V(0.9, 0.3, 0.2)), 0.3, (1.0, 0.55, 0.45), lights_for(STOR, 50.0))
point("S_ulc", tuple(U_W + U_N * 0.7 + V(0, 0, 0.3)), 0.02, (1.0, 0.85, 0.75), lights_for([S["ulcer"]], 14.0))

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = False
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("PROBE"): exec(open(os.environ["PROBE"]).read())
if os.environ.get("SAVE"): bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f_ in map(int, fs.split(",")):
            sc.frame_set(f_); r.filepath = f"{OUT}test_{f_:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
