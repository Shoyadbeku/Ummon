# Protsedural chaqaloq (~1 yosh, bo'yi 0.73 m): metaball tana -> mesh, oddiy skelet (avtomatik og'irliklar),
# ko'zlar, qovoqlar (uxlash / yig'lash), og'iz (ochiladi), ko'z yoshlari, taglik.
# Koordinatalar: chaqaloq -Y ga qaraydi, +Z tepa, chap = +X. Ildiz (0,0,0) = oyoq tagi.
import bpy, bmesh, math
from mathutils import Vector, Quaternion, Matrix

R = math.radians
SKIN = (0.86, 0.6, 0.49)


def _mat_skin(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Subsurface Weight"].default_value = 0.35
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.004
    b.inputs["Specular IOR Level"].default_value = 0.35
    tc = N.new("ShaderNodeTexCoord")
    # yonoqlar qizilligi + tizza/tirsaklar
    def blob(c, r):
        vm = N.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"; vm.inputs[1].default_value = c
        L.new(tc.outputs["Object"], vm.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = r; mr.inputs["From Max"].default_value = 0.0
        L.new(vm.outputs["Value"], mr.inputs["Value"]); return mr.outputs[0]
    add = N.new("ShaderNodeMath"); add.operation = "MAXIMUM"
    L.new(blob((0.036, -0.055, 0.615), 0.03), add.inputs[0]); L.new(blob((-0.036, -0.055, 0.615), 0.03), add.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"; base.inputs["Factor"].default_value = 0.08
    base.inputs[6].default_value = (*SKIN, 1); base.inputs[7].default_value = (0.75, 0.48, 0.42, 1)
    L.new(nz.outputs["Fac"], base.inputs["Factor"])
    blush = N.new("ShaderNodeMix"); blush.data_type = "RGBA"
    L.new(add.outputs[0], blush.inputs["Factor"]); L.new(base.outputs[2], blush.inputs[6])
    blush.inputs[7].default_value = (0.9, 0.45, 0.4, 1)
    # siyrak sochlar (bosh tepasi)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    hz = N.new("ShaderNodeMapRange"); hz.inputs["From Min"].default_value = 0.66; hz.inputs["From Max"].default_value = 0.70
    L.new(sep.outputs["Z"], hz.inputs["Value"])
    hy = N.new("ShaderNodeMapRange"); hy.inputs["From Min"].default_value = -0.035; hy.inputs["From Max"].default_value = -0.01
    hy.inputs["To Min"].default_value = 0.0; hy.inputs["To Max"].default_value = 1.0
    L.new(sep.outputs["Y"], hy.inputs["Value"])
    hm = N.new("ShaderNodeMath"); hm.operation = "MULTIPLY"; L.new(hz.outputs[0], hm.inputs[0]); L.new(hy.outputs[0], hm.inputs[1])
    hw = N.new("ShaderNodeTexWave"); hw.inputs["Scale"].default_value = 140; hw.inputs["Distortion"].default_value = 14; hw.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], hw.inputs["Vector"])
    hm2 = N.new("ShaderNodeMath"); hm2.operation = "MULTIPLY"; L.new(hm.outputs[0], hm2.inputs[0]); L.new(hw.outputs["Fac"], hm2.inputs[1])
    hm3 = N.new("ShaderNodeMath"); hm3.operation = "MULTIPLY"; hm3.inputs[1].default_value = 0.55; L.new(hm2.outputs[0], hm3.inputs[0])
    hair = N.new("ShaderNodeMix"); hair.data_type = "RGBA"; L.new(hm3.outputs[0], hair.inputs["Factor"])
    L.new(blush.outputs[2], hair.inputs[6]); hair.inputs[7].default_value = (0.45, 0.3, 0.16, 1)
    L.new(hair.outputs[2], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.05; L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    return m


def _mat(name, col, rough=0.5, coat=0.0, emit=0.0, sss=0.0, alpha=1.0, trans=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Alpha"].default_value = alpha; b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m


def _eye_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.08; b.inputs["Coat Weight"].default_value = 1.0
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    # ob'ekt -Y ga qaraydi: old nuqtadan masofa = sqrt(x^2+z^2) (birlik sferada)
    xz = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs["X"], xz.inputs["X"]); L.new(sep.outputs["Z"], xz.inputs["Y"])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(xz.outputs[0], ln.inputs[0])
    front = N.new("ShaderNodeMath"); front.operation = "LESS_THAN"; front.inputs[1].default_value = 0.0
    L.new(sep.outputs["Y"], front.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(ln.outputs["Value"], cr.inputs["Fac"])
    e = cr.color_ramp; e.interpolation = "EASE"
    e.elements[0].position = 0.0; e.elements[0].color = (0.005, 0.004, 0.004, 1)
    e.elements[1].position = 0.27; e.elements[1].color = (0.12, 0.07, 0.035, 1)
    p = e.elements.new(0.52); p.color = (0.18, 0.11, 0.06, 1)
    p = e.elements.new(0.58); p.color = (0.9, 0.88, 0.86, 1)
    p = e.elements.new(1.0); p.color = (0.95, 0.93, 0.92, 1)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(front.outputs[0], mx.inputs["Factor"])
    mx.inputs[6].default_value = (0.95, 0.93, 0.92, 1); L.new(cr.outputs["Color"], mx.inputs[7])
    L.new(mx.outputs[2], b.inputs["Base Color"])
    return m


BONES = {  # nom: (bosh, dum, ota)
    "hips": ((0, 0, 0.30), (0, 0, 0.40), None),
    "spine": ((0, 0, 0.40), (0, 0, 0.53), "hips"),
    "neck": ((0, 0, 0.53), (0, 0, 0.585), "spine"),
    "head": ((0, 0, 0.585), (0, 0, 0.74), "neck"),
    "upper_arm.L": ((0.095, 0, 0.515), (0.215, 0, 0.515), "spine"),
    "forearm.L": ((0.215, 0, 0.515), (0.325, 0, 0.515), "upper_arm.L"),
    "hand.L": ((0.325, 0, 0.515), (0.375, 0, 0.515), "forearm.L"),
    "upper_arm.R": ((-0.095, 0, 0.515), (-0.215, 0, 0.515), "spine"),
    "forearm.R": ((-0.215, 0, 0.515), (-0.325, 0, 0.515), "upper_arm.R"),
    "hand.R": ((-0.325, 0, 0.515), (-0.375, 0, 0.515), "forearm.R"),
    "thigh.L": ((0.05, 0, 0.33), (0.05, 0, 0.185), "hips"),
    "shin.L": ((0.05, 0, 0.185), (0.05, 0, 0.05), "thigh.L"),
    "foot.L": ((0.05, 0, 0.05), (0.05, -0.08, 0.02), "shin.L"),
    "thigh.R": ((-0.05, 0, 0.33), (-0.05, 0, 0.185), "hips"),
    "shin.R": ((-0.05, 0, 0.185), (-0.05, 0, 0.05), "thigh.R"),
    "foot.R": ((-0.05, 0, 0.05), (-0.05, -0.08, 0.02), "shin.R"),
}


def _ell(name, c, r):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    for v in o.data.vertices: v.co = Vector((v.co.x * r[0] + c[0], v.co.y * r[1] + c[1], v.co.z * r[2] + c[2]))
    return o


def _caps(name, p0, p1, r0, r1=None):
    """kapsula p0 -> p1 (radius r0 dan r1 ga)"""
    r1 = r1 or r0
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=24, radius=1, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    for v in o.data.vertices:
        t = 1.0 if v.co.z > 0 else 0.0
        rr = r1 if t else r0
        v.co = Vector((v.co.x * rr, v.co.y * rr, v.co.z * rr + t * L))
    q = Vector((0, 0, 1)).rotation_difference(d)
    for v in o.data.vertices: v.co = q @ v.co + p0
    return o


def _union_body(sc):
    P = []
    # bosh va yuz
    P.append(_ell("head", (0, 0.005, 0.648), (0.068, 0.074, 0.076)))
    for s in (1, -1):
        P.append(_ell("cheek", (s * 0.03, -0.031, 0.612), (0.033, 0.031, 0.027)))
        P.append(_ell("ear", (s * 0.068, 0.006, 0.645), (0.009, 0.016, 0.022)))
    P.append(_ell("chin", (0, -0.044, 0.592), (0.026, 0.025, 0.022)))
    P.append(_ell("nose", (0, -0.066, 0.632), (0.012, 0.01, 0.01)))
    P.append(_ell("lipU", (0, -0.062, 0.611), (0.013, 0.008, 0.004)))
    P.append(_ell("neck", (0, 0.004, 0.562), (0.036, 0.034, 0.04)))
    # tana
    P.append(_ell("torso", (0, 0.0, 0.45), (0.084, 0.066, 0.115)))
    P.append(_ell("belly", (0, -0.014, 0.405), (0.077, 0.07, 0.07)))
    P.append(_ell("pelvis", (0, 0.004, 0.335), (0.083, 0.064, 0.06)))
    for s in (1, -1):
        P.append(_ell("shoulder", (s * 0.083, 0, 0.513), (0.04, 0.038, 0.038)))
        P.append(_caps("uarm", (s * 0.09, 0, 0.515), (s * 0.215, 0, 0.515), 0.033, 0.029))
        P.append(_caps("farm", (s * 0.215, 0, 0.515), (s * 0.322, 0, 0.515), 0.028, 0.023))
        P.append(_ell("hand", (s * 0.345, -0.003, 0.513), (0.03, 0.017, 0.025)))
        P.append(_caps("thumb", (s * 0.33, -0.012, 0.515), (s * 0.345, -0.03, 0.52), 0.008, 0.007))
        P.append(_caps("thigh", (s * 0.05, 0, 0.335), (s * 0.05, 0, 0.185), 0.047, 0.04))
        P.append(_caps("shin", (s * 0.05, 0, 0.185), (s * 0.05, 0, 0.055), 0.036, 0.027))
        P.append(_ell("foot", (s * 0.05, -0.024, 0.027), (0.03, 0.055, 0.026)))
    bpy.ops.object.select_all(action="DESELECT")
    for o in P: o.select_set(True)
    bpy.context.view_layer.objects.active = P[0]
    bpy.ops.object.join()
    body = bpy.context.object; body.name = "baby_body"
    rm = body.modifiers.new("rm", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.0028; rm.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier="rm")
    sm = body.modifiers.new("sm", "CORRECTIVE_SMOOTH"); sm.iterations = 6; sm.factor = 0.5; sm.use_only_smooth = True
    bpy.ops.object.modifier_apply(modifier="sm")
    for p in body.data.polygons: p.use_smooth = True
    return body


def _armature(sc):
    a = bpy.data.armatures.new("baby_arm"); arm = bpy.data.objects.new("baby_arm", a); sc.collection.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for n, (h, t, p) in BONES.items():
        eb = a.edit_bones.new(n); eb.head = h; eb.tail = t; eb.roll = 0
        if p: eb.parent = a.edit_bones[p]; eb.use_connect = (Vector(a.edit_bones[p].tail) - Vector(h)).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones: pb.rotation_mode = "QUATERNION"
    return arm


def build(sc, name="baby"):
    body = _union_body(sc)
    skin = _mat_skin(name + "_skin"); body.data.materials.append(skin)
    # og'iz: shape key (botiq) — "line" (yopiq lab chizig'i), "cry" (katta ochiq)
    body.shape_key_add(name="Basis", from_mix=False)
    MC = Vector((0, -0.066, 0.606))
    for kn, rx, rz, depth in (("line", 0.011, 0.0018, 0.0014), ("cry", 0.018, 0.012, 0.016)):
        kb = body.shape_key_add(name=kn, from_mix=False); kb.value = 0.0
        for i, v in enumerate(body.data.vertices):
            d = v.co - MC
            if d.y > 0.02 or v.co.y > -0.04: continue
            e = (d.x / rx) ** 2 + (d.z / rz) ** 2
            if e < 2.5:
                w = math.exp(-e * e * 1.2)
                kb.data[i].co = v.co + Vector((0, depth * w, 0))
                if kn == "cry" and 1.0 < e < 2.5: kb.data[i].co.y -= 0.0012 * math.exp(-(e - 1.6) ** 2 * 6)
    body.data.shape_keys.key_blocks["line"].value = 1.0
    arm = _armature(sc)
    # taglik: tana nusxasidan chanoq qismi
    dia = body.copy(); dia.data = body.data.copy(); dia.name = name + "_diaper"; sc.collection.objects.link(dia)
    bm = bmesh.new(); bm.from_mesh(dia.data)
    kill = [v for v in bm.verts if not (0.25 < v.co.z < 0.39 and (v.co.z > 0.305 + 0.55 * (abs(v.co.x) - 0.03) or abs(v.co.x) < 0.03))]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(dia.data); bm.free()
    dia.data.materials.clear()
    dmat = _mat(name + "_diaper_m", (0.92, 0.93, 0.95), 0.75, sss=0.1)
    nb = dmat.node_tree.nodes; nz = nb.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90
    bp = nb.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    dmat.node_tree.links.new(nz.outputs["Fac"], bp.inputs["Height"]); dmat.node_tree.links.new(bp.outputs[0], nb["Principled BSDF"].inputs["Normal"])
    dia.data.materials.append(dmat)
    so = dia.modifiers.new("so", "SOLIDIFY"); so.thickness = 0.006; so.offset = 1.0
    dis = dia.modifiers.new("ds", "DISPLACE"); dis.strength = 0.006; dis.direction = "NORMAL"
    # skelet bog'lash (avtomatik og'irliklar)
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    # taglik: og'irliklarni tanadan ko'chirish
    dia.parent = arm
    dt = dia.modifiers.new("dt", "DATA_TRANSFER"); dt.object = body; dt.use_vert_data = True
    dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "NEAREST"
    bpy.context.view_layer.objects.active = dia
    bpy.ops.object.datalayout_transfer(modifier="dt")
    bpy.ops.object.modifier_apply(modifier="dt")
    am = dia.modifiers.new("arm", "ARMATURE"); am.object = arm
    bpy.ops.object.modifier_move_to_index(modifier="arm", index=0)
    # ko'zlar, qovoqlar, og'iz (head suyagiga bog'langan)
    hb = arm.data.bones["head"]
    def to_head(o):
        mb = o.matrix_basis.copy(); o.parent = arm; o.parent_type = "BONE"; o.parent_bone = "head"
        o.matrix_parent_inverse = Matrix.Identity(4); bpy.context.view_layer.update()
        P = o.matrix_world @ o.matrix_basis.inverted()
        o.matrix_parent_inverse = P.inverted(); o.matrix_basis = mb
    eye_m = _eye_mat(name + "_eye")
    lid_m = _mat(name + "_lid", (0.84, 0.57, 0.47), 0.5, sss=0.3)
    lid_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.002
    parts = {}
    for s, side in ((1, "L"), (-1, "R")):
        c = Vector((s * 0.025, -0.0565, 0.652))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=c)
        e = bpy.context.object; e.name = f"{name}_eye{side}"; e.data.materials.append(eye_m); e.scale = (0.012,) * 3
        for p in e.data.polygons: p.use_smooth = True
        e.rotation_euler = (0, 0, R(-s * 8)); to_head(e)
        # yuqori va pastki qovoq (yarim sferalar, X o'qi atrofida aylanadi)
        for lid, sign in (("up", 1), ("lo", -1)):
            piv = bpy.data.objects.new(f"{name}_lid{lid}{side}", None); sc.collection.objects.link(piv); piv.location = c
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.0125, location=(0, 0, 0))
            l = bpy.context.object; l.name = f"{name}_lidm{lid}{side}"
            bm = bmesh.new(); bm.from_mesh(l.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z * sign < -0.0005], context="VERTS")
            bm.to_mesh(l.data); bm.free()
            sl = l.modifiers.new("so", "SOLIDIFY"); sl.thickness = 0.0008
            for p in l.data.polygons: p.use_smooth = True
            l.data.materials.append(lid_m); l.parent = piv
            to_head(piv)
            parts[f"lid{lid}{side}"] = piv
        parts["eye" + side] = e
    # og'iz
    mo = bpy.data.objects.new(name + "_mouthp", None); sc.collection.objects.link(mo); mo.location = (0, -0.047, 0.606)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(0, 0, 0))
    mm = bpy.context.object; mm.name = name + "_mouth"; mm.parent = mo
    for p in mm.data.polygons: p.use_smooth = True
    mm.data.materials.append(_mat(name + "_mouth_m", (0.05, 0.006, 0.01), 0.7))
    mm.scale = (0.012, 0.006, 0.002)
    to_head(mo); parts["mouth"] = mm
    # ko'z yoshlari
    tear_m = _mat(name + "_tear", (0.8, 0.85, 0.9), 0.02, coat=1.0, trans=0.9)
    tears = []
    for s in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.0026, location=(s * 0.031, -0.066, 0.628))
        t = bpy.context.object; t.name = f"{name}_tear{s}"; t.scale = (1, 0.6, 1.8); t.data.materials.append(tear_m)
        for p in t.data.polygons: p.use_smooth = True
        to_head(t); tears.append(t)
    parts["tears"] = tears; parts["body"] = body
    root = bpy.data.objects.new(name + "_root", None); sc.collection.objects.link(root)
    arm.parent = root
    return root, arm, body, dia, parts


# --------- pozalar (armatura fazosida burilishlar, gradusda: (o'q, burchak) ro'yxati) ---------
def _q(spec):
    q = Quaternion()
    for ax, a in spec:
        q = Quaternion({"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[ax], R(a)) @ q
    return q


def local_q(arm, bone, q_arm):
    B = arm.data.bones[bone].matrix_local.to_quaternion()
    return B.inverted() @ q_arm @ B


POSES = {
    "tpose": {},
    "stand": {"upper_arm.L": [("y", 72)], "upper_arm.R": [("y", -72)], "forearm.L": [("z", -15)], "forearm.R": [("z", 15)]},
    # o'tirish (polda): sonlar oldinga, boldirlar pastga
    "sit": {"thigh.L": [("x", -85), ("z", 12)], "thigh.R": [("x", -85), ("z", -12)], "shin.L": [("x", 40)], "shin.R": [("x", 40)],
            "spine": [("x", -8)], "upper_arm.L": [("y", 65), ("z", -20)], "upper_arm.R": [("y", -65), ("z", 20)],
            "forearm.L": [("z", -40)], "forearm.R": [("z", 40)]},
    # tik turib, qo'llar oldinga-yuqoriga (panjarani ushlab)
    "hold": {"upper_arm.L": [("z", -80), ("x", 35)], "upper_arm.R": [("z", 80), ("x", 35)], "forearm.L": [("z", -10)], "forearm.R": [("z", 10)],
             "spine": [("x", -6)], "head": [("x", 10)]},
    # panjara orasidan o'tish: oldinga engashgan
    "lean": {"spine": [("x", -35)], "hips": [("x", -10)], "head": [("x", 15)], "upper_arm.L": [("z", -85), ("x", 15)], "upper_arm.R": [("z", 85), ("x", 15)],
             "thigh.L": [("x", -20)], "thigh.R": [("x", 10)], "shin.L": [("x", 25)], "shin.R": [("x", 5)]},
    # yiqilish: qo'llar tepada, oyoqlar bukilgan
    "flail": {"upper_arm.L": [("y", -55), ("z", -20)], "upper_arm.R": [("y", 55), ("z", 20)], "forearm.L": [("y", -25)], "forearm.R": [("y", 25)],
              "thigh.L": [("x", -45), ("z", 15)], "thigh.R": [("x", -60), ("z", -15)], "shin.L": [("x", 70)], "shin.R": [("x", 55)],
              "spine": [("x", 12)], "head": [("x", -10)]},
    # qo'lda yotish (chalqancha, tizzalar bukilgan, qo'llar ko'krakda)
    "cradle": {"thigh.L": [("x", -55), ("z", 8)], "thigh.R": [("x", -50), ("z", -8)], "shin.L": [("x", 60)], "shin.R": [("x", 55)],
               "upper_arm.L": [("y", 68), ("z", -10)], "upper_arm.R": [("y", -68), ("z", 10)],
               "forearm.L": [("z", -45)], "forearm.R": [("z", 45)], "spine": [("x", -10)], "head": [("x", -8)]},
}


def pose_q(name):
    return {b: _q(spec) for b, spec in POSES[name].items()}


def apply_pose(arm, f, weights, extra=None):
    """weights: {poza: og'irlik}; extra: {suyak: [(o'q, burchak)]} qo'shimcha (silkitish)."""
    tot = sum(weights.values())
    for pb in arm.pose.bones:
        q = Quaternion(); acc = 0.0
        for pn, w in weights.items():
            if w <= 0: continue
            qp = _q(POSES[pn].get(pb.name, []))
            acc += w
            q = q.slerp(qp, w / acc) if acc > w else qp
        if extra and pb.name in extra:
            q = _q(extra[pb.name]) @ q
        pb.rotation_quaternion = local_q(arm, pb.name, q)
        pb.keyframe_insert("rotation_quaternion", frame=f)


def face(parts, f, lids=0.0, mouth=0.0, tears=0.0):
    """lids: 0 ochiq, 1 yopiq; mouth: 0 yopiq, 1 yig'lash (katta ochiq)."""
    for side in ("L", "R"):
        up = parts["lidup" + side]; lo = parts["lidlo" + side]
        # yuqori qovoq: ochiq -> orqaga (-X burilish), yopiq -> ko'zni yopadi
        up.rotation_euler = (R(-38 + 125 * lids), 0, 0); up.keyframe_insert("rotation_euler", frame=f)
        lo.rotation_euler = (R(72 - 22 * lids), 0, 0); lo.keyframe_insert("rotation_euler", frame=f)
    m = parts["mouth"]
    m.scale = (0.004 + 0.014 * mouth, 0.008, 0.001 + 0.0095 * mouth); m.keyframe_insert("scale", frame=f)
    kb = parts["body"].data.shape_keys.key_blocks
    kb["cry"].value = mouth; kb["cry"].keyframe_insert("value", frame=f)
    kb["line"].value = 1.0 - mouth; kb["line"].keyframe_insert("value", frame=f)
    for t in parts["tears"]:
        t.hide_render = tears < 0.5; t.keyframe_insert("hide_render", frame=f)
