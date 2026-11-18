import bpy,os
from mathutils import Vector
A=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/assets"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=A+"/characters/Megan.fbx")
meg=bpy.data.objects["Armature"]; meg.name="Megan"
res={}
for a in ["Lifting","Drinking","Focus","Dizzy_Idle","Catwalk_Idle"]:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=A+f"/animations/{a}.fbx")
    new=[o for o in bpy.data.objects if o not in before]
    src=[o for o in new if o.type=='ARMATURE'][0]
    # rest compare
    md=max((meg.data.bones[b.name].matrix_local.to_quaternion().rotation_difference(b.matrix_local.to_quaternion()).angle) for b in src.data.bones if b.name in meg.data.bones)
    ld=max(((meg.data.bones[b.name].head_local-b.head_local).length) for b in src.data.bones)
    act=src.animation_data.action; act.name=a
    for o in new: bpy.data.objects.remove(o)
    print("REST",a,"max rot diff deg",round(md*57.3,2),"max head diff",round(ld,2))
    meg.animation_data_create(); meg.animation_data.action=act
    if hasattr(meg.animation_data,'action_slot') and act.slots: meg.animation_data.action_slot=act.slots[0]
    sc=bpy.context.scene
    for f in range(1,int(act.frame_range[1])+1,15):
        sc.frame_set(f)
        pb=meg.pose.bones
        w=lambda n:(meg.matrix_world@pb["mixamorig:"+n].head)
        print(a,f,"hips",tuple(round(v,2) for v in w("Hips")),"RH",tuple(round(v,2) for v in w("RightHand")),"LH",tuple(round(v,2) for v in w("LeftHand")),"head",tuple(round(v,2) for v in w("Head")))
