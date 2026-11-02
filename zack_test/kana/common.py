# Umumiy yordamchilar: materiallar, primitivlar, kamera, render sozlamalari, kadr oraliqlarini render qilish
import bpy, math, os, sys
from mathutils import Vector

R = math.radians
OUT = os.environ.get("OUT", "/tmp/claude-0/kana_frames/")
FPS = 24
TOTAL = 888            # 37 soniya

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.render.fps = 1, TOTAL, FPS
    sc.unit_settings.system = "METRIC"
    return sc

def sc():
    return bpy.context.scene

# ---------------- materiallar ----------------
def principled(m):
    return m.node_tree.nodes["Principled BSDF"]

def mat(name, col, rough=0.5, metal=0.0, coat=0.0, sss=0.0, sss_r=(1, 0.3, 0.2), sss_scale=0.1,
        emit=0.0, emit_col=None, alpha=1.0, transmission=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = principled(m)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = sss_r
        b.inputs["Subsurface Scale"].default_value = sss_scale
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_col or col), 1)
        b.inputs["Emission Strength"].default_value = emit
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m

def noise_color(m, col2, scale=10.0, detail=6.0, bump=0.0, kind="noise", coord="Object", distortion=0.0, bump_dist=0.02):
    """Base Color ga ikkinchi rang bilan shovqin aralashtirish (+ ixtiyoriy bump)."""
    N = m.node_tree.nodes; L = m.node_tree.links; b = principled(m)
    tc = N.new("ShaderNodeTexCoord")
    if kind == "noise":
        t = N.new("ShaderNodeTexNoise"); t.inputs["Detail"].default_value = detail
        t.inputs["Distortion"].default_value = distortion; out = t.outputs["Fac"]
    elif kind == "voronoi":
        t = N.new("ShaderNodeTexVoronoi"); out = t.outputs["Distance"]
    elif kind == "wave":
        t = N.new("ShaderNodeTexWave"); t.inputs["Distortion"].default_value = distortion or 8
        t.inputs["Detail"].default_value = detail; out = t.outputs["Fac"]
    t.inputs["Scale"].default_value = scale
    L.new(tc.outputs[coord], t.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    L.new(out, mx.inputs["Factor"])
    mx.inputs[6].default_value = b.inputs["Base Color"].default_value[:]
    mx.inputs[7].default_value = (*col2, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    if bump:
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = bump_dist
        L.new(out, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return mx

def add_bump(m, scale=50.0, strength=0.3, kind="noise", dist=0.02):
    N = m.node_tree.nodes; L = m.node_tree.links; b = principled(m)
    tc = N.new("ShaderNodeTexCoord")
    t = N.new("ShaderNodeTexNoise" if kind == "noise" else "ShaderNodeTexVoronoi")
    t.inputs["Scale"].default_value = scale
    L.new(tc.outputs["Object"], t.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = dist
    L.new(t.outputs["Fac"] if kind == "noise" else t.outputs["Distance"], bp.inputs["Height"])
    old = b.inputs["Normal"].links
    if old:
        L.new(old[0].from_socket, bp.inputs["Normal"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    return bp

def pbr(name, folder, scale=1.0, tint=None, ph=None):
    ph = ph or os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(ph, folder, fn))
        t.projection = "BOX"; t.projection_blend = 0.2
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

# ---------------- primitivlar ----------------
def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(name, size, loc, m, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s/2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    if m: o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3; smooth(o)
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), verts=32, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name
    if m: o.data.materials.append(m)
    smooth(o); return o

def sphere(name, r, loc, m, scale=(1, 1, 1), seg=48, ring=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if m: o.data.materials.append(m)
    smooth(o); return o

def plane(name, size, loc, m, cuts=0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); o = bpy.context.object; o.name = name
    o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    if cuts:
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=cuts); bpy.ops.object.mode_set(mode="OBJECT")
    if m: o.data.materials.append(m)
    return o

def tube(name, pts, radius, m, radii=None, res=12):
    """Nuqtalar bo'ylab egri trubka (oyoq, tomir, nerv, ilmoq)."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = radius; cu.bevel_resolution = 4; cu.resolution_u = res; cu.use_fill_caps = True
    sp = cu.splines.new("POLY" if res == 0 else "BEZIER")
    if sp.type == "BEZIER":
        sp.bezier_points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            bp = sp.bezier_points[i]; bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
            if radii: bp.radius = radii[i]
    else:
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*p, 1)
            if radii: sp.points[i].radius = radii[i]
    o = bpy.data.objects.new(name, cu); sc().collection.objects.link(o)
    if m: cu.materials.append(m)
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc().collection.objects.link(o); o.location = loc; o.parent = parent; return o

def parent_keep(child, parent):
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy(); child.parent = parent; child.matrix_world = mw

# ---------------- animatsiya ----------------
def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = scale if hasattr(scale, "__len__") else (scale,) * 3; o.keyframe_insert("scale", frame=f)

def keyval(sock_or_obj, f, value, attr="default_value"):
    setattr(sock_or_obj, attr, value); sock_or_obj.keyframe_insert(attr, frame=f)

def vis(o, ranges):
    """o (va bolalari) faqat berilgan kadr oraliqlarida render qilinadi."""
    objs = [o] + list(o.children_recursive)
    marks = sorted({1} | {a for a, b in ranges} | {b + 1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)
            x.hide_viewport = not on; x.keyframe_insert("hide_viewport", frame=f)

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "layers") and act.layers:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return list(act.fcurves)

def interp(idb, mode="BEZIER", path=None):
    for fc in fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points: k.interpolation = mode

def shake(o, f0, f1, amp=0.01, freq=0.35, seed=0, rot_amp=0.0):
    """Qo'l kamerasi silkinishi: location ga Noise modifikatori (f0..f1 oralig'ida)."""
    if not o.animation_data or not o.animation_data.action:
        o.keyframe_insert("location", frame=f0)
    for fc in fcurves(o):
        if fc.data_path not in ("location", "rotation_euler"): continue
        if fc.data_path == "rotation_euler" and not rot_amp: continue
        n = fc.modifiers.new("NOISE"); n.scale = 1 / freq; n.strength = (amp if fc.data_path == "location" else rot_amp)
        n.phase = seed * 13 + fc.array_index * 7; n.use_restricted_range = True
        n.frame_start = f0; n.frame_end = f1; n.blend_in = 2; n.blend_out = 2

# ---------------- kamera ----------------
def camera(name, loc, target, lens, fstop=None, focus=None, clip=0.01):
    d = bpy.data.cameras.new(name); d.lens = lens; d.clip_start = clip; d.clip_end = 500
    d.sensor_width = 36
    c = bpy.data.objects.new(name, d); sc().collection.objects.link(c); c.location = loc
    if target is not None:
        t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop
        d.dof.focus_object = focus or target
    return c

def cut(f, cam):
    sc().timeline_markers.new(cam.name, frame=f).camera = cam

# ---------------- render ----------------
def setup_render(samples=None, pct=None, exposure=-0.3, bounces=4):
    s = sc(); r = s.render
    r.engine = "CYCLES"; s.cycles.device = "CPU"
    s.cycles.samples = int(os.environ.get("SAMPLES", samples or 16)); s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.03
    s.cycles.use_denoising = True; s.cycles.max_bounces = bounces
    s.cycles.diffuse_bounces = 2; s.cycles.glossy_bounces = 2; s.cycles.transmission_bounces = 4
    s.cycles.caustics_reflective = s.cycles.caustics_refractive = False
    s.cycles.blur_glossy = 1.0
    r.use_motion_blur = True; r.motion_blur_shutter = 0.5
    r.resolution_x, r.resolution_y = 1080, 1920
    r.resolution_percentage = int(os.environ.get("PCT", pct or 50))
    s.view_settings.view_transform = "AgX"; s.view_settings.look = "AgX - Punchy"; s.view_settings.exposure = exposure
    r.image_settings.file_format = "PNG"
    r.use_persistent_data = True
    r.film_transparent = False

def world_hdri(path, strength=1.0, rot=0.0):
    w = bpy.data.worlds.new("hdri"); sc().world = w; w.use_nodes = True
    N = w.node_tree.nodes; env = N.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path)
    mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(rot))
    w.node_tree.links.new(tc.outputs["Generated"], mp.inputs[0]); w.node_tree.links.new(mp.outputs[0], env.inputs[0])
    w.node_tree.links.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = strength
    return w, mp

def world_color(col, strength=1.0):
    w = bpy.data.worlds.new("bg"); sc().world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*col, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = strength
    return w

def light(name, kind, loc, rot, energy, size=1.0, col=(1, 1, 1)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); sc().collection.objects.link(l)
    l.data.energy = energy; l.data.color = col; l.location = loc; l.rotation_euler = [R(a) for a in rot]
    if kind == "AREA": l.data.size = size
    elif kind == "SUN": l.data.angle = R(size)
    else: l.data.shadow_soft_size = size
    return l

def render_ranges(ranges):
    """FRAMES='a,b,c' bo'lsa faqat o'shalar (shu set'ga tegishlilari); aks holda o'z oraliqlari."""
    s = sc(); r = s.render
    own = [f for a, b in ranges for f in range(a, b + 1)]
    fs = os.environ.get("FRAMES")
    if fs:
        frames = [int(x) for x in fs.split(",") if int(x) in own]
    elif os.environ.get("RANGE"):
        a, b = map(int, os.environ["RANGE"].split("-")); frames = [f for f in own if a <= f <= b]
    else:
        frames = own
    skip = os.environ.get("SKIP_EXISTING") == "1"
    os.makedirs(OUT, exist_ok=True)
    for f in frames:
        path = f"{OUT}{f:04d}.png"
        if skip and os.path.exists(path): continue
        s.frame_set(f); r.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {f}", flush=True)
