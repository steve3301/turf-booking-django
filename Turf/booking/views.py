# force redeploy

from datetime import datetime, timedelta, time
from functools import wraps
import base64
from io import BytesIO

import qrcode

from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.conf import settings

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from .models import Sport, Slot, Booking, Contact
from .utils import get_slot_price
from gallery.models import GalleryImage


# ================= STAFF AUTH =================

def staff_login(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )
        if user and user.is_staff:
            login(request, user)
            return redirect("staff_dashboard")

        return render(request, "booking/staff_login.html", {
            "error": "Invalid credentials or not staff"
        })

    return render(request, "booking/staff_login.html")


def staff_logout(request):
    logout(request)
    return redirect("staff_login")


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect("staff_login")
        return view_func(request, *args, **kwargs)
    return wrapper


# ================= HOME =================

def home(request):
    return render(request, "booking/home.html", {
        "sports": Sport.objects.all()
    })


# ================= SLOT LIST =================

def slots_view(request, sport_id):
    sport = get_object_or_404(Sport, id=sport_id)

    selected_date = timezone.localdate()
    if request.GET.get("date"):
        selected_date = datetime.strptime(
            request.GET.get("date"), "%Y-%m-%d"
        ).date()

    for hour in range(24):
        Slot.objects.get_or_create(
            sport=sport,
            date=selected_date,
            time=time(hour, 0)
        )

    slots = Slot.objects.filter(sport=sport, date=selected_date)

    for slot in slots:
        start = datetime.combine(slot.date, slot.time)
        slot.start_label = start.strftime("%I:%M %p").lstrip("0")
        slot.end_label = (start + timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")
        slot.price = get_slot_price(slot)

    return render(request, "booking/slots.html", {
        "sport": sport,
        "slots": slots,
        "selected_date": selected_date,
        "dates": [timezone.localdate() + timedelta(days=i) for i in range(7)],
        "today": timezone.localdate(),
        "current_hour": timezone.localtime().hour
    })


# ================= USER DETAILS =================

def user_details(request):
    if request.method != "POST":
        return redirect("home")

    slot_ids = request.POST.getlist("slots[]")
    if not slot_ids:
        return redirect("home")

    return render(request, "booking/user_details.html", {
        "slot_ids": slot_ids
    })


# ================= PAYMENT =================

def payment_page(request):
    if request.method != "POST":
        return redirect("home")

    slot_ids = request.POST.getlist("slots[]")
    user_name = request.POST.get("user_name")
    phone = request.POST.get("phone")

    slots = Slot.objects.filter(id__in=slot_ids)

    total = 0
    for slot in slots:
        slot.price = get_slot_price(slot)
        total += slot.price

    first_slot = slots.first()

    return render(request, "booking/payment.html", {
        "slots": slots,
        "total": total,
        "sport": first_slot.sport,
        "date": first_slot.date,
        "user_name": user_name,
        "phone": phone
    })


# ================= QR =================

def generate_qr_base64(booking):
    qr_data = f"{settings.SITE_URL}/verify/{booking.booking_id}/"
    qr = qrcode.make(qr_data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


# ================= CONFIRM BOOKING =================

@transaction.atomic
def confirm_booking(request):
    if request.method != "POST":
        return redirect("home")

    slot_ids = request.POST.getlist("slots[]")
    user_name = request.POST.get("user_name")
    phone = request.POST.get("phone")

    slots = Slot.objects.select_for_update().filter(
        id__in=slot_ids,
        is_booked=False
    )

    if slots.count() != len(slot_ids):
        return render(request, "booking/error.html", {
            "message": "One or more slots already booked"
        })

    booking = Booking.objects.create(
        user_name=user_name,
        phone=phone
    )

    booking.slots.set(slots)
    slots.update(is_booked=True)

    for slot in slots:
        start = datetime.combine(slot.date, slot.time)
        slot.start_label = start.strftime("%I:%M %p").lstrip("0")
        slot.end_label = (start + timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")
        slot.price = get_slot_price(slot)

    total = sum(slot.price for slot in slots)
    qr_code = generate_qr_base64(booking)

    return render(request, "booking/success.html", {
        "booking": booking,
        "slots": slots,
        "total": total,
        "qr_code": qr_code
    })


# ================= SUCCESS (REQUIRED) =================
# This fixes the Render crash

def success(request):
    return redirect("home")


# ================= VERIFY =================

def verify_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    return render(request, "booking/verify.html", {"booking": booking})


# ================= STATIC PAGES =================

def contact_page(request):
    return render(request, "booking/contact.html", {
        "contact": Contact.objects.first()
    })


def gallery(request):
    images = GalleryImage.objects.filter(active=True).order_by("-created_at")
    return render(request, "booking/gallery.html", {
        "images": images
    })
