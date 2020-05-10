#!/bin/bash

cd backend
while true; do
    python3 start_bot.py
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
