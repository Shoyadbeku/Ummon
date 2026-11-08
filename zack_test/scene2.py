# Zack D. Films uslubidagi 10 soniyalik test (v2, realistik odamlar):
# qiz onasi bilan janjallashadi, uydan chiqib ketadi va mashinada ketadi. Ovozsiz, subtitrsiz.
import bpy, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import char
from mathutils import Vector

R = math.radians
OUT = os.environ.get("OUT", "/tmp/zack_frames/")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, 240, 24

# ---------------- yordamchilar ----------------
def mat(name, col, rough=0.5, metal=0.0, emit=0.0, coat=0.0, tex=None, tex_scale=10, col2=None, bump=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    if tex:
        t = N.new({"noise": "ShaderNodeTexNoise", "wave": "ShaderNodeTexWave", "brick": "ShaderNodeTexBrick", "voronoi": "ShaderNodeTexVoronoi"}[tex])
        tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], t.inputs["Vector"])
        t.inputs["Scale"].default_value = tex_scale
        if tex == "wave": t.inputs["Distortion"].default_value = 6; t.inputs["Detail"].default_value = 4
        if tex == "brick":
            t.inputs["Color1"].default_value = (*col, 1); t.inputs["Color2"].default_value = (*(col2 or col), 1)
            t.inputs["Mortar"].default_value = (*[c*0.7 for c in col], 1); t.inputs["Mortar Size"].default_value = 0.01
            L.new(t.outputs["Color"], b.inputs["Base Color"])
        else:
            mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
            out = t.outputs["Fac"] if "Fac" in t.outputs else t.outputs["Distance"]
            L.new(out, mx.inputs["Factor"]); mx.inputs[6].default_value = (*col, 1)
            mx.inputs[7].default_value = (*(col2 or [c*0.75 for c in col]), 1)
            L.new(mx.outputs[2], b.inputs["Base Color"])
            if bump:
                bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
                L.new(out, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(name, size, loc, m, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=[R(a) for a in rot]); o = bpy.context.object
    o.name = name; o.scale = [s/2 for s in size]; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3; smooth(o)
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o

def cyl(name, r, depth, loc, m, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=[R(a) for a in rot])
    o = bpy.context.object; o.name = name; o.data.materials.append(m); smooth(o)
    b = o.modifiers.new("bev", "BEVEL"); b.width = min(0.02, r*0.2); b.segments = 3; b.limit_method = "ANGLE"
    o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o

def sphere(name, r, loc, m, scale=(1, 1, 1), sub=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m); smooth(o); return o

def prism(name, pts, width, m, loc=(0, 0, 0), axis="y", bevel=0.03):
    """XZ profilini Y bo'ylab cho'zish (mashina kuzovi, tom)."""
    me = bpy.data.meshes.new(name); n = len(pts); verts = []
    for s in (-width/2, width/2):
        for x, z in pts: verts.append((x, s, z))
    faces = [list(range(n))[::-1], list(range(n, 2*n))]
    for i in range(n):
        j = (i+1) % n; faces.append([i, j, n+j, n+i])
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc
    me.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 4; b.limit_method = "ANGLE"; smooth(o)
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o

def key(o, f, loc=None, rot=None, interp=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = [R(a) for a in rot]; o.keyframe_insert("rotation_euler", frame=f)

def vis(o, ranges):
    """o faqat berilgan kadr oraliqlarida render qilinadi."""
    objs = [o] + list(o.children_recursive)
    marks = sorted({1} | {a for a, b in ranges} | {b+1 for a, b in ranges})
    for f in marks:
        on = any(a <= f <= b for a, b in ranges)
        for x in objs:
            x.hide_render = not on; x.keyframe_insert("hide_render", frame=f)

def pose(arm, f, **bones):
    for bn, rot in bones.items():
        pb = arm.pose.bones[bn.replace("_", ".")]; pb.rotation_mode = "XYZ"
        pb.rotation_euler = [R(a) for a in rot]; pb.keyframe_insert("rotation_euler", frame=f)

def all_fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "layers") and act.layers:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return list(act.fcurves)

def set_interp(idb, mode="BEZIER", path=None, easing=None):
    for fc in all_fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for k in fc.keyframe_points:
            k.interpolation = mode
            if easing: k.easing = easing

# ---------------- materiallar ----------------
M = dict(
    wallpaint = mat("wallpaint", (0.78, 0.72, 0.62), 0.85, tex="noise", tex_scale=40, bump=0.02),
    wood      = mat("wood", (0.42, 0.25, 0.13), 0.35, tex="wave", tex_scale=3, col2=(0.25, 0.13, 0.06), coat=0.3),
    trim      = mat("trim", (0.92, 0.92, 0.9), 0.4),
    sofa      = mat("sofa", (0.22, 0.3, 0.38), 0.9, tex="noise", tex_scale=200, bump=0.1),
    rug       = mat("rug", (0.55, 0.18, 0.12), 0.95, tex="voronoi", tex_scale=12, col2=(0.75, 0.6, 0.4)),
    darkwood  = mat("darkwood", (0.15, 0.08, 0.04), 0.4, tex="wave", tex_scale=6, coat=0.4),
    glass     = mat("glass", (0.02, 0.025, 0.03), 0.02, coat=1.0),
    winlight  = mat("winlight", (1.0, 0.95, 0.85), 0.5, emit=6.0),
    lampshade = mat("lampshade", (1.0, 0.85, 0.6), 0.6, emit=3.0),
    plant     = mat("plant", (0.12, 0.35, 0.1), 0.6, tex="noise", tex_scale=30, bump=0.3),
    pot       = mat("pot", (0.7, 0.35, 0.2), 0.6),
    frame     = mat("frame", (0.05, 0.05, 0.05), 0.4),
    art       = mat("art", (0.2, 0.45, 0.6), 0.5, tex="wave", tex_scale=2, col2=(0.9, 0.7, 0.3)),
    curtain   = mat("curtain", (0.85, 0.82, 0.72), 0.9, tex="wave", tex_scale=8, bump=0.2),
    siding    = mat("siding", (0.82, 0.83, 0.8), 0.7, tex="wave", tex_scale=1.2, col2=(0.7, 0.71, 0.68), bump=0.2),
    roof      = mat("roof", (0.18, 0.18, 0.2), 0.8, tex="brick", tex_scale=6, col2=(0.12, 0.12, 0.14)),
    door      = mat("door", (0.35, 0.08, 0.06), 0.35, coat=0.5),
    brass     = mat("brass", (0.85, 0.65, 0.3), 0.25, metal=1.0),
    concrete  = mat("concrete", (0.55, 0.54, 0.5), 0.85, tex="brick", tex_scale=0.6, col2=(0.5, 0.49, 0.46)),
    asphalt   = mat("asphalt", (0.07, 0.07, 0.075), 0.9, tex="noise", tex_scale=300, col2=(0.12, 0.12, 0.12), bump=0.3),
    paint     = mat("lines", (0.9, 0.9, 0.85), 0.6),
    grass     = mat("grass", (0.14, 0.3, 0.07), 0.9, tex="noise", tex_scale=80, col2=(0.22, 0.38, 0.1), bump=0.5),
    leaves    = mat("leaves", (0.12, 0.28, 0.08), 0.7, tex="voronoi", tex_scale=20, col2=(0.2, 0.4, 0.1), bump=0.5),
    bark      = mat("bark", (0.2, 0.13, 0.08), 0.9, tex="noise", tex_scale=30, bump=0.5),
    carpaint  = mat("carpaint", (0.03, 0.08, 0.22), 0.25, metal=0.6, coat=1.0),
    chrome    = mat("chrome", (0.9, 0.9, 0.9), 0.1, metal=1.0),
    tire      = mat("tire", (0.02, 0.02, 0.02), 0.8),
    carglass  = mat("carglass", (0.01, 0.012, 0.015), 0.02, coat=1.0),
    headlight = mat("headlight", (1.0, 0.97, 0.9), 0.1, emit=3.0),
    taillight = mat("taillight", (0.8, 0.02, 0.02), 0.2, emit=2.0),
    black     = mat("black", (0.02, 0.02, 0.02), 0.5),
)

# ================= UY ICHI =================
# xona: x [-3,3], y [0,5], fasad y=0 (eshik x=0)
box("floor", (6, 5, 0.06), (0, 2.5, -0.03), M["wood"])
box("ceiling", (6, 5, 0.06), (0, 2.5, 2.73), M["trim"])
box("wall_back_l", (2.2, 0.12, 2.7), (-1.9, 5.0, 1.35), M["wallpaint"])
box("wall_back_r", (2.2, 0.12, 2.7), (1.9, 5.0, 1.35), M["wallpaint"])
box("wall_back_b", (1.6, 0.12, 0.85), (0, 5.0, 0.425), M["wallpaint"])
box("wall_back_t", (1.6, 0.12, 0.45), (0, 5.0, 2.475), M["wallpaint"])
box("window_glow", (1.8, 0.02, 1.6), (0, 5.4, 1.6), M["winlight"])
for x in (-0.78, 0.78): box("wframe", (0.06, 0.16, 1.4), (x, 5.0, 1.55), M["trim"])
box("wframe_m", (1.6, 0.16, 0.06), (0, 5.0, 1.55), M["trim"])
for x in (-1.1, 1.1):
    c = box("curtain", (0.5, 0.06, 2.3), (x, 4.88, 1.4), M["curtain"])
    d = c.modifiers.new("wave", "WAVE"); d.height = 0.04; d.width = 0.15; d.narrowness = 1; d.use_y = False
    d.time_offset = 0; d.speed = 0
box("wall_left", (0.12, 5, 2.7), (-3.0, 2.5, 1.35), M["wallpaint"])
box("wall_right", (0.12, 5, 2.7), (3.0, 2.5, 1.35), M["wallpaint"])
for x, w in ((-1.75, 2.5), (1.75, 2.5)):
    box("wall_front", (w, 0.2, 2.7), (x, 0.0, 1.35), M["wallpaint"])
box("wall_front_t", (1.0, 0.2, 0.55), (0, 0.0, 2.425), M["wallpaint"])
for x, y, l, a in ((0, 4.93, 6, 0), (-2.93, 2.5, 5, 90), (2.93, 2.5, 5, 90)):
    box("baseboard", (l, 0.03, 0.12), (x, y, 0.06), M["trim"], rot=(0, 0, a))
# eshik (ichkariga-tashqariga ochiladi)
hinge = empty("door_hinge", (-0.47, 0.0, 0))
dr = box("door", (0.92, 0.05, 2.12), (0.46, 0, 1.06), M["door"], 0.01); dr.parent = hinge
knob = sphere("knob", 0.03, (0.82, -0.05, 1.0), M["brass"]); knob.parent = hinge
knob2 = sphere("knob2", 0.03, (0.82, 0.05, 1.0), M["brass"]); knob2.parent = hinge
for x in (-0.53, 0.53): box("dframe", (0.08, 0.26, 2.2), (x, 0, 1.1), M["trim"])
box("dframe_t", (1.14, 0.26, 0.08), (0, 0, 2.18), M["trim"])
key(hinge, 1, rot=(0, 0, 0)); key(hinge, 103, rot=(0, 0, 0)); key(hinge, 110, rot=(0, 0, -100))
key(hinge, 128, rot=(0, 0, -100)); key(hinge, 136, rot=(0, 0, 0))
# mebel
box("sofa_seat", (2.2, 0.9, 0.42), (-0.2, 4.3, 0.21), M["sofa"], 0.06)
box("sofa_back", (2.2, 0.22, 0.55), (-0.2, 4.72, 0.68), M["sofa"], 0.08)
for x in (-1.25, 0.85): box("sofa_arm", (0.22, 0.9, 0.6), (x, 4.3, 0.3), M["sofa"], 0.08)
for i, x in enumerate((-0.75, 0.35)):
    box("cushion", (1.0, 0.75, 0.16), (x, 4.25, 0.5), M["sofa"], 0.07)
box("rug", (2.8, 1.9, 0.01), (-0.1, 2.9, 0.005), M["rug"])
box("table", (1.1, 0.6, 0.05), (-0.2, 3.3, 0.42), M["darkwood"], 0.01)
for dx in (-0.48, 0.48):
    for dy in (-0.24, 0.24): box("tleg", (0.04, 0.04, 0.4), (-0.2+dx, 3.3+dy, 0.2), M["darkwood"])
cyl("mug", 0.04, 0.1, (-0.4, 3.3, 0.5), M["trim"])
# lampa
cyl("lamp_base", 0.12, 0.03, (2.4, 4.4, 0.015), M["brass"])
cyl("lamp_pole", 0.015, 1.5, (2.4, 4.4, 0.75), M["brass"])
cyl("lamp_shade", 0.22, 0.32, (2.4, 4.4, 1.55), M["lampshade"])
# o'simlik
cyl("pot", 0.18, 0.35, (-2.5, 4.5, 0.175), M["pot"])
for i, (dx, dy, dz, s) in enumerate(((0, 0, 0.6, 0.28), (0.12, 0.05, 0.85, 0.2), (-0.1, -0.05, 0.8, 0.22), (0.02, 0.1, 1.05, 0.16))):
    o = sphere("leaf", s, (-2.5+dx, 4.5+dy, dz), M["plant"], sub=2)
    dm = o.modifiers.new("disp", "DISPLACE"); dm.strength = 0.08; dm.texture = bpy.data.textures.new("lt", "CLOUDS")
# rasmlar
for x, z, w, h in ((-2.0, 1.6, 0.6, 0.8), (2.0, 1.7, 0.5, 0.5)):
    box("pframe", (w+0.06, 0.03, h+0.06), (x, 4.92, z), M["frame"])
    box("pic", (w, 0.035, h), (x, 4.915, z), M["art"])
box("shelf", (0.08, 1.4, 0.03), (-2.92, 2.0, 1.5), M["darkwood"])
for i in range(6):
    box("book", (0.16, 0.05, 0.22 + 0.03*(i % 3)), (-2.86, 1.5 + i*0.08, 1.63), mat(f"book{i}", [(0.6, 0.1, 0.1), (0.1, 0.3, 0.5), (0.8, 0.7, 0.3)][i % 3], 0.6))

# ================= TASHQARI =================
# fasad (tashqi tomoni y<0): siding qoplama, tom, zinapoya
box("facade_l", (5.47, 0.1, 3.0), (-3.265, -0.16, 1.5), M["siding"])
box("facade_r", (5.47, 0.1, 3.0), (3.265, -0.16, 1.5), M["siding"])
box("facade_top", (1.06, 0.1, 0.8), (0, -0.16, 2.6), M["siding"])
prism("roof", [(-6.5, 3.0), (6.5, 3.0), (0, 4.6)], 6.2, M["roof"], loc=(0, 2.4, 0), bevel=0)
bpy.data.objects["roof"].rotation_euler = (0, 0, 0)
roof = bpy.data.objects["roof"]
# tom: profil XZ, Y bo'ylab => uy uzunligi bo'ylab chiziq
for x in (-2.6, 2.6):  # derazalar
    box("win_out", (1.2, 0.04, 1.2), (x, -0.22, 1.6), M["winlight"])
    box("win_frame", (1.34, 0.08, 1.34), (x, -0.2, 1.6), M["trim"])
    box("win_glass", (1.2, 0.02, 1.2), (x, -0.25, 1.6), M["glass"])
    box("shutter", (0.3, 0.05, 1.34), (x-0.85, -0.22, 1.6), M["darkwood"])
    box("shutter", (0.3, 0.05, 1.34), (x+0.85, -0.22, 1.6), M["darkwood"])
box("step1", (1.6, 0.6, 0.1), (0, -0.5, 0.05), M["concrete"], 0.01)
box("porch_light", (0.12, 0.12, 0.2), (0.75, -0.25, 2.1), M["lampshade"])
box("lawn", (60, 3.2, 0.1), (0, -1.6, -0.06), M["grass"])
box("path", (1.4, 2.8, 0.03), (0, -2.2, 0.0), M["concrete"])
box("sidewalk", (60, 1.6, 0.14), (0, -3.6, 0.0), M["concrete"])
box("curb", (60, 0.15, 0.18), (0, -4.42, 0.0), M["concrete"], 0.02)
box("road", (80, 8, 0.1), (0, -8.5, -0.07), M["asphalt"])
for x in range(-40, 41, 6): box("line", (3, 0.15, 0.02), (x, -8.5, -0.015), M["paint"])
box("lawn_far", (80, 10, 0.1), (0, -18, -0.06), M["grass"])
box("ground", (400, 400, 0.1), (0, 0, -0.2), M["grass"])
# qarshi tomondagi uylar
for i, x in enumerate(range(-20, 21, 9)):
    col = [(0.75, 0.68, 0.55), (0.6, 0.7, 0.75), (0.85, 0.85, 0.82), (0.7, 0.55, 0.45), (0.65, 0.7, 0.6)][i % 5]
    box(f"house{i}", (6, 6, 3.4), (x, -17, 1.7), mat(f"hs{i}", col, 0.8, tex="wave", tex_scale=1.2, bump=0.2))
    prism(f"hroof{i}", [(-3.4, 0), (3.4, 0), (0, 1.8)], 6.4, M["roof"], loc=(x, -17, 3.4), bevel=0)
    for dx in (-1.6, 1.6): box("hw", (1.0, 0.05, 1.0), (x+dx, -13.97, 1.8), M["glass"])
# daraxtlar
def tree(x, y, s=1.0):
    cyl("trunk", 0.12*s, 2.2*s, (x, y, 1.1*s), M["bark"], verts=16)
    for dx, dy, dz, r in ((0, 0, 2.8, 1.2), (0.6, 0.2, 2.4, 0.8), (-0.5, -0.3, 2.5, 0.9), (0.1, 0.4, 3.4, 0.8)):
        o = sphere("crown", r*s, (x+dx*s, y+dy*s, dz*s), M["leaves"], sub=3)
        dm = o.modifiers.new("d", "DISPLACE"); dm.strength = 0.35*s
        t = bpy.data.textures.new("cl", "CLOUDS"); t.noise_scale = 0.4; dm.texture = t
for x in (-7, 6.5, 14, -15): tree(x, -2.2, 1.0)
for x in (-11, 3, 17): tree(x, -13, 1.2)

# ================= MASHINA =================
CAR0 = Vector((0.5, -5.35, 0))
car = empty("car", CAR0)
body = prism("car_body", [(-2.2, 0.3), (2.15, 0.3), (2.3, 0.5), (2.28, 0.75), (2.0, 0.86), (1.1, 0.93), (-1.75, 0.96),
                          (-2.22, 0.88), (-2.3, 0.6)], 1.8, M["carpaint"], bevel=0.07)
body.parent = car
for x in (-1.4, 1.45):  # g'ildirak uyalari
    cut = cyl("arch_cut", 0.4, 2.2, (x, 0, 0.33), M["black"], rot=(90, 0, 0)); cut.modifiers.clear()
    b = body.modifiers.new("arch", "BOOLEAN"); b.object = cut; b.operation = "DIFFERENCE"; b.solver = "EXACT"
    cut.hide_render = True; cut.hide_viewport = True; cut.parent = car
body.modifiers.move(len(body.modifiers)-1, 0); body.modifiers.move(len(body.modifiers)-1, 0)
cab = prism("car_cabin", [(1.1, 0.92), (0.35, 1.36), (-1.15, 1.38), (-1.8, 0.95)], 1.52, M["carglass"], bevel=0.05)
cab.parent = car
rf = prism("car_roof", [(0.3, 1.355), (-1.12, 1.375), (-1.1, 1.42), (0.28, 1.4)], 1.5, M["carpaint"], bevel=0.02); rf.parent = car
for x, w in ((-0.38, 0.09), (-1.05, 0.12)):   # ustunlar
    p = box("pillar", (w, 1.54, 0.38), (x, 0, 1.13), M["carpaint"], 0.02); p.parent = car
for x in (-1.4, 1.45):
    for y in (-0.82, 0.82):
        t = cyl("tire", 0.34, 0.24, (x, y, 0.34), M["tire"], rot=(90, 0, 0)); t.parent = car
        rim = cyl("rim", 0.22, 0.25, (x, y, 0.34), M["chrome"], rot=(90, 0, 0)); rim.parent = car
        hub = cyl("hub", 0.06, 0.26, (x, y, 0.34), M["black"], rot=(90, 0, 0)); hub.parent = car
for y in (-0.6, 0.6):
    h = box("headlight", (0.06, 0.38, 0.1), (2.25, y, 0.72), M["headlight"], 0.02); h.parent = car
    t = box("taillight", (0.06, 0.4, 0.1), (-2.28, y, 0.78), M["taillight"], 0.02); t.parent = car
g = box("grille", (0.05, 0.8, 0.14), (2.29, 0, 0.55), M["black"], 0.02); g.parent = car
for y in (-0.95, 0.95):
    mr = box("mirror", (0.18, 0.1, 0.1), (0.95, y, 1.0), M["carpaint"], 0.03); mr.parent = car
bump = box("bumper_r", (0.08, 1.7, 0.18), (-2.3, 0, 0.42), M["black"], 0.03); bump.parent = car
# ochiladigan eshik (uy tomonda, +Y)
dh = empty("cardoor_hinge", (0.9, 0.915, 0), car)
cd = box("car_door", (1.25, 0.05, 0.6), (-0.62, 0, 0.62), M["carpaint"], 0.02); cd.parent = dh
cw = box("car_door_win", (1.05, 0.04, 0.4), (-0.6, 0, 1.12), M["carglass"], 0.02); cw.parent = dh
hd = box("car_door_handle", (0.15, 0.03, 0.03), (-1.0, 0.03, 0.82), M["chrome"]); hd.parent = dh
key(dh, 1, rot=(0, 0, 0)); key(dh, 160, rot=(0, 0, 0)); key(dh, 168, rot=(0, 0, 65))
key(dh, 176, rot=(0, 0, 65)); key(dh, 183, rot=(0, 0, 0))
# haydab ketish
key(car, 1, loc=tuple(CAR0)); key(car, 190, loc=tuple(CAR0)); key(car, 240, loc=tuple(CAR0 + Vector((24, 0, 0))))
set_interp(car, "QUAD", "location", "EASE_IN")

# ================= QAHRAMONLAR =================
GIRL = dict(skin=(0.78, 0.55, 0.43), lip=(0.62, 0.28, 0.28), brow=(0.07, 0.04, 0.02), c1=(0.72, 0.1, 0.16),
            c2=(0.1, 0.15, 0.28), shoe=(0.9, 0.9, 0.88), hair=(0.1, 0.05, 0.025), iris=(0.22, 0.12, 0.05))
MOM = dict(skin=(0.74, 0.52, 0.4), lip=(0.55, 0.25, 0.25), brow=(0.05, 0.03, 0.02), c1=(0.35, 0.45, 0.32),
           c2=(0.18, 0.16, 0.15), shoe=(0.12, 0.08, 0.05), hair=(0.06, 0.035, 0.02), iris=(0.15, 0.09, 0.04))
girl = char.make_human("girl", GIRL, hair="ponytail", widen=1.0, height=0.97, sleeves="short")
mom = char.make_human("mom", MOM, hair="bun", widen=1.07, height=1.03, sleeves="long")

ARMS_DOWN = dict(uarm_L=(0, 0, -17), uarm_R=(0, 0, 17), farm_L=(8, 0, 0), farm_R=(8, 0, 0))

# ---- ONA: ichkarida, qizga qarab (+X), barmoq bilan ko'rsatib baqiradi
mom.location = (-0.75, 2.65, 0); mom.rotation_euler = (0, 0, R(90))
for f in range(1, 241, 8):
    up = (f // 8) % 2 == 0
    pose(mom, f, uarm_R=(78 if up else 62, 0, 12), farm_R=(15 if up else 30, 0, 0),
         uarm_L=(10, 0, -20), farm_L=(85, 0, -30), hand_L=(0, 0, 0),
         head=(8 if up else -4, 6 if up else -6, 0), spine=(6 if up else 3, 0, 0), chest=(4, 0, 0))

# ---- QIZ
G = girl
G.location = (0.55, 2.55, 0); G.rotation_euler = (0, 0, R(-90))
key(G, 1, loc=(0.55, 2.55, 0), rot=(0, 0, -90))
# janjal imo-ishoralari (1-84)
for f in range(1, 85, 10):
    a = (f // 10) % 2 == 0
    pose(G, f, uarm_L=(25 if a else 10, 0, -10), uarm_R=(25 if not a else 10, 0, 10),
         farm_L=(70 if a else 35, 0, 0), farm_R=(70 if not a else 35, 0, 0),
         head=(-6, 0, 0), spine=(-4 if a else -2, 0, 0), thigh_L=(0, 0, 0), thigh_R=(0, 0, 0),
         shin_L=(0, 0, 0), shin_R=(0, 0, 0), hips=(0, 0, 0))
# bosh chayqash (62-84)
for i, f in enumerate(range(62, 85, 5)):
    pose(G, f, head=(-4, 22 if i % 2 else -22, 0))
pose(G, 86, head=(0, 0, 0), **ARMS_DOWN)
# keskin o'girilish (86-98)
key(G, 86, rot=(0, 0, -90)); key(G, 98, rot=(0, 0, -15))
key(G, 98, loc=(0.55, 2.55, 0))

def walk(arm, f0, f1, p0, p1, cycle=18, heading=0.0):
    """Ildiz harakati + oyoq/qo'l sikli."""
    key(arm, f0, loc=p0, rot=(0, 0, heading)); key(arm, f1, loc=p1, rot=(0, 0, heading))
    for fc in all_fcurves(arm):
        if fc.data_path == "location":
            for k in fc.keyframe_points:
                if f0 <= k.co.x <= f1: k.interpolation = "LINEAR"
    f = f0
    while f <= f1:
        ph = ((f - f0) % cycle) / cycle * 2 * math.pi
        s = math.sin(ph); c = math.cos(ph)
        pose(arm, f,
             thigh_L=(28*s, 0, 0), thigh_R=(-28*s, 0, 0),
             shin_L=(-max(0, -c)*45 - 5, 0, 0), shin_R=(-max(0, c)*45 - 5, 0, 0),
             foot_L=(10*s, 0, 0), foot_R=(-10*s, 0, 0),
             uarm_L=(-22*s, 0, -15), uarm_R=(22*s, 0, 15), farm_L=(20, 0, 0), farm_R=(20, 0, 0),
             spine=(4, 0, 0), chest=(0, 4*s, 0), head=(-2, 0, 0),
             hips=(0, -6*s, 0))
        f += 3

# ichkarida birinchi qadamlar (98-100), keyin kadr almashganda eshik oldida
walk(G, 98, 100, (0.55, 2.55, 0), (0.5, 2.3, 0), heading=-15)
walk(G, 101, 160, (0.05, 0.55, 0), (0.75, -3.45, 0), heading=-8)
# mashina eshigiga o'girilib, ichiga kiradi (160-178)
key(G, 162, loc=(0.75, -3.5, 0), rot=(0, 0, -8)); key(G, 168, rot=(0, 0, 60))
pose(G, 161, **ARMS_DOWN, thigh_L=(0, 0, 0), thigh_R=(0, 0, 0), shin_L=(0, 0, 0), shin_R=(0, 0, 0), spine=(0, 0, 0))
pose(G, 172, uarm_L=(30, 0, -15), uarm_R=(10, 0, 15), thigh_L=(55, 0, 0), shin_L=(-60, 0, 0), spine=(25, 0, 0), head=(15, 0, 0))
key(G, 170, loc=(0.75, -3.6, 0)); key(G, 178, loc=(0.55, -4.45, -0.25))
vis(G, [(1, 178)])

# ================= KAMERALAR =================
def camera(name, loc, target, lens, fstop=None, focus=None):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_fit = "AUTO"
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop:
        d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = focus or target
    return c

# 1) Ikki kishilik o'rta plan, sekin yaqinlashish
t1 = empty("t1", (-0.1, 2.6, 1.3))
c1 = camera("cam1_twoshot", (0.15, 0.35, 1.45), t1, 20, 2.8)
key(c1, 1, loc=(0.15, 0.35, 1.45)); key(c1, 60, loc=(0.1, 0.9, 1.42))
# 2) Qizning yuziga yaqin plan (ona orqa fonda xira)
t2 = empty("t2", (0.55, 2.52, 1.5))
c2 = camera("cam2_closeup", (-0.15, 1.75, 1.52), t2, 55, 2.0)
key(c2, 61, loc=(-0.15, 1.75, 1.52)); key(c2, 100, loc=(-0.05, 1.85, 1.5))
key(t2, 61, loc=(0.55, 2.52, 1.5)); key(t2, 100, loc=(0.52, 2.4, 1.48))
# 3) Tashqarida past burchak, qiz eshikdan chiqib keladi
t3 = empty("t3", (0, 0, 1.1))
key(t3, 101, loc=(0.05, 0.3, 1.2)); key(t3, 160, loc=(0.7, -3.3, 1.1))
c3 = camera("cam3_exterior", (3.4, -3.3, 0.4), t3, 18, 4.0)
key(c3, 101, loc=(3.4, -3.3, 0.4)); key(c3, 160, loc=(3.1, -3.0, 0.45))
# 4) Mashina eshigi oldida
t4 = empty("t4", (0.6, -3.9, 1.0))
c4 = camera("cam4_cardoor", (2.9, -2.3, 1.35), t4, 26, 4.0)
key(c4, 161, loc=(2.9, -2.3, 1.35)); key(c4, 189, loc=(2.6, -2.5, 1.25))
# 5) Mashina orqasidan past burchak, haydab ketadi
c5 = camera("cam5_driveaway", (-4.5, -5.0, 0.4), car, 30, 5.6)
key(c5, 190, loc=(-4.5, -5.0, 0.4)); key(c5, 240, loc=(-3.8, -5.1, 0.55))
for f, c in ((1, c1), (61, c2), (101, c3), (161, c4), (190, c5)):
    sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = c1

# ================= YORUG'LIK =================
w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; sky = N.new("ShaderNodeTexSky")
try: sky.sun_elevation = R(35); sky.sun_rotation = R(200)
except Exception: pass
w.node_tree.links.new(sky.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 0.35
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.angle = R(3); sun.data.color = (1.0, 0.92, 0.8)
sun.rotation_euler = (R(55), R(0), R(160))
def area(name, loc, rot, energy, size, col=(1, 0.9, 0.78)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.energy = energy; l.data.size = size; l.data.color = col; l.location = loc; l.rotation_euler = [R(a) for a in rot]
    return l
area("ceiling_light", (0, 2.6, 2.65), (0, 0, 0), 120, 1.2)
area("window_key", (0.0, 4.7, 1.7), (-80, 0, 0), 180, 1.6, (0.95, 0.97, 1.0))
area("rim_light", (1.8, 3.8, 2.2), (-60, 30, 140), 60, 0.6, (1.0, 0.75, 0.5))
pl = bpy.data.objects.new("lamp_pt", bpy.data.lights.new("lamp_pt", "POINT")); sc.collection.objects.link(pl)
pl.data.energy = 60; pl.data.color = (1, 0.7, 0.4); pl.location = (2.4, 4.4, 1.5); pl.data.shadow_soft_size = 0.2

# ================= RENDER =================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 20)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 3; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.6
r.image_settings.file_format = "PNG"; r.filepath = OUT
r.use_persistent_data = True

if "--render" in sys.argv:
    fs = os.environ.get("FRAMES")
    if fs:
        for f in map(int, fs.split(",")):
            sc.frame_set(f); r.filepath = f"{OUT}test_{f:04d}.png"; bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
