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
