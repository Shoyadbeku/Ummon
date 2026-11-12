"""Shared helpers for the water-intoxication short (Blender 5.2 as Python module).

Pitfalls handled here (bpy 5.x):
  * actions are slotted: assign `animation_data.action_slot` explicitly and reach
    fcurves through layers/strips/channelbag (action.fcurves no longer exists);
  * Mixamo FBX armatures are imported at scale 0.01 with centimetre bones;
  * never name a script after a stdlib module (inspect.py, random.py ...) - bpy
    imports them and crashes with a glog "InitGoogleLogging() twice" abort.
"""
import bpy, math, os, random
from mathutils import Vector, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets")
FPS = 24


# ---------------------------------------------------------------- scene / render
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    return sc


def setup_render(sc, res=(1080, 1920), pct=100, samples=48, blur=True, shutter=0.5):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 4
    sc.cycles.transparent_max_bounces = 10
    sc.cycles.glossy_bounces = 2
    sc.cycles.diffuse_bounces = 2
    sc.cycles.volume_bounces = 0
    sc.cycles.denoising_prefilter = "ACCURATE"
    sc.cycles.transmission_bounces = 6
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = pct
    sc.render.use_motion_blur = blur and os.environ.get("NOBLUR") is None
    sc.render.motion_blur_shutter = shutter
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.threads_mode = "AUTO"


def world_color(sc, rgb, strength=1.0):
    w = bpy.data.worlds.new("W"); sc.world = w
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*rgb, 1)
    bg.inputs[1].default_value = strength


def world_hdri(sc, path, strength=1.0, rot=0.0):
    w = bpy.data.worlds.new("W"); sc.world = w
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path)
    mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord")
    mp.inputs["Rotation"].default_value[2] = rot
    nt.links.new(tc.outputs["Generated"], mp.inputs[0])
    nt.links.new(mp.outputs[0], env.inputs[0])
    bg = nt.nodes["Background"]
    nt.links.new(env.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = strength


# ---------------------------------------------------------------- animation utils
def fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action:
        return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            cb = strip.channelbag(ad.action_slot)
            if cb:
                out.extend(cb.fcurves)
    return out


def ease_all(idblock, interp="BEZIER"):
    for fc in fcurves(idblock):
        for k in fc.keyframe_points:
            k.interpolation = interp


def key(obj, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        obj.location = loc; obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rot; obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale if hasattr(scale, "__len__") else (scale,) * 3
        obj.keyframe_insert("scale", frame=frame)


def shake(obj, strength=0.01, scale=8.0, rot=True, loc=True, seed=0):
    """Hand-held camera noise on an already-keyed object."""
    if loc and not any(f.data_path == "location" for f in fcurves(obj)):
        obj.keyframe_insert("location", frame=1)
    if rot and not any(f.data_path == "rotation_euler" for f in fcurves(obj)):
        obj.keyframe_insert("rotation_euler", frame=1)
    for i, fc in enumerate(fcurves(obj)):
        if (fc.data_path == "location" and loc) or (fc.data_path == "rotation_euler" and rot):
            m = fc.modifiers.new("NOISE")
            m.scale = scale
            m.strength = strength * (0.6 if fc.data_path == "rotation_euler" else 1.0)
            m.phase = seed * 13.7 + i * 5.1


# ---------------------------------------------------------------- camera
def camera(sc, loc, look_at=None, lens=35, dof_obj=None, fstop=2.8, sensor=36):
    cd = bpy.data.cameras.new("Cam"); cd.lens = lens; cd.sensor_width = sensor
    cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam)
    cam.location = loc
    sc.camera = cam
    if look_at is not None:
        aim(cam, look_at)
    if dof_obj is not None:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        if isinstance(dof_obj, bpy.types.Object):
            cd.dof.focus_object = dof_obj
        else:
            cd.dof.focus_distance = float(dof_obj)
    cd.clip_start = 0.01
    return cam


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def cam_move(cam, keys):
    """keys: list of (frame, loc, look_at[, lens]) -> keyframed smooth move."""
    for k in keys:
        f, loc, tgt = k[:3]
        cam.location = loc; aim(cam, tgt)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
        if len(k) > 3:
            cam.data.lens = k[3]; cam.data.keyframe_insert("lens", frame=f)


def empty(name, loc=(0, 0, 0), parent=None, bone=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    if parent is not None:
        e.parent = parent
        if bone:
            e.parent_type = "BONE"; e.parent_bone = bone
    e.location = loc
    return e


# ---------------------------------------------------------------- lights
def area(sc, loc, target, energy=300, size=2.0, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    ld = bpy.data.lights.new("Area", "AREA"); ld.energy = energy; ld.color = color
    ld.shape = shape; ld.size = size; ld.size_y = size_y or size
    o = bpy.data.objects.new("Area", ld); sc.collection.objects.link(o)
    o.location = loc; aim(o, target)
    return o


def point(sc, loc, energy=100, color=(1, 1, 1), radius=0.1):
    ld = bpy.data.lights.new("Pt", "POINT"); ld.energy = energy; ld.color = color
    ld.shadow_soft_size = radius
    o = bpy.data.objects.new("Pt", ld); sc.collection.objects.link(o); o.location = loc
    return o


# ---------------------------------------------------------------- materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, sss=0.0, sss_radius=(1, 0.3, 0.2),
        emit=None, emit_strength=0.0, transmission=0.0, ior=1.45, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    # SSS is the most expensive thing on CPU; LOW_SSS scales it down (env var, default on)
    p.inputs["Subsurface Weight"].default_value = sss * float(os.environ.get("SSS_SCALE", "1"))
    p.inputs["Subsurface Radius"].default_value = sss_radius
    p.inputs["Transmission Weight"].default_value = transmission
    p.inputs["IOR"].default_value = ior
    p.inputs["Alpha"].default_value = alpha
    p.inputs["Coat Weight"].default_value = coat
    if emit is not None:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = emit_strength
    return m


def add_bump(m, scale=20.0, strength=0.3, detail=6.0, kind="noise"):
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    if kind == "voronoi":
        tx = nt.nodes.new("ShaderNodeTexVoronoi"); tx.inputs["Scale"].default_value = scale
        out = tx.outputs["Distance"]
    else:
        tx = nt.nodes.new("ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = scale
        tx.inputs["Detail"].default_value = detail; out = tx.outputs["Fac"]
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = strength
    nt.links.new(out, b.inputs["Height"]); nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return tx


def pbr_tex(name, folder, uv_scale=4.0):
    """Material from a Poly Haven texture folder (Diffuse/nor_gl/Rough)."""
    m = bpy.data.materials.new(name); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (uv_scale,) * 3
    nt.links.new(tc.outputs["UV"], mp.inputs[0])

    def img(fn, nonc=False):
        for ext in ("jpg", "png"):
            fp = os.path.join(folder, f"{fn}.{ext}")
            if os.path.exists(fp):
                t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fp)
                if nonc: t.image.colorspace_settings.name = "Non-Color"
                nt.links.new(mp.outputs[0], t.inputs[0]); return t
    d = img("Diffuse"); r = img("Rough", True); n = img("nor_gl", True)
    if d: nt.links.new(d.outputs[0], p.inputs["Base Color"])
    if r: nt.links.new(r.outputs[0], p.inputs["Roughness"])
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], p.inputs["Normal"])
    return m


def assign(obj, m):
    obj.data.materials.clear(); obj.data.materials.append(m)


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


# ---------------------------------------------------------------- imports
def import_gltf(path, name=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(name or os.path.basename(path))
    for o in new:
        if o.parent is None:
            o.parent = root
    return root, new


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, use_anim=True)
    return [o for o in bpy.data.objects if o not in before]


def load_character(name="Brian"):
    objs = import_fbx(os.path.join(ASSETS, "mixamo", f"char_{name}.fbx"))
    arm = next(o for o in objs if o.type == "ARMATURE")
    meshes = [o for o in objs if o.type == "MESH"]
    if arm.animation_data:
        arm.animation_data.action = None
    return arm, meshes


def load_action(anim):
    """Import a Mixamo motion FBX and return its action (temp armature deleted)."""
    objs = import_fbx(os.path.join(ASSETS, "mixamo", f"anim_{anim}.fbx"))
    a = next(o for o in objs if o.type == "ARMATURE")
    act = a.animation_data.action
    act.name = anim; act.use_fake_user = True
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    return act


def apply_action(arm, act, start=1, speed=1.0, hold_first=0):
    """Play `act` on `arm` starting at scene frame `start` through an NLA strip."""
    ad = arm.animation_data or arm.animation_data_create()
    tr = ad.nla_tracks.new(); tr.name = act.name
    s = tr.strips.new(act.name, int(start), act)
    s.scale = 1.0 / speed
    s.extrapolation = "HOLD"
    s.blend_type = "REPLACE"
    try:
        s.action_slot = act.slots[0]
    except Exception:
        pass
    return s


def bone_world(arm, bone, frame=None):
    sc = bpy.context.scene
    if frame is not None:
        sc.frame_set(frame)
    pb = arm.pose.bones[bone]
    return arm.matrix_world @ pb.head


def fix_char_materials(meshes, skin_sss=0.15):
    """Mixamo materials come in very glossy; make skin/cloth read more realistic."""
    for o in meshes:
        for sl in o.material_slots:
            m = sl.material
            if not m or not m.use_nodes: continue
            p = m.node_tree.nodes.get("Principled BSDF")
            if not p: continue
            n = m.name.lower()
            p.inputs["Metallic"].default_value = 0.0
            if p.inputs["Metallic"].is_linked:
                m.node_tree.links.remove(p.inputs["Metallic"].links[0])
            if "body" in n or "skin" in n:
                p.inputs["Subsurface Weight"].default_value = skin_sss
                p.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
                p.inputs["Subsurface Scale"].default_value = 0.01
                if not p.inputs["Roughness"].is_linked:
                    p.inputs["Roughness"].default_value = 0.45
            if "eyelash" in n or "hair" in n:
                m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
            if "eye" in n and "lash" not in n:
                p.inputs["Roughness"].default_value = 0.05
