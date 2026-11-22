"use client";
import * as D from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Dialog = D.Root;
export const DialogTrigger = D.Trigger;
export const DialogClose = D.Close;

export function DialogContent({ className, children, title, description, closeLabel = "Yopish" }: { className?: string; children: React.ReactNode; title: React.ReactNode; description?: React.ReactNode; closeLabel?: string }) {
  return (
    <D.Portal>
      <D.Overlay className="fixed inset-0 z-50 flex items-end justify-center bg-navy-950/60 backdrop-blur-sm data-[state=open]:animate-fade-in sm:items-center sm:p-4">
      <D.Content
        className={cn(
          "relative flex max-h-[92dvh] w-full flex-col overflow-hidden border bg-card text-card-foreground shadow-2xl data-[state=open]:animate-scale-in",
          "rounded-t-2xl sm:max-w-xl sm:rounded-2xl",
          className,
        )}
      >
        <div className="flex items-start justify-between gap-4 border-b px-5 py-4">
          <div>
            <D.Title className="text-lg font-bold">{title}</D.Title>
            {description ? <D.Description className="text-sm text-muted-foreground">{description}</D.Description> : <D.Description className="sr-only">{typeof title === "string" ? title : ""}</D.Description>}
          </div>
          <D.Close className="rounded-md p-1.5 text-muted-foreground hover:bg-muted" aria-label={closeLabel}>
            <X className="h-5 w-5" />
          </D.Close>
        </div>
        <div className="overflow-y-auto">{children}</div>
      </D.Content>
      </D.Overlay>
    </D.Portal>
  );
}
