# Nafas yo'lidagi ko'rinmas konveyer: kiprikchalar, shilimshiq va chekish — Zack D. Films uslubida 41.6 s video.
# Asos: zack_test/scene3.py + mixchar.py + koz_qon/koz_qon.py; procedural a'zolar: organs.py
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=10 /tmp/claude-0/bvenv/bin/python -I zack_test/kiprik/kiprik.py --render
# Sinov: FRAMES=20,70,150,280,350 PCT=35 ; bitta kadr oralig'i: RANGE=249,309
import bpy, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "burish"))
from mathutils import Vector, Matrix, Quaternion, Euler
bpy.ops.wm.read_factory_settings(use_empty=True)
import mixchar as mc
import lib as U
import organs as O
import parts as P
from lib import R, key, interp, vis, mat, bsdf, box, cyl, sphere, plane, empty, camera, shake, lens_keys, area, lights_for

OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = U.PH; BK = U.BK
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 999
sc.frame_start, sc.frame_end = 1, END
rnd = random.Random(11)

# ---------------- kadrlar (ovoz so'zlariga bog'langan: kadr = t*24+1) ----------------
SHOTS = [(1, "hook"), (37, "street"), (104, "xray_flow"), (188, "xray_dive"), (249, "cil_reveal"), (310, "cil_wave"),
         (389, "mucus"), (452, "smoke_drag"), (486, "smoke_tunnel"), (524, "toxins"), (573, "paralysis"), (626, "clock"),
         (651, "frozen"), (683, "tar"), (780, "lungs_dark"), (817, "morning"), (872, "cough"), (896, "xray_cough"), (963, "blob_out")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]

TUN = ["hook", "smoke_tunnel", "blob_out"]
CIL = ["cil_reveal", "cil_wave", "mucus", "toxins", "paralysis", "frozen", "tar"]
XRS = ["xray_flow", "xray_dive", "lungs_dark", "xray_cough"]
STR = ["street", "smoke_drag"]
BED = ["morning", "cough", "clock"]

# ======================================================================
# 1) KIPRIKCHALAR MAYDONI (dunyo markazi), kiprikcha uzunligi 0.25
# ======================================================================
CL = 0.25
croot = empty("cilia_root", (0, 0, 0))
cil = O.cilia_mesh("cilia", size=(6.0, 3.2), n=(112, 60), L=CL, r0=0.0068, seg=7, sides=6)
cil.parent = croot
M_cil = O.cilia_material(); cil.data.materials.append(M_cil)
md = cil.modifiers.new("beat", "NODES"); md.node_group = O.cilia_group(); md.show_viewport = False
cil.cycles.use_motion_blur = False          # tez urayotgan uchlar yuvilib ketmasin (deform blur)
M_epi = O.epithelium_material()
plane("epithelium", (7, 4.4), (0, 0, 0.0), M_epi, parent=croot)
# kiprikchalar to'lqini: T (faza), Amp, Droop
OMEGA = 2 * math.pi / 13.0           # bitta zarba ~13 kadr
PA0, PA1 = S["paralysis"]
FALAJ = 605                          # "falaj" (25.16 s)
def omega_at(f):
    if f < PA0 + 4: return OMEGA
    if f < FALAJ + 8: return OMEGA * max(0.0, 1 - (f - PA0 - 4) / (FALAJ + 8 - PA0 - 4)) ** 1.5
    return 0.0
T = 0.0
for f in range(1, END + 2):
    if f == 1 or f % 2 == 0 or PA0 - 2 <= f <= FALAJ + 12:
        O.key_cilia(cil, "T", f, T)
    T += omega_at(f)
for f, a, d in ((1, 1.0, 0.0), (PA0 + 4, 1.0, 0.0), (FALAJ - 8, 0.45, 0.35), (FALAJ + 2, 0.12, 0.75), (FALAJ + 12, 0.0, 0.9), (END, 0.0, 0.9)):
    O.key_cilia(cil, "Amp", f, a); O.key_cilia(cil, "Droop", f, d)
for f, v in ((1, 0.0), (PA0 + 6, 0.0), (FALAJ + 10, 1.0)):
    U.key_value(M_cil, "DEAD", f, v)
TA0, TA1 = S["tar"]
for f, v in ((1, 0.0), (TA0 + 10, 0.0), (TA1, 0.75)):
    U.key_value(M_cil, "TAR", f, v)

# shilimshiq oqimi: barcha bo'laklar + chang "flow" empty'ga bog'langan, +X (tomoq tomonga) siljiydi
flow = empty("flow", (0, 0, 0), croot)
V_FLOW = 0.016
x = 0.0
for f in range(1, END + 2):
    if f % 3 == 0 or f == 1 or f > END:
        flow.location = (x, 0, 0); flow.keyframe_insert("location", frame=f)
    x += V_FLOW * (omega_at(f) / OMEGA)
interp(flow, "LINEAR")
M_muc = O.mucus_material()
rafts = []
for k in range(26):
    lx = rnd.uniform(-9.5, 2.5); ly = rnd.uniform(-0.95, 1.4)
    o = U.uvsphere(f"raft{k}", 1.0, (lx, ly, CL - 0.005), M_muc, scale=(rnd.uniform(0.18, 0.42), rnd.uniform(0.12, 0.3), rnd.uniform(0.05, 0.08)),
                   seg=40, ring=20, parent=flow)
    o.rotation_euler = (0, 0, rnd.uniform(0, 3.14))
    dp = o.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new(f"rt{k}", "CLOUDS"); tx.noise_scale = 0.5
    dp.texture = tx; dp.strength = 0.25; dp.texture_coords = "LOCAL"
    rafts.append(o)
M_dust = mat("dust", (0.22, 0.2, 0.18), 0.85)
M_soot = mat("soot", (0.02, 0.018, 0.016), 0.6)
M_pollen = mat("pollen", (0.85, 0.62, 0.12), 0.5, sss=0.3)
M_bact = mat("bacteria", (0.25, 0.55, 0.18), 0.35, sss=0.4, coat=0.5)
M_bact.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.005
debris = []
for k in range(150):
    r = rows = None
    host = rnd.choice(rafts) if k < 110 else None
    if host:
        sx, sy = host.scale[0], host.scale[1]
        a = rnd.uniform(0, 6.283); d = rnd.uniform(0, 0.8)
        p = Vector((host.location.x + math.cos(a) * d * sx, host.location.y + math.sin(a) * d * sy, CL + 0.012 + rnd.uniform(-0.01, 0.03)))
    else:
        p = Vector((rnd.uniform(-9.5, 2.5), rnd.uniform(-1.4, 1.4), CL + rnd.uniform(0.0, 0.03)))
    kind = rnd.random()
    if kind < 0.45: o = O.rock(f"dust{k}", rnd.uniform(0.012, 0.03), M_dust, k, parent=flow)
    elif kind < 0.7: o = O.rock(f"soot{k}", rnd.uniform(0.008, 0.018), M_soot, k, parent=flow)
    elif kind < 0.82: o = sphere(f"pollen{k}", rnd.uniform(0.015, 0.024), (0, 0, 0), M_pollen, sub=2, parent=flow)
    else:
        o = O.bacterium(f"bact{k}", rnd.uniform(0.008, 0.011), rnd.uniform(0.02, 0.04), M_bact, parent=flow)
        o.rotation_euler = (R(90), 0, rnd.uniform(0, 6.28))
    o.location = p
    debris.append(o)

# zaharli molekulalar (tutun): tepadan yog'iladi va kiprikchalarga yopishadi
M_tox = mat("toxin", (0.65, 0.95, 0.12), 0.3, emit=1.2, emit_col=(0.6, 1.0, 0.1))
M_tox2 = mat("toxin2", (0.95, 0.55, 0.05), 0.3, emit=0.8, emit_col=(1.0, 0.5, 0.05))
M_bond = mat("bond", (0.8, 0.8, 0.75), 0.3)
TX0, TX1 = S["toxins"]
mols = []
for k in range(55):
    m_ = O.molecule(f"mol{k}", M_tox, M_tox2, M_bond, 100 + k, size=rnd.uniform(0.012, 0.02), parent=croot)
    land = rnd.randint(TX0 + 2, TX1 + 30)
    px, py = rnd.uniform(-1.2, 1.4), rnd.uniform(-1.0, 1.0)
    z1 = CL * rnd.uniform(0.6, 1.0)
    start = land - rnd.randint(16, 26)
    for f in (start, land):
        z = 1.4 if f == start else z1
        m_.location = (px + (0.15 if f == start else 0), py, z); m_.keyframe_insert("location", frame=f)
        m_.rotation_euler = (rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6)); m_.keyframe_insert("rotation_euler", frame=f)
    m_.scale = (0, 0, 0); m_.keyframe_insert("scale", frame=start - 1)
    m_.scale = (1, 1, 1); m_.keyframe_insert("scale", frame=start)
    interp(m_, "CONSTANT", "scale")
    mols.append(m_)
# qatron tomchilari: jigarrang, yopishqoq
M_tar = mat("tar", (0.09, 0.04, 0.012), 0.08, coat=1.0)
bsdf(M_tar).inputs["Subsurface Weight"].default_value = 0.2
tars = []
for k in range(110):
    o = U.uvsphere(f"tar{k}", rnd.uniform(0.03, 0.065), (0, 0, 0), M_tar, scale=(1, 1, 0.55), seg=24, ring=12, parent=croot)
    land = rnd.randint(TA0 + 4, TA1 - 10)
    px, py = rnd.uniform(-1.0, 1.4), rnd.uniform(-0.9, 0.9)
    zl = CL * rnd.uniform(0.35, 0.8)
    for f, z, s in ((land - 14, 1.2, (0.6, 0.6, 1.3)), (land, zl, (1.25, 1.25, 0.55)), (land + 6, zl - 0.01, (1.4, 1.4, 0.45))):
        o.location = (px, py, z); o.keyframe_insert("location", frame=f)
        o.scale = s; o.keyframe_insert("scale", frame=f)
    o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=land - 15)
    tars.append(o)
for f, v in ((1, 0.0), (TA0 + 10, 0.0), (TA1, 1.0)):
    U.key_value(M_muc, "DIRTY", f, v)
CIL_R = rng(*CIL)
vis(croot, CIL_R)

# ======================================================================
# 2) TRAXEYA TUNNELI (x = 60), o'q +Y (chuqurga), og'iz tomoni y = 0
# ======================================================================
TN = Vector((60.0, 0, 0)); troot = empty("tunnel_root", tuple(TN))
M_air = O.airway_material()
tun = O.tunnel("trachea_tunnel", length=40.0, r=1.0, parent=troot, m=M_air)
# devordagi shilimshiq zarralari (og'iz tomon, -Y ga oqadi)
M_speck = mat("speck", (0.85, 0.8, 0.45), 0.1, coat=1.0)
specks = []
for k in range(180):
    a = rnd.uniform(0, 6.283); rr = rnd.uniform(0.86, 0.95); y0 = rnd.uniform(0, 30)
    o = sphere(f"speck{k}", rnd.uniform(0.01, 0.03), (rr * math.cos(a), y0, rr * math.sin(a)), M_speck, scale=(1, 1.6, 1), sub=2, parent=troot)
    for f, dy in ((1, 0.0), (END + 1, -0.004 * END)):
        o.location = (rr * math.cos(a), y0 + dy, rr * math.sin(a)); o.keyframe_insert("location", frame=f)
    interp(o, "LINEAR")
    specks.append(o)
# tutun (hajmiy): old qismi FRONT bo'ylab chuqurga kiradi
M_smoke = bpy.data.materials.new("smoke_vol"); M_smoke.use_nodes = True
N = M_smoke.node_tree.nodes; L = M_smoke.node_tree.links
N.remove(N["Principled BSDF"]); outm = N["Material Output"]
vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.85, 0.83, 0.78, 1)
tc = N.new("ShaderNodeTexCoord"); mpn = N.new("ShaderNodeMapping")
L.new(tc.outputs["Object"], mpn.inputs[0])
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 6.0
L.new(mpn.outputs[0], nz.inputs["Vector"])
sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
front = U.value_node(M_smoke, "FRONT", 0.0)
mask = U._m(N, L, "MULTIPLY", U._m(N, L, "SUBTRACT", front.outputs[0], sep.outputs[1]), 0.6, clamp=True)
dens = U._m(N, L, "MULTIPLY", U._m(N, L, "MULTIPLY", U._m(N, L, "SUBTRACT", nz.outputs["Fac"], 0.3, clamp=True), mask), 14.0)
L.new(dens, vol.inputs["Density"]); L.new(vol.outputs[0], outm.inputs["Volume"])
vol.inputs["Absorption Color"].default_value = (0.8, 0.78, 0.74, 1)
vol.inputs["Emission Color"].default_value = (0.75, 0.72, 0.68, 1); vol.inputs["Emission Strength"].default_value = 0.12
smoke = box("smoke_box", (2.0, 13.0, 2.0), (0, 6.5, 0), M_smoke, parent=troot)
tc.object = troot                    # maska tunnel koordinatasida (y = 0 og'iz tomoni)
ST0, ST1 = S["smoke_tunnel"]
for f, v in ((ST0, 1.0), (ST0 + 14, 4.5), (ST1 + 1, 7.7)):
    U.key_value(M_smoke, "FRONT", f, v)
mpn.inputs["Location"].default_value = (0, 0, 0); mpn.inputs["Location"].keyframe_insert("default_value", frame=ST0)
mpn.inputs["Location"].default_value = (0, -4, 0.3); mpn.inputs["Location"].keyframe_insert("default_value", frame=ST1 + 1)
for f, v in ((1, 0.0), (ST0 + 8, 0.0), (ST1, 0.35), (S["blob_out"][0], 0.5)):
    U.key_value(M_air, "SMOKE", f, v)
vis(smoke, rng("smoke_tunnel"), False)
# yo'tal bilan otilgan qora shilimshiq bo'lagi
M_glob = mat("glob", (0.16, 0.11, 0.03), 0.05, coat=1.0, sss=0.2)
glob = U.uvsphere("glob", 0.62, (0, 14, 0), M_glob, scale=(1, 1.25, 0.85), seg=64, ring=32, parent=troot)
gd = glob.modifiers.new("d", "DISPLACE"); gtx = bpy.data.textures.new("globtex", "CLOUDS"); gtx.noise_scale = 0.4
gd.texture = gtx; gd.strength = 0.22
B0, B1 = S["blob_out"]
for f, y in ((B0, 16.0), (B0 + 12, 12.5), (B0 + 24, 8.0), (B1 + 1, 3.6)):
    key(glob, f, loc=(0, y, -0.05))
vis(glob, rng("blob_out"), False)
vis(troot, rng(*TUN), False)
for o in troot.children_recursive:
    if o not in (glob, smoke): vis(o, rng(*TUN), False)

# ======================================================================
# 3) QAHRAMON (Adam): ko'cha, rentgen, yotoqxona
# ======================================================================
aroot, adam, ameshes = mc.load_character("adam", "Adam.fbx")
U.soften(ameshes)
A = lambda f, inplace=True: mc.load_action(f, inplace)
ST = Vector((-80.0, 0, 0)); XR = Vector((-40.0, 0, 0)); BR = Vector((-120.0, 0, 0))

def strip(act, start, end, src=None, blend=4, speed=1.0):
    s = mc.add_strip(adam, act, start, blend=blend, src=src, speed=speed, hold=False)
    ln = (s.action_frame_end - s.action_frame_start) * s.scale
    s.repeat = max(1.0, (end - start + 1) / max(ln, 0.01))
    return s

# --- ko'cha (x = -80): yo'l -X/+X bo'ylab, trotuar y = 1.2..4.6
sroot = empty("street", tuple(ST))
M_asph = U.pbr("asphalt", "asphalt_02", 0.25)
M_pave = U.pbr("pavement", "concrete_pavement", 0.4)
M_wall = U.pbr("facade", "painted_plaster_wall", 0.3, tint=(0.92, 0.84, 0.72))
plane("road", (70, 14), (0, -5.8, 0), M_asph, parent=sroot)
box("sidewalk", (70, 3.4, 0.12), (0, 2.9, 0.06), M_pave, parent=sroot)
box("curb", (70, 0.15, 0.14), (0, 1.17, 0.07), mat("curb", (0.6, 0.6, 0.58), 0.7), parent=sroot)
M_glass = mat("winglass", (0.05, 0.07, 0.09), 0.05, metal=0.6)
M_frame = mat("winframe", (0.85, 0.85, 0.82), 0.5)
bx = -14.0
while bx < 30:
    w = rnd.uniform(5, 9); h = rnd.uniform(7, 14)
    tint = rnd.choice([(0.92, 0.84, 0.72), (0.8, 0.72, 0.62), (0.95, 0.92, 0.86), (0.75, 0.6, 0.5)])
    mw = U.pbr(f"facade{int(bx)}", "painted_plaster_wall", 0.3, tint=tint)
    box(f"bld{int(bx)}", (w - 0.3, 6, h), (bx + w / 2, 7.6, h / 2), mw, parent=sroot)
    for fl in range(int(h / 3)):
        for wi in range(int(w / 1.8)):
            wx = bx + 0.9 + wi * 1.8; wz = 1.6 + fl * 3.0
            if wz + 1.2 < h:
                box(f"win{int(bx)}_{fl}_{wi}", (1.0, 0.06, 1.4), (wx, 4.58, wz), M_glass, parent=sroot)
                box(f"wfr{int(bx)}_{fl}_{wi}", (1.12, 0.04, 1.52), (wx, 4.6, wz), M_frame, parent=sroot)
    bx += w
# mashina (BlenderKit Audi e-tron GT), yo'l chetida
car_root = empty("car_root", (5.8, -0.1, 0), sroot)
car = U.import_glb(BK + "c3c28d91_u.glb", car_root)
mn, mx = U.bbox(car)
if (mx.y - mn.y) > (mx.x - mn.x): car_root.rotation_euler = (0, 0, R(90))
bpy.context.view_layer.update(); mn, mx = U.bbox(car)
car_root.location.z -= mn.z
# quyosh nurida chang zarralari (DOF da yumaloq bokeh)
M_mote = mat("mote", (1, 0.9, 0.75), 0.5, emit=0.8, emit_col=(1, 0.85, 0.6))
motes = []
for k in range(260):
    p = Vector((rnd.uniform(-0.8, 4.0), rnd.uniform(1.4, 3.6), rnd.uniform(0.1, 2.2)))
    o = sphere(f"mote{k}", rnd.uniform(0.0015, 0.0035), tuple(p), M_mote, sub=1, parent=sroot)
    d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.6))) * 0.0012
    for f in (S["street"][0], S["smoke_drag"][1] + 1):
        o.location = p + d * (f - S["street"][0]); o.keyframe_insert("location", frame=f)
    interp(o, "LINEAR"); motes.append(o)
vis(sroot, rng(*STR))

# --- yurish: kameraga qarab (-X)
SW0, SW1 = S["street"]
aroot.location = ST + Vector((4.7, 2.5, 0.12)); aroot.rotation_euler = (0, 0, R(-90))
aroot.keyframe_insert("location", frame=SW0 - 8); aroot.keyframe_insert("rotation_euler", frame=SW0 - 8)
aroot.location = ST + Vector((1.25, 2.5, 0.12)); aroot.keyframe_insert("location", frame=SW1)
strip(A("Walking.fbx"), SW0 - 20, SW1 + 2, blend=0)
# --- chekish
SD0, SD1 = S["smoke_drag"]
U.at(aroot, SD0, tuple(ST + Vector((1.0, 2.6, 0.12))), -75)
strip(A("Smoking.fbx"), SD0 - 100, SD1 + 2, blend=0)
# --- rentgen: tik turgan poza (Breathing_Idle, qotirilgan)
for nm in XRS:
    U.at(aroot, S[nm][0], tuple(XR), 0)
    strip(A("Breathing_Idle.fbx"), S[nm][0] - 1, S[nm][1] + 1, src=(40, 41), blend=0)
# --- yotoqxona
MO0, MO1 = S["morning"]; CO0, CO1 = S["cough"]

# ======================================================================
# 4) YOTOQXONA (x = -120)
# ======================================================================
broom = empty("bedroom", tuple(BR))
M_lam = U.pbr("laminate", "laminate_floor_02", 0.5)
M_pl = U.pbr("plaster", "painted_plaster_wall", 0.5, tint=(0.95, 0.9, 0.82))
plane("br_floor", (5, 5), (0, 0, 0), M_lam, parent=broom)
plane("br_ceil", (5, 5), (0, 0, 2.7), mat("br_ceil", (0.9, 0.88, 0.85), 0.9), rot=(180, 0, 0), parent=broom)
plane("br_n", (5, 2.7), (0, 2.2, 1.35), M_pl, rot=(90, 0, 0), parent=broom)
plane("br_s", (5, 2.7), (0, -2.4, 1.35), M_pl, rot=(90, 0, 0), parent=broom)
plane("br_w", (5, 2.7), (-2.2, 0, 1.35), M_pl, rot=(90, 0, 90), parent=broom)
# sharqiy devor: deraza o'yig'i (y -0.2..1.2, z 0.9..2.2)
for nm, sz, loc in (("br_e1", (0.1, 1.8, 2.7), (2.2, -1.3, 1.35)), ("br_e2", (0.1, 1.0, 2.7), (2.2, 1.7, 1.35)),
                    ("br_e3", (0.1, 1.4, 0.9), (2.2, 0.5, 0.45)), ("br_e4", (0.1, 1.4, 0.5), (2.2, 0.5, 2.45))):
    box(nm, sz, loc, M_pl, parent=broom)
box("br_sill", (0.25, 1.5, 0.05), (2.15, 0.5, 0.88), mat("sill", (0.9, 0.9, 0.88), 0.4), parent=broom)
plane("br_sky", (6, 4), (6.0, 0.5, 1.8), mat("skyp", (0.8, 0.88, 1.0), emit=2.5), rot=(90, 0, 90), parent=broom)
bed_root, bed = U.import_ph("GothicBed_01", broom, (0, 1.0, 0), 0)
bpy.context.view_layer.update()
def ray_z(x, y):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = sc.ray_cast(dg, Vector((x, y, BR.z + 1.0)) + Vector((BR.x, 0, 0)), Vector((0, 0, -1)))
    return loc.z if hit else 0.0
RAYZ = 2.4
bmn, bmx = U.bbox(bed)
zy0 = ray_z(0, bmn.y + 0.06 - BR.y); zy1 = ray_z(0, bmx.y - 0.06 - BR.y)
if False:                     # bosh taxtasi -Y tomonda: 180 burib, +Y (shimoliy devor) tomonga qo'yamiz
    bed_root.rotation_euler = (0, 0, R(180)); bpy.context.view_layer.update(); bmn, bmx = U.bbox(bed)
bed_root.location.y += (2.15 - (bmx.y - BR.y)); bpy.context.view_layer.update(); bmn, bmx = U.bbox(bed)
MTOP = ray_z((bmn.x + bmx.x) / 2 - BR.x, (bmn.y + bmx.y) / 2 - BR.y + 0.15)
print("bed", bmn, bmx, "mattress top", MTOP)
ns_root, ns = U.import_ph("ClassicNightstand_01", broom, (bmx.x - BR.x + 0.4, bmx.y - BR.y - 0.35, 0), 0)
clk_root, clk = U.import_ph("alarm_clock_01", broom, (bmx.x - BR.x + 0.4, bmx.y - BR.y - 0.42, 0.7), -15)
U.import_ph("potted_plant_01", broom, (-1.8, 1.8, 0), 0, 1.1)
fr_root, _ = U.import_ph("fancy_picture_frame_01", broom, (-2.17, 0.2, 1.6), 0, 1.5)
fr_root.rotation_euler = (R(90), 0, R(90))
for o in clk:
    for m_ in (o.data.materials if o.type == "MESH" else []):
        b_ = m_.node_tree.nodes.get("Principled BSDF") if m_ and m_.use_nodes else None
        if b_ and m_.name.lower().endswith("glass"):          # shisha materiali shaffof emas (qora disk): yarim shaffof qilamiz
            for l_ in list(b_.inputs["Alpha"].links) + list(b_.inputs["Base Color"].links): m_.node_tree.links.remove(l_)
            b_.inputs["Alpha"].default_value = 0.07; b_.inputs["Base Color"].default_value = (1, 1, 1, 1); b_.inputs["Roughness"].default_value = 0.02
# soat millari tez aylanadi ("bir necha soatga")
CK0, CK1 = S["clock"]
hands = {o.name.split(".")[0]: o for o in clk}
for hn, turns in (("houd_hand", -0.35), ("minute_hand", -4.0), ("second_hand", -40.0)):
    h = hands.get(hn)
    if not h: continue
    h.rotation_mode = "XYZ"; r0 = h.rotation_euler.copy()
    h.keyframe_insert("rotation_euler", frame=CK0)
    h.rotation_euler = (r0.x, r0.y + turns * 2 * math.pi, r0.z); h.keyframe_insert("rotation_euler", frame=CK1 + 1)
    for fc in U.fcurves(h):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
# chang zarralari deraza nurida
motes2 = []
for k in range(160):
    p = Vector((rnd.uniform(-0.5, 2.0), rnd.uniform(-0.4, 1.6), rnd.uniform(0.6, 2.2)))
    o = sphere(f"bmote{k}", rnd.uniform(0.0015, 0.003), tuple(p), M_mote, sub=1, parent=broom)
    d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 0.5))) * 0.001
    for f in (CK0, S["cough"][1] + 1):
        o.location = p + d * (f - CK0); o.keyframe_insert("location", frame=f)
    interp(o, "LINEAR")
vis(broom, rng(*BED))
# Adam karavotda: bosh +Y (yostiq) tomonda
BED_C = Vector(((bmn.x + bmx.x) / 2, (bmn.y + bmx.y) / 2, 0))
lay_loc = Vector((BED_C.x, bmx.y - 0.42 - 0.6, MTOP - 0.93))
U.at(aroot, MO0, tuple(lay_loc), 0)
strip(A("Laying_Sleeping.fbx"), MO0 - 10, MO0 + 34, blend=0)
CG1 = MO0 + 32                      # birinchi yo'tal (~35.3 s)
strip(A("Laying_Severe_Cough.fbx"), CG1, CG1 + 42, blend=5)
CG2 = CO0 - 4
strip(A("Laying_Severe_Cough.fbx"), CG2, CO1 + 2, blend=3, speed=1.15)
ADAM_VIS = rng(*STR, "morning", "cough")
interp(aroot, "CONSTANT")
# yurish oralig'ida root chiziqli siljiydi
for fc in U.fcurves(aroot):
    for k in fc.keyframe_points:
        if SW0 - 9 <= k.co.x <= SW1: k.interpolation = "LINEAR"

# sigaret: o'ng qo'l barmoqlari orasida
M_paper = mat("cig_paper", (0.95, 0.94, 0.9), 0.6)
M_filter = mat("cig_filter", (0.85, 0.5, 0.2), 0.5)
M_ember = mat("ember", (0.3, 0.05, 0.0), 0.8, emit=6.0, emit_col=(1.0, 0.3, 0.05))
cig_b = U.bone_empty("cig_bone", adam, "Head")
cig = empty("cig", (0.012, 0.02, 0.118), cig_b)   # lablar orasida; Head: X chap, Y tepa, Z old
cig.rotation_euler = (R(105), 0, R(-12))        # +Y (uchi) oldinga va biroz pastga
cyl("cig_body", 0.0042, 0.075, (0, 0.0375, 0), M_paper, rot=(90, 0, 0), parent=cig, verts=16)
cyl("cig_filter", 0.0043, 0.022, (0, -0.011, 0), M_filter, rot=(90, 0, 0), parent=cig, verts=16)
emb = cyl("cig_ember", 0.0041, 0.004, (0, 0.077, 0), M_ember, rot=(90, 0, 0), parent=cig, verts=16)
DRAG = SD0 + 12
for f, e in ((1, 4.0), (DRAG - 4, 4.0), (DRAG, 22.0), (DRAG + 10, 18.0), (DRAG + 16, 5.0)):
    bsdf(M_ember).inputs["Emission Strength"].default_value = e; bsdf(M_ember).inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
vis(cig_b, rng("smoke_drag"))
# chiqarilgan tutun (hajmiy sharlar)
ahead = U.bone_empty("adam_head", adam, "Head")
aface = empty("adam_face", (0, 0.07, 0.09), ahead)
amouth = empty("adam_mouth", (0, 0.025, 0.11), ahead)
M_puff = bpy.data.materials.new("puff"); M_puff.use_nodes = True
N = M_puff.node_tree.nodes; L = M_puff.node_tree.links; N.remove(N["Principled BSDF"])
pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (0.8, 0.8, 0.78, 1)
tcp = N.new("ShaderNodeTexCoord"); nzp = N.new("ShaderNodeTexNoise"); nzp.inputs["Scale"].default_value = 3.0; nzp.inputs["Detail"].default_value = 5
L.new(tcp.outputs["Object"], nzp.inputs["Vector"])
grad = N.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"; L.new(tcp.outputs["Object"], grad.inputs["Vector"])
dp_ = U._m(N, L, "MULTIPLY", U._m(N, L, "MULTIPLY", U._m(N, L, "SUBTRACT", nzp.outputs["Fac"], 0.3, clamp=True), grad.outputs["Fac"]), 6.0)
U.value_node(M_puff, "PDEN", 1.0)
L.new(U._m(N, L, "MULTIPLY", dp_, N["PDEN"].outputs[0]), pv.inputs["Density"]); L.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
EXH = SD0 + 22
sc.frame_set(EXH); bpy.context.view_layer.update()
mpos = amouth.matrix_world.translation.copy()
hfwd = (ahead.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
puffs = []
for k in range(5):
    o = sphere(f"puff{k}", 1.0, tuple(mpos), M_puff, sub=2)
    d = (hfwd + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0.05, 0.35)))).normalized()
    st = EXH + k
    o.scale = (0.01,) * 3; o.keyframe_insert("scale", frame=st); o.location = mpos; o.keyframe_insert("location", frame=st)
    e_ = SD1 + 2
    o.scale = (0.12 + 0.03 * k,) * 3; o.keyframe_insert("scale", frame=e_)
    o.location = mpos + d * (0.28 + 0.05 * k); o.keyframe_insert("location", frame=e_)
    vis(o, [(st, SD1)], False); puffs.append(o)
for f, v in ((EXH, 1.0), (SD1 + 2, 0.4)): U.key_value(M_puff, "PDEN", f, v)
sc.frame_set(1)

# ======================================================================
# 5) RENTGEN (x = -40): shaffof tana, nurli bronxlar daraxti, o'pka
# ======================================================================
sc.frame_set(S["xray_flow"][0] + 2); bpy.context.view_layer.update()
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.3, base=0.012)
ghosts = []
for o in ameshes:
    if "Eyelash" in o.name: continue
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g); g.animation_data_clear()
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
def bh(bn): return adam.matrix_world @ adam.pose.bones["mixamorig:" + bn].head
W3 = adam.matrix_world.to_3x3() @ adam.pose.bones["mixamorig:Spine2"].matrix.to_3x3()
fwd = (W3 @ Vector((0, 0, 1))).normalized(); side = (W3 @ Vector((1, 0, 0))).normalized(); up = Vector((0, 0, 1))
neck = bh("Neck"); sp2 = bh("Spine2"); sp1 = bh("Spine1"); headp = bh("Head")
top = neck.lerp(headp, 0.35) + fwd * 0.045
carina = sp2 + up * 0.02 + fwd * 0.03
M_tube = P.pulse_material("xray_airway", (0.04, 0.25, 0.45), base_emit=0.6, pulse_col=(0.35, 0.8, 1.0), width=0.1)
atubes, leafs = O.airway_tree(top, carina, side, fwd, M_tube, seed=5, depth=5)
# o'pkalar
M_lung = bpy.data.materials.new("xray_lung"); M_lung.use_nodes = True
N = M_lung.node_tree.nodes; L = M_lung.node_tree.links; N.remove(N["Principled BSDF"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
fac = U._m(N, L, "POWER", lw.outputs["Facing"], 1.3)
U.value_node(M_lung, "DIRT", 0.0)
tcl = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 28.0; L.new(tcl.outputs["Object"], vo.inputs["Vector"])
nzl = N.new("ShaderNodeTexNoise"); nzl.inputs["Scale"].default_value = 9.0; L.new(tcl.outputs["Object"], nzl.inputs["Vector"])
spot = U._m(N, L, "LESS_THAN", U._m(N, L, "ADD", vo.outputs["Distance"], U._m(N, L, "MULTIPLY", nzl.outputs["Fac"], 0.3)),
            U._m(N, L, "MULTIPLY", N["DIRT"].outputs[0], 0.55))
em = N.new("ShaderNodeEmission")
cmix = N.new("ShaderNodeMix"); cmix.data_type = "RGBA"; L.new(U._m(N, L, "MULTIPLY", N["DIRT"].outputs[0], 0.6), cmix.inputs["Factor"])
cmix.inputs[6].default_value = (1.0, 0.45, 0.5, 1); cmix.inputs[7].default_value = (0.55, 0.32, 0.18, 1); L.new(cmix.outputs[2], em.inputs["Color"])
L.new(U._m(N, L, "ADD", U._m(N, L, "MULTIPLY", fac, 1.6), 0.25), em.inputs["Strength"])
trn = N.new("ShaderNodeBsdfTransparent")
ms1 = N.new("ShaderNodeMixShader"); L.new(U._m(N, L, "ADD", U._m(N, L, "MULTIPLY", fac, 0.6), 0.12, clamp=True), ms1.inputs[0])
L.new(trn.outputs[0], ms1.inputs[1]); L.new(em.outputs[0], ms1.inputs[2])
dark = N.new("ShaderNodeBsdfDiffuse"); dark.inputs["Color"].default_value = (0.01, 0.008, 0.006, 1)
ms2 = N.new("ShaderNodeMixShader"); L.new(U._m(N, L, "MULTIPLY", spot, 0.92), ms2.inputs[0])
L.new(ms1.outputs[0], ms2.inputs[1]); L.new(dark.outputs[0], ms2.inputs[2]); L.new(ms2.outputs[0], N["Material Output"].inputs["Surface"])
lungs = []
for sx in (-1, 1):
    c_ = sp2 + side * sx * 0.085 + fwd * 0.005 - up * 0.03
    o = U.uvsphere(f"lung{sx}", 1.0, tuple(c_), M_lung, seg=48, ring=24)
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = W3.to_quaternion()
    o.scale = (0.072, 0.13, 0.068)          # Spine2 mahalliy: X yon, Y tepa, Z old
    lungs.append(o)
LD0, LD1 = S["lungs_dark"]
for f, v in ((1, 0.0), (LD0, 0.15), (LD1, 0.95), (S["xray_cough"][0], 0.85), (END, 0.6)): U.key_value(M_lung, "DIRT", f, v)
# konveyer zarralari: bronx uchidan tomoqqa qarab
M_part = mat("xpart", (1, 0.85, 0.4), 0.4, emit=8.0, emit_col=(1.0, 0.8, 0.35))
XF0 = S["xray_flow"][0]; XD1 = S["xray_dive"][1]
parts_ = []
for k in range(70):
    pth = rnd.choice(leafs); u0 = rnd.random(); spd = rnd.uniform(1 / 90, 1 / 60)
    o = sphere(f"xp{k}", rnd.uniform(0.004, 0.0065), (0, 0, 0), M_part, sub=1)
    for f in range(XF0 - 1, XD1 + 2):
        u = (u0 + (f - XF0) * spd) % 1.0
        o.location = U.path_point(pth, u); o.keyframe_insert("location", frame=f)
    vis(o, rng("xray_flow", "xray_dive"), False); parts_.append(o)
# qora shilimshiq bo'lagi yo'tal bilan yuqoriga
XC0, XC1 = S["xray_cough"]
M_xglob = mat("xglob", (0.05, 0.03, 0.01), 0.3, emit=0.25, emit_col=(0.7, 0.3, 0.05))
xg = sphere("xglob", 0.016, (0, 0, 0), M_xglob, scale=(1, 1, 1.6), sub=3)
gpath = [p for p in max(leafs, key=lambda p: len(p))]
COUGHS = [XC0 + 6, XC0 + 22, XC0 + 38, XC0 + 54]
us = [0.45, 0.62, 0.78, 0.92, 1.02]
key(xg, XC0, loc=tuple(U.path_point(gpath, us[0])))
for i, cf in enumerate(COUGHS):
    key(xg, cf, loc=tuple(U.path_point(gpath, us[i])))
    key(xg, cf + 4, loc=tuple(U.path_point(gpath, min(1, us[i + 1]))))
vis(xg, rng("xray_cough"), False)
for o in lungs:
    s0 = o.scale.copy()
    for cf in COUGHS:
        o.scale = s0; o.keyframe_insert("scale", frame=cf - 1)
        o.scale = s0 * 0.88; o.keyframe_insert("scale", frame=cf + 2)
        o.scale = s0; o.keyframe_insert("scale", frame=cf + 9)
for cf in COUGHS:
    P.mat_value(M_tube, "glow", cf - 1, 0.6); P.mat_value(M_tube, "glow", cf + 1, 4.0); P.mat_value(M_tube, "glow", cf + 8, 0.6)
for f in range(XF0, XD1 + 2, 20):
    P.mat_value(M_tube, "pos", f, 1.1); P.mat_value(M_tube, "pos", f + 19, -0.1)
XR_ALL = rng(*XRS)
for o in ghosts + atubes + lungs: vis(o, XR_ALL, False)
for o in [aroot, adam] + ameshes: vis(o, ADAM_VIS, False)
XCEN = carina.lerp(top, 0.3)
sc.frame_set(1)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c
def cam_path(c, pairs):
    for f, loc in pairs: key(c, f, loc=tuple(loc))

# 1 ilgak: traxeya ichida tez uchish
H0, H1 = S["hook"]
hT = empty("hookT", tuple(TN + Vector((0, 4, 0))))
c = shot_cam("hook", (0, 0, 0), hT, 20, 2.8, focus=hT)
cam_path(c, [(H0, TN + Vector((0.12, 0.6, 0.18))), (H0 + 10, TN + Vector((0.0, 3.0, 0.1))), (H1 + 1, TN + Vector((-0.1, 9.0, 0.05)))])
cam_path(hT, [(H0, TN + Vector((0, 5, 0))), (H1 + 1, TN + Vector((0.1, 14, -0.05)))])
shake(c, H0, H1, 0.03, 1)
# 2 ko'cha: pastdan 16 mm
SWT = U.bone_empty("adam_chest", adam, "Spine2")
c = shot_cam("street", (0, 0, 0), SWT, 16, 4.0, focus=ahead)
cam_path(c, [(SW0, ST + Vector((-0.35, 2.15, 0.28))), (SW1 + 1, ST + Vector((-0.55, 2.1, 0.3)))])
# 3 rentgen: konveyer
xT = empty("xrayT", tuple(XCEN))
c = shot_cam("xray_flow", (0, 0, 0), xT, 40, 4.0, focus=xT)
fd = (fwd + side * 0.35).normalized()
cam_path(c, [(XF0, XCEN + fd * 1.25 - up * 0.1), (S["xray_flow"][1] + 1, XCEN + fd * 0.85 - up * 0.02)])
# 4 sho'ng'ish
XD0 = S["xray_dive"][0]
dT = empty("diveT", tuple(carina))
c = shot_cam("xray_dive", (0, 0, 0), dT, 35, 3.5, focus=dT)
fd2 = (fwd - side * 0.25 + up * 0.15).normalized()
for f in range(XD0, XD1 + 2, 2):
    t = (f - XD0) / (XD1 - XD0); e = t ** 2.4
    key(c, f, loc=tuple(carina + fd2 * (0.7 * (1 - e) + 0.035 * e)))
lens_keys(c, [(XD0, 35), (XD1 - 6, 45), (XD1, 60)])
# 5 kiprikchalar o'rmoni: tepadan pastga
CR0, CR1 = S["cil_reveal"]
crT = empty("crT", (0.2, 0.0, 0.2))
c = shot_cam("cil_reveal", (0, 0, 0), crT, 24, 2.8, focus=crT)
for f in range(CR0, CR1 + 2, 2):
    t = (f - CR0) / (CR1 - CR0); e = 1 - (1 - t) ** 2.2
    key(c, f, loc=(-0.25 - 0.55 * e, -1.0 + 0.4 * e, 1.7 - 1.36 * e))
cam_path(crT, [(CR0, (0.2, 0.0, 0.1)), (CR1 + 1, (0.35, 0.05, 0.22))])
# 6 yon tomondan to'lqin
CW0, CW1 = S["cil_wave"]
cwT = empty("cwT", (-0.2, -1.25, 0.2))
c = shot_cam("cil_wave", (0, 0, 0), cwT, 45, 5.0, focus=cwT)
cam_path(c, [(CW0, (-0.6, -1.95, 0.42)), (CW1 + 1, (-0.2, -1.92, 0.4))])
cam_path(cwT, [(CW0, (-0.45, -1.3, 0.2)), (CW1 + 1, (-0.05, -1.3, 0.2))])
# 7 shilimshiq bilan birga kuzatish
MU0, MU1 = S["mucus"]
sc.frame_set(MU0); bpy.context.view_layer.update()
host = min(rafts, key=lambda r: abs(r.matrix_world.translation.x + 0.3) + abs(r.matrix_world.translation.y) * 0.5)
muT = empty("muT", (0, 0, 0), host); muT.location = (0, 0, 0.6)
c = shot_cam("mucus", (0, 0, 0), muT, 32, 3.2, focus=muT)
hp0 = host.matrix_world.translation.copy()
sc.frame_set(MU1 + 1); bpy.context.view_layer.update(); hp1 = host.matrix_world.translation.copy(); sc.frame_set(1)
cam_path(c, [(MU0, hp0 + Vector((-0.8, -0.95, 0.55))), (MU1 + 1, hp1 + Vector((-0.6, -0.8, 0.45)))])
# 8 sigaret tortish: yuzga yaqin
c = shot_cam("smoke_drag", (0, 0, 0), aface, 60, 2.0, focus=aface)
sc.frame_set(SD0 + 5); bpy.context.view_layer.update()
fpos = aface.matrix_world.translation.copy(); hf = (ahead.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
hs = (ahead.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
sc.frame_set(1)
cam_path(c, [(SD0, fpos + hf * 0.55 - hs * 0.55 - up * 0.1), (SD1 + 1, fpos + hf * 0.48 - hs * 0.45 - up * 0.08)])
# 9 tutun tunnelga kiradi
stT = empty("smokeT", tuple(TN + Vector((0, 1.5, 0))))
c = shot_cam("smoke_tunnel", (0, 0, 0), stT, 22, 4.0, focus=stT)
cam_path(c, [(ST0, TN + Vector((0.1, 8.2, 0.12))), (ST1 + 1, TN + Vector((0.0, 8.9, 0.1)))])
# 10 zaharli molekulalar yog'iladi: pastdan keng
c = shot_cam("toxins", (0, 0, 0), None, 18, 5.0, focus=0.55)
c.rotation_euler = (R(104), 0, R(-20))
cam_path(c, [(TX0, (-0.45, -1.78, 0.1)), (TX1 + 1, (-0.38, -1.74, 0.11))])
# 11 falaj: crash zoom
pT = empty("parT", (0.05, -1.3, 0.12))
c = shot_cam("paralysis", (0, 0, 0), pT, 38, 5.6, focus=pT)
cam_path(c, [(PA0, (-0.3, -2.0, 0.5)), (FALAJ - 1, (-0.25, -1.95, 0.48)), (FALAJ + 2, (-0.1, -1.72, 0.36)), (PA1 + 1, (-0.09, -1.7, 0.35))])
lens_keys(c, [(PA0, 38), (FALAJ - 1, 38), (FALAJ + 2, 55)])
shake(c, FALAJ, FALAJ + 14, 0.02, 9)
# 12 soat
bpy.context.view_layer.update()
cpos = clk_root.matrix_world.translation.copy()
ckT = empty("clockT", tuple(cpos + Vector((0, 0, 0.075))))
cq = clk_root.matrix_world.to_3x3()
c = shot_cam("clock", (0, 0, 0), ckT, 50, 3.5, focus=ckT)
cam_path(c, [(CK0, cpos + cq @ Vector((0.12, -0.42, 0.16))), (CK1 + 1, cpos + cq @ Vector((0.08, -0.34, 0.13)))])
# 13 qotib qolgan kiprikchalar: keng, qimirlamas
frT = empty("frT", (0.1, 0.1, 0.12))
c = shot_cam("frozen", (-1.25, -1.35, 0.75), frT, 26, 5.6, focus=frT)
# 14 qatron yog'adi
taT = empty("taT", (0.2, 0.0, 0.18))
c = shot_cam("tar", (0, 0, 0), taT, 32, 3.5, focus=taT)
cam_path(c, [(TA0, (0.75, -1.05, 0.6)), (TA1 + 1, (0.45, -0.65, 0.4))])
# 15 o'pkada qora dog'lar: sekin aylanma
ldT = empty("ldT", tuple(sp2 - up * 0.03))
c = shot_cam("lungs_dark", (0, 0, 0), ldT, 35, 4.0, focus=ldT)
for f in range(LD0, LD1 + 2, 3):
    t = (f - LD0) / (LD1 - LD0); a = R(-25 + 35 * t)
    d = (Quaternion(up, a) @ fwd).normalized()
    key(c, f, loc=tuple(ldT.location + d * (0.75 - 0.15 * t)))
# 16 ertalab: past burchak keng
mT = empty("mornT", tuple(lay_loc + Vector((0, 0.35, 1.0))))
c = shot_cam("morning", (0, 0, 0), mT, 18, 4.0, focus=ahead)
cam_path(c, [(MO0, Vector((bmn.x - 1.05, bmn.y + 0.35, 0.5))), (MO1 + 1, Vector((bmn.x - 0.9, bmn.y + 0.55, 0.55)))])
# 17 yo'tal: yuzga yaqin, kuchli silkinish
c = shot_cam("cough", (0, 0, 0), aface, 50, 2.0, focus=aface)
cam_path(c, [(CO0, lay_loc + Vector((-0.75, 0.35, 1.25))), (CO1 + 1, lay_loc + Vector((-0.68, 0.38, 1.25)))])
for cf in (CO0 + 2, CO0 + 12):
    shake(c, cf, cf + 10, 0.025, cf)
# 18 rentgen yo'tal
xcT = empty("xcT", tuple(carina.lerp(top, 0.4)))
c = shot_cam("xray_cough", (0, 0, 0), xcT, 38, 4.0, focus=xcT)
fd3 = (fwd + side * 0.4).normalized()
cam_path(c, [(XC0, xcT.location + fd3 * 0.8), (XC1 + 1, xcT.location + fd3 * 0.55)])
for cf in COUGHS: shake(c, cf, cf + 10, 0.02, cf)
# 19 qora bo'lak kameraga otiladi
boT = empty("blobT", tuple(TN + Vector((0, 14, 0))))
c = shot_cam("blob_out", (0, 0, 0), boT, 22, 4.0, focus=glob)
cam_path(c, [(B0, TN + Vector((0.08, 2.2, 0.1))), (B1 + 1, TN + Vector((0.0, 2.5, 0.08)))])
shake(c, B1 - 12, B1, 0.04, 19)

for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 7) YORUG'LIK
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
tcw = N.new("ShaderNodeTexCoord"); mpw = N.new("ShaderNodeMapping"); L.new(tcw.outputs["Generated"], mpw.inputs[0])
mpw.inputs["Rotation"].default_value = (0, 0, R(200))
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr"); L.new(mpw.outputs[0], env.inputs[0])
flat = N.new("ShaderNodeMix"); flat.data_type = "RGBA"; L.new(env.outputs[0], flat.inputs[6])
bg = N["Background"]; L.new(flat.outputs[2], bg.inputs[0])
WL = {"hook": (0.0, 1, (0, 0, 0)), "street": (1.0, 0, (0, 0, 0)), "xray_flow": (1.0, 1, (0.0, 0.004, 0.012)),
      "cil_reveal": (1.0, 1, (0.06, 0.008, 0.015)), "smoke_drag": (1.0, 0, (0, 0, 0)), "smoke_tunnel": (0.0, 1, (0, 0, 0)),
      "toxins": (1.0, 1, (0.05, 0.012, 0.012)), "paralysis": (1.0, 1, (0.035, 0.02, 0.012)), "clock": (0.5, 0, (0, 0, 0)),
      "frozen": (1.0, 1, (0.02, 0.016, 0.012)), "lungs_dark": (1.0, 1, (0.0, 0.004, 0.012)), "morning": (0.5, 0, (0, 0, 0)), "xray_cough": (1.0, 1, (0.0, 0.004, 0.012)),
      "blob_out": (0.0, 1, (0, 0, 0))}
cur = WL["hook"]
for f, n in SHOTS:
    cur = WL.get(n, cur)
    bg.inputs[1].default_value = cur[0]; bg.inputs[1].keyframe_insert("default_value", frame=f)
    flat.inputs["Factor"].default_value = cur[1]; flat.inputs["Factor"].keyframe_insert("default_value", frame=f)
    flat.inputs[7].default_value = (*cur[2], 1); flat.inputs[7].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")

# tunnel: kamera bilan yuradigan "endoskop" chirog'i
for n in TUN:
    cm = CAMS[n]
    area(f"endo_{n}", (0.05, 0.08, 0.05), 0.15, (1, 0.93, 0.85), lights_for(rng(n), 45), parent=cm, kind="POINT")
area("tun_glow", tuple(TN + Vector((0, 18, 0))), 1.0, (1.0, 0.35, 0.3), lights_for(rng(*TUN), 60), kind="POINT")
# kiprikchalar
CIL_N = rng("cil_reveal", "cil_wave", "mucus", "toxins")
area("cil_key", (-1.6, -2.0, 2.4), 2.0, (1, 0.9, 0.86), lights_for(CIL_N, 260) + [(PA0, 200), (S["frozen"][0], 90), (TA0, 140), (TA1 + 1, 0)],
     target=croot)
area("cil_rim", (1.8, 2.2, 0.7), 1.5, (0.45, 0.75, 1.0), lights_for(CIL_N, 180) + [(PA0, 150), (S["frozen"][0], 0), (TA1 + 1, 0)], target=croot)
area("cil_sick", (1.6, 1.8, 0.9), 1.5, (0.75, 1.0, 0.25), lights_for(rng("toxins", "paralysis", "frozen", "tar"), 110), target=croot)
area("cil_fill", (0.3, -1.5, 0.35), 1.2, (1, 0.6, 0.55), lights_for(CIL_R, 25), target=croot)
# ko'cha: quyosh
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (R(50), 0, R(-50)); sun.data.angle = R(1.0); sun.data.color = (1, 0.93, 0.82)
for f, e in lights_for(rng(*STR), 4.0): sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
interp(sun.data, "CONSTANT")
area("str_bounce", tuple(ST + Vector((0.0, 1.0, 0.6))), 2.0, (1, 0.9, 0.8), lights_for(rng("street"), 120), target=ahead)
area("str_face", tuple(ST + Vector((0.2, 1.8, 1.9))), 0.8, (1, 0.92, 0.85), lights_for(rng("smoke_drag"), 60), target=aface)
area("str_rim", tuple(ST + Vector((2.4, 3.6, 2.0))), 0.6, (0.7, 0.85, 1.0), lights_for(rng("smoke_drag"), 80), target=aface)
# yotoqxona: ertalabki quyosh deraza orqali
bsun = bpy.data.objects.new("bsun", bpy.data.lights.new("bsun", "SUN")); sc.collection.objects.link(bsun)
bsun.rotation_euler = (R(65), 0, R(95)); bsun.data.angle = R(1.5); bsun.data.color = (1, 0.8, 0.55)
for f, e in lights_for(rng(*BED), 7.0): bsun.data.energy = e; bsun.data.keyframe_insert("energy", frame=f)
interp(bsun.data, "CONSTANT")
area("br_win", tuple(BR + Vector((2.05, 0.5, 1.55))), 1.3, (1, 0.88, 0.7), lights_for(rng(*BED), 250), target=ahead)
area("br_fill", tuple(BR + Vector((-1.6, -1.8, 2.2))), 1.5, (0.85, 0.9, 1.0), lights_for(rng(*BED), 90), target=ahead)
area("clock_key", tuple(cpos + Vector((-0.25, -0.3, 0.3))), 0.3, (1, 0.9, 0.75), lights_for(rng("clock"), 12), target=ckT)
# rentgen: hech qanday chiroq kerak emas (emission), lekin qatron bo'lagi uchun
area("x_rim", tuple(XR + Vector((0.6, -0.6, 1.8))), 0.5, (1, 0.6, 0.3), lights_for(rng("xray_cough"), 10), target=xcT)

# ======================================================================
# 8) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 10)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.transmission_bounces = 4
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = os.environ.get("PERSIST", "1") == "1"
r.use_overwrite = False; r.use_placeholder = True

if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True; bpy.ops.render.render(write_still=True)
    else:
        a, b_ = map(int, os.environ.get("RANGE", f"1,{END}").split(","))
        sc.frame_start, sc.frame_end = a, b_
        bpy.ops.render.render(animation=True)
