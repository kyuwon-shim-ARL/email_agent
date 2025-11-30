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
        self, thread_id: str, to: str, subject: str, body: str, is_html: bool = True
    ) -> dict[str, Any]:
        """
        Create a draft reply in Gmail with HTML support.

        Args:
            thread_id: Thread ID to reply to
            to: Recipient email address
            subject: Email subject (with Re: prefix)
            body: Draft email body (HTML or plain text)
            is_html: If True, body is treated as HTML (default: True)

        Returns:
            Created draft information with 'id' and 'message' fields
        """
        import base64
        from email.mime.text import MIMEText

        # Create message with appropriate content type
        message = MIMEText(body, 'html' if is_html else 'plain', 'utf-8')
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

    def send_draft(self, draft_id: str) -> dict[str, Any]:
        """
        Send an existing Gmail draft by ID.

        This preserves all user edits made in the Gmail app.

        Args:
            draft_id: Draft ID from create_draft() return value

        Returns:
            Sent message information

        Raises:
            HttpError: If draft not found (404) or send fails
        """
        sent = (
            self.service.users()
            .drafts()
            .send(userId="me", body={"id": draft_id})
            .execute()
        )

        return sent

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

    def batch_send_drafts(self, draft_ids: list[str]) -> list[dict[str, Any]]:
        """
        Send multiple Gmail drafts by ID.

        Preserves all user edits made in Gmail app.

        Args:
            draft_ids: List of draft IDs to send

        Returns:
            List of results with success/failure status

        Example:
            results = gmail.batch_send_drafts(['r123...', 'r456...'])
            for result in results:
                if result['success']:
                    print(f"Sent: {result['message_id']}")
                else:
                    print(f"Failed: {result['error']}")
        """
        results = []

        for draft_id in draft_ids:
            try:
                sent = self.send_draft(draft_id)

                results.append({
                    "draft_id": draft_id,
                    "success": True,
                    "message_id": sent.get("id"),
                    "thread_id": sent.get("threadId"),
                    "error": None,
                })
            except Exception as e:
                results.append({
                    "draft_id": draft_id,
                    "success": False,
                    "message_id": None,
                    "thread_id": None,
                    "error": str(e),
                })

        return results

    def batch_send_emails(self, emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        DEPRECATED: Use batch_send_drafts() instead.

        This function recreates emails from text and loses Gmail edits.
        Only kept for backward compatibility.

        Args:
            emails: List of email dicts with 'to', 'subject', 'body', 'cc', 'thread_id'

        Returns:
            List of results with success/failure status
        """
        import warnings
        warnings.warn(
            "batch_send_emails() is deprecated. Use batch_send_drafts() instead.",
            DeprecationWarning,
            stacklevel=2
        )
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

    def collect_all_sender_stats(
        self,
        max_emails: int = 200,
        classified_emails: list[dict[str, Any]] | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Collect statistics for all senders for sender management tab.

        This function analyzes recent emails and calculates stats needed
        for automatic sender importance scoring.

        Args:
            max_emails: Maximum number of emails to analyze (default: 200)
            classified_emails: Optional list of already classified emails with priority scores

        Returns:
            Dict mapping sender email to stats:
            {
                'sender@example.com': {
                    'name': 'John Doe',
                    'total_sent': 5,
                    'total_received': 10,
                    'p45_count': 3,  # Count of P4-5 priority emails
                    'total_emails': 10,  # Total received from this sender
                    'recent_7days': 2,
                    'last_contact_date': '2024-01-15',
                }
            }
        """
        import re
        from datetime import datetime, timedelta
        from collections import defaultdict

        sender_stats = defaultdict(lambda: {
            'name': '',
            'total_sent': 0,
            'total_received': 0,
            'p45_count': 0,
            'total_emails': 0,
            'recent_7days': 0,
            'last_contact_date': '',
        })

        # Get recent emails (both inbox and sent)
        query = 'in:inbox OR in:sent'
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_emails)
            .execute()
        )

        messages = results.get("messages", [])
        seven_days_ago = datetime.now() - timedelta(days=7)

        # Build priority map from classified emails if provided
        priority_map = {}
        if classified_emails:
            for email in classified_emails:
                sender = email.get('sender', '')
                # Extract email from "Name <email>" format
                email_match = re.search(r'<(.+?)>', sender)
                sender_email = email_match.group(1) if email_match else sender
                priority = email.get('priority', 3)

                if sender_email not in priority_map:
                    priority_map[sender_email] = []
                priority_map[sender_email].append(priority)

        for msg in messages:
            # Get message details
            message = (
                self.service.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From", "To", "Date"]
                ).execute()
            )

            headers = message["payload"]["headers"]
            from_header = next((h["value"] for h in headers if h["name"] == "From"), "")
            to_header = next((h["value"] for h in headers if h["name"] == "To"), "")
            date_header = next((h["value"] for h in headers if h["name"] == "Date"), "")

            # Parse date
            try:
                # Simple date parsing (handles most formats)
                msg_date = datetime.strptime(date_header.split(' +')[0].split(' -')[0].strip(),
                                            "%a, %d %b %Y %H:%M:%S")
            except:
                msg_date = datetime.now()

            # Determine if sent or received
            is_sent = 'SENT' in message.get('labelIds', [])

            # Extract sender email and name
            sender_match = re.search(r'(.+?)\s*<(.+?)>', from_header)
            if sender_match:
                sender_name = sender_match.group(1).strip(' "\'')
                sender_email = sender_match.group(2)
            else:
                sender_name = ''
                sender_email = from_header

            # Skip if it's me (for sent emails, track recipient instead)
            if is_sent:
                # For sent emails, extract recipient
                recipient_match = re.search(r'<(.+?)>', to_header)
                sender_email = recipient_match.group(1) if recipient_match else to_header
                sender_stats[sender_email]['total_sent'] += 1
            else:
                # Received email
                sender_stats[sender_email]['name'] = sender_name or sender_stats[sender_email]['name']
                sender_stats[sender_email]['total_received'] += 1
                sender_stats[sender_email]['total_emails'] += 1

                # Check priority (from classified_emails if available)
                if sender_email in priority_map:
                    # Use average priority from classified emails
                    avg_priority = sum(priority_map[sender_email]) / len(priority_map[sender_email])
                    if avg_priority >= 4:
                        sender_stats[sender_email]['p45_count'] += 1

            # Update last contact date
            date_str = msg_date.strftime('%Y-%m-%d')
            if not sender_stats[sender_email]['last_contact_date'] or \
               date_str > sender_stats[sender_email]['last_contact_date']:
                sender_stats[sender_email]['last_contact_date'] = date_str

            # Check if within last 7 days
            if msg_date >= seven_days_ago:
                sender_stats[sender_email]['recent_7days'] += 1

        # Convert defaultdict to regular dict and filter out low-activity senders
        result = {}
        for email, stats in sender_stats.items():
            # Only include senders with at least 1 received email
            if stats['total_received'] > 0:
                result[email] = dict(stats)

        return result

    def create_or_get_label(self, label_name: str, color: dict[str, str] | None = None) -> str:
        """
        Create a Gmail label or get existing one.

        Args:
            label_name: Label name (e.g., "답장필요", "P5-최우선")
            color: Optional color dict with 'backgroundColor' and 'textColor'
                   e.g., {'backgroundColor': '#fb4c2f', 'textColor': '#ffffff'}

        Returns:
            Label ID

        Example:
            label_id = gmail.create_or_get_label(
                "P5-최우선",
                {'backgroundColor': '#fb4c2f', 'textColor': '#ffffff'}
            )
        """
        # Check if label already exists
        results = self.service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        for label in labels:
            if label["name"] == label_name:
                return label["id"]

        # Create new label
        label_object = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }

        if color:
            label_object["color"] = color

        created = (
            self.service.users()
            .labels()
            .create(userId="me", body=label_object)
            .execute()
        )

        return created["id"]

    def setup_email_labels(self) -> dict[str, str]:
        """
        Set up all email classification labels with colors.

        Creates 8 labels:
        - 3 status labels: 답장필요, 답장불필요, 답장완료
        - 5 priority labels: P1-최저, P2-낮음, P3-보통, P4-긴급, P5-최우선

        Returns:
            Dict mapping label name to label ID

        Example:
            label_ids = gmail.setup_email_labels()
            # {'답장필요': 'Label_123', 'P5-최우선': 'Label_456', ...}
        """
        labels_config = {
            # Status labels
            "답장필요": {"backgroundColor": "#fb4c2f", "textColor": "#ffffff"},      # Red
            "답장불필요": {"backgroundColor": "#cccccc", "textColor": "#000000"},    # Gray
            "답장완료": {"backgroundColor": "#16a766", "textColor": "#ffffff"},      # Green

            # Priority labels
            "P1-최저": {"backgroundColor": "#efefef", "textColor": "#000000"},       # Light gray
            "P2-낮음": {"backgroundColor": "#a4c2f4", "textColor": "#000000"},       # Light blue
            "P3-보통": {"backgroundColor": "#fad165", "textColor": "#000000"},       # Yellow
            "P4-긴급": {"backgroundColor": "#fb4c2f", "textColor": "#ffffff"},       # Orange-red
            "P5-최우선": {"backgroundColor": "#cc0000", "textColor": "#ffffff"},     # Dark red
        }

        label_ids = {}
        for label_name, color in labels_config.items():
            label_id = self.create_or_get_label(label_name, color)
            label_ids[label_name] = label_id

        return label_ids

    def apply_labels_to_email(
        self,
        message_id: str,
        status: str,
        priority: int,
        label_ids: dict[str, str]
    ) -> None:
        """
        Apply status and priority labels to an email.

        Args:
            message_id: Gmail message ID
            status: Status ("답장필요", "답장불필요", "답장완료")
            priority: Priority (1-5)
            label_ids: Dict mapping label names to IDs (from setup_email_labels)

        Example:
            label_ids = gmail.setup_email_labels()
            gmail.apply_labels_to_email(
                message_id="abc123",
                status="답장필요",
                priority=5,
                label_ids=label_ids
            )
        """
        # Map priority number to label name
        priority_labels = {
            1: "P1-최저",
            2: "P2-낮음",
            3: "P3-보통",
            4: "P4-긴급",
            5: "P5-최우선",
        }

        # Get label IDs to add
        labels_to_add = []

        if status in label_ids:
            labels_to_add.append(label_ids[status])

        priority_label = priority_labels.get(priority, "P3-보통")
        if priority_label in label_ids:
            labels_to_add.append(label_ids[priority_label])

        # Apply labels
        if labels_to_add:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": labels_to_add}
            ).execute()

    def remove_all_classification_labels(self, message_id: str, label_ids: dict[str, str]) -> None:
        """
        Remove all classification labels from an email.

        Useful when reclassifying an email.

        Args:
            message_id: Gmail message ID
            label_ids: Dict mapping label names to IDs (from setup_email_labels)
        """
        labels_to_remove = list(label_ids.values())

        if labels_to_remove:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": labels_to_remove}
            ).execute()
