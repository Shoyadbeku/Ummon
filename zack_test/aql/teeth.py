# "Aql tishlari" uchun procedural modellar: tish (emal + dentin + pulpa qatlamlari), milk, jag' suyagi kesimi,
# kista, ushoqlar, yoriqlar. Masshtab: 10x (tish toji ~0.1 m), kesim tekisligi y=0 (kamera -Y tomonda).
import bpy, math, random
from mathutils import Vector

R = math.radians
def sc(): return bpy.context.scene

def link(o, parent=None):
    sc().collection.objects.link(o)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); e.location = loc; e.empty_display_size = 0.01
    return link(e, parent)

def _active(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)

def _join(objs, name):
    _active(objs[0])
    for o in objs[1:]: o.select_set(True)
    bpy.ops.object.join(); o = bpy.context.object; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o

def _apply(o, mod):
    _active(o); bpy.ops.object.modifier_apply(modifier=mod.name)

def remesh(o, voxel, smooth=4):
    m = o.modifiers.new("rm", "REMESH"); m.mode = "VOXEL"; m.voxel_size = voxel; m.use_smooth_shade = True; _apply(o, m)
    if smooth:
        s = o.modifiers.new("sm", "SMOOTH"); s.iterations = smooth; s.factor = 0.8; _apply(o, s)
    for p in o.data.polygons: p.use_smooth = True
    return o

def _uv(r, loc, scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.scale = scale; return o

def _cone(r1, r2, depth, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=[R(a) for a in rot])
    return bpy.context.object

# ======================================================================
# MATERIALLAR
# ======================================================================
def _bsdf(m):
    return m.node_tree.nodes["Principled BSDF"]

def enamel_material(name="enamel"):
    """Toj: oq-sadaf emal (yaltiroq); ildiz (lokal z < 0): sarg'ish sement. Object koordinatasi bo'yicha."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = _bsdf(m)
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -0.006; mr.inputs[2].default_value = 0.008
    L.new(sp.outputs[2], mr.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; L.new(tc.outputs["Object"], nz.inputs[0])
    cr = N.new("ShaderNodeMix"); cr.data_type = "RGBA"
    cr.inputs[6].default_value = (0.78, 0.66, 0.45, 1); cr.inputs[7].default_value = (0.93, 0.91, 0.84, 1)
    L.new(mr.outputs[0], cr.inputs[0])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.blend_type = "MULTIPLY"; c2.inputs[0].default_value = 0.12
    L.new(cr.outputs[2], c2.inputs[6]); L.new(nz.outputs["Color"], c2.inputs[7]); L.new(c2.outputs[2], b.inputs["Base Color"])
    ro = N.new("ShaderNodeMapRange"); ro.inputs[3].default_value = 0.55; ro.inputs[4].default_value = 0.14
    L.new(mr.outputs[0], ro.inputs[0]); L.new(ro.outputs[0], b.inputs["Roughness"])
    L.new(mr.outputs[0], b.inputs["Coat Weight"]); b.inputs["Coat Roughness"].default_value = 0.08
    b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.5)
    return m

def plain(name, col, rough=0.5, sss=0.0, sss_scale=0.01, coat=0.0, emit=0.0, emit_col=None, noise=0.0, nscale=40.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = _bsdf(m)
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = sss_scale
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.05
    if noise:
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = nscale
        nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = noise
        mx.inputs[6].default_value = (*col, 1); L.new(nz.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
        bm = N.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.15; L.new(nz.outputs["Fac"], bm.inputs["Height"])
        L.new(bm.outputs[0], b.inputs["Normal"])
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    return m

def glow_value(m, name="glow", v=0.0, col=None):
    """Principled emission kuchini 'glow' Value tuguniga bog'laydi (P.mat_value bilan keyframe)."""
    N = m.node_tree.nodes; L = m.node_tree.links; b = _bsdf(m)
    val = N.new("ShaderNodeValue"); val.name = name; val.outputs[0].default_value = v
    if col: b.inputs["Emission Color"].default_value = (*col, 1)
    L.new(val.outputs[0], b.inputs["Emission Strength"]); return m

def mat_value(m, name, f, v):
    n = m.node_tree.nodes[name]; n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)

def bone_material(name="jaw_bone"):
    """Jag' suyagi: kesimda g'ovak (spongiy) tuzilish: krem rang, g'ovaklar ichi qizg'ish ilik."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = _bsdf(m)
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 140
    vo.inputs["Randomness"].default_value = 1.0
    dn = N.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 18; dn.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], dn.inputs[0])
    dmix = N.new("ShaderNodeMix"); dmix.data_type = "VECTOR"; dmix.inputs[0].default_value = 0.035
    L.new(tc.outputs["Object"], dmix.inputs[4]); L.new(dn.outputs["Color"], dmix.inputs[5]); L.new(dmix.outputs[1], vo.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 25; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.02; mr.inputs[2].default_value = 0.09
    L.new(vo.outputs["Distance"], mr.inputs[0])                        # 0 = trabekula chetida (suyak), 1 = g'ovak ichi
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L.new(mr.outputs[0], inv.inputs[1])
    cr = N.new("ShaderNodeMix"); cr.data_type = "RGBA"
    cr.inputs[6].default_value = (0.32, 0.07, 0.05, 1); cr.inputs[7].default_value = (0.82, 0.74, 0.58, 1)
    L.new(inv.outputs[0], cr.inputs[0])
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.blend_type = "MULTIPLY"; c2.inputs[0].default_value = 0.45
    L.new(cr.outputs[2], c2.inputs[6]); L.new(nz.outputs["Color"], c2.inputs[7]); L.new(c2.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    bm = N.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.6; bm.inputs["Distance"].default_value = 0.004
    L.new(inv.outputs[0], bm.inputs["Height"]); L.new(bm.outputs[0], b.inputs["Normal"])
    b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Scale"].default_value = 0.005
    return m

# ======================================================================
# TISH
# ======================================================================
def tooth_shapes(name, w=0.1, h=0.075, root_len=0.13, roots=2, seed=0, premolar=False):
    """Tishning tashqi (emal+sement), ichki (dentin) va pulpa meshlari; lokal z=0 — bo'yin (milk chizig'i)."""
    rnd = random.Random(seed)
    p = []
    bw = w * (0.8 if premolar else 1.0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h * 0.45)); o = bpy.context.object
    o.scale = (bw * 0.84, w * 0.8, h * 0.6); p.append(o)                  # toj: yumaloqlangan quti (remesh+smooth)
    p.append(_uv(1, (0, 0, h * 0.42), (bw * 0.53, w * 0.5, h * 0.4)))      # bo'rtiq yon devorlar
    cus = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if not premolar else [(0, -1), (0, 1)]
    for sx, sy in cus:
        p.append(_uv(w * 0.23, (sx * bw * 0.22 + rnd.uniform(-1, 1) * w * 0.015, sy * w * 0.2, h * 0.74), (1, 1, 0.72)))
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=h * 0.5, location=(0, 0, h * 0.05))
    o = bpy.context.object; o.scale = (bw * 0.42, w * 0.4, 1); p.append(o)
    rx = [-0.24, 0.24] if roots == 2 else [0.0]
    for i, x in enumerate(rx):
        tilt = -(x / 0.24) * 7 if roots == 2 else 0
        L_ = root_len * rnd.uniform(0.92, 1.05)
        p.append(_cone(w * 0.05, w * (0.21 if roots == 2 else 0.26), L_, (x * bw - math.sin(R(tilt)) * L_ * 0.5, 0, -L_ * 0.5 + h * 0.05),
                       (0, tilt, 0)))
    outer = remesh(_join(p, name + "_outer"), w * 0.02, 12)
    inner = outer.copy(); inner.data = outer.data.copy(); inner.name = name + "_dentin"; link(inner)
    d = inner.modifiers.new("shrink", "DISPLACE"); d.strength = -w * 0.07; d.mid_level = 0; _apply(inner, d)
    remesh(inner, w * 0.018, 3)               # displace'dan keyingi o'z-o'zini kesishlarni tozalaydi (aks holda boolean ishlamaydi)
    # pulpa: kamera + kanallar
    q = [_uv(1, (0, 0, h * 0.22), (bw * 0.22, w * 0.18, h * 0.2))]
    for i, x in enumerate(rx):
        tilt = -(x / 0.24) * 7 if roots == 2 else 0
        L_ = root_len * 0.9
        q.append(_cone(w * 0.012, w * 0.06, L_, (x * bw * 0.95 - math.sin(R(tilt)) * L_ * 0.5, 0, -L_ * 0.5 + h * 0.1), (0, tilt, 0)))
    pulp = remesh(_join(q, name + "_pulp"), w * 0.012, 3)
    return outer, inner, pulp

def cutter(name, y_front, size=4.0):
    """y < y_front hududini kesib tashlaydigan quti (render'da ko'rinmaydi)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y_front - size / 2, 0)); o = bpy.context.object
    o.name = name; o.scale = (size, size, size); o.hide_render = True; o.display_type = "WIRE"
    return o

def bool_diff(o, cut_obj, name="cut", solver="EXACT"):
    m = o.modifiers.new(name, "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = cut_obj; m.solver = solver
    return m

def key_show(mod, ranges, end):
    """Modifierni faqat ranges ichida render'da yoqadi."""
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        mod.show_render = any(a <= f <= b for a, b in ranges); mod.keyframe_insert("show_render", frame=f)

def jagged_sphere(name, r, loc, seed=1, amt=0.25):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=loc); o = bpy.context.object; o.name = name
    rnd = random.Random(seed)
    for v in o.data.vertices: v.co *= 1 + rnd.uniform(-amt, amt)
    return o

def crumb(name, r, mat, seed):
    rnd = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r); o = bpy.context.object; o.name = name
    for v in o.data.vertices: v.co *= 1 + rnd.uniform(-0.35, 0.35)
    o.scale = (rnd.uniform(0.7, 1.3), rnd.uniform(0.7, 1.3), rnd.uniform(0.5, 1.0))
    o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return o

def crack_curve(name, pts, depth, mat, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new(name, cu); link(o, parent); cu.materials.append(mat)
    return o

def jag_path(a, b, n, amp, rnd, axis=(0, 1, 0)):
    a = Vector(a); b = Vector(b); d = b - a; perp = d.cross(Vector(axis)).normalized()
    pts = []
    for i in range(n + 1):
        t = i / n; off = 0 if i in (0, n) else rnd.uniform(-amp, amp)
        pts.append(tuple(a + d * t + perp * off))
    return pts
