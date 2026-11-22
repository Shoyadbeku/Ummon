import { getSettings } from "@/lib/settings";
import { PageHeader } from "@/components/ui/misc";
import { SettingsForm } from "@/components/admin/settings-form";

export default async function SettingsPage() {
  return (
    <div>
      <PageHeader title="Sozlamalar" subtitle="Imtihon rejimi parametrlari va savollar ko'rinishi" />
      <SettingsForm initial={await getSettings()} />
    </div>
  );
}
