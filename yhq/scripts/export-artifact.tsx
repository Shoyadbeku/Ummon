// Savollar bazasini Claude Artifact (statik sahifa) uchun JSON ga eksport qiladi:
// npx tsx scripts/export-artifact.tsx  →  artifact/data.json
import { PrismaClient } from "@prisma/client";
import { renderToStaticMarkup } from "react-dom/server";
import { writeFileSync } from "node:fs";
import { SignIcon } from "../src/components/sign-icon";
import { SceneView, type SceneData } from "../src/components/test/scene-view";

const prisma = new PrismaClient();

async function main() {
  const [cats, qs, tickets, signs] = await Promise.all([
    prisma.category.findMany({ orderBy: { order: "asc" } }),
    prisma.question.findMany({
      where: { isActive: true, verificationStatus: { not: "REJECTED" }, code: { startsWith: "Q-" } },
      orderBy: { code: "asc" },
      include: { options: { orderBy: { order: "asc" } }, category: { select: { slug: true } } },
    }),
    prisma.ticket.findMany({ where: { isPublished: true }, orderBy: { number: "asc" }, include: { questions: { orderBy: { position: "asc" }, include: { question: { select: { code: true } } } } } }),
    prisma.trafficSign.findMany({ orderBy: { order: "asc" } }),
  ]);
  const signSvg = (code: string) => renderToStaticMarkup(<SignIcon code={code} className="sign" />);
  const data = {
    generatedAt: new Date().toISOString(),
    law: "https://lex.uz/docs/-5953883",
    categories: cats.map((c) => ({ slug: c.slug, name: c.name, description: c.description })),
    questions: qs.map((q) => ({
      code: q.code,
      cat: q.category.slug,
      d: q.difficulty,
      text: q.text,
      exp: q.explanation,
      rule: q.ruleRef,
      opts: q.options.map((o) => o.text),
      notes: q.options.map((o) => o.explanation),
      a: q.options.findIndex((o) => o.isCorrect),
      sign: q.signCode,
      scene: q.scene ? renderToStaticMarkup(<SceneView scene={q.scene as unknown as SceneData} />) : null,
      firstAid: q.category.slug === "tibbiy",
    })),
    tickets: tickets.filter((t) => t.questions.length === 10).map((t) => ({ n: t.number, q: t.questions.map((x) => x.question.code) })),
    signs: signs.map((s) => ({ code: s.code, group: s.group, name: s.name, meaning: s.meaning, usage: s.usage, rule: s.ruleRef })),
    signSvg: Object.fromEntries([...new Set([...signs.map((s) => s.code), ...qs.map((q) => q.signCode).filter(Boolean) as string[]])].map((c) => [c, signSvg(c)])),
  };
  const bad = data.questions.filter((q) => q.a < 0);
  if (bad.length) throw new Error("To'g'ri javobsiz savollar: " + bad.map((b) => b.code).join(","));
  const json = JSON.stringify(data);
  writeFileSync("artifact/data.json", json);
  console.log(`questions=${data.questions.length} tickets=${data.tickets.length} signs=${data.signs.length} bytes=${json.length}`);
}
main().finally(() => prisma.$disconnect());
