import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface BarConfig {
  dataKey: string;
  color: string;
  name?: string;
  stackId?: string;
}

interface Props {
  data: Record<string, unknown>[];
  xKey: string;
  bars: BarConfig[];
  xLabel?: string;
  yLabel?: string;
}

export function DashboardBarChart({ data, xKey, bars, xLabel, yLabel }: Props) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 12, fill: '#6b7280' }}
          label={xLabel ? { value: xLabel, position: 'insideBottom', offset: -5, fontSize: 12, fill: '#9ca3af' } : undefined}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#6b7280' }}
          tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)}
          label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fontSize: 12, fill: '#9ca3af' } : undefined}
        />
        <Tooltip
          contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
          formatter={(value) => [Number(value).toLocaleString(), '']}
        />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
        {bars.map((bar) => (
          <Bar
            key={bar.dataKey}
            dataKey={bar.dataKey}
            fill={bar.color}
            name={bar.name || bar.dataKey}
            radius={[4, 4, 0, 0]}
            stackId={bar.stackId}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
