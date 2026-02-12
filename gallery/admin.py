from django.contrib import admin
from .models import GalleryImage


class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "image", "active")

    def save_model(self, request, obj, form, change):
        files = request.FILES.getlist("image")
        if files:
            for f in files:
                GalleryImage.objects.create(image=f)
        else:
            super().save_model(request, obj, form, change)


admin.site.register(GalleryImage, GalleryImageAdmin)
