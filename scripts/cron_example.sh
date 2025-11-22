#!/bin/bash
# Example script for running dailynews from cron on macOS
# Ensure the virtual environment was created with Python 3.10+
set -e
VENV="/path/to/project/.venv"
LOG="/path/to/project/dailynews.log"
source "$VENV/bin/activate"
dailynews -t "finance,economy,politics" -h 8 -r US -l en >> "$LOG" 2>&1