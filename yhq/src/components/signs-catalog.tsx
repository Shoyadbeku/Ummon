"use client";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useI18n } from "@/lib/i18n/client";
import { Card } from "@/components/ui/misc";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { SignIcon } from "@/components/sign-icon";
import { cn } from "@/lib/utils";

type Sign = { code: string; group: string; name: string; meaning: string; usage: string | null; ruleRef: string | null; imageUrl: string | null };
const GROUPS = ["WARNING", "PRIORITY", "PROHIBITORY", "MANDATORY", "INFORMATION", "SERVICE", "ADDITIONAL"] as const;

function SignImage({ s, className }: { s: Sign; className?: string }) {
  // eslint-disable-next-line @next/next/no-img-element
  if (s.imageUrl) return <img src={s.imageUrl} alt={s.name} className={cn("object-contain", className)} loading="lazy" />;
  return <SignIcon code={s.code} className={className} title={s.name} />;
}

export function SignsCatalog({ signs }: { signs: Sign[] }) {
  const { t, c } = useI18n();
  const [q, setQ] = useState("");
  const [group, setGroup] = useState<string>("ALL");
  const [active, setActive] = useState<Sign | null>(null);
  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    return signs.filter((x) => (group === "ALL" || x.group === group) && (!s || x.code.startsWith(s) || x.name.toLowerCase().includes(s) || x.meaning.toLowerCase().includes(s)));
  }, [signs, q, group]);
  const groups = GROUPS.filter((g) => filtered.some((s) => s.group === g));

  return (
    <div>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <label className="relative flex-1">
          <span className="sr-only">{t("signs.search")}</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input className="input pl-9" placeholder={t("signs.search")} value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <div className="flex gap-1.5 overflow-x-auto pb-1">
          {["ALL", ...GROUPS.filter((g) => signs.some((s) => s.group === g))].map((g) => (
            <button key={g} onClick={() => setGroup(g)} className={cn("shrink-0 rounded-full border px-3 py-1.5 text-sm font-medium", group === g ? "border-accent bg-accent text-accent-foreground" : "bg-card hover:bg-muted")}>
              {g === "ALL" ? t("tickets.filter.all") : t(`signs.group.${g}` as never).replace(/ belgilari$| знаки$/, "")}
            </button>
          ))}
        </div>
      </div>
      {groups.map((g) => (
        <section key={g} className="mb-8">
          <h2 className="mb-3 text-lg font-bold">{t(`signs.group.${g}` as never)}</h2>
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {filtered.filter((s) => s.group === g).map((s) => (
              <li key={s.code}>
                <button onClick={() => setActive(s)} className="w-full text-left">
                  <Card className="flex h-full flex-col items-center gap-2 p-4 text-center transition hover:-translate-y-0.5 hover:shadow-md">
                    <SignImage s={s} className="h-20 w-20" />
                    <span className="text-xs font-semibold text-muted-foreground">{s.code}</span>
                    <span className="text-sm font-semibold leading-tight">{c(s.name)}</span>
                  </Card>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
      <Dialog open={!!active} onOpenChange={(o) => !o && setActive(null)}>
        {active && (
          <DialogContent title={`${active.code} — ${c(active.name)}`} closeLabel={t("modal.close")}>
            <div className="space-y-4 p-5">
              <SignImage s={active} className="mx-auto h-36 w-36" />
              <section><h3 className="font-semibold">{t("signs.meaning")}</h3><p className="mt-1 text-sm">{c(active.meaning)}</p></section>
              {active.usage && <section><h3 className="font-semibold">{t("signs.usage")}</h3><p className="mt-1 text-sm">{c(active.usage)}</p></section>}
              {active.ruleRef && <section className="rounded-md bg-muted p-3 text-sm"><span className="font-semibold">{t("signs.rule")}: </span>{c(active.ruleRef)} · <a href="https://lex.uz/docs/-5953883" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">lex.uz ↗</a></section>}
            </div>
          </DialogContent>
        )}
      </Dialog>
    </div>
  );
}
