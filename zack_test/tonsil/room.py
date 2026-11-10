"""Mehmonxona sahnasi (Poly Haven CC0 mebel + teksturalar) va Megan."""
import math
import os

import bpy
from mathutils import Vector

import common as C
import mixchar as M

PH = lambda *p: os.path.join(C.ASSETS, "ph", *p)
MX = lambda *p: os.path.join(C.ASSETS, "mixamo", *p)


def import_gltf(path, loc=(0, 0, 0), rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = C.link(bpy.data.objects.new(os.path.basename(path) + "_root", None))
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc
    root.rotation_euler[2] = rot_z
    root.scale = (scale,) * 3
    return root


def build_room():
    C.world_hdri(PH("hdri", "kloofendal_48d_partly_cloudy_puresky.hdr"), strength=0.35, rot=1.2)

    # pol
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Floor"
    C.assign(floor, C.pbr_texture("Laminate", PH("tex", "laminate_floor_02"), scale=3.0, rough_mult=0.7))

    wall_mat = C.pbr_texture("Plaster", PH("tex", "painted_plaster_wall"), scale=2.0)
    wall_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.75, 0.68, 1)
    # Tekstura juda oq — iliq rangga bo'yaymiz
    nt = wall_mat.node_tree
    p = nt.nodes["Principled BSDF"]
    for l in list(p.inputs["Base Color"].links):
        src = l.from_socket
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs["B"].default_value = (0.86, 0.74, 0.62, 1)
        nt.links.new(src, mix.inputs["A"])
        nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])

    walls = []
    for name, loc, rot in [
        ("WallBack", (0, 3.2, 2.0), (math.pi / 2, 0, 0)),
        ("WallLeft", (-3.5, 0, 2.0), (math.pi / 2, 0, math.pi / 2)),
        ("WallFront", (0, -4.5, 2.0), (math.pi / 2, 0, 0)),
    ]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
        w = bpy.context.object
        w.name = name
        w.scale = (10, 4.0, 1)
        C.assign(w, wall_mat)
        walls.append(w)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 3.6))
    ceil = bpy.context.object
    ceil.name = "Ceiling"
    C.assign(ceil, C.principled("CeilMat", (0.85, 0.82, 0.78), 0.8))
    # o'ng devor deraza bilan: deraza o'rni ochiq qoladi (HDRI ko'rinadi)
    for nm, loc, sc in [("WallR1", (3.5, -2.4, 2.0), (4.2, 4.0)), ("WallR2", (3.5, 3.0, 2.0), (2.6, 4.0)),
                        ("WallR3", (3.5, 0.6, 0.45), (1.8, 0.9)), ("WallR4", (3.5, 0.6, 3.3), (1.8, 0.7))]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.pi / 2, 0, math.pi / 2))
        w = bpy.context.object
        w.name = nm
        w.scale = (*sc, 1)
        C.assign(w, wall_mat)
    # plintus
    bpy.ops.mesh.primitive_cube_add(location=(0, 3.18, 0.05))
    sk = bpy.context.object
    sk.scale = (5, 0.02, 0.05)
    C.assign(sk, C.principled("Skirt", (0.9, 0.88, 0.85), 0.4))

    # mebel
    import_gltf(PH("models", "Sofa_01", "Sofa_01.gltf"), loc=(0.2, 2.55, 0), rot_z=0)
    import_gltf(PH("models", "modern_coffee_table_01", "modern_coffee_table_01.gltf"), loc=(0.3, 1.35, 0))
    import_gltf(PH("models", "potted_plant_01", "potted_plant_01.gltf"), loc=(-2.6, 2.6, 0), scale=1.6)
    import_gltf(PH("models", "potted_plant_01", "potted_plant_01.gltf"), loc=(2.7, 2.7, 0), scale=1.3, rot_z=1.0)
    fr = import_gltf(PH("models", "fancy_picture_frame_01", "fancy_picture_frame_01.gltf"),
                     loc=(0.2, 3.17, 1.75), scale=2.2)

    # yorug'lik: o'ngda deraza (katta iliq area), orqadan rim, old fill
    C.area_light("Window", (3.45, 0.6, 1.9), (0, math.radians(90), 0), 1.8, 700,
                 color=(1.0, 0.93, 0.82), size_y=2.0)
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 4.0
    sun.angle = math.radians(2)
    sun.color = (1.0, 0.9, 0.75)
    so = C.link(bpy.data.objects.new("Sun", sun))
    so.rotation_euler = (math.radians(55), 0, math.radians(75))
    C.area_light("Fill", (-1.5, -3.0, 2.2), (math.radians(65), 0, math.radians(-25)), 3.0, 180,
                 color=(0.8, 0.88, 1.0))
    C.area_light("Rim", (-1.2, 2.9, 2.6), (math.radians(-130), 0, math.radians(20)), 1.2, 260,
                 color=(1.0, 0.85, 0.7))
    return floor


def add_megan(anims, rot_z=0.0, loc=(0, 0, 0)):
    """anims: [(nom, boshlanish, tezlik, ekstrapolyatsiya, blend_in, blend_out), ...]
    Ro'yxatda keyingisi NLA da yuqorida (ustun) turadi."""
    root, arm, meshes = M.import_character(MX("char", "Megan.fbx"), "Megan")
    root.location = loc
    root.rotation_euler[2] = rot_z
    cache = {}
    for name, start, speed, extrap, bin_, bout in anims:
        if name not in cache:
            cache[name] = M.load_action(MX("anim", name + ".fbx"))
        s = M.apply_action(arm, cache[name], start=start, speed=speed)
        s.use_auto_blend = False
        s.extrapolation = extrap
        s.blend_in = bin_
        s.blend_out = bout
    return root, arm, meshes


def stone_ball(name="Stone", r=0.012):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r)
    o = bpy.context.object
    o.name = name
    o.scale = (1.0, 0.85, 0.78)
    C.displace(o, "CLOUDS", size=r * 0.6, strength=r * 0.35, depth=3, coords="LOCAL", name=name + "_d")
    C.smooth(o)
    m = C.principled("StoneMat", (0.86, 0.74, 0.42), rough=0.65, sss=0.3,
                     sss_radius=(1, 0.8, 0.4), sss_scale=0.004)
    C.add_noise_color(m, (0.93, 0.86, 0.6), (0.72, 0.58, 0.28), scale=400, bump=0.6, bump_scale=900)
    C.assign(o, m)
    return o
