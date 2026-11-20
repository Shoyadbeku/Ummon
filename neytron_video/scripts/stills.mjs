// Render a list of frames as stills with one bundle: node scripts/stills.mjs 23 163 ...
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const B = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'Main', browserExecutable: B});
for (const fr of process.argv.slice(2)) {
  await renderStill({composition, serveUrl, frame: Number(fr), output: `out/stills/s_${fr}.jpg`, imageFormat: 'jpeg', scale: 0.4, browserExecutable: B});
  console.log('ok', fr);
}
