from django.shortcuts import render
from .models import GalleryImage

def gallery_view(request):
    images = GalleryImage.objects.filter(active=True).order_by("-uploaded_at")
    return render(request, "gallery/gallery.html", {
        "images": images
    })
