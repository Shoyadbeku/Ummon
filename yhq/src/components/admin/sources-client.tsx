"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Pencil, Plus, Trash2 } from "lucide-react";
import { apiFetch } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Badge, Card, Spinner } from "@/components/ui/misc";

type Source = { id: string; name: string; type: string; url: string | null; license: string | null; notes: string | null; verified: boolean; _count: { questions: number } };
const TYPES: Record<string, string> = { OFFICIAL_LAW: "Rasmiy normativ hujjat", OFFICIAL_QUESTION_BANK: "Rasmiy savollar bazasi", ORIGINAL_PRACTICE: "Mustaqil mashq savollari", THIRD_PARTY: "Uchinchi tomon" };
const EMPTY = { name: "", type: "ORIGINAL_PRACTICE", url: "", license: "", notes: "", verified: false };

export function SourcesClient() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["sources"], queryFn: () => apiFetch<Source[]>("/api/admin/sources") });
  const [edit, setEdit] = useState<(typeof EMPTY & { id?: string }) | null>(null);
  const [err, setErr] = useState<string | null>(null);
  async function save() {
    if (!edit) return;
    setErr(null);
    try {
      const { id, ...body } = edit;
      await apiFetch(id ? `/api/admin/sources/${id}` : "/api/admin/sources", { method: id ? "PUT" : "POST", body });
      setEdit(null); qc.invalidateQueries({ queryKey: ["sources"] });
    } catch (e) { setErr((e as Error).message); }
  }
  async function remove(id: string) {
    if (!confirm("Manbani o'chirasizmi? Savollardagi bog'lanish uziladi.")) return;
    await apiFetch(`/api/admin/sources/${id}`, { method: "DELETE" }); qc.invalidateQueries({ queryKey: ["sources"] });
  }
  if (isLoading) return <Spinner />;
  return (
    <div className="space-y-4">
      <Button variant="accent" onClick={() => setEdit({ ...EMPTY })}><Plus className="h-4 w-4" />Yangi manba</Button>
      {edit && (
        <Card className="grid gap-3 p-5 sm:grid-cols-2">
          <label className="space-y-1 sm:col-span-2"><span className="label">Nomi</span><input className="input" value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></label>
          <label className="space-y-1"><span className="label">Turi</span><select className="input" value={edit.type} onChange={(e) => setEdit({ ...edit, type: e.target.value })}>{Object.entries(TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
          <label className="space-y-1"><span className="label">Havola</span><input className="input" value={edit.url} onChange={(e) => setEdit({ ...edit, url: e.target.value })} /></label>
          <label className="space-y-1"><span className="label">Foydalanish shartlari / litsenziya</span><input className="input" value={edit.license} onChange={(e) => setEdit({ ...edit, license: e.target.value })} /></label>
          <label className="flex items-center gap-2 pt-6 text-sm font-medium"><input type="checkbox" checked={edit.verified} onChange={(e) => setEdit({ ...edit, verified: e.target.checked })} />Manba tasdiqlangan</label>
          <label className="space-y-1 sm:col-span-2"><span className="label">Izoh</span><textarea className="textarea" value={edit.notes} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} /></label>
          {err && <p className="text-sm text-danger sm:col-span-2">{err}</p>}
          <div className="flex gap-2 sm:col-span-2"><Button variant="accent" onClick={save}>Saqlash</Button><Button variant="outline" onClick={() => setEdit(null)}>Bekor qilish</Button></div>
        </Card>
      )}
      {data?.map((s) => (
        <Card key={s.id} className="p-4">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{s.name}</h3>
            <Badge tone="muted">{TYPES[s.type]}</Badge>
            {s.verified ? <Badge tone="success"><CheckCircle2 className="h-3 w-3" />Tasdiqlangan</Badge> : <Badge tone="warning">Tasdiqlanmagan</Badge>}
            <span className="ml-auto text-sm text-muted-foreground">{s._count.questions} ta savol</span>
            <Button size="icon" variant="ghost" aria-label="Tahrirlash" onClick={() => setEdit({ id: s.id, name: s.name, type: s.type, url: s.url ?? "", license: s.license ?? "", notes: s.notes ?? "", verified: s.verified })}><Pencil className="h-4 w-4" /></Button>
            <Button size="icon" variant="ghost" aria-label="O'chirish" onClick={() => remove(s.id)}><Trash2 className="h-4 w-4" /></Button>
          </div>
          {s.url && <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-sm text-accent hover:underline">{s.url}</a>}
          {s.notes && <p className="mt-1 text-sm text-muted-foreground">{s.notes}</p>}
        </Card>
      ))}
    </div>
  );
}
