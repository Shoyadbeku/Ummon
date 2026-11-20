// Kalit kadrlarni tez tekshirish uchun still render
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import path from 'node:path';
const frames = process.argv.slice(3).map(Number);
const outDir = process.argv[2];
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const browser = await openBrowser('chrome', {browserExecutable: process.env.CHROME_BIN, chromiumOptions: {gl: 'swangle'}});
const composition = await selectComposition({serveUrl, id: 'Main', puppeteerInstance: browser});
for (const frame of frames) {
	await renderStill({composition, serveUrl, frame, output: `${outDir}/f${String(frame).padStart(4, '0')}.jpg`, imageFormat: 'jpeg', jpegQuality: 80, puppeteerInstance: browser, scale: 0.5});
	console.log('ok', frame);
}
await browser.close({silent: true});
