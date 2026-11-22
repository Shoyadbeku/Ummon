import { handler, json } from "@/lib/api";
import { getAttemptView } from "@/lib/attempts";

export const dynamic = "force-dynamic";

export const GET = handler(async (_req: Request, ctx: { params: Promise<{ id: string }> }) => {
  const { id } = await ctx.params;
  return json(await getAttemptView(id));
});
