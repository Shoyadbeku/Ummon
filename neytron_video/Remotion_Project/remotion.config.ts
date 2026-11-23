import {Config} from '@remotion/cli/config';
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setConcurrency(4);
Config.setOverwriteOutput(true);
// Use a locally installed headless Chromium when present (otherwise Remotion downloads its own)
import fs from 'fs';
const localChrome = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
if (fs.existsSync(localChrome)) Config.setBrowserExecutable(localChrome);
