#! /bin/bash

basedir=$(dirname "$0")
cd $basedir

helpFunction() {
    echo "Invalid or no phase selected. Please provide LOCAL, DEV, TST or PRD as argument."
    echo "For test, provide --test instead."
    exit 1
}

if [ $# -lt 1 ]; then
    helpFunction
fi

if [ $# -eq 1 ] && [ "$1" = "build" ]; then
    docker compose -f docker/compose.yml build
    exit 0
fi

phase="$1"
shift 1
if [ "$phase" = "LOCAL" ]; then
    # Setup SIGTERM handling
    unset term_child_pid
    unset term_kill_needed

    handle_term()
    {
        if [ "${term_child_pid}" ]; then
            kill -TERM "${term_child_pid}" 2> /dev/null
        else
            term_kill_needed="yes"
        fi
    }
 
    wait_term()
    {
        term_child_pid=$!
        if [ "${term_kill_needed}" ]; then
            kill -TERM "${term_child_pid}" 2> /dev/null 
        fi
        wait ${term_child_pid} 2> /dev/null
        trap - TERM INT
        wait ${term_child_pid} 2> /dev/null
    }

    echo "Build all crates"
    if ! cargo build; then exit 1; fi

    echo "Create local database"
    if ! ./scripts/init_db.sh; then exit 1; fi

    echo "Create local IRC"
    if ! ./scripts/init_irc.sh; then exit 1; fi

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
elif [ "$phase" = "DEV" ]; then
    docker compose -f docker/compose.yml -f docker/development.yml $@
elif [ "$phase" = "TST" ]; then
    docker compose -f docker/compose.yml -f docker/testing.yml $@
elif [ "$phase" = "PRD" ]; then
    docker compose -f docker/compose.yml -f docker/production.yml $@
elif [ "$phase" = "--test" ]; then
    docker compose -f docker/test-compose.yml down
    docker compose -f docker/test-compose.yml up --build --exit-code-from test
    docker images --quiet --filter=dangling=true | xargs --no-run-if-empty docker rmi > /dev/null
    docker volume ls --quiet --filter=dangling=true | xargs --no-run-if-empty docker volume rm > /dev/null
else
    helpFunction
fi
