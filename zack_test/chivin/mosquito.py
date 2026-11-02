# Chivin (Aedes) va makro teri uchun procedural modellar. Hammasi real o'lchamda (metr).
# Chivin mahalliy o'qlari: +Y = bosh tomoni, +Z = tepa. Tumshuq (proboscis) pastga-oldinga qaragan.
# Tumshuq tuzilishi: tashqi qobiq (labium) + ichida 6 ta stilet to'plami (fascicle).
# Chaqqanda: stiletlar teriga kiradi, labium teriga kira olmaydi va kamon kabi orqaga bukiladi.
import bpy, math, random
from mathutils import Vector, Matrix
import eye as E

R_ = math.radians
_node, _math, empty, value_node, key_value = E._node, E._math, E.empty, E.value_node, E.key_value

# tumshuq geometriyasi (scale=1 da)
H0 = Vector((0.0, 0.00158, -0.00036))            # bosh ostidagi tumshuq asosi
D0 = Vector((0.0, 0.42, -0.91)).normalized()     # tumshuq yo'nalishi
LP = 0.0024                                      # labium uzunligi
TIP0 = H0 + D0 * LP                              # tinch holatdagi uchi (teriga tegadigan nuqta)


def pmat(name, col, rough=0.35, coat=0.5, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    for k, v in kw.items(): b.inputs[k].default_value = v
    return m


def _ell(name, size, loc, m, parent, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1, location=loc, rotation=[R_(a) for a in rot])
    o = bpy.context.object; o.name = name; o.scale = size; o.parent = parent; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def _scaly(m, scale=30000.0, strength=0.35):
    """mayda tangachalar (bump)"""
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); vo = _node(N, "ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = 0.000004
    L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return tc


def _curve(name, parent, bevel, mats, kind="POLY"):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = bevel
    cu.bevel_resolution = 3; cu.use_fill_caps = True; cu.resolution_u = 6
    for m in mats: cu.materials.append(m)
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o); o.parent = parent
    return o


def _abdomen_material(name):
    """qora-oq halqali qorin; FILL (0..1) -> qonga to'lib, qizil va shaffof bo'ladi"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.42; b.inputs["Coat Weight"].default_value = 0.25
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    # halqalar: y bo'ylab (mahalliy -1..1), har segment boshida oq tasma
    band = _math(N, L, "FRACT", _math(N, L, "MULTIPLY", _math(N, L, "ADD", sep.outputs["Y"], 1.0), 3.6))
    white = _math(N, L, "LESS_THAN", band, 0.13)
    side = _math(N, L, "GREATER_THAN", _math(N, L, "ABSOLUTE", sep.outputs["X"]), 0.55)      # yon tomondagi oq dog'lar
    w = _math(N, L, "MAXIMUM", white, _math(N, L, "MULTIPLY", side, _math(N, L, "LESS_THAN", band, 0.45)))
    fill = value_node(m, "FILL", 0.0)
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; L.new(w, c1.inputs["Factor"])
    c1.inputs[6].default_value = (0.02, 0.017, 0.014, 1); c1.inputs[7].default_value = (0.6, 0.6, 0.57, 1)
    # to'lganda halqalar orasidagi parda cho'ziladi va qizil qon ko'rinadi
    redf = _math(N, L, "MULTIPLY", fill.outputs[0], _math(N, L, "SUBTRACT", 1.0, _math(N, L, "MULTIPLY", w, 0.35)))
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; L.new(redf, c2.inputs["Factor"])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.55, 0.012, 0.01, 1)
    L.new(c2.outputs[2], b.inputs["Base Color"])
    L.new(_math(N, L, "MULTIPLY", fill.outputs[0], 0.9), b.inputs["Subsurface Weight"])
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.15, 0.1); b.inputs["Subsurface Scale"].default_value = 0.0006
    L.new(_math(N, L, "MULTIPLY", fill.outputs[0], 0.25), b.inputs["Transmission Weight"])
    _scaly(m, 26000, 0.25)
    return m, fill


def _wing_material(name):
    wm = bpy.data.materials.new(name); wm.use_nodes = True; Nw = wm.node_tree.nodes; Lw = wm.node_tree.links; bw = Nw["Principled BSDF"]
    bw.inputs["Base Color"].default_value = (0.75, 0.77, 0.8, 1); bw.inputs["Roughness"].default_value = 0.08
    bw.inputs["Thin Film Thickness"].default_value = 520; bw.inputs["Thin Film IOR"].default_value = 1.45
    tw = Nw.new("ShaderNodeTexCoord"); sep = Nw.new("ShaderNodeSeparateXYZ"); Lw.new(tw.outputs["Object"], sep.inputs[0])
    # bo'ylama tomirlar (chivin qanotida parallel tomirlar) + chetidagi tangachalar
    vein = _math(Nw, Lw, "LESS_THAN", _math(Nw, Lw, "PINGPONG", _math(Nw, Lw, "MULTIPLY", sep.outputs["X"], 4.5), 0.5), 0.06)
    edge = _math(Nw, Lw, "GREATER_THAN", _math(Nw, Lw, "ABSOLUTE", sep.outputs["X"]), 0.82)
    a = _math(Nw, Lw, "ADD", 0.12, _math(Nw, Lw, "MULTIPLY", _math(Nw, Lw, "MAXIMUM", vein, edge), 0.75), clamp=True)
    Lw.new(a, bw.inputs["Alpha"])
    return wm


def build_mosquito(name, scale=1.0):
    root = empty(name)
    chit = pmat(name + "_chitin", (0.022, 0.018, 0.014), 0.5, 0.12); _scaly(chit, 30000, 0.3)
    white = pmat(name + "_white", (0.82, 0.82, 0.8), 0.35, 0.3)
    # ko'krak: qora, ustida oq "lira" naqshi (Aedes belgisi)
    thx = pmat(name + "_thorax", (0.022, 0.018, 0.014), 0.5, 0.12)
    N = thx.node_tree.nodes; L = thx.node_tree.links; tc = _scaly(thx, 30000, 0.3)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    stripe = _math(N, L, "LESS_THAN", _math(N, L, "ABSOLUTE", sep.outputs["X"]), 0.09)
    lyre = _math(N, L, "LESS_THAN", _math(N, L, "ABSOLUTE", _math(N, L, "SUBTRACT", _math(N, L, "ABSOLUTE", sep.outputs["X"]),
                                                                    _math(N, L, "ADD", 0.45, _math(N, L, "MULTIPLY", sep.outputs["Y"], 0.25)))), 0.07)
    top = _math(N, L, "GREATER_THAN", sep.outputs["Z"], 0.25)
    wmask = _math(N, L, "MULTIPLY", _math(N, L, "MAXIMUM", stripe, lyre), top)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(wmask, cm.inputs["Factor"])
    cm.inputs[6].default_value = (0.022, 0.018, 0.014, 1); cm.inputs[7].default_value = (0.8, 0.8, 0.78, 1)
    L.new(cm.outputs[2], N["Principled BSDF"].inputs["Base Color"])

    _ell(name + "_thorax", (0.00062, 0.00105, 0.00078), (0, 0.0, 0.0001), thx, root, rot=(-12, 0, 0))
    abm, fill = _abdomen_material(name + "_abd")
    abd_piv = empty(name + "_abd_piv", (0, -0.0007, -0.0001), root); abd_piv.rotation_euler = (R_(6), 0, 0)
    abd = _ell(name + "_abdomen", (0.00048, 0.0023, 0.00042), (0, -0.0023, 0.0), abm, abd_piv)
    _ell(name + "_head", (0.00042, 0.00038, 0.0004), (0, 0.00125, -0.00012), chit, root)
    em = pmat(name + "_eye", (0.03, 0.02, 0.025), 0.25, 0.8, **{"Thin Film Thickness": 380.0})
    Ne = em.node_tree.nodes; Le = em.node_tree.links; vo = _node(Ne, "ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 60000.0
    bpe = Ne.new("ShaderNodeBump"); bpe.inputs["Strength"].default_value = 0.6; bpe.inputs["Distance"].default_value = 0.000003
    Le.new(vo.outputs["Distance"], bpe.inputs["Height"]); Le.new(bpe.outputs[0], Ne["Principled BSDF"].inputs["Normal"])
    for sx in (-1, 1):
        _ell(name + "_eye", (0.00026, 0.00028, 0.00034), (sx * 0.00027, 0.00133, -0.00004), em, root)

    # antennalar (tukli) va palplar
    ant = _curve(name + "_antennae", root, 0.000014, [chit, white])
    for sx in (-1, 1):
        sp = ant.data.splines.new("NURBS"); sp.points.add(5); sp.order_u = 3; sp.use_endpoint_u = True
        for i, p in enumerate(sp.points):
            u = i / 5; p.co = (sx * (0.00012 + 0.0007 * u), 0.00165 + 0.0011 * u, -0.0001 + 0.0009 * u - 0.0004 * u * u, 1)
            p.radius = 1.4 - 0.8 * u
        for i in range(11):                                  # tuklar halqasi
            u = 0.12 + 0.075 * i; c = Vector((sx * (0.00012 + 0.0007 * u), 0.00165 + 0.0011 * u, -0.0001 + 0.0009 * u - 0.0004 * u * u))
            for a in range(6):
                th = a / 6 * 2 * math.pi + i
                dv = Vector((math.cos(th), 0.25, math.sin(th))).normalized() * 0.00018 * (1.1 - u * 0.6)
                s2 = ant.data.splines.new("POLY"); s2.points.add(1); s2.points[0].co = (*c, 1); s2.points[1].co = (*(c + dv), 1)
                s2.points[0].radius = 0.35; s2.points[1].radius = 0.1
    for sx in (-1, 1):                                      # palplar (uchi oq)
        for k, (u0, u1, mi) in enumerate(((0.0, 0.75, 0), (0.75, 1.0, 1))):
            sp = ant.data.splines.new("POLY"); sp.points.add(1); sp.material_index = mi
            for p, u in zip(sp.points, (u0, u1)):
                q = H0 + Vector((sx * 0.00011, 0.0, 0.0)) + D0 * (0.00055 * u) + Vector((0, -0.00005, 0.0))
                p.co = (*q, 1); p.radius = 2.6
    # qanotlar
    wm = _wing_material(name + "_wing")
    wings = []
    for sx in (-1, 1):
        piv = empty(f"{name}_wpiv{sx}", (sx * 0.00028, -0.00025, 0.00062), root); piv.rotation_mode = "XYZ"
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=1, fill_type="NGON", location=(0, 0, 0))
        w = bpy.context.object; w.name = f"{name}_wing{sx}"
        for v in w.data.vertices:
            x, y = v.co.x, v.co.y
            v.co.x = x * 0.00034 * (1 - 0.35 * max(0, -y)); v.co.y = -(y * 0.0016 + 0.0016); v.co.z = 0
        w.parent = piv; w.data.materials.append(wm)
        wings.append((piv, sx))
    # oyoqlar: 6 ta, oq-qora yo'l-yo'l (har bir oyoq bo'g'imi boshida oq halqa)
    legs = _curve(name + "_legs", root, 0.000032, [chit, white])
    leg_n = 6 * (2 + 10)
    for i in range(leg_n):
        sp = legs.data.splines.new("POLY"); sp.points.add(1)
    # tumshuq: labium (tashqi qobiq) va 6 ta stilet
    lab = _curve(name + "_labium", root, 0.000055, [chit])
    sp = lab.data.splines.new("NURBS"); sp.points.add(13); sp.order_u = 4; sp.use_endpoint_u = True
    for i, p in enumerate(sp.points):
        u = i / 13; p.radius = 1.0 + 0.6 * max(0.0, (u - 0.85) / 0.15) ** 2 - 0.15 * u
    smat = pmat(name + "_stylet", (0.42, 0.2, 0.06), 0.18, 1.0, **{"Subsurface Weight": 0.3, "Subsurface Radius": (1.0, 0.5, 0.2),
                                                                     "Subsurface Scale": 0.00005})
    stylets = []
    for k in range(6):
        s = _curve(f"{name}_stylet{k}", root, 0.0000115, [smat])
        sp = s.data.splines.new("POLY"); sp.points.add(2)
        sp.points[2].radius = 0.35
        stylets.append(s)
    root.scale = (scale,) * 3
    mq = dict(root=root, wings=wings, legs=legs, labium=lab, stylets=stylets, abdomen=abd, abd_piv=abd_piv, fill=fill,
              name=name)
    pose(mq, None, 0.0, air=True)
    wings_rest(mq, None)
    return mq


def _key(p, f):
    if f is not None: p.keyframe_insert("co", frame=f)


def leg_segments(h, air, curv=None):
    """6 ta oyoq uchun bo'g'inlar ro'yxati [(a, b, mat, r0, r1)] (mahalliy koordinatada).
    h = tananing teriga botishi (teri sathi z = TIP0.z + h)."""
    zs = TIP0.z + h
    segs = []
    for k in range(3):
        for sx in (-1, 1):
            dy = (0.75, 0.05, -0.75)[k]
            a = Vector((sx * 0.00028, 0.00045 - k * 0.00038, -0.00052))
            b = a + Vector((sx * 0.0015, dy * 0.0013, 0.0008))
            if air:
                c = b + Vector((sx * 0.0006, dy * 0.0006 - 0.0006, -0.0012))
                d = c + Vector((sx * 0.0004, -0.0011, -0.0022))
            elif k == 2:                                           # orqa oyoqlar havoga ko'tarilgan
                c = b + Vector((sx * 0.0007, -0.0014, -0.0004))
                d = c + Vector((sx * 0.0006, -0.0026, 0.0016))
            else:
                d = Vector((sx * (0.0034 if k == 0 else 0.0038), a.y + dy * 0.0042 + (0.0012 if k == 0 else 0.0), zs))
                if curv: d.z -= (d.y - TIP0.y) ** 2 / (2 * curv)        # bilak yuzasi egriligi (chivin qo'lga ko'ndalang)
                c = b + (d - b) * 0.42 + Vector((sx * 0.0003, 0, 0.00025))
            segs.append((a, b, 0, 1.15, 1.0)); segs.append((b, c, 0, 1.0, 0.8))
            for t in range(5):                                     # 5 ta tarsus bo'g'imi
                u0, u1 = t / 5, (t + 1) / 5; um = u0 + (u1 - u0) * 0.28
                r0 = 0.75 - 0.08 * t; r1 = r0 - 0.08
                segs.append((c.lerp(d, u0), c.lerp(d, um), 1, r0, r0))
                segs.append((c.lerp(d, um), c.lerp(d, u1), 0, r0, r1))
    return segs


def pose(mq, f, h=0.0, spread=0.0, air=False, inject=0.0):
    """Tumshuq va oyoqlarni keyframe qiladi. h: chuqurlik (tana pastga tushadi, labium bukiladi);
    spread: stiletlar ajralib ko'rinishi (0..1). air: uchayotgan holat."""
    for sp, (a, b, mi, r0, r1) in zip(mq["legs"].data.splines, leg_segments(h, air, mq.get("curv"))):
        sp.material_index = mi
        sp.points[0].co = (*a, 1); sp.points[1].co = (*b, 1); sp.points[0].radius = r0; sp.points[1].radius = r1
        _key(sp.points[0], f); _key(sp.points[1], f)
    # labium: H0 dan teri sathidagi C gacha, uzunligi LP — vatar qisqarsa orqaga kamon bo'lib bukiladi
    chord = LP - (h / abs(D0.z) if not air else 0.0)
    C = H0 + D0 * chord
    nrm = Vector((0.0, -abs(D0.z), -abs(D0.y))).normalized()            # orqaga-pastga
    nrm = Vector((0.0, -abs(D0.z), D0.y * 0.3)).normalized()
    def length(bb):
        pts = [H0.lerp(C, i / 40) + nrm * bb * math.sin(math.pi * i / 40) ** 0.8 for i in range(41)]
        return sum((pts[i + 1] - pts[i]).length for i in range(40))
    lo, hi = 0.0, LP
    for _ in range(30):
        mid = (lo + hi) / 2
        if length(mid) < LP: lo = mid
        else: hi = mid
    bulge = lo
    sp = mq["labium"].data.splines[0]
    for i, p in enumerate(sp.points):
        u = i / (len(sp.points) - 1)
        q = H0.lerp(C, u) + nrm * bulge * math.sin(math.pi * u) ** 0.8
        p.co = (*q, 1); _key(p, f)
    # stiletlar: to'g'ri chiziq bo'ylab teriga kiradi
    e1 = Vector((1, 0, 0)); e2 = D0.cross(e1).normalized()
    s_end = (LP - 0.00005) if air else (chord + 0.0008)
    for k, s in enumerate(mq["stylets"]):
        th = k / 6 * 2 * math.pi
        off = (e1 * math.cos(th) + e2 * math.sin(th)) * 0.000021
        fan = (e1 * math.cos(th) + e2 * math.sin(th)) * 0.00028 * spread
        sp = s.data.splines[0]
        pts = (H0 + D0 * 0.0001 + off, H0 + D0 * (chord * 0.55) + off + fan, H0 + D0 * s_end + off)
        for p, q in zip(sp.points, pts):
            p.co = (*q, 1); _key(p, f)


def wings_rest(mq, f):
    for piv, sx in mq["wings"]:
        piv.rotation_euler = (R_(4), 0, R_(sx * 6))
        if f is not None: piv.keyframe_insert("rotation_euler", frame=f)


def wings_flap(mq, f):
    for piv, sx in mq["wings"]:
        up = (f % 2 == 0)
        piv.rotation_euler = (R_(10), R_(sx * (-75 if up else 55)), R_(sx * (70 if up else 45)))
        piv.keyframe_insert("rotation_euler", frame=f)


def set_fill(mq, f, v):
    key_value(mq["fill"], f, v)
    s = 1.0 + 0.9 * v
    mq["abdomen"].scale = (0.00048 * s, 0.0023 * (1 + 0.28 * v), 0.00042 * s)
    mq["abdomen"].keyframe_insert("scale", frame=f)


# ======================= MAKRO TERI (bilak) =======================
def skin_patch(name, size=0.2, res=240, arm_r=0.045):
    """bilak terisi: z=0 da, X bo'ylab bukilgan (qo'l silindri), Y = qo'l o'qi. 'WELT' shape key (qichishgan do'mboq).
    Material: RED qiymati (0..1) do'mboqni qizartiradi."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=res, y_subdivisions=res, size=size, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        v.co.z = -(v.co.x ** 2) / (2 * arm_r)
    for p in o.data.polygons: p.use_smooth = True
    o.shape_key_add(name="Basis", from_mix=False)
    kb = o.shape_key_add(name="WELT", from_mix=False); kb.value = 0.0
    for i, v in enumerate(o.data.vertices):
        r = math.hypot(v.co.x, v.co.y)
        kb.data[i].co.z = v.co.z + 0.0019 * math.exp(-(r / 0.0038) ** 2) + 0.0001 * math.exp(-(r / 0.0006) ** 2)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = _node(N, "ShaderNodeTexNoise", **{"Scale": 160.0, "Detail": 8.0}); L.new(tc.outputs["Object"], nz.inputs["Vector"])
    nz2 = _node(N, "ShaderNodeTexNoise", **{"Scale": 2500.0, "Detail": 3.0}); L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; L.new(nz.outputs["Fac"], base.inputs["Factor"])
    base.inputs[6].default_value = (0.5, 0.29, 0.2, 1); base.inputs[7].default_value = (0.4, 0.22, 0.15, 1)
    freck = N.new("ShaderNodeMix"); freck.data_type = "RGBA"; freck.blend_type = "MULTIPLY"
    L.new(_math(N, L, "MULTIPLY", _math(N, L, "GREATER_THAN", nz2.outputs["Fac"], 0.66), 0.5), freck.inputs["Factor"])
    L.new(base.outputs[2], freck.inputs[6]); freck.inputs[7].default_value = (0.8, 0.6, 0.5, 1)
    red = value_node(m, "RED", 0.0)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    r2 = _math(N, L, "ADD", _math(N, L, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]), _math(N, L, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"]))
    gauss = _math(N, L, "EXPONENT", _math(N, L, "MULTIPLY", r2, -1.0 / (0.0048 ** 2)))
    dot = _math(N, L, "EXPONENT", _math(N, L, "MULTIPLY", r2, -1.0 / (0.00035 ** 2)))
    redf = _math(N, L, "MULTIPLY", red.outputs[0], _math(N, L, "ADD", _math(N, L, "MULTIPLY", gauss, 0.75), dot, clamp=True))
    cr = N.new("ShaderNodeMix"); cr.data_type = "RGBA"; L.new(redf, cr.inputs["Factor"])
    L.new(freck.outputs[2], cr.inputs[6]); cr.inputs[7].default_value = (0.62, 0.08, 0.06, 1)
    L.new(cr.outputs[2], b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 0.45; b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.0012
    L.new(_math(N, L, "ADD", 0.38, _math(N, L, "MULTIPLY", nz.outputs["Fac"], 0.2)), b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.6
    pores = _node(N, "ShaderNodeTexVoronoi"); pores.inputs["Scale"].default_value = 2200.0; L.new(tc.outputs["Object"], pores.inputs["Vector"])
    w1 = _node(N, "ShaderNodeTexWave", **{"Scale": 180.0, "Distortion": 6.0, "Detail": 3.0}); L.new(tc.outputs["Object"], w1.inputs["Vector"])
    w2 = _node(N, "ShaderNodeTexWave", **{"Scale": 140.0, "Distortion": 7.0, "Detail": 3.0}); w2.bands_direction = "Y"
    L.new(tc.outputs["Object"], w2.inputs["Vector"])
    hgt = _math(N, L, "ADD", pores.outputs["Distance"], _math(N, L, "MULTIPLY", _math(N, L, "MULTIPLY", w1.outputs["Fac"], w2.outputs["Fac"]), 0.6))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.00006
    L.new(hgt, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    o.data.materials.append(m)
    # mayda tuklar
    hm = pmat(name + "_hair", (0.06, 0.035, 0.02), 0.35, 0.0)
    cu = bpy.data.curves.new(name + "_hairs", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.000016; cu.bevel_resolution = 1
    cu.materials.append(hm)
    rnd = random.Random(5)
    n = 0
    while n < 160:
        x, y = rnd.uniform(-0.035, 0.035), rnd.uniform(-0.05, 0.05)
        if math.hypot(x, y * 0.8) < 0.0045: continue
        n += 1
        ln = rnd.uniform(0.0025, 0.0055); a = R_(rnd.uniform(-25, 25)); rise = rnd.uniform(0.12, 0.3)
        sp = cu.splines.new("NURBS"); sp.points.add(3); sp.order_u = 3; sp.use_endpoint_u = True
        for i, p in enumerate(sp.points):
            u = i / 3
            px = x + math.sin(a) * ln * u; py = y + math.cos(a) * ln * u
            pz = -(px ** 2) / (2 * arm_r) + ln * rise * math.sin(u * 2.2) * 0.6 - 0.00005
            p.co = (px, py, pz, 1); p.radius = 1.0 - 0.7 * u
    ho = bpy.data.objects.new(name + "_hairs", cu); bpy.context.scene.collection.objects.link(ho); ho.parent = o
    return o, red


def welt_key(o, f, v):
    kb = o.data.shape_keys.key_blocks["WELT"]; kb.value = v; kb.keyframe_insert("value", frame=f)


# ======================= QON HUJAYRALARI =======================
def rbc_mesh(name, r):
    """eritrotsit: o'rtasi botiq disk"""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        rr = math.hypot(v.co.x, v.co.y)
        th = 0.18 + 0.32 * rr ** 2
        v.co.z = math.copysign(th, v.co.z) * (abs(v.co.z) > 1e-6)
        v.co *= r
    for p in o.data.polygons: p.use_smooth = True
    bpy.ops.object.transform_apply(scale=True)
    return o
