// Ummon Ovoz: Gemini Voices API (voice replication) + Gemini 3.8 Flash TTS, to'g'ridan-to'g'ri brauzerdan.
const $ = (sel, root = document) => root.querySelector(sel);

const API = 'https://generativelanguage.googleapis.com/v1beta';
const RATE = 24000; // API tavsiyasi: 24 kHz, mono, 16-bit WAV

const CONSENT = {
  'uz-UZ': {
    text: 'Men ushbu ovozning egasiman va Google’ga ushbu ovozdan sintetik ovoz modelini yaratish uchun foydalanishga roziman.',
    hint: 'Sinov: Google o‘zbekcha rozilikni hali rasman qo‘llamasligi mumkin. Rad etilsa, inglizcha variantni tanlang.',
  },
  'en-US': {
    text: 'I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model.',
    hint: 'Talaffuz: «Ay em di ouner ov dis voys end ay kensent tu Gugl yuzing dis voys tu kriyeyt e sintetik voys model.»',
  },
  'zh-CN': {
    text: '我是此声音的拥有者并授权谷歌使用此声音创建语音合成模型',
    hint: 'Pinyin: Wǒ shì cǐ shēngyīn de yōngyǒuzhě bìng shòuquán Gǔgē shǐyòng cǐ shēngyīn chuàngjiàn yǔyīn héchéng móxíng',
  },
};

/* ================= holat ================= */
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* saqlash mavjud emas */ } },
  del(k) { try { localStorage.removeItem(k); } catch { /* e'tiborsiz */ } },
};
let voices = store.get('ummon-voices', []); // [{ name, ref, model, stored, created }]
const clips = { source: null, consent: null }; // { wav: Blob, dur: number }

function toast(msg, ms = 2600) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove('show'), ms);
}
function status(el, msg, kind = '') {
  el.textContent = msg;
  el.className = 'sm' + (kind ? ` vc-${kind}` : '');
}
const fmtSec = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

/* ================= audio: istalgan formatdan 24 kHz mono WAV ================= */
// Video fayllardan ham ovoz olinadi; maxSec dan uzun bo'lsa, boshidan qirqiladi.
async function toWav(blob, maxSec = Infinity) {
  const buf = await blob.arrayBuffer();
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  let decoded;
  try { decoded = await ctx.decodeAudioData(buf); } finally { ctx.close(); }
  const dur = Math.min(decoded.duration, maxSec);
  const off = new OfflineAudioContext(1, Math.ceil(dur * RATE), RATE);
  const src = off.createBufferSource();
  src.buffer = decoded;
  src.connect(off.destination);
  src.start();
  const out = await off.startRendering();
  return { wav: pcmToWav(out.getChannelData(0), RATE), dur, trimmed: decoded.duration > maxSec };
}

function wavHeader(dataLen, rate) {
  const h = new DataView(new ArrayBuffer(44));
  const w = (o, s) => [...s].forEach((c, i) => h.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF'); h.setUint32(4, 36 + dataLen, true); w(8, 'WAVE');
  w(12, 'fmt '); h.setUint32(16, 16, true); h.setUint16(20, 1, true); h.setUint16(22, 1, true);
  h.setUint32(24, rate, true); h.setUint32(28, rate * 2, true); h.setUint16(32, 2, true); h.setUint16(34, 16, true);
  w(36, 'data'); h.setUint32(40, dataLen, true);
  return h.buffer;
}
function pcmToWav(float32, rate) {
  const pcm = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return new Blob([wavHeader(pcm.byteLength, rate), pcm.buffer], { type: 'audio/wav' });
}

function blobToB64(blob) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(String(r.result).split(',')[1]);
    r.onerror = () => rej(r.error);
    r.readAsDataURL(blob);
  });
}
function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

/* ================= yozish / fayl tanlash ================= */
const LIMITS = { source: [10, 30], consent: [2, 60] };

function setupSlot(slot) {
  const root = $(`[data-slot="${slot}"]`);
  const recBtn = $('[data-rec]', root);
  const fileIn = $('[data-file]', root);
  const timer = $('[data-timer]', root);
  const audio = $('[data-audio]', root);
  const info = $('[data-info]', root);
  let rec = null;
  let tick = 0;

  async function accept(blob) {
    status(info, 'Audio tayyorlanmoqda…');
    try {
      clips[slot] = await toWav(blob, LIMITS[slot][1]);
    } catch {
      clips[slot] = null;
      audio.hidden = true;
      status(info, 'Bu fayldan ovoz olib bo‘lmadi. WAV, MP3, M4A yoki MP4/MOV video tanlang.', 'err');
      return;
    }
    const { wav, dur, trimmed } = clips[slot];
    URL.revokeObjectURL(audio.src);
    audio.src = URL.createObjectURL(wav);
    audio.hidden = false;
    const [min, max] = LIMITS[slot];
    if (dur < min || dur > max) status(info, `${dur.toFixed(1)} soniya. Tavsiya: ${min}–${max} soniya, aks holda rad etilishi mumkin.`, 'warn');
    else status(info, `${dur.toFixed(1)} soniya ✓${trimmed ? ' (fayl uzun edi, boshidan qirqildi)' : ''}`, 'ok');
  }

  fileIn.addEventListener('change', () => {
    if (fileIn.files[0]) accept(fileIn.files[0]);
    fileIn.value = '';
  });

  recBtn.addEventListener('click', async () => {
    if (rec) { rec.stop(); return; }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    } catch {
      toast('Mikrofonga ruxsat berilmadi');
      return;
    }
    const chunks = [];
    rec = new MediaRecorder(stream);
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    rec.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      clearInterval(tick);
      timer.hidden = true;
      recBtn.classList.remove('on');
      recBtn.textContent = '● Qayta yozish';
      const blob = new Blob(chunks, { type: rec.mimeType });
      rec = null;
      accept(blob);
    };
    const t0 = performance.now();
    const max = LIMITS[slot][1];
    timer.textContent = '0:00';
    timer.hidden = false;
    tick = setInterval(() => {
      const s = (performance.now() - t0) / 1000;
      timer.textContent = fmtSec(s);
      if (s >= max) rec?.stop();
    }, 250);
    rec.start();
    recBtn.classList.add('on');
    recBtn.textContent = '■ To‘xtatish';
  });
}

/* ================= Gemini API ================= */
function apiKey() {
  const k = $('#apiKey').value.trim();
  if (!k) { toast('Avval Gemini API kalitini kiriting'); $('#apiKey').focus(); }
  return k;
}

async function call(path, key, body) {
  const res = await fetch(`${API}/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-goog-api-key': key },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(friendlyError(res.status, data?.error?.message || res.statusText));
  return data;
}

function friendlyError(code, msg) {
  const m = msg.toLowerCase();
  if (code === 401 || code === 403 || m.includes('api key')) return `API kalit noto‘g‘ri yoki ruxsati yo‘q. (${msg})`;
  if (code === 429 || m.includes('quota') || m.includes('exhausted')) return `Limit tugadi (bepul tarifda kuniga ~10 so‘rov). Keyinroq urinib ko‘ring yoki Lite modelni tanlang. (${msg})`;
  if (m.includes('location') || m.includes('region') || m.includes('not available')) return `Bu xizmat sizning hududingizda mavjud emas. (${msg})`;
  if (m.includes('consent')) return `Rozilik yozuvi tasdiqlanmadi: matn so‘zma-so‘z va namunadagi odamning o‘zi tomonidan o‘qilishi kerak. O‘zbekcha rozilik rad etilsa, inglizchasini sinang. (${msg})`;
  if (code === 400) return `So‘rov rad etildi: audio uzunligi va sifatini tekshiring. (${msg})`;
  return `Gemini API xatosi ${code}: ${msg}`;
}

async function createVoice() {
  const key = apiKey();
  if (!key) return;
  const st = $('#createStatus');
  const name = $('#voiceName').value.trim() || 'Mening ovozim';
  if (!clips.source) return status(st, 'Ovoz namunasini yozing yoki yuklang (2-qadam).', 'err');
  if (!clips.consent) return status(st, 'Rozilik yozuvini yozing yoki yuklang (3-qadam).', 'err');
  if (!$('#ownerOk').checked) return status(st, 'Ovoz egasining ruxsati borligini tasdiqlang.', 'err');

  const model = $('#model').value;
  const stored = $('#storeVoice').checked;
  const btn = $('#createBtn');
  btn.disabled = true;
  status(st, 'Ovoz klonlanmoqda…');
  try {
    const [source, consent] = await Promise.all([blobToB64(clips.source.wav), blobToB64(clips.consent.wav)]);
    // Voices API so'rovi: { voice, store }, maydonlar snake_case (rasmiy google-genai SDK bo'yicha).
    const res = await call('voices', key, {
      voice: {
        model,
        type: 'replicated',
        display_name: name,
        replicated: {
          source_audio: { mime_type: 'audio/wav', data: source },
          consent_audio: { mime_type: 'audio/wav', data: consent },
        },
      },
      store: stored,
    });
    const v = res.voice || res;
    const ref = v.id || v.key || (v.name || '').split('/').pop();
    if (!ref) throw new Error('Ovoz yaratildi, lekin API ID qaytarmadi.');
    voices.unshift({ name: v.display_name || v.displayName || name, ref, model, stored, created: Date.now() });
    store.set('ummon-voices', voices);
    renderVoices(ref);
    status(st, `Tayyor! «${name}» ovozi yaratildi. Endi 5-qadamda matnni o‘qiting.`, 'ok');
    $('#h-tts').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (e) {
    status(st, e.message, 'err');
  } finally {
    btn.disabled = false;
  }
}

let lastUrl = '';
async function synthesize() {
  const key = apiKey();
  if (!key) return;
  const st = $('#ttsStatus');
  const ref = $('#voiceRef').value.trim() || $('#voiceSel').value;
  const text = $('#ttsText').value.trim();
  if (!ref) return status(st, 'Avval ovoz yarating yoki ovoz ID sini qo‘ying.', 'err');
  if (!text) return status(st, 'Matn kiriting.', 'err');

  const known = voices.find((v) => v.ref === ref);
  const model = known?.model || $('#model').value;
  const style = $('#ttsStyle').value.trim();
  const btn = $('#ttsBtn');
  btn.disabled = true;
  status(st, 'Ovozlashtirilmoqda…');
  try {
    const part = { text };
    if (style) part.speechMetadata = { style };
    const data = await call(`models/${model}:generateContent`, key, {
      contents: [{ role: 'user', parts: [part] }],
      generationConfig: {
        responseModalities: ['AUDIO'],
        speechConfig: { voiceConfig: { voice: ref } },
      },
    });
    const inline = data?.candidates?.[0]?.content?.parts?.find((p) => p.inlineData)?.inlineData;
    if (!inline?.data) throw new Error('Javobda audio yo‘q. Matnni qisqartirib qayta urinib ko‘ring.');
    const wav = toWavBlob(b64ToBytes(inline.data), inline.mimeType || '');
    URL.revokeObjectURL(lastUrl);
    lastUrl = URL.createObjectURL(wav);
    const audio = $('#ttsAudio');
    audio.src = lastUrl;
    audio.hidden = false;
    audio.play().catch(() => {});
    const dl = $('#dlBtn');
    dl.href = lastUrl;
    dl.download = `ummon-ovoz-${Date.now()}.wav`;
    dl.hidden = false;
    status(st, 'Tayyor ✓', 'ok');
  } catch (e) {
    status(st, e.message, 'err');
  } finally {
    btn.disabled = false;
  }
}

// API WAV yoki xom PCM (audio/L16;rate=24000) qaytarishi mumkin.
function toWavBlob(bytes, mime) {
  if (/wav/i.test(mime) || String.fromCharCode(...bytes.slice(0, 4)) === 'RIFF') return new Blob([bytes], { type: 'audio/wav' });
  const rate = Number(/rate=(\d+)/i.exec(mime)?.[1]) || RATE;
  return new Blob([wavHeader(bytes.byteLength, rate), bytes], { type: 'audio/wav' });
}

/* ================= saqlangan ovozlar ================= */
function renderVoices(selectRef) {
  const sel = $('#voiceSel');
  sel.replaceChildren(...(voices.length
    ? voices.map((v) => new Option(v.name, v.ref))
    : [new Option('— hali ovoz yo‘q —', '')]));
  if (selectRef) sel.value = selectRef;

  const list = $('#voiceList');
  list.replaceChildren(...voices.map((v) => {
    const li = document.createElement('li');
    const box = document.createElement('div');
    const b = document.createElement('b');
    b.textContent = v.name;
    const code = document.createElement('code');
    code.textContent = v.ref;
    code.title = v.ref;
    box.append(b, code);
    const copy = document.createElement('button');
    copy.type = 'button';
    copy.textContent = 'Nusxa';
    copy.onclick = () => navigator.clipboard?.writeText(v.ref).then(() => toast('ID nusxalandi'));
    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'del';
    del.textContent = '✕';
    del.setAttribute('aria-label', `${v.name} ni ro‘yxatdan o‘chirish`);
    del.onclick = () => {
      voices = voices.filter((x) => x !== v);
      store.set('ummon-voices', voices);
      renderVoices();
      toast('Ro‘yxatdan o‘chirildi (Google’dagi nusxa qoladi)');
    };
    li.append(box, copy, del);
    return li;
  }));
}

/* ================= ishga tushirish ================= */
const keyIn = $('#apiKey');
const savedKey = store.get('ummon-gemini-key', '');
if (savedKey) { keyIn.value = savedKey; $('#keyRemember').checked = true; }
function syncKey() {
  if ($('#keyRemember').checked && keyIn.value.trim()) store.set('ummon-gemini-key', keyIn.value.trim());
  else store.del('ummon-gemini-key');
}
keyIn.addEventListener('change', syncKey);
$('#keyRemember').addEventListener('change', syncKey);
$('#keyToggle').addEventListener('click', (e) => {
  const show = keyIn.type === 'password';
  keyIn.type = show ? 'text' : 'password';
  e.currentTarget.textContent = show ? 'Yashirish' : 'Ko‘rsatish';
});

$('#model').value = store.get('ummon-voice-model', 'gemini-3.8-flash-tts');
$('#model').addEventListener('change', (e) => store.set('ummon-voice-model', e.target.value));

function renderConsent() {
  const c = CONSENT[$('#consentLang').value];
  $('#consentText').textContent = c.text;
  $('#consentText').lang = $('#consentLang').value;
  $('#consentHint').textContent = c.hint;
}
$('#consentLang').addEventListener('change', renderConsent);
renderConsent();

const countText = () => { $('#ttsCount').textContent = `${$('#ttsText').value.length} belgi`; };
$('#ttsText').addEventListener('input', countText);
countText();

if (!window.MediaRecorder || !navigator.mediaDevices?.getUserMedia) {
  document.querySelectorAll('[data-rec]').forEach((b) => { b.disabled = true; b.title = 'Brauzer yozishni qo‘llamaydi'; });
}
setupSlot('source');
setupSlot('consent');
renderVoices();
$('#createBtn').addEventListener('click', createVoice);
$('#ttsBtn').addEventListener('click', synthesize);
