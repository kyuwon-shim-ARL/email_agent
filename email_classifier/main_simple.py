"""Simple CLI without style learning (for testing comparison)."""
import sys

from .classifier import EmailClassifier
from .gmail_client import GmailClient


def main_simple() -> None:
    """Run email classifier without style learning."""
    print("🔍 Simple Email Classifier (Without Style Learning)\n")

    try:
        # Initialize clients
        print("📧 Connecting to Gmail...")
        gmail = GmailClient()

        print("🤖 Connecting to Claude AI...")
        classifier = EmailClassifier()

        # Get recent emails
        print("\n📬 Fetching recent emails...\n")
        emails = gmail.get_recent_emails(max_results=10)

        if not emails:
            print("No emails found.")
            return

        # Classify each email and generate drafts (without style)
        needs_response = []
        no_response = []
        drafts_created = 0

        print("🤖 Analyzing emails and generating draft replies...\n")

        for i, email in enumerate(emails, 1):
            print(f"  [{i}/{len(emails)}] {email['subject'][:50]}...")

            result = classifier.classify_email(
                subject=email["subject"],
                sender=email["sender"],
                snippet=email["snippet"],
            )

            email_info = {
                "subject": email["subject"],
                "sender": email["sender"],
                "confidence": result["confidence"],
                "reason": result["reason"],
            }

            if result["requires_response"]:
                # Generate draft reply WITHOUT user style
                try:
                    draft = classifier.generate_draft_reply(
                        original_subject=email["subject"],
                        original_sender=email["sender"],
                        original_body=email["body"] or email["snippet"],
                        user_style=None,  # No style learning
                    )

                    # Save draft to Gmail
                    gmail.create_draft(
                        thread_id=email["thread_id"],
                        to=email["sender"],
                        subject=draft["subject"],
                        body=draft["body"],
                    )

                    email_info["draft_created"] = True
                    email_info["draft_tone"] = draft["tone"]
                    drafts_created += 1

                except Exception as e:
                    print(f"    ⚠️  Draft creation failed: {e}")
                    email_info["draft_created"] = False

                needs_response.append(email_info)
            else:
                no_response.append(email_info)

        print()

        # Print results
        print("=" * 80)
        print(f"🔴 NEEDS RESPONSE ({len(needs_response)} emails)")
        print("=" * 80)
        for i, email in enumerate(needs_response, 1):
            print(f"\n{i}. {email['subject']}")
            print(f"   From: {email['sender']}")
            print(f"   Confidence: {email['confidence']:.0%}")
            print(f"   Reason: {email['reason']}")
            if email.get("draft_created"):
                print(f"   ✅ Draft reply created (tone: {email.get('draft_tone', 'neutral')})")
            else:
                print("   ⚠️  Draft creation failed")

        print("\n" + "=" * 80)
        print(f"✅ NO RESPONSE NEEDED ({len(no_response)} emails)")
        print("=" * 80)
        for i, email in enumerate(no_response, 1):
            print(f"\n{i}. {email['subject']}")
            print(f"   From: {email['sender']}")
            print(f"   Confidence: {email['confidence']:.0%}")
            print(f"   Reason: {email['reason']}")

        print("\n" + "=" * 80)
        print("✨ Classification complete!")
        print(f"\n📝 Created {drafts_created} draft replies in Gmail!")
        print("   (Generic style - no personalization)")
        if drafts_created > 0:
            print("   → Check your Gmail Drafts folder to review and send them.")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nSetup instructions:")
        print("1. Get credentials.json from Google Cloud Console")
        print("2. Create .env file with CLAUDE_API_KEY")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main_simple()
