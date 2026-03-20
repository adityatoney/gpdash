import { useFilterStore } from '../stores/filterStore';

// Selector hooks for surgical re-renders
export const useSelectedYears = () => useFilterStore((s) => s.years);
export const useSelectedRegions = () => useFilterStore((s) => s.regions);
export const useSelectedRoomTypes = () => useFilterStore((s) => s.roomTypes);
export const useDateRange = () => useFilterStore((s) => s.dateRange);
export const useActiveTab = () => useFilterStore((s) => s.activeTab);

export function buildQueryParams(): string {
  const state = useFilterStore.getState();
  const params = new URLSearchParams();
  if (state.years.length > 0) params.set('years', state.years.join(','));
  if (state.regions.length > 0) params.set('regions', state.regions.join(','));
  if (state.roomTypes.length > 0) params.set('roomTypes', state.roomTypes.join(','));
  if (state.dateRange.from) params.set('dateFrom', state.dateRange.from);
  if (state.dateRange.to) params.set('dateTo', state.dateRange.to);
  return params.toString();
}
