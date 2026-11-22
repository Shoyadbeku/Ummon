import { PageHeader } from "@/components/ui/misc";
import { UsersClient } from "@/components/admin/users-client";
import { getCurrentUser } from "@/lib/auth";

export default async function UsersPage() {
  const me = await getCurrentUser();
  return (
    <div>
      <PageHeader title="Foydalanuvchilar" subtitle="Rollarni boshqarish, bloklash va o'chirish" />
      <UsersClient meId={me!.id} />
    </div>
  );
}
