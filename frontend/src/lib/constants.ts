export const YEAR_COLORS: Record<number, string> = {
  2022: '#3B82F6', // blue-500
  2023: '#14B8A6', // teal-500
  2024: '#F59E0B', // amber-500
  2025: '#F97316', // orange-500
};

export const TAB_CONFIG = [
  { id: 'overview', label: 'Overview', icon: 'chart-bar' },
  { id: 'registrations', label: 'Registrations', icon: 'users' },
  { id: 'rooms', label: 'Rooms', icon: 'building' },
  { id: 'dining', label: 'Dining', icon: 'utensils' },
  { id: 'ai-insights', label: 'AI Insights', icon: 'sparkles' },
  { id: 'raw-data', label: 'Raw Data', icon: 'table' },
] as const;

export type TabId = typeof TAB_CONFIG[number]['id'];
