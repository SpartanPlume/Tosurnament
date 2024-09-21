FROM postgres:16

COPY crates/libs/core/migrations/* /docker-entrypoint-initdb.d/
