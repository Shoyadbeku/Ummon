import { requireAdmin } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { getSettings, saveSettings, settingsSchema } from "@/lib/settings";
import { audit } from "@/lib/admin/questions";

export const GET = handler(async () => {
  await requireAdmin();
  return json(await getSettings());
});

export const PUT = handler(async (req: Request) => {
  const admin = await requireAdmin();
  const s = settingsSchema.parse(await readJson(req));
  await saveSettings(s);
  await audit(admin.id, "update", "settings", undefined, s);
  return json(s);
});
