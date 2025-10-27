#!/bin/bash

while true; do
    echo "=== $(date '+%Y-%m-%d %H:%M:%S') Running Docker restart cycle ==="

    # Stop containers (volumes are preserved)
    docker compose down

    # Rebuild and start containers
    docker compose up -d 

    echo "=== $(date '+%Y-%m-%d %H:%M:%S') Docker restarted successfully. Sleeping for 24 hours ==="
    sleep 24h
done
