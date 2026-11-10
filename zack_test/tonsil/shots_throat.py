"""Tomoq ichi kadrlari 06–14 (global kadrlar 278–1041)."""
import math
import random

import bpy
from mathutils import Vector

import common as C
import throat as T

SHOTS = {
    6: (278, 352), 7: (353, 428), 8: (429, 499), 9: (500, 572), 10: (573, 677),
    11: (678, 776), 12: (777, 885), 13: (886, 976), 14: (977, 1041),
}


def cam_light(cam, power=120, color=(1.0, 0.92, 0.85), off=(0.12, 0.1, 0.0), radius=0.08):
    l = C.point_light(cam.name + "_lamp", (0, 0, 0), power, color, radius)
    l.parent = cam
    l.location = off
    return l


def build(shot):
    sc = C.setup_render(576, 1024, samples=10)
    sc.render.use_persistent_data = True
    a, b = SHOTS[shot]
    sc.frame_start, sc.frame_end = a, b
    globals()[f"shot{shot}"](a, b)
    return sc


# ---------------------------------------------------------------- 06: tomoqqa uchib kirish
def shot6(a, b):
    tun, tl, tr = T.throat_world()
    C.point_light("Deep", (0, 9, 0), 400, (1.0, 0.35, 0.25), 0.6)
    cam = C.camera(lens=18, fstop=2.8)
    tgt = C.cam_path(cam, [(a, (0.0, -3.6, 0.25)), (a + 40, (0.05, 1.2, 0.1)), (b, (0.3, 2.75, 0.05))],
                     [(a, (0.0, 5.0, 0.0)), (a + 40, (0.4, 4.5, -0.05)), (b, (0.95, 4.1, -0.1))],
                     handheld=0.008, seed=6)
    cam.data.dof.focus_object = tgt
    cam_light(cam, 160)


# ---------------------------------------------------------------- yoriq + tosh umumiy
def crypt_set(stone_scale=1.0, light=1.0):
    cr = T.crypt_world()
    st, sm = T.stone()
    st.scale = Vector((1.0, 0.85, 1.15)) * stone_scale
    C.area_light("Key", (1.5, -2.0, 3.0), (math.radians(40), 0, math.radians(35)), 2.0, 350 * light,
                 (1.0, 0.9, 0.8))
    C.area_light("Rim", (-2.0, 2.0, 1.5), (math.radians(-60), 0, math.radians(-135)), 2.0, 250 * light,
                 (1.0, 0.55, 0.45))
    return cr, st, sm


def shot7(a, b):
    cr, st, sm = crypt_set()
    pts = T.scatter_on(st, 70, 1)
    pts = [(p, n) for p, n in pts if p.z > -0.35]
    T.bacteria(pts, a, b, seed=7, size=0.07, wiggle=0.012)
    rim = [(p, n) for p, n in T.scatter_on(cr, 900, 2) if 0.4 < (p.xy.length) < 1.4 and p.z > -0.4][:60]
    T.bacteria(rim, a, b, seed=8, size=0.07, wiggle=0.012)
    T.dead_cells([(p, n) for p, n in T.scatter_on(st, 40, 3) if p.z > -0.3][:22], size=0.11)
    cam = C.camera(lens=35, fstop=2.2, focus=st)
    C.cam_path(cam, [(a, (1.7, -1.9, 1.5)), (b, (0.8, -0.95, 0.62))],
               [(a, (0, 0, -0.15)), (b, (0.05, 0, -0.05))], handheld=0.006, seed=7)
    cam_light(cam, 40)


# ---------------------------------------------------------------- 08: bez atrofida orbit
def shot8(a, b):
    tun, tl, tr = T.throat_world()
    C.point_light("Deep", (0, 9, 0), 400, (1.0, 0.35, 0.25), 0.6)
    c = Vector((1.05, 4.2, -0.1))
    cam = C.camera(lens=24, fstop=2.8)
    keys = []
    for i, f in enumerate(range(a, b + 1, 10)):
        t = (f - a) / (b - a)
        ang = math.radians(-70 + 120 * t)
        r = 1.45 - 0.25 * t
        keys.append((f, c + Vector((-r * math.cos(ang) * 0.8, -r * math.sin(ang) * 0.9 - 0.2, 0.35 - 0.1 * t))))
    keys.append((b, keys[-1][1]))
    tgt = C.cam_path(cam, keys, [(a, c), (b, c + Vector((0, 0.1, 0)))], handheld=0.006, seed=8)
    cam.data.dof.focus_object = tgt
    cam_light(cam, 90)


# ---------------------------------------------------------------- 09: yoriq ichiga tushish
def shot9(a, b):
    cr = T.crypt_world()
    C.area_light("Key", (1.5, -2.0, 3.0), (math.radians(40), 0, math.radians(35)), 2.0, 300, (1.0, 0.9, 0.8))
    cam = C.camera(lens=16, fstop=3.5)
    tgt = C.cam_path(cam, [(a, (0.6, -1.6, 2.0)), (a + 35, (0.1, -0.3, 0.6)), (b, (0.0, -0.05, -0.9))],
                     [(a, (0, 0, -0.5)), (a + 35, (0, 0.05, -1.2)), (b, (0, 0.25, -1.9))],
                     handheld=0.01, seed=9)
    cam.data.dof.focus_object = tgt
    cam_light(cam, 60, off=(0.05, 0.05, 0))
    C.point_light("Bottom", (0, 0, -2.0), 15, (1.0, 0.5, 0.3), 0.2)


# ---------------------------------------------------------------- 10: shilimshiq va to'qima tiqiladi
def shot10(a, b):
    cr, st, sm = crypt_set(stone_scale=0.6)
    for f, s in [(a, 0.6), (b, 0.82)]:
        st.scale = Vector((1.0, 0.85, 1.15)) * s
        st.keyframe_insert("scale", frame=f)
    rng = random.Random(10)
    mucus = C.principled("Mucus", (0.95, 0.9, 0.65), rough=0.05, transmission=0.3, ior=1.33, sss=0.8,
                         sss_radius=(1, 0.9, 0.6), sss_scale=0.05, coat=1.0)
    cell_mat = C.principled("Flake", (0.92, 0.88, 0.8), rough=0.45, sss=0.6, sss_scale=0.03)
    for i in range(34):
        is_drop = i % 2 == 0
        if is_drop:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=rng.uniform(0.05, 0.11))
            o = bpy.context.object
            o.scale = (1, 1, rng.uniform(1.2, 1.8))
            C.assign(o, mucus)
        else:
            bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=rng.uniform(0.06, 0.1), depth=0.01)
            o = bpy.context.object
            C.displace(o, "CLOUDS", size=0.05, strength=0.03, name=f"fl{i}")
            C.subsurf(o, 1)
            C.assign(o, cell_mat)
        C.smooth(o)
        start = a + rng.randint(-20, b - a - 40)
        ang = rng.uniform(0, 6.28)
        p0 = Vector((math.cos(ang) * 1.8, math.sin(ang) * 1.6, rng.uniform(1.2, 2.2)))
        p1 = Vector((math.cos(ang + 1) * 0.5, math.sin(ang + 1) * 0.4, 0.15))
        p2 = Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), rng.uniform(-0.35, -0.05)))
        for f, p in [(start, p0), (start + 22, p1), (start + 40, p2)]:
            o.location = p
            o.keyframe_insert("location", frame=f)
        o.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), 0)
        o.keyframe_insert("rotation_euler", frame=start)
        o.rotation_euler = (rng.uniform(3, 8), rng.uniform(3, 8), 2)
        o.keyframe_insert("rotation_euler", frame=start + 40)
    cam = C.camera(lens=26, fstop=2.8, focus=st)
    C.cam_path(cam, [(a, (1.9, -1.5, 1.6)), (b, (1.05, -0.95, 0.55))],
               [(a, (0, 0, 0.1)), (b, (0, 0, -0.15))], handheld=0.006, seed=10)
    cam_light(cam, 40)


# ---------------------------------------------------------------- 11: bakteriyalar + oltingugurt gazi
def shot11(a, b):
    cr, st, sm = crypt_set(stone_scale=0.85)
    for f, s in [(a, 0.85), (b, 0.95)]:
        st.scale = Vector((1.0, 0.85, 1.15)) * s
        st.keyframe_insert("scale", frame=f)
    pts = [(p, n) for p, n in T.scatter_on(st, 260, 11) if p.z > -0.4][:130]
    T.bacteria(pts, a, b, seed=11, size=0.075, wiggle=0.015)
    origins = [p for p, n in T.scatter_on(st, 80, 12) if p.z > -0.1][:40]
    T.bubbles(origins, a, b, seed=12, rmin=0.025, rmax=0.08, rise=1.8)
    cam = C.camera(lens=30, fstop=2.4, focus=st)
    keys = []
    for f in range(a, b + 1, 12):
        t = (f - a) / (b - a)
        ang = math.radians(-50 + 80 * t)
        keys.append((f, Vector((1.25 * math.sin(ang), -1.25 * math.cos(ang), 0.7 - 0.15 * t))))
    keys.append((b, keys[-1][1]))
    C.cam_path(cam, keys, [(a, (0, 0, 0.0)), (b, (0, 0, 0.15))], handheld=0.006, seed=11)
    cam_light(cam, 40)


# ---------------------------------------------------------------- 12: kalsifikatsiya
def shot12(a, b):
    cr, st, sm = crypt_set(stone_scale=1.0)
    T.set_hard(sm, [(a + 6, 0.0), (b - 18, 1.0)])
    pts = [(p, n) for p, n in T.scatter_on(st, 200, 13) if p.z > -0.4][:80]
    T.bacteria(pts, a, b, seed=13, size=0.075, wiggle=0.01,
               scale_keys=[(a + 20, 1.0), (a + 70, 0.0)])
    # "sement" — mayda kristallar yuzaga o'sib chiqadi
    crys = C.principled("Crystal", (0.85, 0.8, 0.65), rough=0.3, coat=0.3)
    rng = random.Random(12)
    for i, (p, n) in enumerate([(p, n) for p, n in T.scatter_on(st, 160, 14) if p.z > -0.35][:70]):
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.03, radius2=0.0, depth=0.06)
        o = bpy.context.object
        C.assign(o, crys)
        o.location = p
        o.rotation_euler = n.to_track_quat("Z", "Y").to_euler()
        o.rotation_euler.x += rng.uniform(-0.4, 0.4)
        o.rotation_euler.y += rng.uniform(-0.4, 0.4)
        f0 = a + rng.randint(20, 70)
        o.scale = (0.001,) * 3
        o.keyframe_insert("scale", frame=f0)
        s = rng.uniform(0.6, 1.3)
        o.scale = (s, s, s)
        o.keyframe_insert("scale", frame=f0 + 14)
    cam = C.camera(lens=32, fstop=2.2, focus=st)
    C.cam_path(cam, [(a, (1.2, -1.25, 0.8)), (b, (0.5, -0.55, 0.3))],
               [(a, (0, 0, -0.05)), (b, (0, 0, 0.0))], handheld=0.006, seed=12)
    cam_light(cam, 40)


# ---------------------------------------------------------------- 13: cho'p bilan bosish
def shot13(a, b):
    tun, tl, tr = T.throat_world()
    C.point_light("Deep", (0, 9, 0), 400, (1.0, 0.35, 0.25), 0.6)
    contact = Vector((0.62, 4.05, -0.05))
    nrm = Vector((-1, -0.25, 0.05)).normalized()
    # paxtali cho'p
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.035, depth=4.0)
    stick = bpy.context.object
    stick.name = "Stick"
    C.assign(stick, C.principled("StickMat", (0.92, 0.9, 0.86), rough=0.5))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.1)
    tip = bpy.context.object
    tip.name = "Cotton"
    tip.scale = (1, 1, 1.7)
    C.displace(tip, "CLOUDS", size=0.015, strength=0.02, name="cot_d")
    C.subsurf(tip, 1)
    cot = C.principled("Cotton", (0.95, 0.95, 0.95), rough=0.9, sss=0.4, sss_scale=0.02)
    p = cot.node_tree.nodes["Principled BSDF"]
    p.inputs["Sheen Weight"].default_value = 1.0
    C.assign(tip, cot)
    swab = C.link(bpy.data.objects.new("Swab", None))
    stick.parent = swab
    stick.location = (0, 0, -2.0 - 0.1)
    tip.parent = swab
    tip.location = (0, 0, 0)
    dirv = (contact - Vector((0.1, 0.5, 0.15))).normalized()
    swab.rotation_euler = (-dirv).to_track_quat("-Z", "Y").to_euler()
    swab.rotation_euler = dirv.to_track_quat("Z", "Y").to_euler()
    # cho'p uchi oldinda (+Z), sopi orqada
    stick.location = (0, 0, -2.1)
    for f, d in [(a, -1.6), (a + 28, -0.12), (a + 50, 0.1), (a + 62, 0.05), (b, 0.14)]:
        swab.location = contact + dirv * d - dirv * 0.17
        swab.keyframe_insert("location", frame=f)
    # bez to'qimasi botadi (Warp modifier)
    e_from = C.link(bpy.data.objects.new("WarpFrom", None))
    e_to = C.link(bpy.data.objects.new("WarpTo", None))
    e_from.location = contact
    for f, d in [(a, 0.0), (a + 28, 0.0), (a + 50, 0.16), (a + 62, 0.12), (b, 0.18)]:
        e_to.location = contact + dirv * d
        e_to.keyframe_insert("location", frame=f)
    w = tr.modifiers.new("Press", "WARP")
    w.object_from = e_from
    w.object_to = e_to
    w.falloff_radius = 0.38
    w.falloff_type = "SMOOTH"
    # yallig'lanish: bez qizaradi
    pm = tr.active_material.node_tree.nodes["Principled BSDF"]
    for f, s in [(a + 30, 0.0), (b, 0.6)]:
        pm.inputs["Emission Strength"].default_value = s
        pm.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    pm.inputs["Emission Color"].default_value = (0.9, 0.05, 0.03, 1)
    # qon tomchilari
    blood = C.principled("Blood", (0.35, 0.0, 0.01), rough=0.08, coat=1.0, sss=0.3, sss_radius=(1, 0.1, 0.1))
    rng = random.Random(13)
    for i in range(10):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1)
        o = bpy.context.object
        C.assign(o, blood)
        C.smooth(o)
        off = Vector((rng.uniform(-0.05, 0.05), rng.uniform(-0.18, 0.18), rng.uniform(-0.2, 0.2)))
        o.location = contact + off + nrm * 0.02
        f0 = a + 52 + rng.randint(0, 25)
        o.scale = (0.001,) * 3
        o.keyframe_insert("scale", frame=f0)
        r = rng.uniform(0.02, 0.05)
        o.scale = (r, r, r * 1.3)
        o.keyframe_insert("scale", frame=f0 + 10)
        o.keyframe_insert("location", frame=f0 + 10)
        o.location.z -= rng.uniform(0.05, 0.2)
        o.keyframe_insert("location", frame=b)
    cam = C.camera(lens=24, fstop=2.8)
    tgt = C.cam_path(cam, [(a, (-0.35, 2.6, 0.45)), (b, (-0.05, 3.25, 0.3))],
                     [(a, contact + Vector((0, -0.3, 0))), (b, contact)], handheld=0.01, seed=13)
    cam.data.dof.focus_object = tgt
    cam_light(cam, 90)


# ---------------------------------------------------------------- 14: qon tomiri
def shot14(a, b):
    T.vessel_world()
    rbc = T.red_cell_mesh()
    rbc.hide_render = True
    rng = random.Random(14)
    n = b - a
    for i in range(160):
        o = C.link(bpy.data.objects.new(f"RBC{i}", rbc.data))
        ang = rng.uniform(0, 6.28)
        r = math.sqrt(rng.uniform(0, 1)) * 1.1
        y0 = rng.uniform(-2, 34)
        s = rng.uniform(0.16, 0.2)
        o.scale = (s, s, s)
        o.location = (r * math.cos(ang), y0, r * math.sin(ang))
        o.rotation_euler = (rng.uniform(0, 6), rng.uniform(0, 6), 0)
        o.keyframe_insert("location", frame=a)
        o.keyframe_insert("rotation_euler", frame=a)
        o.location.y += rng.uniform(5, 8)
        o.rotation_euler.x += rng.uniform(-3, 3)
        o.keyframe_insert("location", frame=b)
        o.keyframe_insert("rotation_euler", frame=b)
    bact_pts = []
    for i in range(45):
        ang = rng.uniform(0, 6.28)
        r = rng.uniform(0, 1.0)
        bact_pts.append((Vector((r * math.cos(ang), rng.uniform(2, 30), r * math.sin(ang))),
                         Vector((0, 0, 1))))
    objs = T.bacteria(bact_pts, a, b, seed=14, size=0.22, wiggle=0.05)
    for o in objs:
        o.keyframe_insert("location", frame=a)
        o.location.y += rng.uniform(5, 9)
        o.keyframe_insert("location", frame=b)
    cam = C.camera(lens=20, fstop=4.0)
    tgt = C.cam_path(cam, [(a, (0.0, -1.0, 0.1)), (b, (0.15, 20.0, -0.1))],
                     [(a, (0.0, 6, 0.0)), (b, (0.1, 30, 0.0))], ease="LINEAR", handheld=0.015, seed=14)
    cam.data.dof.focus_distance = 2.5
    cam.data.dof.focus_object = None
    cam_light(cam, 120, color=(1.0, 0.8, 0.75))
    for i in range(6):
        C.point_light(f"VL{i}", (0, 4 + i * 5, 0.9), 200, (1.0, 0.4, 0.35), 0.3)
