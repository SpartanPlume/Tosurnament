#! /bin/bash

set -eo pipefail

basedir=$(dirname "$0")
cd $basedir

# Check if docker is installed and running
./check_docker.sh

echo >&2 "No phase provided. Trying to automatically determine the phase instead."

containers=`docker ps --format '{{.Names}}'`
phases=()
for container in ${containers[@]}; do
    if [[ "$container" =~ tosurnament-([^-]+)-db ]]; then
        phases+=(${BASH_REMATCH[1]})
    fi
    if [[ "$container" =~ tosurnament-db ]]; then
        phases+=("production")
    fi
done

if [ ${#phases[@]} -eq 0 ]; then
    echo >&2 "Error: Could not find any phase. Did you start tosurnament?"
    exit 1
elif [ ${#phases[@]} -gt 1 ]; then
    echo >&2 "Error: Multiple instances of tosurnament found."
    exit 1
fi

phase="${phases[0]}"
echo >&2 "Phase found: $phase"

echo "$phase"

exit 0
