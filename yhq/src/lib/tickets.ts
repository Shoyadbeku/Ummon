import { seededRandom, shuffle } from "./utils";

export const QUESTIONS_PER_TICKET = 10;

export type TicketCandidate = { id: string; categoryId: string; difficulty?: "EASY" | "MEDIUM" | "HARD" };

export type TicketPlan = {
  tickets: string[][];
  /** Biletga sig'magan (10 tadan kam qolgan) savollar — tasodifiy va mavzu testlarida ishlatiladi */
  leftover: string[];
};

/**
 * Biletlarni shakllantirish algoritmi.
 *
 * 1. Savollar mavzu (kategoriya) bo'yicha guruhlanadi va har bir guruh ichida deterministik aralashtiriladi.
 * 2. Guruhlar navbatma-navbat (round-robin) bitta umumiy ro'yxatga yoyiladi — shu sababli har bir
 *    biletga turli mavzulardan savollar tushadi.
 * 3. Ro'yxat ketma-ket 10 talik bo'laklarga bo'linadi. Har bir bilet aniq 10 ta savoldan iborat bo'ladi.
 * 4. 10 taga to'lmagan qoldiq bilet yaratilmaydi, `leftover` sifatida qaytariladi.
 * 5. Bitta biletda bitta savol ikki marta uchramaydi (kirishdagi takrorlar olib tashlanadi).
 */
export function planTickets(candidates: TicketCandidate[], seed = 2022): TicketPlan {
  const seen = new Set<string>();
  const unique = candidates.filter((c) => (seen.has(c.id) ? false : (seen.add(c.id), true)));
  const rand = seededRandom(seed);

  const groups = new Map<string, string[]>();
  for (const c of [...unique].sort((a, b) => a.id.localeCompare(b.id))) {
    const g = groups.get(c.categoryId) ?? [];
    g.push(c.id);
    groups.set(c.categoryId, g);
  }
  const queues = [...groups.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, ids]) => shuffle(ids, rand));

  // Katta guruhlar birinchi bo'lsin — ular biletlarga bir tekisroq tarqaladi
  queues.sort((a, b) => b.length - a.length);

  const spread: string[] = [];
  let remaining = unique.length;
  while (remaining > 0) {
    for (const q of queues) {
      const id = q.shift();
      if (id) {
        spread.push(id);
        remaining--;
      }
    }
  }

  const fullCount = Math.floor(spread.length / QUESTIONS_PER_TICKET);
  const tickets: string[][] = [];
  for (let i = 0; i < fullCount; i++) {
    tickets.push(spread.slice(i * QUESTIONS_PER_TICKET, (i + 1) * QUESTIONS_PER_TICKET));
  }
  return { tickets, leftover: spread.slice(fullCount * QUESTIONS_PER_TICKET) };
}

export function validateTicketComposition(questionIds: string[]): string | null {
  if (questionIds.length !== QUESTIONS_PER_TICKET) return `Biletda aniq ${QUESTIONS_PER_TICKET} ta savol bo'lishi shart (hozir ${questionIds.length} ta)`;
  if (new Set(questionIds).size !== questionIds.length) return "Biletda bir savol ikki marta takrorlangan";
  return null;
}

export type TicketStatus = "NOT_STARTED" | "IN_PROGRESS" | "PASSED" | "FAILED";

export function ticketStatus(
  attempts: { status: "IN_PROGRESS" | "FINISHED" | "EXPIRED"; wrongCount: number; startedAt: Date }[],
): TicketStatus {
  if (!attempts.length) return "NOT_STARTED";
  const latest = [...attempts].sort((a, b) => b.startedAt.getTime() - a.startedAt.getTime())[0];
  if (latest.status === "IN_PROGRESS") return "IN_PROGRESS";
  return latest.wrongCount === 0 && latest.status === "FINISHED" ? "PASSED" : "FAILED";
}
