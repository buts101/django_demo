#!/bin/bash

# Navigate to the repository directory
cd "$(dirname "$0")"

# Pull the latest changes
git pull

# Log the pull with timestamp
echo "Git pull executed at $(date)" >> git_pull_log.txt
