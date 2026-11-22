import { handler, json, readJson } from "@/lib/api";
import { revealSchema } from "@/lib/validation";
import { revealAnswer } from "@/lib/attempts";

export const POST = handler(async (req: Request, ctx: { params: Promise<{ id: string }> }) => {
  const { id } = await ctx.params;
  const { questionId } = revealSchema.parse(await readJson(req));
  return json({ feedback: await revealAnswer(id, questionId) });
});
