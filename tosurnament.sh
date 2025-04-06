#! /bin/bash

basedir=$(dirname "$0")
cd $basedir

# Check if docker is installed and running
./scripts/utils/check_docker.sh

helpFunction() {
    echo >&2 "Invalid or no phase selected. Please provide LOCAL, DEV, TST or PRD as argument."
    echo >&2 "For test, provide --test instead."
    echo >&2 "For coverage, provide --coverage instead."
    exit 1
}

if [ $# -lt 1 ]; then
    helpFunction
fi

if [ $# -eq 1 ] && [ "$1" = "build" ]; then
    docker compose -f docker/compose.yml build
    exit 0
fi

if [ "$1" = "--test" ] || [ "$1" = "--coverage" ]; then
    additional_compose=""
    if [ "$1" = "--coverage" ]; then
        additional_compose="-f docker/test/coverage-compose.yml"
    fi
    env $(grep -v '^#' docker/test/local.env | xargs) docker compose -f docker/test/test-compose.yml $additional_compose down
    env $(grep -v '^#' docker/test/local.env | xargs) docker compose -f docker/test/test-compose.yml $additional_compose up --build --exit-code-from test
    docker images --quiet --filter=dangling=true | xargs --no-run-if-empty docker rmi > /dev/null
    docker volume ls --quiet --filter=dangling=true | xargs --no-run-if-empty docker volume rm > /dev/null
    exit 0
fi

phase=`./scripts/utils/parse_phase.sh $1`
if [ $? -ne 0 ]; then
    helpFunction
fi

shift 1
if [ "$phase" = "local" ]; then
    # Setup SIGTERM handling
    unset term_child_pid
    unset term_kill_needed

    handle_term()
    {
        if [ "$term_child_pid" ]; then
            kill -TERM "$term_child_pid" 2> /dev/null
        else
            term_kill_needed="yes"
        fi
    }
 
    wait_term()
    {
        term_child_pid=$!
        if [ "$term_kill_needed" ]; then
            kill -TERM "$term_child_pid" 2> /dev/null 
        fi
        wait $term_child_pid 2> /dev/null
        trap - TERM INT
        wait $term_child_pid 2> /dev/null
    }

    echo "Build all crates"
    if ! cargo build; then exit 1; fi

    echo "Create local database"
    if ! ./scripts/init_db.sh; then exit 1; fi

    echo "Create local IRC"
    if ! ./scripts/init_irc.sh; then exit 1; fi

    ./scripts/import_tests_data.sh "$phase"

    echo "Run binaries (Use CTRL+C to stop the program)"
    # Start handling SIGTERM
    trap 'handle_term' TERM INT

    cargo run --bin tosurnament-web &
    tosurnament_web_pid=$!
    cargo run --bin tosurnament-api &

    # Wait for SIGTERM
    wait_term
    # Kill other processes
    kill $tosurnament_web_pid
    # Delete local IRC
    docker stop tosurnament-local-irc > /dev/null
    docker rm tosurnament-local-irc > /dev/null
    # Delete local database
    docker stop tosurnament-local-db > /dev/null
    docker rm tosurnament-local-db > /dev/null
else
    env $(grep -v '^#' docker/$phase.env | xargs) docker compose -f docker/compose.yml -f docker/$phase.yml $@
fi
