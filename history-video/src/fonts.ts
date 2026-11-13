import { continueRender, delayRender } from "remotion";
import { Cinzel, Playfair, SpecialElite } from "./fontData";

const handle = delayRender("fonts", { timeoutInMilliseconds: 60000 });
Promise.all(
  ([["Cinzel", Cinzel], ["Playfair", Playfair], ["SpecialElite", SpecialElite]] as const).map(([name, url]) => {
    const f = new FontFace(name, `url(${url})`, { weight: "100 900" });
    return f.load().then(() => document.fonts.add(f));
  }),
)
  .catch((e) => console.error("font load failed", e))
  .finally(() => continueRender(handle));

export const TITLE = "Cinzel, serif";
export const SERIF = "Playfair, serif";
export const TYPE = "SpecialElite, 'Courier New', monospace";
export const GOLD = "#d9b26f";
