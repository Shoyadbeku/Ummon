"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { BookOpen, Car, ClipboardList, GraduationCap, LayoutDashboard, LogIn, LogOut, Menu, Moon, Search, Shapes, Sun, TriangleAlert, User, X, Shuffle } from "lucide-react";
import { useI18n } from "@/lib/i18n/client";
import { LOCALES, LOCALE_SHORT, LOCALE_LABELS, type Locale } from "@/lib/i18n/dict";
import { cn } from "@/lib/utils";
import { buttonClass } from "@/components/ui/button";

type HeaderUser = { name: string; role: "USER" | "ADMIN" } | null;

export function Header({ user, siteName }: { user: HeaderUser; siteName: string }) {
  const { t, locale } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  useEffect(() => setOpen(false), [pathname]);

  const nav = [
    { href: "/biletlar", label: t("nav.tickets"), icon: ClipboardList },
    { href: "/imtihon", label: t("nav.exam"), icon: GraduationCap },
    { href: "/mavzular", label: t("nav.topics"), icon: BookOpen },
    { href: "/belgilar", label: t("nav.signs"), icon: Shapes },
    { href: "/xatolar", label: t("nav.mistakes"), icon: TriangleAlert },
  ];
  const extra = [
    { href: "/tasodifiy", label: t("nav.random"), icon: Shuffle },
    { href: "/qidiruv", label: t("nav.search"), icon: Search },
  ];

  async function setLocale(l: Locale) {
    await fetch("/api/lang", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ locale: l }) });
    router.refresh();
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/");
    router.refresh();
  }

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="container flex h-16 items-center gap-3">
        <Link href="/" className="flex items-center gap-2 font-extrabold tracking-tight" aria-label={siteName}>
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary text-primary-foreground shadow"><Car className="h-5 w-5" /></span>
          <span className="hidden text-lg sm:inline">{siteName}</span>
        </Link>
        <nav className="ml-4 hidden items-center gap-1 lg:flex" aria-label="Asosiy">
          {nav.map((n) => (
            <Link key={n.href} href={n.href} className={cn("rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground", isActive(n.href) && "bg-muted text-foreground")}>
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-1">
          <Link href="/qidiruv" className={buttonClass("ghost", "icon", "hidden sm:inline-flex")} aria-label={t("nav.search")}><Search className="h-5 w-5" /></Link>
          <LangSwitch locale={locale} onChange={setLocale} label={t("lang.label")} />
          <ThemeToggle label={t("theme.toggle")} />
          {user ? (
            <>
              {user.role === "ADMIN" && (
                <Link href="/admin" className={buttonClass("ghost", "icon", "hidden sm:inline-flex")} aria-label={t("nav.admin")} title={t("nav.admin")}><LayoutDashboard className="h-5 w-5" /></Link>
              )}
              <Link href="/kabinet" className={buttonClass("soft", "sm", "hidden sm:inline-flex")}><User className="h-4 w-4" />{user.name.split(" ")[0]}</Link>
            </>
          ) : (
            <Link href="/kirish" className={buttonClass("primary", "sm", "hidden sm:inline-flex")}><LogIn className="h-4 w-4" />{t("nav.login")}</Link>
          )}
          <button className={buttonClass("ghost", "icon", "lg:hidden")} onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-label={t("nav.menu")}>
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>
      {open && (
        <div className="border-t bg-background lg:hidden animate-fade-in">
          <nav className="container grid gap-1 py-3" aria-label="Mobil">
            {[...nav, ...extra].map((n) => (
              <Link key={n.href} href={n.href} className={cn("flex items-center gap-3 rounded-md px-3 py-3 font-medium hover:bg-muted", isActive(n.href) && "bg-muted")}>
                <n.icon className="h-5 w-5 text-accent" />{n.label}
              </Link>
            ))}
            <div className="my-2 border-t" />
            {user ? (
              <>
                <Link href="/kabinet" className="flex items-center gap-3 rounded-md px-3 py-3 font-medium hover:bg-muted"><User className="h-5 w-5 text-accent" />{t("nav.cabinet")}</Link>
                {user.role === "ADMIN" && <Link href="/admin" className="flex items-center gap-3 rounded-md px-3 py-3 font-medium hover:bg-muted"><LayoutDashboard className="h-5 w-5 text-accent" />{t("nav.admin")}</Link>}
                <button onClick={logout} className="flex items-center gap-3 rounded-md px-3 py-3 text-left font-medium hover:bg-muted"><LogOut className="h-5 w-5 text-danger" />{t("nav.logout")}</button>
              </>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Link href="/kirish" className={buttonClass("primary")}>{t("nav.login")}</Link>
                <Link href="/royxat" className={buttonClass("outline")}>{t("nav.register")}</Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

function LangSwitch({ locale, onChange, label }: { locale: Locale; onChange: (l: Locale) => void; label: string }) {
  return (
    <label className="relative">
      <span className="sr-only">{label}</span>
      <select
        value={locale}
        onChange={(e) => onChange(e.target.value as Locale)}
        className="h-10 cursor-pointer appearance-none rounded-md bg-transparent px-2 text-sm font-semibold hover:bg-muted"
        aria-label={label}
      >
        {LOCALES.map((l) => (
          <option key={l} value={l} title={LOCALE_LABELS[l]}>{LOCALE_SHORT[l]}</option>
        ))}
      </select>
    </label>
  );
}

function ThemeToggle({ label }: { label: string }) {
  const [dark, setDark] = useState<boolean | null>(null);
  useEffect(() => setDark(document.documentElement.classList.contains("dark")), []);
  function toggle() {
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    try { localStorage.setItem("theme", next ? "dark" : "light"); } catch {}
    setDark(next);
  }
  return (
    <button onClick={toggle} className={buttonClass("ghost", "icon")} aria-label={label} title={label}>
      {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}
