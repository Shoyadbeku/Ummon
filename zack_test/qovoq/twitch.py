# Megan (Mixamo) chap ko'z qovog'i uchishi uchun shape key'lar.
# Dam holatida (T-poza) dunyo koordinatasida o'lchangan: Megan -Y tomonga qaraydi, uning chapi = +X.
# Ko'z markazi ~ (0.033, -0.133, 1.624); pastki qovoq ~ z 1.608..1.621; ko'z soqqasi alohida orol (ko'chirilmaydi).
import bpy, bmesh
from mathutils import Vector

EYE_W = Vector((0.033, -0.133, 1.624))     # dunyo (dam holati)
EYE_H = (0.033, 0.088, 0.135)              # Head suyagi fazosi: X chap, Y tepa, Z old

def _islands(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    seen = [-1] * len(bm.verts); isl = 0
    for v in bm.verts:
        if seen[v.index] >= 0: continue
        st = [v]; seen[v.index] = isl
        while st:
            a = st.pop()
            for e in a.link_edges:
                b = e.other_vert(a)
                if seen[b.index] < 0: seen[b.index] = isl; st.append(b)
        isl += 1
    bm.free(); return seen, isl

def _field(p, lower=1.0, upper=1.0):
    """dunyo nuqtasi -> siljish (dunyo, metr; 1.0 = ~1.6 mm)"""
    d = Vector((0, 0, 0))
    # pastki qovoq: ko'z ostidagi ellips
    dx = (p.x - 0.032) / 0.019; dz = (p.z - 1.616) / 0.010
    r2 = dx * dx + dz * dz
    if r2 < 1.0 and p.z < 1.6235:
        w = (1 - r2) ** 2
        d += Vector((0.0, -0.0006, 0.0016)) * w * lower
    # yuqori qovoq: kichik pastga titrash
    dx = (p.x - 0.032) / 0.02; dz = (p.z - 1.630) / 0.009
    r2 = dx * dx + dz * dz
    if r2 < 1.0 and p.z > 1.6245:
        w = (1 - r2) ** 2
        d += Vector((0.0, -0.0003, -0.0009)) * w * upper
    return d

def add_twitch(meshes, name="twitch"):
    """meshes: Body va Eyelashes. Har biriga shape key qo'shadi, kalitlar ro'yxatini qaytaradi."""
    keys = []
    for o in meshes:
        me = o.data
        if not me.shape_keys: o.shape_key_add(name="Basis", from_mix=False)
        kb = o.shape_key_add(name=name, from_mix=False); kb.value = 0.0
        W = o.matrix_world; Wi = W.inverted().to_3x3()
        if "Body" in o.name:
            seen, n = _islands(me)
            # ko'z atrofidagi kichik orollar (ko'z soqqasi, shox parda) o'z joyida qoladi
            cnt = {}
            for i in seen: cnt[i] = cnt.get(i, 0) + 1
            big = max(cnt, key=cnt.get)
        else:
            seen, big = None, None
        for i, v in enumerate(me.vertices):
            if seen is not None and seen[i] != big: continue
            p = W @ v.co
            if (p - EYE_W).length > 0.04: continue
            d = _field(p)
            if d.length_squared: kb.data[i].co = v.co + Wi @ d
        keys.append(kb)
    return keys
