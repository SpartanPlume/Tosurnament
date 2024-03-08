-- Add migration script here
CREATE TABLE IF NOT EXISTS tournaments(
    id SERIAL NOT NULL,
    name TEXT NOT NULL UNIQUE,
    acronym TEXT NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
)