export default function Loading() {
  return (
    <div className="space-y-4" role="status" aria-label="Yuklanmoqda">
      <div className="h-8 w-56 animate-pulse rounded-md bg-muted" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }, (_, i) => <div key={i} className="h-40 animate-pulse rounded-lg bg-muted" />)}
      </div>
    </div>
  );
}
