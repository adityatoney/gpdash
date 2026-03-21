import dotenv from 'dotenv';
import path from 'path';

// Load .env from project root
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

import express from 'express';
import corsMiddleware from './middleware/cors';
import { errorHandler } from './middleware/errorHandler';
import { healthCheck } from './services/db';
import summaryRouter from './routes/summary';
import filtersRouter from './routes/filters';
import registrationsRouter from './routes/registrations';
import roomsRouter from './routes/rooms';
import mealsRouter from './routes/meals';
import agentRouter from './routes/agent';

const app = express();
const PORT = process.env.API_PORT ? parseInt(process.env.API_PORT, 10) : 3002;
const HOST = process.env.API_HOST || '0.0.0.0';

// Middleware
app.use(corsMiddleware);
app.use(express.json());

// Routes
app.get('/api/health', async (_req, res) => {
  const dbOk = await healthCheck();
  res.status(dbOk ? 200 : 503).json({
    status: dbOk ? 'ok' : 'degraded',
    db: dbOk ? 'connected' : 'unreachable',
    timestamp: new Date().toISOString(),
  });
});

app.use('/api/summary', summaryRouter);
app.use('/api/filters', filtersRouter);
app.use('/api/registrations', registrationsRouter);
app.use('/api/rooms', roomsRouter);
app.use('/api/meals', mealsRouter);
app.use('/api/agent', agentRouter);

// Error handler (must be last)
app.use(errorHandler);

app.listen(PORT, HOST, () => {
  console.log(`gpdash API server listening on http://${HOST}:${PORT}`);
});

export default app;
