COPY tournament ( name, acronym) FROM PROGRAM 'egrep -v "^-- " "/tests-data/tournament.csv"' WITH (FORMAT CSV);
COPY bracket ( tournament_id, name, current_round, qualifiers_type, group_stage_type, main_stage_type) FROM PROGRAM 'egrep -v "^-- " "/tests-data/bracket.csv"' WITH (FORMAT CSV);
