ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS location_matches jsonb NOT NULL DEFAULT '[]';
