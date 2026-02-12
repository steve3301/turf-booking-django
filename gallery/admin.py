from django.contrib import admin
from django import forms
from .models import GalleryImage


class MultiImageUploadForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.FileInput(attrs={"multiple": True}),
        required=False
    )

    class Meta:
        model = GalleryImage
        fields = ["images"]


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    change_list_template = "admin/gallery_upload.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path("upload-multiple/", self.admin_site.admin_view(self.upload_multiple), name="upload-multiple"),
        ]
        return custom_urls + urls

    def upload_multiple(self, request):
        if request.method == "POST":
            files = request.FILES.getlist("images")
            for f in files:
                GalleryImage.objects.create(image=f)
            self.message_user(request, "Images uploaded successfully.")
            from django.shortcuts import redirect
            return redirect("..")

        from django.shortcuts import render
        return render(request, "admin/gallery_upload.html")
