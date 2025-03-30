#! /bin/bash

set -eo pipefail

if ! [ -x "$(command -v psql)" ]; then
    echo >&2 "Error: psql is not installed."
    exit 1
fi

if ! [ -x "$(command -v sqlx)" ]; then
    echo >&2 "Error: sqlx is not installed."
    echo >&2 "Use: cargo install --version="~0.7" sqlx-cli --no-default-features --features rustls,postgres"
    echo >&2 "You might need to install libpq-dev too"
    exit 1
fi

if ! [ -x "$(command -v docker)" ]; then
    echo >&2 "Error: docker is not installed."
    echo >&2 "If you are on WSL, start Docker Desktop."
    exit 1
fi

if ! docker --help > /dev/null; then
    echo >&2 "Error: docker is not started."
    echo >&2 "If you are on WSL, start Docker Desktop."
    exit 1
fi

DB_USER=${POSTGRES_USER:=postgres}
DB_PASSWORD=${POSTGRES_PASSWORD:=password}
DB_NAME=${POSTGRES_DB:=tosurnament}
DB_PORT=${POSTGRES_PORT:=5432}
DB_HOST=${POSTGRES_HOST:=localhost}

if [[ -z "${SKIP_DOCKER}" ]]; then
    container_name="tosurnament-local-db"
    if [ "$(docker ps -a -q -f name=$container_name)" ]; then
        if [ "$(docker ps -aq -f status=running -f name=$container_name)" ]; then
            docker stop $container_name > /dev/null
        fi
        docker rm $container_name > /dev/null
    fi
    docker build -t tosurnament-db -f docker/test-db.Dockerfile $(dirname "$0")/.. 2> /dev/null
    docker run \
        --name $container_name \
        -e POSTGRES_USER=${DB_USER} \
        -e POSTGRES_PASSWORD=${DB_PASSWORD} \
        -e POSTGRES_DB=${DB_NAME} \
        -p "${DB_PORT}":5432 \
        -d \
        tosurnament-db -N 1000 > /dev/null
fi

export PGPASSWORD="${DB_PASSWORD}"
until psql -h "${DB_HOST}" -U "${DB_USER}" -p "${DB_PORT}" -d "${DB_NAME}" -c '\q' 2> /dev/null; do
    if [ "$(docker ps -aq -f status=exited -f name=$container_name)" ]; then
        echo >&2 "Database container could not start. Check the container logs for more information."
        exit 1
    fi
    echo >&2 "Postgres is still unavailable - sleeping"
    sleep 1
done

echo >&2 "Postgres is up and running on port ${DB_PORT}!"
