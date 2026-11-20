"""Timeline renderer: shots -> raw RGB frames -> ffmpeg encoder."""
import subprocess, numpy as np, os, sys, time, math
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from gfx import *

GRADE = "eq=contrast=1.07:saturation=1.06:gamma=0.97:brightness=-0.01,vignette=angle=PI/5"


class Shot:
    def __init__(self, start, end, trans="cut", tdur=0.32, overlays=None, natsound=None, label=""):
        self.start, self.end = start, end
        self.trans, self.tdur = trans, tdur
        self.overlays = overlays or []
        self.natsound = natsound  # (gain_db) for videos
        self.label = label
    def dur(self):
        return self.end - self.start
    def open(self, ctx): pass
    def frame(self, ctx, t): raise NotImplementedError
    def close(self): pass
    def render(self, ctx, t):
        f = self.frame(ctx, t)
        if not f.flags.writeable:
            f = f.copy()
        for o in self.overlays:
            o.draw(f, t)
        return f


class VideoShot(Shot):
    """src video from src_in seconds, optional speed (<1 = slow motion), fit cover or window."""
    def __init__(self, start, end, src, src_in=0.0, speed=1.0, fit="cover", zoom=1.0, drift=(0, 0), hflip=False, focus=(0.5, 0.5), dark=0.0, **kw):
        super().__init__(start, end, **kw)
        self.src, self.src_in, self.speed, self.fit, self.zoom, self.drift, self.hflip = src, src_in, speed, fit, zoom, drift, hflip
        self.focus, self.dark = focus, dark
        self.proc = None; self.last = None; self.n = 0

    def open(self, ctx):
        W, H = ctx.W, ctx.H
        need = (self.dur() + 1.5) * self.speed + 0.5
        zw, zh = int(W * self.zoom) // 2 * 2, int(H * self.zoom) // 2 * 2
        pre = f"setpts=PTS/{self.speed}," if self.speed != 1 else ""
        flip = "hflip," if self.hflip else ""
        if self.fit == "cover":
            vf = (f"{pre}fps={ctx.fps},{flip}scale={zw}:{zh}:force_original_aspect_ratio=increase:flags=lanczos,"
                  f"crop={W}:{H}:(iw-{W})*{self.focus[0]}:(ih-{H})*{self.focus[1]},{GRADE}" + (f",eq=brightness={-self.dark}" if self.dark else "") + ",format=rgb24")
            if self.speed < 1:
                vf = vf.replace(f"{pre}fps={ctx.fps}", f"{pre}minterpolate=fps={ctx.fps}:mi_mode=blend")
            args = ["-vf", vf]
        else:  # window: blurred bg + framed fg
            fh = int(H * 0.80) // 2 * 2
            fc = (f"[0:v]{pre}fps={ctx.fps},split[a][b];"
                  f"[a]scale={W//8}:{H//8}:force_original_aspect_ratio=increase,crop={W//8}:{H//8},boxblur=8:2,eq=brightness=-0.18:saturation=0.6,scale={W}:{H}[bg];"
                  f"[b]scale=-2:{fh}:flags=lanczos,pad=iw+{ctx.s(16)}:ih+{ctx.s(16)}:{ctx.s(8)}:{ctx.s(8)}:color=white[fg];"
                  f"[bg][fg]overlay=(W-w)/2:(H-h)/2-{ctx.s(40)},eq=contrast=1.05:saturation=1.05,format=rgb24[o]")
            args = ["-filter_complex", fc, "-map", "[o]"]
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{self.src_in:.3f}", "-t", f"{need:.3f}", "-i", self.src, *args,
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
        self.fs = W * H * 3

    def frame(self, ctx, t):
        want = int(round(t * ctx.fps))
        while self.n <= want:
            buf = self.proc.stdout.read(self.fs) if self.proc else b""
            if len(buf) < self.fs:
                if self.last is None:
                    self.last = np.zeros((ctx.H, ctx.W, 3), np.uint8)
                self.proc = None
                break
            self.last = np.frombuffer(buf, np.uint8).reshape(ctx.H, ctx.W, 3)
            self.n += 1
        f = self.last
        if self.drift != (0, 0):
            pass
        return f.copy()

    def close(self):
        if self.proc:
            self.proc.stdout.close(); self.proc.kill(); self.proc = None


def load_photo(path, grade=True):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")
    if grade:
        im = ImageEnhance.Contrast(im).enhance(1.06)
        im = ImageEnhance.Color(im).enhance(1.04)
    return im


def vignette_mask(W, H, strength=0.35):
    y, x = np.ogrid[-1:1:H * 1j, -1:1:W * 1j]
    r = np.sqrt(x * x * 0.8 + y * y * 1.1)
    m = 1 - strength * np.clip(r - 0.35, 0, None) ** 1.6
    return np.clip(m, 0, 1).astype(np.float32)


class PhotoShot(Shot):
    """Ken Burns: rect = (cx, cy, zoom) in normalised source coordinates (cover crop)."""
    def __init__(self, start, end, src, a=(0.5, 0.5, 1.0), b=(0.5, 0.5, 1.12), fit="cover", darken=0.0, blur_bg=True, **kw):
        super().__init__(start, end, **kw)
        self.src, self.a, self.b, self.fit, self.darken = src, a, b, fit, darken

    def open(self, ctx):
        W, H = ctx.W, ctx.H
        im = load_photo(self.src)
        zmax = max(self.a[2], self.b[2])
        if self.fit == "cover":
            sc = max(W / im.width, H / im.height) * min(zmax, 1.6) * 1.02
            sc = min(sc, 1.0) if im.width * min(sc, 1.0) >= W and im.height * min(sc, 1.0) >= H else sc
            im = im.resize((max(W, int(im.width * sc)), max(H, int(im.height * sc))), Image.LANCZOS)
            self.base = im
        else:  # contain on blurred background (portrait / odd aspect)
            bg = im.resize((W // 8, int(W // 8 * im.height / im.width)), Image.BILINEAR)
            bgw = bg.width; bgh = bg.height
            sc = max((W // 8) / bgw, (H // 8) / bgh)
            bg = bg.resize((int(bgw * sc) + 1, int(bgh * sc) + 1)).crop((0, 0, W // 8, H // 8))
            bg = bg.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
            bg = ImageEnhance.Brightness(bg).enhance(0.55)
            fh = int(H * 0.86)
            fg = im.resize((int(im.width * fh / im.height), fh), Image.LANCZOS)
            if fg.width > W * 0.9:
                fw = int(W * 0.9); fg = im.resize((fw, int(im.height * fw / im.width)), Image.LANCZOS)
            bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
            self.base = bg.resize((int(W * zmax * 1.02), int(H * zmax * 1.02)), Image.LANCZOS)
        self.vig = vignette_mask(W, H, 0.42)[..., None] * (1 - self.darken)

    def frame(self, ctx, t):
        W, H = ctx.W, ctx.H
        p = ease_in_out(t / max(0.01, self.dur()))
        cx = self.a[0] + (self.b[0] - self.a[0]) * p
        cy = self.a[1] + (self.b[1] - self.a[1]) * p
        z = self.a[2] + (self.b[2] - self.a[2]) * p
        bw, bh = self.base.size
        # crop size so that output covers frame at zoom z
        cw = bw / z if bw / bh <= W / H else bh * W / H / z
        ch = cw * H / W
        if ch > bh: ch = bh; cw = ch * W / H
        x0 = min(max(0, cx * bw - cw / 2), bw - cw)
        y0 = min(max(0, cy * bh - ch / 2), bh - ch)
        im = self.base.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        f = np.asarray(im, dtype=np.float32) * self.vig
        return f.astype(np.uint8)


class GraphicShot(Shot):
    """fn(ctx, t, dur) -> np.uint8 frame"""
    def __init__(self, start, end, fn, setup=None, **kw):
        super().__init__(start, end, **kw)
        self.fn, self.setup = fn, setup
    def open(self, ctx):
        self.state = self.setup(ctx) if self.setup else None
    def frame(self, ctx, t):
        return self.fn(ctx, t, self.dur(), self.state)


def render(ctx, shots, out, globals_=(), t_from=0.0, t_to=None, crf=17, preset="faster", log_every=250):
    shots = sorted(shots, key=lambda s: s.start)
    total = t_to if t_to is not None else shots[-1].end
    n0, n1 = int(round(t_from * ctx.fps)), int(round(total * ctx.fps))
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ctx.W}x{ctx.H}",
                            "-r", str(ctx.fps), "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    opened = set()
    t_start = time.time()
    for n in range(n0, n1):
        t = n / ctx.fps
        cur = None
        for i, s in enumerate(shots):
            if s.start <= t < s.end:
                cur = i; break
        if cur is None:
            cur = len(shots) - 1
        s = shots[cur]
        # open current and (for transitions) previous
        need = {cur}
        prev = cur - 1
        in_trans = s.trans != "cut" and prev >= 0 and t - s.start < s.tdur
        if in_trans: need.add(prev)
        for i in list(opened):
            if i not in need and i < cur:
                shots[i].close(); opened.discard(i)
        for i in need:
            if i not in opened:
                shots[i].open(ctx); opened.add(i)
        f = s.render(ctx, t - s.start)
        if in_trans:
            p = (t - s.start) / s.tdur
            g = shots[prev].render(ctx, t - shots[prev].start)
            if s.trans == "dissolve":
                a = ease_in_out(p)
                f = (f.astype(np.uint16) * int(a * 256) + g.astype(np.uint16) * (256 - int(a * 256)) >> 8).astype(np.uint8)
            elif s.trans == "flash":
                w = 1 - abs(p * 2 - 1)  # 0->1->0
                base = g if p < 0.5 else f
                f = (base.astype(np.uint16) + int(w * 255 * 0.85)).clip(0, 255).astype(np.uint8)
            elif s.trans == "dip":
                w = 1 - abs(p * 2 - 1)
                base = g if p < 0.5 else f
                f = (base.astype(np.uint16) * int((1 - w) * 256) >> 8).astype(np.uint8)
            elif s.trans == "push":
                a = ease_in_out(p); off = int(ctx.W * a)
                f2 = np.empty_like(f)
                f2[:, :ctx.W - off] = g[:, off:]
                f2[:, ctx.W - off:] = f[:, :off]
                f = f2
        else:
            if not f.flags.writeable: f = f.copy()
        for o in globals_:
            o.draw(f, t)
        enc.stdin.write(f.tobytes())
        if (n - n0) % log_every == 0:
            el = time.time() - t_start
            print(f"frame {n}/{n1} t={t:.1f}s  {(n - n0 + 1) / max(el, 1e-3):.2f} fps", flush=True)
    for i in opened: shots[i].close()
    enc.stdin.close(); enc.wait()
    print("done", out, f"{time.time() - t_start:.0f}s", flush=True)
