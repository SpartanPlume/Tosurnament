CREATE TABLE IF NOT EXISTS tournaments(
    id uuid NOT NULL,
    PRIMARY KEY(id),
    name TEXT NOT NULL UNIQUE,
    acronym TEXT NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
)