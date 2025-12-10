#!/bin/bash
# Daily Email Analysis + Draft Creation Script
# Runs at 8:00 AM via cron
#
# Setup:
#   1. Make executable: chmod +x scripts/daily_email_analyze.sh
#   2. Add to crontab: crontab -e
#      0 8 * * * /path/to/email_agent/scripts/daily_email_analyze.sh

# Get script directory (works even when called via cron)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Create logs directory if not exists
mkdir -p logs

# Log file
LOG_FILE="logs/daily_analyze_$(date +%Y%m%d).log"

echo "=== Email Analysis Started: $(date) ===" >> "$LOG_FILE"
echo "Project: $PROJECT_DIR" >> "$LOG_FILE"

# Run Claude Code: Analyze emails AND create Gmail drafts
# --dangerously-skip-permissions: bypass permission prompts for cron execution
claude -p "이메일 분석하고 초안도 만들어줘" --dangerously-skip-permissions >> "$LOG_FILE" 2>&1

echo "=== Completed: $(date) ===" >> "$LOG_FILE"
