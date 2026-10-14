#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
umask 077
mkdir -p .data/backups
RESTORE_DATABASE="homeatlas_restore_$(date +%s)"
pg_dump -h 127.0.0.1 -p 54329 -U homeatlas -Fc homeatlas > .data/backups/verification.dump
createdb -h 127.0.0.1 -p 54329 -U homeatlas "$RESTORE_DATABASE"
trap 'dropdb -h 127.0.0.1 -p 54329 -U homeatlas "$RESTORE_DATABASE"' EXIT
pg_restore -h 127.0.0.1 -p 54329 -U homeatlas --no-owner -d "$RESTORE_DATABASE" .data/backups/verification.dump
HOMEATLAS_RESTORE_DB="$RESTORE_DATABASE" node --input-type=module <<'JS'
import pg from 'pg';
const source=new pg.Client({connectionString:'postgres://homeatlas:homeatlas@127.0.0.1:54329/homeatlas'}),restored=new pg.Client({connectionString:`postgres://homeatlas:homeatlas@127.0.0.1:54329/${process.env.HOMEATLAS_RESTORE_DB}`});await source.connect();await restored.connect();
for(const table of ['households','memberships','sources','source_versions','chunks','credit_accounts','credit_ledger']){const a=(await source.query(`SELECT count(*)::int AS n FROM ${table}`)).rows[0].n,b=(await restored.query(`SELECT count(*)::int AS n FROM ${table}`)).rows[0].n;if(a!==b)throw new Error(table+' restore mismatch');console.log('PASS restored rows',table,a)}
const ledger=await restored.query(`SELECT a.household_id FROM credit_accounts a LEFT JOIN (SELECT household_id,sum(available_delta) available,sum(reserved_delta) reserved FROM credit_ledger GROUP BY household_id) l USING(household_id) WHERE a.available<>COALESCE(l.available,0) OR a.reserved<>COALESCE(l.reserved,0)`);if(ledger.rows.length)throw new Error('Restored credit ledger does not reconcile');console.log('PASS restored ledger reconciliation');await source.end();await restored.end();
JS
