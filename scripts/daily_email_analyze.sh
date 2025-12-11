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

# Expand PATH for cron (add common npm global paths)
export PATH="$PATH:/usr/local/bin:/usr/bin:$HOME/.npm-global/bin:$HOME/.local/bin"

# Find claude command
CLAUDE_CMD=$(command -v claude 2>/dev/null)
if [ -z "$CLAUDE_CMD" ]; then
    echo "ERROR: claude command not found in PATH" >&2
    echo "Install: npm install -g @anthropic-ai/claude-code" >&2
    exit 1
fi

# Create logs directory if not exists
mkdir -p logs

# Log file
LOG_FILE="logs/daily_analyze_$(date +%Y%m%d).log"

echo "=== Email Analysis Started: $(date) ===" >> "$LOG_FILE"
echo "Project: $PROJECT_DIR" >> "$LOG_FILE"
echo "Claude: $CLAUDE_CMD" >> "$LOG_FILE"

# Run Claude Code: Execute /email-analyze slash command
# This runs the full workflow: Gmail → Sheets → Labels → Drafts → Summary Report
# --dangerously-skip-permissions: bypass permission prompts for cron execution
"$CLAUDE_CMD" -p "/email-analyze 슬래시 명령어 실행해줘" --dangerously-skip-permissions >> "$LOG_FILE" 2>&1

echo "=== Completed: $(date) ===" >> "$LOG_FILE"
