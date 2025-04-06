#! /bin/bash

basedir=$(dirname "$0")
cd $basedir/..

if ! [ -x "$(command -v psql)" ]; then
    echo >&2 "Error: psql is not installed."
    exit 1
fi

helpFunction() {
    echo >&2 "Usage: $0 [<phase>] <sql_file> [<sql_file> ...]"
    echo >&2 "  <phase> must be one of LOCAL, DEV, TST, PRD."
    exit 1
}

if [ $# -eq 0 ]; then
    helpFunction
fi

if [[ ! "$1" =~ \.sql$ ]]; then
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

for sql_file in "$@"; do
    if [[ ! "$sql_file" =~ \.sql$ ]]; then
        echo >&2 "Warning: '$sql_file' is not a sql file. Skipping."
        continue
    elif [ ! -e "$sql_file" ]; then
        echo >&2 "Warning: '$sql_file' does not exist. Skipping."
        continue
    fi

    echo >&2 "Processing $sql_file"
    sql_file_dir=$(dirname $sql_file)

    if ! psql -X -h "localhost" -U "$DB_USERNAME" -p "$DB_PORT" -d "$DB_NAME" < "$sql_file" > /dev/null; then
        echo >&2 "Error: Could not restore the database."
        exit 1
    fi
done

exit 0
