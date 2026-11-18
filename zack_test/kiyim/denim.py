# "Ko'cha shimi" videosi uchun mikro dunyo (1000x, artistik masshtab): jinsi twill to'qimasi (ko'k tanda + oq arqoq),
# ichak tayoqchasi (E. coli, xivchinli), chang kanasi (8 oyoq) va lichinkasi (6 oyoq), tuxumlar, jinsi ko'ndalang kesimi.
# Paxta to'qima, bakteriyalar, teri — micro.py / mite.py dan.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import micro as U
import mite as M

R = math.radians
_link = U._link
math_n = U.math_n
value_node = U.value_node


# ======================= JINSI TWILL =======================
def twill(name, size, sp, r, m_warp, m_weft, parent=None, size_y=None):
    """2/1 twill: tanda (X bo'ylab, ko'k) har 3 arqoqdan 2 tasining ustidan o'tadi, faza har ipda 1 ga siljiydi -> diagonal chiziqlar.
    Qaytaradi: ob'ektlar, BVH (mahalliy)."""
    sy = size_y or size
    nx, ny = int(size / sp), int(sy / sp)                 # nx: arqoq (Y bo'ylab) soni, ny: tanda (X bo'ylab) soni
    amp = r * 1.1; ph0 = R(30)
    objs = []; allv, allf = [], []
    def add(me, mat):
        me.materials.append(mat)
        o = _link(bpy.data.objects.new(me.name, me), parent); objs.append(o)
        off = len(allv); allv.extend(v.co.copy() for v in me.vertices); allf.extend(tuple(off + i for i in p.vertices) for p in me.polygons)
    for k in range(ny):                                     # tanda
        c = -sy / 2 + (k + 0.5) * sp; pts = []
        for i in range(int(size / sp * 8) + 1):
            t = -size / 2 + i * sp / 8; u = (t + size / 2) / sp - 0.5
            pts.append(Vector((t, c, amp * math.sin(2 * math.pi * (u + k) / 3 + ph0))))
        add(U.tube_mesh(f"{name}_wp{k}", pts, sp * 0.5, r * 0.62), m_warp)
    for j in range(nx):                                     # arqoq
        c = -size / 2 + (j + 0.5) * sp; pts = []
        for i in range(int(sy / sp * 8) + 1):
            t = -sy / 2 + i * sp / 8; u = (t + sy / 2) / sp - 0.5
            pts.append(Vector((c, t, -amp * math.sin(2 * math.pi * (u + j) / 3 + ph0))))
        add(U.tube_mesh(f"{name}_wf{j}", pts, sp * 0.42, r * 0.55), m_weft)
    return objs, BVHTree.FromPolygons(allv, allf)

def denim_materials():
    warp = U.fabric_material("denim_warp", (0.012, 0.03, 0.14), (0.05, 0.11, 0.32), dirt_col=(0.32, 0.27, 0.16), sss=0.05)
    warp.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.15
    weft = U.fabric_material("denim_weft", (0.62, 0.62, 0.6), (0.86, 0.85, 0.8), dirt_col=(0.55, 0.45, 0.25), sss=0.3)
    return warp, weft


# ======================= ICHAK TAYOQCHASI (E. coli) =======================
def helix_mesh(name, length, amp, turns, r, NP=8, NS=90):
    """+Y bo'ylab spiral ip (xivchin): boshi (0,0,0), oxiri (0,length,0)"""
    pts = []
    for i in range(NS + 1):
        t = i / NS; a = 2 * math.pi * turns * t; e = min(1.0, t * 6)       # ildizda to'g'ri
        pts.append(Vector((amp * e * math.cos(a), length * t, amp * e * math.sin(a))))
    return U.tube_mesh(name, pts, r, r, NP=NP)

def ecoli_material():
    return U.bact_material("ecoli_m", (0.42, 0.62, 0.16), (0.7, 0.8, 0.25), 0.06)

def flagella_material():
    m = bpy.data.materials.new("flag_m"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.75, 0.82, 0.55, 1); b.inputs["Roughness"].default_value = 0.4
    b.inputs["Subsurface Weight"].default_value = 0.5; b.inputs["Subsurface Scale"].default_value = 0.01
    b.inputs["Emission Color"].default_value = (0.7, 0.9, 0.5, 1); b.inputs["Emission Strength"].default_value = 0.15
    return m

class EKit:
    def __init__(self):
        self.body = U.capsule_mesh("ecoli_body", 0.22, 0.05, NP=20, NR=10); self.body.materials.append(ecoli_material())
        self.flag = helix_mesh("flagellum", 0.55, 0.025, 3.0, 0.0055); self.flag.materials.append(flagella_material())

def build_ecoli(name, kit, parent=None, seed=0, nflag=5):
    """tana +Y o'qi bo'ylab; xivchinlar orqa uchdan (-Y) chiqadi va o'z o'qi atrofida aylanadi ('spin' — CYCLES)"""
    rnd = random.Random(seed)
    root = _link(bpy.data.objects.new(name, None), parent)
    body = _link(bpy.data.objects.new(name + "_b", kit.body), root)
    flags = []
    for i in range(nflag):
        f = _link(bpy.data.objects.new(f"{name}_f{i}", kit.flag), root)
        a = 2 * math.pi * i / nflag + rnd.uniform(-0.3, 0.3)
        f.location = (0.035 * math.cos(a), -0.08 + rnd.uniform(-0.05, 0.06), 0.035 * math.sin(a))
        f.rotation_mode = "YXZ"
        f.rotation_euler = (R(160 + rnd.uniform(-20, 20)) * math.sin(a) * 0.25, rnd.uniform(0, 6.28), R(180) + R(rnd.uniform(-25, 25)) * math.cos(a))
        f.scale = (1, rnd.uniform(0.8, 1.2), 1)
        flags.append(f)
    return root, body, flags

def spin(objs, f0, f1, turns_per_s=3.0, axis=1):
    """xivchin aylanishi (to'lqin yuguradi): mahalliy Y o'qi atrofida chiziqli"""
    for o in objs:
        r0 = o.rotation_euler[axis]
        o.keyframe_insert("rotation_euler", index=axis, frame=f0)
        o.rotation_euler[axis] = r0 + 2 * math.pi * turns_per_s * (f1 - f0) / 24.0
        o.keyframe_insert("rotation_euler", index=axis, frame=f1)
        for fc in U_fc(o):
            if fc.data_path == "rotation_euler":
                for k in fc.keyframe_points: k.interpolation = "LINEAR"

def U_fc(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    return M._fcurves(ad.action)


# ======================= CHANG KANASI =======================
def dmite_mesh(name="dmite_body", NU=48, NV=28, rx=0.055, ry=0.078, rz=0.045):
    """yumaloq-oval tana, old tomoni (+Y) torayadi, orqa tomonda ko'ndalang burmalar"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=NU, v_segments=NV, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        sx = rx * (1 - 0.28 * max(0, y) ** 2); sz = rz * (0.78 if z < 0 else 1.0) * (1 - 0.2 * max(0, y) ** 2)
        fold = 1 + 0.035 * math.sin(y * 22) * max(0, z) if y < 0.3 else 1.0
        v.co = Vector((x * sx * fold, y * ry, z * sz * fold))
    # og'iz qismi (gnatosoma)
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.022, radius2=0.01, depth=0.035)
    bmesh.ops.rotate(bm, verts=g["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(R(-90), 3, "X"))
    bmesh.ops.translate(bm, verts=g["verts"], vec=(0, ry + 0.012, -0.008))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    at = me.attributes.new("tail", "FLOAT", "POINT")
    for i, v in enumerate(me.vertices): at.data[i].value = max(0.0, min(1.0, -v.co.y / ry))
    return me

class DKit:
    def __init__(self, mat=None):
        self.body = dmite_mesh(); self.leg = M.leg_mesh("dm_leg")
        self.mat = mat or M.mite_material("dmite_m")
        self.hair_m = M.hair_material("dm_seta", (0.85, 0.75, 0.55), 0.4, trans=0.3)
        for me in (self.body, self.leg): me.materials.append(self.mat)

DLEG_Y = (0.045, 0.02, -0.02, -0.045)

def build_dmite(name, kit, parent=None, seed=0, pairs=4, scale=1.0):
    """root['ph'] — qadam fazasi (M.walk), root['amp'] — oyoq tebranishi. Bosh +Y, orqa +Z."""
    rnd = random.Random(seed)
    root = _link(bpy.data.objects.new(name, None), parent); root.scale = (scale,) * 3
    root["ph"] = rnd.random(); root["amp"] = 1.0
    body = _link(bpy.data.objects.new(name + "_body", kit.body), root)
    ys = DLEG_Y if pairs == 4 else (0.045, 0.01, -0.035)
    for i, y in enumerate(ys):
        for sx in (-1, 1):
            lg = _link(bpy.data.objects.new(f"{name}_leg{i}{'LR'[sx > 0]}", kit.leg), root)
            lg.location = (sx * 0.042, y, -0.016); lg.scale = (1.8, 1.8, 2.3)
            # oyoq mesh'i -Z ga qaragan: Ry(-sx*62) -> tashqariga va pastga, Rz(yaw) -> old/orqa
            yaw = sx * R((40 - 26 * i) if pairs == 4 else (35 - 35 * i))
            base_y = -sx * R(62); off = (i % 2) * math.pi + (0 if sx > 0 else math.pi)
            lg.rotation_mode = "XYZ"
            lg.rotation_euler = (0, base_y, yaw)
            M._drive(lg, "rotation_euler", 2, root, f"{yaw:.4f}+0.35*a*sin(ph*6.2832+{off:.3f})")
            M._drive(lg, "rotation_euler", 1, root, f"{base_y:.4f}+{-sx}*0.25*a*max(0,cos(ph*6.2832+{off:.3f}))")
    # uzun tuklar (setae)
    for k in range(10):
        a = rnd.uniform(0, 6.28); yy = rnd.uniform(-0.06, 0.03)
        base = Vector((0.045 * math.cos(a) * 0.9, yy, 0.03 * abs(math.sin(a)) + 0.012))
        d = Vector((math.cos(a) * 0.6, -0.8 if yy < 0 else -0.3, 0.6)).normalized()
        M.hair(f"{name}_seta{k}", base, d, rnd.uniform(0.06, 0.12), 0.0022, kit.hair_m, root,
               bend=Vector((0, -0.02, -0.02)), segs=10, depth=0.004)
    return root, body


# ======================= TUXUMLAR =======================
def egg_material():
    m = bpy.data.materials.new("egg_m"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.93, 0.9, 0.82, 1); b.inputs["Roughness"].default_value = 0.22
    b.inputs["Subsurface Weight"].default_value = 0.7; b.inputs["Subsurface Scale"].default_value = 0.02
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.85, 0.6)
    b.inputs["Coat Weight"].default_value = 0.9; b.inputs["Coat Roughness"].default_value = 0.05
    b.inputs["Sheen Weight"].default_value = 0.4
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 60.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.002
    L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def egg_mesh(name, r=0.045, ry=0.07, part="full"):
    """cho'ziq tuxum (+Y o'qi); part: "full" — butun, "cap" — faqat qopqoq (y > 0.62*ry), "body" — qopqoqsiz tana"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * r * (1 - 0.12 * v.co.y), v.co.y * ry, v.co.z * r * (1 - 0.12 * v.co.y)))
    cut = 0.62 * ry
    if part == "cap": bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < cut - 1e-4], context="VERTS")
    if part == "body": bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > cut + 1e-4], context="VERTS")
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me


# ======================= JINSI KO'NDALANG KESIMI =======================
def fiber_meshes(length):
    me = bpy.data.meshes.new("fiber")
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=1.0, radius2=1.0, depth=length)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R(90), 3, "Y"))     # o'q X
    bmesh.ops.translate(bm, verts=bm.verts, vec=(-length / 2, 0, 0))                                   # x: -length..0
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = abs(p.normal.x) < 0.5
    return me

def yarn_section(name, center, ry, rz, n, fiber_me, m_out, m_in, parent, seed=0, length=4.0):
    """X o'qi bo'ylab yotgan ip (tolalar to'plami); x=0 da kesilgan (kesim yuzasi +X ga qaraydi).
    Halqali bo'yash: tashqi tolalar indigo, ichki oq (jinsining haqiqiy xususiyati)."""
    rnd = random.Random(seed); out = []; placed = []
    tries = 0
    while len(placed) < n and tries < n * 40:
        tries += 1
        a = rnd.uniform(0, 6.28); d = math.sqrt(rnd.random())
        y, z = ry * d * math.cos(a), rz * d * math.sin(a)
        fr = rnd.uniform(0.022, 0.032)
        if any((y - py) ** 2 + (z - pz) ** 2 < (fr + pr) ** 2 * 0.9 for py, pz, pr in placed): continue
        placed.append((y, z, fr))
    for i, (y, z, fr) in enumerate(placed):
        o = _link(bpy.data.objects.new(f"{name}_{i}", fiber_me), parent)
        edge = math.sqrt((y / ry) ** 2 + (z / rz) ** 2)
        o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = m_out if edge > 0.62 else m_in
        o.location = (Vector(center) + Vector((rnd.uniform(-0.04, 0.0), y, z)))
        o.scale = (1.0 + rnd.uniform(-0.05, 0.05) * 0, fr, fr)
        o.rotation_euler = (0, R(rnd.uniform(-2, 2)), R(rnd.uniform(-2, 2)))
        out.append(o)
    return out

def section_fiber_mat(name, col, glow=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.45
    b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Scale"].default_value = 0.02
    b.inputs["Sheen Weight"].default_value = 0.5
    # 'wet' — ter singishi: kesimda sarg'ish dog' (mahalliy z bo'yicha yuqoridan pastga)
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    ow = N.new("ShaderNodeObjectInfo")
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(ow.outputs["Location"], sp.inputs[0])
    wl = value_node(m, "wl", 99.0)                                     # ter chegarasi (dunyo z); undan yuqori tolalar ho'l
    wet = math_n(N, L, "GREATER_THAN", sp.outputs["Z"], wl)
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"; c.blend_type = "MULTIPLY"; c.inputs[7].default_value = (1.0, 0.82, 0.45, 1)
    c.inputs[6].default_value = (*col, 1); L.new(math_n(N, L, "MULTIPLY", wet, 0.85), c.inputs["Factor"]); L.new(c.outputs[2], b.inputs["Base Color"])
    L.new(math_n(N, L, "SUBTRACT", 0.45, math_n(N, L, "MULTIPLY", wet, 0.35)), b.inputs["Roughness"])
    L.new(math_n(N, L, "MULTIPLY", wet, 0.8), b.inputs["Coat Weight"])
    return m
