import { loadFont } from "@remotion/fonts";

// Fontlar @fontsource paketlaridan lokal yuklanadi: render internetsiz ham
// ishlaydi. O'zbek lotin harflari (o‘, g‘, ʼ) uchun latin + latin-ext.
const LATIN =
  "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD";
const LATIN_EXT =
  "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF";

type Face = { family: string; pkg: string; file: string; weight: string; style: "normal" | "italic" };

// eslint-disable-next-line @typescript-eslint/no-require-imports
const asset = (pkg: string, name: string): string => require(`@fontsource/${pkg}/files/${name}`);

const faces: Face[] = [
  { family: "Cinzel", pkg: "cinzel", file: "cinzel", weight: "400", style: "normal" },
  { family: "Cinzel", pkg: "cinzel", file: "cinzel", weight: "700", style: "normal" },
  { family: "Cormorant Garamond", pkg: "cormorant-garamond", file: "cormorant-garamond", weight: "500", style: "normal" },
  { family: "Cormorant Garamond", pkg: "cormorant-garamond", file: "cormorant-garamond", weight: "600", style: "normal" },
  { family: "Cormorant Garamond", pkg: "cormorant-garamond", file: "cormorant-garamond", weight: "700", style: "normal" },
  { family: "Cormorant Garamond", pkg: "cormorant-garamond", file: "cormorant-garamond", weight: "500", style: "italic" },
  { family: "Inter", pkg: "inter", file: "inter", weight: "400", style: "normal" },
  { family: "Inter", pkg: "inter", file: "inter", weight: "600", style: "normal" },
];

for (const f of faces) {
  for (const [subset, range] of [
    ["latin", LATIN],
    ["latin-ext", LATIN_EXT],
  ] as const) {
    loadFont({
      family: f.family,
      url: asset(f.pkg, `${f.file}-${subset}-${f.weight}-${f.style}.woff2`),
      weight: f.weight,
      style: f.style,
      unicodeRange: range,
    });
  }
}

export const fonts = {
  display: "Cinzel, serif",
  serif: "'Cormorant Garamond', Georgia, serif",
  serifItalic: "'Cormorant Garamond', Georgia, serif",
  sans: "Inter, Arial, sans-serif",
};
