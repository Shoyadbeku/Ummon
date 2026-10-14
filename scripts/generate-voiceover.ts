/**
 * Gemini TTS orqali har bir sahna uchun ovoz (voiceover) yaratish.
 *
 *   GEMINI_API_KEY=... npm run voiceover               # yetishmayotganlarini yaratadi
 *   npm run voiceover -- --force                      # hammasini qayta yaratadi
 *   npm run voiceover -- --only=04-stop               # bitta sahna
 *
 * Natija: public/voiceover/<sahna-id>.wav
 * Video taymlayni (calculateMetadata) bu fayllarning davomiyligini o'qiydi va
 * sahnalar, kinetik matn hamda o'tishlarni avtomatik moslashtiradi.
 *
 * Sozlamalar (.env yoki muhit o'zgaruvchilari):
 *   GEMINI_API_KEY      — majburiy
 *   GEMINI_TTS_MODEL    — standart: gemini-2.5-flash-preview-tts
 *   GEMINI_TTS_VOICE    — standart: Puck (boshqalar: Kore, Charon, Fenrir, Aoede, ...)
 */
import {existsSync, mkdirSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {narrationOf, SCENES} from '../src/data/script';

try {
  process.loadEnvFile();
} catch {
  // .env bo'lmasa — muhit o'zgaruvchilaridan foydalanamiz
}

const API_KEY = process.env.GEMINI_API_KEY;
const MODEL = process.env.GEMINI_TTS_MODEL ?? 'gemini-2.5-flash-preview-tts';
const VOICE = process.env.GEMINI_TTS_VOICE ?? 'Puck';
const OUT_DIR = path.resolve('public/voiceover');

const args = process.argv.slice(2);
const force = args.includes('--force');
const only = args.find((a) => a.startsWith('--only='))?.split('=')[1];

if (!API_KEY) {
  console.error('❌ GEMINI_API_KEY topilmadi. .env fayliga GEMINI_API_KEY=... yozing.');
  process.exit(1);
}

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
  const prompt = `${style}. Speak in natural Uzbek (O'zbek tili), clear pronunciation:\n${text}`;
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
    const wav = await synthesize(text, scene.ttsStyle);
    writeFileSync(out, wav);
    console.log('✓');
  } catch (err) {
    console.log('✗');
    console.error(`   ${(err as Error).message}`);
  }
}

console.log('\nTayyor. Taymlaynni tekshirish: npm run assets');
