#! /bin/bash

set -eo pipefail

basedir=$(dirname "$0")
cd $basedir/..

# Check if docker is installed and running
./scripts/utils/check_docker.sh

helpFunction() {
    echo >&2 "No container name given or invalid container name."
    echo >&2 "Available containers:"
    docker ps --format '{{.Names}}'
    exit 1
}

if [ $# -lt 1 ]; then
    helpFunction
fi

container=`docker ps -aqf "name=$1"`

if [ -z "$container" ]; then
    helpFunction
fi

docker exec -it $container /bin/bash
