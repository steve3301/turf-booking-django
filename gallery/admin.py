from django.contrib import admin
from django import forms
from .models import GalleryImage


class GalleryImageAdminForm(forms.ModelForm):
    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False
    )

    class Meta:
        model = GalleryImage
        fields = "__all__"


class GalleryImageAdmin(admin.ModelAdmin):
    form = GalleryImageAdminForm

    def save_model(self, request, obj, form, change):
        images = request.FILES.getlist("images")

        if images:
            for img in images:
                GalleryImage.objects.create(image=img)
        else:
            super().save_model(request, obj, form, change)


admin.site.register(GalleryImage, GalleryImageAdmin)
