# Makro kadrlar uchun procedural modellar: ko'z (qovoq, kipriklar, qon tomirlari), chuvalchang, barmoq, pashsha.
# Hammasi real o'lchamda (metr). Ko'z mahalliy o'qlari: X = o'ng, Z = tepa, -Y = kameraga (ko'z qaraydigan tomon).
import bpy, math, random
from mathutils import Vector, Matrix

R_ = math.radians

def _link(o, parent=None):
    bpy.context.scene.collection.objects.link(o)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); _link(o, parent); o.location = loc; return o

def _node(N, t, **kw):
    n = N.new(t)
    for k, v in kw.items():
        if k in n.inputs: n.inputs[k].default_value = v
        else: setattr(n, k, v)
    return n

def _math(N, L, op, a, b=None, c=None, clamp=False):
    m = N.new("ShaderNodeMath"); m.operation = op; m.use_clamp = clamp
    for i, x in enumerate((a, b, c)):
        if x is None: continue
        if isinstance(x, (int, float)): m.inputs[i].default_value = x
        else: L.new(x, m.inputs[i])
    return m.outputs[0]

def value_node(mat, name, v):
    """Kadrlarga qarab o'zgaradigan son (masalan qizarish). keyframe uchun qaytaradi: node.outputs[0]"""
    n = mat.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.label = name
    n.outputs[0].default_value = v; return n

def key_value(node, f, v):
    node.outputs[0].default_value = v; node.outputs[0].keyframe_insert("default_value", frame=f)

# ======================= KO'Z OLMASI =======================
def eyeball_material(name, kind):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    red = value_node(m, "REDNESS", 0.0)
    tc = N.new("ShaderNodeTexCoord")
    nv = N.new("ShaderNodeVectorMath"); nv.operation = "NORMALIZE"; L.new(tc.outputs["Object"], nv.inputs[0])
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(nv.outputs[0], sx.inputs[0])
    X, Y, Z = sx.outputs
    # s = sin(old o'qdan burchak) = sqrt(x^2+z^2); old yarim sfera: y<0
    s = _math(N, L, "SQRT", _math(N, L, "ADD", _math(N, L, "MULTIPLY", X, X), _math(N, L, "MULTIPLY", Z, Z)))
    front = _math(N, L, "LESS_THAN", Y, 0.0)
    if kind == "cow":
        q = _math(N, L, "SQRT", _math(N, L, "ADD", _math(N, L, "MULTIPLY", _math(N, L, "MULTIPLY", X, X), 0.35),
                                      _math(N, L, "MULTIPLY", _math(N, L, "MULTIPLY", Z, Z), 3.2)))
        IRIS, PUP = 0.80, 0.30
    else:
        q = s; IRIS, PUP = 0.50, 0.17
    # irisdagi radial tolalar: (burchak*12, s*3)
    ang = _math(N, L, "ARCTAN2", Z, X)
    cv = N.new("ShaderNodeCombineXYZ"); L.new(_math(N, L, "MULTIPLY", ang, 9.0), cv.inputs[0]); L.new(_math(N, L, "MULTIPLY", s, 2.2), cv.inputs[1])
    nz = _node(N, "ShaderNodeTexNoise", **{"Scale": 3.5, "Detail": 10.0, "Roughness": 0.65}); L.new(cv.outputs[0], nz.inputs["Vector"])
    ir = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], ir.inputs[0])
    E = ir.color_ramp.elements
    if kind == "cow":
        E[0].position, E[0].color = 0.3, (0.03, 0.018, 0.01, 1); E[1].position, E[1].color = 0.75, (0.22, 0.12, 0.05, 1)
    else:
        E[0].position, E[0].color = 0.3, (0.10, 0.20, 0.24, 1); E[1].position, E[1].color = 0.72, (0.42, 0.62, 0.62, 1)
        e2 = E.new(0.9); e2.color = (0.65, 0.78, 0.72, 1)
    # qorachiq atrofidagi qo'ng'ir halqa va chekkadagi to'q halqa (limbus)
    coll = _math(N, L, "SUBTRACT", 1.0, _math(N, L, "SMOOTH_MAX", _math(N, L, "MULTIPLY", _math(N, L, "SUBTRACT", s, PUP * 1.1), 9.0), 0.0, 0.1), clamp=True)
    mixc = N.new("ShaderNodeMix"); mixc.data_type = "RGBA"; L.new(coll, mixc.inputs["Factor"])
    L.new(ir.outputs[0], mixc.inputs[6]); mixc.inputs[7].default_value = (0.35, 0.2, 0.07, 1) if kind != "cow" else (0.05, 0.03, 0.02, 1)
    limb = N.new("ShaderNodeMapRange"); L.new(q, limb.inputs[0]); limb.inputs[1].default_value = IRIS - 0.12; limb.inputs[2].default_value = IRIS
    mixl = N.new("ShaderNodeMix"); mixl.data_type = "RGBA"; L.new(limb.outputs[0], mixl.inputs["Factor"])
    L.new(mixc.outputs[2], mixl.inputs[6]); mixl.inputs[7].default_value = (0.03, 0.04, 0.05, 1)
    # sklera: oq-pushti, qon tomirlari (voronoi chegaralari)
    # tomirlar: shovqin 0.5 sathining chiziqlari (|n-0.5| kichik joylar)
    def vline(scale, width, dist):
        nn = _node(N, "ShaderNodeTexNoise", **{"Scale": scale, "Detail": 3.0, "Distortion": dist, "Roughness": 0.55})
        L.new(tc.outputs["Object"], nn.inputs["Vector"])
        d = _math(N, L, "ABSOLUTE", _math(N, L, "SUBTRACT", nn.outputs["Fac"], 0.5))
        return _math(N, L, "SUBTRACT", 1.0, _math(N, L, "DIVIDE", d, width), clamp=True)
    v1 = vline(140.0, 0.03, 0.6); v2 = vline(420.0, 0.02, 0.9)
    veins = _math(N, L, "MAXIMUM", v1, _math(N, L, "MULTIPLY", v2, 0.6))
    edge = _math(N, L, "MULTIPLY", _math(N, L, "SUBTRACT", s, IRIS + 0.03), 3.0, clamp=True)
    base_v = 0.3 if kind != "cow" else 0.1
    vamt = _math(N, L, "MULTIPLY", _math(N, L, "MULTIPLY", veins, _math(N, L, "ADD", 0.25, edge)), _math(N, L, "ADD", base_v, _math(N, L, "MULTIPLY", red.outputs[0], 1.6)), clamp=True)
    scl = N.new("ShaderNodeMix"); scl.data_type = "RGBA"
    L.new(_math(N, L, "MULTIPLY", _math(N, L, "MULTIPLY", _math(N, L, "ADD", 0.35, edge), red.outputs[0]), 0.55), scl.inputs["Factor"])
    scl.inputs[6].default_value = (0.8, 0.74, 0.68, 1) if kind != "cow" else (0.75, 0.68, 0.62, 1)
    scl.inputs[7].default_value = (0.85, 0.3, 0.27, 1)
    sv = N.new("ShaderNodeMix"); sv.data_type = "RGBA"; L.new(vamt, sv.inputs["Factor"])
    L.new(scl.outputs[2], sv.inputs[6]); sv.inputs[7].default_value = (0.55, 0.03, 0.03, 1)
    # tanlash: sklera / iris / qorachiq
    isiris = _math(N, L, "MULTIPLY", _math(N, L, "LESS_THAN", q, IRIS), front)
    ispup = _math(N, L, "MULTIPLY", _math(N, L, "LESS_THAN", q, PUP), front)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(isiris, c1.inputs["Factor"]); L.new(sv.outputs[2], c1.inputs[6]); L.new(mixl.outputs[2], c1.inputs[7])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(ispup, c2.inputs["Factor"]); L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.004, 0.004, 0.005, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.25
    b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.0; b.inputs["Coat IOR"].default_value = 1.376
    b.inputs["Subsurface Weight"].default_value = 0.08; b.inputs["Subsurface Scale"].default_value = 0.0004
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; bp.inputs["Distance"].default_value = 0.0002
    L.new(_math(N, L, "MULTIPLY", nz.outputs["Fac"], isiris), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m, red

def build_eyeball(name, R, kind, parent):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=R, rotation=(R_(90), 0, 0))
    o = bpy.context.object; o.name = name
    bpy.ops.object.transform_apply(rotation=True)
    for p in o.data.polygons: p.use_smooth = True
    IR = 0.5 if kind != "cow" else 0.8
    for v in o.data.vertices:                       # shox parda (cornea) bo'rtig'i
        d = v.co.normalized(); s = math.hypot(d.x, d.z)
        if d.y < 0 and s < IR:
            v.co = d * (R + 0.06 * R * math.cos(s / IR * math.pi / 2) ** 2)
    m, red = eyeball_material(name + "_mat", kind); o.data.materials.append(m)
    o.parent = parent
    return o, red

# ======================= QOVOQLAR + KIPRIKLAR =======================
NPHI, NT = 120, 30
def _smin(a, b, k):
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25

class LidShape:
    def __init__(self, R, kind):
        self.R = R; self.kind = kind
        s = R / 0.012
        self.W = 0.0118 * s; self.Hu = 0.0052 * s; self.Hl = 0.0043 * s
        self.out = (0.05 * s, 0.058 * s)
        self.Rl = R + 0.0009 * s
        random.seed(11 if kind != "cow" else 12)
        nU, nL = (58, 30) if kind != "cow" else (60, 28)
        self.lashes = []
        for i in range(nU):
            u = -0.88 + 1.76 * (i + random.random() * 0.6) / nU
            self.lashes.append((1, u, random.uniform(0.75, 1.0), random.uniform(-0.25, 0.25), random.uniform(-.0004, .0004)))
        for i in range(nL):
            u = -0.8 + 1.6 * (i + random.random() * 0.6) / nL
            self.lashes.append((-1, u, random.uniform(0.6, 1.0), random.uniform(-0.25, 0.25), random.uniform(-.0003, .0003)))

    def depth(self, x, z):
        d2 = x * x + z * z
        ys = -math.sqrt(max(self.Rl ** 2 - d2, 0.0))
        f = -0.0082 * self.R / 0.012
        if z > 0.012 * self.R / 0.012: f -= 0.18 * (z - 0.012 * self.R / 0.012)        # qosh suyagi
        return _smin(ys, f, 0.0025 * self.R / 0.012)

    def margin(self, x, upper, ou, ol):
        W = self.W; f = max(0.0, 1 - (x / W) ** 2)
        if upper:
            op = self.Hu * f ** 0.8 + 0.0005 * (x / W) * f      # tashqi burchak biroz yuqoriroq
            cl = -0.32 * self.Hl * f ** 0.9
            return cl + (op - cl) * ou
        return -self.Hl * ol * f ** (0.9 if ol <= 1 else 0.75)

    def verts(self, ou, ol):
        W = self.W; V = []
        for j in range(NT):
            t = (j / (NT - 1)) ** 1.8
            for i in range(NPHI):
                ph = 2 * math.pi * i / NPHI
                x0 = W * math.cos(ph); up = math.sin(ph) >= 0 if i not in (0, NPHI // 2) else True
                z0 = self.margin(x0, math.sin(ph) > 1e-9 or i == 0, ou, ol) if i != NPHI // 2 else 0.0
                if i == 0 or i == NPHI // 2: z0 = 0.0
                x1 = self.out[0] * math.cos(ph); z1 = self.out[1] * math.sin(ph)
                x = x0 + (x1 - x0) * t; z = z0 + (z1 - z0) * t
                y = self.depth(x, z)
                if math.sin(ph) > 0:          # yuqori qovoq burmasi va uning ustidagi do'mboqlik
                    fx = max(0.0, 1 - (x0 / W) ** 2)
                    y += fx * (0.0009 * math.exp(-((t - 0.17) / 0.035) ** 2) - 0.0005 * math.exp(-((t - 0.3) / 0.08) ** 2)) * self.R / 0.012
                V.append(Vector((x, y, z)))
        # kipriklar: har biri 4 qirrali, 6 bo'g'inli naycha
        for side, u, ln, sp, dz in self.lashes:
            x = u * W
            z = self.margin(x, side > 0, ou, ol) + side * 0.00025
            root = Vector((x, self.depth(x, z) - 0.0002, z))
            L = (0.0105 if side > 0 else 0.0055) * ln * self.R / 0.012 * (1.5 if self.kind == "cow" else 1.0)
            if side > 0:
                k = max(0.0, min(1.0, ou))            # yumilganda kiprik pastga qaraydi
                d = Vector((u * 0.35 + sp * 0.3, -0.75, 0.66 * (2 * k - 1))).normalized()
                curl = Vector((0, 0.15, 1.0 if k > 0.5 else -0.4))
            else:
                d = Vector((u * 0.3 + sp * 0.3, -0.7, -0.72)).normalized(); curl = Vector((0, 0.1, -0.6))
            side_v = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
            up_v = side_v.cross(d).normalized()
            for r in range(6):
                s = r / 5; c = root + d * L * s + curl * L * 0.35 * s * s
                rad = 0.00006 * (1 - s * 0.85) * (1.6 if self.kind == "cow" else 1.0)
                for a in range(4):
                    an = a * math.pi / 2
                    V.append(c + (side_v * math.cos(an) + up_v * math.sin(an)) * rad)
        return V

    def faces(self):
        F = []; M = []
        for j in range(NT - 1):
            for i in range(NPHI):
                a = j * NPHI + i; b = j * NPHI + (i + 1) % NPHI
                F.append((a, b, b + NPHI, a + NPHI)); M.append(0)
        base = NT * NPHI
        for k in range(len(self.lashes)):
            o = base + k * 24
            for r in range(5):
                for a in range(4):
                    p = o + r * 4 + a; q = o + r * 4 + (a + 1) % 4
                    F.append((p, q, q + 4, p + 4)); M.append(1)
        return F, M

def skin_material(name, kind, base=(0.56, 0.33, 0.25)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "lidt"
    tc = N.new("ShaderNodeTexCoord")
    nz = _node(N, "ShaderNodeTexNoise", **{"Scale": 220.0, "Detail": 6.0}); L.new(tc.outputs["Object"], nz.inputs["Vector"])
    rim = _math(N, L, "POWER", _math(N, L, "SUBTRACT", 1.0, _math(N, L, "MULTIPLY", at.outputs["Fac"], 9.0), clamp=True), 1.5)   # qovoq cheti (ho'l, pushti)
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"; L.new(_math(N, L, "MULTIPLY", nz.outputs["Fac"], 0.5), col.inputs["Factor"])
    if kind == "cow":
        col.inputs[6].default_value = (0.06, 0.035, 0.022, 1); col.inputs[7].default_value = (0.16, 0.09, 0.05, 1)
    else:
        col.inputs[6].default_value = (*base, 1); col.inputs[7].default_value = (base[0] * 0.85, base[1] * 0.75, base[2] * 0.7, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(rim, c2.inputs["Factor"]); L.new(col.outputs[2], c2.inputs[6])
    c2.inputs[7].default_value = (0.62, 0.2, 0.18, 1) if kind != "cow" else (0.25, 0.08, 0.06, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"])
    L.new(_math(N, L, "SUBTRACT", 0.5 if kind != "cow" else 0.7, _math(N, L, "MULTIPLY", rim, 0.45)), b.inputs["Roughness"])
    b.inputs["Subsurface Weight"].default_value = 0.35 if kind != "cow" else 0.05
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.002
    # teri g'ovaklari va ajinlar (bump)
    pores = _node(N, "ShaderNodeTexVoronoi"); pores.inputs["Scale"].default_value = 4000.0 if kind != "cow" else 300.0
    L.new(tc.outputs["Object"], pores.inputs["Vector"])
    if kind == "cow":     # qisqa jun: bir yo'nalishda cho'zilgan shovqin
        mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2500, 2500, 250); L.new(tc.outputs["Object"], mp.inputs[0])
        fur = _node(N, "ShaderNodeTexNoise", **{"Scale": 1.0, "Detail": 2.0}); L.new(mp.outputs[0], fur.inputs["Vector"])
        h = fur.outputs["Fac"]
    else:
        wv = _node(N, "ShaderNodeTexWave", **{"Scale": 260.0, "Distortion": 9.0, "Detail": 4.0}); L.new(tc.outputs["Object"], wv.inputs["Vector"])
        h = _math(N, L, "ADD", pores.outputs["Distance"], _math(N, L, "MULTIPLY", wv.outputs["Fac"], 0.25))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12 if kind != "cow" else 0.5; bp.inputs["Distance"].default_value = 0.0001
    L.new(h, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    # rentgen rejimi (shaffof ko'k), XRAY qiymati bilan boshqariladi
    xr = value_node(m, "XRAY", 0.0)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.65, 1.0, 1); em.inputs["Strength"].default_value = 3.0
    tr = N.new("ShaderNodeBsdfTransparent")
    xm = N.new("ShaderNodeMixShader"); L.new(lw.outputs["Facing"], xm.inputs[0]); L.new(tr.outputs[0], xm.inputs[1]); L.new(em.outputs[0], xm.inputs[2])
    mx = N.new("ShaderNodeMixShader"); L.new(xr.outputs[0], mx.inputs[0]); L.new(b.outputs[0], mx.inputs[1]); L.new(xm.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m, xr

def lash_material(kind):
    m = bpy.data.materials.new("lash_" + kind); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.02, 0.014, 0.01, 1) if kind != "cow" else (0.12, 0.08, 0.05, 1)
    b.inputs["Roughness"].default_value = 0.35
    return m

def build_lids(name, R, kind, parent, states):
    """states: {"blink": (ou, ol), ...} -> shape key'lar. Basis = ochiq (1, 1).
    Ikki ob'ekt: teri (qalinlik bilan) va kipriklar; ikkalasida ham bir xil shape key'lar."""
    ls = LidShape(R, kind)
    F, M = ls.faces(); nskin = NT * NPHI
    Fs = [f for f, mi in zip(F, M) if mi == 0]
    Fl = [tuple(i - nskin for i in f) for f, mi in zip(F, M) if mi == 1]
    allv = {"__basis": ls.verts(1.0, 1.0)}
    for k, (ou, ol) in states.items(): allv[k] = ls.verts(ou, ol)
    objs = []
    for part, faces, sl in (("skin", Fs, slice(0, nskin)), ("lash", Fl, slice(nskin, None))):
        me = bpy.data.meshes.new(f"{name}_{part}")
        me.from_pydata([tuple(v) for v in allv["__basis"][sl]], [], faces)
        for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(f"{name}_{part}", me); _link(o, parent)
        o.shape_key_add(name="Basis")
        for k in states:
            kb = o.shape_key_add(name=k, from_mix=False); kb.value = 0.0      # Blender 5: sukut bo'yicha 1.0
            for i, v in enumerate(allv[k][sl]): kb.data[i].co = v
        objs.append(o)
    skin, lash = objs
    at = skin.data.attributes.new("lidt", "FLOAT", "POINT")
    for j in range(NT):
        for i in range(NPHI): at.data[j * NPHI + i].value = (j / (NT - 1)) ** 1.8
    sm, xr = skin_material(name + "_skin", kind); skin.data.materials.append(sm)
    lash.data.materials.append(lash_material(kind))
    so = skin.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.0016 * R / 0.012; so.offset = 1.0; so.use_even_offset = True
    sd = skin.modifiers.new("sub", "SUBSURF"); sd.levels = 1; sd.render_levels = 2
    class Keys(dict):
        pass
    keys = Keys()
    for k in states:
        keys[k] = [skin.data.shape_keys.key_blocks[k], lash.data.shape_keys.key_blocks[k]]
    return skin, lash, keys, xr, ls

def set_key(eye, k, f, v):
    for kb in eye["keys"][k]:
        kb.value = v; kb.keyframe_insert("value", frame=f)

def build_eye(name, loc, kind="human", R=0.012):
    root = empty(name, loc)
    ball, red = build_eyeball(name + "_ball", R, kind, root)
    lids, lash, keys, xr, ls = build_lids(name + "_lids", R, kind, root,
                                    {"blink": (0.0, 1.0), "pull": (1.15, 1.9), "wide": (1.3, 1.05), "squint": (0.55, 0.85)})
    # ichki burchak (karunkula)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0014 * R / 0.012, location=(-ls.W + 0.0011 * R / 0.012, -R * 0.55, 0))
    car = bpy.context.object; car.name = name + "_caruncle"; car.scale = (0.8, 1.3, 1.0); car.parent = root
    for p in car.data.polygons: p.use_smooth = True
    cm = bpy.data.materials.new(name + "_car"); cm.use_nodes = True; cb = cm.node_tree.nodes["Principled BSDF"]
    cb.inputs["Base Color"].default_value = (0.75, 0.3, 0.3, 1); cb.inputs["Roughness"].default_value = 0.1
    cb.inputs["Subsurface Weight"].default_value = 0.5; cb.inputs["Subsurface Scale"].default_value = 0.0008; car.data.materials.append(cm)
    car.location.y = ls.depth(car.location.x, 0) + 0.0012
    return dict(root=root, ball=ball, red=red, lids=lids, lash=lash, keys=keys, xray=xr, shape=ls, R=R)

def on_eye(eye, x, z, lift=0.00028):
    """ko'z olmasi sirtidagi nuqta (mahalliy koordinatada)"""
    R = eye["R"]; d2 = min(x * x + z * z, (R * 0.995) ** 2)
    s = math.sqrt(d2) / R; IR = 0.5
    rr = R + (0.06 * R * math.cos(s / IR * math.pi / 2) ** 2 if s < IR else 0)
    return Vector((x, -math.sqrt(max(rr * rr - d2, 0)) - lift, z))

# ======================= CHUVALCHANG =======================
_worm_mat = None
def worm_material():
    global _worm_mat
    if _worm_mat: return _worm_mat
    m = bpy.data.materials.new("worm"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.92, 0.9, 0.84, 1); b.inputs["Roughness"].default_value = 0.18
    b.inputs["Subsurface Weight"].default_value = 0.8; b.inputs["Subsurface Radius"].default_value = (1, 0.9, 0.7)
    b.inputs["Subsurface Scale"].default_value = 0.0006
    b.inputs["Coat Weight"].default_value = 0.6
    tc = N.new("ShaderNodeTexCoord"); wv = _node(N, "ShaderNodeTexWave", **{"Scale": 1.0, "Distortion": 0.5})
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (9000, 9000, 9000)
    L.new(tc.outputs["Object"], mp.inputs[0]); L.new(mp.outputs[0], wv.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.inputs["Distance"].default_value = 0.00003
    L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    _worm_mat = m; return m

def make_worm(name, parent, n=22, radius=0.00034):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = radius; cu.bevel_resolution = 3; cu.use_fill_caps = True; cu.resolution_u = 4
    sp = cu.splines.new("NURBS"); sp.points.add(n - 1); sp.order_u = 4; sp.use_endpoint_u = True
    for i, p in enumerate(sp.points):
        u = i / (n - 1); p.radius = 0.35 + 0.65 * math.sin(math.pi * min(1, u * 1.15)) ** 0.5
        p.co = (u * 0.01, 0, 0, 1)
    o = bpy.data.objects.new(name, cu); _link(o, parent); cu.materials.append(worm_material())
    return o

def set_worm(o, f, pts):
    sp = o.data.splines[0]
    for p, q in zip(sp.points, pts):
        p.co = (q[0], q[1], q[2], 1); p.keyframe_insert("co", frame=f)

def wiggle_path(n, length, f, head, heading, amp=0.0012, k=2.5, w=0.55, phase=0.0):
    """2D (x,z) nuqtalar: bosh 'head' da, tanasi 'heading' ga teskari yo'nalishda, ilonsimon to'lqin"""
    hx, hz = math.cos(heading), math.sin(heading); nx, nz = -hz, hx
    pts = []
    for i in range(n):
        s = i / (n - 1)
        a = amp * math.sin(k * 2 * math.pi * s - w * f + phase) * (0.3 + 0.7 * s)
        pts.append((head[0] - hx * length * s + nx * a, head[1] - hz * length * s + nz * a))
    return pts

# ======================= BARMOQ =======================
def build_finger(name, parent=None, r=0.0078, length=0.07):
    """uchi (0,0,0) da, tanasi +Y bo'ylab; tirnoq +Z tomonda"""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=r, location=(0, 0, 0))
    tip = bpy.context.object
    for v in tip.data.vertices:
        if v.co.y > 0: v.co.y = 0
        v.co.y += r
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=length, location=(0, r + length / 2, 0), rotation=(R_(90), 0, 0))
    cyl = bpy.context.object
    bpy.ops.object.select_all(action="DESELECT"); tip.select_set(True); cyl.select_set(True)
    bpy.context.view_layer.objects.active = tip; bpy.ops.object.join(); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o = tip; o.name = name
    for v in o.data.vertices:
        v.co.z *= 0.82
        if v.co.z < 0: v.co.z *= 1.0 + 0.25 * math.exp(-((v.co.y - 0.012) / 0.01) ** 2)   # barmoq yostiqchasi
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.remove_doubles(threshold=0.0002); bpy.ops.object.mode_set(mode="OBJECT")
    for p in o.data.polygons: p.use_smooth = True
    o.modifiers.new("sub", "SUBSURF").levels = 1
    m, _ = skin_material(name + "_skin", "human", base=(0.78, 0.52, 0.42))
    N = m.node_tree.nodes; L = m.node_tree.links; b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = next(n for n in N if n.type == "TEX_COORD")
    wv = _node(N, "ShaderNodeTexWave", **{"Scale": 450.0, "Distortion": 3.0, "Detail": 2.0}); wv.wave_type = "RINGS"   # barmoq izi
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = 0.25; bp2.inputs["Distance"].default_value = 0.00008
    L.new(wv.outputs["Fac"], bp2.inputs["Height"]); L.new(b.inputs["Normal"].links[0].from_socket, bp2.inputs["Normal"])
    L.new(bp2.outputs[0], b.inputs["Normal"])
    o.data.materials.append(m)
    # tirnoq
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(0, 0.011, r * 0.68))
    nail = bpy.context.object; nail.name = name + "_nail"; nail.scale = (r * 0.78, 0.011, r * 0.2)
    nm = bpy.data.materials.new("nail"); nm.use_nodes = True; nb = nm.node_tree.nodes["Principled BSDF"]
    nb.inputs["Base Color"].default_value = (0.85, 0.62, 0.58, 1); nb.inputs["Roughness"].default_value = 0.15; nb.inputs["Coat Weight"].default_value = 0.8
    nail.data.materials.append(nm); nail.parent = o
    for p in nail.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

# ======================= PASHSHA =======================
def build_fly(name, scale=1.0):
    """markaz (0,0,0), bosh +Y tomonda, oyoqlar -Z da. Qanotlar: root['wings'] (keyframe uchun)"""
    root = empty(name)
    def ell(n, size, loc, m, parent=root):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=loc)
        o = bpy.context.object; o.name = n; o.scale = size; o.parent = parent; o.data.materials.append(m)
        for p in o.data.polygons: p.use_smooth = True
        return o
    def pm(n, col, rough=0.35, coat=0.6):
        m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Coat Weight"].default_value = coat
        return m
    body = pm("fly_body", (0.02, 0.02, 0.018), 0.45, 0.3)
    N = body.node_tree.nodes; L = body.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    wv = _node(N, "ShaderNodeTexWave", **{"Scale": 900.0, "Distortion": 2.0}); wv.bands_direction = "X"; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.01, 0.01, 0.01, 1); cr.color_ramp.elements[1].color = (0.16, 0.15, 0.13, 1)
    L.new(cr.outputs[0], N["Principled BSDF"].inputs["Base Color"])
    hairs = _node(N, "ShaderNodeTexNoise", **{"Scale": 6000.0}); bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6
    bp.inputs["Distance"].default_value = 0.00005; L.new(hairs.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], N["Principled BSDF"].inputs["Normal"])
    ell("thorax", (0.0021, 0.0026, 0.002), (0, 0, 0), body)
    ab = pm("fly_abd", (0.05, 0.045, 0.03), 0.3, 0.8)
    ell("abdomen", (0.002, 0.0031, 0.0016), (0, -0.0038, -0.0003), ab)
    head = ell("head", (0.0017, 0.0012, 0.0015), (0, 0.0031, 0.0001), body)
    em = pm("fly_eye", (0.16, 0.02, 0.012), 0.3, 0.6)
    Ne = em.node_tree.nodes; Le = em.node_tree.links; vo = _node(Ne, "ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 9000.0
    bpe = Ne.new("ShaderNodeBump"); bpe.inputs["Strength"].default_value = 0.5; bpe.inputs["Distance"].default_value = 0.00002
    Le.new(vo.outputs["Distance"], bpe.inputs["Height"]); Le.new(bpe.outputs[0], Ne["Principled BSDF"].inputs["Normal"])
    for sx in (-1, 1):
        ell("eye", (0.0011, 0.0009, 0.0012), (sx * 0.0011, 0.0034, 0.0004), em)
    # xartumcha
    bpy.ops.mesh.primitive_cylinder_add(radius=0.00022, depth=0.0014, location=(0, 0.0036, -0.0012), rotation=(R_(20), 0, 0))
    pr = bpy.context.object; pr.name = "proboscis"; pr.parent = root; pr.data.materials.append(body)
    # qanotlar
    wm = bpy.data.materials.new("fly_wing"); wm.use_nodes = True; Nw = wm.node_tree.nodes; Lw = wm.node_tree.links; bw = Nw["Principled BSDF"]
    bw.inputs["Base Color"].default_value = (0.8, 0.82, 0.85, 1); bw.inputs["Roughness"].default_value = 0.05
    bw.inputs["Alpha"].default_value = 0.25; bw.inputs["Thin Film Thickness"].default_value = 450; bw.inputs["Thin Film IOR"].default_value = 1.5
    vw = _node(Nw, "ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE"); vw.inputs["Scale"].default_value = 900.0
    tw = Nw.new("ShaderNodeTexCoord"); Lw.new(tw.outputs["Object"], vw.inputs["Vector"])
    vein = _math(Nw, Lw, "SUBTRACT", 1.0, _math(Nw, Lw, "MULTIPLY", vw.outputs["Distance"], 25.0), clamp=True)
    Lw.new(_math(Nw, Lw, "ADD", 0.18, _math(Nw, Lw, "MULTIPLY", vein, 0.7), clamp=True), bw.inputs["Alpha"])
    wings = []
    for sx in (-1, 1):
        piv = empty(f"wingpiv{sx}", (sx * 0.0008, -0.0002, 0.0017), root)
        bpy.ops.mesh.primitive_circle_add(vertices=24, radius=1, fill_type="NGON", location=(0, 0, 0))
        w = bpy.context.object; w.name = f"wing{sx}"
        for v in w.data.vertices:
            v.co.x = (v.co.x * 0.0031 + 0.0031) * sx; v.co.y = v.co.y * 0.0013
        w.parent = piv; w.data.materials.append(wm)
        piv.rotation_mode = "XYZ"
        wings.append((piv, sx))
    # oyoqlar
    lm = pm("fly_leg", (0.02, 0.02, 0.02), 0.4, 0.2)
    for k, yy in enumerate((0.0012, 0.0, -0.0012)):
        for sx in (-1, 1):
            cu = bpy.data.curves.new("leg", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.00011
            sp = cu.splines.new("POLY"); sp.points.add(3)
            P = [(sx * 0.0012, yy, -0.0012), (sx * 0.0032, yy + 0.0006 * (1 - k), -0.0004), (sx * 0.0044, yy + 0.0012 * (1 - k), -0.0024), (sx * 0.0048, yy + 0.0016 * (1 - k), -0.0034)]
            for p, q in zip(sp.points, P): p.co = (*q, 1)
            lo = bpy.data.objects.new("leg", cu); _link(lo, root); cu.materials.append(lm)
    root.scale = (scale,) * 3
    root["wings"] = [p.name for p, _ in wings]
    return root, wings

def wings_rest(wings, f):
    for piv, sx in wings:
        piv.rotation_euler = (0, R_(sx * -8), R_(sx * -68)); piv.keyframe_insert("rotation_euler", frame=f)

def wings_flap(wings, f0, f1):
    for f in range(f0, f1 + 1):
        for piv, sx in wings:
            up = (f % 2 == 0)
            piv.rotation_euler = (0, R_(sx * (-60 if up else 45)), R_(sx * (-15 if up else -30))); piv.keyframe_insert("rotation_euler", frame=f)
