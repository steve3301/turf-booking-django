from django.db import models

class GalleryImage(models.Model):
    title = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="gallery/")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else f"Gallery Image {self.id}"