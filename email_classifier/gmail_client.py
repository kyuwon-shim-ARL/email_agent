"""Gmail API client for fetching emails."""
import os.path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",  # 초안 작성 권한
    "https://www.googleapis.com/auth/gmail.send",  # 메일 발송 권한
]


class GmailClient:
    """Simple Gmail API client."""

    def __init__(self) -> None:
        """Initialize Gmail client with OAuth."""
        self.creds = self._get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    def _get_credentials(self) -> Credentials:
        """Get or create OAuth credentials."""
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

    def get_recent_emails(self, max_results: int = 10) -> list[dict[str, Any]]:
        """
        Get recent emails from inbox.

        Args:
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries with id, subject, sender, snippet
        """
        # Get message list
        results = (
            self.service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            # Get full message details
            message = (
                self.service.users().messages().get(userId="me", id=msg["id"]).execute()
            )

            # Extract headers
            headers = message["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")

            # Extract thread ID and full body
            thread_id = message["threadId"]

            # Get email body (prefer text/plain)
            body = self._get_message_body(message["payload"])

            emails.append(
                {
                    "id": message["id"],
                    "thread_id": thread_id,
                    "subject": subject,
                    "sender": sender,
                    "snippet": message["snippet"],
                    "body": body,
                }
            )

        return emails

    def _get_message_body(self, payload: dict) -> str:
        """Extract email body from message payload."""
        body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        import base64
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode()
                        break
        elif "body" in payload and "data" in payload["body"]:
            import base64
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode()

        return body or ""

    def create_draft(
        self, thread_id: str, to: str, subject: str, body: str
    ) -> dict[str, Any]:
        """
        Create a draft reply in Gmail.

        Args:
            thread_id: Thread ID to reply to
            to: Recipient email address
            subject: Email subject (with Re: prefix)
            body: Draft email body

        Returns:
            Created draft information
        """
        import base64
        from email.mime.text import MIMEText

        # Create message
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create draft
        draft = (
            self.service.users()
            .drafts()
            .create(
                userId="me",
                body={"message": {"raw": raw, "threadId": thread_id}},
            )
            .execute()
        )

        return draft

    def send_email(
        self, to: str, subject: str, body: str, cc: str | None = None, thread_id: str | None = None
    ) -> dict[str, Any]:
        """
        Send an email directly (for batch sending).

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: CC recipients (comma-separated)
            thread_id: Thread ID for replies

        Returns:
            Sent message information
        """
        import base64
        from email.mime.text import MIMEText

        # Create message
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if cc:
            message["cc"] = cc

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send email
        send_message = {"raw": raw}
        if thread_id:
            send_message["threadId"] = thread_id

        sent = (
            self.service.users()
            .messages()
            .send(userId="me", body=send_message)
            .execute()
        )

        return sent

    def batch_send_emails(self, emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Send multiple emails in batch.

        Args:
            emails: List of email dicts with 'to', 'subject', 'body', 'cc', 'thread_id'

        Returns:
            List of results with success/failure status
        """
        results = []

        for email in emails:
            try:
                sent = self.send_email(
                    to=email.get("to", ""),
                    subject=email.get("subject", ""),
                    body=email.get("body", ""),
                    cc=email.get("cc"),
                    thread_id=email.get("thread_id"),
                )

                results.append({
                    "email": email,
                    "success": True,
                    "message_id": sent.get("id"),
                    "error": None,
                })
            except Exception as e:
                results.append({
                    "email": email,
                    "success": False,
                    "message_id": None,
                    "error": str(e),
                })

        return results

    def get_sent_emails(self, max_results: int = 50) -> list[dict[str, Any]]:
        """
        Get user's sent emails for style analysis.

        Args:
            max_results: Maximum number of sent emails to fetch

        Returns:
            List of sent email dictionaries with subject, body, and recipient
        """
        # Get sent messages
        results = (
            self.service.users()
            .messages()
            .list(userId="me", labelIds=["SENT"], maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        sent_emails = []

        for msg in messages:
            # Get full message details
            message = (
                self.service.users().messages().get(userId="me", id=msg["id"]).execute()
            )

            # Extract headers
            headers = message["payload"]["headers"]
            subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"), "No Subject"
            )
            recipient = next(
                (h["value"] for h in headers if h["name"] == "To"), "Unknown"
            )

            # Get email body
            body = self._get_message_body(message["payload"])

            # Only include if body is substantial (not just "Sent from my iPhone")
            if len(body.strip()) > 50:
                sent_emails.append({
                    "subject": subject,
                    "body": body,
                    "recipient": recipient,
                })

        return sent_emails

    def get_conversation_history(self, sender_email: str, max_results: int = 20) -> dict[str, Any]:
        """
        Get conversation history with a specific sender.

        Args:
            sender_email: Email address to get history for
            max_results: Maximum number of messages to analyze

        Returns:
            Dictionary with sent/received emails and conversation stats
        """
        # Extract email address from "Name <email@domain.com>" format
        import re
        email_match = re.search(r'<(.+?)>', sender_email)
        search_email = email_match.group(1) if email_match else sender_email

        # Search for emails from/to this sender
        query = f'from:{search_email} OR to:{search_email}'
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])

        sent_to_sender = []
        received_from_sender = []

        for msg in messages:
            # Get full message details
            message = (
                self.service.users().messages().get(userId="me", id=msg["id"]).execute()
            )

            # Extract headers
            headers = message["payload"]["headers"]
            from_header = next((h["value"] for h in headers if h["name"] == "From"), "")
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")

            # Get email body
            body = self._get_message_body(message["payload"])

            # Categorize by sent/received
            if search_email.lower() in from_header.lower():
                # Received from sender
                received_from_sender.append({
                    "subject": subject,
                    "body": body,
                })
            else:
                # Sent to sender
                if len(body.strip()) > 50:
                    sent_to_sender.append({
                        "subject": subject,
                        "body": body,
                    })

        # Calculate priority score (발신 가중치 적용)
        # 내가 보낸 메일에 2배 가중치 (회사 공지 등 수신만 하는 경우 중요도 낮음)
        weighted_score = len(sent_to_sender) * 2 + len(received_from_sender)

        # 첫 연락 여부 확인
        is_first_contact = len(sent_to_sender) == 0 and len(received_from_sender) == 1

        return {
            "sender_email": search_email,
            "sent_to_sender": sent_to_sender,
            "received_from_sender": received_from_sender,
            "total_sent": len(sent_to_sender),
            "total_received": len(received_from_sender),
            "total_exchanges": len(sent_to_sender) + len(received_from_sender),
            "weighted_score": weighted_score,
            "is_first_contact": is_first_contact,
        }
