CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS households (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL, kind text NOT NULL DEFAULT 'apartment',
 address text NOT NULL DEFAULT '', created_by text NOT NULL REFERENCES "user"(id), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS memberships (
 household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE, user_id text NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
 role text NOT NULL CHECK(role IN ('owner','editor','viewer')), created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(household_id,user_id)
);
CREATE TABLE IF NOT EXISTS invitations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 email text NOT NULL, role text NOT NULL CHECK(role IN ('editor','viewer')), token_hash text NOT NULL UNIQUE,
 expires_at timestamptz NOT NULL, used_at timestamptz, created_by text NOT NULL REFERENCES "user"(id), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS rooms (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 name text NOT NULL, kind text NOT NULL DEFAULT 'living', color text NOT NULL DEFAULT '#d4bfa9', position jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(household_id,id)
);
CREATE TABLE IF NOT EXISTS items (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 room_id uuid, name text NOT NULL, category text NOT NULL DEFAULT 'appliance', make text NOT NULL DEFAULT '', model text NOT NULL DEFAULT '',
 serial_number text NOT NULL DEFAULT '', purchase_date date, warranty_date date, notes text NOT NULL DEFAULT '',
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(household_id,id),
 FOREIGN KEY(household_id,room_id) REFERENCES rooms(household_id,id)
);
CREATE TABLE IF NOT EXISTS sources (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 room_id uuid, item_id uuid, title text NOT NULL, mime_type text NOT NULL, current_version_id uuid,
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','processing','ready','failed')),
 created_by text NOT NULL REFERENCES "user"(id), created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(household_id,id),
 FOREIGN KEY(household_id,room_id) REFERENCES rooms(household_id,id), FOREIGN KEY(household_id,item_id) REFERENCES items(household_id,id)
);
CREATE TABLE IF NOT EXISTS source_versions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 source_id uuid NOT NULL, version integer NOT NULL, storage_path text NOT NULL, sha256 text NOT NULL, size_bytes bigint NOT NULL,
 mime_type text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(source_id,version), UNIQUE(household_id,id),
 FOREIGN KEY(household_id,source_id) REFERENCES sources(household_id,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS credit_accounts (
 household_id uuid PRIMARY KEY REFERENCES households(id) ON DELETE CASCADE, available bigint NOT NULL DEFAULT 0 CHECK(available>=0),
 reserved bigint NOT NULL DEFAULT 0 CHECK(reserved>=0), updated_at timestamptz NOT NULL DEFAULT now()
);
-- Preserve existing balances while supporting allowances beyond PostgreSQL int4.
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_attribute WHERE attrelid='credit_accounts'::regclass AND attname='available' AND atttypid='integer'::regtype) THEN
  ALTER TABLE credit_accounts ALTER COLUMN available TYPE bigint, ALTER COLUMN reserved TYPE bigint;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='credit_accounts'::regclass AND conname='credit_balance_safe_integer') THEN
  ALTER TABLE credit_accounts ADD CONSTRAINT credit_balance_safe_integer CHECK(available+reserved<=9007199254740991);
 END IF;
END $$;
CREATE TABLE IF NOT EXISTS credit_reservations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 operation_id text NOT NULL, kind text NOT NULL, amount integer NOT NULL CHECK(amount>0), actor_id text REFERENCES "user"(id),
 status text NOT NULL DEFAULT 'reserved' CHECK(status IN ('reserved','charged','refunded')),
 result jsonb, created_at timestamptz NOT NULL DEFAULT now(), settled_at timestamptz, UNIQUE(household_id,operation_id)
);
CREATE TABLE IF NOT EXISTS credit_ledger (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 operation_id text NOT NULL, kind text NOT NULL CHECK(kind IN ('grant','reservation','charge','refund')),
 amount integer NOT NULL CHECK(amount>0), available_delta integer NOT NULL, reserved_delta integer NOT NULL,
 actor_id text REFERENCES "user"(id), description text NOT NULL DEFAULT '', created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(household_id,operation_id,kind)
);
CREATE OR REPLACE FUNCTION atlas_ledger_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' THEN RAISE EXCEPTION 'Credit ledger is append-only'; END IF;
 IF TG_OP='DELETE' AND EXISTS(SELECT 1 FROM households WHERE id=OLD.household_id) THEN RAISE EXCEPTION 'Credit ledger is append-only'; END IF;
 RETURN OLD;
END $$;
DROP TRIGGER IF EXISTS credit_ledger_immutable ON credit_ledger;
CREATE TRIGGER credit_ledger_immutable BEFORE UPDATE OR DELETE ON credit_ledger FOR EACH ROW EXECUTE FUNCTION atlas_ledger_immutable();
CREATE OR REPLACE FUNCTION atlas_grant_credit(p_household uuid,p_operation text,p_amount integer,p_actor text DEFAULT NULL) RETURNS boolean LANGUAGE plpgsql AS $$
BEGIN
 IF p_amount<=0 THEN RAISE EXCEPTION 'Invalid credit grant'; END IF;
 INSERT INTO credit_accounts(household_id) VALUES(p_household) ON CONFLICT DO NOTHING;
 PERFORM 1 FROM credit_accounts WHERE household_id=p_household FOR UPDATE;
 IF EXISTS(SELECT 1 FROM credit_ledger WHERE household_id=p_household AND operation_id=p_operation AND kind='grant') THEN RETURN false; END IF;
 UPDATE credit_accounts SET available=available+p_amount,updated_at=now() WHERE household_id=p_household;
 INSERT INTO credit_ledger(household_id,operation_id,kind,amount,available_delta,reserved_delta,actor_id,description) VALUES(p_household,p_operation,'grant',p_amount,p_amount,0,p_actor,'Monthly household allowance');
 RETURN true;
END $$;
CREATE OR REPLACE FUNCTION atlas_reserve_credit(p_household uuid,p_operation text,p_kind text,p_amount integer,p_actor text) RETURNS text LANGUAGE plpgsql AS $$
DECLARE existing credit_reservations%ROWTYPE;
BEGIN
 IF p_amount<=0 THEN RAISE EXCEPTION 'Invalid credit cost'; END IF;
 PERFORM 1 FROM credit_accounts WHERE household_id=p_household FOR UPDATE;
 SELECT * INTO existing FROM credit_reservations WHERE household_id=p_household AND operation_id=p_operation;
 IF FOUND THEN
  IF existing.kind<>p_kind OR existing.amount<>p_amount OR existing.actor_id IS DISTINCT FROM p_actor THEN RAISE EXCEPTION 'Operation ID conflict'; END IF;
  RETURN existing.status;
 END IF;
 UPDATE credit_accounts SET available=available-p_amount,reserved=reserved+p_amount,updated_at=now() WHERE household_id=p_household AND available>=p_amount;
 IF NOT FOUND THEN RAISE EXCEPTION 'Insufficient credits'; END IF;
 INSERT INTO credit_reservations(household_id,operation_id,kind,amount,actor_id) VALUES(p_household,p_operation,p_kind,p_amount,p_actor);
 INSERT INTO credit_ledger(household_id,operation_id,kind,amount,available_delta,reserved_delta,actor_id,description) VALUES(p_household,p_operation,'reservation',p_amount,-p_amount,p_amount,p_actor,p_kind);
 RETURN 'created';
END $$;
CREATE OR REPLACE FUNCTION atlas_settle_credit(p_household uuid,p_operation text,p_success boolean) RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE reservation credit_reservations%ROWTYPE;
BEGIN
 PERFORM 1 FROM credit_accounts WHERE household_id=p_household FOR UPDATE;
 SELECT * INTO reservation FROM credit_reservations WHERE household_id=p_household AND operation_id=p_operation FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Unknown reservation'; END IF;
 IF reservation.status<>'reserved' THEN RETURN false; END IF;
 UPDATE credit_accounts SET available=available+CASE WHEN p_success THEN 0 ELSE reservation.amount END,reserved=reserved-reservation.amount,updated_at=now() WHERE household_id=p_household;
 UPDATE credit_reservations SET status=CASE WHEN p_success THEN 'charged' ELSE 'refunded' END,settled_at=now() WHERE id=reservation.id;
 INSERT INTO credit_ledger(household_id,operation_id,kind,amount,available_delta,reserved_delta,actor_id,description) VALUES(p_household,p_operation,CASE WHEN p_success THEN 'charge' ELSE 'refund' END,reservation.amount,CASE WHEN p_success THEN 0 ELSE reservation.amount END,-reservation.amount,reservation.actor_id,reservation.kind);
 RETURN true;
END $$;
CREATE TABLE IF NOT EXISTS ingestion_jobs (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 source_id uuid NOT NULL, version_id uuid NOT NULL, actor_id text NOT NULL REFERENCES "user"(id), operation_id text NOT NULL,
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','processing','ready','failed')), attempts integer NOT NULL DEFAULT 0,
 error text, started_at timestamptz, completed_at timestamptz, lease_expires_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(household_id,operation_id),
 FOREIGN KEY(household_id,source_id) REFERENCES sources(household_id,id) ON DELETE CASCADE,
 FOREIGN KEY(household_id,version_id) REFERENCES source_versions(household_id,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS chunks (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 source_id uuid NOT NULL, version_id uuid NOT NULL, item_id uuid, room_id uuid, text text NOT NULL,
 page integer, bbox jsonb, start_seconds double precision, end_seconds double precision,
 modality text NOT NULL DEFAULT 'text', embedding real[], embedding_model text, model_revision text,
 image_path text, metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(household_id,source_id) REFERENCES sources(household_id,id) ON DELETE CASCADE,
 FOREIGN KEY(household_id,version_id) REFERENCES source_versions(household_id,id) ON DELETE CASCADE,
 FOREIGN KEY(household_id,item_id) REFERENCES items(household_id,id), FOREIGN KEY(household_id,room_id) REFERENCES rooms(household_id,id)
);
CREATE TABLE IF NOT EXISTS image_assets (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 source_id uuid NOT NULL, version_id uuid NOT NULL, storage_path text NOT NULL, page integer, timestamp_seconds double precision,
 embedding real[], embedding_model text, metadata jsonb NOT NULL DEFAULT '{}',
 FOREIGN KEY(household_id,source_id) REFERENCES sources(household_id,id) ON DELETE CASCADE,
 FOREIGN KEY(household_id,version_id) REFERENCES source_versions(household_id,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS conversations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 user_id text NOT NULL REFERENCES "user"(id), title text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(household_id,id)
);
CREATE TABLE IF NOT EXISTS messages (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 conversation_id uuid NOT NULL, role text NOT NULL CHECK(role IN ('user','assistant')), content text NOT NULL,
 citations jsonb NOT NULL DEFAULT '[]', metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(household_id,conversation_id) REFERENCES conversations(household_id,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS tasks (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 item_id uuid, room_id uuid, title text NOT NULL, due_date date NOT NULL, recurrence_days integer CHECK(recurrence_days>0),
 completed_at timestamptz, created_by text NOT NULL REFERENCES "user"(id), created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(household_id,item_id) REFERENCES items(household_id,id), FOREIGN KEY(household_id,room_id) REFERENCES rooms(household_id,id)
);
CREATE TABLE IF NOT EXISTS maintenance_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 item_id uuid, task_id uuid REFERENCES tasks(id) ON DELETE SET NULL, user_id text NOT NULL REFERENCES "user"(id),
 description text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), FOREIGN KEY(household_id,item_id) REFERENCES items(household_id,id)
);
CREATE TABLE IF NOT EXISTS bookmarks (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 user_id text NOT NULL REFERENCES "user"(id), title text NOT NULL, question text NOT NULL DEFAULT '', answer text NOT NULL DEFAULT '',
 citations jsonb NOT NULL DEFAULT '[]', item_id uuid, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(household_id,item_id) REFERENCES items(household_id,id)
);
CREATE TABLE IF NOT EXISTS audit_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid REFERENCES households(id) ON DELETE CASCADE,
 actor_id text REFERENCES "user"(id), action text NOT NULL, target_id text, metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS rate_limits (
 key text PRIMARY KEY, count integer NOT NULL DEFAULT 1, expires_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS memberships_user_idx ON memberships(user_id);
CREATE INDEX IF NOT EXISTS items_household_idx ON items(household_id,room_id);
CREATE INDEX IF NOT EXISTS sources_household_idx ON sources(household_id,item_id);
CREATE INDEX IF NOT EXISTS chunks_scope_idx ON chunks(household_id,source_id,version_id);
CREATE INDEX IF NOT EXISTS chunks_lexical_idx ON chunks USING gin(to_tsvector('english',text));
CREATE INDEX IF NOT EXISTS jobs_queue_idx ON ingestion_jobs(status,created_at);
CREATE INDEX IF NOT EXISTS audit_household_idx ON audit_events(household_id,created_at DESC);
CREATE INDEX IF NOT EXISTS credit_ledger_household_idx ON credit_ledger(household_id,created_at DESC);
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS heartbeat_at timestamptz;
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS claim_token uuid;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS image_embedding real[];
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS image_embedding_model text;
-- Composite provenance constraints make source/version mismatches impossible even inside a tenant.
CREATE UNIQUE INDEX IF NOT EXISTS source_versions_provenance_idx ON source_versions(household_id,source_id,id);
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='sources_current_version_provenance') THEN
  ALTER TABLE sources ADD CONSTRAINT sources_current_version_provenance FOREIGN KEY(household_id,id,current_version_id) REFERENCES source_versions(household_id,source_id,id) DEFERRABLE INITIALLY DEFERRED;
  ALTER TABLE chunks ADD CONSTRAINT chunks_version_provenance FOREIGN KEY(household_id,source_id,version_id) REFERENCES source_versions(household_id,source_id,id) ON DELETE CASCADE;
  ALTER TABLE ingestion_jobs ADD CONSTRAINT jobs_version_provenance FOREIGN KEY(household_id,source_id,version_id) REFERENCES source_versions(household_id,source_id,id) ON DELETE CASCADE;
  ALTER TABLE image_assets ADD CONSTRAINT images_version_provenance FOREIGN KEY(household_id,source_id,version_id) REFERENCES source_versions(household_id,source_id,id) ON DELETE CASCADE;
 END IF;
END $$;
