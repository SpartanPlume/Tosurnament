#! /bin/bash

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

exit 0
