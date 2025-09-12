#!/bin/bash
# Example script for running dailynews from cron on macOS
set -e
VENV="/path/to/project/.venv"
LOG="/path/to/project/dailynews.log"
source "$VENV/bin/activate"
dailynews "$@" >> "$LOG" 2>&1
