"""Email classifier designed to work with Claude Code - no API costs!"""
import json
from pathlib import Path
from typing import TypedDict


class ClassificationResult(TypedDict):
    """Classification result."""
    requires_response: bool
    confidence: float
    reason: str
    priority: int  # 1-5, where 5 is highest priority


class DraftReply(TypedDict):
    """Draft reply."""
    subject: str
    body: str
    tone: str


class WritingStyle(TypedDict):
    """User's writing style profile."""
    greeting_style: str
    closing_style: str
    formality_level: str
    common_phrases: list[str]
    tone_description: str
    example_sentences: list[str]


class SenderHistory(TypedDict):
    """Conversation history with a specific sender."""
    sender_email: str
    total_exchanges: int
    writing_style: WritingStyle | None
    has_history: bool


class ClaudeCodeClassifier:
    """
    Email classifier that works with Claude Code session.

    Instead of calling Claude API directly (costs money),
    this writes prompts to files that you can feed to Claude Code.
    """

    def __init__(self, work_dir: str = "/tmp/email_classifier") -> None:
        """Initialize classifier with working directory."""
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def prepare_classification_batch(
        self, emails: list[dict], sender_histories: dict[str, SenderHistory] | None = None
    ) -> str:
        """
        Prepare all emails for batch classification with priority.

        Args:
            emails: List of email dicts with subject, sender, snippet
            sender_histories: Optional dict mapping sender email to conversation history

        Returns:
            Path to the prompt file
        """
        prompt = """I need you to classify these emails to determine which require responses and assign priorities.

Guidelines:
- Newsletters, notifications, automated messages → NO response needed
- Direct questions, meeting requests, personal messages → Response needed
- Consider sender relationship and urgency

Priority levels (1-5):
  * 5 = HIGHEST:
    - First contact (처음 연락) - needs investigation
    - VIP contacts with sent emails > 10 (내가 자주 보낸 사람)
    - Direct urgent questions
  * 4 = High:
    - Known frequent contacts (교신 10+ times)
    - Action items from manager
  * 3 = Normal:
    - Regular correspondence (교신 3-10 times)
    - General work emails
  * 2 = Low:
    - Broadcast emails (수신만 한 경우)
    - FYI, optional
  * 1 = Very low:
    - Newsletters, automated notifications

**IMPORTANT Priority Rules:**
- 첫 연락 (is_first_contact = True) → Priority 5
- 내가 보낸 메일 많음 (sent > 10) → Priority 5
- 교신 많지만 내가 안 보냄 (received only) → Priority 2-3

Emails to classify:

"""
        for i, email in enumerate(emails, 1):
            sender = email['sender']
            history_info = ""

            if sender_histories and sender in sender_histories:
                history = sender_histories[sender]
                total = history.get('total_exchanges', 0)
                sent = history.get('total_sent', 0)
                received = history.get('total_received', 0)
                is_first = history.get('is_first_contact', False)
                weighted = history.get('weighted_score', 0)

                if total > 0 or is_first:
                    history_info = f"\n   [History: {total} exchanges (sent: {sent}, received: {received})"
                    if is_first:
                        history_info += " - **FIRST CONTACT**"
                    history_info += f", weighted_score: {weighted}]"

            prompt += f"""
{i}. Subject: {email['subject']}
   From: {sender}{history_info}
   Preview: {email['snippet'][:200]}...

"""

        prompt += """
Respond with a JSON array where each object has:
{
  "email_index": <number>,
  "requires_response": <true/false>,
  "confidence": <0.0-1.0>,
  "reason": "<brief explanation>",
  "priority": <1-5>
}

Example:
[
  {"email_index": 1, "requires_response": true, "confidence": 0.95, "reason": "Direct question from frequent contact", "priority": 5},
  {"email_index": 2, "requires_response": false, "confidence": 0.99, "reason": "Automated newsletter", "priority": 1}
]
"""

        prompt_file = self.work_dir / "classify_batch.txt"
        prompt_file.write_text(prompt)

        return str(prompt_file)

    def parse_classification_batch(
        self, response_json: str
    ) -> list[ClassificationResult]:
        """
        Parse Claude's batch classification response.

        Args:
            response_json: JSON string from Claude

        Returns:
            List of classification results with priority
        """
        try:
            results = json.loads(response_json)
            return [
                {
                    "requires_response": r["requires_response"],
                    "confidence": r["confidence"],
                    "reason": r["reason"],
                    "priority": r.get("priority", 3),  # Default priority 3
                }
                for r in results
            ]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Failed to parse response: {e}")
            return []

    def prepare_style_analysis(
        self, sent_emails: list[dict], specific_recipient: str | None = None
    ) -> str:
        """
        Prepare sent emails for style analysis.

        Args:
            sent_emails: List of sent email dicts
            specific_recipient: Optional - analyze style for specific recipient

        Returns:
            Path to the prompt file
        """
        if specific_recipient:
            # Filter emails to specific recipient
            filtered_emails = [
                email for email in sent_emails
                if specific_recipient.lower() in email.get('recipient', '').lower()
            ]
            if len(filtered_emails) < 3:
                # Not enough data for this recipient, use default
                filtered_emails = sent_emails[:20]
                analysis_note = f"(Not enough emails to {specific_recipient}, using general style)"
            else:
                filtered_emails = filtered_emails[:20]
                analysis_note = f"(Analyzing style specifically for {specific_recipient})"
        else:
            filtered_emails = sent_emails[:20]
            analysis_note = "(Analyzing general writing style)"

        prompt = f"""Analyze my writing style from these sent emails {analysis_note}.

Extract:
1. GREETING_STYLE: How do I typically start emails?
2. CLOSING_STYLE: How do I typically end emails?
3. FORMALITY_LEVEL: formal / casual / neutral
4. COMMON_PHRASES: 5-7 phrases I frequently use
5. TONE_DESCRIPTION: Overall tone
6. EXAMPLE_SENTENCES: 3-4 typical sentence structures

Sent Emails:

"""
        for i, email in enumerate(filtered_emails, 1):
            prompt += f"""
Email {i}:
Subject: {email.get('subject', 'N/A')}
Body:
{email.get('body', 'N/A')[:500]}...

---
"""

        prompt += """
Respond in this exact format:
```json
{
  "greeting_style": "Hi,",
  "closing_style": "Best regards,",
  "formality_level": "neutral",
  "common_phrases": ["phrase1", "phrase2", ...],
  "tone_description": "Professional and friendly",
  "example_sentences": ["sentence1", "sentence2", ...]
}
```
"""

        filename = "analyze_style.txt" if not specific_recipient else f"analyze_style_{specific_recipient.replace('@', '_at_')}.txt"
        prompt_file = self.work_dir / filename
        prompt_file.write_text(prompt)

        return str(prompt_file)

    def parse_style_analysis(
        self, response_json: str
    ) -> WritingStyle:
        """
        Parse Claude's style analysis response.

        Args:
            response_json: JSON string from Claude

        Returns:
            WritingStyle profile
        """
        try:
            # Extract JSON from code block if present
            if "```json" in response_json:
                start = response_json.find("```json") + 7
                end = response_json.find("```", start)
                response_json = response_json[start:end].strip()
            elif "```" in response_json:
                start = response_json.find("```") + 3
                end = response_json.find("```", start)
                response_json = response_json[start:end].strip()

            style = json.loads(response_json)
            return {
                "greeting_style": style.get("greeting_style", "Hello,"),
                "closing_style": style.get("closing_style", "Best regards,"),
                "formality_level": style.get("formality_level", "neutral"),
                "common_phrases": style.get("common_phrases", []),
                "tone_description": style.get("tone_description", "Professional"),
                "example_sentences": style.get("example_sentences", []),
            }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Failed to parse style analysis: {e}")
            return self._default_style()

    def prepare_draft_batch(
        self,
        emails: list[dict],
        default_style: WritingStyle | None = None,
        sender_styles: dict[str, WritingStyle] | None = None,
        conversation_contexts: dict[str, list[dict]] | None = None
    ) -> str:
        """
        Prepare batch draft generation prompt with sender-specific styles.

        Args:
            emails: List of emails needing responses
            default_style: Default writing style (fallback)
            sender_styles: Optional dict mapping sender to their specific style
            conversation_contexts: Optional dict mapping sender to past conversation samples

        Returns:
            Path to the prompt file
        """
        prompt = """Generate draft replies for these emails.

For each email:
1. Use the SPECIFIC writing style if conversation history exists with this sender
2. Otherwise, use the DEFAULT writing style
3. Include relevant context from past conversations when available

"""

        for i, email in enumerate(emails, 1):
            sender = email['sender']

            # Determine which style to use
            if sender_styles and sender in sender_styles:
                style = sender_styles[sender]
                style_note = f"[Use SPECIFIC style for {sender}]"
            elif default_style:
                style = default_style
                style_note = "[Use DEFAULT style]"
            else:
                style = None
                style_note = "[Use professional neutral style]"

            # Add conversation context if available
            context_note = ""
            if conversation_contexts and sender in conversation_contexts:
                past_convos = conversation_contexts[sender][:2]  # Last 2 exchanges
                if past_convos:
                    context_note = "\n   Past conversation samples:\n"
                    for j, convo in enumerate(past_convos, 1):
                        context_note += f"     {j}. {convo.get('body', '')[:150]}...\n"

            # Build style instructions
            if style:
                style_instructions = f"""
   {style_note}
   - Greeting: "{style['greeting_style']}"
   - Closing: "{style['closing_style']}"
   - Formality: {style['formality_level']}
   - Tone: {style['tone_description']}
   - Common phrases: {', '.join(style['common_phrases'][:3]) if style['common_phrases'] else 'N/A'}
"""
            else:
                style_instructions = f"\n   {style_note}"

            prompt += f"""
{i}. From: {sender}
   Subject: {email['subject']}
   Body: {email.get('body', email['snippet'])[:500]}...{style_instructions}{context_note}

"""

        prompt += """
Respond with a JSON array where each object has:
{
  "email_index": <number>,
  "subject": "Re: <original subject>",
  "body": "<draft reply body>",
  "tone": "formal/casual/neutral"
}

Make each reply sound natural and consistent with the writing style specified for that sender!

Example:
```json
[
  {
    "email_index": 1,
    "subject": "Re: Meeting request",
    "body": "Hi,\\n\\nThanks for reaching out...",
    "tone": "formal"
  }
]
```
"""

        prompt_file = self.work_dir / "generate_drafts.txt"
        prompt_file.write_text(prompt)

        return str(prompt_file)

    def parse_draft_batch(
        self, response_json: str
    ) -> list[DraftReply]:
        """
        Parse Claude's batch draft generation response.

        Args:
            response_json: JSON string from Claude

        Returns:
            List of draft replies
        """
        try:
            # Extract JSON from code block if present
            if "```json" in response_json:
                start = response_json.find("```json") + 7
                end = response_json.find("```", start)
                response_json = response_json[start:end].strip()
            elif "```" in response_json:
                start = response_json.find("```") + 3
                end = response_json.find("```", start)
                response_json = response_json[start:end].strip()

            drafts = json.loads(response_json)
            return [
                {
                    "subject": d["subject"],
                    "body": d["body"],
                    "tone": d["tone"],
                }
                for d in drafts
            ]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Failed to parse drafts: {e}")
            return []

    def _default_style(self) -> WritingStyle:
        """Return default style."""
        return {
            "greeting_style": "Hello,",
            "closing_style": "Best regards,",
            "formality_level": "neutral",
            "common_phrases": [],
            "tone_description": "Professional and clear",
            "example_sentences": [],
        }
