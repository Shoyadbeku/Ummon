# Demodex kanasi, mikro teri yuzasi (teshiklar, tuklar, po'st parchalari) va teri/tuk illizi kesimi uchun procedural modellar.
# Mikro dunyo 1000x: kana ~0.3 mm -> 0.30 m. Kana mahalliy o'qlari: bosh +Y, orqa +Z, oyoqlar -Z tomonda; markaz = oyoqli qism (podosoma).
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

R = math.radians

def _link(o, parent=None):
    bpy.context.scene.collection.objects.link(o)
    if parent is not None: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); e.location = loc; return _link(e, parent)

def math_n(N, L, op, a, b=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0]

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]

# ======================= KANA TANASI =======================
TAIL_Y, HEAD_Y = -0.225, 0.085
LEG_Y = (0.047, 0.027, 0.007, -0.013)

def _radius(y):
    """tana kesimi radiusi (m) y bo'yicha: dum -> qorin (halqali) -> oyoqli qism -> og'iz"""
    if y < -0.02:                                   # opistosoma (uzun, halqali dum)
        t = (y - TAIL_Y) / (-0.02 - TAIL_Y)          # 0 dum uchi, 1 oyoqli qism boshi
        base = 0.034 * (1 - (1 - t) ** 2.2) ** 0.55 + 0.004
        ring = 1 - 0.07 * abs(math.sin(math.pi * (y - TAIL_Y) / 0.0105)) ** 3 * min(1, t * 6)
        return base * ring
    if y < 0.055:                                   # podosoma
        t = (y + 0.02) / 0.075
        return 0.038 + 0.006 * math.sin(math.pi * t)
    t = (y - 0.055) / (HEAD_Y - 0.055)               # gnatosoma (og'iz qismi)
    return max(0.0, 0.032 * (1 - t ** 1.6) ** 0.7 * (1 - 0.45 * t))

def mite_mesh(name="mite_body", NY=150, NP=36):
    verts, faces = [], []
    ys = [TAIL_Y + (HEAD_Y - TAIL_Y) * (i / (NY - 1)) for i in range(NY)]
    for y in ys[1:-1]:
        r = _radius(y)
        for j in range(NP):
            a = 2 * math.pi * j / NP
            z = math.sin(a); x = math.cos(a)
            zs = 0.78 if z < 0 else 0.92                   # qorin tomoni yassiroq
            verts.append((r * x, y, r * z * zs))
    n = len(ys) - 2
    for i in range(n - 1):
        for j in range(NP):
            a = i * NP + j; b = i * NP + (j + 1) % NP
            faces.append((a, b, b + NP, a + NP))
    t0 = len(verts); verts.append((0, TAIL_Y, 0)); h0 = len(verts); verts.append((0, HEAD_Y, -0.004))
    for j in range(NP):
        faces.append((t0, (j + 1) % NP, j))
        faces.append((h0, (n - 1) * NP + j, (n - 1) * NP + (j + 1) % NP))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    for p in me.polygons: p.use_smooth = True
    # "dumlilik" atributi (0 bosh .. 1 dum uchi) — rentgen/axlat uchun
    at = me.attributes.new("tail", "FLOAT", "POINT")
    for i, v in enumerate(me.vertices): at.data[i].value = max(0.0, min(1.0, (-0.02 - v.co.y) / (-0.02 - TAIL_Y)))
    return me

def leg_mesh(name="mite_leg"):
    """oyoq: kalta, bo'g'imli (3 bo'g'im), uchida 2 ta tirnoq. Ildizi (0,0,0), -Z ga qarab."""
    bm = bmesh.new()
    segs = ((0.0, 0.0105, 0.009), (-0.011, 0.0088, 0.0075), (-0.021, 0.0072, 0.006), (-0.029, 0.0055, 0.0))
    for k in range(3):
        z0, r0, _ = segs[k]; z1, r1, _ = segs[k + 1]
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r0, radius2=r1 * 1.05, depth=abs(z1 - z0) * 1.15)
        bmesh.ops.translate(bm, verts=res["verts"], vec=(0, 0, (z0 + z1) / 2))
        sp = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r1 * 1.08)
        bmesh.ops.translate(bm, verts=sp["verts"], vec=(0, 0, z1))
    for sx in (-1, 1):
        cl = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.0022, radius2=0.0003, depth=0.009)
        bmesh.ops.rotate(bm, verts=cl["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(R(25 * sx), 3, "Y"))
        bmesh.ops.translate(bm, verts=cl["verts"], vec=(0.002 * sx, 0, -0.033))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me

def palp_mesh(name="mite_palp"):
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0065, radius2=0.0035, depth=0.022)
    bmesh.ops.translate(bm, verts=res["verts"], vec=(0, 0, 0.011))
    sp = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.0042); bmesh.ops.translate(bm, verts=sp["verts"], vec=(0, 0, 0.022))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me

def mite_material(name="mite_m"):
    """sutsimon-sarg'ish, yarim shaffof (SSS), ho'l yaltiroq; ichida donachalar. 'dead' 0..1 — kulrang-jigarrang, xira"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.65; b.inputs["Subsurface Scale"].default_value = 0.012
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.75, 0.5)
    b.inputs["Roughness"].default_value = 0.32; b.inputs["Coat Weight"].default_value = 0.45; b.inputs["Coat Roughness"].default_value = 0.12
    dead = value_node(m, "dead", 0.0)
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60.0; nz.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 110.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    ta = N.new("ShaderNodeAttribute"); ta.attribute_name = "tail"
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"
    c1.inputs[6].default_value = (0.8, 0.66, 0.46, 1); c1.inputs[7].default_value = (0.62, 0.46, 0.28, 1)
    L.new(math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 1.2), c1.inputs["Factor"])
    # ichki donachalar (dumda ko'proq): qoramtir dog'lar
    gr = math_n(N, L, "MULTIPLY", math_n(N, L, "LESS_THAN", vo.outputs["Distance"], 0.22), math_n(N, L, "ADD", ta.outputs["Fac"], 0.25))
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.inputs[7].default_value = (0.5, 0.36, 0.2, 1)
    L.new(c1.outputs[2], c2.inputs[6]); L.new(math_n(N, L, "MULTIPLY", gr, 0.55), c2.inputs["Factor"])
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"; c3.inputs[7].default_value = (0.36, 0.31, 0.26, 1)
    L.new(c2.outputs[2], c3.inputs[6]); L.new(dead, c3.inputs["Factor"])
    L.new(c3.outputs[2], b.inputs["Base Color"])
    L.new(math_n(N, L, "MULTIPLY", math_n(N, L, "SUBTRACT", 1.0, dead), 0.65), b.inputs["Subsurface Weight"])
    L.new(math_n(N, L, "ADD", 0.32, math_n(N, L, "MULTIPLY", dead, 0.5)), b.inputs["Roughness"])
    # halqa izlari (bump)
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.002
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

class Kit:
    """umumiy mesh va materiallar (hamma kanalar ulashadi)"""
    def __init__(self, mat=None):
        self.body = mite_mesh(); self.leg = leg_mesh(); self.palp = palp_mesh()
        self.mat = mat or mite_material()
        for me in (self.body, self.leg, self.palp): me.materials.append(self.mat)

def _drive(obj, path, idx, root, expr):
    d = obj.driver_add(path, idx).driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "ph"; v.type = "SINGLE_PROP"
    v.targets[0].id_type = "OBJECT"; v.targets[0].id = root; v.targets[0].data_path = '["ph"]'
    v2 = d.variables.new(); v2.name = "a"; v2.type = "SINGLE_PROP"
    v2.targets[0].id_type = "OBJECT"; v2.targets[0].id = root; v2.targets[0].data_path = '["amp"]'
    d.expression = expr

def build_mite(name, kit, parent=None, legs=True, mat=None, seed=0):
    """root (bo'sh) -> tana, 8 oyoq, 2 paypaslagich. root['ph'] (yurish fazasi, aylanish), root['amp'] (0..1 oyoq tebranishi)."""
    root = empty(name, (0, 0, 0), parent)
    root["ph"] = random.Random(seed).random(); root["amp"] = 1.0
    body = _link(bpy.data.objects.new(name + "_body", kit.body), root)
    if mat is not None: body.material_slots[0].link = "OBJECT"; body.material_slots[0].material = mat
    sd = body.modifiers.new("sub", "SUBSURF"); sd.levels = 0; sd.render_levels = 1
    parts = [body]
    if legs:
        for i, y in enumerate(LEG_Y):
            for sx in (-1, 1):
                lg = _link(bpy.data.objects.new(f"{name}_leg{i}{'LR'[sx > 0]}", kit.leg), root)
                if mat is not None: lg.material_slots[0].link = "OBJECT"; lg.material_slots[0].material = mat
                lg.location = (sx * 0.033, y, -0.014); lg.scale = (1.45, 1.45, 1.6)
                lg.rotation_mode = "XYZ"
                base_y = sx * R(55)                          # yonga va pastga
                off = (i % 2) * math.pi + (0 if sx > 0 else math.pi)
                fw = -10 + 12 * i                            # old oyoqlar oldinga, orqadagilar orqaga
                lg.rotation_euler = (R(fw), base_y, 0)
                _drive(lg, "rotation_euler", 0, root, f"{R(fw):.4f}+0.45*a*sin(ph*6.2832+{off:.3f})")
                _drive(lg, "rotation_euler", 1, root, f"{base_y:.4f}+{sx}*0.22*a*max(0,cos(ph*6.2832+{off:.3f}))")
                parts.append(lg)
        for sx in (-1, 1):
            pp = _link(bpy.data.objects.new(f"{name}_palp{'LR'[sx > 0]}", kit.palp), root)
            if mat is not None: pp.material_slots[0].link = "OBJECT"; pp.material_slots[0].material = mat
            pp.location = (sx * 0.012, 0.07, -0.006); pp.rotation_euler = (R(-62), sx * R(14), 0)
            _drive(pp, "rotation_euler", 0, root, f"{R(-62):.4f}+0.25*a*sin(ph*12.566+{sx})")
            parts.append(pp)
    root["parts"] = len(parts)
    return root, body

def walk(root, f0, f1, cycles):
    """yurish fazasi: f0..f1 orasida 'cycles' marta oyoq qadami (chiziqli)"""
    root["ph"] = float(root["ph"]); root.keyframe_insert('["ph"]', frame=f0)
    root["ph"] = float(root["ph"]) + cycles; root.keyframe_insert('["ph"]', frame=f1)
    for fc in _fcurves(root.animation_data.action):
        if fc.data_path == '["ph"]':
            for k in fc.keyframe_points: k.interpolation = "LINEAR"

def _fcurves(act):
    if hasattr(act, "layers") and act.layers:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return list(act.fcurves)

def orient(fwd, up=Vector((0, 0, 1)), compat=None):
    """kana root burilishi: bosh (+Y) 'fwd' ga, orqa (+Z) 'up' ga; compat — oldingi burilish (sakrashsiz)"""
    Y = Vector(fwd).normalized(); Z = (Vector(up) - Y * Vector(up).dot(Y)).normalized(); X = Y.cross(Z)
    m = Matrix((X, Y, Z)).transposed()
    return m.to_euler("XYZ", compat) if compat is not None else m.to_euler()

# ======================= MIKRO TERI YUZASI =======================
class Skin:
    """size x size (m) yuza, markaz (0,0), balandlik H(x,y). Teshiklar: (x, y, r, chuqurlik)."""
    def __init__(self, size, pores, seed=3):
        self.size = size; self.pores = pores; self.rnd = random.Random(seed)
        self.waves = [(self.rnd.uniform(0.6, 1.6), self.rnd.uniform(0, 6.28), self.rnd.uniform(0, 6.28), self.rnd.uniform(0.006, 0.016)) for _ in range(9)]
    def H(self, x, y):
        h = 0.0
        for k, a, p, amp in self.waves:
            h += amp * math.sin(k * (x * math.cos(a) + y * math.sin(a)) + p)
        for px, py, r, d in self.pores:
            q = math.hypot(x - px, y - py)
            if q < r: h -= d * (1 - q / r) ** 1.7
            h += 0.035 * math.exp(-((q - r * 1.05) / (0.35 * r)) ** 2)      # teshik labi
        return h
    def depth_fac(self, x, y):
        f = 0.0
        for px, py, r, d in self.pores:
            q = math.hypot(x - px, y - py)
            if q < r: f = max(f, (1 - q / r) ** 0.8)
        return f

def skin_surface(name, sk, res, mat, parent=None):
    n = int(sk.size / res) + 1
    bm = bmesh.new()
    vs = []
    for j in range(n):
        for i in range(n):
            x = -sk.size / 2 + i * res; y = -sk.size / 2 + j * res
            vs.append(bm.verts.new((x, y, sk.H(x, y))))
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            bm.faces.new((vs[a], vs[a + 1], vs[a + n + 1], vs[a + n]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    at = me.attributes.new("pd", "FLOAT", "POINT")
    for i, v in enumerate(me.vertices): at.data[i].value = sk.depth_fac(v.co.x, v.co.y)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); return _link(o, parent)

def skin_micro_material(name="skin_micro"):
    """mikro teri: pushti-bej, hujayra plastinkalari (Voronoi), ho'l yog' yaltirashi; teshik ichi qizg'ish-qorong'i ('pd')"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.45; b.inputs["Subsurface Scale"].default_value = 0.05
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Coat Weight"].default_value = 0.35; b.inputs["Coat Roughness"].default_value = 0.2
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 2.6
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    vo2 = N.new("ShaderNodeTexVoronoi"); vo2.feature = "DISTANCE_TO_EDGE"; vo2.inputs["Scale"].default_value = 9.0
    L.new(tc.outputs["Object"], vo2.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.0; nz.inputs["Detail"].default_value = 8.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    pd = N.new("ShaderNodeAttribute"); pd.attribute_name = "pd"
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"
    c1.inputs[6].default_value = (0.62, 0.36, 0.28, 1); c1.inputs[7].default_value = (0.78, 0.5, 0.4, 1)
    L.new(nz.outputs["Fac"], c1.inputs["Factor"])
    ed = math_n(N, L, "SUBTRACT", 1.0, math_n(N, L, "DIVIDE", vo.outputs["Distance"], 0.05), clamp=True)    # plastinka chetlari
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.inputs[7].default_value = (0.88, 0.72, 0.6, 1)
    L.new(c1.outputs[2], c2.inputs[6]); L.new(math_n(N, L, "MULTIPLY", ed, 0.25), c2.inputs["Factor"])
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"; c3.inputs[7].default_value = (0.28, 0.06, 0.04, 1)
    L.new(c2.outputs[2], c3.inputs[6]); L.new(math_n(N, L, "POWER", pd.outputs["Fac"], 0.6), c3.inputs["Factor"])
    L.new(c3.outputs[2], b.inputs["Base Color"])
    L.new(math_n(N, L, "ADD", 0.28, math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.3)), b.inputs["Roughness"])
    h = math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", vo.outputs["Distance"], 1.0), math_n(N, L, "MULTIPLY", vo2.outputs["Distance"], 0.4))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.inputs["Distance"].default_value = 0.03
    L.new(math_n(N, L, "MINIMUM", h, 0.06), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def hair_material(name, col, rough=0.35, trans=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.5; b.inputs["Subsurface Weight"].default_value = trans
    b.inputs["Subsurface Scale"].default_value = 0.02
    N = m.node_tree.nodes; L = m.node_tree.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.rings_direction = "Z"
    wv.inputs["Scale"].default_value = 18.0; wv.inputs["Distortion"].default_value = 3.0; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def hair(name, root, direction, length, r0, mat, parent=None, bend=Vector((0, 0, 0)), segs=24, depth=0.5):
    """tuk: ildizi 'root' dan 'depth' pastda, 'direction' bo'ylab chiqadi, uchiga qarab ingichkalashadi (kesik uchli)"""
    d = Vector(direction).normalized()
    pts = []
    for i in range(segs + 1):
        t = i / segs; s = -depth + (length + depth) * t
        pts.append(Vector(root) + d * s + bend * max(0.0, s / length) ** 2)
    NP = 14; verts, faces = [], []
    for i, p in enumerate(pts):
        tg = (pts[min(i + 1, segs)] - pts[max(i - 1, 0)]).normalized()
        a = tg.orthogonal().normalized(); b2 = tg.cross(a)
        t = i / segs; r = r0 * (1 - 0.35 * max(0, (t * (length + depth) - depth) / length))
        for j in range(NP):
            ang = 2 * math.pi * j / NP
            verts.append(tuple(p + (a * math.cos(ang) + b2 * math.sin(ang)) * r))
    for i in range(segs):
        for j in range(NP):
            a_ = i * NP + j; b_ = i * NP + (j + 1) % NP
            faces.append((a_, b_, b_ + NP, a_ + NP))
    faces.append(tuple(range(segs * NP, segs * NP + NP)))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    return _link(bpy.data.objects.new(name, me), parent)

def flakes(name, sk, n, mat, parent=None, seed=5, area=None):
    """o'lik hujayra po'stlari: yupqa olti burchakli plastinkalar"""
    rnd = random.Random(seed); out = []
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=1.0, radius2=0.92, depth=0.08); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    for i in range(n):
        a = area or (-sk.size / 2 + 0.3, sk.size / 2 - 0.3, -sk.size / 2 + 0.3, sk.size / 2 - 0.3)
        x = rnd.uniform(a[0], a[1]); y = rnd.uniform(a[2], a[3])
        if sk.depth_fac(x, y) > 0: continue
        o = _link(bpy.data.objects.new(f"{name}{i}", me), parent)
        s = rnd.uniform(0.05, 0.13); o.scale = (s, s * rnd.uniform(0.7, 1.0), s * 0.12)
        o.location = (x, y, sk.H(x, y) + 0.004); o.rotation_euler = (R(rnd.uniform(-12, 12)), R(rnd.uniform(-12, 12)), R(rnd.uniform(0, 60)))
        out.append(o)
    return out

# ======================= TERI KESIMI (tuk illizi) =======================
def cut_material(name="skin_cut"):
    """kesim yuzasi: qatlamlar mahalliy z bo'yicha (0 tepada): shox qatlam, epidermis (hujayralar), derma (tolalar), yog'"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.45
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.04
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    b.inputs["Coat Weight"].default_value = 0.4; b.inputs["Coat Roughness"].default_value = 0.15
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    z = sep.outputs["Z"]
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 22.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    vo.feature = "DISTANCE_TO_EDGE"
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 10; nz.inputs["Distortion"].default_value = 1.5
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 6.0, 1.0); L.new(tc.outputs["Object"], mp.inputs[0])
    L.new(mp.outputs[0], nz.inputs["Vector"])
    fat = N.new("ShaderNodeTexVoronoi"); fat.inputs["Scale"].default_value = 3.5; fat.feature = "DISTANCE_TO_EDGE"; L.new(tc.outputs["Object"], fat.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "EASE"
    stops = [(0.0, (0.95, 0.85, 0.42)), (0.2, (0.98, 0.86, 0.5)), (0.32, (0.85, 0.42, 0.38)), (0.86, (0.78, 0.3, 0.3)), (0.97, (0.98, 0.94, 0.85))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p, c in stops[1:-1]:
        e = cr.elements.new(p); e.color = (*c, 1)
    # z: 0 (tepa) .. -2.6 (past) -> 1..0 ga
    zz = math_n(N, L, "ADD", math_n(N, L, "DIVIDE", z, 2.6), 1.0, clamp=True)
    L.new(zz, ramp.inputs[0])
    base = ramp.outputs[0]
    # qatlam ichidagi naqshlar
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; c1.inputs[7].default_value = (0.55, 0.12, 0.12, 1)
    L.new(base, c1.inputs[6])
    epi = math_n(N, L, "MULTIPLY", math_n(N, L, "GREATER_THAN", z, -0.16), math_n(N, L, "LESS_THAN", z, -0.035))
    cells = math_n(N, L, "MULTIPLY", math_n(N, L, "LESS_THAN", vo.outputs["Distance"], 0.06), epi)
    fib = math_n(N, L, "MULTIPLY", math_n(N, L, "POWER", nz.outputs["Fac"], 3.0), math_n(N, L, "LESS_THAN", z, -0.16))
    L.new(math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", cells, 0.5), math_n(N, L, "MULTIPLY", fib, 0.9), clamp=True), c1.inputs["Factor"])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.inputs[7].default_value = (0.8, 0.6, 0.25, 1)
    L.new(c1.outputs[2], c2.inputs[6])
    L.new(math_n(N, L, "MULTIPLY", math_n(N, L, "LESS_THAN", fat.outputs["Distance"], 0.03), math_n(N, L, "LESS_THAN", z, -2.2)), c2.inputs["Factor"])
    L.new(c2.outputs[2], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.inputs["Distance"].default_value = 0.02
    L.new(math_n(N, L, "ADD", vo.outputs["Distance"], nz.outputs["Fac"]), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def bisect_keep_neg_x(o, fill=True, eps=0.0):
    """mesh'ni x = eps tekisligi bo'ylab kesadi (dunyo emas, mahalliy), +X tomonini olib tashlaydi, kesim yuzini yopadi"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(eps, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    if fill:
        edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bm.to_mesh(o.data); bm.free()

def metaball_mesh(name, balls, res=0.03, parent=None):
    """balls: [(x,y,z,r)] -> bitta yumaloq bo'lakli mesh (yog' bezi, axlat to'dasi)"""
    mb = bpy.data.metaballs.new(name); mb.resolution = res; mb.render_resolution = res
    for x, y, z, r in balls:
        e = mb.elements.new(); e.co = (x, y, z); e.radius = r
    o = bpy.data.objects.new(name, mb); bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.view_layer.objects: x.select_set(False)
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.view_layer.objects.active; o.name = name
    for p in o.data.polygons: p.use_smooth = True
    if parent is not None: o.parent = parent
    return o
