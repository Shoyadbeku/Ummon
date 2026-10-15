// Vite dev serverini ishga tushiradi, render.html ni headless Chromium'da
// ochadi va Motion Canvas render tugaguncha kutadi. Natija: output/*.mp4
import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
import {chromium} from 'playwright-core';

const PORT = 9123;
const server = spawn(
  process.execPath,
  ['node_modules/vite/bin/vite.js', '--port', String(PORT), '--strictPort'],
  {stdio: ['ignore', 'pipe', 'inherit']},
);
process.on('exit', () => server.kill());
await new Promise((res, rej) => {
  server.stdout.on('data', d => String(d).includes('Local') && res());
  server.on('exit', c => rej(new Error('vite exited ' + c)));
});

const executablePath = [
  process.env.CHROMIUM_PATH,
  '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
].find(p => p && existsSync(p));
const browser = await chromium.launch({
  executablePath, // topilmasa playwright o'zining brauzerini qidiradi
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--autoplay-policy=no-user-gesture-required'],
});
const page = await browser.newPage();
page.on('console', m => m.type() === 'error' && console.error('[page]', m.text()));
page.on('pageerror', e => console.error('[page]', e));
await page.goto(`http://localhost:${PORT}/render.html`);

let last = -1;
for (;;) {
  await new Promise(r => setTimeout(r, 2000));
  const {status, frame} = await page.evaluate(() => ({
    status: window.renderStatus, frame: window.renderFrame,
  }));
  if (frame !== last) process.stdout.write(`\rframe ${frame}   `), (last = frame);
  if (status && status !== 'working') {
    console.log(`\nrender: ${status}`);
    await browser.close();
    server.kill();
    process.exit(status === 'Success' ? 0 : 1);
  }
}
