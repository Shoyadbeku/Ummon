import { forwardRef } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "accent" | "outline" | "ghost" | "success" | "danger" | "soft";
type Size = "sm" | "md" | "lg" | "icon";

const variants: Record<Variant, string> = {
  primary: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm",
  accent: "bg-accent text-accent-foreground hover:bg-accent/90 shadow-sm",
  outline: "border bg-card hover:bg-muted",
  ghost: "hover:bg-muted",
  success: "bg-success text-success-foreground hover:bg-success/90",
  danger: "bg-danger text-danger-foreground hover:bg-danger/90",
  soft: "bg-accent/10 text-accent hover:bg-accent/20 dark:text-accent",
};
const sizes: Record<Size, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-4 text-sm",
  lg: "h-12 px-6 text-base",
  icon: "h-10 w-10",
};

export function buttonClass(variant: Variant = "primary", size: Size = "md", className?: string) {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-md font-semibold transition-all active:scale-[.98] disabled:pointer-events-none disabled:opacity-50 select-none",
    variants[variant],
    sizes[size],
    className,
  );
}

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size };

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button({ variant, size, className, type = "button", ...props }, ref) {
  return <button ref={ref} type={type} className={buttonClass(variant, size, className)} {...props} />;
});
