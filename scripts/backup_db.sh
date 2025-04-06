#! /bin/bash

basedir=$(dirname "$0")
cd $basedir/..

if ! [ -x "$(command -v pg_dump)" ]; then
    echo >&2 "Error: pg_dump/psql is not installed."
    exit 1
fi

helpFunction() {
    echo >&2 "Usage: $0 [<phase>] [<target_file>]"
    echo >&2 "  <phase> must be one of LOCAL, DEV, TST, PRD."
    exit 1
}

if [ $# -gt 0 ] && [[ ! "$1" =~ \.sql$ ]]; then
    if ! phase=`./scripts/utils/parse_phase.sh $1`; then
        helpFunction
    fi
    shift 1
else
    if ! phase=`./scripts/utils/determine_current_phase.sh`; then
        exit 1
    fi
fi

if [ "$phase" = "local" ]; then
    export $(grep -v '^#' docker/test/local.env | xargs)
    export PGPASSWORD="$DB_PASSWORD"
else
    export $(grep -v '^#' docker/$phase.env | xargs)
    export PGPASSWORD=`cat docker/secrets/db_password.txt | tr -d '\n'`
fi

if ! nc -z "localhost" "$DB_PORT"; then
    echo >&2 "Error: Database is not available. Did you start tosurnament?"
    exit 1
fi

target_file="bak.sql"
if [ $# -gt 0 ]; then
    target_file="$1"
fi

container_name=`docker ps --filter "name=tosurnament-$phase-db" --format '{{.Names}}'`
docker exec $container_name sh -c "pg_dump $DB_NAME > /root/bak.sql"
docker cp $container_name:/root/bak.sql "$target_file"
docker exec $container_name sh -c "rm -f /root/bak.sql"

exit 0
