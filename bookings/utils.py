"""
Booking utility functions:
- Seat layout generator
- Fare calculator
- PDF ticket generator (ReportLab)
- QR code generator
- SMTP email sender
"""
import io
import os
import uuid
import qrcode
from decimal import Decimal
from PIL import Image

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .models import Seat, Ticket


# ─── Seat Layout Generator ────────────────────────────────────────────────────
COLUMN_MAP = {
    'A': ('WINDOW', False),   # Left window
    'B': ('AISLE', False),    # Left aisle
    'C': ('MIDDLE', False),   # Middle (aisle separator)
    'D': ('AISLE', False),    # Right aisle
    'E': ('WINDOW', False),   # Right window
}

LADIES_RESERVED_ROWS = [1, 2]           # First 2 rows ladies reserved
DISABLED_SEATS = ['1A', '1E']           # Front window seats for disabled
BLOCKED_SEATS = []                       # none blocked by default


def generate_seat_layout(schedule):
    """
    Generate a 2x3 (A,B | C | D,E) seat grid for the given schedule.
    Total seats pulled from bus.total_seats.
    """
    total = schedule.bus.total_seats
    rows = (total // 5) + (1 if total % 5 else 0)
    created = []

    for row in range(1, rows + 1):
        for col_letter, (seat_type, _) in COLUMN_MAP.items():
            seat_num = f"{row}{col_letter}"
            seq_number = (row - 1) * 5 + list(COLUMN_MAP.keys()).index(col_letter) + 1
            if seq_number > total:
                break

            # Determine status
            if seat_num in DISABLED_SEATS:
                status = Seat.SeatStatus.RESERVED_DISABLED
            elif row in LADIES_RESERVED_ROWS and col_letter in ('D', 'E'):
                status = Seat.SeatStatus.RESERVED_LADIES
            elif seat_num in BLOCKED_SEATS:
                status = Seat.SeatStatus.BLOCKED
            else:
                status = Seat.SeatStatus.AVAILABLE

            created.append(Seat(
                schedule=schedule,
                seat_number=seat_num,
                row_number=row,
                column_letter=col_letter,
                seat_type=seat_type,
                status=status,
                is_driver_side=(col_letter in ('A', 'B')),
                price_multiplier=Decimal('1.10') if col_letter in ('A', 'E') else Decimal('1.00'),
            ))

    Seat.objects.bulk_create(created, ignore_conflicts=True)
    return created


# ─── Fare Calculator ──────────────────────────────────────────────────────────
def calculate_fare(schedule, from_stop, to_stop, num_seats=1):
    """Calculate full fare breakdown between two stops on a route."""
    from routes.models import RouteStop

    try:
        from_rs = RouteStop.objects.get(route=schedule.route, stop=from_stop)
        to_rs = RouteStop.objects.get(route=schedule.route, stop=to_stop)
        distance = float(to_rs.distance_from_source) - float(from_rs.distance_from_source)
        distance = max(distance, 1.0)
    except Exception:
        distance = float(schedule.route.distance_km) or 10.0

    per_seat_fare = float(schedule.route.base_fare) + (distance * float(schedule.route.fare_per_km))
    per_seat_fare = round(per_seat_fare, 2)
    base_amount = round(per_seat_fare * num_seats, 2)

    tax_rate = 0.05  # 5% GST
    tax_amount = round(base_amount * tax_rate, 2)
    convenience_fee = 5.00 * num_seats
    discount = 0.00
    total = round(base_amount + tax_amount + convenience_fee - discount, 2)

    return {
        'per_seat_fare': per_seat_fare,
        'base_amount': base_amount,
        'tax_amount': tax_amount,
        'convenience_fee': convenience_fee,
        'discount_amount': discount,
        'total_amount': total,
        'distance_km': round(distance, 2),
        'num_seats': num_seats,
    }


# ─── QR Code Generator ────────────────────────────────────────────────────────
def generate_qr_code(ticket):
    """Generate a QR code image for the ticket and save to media."""
    qr_data = (
        f"ANANDBUS|TICKET:{ticket.ticket_number}|"
        f"BOOKING:{str(ticket.booking.booking_id)[:8].upper()}|"
        f"ROUTE:{ticket.booking.schedule.route.route_number}|"
        f"DATE:{ticket.booking.schedule.travel_date}|"
        f"PASSENGER:{ticket.booking.passenger_name}"
    )
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#1E3A5F', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    filename = f"qr_{ticket.ticket_number}.png"
    ticket.qr_code.save(filename, ContentFile(buffer.read()), save=True)
    return ticket.qr_code.path


# ─── PDF Ticket Generator ─────────────────────────────────────────────────────
def generate_ticket_pdf(ticket):
    """Generate a styled PDF ticket using ReportLab."""
    booking = ticket.booking
    schedule = booking.schedule
    route = schedule.route

    # Generate QR first
    qr_path = None
    if not ticket.qr_code:
        qr_path = generate_qr_code(ticket)
    else:
        qr_path = ticket.qr_code.path

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    brand_color = colors.HexColor('#1E3A5F')
    accent_color = colors.HexColor('#FF6B35')
    light_bg = colors.HexColor('#F8F9FA')

    title_style = ParagraphStyle('title', parent=styles['Title'],
        fontSize=22, textColor=brand_color, spaceAfter=4, alignment=TA_CENTER)
    sub_style = ParagraphStyle('sub', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#666666'), alignment=TA_CENTER)
    heading_style = ParagraphStyle('heading', parent=styles['Normal'],
        fontSize=12, textColor=brand_color, fontName='Helvetica-Bold', spaceAfter=6)
    normal_style = ParagraphStyle('normal', parent=styles['Normal'], fontSize=10, spaceAfter=4)

    story = []

    # Header Banner
    story.append(Paragraph('🚌 ANANDBUS', title_style))
    story.append(Paragraph('Your Smart City Bus Companion — Anand, Gujarat', sub_style))
    story.append(Spacer(1, 0.3*cm))

    # Ticket number banner
    ticket_banner_data = [[
        Paragraph(f'<font size="14" color="white"><b>TICKET # {ticket.ticket_number}</b></font>', normal_style),
        Paragraph(f'<font size="10" color="white">{booking.status}</font>', normal_style),
    ]]
    ticket_banner = Table(ticket_banner_data, colWidths=[13*cm, 4*cm])
    ticket_banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), brand_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(ticket_banner)
    story.append(Spacer(1, 0.4*cm))

    # Journey info table
    seats_list = ', '.join([s.seat_number for s in booking.seats.all()])
    journey_data = [
        ['FROM', str(booking.boarding_stop), 'TO', str(booking.alighting_stop)],
        ['DATE', str(schedule.travel_date), 'TIME', str(schedule.departure_time.strftime('%I:%M %p'))],
        ['BUS', f"{schedule.bus.bus_number} — {schedule.bus.bus_name}", 'SEATS', seats_list],
        ['ROUTE', route.route_number, 'PASSENGERS', str(booking.num_passengers)],
    ]
    journey_table = Table(journey_data, colWidths=[3*cm, 7*cm, 3*cm, 4*cm])
    journey_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), brand_color),
        ('TEXTCOLOR', (2, 0), (2, -1), brand_color),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [light_bg, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(journey_table)
    story.append(Spacer(1, 0.4*cm))

    # Fare breakdown + QR side by side
    fare_data = [
        ['FARE BREAKDOWN', ''],
        ['Base Fare', f'₹{booking.base_amount}'],
        ['GST (5%)', f'₹{booking.tax_amount}'],
        ['Convenience Fee', f'₹{booking.convenience_fee}'],
        ['Discount', f'-₹{booking.discount_amount}'],
        ['TOTAL PAID', f'₹{booking.total_amount}'],
    ]
    fare_table = Table(fare_data, colWidths=[7*cm, 4*cm])
    fare_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), brand_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), accent_color),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))

    # QR code image
    qr_elements = []
    if qr_path and os.path.exists(qr_path):
        qr_img = RLImage(qr_path, width=4*cm, height=4*cm)
        qr_elements = [[qr_img]]
    else:
        qr_elements = [['QR CODE']]

    qr_table = Table(qr_elements, colWidths=[5*cm])
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, brand_color),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    combined = Table([[fare_table, qr_table]], colWidths=[11.5*cm, 5.5*cm])
    combined.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (1, 0), (1, 0), 10)]))
    story.append(combined)
    story.append(Spacer(1, 0.4*cm))

    # Passenger info
    story.append(Paragraph('Passenger Information', heading_style))
    pax_data = [['Name', booking.passenger_name], ['Email', booking.passenger_email],
                ['Phone', booking.passenger_phone or '—']]
    pax_table = Table(pax_data, colWidths=[4*cm, 13*cm])
    pax_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), brand_color),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#DEE2E6')),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
    ]))
    story.append(pax_table)
    story.append(Spacer(1, 0.3*cm))

    # Terms & footer
    terms_style = ParagraphStyle('terms', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#888888'), spaceAfter=3)
    story.append(Paragraph(
        '⚠️ This ticket is non-transferable. Present QR code to conductor for verification. '
        'Arrive 10 minutes before departure. AnandBus is not liable for delays due to traffic or weather.',
        terms_style
    ))
    story.append(Spacer(1, 0.2*cm))
    footer_style = ParagraphStyle('footer', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#AAAAAA'), alignment=TA_CENTER)
    story.append(Paragraph(
        f'Generated by AnandBus System | {booking.created_at.strftime("%d %b %Y %I:%M %p")} | '
        f'Booking ID: {booking.short_id}',
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)

    pdf_filename = f"ticket_{ticket.ticket_number}.pdf"
    ticket.pdf_file.save(pdf_filename, ContentFile(buffer.read()), save=True)
    return ticket.pdf_file.path


# ─── SMTP Email Sender ────────────────────────────────────────────────────────
def send_booking_email(booking):
    """Send HTML confirmation email with PDF ticket attached."""
    ticket = getattr(booking, 'ticket', None)
    subject = f'🎟️ Your AnandBus Ticket Confirmed! #{booking.short_id}'

    html_content = render_to_string('emails/booking_confirmation.html', {
        'booking': booking,
        'ticket': ticket,
        'schedule': booking.schedule,
        'route': booking.schedule.route,
        'passenger': booking.passenger,
        'site_url': settings.SITE_URL,
    })

    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.passenger_email or booking.passenger.email],
    )
    email.content_subtype = 'html'

    # Attach PDF
    if ticket and ticket.pdf_file:
        try:
            with ticket.pdf_file.open('rb') as f:
                email.attach(
                    filename=f'AnandBus_{ticket.ticket_number}.pdf',
                    content=f.read(),
                    mimetype='application/pdf',
                )
        except Exception:
            pass

    email.send(fail_silently=True)
