from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):

    class Meta:

        model = Producto

        fields = [
            'nombre',
            'descripcion',
            'precio_san_mateo',
            'precio_fuera',
            'categoria',
            'estado',
            'destacado'
        ]

        widgets = {

            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control'
            }),

            'precio_san_mateo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),

            'precio_fuera': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),

            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),

            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),

            'destacado': forms.Select(attrs={
                'class': 'form-select'
            }),

        }