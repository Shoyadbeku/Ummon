import Link from "next/link";
import { buttonClass } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 text-center">
      <p className="text-6xl font-extrabold text-accent">404</p>
      <h1 className="text-xl font-bold">Sahifa topilmadi</h1>
      <p className="text-muted-foreground">Siz izlagan sahifa mavjud emas yoki o'chirilgan.</p>
      <Link href="/" className={buttonClass("primary")}>Bosh sahifa</Link>
    </div>
  );
}
