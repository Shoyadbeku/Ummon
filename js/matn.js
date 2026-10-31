// Ummon Matn → Ovoz: Hugging Face Space'dagi Gradio API'ni (/ovozlashtirish) chaqiradi.
const $ = (sel) => document.querySelector(sel);

const DEFAULT_SPACE = 'Baxtbek97/ummon-ovoz';
const API_NAME = 'ovozlashtirish';

const store = {
  get(k, d) { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* saqlash mavjud emas */ } },
};

function toast(msg, ms = 2600) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove('show'), ms);
}
function status(msg, kind = '') {
  const el = $('#status');
  el.textContent = msg;
  el.className = 'sm' + (kind ? ` vc-${kind}` : '');
}

// "egasi/nomi", huggingface.co/spaces/... yoki to'liq *.hf.space manzilidan API manzili.
function spaceUrl(input) {
  const s = input.trim().replace(/\/+$/, '');
  if (/^https?:\/\//i.test(s) && !/huggingface\.co\//i.test(s)) return s; // *.hf.space yoki boshqa server
  const m = /(?:huggingface\.co\/spaces\/)?([\w.-]+)\/([\w.-]+)$/i.exec(s);
  if (!m) throw new Error('Space manzili noto‘g‘ri. Masalan: egasi/space-nomi');
  const sub = `${m[1]}-${m[2]}`.toLowerCase().replace(/[_.]/g, '-');
  return `https://${sub}.hf.space`;
}

// Gradio /call API: POST → event_id, so'ng GET SSE oqimidan natija.
async function callSpace(base, data) {
  const res = await fetch(`${base}/gradio_api/call/${API_NAME}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data }),
  });
  if (!res.ok) {
    if (res.status === 404) throw new Error('Space topilmadi yoki hali ishga tushmagan (404). Manzilni tekshiring.');
    if (res.status === 503) throw new Error('Space uyg‘onyapti yoki qurilyapti (503). Bir daqiqadan keyin qayta urinib ko‘ring.');
    throw new Error(`Space xatosi ${res.status}`);
  }
  const { event_id: id } = await res.json();
  const stream = await fetch(`${base}/gradio_api/call/${API_NAME}/${id}`);
  const text = await stream.text();
  let event = '';
  for (const line of text.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim();
    else if (line.startsWith('data:')) {
      const payload = line.slice(5).trim();
      if (event === 'complete') return JSON.parse(payload);
      if (event === 'error') {
        let msg = payload;
        try { msg = JSON.parse(payload) ?? 'noma’lum xato'; } catch { /* matn holida qoladi */ }
        throw new Error(`Space xatosi: ${msg}`);
      }
    }
  }
  throw new Error('Space natija qaytarmadi.');
}

async function synthesize() {
  const text = $('#text').value.trim();
  if (!text) { toast('Matn kiriting'); $('#text').focus(); return; }
  let base;
  try { base = spaceUrl($('#space').value || DEFAULT_SPACE); } catch (e) { status(e.message, 'err'); return; }

  const btn = $('#goBtn');
  btn.disabled = true;
  $('#dlBtn').hidden = true;
  const t0 = Date.now();
  const tick = setInterval(() => status(`Ovozlashtirilmoqda… ${Math.round((Date.now() - t0) / 1000)} s`), 1000);
  status('Ovozlashtirilmoqda…');
  try {
    const [file] = await callSpace(base, [
      text,
      $('#baseVoice').value,
      Number($('#rate').value),
      Number($('#pitch').value),
      Number($('#protect').value),
    ]);
    const url = file?.url || `${base}/gradio_api/file=${file?.path}`;
    const blob = await (await fetch(url)).blob();
    const obj = URL.createObjectURL(blob);
    URL.revokeObjectURL($('#audio').src);
    $('#audio').src = obj;
    $('#audio').hidden = false;
    $('#audio').play().catch(() => {});
    $('#dlBtn').href = obj;
    $('#dlBtn').hidden = false;
    status(`Tayyor: ${Math.round((Date.now() - t0) / 1000)} soniyada.`, 'ok');
  } catch (e) {
    const msg = e instanceof TypeError ? 'Space bilan bog‘lanib bo‘lmadi. Manzilni va internetni tekshiring.' : e.message;
    status(msg, 'err');
  } finally {
    clearInterval(tick);
    btn.disabled = false;
  }
}

/* ================= boshlash ================= */
const spaceIn = $('#space');
spaceIn.value = store.get('ummon-matn-space', DEFAULT_SPACE);
spaceIn.addEventListener('change', () => store.set('ummon-matn-space', spaceIn.value.trim()));

const bindOut = (id, fmt) => {
  const el = $(`#${id}`);
  const out = $(`#${id}Out`);
  const sync = () => { out.textContent = fmt(el.value); };
  el.addEventListener('input', sync);
  sync();
};
bindOut('rate', (v) => `${v > 0 ? '+' : ''}${v}%`);
bindOut('pitch', (v) => `${v > 0 ? '+' : ''}${v}`);
bindOut('protect', (v) => Number(v).toFixed(2));

// Madina (ayol) asosiy ovozi erkak modeliga o'tganda ohangni pastlatish kerak.
$('#baseVoice').addEventListener('change', (e) => {
  $('#pitch').value = e.target.value.startsWith('Madina') ? -12 : 0;
  $('#pitch').dispatchEvent(new Event('input'));
});

const count = () => { $('#count').textContent = `${$('#text').value.length}/1500`; };
$('#text').addEventListener('input', count);
count();

$('#goBtn').addEventListener('click', synthesize);
