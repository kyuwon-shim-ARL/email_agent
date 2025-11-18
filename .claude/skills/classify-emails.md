# Email Classifier Skill

Automatically classify Gmail emails and generate draft replies.

## What this skill does

1. Fetches recent emails from Gmail
2. Analyzes user's writing style from sent emails
3. Classifies which emails need responses
4. Generates personalized draft replies
5. Saves drafts to Gmail drafts folder

## Prerequisites

- credentials.json in project root (from Google Cloud Console)
- Gmail API enabled with scopes: gmail.readonly, gmail.compose

## Usage

User can say:
- "Classify my emails"
- "Check my recent emails and create drafts"
- "Process 20 emails and generate replies"

## Implementation

When this skill is invoked:

1. **Fetch sent emails for style learning**
   ```python
   from email_classifier.gmail_client import GmailClient
   gmail = GmailClient()
   sent_emails = gmail.get_sent_emails(max_results=30)
   ```

2. **Analyze writing style**
   - Extract greeting style (e.g., "Hi," vs "안녕하세요,")
   - Extract closing style (e.g., "Best," vs "감사합니다,")
   - Determine formality level (formal/casual/neutral)
   - Identify common phrases
   - Capture tone and example sentences

   Ask user for analysis:
   ```
   I have 30 of your sent emails. Let me analyze your writing style.

   [Provide email corpus]

   Please analyze and extract:
   - Greeting style
   - Closing style
   - Formality level
   - Common phrases (5-7)
   - Tone description
   - Example sentences (3-4)
   ```

3. **Fetch recent emails**
   ```python
   emails = gmail.get_recent_emails(max_results=10)
   ```

4. **Classify emails**
   For each email, determine:
   - Does it require a response? (YES/NO)
   - Confidence level (0.0-1.0)
   - Reason for classification

   Guidelines:
   - Newsletters, notifications, automated messages → NO response
   - Direct questions, meeting requests, personal messages → Response needed
   - Consider sender relationship and urgency

5. **Generate draft replies**
   For emails requiring responses:
   - Use learned writing style
   - Include relevant context from original email
   - Match user's tone and formality
   - Format as proper reply with "Re:" subject

6. **Save drafts to Gmail**
   ```python
   gmail.create_draft(
       thread_id=email["thread_id"],
       to=email["sender"],
       subject=draft["subject"],
       body=draft["body"]
   )
   ```

7. **Report results**
   Display:
   - Number of emails processed
   - Number needing responses
   - Number of drafts created
   - Summary of each email with classification

## Output Format

```
📧 EMAIL CLASSIFICATION RESULTS
================================

Analyzed: 10 emails
Writing Style: casual, friendly tone

🔴 NEEDS RESPONSE (3 emails)
----------------------------
1. "Meeting request for next week"
   From: manager@company.com
   Confidence: 95%
   Reason: Direct question requiring response
   ✅ Draft created

2. "Project update needed"
   From: team@company.com
   Confidence: 85%
   Reason: Action item requested
   ✅ Draft created

✅ NO RESPONSE NEEDED (7 emails)
--------------------------------
1. "GitHub Notification: PR merged"
   From: notifications@github.com
   Confidence: 99%
   Reason: Automated notification

[...]

📝 Created 3 draft replies in Gmail!
   → Check your Gmail Drafts folder to review and send them.
```

## Error Handling

- If credentials.json missing → Provide setup instructions
- If OAuth fails → Guide user through authentication
- If Gmail API error → Display error and suggest retry
- If no sent emails → Use default neutral style

## Notes

- **NO API COSTS**: All AI processing happens in Claude Code session
- First run requires OAuth authentication (browser opens)
- Subsequent runs use cached token
- Drafts are never sent automatically - always require user review
