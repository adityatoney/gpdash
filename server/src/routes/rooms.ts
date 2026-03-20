import { Router, Request, Response } from 'express';
import { query } from '../services/db';
import catchAsync from '../utils/catchAsync';
import {
  parseFilterParams,
  buildRoomWhere,
  needsPersonJoin,
  whereClause,
} from '../services/queryBuilder';

const router = Router();

router.get(
  '/',
  catchAsync(async (req: Request, res: Response) => {
    const filters = parseFilterParams(req.query as Record<string, unknown>);
    const personJoin = needsPersonJoin(filters);
    const roomPersonJoin = personJoin
      ? 'JOIN persons p ON rm.primary_room_holder_id = p.person_id'
      : '';

    const { conditions, params } = buildRoomWhere(filters);
    const where = whereClause(conditions);

    // Resolve years for checkInOut subqueries
    let allYears: number[];
    if (filters.years.length > 0) {
      allYears = filters.years;
    } else {
      const yr = await query('SELECT DISTINCT event_year FROM events ORDER BY event_year');
      allYears = yr.rows.map((r: Record<string, unknown>) => r.event_year as number);
    }

    const [
      byTypeResult,
      utilizationResult,
      roomsPerAttendeeResult,
      checkInOutResult,
    ] = await Promise.all([
      // 1. byType (grouped by category)
      query(
        `SELECT COALESCE(rc.category_name, 'Unknown') AS type_name,
                rm.event_year, COUNT(*)::int AS count,
                ROUND(AVG(rm.room_occupancy)::numeric, 1) AS avg_occupancy
         FROM rooms rm
         LEFT JOIN ref_room_types rt ON rm.room_type_assigned_id = rt.room_type_id
         LEFT JOIN ref_room_categories rc ON rt.category_id = rc.category_id
         ${roomPersonJoin}
         ${where}
         GROUP BY rc.category_name, rc.display_order, rm.event_year
         ORDER BY rc.display_order, rm.event_year`,
        params,
      ),

      // 2. utilizationByYear
      query(
        `SELECT rm.event_year, COUNT(*)::int AS total_rooms,
                ROUND(AVG(rm.room_occupancy)::numeric, 1) AS avg_occupancy
         FROM rooms rm
         ${roomPersonJoin}
         ${where}
         GROUP BY rm.event_year
         ORDER BY rm.event_year`,
        params,
      ),

      // 3. roomsPerAttendee - two subqueries joined
      query(
        `SELECT
           room_data.event_year AS year,
           COALESCE(reg_data.registrations, 0)::int AS registrations,
           room_data.rooms::int AS rooms,
           CASE WHEN COALESCE(reg_data.registrations, 0) > 0
             THEN ROUND(room_data.rooms::numeric / reg_data.registrations, 2)
             ELSE NULL
           END AS ratio
         FROM (
           SELECT rm.event_year, COUNT(*) AS rooms
           FROM rooms rm
           ${roomPersonJoin}
           ${where}
           GROUP BY rm.event_year
         ) room_data
         LEFT JOIN (
           SELECT event_year, COUNT(*) AS registrations
           FROM registrations
           ${filters.years.length > 0 ? 'WHERE event_year = ANY($1)' : ''}
           GROUP BY event_year
         ) reg_data ON room_data.event_year = reg_data.event_year
         ORDER BY room_data.event_year`,
        params,
      ),

      // 4. checkInOut — uses separate param for the date universe query
      (() => {
        const ciParams = [...params];
        const ciYearsIdx = ciParams.length + 1;
        ciParams.push(allYears);
        return query(
          `SELECT d.date,
                  COALESCE(ci.cnt, 0)::int AS check_ins,
                  COALESCE(co.cnt, 0)::int AS check_outs
           FROM (
             SELECT DISTINCT check_in_date AS date FROM rooms
             WHERE event_year = ANY($${ciYearsIdx}) AND check_in_date IS NOT NULL
             UNION
             SELECT DISTINCT check_out_date FROM rooms
             WHERE event_year = ANY($${ciYearsIdx}) AND check_out_date IS NOT NULL
           ) d
           LEFT JOIN (
             SELECT rm.check_in_date, COUNT(*)::int AS cnt
             FROM rooms rm
             ${roomPersonJoin}
             ${where ? `${where} AND rm.check_in_date IS NOT NULL` : 'WHERE rm.check_in_date IS NOT NULL'}
             GROUP BY rm.check_in_date
           ) ci ON d.date = ci.check_in_date
           LEFT JOIN (
             SELECT rm.check_out_date, COUNT(*)::int AS cnt
             FROM rooms rm
             ${roomPersonJoin}
             ${where ? `${where} AND rm.check_out_date IS NOT NULL` : 'WHERE rm.check_out_date IS NOT NULL'}
             GROUP BY rm.check_out_date
           ) co ON d.date = co.check_out_date
           ORDER BY d.date`,
          ciParams,
        );
      })(),
    ]);

    res.json({
      data: {
        byType: byTypeResult.rows.map((r: Record<string, unknown>) => ({
          typeName: r.type_name,
          year: r.event_year,
          count: r.count,
          avgOccupancy: r.avg_occupancy != null ? parseFloat(r.avg_occupancy as string) : null,
        })),
        utilizationByYear: utilizationResult.rows.map((r: Record<string, unknown>) => ({
          year: r.event_year,
          totalRooms: r.total_rooms,
          avgOccupancy: r.avg_occupancy != null ? parseFloat(r.avg_occupancy as string) : null,
        })),
        roomsPerAttendee: roomsPerAttendeeResult.rows.map((r: Record<string, unknown>) => ({
          year: r.year,
          registrations: r.registrations,
          rooms: r.rooms,
          ratio: r.ratio != null ? parseFloat(r.ratio as string) : null,
        })),
        checkInOut: checkInOutResult.rows.map((r: Record<string, unknown>) => ({
          date: r.date,
          checkIns: r.check_ins,
          checkOuts: r.check_outs,
        })),
      },
    });
  }),
);

export default router;
