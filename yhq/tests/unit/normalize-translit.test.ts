import { describe, expect, it } from "vitest";
import { normalizeText, similarity, textHash } from "@/lib/normalize";
import { toCyrillic } from "@/lib/translit";

describe("takrorlarni aniqlash", () => {
  it("apostrof turlari va registr farqi xeshga ta'sir qilmaydi", () => {
    expect(textHash("Yo'l bering!")).toBe(textHash("YOʻL   bering"));
    expect(normalizeText("“Asosiy yo‘l”")).toBe("asosiy yo'l");
  });
  it("o'xshash matnlar yuqori o'xshashlik beradi", () => {
    expect(similarity("Toshkent shahrida ruxsat etilgan eng yuqori tezlik qancha?", "Toshkent shahrida ruxsat etilgan eng yuqori tezlik qancha bo'ladi?")).toBeGreaterThan(0.8);
    expect(similarity("Temir yo'l kesishmasi", "Piyodalar o'tish joyi")).toBeLessThan(0.2);
  });
});

describe("lotin → kirill", () => {
  it("asosiy harflar", () => {
    expect(toCyrillic("Yo'l harakati qoidalari")).toBe("Йўл ҳаракати қоидалари");
    expect(toCyrillic("shahar, choy, g'isht")).toBe("шаҳар, чой, ғишт");
    expect(toCyrillic("ertalab")).toBe("эрталаб");
  });
  it("qisqartmalar, havolalar va belgi kodlari o'zgarmaydi", () => {
    expect(toCyrillic("YHQ 78-band")).toBe("YHQ 78-банд");
    expect(toCyrillic("https://lex.uz/docs/-5953883")).toBe("https://lex.uz/docs/-5953883");
  });
});
