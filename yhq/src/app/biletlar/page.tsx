import type { Metadata } from "next";
import Link from "next/link";
import { CheckCircle2, Circle, Clock, XCircle } from "lucide-react";
import { getT } from "@/lib/i18n/server";
import { intlLocale } from "@/lib/i18n/core";
import { getActor } from "@/lib/actor";
import { getTicketsWithStatus } from "@/lib/queries";
import { Badge, Card, EmptyState, PageHeader, Progress } from "@/components/ui/misc";
import { buttonClass } from "@/components/ui/button";
import { StartButton } from "@/components/start/start-button";
import { formatDate } from "@/lib/utils";

export const metadata: Metadata = { title: "Biletlar", description: "YHQ nazariy imtihoniga tayyorlov biletlari — har birida 10 ta savol." };
export const dynamic = "force-dynamic";

const STATUS_UI = {
  NOT_STARTED: { tone: "muted", icon: Circle },
  IN_PROGRESS: { tone: "accent", icon: Clock },
  PASSED: { tone: "success", icon: CheckCircle2 },
  FAILED: { tone: "danger", icon: XCircle },
} as const;

export default async function TicketsPage() {
  const { t, locale } = await getT();
  const tickets = await getTicketsWithStatus(await getActor());
  const passed = tickets.filter((x) => x.status === "PASSED").length;
  const failed = tickets.filter((x) => x.status === "FAILED").length;
  const left = tickets.length - passed - failed;
  return (
    <div>
      <PageHeader title={t("tickets.title")} subtitle={t("tickets.subtitle")} />
      {tickets.length > 0 && (
        <Card className="mb-6 p-4">
          <p className="mb-2 text-sm text-muted-foreground">{t("tickets.summary", { passed, failed, left })}</p>
          <div className="flex h-2.5 overflow-hidden rounded-full bg-muted">
            <div className="bg-success" style={{ width: `${(passed / tickets.length) * 100}%` }} />
            <div className="bg-danger" style={{ width: `${(failed / tickets.length) * 100}%` }} />
          </div>
        </Card>
      )}
      {tickets.length === 0 ? (
        <EmptyState title={t("tickets.empty")} />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="ticket-list">
          {tickets.map((tk) => {
            const ui = STATUS_UI[tk.status];
            return (
              <li key={tk.number}>
                <Card className="flex h-full flex-col p-5 transition hover:shadow-md" data-testid={`ticket-${tk.number}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h2 className="text-lg font-bold">{t("tickets.ticket")} №{tk.number}</h2>
                      <p className="text-xs text-muted-foreground">{tk.questionCount} {t("home.stats.questions")}</p>
                    </div>
                    <Badge tone={ui.tone}><ui.icon className="h-3.5 w-3.5" />{t(`tickets.status.${tk.status}`)}</Badge>
                  </div>
                  <div className="mt-4 space-y-1 text-sm">
                    {tk.lastTotal != null && (
                      <>
                        <div className="flex justify-between"><span className="text-muted-foreground">{t("tickets.lastResult")}</span><span className="font-semibold tabular-nums">{tk.lastCorrect}/{tk.lastTotal}</span></div>
                        <Progress value={((tk.lastCorrect ?? 0) / tk.lastTotal) * 100} tone={tk.lastCorrect === tk.lastTotal ? "success" : "danger"} />
                      </>
                    )}
                    {tk.lastAt && <div className="flex justify-between pt-1"><span className="text-muted-foreground">{t("tickets.lastAt")}</span><span>{formatDate(tk.lastAt, intlLocale(locale))}</span></div>}
                  </div>
                  <div className="mt-auto flex flex-wrap gap-2 pt-5">
                    {tk.inProgressId ? (
                      <Link href={`/test/${tk.inProgressId}`} className={buttonClass("accent", "sm", "flex-1")}>{t("tickets.continue")}</Link>
                    ) : (
                      <StartButton payload={{ kind: "TICKET", mode: "LEARN", ticketNumber: tk.number }} variant="accent" size="sm" className="w-full" wrapperClassName="flex flex-1 flex-col" data-testid={`start-learn-${tk.number}`}>{t("tickets.learn")}</StartButton>
                    )}
                    <StartButton payload={{ kind: "TICKET", mode: "EXAM", ticketNumber: tk.number }} variant="outline" size="sm" className="w-full" wrapperClassName="flex flex-1 flex-col">{t("tickets.exam")}</StartButton>
                  </div>
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
