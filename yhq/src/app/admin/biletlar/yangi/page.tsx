import { PageHeader } from "@/components/ui/misc";
import { TicketEditor } from "@/components/admin/ticket-editor";

export default function NewTicket() {
  return (
    <div>
      <PageHeader title="Yangi bilet" subtitle="Biletda aniq 10 ta savol bo'lishi shart" />
      <TicketEditor initial={{ number: null, title: "", isPublished: true, questions: [] }} />
    </div>
  );
}
