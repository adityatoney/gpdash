import { useState } from 'react';
import { useFiltersData } from '../../hooks/useApi';
import { useFilterStore } from '../../stores/filterStore';
import { YEAR_COLORS } from '../../lib/constants';

function FilterSection({ title, count, defaultOpen = true, children }: { title: string; count?: number; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button onClick={() => setOpen(!open)} className="flex items-center justify-between w-full text-left py-1.5 group">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider group-hover:text-gray-700">{title}</span>
        <div className="flex items-center gap-1.5">
          {count != null && count > 0 && (
            <span className="inline-flex items-center justify-center h-4 min-w-4 px-1 rounded-full bg-blue-100 text-[10px] font-medium text-blue-700">{count}</span>
          )}
          <svg className={`h-3.5 w-3.5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </div>
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
  );
}

export function Sidebar() {
  const { data: filters, isLoading } = useFiltersData();
  const { years, regions, roomTypes, toggleYear, toggleRegion, toggleRoomType, resetFilters } = useFilterStore();

  const activeFilterCount = years.length + regions.length + roomTypes.length;

  return (
    <aside className="w-60 bg-white border-r border-gray-200 flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-xs font-semibold text-gray-900 uppercase tracking-wider">Filters</h2>
        {activeFilterCount > 0 && (
          <span className="text-[10px] text-gray-400">{activeFilterCount} active</span>
        )}
      </div>

      {isLoading ? (
        <div className="p-4 text-sm text-gray-400">Loading...</div>
      ) : filters ? (
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-5">
          <FilterSection title="Years" count={years.length} defaultOpen={true}>
            <div className="space-y-1">
              {filters.years.map((year) => {
                const isSelected = years.length === 0 || years.includes(year);
                const color = YEAR_COLORS[year] || '#6B7280';
                return (
                  <label key={year} className="flex items-center gap-2 cursor-pointer py-0.5 group">
                    <input type="checkbox" checked={isSelected} onChange={() => toggleYear(year)}
                      className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-0" />
                    <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                    <span className="text-[13px] text-gray-700 group-hover:text-gray-900">{year}</span>
                  </label>
                );
              })}
            </div>
          </FilterSection>

          <FilterSection title="Regions" count={regions.length}>
            <div className="space-y-0.5 max-h-44 overflow-y-auto">
              {filters.regions.map((region) => (
                <label key={region.id} className="flex items-center gap-2 cursor-pointer py-0.5 group">
                  <input type="checkbox" checked={regions.length === 0 || regions.includes(region.id)}
                    onChange={() => toggleRegion(region.id)}
                    className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-0" />
                  <span className="text-[13px] text-gray-700 group-hover:text-gray-900 flex-1 truncate">{region.name}</span>
                  <span className="text-[10px] text-gray-400">{region.code}</span>
                </label>
              ))}
            </div>
          </FilterSection>

          <FilterSection title="Room Types" count={roomTypes.length} defaultOpen={true}>
            <div className="space-y-0.5 max-h-44 overflow-y-auto">
              {filters.roomTypes.map((rt) => (
                <label key={rt.id} className="flex items-center gap-2 cursor-pointer py-0.5 group">
                  <input type="checkbox" checked={roomTypes.length === 0 || roomTypes.includes(rt.id)}
                    onChange={() => toggleRoomType(rt.id)}
                    className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-0" />
                  <span className="text-[13px] text-gray-700 group-hover:text-gray-900 truncate" title={rt.name}>{rt.name}</span>
                </label>
              ))}
            </div>
          </FilterSection>
        </div>
      ) : null}

      <div className="px-4 py-3 border-t border-gray-100">
        <button onClick={resetFilters} disabled={activeFilterCount === 0}
          className="w-full px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-50 rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
          Reset Filters
        </button>
      </div>
    </aside>
  );
}
