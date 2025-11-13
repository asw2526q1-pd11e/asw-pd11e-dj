from django import forms
from django.utils import timezone
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title",
            "content",
            "published_date",
            "communities",
            "image",
            "url",
        ]
        labels = {
            "url": "Enlace de interés (opcional)",
            "communities": "Comunidades",
        }
        widgets = {
            "published_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "readonly": "readonly",
                },
                format="%Y-%m-%d %H:%M:%S",
            ),
            "communities": forms.SelectMultiple(
                attrs={
                    "class": "form-control community-select",
                    "multiple": "multiple",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.published_date:
            self.fields["published_date"].initial = (
                self.instance.published_date
            )
        else:
            self.fields["published_date"].initial = timezone.now()

    def clean_published_date(self):
        if self.instance and self.instance.published_date:
            return self.instance.published_date
        return timezone.now()
