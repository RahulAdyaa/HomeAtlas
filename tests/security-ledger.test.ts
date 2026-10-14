import { randomUUID } from 'node:crypto';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { Pool } from 'pg';
import '../lib/pg-types';

// Real PostgreSQL integration tests. Every test owns fresh household fixtures.
// No mocked locks, transactions, balances, or credit functions.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://homeatlas:homeatlas@127.0.0.1:54329/homeatlas',
  max: 16,
  connectionTimeoutMillis: 5000,
});
const ownedHouseholds: string[] = [];
const actorId = randomUUID();
const anotherActorId = randomUUID();

async function household(allowance = 10) {
  const id = randomUUID();
  await pool.query('INSERT INTO households(id,name,created_by) VALUES($1,$2,$3)', [id, 'Security fixture', actorId]);
  ownedHouseholds.push(id);
  await pool.query('INSERT INTO memberships(household_id,user_id,role) VALUES($1,$2,\'owner\')', [id, actorId]);
  await pool.query('SELECT atlas_grant_credit($1,$2,$3,$4)', [id, 'fixture-grant', allowance, actorId]);
  return id;
}
async function balance(id: string) {
  const { rows } = await pool.query('SELECT available,reserved FROM credit_accounts WHERE household_id=$1', [id]);
  return rows[0];
}
async function reserve(id: string, operation: string, amount: number, actor = actorId, kind = 'question') {
  const { rows } = await pool.query('SELECT atlas_reserve_credit($1,$2,$3,$4,$5) AS status', [id, operation, kind, amount, actor]);
  return rows[0].status;
}
async function settle(id: string, operation: string, success: boolean) {
  const { rows } = await pool.query('SELECT atlas_settle_credit($1,$2,$3) AS changed', [id, operation, success]);
  return rows[0].changed;
}
async function reconciles(id: string) {
  const { rows } = await pool.query(`SELECT a.available,a.reserved,
    COALESCE(sum(l.available_delta),0)::bigint AS ledger_available,
    COALESCE(sum(l.reserved_delta),0)::bigint AS ledger_reserved
    FROM credit_accounts a LEFT JOIN credit_ledger l ON l.household_id=a.household_id
    WHERE a.household_id=$1 GROUP BY a.household_id`, [id]);
  expect(rows[0].available).toBe(rows[0].ledger_available);
  expect(rows[0].reserved).toBe(rows[0].ledger_reserved);
}

beforeAll(async () => {
  await pool.query(`INSERT INTO "user"(id,name,email,"emailVerified","createdAt","updatedAt")
    VALUES($1,'Security reviewer',$2,true,now(),now()),($3,'Other reviewer',$4,true,now(),now())`,
    [actorId, `security-${actorId}@example.invalid`, anotherActorId, `security-${anotherActorId}@example.invalid`]);
});
afterAll(async () => {
  try {
    if (ownedHouseholds.length) await pool.query('DELETE FROM households WHERE id=ANY($1::uuid[])', [ownedHouseholds]);
    await pool.query('DELETE FROM "user" WHERE id=ANY($1::text[])', [[actorId, anotherActorId]]);
  } finally { await pool.end(); }
});

describe('independent real-database credit security', () => {
  it('prevents concurrent overspending and reconciles ledger deltas', async () => {
    const id = await household(10);
    const outcomes = await Promise.allSettled(Array.from({ length: 12 }, (_, i) => reserve(id, `parallel-${i}`, 3)));
    expect(outcomes.filter(x => x.status === 'fulfilled')).toHaveLength(3);
    expect(outcomes.filter(x => x.status === 'rejected')).toHaveLength(9);
    expect(await balance(id)).toEqual({ available: 1, reserved: 9 });
    await reconciles(id);
  });

  it('deduplicates simultaneous reservations with the same operation ID', async () => {
    const id = await household();
    const results = await Promise.all(Array.from({ length: 12 }, () => reserve(id, 'one-operation', 4)));
    expect(results.filter(x => x === 'created')).toHaveLength(1);
    expect(results.filter(x => x === 'reserved')).toHaveLength(11);
    expect(await balance(id)).toEqual({ available: 6, reserved: 4 });
    const { rows } = await pool.query('SELECT kind,count(*)::int AS count FROM credit_ledger WHERE household_id=$1 GROUP BY kind', [id]);
    expect(rows.find(x => x.kind === 'reservation')?.count).toBe(1);
    await reconciles(id);
  });

  it('charges once when success callbacks race and rejects a later refund transition', async () => {
    const id = await household();
    await reserve(id, 'settlement', 4);
    const results = await Promise.all(Array.from({ length: 12 }, () => settle(id, 'settlement', true)));
    expect(results.filter(Boolean)).toHaveLength(1);
    expect(await settle(id, 'settlement', false)).toBe(false);
    expect(await reserve(id, 'settlement', 4)).toBe('charged');
    expect(await balance(id)).toEqual({ available: 6, reserved: 0 });
    await reconciles(id);
  });

  it('refunds once, preserves retry idempotency, and permits a distinct retry operation', async () => {
    const id = await household();
    await reserve(id, 'failed', 7);
    const results = await Promise.all(Array.from({ length: 8 }, () => settle(id, 'failed', false)));
    expect(results.filter(Boolean)).toHaveLength(1);
    expect(await reserve(id, 'failed', 7)).toBe('refunded');
    expect(await settle(id, 'failed', true)).toBe(false);
    expect(await balance(id)).toEqual({ available: 10, reserved: 0 });
    expect(await reserve(id, 'failed-retry', 7)).toBe('created');
    expect(await settle(id, 'failed-retry', true)).toBe(true);
    expect(await balance(id)).toEqual({ available: 3, reserved: 0 });
    await reconciles(id);
  });

  it('rejects replay with a different cost, operation kind, or actor', async () => {
    const id = await household();
    await reserve(id, 'bound-operation', 4);
    await expect(reserve(id, 'bound-operation', 1)).rejects.toThrow(/Operation ID conflict/);
    await expect(reserve(id, 'bound-operation', 4, actorId, 'upload')).rejects.toThrow(/Operation ID conflict/);
    await expect(reserve(id, 'bound-operation', 4, anotherActorId)).rejects.toThrow(/Operation ID conflict/);
    expect(await balance(id)).toEqual({ available: 6, reserved: 4 });
    await reconciles(id);
  });

  it('scopes operation IDs and settlement to the household', async () => {
    const first = await household();
    const second = await household(20);
    await reserve(first, 'shared-client-id', 3);
    await expect(settle(second, 'shared-client-id', true)).rejects.toThrow(/Unknown reservation/);
    await reserve(second, 'shared-client-id', 8);
    await settle(second, 'shared-client-id', true);
    expect(await balance(first)).toEqual({ available: 7, reserved: 3 });
    expect(await balance(second)).toEqual({ available: 12, reserved: 0 });
    await reconciles(first);
    await reconciles(second);
  });

  it('makes concurrent monthly grants idempotent', async () => {
    const id = await household();
    const results = await Promise.all(Array.from({ length: 8 }, () => pool.query(
      'SELECT atlas_grant_credit($1,$2,$3,$4) AS granted', [id, 'month-2026-10', 20, actorId])));
    expect(results.filter(x => x.rows[0].granted)).toHaveLength(1);
    expect(await balance(id)).toEqual({ available: 30, reserved: 0 });
    await reconciles(id);
  });

  it('rejects non-positive costs and grants without changing balances', async () => {
    const id = await household();
    await expect(reserve(id, 'zero', 0)).rejects.toThrow(/Invalid credit cost/);
    await expect(reserve(id, 'negative', -8)).rejects.toThrow(/Invalid credit cost/);
    await expect(pool.query('SELECT atlas_grant_credit($1,$2,$3,$4)', [id, 'negative-grant', -8, actorId])).rejects.toThrow(/Invalid credit grant/);
    expect(await balance(id)).toEqual({ available: 10, reserved: 0 });
    await reconciles(id);
  });

  it('rolls back reservation and ledger together when enclosing work fails', async () => {
    const id = await household();
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('SELECT atlas_reserve_credit($1,$2,$3,$4,$5)', [id, 'rolled-back', 'upload', 8, actorId]);
      await client.query('ROLLBACK');
    } finally { client.release(); }
    expect(await balance(id)).toEqual({ available: 10, reserved: 0 });
    const { rows } = await pool.query('SELECT count(*)::int AS count FROM credit_reservations WHERE household_id=$1', [id]);
    expect(rows[0].count).toBe(0);
    await reconciles(id);
  });

  it('rejects updates and individual deletes of ledger entries', async () => {
    const id = await household();
    await expect(pool.query('UPDATE credit_ledger SET amount=999 WHERE household_id=$1', [id])).rejects.toThrow(/append-only/);
    await expect(pool.query('DELETE FROM credit_ledger WHERE household_id=$1', [id])).rejects.toThrow(/append-only/);
    expect(await balance(id)).toEqual({ available: 10, reserved: 0 });
    await reconciles(id);
  });

  it('rejects cross-household parent IDs at the database layer', async () => {
    const first = await household();
    const second = await household();
    const roomId = randomUUID();
    await pool.query('INSERT INTO rooms(id,household_id,name) VALUES($1,$2,$3)', [roomId, first, 'Private room']);
    await expect(pool.query('INSERT INTO items(household_id,room_id,name) VALUES($1,$2,$3)', [second, roomId, 'Forged item'])).rejects.toThrow(/foreign key/);
    await expect(pool.query('INSERT INTO sources(household_id,room_id,title,mime_type,created_by) VALUES($1,$2,$3,$4,$5)', [second, roomId, 'Forged source', 'application/pdf', actorId])).rejects.toThrow(/foreign key/);
  });

  it('rejects source/version mismatches even when both records belong to the same household', async () => {
    const id = await household();
    const source = randomUUID(), otherSource = randomUUID(), version = randomUUID();
    await pool.query("INSERT INTO sources(id,household_id,title,mime_type,created_by) VALUES($1,$3,'First','application/pdf',$4),($2,$3,'Second','application/pdf',$4)", [source, otherSource, id, actorId]);
    await pool.query("INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES($1,$2,$3,1,'test-only-path','test-only-hash',1,'application/pdf')", [version, id, source]);
    await expect(pool.query('UPDATE sources SET current_version_id=$1 WHERE id=$2', [version, otherSource])).rejects.toThrow(/foreign key/);
    await expect(pool.query("INSERT INTO chunks(household_id,source_id,version_id,text) VALUES($1,$2,$3,'Mismatched provenance')", [id, otherSource, version])).rejects.toThrow(/foreign key/);
    await expect(pool.query("INSERT INTO ingestion_jobs(household_id,source_id,version_id,actor_id,operation_id) VALUES($1,$2,$3,$4,'mismatched-version')", [id, otherSource, version, actorId])).rejects.toThrow(/foreign key/);
    await expect(pool.query("INSERT INTO image_assets(household_id,source_id,version_id,storage_path) VALUES($1,$2,$3,'test-only-path')", [id, otherSource, version])).rejects.toThrow(/foreign key/);
  });
});

// Exercises the requested ten-billion allowance with grants that retain int4 operation amounts.
it('supports ten-billion balances with exact reservations, refunds, and ledger totals', async () => {
 const id=await household(1);
 await pool.query('SELECT atlas_grant_credit($1,$2,$3,$4)',[id,'large-grant-rest',1999999999,actorId]);
 for(let i=0;i<4;i++)await pool.query('SELECT atlas_grant_credit($1,$2,$3,$4)',[id,`large-grant-${i}`,2000000000,actorId]);
 expect((await balance(id)).available).toBe(10000000000);
 const op=randomUUID();expect(await reserve(id,op,5)).toBe('created');
 expect(await balance(id)).toEqual({available:9999999995,reserved:5});
 expect(await settle(id,op,false)).toBe(true);
 expect(await balance(id)).toEqual({available:10000000000,reserved:0});
 await reconciles(id);
});
