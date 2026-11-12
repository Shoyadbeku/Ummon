# "G'oz terisi" videosi uchun yordamchilar (samolyot/parts.py dan) + procedural qismlar (Blender 5.2, bpy)
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


# =====================================================================================
# Geometry Nodes yordamchilari (Blender 5.2)
class GN:
    """Kichik GN quruvchi: g = GN('nom'); g.inp('Lift', 'NodeSocketFloat', 0.3) ..."""
    def __init__(self, name):
        self.ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
        self.N = self.ng.nodes; self.L = self.ng.links
        self.ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        self.ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        self.gi = self.N.new("NodeGroupInput"); self.go = self.N.new("NodeGroupOutput")
        self.inputs = {}
    def inp(self, name, stype="NodeSocketFloat", default=0.0):
        s = self.ng.interface.new_socket(name, in_out="INPUT", socket_type=stype)
        try: s.default_value = default
        except Exception: pass
        self.inputs[name] = s.identifier
        return self.gi.outputs[name]
    def node(self, typ, **kw):
        n = self.N.new(typ)
        for k, v in kw.items():
            if k.startswith("_"): setattr(n, k[1:], v)
            else: self.set(n.inputs[k], v)
        return n
    def set(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket): self.L.new(v, sock)
        elif v is not None: sock.default_value = v
    def link(self, a, b): self.L.new(a, b)
    def math(self, op, a, b=None):
        n = self.N.new("ShaderNodeMath"); n.operation = op
        self.set(n.inputs[0], a)
        if b is not None: self.set(n.inputs[1], b)
        return n.outputs[0]
    def vmath(self, op, a, b=None, scale=None):
        n = self.N.new("ShaderNodeVectorMath"); n.operation = op
        self.set(n.inputs[0], a)
        if b is not None: self.set(n.inputs[1], b)
        if scale is not None: self.set(n.inputs["Scale"], scale)
        return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Vector"]
    def rand(self, lo, hi, seed=0, vec=False):
        n = self.N.new("FunctionNodeRandomValue"); n.data_type = "FLOAT_VECTOR" if vec else "FLOAT"
        n.inputs["Min"].default_value = lo; n.inputs["Max"].default_value = hi
        n.inputs["Seed"].default_value = seed; return n.outputs[0]
    def xyz(self, x, y, z):
        n = self.N.new("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)): self.set(n.inputs[i], v)
        return n.outputs[0]
    def sep(self, v):
        n = self.N.new("ShaderNodeSeparateXYZ"); self.set(n.inputs[0], v); return n.outputs
    def out(self, geo): self.L.new(geo, self.go.inputs[0])

def gn_modifier(obj, g, values=None, name="GN"):
    mod = obj.modifiers.new(name, "NODES"); mod.node_group = g.ng
    for k, v in (values or {}).items(): gn_set(mod, g, k, v)
    return mod

def _gn_sock(mod, g, name):
    ident = g.inputs[name]
    try:
        return getattr(mod.properties.inputs, ident)          # Blender 5.2 (CLAUDE.md)
    except Exception:
        return None

def gn_set(mod, g, name, v, frame=None):
    s = _gn_sock(mod, g, name)
    if s is not None:
        s.value = v
        if frame is not None: s.keyframe_insert("value", frame=frame)
    else:
        mod[g.inputs[name]] = v
        if frame is not None: mod.keyframe_insert(f'["{g.inputs[name]}"]', frame=frame)

def hair_strand_mesh(name, length=1.0, r0=0.03, r1=0.004, bend=0.12, seg=6, sides=5):
    """+Z bo'ylab egilgan, uchiga qarab ingichkalashgan tuk (asosi 0 da)."""
    bm = bmesh.new(); rings = []
    for i in range(seg + 1):
        t = i / seg; r = r0 + (r1 - r0) * t ** 0.8
        cx = bend * length * t * t; cz = length * t
        rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * j / sides), r * math.sin(2 * math.pi * j / sides), cz))
                      for j in range(sides)])
    for i in range(seg):
        for j in range(sides):
            k = (j + 1) % sides; bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    bm.faces.new(rings[0][::-1]); tip = bm.verts.new((bend * length, 0, length * 1.03))
    for j in range(sides): bm.faces.new((rings[-1][j], rings[-1][(j + 1) % sides], tip))
    o = mesh_obj(name, bm); smooth(o); return o

def fur_gn(name, hair_obj, density=12000.0, length=0.05, max_y=1.45, down_axis=(0.0, -1.0, 0.0), spread_x=0.8, u=100.0):
    """Skinlangan mesh uchun jun. rest_position ustida taqsimlanadi (silkinmaydi), deformatsiyalangan joyga ko'chiriladi.
    Mahalliy o'qlar (Mixamo mesh): +Y tepa. Lift 0 = jun yotgan, 1 = tik."""
    g = GN(name)
    # u: mesh birligi (Mixamo FBX: sm => u=100). density 1/m^2, length m, max_y m
    lift = g.inp("Lift", default=0.25); length_s = g.inp("Length", default=length * u); dens = g.inp("Density", default=density / u / u)
    max_y = max_y * u; spread_x = spread_x / u
    pos = g.node("GeometryNodeInputPosition").outputs[0]; nor = g.node("GeometryNodeInputNormal").outputs[0]
    st1 = g.node("GeometryNodeStoreNamedAttribute", _data_type="FLOAT_VECTOR", _domain="POINT", Geometry=g.gi.outputs[0], Name="defpos")
    g.set(st1.inputs["Value"], pos)
    st2 = g.node("GeometryNodeStoreNamedAttribute", _data_type="FLOAT_VECTOR", _domain="POINT", Geometry=st1.outputs[0], Name="defnor")
    g.set(st2.inputs["Value"], nor)
    rp = g.node("GeometryNodeInputNamedAttribute", _data_type="FLOAT_VECTOR", Name="rest_position").outputs["Attribute"]
    sp = g.node("GeometryNodeSetPosition", Geometry=st2.outputs[0], Position=rp)
    ry = g.sep(g.node("GeometryNodeInputPosition").outputs[0])[1]
    selc = g.node("FunctionNodeCompare", _data_type="FLOAT", _operation="LESS_THAN", A=ry, B=max_y)
    dist = g.node("GeometryNodeDistributePointsOnFaces", _distribute_method="RANDOM", Mesh=sp.outputs[0], Selection=selc.outputs[0],
                  Density=dens, Seed=7)
    dpos = g.node("GeometryNodeInputNamedAttribute", _data_type="FLOAT_VECTOR", Name="defpos").outputs["Attribute"]
    dnor = g.node("GeometryNodeInputNamedAttribute", _data_type="FLOAT_VECTOR", Name="defnor").outputs["Attribute"]
    pts = g.node("GeometryNodeSetPosition", Geometry=dist.outputs["Points"], Position=dpos).outputs[0]
    N = g.vmath("NORMALIZE", dnor)
    # "pastga" yo'nalish: tana bo'ylab pastga, qo'llarda tashqariga (T-poza mahalliy X)
    px = g.sep(g.node("GeometryNodeInputPosition").outputs[0])[0]
    D = g.vmath("ADD", g.xyz(g.math("MULTIPLY", px, spread_x), 0, 0), down_axis)
    T = g.vmath("SUBTRACT", D, g.vmath("SCALE", N, scale=g.vmath("DOT_PRODUCT", D, N)))
    T = g.vmath("NORMALIZE", T)
    il = g.math("SUBTRACT", 1.0, lift)
    dirv = g.vmath("ADD", g.vmath("SCALE", T, scale=il), g.vmath("SCALE", N, scale=g.math("ADD", lift, 0.12)))
    dirv = g.vmath("ADD", dirv, g.rand((-0.35, -0.35, -0.35), (0.35, 0.35, 0.35), seed=3, vec=True))
    dirv = g.vmath("NORMALIZE", dirv)
    al = g.node("FunctionNodeAlignRotationToVector", _axis="Z", Vector=dirv)
    hi = g.node("GeometryNodeObjectInfo", Object=hair_obj); hi.transform_space = "ORIGINAL"
    sca = g.math("MULTIPLY", length_s, g.rand(0.55, 1.35, seed=5))
    sca = g.math("MULTIPLY", sca, g.math("ADD", 1.0, g.math("MULTIPLY", lift, 0.25)))
    inst = g.node("GeometryNodeInstanceOnPoints", Points=pts, Instance=hi.outputs["Geometry"], Rotation=al.outputs[0], Scale=sca)
    # instansiyalarga yuz/tana: random rang uchun
    j = g.node("GeometryNodeJoinGeometry"); g.link(inst.outputs[0], j.inputs[0]); g.link(g.gi.outputs[0], j.inputs[0])
    g.out(j.outputs[0])
    return g

def snow_gn(name, count=1500, size=(10, 10, 6), speed=0.9, radius=0.012, mat=None):
    """Qor: nuqtalar bulutidan pastga tushuvchi zarralar (Scene Time bilan, tsikl)."""
    g = GN(name)
    pts = g.node("GeometryNodePoints", Count=count, Radius=radius)
    rnd = g.rand((-size[0] / 2, -size[1] / 2, 0), (size[0] / 2, size[1] / 2, size[2]), seed=11, vec=True)
    t = g.node("GeometryNodeInputSceneTime").outputs["Seconds"]
    x, y, z = g.sep(rnd)
    sp = g.math("MULTIPLY", g.rand(0.6, 1.4, seed=2), speed)
    zz = g.math("SUBTRACT", z, g.math("MULTIPLY", t, sp))
    zz = g.math("FLOORED_MODULO", zz, size[2]) if True else zz
    ph = g.rand(0, 6.28, seed=4)
    xx = g.math("ADD", x, g.math("MULTIPLY", g.math("SINE", g.math("ADD", g.math("MULTIPLY", t, 1.3), ph)), 0.15))
    yy = g.math("ADD", y, g.math("MULTIPLY", t, 0.25))
    sp_ = g.node("GeometryNodeSetPosition", Geometry=pts.outputs[0], Position=g.xyz(xx, yy, zz))
    rad = g.node("GeometryNodeSetPointRadius", Points=sp_.outputs[0], Radius=g.math("MULTIPLY", g.rand(0.5, 1.5, seed=9), radius))
    geo = rad.outputs[0]
    if mat: geo = g.node("GeometryNodeSetMaterial", Geometry=geo, Material=mat).outputs[0]
    g.out(geo)
    return g

def skin_hair_gn(name, hair_obj, bump_h=0.2, tilt0=72.0, tilt1=12.0):
    """Teri makro uchun: ob'ekt vertekslari = follikulalar. Lift (0..1) tuklarni tiklaydi, Goose (0..1) asosini ko'taradi."""
    g = GN(name)
    lift = g.inp("Lift", default=0.0); goose = g.inp("Goose", default=0.0)
    pts = g.node("GeometryNodeMeshToPoints", Mesh=g.gi.outputs[0]).outputs[0]
    pos = g.node("GeometryNodeInputPosition").outputs[0]
    pts = g.node("GeometryNodeSetPosition", Geometry=pts, Offset=g.xyz(0, 0, g.math("MULTIPLY", goose, bump_h))).outputs[0]
    # har tuk o'z vaqtida: lift'ga kichik kechikish (to'lqin kabi)
    jit = g.rand(-0.12, 0.12, seed=21)
    lf = g.math("MINIMUM", 1.0, g.math("MAXIMUM", 0.0, g.math("ADD", lift, g.math("MULTIPLY", jit, g.math("SUBTRACT", 1.0, lift)))))
    a = g.math("ADD", math.radians(tilt0), g.math("MULTIPLY", lf, math.radians(tilt1 - tilt0)))
    a = g.math("ADD", a, g.rand(-0.15, 0.15, seed=22))
    yaw = g.rand(-0.35, 0.35, seed=23)
    e2r = g.node("FunctionNodeEulerToRotation"); g.set(e2r.inputs[0], g.xyz(0, a, yaw))
    hi = g.node("GeometryNodeObjectInfo", Object=hair_obj); hi.transform_space = "ORIGINAL"
    inst = g.node("GeometryNodeInstanceOnPoints", Points=pts, Instance=hi.outputs["Geometry"], Rotation=e2r.outputs[0],
                  Scale=g.rand(0.75, 1.25, seed=24))
    g.out(inst.outputs[0])
    return g

# =====================================================================================
# maxsus materiallar
def xray_mat(name, col=(0.25, 0.7, 1.0), strength=2.5, inner=0.04):
    """Rentgen: chekkalari yorqin, o'rtasi shaffof."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = N["Material Output"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; L.new(lw.outputs["Facing"], pw.inputs[0]); pw.inputs[1].default_value = 1.6
    ad = N.new("ShaderNodeMath"); ad.operation = "ADD"; L.new(pw.outputs[0], ad.inputs[0]); ad.inputs[1].default_value = inner
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(ad.outputs[0], mu.inputs[0]); mu.inputs[1].default_value = strength
    L.new(mu.outputs[0], em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    add = N.new("ShaderNodeAddShader"); L.new(tr.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs["Surface"])
    return m

def emit_mat(name, col, strength=5.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    e.name = "EM"
    m.node_tree.links.new(e.outputs[0], N["Material Output"].inputs["Surface"])
    return m

def thermal(m, ranges, kind="body"):
    """Materialga 'issiqlik kamerasi' ko'rinishini qo'shish: ranges oraliqlarida (CONSTANT kalit) emissiyaga o'tadi."""
    nt = m.node_tree; N = nt.nodes; L = nt.links
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    if not out.inputs["Surface"].links: return
    src = out.inputs["Surface"].links[0].from_socket
    cols = {"body": [(0.0, (0.9, 0.25, 0.02)), (0.45, (1.0, 0.75, 0.05)), (1.0, (1.0, 1.0, 0.75))],
            "fur": [(0.0, (0.55, 0.0, 0.25)), (0.5, (0.95, 0.25, 0.02)), (1.0, (1.0, 0.65, 0.05))],
            "cold": [(0.0, (0.0, 0.0, 0.08)), (0.6, (0.05, 0.05, 0.35)), (1.0, (0.2, 0.05, 0.5))]}[kind]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    ns = N.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 3.0
    mx = N.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"
    L.new(lw.outputs["Facing"], mx.inputs[0]); mx.inputs[1].default_value = -0.6; mx.inputs[2].default_value = 0.85
    mx2 = N.new("ShaderNodeMath"); mx2.operation = "MULTIPLY_ADD"; L.new(ns.outputs["Fac"], mx2.inputs[0])
    mx2.inputs[1].default_value = 0.3; L.new(mx.outputs[0], mx2.inputs[2])
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
    cr.elements[0].position = cols[0][0]; cr.elements[0].color = (*cols[0][1], 1)
    cr.elements[1].position = cols[-1][0]; cr.elements[1].color = (*cols[-1][1], 1)
    for p, c in cols[1:-1]:
        e = cr.elements.new(p); e.color = (*c, 1)
    L.new(mx2.outputs[0], ramp.inputs[0])
    em = N.new("ShaderNodeEmission"); L.new(ramp.outputs[0], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.6
    mix = N.new("ShaderNodeMixShader"); mix.name = "THERMAL"
    L.new(src, mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2]); L.new(mix.outputs[0], out.inputs["Surface"])
    fac = mix.inputs[0]
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        fac.default_value = 1.0 if any(a <= f <= b for a, b in ranges) else 0.0
        fac.keyframe_insert("default_value", frame=f)
    if nt.animation_data and nt.animation_data.action:
        for fc in all_fcurves(nt):
            for k in fc.keyframe_points: k.interpolation = "CONSTANT"
