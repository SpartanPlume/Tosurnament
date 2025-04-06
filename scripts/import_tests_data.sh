#! /bin/bash

basedir=$(dirname "$0")
cd $basedir/..

sql_files=(`find crates/libs/core/migrations -type f -regex ".*\.up\.sql$" | sort -n`)
if [ -z "$sql_files" ]; then
    echo >&2 "Error: Could not find any sql files to process."
    exit 1
fi

csv_files=`find crates/libs/core/tests-data -type f -regex ".*\.csv$"`
if [ -z "$csv_files" ]; then
    echo >&2 "Error: Could not find any tests data csv files."
    exit 1
fi
tmp_file=`mktemp --suffix .sql`
for csv_file in ${csv_files[@]}; do
    table_fields=`head -n 1 "$csv_file" | cut -c3-`
    table_name=`basename "$csv_file" .csv`
    echo "\\copy $table_name (${table_fields[@]}) FROM PROGRAM 'egrep -v \"^-- \" \"$csv_file\"' WITH (FORMAT CSV)" >> "$tmp_file"
done

sql_files+=("$tmp_file")

./scripts/restore_db.sh ${sql_files[@]}

rm $tmp_file
exit 0
