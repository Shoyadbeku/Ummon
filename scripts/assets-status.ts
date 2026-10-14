/**
 * Aktivlar holati: qaysi sahnaga ovoz / AI rasm qo'yilgan, qaysi biri yetishmaydi
 * va video taymlayni qanday bo'lishini ko'rsatadi.
 *
 *   npm run assets
 */
import {execFileSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import path from 'node:path';
import {narrationOf, SCENES} from '../src/data/script';
import {estimateSpeechSeconds, FPS, LEAD_IN_SEC, TAIL_SEC, TRANSITION_FRAMES} from '../src/lib/timeline';

const PUBLIC = path.resolve('public');
const find = (base: string, exts: string[]) =>
  exts.map((e) => `${base}.${e}`).find((f) => existsSync(path.join(PUBLIC, f))) ?? null;

const probe = (file: string): number | null => {
  try {
    const out = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file]);
    return parseFloat(out.toString().trim());
  } catch {
    return null;
  }
};

let total = 0;
console.log('\nSahna            Ovoz                         Rasm                      Nutq(s)  Sahna(s)');
console.log('─'.repeat(98));
SCENES.forEach((scene, i) => {
  const audio = find(`voiceover/${scene.id}`, ['wav', 'mp3', 'm4a', 'aac', 'ogg']);
  const image = find(`images/${scene.id}`, ['png', 'jpg', 'jpeg', 'webp']);
  const speech = (audio && probe(path.join(PUBLIC, audio))) || estimateSpeechSeconds(scene);
  const natural = Math.round(LEAD_IN_SEC * FPS) + Math.round(speech * FPS) + Math.round(TAIL_SEC * FPS) + TRANSITION_FRAMES;
  const dur = Math.max(natural, Math.round(scene.minSeconds * FPS) + TRANSITION_FRAMES);
  total += dur - (i > 0 ? TRANSITION_FRAMES : 0);
  console.log(
    `${scene.id.padEnd(16)} ${(audio ?? '— (taxminiy)').padEnd(28)} ${(image ?? '— (vektor)').padEnd(25)} ${speech
      .toFixed(2)
      .padStart(7)}  ${(dur / FPS).toFixed(2).padStart(7)}`,
  );
});
console.log('─'.repeat(98));
console.log(`Jami: ${total} kadr = ${(total / FPS).toFixed(2)} s @ ${FPS}fps\n`);

if (process.argv.includes('--prompts')) {
  for (const s of SCENES) {
    console.log(`## ${s.id}\nMatn: ${narrationOf(s)}\nPrompt: ${s.imagePrompt}\n`);
  }
}
