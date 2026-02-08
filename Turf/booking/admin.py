from django.contrib import admin
from django.utils.html import format_html

from .models import Sport, Slot, Booking, SlotPricing, Contact


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ("name", "image_preview")
    search_fields = ("name",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:50px;border-radius:6px;" />',
                obj.image.url
            )
        return "No Image"

    image_preview.short_description = "Image"


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("sport", "date", "time", "is_booked")
    list_filter = ("sport", "date", "is_booked")
    ordering = ("date", "time")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user_name", "phone", "booking_id", "created_at")
    search_fields = ("user_name", "phone", "booking_id")
    readonly_fields = ("booking_id", "created_at")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("phone", "email")
    search_fields = ("phone", "email")


@admin.register(SlotPricing)
class SlotPricingAdmin(admin.ModelAdmin):
    list_display = (
        "sport",
        "date",
        "start_time",
        "end_time",
        "price",
        "discount",
        "active",
    )
    list_filter = ("sport", "date", "active")
    search_fields = ("sport__name",)
