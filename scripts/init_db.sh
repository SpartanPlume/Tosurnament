#! /bin/bash

set -eo pipefail

basedir=$(dirname "$0")
cd $basedir/..

# Check if docker is installed and running
./scripts/utils/check_docker.sh

if ! [ -x "$(command -v psql)" ]; then
    echo >&2 "Error: psql is not installed."
    exit 1
fi

export $(grep -v '^#' docker/test/local.env | xargs)
DB_HOST="localhost"

container_name="tosurnament-local-db"
if [ "$(docker ps -a -q -f name=$container_name)" ]; then
    if [ "$(docker ps -aq -f status=running -f name=$container_name)" ]; then
        docker stop $container_name > /dev/null
    fi
    docker rm $container_name > /dev/null
fi
docker build -t tosurnament-local-db -f docker/test/test-db.Dockerfile $(dirname "$0")/.. 2> /dev/null
docker run \
    --name $container_name \
    -e POSTGRES_USER=$DB_USERNAME \
    -e POSTGRES_PASSWORD=$DB_PASSWORD \
    -e POSTGRES_DB=$DB_NAME \
    -p "$DB_PORT":5432 \
    -d \
    tosurnament-local-db -N 1000 > /dev/null

export PGPASSWORD="$DB_PASSWORD"
until psql -h "$DB_HOST" -U "$DB_USERNAME" -p "$DB_PORT" -d "$DB_NAME" -c '\q' 2> /dev/null; do
    if [ "$(docker ps -aq -f status=exited -f name=$container_name)" ]; then
        echo >&2 "Database container could not start. Check the container logs for more information."
        exit 1
    fi
    echo >&2 "Postgres is still unavailable - sleeping"
    sleep 1
done

echo >&2 "Postgres is up and running on port $DB_PORT!"
