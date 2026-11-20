"""Animated news maps from Natural Earth (public domain)."""
import shapefile, math, numpy as np, os
from PIL import Image, ImageDraw, ImageFilter
from gfx import *

NE = os.path.join(os.path.dirname(__file__), "..", "ne", "ne_50m_admin_0_countries.shp")
_countries = None

def countries():
    global _countries
    if _countries is None:
        r = shapefile.Reader(NE, encoding="latin1")
        fields = [f[0] for f in r.fields[1:]]
        out = []
        for sr in r.iterShapeRecords():
            rec = dict(zip(fields, sr.record))
            iso = rec.get("ADM0_A3") or rec.get("ISO_A3")
            sh = sr.shape
            parts = list(sh.parts) + [len(sh.points)]
            rings = [np.array(sh.points[parts[i]:parts[i + 1]], dtype=np.float64) for i in range(len(parts) - 1)]
            bb = sh.bbox
            out.append((iso, rec.get("NAME", ""), rings, bb))
        _countries = out
    return _countries

OCEAN = (10, 20, 38)
LAND = (34, 44, 62)
LAND2 = (44, 56, 78)
BORDER = (78, 92, 118)

CITY = {
    "Riyadh": (46.72, 24.69), "Tehran": (51.39, 35.69), "Tashkent": (69.24, 41.30), "Hodeidah": (42.95, 14.80),
    "Sanaa": (44.21, 15.35), "Jeddah": (39.17, 21.54), "Makkah": (39.83, 21.42), "Dubai": (55.30, 25.27),
    "Doha": (51.53, 25.29), "Bandar Abbas": (56.27, 27.18), "Chabahar": (60.64, 25.29), "Ashgabat": (58.38, 37.95),
    "Hormuz": (56.45, 26.55), "Kharg": (50.32, 29.24), "Washington": (-77.04, 38.90), "Jerusalem": (35.22, 31.77),
    "Istanbul": (28.98, 41.01), "Mashhad": (59.6, 36.3), "Samarkand": (66.96, 39.65),
}


class MapScene:
    def __init__(self, cams, highlights=None, labels=(), pins=(), arcs=(), routes=(), zones=(), ripples=(),
                 title=None, dim_others=False):
        """cams: [(t, lon, lat, span_lon)].
        highlights: {iso: (color, t_on)}. labels: [(text, lon, lat, t_on, size, kind)].
        pins: [(lon, lat, t_on, color)]. arcs: [(lon0,lat0,lon1,lat1, t0, t1, color, height)].
        routes: [([(lon,lat),...], t0, t1, color, dashed)]. zones: [(iso, t_on, color)] hatched.
        ripples: [(lon, lat, t0, t1, color, max_r_deg)]"""
        self.cams = cams; self.hl = highlights or {}; self.labels = labels; self.pins = pins
        self.arcs = arcs; self.routes = routes; self.zones = zones; self.ripples = ripples; self.title = title

    def cam(self, t):
        c = self.cams
        if t <= c[0][0]: return c[0][1:]
        for (t0, *a), (t1, *b) in zip(c, c[1:]):
            if t0 <= t <= t1:
                p = ease_in_out((t - t0) / max(1e-3, t1 - t0))
                return tuple(x + (y - x) * p for x, y in zip(a, b))
        return c[-1][1:]

    def render(self, ctx, t):
        W, H = ctx.W, ctx.H
        lon0, lat0, span = self.cam(t)
        k = math.cos(math.radians(lat0))
        sx = W / span
        def P(lon, lat):
            return ((lon - lon0) * k * sx + W / 2, -(lat - lat0) * sx + H / 2)
        def Parr(a):
            return np.stack([(a[:, 0] - lon0) * k * sx + W / 2, -(a[:, 1] - lat0) * sx + H / 2], 1)
        img = Image.new("RGB", (W, H), OCEAN)
        # subtle graticule
        d = ImageDraw.Draw(img, "RGBA")
        g = 5 if span < 60 else 10
        for gl in range(-180, 181, g):
            x, _ = P(gl, lat0); d.line([x, 0, x, H], fill=(255, 255, 255, 10), width=max(1, ctx.s(2)))
        for gt in range(-80, 81, g):
            _, y = P(lon0, gt); d.line([0, y, W, y], fill=(255, 255, 255, 10), width=max(1, ctx.s(2)))
        lonmin = lon0 - span / k / 2 - 5; lonmax = lon0 + span / k / 2 + 5
        latspan = span * H / W
        latmin = lat0 - latspan / 2 - 5; latmax = lat0 + latspan / 2 + 5
        bw = max(1, ctx.s(3))
        for iso, name, rings, bb in countries():
            if bb[2] < lonmin or bb[0] > lonmax or bb[3] < latmin or bb[1] > latmax:
                continue
            col = LAND
            if iso in self.hl:
                c, ton = self.hl[iso][:2]
                a = ease_out((t - ton) / 0.6) if t >= ton else 0
                col = tuple(int(LAND[i] + (c[i] - LAND[i]) * a) for i in range(3))
            for r in rings:
                pts = [tuple(p) for p in Parr(r)]
                if len(pts) > 2:
                    d.polygon(pts, fill=col, outline=BORDER, width=bw)
        # hatched zones
        for iso, ton, color in self.zones:
            if t < ton: continue
            a = ease_out((t - ton) / 0.8)
            layer = Image.new("L", (W, H), 0)
            ld = ImageDraw.Draw(layer)
            for ciso, name, rings, bb in countries():
                if ciso == iso:
                    for r in rings:
                        pts = [tuple(p) for p in Parr(r)]
                        if len(pts) > 2: ld.polygon(pts, fill=255)
            step = ctx.s(48)
            if getattr(self, "_hatch", None) is None or self._hatch.shape != (H, W):
                hatch = Image.new("L", (W, H), 0)
                hd = ImageDraw.Draw(hatch)
                for x in range(-H, W + H, step):
                    hd.line([x, 0, x + H, H], fill=255, width=ctx.s(14))
                self._hatch = (0.25 + 0.45 * np.asarray(hatch, np.float32) / 255)
            off = int(t * ctx.s(60)) % step
            hm = np.roll(self._hatch, off, axis=1)
            m = (np.asarray(layer, np.float32) / 255 * hm * a * 255).astype(np.uint8)
            col = Image.new("RGB", (W, H), color)
            img.paste(col, (0, 0), Image.fromarray(m))
            d = ImageDraw.Draw(img, "RGBA")
        # routes
        for pts, t0, t1, color, dashed in self.routes:
            if t < t0: continue
            p = ease_in_out((t - t0) / max(1e-3, t1 - t0))
            xy = [P(*q) for q in pts]
            # cumulative length
            segs = [math.dist(xy[i], xy[i + 1]) for i in range(len(xy) - 1)]
            L = sum(segs) * p; out = [xy[0]]
            for i, sl in enumerate(segs):
                if L >= sl: out.append(xy[i + 1]); L -= sl
                else:
                    f = L / sl if sl else 0
                    out.append((xy[i][0] + (xy[i + 1][0] - xy[i][0]) * f, xy[i][1] + (xy[i + 1][1] - xy[i][1]) * f)); break
            d.line(out, fill=color + (255,), width=ctx.s(14), joint="curve")
            hx, hy = out[-1]; r = ctx.s(22)
            d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=color + (255,))
        # arcs
        for lo0, la0, lo1, la1, t0, t1, color, hgt in self.arcs:
            if t < t0: continue
            p = ease_in_out((t - t0) / max(1e-3, t1 - t0))
            (x0, y0), (x1, y1) = P(lo0, la0), P(lo1, la1)
            n = 64; pts = []
            for i in range(int(n * p) + 1):
                u = i / n
                x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u - math.sin(math.pi * u) * hgt * math.dist((x0, y0), (x1, y1))
                pts.append((x, y))
            if len(pts) > 1:
                for wdt, al in ((ctx.s(36), 60), (ctx.s(12), 255)):
                    d.line(pts, fill=color + (al,), width=wdt, joint="curve")
                hx, hy = pts[-1]; r = ctx.s(26)
                if p < 1:
                    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(255, 255, 255, 255))
        # ripples
        for lon, lat, t0, t1, color, rmax in self.ripples:
            if not (t0 <= t <= t1 + 1.2): continue
            x, y = P(lon, lat)
            for kk in range(3):
                q = ((t - t0) / 1.4 - kk * 0.33) % 1.0 if t <= t1 else None
                if q is None: continue
                r = q * rmax * sx; al = int(200 * (1 - q))
                d.ellipse([x - r, y - r, x + r, y + r], outline=color + (al,), width=ctx.s(10))
        # pins
        for lon, lat, ton, color in self.pins:
            if t < ton: continue
            x, y = P(lon, lat)
            a = ease_out_back((t - ton) / 0.4)
            r = ctx.s(26) * a
            q = ((t - ton) % 1.4) / 1.4; rr = ctx.s(26) + q * ctx.s(110)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=color + (int(220 * (1 - q)),), width=ctx.s(8))
            d.ellipse([x - r - ctx.s(8), y - r - ctx.s(8), x + r + ctx.s(8), y + r + ctx.s(8)], fill=(255, 255, 255, 255))
            d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,))
        # labels
        for lab in self.labels:
            text, lon, lat, ton = lab[:4]
            size = lab[4] if len(lab) > 4 else 70
            kind = lab[5] if len(lab) > 5 else "country"
            if t < ton: continue
            a = ease_out((t - ton) / 0.5)
            x, y = P(lon, lat)
            f = font("black" if kind == "country" else "bold", ctx.s(size))
            tw = f.getlength(text)
            if kind == "country":
                draw_text(d, (x - tw / 2 - ctx.s(3) * len(text) / 2, y - ctx.s(size) / 2), text, f, (255, 255, 255, int(235 * a)), tracking=ctx.s(3))
            else:
                bx, by = x + ctx.s(48), y - ctx.s(size) * 0.75
                d.rectangle([bx - ctx.s(18), by - ctx.s(12), bx + tw + ctx.s(18), by + ctx.s(size) * 1.25], fill=(255, 255, 255, int(240 * a)))
                d.text((bx, by), text, font=f, fill=NAVY + (int(255 * a),))
        arr = np.array(img)
        return arr


def map_shot_fn(scene):
    def fn(ctx, t, dur, state):
        return scene.render(ctx, t)
    return fn
