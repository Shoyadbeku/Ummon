import bpy,sys,os
A=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/assets"
def reset(): bpy.ops.wm.read_factory_settings(use_empty=True)
reset()
bpy.ops.import_scene.fbx(filepath=A+"/characters/Megan.fbx")
for o in bpy.data.objects: print("OBJ",o.name,o.type,tuple(round(v,3) for v in o.dimensions),o.scale[:], o.rotation_euler[:], len(o.data.vertices) if o.type=='MESH' else '')
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
print("BONES",len(arm.data.bones),[b.name for b in arm.data.bones][:8])
for m in bpy.data.materials: print("MAT",m.name,[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE'] if m.node_tree else None)
print("IMGS",[(i.name,i.size[:],i.packed_file is not None) for i in bpy.data.images])
for a in ["Lifting","Drinking","Focus","Dizzy_Idle"]:
    reset(); bpy.ops.import_scene.fbx(filepath=A+f"/animations/{a}.fbx")
    ar=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
    act=ar.animation_data.action
    print("ANIM",a,act.name,act.frame_range[:],len(ar.data.bones),ar.data.bones[0].name,[o.name for o in bpy.data.objects], ar.scale[:])
reset(); bpy.ops.import_scene.gltf(filepath=A+"/models/street_rat/street_rat.gltf")
for o in bpy.data.objects: print("RAT",o.name,o.type,tuple(round(v,3) for v in o.dimensions),o.location[:],o.rotation_euler[:])
