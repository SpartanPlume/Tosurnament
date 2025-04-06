#! /bin/bash

set -eo pipefail

basedir=$(dirname "$0")
cd $basedir/..

# Check if docker is installed and running
./scripts/utils/check_docker.sh

export $(grep -v '^#' docker/test/local.env | xargs)

container_name="tosurnament-local-irc"
if [ "$(docker ps -a -q -f name=$container_name)" ]; then
    if [ "$(docker ps -aq -f status=running -f name=$container_name)" ]; then
        docker stop $container_name > /dev/null
    fi
    docker rm $container_name > /dev/null
fi
docker build -t tosurnament-local-irc -f docker/test/test-irc.Dockerfile $(dirname "$0")/.. 2> /dev/null
docker run \
    --name $container_name \
    -p "$IRC_PORT":"$IRC_PORT" \
    -d \
    tosurnament-local-irc > /dev/null

echo >&2 "IRC is up and running on port $IRC_PORT!"
