import { useSummaryData, useAgentStatus } from '../../hooks/useApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { DataGapBanner } from '../common/DataGapBanner';
import { formatNumber } from '../../lib/formatters';

interface KpiCardProps {
  label: string;
  value: string;
  accentColor: string;
  icon: React.ReactNode;
}

function KpiCard({ label, value, accentColor, icon }: KpiCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 border-l-4" style={{ borderLeftColor: accentColor }}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-gray-400">{icon}</span>
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

export function OverviewTab() {
  const { data, isLoading, error } = useSummaryData();
  const { data: agentData } = useAgentStatus();

  if (isLoading) return <LoadingSpinner message="Loading dashboard data..." />;

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-center">
        <h3 className="text-sm font-semibold text-red-800">Failed to load data</h3>
        <p className="mt-1 text-sm text-red-600">{(error as Error).message}</p>
      </div>
    );
  }

  if (!data) return null;

  const yearsWithGaps = data.byYear.filter(yr => yr.dataGaps.length > 0);

  return (
    <div className="space-y-6">
      {/* Data Gap Banners */}
      {yearsWithGaps.length > 0 && (
        <div className="space-y-2">
          {yearsWithGaps.map((yr) => (
            <DataGapBanner key={yr.year} gaps={yr.dataGaps} year={yr.year} />
          ))}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Registrations" value={formatNumber(data.totalRegistrations)} accentColor="#3B82F6"
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" /></svg>}
        />
        <KpiCard label="Room Nights" value={formatNumber(data.totalRoomNights)} accentColor="#8B5CF6"
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" /></svg>}
        />
        <KpiCard label="Avg Daily Meals" value={formatNumber(data.averageDailyMeals)} accentColor="#10B981"
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8.25v-1.5m0 1.5c-1.355 0-2.697.056-4.024.166C6.845 8.51 6 9.473 6 10.608v2.513m6-4.871c1.355 0 2.697.056 4.024.166C17.155 8.51 18 9.473 18 10.608v2.513M15 8.25v-1.5m-6 1.5v-1.5m12 9.75-1.5.75a3.354 3.354 0 0 1-3 0 3.354 3.354 0 0 0-3 0 3.354 3.354 0 0 1-3 0 3.354 3.354 0 0 0-3 0 3.354 3.354 0 0 1-3 0L3 16.5m15-3.379a48.474 48.474 0 0 0-6-.371c-2.032 0-4.034.126-6 .371m12 0c.39.049.777.102 1.163.16 1.07.16 1.837 1.094 1.837 2.175v5.169c0 .621-.504 1.125-1.125 1.125H4.125A1.125 1.125 0 0 1 3 20.625v-5.17c0-1.08.768-2.014 1.837-2.174A47.78 47.78 0 0 1 6 13.12M12.265 3.11a.375.375 0 1 1-.53.53.375.375 0 0 1 .53-.53Z" /></svg>}
        />
        <KpiCard label="YoY Growth" value={data.yoyGrowthPercent !== null ? `${data.yoyGrowthPercent > 0 ? '+' : ''}${data.yoyGrowthPercent.toFixed(1)}%` : '--'} accentColor="#F59E0B"
          icon={data.yoyGrowthPercent !== null && data.yoyGrowthPercent >= 0 ? (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" /></svg>
          ) : (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6 9 12.75l4.286-4.286a11.948 11.948 0 0 1 4.306 6.986l.776 2.898m0 0 3.182-5.511m-3.182 5.51-5.511-3.181" /></svg>
          )}
        />
      </div>

      {/* Per-Year Breakdown Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-900">Per-Year Breakdown</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-100">
                <th className="px-5 py-2.5 text-left font-semibold text-gray-500 uppercase text-[11px] tracking-wider">Year</th>
                <th className="px-5 py-2.5 text-right font-semibold text-gray-500 uppercase text-[11px] tracking-wider">Registrations</th>
                <th className="px-5 py-2.5 text-right font-semibold text-gray-500 uppercase text-[11px] tracking-wider">Room Nights</th>
                <th className="px-5 py-2.5 text-right font-semibold text-gray-500 uppercase text-[11px] tracking-wider">Avg Daily Meals</th>
                <th className="px-5 py-2.5 text-left font-semibold text-gray-500 uppercase text-[11px] tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {data.byYear.map((yr) => (
                <tr key={yr.year} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-900">{yr.year}</td>
                  <td className="px-5 py-3 text-right text-gray-700 tabular-nums">{formatNumber(yr.registrations)}</td>
                  <td className="px-5 py-3 text-right text-gray-700 tabular-nums">{formatNumber(yr.roomNights)}</td>
                  <td className="px-5 py-3 text-right text-gray-700 tabular-nums">{formatNumber(yr.avgDailyMeals)}</td>
                  <td className="px-5 py-3">
                    {yr.dataGaps.length > 0 ? (
                      <span className="inline-flex items-center gap-1 text-[11px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full ring-1 ring-inset ring-amber-600/20">
                        {yr.dataGaps.join(', ')} gaps
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full ring-1 ring-inset ring-emerald-600/20">
                        Complete
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Agent Status */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">ETL Agent</h3>
            <p className="text-xs text-gray-500 mt-0.5">Data pipeline status</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1 ring-inset ${
              agentData?.status === 'running' ? 'text-amber-700 bg-amber-50 ring-amber-600/20' :
              agentData?.status === 'failed' ? 'text-red-700 bg-red-50 ring-red-600/20' :
              'text-emerald-700 bg-emerald-50 ring-emerald-600/20'
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${
                agentData?.status === 'running' ? 'bg-amber-500 animate-pulse' :
                agentData?.status === 'failed' ? 'bg-red-500' :
                'bg-emerald-500'
              }`} />
              {agentData?.status === 'running' ? `Running${agentData.phase ? `: ${agentData.phase}` : ''}` :
               agentData?.status === 'failed' ? 'Failed' :
               agentData?.status === 'completed' ? 'Completed' : 'Idle'}
            </span>
          </div>
        </div>
        {agentData?.status === 'running' && agentData.progressPct != null && (
          <div className="mt-3">
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-amber-500 rounded-full transition-all duration-500" style={{ width: `${agentData.progressPct}%` }} />
            </div>
          </div>
        )}
        {agentData?.completedAt && (
          <p className="mt-2 text-[11px] text-gray-400">
            Last run: {new Date(agentData.completedAt).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
}
