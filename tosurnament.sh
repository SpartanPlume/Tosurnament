#!/bin/bash

while true; do
    python3 main.py
    code=$?
    case $code in
        0)
            echo "Stopping Tosurnament..."
            break
        1)
            echo "RRestarting Tosurnament after crash..."
        42)
            echo "Updating Tosurnament..."
            git pull
        43)
            echo "Restarting Tosurnament..."
    esac
done