"use client";
import { BookOpenCheck, CheckCircle2, ExternalLink, XCircle } from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n/client";
import { cn, optionLabel } from "@/lib/utils";

export type FeedbackData = {
  questionId: string;
  isCorrect: boolean;
  selectedOptionId: string | null;
  correctOptionId: string;
  explanation: string;
  ruleRef: string | null;
  ruleUrl: string | null;
  sourceName: string | null;
  sourceUrl: string | null;
  options: { id: string; text: string; isCorrect: boolean; explanation: string | null }[];
};

export function AnswerModal({
  open,
  onOpenChange,
  feedback,
  onNext,
  hasNext,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  feedback: FeedbackData | null;
  onNext?: () => void;
  hasNext?: boolean;
}) {
  const { t, c } = useI18n();
  if (!feedback) return null;
  const correctIdx = feedback.options.findIndex((o) => o.id === feedback.correctOptionId);
  const correct = feedback.options[correctIdx];
  const answered = feedback.selectedOptionId != null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title={t("modal.title")} closeLabel={t("modal.close")}>
        <div className="space-y-5 p-5" data-testid="answer-modal">
          <div className="rounded-xl border-2 border-success bg-success-soft p-4">
            <div className="text-xs font-bold tracking-widest text-success">{t("modal.correctAnswer")}: {optionLabel(correctIdx)}</div>
            <div className="mt-1.5 flex gap-2 text-base font-semibold">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />
              <span>{correct ? c(correct.text) : "—"}</span>
            </div>
          </div>

          {answered && !feedback.isCorrect && (
            <div className="rounded-xl border-2 border-danger bg-danger-soft p-3 text-sm">
              <span className="font-semibold text-danger">{t("modal.yourAnswer")}: </span>
              {(() => {
                const i = feedback.options.findIndex((o) => o.id === feedback.selectedOptionId);
                return i >= 0 ? `${optionLabel(i)}) ${c(feedback.options[i].text)}` : "—";
              })()}
            </div>
          )}

          <section>
            <h3 className="mb-1.5 flex items-center gap-2 font-semibold"><BookOpenCheck className="h-4 w-4 text-accent" />{t("modal.why")}</h3>
            <p className="leading-relaxed text-foreground/90">{c(feedback.explanation)}</p>
          </section>

          <section>
            <h3 className="mb-2 font-semibold">{t("modal.others")}</h3>
            <ul className="space-y-2">
              {feedback.options.map((o, i) =>
                o.isCorrect ? null : (
                  <li key={o.id} className={cn("flex gap-2 rounded-lg border p-3 text-sm", o.id === feedback.selectedOptionId && "border-danger bg-danger-soft")}>
                    <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
                    <div>
                      <span className="font-semibold">{optionLabel(i)}) {c(o.text)}</span>
                      <p className="mt-0.5 text-muted-foreground">{c(o.explanation ?? t("modal.othersWrong"))}</p>
                    </div>
                  </li>
                ),
              )}
            </ul>
          </section>

          {(feedback.ruleRef || feedback.sourceName) && (
            <section className="rounded-lg bg-muted p-3 text-sm">
              {feedback.ruleRef && (
                <p><span className="font-semibold">{t("modal.rule")}: </span>{c(feedback.ruleRef)}</p>
              )}
              {feedback.sourceName && (
                <p className="mt-1"><span className="font-semibold">{t("modal.source")}: </span>{c(feedback.sourceName)}</p>
              )}
              {(feedback.ruleUrl || feedback.sourceUrl) && (
                <a href={feedback.ruleUrl ?? feedback.sourceUrl!} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1 font-medium text-accent hover:underline">
                  {t("modal.openLaw")} <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </section>
          )}
        </div>
        <div className="sticky bottom-0 flex gap-2 border-t bg-card p-4">
          <Button variant="outline" className="flex-1" onClick={() => onOpenChange(false)}>{t("modal.close")}</Button>
          {hasNext && onNext && (
            <Button variant="accent" className="flex-1" onClick={onNext}>{t("modal.next")}</Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
