FROM postgres:16

COPY crates/libs/core/tests-data/*.csv /tests-data/
