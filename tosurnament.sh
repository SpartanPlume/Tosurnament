#! /bin/bash

basedir=$(dirname "$0")
cd $basedir

helpFunction() {
    echo "Invalid or no phase selected. Please provide LOCAL, DEV, TST or PRD as argument."
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
    cargo build
    if [ $? -ne 0 ]; then
        exit 1
    fi

    echo "Create local database"
    ./scripts/init_db.sh

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
    # Delete local database
    docker stop tosurnament-local-db > /dev/null
    docker rm tosurnament-local-db > /dev/null
elif [ "$phase" = "DEV" ]; then
    docker compose -f docker/compose.yml -f docker/development.yml $@
elif [ "$phase" = "TST" ]; then
    docker compose -f docker/compose.yml -f docker/testing.yml $@
elif [ "$phase" = "PRD" ]; then
    docker compose -f docker/compose.yml -f docker/production.yml $@
else
    helpFunction
fi
