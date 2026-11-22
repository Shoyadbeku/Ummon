import { PrismaClient, type Difficulty } from "@prisma/client";
import bcrypt from "bcryptjs";
import { SIGNS } from "./data/signs";
import { QUESTIONS_1 } from "./data/questions-1";
import { QUESTIONS_2 } from "./data/questions-2";
import { QUESTIONS_3 } from "./data/questions-3";
import type { QSeed } from "./data/types";
import { textHash } from "../src/lib/normalize";
import { planTickets } from "../src/lib/tickets";
import { seededRandom, shuffle } from "../src/lib/utils";

const prisma = new PrismaClient();

export const YHQ_URL = "https://lex.uz/docs/-5953883";

export const CATEGORIES = [
  { slug: "umumiy", name: "Umumiy qoidalar va haydovchi majburiyatlari", nameRu: "Общие положения и обязанности водителя", description: "YHQ 1–3-boblar: hujjatlar, toifalar, kamar, taqiqlar, YTH" },
  { slug: "piyoda", name: "Piyodalar, yo'lovchilar va o'tish joylari", nameRu: "Пешеходы, пассажиры и переходы", description: "YHQ 4, 5, 17-boblar" },
  { slug: "maxsus", name: "Maxsus transport vositalari", nameRu: "Спецтранспорт", description: "YHQ 6-bob" },
  { slug: "svetofor", name: "Svetofor va tartibga soluvchi ishoralari", nameRu: "Сигналы светофора и регулировщика", description: "YHQ 7-bob" },
  { slug: "ishoralar", name: "Ogohlantiruvchi va avariya ishoralari", nameRu: "Предупредительные и аварийные сигналы", description: "YHQ 8-bob" },
  { slug: "manyovr", name: "Manyovr va qatnov qismida joylashuv", nameRu: "Маневрирование и расположение на проезжей части", description: "YHQ 9–10-boblar" },
  { slug: "tezlik", name: "Harakatlanish tezligi", nameRu: "Скорость движения", description: "YHQ 11-bob" },
  { slug: "quvib", name: "Quvib o'tish", nameRu: "Обгон", description: "YHQ 12-bob" },
  { slug: "toxtash", name: "To'xtash va to'xtab turish", nameRu: "Остановка и стоянка", description: "YHQ 13-bob" },
  { slug: "chorraha", name: "Chorrahalardan o'tish", nameRu: "Проезд перекрёстков", description: "YHQ 14–16-boblar" },
  { slug: "temiryol", name: "Temir yo'l kesishmalari", nameRu: "Железнодорожные переезды", description: "YHQ 18-bob" },
  { slug: "magistral", name: "Avtomagistral, turar joy dahasi, nishabliklar", nameRu: "Автомагистрали, жилые зоны, уклоны", description: "YHQ 19–22-boblar" },
  { slug: "yoritish", name: "Tashqi yoritish asboblari", nameRu: "Внешние световые приборы", description: "YHQ 23-bob" },
  { slug: "shatak", name: "Shatakka olish, odam va yuk tashish", nameRu: "Буксировка, перевозка людей и грузов", description: "YHQ 24–27-boblar" },
  { slug: "velo", name: "Velosiped, moped va hayvonlar", nameRu: "Велосипеды, мопеды и животные", description: "YHQ 28-bob" },
  { slug: "belgilar", name: "Yo'l belgilari", nameRu: "Дорожные знаки", description: "YHQ 1-ilova" },
  { slug: "tibbiy", name: "Birinchi tibbiy yordam", nameRu: "Первая помощь", description: "YTHda birinchi yordam asoslari" },
  { slug: "texnik", name: "Transport vositasining texnik holati", nameRu: "Техническое состояние ТС", description: "YHQ 11–12-bandlar" },
];

const DIFF: Record<QSeed["d"], Difficulty> = { E: "EASY", M: "MEDIUM", H: "HARD" };

function ruleRefOf(r: string) {
  return r.startsWith("1-ilova") ? `YHQ, ${r}` : `YHQ ${r}-band`;
}

async function main() {
  console.log("→ Kategoriyalar");
  const catIds: Record<string, string> = {};
  for (const [i, c] of CATEGORIES.entries()) {
    const row = await prisma.category.upsert({
      where: { slug: c.slug },
      create: { ...c, order: i },
      update: { name: c.name, nameRu: c.nameRu, description: c.description, order: i },
    });
    catIds[c.slug] = row.id;
  }

  console.log("→ Manbalar");
  const law = await upsertSource("src-yhq-172", {
    name: "O'zbekiston Respublikasi Yo'l harakati qoidalari (VM 2022-yil 12-apreldagi 172-son qarori)",
    type: "OFFICIAL_LAW",
    url: YHQ_URL,
    license: "Rasmiy normativ-huquqiy hujjat (mualliflik huquqi obyekti hisoblanmaydi)",
    notes: "Savollardagi barcha bandlar shu hujjatning lex.uz dagi amaldagi tahririga havola qiladi.",
    verified: true,
  });
  const practice = await upsertSource("src-original-practice", {
    name: "Mustaqil tuzilgan mashq savollari (YHQ asosida)",
    type: "ORIGINAL_PRACTICE",
    url: YHQ_URL,
    license: "Platformaning original kontenti",
    notes: "Rasmiy imtihon savollari EMAS. YHQ matni asosida tuzilgan, ekspert (avtomaktab o'qituvchisi) tekshiruvini kutmoqda.",
    verified: false,
  });
  const firstAid = await upsertSource("src-first-aid", {
    name: "Birinchi tibbiy yordam bo'yicha umumqabul qilingan tavsiyalar",
    type: "ORIGINAL_PRACTICE",
    url: null,
    license: "Platformaning original kontenti",
    notes: "YHQ 13-band birinchi yordam ko'rsatish majburiyatini belgilaydi; usullar umumiy tavsiyalarga asoslangan va tibbiyot mutaxassisi tomonidan tekshirilishi kerak.",
    verified: false,
  });

  console.log("→ Yo'l belgilari");
  for (const [i, s] of SIGNS.entries()) {
    await prisma.trafficSign.upsert({
      where: { code: s.code },
      create: { ...s, order: i },
      update: { ...s, order: i },
    });
  }

  console.log("→ Savollar");
  const all = [...QUESTIONS_1, ...QUESTIONS_2, ...QUESTIONS_3];
  let created = 0;
  for (const [i, q] of all.entries()) {
    const code = `Q-${String(i + 1).padStart(4, "0")}`;
    const exists = await prisma.question.findUnique({ where: { code } });
    if (exists) continue;
    if (!catIds[q.c]) throw new Error(`Noma'lum kategoriya: ${q.c} (${code})`);
    if (q.a < 0 || q.a >= q.o.length) throw new Error(`To'g'ri javob indeksi noto'g'ri: ${code}`);
    const rand = seededRandom(1000 + i);
    const opts = shuffle(
      q.o.map((text, idx) => ({ text, isCorrect: idx === q.a, explanation: q.n?.[idx] ?? null })),
      rand,
    );
    await prisma.question.create({
      data: {
        code,
        text: q.q,
        explanation: q.e,
        signCode: q.sign ?? null,
        scene: q.scene ?? undefined,
        categoryId: catIds[q.c],
        difficulty: DIFF[q.d],
        sourceId: q.c === "tibbiy" ? firstAid.id : practice.id,
        ruleRef: ruleRefOf(q.r),
        ruleUrl: YHQ_URL,
        origin: "PRACTICE",
        verificationStatus: "UNVERIFIED",
        textHash: textHash(q.q + " " + q.o.join(" ")),
        options: { create: opts.map((o, order) => ({ ...o, order })) },
      },
    });
    created++;
  }
  console.log(`  ${created} ta yangi savol (jami ${all.length})`);
  void law;

  console.log("→ Biletlar");
  const ticketCount = await prisma.ticket.count();
  if (ticketCount === 0) {
    const qs = await prisma.question.findMany({ where: { isActive: true }, select: { id: true, categoryId: true } });
    const plan = planTickets(qs);
    for (const [i, ids] of plan.tickets.entries()) {
      await prisma.ticket.create({
        data: {
          number: i + 1,
          questions: { create: ids.map((questionId, position) => ({ questionId, position })) },
        },
      });
    }
    console.log(`  ${plan.tickets.length} ta bilet, ${plan.leftover.length} ta savol biletdan tashqarida`);
  } else {
    console.log(`  Biletlar mavjud (${ticketCount}) — o'zgartirilmadi`);
  }

  console.log("→ Administrator");
  const email = (process.env.ADMIN_EMAIL ?? "admin@example.com").toLowerCase();
  const password = process.env.ADMIN_PASSWORD ?? "change-me-now-123";
  const admin = await prisma.user.findUnique({ where: { email } });
  if (!admin) {
    await prisma.user.create({
      data: { email, name: "Administrator", role: "ADMIN", passwordHash: await bcrypt.hash(password, 12) },
    });
    console.log(`  Yaratildi: ${email}`);
  } else {
    console.log(`  Mavjud: ${email}`);
  }
}

async function upsertSource(
  id: string,
  data: { name: string; type: "OFFICIAL_LAW" | "ORIGINAL_PRACTICE"; url: string | null; license: string; notes: string; verified: boolean },
) {
  return prisma.questionSource.upsert({ where: { id }, create: { id, ...data }, update: data });
}

main()
  .then(() => prisma.$disconnect())
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
