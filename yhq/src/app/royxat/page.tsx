import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthForm } from "@/components/auth-form";

export const metadata: Metadata = { title: "Ro'yxatdan o'tish", robots: { index: false } };

export default function Page() {
  return (
    <div className="py-6">
      <Suspense>
        <AuthForm mode="register" />
      </Suspense>
    </div>
  );
}
