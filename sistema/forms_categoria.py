from django import forms
from .models import Categoria


class CategoriaForm(forms.ModelForm):

    class Meta:

        model = Categoria

        fields = [
            'nombre',
            'descripcion',
            'destacada',
            'imagen'
        ]

        widgets = {

            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe brevemente esta categoría...',
                'rows': 4
            }),

            'destacada': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),

            'imagen': forms.FileInput(attrs={
                'class': 'form-control'
            })

        }