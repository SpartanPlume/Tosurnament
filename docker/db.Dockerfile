FROM postgres:16

COPY crates/libs/core/migrations/* /docker-entrypoint-initdb.d/
COPY crates/libs/core/tests-data/* /docker-entrypoint-initdb.d/
