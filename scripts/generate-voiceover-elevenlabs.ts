/**
 * ElevenLabs orqali har bir sahna uchun ovoz + so'zlar vaqt belgilari (alignment).
 *
 *   npm run voiceover:eleven                  # yetishmayotganlarini yaratadi
 *   npm run voiceover:eleven -- --force       # hammasini qayta yaratadi
 *   npm run voiceover:eleven -- --only=04-stop
 *
 * Natija:
 *   public/voiceover/<sahna-id>.wav   — "jarangdor" qilib ishlangan ovoz (EQ, kompressor, -14 LUFS)
 *   public/voiceover/<sahna-id>.json  — har bir matn bo'lagi (segment) qachon aytilishi (soniya)
 *
 * Taymlayn JSON'dagi aniq vaqtlarni o'qiydi — kinetik matn ovozga kadrma-kadr sinxron chiqadi.
 *
 * Sozlamalar (.env):
 *   ELEVENLABS_API_KEY   — majburiy
 *   ELEVENLABS_VOICE_ID  — majburiy
 *   ELEVENLABS_MODEL     — standart: eleven_v3 (o'zbek tilini qo'llaydi)
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

const API_KEY = process.env.ELEVENLABS_API_KEY;
const VOICE_ID = process.env.ELEVENLABS_VOICE_ID;
const MODEL = process.env.ELEVENLABS_MODEL ?? 'eleven_v3';
const OUT_DIR = path.resolve('public/voiceover');

const args = process.argv.slice(2);
const force = args.includes('--force');
const only = args.find((a) => a.startsWith('--only='))?.split('=')[1];

if (!API_KEY || !VOICE_ID) {
  console.error('❌ .env faylida ELEVENLABS_API_KEY va ELEVENLABS_VOICE_ID bo‘lishi kerak.');
  process.exit(1);
}

/**
 * Jarangdor ovoz uchun mastering. Boshidagi jimlik KESILMAYDI — aks holda
 * alignment vaqtlari siljib ketadi; faqat oxiridagi jimlik olib tashlanadi.
 */
const MASTER_FILTER = [
  'areverse',
  'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15',
  'areverse',
  'highpass=f=80',
  'equalizer=f=250:t=q:w=1.2:g=-2',
  'equalizer=f=3500:t=q:w=1.0:g=3',
  'equalizer=f=10000:t=h:w=0.7:g=2',
  'acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=2',
  'loudnorm=I=-14:TP=-1.5:LRA=7',
].join(',');

type Alignment = {
  characters: string[];
  character_start_times_seconds: number[];
  character_end_times_seconds: number[];
};

type TtsResponse = {
  audio_base64: string;
  alignment?: Alignment;
  normalized_alignment?: Alignment;
  detail?: {message?: string} | string;
};

const synthesize = async (text: string) => {
  const url = `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}/with-timestamps?output_format=mp3_44100_128`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'xi-api-key': API_KEY},
    body: JSON.stringify({
      text,
      model_id: MODEL,
      language_code: 'uz',
      voice_settings: {stability: 0.5, similarity_boost: 0.8, style: 0.45, use_speaker_boost: true},
    }),
  });
  const json = (await res.json()) as TtsResponse;
  if (!res.ok) {
    const d = json.detail;
    throw new Error(typeof d === 'string' ? d : (d?.message ?? `HTTP ${res.status}`));
  }
  return json;
};

/** Har bir segment uchun [boshlanish, tugash] (soniya) — matndagi belgilar o'rni bo'yicha */
const segmentTimes = (segments: string[], al: Alignment): [number, number][] => {
  const text = al.characters.join('');
  const out: [number, number][] = [];
  let cursor = 0;
  for (const seg of segments) {
    const idx = text.indexOf(seg, cursor);
    const startIdx = idx >= 0 ? idx : cursor;
    const endIdx = Math.min(al.characters.length - 1, startIdx + seg.length - 1);
    out.push([al.character_start_times_seconds[startIdx] ?? 0, al.character_end_times_seconds[endIdx] ?? 0]);
    cursor = endIdx + 1;
  }
  return out;
};

mkdirSync(OUT_DIR, {recursive: true});

for (const scene of SCENES) {
  if (only && scene.id !== only) continue;
  const wav = path.join(OUT_DIR, `${scene.id}.wav`);
  const json = path.join(OUT_DIR, `${scene.id}.json`);
  if (existsSync(wav) && existsSync(json) && !force) {
    console.log(`⏭  ${scene.id} — mavjud (qayta yaratish uchun --force)`);
    continue;
  }
  const text = narrationOf(scene);
  process.stdout.write(`🎙  ${scene.id}: "${text}" … `);
  try {
    const res = await synthesize(text);
    const mp3 = path.join(OUT_DIR, `${scene.id}.el.mp3`);
    writeFileSync(mp3, Buffer.from(res.audio_base64, 'base64'));
    try {
      execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', mp3, '-af', MASTER_FILTER, '-ar', '48000', '-ac', '1', wav]);
      rmSync(mp3);
    } catch {
      renameSync(mp3, path.join(OUT_DIR, `${scene.id}.mp3`));
      console.warn('(ffmpeg topilmadi — xom mp3 saqlandi)');
    }
    const al = res.alignment ?? res.normalized_alignment;
    if (al) {
      const times = segmentTimes(
        scene.segments.map((s) => s.text),
        al,
      );
      writeFileSync(json, JSON.stringify({model: MODEL, voice: VOICE_ID, segments: times}, null, 2));
    }
    console.log('✓');
  } catch (err) {
    console.log('✗');
    console.error(`   ${(err as Error).message}`);
  }
}

console.log('\nTayyor. Taymlaynni tekshirish: npm run assets, keyin: npm run render');
