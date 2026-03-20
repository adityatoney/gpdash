import { Router, Request, Response } from 'express';
import { query } from '../services/db';
import catchAsync from '../utils/catchAsync';
import { FiltersResponse } from '../types';

const router = Router();

router.get(
  '/',
  catchAsync(async (_req: Request, res: Response) => {
    const [yearsResult, regionsResult, roomTypesResult, dateRangeResult] =
      await Promise.all([
        query('SELECT event_year FROM events ORDER BY event_year'),
        query('SELECT region_id, region_code, region_name FROM ref_regions ORDER BY region_name'),
        query('SELECT category_id, category_code, category_name FROM ref_room_categories ORDER BY display_order'),
        query('SELECT MIN(start_date) as min_date, MAX(end_date) as max_date FROM events'),
      ]);

    const years = yearsResult.rows.map(
      (r: { event_year: number }) => r.event_year
    );

    const regions = regionsResult.rows.map(
      (r: { region_id: number; region_code: string; region_name: string }) => ({
        id: r.region_id,
        code: r.region_code,
        name: r.region_name,
      })
    );

    const roomTypes = roomTypesResult.rows.map(
      (r: { category_id: number; category_code: string; category_name: string }) => ({
        id: r.category_id,
        code: r.category_code,
        name: r.category_name,
      })
    );

    const dateRow = dateRangeResult.rows[0] as {
      min_date: string | null;
      max_date: string | null;
    };
    const dateRange = {
      min: dateRow.min_date ?? '',
      max: dateRow.max_date ?? '',
    };

    const response: FiltersResponse = {
      years,
      regions,
      roomTypes,
      dateRange,
    };

    res.json({ data: response });
  })
);

export default router;
