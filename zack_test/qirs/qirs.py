# Barmoq nega qirsillaydi — Zack D. Films uslubida 47.5 s video (1140 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py + burish/parts.py (quvur, rentgen material, yordamchilar).
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/qirs/qirs.py --render
# Sinov: FRAMES=20,100,190,300,780 PCT=35
import bpy, math, sys, os, random, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "burish"))
from mathutils import Vector, Matrix, Euler
import mixchar as mc

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
import parts as P
P.VIEWPORT_OFF = True
sc = bpy.context.scene
sc.render.fps = 24
END = 1140
sc.frame_start, sc.frame_end = 1, END

# ---------------- kadrlar (ovoz so'zlariga bog'langan, Whisper) ----------------
SHOTS = [(1, "hook"), (73, "myth"), (138, "xray"), (230, "anat"), (337, "gas"), (405, "pull"), (491, "vac"), (605, "bub"),
         (701, "pop"), (786, "face"), (827, "xflash"), (863, "relief"), (919, "retry"), (996, "shake"), (1046, "refill"),
         (1101, "clock")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
# ---------------- yordamchilar ----------------
empty = P.empty
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return mc._fcurves(ad.action)

def interp(idb, mode="LINEAR", path=None):
    for fc in fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode

def vis(o, ranges, recursive=True):
    objs = [o] + (list(o.children_recursive) if recursive else [])
    for x in objs:                                   # oldingi ko'rinish kalitlarini tozalash (qayta chaqirish mumkin)
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def pbr(name, folder, scale=1.0, tint=None, proj="BOX", rough_mul=None):
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
    r = img("rough.jpg", True)
    if rough_mul is not None:
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        L.new(r.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], b.inputs["Roughness"])
    else:
        L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def box(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if parent: _par(o, parent)
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: _par(o, parent)
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: _par(o, parent)
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if parent: _par(o, parent)
    return o

def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 300
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c

def shake(cam, f0, f1, amp, seed=1):
    rnd = random.Random(seed)
    sc.frame_set(f0); base = cam.location.copy()
    for f in range(f0, f1):
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)
    cam.location = base; cam.keyframe_insert("location", frame=f1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None, shape=None):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)

WORLD_PARENTS = set()
def _par(o, parent):
    o.parent = parent
    if parent.name in WORLD_PARENTS:
        bpy.context.view_layer.update(); o.matrix_parent_inverse = parent.matrix_world.inverted()

CAMS = {}
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c


def smooth(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

def mesh_obj(name, verts, faces, m=None, parent=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    if m: me.materials.append(m)
    if parent: o.parent = parent
    return o

def revolve(name, prof, m=None, segs=64, a0=0.0, a1=2 * math.pi, parent=None, closed=True):
    """prof: [(x, r)] — X o'qi atrofida aylantirish. Burchak: y = r sin(a), z = r cos(a)."""
    n = len(prof); verts = []; faces = []
    ring = segs if closed else segs + 1
    for j in range(ring):
        a = a0 + (a1 - a0) * j / segs
        for x, r in prof: verts.append((x, r * math.sin(a), r * math.cos(a)))
    for j in range(segs):
        j2 = (j + 1) % ring if closed else j + 1
        for i in range(n - 1):
            faces.append((j * n + i, j * n + i + 1, j2 * n + i + 1, j2 * n + i))
    o = mesh_obj(name, verts, faces, m, parent)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o

def bisect_back(o, fill=False, fill_mat=None):
    """y<0 qismini kesib tashlaydi (kesim: kamera -Y tomondan ichini ko'radi)."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, -1, 0), clear_outer=True)
    if fill:
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        fr = bmesh.ops.holes_fill(bm, edges=edges)
        for f in fr["faces"]:
            f.smooth = False
            if fill_mat is not None: f.material_index = fill_mat
    bm.to_mesh(o.data); bm.free()

# ======================================================================
# 1) XONA (dunyo markazi): devorlar, pol, divan, stol, o'simlik, rasm, soat, chiroq
# ======================================================================
room = empty("room")
floor_m = pbr("floor", "laminate_floor_02", 0.6)
wall_m = pbr("wall", "painted_plaster_wall", 0.5, tint=(0.86, 0.78, 0.68))
wall_m2 = pbr("wall2", "painted_plaster_wall", 0.5, tint=(0.55, 0.66, 0.72))
RW = 2.4            # xona yarim kengligi
BACK = 0.62         # orqa devor (y)
plane("floor", (RW * 2, 6.0), (0, -2.0, 0), floor_m, parent=room)
box("wall_back", (RW * 2, 0.1, 3.0), (0, BACK + 0.05, 1.5), wall_m, parent=room)
box("wall_left", (0.1, 6.0, 3.0), (-RW, -2.0, 1.5), wall_m2, parent=room)
box("wall_right", (0.1, 6.0, 3.0), (RW, -2.0, 1.5), wall_m2, parent=room)
plane("ceiling", (RW * 2, 6.0), (0, -2.0, 2.8), mat("ceil", (0.9, 0.9, 0.88), 0.8), rot=(180, 0, 0), parent=room)
box("skirting", (RW * 2, 0.02, 0.09), (0, BACK - 0.005, 0.045), mat("skirt", (0.92, 0.92, 0.9), 0.4), parent=room)

def ph_model(name, loc, rot=0.0, scale=1.0, parent=room):
    e = empty(name + "_R", loc); e.rotation_euler = (0, 0, R(rot)); e.scale = (scale,) * 3; e.parent = parent
    objs = import_gltf(PH + f"{name}/{name}.gltf", e)
    return e, objs

sofaR, sofa_o = ph_model("Sofa_01", (0, 0.18, 0), 0)
tableR, table_o = ph_model("modern_coffee_table_01", (0.05, -0.95, 0), 90)
plantR, plant_o = ph_model("potted_plant_01", (1.25, 0.3, 0), 30, 1.15)
frameR, frame_o = ph_model("fancy_picture_frame_01", (-0.45, BACK - 0.01, 1.42), 0, 1.0)
clockR, clock_o = ph_model("wall_clock", (0.62, BACK, 1.62), 0, 1.25)
lampR, lamp_o = ph_model("desk_lamp_arm_01", (-0.25, -0.95, 0.0), 200, 1.0)
CLOCK_C = Vector((0.62, BACK - 0.03, 1.62))
bpy.context.view_layer.update()
# o'lchamlarni moslash: stol ustiga chiroq
tlo, thi = bbox(table_o); lampR.location.z = thi.z - 0.005
flo, fhi = bbox(frame_o)
if fhi.y > BACK:      # rasm devorga yopishsin
    frameR.location.y -= (fhi.y - BACK) + 0.005
clo, chi = bbox(clock_o)
print("sofa", bbox(sofa_o), "table", tlo, thi, "frame", flo, fhi, "clock", clo, chi)
hands_clock = {o.name: o for o in clock_o}
min_hand = next(o for o in clock_o if "minute" in o.name)
hour_hand = next(o for o in clock_o if "hours" in o.name)
sec_hand = next(o for o in clock_o if "second" in o.name)

# divan o'rindig'i balandligi (nur bilan o'lchash)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
hit = sc.ray_cast(dg, Vector((0, -0.05, 1.5)), Vector((0, 0, -1)))
SEAT_Z = hit[1].z if hit[0] else 0.45
hit2 = sc.ray_cast(dg, Vector((0, -1.0, 0.75)), Vector((0, 1, 0)))
SEAT_BACK_Y = hit2[1].y if hit2[0] else 0.25
print("seat", SEAT_Z, "back", SEAT_BACK_Y)

# ---------------- Megan ----------------
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
def soften(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                    n.inputs["Roughness"].default_value = 0.6 if "hair" in m.name.lower() else 0.45
                    n.inputs["Coat Weight"].default_value = 0.0
soften(mmeshes)
# Sitting_Idle_4: Hips (0,-0.008,0.602), tizza y=-0.42
MEG = Vector((0.0, SEAT_BACK_Y - 0.30, SEAT_Z + 0.10 - 0.602))
mroot.location = MEG
A_ = lambda f: mc.load_action(f, True)
mc.add_strip(meg, A_("Sitting_Idle_4.fbx"), 1, blend=0, repeat=16.0); sc.render.fps = 24

def W(x, y, z): return MEG + Vector((x, y, z))     # Megan'ga nisbatan dunyo nuqtasi

# qo'llar: IK (bilak), barmoqlar yo'nalishi (Y), kaft (Z), barmoq bukilishi (TRANSFORM)
HAND = {}
for side, s, pa in (("Right", -1, 180), ("Left", 1, 0)):
    fa = meg.pose.bones[f"mixamorig:{side}ForeArm"]; hb = meg.pose.bones[f"mixamorig:{side}Hand"]
    ik_t = empty("ik" + side, (0, 0, 0)); pole = empty("pole" + side, tuple(W(s * 0.7, 0.1, 0.45)))
    k = fa.constraints.new("IK"); k.target = ik_t; k.chain_count = 2; k.use_tail = True; k.pole_target = pole; k.pole_angle = R(pa)
    aim = empty("aim" + side); palm = empty("palm" + side)
    d = hb.constraints.new("DAMPED_TRACK"); d.target = aim; d.track_axis = "TRACK_Y"
    l = hb.constraints.new("LOCKED_TRACK"); l.target = palm; l.lock_axis = "LOCK_Y"; l.track_axis = "TRACK_Z"
    curl = empty("curl" + side)
    for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
        for i in (1, 2, 3):
            pb = meg.pose.bones[f"mixamorig:{side}Hand{fn}{i}"]
            t = pb.constraints.new("TRANSFORM"); t.target = curl; t.map_from = "LOCATION"; t.from_min_x = 0; t.from_max_x = 1
            t.map_to = "ROTATION"; t.owner_space = "LOCAL"; t.target_space = "WORLD"; t.mix_mode_rot = "AFTER"
            t.map_to_x_from = "X"; t.to_min_x_rot = 0; t.to_max_x_rot = R(35 if fn == "Thumb" else 78)
    HAND[side] = dict(ik=ik_t, aim=aim, palm=palm, curl=curl, cons=[k, d, l])
headT = empty("headT", tuple(W(0.0, -0.6, 0.6)))
hdc = meg.pose.bones["mixamorig:Head"].constraints.new("DAMPED_TRACK"); hdc.target = headT; hdc.track_axis = "TRACK_Z"
neckc = meg.pose.bones["mixamorig:Neck"].constraints.new("DAMPED_TRACK"); neckc.target = headT; neckc.track_axis = "TRACK_Z"

# asosiy poza: o'ng musht chap kaftga bosilgan (sinovda tanlangan)
BASE = {"Right": dict(w=(-0.06, -0.21, 0.85), d=(0.15, -1, 0.05), p=(1, 0.15, 0), c=0.95),
        "Left": dict(w=(0.065, -0.37, 0.85), d=(-1, 0.05, 0.05), p=(0, 1, 0), c=0.45)}
OPEN = {"Right": dict(w=(-0.17, -0.30, 0.70), d=(0.2, -1, 0.5), p=(0.6, 0, 1), c=0.08),
        "Left": dict(w=(0.17, -0.31, 0.70), d=(-0.2, -1, 0.5), p=(-0.6, 0, 1), c=0.08)}
def pose(f, side, w, d, p, c, interp_mode="BEZIER"):
    h = HAND[side]; w = W(*w)
    key(h["ik"], f, loc=tuple(w))
    key(h["aim"], f, loc=tuple(w + Vector(d).normalized() * 0.3))
    key(h["palm"], f, loc=tuple(w + Vector(p).normalized() * 0.3))
    key(h["curl"], f, loc=(c, 0, 0))
def pose_both(f, P_, dR=(0, 0, 0), dL=(0, 0, 0), cR=None, cL=None):
    for side, dv, cc in (("Right", dR, cR), ("Left", dL, cL)):
        q = P_[side]
        pose(f, side, tuple(Vector(q["w"]) + Vector(dv)), q["d"], q["p"], q["c"] if cc is None else cc)
def squeeze(F, crack=True):
    """F — "qirs" kadri: musht kaftga bosiladi, bo'g'imlar qirsillaydi."""
    pose_both(F - 7, BASE)
    pose_both(F - 1, BASE, dR=(0.004, -0.018, -0.004), dL=(0.0, 0.012, 0.0), cR=1.0, cL=0.62)
    if crack:
        pose_both(F + 1, BASE, dR=(0.006, -0.024, -0.008), dL=(0.0, 0.016, -0.004), cR=1.0, cL=0.66)
    pose_both(F + 9, BASE)
def influence(keys):
    for side in HAND:
        for con in HAND[side]["cons"]:
            for f, v in keys: con.influence = v; con.keyframe_insert("influence", frame=f)
def head_look(f, x, y, z, infl=0.75):
    key(headT, f, loc=tuple(W(x, y, z)))
    for c in (hdc, neckc):
        c.influence = infl if c is hdc else infl * 0.4; c.keyframe_insert("influence", frame=f)

# --- harakat jadvali ---
H0, H1 = S["hook"]; PU0, PU1 = S["pull"]; FA0, FA1 = S["face"]; XF0, XF1 = S["xflash"]; RL0, RL1 = S["relief"]
RT0, RT1 = S["retry"]; SH0, SH1 = S["shake"]; CL0, CL1 = S["clock"]; XR0, XR1 = S["xray"]
CRACK1 = 26; CRACK_X = 188; CRACK2 = 819; CRACK_XF = 830
influence([(1, 1.0), (PU0 - 1, 1.0), (PU0, 0.0), (PU0 + 8, 0.0), (PU0 + 26, 1.0), (RL0 - 1, 1.0), (RL0 + 10, 0.0),
           (RL1 - 2, 0.0), (RT0, 1.0), (CL0 - 1, 1.0), (CL0, 0.0)])
pose_both(1, BASE); squeeze(CRACK1); pose_both(60, BASE); squeeze(68, crack=False)
pose_both(XR0, BASE); squeeze(CRACK_X - 14, crack=False); squeeze(CRACK_X)
# pull: qo'llar tizzadan ko'tarilib, barmoqlar bukiladi, keyin musht kaftga
pose_both(PU0, OPEN); pose_both(PU0 + 16, OPEN, dR=(0, 0, 0.12), dL=(0, 0, 0.12))
pose_both(PU0 + 34, BASE, cR=0.5, cL=0.2); pose_both(PU0 + 50, BASE); squeeze(PU0 + 62); pose_both(PU1, BASE)
pose_both(FA0, BASE); squeeze(CRACK2); squeeze(CRACK_XF)
pose_both(RL0, BASE); pose_both(RL0 + 14, OPEN, dR=(-0.04, 0.05, -0.05), dL=(0.04, 0.05, -0.05))
pose_both(RT0, BASE)
for F in (RT0 + 18, RT0 + 40, RT0 + 62):
    squeeze(F, crack=False)
# qo'llar titraydi (zo'r berib siqadi)
rj = random.Random(3)
for f in range(RT0 + 10, RT1, 2):
    dj = Vector((rj.uniform(-1, 1), rj.uniform(-1, 1), rj.uniform(-1, 1))) * 0.003
    pose_both(f, BASE, dR=tuple(dj + Vector((0, -0.01, 0))), dL=tuple(-dj + Vector((0, 0.008, 0))), cR=1.0, cL=0.6)
pose_both(SH0, BASE); pose_both(SH1, BASE)
# bosh: qo'llarga qaraydi; yengil tortishda tepaga; chayqash
head_look(1, 0.0, -0.6, 0.6)
head_look(PU0, 0.0, -0.9, 0.95); head_look(PU0 + 30, 0.0, -0.6, 0.6)
head_look(CRACK2 - 2, 0.0, -0.6, 0.6); head_look(CRACK2 + 6, 0.05, -0.9, 1.0)
head_look(RL0, 0.05, -0.9, 1.0); head_look(RL0 + 18, 0.1, -0.8, 1.7, 0.85); head_look(RL1, 0.1, -0.8, 1.65, 0.85)
head_look(RT0, 0.0, -0.6, 0.6)
for i, f in enumerate(range(SH0 + 4, SH1, 7)):
    head_look(f, (0.22 if i % 2 == 0 else -0.22) * (1 - 0.1 * i), -0.75, 1.0)
head_look(SH1, 0.0, -0.8, 1.05)
head_look(CL0, 0.0, -0.6, 0.6)

# ======================================================================
# 2) BO'G'IM KESIMI (J = (30,0,0)), masshtab: bo'g'im ~1 m
# ======================================================================
J = Vector((30, 0, 0))
jnt = empty("joint", tuple(J)); jnt.rotation_euler = (0, R(-90), 0)   # suyak o'qi vertikal (9:16)
JR = Euler((0, R(-90), 0)).to_matrix()
C_H = -0.32; RH = 0.36; RC = 0.46          # kaft suyagi boshi markazi, radiusi; falanga kosachasi radiusi

def bone_material(name, center, rad, xmin):
    """Suyak (fil suyagi rang) + tog'ay (ko'kish-oq, yaltiroq): obyekt koordinatasida markazdan masofa < rad bo'lsa tog'ay."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    dist = P.math_n(N, L, "DISTANCE", tc.outputs["Object"], tuple(center), vec=True)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    k1 = P.math_n(N, L, "LESS_THAN", dist, rad)
    k2 = P.math_n(N, L, "GREATER_THAN", sep.outputs[0], xmin)
    k = P.math_n(N, L, "MULTIPLY", k1, k2)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18.0; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bone_c = N.new("ShaderNodeMix"); bone_c.data_type = "RGBA"
    bone_c.inputs[6].default_value = (0.62, 0.52, 0.38, 1); bone_c.inputs[7].default_value = (0.78, 0.7, 0.55, 1)
    L.new(nz.outputs["Fac"], bone_c.inputs[0])
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"; L.new(k, col.inputs[0])
    L.new(bone_c.outputs[2], col.inputs[6]); col.inputs[7].default_value = (0.55, 0.72, 0.9, 1)
    L.new(col.outputs[2], b.inputs["Base Color"])
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", k, -0.4), 0.55), b.inputs["Roughness"])
    L.new(P.math_n(N, L, "MULTIPLY", k, 0.8), b.inputs["Coat Weight"])
    b.inputs["Subsurface Weight"].default_value = 0.25; b.inputs["Subsurface Scale"].default_value = 0.03
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
    L.new(P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], P.math_n(N, L, "SUBTRACT", 1.0, k)), bump.inputs["Height"])
    L.new(bump.outputs[0], b.inputs["Normal"])
    return m

prof_mc = [(-2.8, 0.0), (-2.8, 0.19), (-2.2, 0.2), (-1.2, 0.2), (-0.8, 0.23), (-0.62, 0.29)]
for i in range(26):
    ph = R(112 - 112 * i / 25); prof_mc.append((C_H + RH * math.cos(ph), RH * math.sin(ph)))
mcb = revolve("metacarpal", prof_mc, bone_material("bone_mc", (C_H, 0, 0), RH + 0.012, C_H - 0.04), 72, parent=jnt)
prof_ph = []
for i in range(18):
    r = 0.33 * i / 17; prof_ph.append((C_H + math.sqrt(RC * RC - r * r), r))
prof_ph += [(0.03, 0.37), (0.10, 0.385), (0.22, 0.33), (0.45, 0.24), (0.8, 0.2), (2.0, 0.19), (2.8, 0.19), (2.8, 0.0)]
phx = revolve("phalanx", prof_ph, bone_material("bone_ph", (C_H, 0, 0), RC + 0.015, -1.0), 72, parent=jnt)
PHX0 = Vector((0, 0, 0))
# suyaklar ham kesiladi (kesim yuzida g'ovak ilik), aks holda bo'shliq markazi suyak orqasida qoladi
marrow = bpy.data.materials.new("marrow"); marrow.use_nodes = True
N = marrow.node_tree.nodes; L = marrow.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 48.0
vo.feature = "DISTANCE_TO_EDGE"; L.new(tc.outputs["Object"], vo.inputs["Vector"])
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.02; cr.color_ramp.elements[0].color = (0.80, 0.72, 0.58, 1)
cr.color_ramp.elements[1].position = 0.12; cr.color_ramp.elements[1].color = (0.72, 0.52, 0.40, 1)
L.new(vo.outputs["Distance"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.6; b.inputs["Subsurface Weight"].default_value = 0.2
for o in (mcb, phx):
    o.data.materials.append(marrow); bisect_back(o, fill=True, fill_mat=1)

# kapsula (yarim, ichi ko'rinadi) va sinovial suyuqlik
def cap_r(x):
    pts = [(-0.78, 0.26), (-0.55, 0.42), (-0.3, 0.52), (0.0, 0.56), (0.25, 0.53), (0.5, 0.43), (0.72, 0.24)]
    for (x0, r0), (x1, r1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0); return r0 + (r1 - r0) * (t * t * (3 - 2 * t))
    return 0.24
CAPX = [(-0.78 + 1.5 * i / 40) for i in range(41)]
cap_m = mat("capsule", (0.78, 0.32, 0.30), 0.35, sss=0.5, coat=0.4)
cn = cap_m.node_tree.nodes; cl = cap_m.node_tree.links
wv = cn.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 6.0; wv.inputs["Distortion"].default_value = 4.0
wv.bands_direction = "X"; cbmp = cn.new("ShaderNodeBump"); cbmp.inputs["Strength"].default_value = 0.35
cl.new(wv.outputs["Fac"], cbmp.inputs["Height"]); cl.new(cbmp.outputs[0], cn["Principled BSDF"].inputs["Normal"])
cn["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.05
capsule = revolve("capsule", [(x, cap_r(x)) for x in CAPX], cap_m, 64, a0=0.0, a1=math.pi, parent=jnt, closed=False)
sol = capsule.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.045; sol.offset = 1.0

fl_m = bpy.data.materials.new("synovial"); fl_m.use_nodes = True
N = fl_m.node_tree.nodes; L = fl_m.node_tree.links; out = N["Material Output"]; N.remove(N["Principled BSDF"])
trn = N.new("ShaderNodeBsdfTransparent"); trn.inputs[0].default_value = (1.0, 0.86, 0.45, 1)
gls = N.new("ShaderNodeBsdfGlossy"); gls.inputs["Roughness"].default_value = 0.25
emf = N.new("ShaderNodeEmission"); emf.inputs[0].default_value = (1.0, 0.75, 0.3, 1); emf.inputs[1].default_value = 0.08
fr = N.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.15
mx1 = N.new("ShaderNodeMixShader"); L.new(fr.outputs[0], mx1.inputs[0]); L.new(trn.outputs[0], mx1.inputs[1]); L.new(gls.outputs[0], mx1.inputs[2])
ad1 = N.new("ShaderNodeAddShader"); L.new(mx1.outputs[0], ad1.inputs[0]); L.new(emf.outputs[0], ad1.inputs[1])
L.new(ad1.outputs[0], out.inputs[0])
fprof = [(-0.74, 0.0)] + [(x, cap_r(x) - 0.012) for x in CAPX[1:-1]] + [(0.70, 0.0)]
fluid = revolve("fluid", fprof, fl_m, 64, parent=jnt)
bisect_back(fluid, fill=True)

# vakuum: falanga +0.22 ga siljiydi, kapsula o'rtasi ichkariga tortiladi (shape key)
VAC = 0.22
def vac_deform(o):
    o.shape_key_add(name="Basis", from_mix=False); kb = o.shape_key_add(name="vac", from_mix=False); kb.value = 0.0
    for i, v in enumerate(o.data.vertices):
        x, y, z = v.co; r = math.hypot(y, z)
        nx = x + VAC * smooth(-0.35, 0.55, x)
        sq = 1.0 - 0.2 * math.exp(-((x - 0.05) / 0.32) ** 2) if r > 0.2 else 1.0
        kb.data[i].co = (nx, y * sq, z * sq)
    return kb
vk_cap = vac_deform(capsule); vk_fl = vac_deform(fluid)

# ---- gaz zarralari ----
def inside_fluid(x, rho):
    if rho > cap_r(x) - 0.035 or x < -0.7 or x > 0.66: return False
    if x < C_H and rho < 0.30: return False
    d = math.hypot(x - C_H, rho)
    if d < RH + 0.02: return False
    if x > -0.03 and d > RC - 0.02 and rho < 0.39: return False
    return True
gas_m = mat("gas", (0.75, 0.95, 1.0), 0.2, emit=3.0)
rg = random.Random(11); DOTS = []
proto = bpy.data.meshes.new("dot")
bmd = bmesh.new(); bmesh.ops.create_icosphere(bmd, subdivisions=2, radius=1.0); bmd.to_mesh(proto); bmd.free()
for p_ in proto.polygons: p_.use_smooth = True
proto.materials.append(gas_m)
while len(DOTS) < 200:
    x = rg.uniform(-0.65, 0.62); rho = rg.uniform(0.0, 0.56); th = rg.uniform(0.04, math.pi - 0.04)
    if not inside_fluid(x, rho): continue
    o = bpy.data.objects.new(f"dot{len(DOTS)}", proto); sc.collection.objects.link(o); o.parent = jnt
    DOTS.append(dict(o=o, x=x, rho=rho, th=th, r=rg.uniform(0.006, 0.014), ph=rg.uniform(0, 6.28),
                     t0=rg.uniform(0, 1), dt=rg.uniform(0, 1)))

# ---- pufakcha, zarba to'lqini, chaqnash ----
BC = Vector((((C_H + RH) + (C_H + RC + VAC)) / 2, 0.0, 0.0))   # bo'shliq markazi (vakuumdan keyin)
bub_m = bpy.data.materials.new("bubble2"); bub_m.use_nodes = True
N = bub_m.node_tree.nodes; L = bub_m.node_tree.links; out = N["Material Output"]; N.remove(N["Principled BSDF"])
gl = N.new("ShaderNodeBsdfGlass"); gl.inputs["IOR"].default_value = 1.0 / 1.33; gl.inputs["Roughness"].default_value = 0.0
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
emb = N.new("ShaderNodeEmission"); emb.inputs[0].default_value = (0.6, 0.9, 1.0, 1)
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 3.0), 6.0), emb.inputs[1])
ad = N.new("ShaderNodeAddShader"); L.new(gl.outputs[0], ad.inputs[0]); L.new(emb.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], out.inputs[0])
bubble = sphere("bubble", 1.0, tuple(BC), bub_m, sub=4, parent=jnt)
shock_m = bpy.data.materials.new("shock"); shock_m.use_nodes = True
N = shock_m.node_tree.nodes; L = shock_m.node_tree.links; out = N["Material Output"]; N.remove(N["Principled BSDF"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.2
ems = N.new("ShaderNodeEmission"); ems.inputs[0].default_value = (0.8, 0.95, 1.0, 1)
sv = N.new("ShaderNodeValue"); sv.name = "glow"; sv.outputs[0].default_value = 0.0
L.new(P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "POWER", lw.outputs["Facing"], 2.0), sv.outputs[0]), ems.inputs[1])
trs = N.new("ShaderNodeBsdfTransparent"); ads = N.new("ShaderNodeAddShader")
L.new(trs.outputs[0], ads.inputs[0]); L.new(ems.outputs[0], ads.inputs[1]); L.new(ads.outputs[0], out.inputs[0])
shock = sphere("shock", 1.0, tuple(BC), shock_m, sub=4, parent=jnt)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.025, major_segments=64, minor_segments=8, location=tuple(J + BC),
                                 rotation=(0, R(90), 0))
ring = bpy.context.object; ring.name = "ring"; ring.data.materials.append(shock_m); ring.parent = jnt
ring.location = BC; bpy.ops.object.transform_apply(rotation=True)

# ---- vaqt jadvali ----
MY0, MY1 = S["myth"]; AN0, AN1 = S["anat"]; GA0, GA1 = S["gas"]; VA0, VA1 = S["vac"]; BU0, BU1 = S["bub"]
PO0, PO1 = S["pop"]; RF0, RF1 = S["refill"]
EMAS = 123; POP = 772; BUB_START = 618
def vac_amount(f):
    if f < VA0 + 10: return 0.0
    if f < VA0 + 80: return smooth(VA0 + 10, VA0 + 80, f)
    if f <= POP: return 1.0
    if f < RF0: return 1.0
    return 1.0 - smooth(RF0, RF0 + 30, f)
def bub_r(f):
    if f < BUB_START or f > POP + 1: return 0.0
    if f >= POP + 1: return 0.0
    t = smooth(BUB_START, POP - 6, f); return 0.005 + 0.115 * t ** 0.8 + 0.004 * math.sin(f * 0.9) * t
ph_ = phx
for f in [1, MY0 - 1] + list(range(MY0, MY1 + 1, 2)) + [MY1 + 1, VA0] + list(range(VA0 + 10, VA0 + 81, 5)) + [RF0] + list(range(RF0, RF0 + 31, 5)):
    v = vac_amount(f)
    if MY0 <= f <= MY1:
        a = 9 * math.sin((f - MY0) * 0.42) if f < EMAS else 0.0
        ph_.location = (-0.09, 0, 0); ph_.rotation_euler = (0, R(a * 0.35), R(a))
    else:
        ph_.location = (VAC * v, 0, 0); ph_.rotation_euler = (0, 0, 0)
    ph_.keyframe_insert("location", frame=f); ph_.keyframe_insert("rotation_euler", frame=f)
    for kb in (vk_cap, vk_fl):
        kb.value = v if not (MY0 <= f <= MY1) else 0.0; kb.keyframe_insert("value", frame=f)
# pufakcha
for f in [1, BUB_START - 1] + list(range(BUB_START, POP + 1, 2)) + [POP, POP + 1, POP + 2]:
    r = bub_r(f) if f <= POP else 0.0
    bubble.scale = (max(r, 1e-4) * (1 + 0.04 * math.sin(f * 1.3)),) * 2 + (max(r, 1e-4) * (1 - 0.04 * math.sin(f * 1.3)),)
    bubble.keyframe_insert("scale", frame=f)
vis(bubble, [(BUB_START, POP)])
for f, s_, g in ((POP - 1, 0.05, 0.0), (POP, 0.08, 18.0), (POP + 3, 0.45, 8.0), (POP + 8, 0.9, 2.0), (POP + 14, 1.3, 0.0)):
    shock.scale = (s_,) * 3; shock.keyframe_insert("scale", frame=f); P.mat_value(shock_m, "glow", f, g)
    ring.scale = (s_ * 1.2,) * 3; ring.keyframe_insert("scale", frame=f)
vis(shock, [(POP, POP + 14)]); vis(ring, [(POP, POP + 14)])
# mayda parchalar (pufakcha yorilganda)
for i in range(26):
    d_ = Vector((rg.uniform(-1, 1), rg.uniform(0.0, 1), rg.uniform(-1, 1))).normalized()
    o = sphere(f"frag{i}", 1.0, tuple(BC), gas_m, sub=1, parent=jnt); o.scale = (0.01,) * 3
    for k in range(0, 14, 2):
        o.location = BC + d_ * (0.03 + 0.45 * (1 - math.exp(-k / 4.0))); o.keyframe_insert("location", frame=POP + k)
        o.scale = (0.012 * (1 - k / 14) + 0.001,) * 3; o.keyframe_insert("scale", frame=POP + k)
    vis(o, [(POP, POP + 12)])
# uchqunlar (afsona: suyaklar ishqalanadi)
spark_m = mat("spark", (1.0, 0.6, 0.2), 0.3, emit=40.0)
for i in range(36):
    t0 = rg.randint(MY0 + 4, EMAS - 8)
    side = rg.choice((-1, 1)); p0 = Vector((-0.02, rg.uniform(0.0, 0.12), side * rg.uniform(0.2, 0.3)))
    v0 = Vector((rg.uniform(-0.3, 0.6), rg.uniform(-0.6, 0.1), side * rg.uniform(0.3, 0.9))) * 0.05
    o = sphere(f"spark{i}", 1.0, tuple(p0), spark_m, sub=1, parent=jnt); o.scale = (0.012,) * 3
    for k in range(0, 9):
        o.location = p0 + v0 * k + Vector((0, 0, -0.004 * k * k)); o.keyframe_insert("location", frame=t0 + k)
    o.scale = (0.012,) * 3; o.keyframe_insert("scale", frame=t0); o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=t0 + 8)
    vis(o, [(t0, t0 + 8)])

# gaz zarralari harakati
J_SHOTS = rng("myth", "anat", "gas", "vac", "bub", "pop", "refill")
KEYF = sorted(set(f for a, b in J_SHOTS for f in list(range(a - 1, b + 2, 3)) + [b + 1]))
NBUB = 140
for i, d in enumerate(DOTS):
    o = d["o"]; start = BUB_START + 6 + d["t0"] * 120
    for f in KEYF:
        v = vac_amount(f)
        x = d["x"] + VAC * v * smooth(-0.35, 0.55, d["x"]) + 0.012 * math.sin(f * 0.05 + d["ph"])
        rho = d["rho"] * (1 - 0.15 * v * math.exp(-((d["x"] - 0.05) / 0.32) ** 2)) + 0.008 * math.sin(f * 0.07 + d["ph"] * 2)
        th = d["th"] + 0.02 * math.sin(f * 0.04 + d["ph"])
        p = Vector((x, rho * math.sin(th), rho * math.cos(th)))
        s_ = d["r"]
        if i < NBUB and f >= start:          # pufakchaga tortiladi va yutiladi
            t = smooth(start, start + 34, f)
            br = bub_r(min(f, POP))
            tgt = BC + (p - BC).normalized() * br
            p = p.lerp(tgt, t ** 1.5)
            if t >= 0.999 or f > POP: s_ = 0.0
        if f > POP and i >= NBUB:
            s_ = d["r"] * 0.6
        if RF0 - 1 <= f <= RF1 + 1 and f > POP:           # qayta yig'ilish (time-lapse)
            s_ = d["r"] * smooth(RF0 + d["dt"] * 40, RF0 + d["dt"] * 40 + 8, f)
        o.location = p; o.scale = (max(s_, 1e-5),) * 3
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)

# ======================================================================
# 3) RENTGEN QO'L (shaffof Megan + suyaklar)
# ======================================================================
xray_body = P.xray_material("xray_body", col=(0.35, 0.75, 1.0), strength=1.3, base=0.012)
ghosts = []
for o in mmeshes:
    g = o.copy(); g.name = o.name + "_xray"; sc.collection.objects.link(g)
    for slot in g.material_slots: slot.link = "OBJECT"; slot.material = xray_body
    ghosts.append(g)
xb_m = mat("xbone", (0.9, 0.95, 1.0), 0.4, emit=2.2)
kn_m = P.pulse_material("knuckle", (1.0, 0.9, 0.6), base_emit=0.0)
X_SHOTS = rng("xray", "xflash")
XKEY = sorted(set(f for a, b in X_SHOTS for f in range(a - 1, b + 2)))
FING = ("Thumb", "Index", "Middle", "Ring", "Pinky")
segs = []; knucks = []
def bp(side, name): return f"mixamorig:{side}{name}"
for side in ("Right", "Left"):
    segs.append((side, ("ForeArm", "Hand"), 0.0075, (0.012, 0)))
    segs.append((side, ("ForeArm", "Hand"), 0.006, (-0.012, 0)))
    for fn in FING:
        chain = ["Hand"] + [f"Hand{fn}{i}" for i in (1, 2, 3, 4)]
        for a_, b_ in zip(chain, chain[1:]):
            segs.append((side, (a_, b_), 0.0042 if a_ == "Hand" else 0.0036, None))
        if fn != "Thumb": knucks.append((side, f"Hand{fn}1"))
SEG_O = []
for i, (side, (a_, b_), rad, off) in enumerate(segs):
    t = P.tube(f"xb{i}", [(0, 0, 0), (0, 0, 0.01)], rad, xb_m); SEG_O.append(t)
KN_O = [sphere(f"kn{i}", 0.0075, (0, 0, 0), kn_m, sub=2) for i in range(len(knucks))]
for f in XKEY:
    sc.frame_set(f); bpy.context.view_layer.update(); Mw = meg.matrix_world
    for o, (side, (a_, b_), rad, off) in zip(SEG_O, segs):
        pa = Mw @ meg.pose.bones[bp(side, a_)].head; pb_ = Mw @ meg.pose.bones[bp(side, b_)].head
        if off:
            xax = (Mw.to_3x3() @ meg.pose.bones[bp(side, a_)].matrix.to_3x3()).col[0].normalized()
            pa = pa + xax * off[0]; pb_ = pb_ + xax * off[0] * 0.6
        if a_ == "Hand": pa = pa.lerp(pb_, 0.14)
        d_ = pb_ - pa; p1 = pa + d_ * 0.07; p2 = pb_ - d_ * 0.07
        sp = o.data.splines[0]
        sp.points[0].co = (*p1, 1); sp.points[1].co = (*p2, 1)
        sp.points[0].keyframe_insert("co", frame=f); sp.points[1].keyframe_insert("co", frame=f)
    for o, (side, b_) in zip(KN_O, knucks):
        o.location = Mw @ meg.pose.bones[bp(side, b_)].head; o.keyframe_insert("location", frame=f)
for o in SEG_O + KN_O: vis(o, X_SHOTS, recursive=False)
for g in ghosts: vis(g, X_SHOTS, recursive=False)
FLASHES = [CRACK_X, CRACK_XF, CRACK_XF + 6, CRACK_XF + 12]
P.mat_value(kn_m, "glow", 1, 0.0)
for F in FLASHES:
    P.mat_value(kn_m, "glow", F - 1, 0.0); P.mat_value(kn_m, "glow", F, 40.0); P.mat_value(kn_m, "glow", F + 5, 0.0)
interp(kn_m.node_tree, "LINEAR")

# ======================================================================
# 4) KAMERALAR
# ======================================================================
FC = W(-0.03, -0.31, 0.86)        # musht markazi
fcT = empty("fistT", tuple(FC))
faceE = empty("meg_face")
c_ = faceE.constraints.new("CHILD_OF"); c_.target = meg; c_.subtarget = "mixamorig:Head"
c_.use_scale_x = c_.use_scale_y = c_.use_scale_z = False; c_.inverse_matrix = Matrix.Identity(4)
faceT = empty("faceT", (0, 0.07, 0.09), faceE)
JT = lambda x, y, z: tuple(J + JR @ Vector((x, y, z)))
def crash(c, F, l0, l1, n=3): lens_keys(c, ((F - 1, l0), (F + n, l1)))
# 1 ilgak
c = shot_cam("hook", tuple(W(-0.30, -0.80, 0.74)), fcT, 40, 2.2, focus=fcT)
key(c, H0, loc=tuple(W(-0.30, -0.80, 0.74))); key(c, CRACK1 - 1, loc=tuple(W(-0.22, -0.64, 0.78)))
key(c, H1, loc=tuple(W(-0.18, -0.58, 0.80)))
lens_keys(c, ((H0, 36), (CRACK1 - 1, 40), (CRACK1 + 2, 70), (H1, 74))); shake(c, CRACK1, CRACK1 + 12, 0.006, 1)
# 2 afsona
jT0 = empty("jT0", JT(0.0, 0.0, 0.05))
c = shot_cam("myth", JT(-0.6, -2.3, 0.55), jT0, 32, 5.6, focus=jT0)
key(c, MY0, loc=JT(-0.6, -2.3, 0.55)); key(c, EMAS - 1, loc=JT(-0.35, -2.0, 0.45)); key(c, MY1, loc=JT(-0.3, -1.9, 0.42))
lens_keys(c, ((MY0, 32), (EMAS - 1, 34), (EMAS + 2, 44), (MY1, 46))); shake(c, EMAS, EMAS + 12, 0.05, 2)
# 3 rentgen qo'l: ko'krakdan bo'g'imga
xT = empty("xrayT"); key(xT, XR0, loc=tuple(W(0.0, -0.2, 0.95))); key(xT, XR0 + 40, loc=tuple(FC))
c = shot_cam("xray", tuple(W(0.45, -1.5, 1.05)), xT, 30, 3.5, focus=fcT)
key(c, XR0, loc=tuple(W(0.45, -1.5, 1.05))); key(c, CRACK_X - 2, loc=tuple(W(0.08, -0.62, 0.95))); key(c, XR1, loc=tuple(W(0.05, -0.56, 0.93)))
lens_keys(c, ((XR0, 28), (CRACK_X - 1, 45), (CRACK_X + 2, 75), (XR1, 80))); shake(c, CRACK_X, CRACK_X + 12, 0.005, 3)
# 4 anatomiya: aylanma
anT = empty("anT", JT(0.0, 0.1, 0.1))
c = shot_cam("anat", JT(0, -1.9, 0.7), anT, 30, 4.0, focus=anT)
for f in range(AN0, AN1 + 1, 3):
    t = (f - AN0) / (AN1 - AN0); a = R(-40 + 70 * t)
    key(c, f, loc=JT(1.9 * math.sin(a), -1.9 * math.cos(a), 0.75 - 0.35 * t))
# 5 gaz (makro, bokeh)
gT = empty("gasT", JT(0.12, 0.12, 0.42))
c = shot_cam("gas", JT(0.09, -0.95, 0.12), gT, 45, 2.8, focus=gT)
key(c, GA0, loc=JT(0.12, -1.0, 0.25)); key(c, GA1, loc=JT(0.09, -0.72, 0.05))
key(gT, GA0, loc=JT(0.09, 0.02, 0.15)); key(gT, GA1, loc=JT(0.09, 0.02, 0.02))
# 6 tortish: xona, pastdan keng
puT = empty("pullT", tuple(W(0.0, -0.15, 0.85)))
c = shot_cam("pull", tuple(W(-1.3, -1.25, 0.42)), puT, 18, 4.0, focus=fcT)
key(c, PU0, loc=tuple(W(-1.35, -1.3, 0.42))); key(c, PU1, loc=tuple(W(-1.0, -1.05, 0.62)))
# 7 vakuum
vT = empty("vacT", JT(0.1, 0.0, 0.0))
c = shot_cam("vac", JT(0.1, -2.1, 0.15), vT, 30, 5.0, focus=vT)
key(c, VA0, loc=JT(0.05, -2.15, 0.25)); key(c, VA1, loc=JT(0.2, -1.6, 0.1))
# 8 pufakcha tug'iladi
bT = empty("bubT", JT(*BC))
c = shot_cam("bub", JT(0.3, -1.15, 0.25), bT, 35, 3.5, focus=bT)
key(c, BU0, loc=JT(0.35, -1.25, 0.3)); key(c, BU1, loc=JT(0.24, -0.85, 0.1))
# 9 yorilish
c = shot_cam("pop", JT(*(BC + Vector((-0.05, -0.45, 0.07)))), bT, 55, 4.0, focus=bT)
key(c, PO0, loc=JT(*(BC + Vector((-0.06, -0.48, 0.08))))); key(c, POP - 1, loc=JT(*(BC + Vector((-0.02, -0.34, 0.03)))))
key(c, PO1, loc=JT(*(BC + Vector((-0.01, -0.36, 0.02)))))
shake(c, POP, POP + 12, 0.012, 4)
# 10 yuz
c = shot_cam("face", tuple(W(0.25, -0.78, 0.92)), faceT, 55, 1.8, focus=faceT)
key(c, FA0, loc=tuple(W(0.27, -0.80, 0.90))); key(c, FA1, loc=tuple(W(0.20, -0.68, 0.94)))
lens_keys(c, ((FA0, 50), (CRACK2 - 1, 54), (CRACK2 + 2, 70), (FA1, 72))); shake(c, CRACK2, CRACK2 + 8, 0.004, 5)
# 11 rentgen chaqnash
c = shot_cam("xflash", tuple(W(-0.22, -0.66, 1.08)), fcT, 35, 3.0, focus=fcT)
key(c, XF0, loc=tuple(W(-0.24, -0.70, 1.10))); key(c, XF1, loc=tuple(W(-0.16, -0.55, 1.02)))
lens_keys(c, ((XF0, 35), (CRACK_XF - 1, 36), (CRACK_XF + 2, 60), (XF1, 66))); shake(c, CRACK_XF, CRACK_XF + 16, 0.004, 6)
# 12 yengil tortish: past burchak, aylanma
rlT = empty("relT", tuple(W(0.0, -0.1, 0.95)))
c = shot_cam("relief", tuple(W(0.9, -1.0, 0.5)), rlT, 18, 4.0, focus=faceT)
for f in range(RL0, RL1 + 1, 4):
    t = (f - RL0) / (RL1 - RL0); a = R(35 - 40 * t)
    key(c, f, loc=tuple(W(0.75 + 0.5 * math.sin(a), -0.95 - 0.2 * math.cos(a), 0.5 + 0.1 * t)))
# 13 qayta urinish: qo'llar makro, qo'l kamera
c = shot_cam("retry", tuple(W(0.30, -0.72, 0.78)), fcT, 34, 4.0, focus=fcT)
key(c, RT0, loc=tuple(W(0.34, -0.78, 0.76))); key(c, RT1, loc=tuple(W(0.24, -0.64, 0.80)))
# 14 bosh chayqash
c = shot_cam("shake", tuple(W(-0.3, -0.75, 1.1)), faceT, 60, 1.8, focus=faceT)
key(c, SH0, loc=tuple(W(-0.32, -0.80, 1.08))); key(c, SH1, loc=tuple(W(-0.24, -0.66, 1.12)))
# 15 qayta yig'ilish (time-lapse)
rfT = empty("rfT", JT(0.05, 0.05, 0.1))
c = shot_cam("refill", JT(-0.9, -1.6, 0.9), rfT, 32, 4.5, focus=rfT)
key(c, RF0, loc=JT(-0.9, -1.6, 0.9)); key(c, RF1, loc=JT(-0.55, -1.45, 0.55))
# 16 soat
ckT = empty("clockT", tuple(CLOCK_C))
c = shot_cam("clock", (0.42, -0.62, 1.32), ckT, 40, 2.8, focus=ckT)
key(c, CL0, loc=(0.40, -0.70, 1.30)); key(c, CL1, loc=(0.52, -0.22, 1.48))
# soat millari: 20 daqiqa time-lapse (oldin real vaqt)
for o, rev in ((min_hand, 120.0), (hour_hand, 10.0), (sec_hand, 360.0 * 8)):
    o.rotation_mode = "XYZ"; r0 = o.rotation_euler.copy()
    o.keyframe_insert("rotation_euler", frame=1); o.keyframe_insert("rotation_euler", frame=CL0)
    o.rotation_euler = (r0.x, r0.y + R(rev), r0.z); o.keyframe_insert("rotation_euler", frame=CL1 - 2)
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
# sinov
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ko'rinish
ROOM_SHOTS = rng("hook", "pull", "face", "relief", "retry", "shake", "clock")
vis(room, ROOM_SHOTS)
for o in mmeshes: vis(o, ROOM_SHOTS, recursive=False)
for o in (mcb, phx, capsule, fluid): vis(o, J_SHOTS, recursive=False)
for d in DOTS: vis(d["o"], J_SHOTS, recursive=False)

# ======================================================================
# 5) YORUG'LIK VA DUNYO
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; N.remove(N["Background"])
tcw = N.new("ShaderNodeTexCoord")
mp = N.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, R(40)); L.new(tcw.outputs["Generated"], mp.inputs[0])
e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + "studio_small_09.hdr"); L.new(mp.outputs[0], e.inputs[0])
bg_st = N.new("ShaderNodeBackground"); L.new(e.outputs[0], bg_st.inputs[0])
bg_dk = N.new("ShaderNodeBackground"); bg_dk.inputs[0].default_value = (0.006, 0.012, 0.03, 1)
a1 = N.new("ShaderNodeAddShader"); L.new(bg_st.outputs[0], a1.inputs[0]); L.new(bg_dk.outputs[0], a1.inputs[1])
L.new(a1.outputs[0], out.inputs["Surface"])
WL = {n: ((0.22, 0.0) if (S[n] in ROOM_SHOTS) else (0.0, 1.0)) for f, n in SHOTS}
for f, n in SHOTS:
    s1, s3 = WL[n]
    for bgn, v in ((bg_st, s1), (bg_dk, s3)):
        bgn.inputs[1].default_value = v; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# xona
RM = ROOM_SHOTS
roomT = empty("roomT", tuple(W(0, -0.2, 0.9)))
area("room_key", tuple(W(-1.3, -1.7, 2.1)), 1.4, (1.0, 0.9, 0.78), lights_for(RM, 150.0), target=roomT)
area("room_win", tuple(W(2.0, -0.7, 1.6)), 1.6, (0.8, 0.9, 1.0), lights_for(RM, 120.0), target=roomT)
area("room_rim", tuple(W(0.7, 0.35, 2.2)), 0.8, (1.0, 0.75, 0.5), lights_for(RM, 90.0), target=roomT)
area("room_ceil", (0, -1.2, 2.7), 2.0, (1.0, 0.95, 0.88), lights_for(RM, 50.0), target=empty("ceilT", (0, -1.2, 0)))
fk = area("face_key", tuple(W(0.55, -0.9, 1.35)), 0.5, (1.0, 0.92, 0.85), lights_for(rng("face", "shake", "hook", "retry"), 18.0), target=faceT)
fk.visible_camera = False
ck = area("clock_key", (0.2, -0.3, 2.0), 0.5, (1.0, 0.92, 0.8), lights_for(rng("clock"), 25.0), target=ckT)
# rentgen
area("x_rim", tuple(W(-0.8, 0.4, 1.4)), 0.8, (0.3, 0.6, 1.0), lights_for(X_SHOTS, 40.0), target=fcT)
xp = point("x_flash", tuple(FC), 0.02, (1.0, 0.9, 0.6), [(1, 0)])
for F in FLASHES:
    xp.data.energy = 0; xp.data.keyframe_insert("energy", frame=F - 1)
    xp.data.energy = 6.0; xp.data.keyframe_insert("energy", frame=F)
    xp.data.energy = 0; xp.data.keyframe_insert("energy", frame=F + 5)
interp(xp.data, "LINEAR")
# bo'g'im kesimi
area("j_key", JT(-1.6, -2.2, 2.0), 1.6, (1.0, 0.95, 0.9), lights_for(J_SHOTS, 260.0), target=jT0)
area("j_rim", JT(1.6, 1.4, 1.6), 1.4, (0.4, 0.75, 1.0), lights_for(J_SHOTS, 300.0), target=jT0)
area("j_under", JT(0.6, -1.6, -1.3), 1.2, (1.0, 0.7, 0.45), lights_for(J_SHOTS, 90.0), target=jT0)
area("j_inside", JT(0.0, 0.25, 0.0), 0.3, (1.0, 0.85, 0.5), lights_for(J_SHOTS, 25.0), target=empty("jinT", JT(0, -1, 0)))
area("j_blue", JT(1.8, -1.8, 1.0), 1.4, (0.25, 0.5, 1.0), lights_for(rng("vac", "bub"), 600.0), target=jT0)
red = area("j_red", JT(-2.0, -1.5, 1.2), 1.5, (1.0, 0.08, 0.04), [(1, 0), (EMAS, 2000.0), (MY1 + 1, 0)], target=jT0)
bp_ = point("pop_flash", JT(*(BC + Vector((0, -0.1, 0)))), 0.05, (0.8, 0.95, 1.0), [(1, 0)])
for f, e_ in ((POP - 1, 0), (POP, 250.0), (POP + 3, 80.0), (POP + 9, 0)):
    bp_.data.energy = e_; bp_.data.keyframe_insert("energy", frame=f)
interp(bp_.data, "LINEAR")

# ======================================================================
# 6) RENDER
# ======================================================================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_overwrite = False; r.use_placeholder = True
if os.environ.get("THREADS"): r.threads_mode = "FIXED"; r.threads = int(os.environ["THREADS"])

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
