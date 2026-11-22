// Savol formasi uchun turlar va bo'sh qiymat (server komponentlarda ham ishlatiladi, shuning uchun alohida modul)
export type Opt = { text: string; isCorrect: boolean; explanation: string };
export type QuestionFormData = {
  id?: string;
  code: string;
  text: string;
  explanation: string;
  imageUrl: string;
  signCode: string;
  scene: string;
  categorySlug: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  sourceId: string;
  ruleRef: string;
  ruleUrl: string;
  origin: "OFFICIAL" | "PRACTICE";
  verificationStatus: "UNVERIFIED" | "IN_REVIEW" | "VERIFIED" | "REJECTED";
  isActive: boolean;
  reviewNote: string;
  options: Opt[];
  tickets?: number[];
};

export const EMPTY_QUESTION: QuestionFormData = {
  code: "", text: "", explanation: "", imageUrl: "", signCode: "", scene: "", categorySlug: "", difficulty: "MEDIUM", sourceId: "",
  ruleRef: "", ruleUrl: "https://lex.uz/docs/-5953883", origin: "PRACTICE", verificationStatus: "UNVERIFIED", isActive: true, reviewNote: "",
  options: [{ text: "", isCorrect: true, explanation: "" }, { text: "", isCorrect: false, explanation: "" }, { text: "", isCorrect: false, explanation: "" }],
};

