/**
 * Gemini TTS orqali har bir sahna uchun ovoz (voiceover) yaratish.
 *
 *   GEMINI_API_KEY=... npm run voiceover               # yetishmayotganlarini yaratadi
 *   npm run voiceover -- --force                      # hammasini qayta yaratadi
 *   npm run voiceover -- --only=04-stop               # bitta sahna
 *
 * Natija: public/voiceover/<sahna-id>.wav — ffmpeg bilan "jarangdor" qilib ishlangan:
 * boshi/oxiridagi jimlik kesiladi, past shovqin olib tashlanadi, 3–5 kHz "presence"
 * kuchaytiriladi, kompressor + -14 LUFS balandlik normalizatsiyasi, 48 kHz.
 * Video taymlayni (calculateMetadata) bu fayllarning davomiyligini o'qiydi va
 * sahnalar, kinetik matn hamda o'tishlarni avtomatik moslashtiradi.
 *
 * Sozlamalar (.env yoki muhit o'zgaruvchilari):
 *   GEMINI_API_KEY      — majburiy
 *   GEMINI_TTS_MODEL    — standart: gemini-2.5-flash-preview-tts
 *   GEMINI_TTS_VOICE    — standart: Puck (jarangdor, quvnoq). Boshqalar: Zephyr (yorqin),
 *                         Fenrir (hayajonli), Charon (ma'lumotli), Kore (qat'iy), Sadachbia (jonli)
 *   --voice=Zephyr      — bir martalik ovozni tanlash
 *   --raw               — ffmpeg ishlovisiz xom WAV
 */
import {execFileSync} from 'node:child_process';
import {existsSync, mkdirSync, renameSync, rmSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {narrationOf, SCENES} from '../src/data/script';

try {
  process.loadEnvFile();
} catch {
  // .env bo'lmasa — muhit o'zgaruvchilaridan foydalanamiz
}

const API_KEY = process.env.GEMINI_API_KEY;
const MODEL = process.env.GEMINI_TTS_MODEL ?? 'gemini-2.5-flash-preview-tts';
const args = process.argv.slice(2);
const VOICE = args.find((a) => a.startsWith('--voice='))?.split('=')[1] ?? process.env.GEMINI_TTS_VOICE ?? 'Puck';
const RAW = args.includes('--raw');
const OUT_DIR = path.resolve('public/voiceover');

const force = args.includes('--force');
const only = args.find((a) => a.startsWith('--only='))?.split('=')[1];

if (!API_KEY) {
  console.error('❌ GEMINI_API_KEY topilmadi. .env fayliga GEMINI_API_KEY=... yozing.');
  process.exit(1);
}

/** "Jarangdor" ovoz uchun ffmpeg mastering zanjiri */
const MASTER_FILTER = [
  'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05',
  'areverse',
  'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.12',
  'areverse',
  'highpass=f=80',
  'equalizer=f=250:t=q:w=1.2:g=-2',
  'equalizer=f=3500:t=q:w=1.0:g=3.5',
  'equalizer=f=10000:t=h:w=0.7:g=2',
  'acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=2',
  'loudnorm=I=-14:TP=-1.5:LRA=7',
].join(',');

const master = (file: string) => {
  const tmp = file.replace(/\.wav$/, '.raw.wav');
  renameSync(file, tmp);
  try {
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', tmp, '-af', MASTER_FILTER, '-ar', '48000', '-ac', '1', file]);
    rmSync(tmp);
  } catch (err) {
    renameSync(tmp, file);
    console.warn(`   ffmpeg ishlovi o'tkazib yuborildi: ${(err as Error).message}`);
  }
};

/** Gemini TTS 16-bit PCM qaytaradi — unga WAV sarlavhasini qo'shamiz */
const pcmToWav = (pcm: Buffer, sampleRate: number, channels = 1, bits = 16) => {
  const header = Buffer.alloc(44);
  const byteRate = (sampleRate * channels * bits) / 8;
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + pcm.length, 4);
  header.write('WAVE', 8);
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(channels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE((channels * bits) / 8, 32);
  header.writeUInt16LE(bits, 34);
  header.write('data', 36);
  header.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([header, pcm]);
};

type GeminiResponse = {
  candidates?: {content?: {parts?: {inlineData?: {mimeType: string; data: string}}[]}}[];
  error?: {message: string};
};

const synthesize = async (text: string, style: string) => {
  const prompt =
    `Voice direction: ${style}. Bright, resonant and clear voice with crisp diction, confident projection, ` +
    `energetic social-media narrator, natural Uzbek (O'zbek tili) pronunciation, no long pauses.\n` +
    `Read exactly this Uzbek text:\n${text}`;
  const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'x-goog-api-key': API_KEY},
    body: JSON.stringify({
      contents: [{parts: [{text: prompt}]}],
      generationConfig: {
        responseModalities: ['AUDIO'],
        speechConfig: {voiceConfig: {prebuiltVoiceConfig: {voiceName: VOICE}}},
      },
    }),
  });
  const json = (await res.json()) as GeminiResponse;
  if (!res.ok) throw new Error(json.error?.message ?? `HTTP ${res.status}`);
  const inline = json.candidates?.[0]?.content?.parts?.find((p) => p.inlineData)?.inlineData;
  if (!inline) throw new Error('Javobda audio topilmadi');
  const rate = Number(/rate=(\d+)/.exec(inline.mimeType)?.[1] ?? 24000);
  return pcmToWav(Buffer.from(inline.data, 'base64'), rate);
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Bepul tarif limiti (daqiqasiga bir necha so'rov) — kutib qayta urinadi */
const synthesizeWithRetry = async (text: string, style: string, attempts = 6) => {
  for (let i = 1; ; i++) {
    try {
      return await synthesize(text, style);
    } catch (err) {
      const msg = (err as Error).message;
      const quota = /quota|rate|429|RESOURCE_EXHAUSTED/i.test(msg);
      if (!quota || i >= attempts || /per day|PerDay/i.test(msg)) throw err;
      const wait = Math.max(20, Number(/retry in ([\d.]+)s/i.exec(msg)?.[1] ?? 0) + 2);
      process.stdout.write(`(limit, ${Math.round(wait)}s kutilmoqda) `);
      await sleep(wait * 1000);
    }
  }
};

mkdirSync(OUT_DIR, {recursive: true});

for (const scene of SCENES) {
  if (only && scene.id !== only) continue;
  const out = path.join(OUT_DIR, `${scene.id}.wav`);
  if (existsSync(out) && !force) {
    console.log(`⏭  ${scene.id} — mavjud (qayta yaratish uchun --force)`);
    continue;
  }
  const text = narrationOf(scene);
  process.stdout.write(`🎙  ${scene.id}: "${text}" … `);
  try {
    const wav = await synthesizeWithRetry(text, scene.ttsStyle);
    writeFileSync(out, wav);
    if (!RAW) master(out);
    console.log('✓');
  } catch (err) {
    console.log('✗');
    console.error(`   ${(err as Error).message}`);
  }
}

console.log(`\nTayyor (ovoz: ${VOICE}). Taymlaynni tekshirish: npm run assets`);
