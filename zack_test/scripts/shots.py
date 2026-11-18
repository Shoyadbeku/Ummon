"""Shot builders. Every shot is built into its own fresh scene whose frame range is
the GLOBAL frame range of the edit (24 fps), so renders drop straight into
renders/final/frame_XXXXXX.png."""
import bpy, math, random, sys, os
from mathutils import Vector, Matrix, Euler
import common as C
import sets as S

sys.path.insert(0, C.ROOT)
import mixchar as MC

# global edit (frames, 24 fps) — matches the narration timecodes
SHOTS = {
    "s1": (1, 151),     # hook: fridge-cam grab, crack macro, drink
    "s1b": (152, 223),  # sting: rim macro + rat silhouette
    "s2": (224, 369),   # wide warehouse
    "s3": (370, 600),   # rat run, low angle
    "s4": (601, 669),   # UV reveal
    "s5": (670, 905),   # tab pushes bacteria in
    "s6": (906, 1049),  # sick close-up + x-ray
}


def _hide_keys(obj, visible_ranges, f0, f1):
    """Keyframe hide_render so obj renders only inside visible_ranges."""
    def vis(f):
        return any(a <= f <= b for a, b in visible_ranges)
    prev = None
    for f in range(f0 - 1, f1 + 2):
        v = vis(f)
        if v != prev:
            obj.hide_render = not v
            obj.keyframe_insert("hide_render", frame=f)
            obj.hide_viewport = not v
            obj.keyframe_insert("hide_viewport", frame=f)
            prev = v
    for o in obj.children_recursive:
        if o.hide_render:  # cutters stay hidden
            continue
        o.driver_remove("hide_render")
        d = o.driver_add("hide_render").driver
        d.type = "SCRIPTED"
        v = d.variables.new()
        v.name = "h"
        v.targets[0].id = obj
        v.targets[0].data_path = "hide_render"
        d.expression = "h"


def _megan(sc):
    coll = bpy.data.collections.new("Megan")
    sc.collection.children.link(coll)
    arm, meshes = MC.load_character("Megan", coll)
    return arm, meshes


# =========================================================================== S1
def shot_s1(sc):
    f0, f1 = SHOTS["s1"]
    arm, meshes = _megan(sc)
    lift = MC.load_motion("Lifting", arm)
    drink = MC.load_motion("Drinking", arm)
    MC.sequence(arm, [
        dict(action=lift, start=1, src=(16, 150)),
        dict(action=drink, start=97, src=(75, 160)),
    ])
    PICK = 31
    sc.frame_set(PICK)
    grip_pick = MC.hand_grip_matrix(arm, "Right")
    deck = max(0.05, grip_pick.translation.z)
    print("[s1] grip at pickup", grip_pick.translation, "deck z", deck)
    S.build_store(sc, deck_z=deck)

    # hero cans
    canR = C.make_can("HeroR", "volt")
    MC.attach_to_bone(canR, arm, "RightHand", grip_pick, PICK)
    C.animate_can_open(canR, 76, 86)
    canS = C.make_can("HeroShelf", "volt")
    canS.location = (grip_pick.translation.x, grip_pick.translation.y, deck)
    # cut cheat: on the cut to 1c she faces the aisle (+Y)
    arm.location = (0, 0, 0); arm.keyframe_insert("location", frame=96)
    arm.rotation_euler = (math.radians(90), 0, 0); arm.keyframe_insert("rotation_euler", frame=96)
    arm.location = (0, 0.3, 0); arm.keyframe_insert("location", frame=97)
    arm.rotation_euler = (math.radians(90), 0, math.pi); arm.keyframe_insert("rotation_euler", frame=97)
    C.set_interp(arm, "CONSTANT")
    sc.frame_set(110)
    canL = C.make_can("HeroL", "volt")
    MC.attach_to_bone(canL, arm, "LeftHand", MC.hand_grip_matrix(arm, "Left"), 110)
    bpy.data.objects[canL["tab"]].rotation_euler = (math.radians(-8), 0, 0)
    bpy.data.objects[canL["flap"]].rotation_euler = (math.radians(-80), 0, 0)
    _hide_keys(canS, [(f0, PICK - 1)], f0, f1)
    _hide_keys(canR, [(PICK, 96)], f0, f1)
    _hide_keys(canL, [(97, f1)], f0, f1)

    # --- cameras
    # 1a fridge-cam: on the bottom deck among the cans, looking out and up at her
    tgt_a = C.empty("tgtA", (-0.15, -0.05, 0.75))
    C.key_path(tgt_a, [(1, (-0.2, 0.1, 0.7)), (PICK, (-0.2, -0.3, 0.42)), (45, (-0.15, -0.15, 0.7))])
    cam_a = C.camera("Cam1a_fridge", 18, (0.18, -0.37, 0.3), tgt_a, fstop=2.2)
    C.key_path(cam_a, [(1, (0.24, -0.37, 0.28)), (45, (0.12, -0.36, 0.31))])
    fd = cam_a.data.dof
    fd.focus_distance = 0.9; fd.keyframe_insert("focus_distance", frame=1)
    fd.focus_distance = 0.4; fd.keyframe_insert("focus_distance", frame=PICK)
    fd.focus_distance = 0.6; fd.keyframe_insert("focus_distance", frame=45)
    # 1a2 low-angle side push-in as she rises with the can
    tgt_a2 = C.empty("tgtA2", (0, 0, 0))
    tgt_a2.parent = canR; tgt_a2.location = (0, 0, 0.12)
    cam_a2 = C.camera("Cam1a2_low", 24, (-1.1, -0.15, 0.3), tgt_a2, fstop=2.8, focus=tgt_a2)
    C.key_path(cam_a2, [(46, (-1.15, -0.05, 0.28)), (70, (-0.7, 0.05, 0.42))])
    # 1b crack macro: camera rides with the can (hand-held 'snorricam')
    cam_b = C.camera("Cam1b_crack", 70, (0, 0, 0), None, fstop=2.8, focus=None, clip=(0.002, 50))
    cam_b.parent = canR
    cam_b.rotation_euler = (math.radians(55), 0, 0)
    C.key_path(cam_b, [(71, (0.01, -0.12, 0.28)), (96, (0.0, -0.085, 0.235))])
    cam_b.data.dof.focus_distance = 0.13
    # 1c drink: she has turned toward the aisle (cut cheat); front-3/4 push-in, cooler glows behind
    tgt_c = C.empty("tgtC", (0.0, 0.3, 1.45))
    C.key_path(tgt_c, [(97, (-0.03, 0.3, 1.3)), (151, (-0.01, 0.3, 1.5))])
    cam_c = C.camera("Cam1c_drink", 50, (-0.6, 1.2, 1.42), tgt_c, fstop=2.0, focus=canL)
    C.key_path(cam_c, [(97, (-0.62, 1.25, 1.38)), (151, (-0.32, 0.85, 1.5))])
    C.bind_cameras(sc, [(1, cam_a), (46, cam_a2), (71, cam_b), (97, cam_c)])
    return dict(arm=arm)


BUILDERS = {"s1": shot_s1}


def build(shot):
    sc = C.reset()
    f0, f1 = SHOTS[shot]
    sc.frame_start, sc.frame_end = f0, f1
    BUILDERS[shot](sc)
    return sc
