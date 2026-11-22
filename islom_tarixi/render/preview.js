// Tanlangan kadrlarni PNG qilib saqlash: node preview.js out_dir scale t1 t2 ...
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const root = __dirname;
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); }
    const ext = path.extname(f); r.writeHead(200, { 'Content-Type': { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' }[ext] || 'application/octet-stream' }); r.end(d); });
}).listen(0);
(async () => {
  const [out, scale, ...ts] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 800, height: 450 } });
  p.on('console', m => console.log('[page]', m.text())); p.on('pageerror', e => console.log('[err]', e.message));
  await p.goto(`http://localhost:${srv.address().port}/index.html?scale=${scale}`);
  await p.evaluate(() => window.ready);
  for (const t of ts) {
    const t0 = Date.now(); await p.evaluate(t => window.renderFrame(t), +t);
    const d = await p.evaluate(() => window.grab(.9));
    fs.writeFileSync(`${out}/f_${(+t).toFixed(2).padStart(6, '0')}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
    console.log(t, Date.now() - t0, 'ms');
  }
  await b.close(); srv.close();
})();
