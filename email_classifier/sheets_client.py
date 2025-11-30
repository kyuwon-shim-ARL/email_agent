"""Google Sheets API client for email tracking."""
import os.path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API 스코프에 Sheets 추가
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",  # 일괄 발송용
    "https://www.googleapis.com/auth/spreadsheets",  # Sheets 읽기/쓰기
]


class SheetsClient:
    """Google Sheets API client for email management."""

    def __init__(self) -> None:
        """Initialize Sheets client with OAuth."""
        self.creds = self._get_credentials()
        self.service = build("sheets", "v4", credentials=self.creds)

    def _get_credentials(self) -> Credentials:
        """Get or create OAuth credentials with Sheets scope."""
        creds = None

        # Load existing token
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists("credentials.json"):
                    raise FileNotFoundError(
                        "credentials.json not found. "
                        "Download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token for next time
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return creds

    def create_email_tracker(self, title: str = "Email Tracker") -> str:
        """
        Create a new spreadsheet for email tracking.

        Args:
            title: Spreadsheet title

        Returns:
            Spreadsheet ID
        """
        spreadsheet = {
            "properties": {"title": title},
            "sheets": [
                {
                    "properties": {
                        "title": "Emails",
                        "gridProperties": {"frozenRowCount": 1},
                    }
                },
                {
                    "properties": {
                        "title": "발신자 관리",
                        "gridProperties": {"frozenRowCount": 1},
                    }
                }
            ],
        }

        spreadsheet = (
            self.service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )

        spreadsheet_id = spreadsheet.get("spreadsheetId")

        # Initialize headers (v0.4.0 schema)
        headers = [
            "상태",              # A: 답장필요/불필요/완료
            "우선순위",          # B: 1-5
            "제목",              # C: Email subject
            "발신자",            # D: Sender
            "받은시간",          # E: Received date
            "내용미리보기",      # F: Body preview (200 chars)
            "Gmail 초안",        # G: Hyperlink to draft
            "발송여부",          # H: Checkbox
            "Draft ID",          # I: Hidden (for API)
            "Thread ID",         # J: Hidden (for threading)
        ]

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Emails!A1:J1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

        # Format headers and columns
        requests = [
            # Header row formatting (dark background, white text, bold)
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                            "textFormat": {
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                "bold": True,
                            },
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            # Hide columns I and J (Draft ID, Thread ID)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 8,  # Column I (Draft ID)
                        "endIndex": 10,   # Through Column J (Thread ID)
                    },
                    "properties": {"hiddenByUser": True},
                    "fields": "hiddenByUser",
                }
            },
            # Set column G width (Gmail 초안 link)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 6,
                        "endIndex": 7,
                    },
                    "properties": {"pixelSize": 120},
                    "fields": "pixelSize",
                }
            },
            # Set column F width (preview)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 5,
                        "endIndex": 6,
                    },
                    "properties": {"pixelSize": 300},
                    "fields": "pixelSize",
                }
            },
        ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

        # Initialize 발신자 관리 tab
        self._initialize_sender_management_tab(spreadsheet_id)

        return spreadsheet_id

    def add_email_row(
        self,
        spreadsheet_id: str,
        email_data: dict[str, Any],
        draft_id: str = "",      # NEW parameter
        draft_link: str = "",    # NEW parameter
    ) -> None:
        """
        Add email to spreadsheet with draft link.

        Args:
            spreadsheet_id: Target spreadsheet ID
            email_data: Email metadata (subject, sender, body, etc.)
            draft_id: Gmail draft ID (e.g., 'r1234567890abcdef')
            draft_link: HYPERLINK formula for Gmail draft
        """
        # 상태 매핑
        status_map = {
            "needs_response": "답장필요",
            "no_response": "답장불필요",
            "sent": "답장완료",
        }

        status = status_map.get(email_data.get("status", "needs_response"), "답장필요")

        row = [
            status,                                          # A
            email_data.get("priority", 3),                   # B
            email_data.get("subject", ""),                   # C
            email_data.get("sender", ""),                    # D
            email_data.get("date", ""),                      # E
            email_data.get("body", "")[:200],                # F: Preview only (shortened from 500)
            draft_link,                                      # G: Clickable link
            False,                                           # H: Checkbox unchecked
            draft_id,                                        # I: Hidden
            email_data.get("thread_id", ""),                 # J: Hidden
        ]

        self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="Emails!A:J",                              # Updated range
            valueInputOption="USER_ENTERED",                 # Changed to support HYPERLINK formula
            body={"values": [row]},
        ).execute()

    def get_drafts_to_send(self, spreadsheet_id: str) -> list[dict[str, Any]]:
        """
        Get draft IDs for emails marked for sending.

        Returns only rows where:
        - Column H (발송여부) is checked (TRUE)
        - Column I (Draft ID) is not empty

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            List of dicts with draft_id, subject, sender, row_number

        Example:
            [
                {
                    'draft_id': 'r1234567890abcdef',
                    'subject': 'Re: Meeting request',
                    'sender': 'boss@example.com',
                    'row_number': 2
                }
            ]
        """
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range="Emails!A2:J")  # Updated range
            .execute()
        )

        rows = result.get("values", [])
        drafts_to_send = []

        for i, row in enumerate(rows, start=2):  # Row 2 = first data row
            # Ensure row has enough columns
            if len(row) < 9:
                continue

            send_checkbox = row[7] if len(row) > 7 else ""  # Column H
            draft_id = row[8] if len(row) > 8 else ""       # Column I

            # Check if marked for sending
            if send_checkbox in ["TRUE", "True", True, "true"] and draft_id:
                drafts_to_send.append({
                    "draft_id": draft_id,
                    "subject": row[2] if len(row) > 2 else "",
                    "sender": row[3] if len(row) > 3 else "",
                    "row_number": i,
                })

        return drafts_to_send

    # Keep old function for backward compatibility
    def get_emails_to_send(self, spreadsheet_id: str) -> list[dict[str, Any]]:
        """
        DEPRECATED: Use get_drafts_to_send() instead.

        This function is kept for backward compatibility with v0.3.0.
        """
        import warnings
        warnings.warn(
            "get_emails_to_send() is deprecated. Use get_drafts_to_send() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Return empty list for deprecated function
        return []

    def update_email_status(
        self,
        spreadsheet_id: str,
        row_number: int,
        new_status: str = "답장완료",
        uncheck_send_box: bool = True  # NEW parameter
    ) -> None:
        """
        Update email status after sending.

        Args:
            spreadsheet_id: Spreadsheet ID
            row_number: Row number to update (2 = first data row)
            new_status: New status (e.g., '답장완료')
            uncheck_send_box: If True, uncheck '발송여부' checkbox
        """
        # Update status (column A)
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Emails!A{row_number}",
            valueInputOption="RAW",
            body={"values": [[new_status]]},
        ).execute()

        # Uncheck send box (column H)
        if uncheck_send_box:
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"Emails!H{row_number}",
                valueInputOption="RAW",
                body={"values": [[False]]},
            ).execute()

    def batch_update_emails(
        self, spreadsheet_id: str, emails: list[dict[str, Any]]
    ) -> None:
        """
        Batch update multiple emails.

        Args:
            spreadsheet_id: Spreadsheet ID
            emails: List of email data dicts
        """
        data = []
        for email in emails:
            status_map = {
                "needs_response": "답장필요",
                "no_response": "답장불필요",
                "sent": "답장완료",
            }
            status = status_map.get(email.get("status", "needs_response"), "답장필요")

            row = [
                status,
                email.get("priority", 3),
                email.get("subject", ""),
                email.get("sender", ""),
                email.get("to", ""),
                email.get("cc", ""),
                email.get("date", ""),
                email.get("body", "")[:500],
                email.get("draft_body", ""),
                email.get("draft_to", ""),
                email.get("draft_cc", ""),
                "",
                email.get("thread_id", ""),
            ]

            data.append({"range": "Emails!A:M", "values": [row]})

        body = {"valueInputOption": "RAW", "data": data}

        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()

    def _initialize_sender_management_tab(self, spreadsheet_id: str) -> None:
        """
        Initialize the 발신자 관리 tab with headers and formatting.

        Internal helper called by create_email_tracker().
        """
        # Get sheet ID for 발신자 관리 tab
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        sender_sheet_id = None
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == '발신자 관리':
                sender_sheet_id = sheet['properties']['sheetId']
                break

        if sender_sheet_id is None:
            return  # Tab doesn't exist, skip

        # Set up headers
        headers = [
            "발신자",           # A: Sender email
            "이름",             # B: Name (auto-extracted or manual)
            "자동점수",         # C: Auto score (0-100)
            "수동등급",         # D: Manual grade (dropdown)
            "확정점수",         # E: Final score (0-100)
            "총 교신",          # F: Total exchanges
            "보낸 횟수",        # G: Sent count
            "받은 횟수",        # H: Received count
            "P4-5 비율",       # I: High priority ratio (%)
            "최근7일",          # J: Recent 7 days
            "마지막 교신일",    # K: Last contact date
            "메모",             # L: User notes
        ]

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="발신자 관리!A1:L1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

        # Format headers and add data validation
        requests = [
            # Header row formatting
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sender_sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                            "textFormat": {
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                "bold": True,
                            },
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            # Data validation for 수동등급 (column D)
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sender_sheet_id,
                        "startRowIndex": 1,  # Start from row 2 (first data row)
                        "startColumnIndex": 3,  # Column D
                        "endColumnIndex": 4,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": "VIP"},
                                {"userEnteredValue": "중요"},
                                {"userEnteredValue": "보통"},
                                {"userEnteredValue": "낮음"},
                                {"userEnteredValue": "차단"},
                            ]
                        },
                        "showCustomUi": True,
                        "strict": True,
                    }
                }
            },
            # Conditional formatting for 확정점수 (column E)
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sender_sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": 4,
                            "endColumnIndex": 5,
                        }],
                        "gradientRule": {
                            "minpoint": {
                                "color": {"red": 0.9, "green": 0.9, "blue": 0.9},
                                "type": "NUMBER",
                                "value": "0",
                            },
                            "midpoint": {
                                "color": {"red": 1, "green": 0.9, "blue": 0.4},
                                "type": "NUMBER",
                                "value": "50",
                            },
                            "maxpoint": {
                                "color": {"red": 0.2, "green": 0.7, "blue": 0.3},
                                "type": "NUMBER",
                                "value": "100",
                            },
                        }
                    },
                    "index": 0,
                }
            },
            # Set column widths
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sender_sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 1,
                    },
                    "properties": {"pixelSize": 200},  # 발신자
                    "fields": "pixelSize",
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sender_sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 11,
                        "endIndex": 12,
                    },
                    "properties": {"pixelSize": 300},  # 메모
                    "fields": "pixelSize",
                }
            },
        ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

    def add_or_update_sender(
        self,
        spreadsheet_id: str,
        sender_email: str,
        sender_stats: dict[str, Any],
    ) -> None:
        """
        Add or update a sender in the 발신자 관리 tab.

        Args:
            spreadsheet_id: Spreadsheet ID
            sender_email: Sender email address
            sender_stats: Stats dict with keys:
                - name: Sender name (optional)
                - total_sent: Sent count
                - total_received: Received count
                - p45_count: Count of P4-5 emails
                - total_emails: Total emails from sender
                - recent_7days: Recent activity count
                - last_contact_date: Last contact date string
        """
        # Calculate auto score
        auto_score = self._calculate_sender_auto_score(sender_stats)

        # Check if sender already exists
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="발신자 관리!A2:L",
        ).execute()

        rows = result.get("values", [])
        sender_row = None
        row_index = None

        for i, row in enumerate(rows, start=2):
            if row and row[0] == sender_email:
                sender_row = row
                row_index = i
                break

        # Prepare row data
        name = sender_stats.get("name", "")
        manual_grade = sender_row[3] if (sender_row and len(sender_row) > 3) else ""
        final_score = self._get_final_score(auto_score, manual_grade)

        p45_ratio = (
            round(sender_stats["p45_count"] / sender_stats["total_emails"] * 100, 1)
            if sender_stats.get("total_emails", 0) > 0 else 0
        )

        memo = sender_row[11] if (sender_row and len(sender_row) > 11) else ""

        new_row = [
            sender_email,                             # A
            name,                                      # B
            auto_score,                                # C
            manual_grade,                              # D
            final_score,                               # E
            sender_stats.get("total_sent", 0) + sender_stats.get("total_received", 0),  # F
            sender_stats.get("total_sent", 0),         # G
            sender_stats.get("total_received", 0),     # H
            f"{p45_ratio}%",                           # I
            sender_stats.get("recent_7days", 0),       # J
            sender_stats.get("last_contact_date", ""), # K
            memo,                                      # L
        ]

        if row_index:
            # Update existing row
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"발신자 관리!A{row_index}:L{row_index}",
                valueInputOption="USER_ENTERED",
                body={"values": [new_row]},
            ).execute()
        else:
            # Append new row
            self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="발신자 관리!A:L",
                valueInputOption="USER_ENTERED",
                body={"values": [new_row]},
            ).execute()

    def _calculate_sender_auto_score(self, stats: dict[str, Any]) -> int:
        """
        Calculate automatic sender importance score (0-100).

        Algorithm:
        - High priority ratio (40%): % of P4-5 emails
        - Interaction frequency (30%): weighted_exchanges = (sent × 2) + received
        - Sent weight (20%): ratio of sent vs received
        - Recency (10%): last 7 days activity

        Args:
            stats: Sender statistics

        Returns:
            Score from 0-100
        """
        score = 0.0

        # 1. High priority ratio (40 points max)
        total_emails = stats.get("total_emails", 0)
        p45_count = stats.get("p45_count", 0)
        if total_emails > 0:
            p45_ratio = p45_count / total_emails
            score += p45_ratio * 40

        # 2. Interaction frequency (30 points max)
        sent = stats.get("total_sent", 0)
        received = stats.get("total_received", 0)
        weighted_exchanges = (sent * 2) + received

        if weighted_exchanges >= 100:
            score += 30
        elif weighted_exchanges >= 50:
            score += 25
        elif weighted_exchanges >= 20:
            score += 20
        elif weighted_exchanges >= 10:
            score += 15
        elif weighted_exchanges >= 5:
            score += 10
        else:
            score += 5

        # 3. Sent weight (20 points max)
        total_exchanges = sent + received
        if total_exchanges > 0:
            sent_ratio = sent / total_exchanges
            score += sent_ratio * 20

        # 4. Recency (10 points max)
        recent_7days = stats.get("recent_7days", 0)
        if recent_7days >= 10:
            score += 10
        elif recent_7days >= 5:
            score += 8
        elif recent_7days >= 3:
            score += 6
        elif recent_7days >= 1:
            score += 3

        return min(100, int(round(score)))

    def _get_final_score(self, auto_score: int, manual_grade: str) -> int:
        """
        Get final sender importance score.

        If manual_grade is set, use it. Otherwise use auto_score.

        Args:
            auto_score: Automatic score (0-100)
            manual_grade: Manual grade (VIP/중요/보통/낮음/차단)

        Returns:
            Final score (0-100)
        """
        grade_scores = {
            "VIP": 100,
            "중요": 80,
            "보통": 50,
            "낮음": 20,
            "차단": 0,
        }

        if manual_grade in grade_scores:
            return grade_scores[manual_grade]
        else:
            return auto_score

    def get_sender_importance_scores(self, spreadsheet_id: str) -> dict[str, int]:
        """
        Get sender importance scores from 발신자 관리 tab.

        Returns:
            Dict mapping sender email to final score (0-100)

        Example:
            {
                'ceo@company.com': 100,
                'teammate@company.com': 65,
                'spam@example.com': 0,
            }
        """
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="발신자 관리!A2:E",
        ).execute()

        rows = result.get("values", [])
        scores = {}

        for row in rows:
            if len(row) >= 5:
                sender_email = row[0]
                final_score = row[4]

                # Convert to int
                try:
                    scores[sender_email] = int(final_score)
                except (ValueError, TypeError):
                    scores[sender_email] = 0

        return scores
