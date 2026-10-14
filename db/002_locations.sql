-- Additive hierarchy. Legacy room UUIDs remain the room location UUIDs.
CREATE TABLE IF NOT EXISTS locations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), household_id uuid NOT NULL REFERENCES households(id) ON DELETE CASCADE,
 name text NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 160), type text NOT NULL CHECK(type IN ('home','room','zone','container')),
 parent_id uuid, preset text NOT NULL DEFAULT 'area', position jsonb NOT NULL DEFAULT '{"x":0,"y":0,"z":0}',
 size jsonb NOT NULL DEFAULT '{"x":2,"y":1,"z":2}', rotation double precision NOT NULL DEFAULT 0,
 icon text NOT NULL DEFAULT 'box', color text NOT NULL DEFAULT '#dce7f6', openings jsonb NOT NULL DEFAULT '[]',
 attached boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(household_id,id), FOREIGN KEY(household_id,parent_id) REFERENCES locations(household_id,id),
 CHECK((type='home' AND parent_id IS NULL) OR (type<>'home' AND parent_id IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS one_location_home ON locations(household_id) WHERE type='home';
CREATE INDEX IF NOT EXISTS location_parent ON locations(household_id,parent_id);
INSERT INTO locations(id,household_id,name,type) SELECT id,id,name,'home' FROM households ON CONFLICT DO NOTHING;
INSERT INTO locations(id,household_id,name,type,parent_id,preset,color,position,size)
 SELECT id,household_id,name,'room',household_id,kind,color,
 jsonb_build_object('x',((row_number() OVER(PARTITION BY household_id ORDER BY created_at,id)-1)%3)*5,'y',0,'z',floor((row_number() OVER(PARTITION BY household_id ORDER BY created_at,id)-1)/3.0)*5),
 '{"x":4.8,"y":2.5,"z":4.8}' FROM rooms ON CONFLICT DO NOTHING;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS location_id uuid;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS location_path text NOT NULL DEFAULT '';
ALTER TABLE items ADD COLUMN IF NOT EXISTS location_id uuid;
ALTER TABLE items ADD COLUMN IF NOT EXISTS location_path text NOT NULL DEFAULT '';
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='sources_location_fk') THEN
 ALTER TABLE sources ADD CONSTRAINT sources_location_fk FOREIGN KEY(household_id,location_id) REFERENCES locations(household_id,id);
 ALTER TABLE items ADD CONSTRAINT items_location_fk FOREIGN KEY(household_id,location_id) REFERENCES locations(household_id,id);
 END IF;
END $$;
CREATE OR REPLACE FUNCTION atlas_location_path(node uuid) RETURNS text LANGUAGE sql STABLE AS $$
 WITH RECURSIVE ancestors AS (
 SELECT id,parent_id,name,type,0 depth FROM locations WHERE id=node
 UNION ALL SELECT l.id,l.parent_id,l.name,l.type,a.depth+1 FROM locations l JOIN ancestors a ON l.id=a.parent_id WHERE a.depth<16
 ) SELECT coalesce(string_agg(name,' > ' ORDER BY depth DESC) FILTER(WHERE type<>'home'),(SELECT name FROM ancestors WHERE type='home'),'') FROM ancestors;
$$;
CREATE OR REPLACE FUNCTION atlas_location_room(node uuid) RETURNS uuid LANGUAGE sql STABLE AS $$
 WITH RECURSIVE ancestors AS (SELECT id,parent_id,type FROM locations WHERE id=node UNION ALL SELECT l.id,l.parent_id,l.type FROM locations l JOIN ancestors a ON l.id=a.parent_id)
 SELECT id FROM ancestors WHERE type='room' LIMIT 1;
$$;
CREATE OR REPLACE FUNCTION atlas_location_validate() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_type text;
BEGIN
 IF TG_OP='UPDATE' AND (NEW.id<>OLD.id OR NEW.household_id<>OLD.household_id OR NEW.type<>OLD.type) THEN RAISE EXCEPTION 'Location identity cannot change'; END IF;
 IF NEW.type<>'home' THEN
 SELECT type INTO parent_type FROM locations WHERE id=NEW.parent_id AND household_id=NEW.household_id;
 IF NOT ((NEW.type='room' AND parent_type='home') OR (NEW.type='zone' AND parent_type='room') OR (NEW.type='container' AND parent_type='zone')) THEN RAISE EXCEPTION 'Invalid location parent'; END IF;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS location_validate ON locations;
CREATE TRIGGER location_validate BEFORE INSERT OR UPDATE ON locations FOR EACH ROW EXECUTE FUNCTION atlas_location_validate();
CREATE OR REPLACE FUNCTION atlas_legacy_location() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME='households' THEN
 INSERT INTO locations(id,household_id,name,type) VALUES(NEW.id,NEW.id,NEW.name,'home') ON CONFLICT(id) DO UPDATE SET name=excluded.name;
 ELSE
 INSERT INTO locations(id,household_id,name,type,parent_id,preset,color,position,size) VALUES(NEW.id,NEW.household_id,NEW.name,'room',NEW.household_id,NEW.kind,NEW.color,
 jsonb_build_object('x',((SELECT count(*) FROM locations WHERE household_id=NEW.household_id AND type='room')%3)*5,'y',0,'z',floor((SELECT count(*) FROM locations WHERE household_id=NEW.household_id AND type='room')/3.0)*5),'{"x":4.8,"y":2.5,"z":4.8}')
 ON CONFLICT(id) DO UPDATE SET name=excluded.name,preset=excluded.preset;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS household_location_sync ON households;
CREATE TRIGGER household_location_sync AFTER INSERT OR UPDATE OF name ON households FOR EACH ROW EXECUTE FUNCTION atlas_legacy_location();
DROP TRIGGER IF EXISTS room_location_sync ON rooms;
CREATE TRIGGER room_location_sync AFTER INSERT OR UPDATE OF name,kind ON rooms FOR EACH ROW EXECUTE FUNCTION atlas_legacy_location();
CREATE OR REPLACE FUNCTION atlas_attachment_location() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' AND NEW.room_id IS DISTINCT FROM OLD.room_id AND NEW.location_id IS NOT DISTINCT FROM OLD.location_id THEN NEW.location_id=coalesce(NEW.room_id,NEW.household_id); END IF;
 NEW.location_id=coalesce(NEW.location_id,NEW.room_id,NEW.household_id);
 IF NOT EXISTS(SELECT 1 FROM locations WHERE id=NEW.location_id AND household_id=NEW.household_id) THEN RAISE EXCEPTION 'Location outside household: foreign key violation' USING ERRCODE='23503'; END IF;
 NEW.room_id=atlas_location_room(NEW.location_id); NEW.location_path=atlas_location_path(NEW.location_id);
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS source_location ON sources;
CREATE TRIGGER source_location BEFORE INSERT OR UPDATE OF location_id,room_id ON sources FOR EACH ROW EXECUTE FUNCTION atlas_attachment_location();
DROP TRIGGER IF EXISTS item_location ON items;
CREATE TRIGGER item_location BEFORE INSERT OR UPDATE OF location_id,room_id ON items FOR EACH ROW EXECUTE FUNCTION atlas_attachment_location();
UPDATE sources SET location_id=coalesce(location_id,room_id,household_id);
UPDATE items SET location_id=coalesce(location_id,room_id,household_id);
CREATE OR REPLACE FUNCTION atlas_refresh_location_chunks() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 UPDATE chunks SET text='Location: '||NEW.location_path||E'\n\n'||coalesce(metadata->>'content_text',text),
 metadata=metadata||jsonb_build_object('content_text',coalesce(metadata->>'content_text',text),'location_id',NEW.location_id,'location_path',NEW.location_path,'location_embedding_pending',true),
 room_id=NEW.room_id,embedding=NULL,embedding_model=NULL WHERE source_id=NEW.id AND household_id=NEW.household_id;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS source_location_chunks ON sources;
CREATE TRIGGER source_location_chunks AFTER UPDATE OF location_id,location_path ON sources FOR EACH ROW WHEN(OLD.location_id IS DISTINCT FROM NEW.location_id OR OLD.location_path IS DISTINCT FROM NEW.location_path) EXECUTE FUNCTION atlas_refresh_location_chunks();
CREATE OR REPLACE FUNCTION atlas_location_changed() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.name IS DISTINCT FROM OLD.name OR NEW.parent_id IS DISTINCT FROM OLD.parent_id THEN
 WITH RECURSIVE descendants AS (SELECT NEW.id id UNION ALL SELECT l.id FROM locations l JOIN descendants d ON l.parent_id=d.id)
 UPDATE sources SET location_id=location_id WHERE location_id IN(SELECT id FROM descendants);
 WITH RECURSIVE descendants AS (SELECT NEW.id id UNION ALL SELECT l.id FROM locations l JOIN descendants d ON l.parent_id=d.id)
 UPDATE items SET location_id=location_id WHERE location_id IN(SELECT id FROM descendants);
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS location_changed ON locations;
CREATE TRIGGER location_changed AFTER UPDATE ON locations FOR EACH ROW EXECUTE FUNCTION atlas_location_changed();
-- Existing evidence stays addressable. Refresh its vector asynchronously, without charging upload credits.
UPDATE chunks c SET text='Location: '||s.location_path||E'\n\n'||c.text,
 metadata=c.metadata||jsonb_build_object('content_text',c.text,'location_id',s.location_id,'location_path',s.location_path,'location_embedding_pending',true),embedding=NULL,embedding_model=NULL
 FROM sources s WHERE s.id=c.source_id AND s.household_id=c.household_id AND NOT(c.metadata ? 'location_path');
