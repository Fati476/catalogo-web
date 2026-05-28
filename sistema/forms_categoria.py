from django import forms
from .models import Categoria


class CategoriaForm(forms.ModelForm):

    class Meta:

        model = Categoria

        fields = [
            'nombre',
            'descripcion'
        ]

        widgets = {

            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre categoría'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción categoría',
                'rows': 4
            })

        }