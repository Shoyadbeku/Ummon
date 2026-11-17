# Mixamo qahramon + harakatlarni (FBX) Blender'ga yuklash va NLA orqali ketma-ket ulash
import bpy, os
ASSETS = os.environ.get("MIXAMO_DIR", "/tmp/claude-0/assets/mixamo/")
MIXAMO_FPS = 30.0

def _fcurves(act):
    if hasattr(act, "layers") and act.layers:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return list(act.fcurves)

def _channelbag_remove(act, fc):
    if hasattr(act, "layers") and act.layers:
        for l in act.layers:
            for s in l.strips:
                for cb in s.channelbags:
                    if fc in cb.fcurves[:]:
                        cb.fcurves.remove(fc); return
    else:
        act.fcurves.remove(fc)

def load_character(name, file):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ASSETS, "chars", file), automatic_bone_orientation=False)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    arm.name = name
    root = bpy.data.objects.new(name + "_root", None); bpy.context.scene.collection.objects.link(root)
    arm.parent = root
    for o in new:
        if o.type == "MESH":
            o.name = f"{name}_{o.name.split('_', 1)[-1]}"
            for p in o.data.polygons: p.use_smooth = True
    arm.animation_data_create()
    arm.animation_data.action = None          # FBX ichidagi T-poza harakati NLA ni bosib qo'ymasin
    return root, arm, [o for o in new if o.type == "MESH"]

_cache = {}
def load_action(file, inplace=True):
    key = (file, inplace)
    if key in _cache: return _cache[key]
    before_o = set(bpy.data.objects); before_a = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ASSETS, "anims", file))
    act = next(a for a in bpy.data.actions if a not in before_a)
    act.name = os.path.splitext(file)[0] + ("_inplace" if inplace else "")
    act.use_fake_user = True
    for o in [o for o in bpy.data.objects if o not in before_o]:
        bpy.data.objects.remove(o, do_unlink=True)
    if inplace:
        for fc in list(_fcurves(act)):
            if fc.data_path == 'pose.bones["mixamorig:Hips"].location' and fc.array_index in (0, 2):
                _channelbag_remove(act, fc)
    _cache[key] = act
    return act

def add_strip(arm, act, start, *, repeat=1.0, speed=1.0, blend=4, src=None, hold=True):
    """act'ni start kadrdan boshlab qo'yadi. speed=1 => asl tezlik (30fps -> 24fps hisobga olinadi)."""
    ad = arm.animation_data
    tr = ad.nla_tracks.new(); tr.name = act.name
    s = tr.strips.new(act.name, int(start), act)
    if hasattr(s, "action_slot") and act.slots:
        s.action_slot = act.slots[0]
    if src:
        s.action_frame_start, s.action_frame_end = src
    s.scale = (bpy.context.scene.render.fps / MIXAMO_FPS) / speed
    s.repeat = repeat
    s.influence = 1.0
    s.blend_in = blend if len(ad.nla_tracks) > 1 else 0
    s.extrapolation = "HOLD_FORWARD" if hold else "NOTHING"
    return s
