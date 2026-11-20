# Bosh suyagidan pastki jag'ni (mandibula) yon ko'rinishdagi poligon bo'yicha ajratib, skull_split.blend ga saqlash
import bpy, bmesh, math, sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath="/tmp/claude-0/assets/bk/49c13194_u.glb")
for o in list(bpy.data.objects):
    if o.name.startswith("Text"): bpy.data.objects.remove(o)
o = bpy.data.objects["Female Skull"]; bpy.context.view_layer.update()
MW = o.matrix_world.copy()
# piksel (600x600, ortho 0.3, markaz y=-0.031 z=0.122) -> dunyo (y, z)
PX = [(95, 434), (150, 430), (215, 424), (240, 380), (262, 352), (285, 340), (300, 328), (316, 338), (322, 380),
      (322, 425), (310, 468), (255, 512), (150, 548), (108, 525), (92, 475)]
POLY = [(-0.031 + (x - 300) * 0.0005, 0.122 - (y - 300) * 0.0005) for x, y in PX]
def inside(y, z):
    c = False; n = len(POLY)
    for i in range(n):
        y1, z1 = POLY[i]; y2, z2 = POLY[(i + 1) % n]
        if (z1 > z) != (z2 > z) and y < y1 + (z - z1) * (y2 - y1) / (z2 - z1): c = not c
    return c
bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
jaw = []
for f in bm.faces:
    p = MW @ f.calc_center_median()
    if inside(p.y, p.z): jaw.append(f)
print("JAW faces", len(jaw), "of", len(bm.faces))
keep = set(f.index for f in jaw)
bm2 = bm.copy()
bmesh.ops.delete(bm, geom=jaw, context="FACES")                   # bm: kalla (jag'siz)
bm2.faces.ensure_lookup_table()
bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in keep], context="FACES")
me_c = bpy.data.meshes.new("cranium"); bm.to_mesh(me_c); me_j = bpy.data.meshes.new("mandible"); bm2.to_mesh(me_j)
for me in (me_c, me_j):
    for m in o.data.materials: me.materials.append(m)
cr = bpy.data.objects.new("cranium", me_c); jw = bpy.data.objects.new("mandible", me_j)
for x in (cr, jw): sc.collection.objects.link(x); x.matrix_world = MW
bpy.data.objects.remove(o)
for x in list(bpy.data.objects):
    if x.type == "EMPTY": bpy.data.objects.remove(x)
# TMJ (jag' bo'g'imi) nuqtasi dunyoda
TMJ = Vector((0.0, -0.031, 0.1045)); e = bpy.data.objects.new("TMJ", None); e.location = TMJ; sc.collection.objects.link(e)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/assets/bk/skull_split.blend")
if "--test" in sys.argv:
    red = bpy.data.materials.new("r"); red.use_nodes = True; red.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 0, 0, 1)
    jw.data.materials.clear(); jw.data.materials.append(red)
    jw.rotation_mode = "XYZ"
    # jag'ni TMJ atrofida 25° ochish (X o'qi bo'ylab)
    from mathutils import Matrix
    jw.matrix_world = Matrix.Translation(TMJ) @ Matrix.Rotation(math.radians(-22), 4, "X") @ Matrix.Translation(-TMJ) @ MW
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 0.3; cam.location = (1, -0.031, 0.122); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    sc.camera = cam; w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.render.resolution_x = sc.render.resolution_y = 600
    sc.render.filepath = "/tmp/claude-0/test/skull_split.png"; bpy.ops.render.render(write_still=True)
