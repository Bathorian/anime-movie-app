CREATE TABLE IF NOT EXISTS omdb_title_cache (
    imdb_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL DEFAULT 'omdb',
    title TEXT,
    year TEXT,
    rated TEXT,
    released TEXT,
    runtime TEXT,
    genre TEXT,
    director TEXT,
    writer TEXT,
    actors TEXT,
    language TEXT,
    country TEXT,
    awards TEXT,
    plot TEXT,
    metascore TEXT,
    imdb_rating TEXT,
    imdb_votes TEXT,
    response_status TEXT,
    error_message TEXT,
    raw_response TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omdb_title_cache_provider ON omdb_title_cache (provider);
