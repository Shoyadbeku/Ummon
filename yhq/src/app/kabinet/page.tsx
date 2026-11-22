import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, CheckCircle2, ClipboardList, Percent, Star, TriangleAlert, UserRound } from "lucide-react";
import { getT } from "@/lib/i18n/server";
import { contentText, intlLocale } from "@/lib/i18n/core";
import { getActor } from "@/lib/actor";
import { getCabinet } from "@/lib/queries";
import { Badge, Card, EmptyState, PageHeader, Stat } from "@/components/ui/misc";
import { buttonClass } from "@/components/ui/button";
import { StartButton } from "@/components/start/start-button";
import { ProgressChart } from "@/components/progress-chart";
import { LogoutButton } from "@/components/logout-button";
import { formatDate, formatDuration } from "@/lib/utils";

export const metadata: Metadata = { title: "Shaxsiy kabinet", robots: { index: false } };
export const dynamic = "force-dynamic";

export default async function CabinetPage() {
  const { t, locale } = await getT();
  const actor = await getActor();
  const data = await getCabinet(actor);
  const c = (s: string) => contentText(locale, s);
  const L = intlLocale(locale);

  return (
    <div>
      <PageHeader title={t("cabinet.title")}>{actor.user && <LogoutButton label={t("nav.logout")} />}</PageHeader>

      <Card className="mb-6 flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
        <span className="grid h-14 w-14 place-items-center rounded-full bg-accent/15 text-accent"><UserRound className="h-7 w-7" /></span>
        {actor.user ? (
          <div>
            <p className="text-lg font-bold">{actor.user.name}</p>
            <p className="text-sm text-muted-foreground">{actor.user.email}</p>
            <p className="text-xs text-muted-foreground">{t("cabinet.member")}: {formatDate(actor.user.createdAt, L)}</p>
          </div>
        ) : (
          <div className="flex-1">
            <p className="font-bold">{t("cabinet.guest")}</p>
            <p className="text-sm text-muted-foreground">{t("cabinet.guestText")}</p>
            <div className="mt-3 flex gap-2">
              <Link href="/royxat" className={buttonClass("accent", "sm")}>{t("nav.register")}</Link>
              <Link href="/kirish" className={buttonClass("outline", "sm")}>{t("nav.login")}</Link>
            </div>
          </div>
        )}
      </Card>

      {!data ? (
        <EmptyState title={t("cabinet.noTests")} />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label={t("cabinet.tests")} value={data.totalTests} icon={<ClipboardList className="h-4 w-4" />} />
            <Stat label={t("cabinet.tickets")} value={data.ticketsDone} icon={<CheckCircle2 className="h-4 w-4" />} tone="success" />
            <Stat label={t("cabinet.accuracy")} value={`${data.accuracy}%`} icon={<Percent className="h-4 w-4" />} tone="accent" />
            <Stat label={t("nav.mistakes")} value={data.mistakesCount} icon={<TriangleAlert className="h-4 w-4" />} tone="danger" />
          </div>

          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-2 font-semibold"><BarChart3 className="h-5 w-5 text-accent" />{t("cabinet.chart")}</h2>
            {data.chart.length ? <ProgressChart data={data.chart} /> : <p className="text-sm text-muted-foreground">{t("cabinet.noTests")}</p>}
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="p-5">
              <h2 className="mb-3 font-semibold">{t("cabinet.recent")}</h2>
              {data.recent.length === 0 ? (
                <p className="text-sm text-muted-foreground">{t("cabinet.noTests")}</p>
              ) : (
                <ul className="divide-y text-sm">
                  {data.recent.map((a) => (
                    <li key={a.id} className="flex items-center gap-2 py-2.5">
                      <Badge tone={a.mode === "EXAM" ? "warning" : "accent"}>{t(`cabinet.kind.${a.kind}`)}{a.ticket ? ` №${a.ticket.number}` : ""}</Badge>
                      <span className="text-muted-foreground">{formatDate(a.startedAt, L)}</span>
                      <span className="ml-auto font-semibold tabular-nums">
                        {a.status === "IN_PROGRESS" ? t("cabinet.inProgress") : `${a.correctCount}/${a.total} · ${formatDuration(a.durationSec)}`}
                      </span>
                      <Link href={a.status === "IN_PROGRESS" ? `/test/${a.id}` : `/natija/${a.id}`} className="text-accent hover:underline">{t("cabinet.open")}</Link>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card className="p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="flex items-center gap-2 font-semibold"><Star className="h-5 w-5 text-warning" />{t("cabinet.saved")}</h2>
                {data.saved.length >= 1 && (
                  <StartButton payload={{ kind: "FAVORITES", mode: "LEARN", count: Math.min(50, Math.max(5, data.saved.length)) }} size="sm" variant="soft">{t("cabinet.practiceSaved")}</StartButton>
                )}
              </div>
              {data.saved.length === 0 ? (
                <p className="text-sm text-muted-foreground">{t("cabinet.savedEmpty")}</p>
              ) : (
                <ul className="divide-y text-sm">
                  {data.saved.slice(0, 15).map((q) => (
                    <li key={q.id} className="py-2.5"><span className="text-xs text-muted-foreground">{q.code} · {c(q.category.name)}</span><p>{c(q.text)}</p></li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          <Card className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold">{t("cabinet.mistakesHistory")}</h2>
              <Link href="/xatolar" className="text-sm font-semibold text-accent hover:underline">{t("nav.mistakes")} →</Link>
            </div>
            {data.recentWrong.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("mistakes.empty")}</p>
            ) : (
              <ul className="divide-y text-sm">
                {data.recentWrong.map((w, i) => (
                  <li key={i} className="flex gap-3 py-2.5"><span className="shrink-0 text-xs text-muted-foreground">{formatDate(w.answeredAt, L)}</span><span>{c(w.question.text)}</span></li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
