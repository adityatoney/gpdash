import { Router, Request, Response } from 'express';
import { query } from '../services/db';
import catchAsync from '../utils/catchAsync';
import { SummaryResponse, YearSummary } from '../types';
import { AppError } from '../middleware/errorHandler';

const router = Router();

function parseIntArray(raw: unknown, label: string): number[] | null {
  if (!raw || typeof raw !== 'string') return null;
  return raw.split(',').map((v) => {
    const n = parseInt(v.trim(), 10);
    if (isNaN(n)) throw new AppError(400, 'INVALID_PARAM', `Invalid ${label} value: ${v}`);
    return n;
  });
}

router.get(
  '/',
  catchAsync(async (req: Request, res: Response) => {
    const yearFilter = parseIntArray(req.query.years, 'year');
    const regionFilter = parseIntArray(req.query.regions, 'region');
    const roomTypeFilter = parseIntArray(req.query.roomTypes, 'roomType');

    const hasDetailFilters = regionFilter !== null || roomTypeFilter !== null;

    // Resolve years
    let years: number[];
    if (yearFilter) {
      years = yearFilter;
    } else {
      const allYears = await query('SELECT DISTINCT event_year FROM events ORDER BY event_year');
      years = allYears.rows.map((r: { event_year: number }) => r.event_year);
    }

    if (years.length === 0) {
      const empty: SummaryResponse = {
        totalRegistrations: 0,
        totalRoomNights: 0,
        averageDailyMeals: 0,
        yoyGrowthPercent: null,
        byYear: [],
      };
      res.json({ data: empty });
      return;
    }

    // Data gaps (always from data_availability, filter-independent)
    const gapsResult = await query(
      `SELECT event_year, entity_type FROM data_availability
       WHERE data_level IN ('none', 'summary')`,
    );
    const gapsMap = new Map<number, string[]>();
    for (const row of gapsResult.rows) {
      const yr = row.event_year as number;
      if (!gapsMap.has(yr)) gapsMap.set(yr, []);
      gapsMap.get(yr)!.push(row.entity_type as string);
    }

    const EVENT_DURATION_DAYS = 7;
    let byYear: YearSummary[];

    if (!hasDetailFilters) {
      // Fast path: use pre-aggregated event totals
      const statsResult = await query(
        `SELECT e.event_year, e.total_registrations, e.total_room_bookings, e.total_meal_scans
         FROM events e WHERE e.event_year = ANY($1)
         ORDER BY e.event_year`,
        [years]
      );

      byYear = statsResult.rows.map((row: Record<string, unknown>) => {
        const totalMeals = row.total_meal_scans as number | null;
        return {
          year: row.event_year as number,
          registrations: row.total_registrations as number | null,
          roomNights: row.total_room_bookings as number | null,
          avgDailyMeals: totalMeals != null ? Math.round(totalMeals / EVENT_DURATION_DAYS) : null,
          dataGaps: gapsMap.get(row.event_year as number) ?? [],
        };
      });
    } else {
      // Filtered path: count from raw tables with JOINs
      // Build parameterized queries
      let paramIdx = 1;
      const params: unknown[] = [];

      // --- Registrations (filtered by region via persons table) ---
      const regWhere: string[] = [`r.event_year = ANY($${paramIdx})`];
      params.push(years);
      paramIdx++;

      if (regionFilter) {
        regWhere.push(`p.region_id = ANY($${paramIdx})`);
        params.push(regionFilter);
        paramIdx++;
      }

      const regQuery = `
        SELECT r.event_year, COUNT(*) AS cnt
        FROM registrations r
        JOIN persons p ON r.person_id = p.person_id
        WHERE ${regWhere.join(' AND ')}
        GROUP BY r.event_year ORDER BY r.event_year
      `;
      const regResult = await query(regQuery, params.slice(0, paramIdx - 1));
      const regMap = new Map<number, number>();
      for (const row of regResult.rows) {
        regMap.set(row.event_year as number, parseInt(row.cnt as string, 10));
      }

      // --- Rooms (filtered by room type) ---
      const roomParams: unknown[] = [years];
      let roomParamIdx = 2;
      const roomWhere: string[] = [`rm.event_year = ANY($1)`];

      if (roomTypeFilter) {
        roomWhere.push(`rm.room_type_assigned_id IN (SELECT room_type_id FROM ref_room_types WHERE category_id = ANY($${roomParamIdx}))`);
        roomParams.push(roomTypeFilter);
        roomParamIdx++;
      }
      if (regionFilter) {
        roomWhere.push(`p.region_id = ANY($${roomParamIdx})`);
        roomParams.push(regionFilter);
        roomParamIdx++;
      }

      const needsPersonJoinForRooms = regionFilter !== null;
      const roomQuery = `
        SELECT rm.event_year, COUNT(*) AS cnt
        FROM rooms rm
        ${needsPersonJoinForRooms ? 'JOIN persons p ON rm.primary_room_holder_id = p.person_id' : ''}
        WHERE ${roomWhere.join(' AND ')}
        GROUP BY rm.event_year ORDER BY rm.event_year
      `;
      const roomResult = await query(roomQuery, roomParams);
      const roomMap = new Map<number, number>();
      for (const row of roomResult.rows) {
        roomMap.set(row.event_year as number, parseInt(row.cnt as string, 10));
      }

      // --- Meals (filtered by region via persons; room type filter doesn't apply to meals) ---
      const mealParams: unknown[] = [years];
      let mealParamIdx = 2;
      const mealWhere: string[] = [`ms.event_year = ANY($1)`];

      if (regionFilter) {
        mealWhere.push(`p.region_id = ANY($${mealParamIdx})`);
        mealParams.push(regionFilter);
        mealParamIdx++;
      }

      const needsPersonJoinForMeals = regionFilter !== null;
      const mealQuery = `
        SELECT ms.event_year, SUM(ms.food_count) AS total
        FROM meal_scans ms
        ${needsPersonJoinForMeals ? 'JOIN persons p ON ms.person_id = p.person_id' : ''}
        WHERE ${mealWhere.join(' AND ')}
        GROUP BY ms.event_year ORDER BY ms.event_year
      `;
      const mealResult = await query(mealQuery, mealParams.slice(0, mealParamIdx - 1));
      const mealMap = new Map<number, number>();
      for (const row of mealResult.rows) {
        mealMap.set(row.event_year as number, parseInt(row.total as string, 10));
      }

      byYear = years.map((yr) => {
        const totalMeals = mealMap.get(yr) ?? null;
        return {
          year: yr,
          registrations: regMap.get(yr) ?? null,
          roomNights: roomMap.get(yr) ?? null,
          avgDailyMeals: totalMeals != null ? Math.round(totalMeals / EVENT_DURATION_DAYS) : null,
          dataGaps: gapsMap.get(yr) ?? [],
        };
      });
    }

    // Totals
    const totalRegistrations = byYear.reduce((sum, y) => sum + (y.registrations ?? 0), 0);
    const totalRoomNights = byYear.reduce((sum, y) => sum + (y.roomNights ?? 0), 0);
    const totalMealsAll = byYear.reduce(
      (sum, y) => sum + (y.avgDailyMeals != null ? y.avgDailyMeals * EVENT_DURATION_DAYS : 0),
      0
    );
    const averageDailyMeals =
      byYear.length > 0 ? Math.round(totalMealsAll / (byYear.length * EVENT_DURATION_DAYS)) : 0;

    // YoY growth: compare last two years that have actual registration data
    let yoyGrowthPercent: number | null = null;
    const yearsWithRegs = byYear
      .filter((y) => y.registrations != null && y.registrations > 0)
      .sort((a, b) => a.year - b.year);
    if (yearsWithRegs.length >= 2) {
      const prev = yearsWithRegs[yearsWithRegs.length - 2].registrations!;
      const curr = yearsWithRegs[yearsWithRegs.length - 1].registrations!;
      yoyGrowthPercent = Math.round(((curr - prev) / prev) * 10000) / 100;
    }

    const response: SummaryResponse = {
      totalRegistrations,
      totalRoomNights,
      averageDailyMeals,
      yoyGrowthPercent,
      byYear,
    };

    res.json({ data: response });
  })
);

export default router;
