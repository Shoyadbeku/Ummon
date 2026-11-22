"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, type ButtonProps } from "@/components/ui/button";
import { Spinner } from "@/components/ui/misc";

export type StartPayload = {
  kind: "TICKET" | "EXAM" | "RANDOM" | "TOPIC" | "MISTAKES" | "SIGNS" | "FAVORITES";
  mode?: "LEARN" | "EXAM";
  ticketNumber?: number;
  categorySlug?: string;
  count?: number;
};

/** Yangi test urinishini serverda yaratadi va test sahifasiga o'tadi */
export function StartButton({ payload, children, wrapperClassName = "inline-flex flex-col", ...props }: { payload: StartPayload; wrapperClassName?: string } & ButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  async function start() {
    setLoading(true);
    setErr(null);
    try {
      const res = await fetch("/api/attempts", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error ?? "Xatolik");
      router.push(`/test/${data.id}`);
    } catch (e) {
      setErr(navigator.onLine ? (e as Error).message : "Internet aloqasi yo'q");
      setLoading(false);
    }
  }
  return (
    <span className={wrapperClassName}>
      <Button {...props} onClick={start} disabled={loading || props.disabled}>
        {loading && <Spinner className="h-4 w-4" />}
        {children}
      </Button>
      {err && <span className="mt-1 text-xs text-danger" role="alert">{err}</span>}
    </span>
  );
}
