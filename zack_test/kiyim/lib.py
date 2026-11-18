# Yostiq videosi uchun yordamchilar (ogri/lib.py dan ko'chirilgan: material, kamera, yorug'lik, primitivlar, vis/key).
# Import qilinganda sahnani tozalaydi (read_factory_settings), shuning uchun eng birinchi import qilinadi.
import bpy, math, sys, os, random
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); ZT = os.path.dirname(HERE)
sys.path.insert(0, ZT)
import mixchar as mc
R = math.radians
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24

class P:
    @staticmethod
    def empty(name, loc=(0, 0, 0), parent=None):
        e = bpy.data.objects.new(name, None); e.location = loc; e.empty_display_size = 0.01
        sc.collection.objects.link(e)
        if parent: e.parent = parent
        return e
    @staticmethod
    def math_n(N, L, op, a=None, b=None, clamp=False, vec=False):
        n = N.new("ShaderNodeVectorMath" if vec else "ShaderNodeMath"); n.operation = op
        if not vec: n.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)) or (vec and isinstance(x, tuple)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0] if not vec or op not in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Value"]
    @staticmethod
    def mat_value(m, name, f, v):
        n = m.node_tree.nodes[name]; n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)


# ---------------- yordamchilar (quloq.py / aksirish.py dan) ----------------
empty = P.empty
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
    for x in objs:
        for fc in fcurves(x):
            if fc.data_path == "hide_render": fc.keyframe_points.clear()
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
    for x in objs: interp(x, "CONSTANT", "hide_render")

def mat(name, col, rough=0.5, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, trans=0.0, sss=0.0, sss_scale=None, emit_col=None, ior=1.45):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["IOR"].default_value = ior
    if sss_scale is not None: b.inputs["Subsurface Scale"].default_value = sss_scale
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1); b.inputs["Emission Strength"].default_value = emit
    return m

def pbr(name, folder, scale=1.0, tint=None, proj="BOX"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs[0])
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
    L.new(img("rough.jpg", True).outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def _par(o, parent):
    o.parent = parent
    bpy.context.view_layer.update(); o.matrix_parent_inverse = parent.matrix_world.inverted()

CAMS = {}
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.005):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "VERTICAL"; d.sensor_height = 24; d.clip_start = clip
    d.clip_end = 400
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)): d.dof.focus_distance = focus
        else: d.dof.focus_object = focus or target
    return c
def shot_cam(name, *a, **k):
    c = camera("cam_" + name, *a, **k); CAMS[name] = c; return c

def shake(cam, f0, f1, amp, seed=1, decay=True):
    rnd = random.Random(seed)
    for f in range(f0, f1):
        k = amp * ((1 - (f - f0) / (f1 - f0)) ** 2 if decay else 1.0)
        cam.delta_location = Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        cam.keyframe_insert("delta_location", frame=f)
    cam.delta_location = (0, 0, 0); cam.keyframe_insert("delta_location", frame=f1)

def lens_keys(cam, pairs):
    for f, l in pairs: cam.data.lens = l; cam.data.keyframe_insert("lens", frame=f)

def area(name, loc, size, col, keys, target=None, parent=None, shape=None, cam_vis=False):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.size = size; l.data.color = col; l.location = loc
    if shape: l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = shape
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    interp(l.data, "CONSTANT")
    if target is not None:
        t = l.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    l.visible_camera = cam_vis
    return l

def point(name, loc, r, col, keys, parent=None, const=True):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT")); sc.collection.objects.link(l)
    l.data.shadow_soft_size = r; l.data.color = col; l.location = loc
    if parent: l.parent = parent
    for f, e in keys: l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
    if const: interp(l.data, "CONSTANT")
    return l

def lights_for(ranges, energy):
    keys = [(1, 0)]
    for a, b in ranges: keys += [(a, energy), (b + 1, 0)]
    return keys

def ease(t): return t * t * (3 - 2 * t)
def lerp3(a, b_, t, e=True):
    t = ease(t) if e else t; return tuple(Vector(a).lerp(Vector(b_), t))

def child_of_bone(name, arm, bone, loc=(0, 0, 0)):
    e = empty(name)
    c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + bone
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    if any(loc): return empty(name + "_o", loc, e)
    return e

def value_node(m, name, v):
    n = m.node_tree.nodes.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = v; return n.outputs[0]
def val_key(m, name, f, v): P.mat_value(m, name, f, v)
def wpos(o, f, local=(0, 0, 0)):
    sc.frame_set(f); return o.matrix_world @ Vector(local)

def soften(meshes):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.35
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = 0.45
                    n.inputs["Coat Weight"].default_value = 0.0

def A_(f, inplace=True):
    a = mc.load_action(f, inplace); sc.render.fps = 24; return a
def strip(arm, act, start, src=None, speed=1.0, blend=6, bout=6, repeat=1.0):
    s = mc.add_strip(arm, act, start, src=src, speed=speed, blend=blend, hold=False, repeat=repeat)
    s.blend_out = bout; s.use_auto_blend = False
    return s
def place(root, f, loc, rot=0.0, scale=1.0):
    root.location = loc; root.rotation_euler = (0, 0, R(rot)); root.scale = (scale,) * 3
    for p in ("location", "rotation_euler", "scale"): root.keyframe_insert(p, frame=f)

def ray_down(objs, x, y, z0=3.0):
    """ob'ektlar ustidagi eng baland nuqta (x, y) da"""
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    for o in objs:
        if o.type != "MESH": continue
        mi = o.matrix_world.inverted(); org = mi @ Vector((x, y, z0)); dr = (mi.to_3x3() @ Vector((0, 0, -1))).normalized()
        ok, loc, nor, idx = o.evaluated_get(dg).ray_cast(org, dr)
        if ok:
            z = (o.matrix_world @ loc).z
            best = z if best is None else max(best, z)
    return best

# --- primitivlar: (0,0,0) da yasab, keyin joylashtiramiz (transform_apply tuzog'idan qochish) ---
def _fin(o, name, loc, rot, m, parent):
    o.name = name; o.location = loc; o.rotation_euler = [R(a) for a in rot]
    if m: o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def plane(name, size, loc, m, rot=(0, 0, 0), parent=None):
    sx, sy = size[0] / 2, size[1] / 2
    me = bpy.data.meshes.new(name); me.from_pydata([(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)], [], [(0, 1, 2, 3)]); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return _fin(o, name, loc, rot, m, parent)
def box(name, size, loc, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(); o = bpy.context.object
    for v in o.data.vertices: v.co = Vector((v.co.x * size[0] / 2, v.co.y * size[1] / 2, v.co.z * size[2] / 2))
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL"); bv.width = bevel; bv.segments = 3
    return _fin(o, name, loc, rot, m, parent)
def cyl(name, r, depth, loc, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth); o = bpy.context.object
    for p in o.data.polygons: p.use_smooth = len(p.vertices) == 4
    return _fin(o, name, loc, rot, m, parent)
def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3, parent=None, world=True):
    if sub >= 4: bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r)
    else: bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r)
    o = bpy.context.object; o.scale = scale
    for p in o.data.polygons: p.use_smooth = True
    return _fin(o, name, loc, (0, 0, 0), m, parent)
FONT = bpy.data.fonts.load("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf")
def text(name, body, size, loc, rot, m, parent=None, align="CENTER", extrude=0.0):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.font = FONT; cu.size = size
    cu.align_x = align; cu.align_y = "CENTER"; cu.extrude = extrude
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o)
    return _fin(o, name, loc, rot, m, parent)
def frame_q(fwd, up):
    y = Vector(fwd).normalized(); z = Vector(up); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_quaternion()
def import_gltf(path, parent):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.parent = parent
    return new

def tile_mat(name, c1, c2, grout=(0.5, 0.5, 0.5), scale=3.3, rough=0.08):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.offset = 0.5
    br.inputs["Color1"].default_value = (*c1, 1); br.inputs["Color2"].default_value = (*c2, 1); br.inputs["Mortar"].default_value = (*grout, 1)
    br.inputs["Scale"].default_value = scale; br.inputs["Mortar Size"].default_value = 0.012
    L.new(tc.outputs["Object"], br.inputs["Vector"]); L.new(br.outputs["Color"], b.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange"); L.new(br.outputs["Fac"], mr.inputs["Value"]); mr.inputs["To Min"].default_value = rough
    mr.inputs["To Max"].default_value = 0.8; L.new(mr.outputs[0], b.inputs["Roughness"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.004
    L.new(P.math_n(N, L, "SUBTRACT", 1.0, br.outputs["Fac"]), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def aim(c, tgt, focus=None):
    t = c.constraints.new("TRACK_TO"); t.target = tgt; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if c.data.dof.use_dof: c.data.dof.focus_object = focus or tgt
def path(c, keys, base=Vector((0, 0, 0)), lin=False):
    for f, p in keys: key(c, f, loc=tuple(Vector(base) + Vector(p)))
    if lin: interp(c, "LINEAR", "location")
def tgt_path(name, keys, base=Vector((0, 0, 0))):
    t = empty(name, (0, 0, 0)); path(t, keys, base); return t
def orbit_cam(name, f0, f1, center, r0, r1, a0, a1, z0, z1, lens, tgt, fstop=None):
    c = shot_cam(name, (0, 0, 0), tgt, lens, clip=0.01, fstop=fstop)
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / max(1, f1 - f0); a = R(a0 + (a1 - a0) * t); rr_ = r0 + (r1 - r0) * t
        key(c, f, loc=tuple(Vector(center) + Vector((rr_ * math.cos(a), rr_ * math.sin(a), z0 + (z1 - z0) * t))))
    interp(c, "LINEAR", "location"); return c
def glow_mat(name, col):
    """yumshoq nur: Transparent + Emission (Add); 'a' = kuch"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    a = value_node(m, "a", 0.0); lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    c_ = P.math_n(N, L, "POWER", P.math_n(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"], clamp=True), 2.5)
    L.new(P.math_n(N, L, "MULTIPLY", a, c_), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); ad = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N["Material Output"].inputs[0])
    return m
def emit_mat(name, col, s):
    return mat(name, col, 0.5, emit=s)
def smooth(o):
    for p in o.data.polygons: p.use_smooth = True
def mesh_obj(name, verts, faces, m=None, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc
    if m: me.materials.append(m)
    if parent: o.parent = parent
    return o
def rrect(w, h, zc=0.0, n=20, p=0.4):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n; c_, s_ = math.cos(t), math.sin(t)
        out.append((w / 2 * math.copysign(abs(c_) ** p, c_), zc + h / 2 * math.copysign(abs(s_) ** p, s_)))
    return out
def sweep(name, prof, ax, ay, m, a0=0.0, a1=math.pi, n=48, closed=True, parent=None, loc=(0, 0, 0)):
    """profil (r_off, z) ni ellips bo'ylab aylantirish; closed=True: yopiq profil (halqa), aks holda ochiq (kosa devori)"""
    vs = []; fs = []; k = len(prof)
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n; ca, sa = math.cos(a), math.sin(a)
        for ro, z in prof: vs.append(((ax + ro) * ca, (ay + ro) * sa, z))
    for i in range(n):
        for j in range(k if closed else k - 1):
            fs.append((i * k + j, i * k + (j + 1) % k, (i + 1) * k + (j + 1) % k, (i + 1) * k + j))
    if closed: fs.append(tuple(range(k))[::-1]); fs.append(tuple(range(n * k, n * k + k)))
    o = mesh_obj(name, vs, fs, m, parent, loc); smooth(o)
    if closed:
        o.data.polygons[-1].use_smooth = o.data.polygons[-2].use_smooth = False
    return o
def arrow(name, m, parent=None, s=1.0):
    e = empty(name, (0, 0, 0), parent)
    cyl(name + "_s", 0.014 * s, 0.13 * s, (0, 0, 0.115 * s), m, parent=e, verts=12)
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.04 * s, depth=0.08 * s); c_ = bpy.context.object
    c_.rotation_euler = (math.pi, 0, 0); c_.location = (0, 0, 0.04 * s); c_.data.materials.append(m); c_.parent = e
    return e
def cyc(o):
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
def skey(kb, pairs):
    for f, v in pairs: kb.value = v; kb.keyframe_insert("value", frame=f)

