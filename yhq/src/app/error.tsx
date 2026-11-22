"use client";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 text-center" role="alert">
      <AlertTriangle className="h-12 w-12 text-danger" />
      <h1 className="text-xl font-bold">Xatolik yuz berdi</h1>
      <p className="max-w-md text-muted-foreground">Sahifani yuklashda muammo bo'ldi. Internet aloqasini tekshirib, qayta urinib ko'ring.</p>
      {error.digest && <p className="text-xs text-muted-foreground">Kod: {error.digest}</p>}
      <Button onClick={reset}><RefreshCw className="h-4 w-4" />Qayta urinish</Button>
    </div>
  );
}
