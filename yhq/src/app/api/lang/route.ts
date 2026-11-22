import { cookies } from "next/headers";
import { z } from "zod";
import { handler, json, readJson } from "@/lib/api";
import { LANG_COOKIE } from "@/lib/session-constants";

export const POST = handler(async (req: Request) => {
  const { locale } = z.object({ locale: z.enum(["uz", "uzc", "ru"]) }).parse(await readJson(req));
  const jar = await cookies();
  jar.set(LANG_COOKIE, locale, { path: "/", sameSite: "lax", maxAge: 60 * 60 * 24 * 365 });
  return json({ ok: true });
});
