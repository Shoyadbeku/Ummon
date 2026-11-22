import type { Metadata } from "next";
import { getT } from "@/lib/i18n/server";
import { contentText } from "@/lib/i18n/core";
import { getActor } from "@/lib/actor";
import { getTopics } from "@/lib/queries";
import { Card, PageHeader, Progress } from "@/components/ui/misc";
import { StartButton } from "@/components/start/start-button";

export const metadata: Metadata = { title: "Mavzular bo'yicha testlar" };
export const dynamic = "force-dynamic";

export default async function TopicsPage() {
  const { t, locale } = await getT();
  const topics = await getTopics(await getActor());
  return (
    <div>
      <PageHeader title={t("topics.title")} subtitle={t("topics.subtitle")} />
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {topics.map((tp) => (
          <li key={tp.slug}>
            <Card className="flex h-full flex-col p-5">
              <h2 className="font-bold">{locale === "ru" && tp.nameRu ? tp.nameRu : contentText(locale, tp.name)}</h2>
              {tp.description && <p className="mt-1 text-sm text-muted-foreground">{contentText(locale, tp.description)}</p>}
              <p className="mt-3 text-sm">{t("topics.questions", { n: tp.count })}</p>
              <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                <Progress value={tp.count ? (tp.mastered / tp.count) * 100 : 0} tone="success" />
                <span className="shrink-0 tabular-nums">{t("topics.mastery")}: {tp.mastered}/{tp.count}</span>
              </div>
              <div className="mt-auto pt-4">
                <StartButton payload={{ kind: "TOPIC", mode: "LEARN", categorySlug: tp.slug, count: 10 }} variant="accent" size="sm" className="w-full" wrapperClassName="flex flex-col" disabled={tp.count === 0}>
                  {t("topics.start")}
                </StartButton>
              </div>
            </Card>
          </li>
        ))}
      </ul>
    </div>
  );
}
