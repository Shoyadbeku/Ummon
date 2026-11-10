"""Xona kadrlari 01–05 (global kadrlar 1–277, ovoz bilan bir xil vaqt o'qi)."""
import math

import bpy
from mathutils import Vector

import common as C
import mixchar as M
import room as R

SHOTS = {  # nom: (birinchi, oxirgi) global kadr
    1: (1, 62), 2: (63, 124), 3: (125, 167), 4: (168, 210), 5: (211, 277),
}
EJECT = 27          # sharcha og'izdan chiqadigan kadr (bosh eng pastda)
HAND_FROM = 125     # shu kadrdan sharcha qo'lda
SQUEEZE = (140, 162)
BALL_R = 0.013
CAM1_EJ = (0.12, -0.92, 1.12)        # 1-kadr: kamera EJECT paytida
CAM1_HIT = (0.17, -0.86, 1.05)


_LIP = {}


def mouth(arm, f):
    """Lab nuqtasi: Body meshidagi lablar vertexi (deformatsiyadan keyin)."""
    sc = bpy.context.scene
    body = next(o for o in bpy.data.objects if o.name.endswith("_Body"))
    if "i" not in _LIP:
        # dam holatida: yuzning eng oldingi nuqtasi lab balandligida
        hd = M.bone_head_world(arm, "mixamorig:Head", sc.frame_current)
        top = M.bone_head_world(arm, "mixamorig:HeadTop_End", sc.frame_current)
        zl = hd.z + (top.z - hd.z) * 0.09
        dg = bpy.context.evaluated_depsgraph_get()
        e = body.evaluated_get(dg)
        mw = e.matrix_world
        best = None
        for v in e.data.vertices:
            w = mw @ v.co
            if abs(w.z - zl) < 0.008 and abs(w.x - hd.x) < 0.01:
                if best is None or w.y < best[1]:
                    best = (v.index, w.y)
        _LIP["i"] = best[0]
    sc.frame_set(int(f))
    dg = bpy.context.evaluated_depsgraph_get()
    e = body.evaluated_get(dg)
    return e.matrix_world @ e.data.vertices[_LIP["i"]].co + Vector((0, -0.004, 0))


def cam1_ej(arm):
    """1-kadr kamerasi: yuzning oldinga yo'nalishi bo'yicha, biroz pastda."""
    m = M.bone_world(arm, "mixamorig:Head", EJECT)
    fwd = Vector(m.col[2][:3]).normalized()
    return mouth(arm, EJECT) + fwd * 0.75 + Vector((0.1, 0, -0.12))


def hand_pinch(arm, f):
    a = M.bone_head_world(arm, "mixamorig:RightHandThumb4", f)
    b = M.bone_head_world(arm, "mixamorig:RightHandIndex4", f)
    return (a + b) / 2


def build(shot):
    C.setup_render(576, 1024, samples=10)
    sc = bpy.context.scene
    # TUZOQ: persistent data + Mixamo tasvir teksturalari => animatsiyada qahramon qora bo'lib qoladi
    sc.render.use_persistent_data = False
    _LIP.clear()
    R.build_room()
    root, arm, meshes = R.add_megan([
        ("Breathing_Idle", 1, 1.0, "HOLD", 0, 0),
        # 0.6x: qo'llar yuz oldida (lokal 60–105) 125–200 global kadrlarga to'g'ri keladi
        ("Taking_Item", 25, 0.6, "HOLD_FORWARD", 0, 0),
        ("Stomach_Hit", 12, 0.75, "NOTHING", 3, 8),
        ("Annoyed_Head_Shake", 194, 1.0, "HOLD_FORWARD", 6, 0),
        ("Taking_Item", 205, 1.0, "HOLD_FORWARD", 6, 0),
    ])
    ball = R.stone_ball(r=BALL_R if shot != 1 else 0.016)
    animate_ball(ball, arm, shot)
    if shot in (3, 4):
        stink(ball, arm)
    cam_for(shot, ball, arm)
    a, b = SHOTS[shot]
    sc.frame_start, sc.frame_end = a, b
    return sc


# ------------------------------------------------------------------ sharcha
def animate_ball(ball, arm, shot):
    a, b = SHOTS[shot]
    if shot == 1:
        # og'izda yashirin, EJECT dan keyin ballistik uchish (sekinlashtirilgan, 0.55x)
        p = mouth(arm, EJECT)
        g = Vector((0, 0, -1.5))     # sekin-mo: deyarli to'g'ri chiziq ob'ektiv tomon
        slow = 0.5
        ce = cam1_ej(arm)
        T = ce + (p - ce).normalized() * 0.28 + Vector((0.03, 0, -0.02))  # ob'ektiv oldidagi nuqta
        ta = 12 / 24 * slow
        v = (T - p - g * (0.5 * ta * ta)) / ta
        for f in range(a, b + 1):
            if f < EJECT:
                ball.location = mouth(arm, f)
                ball.scale = (0.001,) * 3
            else:
                t = (f - EJECT) / 24 * slow
                pos = p + v * t + g * (0.5 * t * t)
                ball.location = pos
                ball.scale = (1, 0.85, 0.78)
                ball.rotation_euler = (t * 9, t * 5, 0)
            ball.keyframe_insert("location", frame=f)
            ball.keyframe_insert("scale", frame=f)
            ball.keyframe_insert("rotation_euler", frame=f)
    elif shot == 2:
        # polga tushib sakrash va dumalab to'xtash
        x, y, z = 0.1, -1.62, 0.16
        vx, vy, vz = 0.0, -0.18, -0.4
        dt = 1 / 24
        rot = 0.0
        for f in range(a, b + 1):
            ball.location = (x, y, z)
            sq = 1.0
            ball.rotation_euler = (rot, rot * 0.4, 0)
            ball.keyframe_insert("location", frame=f)
            ball.keyframe_insert("rotation_euler", frame=f)
            vz -= 9.81 * dt
            x += vx * dt
            y += vy * dt
            z += vz * dt
            if z < BALL_R * 0.78:
                z = BALL_R * 0.78
                vz = -vz * 0.45
                vx *= 0.8
                vy *= 0.8
                if abs(vz) < 0.15:
                    vz = 0
            if vz == 0:
                vx *= 0.93
                vy *= 0.93
            rot += math.hypot(vx, vy) * dt / BALL_R
    else:
        for f in range(a, b + 1):
            ball.location = hand_pinch(arm, f) + Vector((0, -0.004, 0))
            s0, s1 = SQUEEZE
            k = 0.0 if f < s0 else min(1.0, (f - s0) / (s1 - s0)) if shot >= 3 else 0
            ball.scale = (1 + 0.35 * k, 0.85 + 0.3 * k, 0.78 * (1 - 0.45 * k))
            ball.keyframe_insert("location", frame=f)
            ball.keyframe_insert("scale", frame=f)


def stink(ball, arm):
    """Sharchadan ko'tarilayotgan sarg'ish-yashil hid buluti (kichik hajmli volume)."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    v = bpy.context.object
    v.name = "Stink"
    v.scale = (0.13, 0.13, 0.22)
    m = bpy.data.materials.new("StinkMat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    out = nt.nodes["Material Output"]
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.45, 0.75, 0.05, 1)
    vol.inputs["Emission Color"].default_value = (0.5, 0.8, 0.1, 1)
    vol.inputs["Emission Strength"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 5.0
    nz.inputs["Detail"].default_value = 8
    nz.inputs["Roughness"].default_value = 0.65
    # shovqin vaqt bilan ko'tariladi
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    for f, zz in [(125, 0.0), (210, -1.6)]:
        mp.inputs["Location"].default_value[2] = zz
        mp.inputs["Location"].keyframe_insert("default_value", index=2, frame=f)
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    nt.links.new(tc.outputs["Object"], grad.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.52
    ramp.color_ramp.elements[1].position = 0.85
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(grad.outputs["Fac"], mul.inputs[1])
    dens = nt.nodes.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"
    nt.links.new(mul.outputs[0], dens.inputs[0])
    for f, d in [(138, 0.0), (160, 10.0), (210, 14.0)]:
        dens.inputs[1].default_value = d
        dens.inputs[1].keyframe_insert("default_value", frame=f)
    nt.links.new(dens.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    C.assign(v, m)
    # qo'l bilan birga yuradi
    con = v.constraints.new("COPY_LOCATION")
    con.target = ball
    v.location = (0, 0, 0)
    v.delta_location = (0.02, -0.06, 0.1)
    bpy.context.scene.cycles.volume_step_rate = 4.0
    return v


# ------------------------------------------------------------------ kamera
def cam_for(shot, ball, arm):
    a, b = SHOTS[shot]
    if shot == 1:
        # HOOK: pastdan keng ob'ektiv, tez push-in + qo'l titrashi
        face = mouth(arm, EJECT)
        ce = cam1_ej(arm)
        cam = C.camera(lens=18, fstop=2.8, focus=ball)
        C.cam_path(cam, [(a, (0.85, -2.5, 0.22)), (EJECT - 3, ce), (EJECT + 4, ce + Vector((0.01, -0.03, 0))),
                         (b, ce + Vector((0.06, -0.25, -0.08)))],
                   [(a, (0.0, 0.0, 1.1)), (EJECT - 3, face), (b, face + Vector((0.0, -0.1, 0.05)))],
                   handheld=0.012, seed=1)
        C.lens_anim(cam, [(a, 18), (EJECT - 3, 24), (b, 24)])
    elif shot == 2:
        # pol darajasida makro, sharchani kuzatadi, orqada Megan oyoqlari xira
        cam = C.camera(lens=45, fstop=1.8, focus=ball)
        C.cam_path(cam, [(a, (0.16, -2.12, 0.035)), (b, (0.02, -2.02, 0.03))],
                   [(a, (0.1, -1.66, 0.07)), (a + 12, (0.1, -1.7, 0.02)), (b, (0.1, -1.78, 0.015))],
                   handheld=0.005, seed=2)
    elif shot == 3:
        # qo'lda sharcha, yaqin plan, orbit
        h = hand_pinch(arm, a + 20)
        cam = C.camera(lens=60, fstop=2.0, focus=ball)
        C.cam_path(cam, [(a, h + Vector((0.32, -0.42, -0.05))), (b, h + Vector((-0.12, -0.36, 0.02)))],
                   [(a, h), (b, hand_pinch(arm, b))], handheld=0.004, seed=3)
    elif shot == 4:
        # yuz yaqin plan, sekin dolly-in
        hd = M.bone_head_world(arm, "mixamorig:Head", a + 10) + Vector((0, 0, 0.04))
        cam = C.camera(lens=45, fstop=2.0, focus=None)
        C.cam_path(cam, [(a, hd + Vector((0.32, -0.95, -0.22))), (b, hd + Vector((0.18, -0.68, -0.16)))],
                   [(a, hd + Vector((0, 0, -0.1))), (b, hd + Vector((0, 0, -0.06)))], handheld=0.004, seed=4)
        tgt = bpy.data.objects[cam.name + "_tgt"]
        cam.data.dof.focus_object = tgt
    elif shot == 5:
        # keng plan, past burchakdan orbit
        cam = C.camera(lens=16, fstop=4.0, focus=2.4)
        C.cam_path(cam, [(a, (2.3, -2.4, 0.22)), (b, (-1.0, -2.6, 0.3))],
                   [(a, (0.0, 0.2, 1.1)), (b, (0.1, 0.2, 1.0))], handheld=0.005, seed=5)
    return cam
