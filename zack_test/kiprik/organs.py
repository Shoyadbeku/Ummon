# Procedural a'zolar: kiprikchalar maydoni (Geometry Nodes to'lqini), shilimshiq, traxeya tunneli,
# bronxlar daraxti (rentgen), o'pka, molekulalar, qatron, chang, mikroblar.
import bpy, math, random
from mathutils import Vector, Matrix, Quaternion
import lib as U
from lib import R, _m

# ======================================================================
# KIPRIKCHALAR: bitta mesh (har biri ingichka quvur), har vertexda "h" (0 ildiz .. 1 uch), "ph" (tasodifiy faza)
# GN: offset = egilish (Amp * sin(k*x - T + ph) + Droop) -> kiprikcha ildiz atrofida X tomonga egiladi
# ======================================================================
def cilia_mesh(name, size=(4.0, 2.4), n=(100, 60), L=0.25, r0=0.007, seg=7, sides=6, seed=3):
    rnd = random.Random(seed)
    V = []; F = []; H = []; PHs = []; LEN = []
    dx = size[0] / n[0]; dy = size[1] / n[1]
    for i in range(n[0]):
        for j in range(n[1]):
            x = -size[0] / 2 + (i + 0.5 + rnd.uniform(-0.35, 0.35)) * dx
            y = -size[1] / 2 + (j + 0.5 + rnd.uniform(-0.35, 0.35)) * dy
            ln = L * rnd.uniform(0.85, 1.1); ph = rnd.uniform(-0.35, 0.35); lean = (rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04))
            base = len(V)
            for s in range(seg + 1):
                h = s / seg; r = r0 * (1 - 0.55 * h)
                cx = x + lean[0] * h * ln; cy = y + lean[1] * h * ln; cz = h * ln
                for k in range(sides):
                    a = 2 * math.pi * k / sides
                    V.append((cx + r * math.cos(a), cy + r * math.sin(a), cz)); H.append(h); PHs.append(ph); LEN.append(ln)
            tip = len(V); V.append((x + lean[0] * ln, y + lean[1] * ln, ln + r0 * 0.4)); H.append(1.0); PHs.append(ph); LEN.append(ln)
            for s in range(seg):
                for k in range(sides):
                    a = base + s * sides + k; b = base + s * sides + (k + 1) % sides
                    F.append((a, b, b + sides, a + sides))
            top = base + seg * sides
            for k in range(sides): F.append((top + k, top + (k + 1) % sides, tip))
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F)
    for p in me.polygons: p.use_smooth = True
    for nm, arr in (("h", H), ("ph", PHs), ("ln", LEN)):
        at = me.attributes.new(nm, "FLOAT", "POINT"); at.data.foreach_set("value", arr)
    o = bpy.data.objects.new(name, me); U.link(o)
    return o

_CG = None
def cilia_group():
    global _CG
    if _CG: return _CG
    ng = bpy.data.node_groups.new("CiliaBeat", "GeometryNodeTree"); I = ng.interface
    I.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm, dv in (("T", 0.0), ("Amp", 1.0), ("Droop", 0.0), ("K", 10.5)):
        s = I.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = dv
    I.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    def attr(nm):
        a = N.new("GeometryNodeInputNamedAttribute"); a.data_type = "FLOAT"; a.inputs["Name"].default_value = nm
        return a.outputs["Attribute"]
    h = attr("h"); ph = attr("ph"); ln = attr("ln")
    pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sep.inputs[0])
    x = sep.outputs[0]; y = sep.outputs[1]
    phase = _m(N, L, "ADD", _m(N, L, "SUBTRACT", _m(N, L, "MULTIPLY", x, gi.outputs["K"]), gi.outputs["T"]),
               _m(N, L, "ADD", ph, _m(N, L, "MULTIPLY", y, 1.3)))
    s_ = _m(N, L, "SINE", phase); c_ = _m(N, L, "COSINE", phase)
    # samarali zarba (+X) tez, qaytish sekin: sin + 0.35*sin(2x) asimmetriya
    beat = _m(N, L, "ADD", s_, _m(N, L, "MULTIPLY", _m(N, L, "SINE", _m(N, L, "MULTIPLY", phase, 2.0)), 0.3))
    th = _m(N, L, "ADD", _m(N, L, "MULTIPLY", _m(N, L, "MULTIPLY", beat, gi.outputs["Amp"]), 0.75), _m(N, L, "MULTIPLY", gi.outputs["Droop"], 1.25))
    hp = _m(N, L, "POWER", h, 1.6)
    rl = _m(N, L, "MULTIPLY", hp, ln)
    dx = _m(N, L, "MULTIPLY", rl, _m(N, L, "SINE", th))
    dz = _m(N, L, "MULTIPLY", rl, _m(N, L, "SUBTRACT", _m(N, L, "COSINE", th), 1.0))
    # qaytish zarbasida yon tomonga (y) og'ish
    dy = _m(N, L, "MULTIPLY", _m(N, L, "MULTIPLY", _m(N, L, "MULTIPLY", hp, ln), c_), _m(N, L, "MULTIPLY", gi.outputs["Amp"], 0.18))
    comb = N.new("ShaderNodeCombineXYZ"); L.new(dx, comb.inputs[0]); L.new(dy, comb.inputs[1]); L.new(dz, comb.inputs[2])
    sp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(comb.outputs[0], sp.inputs["Offset"])
    L.new(sp.outputs[0], go.inputs[0])
    _CG = ng
    return ng

def cilia_ids():
    g = cilia_group()
    return {it.name: it.identifier for it in g.interface.items_tree if getattr(it, "in_out", "") == "INPUT" and it.socket_type != "NodeSocketGeometry"}

def key_cilia(o, nm, f, v):
    ids = cilia_ids(); x = getattr(o.modifiers["beat"].properties.inputs, ids[nm]); x.value = v; x.keyframe_insert("value", frame=f)

def cilia_material():
    m = bpy.data.materials.new("cilia"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "h"
    cr = N.new("ShaderNodeValToRGB"); L.new(attr.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.55, 0.12, 0.16, 1); cr.color_ramp.elements[1].color = (0.98, 0.72, 0.68, 1)
    U.value_node(m, "DEAD", 0.0); U.value_node(m, "TAR", 0.0)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(N["DEAD"].outputs[0], mx.inputs["Factor"])
    L.new(cr.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.42, 0.38, 0.33, 1)
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"
    L.new(_m(N, L, "MULTIPLY", N["TAR"].outputs[0], _m(N, L, "POWER", attr.outputs["Fac"], 0.7)), mx2.inputs["Factor"])
    L.new(mx.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = (0.12, 0.06, 0.02, 1)
    L.new(mx2.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.3; b.inputs["Coat Weight"].default_value = 0.6
    b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.3)
    b.inputs["Subsurface Scale"].default_value = 0.004
    # uchlari biroz yorug'likni o'tkazadi (sheen)
    b.inputs["Sheen Weight"].default_value = 0.4; b.inputs["Sheen Tint"].default_value = (1, 0.8, 0.8, 1)
    return m

def epithelium_material():
    m = bpy.data.materials.new("epithelium"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 9.0
    cr = N.new("ShaderNodeValToRGB"); L.new(vo.outputs["Distance"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.18, 0.02, 0.04, 1); cr.color_ramp.elements[1].position = 0.12
    cr.color_ramp.elements[1].color = (0.62, 0.16, 0.18, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; L.new(vo.outputs["Distance"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.8
    b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Scale"].default_value = 0.01
    U.value_node(m, "DEAD", 0.0)
    return m

def mucus_material():
    """shilimshiq: yarim shaffof sarg'ish-yashil, Transmission'siz (Layer Weight bilan Transparent aralashmasi)"""
    m = bpy.data.materials.new("mucus"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.78, 0.82, 0.5, 1); b.inputs["Roughness"].default_value = 0.04
    b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.02
    U.value_node(m, "DIRTY", 0.0)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(N["DIRTY"].outputs[0], mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.78, 0.82, 0.5, 1); mx.inputs[7].default_value = (0.32, 0.22, 0.08, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
    op = _m(N, L, "ADD", 0.22, _m(N, L, "MULTIPLY", lw.outputs["Facing"], 0.6), clamp=True)
    op = _m(N, L, "ADD", op, _m(N, L, "MULTIPLY", N["DIRTY"].outputs[0], 0.3), clamp=True)
    U.fade_mix(m, op, N, L, b.outputs[0])
    return m

def mucus_sheet(name, size, z, m, flow_empty):
    o = U.plane(name, size, (0, 0, z), m)
    me = o.data
    sd = o.modifiers.new("sub", "SUBSURF"); sd.subdivision_type = "SIMPLE"; sd.levels = 6; sd.render_levels = 7
    tex = bpy.data.textures.new(name + "_tex", "CLOUDS"); tex.noise_scale = 0.35; tex.noise_depth = 2
    dp = o.modifiers.new("disp", "DISPLACE"); dp.texture = tex; dp.texture_coords = "OBJECT"; dp.texture_coords_object = flow_empty
    dp.strength = 0.06; dp.mid_level = 0.5
    sm = o.modifiers.new("smooth", "SMOOTH"); sm.iterations = 4
    for p in me.polygons: p.use_smooth = True
    return o

# ======================================================================
# CHANG, MIKROB, MOLEKULA, QATRON
# ======================================================================
def rock(name, r, m, seed, parent=None):
    rnd = random.Random(seed)
    o = U.sphere(name, r, (0, 0, 0), m, sub=2, parent=parent)
    for v in o.data.vertices:
        v.co *= rnd.uniform(0.7, 1.25)
    o.scale = (rnd.uniform(0.7, 1.3), rnd.uniform(0.7, 1.3), rnd.uniform(0.6, 1.0))
    o.rotation_euler = (rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6))
    return o

def bacterium(name, r, length, m, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=r)
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        if v.co.z > 0: v.co.z += length / 2
        else: v.co.z -= length / 2
    o.data.materials.append(m); U._smooth(o)
    if parent: o.parent = parent
    return o

def molecule(name, m_atom, m_atom2, m_bond, seed, size=0.016, parent=None):
    rnd = random.Random(seed)
    root = U.empty(name, (0, 0, 0), parent)
    pts = [Vector((0, 0, 0))]
    for k in range(rnd.randint(3, 6)):
        base = rnd.choice(pts)
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * size * 2.6
        p = base + d; pts.append(p)
        mid = (base + p) / 2
        b = U.cyl(f"{name}_b{k}", size * 0.28, d.length, tuple(mid), m_bond, parent=root, verts=10)
        b.rotation_mode = "QUATERNION"; b.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    for i, p in enumerate(pts):
        U.sphere(f"{name}_a{i}", size * (1.0 if i % 3 else 1.25), tuple(p), m_atom if i % 2 == 0 else m_atom2, sub=2, parent=root)
    return root

# ======================================================================
# TRAXEYA TUNNELI (ichidan ko'rinish): +Y o'qi bo'ylab, xalqa tog'aylar
# ======================================================================
def airway_material(name="airway"):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.0; nz.inputs["Detail"].default_value = 10.0
    nz.inputs["Roughness"].default_value = 0.6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 30.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.45, 0.07, 0.08, 1); cr.color_ramp.elements[1].color = (0.85, 0.36, 0.34, 1)
    # mayda tomirchalar
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 2.5; wv.inputs["Distortion"].default_value = 14.0
    wv.inputs["Detail"].default_value = 6.0; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    vein = _m(N, L, "GREATER_THAN", wv.outputs["Fac"], 0.93)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(_m(N, L, "MULTIPLY", vein, 0.7), mx.inputs["Factor"])
    L.new(cr.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.35, 0.02, 0.03, 1)
    U.value_node(m, "SMOKE", 0.0)
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; L.new(N["SMOKE"].outputs[0], mx2.inputs["Factor"])
    L.new(mx.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = (0.25, 0.14, 0.08, 1)
    L.new(mx2.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.12; b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.05
    b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Scale"].default_value = 0.05
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
    L.new(_m(N, L, "ADD", nz.outputs["Fac"], _m(N, L, "MULTIPLY", vo.outputs["Distance"], 0.4)), bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def tunnel(name, length=40.0, r=1.0, nx=480, nr=72, ring_pitch=0.55, parent=None, m=None):
    V = []; F = []
    for i in range(nx + 1):
        y = length * i / nx
        ring = math.sin(math.pi * y / ring_pitch) ** 8
        for j in range(nr):
            a = 2 * math.pi * j / nr
            # orqa devor (membrana, -Z tomonda) tekisroq, xalqasiz
            back = max(0.0, -math.sin(a)) ** 3
            rr = r * (1 - 0.07 * ring * (1 - back) + 0.02 * math.sin(a * 3 + y * 0.7) + 0.06 * back)
            V.append((rr * math.cos(a), y, rr * math.sin(a)))
    for i in range(nx):
        for j in range(nr):
            a = i * nr + j; b = i * nr + (j + 1) % nr
            F.append((a, a + nr, b + nr, b))
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); U.link(o, parent)
    o.data.materials.append(m or airway_material())
    return o

# ======================================================================
# BRONXLAR DARAXTI (rentgen uchun): traxeya + tarmoqlar; qaytaradi: (tubes, leaf_paths)
# ======================================================================
def airway_tree(top, carina, side, fwd, mat_tube, seed=4, depth=4):
    import sys
    sys.path.insert(0, U.os.path.join(U.os.path.dirname(U.HERE), "burish"))
    import parts as P
    rnd = random.Random(seed)
    tubes = []; paths = []
    up = (top - carina).normalized()
    tubes.append(P.tube("trachea_x", [tuple(top), tuple(top.lerp(carina, 0.5) + fwd * 0.004), tuple(carina)], 0.011, mat_tube))
    def grow(p0, d, ln, rad, lvl, path):
        p1 = p0 + d * ln
        mid = p0.lerp(p1, 0.5) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * ln * 0.08
        tubes.append(P.tube(f"br{len(tubes)}", [tuple(p0), tuple(mid), tuple(p1)], rad, mat_tube, taper=[1, 0.9, 0.8]))
        path2 = path + [p1]
        if lvl >= depth:
            paths.append(list(reversed(path2))); return
        for k in (-1, 1):
            ax = d.cross(fwd).normalized() if abs(d.dot(fwd)) < 0.95 else side
            q = Quaternion(ax, R(rnd.uniform(22, 38)) * k)
            q2 = Quaternion(d, R(rnd.uniform(-60, 60)))
            nd = (q2 @ (q @ d)).normalized()
            nd = (nd - up * 0.15).normalized()
            grow(p1, nd, ln * rnd.uniform(0.68, 0.8), rad * 0.72, lvl + 1, path2)
    for sx in (-1, 1):
        d0 = (side * sx * 0.75 - up * 0.65).normalized()
        grow(carina, d0, 0.06, 0.008, 1, [top, carina])
    return tubes, paths
