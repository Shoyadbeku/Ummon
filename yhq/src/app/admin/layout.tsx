import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { AdminNav } from "@/components/admin/admin-nav";

export const metadata: Metadata = { title: "Admin panel", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/kirish?next=/admin");
  if (user.role !== "ADMIN") redirect("/");
  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <AdminNav />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
