import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Seat(models.Model):
    class SeatType(models.TextChoices):
        WINDOW = 'WINDOW', _('Window')
        AISLE  = 'AISLE',  _('Aisle')
        MIDDLE = 'MIDDLE', _('Middle')

    class SeatStatus(models.TextChoices):
        AVAILABLE         = 'AVAILABLE',         _('Available')
        BOOKED            = 'BOOKED',            _('Booked')
        RESERVED_LADIES   = 'RESERVED_LADIES',   _('Ladies Reserved')
        RESERVED_DISABLED = 'RESERVED_DISABLED', _('Special Access')
        BLOCKED           = 'BLOCKED',           _('Blocked')
        SELECTED          = 'SELECTED',          _('Selected (Temp)')

    schedule         = models.ForeignKey('routes.Schedule', on_delete=models.CASCADE, related_name='seats')
    seat_number      = models.CharField(max_length=5)
    row_number       = models.PositiveSmallIntegerField()
    column_letter    = models.CharField(max_length=1)
    seat_type        = models.CharField(max_length=20, choices=SeatType.choices, default=SeatType.WINDOW)
    status           = models.CharField(max_length=25, choices=SeatStatus.choices, default=SeatStatus.AVAILABLE)
    is_driver_side   = models.BooleanField(default=False)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.00'))

    class Meta:
        verbose_name = 'Seat'
        unique_together = ['schedule', 'seat_number']
        ordering = ['row_number', 'column_letter']

    def __str__(self):
        return f"Seat {self.seat_number} — {self.schedule}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING      = 'PENDING',      _('Pending Payment')
        CONFIRMED    = 'CONFIRMED',    _('Confirmed')
        CANCELLED    = 'CANCELLED',    _('Cancelled')
        REFUNDED     = 'REFUNDED',     _('Refunded')
        COMPLETED    = 'COMPLETED',    _('Completed')
        RESCHEDULED  = 'RESCHEDULED',  _('Rescheduled')

    booking_id       = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    passenger        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                          related_name='bookings', limit_choices_to={'role': 'PASSENGER'})
    schedule         = models.ForeignKey('routes.Schedule', on_delete=models.PROTECT, related_name='bookings')
    seats            = models.ManyToManyField(Seat, related_name='bookings', blank=True)
    boarding_stop    = models.ForeignKey('routes.Stop', on_delete=models.PROTECT,
                                          related_name='boarding_bookings', null=True)
    alighting_stop   = models.ForeignKey('routes.Stop', on_delete=models.PROTECT,
                                          related_name='alighting_bookings', null=True)
    num_passengers   = models.PositiveSmallIntegerField(default=1)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Fare
    base_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount       = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount     = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    convenience_fee  = models.DecimalField(max_digits=8,  decimal_places=2, default=Decimal('5.00'))

    # Pass-based booking
    bus_pass         = models.ForeignKey('BusPass', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='bookings')

    # Passenger snapshot
    passenger_name   = models.CharField(max_length=100, blank=True)
    passenger_email  = models.EmailField(blank=True)
    passenger_phone  = models.CharField(max_length=15, blank=True)

    # Reschedule / Cancel
    original_booking     = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='rescheduled_to')
    cancellation_reason  = models.TextField(blank=True)
    cancelled_at         = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['passenger', 'status']),
            models.Index(fields=['schedule', 'status']),
        ]

    def __str__(self):
        return f"Booking {self.short_id} — {self.passenger.username}"

    @property
    def short_id(self):
        return str(self.booking_id).upper()[:8]

    def calculate_totals(self):
        tax_rate = Decimal('0.05')
        self.tax_amount = (self.base_amount * tax_rate).quantize(Decimal('0.01'))
        self.total_amount = (
            self.base_amount + self.tax_amount + self.convenience_fee - self.discount_amount
        ).quantize(Decimal('0.01'))


class PassengerDetail(models.Model):
    class GenderChoice(models.TextChoices):
        MALE   = 'M', _('Male')
        FEMALE = 'F', _('Female')
        OTHER  = 'O', _('Other')

    booking  = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passenger_details')
    seat     = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='passenger_details')
    name     = models.CharField(max_length=100)
    age      = models.PositiveSmallIntegerField()
    gender   = models.CharField(max_length=1, choices=GenderChoice.choices, default=GenderChoice.MALE)
    email    = models.EmailField(blank=True)
    phone    = models.CharField(max_length=15, blank=True)
    email    = models.EmailField(blank=True, default='')
    phone    = models.CharField(max_length=15, blank=True, default='')
    id_type  = models.CharField(max_length=20, choices=[
                   ('AADHAR', 'Aadhar'), ('PAN', 'PAN'), ('PASSPORT', 'Passport'), ('DL', 'Driving License')
               ], blank=True)
    id_number = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = 'Passenger Detail'

    def __str__(self):
        return f"{self.name} — Seat {self.seat.seat_number}"


class Payment(models.Model):
    class Gateway(models.TextChoices):
        RAZORPAY = 'RAZORPAY', _('Razorpay')
        STRIPE   = 'STRIPE',   _('Stripe')
        CASH     = 'CASH',     _('Cash (Offline)')

    class Status(models.TextChoices):
        PENDING        = 'PENDING',        _('Pending')
        SUCCESS        = 'SUCCESS',        _('Success')
        FAILED         = 'FAILED',         _('Failed')
        REFUNDED       = 'REFUNDED',       _('Refunded')
        PARTIAL_REFUND = 'PARTIAL_REFUND', _('Partial Refund')

    class Method(models.TextChoices):
        UPI        = 'UPI',        _('UPI')
        CARD       = 'CARD',       _('Credit/Debit Card')
        NETBANKING = 'NETBANKING', _('Net Banking')
        WALLET     = 'WALLET',     _('Wallet')
        CASH       = 'CASH',       _('Cash')

    booking            = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    gateway            = models.CharField(max_length=20, choices=Gateway.choices, default=Gateway.RAZORPAY)
    method             = models.CharField(max_length=20, choices=Method.choices, blank=True)
    status             = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount             = models.DecimalField(max_digits=10, decimal_places=2)
    currency           = models.CharField(max_length=5, default='INR')
    gateway_order_id   = models.CharField(max_length=100, blank=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_signature  = models.CharField(max_length=255, blank=True)
    gateway_response   = models.JSONField(blank=True, null=True)
    refund_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    refund_id          = models.CharField(max_length=100, blank=True)
    refunded_at        = models.DateTimeField(null=True, blank=True)
    paid_at            = models.DateTimeField(null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.gateway_payment_id or 'PENDING'} — ₹{self.amount}"


class Ticket(models.Model):
    booking      = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='ticket')
    ticket_number = models.CharField(max_length=20, unique=True, db_index=True)
    qr_code      = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    pdf_file     = models.FileField(upload_to='tickets/', blank=True, null=True)
    is_verified  = models.BooleanField(default=False)
    verified_at  = models.DateTimeField(null=True, blank=True)
    verified_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='verified_tickets')
    issued_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ticket'
        ordering = ['-issued_at']

    def __str__(self):
        return f"Ticket #{self.ticket_number}"

    def generate_ticket_number(self):
        import datetime
        date_str = datetime.date.today().strftime('%Y%m%d')
        short_id = str(self.booking.booking_id).replace('-', '').upper()[:8]
        self.ticket_number = f"AB-{date_str}-{short_id}"
        return self.ticket_number


# ─── Bus Pass System ──────────────────────────────────────────────────────────
class PassScheme(models.Model):
    """Admin-defined pass schemes."""

    class SchemeType(models.TextChoices):
        MONTHLY    = 'MONTHLY',    _('Monthly Pass')
        STUDENT    = 'STUDENT',    _('Student Pass')
        SENIOR     = 'SENIOR',     _('Senior Citizen Pass')
        WOMEN      = 'WOMEN',      _('Ladies Special Pass')
        WORKER     = 'WORKER',     _('Daily Worker Pass')
        DIVYANGJAN = 'DIVYANGJAN', _('Divyangjan (Disabled) Pass')

    name              = models.CharField(max_length=100)
    scheme_type       = models.CharField(max_length=20, choices=SchemeType.choices, default=SchemeType.MONTHLY)
    description       = models.TextField(blank=True)
    validity_days     = models.PositiveSmallIntegerField(default=30)
    price             = models.DecimalField(max_digits=8, decimal_places=2)
    discount_pct      = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    unlimited_trips   = models.BooleanField(default=False)
    trip_limit        = models.PositiveSmallIntegerField(default=0)
    applicable_routes = models.ManyToManyField('routes.Route', blank=True, related_name='pass_schemes')
    is_active         = models.BooleanField(default=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pass Scheme'
        verbose_name_plural = 'Pass Schemes'
        ordering = ['scheme_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_scheme_type_display()}) — ₹{self.price}"

    @property
    def discount_multiplier(self):
        return Decimal('1.00') - (self.discount_pct / Decimal('100'))


class BusPass(models.Model):
    """An issued bus pass."""

    class Status(models.TextChoices):
        ACTIVE    = 'ACTIVE',    _('Active')
        EXPIRED   = 'EXPIRED',   _('Expired')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        PENDING   = 'PENDING',   _('Pending Approval')
        REJECTED  = 'REJECTED',  _('Rejected')

    pass_id          = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pass_number      = models.CharField(max_length=25, unique=True, db_index=True)
    passenger        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                          related_name='booking_bus_passes')
    scheme           = models.ForeignKey(PassScheme, on_delete=models.PROTECT, related_name='passes')
    status           = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    issued_date      = models.DateField(auto_now_add=True)
    valid_from       = models.DateField()
    valid_until      = models.DateField()
    trips_used       = models.PositiveSmallIntegerField(default=0)
    amount_paid      = models.DecimalField(max_digits=8, decimal_places=2)

    # ID proof
    id_proof_type    = models.CharField(max_length=30, blank=True,
                                         choices=[('STUDENT_ID', 'Student ID Card'),
                                                  ('AADHAR', 'Aadhar Card'),
                                                  ('COLLEGE_LETTER', 'College Letter'),
                                                  ('GOVT_ID', 'Govt ID')])
    id_proof_number  = models.CharField(max_length=50, blank=True)
    institution_name = models.CharField(max_length=150, blank=True)
    photo            = models.ImageField(upload_to='pass_photos/', blank=True, null=True)
    id_proof_doc     = models.FileField(upload_to='pass_docs/', blank=True, null=True)

    approved_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='approved_passes')
    approved_at      = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bus Pass'
        verbose_name_plural = 'Bus Passes'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['passenger', 'status'])]

    def __str__(self):
        return f"Pass {self.pass_number} — {self.passenger.get_full_name()}"

    @property
    def is_valid_today(self):
        import datetime
        today = datetime.date.today()
        return (self.status == self.Status.ACTIVE and
                self.valid_from <= today <= self.valid_until)

    @property
    def secure_qr_token(self):
        import hmac, hashlib, base64, json
        payload = {
            "pass": self.pass_number,
            "valid_until": str(self.valid_until),
            "passenger": self.passenger.get_full_name() or self.passenger.username,
            "iss": "ANANDBUS",
            "type": self.scheme.scheme_type,
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        sig = hmac.new(settings.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()[:16]
        return f"ABTOKEN.{payload_b64}.{sig}"

    @property
    def trips_remaining(self):
        if self.scheme.unlimited_trips or self.scheme.trip_limit == 0:
            return '∞'
        return max(0, self.scheme.trip_limit - self.trips_used)

    def generate_pass_number(self):
        import datetime
        type_code = self.scheme.scheme_type[:3].upper()
        date_str = datetime.date.today().strftime('%y%m')
        uid = str(self.pass_id).replace('-', '').upper()[:6]
        self.pass_number = f"AB-{type_code}-{date_str}-{uid}"
        return self.pass_number


class PassUsageLog(models.Model):
    """Log every trip made using a bus pass."""
    bus_pass    = models.ForeignKey(BusPass, on_delete=models.CASCADE, related_name='usage_logs')
    schedule    = models.ForeignKey('routes.Schedule', on_delete=models.SET_NULL, null=True)
    boarding    = models.ForeignKey('routes.Stop', on_delete=models.SET_NULL, null=True,
                                    related_name='pass_boarding_logs')
    alighting   = models.ForeignKey('routes.Stop', on_delete=models.SET_NULL, null=True,
                                    related_name='pass_alighting_logs')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='pass_verifications')
    verified_at = models.DateTimeField(auto_now_add=True)
    fare_saved  = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Pass Usage Log'
        ordering = ['-verified_at']

    def __str__(self):
        return f"Pass {self.bus_pass.pass_number} used on {self.verified_at.date()}"


# ─── Ride Ratings & Staff Reviews ─────────────────────────────────────────────
class RideRating(models.Model):
    """Driver & Bus Staff Ratings & Feedback submitted by passengers for completed trips."""
    booking            = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='ride_rating')
    passenger          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ride_ratings')
    schedule           = models.ForeignKey('routes.Schedule', on_delete=models.CASCADE, related_name='ride_ratings')
    driver             = models.ForeignKey('buses.Driver', on_delete=models.SET_NULL, null=True, blank=True, related_name='ratings')
    bus                = models.ForeignKey('buses.Bus', on_delete=models.SET_NULL, null=True, blank=True, related_name='ratings')

    driver_punctuality = models.PositiveSmallIntegerField(default=5)
    bus_cleanliness    = models.PositiveSmallIntegerField(default=5)
    staff_behavior     = models.PositiveSmallIntegerField(default=5)
    overall_rating     = models.PositiveSmallIntegerField(default=5)

    comment            = models.TextField(blank=True, default='')
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ride Rating'
        verbose_name_plural = 'Ride Ratings'
        ordering = ['-created_at']

    def __str__(self):
        return f"Rating {self.overall_rating}★ for Booking {self.booking.short_id} by {self.passenger.username}"

