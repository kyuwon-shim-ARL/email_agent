"""
Claude Code-optimized email classifier - NO API COSTS!

This version is designed to run inside Claude Code sessions.
Instead of calling Claude API (which costs money), it:
1. Fetches emails from Gmail
2. Prepares prompts in text files
3. YOU copy prompts and ask Claude Code
4. You paste Claude's responses back
5. It parses responses and creates Gmail drafts

NEW FEATURES:
- Sender-specific writing styles (learns from past conversations)
- Priority ranking based on conversation frequency
- Context-aware draft generation

Perfect for daily use without API costs!
"""
import json
import sys
import re
from pathlib import Path

from .claude_code_classifier import ClaudeCodeClassifier
from .gmail_client import GmailClient


def extract_email_address(sender: str) -> str:
    """Extract clean email address from 'Name <email@domain.com>' format."""
    match = re.search(r'<(.+?)>', sender)
    return match.group(1) if match else sender


def main() -> None:
    """Run Claude Code-optimized email classifier with sender-specific features."""
    print("🔍 Email Classifier (Claude Code Edition - FREE!)")
    print("   ✨ NEW: Sender-specific styles + Priority ranking")
    print("   No API costs - runs in your Claude Code session\n")

    try:
        # Initialize clients
        print("📧 Connecting to Gmail...")
        gmail = GmailClient()

        print("🤖 Initializing Claude Code classifier...")
        classifier = ClaudeCodeClassifier()

        # === STEP 1: Default Style Learning ===
        print("\n" + "="*80)
        print("STEP 1: LEARN YOUR DEFAULT WRITING STYLE")
        print("="*80)

        print("\n✍️  Fetching your sent emails...")
        sent_emails = gmail.get_sent_emails(max_results=50)
        print(f"   → Found {len(sent_emails)} sent emails")

        default_style = None
        if sent_emails:
            style_prompt_file = classifier.prepare_style_analysis(sent_emails)
            print(f"\n✅ Default style analysis prompt ready!")
            print(f"   File: {style_prompt_file}")
            print("\n" + "="*80)
            print("ACTION REQUIRED:")
            print("="*80)
            print(f"1. Run: cat {style_prompt_file}")
            print("2. Copy the prompt")
            print("3. Paste it to Claude Code (in this conversation)")
            print("4. Copy Claude's JSON response")
            print("5. Paste it below")
            print("="*80)

            response = input("\n📋 Paste Claude's default style JSON: ").strip()

            if response:
                default_style = classifier.parse_style_analysis(response)
                print(f"\n✅ Default style learned!")
                print(f"   Greeting: {default_style['greeting_style']}")
                print(f"   Closing: {default_style['closing_style']}")
                print(f"   Formality: {default_style['formality_level']}")
            else:
                print("\n⚠️  No style provided, using defaults")
        else:
            print("\n⚠️  No sent emails found, skipping style learning")

        # === STEP 2: Fetch & Analyze Emails ===
        print("\n" + "="*80)
        print("STEP 2: FETCH EMAILS & ANALYZE CONVERSATION HISTORY")
        print("="*80)

        print("\n📬 Fetching recent emails...")
        emails = gmail.get_recent_emails(max_results=10)

        if not emails:
            print("No emails found.")
            return

        print(f"   → Found {len(emails)} emails")

        # Analyze conversation history for each sender
        print("\n🔍 Analyzing conversation history with each sender...")
        sender_histories = {}

        for email in emails:
            sender = email['sender']
            sender_email = extract_email_address(sender)

            if sender not in sender_histories:
                print(f"   Checking {sender_email}...", end=" ")
                history = gmail.get_conversation_history(sender, max_results=20)
                sender_histories[sender] = {
                    "sender_email": sender_email,
                    "total_exchanges": history['total_exchanges'],
                    "sent_to_sender": history['sent_to_sender'],
                    "received_from_sender": history['received_from_sender'],
                    "has_history": history['total_exchanges'] > 0,
                }
                print(f"{history['total_exchanges']} exchanges")

        # === STEP 3: Classify with Priority ===
        print("\n" + "="*80)
        print("STEP 3: CLASSIFY EMAILS WITH PRIORITY RANKING")
        print("="*80)

        classification_prompt_file = classifier.prepare_classification_batch(
            emails,
            sender_histories
        )

        print(f"\n✅ Classification prompt ready (with conversation history)!")
        print(f"   File: {classification_prompt_file}")
        print("\n" + "="*80)
        print("ACTION REQUIRED:")
        print("="*80)
        print(f"1. Run: cat {classification_prompt_file}")
        print("2. Copy the prompt")
        print("3. Paste it to Claude Code")
        print("4. Copy Claude's JSON array response")
        print("5. Paste it below")
        print("="*80)

        response = input("\n📋 Paste Claude's classification JSON: ").strip()

        if not response:
            print("\n❌ No classification provided, exiting")
            return

        classifications = classifier.parse_classification_batch(response)

        if len(classifications) != len(emails):
            print(f"\n⚠️  Warning: Got {len(classifications)} results for {len(emails)} emails")

        # Attach classifications to emails
        for email, classification in zip(emails, classifications):
            email['classification'] = classification

        # === STEP 4: Learn Sender-Specific Styles ===
        print("\n" + "="*80)
        print("STEP 4: LEARN SENDER-SPECIFIC WRITING STYLES")
        print("="*80)

        emails_needing_response = [e for e in emails if e.get('classification', {}).get('requires_response')]

        if not emails_needing_response:
            print("\n✅ No emails need responses!")
            print("\n" + "="*80)
            print("RESULTS SUMMARY")
            print("="*80)
            _display_results(emails)
            return

        print(f"\n📝 {len(emails_needing_response)} emails need responses")
        print("\nLearning sender-specific styles for frequent contacts...")

        sender_styles = {}
        for email in emails_needing_response:
            sender = email['sender']
            history = sender_histories.get(sender)

            if history and history['total_exchanges'] >= 3:
                # Enough history to learn sender-specific style
                sender_email = extract_email_address(sender)
                print(f"   Learning style for {sender_email}...", end=" ")

                style_prompt_file = classifier.prepare_style_analysis(
                    sent_emails,
                    specific_recipient=sender_email
                )

                print(f"prompt ready")
                print(f"   File: {style_prompt_file}")
                print("\n" + "="*80)
                print(f"ACTION: Analyze style for {sender_email}")
                print("="*80)
                print(f"1. Run: cat {style_prompt_file}")
                print("2. Copy the prompt")
                print("3. Paste it to Claude Code")
                print("4. Copy Claude's JSON response")
                print("5. Paste it below (or press Enter to skip)")
                print("="*80)

                response = input(f"\n📋 Paste style JSON for {sender_email}: ").strip()

                if response:
                    sender_styles[sender] = classifier.parse_style_analysis(response)
                    print(f"   ✅ Learned specific style for {sender_email}")
                else:
                    print(f"   ⚠️  Skipped, will use default style")
            else:
                # Not enough history, use default
                print(f"   Using default style for {extract_email_address(sender)} (limited history)")

        # === STEP 5: Generate Drafts ===
        print("\n" + "="*80)
        print("STEP 5: GENERATE PERSONALIZED DRAFT REPLIES")
        print("="*80)

        # Prepare conversation contexts
        conversation_contexts = {}
        for email in emails_needing_response:
            sender = email['sender']
            history = sender_histories.get(sender)
            if history and history['sent_to_sender']:
                conversation_contexts[sender] = history['sent_to_sender']

        draft_prompt_file = classifier.prepare_draft_batch(
            emails_needing_response,
            default_style=default_style,
            sender_styles=sender_styles,
            conversation_contexts=conversation_contexts
        )

        print(f"\n✅ Draft generation prompt ready!")
        print(f"   File: {draft_prompt_file}")
        print("\n" + "="*80)
        print("ACTION REQUIRED:")
        print("="*80)
        print(f"1. Run: cat {draft_prompt_file}")
        print("2. Copy the prompt")
        print("3. Paste it to Claude Code")
        print("4. Copy Claude's JSON array response")
        print("5. Paste it below")
        print("="*80)

        response = input("\n📋 Paste Claude's draft JSON: ").strip()

        if not response:
            print("\n⚠️  No drafts provided, skipping draft creation")
            drafts = []
        else:
            drafts = classifier.parse_draft_batch(response)

            # Create drafts in Gmail
            drafts_created = 0
            for email, draft in zip(emails_needing_response, drafts):
                try:
                    gmail.create_draft(
                        thread_id=email["thread_id"],
                        to=email["sender"],
                        subject=draft["subject"],
                        body=draft["body"],
                    )
                    drafts_created += 1
                    print(f"   ✅ Draft created for: {email['subject'][:50]}...")
                except Exception as e:
                    print(f"   ⚠️  Failed to create draft: {e}")

            print(f"\n📝 Created {drafts_created} drafts in Gmail!")

        # === STEP 6: Display Results ===
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)

        _display_results(emails)

        if emails_needing_response:
            print(f"\n📝 Check your Gmail Drafts folder to review and send replies!")
            print("   → https://mail.google.com/mail/#drafts")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nSetup instructions:")
        print("1. Get credentials.json from Google Cloud Console")
        print("2. See docs/SETUP_CREDENTIALS.md for help")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _display_results(emails: list[dict]) -> None:
    """Display classification results sorted by priority."""
    needs_response = [e for e in emails if e.get('classification', {}).get('requires_response')]
    no_response = [e for e in emails if not e.get('classification', {}).get('requires_response')]

    # Sort by priority (highest first)
    needs_response.sort(key=lambda e: e.get('classification', {}).get('priority', 0), reverse=True)

    print(f"\n🔴 NEEDS RESPONSE ({len(needs_response)} emails)")
    print("=" * 80)

    for i, email in enumerate(needs_response, 1):
        classification = email.get('classification', {})
        priority = classification.get('priority', 3)
        priority_indicator = "🔥" * priority

        print(f"\n{i}. [{priority_indicator} Priority {priority}] {email['subject']}")
        print(f"   From: {email['sender']}")
        print(f"   Confidence: {classification.get('confidence', 0):.0%}")
        print(f"   Reason: {classification.get('reason', 'N/A')}")

    print(f"\n\n✅ NO RESPONSE NEEDED ({len(no_response)} emails)")
    print("=" * 80)

    for i, email in enumerate(no_response, 1):
        classification = email.get('classification', {})
        print(f"\n{i}. {email['subject']}")
        print(f"   From: {email['sender']}")
        print(f"   Confidence: {classification.get('confidence', 0):.0%}")
        print(f"   Reason: {classification.get('reason', 'N/A')}")

    print("\n" + "=" * 80)
    print("✨ Classification complete!")


if __name__ == "__main__":
    main()
