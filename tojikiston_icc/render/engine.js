// Kadrma-kadr deterministik render dvigateli (1920x1080, 25 fps).
// window.renderAt(t) — t soniyadagi kadrni chizadi va JPEG dataURL qaytaradi.
'use strict';
const W = 1920, H = 1080, FPS = 25;
const C = {
  navy: '#08101F', navy2: '#0F1C36', panel: 'rgba(8,16,31,0.86)', red: '#D7263D', redD: '#9E1B2C',
  gold: '#F2B134', white: '#FFFFFF', grey: '#A7B0C0', dim: '#5B6780', blue: '#3D7BE0',
  sea: '#050B17', land: '#22324F', land2: '#22345A', border: '#50648F',
};
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const small = document.createElement('canvas'); small.width = 48; small.height = 27;
const sctx = small.getContext('2d');

// ---------- yordamchi funksiyalar ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const eOut = p => 1 - Math.pow(1 - clamp(p), 3);
const eIn = p => Math.pow(clamp(p), 3);
const eIO = p => { p = clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
const eBack = p => { p = clamp(p); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
function env(t, t0, t1, fi = 0.45, fo = 0.35) {
  return Math.min(eOut((t - t0) / fi), eOut((t1 - t) / fo));
}
function font(size, weight = 700, fam = 'Oswald') { return `${weight} ${size}px ${fam}`; }
const INTER = 'Inter';

function wrap(text, maxW) {
  const words = String(text).split(' '); const lines = []; let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

// ---------- rasm keshi ----------
const cache = new Map();
function loadImg(url) {
  if (cache.has(url)) { const v = cache.get(url); cache.delete(url); cache.set(url, v); return v; }
  const p = new Promise((res) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = url; });
  cache.set(url, p);
  while (cache.size > 48) cache.delete(cache.keys().next().value);
  return p;
}
let MAN = null, WORLD = null;

// ---------- fon turlari ----------
function frameUrl(clip, idx) { return `frames/${clip}/${String(idx + 1).padStart(5, '0')}.jpg`; }
function clipFrameIdx(s, t) {
  const n = MAN[s.clip].n;
  let f = Math.floor(((t - s.t0) * (s.rate || 1) + (s.off || 0)) * FPS);
  if (f >= n) { // ping-pong, kadr qotib qolmasligi uchun
    const per = 2 * (n - 1); f = f % per; if (f >= n) f = per - f;
  }
  return clamp(f, 0, n - 1);
}
function kbParams(s, t) {
  const p = clamp((t - s.t0) / Math.max(0.1, s.t1 - s.t0));
  const kb = s.kb || {};
  const z = lerp(kb.z0 ?? 1.04, kb.z1 ?? 1.12, eIO(p));
  const x = lerp(kb.x0 ?? 0, kb.x1 ?? 0, eIO(p));
  const y = lerp(kb.y0 ?? 0, kb.y1 ?? 0, eIO(p));
  return { z, x, y };
}
function drawCover(im, z, ox, oy, bx = 0, by = 0, bw = W, bh = H) {
  const s = Math.max(bw / im.width, bh / im.height) * z;
  const w = im.width * s, h = im.height * s;
  const x = bx + (bw - w) / 2 + ox * (w - bw) / 2, y = by + (bh - h) / 2 + oy * (h - bh) / 2;
  ctx.drawImage(im, x, y, w, h);
}
function blurFill(im) {
  sctx.drawImage(im, 0, 0, 48, 27);
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(small, -40, -40, W + 80, H + 80);
  ctx.fillStyle = 'rgba(5,10,22,0.55)'; ctx.fillRect(0, 0, W, H);
}
async function drawVideo(s, t) {
  const im = await loadImg(frameUrl(s.clip, clipFrameIdx(s, t)));
  if (!im) return;
  const k = kbParams(s, t);
  if (MAN[s.clip].lowres && !s.full) {
    blurFill(im);
    const ar = im.width / im.height; const bh = 700, bw = Math.round(bh * ar);
    const bx = (W - bw) / 2, by = 120 + (s.wy || 0);
    ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 50; ctx.fillStyle = '#000';
    ctx.fillRect(bx - 4, by - 4, bw + 8, bh + 8); ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.rect(bx, by, bw, bh); ctx.clip();
    drawCover(im, 1 + (k.z - 1) * 0.5, k.x, k.y, bx, by, bw, bh); ctx.restore();
    ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 3; ctx.strokeRect(bx - 1.5, by - 1.5, bw + 3, bh + 3);
    if (s.archive) {
      ctx.font = font(26, 700); const label = 'ARXIV · ' + s.archive; const tw = ctx.measureText(label).width;
      ctx.fillStyle = C.red; ctx.fillRect(bx, by - 46, tw + 28, 42);
      ctx.fillStyle = C.white; ctx.textBaseline = 'middle'; ctx.fillText(label, bx + 14, by - 24);
    }
  } else {
    drawCover(im, k.z, k.x, k.y);
  }
}
async function drawPhoto(s, t) {
  const im = await loadImg('photos/' + s.photo + '.jpg'); if (!im) return;
  const k = kbParams(s, t); drawCover(im, k.z, k.x, k.y);
}
function drawGraphicBg(t, s) {
  const g = ctx.createLinearGradient(0, 0, W, H);
  g.addColorStop(0, s.c0 || '#0C1830'); g.addColorStop(1, s.c1 || '#050A15');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // harakatlanuvchi to'r
  ctx.strokeStyle = 'rgba(120,150,210,0.07)'; ctx.lineWidth = 1;
  const off = (t * 12) % 80;
  for (let x = -80 + off; x < W; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = -80 + off; y < H; y += 80) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  const rg = ctx.createRadialGradient(W * 0.5, H * 0.45, 100, W * 0.5, H * 0.5, 1100);
  rg.addColorStop(0, 'rgba(61,123,224,0.16)'); rg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
}
async function drawBlurPhoto(s, t) {
  const im = await loadImg('photos/' + s.photo + '.jpg'); if (!im) return;
  blurFill(im); ctx.fillStyle = 'rgba(5,10,22,0.35)'; ctx.fillRect(0, 0, W, H);
}

// ---------- xarita ----------
function camAt(s, t) {
  const p = eIO((t - s.t0 - (s.camDelay || 0)) / (s.camDur || (s.t1 - s.t0)));
  const a = s.cam0, b = s.cam1 || s.cam0;
  return { lon: lerp(a[0], b[0], p), lat: lerp(a[1], b[1], p), k: Math.exp(lerp(Math.log(a[2]), Math.log(b[2]), p)) };
}
function proj(cam, lon, lat) {
  const cl = Math.cos(cam.lat * Math.PI / 180);
  return [W / 2 + (lon - cam.lon) * cam.k * cl, H / 2 - (lat - cam.lat) * cam.k];
}
function countryPath(cam, iso) {
  const c = WORLD[iso]; if (!c) return null;
  const p = new Path2D();
  for (const ring of c.rings) {
    ring.forEach(([lo, la], i) => { const [x, y] = proj(cam, lo, la); i ? p.lineTo(x, y) : p.moveTo(x, y); });
    p.closePath();
  }
  return p;
}
function drawMap(s, t) {
  const cam = camAt(s, t);
  ctx.fillStyle = C.sea; ctx.fillRect(0, 0, W, H);
  // graticule
  ctx.strokeStyle = 'rgba(90,120,180,0.10)'; ctx.lineWidth = 1;
  for (let lo = -180; lo <= 180; lo += 10) { const [x1, y1] = proj(cam, lo, -80), [x2, y2] = proj(cam, lo, 85); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); }
  for (let la = -80; la <= 80; la += 10) { const [x1, y1] = proj(cam, -180, la), [x2, y2] = proj(cam, 180, la); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); }
  const hl = {}; (s.hl || []).forEach(h => { hl[h.iso] = h; });
  ctx.lineJoin = 'round';
  for (const iso in WORLD) {
    const c = WORLD[iso];
    // tez kesish: yorliq nuqtasi ekrandan juda uzoq bo'lsa ham chiziladi (katta davlatlar uchun), shuning uchun faqat juda kichik k da hammasi
    const path = countryPath(cam, iso); if (!path) continue;
    ctx.fillStyle = C.land; ctx.fill(path);
    ctx.strokeStyle = C.border; ctx.lineWidth = 1; ctx.stroke(path);
  }
  // ajratib ko'rsatilgan davlatlar
  for (const h of (s.hl || [])) {
    const a = clamp((t - (s.t0 + (h.at || 0))) / 0.6) * (h.until ? clamp((s.t0 + h.until - t) / 0.5) : 1);
    if (a <= 0) continue;
    const path = countryPath(cam, h.iso); if (!path) continue;
    ctx.save(); ctx.globalAlpha = a * (h.alpha ?? 0.9);
    if (h.glow) { ctx.shadowColor = h.color; ctx.shadowBlur = 30 + 12 * Math.sin(t * 4); }
    ctx.fillStyle = h.color; ctx.fill(path); ctx.restore();
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = h.stroke || '#fff'; ctx.lineWidth = 2; ctx.stroke(path); ctx.restore();
  }
  // strelkalar
  for (const ar of (s.arrows || [])) {
    const p = eIO((t - s.t0 - ar.at) / (ar.dur || 1.2)); if (p <= 0) continue;
    const [x1, y1] = proj(cam, ar.from[0], ar.from[1]), [x2, y2] = proj(cam, ar.to[0], ar.to[1]);
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2 - Math.hypot(x2 - x1, y2 - y1) * (ar.bend ?? 0.25);
    ctx.save(); ctx.strokeStyle = ar.color || C.gold; ctx.lineWidth = 5; ctx.lineCap = 'round';
    ctx.setLineDash([]); ctx.beginPath();
    const N = 60; let lx = x1, ly = y1;
    ctx.moveTo(x1, y1);
    for (let i = 1; i <= N * p; i++) { const u = i / N; lx = (1 - u) * (1 - u) * x1 + 2 * (1 - u) * u * mx + u * u * x2; ly = (1 - u) * (1 - u) * y1 + 2 * (1 - u) * u * my + u * u * y2; ctx.lineTo(lx, ly); }
    ctx.shadowColor = ar.color || C.gold; ctx.shadowBlur = 16; ctx.stroke();
    ctx.beginPath(); ctx.arc(lx, ly, 9, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill();
    ctx.restore();
    if (ar.label && p > 0.6) {
      const a = clamp((p - 0.6) / 0.4);
      label(lerp(x1, x2, 0.5) + (ar.lx || 0), my + (ar.ly || 0), ar.label, a, ar.color || C.gold, 30);
    }
  }
  // pinlar
  for (const pn of (s.pins || [])) {
    const a = clamp((t - s.t0 - pn.at) / 0.5); if (a <= 0) continue;
    const [x, y] = proj(cam, pn.lon, pn.lat);
    const pulse = (t * 1.2) % 1;
    ctx.save(); ctx.globalAlpha = a * (1 - pulse); ctx.strokeStyle = pn.color || C.red; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(x, y, 12 + pulse * 40, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = pn.color || C.red; ctx.beginPath(); ctx.arc(x, y, 11, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.stroke(); ctx.restore();
    if (pn.label) label(x + (pn.dx ?? 24), y + (pn.dy ?? -6), pn.label, a, pn.color || C.red, pn.size || 34, pn.align || 'left');
  }
  // davlat nomlari
  for (const h of (s.hl || [])) {
    if (!h.label) continue;
    const a = clamp((t - (s.t0 + (h.lat ?? h.at ?? 0))) / 0.5) * (h.until ? clamp((s.t0 + h.until - t) / 0.5) : 1); if (a <= 0) continue;
    const c = WORLD[h.iso]; const [x, y] = proj(cam, (h.pos || c.lab)[0], (h.pos || c.lab)[1]);
    label(x + (h.dx || 0), y + (h.dy || 0), h.label, a, h.color, h.size || 30, h.align || 'center', h.sub);
  }
  for (const tl of (s.texts || [])) {
    const a = clamp((t - s.t0 - tl.at) / 0.5); if (a <= 0) continue;
    const [x, y] = proj(cam, tl.lon, tl.lat);
    ctx.save(); ctx.globalAlpha = a * (tl.alpha ?? 0.75); ctx.fillStyle = tl.color || C.grey; ctx.font = font(tl.size || 26, 500, INTER);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.letterSpacing = '4px'; ctx.fillText(tl.text, x, y); ctx.restore();
  }
}
function label(x, y, text, a, color, size = 30, align = 'left', sub) {
  ctx.save(); ctx.globalAlpha = a; ctx.font = font(size, 700); ctx.letterSpacing = '1px';
  const tw = ctx.measureText(text).width; let sw = 0;
  if (sub) { ctx.font = font(size * 0.62, 500, INTER); sw = ctx.measureText(sub).width; }
  const bw = Math.max(tw, sw) + 28, bh = size * 1.35 + (sub ? size * 0.9 : 0);
  let bx = align === 'center' ? x - bw / 2 : align === 'right' ? x - bw : x; const by = y - size * 0.7;
  ctx.fillStyle = 'rgba(5,10,22,0.85)'; rr(bx, by, bw, bh, 6); ctx.fill();
  ctx.fillStyle = color; ctx.fillRect(bx, by, 6, bh);
  ctx.fillStyle = '#fff'; ctx.font = font(size, 700); ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  ctx.fillText(text, bx + 16, by + size * 0.68);
  if (sub) { ctx.font = font(size * 0.62, 500, INTER); ctx.fillStyle = '#D4DAE6'; ctx.letterSpacing = '0px'; ctx.fillText(sub, bx + 16, by + size * 1.55); }
  ctx.restore();
}

// ---------- ustki qatlamlar ----------
const OV = {};
OV.lower3 = (o, t) => {
  const a = env(t, o.t0, o.t1, 0.5, 0.35); if (a <= 0) return;
  const slide = (1 - eOut((t - o.t0) / 0.5)) * -120;
  ctx.save(); ctx.globalAlpha = a;
  const x = 110 + slide, y = H - 290 + (o.dy || 0);
  ctx.font = font(50, 700); const tw = ctx.measureText(o.title).width;
  ctx.font = font(29, 500, INTER); const sw = o.sub ? ctx.measureText(o.sub).width : 0;
  const bw = Math.max(tw, sw) + 70;
  ctx.fillStyle = C.red; ctx.fillRect(x, y, 14, o.sub ? 128 : 78);
  ctx.fillStyle = 'rgba(255,255,255,0.96)'; ctx.fillRect(x + 14, y, bw * eOut((t - o.t0) / 0.6), 78);
  ctx.fillStyle = C.navy; ctx.font = font(50, 700); ctx.textBaseline = 'middle'; ctx.fillText(o.title, x + 40, y + 41);
  if (o.sub) { ctx.fillStyle = C.panel; ctx.fillRect(x + 14, y + 78, (sw + 60) * eOut((t - o.t0 - 0.15) / 0.6), 50); ctx.fillStyle = '#E8ECF3'; ctx.font = font(29, 500, INTER); ctx.fillText(o.sub, x + 40, y + 104); }
  ctx.restore();
};
OV.headline = (o, t) => {
  const a = env(t, o.t0, o.t1, 0.4, 0.35); if (a <= 0) return;
  const size = o.size || 96; const lines = o.lines;
  const y0 = (o.y ?? H / 2) - (lines.length - 1) * size * 0.6;
  if (o.scrim !== false) { ctx.save(); ctx.globalAlpha = a * 0.55; const g = ctx.createLinearGradient(0, y0 - 300, 0, y0 + lines.length * size + 200); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.5, 'rgba(0,0,0,0.9)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, y0 - 300, W, lines.length * size + 500); ctx.restore(); }
  lines.forEach((ln, i) => {
    const li = clamp((t - o.t0 - i * (o.stagger ?? 0.18)) / 0.5); const la = Math.min(eOut(li), env(t, o.t0, o.t1, 0.01, 0.35));
    if (la <= 0) return;
    const txt = typeof ln === 'string' ? ln : ln.text; const col = typeof ln === 'string' ? (i === 0 && o.accentFirst ? C.gold : C.white) : ln.color;
    const sz = typeof ln === 'string' ? size : (ln.size || size);
    ctx.save(); ctx.globalAlpha = la; ctx.font = font(sz, 700); ctx.letterSpacing = (o.ls ?? 2) + 'px';
    ctx.textAlign = o.align || 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = col;
    ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 24;
    const x = o.align === 'left' ? (o.x || 120) : (o.x || W / 2);
    ctx.fillText(txt, x, y0 + i * sz * 1.2 + (1 - eOut(li)) * 40);
    ctx.restore();
  });
};
OV.tag = (o, t) => { // qizil yorliq, masalan "MUHIM"
  const a = env(t, o.t0, o.t1, 0.25, 0.3); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.font = font(o.size || 36, 700); ctx.letterSpacing = '3px';
  const tw = ctx.measureText(o.text).width; const x = o.x ?? (W - tw) / 2, y = o.y ?? 200;
  ctx.fillStyle = o.color || C.red; ctx.fillRect(x - 22, y - 34, tw * eOut((t - o.t0) / 0.35) + 44, 68);
  ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(o.text, x, y + 2); ctx.restore();
};
OV.date = (o, t) => {
  const a = env(t, o.t0, o.t1, 0.4, 0.35); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.font = font(40, 700); ctx.letterSpacing = '2px';
  const tw = ctx.measureText(o.text).width; const x = W - 110 - tw, y = 150;
  ctx.fillStyle = C.panel; ctx.fillRect(x - 30, y - 38, tw + 60, 76);
  ctx.fillStyle = C.gold; ctx.fillRect(x - 30, y + 34, (tw + 60) * eOut((t - o.t0) / 0.7), 5);
  ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(o.text, x, y + 2); ctx.restore();
};
OV.list = (o, t) => {
  const a0 = env(t, o.t0, o.t1, 0.3, 0.35); if (a0 <= 0) return;
  const x = o.x ?? 130; let y = o.y ?? 300; const size = o.size || 52;
  if (o.title) { ctx.save(); ctx.globalAlpha = a0; ctx.font = font(30, 700); ctx.letterSpacing = '4px'; ctx.fillStyle = C.gold; ctx.textBaseline = 'middle'; ctx.fillText(o.title, x, y); ctx.restore(); y += 70; }
  o.items.forEach((it, i) => {
    const at = o.t0 + (it.at ?? i * 0.6); const p = clamp((t - at) / 0.45); if (p <= 0) return;
    const a = Math.min(eOut(p), a0);
    ctx.save(); ctx.globalAlpha = a; ctx.font = font(size, 700); const txt = it.text || it;
    const tw = ctx.measureText(txt).width;
    const dx = (1 - eOut(p)) * -60;
    ctx.fillStyle = C.panel; ctx.fillRect(x + dx, y + i * (size * 1.55) - size * 0.68, tw + 90, size * 1.36);
    ctx.fillStyle = it.color || C.red; ctx.fillRect(x + dx, y + i * (size * 1.55) - size * 0.68, 12, size * 1.36);
    ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(txt, x + dx + 40, y + i * (size * 1.55) + 2);
    ctx.restore();
  });
};
OV.section = (o, t) => { // bo'lim sarlavhasi
  const a = env(t, o.t0, o.t1, 0.35, 0.35); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a * 0.6; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.restore();
  const p = eOut((t - o.t0) / 0.6);
  ctx.save(); ctx.globalAlpha = a;
  const y = H / 2;
  ctx.fillStyle = C.red; ctx.fillRect(W / 2 - 500 * p, y - 120, 1000 * p, 8);
  if (o.num) { ctx.font = font(150, 700); ctx.fillStyle = C.gold; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(o.num, W / 2, y - 210); }
  ctx.font = font(o.size || 104, 700); ctx.letterSpacing = '3px'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(o.text, W / 2, y + (1 - p) * 30);
  if (o.sub) { ctx.font = font(36, 500, INTER); ctx.letterSpacing = '0px'; ctx.fillStyle = '#D0D7E4'; ctx.fillText(o.sub, W / 2, y + 100); }
  ctx.restore();
};
OV.title = (o, t) => { // asosiy sarlavha
  const a = env(t, o.t0, o.t1, 0.4, 0.5); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a * 0.7; const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, 'rgba(0,0,0,0.95)'); g.addColorStop(0.75, 'rgba(0,0,0,0.3)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
  const p1 = eOut((t - o.t0) / 0.6), p2 = eOut((t - o.t0 - 0.25) / 0.6), p3 = eOut((t - o.t0 - 0.6) / 0.6);
  ctx.save(); ctx.globalAlpha = a; ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = C.red; ctx.fillRect(120, 330, 260 * p1, 54);
  ctx.font = font(32, 700); ctx.letterSpacing = '4px'; ctx.fillStyle = '#fff'; ctx.fillText(o.kicker, 138, 369);
  ctx.font = font(118, 700); ctx.letterSpacing = '1px';
  o.lines.forEach((ln, i) => { ctx.globalAlpha = a * p2; ctx.fillStyle = i === o.lines.length - 1 ? C.gold : '#fff'; ctx.fillText(ln, 120 + (1 - p2) * -50, 520 + i * 130); });
  ctx.globalAlpha = a * p3; ctx.font = font(40, 500, INTER); ctx.letterSpacing = '0px'; ctx.fillStyle = '#DCE2EC'; ctx.fillText(o.sub, 124, 520 + o.lines.length * 130 + 10);
  ctx.restore();
};
OV.card = (o, t) => { // iqtibos kartochkasi
  const a = env(t, o.t0, o.t1, 0.45, 0.35); if (a <= 0) return;
  const x = o.x ?? 120, w = o.w ?? 1100; const size = o.size || 50;
  ctx.save(); ctx.font = font(size, 700); const lines = wrap(o.text, w - 120);
  const h = 120 + lines.length * size * 1.25 + (o.src ? 70 : 0) + (o.head ? 60 : 0);
  const y = o.y ?? (H - h) / 2 - 40; const dy = (1 - eOut((t - o.t0) / 0.5)) * 40;
  ctx.globalAlpha = a; ctx.fillStyle = 'rgba(8,16,31,0.9)'; rr(x, y + dy, w, h, 10); ctx.fill();
  ctx.fillStyle = o.color || C.red; ctx.fillRect(x, y + dy, 12, h);
  let yy = y + dy + 70;
  if (o.head) { ctx.font = font(30, 700); ctx.letterSpacing = '3px'; ctx.fillStyle = o.color || C.gold; ctx.textBaseline = 'middle'; ctx.fillText(o.head, x + 60, yy - 10); yy += 60; }
  if (o.quote) { ctx.font = font(170, 700); ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.fillText('“', x + w - 150, y + dy + 120); }
  ctx.font = font(size, 700); ctx.letterSpacing = '0.5px'; ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle';
  lines.forEach((ln, i) => { const p = clamp((t - o.t0 - 0.2 - i * 0.12) / 0.4); ctx.globalAlpha = a * eOut(p); ctx.fillText(ln, x + 60, yy + i * size * 1.25); });
  if (o.src) { ctx.globalAlpha = a; ctx.font = font(28, 500, INTER); ctx.letterSpacing = '0px'; ctx.fillStyle = C.grey; ctx.fillText(o.src, x + 60, yy + lines.length * size * 1.25 + 30); }
  ctx.restore();
};
OV.counter = (o, t) => {
  const a = env(t, o.t0, o.t1, 0.3, 0.35); if (a <= 0) return;
  const v = Math.round(lerp(o.from, o.to, eOut((t - o.t0) / (o.dur || 1.6))));
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 30;
  ctx.font = font(300, 700); ctx.fillStyle = '#fff'; ctx.fillText(v + (o.suffix || ''), W / 2, H / 2 - 60);
  ctx.font = font(64, 700); ctx.letterSpacing = '6px'; ctx.fillStyle = C.gold; ctx.fillText(o.label, W / 2, H / 2 + 140);
  ctx.restore();
};
OV.tribunals = (o, t) => { // vaqt chizig'i: tribunallar va XJS
  const a = env(t, o.t0, o.t1, 0.4, 0.4); if (a <= 0) return;
  const X0 = 200, X1 = 1720, Y0 = 1990, Y1 = 2030; const yx = y => lerp(X0, X1, (y - Y0) / (Y1 - Y0));
  ctx.save(); ctx.globalAlpha = a;
  ctx.font = font(44, 700); ctx.letterSpacing = '4px'; ctx.fillStyle = C.gold; ctx.textBaseline = 'middle'; ctx.fillText(o.head, X0, 180);
  ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(X0, 860); ctx.lineTo(X1, 860); ctx.stroke();
  for (let y = 1990; y <= 2030; y += 5) { const x = yx(y); ctx.beginPath(); ctx.moveTo(x, 850); ctx.lineTo(x, 870); ctx.stroke(); ctx.font = font(30, 500, INTER); ctx.fillStyle = C.grey; ctx.textAlign = 'center'; ctx.fillText(y, x, 905); }
  ctx.textAlign = 'left';
  o.bars.forEach((b, i) => {
    const p = eIO((t - o.t0 - b.at) / 1.2); if (p <= 0) return;
    const y = 330 + i * 170; const x0 = yx(b.from), x1 = yx(b.to ?? 2030);
    ctx.fillStyle = b.color; ctx.globalAlpha = a * 0.95; ctx.fillRect(x0, y, (x1 - x0) * p, 70);
    if (!b.to && p > 0.9) { ctx.beginPath(); ctx.moveTo(x1, y - 14); ctx.lineTo(x1 + 50, y + 35); ctx.lineTo(x1, y + 84); ctx.fill(); }
    ctx.globalAlpha = a * clamp((p - 0.2) / 0.3); ctx.fillStyle = '#fff'; ctx.font = font(40, 700); ctx.fillText(b.label, x0 + 22, y + 36);
    ctx.font = font(30, 500, INTER); ctx.fillStyle = '#D8DEEA'; ctx.fillText(b.sub, x0, y + 108);
  });
  ctx.restore();
};
OV.flow = (o, t) => { // XJS orderi -> a'zo davlat -> hibs
  const a = env(t, o.t0, o.t1, 0.3, 0.35); if (a <= 0) return;
  const n = o.steps.length, bw = 470, gap = 120, total = n * bw + (n - 1) * gap, x0 = (W - total) / 2, y = H / 2 - 110;
  ctx.save(); ctx.globalAlpha = a;
  if (o.head) { ctx.font = font(44, 700); ctx.letterSpacing = '4px'; ctx.fillStyle = C.gold; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(o.head, W / 2, 230); }
  o.steps.forEach((s, i) => {
    const p = eBack((t - o.t0 - s.at) / 0.55); if (p <= 0) return;
    const x = x0 + i * (bw + gap);
    ctx.save(); ctx.translate(x + bw / 2, y + 110); ctx.scale(lerp(0.7, 1, clamp(p, 0, 1.2)), lerp(0.7, 1, clamp(p, 0, 1.2))); ctx.globalAlpha = a * clamp(p);
    ctx.fillStyle = 'rgba(15,28,54,0.95)'; rr(-bw / 2, -110, bw, 220, 14); ctx.fill();
    ctx.strokeStyle = s.color || C.blue; ctx.lineWidth = 4; ctx.stroke();
    ctx.font = font(76, 700); ctx.fillStyle = s.color || C.blue; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(i + 1), 0, -50);
    ctx.font = font(42, 700); ctx.fillStyle = '#fff'; ctx.fillText(s.text, 0, 30);
    if (s.sub) { ctx.font = font(26, 500, INTER); ctx.fillStyle = C.grey; ctx.fillText(s.sub, 0, 78); }
    ctx.restore();
    if (i > 0) { const q = eOut((t - o.t0 - s.at + 0.3) / 0.4); ctx.strokeStyle = '#fff'; ctx.lineWidth = 5; const ax = x - gap + 20; ctx.beginPath(); ctx.moveTo(ax, y + 110); ctx.lineTo(ax + (gap - 40) * q, y + 110); ctx.stroke(); if (q > 0.95) { ctx.beginPath(); ctx.moveTo(x - 30, y + 95); ctx.lineTo(x - 18, y + 110); ctx.lineTo(x - 30, y + 125); ctx.stroke(); } }
  });
  if (o.note) { const p = clamp((t - o.t0 - o.note.at) / 0.5); ctx.globalAlpha = a * p; ctx.font = font(40, 500, INTER); ctx.fillStyle = '#E6EAF2'; ctx.textAlign = 'center'; ctx.fillText(o.note.text, W / 2, y + 340); }
  ctx.restore();
};
OV.milestones = (o, t) => { // gorizontal sanalar (Tojikiston tarixi / voqealar tezlashdi)
  const a = env(t, o.t0, o.t1, 0.35, 0.35); if (a <= 0) return;
  const n = o.items.length, x0 = 200, x1 = W - 200, y = o.y ?? 700;
  ctx.save(); ctx.globalAlpha = a;
  if (o.head) { ctx.font = font(58, 700); ctx.letterSpacing = '3px'; ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.shadowColor = 'rgba(0,0,0,.8)'; ctx.shadowBlur = 20; ctx.fillText(o.head, x0, y - 330); ctx.shadowBlur = 0; }
  const lastAt = o.items[n - 1].at; const lp = eIO((t - o.t0 - o.items[0].at) / Math.max(0.5, lastAt - o.items[0].at + 0.5));
  ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
  ctx.strokeStyle = C.gold; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(lerp(x0, x1, lp), y); ctx.stroke();
  o.items.forEach((it, i) => {
    const x = lerp(x0 + 120, x1 - 120, n === 1 ? 0.5 : i / (n - 1)); const p = eBack((t - o.t0 - it.at) / 0.5); if (p <= 0) return;
    const col = it.color || C.gold;
    ctx.save(); ctx.globalAlpha = a * clamp(p);
    ctx.beginPath(); ctx.arc(x, y, 20 * clamp(p, 0, 1.2), 0, Math.PI * 2); ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 4; ctx.stroke();
    const cw = 480, ch = 230, cy = y - 60 - ch + (1 - clamp(p)) * 30;
    ctx.fillStyle = 'rgba(8,16,31,0.92)'; rr(x - cw / 2, cy, cw, ch, 10); ctx.fill(); ctx.fillStyle = col; ctx.fillRect(x - cw / 2, cy, cw, 8);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = font(50, 700); ctx.fillStyle = col; ctx.fillText(it.date, x, cy + 60);
    ctx.font = font(31, 600, INTER); ctx.fillStyle = '#fff'; wrap(it.text, cw - 50).forEach((l, k) => ctx.fillText(l, x, cy + 128 + k * 40));
    ctx.restore();
  });
  ctx.restore();
};
function wrapC(text, x, y, maxW, lh) { const lines = wrap(text, maxW); lines.forEach((l, i) => ctx.fillText(l, x, y + (i - (lines.length - 1) / 2) * lh)); }
OV.progress = (o, t) => { // 127-modda: bir yillik muddat
  const a = env(t, o.t0, o.t1, 0.35, 0.35); if (a <= 0) return;
  const x0 = 260, x1 = W - 260, y = o.y ?? 620; const p = eIO((t - o.t0 - (o.barAt || 0.3)) / (o.barDur || 3));
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; rr(x0, y - 22, x1 - x0, 44, 22); ctx.fill();
  const g = ctx.createLinearGradient(x0, 0, x1, 0); g.addColorStop(0, C.gold); g.addColorStop(1, C.red);
  ctx.fillStyle = g; rr(x0, y - 22, Math.max(44, (x1 - x0) * p), 44, 22); ctx.fill();
  ctx.font = font(48, 700); ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle';
  ctx.textAlign = 'left'; ctx.fillText(o.left, x0, y + 80); ctx.textAlign = 'right'; ctx.fillText(o.right, x1, y + 80);
  ctx.font = font(28, 500, INTER); ctx.fillStyle = C.grey; ctx.textAlign = 'left'; ctx.fillText(o.leftSub, x0, y + 128); ctx.textAlign = 'right'; ctx.fillText(o.rightSub, x1, y + 128);
  if (o.mid) { ctx.globalAlpha = a * clamp((t - o.t0 - (o.midAt || 1)) / 0.5); ctx.textAlign = 'center'; ctx.font = font(40, 700); ctx.fillStyle = C.gold; ctx.fillText(o.mid, W / 2, y - 80); }
  ctx.restore();
};
OV.doc = (o, t) => { // xabarnoma hujjati grafikasi
  const a = env(t, o.t0, o.t1, 0.4, 0.35); if (a <= 0) return;
  const p = eOut((t - o.t0) / 0.7); const x = o.x ?? 1150, y = 170 + (1 - p) * 60, w = 620, h = 760;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x + w / 2, y + h / 2); ctx.rotate(-0.025); ctx.translate(-w / 2, -h / 2);
  ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 40; ctx.fillStyle = '#F4F1EA'; ctx.fillRect(0, 0, w, h); ctx.shadowBlur = 0;
  ctx.fillStyle = '#1D3A6E'; ctx.font = font(30, 700); ctx.textAlign = 'center'; ctx.fillText(o.org, w / 2, 70);
  ctx.fillStyle = '#333'; ctx.font = font(22, 600, INTER); ctx.fillText(o.ref, w / 2, 110);
  ctx.fillStyle = '#111'; ctx.font = font(44, 700); ctx.fillText(o.heading, w / 2, 190);
  ctx.fillStyle = '#BBB'; for (let i = 0; i < 12; i++) ctx.fillRect(60, 250 + i * 34, (i % 4 === 3 ? 300 : 500), 12);
  (o.lines || []).forEach((l, i) => { ctx.fillStyle = '#222'; ctx.font = font(26, 600, INTER); ctx.textAlign = 'left'; ctx.fillText(l, 60, 690 - (o.lines.length - 1 - i) * 36); });
  const sp = eBack((t - o.t0 - (o.stampAt || 1.2)) / 0.4);
  if (sp > 0) { ctx.save(); ctx.translate(w - 170, h - 230); ctx.rotate(-0.25); ctx.scale(lerp(2, 1, clamp(sp)), lerp(2, 1, clamp(sp))); ctx.globalAlpha = a * clamp(sp) * 0.85; ctx.strokeStyle = C.red; ctx.lineWidth = 6; ctx.strokeRect(-150, -50, 300, 100); ctx.fillStyle = C.red; ctx.font = font(44, 700); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(o.stamp, 0, 4); ctx.restore(); }
  ctx.restore();
};
OV.big127 = (o, t) => {
  const a = env(t, o.t0, o.t1, 0.4, 0.35); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = font(40, 700); ctx.letterSpacing = '6px'; ctx.fillStyle = C.gold; ctx.fillText(o.kicker, W / 2, 230);
  const p = eBack((t - o.t0) / 0.6); ctx.save(); ctx.translate(W / 2, 400); ctx.scale(clamp(p, 0, 1.2), clamp(p, 0, 1.2)); ctx.font = font(220, 700); ctx.fillStyle = '#fff'; ctx.letterSpacing = '4px'; ctx.fillText(o.big, 0, 0); ctx.restore();
  ctx.font = font(48, 600, INTER); ctx.letterSpacing = '0px'; ctx.fillStyle = '#E6EAF2'; ctx.globalAlpha = a * clamp((t - o.t0 - 0.6) / 0.5); wrapC(o.text, W / 2, 600, 1400, 60);
  ctx.restore();
};
OV.persons = (o, t) => { // ism kartochkalari (order)
  o.items.forEach((it, i) => {
    const a = env(t, o.t0 + it.at, o.t1, 0.45, 0.35); if (a <= 0) return;
    const p = eOut((t - o.t0 - it.at) / 0.5); const x = W - 760 + (1 - p) * 80, y = 230 + i * 210;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(8,16,31,0.92)'; ctx.fillRect(x, y, 650, 170); ctx.fillStyle = C.red; ctx.fillRect(x, y, 12, 170);
    ctx.font = font(26, 700); ctx.letterSpacing = '3px'; ctx.fillStyle = C.red; ctx.textBaseline = 'middle'; ctx.fillText(it.kicker, x + 40, y + 38);
    ctx.font = font(50, 700); ctx.letterSpacing = '1px'; ctx.fillStyle = '#fff'; ctx.fillText(it.name, x + 40, y + 92);
    ctx.font = font(26, 500, INTER); ctx.letterSpacing = '0px'; ctx.fillStyle = C.grey; ctx.fillText(it.role, x + 40, y + 140); ctx.restore();
  });
};
OV.legend = (o, t) => {
  const a = env(t, o.t0, o.t1, 0.4, 0.35); if (a <= 0) return;
  const x = o.x ?? 110, y = o.y ?? 160;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(5,10,22,0.85)';
  ctx.font = font(30, 600, INTER); const w = Math.max(...o.items.map(i => ctx.measureText(i.text).width)) + 110;
  const h = 40 + o.items.length * 54 + (o.title ? 56 : 0); rr(x, y, w, h, 10); ctx.fill();
  let yy = y + 44; if (o.title) { ctx.font = font(32, 700); ctx.letterSpacing = '3px'; ctx.fillStyle = C.gold; ctx.textBaseline = 'middle'; ctx.fillText(o.title, x + 30, yy); yy += 56; }
  o.items.forEach((it, i) => { const ia = clamp((t - o.t0 - (it.at || 0)) / 0.4); ctx.globalAlpha = a * ia; ctx.fillStyle = it.color; rr(x + 30, yy + i * 54 - 15, 30, 30, 5); ctx.fill(); ctx.font = font(30, 600, INTER); ctx.letterSpacing = '0px'; ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(it.text, x + 78, yy + i * 54 + 1); });
  ctx.restore();
};
OV.split = (o, t) => { // yakuniy savol: ikki tomon
  const a = env(t, o.t0, o.t1, 0.4, 0.4); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  [[o.left, W * 0.25, o.leftAt || 0, C.blue], [o.right, W * 0.75, o.rightAt || 0, C.red]].forEach(([txt, x, at, col]) => {
    const p = eOut((t - o.t0 - at) / 0.5); if (p <= 0) return;
    ctx.globalAlpha = a * p; ctx.fillStyle = 'rgba(5,10,22,0.82)'; ctx.fillRect(x - 380, H / 2 - 130 + (1 - p) * 40, 760, 260); ctx.fillStyle = col; ctx.fillRect(x - 380, H / 2 - 130 + (1 - p) * 40, 760, 10);
    ctx.font = font(66, 700); ctx.fillStyle = '#fff'; wrapC(txt, x, H / 2 + 5 + (1 - p) * 40, 680, 80);
  });
  ctx.globalAlpha = a * clamp((t - o.t0 - (o.vsAt || 0)) / 0.4); ctx.beginPath(); ctx.arc(W / 2, H / 2, 70, 0, Math.PI * 2); ctx.fillStyle = C.gold; ctx.fill();
  ctx.font = font(56, 700); ctx.fillStyle = C.navy; ctx.fillText('YOKI', W / 2, H / 2 + 2);
  ctx.restore();
};
OV.endcard = (o, t) => {
  const a = env(t, o.t0, o.t1, 0.5, 0.01); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(4,8,18,0.88)'; ctx.fillRect(0, 0, W, H);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = font(44, 700); ctx.letterSpacing = '6px'; ctx.fillStyle = C.gold; ctx.fillText(o.kicker, W / 2, 380);
  ctx.font = font(104, 700); ctx.letterSpacing = '2px'; ctx.fillStyle = '#fff'; ctx.fillText(o.text, W / 2, 500);
  const p = eOut((t - o.t0 - 0.3) / 0.8); ctx.fillStyle = C.red; ctx.fillRect(W / 2 - 300 * p, 590, 600 * p, 8);
  ctx.font = font(40, 500, INTER); ctx.letterSpacing = '0px'; ctx.fillStyle = '#C9D1DF'; ctx.fillText(o.sub, W / 2, 680);
  ctx.restore();
};
OV.flash = (o, t) => { const d = t - o.t0; if (d < 0 || d > (o.dur || 0.35)) return; ctx.save(); ctx.globalAlpha = (1 - d / (o.dur || 0.35)) * (o.alpha || 0.9); ctx.fillStyle = o.color || '#fff'; ctx.fillRect(0, 0, W, H); ctx.restore(); };
OV.note = (o, t) => { // kichik izoh (masalan "Kadr: ... illyustratsiya")
  const a = env(t, o.t0, o.t1, 0.4, 0.3); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.font = font(26, 600, INTER); const tw = ctx.measureText(o.text).width;
  const x = o.x ?? 110, y = o.y ?? 120; ctx.fillStyle = 'rgba(5,10,22,0.78)'; rr(x, y - 24, tw + 36, 48, 6); ctx.fill();
  ctx.fillStyle = '#E3E8F0'; ctx.textBaseline = 'middle'; ctx.fillText(o.text, x + 18, y + 1); ctx.restore();
};

// ---------- doimiy elementlar ----------
function drawBug(t) {
  if (t < CONF.bugFrom || t > CONF.bugTo) return;
  const a = clamp((t - CONF.bugFrom) / 0.6) * clamp((CONF.bugTo - t) / 0.6);
  ctx.save(); ctx.globalAlpha = a * 0.92; const x = 70, y = 56;
  ctx.fillStyle = C.red; ctx.fillRect(x, y, 16, 54);
  ctx.fillStyle = 'rgba(8,16,31,0.82)'; ctx.fillRect(x + 16, y, 236, 54);
  ctx.font = font(32, 700); ctx.letterSpacing = '3px'; ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(CONF.bug, x + 32, y + 29);
  ctx.restore();
}
function drawTicker(t) {
  if (t < CONF.tickFrom || t > CONF.tickTo) return;
  const a = clamp((t - CONF.tickFrom) / 0.5) * clamp((CONF.tickTo - t) / 0.5); const y = H - 64, h = 64;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(8,16,31,0.94)'; ctx.fillRect(0, y, W, h);
  ctx.font = font(30, 600, INTER); ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle';
  const txt = CONF.ticker; const tw = ctx.measureText(txt).width; let x = 330 - ((t - CONF.tickFrom) * 110) % tw;
  ctx.save(); ctx.beginPath(); ctx.rect(300, y, W - 300, h); ctx.clip();
  while (x < W) { ctx.fillText(txt, x, y + h / 2 + 1); x += tw; }
  ctx.restore();
  ctx.fillStyle = C.red; ctx.fillRect(0, y, 300, h); ctx.font = font(34, 700); ctx.letterSpacing = '3px'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.fillText(CONF.tickLabel, 150, y + h / 2 + 2);
  ctx.restore();
}
function drawCredit(text, t, a) {
  if (!text) return;
  const tickerOn = t >= CONF.tickFrom && t <= CONF.tickTo;
  ctx.save(); ctx.globalAlpha = a; ctx.font = font(24, 600, INTER); ctx.letterSpacing = '1px';
  const tw = ctx.measureText(text).width; const x = W - 70 - tw, y = H - (tickerOn ? 100 : 56);
  ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(x - 14, y - 20, tw + 28, 40);
  ctx.fillStyle = 'rgba(255,255,255,0.92)'; ctx.textBaseline = 'middle'; ctx.fillText(text, x, y + 1); ctx.restore();
}
function vignette() {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.5)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function creditOf(s) {
  if (s.credit !== undefined) return s.credit;
  if (s.type === 'video') return MAN[s.clip].credit;
  if (s.type === 'photo' || s.type === 'blurphoto') return 'FOTO: Kremlin.ru (CC BY 4.0)';
  if (s.type === 'map') return 'XARITA: Natural Earth (public domain)';
  return '';
}

// ---------- asosiy render ----------
async function drawScene(s, t) {
  if (s.type === 'video') return drawVideo(s, t);
  if (s.type === 'photo') return drawPhoto(s, t);
  if (s.type === 'blurphoto') return drawBlurPhoto(s, t);
  if (s.type === 'map') return drawMap(s, t);
  if (s.type === 'graphic') return drawGraphicBg(t, s);
}
window.ready = (async () => {
  MAN = await (await fetch('clips_manifest.json')).json();
  WORLD = await (await fetch('assets/world.json')).json();
  await document.fonts.load('700 40px Oswald'); await document.fonts.load('600 40px Inter'); await document.fonts.load('500 40px Inter');
  return true;
})();
window.renderAt = async (t) => {
  await window.ready;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.letterSpacing = '0px'; ctx.textAlign = 'left';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const active = SCENES.filter(s => t >= s.t0 - (s.xf || 0) && t < s.t1);
  let creditTxt = '', creditA = 0;
  for (const s of active) {
    const a = s.xf ? clamp((t - (s.t0 - s.xf)) / s.xf) : 1;
    ctx.save(); ctx.globalAlpha = 1;
    if (a < 1) { // ustma-ust o'tish: avval vaqtinchalik qatlamga chizamiz
      const off = window._off || (window._off = Object.assign(document.createElement('canvas'), { width: W, height: H }));
      const octx = off.getContext('2d');
      octx.drawImage(cv, 0, 0); // hozirgi holat
      await drawScene(s, t);
      ctx.globalAlpha = 1 - a; ctx.drawImage(off, 0, 0); ctx.globalAlpha = 1;
    } else await drawScene(s, t);
    ctx.restore();
    if (s.dim) { ctx.fillStyle = `rgba(0,0,0,${s.dim})`; ctx.fillRect(0, 0, W, H); }
    const c = creditOf(s); if (c) { creditTxt = c; creditA = clamp((t - s.t0) / 0.4) * clamp((s.t1 - t) / 0.3); }
  }
  vignette();
  for (const o of OVERLAYS) { if (t >= o.t0 - 0.05 && t <= o.t1 + 0.05) { ctx.save(); OV[o.type](o, t); ctx.restore(); } }
  drawBug(t); drawTicker(t); drawCredit(creditTxt, t, creditA);
  // keyingi kadrlarni oldindan yuklash
  for (const s of SCENES) if (s.type === 'video' && t + 0.4 >= s.t0 && t < s.t1) { for (let k = 1; k <= 3; k++) loadImg(frameUrl(s.clip, clipFrameIdx(s, t + k / FPS))); }
  return true;
};
window.grab = (q = 0.92) => cv.toDataURL('image/jpeg', q);
