"use client";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Search, Star } from "lucide-react";
import { useI18n } from "@/lib/i18n/client";
import { Badge, Card, EmptyState, Spinner } from "@/components/ui/misc";
import { SignIcon } from "@/components/sign-icon";

type Result = { id: string; code: string; text: string; ruleRef: string | null; signCode: string | null; category: { name: string }; correct: string | null; tickets: number[] };

export function SearchClient() {
  const { t, c } = useI18n();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [savedIds, setSavedIds] = useState<Record<string, boolean>>({});
  useEffect(() => {
    const id = setTimeout(() => setDebounced(q.trim()), 300);
    return () => clearTimeout(id);
  }, [q]);
  const { data, isFetching, error } = useQuery({
    queryKey: ["search", debounced],
    enabled: debounced.length >= 2,
    queryFn: async () => {
      const r = await fetch(`/api/search?q=${encodeURIComponent(debounced)}`);
      if (!r.ok) throw new Error(t("common.error"));
      return (await r.json()).results as Result[];
    },
  });
  async function toggleSave(id: string) {
    const r = await fetch("/api/saved", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ questionId: id }) });
    if (r.ok) { const d = await r.json(); setSavedIds((s) => ({ ...s, [id]: d.saved })); }
  }
  return (
    <div>
      <label className="relative block">
        <span className="sr-only">{t("search.placeholder")}</span>
        <Search className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
        <input autoFocus className="input h-12 pl-10 text-base" placeholder={t("search.placeholder")} value={q} onChange={(e) => setQ(e.target.value)} data-testid="search-input" />
        {isFetching && <Spinner className="absolute right-3 top-3.5 text-accent" />}
      </label>
      <div className="mt-5">
        {debounced.length < 2 ? (
          <p className="text-sm text-muted-foreground">{t("search.hint")}</p>
        ) : error ? (
          <p className="text-danger">{(error as Error).message}</p>
        ) : data && data.length === 0 ? (
          <EmptyState title={t("search.empty")} />
        ) : data ? (
          <>
            <p className="mb-3 text-sm text-muted-foreground">{t("search.results", { n: data.length })}</p>
            <ul className="space-y-3" data-testid="search-results">
              {data.map((r) => (
                <li key={r.id}>
                  <Card className="flex gap-3 p-4">
                    {r.signCode && <SignIcon code={r.signCode} className="h-12 w-12 shrink-0" />}
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone="muted">{c(r.category.name)}</Badge>
                        {r.tickets.map((n) => <Badge key={n} tone="accent">№{n}</Badge>)}
                        <span className="ml-auto text-xs text-muted-foreground">{r.code}</span>
                      </div>
                      <p className="mt-1.5 font-medium">{c(r.text)}</p>
                      <details className="mt-1.5">
                        <summary className="cursor-pointer text-sm font-semibold text-accent">{t("modal.title")}</summary>
                        <p className="mt-1 flex gap-1.5 text-sm text-success"><CheckCircle2 className="h-4 w-4 shrink-0" />{c(r.correct ?? "")}</p>
                        {r.ruleRef && <p className="text-xs text-muted-foreground">{t("search.ruleRef")}: {c(r.ruleRef)}</p>}
                      </details>
                    </div>
                    <button onClick={() => toggleSave(r.id)} aria-label={t("test.save")} className="self-start rounded p-1 hover:bg-muted">
                      <Star className={savedIds[r.id] ? "h-5 w-5 fill-warning text-warning" : "h-5 w-5 text-muted-foreground"} />
                    </button>
                  </Card>
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>
    </div>
  );
}
