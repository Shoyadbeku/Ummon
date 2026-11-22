// To‘liq render: node render.js <scale> <startFrame> <endFrame(excl)> <out.mp4>
// Kadrlar deterministik: har bir kadr vaqt funksiyasi, shuning uchun bo‘laklab parallel render qilish mumkin.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const FPS = 30;
const root = __dirname;
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); }
    const ext = path.extname(f); r.writeHead(200, { 'Content-Type': { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' }[ext] || 'application/octet-stream' }); r.end(d); });
}).listen(0);
(async () => {
  const [scale, a, b, out] = process.argv.slice(2);
  const S = +scale, f0 = +a, f1 = +b;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', S >= 2 ? 'slow' : 'medium', '-crf', S >= 2 ? '14' : '18', '-pix_fmt', 'yuv420p', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const br = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await br.newPage({ viewport: { width: 800, height: 450 } });
  p.on('pageerror', e => console.log('[err]', e.message));
  await p.goto(`http://localhost:${srv.address().port}/index.html?scale=${S}`);
  await p.evaluate(() => window.ready);
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    await p.evaluate(t => window.renderFrame(t), f / FPS);
    const d = await p.evaluate(() => window.grab(.95));
    const buf = Buffer.from(d.slice(d.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 30 === 0) console.log(`[${out}] kadr ${f} / ${f1}  ${((Date.now() - t0) / 1000 / (f - f0 + 1)).toFixed(2)} s/kadr`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await br.close(); srv.close(); console.log('tayyor', out);
})();
