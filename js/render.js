// Kadrni canvasga chizish: fon/video, sarlavha (hook) va subtitrlar.
// Ko‘rish oynasi ham, eksport ham shu funksiyadan foydalanadi, shuning uchun natija bir xil.

import { BACKGROUNDS } from './templates.js';

export const ASPECTS = { '9:16': [9, 16], '1:1': [1, 1], '4:5': [4, 5], '16:9': [16, 9] };

export function canvasSize(aspect, short = 720) {
  const [a, b] = ASPECTS[aspect] || ASPECTS['9:16'];
  return a <= b ? [short, Math.round((short * b) / a)] : [Math.round((short * a) / b), short];
}

function roundRect(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function drawCover(ctx, src, sw, sh, W, H) {
  const s = Math.max(W / sw, H / sh);
  const w = sw * s, h = sh * s;
  ctx.drawImage(src, (W - w) / 2, (H - h) / 2, w, h);
}
function drawContain(ctx, src, sw, sh, W, H) {
  const s = Math.min(W / sw, H / sh);
  const w = sw * s, h = sh * s;
  ctx.drawImage(src, (W - w) / 2, (H - h) / 2, w, h);
}

const supportsFilter = (() => {
  try { const c = document.createElement('canvas').getContext('2d'); c.filter = 'blur(2px)'; return c.filter === 'blur(2px)'; }
  catch { return false; }
})();

function drawGradientBg(ctx, W, H, bgIndex, t) {
  const [c1, c2] = BACKGROUNDS[bgIndex % BACKGROUNDS.length];
  const g = ctx.createLinearGradient(0, 0, W * 0.4, H);
  g.addColorStop(0, c1);
  g.addColorStop(1, c2);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  // sekin suzuvchi yorug‘ dog‘lar
  ctx.save();
  ctx.globalCompositeOperation = 'soft-light';
  for (let i = 0; i < 3; i++) {
    const x = W * (0.5 + 0.35 * Math.sin(t * 0.35 + i * 2.1));
    const y = H * (0.45 + 0.3 * Math.cos(t * 0.27 + i * 1.7));
    const r = Math.max(W, H) * (0.35 + 0.1 * i);
    const rg = ctx.createRadialGradient(x, y, 0, x, y, r);
    rg.addColorStop(0, 'rgba(255,255,255,0.55)');
    rg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = rg;
    ctx.fillRect(0, 0, W, H);
  }
  ctx.restore();
}

/**
 * media: { el, w, h, kind: 'video'|'image' } yoki null
 * opts: { aspect, fit, bgMode, bgColor, bgIndex, style, fontScale, pos, maxWords, hook, hookStyle, segments }
 */
export function drawFrame(ctx, W, H, opts, t, media) {
  ctx.save();
  ctx.clearRect(0, 0, W, H);
  if (media && media.w) {
    if (opts.fit === 'contain') {
      if (opts.bgMode === 'color') {
        ctx.fillStyle = opts.bgColor || '#000';
        ctx.fillRect(0, 0, W, H);
      } else {
        ctx.save();
        if (supportsFilter) ctx.filter = `blur(${Math.round(Math.min(W, H) * 0.04)}px) brightness(0.6)`;
        drawCover(ctx, media.el, media.w, media.h, W, H);
        ctx.restore();
        if (!supportsFilter) { ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(0, 0, W, H); }
      }
      drawContain(ctx, media.el, media.w, media.h, W, H);
    } else {
      drawCover(ctx, media.el, media.w, media.h, W, H);
    }
  } else {
    drawGradientBg(ctx, W, H, opts.bgIndex || 0, t);
  }
  ctx.restore();

  if (opts.hook) drawHook(ctx, W, H, opts.hook, opts.hookStyle, opts.style);
  const seg = findSegment(opts.segments, t);
  if (seg) drawCaption(ctx, W, H, seg, t, opts);
}

export function findSegment(segments, t) {
  if (!segments) return null;
  for (const s of segments) if (t >= s.start && t < s.end && s.text.trim()) return s;
  return null;
}

function fontString(st, px) {
  return `${st.italic ? 'italic ' : ''}${st.weight} ${px}px "${st.font}", "Manrope", sans-serif`;
}

function drawHook(ctx, W, H, text, kind, st) {
  const px = Math.round(Math.min(W, H) * 0.052);
  ctx.save();
  ctx.font = `800 ${px}px "Montserrat", "Manrope", sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const lines = wrapText(ctx, text, W * 0.8);
  const lh = px * 1.25;
  const padX = px * 0.6, padY = px * 0.35;
  const top = H * (W > H ? 0.08 : 0.1);
  lines.forEach((line, i) => {
    const w = ctx.measureText(line).width;
    const y = top + i * (lh + padY * 0.6);
    const bx = W / 2 - w / 2 - padX, by = y - lh / 2 - padY / 2, bw = w + padX * 2, bh = lh + padY;
    if (kind === 'outline') {
      ctx.lineJoin = 'round';
      ctx.lineWidth = px * 0.18;
      ctx.strokeStyle = '#000';
      ctx.strokeText(line, W / 2, y);
      ctx.fillStyle = '#fff';
      ctx.fillText(line, W / 2, y);
    } else {
      ctx.fillStyle = kind === 'accent' ? '#ffb23f' : '#ffffff';
      roundRect(ctx, bx, by, bw, bh, px * 0.35);
      ctx.fill();
      ctx.fillStyle = '#13111b';
      ctx.fillText(line, W / 2, y + px * 0.04);
    }
  });
  ctx.restore();
}

function wrapText(ctx, text, maxW) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}

// So‘zlarga vaqt taqsimlash: uzunroq so‘z ko‘proq vaqt oladi
export function wordTimings(seg) {
  if (seg._wt && seg._wtKey === seg.text + seg.start + seg.end) return seg._wt;
  const words = seg.text.trim().split(/\s+/).filter(Boolean);
  const weights = words.map((w) => w.length + 2);
  const total = weights.reduce((a, b) => a + b, 0) || 1;
  const dur = seg.end - seg.start;
  let acc = seg.start;
  const res = words.map((w, i) => {
    const s = acc;
    acc += (weights[i] / total) * dur;
    return { w, s, e: acc };
  });
  Object.defineProperty(seg, '_wt', { value: res, writable: true, configurable: true, enumerable: false });
  Object.defineProperty(seg, '_wtKey', { value: seg.text + seg.start + seg.end, writable: true, configurable: true, enumerable: false });
  return res;
}

const easeOutBack = (x) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };

function drawCaption(ctx, W, H, seg, t, opts) {
  const st = opts.style;
  const words = wordTimings(seg);
  if (!words.length) return;
  let active = words.findIndex((w) => t >= w.s && t < w.e);
  if (active < 0) active = words.length - 1;

  const mw = opts.maxWords != null && opts.maxWords !== '' ? Number(opts.maxWords) : st.maxWords;
  let from = 0, to = words.length;
  if (mw > 0) { from = Math.floor(active / mw) * mw; to = Math.min(words.length, from + mw); }
  const visible = words.slice(from, to);
  const chunkStart = visible[0].s;

  const px = Math.round(Math.min(W, H) * st.size * (opts.fontScale || 1));
  ctx.save();
  ctx.font = fontString(st, px);
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  const colorMain = opts.colorMain || st.color;
  const colorActive = opts.colorActive || st.active;

  // qatorlarga bo‘lish
  const maxW = W * 0.86;
  const space = ctx.measureText(' ').width;
  const items = visible.map((v, i) => {
    const text = st.upper ? v.w.toLocaleUpperCase('uz') : v.w;
    return { ...v, text, idx: from + i, width: ctx.measureText(text).width };
  });
  const lines = [];
  let line = [], lw = 0;
  for (const it of items) {
    const add = line.length ? space + it.width : it.width;
    if (line.length && lw + add > maxW) { lines.push({ items: line, w: lw }); line = [it]; lw = it.width; }
    else { line.push(it); lw += add; }
  }
  if (line.length) lines.push({ items: line, w: lw });

  const lh = px * (st.font === 'Bebas Neue' ? 1.0 : 1.22);
  const pos = opts.pos != null ? opts.pos : (st.pos || 0.72);
  const blockH = lines.length * lh;
  let y0 = H * pos - blockH / 2 + lh / 2;
  y0 = Math.max(lh, Math.min(H - blockH + lh / 2 - lh * 0.4, y0));

  // blok animatsiyasi
  const since = t - chunkStart;
  let alpha = 1, scale = 1;
  if (st.anim === 'fade') alpha = Math.min(1, Math.max(0, (t - seg.start) / 0.25));
  if (st.anim === 'bounce') scale = 0.6 + 0.4 * easeOutBack(Math.min(1, Math.max(0, since / 0.22)));
  ctx.globalAlpha = alpha;

  const cx = W / 2;
  const cy = y0 + blockH / 2 - lh / 2;
  if (scale !== 1) { ctx.translate(cx, cy); ctx.scale(scale, scale); ctx.translate(-cx, -cy); }

  // umumiy quti
  if (st.box && !st.perLineBox) {
    const bw = Math.max(...lines.map((l) => l.w)) + px * 0.9;
    roundRect(ctx, cx - bw / 2, y0 - lh / 2 - px * 0.25, bw, blockH + px * 0.5, px * 0.3);
    ctx.fillStyle = st.boxColor;
    ctx.fill();
  }

  lines.forEach((ln, li) => {
    const y = y0 + li * lh;
    let x = cx - ln.w / 2;
    if (st.box && st.perLineBox) {
      roundRect(ctx, x - px * 0.3, y - lh / 2, ln.w + px * 0.6, lh, px * 0.15);
      ctx.fillStyle = st.boxColor;
      ctx.fill();
    }
    for (const it of ln.items) {
      const isActive = it.idx === active;
      const spoken = it.idx < active;
      if (st.anim === 'typewriter' && it.idx > active) { x += it.width + space; continue; }

      let color = colorMain;
      let s = 1;
      if (st.anim === 'karaoke' && (isActive || spoken)) color = colorActive;
      if (st.anim === 'pop' && isActive) { color = colorActive; s = 1 + 0.14 * Math.min(1, (t - it.s) / 0.08); }
      if (st.anim === 'bounce' && isActive) color = colorActive;
      if (st.anim === 'highlight' && isActive) {
        ctx.save();
        ctx.fillStyle = st.activeBg;
        roundRect(ctx, x - px * 0.18, y - lh * 0.48, it.width + px * 0.36, lh * 0.96, px * 0.2);
        ctx.fill();
        ctx.restore();
        color = colorActive;
      }

      ctx.save();
      const wx = x + it.width / 2;
      if (s !== 1) { ctx.translate(wx, y); ctx.scale(s, s); ctx.translate(-wx, -y); }
      if (st.shadow) { ctx.shadowColor = st.shadowColor; ctx.shadowBlur = st.shadow * (px / 50); }
      if (st.stroke) {
        ctx.lineJoin = 'round';
        ctx.miterLimit = 2;
        ctx.lineWidth = px * st.stroke;
        ctx.strokeStyle = st.strokeColor;
        ctx.strokeText(it.text, x, y);
        ctx.shadowBlur = 0;
      }
      ctx.fillStyle = color;
      ctx.fillText(it.text, x, y);
      if (st.anim === 'neon' || (st.shadow && !st.stroke && isActive)) ctx.fillText(it.text, x, y);
      ctx.restore();
      x += it.width + space;
    }
  });
  ctx.restore();
}
