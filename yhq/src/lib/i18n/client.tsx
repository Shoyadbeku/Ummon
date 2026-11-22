"use client";
import { createContext, useContext, useMemo } from "react";
import { makeT, contentText, type TFn } from "./core";
import type { Locale } from "./dict";

type Ctx = { locale: Locale; t: TFn; c: (uz: string, ru?: string | null) => string };
const I18nContext = createContext<Ctx | null>(null);

export function I18nProvider({ locale, children }: { locale: Locale; children: React.ReactNode }) {
  const value = useMemo<Ctx>(() => ({ locale, t: makeT(locale), c: (uz, ru) => contentText(locale, uz, ru) }), [locale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("I18nProvider topilmadi");
  return ctx;
}
