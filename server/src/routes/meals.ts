import { Router, Request, Response } from 'express';
import { query } from '../services/db';
import catchAsync from '../utils/catchAsync';
import { parseFilterParams } from '../services/queryBuilder';

const router = Router();

router.get('/', catchAsync(async (req: Request, res: Response) => {
  const filters = parseFilterParams(req.query as Record<string, unknown>);

  // Resolve years
  let years: number[];
  if (filters.years.length > 0) {
    years = filters.years;
  } else {
    const yr = await query('SELECT DISTINCT event_year FROM events ORDER BY event_year');
    years = yr.rows.map((r: Record<string, unknown>) => r.event_year as number);
  }

  // Split years: meal_scans years vs 2024 (aggregates)
  const scanYears = years.filter(y => y !== 2024);
  const include2024 = years.includes(2024);

  const hasRegionFilter = filters.regions != null && filters.regions.length > 0;
  const personJoin = hasRegionFilter ? 'JOIN persons p ON ms.person_id = p.person_id' : '';

  // Build params for meal_scans queries
  const scanParams: unknown[] = [];
  const scanConditions: string[] = [];
  let idx = 1;

  if (scanYears.length > 0) {
    scanConditions.push(`ms.event_year = ANY($${idx})`);
    scanParams.push(scanYears);
    idx++;
  }
  if (hasRegionFilter) {
    scanConditions.push(`p.region_id = ANY($${idx})`);
    scanParams.push(filters.regions);
    idx++;
  }

  const scanWhere = scanConditions.length > 0 ? `WHERE ${scanConditions.join(' AND ')}` : '';
  const hasScanYears = scanYears.length > 0;

  // Build all promises
  const promises: Promise<unknown>[] = [];

  // 0: dailyHeadcount from meal_scans
  if (hasScanYears) {
    promises.push(
      query(
        `SELECT ms.event_year, ms.session_date, SUM(ms.food_count)::int AS total
         FROM meal_scans ms
         ${personJoin}
         ${scanWhere}
         GROUP BY ms.event_year, ms.session_date
         ORDER BY ms.session_date`,
        scanParams
      )
    );
  } else {
    promises.push(Promise.resolve({ rows: [] }));
  }

  // 1: dailyHeadcount from meal_aggregates (2024)
  if (include2024) {
    promises.push(
      query(
        `SELECT 2024 AS event_year, ma.meal_date AS session_date,
                SUM((SELECT SUM(value::int) FROM jsonb_each_text(ma.meal_conflicts)))::int AS total
         FROM meal_aggregates ma
         WHERE ma.event_year = 2024 AND ma.meal_conflicts IS NOT NULL
         GROUP BY ma.meal_date
         ORDER BY ma.meal_date`
      )
    );
  } else {
    promises.push(Promise.resolve({ rows: [] }));
  }

  // 2: byMealType from meal_scans
  if (hasScanYears) {
    promises.push(
      query(
        `SELECT ms.event_year, ms.session_title, SUM(ms.food_count)::int AS total
         FROM meal_scans ms
         ${personJoin}
         ${scanWhere}
         AND ms.session_title IS NOT NULL
         GROUP BY ms.event_year, ms.session_title
         ORDER BY ms.event_year, ms.session_title`,
        scanParams
      )
    );
  } else {
    promises.push(Promise.resolve({ rows: [] }));
  }

  // 3: foodPreference from meal_scans
  if (hasScanYears) {
    promises.push(
      query(
        `SELECT ms.event_year, ms.food_consumed, SUM(ms.food_count)::int AS total
         FROM meal_scans ms
         ${personJoin}
         ${scanWhere}
         AND ms.food_consumed IS NOT NULL
         GROUP BY ms.event_year, ms.food_consumed
         ORDER BY ms.event_year, ms.food_consumed`,
        scanParams
      )
    );
  } else {
    promises.push(Promise.resolve({ rows: [] }));
  }

  // 4: kitchenHeadcount from meal_scans
  if (hasScanYears) {
    promises.push(
      query(
        `SELECT ms.event_year, ms.session_date, ms.session_title, SUM(ms.food_count)::int AS count
         FROM meal_scans ms
         ${personJoin}
         ${scanWhere}
         GROUP BY ms.event_year, ms.session_date, ms.session_title
         ORDER BY ms.session_date, ms.session_title`,
        scanParams
      )
    );
  } else {
    promises.push(Promise.resolve({ rows: [] }));
  }

  const [dailyScanRes, daily2024Res, mealTypeRes, foodPrefRes, kitchenRes] = await Promise.all(promises) as Array<{ rows: Record<string, unknown>[] }>;

  // Merge daily headcount: scan data + 2024 aggregates, sorted by date
  const dailyHeadcount = [
    ...dailyScanRes.rows.map((r) => ({
      year: r.event_year as number,
      date: r.session_date as string,
      total: r.total as number,
    })),
    ...daily2024Res.rows.map((r) => ({
      year: r.event_year as number,
      date: r.session_date as string,
      total: r.total as number,
    })),
  ].sort((a, b) => {
    const dateCompare = String(a.date).localeCompare(String(b.date));
    return dateCompare !== 0 ? dateCompare : a.year - b.year;
  });

  const byMealType = mealTypeRes.rows.map((r) => ({
    year: r.event_year as number,
    session: r.session_title as string,
    total: r.total as number,
  }));

  const foodPreference = foodPrefRes.rows.map((r) => ({
    year: r.event_year as number,
    preference: r.food_consumed as string,
    total: r.total as number,
  }));

  const kitchenHeadcount = kitchenRes.rows.map((r) => ({
    year: r.event_year as number,
    date: r.session_date as string,
    session: r.session_title as string,
    count: r.count as number,
  }));

  res.json({
    data: {
      dailyHeadcount,
      byMealType,
      foodPreference,
      kitchenHeadcount,
    },
  });
}));

export default router;
