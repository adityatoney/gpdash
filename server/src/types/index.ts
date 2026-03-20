export interface ApiResponse<T> {
  data: T;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface YearSummary {
  year: number;
  registrations: number | null;
  roomNights: number | null;
  avgDailyMeals: number | null;
  dataGaps: string[];
}

export interface SummaryResponse {
  totalRegistrations: number;
  totalRoomNights: number;
  averageDailyMeals: number;
  yoyGrowthPercent: number | null;
  byYear: YearSummary[];
}

export interface FilterRegion {
  id: number;
  code: string;
  name: string;
}

export interface FilterRoomType {
  id: number;
  code: string;
  name: string;
}

export interface FiltersResponse {
  years: number[];
  regions: FilterRegion[];
  roomTypes: FilterRoomType[];
  dateRange: { min: string; max: string };
}
