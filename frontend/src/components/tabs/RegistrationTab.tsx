import { useMemo } from 'react';
import { useRegistrationData, useSummaryData } from '../../hooks/useApi';
import { YEAR_COLORS } from '../../lib/constants';
import { ChartContainer } from '../charts/ChartContainer';
import { DashboardBarChart } from '../charts/BarChart';
import { DashboardLineChart } from '../charts/LineChart';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { DataGapBanner } from '../common/DataGapBanner';

const REGION_COLORS: Record<string, string> = {
  'North Central': '#3B82F6',
  'North East': '#14B8A6',
  'South Central': '#F59E0B',
  'South East': '#F97316',
  'Western USA': '#8B5CF6',
  'Canada': '#EC4899',
  'India': '#06B6D4',
  'ROW': '#84CC16',
  'Unknown': '#9CA3AF',
};

export function RegistrationTab() {
  const { data, isLoading } = useRegistrationData();
  const { data: summaryData } = useSummaryData();

  // Find any data gaps from summary
  const dataGaps = useMemo(() => {
    if (!summaryData?.byYear) return [];
    return summaryData.byYear.flatMap((y) => y.dataGaps || []);
  }, [summaryData]);

  // Registrations by Year — bar data with year colors
  const byYearBars = useMemo(() => {
    if (!data?.byYear) return [];
    return data.byYear.map((d) => ({
      dataKey: String(d.year),
      color: YEAR_COLORS[d.year] || '#6b7280',
      name: String(d.year),
    }));
  }, [data]);

  const byYearData = useMemo(() => {
    if (!data?.byYear) return [];
    // Single row with each year as a key
    const row: Record<string, unknown> = { label: 'Registrations' };
    data.byYear.forEach((d) => { row[String(d.year)] = d.count; });
    return [row];
  }, [data]);

  // Registrations by Region — stacked bar: each row is a year, stacks are regions
  const { regionData, regionBars } = useMemo(() => {
    if (!data?.byRegion) return { regionData: [], regionBars: [] };
    const years = [...new Set(data.byRegion.map((d) => d.year))].sort();
    const regions = [...new Set(data.byRegion.map((d) => d.region))];
    const rows = years.map((year) => {
      const row: Record<string, unknown> = { year };
      regions.forEach((region) => {
        const entry = data.byRegion.find((d) => d.year === year && d.region === region);
        row[region] = entry?.count ?? 0;
      });
      return row;
    });
    const bars = regions.map((region) => ({
      dataKey: region,
      color: REGION_COLORS[region] || '#6b7280',
      name: region,
      stackId: 'regions',
    }));
    return { regionData: rows, regionBars: bars };
  }, [data]);

  // New vs Returning
  const newVsReturningData = useMemo(() => {
    if (!data?.newVsReturning) return [];
    return data.newVsReturning.map((d) => ({
      year: d.year,
      New: d.new,
      Returning: d.returning,
    }));
  }, [data]);

  // Arrival Distribution — one line per year
  const { arrivalData, arrivalLines } = useMemo(() => {
    if (!data?.arrivalDistribution) return { arrivalData: [], arrivalLines: [] };
    const years = [...new Set(data.arrivalDistribution.map((d) => d.year))].sort();
    // Group by date across years; format date as MMM D
    const dateMap = new Map<string, Record<string, unknown>>();
    data.arrivalDistribution.forEach((d) => {
      const dt = new Date(d.date);
      const label = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      if (!dateMap.has(label)) {
        dateMap.set(label, { date: label });
      }
      dateMap.get(label)![String(d.year)] = d.count;
    });
    const rows = Array.from(dateMap.values());
    const lines = years.map((year) => ({
      dataKey: String(year),
      color: YEAR_COLORS[year] || '#6b7280',
      name: String(year),
    }));
    return { arrivalData: rows, arrivalLines: lines };
  }, [data]);

  // Length of Stay
  const losData = useMemo(() => {
    if (!data?.lengthOfStay) return [];
    return data.lengthOfStay.map((d) => ({ days: `${d.days}d`, count: d.count }));
  }, [data]);

  // Special Needs
  const specialNeedsData = useMemo(() => {
    if (!data?.specialNeeds) return [];
    return data.specialNeeds.map((d) => ({ year: d.year, count: d.count }));
  }, [data]);

  if (isLoading) {
    return <LoadingSpinner message="Loading registration data..." />;
  }

  return (
    <div className="space-y-6">
      {dataGaps.length > 0 && <DataGapBanner gaps={[...new Set(dataGaps)]} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Registrations by Year */}
        <ChartContainer title="Registrations by Year" isEmpty={!data?.byYear?.length}>
          <DashboardBarChart data={byYearData} xKey="label" bars={byYearBars} />
        </ChartContainer>

        {/* Registrations by Region */}
        <ChartContainer title="Registrations by Region" subtitle="Stacked by region per year" isEmpty={!data?.byRegion?.length}>
          <DashboardBarChart data={regionData} xKey="year" bars={regionBars} />
        </ChartContainer>

        {/* New vs Returning */}
        <ChartContainer title="New vs Returning" isEmpty={!data?.newVsReturning?.length}>
          <DashboardBarChart
            data={newVsReturningData}
            xKey="year"
            bars={[
              { dataKey: 'New', color: '#3B82F6', name: 'New' },
              { dataKey: 'Returning', color: '#14B8A6', name: 'Returning' },
            ]}
          />
        </ChartContainer>

        {/* Arrival Distribution */}
        <ChartContainer title="Arrival Distribution" subtitle="Arrivals by date per year" isEmpty={!data?.arrivalDistribution?.length}>
          <DashboardLineChart data={arrivalData} xKey="date" lines={arrivalLines} />
        </ChartContainer>

        {/* Length of Stay */}
        <ChartContainer title="Length of Stay" subtitle="Distribution of stay durations" isEmpty={!data?.lengthOfStay?.length}>
          <DashboardBarChart
            data={losData}
            xKey="days"
            bars={[{ dataKey: 'count', color: '#3B82F6', name: 'Registrations' }]}
          />
        </ChartContainer>

        {/* Special Needs Requests */}
        <ChartContainer title="Special Needs Requests" subtitle="Requests by year" isEmpty={!data?.specialNeeds?.length}>
          <DashboardBarChart
            data={specialNeedsData}
            xKey="year"
            bars={[{ dataKey: 'count', color: '#F59E0B', name: 'Requests' }]}
          />
        </ChartContainer>
      </div>
    </div>
  );
}
