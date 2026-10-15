CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
ALTER TABLE households ADD COLUMN IF NOT EXISTS data_version bigint NOT NULL DEFAULT 1;
CREATE TABLE IF NOT EXISTS search_aliases(alias text PRIMARY KEY, canonical text NOT NULL);
CREATE OR REPLACE FUNCTION atlas_search_basic(value text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
 SELECT trim(regexp_replace(regexp_replace(regexp_replace(lower(normalize(coalesce(value,''),NFKC) COLLATE "und-x-icu"),
 '([[:alpha:]])\1{2,}', '\1\1', 'g'),'[^[:alnum:][:space:]]',' ','g'),'[[:space:]]+',' ','g'));
$$;
CREATE OR REPLACE FUNCTION atlas_search_normalize(value text) RETURNS text LANGUAGE plpgsql STABLE AS $$
DECLARE result text; pair record;
BEGIN
 result:=atlas_search_basic(value);
 FOR pair IN SELECT alias,canonical FROM search_aliases ORDER BY length(alias) DESC,alias LOOP
  result:=regexp_replace(result COLLATE "und-x-icu",'\m'||pair.alias||'\M',pair.canonical,'g');
 END LOOP;
 RETURN result;
END $$;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS search_text text NOT NULL DEFAULT '';
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS search_terms tsvector NOT NULL DEFAULT '';
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS search_vector vector;
CREATE OR REPLACE FUNCTION atlas_chunk_search() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE src sources%ROWTYPE;
BEGIN
 SELECT * INTO src FROM sources WHERE id=NEW.source_id AND household_id=NEW.household_id;
 NEW.search_text:=atlas_search_normalize(NEW.text||' '||coalesce(src.title,'')||' '||coalesce(src.location_path,'')||' '||coalesce(NEW.metadata->>'tags',''));
 NEW.search_text:=NEW.search_text||' '||atlas_search_basic(NEW.text||' '||coalesce(src.title,''));
 NEW.search_terms:=to_tsvector('simple',NEW.search_text);
 NEW.search_vector:=CASE WHEN NEW.embedding IS NULL THEN NULL ELSE NEW.embedding::vector END;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS atlas_chunk_search_trigger ON chunks;
CREATE TRIGGER atlas_chunk_search_trigger BEFORE INSERT OR UPDATE OF text,embedding,metadata ON chunks FOR EACH ROW EXECUTE FUNCTION atlas_chunk_search();
CREATE INDEX IF NOT EXISTS chunks_search_terms ON chunks USING gin(search_terms);
CREATE INDEX IF NOT EXISTS chunks_search_trigrams ON chunks USING gin(search_text gin_trgm_ops);
CREATE OR REPLACE FUNCTION atlas_source_search() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.title IS DISTINCT FROM OLD.title OR NEW.location_path IS DISTINCT FROM OLD.location_path THEN
  UPDATE chunks SET text=text WHERE source_id=NEW.id AND household_id=NEW.household_id;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS atlas_source_search_trigger ON sources;
CREATE TRIGGER atlas_source_search_trigger AFTER UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION atlas_source_search();
CREATE OR REPLACE FUNCTION atlas_data_changed() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 UPDATE households SET data_version=data_version+1 WHERE id=CASE WHEN TG_OP='DELETE' THEN OLD.household_id ELSE NEW.household_id END;
 RETURN NULL;
END $$;
DO $$ DECLARE relation text; BEGIN
 FOREACH relation IN ARRAY ARRAY['sources','items','locations','chunks'] LOOP
  EXECUTE format('DROP TRIGGER IF EXISTS atlas_cache_invalidate ON %I',relation);
  EXECUTE format('CREATE TRIGGER atlas_cache_invalidate AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION atlas_data_changed()',relation);
 END LOOP;
END $$;
CREATE TABLE IF NOT EXISTS answer_cache (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 user_id text NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
 data_version bigint NOT NULL, config_version text NOT NULL,
 scope_key text NOT NULL, query_key text NOT NULL, query text NOT NULL,
 embedding vector, embedding_model text NOT NULL,
 answer jsonb NOT NULL, references_json jsonb NOT NULL DEFAULT '[]',
 latency_ms double precision NOT NULL DEFAULT 0,
 created_at timestamptz NOT NULL DEFAULT now(), last_used_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL, hit_count bigint NOT NULL DEFAULT 0,
 UNIQUE(household_id,user_id,data_version,config_version,scope_key,query_key)
);
CREATE INDEX IF NOT EXISTS answer_cache_scope ON answer_cache(household_id,user_id,data_version);
CREATE TABLE IF NOT EXISTS cache_metrics (
 household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 user_id text NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
 exact_hits bigint NOT NULL DEFAULT 0, semantic_hits bigint NOT NULL DEFAULT 0, misses bigint NOT NULL DEFAULT 0,
 guard_rejections bigint NOT NULL DEFAULT 0, semantic_candidates bigint NOT NULL DEFAULT 0,
 saved_ms double precision NOT NULL DEFAULT 0, lookup_ms double precision NOT NULL DEFAULT 0,
 PRIMARY KEY(household_id,user_id)
);
