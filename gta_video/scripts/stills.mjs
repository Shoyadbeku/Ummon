import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const times = process.argv.slice(3).map(Number);
const outDir = process.argv[2];
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const comp = await selectComposition({serveUrl, id: process.env.COMP || 'Main'});
for (const t of times) {
  const frame = Math.round(t * 30);
  await renderStill({serveUrl, composition: comp, frame, output: `${outDir}/s_${String(t).padStart(6, '0')}.jpg`, imageFormat: 'jpeg', jpegQuality: 80, scale: 0.4});
  console.log('ok', t);
}
