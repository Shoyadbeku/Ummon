import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const root = process.argv[2]; const times = process.argv[3].split(',').map(Number); const out = process.argv[4];
const serveUrl = await bundle({entryPoint: path.join(root, 'src/index.ts'), publicDir: path.join(root, 'public')});
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const composition = await selectComposition({serveUrl, id: 'Main', browserExecutable});
for (const t of times) {
  await renderStill({serveUrl, composition, frame: Math.round(t * 30), output: `${out}/s_${t.toFixed(2).padStart(7, '0')}.jpg`, imageFormat: 'jpeg', scale: 0.3, browserExecutable, timeoutInMilliseconds: 120000});
}
console.log('done', times.length);
