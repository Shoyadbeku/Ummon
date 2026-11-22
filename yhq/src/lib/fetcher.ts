// Mijoz tomonidagi JSON so'rovlar uchun yordamchi
export class ApiClientError extends Error {
  constructor(public status: number, message: string, public data: Record<string, unknown> = {}) { super(message); }
}

export async function apiFetch<T = unknown>(url: string, opts: { method?: string; body?: unknown; form?: FormData } = {}): Promise<T> {
  const res = await fetch(url, {
    method: opts.method ?? (opts.body !== undefined || opts.form ? "POST" : "GET"),
    headers: opts.body !== undefined ? { "content-type": "application/json" } : undefined,
    body: opts.form ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const details = Array.isArray(data.details) ? ": " + data.details.map((d: { path?: string[]; message: string }) => `${d.path?.join(".") ?? ""} ${d.message}`).join("; ") : "";
    throw new ApiClientError(res.status, (data.error ?? "Xatolik") + details, data);
  }
  return data as T;
}
