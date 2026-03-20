import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AreaConfig {
  dataKey: string;
  color: string;
  name?: string;
}

interface Props {
  data: Record<string, unknown>[];
  xKey: string;
  areas: AreaConfig[];
  xLabel?: string;
  yLabel?: string;
}

export function DashboardAreaChart({ data, xKey, areas, xLabel, yLabel }: Props) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <defs>
          {areas.map((area) => (
            <linearGradient key={area.dataKey} id={`gradient-${area.dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={area.color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={area.color} stopOpacity={0.05} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12, fill: '#6b7280' }} label={xLabel ? { value: xLabel, position: 'insideBottom', offset: -5, fontSize: 12, fill: '#9ca3af' } : undefined} />
        <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)} label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fontSize: 12, fill: '#9ca3af' } : undefined} />
        <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} formatter={(value) => [Number(value).toLocaleString(), '']} />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
        {areas.map((area) => (
          <Area key={area.dataKey} type="monotone" dataKey={area.dataKey} stroke={area.color} fill={`url(#gradient-${area.dataKey})`} name={area.name || area.dataKey} strokeWidth={2} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
