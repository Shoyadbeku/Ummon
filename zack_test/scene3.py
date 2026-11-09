# Zack D. Films uslubidagi 10 soniyalik test (v3): Mixamo qahramonlar + mocap, Poly Haven muhit, BlenderKit mashina.
# qiz onasi bilan janjallashadi, uydan chiqib ketadi va mashinada ketadi. Ovozsiz, subtitrsiz.
import bpy, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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


import mixchar as mc
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/")
BK = os.environ.get("BK_DIR", "/tmp/claude-0/assets/bk/")

# ================= POLY HAVEN: PBR materiallar va mebel =================
def pbr(name, folder, scale=1.0, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs[0])
    def img(fn, non_color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn))
        t.projection = "BOX"; t.projection_blend = 0.2
        if non_color: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = img("diff.jpg")
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        L.new(d.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    else:
        L.new(d.outputs[0], b.inputs["Base Color"])
    r = img("rough.jpg", True); L.new(r.outputs[0], b.inputs["Roughness"])
    n = img("nor.jpg", True); nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    return m

def retex(prefixes, m):
    for o in bpy.data.objects:
        if o.type == "MESH" and any(o.name.startswith(p) for p in prefixes):
            o.data.materials.clear(); o.data.materials.append(m)

retex(["floor"], pbr("ph_floor", "laminate_floor_02", 0.5))
retex(["wall_", "ceiling"], pbr("ph_wall", "painted_plaster_wall", 0.5, tint=(0.95, 0.88, 0.78)))
retex(["road"], pbr("ph_asphalt", "asphalt_02", 0.25))
retex(["sidewalk", "path", "step1", "curb"], pbr("ph_concrete", "concrete_pavement", 0.4))

for o in list(bpy.data.objects):          # oddiy mebelni olib tashlab, Poly Haven modellari bilan almashtiramiz
    if any(o.name.startswith(p) for p in ("sofa", "cushion", "table", "tleg", "mug", "pot", "leaf", "pframe", "pic")):
        bpy.data.objects.remove(o, do_unlink=True)

def import_gltf(path, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = empty(os.path.basename(path).split(".")[0] + "_grp", loc)
    for o in new:
        if o.parent is None: o.parent = root
    root.rotation_euler.z = R(rot_z); root.scale = (scale,) * 3
    return root, new

import_gltf(PH + "Sofa_01/Sofa_01.gltf", (-0.2, 4.35, 0), 0)
import_gltf(PH + "modern_coffee_table_01/modern_coffee_table_01.gltf", (-0.2, 3.35, 0), 0)
import_gltf(PH + "potted_plant_01/potted_plant_01.gltf", (-2.5, 4.5, 0), 0, 1.2)
import_gltf(PH + "fancy_picture_frame_01/fancy_picture_frame_01.gltf", (-2.0, 4.92, 1.5), 0)

# ================= MASHINA (BlenderKit: Audi e-tron GT) =================
for o in list(bpy.data.objects):          # eski qo'lda yasalgan mashinani olib tashlash
    if o.name.startswith(("car", "arch_cut", "tire", "rim", "hub", "headlight", "taillight", "grille", "mirror", "bumper_r", "pillar")):
        bpy.data.objects.remove(o, do_unlink=True)
CAR0 = Vector((float(os.environ.get("CARX", 1.25)), -5.55, 0.0))
car, car_parts = import_gltf(BK + "c3c28d91_u.glb", tuple(CAR0), -90)   # old tomoni -X ga
car.name = "car"
# uy tomondagi oldingi eshikni (mahalliy -X tomon) alohida ajratib, ochiladigan qilish
import bmesh
door_parts = []
for o in car_parts:
    if o.type != "MESH": continue
    nm = o.name
    if nm.startswith("Plane.004") or nm.startswith("Plane.025") or nm.startswith("Plane.040") or nm.startswith("Plane.034"):
        me = o.data.copy(); d = o.copy(); d.data = me; sc.collection.objects.link(d)
        bm = bmesh.new(); bm.from_mesh(me)
        ymax = 0.25
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not (v.co.x < -0.05 and v.co.y < ymax)], context="VERTS"); bm.to_mesh(me); bm.free()
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.co.x < -0.05 and v.co.y < ymax)], context="VERTS"); bm.to_mesh(o.data); bm.free()
        door_parts.append(d)
dh = empty("cardoor_hinge", (-0.95, -0.9, 0.0), car)       # oldingi chekkadagi ilmoq (mahalliy)
bpy.context.view_layer.update()
for d in door_parts:
    d.parent = dh; d.matrix_parent_inverse = dh.matrix_world.inverted() @ car.matrix_world

# ================= QAHRAMONLAR (Mixamo, Hugging Face to'plami) =================
groot, girl, gmesh = mc.load_character("girl", "Megan.fbx")
mroot, mom, mmesh = mc.load_character("mom", "Kate.fbx")
for o in gmesh + mmesh:                  # plastmassa yaltirashini kamaytirish
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                for k in ("Specular IOR Level",):
                    for l in list(n.inputs[k].links): m.node_tree.links.remove(l)
                    n.inputs[k].default_value = 0.25
                if "hair" not in m.name.lower():
                    for l in list(n.inputs["Roughness"].links): m.node_tree.links.remove(l)
                    n.inputs["Roughness"].default_value = 0.62
                n.inputs["Coat Weight"].default_value = 0.0

A = lambda f, inplace=True: mc.load_action(f, inplace)
# ONA: ichkarida, qizga (+X) qarab barmoq bilan ko'rsatib baqiradi
mroot.location = (-0.75, 2.65, 0); mroot.rotation_euler.z = R(90)
mc.add_strip(mom, A("Angry_Point.fbx"), 1, repeat=2.0, speed=1.0)
mc.add_strip(mom, A("Angry_Gesture_3.fbx"), 60, repeat=3.0, speed=1.0, blend=6)

# QIZ
T = {"s1": 1, "s2": 51, "s3": 91, "s4": 146, "s5": 206}
groot.location = (0.55, 2.55, 0); groot.rotation_euler.z = R(-90)
groot.keyframe_insert("location", frame=1); groot.keyframe_insert("rotation_euler", frame=1)
mc.add_strip(girl, A("Dismissing_Gesture_2.fbx"), 1, speed=1.1)
mc.add_strip(girl, A("Annoyed_Head_Shake.fbx"), 48, speed=1.2, blend=6)
mc.add_strip(girl, A("Catwalk_Walk_Start_Turn_180_Right_2.fbx"), 74, speed=1.3, blend=5)
# kadr almashganda (91) eshik ostonasida; yurish (joyida) + ildizni ko'chirish
def at(f, loc, rz):
    groot.location = loc; groot.rotation_euler.z = R(rz)
    groot.keyframe_insert("location", frame=f); groot.keyframe_insert("rotation_euler", frame=f)
at(90, (0.55, 2.55, 0), -90)
at(91, (0.05, 0.25, 0), -2)
at(143, (0.95, -3.85, 0), -10)
walk = mc.add_strip(girl, A("Female_Walk.fbx"), 91, repeat=4.0, speed=1.45, blend=0)
# mashinaga o'tirish (ildiz harakati saqlanadi)
ENTER_ROT = float(os.environ.get("ENTER_ROT", -90))
ENTER_POS = tuple(map(float, os.environ.get("ENTER_POS", "0.95,-3.95,0").split(",")))
at(145, (0.95, -3.85, 0), -10); at(146, ENTER_POS, ENTER_ROT)
enter = mc.add_strip(girl, A("Entering_Car.fbx"), 146, speed=1.8, blend=3, src=(30, 165))
# o'tirish bosqichida (168-192) ildizni mashina ichiga, haydovchi o'rindig'iga suramiz
SEAT = tuple(map(float, os.environ.get("SEAT", "1.0,-5.0,-0.05").split(",")))
at(168, ENTER_POS, ENTER_ROT); at(192, SEAT, ENTER_ROT)
for fc in mc._fcurves(groot.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = "LINEAR" if (91 <= k.co.x <= 143 or 168 <= k.co.x < 192) else "CONSTANT"
# eshik: 150-162 ochiladi, 196-204 yopiladi
key(dh, 1, rot=(0, 0, 0)); key(dh, 150, rot=(0, 0, 0)); DA = float(os.environ.get("DOOR_ANG", 62))
key(dh, 162, rot=(0, 0, DA))
key(dh, 196, rot=(0, 0, DA)); key(dh, 204, rot=(0, 0, 0))
# mashina haydab ketadi
key(car, 1, loc=tuple(CAR0)); key(car, 208, loc=tuple(CAR0)); key(car, 240, loc=tuple(CAR0 + Vector((-16, 0, 0))))
set_interp(car, "QUAD", "location", "EASE_IN")
groot.parent = None
vis(groot, [(1, 204)])
for o in gmesh: vis(o, [(1, 204)])

# ================= KAMERALAR =================
def camera(name, loc, target, lens, fstop=None):
    d = bpy.data.cameras.new(name); d.lens = lens
    c = bpy.data.objects.new(name, d); sc.collection.objects.link(c); c.location = loc
    t = c.constraints.new("TRACK_TO"); t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    if fstop: d.dof.use_dof = True; d.dof.aperture_fstop = fstop; d.dof.focus_object = target
    return c
t1 = empty("t1", (-0.1, 2.6, 1.25))
c1 = camera("cam1_twoshot", (0.2, 0.35, 1.45), t1, 20, 2.8)
key(c1, 1, loc=(0.2, 0.35, 1.45)); key(c1, 50, loc=(0.15, 0.85, 1.42))
gh = empty("girl_head_t", (0.55, 2.55, 1.5))
c2 = camera("cam2_closeup", (-0.15, 1.85, 1.6), gh, 50, 2.0)
key(c2, 51, loc=(-0.15, 1.85, 1.6)); key(c2, 90, loc=(-0.05, 1.95, 1.58))
key(gh, 51, loc=(0.55, 2.55, 1.52)); key(gh, 90, loc=(0.55, 2.55, 1.45))
t3 = empty("t3", (0, 0, 1.1)); key(t3, 91, loc=(0.1, 0.0, 1.15)); key(t3, 145, loc=(0.9, -3.7, 1.05))
c3 = camera("cam3_exterior", (3.6, -3.4, 0.4), t3, 18, 4.0)
key(c3, 91, loc=(3.6, -3.4, 0.4)); key(c3, 145, loc=(3.3, -3.1, 0.45))
t4 = empty("t4", (1.0, -4.4, 0.95))
c4 = camera("cam4_cardoor", (-1.5, -2.5, 1.45), t4, 24, 4.0)
key(c4, 146, loc=(-1.5, -2.5, 1.45)); key(c4, 205, loc=(-1.2, -2.7, 1.35))
c5 = camera("cam5_driveaway", (7.2, -5.4, 0.45), car, 30, 5.6)
key(c5, 206, loc=(7.2, -5.4, 0.45)); key(c5, 240, loc=(6.6, -5.5, 0.6))
for f, c in ((1, c1), (51, c2), (91, c3), (146, c4), (206, c5)):
    sc.timeline_markers.new(c.name, frame=f).camera = c
sc.camera = c1

# ================= YORUG'LIK: Poly Haven HDRI =================
w = bpy.data.worlds.new("hdri"); sc.world = w; w.use_nodes = True
N = w.node_tree.nodes; env = N.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(PH + "kloofendal_48d_partly_cloudy_puresky.hdr")
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, R(120))
w.node_tree.links.new(tc.outputs["Generated"], mp.inputs[0]); w.node_tree.links.new(mp.outputs[0], env.inputs[0])
w.node_tree.links.new(env.outputs[0], N["Background"].inputs[0]); N["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 2.5; sun.data.angle = R(2); sun.data.color = (1.0, 0.93, 0.82); sun.rotation_euler = (R(52), 0, R(160))
def area(name, loc, rot, energy, size, col=(1, 0.9, 0.78)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")); sc.collection.objects.link(l)
    l.data.energy = energy; l.data.size = size; l.data.color = col; l.location = loc; l.rotation_euler = [R(a) for a in rot]
area("ceiling_light", (0, 2.6, 2.65), (0, 0, 0), 100, 1.2)
area("window_key", (0.0, 4.7, 1.7), (-80, 0, 0), 200, 1.6, (0.95, 0.97, 1.0))
area("face_fill", (0.6, 1.2, 1.7), (75, 0, 200), 40, 0.8, (1.0, 0.85, 0.7))

# ================= RENDER =================
r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("SAMPLES", 16)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 3
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(os.environ.get("PCT", 50))
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.4
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
