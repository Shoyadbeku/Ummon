"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ImagePlus, Plus, Save, Trash2, X } from "lucide-react";
import { apiFetch, ApiClientError } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Card, Spinner } from "@/components/ui/misc";
import { SignIcon } from "@/components/sign-icon";
import { optionLabel } from "@/lib/utils";

import type { QuestionFormData, Opt } from "./question-form-data";

export function QuestionForm({ initial, categories, sources }: { initial: QuestionFormData; categories: { slug: string; name: string }[]; sources: { id: string; name: string; type: string; verified: boolean }[] }) {
  const router = useRouter();
  const [f, setF] = useState<QuestionFormData>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dups, setDups] = useState<{ id: string; code: string; text: string; score: number }[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const set = <K extends keyof QuestionFormData>(k: K, v: QuestionFormData[K]) => setF((p) => ({ ...p, [k]: v }));
  const setOpt = (i: number, patch: Partial<Opt>) => setF((p) => ({ ...p, options: p.options.map((o, j) => (j === i ? { ...o, ...patch } : patch.isCorrect ? { ...o, isCorrect: false } : o)) }));

  async function upload(file: File) {
    setUploading(true);
    try {
      const fd = new FormData();
      fd.set("file", file);
      const r = await apiFetch<{ url: string }>("/api/admin/upload", { form: fd });
      set("imageUrl", r.url);
    } catch (e) { setError((e as Error).message); } finally { setUploading(false); }
  }

  async function save(force = false) {
    setSaving(true); setError(null); setDups(null);
    let scene: unknown = null;
    if (f.scene.trim()) {
      try { scene = JSON.parse(f.scene); } catch { setError("Vaziyat (scene) JSON noto'g'ri"); setSaving(false); return; }
    }
    const body = {
      ...f, scene, force,
      code: f.code || undefined, sourceId: f.sourceId || null, imageUrl: f.imageUrl || null, signCode: f.signCode || null,
      ruleRef: f.ruleRef || null, ruleUrl: f.ruleUrl || null, reviewNote: f.reviewNote || null,
      options: f.options.map((o) => ({ text: o.text, isCorrect: o.isCorrect, explanation: o.explanation || null })),
    };
    try {
      const r = await apiFetch<{ id: string }>(f.id ? `/api/admin/questions/${f.id}` : "/api/admin/questions", { method: f.id ? "PUT" : "POST", body });
      router.push(`/admin/savollar/${r.id}?saved=1`);
      router.refresh();
      if (f.id) setError(null);
    } catch (e) {
      if (e instanceof ApiClientError && e.status === 409 && e.data.duplicates) setDups(e.data.duplicates as never);
      else setError((e as Error).message);
    } finally { setSaving(false); }
  }

  async function remove() {
    if (!f.id || !confirm("Savolni o'chirasizmi? Bu savol bo'lgan biletlar nashrdan olinadi.")) return;
    try { await apiFetch(`/api/admin/questions/${f.id}`, { method: "DELETE" }); router.push("/admin/savollar"); router.refresh(); }
    catch (e) { setError((e as Error).message); }
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); save(); }} className="space-y-5">
      <Card className="space-y-4 p-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Kod (bo'sh qoldirilsa avtomatik)"><input className="input" value={f.code} onChange={(e) => set("code", e.target.value)} placeholder="Q-0001" /></Field>
          <Field label="Mavzu *">
            <select className="input" required value={f.categorySlug} onChange={(e) => set("categorySlug", e.target.value)}>
              <option value="">Tanlang…</option>
              {categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Qiyinlik">
            <select className="input" value={f.difficulty} onChange={(e) => set("difficulty", e.target.value as never)}>
              <option value="EASY">Oson</option><option value="MEDIUM">O'rta</option><option value="HARD">Qiyin</option>
            </select>
          </Field>
        </div>
        <Field label="Savol matni *"><textarea className="textarea" required value={f.text} onChange={(e) => set("text", e.target.value)} /></Field>
        <Field label="Tushuntirish (nima uchun to'g'ri) *"><textarea className="textarea" required value={f.explanation} onChange={(e) => set("explanation", e.target.value)} /></Field>
      </Card>

      <Card className="space-y-3 p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Javob variantlari (to'g'ri javobni belgilang)</h2>
          <Button size="sm" variant="outline" disabled={f.options.length >= 6} onClick={() => set("options", [...f.options, { text: "", isCorrect: false, explanation: "" }])}><Plus className="h-4 w-4" />Variant</Button>
        </div>
        {f.options.map((o, i) => (
          <div key={i} className={`rounded-lg border-2 p-3 ${o.isCorrect ? "border-success bg-success-soft" : ""}`}>
            <div className="flex items-start gap-2">
              <label className="mt-2.5 flex items-center gap-1.5 text-sm font-bold">
                <input type="radio" name="correct" checked={o.isCorrect} onChange={() => setOpt(i, { isCorrect: true })} aria-label={`${optionLabel(i)} to'g'ri javob`} />
                {optionLabel(i)})
              </label>
              <div className="flex-1 space-y-2">
                <input className="input" required value={o.text} onChange={(e) => setOpt(i, { text: e.target.value })} placeholder="Variant matni" aria-label={`${optionLabel(i)} variant matni`} />
                {!o.isCorrect && <input className="input h-9 text-sm" value={o.explanation} onChange={(e) => setOpt(i, { explanation: e.target.value })} placeholder="Nima uchun noto'g'ri (ixtiyoriy)" />}
              </div>
              <Button size="icon" variant="ghost" disabled={f.options.length <= 2} onClick={() => set("options", f.options.filter((_, j) => j !== i))} aria-label="Variantni o'chirish"><X className="h-4 w-4" /></Button>
            </div>
          </div>
        ))}
      </Card>

      <Card className="grid gap-4 p-5 sm:grid-cols-2">
        <Field label="Rasm">
          <div className="flex items-center gap-2">
            <input className="input" value={f.imageUrl} onChange={(e) => set("imageUrl", e.target.value)} placeholder="/uploads/…" />
            <label className="inline-flex h-11 shrink-0 cursor-pointer items-center gap-1 rounded-md border px-3 text-sm hover:bg-muted">
              {uploading ? <Spinner className="h-4 w-4" /> : <ImagePlus className="h-4 w-4" />}Yuklash
              <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="sr-only" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
            </label>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {f.imageUrl && <img src={f.imageUrl} alt="" className="mt-2 max-h-40 rounded border" />}
        </Field>
        <Field label="Yo'l belgisi kodi (masalan 2.4)">
          <div className="flex items-center gap-3"><input className="input" value={f.signCode} onChange={(e) => set("signCode", e.target.value)} />{f.signCode && <SignIcon code={f.signCode} className="h-12 w-12 shrink-0" />}</div>
        </Field>
        <Field label="YHQ bandi"><input className="input" value={f.ruleRef} onChange={(e) => set("ruleRef", e.target.value)} placeholder="YHQ 78-band" /></Field>
        <Field label="Manba havolasi"><input className="input" type="url" value={f.ruleUrl} onChange={(e) => set("ruleUrl", e.target.value)} /></Field>
        <div className="sm:col-span-2">
          <Field label="Vaziyat sxemasi (JSON, ixtiyoriy)">
            <textarea className="textarea font-mono text-xs" value={f.scene} onChange={(e) => set("scene", e.target.value)} placeholder='{"layout":"cross","vehicles":[{"id":"A","from":"S","to":"N"}]}' />
          </Field>
        </div>
      </Card>

      <Card className="grid gap-4 p-5 sm:grid-cols-2">
        <Field label="Kelib chiqishi">
          <select className="input" value={f.origin} onChange={(e) => set("origin", e.target.value as never)}>
            <option value="PRACTICE">Mustaqil mashq savoli</option>
            <option value="OFFICIAL">Rasmiy imtihon savoli (manba tasdiqlangan bo'lishi shart)</option>
          </select>
        </Field>
        <Field label="Manba">
          <select className="input" value={f.sourceId} onChange={(e) => set("sourceId", e.target.value)}>
            <option value="">—</option>
            {sources.map((s) => <option key={s.id} value={s.id}>{s.name}{s.verified ? " ✓" : ""}</option>)}
          </select>
        </Field>
        <Field label="Tekshiruv holati">
          <select className="input" value={f.verificationStatus} onChange={(e) => set("verificationStatus", e.target.value as never)}>
            <option value="UNVERIFIED">Tekshirilmagan</option><option value="IN_REVIEW">Tekshiruvda</option><option value="VERIFIED">Tekshirilgan</option><option value="REJECTED">Rad etilgan (foydalanuvchilarga ko'rinmaydi)</option>
          </select>
        </Field>
        <label className="flex items-center gap-2 pt-7 text-sm font-medium"><input type="checkbox" checked={f.isActive} onChange={(e) => set("isActive", e.target.checked)} />Faol (foydalanuvchilarga ko'rsatiladi)</label>
        <div className="sm:col-span-2"><Field label="Tekshiruv izohi"><input className="input" value={f.reviewNote} onChange={(e) => set("reviewNote", e.target.value)} /></Field></div>
        {f.tickets && f.tickets.length > 0 && <p className="text-sm text-muted-foreground sm:col-span-2">Biletlarda: {f.tickets.map((n) => `№${n}`).join(", ")}</p>}
      </Card>

      {dups && (
        <Card className="border-warning bg-warning-soft p-4 text-sm" role="alert">
          <p className="font-semibold">O'xshash savollar topildi:</p>
          <ul className="mt-2 list-disc pl-5">{dups.map((d) => <li key={d.id}><a className="text-accent underline" href={`/admin/savollar/${d.id}`} target="_blank">{d.code}</a> — {d.text.slice(0, 100)} ({Math.round(d.score * 100)}%)</li>)}</ul>
          <Button size="sm" variant="outline" className="mt-3" onClick={() => save(true)}>Baribir saqlash</Button>
        </Card>
      )}
      {error && <p className="rounded-md bg-danger-soft p-3 text-sm text-danger" role="alert">{error}</p>}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" variant="accent" disabled={saving} data-testid="save-question">{saving ? <Spinner className="h-4 w-4" /> : <Save className="h-4 w-4" />}Saqlash</Button>
        {f.id && <Button variant="danger" onClick={remove}><Trash2 className="h-4 w-4" />O'chirish</Button>}
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block space-y-1.5"><span className="label">{label}</span>{children}</label>;
}
