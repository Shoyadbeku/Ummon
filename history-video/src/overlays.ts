// Per-scene motion-graphic overlays (keyed by storyboard scene number).
// `at` = seconds after the scene starts, `dur` = seconds on screen.
export type Overlay =
  | { kind: "date"; text: string; place?: string; at?: number; dur?: number }
  | { kind: "lower"; name: string; role: string; at?: number; dur?: number }
  | { kind: "stat"; value: number; suffix?: string; label: string; at?: number; dur?: number }
  | { kind: "chapter"; number: string; title: string; at?: number; dur?: number }
  | { kind: "title"; title: string; subtitle: string; at?: number; dur?: number }
  | { kind: "burn"; at?: number; dur?: number };

export const CHANNEL = "QIZIQ-A?";

export const overlays: Record<number, Overlay[]> = {
  1: [{ kind: "date", text: "1872-yil 4-dekabr", place: "Atlantika okeani · Azor orollari", at: 1.2, dur: 6.5 }],
  8: [{ kind: "burn", dur: 1.2 }],
  10: [{ kind: "burn", dur: 1.5 }, { kind: "title", title: "MERI SELEST", subtitle: "150 yillik dengiz siri", at: 0.6, dur: 8 }],
  11: [{ kind: "burn" }, { kind: "chapter", number: "I", title: "Nyu-York, 1872", dur: 3.6 }, { kind: "date", text: "1872-yil noyabr", place: "Nyu-York porti", at: 4, dur: 5.5 }],
  12: [{ kind: "stat", value: 1700, suffix: "+", label: "bochka sanoat spirti", at: 1.5, dur: 6.5 }],
  13: [{ kind: "lower", name: "Bendjamin Briggs", role: "Kema kapitani · 37 yosh", at: 0.8, dur: 6.5 }],
  14: [{ kind: "lower", name: "Sara va Sofiya Briggs", role: "Kapitanning rafiqasi va 2 yoshli qizi", at: 2.5, dur: 5.5 }],
  15: [{ kind: "stat", value: 10, label: "kishi bortda", at: 5, dur: 4.5 }],
  17: [{ kind: "date", text: "7-noyabr, 1872", place: "Nyu-York → Genuya", at: 0.3, dur: 6 }],
  18: [{ kind: "lower", name: "Devid Morxaus", role: "'Dei Gratsiya' kapitani", at: 6, dur: 7 }],
  19: [{ kind: "burn" }, { kind: "chapter", number: "II", title: "Topilma", dur: 3.6 }, { kind: "date", text: "4-dekabr, 1872", place: "Ochiq okean", at: 4, dur: 5 }],
  21: [{ kind: "stat", value: 6, label: "oylik oziq-ovqat", at: 0.5, dur: 4.5 }],
  25: [{ kind: "burn", dur: 1.2 }],
  28: [{ kind: "date", text: "25-noyabr · 08:00", place: "Kema jurnalidagi oxirgi yozuv", at: 0.5, dur: 5.5 }],
  30: [{ kind: "stat", value: 10, label: "kun boshqaruvsiz", at: 7, dur: 6 }],
  32: [{ kind: "burn" }, { kind: "chapter", number: "III", title: "Tergov", dur: 3.6 }],
  33: [{ kind: "lower", name: "Frederik Solli-Flad", role: "Gibraltar bosh prokurori", at: 0.8, dur: 7 }],
  38: [{ kind: "burn" }, { kind: "chapter", number: "IV", title: "Afsona", dur: 3.6 }, { kind: "date", text: "1884-yil", at: 4, dur: 4.5 }, { kind: "lower", name: "Artur Konan Doyl", role: "Yozuvchi", at: 9, dur: 7 }],
  43: [{ kind: "burn" }, { kind: "chapter", number: "V", title: "Haqiqat izlab", dur: 3.6 }],
  44: [{ kind: "stat", value: 9, label: "bo'sh bochka", at: 5, dur: 6 }],
  45: [{ kind: "burn", at: 1.5, dur: 1.4 }],
  46: [{ kind: "date", text: "2006-yil", place: "London universiteti", at: 0.3, dur: 5.5 }],
  50: [{ kind: "burn", dur: 1.2 }],
  52: [{ kind: "burn" }, { kind: "chapter", number: "VI", title: "So'nggi sahifa", dur: 3.6 }, { kind: "date", text: "1885-yil", place: "Gaiti qirg'oqlari", at: 4, dur: 5 }],
  57: [{ kind: "burn", dur: 1.5 }],
};
