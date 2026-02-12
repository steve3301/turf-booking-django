from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("booking.urls")),
    path("gallery/", include("gallery.urls")),
]

# 🔥 ALWAYS serve media (for now)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
