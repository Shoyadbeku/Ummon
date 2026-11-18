"""Environment builders: convenience store with open cooler, night warehouse."""
import bpy, math, random
from mathutils import Vector
import common as C


def can_collection(design, stain=False):
    """A hidden collection holding one closed can, for instancing."""
    key = f"CAN_{design}"
    if key in bpy.data.collections:
        return bpy.data.collections[key]
    coll = bpy.data.collections.new(key)
    C.make_can(f"can_{design}", design, coll=coll, stain=stain)
    return coll


def can_instance(design, loc, rot_z=0.0, coll=None):
    e = bpy.data.objects.new("canI", None)
    e.instance_type = "COLLECTION"
    e.instance_collection = can_collection(design)
    e.location = loc
    e.rotation_euler = (0, 0, rot_z)
    return C.link(e, coll)


# ------------------------------------------------------------------- STORE
def build_store(sc, deck_z=0.18):
    rnd = random.Random(7)
    coll = bpy.data.collections.new("Store")
    sc.collection.children.link(coll)
    floor = C.plane("Floor", 14, 14, (0, 0, 0), mat=C.pbr_texture("StoreFloor", "anti_slip_concrete", 1.2, 0.55, tint=(0.75, 0.75, 0.78)), coll=coll)
    wall_m = C.pbr_texture("Wall", "painted_plaster_wall", 1.0, 1.0, tint=(0.85, 0.88, 0.9))
    C.box("BackWall", (10, 0.2, 3.2), (0, -1.15, 1.6), wall_m, coll)
    C.box("SideWallL", (0.2, 10, 3.2), (-3.2, 2, 1.6), wall_m, coll)
    C.box("SideWallR", (0.2, 10, 3.2), (3.4, 2, 1.6), wall_m, coll)
    C.box("FrontWall", (10, 0.2, 3.2), (0, 4.2, 1.6), wall_m, coll)
    C.box("Ceiling", (10, 10, 0.1), (0, 1.5, 3.2), C.principled("Ceil", (0.6, 0.6, 0.62), 0, 0.8), coll)
    # ceiling light panels
    for i, (x, y) in enumerate([(-1.2, 0.6), (1.2, 0.6), (-1.2, 2.6), (1.2, 2.6)]):
        C.box(f"Panel{i}", (1.2, 0.3, 0.02), (x, y, 3.14), C.emission("PanelE", (1, 0.95, 0.88), 6), coll)
        C.area_light(f"PanelL{i}", 1.2, 90, (x, y, 3.1), color=(1, 0.93, 0.85), size_y=0.3, coll=coll)

    # ---- open multideck cooler (front plane y=-0.33, back y=-1.0)
    metal_out = C.principled("CoolerOut", (0.05, 0.055, 0.06), 0.6, 0.35)
    metal_in = C.principled("CoolerIn", (0.22, 0.23, 0.25), 0.4, 0.35)
    x0, x1, yf, yb, top = -1.6, 1.6, -0.33, -1.0, 2.05
    C.box("CoolerBack", (x1 - x0, 0.04, top), (0, yb, top / 2), metal_in, coll)
    C.box("CoolerSideL", (0.06, yf - yb + 0.1, top + 0.15), (x0 - 0.03, (yf + yb) / 2, (top + 0.15) / 2), metal_out, coll)
    C.box("CoolerSideR", (0.06, yf - yb + 0.1, top + 0.15), (x1 + 0.03, (yf + yb) / 2, (top + 0.15) / 2), metal_out, coll)
    C.box("CoolerBase", (x1 - x0, yf - yb + 0.1, deck_z), (0, (yf + yb) / 2 + 0.05, deck_z / 2), metal_out, coll)
    C.box("CoolerCanopy", (x1 - x0 + 0.12, 0.85, 0.22), (0, (yf + yb) / 2, top + 0.11), metal_out, coll)
    # header sign strip (cold LED)
    C.box("Header", (x1 - x0, 0.02, 0.14), (0, yf - 0.04, top + 0.1), C.emission("HeaderE", (0.55, 0.85, 1.0), 4), coll)
    shelves = [deck_z, 0.62, 0.98, 1.34, 1.70]
    glass_edge = C.principled("ShelfEdge", (0.02, 0.02, 0.02), 0.3, 0.4)
    led = C.emission("LED", (0.85, 0.93, 1.0), 10)
    designs = ["volt", "blue", "red"]
    for si, z in enumerate(shelves):
        if si > 0:
            C.box(f"Shelf{si}", (x1 - x0, 0.6, 0.015), (0, (yf + yb) / 2 + 0.04, z - 0.008), metal_in, coll)
            C.box(f"ShelfEdge{si}", (x1 - x0, 0.012, 0.04), (0, yf + 0.02, z - 0.01), glass_edge, coll)
        # LED strip under the shelf above
        ztop = shelves[si + 1] - 0.02 if si + 1 < len(shelves) else top - 0.02
        C.box(f"LED{si}", (x1 - x0 - 0.05, 0.01, 0.008), (0, yf - 0.03, ztop), led, coll)
        C.area_light(f"LEDL{si}", x1 - x0, 25, (0, yf - 0.06, ztop - 0.01), rot=(0, 0, 0), color=(0.82, 0.92, 1.0), size_y=0.04, coll=coll).data.energy = 12
        # cans: blocks of one design, 4 deep
        n = int((x1 - x0) / 0.068)
        for i in range(n):
            x = x0 + 0.04 + i * 0.068
            d = designs[(i // 6 + si) % 3]
            for j in range(4):
                y = yf - 0.06 - j * 0.07
                if si == 0 and j == 0 and -0.32 < x < 0.3:
                    continue  # gap where the hero can sits
                if rnd.random() < 0.06:
                    continue
                can_instance(d, (x + rnd.uniform(-0.003, 0.003), y, z), rnd.uniform(0, 6.28), coll)
    # air-curtain grille on the floor-front
    C.box("Grille", (x1 - x0, 0.06, 0.02), (0, yf - 0.02, deck_z + 0.005), C.principled("Grille", (0.1, 0.1, 0.1), 0.8, 0.4), coll)
    # opposite aisle: shelving with boxes (seen in reverse shots)
    try:
        box_meshes = C.polyhaven_model("cardboard_box_01")
        for i in range(10):
            for lvl in range(3):
                if rnd.random() < 0.25:
                    continue
                C.instance_of(box_meshes, "box", (-2.4 + i * 0.5, 3.75 - rnd.uniform(0, 0.05), 0.05 + lvl * 0.7),
                              (0, 0, rnd.uniform(-0.2, 0.2)), 1.0, coll)
        for lvl in range(4):
            C.box(f"OppShelf{lvl}", (5.2, 0.55, 0.03), (0, 3.85, lvl * 0.7 + 0.02), C.principled("OppShelfM", (0.7, 0.7, 0.72), 0.7, 0.4), coll)
    except Exception as e:
        print("[store] cardboard boxes skipped:", e)
    # cold fill from the cooler onto the shopper
    C.area_light("CoolerFill", 1.8, 50, (0, -0.45, 1.0), rot=(math.radians(-90), 0, 0), color=(0.75, 0.88, 1.0), size_y=1.4, coll=coll)
    C.world_color(sc, (0.02, 0.022, 0.025), 1.0)
    return coll


# ------------------------------------------------------------------- WAREHOUSE
def build_warehouse(sc, skip=(9, 4)):
    """Night warehouse. Pallet of shrink-wrapped can trays centred at origin; top of
    the cans at z = TOP_Z (returned)."""
    rnd = random.Random(3)
    coll = bpy.data.collections.new("Warehouse")
    sc.collection.children.link(coll)
    C.plane("Floor", 40, 40, (0, 0, 0), mat=C.pbr_texture("WFloor", "brushed_concrete", 0.6, 0.9, tint=(0.6, 0.6, 0.62)), coll=coll)
    wm = C.pbr_texture("WWall", "painted_plaster_wall", 0.4, 1.0, tint=(0.45, 0.48, 0.5))
    C.box("WBack", (30, 0.3, 9), (0, -9, 4.5), wm, coll)
    # left wall with a real window opening (y -3.5..0.5, z 5.6..7.2) for moonlight
    C.box("WLeftA", (0.3, 11.5, 9), (-9, -9.25, 4.5), wm, coll)
    C.box("WLeftB", (0.3, 11.5, 9), (-9, 6.25, 4.5), wm, coll)
    C.box("WLeftC", (0.3, 4.0, 5.6), (-9, -1.5, 2.8), wm, coll)
    C.box("WLeftD", (0.3, 4.0, 1.8), (-9, -1.5, 8.1), wm, coll)
    for k in range(5):  # window mullions
        C.box(f"Mullion{k}", (0.08, 0.06, 1.6), (-9, -3.5 + k * 1.0, 6.4), C.principled("Mull", (0.05, 0.05, 0.05), 0.6, 0.5), coll)
    C.box("WRight", (0.3, 30, 9), (11, 0, 4.5), wm, coll)
    C.box("WFront", (30, 0.3, 9), (0, 12, 4.5), wm, coll)
    C.box("WRoof", (30, 30, 0.3), (0, 0, 9), C.principled("Roof", (0.1, 0.1, 0.1), 0.5, 0.6), coll)
    # high window on the left wall (moonlight source)
    # pallet + can trays
    wood = C.principled("PalletWood", (0.35, 0.25, 0.15), 0, 0.8)
    nx, ny, layers = 12, 8, 3
    pitch = 0.068
    pw, pd = nx * pitch + 0.02, ny * pitch + 0.02
    C.box("PalletTop", (pw + 0.1, pd + 0.1, 0.025), (0, 0, 0.13), wood, coll)
    for k in (-1, 0, 1):
        C.box(f"PalletBlock{k}", (pw + 0.1, 0.1, 0.1), (0, k * (pd / 2), 0.06), wood, coll)
    tray_m = C.principled("Tray", (0.42, 0.32, 0.2), 0, 0.85)
    z = 0.145
    designs = ["volt", "blue", "red"]
    for L in range(layers):
        C.box(f"Tray{L}", (pw, pd, 0.004), (0, 0, z + 0.002), tray_m, coll)
        C.box(f"TrayLipF{L}", (pw, 0.004, 0.03), (0, -pd / 2, z + 0.015), tray_m, coll)
        C.box(f"TrayLipB{L}", (pw, 0.004, 0.03), (0, pd / 2, z + 0.015), tray_m, coll)
        z += 0.004
        for i in range(nx):
            for j in range(ny):
                x = -pw / 2 + 0.01 + pitch / 2 + i * pitch
                y = -pd / 2 + 0.01 + pitch / 2 + j * pitch
                if L == layers - 1 and (i, j) == skip:
                    hero_xy = (x, y)
                    continue
                can_instance(designs[0 if L == layers - 1 else (i + j) % 3], (x, y, z), rnd.uniform(0, 6.28), coll)
        z += C.CAN_H + 0.002
    top_z = z - 0.002
    # shrink wrap on the sides (not over the top: open to the rat)
    wrap = C.principled("Wrap", (0.9, 0.9, 0.92), 0, 0.15, **{"Transmission Weight": 1.0, "IOR": 1.3})
    wrap.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
    for nm, sz, loc in [("WrapF", (pw + 0.01, 0.002, top_z - 0.13), (0, -pd / 2 - 0.006, (top_z + 0.13) / 2)),
                        ("WrapB", (pw + 0.01, 0.002, top_z - 0.13), (0, pd / 2 + 0.006, (top_z + 0.13) / 2)),
                        ("WrapL", (0.002, pd + 0.01, top_z - 0.13), (-pw / 2 - 0.006, 0, (top_z + 0.13) / 2)),
                        ("WrapR", (0.002, pd + 0.01, top_z - 0.13), (pw / 2 + 0.006, 0, (top_z + 0.13) / 2))]:
        C.box(nm, sz, loc, wrap, coll)
    # surrounding racks and stock
    try:
        rack = C.polyhaven_model("worn_metal_rack")
        boxes = C.polyhaven_model("cardboard_box_01")
        crates = C.polyhaven_model("wooden_crate_02")
        pcr = C.polyhaven_model("plastic_crate_01")
        rdim = max(max(o.dimensions) for o in rack)
        for i in range(6):
            C.instance_of(rack, "rack", (-4.5 + i * 1.6, -3.2, 0), (0, 0, 0), 2.2 / rdim * 1.0, coll)
            for lvl in range(4):
                for b in range(3):
                    if rnd.random() < 0.3:
                        continue
                    C.instance_of(boxes, "box", (-5.0 + i * 1.6 + b * 0.42, -3.2 + rnd.uniform(-0.05, 0.05), 0.05 + lvl * 0.55),
                                  (0, 0, rnd.uniform(-0.3, 0.3)), 1.0, coll)
        for i in range(5):
            C.instance_of(crates, "crate", (2.0 + rnd.uniform(-0.2, 0.2), -1.5 + i * 0.9, 0), (0, 0, rnd.uniform(0, 1)), 1.0, coll)
            C.instance_of(pcr, "pcrate", (-2.2, 1.0 + i * 0.5, 0), (0, 0, rnd.uniform(0, 1)), 1.0, coll)
        # second pallet stack behind
        for (px, py) in [(-1.6, -1.6), (1.4, 2.2)]:
            C.box(f"Pallet2_{px}", (pw, pd, 0.6), (px, py, 0.4), C.principled("BoxedStock", (0.45, 0.34, 0.22), 0, 0.85), coll)
    except Exception as e:
        print("[warehouse] props skipped:", e)
    # light: cold moon through window + faint HDRI
    C.world_hdri(sc, "empty_warehouse_01", strength=0.02)
    C.sun("Moon", 9.0, (0, math.radians(-57), math.radians(12)), color=(0.55, 0.68, 1.0), angle=0.4)
    C.area_light("WinFill", 4, 60, (-8.7, -1.5, 6.4), rot=(0, math.radians(-90), 0), color=(0.55, 0.7, 1.0), size_y=1.6, coll=coll)
    sc["exposure"] = 1.0
    # cool moon-like key on the pallet so the hero area reads
    C.spot_light("PalletKey", 900, (-2.2, -1.2, 3.4), C.look_at_rot((-2.2, -1.2, 3.4), (0, 0, top_z)), angle=28, blend=0.5, color=(0.6, 0.72, 1.0), radius=0.15, coll=coll)
    C.area_light("PalletRim", 1.0, 120, (1.6, 1.4, 1.6), rot=C.look_at_rot((1.6, 1.4, 1.6), (0, 0, top_z)), color=(1.0, 0.75, 0.5), coll=coll)
    return coll, top_z, dict(pw=pw, pd=pd, pitch=pitch, hero=hero_xy)
