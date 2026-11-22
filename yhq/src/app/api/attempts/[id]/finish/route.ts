import { handler, json } from "@/lib/api";
import { finishAttempt } from "@/lib/attempts";

export const POST = handler(async (_req: Request, ctx: { params: Promise<{ id: string }> }) => {
  const { id } = await ctx.params;
  const a = await finishAttempt(id);
  return json({ id: a.id, correct: a.correctCount, wrong: a.wrongCount, total: a.total });
});
