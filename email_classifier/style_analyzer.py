"""Analyze user's writing style from sent emails."""
from typing import TypedDict

from anthropic import Anthropic


class WritingStyle(TypedDict):
    """User's writing style profile."""

    greeting_style: str  # e.g., "Hi,", "Hello,", "안녕하세요,"
    closing_style: str  # e.g., "Best,", "Thanks,", "감사합니다,"
    formality_level: str  # formal, casual, neutral
    common_phrases: list[str]  # frequently used expressions
    tone_description: str  # overall tone
    example_sentences: list[str]  # typical sentence patterns


class StyleAnalyzer:
    """Analyze writing style from user's sent emails."""

    def __init__(self, anthropic_client: Anthropic) -> None:
        """Initialize style analyzer."""
        self.client = anthropic_client

    def analyze_writing_style(self, sent_emails: list[dict]) -> WritingStyle:
        """
        Analyze user's writing style from sent emails.

        Args:
            sent_emails: List of sent email dictionaries with 'subject' and 'body'

        Returns:
            WritingStyle profile extracted from the emails
        """
        if not sent_emails:
            return self._default_style()

        # Prepare email corpus for analysis
        email_samples = []
        for i, email in enumerate(sent_emails[:20], 1):  # Analyze up to 20 recent emails
            email_samples.append(
                f"Email {i}:\nSubject: {email.get('subject', 'N/A')}\n"
                f"Body:\n{email.get('body', 'N/A')[:500]}...\n"
            )

        corpus = "\n---\n".join(email_samples)

        prompt = f"""Analyze the writing style from these sent emails and extract patterns.

Email Corpus:
{corpus}

Extract and summarize:
1. GREETING_STYLE: How does the person typically start emails? (exact phrases)
2. CLOSING_STYLE: How do they typically end emails? (exact phrases)
3. FORMALITY_LEVEL: formal / casual / neutral
4. COMMON_PHRASES: List 5-7 phrases they frequently use
5. TONE_DESCRIPTION: Overall tone in 1-2 sentences
6. EXAMPLE_SENTENCES: 3-4 typical sentence structures they use

Respond in this exact format:
GREETING_STYLE: [typical greeting]
CLOSING_STYLE: [typical closing]
FORMALITY_LEVEL: [formal/casual/neutral]
COMMON_PHRASES:
- [phrase 1]
- [phrase 2]
- [phrase 3]
TONE_DESCRIPTION: [description]
EXAMPLE_SENTENCES:
- [sentence 1]
- [sentence 2]
- [sentence 3]"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = message.content[0].text
        return self._parse_style_response(response_text)

    def _parse_style_response(self, response: str) -> WritingStyle:
        """Parse Claude's style analysis response."""
        lines = response.split("\n")

        greeting = "Hello,"
        closing = "Best regards,"
        formality = "neutral"
        phrases = []
        tone = "Professional and clear"
        examples = []

        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("GREETING_STYLE:"):
                greeting = line.split(":", 1)[1].strip()
            elif line.startswith("CLOSING_STYLE:"):
                closing = line.split(":", 1)[1].strip()
            elif line.startswith("FORMALITY_LEVEL:"):
                formality = line.split(":", 1)[1].strip().lower()
            elif line.startswith("COMMON_PHRASES:"):
                current_section = "phrases"
            elif line.startswith("TONE_DESCRIPTION:"):
                tone = line.split(":", 1)[1].strip()
                current_section = None
            elif line.startswith("EXAMPLE_SENTENCES:"):
                current_section = "examples"
            elif line.startswith("- ") and current_section == "phrases":
                phrases.append(line[2:].strip())
            elif line.startswith("- ") and current_section == "examples":
                examples.append(line[2:].strip())

        return {
            "greeting_style": greeting,
            "closing_style": closing,
            "formality_level": formality,
            "common_phrases": phrases,
            "tone_description": tone,
            "example_sentences": examples,
        }

    def _default_style(self) -> WritingStyle:
        """Return default style if no sent emails available."""
        return {
            "greeting_style": "Hello,",
            "closing_style": "Best regards,",
            "formality_level": "neutral",
            "common_phrases": [],
            "tone_description": "Professional and clear",
            "example_sentences": [],
        }
