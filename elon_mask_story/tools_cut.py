import subprocess, sys, concurrent.futures as cf
jobs = [l.split('|') for l in open(sys.argv[1]).read().strip().split('\n')]
out = sys.argv[2]
def cut(j):
    name, src, ss, dur = [x.strip() for x in j]
    r = subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-ss',ss,'-i',src,'-t',dur,'-an','-vf','scale=-2:1080,fps=30','-c:v','libx264','-crf','19','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',f'{out}/{name}.mp4'])
    return name, r.returncode
with cf.ThreadPoolExecutor(int(sys.argv[3]) if len(sys.argv) > 3 else 4) as ex:
    for n, rc in ex.map(cut, jobs): print(n, 'OK' if rc == 0 else 'FAIL')
