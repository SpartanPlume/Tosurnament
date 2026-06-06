CREATE TABLE IF NOT EXISTS stage_round(
    id SERIAL PRIMARY KEY,
    bracket_id INTEGER NOT NULL REFERENCES bracket,
    stage TEXT NOT NULL,
    round TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
