// Kadr dispetcheri: vaqt (soniya) bo‘yicha sahnani tanlaydi va post-ishlovni qo‘llaydi.
import { W, H, post, clamp, smooth } from './core.js';
import { scene1, scene2 } from './scenes_a.js';
import { scene3, scene5 } from './scenes_b.js';
import { initGL, scene4, scene6 } from './scenes_3d.js';

const Q = new URLSearchParams(location.search);
const S = +(Q.get('scale') || 1);
const cvs = document.getElementById('out');
cvs.width = W * S; cvs.height = H * S;
const ctx = cvs.getContext('2d', { alpha: false });
const glc = document.getElementById('gl');
glc.width = W * S; glc.height = H * S;

const fontsReady = Promise.all([
  '900 40px "Cinzel"', '700 40px "Cinzel"', '400 40px "Cinzel"', '500 40px "Cormorant"', '600 40px "Cormorant"',
  'italic 600 40px "Cormorant"', '400 40px "Amiri"', '700 40px "Amiri"', '600 40px "ReemKufi"', '700 40px "ArefRuqaa"',
].map(f => document.fonts.load(f, f.includes('Amiri') || f.includes('Kufi') || f.includes('Ruqaa') ? 'العلم' : 'Aa‘ʻ'))).then(() => document.fonts.ready);

const ready = (async () => { await fontsReady; await initGL(glc, S); })();

function draw(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, cvs.width, cvs.height);
  ctx.setTransform(S, 0, 0, S, 0, 0);
  const env = { S, ctx, gl: glc };
  let pp = { S, bloom: .5, vignette: .7, grain: .05 };
  if (t < 10) Object.assign(pp, scene1(ctx, t, env));
  else if (t < 20) Object.assign(pp, scene2(ctx, t - 10, env));
  else if (t < 30) Object.assign(pp, scene3(ctx, t - 20, env));
  else if (t < 40) Object.assign(pp, scene4(ctx, t - 30, env));
  else if (t < 50) Object.assign(pp, scene5(ctx, t - 40, env));
  else Object.assign(pp, scene6(ctx, t - 50, env));
  post(ctx, cvs, t, pp);
}

window.renderFrame = async (t) => { await ready; draw(t); return true; };
window.grab = (q = .93) => cvs.toDataURL('image/jpeg', q);
window.ready = ready;
if (Q.has('t')) ready.then(() => draw(+Q.get('t')));
