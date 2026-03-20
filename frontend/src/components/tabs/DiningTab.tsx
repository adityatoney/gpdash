import { useState, useMemo } from 'react';
import { useMealData, useSummaryData } from '../../hooks/useApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { DataGapBanner } from '../common/DataGapBanner';
import { ExportButton } from '../common/ExportButton';
import { ChartContainer } from '../charts/ChartContainer';
import { DashboardAreaChart } from '../charts/AreaChart';
import { DashboardBarChart } from '../charts/BarChart';
import { YEAR_COLORS } from '../../lib/constants';
import { generateCsv, downloadCsv } from '../../lib/csv';
import { formatNumber } from '../../lib/formatters';

type SortDir = 'asc' | 'desc';
type SortKey = 'year' | 'date' | 'session' | 'count';

function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function DiningTab() {
  const { data, isLoading } = useMealData();
  const { data: summaryData } = useSummaryData();
  const [sortKey, setSortKey] = useState<SortKey>('date');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  // Data gap detection
  const foodGapYears = summaryData?.byYear.filter(yr => yr.dataGaps.includes('food')) ?? [];

  // Pivot daily headcount: { date, "2022": val, "2025": val }
  const dailyChartData = useMemo(() => {
    if (!data?.dailyHeadcount) return [];
    const byDate = new Map<string, Record<string, unknown>>();
    for (const row of data.dailyHeadcount) {
      const key = formatShortDate(row.date);
      if (!byDate.has(key)) byDate.set(key, { date: key });
      byDate.get(key)![String(row.year)] = row.total;
    }
    return Array.from(byDate.values());
  }, [data?.dailyHeadcount]);

  const dailyYears = useMemo(() => {
    if (!data?.dailyHeadcount) return [];
    return [...new Set(data.dailyHeadcount.map(d => d.year))].sort();
  }, [data?.dailyHeadcount]);

  // Pivot by meal type: { year, Breakfast, Lunch, Dinner, ... }
  const mealTypeData = useMemo(() => {
    if (!data?.byMealType) return [];
    const byYear = new Map<number, Record<string, unknown>>();
    for (const row of data.byMealType) {
      if (!byYear.has(row.year)) byYear.set(row.year, { year: String(row.year) });
      byYear.get(row.year)![row.session] = row.total;
    }
    return Array.from(byYear.values()).sort((a, b) => Number(a.year) - Number(b.year));
  }, [data?.byMealType]);

  const mealSessions = useMemo(() => {
    if (!data?.byMealType) return [];
    return [...new Set(data.byMealType.map(d => d.session))].sort();
  }, [data?.byMealType]);

  // Pivot food preference: { year, Regular, Jain, ... }
  const foodPrefData = useMemo(() => {
    if (!data?.foodPreference) return [];
    const byYear = new Map<number, Record<string, unknown>>();
    for (const row of data.foodPreference) {
      if (!byYear.has(row.year)) byYear.set(row.year, { year: String(row.year) });
      byYear.get(row.year)![row.preference] = row.total;
    }
    return Array.from(byYear.values()).sort((a, b) => Number(a.year) - Number(b.year));
  }, [data?.foodPreference]);

  const foodPrefs = useMemo(() => {
    if (!data?.foodPreference) return [];
    return [...new Set(data.foodPreference.map(d => d.preference))].sort();
  }, [data?.foodPreference]);

  // Sortable kitchen table
  const sortedKitchen = useMemo(() => {
    if (!data?.kitchenHeadcount) return [];
    const sorted = [...data.kitchenHeadcount];
    sorted.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'year': cmp = a.year - b.year; break;
        case 'date': cmp = a.date.localeCompare(b.date); break;
        case 'session': cmp = (a.session || '').localeCompare(b.session || ''); break;
        case 'count': cmp = a.count - b.count; break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return sorted;
  }, [data?.kitchenHeadcount, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const handleExport = () => {
    if (!sortedKitchen.length) return;
    const csv = generateCsv(
      ['Year', 'Date', 'Session', 'Count'],
      sortedKitchen.map(r => [r.year, r.date, r.session, r.count])
    );
    downloadCsv('kitchen-headcount.csv', csv);
  };

  const SortIcon = ({ column }: { column: SortKey }) => (
    <span className="ml-1 text-gray-400">
      {sortKey === column ? (sortDir === 'asc' ? '\u2191' : '\u2193') : '\u2195'}
    </span>
  );

  const MEAL_COLORS = ['#3B82F6', '#14B8A6', '#F59E0B', '#F97316', '#8B5CF6'];
  const PREF_COLORS: Record<string, string> = { Regular: '#3B82F6', Jain: '#14B8A6', Western: '#F59E0B', Others: '#F97316' };

  if (isLoading) return <LoadingSpinner message="Loading dining data..." />;

  return (
    <div className="space-y-6">
      {/* Data gap banners */}
      {foodGapYears.map(yr => (
        <DataGapBanner key={yr.year} gaps={['food']} year={yr.year} />
      ))}

      {/* Charts grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ChartContainer title="Daily Meal Headcount" subtitle="Total meals served per day" isEmpty={dailyChartData.length === 0} className="lg:col-span-2">
          <DashboardAreaChart
            data={dailyChartData}
            xKey="date"
            areas={dailyYears.map(y => ({ dataKey: String(y), color: YEAR_COLORS[y] || '#6B7280', name: String(y) }))}
          />
        </ChartContainer>

        <ChartContainer title="Meals by Type" subtitle="Breakdown by meal session" isEmpty={mealTypeData.length === 0}>
          <DashboardBarChart
            data={mealTypeData}
            xKey="year"
            bars={mealSessions.map((s, i) => ({ dataKey: s, color: MEAL_COLORS[i % MEAL_COLORS.length], name: s, stackId: 'meals' }))}
          />
        </ChartContainer>

        <ChartContainer title="Food Preference" subtitle="By dietary preference" isEmpty={foodPrefData.length === 0}>
          <DashboardBarChart
            data={foodPrefData}
            xKey="year"
            bars={foodPrefs.map(p => ({ dataKey: p, color: PREF_COLORS[p] || '#6B7280', name: p }))}
          />
        </ChartContainer>
      </div>

      {/* Kitchen Headcount Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-gray-900">Kitchen Headcount</h2>
            <p className="text-xs text-gray-500 mt-0.5">{sortedKitchen.length} records</p>
          </div>
          <ExportButton onClick={handleExport} />
        </div>
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-[13px]">
            <thead className="sticky top-0 bg-gray-50/95 backdrop-blur-sm">
              <tr className="border-b border-gray-100">
                {([['year', 'Year'], ['date', 'Date'], ['session', 'Session'], ['count', 'Count']] as [SortKey, string][]).map(([key, label]) => (
                  <th key={key} onClick={() => handleSort(key)}
                    className={`px-5 py-2.5 text-left font-semibold text-gray-500 uppercase text-[11px] tracking-wider cursor-pointer hover:text-gray-700 select-none ${key === 'count' ? 'text-right' : ''}`}>
                    {label}<SortIcon column={key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sortedKitchen.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-2.5 text-gray-700 tabular-nums">{row.year}</td>
                  <td className="px-5 py-2.5 text-gray-700">{new Date(row.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
                  <td className="px-5 py-2.5 text-gray-700">{row.session}</td>
                  <td className="px-5 py-2.5 text-right text-gray-900 font-medium tabular-nums">{formatNumber(row.count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
