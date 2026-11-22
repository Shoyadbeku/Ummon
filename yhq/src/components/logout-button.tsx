"use client";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LogoutButton({ label }: { label: string }) {
  const router = useRouter();
  return (
    <Button variant="outline" onClick={async () => { await fetch("/api/auth/logout", { method: "POST" }); router.push("/"); router.refresh(); }}>
      <LogOut className="h-4 w-4" />{label}
    </Button>
  );
}
