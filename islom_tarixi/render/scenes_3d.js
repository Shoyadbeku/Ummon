// 3D sahnalar (three.js): 4-sahna me’morchilik parvozi, 6-sahna Registon — quyosh botishi.
import * as THREE from './assets/three.module.js';
import { W, H, C, clamp, lerp, inv, smooth, ease, rng, glow, dust, rosette, starPoly, drawLines, title3D, text, revealText, flash, lensFlare, FONT, mkCanvas } from './core.js';
import { starWipe } from './scenes_b.js';

let R, glCanvas, SC = 1;
const scenes = {};

// ------------------------------------------------------------ teksturalar
function canvasTex(w, h, draw, { repeat = [1, 1], srgb = true } = {}) {
  const c = mkCanvas(w, h), g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.needsUpdate = true; return t;
}
function star8(g, cx, cy, r) {
  g.beginPath();
  for (let k = 0; k < 16; k++) { const a = k / 16 * Math.PI * 2 + Math.PI / 8, rr = k % 2 ? r * .7 : r; k ? g.lineTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a)) : g.moveTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a)); }
  g.closePath();
}
function noiseFill(g, w, h, seed, a, cols) {
  const r = rng(seed); g.globalAlpha = a;
  for (let i = 0; i < w * h / 60; i++) { g.fillStyle = cols[Math.floor(r() * cols.length)]; g.fillRect(r() * w, r() * h, 1 + r() * 2, 1 + r() * 2); }
  g.globalAlpha = 1;
}
let TX;
function textures() {
  if (TX) return TX;
  TX = {};
  // Temuriylar koshinkori mozaikasi
  TX.mosaic = canvasTex(1024, 1024, (g, w, h) => {
    g.fillStyle = '#163a86'; g.fillRect(0, 0, w, h);
    const s = 128;
    for (let i = 0; i <= 8; i++) for (let j = 0; j <= 8; j++) {
      const cx = i * s, cy = j * s;
      star8(g, cx, cy, s * .52); g.fillStyle = '#1fa9b8'; g.fill(); g.lineWidth = 6; g.strokeStyle = '#f2ead8'; g.stroke();
      star8(g, cx, cy, s * .22); g.fillStyle = '#e2b04a'; g.fill(); g.lineWidth = 3; g.strokeStyle = '#163a86'; g.stroke();
      // xochlar markazi
      const qx = cx + s / 2, qy = cy + s / 2;
      g.beginPath(); g.arc(qx, qy, s * .12, 0, 7); g.fillStyle = '#f2ead8'; g.fill();
      g.beginPath(); g.arc(qx, qy, s * .07, 0, 7); g.fillStyle = '#0d6b5a'; g.fill();
    }
    noiseFill(g, w, h, 3, .08, ['#000', '#fff']);
  });
  // naqshli tasma (minora va baraban)
  TX.band = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#c9a46a'; g.fillRect(0, 0, w, h);
    const s = 64; g.lineWidth = 14; g.strokeStyle = '#1e5fa8';
    for (let i = -8; i < 16; i++) { g.beginPath(); g.moveTo(i * s, 0); g.lineTo(i * s + h, h); g.stroke(); g.beginPath(); g.moveTo(i * s, h); g.lineTo(i * s + h, 0); g.stroke(); }
    g.lineWidth = 5; g.strokeStyle = '#2cc0c4';
    for (let i = -8; i < 16; i++) { g.beginPath(); g.moveTo(i * s, 0); g.lineTo(i * s + h, h); g.stroke(); g.beginPath(); g.moveTo(i * s, h); g.lineTo(i * s + h, 0); g.stroke(); }
    for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) { g.fillStyle = (i + j) % 2 ? '#f0e6d0' : '#e2b04a'; g.beginPath(); g.arc(i * s + s / 2, j * s, 6, 0, 7); g.fill(); }
    noiseFill(g, w, h, 5, .1, ['#000', '#fff']);
  });
  // madrasa fasadi: ikki qavatli ravoqli tokchalar
  TX.facade = canvasTex(1024, 512, (g, w, h) => {
    g.fillStyle = '#c49c62'; g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(90,60,30,.25)'; g.lineWidth = 1;
    for (let y = 0; y < h; y += 8) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); for (let x = (y / 8) % 2 * 12; x < w; x += 24) { g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 8); g.stroke(); } }
    const niche = (x, y, nw, nh) => {
      const R = nw / 2 * 1.15;
      g.beginPath(); g.moveTo(x, y + nh); g.lineTo(x, y + nh * .38);
      g.quadraticCurveTo(x, y, x + nw / 2, y); g.quadraticCurveTo(x + nw, y, x + nw, y + nh * .38); g.lineTo(x + nw, y + nh); g.closePath();
    };
    for (let row = 0; row < 2; row++) for (let i = 0; i < 8; i++) {
      const x = i * 128 + 18, y = 28 + row * 245, nw = 92, nh = 210;
      g.fillStyle = '#1e5fa8'; g.fillRect(x - 12, y - 12, nw + 24, nh + 14);
      g.strokeStyle = '#2cc0c4'; g.lineWidth = 4; g.strokeRect(x - 8, y - 8, nw + 16, nh + 8);
      niche(x, y, nw, nh); g.fillStyle = '#c49c62'; g.fill();
      niche(x + 8, y + 10, nw - 16, nh - 10); const gr = g.createLinearGradient(0, y, 0, y + nh); gr.addColorStop(0, '#1a1410'); gr.addColorStop(1, '#3a2a1c'); g.fillStyle = gr; g.fill();
      g.fillStyle = '#e2b04a'; star8(g, x + nw / 2, y + nh * .28, 9); g.fill();
    }
    g.fillStyle = '#1e5fa8'; g.fillRect(0, h - 10, w, 10); g.fillStyle = '#2cc0c4'; g.fillRect(0, h - 6, w, 3);
    noiseFill(g, w, h, 8, .12, ['#5a3a1a', '#f0dcb0']);
  });
  // feruza gumbaz
  TX.dome = canvasTex(512, 512, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#36c6cf'); gr.addColorStop(1, '#1b8fa6'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(10,60,90,.35)'; g.lineWidth = 1;
    for (let y = 0; y < h; y += 10) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    // romb naqsh (sariq va oq)
    for (let i = 0; i < 16; i++) for (let j = 0; j < 16; j++) if ((i + j) % 4 === 0) { g.fillStyle = (j % 8 < 4) ? 'rgba(240,220,170,.55)' : 'rgba(20,50,130,.5)'; g.beginPath(); const cx = i * 32 + 16, cy = j * 32 + 16; g.moveTo(cx, cy - 10); g.lineTo(cx + 7, cy); g.lineTo(cx, cy + 10); g.lineTo(cx - 7, cy); g.fill(); }
    noiseFill(g, w, h, 12, .12, ['#0a4a5a', '#bff']);
  });
  // tosh yotqizilgan maydon
  TX.paving = canvasTex(1024, 1024, (g, w, h) => {
    g.fillStyle = '#a88a62'; g.fillRect(0, 0, w, h);
    const r = rng(21);
    for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) { const v = 150 + r() * 40; g.fillStyle = `rgb(${v},${v * .82},${v * .6})`; g.fillRect(i * 128 + 3, j * 128 + 3, 122, 122); }
    noiseFill(g, w, h, 4, .15, ['#5a4228', '#e8d2a8']);
  }, { repeat: [40, 40] });
  // pishgan g‘isht (Minorai Kalon) — balandlik bo‘yicha naqshli tasmalar
  TX.kalyan = canvasTex(1024, 2048, (g, w, h) => {
    g.fillStyle = '#b98f5a'; g.fillRect(0, 0, w, h);
    const bands = [[0, .08, 'run'], [.08, .2, 'lozenge'], [.2, .22, 'run'], [.22, .36, 'zig'], [.36, .38, 'run'], [.38, .52, 'lozenge'], [.52, .54, 'run'], [.54, .66, 'grid'], [.66, .69, 'turq'], [.69, .72, 'run'], [.72, .86, 'arches'], [.86, 1, 'stal']];
    for (const [a, b, k] of bands) {
      const y0 = (1 - b) * h, y1 = (1 - a) * h;
      g.save(); g.beginPath(); g.rect(0, y0, w, y1 - y0); g.clip();
      g.fillStyle = '#c39a62'; g.fillRect(0, y0, w, y1 - y0);
      g.strokeStyle = 'rgba(80,50,25,.55)'; g.lineWidth = 3;
      if (k === 'run') { for (let y = y0; y < y1; y += 12) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); } }
      if (k === 'lozenge' || k === 'grid' || k === 'zig') {
        const s = k === 'grid' ? 32 : 48;
        for (let i = -40; i < 60; i++) {
          g.beginPath(); g.moveTo(i * s, y0); g.lineTo(i * s + (y1 - y0), y1); g.stroke();
          if (k !== 'zig') { g.beginPath(); g.moveTo(i * s, y1); g.lineTo(i * s + (y1 - y0), y0); g.stroke(); }
        }
        if (k === 'zig') for (let y = y0; y < y1; y += 24) { g.beginPath(); for (let x = 0; x <= w; x += 24) g.lineTo(x, y + ((x / 24) % 2) * 12); g.stroke(); }
      }
      if (k === 'turq') { g.fillStyle = '#2a9fb0'; g.fillRect(0, y0, w, y1 - y0); g.fillStyle = '#e6d6aa'; for (let x = 0; x < w; x += 32) { g.beginPath(); g.moveTo(x, y0 + 8); g.lineTo(x + 10, (y0 + y1) / 2); g.lineTo(x, y1 - 8); g.lineTo(x - 10, (y0 + y1) / 2); g.fill(); } }
      if (k === 'arches') { for (let i = 0; i < 16; i++) { const x = i * 64 + 12, nw = 40, top = y0 + 30; g.fillStyle = '#20140c'; g.beginPath(); g.moveTo(x, y1 - 20); g.lineTo(x, top + 30); g.quadraticCurveTo(x + nw / 2, top - 20, x + nw, top + 30); g.lineTo(x + nw, y1 - 20); g.fill(); } }
      if (k === 'stal') { for (let r = 0; r < 5; r++) for (let i = 0; i < 32; i++) { g.fillStyle = r % 2 ? '#a07848' : '#d0a872'; const x = i * 32 + (r % 2) * 16, y = y0 + r * (y1 - y0) / 5; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 16, y + (y1 - y0) / 5); g.lineTo(x + 32, y); g.fill(); } }
      g.restore();
      g.fillStyle = 'rgba(60,40,20,.5)'; g.fillRect(0, y0, w, 4);
    }
    noiseFill(g, w, h, 30, .12, ['#5a3a1a', '#f0dcb0']);
  }, { repeat: [2, 1] });
  // Kordova: qizil-oq ark toshlari (voussoir)
  TX.vous = canvasTex(512, 640, (g, w, h) => {
    g.fillStyle = '#e8dcc0'; g.fillRect(0, 0, w, h);
    noiseFill(g, w, h, 6, .15, ['#c0aa80', '#fff8e8']);
    const sx = w, sy = h / 1.25;
    const ring = (cx, cy, r0, r1, n, a0, a1) => {
      const P = (r, a) => [cx * sx + r * sx * Math.cos(a), h - (cy * sy + r * sy * Math.sin(a))];
      for (let i = 0; i < n; i++) {
        const a = a0 + (a1 - a0) * i / n, b = a0 + (a1 - a0) * (i + 1) / n;
        g.beginPath(); for (let k = 0; k <= 6; k++) { const q = P(r1, a + (b - a) * k / 6); k ? g.lineTo(...q) : g.moveTo(...q); }
        for (let k = 6; k >= 0; k--) g.lineTo(...P(r0, a + (b - a) * k / 6)); g.closePath();
        g.fillStyle = i % 2 ? '#a5341f' : '#ecdfc0'; g.fill(); g.strokeStyle = 'rgba(80,40,20,.35)'; g.lineWidth = 1; g.stroke();
      }
    };
    ring(.5, .3, .42, .52, 19, -0.26, Math.PI + 0.26);
    ring(.5, .8, .38, .47, 13, 0, Math.PI);
  });
  TX.wood = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#3a2414'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { g.fillStyle = '#24160c'; g.fillRect(i * 128 + 14, j * 128 + 14, 100, 100); g.fillStyle = '#7a5a2a'; star8(g, i * 128 + 64, j * 128 + 64, 26); g.fill(); }
  }, { repeat: [12, 12] });
  return TX;
}

// ------------------------------------------------------------ osmon
const skyVS = `varying vec3 vDir; void main(){ vDir = normalize((modelMatrix*vec4(position,1.)).xyz - cameraPosition); gl_Position = projectionMatrix*viewMatrix*modelMatrix*vec4(position,1.); gl_Position.z = gl_Position.w; }`;
const skyFS = `
uniform vec3 top, mid, hor, sunDir, sunCol; uniform float clouds, stars, time;
varying vec3 vDir;
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float n(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f); return mix(mix(h(i),h(i+vec2(1,0)),f.x), mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x), f.y); }
float fbm(vec2 p){ float s=0., a=.5; for(int i=0;i<5;i++){ s+=a*n(p); p*=2.03; a*=.5; } return s; }
void main(){
  vec3 d = normalize(vDir); float y = d.y;
  vec3 c = mix(hor, mid, smoothstep(0., .18, y)); c = mix(c, top, smoothstep(.15, .7, y));
  if (y < 0.) c = mix(hor*.8, hor*.35, smoothstep(0., -.2, y));
  float sd = max(dot(d, normalize(sunDir)), 0.);
  c += sunCol * (pow(sd, 900.)*6. + pow(sd, 60.)*.8 + pow(sd, 6.)*.25 * (1.-smoothstep(0.,.5,y)));
  if (clouds > 0. && y > 0.) {
    vec2 uv = d.xz / (y + .12) * 1.4 + vec2(time*.02, 0.);
    float cl = smoothstep(.48, .78, fbm(uv*1.3)) * clouds * smoothstep(0., .08, y) * (1.-smoothstep(.45,.9,y));
    vec3 cc = mix(vec3(.25,.18,.3), sunCol*1.3 + vec3(.25,.12,.05), pow(sd, 3.)*.9 + .25);
    c = mix(c, cc, cl);
  }
  if (stars > 0. && y > 0.05) { vec2 g = d.xz/(y+.3)*260.; float s = step(.996, h(floor(g))); c += vec3(s)*stars*smoothstep(.05,.4,y)*(.5+.5*h(floor(g)+3.)); }
  gl_FragColor = vec4(c, 1.);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function sky(o) {
  const u = {
    top: { value: new THREE.Color(o.top) }, mid: { value: new THREE.Color(o.mid) }, hor: { value: new THREE.Color(o.hor) },
    sunDir: { value: o.sunDir.clone().normalize() }, sunCol: { value: new THREE.Color(o.sunCol) }, clouds: { value: o.clouds ?? .6 }, stars: { value: o.stars ?? 0 }, time: { value: 0 },
  };
  const m = new THREE.Mesh(new THREE.SphereGeometry(4000, 48, 24), new THREE.ShaderMaterial({ uniforms: u, vertexShader: skyVS, fragmentShader: skyFS, side: THREE.BackSide, depthWrite: false }));
  m.frustumCulled = false; m.userData.u = u; return m;
}
function envFrom(skyMesh) {
  const pm = new THREE.PMREMGenerator(R); const sc = new THREE.Scene(); sc.add(skyMesh.clone());
  const rt = pm.fromScene(sc, 0, .1, 5000); pm.dispose(); return rt.texture;
}

// ------------------------------------------------------------ geometriya
function pointedArchPts(cx, w, spring, rise, n = 20) {
  const half = w / 2, Rr = (half * half + rise * rise) / (2 * half), a1 = Math.acos((Rr - half) / Rr), pts = [];
  for (let i = 0; i <= n; i++) { const a = a1 * i / n; pts.push(new THREE.Vector2(cx - half + Rr - Rr * Math.cos(a), spring + Rr * Math.sin(a))); }
  const right = pts.slice(0, -1).reverse().map(p => new THREE.Vector2(2 * cx - p.x, p.y));
  return pts.concat(right);
}
function uvScale(geo, sx, sy) { const uv = geo.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * sx, uv.getY(i) * sy); uv.needsUpdate = true; return geo; }
function mat(o) { return new THREE.MeshStandardMaterial(o); }
function ribbedDome(r, ribs = 32, h = 1.35) {
  const pts = [];
  for (let i = 0; i <= 40; i++) { const u = i / 40; const y = u * r * h; const bul = Math.sin(Math.min(1, u * 1.35) * Math.PI * .5 + .3); let rad = r * (u < .74 ? (1 + .14 * Math.sin(u / .74 * Math.PI)) * (1 - u * .25) : (1 - u) / .26 * .8); pts.push(new THREE.Vector2(Math.max(.001, rad), y)); }
  const g = new THREE.LatheGeometry(pts, 128);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), a = Math.atan2(z, x); const k = .93 + .07 * Math.pow(Math.abs(Math.cos(a * ribs / 2)), .45); p.setX(i, x * k); p.setZ(i, z * k); }
  g.computeVertexNormals(); return g;
}
function smoothDome(r, h = 1.0) { const g = new THREE.SphereGeometry(r, 64, 24, 0, Math.PI * 2, 0, Math.PI / 2); g.scale(1, h, 1); return g; }
function domeOnDrum(T, env, { r = 7, drumH = 8, ribbed = true, ribs = 36 }) {
  const gr = new THREE.Group();
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(r * .98, r * .98, drumH, 64, 1, true), mat({ map: T.bandDrum, roughness: .6 }));
  drum.position.y = drumH / 2; gr.add(drum);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(r * 1.03, r * 1.03, .6, 64), mat({ color: '#d8c49a', roughness: .7 })); cap.position.y = drumH; gr.add(cap);
  const dm = new THREE.Mesh(ribbed ? ribbedDome(r, ribs) : smoothDome(r * 1.02, 1.15), mat({ map: T.dome, color: '#ffffff', roughness: .22, metalness: .05, envMap: env, envMapIntensity: 1.1 }));
  dm.position.y = drumH + .3; gr.add(dm);
  const fin = new THREE.Mesh(new THREE.CylinderGeometry(.08, .2, r * .5, 8), mat({ color: '#d6a640', metalness: 1, roughness: .25, envMap: env }));
  fin.position.y = drumH + .3 + r * (ribbed ? 1.35 : 1.17) + r * .2; gr.add(fin);
  gr.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return gr;
}
function minaret(T, env, { h = 33, r = 2.2, top = 'flat', taper = .78 }) {
  const gr = new THREE.Group();
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(r * taper, r, h, 48, 1, true), mat({ map: T.bandMin, roughness: .7 }));
  shaft.position.y = h / 2; gr.add(shaft);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(r * 1.12, r * 1.15, 3, 32), mat({ color: '#b08a56', roughness: .8 })); base.position.y = 1.5; gr.add(base);
  const balc = new THREE.Mesh(new THREE.CylinderGeometry(r * taper * 1.35, r * taper * 1.05, 1.4, 48), mat({ map: T.mosaicSmall, roughness: .5 })); balc.position.y = h - .5; gr.add(balc);
  if (top === 'cupola') {
    const lant = new THREE.Mesh(new THREE.CylinderGeometry(r * taper * .9, r * taper * .9, 2.4, 32), mat({ color: '#c9a46a', roughness: .7 })); lant.position.y = h + 1.2; gr.add(lant);
    const cp = new THREE.Mesh(smoothDome(r * taper * .95, 1.2), mat({ map: T.dome, roughness: .25, envMap: env })); cp.position.y = h + 2.4; gr.add(cp);
  }
  gr.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return gr;
}
// Peshtoq: o‘tkir arkli katta portal
function pishtaq(T, env, { w = 22, h = 33, d = 3, aw = .56, ah = .72 }) {
  const gr = new THREE.Group();
  const shape = new THREE.Shape(); shape.moveTo(-w / 2, 0); shape.lineTo(w / 2, 0); shape.lineTo(w / 2, h); shape.lineTo(-w / 2, h); shape.closePath();
  const ow = w * aw, oh = h * ah, rise = ow * .62;
  const hole = new THREE.Path(); const ap = pointedArchPts(0, ow, oh - rise, rise);
  hole.moveTo(-ow / 2, 0.01); ap.forEach(p => hole.lineTo(p.x, p.y)); hole.lineTo(ow / 2, .01); hole.closePath();
  // teshik pastki chetga tegmasligi uchun shakl konturini qayta quramiz
  const s2 = new THREE.Shape(); s2.moveTo(-w / 2, 0); s2.lineTo(-ow / 2, 0); ap.forEach(p => s2.lineTo(p.x, p.y)); s2.lineTo(ow / 2, 0); s2.lineTo(w / 2, 0); s2.lineTo(w / 2, h); s2.lineTo(-w / 2, h); s2.closePath();
  const g = new THREE.ExtrudeGeometry(s2, { depth: d, bevelEnabled: false, curveSegments: 6 });
  uvScale(g, 1 / 11, 1 / 11);
  const front = new THREE.Mesh(g, [mat({ map: T.mosaic, roughness: .45, envMap: env, envMapIntensity: .6 }), mat({ color: '#b99260', roughness: .8 })]);
  gr.add(front);
  // ramka (oltin-oq tasma)
  const fr = new THREE.Mesh(new THREE.BoxGeometry(w + .6, .9, d + .4), mat({ map: T.bandDrum, roughness: .5 })); fr.position.set(0, h - .45, d / 2); gr.add(fr);
  for (const sx of [-1, 1]) { const col = new THREE.Mesh(new THREE.CylinderGeometry(.5, .5, h * .97, 16), mat({ map: T.bandMin, roughness: .5 })); col.position.set(sx * (w / 2 + .1), h * .485, d + .1); gr.add(col); }
  const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(-ow / 2, 0, d + .05), ...ap.map(p => new THREE.Vector3(p.x, p.y, d + .05)), new THREE.Vector3(ow / 2, 0, d + .05)]);
  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 80, .45, 10, false), mat({ map: T.bandMin, roughness: .45 })); gr.add(tube);
  const fr2 = new THREE.Shape(); fr2.moveTo(-ow / 2 - 2.2, 0); fr2.lineTo(-ow / 2 - 2.2, oh + 1.6); fr2.lineTo(ow / 2 + 2.2, oh + 1.6); fr2.lineTo(ow / 2 + 2.2, 0); fr2.lineTo(ow / 2 + 1.4, 0); fr2.lineTo(ow / 2 + 1.4, oh + .8); fr2.lineTo(-ow / 2 - 1.4, oh + .8); fr2.lineTo(-ow / 2 - 1.4, 0); fr2.closePath();
  const frm = new THREE.Mesh(new THREE.ExtrudeGeometry(fr2, { depth: .3, bevelEnabled: false }), mat({ map: T.bandDrum, roughness: .5 })); frm.position.z = d; gr.add(frm);
  // ravoq ichi (iwan): orqa devor + yarim gumbaz
  const back = new THREE.Mesh(new THREE.PlaneGeometry(ow, oh), mat({ map: T.facadeIwan, roughness: .8 })); back.position.set(0, oh / 2, -ow * .45); gr.add(back);
  for (const sx of [-1, 1]) { const sw = new THREE.Mesh(new THREE.PlaneGeometry(ow * .45 + d, oh - rise), mat({ map: T.facadeIwan, roughness: .8, side: THREE.DoubleSide })); sw.rotation.y = Math.PI / 2; sw.position.set(sx * ow / 2, (oh - rise) / 2, (d - ow * .45) / 2); gr.add(sw); }
  const sd = new THREE.Mesh(new THREE.SphereGeometry(ow / 2, 32, 16, Math.PI, Math.PI, 0, Math.PI / 2), mat({ map: T.mosaic, roughness: .5, side: THREE.DoubleSide, color: '#c8d8ff' }));
  sd.scale.set(1, rise / (ow / 2) * 1.05, .9); sd.rotation.y = 0; sd.position.set(0, oh - rise, -ow * .45 + .01); gr.add(sd);
  const vault = new THREE.Mesh(new THREE.CylinderGeometry(ow / 2, ow / 2, ow * .45 + d, 32, 1, true, -Math.PI / 2, Math.PI), mat({ map: T.mosaic, roughness: .5, side: THREE.BackSide, color: '#c8d8ff' }));
  vault.rotation.x = Math.PI / 2; vault.scale.set(1, 1, rise / (ow / 2)); vault.position.set(0, oh - rise, (d - ow * .45) / 2); gr.add(vault);
  gr.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return gr;
}
function madrasa(T, env, o) {
  const { w = 64, h = 18, pw = 24, ph = 34, minarets = true, minH = 34, domes = [], guldasta = false } = o;
  const gr = new THREE.Group();
  const ow = pw * .56, wing = (w - ow) / 2;
  const fm = () => [mat({ color: '#b48e58', roughness: .9 }), mat({ color: '#b48e58', roughness: .9 }), mat({ color: '#a8875a', roughness: .9 }), mat({ color: '#b48e58' }), mat({ map: T.facadeWide, roughness: .75 }), mat({ color: '#a8875a', roughness: .9 })];
  for (const sx of [-1, 1]) { const b = new THREE.Mesh(new THREE.BoxGeometry(wing, h, 34), fm()); b.position.set(sx * (ow / 2 + wing / 2), h / 2, -17); gr.add(b); }
  const bd = 34 - ow * .45 - 1; const bb = new THREE.Mesh(new THREE.BoxGeometry(ow, h, bd), fm()); bb.position.set(0, h / 2, -34 + bd / 2); gr.add(bb);
  const top = new THREE.Mesh(new THREE.BoxGeometry(w + .5, .8, 34.5), mat({ map: T.bandDrum, roughness: .6 })); top.position.set(0, h, -17); gr.add(top);
  const p = pishtaq(T, env, { w: pw, h: ph, d: 3 }); p.position.set(0, 0, -1.5); gr.add(p);
  if (minarets) for (const sx of [-1, 1]) { const m = minaret(T, env, { h: minH, r: 2.4, top: 'flat' }); m.position.set(sx * w / 2, 0, -.5); gr.add(m); }
  if (guldasta) for (const sx of [-1, 1]) { const m = minaret(T, env, { h: h + 6, r: 1.6, top: 'cupola', taper: .9 }); m.position.set(sx * w / 2, 0, -.5); gr.add(m); }
  for (const dd of domes) { const dm = domeOnDrum(T, env, dd); dm.position.set(dd.x, h - 1, dd.z ?? -10); gr.add(dm); }
  gr.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return gr;
}

// ------------------------------------------------------------ sahnalar
function buildCordoba(T) {
  const sc = new THREE.Scene();
  sc.background = new THREE.Color('#0d0804'); sc.fog = new THREE.FogExp2('#1c1008', .045);
  sc.add(new THREE.HemisphereLight('#ffd7a0', '#2a1608', .5));
  const env = envFrom(sky({ top: '#3a2a20', mid: '#8a5a30', hor: '#d09050', sunDir: new THREE.Vector3(0, 1, 0), sunCol: '#ffb060', clouds: 0 }));
  const shape = new THREE.Shape();
  const Ht = 1.25;
  shape.moveTo(0, 0); shape.lineTo(.1, 0); shape.lineTo(.094, .19);
  shape.absarc(.5, .3, .42, Math.PI + .26, -.26, true);
  shape.lineTo(.9, 0); shape.lineTo(1, 0); shape.lineTo(1, Ht); shape.lineTo(0, Ht); shape.closePath();
  const hole = new THREE.Path(); hole.moveTo(.13, .8); hole.absarc(.5, .8, .37, Math.PI, 0, true); hole.lineTo(.87, .62); hole.lineTo(.13, .62); hole.closePath();
  shape.holes.push(hole);
  const g = new THREE.ExtrudeGeometry(shape, { depth: .14, bevelEnabled: false, curveSegments: 24 });
  uvScale(g, 1, 1 / Ht);
  const panelMat = [mat({ map: T.vous, roughness: .7 }), mat({ color: '#d8c8a8', roughness: .8 })];
  const colMats = ['#8a8a86', '#a07a6a', '#5a6a60', '#9a948a', '#6a5a5a'].map(c => mat({ color: c, roughness: .35, metalness: .05, envMap: env, envMapIntensity: .5 }));
  const colG = new THREE.CylinderGeometry(.16, .18, 3.0, 20), capG = new THREE.BoxGeometry(.5, .25, .5), r = rng(77);
  const BAY = 3;
  for (let ax = -4; ax <= 4; ax++) {
    const x = ax * BAY + BAY / 2;
    for (let bz = -2; bz < 16; bz++) {
      const z = bz * BAY;
      const c = new THREE.Mesh(colG, colMats[Math.floor(r() * colMats.length)]); c.position.set(x, 1.5, z); sc.add(c);
      const cp = new THREE.Mesh(capG, mat({ color: '#c8a870', roughness: .6 })); cp.position.set(x, 3.12, z); sc.add(cp);
      const p = new THREE.Mesh(g, panelMat); p.scale.set(BAY, BAY, BAY); p.rotation.y = -Math.PI / 2; p.position.set(x - .21, 3.25, z); sc.add(p);
    }
  }
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(80, 120), mat({ color: '#6a5038', roughness: .28, metalness: .0, envMap: env, envMapIntensity: .8 }));
  floor.rotation.x = -Math.PI / 2; floor.position.z = 20; sc.add(floor);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(80, 120), mat({ map: T.wood, roughness: .8 }));
  ceil.rotation.x = Math.PI / 2; ceil.position.set(0, 3.25 + 1.25 * BAY, 20); sc.add(ceil);
  // iliq chiroqlar
  for (let k = 0; k < 7; k++) { const L = new THREE.PointLight('#ffb460', 5, 14, 1.6); L.position.set(k % 2 ? -1.5 : 1.5, 5.4, k * 6 + 2); sc.add(L); }
  const key = new THREE.PointLight('#ffd090', 30, 40, 1.4); key.position.set(0, 6, 30); sc.add(key);
  const cam = new THREE.PerspectiveCamera(48, W / H, .1, 400);
  return {
    sc, cam, update(t) {
      const u = ease.inOut(clamp(t / 3.5));
      cam.position.set(lerp(-.4, .3, u), lerp(1.5, 2.3, u), lerp(-1, 11, u));
      cam.lookAt(lerp(.8, -.4, u), lerp(2.6, 3.9, u), cam.position.z + 10);
    },
  };
}
function buildKalyan(T) {
  const sc = new THREE.Scene();
  const sk = sky({ top: '#0a1430', mid: '#2a3a70', hor: '#e08a5a', sunDir: new THREE.Vector3(-1, .02, -.6), sunCol: '#ff9a50', clouds: .45, stars: .9 });
  sc.add(sk); const env = envFrom(sk);
  sc.fog = new THREE.Fog('#5a4a6a', 120, 700);
  sc.add(new THREE.HemisphereLight('#7a8ac8', '#4a3020', .55));
  const sun = new THREE.DirectionalLight('#ff9a5a', 1.6); sun.position.set(-200, 25, -120); sc.add(sun);
  // minora: balandligi 45.6 m, asosi ~9 m, tepasi ~6 m
  const Hm = 45.6, rb = 4.55, rt = 3.0;
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, Hm * .86, 96, 1, true), mat({ map: T.kalyan, bumpMap: T.kalyan, bumpScale: 2.5, roughness: .85 }));
  shaft.position.y = Hm * .43; sc.add(shaft);
  // fonar (rotunda) va karniz
  const lan = new THREE.Mesh(new THREE.CylinderGeometry(rt * 1.08, rt * 1.0, Hm * .14, 96, 1, true), mat({ map: T.kalyanTop, roughness: .85 })); lan.position.y = Hm * .93; sc.add(lan);
  for (let k = 0; k < 4; k++) { const ring = new THREE.Mesh(new THREE.CylinderGeometry(rt * (1.02 + k * .05), rt * (1.0 + k * .05), .5, 64), mat({ color: k % 2 ? '#a07848' : '#cfa876', roughness: .8 })); ring.position.y = Hm * .86 + k * .5; sc.add(ring); }
  const capm = new THREE.Mesh(new THREE.CylinderGeometry(rt * 1.1, rt * 1.12, .8, 64), mat({ color: '#c09a68' })); capm.position.y = Hm; sc.add(capm);
  const tc = new THREE.Mesh(smoothDome(rt * .9, .5), mat({ color: '#b08a58', roughness: .8 })); tc.position.y = Hm + .4; sc.add(tc);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(rb * 1.15, rb * 1.2, 1.2, 64), mat({ color: '#9a7a52' })); base.position.y = .6; sc.add(base);
  // yuqoriga yorituvchi chiroqlar
  for (const a of [0, 2.1, 4.2]) { const sp = new THREE.SpotLight('#ffc080', 320, 80, .35, .7, 1.6); sp.position.set(Math.cos(a) * 14, .5, Math.sin(a) * 14); sp.target.position.set(0, 30, 0); sc.add(sp, sp.target); }
  // fon: Kalon masjidi va Mir-i Arab gumbazlari
  const d1 = domeOnDrum(T, env, { r: 9, drumH: 10, ribbed: false }); d1.position.set(-60, 14, -70); sc.add(d1);
  for (const [x, z] of [[70, -40], [90, -55]]) { const d = domeOnDrum(T, env, { r: 7, drumH: 8, ribbed: false }); d.position.set(x, 12, z); sc.add(d); }
  const blk = new THREE.Mesh(new THREE.BoxGeometry(70, 14, 50), mat({ map: T.facadeWide, color: '#b8a080', roughness: .9 })); blk.position.set(-60, 7, -70); sc.add(blk);
  const blk2 = new THREE.Mesh(new THREE.BoxGeometry(60, 12, 40), mat({ map: T.facadeWide, color: '#b8a080', roughness: .9 })); blk2.position.set(80, 6, -45); sc.add(blk2);
  const p1 = pishtaq(T, env, { w: 18, h: 26, d: 3 }); p1.position.set(-60, 0, -44); sc.add(p1);
  const gnd = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), mat({ map: T.paving, roughness: .9, color: '#a08870' })); gnd.rotation.x = -Math.PI / 2; sc.add(gnd);
  const cam = new THREE.PerspectiveCamera(50, W / H, .5, 6000);
  return {
    sc, cam, update(t) {
      const u = ease.inOut(clamp(t / 3.4)), a = lerp(.9, 1.9, u), rr = lerp(30, 22, u);
      cam.position.set(Math.cos(a) * rr, lerp(3, 36, u), Math.sin(a) * rr);
      cam.lookAt(0, lerp(26, 44, u), 0); sk.userData.u.time.value = t;
    },
  };
}
function buildTimurid(T, { sunset = false } = {}) {
  const sc = new THREE.Scene();
  const sunDir = sunset ? new THREE.Vector3(-1, .1, .35) : new THREE.Vector3(-.6, .55, .7);
  const sk = sky(sunset
    ? { top: '#1a2450', mid: '#7a5a78', hor: '#ffb25a', sunDir, sunCol: '#ff9840', clouds: .85 }
    : { top: '#1d4f9a', mid: '#5f97d0', hor: '#f2d2a0', sunDir, sunCol: '#ffd090', clouds: .45 });
  sc.add(sk); const env = envFrom(sk); sc.environment = null;
  sc.fog = new THREE.Fog(sunset ? '#c08a68' : '#c8c0b0', 200, 1400);
  sc.add(new THREE.HemisphereLight(sunset ? '#9a98d0' : '#a8c8ff', sunset ? '#7a4a2a' : '#a08060', sunset ? .95 : .7));
  const sun = new THREE.DirectionalLight(sunset ? '#ffa050' : '#ffe0b0', sunset ? 3.2 : 3.0);
  sun.position.copy(sunDir).multiplyScalar(300); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); const sc_ = sun.shadow.camera; sc_.left = -140; sc_.right = 140; sc_.top = 140; sc_.bottom = -140; sc_.near = 10; sc_.far = 900; sun.shadow.bias = -.0005; sun.shadow.normalBias = .4;
  sc.add(sun);
  const gnd = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000), mat({ map: T.paving, roughness: .85 })); gnd.rotation.x = -Math.PI / 2; gnd.receiveShadow = true; sc.add(gnd);
  // Registon tartibi: g‘arbda (Ulug‘bek), sharqda (Sherdor), shimolda (Tillakori)
  const ub = madrasa(T, env, { w: 62, h: 18, pw: 24, ph: 34, minarets: true, minH: 33 }); ub.position.set(-48, 0, 0); ub.rotation.y = Math.PI / 2; sc.add(ub);
  const sd = madrasa(T, env, { w: 62, h: 18, pw: 24, ph: 34, minarets: true, minH: 31, domes: [{ x: -21, z: -9, r: 6.2, drumH: 7, ribbed: true, ribs: 30 }, { x: 21, z: -9, r: 6.2, drumH: 7, ribbed: true, ribs: 30 }] });
  sd.position.set(48, 0, 0); sd.rotation.y = -Math.PI / 2; sc.add(sd);
  const tk = madrasa(T, env, { w: 74, h: 16, pw: 22, ph: 30, minarets: false, guldasta: true, domes: [{ x: -24, z: -14, r: 8.5, drumH: 9, ribbed: false }] });
  tk.position.set(0, 0, -50); sc.add(tk);
  const cam = new THREE.PerspectiveCamera(sunset ? 42 : 46, W / H, .5, 8000);
  return { sc, cam, sk, sun };
}

let S4 = {}, S6;
export async function initGL(canvas, S) {
  SC = S; glCanvas = canvas;
  R = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  R.setPixelRatio(1); R.setSize(W * S, H * S, false);
  R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.0; R.outputColorSpace = THREE.SRGBColorSpace;
  R.shadowMap.enabled = true; R.shadowMap.type = THREE.PCFSoftShadowMap;
  const T = textures();
  T.bandDrum = T.band.clone(); T.bandDrum.repeat.set(12, .5); T.bandDrum.needsUpdate = true;
  T.bandMin = T.band.clone(); T.bandMin.repeat.set(4, 12); T.bandMin.needsUpdate = true;
  T.mosaicSmall = T.mosaic.clone(); T.mosaicSmall.repeat.set(4, .4); T.mosaicSmall.needsUpdate = true;
  T.facadeWide = T.facade.clone(); T.facadeWide.repeat.set(5, 1.4); T.facadeWide.needsUpdate = true;
  T.facadeIwan = T.facade.clone(); T.facadeIwan.repeat.set(1.2, 1.6); T.facadeIwan.needsUpdate = true;
  T.kalyanTop = T.kalyan.clone(); T.kalyanTop.repeat.set(2, .14); T.kalyanTop.offset.set(0, .72); T.kalyanTop.needsUpdate = true;
  S4.cordoba = buildCordoba(T);
  S4.kalyan = buildKalyan(T);
  S4.tim = buildTimurid(T, { sunset: false });
  S6 = buildTimurid(T, { sunset: true });
}

function blit(ctx) { ctx.drawImage(glCanvas, 0, 0, W, H); }
function lowerThird(ctx, t, a, b, title, sub, S) {
  const p = inv(a, a + .7, t), q = smooth(b - .4, b, t); if (p <= 0 || q >= 1) return;
  ctx.save(); ctx.globalAlpha = 1 - q;
  const lw = 520 * ease.out(p);
  ctx.strokeStyle = C.gold2; ctx.lineWidth = 2; ctx.shadowColor = 'rgba(255,200,110,.8)'; ctx.shadowBlur = 8;
  ctx.beginPath(); ctx.moveTo(110, H - 168); ctx.lineTo(110 + lw, H - 168); ctx.stroke(); ctx.restore();
  ctx.save(); ctx.globalAlpha = 1 - q;
  const g = ctx.createLinearGradient(0, H - 330, 0, H); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,4,14,.55)'); ctx.fillStyle = g; ctx.fillRect(0, H - 330, W * .6, 330);
  ctx.restore();
  revealText(ctx, title, 110, H - 190, p, { size: 44, font: FONT.title, weight: 700, color: C.gold2, align: 'left', track: 3, alpha: 1 - q, S, glowA: .4 });
  revealText(ctx, sub, 110, H - 124, clamp(p - .15), { size: 30, font: FONT.body, weight: 600, italic: true, color: '#eef6f3', align: 'left', alpha: 1 - q, S });
}

export function scene4(ctx, t, env) {
  const S = env.S;
  let shot, lt;
  if (t < 3.4) { shot = S4.cordoba; lt = t; }
  else if (t < 6.7) { shot = S4.kalyan; lt = t - 3.4; }
  else { shot = S4.tim; lt = t - 6.7; }
  if (shot === S4.tim) {
    const u = ease.inOut(clamp(lt / 3.3)), cam = shot.cam;
    cam.position.set(lerp(-34, -6, u), lerp(3, 19, u), lerp(14, -16, u));
    cam.lookAt(lerp(6, 24, u), lerp(15, 21, u), lerp(-44, -50, u));
    shot.sk.userData.u.time.value = t;
  } else shot.update(lt);
  R.render(shot.sc, shot.cam);
  blit(ctx);
  // nur hüzmesi va chang
  if (shot === S4.cordoba) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let k = 0; k < 3; k++) { const x = 600 + k * 420 - lt * 30; const g = ctx.createLinearGradient(x, 0, x + 260, H); g.addColorStop(0, 'rgba(255,200,120,.16)'); g.addColorStop(1, 'rgba(255,180,90,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 90, 0); ctx.lineTo(x + 420, H); ctx.lineTo(x + 200, H); ctx.closePath(); ctx.fill(); }
    ctx.restore();
    dust(ctx, t, { n: 220, alpha: .7, vx: .002, vy: -.004, size: .9 });
  } else dust(ctx, t, { n: 120, alpha: .4, vx: .004, vy: -.003 });
  lowerThird(ctx, t, .5, 3.35, 'KORDOVA JOME MASJIDI', 'Andalus · 785-yildan qurila boshlagan', S);
  lowerThird(ctx, t, 3.8, 6.65, 'MINORAI KALON', 'Buxoro · 1127-yil · balandligi 45,6 m', S);
  lowerThird(ctx, t, 7.1, 9.6, 'SAMARQAND', 'Temuriylar me’morchiligi · XV asr', S);
  // o‘tishlar
  starWipe(ctx, 1 - inv(0, .55, t));
  for (const c of [3.4, 6.7]) { const d = Math.abs(t - c); flash(ctx, .85 * Math.exp(-Math.pow(d / .12, 2))); }
  flash(ctx, ease.in(inv(9.55, 10, t)) * .8);
  return { bloom: .45, vignette: .7, grain: .05 };
}

export function scene6(ctx, t, env) {
  const S = env.S;
  const cam = S6.cam;
  // kamera: maydon ichidan orqaga va yuqoriga
  const u = ease.inOut(clamp(t / 8.0));
  cam.position.set(lerp(4, 0, u), lerp(4, 26, u), lerp(8, 175, u));
  cam.lookAt(lerp(6, 0, u), lerp(17, 34, u), lerp(-50, -40, u));
  S6.sk.userData.u.time.value = t;
  R.toneMappingExposure = 1.15;
  R.render(S6.sc, cam);
  R.toneMappingExposure = 1.0;
  blit(ctx);
  dust(ctx, t, { n: 220, alpha: .6, vx: .004, vy: -.004 });
  lensFlare(ctx, lerp(-200, 150, u), lerp(560, 760, u), .4);
  // boshlanish: oltin yorug‘likdan
  flash(ctx, 1.0 * (1 - smooth(0, .8, t)));
  // yakuniy naqsh va sarlavha
  const pa = inv(4.0, 6.0, t);
  if (pa > 0) {
    const dg = ctx.createRadialGradient(W / 2, H * .36, 50, W / 2, H * .36, 950);
    dg.addColorStop(0, `rgba(3,8,22,${.72 * smooth(4, 5.5, t)})`); dg.addColorStop(1, 'rgba(3,8,22,0)'); ctx.fillStyle = dg; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.translate(W / 2, H * .36); ctx.rotate(-t * .02);
    const L = [...rosette(16, 330)]; for (const rr of [345, 362]) for (let i = 0; i < 96; i++) { const a = i / 96 * 6.283, b = (i + 1) / 96 * 6.283; L.push([[rr * Math.cos(a), rr * Math.sin(a)], [rr * Math.cos(b), rr * Math.sin(b)]]); }
    ctx.globalAlpha = .75 * (1 - smooth(9.0, 9.8, t));
    drawLines(ctx, L, ease.out(pa), { width: 1.6, glowA: .8, spread: 1.2 });
    ctx.restore();
  }
  const fa = 1 - smooth(9.2, 9.85, t);
  if (t > 5.0) {
    title3D(ctx, 'ISLOM SIVILIZATSIYASI', W / 2, H * .36 + 40, 108, inv(5.0, 6.4, t), { S, depth: 14, sweep: inv(6.3, 7.5, t), alpha: fa, track: .05 });
    const lp = ease.inOut(inv(6.6, 7.4, t));
    if (lp > 0) {
      ctx.save(); ctx.globalAlpha = fa; ctx.strokeStyle = C.gold2; ctx.lineWidth = 1.5; ctx.shadowColor = 'rgba(255,200,110,.8)'; ctx.shadowBlur = 8;
      const y = H * .36 + 92, hw = 420 * lp;
      ctx.beginPath(); ctx.moveTo(W / 2 - 40 - hw, y); ctx.lineTo(W / 2 - 40, y); ctx.moveTo(W / 2 + 40, y); ctx.lineTo(W / 2 + 40 + hw, y); ctx.stroke();
      ctx.translate(W / 2, y); ctx.rotate(Math.PI / 4); ctx.strokeRect(-9, -9, 18, 18); ctx.fillStyle = C.gold2; ctx.fillRect(-4, -4, 8, 8); ctx.restore();
    }
    revealText(ctx, 'BUYUK TARIX  •  BUYUK MEROS', W / 2, H * .36 + 160, inv(7.2, 8.1, t), { size: 46, font: FONT.title, weight: 700, color: '#fff1cc', track: 10, alpha: fa, S, glowA: .7 });
    revealText(ctx, 'الحضارة الإسلامية', W / 2, H * .36 - 92, inv(5.6, 6.6, t), { size: 62, font: FONT.ar, weight: 700, color: C.gold2, alpha: fa, S, dir: 'rtl', glowA: .5 });
  }
  // oltin nur bilan yakun
  const end = inv(8.9, 9.6, t);
  flash(ctx, Math.sin(clamp(end) * Math.PI) * .9 + ease.in(inv(9.3, 9.6, t)) * .3);
  return { bloom: .55, vignette: .75, goldFade: Math.sin(clamp(end) * Math.PI) * .35, fade: ease.inOut(inv(9.35, 10, t)) };
}
