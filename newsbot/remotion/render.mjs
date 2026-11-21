// Usage: node render.mjs <episodeDir>
// <episodeDir> must contain render_props.json and the assets it references (audio, media/).
import path from 'node:path';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const epDir = path.resolve(process.argv[2]);
const props = JSON.parse(fs.readFileSync(path.join(epDir, 'render_props.json'), 'utf8'));
const out = path.join(epDir, 'final.mp4');

// Use the preinstalled Chromium when present (no extra download needed).
const preinstalled = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const browserExecutable = process.env.REMOTION_CHROME || (fs.existsSync(preinstalled) ? preinstalled : null);

const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.ts'), publicDir: epDir});
const composition = await selectComposition({serveUrl, id: 'NewsVideo', inputProps: props, browserExecutable});
let last = -1;
await renderMedia({
	composition,
	serveUrl,
	codec: 'h264',
	crf: 20,
	audioCodec: 'aac',
	outputLocation: out,
	inputProps: props,
	browserExecutable,
	concurrency: Number(process.env.RENDER_CONCURRENCY || 3),
	chromiumOptions: {gl: 'swangle'},
	onProgress: ({progress}) => {
		const pct = Math.floor(progress * 100);
		if (pct % 10 === 0 && pct !== last) {
			last = pct;
			console.log(`render ${pct}%`);
		}
	},
});
console.log('OK', out);
