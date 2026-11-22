import { PageHeader } from "@/components/ui/misc";
import { SourcesClient } from "@/components/admin/sources-client";

export default function SourcesPage() {
  return (
    <div>
      <PageHeader title="Savol manbalari" subtitle="Rasmiy hujjatlar, rasmiy savollar bazasi va mustaqil mashq manbalari. Faqat tasdiqlangan manbadagi savollar 'rasmiy' deb belgilanishi kerak." />
      <SourcesClient />
    </div>
  );
}
