import { Pool, QueryResult } from 'pg';

let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 10,
    });
  }
  return pool;
}

async function query(text: string, params?: unknown[]): Promise<QueryResult> {
  return getPool().query(text, params);
}

async function healthCheck(): Promise<boolean> {
  try {
    const result = await query('SELECT 1');
    return result.rowCount === 1;
  } catch {
    return false;
  }
}

export { query, getPool, healthCheck };
