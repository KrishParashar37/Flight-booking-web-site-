import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
django.setup()

from flight.models import Ticket
from capstone.utils import generate_ticket_pdf

ticket = Ticket.objects.last()
print(f"Testing PDF generation for Ticket Ref: {ticket.ref_no}")

try:
    pdf_bytes = generate_ticket_pdf(ticket)
    if pdf_bytes:
        with open('test_ticket.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print("✅ PDF generated successfully and saved to test_ticket.pdf")
    else:
        print("❌ PDF generation returned None.")
except Exception as e:
    print("❌ PDF generation failed with exception:")
    traceback.print_exc()
