#!/bin/bash

# AI News Bot - Database Sync Script
# Haalt dagelijks de nieuwste database op van de server

set -e

# Configuratie
PROJECT_DIR="/Users/frank/Projecten/ai-news-bot"
SERVER="dtd"
REMOTE_PATH="/home/frank/apps/ai-news-bot/data/newsbot.db"
LOCAL_PATH="$PROJECT_DIR/data/newsbot.db"
LOG_FILE="$PROJECT_DIR/logs/db-sync.log"

# Maak logs directory aan als deze niet bestaat
mkdir -p "$PROJECT_DIR/logs"

# Log functie
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Verstuur macOS notificatie
notify() {
    local title="$1"
    local message="$2"
    osascript -e "display notification \"$message\" with title \"$title\""
}

log "Starting database sync..."

# Backup van huidige database (optioneel)
if [ -f "$LOCAL_PATH" ]; then
    BACKUP_PATH="${LOCAL_PATH}.backup"
    cp "$LOCAL_PATH" "$BACKUP_PATH"
    log "Created backup at $BACKUP_PATH"
fi

# SCP database van server
if scp "$SERVER:$REMOTE_PATH" "$LOCAL_PATH" >> "$LOG_FILE" 2>&1; then
    log "Database sync successful!"
    notify "AI News Bot" "Database sync voltooid ✓"
    exit 0
else
    log "ERROR: Database sync failed!"
    notify "AI News Bot" "Database sync mislukt ✗"
    exit 1
fi
