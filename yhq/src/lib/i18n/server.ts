import "server-only";
import { cookies } from "next/headers";
import { LANG_COOKIE } from "../session-constants";
import { isLocale, makeT } from "./core";
import type { Locale } from "./dict";

export async function getLocale(): Promise<Locale> {
  const jar = await cookies();
  const v = jar.get(LANG_COOKIE)?.value;
  return isLocale(v) ? v : "uz";
}

export async function getT() {
  const locale = await getLocale();
  return { locale, t: makeT(locale) };
}
