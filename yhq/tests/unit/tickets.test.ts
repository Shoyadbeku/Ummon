import { describe, expect, it } from "vitest";
import { planTickets, QUESTIONS_PER_TICKET, ticketStatus, validateTicketComposition } from "@/lib/tickets";

const make = (n: number, cats = 5) => Array.from({ length: n }, (_, i) => ({ id: `q${String(i).padStart(4, "0")}`, categoryId: `c${i % cats}` }));

describe("planTickets — biletlarni shakllantirish algoritmi", () => {
  it("har bir biletda aniq 10 ta savol bo'ladi", () => {
    const plan = planTickets(make(228, 18));
    expect(plan.tickets).toHaveLength(22);
    for (const t of plan.tickets) expect(t).toHaveLength(QUESTIONS_PER_TICKET);
    expect(plan.leftover).toHaveLength(8);
  });

  it("savollar takrorlanmaydi va hech biri yo'qolmaydi", () => {
    const input = make(137, 7);
    const plan = planTickets(input);
    const all = [...plan.tickets.flat(), ...plan.leftover];
    expect(new Set(all).size).toBe(all.length);
    expect(all.sort()).toEqual(input.map((q) => q.id).sort());
  });

  it("kirishdagi takroriy ID lar olib tashlanadi", () => {
    const input = [...make(20), ...make(20)];
    const plan = planTickets(input);
    expect(plan.tickets).toHaveLength(2);
    expect(new Set(plan.tickets.flat()).size).toBe(20);
  });

  it("biletlar turli mavzulardan iborat bo'ladi (round-robin)", () => {
    const plan = planTickets(make(100, 5));
    for (const t of plan.tickets) {
      const cats = new Set(t.map((id) => Number(id.slice(1)) % 5));
      expect(cats.size).toBe(5);
    }
  });

  it("bir xil seed bilan natija deterministik", () => {
    expect(planTickets(make(50), 7)).toEqual(planTickets(make(50), 7));
  });

  it("10 tadan kam savol bo'lsa bilet yaratilmaydi", () => {
    const plan = planTickets(make(9));
    expect(plan.tickets).toHaveLength(0);
    expect(plan.leftover).toHaveLength(9);
  });
});

describe("validateTicketComposition", () => {
  it("10 ta noyob savolni qabul qiladi", () => {
    expect(validateTicketComposition(make(10).map((q) => q.id))).toBeNull();
  });
  it("10 tadan farqli sonni rad etadi", () => {
    expect(validateTicketComposition(make(9).map((q) => q.id))).toMatch(/aniq 10/);
    expect(validateTicketComposition(make(11).map((q) => q.id))).toMatch(/aniq 10/);
  });
  it("takrorni rad etadi", () => {
    const ids = make(9).map((q) => q.id);
    expect(validateTicketComposition([...ids, ids[0]])).toMatch(/takror/);
  });
});

describe("ticketStatus", () => {
  const d = (m: number) => new Date(2026, 0, 1, 0, m);
  it("urinish bo'lmasa — ishlanmagan", () => expect(ticketStatus([])).toBe("NOT_STARTED"));
  it("oxirgi urinish davom etayotgan bo'lsa — ishlanmoqda", () =>
    expect(ticketStatus([{ status: "FINISHED", wrongCount: 0, startedAt: d(1) }, { status: "IN_PROGRESS", wrongCount: 0, startedAt: d(2) }])).toBe("IN_PROGRESS"));
  it("xatosiz yakunlangan — muvaffaqiyatli", () => expect(ticketStatus([{ status: "FINISHED", wrongCount: 0, startedAt: d(1) }])).toBe("PASSED"));
  it("xato bilan yakunlangan — xatolar bilan", () => expect(ticketStatus([{ status: "FINISHED", wrongCount: 2, startedAt: d(1) }])).toBe("FAILED"));
});
