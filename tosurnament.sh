#!/bin/bash

while true; do
    python3 main.py --noauth_local_webserver
    code=$?
    case $code in
        1)
            echo "Restarting Tosurnament after crash..."
        ;;
        42)
            echo "Updating Tosurnament..."
            git pull
        ;;
        43)
            echo "Restarting Tosurnament..."
        ;;
        *)
            echo "Exiting Tosurnament..."
            break
        ;;
    esac
done
