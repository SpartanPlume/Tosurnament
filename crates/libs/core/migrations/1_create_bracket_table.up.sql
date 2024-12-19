CREATE TABLE IF NOT EXISTS bracket(
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournament,
    name TEXT DEFAULT NULL,
    current_round TEXT NOT NULL DEFAULT 'NotStarted',
    qualifiers_type TEXT DEFAULT NULL,
    group_stage_type TEXT DEFAULT NULL,
    main_stage_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);