# Yostiq jildi videosi uchun mikro dunyo modellari (1000x): to'qilgan paxta iplari, bakteriyalar (tayoqcha va sharsimon),
# zamburug' iplari (gifalar), chang donalari, so'lak tomchilari. Teri yuzasi va kesim — mite.py dan.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

R = math.radians

def _link(o, parent=None):
    bpy.context.scene.collection.objects.link(o)
    if parent is not None: o.parent = parent
    return o

def math_n(N, L, op, a, b=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0]

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]

# ======================= TO'QILGAN MATO =======================
def tube_mesh(name, pts, ry, rz, NP=14, twist=0.0):
    """pts bo'ylab elliptik quvur (ry yon, rz balandlik), UV: u = uzunlik, v = aylana (ip eshilishi uchun)"""
    n = len(pts); verts, faces, uvs = [], [], []
    acc = [0.0]
    for i in range(1, n): acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
    for i, p in enumerate(pts):
        tg = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        up = Vector((0, 0, 1)); side = tg.cross(up).normalized(); up2 = side.cross(tg).normalized()
        for j in range(NP):
            a = 2 * math.pi * j / NP
            verts.append(tuple(p + side * math.cos(a) * ry + up2 * math.sin(a) * rz))
    for i in range(n - 1):
        for j in range(NP):
            a_ = i * NP + j; b_ = i * NP + (j + 1) % NP
            faces.append((a_, b_, b_ + NP, a_ + NP))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; i, j = divmod(vi, NP)
            jj = j if not (j == 0 and any(me.loops[k].vertex_index % NP == NP - 1 for k in poly.loop_indices)) else NP
            uv.data[li].uv = (acc[i] / 0.5, jj / NP)
    for p in me.polygons: p.use_smooth = True
    return me

def fabric_material(name="fabric"):
    """paxta ipi: eshilgan tolalar (diagonal to'lqin), mayda tukchalar; 'dirt' — sarg'ish dog'lar, 'wet' + 'wx','wy','wr' — ho'l doira"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Scale"].default_value = 0.08
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.9, 0.7)
    b.inputs["Sheen Weight"].default_value = 0.6; b.inputs["Sheen Roughness"].default_value = 0.4
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs[0], sep.inputs[0])
    tw = math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", sep.outputs["X"], 9.0), math_n(N, L, "MULTIPLY", sep.outputs["Y"], 6.2832 * 1.0))
    st = math_n(N, L, "SINE", math_n(N, L, "MULTIPLY", tw, 3.0))           # 3 ta eshilgan tola
    fine = math_n(N, L, "SINE", math_n(N, L, "MULTIPLY", tw, 41.0))         # ingichka tolalar
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.45; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 3.0; nz2.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    dirt = value_node(m, "dirt", 0.0); wet = value_node(m, "wet", 0.0)
    wx = value_node(m, "wx", 0.0); wy = value_node(m, "wy", 0.0); wr = value_node(m, "wr", 0.0)
    # dog' niqobi: shovqin * dirt
    dm = math_n(N, L, "MULTIPLY", math_n(N, L, "POWER", nz.outputs["Fac"], 1.4), math_n(N, L, "MULTIPLY", dirt, 2.2), clamp=True)
    # ho'l doira (mahalliy XY)
    sepo = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sepo.inputs[0])
    dx = math_n(N, L, "SUBTRACT", sepo.outputs["X"], wx); dy = math_n(N, L, "SUBTRACT", sepo.outputs["Y"], wy)
    dd = math_n(N, L, "SQRT", math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", dx, dx), math_n(N, L, "MULTIPLY", dy, dy)))
    wm = math_n(N, L, "MULTIPLY", math_n(N, L, "SUBTRACT", 1.0, math_n(N, L, "DIVIDE", math_n(N, L, "SUBTRACT", dd, wr), 0.8), clamp=True), wet)
    c0 = N.new("ShaderNodeMix"); c0.data_type = "RGBA"; c0.inputs[6].default_value = (0.84, 0.82, 0.77, 1); c0.inputs[7].default_value = (0.95, 0.94, 0.9, 1)
    L.new(math_n(N, L, "MULTIPLY", math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", st, fine), 1.0), 0.5), c0.inputs["Factor"])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"; c1.inputs[7].default_value = (0.66, 0.5, 0.2, 1)
    L.new(c0.outputs[2], c1.inputs[6]); L.new(math_n(N, L, "MULTIPLY", dm, math_n(N, L, "ADD", 0.7, math_n(N, L, "MULTIPLY", nz2.outputs["Fac"], 0.5))), c1.inputs["Factor"])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.blend_type = "MULTIPLY"; c2.inputs[7].default_value = (0.62, 0.58, 0.45, 1)
    L.new(c1.outputs[2], c2.inputs[6]); L.new(wm, c2.inputs["Factor"])
    L.new(c2.outputs[2], b.inputs["Base Color"])
    L.new(math_n(N, L, "SUBTRACT", 0.75, math_n(N, L, "MULTIPLY", wm, 0.6)), b.inputs["Roughness"])
    L.new(math_n(N, L, "MULTIPLY", wm, 0.8), b.inputs["Coat Weight"])
    h = math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", st, 0.6), math_n(N, L, "MULTIPLY", fine, 0.15))
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 1.0; bp.inputs["Distance"].default_value = 0.06
    L.new(h, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def weave(name, size, sp, r, mat, parent=None):
    """size x size maydonda tanda (X) va arqoq (Y) iplari, bir-birining ustidan/ostidan o'tadi. Qaytaradi: obyektlar, BVH (mahalliy)"""
    n = int(size / sp); objs = []; amp = r * 0.55
    allv, allf = [], []
    for k in range(n):
        c = -size / 2 + (k + 0.5) * sp
        for axis in (0, 1):
            pts = []
            for i in range(int(size / sp * 8) + 1):
                t = -size / 2 + i * sp / 8
                ph = (t + size / 2) / sp * math.pi + (k % 2) * math.pi + axis * 0.0
                z = amp * math.sin(ph) * (1 if axis == 0 else -1)
                pts.append(Vector((t, c, z)) if axis == 0 else Vector((c, t, z)))
            me = tube_mesh(f"{name}_{axis}_{k}", pts, sp * 0.47, r * 0.62)
            me.materials.append(mat)
            o = _link(bpy.data.objects.new(me.name, me), parent); objs.append(o)
            off = len(allv); allv += [v.co.copy() for v in me.vertices]; allf += [tuple(off + i for i in p.vertices) for p in me.polygons]
    bvh = BVHTree.FromPolygons(allv, allf)
    return objs, bvh

def top_z(bvh, x, y, z0=5.0):
    hit = bvh.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)))
    return (hit[0].z, hit[1]) if hit[0] is not None else (0.0, Vector((0, 0, 1)))

def fuzz(name, bvh, n, mat, parent, area, seed=3, hair_fn=None):
    """ipdan chiqib turgan mayda tolalar"""
    rnd = random.Random(seed); out = []
    for i in range(n):
        x = rnd.uniform(area[0], area[1]); y = rnd.uniform(area[2], area[3])
        z, nr = top_z(bvh, x, y)
        a = rnd.uniform(0, 6.28); d = Vector((math.cos(a), math.sin(a), rnd.uniform(0.3, 1.2)))
        out.append(hair_fn(f"{name}{i}", (x, y, z - 0.02), d, rnd.uniform(0.6, 1.8), rnd.uniform(0.012, 0.022), mat, parent,
                           bend=Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), -0.5)), depth=0.05))
    return out

# ======================= BAKTERIYALAR =======================
def capsule_mesh(name, length, r, NP=16, NR=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=NP, v_segments=NR * 2, radius=r)
    for v in bm.verts:
        if v.co.z > 1e-6: v.co.z += length / 2
        elif v.co.z < -1e-6: v.co.z -= length / 2
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R(90), 3, "X"))   # o'q +Y
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me

def bact_material(name, col, col2, glow=0.0):
    """ho'l, yarim shaffof bakteriya: SSS + coat, mayda donachalar; 'pop' bo'linish paytida yorishadi"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.03
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.6)
    b.inputs["Coat Weight"].default_value = 0.7; b.inputs["Coat Roughness"].default_value = 0.1; b.inputs["Roughness"].default_value = 0.35
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nz.inputs["Detail"].default_value = 5
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    oi = N.new("ShaderNodeObjectInfo")
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; c.inputs[6].default_value = (*col, 1); c.inputs[7].default_value = (*col2, 1)
    L.new(math_n(N, L, "ADD", math_n(N, L, "MULTIPLY", nz.outputs["Fac"], 0.6), math_n(N, L, "MULTIPLY", oi.outputs["Random"], 0.5)), c.inputs["Factor"])
    L.new(c.outputs[2], b.inputs["Base Color"])
    if glow:
        L.new(c.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = glow
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.004
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

class BKit:
    def __init__(self):
        self.rod = capsule_mesh("rod", 0.11, 0.032)
        self.rod2 = capsule_mesh("rod2", 0.06, 0.03)
        self.coc = capsule_mesh("coccus", 0.0, 0.035)
        self.m_rod = bact_material("bact_rod", (0.35, 0.62, 0.12), (0.62, 0.78, 0.2), 0.04)
        self.m_acne = bact_material("bact_acne", (0.75, 0.28, 0.42), (0.9, 0.5, 0.55), 0.04)
        self.m_coc = bact_material("bact_coc", (0.45, 0.25, 0.7), (0.7, 0.45, 0.85), 0.04)
        self.rod.materials.append(self.m_rod); self.rod2.materials.append(self.m_acne); self.coc.materials.append(self.m_coc)
    def new(self, name, kind, parent=None):
        me = {"rod": self.rod, "acne": self.rod2, "coc": self.coc}[kind]
        return _link(bpy.data.objects.new(name, me), parent)

def scatter_bacteria(kit, name, bvh, n, area, parent, seed=1, kinds=("rod", "acne", "coc"), lift=0.025, clump=0.0, centers=None):
    """ip yuzasiga yopishgan bakteriyalar; centers berilsa, to'dalar atrofida"""
    rnd = random.Random(seed); out = []
    for i in range(n):
        if centers and rnd.random() < clump:
            cx, cy, cr = rnd.choice(centers); a = rnd.uniform(0, 6.28); d = cr * math.sqrt(rnd.random())
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        else:
            x = rnd.uniform(area[0], area[1]); y = rnd.uniform(area[2], area[3])
        z, nr = top_z(bvh, x, y)
        kd = rnd.choice(kinds)
        o = kit.new(f"{name}{i}", kd, parent)
        s = rnd.uniform(0.75, 1.3); o.scale = (s, s * rnd.uniform(0.85, 1.25), s)
        o.location = (x, y, z + lift * s)
        nrm = Vector(nr); fw = Vector((math.cos(rnd.uniform(0, 6.28)), math.sin(rnd.uniform(0, 6.28)), 0))
        fw = (fw - nrm * fw.dot(nrm)).normalized()
        Y = fw; Z = (nrm - Y * nrm.dot(Y)).normalized(); X = Y.cross(Z)
        o.rotation_euler = Matrix((X, Y, Z)).transposed().to_euler()
        o.rotation_euler.y += R(rnd.uniform(-15, 15))
        out.append(o)
    return out

def pop(o, f, dur=6, s1=None):
    """f kadrda paydo bo'ladi (0 -> 1.15 -> 1)"""
    s1 = Vector(s1 or o.scale)
    o.scale = s1 * 0.001; o.keyframe_insert("scale", frame=f - 1)
    o.scale = s1 * 1.18; o.keyframe_insert("scale", frame=f + dur * 0.6)
    o.scale = s1; o.keyframe_insert("scale", frame=f + dur)

# ======================= ZAMBURUG' (gifalar) =======================
def hypha_material(name="hypha"):
    """oq-kulrang paxmoq ip, 'grow' (0..1) — egri bo'ylab o'sish (u < grow ko'rinadi)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.86, 0.88, 0.8, 1)
    b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Scale"].default_value = 0.03
    b.inputs["Roughness"].default_value = 0.45; b.inputs["Coat Weight"].default_value = 0.3
    b.inputs["Emission Color"].default_value = (0.7, 0.95, 0.75, 1); b.inputs["Emission Strength"].default_value = 0.05
    ua = N.new("ShaderNodeAttribute"); ua.attribute_name = "u"
    g = value_node(m, "grow", 0.0)
    vis = math_n(N, L, "LESS_THAN", ua.outputs["Fac"], g)
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(vis, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs[0])
    return m

def hyphae(name, bvh, start, n_branch, mat, parent, tube_fn, seed=5, step=0.12, nsteps=26, r=0.022):
    """tasodifiy yuruvchi, shoxlanuvchi iplar (ip yuzasidan ozgina yuqorida)"""
    rnd = random.Random(seed); out = []; tips = []
    def walk(p0, a0, ns):
        pts = [p0]; a = a0; x, y = p0.x, p0.y
        for i in range(ns):
            a += rnd.uniform(-0.45, 0.45); x += math.cos(a) * step; y += math.sin(a) * step
            z, _ = top_z(bvh, x, y); pts.append(Vector((x, y, z + r * 1.2 + 0.02 * math.sin(i * 1.3))))
        return pts, a
    trunk = []
    for k in range(n_branch):
        if k == 0 or not trunk:
            z, _ = top_z(bvh, *start); p0 = Vector((start[0], start[1], z + r)); a0 = rnd.uniform(0, 6.28); ns = nsteps
        else:
            base = rnd.choice(trunk); p0 = base[rnd.randint(2, len(base) - 3)]; a0 = rnd.uniform(0, 6.28); ns = int(nsteps * rnd.uniform(0.35, 0.7))
        pts, _ = walk(p0, a0, ns); trunk.append(pts)
        out.append(tube_fn(f"{name}{k}", pts, r * (1.0 if k == 0 else 0.75), mat, parent)); tips.append(pts[-1])
    return out, tips

# ======================= CHANG DONASI =======================
def dust_mesh(name, seed=0):
    rnd = random.Random(seed)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    k = [Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() for _ in range(5)]
    for v in bm.verts:
        d = v.co.normalized(); s = 1.0 + sum(0.25 * max(0, d.dot(q)) ** 3 for q in k) + rnd.uniform(-0.06, 0.06)
        v.co = d * s
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me

def fall(o, f0, f1, p0, p1, spin, step=2):
    """p0 dan p1 ga tushish (ohista sekinlashib), aylanib"""
    p0 = Vector(p0); p1 = Vector(p1); r0 = Vector(o.rotation_euler)
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        t = (f - f0) / max(1, f1 - f0); t2 = 1 - (1 - t) ** 1.6
        o.location = p0.lerp(p1, t2) + Vector((0.08 * math.sin(t * 7 + spin), 0.08 * math.cos(t * 5 + spin), 0)) * (1 - t)
        o.keyframe_insert("location", frame=f)
        o.rotation_euler = (r0.x + spin * t * 2.5 * (1 - t * 0.6), r0.y + spin * t * 1.7 * (1 - t * 0.6), r0.z + spin * t)
        o.keyframe_insert("rotation_euler", frame=f)
