import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '../lib/api';
import { useSelectedYears, useSelectedRegions, useSelectedRoomTypes } from './useFilters';

export function useFiltersData() {
  return useQuery({
    queryKey: ['filters'],
    queryFn: () => fetchApi<{
      years: number[];
      regions: { id: number; code: string; name: string }[];
      roomTypes: { id: number; code: string; name: string }[];
      dateRange: { min: string; max: string };
    }>('/filters'),
    staleTime: 5 * 60 * 1000, // filters rarely change
  });
}

/** Build query string from all active filters */
function useFilterQueryString() {
  const years = useSelectedYears();
  const regions = useSelectedRegions();
  const roomTypes = useSelectedRoomTypes();

  const params = new URLSearchParams();
  if (years.length > 0) params.set('years', years.join(','));
  if (regions.length > 0) params.set('regions', regions.join(','));
  if (roomTypes.length > 0) params.set('roomTypes', roomTypes.join(','));
  return params.toString();
}

export function useRegistrationData() {
  const years = useSelectedYears();
  const regions = useSelectedRegions();
  const params = new URLSearchParams();
  if (years.length > 0) params.set('years', years.join(','));
  if (regions.length > 0) params.set('regions', regions.join(','));
  const qs = params.toString();

  return useQuery({
    queryKey: ['registrations', years, regions],
    queryFn: () => fetchApi<{
      byYear: { year: number; count: number }[];
      byRegion: { region: string; year: number; count: number }[];
      newVsReturning: { year: number; new: number; returning: number }[];
      arrivalDistribution: { year: number; date: string; count: number }[];
      lengthOfStay: { days: number; count: number }[];
      specialNeeds: { year: number; count: number }[];
    }>(`/registrations${qs ? `?${qs}` : ''}`),
  });
}

export function useRoomData() {
  const years = useSelectedYears();
  const regions = useSelectedRegions();
  const roomTypes = useSelectedRoomTypes();
  const params = new URLSearchParams();
  if (years.length > 0) params.set('years', years.join(','));
  if (regions.length > 0) params.set('regions', regions.join(','));
  if (roomTypes.length > 0) params.set('roomTypes', roomTypes.join(','));
  const qs = params.toString();

  return useQuery({
    queryKey: ['rooms', years, regions, roomTypes],
    queryFn: () => fetchApi<{
      byType: { typeName: string; year: number; count: number; avgOccupancy: number | null }[];
      utilizationByYear: { year: number; totalRooms: number; avgOccupancy: number | null }[];
      roomsPerAttendee: { year: number; registrations: number; rooms: number; ratio: number | null }[];
      checkInOut: { date: string; checkIns: number; checkOuts: number }[];
    }>(`/rooms${qs ? `?${qs}` : ''}`),
  });
}

export function useMealData() {
  const years = useSelectedYears();
  const regions = useSelectedRegions();
  const params = new URLSearchParams();
  if (years.length > 0) params.set('years', years.join(','));
  if (regions.length > 0) params.set('regions', regions.join(','));
  const qs = params.toString();

  return useQuery({
    queryKey: ['meals', years, regions],
    queryFn: () => fetchApi<{
      dailyHeadcount: { year: number; date: string; total: number }[];
      byMealType: { year: number; session: string; total: number }[];
      foodPreference: { year: number; preference: string; total: number }[];
      kitchenHeadcount: { year: number; date: string; session: string; count: number }[];
    }>(`/meals${qs ? `?${qs}` : ''}`),
  });
}

export function useAgentStatus() {
  return useQuery({
    queryKey: ['agent-status'],
    queryFn: () => fetchApi<{
      status: string;
      phase?: string;
      progressPct?: number;
      error?: string;
      startedAt?: string;
      completedAt?: string;
      jobId?: string;
    }>('/agent/status'),
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === 'running' ? 3000 : 30000;
    },
  });
}

export function useSummaryData() {
  const years = useSelectedYears();
  const regions = useSelectedRegions();
  const roomTypes = useSelectedRoomTypes();
  const qs = useFilterQueryString();

  return useQuery({
    queryKey: ['summary', years, regions, roomTypes],
    queryFn: () => fetchApi<{
      totalRegistrations: number;
      totalRoomNights: number;
      averageDailyMeals: number;
      yoyGrowthPercent: number | null;
      byYear: {
        year: number;
        registrations: number | null;
        roomNights: number | null;
        avgDailyMeals: number | null;
        dataGaps: string[];
      }[];
    }>(`/summary${qs ? `?${qs}` : ''}`),
  });
}
