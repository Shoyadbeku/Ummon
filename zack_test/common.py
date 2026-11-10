"""Umumiy sahna yordamchilari: render sozlamalari, materiallar, kamera harakati."""
import math
import os
import random

import bpy
from mathutils import Vector

ASSETS = os.environ.get("ZACK_ASSETS", os.path.join(os.path.dirname(__file__), "assets"))


# ---------------------------------------------------------------- render
def setup_render(res_x=1080, res_y=1920, pct=100, samples=48, mblur=True):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 1
    sc.cycles.glossy_bounces = 1
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.volume_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.cycles.use_auto_tile = False
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.resolution_percentage = pct
    sc.render.fps = 24
    sc.render.use_motion_blur = mblur
    sc.render.motion_blur_shutter = 0.5
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 93
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = 0.0
    sc.render.threads_mode = "AUTO"
    return sc


def world_hdri(path, strength=1.0, rot=0.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    if path:
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(path)
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value[2] = rot
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def world_color(rgb, strength=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*rgb, 1)
    bg.inputs["Strength"].default_value = strength
    return w


# ---------------------------------------------------------------- materials
def principled(name, color, rough=0.5, sss=0.0, sss_radius=(1, 0.3, 0.2), sss_scale=0.05,
               coat=0.0, emission=None, emit_strength=0.0, transmission=0.0, ior=1.45, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Subsurface Weight"].default_value = sss
    p.inputs["Subsurface Radius"].default_value = sss_radius
    p.inputs["Subsurface Scale"].default_value = sss_scale
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.05
    p.inputs["Transmission Weight"].default_value = transmission
    p.inputs["IOR"].default_value = ior
    p.inputs["Alpha"].default_value = alpha
    if hasattr(p, "subsurface_method"):
        p.subsurface_method = "BURLEY"   # random walk dan ~2x tezroq, CPU uchun muhim
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = emit_strength
    return m


def add_noise_color(mat, c1, c2, scale=6.0, detail=6.0, bump=0.3, bump_scale=None):
    """Base Color ni ikki rang orasida shovqin bilan aralashtiradi + bump."""
    nt = mat.node_tree
    p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    if bump:
        nz2 = nt.nodes.new("ShaderNodeTexNoise")
        nz2.inputs["Scale"].default_value = bump_scale or scale * 4
        nz2.inputs["Detail"].default_value = 8
        nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        nt.links.new(nz2.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return ramp


def pbr_texture(name, folder, scale=1.0, rough_mult=1.0):
    """Poly Haven tekstura papkasidan (diff/nor/rough) material."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def img(fn, non_color=False):
        for ext in ("jpg", "png"):
            f = os.path.join(folder, f"{fn}.{ext}")
            if os.path.exists(f):
                n = nt.nodes.new("ShaderNodeTexImage")
                n.image = bpy.data.images.load(f)
                if non_color:
                    n.image.colorspace_settings.name = "Non-Color"
                nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
                return n
    d = img("diff")
    if d:
        nt.links.new(d.outputs["Color"], p.inputs["Base Color"])
    r = img("rough", True)
    if r:
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = rough_mult
        nt.links.new(r.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs[0], p.inputs["Roughness"])
    n = img("nor", True)
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------------------------------------------------------- objects
def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def subsurf(obj, levels=2):
    m = obj.modifiers.new("Sub", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


def displace(obj, tex_type="CLOUDS", size=0.5, strength=0.1, depth=2, mid=0.5, coords="LOCAL",
             noise_basis=None, name="Disp"):
    t = bpy.data.textures.new(name, tex_type)
    if hasattr(t, "noise_scale"):
        t.noise_scale = size
    if hasattr(t, "noise_depth"):
        t.noise_depth = depth
    if noise_basis and hasattr(t, "noise_basis"):
        t.noise_basis = noise_basis
    m = obj.modifiers.new(name, "DISPLACE")
    m.texture = t
    m.strength = strength
    m.mid_level = mid
    m.texture_coords = coords
    return m, t


def area_light(name, loc, rot, size, power, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    l = bpy.data.lights.new(name, "AREA")
    l.energy = power
    l.color = color
    l.shape = shape
    l.size = size
    if size_y:
        l.size_y = size_y
    o = link(bpy.data.objects.new(name, l))
    o.location = loc
    o.rotation_euler = rot
    return o


def point_light(name, loc, power, color=(1, 1, 1), radius=0.1):
    l = bpy.data.lights.new(name, "POINT")
    l.energy = power
    l.color = color
    l.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, l))
    o.location = loc
    return o


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------- camera
def camera(name="Cam", lens=35, fstop=None, focus=None, sensor=36):
    c = bpy.data.cameras.new(name)
    c.lens = lens
    c.sensor_width = sensor
    c.sensor_fit = "AUTO"
    c.clip_start = 0.005
    c.clip_end = 200
    if fstop:
        c.dof.use_dof = True
        c.dof.aperture_fstop = fstop
        if isinstance(focus, bpy.types.Object):
            c.dof.focus_object = focus
        elif focus is not None:
            c.dof.focus_distance = focus
    o = link(bpy.data.objects.new(name, c))
    bpy.context.scene.camera = o
    return o


def cam_path(cam, keys, target_keys=None, ease="EASE_IN_OUT", handheld=0.0, seed=1):
    """keys: [(frame, (x,y,z)), ...]; target_keys: [(frame, (x,y,z))] — nishon Empty."""
    for f, loc in keys:
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
    tgt = None
    if target_keys:
        tgt = link(bpy.data.objects.new(cam.name + "_tgt", None))
        for f, loc in target_keys:
            tgt.location = loc
            tgt.keyframe_insert("location", frame=f)
        con = cam.constraints.new("TRACK_TO")
        con.target = tgt
        con.track_axis = "TRACK_NEGATIVE_Z"
        con.up_axis = "UP_Y"
    for ob in [cam] + ([tgt] if tgt else []):
        _ease(ob, ease)
    if handheld > 0:
        add_shake(cam, handheld, seed)
    return tgt


def _ease(ob, ease):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    from mixchar import _fcurves
    for fc in _fcurves(ad.action):
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
            k.easing = "AUTO"
        if ease == "LINEAR":
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"


def add_shake(cam, amount=0.01, seed=1):
    """Qo'lda ushlangan kamera titrashi (rotation ga Noise modifier)."""
    cam.rotation_mode = "XYZ"
    for i in range(3):
        cam.keyframe_insert("rotation_euler", index=i, frame=1)
    from mixchar import _fcurves
    for fc in _fcurves(cam.animation_data.action):
        if fc.data_path == "rotation_euler":
            n = fc.modifiers.new("NOISE")
            n.scale = 18
            n.strength = amount
            n.phase = seed * 7 + fc.array_index * 13


def lens_anim(cam, keys):
    for f, v in keys:
        cam.data.lens = v
        cam.data.keyframe_insert("lens", frame=f)


def rnd(seed):
    return random.Random(seed)
