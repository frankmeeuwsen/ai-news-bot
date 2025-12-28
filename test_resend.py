#!/usr/bin/env python3
"""Quick test script for Resend integration"""
import os
from dotenv import load_dotenv
from src.notifiers import ResendNotifier

load_dotenv()

# Test content
test_content = """
# Test Email via Resend

Dit is een test email om Resend integratie te verifiëren.

**Features:**
- Transactional email delivery
- 99%+ deliverability
- Domein verificatie voor custom sender

Als je deze email ontvangt, werkt Resend perfect!
"""

print("Testing Resend integration...")
print(f"API Key: {os.getenv('RESEND_API_KEY', 'NOT SET')[:10]}...")
print(f"From: {os.getenv('RESEND_FROM', 'NOT SET')}")
print(f"To: {os.getenv('EMAIL_TO', 'NOT SET')}")
print()

notifier = ResendNotifier()
success = notifier.send(
    content=test_content,
    subject="Test: Resend Integration",
    language="nl"
)

if success:
    print("✓ Email sent successfully via Resend!")
    print("Check your inbox at:", os.getenv('EMAIL_TO'))
else:
    print("✗ Failed to send email")
    print("Check logs above for error details")
