import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const DEFAULT_COLORS = ['#3B82F6', '#14B8A6', '#F59E0B', '#F97316', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

interface Props {
  data: { name: string; value: number }[];
  colors?: string[];
  innerRadius?: number;
  showLabels?: boolean;
}

export function DashboardPieChart({ data, colors = DEFAULT_COLORS, innerRadius = 60, showLabels = false }: Props) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius="80%"
          paddingAngle={2}
          dataKey="value"
          label={showLabels ? (props: { name?: string; percent?: number }) => `${props.name ?? ''} ${((props.percent ?? 0) * 100).toFixed(0)}%` : undefined}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={colors[i % colors.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
          formatter={(value) => [Number(value).toLocaleString(), '']}
        />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
