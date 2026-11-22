import Link from "next/link";
import { BarChart3, BookOpen, CheckCircle2, ClipboardList, GraduationCap, Info, ListChecks, Repeat, Shapes, Smartphone, Timer, TriangleAlert } from "lucide-react";
import { getT } from "@/lib/i18n/server";
import { getHomeStats } from "@/lib/queries";
import { buttonClass } from "@/components/ui/button";
import { Card } from "@/components/ui/misc";
import { SignIcon } from "@/components/sign-icon";
import { YHQ_LAW_URL } from "@/lib/site";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const { t } = await getT();
  const stats = await getHomeStats();
  const steps = [
    { icon: ClipboardList, title: t("home.step1"), text: t("home.step1d") },
    { icon: CheckCircle2, title: t("home.step2"), text: t("home.step2d") },
    { icon: Repeat, title: t("home.step3"), text: t("home.step3d") },
    { icon: GraduationCap, title: t("home.step4"), text: t("home.step4d") },
  ];
  const features = [
    { icon: BookOpen, title: t("home.f.learn"), text: t("home.f.learnd"), href: "/biletlar" },
    { icon: Timer, title: t("home.f.exam"), text: t("home.f.examd"), href: "/imtihon" },
    { icon: TriangleAlert, title: t("home.f.mistakes"), text: t("home.f.mistakesd"), href: "/xatolar" },
    { icon: Shapes, title: t("home.f.signs"), text: t("home.f.signsd"), href: "/belgilar" },
    { icon: BarChart3, title: t("home.f.stats"), text: t("home.f.statsd"), href: "/kabinet" },
    { icon: Smartphone, title: t("home.f.offline"), text: t("home.f.offlined"), href: "/" },
  ];
  return (
    <div className="space-y-14">
      <section className="hero-bg relative -mx-4 overflow-hidden px-6 py-12 text-white sm:mx-0 sm:rounded-3xl sm:px-12 sm:py-16">
        <div className="relative z-10 max-w-2xl animate-fade-in">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold ring-1 ring-white/20">{t("home.badge")}</span>
          <h1 className="mt-4 text-3xl font-extrabold leading-tight tracking-tight sm:text-5xl">{t("home.title")}</h1>
          <p className="mt-4 text-base text-blue-100 sm:text-lg">{t("home.subtitle")}</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/biletlar" className={buttonClass("accent", "lg")}><ListChecks className="h-5 w-5" />{t("home.start")}</Link>
            <Link href="/imtihon" className={buttonClass("outline", "lg", "border-white/30 bg-white/10 text-white hover:bg-white/20")}><Timer className="h-5 w-5" />{t("home.exam")}</Link>
          </div>
        </div>
        <div className="pointer-events-none absolute -right-6 top-6 hidden rotate-6 gap-4 opacity-90 md:grid md:grid-cols-2">
          {["2.1", "1.20", "3.24", "2.5", "4.3", "3.27"].map((c) => <SignIcon key={c} code={c} className="h-24 w-24" />)}
        </div>
        <dl className="relative z-10 mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            [stats.questions, t("home.stats.questions")],
            [stats.tickets, t("home.stats.tickets")],
            [stats.signs, t("home.stats.signs")],
            [stats.topics, t("home.stats.topics")],
          ].map(([v, l]) => (
            <div key={String(l)} className="rounded-xl bg-white/10 p-4 ring-1 ring-white/15">
              <dt className="text-sm text-blue-100">{l}</dt>
              <dd className="text-2xl font-extrabold tabular-nums">{v}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h2 className="mb-5 text-2xl font-bold">{t("home.how")}</h2>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((s, i) => (
            <li key={s.title}>
              <Card className="h-full p-5">
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-full bg-accent/15 font-bold text-accent">{i + 1}</span>
                  <s.icon className="h-5 w-5 text-muted-foreground" />
                </div>
                <h3 className="mt-3 font-semibold">{s.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{s.text}</p>
              </Card>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h2 className="mb-5 text-2xl font-bold">{t("home.features")}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <Link key={f.title} href={f.href} className="group">
              <Card className="h-full p-5 transition group-hover:-translate-y-0.5 group-hover:shadow-md">
                <f.icon className="h-7 w-7 text-accent" />
                <h3 className="mt-3 font-semibold">{f.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{f.text}</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <Card className="flex gap-4 border-warning/40 bg-warning-soft/60 p-5">
          <Info className="mt-0.5 h-6 w-6 shrink-0 text-warning" />
          <div>
            <h2 className="font-semibold">{t("home.disclaimerTitle")}</h2>
            <p className="mt-1 text-sm text-foreground/80">{t("home.disclaimer")}</p>
            <a href={YHQ_LAW_URL} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-sm font-semibold text-accent hover:underline">lex.uz ↗</a>
          </div>
        </Card>
      </section>
    </div>
  );
}
