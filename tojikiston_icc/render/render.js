// Foydalanish:
//   node render.js <webroot> preview <outdir> t1 t2 ...     — alohida kadrlar (PNG/JPG)
//   node render.js <webroot> video <out.mp4> <workers>       — butun video (ovozsiz)
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const [root, mode, out, ...rest] = process.argv.slice(2);
const FPS = 25, DUR = 376.82;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); });
});
async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.error('PAGEERR', e.message));
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await page.evaluate(() => window.ready);
  return page;
}
async function frameJpeg(page, t) {
  const url = await page.evaluate(async (t) => { await window.renderAt(t); return window.grab(0.93); }, t);
  return Buffer.from(url.split(',')[1], 'base64');
}
server.listen(0, async () => {
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--disable-gpu', '--disable-web-security'] });
  if (mode === 'preview') {
    fs.mkdirSync(out, { recursive: true });
    const page = await openPage(browser, port);
    for (const ts of rest) { const t = parseFloat(ts); fs.writeFileSync(path.join(out, `f_${t.toFixed(2)}.jpg`), await frameJpeg(page, t)); }
  } else {
    const workers = parseInt(rest[0] || '4'); const total = Math.ceil(DUR * FPS);
    const per = Math.ceil(total / workers); const parts = [];
    const t0 = Date.now(); let done = 0;
    await Promise.all(Array.from({ length: workers }, async (_, w) => {
      const a = w * per, b = Math.min(total, a + per); const part = `${out}.part${w}.mp4`; parts.push(part);
      const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-threads', '1', part], { stdio: ['pipe', 'inherit', 'inherit'] });
      const page = await openPage(browser, port);
      for (let f = a; f < b; f++) {
        const buf = await frameJpeg(page, f / FPS);
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        done++; if (done % 250 === 0) console.log(`${done}/${total} kadr, ${((Date.now() - t0) / 1000).toFixed(0)} s`);
      }
      ff.stdin.end(); await new Promise(r => ff.on('close', r));
    }));
    parts.sort();
    fs.writeFileSync(out + '.list', parts.map(p => `file '${path.resolve(p)}'`).join('\n'));
    await new Promise(r => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', out + '.list', '-c', 'copy', out], { stdio: 'inherit' }).on('close', r));
    console.log('TAYYOR', out, ((Date.now() - t0) / 1000).toFixed(0), 's');
  }
  await browser.close(); server.close();
});
