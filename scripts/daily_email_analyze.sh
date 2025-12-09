#!/bin/bash
# Daily Email Analysis + Draft Creation Script
# Runs at 8:00 AM via cron

cd /home/kyuwon/projects/email_agent

# Log file
LOG_FILE="/home/kyuwon/projects/email_agent/logs/daily_analyze_$(date +%Y%m%d).log"

echo "=== Email Analysis Started: $(date) ===" >> "$LOG_FILE"

# Run Claude Code: Analyze emails AND create Gmail drafts
# --dangerously-skip-permissions: bypass permission prompts for cron execution
/home/kyuwon/.npm-global/bin/claude -p "이메일 분석하고 초안도 만들어줘" --dangerously-skip-permissions >> "$LOG_FILE" 2>&1

echo "=== Completed: $(date) ===" >> "$LOG_FILE"
