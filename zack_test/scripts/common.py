"""Shared helpers for the 'Rat Can' short: render setup, materials, cameras,
procedural energy-drink can, asset import.  Blender 5.2 (bpy 5.2.3)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FPS = 24


# ---------------------------------------------------------------- scene / render
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    return sc


def setup_render(sc, quality="final", res=(1080, 1920), samples=None):
    r = sc.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.fps = FPS
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.5
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.image_settings.color_depth = "8"
    r.use_persistent_data = True
    c = sc.cycles
    c.device = "CPU"
    try:  # GPU if available
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = t
                prefs.get_devices()
                if any(d.type == t for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = True
                    c.device = "GPU"
                    break
            except Exception:
                pass
    except Exception:
        pass
    c.samples = samples or {"preview": 16, "final": 20}[quality]
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.adaptive_min_samples = 0
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    try:
        c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        c.denoising_prefilter = "ACCURATE"
    except Exception:
        pass
    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 3
    c.transmission_bounces = 6
    c.transparent_max_bounces = 16
    c.volume_bounces = 0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.sample_clamp_indirect = 8.0
    c.use_auto_tile = True
    c.tile_size = 1024
    c.seed = 0
    c.use_animated_seed = True
    vs = sc.view_settings
    try:
        sc.display_settings.display_device = "sRGB"
    except Exception:
        pass
    vs.view_transform = "AgX"
    looks = [i.identifier for i in vs.bl_rna.properties["look"].enum_items]
    for cand in ("AgX - Punchy", "Punchy"):
        if cand in looks:
            vs.look = cand
            break
    vs.exposure = float(sc.get("exposure", 0.0))
    return sc


def world_hdri(sc, name, strength=1.0, rot_z=0.0, bg_strength=None):
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(ASSETS, "hdri", f"{name}_2k.hdr"))
    mp = nt.nodes.new("ShaderNodeMapping")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp.inputs["Rotation"].default_value[2] = rot_z
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def world_color(sc, color=(0, 0, 0), strength=1.0):
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    return w


# ---------------------------------------------------------------- materials
def principled(name, color=(0.8, 0.8, 0.8), metallic=0.0, rough=0.5, **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        sock = b.inputs[k]
        sock.default_value = (*v, 1) if isinstance(v, tuple) and len(v) == 3 else v
    return m


def emission(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def pbr_texture(name, folder, scale=1.0, rough_mul=1.0, tint=None):
    """Poly Haven texture set (diff/nor/rough), box-projected in object space."""
    d = os.path.join(ASSETS, "textures", folder)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def tex(kind, cs):
        fn = [f for f in os.listdir(d) if f"_{kind}_" in f][0]
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(d, fn), check_existing=True)
        t.image.colorspace_settings.name = cs
        t.projection = "BOX"
        t.projection_blend = 0.25
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t

    dif = tex("diff", "sRGB")
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(dif.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = (*tint, 1)
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    else:
        nt.links.new(dif.outputs["Color"], b.inputs["Base Color"])
    ro = tex("rough", "Non-Color")
    mm = nt.nodes.new("ShaderNodeMath")
    mm.operation = "MULTIPLY"
    mm.inputs[1].default_value = rough_mul
    nt.links.new(ro.outputs["Color"], mm.inputs[0])
    nt.links.new(mm.outputs[0], b.inputs["Roughness"])
    no = tex("nor", "Non-Color")
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(no.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------------------------------------------------------- geometry
def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_obj(name, bm, coll=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me), coll)


def box(name, size, loc=(0, 0, 0), mat=None, coll=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    o = mesh_obj(name, bm, coll)
    o.location = loc
    if mat:
        assign(o, mat)
    return o


def plane(name, sx, sy, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, coll=None):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bmesh.ops.scale(bm, vec=Vector((sx, sy, 1)), verts=bm.verts)
    o = mesh_obj(name, bm, coll)
    o.location = loc
    o.rotation_euler = rot
    if mat:
        assign(o, mat)
    return o


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def import_gltf(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def polyhaven_model(name, coll=None):
    objs = import_gltf(os.path.join(ASSETS, "models", name, f"{name}.gltf"))
    meshes = [o for o in objs if o.type == "MESH"]
    if coll:
        for o in objs:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll.objects.link(o)
    return meshes


def instance_of(objs, name, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, coll=None):
    """Collection-instance a set of objects (kept in a hidden collection)."""
    key = "SRC_" + "_".join(sorted(o.name for o in objs))[:50]
    src = bpy.data.collections.get(key)
    if src is None:
        src = bpy.data.collections.new(key)
        for o in objs:
            for c in o.users_collection:
                c.objects.unlink(o)
            src.objects.link(o)
    e = bpy.data.objects.new(name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = src
    e.location = loc
    e.rotation_euler = rot
    e.scale = (scale, scale, scale)
    link(e, coll)
    return e


# ---------------------------------------------------------------- energy-drink can
CAN_R = 0.033
CAN_H = 0.168
LID_Z = 0.1625
LID_R = 0.0262


def _can_body_mat(design="volt"):
    m = bpy.data.materials.new("CanBody_" + design)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # cylindrical coordinates: angle + height
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    at = nt.nodes.new("ShaderNodeMath"); at.operation = "ARCTAN2"
    nt.links.new(sep.outputs["Y"], at.inputs[0]); nt.links.new(sep.outputs["X"], at.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.033
    nt.links.new(at.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], comb.inputs["X"]); nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    # bold diagonal "claw" bands
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"; wave.bands_direction = "DIAGONAL"
    wave.inputs["Scale"].default_value = 9.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 2.0
    wave.inputs["Detail Scale"].default_value = 1.5
    nt.links.new(comb.outputs[0], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.80
    ramp.color_ramp.elements[0].color = (0.004, 0.004, 0.005, 1)
    ramp.color_ramp.elements[1].position = 0.86
    col = {"volt": (0.18, 0.95, 0.05), "blue": (0.05, 0.35, 1.0), "red": (1.0, 0.08, 0.03)}[design]
    ramp.color_ramp.elements[1].color = (*col, 1)
    nt.links.new(wave.outputs["Fac"], ramp.inputs[0])
    # top & bottom silver bands (bare aluminium)
    band = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(sep.outputs["Z"], band.inputs[0])
    band.inputs[1].default_value = 0.150; band.inputs[2].default_value = 0.152
    band2 = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(sep.outputs["Z"], band2.inputs[0])
    band2.inputs[1].default_value = 0.014; band2.inputs[2].default_value = 0.012
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    nt.links.new(band.outputs[0], mx.inputs[0]); nt.links.new(band2.outputs[0], mx.inputs[1])
    mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    nt.links.new(mx.outputs[0], mixc.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], mixc.inputs["A"])
    mixc.inputs["B"].default_value = (0.75, 0.76, 0.78, 1)
    nt.links.new(mixc.outputs["Result"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mx.outputs[0], rr.inputs[0]); rr.inputs[3].default_value = 0.32; rr.inputs[4].default_value = 0.18
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    met = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mx.outputs[0], met.inputs[0]); met.inputs[3].default_value = 0.55; met.inputs[4].default_value = 1.0
    nt.links.new(met.outputs[0], b.inputs["Metallic"])
    b.inputs["Coat Weight"].default_value = 0.6
    b.inputs["Coat Roughness"].default_value = 0.08
    # condensation micro-bump (cold can)
    nz = nt.nodes.new("ShaderNodeTexVoronoi"); nz.inputs["Scale"].default_value = 900
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.0
    bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(nz.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Coat Normal"])
    m["condensation_bump"] = bump.name
    return m


def alu_mat(name="Aluminium", rough=0.28):
    return principled(name, (0.82, 0.83, 0.85), 1.0, rough)


def lid_mat(stain=True):
    """Aluminium lid with an invisible dried-urine stain that glows under 'UV'.
    Animate node 'UV' (Value) 0->1 to reveal."""
    m = bpy.data.materials.new("CanLid")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.80, 0.81, 0.83, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.3
    # concentric machining rings
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
    wav = nt.nodes.new("ShaderNodeTexWave"); wav.wave_type = "RINGS"
    wav.inputs["Scale"].default_value = 160; wav.inputs["Distortion"].default_value = 0.3
    nt.links.new(tc.outputs["Object"], wav.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
    nt.links.new(wav.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if not stain:
        return m
    # stain mask: noise blobs around the drinking opening (object space, +Y side)
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    mp.inputs["Location"].default_value = (0, -0.012, 0)
    d = nt.nodes.new("ShaderNodeVectorMath"); d.operation = "LENGTH"
    nt.links.new(mp.outputs[0], d.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(d.outputs["Value"], fall.inputs[0])
    fall.inputs[1].default_value = 0.022; fall.inputs[2].default_value = 0.004
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180
    nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    th = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(nz.outputs["Fac"], th.inputs[0])
    th.inputs[1].default_value = 0.45; th.inputs[2].default_value = 0.6
    mask = nt.nodes.new("ShaderNodeMath"); mask.operation = "MULTIPLY"
    nt.links.new(fall.outputs[0], mask.inputs[0]); nt.links.new(th.outputs[0], mask.inputs[1])
    # visible-light effect: slightly duller
    rr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mask.outputs[0], rr.inputs[0]); rr.inputs[3].default_value = 0.3; rr.inputs[4].default_value = 0.42
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    # UV reveal emission
    uv = nt.nodes.new("ShaderNodeValue"); uv.name = "UV"; uv.label = "UV"
    uv.outputs[0].default_value = 0.0
    em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"
    nt.links.new(mask.outputs[0], em.inputs[0]); nt.links.new(uv.outputs[0], em.inputs[1])
    em2 = nt.nodes.new("ShaderNodeMath"); em2.operation = "MULTIPLY"; em2.inputs[1].default_value = 6.0
    nt.links.new(em.outputs[0], em2.inputs[0])
    b.inputs["Emission Color"].default_value = (0.75, 1.0, 0.15, 1)
    nt.links.new(em2.outputs[0], b.inputs["Emission Strength"])
    return m


def _disc_points(cx, cy, rx, ry, n=24):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _prism(name, pts2d, z0, z1, coll=None):
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, z0)) for x, y in pts2d]
    vt = [bm.verts.new((x, y, z1)) for x, y in pts2d]
    bm.faces.new(vt)
    bm.faces.new(list(reversed(vb)))
    n = len(pts2d)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, coll)


def flap_outline():
    """Tear panel (drinking opening) outline in lid space; hinge edge at y=+0.0045."""
    pts = [(0.0062, 0.0045)]
    for i in range(17):
        a = math.pi * i / 16
        pts.append((0.0078 * math.cos(a), 0.0125 + 0.0078 * math.sin(a)))
    pts.append((-0.0062, 0.0045))
    return pts


def make_can(name, design="volt", coll=None, stain=False, lid_material=None, body_material=None):
    """Returns the can body object; lid, tear-panel 'flap', tab are children.
    Origin at can bottom centre, +Z up, tab tail toward -Y, opening toward +Y.
    Custom props: obj['flap'], obj['tab'] -> child names for animation."""
    prof = [(0.0, 0.007), (0.012, 0.0055), (0.0245, 0.0005), (0.0275, 0.0), (0.0305, 0.0015),
            (0.0322, 0.005), (0.0328, 0.009), (CAN_R, 0.013), (CAN_R, 0.148), (0.0326, 0.152),
            (0.0308, 0.157), (0.0288, 0.1615), (0.0281, 0.165), (0.0283, 0.1675), (0.0276, 0.1683),
            (0.0268, 0.1676), (0.0265, 0.1645), (LID_R, LID_Z)]
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=64, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    body = mesh_obj(name, bm, coll)
    smooth(body)
    assign(body, body_material or _can_body_mat(design))

    lm = lid_material or lid_mat(stain)
    am = alu_mat("TabAlu", 0.22)
    # lid disc with opening cut (boolean, live)
    lid = _prism(name + "_lid", _disc_points(0, 0, LID_R, LID_R, 64), LID_Z - 0.0006, LID_Z, coll)
    assign(lid, lm)
    cutter = _prism(name + "_cut", flap_outline(), LID_Z - 0.003, LID_Z + 0.003, coll)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    bo = lid.modifiers.new("open", "BOOLEAN")
    bo.operation = "DIFFERENCE"
    bo.object = cutter
    bo.solver = "EXACT"
    # dark interior visible through the opening
    inner = _prism(name + "_inner", _disc_points(0, 0, LID_R * 0.98, LID_R * 0.98, 32), LID_Z - 0.02, LID_Z - 0.019, coll)
    assign(inner, principled("CanInside", (0.02, 0.015, 0.01), 0.0, 0.2))
    # tear panel: origin on hinge line
    fo = [(x, y - 0.0045) for x, y in flap_outline()]
    flap = _prism(name + "_flap", [(x * 0.97, y * 0.97) for x, y in fo], -0.0006, 0.0, coll)
    flap.location = (0, 0.0045, LID_Z)
    assign(flap, lm)
    # pull tab: plate with finger hole, origin at rivet
    outer = []
    for i in range(20):
        a = math.pi * i / 19
        outer.append((0.0062 * math.cos(a), 0.0085 + 0.0045 * math.sin(a)))
    for i in range(20):
        a = math.pi + math.pi * i / 19
        outer.append((0.0068 * math.cos(a), -0.0075 + 0.0068 * math.sin(a)))
    tab = _prism(name + "_tab", outer, 0.0003, 0.0009, coll)
    hole = _prism(name + "_tabhole", _disc_points(0, -0.0085, 0.0042, 0.0034, 20), -0.001, 0.002, coll)
    hole.hide_render = True
    hb = tab.modifiers.new("hole", "BOOLEAN"); hb.object = hole; hb.solver = "EXACT"
    tab.location = (0, 0.0, LID_Z)
    assign(tab, am)
    rivet = _prism(name + "_rivet", _disc_points(0, 0, 0.0019, 0.0019, 16), LID_Z, LID_Z + 0.0011, coll)
    assign(rivet, am)
    for o in (lid, cutter, inner, flap, tab, rivet):
        o.parent = body
    hole.parent = tab
    body["flap"] = flap.name
    body["tab"] = tab.name
    body["lid"] = lid.name
    return body


def animate_can_open(can, f_start, f_end, tab_angle=-75, flap_angle=-80):
    """Tab lifts, nose pushes the tear panel into the can."""
    tab = bpy.data.objects[can["tab"]]
    flap = bpy.data.objects[can["flap"]]
    mid = f_start + (f_end - f_start) * 0.45
    tab.rotation_euler = (0, 0, 0); tab.keyframe_insert("rotation_euler", frame=f_start)
    flap.rotation_euler = (0, 0, 0); flap.keyframe_insert("rotation_euler", frame=mid)
    tab.rotation_euler = (math.radians(tab_angle), 0, 0); tab.keyframe_insert("rotation_euler", frame=f_end)
    flap.rotation_euler = (math.radians(flap_angle), 0, 0); flap.keyframe_insert("rotation_euler", frame=f_end)
    tab.rotation_euler = (math.radians(-8), 0, 0); tab.keyframe_insert("rotation_euler", frame=f_end + 8)


# ---------------------------------------------------------------- cameras
def camera(name, lens=35, loc=(0, 0, 1), target=None, fstop=None, focus=None, sensor=36, clip=(0.005, 200)):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = "AUTO"
    cd.clip_start, cd.clip_end = clip
    cam = link(bpy.data.objects.new(name, cd))
    cam.location = loc
    if target is not None:
        tc = cam.constraints.new("TRACK_TO")
        tc.target = target
        tc.track_axis = "TRACK_NEGATIVE_Z"
        tc.up_axis = "UP_Y"
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.aperture_blades = 7
        if focus is not None:
            cd.dof.focus_object = focus
    return cam


def empty(name, loc=(0, 0, 0), coll=None):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    e.empty_display_size = 0.05
    return link(e, coll)


def key_path(obj, frames_locs, interp="BEZIER", prop="location"):
    for f, v in frames_locs:
        setattr(obj, prop, v)
        obj.keyframe_insert(prop, frame=f)
    set_interp(obj, interp)


def fcurves_of(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out


def set_interp(idblock, interp="BEZIER", easing=None):
    for fc in fcurves_of(idblock):
        for k in fc.keyframe_points:
            k.interpolation = interp
            if easing:
                k.easing = easing


def bind_cameras(sc, cams):
    """cams: list of (frame, camera) -> timeline markers for hard cuts."""
    for f, c in cams:
        m = sc.timeline_markers.new(c.name, frame=f)
        m.camera = c
    sc.camera = cams[0][1]


def shake(obj, f0, f1, amp=0.004, freq=0.6, seed=1):
    """Subtle handheld noise on rotation via a noise F-modifier."""
    obj.keyframe_insert("rotation_euler", frame=f0)
    for fc in fcurves_of(obj):
        if fc.data_path == "rotation_euler":
            md = fc.modifiers.new("NOISE")
            md.scale = 1.0 / max(freq, 0.01) * 6
            md.strength = amp
            md.phase = seed * 13 + fc.array_index * 7


def area_light(name, size, energy, loc, rot=(0, 0, 0), color=(1, 1, 1), shape="RECTANGLE", size_y=None, coll=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    o = link(bpy.data.objects.new(name, ld), coll)
    o.location = loc
    o.rotation_euler = rot
    return o


def point_light(name, energy, loc, color=(1, 1, 1), radius=0.05, coll=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, ld), coll)
    o.location = loc
    return o


def spot_light(name, energy, loc, rot, angle=40, blend=0.3, color=(1, 1, 1), radius=0.05, coll=None):
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy = energy
    ld.color = color
    ld.spot_size = math.radians(angle)
    ld.spot_blend = blend
    ld.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, ld), coll)
    o.location = loc
    o.rotation_euler = rot
    return o


def sun(name, strength, rot, color=(1, 1, 1), angle=0.5):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.color = color
    ld.angle = math.radians(angle)
    o = link(bpy.data.objects.new(name, ld))
    o.rotation_euler = rot
    return o


def look_at_rot(src, dst):
    d = Vector(dst) - Vector(src)
    return d.to_track_quat("-Z", "Y").to_euler()
