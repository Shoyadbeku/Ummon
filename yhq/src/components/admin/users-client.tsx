"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Badge, Card, Spinner } from "@/components/ui/misc";

type U = { id: string; name: string; email: string; role: "USER" | "ADMIN"; isBlocked: boolean; createdAt: string; _count: { attempts: number } };

export function UsersClient({ meId }: { meId: string }) {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["users", q], queryFn: () => apiFetch<U[]>(`/api/admin/users?q=${encodeURIComponent(q)}`) });
  const [err, setErr] = useState<string | null>(null);
  async function patch(id: string, body: Partial<U>) {
    setErr(null);
    try { await apiFetch(`/api/admin/users/${id}`, { method: "PATCH", body }); qc.invalidateQueries({ queryKey: ["users"] }); } catch (e) { setErr((e as Error).message); }
  }
  async function remove(id: string) {
    if (!confirm("Foydalanuvchi va uning barcha natijalari o'chiriladi. Davom etasizmi?")) return;
    try { await apiFetch(`/api/admin/users/${id}`, { method: "DELETE" }); qc.invalidateQueries({ queryKey: ["users"] }); } catch (e) { setErr((e as Error).message); }
  }
  return (
    <div>
      <input className="input mb-4 max-w-sm" placeholder="Ism yoki email…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Qidiruv" />
      {err && <p className="mb-3 text-sm text-danger" role="alert">{err}</p>}
      {isLoading ? <Spinner /> : (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground"><tr><th className="p-3">Foydalanuvchi</th><th className="p-3">Rol</th><th className="p-3">Testlar</th><th className="p-3">Ro'yxatdan o'tgan</th><th className="p-3" /></tr></thead>
            <tbody className="divide-y">
              {data?.map((u) => (
                <tr key={u.id}>
                  <td className="p-3"><div className="font-medium">{u.name} {u.isBlocked && <Badge tone="danger">bloklangan</Badge>}</div><div className="text-muted-foreground">{u.email}</div></td>
                  <td className="p-3"><Badge tone={u.role === "ADMIN" ? "accent" : "muted"}>{u.role}</Badge></td>
                  <td className="p-3">{u._count.attempts}</td>
                  <td className="p-3">{u.createdAt.slice(0, 10)}</td>
                  <td className="p-3">
                    {u.id !== meId && (
                      <div className="flex flex-wrap justify-end gap-1">
                        <Button size="sm" variant="outline" onClick={() => patch(u.id, { role: u.role === "ADMIN" ? "USER" : "ADMIN" })}>{u.role === "ADMIN" ? "Adminlikdan olish" : "Admin qilish"}</Button>
                        <Button size="sm" variant="outline" onClick={() => patch(u.id, { isBlocked: !u.isBlocked })}>{u.isBlocked ? "Blokdan chiqarish" : "Bloklash"}</Button>
                        <Button size="sm" variant="danger" onClick={() => remove(u.id)}>O'chirish</Button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
