"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, ClipboardList, FileQuestion, FileUp, Library, Settings, Users } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/admin", label: "Statistika", icon: BarChart3, exact: true },
  { href: "/admin/savollar", label: "Savollar", icon: FileQuestion },
  { href: "/admin/biletlar", label: "Biletlar", icon: ClipboardList },
  { href: "/admin/import", label: "Import", icon: FileUp },
  { href: "/admin/manbalar", label: "Manbalar", icon: Library },
  { href: "/admin/foydalanuvchilar", label: "Foydalanuvchilar", icon: Users },
  { href: "/admin/sozlamalar", label: "Sozlamalar", icon: Settings },
];

export function AdminNav() {
  const p = usePathname();
  return (
    <aside className="lg:w-56 lg:shrink-0">
      <nav className="flex gap-1 overflow-x-auto rounded-lg border bg-card p-1.5 lg:sticky lg:top-20 lg:flex-col" aria-label="Admin">
        {items.map((i) => {
          const active = i.exact ? p === i.href : p.startsWith(i.href);
          return (
            <Link key={i.href} href={i.href} className={cn("flex shrink-0 items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium hover:bg-muted", active && "bg-primary text-primary-foreground hover:bg-primary")}>
              <i.icon className="h-4 w-4" />{i.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
