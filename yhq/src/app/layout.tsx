import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { getT } from "@/lib/i18n/server";
import { htmlLang } from "@/lib/i18n/core";
import { getCurrentUser } from "@/lib/auth";
import { SITE_NAME, SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: `${SITE_NAME} — YHQ nazariy imtihoniga tayyorgarlik`, template: `%s · ${SITE_NAME}` },
  description: "O'zbekiston haydovchilik guvohnomasi nazariy imtihoniga tayyorgarlik: biletlar, imtihon rejimi, yo'l belgilari, xatolar ustida ishlash. YHQ (VM 172-son qarori) asosida.",
  applicationName: SITE_NAME,
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icons/icon-192.png", apple: "/icons/apple-touch-icon.png" },
  openGraph: { type: "website", siteName: SITE_NAME, locale: "uz_UZ" },
  appleWebApp: { capable: true, title: SITE_NAME, statusBarStyle: "default" },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0b1f4b" },
    { media: "(prefers-color-scheme: dark)", color: "#06122b" },
  ],
};

const themeScript = `(function(){try{var t=localStorage.getItem('theme');var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark')}catch(e){}})()`;

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { locale, t } = await getT();
  const user = await getCurrentUser();
  return (
    <html lang={htmlLang(locale)} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-dvh">
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-card focus:px-4 focus:py-2">Asosiy kontentga o'tish</a>
        <Providers locale={locale}>
          <Header user={user ? { name: user.name, role: user.role } : null} siteName={SITE_NAME} />
          <main id="main" className="container py-6 sm:py-10">{children}</main>
          <Footer t={t} siteName={SITE_NAME} />
        </Providers>
      </body>
    </html>
  );
}
