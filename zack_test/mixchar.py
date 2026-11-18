"""Mixamo character + motion helpers (Linzhan/Mixamo-Animations-Characters).

Character FBX (character_refined/*.fbx) and motion FBX (animation_motion/*.fbx)
share the 65-bone 'mixamorig:' skeleton, so motions are transferred by assigning
the action directly.  The motions were captured on a taller rig, so Hips
translation is rescaled to the target's hip height (prevents foot sliding and
floor penetration)."""
import bpy, os, math
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
P = "mixamorig:"


def _new_objects(fn):
    before = set(bpy.data.objects)
    fn()
    return [o for o in bpy.data.objects if o not in before]


def load_character(name="Megan", coll=None):
    path = os.path.join(ASSETS, "characters", f"{name}.fbx")
    objs = _new_objects(lambda: bpy.ops.import_scene.fbx(filepath=path, use_anim=False))
    arm = [o for o in objs if o.type == "ARMATURE"][0]
    arm.name = name
    if coll:
        for o in objs:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll.objects.link(o)
    meshes = [o for o in objs if o.type == "MESH"]
    fix_materials(meshes)
    return arm, meshes


def fix_materials(meshes):
    """Mixamo FBX materials: wire alpha for hair/lashes, add skin SSS, sane roughness."""
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes:
                continue
            nt = m.node_tree
            b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if not b:
                continue
            lname = (m.name + o.name).lower()
            tex = [n for n in nt.nodes if n.type == "TEX_IMAGE"]
            # base colour texture -> alpha for cards
            if any(k in lname for k in ("hair", "lash")):
                base = next((l.from_node for l in nt.links if l.to_socket == b.inputs["Base Color"]), None)
                if base is not None and base.type == "TEX_IMAGE" and not b.inputs["Alpha"].is_linked:
                    nt.links.new(base.outputs["Alpha"], b.inputs["Alpha"])
                b.inputs["Roughness"].default_value = 0.45
                try:
                    m.surface_render_method = "DITHERED"
                except Exception:
                    pass
            if "body" in lname:
                b.inputs["Subsurface Weight"].default_value = 0.15
                b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
                b.inputs["Subsurface Scale"].default_value = 0.01
            # Mixamo FBX gloss maps import as roughness -> plastic look; use fixed values
            for l in list(b.inputs["Roughness"].links):
                nt.links.remove(l)
            rough = 0.45
            if "body" in lname:
                rough = 0.52
            elif any(k in lname for k in ("shirt", "top", "pants", "jean", "cloth")):
                rough = 0.85
            elif "sneaker" in lname or "shoe" in lname:
                rough = 0.6
            b.inputs["Roughness"].default_value = rough
            try:
                b.inputs["Specular IOR Level"].default_value = 0.4
            except KeyError:
                pass
            if not b.inputs["Metallic"].is_linked:
                b.inputs["Metallic"].default_value = 0.0
        for p in o.data.polygons:
            p.use_smooth = True


def _fcurves(act):
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out


def load_motion(name, target_arm):
    """Import animation_motion/<name>.fbx, return its action, hip-rescaled for target."""
    path = os.path.join(ASSETS, "animations", f"{name}.fbx")
    objs = _new_objects(lambda: bpy.ops.import_scene.fbx(filepath=path))
    src = [o for o in objs if o.type == "ARMATURE"][0]
    act = src.animation_data.action
    act.name = name
    act.use_fake_user = True
    sh = src.data.bones[P + "Hips"].head_local.length
    th = target_arm.data.bones[P + "Hips"].head_local.length
    ratio = th / sh if sh > 1e-6 else 1.0
    for fc in _fcurves(act):
        if fc.data_path == f'pose.bones["{P}Hips"].location':
            for k in fc.keyframe_points:
                k.co[1] *= ratio
                k.handle_left[1] *= ratio
                k.handle_right[1] *= ratio
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f"[mixchar] motion {name}: frames {tuple(act.frame_range)} hip ratio {ratio:.3f}")
    return act


def sequence(arm, clips):
    """clips: list of dict(action, start, src=(a,b), blend=frames, scale=1.0, repeat=1).
    Builds NLA strips on one track per clip (alternating) with blend-in for smooth
    transitions."""
    ad = arm.animation_data_create()
    ad.action = None
    tracks = [ad.nla_tracks.new(), ad.nla_tracks.new()]
    for i, c in enumerate(clips):
        tr = tracks[i % 2]
        st = tr.strips.new(c["action"].name + f"_{i}", int(c["start"]), c["action"])
        try:
            if c["action"].slots:
                st.action_slot = c["action"].slots[0]
        except Exception:
            pass
        a, b = c.get("src", tuple(c["action"].frame_range))
        st.action_frame_start = a
        st.action_frame_end = b
        st.scale = c.get("scale", 1.0)
        st.repeat = c.get("repeat", 1.0)
        st.frame_start = c["start"]
        st.blend_in = c.get("blend", 0)
        st.extrapolation = "HOLD_FORWARD" if i else "HOLD"
        st.use_auto_blend = False
    return tracks


def bone_world(arm, bone):
    return arm.matrix_world @ arm.pose.bones[P + bone].matrix


def bone_head(arm, bone):
    return arm.matrix_world @ arm.pose.bones[P + bone].head


def hand_grip_matrix(arm, side="Right", can_radius=0.033, can_half=0.084):
    """World matrix for a cylinder (origin at its bottom) gripped in the palm."""
    h = bone_head(arm, f"{side}Hand")
    mid = bone_head(arm, f"{side}HandMiddle1")
    idx = bone_head(arm, f"{side}HandIndex1")
    pin = bone_head(arm, f"{side}HandPinky1")
    thb = bone_head(arm, f"{side}HandThumb2")
    fwd = (mid - h)
    palm_c = h + fwd * 0.75
    axis = (idx - pin).normalized()              # can axis ~ knuckle line
    toward = (thb - (idx + pin) * 0.5)
    toward = (toward - axis * toward.dot(axis)).normalized()
    center = palm_c + toward * (can_radius + 0.012)
    # make the can's up roughly world-up (thumb side is up for a natural grip)
    if axis.z < 0:
        axis = -axis
    x = toward.cross(axis).normalized()
    y = axis.cross(x).normalized()
    rot = Matrix((x, y, axis)).transposed()
    m = rot.to_4x4()
    m.translation = center - axis * can_half
    return m


def attach_to_bone(obj, arm, bone, world_matrix_at_frame, frame):
    """Parent obj to a bone keeping the given world matrix at `frame`."""
    sc = bpy.context.scene
    sc.frame_set(frame)
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = P + bone
    bpy.context.view_layer.update()
    pb = arm.pose.bones[P + bone]
    # bone parent space = armature world @ pose bone matrix @ translate(tail)
    bone_mat = arm.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = bone_mat.inverted() @ world_matrix_at_frame
