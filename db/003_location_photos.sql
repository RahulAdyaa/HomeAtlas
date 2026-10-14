ALTER TABLE sources ADD COLUMN IF NOT EXISTS photo_source_id uuid;
ALTER TABLE items ADD COLUMN IF NOT EXISTS photo_source_id uuid;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='sources_photo_fk') THEN
  ALTER TABLE sources ADD CONSTRAINT sources_photo_fk FOREIGN KEY(household_id,photo_source_id) REFERENCES sources(household_id,id) ON DELETE SET NULL (photo_source_id);
  ALTER TABLE items ADD CONSTRAINT items_photo_fk FOREIGN KEY(household_id,photo_source_id) REFERENCES sources(household_id,id) ON DELETE SET NULL (photo_source_id);
 END IF;
END $$;
