import { DICTS, interpolate, LOCALES, type DictKey, type Locale } from "./dict";
import { toCyrillic } from "../translit";

export function isLocale(v: unknown): v is Locale {
  return typeof v === "string" && (LOCALES as readonly string[]).includes(v);
}

export function makeT(locale: Locale) {
  const base = locale === "ru" ? DICTS.ru : DICTS.uz;
  return (key: DictKey, vars?: Record<string, string | number>) => {
    const s = interpolate(base[key] ?? DICTS.uz[key] ?? key, vars);
    return locale === "uzc" ? toCyrillic(s) : s;
  };
}

/** Kontent (savol matni) uchun: kirillda transliteratsiya, rusda — tarjima bo'lsa tarjima */
export function contentText(locale: Locale, uzText: string, ruText?: string | null) {
  if (locale === "uzc") return toCyrillic(uzText);
  if (locale === "ru" && ruText) return ruText;
  return uzText;
}

export function htmlLang(locale: Locale) {
  return locale === "uzc" ? "uz-Cyrl" : locale === "ru" ? "ru" : "uz";
}

export function intlLocale(locale: Locale) {
  return locale === "ru" ? "ru-RU" : "uz-UZ";
}

export type TFn = ReturnType<typeof makeT>;
