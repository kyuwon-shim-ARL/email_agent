"""Email classifier using interactive prompts."""
from typing import TypedDict


class ClassificationResult(TypedDict):
    """Classification result."""

    requires_response: bool
    confidence: float
    reason: str


class DraftReply(TypedDict):
    """Draft reply."""

    subject: str
    body: str
    tone: str


class EmailClassifier:
    """Classify emails interactively."""

    def __init__(self) -> None:
        """Initialize classifier."""
        pass

    def classify_email(
        self, subject: str, sender: str, snippet: str
    ) -> ClassificationResult:
        """
        Classify if email requires response.

        Args:
            subject: Email subject
            sender: Email sender
            snippet: Email preview text

        Returns:
            Classification result with requires_response flag
        """
        prompt = f"""Analyze this email and determine if it requires a response.

Subject: {subject}
From: {sender}
Preview: {snippet}

Guidelines:
- Newsletters, notifications, automated messages → NO response needed
- Direct questions, meeting requests, personal messages → Response needed
- Consider sender relationship and urgency

Respond in this exact format:
REQUIRES_RESPONSE: [YES/NO]
CONFIDENCE: [0.0-1.0]
REASON: [brief explanation]"""

        print(f"\n{'='*80}")
        print(f"📧 EMAIL TO CLASSIFY:")
        print(f"{'='*80}")
        print(prompt)
        print(f"{'='*80}")

        response_text = input("\n✍️  Please classify this email (paste Claude's response): ").strip()

        if not response_text:
            print("❌ No response provided, using defaults")
            return {
                "requires_response": False,
                "confidence": 0.5,
                "reason": "No classification provided",
            }

        # Parse response
        lines = response_text.strip().split("\n")

        requires_response = False
        confidence = 0.5
        reason = "Unable to parse"

        for line in lines:
            if line.startswith("REQUIRES_RESPONSE:"):
                requires_response = "YES" in line.upper()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    confidence = 0.5
            elif line.startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        return {
            "requires_response": requires_response,
            "confidence": confidence,
            "reason": reason,
        }

    def generate_draft_reply(
        self,
        original_subject: str,
        original_sender: str,
        original_body: str,
        user_style: dict | None = None,
    ) -> DraftReply:
        """
        Generate a draft reply using Claude AI.

        Args:
            original_subject: Original email subject
            original_sender: Original email sender
            original_body: Original email body text
            user_style: User's writing style profile (optional)

        Returns:
            Draft reply with subject and body
        """
        # Build style instructions
        style_instructions = ""
        if user_style:
            style_instructions = f"""

IMPORTANT - Match the user's writing style:
- Start with: "{user_style.get('greeting_style', 'Hello,')}"
- End with: "{user_style.get('closing_style', 'Best regards,')}"
- Formality level: {user_style.get('formality_level', 'neutral')}
- Tone: {user_style.get('tone_description', 'Professional')}
- Common phrases to use: {', '.join(user_style.get('common_phrases', [])[:3])}
- Sentence style: Mirror these patterns: {'; '.join(user_style.get('example_sentences', [])[:2])}

The reply should sound like the user wrote it themselves."""

        prompt = f"""You are helping write a personalized email reply.

Original Email:
From: {original_sender}
Subject: {original_subject}

Body:
{original_body}

---
{style_instructions}

Write a reply that:
1. Addresses the main points or questions
2. Is concise but complete
3. Sounds natural and authentic to the user's style
4. Includes proper greeting and closing

Respond in this exact format:
SUBJECT: [reply subject with Re: prefix]
TONE: [formal/casual/neutral]
BODY:
[draft email body matching user's style]"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = message.content[0].text
        lines = response_text.split("\n")

        subject = f"Re: {original_subject}"
        tone = "neutral"
        body = ""
        body_started = False

        for line in lines:
            if line.startswith("SUBJECT:"):
                subject = line.split(":", 1)[1].strip()
            elif line.startswith("TONE:"):
                tone = line.split(":", 1)[1].strip().lower()
            elif line.startswith("BODY:"):
                body_started = True
            elif body_started:
                body += line + "\n"

        return {
            "subject": subject,
            "body": body.strip(),
            "tone": tone,
        }
