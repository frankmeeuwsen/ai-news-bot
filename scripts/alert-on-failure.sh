#!/bin/bash
source /home/frank/.env-newsbot

# Stuur email bij failure
echo "AI News Bot failed at $(date). Check logs." | \
  mail -s "🚨 AI News Bot FAILED" -r "$GMAIL_ADDRESS" "$EMAIL_TO"

