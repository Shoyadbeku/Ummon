import sys, os, subprocess, json
from multiprocessing import Pool
from gfx import *
import scenes as SN

OUT = os.path.join(ROOT, 'seg')
os.makedirs(OUT, exist_ok=True)


def probe(src):
    o = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src]).decode().strip()
    w, h = map(int, o.split(',')[:2])
    return w, h


def nframes(sc):
    return round(sc['t1'] * FPS) - round(sc['t0'] * FPS)


def scene_credit(sc):
    if sc.get('credit_key'):
        if SN.photo(sc['credit_key']):
            return SN.photo_credit(sc['credit_key'])
        return sc.get('credit_fallback')
    return sc.get('credit')


def render(i):
    sc = SN.SC[i]
    n = nframes(sc)
    dur = n / FPS
    out = f'{OUT}/{i:03d}.mp4'
    if os.path.exists(out) and '--force' not in sys.argv:
        return out
    enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-frames:v', str(n), '-an', '-y', out + '.tmp.mp4']
    pipe_in = ['-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0']
    if sc['kind'] == 'clip':
        w, h = probe(sc['src'])
        sp = sc['speed']
        need = dur * sp + 0.5
        grade = 'eq=contrast=1.07:saturation=1.08:gamma=0.98,unsharp=5:5:0.6'
        if w / h < 1.5:
            fg_h = H
            fg = f'scale=-2:{fg_h}:flags=lanczos'
            bgf = f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=40,eq=brightness=-0.18:saturation=0.8'
            v = (f"[0:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},split[a][b];[a]{bgf}[bg];[b]{fg},{grade}[fg];"
                 f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base]")
        else:
            # cover-fit with slow push-in
            z0, z1 = 1.0, 1.06
            v = (f"[0:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},scale={int(W*1.08)}:{int(H*1.08)}:force_original_aspect_ratio=increase:flags=lanczos,"
                 f"crop={W}:{H}:x='(iw-ow)*(0.2+0.6*t/{dur:.3f})':y='(ih-oh)/2',setsar=1,{grade}[base]")
        if sc['darken']:
            v += f";[base]eq=brightness={-0.25*sc['darken']}:saturation={1-0.4*sc['darken']}[base2]"
            b = 'base2'
        else:
            b = 'base'
        v += f";[{b}][1:v]overlay=format=auto,format=yuv420p[v]"
        cmd = ['ffmpeg', '-loglevel', 'error', '-ss', str(sc['ss']), '-t', f'{need:.3f}', '-i', sc['src']] + pipe_in + ['-filter_complex', v, '-map', '[v]'] + enc
    else:
        cmd = ['ffmpeg', '-loglevel', 'error'] + pipe_in + ['-vf', 'format=yuv420p'] + enc
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cr = scene_credit(sc)
    for f in range(n):
        t = f / FPS
        if sc['kind'] == 'clip':
            im = layer()
            vignette(im)
            if sc.get('overlay'):
                sc['overlay'](im, t, dur)
        else:
            im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
            sc['draw'](im, t, dur)
        if sc.get('tag'):
            loc_tag(im, sc['tag'], t, dur + 0.4)
        if cr:
            credit(im, cr, t, dur + 0.4)
        p.stdin.write(im.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f'scene {i} failed')
    os.replace(out + '.tmp.mp4', out)
    return out


if __name__ == '__main__':
    idx = list(range(len(SN.SC)))
    if len(sys.argv) > 1 and sys.argv[1].replace(',', '').isdigit():
        idx = [int(x) for x in sys.argv[1].split(',')]
    # longest first for load balance
    idx.sort(key=lambda i: -nframes(SN.SC[i]))
    with Pool(int(os.environ.get('JOBS', 3))) as pool:
        for r in pool.imap_unordered(render, idx):
            print('done', r, flush=True)
