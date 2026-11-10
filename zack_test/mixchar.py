"""Mixamo qahramon + harakat yordamchisi (Blender 5.2, bpy moduli).

Linzhan/Mixamo-Animations-Characters dagi character_refined/*.fbx va
animation_motion/*.fbx bir xil "mixamorig:*" suyak nomlariga ega, shuning
uchun harakatni retargetsiz to'g'ridan-to'g'ri armaturaga ulash mumkin.

Tuzoqlar:
- Blender 5 da action bilan birga action_slot ham o'rnatilishi kerak,
  aks holda armatura qimirlamaydi.
- Animatsiya FBX o'z armaturasini ham olib keladi: uni (va meshlarini) o'chirish kerak.
- FBX armatura 0.01 masshtabda keladi; butun qahramonni ildiz Empty orqali siljitamiz.
"""
import bpy
from mathutils import Matrix, Vector


def import_character(path, name="Char"):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, use_anim=False)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    arm.name = name
    root = bpy.data.objects.new(name + "_root", None)
    bpy.context.scene.collection.objects.link(root)
    arm.parent = root
    fix_materials(new)
    return root, arm, [o for o in new if o.type == "MESH"]


def fix_materials(objs):
    """Mixamo FBX materiallari juda yaltiroq keladi — terini yumshatamiz."""
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.node_tree:
                continue
            p = m.node_tree.nodes.get("Principled BSDF")
            if not p:
                continue
            # Specular map ba'zan Roughness ga noto'g'ri ulanadi
            for l in list(p.inputs["Roughness"].links):
                m.node_tree.links.remove(l)
            p.inputs["Roughness"].default_value = 0.55
            p.inputs["Specular IOR Level"].default_value = 0.35
            if "body" in m.name.lower():
                p.inputs["Subsurface Weight"].default_value = 0.08
                p.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
                p.inputs["Subsurface Scale"].default_value = 0.01


def load_action(path):
    """Animatsiya FBX dan action ni olib, keraksiz armaturani o'chiradi."""
    before_o = set(bpy.data.objects)
    before_a = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path)
    act = next(a for a in bpy.data.actions if a not in before_a and a.frame_range[1] > 2)
    act.use_fake_user = True
    for o in [o for o in bpy.data.objects if o not in before_o]:
        bpy.data.objects.remove(o, do_unlink=True)
    return act


def apply_action(arm, act, start=1, speed=1.0, strip_root_xy=True):
    """Action ni NLA strip sifatida qo'yadi (start kadrdan, kerakli tezlikda)."""
    if strip_root_xy and not act.get("_flat"):
        _flatten_root(act)
        act["_flat"] = True
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    track = ad.nla_tracks.new()
    strip = track.strips.new(act.name, int(start), act)
    strip.scale = 1.0 / speed
    strip.extrapolation = "HOLD"
    if hasattr(strip, "action_slot") and len(act.slots):
        strip.action_slot = act.slots[0]
    return strip


def _flatten_root(act):
    """Hips X/Z (Mixamo 'oldinga') siljishini olib tashlaydi — qahramon joyida qoladi."""
    for fc in _fcurves(act):
        if fc.data_path.endswith('"mixamorig:Hips"].location') and fc.array_index in (0, 2):
            v0 = fc.keyframe_points[0].co[1] if len(fc.keyframe_points) else 0
            for k in fc.keyframe_points:
                k.co[1] = v0 + (k.co[1] - v0) * 0.15
                k.handle_left[1] = k.co[1]
                k.handle_right[1] = k.co[1]


def _fcurves(act):
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out


def bone_world(arm, bone, frame):
    sc = bpy.context.scene
    sc.frame_set(int(frame), subframe=frame - int(frame))
    pb = arm.pose.bones[bone]
    return arm.matrix_world @ pb.matrix


def bone_head_world(arm, bone, frame):
    return bone_world(arm, bone, frame).to_translation()
