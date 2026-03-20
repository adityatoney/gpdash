import { Router, Request, Response } from 'express';
import { query } from '../services/db';
import catchAsync from '../utils/catchAsync';

const router = Router();

router.get('/status', catchAsync(async (_req: Request, res: Response) => {
  const result = await query(
    `SELECT job_id, status, phase, progress, current_step, errors, started_at, completed_at
     FROM agent_jobs ORDER BY started_at DESC LIMIT 1`
  );

  if (result.rows.length === 0) {
    res.json({ data: { status: 'idle', lastRun: null } });
    return;
  }

  const job = result.rows[0] as Record<string, unknown>;
  res.json({
    data: {
      status: job.status as string,
      phase: job.phase,
      progressPct: job.progress,
      currentStep: job.current_step,
      error: job.errors ? (job.errors as string[]).join('; ') : null,
      startedAt: job.started_at,
      completedAt: job.completed_at,
      jobId: job.job_id,
    },
  });
}));

export default router;
