"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/misc";

type S = { examQuestionCount: number; examTimeMinutes: number; examMaxErrors: number; examFormatVerified: boolean; examFormatNote: string; includeUnverified: boolean };

export function SettingsForm({ initial }: { initial: S }) {
  const [s, setS] = useState(initial);
  const [msg, setMsg] = useState<string | null>(null);
  async function save() {
    setMsg(null);
    try { await apiFetch("/api/admin/settings", { method: "PUT", body: s }); setMsg("Saqlandi ✓"); } catch (e) { setMsg((e as Error).message); }
  }
  const num = (k: keyof S) => (e: React.ChangeEvent<HTMLInputElement>) => setS({ ...s, [k]: Number(e.target.value) });
  return (
    <Card className="max-w-2xl space-y-4 p-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <label className="space-y-1"><span className="label">Savollar soni</span><input type="number" min={5} max={100} className="input" value={s.examQuestionCount} onChange={num("examQuestionCount")} /></label>
        <label className="space-y-1"><span className="label">Vaqt (daqiqa)</span><input type="number" min={1} max={180} className="input" value={s.examTimeMinutes} onChange={num("examTimeMinutes")} /></label>
        <label className="space-y-1"><span className="label">Ruxsat etilgan xatolar</span><input type="number" min={0} max={50} className="input" value={s.examMaxErrors} onChange={num("examMaxErrors")} /></label>
      </div>
      <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={s.examFormatVerified} onChange={(e) => setS({ ...s, examFormatVerified: e.target.checked })} /><span><b>Imtihon formati rasmiy talablar bo'yicha tekshirilgan.</b> Faqat amaldagi DYHXX/IIV talablarini rasmiy manbadan tekshirgandan keyin belgilang.</span></label>
      <label className="block space-y-1"><span className="label">Foydalanuvchiga ko'rsatiladigan format izohi</span><textarea className="textarea" value={s.examFormatNote} onChange={(e) => setS({ ...s, examFormatNote: e.target.value })} /></label>
      <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={s.includeUnverified} onChange={(e) => setS({ ...s, includeUnverified: e.target.checked })} /><span><b>Tekshirilmagan mashq savollarini ko'rsatish.</b> O'chirilsa, foydalanuvchilarga faqat "Tekshirilgan" holatidagi savollar beriladi (rad etilganlar hech qachon ko'rsatilmaydi).</span></label>
      <div className="flex items-center gap-3"><Button variant="accent" onClick={save}>Saqlash</Button>{msg && <span className="text-sm" role="status">{msg}</span>}</div>
    </Card>
  );
}
