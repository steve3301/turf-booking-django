from django.urls import path
from . import views

urlpatterns = [
    # ---------- STAFF AUTH ----------
    path("staff/login/", views.staff_login, name="staff_login"),
    path("staff/logout/", views.staff_logout, name="staff_logout"),
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),

    # ---------- STAFF PANEL ----------
    path("staff/booking/<int:sport_id>/", views.staff_slots_view, name="staff_slots"),
    path("staff/toggle/<int:slot_id>/", views.toggle_slot_booking, name="toggle_slot"),

    # ---------- PUBLIC ----------
    path("", views.home, name="home"),
    path("slots/<int:sport_id>/", views.slots_view, name="slots"),
    path("booking/details/", views.user_details, name="user_details"),
    path("payment/", views.payment_page, name="payment"),
    path("confirm/", views.confirm_booking, name="confirm_booking"),

    # ---------- VERIFY & DOWNLOAD ----------
    path("verify/<uuid:booking_id>/", views.verify_booking, name="verify_booking"),
    path("download/<uuid:booking_id>/", views.download_booking_pdf, name="download_booking_pdf"),
    path("staff/toggle/<int:slot_id>/", views.toggle_slot_booking, name="toggle_slot_booking"),


    # ---------- STATIC ----------
    path("gallery/", views.gallery, name="gallery"),
    path("contact/", views.contact_page, name="contact"),
]
