#! /bin/bash

set -eo pipefail

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

IRC_PORT=6667

container_name="tosurnament-local-irc"
if [ "$(docker ps -a -q -f name=$container_name)" ]; then
    if [ "$(docker ps -aq -f status=running -f name=$container_name)" ]; then
        docker stop $container_name > /dev/null
    fi
    docker rm $container_name > /dev/null
fi
docker build -t tosurnament-irc -f docker/test-irc.Dockerfile $(dirname "$0")/.. 2> /dev/null
docker run \
    --name $container_name \
    -p "${IRC_PORT}":"${IRC_PORT}" \
    -d \
    tosurnament-irc > /dev/null

echo >&2 "IRC is up and running on port ${IRC_PORT}!"
