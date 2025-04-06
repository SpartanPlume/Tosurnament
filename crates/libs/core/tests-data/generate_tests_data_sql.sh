#! /bin/bash

basedir=$(dirname "$0")
cd $basedir

sql_file="10000_fill_tests_data.up.sql"
rm -f "$sql_file"
touch "$sql_file"

csv_files=`find . -type f -regex ".*\.csv$"`
for csv_file in ${csv_files[@]}; do
    table_fields=`head -n 1 "$csv_file" | cut -c3-`
    table_name=`basename "$csv_file" .csv`
    echo "COPY $table_name (${table_fields[@]}) FROM PROGRAM 'egrep -v \"^-- \" \"/tests-data/$table_name.csv\"' WITH (FORMAT CSV);" >> "$sql_file"
done

exit 0
