import bpy, os
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "scene.blend"))
s = bpy.context.scene
s.render.filepath = os.path.join(HERE, "frames", "f_")
s.render.use_overwrite = False
s.render.use_placeholder = True
bpy.ops.render.render(animation=True)
print("RENDER DONE")
