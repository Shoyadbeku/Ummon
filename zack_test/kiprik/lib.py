# Umumiy yordamchilar (koz_qon.py dan ajratib olingan): materiallar, primitivlar, kamera, yorug'lik, ko'rinish kalitlari
import bpy, math, os, random, sys
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import mixchar as mc

R = math.radians
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = "/tmp/claude-0/assets/bk/"
def sc(): return bpy.context.scene

def link(o, parent=None):
    sc().collection.objects.link(o)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); e.location = loc; e.empty_display_size = 0.02
    return link(e, parent)

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return mc._fcurves(ad.action)

def interp(idb, mode="LINEAR", path=None):
    for fc in fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode

def vis(o, ranges, recursive=True):
    objs = [o] + (list(o.children_recursive) if recursive else [])
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def _m(N, L, op, a, b=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0]

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v
    return n

def key_value(m, name, f, v):
    n = m.node_tree.nodes[name]; n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, sss=0.0, coat=0.0, emit_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    return m

def bsdf(m): return m.node_tree.nodes["Principled BSDF"]

def pbr(name, folder, scale=1.0, tint=None, proj="BOX", coord="Object"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs[coord], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = proj; t.projection_blend = 0.25
        if non_color: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = img("diff.jpg")
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        L.new(d.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    else:
        L.new(d.outputs[0], b.inputs["Base Color"])
    r = img("rough.jpg", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def _smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(name, size, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s / 2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m); _smooth(o)
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m); _smooth(o)
    if parent: o.parent = parent
    return o

def uvsphere(name, r, loc, m, scale=(1, 1, 1), seg=32, ring=16, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m); _smooth(o)
    if parent: o.parent = parent
    return o

def plane(name, size, loc, m, rot=(0, 0, 0), parent=None, sub=0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    if sub:
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=sub); bpy.ops.object.mode_set(mode="OBJECT")
    if parent: o.parent = parent
    return o

def import_glb(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def import_ph(model, parent, loc=(0, 0, 0), rz=0.0, scale=1.0):
    root = empty(model + "_root", loc, parent); root.rotation_euler = (0, 0, R(rz)); root.scale = (scale,) * 3
    objs = import_glb(os.path.join(PH, model, model + ".gltf"), root)
    return root, objs

def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.001):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 600
    c = bpy.data.objects.new(name, d); sc().collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c

def shake(cam, f0, f1, amp, seed=1, rot=0.0):
    rnd = random.Random(seed)
    fc = [fc for fc in fcurves(cam) if fc.data_path == "location"]
    for f in range(f0, f1):
        base = Vector([c.evaluate(f) for c in sorted(fc, key=lambda c: c.array_index)]) if fc else cam.location.copy()
        k = amp * (1 - (f - f0) / (f1 - f0)) ** 2
        cam.location = base + Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("location", frame=f)

def lens_keys(cam, pairs):
    for f, l in pairs:
        cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None, kind="AREA"):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); sc().collection.objects.link(l)
    if kind == "AREA": l.data.size = size
    elif kind in ("POINT", "SPOT"): l.data.shadow_soft_size = size
    l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def bone_empty(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if tuple(loc) != (0, 0, 0):
        return empty(name + "_off", loc, e)
    return e

def at(root, f, loc, rz):
    root.location = loc; root.rotation_euler = (0, 0, R(rz))
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)

def soften(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.3
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.6
                    n.inputs["Coat Weight"].default_value = 0.0

def fade_mix(m, alpha_expr_node_out, N, L, surface_out):
    """Principled -> Transparent aralashmasi (Layer Weight bilan), Transmission'siz (CLAUDE.md tuzog'i)"""
    trn = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader")
    L.new(alpha_expr_node_out, ms.inputs[0]); L.new(trn.outputs[0], ms.inputs[1]); L.new(surface_out, ms.inputs[2])
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL"); L.new(ms.outputs[0], out.inputs["Surface"])
    return ms

def path_point(pts, u):
    """poliliniya bo'ylab yoy uzunligi parametri u (0..1) dagi nuqta"""
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    tot = sum(seg); d = max(0.0, min(1.0, u)) * tot
    for i, s in enumerate(seg):
        if d <= s or i == len(seg) - 1:
            t = d / s if s > 0 else 0
            return pts[i].lerp(pts[i + 1], min(1, t))
        d -= s
    return pts[-1]
