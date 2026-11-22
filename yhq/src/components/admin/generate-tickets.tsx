"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Wand2 } from "lucide-react";
import { apiFetch } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/misc";

export function GenerateTickets({ unassigned }: { unassigned: number }) {
  const router = useRouter();
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function run(mode: "append" | "rebuild") {
    if (mode === "rebuild" && !confirm("Barcha biletlar o'chirilib, qaytadan tuziladi. Foydalanuvchilarning bilet bo'yicha holatlari yangilanadi. Davom etasizmi?")) return;
    setBusy(true); setMsg(null);
    try {
      const r = await apiFetch<{ created: number; leftover: number }>("/api/admin/tickets/generate", { body: { mode } });
      setMsg(`${r.created} ta bilet yaratildi. ${r.leftover} ta savol 10 talik biletga yetmadi (tasodifiy/mavzu testlarida ishlatiladi).`);
      router.refresh();
    } catch (e) { setMsg((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <Card className="p-5">
      <h2 className="flex items-center gap-2 font-semibold"><Wand2 className="h-5 w-5 text-accent" />Avtomatik shakllantirish</h2>
      <p className="mt-1 text-sm text-muted-foreground">Algoritm savollarni mavzular bo'yicha navbatma-navbat taqsimlaydi: har bir biletda aniq 10 ta, turli mavzulardan savol bo'ladi. 10 taga to'lmagan qoldiq bilet qilinmaydi.</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button variant="accent" disabled={busy || unassigned < 10} onClick={() => run("append")}>Yangi savollardan bilet qo'shish ({Math.floor(unassigned / 10)})</Button>
        <Button variant="outline" disabled={busy} onClick={() => run("rebuild")}>Barchasini qaytadan tuzish</Button>
      </div>
      {msg && <p className="mt-3 text-sm" role="status">{msg}</p>}
    </Card>
  );
}
