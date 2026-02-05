from django.contrib import admin
from .models import GalleryImage

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("title",)

