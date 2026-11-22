// Umumiy yadro: matematika, effektlar, tipografiya, islomiy naqshlar, zarrachalar.
// Hamma narsa vaqt (t) ning sof funksiyasi: istalgan kadrni istalgan tartibda chizish mumkin.
export const W = 1920, H = 1080;

export const C = {
  night: '#030714', navy: '#071430', navy2: '#0c2148', blue: '#123a6b',
  turq: '#2ec4b6', turq2: '#7fe3d8', emerald: '#0f7a5a', emerald2: '#1fa77d',
  gold: '#d4a64a', gold2: '#f3d58c', gold3: '#fff3cf', bronze: '#8a5a1c', ink: '#1a1208',
  parch: '#e9d9b0', parch2: '#cdb47e',
};

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const inv = (a, b, x) => clamp((x - a) / (b - a));
export const smooth = (a, b, x) => { const t = inv(a, b, x); return t * t * (3 - 2 * t); };
export const ease = {
  inOut: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  outBack: t => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
};
export const seg = (t, a, b, fn = ease.inOut) => fn(inv(a, b, t));

export function rng(seed) {
  let s = seed >>> 0;
  return () => { s += 0x6D2B79F5; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
// 1D / 2D qiymat shovqini
const PERM = (() => { const r = rng(7), p = [...Array(256).keys()]; for (let i = 255; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [p[i], p[j]] = [p[j], p[i]]; } return p.concat(p); })();
const grad = (h, x, y) => ((h & 1) ? -x : x) + ((h & 2) ? -y : y);
export function noise2(x, y) {
  const X = Math.floor(x) & 255, Y = Math.floor(y) & 255; x -= Math.floor(x); y -= Math.floor(y);
  const u = x * x * (3 - 2 * x), v = y * y * (3 - 2 * y);
  const a = PERM[X] + Y, b = PERM[X + 1] + Y;
  return lerp(lerp(grad(PERM[a], x, y), grad(PERM[b], x - 1, y), u), lerp(grad(PERM[a + 1], x, y - 1), grad(PERM[b + 1], x - 1, y - 1), u), v);
}
export const fbm = (x, y, o = 4) => { let s = 0, a = .5, f = 1; for (let i = 0; i < o; i++) { s += a * noise2(x * f, y * f); f *= 2; a *= .5; } return s; };

export function mkCanvas(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; }

// ---------- Spritlar ----------
const spriteCache = new Map();
export function glowSprite(color = '255,214,140', size = 128, hard = .15) {
  const k = color + size + hard; if (spriteCache.has(k)) return spriteCache.get(k);
  const c = mkCanvas(size, size), g = c.getContext('2d');
  const gr = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gr.addColorStop(0, `rgba(${color},1)`); gr.addColorStop(hard, `rgba(${color},.55)`);
  gr.addColorStop(.45, `rgba(${color},.12)`); gr.addColorStop(1, `rgba(${color},0)`);
  g.fillStyle = gr; g.fillRect(0, 0, size, size); spriteCache.set(k, c); return c;
}
export function glow(ctx, x, y, r, a = 1, color, hard) {
  if (a <= 0 || r <= 0) return; const s = glowSprite(color, 128, hard);
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = Math.min(1, a);
  ctx.drawImage(s, x - r, y - r, 2 * r, 2 * r); ctx.restore();
}

// ---------- Oltin chang zarrachalari (holatsiz) ----------
const DUST = (() => { const r = rng(11), a = []; for (let i = 0; i < 900; i++) a.push({ x: r(), y: r(), z: r(), ph: r() * 6.28, sp: .3 + r(), tw: r() }); return a; })();
export function dust(ctx, t, o = {}) {
  const { n = 300, alpha = 1, vx = .004, vy = -.01, color = '255,210,130', size = 1, zoom = 0, cx = W / 2, cy = H / 2, swirl = 0 } = o;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const spr = glowSprite(color, 64, .25);
  for (let i = 0; i < Math.min(n, DUST.length); i++) {
    const p = DUST[i], depth = .25 + p.z * 1.5;
    let x = ((p.x + vx * t * p.sp * depth + .03 * Math.sin(t * .4 + p.ph)) % 1 + 1) % 1;
    let y = ((p.y + vy * t * p.sp * depth + .02 * Math.cos(t * .33 + p.ph)) % 1 + 1) % 1;
    let X = x * (W + 200) - 100, Y = y * (H + 200) - 100;
    if (zoom) { const k = 1 + zoom * depth; X = cx + (X - cx) * k; Y = cy + (Y - cy) * k; }
    if (swirl) { const dx = X - cx, dy = Y - cy, an = swirl * depth * .3; X = cx + dx * Math.cos(an) - dy * Math.sin(an); Y = cy + dx * Math.sin(an) + dy * Math.cos(an); }
    const tw = .55 + .45 * Math.sin(t * (1.5 + p.tw * 3) + p.ph);
    const r = (1.2 + depth * 3.2) * size;
    ctx.globalAlpha = clamp(alpha * tw * (.35 + .65 * (1 - Math.abs(depth - .9) / 1.2)));
    ctx.drawImage(spr, X - r * 3, Y - r * 3, r * 6, r * 6);
  }
  ctx.restore();
}

// ---------- Islomiy geometrik naqshlar ----------
// {n/k} yulduz ko‘pburchak
export function starPoly(n, k, R, rot = 0) {
  const pts = []; for (let i = 0; i < n; i++) { const a = rot + i * 2 * Math.PI / n; pts.push([R * Math.cos(a), R * Math.sin(a)]); }
  const lines = []; for (let i = 0; i < n; i++) lines.push([pts[i], pts[(i + k) % n]]); return lines;
}
// Rozetta: ichki n-qirrali yulduz + gulbarglar (klassik 8/12/16 yulduzli rozetta)
export function rosette(n, R) {
  const L = [];
  const step = Math.PI * 2 / n;
  const rIn = R * .38, rMid = R * .62;
  for (let i = 0; i < n; i++) {
    const a = i * step, b = a + step / 2, c = a + step;
    const p = (r, an) => [r * Math.cos(an), r * Math.sin(an)];
    // yulduz uchlari
    L.push([p(rIn, b - step / 2), p(rMid, b)], [p(rMid, b), p(rIn, b + step / 2)]);
    // gulbarg
    L.push([p(rMid, b), p(R * .82, a + step)], [p(R * .82, a), p(rMid, b)]);
    L.push([p(R * .82, a), p(R, b - step * .25)], [p(R, b - step * .25), p(R, b + step * .25)], [p(R, b + step * .25), p(R * .82, c)]);
  }
  L.push(...starPoly(n, Math.floor(n / 3), rIn, step / 2));
  return L;
}
// Xotam (8 qirrali yulduz va xochlar) to‘ri
export function khatamTile(cx, cy, s) {
  const L = [], r = s * .5;
  for (const rot of [0, Math.PI / 4]) {
    const pts = []; for (let i = 0; i < 4; i++) { const a = rot + Math.PI / 4 + i * Math.PI / 2; pts.push([cx + r * Math.SQRT2 * .76 * Math.cos(a), cy + r * Math.SQRT2 * .76 * Math.sin(a)]); }
    for (let i = 0; i < 4; i++) L.push([pts[i], pts[(i + 1) % 4]]);
  }
  return L;
}
// Chiziqlarni markazdan tashqariga qarab bosqichma-bosqich chizish
export function drawLines(ctx, lines, prog, o = {}) {
  const { cx = 0, cy = 0, width = 1.4, color = C.gold2, glowA = .9, origin = [0, 0], spread = 1 } = o;
  if (prog <= 0) return;
  ctx.save(); ctx.translate(cx, cy); ctx.lineCap = 'round';
  let maxd = 1; for (const [a] of lines) maxd = Math.max(maxd, Math.hypot(a[0] - origin[0], a[1] - origin[1]));
  const path = new Path2D();
  for (const [a, b] of lines) {
    const da = Math.hypot(a[0] - origin[0], a[1] - origin[1]) / maxd, db = Math.hypot(b[0] - origin[0], b[1] - origin[1]) / maxd;
    const d0 = Math.min(da, db) * spread;
    const lp = clamp((prog * (1 + spread) - d0) / 1);
    if (lp <= 0) continue;
    const [s, e] = da <= db ? [a, b] : [b, a];
    path.moveTo(s[0], s[1]); path.lineTo(lerp(s[0], e[0], lp), lerp(s[1], e[1], lp));
  }
  ctx.strokeStyle = color; ctx.lineWidth = width;
  if (glowA > 0) { ctx.shadowColor = 'rgba(255,200,110,' + glowA + ')'; ctx.shadowBlur = width * 6; }
  ctx.stroke(path); ctx.restore();
}

// ---------- Tipografiya ----------
export const FONT = { title: '"Cinzel"', body: '"Cormorant"', ar: '"Amiri"', kufi: '"ReemKufi"', ruqaa: '"ArefRuqaa"' };
const titleCache = new Map();
// 3D bo‘rtma oltin harf (kesh)
function goldGlyph(ch, size, depth, S) {
  const k = ch + size + depth + S; if (titleCache.has(k)) return titleCache.get(k);
  const f = `900 ${size * S}px ${FONT.title}`;
  const m = mkCanvas(10, 10).getContext('2d'); m.font = f; const w = Math.ceil(m.measureText(ch).width) + 1;
  const pad = size * S * .5, dx = depth * S * .55, dy = depth * S * .85;
  const c = mkCanvas(w + pad * 2 + dx, size * S * 1.5 + pad + dy), g = c.getContext('2d');
  g.font = f; g.textBaseline = 'alphabetic';
  const bx = pad, by = pad * .5 + size * S * 1.05;
  // ekstruziya (orqa qatlamlar)
  for (let i = depth; i >= 1; i--) {
    const q = i / depth; g.fillStyle = `rgb(${Math.round(lerp(120, 40, q))},${Math.round(lerp(78, 22, q))},${Math.round(lerp(24, 8, q))})`;
    g.fillText(ch, bx + i * S * .55, by + i * S * .85);
  }
  // old yuz: metall oltin gradiyent
  const gr = g.createLinearGradient(0, by - size * S * .95, 0, by + size * S * .1);
  gr.addColorStop(0, '#fff6d6'); gr.addColorStop(.28, '#f2cf7a'); gr.addColorStop(.5, '#a8721f');
  gr.addColorStop(.62, '#e8bb5c'); gr.addColorStop(.85, '#fff0b8'); gr.addColorStop(1, '#b07c26');
  g.shadowColor = 'rgba(255,190,90,.55)'; g.shadowBlur = size * S * .12;
  g.fillStyle = gr; g.fillText(ch, bx, by); g.shadowBlur = 0;
  g.lineWidth = Math.max(1, size * S * .012); g.strokeStyle = 'rgba(255,248,220,.85)'; g.strokeText(ch, bx, by);
  const out = { c, w: w / S, ox: bx / S, oy: by / S, S }; titleCache.set(k, out); return out;
}
// Harfma-harf ochiladigan 3D sarlavha. prog 0..1, sweep 0..1 (yorug‘lik o‘tishi)
export function title3D(ctx, text, x, y, size, prog, o = {}) {
  const { S = 1, depth = 14, track = .08, sweep = -1, alpha = 1, spreadFrom = 1.0, blurMax = 14 } = o;
  const glyphs = [...text].map(ch => ch === ' ' ? null : goldGlyph(ch, size, depth, S));
  const m = mkCanvas(10, 10).getContext('2d'); m.font = `900 ${size}px ${FONT.title}`;
  const adv = [...text].map(ch => m.measureText(ch).width + size * track);
  const total = adv.reduce((a, b) => a + b, 0) - size * track;
  let px = x - total / 2;
  const n = glyphs.length;
  ctx.save();
  for (let i = 0; i < n; i++) {
    const gph = glyphs[i];
    if (gph) {
      const center = (n - 1) / 2, order = Math.abs(i - center) / Math.max(1, center);
      const lp = ease.out(clamp((prog * 1.6 - order * .6)));
      if (lp > 0) {
        const off = (1 - lp) * size * 1.2 * spreadFrom * Math.sign(i - center);
        const sc = lerp(1.35, 1, lp);
        ctx.globalAlpha = alpha * lp;
        const bl = (1 - lp) * blurMax; if (bl > .5) ctx.filter = `blur(${bl * S}px)`;
        const w = gph.c.width / gph.S, h = gph.c.height / gph.S;
        ctx.save(); ctx.translate(px + off + adv[i] / 2, y); ctx.scale(sc, sc);
        ctx.drawImage(gph.c, -adv[i] / 2 - gph.ox + size * track / 2, -gph.oy, w, h); ctx.restore();
        ctx.filter = 'none';
      }
    }
    px += adv[i];
  }
  ctx.restore();
  // yorug‘lik chizig‘i (specular sweep)
  if (sweep > 0 && sweep < 1) {
    const sx = x - total / 2 - 200 + (total + 400) * sweep;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = alpha * .9 * Math.sin(sweep * Math.PI);
    ctx.font = `900 ${size}px ${FONT.title}`; ctx.textBaseline = 'alphabetic';
    const gr = ctx.createLinearGradient(sx - 120, 0, sx + 120, 0);
    gr.addColorStop(0, 'rgba(255,240,200,0)'); gr.addColorStop(.5, 'rgba(255,250,230,.95)'); gr.addColorStop(1, 'rgba(255,240,200,0)');
    ctx.fillStyle = gr; let qx = x - total / 2;
    for (let i = 0; i < n; i++) { const ch = text[i]; if (ch !== ' ') ctx.fillText(ch, qx, y + size * .05); qx += adv[i]; }
    ctx.restore();
  }
  return total;
}
export function text(ctx, s, x, y, o = {}) {
  const { size = 28, font = FONT.body, weight = 500, color = C.gold2, align = 'center', alpha = 1, track = 0, glowA = 0, italic = false, base = 'alphabetic', dir } = o;
  if (alpha <= 0) return 0;
  ctx.save(); ctx.globalAlpha = clamp(alpha); ctx.font = `${italic ? 'italic ' : ''}${weight} ${size}px ${font}`;
  ctx.textAlign = align; ctx.textBaseline = base; ctx.fillStyle = color;
  if (dir) ctx.direction = dir;
  if (track) ctx.letterSpacing = track + 'px';
  if (glowA) { ctx.shadowColor = `rgba(255,200,110,${glowA})`; ctx.shadowBlur = size * .5; }
  ctx.fillText(s, x, y); const w = ctx.measureText(s).width; ctx.restore(); return w;
}
// Matnni harf bo‘yicha paydo qilish (pastdan, xiralikdan)
export function revealText(ctx, s, x, y, p, o = {}) {
  if (p <= 0) return;
  const blur = (1 - ease.out(clamp(p))) * 10;
  ctx.save(); if (blur > .4) ctx.filter = `blur(${blur * (o.S || 1)}px)`;
  text(ctx, s, x, y + (1 - ease.out(clamp(p))) * 18, { ...o, alpha: (o.alpha ?? 1) * clamp(p * 1.4) });
  ctx.restore();
}

// Golografik ma’lumot kartasi
export function infoCard(ctx, x, y, w, h, p, o = {}) {
  if (p <= 0) return;
  const { title = '', sub = '', body = '', year = '', S = 1, accent = C.turq } = o;
  const e = ease.out(clamp(p));
  ctx.save(); ctx.globalAlpha = clamp(p * 1.5) * (o.alpha ?? 1);
  ctx.translate(x, y + (1 - e) * 30);
  const g = ctx.createLinearGradient(0, 0, w, h);
  g.addColorStop(0, 'rgba(20,70,90,.55)'); g.addColorStop(1, 'rgba(6,20,45,.55)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, w * e, h);
  ctx.strokeStyle = 'rgba(127,227,216,.55)'; ctx.lineWidth = 1; ctx.strokeRect(.5, .5, w * e - 1, h - 1);
  // oltin burchaklar
  ctx.strokeStyle = C.gold2; ctx.lineWidth = 2; const k = 16;
  ctx.beginPath(); ctx.moveTo(0, k); ctx.lineTo(0, 0); ctx.lineTo(k, 0); ctx.moveTo(w * e - k, h); ctx.lineTo(w * e, h); ctx.lineTo(w * e, h - k); ctx.stroke();
  // skan chizig‘i
  const sy = ((p * 1.7) % 1) * h; ctx.fillStyle = 'rgba(127,227,216,.10)'; ctx.fillRect(0, sy, w * e, 2);
  ctx.restore();
  const tp = clamp((p - .25) * 1.6);
  if (year) revealText(ctx, year, x + 22, y + 38, tp, { size: 20, font: FONT.title, weight: 700, color: accent, align: 'left', track: 3, S });
  revealText(ctx, title, x + 22, y + (year ? 74 : 44), tp, { size: 30, font: FONT.title, weight: 700, color: C.gold2, align: 'left', track: 1, S, glowA: .25 });
  if (sub) revealText(ctx, sub, x + 22, y + (year ? 106 : 78), clamp(tp - .1), { size: 24, font: FONT.body, weight: 600, color: '#e8f4f0', align: 'left', S, italic: true });
  if (body) revealText(ctx, body, x + 22, y + (year ? 136 : 108), clamp(tp - .2), { size: 22, font: FONT.body, weight: 500, color: 'rgba(220,235,230,.85)', align: 'left', S });
}

// ---------- Post-ishlov: bloom, vinyetka, plyonka donadorligi ----------
let bloomA, bloomB, grainTiles;
export function post(ctx, cvs, t, o = {}) {
  const { bloom = .55, vignette = .75, grain = .055, S = 1, fade = 0, goldFade = 0 } = o;
  const w = cvs.width, h = cvs.height;
  if (bloom > 0) {
    const bw = Math.round(w / 8), bh = Math.round(h / 8);
    if (!bloomA) { bloomA = mkCanvas(bw, bh); bloomB = mkCanvas(bw, bh); }
    const a = bloomA.getContext('2d'), b = bloomB.getContext('2d');
    a.clearRect(0, 0, bw, bh); a.filter = 'brightness(.75) contrast(2.2) saturate(1.2)'; a.drawImage(cvs, 0, 0, bw, bh); a.filter = 'none';
    b.clearRect(0, 0, bw, bh); b.filter = `blur(${Math.round(bw / 90)}px)`; b.drawImage(bloomA, 0, 0); b.filter = 'none';
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = bloom;
    ctx.imageSmoothingQuality = 'high'; ctx.drawImage(bloomB, 0, 0, w, h);
    b.clearRect(0, 0, bw, bh); b.filter = `blur(${Math.round(bw / 30)}px)`; b.drawImage(bloomA, 0, 0); b.filter = 'none';
    ctx.globalAlpha = bloom * .6; ctx.drawImage(bloomB, 0, 0, w, h); ctx.restore();
  }
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  if (vignette > 0) {
    const g = ctx.createRadialGradient(w / 2, h / 2, h * .35, w / 2, h / 2, h * .95);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,8,${vignette})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  }
  if (goldFade > 0) { ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = `rgba(255,214,150,${goldFade})`; ctx.fillRect(0, 0, w, h); ctx.globalCompositeOperation = 'source-over'; }
  if (fade > 0) { ctx.fillStyle = `rgba(0,0,0,${fade})`; ctx.fillRect(0, 0, w, h); }
  if (grain > 0) {
    if (!grainTiles) {
      grainTiles = []; const r = rng(99);
      for (let k = 0; k < 6; k++) {
        const s = 256, c = mkCanvas(s, s), g = c.getContext('2d'), id = g.createImageData(s, s);
        for (let i = 0; i < s * s; i++) { const v = 128 + (r() + r() + r() - 1.5) * 120; id.data[i * 4] = id.data[i * 4 + 1] = id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
        g.putImageData(id, 0, 0); grainTiles.push(c);
      }
    }
    const fi = Math.floor(t * 30), tile = grainTiles[fi % 6], r = rng(fi + 1);
    const pat = ctx.createPattern(tile, 'repeat');
    const m = new DOMMatrix().translateSelf(Math.floor(r() * 256), Math.floor(r() * 256)).scaleSelf(Math.max(1, S * .75));
    pat.setTransform(m);
    ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = grain; ctx.fillStyle = pat; ctx.fillRect(0, 0, w, h);
  }
  ctx.restore();
}

// Ekranni oltin yorug‘lik chaqnashi bilan o‘tish
export function flash(ctx, a, x = W / 2, y = H / 2) {
  if (a <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(x, y, 0, x, y, W * .8);
  g.addColorStop(0, `rgba(255,236,190,${a})`); g.addColorStop(.35, `rgba(255,190,100,${a * .5})`); g.addColorStop(1, 'rgba(255,160,60,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}
// Anamorfik linza chaqnashi
export function lensFlare(ctx, x, y, a = 1, len = 900) {
  if (a <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createLinearGradient(x - len, 0, x + len, 0);
  g.addColorStop(0, 'rgba(120,200,255,0)'); g.addColorStop(.5, `rgba(255,230,180,${.55 * a})`); g.addColorStop(1, 'rgba(120,200,255,0)');
  ctx.fillStyle = g; ctx.fillRect(x - len, y - 2.5, len * 2, 5);
  ctx.globalAlpha = .4 * a; ctx.fillRect(x - len, y - 10, len * 2, 20);
  ctx.restore(); glow(ctx, x, y, 140, a, '255,225,170', .1);
}
