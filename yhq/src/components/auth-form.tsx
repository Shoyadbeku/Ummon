"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "@/lib/i18n/client";
import { Button } from "@/components/ui/button";
import { Card, Spinner } from "@/components/ui/misc";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { t } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const fd = new FormData(e.currentTarget);
    const body = Object.fromEntries(fd.entries());
    try {
      const res = await fetch(`/api/auth/${mode}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = Array.isArray(data.details) ? data.details.map((d: { message: string }) => d.message).join(". ") : "";
        throw new Error(detail || data.error || t("common.error"));
      }
      const next = params.get("next");
      router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : data.user?.role === "ADMIN" ? "/admin" : "/kabinet");
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  }

  const isLogin = mode === "login";
  return (
    <Card className="mx-auto w-full max-w-md p-6 sm:p-8 animate-scale-in">
      <h1 className="text-2xl font-bold">{isLogin ? t("auth.loginTitle") : t("auth.registerTitle")}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{t("auth.guestMerge")}</p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate={false}>
        {!isLogin && (
          <div className="space-y-1.5">
            <label htmlFor="name" className="label">{t("auth.name")}</label>
            <input id="name" name="name" required minLength={2} maxLength={80} autoComplete="name" className="input" />
          </div>
        )}
        <div className="space-y-1.5">
          <label htmlFor="email" className="label">{t("auth.email")}</label>
          <input id="email" name="email" type="email" required autoComplete="email" className="input" />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="password" className="label">{t("auth.password")}</label>
          <input id="password" name="password" type="password" required minLength={isLogin ? 1 : 8} autoComplete={isLogin ? "current-password" : "new-password"} className="input" />
          {!isLogin && <p className="text-xs text-muted-foreground">{t("auth.passwordHint")}</p>}
        </div>
        {error && <p className="rounded-md bg-danger-soft p-3 text-sm text-danger" role="alert">{error}</p>}
        <Button type="submit" variant="accent" className="w-full" disabled={loading}>
          {loading && <Spinner className="h-4 w-4" />}{isLogin ? t("auth.submitLogin") : t("auth.submitRegister")}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-muted-foreground">
        {isLogin ? t("auth.noAccount") : t("auth.haveAccount")}{" "}
        <Link href={isLogin ? "/royxat" : "/kirish"} className="font-semibold text-accent hover:underline">{isLogin ? t("nav.register") : t("nav.login")}</Link>
      </p>
    </Card>
  );
}
