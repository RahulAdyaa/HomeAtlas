import pg from 'pg';
import './pg-types';
const { Pool } = pg;
// Calendar dates must not shift when the Node host and household use different time zones.
pg.types.setTypeParser(1082, value => value);
const globalDb = globalThis as unknown as { atlasPool?: pg.Pool };
export const pool = globalDb.atlasPool ?? new Pool({
 connectionString: process.env.DATABASE_URL ?? 'postgres://homeatlas:homeatlas@127.0.0.1:54329/homeatlas',
 max: 12, idleTimeoutMillis: 30000, connectionTimeoutMillis: 5000,
});
if (process.env.NODE_ENV !== 'production') globalDb.atlasPool = pool;
export type DB = Pick<pg.PoolClient,'query'>;
export async function transaction<T>(fn: (db: pg.PoolClient) => Promise<T>): Promise<T> {
 const db = await pool.connect();
 try { await db.query('BEGIN'); const result = await fn(db); await db.query('COMMIT'); return result; }
 catch (error) { await db.query('ROLLBACK'); throw error; }
 finally { db.release(); }
}
export function camel<T=Record<string,unknown>>(row: Record<string,unknown>): T {
 return Object.fromEntries(Object.entries(row).map(([key,value])=>[key.replace(/_([a-z])/g,(_,c)=>c.toUpperCase()),value])) as T;
}
