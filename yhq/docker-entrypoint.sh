#!/bin/sh
set -e
echo "→ Migratsiyalar qo'llanmoqda"
npx prisma migrate deploy
if [ "${RUN_SEED:-true}" = "true" ]; then
  echo "→ Seed (idempotent: mavjud ma'lumotlar o'zgartirilmaydi)"
  npx tsx prisma/seed.ts
fi
echo "→ Server ishga tushmoqda"
exec node server.js
