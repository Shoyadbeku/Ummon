import type { Metadata } from "next";
import { prisma } from "@/lib/db";
import { getT } from "@/lib/i18n/server";
import { PageHeader } from "@/components/ui/misc";
import { StartButton } from "@/components/start/start-button";
import { SignsCatalog } from "@/components/signs-catalog";

export const metadata: Metadata = { title: "Yo'l belgilari", description: "O'zbekiston YHQ 1-ilovasi bo'yicha yo'l belgilari: ma'nosi, qo'llanishi va tegishli qoidalar." };
export const dynamic = "force-dynamic";

export default async function SignsPage() {
  const { t } = await getT();
  const signs = await prisma.trafficSign.findMany({ orderBy: { order: "asc" } });
  return (
    <div>
      <PageHeader title={t("signs.title")} subtitle={t("signs.subtitle")}>
        <StartButton payload={{ kind: "SIGNS", mode: "LEARN", count: 10 }} variant="accent" data-testid="signs-test">{t("signs.test")}</StartButton>
      </PageHeader>
      <SignsCatalog signs={signs.map((s) => ({ code: s.code, group: s.group, name: s.name, meaning: s.meaning, usage: s.usage, ruleRef: s.ruleRef, imageUrl: s.imageUrl }))} />
    </div>
  );
}
