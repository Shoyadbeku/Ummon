"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, Clock, Eye, Flag, Keyboard, RefreshCw, Star, WifiOff, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge, Card, Progress, Spinner } from "@/components/ui/misc";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { SignIcon } from "@/components/sign-icon";
import { SceneView, type SceneData } from "./scene-view";
import { AnswerModal, type FeedbackData } from "./answer-modal";
import { useI18n } from "@/lib/i18n/client";
import { cn, formatDuration, optionLabel } from "@/lib/utils";

type QView = {
  id: string;
  code: string;
  text: string;
  imageUrl: string | null;
  scene: SceneData | null;
  signCode: string | null;
  origin: "OFFICIAL" | "PRACTICE";
  verificationStatus: string;
  category: { slug: string; name: string };
  translations: { ru?: { text?: string; options?: string[]; explanation?: string } } | null;
  saved: boolean;
  options: { id: string; text: string }[];
  answer: { optionId: string | null; checked: boolean; revealed: boolean } | null;
  feedback: FeedbackData | null;
};

type AttemptData = {
  id: string;
  mode: "LEARN" | "EXAM";
  kind: string;
  status: "IN_PROGRESS" | "FINISHED" | "EXPIRED";
  ticketNumber: number | null;
  deadlineAt: string | null;
  serverNow: string;
  total: number;
  questions: QView[];
};

class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function api<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data.error ?? "Xatolik");
  return data as T;
}

export function TestRunner({ attemptId }: { attemptId: string }) {
  const { t, c, locale } = useI18n();
  const router = useRouter();
  const qc = useQueryClient();
  const key = ["attempt", attemptId];
  const { data, error, isLoading, refetch, isFetching } = useQuery({ queryKey: key, queryFn: () => api<AttemptData>(`/api/attempts/${attemptId}`) });

  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<Record<string, string>>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [modalFeedback, setModalFeedback] = useState<FeedbackData | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [online, setOnline] = useState(true);
  const restored = useRef(false);

  // Holatni sessiyada saqlash (sahifa yangilansa ham joriy savol saqlanadi)
  useEffect(() => {
    if (!data || restored.current) return;
    restored.current = true;
    try {
      const saved = Number(sessionStorage.getItem(`yhq-idx-${attemptId}`));
      if (saved >= 0 && saved < data.questions.length) setIndex(saved);
      else {
        const firstOpen = data.questions.findIndex((q) => !q.answer);
        if (firstOpen > 0) setIndex(firstOpen);
      }
    } catch {}
  }, [data, attemptId]);
  useEffect(() => {
    try { sessionStorage.setItem(`yhq-idx-${attemptId}`, String(index)); } catch {}
  }, [index, attemptId]);

  useEffect(() => {
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    setOnline(navigator.onLine);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => { window.removeEventListener("online", up); window.removeEventListener("offline", down); };
  }, []);

  useEffect(() => {
    if (data && data.status !== "IN_PROGRESS") router.replace(`/natija/${attemptId}`);
  }, [data, attemptId, router]);

  const updateQuestion = useCallback(
    (qid: string, patch: Partial<QView>) => {
      qc.setQueryData<AttemptData>(key, (old) => old && { ...old, questions: old.questions.map((q) => (q.id === qid ? { ...q, ...patch } : q)) });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [qc, attemptId],
  );

  const answerMut = useMutation({
    mutationFn: (v: { questionId: string; optionId: string }) => api<{ saved: boolean; feedback: FeedbackData | null }>(`/api/attempts/${attemptId}/answer`, v),
    onSuccess: (res, v) => {
      updateQuestion(v.questionId, {
        answer: { optionId: res.feedback?.selectedOptionId ?? v.optionId, checked: data?.mode === "LEARN", revealed: false },
        feedback: res.feedback,
      });
    },
    onError: (e: Error) => {
      if (e instanceof ApiError && e.status === 409) { refetch(); }
      setNotice(e.message);
    },
  });

  const revealMut = useMutation({
    mutationFn: (questionId: string) => api<{ feedback: FeedbackData }>(`/api/attempts/${attemptId}/reveal`, { questionId }),
    onSuccess: (res, qid) => {
      const q = data?.questions.find((x) => x.id === qid);
      updateQuestion(qid, { feedback: res.feedback, answer: q?.answer ? { ...q.answer, revealed: true } : { optionId: null, checked: false, revealed: true } });
      setModalFeedback(res.feedback);
      setModalOpen(true);
    },
    onError: (e: Error) => setNotice(e.message),
  });

  const finishMut = useMutation({
    mutationFn: () => api(`/api/attempts/${attemptId}/finish`, {}),
    onSuccess: () => {
      try { sessionStorage.removeItem(`yhq-idx-${attemptId}`); } catch {}
      router.push(`/natija/${attemptId}`);
      router.refresh();
    },
    onError: (e: Error) => setNotice(e.message),
  });

  const saveMut = useMutation({
    mutationFn: (questionId: string) => api<{ saved: boolean }>(`/api/saved`, { questionId }),
    onSuccess: (res, qid) => updateQuestion(qid, { saved: res.saved }),
  });

  const questions = data?.questions ?? [];
  const q = questions[index];
  const isExam = data?.mode === "EXAM";
  const locked = !!q && !isExam && !!q.answer && (q.answer.checked || q.answer.revealed);
  const currentSel = q ? (selected[q.id] ?? q.answer?.optionId ?? null) : null;

  // ───── Taymer (imtihon rejimi) ─────
  const offset = useMemo(() => (data ? new Date(data.serverNow).getTime() - Date.now() : 0), [data?.serverNow]); // eslint-disable-line react-hooks/exhaustive-deps
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!data?.deadlineAt) return;
    const id = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(id);
  }, [data?.deadlineAt]);
  const remaining = data?.deadlineAt ? Math.max(0, Math.floor((new Date(data.deadlineAt).getTime() - (now + offset)) / 1000)) : null;
  const autoFinished = useRef(false);
  useEffect(() => {
    if (remaining === 0 && data?.status === "IN_PROGRESS" && !autoFinished.current) {
      autoFinished.current = true;
      setNotice(t("test.timeUp"));
      finishMut.mutate();
    }
  }, [remaining, data?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const choose = useCallback(
    (optionId: string) => {
      if (!q || locked || data?.status !== "IN_PROGRESS") return;
      setSelected((s) => ({ ...s, [q.id]: optionId }));
      setNotice(null);
      if (isExam) answerMut.mutate({ questionId: q.id, optionId });
    },
    [q, locked, isExam, answerMut, data?.status],
  );

  const check = useCallback(() => {
    if (!q || isExam || locked) return;
    const opt = selected[q.id];
    if (!opt) { setNotice(t("test.selectFirst")); return; }
    answerMut.mutate({ questionId: q.id, optionId: opt });
  }, [q, isExam, locked, selected, answerMut, t]);

  const showAnswer = useCallback(() => {
    if (!q || isExam) return;
    if (q.feedback) { setModalFeedback(q.feedback); setModalOpen(true); return; }
    revealMut.mutate(q.id);
  }, [q, isExam, revealMut]);

  const go = useCallback((i: number) => {
    setIndex(Math.max(0, Math.min(questions.length - 1, i)));
    setNotice(null);
  }, [questions.length]);

  // ───── Klaviatura ─────
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (modalOpen || confirmOpen) return;
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (!q) return;
      const k = e.key.toLowerCase();
      const map: Record<string, number> = { "1": 0, "2": 1, "3": 2, "4": 3, "5": 4, a: 0, b: 1, c: 2, d: 3, e: 4 };
      if (k in map && q.options[map[k]]) { e.preventDefault(); choose(q.options[map[k]].id); }
      else if (k === "enter") { e.preventDefault(); if (isExam) go(index + 1); else check(); }
      else if (k === "arrowright") go(index + 1);
      else if (k === "arrowleft") go(index - 1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [q, choose, check, go, index, isExam, modalOpen, confirmOpen]);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-muted-foreground" role="status">
        <Spinner className="h-8 w-8 text-accent" />{t("test.loading")}
      </div>
    );
  }
  if (error || !data) {
    return (
      <Card className="mx-auto max-w-md p-8 text-center">
        <AlertTriangle className="mx-auto h-10 w-10 text-danger" />
        <p className="mt-3 font-semibold">{t("test.error")}</p>
        <p className="mt-1 text-sm text-muted-foreground">{(error as Error)?.message}</p>
        <Button className="mt-4" onClick={() => refetch()} disabled={isFetching}><RefreshCw className="h-4 w-4" />{t("test.retry")}</Button>
      </Card>
    );
  }
  if (!q) return null;

  const answeredCount = questions.filter((x) => x.answer?.optionId || x.answer?.revealed).length;
  const unanswered = questions.filter((x) => !x.answer?.optionId).length;
  const fb = !isExam ? q.feedback : null;
  const ruText = locale === "ru" ? q.translations?.ru?.text : null;
  const title =
    data.ticketNumber != null ? `${t("tickets.ticket")} №${data.ticketNumber}` : t(`cabinet.kind.${data.kind}` as never);

  return (
    <div className="mx-auto max-w-3xl pb-28 sm:pb-6">
      {/* Yuqori panel */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold sm:text-2xl">{title}</h1>
          <Badge tone={isExam ? "warning" : "accent"} className="mt-1">{t(`test.mode.${data.mode}`)}</Badge>
        </div>
        {remaining != null && (
          <div className={cn("flex items-center gap-2 rounded-lg border px-3 py-2 font-mono text-lg font-bold tabular-nums", remaining < 60 ? "border-danger text-danger animate-pulse" : "")} aria-live="polite" aria-label={t("test.timeLeft")}>
            <Clock className="h-5 w-5" />{formatDuration(remaining)}
          </div>
        )}
      </div>

      <div className="mb-3 flex items-center justify-between text-sm text-muted-foreground">
        <span className="font-semibold text-foreground" data-testid="question-counter">{t("test.question")} №{index + 1} / {questions.length}</span>
        <span>{answeredCount}/{questions.length}</span>
      </div>
      <Progress value={(answeredCount / questions.length) * 100} label={`${answeredCount}/${questions.length}`} />

      {/* Raqamli navigatsiya */}
      <nav className="mt-4 flex flex-wrap gap-1.5" aria-label="Savollar">
        {questions.map((x, i) => {
          const state = !isExam && x.feedback ? (x.feedback.isCorrect ? "ok" : "bad") : x.answer?.optionId ? "done" : "none";
          return (
            <button
              key={x.id}
              onClick={() => go(i)}
              aria-label={`${t("test.question")} ${i + 1}`}
              aria-current={i === index ? "step" : undefined}
              className={cn(
                "h-9 w-9 rounded-md border text-sm font-semibold transition",
                state === "ok" && "border-success bg-success text-success-foreground",
                state === "bad" && "border-danger bg-danger text-danger-foreground",
                state === "done" && "border-accent bg-accent/15 text-accent",
                state === "none" && "bg-card hover:bg-muted",
                i === index && "ring-2 ring-ring ring-offset-2 ring-offset-background",
              )}
            >
              {i + 1}
            </button>
          );
        })}
      </nav>

      {!online && (
        <div className="mt-4 flex items-center gap-2 rounded-lg bg-warning-soft p-3 text-sm text-warning"><WifiOff className="h-4 w-4" />{t("common.offline")}</div>
      )}

      {/* Savol kartasi */}
      <Card className="mt-4 overflow-hidden animate-fade-in" key={q.id}>
        <div className="p-5 sm:p-6">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Badge tone="muted">{c(q.category.name)}</Badge>
            {q.origin === "OFFICIAL" ? <Badge tone="success">{t("test.officialBadge")}</Badge> : <Badge tone="accent">{t("test.practiceBadge")}</Badge>}
            {q.verificationStatus !== "VERIFIED" && <Badge tone="warning">{t("test.unverified")}</Badge>}
            <button
              onClick={() => saveMut.mutate(q.id)}
              className={cn("ml-auto inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm hover:bg-muted", q.saved ? "text-warning" : "text-muted-foreground")}
              aria-pressed={q.saved}
              aria-label={q.saved ? t("test.saved") : t("test.save")}
            >
              <Star className={cn("h-4 w-4", q.saved && "fill-current")} />
              <span className="hidden sm:inline">{q.saved ? t("test.saved") : t("test.save")}</span>
            </button>
          </div>
          <h2 className="text-lg font-semibold leading-snug sm:text-xl" data-testid="question-text">{c(q.text, ruText)}</h2>
          {locale === "ru" && !ruText && <p className="mt-1 text-xs text-muted-foreground">{t("test.ruNotice")}</p>}

          {(q.imageUrl || q.scene || q.signCode) && (
            <div className="mt-4 flex flex-col items-center gap-3">
              {q.imageUrl && (
                // Rasmlar yuklashda sharp orqali WebP ga siqiladi va o'lchami kichraytiriladi
                // eslint-disable-next-line @next/next/no-img-element
                <img src={q.imageUrl} alt={c(q.text)} loading="lazy" decoding="async" className="h-auto max-h-80 w-auto max-w-full rounded-lg border object-contain" />
              )}
              {q.scene && <SceneView scene={q.scene} className="w-full" />}
              {q.signCode && !q.scene && <SignIcon code={q.signCode} className="h-32 w-32 sm:h-36 sm:w-36" />}
            </div>
          )}
        </div>

        <div className="grid gap-2 border-t bg-muted/30 p-4 sm:p-5" role="radiogroup" aria-label={t("test.question")}>
          {q.options.map((o, i) => {
            const isSel = currentSel === o.id;
            const isRight = fb && o.id === fb.correctOptionId;
            const isWrongSel = fb && isSel && !fb.isCorrect && o.id === fb.selectedOptionId;
            const optRu = locale === "ru" ? q.translations?.ru?.options?.[i] : null;
            return (
              <button
                key={o.id}
                role="radio"
                aria-checked={isSel}
                disabled={locked || data.status !== "IN_PROGRESS"}
                onClick={() => choose(o.id)}
                data-testid="option"
                className={cn(
                  "group flex w-full items-start gap-3 rounded-lg border-2 bg-card p-3.5 text-left transition sm:p-4",
                  !locked && "hover:border-accent/60 hover:bg-accent/5",
                  isSel && !fb && "border-accent bg-accent/10",
                  isRight && "border-success bg-success-soft",
                  isWrongSel && "border-danger bg-danger-soft animate-shake",
                  locked && !isRight && !isWrongSel && "opacity-70",
                )}
              >
                <span className={cn(
                  "grid h-7 w-7 shrink-0 place-items-center rounded-md border text-sm font-bold",
                  isSel && !fb && "border-accent bg-accent text-accent-foreground",
                  isRight && "border-success bg-success text-success-foreground",
                  isWrongSel && "border-danger bg-danger text-danger-foreground",
                )}>{optionLabel(i)}</span>
                <span className="flex-1 pt-0.5 leading-snug">{c(o.text, optRu)}</span>
                {isRight && <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />}
                {isWrongSel && <XCircle className="h-5 w-5 shrink-0 text-danger" />}
              </button>
            );
          })}
        </div>

        {fb && (
          <div className={cn("flex flex-wrap items-center gap-3 border-t p-4 animate-fade-in", fb.isCorrect ? "bg-success-soft" : "bg-danger-soft")} role="status" aria-live="polite" data-testid="feedback">
            {fb.isCorrect ? <CheckCircle2 className="h-6 w-6 text-success" /> : <XCircle className="h-6 w-6 text-danger" />}
            <span className={cn("font-bold", fb.isCorrect ? "text-success" : "text-danger")}>
              {fb.selectedOptionId == null ? t("result.notAnswered") : fb.isCorrect ? t("test.correct") : t("test.wrong")}
            </span>
            <Button size="sm" variant="outline" className="ml-auto" onClick={() => { setModalFeedback(fb); setModalOpen(true); }}>
              <Eye className="h-4 w-4" />{t("modal.why")}
            </Button>
          </div>
        )}
      </Card>

      {notice && <p className="mt-3 rounded-md bg-warning-soft p-3 text-sm text-warning" role="alert">{notice}</p>}
      {isExam && <p className="mt-3 text-sm text-muted-foreground">{t("test.examHint")}</p>}

      {/* Boshqaruv tugmalari (mobilda pastga yopishgan) */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-background/95 p-3 backdrop-blur sm:static sm:mt-5 sm:border-0 sm:bg-transparent sm:p-0">
        <div className="mx-auto grid max-w-3xl grid-cols-4 gap-2 sm:flex sm:flex-wrap">
          <Button variant="outline" onClick={() => go(index - 1)} disabled={index === 0} aria-label={t("test.prev")} className="sm:w-auto">
            <ChevronLeft className="h-4 w-4" /><span className="hidden sm:inline">{t("test.prev")}</span>
          </Button>
          {!isExam && (
            <>
              <Button variant="accent" onClick={check} disabled={locked || answerMut.isPending} className="col-span-2 sm:col-span-1" data-testid="check">
                {answerMut.isPending ? <Spinner className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}{t("test.check")}
              </Button>
            </>
          )}
          {isExam && <div className="col-span-2 sm:hidden" />}
          <Button variant="outline" onClick={() => go(index + 1)} disabled={index === questions.length - 1} aria-label={t("test.next")} className="sm:w-auto">
            <span className="hidden sm:inline">{t("test.next")}</span><ChevronRight className="h-4 w-4" />
          </Button>
          {!isExam && (
            <Button variant="soft" onClick={showAnswer} disabled={revealMut.isPending} className="col-span-2 sm:col-span-1" data-testid="show-answer">
              <Eye className="h-4 w-4" />{t("test.showAnswer")}
            </Button>
          )}
          <Button variant="primary" onClick={() => setConfirmOpen(true)} className={cn(isExam ? "col-span-4" : "col-span-2", "sm:col-span-1 sm:ml-auto")} data-testid="finish">
            <Flag className="h-4 w-4" />{t("test.finish")}
          </Button>
        </div>
      </div>

      <p className="mt-4 hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><Keyboard className="h-4 w-4" />{t("test.keyboard")}</p>

      <AnswerModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        feedback={modalFeedback}
        hasNext={index < questions.length - 1}
        onNext={() => { setModalOpen(false); go(index + 1); }}
      />

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent title={t("test.finishConfirm")} closeLabel={t("modal.close")}>
          <div className="p-5">
            {unanswered > 0 ? <p className="text-muted-foreground">{t("test.finishUnanswered", { n: unanswered })}</p> : <p className="text-muted-foreground">{answeredCount}/{questions.length}</p>}
            <div className="mt-5 flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setConfirmOpen(false)}>{t("test.cancel")}</Button>
              <Button className="flex-1" onClick={() => finishMut.mutate()} disabled={finishMut.isPending} data-testid="confirm-finish">
                {finishMut.isPending && <Spinner className="h-4 w-4" />}{t("test.confirm")}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
