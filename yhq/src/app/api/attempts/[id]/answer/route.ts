import { handler, json, readJson } from "@/lib/api";
import { answerSchema } from "@/lib/validation";
import { submitAnswer } from "@/lib/attempts";

export const POST = handler(async (req: Request, ctx: { params: Promise<{ id: string }> }) => {
  const { id } = await ctx.params;
  const { questionId, optionId } = answerSchema.parse(await readJson(req));
  return json(await submitAnswer(id, questionId, optionId));
});
