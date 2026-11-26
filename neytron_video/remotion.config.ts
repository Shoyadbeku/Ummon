import {Config} from '@remotion/cli/config';
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setConcurrency(3);
Config.setCodec('h264');
Config.setCrf(18);
Config.setBrowserExecutable('/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell');
