import { Router, Request, Response } from 'express';
import { query } from '../services/db';
import catchAsync from '../utils/catchAsync';
import {
  parseFilterParams,
  buildRegistrationWhere,
  needsPersonJoin,
  whereClause,
} from '../services/queryBuilder';

const router = Router();

router.get(
  '/',
  catchAsync(async (req: Request, res: Response) => {
    const filters = parseFilterParams(req.query as Record<string, unknown>);
    const personJoin = needsPersonJoin(filters);
    const joinClause = personJoin
      ? 'JOIN persons p ON r.person_id = p.person_id'
      : '';

    const { conditions, params } = buildRegistrationWhere(filters);
    const where = whereClause(conditions);

    // byRegion always needs the person join for region_name
    const {
      conditions: regConditions,
      params: regParams,
    } = buildRegistrationWhere(filters);
    const regWhere = whereClause(regConditions);

    const [
      byYearResult,
      byRegionResult,
      newVsReturningResult,
      arrivalDistResult,
      lengthOfStayResult,
      specialNeedsResult,
    ] = await Promise.all([
      // 1. byYear
      query(
        `SELECT r.event_year, COUNT(*)::int AS count
         FROM registrations r
         ${joinClause}
         ${where}
         GROUP BY r.event_year
         ORDER BY r.event_year`,
        params,
      ),

      // 2. byRegion (always joins persons for region_name)
      query(
        `SELECT COALESCE(rr.region_name, 'Unknown') AS region,
                r.event_year, COUNT(*)::int AS count
         FROM registrations r
         JOIN persons p ON r.person_id = p.person_id
         LEFT JOIN ref_regions rr ON p.region_id = rr.region_id
         ${regWhere}
         GROUP BY rr.region_name, r.event_year
         ORDER BY rr.region_name, r.event_year`,
        regParams,
      ),

      // 3. newVsReturning
      query(
        `SELECT r.event_year,
                COUNT(*) FILTER (WHERE r.is_returning IS NOT true)::int AS new,
                COUNT(*) FILTER (WHERE r.is_returning = true)::int AS returning
         FROM registrations r
         ${joinClause}
         ${where}
         GROUP BY r.event_year
         ORDER BY r.event_year`,
        params,
      ),

      // 4. arrivalDistribution
      query(
        `SELECT r.event_year, r.arrival_date, COUNT(*)::int AS count
         FROM registrations r
         ${joinClause}
         ${where ? `${where} AND r.arrival_date IS NOT NULL` : 'WHERE r.arrival_date IS NOT NULL'}
         GROUP BY r.event_year, r.arrival_date
         ORDER BY r.arrival_date`,
        params,
      ),

      // 5. lengthOfStay
      query(
        `SELECT r.length_of_stay AS days, COUNT(*)::int AS count
         FROM registrations r
         ${joinClause}
         ${where ? `${where} AND r.length_of_stay IS NOT NULL` : 'WHERE r.length_of_stay IS NOT NULL'}
         GROUP BY r.length_of_stay
         ORDER BY r.length_of_stay`,
        params,
      ),

      // 6. specialNeeds
      query(
        `SELECT r.event_year, COUNT(*)::int AS count
         FROM registrations r
         ${joinClause}
         ${where ? `${where} AND (r.needs_mobility_aid = true OR r.special_assistance IS NOT NULL)` : 'WHERE (r.needs_mobility_aid = true OR r.special_assistance IS NOT NULL)'}
         GROUP BY r.event_year
         ORDER BY r.event_year`,
        params,
      ),
    ]);

    res.json({
      data: {
        byYear: byYearResult.rows.map((r: Record<string, unknown>) => ({
          year: r.event_year,
          count: r.count,
        })),
        byRegion: byRegionResult.rows.map((r: Record<string, unknown>) => ({
          region: r.region,
          year: r.event_year,
          count: r.count,
        })),
        newVsReturning: newVsReturningResult.rows.map((r: Record<string, unknown>) => ({
          year: r.event_year,
          new: r.new,
          returning: r.returning,
        })),
        arrivalDistribution: arrivalDistResult.rows.map((r: Record<string, unknown>) => ({
          year: r.event_year,
          date: r.arrival_date,
          count: r.count,
        })),
        lengthOfStay: lengthOfStayResult.rows.map((r: Record<string, unknown>) => ({
          days: r.days,
          count: r.count,
        })),
        specialNeeds: specialNeedsResult.rows.map((r: Record<string, unknown>) => ({
          year: r.event_year,
          count: r.count,
        })),
      },
    });
  }),
);

export default router;
