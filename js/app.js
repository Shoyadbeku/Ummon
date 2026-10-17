import { CAPTION_STYLES, VIDEO_TEMPLATES, BACKGROUNDS, DEMO_SEGMENTS, styleById } from './templates.js';
import { drawFrame, canvasSize, findSegment } from './render.js';
import { toLatin, toCyrillic, hasCyrillic, normalizeApostrophes } from './translit.js';

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

/* ================= holat ================= */
const DEFAULTS = {
  aspect: '9:16', fit: 'cover', bgMode: 'blur', bgColor: '#14121c', bgIndex: 2,
  styleId: 'karaoke', fontScale: 1, pos: null, maxWords: '', colorMain: null, colorActive: null,
  hook: '', hookStyle: 'pill', script: 'latin',
};
const state = { ...DEFAULTS, segments: DEMO_SEGMENTS.map((s) => ({ ...s })), demoSegs: true };

try {
  const saved = JSON.parse(localStorage.getItem('ummon-project') || 'null');
  if (saved) Object.assign(state, saved);
} catch { /* saqlash mavjud emas */ }

let saveTimer = 0;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    try {
      const { segments, ...rest } = state;
      localStorage.setItem('ummon-project', JSON.stringify({ ...rest, segments: segments.map(({ start, end, text }) => ({ start, end, text })) }));
    } catch { /* e‘tiborsiz */ }
  }, 300);
}

/* ================= yordamchilar ================= */
function toast(msg, ms = 2600) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove('show'), ms);
}
function fmt(t, withMs = true) {
  if (!isFinite(t)) t = 0;
  const m = Math.floor(t / 60);
  const s = t - m * 60;
  return withMs ? `${m}:${s.toFixed(1).padStart(4, '0')}` : `${m}:${String(Math.floor(s)).padStart(2, '0')}`;
}
function parseTime(str) {
  str = String(str).trim().replace(',', '.');
  const parts = str.split(':').map(Number);
  if (parts.some(isNaN)) return null;
  return parts.reduce((acc, p) => acc * 60 + p, 0);
}
function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
function currentStyle() { return styleById(state.styleId); }
function renderOpts(extra = {}) {
  return {
    aspect: state.aspect, fit: state.fit, bgMode: state.bgMode, bgColor: state.bgColor, bgIndex: state.bgIndex,
    style: currentStyle(), fontScale: state.fontScale, pos: state.pos, maxWords: state.maxWords,
    colorMain: state.colorMain, colorActive: state.colorActive,
    hook: state.hook, hookStyle: state.hookStyle, segments: state.segments, ...extra,
  };
}
function sortSegs() { state.segments.sort((a, b) => a.start - b.start); }

// Uzun subtitrni bir necha qisqasiga bo‘lish
function splitLong(seg, maxWords = 7) {
  const words = seg.text.trim().split(/\s+/).filter(Boolean);
  if (words.length <= maxWords) return [seg];
  const parts = Math.ceil(words.length / maxWords);
  const per = Math.ceil(words.length / parts);
  const total = words.reduce((a, w) => a + w.length + 1, 0);
  const res = [];
  let t = seg.start;
  for (let i = 0; i < words.length; i += per) {
    const group = words.slice(i, i + per);
    const len = group.reduce((a, w) => a + w.length + 1, 0);
    const end = i + per >= words.length ? seg.end : t + ((seg.end - seg.start) * len) / total;
    res.push({ start: +t.toFixed(2), end: +end.toFixed(2), text: group.join(' ') });
    t = end;
  }
  return res;
}
function applyScript(text) {
  text = normalizeApostrophes(text);
  if (state.script === 'latin' && hasCyrillic(text)) return toLatin(text);
  if (state.script === 'cyr' && !hasCyrillic(text)) return toCyrillic(text);
  return text;
}

/* ================= marshrut (ko‘rinishlar) ================= */
function route() {
  const id = (location.hash || '#bosh').slice(1);
  const view = ['bosh', 'muharrir', 'shablonlar'].includes(id) ? id : 'bosh';
  $$('.view').forEach((v) => (v.hidden = v.id !== 'view-' + view));
  $$('[data-nav]').forEach((a) => a.classList.toggle('active', a.dataset.nav === view));
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);

$$('[data-go]').forEach((btn) =>
  btn.addEventListener('click', () => {
    location.hash = btn.dataset.go;
    if (btn.dataset.action === 'upload') $('#fileInput').click();
    if (btn.dataset.action === 'camera') openCamera();
  }),
);

/* ================= media ================= */
const video = $('#srcVideo');
const canvas = $('#mainCanvas');
const ctx = canvas.getContext('2d');
let mediaBlob = null;
let hasMedia = false;
let recDuration = 0;
let bgImage = null;
let playing = false;
let demoT = 0;

function mediaForDraw() {
  if (hasMedia && video.videoWidth) return { el: video, w: video.videoWidth, h: video.videoHeight };
  if (bgImage) return { el: bgImage, w: bgImage.naturalWidth, h: bgImage.naturalHeight };
  return null;
}
function segEnd() { return state.segments.reduce((m, s) => Math.max(m, s.end), 0); }
function duration() {
  if (hasMedia) {
    const d = video.duration;
    if (isFinite(d) && d > 0) return d;
    return recDuration || Math.max(segEnd(), 1);
  }
  return Math.max(segEnd() + 0.4, 3);
}
function now() { return hasMedia ? video.currentTime : demoT; }

function loadMedia(blob, name) {
  mediaBlob = blob;
  hasMedia = true;
  playing = false;
  video.pause();
  if (video.src) URL.revokeObjectURL(video.src);
  video.src = URL.createObjectURL(blob);
  video.load();
  $('#mediaName').textContent = name;
  $('#sampleBadge').hidden = true;
  if (state.demoSegs) {
    state.segments = [];
    state.demoSegs = false;
    renderSegList();
  }
  video.addEventListener('loadedmetadata', () => {
    // MediaRecorder yozuvlarida davomiylik ba'zan Infinity bo‘ladi
    if (!isFinite(video.duration)) {
      video.currentTime = 1e7;
      video.addEventListener('timeupdate', function fix() { video.removeEventListener('timeupdate', fix); video.currentTime = 0; }, { once: true });
    } else {
      video.currentTime = 0.01;
    }
    renderTimeline();
  }, { once: true });
  updatePlayIcon();
  save();
}

$('#fileInput').addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (f) {
    loadMedia(f, f.name);
    toast('Video yuklandi. Endi “AI subtitr” tugmasini bosing.');
  }
  e.target.value = '';
});

// sudrab tashlash
const stage = $('#stage');
['dragenter', 'dragover'].forEach((ev) => stage.addEventListener(ev, (e) => { e.preventDefault(); stage.classList.add('drag'); }));
['dragleave', 'drop'].forEach((ev) => stage.addEventListener(ev, (e) => { e.preventDefault(); stage.classList.remove('drag'); }));
stage.addEventListener('drop', (e) => {
  const f = e.dataTransfer.files[0];
  if (!f) return;
  if (f.type.startsWith('image/')) return setBgImage(f);
  loadMedia(f, f.name);
});

/* ================= ijro ================= */
let audioCtx = null, audioDest = null;
function ensureAudioGraph() {
  if (audioCtx) return;
  const AC = window.AudioContext || window.webkitAudioContext;
  audioCtx = new AC();
  const src = audioCtx.createMediaElementSource(video);
  audioDest = audioCtx.createMediaStreamDestination();
  src.connect(audioCtx.destination);
  src.connect(audioDest);
}

async function play() {
  if (hasMedia) {
    if (audioCtx && audioCtx.state === 'suspended') await audioCtx.resume();
    if (video.ended || video.currentTime >= duration() - 0.05) video.currentTime = 0;
    try { await video.play(); } catch (e) { toast('Ijro etib bo‘lmadi: ' + e.message); return; }
  } else if (demoT >= duration()) demoT = 0;
  playing = true;
  updatePlayIcon();
}
function pause() {
  playing = false;
  if (hasMedia) video.pause();
  updatePlayIcon();
}
function seek(t) {
  t = Math.max(0, Math.min(duration(), t));
  if (hasMedia) video.currentTime = t; else demoT = t;
}
function updatePlayIcon() {
  $('#playIcon').setAttribute('d', playing ? 'M6 4h4v16H6zM14 4h4v16h-4z' : 'M7 4l13 8-13 8z');
  $('#playBtn').setAttribute('aria-label', playing ? 'Pauza' : 'Ijro etish');
}
video.addEventListener('ended', () => { playing = false; updatePlayIcon(); });
$('#playBtn').addEventListener('click', () => (playing ? pause() : play()));
$('#seek').addEventListener('input', (e) => seek((e.target.value / 1000) * duration()));
document.addEventListener('keydown', (e) => {
  if (e.code !== 'Space' || $('#view-muharrir').hidden) return;
  if (/INPUT|TEXTAREA|SELECT|BUTTON/.test(document.activeElement.tagName)) return;
  e.preventDefault();
  playing ? pause() : play();
});

/* ================= asosiy chizish sikli ================= */
function resizeMain(short = 720) {
  const [W, H] = canvasSize(state.aspect, short);
  if (canvas.width !== W || canvas.height !== H) { canvas.width = W; canvas.height = H; }
}

let lastTs = performance.now();
let lastActive = null;
let exportJob = null;
function loop(ts) {
  const dt = Math.min(0.1, (ts - lastTs) / 1000);
  lastTs = ts;
  if (playing && !hasMedia) {
    demoT += dt;
    if (demoT >= duration()) {
      if (exportJob) { demoT = duration(); playing = false; exportJob.finish(); }
      else demoT = 0;
    }
  }
  if (!$('#view-muharrir').hidden || exportJob) {
    const t = now();
    drawFrame(ctx, canvas.width, canvas.height, renderOpts(), t, mediaForDraw());
    const d = duration();
    $('#timeLabel').textContent = `${fmt(t)} / ${fmt(d)}`;
    if (document.activeElement !== $('#seek')) $('#seek').value = Math.round((t / d) * 1000) || 0;
    const seg = findSegment(state.segments, t);
    if (seg !== lastActive) {
      lastActive = seg;
      const i = state.segments.indexOf(seg);
      $$('#segList .seg').forEach((li, j) => li.classList.toggle('on', j === i));
      $$('#tlSegs span').forEach((sp, j) => sp.classList.toggle('on', j === i));
    }
    if (exportJob) exportJob.tick(t, d);
  }
  drawMinis(ts / 1000);
  requestAnimationFrame(loop);
}

/* ================= subtitrlar ro‘yxati ================= */
function renderSegList() {
  const list = $('#segList');
  list.innerHTML = '';
  if (!state.segments.length) {
    list.innerHTML = '<li class="empty">Subtitrlar yo‘q. “AI subtitr”ni bosing, SRT import qiling yoki “+ Qator” bilan qo‘lda qo‘shing.</li>';
  }
  state.segments.forEach((seg, i) => {
    const li = document.createElement('li');
    li.className = 'seg';
    li.innerHTML = `
      <div class="seg-top">
        <button class="go" title="Shu joyga o‘tish" aria-label="Shu joyga o‘tish">▶</button>
        <input class="t-start" id="seg-${i}-s" value="${fmt(seg.start)}" aria-label="Boshlanish">
        <span class="arrow">→</span>
        <input class="t-end" id="seg-${i}-e" value="${fmt(seg.end)}" aria-label="Tugash">
        <button class="del" aria-label="O‘chirish">O‘chirish</button>
      </div>
      <textarea rows="2" id="seg-${i}-t" aria-label="Subtitr matni"></textarea>`;
    const ta = $('textarea', li);
    ta.value = seg.text;
    ta.addEventListener('input', () => { seg.text = ta.value; state.demoSegs = false; save(); });
    ta.addEventListener('focus', () => { if (!playing) seek(seg.start + 0.01); });
    $('.go', li).addEventListener('click', () => { seek(seg.start + 0.01); play(); });
    $('.del', li).addEventListener('click', () => { state.segments.splice(i, 1); renderSegList(); save(); });
    const onTime = (cls, key) => $(cls, li).addEventListener('change', (e) => {
      const v = parseTime(e.target.value);
      if (v == null) { e.target.value = fmt(seg[key]); return toast('Vaqt formati: 0:05.2'); }
      seg[key] = v;
      if (seg.end <= seg.start) seg.end = seg.start + 0.5;
      sortSegs(); renderSegList(); save();
    });
    onTime('.t-start', 'start');
    onTime('.t-end', 'end');
    list.appendChild(li);
  });
  lastActive = undefined;
  renderTimeline();
}
function renderTimeline() {
  const d = duration();
  $('#tlSegs').innerHTML = state.segments
    .map((s) => `<span style="left:${(s.start / d) * 100}%;width:${Math.max(0.4, ((s.end - s.start) / d) * 100)}%"></span>`)
    .join('');
}

$('#addSeg').addEventListener('click', () => {
  const t = now();
  const next = state.segments.find((s) => s.start > t);
  const end = Math.min(t + 2, next ? next.start : t + 2, hasMedia ? duration() : t + 2);
  state.segments.push({ start: +t.toFixed(2), end: +Math.max(end, t + 0.5).toFixed(2), text: 'Yangi subtitr' });
  state.demoSegs = false;
  sortSegs(); renderSegList(); save();
});
$('#clearSegs').addEventListener('click', () => ($('#clearConfirm').hidden = false));
$('#clearNo').addEventListener('click', () => ($('#clearConfirm').hidden = true));
$('#clearYes').addEventListener('click', () => {
  state.segments = [];
  state.demoSegs = false;
  $('#clearConfirm').hidden = true;
  renderSegList(); save();
});

function setScript(kind) {
  state.script = kind;
  state.segments.forEach((s) => (s.text = kind === 'latin' ? toLatin(s.text) : toCyrillic(s.text)));
  if (state.hook) state.hook = kind === 'latin' ? toLatin(state.hook) : toCyrillic(state.hook);
  $('#hookInput').value = state.hook;
  $('#toLatin').classList.toggle('active', kind === 'latin');
  $('#toCyr').classList.toggle('active', kind === 'cyr');
  renderSegList(); save();
}
$('#toLatin').addEventListener('click', () => setScript('latin'));
$('#toCyr').addEventListener('click', () => setScript('cyr'));

/* ================= SRT / VTT ================= */
function parseSubs(text) {
  const blocks = text.replace(/\r/g, '').split(/\n\s*\n/);
  const segs = [];
  const re = /(\d{1,2}:)?(\d{1,2}):(\d{2})[.,](\d{1,3})\s*-->\s*(\d{1,2}:)?(\d{1,2}):(\d{2})[.,](\d{1,3})/;
  const toS = (h, m, s, ms) => (parseInt(h || '0', 10) * 3600) + parseInt(m, 10) * 60 + parseInt(s, 10) + parseInt(ms.padEnd(3, '0'), 10) / 1000;
  for (const b of blocks) {
    const lines = b.split('\n');
    const idx = lines.findIndex((l) => re.test(l));
    if (idx < 0) continue;
    const m = lines[idx].match(re);
    const start = toS(m[1] && m[1].slice(0, -1), m[2], m[3], m[4]);
    const end = toS(m[5] && m[5].slice(0, -1), m[6], m[7], m[8]);
    const txt = lines.slice(idx + 1).join(' ').replace(/<[^>]+>/g, '').trim();
    if (txt) segs.push({ start, end, text: txt });
  }
  return segs;
}
function stamp(t, sep) {
  const ms = Math.round(t * 1000);
  const h = Math.floor(ms / 3600000), m = Math.floor((ms % 3600000) / 60000), s = Math.floor((ms % 60000) / 1000);
  const p = (n, l = 2) => String(n).padStart(l, '0');
  return `${p(h)}:${p(m)}:${p(s)}${sep}${p(ms % 1000, 3)}`;
}
const toSRT = () => state.segments.map((s, i) => `${i + 1}\n${stamp(s.start, ',')} --> ${stamp(s.end, ',')}\n${s.text}\n`).join('\n');
const toVTT = () => 'WEBVTT\n\n' + state.segments.map((s) => `${stamp(s.start, '.')} --> ${stamp(s.end, '.')}\n${s.text}\n`).join('\n');

$('#srtInput').addEventListener('change', async (e) => {
  const f = e.target.files[0];
  e.target.value = '';
  if (!f) return;
  const segs = parseSubs(await f.text());
  if (!segs.length) return toast('Faylda subtitr topilmadi');
  state.segments = segs;
  state.demoSegs = false;
  renderSegList(); save();
  toast(`${segs.length} ta subtitr import qilindi`);
});
const baseName = () => !hasMedia ? 'ummon' : ($('#mediaName').textContent.replace(/\.[^.]+$/, '') || 'ummon').replace(/[^\w\-]+/g, '_').slice(0, 40) || 'ummon';
function needSegs() { if (!state.segments.length) { toast('Avval subtitr yarating'); return false; } return true; }
$('#srtBtn').addEventListener('click', () => needSegs() && download(new Blob([toSRT()], { type: 'text/plain' }), baseName() + '.srt'));
$('#vttBtn').addEventListener('click', () => needSegs() && download(new Blob([toVTT()], { type: 'text/vtt' }), baseName() + '.vtt'));
$('#txtBtn').addEventListener('click', () => needSegs() && download(new Blob([state.segments.map((s) => s.text).join('\n')], { type: 'text/plain' }), baseName() + '.txt'));
$('#copyBtn').addEventListener('click', async () => {
  if (!needSegs()) return;
  try { await navigator.clipboard.writeText(state.segments.map((s) => s.text).join(' ')); toast('Matn nusxalandi'); }
  catch { toast('Nusxalab bo‘lmadi'); }
});

/* ================= AI subtitr (Whisper) ================= */
let worker = null;
let aiBusy = false;
async function decodeTo16k(blob) {
  const buf = await blob.arrayBuffer();
  const AC = window.AudioContext || window.webkitAudioContext;
  const ac = new AC();
  const decoded = await new Promise((res, rej) => ac.decodeAudioData(buf, res, rej));
  ac.close && ac.close();
  const len = Math.ceil(decoded.duration * 16000);
  const off = new OfflineAudioContext(1, len, 16000);
  const src = off.createBufferSource();
  src.buffer = decoded;
  src.connect(off.destination);
  src.start();
  const rendered = await off.startRendering();
  return { audio: rendered.getChannelData(0), dur: decoded.duration };
}

$('#aiBtn').addEventListener('click', async () => {
  if (aiBusy) return;
  if (!hasMedia || !mediaBlob) return toast('Avval video yuklang yoki kamerada yozing');
  aiBusy = true;
  const btn = $('#aiBtn');
  btn.disabled = true;
  const prog = $('#aiProgress'), bar = $('#aiBar'), status = $('#aiStatus');
  prog.hidden = false;
  bar.style.width = '3%';
  status.textContent = 'Audio ajratilmoqda…';
  const finish = () => { aiBusy = false; btn.disabled = false; };
  let audio, dur;
  try {
    ({ audio, dur } = await decodeTo16k(mediaBlob));
  } catch (e) {
    finish();
    status.textContent = 'Audio o‘qilmadi';
    return toast('Bu fayldan audio ajratib bo‘lmadi. MP4 yoki WEBM sinab ko‘ring.');
  }
  if (!worker) worker = new Worker(new URL('./whisper-worker.js', import.meta.url), { type: 'module' });
  const files = {};
  const started = performance.now();
  let fakeTimer = 0;
  worker.onmessage = (e) => {
    const m = e.data;
    if (m.type === 'progress' && m.p.status === 'progress') {
      files[m.p.file] = [m.p.loaded || 0, m.p.total || 0];
      const [l, t] = Object.values(files).reduce((a, [x, y]) => [a[0] + x, a[1] + y], [0, 0]);
      const pct = t ? (l / t) * 100 : 0;
      bar.style.width = `${Math.max(3, pct * 0.6)}%`;
      status.textContent = `Model yuklanmoqda… ${Math.round(pct)}% (${(l / 1048576).toFixed(0)} / ${(t / 1048576).toFixed(0)} MB)`;
    } else if (m.type === 'status') {
      status.textContent = m.text;
      if (m.text.startsWith('Nutq')) {
        // transkripsiya vaqtini taxminan ko‘rsatish
        const t0 = performance.now();
        const est = Math.max(8, dur * 0.6);
        clearInterval(fakeTimer);
        fakeTimer = setInterval(() => {
          const p = Math.min(0.97, (performance.now() - t0) / 1000 / est);
          bar.style.width = `${60 + p * 40}%`;
        }, 300);
      }
    } else if (m.type === 'done') {
      clearInterval(fakeTimer);
      const chunks = m.out.chunks && m.out.chunks.length ? m.out.chunks : [{ text: m.out.text, timestamp: [0, dur] }];
      const segs = [];
      for (const c of chunks) {
        let [s, en] = c.timestamp || [0, null];
        if (s == null) s = 0;
        if (en == null || en <= s) en = Math.min(dur, s + 4);
        const text = applyScript(String(c.text || '').replace(/\[[^\]]*\]|\([^)]*\)/g, '').replace(/\s+/g, ' ').trim());
        if (!text) continue;
        segs.push(...splitLong({ start: s, end: en, text }));
      }
      state.segments = segs;
      state.demoSegs = false;
      sortSegs(); renderSegList(); save();
      bar.style.width = '100%';
      status.textContent = `Tayyor: ${segs.length} ta subtitr (${((performance.now() - started) / 1000).toFixed(0)} s)`;
      toast(segs.length ? 'Subtitrlar tayyor! Matnni tekshirib chiqing.' : 'Nutq topilmadi');
      finish();
    } else if (m.type === 'error') {
      clearInterval(fakeTimer);
      status.textContent = 'Xato: ' + m.message;
      toast('AI subtitr ishlamadi. Internet aloqasini tekshiring yoki kichikroq model tanlang.');
      finish();
    }
  };
  worker.onerror = (e) => {
    e.preventDefault && e.preventDefault();
    clearInterval(fakeTimer);
    worker.terminate();
    worker = null;
    status.textContent = 'AI modulini yuklab bo‘lmadi';
    toast('AI modulini yuklab bo‘lmadi. Internet aloqasini tekshirib, qayta urinib ko‘ring.');
    finish();
  };
  worker.postMessage({ audio, model: $('#modelSel').value }, [audio.buffer]);
});

/* ================= uslublar ================= */
function buildStyleGrid(container, w, h, onPick) {
  container.innerHTML = '';
  CAPTION_STYLES.forEach((st, i) => {
    const b = document.createElement('button');
    b.className = 'style-card';
    b.dataset.style = st.id;
    b.innerHTML = `<canvas width="${w}" height="${h}" data-mini="${st.id}" data-bg="${[2, 0, 5, 1, 4, 3, 6, 10, 8, 11, 7, 0][i % 12]}" data-nohook="1"></canvas><span>${st.name}</span>`;
    b.addEventListener('click', () => onPick(st));
    container.appendChild(b);
  });
}
function pickStyle(st) {
  state.styleId = st.id;
  state.colorMain = null;
  state.colorActive = null;
  syncControls();
  save();
}
buildStyleGrid($('#styleGrid'), 200, 150, pickStyle);
buildStyleGrid($('#styleGridBig'), 240, 300, (st) => { pickStyle(st); location.hash = 'muharrir'; toast(`“${st.name}” uslubi tanlandi`); });

/* ================= video shablonlari ================= */
function applyTemplate(tpl) {
  Object.assign(state, {
    aspect: tpl.aspect, fit: tpl.fit, bgMode: tpl.bgMode || 'blur', styleId: tpl.style,
    hook: state.script === 'cyr' ? toCyrillic(tpl.hook) : tpl.hook, hookStyle: tpl.hookStyle,
    bgIndex: tpl.bg, maxWords: '', colorMain: null, colorActive: null, pos: null, fontScale: 1,
  });
  syncControls();
  save();
  location.hash = 'muharrir';
  toast(`“${tpl.name}” shabloni qo‘llandi`);
}
(function buildTemplates() {
  const grid = $('#videoTplGrid');
  VIDEO_TEMPLATES.forEach((tpl) => {
    const [W, H] = canvasSize(tpl.aspect, 200);
    const b = document.createElement('button');
    b.className = 'tpl-card';
    b.innerHTML = `<canvas width="${W}" height="${H}" data-tpl="${tpl.id}"></canvas><b>${tpl.name}</b><small>${tpl.desc}</small>`;
    b.addEventListener('click', () => applyTemplate(tpl));
    grid.appendChild(b);
  });
})();

/* ================= namoyish canvaslari (bosh sahifa, kartalar) ================= */
const DEMO_LEN = 8.8;
const heroStyles = ['karaoke', 'pop', 'highlight', 'headline', 'neon', 'bold-box'];
function drawMinis(time) {
  const view = $$('.view').find((v) => !v.hidden);
  if (!view) return;
  // ~30 fps yetarli
  if (drawMinis._last && time - drawMinis._last < 1 / 30) return;
  drawMinis._last = time;
  const t = time % DEMO_LEN;
  if (view.id === 'view-bosh') {
    const hc = $('#heroCanvas');
    const cycle = Math.floor(time / DEMO_LEN) % heroStyles.length;
    const st = styleById(heroStyles[cycle]);
    $('#heroTag').textContent = st.name;
    drawFrame(hc.getContext('2d'), hc.width, hc.height, { style: st, segments: DEMO_SEGMENTS, bgIndex: cycle * 2, hook: '' }, t, null);
  }
  $$('canvas[data-mini]', view).forEach((c, i) => {
    const st = styleById(c.dataset.mini);
    drawFrame(c.getContext('2d'), c.width, c.height,
      { style: st, segments: DEMO_SEGMENTS, bgIndex: c.dataset.bg != null ? +c.dataset.bg : i * 3 + 1, hook: '', pos: c.dataset.nohook ? 0.5 : null, fontScale: c.dataset.nohook ? (c.width > c.height ? 1.6 : 1.3) : 1 },
      t, null);
  });
  $$('canvas[data-tpl]', view).forEach((c) => {
    const tpl = VIDEO_TEMPLATES.find((x) => x.id === c.dataset.tpl);
    drawFrame(c.getContext('2d'), c.width, c.height,
      { style: styleById(tpl.style), segments: DEMO_SEGMENTS, bgIndex: tpl.bg, hook: tpl.hook, hookStyle: tpl.hookStyle }, t, null);
  });
}

/* ================= boshqaruv elementlari ================= */
function syncControls() {
  resizeMain();
  const st = currentStyle();
  $$('.style-card').forEach((b) => b.classList.toggle('active', b.dataset.style === state.styleId));
  $$('[data-aspect]').forEach((b) => b.classList.toggle('active', b.dataset.aspect === state.aspect));
  $$('[data-fit]').forEach((b) => b.classList.toggle('active', b.dataset.fit === state.fit));
  $('#fontScale').value = Math.round(state.fontScale * 100);
  $('#fontScaleOut').textContent = Math.round(state.fontScale * 100) + '%';
  const pos = state.pos != null ? state.pos : (st.pos || 0.72);
  $('#posY').value = Math.round(pos * 100);
  $('#posYOut').textContent = Math.round(pos * 100) + '%';
  $('#maxWords').value = state.maxWords;
  $('#colorMain').value = toHex(state.colorMain || st.color);
  $('#colorActive').value = toHex(state.colorActive || st.active);
  $('#bgMode').value = state.bgMode;
  $('#bgColor').value = state.bgColor;
  $('#hookInput').value = state.hook;
  $('#hookStyle').value = state.hookStyle;
  $('#toLatin').classList.toggle('active', state.script === 'latin');
  $('#toCyr').classList.toggle('active', state.script === 'cyr');
  $$('#bgSwatches button').forEach((b, i) => b.classList.toggle('active', i === state.bgIndex && !bgImage));
}
function toHex(c) {
  if (/^#[0-9a-f]{6}$/i.test(c)) return c;
  const m = String(c).match(/\d+/g);
  return m ? '#' + m.slice(0, 3).map((n) => (+n).toString(16).padStart(2, '0')).join('') : '#ffffff';
}

$$('.tabs button').forEach((b) =>
  b.addEventListener('click', () => {
    $$('.tabs button').forEach((x) => x.classList.toggle('active', x === b));
    $$('.tab-body').forEach((body) => (body.hidden = body.dataset.body !== b.dataset.tab));
  }),
);
$('#fontScale').addEventListener('input', (e) => { state.fontScale = e.target.value / 100; $('#fontScaleOut').textContent = e.target.value + '%'; save(); });
$('#posY').addEventListener('input', (e) => { state.pos = e.target.value / 100; $('#posYOut').textContent = e.target.value + '%'; save(); });
$('#maxWords').addEventListener('change', (e) => { state.maxWords = e.target.value; save(); });
$('#colorMain').addEventListener('input', (e) => { state.colorMain = e.target.value; save(); });
$('#colorActive').addEventListener('input', (e) => { state.colorActive = e.target.value; save(); });
$$('[data-aspect]').forEach((b) => b.addEventListener('click', () => { state.aspect = b.dataset.aspect; syncControls(); save(); }));
$$('[data-fit]').forEach((b) => b.addEventListener('click', () => { state.fit = b.dataset.fit; syncControls(); save(); }));
$('#bgMode').addEventListener('change', (e) => { state.bgMode = e.target.value; save(); });
$('#bgColor').addEventListener('input', (e) => { state.bgColor = e.target.value; save(); });
$('#hookInput').addEventListener('input', (e) => { state.hook = e.target.value; save(); });
$('#hookStyle').addEventListener('change', (e) => { state.hookStyle = e.target.value; save(); });

// fonlar
(function buildSwatches() {
  const wrap = $('#bgSwatches');
  BACKGROUNDS.forEach(([a, b], i) => {
    const btn = document.createElement('button');
    btn.style.background = `linear-gradient(160deg, ${a}, ${b})`;
    btn.setAttribute('aria-label', `Fon ${i + 1}`);
    btn.addEventListener('click', () => { state.bgIndex = i; bgImage = null; syncControls(); save(); });
    wrap.appendChild(btn);
  });
})();
function setBgImage(file) {
  const img = new Image();
  img.onload = () => { bgImage = img; syncControls(); toast(hasMedia && video.videoWidth ? 'Rasm video bo‘lmaganda fon bo‘ladi' : 'Fon rasmi o‘rnatildi'); };
  img.src = URL.createObjectURL(file);
}
$('#bgImage').addEventListener('change', (e) => { const f = e.target.files[0]; if (f) setBgImage(f); e.target.value = ''; });

// matndan video
$('#wps').addEventListener('input', (e) => ($('#wpsOut').textContent = (e.target.value / 10).toFixed(1) + ' so‘z/soniya'));
$('#scriptBtn').addEventListener('click', () => {
  const text = $('#scriptInput').value.trim();
  if (!text) return toast('Ssenariy matnini yozing');
  const wps = $('#wps').value / 10;
  const sentences = text.replace(/\s+/g, ' ').match(/[^.!?…]+[.!?…]*/g) || [text];
  let t = 0.3;
  const segs = [];
  for (const raw of sentences) {
    const s = applyScript(raw.trim());
    if (!s) continue;
    const n = s.split(/\s+/).length;
    const d = Math.max(1.2, n / wps);
    segs.push(...splitLong({ start: +t.toFixed(2), end: +(t + d).toFixed(2), text: s }, 6));
    t += d + 0.15;
  }
  state.segments = segs;
  state.demoSegs = false;
  if (hasMedia && !video.videoWidth) { /* faqat audio: saqlanadi */ }
  else if (hasMedia) toast('Subtitrlar videongiz ustiga joylandi');
  renderSegList(); save();
  seek(0); play();
  $$('.tabs button')[0].click();
});

/* ================= kamera ================= */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let camStream = null, camRec = null, camChunks = [], recStart = 0, recTimer = 0, facing = 'user';
let speech = null, liveSegs = [], speechStart = null, recording = false;

async function startCam() {
  stopCam();
  try {
    camStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: facing, width: { ideal: 1080 }, height: { ideal: 1920 } },
      audio: { echoCancellation: true, noiseSuppression: true },
    });
    $('#camVideo').srcObject = camStream;
    $('#camVideo').style.transform = facing === 'user' ? 'scaleX(-1)' : '';
    $('#camNote').textContent = SR ? 'Jonli subtitr brauzerning nutq tanish xizmati orqali ishlaydi. Natija yaxshi bo‘lmasa, yozuvdan keyin “AI subtitr”ni bosing.' : 'Brauzeringiz jonli nutq tanishni qo‘llamaydi. Yozuvdan keyin “AI subtitr” tugmasini bosing.';
  } catch (e) {
    $('#camNote').textContent = 'Kameraga ruxsat berilmadi yoki kamera topilmadi. Brauzer sozlamalarida ruxsat bering.';
  }
}
function stopCam() {
  if (camStream) camStream.getTracks().forEach((t) => t.stop());
  camStream = null;
}
function openCamera() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return toast('Bu brauzerda kamera mavjud emas (HTTPS kerak)');
  $('#camModal').hidden = false;
  $('#camCaption').textContent = '';
  startCam();
}
function closeCamera() {
  if (recording) stopRecording(false);
  stopCam();
  $('#camModal').hidden = true;
}
$('#cameraBtn').addEventListener('click', openCamera);
$('#cameraBtn2').addEventListener('click', openCamera);
$('#camClose').addEventListener('click', closeCamera);
$('#camFlip').addEventListener('click', () => { if (recording) return; facing = facing === 'user' ? 'environment' : 'user'; startCam(); });

function pickMime(kind = 'video') {
  const types = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4;codecs=avc1', 'video/mp4', 'video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'];
  return types.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || '';
}
const elapsed = () => (performance.now() - recStart) / 1000;

function startSpeech() {
  if (!SR || !$('#liveCaps').checked) return;
  speech = new SR();
  speech.lang = 'uz-UZ';
  speech.continuous = true;
  speech.interimResults = true;
  speech.onresult = (e) => {
    const t = elapsed();
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i];
      if (speechStart == null) speechStart = Math.max(0, t - 0.8);
      if (r.isFinal) {
        const text = applyScript(r[0].transcript.trim());
        if (text) liveSegs.push(...splitLong({ start: speechStart, end: Math.max(t, speechStart + 0.6), text }));
        speechStart = null;
        $('#camCaption').textContent = text;
      } else interim += r[0].transcript;
    }
    if (interim) $('#camCaption').textContent = interim;
  };
  speech.onerror = (e) => {
    if (e.error === 'language-not-supported') $('#camNote').textContent = 'Brauzer o‘zbek tilini jonli tanimaydi. Yozuvdan keyin “AI subtitr”ni bosing.';
  };
  speech.onend = () => { if (recording && speech) try { speech.start(); } catch { /* */ } };
  try { speech.start(); } catch { /* */ }
}

function startRecording() {
  if (!camStream) return toast('Kamera hali tayyor emas');
  if (!window.MediaRecorder) return toast('Brauzeringiz video yozishni qo‘llamaydi');
  const mime = pickMime();
  camChunks = [];
  liveSegs = [];
  speechStart = null;
  camRec = new MediaRecorder(camStream, mime ? { mimeType: mime } : undefined);
  camRec.ondataavailable = (e) => e.data.size && camChunks.push(e.data);
  camRec.start(250);
  recStart = performance.now();
  recording = true;
  $('#recDot').hidden = false;
  $('#recBtn').textContent = 'To‘xtatish';
  recTimer = setInterval(() => ($('#recTime').textContent = fmt(elapsed(), false)), 250);
  startSpeech();
}
function stopRecording(keep = true) {
  recording = false;
  clearInterval(recTimer);
  $('#recDot').hidden = true;
  $('#recBtn').textContent = 'Yozishni boshlash';
  if (speech) { const s = speech; speech = null; try { s.stop(); } catch { /* */ } }
  const dur = elapsed();
  if (!camRec) return;
  camRec.onstop = () => {
    if (!keep) return;
    const blob = new Blob(camChunks, { type: camRec.mimeType || 'video/webm' });
    recDuration = dur;
    loadMedia(blob, `Kamera yozuvi ${new Date().toLocaleTimeString('uz')}`);
    if (liveSegs.length) {
      state.segments = liveSegs;
      state.demoSegs = false;
      renderSegList(); save();
      toast(`Yozuv tayyor: ${liveSegs.length} ta jonli subtitr`);
    } else toast('Yozuv tayyor. Endi “AI subtitr”ni bosing.');
    stopCam();
    $('#camModal').hidden = true;
    location.hash = 'muharrir';
  };
  camRec.stop();
}
$('#recBtn').addEventListener('click', () => (recording ? stopRecording(true) : startRecording()));

/* ================= eksport ================= */
async function exportVideo() {
  if (exportJob) { exportJob.cancel(); return; }
  if (!window.MediaRecorder || !canvas.captureStream) return toast('Brauzeringiz video eksportni qo‘llamaydi. Chrome yoki Safari’ning yangi versiyasini ishlating.');
  const mime = pickMime();
  const btn = $('#exportBtn');
  const prog = $('#exProgress'), bar = $('#exBar'), status = $('#exStatus');
  pause();
  resizeMain(+$('#quality').value);
  const stream = canvas.captureStream(30);
  if (hasMedia) {
    try {
      ensureAudioGraph();
      if (audioCtx.state === 'suspended') await audioCtx.resume();
      audioDest.stream.getAudioTracks().forEach((tr) => stream.addTrack(tr));
    } catch (e) { console.warn('Audio ulanmadi', e); }
  }
  const rec = new MediaRecorder(stream, { ...(mime ? { mimeType: mime } : {}), videoBitsPerSecond: +$('#quality').value >= 1080 ? 8e6 : 5e6 });
  const chunks = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);

  let cancelled = false;
  const done = new Promise((resolve) => {
    exportJob = {
      finish: resolve,
      cancel: () => { cancelled = true; resolve(); },
      tick: (t, d) => {
        const p = Math.min(1, t / d);
        bar.style.width = `${p * 100}%`;
        status.textContent = `Eksport: ${Math.round(p * 100)}% · ${fmt(t, false)} / ${fmt(d, false)}`;
      },
    };
  });
  const onEnded = () => exportJob && exportJob.finish();
  video.addEventListener('ended', onEnded);

  btn.textContent = 'Bekor qilish';
  prog.hidden = false;
  seek(0);
  if (hasMedia) await new Promise((r) => { if (video.seeking) video.addEventListener('seeked', r, { once: true }); else r(); });
  rec.start(250);
  await play();
  await done;
  pause();
  video.removeEventListener('ended', onEnded);
  exportJob = null;
  await new Promise((r) => { rec.onstop = r; rec.stop(); });
  stream.getVideoTracks().forEach((tr) => tr.stop());
  resizeMain();
  btn.textContent = 'Videoni yuklab olish';
  if (cancelled) { status.textContent = 'Bekor qilindi'; bar.style.width = '0%'; return; }
  const type = rec.mimeType || mime || 'video/webm';
  const ext = type.includes('mp4') ? 'mp4' : 'webm';
  const blob = new Blob(chunks, { type });
  status.textContent = `Tayyor · ${(blob.size / 1048576).toFixed(1)} MB · ${ext.toUpperCase()}`;
  download(blob, `${baseName()}-subtitr.${ext}`);
  toast('Video tayyor va yuklab olindi');
}
$('#exportBtn').addEventListener('click', exportVideo);

/* ================= ishga tushirish ================= */
async function loadFonts() {
  const faces = new Set(CAPTION_STYLES.map((s) => `${s.italic ? 'italic ' : ''}${s.weight} 40px "${s.font}"`));
  faces.add('800 40px "Montserrat"');
  await Promise.all([...faces].map((f) => document.fonts.load(f, 'Aa O‘g‘ Ўқ').catch(() => null)));
}
route();
syncControls();
renderSegList();
loadFonts();
requestAnimationFrame(loop);
