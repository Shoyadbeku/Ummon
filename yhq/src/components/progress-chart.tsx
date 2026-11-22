"use client";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function ProgressChart({ data }: { data: { n: number; percent: number; date: string }[] }) {
  return (
    <div className="h-56 w-full" role="img" aria-label={`O'zlashtirish grafigi: oxirgi ${data.length} ta test`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.4} />
              <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="n" tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} unit="%" />
          <Tooltip
            contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8 }}
            formatter={(v) => [`${v}%`, "Natija"]}
            labelFormatter={(n) => `Test #${n}`}
          />
          <Area type="monotone" dataKey="percent" stroke="hsl(var(--accent))" strokeWidth={2.5} fill="url(#g)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
