import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
django.setup()

from flight.models import Ticket
from capstone.utils import send_email_notification, send_whatsapp_notification

print("Testing Django Notification System...")

# Get the latest ticket
ticket = Ticket.objects.last()
if not ticket:
    print("No tickets found in the database. Please book a ticket first.")
else:
    print(f"Testing with Ticket Ref: {ticket.ref_no}")
    print(f"Ticket Email: {ticket.email}")
    print(f"Ticket Mobile: {ticket.mobile}")
    
    # Force the email to be the one provided by user for testing
    ticket.email = 'krishparashar609@gmail.com'
    ticket.mobile = '+918435679136'
    
    print("\n1. Testing Email Generation & Sending...")
    email_success = send_email_notification(ticket)
    if email_success:
        print("✅ Email test completed successfully!")
    else:
        print("❌ Email test failed!")
        
    print("\n2. Testing WhatsApp sending...")
    whatsapp_success = send_whatsapp_notification(ticket)
    if whatsapp_success:
        print("✅ WhatsApp test completed successfully!")
    else:
        print("❌ WhatsApp test failed (expected if Twilio is not setup).")
