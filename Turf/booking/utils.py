from django.shortcuts import redirect
from django.db import models
from .models import SlotPricing

def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, "staffprofile"):
            return view_func(request, *args, **kwargs)
        return redirect("login")
    return wrapper

def get_slot_price(slot):
    from .models import SlotPricing
    from django.utils import timezone

    pricing = SlotPricing.objects.filter(
        sport=slot.sport,
        active=True
    ).filter(
        models.Q(date=slot.date) | models.Q(date__isnull=True),
        models.Q(start_time__lte=slot.time) | models.Q(start_time__isnull=True),
        models.Q(end_time__gte=slot.time) | models.Q(end_time__isnull=True),
    ).order_by("-date").first()

    if pricing:
        return pricing.final_price()

    return 1599  # default fallback
