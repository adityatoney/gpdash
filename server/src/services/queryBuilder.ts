import { AppError } from '../middleware/errorHandler';

export interface FilterParams {
  years: number[];
  regions?: number[];
  roomTypes?: number[];
  dateFrom?: string;
  dateTo?: string;
}

export function parseFilterParams(query: Record<string, unknown>): FilterParams {
  const years: number[] = [];
  if (query.years && typeof query.years === 'string') {
    for (const y of query.years.split(',')) {
      const n = parseInt(y.trim(), 10);
      if (isNaN(n)) throw new AppError(400, 'INVALID_PARAM', `Invalid year: ${y}`);
      years.push(n);
    }
  }

  const regions = parseOptionalIntArray(query.regions, 'region');
  const roomTypes = parseOptionalIntArray(query.roomTypes, 'roomType');

  return {
    years,
    regions: regions ?? undefined,
    roomTypes: roomTypes ?? undefined,
    dateFrom: typeof query.dateFrom === 'string' ? query.dateFrom : undefined,
    dateTo: typeof query.dateTo === 'string' ? query.dateTo : undefined,
  };
}

function parseOptionalIntArray(raw: unknown, label: string): number[] | null {
  if (!raw || typeof raw !== 'string') return null;
  return raw.split(',').map((v) => {
    const n = parseInt(v.trim(), 10);
    if (isNaN(n)) throw new AppError(400, 'INVALID_PARAM', `Invalid ${label}: ${v}`);
    return n;
  });
}

/**
 * Builds WHERE conditions and params array for registrations queries.
 * Returns { conditions: string[], params: unknown[], nextIdx: number }
 */
export function buildRegistrationWhere(filters: FilterParams, startIdx = 1) {
  const conditions: string[] = [];
  const params: unknown[] = [];
  let idx = startIdx;

  if (filters.years.length > 0) {
    conditions.push(`r.event_year = ANY($${idx})`);
    params.push(filters.years);
    idx++;
  }
  if (filters.regions && filters.regions.length > 0) {
    conditions.push(`p.region_id = ANY($${idx})`);
    params.push(filters.regions);
    idx++;
  }
  if (filters.dateFrom) {
    conditions.push(`r.arrival_date >= $${idx}`);
    params.push(filters.dateFrom);
    idx++;
  }
  if (filters.dateTo) {
    conditions.push(`r.arrival_date <= $${idx}`);
    params.push(filters.dateTo);
    idx++;
  }

  return { conditions, params, nextIdx: idx };
}

export function buildRoomWhere(filters: FilterParams, startIdx = 1) {
  const conditions: string[] = [];
  const params: unknown[] = [];
  let idx = startIdx;

  if (filters.years.length > 0) {
    conditions.push(`rm.event_year = ANY($${idx})`);
    params.push(filters.years);
    idx++;
  }
  if (filters.roomTypes && filters.roomTypes.length > 0) {
    conditions.push(`rm.room_type_assigned_id IN (SELECT room_type_id FROM ref_room_types WHERE category_id = ANY($${idx}))`);
    params.push(filters.roomTypes);
    idx++;
  }
  if (filters.regions && filters.regions.length > 0) {
    conditions.push(`p.region_id = ANY($${idx})`);
    params.push(filters.regions);
    idx++;
  }
  if (filters.dateFrom) {
    conditions.push(`rm.check_in_date >= $${idx}`);
    params.push(filters.dateFrom);
    idx++;
  }
  if (filters.dateTo) {
    conditions.push(`rm.check_out_date <= $${idx}`);
    params.push(filters.dateTo);
    idx++;
  }

  return { conditions, params, nextIdx: idx };
}

export function needsPersonJoin(filters: FilterParams): boolean {
  return (filters.regions != null && filters.regions.length > 0);
}

export function whereClause(conditions: string[]): string {
  return conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
}
