from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title",
            "content",
            "author",
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
            "communities": forms.SelectMultiple(
                attrs={
                    "class": "form-control community-select",
                    "multiple": "multiple",
                }
            ),
        }
