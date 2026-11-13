import { continueRender, delayRender, staticFile } from "remotion";

const fonts: [string, string][] = [
  ["Cinzel", "fonts/Cinzel.ttf"],
  ["Playfair", "fonts/Playfair.ttf"],
  ["SpecialElite", "fonts/SpecialElite.ttf"],
];

const handle = delayRender("fonts");
Promise.all(
  fonts.map(([name, file]) => {
    const f = new FontFace(name, `url(${staticFile(file)})`, { weight: "100 900" });
    return f.load().then(() => document.fonts.add(f));
  }),
).then(() => continueRender(handle));

export const TITLE = "Cinzel, serif";
export const SERIF = "Playfair, serif";
export const TYPE = "SpecialElite, 'Courier New', monospace";
export const GOLD = "#d9b26f";
