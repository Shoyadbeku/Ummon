# "Barmoqlar nega burishadi" uchun procedural modellar:
# barmoq (burmalari Geometry Nodes bilan animatsiya qilinadi), teri kesimi, tomir/asab egri chiziqlari,
# miya, suv, pufakchalar, tomchilar, rentgen (shaffof) material.
import bpy, math, random
from mathutils import Vector, Matrix

R = math.radians
sc = lambda: bpy.context.scene
VIEWPORT_OFF = False
def _vp(mod):
    if VIEWPORT_OFF: mod.show_viewport = False
    return mod

def link(o, parent=None):
    sc().collection.objects.link(o)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); e.location = loc; e.empty_display_size = 0.01
    return link(e, parent)

def node(N, t, loc=None, **inputs):
    n = N.new(t)
    for k, v in inputs.items(): n.inputs[k].default_value = v
    return n

def math_n(N, L, op, a=None, b=None, clamp=False, vec=False):
    n = N.new("ShaderNodeVectorMath" if vec else "ShaderNodeMath"); n.operation = op
    if not vec: n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)) or (vec and isinstance(x, tuple)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0] if not vec or op not in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Value"]

def key_socket(sock, f, v):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)

def mod_in(obj, mod, ident):
    return getattr(obj.modifiers[mod].properties.inputs, ident)

def set_mod(obj, mod, ident, v):
    mod_in(obj, mod, ident).value = v

def key_mod(obj, mod, ident, f, v):
    x = mod_in(obj, mod, ident); x.value = v; x.keyframe_insert("value", frame=f)

# ======================================================================
# BURMA (wrinkle) Geometry Nodes guruhi
# ======================================================================
_WR = None
def wrinkle_group():
    """Kirish: Geometry, Strength (0..1), Radius (barmoq radiusi), PadEnd (yostiqcha uzunligi, m).
    Barmoq uchi (0,0,0), tanasi +Y bo'ylab, tirnoq +Z. Burmalar barmoq bo'ylab (uzunasiga) ketadi."""
    global _WR
    if _WR: return _WR
    ng = bpy.data.node_groups.new("Wrinkles", "GeometryNodeTree")
    I = ng.interface
    I.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    s = I.new_socket("Strength", in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = 0.0
    s = I.new_socket("Radius", in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = 0.0078
    s = I.new_socket("PadEnd", in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = 0.026
    s = I.new_socket("Seed", in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = 0.0
    I.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    sub = N.new("GeometryNodeSubdivisionSurface"); sub.inputs["Level"].default_value = 2
    L.new(gi.outputs["Geometry"], sub.inputs["Mesh"])
    pos = N.new("GeometryNodeInputPosition"); nor = N.new("GeometryNodeInputNormal")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sep.inputs[0])
    x, y, z = sep.outputs
    # aylana bo'ylab yoy uzunligi: atan2(x, -z) * r  (yostiqcha -Z tomonda, 0 burchak)
    ang = math_n(N, L, "ARCTAN2", x, math_n(N, L, "MULTIPLY", z, -1.0))
    arc = math_n(N, L, "MULTIPLY", ang, gi.outputs["Radius"])
    yy = math_n(N, L, "ADD", y, gi.outputs["Seed"])
    comb = N.new("ShaderNodeCombineXYZ"); L.new(arc, comb.inputs[0]); L.new(yy, comb.inputs[1])
    # uzunasiga egri-bugri burmalar: X yo'nalishli to'lqin + kuchli buzilish
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"; wv.wave_profile = "SIN"
    wv.inputs["Scale"].default_value = 190.0; wv.inputs["Distortion"].default_value = 16.0
    wv.inputs["Detail"].default_value = 3.0; wv.inputs["Detail Scale"].default_value = 0.35
    wv.inputs["Detail Roughness"].default_value = 0.55
    L.new(comb.outputs[0], wv.inputs["Vector"])
    # ingichka ariqcha va keng tepacha: h = fac^0.45
    h = math_n(N, L, "POWER", wv.outputs["Fac"], 0.45)
    # ikkinchi, mayda shoxlanuvchi qatlam
    wv2 = N.new("ShaderNodeTexWave"); wv2.wave_type = "BANDS"; wv2.bands_direction = "DIAGONAL"
    wv2.inputs["Scale"].default_value = 160.0; wv2.inputs["Distortion"].default_value = 22.0; wv2.inputs["Detail"].default_value = 3.0
    wv2.inputs["Detail Scale"].default_value = 0.5
    L.new(comb.outputs[0], wv2.inputs["Vector"])
    h2 = math_n(N, L, "POWER", wv2.outputs["Fac"], 0.5)
    hh = math_n(N, L, "MINIMUM", h, math_n(N, L, "ADD", h2, 0.35))   # qiya ariqchalar shoxlanish beradi
    hc = math_n(N, L, "SUBTRACT", hh, 0.75)                         # o'rtacha ~0
    # niqob: yostiqcha (y < PadEnd), tirnoq tomonida (z>0) kamroq
    my = N.new("ShaderNodeMapRange"); L.new(y, my.inputs["Value"]); L.new(gi.outputs["PadEnd"], my.inputs["From Min"])
    my.inputs["From Max"].default_value = 0.0; my.inputs["To Min"].default_value = 0.0; my.inputs["To Max"].default_value = 1.0
    my.interpolation_type = "SMOOTHSTEP"; my.inputs["From Min"].default_value = 0.03
    pad_lo = math_n(N, L, "SUBTRACT", gi.outputs["PadEnd"], 0.0)
    L.new(pad_lo, my.inputs["From Min"])
    mz = N.new("ShaderNodeMapRange"); L.new(z, mz.inputs["Value"])
    L.new(math_n(N, L, "MULTIPLY", gi.outputs["Radius"], 0.85), mz.inputs["From Min"])
    L.new(math_n(N, L, "MULTIPLY", gi.outputs["Radius"], 0.1), mz.inputs["From Max"])
    mz.interpolation_type = "SMOOTHSTEP"
    mtip = N.new("ShaderNodeMapRange"); L.new(y, mtip.inputs["Value"]); mtip.inputs["From Min"].default_value = 0.0008
    mtip.inputs["From Max"].default_value = 0.0055; mtip.interpolation_type = "SMOOTHSTEP"
    mask = math_n(N, L, "MULTIPLY", math_n(N, L, "MULTIPLY", my.outputs[0], mz.outputs[0]), mtip.outputs[0])
    amt = math_n(N, L, "MULTIPLY", mask, gi.outputs["Strength"])
    d = math_n(N, L, "MULTIPLY", math_n(N, L, "MULTIPLY", hc, amt), 0.0008)
    # burishganda yostiqcha biroz "sinadi" (hajm kamayadi)
    d = math_n(N, L, "SUBTRACT", d, math_n(N, L, "MULTIPLY", amt, 0.00018))
    off = N.new("ShaderNodeVectorMath"); off.operation = "SCALE"; L.new(nor.outputs[0], off.inputs[0]); L.new(d, off.inputs["Scale"])
    sp = N.new("GeometryNodeSetPosition"); L.new(sub.outputs[0], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
    # shader uchun atribut: ariqcha chuqurligi (0..1) * niqob
    st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = "FLOAT"; st.domain = "POINT"; st.inputs["Name"].default_value = "wr"
    groove = math_n(N, L, "MULTIPLY", math_n(N, L, "SUBTRACT", 1.0, hh), amt)
    L.new(sp.outputs[0], st.inputs["Geometry"]); L.new(groove, st.inputs["Value"])
    st2 = N.new("GeometryNodeStoreNamedAttribute"); st2.data_type = "FLOAT"; st2.domain = "POINT"; st2.inputs["Name"].default_value = "wmask"
    L.new(st.outputs[0], st2.inputs["Geometry"]); L.new(amt, st2.inputs["Value"])
    sm = N.new("GeometryNodeSetShadeSmooth"); L.new(st2.outputs[0], sm.inputs["Geometry"])
    L.new(sm.outputs[0], go.inputs["Geometry"])
    _WR = ng
    return ng

# ======================================================================
# TERI MATERIALI
# ======================================================================
def skin_material(name, base=(0.74, 0.47, 0.37), wet=0.0, prints=True):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    # rang: dog'lar, qizg'ish joylar
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 260.0; nz.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (base[0] * 0.92, base[1] * 0.8, base[2] * 0.78, 1)
    cr.color_ramp.elements[1].color = (min(1, base[0] * 1.06), base[1] * 1.04, base[2] * 1.02, 1)
    # burmalar: ariqchalar qizg'ish-qorong'i, tepachalar oqarib ketgan
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "wr"
    am = N.new("ShaderNodeAttribute"); am.attribute_name = "wmask"
    pale = N.new("ShaderNodeMix"); pale.data_type = "RGBA"; L.new(am.outputs["Fac"], pale.inputs["Factor"])
    L.new(cr.outputs[0], pale.inputs[6]); pale.inputs[7].default_value = (0.86, 0.66, 0.6, 1)
    grv = N.new("ShaderNodeMix"); grv.data_type = "RGBA"
    L.new(math_n(N, L, "MULTIPLY", at.outputs["Fac"], 1.6, clamp=True), grv.inputs["Factor"])
    L.new(pale.outputs[2], grv.inputs[6]); grv.inputs[7].default_value = (0.42, 0.17, 0.13, 1)
    L.new(grv.outputs[2], b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 1.0
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.18)
    b.inputs["Subsurface Scale"].default_value = 0.0012
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Coat Weight"].default_value = wet; b.inputs["Coat Roughness"].default_value = 0.04
    # g'ovaklar + barmoq izi (bump)
    bump_src = None
    pores = N.new("ShaderNodeTexVoronoi"); pores.inputs["Scale"].default_value = 2200.0
    L.new(tc.outputs["Object"], pores.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.00004
    L.new(pores.outputs["Distance"], bp.inputs["Height"])
    last = bp
    if prints:
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 520.0
        wv.inputs["Distortion"].default_value = 4.0; wv.inputs["Detail"].default_value = 2.0
        mp = N.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (0, -0.012, 0.0)
        mp.inputs["Scale"].default_value = (1.0, 1.4, 1.0)
        L.new(tc.outputs["Object"], mp.inputs[0]); L.new(mp.outputs[0], wv.inputs["Vector"])
        bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = 0.35; bp2.inputs["Distance"].default_value = 0.00005
        L.new(wv.outputs["Fac"], bp2.inputs["Height"]); L.new(bp.outputs[0], bp2.inputs["Normal"]); last = bp2
    L.new(last.outputs[0], b.inputs["Normal"])
    wetv = N.new("ShaderNodeValue"); wetv.name = "wet"; wetv.outputs[0].default_value = wet
    L.new(wetv.outputs[0], b.inputs["Coat Weight"])
    return m

def nail_material():
    m = bpy.data.materials.get("nail")
    if m: return m
    m = bpy.data.materials.new("nail"); m.use_nodes = True; nb = m.node_tree.nodes["Principled BSDF"]
    nb.inputs["Base Color"].default_value = (0.86, 0.6, 0.56, 1); nb.inputs["Roughness"].default_value = 0.2
    nb.inputs["Coat Weight"].default_value = 0.9; nb.inputs["Coat Roughness"].default_value = 0.03
    nb.inputs["Subsurface Weight"].default_value = 0.4; nb.inputs["Subsurface Scale"].default_value = 0.0006
    return m

# ======================================================================
# BARMOQ
# ======================================================================
def build_finger(name, parent=None, r=0.0078, length=0.075, skin=None, strength=0.0, seed=0.0, knuckle=True):
    """uchi (0,0,0) da, tanasi +Y bo'ylab, tirnoq +Z tomonda. Burma kuchi: modifier 'wr' -> Socket 'Strength'."""
    # parametrik mesh: uchi yarim shar (0..pi/2), keyin silindr; halqalar bo'ylab profil
    SEG = 128; prof = []
    for i in range(1, 25):                                   # yarim shar (uchidan)
        th = (i / 24) * (math.pi / 2)
        prof.append((r - r * math.cos(th), math.sin(th)))   # (y, radius koeff.)
    n_len = 90
    for i in range(1, n_len + 1):
        prof.append((r + length * i / n_len, 1.0))
    verts = [(0.0, 0.0, 0.0)]
    for y, k in prof:
        for j in range(SEG):
            a_ = 2 * math.pi * j / SEG
            verts.append((k * r * math.sin(a_), y, -k * r * math.cos(a_)))
    faces = [(0, 1 + (j + 1) % SEG, 1 + j) for j in range(SEG)]
    for i in range(len(prof) - 1):
        b0 = 1 + i * SEG; b1 = b0 + SEG
        for j in range(SEG):
            j2 = (j + 1) % SEG
            faces.append((b0 + j, b0 + j2, b1 + j2, b1 + j))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); link(o)
    for v in o.data.vertices:
        y = v.co.y
        v.co.z *= 0.84
        if v.co.z < 0:                                        # yostiqcha (pad) bo'rtig'i
            v.co.z *= 1.0 + 0.2 * math.exp(-((y - 0.011) / 0.009) ** 2)
        else:                                                 # tirnoq ostida tekisroq
            v.co.z *= 1.0 - 0.08 * math.exp(-((y - 0.012) / 0.012) ** 2)
        k = 1.0 - 0.05 * max(0.0, (0.02 - y) / 0.02)
        if knuckle:
            k *= 1.0 + 0.06 * math.exp(-((y - 0.03) / 0.004) ** 2) + 0.07 * math.exp(-((y - 0.062) / 0.006) ** 2)
            k *= 1.0 + 0.1 * max(0.0, (y - 0.035) / 0.045)
        v.co.x *= k; v.co.z *= k
        if v.co.z < 0 and knuckle:                            # bo'g'imdagi ko'ndalang burmalar
            for yc in (0.0285, 0.0305, 0.0605):
                v.co.z += 0.0003 * math.exp(-((y - yc) / 0.0006) ** 2)
    o.data.shade_smooth()
    mod = _vp(o.modifiers.new("wr", "NODES")); mod.node_group = wrinkle_group()
    ids = {it.name: it.identifier for it in wrinkle_group().interface.items_tree if getattr(it, "in_out", "") == "INPUT"}
    set_mod(o, "wr", ids["Radius"], r); set_mod(o, "wr", ids["Strength"], strength); set_mod(o, "wr", ids["Seed"], seed)
    o["wr_id"] = ids["Strength"]
    o.data.materials.append(skin or skin_material(name + "_skin"))
    # tirnoq
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(0, 0.0125, r * 0.66))
    nail = bpy.context.object; nail.name = name + "_nail"; nail.scale = (r * 0.74, 0.0115, r * 0.17)
    nail.rotation_euler = (R(-3), 0, 0)
    for v in nail.data.vertices:                              # tirnoq uchi biroz tekis kesilgan
        if v.co.y < -0.85: v.co.y = -0.85
    nail.data.materials.append(nail_material()); nail.parent = o
    for p in nail.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o

def set_wrinkle(o, f, v):
    key_mod(o, "wr", o["wr_id"], f, v)

# ======================================================================
# SUV / TOMCHI / PUFAKCHA materiallari
# ======================================================================
def water_material(name="water", tint=(0.85, 0.95, 1.0), rough=0.02):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*tint, 1); b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.333; b.inputs["Roughness"].default_value = rough
    return m

def bubble_material():
    m = bpy.data.materials.get("bubble")
    if m: return m
    m = bpy.data.materials.new("bubble"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    gl = N.new("ShaderNodeBsdfGlass"); gl.inputs["IOR"].default_value = 1.0 / 1.333; gl.inputs["Roughness"].default_value = 0.0
    L.new(gl.outputs[0], out.inputs[0])
    return m

def droplet(name, loc, r, parent=None, mat=None, squash=0.6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = (1, 1, squash)
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(mat or water_material("drop"))
    if parent: o.parent = parent
    return o

def drops_on(target, n, rmin, rmax, mat, seed=1, region=None, align=True):
    """target mesh sirtiga n ta tomchi (target koordinatasida). region(p)->bool."""
    rnd = random.Random(seed); out = []
    me = target.data; polys = list(me.polygons); tries = 0
    while len(out) < n and tries < n * 50:
        tries += 1
        p = rnd.choice(polys); c = p.center.copy()
        if region and not region(c): continue
        r = rnd.uniform(rmin, rmax)
        d = droplet(f"{target.name}_drop{len(out)}", (0, 0, 0), r, target, mat, squash=0.45)
        nrm = p.normal.copy()
        d.location = c + nrm * r * 0.25
        d.rotation_euler = Vector((0, 0, 1)).rotation_difference(nrm).to_euler()
        out.append(d)
    return out

# ======================================================================
# EGRI CHIZIQ (tomir, asab) — bevel bilan, signal impulsi uchun UV
# ======================================================================
_TUBE = None
def tube_group():
    """egri chiziq -> quvur (Curve to Mesh); 'u' atributi = egri bo'ylab parametr (0..1) impuls uchun"""
    global _TUBE
    if _TUBE: return _TUBE
    ng = bpy.data.node_groups.new("Tube", "GeometryNodeTree"); I = ng.interface
    I.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    s = I.new_socket("Radius", in_out="INPUT", socket_type="NodeSocketFloat"); s.default_value = 0.01
    I.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    rs = N.new("GeometryNodeResampleCurve"); rs.inputs["Count"].default_value = 64; L.new(gi.outputs[0], rs.inputs["Curve"])
    par = N.new("GeometryNodeSplineParameter")
    st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = "FLOAT"; st.domain = "POINT"; st.inputs["Name"].default_value = "u"
    L.new(rs.outputs[0], st.inputs["Geometry"]); L.new(par.outputs["Factor"], st.inputs["Value"])
    circ = N.new("GeometryNodeCurvePrimitiveCircle"); circ.inputs["Resolution"].default_value = 12; circ.inputs["Radius"].default_value = 1.0
    rad = N.new("GeometryNodeInputRadius")
    sc_ = math_n(N, L, "MULTIPLY", rad.outputs[0], gi.outputs["Radius"])
    cm = N.new("GeometryNodeCurveToMesh"); L.new(st.outputs[0], cm.inputs["Curve"]); L.new(circ.outputs["Curve"], cm.inputs["Profile Curve"])
    L.new(sc_, cm.inputs["Scale"]); cm.inputs["Fill Caps"].default_value = True
    sm = N.new("GeometryNodeSetShadeSmooth"); L.new(cm.outputs[0], sm.inputs["Geometry"]); L.new(sm.outputs[0], go.inputs[0])
    _TUBE = ng
    return ng

def tube(name, pts, radius, mat, parent=None, res=12, taper=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.resolution_u = res
    sp = cu.splines.new("NURBS" if len(pts) > 2 else "POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        w = 1.0 if taper is None else taper[i]
        sp.points[i].co = (*p, 1.0); sp.points[i].radius = w
    if len(pts) > 2: sp.use_endpoint_u = True; sp.order_u = 3
    o = bpy.data.objects.new(name, cu); link(o, parent); cu.materials.append(mat)
    m = o.modifiers.new("tube", "NODES"); m.node_group = tube_group()
    o["r_id"] = next(it.identifier for it in tube_group().interface.items_tree if getattr(it, "name", "") == "Radius")
    set_mod(o, "tube", o["r_id"], radius); o["r0"] = radius
    return o

def tube_r(o, f, v):
    key_mod(o, "tube", o["r_id"], f, v)

def pulse_material(name, col, base_emit=1.0, pulse_col=None, width=0.06):
    """Egri bo'ylab yuradigan impuls: 'pos' qiymati (0..1+) keyframe qilinadi, 'glow' umumiy yorqinlik."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.3
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    class _S: outputs = [ua.outputs["Fac"]]
    sx = _S()
    pos = N.new("ShaderNodeValue"); pos.name = "pos"; pos.outputs[0].default_value = -1.0
    glow = N.new("ShaderNodeValue"); glow.name = "glow"; glow.outputs[0].default_value = base_emit
    dist = math_n(N, L, "ABSOLUTE", math_n(N, L, "SUBTRACT", sx.outputs[0], pos.outputs[0]))
    p = math_n(N, L, "MULTIPLY", math_n(N, L, "SUBTRACT", 1.0, math_n(N, L, "DIVIDE", dist, width), clamp=True), 1.0)
    p = math_n(N, L, "POWER", p, 2.0)
    # impuls ortidan qolgan iz
    trail = math_n(N, L, "MULTIPLY", math_n(N, L, "LESS_THAN", sx.outputs[0], pos.outputs[0]), 0.25)
    e = math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", p, 40.0), math_n(N, L, "MULTIPLY", trail, 4.0))
    e = math_n(N, L, "ADD", e, glow.outputs[0])
    L.new(e, b.inputs["Emission Strength"]); b.inputs["Emission Color"].default_value = (*(pulse_col or col), 1)
    return m

def mat_value(m, name, f, v):
    n = m.node_tree.nodes[name]; n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)

# ======================================================================
# RENTGEN (shaffof tana) materiali
# ======================================================================
def xray_material(name="xray", col=(0.35, 0.75, 1.0), strength=1.2, base=0.03):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = math_n(N, L, "POWER", lw.outputs["Facing"], 1.6)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    L.new(math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", fac, strength), base), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", fac, 0.7), 0.06, clamp=True), mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m

# ======================================================================
# MIYA
# ======================================================================
def build_brain(name, parent=None, size=0.15):
    root = empty(name, (0, 0, 0), parent)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.85, 0.45, 0.5, 1); b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Coat Weight"].default_value = 0.5
    glow = N.new("ShaderNodeValue"); glow.name = "glow"; glow.outputs[0].default_value = 0.0
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    fl = math_n(N, L, "POWER", nz.outputs["Fac"], 4.0)
    L.new(math_n(N, L, "MULTIPLY", math_n(N, L, "ADD", fl, 0.15), glow.outputs[0]), b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (1.0, 0.55, 0.65, 1)
    tex = bpy.data.textures.new(name + "_gyri", "VORONOI"); tex.distance_metric = "DISTANCE"
    tex.noise_scale = 0.11; tex.color_mode = "INTENSITY"; tex.weight_1 = 1.0; tex.weight_2 = -1.0; tex.noise_intensity = 1.0
    tex2 = bpy.data.textures.new(name + "_warp", "DISTORTED_NOISE"); tex2.noise_scale = 0.4; tex2.distortion = 3.0
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=1, location=(sx * 0.27, 0, 0))
        h = bpy.context.object; h.name = f"{name}_hemi{sx}"; h.scale = (0.5, 0.82, 0.55)
        bpy.ops.object.transform_apply(scale=True)
        for v in h.data.vertices:                             # ichki tomoni tekis
            if v.co.x * sx < 0.03: v.co.x = sx * 0.03 + (v.co.x - sx * 0.03) * 0.25
            if v.co.z < -0.15: v.co.z = -0.15 + (v.co.z + 0.15) * 0.6
        s = _vp(h.modifiers.new("s", "SUBSURF")); s.levels = 1; s.render_levels = 2
        d = h.modifiers.new("warp", "DISPLACE"); d.texture = tex2; d.strength = 0.05; d.texture_coords = "LOCAL"
        d = h.modifiers.new("gyri", "DISPLACE"); d.texture = tex; d.strength = 0.07; d.texture_coords = "LOCAL"; d.mid_level = 0.3
        for p in h.data.polygons: p.use_smooth = True
        h.data.materials.append(m); h.parent = root
    # miyacha
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(0, 0.55, -0.38))
    c = bpy.context.object; c.name = name + "_cereb"; c.scale = (0.42, 0.25, 0.18)
    tw = bpy.data.textures.new(name + "_folia", "WOOD"); tw.wood_type = "BANDNOISE"; tw.noise_scale = 0.05; tw.turbulence = 2.0
    d = c.modifiers.new("f", "DISPLACE"); d.texture = tw; d.strength = 0.03; c.modifiers.new("s", "SUBSURF").levels = 1
    for p in c.data.polygons: p.use_smooth = True
    c.data.materials.append(m); c.parent = root
    root.scale = (size, size, size)
    root["mat"] = m.name
    return root, m

# ======================================================================
# TERI KESIMI (bloki)
# ======================================================================
def section_mats():
    def pm(n, col, rough=0.5, sss=0.5, coat=0.0):
        m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.02
        b.inputs["Coat Weight"].default_value = coat
        return m
    epi = pm("sec_epi", (0.86, 0.62, 0.52), 0.45, 0.6, 0.0)
    N = epi.node_tree.nodes; L = epi.node_tree.links; b = N["Principled BSDF"]
    tint = N.new("ShaderNodeValue"); tint.name = "blue"; tint.outputs[0].default_value = 0.0
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(tint.outputs[0], mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.82, 0.55, 0.45, 1); mx.inputs[7].default_value = (0.55, 0.7, 0.9, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 9.0
    wv.inputs["Distortion"].default_value = 3.0; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(wv.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    wetv = N.new("ShaderNodeValue"); wetv.name = "wet"; wetv.outputs[0].default_value = 0.3
    L.new(wetv.outputs[0], b.inputs["Coat Weight"])
    der = pm("sec_derm", (0.78, 0.36, 0.34), 0.55, 0.5)
    N = der.node_tree.nodes; L = der.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = 6.0; wv.inputs["Distortion"].default_value = 12.0; wv.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.62, 0.22, 0.22, 1); cr.color_ramp.elements[1].color = (0.9, 0.5, 0.46, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(wv.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    fat = pm("sec_fat", (0.95, 0.78, 0.38), 0.3, 0.7, 0.4)
    N = fat.node_tree.nodes; L = fat.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 7.0
    vo.feature = "SMOOTH_F1"; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; L.new(vo.outputs["Distance"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    cr = N.new("ShaderNodeValToRGB"); L.new(vo.outputs["Distance"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (1.0, 0.85, 0.45, 1); cr.color_ramp.elements[1].color = (0.8, 0.55, 0.25, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    return epi, der, fat

_SEC = None
def section_group():
    """Teri bloki uchun GN: Fold (burma kuchi), Swell (shish), Sink (ostki hajm kamayishi).
    Blok mahalliy koordinatada: x,y in [-1,1], z: 0 (pastki) .. 1 (yuqori teri)."""
    global _SEC
    if _SEC: return _SEC
    ng = bpy.data.node_groups.new("SkinBlock", "GeometryNodeTree"); I = ng.interface
    I.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm in ("Fold", "Swell", "Sink", "Layer"):
        I.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
    I.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sep.inputs[0])
    x, y, z = sep.outputs
    # z ga proporsional: ostki qatlamlar kamroq siljiydi; Layer = qatlam tepasining nisbiy balandligi (0..1)
    zr = math_n(N, L, "DIVIDE", z, 1.0)
    # shish/cho'kish: tepaga yaqin nuqtalar ko'proq ko'tariladi
    dz = math_n(N, L, "MULTIPLY", zr, math_n(N, L, "SUBTRACT", math_n(N, L, "MULTIPLY", gi.outputs["Swell"], 0.18),
                                             math_n(N, L, "MULTIPLY", gi.outputs["Sink"], 0.12)))
    # burmalar: x bo'ylab egri-bugri to'lqin, faqat yuqori qatlamlarda (z>0.6)
    comb = N.new("ShaderNodeCombineXYZ"); L.new(x, comb.inputs[0]); L.new(y, comb.inputs[1])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"; wv.inputs["Scale"].default_value = 3.4
    wv.inputs["Distortion"].default_value = 3.0; wv.inputs["Detail Scale"].default_value = 0.8
    L.new(comb.outputs[0], wv.inputs["Vector"])
    h = math_n(N, L, "SUBTRACT", math_n(N, L, "POWER", wv.outputs["Fac"], 0.5), 0.75)
    mzr = N.new("ShaderNodeMapRange"); L.new(z, mzr.inputs["Value"]); mzr.inputs["From Min"].default_value = 0.55
    mzr.inputs["From Max"].default_value = 1.0; mzr.interpolation_type = "SMOOTHSTEP"
    fold = math_n(N, L, "MULTIPLY", math_n(N, L, "MULTIPLY", h, mzr.outputs[0]), math_n(N, L, "MULTIPLY", gi.outputs["Fold"], 0.055))
    off = N.new("ShaderNodeCombineXYZ"); L.new(math_n(N, L, "ADD", dz, fold), off.inputs[2])
    sp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs["Geometry"], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
    L.new(sp.outputs[0], go.inputs["Geometry"])
    _SEC = ng
    return ng

def build_section(name, loc, size=(2.0, 1.4), parent=None):
    """teri bloki: epidermis (0.9..1.0), dermis (0.45..0.9), yog' qatlami (0..0.45). Hammasi bitta GN guruhi bilan siljiydi."""
    root = empty(name, loc, parent)
    epi, der, fat = section_mats()
    W, D = size
    parts = {}
    for nm, z0, z1, m, cuts in (("fat", 0.0, 0.45, fat, 6), ("derm", 0.45, 0.9, der, 8), ("epi", 0.9, 1.0, epi, 4)):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=180, size=1)
        o = bpy.context.object; o.name = f"{name}_{nm}"
        for v in o.data.vertices: v.co.x *= W; v.co.y *= D; v.co.z = z1
        # qalinlik: solidify (pastga)
        so = _vp(o.modifiers.new("th", "SOLIDIFY")); so.thickness = (z1 - z0); so.offset = -1.0; so.use_even_offset = False
        gn = _vp(o.modifiers.new("blk", "NODES")); gn.node_group = section_group()
        o.data.materials.append(m); o.parent = root
        for p in o.data.polygons: p.use_smooth = True
        parts[nm] = o
    # yog' qatlami ustki yuzasi bo'rtiq (lobula) — bump yetarli
    ids = {it.name: it.identifier for it in section_group().interface.items_tree if getattr(it, "in_out", "") == "INPUT"}
    root["ids"] = ids
    return root, parts, (epi, der, fat)

def section_key(parts, f, fold=None, swell=None, sink=None):
    ids = parts["epi"].parent["ids"]
    for o in parts.values():
        for nm, v in (("Fold", fold), ("Swell", swell), ("Sink", sink)):
            if v is None: continue
            key_mod(o, "blk", ids[nm], f, v)

def section_z(fold, swell, sink, x, y, z):
    """section_group bilan bir xil siljish (taxminiy, burmasiz) — tomirlarni joylash uchun"""
    return z + z * (swell * 0.18 - sink * 0.12)
