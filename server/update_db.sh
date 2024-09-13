#!/bin/bash

# Set environment variables
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/home/deployer"

# Change to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment
source /home/deployer/vscode-live-themes/server/venv/bin/activate

# Run the Python script
python3 /home/deployer/vscode-live-themes/server/fetch_themes.py --log-level ERROR --page-size 50 --max-pages 20 all >> /home/deployer/vscode-live-themes/server/cron.log 2>&1

# Deactivate virtual environment
deactivate