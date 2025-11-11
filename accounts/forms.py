from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['nombre', 'bio', 'avatar', 'banner']
        labels = {
            'nombre': 'Nombre para visualizar',
            'bio': 'Biografía',
            'avatar': 'Avatar',
            'banner': 'Banner',
        }
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'style': 'font-size: 0.9rem; resize: vertical;',
            }),
        }
