from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

from flight.models import *
import secrets
from datetime import datetime, timedelta

from flight.constant import FEE

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from django.conf import settings
from django.template.loader import render_to_string

import requests
import os


def generate_ticket_pdf(ticket):
    """Generate a PDF ticket using fpdf2"""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(225, 35, 35)
        pdf.cell(95, 15, "FLIGHT", ln=False)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(95, 15, "E-Ticket", ln=True, align="R")

        pdf.set_draw_color(128, 128, 128)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # Important Information
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 8, "Important Information", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(190, 5, text="- This is your E-Ticket. You must bring it to the airport for check-in.")
        pdf.multi_cell(190, 5, text="- Each passenger needs a printed copy for immigration and security checks.")
        pdf.multi_cell(190, 5, text="- Report to check-in 3 hours before departure (Economy) / 1 hour (Business/First).")
        pdf.ln(5)

        # Ticket Information Section
        pdf.set_fill_color(169, 169, 169)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 8, "  TICKET INFORMATION", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)

        # Row 1
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(45, 7, "TICKET REFERENCE:", border=0)
        pdf.cell(45, 7, str(ticket.ref_no).upper(), border=0)
        pdf.cell(45, 7, "BOOKING DATE:", border=0)
        booking_date_str = ticket.booking_date.strftime("%d %b %Y %H:%M") if ticket.booking_date else "N/A"
        pdf.cell(45, 7, booking_date_str, border=0, ln=True)

        # Row 2
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(45, 7, "FLIGHT DATE:", border=0, fill=True)
        flight_date_str = ticket.flight_ddate.strftime("%d %b %Y") if ticket.flight_ddate else "N/A"
        pdf.cell(45, 7, flight_date_str, border=0, fill=True)
        pdf.cell(45, 7, "CLASS:", border=0, fill=True)
        pdf.cell(45, 7, str(ticket.seat_class).upper(), border=0, fill=True, ln=True)

        # Row 3
        pdf.cell(45, 7, "EMAIL:", border=0)
        pdf.cell(45, 7, str(ticket.email), border=0)
        pdf.cell(45, 7, "MOBILE:", border=0)
        pdf.cell(45, 7, str(ticket.mobile), border=0, ln=True)

        # Row 4
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(45, 7, "STATUS:", border=0, fill=True)
        pdf.cell(135, 7, str(ticket.status).upper(), border=0, fill=True, ln=True)
        pdf.ln(5)

        # Passenger Information
        pdf.set_fill_color(169, 169, 169)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 8, "  PASSENGER INFORMATION", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(15, 7, "S NO.", border=0)
        pdf.cell(75, 7, "PASSENGER NAME", border=0)
        pdf.cell(30, 7, "SEX", border=0)
        pdf.cell(60, 7, "CLASS", border=0, ln=True)
        pdf.set_font("Helvetica", "", 10)

        for i, passenger in enumerate(ticket.passengers.all(), 1):
            fill = (i % 2 == 0)
            if fill:
                pdf.set_fill_color(240, 240, 240)
            pdf.cell(15, 7, str(i), border=0, fill=fill)
            pdf.cell(75, 7, f"{passenger.last_name.upper()}/{passenger.first_name.upper()}", border=0, fill=fill)
            pdf.cell(30, 7, str(passenger.gender).upper(), border=0, fill=fill)
            pdf.cell(60, 7, str(ticket.seat_class).upper(), border=0, fill=fill, ln=True)
        pdf.ln(5)

        # Flight Information
        pdf.set_fill_color(169, 169, 169)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 8, "  FLIGHT INFORMATION", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)

        pdf.cell(50, 7, f"{ticket.flight.airline.upper()}", border=0)
        depart_str = ticket.flight_ddate.strftime("%d %b %Y") if ticket.flight_ddate else "N/A"
        pdf.cell(50, 7, f"Depart: {depart_str}", border=0)
        pdf.cell(80, 7, f"{ticket.flight.origin.airport.upper()} ({ticket.flight.origin.code})", border=0, ln=True)

        pdf.cell(50, 7, f"{ticket.flight.plane.upper()}", border=0)
        arrive_str = ticket.flight_adate.strftime("%d %b %Y") if ticket.flight_adate else "N/A"
        pdf.cell(50, 7, f"Arrive: {arrive_str}", border=0)
        pdf.cell(80, 7, f"{ticket.flight.destination.airport.upper()} ({ticket.flight.destination.code})", border=0, ln=True)
        pdf.ln(5)

        # Fare Details
        pdf.set_fill_color(169, 169, 169)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(190, 8, "  FARE DETAILS", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)

        pdf.cell(60, 7, "FARE:", border=0)
        pdf.cell(120, 7, f"INR {ticket.flight_fare}", border=0, ln=True)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(60, 7, "CHARGES:", border=0, fill=True)
        pdf.cell(120, 7, f"INR {ticket.other_charges}", border=0, fill=True, ln=True)
        pdf.cell(60, 7, "DISCOUNT:", border=0)
        pdf.cell(120, 7, f"INR (-) {ticket.coupon_discount}", border=0, ln=True)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, "TOTAL:", border=0, fill=True)
        pdf.cell(120, 7, f"INR {ticket.total_fare}", border=0, fill=True, ln=True)

        # Footer
        pdf.ln(10)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(190, 5, f"(C) {datetime.now().year} Flight Inc. All rights reserved.", ln=True)

        # Return PDF as bytes
        return pdf.output()

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


def render_to_pdf(template_src, context_dict={}):
    return HttpResponse("PDF generation is temporarily disabled.", content_type='text/plain')


def send_email_notification(ticket):
    """Send ticket email with PDF attachment using smtplib directly"""
    try:
        from_email = settings.EMAIL_HOST_USER
        to_email = ticket.email
        password = settings.EMAIL_HOST_PASSWORD

        # Create MIME message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = f"Flight Ticket Confirmed - Ref: {ticket.ref_no}"
        msg['From'] = from_email
        msg['To'] = to_email

        # HTML body with ticket details
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #e12323, #ff6b6b); color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">FLIGHT</h1>
                    <p style="margin: 5px 0 0 0;">Your E-Ticket</p>
                </div>
                <div style="padding: 20px;">
                    <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin-bottom: 20px; text-align: center;">
                        <h2 style="color: #155724; margin: 0;">Booking Confirmed!</h2>
                    </div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold;">Reference No.</td>
                            <td style="padding: 10px; color: #e12323; font-weight: bold; font-size: 18px;">{ticket.ref_no}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">Route</td>
                            <td style="padding: 10px;">{ticket.flight.origin.city} ({ticket.flight.origin.code}) &#8594; {ticket.flight.destination.city} ({ticket.flight.destination.code})</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold;">Airline</td>
                            <td style="padding: 10px;">{ticket.flight.airline}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">Flight Date</td>
                            <td style="padding: 10px;">{ticket.flight_ddate.strftime('%d %b %Y') if ticket.flight_ddate else 'N/A'}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold;">Class</td>
                            <td style="padding: 10px;">{ticket.seat_class.upper()}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">Total Fare</td>
                            <td style="padding: 10px; font-weight: bold; color: #28a745;">INR {ticket.total_fare}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold;">Status</td>
                            <td style="padding: 10px; color: #28a745; font-weight: bold;">{ticket.status}</td>
                        </tr>
                    </table>
                    <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
                        <p style="margin: 0; font-size: 12px;">Please find your ticket PDF attached. Present it at the airport during check-in.</p>
                    </div>
                </div>
                <div style="background: #333; color: #aaa; padding: 15px; text-align: center; font-size: 11px;">
                    &copy; {datetime.now().year} Flight Inc. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Generate and attach PDF
        pdf_bytes = generate_ticket_pdf(ticket)
        if pdf_bytes:
            pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=f'ticket_{ticket.ref_no}.pdf')
            msg.attach(pdf_attachment)

        # Send email using smtplib
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_whatsapp_notification(ticket):
    """Send WhatsApp message with an Image of the Ticket using pywhatkit"""
    try:
        import pywhatkit
        import fitz  # PyMuPDF
        import os
        from django.conf import settings
        
        to_number = ticket.mobile.replace(" ", "")
        if not to_number.startswith('+'):
            to_number = f"+{to_number}"

        msg_body = (
            f"✈️ *FLIGHT BOOKING CONFIRMED!*\n\n"
            f"Ref: {ticket.ref_no}\n"
            f"From: {ticket.flight.origin.code} To: {ticket.flight.destination.code}\n"
            f"Email check karein, waha PDF bhej di gayi hai!"
        )

        print(f"Generating Ticket Image for WhatsApp...")
        pdf_bytes = generate_ticket_pdf(ticket)
        if pdf_bytes:
            # Convert PDF to Image using PyMuPDF
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = pdf_document[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # High resolution
            
            # Save temporary image
            image_path = os.path.join(settings.BASE_DIR, f"ticket_{ticket.ref_no}.png")
            pix.save(image_path)
            
            print(f"Opening WhatsApp Web to send IMAGE to {to_number}...")
            # Wait time increased to 25s for slower internet to load WhatsApp Web
            pywhatkit.sendwhats_image(to_number, image_path, msg_body, wait_time=25, tab_close=True, close_time=4)
            return True
        else:
            print("Could not generate PDF for WhatsApp.")
            return False

    except ImportError:
        print("Required packages not installed. Please run 'pip install pywhatkit PyMuPDF' in your terminal.")
        return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error sending WhatsApp: {e}")
        return False


def send_notifications(ticket):
    """Send both email and WhatsApp notifications"""
    email_sent = send_email_notification(ticket)
    whatsapp_sent = send_whatsapp_notification(ticket)
    return email_sent, whatsapp_sent


def createticket(user,passengers,passengerscount,flight1,flight_1date,flight_1class,coupon,countrycode,email,mobile):
    ticket = Ticket.objects.create()
    ticket.user = user
    ticket.ref_no = secrets.token_hex(3).upper()
    for passenger in passengers:
        ticket.passengers.add(passenger)
    ticket.flight = flight1
    ticket.flight_ddate = datetime(int(flight_1date.split('-')[2]),int(flight_1date.split('-')[1]),int(flight_1date.split('-')[0]))
    ###################
    flight1ddate = datetime(int(flight_1date.split('-')[2]),int(flight_1date.split('-')[1]),int(flight_1date.split('-')[0]),flight1.depart_time.hour,flight1.depart_time.minute)
    flight1adate = (flight1ddate + flight1.duration)
    ###################
    ticket.flight_adate = datetime(flight1adate.year,flight1adate.month,flight1adate.day)
    ffre = 0.0
    if flight_1class.lower() == 'first':
        ticket.flight_fare = flight1.first_fare*int(passengerscount)
        ffre = flight1.first_fare*int(passengerscount)
    elif flight_1class.lower() == 'business':
        ticket.flight_fare = flight1.business_fare*int(passengerscount)
        ffre = flight1.business_fare*int(passengerscount)
    else:
        ticket.flight_fare = flight1.economy_fare*int(passengerscount)
        ffre = flight1.economy_fare*int(passengerscount)
    ticket.other_charges = FEE
    if coupon:
        ticket.coupon_used = coupon                     ##########Coupon
    ticket.total_fare = ffre+FEE+0.0                    ##########Total(Including coupon)
    ticket.seat_class = flight_1class.lower()
    ticket.status = 'PENDING'
    ticket.mobile = ('+'+countrycode+' '+mobile)
    ticket.email = email
    ticket.save()
    return ticket