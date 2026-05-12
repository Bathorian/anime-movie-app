CREATE TABLE IF NOT EXISTS name_basics (
    nconst TEXT PRIMARY KEY,
    primaryName TEXT,
    birthYear TEXT,
    deathYear TEXT,
    primaryProfession TEXT,
    knownForTitles TEXT
);

CREATE TABLE IF NOT EXISTS title_basics (
    tconst TEXT PRIMARY KEY,
    titleType TEXT,
    primaryTitle TEXT,
    originalTitle TEXT,
    isAdult SMALLINT,
    startYear TEXT,
    endYear TEXT,
    runtimeMinutes TEXT,
    genres TEXT
);

CREATE TABLE IF NOT EXISTS title_akas (
    titleId TEXT,
    ordering INTEGER,
    title TEXT,
    region TEXT,
    language TEXT,
    types TEXT,
    attributes TEXT,
    isOriginalTitle SMALLINT
);

CREATE TABLE IF NOT EXISTS title_crew (
    tconst TEXT PRIMARY KEY,
    directors TEXT,
    writers TEXT
);

CREATE TABLE IF NOT EXISTS title_episode (
    tconst TEXT PRIMARY KEY,
    parentTconst TEXT,
    seasonNumber TEXT,
    episodeNumber TEXT
);

CREATE TABLE IF NOT EXISTS title_principals (
    tconst TEXT,
    ordering INTEGER,
    nconst TEXT,
    category TEXT,
    job TEXT,
    characters TEXT
);

CREATE TABLE IF NOT EXISTS title_ratings (
    tconst TEXT PRIMARY KEY,
    averageRating FLOAT,
    numVotes INTEGER
);

CREATE TABLE IF NOT EXISTS imdb_media_cache (
    imdb_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    image_url TEXT,
    image_width INTEGER,
    image_height INTEGER,
    label TEXT,
    subtitle TEXT,
    kind TEXT,
    result_rank INTEGER,
    year INTEGER,
    raw_item TEXT,
    raw_response TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT imdb_media_cache_entity_type_chk CHECK (entity_type IN ('title', 'name'))
);

CREATE INDEX IF NOT EXISTS idx_title_principals_tconst ON title_principals (tconst);
CREATE INDEX IF NOT EXISTS idx_title_ratings_numvotes ON title_ratings (numVotes DESC);
CREATE INDEX IF NOT EXISTS idx_title_basics_primarytitle ON title_basics (primaryTitle);
CREATE INDEX IF NOT EXISTS idx_imdb_media_cache_entity_type ON imdb_media_cache (entity_type);
