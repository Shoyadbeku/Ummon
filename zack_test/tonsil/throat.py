"""Tomoq ichi protsedural sahnalari: tunnel, bodomcha bezlar, yoriq (kripta),
tosh, bakteriyalar, o'lik hujayralar, gaz pufakchalari, qon tomiri."""
import math
import random

import bpy
import bmesh
from mathutils import Vector, Matrix

import common as C


# ------------------------------------------------------------------ geometriya
def revolve(name, profile, segs=96, flip=False):
    """profile: [(r, h), ...] — aylanish yuzasi (Z o'qi atrofida)."""
    me = bpy.data.meshes.new(name)
    verts, faces = [], []
    n = len(profile)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        ca, sa = math.cos(a), math.sin(a)
        for r, h in profile:
            verts.append((r * ca, r * sa, h))
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(n - 1):
            f = (i * n + j, i2 * n + j, i2 * n + j + 1, i * n + j + 1)
            faces.append(f[::-1] if flip else f)
    me.from_pydata(verts, [], faces)
    me.update()
    o = C.link(bpy.data.objects.new(name, me))
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(me)
    bm.free()
    C.smooth(o)
    return o


def capsule(name, r=0.02, length=0.08):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r)
    o = bpy.context.object
    o.name = name
    for v in o.data.vertices:
        if v.co.z > 0:
            v.co.z += (length / 2 - r)
        else:
            v.co.z -= (length / 2 - r)
    C.smooth(o)
    return o


# ------------------------------------------------------------------ materiallar
def flesh_mat(name="Flesh", c1=(0.45, 0.06, 0.07), c2=(0.78, 0.25, 0.25), sss=0.35, wet=0.5,
              scale=1.5, bump=0.35):
    m = C.principled(name, c1, rough=0.32, sss=sss, sss_radius=(1.0, 0.25, 0.15), sss_scale=0.15,
                     coat=wet)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.7
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    # mayda tomirchalar (voronoi qirralari)
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale * 2.2
    vor.inputs["Randomness"].default_value = 1.0
    warp = nt.nodes.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = scale * 2
    warp.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], warp.inputs["Vector"])
    wmix = nt.nodes.new("ShaderNodeMix")
    wmix.data_type = "VECTOR"
    wmix.inputs["Factor"].default_value = 0.25
    nt.links.new(tc.outputs["Object"], wmix.inputs["A"])
    nt.links.new(warp.outputs["Color"], wmix.inputs["B"])
    nt.links.new(wmix.outputs["Result"], vor.inputs["Vector"])
    vr = nt.nodes.new("ShaderNodeMapRange")
    vr.inputs["From Min"].default_value = 0.0
    vr.inputs["From Max"].default_value = 0.025
    vr.inputs["To Min"].default_value = 1.0
    vr.inputs["To Max"].default_value = 0.0
    nt.links.new(vor.outputs["Distance"], vr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = (0.35, 0.02, 0.04, 1)
    fm = nt.nodes.new("ShaderNodeMath")
    fm.operation = "MULTIPLY"
    fm.inputs[1].default_value = 0.3
    nt.links.new(vr.outputs["Result"], fm.inputs[0])
    nt.links.new(fm.outputs[0], mix.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["A"])
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    # nam, notekis yuza
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = scale * 12
    nz2.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = bump
    b.inputs["Distance"].default_value = 0.02
    nt.links.new(nz2.outputs["Fac"], b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return m


def stone_mat(name="StoneMat"):
    """Yumshoq (shilimshiq) -> qattiq (kalsifikatsiya) — 'Hard' qiymati 0..1 animatsiya qilinadi."""
    m = C.principled(name, (0.85, 0.75, 0.45), rough=0.35, sss=0.5, sss_radius=(1, 0.85, 0.5),
                     sss_scale=0.05, coat=0.6)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    hard = nt.nodes.new("ShaderNodeValue")
    hard.name = "Hard"
    hard.outputs[0].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6
    nz.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    soft = nt.nodes.new("ShaderNodeValToRGB")
    soft.color_ramp.elements[0].color = (0.95, 0.88, 0.62, 1)
    soft.color_ramp.elements[1].color = (0.78, 0.62, 0.3, 1)
    nt.links.new(nz.outputs["Fac"], soft.inputs["Fac"])
    hardc = nt.nodes.new("ShaderNodeValToRGB")
    hardc.color_ramp.elements[0].color = (0.66, 0.58, 0.42, 1)
    hardc.color_ramp.elements[1].color = (0.38, 0.31, 0.2, 1)
    nt.links.new(nz.outputs["Fac"], hardc.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(hard.outputs[0], mix.inputs["Factor"])
    nt.links.new(soft.outputs["Color"], mix.inputs["A"])
    nt.links.new(hardc.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])

    def lerp(a, b, sock):
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = a
        mr.inputs["To Max"].default_value = b
        nt.links.new(hard.outputs[0], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], p.inputs[sock])
    lerp(0.3, 0.85, "Roughness")
    lerp(0.6, 0.0, "Subsurface Weight")
    lerp(0.7, 0.0, "Coat Weight")
    # kristall bump: voronoi, qattiqlik bilan kuchayadi
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 30
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    bs = nt.nodes.new("ShaderNodeMapRange")
    bs.inputs["To Min"].default_value = 0.15
    bs.inputs["To Max"].default_value = 1.0
    nt.links.new(hard.outputs[0], bs.inputs["Value"])
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Distance"].default_value = 0.02
    nt.links.new(bs.outputs["Result"], b.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(vor.outputs["Distance"], add.inputs[0])
    nt.links.new(nz.outputs["Fac"], add.inputs[1])
    nt.links.new(add.outputs[0], b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return m, hard


def set_hard(mat, keys):
    v = mat.node_tree.nodes["Hard"].outputs[0]
    for f, x in keys:
        v.default_value = x
        v.keyframe_insert("default_value", frame=f)


def bacteria_mat():
    m = C.principled("Bact", (0.35, 0.7, 0.12), rough=0.25, sss=0.6, sss_radius=(0.5, 1.0, 0.3),
                     sss_scale=0.02, coat=0.8, emission=(0.4, 0.9, 0.1), emit_strength=0.4)
    C.add_noise_color(m, (0.55, 0.8, 0.15), (0.2, 0.5, 0.1), scale=30, bump=0.4, bump_scale=80)
    return m


def bubble_mat():
    m = C.principled("Bubble", (0.95, 0.95, 0.6), rough=0.02, transmission=1.0, ior=1.1)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Thin Wall"].default_value = True if p.inputs["Thin Wall"].type == "BOOLEAN" else 1.0
    p.inputs["Emission Color"].default_value = (0.8, 0.85, 0.2, 1)
    p.inputs["Emission Strength"].default_value = 0.15
    return m


# ------------------------------------------------------------------ obyektlar
def tonsil(name, loc, scale=(0.75, 0.9, 1.1), seed=0, crypt_strength=0.11):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=0.6, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    C.smooth(o)
    m1, t1 = C.displace(o, "CLOUDS", size=0.25, strength=0.12, depth=3, name=name + "_lump")
    # kriptalar: voronoi hujayra markazlari = chuqurchalar
    t = bpy.data.textures.new(name + "_crypt", "VORONOI")
    t.distance_metric = "DISTANCE"
    t.noise_scale = 0.13
    t.noise_intensity = 1.0
    t.weight_1 = 1.0
    t.contrast = 1.6
    m2 = o.modifiers.new(name + "_crypt", "DISPLACE")
    m2.texture = t
    m2.strength = crypt_strength
    m2.mid_level = 0.6
    m2.texture_coords = "LOCAL"
    C.subsurf(o, 1)
    C.assign(o, flesh_mat(name + "_m", c1=(0.62, 0.16, 0.16), c2=(0.88, 0.42, 0.4), sss=0.45, scale=3))
    return o


def throat_world():
    """Y o'qi bo'ylab tomoq tunneli, ikki yonda bodomcha bezlar, tepada tilcha."""
    C.world_color((0.05, 0.005, 0.005), 1.0)
    prof = []
    for i in range(150):
        y = -4 + 15 * i / 149
        r = 1.15 + 0.15 * math.sin(y * 1.3) - 0.25 * math.exp(-((y - 6.5) ** 2) / 2)
        if y > 9.0:                      # oxiri yopiq (qizilo'ngach burilishi)
            r *= max(0.0, 1 - ((y - 9.0) / 2.0) ** 2) ** 0.5
        prof.append((r, y))
    prof.append((0.0, 11.05))
    tun = revolve("Tunnel", prof, segs=128, flip=True)   # normallar ichkariga
    tun.rotation_euler[0] = math.radians(-90)              # Z o'qi -> +Y
    tun.scale = (1.3, 1.0, 1.0)
    C.displace(tun, "CLOUDS", size=0.35, strength=0.22, depth=3, name="tun_d")
    C.displace(tun, "CLOUDS", size=0.08, strength=0.03, depth=2, name="tun_d2")
    C.subsurf(tun, 1)
    tm = flesh_mat("TunFlesh", wet=0.2)
    tm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.45
    C.assign(tun, tm)
    tl = tonsil("TonsilL", (-1.15, 4.2, -0.1), seed=1)
    tr = tonsil("TonsilR", (1.15, 4.2, -0.1), seed=2)
    # tilcha (uvula)
    uv = capsule("Uvula", r=0.18, length=0.9)
    uv.location = (0, 3.2, 0.95)
    C.displace(uv, "CLOUDS", size=0.2, strength=0.04, name="uv_d")
    C.subsurf(uv, 1)
    C.assign(uv, flesh_mat("UvFlesh", c1=(0.7, 0.2, 0.2), c2=(0.9, 0.45, 0.42)))
    return tun, tl, tr


def crypt_world(depth=2.4):
    """Bez yuzasi va unga kirib boruvchi chuqur yoriq (kripta). Yuzasi z=0, yoriq -Z ga."""
    C.world_color((0.25, 0.04, 0.04), 0.6)
    prof = []
    for i in range(90):
        t = i / 89
        r = 16.0 * (1 - t) ** 2.4 + 0.0
        if r > 0.7:
            h = 0.12 * math.exp(-((r - 0.9) ** 2) / 0.08) + 0.6 * math.sin(r * 0.5) * min(1, (r - 0.7) / 4)
        else:
            k = (0.7 - r) / 0.7
            h = -depth * k ** 0.6
            r = 0.7 - (0.7 - r) * 0.45 + 0.08 * math.sin(k * 9)
        prof.append((max(r, 0.0), h))
    prof.append((0.0, -depth - 0.1))
    o = revolve("Crypt", prof, segs=128)
    o.scale = (1.0, 0.8, 1.0)
    C.displace(o, "CLOUDS", size=0.3, strength=0.18, depth=3, name="cr_d")
    C.displace(o, "CLOUDS", size=0.06, strength=0.025, depth=2, name="cr_d2")
    t = bpy.data.textures.new("cr_pits", "VORONOI")
    t.noise_scale = 0.5
    t.contrast = 1.5
    m = o.modifiers.new("cr_pits", "DISPLACE")
    m.texture = t
    m.strength = 0.18
    m.mid_level = 0.6
    C.subsurf(o, 1)
    fm = flesh_mat("CryptFlesh", c1=(0.55, 0.12, 0.12), c2=(0.86, 0.38, 0.36), sss=0.45, scale=1.2)
    C.assign(o, fm)
    # yoriq tubidagi qutbni yopuvchi to'qima bo'lagi
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.32, location=(0, 0, -depth + 0.05))
    plug = bpy.context.object
    plug.scale = (1.1, 0.9, 0.7)
    C.displace(plug, "CLOUDS", size=0.12, strength=0.08, name="plug_d")
    C.smooth(plug)
    C.assign(plug, fm)
    # atrofni yopuvchi katta "g'or" gumbazi (osmon ko'rinmasin)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=11, location=(0, 0, -1))
    dome = bpy.context.object
    dome.name = "Dome"
    C.displace(dome, "CLOUDS", size=1.5, strength=0.8, name="dome_d")
    C.smooth(dome)
    C.assign(dome, flesh_mat("DomeFlesh", c1=(0.35, 0.05, 0.05), c2=(0.6, 0.18, 0.16), sss=0.0, scale=0.4))
    return o


def stone(name="Stone", r=0.42, loc=(0, 0, -0.55)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=r, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (1.0, 0.85, 1.15)
    C.displace(o, "CLOUDS", size=r * 0.5, strength=r * 0.3, depth=3, name=name + "_d")
    C.displace(o, "CLOUDS", size=r * 0.12, strength=r * 0.06, depth=2, name=name + "_d2")
    C.smooth(o)
    m, hard = stone_mat(name + "_m")
    C.assign(o, m)
    return o, m


def scatter_on(obj, n, seed, rmin=0.0):
    """Ob'ekt yuzasidan tasodifiy nuqtalar (dunyo koordinatasida) va normal."""
    dg = bpy.context.evaluated_depsgraph_get()
    e = obj.evaluated_get(dg)
    me = e.to_mesh()
    rng = random.Random(seed)
    polys = list(me.polygons)
    mw = e.matrix_world
    out = []
    for _ in range(n):
        p = polys[rng.randrange(len(polys))]
        out.append((mw @ p.center, (mw.to_3x3() @ p.normal).normalized()))
    e.to_mesh_clear()
    return out


def bacteria(points, f0, f1, seed=0, size=0.05, wiggle=0.02, mat=None, scale_keys=None):
    """Har bir nuqtada qimirlaydigan tayoqcha bakteriya (linked duplicate)."""
    base = capsule("BactBase", r=size * 0.28, length=size)
    C.subsurf(base, 1)
    C.assign(base, mat or bacteria_mat())
    rng = random.Random(seed)
    objs = []
    from mixchar import _fcurves
    for i, (p, nrm) in enumerate(points):
        o = bpy.data.objects.new(f"Bact{i}", base.data)
        C.link(o)
        o.location = p + nrm * size * 0.3
        q = nrm.to_track_quat("Z", "Y")
        o.rotation_euler = (q.to_euler().x + rng.uniform(1.0, 2.0), rng.uniform(0, 6.28), rng.uniform(0, 6.28))
        s = rng.uniform(0.7, 1.3)
        o.scale = (s, s, s * rng.uniform(0.8, 1.4))
        o.keyframe_insert("location", frame=f0)
        o.keyframe_insert("rotation_euler", frame=f0)
        if scale_keys:
            for f, k in scale_keys:
                o.scale = (s * k, s * k, s * k)
                o.keyframe_insert("scale", frame=f + rng.randint(-6, 6))
        for fc in _fcurves(o.animation_data.action):
            if fc.data_path in ("location", "rotation_euler"):
                n = fc.modifiers.new("NOISE")
                n.scale = rng.uniform(6, 14)
                n.strength = wiggle if fc.data_path == "location" else 0.6
                n.phase = rng.uniform(0, 100)
        objs.append(o)
    base.hide_render = True
    base.hide_viewport = True
    return objs


def dead_cells(points, size=0.09, seed=3):
    """Yassi, oqish, yarim shaffof o'lik epiteliy hujayralari (yadro bilan)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=size, depth=size * 0.08)
    base = bpy.context.object
    base.name = "CellBase"
    C.displace(base, "CLOUDS", size=size * 0.6, strength=size * 0.25, name="cell_d")
    C.subsurf(base, 2)
    m = C.principled("DeadCell", (0.93, 0.9, 0.82), rough=0.4, sss=0.7, sss_radius=(1, 0.9, 0.8),
                     sss_scale=0.03, coat=0.5)
    C.assign(base, m)
    rng = random.Random(seed)
    out = []
    for i, (p, nrm) in enumerate(points):
        o = C.link(bpy.data.objects.new(f"Cell{i}", base.data))
        o.location = p + nrm * 0.01
        o.rotation_euler = nrm.to_track_quat("Z", "Y").to_euler()
        o.rotation_euler.z = rng.uniform(0, 6.28)
        s = rng.uniform(0.7, 1.4)
        o.scale = (s, s * rng.uniform(0.7, 1.1), 1)
        out.append(o)
    base.hide_render = True
    return out


def bubbles(origins, f0, f1, seed=5, rmin=0.02, rmax=0.07, rise=1.5):
    m = bubble_mat()
    rng = random.Random(seed)
    for i, p in enumerate(origins):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1)
        o = bpy.context.object
        o.name = f"Bub{i}"
        C.smooth(o)
        C.assign(o, m)
        r = rng.uniform(rmin, rmax)
        start = rng.randint(f0, f1 - 20)
        life = rng.randint(30, 60)
        o.scale = (0.001,) * 3
        o.location = p
        o.keyframe_insert("scale", frame=start - 1)
        o.keyframe_insert("location", frame=start)
        o.scale = (r,) * 3
        o.keyframe_insert("scale", frame=start + 6)
        o.location = p + Vector((rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), rise * rng.uniform(0.6, 1.2)))
        o.keyframe_insert("location", frame=start + life)
        o.scale = (r * 1.15,) * 3
        o.keyframe_insert("scale", frame=start + life)


def red_cell_mesh():
    """Eritrotsit: ikki tomoni botiq disk (aylanish yuzasi)."""
    prof = []
    N = 24
    for i in range(N + 1):
        r = i / N
        z = 0.5 * math.sqrt(max(0.0, 1 - r * r)) * (0.21 + 2.0 * r * r - 1.12 * r ** 4)
        prof.append((r, z))
    for i in range(N, -1, -1):
        r = i / N
        z = -0.5 * math.sqrt(max(0.0, 1 - r * r)) * (0.21 + 2.0 * r * r - 1.12 * r ** 4)
        prof.append((r, z))
    o = revolve("RBCBase", prof, segs=32, flip=True)
    m = C.principled("RBC", (0.6, 0.02, 0.02), rough=0.3, sss=0.6, sss_radius=(1, 0.1, 0.1),
                     sss_scale=0.05, coat=0.5)
    C.assign(o, m)
    return o


def vessel_world():
    C.world_color((0.08, 0.0, 0.0), 1.0)
    prof = []
    for i in range(120):
        y = -5 + 45 * i / 119
        prof.append((1.4 + 0.12 * math.sin(y * 0.7), y))
    v = revolve("Vessel", prof, segs=64, flip=True)
    v.rotation_euler[0] = math.radians(-90)
    C.displace(v, "CLOUDS", size=0.5, strength=0.12, name="ves_d")
    C.subsurf(v, 1)
    m = flesh_mat("VesselWall", c1=(0.5, 0.03, 0.03), c2=(0.75, 0.12, 0.1), sss=0.6, scale=0.8)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Emission Color"].default_value = (0.8, 0.05, 0.03, 1)
    p.inputs["Emission Strength"].default_value = 0.15
    C.assign(v, m)
    return v
