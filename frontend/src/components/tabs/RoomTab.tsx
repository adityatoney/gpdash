import { useMemo } from 'react';
import { useRoomData } from '../../hooks/useApi';
import { YEAR_COLORS } from '../../lib/constants';
import { ChartContainer } from '../charts/ChartContainer';
import { DashboardBarChart } from '../charts/BarChart';
import { DashboardLineChart } from '../charts/LineChart';
import { DashboardPieChart } from '../charts/PieDonutChart';
import { LoadingSpinner } from '../common/LoadingSpinner';

export function RoomTab() {
  const { data, isLoading } = useRoomData();

  // Room Type Distribution — donut chart, top 10 + "Other"
  const pieData = useMemo(() => {
    if (!data?.byType) return [];
    const totals = new Map<string, number>();
    data.byType.forEach((d) => {
      totals.set(d.typeName, (totals.get(d.typeName) || 0) + d.count);
    });
    const sorted = [...totals.entries()].sort((a, b) => b[1] - a[1]);
    const top10 = sorted.slice(0, 10).map(([name, value]) => ({ name, value }));
    const otherTotal = sorted.slice(10).reduce((sum, [, v]) => sum + v, 0);
    if (otherTotal > 0) top10.push({ name: 'Other', value: otherTotal });
    return top10;
  }, [data]);

  // Utilization by Year — grouped bar: total rooms + avg occupancy
  const utilizationData = useMemo(() => {
    if (!data?.utilizationByYear) return [];
    return data.utilizationByYear.map((d) => ({
      year: d.year,
      'Total Rooms': d.totalRooms,
      'Avg Occupancy %': d.avgOccupancy != null ? Math.round(d.avgOccupancy * 100) : 0,
    }));
  }, [data]);

  // Rooms per Attendee
  const ratioData = useMemo(() => {
    if (!data?.roomsPerAttendee) return [];
    return data.roomsPerAttendee.map((d) => ({
      year: d.year,
      ratio: d.ratio != null ? Number(d.ratio.toFixed(2)) : 0,
    }));
  }, [data]);

  const ratioBars = useMemo(() => {
    if (!data?.roomsPerAttendee) return [];
    return data.roomsPerAttendee.map((d) => ({
      dataKey: 'ratio',
      color: YEAR_COLORS[d.year] || '#6b7280',
      name: String(d.year),
    }));
  }, [data]);

  // Check-in / Check-out
  const checkInOutData = useMemo(() => {
    if (!data?.checkInOut) return [];
    return data.checkInOut.map((d) => {
      const dt = new Date(d.date);
      return {
        date: dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        'Check-ins': d.checkIns,
        'Check-outs': d.checkOuts,
      };
    });
  }, [data]);

  if (isLoading) {
    return <LoadingSpinner message="Loading room data..." />;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Room Type Distribution */}
        <ChartContainer title="Room Type Distribution" subtitle="Aggregated across all years" isEmpty={pieData.length === 0}>
          <DashboardPieChart data={pieData} />
        </ChartContainer>

        {/* Utilization by Year */}
        <ChartContainer title="Utilization by Year" subtitle="Total rooms and average occupancy" isEmpty={!data?.utilizationByYear?.length}>
          <DashboardBarChart
            data={utilizationData}
            xKey="year"
            bars={[
              { dataKey: 'Total Rooms', color: '#3B82F6', name: 'Total Rooms' },
              { dataKey: 'Avg Occupancy %', color: '#14B8A6', name: 'Avg Occupancy %' },
            ]}
          />
        </ChartContainer>

        {/* Rooms per Attendee */}
        <ChartContainer title="Rooms per Attendee" subtitle="Ratio of rooms to registrations" isEmpty={!data?.roomsPerAttendee?.length}>
          <DashboardBarChart
            data={ratioData}
            xKey="year"
            bars={[{ dataKey: 'ratio', color: '#8B5CF6', name: 'Rooms/Attendee' }]}
          />
        </ChartContainer>

        {/* Check-in / Check-out Clusters */}
        <ChartContainer title="Check-in / Check-out Clusters" subtitle="Daily check-in and check-out counts" isEmpty={!data?.checkInOut?.length}>
          <DashboardLineChart
            data={checkInOutData}
            xKey="date"
            lines={[
              { dataKey: 'Check-ins', color: '#3B82F6', name: 'Check-ins' },
              { dataKey: 'Check-outs', color: '#F97316', name: 'Check-outs' },
            ]}
          />
        </ChartContainer>
      </div>
    </div>
  );
}
