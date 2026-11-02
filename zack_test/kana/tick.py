# Protsedural kana (Ixodes): tana, qalqon (scutum), boshcha (capitulum), palplar, tikanli xipostom,
# ikki xelitsera ("pichoqlar") va 8 ta bo'g'imli oyoq. Mahalliy o'qlar: +X oldinga, +Z tepaga.
import bpy, bmesh, math
from mathutils import Vector, Matrix
import common as C

R = math.radians

def _mats():
    M = {}
    m = C.mat("tick_body", (0.22, 0.045, 0.025), 0.32, coat=0.7, sss=0.15, sss_r=(1, 0.2, 0.1), sss_scale=0.05)
    mix = C.noise_color(m, (0.11, 0.02, 0.012), scale=5, detail=10, bump=0.12, kind="noise", distortion=1.5, bump_dist=0.01)
    C.add_bump(m, scale=120, strength=0.15, dist=0.004)
    # to'yganda: kulrang-ko'kimtir sharga aylanadi (Mix "engorge" omili bilan)
    N = m.node_tree.nodes; L = m.node_tree.links; b = C.principled(m)
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; mx2.name = "engorge"; mx2.inputs["Factor"].default_value = 0.0
    L.new(mix.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = (0.13, 0.115, 0.12, 1)
    L.new(mx2.outputs[2], b.inputs["Base Color"])
    M["body"] = m
    m = C.mat("tick_scutum", (0.035, 0.018, 0.01), 0.25, coat=1.0)
    C.add_bump(m, scale=90, strength=0.1, kind="voronoi", dist=0.003)
    M["scutum"] = m
    m = C.mat("tick_leg", (0.17, 0.06, 0.03), 0.35, coat=0.5, sss=0.3, sss_r=(1, 0.4, 0.2), sss_scale=0.03)
    C.noise_color(m, (0.08, 0.025, 0.012), scale=40, bump=0.2, bump_dist=0.003)
    M["leg"] = m
    m = C.mat("tick_mouth", (0.3, 0.12, 0.06), 0.3, coat=0.6, sss=0.2, sss_r=(1, 0.5, 0.3), sss_scale=0.02)
    M["mouth"] = m
    m = C.mat("tick_hypo", (0.55, 0.32, 0.16), 0.28, coat=0.8, sss=0.2, sss_r=(1, 0.6, 0.3), sss_scale=0.02)
    M["hypo"] = m
    m = C.mat("tick_cheli", (0.5, 0.24, 0.09), 0.2, coat=1.0, sss=0.2, sss_r=(1, 0.5, 0.2), sss_scale=0.01)
    M["cheli"] = m
    return M

def _body_mesh(name, m):
    """Tomchi shaklidagi yassi tana; markaz (0,0,0), uzunlik ~1.1 (X), eni ~0.85."""
    o = C.sphere(name, 1.0, (0, 0, 0), m, seg=64, ring=32)
    for v in o.data.vertices:
        x, y, z = v.co
        w = 0.42 * (1.0 - 0.32 * max(0.0, x))           # oldi tor
        v.co = Vector((x * 0.56, y * w, z * (0.17 if z > 0 else 0.12)))
        # yon cheti bo'ylab nozik egat (marginal groove)
        r = math.hypot(v.co.x / 0.56, v.co.y / max(w, 1e-3))
        if 0.8 < r < 0.9 and z > 0: v.co.z -= 0.012
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    return o

def _scutum(name, body, m):
    """Silliq chetli qalqon: konsentrik halqalardan disk, keyin tanaga yopishtiriladi."""
    cx, rx, ry, rings, segs = 0.24, 0.33, 0.27, 14, 72
    verts = [(cx, 0, 0.3)]; faces = []
    for i in range(1, rings + 1):
        r = i / rings
        for j in range(segs):
            a = 2 * math.pi * j / segs
            # orqa tomoni biroz o'tkir (qalqon shakli)
            k = 1.0 + 0.18 * max(0.0, -math.cos(a)) ** 2
            verts.append((cx + rx * r * math.cos(a) * k, ry * r * math.sin(a) * (1 - 0.25 * max(0.0, -math.cos(a))), 0.3))
    for j in range(segs):
        faces.append((0, 1 + j, 1 + (j + 1) % segs))
    for i in range(1, rings):
        a0 = 1 + (i - 1) * segs; a1 = 1 + i * segs
        for j in range(segs):
            jn = (j + 1) % segs
            faces.append((a0 + j, a1 + j, a1 + jn, a0 + jn))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); C.sc().collection.objects.link(o); me.materials.append(m); C.smooth(o)
    sw = o.modifiers.new("wrap", "SHRINKWRAP"); sw.target = body; sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.offset = 0.004
    so = o.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.01; so.offset = 1.0
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.004; bv.segments = 2
    return o

def _hypostome(name, m, length=0.32, r0=0.04):
    """Nayzasimon xipostom +X bo'ylab, ventral tomonida orqaga qaragan tikanchalar qatorlari."""
    parts = []
    shaft = C.cyl(name + "_shaft", r0, length, (length / 2, 0, 0), m, rot=(0, 90, 0), verts=24, r2=r0 * 0.25)
    shaft.scale = (1.0, 1.25, 0.7)
    tip = C.sphere(name + "_tip", r0 * 0.32, (length, 0, 0), m, seg=16, ring=8)
    parts += [shaft, tip]
    rows = 4; n = 9
    for side in (-1, 1):
        for rI in range(rows):
            ang = R(-15 - rI * 26)                    # ventral (pastki) yarim aylana bo'ylab
            for i in range(n):
                t = 0.12 + 0.8 * i / (n - 1)
                rr = r0 * (1 - 0.75 * t) * 1.0
                x = length * t
                y = side * rr * 1.25 * math.cos(ang) * 0.95
                z = rr * 0.7 * math.sin(ang)
                bl = 0.028 * (1 - 0.5 * t)
                bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.009 * (1 - 0.5 * t), radius2=0.0, depth=bl)
                c = bpy.context.object; c.name = name + "_barb"
                # tikan uchi orqaga (-X) va biroz tashqariga qaraydi
                d = Vector((-1.0, side * 0.55 * math.cos(ang), 0.55 * math.sin(ang))).normalized()
                c.rotation_mode = "QUATERNION"; c.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
                c.location = Vector((x, y, z)) + d * bl * 0.45
                c.data.materials.append(m); parts.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = shaft
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    return o

def _chelicera(name, m, length=0.3):
    """Xelitsera: ingichka sop + uchida yassi, tishli "pichoq"."""
    parts = [C.cyl(name + "_s", 0.018, length, (length / 2, 0, 0), m, rot=(0, 90, 0), verts=16, r2=0.013)]
    blade = C.cyl(name + "_b", 0.03, 0.12, (length + 0.05, 0, 0), m, rot=(0, 90, 0), verts=24, r2=0.002)
    blade.scale = (1, 0.32, 1.35); parts.append(blade)
    for i in range(4):
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.011, radius2=0, depth=0.035,
                                        location=(length + 0.0 + i * 0.025, 0, 0.03 - i * 0.004), rotation=(0, R(-40), 0))
        t = bpy.context.object; t.data.materials.append(m); parts.append(t)
    for i in range(3):
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.008, radius2=0, depth=0.025,
                                        location=(length + 0.012 + i * 0.025, 0, -0.03 + i * 0.004), rotation=(0, R(-140), 0))
        t = bpy.context.object; t.data.materials.append(m); parts.append(t)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH"); bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    return o

def _leg_points(base, tip, lift, n=7):
    """Asos -> tizza (tepada) -> uch: bo'g'imli siniq chiziq."""
    pts = []
    knee = base.lerp(tip, 0.35) + Vector((0, 0, lift))
    for i in range(n):
        t = i / (n - 1)
        if t < 0.35:
            p = base.lerp(knee, t / 0.35)
        else:
            p = knee.lerp(tip, (t - 0.35) / 0.65)
            p.z += 0.06 * math.sin(math.pi * (t - 0.35) / 0.65)
        pts.append(p)
    return pts

def build(name="tick", ground_z=0.0, tilt=38.0, leg_tip_fn=None, mats=None, loc=(0, 0, 0), heading=0.0):
    """Qaytaradi: dict(root, tilt, body_grp, body, scutum, hypo, hypo_grp, cheL, cheR, palps, legs, mats).
    root: og'iz (xipostom asosi) nuqtasi. tilt: bosh pastga egilish burchagi."""
    M = mats or _mats()
    root = C.empty(name + "_root", loc); root.rotation_euler.z = R(heading)
    tl = C.empty(name + "_tilt", (0, 0, 0), root); tl.rotation_euler.y = R(tilt)
    # boshcha (basis capituli)
    basis = C.box(name + "_basis", (0.16, 0.17, 0.08), (-0.07, 0, 0.0), M["mouth"], bevel=0.025); basis.parent = tl
    # tana guruhi: oldingi chekkasidan kattalashadi
    bg = C.empty(name + "_body_grp", (-0.16, 0, 0.02), tl)
    body = _body_mesh(name + "_body", M["body"]); body.parent = bg; body.location = (-0.5, 0, 0)
    bpy.context.view_layer.update()
    scu = _scutum(name + "_scutum", body, M["scutum"]); scu.parent = bg; scu.location = (-0.5, 0, 0)
    # palplar (yon tomonga yoyilgan)
    palps = []
    for s in (-1, 1):
        p = C.sphere(name + "_palp", 1.0, (0.0, s * 0.07, 0.0), M["mouth"], seg=24, ring=12)
        p.scale = (0.14, 0.03, 0.05); p.parent = tl
        p.rotation_euler.z = R(-s * 42); p.location = (0.06, s * 0.13, 0.0)
        palps.append(p)
    # xipostom (o'sishi/kirishi: hypo_grp.scale.x)
    hg = C.empty(name + "_hypo_grp", (0.0, 0, -0.005), tl)
    hypo = _hypostome(name + "_hypo", M["hypo"]); hypo.parent = hg
    # xelitseralar (pichoqlar)
    che = []
    for s in (-1, 1):
        e = C.empty(name + ("_cheL" if s < 0 else "_cheR"), (-0.02, s * 0.022, 0.035), tl)
        c = _chelicera(name + "_che", M["cheli"]); c.parent = e
        che.append(e)
    # oyoqlar: asos tanada (tilt fazosida), uch esa dunyo fazosida yerga
    bpy.context.view_layer.update()
    TW = tl.matrix_world.copy(); TWi = TW.inverted()
    legs = []
    angs = [32, 72, 108, 145]; lens = [0.72, 0.62, 0.62, 0.7]; bx = [-0.2, -0.3, -0.4, -0.5]
    for side in (-1, 1):
        for i in range(4):
            bl = Vector((bx[i], side * 0.2, -0.06))
            bw = TW @ bl
            a = R(angs[i]) * side + R(heading)
            d = Vector((math.cos(a), math.sin(a), 0))
            tip = bw + d * lens[i]; tip.z = ground_z + 0.012
            lift = 0.24
            if leg_tip_fn:
                tip, lift = leg_tip_fn(side, i, bw, tip, lift)
            pts_w = _leg_points(bw, tip, lift)
            e = C.empty(f"{name}_leg{side}{i}", bl, tl)
            bpy.context.view_layer.update()
            Ei = e.matrix_world.inverted()
            pts = [Ei @ p for p in pts_w]
            radii = [1.0, 0.85, 1.0, 0.8, 0.85, 0.6, 0.25]
            lg = C.tube(f"{name}_legc{side}{i}", pts, 0.032, M["leg"], radii=radii, res=0)
            lg.data.bevel_depth = 0.04
            lg.parent = e
            # tizzalarda kichik bo'g'im sharchalari
            for k in (1, 2, 4):
                j = C.sphere(f"{name}_joint", 0.03 * radii[k], pts[k], M["leg"], seg=12, ring=6); j.parent = e
            legs.append(e)
    return dict(root=root, tilt=tl, body_grp=bg, body=body, scutum=scu, hypo=hypo, hypo_grp=hg,
                cheL=che[0], cheR=che[1], palps=palps, legs=legs, mats=M, basis=basis)

def engorge(t, f, s):
    """s: 0 (och) .. 1 (to'yingan). Tana kattalashadi, rangi o'zgaradi, qalqon kichik qoladi."""
    sx, sy, sz = 1 + 1.15 * s, 1 + 0.95 * s, 1 + 1.9 * s
    bg = t["body_grp"]; bg.scale = (sx, sy, sz); bg.keyframe_insert("scale", frame=f)
    # qalqonni teskari masshtablab, kichik holda ushlab turamiz (shrinkwrap tanaga yopishtiradi)
    sc = t["scutum"]; sc.scale = (1 / sx, 1 / sy, 1 / sz); sc.location = (0.06 - 0.55 / sx, 0, 0)
    sc.keyframe_insert("scale", frame=f); sc.keyframe_insert("location", frame=f)
    nd = t["mats"]["body"].node_tree.nodes["engorge"].inputs["Factor"]
    nd.default_value = min(1.0, s * 1.15); nd.keyframe_insert("default_value", frame=f)
    rgh = C.principled(t["mats"]["body"]).inputs["Roughness"]
    rgh.default_value = 0.32 - 0.14 * s; rgh.keyframe_insert("default_value", frame=f)
