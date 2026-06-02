"""
Simple test script to check if Gmail SMTP is working.
Run this from the project directory:
    python test_email.py
"""
import smtplib
from email.mime.text import MIMEText

EMAIL = 'krishparashar609@gmail.com'
PASSWORD = 'gjuf apgx urjq wgsg'

print("Testing Gmail SMTP connection...")
print(f"Email: {EMAIL}")
print(f"Password length: {len(PASSWORD)} characters")

try:
    print("\n1. Connecting to smtp.gmail.com:587...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    print("   Connected!")
    
    print("2. Starting TLS...")
    server.starttls()
    print("   TLS started!")
    
    print("3. Logging in...")
    server.login(EMAIL, PASSWORD)
    print("   Login successful!")
    
    print("4. Sending test email to yourself...")
    msg = MIMEText("This is a test email from your Flight Booking website. If you received this, email is working!")
    msg['Subject'] = 'Flight Website - Test Email'
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    
    server.sendmail(EMAIL, EMAIL, msg.as_string())
    print("   Email sent!")
    
    server.quit()
    print("\n SUCCESS! Check your Gmail inbox for the test email.")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n AUTHENTICATION FAILED!")
    print(f"   Error: {e}")
    print(f"\n   Your App Password might be wrong.")
    print(f"   Go to https://myaccount.google.com/apppasswords and generate a new one.")
    
except Exception as e:
    print(f"\n ERROR: {type(e).__name__}: {e}")
