"""Google Sheets API client for email tracking."""
import os.path
import re
from typing import List, Dict, Optional, Tuple, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def strip_html(text: str) -> str:
    """HTML 태그 및 스타일/스크립트 제거하고 텍스트만 추출."""
    if not text:
        return ""

    # 1. script, style 태그와 내용 전체 제거 (닫는 태그 없어도 처리)
    clean = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<script[^>]*>.*', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*', '', clean, flags=re.DOTALL | re.IGNORECASE)

    # 2. HTML 주석 제거
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)

    # 3. 모든 HTML 태그 제거
    clean = re.sub(r'<[^>]+>', ' ', clean)

    # 4. CSS 패턴 제거 (태그 없이 남은 CSS)
    clean = re.sub(r'[a-z-]+\s*\{[^}]*\}', ' ', clean, flags=re.IGNORECASE)
    # CSS 선택자 패턴 제거
    clean = re.sub(r'\.[a-z-]+\s*\{[^}]*\}', ' ', clean, flags=re.IGNORECASE)

    # 5. HTML 엔티티 변환
    clean = clean.replace('&nbsp;', ' ')
    clean = clean.replace('&amp;', '&')
    clean = clean.replace('&lt;', '<')
    clean = clean.replace('&gt;', '>')
    clean = clean.replace('&quot;', '"')

    # 6. 연속 공백/줄바꿈 정리
    clean = re.sub(r'\s+', ' ', clean)

    return clean.strip()

# Gmail + Sheets 통합 스코프
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",  # 일괄 발송용
    "https://www.googleapis.com/auth/gmail.modify",  # 라벨 관리 권한
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
                        "sheetId": 0,
                        "title": "Emails",
                        "gridProperties": {"frozenRowCount": 1},
                    }
                },
                {
                    "properties": {
                        "sheetId": 1,
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

        # Initialize headers (v0.5.2 schema)
        headers = [
            "상태",              # A: 답장필요/불필요/완료 (Dropdown)
            "우선순위",          # B: 1-5
            "라벨",              # C: Gmail labels (Dropdown, multi-select style)
            "제목",              # D: Email subject
            "발신자",            # E: Sender
            "받은CC",            # F: CC recipients when received
            "받은시간",          # G: Received date (from Gmail)
            "내용미리보기",      # H: Body preview (200 chars)
            "AI요약",            # I: AI summary (5 lines max) - NEW
            "초안(제목)",        # J: Draft subject - NEW
            "초안(내용)",        # K: Draft body - NEW
            "보낼CC",            # L: CC to add when replying
            "전송예정",          # M: Checkbox for bulk send
            "Draft ID",          # N: Hidden (for API)
            "Thread ID",         # O: Hidden (for threading)
        ]

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Emails!A1:O1",
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
            # Hide columns N and O (Draft ID, Thread ID)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 13,  # Column N (Draft ID)
                        "endIndex": 15,    # Through Column O (Thread ID)
                    },
                    "properties": {"hiddenByUser": True},
                    "fields": "hiddenByUser",
                }
            },
            # Data validation for 상태 column (A) - Dropdown (limit to 100 rows)
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 1,
                        "endRowIndex": 101,
                        "startColumnIndex": 0,  # Column A
                        "endColumnIndex": 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": "답장필요"},
                                {"userEnteredValue": "답장불필요"},
                                {"userEnteredValue": "답장완료"},
                            ]
                        },
                        "showCustomUi": True,
                        "strict": False,
                    }
                }
            },
            # Data validation for 라벨 column (C) - Dropdown (limit to 100 rows)
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 1,
                        "endRowIndex": 101,
                        "startColumnIndex": 2,  # Column C
                        "endColumnIndex": 3,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": "P1-최우선"},
                                {"userEnteredValue": "P2-높음"},
                                {"userEnteredValue": "P3-보통"},
                                {"userEnteredValue": "P4-긴급"},
                                {"userEnteredValue": "P5-낮음"},
                                {"userEnteredValue": "답장필요"},
                                {"userEnteredValue": "답장불필요"},
                                {"userEnteredValue": "답장완료"},
                            ]
                        },
                        "showCustomUi": True,
                        "strict": False,  # Allow custom values for flexibility
                    }
                }
            },
            # Set column D width (subject)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 3,
                        "endIndex": 4,
                    },
                    "properties": {"pixelSize": 250},
                    "fields": "pixelSize",
                }
            },
            # Set column H width (내용미리보기)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 7,
                        "endIndex": 8,
                    },
                    "properties": {"pixelSize": 300},
                    "fields": "pixelSize",
                }
            },
            # Set column I width (AI요약)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 8,
                        "endIndex": 9,
                    },
                    "properties": {"pixelSize": 350},
                    "fields": "pixelSize",
                }
            },
            # Set column J width (초안 제목)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 9,
                        "endIndex": 10,
                    },
                    "properties": {"pixelSize": 200},
                    "fields": "pixelSize",
                }
            },
            # Set column K width (초안 내용)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 10,
                        "endIndex": 11,
                    },
                    "properties": {"pixelSize": 400},
                    "fields": "pixelSize",
                }
            },
            # Checkbox for 전송예정 column (M) - limit to 100 rows
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 1,
                        "endRowIndex": 101,  # Limit to 100 data rows
                        "startColumnIndex": 12,  # Column M
                        "endColumnIndex": 13,
                    },
                    "rule": {
                        "condition": {"type": "BOOLEAN"},
                        "showCustomUi": True,
                    }
                }
            },
            # Conditional formatting for 상태 column (A) - 답장필요 = red
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": 0,
                            "startRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1,
                        }],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [{"userEnteredValue": "답장필요"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 0.96, "green": 0.8, "blue": 0.8},
                                "textFormat": {"foregroundColor": {"red": 0.8, "green": 0.2, "blue": 0.2}}
                            }
                        }
                    },
                    "index": 0,
                }
            },
            # Conditional formatting for 상태 column (A) - 답장완료 = green
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": 0,
                            "startRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1,
                        }],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [{"userEnteredValue": "답장완료"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 0.8, "green": 0.92, "blue": 0.8},
                                "textFormat": {"foregroundColor": {"red": 0.2, "green": 0.6, "blue": 0.2}}
                            }
                        }
                    },
                    "index": 1,
                }
            },
            # Conditional formatting for 우선순위 column (B) - P1/P2 = red
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": 0,
                            "startRowIndex": 1,
                            "startColumnIndex": 1,
                            "endColumnIndex": 2,
                        }],
                        "booleanRule": {
                            "condition": {
                                "type": "NUMBER_LESS_THAN_EQ",
                                "values": [{"userEnteredValue": "2"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 0.96, "green": 0.8, "blue": 0.8},
                            }
                        }
                    },
                    "index": 2,
                }
            },
            # Conditional formatting for 우선순위 column (B) - P4/P5 = green
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": 0,
                            "startRowIndex": 1,
                            "startColumnIndex": 1,
                            "endColumnIndex": 2,
                        }],
                        "booleanRule": {
                            "condition": {
                                "type": "NUMBER_GREATER_THAN_EQ",
                                "values": [{"userEnteredValue": "4"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 0.8, "green": 0.92, "blue": 0.8},
                            }
                        }
                    },
                    "index": 3,
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
        email_data: Dict[str, Any],
        draft_id: str = "",
        draft_subject: str = "",   # NEW: Draft subject
        draft_body: str = "",      # NEW: Draft body content
        ai_summary: str = "",      # NEW: AI-generated summary
    ) -> None:
        """
        Add email to spreadsheet (v0.5.2 schema).

        Args:
            spreadsheet_id: Target spreadsheet ID
            email_data: Email metadata (subject, sender, body, cc, labels, etc.)
            draft_id: Gmail draft ID (e.g., 'r1234567890abcdef')
            draft_subject: Draft reply subject
            draft_body: Draft reply body content
            ai_summary: AI-generated summary of the email (5 lines max)
        """
        # 상태 매핑
        status_map = {
            "needs_response": "답장필요",
            "no_response": "답장불필요",
            "sent": "답장완료",
        }

        status = status_map.get(email_data.get("status", "needs_response"), "답장필요")

        # 라벨 처리 (사용자 정의 라벨만 표시)
        labels = email_data.get("labels", [])
        user_labels = [l for l in labels if not l.startswith(("CATEGORY_", "INBOX", "UNREAD", "SENT", "IMPORTANT", "STARRED", "DRAFT", "SPAM", "TRASH"))]
        labels_str = ", ".join(user_labels) if user_labels else ""

        # 내용미리보기 - body가 없으면 snippet 사용
        body_preview = email_data.get("body", "") or email_data.get("snippet", "")
        body_preview = body_preview[:300] if body_preview else ""

        # 전송예정 체크박스: 초안이 있으면 기본 TRUE
        send_checkbox = True if (draft_id and draft_body) else False

        row = [
            status,                                          # A: 상태
            email_data.get("priority", 3),                   # B: 우선순위
            labels_str,                                      # C: 라벨
            email_data.get("subject", ""),                   # D: 제목
            email_data.get("sender", ""),                    # E: 발신자
            email_data.get("cc", ""),                        # F: 받은CC
            email_data.get("date", ""),                      # G: 받은시간 (Gmail Date 헤더)
            body_preview,                                    # H: 내용미리보기
            ai_summary,                                      # I: AI요약
            draft_subject,                                   # J: 초안(제목)
            draft_body,                                      # K: 초안(내용)
            "",                                              # L: 보낼CC (사용자 입력)
            send_checkbox,                                   # M: 전송예정 (초안 있으면 TRUE)
            draft_id,                                        # N: Hidden
            email_data.get("thread_id", ""),                 # O: Hidden
        ]

        # Find next empty row (after row 1 header)
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Emails!A:A",
        ).execute()
        existing_rows = len(result.get("values", []))
        next_row = max(2, existing_rows + 1)  # At least row 2

        # Use update instead of append to avoid empty row issues
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Emails!A{next_row}:O{next_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [row]},
        ).execute()

    def get_drafts_to_send(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """
        Get draft IDs for emails marked for sending (v0.5.2 schema).

        Returns only rows where:
        - Column M (전송예정) is checked (TRUE)
        - Column N (Draft ID) is not empty

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            List of dicts with draft_id, draft_subject, draft_body, sender, cc, row_number

        Example:
            [
                {
                    'draft_id': 'r1234567890abcdef',
                    'draft_subject': 'Re: Meeting request',
                    'draft_body': 'Thank you for...',
                    'sender': 'boss@example.com',
                    'send_cc': 'team@example.com',
                    'row_number': 2
                }
            ]
        """
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range="Emails!A2:O")
            .execute()
        )

        rows = result.get("values", [])
        drafts_to_send = []

        for i, row in enumerate(rows, start=2):  # Row 2 = first data row
            # Ensure row has enough columns
            if len(row) < 14:
                continue

            send_checkbox = row[12] if len(row) > 12 else ""  # Column M (전송예정)
            draft_id = row[13] if len(row) > 13 else ""       # Column N (Draft ID)

            # Check if marked for sending
            if send_checkbox in ["TRUE", "True", True, "true"] and draft_id:
                drafts_to_send.append({
                    "draft_id": draft_id,
                    "draft_subject": row[9] if len(row) > 9 else "",   # Column J
                    "draft_body": row[10] if len(row) > 10 else "",    # Column K
                    "sender": row[4] if len(row) > 4 else "",          # Column E
                    "send_cc": row[11] if len(row) > 11 else "",       # Column L
                    "row_number": i,
                })

        return drafts_to_send

    # Keep old function for backward compatibility
    def get_emails_to_send(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
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
        uncheck_send_box: bool = True
    ) -> None:
        """
        Update email status after sending (v0.5.2 schema).

        Args:
            spreadsheet_id: Spreadsheet ID
            row_number: Row number to update (2 = first data row)
            new_status: New status (e.g., '답장완료')
            uncheck_send_box: If True, uncheck '전송예정' checkbox (column M)
        """
        # Update status (column A)
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Emails!A{row_number}",
            valueInputOption="RAW",
            body={"values": [[new_status]]},
        ).execute()

        # Uncheck send box (column M - 전송예정)
        if uncheck_send_box:
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"Emails!M{row_number}",
                valueInputOption="RAW",
                body={"values": [[False]]},
            ).execute()

    def batch_update_emails(
        self, spreadsheet_id: str, emails: List[Dict[str, Any]]
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
        sender_stats: Dict[str, Any],
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

    def _calculate_sender_auto_score(self, stats: Dict[str, Any]) -> int:
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

    def get_sender_importance_scores(self, spreadsheet_id: str) -> Dict[str, int]:
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

    # ===== 이메일 이력 관리 (누적 시트) =====

    # 고정된 이력 스프레드시트 ID (최초 생성 후 재사용)
    HISTORY_SPREADSHEET_ID = None  # 설정 파일에서 로드하거나 최초 생성 시 저장

    def get_or_create_history_sheet(self) -> str:
        """
        Get existing history spreadsheet or create new one.

        Returns:
            History spreadsheet ID
        """
        import os
        import json

        config_path = os.path.join(os.path.dirname(__file__), '..', 'email_history_config.json')

        # 기존 설정 파일에서 ID 로드
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                if config.get('history_spreadsheet_id'):
                    return config['history_spreadsheet_id']

        # 새로 생성
        spreadsheet_id = self._create_history_spreadsheet()

        # 설정 파일에 저장
        with open(config_path, 'w') as f:
            json.dump({'history_spreadsheet_id': spreadsheet_id}, f)

        return spreadsheet_id

    def _create_history_spreadsheet(self) -> str:
        """
        Create a new history spreadsheet for cumulative email tracking.
        Uses Email Tracker format (15 columns) for bulk management.

        Returns:
            New spreadsheet ID
        """
        spreadsheet = {
            "properties": {"title": "📚 Email History (누적 이력)"},
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "신규 메일",
                        "gridProperties": {"frozenRowCount": 1},
                    }
                },
                {
                    "properties": {
                        "sheetId": 1,
                        "title": "처리 이력",
                        "gridProperties": {"frozenRowCount": 1},
                    }
                },
            ],
        }

        spreadsheet = (
            self.service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )

        spreadsheet_id = spreadsheet.get("spreadsheetId")

        # Email Tracker 형식 헤더 (16열 - 답장여부 추가)
        headers = [
            "상태",              # A: 답장필요/불필요/완료
            "우선순위",          # B: 1-5
            "라벨",              # C: Gmail labels
            "제목",              # D: 이메일 제목
            "발신자",            # E: 발신자
            "받은CC",            # F: CC 수신자
            "받은시간",          # G: Gmail Date 헤더
            "내용미리보기",      # H: 본문 미리보기 (300자)
            "AI요약",            # I: AI 요약
            "초안(제목)",        # J: 답장 초안 제목
            "초안(내용)",        # K: 답장 초안 내용
            "보낼CC",            # L: 발송 시 CC
            "전송예정",          # M: 체크박스
            "답장여부",          # N: 답장함/미답장
            "Draft ID",         # O: Gmail Draft ID
            "Thread ID",        # P: Gmail Thread ID
        ]

        # 두 탭 모두에 헤더 설정
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="신규 메일!A1:P1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="처리 이력!A1:P1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

        # 헤더 포맷팅 및 조건부 서식 (두 탭 모두)
        requests = []
        for sheet_id in [0, 1]:  # 0: 신규 메일, 1: 처리 이력
            requests.extend(self._get_history_tab_format_requests(sheet_id))

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

        return spreadsheet_id

    def _get_history_tab_format_requests(self, sheet_id: int) -> List[dict]:
        """
        Get formatting requests for history tab (Email Tracker format).

        컬럼 구조 (16열):
        A(0): 상태, B(1): 우선순위, C(2): 라벨, D(3): 제목, E(4): 발신자
        F(5): 받은CC, G(6): 받은시간, H(7): 내용미리보기, I(8): AI요약
        J(9): 초안(제목), K(10): 초안(내용), L(11): 보낼CC
        M(12): 전송예정, N(13): 답장여부, O(14): Draft ID, P(15): Thread ID
        """
        return [
            # 헤더 포맷팅 (진한 회색 배경, 흰 글씨) - 헤더만!
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            # 데이터 행 배경색 흰색으로 (조건부 서식 적용 전 초기화)
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 1000},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                            "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}, "bold": False},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            # 컬럼 너비: 제목 (D)
            {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 250}, "fields": "pixelSize"}},
            # 컬럼 너비: 내용미리보기 (H)
            {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 7, "endIndex": 8}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
            # 컬럼 너비: AI요약 (I)
            {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 8, "endIndex": 9}, "properties": {"pixelSize": 350}, "fields": "pixelSize"}},
            # 컬럼 너비: 초안(제목) (J)
            {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 9, "endIndex": 10}, "properties": {"pixelSize": 200}, "fields": "pixelSize"}},
            # 컬럼 너비: 초안(내용) (K)
            {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 10, "endIndex": 11}, "properties": {"pixelSize": 400}, "fields": "pixelSize"}},
            # Draft ID, Thread ID 숨김 (O, P)
            {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 14, "endIndex": 16}, "properties": {"hiddenByUser": True}, "fields": "hiddenByUser"}},
            # ===== 상태 컬럼 (A) - 답장필요=연빨강, 답장완료=연초록 =====
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "답장필요"}]}, "format": {"backgroundColor": {"red": 0.96, "green": 0.8, "blue": 0.8}}}}, "index": 0}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "답장완료"}]}, "format": {"backgroundColor": {"red": 0.8, "green": 0.92, "blue": 0.8}}}}, "index": 1}},
            # ===== 우선순위 컬럼 (B) - P4-5=연초록, P1-2=연빨강 =====
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 2}], "booleanRule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "4"}]}, "format": {"backgroundColor": {"red": 0.8, "green": 0.92, "blue": 0.8}}}}, "index": 2}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 2}], "booleanRule": {"condition": {"type": "NUMBER_LESS_THAN_EQ", "values": [{"userEnteredValue": "2"}]}, "format": {"backgroundColor": {"red": 0.96, "green": 0.8, "blue": 0.8}}}}, "index": 3}},
            # ===== 답장여부 컬럼 (N) - 미답장=연빨강, 답장함=연초록 =====
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 13, "endColumnIndex": 14}], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "미답장"}]}, "format": {"backgroundColor": {"red": 0.96, "green": 0.8, "blue": 0.8}}}}, "index": 4}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 13, "endColumnIndex": 14}], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "답장함"}]}, "format": {"backgroundColor": {"red": 0.8, "green": 0.92, "blue": 0.8}}}}, "index": 5}},
            # 상태 드롭다운 (A)
            {"setDataValidation": {"range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 1}, "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": "답장필요"}, {"userEnteredValue": "답장불필요"}, {"userEnteredValue": "답장완료"}]}, "showCustomUi": True, "strict": False}}},
            # 전송예정 체크박스 (M)
            {"setDataValidation": {"range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 12, "endColumnIndex": 13}, "rule": {"condition": {"type": "BOOLEAN"}, "showCustomUi": True}}},
            # 답장여부 드롭다운 (N)
            {"setDataValidation": {"range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 13, "endColumnIndex": 14}, "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": "답장함"}, {"userEnteredValue": "미답장"}]}, "showCustomUi": True, "strict": False}}},
        ]

    def add_to_history(
        self,
        email_data: dict,
        classification: dict,
        replied: bool,
    ) -> str:
        """
        Add or update processed email in history sheet (Email Tracker 15-column format).

        Args:
            email_data: Email data dict with id, subject, sender, date, cc, body, thread_id, labels
            classification: Classification result with priority, summary, draft_subject, draft_body, etc.
            replied: Whether user has replied

        Returns:
            'added' if new, 'updated' if existing was updated, 'unchanged' if same
        """
        history_id = self.get_or_create_history_sheet()
        thread_id = email_data.get('thread_id', '')

        # 상태 결정
        if replied:
            status = '답장완료'
        elif classification.get('requires_response'):
            status = '답장필요'
        else:
            status = '답장불필요'

        # 라벨 처리
        labels = email_data.get('labels', [])
        user_labels = [l for l in labels if not l.startswith(("CATEGORY_", "INBOX", "UNREAD", "SENT", "IMPORTANT", "STARRED", "DRAFT", "SPAM", "TRASH"))]
        labels_str = ", ".join(user_labels) if user_labels else ""

        # 본문 미리보기 (HTML 태그 제거)
        body_raw = email_data.get('body', '') or email_data.get('snippet', '')
        body_preview = strip_html(body_raw)[:300] if body_raw else ""

        # 답장여부
        reply_status = '답장함' if replied else '미답장'

        # 행 데이터 (16열 Email Tracker 형식)
        row = [
            status,                                         # A: 상태
            classification.get('priority', 3),              # B: 우선순위
            labels_str,                                     # C: 라벨
            email_data.get('subject', ''),                  # D: 제목
            email_data.get('sender', ''),                   # E: 발신자
            email_data.get('cc', ''),                       # F: 받은CC
            email_data.get('date', ''),                     # G: 받은시간
            body_preview,                                   # H: 내용미리보기
            classification.get('summary', ''),              # I: AI요약
            classification.get('draft_subject', '') or '',  # J: 초안(제목)
            classification.get('draft_body', '') or '',     # K: 초안(내용)
            '',                                             # L: 보낼CC
            False,                                          # M: 전송예정
            reply_status,                                   # N: 답장여부
            '',                                             # O: Draft ID
            thread_id,                                      # P: Thread ID
        ]

        # 기존 행 찾기 (Thread ID로 검색)
        existing_row = self._find_history_row(history_id, thread_id)

        if existing_row:
            # 기존 데이터와 비교
            old_status = existing_row.get('status', '')

            if old_status == status:
                return 'unchanged'

            # 업데이트
            self.service.spreadsheets().values().update(
                spreadsheetId=history_id,
                range=f"처리 이력!A{existing_row['row_number']}:P{existing_row['row_number']}",
                valueInputOption="USER_ENTERED",
                body={"values": [row]},
            ).execute()
            return 'updated'
        else:
            # 신규 추가
            self.service.spreadsheets().values().append(
                spreadsheetId=history_id,
                range="처리 이력!A:P",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]},
            ).execute()
            return 'added'

    def _find_history_row(self, history_id: str, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Find existing row in history by Thread ID (column P, index 15).

        Returns:
            Dict with row data and row_number, or None if not found
        """
        if not thread_id:
            return None

        result = self.service.spreadsheets().values().get(
            spreadsheetId=history_id,
            range="처리 이력!A:P",
        ).execute()

        rows = result.get("values", [])

        for i, row in enumerate(rows[1:], start=2):  # Skip header, row 2 = first data
            if len(row) >= 16 and row[15] == thread_id:  # Column P = Thread ID (index 15)
                return {
                    'row_number': i,
                    'status': row[0] if len(row) > 0 else '',
                }

        return None

    def _check_history_exists(self, history_id: str, message_id: str) -> bool:
        """
        Check if message already exists in history.

        Args:
            history_id: History spreadsheet ID
            message_id: Gmail message ID to check

        Returns:
            True if exists, False otherwise
        """
        if not message_id:
            return False

        result = self.service.spreadsheets().values().get(
            spreadsheetId=history_id,
            range="처리 이력!K:K",  # Message ID 컬럼
        ).execute()

        rows = result.get("values", [])
        existing_ids = [row[0] for row in rows if row]

        return message_id in existing_ids

    def get_history_spreadsheet_url(self) -> str:
        """
        Get URL to history spreadsheet.

        Returns:
            Spreadsheet URL or empty string if not created yet
        """
        import os
        import json

        config_path = os.path.join(os.path.dirname(__file__), '..', 'email_history_config.json')

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                sheet_id = config.get('history_spreadsheet_id', '')
                if sheet_id:
                    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"

        return ""

    def get_tab_ids(self, spreadsheet_id: str) -> Dict[str, int]:
        """
        Get sheet IDs for each tab.

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            Dict mapping tab name to sheet ID
            e.g., {'신규 메일': 123456, '처리 이력': 0}
        """
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        return {
            sheet['properties']['title']: sheet['properties']['sheetId']
            for sheet in spreadsheet['sheets']
        }

    def ensure_new_emails_tab_exists(self, spreadsheet_id: str) -> int:
        """
        Ensure '신규 메일' tab exists in the spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            Sheet ID of '신규 메일' tab
        """
        # Check if tab exists
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == '신규 메일':
                return sheet['properties']['sheetId']

        # Create new tab
        requests = [{
            "addSheet": {
                "properties": {
                    "title": "신규 메일",
                    "index": 0,  # First tab
                    "gridProperties": {"frozenRowCount": 1},
                }
            }
        }]

        result = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()

        new_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']

        # Email Tracker 형식 헤더 (16열 - 답장여부 포함)
        headers = [
            "상태", "우선순위", "라벨", "제목", "발신자", "받은CC", "받은시간",
            "내용미리보기", "AI요약", "초안(제목)", "초안(내용)", "보낼CC",
            "전송예정", "답장여부", "Draft ID", "Thread ID"
        ]

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="신규 메일!A1:P1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

        # Format header and conditional formatting
        format_requests = self._get_history_tab_format_requests(new_sheet_id)

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": format_requests}
        ).execute()

        return new_sheet_id

    def clear_new_emails_tab(self, spreadsheet_id: str) -> None:
        """
        Clear all data from '신규 메일' tab (keep headers).

        Args:
            spreadsheet_id: Spreadsheet ID
        """
        self.ensure_new_emails_tab_exists(spreadsheet_id)

        # Clear data rows (keep header row 1) - 16 columns A:P
        self.service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range="신규 메일!A2:P",
        ).execute()

    def add_to_new_emails(
        self,
        email_data: dict,
        classification: dict,
        replied: bool,
    ) -> None:
        """
        Add email to '신규 메일' tab (Email Tracker 16-column format).

        Args:
            email_data: Email data dict
            classification: Classification result
            replied: Whether user has replied
        """
        history_id = self.get_or_create_history_sheet()
        self.ensure_new_emails_tab_exists(history_id)

        # 상태 결정
        if replied:
            status = '답장완료'
        elif classification.get('requires_response'):
            status = '답장필요'
        else:
            status = '답장불필요'

        # 라벨 처리
        labels = email_data.get('labels', [])
        user_labels = [l for l in labels if not l.startswith(("CATEGORY_", "INBOX", "UNREAD", "SENT", "IMPORTANT", "STARRED", "DRAFT", "SPAM", "TRASH"))]
        labels_str = ", ".join(user_labels) if user_labels else ""

        # 본문 미리보기 (HTML 태그 제거)
        body_raw = email_data.get('body', '') or email_data.get('snippet', '')
        body_preview = strip_html(body_raw)[:300] if body_raw else ""

        # 답장여부
        reply_status = '답장함' if replied else '미답장'

        row = [
            status,                                         # A: 상태
            classification.get('priority', 3),              # B: 우선순위
            labels_str,                                     # C: 라벨
            email_data.get('subject', ''),                  # D: 제목
            email_data.get('sender', ''),                   # E: 발신자
            email_data.get('cc', ''),                       # F: 받은CC
            email_data.get('date', ''),                     # G: 받은시간
            body_preview,                                   # H: 내용미리보기
            classification.get('summary', ''),              # I: AI요약
            classification.get('draft_subject', '') or '',  # J: 초안(제목)
            classification.get('draft_body', '') or '',     # K: 초안(내용)
            '',                                             # L: 보낼CC
            False,                                          # M: 전송예정
            reply_status,                                   # N: 답장여부
            '',                                             # O: Draft ID
            email_data.get('thread_id', ''),                # P: Thread ID
        ]

        self.service.spreadsheets().values().append(
            spreadsheetId=history_id,
            range="신규 메일!A:P",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()

    def add_email_to_both_tabs(
        self,
        email_data: dict,
        classification: dict,
        replied: bool,
    ) -> str:
        """
        Add email to both '신규 메일' and '처리 이력' tabs.

        '신규 메일': 매 분석 시 초기화 후 새 이메일만 추가
        '처리 이력': 누적 저장 (중복 시 업데이트)

        Args:
            email_data: Email data dict
            classification: Classification result
            replied: Whether user has replied

        Returns:
            History result: 'added', 'updated', or 'unchanged'
        """
        # 1. 신규 메일 탭에 추가
        self.add_to_new_emails(email_data, classification, replied)

        # 2. 처리 이력 탭에 추가/업데이트
        return self.add_to_history(email_data, classification, replied)
