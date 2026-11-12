# "Pichoqni sug'urma!" — Zack D. Films uslubida 39.5 s (949 kadr, 24 fps, 9:16).
# Besh dunyo bitta faylda (metr): mehmonxona (0,0,0), kino ko'chasi (100,0,0), rentgen tana (200,0,0),
# shisha studiyasi (400,0,0); makro kesim (1000,0,0) [1 birlik = 1 mm]. Kesishlar kamera markerlari bilan (STORYBOARD.md).
# Render: OUT=... SAMPLES=8 PCT=40 python -I pichoq.py --render   (FRAMES=1,60 sinov uchun, RANGE=a,b qism)
import bpy, bmesh, math, sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ZT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ZT, "goz")); sys.path.insert(0, ZT)
from mathutils import Vector, Matrix
import numpy as np
import parts as P                                   # zack_test/goz/parts.py
from parts import R, box, cyl, sphere, empty, par, mat, bsdf, vis, cam_move, camera
import mixchar as mc

OUT = os.environ.get("OUT", "/tmp/claude-0/frames/")
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
NF = 949
sc.frame_start, sc.frame_end, sc.render.fps = 1, NF, 24

# kadrlar (ovoz so'zlariga bog'langan, STORYBOARD.md; 14 ikki kameraga bo'lingan: 14, 15)
S = {1: (1, 31), 2: (32, 71), 3: (72, 95), 4: (96, 135), 5: (136, 183), 6: (184, 236), 7: (237, 285), 8: (286, 334),
     9: (335, 360), 10: (361, 397), 11: (398, 461), 12: (462, 513), 13: (514, 555), 14: (556, 624), 15: (625, 692),
     16: (693, 720), 17: (721, 771), 18: (772, 848), 19: (849, 889), 20: (890, NF)}
def rng(*shots): return [S[s] for s in shots]
ROOM = Vector((0, 0, 0)); ST = Vector((100, 0, 0)); XR = Vector((200, 0, 0)); BT = Vector((400, 0, 0)); MC = Vector((1000, 0, 0))
K = lambda v: tuple(v)
YANK = 117                      # kino: pichoq sug'uriladigan kadr ("sug'urib" ~4.9 s)
PULL0, PULL1 = 721, 733         # makro: tig' arteriyadan chiqadi

def keyv(sock, f, v, path="default_value"):
    setattr(sock, path, v); sock.keyframe_insert(path, frame=f)

def all_const(idb):
    for fc in P.all_fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"

def vis_only(o, ranges):
    """Ota vis() qoldirgan hide_render kalitlarini o'chirib, faqat shu oraliqlarni qo'yish (o va bolalari)."""
    for x in [o] + list(o.children_recursive):
        ad = x.animation_data
        if ad and ad.action:
            act = ad.action
            bags = [cb for l in act.layers for st in l.strips for cb in st.channelbags] if getattr(act, "layers", None) else [act]
            for cb in bags:
                for fc in [fc for fc in cb.fcurves if fc.data_path == "hide_render"]: cb.fcurves.remove(fc)
    vis(o, ranges)

def tame(meshes, rough=0.55):
    for o in meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Specular IOR Level"].links): m.node_tree.links.remove(l)
                    n.inputs["Specular IOR Level"].default_value = 0.3
                    if "hair" not in m.name.lower():
                        for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                        n.inputs["Roughness"].default_value = rough
                    n.inputs["Coat Weight"].default_value = 0.0

def area(nm, loc, rot, en, size, col, cam_vis=False):
    l = P.link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA"))); l.data.energy = en; l.data.size = size
    l.data.color = col; l.location = loc; l.rotation_euler = rot; l.visible_camera = cam_vis; return l

def point(nm, loc, en, col, r=0.05):
    l = P.link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "POINT"))); l.data.energy = en; l.data.color = col
    l.data.shadow_soft_size = r; l.location = loc; l.visible_camera = False; return l

def glow_mat(name, col, strength=4.0, power=2.0):
    """Yumshoq nur: markazi yorqin, chetlari shaffof (Transparent + Emission Add, CLAUDE.md)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = N["Material Output"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L.new(lw.outputs["Facing"], inv.inputs[1])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; L.new(inv.outputs[0], pw.inputs[0]); pw.inputs[1].default_value = power
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(pw.outputs[0], mu.inputs[0])
    st = N.new("ShaderNodeValue"); st.name = "STR"; st.outputs[0].default_value = strength; L.new(st.outputs[0], mu.inputs[1])
    L.new(mu.outputs[0], em.inputs["Strength"])
    ad = N.new("ShaderNodeAddShader"); tr = N.new("ShaderNodeBsdfTransparent")
    L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs["Surface"])
    return m

def xray_mat(name, col, strength=2.0, inner=0.04):
    """Rentgen qobiq: chetlari yorqin (fresnel), o'rtasi deyarli shaffof — transmission'siz (CLAUDE.md: aql.py)."""
    m = glow_mat(name, col, strength, power=3.2)
    N = m.node_tree.nodes; L = m.node_tree.links
    mu = [n for n in N if n.type == "MATH" and n.operation == "MULTIPLY"][0]
    ad = N.new("ShaderNodeMath"); ad.operation = "ADD"; ad.inputs[1].default_value = inner
    L.new(mu.outputs[0], ad.inputs[0]); L.new(ad.outputs[0], N["Emission"].inputs["Strength"])
    return m

def organ_mat(name, col, emit=1.2, alpha=0.75):
    """Rentgen ichidagi a'zo: rangli emissiya + yarim shaffof."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1)
    mr = N.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = emit * 0.55; mr.inputs["To Max"].default_value = emit * 1.4
    L.new(lw.outputs["Fresnel"], mr.inputs["Value"])
    st = N.new("ShaderNodeValue"); st.name = "STR"; st.outputs[0].default_value = 1.0
    mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(mr.outputs[0], mu.inputs[0]); L.new(st.outputs[0], mu.inputs[1])
    L.new(mu.outputs[0], em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    N["Material Output"] if "Material Output" in N else None
    L.new(mx.outputs[0], [n for n in N if n.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
    return m

def cmat(name, col, rough=0.5, emit=0.0, sss=0.0, tex=None, tex_scale=3.0, col2=None, bump=0.0, emit_col=None):
    m = mat(name, col, rough, emit=emit, emit_col=emit_col)
    b = bsdf(m)
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.4
    if tex:
        nt = m.node_tree; N = nt.nodes; L = nt.links; g = P.G(nt)
        tc = N.new("ShaderNodeTexCoord")
        t = N.new("ShaderNodeTexWave" if tex == "wave" else "ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = tex_scale
        if tex == "wave": t.inputs["Distortion"].default_value = 9; t.inputs["Detail"].default_value = 6; t.inputs["Detail Scale"].default_value = 2
        L.new(tc.outputs["Object"], t.inputs["Vector"])
        L.new(g.mixcol(t.outputs["Fac"], col, col2 or tuple(c * 0.7 for c in col)), b.inputs["Base Color"])
        if bump:
            bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(t.outputs["Fac"], bp.inputs["Height"])
            L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def tube(name, pts, r, m, res=4):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = res
    cu.use_fill_caps = True
    spl = cu.splines.new("BEZIER"); spl.bezier_points.add(len(pts) - 1)
    for bp_, p in zip(spl.bezier_points, pts):
        bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
    o = P.link(bpy.data.objects.new(name, cu)); cu.materials.append(m)
    return o

def lathe(name, prof, m, loc, steps=48):
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in prof]
    for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=steps, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    o = P.mesh_obj(name, bm, m, loc); P.smooth(o); return o

A_ = lambda f, inplace=True: mc.load_action(f, inplace)
def bone_mat(arm, b):
    """Suyakning dunyo matritsasi, masshtabsiz (CHILD_OF use_scale=False bilan mos)."""
    M = arm.matrix_world @ arm.pose.bones["mixamorig:" + b].matrix
    l, q, _ = M.decompose(); return Matrix.LocRotScale(l, q, None)
def bone_head(arm, b): return arm.matrix_world @ arm.pose.bones["mixamorig:" + b].head
def bone_child(name, arm, b, local=Matrix.Identity(4)):
    e = empty(name); c = e.constraints.new("CHILD_OF"); c.target = arm; c.subtarget = "mixamorig:" + b
    c.use_scale_x = c.use_scale_y = c.use_scale_z = False; c.inverse_matrix = Matrix.Identity(4)
    e.matrix_basis = local; return e
def look_basis(d_in, up=Vector((0, 0, 1))):
    """Pichoq matritsasi: mahalliy -Z = tanaga kirish yo'nalishi, +X = tig' orqasi (tepaga), edge -X."""
    z = (-d_in).normalized(); x = (up - up.dot(z) * z).normalized(); y = z.cross(x)
    return Matrix((x, y, z)).transposed()

# ------------------------------------------------------------------- pichoq modeli (metr; mm uchun s=1000)
STEEL = mat("steel", (0.86, 0.87, 0.9), 0.12, metal=1.0)
HANDLE = mat("knife_handle", (0.025, 0.022, 0.02), 0.4, coat=0.4)
RIVET = mat("rivet", (0.75, 0.72, 0.65), 0.2, metal=1.0)
BL = 0.17
def blade_profile(s=1.0, grow=0.0):
    p = [(0.007, 0.0), (0.0075, -BL * 0.62), (0.004, -BL * 0.86), (-0.001, -BL), (-0.012, -BL * 0.82),
         (-0.019, -BL * 0.55), (-0.021, -BL * 0.2), (-0.021, 0.0)]
    return [((x + (grow if x > 0 else -grow)) * s, (z - (grow if z < -BL * 0.5 else 0)) * s) for x, z in p]
def prism(name, prof, th, m, loc=(0, 0, 0)):
    bm = bmesh.new()
    vf = [bm.verts.new((x, -th / 2, z)) for x, z in prof]; vb = [bm.verts.new((x, th / 2, z)) for x, z in prof]
    bm.faces.new(vf[::-1]); bm.faces.new(vb)
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((vf[i], vf[j], vb[j], vb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return P.mesh_obj(name, bm, m, loc)
def make_knife(name, s=1.0):
    """Mahalliy: tig' -Z bo'ylab (uchi -BL da), dasta +Z bo'ylab; teri sathi = (0,0,0)."""
    root = empty(name)
    bl = prism(name + "_blade", blade_profile(s), 0.0018 * s, STEEL); bl.parent = root
    bv = bl.modifiers.new("bev", "BEVEL"); bv.width = 0.0005 * s; bv.segments = 2
    bo = box(name + "_bolster", (0.031 * s, 0.012 * s, 0.008 * s), (-0.007 * s, 0, 0.004 * s), STEEL, bevel=0.001 * s); bo.parent = root
    hd = box(name + "_handle", (0.027 * s, 0.017 * s, 0.11 * s), (-0.006 * s, 0, 0.063 * s), HANDLE, bevel=0.005 * s); hd.parent = root
    for z in (0.035, 0.07, 0.1):
        rv = cyl(name + "_rivet", 0.0028 * s, 0.0182 * s, (-0.006 * s, 0, z * s), RIVET, rot=(90, 0, 0), verts=16); rv.parent = root
    return root
BLOODSTAIN = mat("stain", (0.16, 0.0, 0.004), 0.35, coat=0.6)
def stain(name, parent, r=0.035):
    st = sphere(name, 1.0, (0, 0, 0), BLOODSTAIN, scale=(r, r * 0.8, 0.004), seg=24); st.parent = parent; return st

def knife_pose(arm, torso, aorta_off=Vector((0.014, -0.045, 0.0)), ray_from=Vector((0.32, -0.26, 0.0))):
    """Aortaga qarab ketgan pichoq: chap biqindan kiradi (nur faqat tana/ko'ylakka — qo'lga emas).
    Qaytaradi: (Spine-mahalliy matritsa, kirish nuqtasi, aorta nuqtasi, tig' asosi)."""
    bpy.context.view_layer.update()
    A0 = bone_head(arm, "Spine") + aorta_off
    o = A0 + ray_from; d = (A0 - o).normalized()
    dg = bpy.context.evaluated_depsgraph_get()
    best = None
    for ob in torso:
        Mi = ob.matrix_world.inverted()
        ok, loc, *_ = ob.ray_cast(Mi @ o, (Mi.to_3x3() @ d).normalized(), depsgraph=dg)
        if ok:
            wl = ob.matrix_world @ loc
            if best is None or (wl - o).length < (best - o).length: best = wl
    print("knife entry", arm.name, best, "aorta", A0)
    entry = best if best is not None else A0 + ray_from * 0.4
    din = (A0 - entry).normalized()
    tip = A0 + din * 0.006
    org = tip - din * BL                         # tig' asosi (dasta boshlanishi)
    Mw = Matrix.Translation(org) @ look_basis(din).to_4x4()
    return bone_mat(arm, "Spine").inverted() @ Mw, entry, A0, org

def hand_rig(arm, knife_e, tag, pole_world, grip_off=Vector((-0.006, 0, 0.06))):
    """O'ng qo'l pichoq dastasini ushlaydi: IK (forearm tail -> wristE), DAMPED_TRACK, barmoq bukish.
    Bilak va barmoq nishonlari dunyo yo'nalishida (o'ng = -X, old = -Y) hisoblanib, pichoqqa bog'lanadi."""
    bpy.context.view_layer.update()
    Mk = knife_e.matrix_world; Mi = Mk.inverted()
    gw = Mk @ grip_off
    pinch = empty(f"{tag}_pinch", K(Mi @ (gw + Vector((0.06, -0.02, -0.03))))); pinch.parent = knife_e
    wrist = empty(f"{tag}_wrist", K(Mi @ (gw + Vector((-0.075, -0.035, -0.005))))); wrist.parent = knife_e
    pole = empty(f"{tag}_pole", pole_world)
    fa = arm.pose.bones["mixamorig:RightForeArm"]; hb = arm.pose.bones["mixamorig:RightHand"]
    ik = fa.constraints.new("IK"); ik.target = wrist; ik.chain_count = 2; ik.use_tail = True
    ik.pole_target = pole; ik.pole_angle = R(-90)
    dt = hb.constraints.new("DAMPED_TRACK"); dt.target = pinch; dt.track_axis = "TRACK_Y"
    curlE = empty(f"{tag}_curl", (1.0, 0, 0)); curls = []
    for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
        for i in (1, 2, 3):
            pbn = arm.pose.bones.get(f"mixamorig:RightHand{fn}{i}")
            if not pbn: continue
            c_ = pbn.constraints.new("TRANSFORM"); c_.target = curlE; c_.map_from = "LOCATION"; c_.from_min_x = 0; c_.from_max_x = 1
            c_.map_to = "ROTATION"; c_.owner_space = "LOCAL"; c_.target_space = "WORLD"; c_.mix_mode_rot = "AFTER"
            c_.map_to_x_from = "X"; c_.to_min_x_rot = 0; c_.to_max_x_rot = R(40 if fn == "Thumb" else 80)
            curls.append(c_)
    return dict(ik=ik, dt=dt, curls=curls, wrist=wrist, pole=pole, pinch=pinch)
def infl(cons, f, v):
    for con in cons:
        con.influence = v; con.keyframe_insert("influence", frame=f)

WORLD_OBJS = {k: [] for k in ("room", "street", "xray", "bottle", "macro")}
def W(world, *objs):
    WORLD_OBJS[world].extend(objs); return objs[0] if len(objs) == 1 else objs

# =================================================================== 1) MEHMONXONA (metr)
floor_m = P.tex_image_mat("ph_floor", PH + "laminate_floor_02", 0.5)
plaster = P.tex_image_mat("ph_plaster", PH + "painted_plaster_wall", 0.5, tint=(0.95, 0.88, 0.78))
W("room", box("r_floor", (7, 7, 0.04), (0, 0.4, -0.02), floor_m))
W("room", box("r_ceiling", (7, 7, 0.04), (0, 0.4, 2.72), mat("ceil", (0.92, 0.9, 0.86), 0.8)))
W("room", box("r_wall_back", (7, 0.08, 2.74), (0, 2.9, 1.35), plaster))
W("room", box("r_wall_l", (0.08, 7, 2.74), (-3.0, 0.4, 1.35), plaster))
W("room", box("r_wall_front", (7, 0.08, 2.74), (0, -3.1, 1.35), plaster))
# o'ng devor deraza teshigi bilan (ko'k-qizil chiroqlar shu yerdan kiradi)
for nm, sz, lc in (("r_wall_r1", (0.08, 2.8, 2.74), (3.0, -1.7, 1.35)), ("r_wall_r2", (0.08, 2.2, 2.74), (3.0, 2.8, 1.35)),
                   ("r_wall_r3", (0.08, 1.6, 0.9), (3.0, 0.5, 0.45)), ("r_wall_r4", (0.08, 1.6, 0.6), (3.0, 0.5, 2.42))):
    W("room", box(nm, sz, lc, plaster))
wg = W("room", box("r_win_glow", (0.02, 1.6, 1.24), (3.06, 0.5, 1.52), mat("winglow", (0.7, 0.8, 1.0), 0.3, emit=2.5)))
wg.visible_shadow = False
W("room", box("r_win_frame", (0.06, 1.62, 0.04), (2.98, 0.5, 1.52), mat("wframe", (0.9, 0.9, 0.88), 0.4)))
W("room", box("r_baseboard", (6.9, 0.02, 0.1), (0, 2.85, 0.05), mat("base", (0.92, 0.9, 0.86), 0.4)))
sofa, sp = P.import_gltf(PH + "Sofa_01/Sofa_01.gltf", (0.1, 2.2, 0), name="sofa"); W("room", sofa, *sp)
tab, tp = P.import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (0.1, 1.15, 0), name="table"); W("room", tab, *tp)
pl, pp = P.import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-1.6, 2.4, 0), name="plant"); pl.scale = (1.3,) * 3; W("room", pl, *pp)
# stol ustida: kesish taxtasi + olma (pichoq shu yerdan)
W("room", box("r_board", (0.34, 0.22, 0.02), (0.25, 1.05, 0.42), mat("board", (0.55, 0.36, 0.2), 0.5), bevel=0.004))
W("room", sphere("r_apple", 0.04, (0.18, 1.05, 0.47), mat("apple", (0.6, 0.05, 0.04), 0.3, coat=0.5)))
W("room", sphere("r_apple2", 0.04, (0.3, 1.08, 0.465), mat("apple_in", (0.95, 0.9, 0.7), 0.5), scale=(1, 1, 0.6)))
# devordagi rasm (oynasiz — CLAUDE.md: aks ettirmasin)
W("room", box("r_art", (1.0, 0.03, 0.7), (0.1, 2.85, 1.65), mat("art", (0.35, 0.45, 0.55), 0.7), bevel=0.01))
W("room", area("r_key", (-1.6, -1.8, 2.4), (R(55), 0, R(-35)), 220, 1.5, (1.0, 0.88, 0.75)))
W("room", area("r_win", (2.6, 0.5, 1.6), (0, R(90), 0), 160, 1.4, (0.75, 0.85, 1.0)))
W("room", area("r_ceil", (0, 0.6, 2.62), (0, 0, 0), 120, 1.6, (1.0, 0.9, 0.78)))
W("room", area("r_rim", (-0.8, 1.6, 2.2), (R(-55), 0, R(-160)), 90, 0.8, (1.0, 0.82, 0.65)))
# tez yordam chiroqlari (19-kadr): deraza tashqarisida ko'k/qizil miltillash
amb_b = W("room", area("amb_blue", (3.6, 0.5, 1.9), (0, R(70), 0), 0, 1.6, (0.1, 0.25, 1.0)))
amb_r = W("room", area("amb_red", (3.6, 0.2, 1.7), (0, R(70), 0), 0, 1.6, (1.0, 0.06, 0.04)))
for f in range(1, NF + 1, 3):
    on = S[19][0] - 2 <= f <= NF
    ph = (f // 6) % 2
    amb_b.data.energy = (9000 if ph == 0 else 300) * on; amb_b.data.keyframe_insert("energy", frame=f)
    amb_r.data.energy = (8000 if ph == 1 else 250) * on; amb_r.data.keyframe_insert("energy", frame=f)
all_const(amb_b.data); all_const(amb_r.data)
for ln in ("r_key", "r_ceil", "r_rim", "r_win"):
    ld = bpy.data.objects[ln].data; e0 = ld.energy
    for f, v in ((1, e0), (S[19][0] - 1, e0), (S[19][0], e0 * 0.15)):
        ld.energy = v; ld.keyframe_insert("energy", frame=f)
    all_const(ld)

# --- Megan ---
mroot, meg, mmesh = mc.load_character("megan", "Megan.fbx"); sc.render.fps = 24; tame(mmesh, 0.5)
idle = A_("Injured_Idle.fbx"); sc.render.fps = 24
L_idle = (idle.frame_range[1] - idle.frame_range[0]) * 0.8
mc.add_strip(meg, idle, -40, repeat=math.ceil((S[19][0] + 60) / L_idle), blend=0)
dying8 = A_("Dying_8.fbx", inplace=False); sc.render.fps = 24
s8 = mc.add_strip(meg, dying8, S[19][0] - 1, blend=0); s8.repeat = 1.0
# yotganda ham shu xona (19-kadr): root siljitiladi
for f, loc, rz in ((1, (0, 0, 0), 0), (S[19][0] - 2, (0, 0, 0), 0), (S[19][0] - 1, (0.25, -0.2, 0.0), R(-20))):
    mroot.location = loc; mroot.rotation_euler = (0, 0, rz)
    mroot.keyframe_insert("location", frame=f); mroot.keyframe_insert("rotation_euler", frame=f)
all_const(mroot)
W("room", mroot)
sc.frame_set(250)
MK_local, M_entry, M_A, _ = knife_pose(meg, [o for o in mmesh if "Shirt" in o.name or "Body" in o.name])
mk_e = bone_child("meg_knife_e", meg, "Spine", MK_local)
mk = make_knife("meg_knife"); mk.parent = mk_e
for f, z in ((1, 0.0), (520, 0.0), (555, 0.04)):           # 13-kadr: tortila boshlaydi
    mk.location = (0, 0, z); mk.keyframe_insert("location", frame=f)
mst = empty("meg_stain_e"); mst.parent = mk_e
# dog' teri (kirish) nuqtasida: pichoq mahalliy koordinatasida kirish = asos + din * |entry-org|
_org_w = (bone_mat(meg, "Spine") @ MK_local).translation
mst.location = (0, 0, -(M_entry - _org_w).length)
stain("meg_stain", mst, 0.045)
mrig = hand_rig(meg, mk, "meg", (-0.6, 0.4, 1.0))
mcons = [mrig["ik"], mrig["dt"]] + mrig["curls"]
infl(mcons, 1, 0.0); infl(mcons, 440, 0.0); infl(mcons, 458, 1.0); infl(mcons, 556, 1.0); infl(mcons, 557, 0.0)
W("room", mk_e)
# polda yotgan pichoq va qon (19-kadr)
fk = make_knife("floor_knife"); fk.location = (0.75, -0.75, 0.012); fk.rotation_euler = (R(90), 0, R(30))
W("room", fk)
pool_r = sphere("room_pool", 1.0, (0.42, -0.3, 0.002), BLOODSTAIN, scale=(0.3, 0.22, 0.002), seg=32)
for f, s in ((1, 0.6), (S[19][0], 0.6), (S[19][1], 1.0)):
    pool_r.scale = (0.3 * s, 0.22 * s, 0.002); pool_r.keyframe_insert("scale", frame=f)
W("room", pool_r)
ROOMS = rng(7, 12, 13, 19)

# =================================================================== 2) KINO KO'CHASI (shom)
asph = P.tex_image_mat("ph_asphalt", PH + "asphalt_02", 0.35)
pave = P.tex_image_mat("ph_pave", PH + "concrete_pavement", 0.5)
W("street", box("s_road", (60, 14, 0.04), K(ST + Vector((0, -5, -0.02))), asph))
W("street", box("s_walk", (60, 4, 0.14), K(ST + Vector((0, 4, 0.07))), pave))
W("street", box("s_curb", (60, 0.15, 0.16), K(ST + Vector((0, 1.98, 0.08))), mat("curb", (0.55, 0.54, 0.52), 0.7)))
fac = P.tex_image_mat("ph_fac", PH + "concrete_pavement", 0.25, tint=(0.45, 0.42, 0.42))
WINM = [mat(f"win{i}", c, 0.3, emit=e) for i, (c, e) in enumerate((((1.0, 0.7, 0.4), 4.0), ((0.9, 0.85, 0.7), 2.5), ((0.08, 0.09, 0.12), 0.0)))]
rr = random.Random(5)
for bi, (bx0, w_, h_) in enumerate(((-14, 9, 14), (-4.5, 8, 20), (4.5, 8.5, 11), (13.5, 9, 17))):
    W("street", box(f"s_bld{bi}", (w_, 6, h_), K(ST + Vector((bx0, 9.1, h_ / 2))), fac))
    for i in range(int(w_ / 1.6)):
        for j in range(int(h_ / 3.0)):
            m_ = WINM[0] if rr.random() < 0.3 else (WINM[1] if rr.random() < 0.2 else WINM[2])
            W("street", box("s_win", (1.0, 0.05, 1.5), K(ST + Vector((bx0 - w_ / 2 + 0.9 + i * 1.6, 6.07, 2.0 + j * 3.0))), m_))
LAMP = mat("lampglow", (1.0, 0.75, 0.45), 0.3, emit=25)
POLE = mat("pole", (0.06, 0.06, 0.065), 0.4, metal=0.8)
for li, lx in enumerate((-9, 3.8, 14)):
    W("street", cyl(f"s_pole{li}", 0.06, 5.5, K(ST + Vector((lx, 2.5, 2.9))), POLE))
    W("street", cyl(f"s_arm{li}", 0.04, 1.2, K(ST + Vector((lx, 2.0, 5.6))), POLE, rot=(90, 0, 0)))
    W("street", box(f"s_head{li}", (0.4, 0.25, 0.08), K(ST + Vector((lx, 1.4, 5.55))), LAMP))
    W("street", point(f"s_lamp{li}", K(ST + Vector((lx, 1.4, 5.3))), 900, (1.0, 0.7, 0.4), 0.3))
# to'xtab turgan mashina silueti (qorong'i), uzoqda
W("street", box("s_car", (4.3, 1.8, 1.0), K(ST + Vector((-6.5, -2.5, 0.7))), mat("carbody", (0.05, 0.06, 0.08), 0.2, metal=0.6, coat=1.0), bevel=0.25))
W("street", box("s_carroof", (2.2, 1.6, 0.6), K(ST + Vector((-6.7, -2.5, 1.45))), mat("cargl", (0.02, 0.02, 0.03), 0.05, coat=1.0), bevel=0.2))
for cx_ in (-5.0, -8.0):
    for cy_ in (-3.35, -1.65):
        W("street", cyl("s_wheel", 0.36, 0.25, K(ST + Vector((cx_, cy_, 0.36))), mat("tire", (0.02, 0.02, 0.02), 0.8), rot=(90, 0, 0)))
W("street", box("s_tail", (0.05, 1.6, 0.12), K(ST + Vector((-4.33, -2.5, 0.95))), mat("taillight", (1.0, 0.05, 0.02), 0.3, emit=12)))
# yorug'lik: shom quyoshi (orqa-chapdan iliq kontur), ko'k to'ldiruvchi
W("street", area("s_sun", K(ST + Vector((-6, 7, 3.5))), (R(-70), 0, R(-140)), 9000, 4.0, (1.0, 0.55, 0.25)))
W("street", area("s_fill", K(ST + Vector((3, -6, 3))), (R(60), 0, R(25)), 1200, 4.0, (0.45, 0.6, 1.0)))
W("street", area("s_rim2", K(ST + Vector((4, 3, 2.2))), (R(-70), 0, R(130)), 2200, 2.0, (1.0, 0.6, 0.35)))

lroot, leo, lmesh = mc.load_character("leo", "Leonard.fbx"); sc.render.fps = 24; tame(lmesh, 0.55)
lroot.location = K(ST)
stum = A_("Injured_Stumble_Idle.fbx"); sc.render.fps = 24
L_st = (stum.frame_range[1] - stum.frame_range[0]) * 0.8
mc.add_strip(leo, stum, -30, repeat=math.ceil(200 / L_st) + 1, blend=0)
dy6 = A_("Dying_6.fbx", inplace=False); sc.render.fps = 24
mc.add_strip(leo, dy6, 136, blend=6)
sc.frame_set(60)
LK_local, L_entry, L_A, _ = knife_pose(leo, [o for o in lmesh if "Sweater" in o.name or "Body" in o.name])
lk_e = bone_child("leo_knife_e", leo, "Spine", LK_local)
lk = make_knife("leo_knife"); lk.parent = lk_e
lst = empty("leo_stain_e"); lst.parent = lk_e
_org_l = (bone_mat(leo, "Spine") @ LK_local).translation
lst.location = (0, 0, -(L_entry - _org_l).length); lstain = stain("leo_stain", lst, 0.05)
lrig = hand_rig(leo, lk, "leo", K(ST + Vector((-0.6, 0.45, 1.0))))
lcons = [lrig["ik"], lrig["dt"]] + lrig["curls"]
infl(lcons, 1, 0.0); infl(lcons, 34, 0.0); infl(lcons, 48, 1.0)
# sug'urish: pichoq tanadan keskin chiqadi (mahalliy +Z bo'ylab) — keyin qo'ldagi nusxa
for f, z in ((1, 0.0), (YANK - 6, 0.0), (YANK - 3, -0.01), (YANK, 0.2)):
    lk.location = (0, 0, z); lk.keyframe_insert("location", frame=f)
for fc in P.all_fcurves(lk):
    for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "EASE_IN"
# ikkinchi IK: qo'l pichoq bilan yuqoriga ko'tariladi (qahramon pozasi), keyin yiqilishda o'chadi
raise_e = empty("leo_raise")
fa = leo.pose.bones["mixamorig:RightForeArm"]
ik2 = fa.constraints.new("IK"); ik2.target = raise_e; ik2.chain_count = 2; ik2.use_tail = True
ik2.pole_target = lrig["pole"]; ik2.pole_angle = R(-90)
sc.frame_set(YANK)
W0 = leo.matrix_world @ fa.tail
for f, p in ((YANK, W0), (YANK + 9, ST + Vector((-0.42, -0.3, 1.5))), (138, ST + Vector((-0.44, -0.28, 1.53)))):
    raise_e.location = p; raise_e.keyframe_insert("location", frame=f)
for c_, f, v in ((ik2, 1, 0.0), (ik2, YANK, 0.0), (ik2, YANK + 2, 1.0), (ik2, 138, 1.0), (ik2, 150, 0.0)):
    c_.influence = v; c_.keyframe_insert("influence", frame=f)
infl([lrig["ik"], lrig["dt"]], YANK + 1, 1.0); infl([lrig["ik"], lrig["dt"]], YANK + 2, 0.0)
infl(lrig["curls"], 170, 1.0); infl(lrig["curls"], 185, 0.3)
# qo'ldagi pichoq: sug'urish kadrida RightHand ga bog'lanadi
sc.frame_set(YANK + 1)
Mk_w = lk.matrix_world.copy()
lk2 = make_knife("leo_knife_hand")
lk2_e = bone_child("leo_knife_hand_e", leo, "RightHand", bone_mat(leo, "RightHand").inverted() @ Mk_w)
lk2.parent = lk2_e
# tig'dagi qon (sug'urilgandan keyin)
BLADE_BLOOD = mat("blade_blood", (0.22, 0.0, 0.005), 0.15, coat=0.9)
bb = prism("leo_blade_blood", blade_profile(1.0)[2:6], 0.0022, BLADE_BLOOD); bb.parent = lk2
vis(lk, [(1, YANK)]); vis(lk2_e, [(YANK + 1, NF)])
# yerdagi qon ko'lmagi (6-kadr)
pool = sphere("street_pool", 1.0, K(ST + Vector((-0.05, -1.05, 0.003))), BLOODSTAIN, scale=(0.02, 0.02, 0.002), seg=32)
for f, s in ((1, 0.02), (200, 0.05), (236, 0.55)):
    pool.scale = (s * 0.8, s, 0.002); pool.keyframe_insert("scale", frame=f)
W("street", lroot, lk_e, lk2_e, pool)
STREETS = rng(1, 2, 3, 4, 5, 6)

# =================================================================== 3) RENTGEN TANA (Megan nusxasi, muzlatilgan)
xroot, megx, xmesh = mc.load_character("megx", "Megan.fbx"); sc.render.fps = 24
xroot.location = K(XR)
mc.add_strip(megx, idle, 1, blend=0, src=(30, 31))
XRM = xray_mat("xray_body", (0.2, 0.5, 1.0), 0.85, inner=0.0)
for o in xmesh:
    if "Eyelash" in o.name: o.hide_render = True; continue
    o.data.materials.clear(); o.data.materials.append(XRM)
sc.frame_set(300)
XK_local, X_entry, X_A, X_org = knife_pose(megx, [o for o in xmesh if "Shirt" in o.name or "Body" in o.name])
xk_e = bone_child("x_knife_e", megx, "Spine", XK_local)
xk = make_knife("x_knife"); xk.parent = xk_e
H_ = bone_head(megx, "Hips"); S0 = bone_head(megx, "Spine"); S1 = bone_head(megx, "Spine1"); S2 = bone_head(megx, "Spine2")
NK = bone_head(megx, "Neck")
print("XRAY bones", H_, S0, S1, S2, NK, "entry", X_entry, "A", X_A)
FWD = Vector((0, -1, 0))
AO = organ_mat("aorta_x", (1.0, 0.06, 0.03), 1.5, 0.9)
VC = organ_mat("vcava_x", (0.15, 0.3, 1.0), 1.6, 0.7)
aoff = Vector((0.014, -0.045, 0))
heart_p = S2 + Vector((0.025, -0.075, -0.02))
ao_pts = [heart_p + Vector((0, 0.01, 0.04)), heart_p + Vector((-0.01, 0.03, 0.08)), S2 + aoff + Vector((0, 0.01, 0.06)), S2 + aoff, S1 + aoff,
          S0 + aoff, H_ + aoff + Vector((0, 0, 0.04))]
aorta = tube("x_aorta", [K(p) for p in ao_pts], 0.012, AO)
for sx in (1, -1):
    tube(f"x_iliac{sx}", [K(H_ + aoff + Vector((0, 0, 0.04))), K(H_ + Vector((0.04 * sx + 0.01, -0.05, -0.04))),
                          K(H_ + Vector((0.085 * sx, -0.04, -0.14)))], 0.008, AO)
    tube(f"x_artarm{sx}", [K(S2 + aoff + Vector((0, 0.01, 0.07))), K(S2 + Vector((0.07 * sx, -0.02, 0.1)))], 0.006, AO)
vc_pts = [K(p + Vector((-0.032, 0.005, 0))) for p in ao_pts[2:]]
tube("x_vcava", vc_pts, 0.013, VC)
HEART = organ_mat("heart_x", (1.0, 0.08, 0.05), 1.8, 1.0)
hn = HEART.node_tree.nodes; hl = HEART.node_tree.links
mixc = hn.new("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.name = "DRAIN"
mixc.inputs[6].default_value = (1.0, 0.1, 0.06, 1); mixc.inputs[7].default_value = (0.75, 0.62, 0.62, 1)
hl.new(mixc.outputs[2], hn["Emission"].inputs["Color"])
heart = sphere("x_heart", 1.0, K(heart_p), HEART, scale=(0.045, 0.04, 0.055), seg=32)
heart.rotation_euler = (R(20), R(-25), R(30))
hd_ = heart.modifiers.new("lumpy", "DISPLACE"); htx = bpy.data.textures.new("heart_t", "CLOUDS"); htx.noise_scale = 0.4
hd_.texture = htx; hd_.strength = 0.12
LUNG = organ_mat("lung_x", (1.0, 0.55, 0.6), 0.7, 0.45)
for sx in (1, -1):
    sphere(f"x_lung{sx}", 1.0, K(S2 + Vector((0.07 * sx, -0.03, 0.05))), LUNG, scale=(0.06, 0.06, 0.11), seg=24)
LIVER = organ_mat("liver_x", (0.6, 0.12, 0.08), 1.0, 0.6)
liv = sphere("x_liver", 1.0, K(S1 + Vector((-0.05, -0.06, -0.01))), LIVER, scale=(0.09, 0.06, 0.05), seg=24)
liv.rotation_euler = (0, R(12), 0)
GUT = organ_mat("gut_x", (1.0, 0.65, 0.5), 1.0, 0.55)
rg_ = random.Random(3); gp = []
cx0 = (H_ + S1) / 2 + Vector((0, -0.07, -0.01))
for i in range(26):
    a = i * 1.9; rr_ = 0.03 + 0.05 * rg_.random()
    gp.append(cx0 + Vector((rr_ * math.cos(a), 0.025 * math.sin(a * 0.7), -0.06 + 0.12 * (i / 25) + 0.012 * math.sin(a))))
gut = tube("x_gut", [K(p) for p in gp], 0.011, GUT, res=3)
for o_ in ("x_aorta", "x_vcava", "x_heart", "x_liver", "x_gut", "x_lung1", "x_lung-1", "x_iliac1", "x_iliac-1", "x_artarm1", "x_artarm-1"):
    W("xray", bpy.data.objects[o_])
# aorta urishi (emissiya), 8-kadrda tig' uchida yonish
aoS = AO.node_tree.nodes["STR"].outputs[0]
hS = HEART.node_tree.nodes["STR"].outputs[0]
drain = mixc.inputs[0]
def beats(f0, f1, period0, period1, amp0, amp1):
    f = f0
    while f < f1:
        u = (f - f0) / max(1, f1 - f0); per = period0 + (period1 - period0) * u; amp = amp0 + (amp1 - amp0) * u
        yield int(f), int(per), amp
        f += per
for f, per, amp in beats(1, NF, 17, 17, 1.0, 1.0):
    for df, v in ((0, 1.0), (3, 1.9), (8, 1.0)):
        keyv(aoS, f + df, v)
# yurak: 20-kadrda sekinlashib, kichrayib, oqaradi
HS = Vector((0.045, 0.04, 0.055))
for f, per, amp in list(beats(1, S[20][0], 17, 17, 1.0, 1.0)) + list(beats(S[20][0], NF + 30, 18, 34, 1.0, 0.25)):
    shrink = 1.0 if f < S[20][0] else 1.0 - 0.3 * min(1, (f - S[20][0]) / (NF - S[20][0]))
    for df, s in ((0, 1.0), (3, 1.0 + 0.16 * amp), (7, 1.0 - 0.06 * amp), (11, 1.0)):
        heart.scale = HS * (s * shrink); heart.keyframe_insert("scale", frame=f + df)
    keyv(hS, f, 1.0); keyv(hS, f + 3, 1.0 + 1.2 * amp)
keyv(drain, 1, 0.0); keyv(drain, S[20][0] + 8, 0.0); keyv(drain, NF, 0.8)
keyv(aoS, S[20][0] + 2, 1.0); keyv(aoS, NF, 0.3)
# tig' uchidagi nuqta (8-kadr) va qon favvorasi (18-kadr)
TIPG = glow_mat("tip_glow", (1.0, 0.15, 0.05), 6.0); tipS = TIPG.node_tree.nodes["STR"].outputs[0]
tipg = sphere("x_tipglow", 0.03, K(X_A), TIPG, seg=24)
for f, v in ((1, 0.0), (300, 0.0), (312, 6.0), (334, 4.0), (S[18][0], 6.0), (S[18][1], 8.0)):
    keyv(tipS, f, v)
BLOODX = glow_mat("blood_x", (1.0, 0.03, 0.015), 2.2, power=0.8)
bloodV = BLOODX.node_tree.nodes["STR"].outputs[0]
cav = sphere("x_cavity_blood", 1.0, K(cx0 + Vector((0.0, 0.0, -0.035))), BLOODX, scale=(0.01, 0.01, 0.01), seg=32)
cd_ = cav.modifiers.new("lumpy", "DISPLACE"); ctx = bpy.data.textures.new("cav_t", "CLOUDS"); ctx.noise_scale = 0.5
cd_.texture = ctx; cd_.strength = 0.2
for f, s in ((1, 0.01), (S[18][0] + 6, 0.01), (S[18][1], 1.0), (NF, 1.08)):
    cav.scale = (0.12 * s, 0.075 * s, 0.1 * s); cav.keyframe_insert("scale", frame=f)
rj = random.Random(77)
DROPX = mat("dropx", (0.6, 0.0, 0.0), 0.2, emit=3.0, emit_col=(1.0, 0.05, 0.02))
jets = []
for i in range(70):
    t0 = S[18][0] + rj.randint(0, 60)
    v0 = Vector((rj.uniform(-0.2, 0.25), rj.uniform(-0.45, -0.15), rj.uniform(0.0, 0.45)))
    d = sphere(f"x_jet{i}", rj.uniform(0.004, 0.008), K(X_A), DROPX, seg=10)
    for f in range(t0, t0 + 20, 2):
        tt = (f - t0) / 24.0
        d.location = X_A + v0 * tt + Vector((0, 0, -1.2 * tt * tt)); d.keyframe_insert("location", frame=f)
    jets.append((d, (t0, t0 + 18)))
W("xray", xroot, xk_e, tipg, cav)
XRAYS = rng(8, 18, 20)
for f, v in ((1, 1.0), (S[18][0], 1.0)): keyv(bloodV, f, v)

# =================================================================== 4) SHISHA STUDIYASI (tiqin taqqoslash)
GLASS = mat("bottle_glass", (0.9, 1.0, 0.94), 0.02); gb = bsdf(GLASS)
gb.inputs["Transmission Weight"].default_value = 1.0; gb.inputs["IOR"].default_value = 1.45
WINE = mat("wine", (0.7, 0.02, 0.04), 0.05, emit=0.35, emit_col=(1.0, 0.05, 0.05)); wb = bsdf(WINE)
wb.inputs["Transmission Weight"].default_value = 0.6; wb.inputs["IOR"].default_value = 1.33
CORK = cmat("cork", (0.72, 0.52, 0.32), 0.85, tex="noise", tex_scale=180, col2=(0.5, 0.33, 0.18), bump=0.6)
bprof = [(0.0, 0.0), (0.036, 0.0), (0.038, 0.004), (0.038, 0.19), (0.032, 0.22), (0.016, 0.255), (0.0135, 0.27), (0.0135, 0.31),
         (0.016, 0.312), (0.016, 0.318), (0.0118, 0.318), (0.0118, 0.272), (0.0335, 0.218), (0.0355, 0.19), (0.0355, 0.006), (0.0, 0.006)]
bottle = W("bottle", lathe("bottle", bprof, GLASS, K(BT)))
wprof = [(0.0, 0.0065), (0.0352, 0.0065), (0.0352, 0.19), (0.033, 0.215), (0.02, 0.24), (0.0116, 0.265), (0.0116, 0.285), (0.0, 0.285)]
W("bottle", lathe("wine", wprof, WINE, K(BT)))
cork = W("bottle", cyl("cork", 0.0119, 0.042, K(BT + Vector((0, 0, 0.3))), CORK, verts=32))
for f, p, rx in ((1, (0, 0, 0.3), 0), (700, (0, 0, 0.3), 0), (701, (0, 0, 0.312), 0), (712, (0.05, 0.02, 0.62), 380), (722, (0.09, 0.03, 0.85), 620)):
    cork.location = BT + Vector(p); cork.rotation_euler = (R(rx), R(rx * 0.3), 0)
    cork.keyframe_insert("location", frame=f); cork.keyframe_insert("rotation_euler", frame=f)
for fc in P.all_fcurves(cork):
    for kp in fc.keyframe_points:
        if kp.co[0] >= 701: kp.interpolation = "LINEAR"
WINED = mat("wine_drop", (0.5, 0.0, 0.02), 0.05, coat=0.8)
rb = random.Random(19); bdrops = []
for i in range(90):
    t0 = 701 + rb.randint(0, 16)
    v0 = Vector((rb.uniform(-0.35, 0.35), rb.uniform(-0.35, 0.35), rb.uniform(1.4, 2.8)))
    d = W("bottle", sphere(f"b_drop{i}", rb.uniform(0.003, 0.007), K(BT + Vector((0, 0, 0.31))), WINED, seg=10))
    for f in range(t0, t0 + 22, 2):
        tt = (f - t0) / 24.0
        d.location = BT + Vector((0, 0, 0.31)) + v0 * tt + Vector((0, 0, -4.9 * tt * tt)); d.keyframe_insert("location", frame=f)
    bdrops.append((d, (t0, 720)))
W("bottle", box("b_table", (3, 3, 0.04), K(BT + Vector((0, 0, -0.02))), mat("btable", (0.05, 0.05, 0.055), 0.25, coat=0.6)))
W("bottle", box("b_back", (3, 0.04, 2), K(BT + Vector((0, 0.8, 1.0))), mat("bback", (0.05, 0.04, 0.04), 0.8, emit=0.5, emit_col=(1.0, 0.75, 0.6))))
W("bottle", area("b_key", K(BT + Vector((-0.5, -0.5, 0.7))), (R(50), 0, R(-45)), 120, 0.6, (1.0, 0.92, 0.85)))
W("bottle", area("b_rim", K(BT + Vector((0.35, 0.45, 0.45))), (R(-65), 0, R(145)), 160, 0.4, (1.0, 0.6, 0.4)))
W("bottle", area("b_back_l", K(BT + Vector((0, 0.5, 0.2))), (R(-90), 0, 0), 90, 0.8, (1.0, 0.25, 0.2)))
BOTTLES = rng(10, 16)

# =================================================================== 5) MAKRO KESIM (1 birlik = 1 mm)
CM = dict(
    epi=cmat("m_epi", (0.88, 0.66, 0.55), 0.5, sss=0.3, tex="wave", tex_scale=0.6, col2=(0.72, 0.48, 0.38), bump=0.2),
    dermis=cmat("m_dermis", (0.82, 0.4, 0.38), 0.55, sss=0.4, tex="wave", tex_scale=0.25, col2=(0.75, 0.38, 0.4), bump=0.25),
    fat=cmat("m_fat", (0.82, 0.5, 0.14), 0.25, sss=0.5, tex="noise", tex_scale=0.4, col2=(0.7, 0.4, 0.1), bump=0.15),
    muscle=cmat("m_muscle", (0.5, 0.04, 0.04), 0.45, sss=0.4, tex="wave", tex_scale=0.5, col2=(0.45, 0.04, 0.05), bump=0.35),
    fascia=cmat("m_fascia", (0.88, 0.82, 0.78), 0.45, sss=0.2, tex="wave", tex_scale=0.8, col2=(0.75, 0.7, 0.66), bump=0.2),
    deep=cmat("m_deep", (0.5, 0.12, 0.12), 0.5, sss=0.3, tex="noise", tex_scale=0.15, col2=(0.35, 0.07, 0.08), bump=0.2),
    artery=cmat("m_artery", (0.85, 0.32, 0.32), 0.35, sss=0.4, tex="wave", tex_scale=0.4, col2=(0.7, 0.22, 0.24), bump=0.25),
    lumen=cmat("m_lumen", (0.55, 0.03, 0.04), 0.25, sss=0.3),
    cell=mat("m_rbc", (0.75, 0.02, 0.03), 0.3, coat=0.5),
    blood=mat("m_blood", (0.4, 0.0, 0.01), 0.1, coat=0.9),
)
CW, CD = 170.0, 40.0
LAYERS = [("m_epidermis", 0.0, -2.0, "epi"), ("m_dermisL", -2.0, -5.0, "dermis"), ("m_fatL", -5.0, -15.0, "fat"),
          ("m_fasciaL", -15.0, -16.2, "fascia"), ("m_muscleL", -16.2, -29.0, "muscle"), ("m_fascia2", -29.0, -30.0, "fascia"),
          ("m_deepL", -30.0, -60.0, "deep")]
ART_Z, ART_R, ART_W = -40.0, 9.0, 1.6
TIP = Vector((0.0, 0.0, -45.0)); ENTRY = Vector((-13.0, 0.0, 0.0))
DIN = (TIP - ENTRY).normalized()
MB = Matrix.Translation(MC + TIP - DIN * BL * 1000) @ look_basis(DIN).to_4x4()   # tig' asosi = teri ustida
# kesuvchi: tig' shaklidagi ariqcha + arteriya kanali
cut = prism("m_slot_cut", blade_profile(1000, 0.0015), 3.0, None); cut.matrix_world = MB
cut.hide_render = True; cut.display_type = "WIRE"
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=ART_R, radius2=ART_R, depth=CW + 4,
                                        matrix=Matrix.Translation(MC + Vector((0, 0, ART_Z))) @ Matrix.Rotation(R(90), 4, "Y"))
acut = P.mesh_obj("m_art_cut", bm); acut.hide_render = True; acut.display_type = "WIRE"
for nm, z0, z1, lk_ in LAYERS:
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((CW, CD, z0 - z1)), verts=bm.verts)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    o = P.mesh_obj(nm, bm, CM[lk_], K(MC + Vector((0, CD / 2, (z0 + z1) / 2))))
    for c_ in (cut, acut):
        bo = o.modifiers.new("cut", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = c_; bo.solver = "EXACT"
        bo.use_self = True; bo.use_hole_tolerant = True
    W("macro", o)
# arteriya: orqa yarim quvur (y >= 0), devor qalinligi ART_W; urishda kengayadi
def half_pipe(name, r0, r1, m, L=CW):
    bm = bmesh.new(); na, nx = 40, 60; rings = []
    for i in range(nx + 1):
        x = -L / 2 + L * i / nx
        ring = []
        for j in range(na + 1):
            a = math.pi * j / na
            ring.append((bm.verts.new((x, r0 * math.cos(a), r0 * math.sin(a) * 1.0)), bm.verts.new((x, r1 * math.cos(a), r1 * math.sin(a)))))
        rings.append(ring)
    # bu yerda y = cos, z = sin bo'lsa yarim quvur -y..+y bo'lib qoladi: y>=0 uchun burchakni (−90..90) qilamiz
    for ring in rings:
        for j, (vi, vo) in enumerate(ring):
            a = -math.pi / 2 + math.pi * j / na
            vi.co.y, vi.co.z = r0 * math.cos(a), r0 * math.sin(a)
            vo.co.y, vo.co.z = r1 * math.cos(a), r1 * math.sin(a)
    for i in range(nx):
        for j in range(na):
            bm.faces.new((rings[i][j][0], rings[i + 1][j][0], rings[i + 1][j + 1][0], rings[i][j + 1][0]))
            bm.faces.new((rings[i][j][1], rings[i][j + 1][1], rings[i + 1][j + 1][1], rings[i + 1][j][1]))
        for j in (0, na):
            bm.faces.new((rings[i][j][0], rings[i][j][1], rings[i + 1][j][1], rings[i + 1][j][0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = P.mesh_obj(name, bm, m); P.smooth(o); return o
art = half_pipe("m_artery", ART_R - ART_W, ART_R, CM["artery"]); art.location = K(MC + Vector((0, 0, ART_Z)))
bo = art.modifiers.new("hole", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cut; bo.solver = "EXACT"; bo.use_hole_tolerant = True
W("macro", art)
lum = half_pipe("m_lumen_back", ART_R - ART_W - 0.05, ART_R - ART_W - 0.04, CM["lumen"]); lum.location = art.location
lum.modifiers.new("hole", "BOOLEAN").object = cut; W("macro", lum)
for f, per, amp in beats(1, NF, 17, 17, 1.0, 1.0):
    for df, s in ((0, 1.0), (3, 1.06), (9, 1.0)):
        for o_ in (art, lum):
            o_.scale = (1, s, s); o_.keyframe_insert("scale", frame=f + df)
# tig' (mm): 14–15-kadrda uchi atrofida buriladi (yangi to'qimani kesadi), 17-kadrda sug'uriladi
piv = empty("m_blade_pivot", K(MC + TIP))
bl_root = make_knife("m_knife", 1000.0)
bl_root.parent = piv
bl_root.matrix_parent_inverse = Matrix.Identity(4)
bl_root.matrix_basis = Matrix.Translation(-DIN * BL * 1000) @ look_basis(DIN).to_4x4()
SWEEP = 13.0
for f, a, d in ((1, 0, 0), (560, 0, 0), (600, SWEEP * 0.55, 1.5), (660, SWEEP, 3.0), (692, SWEEP, 3.5), (PULL0, SWEEP, 3.5),
                (PULL1, SWEEP, 90), (NF, SWEEP, 200)):
    piv.rotation_euler = (0, R(-a), 0); piv.keyframe_insert("rotation_euler", frame=f)
    bl_root.location = (Matrix.Translation(-DIN * (BL * 1000 + d)) @ look_basis(DIN).to_4x4()).translation
    bl_root.keyframe_insert("location", frame=f)
for fc in P.all_fcurves(bl_root):
    for kp in fc.keyframe_points:
        if kp.co[0] >= PULL0: kp.interpolation = "BEZIER"; kp.easing = "EASE_IN"
W("macro", piv)
SW_KEYS = [(1, 0, 0), (560, 0, 0), (600, SWEEP * 0.55, 1.5), (660, SWEEP, 3.0), (692, SWEEP, 3.5)]
def _sw(f):
    for (fa_, aa, da), (fb, ab, db) in zip(SW_KEYS, SW_KEYS[1:]):
        if fa_ <= f <= fb:
            u = P.ease((f - fa_) / (fb - fa_), "inout"); return aa + (ab - aa) * u, da + (db - da) * u
    return SW_KEYS[-1][1:]
def edge_x_at(z, f):
    """f kadrda tig' qirrasining (edge) z chuqurlikdagi x qiymati (MC ga nisbatan, mm)."""
    ang, d = _sw(f)
    M = Matrix.Rotation(R(-ang), 4, "Y") @ Matrix.Translation(-DIN * (BL * 1000 + d)) @ look_basis(DIN).to_4x4()
    pr = blade_profile(1000)
    edge = [M @ Vector((x, 0, zz)) + TIP for x, zz in (pr[3], pr[4], pr[5], pr[6])]
    for a_, b_ in zip(edge, edge[1:]):
        if min(a_.z, b_.z) <= z <= max(a_.z, b_.z):
            u = (z - a_.z) / (b_.z - a_.z); return a_.x + (b_.x - a_.x) * u
    return edge[0].x
# asab tolalari (sariq) va mushak tolalari: 14–15-kadrda tig' qirrasi yetganda uziladi
NERVE_M = []
fibers = []
rf = random.Random(11)
FIB = [(-18.5, "nerve", 1.5, 612), (-21.8, "nerve", 1.7, 640), (-25.2, "nerve", 1.4, 668),
       (-17.5, "mus", 0.5, 604), (-20.0, "mus", 0.55, 626), (-23.0, "mus", 0.5, 652), (-26.5, "mus", 0.55, 676), (-28.0, "mus", 0.5, 686)]
for k_, (z, kind, r, fsnap) in enumerate(FIB):
    xc = edge_x_at(z, fsnap)
    if kind == "nerve":
        m_ = cmat(f"m_nerve{k_}", (1.0, 0.92, 0.25), 0.35, sss=0.3, tex="wave", tex_scale=1.2, col2=(0.85, 0.68, 0.25),
                  bump=0.3, emit=0.0001, emit_col=(1.0, 0.9, 0.3))
        eS = bsdf(m_).inputs["Emission Strength"]
        for f, v in ((1, 0.6), (fsnap - 1, 0.6), (fsnap, 9.0), (fsnap + 4, 2.0), (fsnap + 9, 5.0), (fsnap + 16, 0.6), (NF, 0.4)):
            keyv(eS, f, v)
        NERVE_M.append(m_)
    else:
        m_ = cmat(f"m_mfib{k_}", (0.7, 0.12, 0.1), 0.4, sss=0.3, tex="wave", tex_scale=2.0, col2=(0.5, 0.06, 0.06), bump=0.4)
    ys = 1.25 if kind == "nerve" else 0.8
    for side in (-1, 1):
        xa, xb = (-CW / 2, xc) if side < 0 else (xc, CW / 2)
        pts = [K(MC + Vector((x, ys, z + 0.25 * math.sin(x * 0.2 + k_)))) for x in np.linspace(xa, xb, 8)]
        t_ = tube(f"m_fib{k_}_{side}", pts, r, m_, res=3)
        cu = t_.data
        if side < 0:
            for f, v in ((1, 1.0), (fsnap, 1.0), (fsnap + 5, 0.93)): cu.bevel_factor_end = v; cu.keyframe_insert("bevel_factor_end", frame=f)
        else:
            for f, v in ((1, 0.0), (fsnap, 0.0), (fsnap + 5, 0.07)): cu.bevel_factor_start = v; cu.keyframe_insert("bevel_factor_start", frame=f)
        W("macro", t_)
    fibers.append((z, kind, fsnap, xc))
# uchqun (uzilish chaqnashi) sharlari
SPARK = glow_mat("spark", (1.0, 0.85, 0.4), 0.0)
for z, kind, fsnap, xc in fibers:
    if kind != "nerve": continue
    s_ = W("macro", sphere(f"m_spark{fsnap}", 2.2, K(MC + Vector((xc, -0.6, z))), SPARK, seg=16))
    sm = glow_mat(f"spark{fsnap}", (1.0, 0.8, 0.35), 0.0); s_.data.materials[0] = sm
    sv = sm.node_tree.nodes["STR"].outputs[0]
    for f, v in ((1, 0.0), (fsnap - 1, 0.0), (fsnap, 14.0), (fsnap + 6, 2.0), (fsnap + 12, 0.0)): keyv(sv, f, v)
    for f, s in ((fsnap - 1, 0.3), (fsnap + 6, 1.4), (fsnap + 12, 0.6)):
        s_.scale = (s, s, s); s_.keyframe_insert("scale", frame=f)
# qizil qon tanachalari: arteriya bo'ylab oqadi (aylanmasdan — CLAUDE.md: motion blur chizig'i bo'lmasin)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
for v in bm.verts:
    rr2 = math.hypot(v.co.x, v.co.y); v.co.z *= 0.32 * (0.55 + 0.9 * rr2 * rr2)
cell_me = bpy.data.meshes.new("rbc"); bm.to_mesh(cell_me); bm.free(); cell_me.materials.append(CM["cell"])
for p_ in cell_me.polygons: p_.use_smooth = True
rc = random.Random(4); V_ = 0.45                     # mm/kadr
F0, F1 = 330, 780
cells = []
for i in range(230):
    x1 = rc.uniform(-CW / 2 + 5, CW / 2 - 5 + V_ * (F1 - F0)); x0 = x1 - V_ * (F1 - F0)
    a = rc.uniform(-math.pi / 2 + 0.25, math.pi / 2 - 0.25); rr2 = rc.uniform(0.5, ART_R - ART_W - 1.4)
    y, z = rr2 * math.cos(a) + 0.4, rr2 * math.sin(a)
    c_ = P.link(bpy.data.objects.new(f"m_rbc{i}", cell_me)); c_.scale = (1.2, 1.2, 1.2)
    c_.rotation_euler = (rc.uniform(0, 6.3), rc.uniform(0, 6.3), rc.uniform(0, 6.3))
    for f, x in ((F0, x0), (F1, x1)):
        c_.location = K(MC + Vector((x, y, ART_Z + z))); c_.keyframe_insert("location", frame=f)
    c_.rotation_euler.x += rc.uniform(-2, 2); c_.keyframe_insert("rotation_euler", frame=F1)
    c_.rotation_euler.x -= 0; c_.keyframe_insert("rotation_euler", frame=F0)
    P.set_interp(c_, "LINEAR")
    W("macro", c_)
# 17-kadr: teshikdan qon favvorasi (tig' chiqqach)
HOLE = MC + TIP + (-DIN) * ((TIP.z - (ART_Z + ART_R)) / (-DIN.z)) * -1
HOLE = MC + Vector((TIP.x + DIN.x * ((ART_Z + ART_R - TIP.z) / DIN.z), 0, ART_Z + ART_R))
rj2 = random.Random(31); mjets = []
for i in range(260):
    t0 = PULL0 + 4 + int(rj2.random() ** 1.3 * 46)
    sp_ = rj2.uniform(5.0, 9.0) * (1.25 if t0 < PULL0 + 20 else 1.0)
    v0 = (-DIN * sp_ + Vector((rj2.uniform(-1.6, 1.6), rj2.uniform(-1.4, -0.2), rj2.uniform(-0.8, 1.2))))
    d = sphere(f"m_jet{i}", rj2.uniform(0.35, 1.0), K(HOLE), CM["blood"], seg=10)
    for f in range(t0, min(t0 + 24, S[17][1] + 2), 2):
        tt = (f - t0)
        d.location = HOLE + v0 * tt + Vector((0, 0, -0.012 * tt * tt)) + Vector((0, -0.2, 0)); d.keyframe_insert("location", frame=f)
    mjets.append((d, (t0, min(t0 + 22, S[17][1]))))
JETG = glow_mat("jet_glow", (1.0, 0.08, 0.03), 0.0); jgS = JETG.node_tree.nodes["STR"].outputs[0]
jg = W("macro", sphere("m_jet_glow", 8.0, K(HOLE + Vector((0, -1, 6))), JETG, scale=(0.8, 0.5, 1.6), seg=24))
for f, v in ((1, 0.0), (PULL0 + 3, 0.0), (PULL0 + 8, 3.0), (S[17][1], 2.0)): keyv(jgS, f, v)
W("macro", area("m_key", K(MC + Vector((-60, -110, 70))), (R(55), 0, R(-25)), 7e5, 90, (1.0, 0.95, 0.9)))
W("macro", area("m_rim", K(MC + Vector((60, 50, 40))), (R(-50), 0, R(140)), 4e5, 60, (0.6, 0.75, 1.0)))
W("macro", area("m_low", K(MC + Vector((40, -80, -70))), (R(120), 0, R(25)), 1.5e5, 60, (1.0, 0.7, 0.6)))
MACROS = rng(9, 11, 14, 15, 17)

# =================================================================== ko'rinish (har dunyo faqat o'z kadrlarida)
RANGES = dict(room=ROOMS, street=STREETS, xray=XRAYS, bottle=BOTTLES, macro=MACROS)
seen = set()
for wname, objs in WORLD_OBJS.items():
    for o in objs:
        if o.name in seen: continue
        seen.add(o.name); vis(o, RANGES[wname])
# bolalarga alohida vis — otadan keyin (CLAUDE.md)
vis_only(lk, [(a, min(b, YANK)) for a, b in STREETS if a <= YANK])
vis_only(lk2_e, [(max(a, YANK + 1), b) for a, b in STREETS if b > YANK])
vis_only(mk_e, rng(7, 12, 13))
vis_only(fk, rng(19)); vis_only(pool_r, rng(19))
vis_only(xk_e, rng(8))
vis_only(tipg, rng(8, 18)); vis_only(cav, rng(18, 20))
for d, (a, b) in jets: vis_only(d, [(a, min(b, S[18][1]))])
for d, (a, b) in bdrops: vis_only(d, [(a, b)])
for d, rg2 in mjets: vis_only(d, [rg2])
vis_only(jg, rng(17))
for o in bpy.data.objects:
    if o.name.startswith("m_spark"): vis_only(o, rng(14, 15))
for o in bpy.data.objects:
    if o.name.startswith("m_rbc"): vis_only(o, rng(9, 11, 14, 15, 17))
# bosh suyagi (head) kuzatuvchi bo'sh ob'ektlar
def head_e(name, arm, off=(0, 0.05, 0.06)):
    return bone_child(name, arm, "Head", Matrix.Translation(off))
lhead = head_e("leo_head_t", leo); mhead = head_e("meg_head_t", meg)
lgrip = empty("leo_grip_t", (-0.006, 0, 0.05)); lgrip.parent = lk
mgrip = empty("meg_grip_t", (-0.006, 0, 0.04)); mgrip.parent = mk

# =================================================================== OSMON / DUNYO
w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
nt = w.node_tree; N = nt.nodes; L = nt.links
e = N.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs[0].default_value = 1.0
L.new(e.outputs[0], tint.inputs[6])
mixS = N.new("ShaderNodeMix"); mixS.data_type = "RGBA"; L.new(tint.outputs[2], mixS.inputs[6])
bg = N["Background"]; L.new(mixS.outputs[2], bg.inputs[0])
WT = {}
for s_ in (1, 2, 3, 4, 5, 6): WT[s_] = (0, (0, 0, 0), 0.35, (1.0, 0.55, 0.35))
for s_ in (7, 12, 13): WT[s_] = (0, (0, 0, 0), 0.6, (1, 1, 1))
WT[19] = (0, (0, 0, 0), 0.08, (0.4, 0.5, 1.0))
for s_ in (8, 18, 20): WT[s_] = (1, (0.003, 0.006, 0.015), 1.0, (1, 1, 1))
for s_ in (9, 11, 14, 15, 17): WT[s_] = (1, (0.012, 0.004, 0.004), 1.0, (1, 1, 1))
for s_ in (10, 16): WT[s_] = (1, (0.01, 0.01, 0.012), 1.0, (1, 1, 1))
for s_, (so, col, stg, tc_) in WT.items():
    f = S[s_][0]
    keyv(mixS.inputs[0], f, so); keyv(mixS.inputs[7], f, (*col, 1)); keyv(bg.inputs[1], f, stg); keyv(tint.inputs[7], f, (*tc_, 1))
all_const(nt)

# =================================================================== KAMERALAR
cams = {}
def C(n, lens, fstop=None, focus=None):
    c, t = camera(f"cam{n:02d}", lens, fstop, focus); cams[n] = c
    if n in (9, 11, 14, 15, 17): c.data.clip_start = 0.5
    return c, t
def orbit(c, t, f0, f1, center, r0, r1, a0, a1, z0, z1, kind="inout", tgt=None, shake=None):
    rnd = random.Random(f0)
    for f in range(f0, f1 + 1):
        u = P.ease((f - f0) / max(1, f1 - f0), kind); a = R(a0 + (a1 - a0) * u); rd = r0 + (r1 - r0) * u
        p = Vector(center) + Vector((rd * math.sin(a), -rd * math.cos(a), z0 + (z1 - z0) * u))
        for sa, sb, amp in (shake or []):
            if sa <= f <= sb:
                k = amp * (1 - (f - sa) / max(1, sb - sa + 1)) ** 1.5
                p += Vector((rnd.uniform(-k, k), rnd.uniform(-k, k), rnd.uniform(-k, k)))
        c.location = p; c.keyframe_insert("location", frame=f)
        t.location = tgt if tgt is not None else Vector(center) + Vector((0, 0, z0 + (z1 - z0) * u)); t.keyframe_insert("location", frame=f)
def follow(c, obj): c.constraints["Track To"].target = obj
V = lambda base, *xyz: K(base + Vector(xyz))
# --- kino ko'chasi ---
c, t = C(1, 16, 2.8)
cam_move(c, t, *S[1], V(ST, -1.0, -3.4, 0.12), V(ST, -0.55, -1.75, 0.3), V(ST, 0, 0, 1.15), V(ST, 0.02, 0, 1.1), "out")
c, t = C(2, 55, 2.0, focus=lgrip); follow(c, lgrip)
cam_move(c, t, *S[2], V(ST, 0.75, -0.7, 1.12), V(ST, 0.42, -0.62, 1.0), (0, 0, 0), (0, 0, 0), "inout", tgt_obj_follow=True)
c, t = C(3, 35, 2.0, focus=lhead); follow(c, lhead)
cam_move(c, t, *S[3], V(ST, 0.22, -0.78, 1.22), V(ST, 0.12, -0.6, 1.28), (0, 0, 0), (0, 0, 0), "inout",
         shake=[(72, 95, 0.012)], tgt_obj_follow=True)
c, t = C(4, 18, 3.2)
cam_move(c, t, *S[4], V(ST, 0.95, -1.75, 0.22), V(ST, 0.7, -1.3, 0.32), V(ST, 0, 0, 1.25), V(ST, -0.1, 0, 1.3), "inout",
         shake=[(YANK, YANK + 12, 0.05)])
c, t = C(5, 28, 3.5)
cam_move(c, t, *S[5], V(ST, -1.7, -0.9, 1.0), V(ST, -1.5, -1.9, 0.55), V(ST, 0, -0.2, 0.95), V(ST, 0, -0.55, 0.5), "inout",
         shake=[(170, 183, 0.03)])
c, t = C(6, 22, 4.0)
cam_move(c, t, *S[6], V(ST, 0.7, -2.6, 0.25), V(ST, 0.15, -1.6, 3.4), V(ST, 0, -0.8, 0.35), V(ST, 0, -1.05, 0.0), "inout",
         shake=[(195, 206, 0.04)])
# --- mehmonxona ---
c, t = C(7, 42, 2.0)
cam_move(c, t, *S[7], (-0.25, -0.95, 1.5), (0.32, -0.62, 1.08), K(M_entry + Vector((-0.12, 0, 0.38))), K(M_entry), "inout")
c, t = C(12, 50, 2.0, focus=mgrip); follow(c, mgrip)
cam_move(c, t, *S[12], (0.62, -0.62, 1.2), (0.4, -0.5, 1.08), (0, 0, 0), (0, 0, 0), "out", tgt_obj_follow=True)
c, t = C(13, 16, 4.0)
cam_move(c, t, *S[13], (0.7, -1.2, 0.2), (0.5, -0.92, 0.28), (0.0, 0.0, 1.2), (0.05, 0, 1.15), "inout", shake=[(530, 555, 0.012)])
c, t = C(19, 22, 4.0)
orbit(c, t, *S[19], (0.35, -0.15, 0.0), 0.25, 0.15, -20, 35, 2.6, 2.1, "inout", tgt=Vector((0.35, -0.15, 0.1)))
# --- rentgen ---
xc_ = cx0 + Vector((0, 0, 0.03))
c, t = C(8, 30, 5.6)
orbit(c, t, *S[8], xc_ - Vector((0, 0, xc_.z)), 0.95, 0.62, -45, 15, xc_.z + 0.15, xc_.z + 0.02, "inout", tgt=X_A + Vector((0.03, 0, 0.02)))
c, t = C(18, 26, 5.6)
orbit(c, t, *S[18], xc_ - Vector((0, 0, xc_.z)), 0.75, 1.05, 30, 120, xc_.z - 0.1, xc_.z + 0.35, "inout", tgt=xc_,
      shake=[(772, 790, 0.02)])
c, t = C(20, 45, 8.0)
cam_move(c, t, *S[20], K(heart_p + Vector((0.25, -0.85, 0.15))), K(heart_p + Vector((0.06, -0.3, 0.04))), K(heart_p), K(heart_p), "out")
# --- shisha ---
c, t = C(10, 50, 2.8)
orbit(c, t, *S[10], K(BT), 0.75, 0.6, -60, 25, 0.32, 0.24, "inout", tgt=BT + Vector((0, 0, 0.24)))
c, t = C(16, 24, 3.2)
cam_move(c, t, *S[16], V(BT, 0.34, -0.5, 0.08), V(BT, 0.22, -0.4, 0.12), V(BT, 0, 0, 0.26), V(BT, 0.02, 0, 0.36), "out",
         shake=[(701, 715, 0.01)], lens=(20, 30, "out"))
# --- makro ---
c, t = C(9, 22, 6.0)
cam_move(c, t, *S[9], V(MC, -40, -120, 45), V(MC, -14, -55, -28), V(MC, -8, 0, -12), V(MC, -2, 0, -36), "in")
c, t = C(11, 30, 6.0)
cam_move(c, t, *S[11], V(MC, -38, -62, -8), V(MC, 8, -48, -44), V(MC, -9, 0, -10), V(MC, -1, 0, -40), "inout")
c, t = C(14, 26, 6.0)
cam_move(c, t, *S[14], V(MC, -45, -70, -10), V(MC, -24, -58, -18), V(MC, -5, 0, -24), V(MC, -4, 0, -21), "inout")
c, t = C(15, 34, 6.0)
cam_move(c, t, *S[15], V(MC, -16, -34, -12), V(MC, -6, -27, -26), V(MC, -5, 0, -19), V(MC, -4, 0, -24), "inout",
         shake=[(640, 652, 0.6), (668, 680, 0.6)])
c, t = C(17, 22, 6.0)
cam_move(c, t, *S[17], K(HOLE + Vector((22, -70, -18))), K(HOLE + Vector((8, -42, -6))), K(HOLE), K(HOLE + Vector((-4, 0, 12))), "out",
         shake=[(PULL0, PULL0 + 22, 2.0)])
for n, c in cams.items():
    sc.timeline_markers.new(c.name, frame=S[n][0]).camera = c
sc.camera = cams[1]

# =================================================================== RENDER
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 24
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = "START"
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 40))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True
r.use_overwrite = False; r.use_placeholder = True

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; r.use_overwrite = True
            bpy.ops.render.render(write_still=True)
    else:
        a, b = map(int, os.environ.get("RANGE", f"1,{NF}").split(","))
        sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
