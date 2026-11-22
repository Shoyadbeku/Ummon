"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { I18nProvider } from "@/lib/i18n/client";
import type { Locale } from "@/lib/i18n/dict";

export function Providers({ locale, children }: { locale: Locale; children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 2, refetchOnWindowFocus: false, staleTime: 10_000 },
          mutations: { retry: 1 },
        },
      }),
  );
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, []);
  return (
    <QueryClientProvider client={client}>
      <I18nProvider locale={locale}>{children}</I18nProvider>
    </QueryClientProvider>
  );
}
