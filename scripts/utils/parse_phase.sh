#! /bin/bash

if [ $# -ne 1 ]; then
    echo >&2 "This script should not be called directly."
    exit 1
fi

contains() {
    [[ ${1,,} =~ (^|[[:space:]])${2,,}($|[[:space:]]) ]] && return 0 || return 1
}

if contains "l loc local" "$1"; then
    echo "local"
elif contains "d dev develop development" "$1"; then
    echo "development"
elif contains "t tst test testing" "$1"; then
    echo "testing"
elif contains "p prd prod production" "$1"; then
    echo "production"
else
    exit 1
fi

exit 0
