# Tatuirovka nega o'chmaydi — Zack D. Films uslubida 40.3 s video (967 kadr, 24 fps, 9:16).
# Asos: zack_test/scene3.py + mixchar.py; yordamchilar zack_test/ishqalash/ishqalash.py dan; egri chiziqlar: burish/parts.py
# Assetlar: zack_test/tools/get_tatu.sh
# Render: OUT=/tmp/claude-0/frames/ SAMPLES=8 PCT=40 /tmp/claude-0/bvenv/bin/python -I zack_test/tatu/tatu.py --render
# Sinov:  FRAMES=20,100,240,600,720 PCT=35 OUT=/tmp/claude-0/test/ ... --render
import bpy, math, sys, os, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT); sys.path.insert(0, os.path.join(ZT, "burish"))
from mathutils import Vector, Matrix, Euler, Quaternion
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
END = 967
sc.frame_start, sc.frame_end = 1, END

# ---------------- yordamchilar (qovoq.py dan) ----------------
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

def frames_vis(o, frames, lo=1, hi=END):
    """faqat berilgan kadrlarda ko'rinadi (chaqmoq/uchqun miltillashi)"""
    fs = set(frames)
    prev = None
    for f in range(lo, hi + 2):
        on = f in fs
        if on != prev:
            o.hide_render = not on; o.keyframe_insert("hide_render", frame=f); prev = on
    interp(o, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
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

def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 3
        for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    o.location = loc; o.rotation_euler = [R(a) for a in rot]     # transform_apply joylashuvni ham mesh'ga yozib yuboradi
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
    return root

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
val_key = P.mat_value

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.01):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 400
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
    rnd = random.Random(seed)
    base = {}
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

def orbit(cam, f0, f1, center, r0, r1, a0, a1, z0, z1, step=2):
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = (f - f0) / max(1, f1 - f0); t = t * t * (3 - 2 * t) * 0.5 + t * 0.5
        a = R(a0 + (a1 - a0) * t); rr = r0 + (r1 - r0) * t
        key(cam, f, loc=tuple(Vector(center) + Vector((rr * math.sin(a), -rr * math.cos(a), z0 + (z1 - z0) * t))))

def area(name, loc, size, col, keys, target=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    l.visible_camera = cam_vis
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return l

def point(name, loc, r, col, keys, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc; l.visible_camera = False
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)

# ======================================================================
# KADRLAR (ovoz so'zlariga bog'langan, STORYBOARD.md)
# ======================================================================
def FT(t): return int(round(t * 24)) + 1           # soniya -> kadr
SHOTS = [(1, "hook"), (33, "shed"), (68, "studio"), (126, "surface"), (169, "notpaint"), (198, "war"), (263, "urush"),
         (322, "needle"), (368, "pierce"), (413, "attack"), (476, "vessel"), (530, "predator"), (584, "engulf"),
         (669, "toobig"), (763, "stuck"), (810, "die"), (862, "release"), (893, "again"), (950, "final")]
S = {}
for i, (f, n) in enumerate(SHOTS):
    S[n] = (f, (SHOTS[i + 1][0] - 1) if i + 1 < len(SHOTS) else END)
def rng(*names): return [S[n] for n in names]
MACN = ("hook", "surface", "needle", "final")
CUTN = ("shed", "notpaint", "pierce", "attack", "stuck")
STUN = ("studio",)
MICN = ("war", "urush", "vessel", "predator", "engulf", "toobig", "die", "release", "again")
MACR = rng(*MACN); CUTR = rng(*CUTN); STUR = rng(*STUN); MICR = rng(*MICN)
F_URUSH = FT(11.66); F_HUJUM = FT(18.42); F_ERIT = FT(26.90); F_KATTA = FT(29.38); F_HAZM = FT(30.94)
F_OLGAN = FT(35.20); F_BOSH = FT(36.48); F_YANGI = FT(38.02); F_TESH = FT(15.80)
def V(*a): return Vector(a)
def ckey(idb, mode="CONSTANT", path=None): interp(idb, mode, path)

# ======================================================================
# TATU RASMI (numpy): oy, yulduzlar, yulduz turkumi; R = siyoh, G = qizarish (xira), B = nuqtali soya
# ======================================================================
TN = 512
def make_tattoo():
    u, v = np.meshgrid((np.arange(TN) + 0.5) / TN, (np.arange(TN) + 0.5) / TN)
    ink = np.zeros((TN, TN)); w = 0.0075
    def circ(cx, cy, r): return np.hypot(u - cx, v - cy) - r
    do, di = circ(0.42, 0.5, 0.3), circ(0.55, 0.57, 0.255)
    moon_in = (do < 0) & (di > 0)
    ink[(np.abs(do) < w) & (di > -w)] = 1; ink[(np.abs(di) < w) & (do < w)] = 1
    # nuqtali soya (dotwork) ichki chetga yaqin
    rs = np.random.default_rng(3)
    dots = rs.random((TN, TN)) < np.clip(0.55 - di * 7.0, 0, 0.55) * 0.35
    ink[moon_in & dots] = 1
    def star(cx, cy, r, fill=True):
        th = np.arctan2(v - cy, u - cx) + math.pi / 2; rr = np.hypot(u - cx, v - cy)
        edge = r * (0.38 + 0.62 * np.abs(np.cos(2.5 * th)) ** 4)
        if fill: ink[rr < edge] = 1
        else: ink[np.abs(rr - edge) < w * 0.8] = 1
        return (cx, cy)
    stars = [star(0.8, 0.28, 0.075, False), star(0.86, 0.66, 0.05), star(0.66, 0.12, 0.035), star(0.73, 0.86, 0.03), star(0.2, 0.86, 0.025)]
    for (ax, ay), (bx, by) in zip(stars[:-1], stars[1:]):
        for t in np.linspace(0.15, 0.85, 9):
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            ink[np.hypot(u - px, v - py) < 0.006] = 1
    for k in range(18):
        px, py = rs.uniform(0.05, 0.95), rs.uniform(0.05, 0.95)
        if np.hypot(px - 0.42, py - 0.5) < 0.33: continue
        ink[np.hypot(u - px, v - py) < rs.uniform(0.003, 0.006)] = 1
    halo = ink.copy()
    for _ in range(6):
        halo = (np.roll(halo, 3, 0) + np.roll(halo, -3, 0) + np.roll(halo, 3, 1) + np.roll(halo, -3, 1) + halo) / 5
    img = bpy.data.images.new("tattoo", TN, TN, alpha=True, float_buffer=True)
    px = np.stack([ink, np.clip(halo * 2.5, 0, 1), moon_in.astype(float), np.ones_like(ink)], -1).astype(np.float32)
    img.pixels.foreach_set(px.ravel()); img.pack(); img.colorspace_settings.name = "Non-Color"
    return img, ink
TATIMG, TATINK = make_tattoo()
def moon_point(u):
    """oyning tashqi chizig'i pastki yoyida u ga mos nuqta (igna shu yerda yuradi)"""
    u = min(max(u, 0.125), 0.715); return u, 0.5 - math.sqrt(max(0.0, 0.3 ** 2 - (u - 0.42) ** 2))

def tattoo_nodes(m, uv):
    """uv (vektor) -> (siyoh omili, trafaret omili, qizarish); 'prog' qiymati: u < prog bo'lgan joy bo'yalgan"""
    N = m.node_tree.nodes; L = m.node_tree.links
    t = N.new("ShaderNodeTexImage"); t.image = TATIMG; t.extension = "CLIP"; t.interpolation = "Cubic"
    L.new(uv, t.inputs[0])
    sep = N.new("ShaderNodeSeparateColor"); L.new(t.outputs["Color"], sep.inputs[0])
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(uv, sx.inputs[0])
    prog = value_node(m, "prog", 1.2)
    done = P.math_n(N, L, "LESS_THAN", sx.outputs["X"], prog)
    inkf = P.math_n(N, L, "MULTIPLY", sep.outputs[0], done)
    sten = P.math_n(N, L, "MULTIPLY", sep.outputs[0], P.math_n(N, L, "SUBTRACT", 1.0, done))
    halo = P.math_n(N, L, "MULTIPLY", sep.outputs[1], P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", done, 0.8), 0.0))
    return inkf, sten, halo

def skin_tat_mat(name, coord="OBJECT", size=0.07, offset=(0, 0), base=(0.78, 0.55, 0.44), pores=2200.0, decal=False, scale_sss=0.0015):
    """teri + tatu. coord: OBJECT (x,y metrda -> uv) yoki UV. decal=True: siyohsiz joy shaffof"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; out = N["Material Output"]
    tc = N.new("ShaderNodeTexCoord")
    if coord == "UV":
        uv = tc.outputs["UV"]
    else:
        mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / size, 1 / size, 1)
        mp.inputs["Location"].default_value = (0.5 - offset[0] / size, 0.5 - offset[1] / size, 0)
        L.new(tc.outputs["Object"], mp.inputs[0]); uv = mp.outputs[0]
    inkf, sten, halo = tattoo_nodes(m, uv)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180.0; nz.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (base[0] * 0.93, base[1] * 0.84, base[2] * 0.8, 1)
    cr.color_ramp.elements[1].color = (min(1, base[0] * 1.05), base[1] * 1.03, base[2] * 1.02, 1)
    red = N.new("ShaderNodeMix"); red.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", halo, 0.55), red.inputs["Factor"])
    L.new(cr.outputs[0], red.inputs[6]); red.inputs[7].default_value = (0.75, 0.25, 0.22, 1)
    st = N.new("ShaderNodeMix"); st.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", sten, 0.6), st.inputs["Factor"])
    L.new(red.outputs[2], st.inputs[6]); st.inputs[7].default_value = (0.3, 0.12, 0.5, 1)
    ik = N.new("ShaderNodeMix"); ik.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", inkf, 0.97), ik.inputs["Factor"])
    L.new(st.outputs[2], ik.inputs[6]); ik.inputs[7].default_value = (0.012, 0.016, 0.03, 1)
    L.new(ik.outputs[2], b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 1.0; b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.18)
    b.inputs["Subsurface Scale"].default_value = scale_sss
    L.new(P.math_n(N, L, "SUBTRACT", 1.0, inkf), b.inputs["Subsurface Weight"])
    b.inputs["Roughness"].default_value = 0.45
    wet = value_node(m, "wet", 0.0)
    L.new(P.math_n(N, L, "ADD", wet, P.math_n(N, L, "MULTIPLY", inkf, 0.3)), b.inputs["Coat Weight"])
    b.inputs["Coat Roughness"].default_value = 0.08
    pv = N.new("ShaderNodeTexVoronoi"); pv.inputs["Scale"].default_value = pores; L.new(tc.outputs["Object"], pv.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.00006
    L.new(pv.outputs["Distance"], bp.inputs["Height"])
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 90.0; wv.inputs["Distortion"].default_value = 6.0
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = 0.25; bp2.inputs["Distance"].default_value = 0.0001
    L.new(wv.outputs["Fac"], bp2.inputs["Height"]); L.new(bp.outputs[0], bp2.inputs["Normal"]); L.new(bp2.outputs[0], b.inputs["Normal"])
    if decal:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
        L.new(P.math_n(N, L, "MINIMUM", P.math_n(N, L, "ADD", P.math_n(N, L, "ADD", inkf, P.math_n(N, L, "MULTIPLY", sten, 0.6)),
                                                  P.math_n(N, L, "MULTIPLY", halo, 0.4)), 1.0), mx.inputs[0])
        L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
TAT_MATS = []
def prog_key(f, v):
    for m in TAT_MATS: val_key(m, "prog", f, v)

def rubber_mat(name, col, rough=0.6):
    m = mat(name, col, rough)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 160
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
steel_m = mat("steel", (0.8, 0.8, 0.82), 0.18, metal=1.0)
ink_m = mat("ink", (0.008, 0.01, 0.018), 0.15, coat=0.8)
clear_m = mat("clear_plastic", (0.9, 0.95, 1.0), 0.05, trans=1.0)
anod_m = mat("anod", (0.45, 0.02, 0.04), 0.28, metal=0.9)
grip_m = rubber_mat("grip", (0.02, 0.02, 0.022), 0.55)
cable_m = mat("cable", (0.02, 0.02, 0.02), 0.4)

def tattoo_pen(name, scale=1.0):
    """qalam shaklidagi tatu mashinkasi: mahalliy +Z = uchidan orqaga; (0,0,0) = uch. 'needle' bolasi z bo'yicha yuradi"""
    g = empty(name); s = scale
    def seg(nm, z0, z1, r0, r1, m, verts=40):
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r0 * s, radius2=r1 * s, depth=(z1 - z0) * s, location=(0, 0, (z0 + z1) / 2 * s))
        o = bpy.context.object; o.name = f"{name}_{nm}"; o.data.materials.append(m); o.parent = g
        for p in o.data.polygons: p.use_smooth = True
        bv = o.modifiers.new("bv", "BEVEL"); bv.width = 0.0006 * s; bv.segments = 2; bv.limit_method = "ANGLE"
        return o
    seg("tip", 0.0, 0.02, 0.0018, 0.0062, clear_m)
    seg("cart", 0.02, 0.046, 0.0066, 0.0066, clear_m)
    seg("cart_ink", 0.004, 0.03, 0.0012, 0.004, ink_m, 16)
    seg("grip", 0.046, 0.1, 0.0098, 0.0108, grip_m)
    seg("ring", 0.1, 0.106, 0.0118, 0.0118, steel_m)
    seg("body", 0.106, 0.19, 0.0124, 0.0124, anod_m)
    seg("cap", 0.19, 0.2, 0.0124, 0.009, steel_m)
    P.tube(f"{name}_cable", [(0, 0, 0.2 * s), (0, 0.004 * s, 0.24 * s), (0.01 * s, 0.03 * s, 0.32 * s), (0.04 * s, 0.09 * s, 0.42 * s), (0.08 * s, 0.2 * s, 0.6 * s)],
           0.0035 * s, cable_m, g)
    nd = empty(f"{name}_needle", (0, 0, 0), g)
    for k in range(5):
        a = k * 2 * math.pi / 5; off = (0.00035 * math.cos(a) * s, 0.00035 * math.sin(a) * s, 0)
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.00001 * s, radius2=0.00022 * s, depth=0.0025 * s, location=(off[0], off[1], -0.00125 * s + 0.0025 * s))
        o = bpy.context.object; o.name = f"{name}_nt{k}"; o.data.materials.append(steel_m); o.parent = nd
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.00022 * s, depth=0.03 * s, location=(off[0], off[1], 0.0175 * s))
        o = bpy.context.object; o.name = f"{name}_ns{k}"; o.data.materials.append(steel_m); o.parent = nd
    return g, nd
def aim(o, axis_dir):
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(axis_dir).normalized())
def needle_buzz(nd, f0, f1, out=-0.0024, inn=0.0006, step=1, s=1.0):
    """igna har 'step' kadrda chiqib-kiradi (motion blur bilan xira)"""
    for f in range(f0, f1 + 1, step):
        k = ((f - f0) // step) % 2
        nd.location = (0, 0, (out if k == 0 else inn) * s); nd.keyframe_insert("location", frame=f)
    interp(nd, "LINEAR", "location")

# ======================================================================
# 1) MAKRO: bilak (real o'lcham), tatu, igna, siyoh sachrashi, tuklar
# ======================================================================
MAC = V(30.0, 0.0, 1.0)
ARY, ARZ = 0.045, 0.032                                   # bilak kesimi: ellips (kenglik, balandlik)
mac_objs = []
def M_(o): mac_objs.append(o); return o
def arm_prop(name, loc, L_=0.4, nx=420, nt=320):
    xs = np.linspace(-L_ / 2, L_ / 2, nx); th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    X, TH = np.meshgrid(xs, th, indexing="ij")
    Y = ARY * np.cos(TH); Z = ARZ * np.sin(TH) * np.where(np.sin(TH) > 0, 1.0, 0.9)
    vs = np.stack([X, Y, Z], -1).reshape(-1, 3)
    fs = []
    for i in range(nx - 1):
        for j in range(nt):
            a = i * nt + j; b = i * nt + (j + 1) % nt
            fs.append((a, a + nt, b + nt, b))
    me = bpy.data.meshes.new(name); me.from_pydata(vs.tolist(), [], fs); me.update()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc
    return o
def surf(u, v):
    x, y = (u - 0.5) * 0.07, (v - 0.5) * 0.07
    z = ARZ * math.sqrt(max(0.0, 1 - (y / ARY) ** 2))
    return MAC + V(x, y, z)
arm = M_(arm_prop("mac_arm", tuple(MAC)))
arm_m = skin_tat_mat("mac_skin", "OBJECT", 0.07, (0, 0), base=(0.72, 0.47, 0.37)); TAT_MATS.append(arm_m)
arm.data.materials.append(arm_m)
tipE = M_(empty("mac_tipE", tuple(surf(*moon_point(0.22)))))
vg = arm.vertex_groups.new(name="dent"); vg.add(list(range(len(arm.data.vertices))), 0.0, "REPLACE")
wp = arm.modifiers.new("prox", "VERTEX_WEIGHT_PROXIMITY"); wp.vertex_group = "dent"; wp.target = tipE
wp.proximity_mode = "OBJECT"; wp.min_dist = 0.006; wp.max_dist = 0.0; wp.falloff_type = "SMOOTH"
dent = arm.modifiers.new("dent", "DISPLACE"); dent.vertex_group = "dent"; dent.direction = "NORMAL"; dent.mid_level = 0.0; dent.strength = 0.0
def dent_key(f, v): dent.strength = v; dent.keyframe_insert("strength", frame=f)
dent_key(1, 0.0)
# qora charm tayanch
M_(box("mac_pad", (0.6, 0.3, 0.04), tuple(MAC + V(0, 0, -ARZ * 0.9 - 0.02)), mat("leather", (0.015, 0.015, 0.017), 0.35, coat=0.3), bevel=0.01))
# tuklar (tatu joyi qirilgan)
rh = random.Random(5)
hc = bpy.data.curves.new("mac_hair", "CURVE"); hc.dimensions = "3D"; hc.bevel_depth = 0.000028; hc.bevel_resolution = 1
for k in range(900):
    x = rh.uniform(-0.18, 0.18); t_ = rh.uniform(R(25), R(155))
    y, z = ARY * math.cos(t_), ARZ * math.sin(t_)
    if abs(x) < 0.05 and abs(y) < 0.042: continue
    n = V(math.cos(t_) / ARY, 0, math.sin(t_) / ARZ).normalized(); n = V(0, n.x, n.z) if False else V(0, math.cos(t_) * ARZ, math.sin(t_) * ARY).normalized()
    d = (V(1, rh.uniform(-0.3, 0.3), 0) * 0.85 + n * 0.45).normalized(); ln = rh.uniform(0.003, 0.007)
    p0 = V(x, y, z); p1 = p0 + d * ln * 0.5 + n * 0.0006; p2 = p0 + d * ln + n * 0.0003
    sp = hc.splines.new("NURBS"); sp.points.add(2)
    for i, p in enumerate((p0, p1, p2)): sp.points[i].co = (*p, 1); sp.points[i].radius = 1.0 - 0.6 * i / 2
    sp.use_endpoint_u = True; sp.order_u = 3
hair_o = bpy.data.objects.new("mac_hair", hc); sc.collection.objects.link(hair_o); hair_o.location = tuple(MAC)
hc.materials.append(mat("vellus", (0.32, 0.22, 0.14), 0.35, trans=0.2)); M_(hair_o)
# fon: xira studiya chiroqlari (bokeh)
rb = random.Random(9)
bokeh_ms = [mat("bk_warm", (1.0, 0.6, 0.3), 0.5, emit=6.0), mat("bk_pink", (1.0, 0.15, 0.6), 0.5, emit=6.0), mat("bk_blue", (0.3, 0.5, 1.0), 0.5, emit=5.0)]
for k in range(40):
    a = rb.uniform(0, 2 * math.pi); d = rb.uniform(1.2, 3.5)
    M_(sphere(f"mac_bokeh{k}", rb.uniform(0.02, 0.06), tuple(MAC + V(d * math.cos(a), d * math.sin(a), rb.uniform(0.2, 1.4))), rb.choice(bokeh_ms), sub=2))
M_(plane("mac_floor", (8, 8), tuple(MAC + V(0, 0, -0.8)), mat("mac_floor_m", (0.02, 0.02, 0.025), 0.4)))
# mashinka
PEN_A = V(-0.18, -0.5, 0.85).normalized()
pen_m, nd_m = tattoo_pen("mac_pen"); aim(pen_m, PEN_A)      # M_ emas: o'z vis() i bor
def pen_at(f, u):
    p = surf(*moon_point(u)); pen_m.location = tuple(p + PEN_A * 0.0003); pen_m.keyframe_insert("location", frame=f)
    tipE.location = tuple(p); tipE.keyframe_insert("location", frame=f)
H0, H1 = S["hook"]; N0, N1 = S["needle"]
pen_at(H0, 0.45); pen_at(H1 + 1, 0.5); pen_at(N0, 0.58); pen_at(N1 + 1, 0.62)
interp(pen_m, "LINEAR", "location"); interp(tipE, "LINEAR", "location")
needle_buzz(nd_m, H0, H1 + 1); needle_buzz(nd_m, N0, N1 + 1)
for f in range(H0, H1 + 2): dent_key(f, -0.0011 if (f - H0) % 2 == 0 else -0.0004)
for f in range(N0, N1 + 2): dent_key(f, -0.0013 if (f - N0) % 2 == 0 else -0.0003)
dent_key(N1 + 2, 0.0); interp(arm, "LINEAR", "modifiers")
PROG = [(1, 0.45), (H1 + 1, 0.5), (S["studio"][0], 0.52), (S["studio"][1], 0.56), (S["surface"][0], 1.2), (N0, 0.58), (N1 + 1, 0.62), (N1 + 2, 1.2)]
val_key(arm_m, "wet", 1, 0.55); val_key(arm_m, "wet", S["surface"][0], 0.3); val_key(arm_m, "wet", N0, 0.6); val_key(arm_m, "wet", S["final"][0], 0.3)
ckey(arm_m.node_tree)
vis(pen_m, rng("hook", "needle"))
# siyoh sachrashi (ilgak kadri)
splat = empty("mac_splat")        # vis() ro'yxatiga qo'shilmaydi: tomchilarning frames_vis kalitlari saqlansin
for k in range(16):
    d = sphere(f"mac_drop{k}", rh.uniform(0.00025, 0.0006), (0, 0, 0), ink_m, sub=2, parent=splat)
    f0 = H0 + 2 + k * 2 if k < 12 else N0 + (k - 12) * 9
    sc.frame_set(f0); bpy.context.view_layer.update(); p0 = tipE.matrix_world.translation.copy()
    vdir = V(rh.uniform(-1, 1), rh.uniform(-1, 1), rh.uniform(0.8, 1.8)).normalized() * rh.uniform(0.12, 0.3)
    for i in range(0, 9):
        t = i / 24.0; p = p0 + vdir * t + V(0, 0, -4.9 * t * t)
        p.z = max(p.z, surf(0.5, 0.5).z - 0.001 if abs(p.y - MAC.y) < 0.03 else p.z)
        key(d, f0 + i, loc=tuple(p))
    frames_vis(d, list(range(f0, f0 + 9)))

# ======================================================================
# 2) KESIM: teri bloki (x ±0.3, y ±0.2, z 0..0.3); old yuz y=-0.2 — kesim tekisligi
# ======================================================================
CUT = V(60.0, 0.0, 1.0)
cut_objs = []
def C_(o): cut_objs.append(o); return o
def CP(x, y, z): return CUT + V(x, y, z)
def cell_cut_mat(name, c_in, c_mem, scale, flow=False, zlight=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs[0])
    if flow:
        fl = value_node(m, "flow", 0.0); cmb = N.new("ShaderNodeCombineXYZ"); L.new(P.math_n(N, L, "MULTIPLY", fl, -1.0), cmb.inputs[2])
        L.new(cmb.outputs[0], mp.inputs["Location"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = scale
    L.new(mp.outputs[0], vo.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    L.new(P.math_n(N, L, "LESS_THAN", vo.outputs["Distance"], 0.06), mx.inputs["Factor"])
    mx.inputs[6].default_value = (*c_in, 1); mx.inputs[7].default_value = (*c_mem, 1)
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.inputs["Scale"].default_value = scale; L.new(mp.outputs[0], vo2.inputs["Vector"])
    nuc = P.math_n(N, L, "LESS_THAN", vo2.outputs["Distance"], 0.18)
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; L.new(P.math_n(N, L, "MULTIPLY", nuc, 0.7), mx2.inputs["Factor"])
    L.new(mx.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = (0.35, 0.18, 0.4, 1)
    L.new(mx2.outputs[2], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.35; b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.01
    b.inputs["Coat Weight"].default_value = 0.4
    return m
epi_m = cell_cut_mat("epi_cut", (0.92, 0.74, 0.62), (0.62, 0.36, 0.3), 90.0, flow=True)
fat_m = cell_cut_mat("fat_cut", (1.0, 0.82, 0.38), (0.85, 0.55, 0.22), 16.0)
der_m = bpy.data.materials.new("der_cut"); der_m.use_nodes = True
N = der_m.node_tree.nodes; L = der_m.node_tree.links; b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.bands_direction = "X"; wv.inputs["Scale"].default_value = 22.0
wv.inputs["Distortion"].default_value = 16.0; wv.inputs["Detail"].default_value = 6.0; wv.inputs["Detail Roughness"].default_value = 0.7; L.new(tc.outputs["Object"], wv.inputs["Vector"])
cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.62, 0.22, 0.24, 1); cr.color_ramp.elements[1].color = (0.86, 0.46, 0.44, 1)
L.new(cr.outputs[0], b.inputs["Base Color"])
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.45; L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.4; b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.01
b.inputs["Coat Weight"].default_value = 0.35
C_(box("cut_fat", (0.6, 0.4, 0.14), tuple(CP(0, 0, 0.07)), fat_m, bevel=0.002))
C_(box("cut_derm", (0.6, 0.4, 0.14), tuple(CP(0, 0, 0.21)), der_m))
epi = C_(box("cut_epi", (0.6, 0.4, 0.02), tuple(CP(0, 0, 0.29)), epi_m))
top_m = skin_tat_mat("cut_top", "OBJECT", 0.5, (0, -0.2), pores=60.0, scale_sss=0.01, base=(0.74, 0.5, 0.4))   # doim tayyor (prog 1.2)
epi.data.materials.append(top_m)
for p in epi.data.polygons: p.material_index = 1 if p.normal.z > 0.9 else 0
val_key(epi_m, "flow", S["shed"][0], 0.0); val_key(epi_m, "flow", S["shed"][1], -0.05)
for fc in mc._fcurves(epi_m.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
C_(plane("cut_table", (6, 6), tuple(CP(0, 0, -0.002)), mat("cut_tbl", (0.03, 0.035, 0.045), 0.35, coat=0.5)))
# siyoh to'dalari (old yuzdan biroz chiqib turadi): tatuning v=0.5 qatoridagi bo'yalgan ustunlar
ri = random.Random(21)
row = TATINK[TN // 2]
INKX = sorted({((i + 0.5) / TN - 0.5) * 0.5 for j in range(TN // 2 - 24, TN // 2 + 25, 8) for i in range(0, TN, 5) if TATINK[j, i] > 0.5})
inkblobs = []
for x in INKX:
    for k in range(ri.randint(2, 4)):
        r_ = ri.uniform(0.005, 0.011)
        p = CP(x + ri.uniform(-0.008, 0.008), -0.2 + r_ * 0.45, ri.uniform(0.2, 0.268))
        inkblobs.append(C_(sphere(f"cut_ink{len(inkblobs)}", r_, tuple(p), ink_m, sub=2)))
print("ink blobs", len(inkblobs))
shell_m = mat("ink_cell", (0.92, 0.86, 0.7), 0.3, alpha=0.45, sss=0.3)
shells = []
for i, bl in enumerate(inkblobs[::2]):
    shells.append(sphere(f"cut_shell{i}", 0.016, tuple(bl.location + V(0, 0.002, 0)), shell_m, sub=3))
# qon tomirlari: old yuzda yarmi ko'rinadi
ves_m = mat("vessel", (0.55, 0.04, 0.05), 0.25, coat=0.6, sss=0.4, emit=0.0, emit_col=(1.0, 0.05, 0.03))
vein_m = mat("vein", (0.25, 0.05, 0.12), 0.3, coat=0.6, sss=0.3, emit=0.0, emit_col=(1.0, 0.05, 0.08))
vessels = []
vessels.append(C_(P.tube("cut_art", [tuple(CP(x, -0.2, 0.165 + 0.006 * math.sin(x * 20))) for x in np.linspace(-0.31, 0.31, 9)], 0.010, ves_m)))
vessels.append(C_(P.tube("cut_vein", [tuple(CP(x, -0.2, 0.185 + 0.006 * math.cos(x * 17))) for x in np.linspace(-0.31, 0.31, 9)], 0.012, vein_m)))
for k, x0 in enumerate((-0.24, -0.08, 0.06, 0.2)):
    pts = [CP(x0, -0.2, 0.168), CP(x0 + 0.005, -0.2, 0.235), CP(x0 + 0.02, -0.2, 0.266), CP(x0 + 0.035, -0.2, 0.235), CP(x0 + 0.04, -0.2, 0.186)]
    vessels.append(C_(P.tube(f"cut_cap{k}", [tuple(p) for p in pts], 0.0035, ves_m)))
# tuk follikulalari
hair_m = mat("hair_shaft", (0.08, 0.05, 0.03), 0.35, coat=0.4)
foll_m = mat("follicle", (0.95, 0.75, 0.68), 0.4, sss=0.5, alpha=0.8)
glan_m = mat("sebum", (1.0, 0.85, 0.5), 0.3, sss=0.6)
for k, x0 in enumerate((-0.27, 0.235)):
    C_(P.tube(f"cut_hair{k}", [tuple(CP(x0, -0.2, 0.12)), tuple(CP(x0 + 0.025, -0.2, 0.22)), tuple(CP(x0 + 0.045, -0.2, 0.3)), tuple(CP(x0 + 0.09, -0.2, 0.4)), tuple(CP(x0 + 0.16, -0.2, 0.47))], 0.006, hair_m))
    C_(P.tube(f"cut_foll{k}", [tuple(CP(x0 - 0.002, -0.2, 0.115)), tuple(CP(x0 + 0.025, -0.2, 0.22)), tuple(CP(x0 + 0.043, -0.2, 0.292))], 0.013, foll_m))
    C_(sphere(f"cut_gland{k}", 0.02, tuple(CP(x0 + 0.04, -0.2, 0.2)), glan_m, scale=(1, 0.7, 1.3), sub=3))
# ko'chib tushayotgan po'stlar (1-kesim kadri)
flake_m = mat("flake", (0.95, 0.88, 0.8), 0.6, sss=0.3, alpha=0.85)
SH0, SH1 = S["shed"]
for k in range(34):
    x, y = ri.uniform(-0.28, 0.28), ri.uniform(-0.19, 0.18)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=ri.uniform(0.008, 0.016), depth=0.0015, location=(0, 0, 0))
    fo = bpy.context.object; fo.name = f"cut_flake{k}"; fo.data.materials.append(flake_m)
    d0 = ri.randint(0, 12); h = ri.uniform(0.04, 0.12)
    key(fo, SH0, loc=tuple(CP(x, y, 0.3015)), rot=(0, 0, ri.uniform(0, 180)))
    key(fo, SH0 + d0, loc=tuple(CP(x, y, 0.3015)), rot=(0, 0, ri.uniform(0, 180)))
    key(fo, SH1 + 1, loc=tuple(CP(x + ri.uniform(-0.03, 0.03), y + ri.uniform(-0.03, 0.01), 0.302 + h)),
        rot=(ri.uniform(-70, 70), ri.uniform(-70, 70), ri.uniform(0, 360)))
    vis(fo, [S["shed"]])
# katta igna (kesim): pen scale 40, old yuz tekisligida (yarmi ko'rinadi)
CPS = 40.0
cpen, cnd = tattoo_pen("cut_pen", CPS); aim(cpen, V(0.12, 0.0, 1.0))
PI0, PI1 = S["pierce"]
key(cpen, PI0, loc=tuple(CP(-0.12, -0.2, 0.303))); key(cpen, PI1 + 1, loc=tuple(CP(0.02, -0.2, 0.303)))
interp(cpen, "LINEAR", "location")
cnd.location = (0, 0, 0.002 * CPS); cnd.keyframe_insert("location", frame=1)
STEP = 5
for i, f in enumerate(range(PI0, PI1 + 1, STEP)):
    cnd.location = (0, 0, 0.0008 * CPS); cnd.keyframe_insert("location", frame=f)
    cnd.location = (0, 0, -0.0024 * CPS); cnd.keyframe_insert("location", frame=f + 2)
    cnd.location = (0, 0, 0.0008 * CPS); cnd.keyframe_insert("location", frame=f + 4)
    sc.frame_set(f + 2); bpy.context.view_layer.update()
    tip = cpen.matrix_world @ V(0, 0, -0.0024 * CPS)
    for k in range(3):
        d = sphere(f"cut_newink{i}_{k}", ri.uniform(0.005, 0.009), tuple(V(tip.x + ri.uniform(-0.01, 0.01), -0.2 + 0.004 + CUT.y, tip.z + ri.uniform(0.0, 0.05))), ink_m, sub=2)
        frames_vis(d, list(range(f + 2, END + 1)))
interp(cnd, "LINEAR", "location")
vis(cpen, [S["pierce"]])
for m_ in (ves_m, vein_m):
    bb = m_.node_tree.nodes["Principled BSDF"]; bb.inputs["Emission Color"].default_value = (1.0, 0.06, 0.04, 1)
    def ek(f, v, bb=bb): bb.inputs["Emission Strength"].default_value = v; bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    ek(1, 0.0); AT0, AT1 = S["attack"]; ek(AT0, 0.3)
    for f in range(AT0 + 4, AT1, 12): ek(f, 0.4); ek(f + 3, 9.0 if f >= F_HUJUM - 6 else 5.0); ek(f + 7, 0.6)
    ek(AT1 + 1, 0.0)
    ckey(m_.node_tree, "LINEAR")

# ======================================================================
# 3) MIKRO: hujayralar dunyosi. Uch sahna: W (urush), V (qon tomiri), E (qahramon makrofag)
# ======================================================================
MIC = V(100.0, 0.0, 0.0)
W0 = MIC + V(0, 0, 0); V0 = MIC + V(30, 0, 0); E0 = MIC + V(60, 0, 0)
mic_objs = []
def Mi(o): mic_objs.append(o); return o
rm = random.Random(33)
def cell_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; out = N["Material Output"]
    dead = value_node(m, "dead", 0.0); red = value_node(m, "red", 0.0)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 5.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(nz.outputs["Fac"], c1.inputs["Factor"])
    c1.inputs[6].default_value = (0.95, 0.86, 0.62, 1); c1.inputs[7].default_value = (0.8, 0.72, 0.85, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(dead, c2.inputs["Factor"]); L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.16, 0.14, 0.11, 1)
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"; L.new(red, c3.inputs["Factor"]); L.new(c2.outputs[2], c3.inputs[6]); c3.inputs[7].default_value = (1.0, 0.35, 0.3, 1)
    L.new(c3.outputs[2], b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 1.0; b.inputs["Subsurface Scale"].default_value = 0.12; b.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.6)
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.7; b.inputs["Coat Roughness"].default_value = 0.1
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.85, 0.65, 1)
    L.new(P.math_n(N, L, "MULTIPLY", lw.outputs["Fresnel"], P.math_n(N, L, "SUBTRACT", 0.8, P.math_n(N, L, "MULTIPLY", dead, 0.7))), em.inputs["Strength"])
    ad = N.new("ShaderNodeAddShader"); L.new(b.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    # markazi shaffofroq (ichidagi siyoh va yadro ko'rinsin), chetlari zich
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", lw.outputs["Facing"], 0.55), P.math_n(N, L, "SUBTRACT", 0.4, P.math_n(N, L, "MULTIPLY", dead, 0.15)), clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(ad.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m
nuc_m = mat("nucleus", (0.35, 0.18, 0.55), 0.35, sss=0.5, coat=0.4)
CELLS = []
class Cell:
    def __init__(self, name, loc, r=0.6, pods=6, seed=1):
        self.rs = random.Random(seed); self.r = r
        mb = bpy.data.metaballs.new(name); mb.resolution = 0.12; mb.render_resolution = r * 0.055; mb.threshold = 0.6
        self.o = bpy.data.objects.new(name, mb); sc.collection.objects.link(self.o); self.o.location = loc
        self.m = cell_mat(name + "_m"); mb.materials.append(self.m)
        self.body = []
        for k in range(4):
            e = mb.elements.new(); e.radius = r * (1.0 if k == 0 else 0.7); e.stiffness = 2.0
            e.co = (0, 0, 0) if k == 0 else tuple(V(self.rs.uniform(-1, 1), self.rs.uniform(-1, 1), self.rs.uniform(-0.5, 0.5)).normalized() * r * 0.35)
            self.body.append((e, Vector(e.co)))
        self.pods = []
        for k in range(pods):
            d = V(self.rs.uniform(-1, 1), self.rs.uniform(-1, 1), self.rs.uniform(-0.6, 0.6)).normalized()
            e = mb.elements.new(); e.radius = r * self.rs.uniform(0.3, 0.42); e.stiffness = 2.0; e.co = tuple(d * r * 0.75)
            self.pods.append([e, d, self.rs.uniform(0, 6.28)])
        self.nuc = sphere(name + "_nuc", r * 0.33, (r * 0.08, -r * 0.05, r * 0.05), nuc_m, scale=(1.2, 1.0, 0.85), sub=3, parent=self.o)
        self.lm = mat(name + "_lys", (0.3, 1.0, 0.35), 0.3, emit=0.0, emit_col=(0.35, 1.0, 0.3))
        self.lys = []
        for k in range(10):
            p = V(self.rs.uniform(-1, 1), self.rs.uniform(-1, 1), self.rs.uniform(-1, 1)).normalized() * r * self.rs.uniform(0.3, 0.6)
            self.lys.append(sphere(f"{name}_ly{k}", r * self.rs.uniform(0.05, 0.08), tuple(p), self.lm, sub=2, parent=self.o))
        CELLS.append(self)
    def wiggle(self, f0, f1, amp=0.25, reach=0.85, step=2, speed=1.0):
        for f in range(f0, f1 + 1, step):
            t = f / 24.0 * speed
            for e, d, ph in self.pods:
                rr = self.r * (reach + amp * math.sin(t * 2.3 + ph))
                e.co = tuple(d * rr + V(0, 0, 0.05 * self.r * math.sin(t * 3.1 + ph * 2))); e.keyframe_insert("co", frame=f)
            for e, c0 in self.body[1:]:
                e.co = tuple(c0 + V(math.sin(t * 1.7 + c0.x * 9), math.cos(t * 1.3 + c0.y * 7), math.sin(t * 2.1)) * self.r * 0.07)
                e.keyframe_insert("co", frame=f)
    def reach_to(self, f0, f1, target_w, rp, step=2, wrap=1.0):
        """oyoqchalar target atrofini o'rab oladi (wrap 0..1)"""
        n = len(self.pods)
        for f in range(f0, f1 + 1, step):
            t = ease((f - f0) / max(1, f1 - f0)) * wrap
            loc = self.loc_at(f)
            for i, (e, d, ph) in enumerate(self.pods):
                a = 2 * math.pi * i / n
                ring = V(math.cos(a), math.sin(a) * 0.6, math.sin(a) * 0.8).normalized() * (rp + self.r * 0.12)
                tgt = (target_w - loc) + ring * (1.0 - 0.5 * t)
                base = d * self.r * 0.8
                p = base.lerp(tgt, min(1.0, t * 1.4)) + V(0, 0, 0.04 * self.r * math.sin(f * 0.4 + ph))
                e.co = tuple(p); e.keyframe_insert("co", frame=f)
    def loc_at(self, f):
        ad = self.o.animation_data
        if not ad or not ad.action: return self.o.location.copy()
        v = self.o.location.copy()
        for fc in mc._fcurves(ad.action):
            if fc.data_path == "location": v[fc.array_index] = fc.evaluate(f)
        return v
    def move(self, pts):
        for f, p in pts: key(self.o, f, loc=tuple(p))
    def enz(self, f, v):
        val = self.lm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]; val.default_value = v; val.keyframe_insert("default_value", frame=f)
    def setv(self, name, f, v): val_key(self.m, name, f, v)

def ink_particle(name, loc, r, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(0, 0, 0)); o = bpy.context.object; o.name = name
    rs = random.Random(seed)
    for v in o.data.vertices: v.co *= rs.uniform(0.75, 1.2)
    o.scale = (rs.uniform(0.8, 1.25), rs.uniform(0.8, 1.2), rs.uniform(0.75, 1.1)); o.rotation_euler = (rs.uniform(0, 6), rs.uniform(0, 6), rs.uniform(0, 6))
    o.location = loc; o.data.materials.append(pig_m)
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = r * 0.06; bv.segments = 2
    return Mi(o)
pig_m = mat("pigment", (0.006, 0.008, 0.016), 0.18, coat=1.0)
pig_m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.8

# kollagen tolalari va mayda zarralar (har sahna atrofida)
fib_m = mat("collagen", (0.9, 0.52, 0.52), 0.35, sss=0.8, coat=0.5)
fib_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.2
speck_m = mat("speck", (1.0, 0.8, 0.75), 0.4, emit=0.4)
def field(c, n=26, span=9.0, seed=1, tube_clear=False):
    rs = random.Random(seed)
    for k in range(n):
        d = V(rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(-0.35, 0.35)).normalized()
        mid = c + V(rs.uniform(-span, span), rs.uniform(-span, span), rs.uniform(-3.5, 3.5))
        if (mid - c).length < 1.8: mid += (mid - c).normalized() * 2.0
        side = d.cross(V(0, 0, 1)).normalized()
        for s in range(rs.randint(2, 4)):
            off = side * rs.uniform(-0.35, 0.35) + V(0, 0, rs.uniform(-0.25, 0.25))
            pts = [tuple(mid + off + d * t * 7 + side * 0.35 * math.sin(t * 5 + s) + V(0, 0, 0.25 * math.cos(t * 4 + s))) for t in np.linspace(-1, 1, 9)]
            if any(-7.0 < p[1] - c.y < -1.0 and abs(p[0] - c.x) < 7.0 and abs(p[2] - c.z) < 3.5 for p in pts): continue   # kamera tomoni bo'sh
            if tube_clear and any(abs(p.y - c.y) < 1.8 and abs(p.z - c.z) < 1.8 for p in (mid + off + d * t * 7 for t in np.linspace(-1, 1, 41))): continue           # qon tomiri ichi bo'sh
            Mi(P.tube(f"fib_{seed}_{k}_{s}", pts, rs.uniform(0.05, 0.11), fib_m))
    for k in range(120):
        p = c + V(rs.uniform(-span, span), rs.uniform(-span, span), rs.uniform(-4, 4))
        Mi(sphere(f"speck_{seed}_{k}", rs.uniform(0.015, 0.05), tuple(p), speck_m, sub=1))
for i, c in enumerate((W0, V0, E0)): field(c, n=44, seed=40 + i, tube_clear=(i == 1))

# --- W: urush sahnasi: siyoh to'dalari va ularni o'rab olgan makrofaglar
PW0, PW1 = S["war"][0], S["urush"][1]
clusters = [W0 + V(-1.2, 0.6, 0.0), W0 + V(1.4, 1.5, 0.3), W0 + V(0.3, -1.3, -0.2)]
for ci, cc in enumerate(clusters):
    for k in range(6):
        ink_particle(f"w_ink{ci}_{k}", tuple(cc + V(rm.uniform(-0.45, 0.45), rm.uniform(-0.45, 0.45), rm.uniform(-0.3, 0.3))), rm.uniform(0.1, 0.22), 100 + ci * 10 + k)
wcells = []
for ci, cc in enumerate(clusters):
    for k in range(2):
        a = rm.uniform(0, 6.28); p = cc + V(math.cos(a), math.sin(a), rm.uniform(-0.2, 0.2)) * 0.95
        c_ = Cell(f"wcell{ci}{k}", tuple(p), r=rm.uniform(0.5, 0.65), seed=200 + ci * 3 + k)
        c_.move([(PW0, p), (PW1 + 1, p + (cc - p) * 0.35)]); interp(c_.o, "LINEAR", "location")
        c_.wiggle(PW0 - 2, PW1 + 2, amp=0.35, reach=1.0)
        wcells.append(c_)
hero_w = wcells[0]
for c_ in wcells:
    c_.setv("red", 1, 0.0); c_.setv("red", F_URUSH - 1, 0.0); c_.setv("red", F_URUSH + 2, 0.75); c_.setv("red", F_URUSH + 14, 0.15)
# yirtqich (predator) — W sahnasi chetida
PR0, PR1 = S["predator"]
pred = Cell("predcell", tuple(W0 + V(4.5, -3.0, 0.0)), r=0.7, pods=7, seed=301)
pred.move([(PR0, W0 + V(4.5, -3.0, 0.0)), (PR1 + 1, W0 + V(4.1, -3.6, 0.0))]); interp(pred.o, "LINEAR", "location")
pred.wiggle(PR0 - 2, PR1 + 2, amp=0.5, reach=1.25, speed=1.6)
for k in range(5):
    ink_particle(f"pr_ink{k}", tuple(W0 + V(4.3 + rm.uniform(-0.6, 0.6), -4.4 + rm.uniform(-0.4, 0.4), rm.uniform(-0.3, 0.3))), rm.uniform(0.1, 0.18), 400 + k)

# --- V: qon tomiri, eritrotsitlar, devordan chiqayotgan makrofaglar
VS0, VS1 = S["vessel"]
vw_m = mat("vwall", (0.85, 0.3, 0.32), 0.3, sss=0.6, alpha=0.38, coat=0.5)
Mi(P.tube("vessel_wall", [tuple(V0 + V(x, 0, 0.12 * math.sin(x * 0.4))) for x in np.linspace(-14, 14, 9)], 1.25, vw_m))
rbc_m = mat("rbc", (0.75, 0.03, 0.04), 0.35, sss=0.5, coat=0.4)
for k in range(46):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.11, location=(0, 0, 0)); o = bpy.context.object
    o.name = f"rbc{k}"; o.data.materials.append(rbc_m); o.scale = (1, 1, 0.8)
    for p in o.data.polygons: p.use_smooth = True
    y, z = rm.uniform(-0.8, 0.8), rm.uniform(-0.8, 0.8)
    while y * y + z * z > 0.7: y, z = rm.uniform(-0.8, 0.8), rm.uniform(-0.8, 0.8)
    x0 = rm.uniform(-14, 6); rot0 = (rm.uniform(0, 180), rm.uniform(0, 180), 0)
    key(o, VS0 - 2, loc=tuple(V0 + V(x0, y, z)), rot=rot0)
    key(o, VS1 + 2, loc=tuple(V0 + V(x0 + 6.5, y + rm.uniform(-0.1, 0.1), z)), rot=(rot0[0] + rm.uniform(-90, 90), rot0[1] + 60, 0))
    interp(o, "LINEAR"); Mi(o)
vcells = []
for k, (x, d0) in enumerate(((-1.6, 0), (0.6, 10), (2.6, 22))):
    c_ = Cell(f"vcell{k}", tuple(V0 + V(x, 0.7, 0.2)), r=0.55, seed=500 + k)
    c_.move([(VS0, V0 + V(x, 0.6, 0.2)), (VS0 + d0, V0 + V(x, 0.75, 0.2)), (VS1 + 1, V0 + V(x + 0.6, 2.4, 0.4))])
    c_.wiggle(VS0 - 2, VS1 + 2, amp=0.3, reach=1.0)
    vcells.append(c_)

# --- E: qahramon makrofag H1 (yutadi, hazm qila olmaydi, o'ladi) va H2 (yangi keladi)
EN0, EN1 = S["engulf"]; TB0, TB1 = S["toobig"]; DI0, DI1 = S["die"]; RL0, RL1 = S["release"]; AG0, AG1 = S["again"]
CRY_R = 0.55
crystal = ink_particle("crystal", tuple(E0), CRY_R, 777)
crystal.rotation_euler = (0.3, 0.5, 0.2); crystal.keyframe_insert("rotation_euler", frame=EN0)
crystal.rotation_euler = (0.3, 0.5, 1.4); crystal.keyframe_insert("rotation_euler", frame=AG1 + 1); interp(crystal, "LINEAR")
for k in range(7):
    a = k * 0.9; ink_particle(f"e_ink{k}", tuple(E0 + V(2.2 * math.cos(a) + 0.5, 2.2 * math.sin(a) + 0.8, rm.uniform(-0.8, 0.6))), rm.uniform(0.1, 0.2), 800 + k)
H1 = Cell("hero1", tuple(E0 + V(-2.4, 0.4, 0.1)), r=0.62, pods=7, seed=901)
H1.move([(EN0, E0 + V(-2.4, 0.4, 0.1)), (EN0 + 30, E0 + V(-1.3, 0.2, 0.05)), (EN0 + 70, E0 + V(-0.15, 0.03, 0.0)), (TB1 + 1, E0 + V(-0.05, 0.0, 0.0))])
H1.wiggle(EN0 - 2, EN0 + 14, amp=0.3)
H1.reach_to(EN0 + 16, EN0 + 66, E0, CRY_R, wrap=1.0)
# hazm qila olmaydi: oyoqchalar kristall atrofida titraydi, tana cho'zilgan
for f in range(EN0 + 68, DI0 + 24, 2):
    loc = H1.loc_at(f)
    for i, (e, d, ph) in enumerate(H1.pods):
        a = 2 * math.pi * i / len(H1.pods)
        ring = V(math.cos(a), math.sin(a) * 0.6, math.sin(a) * 0.8).normalized() * (CRY_R * 0.75)
        e.co = tuple((E0 - loc) + ring * (1 + 0.06 * math.sin(f * 0.9 + ph))); e.keyframe_insert("co", frame=f)
for e, c0 in H1.body:
    e.co = tuple(c0 * 1.3); e.keyframe_insert("co", frame=EN0 + 70); e.radius = e.radius * 1.12; e.keyframe_insert("radius", frame=EN0 + 70)
# fermentlar: "eritmoqchi" da yonadi, "hazm qila olmay" da o'chib-yonadi
H1.enz(1, 0.0); H1.enz(F_ERIT - 2, 0.0); H1.enz(F_ERIT + 3, 9.0)
for f in range(F_ERIT + 8, TB1, 6): H1.enz(f, 9.0 if f < F_HAZM else (3.0 if (f // 6) % 2 else 9.0)); H1.enz(f + 3, 5.0 if f < F_HAZM else 0.5)
H1.enz(TB1 + 1, 2.0); H1.enz(DI0 + 6, 0.0)
for ly in H1.lys:
    p0 = Vector(ly.location)
    key(ly, F_ERIT, loc=tuple(p0))
    key(ly, F_ERIT + 20, loc=tuple(p0.lerp((E0 - H1.loc_at(F_ERIT + 20)) + (p0 - (E0 - H1.loc_at(F_ERIT + 20))).normalized() * CRY_R * 1.05, 0.7)))
# o'lim: kulrang, burishadi, yoriladi
H1.setv("dead", 1, 0.0); H1.setv("dead", DI0 + 4, 0.0); H1.setv("dead", F_OLGAN, 1.0)
for c in mc._fcurves(H1.m.node_tree.animation_data.action):
    for kp in c.keyframe_points: kp.interpolation = "LINEAR"
for f in range(DI0 + 4, F_OLGAN + 4, 2):
    t = (f - DI0 - 4) / (F_OLGAN + 4 - DI0 - 4)
    for e, c0 in H1.body:
        e.radius = H1.r * (1.0 if e is H1.body[0][0] else 0.7) * 1.12 * (1 - 0.3 * t) * (1 + 0.04 * math.sin(f * 1.7)); e.keyframe_insert("radius", frame=f)
POP = F_OLGAN + 6
vis(H1.o, [(1, POP - 1)])
frag_m = mat("frag", (0.4, 0.37, 0.32), 0.5, sss=0.3, alpha=0.8)
for k in range(28):
    d = V(rm.uniform(-1, 1), rm.uniform(-1, 1), rm.uniform(-1, 1)).normalized()
    fr = sphere(f"frag{k}", rm.uniform(0.04, 0.11), (0, 0, 0), frag_m, sub=2)
    c0 = H1.loc_at(POP)
    key(fr, POP, loc=tuple(c0 + d * 0.65), scale=1.0); key(fr, POP + 6, loc=tuple(c0 + d * 1.5), scale=0.8)
    key(fr, AG1, loc=tuple(c0 + d * (2.6 + rm.uniform(0, 1.5))), scale=0.4)
    frames_vis(fr, list(range(POP, AG1 + 1)))
# H2: yangi makrofag chetdan otilib keladi va yutadi
H2 = Cell("hero2", tuple(E0 + V(4.5, -1.5, 0.6)), r=0.66, pods=7, seed=902)
H2.move([(1, E0 + V(4.5, -1.5, 0.6)), (AG0, E0 + V(4.5, -1.5, 0.6)), (AG0 + 22, E0 + V(1.2, -0.3, 0.15)), (AG1 + 1, E0 + V(0.1, 0.0, 0.0))])
H2.wiggle(AG0 - 2, AG0 + 14, amp=0.45, reach=1.15, speed=1.8)
H2.reach_to(AG0 + 16, AG1 + 4, E0, CRY_R, wrap=1.0)
H2.enz(1, 0.0)
vis(H2.o, [(AG0 - 4, END)])

# ======================================================================
# 4) STUDIYA: g'isht devorli tatu salon; Megan kresloda (chap bilagi tayanchda), Leonard stulda — mashinka bilan
# ======================================================================
stu_objs = []
def St(o): stu_objs.append(o); return o
X0, X1, Y0, Y1, HZ = -2.6, 2.6, -3.2, 1.8, 2.9
brick_m = pbr("brick", "brick_wall_001", 0.8, tint=(0.75, 0.62, 0.58))
wall_m = pbr("wall", "painted_plaster_wall", 0.6, tint=(0.22, 0.22, 0.25))
floor_m = pbr("floor", "laminate_floor_02", 0.5, tint=(0.45, 0.4, 0.38))
St(plane("s_floor", (X1 - X0, Y1 - Y0), ((X0 + X1) / 2, (Y0 + Y1) / 2, 0), floor_m))
St(box("s_ceil", (X1 - X0, Y1 - Y0, 0.05), ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ + 0.025), mat("s_ceil_m", (0.05, 0.05, 0.055), 0.8)))
St(box("s_wall_B", (X1 - X0, 0.1, HZ), ((X0 + X1) / 2, Y1 + 0.05, HZ / 2), brick_m))
St(box("s_wall_L", (0.1, Y1 - Y0, HZ), (X0 - 0.05, (Y0 + Y1) / 2, HZ / 2), brick_m))
St(box("s_wall_R", (0.1, Y1 - Y0, HZ), (X1 + 0.05, (Y0 + Y1) / 2, HZ / 2), wall_m))
St(box("s_wall_F", (X1 - X0, 0.1, HZ), ((X0 + X1) / 2, Y0 - 0.05, HZ / 2), wall_m))
def import_fit(nm, loc, rot_z=0.0, scale=1.0, top=None):
    g = import_gltf(PH + f"{nm}/{nm}.gltf", loc, rot_z, scale)
    if top is not None:
        bpy.context.view_layer.update()
        zs = [(o.matrix_world @ Vector(c)).z for o in g.children_recursive if o.type == "MESH" for c in o.bound_box]
        g.location.z += top - max(zs)
    return St(g)
MEG = V(0.0, 0.1, 0.0)
import_fit("modern_arm_chair_01", (0.0, 0.2, 0.0), 0, 1.0)
LEO = V(0.84, -0.17, 0.0)
import_fit("metal_stool_02", tuple(LEO), 0, 1.0)
import_fit("drawer_cabinet", (-1.9, 1.45, 0.0), 180, 1.0)
import_fit("spray_paint_bottles", (-1.9, 1.4, 0.0), 160, 1.0, top=None)
import_fit("wooden_bookshelf_worn", (1.7, 1.55, 0.0), 180, 1.0)
import_fit("potted_plant_01", (-2.25, -0.6, 0.0), 30, 1.3)
import_fit("Sofa_01", (-1.6, -2.6, 0.0), 0, 1.0)
for k, (x, z) in enumerate(((0.35, 1.7), (0.95, 1.45), (-0.2, 1.3))):
    import_fit("fancy_picture_frame_01", (x, Y1 - 0.03, z), 180, 0.9)
LAMP = V(0.3, -0.15, 0.0)
lamp_g = import_fit("hanging_industrial_lamp", tuple(LAMP), 0, 0.75, top=HZ)
# siyoh shishachalari va qopqoqchalar (stol ustida)
TRAY = V(0.62, -0.62, 0.0)
import_fit("WoodenTable_01", tuple(TRAY), 90, (0.4, 0.75, 1.3))
cols = [(0.02, 0.02, 0.02), (0.6, 0.05, 0.05), (0.05, 0.2, 0.6), (0.05, 0.4, 0.1), (0.7, 0.5, 0.05)]
for k in range(5):
    g = St(empty(f"s_bottle{k}", tuple(TRAY + V(-0.06 + 0.04 * k, -0.15 + 0.02 * (k % 2), 0.715))))
    cyl(f"s_bot{k}", 0.014, 0.07, (0, 0, 0.035), mat(f"s_botm{k}", (0.9, 0.9, 0.9), 0.1, trans=0.6), parent=g)
    cyl(f"s_botink{k}", 0.012, 0.05, (0, 0, 0.027), mat(f"s_botink{k}", cols[k], 0.2), parent=g)
    cyl(f"s_botcap{k}", 0.008, 0.022, (0, 0, 0.081), mat(f"s_cap{k}", (0.02, 0.02, 0.02), 0.4), parent=g)
    St(cyl(f"s_inkcap{k}", 0.008, 0.012, tuple(TRAY + V(-0.05 + 0.03 * k, 0.05, 0.721)), mat(f"s_ic{k}", cols[k], 0.2)))
St(box("s_towel", (0.2, 0.25, 0.012), tuple(TRAY + V(0.0, 0.18, 0.721)), mat("s_towel_m", (0.15, 0.35, 0.75), 0.9)))
# neon yozuvlar
def neon(name, body, loc, size, col):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.bevel_depth = size * 0.04
    cu.extrude = 0.0; cu.fill_mode = "NONE"; cu.offset = -size * 0.03
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = (R(90), 0, R(180))
    cu.materials.append(mat(name + "_m", col, 0.3, emit=7.0)); return St(o)
neon("s_neon1", "TATTOO", (-0.95, Y1 - 0.04, 1.95), 0.32, (1.0, 0.1, 0.55))
neon("s_neon2", "INK", (-0.95, Y1 - 0.04, 1.55), 0.22, (0.15, 0.6, 1.0))
# bilak tayanchi
EL = V(0.25, -0.03, 0.775); ADIR = V(0.06, -1.0, 0.03).normalized(); WR = EL + ADIR * 0.245
pad = St(box("s_armpad", (0.12, 0.46, 0.05), tuple((EL + WR) / 2 + V(0, -0.03, -0.062)), mat("s_pad_m", (0.02, 0.02, 0.022), 0.35, coat=0.4), bevel=0.015))
pad.rotation_euler.z = math.atan2(ADIR.x, -ADIR.y) * -1
St(cyl("s_armpost", 0.018, 0.7, (EL.x + 0.012, (EL.y + WR.y) / 2, 0.36), steel_m))
St(cyl("s_armbase", 0.16, 0.02, (EL.x + 0.012, (EL.y + WR.y) / 2, 0.01), mat("s_base_m", (0.03, 0.03, 0.03), 0.3, metal=0.6)))
St(box("s_film", (0.12, 0.46, 0.002), tuple((EL + WR) / 2 + V(0, -0.03, -0.035)), mat("s_film_m", (0.9, 0.95, 1.0), 0.05, trans=0.8)))

def soften(meshes, rough=0.5):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = rough
                    n.inputs["Coat Weight"].default_value = 0.0
def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm_, act, start, repeat=1.0, speed=1.0, src=None, bi=0, bo=0):
    s = mc.add_strip(arm_, act, start, repeat=repeat, speed=speed, blend=0, hold=False, src=src)
    s.use_auto_blend = False; s.blend_in = bi; s.blend_out = bo; return s
def span(act, n):
    a, b = act.frame_range; return n / ((b - a) * 0.8)
def bone_c(arm_, bone, kind, target, **kw):
    c = arm_.pose.bones["mixamorig:" + bone].constraints.new(kind); c.target = target
    for k, v in kw.items(): setattr(c, k, v)
    return c
mroot, meg, mmeshes = mc.load_character("meg", "Megan.fbx"); sc.render.fps = 24
soften(mmeshes, 0.48)
mroot.location = tuple(MEG)
SIT = A_("Sitting_Idle_4.fbx")
strip(meg, SIT, -10, repeat=span(SIT, END + 20))
ikL = St(empty("meg_ikL", tuple(WR)))
bone_c(meg, "LeftForeArm", "IK", ikL, chain_count=2, use_tail=True)
handT = St(empty("meg_handT", tuple(WR + ADIR * 0.2 + V(0, 0, -0.03))))
palmT = St(empty("meg_palmT", tuple(WR + ADIR * 0.06 + V(0, 0, -0.3))))
bone_c(meg, "LeftHand", "DAMPED_TRACK", handT, track_axis="TRACK_Y")
bone_c(meg, "LeftHand", "LOCKED_TRACK", palmT, track_axis="TRACK_Z", lock_axis="LOCK_Y")
lookT = St(empty("meg_lookT", tuple((EL + WR) / 2 + V(0, 0, 0.03))))
bone_c(meg, "Head", "DAMPED_TRACK", lookT, track_axis="TRACK_Z", influence=0.55)
bone_c(meg, "Neck", "DAMPED_TRACK", lookT, track_axis="TRACK_Z", influence=0.25)
# bilakdagi tatu (decal): bilak ustiga qo'yilgan to'r, Megan tanasiga shrinkwrap
sc.frame_set(S["studio"][0]); bpy.context.view_layer.update()
body = next(o for o in mmeshes if o.name.endswith("Body"))
SIDE = ADIR.cross(V(0, 0, 1)).normalized()
MIDA = EL + ADIR * 0.14
dg = bpy.context.evaluated_depsgraph_get()
hit, TOPP, nrm, *_ = sc.ray_cast(dg, MIDA + V(0, 0, 0.2), V(0, 0, -1))
print("forearm top hit", hit, tuple(round(x, 3) for x in TOPP))
if not hit: TOPP = MIDA + V(0, 0, 0.032)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=0.07, location=(0, 0, 0))
dec = bpy.context.object; dec.name = "meg_tattoo"
for v in dec.data.vertices: v.co.z = -(v.co.y ** 2) * 9.0
mw = Matrix((ADIR, SIDE * -1, ADIR.cross(SIDE * -1))).transposed().to_4x4(); mw.translation = TOPP + V(0, 0, 0.004)
dec.matrix_world = mw
sw = dec.modifiers.new("sw", "SHRINKWRAP"); sw.target = body; sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.offset = 0.0007
dec_m = skin_tat_mat("dec_skin", "UV", decal=True, base=(0.8, 0.57, 0.46)); TAT_MATS.append(dec_m); dec.data.materials.append(dec_m)
St(dec)
def dec_point(u, v):
    return TOPP + ADIR * ((u - 0.5) * 0.07) + SIDE * (-(v - 0.5) * 0.07)
# Leonard (usta) — stulda, Typing; qo'llari IK bilan mashinka va bilakda
lroot, leo, lmeshes = mc.load_character("leo", "Leonard.fbx"); sc.render.fps = 24
soften(lmeshes, 0.55)
lroot.location = tuple(LEO); lroot.rotation_euler = (0, 0, R(-90))
TYP = A_("Typing.fbx")
strip(leo, TYP, -5, repeat=span(TYP, END + 20))
PEN_S = V(0.55, 0.2, 0.8).normalized()
spen, snd = tattoo_pen("stu_pen"); aim(spen, PEN_S); St(spen)
SU0, SU1 = S["studio"]
for f in range(SU0 - 2, SU1 + 4, 3):
    t = (f - SU0) / (SU1 - SU0)
    u = 0.52 + 0.04 * t; _, v = moon_point(u)
    p = dec_point(u, v) + V(0, 0, 0.0015 * math.sin(f * 1.7))
    spen.location = tuple(p); spen.keyframe_insert("location", frame=f)
needle_buzz(snd, SU0 - 2, SU1 + 2)
gripT = St(empty("leo_gripT")); cl_ = gripT.constraints.new("COPY_LOCATION"); cl_.target = spen
gripO = empty("leo_gripO", tuple(PEN_S * 0.075), gripT); St(gripO)
bone_c(leo, "RightForeArm", "IK", gripO, chain_count=2, use_tail=True)
rhT = St(empty("leo_rhT")); c_ = rhT.constraints.new("COPY_LOCATION"); c_.target = spen
bone_c(leo, "RightHand", "DAMPED_TRACK", rhT, track_axis="TRACK_Y", influence=0.8)
lhT = St(empty("leo_lhT", tuple(WR + V(0.03, 0.02, 0.05))))
bone_c(leo, "LeftForeArm", "IK", lhT, chain_count=2, use_tail=True)
lhD = St(empty("leo_lhD", tuple(WR + V(-0.1, -0.02, 0.0))))
bone_c(leo, "LeftHand", "DAMPED_TRACK", lhD, track_axis="TRACK_Y", influence=0.7)
bone_c(leo, "Head", "DAMPED_TRACK", lookT, track_axis="TRACK_Z", influence=0.6)
for o in mmeshes + lmeshes: vis(o, STUR, recursive=False)
vis(spen, STUR); vis(dec, STUR, recursive=False)
for m_ in TAT_MATS:
    for f, v in PROG: val_key(m_, "prog", f, v)
    ckey(m_.node_tree)

# ======================================================================
# 5) KO'RINISH (dunyolar)
# ======================================================================
for o in mac_objs: vis(o, MACR)
for o in cut_objs: vis(o, CUTR)
for o in shells: vis(o, [S["stuck"]])
for o in mic_objs: vis(o, MICR)
for c_ in CELLS:
    if c_ not in (H1, H2): vis(c_.o, MICR)
for o in stu_objs:
    if o.name not in ("meg_tattoo", "stu_pen"): vis(o, STUR)

# ======================================================================
# 6) KAMERALAR
# ======================================================================
def abs_cam(name, pts, tgt_pts, lens, fstop, clip=0.002):
    t = empty(name + "_t"); path_keys(t, tgt_pts)
    c = shot_cam(name, (0, 0, 0), t, lens, fstop, focus=t, clip=clip); path_keys(c, pts)
    return c
def TPu(u): return surf(*moon_point(u))
# 1 ILGAK: makro, teri sathidan, keng ob'ektiv, crash push-in
H0, H1f = S["hook"]; tp0, tp1 = TPu(0.45), TPu(0.5)
c = abs_cam("hook", [(H0, tp0 + V(0.05, -0.13, 0.004)), (H0 + 8, tp0 + V(0.035, -0.085, 0.006)), (H1f, tp1 + V(0.02, -0.06, 0.008))],
            [(H0, tp0 + V(0, 0, 0.012)), (H1f, tp1 + V(0, 0, 0.006))], 16, 11.0, clip=0.001)
lens_keys(c, [(H0, 15), (H0 + 8, 19), (H1f, 21)]); shake(c, H0 + 6, H1f, 0.0015, seed=1)
# 2 po'st ko'chishi: kesim, yonlama siljish
A0, A1 = S["shed"]
abs_cam("shed", [(A0, CP(-0.42, -0.78, 0.55)), (A1, CP(0.02, -0.82, 0.5))], [(A0, CP(-0.06, -0.15, 0.27)), (A1, CP(0.04, -0.15, 0.27))], 30, 5.6)
# 3 studiya: past burchak, keng, aylanma
A0, A1 = S["studio"]; PP = dec_point(*moon_point(0.54))
c = abs_cam("studio", [(A0, V(-0.7, -1.4, 0.72)), (A1, V(-0.2, -1.6, 0.78))], [(A0, V(0.22, -0.05, 0.8)), (A1, V(0.3, -0.08, 0.78))], 20, 2.8)
c.data.dof.focus_object = None; c.data.dof.focus_distance = (V(-0.45, -1.45, 0.58) - PP).length
# 4 tayyor tatu: makro, sekin push-in
A0, A1 = S["surface"]; cc = surf(0.47, 0.5)
abs_cam("surface", [(A0, cc + V(0.09, -0.15, 0.09)), (A1, cc + V(0.05, -0.095, 0.06))], [(A0, cc), (A1, cc + V(0.003, 0, 0))], 35, 16.0, clip=0.001)
# 5 bo'yoq emas: kesim, tepadan pastga crash zoom
A0, A1 = S["notpaint"]
c = abs_cam("notpaint", [(A0, CP(0.02, -0.1, 0.72)), (A0 + 9, CP(0.02, -0.32, 0.5)), (A0 + 14, CP(0.03, -0.46, 0.3)), (A1, CP(0.04, -0.44, 0.27))],
            [(A0, CP(0.0, 0.0, 0.3)), (A0 + 9, CP(0.0, -0.12, 0.27)), (A0 + 14, CP(0.02, -0.2, 0.235)), (A1, CP(0.02, -0.2, 0.235))], 24, 6.0)
lens_keys(c, [(A0, 22), (A0 + 9, 26), (A0 + 14, 40), (A1, 42)]); shake(c, A0 + 14, A0 + 24, 0.006, seed=5)
# 6 urush: mikro, past burchakdan oldinga uchish
A0, A1 = S["war"]
abs_cam("war", [(A0, W0 + V(-3.6, -4.8, -1.0)), (A1, W0 + V(-1.7, -3.1, -0.7))], [(A0, W0 + V(0, 0, 0.1)), (A1, W0 + V(0.2, 0.1, 0.1))], 18, 2.8)
# 7 tugamas urush: crash zoom
A0, A1 = S["urush"]; hw = hero_w.loc_at(F_URUSH)
c = abs_cam("urush", [(A0, hw + V(1.7, -2.7, 0.6)), (F_URUSH - 1, hw + V(1.25, -2.05, 0.45)), (F_URUSH + 2, hw + V(0.75, -1.3, 0.28)), (A1, hw + V(0.62, -1.08, 0.2))],
            [(A0, hw), (A1, hw + V(0, 0, 0.05))], 24, 2.8)
lens_keys(c, [(A0, 22), (F_URUSH - 1, 26), (F_URUSH + 2, 38), (A1, 40)]); shake(c, F_URUSH, F_URUSH + 12, 0.06, seed=7)
# 8 igna: makro yondan, qo'l kamerasi
A0, A1 = S["needle"]; tn0, tn1 = TPu(0.58), TPu(0.62)
c = abs_cam("needle", [(A0, tn0 + V(0.085, -0.03, 0.006)), (A1, tn1 + V(0.065, -0.028, 0.006))], [(A0, tn0 + V(0, 0, 0.004)), (A1, tn1 + V(0, 0, 0.004))], 42, 16.0, clip=0.001)
shake(c, A0, A1, 0.0012, seed=8, decay=False)
# 9 teshish: kesim, push-in
A0, A1 = S["pierce"]
abs_cam("pierce", [(A0, CP(-0.06, -0.62, 0.33)), (A1, CP(0.03, -0.48, 0.29))], [(A0, CP(-0.12, -0.2, 0.25)), (A1, CP(0.02, -0.2, 0.25))], 30, 5.6)
# 10 hujum: kesim, aylanma + silkinish
A0, A1 = S["attack"]
c = shot_cam("attack", (0, 0, 0), empty("attack_t", tuple(CP(0, -0.15, 0.18))), 26, 5.6)
orbit(c, A0, A1, CP(0, -0.15, 0.1), 0.8, 0.62, -40, 25, 0.18, 0.32)
shake(c, F_HUJUM, F_HUJUM + 12, 0.02, seed=10)
# 11 qon tomiri: yonlama siljish
A0, A1 = S["vessel"]
abs_cam("vessel", [(A0, V0 + V(-3.6, -5.4, 0.9)), (A1, V0 + V(0.6, -5.0, 1.3))], [(A0, V0 + V(-1.2, 0.8, 0.2)), (A1, V0 + V(1.2, 1.5, 0.3))], 26, 3.5)
# 12 yirtqich: past burchakdan crash zoom
A0, A1 = S["predator"]; pl = pred.loc_at(A0 + 20)
c = abs_cam("predator", [(A0, pl + V(0.9, -3.2, -1.3)), (A0 + 7, pl + V(0.45, -1.7, -0.7)), (A1, pl + V(0.3, -1.35, -0.55))], [(A0, pl + V(0, 0, 0.1)), (A1, pl + V(0, -0.2, 0.1))], 16, 2.8)
lens_keys(c, [(A0, 15), (A0 + 7, 21), (A1, 22)]); shake(c, A0 + 6, A0 + 18, 0.05, seed=12)
# 13 yutish: aylanma
A0, A1 = S["engulf"]
c = shot_cam("engulf", (0, 0, 0), empty("engulf_t", tuple(E0 + V(-0.6, 0, 0.1))), 30, 3.2)
orbit(c, A0, A1, E0 + V(-0.6, 0, 0), 3.4, 2.5, -55, -5, 0.8, 1.0)
# 14 hazm qila olmaydi: sekin push-in
A0, A1 = S["toobig"]
abs_cam("toobig", [(A0, E0 + V(1.3, -2.5, 0.6)), (A1, E0 + V(0.7, -1.55, 0.3))], [(A0, E0 + V(-0.1, 0, 0.05)), (A1, E0)], 35, 2.8)
# 15 qotib qoladi: kesim, tez orqaga uchish
A0, A1 = S["stuck"]
c = abs_cam("stuck", [(A0, CP(0.0, -0.3, 0.235)), (A0 + 12, CP(-0.1, -0.6, 0.35)), (A1, CP(-0.3, -1.05, 0.62))], [(A0, CP(0.0, -0.2, 0.232)), (A1, CP(0.0, -0.05, 0.16))], 40, 6.0)
lens_keys(c, [(A0, 42), (A0 + 12, 30), (A1, 24)])
# 16 o'lim: timelapse
A0, A1 = S["die"]
abs_cam("die", [(A0, E0 + V(-1.1, -2.5, 0.9)), (A1, E0 + V(-0.6, -1.9, 0.6))], [(A0, E0), (A1, E0 + V(0, 0, 0.05))], 32, 2.8)
# 17 bo'shagan siyoh: sekin aylanma
A0, A1 = S["release"]
c = shot_cam("release", (0, 0, 0), crystal, 30, 2.8)
orbit(c, A0, A1, E0, 3.4, 3.0, 20, 50, 0.5, 0.7)
# 18 yangi hujayra: ergashuvchi
A0, A1 = S["again"]
pts = [(f, H2.loc_at(f) * 0.35 + E0 * 0.65 + V(1.5, -2.9, 0.5)) for f in range(A0, A1 + 1, 6)]
tgt = [(f, H2.loc_at(f).lerp(E0, 0.45)) for f in range(A0, A1 + 1, 6)]
abs_cam("again", pts, tgt, 28, 2.8)
# 19 yakun: tayyor tatu, tez push-in
A0, A1 = S["final"]; cc = surf(0.5, 0.5)
abs_cam("final", [(A0, cc + V(0.12, -0.2, 0.14)), (A1, cc + V(0.05, -0.08, 0.06))], [(A0, cc), (A1, cc)], 24, 16.0, clip=0.001)
for n, cam in CAMS.items():
    for fc in fcurves(cam):
        for k in fc.keyframe_points:
            if k.interpolation == "BEZIER": k.interpolation = "LINEAR"
    for fc in fcurves(cam.data):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
for f, n in SHOTS:
    sc.timeline_markers.new(n, frame=f).camera = CAMS[n]
sc.camera = CAMS["hook"]

# ======================================================================
# 7) YORUG'LIK VA FON
# ======================================================================
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; L = w.node_tree.links
out = N["World Output"]; bgn = N["Background"]
def world_of(n): return "mac" if n in MACN else "cut" if n in CUTN else "stu" if n in STUN else "mic"
WORLD = {"mac": ((0.004, 0.004, 0.006), 1.0), "cut": ((0.012, 0.017, 0.032), 1.0), "stu": ((0.01, 0.01, 0.012), 1.0), "mic": ((0.07, 0.012, 0.018), 1.0)}
for f, n in SHOTS:
    col, s_ = WORLD[world_of(n)]
    bgn.inputs[0].default_value = (*col, 1); bgn.inputs[0].keyframe_insert("default_value", frame=f)
    bgn.inputs[1].default_value = s_; bgn.inputs[1].keyframe_insert("default_value", frame=f)
interp(w.node_tree, "CONSTANT")
# makro
MT = empty("macT", tuple(surf(0.4, 0.45)))
area("M_key", tuple(MAC + V(-0.25, -0.35, 0.55)), 0.45, (1.0, 0.93, 0.85), lights_for(MACR, 8.0), target=MT)
area("M_fill", tuple(MAC + V(0.4, -0.1, 0.2)), 0.4, (0.75, 0.85, 1.0), lights_for(MACR, 2.0), target=MT)
area("M_rim", tuple(MAC + V(0.05, 0.45, 0.35)), 0.35, (1.0, 0.35, 0.75), lights_for(MACR, 7.0), target=MT)
# kesim
CT = empty("cutT", tuple(CP(0, -0.15, 0.2)))
area("C_key", tuple(CP(-0.7, -0.9, 0.95)), 0.9, (1.0, 0.95, 0.9), lights_for(CUTR, 30.0), target=CT)
area("C_fill", tuple(CP(0.85, -0.6, 0.35)), 0.6, (0.85, 0.9, 1.0), lights_for(CUTR, 9.0), target=CT)
area("C_rim", tuple(CP(0.3, 0.9, 0.9)), 0.8, (0.4, 0.6, 1.0), lights_for(CUTR, 22.0), target=CT)
attack_red = point("C_red", tuple(CP(0.1, -0.7, 0.35)), 0.2, (1.0, 0.08, 0.05), [(1, 0), (S["attack"][0], 0), (F_HUJUM - 1, 0), (F_HUJUM, 25.0), (F_HUJUM + 10, 6.0), (S["attack"][1] + 1, 0)], const=False)
# studiya
LT = empty("stuT", tuple(PP))
area("S_lamp", tuple(V(0.3, -0.15, 1.75)), 0.35, (1.0, 0.72, 0.45), lights_for(STUR, 70.0), target=LT)
area("S_neon", (-0.95, Y1 - 0.4, 1.8), 1.0, (1.0, 0.2, 0.6), lights_for(STUR, 40.0), target=LT)
area("S_fill", (-1.4, -1.6, 1.4), 1.2, (0.55, 0.7, 1.0), lights_for(STUR, 35.0), target=LT)
area("S_rim", (1.6, 1.2, 2.0), 0.8, (0.7, 0.8, 1.0), lights_for(STUR, 45.0), target=LT)
lamp_bulb = point("S_bulb", (0.3, -0.15, 1.95), 0.03, (1.0, 0.7, 0.4), lights_for(STUR, 15.0))
# mikro: har sahnaga alohida
def mic_lights(nm, c, shots, k=1.0, flicker=None):
    rr = rng(*shots); ct = empty(nm + "_T", tuple(c))
    ks = lights_for(rr, 900.0 * k)
    if flicker:
        a, b = flicker; ks = [x for x in ks if not (a <= x[0] <= b)]
        rf = random.Random(4)
        for f in range(a, b + 1, 3): ks.append((f, 900.0 * k * rf.choice((0.35, 1.0, 0.6, 1.3))))
        ks.sort()
    area(nm + "_key", tuple(c + V(-4.0, -4.5, 6.0)), 3.0, (1.0, 0.92, 0.85), ks, target=ct)
    area(nm + "_rim", tuple(c + V(3.5, 5.0, 2.5)), 3.0, (0.45, 0.6, 1.0), lights_for(rr, 700.0 * k), target=ct)
    area(nm + "_fill", tuple(c + V(4.5, -4.0, -2.0)), 3.0, (1.0, 0.45, 0.55), lights_for(rr, 260.0 * k), target=ct)
mic_lights("W", W0, ("war", "urush"))
mic_lights("WP", W0 + V(4.4, -3.4, 0), ("predator",))
mic_lights("VL", V0, ("vessel",))
mic_lights("E", E0, ("engulf", "toobig", "die", "release", "again"), flicker=(S["die"][0] + 4, F_OLGAN))
urush_red = point("W_red", tuple(hero_w.loc_at(F_URUSH) + V(0.5, -1.2, 0.6)), 0.5, (1.0, 0.1, 0.06),
                  [(1, 0), (F_URUSH - 1, 0), (F_URUSH, 400.0), (F_URUSH + 12, 60.0), (S["urush"][1] + 1, 0)], const=False)

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
