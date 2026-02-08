from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime, timedelta

# ================= SPORT =================

class Sport(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to="sports/", blank=True, null=True)

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
    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    slots = models.ManyToManyField(Slot, related_name="bookings")

    total_amount = models.PositiveIntegerField(default=0)  # ✅ FIX
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} | {self.booking_id}"


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
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    price = models.PositiveIntegerField()
    discount = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def final_price(self):
        return max(self.price - self.discount, 0)

    def __str__(self):
        return f"{self.sport} | ₹{self.final_price()}"
