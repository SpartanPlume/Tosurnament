#!/bin/sh

helpFunction() {
    echo "Invalid or no phase selected. Please provider DEV, TST or PRD as argument."
    exit 1
}

if [ $# -lt 1 ]; then
    helpFunction
fi

if [ $# -eq 1 ] && [ "$1" = "build" ]; then
    docker compose -f docker/compose.yml build
    exit 0
fi

if [ "$1" = "DEV" ]; then
    shift 1
    docker compose -f docker/compose.yml -f docker/development.yml $@
elif [ "$1" = "TST" ]; then
    shift 1
    docker compose -f docker/compose.yml -f docker/testing.yml $@
elif [ "$1" = "PRD" ]; then
    shift 1
    docker compose -f docker/compose.yml -f docker/production.yml $@
else
    helpFunction
fi
