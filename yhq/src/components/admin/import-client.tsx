"use client";
import { useState } from "react";
import { FileUp } from "lucide-react";
import { apiFetch } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Badge, Card, Spinner } from "@/components/ui/misc";

type Res = { summary: { total: number; ok: number; invalid: number; duplicate: number; imported: number }; rows: { row: number; status: string; errors: string[]; duplicateOf?: string; preview: string }[] };

export function ImportClient() {
  const [file, setFile] = useState<File | null>(null);
  const [res, setRes] = useState<Res | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "ok" | "invalid" | "duplicate">("all");

  async function send(commit: boolean) {
    if (!file) return;
    setBusy(true); setErr(null);
    const fd = new FormData();
    fd.set("file", file);
    fd.set("commit", commit ? "1" : "0");
    try { setRes(await apiFetch<Res>("/api/admin/import", { form: fd })); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  const rows = res?.rows.filter((r) => filter === "all" || r.status === filter) ?? [];
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center gap-3">
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border px-4 py-2.5 text-sm font-medium hover:bg-muted">
          <FileUp className="h-4 w-4" />{file ? file.name : "Fayl tanlash"}
          <input type="file" accept=".csv,.json,.xlsx" className="sr-only" data-testid="import-file" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setRes(null); }} />
        </label>
        <Button variant="outline" disabled={!file || busy} onClick={() => send(false)} data-testid="import-analyze">{busy && <Spinner className="h-4 w-4" />}Tahlil qilish</Button>
        <Button variant="accent" disabled={!file || busy || !res || res.summary.ok === 0 || res.summary.imported > 0} onClick={() => send(true)} data-testid="import-commit">Import qilish ({res?.summary.ok ?? 0})</Button>
      </div>
      {err && <p className="mt-3 rounded-md bg-danger-soft p-3 text-sm text-danger" role="alert">{err}</p>}
      {res && (
        <div className="mt-5">
          <div className="flex flex-wrap gap-2 text-sm" data-testid="import-summary">
            {(["all", "ok", "invalid", "duplicate"] as const).map((k) => (
              <button key={k} onClick={() => setFilter(k)} className={`rounded-full border px-3 py-1 ${filter === k ? "border-accent bg-accent/10" : ""}`}>
                {k === "all" ? `Jami: ${res.summary.total}` : k === "ok" ? `To'g'ri: ${res.summary.ok}` : k === "invalid" ? `Xato: ${res.summary.invalid}` : `Takror: ${res.summary.duplicate}`}
              </button>
            ))}
            {res.summary.imported > 0 && <Badge tone="success">Import qilindi: {res.summary.imported}</Badge>}
          </div>
          <ul className="mt-3 max-h-[480px] divide-y overflow-y-auto rounded-md border text-sm">
            {rows.map((r) => (
              <li key={r.row} className="p-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{r.row}-qator</span>
                  <Badge tone={r.status === "ok" ? "success" : r.status === "invalid" ? "danger" : "warning"}>{r.status === "ok" ? "OK" : r.status === "invalid" ? "Xato" : "Takror"}</Badge>
                  <span className="line-clamp-1 flex-1">{r.preview}</span>
                </div>
                {r.errors.length > 0 && <ul className="mt-1 list-disc pl-5 text-xs text-danger">{r.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>}
                {r.duplicateOf && <p className="mt-1 text-xs text-warning">Takror: {r.duplicateOf}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
