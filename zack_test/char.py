# Realistik odam: Blender Human Base Meshes (CC0) + avtomatik skelet + kiyim ranglari + soch
import bpy, bmesh, math
from mathutils import Vector, Matrix

ASSET = "/tmp/claude-0/assets/hbm/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
CX = -1.3400524854660034          # modelning asl X markazi

# skelet (A-poza, metr; front = -Y)
BONES = {  # name: (head, tail, parent)
 "hips":   ((0, 0.0, 0.92), (0, 0.0, 1.02), None),
 "spine":  ((0, 0.0, 1.02), (0, 0.0, 1.17), "hips"),
 "chest":  ((0, 0.0, 1.17), (0, 0.0, 1.36), "spine"),
 "neck":   ((0, -0.01, 1.38), (0, -0.02, 1.47), "chest"),
 "head":   ((0, -0.02, 1.47), (0, -0.02, 1.66), "neck"),
}
for s, k in (("L", 1), ("R", -1)):
    BONES.update({
     f"clav.{s}":  ((0.03*k, -0.01, 1.36), (0.15*k, 0.0, 1.37), "chest"),
     f"uarm.{s}":  ((0.17*k, 0.0, 1.35), (0.275*k, -0.01, 1.077), f"clav.{s}"),
     f"farm.{s}":  ((0.275*k, -0.01, 1.077), (0.37*k, -0.05, 0.83), f"uarm.{s}"),
     f"hand.{s}":  ((0.37*k, -0.05, 0.83), (0.42*k, -0.09, 0.70), f"farm.{s}"),
     f"thigh.{s}": ((0.09*k, 0.0, 0.90), (0.088*k, -0.01, 0.47), "hips"),
     f"shin.{s}":  ((0.088*k, -0.01, 0.47), (0.09*k, 0.03, 0.08), f"thigh.{s}"),
     f"foot.{s}":  ((0.09*k, 0.03, 0.08), (0.09*k, -0.11, 0.02), f"shin.{s}"),
    })

def _mat_skin_cloth(name, cols):
    """Rang atributi (cloth_id) bo'yicha teri/kiyim/soch-qosh/lab materiali."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "zone"
    # zone: R=kiyim1, G=kiyim2, B=poyabzal, A yo'q; brow/lip alohida
    a2 = N.new("ShaderNodeAttribute"); a2.attribute_name = "face"
    sep = N.new("ShaderNodeSeparateColor"); L.new(attr.outputs["Color"], sep.inputs[0])
    sep2 = N.new("ShaderNodeSeparateColor"); L.new(a2.outputs["Color"], sep2.inputs[0])
    def rgb(c):
        n = N.new("ShaderNodeRGB"); n.outputs[0].default_value = (*c, 1); return n.outputs[0]
    def mix(f, a, bb):
        n = N.new("ShaderNodeMix"); n.data_type = "RGBA"
        L.new(f, n.inputs["Factor"]); L.new(a, n.inputs[6]); L.new(bb, n.inputs[7]); return n.outputs[2]
    def mixf(f, a, bb):
        n = N.new("ShaderNodeMix"); n.data_type = "FLOAT"
        L.new(f, n.inputs["Factor"]); n.inputs[2].default_value = a; n.inputs[3].default_value = bb; return n.outputs[0]
    # teri: biroz notekis ton
    noise = N.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 60
    skin = mix(noise.outputs["Fac"], rgb(cols["skin"]), rgb(tuple(c*0.9 for c in cols["skin"])))
    c = mix(sep2.outputs[1], skin, rgb(cols["lip"]))
    c = mix(sep2.outputs[0], c, rgb(cols["brow"]))
    # mato teksturasi
    fab = N.new("ShaderNodeTexWave"); fab.inputs["Scale"].default_value = 400; fab.inputs["Distortion"].default_value = 4
    c1 = mix(fab.outputs["Fac"], rgb(cols["c1"]), rgb(tuple(x*0.85 for x in cols["c1"])))
    c2 = mix(fab.outputs["Fac"], rgb(cols["c2"]), rgb(tuple(x*0.8 for x in cols["c2"])))
    c = mix(sep.outputs[0], c, c1); c = mix(sep.outputs[1], c, c2); c = mix(sep.outputs[2], c, rgb(cols["shoe"]))
    L.new(c, b.inputs["Base Color"])
    cloth = N.new("ShaderNodeMath"); cloth.operation = "MAXIMUM"
    L.new(sep.outputs[0], cloth.inputs[0]); L.new(sep.outputs[1], cloth.inputs[1])
    L.new(mixf(cloth.outputs[0], 0.42, 0.85), b.inputs["Roughness"])
    L.new(mixf(cloth.outputs[0], 0.35, 0.0), b.inputs["Subsurface Weight"])
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.012
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
    L.new(noise.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    return m

def _mat_hair(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (300, 300, 4)          # ingichka tolalar
    L.new(tc.outputs["Object"], mp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Detail"].default_value = 8
    L.new(mp.outputs[0], nz.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*[c*0.45 for c in col], 1); ramp.color_ramp.elements[1].color = (*[min(1, c*1.6) for c in col], 1)
    L.new(nz.outputs["Fac"], ramp.inputs[0]); L.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Anisotropic"].default_value = 0.8
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4
    L.new(nz.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    return m

def _mat_eye(name, iris):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Normal"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); E = ramp.color_ramp.elements
    E[0].position = 0.0; E[0].color = (0.01, 0.01, 0.01, 1)
    E[1].position = 0.08; E[1].color = (*iris, 1)
    e = E.new(0.22); e.color = (*iris, 1)
    e = E.new(0.26); e.color = (0.85, 0.82, 0.8, 1)
    neg = N.new("ShaderNodeMath"); neg.operation = "ADD"; neg.inputs[1].default_value = 1.0
    L.new(sep.outputs["Y"], neg.inputs[0])      # oldinga qaragan normal (-Y) => 0
    L.new(neg.outputs[0], ramp.inputs[0]); L.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.05; b.inputs["Coat Weight"].default_value = 1.0
    return m

def _bone_parent(obj, arm, bone):
    obj.parent = arm; obj.parent_type = "BONE"; obj.parent_bone = bone
    bn = arm.data.bones[bone]
    obj.matrix_parent_inverse = (arm.matrix_world @ bn.matrix_local @ Matrix.Translation((0, bn.length, 0))).inverted()

def make_human(name, cols, hair="ponytail", widen=1.0, height=1.0, sleeves="short"):
    with bpy.data.libraries.load(ASSET) as (src, dst):
        dst.objects = ["GEO-body_female_realistic", "GEO-body_female_realistic.eye.L", "GEO-body_female_realistic.eye.R"]
    body, eyeL, eyeR = dst.objects
    sc = bpy.context.scene
    for o in (body, eyeL, eyeR):
        sc.collection.objects.link(o)
    body.name = name; body.location = (0, 0, 0)
    body.data = body.data.copy()
    # ko'zlar dunyoviy pozitsiyasi (asl joyidan siljitib)
    for e, ex in ((eyeL, 0.0329), (eyeR, -0.0329)):
        e.parent = None; e.matrix_parent_inverse = Matrix.Identity(4)
        e.location = (ex, -0.1216, 1.5344); e.rotation_euler = (0, 0, 0)
        e.data = e.data.copy(); e.data.materials.clear(); e.data.materials.append(_mat_eye(name+"_eye", cols["iris"]))
        for p in e.data.polygons: p.use_smooth = True
    eyes = [Vector(e.location) for e in (eyeL, eyeR)]

    me = body.data
    # --- zonalar: kiyim / poyabzal / qosh / lab ---
    zone = me.color_attributes.new("zone", "FLOAT_COLOR", "POINT")
    face = me.color_attributes.new("face", "FLOAT_COLOR", "POINT")
    cloth_vg = body.vertex_groups.new(name="cloth")
    ez = sum(e.z for e in eyes) / 2
    for v in me.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z    # mahalliy (markaz = 0)
        ax = abs(x)
        armpos = 0.68 < z < 1.38 and ax > 0.17 + (1.35 - z) / 0.65 * 0.25 - 0.06
        # A-poza qo'lida tirsak/bilak chegarasi: uzunlik bo'yicha
        r = r2 = s = 0.0
        if armpos:
            t = (1.35 - z) / 0.65            # 0 = yelka, 1 = barmoq uchi
            lim = 0.28 if sleeves == "short" else 0.78
            if t < lim: r = 1.0
        else:
            if 0.93 < z < 1.42 and not (z > 1.36 and ax < 0.07 and y < -0.02): r = 1.0   # ko'ylak
            if 0.09 < z <= 0.98: r2 = 1.0                                               # shim
            if z <= 0.115: s = 1.0                                                       # poyabzal
        if r2 and z > 0.93: r = 0.0
        zone.data[v.index].color = (r, r2, s, 1)
        if r or r2 or s: cloth_vg.add([v.index], 1.0, "REPLACE")
        brow = lip = 0.0
        for e in eyes:
            if abs(x - e.x) < 0.024 and ez + 0.014 < z < ez + 0.024 and y < e.y + 0.005 and abs(x) > 0.006: brow = 1.0
        if abs(x) < 0.022 and ez - 0.085 < z < ez - 0.065 and y < -0.10: lip = 1.0
        face.data[v.index].color = (brow, lip, 0, 1)

    me.materials.clear(); me.materials.append(_mat_skin_cloth(name+"_skin", cols))
    for p in me.polygons: p.use_smooth = True
    # kiyim qalinligi
    d = body.modifiers.new("cloth_thick", "DISPLACE"); d.vertex_group = "cloth"; d.strength = 0.007; d.mid_level = 0
    body.modifiers["Multires"].levels = 1; body.modifiers["Multires"].render_levels = 2

    # --- skelet ---
    ad = bpy.data.armatures.new(name+"_rig"); arm = bpy.data.objects.new(name+"_rig", ad)
    sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for bn, (h, t, p) in BONES.items():
        eb = ad.edit_bones.new(bn); eb.head = h; eb.tail = t
        eb.align_roll(Vector((0, -1, 0)))
        if p: eb.parent = ad.edit_bones[p]
        eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    # avtomatik og'irliklar (bone heat)
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    # armature modifikatori oxirida bo'lsin
    for e in (eyeL, eyeR):
        _bone_parent(e, arm, "head")

    # --- soch ---
    hm = _mat_hair(name+"_hair", cols["hair"])
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    def scalp(v):
        x, y, z = v.co
        return (z > 1.585) or (y > -0.035 and z > 1.50) or (y > 0.0 and z > 1.45)
    kill = [v for v in bm.verts if not scalp(v)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    for v in bm.verts:
        v.co += v.normal * 0.010
    hme = bpy.data.meshes.new(name+"_hairmesh"); bm.to_mesh(hme); bm.free()
    for a in list(hme.color_attributes): hme.color_attributes.remove(a)
    hob = bpy.data.objects.new(name+"_hair", hme); sc.collection.objects.link(hob)
    sm = hob.modifiers.new("smooth", "SMOOTH"); sm.factor = 1.0; sm.iterations = 6
    hob.modifiers.new("sol", "SOLIDIFY").thickness = 0.014
    sub = hob.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    hme.materials.append(hm)
    for p in hme.polygons: p.use_smooth = True
    parts = [hob]
    def blob(n, size, loc, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc, rotation=rot)
        o = bpy.context.object; o.name = n; o.scale = size
        bpy.ops.object.transform_apply(scale=True, rotation=True, location=False)
        o.data.materials.append(hm)
        for p in o.data.polygons: p.use_smooth = True
        parts.append(o); return o
    if hair == "ponytail":
        blob(name+"_tie", (0.022, 0.022, 0.022), (0, 0.10, 1.60))
        pt = blob(name+"_tail", (0.045, 0.04, 0.17), (0, 0.13, 1.46), (math.radians(-12), 0, 0))
        tp = pt.modifiers.new("taper", "SIMPLE_DEFORM"); tp.deform_method = "TAPER"; tp.factor = 0.8
    elif hair == "bun":
        blob(name+"_bun", (0.05, 0.045, 0.045), (0, 0.10, 1.63))
    for o in parts:
        _bone_parent(o, arm, "head")

    arm.scale = (widen*height, height, height)
    return arm
