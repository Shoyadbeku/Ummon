"""Water intoxication short - Zack D. Films style. One Blender scene per shot.

usage (from any dir):
  python3 film.py --shot 1 --frames 1-53 --pct 50 --out /path/frames/    # render
  python3 film.py --shot 1 --test 30 --pct 50 --out /path/test.png       # one frame
"""
import sys, os, math, random, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Euler, Matrix
from common import *

# shot -> frames (24 fps), sums to 1020 = 42.5 s of narration
# Cycles samples per shot (OIDN denoised) - tuned for CPU render time
SAMPLES = {1: 16, 2: 16, 3: 16, 4: 12, 5: 8, 6: 8, 7: 10, 8: 12, 9: 12, 10: 12, 11: 12, 12: 16}
NO_PERSIST = {1, 2, 3, 12}   # every shot with the skinned character
SHOTS = {1: 53, 2: 58, 3: 74, 4: 98, 5: 91, 6: 94, 7: 118, 8: 89, 9: 88, 10: 94, 11: 91, 12: 72}
PH = os.path.join(ASSETS, "ph")
BK = os.path.join(ASSETS, "bk")


# ====================================================================== props
def bottle(name="Bottle", water=1.0, scale=2.2):
    """BlenderKit 'Water bottle' (Draco decoded), scaled to a ~1.5 L bottle."""
    root, objs = import_gltf(os.path.join(BK, "bottle_dec.glb"), name)
    root.scale = (scale,) * 3
    for o in objs:
        if o.type != "MESH":
            continue
        # match on the original material name: object names get renamed on re-import
        n = o.material_slots[0].material.name.lower() if o.material_slots and o.material_slots[0].material else ""
        if n.startswith("circle.000_baked"):            # outer plastic
            assign(o, PLASTIC)
            bb = [Vector(c) for c in o.bound_box]
            lo = min(c.z for c in bb); hi = max(c.z for c in bb); rad = max(c.x for c in bb)
            bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=rad * 1.012, depth=(hi - lo) * 0.24,
                                                location=(0, 0, lo + (hi - lo) * 0.45), end_fill_type="NOTHING")
            lab = bpy.context.object; lab.name = name + "_Label"; smooth(lab); assign(lab, LABEL)
            lab.parent = o; lab.matrix_parent_inverse = Matrix.Identity(4)
            lab.location = (0, 0, lo + (hi - lo) * 0.45)
        elif n.startswith("circle.001_baked"):          # liquid
            if water <= 0.01:
                o.hide_render = True
            else:
                assign(o, WATER)
        smooth(o)
    return root


def make_materials():
    global PLASTIC, WATER, LABEL
    # thin clear PET shell: transparent + fresnel gloss (a solid glass shell reads milky)
    PLASTIC = bpy.data.materials.new("Plastic"); nt = PLASTIC.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); mx = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs[0].default_value = (0.93, 0.97, 1.0, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.05
    fr = nt.nodes.new("ShaderNodeLayerWeight"); fr.inputs[0].default_value = 0.15
    nt.links.new(fr.outputs["Fresnel"], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
    LABEL = mat("Label", base=(0.05, 0.35, 0.85), rough=0.35)
    WATER = mat("Water", base=(0.55, 0.8, 1.0), rough=0.0, transmission=1.0, ior=1.33)


def room(sc, table=True, table_loc=(0.1, -0.85, 0)):
    floor = bpy.data.objects.new("Floor", bpy.data.meshes.new("Floor"))
    sc.collection.objects.link(floor)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6); bm.to_mesh(floor.data); bm.free()
    floor.data.uv_layers.new()
    for i, l in enumerate(floor.data.uv_layers[0].data):
        v = floor.data.vertices[floor.data.loops[i].vertex_index].co
        l.uv = (v.x / 2.0, v.y / 2.0)
    assign(floor, pbr_tex("Laminate", os.path.join(PH, "laminate_floor_02"), 1.0))

    wallm = pbr_tex("Plaster", os.path.join(PH, "painted_plaster_wall"), 1.0)
    p = wallm.node_tree.nodes["Principled BSDF"]
    tint = wallm.node_tree.nodes.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs[7].default_value = (0.93, 0.86, 0.76, 1)
    lk = p.inputs["Base Color"].links[0]
    wallm.node_tree.links.new(lk.from_socket, tint.inputs[6])
    wallm.node_tree.links.new(tint.outputs[2], p.inputs["Base Color"])

    def wall(name, loc, rot, w=12, h=3.2, hole=None):
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
        o = bpy.context.object; o.name = name; o.scale = (w, h, 1)
        bpy.ops.object.transform_apply(scale=True)
        o.data.uv_layers.active.data.foreach_set("uv", [c for l in o.data.loops for c in (
            o.data.vertices[l.vertex_index].co.x / 2.0, o.data.vertices[l.vertex_index].co.y / 2.0)])
        assign(o, wallm)
        return o
    wall("WallBack", (0, 2.6, 1.6), (math.radians(90), 0, 0))
    wall("WallLeft", (-3.0, 0, 1.6), (math.radians(90), 0, math.radians(90)))
    wall("WallRight", (3.4, 0, 1.6), (math.radians(90), 0, math.radians(-90)))
    wall("WallFront", (0, -4.0, 1.6), (math.radians(90), 0, math.radians(180)))
    ceil = wall("Ceiling", (0, 0, 3.0), (math.radians(180), 0, 0), w=12, h=12)
    assign(ceil, mat("Ceil", (0.9, 0.88, 0.85), 0.8))
    # baseboard
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.58, 0.05)); bb = bpy.context.object
    bb.scale = (12, 0.03, 0.1); assign(bb, mat("Base", (0.9, 0.9, 0.88), 0.4))

    sofa, _ = import_gltf(os.path.join(PH, "Sofa_01", "Sofa_01_1k.gltf"), "Sofa")
    sofa.location = (0.2, 1.75, 0); sofa.rotation_euler = (0, 0, math.radians(0))
    plant, _ = import_gltf(os.path.join(PH, "potted_plant_01", "potted_plant_01_1k.gltf"), "Plant")
    plant.location = (-1.7, 2.1, 0); plant.scale = (1.3,) * 3
    frame, _ = import_gltf(os.path.join(PH, "fancy_picture_frame_01", "fancy_picture_frame_01_1k.gltf"), "Frame")
    frame.location = (0.3, 2.57, 1.75); frame.rotation_euler = (0, 0, 0); frame.scale = (1.6,) * 3
    tbl = None
    if table:
        tbl, _ = import_gltf(os.path.join(PH, "modern_coffee_table_01", "modern_coffee_table_01_1k.gltf"), "Table")
        tbl.location = table_loc
    # light: big soft window light from the left + warm fill + HDRI ambience
    world_hdri(sc, os.path.join(PH, "kloofendal_48d_partly_cloudy_puresky", "kloofendal_48d_partly_cloudy_puresky_1k.hdr"), 0.35)
    area(sc, (-2.6, -1.2, 2.2), (0, 0, 1.2), energy=900, size=2.2, color=(1.0, 0.96, 0.9))
    area(sc, (2.4, -2.4, 2.6), (0, 0, 1.2), energy=250, size=3.0, color=(1.0, 0.82, 0.62))
    area(sc, (0.5, 2.3, 2.9), (0, 0, 1.5), energy=180, size=1.2, color=(0.8, 0.88, 1.0))   # rim
    return tbl


def snap_to_grip(sc, arm, b, ref_frame):
    """Move the hand bottle so its middle sits in the curled fingers at ref_frame."""
    sc.frame_set(ref_frame); bpy.context.view_layer.update()
    pb = arm.pose.bones
    grip = sum((arm.matrix_world @ pb[f"mixamorig:LeftHand{n}"].head for n in ("Middle1", "Middle2", "Thumb2")), Vector()) / 3
    shell = next(o for o in b.children_recursive if o.type == "MESH" and o.material_slots
                 and o.material_slots[0].material and o.material_slots[0].material.name == "Plastic")
    # aim the bottle's long axis (cap end) at the mouth, pivoting about the grip
    hb = pb["mixamorig:Head"]; hm = arm.matrix_world @ hb.matrix
    mouth = hm.translation + (hm.col[1].xyz.normalized() * 0.02) + (hm.col[2].xyz.normalized() * 0.13)
    axis = (shell.matrix_world.col[2].xyz).normalized()
    q = axis.rotation_difference((mouth - grip).normalized())
    b.matrix_world = Matrix.Translation(grip) @ q.to_matrix().to_4x4() @ Matrix.Translation(-grip) @ b.matrix_world
    bpy.context.view_layer.update()
    mid = sum((shell.matrix_world @ Vector(c) for c in shell.bound_box), Vector()) / 8
    b.matrix_world = Matrix.Translation(grip - mid) @ b.matrix_world
    bpy.context.view_layer.update()


def brian(sc, acts, loc=(0, 0, 0), rotz=0.0, bottle_in_hand=True, grip_frame=None):
    arm, meshes = load_character("Brian")
    fix_char_materials(meshes)
    arm.location = loc; arm.rotation_euler.z = rotz   # keep the FBX +90deg X rotation
    for (anim, start, speed) in acts:
        apply_action(arm, load_action(anim), start, speed)
    b = None
    if bottle_in_hand:
        b = bottle("HandBottle", water=0.6, scale=2.0)
        b.parent = arm; b.parent_type = "BONE"; b.parent_bone = "mixamorig:LeftHand"
        # bone-space offset (bones are in cm because the armature is scaled 0.01)
        b.location = (2.5, 9.0, 4.5)
        b.rotation_euler = (math.radians(-10), math.radians(0), math.radians(-90))
        b.scale = (200,) * 3
        if grip_frame is not None:
            snap_to_grip(sc, arm, b, grip_frame)
    return arm, meshes, b


# ====================================================================== shots
def shot1(sc):
    """Wide low angle: Brian drinks in the living room. Slow push in."""
    make_materials()
    room(sc, table_loc=(0.85, -0.55, 0))
    arm, meshes, b = brian(sc, [("Drinking", -55, 1.25)])
    for i in range(3):
        bt = bottle(f"T{i}", water=0.0)
        bt.location = (0.65 + i * 0.16, -0.5 + (i % 2) * 0.08, 0.40)
        bt.rotation_euler = (0, 0, i * 0.7)
    cam = camera(sc, (0.6, -2.6, 0.35), (0, 0, 1.3), lens=18)
    cam_move(cam, [(1, (0.65, -1.95, 0.32), (0.05, 0, 1.15), 18), (53, (0.40, -1.45, 0.40), (0.0, 0, 1.30), 19)])
    ease_all(cam); shake(cam, 0.006, 20)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 2.3; cam.data.dof.aperture_fstop = 4


def shot2(sc):
    """Coffee table: empty bottles drop one after another (5-6 litres)."""
    make_materials()
    tbl = room(sc)
    top = 0.40
    land = [7, 16, 24, 31, 38, 44]
    spots = [(-0.30, -0.80), (-0.12, -0.70), (0.06, -0.86), (0.24, -0.74), (0.40, -0.88), (-0.02, -1.00)]
    for i, (fr, (x, y)) in enumerate(zip(land, spots)):
        bt = bottle(f"Drop{i}", water=0.0)
        rz = random.Random(i).uniform(0, 6.28)
        tip = (i % 3 == 2)
        key(bt, fr - 8, loc=(x, y, top + 1.3), rot=(0.3, 0.2, rz))
        key(bt, fr, loc=(x, y, top), rot=(0, 0, rz))
        key(bt, fr + 3, loc=(x, y, top + 0.05), rot=(0.08, 0, rz))
        key(bt, fr + 6, loc=(x, y, top), rot=(0, 0, rz))
        if tip:  # falls on its side and rolls a bit
            key(bt, fr + 12, loc=(x + 0.05, y, top + 0.045), rot=(math.radians(90), 0, rz))
            key(bt, fr + 30, loc=(x + 0.15, y - 0.03, top + 0.045), rot=(math.radians(90), math.radians(140), rz))
        ease_all(bt)
        for fc in fcurves(bt):  # hard landing: linear fall, ease after
            for k in fc.keyframe_points:
                if abs(k.co.x - (fr - 8)) < 0.1:
                    k.interpolation = "QUAD"; k.easing = "EASE_IN"
    # Brian behind, out of focus, still drinking
    brian(sc, [("Drinking", -95, 1.25)])
    cam = camera(sc, (-0.9, -1.75, 0.62), (0.05, -0.85, 0.48), lens=40)
    cam_move(cam, [(1, (-0.85, -1.85, 0.6), (-0.15, -0.85, 0.5), 40), (58, (0.75, -1.85, 0.66), (0.2, -0.85, 0.5), 40)])
    ease_all(cam); shake(cam, 0.004, 15)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.0
    foc = empty("Focus", (0.05, -0.84, 0.55)); cam.data.dof.focus_object = foc


def shot3(sc):
    """Close up of the face while gulping, background blurred."""
    make_materials()
    room(sc, table=False)
    arm, meshes, b = brian(sc, [("Drinking", -100, 1.0)], grip_frame=30)
    head = empty("HeadFocus", (0, 8, 0), arm, "mixamorig:Head")
    cam = camera(sc, (-0.5, -0.9, 1.6), (0, 0, 1.62), lens=70)
    cam_move(cam, [(1, (-0.62, -1.05, 1.55), (-0.02, 0.0, 1.62), 65), (74, (-0.45, -0.85, 1.58), (-0.02, 0.02, 1.64), 80)])
    ease_all(cam); shake(cam, 0.006, 12)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 1.8; cam.data.dof.focus_object = head


# ---------------------------------------------------------------- inner body
def blob(name, loc, radius, seg=48, mat_=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=radius, location=loc)
    o = bpy.context.object; o.name = name; smooth(o)
    if mat_: assign(o, mat_)
    return o


def kidney(name, loc, side=1, m=None):
    o = blob(name, (0, 0, 0), 1.0, 64)
    for v in o.data.vertices:
        x, y, z = v.co
        x *= 0.62; y *= 0.42; z *= 1.05
        # hilum notch on the medial side
        if x * side < 0:
            d = math.exp(-(z * z) / 0.18)
            x += side * 0.35 * d * (abs(x) / 0.62)
        z += 0.12 * x * x * side * 0
        v.co = (x, y, z)
    o.scale = (0.11,) * 3; o.location = loc
    bpy.ops.object.transform_apply(scale=True)
    o.modifiers.new("Sub", "SUBSURF").levels = 1
    if m: assign(o, m)
    return o


def tube_along(name, pts, radius, m, res=12):
    cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "3D"
    sp = cd.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
    cd.bevel_depth = radius; cd.bevel_resolution = 6; cd.resolution_u = res
    cd.use_fill_caps = True
    o = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(o)
    cd.materials.append(m)
    return o


def droplet_mat():
    """Cheap 'water drop': fresnel glossy rim + tinted see-through core + faint glow (no refraction)."""
    m = bpy.data.materials.new("WaterDrop"); nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs[0].default_value = (0.45, 0.75, 1.0, 1)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.25, 0.6, 1.0, 1); em.inputs[1].default_value = 1.2
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
    a = nt.nodes.new("ShaderNodeMixShader"); b = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], a.inputs[0]); nt.links.new(tr.outputs[0], a.inputs[1]); nt.links.new(em.outputs[0], a.inputs[2])
    nt.links.new(lw.outputs["Fresnel"], b.inputs[0]); nt.links.new(a.outputs[0], b.inputs[1]); nt.links.new(gl.outputs[0], b.inputs[2])
    nt.links.new(b.outputs[0], o.inputs[0])
    return m


def flesh_mat(name="Flesh", base=(0.55, 0.06, 0.07), bump=40):
    m = mat(name, base=base, rough=0.28, sss=0.6, sss_radius=(1.0, 0.25, 0.15), coat=0.4)
    m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.05
    add_bump(m, bump, 0.25)
    return m


def path_point(pts, t):
    """Catmull-Rom through pts, t in [0,1]."""
    n = len(pts) - 1; t = min(max(t, 0), 0.9999) * n; i = int(t); u = t - i
    p0 = Vector(pts[max(i - 1, 0)]); p1 = Vector(pts[i]); p2 = Vector(pts[i + 1]); p3 = Vector(pts[min(i + 2, n)])
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def shot4(sc):
    """X-ray dive to the kidneys: blue water drops trickle in, slowly filtered."""
    world_color(sc, (0.004, 0.006, 0.012), 1.0)
    km = flesh_mat("Kidney", (0.45, 0.06, 0.06), 60)
    L = kidney("KidL", (-0.17, 0, 0), side=1, m=km)
    R = kidney("KidR", (0.17, 0, 0), side=-1, m=km)
    # translucent torso silhouette (x-ray) around them
    xr = bpy.data.materials.new("Xray"); nt = xr.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (0.25, 0.6, 1.0, 1); em.inputs[1].default_value = 2.0
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.25
    nt.links.new(lw.outputs["Facing"], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])
    torso = blob("Torso", (0, 0.05, 0.1), 1.0, 64); torso.scale = (0.42, 0.26, 0.75); assign(torso, xr)
    spine = tube_along("Spine", [(0, 0.16, -0.7), (0, 0.17, 0), (0, 0.15, 0.8)], 0.035, mat("Bone", (0.85, 0.8, 0.7), 0.5, sss=0.2))
    # blood vessels: aorta + renal arteries, ureters
    red = flesh_mat("Vessel", (0.6, 0.03, 0.04), 20)
    tube_along("Aorta", [(0.0, 0.06, 0.8), (0.01, 0.06, 0.0), (0.0, 0.06, -0.7)], 0.025, red)
    tube_along("RenalL", [(0.0, 0.06, 0.02), (-0.07, 0.03, 0.02), (-0.12, 0.0, 0.0)], 0.012, red)
    tube_along("RenalR", [(0.0, 0.06, 0.02), (0.07, 0.03, 0.02), (0.12, 0.0, 0.0)], 0.012, red)
    ure = mat("Ureter", (0.85, 0.75, 0.55), 0.3, sss=0.3)
    tube_along("UretL", [(-0.11, 0.0, -0.05), (-0.09, 0.02, -0.35), (-0.05, 0.02, -0.65)], 0.007, ure)
    tube_along("UretR", [(0.11, 0.0, -0.05), (0.09, 0.02, -0.35), (0.05, 0.02, -0.65)], 0.007, ure)
    # water drops: lots arrive down the aorta, only a slow trickle leaves through the ureters
    dm = droplet_mat(); rnd = random.Random(4)
    for i in range(70):
        d = blob(f"D{i}", (0, 0, 0), 0.011 * rnd.uniform(0.7, 1.2), 16, dm)
        side = -1 if i % 2 else 1
        pts = [(0.0, 0.06, 0.85), (0.0, 0.06, 0.05), (side * 0.07, 0.03, 0.02), (side * 0.13, 0.0, 0.0),
               (side * 0.15, -0.02, 0.05 * rnd.uniform(-1, 1))]
        t0 = rnd.uniform(-60, 90)
        jitter = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * 0.012
        for f in range(1, 99, 3):
            t = (f - t0) / 45.0
            if t < 0: p = Vector(pts[0]) + Vector((0, 0, 0.3))
            elif t >= 1:  # queue up around the kidney
                p = Vector(pts[-1]) + Vector((side * 0.04 * math.sin(i + f * 0.05), -0.06, 0.12 * math.cos(i * 1.7)))
            else: p = path_point(pts, t) + jitter
            key(d, f, loc=p)
    for i in range(6):
        d = blob(f"U{i}", (0, 0, 0), 0.008, 12, dm); side = -1 if i % 2 else 1
        for f in range(1, 99, 4):
            t = ((f + i * 16) % 96) / 96.0
            key(d, f, loc=path_point([(side * 0.11, 0.0, -0.05), (side * 0.09, 0.02, -0.35), (side * 0.05, 0.02, -0.65)], t))
    area(sc, (0.6, -1.0, 0.8), (0, 0, 0), 120, 1.0, (1.0, 0.85, 0.8))
    area(sc, (-0.6, 0.8, 0.6), (0, 0, 0), 80, 1.0, (0.4, 0.6, 1.0))
    cam = camera(sc, (0, -1.6, 0.35), (0, 0, 0.05), lens=30)
    cam_move(cam, [(1, (0.05, -1.9, 0.45), (0, 0, 0.1), 28), (60, (0.18, -0.65, 0.12), (0.0, 0, 0.02), 32),
                   (98, (0.24, -0.45, 0.05), (-0.1, 0, 0.0), 35)])
    ease_all(cam); shake(cam, 0.004, 14)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.2
    cam.data.dof.focus_object = empty("F", (-0.1, 0, 0.02))


def rbc_mesh():
    """Biconcave red blood cell disc."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co; r2 = x * x + y * y
        th = 0.18 + 0.32 * r2 - 0.28 * math.exp(-r2 / 0.15) * 0
        z = math.copysign(max(0.08, 0.36 * (r2 ** 0.5) * (1 - r2) ** 0.5 + 0.1), z) if r2 < 1 else 0
        v.co = (x, y, z)
    me = bpy.data.meshes.new("RBC"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me


def vessel(sc, length=12.0, radius=0.6):
    """Wavy blood vessel tunnel along +Y, camera inside."""
    vm = flesh_mat("VesselWall", (0.42, 0.03, 0.035), 6)
    p = vm.node_tree.nodes["Principled BSDF"]
    p.inputs["Emission Color"].default_value = (0.5, 0.02, 0.02, 1); p.inputs["Emission Strength"].default_value = 0.15
    pts = [(0.25 * math.sin(i * 0.9), i * length / 8 - 1.0, 0.2 * math.cos(i * 0.7)) for i in range(9)]
    t = tube_along("Vessel", pts, radius, vm, res=24)
    t.data.use_fill_caps = False
    m = t.modifiers.new("Solid", "SOLIDIFY"); m.thickness = 0.05
    # (curves take no Displace modifier - the wall relief comes from the bump map)
    return pts


def scatter_cells(sc, pts, n, me_or_fn, m, rmin, rmax, t_speed, seed, nframes, size=0.11, radial=0.45):
    rnd = random.Random(seed); objs = []
    for i in range(n):
        if callable(me_or_fn):
            o = me_or_fn(i)
        else:
            o = bpy.data.objects.new(f"C{seed}_{i}", me_or_fn); sc.collection.objects.link(o)
        o.data.materials.clear() if o.data.materials and m else None
        if m: o.data.materials.append(m)
        s = size * rnd.uniform(0.85, 1.15); o.scale = (s, s, s)
        t0 = rnd.uniform(0, 1); ang = rnd.uniform(0, 6.28); rr = radial * math.sqrt(rnd.uniform(0.02, 1))
        rot0 = Euler((rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6)))
        for f in (1, nframes):
            t = t0 + t_speed * (f - 1) / 24.0
            c = path_point(pts, (t % 1.0) * 0.85 + 0.05)
            key(o, f, loc=c + Vector((math.cos(ang) * rr, 0, math.sin(ang) * rr)),
                rot=(rot0.x + f * 0.03, rot0.y + f * 0.02, rot0.z))
        for fc in fcurves(o):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"
        objs.append(o)
    return objs


def blood_scene(sc, flood):
    world_color(sc, (0.02, 0.0, 0.0), 1.0)
    pts = vessel(sc)
    rbcm = mat("RBC", (0.75, 0.04, 0.05), 0.35, sss=0.5, sss_radius=(1, 0.2, 0.1), coat=0.3)
    me = rbc_mesh()
    n = SHOTS[6 if flood else 5]
    rbcs = scatter_cells(sc, pts, 140, me, rbcm, 0, 0, 0.06, 1, n, size=0.09)
    salt_m = mat("Salt", (0.95, 0.95, 0.98), 0.15, transmission=0.5, ior=1.54, sss=0.2, sss_radius=(1, 1, 1))
    def cube(i):
        bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object; o.name = f"Salt{i}"
        bv = o.modifiers.new("B", "BEVEL"); bv.width = 0.06; bv.segments = 2
        return o
    salts = scatter_cells(sc, pts, 90 if not flood else 70, cube, salt_m, 0, 0, 0.06, 2, n, size=0.05)
    # lights travel with the camera
    cam = camera(sc, path_point(pts, 0.05), path_point(pts, 0.1), lens=20)
    head = point(sc, (0, 0, 0), 60, (1.0, 0.85, 0.75), 0.2); head.parent = cam; head.location = (0.15, 0.1, 0.2)
    fill = point(sc, (0, 0, 0), 25, (1.0, 0.4, 0.3), 0.3); fill.parent = cam; fill.location = (0, 0, -2.5)
    if not flood:
        keys = []
        for j, f in enumerate(range(1, n + 1, 10)):
            t = 0.08 + 0.32 * (f / n)
            keys.append((f, path_point(pts, t) + Vector((0.1 * math.sin(f * 0.05), 0, 0.05)), path_point(pts, t + 0.07)))
        cam_move(cam, keys)
        shake(cam, 0.01, 18)
    else:
        # water flood: blue droplets rush past from behind, salts get pushed apart
        dm = droplet_mat(); rnd = random.Random(9)
        centre = path_point(pts, 0.35)
        for i in range(160):
            d = blob(f"W{i}", (0, 0, 0), rnd.uniform(0.03, 0.07), 16, dm)
            t_arr = rnd.uniform(0, n * 0.7); ang = rnd.uniform(0, 6.28); rr = 0.5 * math.sqrt(rnd.random())
            off = Vector((math.cos(ang) * rr, 0, math.sin(ang) * rr))
            for f in (1, n):
                tt = 0.18 + (f - t_arr) / n * 0.4
                key(d, f, loc=path_point(pts, max(tt, 0.02)) + off)
            for fc in fcurves(d):
                for k in fc.keyframe_points: k.interpolation = "LINEAR"
        for s in salts:  # spread outward
            for fc in fcurves(s):
                if fc.data_path == "location" and fc.array_index in (0, 2):
                    last = fc.keyframe_points[-1]; last.co.y += (last.co.y - centre[fc.array_index]) * 0.9
        # orbit around the flood
        keys = []
        for f in range(1, n + 1, 8):
            a = -0.6 + 1.2 * f / n
            c = centre + Vector((0.32 * math.sin(a), -0.55 * math.cos(a) + 0.2, 0.06))
            keys.append((f, c, centre + Vector((0, 0.5, 0))))
        cam_move(cam, keys); cam.data.lens = 22
        shake(cam, 0.008, 18)
    ease_all(cam) if False else None
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8; cam.data.dof.focus_distance = 0.6


def shot5(sc): blood_scene(sc, flood=False)
def shot6(sc): blood_scene(sc, flood=True)


def cell_mats():
    m = mat("Cell", (1.0, 0.62, 0.66), 0.15, transmission=0.82, ior=1.2, coat=0.3, sss=0.15, sss_radius=(1, 0.5, 0.5))
    add_bump(m, 6, 0.08)
    nm = mat("Nucleus", (0.62, 0.22, 0.48), 0.4, sss=0.5, sss_radius=(1, 0.4, 0.8))
    return m, nm


def cell(name, loc, r, m, nm):
    c = blob(name, loc, r, 48, m)
    d = c.modifiers.new("Wob", "DISPLACE"); tx = bpy.data.textures.new(name + "T", "CLOUDS")
    tx.noise_scale = 0.6; d.texture = tx; d.strength = 0.05 * r / 0.3
    n = blob(name + "N", loc, r * 0.38, 24, nm); n.parent = c; n.matrix_parent_inverse = c.matrix_world.inverted()
    return c


def shot7(sc):
    """Tissue: water rushes in from the blood into the cells."""
    world_color(sc, (0.35, 0.08, 0.1), 1.0)
    m, nm = cell_mats(); dm = droplet_mat(); rnd = random.Random(3)
    cells = []
    for i in range(26):
        p = Vector((rnd.uniform(-1.6, 1.6), rnd.uniform(0, 3.5), rnd.uniform(-0.6, 0.9)))
        r = rnd.uniform(0.25, 0.38)
        if any((p - c.location).length < (r + c["r"]) * 0.95 for c in cells): continue
        c = cell(f"Cell{i}", p, r, m, nm); c["r"] = r; cells.append(c)
        g = 1.0 + 0.18 * rnd.random()
        key(c, 1, scale=1.0); key(c, 118, scale=g)
    for i in range(170):  # droplets from the camera side rushing into random cells
        c = cells[i % len(cells)]
        d = blob(f"W{i}", (0, 0, 0), rnd.uniform(0.015, 0.035), 12, dm)
        st = Vector((rnd.uniform(-2, 2), -1.2 + rnd.uniform(-0.4, 0.4), rnd.uniform(-1.0, 1.2)))
        t0 = rnd.uniform(-20, 90); t1 = t0 + rnd.uniform(25, 40)
        key(d, 1, loc=st if t0 > 1 else st.lerp(c.location, min(1, (1 - t0) / (t1 - t0))))
        if t0 > 1: key(d, int(t0), loc=st)
        key(d, max(int(t1), 2), loc=c.location + Vector((0, 0, 0)), scale=0.2)
        ease_all(d)
    area(sc, (-2, -2, 3), (0, 1.5, 0), 500, 3, (1.0, 0.9, 0.85))
    area(sc, (2, 4, 1), (0, 1.5, 0), 300, 3, (0.5, 0.6, 1.0))
    cam = camera(sc, (0, -1.6, 0.0), (0, 1.5, 0.1), lens=18)
    cam_move(cam, [(1, (-0.7, -1.9, -0.45), (0.0, 1.5, 0.15), 18), (118, (0.5, -0.6, 0.0), (0.0, 2.0, 0.3), 22)])
    ease_all(cam); shake(cam, 0.008, 18)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.4
    cam.data.dof.focus_object = cells[len(cells) // 2] if cells else None


def shot8(sc):
    """One cell swells like a water balloon and wobbles."""
    world_color(sc, (0.35, 0.08, 0.1), 1.0)
    m, nm = cell_mats(); dm = droplet_mat(); rnd = random.Random(8)
    c = cell("Hero", (0, 0, 0), 0.3, m, nm)
    n = SHOTS[8]
    for f, s in [(1, 1.0), (20, 1.15), (40, 1.35), (60, 1.55), (75, 1.68), (89, 1.75)]:
        key(c, f, scale=(s * (1 + 0.04 * math.sin(f)), s * (1 - 0.03 * math.sin(f * 1.3)), s))
    for i in range(6):  # neighbours, blurred
        a = i / 6 * 6.28
        cell(f"Nb{i}", (math.cos(a) * 1.3, 1.0 + math.sin(a) * 0.6, rnd.uniform(-0.5, 0.5)), 0.3, m, nm)
    for i in range(90):
        d = blob(f"W{i}", (0, 0, 0), rnd.uniform(0.025, 0.045), 12, dm)
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        t0 = rnd.uniform(-10, 70)
        key(d, 1, loc=v * (1.4 if t0 > 1 else 1.4 - 0.9 * (1 - t0) / 25))
        if t0 > 1: key(d, int(t0), loc=v * 1.4)
        key(d, int(t0) + 25, loc=v * 0.25, scale=0.1)
        ease_all(d)
    area(sc, (-1.5, -2, 2), (0, 0, 0), 600, 2, (1.0, 0.9, 0.85))
    area(sc, (1.5, 1.5, -0.5), (0, 0, 0), 500, 2, (0.5, 0.6, 1.0))
    area(sc, (0, 2.5, 0.5), (0, 0, 0), 400, 3, (1.0, 0.5, 0.5))
    cam = camera(sc, (0, -1.6, 0.0), (0, 0, 0), lens=50)
    cam_move(cam, [(1, (-0.35, -1.5, 0.15), (0, 0, 0), 55), (89, (0.4, -1.75, -0.1), (0, 0, 0), 45)])
    ease_all(cam); shake(cam, 0.006, 14)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.0; cam.data.dof.focus_object = c


# ---------------------------------------------------------------- head x-ray
def xray_brian(sc, acts):
    arm, meshes = load_character("Brian")
    xr = bpy.data.materials.new("XraySkin"); nt = xr.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (0.3, 0.65, 1.0, 1); em.inputs[1].default_value = 1.6
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.3
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.5
    nt.links.new(lw.outputs["Facing"], pw.inputs[0]); nt.links.new(pw.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    for o in meshes:
        if any(k in o.name.lower() for k in ("eyelash", "shirt", "pants", "sneakers")):
            o.hide_render = True; continue   # fewer transparent layers = much faster x-ray
        for sl in o.material_slots: sl.material = xr
    for (anim, start, speed) in acts:
        apply_action(arm, load_action(anim), start, speed)
    # skull + brain parented to the head bone (bone space is cm, y along the bone)
    skroot, sk = import_gltf(os.path.join(BK, "skull_dec.glb"), "Skull")
    for o in sk:
        if o.type == "MESH" and o.name.startswith("Text"): o.hide_render = True
        elif o.type == "MESH":
            assign(o, mat("SkullBone", (0.95, 0.92, 0.85), 0.35, sss=0.2, sss_radius=(1, 0.8, 0.6), alpha=0.32,
                          emit=(0.6, 0.8, 1.0), emit_strength=0.08))
            smooth(o)
    brroot, br = import_gltf(os.path.join(BK, "brain_dec.glb"), "Brain")
    bm = mat("BrainM", (0.85, 0.48, 0.5), 0.35, sss=0.5, sss_radius=(1, 0.3, 0.25), coat=0.5)
    for o in br:
        if o.type == "MESH":
            assign(o, bm); smooth(o)
    for r, objs in ((skroot, sk), (brroot, br)):
        recentre(r, objs)
        r.parent = arm; r.parent_type = "BONE"; r.parent_bone = "mixamorig:Head"
    return arm, meshes, skroot, brroot, bm


def recentre(root, objs):
    """Move the children so the root sits at the centre of their bounding box; store width."""
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" and not o.hide_render for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    for o in objs:
        if o.parent == root:
            o.location -= c
    root["size"] = tuple(hi - lo)


def fit_head(skroot, brroot):
    # Bone-parented children sit at the bone TAIL (top of the head, 19.6 cm above its base);
    # bone space is in cm (armature scale 0.01), +Y up the bone, +Z toward the face.
    # glTF models are Z-up / -Y front -> rotate -90 deg about X.
    sw = skroot["size"][0]; bw = brroot["size"][0]
    skroot.location = (0.0, -10.5, 0.8); skroot.rotation_euler = (math.radians(-90), 0, 0)
    skroot.scale = (13.6 / (sw * 1.0),) * 3          # skull 13.6 cm wide
    brroot.location = (0.0, -8.0, -0.3); brroot.rotation_euler = (math.radians(-90), 0, 0)
    brroot.scale = (11.6 / (bw * 1.0),) * 3          # brain 11.6 cm wide


def head_world(sc):
    world_color(sc, (0.003, 0.008, 0.02), 1.0)
    area(sc, (0.8, -1.2, 2.2), (0, 0, 1.6), 150, 1.0, (1.0, 0.92, 0.85))
    area(sc, (-1.0, 0.8, 1.9), (0, 0, 1.6), 120, 1.0, (0.45, 0.65, 1.0))


def shot9(sc):
    head_world(sc)
    arm, meshes, sk, br, bm = xray_brian(sc, [("Dizzy_Idle", 1, 1.25)]); fit_head(sk, br)
    tgt = empty("HeadT", (0, -9, 4), arm, "mixamorig:Head")
    cam = camera(sc, (0.9, -0.9, 1.7), (0, 0, 1.62), lens=50)
    keys = []
    for f in range(1, SHOTS[9] + 1, 8):
        a = math.radians(-60 + 70 * f / SHOTS[9])
        keys.append((f, (0.75 * math.sin(a), -0.75 * math.cos(a), 1.72 - 0.08 * f / SHOTS[9]), (0, 0, 1.66), 50))
    cam_move(cam, keys); shake(cam, 0.004, 14)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8; cam.data.dof.focus_object = tgt


def shot10(sc):
    head_world(sc)
    arm, meshes, sk, br, bm = xray_brian(sc, [("Dizzy_Idle", -40, 1.0)]); fit_head(sk, br)
    tgt = empty("HeadT", (0, -9, 4), arm, "mixamorig:Head")
    cam = camera(sc, (0.0, -0.9, 1.66), (0, 0, 1.66), lens=40)
    cam_move(cam, [(1, (-0.15, -0.95, 1.62), (0, 0, 1.66), 40), (94, (-0.05, -0.36, 1.68), (0, 0, 1.68), 50)])
    ease_all(cam); shake(cam, 0.004, 14)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.2; cam.data.dof.focus_object = tgt


def shot11(sc):
    head_world(sc)
    arm, meshes, sk, br, bm = xray_brian(sc, [("Dizzy_Idle", -70, 1.0)]); fit_head(sk, br)
    s0 = br.scale[0]
    for f, k in [(1, 1.0), (25, 1.06), (45, 1.12), (65, 1.18), (91, 1.22)]:
        key(br, f, scale=s0 * k)
    # brain stem / breathing centre glow
    stem = empty("StemPos", (0, -12.5, -3.5), arm, "mixamorig:Head")
    g = blob("Stem", (0, 0, 0), 0.016, 24, None); g.scale = (100,) * 3   # parent space is cm
    gl = point(sc, (0, 0, 0), 0.0, (1.0, 0.1, 0.05), 0.02); gl.parent = stem; gl.scale = (100,) * 3
    for f, e in [(1, 0), (20, 0), (30, 3), (40, 0.5), (50, 4), (60, 0.8), (70, 5), (80, 0.3), (91, 0)]:
        gl.data.energy = e; gl.data.keyframe_insert("energy", frame=f)
    gm = mat("Glow", (1, 0.1, 0.05), 0.3, emit=(1.0, 0.08, 0.03), emit_strength=0.0)
    assign(g, gm); g.parent = stem
    p = gm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, e in [(1, 0), (20, 0), (30, 25), (40, 4), (50, 30), (60, 6), (70, 35), (80, 2), (91, 0)]:
        p.default_value = e; p.keyframe_insert("default_value", frame=f)
    # skull flashes red where the brain presses
    tgt = empty("HeadT", (0, -10, 2), arm, "mixamorig:Head")
    cam = camera(sc, (0.3, -0.45, 1.52), (0, 0, 1.64), lens=45)
    cam_move(cam, [(1, (0.32, -0.42, 1.48), (0, 0, 1.62), 45), (91, (0.22, -0.33, 1.52), (0, 0, 1.63), 50)])
    ease_all(cam); shake(cam, 0.010, 6)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.0; cam.data.dof.focus_object = tgt


def shot12(sc):
    """He collapses. Low wide angle from the floor, a bottle rolls."""
    make_materials()
    room(sc, table_loc=(1.15, -0.2, 0))
    arm, meshes, b = brian(sc, [("Dizzy_Idle", -20, 1.25), ("Falling_Forward_Death", 14, 1.25)], loc=(0, 0.4, 0), rotz=math.radians(-20))
    for o in [b] + list(b.children_recursive):   # hiding the empty alone does not hide its children
        o.hide_render = True
    rb = bottle("Roll", water=0.0)
    key(rb, 1, loc=(-0.35, -1.6, 0.045), rot=(math.radians(90), 0, math.radians(30)))
    key(rb, 72, loc=(-0.05, -2.05, 0.045), rot=(math.radians(90), math.radians(-260), math.radians(30)))
    for i in range(4):
        bt = bottle(f"T{i}", water=0.0); bt.location = (0.95 + i * 0.15, -0.15 + (i % 2) * 0.1, 0.40)
    cam = camera(sc, (0.4, -2.0, 0.1), (-0.3, -0.3, 0.6), lens=18)
    cam_move(cam, [(1, (0.35, -1.75, 0.12), (-0.05, 0.25, 0.95), 18), (34, (0.25, -1.65, 0.10), (-0.35, -0.3, 0.45), 20),
                   (72, (0.12, -1.55, 0.08), (-0.6, -0.5, 0.12), 24)])
    ease_all(cam); shake(cam, 0.008, 10)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4; cam.data.dof.focus_distance = 2.0


# ====================================================================== main
def build(n):
    random.seed(n)
    sc = reset()
    globals()[f"shot{n}"](sc)
    sc.frame_start, sc.frame_end = 1, SHOTS[n]
    return sc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", type=int, required=True)
    ap.add_argument("--frames", default=None)
    ap.add_argument("--test", type=int, default=None)
    ap.add_argument("--pct", type=int, default=50)
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--save", default=None)
    a = ap.parse_args()
    import time; T0 = time.time()
    sc = build(a.shot)
    print(f"[film] built shot {a.shot} in {time.time() - T0:.1f}s", flush=True)
    setup_render(sc, pct=a.pct, samples=a.samples or SAMPLES[a.shot])
    if a.shot in NO_PERSIST:   # persistent data + fast deforming fall rendered the body pitch black
        sc.render.use_persistent_data = False
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save)
    if a.test is not None:
        sc.frame_set(a.test); sc.render.filepath = a.out
        T1 = time.time(); bpy.ops.render.render(write_still=True)
        print(f"[film] rendered in {time.time() - T1:.1f}s", flush=True)
    else:
        f0, f1 = map(int, (a.frames or f"1-{SHOTS[a.shot]}").split("-"))
        sc.frame_start, sc.frame_end = f0, f1
        sc.render.filepath = os.path.join(a.out, "f_")
        sc.render.use_overwrite = False
        bpy.ops.render.render(animation=True)
