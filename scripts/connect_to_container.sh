#!/bin/sh

helpFunction() {
    echo "No container name given or invalid container name."
    echo "Available containers:"
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
