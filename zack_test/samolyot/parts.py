# "Samolyot derazalari" videosi uchun yordamchilar va procedural qismlar (Blender 5.2, bpy)
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix

R = math.radians
sc = lambda: bpy.context.scene

# ---------------- umumiy ----------------
def link(o):
    sc().collection.objects.link(o); return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = link(bpy.data.objects.new(name, None)); o.location = loc
    if parent: par(o, parent)
    return o

def par(child, parent):
    """Bolani dunyo koordinatasini saqlagan holda ota-ga bog'lash (CLAUDE.md: matrix_parent_inverse)."""
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy(); child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted(); child.matrix_world = mw

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def mesh_obj(name, bm, m=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    if m: me.materials.append(m)
    return o

def box(name, size, loc, m, bevel=0.0, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    o = mesh_obj(name, bm, m, loc); o.rotation_euler = [R(a) for a in rot]
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3; smooth(o)
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), verts=32, bevel=True):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
    o = mesh_obj(name, bm, m, loc); o.rotation_euler = [R(a) for a in rot]; smooth(o)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = min(0.02, r * 0.2); b.segments = 2; b.limit_method = "ANGLE"
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), seg=24):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    o = mesh_obj(name, bm, m, loc); o.scale = scale; smooth(o); return o

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

def all_fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "layers") and act.layers:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return list(act.fcurves)

def set_interp(idb, mode="LINEAR", path=None):
    for fc in all_fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode

def vis(o, ranges):
    """o (va bolalari) faqat berilgan kadr oraliqlarida render qilinadi."""
    objs = [o] + list(o.children_recursive)
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
            if x.animation_data and x.animation_data.action:
                for fc in all_fcurves(x):
                    if fc.data_path == "hide_render":
                        for k in fc.keyframe_points: k.interpolation = "CONSTANT"

# ---------------- materiallar ----------------
def mat(name, col, rough=0.5, metal=0.0, emit=0.0, coat=0.0, alpha=1.0, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    return m

def bsdf(m): return m.node_tree.nodes["Principled BSDF"]

class G:
    """Shader node ifoda quruvchisi: G(nt).math('ADD', a, b) -> socket."""
    def __init__(self, nt): self.nt = nt; self.N = nt.nodes; self.L = nt.links
    def _in(self, sock, v):
        if isinstance(v, (int, float)): sock.default_value = v
        elif isinstance(v, tuple): sock.default_value = v
        else: self.L.new(v, sock)
    def math(self, op, a, b=None, c=None):
        n = self.N.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is not None: self._in(n.inputs[i], v)
        return n.outputs[0]
    def add(self, a, b): return self.math("ADD", a, b)
    def sub(self, a, b): return self.math("SUBTRACT", a, b)
    def mul(self, a, b): return self.math("MULTIPLY", a, b)
    def div(self, a, b): return self.math("DIVIDE", a, b)
    def pw(self, a, b): return self.math("POWER", a, b)
    def ab(self, a): return self.math("ABSOLUTE", a)
    def exp(self, a): return self.math("EXPONENT", a)
    def mx(self, a, b): return self.math("MAXIMUM", a, b)
    def mn(self, a, b): return self.math("MINIMUM", a, b)
    def sin(self, a): return self.math("SINE", a)
    def fr(self, a): return self.math("FRACT", a)
    def sqrt(self, a): return self.math("SQRT", a)
    def maprange(self, v, a, b, c, d, clamp=True):
        n = self.N.new("ShaderNodeMapRange"); n.clamp = clamp
        self._in(n.inputs["Value"], v)
        for s, x in zip(("From Min", "From Max", "To Min", "To Max"), (a, b, c, d)): n.inputs[s].default_value = x
        return n.outputs["Result"]
    def value(self, name, v=0.0):
        n = self.N.new("ShaderNodeValue"); n.name = n.label = name; n.outputs[0].default_value = v; return n
    def objxyz(self, kind="Object"):
        tc = self.N.new("ShaderNodeTexCoord"); s = self.N.new("ShaderNodeSeparateXYZ")
        self.L.new(tc.outputs[kind], s.inputs[0]); return s.outputs[0], s.outputs[1], s.outputs[2]
    def ramp(self, v, stops):
        n = self.N.new("ShaderNodeValToRGB"); cr = n.color_ramp
        while len(cr.elements) > 1: cr.elements.remove(cr.elements[-1])
        cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1)
        for p, c in stops[1:]:
            e = cr.elements.new(p); e.color = (*c, 1)
        self._in(n.inputs[0], v); return n.outputs[0]
    def mixcol(self, fac, a, b):
        n = self.N.new("ShaderNodeMix"); n.data_type = "RGBA"
        self._in(n.inputs[0], fac)
        for i, v in ((6, a), (7, b)):
            if isinstance(v, tuple): n.inputs[i].default_value = (*v, 1) if len(v) == 3 else v
            else: self.L.new(v, n.inputs[i])
        return n.outputs[2]

def key_value(m, name, f, v):
    n = m.node_tree.nodes[name]; n.outputs[0].default_value = v
    n.outputs[0].keyframe_insert("default_value", frame=f)

def key_input(sock, f, v):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)

def tex_image_mat(name, folder, scale=1.0, tint=None, rough_mul=None):
    """Poly Haven PBR tekstura (diff/rough/nor)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, nc=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(folder, fn))
        t.projection = "BOX"; t.projection_blend = 0.2
        if nc: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = img("diff.jpg")
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1
        L.new(d.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    else: L.new(d.outputs[0], b.inputs["Base Color"])
    r = img("rough.jpg", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def import_gltf(path, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, name=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(name or os.path.basename(path).split(".")[0] + "_grp", (0, 0, 0))
    for o in new:
        if o.parent is None: o.parent = root
    root.location = loc; root.rotation_euler = [R(a) for a in rot]; root.scale = (scale,) * 3
    return root, new

# ---------------- kamera: har kadrga kalit (ease + silkinish) ----------------
def ease(t, kind="inout"):
    t = max(0.0, min(1.0, t))
    if kind == "in": return t * t * t
    if kind == "out": return 1 - (1 - t) ** 3
    if kind == "lin": return t
    return t * t * (3 - 2 * t)

def camera(name, lens=24, fstop=None, focus=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = 0.01; d.clip_end = 5000
    c = link(bpy.data.objects.new(name, d))
    tgt = empty(name + "_tgt")
    t = c.constraints.new("TRACK_TO"); t.target = tgt; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = focus or tgt
    c["tgt"] = tgt.name
    return c, tgt

def cam_move(c, tgt, f0, f1, p0, p1, t0, t1, kind="inout", shake=None, lens=None, roll=None, tgt_obj_follow=None):
    """f0..f1 oralig'ida kamera p0->p1, nishon t0->t1. shake = [(a, b, amp)] silkinish oraliqlari.
    lens = (l0, l1, kind) — crash zoom. roll = (r0, r1) gradus."""
    rnd = random.Random(f0 * 7 + 3)
    p0, p1, t0, t1 = map(Vector, (p0, p1, t0, t1))
    for f in range(f0, f1 + 1):
        u = ease((f - f0) / max(1, f1 - f0), kind)
        p = p0.lerp(p1, u); q = t0.lerp(t1, u)
        for a, b, amp in (shake or []):
            if a <= f <= b:
                k = amp * (1 - (f - a) / max(1, b - a + 1)) ** 1.5
                p = p + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        c.location = p; c.keyframe_insert("location", frame=f)
        if tgt_obj_follow is None:
            tgt.location = q; tgt.keyframe_insert("location", frame=f)
        if lens:
            l0, l1, lk = lens; c.data.lens = l0 + (l1 - l0) * ease((f - f0) / max(1, f1 - f0), lk)
            c.data.keyframe_insert("lens", frame=f)
    if roll:
        # TRACK_TO bilan roll: kamera ustiga yana bir burilish — "up" o'qini o'zgartirish o'rniga ota-bo'sh ob'ekt aylanmaydi;
        pass

# ---------------- procedural samolyot ("Comet", 1950-yillar) ----------------
def comet_profile(x, L=28.0, Rr=1.5):
    """fyuzelyaj radiusi va markaz balandligi (burun x=0, dum x=L)."""
    x = max(0.0, min(L, x))
    if x < 4.5:
        t = x / 4.5; r = Rr * (1 - (1 - t) ** 2.2) ** 0.5; zc = -0.25 * (1 - t) ** 2
    elif x < 19.5:
        r = Rr; zc = 0.0
    else:
        t = (x - 19.5) / (L - 19.5); r = Rr - (Rr - 0.28) * t ** 1.25; zc = 0.95 * t ** 1.6
    return max(r, 0.02), zc

def build_fuselage(name, m, x0=0.0, x1=28.0, split=None, seed=4, ring_dx=0.2, seg=56):
    """Aylanma jism. split=(xc, side): xc atrofida tishsimon kesim, side='front' yoki 'rear'."""
    rnd = random.Random(seed)
    jag = [rnd.uniform(-0.45, 0.45) for _ in range(seg)]
    jag = [(jag[i] + jag[i - 1] + jag[(i + 1) % seg]) / 3 * 1.6 for i in range(seg)]
    bm = bmesh.new(); rings = []
    n = int((x1 - x0) / ring_dx) + 1
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1); r, zc = comet_profile(x)
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            ring.append(bm.verts.new((x, r * math.cos(a), zc + r * math.sin(a))))
        rings.append(ring)
    for i in range(n - 1):
        for j in range(seg):
            k = (j + 1) % seg
            f = bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    if split:
        xc, side = split
        dead = []
        for f in bm.faces:
            c = f.calc_center_median(); a = math.atan2(c.z, c.y) % (2 * math.pi)
            j = int(a / (2 * math.pi) * seg) % seg
            front = c.x < xc + jag[j]
            if (side == "front") != front: dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.faces and (bm.faces[len(bm.faces) // 2].normal.dot(bm.faces[len(bm.faces) // 2].calc_center_median() - Vector((bm.faces[len(bm.faces) // 2].calc_center_median().x, 0, 0))) < 0):
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    o = mesh_obj(name, bm, m); smooth(o)
    # analitik normallar: kesim chegarasida soyalanish sinmasin
    nrm = []
    for v in o.data.vertices:
        x = v.co.x; r0, z0 = comet_profile(x - 0.01); r1, z1 = comet_profile(x + 0.01)
        dr, dz = (r1 - r0) / 0.02, (z1 - z0) / 0.02
        r, zc = comet_profile(x); a = math.atan2(v.co.z - zc, v.co.y)
        nrm.append(Vector((-dr - dz * math.sin(a), math.cos(a), math.sin(a))).normalized())
    o.data.normals_split_custom_set_from_vertices(nrm)
    return o

def wing_mesh(name, root_le, root_te, tip_le, tip_te, y0, y1, z0, z1, t0, t1, m, side=1):
    bm = bmesh.new()
    def sec(le, te, y, z, t):
        ch = te - le
        prof = [(0.0, 0.0), (0.06, 0.55), (0.3, 1.0), (0.7, 0.6), (1.0, 0.05), (0.7, -0.35), (0.3, -0.5), (0.06, -0.35)]
        return [bm.verts.new((le + ch * u, y * side, z + t * h * 0.5)) for u, h in prof]
    a = sec(root_le, root_te, y0, z0, t0); b = sec(tip_le, tip_te, y1, z1, t1)
    k = len(a)
    for i in range(k):
        j = (i + 1) % k; bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(a[::-1]); bm.faces.new(b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, m); smooth(o)
    o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o

def comet_livery(name):
    """yuqori oq, deraza ostida ko'k chiziq, pastki qism silliq alyumin (ob'ekt Z bo'yicha) + panel chiziqlari."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; g = G(nt); b = nt.nodes["Principled BSDF"]
    x, y, z = g.objxyz("Object")
    white = g.maprange(z, 0.12, 0.16, 0, 1)
    blue = g.mul(g.maprange(z, -0.32, -0.28, 0, 1), g.maprange(z, -0.06, -0.02, 1, 0))
    col = g.mixcol(white, (0.62, 0.64, 0.66), (0.86, 0.87, 0.88))
    col = g.mixcol(blue, col, (0.02, 0.09, 0.3))
    g.L.new(col, b.inputs["Base Color"])
    g.L.new(g.mul(g.sub(1, white), g.sub(1, blue)), b.inputs["Metallic"])
    b.inputs["Roughness"].default_value = 0.28; b.inputs["Coat Weight"].default_value = 0.4
    br = nt.nodes.new("ShaderNodeTexBrick"); tc = nt.nodes.new("ShaderNodeTexCoord")
    g.L.new(tc.outputs["Object"], br.inputs["Vector"]); br.inputs["Scale"].default_value = 0.9
    br.inputs["Mortar Size"].default_value = 0.004; br.inputs["Brick Width"].default_value = 1.6; br.inputs["Row Height"].default_value = 0.6
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.004
    g.L.new(br.outputs["Fac"], bp.inputs["Height"]); g.L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def build_comet(prefix, M, window="square", split_x=12.0, wings=True):
    """Kumush 4 dvigatelli 1950-yillar reaktiv yo'lovchi samolyoti. Burun -X ga qaragan (x=0), dum +X (28 m).
    Qaytaradi: root, front_root, rear_root, window_list."""
    root = empty(prefix + "_root"); sx = split_x or 12.0
    fr = empty(prefix + "_front", (sx, 0, 0), parent=root); rr = empty(prefix + "_rear", (sx, 0, 0), parent=root)
    liv = M["livery"]
    f1 = build_fuselage(prefix + "_fus_f", liv, split=(split_x, "front") if split_x else None); par(f1, fr)
    if split_x:
        f2 = build_fuselage(prefix + "_fus_r", liv, split=(split_x, "rear")); par(f2, rr)
    split_x = split_x or 99.0
    # kokpit oynalari
    for s in (-1, 1):
        o = box(prefix + "_cockpit", (0.55, 0.05, 0.28), (2.75, s * 0.86, 0.72), M["darkglass"], 0.03, rot=(s * 38, 0, s * -12)); par(o, fr)
    o = box(prefix + "_cockpit_c", (0.5, 0.7, 0.05), (2.55, 0, 0.98), M["darkglass"], 0.03, rot=(0, -28, 0)); par(o, fr)
    # derazalar (to'rtburchak, kichik burchak radiusi)
    wins = []
    for s in (-1, 1):
        for i in range(13):
            x = 5.6 + i * 1.05
            ww = 0.44 if window == "square" else 0.36; wh = 0.44 if window == "square" else 0.5
            tl = math.degrees(math.asin(0.24 / 1.5)) * -s
            fr_o = box(prefix + "_wframe", (ww + 0.07, 0.01, wh + 0.07), (x, s * 1.497, 0.237), M["alu"], 0.012, rot=(tl, 0, 0))
            gl = box(prefix + "_win", (ww, 0.01, wh), (x, s * 1.503, 0.238), M["darkglass"], 0.03 if window == "square" else 0.17, rot=(tl, 0, 0))
            for o in (fr_o, gl): par(o, fr if x < split_x else rr)
            wins.append((x, s, gl))
    if wings:
        for s in (-1, 1):
            w = wing_mesh(prefix + "_wing", 9.4, 16.2, 15.4, 17.6, 1.1, 17.0, -0.85, -0.35, 0.75, 0.16, M["alu"], s); par(w, fr)
            for yy in (2.0, 2.95):
                it = sphere(prefix + "_intake", 0.3, (9.55, s * yy, -0.82), M["black"], scale=(0.6, 1.5, 0.95)); par(it, fr)
                ex = cyl(prefix + "_exhaust", 0.27, 0.6, (16.35, s * yy, -0.82), M["exhaust"], rot=(0, 90, 0), verts=24); par(ex, fr)
    for s in (-1, 1):
            hs = wing_mesh(prefix + "_hstab", 23.6, 27.2, 26.4, 27.9, 0.3, 5.4, 0.55, 0.75, 0.3, 0.1, M["alu"], s); par(hs, rr)
    if True:  # vertikal stabilizator
        bm = bmesh.new()
        prof = [(0.0, 0.0), (0.1, 0.5), (0.4, 1.0), (1.0, 0.0), (0.4, -1.0), (0.1, -0.5)]
        a = [bm.verts.new((22.2 + 5.6 * u, 0.13 * h, 0.75)) for u, h in prof]
        b = [bm.verts.new((26.1 + 2.1 * u, 0.05 * h, 4.9)) for u, h in prof]
        for i in range(len(a)):
            j = (i + 1) % len(a); bm.faces.new((a[i], a[j], b[j], b[i]))
        bm.faces.new(a[::-1]); bm.faces.new(b); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        fin = mesh_obj(prefix + "_fin", bm, M["livery_fin"]); smooth(fin); par(fin, rr)
    return root, fr, rr, wins

# ---------------- kuch chiziqlari (rentgen) shader ----------------
def stress_material(name, shape="square", a=0.25):
    """Panel materiali: metall + emission (kuch oqimi chiziqlari va kuchlanish issiqlik xaritasi).
    Boshqaruv: 'P' (bosim 0..1), 'T' (oqim fazasi), 'HOT' (burchak kuchlanishi koeffitsienti), 'GLOW' (umumiy yorqinlik)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; g = G(nt); b = nt.nodes["Principled BSDF"]
    P = g.value("P", 0.3).outputs[0]; T = g.value("T", 0.0).outputs[0]
    HOT = g.value("HOT", 1.0).outputs[0]; GLOW = g.value("GLOW", 1.0).outputs[0]
    x, y, z = g.objxyz("Object")
    xn = g.div(x, a); yn = g.div(y, a)
    if shape == "square":
        p = 10.0
        rr = g.pw(g.add(g.pw(g.ab(xn), p), g.pw(g.ab(yn), p)), 1.0 / p)
    else:
        rr = g.sqrt(g.add(g.mul(xn, xn), g.mul(yn, yn)))
    rr = g.mx(rr, 1.0)
    # oqim funksiyasi: psi = y (1 - 1/r^2) -> chiziqlar teshikni aylanib o'tadi
    psi = g.mul(yn, g.sub(1.0, g.div(1.0, g.mul(rr, rr))))
    d = g.ab(g.sub(g.fr(g.mul(psi, 3.2)), 0.5))
    line = g.maprange(d, 0.0, 0.11, 1.0, 0.0)
    dash = g.add(0.35, g.mul(0.65, g.maprange(g.sin(g.sub(g.mul(xn, 5.0), T)), -0.2, 1.0, 0.0, 1.0)))
    flow = g.mul(line, dash)
    if shape == "square":
        dc = g.sqrt(g.add(g.pw(g.sub(g.ab(xn), 0.93), 2.0), g.pw(g.sub(g.ab(yn), 0.93), 2.0)))
        hot = g.mul(g.exp(g.mul(dc, -7.0)), HOT)
        hot = g.add(hot, g.mul(0.12, g.exp(g.mul(g.sub(rr, 1.0), -3.0))))
    else:
        hot = g.mul(0.28, g.exp(g.mul(g.sub(rr, 1.0), -1.6)))
    s = g.add(0.08, g.mul(hot, g.add(0.35, P)))
    col = g.ramp(s, [(0.0, (0.0, 0.08, 0.5)), (0.18, (0.0, 0.55, 1.0)), (0.36, (0.05, 1.0, 0.45)),
                     (0.55, (1.0, 0.95, 0.1)), (0.75, (1.0, 0.35, 0.0)), (1.0, (1.0, 0.03, 0.02))])
    strength = g.mul(GLOW, g.add(g.mul(0.35, g.add(0.4, P)), g.mul(flow, 2.2)))
    strength = g.add(strength, g.mul(g.mul(hot, P), 3.0))
    g.L.new(col, b.inputs["Emission Color"]); g.L.new(strength, b.inputs["Emission Strength"])
    b.inputs["Base Color"].default_value = (0.32, 0.36, 0.42, 1); b.inputs["Metallic"].default_value = 0.85
    b.inputs["Roughness"].default_value = 0.38
    return m

def panel_with_hole(name, m, shape="square", a=0.25, size=2.6, thick=0.02, rivet_m=None):
    """XY tekislikda panel (teshik markazi 0,0), keyin X atrofida 90° buriladi -> yuzi -Y ga."""
    bm = bmesh.new(); n = 160
    for i in range(n + 1):
        for j in range(n + 1):
            bm.verts.new((-size / 2 + size * i / n, -size / 2 + size * j / n, 0))
    bm.verts.ensure_lookup_table()
    V = bm.verts
    for i in range(n):
        for j in range(n):
            bm.faces.new((V[i * (n + 1) + j], V[(i + 1) * (n + 1) + j], V[(i + 1) * (n + 1) + j + 1], V[i * (n + 1) + j + 1]))
    def inside(px, py):
        if shape == "square": return (abs(px / a) ** 10 + abs(py / a) ** 10) ** 0.1 < 1.0
        return (px * px + py * py) ** 0.5 < a
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if inside(*f.calc_center_median().xy)], context="FACES")
    # teshik chetini aniq shaklga tortish
    for v in bm.verts:
        if not v.is_boundary or abs(v.co.x) > size / 2 - 1e-4 or abs(v.co.y) > size / 2 - 1e-4: continue
        x, y = v.co.x, v.co.y; r = math.hypot(x, y) or 1
        if shape == "square":
            t = (abs(x / a) ** 10 + abs(y / a) ** 10) ** 0.1; v.co.x, v.co.y = x / t, y / t
        else:
            v.co.x, v.co.y = x / r * a, y / r * a
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    o = mesh_obj(name, bm, m)
    s = o.modifiers.new("sol", "SOLIDIFY"); s.thickness = thick; s.offset = 1
    o.rotation_euler = (R(90), 0, 0)
    if rivet_m:
        bm = bmesh.new()
        pts = []
        off = a + 0.07
        k = 14
        for i in range(k):
            t = -off + 2 * off * i / (k - 1)
            pts += [(t, off), (t, -off), (off, t), (-off, t)] if shape == "square" else []
        if shape != "square":
            pts += [(off * math.cos(2 * math.pi * i / 40), off * math.sin(2 * math.pi * i / 40)) for i in range(40)]
        for i in range(24):
            t = -size / 2 + 0.05 + (size - 0.1) * i / 23
            pts += [(t, size / 2 - 0.05), (t, -size / 2 + 0.05), (size / 2 - 0.05, t), (-size / 2 + 0.05, t)]
        for px, py in pts:
            r = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.009)
            bmesh.ops.scale(bm, vec=(1, 1, 0.45), verts=r["verts"])
            bmesh.ops.translate(bm, vec=(px, py, thick), verts=r["verts"])
        rv = mesh_obj(name + "_rivets", bm, rivet_m); smooth(rv); rv.parent = o
    return o

def crack_strip(name, m, start, direction, length=0.42, width=0.007, seed=2, segs=40):
    """Zigzag yoriq lentasi (XY tekislik, UV u = 0..1 uzunlik bo'yicha)."""
    rnd = random.Random(seed); bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    d = Vector(direction).normalized(); nrm = Vector((-d.y, d.x)); pts = []
    p = Vector(start); off = 0.0
    for i in range(segs + 1):
        t = i / segs; off = off * 0.5 + rnd.uniform(-1, 1) * 0.012
        pts.append((Vector(start) + d * length * t + nrm * off, t))
    L, Rr = [], []
    for q, t in pts:
        w = width * (1 - 0.85 * t)
        L.append(bm.verts.new((q.x + nrm.x * w, q.y + nrm.y * w, 0))); Rr.append(bm.verts.new((q.x - nrm.x * w, q.y - nrm.y * w, 0)))
    for i in range(segs):
        f = bm.faces.new((L[i], Rr[i], Rr[i + 1], L[i + 1]))
        for lp, (vv, tt) in zip(f.loops, ((0, i), (1, i), (1, i + 1), (0, i + 1))):
            lp[uv].uv = (tt / segs, vv)
    return mesh_obj(name, bm, m)

def crack_material(name):
    """Yoriq: PROG gacha ko'rinadi, uchi to'q sariq yonadi."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; g = G(nt); b = nt.nodes["Principled BSDF"]
    PROG = g.value("PROG", 0.0).outputs[0]
    uvn = nt.nodes.new("ShaderNodeUVMap"); s = nt.nodes.new("ShaderNodeSeparateXYZ"); g.L.new(uvn.outputs[0], s.inputs[0])
    u = s.outputs[0]
    vis_ = g.math("LESS_THAN", u, PROG)
    tip = g.exp(g.mul(g.ab(g.sub(PROG, u)), -45.0))
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1); b.inputs["Roughness"].default_value = 0.9
    b.inputs["Emission Color"].default_value = (1.0, 0.25, 0.02, 1)
    g.L.new(g.mul(tip, 18.0), b.inputs["Emission Strength"])
    g.L.new(vis_, b.inputs["Alpha"])
    return m

# ---------------- bulutlar ----------------
def cloud_material(name, scale=0.004, thresh=0.52, col=(1, 1, 1)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; g = G(nt); b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "MAP"
    g.L.new(tc.outputs["Object"], mp.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.62; g.L.new(mp.outputs[0], nz.inputs["Vector"])
    a = g.maprange(nz.outputs["Fac"], thresh, thresh + 0.12, 0.0, 1.0)
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 1.0
    b.inputs["Subsurface Weight"].default_value = 0.0
    sh = g.maprange(nz.outputs["Fac"], thresh, thresh + 0.3, 0.55, 1.0)
    g.L.new(g.mixcol(sh, (0.55, 0.6, 0.7), col), b.inputs["Base Color"])
    g.L.new(a, b.inputs["Alpha"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 8.0
    g.L.new(nz.outputs["Fac"], bp.inputs["Height"]); g.L.new(bp.outputs[0], b.inputs["Normal"])
    return m
