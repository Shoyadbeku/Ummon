"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Download, Plus, Search } from "lucide-react";
import { apiFetch } from "@/lib/fetcher";
import { Badge, Card, Spinner } from "@/components/ui/misc";
import { Button, buttonClass } from "@/components/ui/button";

type Row = { id: string; code: string; text: string; origin: string; verificationStatus: string; isActive: boolean; difficulty: string; ruleRef: string | null; category: { name: string }; _count: { tickets: number } };
const STATUS_TONE: Record<string, "success" | "warning" | "danger" | "muted"> = { VERIFIED: "success", IN_REVIEW: "warning", UNVERIFIED: "muted", REJECTED: "danger" };
export const STATUS_LABEL: Record<string, string> = { VERIFIED: "Tekshirilgan", IN_REVIEW: "Tekshiruvda", UNVERIFIED: "Tekshirilmagan", REJECTED: "Rad etilgan" };

export function QuestionsTable({ categories }: { categories: { slug: string; name: string }[] }) {
  const [q, setQ] = useState("");
  const [dq, setDq] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [origin, setOrigin] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => { const t = setTimeout(() => { setDq(q); setPage(1); }, 300); return () => clearTimeout(t); }, [q]);
  const params = new URLSearchParams({ q: dq, category, status, origin, page: String(page) });
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-questions", params.toString()],
    queryFn: () => apiFetch<{ total: number; pages: number; items: Row[] }>(`/api/admin/questions?${params}`),
  });
  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        <label className="relative min-w-[200px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input className="input pl-9" placeholder="Matn, kod yoki YHQ bandi…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Qidiruv" />
        </label>
        <select className="input w-auto" value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }} aria-label="Mavzu">
          <option value="">Barcha mavzular</option>
          {categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
        </select>
        <select className="input w-auto" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Holat">
          <option value="">Barcha holatlar</option>
          {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className="input w-auto" value={origin} onChange={(e) => { setOrigin(e.target.value); setPage(1); }} aria-label="Turi">
          <option value="">Rasmiy + mashq</option>
          <option value="OFFICIAL">Rasmiy</option>
          <option value="PRACTICE">Mashq</option>
        </select>
        <Link href="/admin/savollar/yangi" className={buttonClass("accent")}><Plus className="h-4 w-4" />Yangi savol</Link>
        <a href="/api/admin/export" className={buttonClass("outline")}><Download className="h-4 w-4" />JSON eksport</a>
      </div>
      {isLoading ? <Spinner /> : error ? <p className="text-danger">{(error as Error).message}</p> : data && (
        <>
          <p className="mb-2 text-sm text-muted-foreground">Jami: {data.total}</p>
          <Card className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                <tr><th className="p-3">Kod</th><th className="p-3">Savol</th><th className="p-3">Mavzu</th><th className="p-3">Holat</th><th className="p-3">Bilet</th></tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((r) => (
                  <tr key={r.id} className="hover:bg-muted/40">
                    <td className="whitespace-nowrap p-3 font-mono"><Link href={`/admin/savollar/${r.id}`} className="text-accent hover:underline">{r.code}</Link></td>
                    <td className="p-3"><Link href={`/admin/savollar/${r.id}`} className="line-clamp-2 hover:underline">{r.text}</Link>{!r.isActive && <Badge tone="danger" className="ml-1">nofaol</Badge>}</td>
                    <td className="p-3 text-muted-foreground">{r.category.name}</td>
                    <td className="p-3"><div className="flex flex-col gap-1"><Badge tone={STATUS_TONE[r.verificationStatus]}>{STATUS_LABEL[r.verificationStatus]}</Badge><Badge tone={r.origin === "OFFICIAL" ? "success" : "accent"}>{r.origin === "OFFICIAL" ? "Rasmiy" : "Mashq"}</Badge></div></td>
                    <td className="p-3 text-center">{r._count.tickets}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          <div className="mt-4 flex items-center justify-center gap-2">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>←</Button>
            <span className="text-sm">{page} / {Math.max(1, data.pages)}</span>
            <Button size="sm" variant="outline" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>→</Button>
          </div>
        </>
      )}
    </div>
  );
}
