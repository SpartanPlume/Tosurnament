CREATE TABLE IF NOT EXISTS tournament(
    id SERIAL NOT NULL,
    name TEXT NOT NULL UNIQUE,
    acronym TEXT NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);