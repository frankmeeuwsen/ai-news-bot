#!/bin/bash
source /home/frank/apps/ai-news-bot/.env

# Stuur email bij failure
echo "AI News Bot failed at $(date). Check logs." | \
  mail -s "AI News Bot FAILED" -r "$GMAIL_ADDRESS" "$EMAIL_TO"

