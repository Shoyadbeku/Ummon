import type { Metadata } from "next";
import { getT } from "@/lib/i18n/server";
import { PageHeader } from "@/components/ui/misc";
import { SearchClient } from "@/components/search-client";

export const metadata: Metadata = { title: "Savollarni qidirish" };

export default async function SearchPage() {
  const { t } = await getT();
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("search.title")} />
      <SearchClient />
    </div>
  );
}
