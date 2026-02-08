from django.shortcuts import redirect
from django.db import models
from .models import SlotPricing

def get_slot_price(slot):
    pricing = SlotPricing.objects.filter(
        sport=slot.sport,
        active=True
    ).filter(
        models.Q(date=slot.date) | models.Q(date__isnull=True),
        models.Q(start_time__lte=slot.time) | models.Q(start_time__isnull=True),
        models.Q(end_time__gte=slot.time) | models.Q(end_time__isnull=True),
    ).order_by("-date").first()

    if pricing:
        price = pricing.final_price()
        if price > 0:
            return price

    # 🔥 ABSOLUTE FALLBACK (NEVER ZERO)
    return 1599
