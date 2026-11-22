// 3-sahna: Baytul Hikma kutubxonasi va qo‘lyozma. 5-sahna: ilm va meros.
import { W, H, C, clamp, lerp, inv, smooth, seg, ease, rng, glow, dust, starPoly, rosette, khatamTile, drawLines, text, revealText, infoCard, flash, FONT, mkCanvas, lensFlare } from './core.js';

// ================= Kutubxona (3D proyeksiya) =================
const BOOKS = (() => {
  const r = rng(321), out = [];
  const cols = ['#6b1f1a', '#7a4a1c', '#1f3d5a', '#2b5a3c', '#5a2a3a', '#8a6a2a', '#3a2418', '#1e4a4a'];
  for (let bay = 0; bay < 8; bay++) for (const side of [-1, 1]) for (let sh = 0; sh < 6; sh++) {
    let z = 0; const row = [];
    while (z < 1) { const w = .025 + r() * .035; if (z + w > 1) break; row.push({ z0: z, z1: z + w * .92, h: .65 + r() * .3, c: cols[Math.floor(r() * cols.length)], g: r() < .35, lean: r() < .06 }); z += w; }
    out.push({ bay, side, sh, row });
  }
  return out;
})();
function libCam(camZ, camX = 0, camY = 2.3, f = 900) {
  return (x, y, z) => { const d = z - camZ; if (d < .15) return null; return [W / 2 + f * (x - camX) / d, H * .5 - f * (y - camY) / d, d]; };
}
function quad(ctx, P, a, b, c, d) {
  const A = P(...a), B = P(...b), Cc = P(...c), D = P(...d); if (!A || !B || !Cc || !D) return false;
  ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.lineTo(Cc[0], Cc[1]); ctx.lineTo(D[0], D[1]); ctx.closePath(); return true;
}
function pointedArch(cx, w, ySpring, rise, n = 24) {
  // ikki markazli o‘tkir ark: chap va o‘ng yoylar
  const pts = []; const half = w / 2;
  const R = (half * half + rise * rise) / (2 * half);
  for (let i = 0; i <= n; i++) { const u = i / n; const ang = Math.acos((R - half) / R) * u; pts.push([cx - half + R - R * Math.cos(ang), ySpring + R * Math.sin(ang)]); }
  const right = pts.slice(0, -1).reverse().map(([x, y]) => [2 * cx - x, y]);
  return pts.concat(right);
}
let windowCache;
function windowLattice(R) {
  if (windowCache) return windowCache;
  const L = [...rosette(12, R), ...starPoly(12, 5, R * .5, 0), ...starPoly(6, 2, R * .25, 0)];
  windowCache = L; return L;
}
function drawLibrary(ctx, t, camZ, o = {}) {
  const P = libCam(camZ, o.camX || 0, o.camY || 2.3);
  const ZB = 30, X = 4, XS = 6.2;
  // fon
  const bg = ctx.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, '#0b0f1e'); bg.addColorStop(.6, '#1a1410'); bg.addColorStop(1, '#0c0806');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  // orqa devor
  if (quad(ctx, P, [-XS, 0, ZB], [XS, 0, ZB], [XS, 11, ZB], [-XS, 11, ZB])) { ctx.fillStyle = '#2a1d14'; ctx.fill(); }
  // dumaloq deraza
  const wc = P(0, 6.4, ZB);
  if (wc) {
    const wr = 900 * 2.3 / wc[2];
    glow(ctx, wc[0], wc[1], wr * 4.5, .55, '255,205,130', .05);
    const g = ctx.createRadialGradient(wc[0], wc[1], 0, wc[0], wc[1], wr);
    g.addColorStop(0, '#fff6dc'); g.addColorStop(.6, '#ffd890'); g.addColorStop(1, '#e8a650');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(wc[0], wc[1], wr, 0, 7); ctx.fill();
    ctx.save(); ctx.translate(wc[0], wc[1]); ctx.scale(wr / 200, wr / 200);
    ctx.strokeStyle = '#3a2412'; ctx.lineWidth = 9; ctx.lineCap = 'round';
    const path = new Path2D(); for (const [a, b] of windowLattice(200)) { path.moveTo(a[0], a[1]); path.lineTo(b[0], b[1]); }
    ctx.stroke(path); ctx.strokeStyle = 'rgba(255,210,140,.35)'; ctx.lineWidth = 2.5; ctx.stroke(path);
    ctx.beginPath(); ctx.arc(0, 0, 200, 0, 7); ctx.lineWidth = 14; ctx.strokeStyle = '#5a3a1c'; ctx.stroke();
    ctx.lineWidth = 3; ctx.strokeStyle = C.gold2; ctx.stroke();
    ctx.restore();
    // pastki ark eshik
    const door = pointedArch(0, 3.2, 2.2, 1.6).map(([x, y]) => P(x, y, ZB));
    ctx.beginPath(); ctx.moveTo(P(-1.6, 0, ZB)[0], P(-1.6, 0, ZB)[1]); door.forEach(p => ctx.lineTo(p[0], p[1])); ctx.lineTo(P(1.6, 0, ZB)[0], P(1.6, 0, ZB)[1]); ctx.closePath();
    const dg = ctx.createLinearGradient(0, door[0][1] - 200, 0, door[0][1]); dg.addColorStop(0, '#ffe7b0'); dg.addColorStop(1, '#d69a52'); ctx.fillStyle = dg; ctx.fill();
  }
  // pol
  if (quad(ctx, P, [-X, 0, camZ + .3], [X, 0, camZ + .3], [X, 0, ZB], [-X, 0, ZB])) {
    const fg = ctx.createLinearGradient(0, H, 0, H * .5); fg.addColorStop(0, '#120c08'); fg.addColorStop(1, '#4a3420'); ctx.fillStyle = fg; ctx.fill();
  }
  // pol naqshi (perspektiv to‘r)
  ctx.save(); ctx.strokeStyle = 'rgba(243,213,140,.16)'; ctx.lineWidth = 1;
  const gp = new Path2D();
  for (let z = Math.ceil(camZ + .5); z <= ZB; z += 1) { const a = P(-X, 0, z), b = P(X, 0, z); if (a && b) { gp.moveTo(a[0], a[1]); gp.lineTo(b[0], b[1]); } }
  for (let x = -X; x <= X; x += 1) { const a = P(x, 0, Math.max(camZ + .5, 0)), b = P(x, 0, ZB); if (a && b) { gp.moveTo(a[0], a[1]); gp.lineTo(b[0], b[1]); } }
  ctx.stroke(gp); ctx.restore();
  // derazaning poldagi aksi
  const rf = P(0, 0, ZB - 6);
  if (rf) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(rf[0], rf[1]); ctx.scale(1, .25); glow(ctx, 0, 0, 900 * 6 / rf[2], .35, '255,200,120', .1); ctx.restore(); }
  // bo‘lmalar: uzoqdan yaqinga
  for (let bay = 7; bay >= 0; bay--) {
    const z0 = 2 + bay * 3.5, z1 = z0 + 3.5;
    if (z1 - camZ < .3) continue;
    for (const side of [-1, 1]) {
      // javon devori
      const xs = side * XS;
      if (quad(ctx, P, [xs, 0, z0], [xs, 0, z1], [xs, 5.2, z1], [xs, 5.2, z0])) { ctx.fillStyle = '#1d140d'; ctx.fill(); }
      // kitoblar
      for (const B of BOOKS) {
        if (B.bay !== bay || B.side !== side) continue;
        const y0 = .35 + B.sh * .78;
        for (const bk of B.row) {
          const za = lerp(z0 + .15, z1 - .15, bk.z0), zb = lerp(z0 + .15, z1 - .15, bk.z1);
          if (za - camZ < .3) continue;
          if (quad(ctx, P, [xs - side * .05, y0, za], [xs - side * .05, y0, zb], [xs - side * .05, y0 + .62 * bk.h, zb], [xs - side * .05, y0 + .62 * bk.h, za])) {
            ctx.fillStyle = bk.c; ctx.fill();
            if (bk.g) { ctx.strokeStyle = 'rgba(230,190,110,.55)'; ctx.lineWidth = .8; ctx.stroke(); }
          }
        }
        // javon taxtasi
        if (quad(ctx, P, [xs, y0 - .05, z0], [xs, y0 - .05, z1], [xs - side * .4, y0 - .05, z1], [xs - side * .4, y0 - .05, z0])) { ctx.fillStyle = '#3a2614'; ctx.fill(); }
      }
      // ustun
      for (const zc of [z0]) {
        const a = P(side * X, 0, zc), b = P(side * X, 4.3, zc);
        if (a && b) {
          const w = 900 * .32 / a[2];
          const cg = ctx.createLinearGradient(a[0] - w, 0, a[0] + w, 0);
          cg.addColorStop(0, '#2a1c12'); cg.addColorStop(.5, side < 0 ? '#9a7348' : '#6a4a2c'); cg.addColorStop(1, '#1a120c');
          ctx.fillStyle = cg; ctx.fillRect(a[0] - w / 2, b[1], w, a[1] - b[1]);
          ctx.fillStyle = '#b08a50'; ctx.fillRect(a[0] - w * .8, b[1] - w * .35, w * 1.6, w * .35);
        }
      }
      // yon ark (ustunlar orasida)
      const arch = pointedArch((z0 + z1) / 2, 3.5, 4.3, 2.0);
      ctx.beginPath(); let ok = true;
      const top = [];
      arch.forEach(([z, y], k) => { const p = P(side * X, y, z); if (!p) { ok = false; return; } top.push(p); k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); });
      if (ok && top.length) {
        const pz1 = P(side * X, 8, z1), pz0 = P(side * X, 8, z0);
        if (pz1 && pz0) {
          ctx.lineTo(pz1[0], pz1[1]); ctx.lineTo(pz0[0], pz0[1]); ctx.closePath();
          ctx.fillStyle = '#3b2a1c'; ctx.fill();
          ctx.beginPath(); top.forEach((p, k) => k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]));
          ctx.strokeStyle = 'rgba(230,184,100,.75)'; ctx.lineWidth = Math.max(1, 900 * .05 / top[0][2]); ctx.stroke();
        }
      }
    }
    // ko‘ndalang ark (kameraga qaragan)
    const tz = z0;
    if (tz - camZ > .4) {
      const arch = pointedArch(0, 2 * X, 4.3, 2.6);
      const pts = arch.map(([x, y]) => P(x, y, tz));
      const L = P(-XS - 1, 11, tz), Rr = P(XS + 1, 11, tz), BL = P(-XS - 1, 4.3, tz), BR = P(XS + 1, 4.3, tz);
      if (L && Rr && BL && BR) {
        ctx.beginPath(); ctx.moveTo(BL[0], BL[1]); pts.forEach(p => ctx.lineTo(p[0], p[1])); ctx.lineTo(BR[0], BR[1]); ctx.lineTo(Rr[0], Rr[1]); ctx.lineTo(L[0], L[1]); ctx.closePath();
        const ag = ctx.createLinearGradient(0, L[1], 0, BL[1]); ag.addColorStop(0, '#120c0a'); ag.addColorStop(1, '#4a3220');
        ctx.fillStyle = ag; ctx.fill();
        ctx.beginPath(); pts.forEach((p, k) => k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]));
        const lw = 900 * .09 / pts[0][2];
        ctx.strokeStyle = 'rgba(214,166,74,.85)'; ctx.lineWidth = lw; ctx.stroke();
        ctx.strokeStyle = 'rgba(255,230,170,.35)'; ctx.lineWidth = lw * .3; ctx.stroke();
      }
    }
    // osma chiroq
    const lz = z0 + 1.75; const lp = P(0, 5.6, lz), lc = P(0, 9, lz);
    if (lp && lc && lp[2] > .5) {
      ctx.strokeStyle = 'rgba(120,90,50,.7)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(lc[0], lc[1]); ctx.lineTo(lp[0], lp[1]); ctx.stroke();
      const s = 900 / lp[2];
      ctx.fillStyle = '#c9963c'; ctx.beginPath(); ctx.ellipse(lp[0], lp[1], .22 * s, .14 * s, 0, 0, 7); ctx.fill();
      glow(ctx, lp[0], lp[1], 2.6 * s, .9, '255,190,100', .12);
      glow(ctx, lp[0], lp[1], .5 * s, 1, '255,240,200', .3);
    }
  }
  // hajmli nur ustunlari (derazadan)
  if (wc) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const base = [P(-2.6, 0, 8), P(2.6, 0, 8)];
    if (base[0] && base[1]) {
      const g = ctx.createLinearGradient(wc[0], wc[1], wc[0], base[0][1]);
      g.addColorStop(0, 'rgba(255,214,150,.28)'); g.addColorStop(1, 'rgba(255,190,110,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(wc[0] - 30, wc[1]); ctx.lineTo(wc[0] + 30, wc[1]); ctx.lineTo(base[1][0], base[1][1]); ctx.lineTo(base[0][0], base[0][1]); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }
}

// ================= Qo‘lyozma =================
let pageCache = {};
function parchment(w, h, seed) {
  const c = mkCanvas(w, h), g = c.getContext('2d');
  const gr = g.createRadialGradient(w / 2, h / 2, 50, w / 2, h / 2, w * .8);
  gr.addColorStop(0, '#efe0b8'); gr.addColorStop(.7, '#d9c08a'); gr.addColorStop(1, '#a78550');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  const r = rng(seed); g.globalAlpha = .07;
  for (let i = 0; i < 1400; i++) { g.fillStyle = r() < .5 ? '#7a5a2a' : '#fff4d6'; const s = r() * 3; g.fillRect(r() * w, r() * h, s, s); }
  g.globalAlpha = 1;
  return c;
}
function frameBorder(g, w, h, m) {
  g.strokeStyle = '#a87a28'; g.lineWidth = 3; g.strokeRect(m, m, w - 2 * m, h - 2 * m);
  g.strokeStyle = '#1f3d6a'; g.lineWidth = 1.5; g.strokeRect(m + 8, m + 8, w - 2 * m - 16, h - 2 * m - 16);
  g.strokeStyle = '#a87a28'; g.lineWidth = 1; g.strokeRect(m + 13, m + 13, w - 2 * m - 26, h - 2 * m - 26);
}
function shamsa(g, x, y, R) {
  // oltin-lojuvard shamsa (quyoshsimon bezak)
  for (let i = 0; i < 32; i++) { const a = i / 32 * 6.283; g.strokeStyle = i % 2 ? '#1f3d6a' : '#b8862c'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + R * Math.cos(a), y + R * Math.sin(a)); g.lineTo(x + R * 1.25 * Math.cos(a), y + R * 1.25 * Math.sin(a)); g.stroke(); }
  const gr = g.createRadialGradient(x, y, 0, x, y, R); gr.addColorStop(0, '#f5d27a'); gr.addColorStop(1, '#b07e24');
  g.fillStyle = gr; g.beginPath(); g.arc(x, y, R, 0, 7); g.fill();
  g.fillStyle = '#1f3d6a'; g.beginPath(); g.arc(x, y, R * .72, 0, 7); g.fill();
  g.strokeStyle = '#e8c26a'; g.lineWidth = 1.5; g.save(); g.translate(x, y);
  for (const [a, b] of starPoly(8, 3, R * .62, Math.PI / 8)) { g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  g.restore();
}
function leftPage() {
  if (pageCache.L) return pageCache.L;
  const w = 640, h = 860, c = parchment(w, h, 5), g = c.getContext('2d');
  frameBorder(g, w, h, 34);
  shamsa(g, w / 2, 150, 48);
  g.direction = 'rtl'; g.textAlign = 'center'; g.fillStyle = '#8a1c14';
  g.font = '700 44px "Amiri"'; g.fillText('كتاب الجبر والمقابلة', w / 2, 270);
  g.fillStyle = '#2a1a0c'; g.font = '400 30px "Amiri"';
  g.fillText('للخوارزمي', w / 2, 318);
  g.strokeStyle = '#a87a28'; g.lineWidth = 1.2; g.beginPath(); g.moveTo(140, 350); g.lineTo(w - 140, 350); g.stroke();
  g.font = '700 36px "Amiri"'; g.fillStyle = '#2a1a0c';
  g.fillText('مالٌ وعشرةُ أجذارٍ', w / 2, 440);
  g.fillText('يَعدِلُ تسعةً وثلاثين درهمًا', w / 2, 500);
  g.fillStyle = '#8a1c14'; g.font = '400 28px "Amiri"'; g.fillText('١٠ + ٣٩', w / 2, 560);
  // pastki geometrik bezak
  g.save(); g.translate(w / 2, 690); g.strokeStyle = '#a87a28'; g.lineWidth = 1.4;
  for (const [a, b] of rosette(8, 80)) { g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  g.restore();
  pageCache.L = c; return c;
}
function rightPageBase() {
  if (pageCache.R) return pageCache.R;
  const w = 640, h = 860, c = parchment(w, h, 9), g = c.getContext('2d');
  frameBorder(g, w, h, 34);
  pageCache.R = c; return c;
}
// al-Xorazmiy: x² + 10x = 39 ni kvadratni to‘ldirish usuli
function khwarizmiDiagram(ctx, x, y, s, p) {
  const xs = s * 3 / 8, k = s * 2.5 / 8; // x = 3, 10/4 = 2.5, jami tomon 8
  ctx.save(); ctx.translate(x, y); ctx.lineWidth = 3; ctx.strokeStyle = '#2a1a0c';
  const a1 = ease.out(inv(0, .2, p)), a2 = ease.out(inv(.2, .5, p)), a3 = ease.out(inv(.5, .75, p)), a4 = inv(.75, 1, p);
  // markaziy kvadrat x²
  if (a1 > 0) { ctx.globalAlpha = a1; ctx.fillStyle = 'rgba(31,61,106,.55)'; ctx.fillRect(-xs / 2, -xs / 2, xs, xs); ctx.strokeRect(-xs / 2, -xs / 2, xs, xs); }
  // 4 to‘g‘ri to‘rtburchak (2.5 · x)
  if (a2 > 0) {
    ctx.globalAlpha = a2; ctx.fillStyle = 'rgba(176,126,36,.55)';
    const r = [[-xs / 2, -xs / 2 - k, xs, k], [-xs / 2, xs / 2, xs, k], [-xs / 2 - k, -xs / 2, k, xs], [xs / 2, -xs / 2, k, xs]];
    r.forEach(([a, b, c, d]) => { ctx.fillRect(a, b, c, d * a2 + (1 - a2) * 0); ctx.strokeRect(a, b, c, d); });
  }
  // burchak kvadratlari (4 · 2.5² = 25)
  if (a3 > 0) {
    ctx.globalAlpha = a3; ctx.fillStyle = 'rgba(138,28,20,.55)';
    for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) { const qx = sx < 0 ? -xs / 2 - k : xs / 2, qy = sy < 0 ? -xs / 2 - k : xs / 2; ctx.fillRect(qx, qy, k, k); ctx.strokeRect(qx, qy, k, k); }
  }
  // tashqi kvadrat (8 × 8 = 64)
  if (a4 > 0) { ctx.globalAlpha = a4; ctx.strokeStyle = '#8a1c14'; ctx.lineWidth = 5; ctx.strokeRect(-s / 2, -s / 2, s, s * ease.out(a4)); }
  ctx.globalAlpha = 1;
  // harflar (arabcha: أ ب ج د)
  ctx.fillStyle = '#2a1a0c'; ctx.font = '700 30px "Amiri"'; ctx.textAlign = 'center'; ctx.globalAlpha = a1;
  ctx.fillText('أ', -s / 2 - 22, -s / 2 - 8); ctx.fillText('ب', s / 2 + 22, -s / 2 - 8); ctx.fillText('ج', s / 2 + 22, s / 2 + 30); ctx.fillText('د', -s / 2 - 22, s / 2 + 30);
  ctx.restore();
}

// ================= Usturlob =================
function astrolabe(ctx, x, y, R, rotY, rete, a = 1) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y);
  const sx = Math.max(.08, Math.abs(Math.cos(rotY)));
  ctx.scale(sx, 1);
  const brass = (r0, r1) => { const g = ctx.createLinearGradient(-R, -R, R, R); g.addColorStop(0, '#f7dc96'); g.addColorStop(.35, '#b5822e'); g.addColorStop(.6, '#e9c06a'); g.addColorStop(1, '#6e4614'); return g; };
  // qalinlik (yon tomoni)
  ctx.fillStyle = '#5a3810'; ctx.beginPath(); ctx.arc(R * .05 * Math.sign(Math.sin(rotY)) / sx * .3, 0, R, 0, 7); ctx.fill();
  // kursi (taxt) va halqa
  ctx.fillStyle = brass(); ctx.beginPath(); ctx.moveTo(-R * .25, -R * .93); ctx.quadraticCurveTo(-R * .2, -R * 1.25, 0, -R * 1.22); ctx.quadraticCurveTo(R * .2, -R * 1.25, R * .25, -R * .93); ctx.fill();
  ctx.strokeStyle = brass(); ctx.lineWidth = R * .04; ctx.beginPath(); ctx.arc(0, -R * 1.32, R * .1, 0, 7); ctx.stroke();
  // ona disk
  ctx.fillStyle = brass(); ctx.beginPath(); ctx.arc(0, 0, R, 0, 7); ctx.fill();
  ctx.fillStyle = '#2a1c0c'; ctx.beginPath(); ctx.arc(0, 0, R * .86, 0, 7); ctx.fill();
  // daraja shkalasi
  ctx.strokeStyle = '#3a240c'; ctx.lineWidth = 1;
  for (let i = 0; i < 360; i += 2) { const an = i * Math.PI / 180, l = i % 10 ? .04 : .08; ctx.beginPath(); ctx.moveTo(R * .97 * Math.cos(an), R * .97 * Math.sin(an)); ctx.lineTo(R * (.97 - l) * Math.cos(an), R * (.97 - l) * Math.sin(an)); ctx.stroke(); }
  // plastinka: almukantaratlar (stereografik — markazi siljigan aylanalar)
  ctx.save(); ctx.beginPath(); ctx.arc(0, 0, R * .86, 0, 7); ctx.clip();
  ctx.fillStyle = '#b48a3c'; ctx.fillRect(-R, -R, 2 * R, 2 * R);
  ctx.strokeStyle = 'rgba(60,36,10,.75)'; ctx.lineWidth = 1.2;
  for (let k = 0; k < 9; k++) { const rr = R * (.82 - k * .085), cy = -R * .18 - k * R * .035; ctx.beginPath(); ctx.arc(0, cy, rr, 0, 7); ctx.stroke(); }
  for (const rr of [.3, .55, .84]) { ctx.beginPath(); ctx.arc(0, 0, R * rr, 0, 7); ctx.stroke(); }
  ctx.beginPath(); ctx.moveTo(-R, 0); ctx.lineTo(R, 0); ctx.moveTo(0, -R); ctx.lineTo(0, R); ctx.stroke();
  ctx.restore();
  // rete (aylanadigan to‘r)
  ctx.save(); ctx.rotate(rete);
  ctx.strokeStyle = brass(); ctx.lineWidth = R * .035;
  ctx.beginPath(); ctx.arc(0, -R * .22, R * .58, 0, 7); ctx.stroke(); // ekliptika
  ctx.lineWidth = R * .02; ctx.beginPath(); ctx.arc(0, 0, R * .84, 0, 7); ctx.stroke();
  for (let i = 0; i < 6; i++) { const an = i / 6 * 6.283; ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(R * .4 * Math.cos(an + .5), R * .4 * Math.sin(an + .5), R * .84 * Math.cos(an), R * .84 * Math.sin(an)); ctx.stroke(); }
  ctx.fillStyle = '#f4d68a';
  for (let i = 0; i < 9; i++) { const an = i / 9 * 6.283 + .3, rr = R * (.45 + (i % 3) * .12); ctx.beginPath(); ctx.moveTo(rr * Math.cos(an), rr * Math.sin(an)); ctx.lineTo((rr - R * .1) * Math.cos(an - .08), (rr - R * .1) * Math.sin(an - .08)); ctx.lineTo((rr - R * .1) * Math.cos(an + .08), (rr - R * .1) * Math.sin(an + .08)); ctx.fill(); }
  ctx.restore();
  // alidada
  ctx.save(); ctx.rotate(-rete * .6 + .8); ctx.fillStyle = brass(); ctx.fillRect(-R * .95, -R * .03, R * 1.9, R * .06); ctx.restore();
  ctx.fillStyle = '#f7dc96'; ctx.beginPath(); ctx.arc(0, 0, R * .05, 0, 7); ctx.fill();
  // yaltiroq
  ctx.globalCompositeOperation = 'lighter';
  const sh = ctx.createLinearGradient(-R, -R, R, R); const sp = (Math.sin(rotY * 2) * .5 + .5);
  sh.addColorStop(clamp(sp - .15), 'rgba(255,240,200,0)'); sh.addColorStop(sp, 'rgba(255,240,200,.35)'); sh.addColorStop(clamp(sp + .15), 'rgba(255,240,200,0)');
  ctx.fillStyle = sh; ctx.beginPath(); ctx.arc(0, 0, R, 0, 7); ctx.fill();
  ctx.restore();
}

// Islomiy yulduz-plitkali o‘tish
export function starWipe(ctx, p, reverse = false) {
  if (p <= 0 || p >= 1 && reverse) return;
  const s = 120;
  ctx.save();
  for (let i = -1; i <= W / s + 1; i++) for (let j = -1; j <= H / s + 1; j++) {
    const cx = i * s + (j % 2 ? s / 2 : 0), cy = j * s * .87;
    const d = (cx / W) * .75 + (cy / H) * .25;
    let q = clamp(p * 1.8 - d * .8); if (reverse) q = 1 - q;
    if (q <= 0) continue;
    const r = s * .82 * ease.inOut(q);
    ctx.beginPath();
    for (let k = 0; k < 16; k++) { const an = k / 16 * 6.283 + Math.PI / 8 * q, rr = k % 2 ? r * .62 : r; k ? ctx.lineTo(cx + rr * Math.cos(an), cy + rr * Math.sin(an)) : ctx.moveTo(cx + rr * Math.cos(an), cy + rr * Math.sin(an)); }
    ctx.closePath(); ctx.fillStyle = '#071430'; ctx.fill();
    ctx.strokeStyle = `rgba(243,213,140,${.9 * Math.sin(q * Math.PI)})`; ctx.lineWidth = 2; ctx.stroke();
  }
  ctx.restore();
}

let libBlur;
export function scene3(ctx, t, env) {
  const S = env.S;
  // A: kutubxona (0 – 3.7)
  if (t < 4.0) {
    const camZ = lerp(26.4, -1.5, ease.out(inv(0, 3.6, t)));
    drawLibrary(ctx, t, camZ, { camX: Math.sin(t * .4) * .3, camY: 2.3 + t * .05 });
    dust(ctx, t, { n: 260, alpha: .8, vx: .002, vy: -.006, size: .9 });
    flash(ctx, .8 * (1 - smooth(0, .5, t)));
    const ta = smooth(1.0, 1.6, t) * (1 - smooth(3.1, 3.5, t));
    revealText(ctx, 'BAYTUL HIKMA', W / 2, H - 170, inv(1.0, 1.8, t), { size: 54, font: FONT.title, weight: 700, color: C.gold2, track: 10, alpha: ta, S, glowA: .5 });
    revealText(ctx, 'بيت الحكمة', W / 2, H - 245, inv(1.2, 2.0, t), { size: 52, font: FONT.ar, weight: 700, color: C.gold2, alpha: ta, S, dir: 'rtl', glowA: .4 });
    revealText(ctx, '«Donishmandlik uyi» · Bag‘dod, IX asr', W / 2, H - 120, inv(1.4, 2.2, t), { size: 28, font: FONT.body, weight: 600, italic: true, color: '#e6f2ee', alpha: ta, S });
  }
  // B: qo‘lyozma (3.4 – 10)
  if (t > 3.4) {
    const a = smooth(3.4, 3.95, t);
    ctx.save(); ctx.globalAlpha = a;
    // fon: xiralashgan kutubxona (maydon chuqurligi)
    if (!libBlur) {
      libBlur = mkCanvas(W / 4, H / 4); const g = libBlur.getContext('2d');
      const big = mkCanvas(W / 2, H / 2), bg = big.getContext('2d'); bg.scale(.5, .5); drawLibrary(bg, 0, 8, { camY: 2.0 });
      g.filter = 'blur(6px) brightness(.55)'; g.drawImage(big, 0, 0, W / 4, H / 4);
    }
    const sc = 1.08 + (t - 3.4) * .01;
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(sc, sc); ctx.drawImage(libBlur, -W / 2, -H / 2, W, H); ctx.restore();
    // kitob
    const push = lerp(.94, 1.04, ease.inOut(inv(3.4, 10, t)));
    const mv = ease.inOut(inv(4.7, 5.6, t)); const bx = lerp(W / 2, 640, mv), by = lerp(H / 2 - 40, 450, mv);
    ctx.save(); ctx.translate(bx, by); ctx.scale(push * lerp(1, .74, mv), push * .92 * lerp(1, .74, mv));
    // soya
    ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.filter = `blur(${24 * S}px)`; ctx.fillRect(-680, -400, 1360, 900); ctx.filter = 'none';
    // muqova
    ctx.fillStyle = '#4a1a14'; ctx.fillRect(-668, -446, 1336, 892);
    ctx.strokeStyle = C.gold; ctx.lineWidth = 3; ctx.strokeRect(-660, -438, 1320, 876);
    // sahifalar
    const L = leftPage(), R = rightPageBase();
    ctx.drawImage(L, -650, -430, 640, 860);
    ctx.drawImage(R, 10, -430, 640, 860);
    // o‘ng sahifa: diagramma
    khwarizmiDiagram(ctx, 330, -60, 400, inv(4.5, 7.6, t));
    ctx.save(); ctx.direction = 'rtl'; ctx.textAlign = 'center'; ctx.fillStyle = '#8a1c14'; ctx.font = '700 34px "Amiri"'; ctx.globalAlpha = smooth(4.3, 4.9, t);
    ctx.fillText('باب المال والأجذار', 330, -340); ctx.restore();
    // umurtqa soyasi
    const sp = ctx.createLinearGradient(-90, 0, 90, 0);
    sp.addColorStop(0, 'rgba(60,30,10,0)'); sp.addColorStop(.45, 'rgba(60,30,10,.45)'); sp.addColorStop(.55, 'rgba(60,30,10,.45)'); sp.addColorStop(1, 'rgba(60,30,10,0)');
    ctx.fillStyle = sp; ctx.fillRect(-90, -430, 180, 860);
    // varaq aylanishi
    const fp = ease.inOut(inv(3.6, 4.5, t));
    if (fp > 0 && fp < 1) {
      const ang = fp * Math.PI, sx = Math.cos(ang);
      ctx.save(); ctx.translate(0, 0); ctx.scale(sx, 1 + Math.sin(ang) * .04);
      ctx.drawImage(sx > 0 ? rightPageBase() : leftPage(), sx > 0 ? 10 : -650 + 0, -430, 640, 860);
      ctx.fillStyle = `rgba(40,20,5,${.45 * Math.sin(ang)})`; ctx.fillRect(sx > 0 ? 10 : -650, -430, 640, 860);
      ctx.restore();
    }
    // sham yorug‘i
    const lg = ctx.createRadialGradient(-300, -500, 50, -100, -200, 1300);
    lg.addColorStop(0, 'rgba(255,200,120,.22)'); lg.addColorStop(1, 'rgba(0,0,0,.35)');
    ctx.fillStyle = lg; ctx.fillRect(-680, -450, 1360, 900);
    ctx.restore();
    // golografik tenglama
    const eqx = 1180, eqy = 190;
    const steps = [[5.0, 'x² + 10x = 39'], [5.8, '(x + 5)² = 39 + 25 = 64'], [6.6, 'x + 5 = 8   →   x = 3']];
    steps.forEach(([st, s], k) => {
      const p = inv(st, st + .6, t), q = smooth(st + 1.0, st + 1.3, t) * (k < 2 ? 1 : 0);
      const al = (1 - q * .55) * (1 - smooth(9.3, 9.7, t));
      revealText(ctx, s, eqx, eqy + k * 62, p, { size: 44, font: FONT.body, weight: 600, color: k === 2 ? C.gold3 : C.turq2, align: 'left', alpha: al, S, glowA: .6 });
    });
    // usturlob
    const asA = smooth(6.2, 7.0, t);
    if (asA > 0) {
      const ax = 1580, ay = 590;
      glow(ctx, ax, ay, 420, .35 * asA, '255,200,120', .1);
      astrolabe(ctx, ax, ay + (1 - ease.out(asA)) * 60, 165, Math.sin(t * .55) * .55 + .2, t * .35, asA);
      revealText(ctx, 'USTURLOB', ax, ay + 228, inv(7.0, 7.6, t), { size: 26, font: FONT.title, weight: 700, color: C.gold2, track: 8, alpha: 1 - smooth(9.3, 9.7, t), S });
    }
    // olimlar kartalari
    const cards = [
      ['taxm. 780 – 850', 'AL-XORAZMIY', 'Algebra va algoritm asoschisi'],
      ['980 – 1037', 'IBN SINO', '«Tib qonunlari», 1025-yil'],
      ['973 – 1048', 'AL-BERUNIY', 'Yer radiusini o‘lchadi'],
      ['965 – 1040', 'IBN AL-HAYSAM', '«Optika kitobi»'],
    ];
    cards.forEach(([y, n, s], k) => {
      const st = 7.0 + k * .35;
      ctx.save(); ctx.globalAlpha = 1 - smooth(9.3, 9.7, t);
      infoCard(ctx, 70 + k * 452, 862, 430, 150, inv(st, st + .7, t), { year: y, title: n, sub: s, S });
      ctx.restore();
    });
    dust(ctx, t, { n: 160, alpha: .6, vx: .002, vy: -.005 });
    ctx.restore();
  }
  starWipe(ctx, inv(9.25, 10, t));
  return { bloom: .5, vignette: .8 };
}

// ================= 5-sahna: ilm va meros =================
const toAr = s => s.replace(/[0-9]/g, d => '٠١٢٣٤٥٦٧٨٩'[d]).replace('.', '٫');
function zijPage() {
  if (pageCache.Z) return pageCache.Z;
  const w = 900, h = 1150, c = parchment(w, h, 17), g = c.getContext('2d');
  frameBorder(g, w, h, 40);
  shamsa(g, w / 2, 160, 56);
  g.direction = 'rtl'; g.textAlign = 'center';
  g.fillStyle = '#8a1c14'; g.font = '700 54px "Amiri"'; g.fillText('جدول الجيب', w / 2, 300);
  // jadval
  const x0 = 170, x1 = w - 170, y0 = 350, rh = 52;
  g.strokeStyle = '#a87a28'; g.lineWidth = 1.5;
  g.fillStyle = '#2a1a0c'; g.font = '700 36px "Amiri"';
  g.fillText('القوس', x1 - 120, y0 + 38); g.fillText('الجيب', x0 + 160, y0 + 38);
  g.strokeRect(x0, y0, x1 - x0, rh * 13);
  for (let i = 1; i <= 13; i++) { g.beginPath(); g.moveTo(x0, y0 + rh * i); g.lineTo(x1, y0 + rh * i); g.stroke(); }
  g.beginPath(); g.moveTo((x0 + x1) / 2 + 60, y0); g.lineTo((x0 + x1) / 2 + 60, y0 + rh * 13); g.stroke();
  g.font = '400 34px "Amiri"';
  for (let d = 1; d <= 12; d++) {
    const s = Math.sin(d * Math.PI / 180).toFixed(4);
    g.fillStyle = '#2a1a0c'; g.fillText(toAr(String(d)), x1 - 120, y0 + rh * d + 38);
    g.fillStyle = d % 2 ? '#2a1a0c' : '#8a1c14'; g.fillText(toAr(s), x0 + 160, y0 + rh * d + 38);
  }
  pageCache.Z = c; return c;
}
const STARS = [
  ['Dubhe', 165.93, 61.75], ['Merak', 165.46, 56.38], ['Phecda', 178.46, 53.69], ['Megrez', 183.86, 57.03], ['Alioth', 193.51, 55.96], ['Mizar', 200.98, 54.93], ['Alkaid', 206.89, 49.31],
  ['Betelgeuse', 88.79, 7.41], ['Bellatrix', 81.28, 6.35], ['Alnitak', 85.19, -1.94], ['Alnilam', 84.05, -1.2], ['Mintaka', 83.0, -.3], ['Saiph', 86.94, -9.67], ['Rigel', 78.63, -8.2],
  ['Aldebaran', 68.98, 16.51], ['Altair', 297.7, 8.87], ['Vega', 279.23, 38.78], ['Deneb', 310.36, 45.28],
  ['Caph', 2.29, 59.15], ['Schedar', 10.13, 56.54], ['Gamma Cas', 14.18, 60.72], ['Ruchbah', 21.45, 60.24], ['Segin', 28.6, 63.67],
];
const CONST = [[0, 1], [1, 2], [2, 3], [3, 0], [3, 4], [4, 5], [5, 6], [7, 9], [8, 11], [9, 10], [10, 11], [9, 12], [11, 13], [7, 8], [18, 19], [19, 20], [20, 21], [21, 22], [16, 17], [17, 15], [15, 16]];
const LABELED = { Aldebaran: 'Aldebaran · الدبران', Altair: 'Altair · الطائر', Vega: 'Vega · الواقع', Rigel: 'Rigel · رجل', Deneb: 'Deneb · ذنب', Betelgeuse: 'Betelgeuse · يد الجوزاء' };
const BGSTARS = (() => { const r = rng(55), a = []; for (let i = 0; i < 700; i++) a.push([r() * 360, Math.asin(r() * 2 - 1) * 180 / Math.PI, r()]); return a; })();
function starSphere(ctx, cx, cy, R, rotA, tilt, a, t, S) {
  if (a <= 0) return;
  const D = Math.PI / 180;
  const pr = (ra, dec) => {
    const x0 = Math.cos(dec * D) * Math.cos(ra * D + rotA), y0 = Math.sin(dec * D), z0 = Math.cos(dec * D) * Math.sin(ra * D + rotA);
    const y1 = y0 * Math.cos(tilt) - z0 * Math.sin(tilt), z1 = y0 * Math.sin(tilt) + z0 * Math.cos(tilt);
    return [cx + R * x0, cy - R * y1, z1];
  };
  ctx.save(); ctx.globalAlpha = a;
  // sfera halqalari
  ctx.strokeStyle = 'rgba(127,227,216,.25)'; ctx.lineWidth = 1.2;
  for (let dec = -60; dec <= 60; dec += 30) { ctx.beginPath(); for (let ra = 0; ra <= 360; ra += 5) { const p = pr(ra, dec); ra ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); } ctx.stroke(); }
  for (let ra = 0; ra < 360; ra += 30) { ctx.beginPath(); for (let dec = -90; dec <= 90; dec += 5) { const p = pr(ra, dec); dec > -90 ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); } ctx.stroke(); }
  // ekliptika (23.44°)
  ctx.strokeStyle = 'rgba(243,213,140,.8)'; ctx.lineWidth = 2.2; ctx.shadowColor = 'rgba(255,200,110,.8)'; ctx.shadowBlur = 8; ctx.beginPath();
  for (let l = 0; l <= 360; l += 4) { const lr = l * D, e = 23.44 * D; const ra = Math.atan2(Math.sin(lr) * Math.cos(e), Math.cos(lr)) / D, dec = Math.asin(Math.sin(e) * Math.sin(lr)) / D; const p = pr(ra, dec); l ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); }
  ctx.stroke(); ctx.shadowBlur = 0;
  ctx.strokeStyle = 'rgba(127,227,216,.6)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.stroke();
  ctx.restore();
  for (const [ra, dec, m] of BGSTARS) { const p = pr(ra, dec); const al = a * (p[2] > 0 ? 1 : .25) * (.3 + m * .7); glow(ctx, p[0], p[1], 3 + m * 5, al, '220,235,255', .35); }
  ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = 'rgba(243,213,140,.75)'; ctx.lineWidth = 1.6;
  const cp = ease.inOut(inv(3.8, 5.2, t + 40) );
  for (const [i, j] of CONST) { const p = pr(STARS[i][1], STARS[i][2]), q = pr(STARS[j][1], STARS[j][2]); if (p[2] < -.2 || q[2] < -.2) continue; ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(lerp(p[0], q[0], cp), lerp(p[1], q[1], cp)); ctx.stroke(); }
  ctx.restore();
  for (const [n, ra, dec] of STARS) {
    const p = pr(ra, dec); if (p[2] < -.3) continue; const al = a * (p[2] > 0 ? 1 : .4);
    glow(ctx, p[0], p[1], 22, al, '255,236,190', .3);
    if (LABELED[n] && p[2] > .1) text(ctx, LABELED[n], p[0] + 16, p[1] - 12, { size: 22, font: FONT.body, weight: 600, align: 'left', color: '#f3e6c4', alpha: al * smooth(4.2, 4.8, t + 40) });
  }
}
function flowCurve(a, b, bend) { const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2; const dx = b[0] - a[0], dy = b[1] - a[1]; return [a, [mx - dy * bend, my + dx * bend], b]; }
function bez(c, u) { const [a, m, b] = c; return [(1 - u) * (1 - u) * a[0] + 2 * u * (1 - u) * m[0] + u * u * b[0], (1 - u) * (1 - u) * a[1] + 2 * u * (1 - u) * m[1] + u * u * b[1]]; }

export function scene5(ctx, t, env) {
  const S = env.S;
  const bg = ctx.createRadialGradient(W / 2, H / 2, 80, W / 2, H / 2, W * .75);
  bg.addColorStop(0, '#0e2650'); bg.addColorStop(.6, '#071430'); bg.addColorStop(1, '#02060f');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  // fon naqshi
  ctx.save(); ctx.globalAlpha = .08; ctx.translate(W / 2, H / 2); ctx.rotate(t * .02);
  const L = []; for (let i = -8; i <= 8; i++) for (let j = -5; j <= 5; j++) L.push(...khatamTile(i * 140, j * 140, 140));
  drawLines(ctx, L, 1, { width: 1.2, glowA: 0 }); ctx.restore();
  starWipe(ctx, 1 - inv(0, .5, t), false);

  // A: Zij sahifasi (0 – 3.4)
  if (t < 3.6) {
    const pa = smooth(0, .4, t) * (1 - smooth(2.9, 3.5, t));
    const sc = lerp(.82, .95, ease.inOut(inv(0, 3.4, t)));
    const pg = zijPage();
    ctx.save(); ctx.globalAlpha = pa; ctx.translate(W / 2 - 330, H / 2 + 40); ctx.rotate(-.05); ctx.scale(sc, sc);
    ctx.fillStyle = 'rgba(0,0,0,.5)'; ctx.filter = `blur(${20 * S}px)`; ctx.fillRect(-440, -560, 900, 1150); ctx.filter = 'none';
    ctx.drawImage(pg, -450, -575, 900, 1150);
    // siyoh oltin zarrachaga aylanadi
    const dis = inv(1.8, 3.2, t);
    if (dis > 0) {
      const r = rng(4);
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 500; i++) {
        const x0 = -280 + r() * 560, y0 = -260 + r() * 640, dl = r() * .5, q = clamp((dis - dl) * 2);
        if (q <= 0) continue;
        const x = x0 + q * q * (500 + r() * 500), y = y0 - q * q * (300 + r() * 300) + Math.sin(q * 6 + i) * 30;
        ctx.globalAlpha = (1 - q) * .9; ctx.drawImage(glowSpr(), x - 8, y - 8, 16, 16);
      }
    }
    ctx.restore();
    revealText(ctx, 'JIB (SINUS) JADVALI', W / 2 + 330, H / 2 - 60, inv(.4, 1.2, t), { size: 44, font: FONT.title, weight: 700, color: C.gold2, align: 'left', track: 4, alpha: 1 - smooth(2.6, 3.1, t), S, glowA: .4 });
    revealText(ctx, 'Trigonometriya islom olimlari qo‘lida', W / 2 + 330, H / 2 - 8, inv(.7, 1.5, t), { size: 30, font: FONT.body, weight: 600, italic: true, color: '#e6f2ee', align: 'left', alpha: 1 - smooth(2.6, 3.1, t), S });
    revealText(ctx, 'mustaqil fanga aylandi', W / 2 + 330, H / 2 + 32, inv(.8, 1.6, t), { size: 30, font: FONT.body, weight: 600, italic: true, color: '#e6f2ee', align: 'left', alpha: 1 - smooth(2.6, 3.1, t), S });
  }
  // B: osmon sferasi (3.0 – 6.8)
  if (t > 2.9 && t < 7.0) {
    const a = smooth(2.9, 3.6, t) * (1 - smooth(6.3, 6.9, t));
    const R = lerp(300, 380, ease.out(inv(2.9, 6.8, t)));
    starSphere(ctx, W / 2 + 280, H / 2 + 10, R, t * .18 + 1.2, .45, a, t - 40, S);
    ctx.save(); ctx.globalAlpha = a;
    revealText(ctx, 'ULUG‘BEK RASADXONASI', 120, 230, inv(3.3, 4.0, t), { size: 44, font: FONT.title, weight: 700, color: C.gold2, align: 'left', track: 3, S, glowA: .4 });
    revealText(ctx, 'Samarqand · 1420-yillar', 120, 280, inv(3.5, 4.2, t), { size: 30, font: FONT.body, weight: 600, italic: true, color: '#e6f2ee', align: 'left', S });
    revealText(ctx, '«Ziji Ko‘ragoniy» — 1018 yulduz katalogi', 120, 330, inv(3.7, 4.4, t), { size: 30, font: FONT.body, weight: 600, color: C.turq2, align: 'left', S });
    // suzuvchi formulalar
    const F = [['0 1 2 3 4 5 6 7 8 9', 120, 470, 3.9], ['al-Xwārizmī  →  Algoritmi  →  algoritm', 120, 530, 4.4], ['sin²α + cos²α = 1', 120, 590, 4.9]];
    F.forEach(([s, x, y, st]) => revealText(ctx, s, x, y + Math.sin(t + x) * 4, inv(st, st + .6, t), { size: 36, font: FONT.body, weight: 600, color: C.gold3, align: 'left', S, glowA: .5 }));
    revealText(ctx, 'Ko‘plab yulduz nomlari arabcha: Aldebaran, Altair, Vega, Rigel…', 120, 700, inv(5.1, 5.8, t), { size: 26, font: FONT.body, weight: 500, italic: true, color: 'rgba(230,240,236,.85)', align: 'left', S });
    ctx.restore();
  }
  // C: bilim uzatilishi tarmog‘i (6.4 – 10)
  if (t > 6.3) {
    const a = smooth(6.3, 6.9, t);
    const conv = ease.in(inv(9.0, 9.9, t));
    const N = {
      gr: [330, 300, 'YUNON', 'Aristotel, Ptolemey, Evklid'], in: [330, 540, 'HIND', 'O‘nlik sanoq, sinus'], fa: [330, 780, 'FORS', 'Astronomiya, tibbiyot'],
      bg: [960, 540, 'BAG‘DOD', 'Baytul Hikma'], es: [1500, 380, 'ANDALUS', 'Kordova · Toledo'], eu: [1590, 700, 'YEVROPA', 'Lotin tarjimalari, XII asr'],
    };
    const E = [['gr', 'bg', .15, 6.6], ['in', 'bg', 0, 6.75], ['fa', 'bg', -.15, 6.9], ['bg', 'es', .2, 7.5], ['bg', 'eu', -.15, 7.7], ['es', 'eu', .25, 8.1]];
    const cpos = k => { const n = N[k]; return [lerp(n[0], W / 2, conv), lerp(n[1], H / 2, conv)]; };
    ctx.save(); ctx.globalAlpha = a * (1 - conv * .6);
    for (const [x, y, st] of E.map(([p, q, b, st]) => [p, q, st])) {
      const k = E.find(e => e[0] === x && e[1] === y);
      const c = flowCurve(cpos(x), cpos(y), k[2]); const p = ease.inOut(inv(st, st + .7, t));
      if (p <= 0) continue;
      ctx.strokeStyle = 'rgba(243,213,140,.55)'; ctx.lineWidth = 2; ctx.beginPath();
      for (let i = 0; i <= 40 * p; i++) { const q = bez(c, i / 40); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); } ctx.stroke();
      // oqayotgan zarrachalar
      for (let i = 0; i < 9; i++) { const u = ((t * .45 + i / 9) % 1); if (u > p) continue; const q = bez(c, u); glow(ctx, q[0], q[1], 14, .9, i % 3 ? '255,220,150' : '127,227,216', .3); }
    }
    ctx.restore();
    for (const k in N) {
      const [x0, y0, name, sub] = N[k]; const [x, y] = cpos(k);
      const st = { gr: 6.4, in: 6.5, fa: 6.6, bg: 6.9, es: 7.7, eu: 8.0 }[k];
      const p = inv(st, st + .5, t); if (p <= 0) continue;
      const big = k === 'bg';
      glow(ctx, x, y, (big ? 110 : 60) * ease.out(p), a, big ? '255,214,140' : '127,227,216', .25);
      ctx.save(); ctx.globalAlpha = a * ease.out(p); ctx.strokeStyle = C.gold2; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, big ? 34 : 18, 0, 7); ctx.stroke();
      ctx.translate(x, y); ctx.rotate(t * .5);
      if (big) { for (const [aa, bb] of starPoly(8, 3, 50, 0)) { ctx.beginPath(); ctx.moveTo(aa[0], aa[1]); ctx.lineTo(bb[0], bb[1]); ctx.stroke(); } }
      ctx.restore();
      const ta = a * (1 - conv);
      revealText(ctx, name, x, y + (big ? 90 : 56), p, { size: big ? 40 : 30, font: FONT.title, weight: 700, color: C.gold2, track: 4, alpha: ta, S, glowA: .3 });
      revealText(ctx, sub, x, y + (big ? 128 : 88), clamp(p - .2), { size: big ? 28 : 24, font: FONT.body, weight: 600, italic: true, color: '#e2efeb', alpha: ta, S });
    }
    // vaqt chizig‘i
    const tl = a * (1 - conv);
    if (tl > 0) {
      const items = [['762', 'Bag‘dod'], ['IX asr', 'Baytul Hikma'], ['1025', 'Tib qonunlari'], ['1145', 'Algebra lotin tilida'], ['1437', 'Ulug‘bek Ziji']];
      const x0 = 260, x1 = 1660, y = H - 92, pr = inv(6.6, 8.8, t);
      ctx.save(); ctx.globalAlpha = tl;
      ctx.strokeStyle = 'rgba(243,213,140,.3)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
      ctx.strokeStyle = C.gold2; ctx.shadowColor = 'rgba(255,200,110,.9)'; ctx.shadowBlur = 10; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(lerp(x0, x1, pr), y); ctx.stroke(); ctx.restore();
      items.forEach(([yr, lab], k) => {
        const x = lerp(x0, x1, k / 4), on = pr >= k / 4 - .001;
        ctx.save(); ctx.globalAlpha = tl; ctx.fillStyle = on ? C.gold3 : 'rgba(243,213,140,.4)'; ctx.beginPath(); ctx.arc(x, y, on ? 6 : 4, 0, 7); ctx.fill(); ctx.restore();
        text(ctx, yr, x, y - 22, { size: 26, font: FONT.title, weight: 700, color: on ? C.gold3 : 'rgba(243,213,140,.5)', alpha: tl, track: 2 });
        text(ctx, lab, x, y + 36, { size: 24, font: FONT.body, weight: 600, italic: true, color: on ? '#e6f2ee' : 'rgba(230,242,238,.45)', alpha: tl });
      });
    }
    // yakuniy nur
    glow(ctx, W / 2, H / 2, 200 + 1400 * conv, conv, '255,226,170', .15);
  }
  dust(ctx, t, { n: 240, alpha: .7, vx: .003, vy: -.008, zoom: ease.in(inv(8.8, 10, t)) * 1.5, swirl: ease.in(inv(8.6, 10, t)) * 2 });
  flash(ctx, ease.in(inv(9.3, 10, t)) * 1.1);
  return { bloom: .55, vignette: .8, goldFade: ease.in(inv(9.5, 10, t)) * .6 };
}
let _gs; function glowSpr() { if (!_gs) { _gs = mkCanvas(32, 32); const g = _gs.getContext('2d'); const r = g.createRadialGradient(16, 16, 0, 16, 16, 16); r.addColorStop(0, 'rgba(255,225,160,1)'); r.addColorStop(1, 'rgba(255,200,120,0)'); g.fillStyle = r; g.fillRect(0, 0, 32, 32); } return _gs; }
