import { handler, json, readJson } from "@/lib/api";
import { startAttemptSchema } from "@/lib/validation";
import { startAttempt } from "@/lib/attempts";

export const POST = handler(async (req: Request) => {
  const input = startAttemptSchema.parse(await readJson(req));
  const attempt = await startAttempt(input);
  return json({ id: attempt.id }, 201);
});
