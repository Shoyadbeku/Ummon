# "Tish sug'urilgach jag' suyagi" uchun procedural modellar (o'lchov: 1 birlik = 1 sm, makro sahnalar):
# tish (oziq, kichik oziq, qoziq, kesuvchi), milk va tish qatori (arch), jag' kesimi (milk + g'ovak suyak),
# qisqich (forseps), metall lagan, rentgen jag'i.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import parts as P

R = math.radians
sc = lambda: bpy.context.scene

# ======================================================================
# MATERIALLAR
# ======================================================================
def _pm(name, col, rough=0.4, sss=0.0, coat=0.0, sss_scale=0.05, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = sss_scale
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Metallic"].default_value = metal
    return m

def _noise_col(m, scale, c0, c1, bump=0.0, coord="Object", detail=4.0):
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    L.new(tc.outputs[coord], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (*c0, 1); cr.color_ramp.elements[1].color = (*c1, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    if bump:
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return nz

def enamel_material(name="enamel"):
    m = bpy.data.materials.get(name)
    if m: return m
    m = _pm(name, (0.92, 0.9, 0.82), 0.18, sss=0.35, coat=0.8, sss_scale=0.04)
    m.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.05
    _noise_col(m, 9.0, (0.86, 0.82, 0.7), (0.97, 0.96, 0.9), bump=0.05)
    return m

def dentin_material(name="dentin", blood=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    c0 = (0.78, 0.66, 0.46); c1 = (0.9, 0.8, 0.62)
    if blood: c0 = (0.45, 0.06, 0.05); c1 = (0.75, 0.45, 0.35)
    m = _pm(name, c0, 0.45, sss=0.25, coat=0.3 + blood * 0.6, sss_scale=0.04)
    _noise_col(m, 14.0, c0, c1, bump=0.15)
    return m

def gum_material(name="gum", col=(0.78, 0.33, 0.36)):
    m = bpy.data.materials.get(name)
    if m: return m
    m = _pm(name, col, 0.32, sss=0.8, coat=0.7, sss_scale=0.08)
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.25)
    b.inputs["Coat Roughness"].default_value = 0.08
    _noise_col(m, 6.0, tuple(c * 0.85 for c in col), tuple(min(1, c * 1.12) for c in col), bump=0.08)
    return m

def bone_materials():
    """(cortical, spongy). spongy: 'pores' qiymati (0..1) g'ovaklar hajmi, 'alive' oltin nur, 'sick' qizarish."""
    if bpy.data.materials.get("bone_cort"):
        return bpy.data.materials["bone_cort"], bpy.data.materials["bone_spongy"]
    cort = _pm("bone_cort", (0.88, 0.8, 0.64), 0.5, sss=0.2, coat=0.2, sss_scale=0.05)
    _noise_col(cort, 5.0, (0.8, 0.72, 0.56), (0.93, 0.87, 0.72), bump=0.2)
    sp = bpy.data.materials.new("bone_spongy"); sp.use_nodes = True
    N = sp.node_tree.nodes; L = sp.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.6; b.inputs["Subsurface Weight"].default_value = 0.2
    b.inputs["Subsurface Scale"].default_value = 0.04
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 9.0
    vo.inputs["Randomness"].default_value = 1.0
    wp = N.new("ShaderNodeTexNoise"); wp.inputs["Scale"].default_value = 3.0; L.new(tc.outputs["Object"], wp.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "VECTOR"; mx.inputs["Factor"].default_value = 0.12
    L.new(tc.outputs["Object"], mx.inputs[4]); L.new(wp.outputs["Color"], mx.inputs[5]); L.new(mx.outputs[1], vo.inputs["Vector"])
    pores = N.new("ShaderNodeValue"); pores.name = "pores"; pores.outputs[0].default_value = 0.0
    # tirgak (trabekula) qalinligi: pores oshsa ingichkalashadi
    thick = P.math_n(N, L, "SUBTRACT", 0.11, P.math_n(N, L, "MULTIPLY", pores.outputs[0], 0.085))
    hole = P.math_n(N, L, "GREATER_THAN", vo.outputs["Distance"], thick)      # 1 = teshik
    soft = N.new("ShaderNodeMapRange"); L.new(vo.outputs["Distance"], soft.inputs["Value"])
    L.new(thick, soft.inputs["From Min"]); L.new(P.math_n(N, L, "ADD", thick, 0.03), soft.inputs["From Max"])
    cA = N.new("ShaderNodeMix"); cA.data_type = "RGBA"; L.new(soft.outputs[0], cA.inputs["Factor"])
    cA.inputs[6].default_value = (0.9, 0.82, 0.66, 1); cA.inputs[7].default_value = (0.45, 0.12, 0.08, 1)
    sick = N.new("ShaderNodeValue"); sick.name = "sick"; sick.outputs[0].default_value = 0.0
    cB = N.new("ShaderNodeMix"); cB.data_type = "RGBA"; L.new(sick.outputs[0], cB.inputs["Factor"])
    L.new(cA.outputs[2], cB.inputs[6]); cB.inputs[7].default_value = (0.55, 0.2, 0.14, 1)
    L.new(cB.outputs[2], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.7; bp.invert = True
    L.new(soft.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    alive = N.new("ShaderNodeValue"); alive.name = "alive"; alive.outputs[0].default_value = 0.0
    em = P.math_n(N, L, "MULTIPLY", P.math_n(N, L, "SUBTRACT", 1.0, soft.outputs[0]), alive.outputs[0])
    L.new(em, b.inputs["Emission Strength"]); b.inputs["Emission Color"].default_value = (1.0, 0.72, 0.25, 1)
    L.new(hole, b.inputs["Roughness"])
    return cort, sp

def glow_material(name, col, strength=8.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    st = N.new("ShaderNodeValue"); st.name = "glow"; st.outputs[0].default_value = strength
    L.new(st.outputs[0], em.inputs["Strength"]); L.new(em.outputs[0], out.inputs[0])
    return m

def soft_glow_material(name, col, strength=3.0):
    """Chetlari shaffof yumshoq nur (og'riq, to'lqin)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fac = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"]), 2.0)
    st = N.new("ShaderNodeValue"); st.name = "glow"; st.outputs[0].default_value = strength
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    L.new(P.math_n(N, L, "MULTIPLY", fac, st.outputs[0]), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], out.inputs[0])
    return m

def steel_material(name="steel"):
    m = bpy.data.materials.get(name)
    if m: return m
    m = _pm(name, (0.8, 0.8, 0.82), 0.18, metal=1.0)
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 400.0
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 0.01)
    L.new(tc.outputs["Object"], mp.inputs[0]); L.new(mp.outputs[0], nz.inputs["Vector"])
    L.new(P.math_n(N, L, "ADD", P.math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.2), 0.1), b.inputs["Roughness"])
    b.inputs["Anisotropic"].default_value = 0.6
    return m

# ======================================================================
# TISH
# ======================================================================
SPEC = {  # kenglik (mezio-distal x), chuqurlik (y), toj balandligi, ildizlar [(x, uzunlik, radius)]
    "molar":    dict(w=1.05, d=1.0, h=0.72, roots=[(-0.27, 1.35, 0.23), (0.27, 1.25, 0.22)], cusp=4),
    "premolar": dict(w=0.72, d=0.82, h=0.8, roots=[(0.0, 1.45, 0.26)], cusp=2),
    "canine":   dict(w=0.75, d=0.78, h=1.0, roots=[(0.0, 1.7, 0.28)], cusp=1),
    "incisor":  dict(w=0.56, d=0.62, h=0.95, roots=[(0.0, 1.3, 0.2)], cusp=0),
}

def _crown_mesh(name, s, upper=False):
    w, d, h = s["w"], s["d"], s["h"]
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.0)
    rnd = random.Random(hash(name) & 0xffff)
    for v in bm.verts:
        nx, ny, nz = v.co
        rr = math.hypot(nx, ny)
        if rr > 1e-6:                                   # superellips kesim (to'rtburchakroq)
            p = 3.0; sq = (abs(nx) ** p + abs(ny) ** p) ** (1 / p); k = rr / sq
            nx *= k; ny *= k
        t = (nz + 1) / 2                               # 0 pastki (bo'yin) .. 1 tepa
        bulge = 1.0 - 0.32 * max(0.0, 0.45 - t) / 0.45 * 1.0 - 0.06 * max(0, t - 0.75) / 0.25
        x = nx * w / 2 * bulge; y = ny * d / 2 * bulge
        if s["cusp"] == 0:                              # kesuvchi: tepaga qarab yupqa tig'
            y *= 1.0 - 0.75 * t ** 1.5
        elif s["cusp"] == 1:                            # qoziq: o'tkir uch
            x *= 1.0 - 0.55 * t ** 2; y *= 1.0 - 0.3 * t ** 2
        z = (t - 0.18) * h
        if t > 0.55 and s["cusp"] >= 2:                 # do'mboqchalar va o'rtadagi ariqcha
            top = (t - 0.55) / 0.45
            if s["cusp"] == 4:
                c = sum(math.exp(-(((x - cx * w) / (0.2 * w)) ** 2 + ((y - cy * d) / (0.22 * d)) ** 2))
                        for cx in (-0.22, 0.22) for cy in (-0.2, 0.2))
            else:
                c = sum(math.exp(-((x / (0.35 * w)) ** 2 + ((y - cy * d) / (0.2 * d)) ** 2)) for cy in (-0.2, 0.2))
            z += (c * 0.16 - 0.1) * h * top ** 0.7
        z += rnd.uniform(-0.004, 0.004)
        v.co = (x, y, z)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me

def _root_mesh(name, x0, L_, r0, bend=0.12):
    bm = bmesh.new(); seg = 20; rings = 16
    rows = []
    for i in range(rings + 1):
        t = i / rings
        r = r0 * (1 - t) ** 0.55 + 0.02
        cx = x0 + bend * t * t * (1 if x0 >= 0 else -1) * 0.6 + (bend * 0.4 * t * t)
        cz = 0.08 - t * L_
        row = [bm.verts.new((cx + r * math.cos(a) * 1.0, r * math.sin(a) * 1.35, cz))
               for a in (2 * math.pi * k / seg for k in range(seg))]
        rows.append(row)
    for i in range(rings):
        for k in range(seg):
            bm.faces.new((rows[i][k], rows[i][(k + 1) % seg], rows[i + 1][(k + 1) % seg], rows[i + 1][k]))
    tip = bm.verts.new((rows[-1][0].co.x - r0 * 0.0 - 0.02, 0, 0.08 - L_ - 0.04))
    tip.co.x = sum(v.co.x for v in rows[-1]) / seg
    for k in range(seg): bm.faces.new((rows[-1][(k + 1) % seg], rows[-1][k], tip))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me

def build_tooth(name, kind="molar", parent=None, root_mat=None, scale=1.0):
    """Ildiz (bo'yin, CEJ) (0,0,0) da; toj +Z, ildizlar -Z. Qaytaradi: root empty (bolalari: toj, ildizlar)."""
    s = SPEC[kind]
    root = P.empty(name, (0, 0, 0), parent)
    cm = _crown_mesh(name + "_crown", s)
    c = bpy.data.objects.new(name + "_crown", cm); P.link(c, root); cm.materials.append(enamel_material())
    sub = P._vp(c.modifiers.new("s", "SUBSURF")); sub.levels = 1; sub.render_levels = 2
    parts = [c]
    for i, (x0, L_, r0) in enumerate(s["roots"]):
        rm = _root_mesh(f"{name}_root{i}", x0 * s["w"] / 1.05 if kind == "molar" else x0, L_, r0)
        o = bpy.data.objects.new(f"{name}_root{i}", rm); P.link(o, root)
        rm.materials.append(root_mat or dentin_material())
        sub = P._vp(o.modifiers.new("s", "SUBSURF")); sub.levels = 1; sub.render_levels = 2
        parts.append(o)
    root.scale = (scale,) * 3
    root["kind"] = kind
    return root, parts

# ======================================================================
# SUPURISH (sweep): yo'l bo'ylab ellips kesim -> mesh
# ======================================================================
def sweep(name, path, prof_w, prof_h, mat, parent=None, segs=24, cap=True, z_flat=None, close=False):
    """path: [(Vector, up Vector)] ; prof_w/prof_h: kenglik/balandlik funksiyasi(t) yoki son."""
    bm = bmesh.new(); rows = []
    n = len(path)
    for i, (p, up) in enumerate(path):
        t = i / (n - 1)
        tan = (path[min(n - 1, i + 1)][0] - path[max(0, i - 1)][0]).normalized()
        side = tan.cross(up).normalized(); upn = side.cross(tan).normalized()
        pw = prof_w(t) if callable(prof_w) else prof_w; ph = prof_h(t) if callable(prof_h) else prof_h
        row = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ca, sa = math.cos(a), math.sin(a)
            sx = math.copysign(abs(ca) ** 0.8, ca); sz = math.copysign(abs(sa) ** 0.8, sa)
            if z_flat is not None and sz > 0: sz *= z_flat
            row.append(bm.verts.new(p + side * sx * pw / 2 + upn * sz * ph / 2))
        rows.append(row)
    for i in range(n - 1):
        for k in range(segs):
            bm.faces.new((rows[i][k], rows[i][(k + 1) % segs], rows[i + 1][(k + 1) % segs], rows[i + 1][k]))
    if cap:
        bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for pl in me.polygons: pl.use_smooth = True
    o = bpy.data.objects.new(name, me); P.link(o, parent); me.materials.append(mat)
    sub = P._vp(o.modifiers.new("s", "SUBSURF")); sub.levels = 1; sub.render_levels = 2
    return o

# ======================================================================
# TISH QATORI (pastki jag', arch)
# ======================================================================
ORDER = ["incisor", "incisor", "canine", "premolar", "premolar", "molar", "molar"]

def arch_points(half_w=2.45, depth=4.3, n=200):
    """U shaklidagi yoy: oldi (0, 0), orqa uchlari (+-half_w, depth). Qaytaradi: [(Vector, s)] (yoy uzunligi)."""
    pts = []
    for i in range(n + 1):
        u = -1 + 2 * i / n
        x = half_w * math.sin(u * math.pi / 2 * 1.0) * (1.0 if abs(u) < 1 else 1)
        y = depth * (abs(u) ** 1.9)
        pts.append(Vector((x, y, 0)))
    s = [0.0]
    for i in range(1, len(pts)): s.append(s[-1] + (pts[i] - pts[i - 1]).length)
    return pts, s

def _at(pts, s, d):
    """yoy uzunligi d (markazdan, ishorali) bo'yicha nuqta va urinma."""
    mid = s[len(s) // 2]; target = mid + d
    for i in range(1, len(s)):
        if s[i] >= target:
            a = (target - s[i - 1]) / (s[i] - s[i - 1]); p = pts[i - 1].lerp(pts[i], a)
            return p, (pts[i] - pts[i - 1]).normalized()
    return pts[-1], (pts[-1] - pts[-2]).normalized()

def build_arch(name, parent=None, upper=False, missing=(), gum_mat=None, gap_scale=1.0):
    """Pastki (yoki yuqori) tish qatori + milk. missing: ('R5',) kabi (R/L + indeks 0..6).
    Qaytaradi: root, {kalit: tish_root}, gum."""
    root = P.empty(name, (0, 0, 0), parent)
    pts, s = arch_points()
    teeth = {}; d = 0.0; centers = {}
    for side, sg in (("R", 1), ("L", -1)):
        d = 0.0
        for i, kind in enumerate(ORDER):
            w = SPEC[kind]["w"]
            dc = (d + w / 2 + 0.02) * sg; d += w + 0.04
            p, tan = _at(pts, s, dc)
            k = f"{side}{i}"; centers[k] = (p, tan)
            if k in missing: continue
            t, _ = build_tooth(f"{name}_{k}", kind, root)
            t.location = p
            ang = math.atan2(tan.y, tan.x) * 1.0
            t.rotation_euler = (0, 0, ang)
            if upper: t.rotation_euler = (R(180), 0, ang)
            teeth[k] = t
    # milk: yoy bo'ylab supurish (tishlar bo'yni atrofida)
    path = []
    total = d + 0.25
    for j in range(61):
        dc = -total + 2 * total * j / 60
        p, tan = _at(pts, s, dc)
        path.append((p + Vector((0, 0, -0.32)), Vector((0, 0, 1))))
    gum = sweep(name + "_gum", path, lambda t: 1.35, lambda t: 0.95, gum_mat or gum_material(), root, segs=28, z_flat=0.55)
    if upper:
        gum.scale.z = -1
    root["centers"] = {k: (tuple(v[0]), tuple(v[1])) for k, v in centers.items()}
    return root, teeth, gum

# ======================================================================
# JAG' KESIMI (cutaway blok): milk + suyak, tish uyasi (boolean)
# ======================================================================
def _box_grid(name, x0, x1, y0, y1, z0, z1, n=(40, 12, 30)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); P.link(o)
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); o.scale = (x1 - x0, y1 - y0, z1 - z0)
    return o

def _apply_all(o):
    bpy.context.view_layer.objects.active = o
    for ob in bpy.context.view_layer.objects: ob.select_set(False)
    o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)

def socket_proxy(name, kind="molar", inflate=0.035):
    """Tish ildizlari shaklidagi kesuvchi (boolean uchun)."""
    s = SPEC[kind]; objs = []
    for i, (x0, L_, r0) in enumerate(s["roots"]):
        me = _root_mesh(f"{name}_r{i}", x0, L_, r0 + inflate)
        o = bpy.data.objects.new(f"{name}_r{i}", me); P.link(o); objs.append(o)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=s["w"] / 2 * 0.78 + inflate, depth=0.9, location=(0, 0, 0.25))
    c = bpy.context.object; c.scale = (1, s["d"] / s["w"], 1); objs.append(c)
    for o in bpy.context.view_layer.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); j = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # o'zaro kesishgan qismlarni birlashtirish (exact boolean uchun bitta yopiq hajm)
    rm = j.modifiers.new("rm", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.03
    _apply_all(j); j.name = name; j.hide_render = True; j.hide_viewport = True
    return j

def build_section(name, parent=None, W=3.4, D=1.4, socket=True, kind="molar"):
    """Kesim bloki: old (kesilgan) yuzi y=0, orqasi y=D. Tish bo'yni (0,0,0).
    Qaytaradi: dict(bone, gum)."""
    cort, sp = bone_materials()
    bone = _box_grid(name + "_bone", -W / 2, W / 2, 0.0, D, -2.5, -0.14)
    gum = _box_grid(name + "_gum", -W / 2, W / 2, -0.0, D, -0.62, 0.04)
    gum.location.y += 0.0005
    for o in (bone, gum):
        bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.12 if o is gum else 0.05; bv.segments = 4
        _apply_all(o)
    # zich to'r (shape key va silliq deformatsiya uchun)
    for o in (bone, gum):
        rm = o.modifiers.new("rm", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.03; rm.use_smooth_shade = True
        _apply_all(o)
    if socket:
        cut = socket_proxy(name + "_sock", kind)
        for o in (bone, gum):
            b = o.modifiers.new("sock", "BOOLEAN"); b.operation = "DIFFERENCE"; b.object = cut; b.solver = "EXACT"
            _apply_all(o)
    # materiallar: kesilgan (old) yuz g'ovak suyak, qolgani zich qobiq
    bone.data.materials.clear(); gum.data.materials.clear()
    bone.data.materials.append(cort); bone.data.materials.append(sp)
    for p in bone.data.polygons:
        p.material_index = 1 if (p.normal.y < -0.7 and p.center.y < 0.02) else 0
        p.use_smooth = p.material_index == 0 or p.normal.y > -0.98
    gm = gum_material()
    gum.data.materials.append(gm); gum.data.materials.append(gum_material("gum_cut", (0.72, 0.22, 0.24)))
    for p in gum.data.polygons:
        p.material_index = 1 if (p.normal.y < -0.7 and p.center.y < 0.02) else 0
    for o in (bone, gum): o.parent = parent
    return dict(bone=bone, gum=gum)

def sink_shapekey(o, depth=0.7, sigma=0.75, crest=-0.14, reach=1.3, narrow=0.0):
    """Suyak/milk tepasini (x=0 atrofida) pastga cho'ktiruvchi shape key ('sink')."""
    if not o.data.shape_keys: o.shape_key_add(name="Basis", from_mix=False)
    kb = o.shape_key_add(name="sink", from_mix=False); kb.value = 0.0
    for i, v in enumerate(o.data.vertices):
        x, y, z = v.co
        g = math.exp(-(x / sigma) ** 2)
        h = max(0.0, 1.0 - max(0.0, crest - z) / reach)            # tepaga yaqin nuqtalar ko'proq tushadi
        kb.data[i].co = (x, y, z - depth * g * h ** 1.5)
    return kb

# ======================================================================
# QISQICH (forseps) va LAGAN
# ======================================================================
def build_forceps(name, parent=None, mat=None):
    """Ikki tumshuq: +Y va -Y tomonda, tishni toj yonidan ushlaydi. Har biri o'z ilmoq empty'si atrofida buriladi
    (X o'qi). Qaytaradi: root, (hinge_a, hinge_b)."""
    m = mat or steel_material()
    root = P.empty(name, (0, 0, 0), parent)
    hinges = []
    for sg in (1, -1):
        hg = P.empty(f"{name}_hinge{sg}", (0, 0, 3.2), root)
        pts = [Vector((0, sg * 0.15, 0.0)), Vector((0, sg * 0.5, -0.9)), Vector((0, sg * 0.75, -2.0)),
               Vector((0, sg * 0.62, -2.75)), Vector((0, sg * 0.5, -3.15))]
        path = [(p, Vector((1, 0, 0))) for p in pts]
        # yo'lni silliq qilish
        sm = []
        for i in range(len(pts) - 1):
            for k in range(6):
                sm.append((pts[i].lerp(pts[i + 1], k / 6), Vector((1, 0, 0))))
        sm.append((pts[-1], Vector((1, 0, 0))))
        beak = sweep(f"{name}_beak{sg}", sm, lambda t: 0.55 - 0.15 * t, lambda t: 0.16 + 0.05 * t, m, hg, segs=16)
        handle = sweep(f"{name}_handle{sg}", [(Vector((0, sg * 0.15, 0)), Vector((1, 0, 0))), (Vector((0, sg * 0.45, 4.0)), Vector((1, 0, 0))),
                                             (Vector((0, sg * 0.8, 9.0)), Vector((1, 0, 0)))], 0.5, 0.2, m, hg, segs=16)
        hinges.append(hg)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.28, depth=0.7, location=(0, 0, 3.2), rotation=(0, R(90), 0))
    pv = bpy.context.object; pv.name = name + "_pivot"; pv.data.materials.append(m); pv.parent = root
    for p in pv.data.polygons: p.use_smooth = True
    return root, hinges

def build_tray(name, parent=None, size=(14, 9, 0.9)):
    m = steel_material()
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, 0.05); o.data.materials.append(m)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(o.data)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    r = bmesh.ops.inset_region(bm, faces=top, thickness=0.6, depth=0)
    bmesh.ops.translate(bm, vec=(0, 0, -size[2]), verts=list({v for f in top for v in f.verts}))
    bm.to_mesh(o.data); bm.free()
    sol = o.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.08
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.25; bv.segments = 6; bv.limit_method = "ANGLE"
    o.modifiers.new("s", "SUBSURF").levels = 1
    for p in o.data.polygons: p.use_smooth = True
    o.parent = parent
    return o

# ======================================================================
# RENTGEN JAG'I (metrda, bosh suyagi koordinatasida: X chap, Y tepa, Z old)
# ======================================================================
def build_xray_jaw(name, parent, bone_mat, tooth_mat, gap_mat, missing="R5"):
    root = P.empty(name, (0, 0, 0), parent)
    # pastki jag' tanasi + shoxlari: U yoy
    pts = []
    for i in range(41):
        u = -1 + 2 * i / 40
        x = 0.047 * math.sin(u * math.pi / 2); z = 0.075 - 0.07 * abs(u) ** 1.8
        pts.append(Vector((x, -0.06, z)))
    ram = lambda sg: [Vector((sg * 0.05, -0.055, -0.0)), Vector((sg * 0.052, -0.02, -0.012)), Vector((sg * 0.053, 0.012, -0.018))]
    path = [(p, Vector((0, 1, 0))) for p in ram(-1)[::-1] + pts + ram(1)]
    body = sweep(name + "_mand", path, 0.011, 0.028, bone_mat, root, segs=16)
    # tishlar (kichraytirilgan arch: 1 sm -> 0.0085 m)
    arch, teeth, gum = build_arch(name + "_low", root, missing=(missing,), gum_mat=bone_mat)
    arch.scale = (0.0088,) * 3; arch.rotation_euler = (R(-90), 0, 0); arch.location = (0, -0.044, 0.078)
    uarch, uteeth, ugum = build_arch(name + "_up", root, upper=True, gum_mat=bone_mat)
    uarch.scale = (0.0092,) * 3; uarch.rotation_euler = (R(-90), 0, 0); uarch.location = (0, -0.03, 0.08)
    for t in list(teeth.values()) + list(uteeth.values()):
        for c in t.children:
            c.data.materials.clear(); c.data.materials.append(tooth_mat)
    # bo'sh joy (sug'urilgan tish o'rni) — qizil nur
    p, tan = arch["centers"][missing]
    gap = P.sphere(name + "_gap", 0.55, tuple(p), gap_mat, scale=(1.2, 1.0, 0.8), parent=None) if hasattr(P, "sphere") else None
    if gap is None:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.55, location=tuple(p))
        gap = bpy.context.object; gap.name = name + "_gap"; gap.data.materials.append(gap_mat)
        for pl in gap.data.polygons: pl.use_smooth = True
    gap.parent = arch
    return root, arch, uarch, gap
