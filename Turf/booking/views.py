from datetime import datetime, timedelta, time
from functools import wraps
import base64
from io import BytesIO
import qrcode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
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
        return render(request, "booking/staff_login.html", {"error": "Invalid credentials"})
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


# ================= STAFF =================

@staff_required
def staff_dashboard(request):
    return render(request, "booking/staff_dashboard.html", {
        "sports": Sport.objects.all()
    })


@staff_required
def staff_slots_view(request, sport_id):
    sport = get_object_or_404(Sport, id=sport_id)

    selected_date = timezone.localdate()
    if request.GET.get("date"):
        selected_date = datetime.strptime(request.GET.get("date"), "%Y-%m-%d").date()

    for hour in range(24):
        Slot.objects.get_or_create(
            sport=sport,
            date=selected_date,
            time=time(hour, 0)
        )

    slots = Slot.objects.filter(sport=sport, date=selected_date).order_by("time")

    for slot in slots:
        start = datetime.combine(slot.date, slot.time)
        slot.start_label = start.strftime("%I:%M %p").lstrip("0")
        slot.end_label = (start + timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")

    return render(request, "booking/staff_slots.html", {
        "sport": sport,
        "slots": slots,
        "selected_date": selected_date,
        "dates": [timezone.localdate() + timedelta(days=i) for i in range(7)],
        "today": timezone.localdate(),
        "current_hour": timezone.localtime().hour,
    })


@require_POST
@staff_required
def toggle_slot_booking(request, slot_id):
    slot = get_object_or_404(Slot, id=slot_id)
    slot.is_booked = not slot.is_booked
    slot.save()
    return JsonResponse({"booked": slot.is_booked})


# ================= PUBLIC =================

def home(request):
    return render(request, "booking/home.html", {
        "sports": Sport.objects.all()
    })


def slots_view(request, sport_id):
    sport = get_object_or_404(Sport, id=sport_id)

    selected_date = timezone.localdate()
    if request.GET.get("date"):
        selected_date = datetime.strptime(request.GET.get("date"), "%Y-%m-%d").date()

    for hour in range(24):
        Slot.objects.get_or_create(
            sport=sport,
            date=selected_date,
            time=time(hour, 0)
        )

    slots = Slot.objects.filter(sport=sport, date=selected_date).order_by("time")

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
        "current_hour": timezone.localtime().hour,
    })


def user_details(request):
    if request.method != "POST":
        return redirect("home")
    return render(request, "booking/user_details.html", {
        "slot_ids": request.POST.getlist("slots[]")
    })


def payment_page(request):
    if request.method != "POST":
        return redirect("home")

    slot_ids = request.POST.getlist("slots[]")
    slots = Slot.objects.filter(id__in=slot_ids).order_by("time")

    for slot in slots:
        start = datetime.combine(slot.date, slot.time)
        slot.start_label = start.strftime("%I:%M %p").lstrip("0")
        slot.end_label = (start + timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")

    total = sum(get_slot_price(slot) for slot in slots)

    return render(request, "booking/payment.html", {
        "slots": slots,
        "total": total,
        "user_name": request.POST.get("user_name"),
        "phone": request.POST.get("phone"),
        "sport": slots.first().sport,
        "date": slots.first().date,
    })


# ================= BOOKING =================

def generate_qr_base64(booking):
    qr = qrcode.make(f"{settings.SITE_URL}/verify/{booking.booking_id}/")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


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
    ).order_by("time")

    if not slots.exists():
        return redirect("home")

    booking = Booking.objects.create(
        user_name=user_name,
        phone=phone
    )

    booking.slots.set(slots)
    slots.update(is_booked=True)

    total_amount = 0

    for slot in slots:
        start = datetime.combine(slot.date, slot.time)
        slot.start_label = start.strftime("%I:%M %p").lstrip("0")
        slot.end_label = (start + timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")
        slot.price = get_slot_price(slot)
        total_amount += slot.price

    return render(request, "booking/success.html", {
        "booking": booking,
        "slots": slots,
        "total_amount": total_amount,
        "qr_code": generate_qr_base64(booking),
    })



# ================= VERIFY / PDF =================

def verify_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    return render(request, "booking/verify.html", {"booking": booking})


def download_booking_pdf(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="booking_{booking.booking_id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    qr_img = ImageReader(BytesIO(base64.b64decode(generate_qr_base64(booking))))
    p.drawImage(qr_img, 100, 500, 200, 200)
    p.showPage()
    p.save()
    return response


# ================= STATIC =================

def contact_page(request):
    return render(request, "booking/contact.html", {
        "contact": Contact.objects.first()
    })


def gallery(request):
    return render(request, "booking/gallery.html", {
        "images": GalleryImage.objects.filter(active=True)
    })
