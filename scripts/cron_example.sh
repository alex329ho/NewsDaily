#!/bin/bash
# Example script for running dailynews from cron on macOS
set -e
VENV="/path/to/project/.venv"
LOG="/path/to/project/dailynews.log"
source "$VENV/bin/activate"
dailynews -t "finance,economy,politics" -h 8 -r US -l en >> "$LOG" 2>&1
