# "Qaynoq choy" videosi uchun procedural modellar: piyola va choynak (paxta naqshi), qaynoq choy, bug' (hajmli),
# qizilo'ngach kesimi (qatlamlar), o'sma, termometr, DNK spirali, hujayralar maydoni, qizilo'ngach ichi (tunnel).
import bpy, bmesh, math, random
from mathutils import Vector

R = math.radians
sc = lambda: bpy.context.scene
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

def link(o, parent=None):
    sc().collection.objects.link(o)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); e.location = loc; e.empty_display_size = 0.01
    return link(e, parent)

def mesh_obj(name, bm, m, parent=None, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o, parent)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if m: me.materials.append(m)
    return o

def nodes(m):
    return m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]

def value(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]

def mth(N, L, op, a, b=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0]

def base_mat(name, col, rough=0.5, coat=0.0, sss=0.0, sss_scale=0.01, metal=0.0, trans=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Scale"].default_value = sss_scale; b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["Alpha"].default_value = alpha
    return m

def emit_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    L.new(e.outputs[0], N["Material Output"].inputs[0])
    return m

# ----------------------------------------------------------------------
# aylanma jism (lathe): profil [(r, z)], ichi bo'sh idish uchun ichki profil ham
# ----------------------------------------------------------------------
def lathe(name, prof, m, parent=None, segs=64, close_bottom=True):
    bm = bmesh.new(); rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / segs), r * math.sin(2 * math.pi * j / segs), z)) for j in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for j in range(segs):
            bm.faces.new((a[j], a[(j + 1) % segs], b[(j + 1) % segs], b[j]))
    if close_bottom:
        c = bm.verts.new((0, 0, prof[0][1]))
        for j in range(segs): bm.faces.new((c, rings[0][(j + 1) % segs], rings[0][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m, parent)

def paxta_mat(name):
    """O'zbek "paxta" naqshi: oq chinni + ko'k paxta guli bandlari (oddiylashtirilgan)"""
    m = base_mat(name, (0.95, 0.95, 0.93), 0.12, coat=0.8)
    N, L, b = nodes(m)
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    ang = mth(N, L, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
    z = sep.outputs["Z"]
    # z bo'yicha band (piyola o'rtasi), ichida burchak bo'yicha takrorlanuvchi gul
    cell = mth(N, L, "SINE", mth(N, L, "MULTIPLY", ang, 8.0))
    zn = N.new("ShaderNodeMapRange"); L.new(z, zn.inputs["Value"])
    zn.inputs["From Min"].default_value = 0.0; zn.inputs["From Max"].default_value = 1.0
    zn.inputs["To Min"].default_value = 0.0; zn.inputs["To Max"].default_value = 1.0
    zc = value(m, "zc", 0.025); zw = value(m, "zw", 0.012)
    dz = mth(N, L, "ABSOLUTE", mth(N, L, "SUBTRACT", z, zc))
    band = mth(N, L, "LESS_THAN", dz, zw)
    petal = mth(N, L, "GREATER_THAN", mth(N, L, "ADD", mth(N, L, "MULTIPLY", cell, 0.5),
                                         mth(N, L, "MULTIPLY", mth(N, L, "DIVIDE", dz, zw), -1.0)), -0.35)
    stripe = mth(N, L, "LESS_THAN", mth(N, L, "ABSOLUTE", mth(N, L, "SUBTRACT", dz, mth(N, L, "MULTIPLY", zw, 1.35))), 0.0012)
    f = mth(N, L, "MAXIMUM", mth(N, L, "MULTIPLY", band, petal), stripe)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(f, mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.95, 0.95, 0.93, 1); mx.inputs[7].default_value = (0.04, 0.12, 0.55, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    return m

def tea_mat(name, glow=0.0):
    """achchiq qora choy: to'q qizil-jigarrang, yaltiroq; 'boil' qiymati qaynash to'lqinini siljitadi"""
    m = base_mat(name, (0.16, 0.035, 0.008), 0.04, coat=1.0)
    N, L, b = nodes(m)
    b.inputs["Coat Roughness"].default_value = 0.02
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 90.0; nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], nz.inputs["Vector"]); L.new(value(m, "boil", 0.0), nz.inputs["W"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.002
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (1.0, 0.35, 0.05, 1); b.inputs["Emission Strength"].default_value = glow
    return m

def piyola(name, parent=None, mat=None, tea=None, scale=1.0, tea_level=0.8):
    """o'zbek piyolasi: balandligi ~5.5 sm, og'zi ~9.5 sm. Ob'ekt markazi tagida, og'zi +Z."""
    s = scale
    out = [(0.0, 0.0), (0.021, 0.0), (0.022, 0.006), (0.019, 0.007), (0.024, 0.011), (0.034, 0.02), (0.042, 0.034),
           (0.046, 0.047), (0.0475, 0.055)]
    inn = [(0.0453, 0.055), (0.0438, 0.047), (0.0398, 0.034), (0.031, 0.021), (0.019, 0.013), (0.0, 0.011)]
    prof = [(r * s, z * s) for r, z in out + inn]
    bm = bmesh.new(); segs = 64; rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / segs), r * math.sin(2 * math.pi * j / segs), z)) for j in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for j in range(segs): bm.faces.new((a[j], a[(j + 1) % segs], b[(j + 1) % segs], b[j]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, mat or paxta_mat(name + "_m"), parent)
    o.data.materials[0].node_tree.nodes["zc"].outputs[0].default_value = 0.036 * s
    o.data.materials[0].node_tree.nodes["zw"].outputs[0].default_value = 0.008 * s
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 1
    tsurf = None
    if tea:
        z = (0.011 + (0.055 - 0.011) * tea_level) * s
        # ichki profil bo'yicha shu balandlikdagi radius
        r = 0.0
        for (r1, z1), (r2, z2) in zip(inn, inn[1:]):
            if z2 * s <= z <= z1 * s: r = (r2 + (r1 - r2) * (z - z2 * s) / ((z1 - z2) * s)) * s; break
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=r * 0.998, fill_type="NGON", location=(0, 0, 0))
        tsurf = bpy.context.object; tsurf.name = name + "_tea"; tsurf.data.materials.append(tea)
        tsurf.parent = o; tsurf.location = (0, 0, z)
    return o, tsurf

def choynak(name, parent=None, mat=None):
    """o'zbek choynagi (~1 l): tana, jo'mrak, dasta, qopqoq. Markazi tagida, jo'mrak +X tomonda."""
    m = mat or paxta_mat(name + "_m")
    m.node_tree.nodes["zc"].outputs[0].default_value = 0.075; m.node_tree.nodes["zw"].outputs[0].default_value = 0.014
    root = empty(name, (0, 0, 0), parent)
    body = lathe(name + "_body", [(0.045, 0.0), (0.05, 0.004), (0.07, 0.03), (0.082, 0.065), (0.078, 0.1), (0.062, 0.125),
                                  (0.045, 0.135), (0.044, 0.14)], m, root)
    body.modifiers.new("sub", "SUBSURF").render_levels = 1
    lid = lathe(name + "_lid", [(0.047, 0.138), (0.04, 0.152), (0.02, 0.158), (0.008, 0.16), (0.012, 0.172), (0.0, 0.176)], m, root,
                close_bottom=False)
    # jo'mrak va dasta (egri quvur)
    def ctube(nm, pts, r0, r1):
        cu = bpy.data.curves.new(nm, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 4
        cu.use_fill_caps = True; sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            bp = sp.bezier_points[i]; bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
            bp.radius = r0 + (r1 - r0) * i / (len(pts) - 1)
        o = bpy.data.objects.new(nm, cu); link(o, root); cu.materials.append(m); return o
    ctube(name + "_spout", [(0.06, 0, 0.04), (0.105, 0, 0.075), (0.13, 0, 0.12), (0.15, 0, 0.142)], 0.016, 0.0065)
    ctube(name + "_handle", [(-0.07, 0, 0.11), (-0.11, 0, 0.11), (-0.12, 0, 0.06), (-0.075, 0, 0.03)], 0.007, 0.007)
    return root, (0.152, 0, 0.143)                                        # jo'mrak uchi (choynak koordinatasida)

# ----------------------------------------------------------------------
# BUG' (hajmli): 4D shovqin, tepaga siljiydi, balandlik bo'yicha so'nadi
# ----------------------------------------------------------------------
def steam(name, loc, radius, height, parent=None, density=6.0, speed=1.0, seed=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=height, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    for v in o.data.vertices: v.co.z += height / 2
    o.location = loc
    if parent: o.parent = parent
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); out = N["Material Output"]
    vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.95, 0.95, 0.95, 1)
    vol.inputs["Anisotropy"].default_value = 0.3
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    # koordinata: z bo'ylab vaqt bilan pastga siljitiladi (bug' tepaga ko'tariladi), z ga qarab burilish
    t = value(m, "t", 0.0)
    zt = mth(N, L, "SUBTRACT", sep.outputs["Z"], mth(N, L, "MULTIPLY", t, 0.04 * speed))
    cx = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs["X"], cx.inputs[0]); L.new(sep.outputs["Y"], cx.inputs[1]); L.new(zt, cx.inputs[2])
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 3.0 / max(radius, 0.01)
    nz.inputs["Detail"].default_value = 4; nz.inputs["Distortion"].default_value = 0.6
    L.new(cx.outputs[0], nz.inputs["Vector"]); L.new(mth(N, L, "ADD", mth(N, L, "MULTIPLY", t, 0.15), seed), nz.inputs["W"])
    d = mth(N, L, "MAXIMUM", mth(N, L, "MULTIPLY", mth(N, L, "SUBTRACT", nz.outputs["Fac"], 0.52), 4.0), 0.0)
    # radial va balandlik so'nishi
    rr = mth(N, L, "SQRT", mth(N, L, "ADD", mth(N, L, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                              mth(N, L, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"])))
    rad = mth(N, L, "SUBTRACT", 1.0, mth(N, L, "DIVIDE", rr, radius), clamp=True)
    hz = mth(N, L, "DIVIDE", sep.outputs["Z"], height)
    hf = mth(N, L, "MULTIPLY", mth(N, L, "MINIMUM", mth(N, L, "MULTIPLY", hz, 8.0), 1.0),
             mth(N, L, "SUBTRACT", 1.0, hz, clamp=True))
    dens = mth(N, L, "MULTIPLY", mth(N, L, "MULTIPLY", mth(N, L, "MULTIPLY", d, rad), hf), value(m, "dens", density))
    L.new(dens, vol.inputs["Density"]); L.new(vol.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    return o, m

def time_driver(m, name, mul=1.0 / 24.0):
    """qiymat = kadr * mul (bug', qaynash uchun uzluksiz vaqt)"""
    d = m.node_tree.nodes[name].outputs[0].driver_add("default_value").driver
    d.type = "SCRIPTED"; d.expression = f"frame*{mul}"

# ----------------------------------------------------------------------
# QIZILO'NGACH KESIMI: o'q Z bo'ylab, -Y tomoni kesib ochilgan (kamera -Y dan qaraydi)
# ----------------------------------------------------------------------
def shell(name, r_in, r_out, a0, a1, z0, z1, m, parent=None, na=96, nz=24):
    """r_in(a, z), r_out(a, z) — sektor qatlam (yopiq jism). a: -Y dan soat bo'yicha burchak."""
    bm = bmesh.new()
    def P(r, a, z): return (r * math.sin(a), -r * math.cos(a), z)
    A = [a0 + (a1 - a0) * i / na for i in range(na + 1)]; Z = [z0 + (z1 - z0) * k / nz for k in range(nz + 1)]
    inner = [[bm.verts.new(P(r_in(a, z), a, z)) for a in A] for z in Z]
    outer = [[bm.verts.new(P(r_out(a, z), a, z)) for a in A] for z in Z]
    for k in range(nz):
        for i in range(na):
            bm.faces.new((inner[k][i], inner[k + 1][i], inner[k + 1][i + 1], inner[k][i + 1]))
            bm.faces.new((outer[k][i], outer[k][i + 1], outer[k + 1][i + 1], outer[k + 1][i]))
    for k in range(nz):                                                  # kesim yuzalari (burchak chetlari)
        bm.faces.new((inner[k][0], outer[k][0], outer[k + 1][0], inner[k + 1][0]))
        bm.faces.new((inner[k][na], inner[k + 1][na], outer[k + 1][na], outer[k][na]))
    for i in range(na):                                                  # tepa va past
        bm.faces.new((inner[0][i], inner[0][i + 1], outer[0][i + 1], outer[0][i]))
        bm.faces.new((inner[nz][i], outer[nz][i], outer[nz][i + 1], inner[nz][i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m, parent)

def tissue_mat(name, c0, c1, scale=8.0, rough=0.35, coat=0.5, sss=0.3, wave=None, bump=0.3, glow_col=None):
    m = base_mat(name, c0, rough, coat=coat, sss=sss, sss_scale=0.02)
    N, L, b = nodes(m)
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.25)
    tc = N.new("ShaderNodeTexCoord")
    if wave:
        t = N.new("ShaderNodeTexWave"); t.wave_type = "BANDS"; t.bands_direction = wave; t.inputs["Scale"].default_value = scale
        t.inputs["Distortion"].default_value = 3.0; t.inputs["Detail"].default_value = 3; fac = t.outputs["Fac"]
    else:
        t = N.new("ShaderNodeTexNoise"); t.inputs["Scale"].default_value = scale; t.inputs["Detail"].default_value = 6; fac = t.outputs["Fac"]
    L.new(tc.outputs["Object"], t.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(fac, cr.inputs[0])
    cr.color_ramp.elements[0].color = (*c0, 1); cr.color_ramp.elements[1].color = (*c1, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
    L.new(fac, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (*(glow_col or c1), 1)
    L.new(value(m, "glow", 0.0), b.inputs["Emission Strength"])
    return m

def esophagus_section(name, parent, L_=2.4, a0=R(48), a1=R(312)):
    """qatlamlar (ichkaridan): shilliq qavat (yupqa, pushti, burmali), shilliq osti, aylana va bo'ylama mushak, tashqi parda"""
    mats = dict(
        muc=tissue_mat(name + "_muc", (0.85, 0.32, 0.36), (0.98, 0.55, 0.55), 14.0, 0.18, coat=1.0, sss=0.6, glow_col=(1.0, 0.35, 0.4)),
        sub=tissue_mat(name + "_sub", (0.93, 0.78, 0.66), (0.98, 0.88, 0.75), 6.0, 0.45, coat=0.2, sss=0.4),
        circ=tissue_mat(name + "_circ", (0.45, 0.05, 0.06), (0.72, 0.14, 0.13), 22.0, 0.4, coat=0.3, sss=0.2, wave="Z", bump=0.5),
        lon=tissue_mat(name + "_lon", (0.5, 0.07, 0.07), (0.78, 0.2, 0.17), 18.0, 0.4, coat=0.3, sss=0.2, wave="X", bump=0.5),
        adv=tissue_mat(name + "_adv", (0.9, 0.8, 0.72), (0.95, 0.88, 0.8), 8.0, 0.5, coat=0.1, sss=0.3),
    )
    folds = lambda a, z: 0.5 + 0.07 * math.sin(7 * a + 0.4 * math.sin(z * 2.0)) + 0.02 * math.sin(17 * a + z * 3)
    layers = [("muc", folds, lambda a, z: 0.6), ("sub", lambda a, z: 0.6, lambda a, z: 0.76),
              ("circ", lambda a, z: 0.76, lambda a, z: 0.95), ("lon", lambda a, z: 0.95, lambda a, z: 1.08),
              ("adv", lambda a, z: 1.08, lambda a, z: 1.11)]
    objs = {}
    for i, (k, ri, ro) in enumerate(layers):
        # har tashqi qatlam kesim chetida biroz ortda (zinapoya) — qatlamlar aniq ko'rinsin
        d = R(3.0) * i
        objs[k] = shell(f"{name}_{k}", ri, ro, a0 + d, a1 - d, -L_ / 2 + 0.03 * i, L_ / 2 - 0.03 * i, mats[k], parent)
    return objs, mats

def tumor(name, parent, r=0.3):
    m = base_mat(name + "_m", (0.32, 0.03, 0.06), 0.3, coat=0.8, sss=0.4, sss_scale=0.05)
    N, L, b = nodes(m)
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 6.0
    vo.feature = "DISTANCE_TO_EDGE"; L.new(tc.outputs["Object"], vo.inputs[0])
    vein = mth(N, L, "LESS_THAN", vo.outputs["Distance"], 0.04)
    cr = N.new("ShaderNodeMix"); cr.data_type = "RGBA"; L.new(vein, cr.inputs["Factor"])
    cr.inputs[6].default_value = (0.3, 0.03, 0.07, 1); cr.inputs[7].default_value = (0.9, 0.1, 0.08, 1)
    L.new(cr.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (1.0, 0.08, 0.05, 1)
    L.new(mth(N, L, "MULTIPLY", vein, value(m, "glow", 0.0)), b.inputs["Emission Strength"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 12; L.new(tc.outputs["Object"], nz.inputs[0])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=r, location=(0, 0, 0)); o = bpy.context.object; o.name = name
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(m)
    tx = bpy.data.textures.new(name + "_t", "CLOUDS"); tx.noise_scale = r * 0.45; tx.noise_depth = 3
    d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = r * 0.55; d.mid_level = 0.5
    tx2 = bpy.data.textures.new(name + "_t2", "CLOUDS"); tx2.noise_scale = r * 0.12
    d2 = o.modifiers.new("d2", "DISPLACE"); d2.texture = tx2; d2.strength = r * 0.12
    if parent: o.parent = parent
    return o, m

# ----------------------------------------------------------------------
# TERMOMETR
# ----------------------------------------------------------------------
def text(name, s, size, m, parent=None, loc=(0, 0, 0), rot=(90, 0, 0), extrude=0.02):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = s; cu.size = size; cu.extrude = extrude
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.bevel_depth = extrude * 0.15
    try: cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    except Exception: pass
    o = bpy.data.objects.new(name, cu); link(o, parent); o.location = loc; o.rotation_euler = [R(a) for a in rot]
    cu.materials.append(m); return o

def thermometer(name, parent):
    glass = base_mat(name + "_glass", (0.95, 0.98, 1.0), 0.02, trans=1.0)
    red = base_mat(name + "_red", (0.85, 0.02, 0.02), 0.15, coat=0.5)
    nb = red.node_tree.nodes["Principled BSDF"]; nb.inputs["Emission Color"].default_value = (1.0, 0.08, 0.03, 1)
    red.node_tree.links.new(value(red, "glow", 0.3), nb.inputs["Emission Strength"])
    white = base_mat(name + "_scale", (0.9, 0.9, 0.88), 0.4)
    dark = base_mat(name + "_tick", (0.02, 0.02, 0.025), 0.4)
    root = empty(name, (0, 0, 0), parent)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.07, depth=2.6, location=(0, 0, 1.3)); g = bpy.context.object
    g.name = name + "_tube"; g.data.materials.append(glass); g.parent = root
    for p in g.data.polygons: p.use_smooth = True
    bv = g.modifiers.new("bv", "BEVEL"); bv.width = 0.03; bv.segments = 6
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.16, location=(0, 0, 0)); bulb = bpy.context.object
    bulb.name = name + "_bulb"; bulb.data.materials.append(red); bulb.parent = root
    for p in bulb.data.polygons: p.use_smooth = True
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.19, location=(0, 0, 0)); gb = bpy.context.object
    gb.name = name + "_gbulb"; gb.data.materials.append(glass); gb.parent = root
    for p in gb.data.polygons: p.use_smooth = True
    # qizil ustun: origin pastda, scale z animatsiya
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.03, depth=1.0, location=(0, 0, 0)); col = bpy.context.object
    for v in col.data.vertices: v.co.z += 0.5
    col.name = name + "_col"; col.data.materials.append(red); col.parent = root; col.location = (0, 0, 0.1)
    # shkala taxtasi (orqada) va chiziqlar: 0..100 °C, z 0.3..2.4
    bpy.ops.mesh.primitive_cube_add(location=(0, 0.11, 1.35)); bd = bpy.context.object; bd.name = name + "_board"
    bd.scale = (0.22, 0.02, 1.2); bd.data.materials.append(white); bd.parent = root
    bvb = bd.modifiers.new("bv", "BEVEL"); bvb.width = 0.03; bvb.segments = 4
    def zt(c): return 0.3 + 2.1 * c / 100.0
    for c in range(0, 101, 5):
        w = 0.16 if c % 10 == 0 else 0.09
        bpy.ops.mesh.primitive_cube_add(location=(-0.1 - w / 2 + 0.02, 0.085, zt(c))); t = bpy.context.object
        t.scale = (w / 2, 0.005, 0.006); t.data.materials.append(dark if c != 65 else red); t.parent = root
        if c % 20 == 0:
            text(f"{name}_n{c}", str(c), 0.09, dark, root, loc=(0.14, 0.085, zt(c)), rot=(90, 0, 0), extrude=0.004)
    # 65 belgisi
    bpy.ops.mesh.primitive_cube_add(location=(0, 0.085, zt(65))); mk = bpy.context.object; mk.scale = (0.2, 0.004, 0.008)
    mk.data.materials.append(red); mk.parent = root
    return root, col, red, zt

# ----------------------------------------------------------------------
# DNK spirali (o'q Z), juftliklar soni n; xato juftlik indeksi
# ----------------------------------------------------------------------
def dna(name, parent, n=40, r=0.32, rise=0.11, turn=10.5):
    root = empty(name, (0, 0, 0), parent)
    bb = base_mat(name + "_bb", (0.15, 0.45, 0.95), 0.25, coat=0.6, sss=0.2)
    bbn = bb.node_tree.nodes["Principled BSDF"]; bbn.inputs["Emission Color"].default_value = (0.2, 0.5, 1.0, 1)
    bbn.inputs["Emission Strength"].default_value = 0.6
    cols = [(0.95, 0.75, 0.1), (0.15, 0.8, 0.35), (0.85, 0.3, 0.75), (0.2, 0.75, 0.9)]
    bmats = []
    for i, c in enumerate(cols):
        mm = base_mat(f"{name}_b{i}", c, 0.3, coat=0.5); nb = mm.node_tree.nodes["Principled BSDF"]
        nb.inputs["Emission Color"].default_value = (*c, 1); nb.inputs["Emission Strength"].default_value = 0.5
        bmats.append(mm)
    err = base_mat(name + "_err", (0.9, 0.03, 0.02), 0.3, coat=0.5); en = err.node_tree.nodes["Principled BSDF"]
    en.inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1)
    err.node_tree.links.new(value(err, "glow", 0.5), en.inputs["Emission Strength"])
    pts = [[], []]
    for i in range(n * 4 + 1):
        t = i / 4.0; a = 2 * math.pi * t / turn
        for s in (0, 1):
            aa = a + (0 if s == 0 else math.pi * 0.8)
            pts[s].append((r * math.cos(aa), r * math.sin(aa), t * rise))
    def strand(nm, P):
        cu = bpy.data.curves.new(nm, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.045; cu.bevel_resolution = 4
        cu.use_fill_caps = True; sp = cu.splines.new("NURBS"); sp.points.add(len(P) - 1)
        for i, p in enumerate(P): sp.points[i].co = (*p, 1)
        sp.use_endpoint_u = True; sp.order_u = 3; cu.resolution_u = 6
        o = bpy.data.objects.new(nm, cu); link(o, root); cu.materials.append(bb); return o
    strand(name + "_s0", pts[0]); strand(name + "_s1", pts[1])
    rungs = []
    for i in range(n):
        a = 2 * math.pi * i / turn; z = i * rise
        p0 = Vector((r * math.cos(a), r * math.sin(a), z)); p1 = Vector((r * math.cos(a + math.pi * 0.8), r * math.sin(a + math.pi * 0.8), z))
        mid = (p0 + p1) / 2; k = random.Random(i).randrange(4)
        halves = []
        for j, (pa, mi) in enumerate(((p0, k), (p1, (k + 2) % 4))):
            d = mid - pa; ln = d.length
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.035, depth=ln * 0.96, location=(0, 0, 0)); c = bpy.context.object
            c.name = f"{name}_r{i}_{j}"; c.data.materials.append(bmats[mi]); c.parent = root
            c.location = pa + d / 2; c.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
            for p in c.data.polygons: p.use_smooth = True
            halves.append(c)
        rungs.append(halves)
    return root, rungs, err

# ----------------------------------------------------------------------
# HUJAYRALAR MAYDONI (mikro): olti burchakli zich joylashuv, bitta umumiy mesh (linked)
# hujayra holati Object Color orqali: R = kuyish (0..1), G = yangi hujayra porlashi, B = mutatsiya
# ----------------------------------------------------------------------
def cell_mat(name):
    m = base_mat(name, (0.95, 0.45, 0.5), 0.3, coat=0.9, sss=0.7, sss_scale=0.05)
    N, L, b = nodes(m)
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.4); b.inputs["Coat Roughness"].default_value = 0.08
    oi = N.new("ShaderNodeObjectInfo"); sp = N.new("ShaderNodeSeparateColor"); L.new(oi.outputs["Color"], sp.inputs[0])
    burn = sp.outputs[0]; fresh = sp.outputs[1]; mut = sp.outputs[2]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 25.0
    L.new(tc.outputs["Object"], nz.inputs[0])
    # yadro: hujayra markazida to'qroq dog' (Object koordinatasi, radius 1 sfera)
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(tc.outputs["Object"], ln.inputs[0])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    rxy = mth(N, L, "SQRT", mth(N, L, "ADD", mth(N, L, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                               mth(N, L, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"])))
    nuc = mth(N, L, "LESS_THAN", mth(N, L, "ADD", rxy, mth(N, L, "MULTIPLY", nz.outputs["Fac"], 0.12)), 0.36)
    pink = N.new("ShaderNodeMix"); pink.data_type = "RGBA"; L.new(nuc, pink.inputs["Factor"])
    pink.inputs[6].default_value = (0.95, 0.5, 0.55, 1); pink.inputs[7].default_value = (0.45, 0.12, 0.38, 1)
    mutc = N.new("ShaderNodeMix"); mutc.data_type = "RGBA"; L.new(mut, mutc.inputs["Factor"])
    L.new(pink.outputs[2], mutc.inputs[6]); mutc.inputs[7].default_value = (0.35, 0.02, 0.1, 1)
    char = N.new("ShaderNodeMix"); char.data_type = "RGBA"; L.new(burn, char.inputs["Factor"])
    L.new(mutc.outputs[2], char.inputs[6])
    chc = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], chc.inputs[0])
    chc.color_ramp.elements[0].color = (0.01, 0.006, 0.004, 1); chc.color_ramp.elements[1].color = (0.12, 0.05, 0.02, 1)
    L.new(chc.outputs[0], char.inputs[7])
    L.new(char.outputs[2], b.inputs["Base Color"])
    L.new(mth(N, L, "SUBTRACT", 0.7, mth(N, L, "MULTIPLY", burn, 0.7)), b.inputs["Subsurface Weight"])
    L.new(mth(N, L, "SUBTRACT", 0.9, mth(N, L, "MULTIPLY", burn, 0.85)), b.inputs["Coat Weight"])
    # emissiya: kuyish o'rtasida to'q sariq (lava cheti), yangi hujayra — oq-pushti, mutatsiya — qizil
    e_burn = mth(N, L, "MULTIPLY", mth(N, L, "MULTIPLY", burn, mth(N, L, "SUBTRACT", 1.0, burn)), 4.0)
    e_burn = mth(N, L, "MULTIPLY", e_burn, mth(N, L, "GREATER_THAN", nz.outputs["Fac"], 0.45))
    ec = N.new("ShaderNodeMix"); ec.data_type = "RGBA"; L.new(mth(N, L, "MINIMUM", mth(N, L, "ADD", fresh, mut), 1.0), ec.inputs["Factor"])
    ec.inputs[6].default_value = (1.0, 0.35, 0.05, 1); ec.inputs[7].default_value = (1.0, 0.45, 0.55, 1)
    L.new(ec.outputs[2], b.inputs["Emission Color"])
    L.new(mth(N, L, "ADD", mth(N, L, "MULTIPLY", e_burn, 6.0), mth(N, L, "ADD", mth(N, L, "MULTIPLY", fresh, 1.5), mth(N, L, "MULTIPLY", mut, 2.0))),
          b.inputs["Emission Strength"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.02
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def cell_field(name, parent, nx=16, ny=16, sp=0.17, seed=3):
    rnd = random.Random(seed); m = cell_mat(name + "_m")
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 0, 0)); proto = bpy.context.object
    proto.name = name + "_proto"
    for p in proto.data.polygons: p.use_smooth = True
    proto.data.materials.append(m)
    bm = bmesh.new(); bm.from_mesh(proto.data)
    for v in bm.verts:                                                   # tepasi gumbaz, tagi tekisroq, yon tomonlari olti burchakka yaqin
        a = math.atan2(v.co.y, v.co.x); k = 1.0 + 0.06 * math.cos(6 * a)
        v.co.x *= k; v.co.y *= k
        if v.co.z < 0: v.co.z *= 0.4
    bm.to_mesh(proto.data); bm.free()
    cells = []
    for j in range(ny):
        for i in range(nx):
            x = (i - nx / 2 + (0.5 if j % 2 else 0)) * sp; y = (j - ny / 2) * sp * 0.866
            c = proto.copy(); c.name = f"{name}_{i}_{j}"; link(c, parent)
            s = sp * 0.56 * rnd.uniform(0.9, 1.08)
            c.location = (x + rnd.uniform(-0.01, 0.01), y + rnd.uniform(-0.01, 0.01), 0.0)
            c.scale = (s, s, s * rnd.uniform(0.55, 0.75)); c.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
            c.color = (0, 0, 0, 1); c["s0"] = tuple(c.scale)
            cells.append(c)
    bpy.data.objects.remove(proto, do_unlink=True)
    return cells, m

def cell_state(c, f, burn=None, fresh=None, mut=None, scale=None):
    col = list(c.color)
    if burn is not None: col[0] = burn
    if fresh is not None: col[1] = fresh
    if mut is not None: col[2] = mut
    c.color = col; c.keyframe_insert("color", frame=f)
    if scale is not None:
        s0 = c["s0"]; c.scale = (s0[0] * scale, s0[1] * scale, s0[2] * scale * (0.6 + 0.4 * (1 - (burn or 0)))); c.keyframe_insert("scale", frame=f)

# ----------------------------------------------------------------------
# QIZILO'NGACH ICHI (tunnel), o'q Z, ichidan ko'rinadi; devor 'wz' dan yuqorida qizaradi (kuyish izi)
# ----------------------------------------------------------------------
def tunnel(name, parent, length=3.0, r=0.16, res=64, rows=90):
    bm = bmesh.new(); grid = []
    for i in range(rows + 1):
        z = length * i / rows; row = []
        for j in range(res):
            a = 2 * math.pi * j / res
            rr = r * (1 + 0.22 * math.sin(6 * a + 0.8 * math.sin(z * 1.7)) + 0.05 * math.sin(14 * a + z * 5) + 0.04 * math.sin(z * 9))
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        grid.append(row)
    for i in range(rows):
        for j in range(res):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][(j + 1) % res], grid[i][(j + 1) % res]))
    m = base_mat(name + "_m", (0.75, 0.25, 0.28), 0.2, coat=1.0, sss=0.5, sss_scale=0.01)
    N, L, b = nodes(m)
    b.inputs["Coat Roughness"].default_value = 0.03; b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18
    nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.55, 0.12, 0.15, 1); cr.color_ramp.elements[1].color = (0.92, 0.45, 0.45, 1)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    burnt = mth(N, L, "MULTIPLY", mth(N, L, "GREATER_THAN", sep.outputs["Z"], value(m, "wz", 99.0)), value(m, "burnamt", 0.8))
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(burnt, mx.inputs["Factor"]); L.new(cr.outputs[0], mx.inputs[6])
    mx.inputs[7].default_value = (0.75, 0.04, 0.03, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (1.0, 0.18, 0.05, 1)
    L.new(mth(N, L, "MULTIPLY", burnt, mth(N, L, "MULTIPLY", nz.outputs["Fac"], 1.5)), b.inputs["Emission Strength"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.inputs["Distance"].default_value = 0.004
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    o = mesh_obj(name, bm, m, parent)
    return o, m

def pulse_mat(name, col, base_emit=1.0, pulse_col=None, width=0.06, trail=1.2, pulse=25.0):
    """egri bo'ylab yuradigan issiq oqim: 'pos' (0..1+), 'glow'; impuls ortida kuchsiz "kuyish izi" (trail)"""
    m = base_mat(name, col, 0.35, coat=0.4, sss=0.3)
    N, L, b = nodes(m)
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"; u = ua.outputs["Fac"]
    pos = value(m, "pos", -1.0); glow = value(m, "glow", base_emit)
    dist = mth(N, L, "ABSOLUTE", mth(N, L, "SUBTRACT", u, pos))
    p = mth(N, L, "POWER", mth(N, L, "SUBTRACT", 1.0, mth(N, L, "DIVIDE", dist, width), clamp=True), 2.0)
    tr = mth(N, L, "MULTIPLY", mth(N, L, "LESS_THAN", u, pos), trail)
    e = mth(N, L, "ADD", mth(N, L, "ADD", mth(N, L, "MULTIPLY", p, pulse), tr), glow)
    L.new(e, b.inputs["Emission Strength"])
    # rang: impuls/iz — to'q sariq, qolgani — pushti
    hot = mth(N, L, "MINIMUM", mth(N, L, "ADD", p, mth(N, L, "MULTIPLY", tr, 0.6)), 1.0)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(hot, mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.95, 0.42, 0.45, 1); mx.inputs[7].default_value = (*(pulse_col or col), 1)
    L.new(mx.outputs[2], b.inputs["Emission Color"])
    return m
