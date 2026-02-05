from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime, timedelta


# ================= SPORT =================

class Sport(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.IntegerField(default=300)

    def __str__(self):
        return self.name




# ================= SLOT =================

class Slot(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("sport", "date", "time")
        ordering = ["time"]

    def display_time(self):
        start = datetime.combine(self.date, self.time)
        end = start + timedelta(hours=1)
        return f"{start.strftime('%I:%M %p')} – {end.strftime('%I:%M %p')}"

    def __str__(self):
        return f"{self.sport.name} | {self.date} | {self.display_time()}"


# ================= BOOKING =================

class Booking(models.Model):
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    user_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    slots = models.ManyToManyField(Slot, related_name="bookings")

    qr_path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} | {self.booking_id}"


# ================= STAFF PROFILE =================

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_staff_member = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username


# ================= CONTACT =================

class Contact(models.Model):
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True)

    def __str__(self):
        return self.phone


# ================= SLOT PRICING =================

class SlotPricing(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)

    date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave empty to apply pricing every day until changed"
    )

    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Leave empty to start from beginning of day"
    )

    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Leave empty to apply until end of day"
    )

    price = models.PositiveIntegerField(help_text="Base price for this time range")
    discount = models.PositiveIntegerField(
        default=0,
        help_text="Flat discount amount (₹)"
    )

    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sport", "date", "start_time"]

    def final_price(self):
        return max(self.price - self.discount, 0)

    def discount_percent(self):
        if self.price > 0 and self.discount > 0:
            return int((self.discount / self.price) * 100)
        return 0

    discount_percent.short_description = "Discount %"

    def __str__(self):
        if self.date:
            return f"{self.sport} | {self.date} | ₹{self.final_price()}"
        return f"{self.sport} | Daily | ₹{self.final_price()}"
