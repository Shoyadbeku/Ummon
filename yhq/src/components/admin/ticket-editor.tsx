"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowDown, ArrowUp, Plus, Save, Search, Trash2, X } from "lucide-react";
import { apiFetch } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Badge, Card, Spinner } from "@/components/ui/misc";

type Q = { id: string; code: string; text: string; category?: { name: string } };

export function TicketEditor({ id, initial }: { id?: string; initial: { number: number | null; title: string; isPublished: boolean; questions: Q[] } }) {
  const router = useRouter();
  const [number, setNumber] = useState<string>(initial.number ? String(initial.number) : "");
  const [title, setTitle] = useState(initial.title);
  const [published, setPublished] = useState(initial.isPublished);
  const [qs, setQs] = useState<Q[]>(initial.questions);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Q[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (search.trim().length < 2) { setResults([]); return; }
    const t = setTimeout(async () => {
      const r = await apiFetch<{ items: Q[] }>(`/api/admin/questions?q=${encodeURIComponent(search)}`).catch(() => ({ items: [] }));
      setResults(r.items);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const move = (i: number, d: number) => setQs((p) => { const a = [...p]; const j = i + d; if (j < 0 || j >= a.length) return a; [a[i], a[j]] = [a[j], a[i]]; return a; });

  async function save() {
    setBusy(true); setErr(null);
    try {
      const body = { number: number ? Number(number) : undefined, title: title || null, isPublished: published, questionIds: qs.map((q) => q.id) };
      await apiFetch(id ? `/api/admin/tickets/${id}` : "/api/admin/tickets", { method: id ? "PUT" : "POST", body });
      router.push("/admin/biletlar"); router.refresh();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  async function remove() {
    if (!id || !confirm("Biletni o'chirasizmi?")) return;
    await apiFetch(`/api/admin/tickets/${id}`, { method: "DELETE" }); router.push("/admin/biletlar"); router.refresh();
  }

  return (
    <div className="space-y-5">
      <Card className="grid gap-4 p-5 sm:grid-cols-3">
        <label className="space-y-1.5"><span className="label">Raqami</span><input className="input" type="number" min={1} value={number} onChange={(e) => setNumber(e.target.value)} placeholder="avtomatik" /></label>
        <label className="space-y-1.5"><span className="label">Sarlavha (ixtiyoriy)</span><input className="input" value={title} onChange={(e) => setTitle(e.target.value)} /></label>
        <label className="flex items-center gap-2 pt-7 text-sm font-medium"><input type="checkbox" checked={published} onChange={(e) => setPublished(e.target.checked)} />Nashr etilgan</label>
      </Card>
      <Card className="p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Savollar</h2>
          <Badge tone={qs.length === 10 ? "success" : "danger"}>{qs.length}/10</Badge>
        </div>
        <ol className="space-y-2">
          {qs.map((q, i) => (
            <li key={q.id} className="flex items-center gap-2 rounded-md border p-2 text-sm">
              <span className="w-6 text-center font-semibold">{i + 1}</span>
              <span className="font-mono text-xs text-accent">{q.code}</span>
              <span className="line-clamp-1 flex-1">{q.text}</span>
              <Button size="icon" variant="ghost" onClick={() => move(i, -1)} aria-label="Yuqoriga"><ArrowUp className="h-4 w-4" /></Button>
              <Button size="icon" variant="ghost" onClick={() => move(i, 1)} aria-label="Pastga"><ArrowDown className="h-4 w-4" /></Button>
              <Button size="icon" variant="ghost" onClick={() => setQs(qs.filter((x) => x.id !== q.id))} aria-label="Olib tashlash"><X className="h-4 w-4" /></Button>
            </li>
          ))}
        </ol>
        <div className="mt-4">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input className="input pl-9" placeholder="Savol qo'shish: matn yoki kod bo'yicha qidiring…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </label>
          {results.length > 0 && (
            <ul className="mt-2 max-h-72 divide-y overflow-y-auto rounded-md border text-sm">
              {results.map((r) => {
                const added = qs.some((q) => q.id === r.id);
                return (
                  <li key={r.id} className="flex items-center gap-2 p-2">
                    <span className="font-mono text-xs text-accent">{r.code}</span><span className="line-clamp-1 flex-1">{r.text}</span>
                    <Button size="sm" variant="soft" disabled={added || qs.length >= 10} onClick={() => setQs([...qs, r])}><Plus className="h-4 w-4" /></Button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </Card>
      {err && <p className="rounded-md bg-danger-soft p-3 text-sm text-danger" role="alert">{err}</p>}
      <div className="flex gap-2">
        <Button variant="accent" onClick={save} disabled={busy || qs.length !== 10}>{busy ? <Spinner className="h-4 w-4" /> : <Save className="h-4 w-4" />}Saqlash</Button>
        {id && <Button variant="danger" onClick={remove}><Trash2 className="h-4 w-4" />O'chirish</Button>}
      </div>
    </div>
  );
}
