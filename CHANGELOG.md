# Changelog

All notable changes to Email Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.3] - 2025-12-10

### Added
- **CI/CD Pipeline**: GitHub Actions workflow for automated testing
  - Hardcoding check on every push/PR
  - Clean install test with uv
- **Hardcoding Check Script**: `scripts/check_hardcoding.sh` for pre-deploy validation
- **uv Support**: Modern Python package management with lockfile

### Changed
- **Context-Based Priority System**: Removed all hardcoded rules
  - 5-axis judgment: sender relationship, request strength, urgency signals, mail type, recipient type
  - Claude analyzes email context holistically (tone, signature, content)
  - No more hardcoded names or roles
- **Portable Deployment**: Removed all user-specific paths
  - `/home/kyuwon/...` → dynamic detection
  - `~/.venv/bin/python` → `python` (uses activated venv)
  - Spreadsheet ID from config file (not hardcoded)
- **Cron Script**: Dynamic PATH expansion and claude command detection

### Fixed
- `email-send.md`: Now reads spreadsheet ID from config
- Column indices updated for 16-column schema (O=Draft ID)
- Sheet name references fixed (Emails → 신규 메일)

---

## [0.6.2] - 2025-12-XX

### Added
- **Auto Gmail Draft Creation**: `/email-analyze` automatically creates Gmail drafts
- **Draft ID Auto-Save**: Draft IDs saved to spreadsheet (column O)
- **16-Column Schema**: Extended Email Tracker format
  - Added: 답장여부 (N), Draft ID (O), Thread ID (P)
- **HTML Stripping**: Body preview shows plain text only

### Changed
- Workflow: Analyze → Label → Sheet → Auto Draft → Report

---

## [0.6.1] - 2025-12-XX

### Added
- **Recipient Type Priority Adjustment**
  - 📩 To (직접수신): Base priority
  - 📋 CC (참조): -1 priority
  - 👥 Group mail: -1 priority

---

## [0.6.0] - 2025-12-XX

### Added
- **Unified Spreadsheet**: Single spreadsheet with two tabs
  - 신규 메일: Today's analyzed emails (cleared each run)
  - 처리 이력: Cumulative history (updates existing)
- **Reply Status Check**: `check_if_replied()` via Gmail Thread API
- **Daily Automation**: Cron script for 8 AM auto-analysis
- **처리완료 Label**: Skip already-processed emails

### Changed
- Architecture: From daily spreadsheets to unified history

---

## [0.5.0] - 2025-12-XX

### Added

#### 3D Priority Scoring System
- **Claude Code Skill**: `prioritize-email` skill for sophisticated priority analysis
- **Sender Importance (0-100)**:
  - Relationship depth (0-50): Based on weighted exchanges `(sent × 3) + received`
  - Role/Position (0-30): Inferred from email content, signature, domain
  - Recent activity (0-20): Exchanges in last 7 days
- **Content Urgency (0-100)**:
  - Time sensitivity (0-40): Keywords like "today", "ASAP", "urgent"
  - Action required (0-35): Decision/task/question/info/FYI/none
  - Content importance (0-25): Business critical/project critical/important
- **Context Modifiers (-20 to +20)**:
  - Bonuses: First contact (+20), long thread (+15), multiple CC (+10)
  - Penalties: Receive-only (-10), automated (-15), old email (-20)
- **Final Calculation**: `(sender × 0.35) + (urgency × 0.50) + context`

#### Sender Management System
- **발신자 관리 Tab** in Google Sheets with 12 columns:
  - 발신자 (email), 이름, 자동점수, 수동등급, 확정점수
  - 총 교신, 보낸 횟수, 받은 횟수, P4-5 비율
  - 최근7일, 마지막 교신일, 메모
- **Auto-scoring algorithm**:
  - High priority ratio (40%): % of P4-5 emails from sender
  - Interaction frequency (30%): Weighted exchanges
  - Sent weight (20%): Ratio of sent vs received
  - Recency (10%): Last 7 days activity
- **Manual grade override**: VIP (100) / 중요 (80) / 보통 (50) / 낮음 (20) / 차단 (0)
- **Data validation**: Dropdown for manual grades
- **Conditional formatting**: Score-based color gradient (0-100)

#### Gmail Label Management
- **Auto-create 8 labels** with colors:
  - Status: 답장필요 (red), 답장불필요 (gray), 답장완료 (green)
  - Priority: P1-최저, P2-낮음, P3-보통, P4-긴급, P5-최우선
- **Auto-apply labels** based on classification
- **Auto-update labels** when emails are sent (답장필요 → 답장완료)
- **Gmail filtering support**: `label:답장필요 label:P5-최우선`

### Changed
- **Classifier**: Updated to use `prioritize-email` skill instead of hardcoded rules
- **Main workflow**: Integrated label management and sender scoring
- **Response format**: Added detailed scoring breakdown fields:
  - `sender_importance`, `content_urgency`, `context_modifiers`
  - `calculation`, `priority_label`, `summary`

### Technical Details
- New functions in `gmail_client.py`:
  - `collect_all_sender_stats()`: Analyze 200+ recent emails
  - `setup_email_labels()`: Create/verify 8 labels
  - `apply_labels_to_email()`: Apply status + priority labels
  - `remove_all_classification_labels()`: Remove all classification labels
- New functions in `sheets_client.py`:
  - `_initialize_sender_management_tab()`: Create 발신자 관리 tab
  - `add_or_update_sender()`: Add/update sender stats
  - `_calculate_sender_auto_score()`: Auto-scoring algorithm
  - `get_sender_importance_scores()`: Retrieve final scores
- New design documents:
  - `priority_scoring_design.md`: 3D scoring framework
  - `sender_management_design.md`: Sender management system
- Updated `TESTING.md` with v0.5.0 test scenarios

---

## [0.4.0] - 2025-01-XX

### Added

#### Hybrid Architecture (Gmail + Sheets)
- **Gmail HTML drafts**: Full formatting support (bold, colors, signatures)
- **Draft preservation**: User edits in Gmail are 100% preserved
- **Sheets workflow**: Dashboard for managing emails and batch sending
- **Draft links**: HYPERLINK formula in Sheets to open Gmail drafts
- **Batch sending**: Send multiple drafts from spreadsheet

### Changed
- **Main workflow reorganization**:
  - STEP 4: Generate drafts → Create Gmail HTML drafts (before Sheets)
  - STEP 5: Update Sheets with draft links
  - STEP 6: Batch send from Sheets (using draft IDs)
- **Draft creation**: `is_html=True` by default for rich formatting
- **Email schema**: Updated to 10 columns (A-J) with draft_id and thread_id

### Added Functions
- `gmail_client.py`:
  - `create_draft()`: Create HTML draft with `is_html` parameter
  - `send_draft(draft_id)`: Send existing draft by ID
  - `batch_send_drafts()`: Send multiple drafts preserving edits
- `sheets_client.py`:
  - `get_drafts_to_send()`: Get draft IDs marked for sending
  - `update_email_status()`: Update status and uncheck send box
  - Extended `add_email_row()` with `draft_id` and `draft_link`

### Deprecated
- `batch_send_emails()`: Replaced by `batch_send_drafts()`
  - Old method recreates emails from text (loses Gmail edits)
  - New method sends existing drafts (preserves all edits)

### Technical Details
- Hidden columns: I (Draft ID), J (Thread ID)
- Body preview: Limited to 200 chars in Sheets
- `valueInputOption="USER_ENTERED"`: Support HYPERLINK formulas
- Draft link format: `=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")`

---

## [0.3.0] - 2024-XX-XX

### Added
- Google Sheets integration
- Improved priority system with sender relationship weighting
- First contact detection (highest priority)
- Sent email weighting (2x importance)
- Sender-specific writing styles
- Conversation history context

### Changed
- Priority scoring algorithm to include relationship depth
- Writing style analysis to support per-sender customization

---

## [0.2.0] - 2024-XX-XX

### Added
- Writing style learning from sent emails
- Draft reply generation
- Batch classification

---

## [0.1.0] - 2024-XX-XX

### Added
- Initial release
- Gmail API integration
- Claude Code classification
- Basic priority scoring
- Response/no-response classification
