from datetime import datetime, timedelta, time
from functools import wraps
import os
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


# ================= STAFF DASHBOARD =================

@staff_required
def staff_dashboard(request):
    return render(request, "booking/staff_dashboard.html", {
        "sports": Sport.objects.all()
    })


# ================= HOME =================

def home(request):
    return render(request, "booking/home.html", {
        "sports": Sport.objects.all()
    })


# ================= USER SLOTS =================

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

def generate_qr(booking):
    qr_data = f"{settings.SITE_URL}/verify/{booking.booking_id}/"
    qr_img = qrcode.make(qr_data)

    folder = os.path.join(settings.MEDIA_ROOT, "qrcodes")
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, f"{booking.booking_id}.png")
    qr_img.save(path)

    return f"qrcodes/{booking.booking_id}.png"


# ================= CONFIRM BOOKING =================

@transaction.atomic
def confirm_booking(request):
    slot_ids = request.POST.getlist("slots[]")
    user_name = request.POST.get("user_name")
    phone = request.POST.get("phone")

    slots = Slot.objects.select_for_update().filter(id__in=slot_ids, is_booked=False)

    booking = Booking.objects.create(user_name=user_name, phone=phone)
    booking.slots.set(slots)
    slots.update(is_booked=True)

    booking.qr_path = generate_qr(booking)
    booking.save()

    return render(request, "booking/success.html", {"booking": booking})

def download_booking_pdf(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="booking_{booking.booking_id}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 18)
    p.drawString(150, height - 50, "Turf Booking Confirmation")

    p.setFont("Helvetica", 12)
    y = height - 120

    details = [
        f"Booking ID: {booking.booking_id}",
        f"Name: {booking.user_name}",
        f"Phone: {booking.phone}",
        f"Slots booked: {booking.slots.count()}",
        "Status: CONFIRMED",
    ]

    for line in details:
        p.drawString(80, y, line)
        y -= 22

    if booking.qr_path:
        qr_path = os.path.join(settings.MEDIA_ROOT, booking.qr_path)
        if os.path.exists(qr_path):
            p.drawImage(qr_path, 80, y - 220, width=200, height=200)

    p.showPage()
    p.save()
    return response

# ================= STAFF SLOT PANEL =================

@staff_required
def staff_slots_view(request, sport_id):
    sport = get_object_or_404(Sport, id=sport_id)
    selected_date = timezone.localdate()

    slots = Slot.objects.filter(sport=sport, date=selected_date)

    return render(request, "booking/staff_slots.html", {
        "sport": sport,
        "slots": slots,
        "selected_date": selected_date
    })


# ================= AJAX TOGGLE =================

@require_POST
@staff_required
def toggle_slot_booking(request, slot_id):
    slot = get_object_or_404(Slot, id=slot_id)
    slot.is_booked = not slot.is_booked
    slot.save()
    return JsonResponse({"status": "success", "booked": slot.is_booked})


# ================= VERIFY =================

def verify_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    return render(request, "booking/verify.html", {"booking": booking})


# ================= STATIC PAGES =================

def success(request):
    return render(request, "booking/success.html")


def contact_page(request):
    return render(request, "booking/contact.html", {
        "contact": Contact.objects.first()
    })


def gallery(request):
    images = GalleryImage.objects.filter(active=True).order_by("-created_at")
    return render(request, "booking/gallery.html", {
        "images": images
    })