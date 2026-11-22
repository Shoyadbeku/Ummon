// PWA ikonkalarini SVG dan PNG ga generatsiya qiladi: npm run icons
import sharp from "sharp";
import { mkdirSync } from "node:fs";

const svg = (pad: number) => Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="${pad ? 0 : 110}" fill="#0b1f4b"/>
  <g transform="translate(${pad} ${pad}) scale(${(512 - pad * 2) / 512})">
    <path d="M256 70 L452 410 Q458 424 442 424 H70 Q54 424 60 410 Z" fill="#d32027"/>
    <path d="M256 135 L395 380 H117 Z" fill="#fff"/>
    <path d="M196 330 L206 290 Q211 272 230 272 H282 Q301 272 306 290 L316 330 V355 H196 Z" fill="#0b1f4b"/>
    <circle cx="222" cy="358" r="16" fill="#0b1f4b"/><circle cx="290" cy="358" r="16" fill="#0b1f4b"/>
  </g>
</svg>`);

async function main() {
mkdirSync("public/icons", { recursive: true });
await sharp(svg(0)).resize(192, 192).png().toFile("public/icons/icon-192.png");
await sharp(svg(0)).resize(512, 512).png().toFile("public/icons/icon-512.png");
await sharp(svg(0)).resize(180, 180).png().toFile("public/icons/apple-touch-icon.png");
await sharp(svg(60)).resize(512, 512).png().toFile("public/icons/icon-maskable-512.png");
await sharp(svg(0)).resize(48, 48).png().toFile("public/favicon.png");
console.log("Ikonkalar tayyor");
}
main();
