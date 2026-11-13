import { staticFile } from "remotion";

// Fonts are declared with plain @font-face (no delayRender): if they are installed
// on the machine (local()) Chrome uses them instantly, otherwise it loads the files
// from public/fonts. Installing them locally makes long renders reliable.
export const fontCss = `
@font-face { font-family: "Cinzel"; src: local("Cinzel"), url(${staticFile("fonts/Cinzel.ttf")}); font-weight: 100 900; }
@font-face { font-family: "Playfair Display"; src: local("Playfair Display"), url(${staticFile("fonts/Playfair.ttf")}); font-weight: 100 900; }
@font-face { font-family: "Special Elite"; src: local("Special Elite"), url(${staticFile("fonts/SpecialElite.ttf")}); }
`;

export const TITLE = "Cinzel, serif";
export const SERIF = "'Playfair Display', serif";
export const TYPE = "'Special Elite', 'Courier New', monospace";
export const GOLD = "#d9b26f";
