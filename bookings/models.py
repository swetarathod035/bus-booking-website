import random
import string
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Seat(models.Model):
    """
    Seat layout for a schedule (generated per trip).
    2x3 grid with driver-side indicator.
    """

    class SeatType(models.TextChoices):
        WINDOW = 'WINDOW', _('Window')
        AISLE = 'AISLE', _('Aisle')
        MIDDLE = 'MIDDLE', _('Middle')

    class SeatStatus(models.TextChoices):
        AVAILABLE = 'AVAILABLE', _('Available')
        BOOKED = 'BOOKED', _('Booked')
        RESERVED_LADIES = 'RESERVED_LADIES', _('Ladies Reserved')
        RESERVED_DISABLED = 'RESERVED_DISABLED', _('Special Access')
        BLOCKED = 'BLOCKED', _('Blocked')
        SELECTED = 'SELECTED', _('Selected (Temp)')

    schedule = models.ForeignKey(
        'routes.Schedule', on_delete=models.CASCADE, related_name='seats'
    )
    seat_number = models.CharField(max_length=5)   # e.g. "1A", "2B", "10C"
    row_number = models.PositiveSmallIntegerField()
    column_letter = models.CharField(max_length=1)  # A, B, C, D, E
    seat_type = models.CharField(max_length=20, choices=SeatType.choices, default=SeatType.WINDOW)
    status = models.CharField(max_length=25, choices=SeatStatus.choices, default=SeatStatus.AVAILABLE)
    is_driver_side = models.BooleanField(default=False)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.00'))

    class Meta:
        verbose_name = 'Seat'
        verbose_name_plural = 'Seats'
        unique_together = ['schedule', 'seat_number']
        ordering = ['row_number', 'column_letter']

    def __str__(self):
        return f"Seat {self.seat_number} - {self.schedule}"


class Booking(models.Model):
    """Core booking/reservation entity."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Payment')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        REFUNDED = 'REFUNDED', _('Refunded')
        COMPLETED = 'COMPLETED', _('Completed')
        RESCHEDULED = 'RESCHEDULED', _('Rescheduled')

    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    pnr_number = models.CharField(max_length=20, unique=True, db_index=True, blank=True, null=True)
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        limit_choices_to={'role': 'PASSENGER'},
    )
    schedule = models.ForeignKey(
        'routes.Schedule', on_delete=models.PROTECT, related_name='bookings'
    )
    seats = models.ManyToManyField(Seat, related_name='bookings', blank=True)
    boarding_stop = models.ForeignKey(
        'routes.Stop', on_delete=models.PROTECT, related_name='boarding_bookings', null=True
    )
    alighting_stop = models.ForeignKey(
        'routes.Stop', on_delete=models.PROTECT, related_name='alighting_bookings', null=True
    )
    num_passengers = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Fare breakdown
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    convenience_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('5.00'))

    # Passenger details snapshot
    passenger_name = models.CharField(max_length=100, blank=True)
    passenger_email = models.EmailField(blank=True)
    passenger_phone = models.CharField(max_length=15, blank=True)

    # Rescheduling
    original_booking = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rescheduled_to'
    )
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['passenger', 'status']),
            models.Index(fields=['schedule', 'status']),
            models.Index(fields=['pnr_number']),
        ]

    def __str__(self):
        return f"Booking {self.pnr_number or self.short_id} - {self.passenger.username}"

    @property
    def short_id(self):
        return self.pnr_number or str(self.booking_id).upper()[:8]

    def generate_pnr(self):
        """Generate a unique PNR code like PNR8A2K9X3."""
        if not self.pnr_number:
            while True:
                code = 'PNR' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
                if not Booking.objects.filter(pnr_number=code).exists():
                    self.pnr_number = code
                    break
        return self.pnr_number

    def save(self, *args, **kwargs):
        if not self.pnr_number:
            self.generate_pnr()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Recalculate fare with tax and convenience fee."""
        tax_rate = Decimal('0.05')  # 5% GST
        self.tax_amount = (self.base_amount * tax_rate).quantize(Decimal('0.01'))
        self.total_amount = (
            self.base_amount + self.tax_amount + self.convenience_fee - self.discount_amount
        ).quantize(Decimal('0.01'))



class PassengerDetail(models.Model):
    """Individual passenger details for multi-passenger bookings."""

    class GenderChoice(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
        OTHER = 'O', _('Other')

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passenger_details')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='passenger_details')
    name = models.CharField(max_length=100)
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=1, choices=GenderChoice.choices, default=GenderChoice.MALE)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    id_type = models.CharField(
        max_length=20,
        choices=[('AADHAR', 'Aadhar'), ('PAN', 'PAN'), ('PASSPORT', 'Passport'), ('DL', 'Driving License')],
        blank=True,
    )
    id_number = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = 'Passenger Detail'

    def __str__(self):
        return f"{self.name} - Seat {self.seat.seat_number}"


class Payment(models.Model):
    """Payment transaction record."""

    class Gateway(models.TextChoices):
        RAZORPAY = 'RAZORPAY', _('Razorpay')
        STRIPE = 'STRIPE', _('Stripe')
        CASH = 'CASH', _('Cash (Offline)')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SUCCESS = 'SUCCESS', _('Success')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')
        PARTIAL_REFUND = 'PARTIAL_REFUND', _('Partial Refund')

    class Method(models.TextChoices):
        UPI = 'UPI', _('UPI')
        CARD = 'CARD', _('Credit/Debit Card')
        NETBANKING = 'NETBANKING', _('Net Banking')
        WALLET = 'WALLET', _('Wallet')
        CASH = 'CASH', _('Cash')

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    gateway = models.CharField(max_length=20, choices=Gateway.choices, default=Gateway.RAZORPAY)
    method = models.CharField(max_length=20, choices=Method.choices, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')

    # Gateway-specific IDs
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(blank=True, null=True)

    # Refund
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    refund_id = models.CharField(max_length=100, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.gateway_payment_id or 'PENDING'} - ₹{self.amount}"


class Ticket(models.Model):
    """Generated ticket with QR code."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='ticket')
    ticket_number = models.CharField(max_length=20, unique=True, db_index=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='tickets/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_tickets',
    )
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-issued_at']

    def __str__(self):
        return f"Ticket #{self.ticket_number}"

    def generate_ticket_number(self):
        """Generate ticket number like AB-20260808-XXXXXXXX."""
        import datetime
        date_str = datetime.date.today().strftime('%Y%m%d')
        short_id = str(self.booking.booking_id).replace('-', '').upper()[:8]
        self.ticket_number = f"AB-{date_str}-{short_id}"
        return self.ticket_number
