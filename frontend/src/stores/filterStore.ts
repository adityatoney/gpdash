import { create } from 'zustand';
import type { TabId } from '../lib/constants';

interface FilterState {
  years: number[];
  regions: number[];
  roomTypes: number[];
  dateRange: { from: string | null; to: string | null };
  activeTab: TabId;

  setYears: (years: number[]) => void;
  toggleYear: (year: number) => void;
  setRegions: (regions: number[]) => void;
  toggleRegion: (id: number) => void;
  setRoomTypes: (roomTypes: number[]) => void;
  toggleRoomType: (id: number) => void;
  setDateRange: (range: { from: string | null; to: string | null }) => void;
  setActiveTab: (tab: TabId) => void;
  resetFilters: () => void;
  initFromUrl: () => void;
}

function parseUrlParams(): Partial<FilterState> {
  const params = new URLSearchParams(window.location.search);
  const result: Partial<FilterState> = {};

  const years = params.get('years');
  if (years) result.years = years.split(',').map(Number).filter(n => !isNaN(n));

  const regions = params.get('regions');
  if (regions) result.regions = regions.split(',').map(Number).filter(n => !isNaN(n));

  const roomTypes = params.get('roomTypes');
  if (roomTypes) result.roomTypes = roomTypes.split(',').map(Number).filter(n => !isNaN(n));

  const tab = params.get('tab');
  if (tab) result.activeTab = tab as TabId;

  const from = params.get('from');
  const to = params.get('to');
  if (from || to) result.dateRange = { from: from || null, to: to || null };

  return result;
}

type FilterData = Pick<FilterState, 'years' | 'regions' | 'roomTypes' | 'dateRange' | 'activeTab'>;

function syncToUrl(state: FilterData) {
  const params = new URLSearchParams();
  if (state.years.length > 0) params.set('years', state.years.join(','));
  if (state.regions.length > 0) params.set('regions', state.regions.join(','));
  if (state.roomTypes.length > 0) params.set('roomTypes', state.roomTypes.join(','));
  if (state.activeTab !== 'overview') params.set('tab', state.activeTab);
  if (state.dateRange.from) params.set('from', state.dateRange.from);
  if (state.dateRange.to) params.set('to', state.dateRange.to);

  const search = params.toString();
  const newUrl = search ? `${window.location.pathname}?${search}` : window.location.pathname;
  window.history.replaceState(null, '', newUrl);
}

const DEFAULT_STATE = {
  years: [] as number[],
  regions: [] as number[],
  roomTypes: [] as number[],
  dateRange: { from: null as string | null, to: null as string | null },
  activeTab: 'overview' as TabId,
};

export const useFilterStore = create<FilterState>((set, get) => ({
  ...DEFAULT_STATE,

  setYears: (years) => { set({ years }); syncToUrl({ ...get(), years }); },
  toggleYear: (year) => {
    const current = get().years;
    const years = current.includes(year) ? current.filter(y => y !== year) : [...current, year].sort();
    set({ years }); syncToUrl({ ...get(), years });
  },
  setRegions: (regions) => { set({ regions }); syncToUrl({ ...get(), regions }); },
  toggleRegion: (id) => {
    const current = get().regions;
    const regions = current.includes(id) ? current.filter(r => r !== id) : [...current, id];
    set({ regions }); syncToUrl({ ...get(), regions });
  },
  setRoomTypes: (roomTypes) => { set({ roomTypes }); syncToUrl({ ...get(), roomTypes }); },
  toggleRoomType: (id) => {
    const current = get().roomTypes;
    const roomTypes = current.includes(id) ? current.filter(r => r !== id) : [...current, id];
    set({ roomTypes }); syncToUrl({ ...get(), roomTypes });
  },
  setDateRange: (dateRange) => { set({ dateRange }); syncToUrl({ ...get(), dateRange }); },
  setActiveTab: (activeTab) => { set({ activeTab }); syncToUrl({ ...get(), activeTab }); },
  resetFilters: () => {
    set({ ...DEFAULT_STATE });
    syncToUrl(DEFAULT_STATE);
  },
  initFromUrl: () => {
    const fromUrl = parseUrlParams();
    if (Object.keys(fromUrl).length > 0) {
      set(fromUrl);
    }
  },
}));
