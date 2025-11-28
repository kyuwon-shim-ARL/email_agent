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

        # Initialize headers
        headers = [
            "상태",  # 답장필요/불필요/완료
            "우선순위",
            "제목",
            "발신자",
            "수신(To)",
            "수신(CC)",
            "받은시간",
            "메일내용",
            "답장초안",
            "답장수신자",
            "답장CC",
            "발송여부",
            "Thread ID",
        ]

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Emails!A1:M1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

        # Format headers
        requests = [
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
            }
        ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

        return spreadsheet_id

    def add_email_row(
        self,
        spreadsheet_id: str,
        email_data: dict[str, Any],
    ) -> None:
        """
        Add email to spreadsheet.

        Args:
            spreadsheet_id: Target spreadsheet ID
            email_data: Email information dict
        """
        # 상태 매핑
        status_map = {
            "needs_response": "답장필요",
            "no_response": "답장불필요",
            "sent": "답장완료",
        }

        status = status_map.get(email_data.get("status", "needs_response"), "답장필요")

        row = [
            status,
            email_data.get("priority", 3),
            email_data.get("subject", ""),
            email_data.get("sender", ""),
            email_data.get("to", ""),
            email_data.get("cc", ""),
            email_data.get("date", ""),
            email_data.get("body", "")[:500],  # 500자 제한
            email_data.get("draft_body", ""),
            email_data.get("draft_to", ""),
            email_data.get("draft_cc", ""),
            "",  # 발송여부 (체크박스)
            email_data.get("thread_id", ""),
        ]

        self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="Emails!A:M",
            valueInputOption="RAW",
            body={"values": [row]},
        ).execute()

    def get_emails_to_send(self, spreadsheet_id: str) -> list[dict[str, Any]]:
        """
        Get emails marked for sending (발송여부 = TRUE).

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            List of emails to send
        """
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range="Emails!A2:M")
            .execute()
        )

        rows = result.get("values", [])
        emails_to_send = []

        for i, row in enumerate(rows, start=2):
            if len(row) < 12:
                continue

            # 발송여부 체크 (12번째 컬럼, 인덱스 11)
            send_flag = row[11] if len(row) > 11 else ""

            if send_flag.upper() in ["TRUE", "YES", "Y", "X", "✓"]:
                emails_to_send.append(
                    {
                        "row_number": i,
                        "status": row[0],
                        "priority": row[1],
                        "subject": row[2],
                        "sender": row[3],
                        "draft_body": row[8] if len(row) > 8 else "",
                        "draft_to": row[9] if len(row) > 9 else "",
                        "draft_cc": row[10] if len(row) > 10 else "",
                        "thread_id": row[12] if len(row) > 12 else "",
                    }
                )

        return emails_to_send

    def update_email_status(
        self, spreadsheet_id: str, row_number: int, status: str = "답장완료"
    ) -> None:
        """
        Update email status after sending.

        Args:
            spreadsheet_id: Spreadsheet ID
            row_number: Row number (1-indexed)
            status: New status
        """
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Emails!A{row_number}",
            valueInputOption="RAW",
            body={"values": [[status]]},
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
