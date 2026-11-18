"""Shots s1b, s2, s3, s4, s5, s6 (registered into shots.BUILDERS)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
import common as C
import sets as S
import shots as SH
import mixchar as MC


# ------------------------------------------------------------------ rat
def make_rat(coll=None, length=0.36):
    """Poly Haven street_rat (static mesh) under a root empty. Root: +X = heading,
    z=0 = feet, origin at body centre."""
    meshes = C.polyhaven_model("street_rat")
    rat = meshes[0]
    bpy.context.view_layer.update()
    mw = rat.matrix_world
    vs = [mw @ v.co for v in rat.data.vertices]
    ys = [v.y for v in vs]
    y0, y1 = min(ys), max(ys)
    L = y1 - y0

    def girth(lo, hi):
        sel = [v for v in vs if lo <= v.y <= hi]
        return (max(v.z for v in sel) - min(v.z for v in sel)) if sel else 0
    # tail end is thin: compare girth of the outer 25% at each end
    head_is_plus = girth(y1 - 0.25 * L, y1) > girth(y0, y0 + 0.25 * L)
    zmin = min(v.z for v in vs)
    # body centre: middle of the thick part (exclude tail ~45% of length)
    body_c = (y1 - 0.28 * L) if head_is_plus else (y0 + 0.28 * L)
    s = length / L
    root = C.empty("RatRoot", (0, 0, 0), coll)
    rat.parent = root
    yaw = -math.pi / 2 if head_is_plus else math.pi / 2  # map head direction to +X
    rot = Matrix.Rotation(yaw, 4, "Z")
    rat.matrix_parent_inverse = Matrix.Identity(4)
    rat.matrix_basis = rot @ Matrix.Scale(s, 4) @ Matrix.Translation((0, -body_c, -zmin)) @ mw
    head_off = (abs((y1 if head_is_plus else y0) - body_c)) * s
    root["head_off"] = head_off
    print(f"[rat] len {L:.3f} -> {length}, head +Y: {head_is_plus}, head offset {head_off:.3f}")
    for m in rat.data.materials:
        if m and m.use_nodes:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b:
                b.inputs["Roughness"].default_value = 0.6
    return root


def rat_motion(root, keys, base_z, fps_stride=6.0):
    """keys: list of (frame, (x, y), mode) mode in {'run','stop','sniff'}.
    Writes per-frame keys: smooth path, heading from velocity, gallop bob/pitch."""
    frames = list(range(keys[0][0], keys[-1][0] + 1))
    def pos(f):
        for (fa, pa, ma), (fb, pb, mb) in zip(keys, keys[1:]):
            if fa <= f <= fb:
                t = (f - fa) / max(1, fb - fa)
                t = t * t * (3 - 2 * t) if ma != "run" else t
                return Vector(pa).lerp(Vector(pb), t), ma
        return Vector(keys[-1][1]), keys[-1][2]
    heading = None
    phase = 0.0
    for f in frames:
        p, mode = pos(f)
        p2, _ = pos(min(f + 2, frames[-1]))
        p0, _ = pos(max(f - 2, frames[0]))
        v = p2 - p0
        speed = v.length / 4
        if v.length > 1e-4:
            h = math.atan2(v.y, v.x)
            heading = h if heading is None else heading + math.atan2(math.sin(h - heading), math.cos(h - heading)) * 0.5
        heading = heading or 0.0
        z, pitch, yaw_w, roll = base_z, 0.0, 0.0, 0.0
        if speed > 0.0015:
            phase += 2 * math.pi / fps_stride
            z += 0.014 * abs(math.sin(phase))
            pitch = 0.10 * math.sin(phase + 0.6)
            yaw_w = 0.05 * math.sin(phase * 0.5)
        elif mode == "sniff":
            pitch = 0.12 + 0.05 * math.sin(f * 1.7)
            yaw_w = 0.18 * math.sin(f * 0.35)
            roll = 0.03 * math.sin(f * 0.9)
        root.location = (p.x, p.y, z)
        root.rotation_euler = (roll, pitch, heading + yaw_w)
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
    C.set_interp(root, "LINEAR")


# ------------------------------------------------------------------ bacteria
def lepto_mat():
    m = bpy.data.materials.get("Leptospira")
    if m:
        return m
    m = bpy.data.materials.new("Leptospira")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (0.55, 1.0, 0.25, 1)
    e.inputs["Strength"].default_value = 4.0
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.4, 0.9, 0.3, 1)
    b.inputs["Transmission Weight"].default_value = 0.6
    b.inputs["Roughness"].default_value = 0.2
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], mx.inputs[0])
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(e.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], o.inputs[0])
    return m


def bacterium(name, L=0.005, r=0.00028, turns=16, thick=0.00009, coll=None):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = thick
    cd.bevel_resolution = 2
    sp = cd.splines.new("POLY")
    n = turns * 10
    sp.points.add(n - 1)
    for i in range(n):
        t = i / (n - 1)
        x = L * (t - 0.5)
        y = r * math.cos(2 * math.pi * turns * t)
        z = r * math.sin(2 * math.pi * turns * t)
        # hooked ends (Leptospira)
        for e0, sgn in ((0.1, -1), (0.9, 1)):
            d = (e0 - t) if sgn < 0 else (t - e0)
            if d > 0:
                z += (d / 0.1) ** 2 * L * 0.08
        sp.points[i].co = (x, y, z, 1)
    o = C.link(bpy.data.objects.new(name, cd), coll)
    cd.materials.append(lepto_mat())
    return o


def bacteria_swarm(n, region_fn, f0, f1, parent=None, seed=1, size=1.0, coll=None, grow=None):
    rnd = random.Random(seed)
    out = []
    for k in range(n):
        o = bacterium(f"lepto{k}", L=0.005 * size * rnd.uniform(0.7, 1.2), r=0.00028 * size, thick=0.00009 * size, coll=coll)
        if parent:
            o.parent = parent
        o.location = region_fn(rnd)
        base = Euler((0, 0, rnd.uniform(0, 6.28)))
        spin = rnd.choice((-1, 1)) * rnd.uniform(10, 18)
        for f in (f0, f1):
            o.rotation_euler = (base.x + spin * (f - f0) / 24.0, 0, base.z + 0.3 * math.sin(f * 0.1 + k))
            o.keyframe_insert("rotation_euler", frame=f)
        if grow:
            o.scale = (0.001,) * 3
            o.keyframe_insert("scale", frame=grow[0] + rnd.randint(0, 8))
            o.scale = (1, 1, 1)
            o.keyframe_insert("scale", frame=grow[1] + rnd.randint(0, 8))
        C.set_interp(o, "LINEAR")
        out.append(o)
    return out


# ------------------------------------------------------------------ helpers
def hero_can_at(xy, base_z, stain=True, name="HeroCan"):
    can = C.make_can(name, "volt", stain=stain)
    can.location = (xy[0], xy[1], base_z)
    can.rotation_euler = (0, 0, math.radians(180))  # opening toward -Y (camera side)
    return can


def lid_uv_node(can):
    lid = bpy.data.objects[can["lid"]]
    return lid.data.materials[0].node_tree.nodes["UV"]


def key_value(node_socket_owner, value_node, pairs):
    for f, v in pairs:
        value_node.outputs[0].default_value = v
        value_node.outputs[0].keyframe_insert("default_value", frame=f)


def fog(sc, size=(20, 20, 9), center=(0, 0, 4.5), density=0.02, color=(0.7, 0.8, 1.0)):
    o = C.box("Fog", size, center)
    m = bpy.data.materials.new("Fog")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Color"].default_value = (*color, 1)
    v.inputs["Anisotropy"].default_value = 0.5
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    C.assign(o, m)
    sc.cycles.volume_bounces = 0
    sc.cycles.volume_step_rate = 4.0
    return o


# ================================================================== S1b sting
def shot_s1b(sc):
    f0, f1 = SH.SHOTS["s1b"]
    C.world_color(sc, (0.0, 0.0, 0.0))
    floor = C.plane("Floor", 4, 4, (0, 0, 0), mat=C.principled("BlackGloss", (0.01, 0.01, 0.012), 0.0, 0.18))
    can = C.make_can("StingCan", "volt")
    bpy.data.objects[can["tab"]].rotation_euler = (math.radians(-8), 0, 0)
    bpy.data.objects[can["flap"]].rotation_euler = (math.radians(-80), 0, 0)
    can.rotation_euler = (0, 0, math.radians(180))
    rat = make_rat(length=0.40)
    C.box("Riser", (0.3, 0.2, 0.1), (0, 0.34, 0.05), C.principled("RiserBlack", (0.005, 0.005, 0.005), 0, 0.6))
    C.plane("RedBackdrop", 2.0, 1.2, (0, 0.9, 0.4), rot=(math.radians(90), 0, 0), mat=C.emission("RedGlow", (1.0, 0.03, 0.015), 0.45))
    rat.location = (0.0, 0.32, 0)
    rat.rotation_euler = (0, 0, -math.pi / 2)  # facing camera (-Y)
    rat.keyframe_insert("location", frame=f0)
    for f, z, p in ((f0, 0.0, 0.0), (176, 0.0, 0.0), (190, 0.1, -0.3), (223, 0.1, -0.4)):
        rat.location = (0.0, 0.32, z)
        rat.rotation_euler = (0, p, -math.pi / 2)
        rat.keyframe_insert("location", frame=f)
        rat.keyframe_insert("rotation_euler", frame=f)
    # red back light (silhouette), rim lights on can
    red = C.area_light("RedBack", 0.6, 60, (0.0, 0.75, 0.35), rot=(math.radians(-80), 0, 0), color=(1.0, 0.05, 0.02))
    for f, e in ((f0, 0), (156, 90), (175, 40), (190, 140), (223, 110)):
        red.data.energy = e
        red.data.keyframe_insert("energy", frame=f)
    C.area_light("RimL", 0.2, 3, (-0.25, 0.1, 0.25), rot=(0, math.radians(-70), 0), color=(1.0, 0.2, 0.1))
    C.area_light("RimR", 0.2, 2, (0.25, 0.1, 0.25), rot=(0, math.radians(70), 0), color=(0.6, 0.8, 1.0))
    C.area_light("Top", 0.12, 0.6, (0, -0.12, 0.42), rot=C.look_at_rot((0, -0.12, 0.42), (0, 0, 0.17)), color=(1, 1, 1))
    tgt = C.empty("tgt", (0, 0, C.CAN_H))
    C.key_path(tgt, [(f0, (0, 0, C.CAN_H - 0.01)), (176, (0, 0.05, C.CAN_H + 0.01)), (f1, (0, 0.12, C.CAN_H + 0.06))])
    cam = C.camera("Cam1b_sting", 35, (0, -0.55, 0.26), tgt, fstop=2.0)
    cd = cam.data
    for f, l in ((f0, 28), (158, 75), (223, 85)):
        cd.lens = l
        cd.keyframe_insert("lens", frame=f)
    for f, d in ((f0, 0.55), (180, 0.55), (195, 0.85), (f1, 0.85)):
        cd.dof.focus_distance = d
        cd.dof.keyframe_insert("focus_distance", frame=f)
    C.set_interp(cd, "BEZIER")
    C.key_path(cam, [(f0, (0, -0.55, 0.26)), (f1, (0, -0.48, 0.24))])
    sc.camera = cam


# ================================================================== S2 wide warehouse
def shot_s2(sc):
    f0, f1 = SH.SHOTS["s2"]
    coll, top, info = S.build_warehouse(sc)
    hero = hero_can_at(info["hero"], top - C.CAN_H)
    fog(sc, density=0.012)
    rat = make_rat()
    rat_motion(rat, [(318, (-0.75, -0.05), "run"), (330, (-0.42, -0.02), "run"), (f1, (0.05, 0.03), "run")], top)
    rat.location.z = -5
    rat.keyframe_insert("location", frame=317)
    tgt = C.empty("tgt2", (0, 0, 0.5))
    C.key_path(tgt, [(f0, (-0.6, 0.0, 0.9)), (f1, (0.0, 0.0, 0.55))])
    cam = C.camera("Cam2_wide", 24, (3.0, 3.2, 1.8), tgt, fstop=4.0, focus=tgt)
    C.key_path(cam, [(f0, (3.4, 2.6, 2.1)), (f1, (1.25, 1.55, 1.05))])
    sc.camera = cam


# ================================================================== S3 rat run
def shot_s3(sc):
    f0, f1 = SH.SHOTS["s3"]
    coll, top, info = S.build_warehouse(sc)
    hx, hy = info["hero"]
    hero = hero_can_at((hx, hy), top - C.CAN_H)
    lid_z = top - C.CAN_H + C.LID_Z
    fog(sc, density=0.008)
    rat = make_rat()
    ho = rat["head_off"]
    stop = (hx - ho + 0.005, hy)
    rat_motion(rat, [(f0, (-0.55, hy - 0.06), "run"), (448, (stop[0] - 0.03, hy - 0.005), "run"),
                     (456, stop, "stop"), (f1, stop, "sniff")], top)
    # droplet (urine/saliva) from under the rat's head onto the lid
    drop = bpy.data.objects.new("Drop", bpy.data.meshes.new("Drop"))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.0032)
    bm.to_mesh(drop.data); bm.free(); C.link(drop); C.smooth(drop)
    dm = C.principled("Urine", (1.0, 0.85, 0.35), 0, 0.02, **{"Transmission Weight": 1.0, "IOR": 1.33})
    C.assign(drop, dm)
    lx, ly = hx, hy - 0.010
    for f, z, s in ((f0, lid_z + 0.03, (0.001,) * 3), (546, lid_z + 0.03, (0.001,) * 3), (548, lid_z + 0.028, (0.9, 0.9, 1.3)),
                    (556, lid_z + 0.003, (0.9, 0.9, 1.25)), (558, lid_z + 0.0006, (2.6, 2.6, 0.18)), (575, lid_z + 0.0004, (3.2, 3.0, 0.12))):
        drop.location = (lx, ly, z)
        drop.scale = s
        drop.keyframe_insert("location", frame=f)
        drop.keyframe_insert("scale", frame=f)
    C.set_interp(drop, "LINEAR")
    # moon key on the pallet top
    C.spot_light("RatKey", 60, (-1.4, -0.9, 2.2), C.look_at_rot((-1.4, -0.9, 2.2), (0, 0, top)), angle=30, color=(0.6, 0.72, 1.0), radius=0.1)
    # 3a: can-top level, rat runs at the lens (camera retreats)
    t_a = C.empty("t3a", (0, 0, 0)); t_a.parent = rat; t_a.location = (0.02, 0, 0.035)
    cam_a = C.camera("Cam3a_low", 20, (0.62, hy, top + 0.035), t_a, fstop=2.8, focus=t_a)
    C.key_path(cam_a, [(f0, (0.55, hy - 0.04, top + 0.03)), (456, (0.66, hy + 0.02, top + 0.05)), (470, (0.67, hy + 0.02, top + 0.055))])
    # 3b: side medium, rat sniffing the lid, slow orbit
    t_b = C.empty("t3b", (hx, hy, top + 0.03))
    cam_b = C.camera("Cam3b_side", 50, (hx + 0.05, hy - 0.42, top + 0.10), t_b, fstop=2.2, focus=t_b)
    C.key_path(cam_b, [(471, (hx - 0.12, hy - 0.42, top + 0.09)), (540, (hx + 0.10, hy - 0.36, top + 0.12))])
    # 3c: macro of the lid; droplet lands
    t_c = C.empty("t3c", (lx, ly, lid_z))
    cam_c = C.camera("Cam3c_drop", 85, (hx + 0.02, hy - 0.26, lid_z + 0.11), t_c, fstop=2.8, focus=t_c)
    C.key_path(cam_c, [(541, (hx + 0.03, hy - 0.27, lid_z + 0.11)), (f1, (hx + 0.015, hy - 0.21, lid_z + 0.085))])
    C.bind_cameras(sc, [(f0, cam_a), (471, cam_b), (541, cam_c)])


# ================================================================== S4 UV reveal
def shot_s4(sc):
    f0, f1 = SH.SHOTS["s4"]
    coll, top, info = S.build_warehouse(sc)
    hx, hy = info["hero"]
    hero = hero_can_at((hx, hy), top - C.CAN_H)
    lid_z = top - C.CAN_H + C.LID_Z
    uv = lid_uv_node(hero)
    key_value(None, uv, [(f0, 0.0), (612, 0.0), (632, 1.0), (f1, 1.0)])
    # UV torch: violet spot sweeping across the pallet top
    sp = C.spot_light("UVTorch", 0, (hx - 0.4, hy - 0.3, lid_z + 0.35), (0, 0, 0), angle=18, blend=0.6, color=(0.35, 0.1, 1.0), radius=0.01)
    tr = sp.constraints.new("TRACK_TO"); trg = C.empty("uvtgt", (hx - 0.25, hy, lid_z)); tr.target = trg
    tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    C.key_path(trg, [(f0, (hx - 0.25, hy + 0.05, lid_z)), (630, (hx, hy - 0.01, lid_z)), (f1, (hx + 0.03, hy - 0.01, lid_z))])
    for f, e in ((f0, 0), (606, 25), (f1, 25)):
        sp.data.energy = e
        sp.data.keyframe_insert("energy", frame=f)
    t = C.empty("t4", (hx, hy - 0.008, lid_z))
    cam = C.camera("Cam4_uv", 85, (hx + 0.06, hy - 0.22, lid_z + 0.16), t, fstop=2.0, focus=t)
    C.key_path(cam, [(f0, (hx + 0.07, hy - 0.24, lid_z + 0.17)), (f1, (hx + 0.02, hy - 0.15, lid_z + 0.10))])
    sc.camera = cam
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.008


# ================================================================== S5 tab pushes bacteria in
def _cut_can(name):
    can = C.make_can(name, "volt", stain=True)
    alu_in = C.alu_mat("InnerAlu", 0.35)
    can.data.materials.append(alu_in)
    so = can.modifiers.new("shell", "SOLIDIFY")
    so.thickness = 0.0006
    so.material_offset = 1
    so.material_offset_rim = 1
    cutter = C.box(name + "_halfcut", (0.2, 0.1, 0.4), (0, -0.05, 0.1))
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    for o in [can] + [bpy.data.objects[can["lid"]], bpy.data.objects[name + "_inner"]]:
        b = o.modifiers.new("cutaway", "BOOLEAN")
        b.operation = "DIFFERENCE"; b.object = cutter; b.solver = "EXACT"
    bpy.data.objects[name + "_inner"].hide_render = True
    return can, cutter


def shot_s5(sc):
    f0, f1 = SH.SHOTS["s5"]
    # ---------- 5a: macro of the stained lid, tab opens in slow motion (warehouse)
    coll, top, info = S.build_warehouse(sc)
    hx, hy = info["hero"]
    hero = hero_can_at((hx, hy), top - C.CAN_H)
    lid_z = top - C.CAN_H + C.LID_Z
    key_value(None, lid_uv_node(hero), [(f0, 0.5), (700, 0.12), (780, 0.12)])
    C.animate_can_open(hero, 705, 770, tab_angle=-70, flap_angle=-85)
    flap = bpy.data.objects[hero["flap"]]
    bact = bacteria_swarm(9, lambda r: (r.uniform(-0.006, 0.006), r.uniform(0.0, 0.014), 0.0004), f0, 780,
                          parent=flap, seed=4, size=1.1, grow=(672, 690))
    C.area_light("MacroKey", 0.25, 6, (hx - 0.2, hy - 0.25, lid_z + 0.3), rot=C.look_at_rot((hx - 0.2, hy - 0.25, lid_z + 0.3), (hx, hy, lid_z)), color=(0.75, 0.82, 1.0))
    sp = C.spot_light("UVTorch", 18, (hx - 0.3, hy - 0.25, lid_z + 0.3), C.look_at_rot((hx - 0.3, hy - 0.25, lid_z + 0.3), (hx, hy, lid_z)), angle=20, blend=0.6, color=(0.35, 0.1, 1.0), radius=0.01)
    t = C.empty("t5a", (hx, hy - 0.012, lid_z))
    cam_a = C.camera("Cam5a_tab", 100, (hx + 0.04, hy - 0.2, lid_z + 0.12), t, fstop=2.8, focus=t)
    C.key_path(cam_a, [(f0, (hx + 0.05, hy - 0.21, lid_z + 0.13)), (780, (hx + 0.01, hy - 0.13, lid_z + 0.075))])
    # ---------- 5b: cutaway can on a dark stage far away (x+30)
    X = 30.0
    stage = C.plane("Stage", 3, 3, (X, 0, 0), mat=C.principled("StageBlack", (0.008, 0.008, 0.01), 0, 0.3))
    can, cutter = _cut_can("CutCan")
    can.location = (X, 0, 0)
    cutter.location = (X, -0.05, 0.1)
    cutter.parent = None
    C.animate_can_open(can, 785, 815, tab_angle=-70, flap_angle=-85)
    # liquid (energy drink), cut in half too
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=C.CAN_R - 0.0008, radius2=C.CAN_R - 0.0008, depth=0.125)
    liq = C.mesh_obj("Liquid", bm)
    liq.location = (X, 0, 0.008 + 0.0625)
    lm = C.principled("Drink", (1.0, 0.82, 0.3), 0, 0.02, **{"Transmission Weight": 1.0, "IOR": 1.34})
    vol = lm.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = (1.0, 0.7, 0.15, 1); vol.inputs["Density"].default_value = 18
    lm.node_tree.links.new(vol.outputs[0], lm.node_tree.nodes["Material Output"].inputs["Volume"])
    C.assign(liq, lm)
    b = liq.modifiers.new("cutaway", "BOOLEAN"); b.operation = "DIFFERENCE"; b.object = cutter; b.solver = "EXACT"
    surf_z = 0.008 + 0.125
    # bubbles rising in the back half
    rnd = random.Random(9)
    bub_m = C.principled("Bubble", (1, 1, 1), 0, 0.0, **{"Transmission Weight": 1.0, "IOR": 1.0})
    for k in range(70):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=rnd.uniform(0.0004, 0.0012))
        o = C.mesh_obj(f"bub{k}", bm); C.smooth(o); C.assign(o, bub_m)
        a = rnd.uniform(0.1, math.pi - 0.1); rr = rnd.uniform(0.004, C.CAN_R - 0.004)
        x, y = X + rr * math.cos(a), rr * math.sin(a) + 0.002
        z0 = rnd.uniform(0.01, surf_z); sp_ = rnd.uniform(0.0015, 0.003)
        for f in (781, 905):
            z = z0 + sp_ * (f - 781)
            z = 0.01 + (z - 0.01) % (surf_z - 0.012)
            o.location = (x, y, z); o.keyframe_insert("location", frame=f)
        C.set_interp(o, "LINEAR")
    # bacteria raining from the flap into the drink
    def region(r):
        return (r.uniform(-0.007, 0.007), r.uniform(0.002, 0.016), 0.0004)
    cflap = bpy.data.objects[can["flap"]]
    fall = []
    for k in range(18):
        o = bacterium(f"fall{k}", L=0.0065, r=0.0006, thick=0.00012, turns=10)
        sx, sy = rnd.uniform(-0.006, 0.006), rnd.uniform(0.004, 0.016)
        t0 = 800 + rnd.randint(0, 25)
        start = Vector((X - sx, -sy, C.LID_Z - 0.002))  # can rotated 0 here: opening at +Y -> use world below flap
        start = Vector((X + sx, sy, C.LID_Z - 0.004))
        end = Vector((X + sx * 1.6 + rnd.uniform(-0.01, 0.01), sy * 0.6 + rnd.uniform(0, 0.012), surf_z - rnd.uniform(0.005, 0.07)))
        o.location = start; o.scale = (0.001,) * 3
        o.keyframe_insert("location", frame=781); o.keyframe_insert("scale", frame=t0 - 1)
        o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=t0)
        o.location = start; o.keyframe_insert("location", frame=t0)
        hit = t0 + 10 + rnd.randint(0, 6)
        o.location = (end.x, end.y, surf_z); o.keyframe_insert("location", frame=hit)
        o.location = end; o.keyframe_insert("location", frame=hit + 60)
        spin = rnd.uniform(14, 22)
        for f in (781, 905):
            o.rotation_euler = (spin * (f - 781) / 24, rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6.28))
            o.keyframe_insert("rotation_euler", frame=f)
        fall.append(o)
    C.area_light("StageKey", 0.3, 10, (X - 0.25, -0.3, 0.35), rot=C.look_at_rot((X - 0.25, -0.3, 0.35), (X, 0, 0.12)), color=(1, 0.95, 0.9))
    C.area_light("StageRim", 0.3, 14, (X + 0.25, 0.25, 0.3), rot=C.look_at_rot((X + 0.25, 0.25, 0.3), (X, 0, 0.12)), color=(0.4, 0.7, 1.0))
    C.area_light("StageBack", 0.3, 6, (X, 0.35, 0.1), rot=C.look_at_rot((X, 0.35, 0.1), (X, 0, 0.1)), color=(1.0, 0.6, 0.2))
    t_b = C.empty("t5b", (X, 0.01, C.LID_Z - 0.01))
    C.key_path(t_b, [(781, (X, 0.01, C.LID_Z - 0.008)), (840, (X, 0.012, surf_z - 0.005)), (905, (X, 0.012, surf_z - 0.04))])
    cam_b = C.camera("Cam5b_cutaway", 60, (X, -0.3, 0.2), t_b, fstop=4.0, focus=t_b)
    C.key_path(cam_b, [(781, (X + 0.04, -0.2, 0.2)), (840, (X - 0.02, -0.14, 0.15)), (905, (X - 0.005, -0.065, 0.11))])
    C.bind_cameras(sc, [(f0, cam_a), (781, cam_b)])


# ================================================================== S6 sick + x-ray
def xray_rig(meshes, f_on):
    """Insert a mix to an x-ray (fresnel emission + transparency) shader, keyed on at f_on."""
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes:
                continue
            nt = m.node_tree
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
            src = out.inputs["Surface"].links[0].from_socket
            lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
            em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.75, 1.0, 1)
            em.inputs["Strength"].default_value = 3.0
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(lw.outputs["Facing"], mx.inputs[0])
            nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
            sw = nt.nodes.new("ShaderNodeMixShader"); sw.name = "XRAY"
            nt.links.new(src, sw.inputs[1]); nt.links.new(mx.outputs[0], sw.inputs[2])
            nt.links.new(sw.outputs[0], out.inputs["Surface"])
            for f, v in ((f_on - 1, 0.0), (f_on, 1.0)):
                sw.inputs[0].default_value = v
                sw.inputs[0].keyframe_insert("default_value", frame=f)
            for fc in (nt.animation_data.action and C.fcurves_of(nt)) or []:
                for k in fc.keyframe_points:
                    k.interpolation = "CONSTANT"


def organ(name, size, loc_world, arm, bone, color, coll=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    o = C.mesh_obj(name, bm, coll); C.smooth(o)
    o.scale = size
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 1
    m = bpy.data.materials.new(name + "M"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Coat Weight"].default_value = 0.5
    C.assign(o, m)
    o.location = loc_world
    bpy.context.view_layer.update()
    MC.attach_to_bone(o, arm, bone, o.matrix_world.copy(), bpy.context.scene.frame_current)
    return o, b


def shot_s6(sc):
    f0, f1 = SH.SHOTS["s6"]
    XR = 991
    arm, meshes = SH._megan(sc)
    focus = MC.load_motion("Focus", arm)
    dizzy = MC.load_motion("Dizzy_Idle", arm)
    MC.sequence(arm, [dict(action=focus, start=f0, src=(1, 50), scale=1.7), dict(action=dizzy, start=XR, src=(20, 129))])
    arm.location = (0, 0.3, 0)
    arm.rotation_euler = (math.radians(90), 0, math.pi)
    S.build_store(sc)
    # dim the store, harsher key for the sick look
    for o in sc.objects:
        if o.type == "LIGHT" and o.name.startswith("PanelL"):
            o.data.energy = 45
    key = C.spot_light("SickKey", 120, (0.9, 1.4, 2.4), C.look_at_rot((0.9, 1.4, 2.4), (0, 0.3, 1.5)), angle=35, blend=0.5, color=(0.85, 0.95, 1.0), radius=0.08)
    # x-ray organs, keyed visible at XR
    sc.frame_set(XR)
    sp = MC.bone_head(arm, "Spine1"); hips = MC.bone_head(arm, "Hips")
    fwd = Vector((0, 1, 0))  # she faces +Y
    right = Vector((1, 0, 0))  # her right side is +X when facing +Y
    liver, lb = organ("Liver", (0.085, 0.06, 0.05), sp + right * 0.05 + fwd * 0.03 - Vector((0, 0, 0.03)), arm, "Spine1", (0.55, 0.08, 0.06))
    kidL, kb1 = organ("KidneyL", (0.026, 0.02, 0.05), hips.lerp(sp, 0.55) - right * 0.055 - fwd * 0.03, arm, "Spine", (0.6, 0.1, 0.08))
    kidR, kb2 = organ("KidneyR", (0.026, 0.02, 0.05), hips.lerp(sp, 0.55) + right * 0.055 - fwd * 0.03, arm, "Spine", (0.6, 0.1, 0.08))
    for o, b in ((liver, lb), (kidL, kb1), (kidR, kb2)):
        SH._hide_keys(o, [(XR, f1)], f0, f1)
        for f, e in ((XR, 2.0), (1005, 6.0), (1012, 2.5), (1020, 7.0), (1028, 1.5), (1036, 3.0), (1044, 0.2), (f1, 0.0)):
            b.inputs["Emission Strength"].default_value = e
            b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    xray_rig(meshes, XR)
    # 6a: emotional close-up 85mm
    head = C.empty("tHead", (0, 0, 0))
    head.parent = arm; head.parent_type = "BONE"; head.parent_bone = "mixamorig:Head"
    head.location = (0, 0, 0)
    cam_a = C.camera("Cam6a_face", 70, (-0.3, 1.1, 1.05), head, fstop=1.8, focus=head)
    C.key_path(cam_a, [(f0, (-0.36, 1.25, 1.0)), (990, (-0.2, 0.95, 1.08))])
    # 6b: x-ray orbit, torso framing
    t_b = C.empty("t6b", (0, 0.3, 1.15))
    cam_b = C.camera("Cam6b_xray", 35, (0.0, 1.6, 1.2), t_b, fstop=4.0, focus=t_b)
    pts = []
    for i, f in enumerate(range(XR, f1 + 1, 6)):
        a = math.radians(-35 + 70 * (f - XR) / (f1 - XR))
        r = 1.25 - 0.25 * (f - XR) / (f1 - XR)
        pts.append((f, (math.sin(a) * r, 0.3 + math.cos(a) * r, 1.2)))
    C.key_path(cam_b, pts)
    C.bind_cameras(sc, [(f0, cam_a), (XR, cam_b)])


SH.BUILDERS.update({"s1b": shot_s1b, "s2": shot_s2, "s3": shot_s3, "s4": shot_s4, "s5": shot_s5, "s6": shot_s6})
