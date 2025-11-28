"""
Claude Code email classifier with Google Sheets integration.

New Features:
- Google Sheets tracking for all emails
- Improved priority system (발신 가중치 + 첫 연락)
- Batch sending from spreadsheet
- Status management (답장필요/불필요/완료)
"""
import sys
import re
from datetime import datetime

from .claude_code_classifier import ClaudeCodeClassifier
from .gmail_client import GmailClient
from .sheets_client import SheetsClient


def extract_email_address(sender: str) -> str:
    """Extract clean email address from 'Name <email@domain.com>' format."""
    match = re.search(r'<(.+?)>', sender)
    return match.group(1) if match else sender


def main() -> None:
    """Run email classifier with Sheets integration."""
    print("🔍 Email Classifier with Google Sheets Integration")
    print("   ✨ Features: Priority ranking + Sheets tracking + Batch sending")
    print("   💰 No API costs - runs in Claude Code\n")

    try:
        # Initialize clients
        print("📧 Connecting to Gmail...")
        gmail = GmailClient()

        print("📊 Connecting to Google Sheets...")
        sheets = SheetsClient()

        print("🤖 Initializing classifier...")
        classifier = ClaudeCodeClassifier()

        # Create or get spreadsheet
        print("\n" + "="*80)
        print("SPREADSHEET SETUP")
        print("="*80)

        spreadsheet_id = input("\n📋 Enter existing Spreadsheet ID (or press Enter to create new): ").strip()

        if not spreadsheet_id:
            print("\nCreating new spreadsheet...")
            spreadsheet_id = sheets.create_email_tracker(
                title=f"Email Tracker - {datetime.now().strftime('%Y-%m-%d')}"
            )
            print(f"✅ Created spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        else:
            print(f"✅ Using spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

        # === STEP 1: Style Learning ===
        print("\n" + "="*80)
        print("STEP 1: LEARN YOUR WRITING STYLE")
        print("="*80)

        print("\n✍️  Fetching your sent emails...")
        sent_emails = gmail.get_sent_emails(max_results=50)
        print(f"   → Found {len(sent_emails)} sent emails")

        default_style = None
        if sent_emails:
            style_prompt_file = classifier.prepare_style_analysis(sent_emails)
            print(f"\n✅ Style prompt: {style_prompt_file}")
            print("   Run: cat", style_prompt_file)

            response = input("\n📋 Paste Claude's style JSON: ").strip()
            if response:
                default_style = classifier.parse_style_analysis(response)
                print(f"✅ Style learned: {default_style['formality_level']}")

        # === STEP 2: Fetch & Analyze ===
        print("\n" + "="*80)
        print("STEP 2: FETCH EMAILS & ANALYZE HISTORY")
        print("="*80)

        print("\n📬 Fetching recent emails...")
        emails = gmail.get_recent_emails(max_results=20)
        print(f"   → Found {len(emails)} emails")

        # Analyze conversation history
        print("\n🔍 Analyzing conversation history...")
        sender_histories = {}

        for email in emails:
            sender = email['sender']

            if sender not in sender_histories:
                sender_email = extract_email_address(sender)
                print(f"   {sender_email}...", end=" ")

                history = gmail.get_conversation_history(sender, max_results=20)
                sender_histories[sender] = history

                # Display priority hints
                if history['is_first_contact']:
                    print("✨ FIRST CONTACT")
                elif history['total_sent'] > 10:
                    print(f"🔥 VIP (sent: {history['total_sent']})")
                elif history['total_exchanges'] > 10:
                    print(f"📧 Frequent ({history['total_exchanges']} exchanges)")
                else:
                    print(f"{history['total_exchanges']} exchanges")

        # === STEP 3: Classify with Enhanced Priority ===
        print("\n" + "="*80)
        print("STEP 3: CLASSIFY EMAILS (ENHANCED PRIORITY)")
        print("="*80)

        classification_prompt_file = classifier.prepare_classification_batch(
            emails, sender_histories
        )

        print(f"\n✅ Classification prompt: {classification_prompt_file}")
        print("   Run: cat", classification_prompt_file)

        response = input("\n📋 Paste Claude's classification JSON: ").strip()
        if not response:
            print("❌ No classification, exiting")
            return

        classifications = classifier.parse_classification_batch(response)

        # Attach classifications
        for email, classification in zip(emails, classifications):
            email['classification'] = classification

        # === STEP 4: Update Spreadsheet ===
        print("\n" + "="*80)
        print("STEP 4: UPDATE GOOGLE SHEETS")
        print("="*80)

        print("\n📊 Adding emails to spreadsheet...")

        for email in emails:
            classification = email.get('classification', {})
            status = "needs_response" if classification.get('requires_response') else "no_response"

            email_data = {
                "status": status,
                "priority": classification.get('priority', 3),
                "subject": email.get('subject', ''),
                "sender": email.get('sender', ''),
                "to": "me",  # 받은 메일이므로
                "cc": "",
                "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "body": email.get('body', email.get('snippet', '')),
                "draft_body": "",  # 아직 생성 안 됨
                "draft_to": "",
                "draft_cc": "",
                "thread_id": email.get('thread_id', ''),
            }

            sheets.add_email_row(spreadsheet_id, email_data)

        print(f"✅ Added {len(emails)} emails to spreadsheet")

        # === STEP 5: Generate Drafts ===
        emails_needing_response = [e for e in emails if e.get('classification', {}).get('requires_response')]

        if not emails_needing_response:
            print("\n✅ No emails need responses!")
            _display_results(emails)
            return

        print("\n" + "="*80)
        print(f"STEP 5: GENERATE DRAFTS ({len(emails_needing_response)} emails)")
        print("="*80)

        # Learn sender-specific styles
        sender_styles = {}
        for email in emails_needing_response:
            sender = email['sender']
            history = sender_histories.get(sender, {})

            if history.get('total_exchanges', 0) >= 3:
                # 생략 가능 (기존과 동일)
                pass

        # Prepare conversation contexts
        conversation_contexts = {}
        for email in emails_needing_response:
            sender = email['sender']
            history = sender_histories.get(sender, {})
            if history.get('sent_to_sender'):
                conversation_contexts[sender] = history['sent_to_sender']

        draft_prompt_file = classifier.prepare_draft_batch(
            emails_needing_response,
            default_style=default_style,
            sender_styles=sender_styles,
            conversation_contexts=conversation_contexts
        )

        print(f"\n✅ Draft prompt: {draft_prompt_file}")
        print("   Run: cat", draft_prompt_file)

        response = input("\n📋 Paste Claude's draft JSON: ").strip()
        if not response:
            print("⚠️  Skipping drafts")
            drafts = []
        else:
            drafts = classifier.parse_draft_batch(response)

            # Create drafts & update spreadsheet
            for email, draft in zip(emails_needing_response, drafts):
                # Create Gmail draft
                try:
                    gmail.create_draft(
                        thread_id=email["thread_id"],
                        to=email["sender"],
                        subject=draft["subject"],
                        body=draft["body"],
                    )
                    print(f"   ✅ Draft: {email['subject'][:50]}...")
                except Exception as e:
                    print(f"   ⚠️  Failed: {e}")

                # Update spreadsheet with draft
                # (여기서는 간단히 생략, 실제로는 find & update 필요)

        # === STEP 6: Batch Send (Optional) ===
        print("\n" + "="*80)
        print("STEP 6: BATCH SEND FROM SPREADSHEET (OPTIONAL)")
        print("="*80)

        send_choice = input("\n📧 Send emails marked in spreadsheet? (y/N): ").strip().lower()

        if send_choice == 'y':
            print("\n🔍 Checking spreadsheet for emails to send...")
            emails_to_send = sheets.get_emails_to_send(spreadsheet_id)

            if not emails_to_send:
                print("   No emails marked for sending")
            else:
                print(f"   Found {len(emails_to_send)} emails marked for sending")

                confirm = input(f"\n⚠️  Send {len(emails_to_send)} emails? (yes/no): ").strip().lower()

                if confirm == 'yes':
                    print("\n📤 Sending emails...")

                    send_data = [
                        {
                            "to": email['draft_to'] or email['sender'],
                            "subject": email['subject'],
                            "body": email['draft_body'],
                            "cc": email.get('draft_cc'),
                            "thread_id": email.get('thread_id'),
                        }
                        for email in emails_to_send
                    ]

                    results = gmail.batch_send_emails(send_data)

                    # Update spreadsheet status
                    for result, email in zip(results, emails_to_send):
                        if result['success']:
                            sheets.update_email_status(
                                spreadsheet_id,
                                email['row_number'],
                                "답장완료"
                            )
                            print(f"   ✅ Sent: {email['subject'][:50]}...")
                        else:
                            print(f"   ❌ Failed: {email['subject'][:50]}... - {result['error']}")

                    success_count = sum(1 for r in results if r['success'])
                    print(f"\n📧 Sent {success_count}/{len(results)} emails")

        # === STEP 7: Results ===
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)

        _display_results(emails)

        print(f"\n📊 Spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        print("   → Review, edit drafts, and mark emails for batch sending")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _display_results(emails: list[dict]) -> None:
    """Display classification results sorted by priority."""
    needs_response = [e for e in emails if e.get('classification', {}).get('requires_response')]
    no_response = [e for e in emails if not e.get('classification', {}).get('requires_response')]

    # Sort by priority
    needs_response.sort(key=lambda e: e.get('classification', {}).get('priority', 0), reverse=True)

    print(f"\n🔴 NEEDS RESPONSE ({len(needs_response)} emails)")
    print("=" * 80)

    for i, email in enumerate(needs_response, 1):
        classification = email.get('classification', {})
        priority = classification.get('priority', 3)
        priority_indicator = "🔥" * priority

        print(f"\n{i}. [{priority_indicator} P{priority}] {email['subject']}")
        print(f"   From: {email['sender']}")
        print(f"   Reason: {classification.get('reason', 'N/A')}")

    print(f"\n\n✅ NO RESPONSE ({len(no_response)} emails)")
    print("=" * 80)

    for i, email in enumerate(no_response, 1):
        classification = email.get('classification', {})
        priority = classification.get('priority', 1)
        print(f"\n{i}. [P{priority}] {email['subject']}")
        print(f"   From: {email['sender']}")


if __name__ == "__main__":
    main()
