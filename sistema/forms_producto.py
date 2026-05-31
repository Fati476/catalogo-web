from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):

    class Meta:

        model = Producto

        fields = [
            'nombre',
            'descripcion',
            'precio',
            'categoria',
            'estado'
        ]

        widgets = {

            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control'
            }),

            'precio': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),

            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),

        }