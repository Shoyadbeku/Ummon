import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { CheckCircle2, Clock, Hash, ListChecks, Percent, Trophy, XCircle, TrendingDown, TrendingUp, Minus } from "lucide-react";
import { getT } from "@/lib/i18n/server";
import { intlLocale } from "@/lib/i18n/core";
import { getAttemptView, getResultSummary } from "@/lib/attempts";
import { HttpError } from "@/lib/auth";
import { Card, Stat } from "@/components/ui/misc";
import { buttonClass } from "@/components/ui/button";
import { StartButton } from "@/components/start/start-button";
import { ReviewList } from "@/components/test/review-list";
import { formatDate, formatDuration, percent } from "@/lib/utils";

export const metadata: Metadata = { title: "Natija", robots: { index: false } };
export const dynamic = "force-dynamic";

export default async function ResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { t, locale } = await getT();
  let summary: Awaited<ReturnType<typeof getResultSummary>>;
  let view: Awaited<ReturnType<typeof getAttemptView>>;
  try {
    view = await getAttemptView(id);
    if (view.status === "IN_PROGRESS") redirect(`/test/${id}`);
    summary = await getResultSummary(id);
  } catch (e) {
    if (e instanceof HttpError) notFound();
    throw e;
  }
  const { attempt, previous, nextTicket } = summary;
  const pct = percent(attempt.correctCount, attempt.total);
  const examLike = attempt.maxErrors != null;
  const passed = examLike ? !!attempt.passed : attempt.wrongCount === 0;
  const prev = previous[0];
  const diff = prev ? attempt.correctCount - prev.correctCount : null;

  const retryPayload =
    attempt.kind === "TICKET"
      ? { kind: "TICKET" as const, mode: attempt.mode, ticketNumber: view.ticketNumber ?? undefined }
      : attempt.kind === "TOPIC"
        ? { kind: "TOPIC" as const, mode: attempt.mode, categorySlug: attempt.categorySlug ?? undefined }
        : { kind: attempt.kind, mode: attempt.mode };

  return (
    <div className="mx-auto max-w-4xl">
      <Card className={`overflow-hidden animate-scale-in ${passed ? "border-success/40" : "border-danger/40"}`} data-testid="result-card">
        <div className={`flex flex-col items-center gap-3 p-8 text-center ${passed ? "bg-success-soft" : "bg-danger-soft"}`}>
          {passed ? <Trophy className="h-14 w-14 text-success" /> : <XCircle className="h-14 w-14 text-danger" />}
          <h1 className="text-2xl font-extrabold sm:text-3xl">{t("result.title")}</h1>
          <p className={`text-lg font-semibold ${passed ? "text-success" : "text-danger"}`}>
            {examLike ? (passed ? t("result.examPassed") : t("result.examFailed")) : passed ? t("result.passed") : t("result.failed")}
          </p>
          {examLike && <p className="text-sm text-muted-foreground">{t("result.allowed", { n: attempt.maxErrors! })}</p>}
          <div className="relative mt-2 grid h-32 w-32 place-items-center">
            <svg viewBox="0 0 36 36" className="absolute inset-0 -rotate-90">
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="hsl(var(--muted))" strokeWidth="3" />
              <circle cx="18" cy="18" r="15.9" fill="none" stroke={passed ? "hsl(var(--success))" : "hsl(var(--danger))"} strokeWidth="3" strokeDasharray={`${pct} 100`} strokeLinecap="round" />
            </svg>
            <span className="text-3xl font-extrabold tabular-nums" data-testid="result-percent">{pct}%</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3 lg:grid-cols-6">
          <Stat label={t("result.total")} value={attempt.total} icon={<ListChecks className="h-4 w-4" />} />
          <Stat label={t("result.correct")} value={<span data-testid="result-correct">{attempt.correctCount}</span>} tone="success" icon={<CheckCircle2 className="h-4 w-4" />} />
          <Stat label={t("result.wrong")} value={<span data-testid="result-wrong">{attempt.wrongCount}</span>} tone="danger" icon={<XCircle className="h-4 w-4" />} />
          <Stat label={t("result.percent")} value={`${pct}%`} icon={<Percent className="h-4 w-4" />} />
          <Stat label={t("result.time")} value={formatDuration(attempt.durationSec)} icon={<Clock className="h-4 w-4" />} />
          <Stat label={t("result.ticket")} value={view.ticketNumber != null ? `№${view.ticketNumber}` : "—"} icon={<Hash className="h-4 w-4" />} />
        </div>
      </Card>

      <div className="mt-5 grid gap-2 sm:grid-cols-4">
        <a href="#review" className={buttonClass("danger", "md")}>{t("result.review")}</a>
        <StartButton payload={retryPayload} variant="outline" className="w-full" wrapperClassName="flex flex-col">{t("result.retry")}</StartButton>
        {nextTicket ? (
          <StartButton payload={{ kind: "TICKET", mode: attempt.mode, ticketNumber: nextTicket }} variant="accent" className="w-full" wrapperClassName="flex flex-col" data-testid="next-ticket">{t("result.nextTicket")} →</StartButton>
        ) : (
          <Link href="/xatolar" className={buttonClass("accent")}>{t("nav.mistakes")}</Link>
        )}
        <Link href="/biletlar" className={buttonClass("outline")}>{t("result.allTickets")}</Link>
      </div>

      <Card className="mt-6 p-5">
        <h2 className="font-semibold">{t("result.compare")}</h2>
        {previous.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">{t("result.noPrevious")}</p>
        ) : (
          <>
            <p className={`mt-2 flex items-center gap-2 text-sm font-semibold ${diff! > 0 ? "text-success" : diff! < 0 ? "text-danger" : "text-muted-foreground"}`}>
              {diff! > 0 ? <TrendingUp className="h-4 w-4" /> : diff! < 0 ? <TrendingDown className="h-4 w-4" /> : <Minus className="h-4 w-4" />}
              {diff! > 0 ? t("result.better", { n: diff! }) : diff! < 0 ? t("result.worse", { n: -diff! }) : t("result.same")}
            </p>
            <ul className="mt-3 divide-y text-sm">
              {previous.map((p) => (
                <li key={p.id} className="flex items-center justify-between py-2">
                  <span className="text-muted-foreground">{formatDate(p.finishedAt, intlLocale(locale))}</span>
                  <span className="font-semibold tabular-nums">{p.correctCount}/{p.total} · {formatDuration(p.durationSec)}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </Card>

      <section id="review" className="mt-8 scroll-mt-20">
        <h2 className="mb-3 text-xl font-bold">{t("result.reviewTitle")}</h2>
        <ReviewList questions={view.questions as never} />
      </section>
    </div>
  );
}
