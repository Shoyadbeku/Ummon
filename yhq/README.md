# YHQ Mashq — haydovchilik nazariy imtihoniga tayyorlov platformasi

O'zbekiston Respublikasi Yo'l harakati qoidalari (VM 2022-yil 12-apreldagi 172-son qarori, [lex.uz](https://lex.uz/docs/-5953883)) asosidagi test platformasi: biletlar, o'quv va imtihon rejimlari, to'g'ri javob oynasi, xatolar ustida ishlash, yo'l belgilari, shaxsiy kabinet va admin panel.

## Savollar bazasi haqida (muhim)

- Bazadagi **228 ta savol mustaqil tuzilgan mashq savollari**, rasmiy imtihon savollari emas. Har biri YHQ matnining aniq bandiga havola qiladi (`ruleRef`, `ruleUrl`).
- Barcha savollar `origin = PRACTICE`, `verificationStatus = UNVERIFIED` holatida. Saytda "Mashq savoli · Ekspert tekshiruvi kutilmoqda" deb ko'rsatiladi. Avtomaktab o'qituvchisi tekshirgach, admin panelda "Tekshirilgan" holatiga o'tkazing.
- Birinchi tibbiy yordam savollari umumqabul qilingan tavsiyalarga asoslangan; tibbiyot mutaxassisi tekshirishi kerak.
- Rasmiy imtihon savollarining ochiq va qonuniy foydalanish mumkin bo'lgan bazasi topilmadi. Rasmiy savollar faqat tasdiqlangan manba (`Manbalar` bo'limi) bilan `OFFICIAL` sifatida qo'shilishi mumkin — validatsiya buni majburiy qiladi.
- Imtihon formati (20 savol / 25 daqiqa / 2 xato) norasmiy manbalardan olingan standart qiymat; admin `Sozlamalar`da o'zgartiradi va "rasmiy tekshirilgan" belgisini faqat rasmiy manbadan tekshirgach qo'yadi.
- Yo'l belgilari tasvirlari sxematik SVG (rasmiy ko'rinish uchun 1-ilovaga qarang); admin o'z rasmlarini yuklashi mumkin.

## Texnologiyalar

Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS (shadcn uslubidagi komponentlar, Radix Dialog) · Lucide · PostgreSQL + Prisma 6 · Zod · TanStack Query · Recharts · Vitest · Playwright · Docker.

Autentifikatsiya: bcrypt (12 raund) + ma'lumotlar bazasidagi sessiyalar (tasodifiy token, bazada SHA-256 xeshi, httpOnly cookie), rolga asoslangan ruxsat (USER/ADMIN), login rate-limit, Origin tekshiruvi (CSRF), xavfsizlik headerlari. Javoblar faqat serverda tekshiriladi; imtihon rejimida to'g'ri javoblar test yakunlanguncha mijozga yuborilmaydi, taymer serverda ham nazorat qilinadi.

## Arxitektura

```
prisma/
  schema.prisma          Users, Sessions, Categories, QuestionSources, Questions, AnswerOptions,
                         Tickets, TicketQuestions, TestAttempts, UserAnswers, UserProgress,
                         SavedQuestion, TrafficSigns, AppSettings, AuditLog
  data/                  savollar (questions-1..3.ts) va yo'l belgilari (signs.ts)
  seed.ts                idempotent seed: mavzular, manbalar, belgilar, savollar, biletlar, admin
src/lib/
  attempts.ts            test mexanizmi: boshlash, javob, javobni ko'rsatish, yakunlash, natija
  tickets.ts             biletlarni shakllantirish algoritmi (planTickets) va bilet holati
  grading.ts             natijani hisoblash, "xatolarim" qoidasi
  admin/import.ts        CSV/XLSX/JSON import, validatsiya, takrorlarni aniqlash
  admin/questions.ts     savol CRUD, takroriy savolni aniqlash, audit
  auth.ts, actor.ts      sessiyalar; mehmon (cookie) natijalarini hisobga ko'chirish
  i18n/                  o'zbek (lotin), kirill (avtomatik), rus interfeysi
src/app/                 sahifalar va /api route handler'lar
src/components/test/     TestRunner, AnswerModal (to'g'ri javob oynasi), SceneView (chorraha sxemalari)
tests/unit, tests/e2e    Vitest va Playwright testlari
```

**Bilet algoritmi:** savollar mavzular bo'yicha guruhlanadi, guruh ichida deterministik aralashtiriladi, so'ng navbatma-navbat (round-robin) yoyilib 10 talik bo'laklarga bo'linadi. Har bir bilet aniq 10 ta, turli mavzulardan savoldan iborat; qoldiq bilet qilinmaydi (tasodifiy va mavzu testlarida ishlatiladi). Admin "yangilaridan qo'shish" yoki "qaytadan tuzish" mumkin, biletni qo'lda ham tahrirlaydi (10 ta sharti tekshiriladi).

**Xatolarim:** noto'g'ri javob (yoki o'quv rejimida javobsiz oldindan ko'rilgan savol) ro'yxatga tushadi, ketma-ket 2 marta to'g'ri ishlanganda chiqadi.

**Mehmon rejimi:** natijalar brauzerga bog'langan httpOnly cookie identifikatori bilan saqlanadi; ro'yxatdan o'tganda yoki kirganda hisobga ko'chiriladi.

## Lokal ishga tushirish

Talablar: Node.js 22, PostgreSQL 16.

```bash
cd yhq
cp .env.example .env            # DATABASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD ni sozlang
npm ci
npx prisma migrate deploy       # sxemani yaratish
npm run db:seed                 # savollar, biletlar, belgilar, administrator
npm run dev                     # http://localhost:3000
```

Admin panel: `/admin` (seed'dagi `ADMIN_EMAIL` / `ADMIN_PASSWORD`).

## Testlar

```bash
npm test                        # unit testlar (Vitest)
npm run typecheck
npm run build
# E2E (alohida test bazasi kerak, masalan yhq_test):
TEST_DATABASE_URL=postgresql://yhq:yhq@localhost:5432/yhq_test npm run test:e2e
```

E2E test bazasiga `prisma migrate deploy` va seed qo'llaydi (bazani o'chirmaydi); testlar noyob ma'lumotlar bilan ishlaydi.

## Production'ga joylash

### Docker Compose

```bash
cd yhq
cat > .env <<'ENV'
POSTGRES_PASSWORD=kuchli-parol
ADMIN_EMAIL=admin@sizning-domen.uz
ADMIN_PASSWORD=juda-kuchli-parol
NEXT_PUBLIC_SITE_NAME="YHQ Mashq"
NEXT_PUBLIC_SITE_URL=https://sizning-domen.uz
ENV
docker compose up -d --build
```

Konteyner ishga tushganda migratsiyalar va idempotent seed avtomatik bajariladi (`RUN_SEED=false` bilan o'chiriladi). Yuklangan rasmlar `uploads` volume'da saqlanadi.

Oldiga HTTPS beruvchi reverse proxy qo'ying (Caddy, Nginx + Let's Encrypt). Production'da cookie'lar `Secure` — HTTPS majburiy (faqat lokal sinov uchun `INSECURE_COOKIES=1`).

### Dockersiz (VPS)

```bash
npm ci && npx prisma migrate deploy && npm run db:seed && npm run build
cp -r .next/static .next/standalone/.next/ && cp -r public .next/standalone/
NODE_ENV=production PORT=3000 node .next/standalone/server.js   # systemd yoki pm2 orqali
```

### Tavsiyalar

- Birinchi kirishdan keyin admin parolini almashtiring; `ADMIN_PASSWORD` ni xavfsiz saqlang.
- PostgreSQL'ning muntazam zaxira nusxasini oling (`pg_dump`) va `uploads` papkasini ham zaxiralang.
- Bir nechta server instansiyasida login rate-limit uchun Redis kabi umumiy xotira ulang (hozirgisi xotirada).

## Ma'lum cheklovlar

- Dockerfile shu ishlab chiqish muhitida build qilib tekshirilmagan (Docker mavjud emas edi); standalone server va migratsiya/seed bosqichlari alohida tekshirilgan.
- Rus tilida faqat interfeys tarjima qilingan; savollar matni uchun `translations.ru` maydoni bor, ammo tarjimalar hali kiritilmagan.
- `npm audit`: Prisma CLI (`effect`, `deepmerge-ts`) va `exceljs` → `uuid` bog'liqliklarida ogohlantirishlar bor; ular runtime'da foydalanuvchi ma'lumotlarini qayta ishlamaydi, yangilanishlar chiqqanda versiyalarni ko'taring.
