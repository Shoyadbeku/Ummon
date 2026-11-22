import { cn } from "@/lib/utils";

export function Card({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("card", className)} {...p} />;
}

type Tone = "default" | "success" | "danger" | "warning" | "accent" | "muted";
const tones: Record<Tone, string> = {
  default: "bg-primary/10 text-primary dark:text-primary",
  success: "bg-success-soft text-success",
  danger: "bg-danger-soft text-danger",
  warning: "bg-warning-soft text-warning",
  accent: "bg-accent/10 text-accent",
  muted: "bg-muted text-muted-foreground",
};

export function Badge({ tone = "default", className, ...p }: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold", tones[tone], className)} {...p} />;
}

export function Progress({ value, className, tone = "accent", label }: { value: number; className?: string; tone?: "accent" | "success" | "danger"; label?: string }) {
  const color = tone === "success" ? "bg-success" : tone === "danger" ? "bg-danger" : "bg-accent";
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)} role="progressbar" aria-valuenow={Math.round(v)} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      <div className={cn("h-full rounded-full transition-[width] duration-500", color)} style={{ width: `${v}%` }} />
    </div>
  );
}

export function PageHeader({ title, subtitle, children }: { title: string; subtitle?: string; children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1.5 max-w-2xl text-muted-foreground">{subtitle}</p>}
      </div>
      {children && <div className="flex flex-wrap gap-2">{children}</div>}
    </div>
  );
}

export function Stat({ label, value, icon, tone }: { label: string; value: React.ReactNode; icon?: React.ReactNode; tone?: "success" | "danger" | "accent" }) {
  const t = tone === "success" ? "text-success" : tone === "danger" ? "text-danger" : tone === "accent" ? "text-accent" : "";
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">{icon}{label}</div>
      <div className={cn("mt-1 text-2xl font-bold tabular-nums", t)}>{value}</div>
    </Card>
  );
}

export function EmptyState({ icon, title, children }: { icon?: React.ReactNode; title: string; children?: React.ReactNode }) {
  return (
    <Card className="flex flex-col items-center gap-3 p-10 text-center">
      {icon && <div className="text-muted-foreground">{icon}</div>}
      <p className="font-medium">{title}</p>
      {children}
    </Card>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <span className={cn("inline-block h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent", className)} aria-hidden />;
}
