import Link from "next/link";
import type { TFn } from "@/lib/i18n/core";
import { YHQ_LAW_URL } from "@/lib/site";

export function Footer({ t, siteName }: { t: TFn; siteName: string }) {
  return (
    <footer className="mt-16 border-t py-8 text-sm text-muted-foreground">
      <div className="container flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-xl">
          <p className="font-semibold text-foreground">{siteName}</p>
          <p className="mt-1">{t("footer.disclaimer")}</p>
        </div>
        <nav className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Footer">
          <Link href="/biletlar" className="hover:text-foreground">{t("nav.tickets")}</Link>
          <Link href="/belgilar" className="hover:text-foreground">{t("nav.signs")}</Link>
          <Link href="/qidiruv" className="hover:text-foreground">{t("nav.search")}</Link>
          <a href={YHQ_LAW_URL} target="_blank" rel="noopener noreferrer" className="hover:text-foreground">{t("footer.law")} ↗</a>
        </nav>
      </div>
    </footer>
  );
}
