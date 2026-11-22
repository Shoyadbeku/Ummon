import type { Metadata } from "next";
import { CheckCircle2, Eye, PartyPopper } from "lucide-react";
import { getT } from "@/lib/i18n/server";
import { contentText } from "@/lib/i18n/core";
import { getActor } from "@/lib/actor";
import { getMistakes } from "@/lib/queries";
import { Badge, Card, EmptyState, PageHeader, Stat } from "@/components/ui/misc";
import { StartButton } from "@/components/start/start-button";

export const metadata: Metadata = { title: "Mening xatolarim" };
export const dynamic = "force-dynamic";

export default async function MistakesPage() {
  const { t, locale } = await getT();
  const { mistakes, mastered, seen } = await getMistakes(await getActor());
  const c = (s: string) => contentText(locale, s);
  return (
    <div>
      <PageHeader title={t("mistakes.title")} subtitle={t("mistakes.subtitle")}>
        {mistakes.length > 0 && (
          <StartButton payload={{ kind: "MISTAKES", mode: "LEARN", count: Math.min(50, Math.max(5, mistakes.length)) }} variant="accent" data-testid="practice-mistakes">
            {t("mistakes.practice")}
          </StartButton>
        )}
      </PageHeader>
      <div className="mb-6 grid grid-cols-3 gap-3">
        <Stat label={t("mistakes.title")} value={mistakes.length} tone="danger" />
        <Stat label={t("mistakes.mastered")} value={mastered} tone="success" />
        <Stat label={t("mistakes.seen")} value={seen} />
      </div>
      {mistakes.length === 0 ? (
        <EmptyState icon={<PartyPopper className="h-10 w-10" />} title={t("mistakes.empty")} />
      ) : (
        <ul className="space-y-3" data-testid="mistake-list">
          {mistakes.map((m) => (
            <li key={m.question.id}>
              <Card className="p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="muted">{c(m.question.category.name)}</Badge>
                  <Badge tone="danger">{t("mistakes.wrongTimes", { n: m.wrongCount })}</Badge>
                  <span className="ml-auto text-xs text-muted-foreground">{m.question.code}</span>
                </div>
                <p className="mt-2 font-medium">{c(m.question.text)}</p>
                <details className="group mt-2">
                  <summary className="inline-flex cursor-pointer items-center gap-1 text-sm font-semibold text-accent"><Eye className="h-4 w-4" />{t("modal.title")}</summary>
                  <div className="mt-2 rounded-md bg-success-soft p-3 text-sm">
                    <p className="flex gap-2 font-semibold text-success"><CheckCircle2 className="h-4 w-4 shrink-0" />{c(m.question.options[0]?.text ?? "")}</p>
                    <p className="mt-1 text-foreground/80">{c(m.question.explanation)}</p>
                    {m.question.ruleRef && <p className="mt-1 text-xs text-muted-foreground">{c(m.question.ruleRef)}</p>}
                  </div>
                </details>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
