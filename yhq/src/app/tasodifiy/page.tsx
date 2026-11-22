import type { Metadata } from "next";
import { Shuffle } from "lucide-react";
import { getT } from "@/lib/i18n/server";
import { Card, PageHeader } from "@/components/ui/misc";
import { StartButton } from "@/components/start/start-button";

export const metadata: Metadata = { title: "Tasodifiy 10 ta savol" };

export default async function RandomPage() {
  const { t } = await getT();
  return (
    <div className="mx-auto max-w-xl">
      <PageHeader title={t("random.title")} subtitle={t("random.subtitle")} />
      <Card className="flex flex-col items-center gap-4 p-8 text-center">
        <Shuffle className="h-12 w-12 text-accent" />
        <div className="grid w-full gap-2 sm:grid-cols-2">
          <StartButton payload={{ kind: "RANDOM", mode: "LEARN", count: 10 }} variant="accent" className="w-full" wrapperClassName="flex flex-col" data-testid="start-random">{t("tickets.learn")}</StartButton>
          <StartButton payload={{ kind: "RANDOM", mode: "EXAM", count: 10 }} variant="outline" className="w-full" wrapperClassName="flex flex-col">{t("tickets.exam")}</StartButton>
        </div>
      </Card>
    </div>
  );
}
