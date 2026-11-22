// 1-sahna: kirish (globus, naqsh, sarlavha). 2-sahna: cho‘l, tarixiy xarita, Bag‘dod.
import { W, H, C, clamp, lerp, inv, smooth, seg, ease, rng, fbm, noise2, glow, dust, rosette, starPoly, khatamTile, drawLines, title3D, text, revealText, infoCard, flash, lensFlare, FONT, mkCanvas } from './core.js';

const D2R = Math.PI / 180;
const GEO = window.GEO;

// ============ Globus (ortografik proyeksiya) ============
function ortho(lon, lat, lon0, lat0, R) {
  const l = lon * D2R, p = lat * D2R, l0 = lon0 * D2R, p0 = lat0 * D2R;
  const cosc = Math.sin(p0) * Math.sin(p) + Math.cos(p0) * Math.cos(p) * Math.cos(l - l0);
  let x = R * Math.cos(p) * Math.sin(l - l0);
  let y = -R * (Math.cos(p0) * Math.sin(p) - Math.sin(p0) * Math.cos(p) * Math.cos(l - l0));
  if (cosc < 0) { const m = Math.hypot(x, y) || 1; x = x / m * R; y = y / m * R; }
  return [x, y, cosc];
}
function ringPath(rings, f, path = new Path2D(), cull) {
  for (const r of rings) {
    let any = false; const pts = r.map(([lo, la]) => f(lo, la));
    if (cull) { for (const p of pts) if (p[2] > 0) { any = true; break; } if (!any) continue; }
    path.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) path.lineTo(pts[i][0], pts[i][1]); path.closePath();
  }
  return path;
}
function drawGlobe(ctx, cx, cy, R, lon0, lat0, t, o = {}) {
  const { alpha = 1, detail = 0, lightR = 0 } = o;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha; ctx.translate(cx, cy);
  // atmosfera
  const at = ctx.createRadialGradient(0, 0, R * .96, 0, 0, R * 1.18);
  at.addColorStop(0, 'rgba(60,200,210,.45)'); at.addColorStop(.35, 'rgba(40,140,190,.16)'); at.addColorStop(1, 'rgba(20,60,120,0)');
  ctx.fillStyle = at; ctx.beginPath(); ctx.arc(0, 0, R * 1.18, 0, 7); ctx.fill();
  // okean
  const og = ctx.createRadialGradient(-R * .35, -R * .4, R * .05, 0, 0, R);
  og.addColorStop(0, '#1b4f86'); og.addColorStop(.55, '#0b2550'); og.addColorStop(1, '#040c22');
  ctx.fillStyle = og; ctx.beginPath(); ctx.arc(0, 0, R, 0, 7); ctx.fill();
  ctx.save(); ctx.beginPath(); ctx.arc(0, 0, R, 0, 7); ctx.clip();
  const f = (lo, la) => ortho(lo, la, lon0, lat0, R);
  // graticule
  const gp = new Path2D();
  for (let la = -75; la <= 75; la += 15) { let first = true; for (let lo = -180; lo <= 180; lo += 4) { const p = f(lo, la); if (p[2] < 0) { first = true; continue; } first ? gp.moveTo(p[0], p[1]) : gp.lineTo(p[0], p[1]); first = false; } }
  for (let lo = -180; lo < 180; lo += 15) { let first = true; for (let la = -88; la <= 88; la += 4) { const p = f(lo, la); if (p[2] < 0) { first = true; continue; } first ? gp.moveTo(p[0], p[1]) : gp.lineTo(p[0], p[1]); first = false; } }
  ctx.strokeStyle = 'rgba(243,213,140,.14)'; ctx.lineWidth = 1; ctx.stroke(gp);
  // quruqlik
  const useDetail = detail > 0;
  const landP = ringPath(useDetail ? GEO.land : GEO.world, f, new Path2D(), true);
  const lg = ctx.createLinearGradient(-R, -R, R, R);
  lg.addColorStop(0, '#1d5a4c'); lg.addColorStop(.5, '#123d36'); lg.addColorStop(1, '#0a2425');
  ctx.fillStyle = lg; ctx.fill(landP, 'evenodd');
  // Hijozdan taralayotgan nur
  if (lightR > 0) {
    const m = f(39.8, 21.4);
    ctx.save(); ctx.clip(landP, 'evenodd');
    const lr = ctx.createRadialGradient(m[0], m[1], 0, m[0], m[1], lightR);
    lr.addColorStop(0, 'rgba(255,226,160,.9)'); lr.addColorStop(.25, 'rgba(240,186,96,.45)'); lr.addColorStop(.7, 'rgba(200,140,60,.12)'); lr.addColorStop(1, 'rgba(200,140,50,0)');
    ctx.fillStyle = lr; ctx.globalCompositeOperation = 'screen'; ctx.fillRect(-R, -R, 2 * R, 2 * R); ctx.restore();
  }
  ctx.strokeStyle = 'rgba(243,213,140,.75)'; ctx.lineWidth = 1.1; ctx.stroke(landP);
  // tun / kun soyasi
  const sh = ctx.createLinearGradient(-R, -R * .3, R, R * .3);
  sh.addColorStop(0, 'rgba(0,0,0,0)'); sh.addColorStop(.55, 'rgba(0,0,10,.15)'); sh.addColorStop(1, 'rgba(0,0,12,.7)');
  ctx.fillStyle = sh; ctx.fillRect(-R, -R, 2 * R, 2 * R);
  ctx.restore();
  // chekka yorug‘lik
  ctx.strokeStyle = 'rgba(127,227,216,.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(0, 0, R, Math.PI * .9, Math.PI * 1.65); ctx.stroke();
  ctx.restore();
  return f;
}

// Markaziy naqsh (rozetta + xotam to‘ri)
let patCache;
function patternLines() {
  if (patCache) return patCache;
  const L = [];
  L.push(...rosette(16, 470));
  L.push(...starPoly(16, 5, 300, 0), ...starPoly(8, 3, 190, Math.PI / 8));
  const ring = (r, n = 96) => { for (let i = 0; i < n; i++) { const a = i / n * 6.283, b = (i + 1) / n * 6.283; L.push([[r * Math.cos(a), r * Math.sin(a)], [r * Math.cos(b), r * Math.sin(b)]]); } };
  ring(480); ring(500); ring(160);
  const s = 150;
  for (let i = -8; i <= 8; i++) for (let j = -5; j <= 5; j++) {
    const x = i * s, y = j * s; if (Math.hypot(x, y) < 560) continue; L.push(...khatamTile(x, y, s));
  }
  patCache = L; return L;
}

export function scene1(ctx, t, env) {
  const S = env.S;
  // fon
  const bg = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * .7);
  bg.addColorStop(0, `rgba(10,26,58,${smooth(1, 4, t)})`); bg.addColorStop(1, '#010309');
  ctx.fillStyle = '#010309'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  // yulduzlar / zarrachalar
  dust(ctx, t, { n: 420, alpha: smooth(.2, 2.2, t) * (1 - .4 * smooth(7, 9, t)), vx: .003, vy: -.006, zoom: ease.in(inv(3.5, 7.2, t)) * 2.2 });

  // globus
  const appear = smooth(1.0, 3.2, t);
  const zoomP = ease.in(inv(3.6, 7.0, t));
  const R = lerp(lerp(250, 340, smooth(1, 4, t)), 3400, zoomP);
  const lon0 = lerp(-5, 43, ease.inOut(inv(1, 6.4, t))), lat0 = lerp(8, 23.5, ease.inOut(inv(1, 6.4, t)));
  const gA = appear * (1 - .82 * smooth(6.0, 7.4, t)) * (1 - smooth(9.5, 10, t));
  ctx.save();
  if (t < 3.2) { const b = (1 - appear) * 18; if (b > .5) ctx.filter = `blur(${b * S}px)`; }
  const f = drawGlobe(ctx, W / 2, H / 2, R, lon0, lat0, t, { alpha: gA, detail: R > 1100 ? 1 : 0, lightR: R * .55 * ease.out(inv(3.0, 6.6, t)) });
  ctx.restore();
  // Makka va Madina nuqtalari
  if (f && t > 2.6) {
    const a = smooth(2.6, 3.4, t) * gA;
    for (const [lo, la, name, dy] of [[39.83, 21.42, 'MAKKA', 34], [39.61, 24.47, 'MADINA', -22]]) {
      const p = f(lo, la); if (p[2] < .1) continue;
      const x = W / 2 + p[0], y = H / 2 + p[1];
      glow(ctx, x, y, 60 + 10 * Math.sin(t * 4), a, '255,220,150', .2);
      const pr = ((t * .8) % 1); ctx.save(); ctx.globalAlpha = a * (1 - pr); ctx.strokeStyle = C.gold2; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, 8 + pr * 50, 0, 7); ctx.stroke(); ctx.restore();
      text(ctx, name, x + 26, y + dy * .4 + 6, { size: 22, font: FONT.title, weight: 700, track: 4, align: 'left', alpha: a * (1 - smooth(5.6, 6.4, t)), glowA: .5 });
    }
  }
  // naqsh kengayishi
  const pp = inv(5.4, 7.6, t);
  if (pp > 0) {
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(t * .025); ctx.scale(lerp(.8, 1.08, ease.out(pp)) + .02 * (t - 7), lerp(.8, 1.08, ease.out(pp)) + .02 * (t - 7));
    const a = 1 - .55 * smooth(7.2, 8.4, t);
    ctx.globalAlpha = a * (1 - smooth(9.5, 10, t));
    drawLines(ctx, patternLines(), ease.out(pp), { width: 1.6, glowA: .8, spread: 1.4 });
    ctx.restore();
  }
  // sarlavha orqasidagi qorong‘ulik
  const da = smooth(6.6, 7.6, t);
  if (da > 0) { const g = ctx.createRadialGradient(W / 2, H / 2 + 20, 50, W / 2, H / 2 + 20, 900); g.addColorStop(0, `rgba(2,6,18,${.75 * da})`); g.addColorStop(1, 'rgba(2,6,18,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  // chaqnash va sarlavha
  flash(ctx, .9 * Math.exp(-Math.pow((t - 7.05) / .18, 2)));
  const tp = inv(7.0, 8.5, t);
  if (tp > 0) {
    ctx.save();
    const push = 1 + .025 * (t - 7) + ease.in(inv(9.3, 10, t)) * .25;
    ctx.translate(W / 2, H / 2 + 30); ctx.scale(push, push); ctx.translate(-W / 2, -(H / 2 + 30));
    const fa = 1 - smooth(9.4, 9.95, t);
    // arabcha sarlavha
    revealText(ctx, 'تاريخ العالم الإسلامي', W / 2, H / 2 - 105, inv(7.5, 8.6, t), { size: 70, font: FONT.ar, weight: 700, color: C.gold2, glowA: .55, alpha: fa, S, dir: 'rtl' });
    title3D(ctx, 'ISLOM OLAMI TARIXI', W / 2, H / 2 + 62, 122, tp, { S, depth: 16, sweep: inv(8.1, 9.4, t), alpha: fa, track: .06 });
    // ornament chiziq
    const lp = ease.inOut(inv(8.1, 9.0, t));
    if (lp > 0) {
      ctx.save(); ctx.globalAlpha = fa; ctx.strokeStyle = C.gold2; ctx.lineWidth = 1.5; ctx.shadowColor = 'rgba(255,200,110,.8)'; ctx.shadowBlur = 8;
      const y = H / 2 + 118, hw = 360 * lp;
      ctx.beginPath(); ctx.moveTo(W / 2 - 40 - hw, y); ctx.lineTo(W / 2 - 40, y); ctx.moveTo(W / 2 + 40, y); ctx.lineTo(W / 2 + 40 + hw, y); ctx.stroke();
      ctx.translate(W / 2, y); ctx.rotate(Math.PI / 4); ctx.strokeRect(-9, -9, 18, 18); ctx.fillStyle = C.gold2; ctx.fillRect(-4, -4, 8, 8);
      ctx.restore();
    }
    revealText(ctx, 'HUJJATLI FILM', W / 2, H / 2 + 172, inv(8.5, 9.3, t), { size: 24, font: FONT.title, weight: 400, color: '#cfe9e4', track: 12, alpha: fa, S });
    ctx.restore();
  }
  // 10-soniyadagi o‘tish
  flash(ctx, ease.in(inv(9.4, 10, t)) * .95);
  return { bloom: .55, vignette: .8, goldFade: ease.in(inv(9.6, 10, t)) * .5 };
}

// ============ 2-sahna ============
// --- cho‘l ---
function camel(ctx, x, y, s, ph) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.beginPath();
  ctx.ellipse(0, -.64, .42, .16, 0, 0, 7);
  ctx.ellipse(-.04, -.8, .2, .15, 0, 0, 7);
  ctx.moveTo(.3, -.72); ctx.quadraticCurveTo(.5, -.72, .55, -.98); ctx.lineTo(.62, -1.0); ctx.lineTo(.72, -.95); ctx.lineTo(.6, -.9); ctx.quadraticCurveTo(.55, -.66, .38, -.56); ctx.closePath();
  ctx.fill();
  ctx.lineWidth = .065; ctx.lineCap = 'round';
  const legs = [[-.3, 0], [-.2, Math.PI], [.2, Math.PI * .5], [.3, Math.PI * 1.5]];
  ctx.beginPath();
  for (const [lx, o] of legs) { const sw = Math.sin(ph + o) * .09; ctx.moveTo(lx, -.55); ctx.lineTo(lx + sw * .5, -.28); ctx.lineTo(lx + sw, 0); }
  ctx.moveTo(-.42, -.66); ctx.quadraticCurveTo(-.5, -.55, -.47, -.45);
  ctx.stroke();
  // yuk va chavandoz siluetlari (oddiy)
  ctx.beginPath(); ctx.ellipse(-.03, -.98, .1, .07, 0, 0, 7); ctx.fill();
  ctx.restore();
}
function dunes(ctx, t, cam) {
  // osmon
  const sky = ctx.createLinearGradient(0, 0, 0, H * .7);
  sky.addColorStop(0, '#081634'); sky.addColorStop(.45, '#1d4766'); sky.addColorStop(.78, '#c98a52'); sky.addColorStop(1, '#f3c27a');
  ctx.fillStyle = sky; ctx.fillRect(0, 0, W, H);
  const sx = 1340 - cam * 30, sy = 640;
  glow(ctx, sx, sy, 520, .55, '255,190,110', .08);
  glow(ctx, sx, sy, 160, 1, '255,236,190', .3);
  // uzoq shahar silueti
  ctx.save(); ctx.translate(-cam * 18, 0);
  ctx.fillStyle = 'rgba(70,60,90,.55)';
  const by = 668;
  ctx.beginPath(); ctx.moveTo(260, by);
  const city = [[300, 10, 'b'], [330, 26, 'd'], [372, 70, 'm'], [395, 18, 'b'], [430, 40, 'D'], [480, 16, 'b'], [500, 82, 'm'], [520, 24, 'd'], [560, 14, 'b'], [600, 30, 'd'], [640, 12, 'b']];
  for (const [x, h, k] of city) {
    if (k === 'b') ctx.rect(x - 22, by - h, 44, h);
    if (k === 'd' || k === 'D') { const r = k === 'D' ? 30 : 18; ctx.rect(x - r, by - h, 2 * r, h); ctx.moveTo(x - r, by - h); ctx.ellipse(x, by - h, r, r * 1.15, 0, Math.PI, 0); }
    if (k === 'm') { ctx.rect(x - 4, by - h, 8, h); ctx.moveTo(x - 6, by - h); ctx.lineTo(x, by - h - 14); ctx.lineTo(x + 6, by - h); }
  }
  ctx.fill(); ctx.restore();
  // qum tepaliklari
  const layers = [
    { base: 695, A: 45, f: .0022, par: .25, top: '#b9824f', bot: '#6a4a52', haze: .45 },
    { base: 760, A: 85, f: .0017, par: .5, top: '#d69a58', bot: '#5a3a3c', haze: .25 },
    { base: 870, A: 150, f: .0013, par: .85, top: '#e0a560', bot: '#3e2632', haze: .1 },
    { base: 1010, A: 190, f: .001, par: 1.35, top: '#c98a4c', bot: '#24151e', haze: 0 },
  ];
  layers.forEach((L, i) => {
    const off = cam * 160 * L.par + i * 50;
    const ys = [];
    for (let x = -16; x <= W + 16; x += 6) {
      const n = fbm((x + off) * L.f, i * 3.1, 3); const ridge = Math.pow(1 - Math.abs(n * 1.7), 1.6);
      ys.push([x, L.base - L.A * ridge]);
    }
    ctx.beginPath(); ctx.moveTo(-16, H); ys.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(W + 16, H); ctx.closePath();
    const g = ctx.createLinearGradient(0, L.base - L.A, 0, H);
    g.addColorStop(0, L.top); g.addColorStop(.35, L.bot); g.addColorStop(1, '#120a12'); ctx.fillStyle = g; ctx.fill();
    // shamolga teskari yonbag‘ir soyasi
    ctx.save(); ctx.beginPath(); ctx.moveTo(-16, H); ys.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(W + 16, H); ctx.closePath(); ctx.clip();
    ctx.beginPath(); ctx.moveTo(-16, H); ys.forEach(([x, y]) => ctx.lineTo(x - 70, y + 26 + L.A * .12)); ctx.lineTo(W + 16, H); ctx.closePath();
    ctx.fillStyle = `rgba(40,18,40,${.35 - i * .04})`; ctx.fill(); ctx.restore();
    if (L.haze) { ctx.fillStyle = `rgba(214,150,110,${L.haze * .8})`; ctx.fill(); }
    // qirra yorug‘ligi
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = `rgba(255,214,150,${.5 - i * .06})`; ctx.lineWidth = 1.4;
    ctx.beginPath(); ys.forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); ctx.restore();
    if (i === 1) {
      // karvon 2-qatlam qirrasida
      ctx.fillStyle = '#2a1a1c'; ctx.strokeStyle = '#2a1a1c';
      for (let k = 0; k < 7; k++) {
        const cx = 520 + k * 72 + t * 26 - cam * 160 * L.par * .0; const xi = Math.round((cx + 16) / 6);
        const pt = ys[clamp(xi, 0, ys.length - 1)];
        camel(ctx, cx, pt[1] + 4, k === 0 ? 48 : 44, t * 5.5 + k * 1.3);
      }
    }
  });
}

// --- xarita (perspektiv tekislik) ---
const LATREF = Math.cos(32 * D2R), KX = 12;
function mapCam(lonC, latC, zoom, tilt, yaw = 0) {
  const f = 1100, D = f / zoom, ct = Math.cos(tilt * D2R), st = Math.sin(tilt * D2R), cy = Math.cos(yaw), sy = Math.sin(yaw);
  return (lon, lat) => {
    let X = (lon - lonC) * LATREF * KX, Y = (lat - latC) * KX;
    const Xr = X * cy - Y * sy, Yr = X * sy + Y * cy;
    const yc = Yr * ct, zc = D - Yr * st;
    const z = Math.max(zc, 20);
    return [W / 2 + f * Xr / z, H * .54 - f * yc / z, z];
  };
}
function polyPath(rings, P, path = new Path2D()) {
  for (const r of rings) { r.forEach(([lo, la], i) => { const p = P(lo, la); i ? path.lineTo(p[0], p[1]) : path.moveTo(p[0], p[1]); }); path.closePath(); }
  return path;
}
function linePath(lines, P, path = new Path2D()) {
  for (const r of lines) { r.forEach(([lo, la], i) => { const p = P(lo, la); i ? path.lineTo(p[0], p[1]) : path.moveTo(p[0], p[1]); }); }
  return path;
}
// Taxminiy hududlar (quruqlik bilan kesiladi, shuning uchun dengiz ustida keng chizilgan)
const ERA = {
  a632: [[34.95, 29.5], [36, 30.5], [38, 31.5], [41, 31.8], [44, 31], [47.5, 30.3], [48.5, 29.7], [49.6, 28.6], [51.5, 27.0], [54, 25.9], [56.4, 26.6], [56.7, 25.0], [60, 22.5], [54, 15], [46, 12.6], [43.6, 12.4], [42.9, 13], [41.2, 15.5], [38.6, 20], [37.3, 23], [34.8, 27], [34.75, 28.2]],
  r661: [[20, 33.5], [20, 28], [25, 25.5], [25, 22], [33.5, 22], [37.5, 22], [38.6, 20], [41.2, 15.5], [42.9, 13], [43.6, 12.4], [46, 12.6], [54, 15], [60, 22.5], [64, 24.5], [64.5, 26.5], [64, 30], [62.5, 32.5], [64.5, 35], [66, 37], [67, 37.3], [65.2, 37.9], [63.6, 39.1], [61, 40], [56, 39], [54, 38.3], [52, 38.5], [49.5, 40], [49.8, 40.6], [48, 41.5], [45, 41.5], [43, 40.8], [40.5, 39], [38.5, 38], [37, 37], [36.2, 36.5], [35.3, 36.2], [34.5, 34], [30, 32.2], [25, 33]],
  u750: [[-10.5, 42.3], [-8, 42.4], [-5, 42.6], [-2, 42.6], [0, 42.7], [1.5, 43.2], [2.5, 43.8], [4.5, 43.8], [4.8, 43.3], [3.5, 41.5], [1, 40.6], [.6, 38.6], [0, 37.5], [2, 37.2], [8, 37.6], [11.5, 37.3], [13, 35.5], [16, 33], [20, 33.5], [25, 33], [30, 32.2], [34.5, 34], [35.3, 36.2], [36.2, 36.5], [37, 37], [38.5, 38], [40.5, 39], [43, 40.8], [45, 41.5], [47.6, 42.5], [48.5, 42.3], [51, 41], [53.5, 41.5], [56, 42.5], [58.5, 43.5], [61.5, 44.5], [64, 43.5], [66.5, 42], [68.5, 41.3], [69.6, 40.4], [71.5, 40.6], [70.5, 38.5], [69.5, 37], [68, 36], [66, 34], [66.5, 31], [70.5, 31.3], [72, 30], [71.5, 27.5], [70, 25.5], [69.5, 24], [67.5, 23.4], [66, 24], [64, 24.5], [60, 22.5], [54, 15], [46, 12.6], [43.6, 12.4], [42.9, 13], [41.2, 15.5], [38.6, 20], [37.5, 22], [33.5, 22], [25, 22], [20, 26], [15, 26], [10, 30], [5, 30], [-5, 28], [-13, 27.8], [-11, 33], [-10.5, 36.5]],
};
const CITIES = [
  { n: 'Makka', lo: 39.83, la: 21.42, t: 0, side: 1 }, { n: 'Madina', lo: 39.61, la: 24.47, t: 0, side: 1 },
  { n: 'Damashq', lo: 36.29, la: 33.51, t: 1, side: -1 }, { n: 'Quddus', lo: 35.23, la: 31.78, t: 1, side: -1 }, { n: 'Kufa', lo: 44.4, la: 32.03, t: 1, side: 1 },
  { n: 'Fustot', lo: 31.23, la: 30.0, t: 1, side: -1 }, { n: 'Marv', lo: 62.17, la: 37.66, t: 1, side: 1 },
  { n: 'Qayrovan', lo: 10.1, la: 35.68, t: 2, side: -1 }, { n: 'Kordova', lo: -4.78, la: 37.88, t: 2, side: 1 },
  { n: 'Buxoro', lo: 64.42, la: 39.77, t: 2, side: -1 }, { n: 'Samarqand', lo: 66.97, la: 39.65, t: 2, side: 1 }, { n: 'Multon', lo: 71.47, la: 30.2, t: 2, side: 1 },
];
const ROUTES = [
  [[39.61, 24.47], [36.29, 33.51], 0], [[39.61, 24.47], [44.4, 32.03], 0], [[39.61, 24.47], [31.23, 30.0], 0], [[44.4, 32.03], [62.17, 37.66], 0],
  [[36.29, 33.51], [10.1, 35.68], 1], [[10.1, 35.68], [-4.78, 37.88], 1], [[62.17, 37.66], [66.97, 39.65], 1], [[44.4, 32.03], [71.47, 30.2], 1],
];
function route(ctx, P, a, b, p, t) {
  if (p <= 0) return;
  const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, d = Math.hypot(b[0] - a[0], b[1] - a[1]);
  const nx = -(b[1] - a[1]) / d, ny = (b[0] - a[0]) / d;
  const c = [mx + nx * d * .18, my + ny * d * .18];
  const N = 48, pts = [];
  for (let i = 0; i <= N; i++) { const u = i / N; const lo = (1 - u) * (1 - u) * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0], la = (1 - u) * (1 - u) * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1]; pts.push(P(lo, la)); }
  const head = ease.inOut(clamp(p)) * N;
  ctx.save(); ctx.lineCap = 'round'; ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < Math.floor(head); i++) {
    const age = (head - i) / N; const al = clamp(1 - age * .9) * .9;
    ctx.strokeStyle = `rgba(255,214,140,${al})`; ctx.lineWidth = 2.6;
    ctx.beginPath(); ctx.moveTo(pts[i][0], pts[i][1]); ctx.lineTo(pts[i + 1][0], pts[i + 1][1]); ctx.stroke();
  }
  ctx.restore();
  const hp = pts[Math.min(N, Math.floor(head))];
  if (p < 1.15) glow(ctx, hp[0], hp[1], 26, 1 - smooth(1, 1.15, p), '255,230,170', .25);
}

function drawMap(ctx, t, P, eras, o = {}) {
  // okean
  const og = ctx.createRadialGradient(W / 2, H * .3, 100, W / 2, H / 2, W * .8);
  og.addColorStop(0, '#0d2a55'); og.addColorStop(1, '#040b1f');
  ctx.fillStyle = og; ctx.fillRect(0, 0, W, H);
  // koordinata to‘ri
  const grid = new Path2D();
  for (let lo = -30; lo <= 100; lo += 5) { for (let la = -10; la <= 65; la += 2.5) { const p = P(lo, la); la === -10 ? grid.moveTo(p[0], p[1]) : grid.lineTo(p[0], p[1]); } }
  for (let la = -10; la <= 65; la += 5) { for (let lo = -30; lo <= 100; lo += 2.5) { const p = P(lo, la); lo === -30 ? grid.moveTo(p[0], p[1]) : grid.lineTo(p[0], p[1]); } }
  ctx.strokeStyle = 'rgba(127,227,216,.08)'; ctx.lineWidth = 1; ctx.stroke(grid);
  // quruqlik
  const land = polyPath(GEO.land, P);
  const lg = ctx.createLinearGradient(0, 0, 0, H);
  lg.addColorStop(0, '#18332f'); lg.addColorStop(1, '#22403a');
  ctx.fillStyle = lg; ctx.fill(land, 'evenodd');
  // hududlar
  ctx.save(); ctx.clip(land, 'evenodd');
  const lakes = polyPath(GEO.lakes, P);
  const eraStyle = [['rgba(246,206,120,', '255,225,160'], ['rgba(40,190,160,', '120,240,210'], ['rgba(30,150,120,', '90,210,180']];
  [['a632', 0], ['r661', 1], ['u750', 2]].forEach(([k, i]) => {
    const p = eras[i]; if (p <= 0) return;
    const path = polyPath([ERA[k]], P);
    // o‘sish doirasi (Madinadan)
    ctx.save();
    const rad = ease.inOut(clamp(p)) * 70;
    const circ = new Path2D(); for (let j = 0; j <= 72; j++) { const a = j / 72 * 6.283; const q = P(39.61 + rad * Math.cos(a) / LATREF, 24.47 + rad * Math.sin(a)); j ? circ.lineTo(q[0], q[1]) : circ.moveTo(q[0], q[1]); }
    ctx.clip(circ);
    ctx.fillStyle = eraStyle[i][0] + (i === 0 ? .42 : .32) * (o.eraFade ?? 1) + ')'; ctx.fill(path);
    ctx.strokeStyle = `rgba(${eraStyle[i][1]},.9)`; ctx.lineWidth = 2; ctx.shadowColor = `rgba(${eraStyle[i][1]},.9)`; ctx.shadowBlur = 10; ctx.stroke(path);
    ctx.restore();
  });
  ctx.restore();
  // ko‘llar va daryolar
  ctx.fillStyle = '#0a2148'; ctx.fill(polyPath(GEO.lakes, P), 'evenodd');
  ctx.strokeStyle = 'rgba(243,213,140,.5)'; ctx.lineWidth = 1; ctx.stroke(polyPath(GEO.lakes, P));
  const riv = new Path2D(); for (const k in GEO.rivers) linePath(GEO.rivers[k], P, riv);
  ctx.strokeStyle = 'rgba(80,210,220,.55)'; ctx.lineWidth = 1.4; ctx.stroke(riv);
  ctx.strokeStyle = 'rgba(243,213,140,.7)'; ctx.lineWidth = 1.2; ctx.stroke(land);
}

export function scene2(ctx, t, env) {
  const S = env.S;
  let out = { bloom: .5, vignette: .75 };
  // --- A: cho‘l ---
  if (t < 2.9) {
    const cam = t;
    ctx.save();
    const tilt = ease.in(inv(2.1, 2.9, t));
    const sc = 1.0 + t * .02;
    ctx.translate(W / 2, H / 2); ctx.scale(sc, sc); ctx.translate(-W / 2, -H / 2 + tilt * -420);
    dunes(ctx, t, cam);
    ctx.restore();
    dust(ctx, t, { n: 260, alpha: .7, vx: .05, vy: -.004, color: '255,200,140', size: .8 });
    lensFlare(ctx, 1340 - cam * 30, 640 + tilt * -420, .5 * (1 - tilt));
    revealText(ctx, 'VII ASR  ·  ARABISTON YARIM OROLI', 140, H - 120, inv(.4, 1.3, t), { size: 26, font: FONT.title, weight: 700, color: C.gold2, align: 'left', track: 5, alpha: 1 - smooth(1.9, 2.4, t), S, glowA: .3 });
    out.goldFade = .5 * (1 - smooth(0, .6, t));
    if (t < .6) flash(ctx, .8 * (1 - smooth(0, .6, t)));
  }
  // --- B: xarita ---
  if (t > 2.3 && t < 8.6) {
    const K = [
      [2.3, 42, 22, 3.4, 62], [3.9, 42, 28, 2.3, 40], [5.5, 34, 31, 1.65, 34], [7.0, 30, 33, 1.42, 30], [8.6, 44.4, 33.3, 11, 18],
    ];
    let i = 0; while (i < K.length - 2 && t > K[i + 1][0]) i++;
    const a = K[i], b = K[i + 1], u = ease.inOut(inv(a[0], b[0], t));
    const zu = i === 3 ? ease.in(inv(a[0], b[0], t)) : u;
    const zoom = Math.exp(lerp(Math.log(a[3]), Math.log(b[3]), zu));
    const P = mapCam(lerp(a[1], b[1], u), lerp(a[2], b[2], u), zoom, lerp(a[4], b[4], u), lerp(-.06, .04, inv(2.3, 8.6, t)));
    const eras = [inv(2.6, 3.7, t), inv(3.9, 5.2, t), inv(5.4, 6.9, t)];
    ctx.save();
    ctx.globalAlpha = smooth(2.3, 2.8, t);
    drawMap(ctx, t, P, eras);
    // marshrutlar
    ROUTES.forEach(([a, b, era], k) => route(ctx, P, a, b, inv(era ? 5.5 + k * .08 - .3 : 4.0 + k * .12, era ? 6.6 + k * .08 : 5.0 + k * .12, t), t));
    // shaharlar
    for (const c of CITIES) {
      const st = [2.8, 4.2, 5.9][c.t] + (c.n.length % 3) * .12;
      const ap = smooth(st, st + .5, t) * (1 - smooth(7.4, 7.9, t));
      if (ap <= 0) continue;
      const p = P(c.lo, c.la); glow(ctx, p[0], p[1], 22, ap, '255,225,160', .3);
      ctx.save(); ctx.globalAlpha = ap; ctx.fillStyle = C.gold3; ctx.beginPath(); ctx.arc(p[0], p[1], 3.5, 0, 7); ctx.fill(); ctx.restore();
      text(ctx, c.n, p[0] + c.side * 12, p[1] + 7, { size: 23, font: FONT.body, weight: 600, align: c.side > 0 ? 'left' : 'right', color: '#f6ead0', alpha: ap, glowA: .0 });
    }
    // Bag‘dod
    const bp = P(44.36, 33.31), ba = smooth(7.1, 7.5, t);
    if (ba > 0) {
      glow(ctx, bp[0], bp[1], 80 + 40 * ease.in(inv(7.5, 8.6, t)), ba, '255,220,150', .25);
      text(ctx, 'Bag‘dod · 762', bp[0] + 16, bp[1] - 14, { size: 30, font: FONT.body, weight: 600, align: 'left', color: C.gold3, alpha: ba * (1 - smooth(8.0, 8.4, t)), glowA: .6 });
    }
    ctx.restore();
    // davr kartasi
    const cards = [
      [2.7, 3.95, '632', 'ARABISTON', 'Yarim orol birlashdi'],
      [3.95, 5.45, '632 – 661', 'ROSHIDUN XALIFALIGI', 'Shom, Iroq, Misr, Eron'],
      [5.45, 7.15, '661 – 750', 'UMAVIYLAR XALIFALIGI', 'Andalusiyadan Sind va Movarounnahrgacha'],
      [7.15, 8.3, '762', 'BAG‘DOD', 'Abbosiylar poytaxti barpo etildi'],
    ];
    for (const [s, e, y, ti, sub] of cards) {
      const p = inv(s, s + .55, t), q = smooth(e - .25, e, t);
      if (p <= 0 || q >= 1) continue;
      ctx.save(); ctx.globalAlpha = 1 - q;
      infoCard(ctx, 90, 90, 560, 150, p, { year: y, title: ti, sub, S });
      ctx.restore();
    }
    // vaqt chizig‘i
    const tl = smooth(2.5, 3.0, t) * (1 - smooth(8.0, 8.4, t));
    if (tl > 0) {
      const ys = [[622, 2.4], [632, 2.7], [661, 3.95], [750, 5.45], [762, 7.15]];
      const x0 = 420, x1 = 1500, y = H - 80; const prog = inv(2.4, 7.3, t);
      ctx.save(); ctx.globalAlpha = tl;
      ctx.strokeStyle = 'rgba(243,213,140,.35)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
      ctx.strokeStyle = C.gold2; ctx.shadowColor = 'rgba(255,200,110,.9)'; ctx.shadowBlur = 10; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(lerp(x0, x1, prog), y); ctx.stroke(); ctx.shadowBlur = 0;
      ys.forEach(([yr, at], k) => {
        const x = lerp(x0, x1, k / (ys.length - 1)), on = t >= at;
        ctx.fillStyle = on ? C.gold3 : 'rgba(243,213,140,.4)'; ctx.beginPath(); ctx.arc(x, y, on ? 6 : 4, 0, 7); ctx.fill();
        if (on) glow(ctx, x, y, 24, tl * .8);
        text(ctx, String(yr), x, y - 20, { size: 24, font: FONT.title, weight: 700, color: on ? C.gold3 : 'rgba(243,213,140,.5)', alpha: tl, track: 2 });
      });
      text(ctx, 'Chegaralar taxminiy', x1 + 40, y + 8, { size: 18, font: FONT.body, weight: 500, italic: true, align: 'left', color: 'rgba(220,235,230,.6)', alpha: tl });
      ctx.restore();
    }
    dust(ctx, t, { n: 140, alpha: .5, vx: .002, vy: -.004 });
    if (t < 2.9) { flash(ctx, .35 * (1 - smooth(2.3, 2.9, t))); }
  }
  // --- C: Bag‘dod «Doira shahar» ---
  if (t > 8.15) {
    const a = smooth(8.15, 8.6, t);
    ctx.save(); ctx.globalAlpha = a;
    const bg = ctx.createRadialGradient(W / 2, H / 2, 50, W / 2, H / 2, W * .7);
    bg.addColorStop(0, '#0f2c55'); bg.addColorStop(1, '#030918');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    ctx.restore();
    roundCity(ctx, t - 8.15, a, S);
  }
  return out;
}

function roundCity(ctx, u, a, S) {
  const R = 330, cx = W / 2, cy = H / 2 + 10;
  const p = ease.out(inv(0, 1.2, u));
  const zoomOut = 1 + ease.in(inv(1.25, 1.85, u)) * .55;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(cx, cy); ctx.scale(zoomOut, zoomOut * lerp(.86, 1, ease.in(inv(1.1, 1.85, u)))); ctx.rotate(-.12 + u * .05);
  // Dajla daryosi (sharqda)
  ctx.save(); ctx.strokeStyle = 'rgba(60,190,210,.28)'; ctx.lineWidth = 34; ctx.shadowColor = 'rgba(60,200,220,.6)'; ctx.shadowBlur = 20; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(R * 1.55, -R * 1.6); ctx.bezierCurveTo(R * 1.1, -R * .6, R * 1.75, R * .3, R * 1.3, R * 1.6);
  ctx.setLineDash([2000]); ctx.lineDashOffset = 2000 * (1 - p); ctx.stroke(); ctx.restore();
  const L = [];
  const ring = (r, n = 128) => { for (let i = 0; i < n; i++) { const a = i / n * 6.283, b = (i + 1) / n * 6.283; L.push([[r * Math.cos(a), r * Math.sin(a)], [r * Math.cos(b), r * Math.sin(b)]]); } };
  ring(R); ring(R * .95); ring(R * .9); ring(R * .62); ring(R * .58);
  // radial ko‘chalar
  for (let i = 0; i < 96; i++) { const an = i / 96 * 6.283; if (Math.abs(((an / (Math.PI / 2)) % 1) - .5) < .06) continue; L.push([[R * .62 * Math.cos(an), R * .62 * Math.sin(an)], [R * .88 * Math.cos(an), R * .88 * Math.sin(an)]]); }
  // 4 darvoza va ark ko‘chalari (diagonal)
  const gates = [[-Math.PI / 4, 'Xuroson darvozasi'], [Math.PI / 4, 'Basra darvozasi'], [3 * Math.PI / 4, 'Kufa darvozasi'], [-3 * Math.PI / 4, 'Shom darvozasi']];
  for (const [an] of gates) {
    for (const o of [-.035, .035]) L.push([[R * .2 * Math.cos(an + o * 2.4), R * .2 * Math.sin(an + o * 2.4)], [R * 1.02 * Math.cos(an + o), R * 1.02 * Math.sin(an + o)]]);
  }
  // markaz: saroy va masjid
  const sq = (x, y, s) => { L.push([[x - s, y - s], [x + s, y - s]], [[x + s, y - s], [x + s, y + s]], [[x + s, y + s], [x - s, y + s]], [[x - s, y + s], [x - s, y - s]]); };
  sq(0, 0, R * .1); sq(0, -R * .2, R * .07);
  ring(R * .05, 32);
  drawLines(ctx, L, p, { width: 1.8, glowA: .8, spread: .9 });
  // darvozalar
  for (const [an, name] of gates) {
    const gx = R * Math.cos(an), gy = R * Math.sin(an), ga = smooth(.6, 1.0, u);
    glow(ctx, gx, gy, 40, ga, '255,220,150', .3);
    ctx.save(); ctx.rotate(.12 - u * .05);
    const q = [gx * Math.cos(.12 - u * .05) - gy * Math.sin(.12 - u * .05), gx * Math.sin(.12 - u * .05) + gy * Math.cos(.12 - u * .05)];
    text(ctx, name, q[0] * 1.13, q[1] * 1.13 + 6, { size: 21, font: FONT.body, weight: 600, color: '#f1e6c8', alpha: ga * (1 - smooth(1.3, 1.6, u)) });
    ctx.restore();
  }
  glow(ctx, 0, 0, 120, .6 * p, '255,210,130', .2);
  ctx.restore();
  // yozuvlar
  const ta = smooth(.3, .8, u) * (1 - smooth(1.3, 1.6, u));
  revealText(ctx, 'BAG‘DOD  ·  «DOIRA SHAHAR»', 120, 120, inv(.3, .9, u), { size: 34, font: FONT.title, weight: 700, color: C.gold2, align: 'left', track: 4, alpha: ta, S, glowA: .4 });
  revealText(ctx, 'Xalifa al-Mansur, 762–766-yillar', 120, 162, inv(.45, 1.0, u), { size: 26, font: FONT.body, weight: 600, italic: true, color: '#d9efe9', align: 'left', alpha: ta, S });
  revealText(ctx, 'مدينة السلام', W - 120, 130, inv(.5, 1.1, u), { size: 52, font: FONT.ar, weight: 700, color: C.gold2, align: 'right', alpha: ta, S, dir: 'rtl', glowA: .4 });
  flash(ctx, ease.in(inv(1.55, 1.85, u)) * .7);
}
