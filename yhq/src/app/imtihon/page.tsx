import type { Metadata } from "next";
import { AlertTriangle, CheckCircle2, Clock, ListOrdered, ShieldAlert } from "lucide-react";
import { getT } from "@/lib/i18n/server";
import { getSettings } from "@/lib/settings";
import { Card, PageHeader } from "@/components/ui/misc";
import { StartButton } from "@/components/start/start-button";

export const metadata: Metadata = { title: "Imtihon rejimi", description: "Haqiqiy imtihonga o'xshash sinov: vaqt cheklangan, javoblar yakunda." };
export const dynamic = "force-dynamic";

export default async function ExamPage() {
  const { t, locale } = await getT();
  const s = await getSettings();
  const note = locale === "uzc" ? (await import("@/lib/translit")).toCyrillic(s.examFormatNote) : s.examFormatNote;
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("exam.title")} subtitle={t("exam.subtitle")} />
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-5"><ListOrdered className="h-6 w-6 text-accent" /><p className="mt-2 text-sm text-muted-foreground">{t("exam.questions")}</p><p className="text-2xl font-bold">{s.examQuestionCount}</p></Card>
        <Card className="p-5"><Clock className="h-6 w-6 text-accent" /><p className="mt-2 text-sm text-muted-foreground">{t("exam.time")}</p><p className="text-2xl font-bold">{t("exam.minutes", { n: s.examTimeMinutes })}</p></Card>
        <Card className="p-5"><ShieldAlert className="h-6 w-6 text-accent" /><p className="mt-2 text-sm text-muted-foreground">{t("exam.maxErrors")}</p><p className="text-2xl font-bold">{s.examMaxErrors}</p></Card>
      </div>
      <Card className="mt-4 p-5">
        <h2 className="font-semibold">{t("exam.rules")}</h2>
        <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
          {[t("exam.rule1"), t("exam.rule2"), t("exam.rule3")].map((r) => <li key={r} className="flex gap-2"><CheckCircle2 className="h-4 w-4 shrink-0 text-success" />{r}</li>)}
        </ul>
      </Card>
      <Card className={`mt-4 flex gap-3 p-5 ${s.examFormatVerified ? "" : "border-warning/40 bg-warning-soft/60"}`}>
        {s.examFormatVerified ? <CheckCircle2 className="h-5 w-5 shrink-0 text-success" /> : <AlertTriangle className="h-5 w-5 shrink-0 text-warning" />}
        <div>
          <h2 className="font-semibold">{s.examFormatVerified ? t("exam.formatVerified") : t("exam.formatNotice")}</h2>
          <p className="mt-1 text-sm text-foreground/80">{note}</p>
        </div>
      </Card>
      <div className="mt-6">
        <StartButton payload={{ kind: "EXAM", mode: "EXAM" }} variant="accent" size="lg" className="w-full sm:w-auto" data-testid="start-exam">{t("exam.start")}</StartButton>
      </div>
    </div>
  );
}
