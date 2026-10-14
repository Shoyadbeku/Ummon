import {Config} from '@remotion/cli/config';

// Yuqori sifatli yakuniy render: 1080p, 60fps, H.264 (MP4)
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
Config.setCrf(16);
Config.setOverwriteOutput(true);
Config.setChromiumOpenGlRenderer('angle');
