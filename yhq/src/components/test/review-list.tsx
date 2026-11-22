"use client";
import { useState } from "react";
import { CheckCircle2, ChevronDown, XCircle } from "lucide-react";
import { useI18n } from "@/lib/i18n/client";
import { Card } from "@/components/ui/misc";
import { Button } from "@/components/ui/button";
import { SignIcon } from "@/components/sign-icon";
import { SceneView, type SceneData } from "./scene-view";
import type { FeedbackData } from "./answer-modal";
import { cn, optionLabel } from "@/lib/utils";

type Q = { id: string; code: string; text: string; scene: SceneData | null; signCode: string | null; imageUrl: string | null; feedback: FeedbackData | null };

export function ReviewList({ questions }: { questions: Q[] }) {
  const { t, c } = useI18n();
  const wrongCount = questions.filter((q) => !q.feedback?.isCorrect).length;
  const [onlyWrong, setOnlyWrong] = useState(wrongCount > 0);
  const [open, setOpen] = useState<string | null>(null);
  const list = onlyWrong ? questions.filter((q) => !q.feedback?.isCorrect) : questions;
  return (
    <div>
      <div className="mb-3 flex gap-2">
        <Button size="sm" variant={onlyWrong ? "danger" : "outline"} onClick={() => setOnlyWrong(true)}>{t("result.onlyWrong")} ({wrongCount})</Button>
        <Button size="sm" variant={!onlyWrong ? "primary" : "outline"} onClick={() => setOnlyWrong(false)}>{t("result.showAll")} ({questions.length})</Button>
      </div>
      <ol className="space-y-3">
        {list.map((q) => {
          const fb = q.feedback;
          const idx = questions.indexOf(q);
          const isOpen = open === q.id;
          return (
            <li key={q.id}>
              <Card className={cn("overflow-hidden", fb?.isCorrect ? "border-success/40" : "border-danger/40")}>
                <button className="flex w-full items-start gap-3 p-4 text-left" onClick={() => setOpen(isOpen ? null : q.id)} aria-expanded={isOpen}>
                  {fb?.isCorrect ? <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" /> : <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-danger" />}
                  <span className="flex-1 font-medium"><span className="text-muted-foreground">{idx + 1}. </span>{c(q.text)}</span>
                  <ChevronDown className={cn("h-5 w-5 shrink-0 transition", isOpen && "rotate-180")} />
                </button>
                {isOpen && fb && (
                  <div className="space-y-3 border-t p-4 animate-fade-in">
                    {q.scene && <SceneView scene={q.scene} />}
                    {q.signCode && !q.scene && <SignIcon code={q.signCode} className="mx-auto h-24 w-24" />}
                    <ul className="space-y-1.5">
                      {fb.options.map((o, i) => (
                        <li key={o.id} className={cn("rounded-md border p-2.5 text-sm", o.isCorrect && "border-success bg-success-soft font-semibold", !o.isCorrect && o.id === fb.selectedOptionId && "border-danger bg-danger-soft")}>
                          {optionLabel(i)}) {c(o.text)}
                          {!o.isCorrect && o.id === fb.selectedOptionId && <span className="ml-2 text-xs text-danger">← {t("modal.yourAnswer")}</span>}
                        </li>
                      ))}
                    </ul>
                    {fb.selectedOptionId == null && <p className="text-sm text-danger">{t("result.notAnswered")}</p>}
                    <p className="text-sm leading-relaxed">{c(fb.explanation)}</p>
                    {fb.ruleRef && (
                      <p className="text-xs text-muted-foreground">
                        {t("modal.rule")}: {fb.ruleUrl ? <a className="text-accent hover:underline" href={fb.ruleUrl} target="_blank" rel="noopener noreferrer">{c(fb.ruleRef)}</a> : c(fb.ruleRef)}
                      </p>
                    )}
                  </div>
                )}
              </Card>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
